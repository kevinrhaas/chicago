#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frontal fictional reference fitting with an exact, vectorized Jacobian.

Same hm08 landmarks, signed morphs, camera, priors and bounds as fit_portrait_face.
An analytic derivative avoids dozens of extra projections per solver iteration
when importing a reference batch. Existing curated portrait fits are untouched.
"""
import json
import numpy as np
from scipy.optimize import least_squares
import fit_portrait_face as F


def rotation(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch), np.cos(roll), np.sin(roll)
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    X = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Z = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    dY = np.array([[-sy, 0, cy], [0, 0, 0], [-cy, 0, -sy]])
    dX = np.array([[0, 0, 0], [0, -sp, -cp], [0, cp, -sp]])
    dZ = np.array([[-sr, -cr, 0], [cr, -sr, 0], [0, 0, 0]])
    return Z @ X @ Y, (Z @ X @ dY, Z @ dX @ Y, dZ @ X @ Y)


def objective(base, positive, negative, observed, sigma, centre, spreads):
    """Residual and exact derivative; isolated for finite-difference verification."""
    origin = base.mean(axis=0)
    count, axes = len(base), len(centre)

    def state(p):
        cam, v = p[:6], p[6:]
        delta = np.where((v >= 0)[:, None, None], positive, -negative)
        X = base + np.einsum('a,aij->ij', v, delta) - origin
        R, derivatives = rotation(*cam[:3])
        Y = X @ R.T
        pixels = np.column_stack((cam[4] + cam[3] * Y[:, 0], cam[5] - cam[3] * Y[:, 1]))
        return cam, v, delta, X, R, derivatives, Y, pixels

    def residual(p):
        _, v, _, _, _, _, _, pixels = state(p)
        return np.r_[((pixels - observed) / sigma[:, None]).ravel(), (v - centre) / spreads]

    def jacobian(p):
        cam, _, delta, X, R, derivatives, Y, _ = state(p)
        J = np.zeros((count, 2, 6 + axes))
        for k, derivative in enumerate(derivatives):
            d = X @ derivative.T
            J[:, 0, k], J[:, 1, k] = cam[3] * d[:, 0], -cam[3] * d[:, 1]
        J[:, 0, 3], J[:, 1, 3] = Y[:, 0], -Y[:, 1]
        J[:, 0, 4], J[:, 1, 5] = 1, 1
        d = delta @ R.T
        J[:, 0, 6:] = cam[3] * d[:, :, 0].T
        J[:, 1, 6:] = -cam[3] * d[:, :, 1].T
        prior = np.zeros((axes, 6 + axes))
        prior[:, 6:] = np.diag(1 / spreads)
        return np.vstack(((J / sigma[:, None, None]).reshape(count * 2, -1), prior))

    return residual, jacobian, state


def fit(person, portrait):
    header, refs, axes = F.load_kit()
    spec = {a['id']: a for a in json.loads(F.AXES.read_text())['axes']}
    table = json.loads(F.MP_TABLE.read_text())['bodies'][portrait['base_body']]
    ring = min(table['outline'], key=lambda o: abs(o['solved_yaw_deg'] - portrait['outline_yaw_deg']))
    landmarks = {**F.landmarks(), **{k: v['vertex'] for k, v in table['points'].items()},
                 **{k: v['vertex'] for k, v in ring['points'].items()}}
    names = [m['landmark'] for m in portrait['marks']]
    members = [[landmarks[n]] if isinstance(landmarks[n], int) else list(landmarks[n]) for n in names]
    index = F.kit_index()
    rows = np.array(sorted({index[v] for group in members for v in group}))
    at = {v: i for i, v in enumerate(rows)}
    W = np.zeros((len(names), len(rows)))
    for i, group in enumerate(members):
        for v in group: W[i, at[index[v]]] += 1 / len(group)
    base_rows, fitted, prior, held, _ = F.face_base(person, portrait, header, refs, axes, rows)
    base = W @ base_rows
    observed = np.array([[m['x'], m['y']] for m in portrait['marks']])
    sigma = np.array([m['sigma_px'] for m in portrait['marks']])
    spreads = np.array([spec[a]['spread'] or .1 for a in fitted]) * F.PRIOR_WIDEN * portrait.get('prior_widen', 1)
    centre = np.array([np.clip(prior.get(a, 0), -header.get('limit', 1), header.get('limit', 1)) for a in fitted])
    e = [names.index(n) for n in ('pupil_r', 'pupil_l')]
    scale = np.linalg.norm(observed[e[1]] - observed[e[0]]) / np.linalg.norm(base[e[1]] - base[e[0]])
    initial = np.r_[0., 0., 0., scale, observed.mean(axis=0), centre]
    low = np.r_[-1.4, -.8, -.6, scale * .5, -1e5, -1e5, -np.ones(len(fitted))]
    high = np.r_[1.4, .8, .6, scale * 2, 1e5, 1e5, np.ones(len(fitted))]
    if 'head_shape' in fitted: low[6 + fitted.index('head_shape')] = 0
    options = range(len(axes['head_shape']['opts_d'])) if 'head_shape' in fitted else [0]
    best = None
    for option in options:
        pos = np.array([W @ F.delta_at(axes[a], 1., option if axes[a]['kind'] == 'one_of' else 0, rows) for a in fitted])
        neg = np.array([W @ F.delta_at(axes[a], -1., option if axes[a]['kind'] == 'one_of' else 0, rows) for a in fitted])
        residual, jacobian, state = objective(base, pos, neg, observed, sigma, centre, spreads)
        result = least_squares(residual, initial, jac=jacobian, bounds=(low, high), x_scale='jac',
                               max_nfev=20000, ftol=1e-11, xtol=1e-11, gtol=1e-11)
        if result.success and (best is None or result.cost < best[0].cost - 1e-9):
            best = result, option, state(result.x)[-1]
    if best is None: raise ValueError(person + ': no head option converged')
    result, option, projected = best
    cam, values = result.x[:6], result.x[6:]
    fitted_values = {a: round(float(v), 3) + 0. for a, v in zip(fitted, values)}
    fitted_values.update({a: round(float(v), 3) + 0. for a, v in held.items()})
    if 'head_shape' in fitted: fitted_values['head_shape.option'] = int(option)
    return {'values': fitted_values, 'rms_px': round(float(np.sqrt(((projected - observed) ** 2).sum(axis=1).mean())), 2),
            'projection_centre_m': base.mean(axis=0).tolist(),
            'camera': {'yaw_deg': round(float(np.degrees(cam[0])), 1), 'pitch_deg': round(float(np.degrees(cam[1])), 1),
                       'roll_deg': round(float(np.degrees(cam[2])), 1), 'px_per_m': round(float(cam[3]), 1),
                       'shift_px': [round(float(cam[4]), 1), round(float(cam[5]), 1)]}}
