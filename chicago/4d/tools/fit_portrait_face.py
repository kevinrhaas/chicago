#!/usr/bin/env python3
"""Fit a named resident's face to a portrait of them (T-3413).

    python3 tools/fit_portrait_face.py            write data/humans/variation/fits/<person>.json
    python3 tools/fit_portrait_face.py --check    refit in memory; fail if a fit file, or the card's
                                                  still of it (tools/portrait_still.mjs), is stale
    python3 tools/fit_portrait_face.py --overlay OUT.png PERSON CROP   the fitted landmarks over a local copy of the crop

What it reads. A portrait record, data/humans/variation/portraits/<person>.json, holds where
a reader marked facial landmarks on a picture of the person (pixel x, y on a named scan, each
with the reader's own uncertainty in pixels) and cites the picture's source record. The face
is the shared MakeHuman delta kit (assets/humans/web/hm08_variation_kit.*, T-3412): the
landmarks are fixed vertices of the hm08 body, located here from base.obj's own geometry
(eyelash helpers for the eye corners, the midline profile for the nose, mouth and chin, the
ear's own target for the ear), so nobody picks them by hand.

The fit. The face's axis values and a weak-perspective camera (yaw, pitch, roll, scale, shift)
are chosen to put the projected landmarks where the reader marked them, each residual divided
by its uncertainty, while every axis is held towards zero by its own seeded spread from
axes.json (a Gaussian prior: an axis the picture says nothing about stays at the town's
average instead of wandering). The person's age at the picture drives the ageing pair, as it
does in the renderer, so the fitted values are the face's shape, not its years. A record naming
`base_body` (T-3473, a woman's portrait) fits against that body's own rest face (its unoptimised
GLB under assets/humans/, in the kit's vertex order), at its base age, and centres each prior on
the body's face_bias, which a fitted value replaces in the renderer. A record with `stand_in`
(T-3478: no photograph of the person is known) is fitted to a stand-in's photograph, someone of
their sex, age, heritage and work: it must be graded reconstructed, and its `card_note` goes on
the card (tools/cut_portrait.py burns its `label` on the picture). A record's `read_by_eye`
(T-3493) gives values a reader sees in the picture on axes no mark measures (a full cheek, a
jowl, a broad jaw), with its own `basis`: each centres that axis's prior instead of the body's
face_bias, and the fit lists them as read_by_eye. The one_of
head outline is tried option by option and the best kept.

What it writes. The fitted values for every face axis the portrait can move (and the head
outline and forehead height, which a standing figure uses), the residual in pixels, and, per
axis, whether the picture constrains it (the data's information on it exceeds the prior's) or
the value is mostly the prior's. The grade is the portrait's: a picture showing the face whole makes
the proportions attested (AGENTS.md rule 12 read for a face); what a morph cannot express
(spectacles, a moustache, hair) is listed in `not_modelled`, not claimed.
"""
import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np
from scipy.optimize import least_squares

ROOT = pathlib.Path(__file__).resolve().parents[1]
MH = ROOT / 'assets/authored/humans/makehuman_hm08'
KIT_JSON = ROOT / 'assets/humans/web/hm08_variation_kit.json'
AXES = ROOT / 'data/humans/variation/axes.json'
PORTRAITS = ROOT / 'data/humans/variation/portraits'
FITS = ROOT / 'data/humans/variation/fits'
MP_TABLE = ROOT / 'data/humans/variation/mediapipe_hm08_landmarks.json'
# The prior on a fitted axis is MakeHuman's own spread of a face, before T-3412 narrowed the
# seeded draws to 0.65 of it so that no stranger is a caricature: a real face read from a
# picture may sit anywhere a real face does. Bounds are the sliders' own +-1.
PRIOR_WIDEN = 1 / 0.65


def load_kit():
    header = json.loads(KIT_JSON.read_text())
    blob = (KIT_JSON.parent / header['bin']).read_bytes()
    n = header['vertex_count']
    refs = np.frombuffer(blob, dtype='<i2', count=n * 3, offset=header['refs']['offset']).reshape(n, 3) * header['ref_unit_m']

    def half(h):
        if not h:
            return None
        idx = np.frombuffer(blob, dtype='<u2', count=h['count'], offset=h['index']).astype(np.int64)
        d = np.frombuffer(blob, dtype='<i2', count=h['count'] * 3, offset=h['delta']).reshape(-1, 3) * header['delta_unit_m']
        return idx, d

    axes = {}
    for a in header['axes']:
        axes[a['id']] = {**a, 'pos_d': half(a.get('pos')), 'neg_d': half(a.get('neg')),
                         'opts_d': [half(o) for o in a.get('options', [])]}
    return header, refs, axes


def read_base():
    verts, groups, g = [], {}, ''
    for line in (MH / 'makehuman/data/3dobjs/base.obj').read_text().splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == 'v':
            verts.append([float(x) for x in f[1:4]])
        elif f[0] == 'g':
            g = f[1]
        elif f[0] == 'f':
            groups.setdefault(g, set()).update(int(x.split('/')[0]) - 1 for x in f[1:])
    return np.array(verts), groups


def landmarks():
    """Landmark name -> base.obj source vertex index, found from the mesh's own geometry."""
    V, groups = read_base()
    body = np.array(sorted(groups['body']))
    head = body[V[body, 1] > 5.9]
    P = V[head]

    def nearest(point):
        return int(head[np.argmin(((P - point) ** 2).sum(1))])

    out = {}
    for side, sx in (('r', -1), ('l', 1)):
        lash = V[sorted(groups[f'helper-{side}-eyelashes-1'] | groups[f'helper-{side}-eyelashes-2'])]
        ax = np.abs(lash[:, 0])
        out[f'eye_inner_{side}'] = nearest(lash[np.argmin(ax)])
        out[f'eye_outer_{side}'] = nearest(lash[np.argmax(ax)])
        # The pupil, looking ahead, is between the corners: no single vertex of the skin.
        out[f'pupil_{side}'] = (out[f'eye_inner_{side}'], out[f'eye_outer_{side}'])
    # The face's midline profile: midline vertices with nothing of the midline in front of
    # them at their height (the mouth's inside and the nostrils' floor lie behind).
    mid = head[np.abs(V[head, 0]) < 0.012]
    M = V[mid]
    front = np.array([M[k, 2] >= M[np.abs(M[:, 1] - M[k, 1]) < 0.02, 2].max() - 0.03 for k in range(len(mid))])
    mid, M = mid[front & (M[:, 2] > 0.9)], M[front & (M[:, 2] > 0.9)]
    band = lambda lo, hi: mid[(M[:, 1] > lo) & (M[:, 1] < hi)]
    deepest = lambda b: int(b[np.argmin(V[b, 2])])
    foremost = lambda b: int(b[np.argmax(V[b, 2])])
    eye_y = V[list(out['pupil_r']), 1].mean()
    tip = foremost(band(eye_y - 0.8, eye_y - 0.1))
    ty = V[tip, 1]
    out['nose_tip'] = tip
    out['nasion'] = deepest(band(eye_y - 0.05, eye_y + 0.35))
    upper = foremost(band(ty - 0.35, ty - 0.12))                 # the upper lip's crest
    out['subnasale'] = deepest(band(V[upper, 1] + 0.01, ty - 0.02))
    lower = foremost(band(V[upper, 1] - 0.3, V[upper, 1] - 0.08))  # the lower lip's crest
    out['stomion'] = deepest(band(V[lower, 1] + 0.01, V[upper, 1] - 0.01))
    # Gnathion: the chin's most forward-and-down point, where its outline turns under.
    chin = band(V[lower, 1] - 0.6, V[lower, 1] - 0.15)
    out['menton'] = int(chin[np.argmax(V[chin, 2] - V[chin, 1])])
    # The right ear (the reader's left in a picture turned to his left). Its top: the highest
    # point that stands out from the skull's side; its lobe: the lowest point the lobe target moves.
    side = head[(V[head, 0] < -0.78) & (V[head, 2] > 0.1) & (V[head, 2] < 0.8)]
    out['ear_top_r'] = int(side[np.argmax(V[side, 1])])
    moved = {}
    for line in (MH / 'makehuman/data/targets/ears/r-ear-lobe-incr.target').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            i, x, y, z = line.split()
            if int(i) in groups['body']:
                moved[int(i)] = (float(x) ** 2 + float(y) ** 2 + float(z) ** 2) ** 0.5
    lobe = np.array([i for i, d in moved.items() if d > 0.5 * max(moved.values())])
    out['ear_lobe_r'] = int(lobe[np.argmin(V[lobe, 1])])
    out['vertex'] = int(head[np.argmax(P[:, 1])])
    # The left ear, for a face turned the other way (T-3486): the right ear's points mirrored
    # across the midline (base.obj is symmetric), each the nearest skin vertex to its mirror.
    for k in ('ear_top', 'ear_lobe'):
        out[f'{k}_l'] = nearest(V[out[f'{k}_r']] * np.array([-1.0, 1.0, 1.0]))
    return out


def body_rest(asset):
    """The rest positions of a body's skin, in the kit's vertex order (the unoptimised GLB under
    assets/humans/ keeps base.obj's prepared order; the web copies are meshopt-reordered)."""
    import struct
    blob = (ROOT / 'assets/humans' / f'{asset}.lod0.glb').read_bytes()
    n = struct.unpack('<I', blob[12:16])[0]
    gltf, binary = json.loads(blob[20:20 + n]), blob[28 + n:]
    mesh = next(m for m in gltf['meshes'] if '_body_' in m['name'])
    acc = gltf['accessors'][mesh['primitives'][0]['attributes']['POSITION']]
    view = gltf['bufferViews'][acc['bufferView']]
    off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    return np.frombuffer(binary, dtype='<f4', count=acc['count'] * 3, offset=off).reshape(-1, 3).astype(float)


def kit_index():
    prepared = json.loads((MH / 'prepared.json').read_text())['meshes'][0]
    first = {}
    for k, v in enumerate(prepared['source_vertex_indices']):
        first.setdefault(int(v), k)
    return first


def delta_at(axis, value, option, rows):
    """The axis's displacement of the kit rows `rows` at `value` (the renderer's denseDelta)."""
    out = np.zeros((len(rows), 3))
    if not value:
        return out
    if axis['kind'] == 'one_of':
        h, w = axis['opts_d'][option], value
    elif value > 0 or not axis['neg_d']:
        h, w = axis['pos_d'], value
    else:
        h, w = axis['neg_d'], -value
    if h is None:
        return out
    idx, d = h
    where = {int(i): j for j, i in enumerate(idx)}
    for r, row in enumerate(rows):
        j = where.get(int(row))
        if j is not None:
            out[r] = w * d[j]
    return out


def rot(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch), np.cos(roll), np.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def face_base(person, portrait, header, refs, axes, rows):
    """The face the axes move, on the kit rows `rows`: the body's rest shape with the ageing, the
    face_bias on axes the picture does not fit, the build and the axes held by eye; and the axes
    left to fit, with the priors that hold them."""
    # The face the deltas land on. By default the kit's own reference mesh (the men's base);
    # a record naming `base_body` (T-3473) fits against that body's own rest shape instead, so
    # a woman's face is read as departures from a woman's face, not from a man's, with the body's
    # base age and its face_bias (on the axes the picture does not move) as the renderer adds them.
    body = header['assets'].get(portrait['base_body'], {}) if portrait.get('base_body') else {}
    base = (body_rest(portrait['base_body'])[rows] if portrait.get('base_body') else refs[rows]).copy()
    # The ageing the renderer drives from the person's age at the picture (human-variation.js).
    age = portrait['age_at_picture_years']
    asset_age = body.get('base_age_years', 35)
    for a in header['axes']:
        if a.get('drive') != 'age':
            continue
        # Only the body's own sex's age blend (T-3423 added the female twin of each macro axis).
        if a.get('sex', 'male') != portrait.get('sex', 'male'):
            continue
        if a['kind'] == 'age_macro':
            v = float(np.clip((age - asset_age) * header['age']['per_year'], -0.5, 1))
        else:
            v = float(np.clip((age - asset_age) / (90 - asset_age) if age >= asset_age else (age - asset_age) / (asset_age - 25), -0.5, 1))
        if a['kind'] == 'age_macro':
            base += delta_at({**axes[a['id']], 'kind': 'signed'}, v, 0, rows)
        else:
            base += delta_at(axes[a['id']], v, 0, rows)
    fitted = [a['id'] for a in header['axes'] if not a.get('drive') and a['id'] in portrait['axes']]
    # What a reader sees in the picture that no mark measures (T-3493: Frances Glessner's full
    # cheeks, jowls and broad jaw): `read_by_eye.values` replaces the body's face_bias as the
    # prior on those axes, so a flat axis rests at what the picture shows, not at the body's lean.
    eye = (portrait.get('read_by_eye') or {}).get('values', {})
    for k in eye:
        if k not in fitted:
            sys.exit(f"{person}: read_by_eye names {k}, which is not one of the record's fitted axes")
    prior = {**body.get('face_bias', {}), **eye}
    for k, b in body.get('face_bias', {}).items():
        if k not in fitted and k in axes:
            base += delta_at(axes[k], max(-header['limit'], min(header['limit'], b)), 0, rows)
    # T-3553: the build a stand-in's likeness gives (weight, muscle, a paunch, the neck), which
    # moves the face too (a heavy man's fuller face): on the base, as the renderer adds it.
    build = (portrait.get('likeness') or {}).get('build') or {}
    for a in header['axes']:
        k = a.get('draw_as', a['id'])
        if k in ('weight', 'muscle', 'belly', 'neck_width', 'double_chin') and isinstance(build.get(k), (int, float)) \
                and a.get('sex', portrait.get('sex', 'male')) == portrait.get('sex', 'male') and not a.get('drive'):
            base += delta_at(axes[a['id']], max(-header['limit'], min(header['limit'], build[k])), 0, rows)
    # T-3553: an axis a record HOLDS by eye (`read_by_eye.hold`) is not fitted at all but set
    # where the reader put it: one the marks cannot see from a near-frontal view, or read
    # wrongly through the renderer's own painting (a lip's height is its painted colour, which
    # a volume target leaves as it was; a cheekbone's height is shading, not outline). The
    # marks then fit the other axes around it. Owner, 2026-11-13, of Sarah Grey: "her
    # cheekbones are higher ... she has finer features", and her thin lips.
    held = {}
    for k in (portrait.get('read_by_eye') or {}).get('hold', []):
        if k not in eye:
            sys.exit(f"{person}: read_by_eye holds {k} but gives it no value")
        if axes[k]['kind'] == 'one_of':
            sys.exit(f"{person}: read_by_eye cannot hold {k}, a choice of shapes")
        held[k] = max(-1.0, min(1.0, eye[k]))   # the fitted axes' own bounds
        base += delta_at(axes[k], held[k], 0, rows)
        fitted.remove(k)
    return base, fitted, prior, held, body


def fit(person):
    portrait = json.loads((PORTRAITS / f'{person}.json').read_text())
    header, refs, axes = load_kit()
    spec = {a['id']: a for a in json.loads(AXES.read_text())['axes']}
    lm = landmarks()
    names = [m['landmark'] for m in portrait['marks']]
    # T-3553: MediaPipe's points (`mp_<index>`), each on the skin vertex the correspondence
    # table names (tools/face_landmark_correspondence.py).
    if any(n.startswith(('mp_', 'mpo_')) for n in names):
        table = json.loads(MP_TABLE.read_text())['bodies'][portrait['base_body']]
        lm = {**lm, **{k: v['vertex'] for k, v in table['points'].items()}}
        # The face's outline (`mpo_<index>`) from the calibration render turned as the portrait is.
        if 'outline_yaw_deg' in portrait:
            ring = min(table['outline'], key=lambda o: abs(o['solved_yaw_deg'] - portrait['outline_yaw_deg']))
            lm = {**lm, **{k: v['vertex'] for k, v in ring['points'].items()}}
    kidx = kit_index()
    # A landmark is one vertex or the mean of several (a pupil, between the eye's corners).
    members = [[lm[n]] if isinstance(lm[n], int) else list(lm[n]) for n in names]
    rows = np.array(sorted({kidx[v] for m in members for v in m}))
    W = np.zeros((len(names), len(rows)))
    for k, m in enumerate(members):
        for v in m:
            W[k, list(rows).index(kidx[v])] += 1 / len(m)
    obs = np.array([[m['x'], m['y']] for m in portrait['marks']], float)
    sig = np.array([m['sigma_px'] for m in portrait['marks']], float)
    base_rows, fitted, prior, held, body = face_base(person, portrait, header, refs, axes, rows)
    base = W @ base_rows
    if portrait.get('fit_views'):
        return fit_views(person, portrait, header, refs, axes, spec, lm, names, members, obs, sig, kidx)
    # Each signed axis is piecewise linear; precompute its two halves at +-1 on the landmark rows.
    halves = {}
    for aid in fitted:
        a = axes[aid]
        if a['kind'] == 'one_of':
            halves[aid] = [W @ delta_at(a, 1.0, o, rows) for o in range(len(a['opts_d']))]
        else:
            halves[aid] = (W @ delta_at(a, 1.0, 0, rows), W @ delta_at(a, -1.0, 0, rows))
    # A rest axis (never drawn, spread 0: the mouth's resting set) is fitted only where it is
    # read by eye, held there as tightly as the narrowest drawn axis.
    # A record may loosen its prior further (`prior_widen`, T-3553: a face marked at hundreds of
    # points by a landmark model, which should be held by the picture, not by the town's average).
    spreads = np.array([spec[aid]['spread'] or 0.1 for aid in fitted]) * PRIOR_WIDEN * portrait.get('prior_widen', 1.0)
    # A fitted value replaces the body's face_bias in the renderer, so an axis the picture says
    # little about is held towards the body's own lean (a woman's jaw), not towards the men's zero.
    lim = header.get('limit', 1.0)
    centre = np.array([max(-lim, min(lim, prior.get(aid, 0.0))) for aid in fitted])
    limit = 1.0

    def shape(v, option):
        X = base.copy()
        for k, aid in enumerate(fitted):
            h = halves[aid]
            if axes[aid]['kind'] == 'one_of':
                X += abs(v[k]) * h[option]
            elif v[k] >= 0:
                X += v[k] * h[0]
            else:
                X += -v[k] * h[1]
        return X

    def project(X, cam):
        yaw, pitch, roll, s, tx, ty = cam
        c = X - base.mean(0)
        Y = c @ rot(yaw, pitch, roll).T
        return np.stack([tx + s * Y[:, 0], ty - s * Y[:, 1]], 1)

    def residuals(p, option):
        cam, v = p[:6], p[6:]
        r = ((project(shape(v, option), cam) - obs) / sig[:, None]).ravel()
        return np.concatenate([r, (v - centre) / spreads])

    # A profile may hide the far eye. Use the visible crown/chin span for its
    # initial scale instead of inventing a pupil. Full-face fits retain their
    # original initialization and therefore their existing results.
    pair = ('pupil_r', 'pupil_l') if all(n in names for n in ('pupil_r', 'pupil_l')) else ('vertex', 'menton')
    if not all(n in names for n in pair):
        raise ValueError('A portrait needs both visible pupils or visible crown and chin for camera initialization')
    e = [names.index(n) for n in pair]
    s0 = np.linalg.norm(obs[e[1]] - obs[e[0]]) / np.linalg.norm(base[e[1]] - base[e[0]])
    t0 = obs.mean(0)
    best = None
    options = range(len(axes['head_shape']['opts_d'])) if 'head_shape' in fitted else [0]
    for option in options:
        for yaw0 in (-0.6, -0.3, 0.0, 0.3, 0.6):
            p0 = np.concatenate([[yaw0, 0.0, 0.0, s0, *t0], centre])
            lo = np.concatenate([[-1.4, -0.8, -0.6, s0 * 0.5, -1e5, -1e5], -limit * np.ones(len(fitted))])
            hi = np.concatenate([[1.4, 0.8, 0.6, s0 * 2, 1e5, 1e5], limit * np.ones(len(fitted))])
            if 'head_shape' in fitted:
                lo[6 + fitted.index('head_shape')] = 0
            r = least_squares(residuals, p0, bounds=(lo, hi), args=(option,), x_scale='jac', max_nfev=20000,
                              ftol=1e-13, xtol=1e-13, gtol=1e-13)   # converge fully: a flat axis must not stop wherever the BLAS build leaves it
            if best is None or r.cost < best[0].cost - 1e-9:
                best = (r, option)
    r, option = best
    cam, v = r.x[:6], r.x[6:]
    pix = project(shape(v, option), cam) - obs
    # Is an axis constrained by the picture? Its data information (the Jacobian column's
    # weighted norm, over the landmark rows only) against the prior's 1/spread^2.
    J = r.jac[:2 * len(names), 6:]
    info = (J ** 2).sum(0)
    constrained = {aid: bool(info[k] > 1 / spreads[k] ** 2) for k, aid in enumerate(fitted)}
    # The same reading as a ratio (1 is the line); --check lets an axis near it change sides.
    info_ratio = {aid: float(info[k] * spreads[k] ** 2) for k, aid in enumerate(fitted)}
    values = {aid: round(float(v[k]), 3) + 0.0 for k, aid in enumerate(fitted)}   # + 0.0: no -0.0
    values.update({k: round(float(x), 3) + 0.0 for k, x in held.items()})
    if 'head_shape' in fitted:
        values['head_shape.option'] = int(option)
    per_mark = {n: round(float(np.hypot(*pix[i])), 1) for i, n in enumerate(names)}
    return {
        'portrait': portrait, 'values': values, 'held': sorted(held), 'constrained': constrained, 'info_ratio': info_ratio,
        'camera': {'yaw_deg': round(float(np.degrees(cam[0])), 1), 'pitch_deg': round(float(np.degrees(cam[1])), 1),
                   'roll_deg': round(float(np.degrees(cam[2])), 1), 'px_per_m': round(float(cam[3]), 1),
                   'shift_px': [round(float(cam[4]), 1), round(float(cam[5]), 1)]},
        'rms_px': round(float(np.sqrt((pix ** 2).sum(1).mean())), 2),
        'per_mark_px': per_mark,
        'landmarks': {n: lm[n] if isinstance(lm[n], int) else list(lm[n]) for n in names},
        'projected': project(shape(v, option), cam).tolist(),
        'projected_unfitted': project(base, cam).tolist(),
        'obs': obs.tolist(), 'names': names,
    }


# T-3553 (owner, 2026-11-13, of the Greys' stand-ins: "everyone's profiles are way off, their
# noses is not as flat as you have them", "he has no chin and almost no nose", "her jaw is
# ragged"): one near-frontal picture cannot say how far a nose, a chin or a cheek stands out,
# and tracing the side view vertex by vertex on top of a face fitted from the front alone left
# lumps where the two disagreed. A record's `fit_views` fits the axes to more pictures of the
# same face AT ONCE, each with its own camera: further front views (`fronts`, MediaPipe's points
# on another picture) and the side view of `trace.profile` (its eye and lips' marks place a side
# camera; its silhouette, the face's line against the sky, is matched by the face's own outline
# seen from that side). The depth axes (nose_depth, chin_prominence, prognathism) are then read,
# and the face stays one smooth MakeHuman face. `extended_limits` lets an axis pass the slider's
# +-1 where the picture asks for more (a nose that stands further out than MakeHuman's largest).
PROFILE_ITERATIONS = 6     # the side view's outline is re-found this many times (closest points)
PROFILE_REACH_PX = 25      # an outline vertex further than this from the picture's line is left out
SIDE_EYE = ([33, 159, 145], [263, 386, 374])   # the visible eye's outer corner and lids


def body_triangles(asset):
    """The body skin's triangles, in the kit's vertex order (the unoptimised GLB)."""
    import struct
    blob = (ROOT / 'assets/humans' / f'{asset}.lod0.glb').read_bytes()
    n = struct.unpack('<I', blob[12:16])[0]
    gltf, binary = json.loads(blob[20:20 + n]), blob[28 + n:]
    mesh = next(m for m in gltf['meshes'] if '_body_' in m['name'])
    acc = gltf['accessors'][mesh['primitives'][0]['indices']]
    view = gltf['bufferViews'][acc['bufferView']]
    off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    dt = {5123: '<u2', 5125: '<u4'}[acc['componentType']]
    return np.frombuffer(binary, dtype=dt, count=acc['count'], offset=off).reshape(-1, 3).astype(int)


def fit_views(person, portrait, header, refs, axes, spec, lm, names, members, obs, sig, kidx):
    import cv2
    from scipy.spatial import cKDTree
    cfg = portrait['fit_views']
    asset = portrait['base_body']
    rest = body_rest(asset)
    table = json.loads(MP_TABLE.read_text())['bodies'][asset]
    # The head's rows: from the nasion up and down to below the chin.
    chin_y = rest[kidx[lm['menton']], 1]
    nasion_y = rest[kidx[table['points']['mp_168']['vertex']], 1]
    head = np.where(rest[:, 1] > chin_y - 0.6 * (nasion_y - chin_y))[0]
    at = {int(r): i for i, r in enumerate(head)}

    def wmat(groups):
        W = np.zeros((len(groups), len(head)))
        for k, g in enumerate(groups):
            for v in g:
                W[k, at[kidx[v]]] += 1 / len(g)
        return W

    base, fitted, prior, held, body = face_base(person, portrait, header, refs, axes, head)
    halves = {}
    for aid in fitted:
        a = axes[aid]
        if a['kind'] == 'one_of':
            halves[aid] = [delta_at(a, 1.0, o, head) for o in range(len(a['opts_d']))]
        else:
            halves[aid] = (delta_at(a, 1.0, 0, head), delta_at(a, -1.0, 0, head))
    spreads = np.array([spec[aid]['spread'] or 0.1 for aid in fitted]) * PRIOR_WIDEN * portrait.get('prior_widen', 1.0)
    lim = header.get('limit', 1.0)
    centre = np.array([max(-lim, min(lim, prior.get(aid, 0.0))) for aid in fitted])
    centre_of = base.mean(0)

    # Each axis's two halves stacked (a choice of shapes: its option's shape on both sides), so
    # a face is two products, on the rows a residual needs.
    one_of = np.array([axes[aid]['kind'] == 'one_of' for aid in fitted])

    def stacks(option):
        pos = np.stack([halves[aid][option] if one_of[k] else halves[aid][0] for k, aid in enumerate(fitted)])
        neg = np.stack([halves[aid][option] if one_of[k] else halves[aid][1] for k, aid in enumerate(fitted)])
        return pos, neg

    def shape(v, option, rows=None, st=None):
        pos, neg = st if st is not None else stacks(option)
        if rows is not None:
            pos, neg = pos[:, rows], neg[:, rows]
        a = np.where(one_of, np.abs(v), np.maximum(v, 0.0))
        b = np.where(one_of, 0.0, np.maximum(-v, 0.0))
        return (base if rows is None else base[rows]) + np.tensordot(a, pos, 1) + np.tensordot(b, neg, 1)

    def project(X, cam):
        yaw, pitch, roll, s, tx, ty = cam
        Y = (X - centre_of) @ rot(yaw, pitch, roll).T
        return np.stack([tx + s * Y[:, 0], ty - s * Y[:, 1]], 1)

    def solve_camera(W, ob, sg, yaws, prior_cam=None):
        P = W @ base
        best = None
        for y0 in yaws:
            c = np.array([y0, 0.0, 0.0, 1.0, 0.0, 0.0])
            Q = project(P, c)
            c[3] = np.linalg.norm(ob.max(0) - ob.min(0)) / max(np.linalg.norm(Q.max(0) - Q.min(0)), 1e-9)
            c[4:] = ob.mean(0) - project(P, c).mean(0)

            def res(q):
                r = ((project(P, q) - ob) / (sg if sg.ndim == 2 else sg[:, None])).ravel()
                return r if prior_cam is None else np.concatenate([r, prior_cam(q)])
            r = least_squares(res, c, x_scale='jac')
            if best is None or r.cost < best.cost:
                best = r
        return best.x

    # The views: the portrait itself, further front pictures, and the side view.
    fronts = [(wmat(members), obs, sig)]
    eye_span = np.linalg.norm(obs[names.index('mp_33')] - obs[names.index('mp_263')])
    ring0 = min(table['outline'], key=lambda o: abs(o['solved_yaw_deg']))
    for fr in cfg.get('fronts', []):
        pts = np.asarray(fr['points_px'], float)
        skip = set(fr.get('skip_points', []))
        groups, ob = [], []
        for i in range(len(pts)):
            if i not in skip and f'mp_{i}' in table['points']:
                groups.append([table['points'][f'mp_{i}']['vertex']]); ob.append(pts[i])
        for k, v in ring0['points'].items():
            if int(k[4:]) not in skip:
                groups.append([v['vertex']]); ob.append(pts[int(k[4:])])
        scale = np.linalg.norm(pts[33] - pts[263]) / eye_span
        fronts.append((wmat(groups), np.array(ob), np.full(len(ob), float(fr.get('sigma_px', 3.5)) * scale)))

    prof = portrait['trace']['profile']
    pv = cfg['profile']
    mk = {int(k): np.array(v, float) for k, v in prof['marks_px'].items()}
    eye = max(SIDE_EYE, key=lambda e: np.linalg.norm(mk[e[0]] - mk[{33: 133, 263: 362}[e[0]]]))
    # The lips' meeting places the side camera too; under a moustache (`lips: "height"`) only its
    # height counts: the landmark model finds the moustache's edge, which hangs in front of the lips.
    groups = [[table['points'][f'mp_{i}']['vertex']] for i in list(eye) + [13]]
    side_ob = np.array([mk[i] for i in eye] + [(mk[13] + mk[14]) / 2])
    side_sg = np.array([[pv.get('eye_sigma_px', 3.0)] * 2] * len(eye) + [[40.0 if pv.get('lips') == 'height' else 2.5, 2.5]])
    W_side = wmat(groups)
    sil = np.asarray(prof['silhouette_px'], float)
    facing = -1.0 if mk[4][0] < prof['tragus_px'][0] else 1.0
    ymin = mk[10][1] - 5
    ymax = mk[4][1] + (mk[13][1] - mk[4][1]) * 0.45 if pv.get('to') == 'nose' else sil[:, 1].max()
    sil = sil[(sil[:, 1] > ymin) & (sil[:, 1] < ymax) & ((sil[:, 0] - prof['tragus_px'][0]) * facing > 0)]
    tree = cKDTree(sil)
    normals = []
    for q in sil:
        _, j = tree.query(q, k=7)
        P = sil[j] - sil[j].mean(0)
        n = np.linalg.eigh(P.T @ P)[1][:, 0]
        normals.append(n if n[0] * facing >= 0 else -n)
    normals = np.array(normals)
    front_rows = np.where(rest[head, 2] > rest[prof['tragus_kit_vertex'], 2])[0]
    tri = body_triangles(asset)
    tri = np.array([[at[int(x)] for x in t] for t in tri if all(int(x) in at for x in t)])
    # The side camera: the turn the record reads by eye, its nod free (a raised chin), from the marks.
    turn = np.radians(prof['render_yaw_deg'])
    cam_sigma = np.radians(pv.get('camera_sigma_deg', 3.0))
    side0 = solve_camera(W_side, side_ob, side_sg, [turn], lambda q: [(q[0] - turn) / np.radians(1), q[1] / np.radians(1)])

    def outline(X, cam, scale=4):
        """The rows on the face's outline as the side camera sees it."""
        P = project(X, cam)
        lo = P.min(0) - 5
        Q = ((P - lo) * scale).astype(np.int32)
        m = np.zeros((Q[:, 1].max() + 10, Q[:, 0].max() + 10), np.uint8)
        cv2.fillPoly(m, [Q[t] for t in tri], 1)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=len)[:, 0, :] / scale + lo
        c = c[(c[:, 1] > ymin) & (c[:, 1] < ymax)]
        d, j = cKDTree(P[front_rows]).query(c)
        return np.unique(front_rows[j[d < 2.5]])

    nf = len(fronts)
    ext = cfg.get('extended_limits', {})
    lo = np.concatenate([[-1.4, -0.8, -0.6, 0, -1e6, -1e6] * nf, [-np.inf] * 6, -np.ones(len(fitted))])
    hi = np.concatenate([[1.4, 0.8, 0.6, 1e6, 1e6, 1e6] * nf, [np.inf] * 6, np.ones(len(fitted))])
    for k, aid in enumerate(fitted):
        if aid in ext:
            lo[6 * nf + 6 + k], hi[6 * nf + 6 + k] = -ext[aid], ext[aid]
    if 'head_shape' in fitted:
        lo[6 * nf + 6 + fitted.index('head_shape')] = 0
    sil_sigma = pv.get('silhouette_sigma_px', 2.0)

    used = np.unique(np.concatenate([np.nonzero(W.any(0))[0] for W, _, _ in fronts] + [np.nonzero(W_side.any(0))[0]]))

    def residuals(p, option, srows, pairs, w, st):
        v = p[6 * nf + 6:]
        rows = np.concatenate([used, srows])
        Xr = shape(v, option, rows, st)
        Xu, Xs = Xr[:len(used)], Xr[len(used):]
        out = [((project(W[:, used] @ Xu, p[6 * i:6 * i + 6]) - ob) / sg[:, None]).ravel() for i, (W, ob, sg) in enumerate(fronts)]
        cs = p[6 * nf:6 * nf + 6]
        out.append(((project(W_side[:, used] @ Xu, cs) - side_ob) / side_sg).ravel())
        if len(srows):
            out.append(np.sqrt(w) * ((project(Xs, cs) - pairs[0]) * pairs[1]).sum(1) / sil_sigma)
        out.append([(cs[0] - turn) / cam_sigma, cs[1] / cam_sigma])   # turned as the sheet reads, not tipped; the nod is free
        out.append((v - centre) / spreads)
        return np.concatenate([np.ravel(o) for o in out])

    best = None
    options = range(len(axes['head_shape']['opts_d'])) if 'head_shape' in fitted else [0]
    cams = [solve_camera(W, ob, sg, (-0.6, -0.3, 0.0, 0.3, 0.6)) for W, ob, sg in fronts]
    def run(option, p, iterations, nfev=4000):
        st = stacks(option)
        for _ in range(iterations):
            X = shape(p[6 * nf + 6:], option, None, st)
            cs = p[6 * nf:6 * nf + 6]
            srows = outline(X, cs)
            d, j = tree.query(project(X[srows], cs))
            srows, j = srows[d < PROFILE_REACH_PX], j[d < PROFILE_REACH_PX]
            pairs = (sil[j], normals[j])
            w = 150.0 / max(len(srows), 1)      # the outline weighs as much as 150 marks, however finely the mesh draws it
            r = least_squares(residuals, p, bounds=(lo, hi), args=(option, srows, pairs, w, st), x_scale='jac',
                              max_nfev=nfev, ftol=1e-12, xtol=1e-12, gtol=1e-12)
            p = r.x
        return r, option, srows, pairs, w

    # The head's outline is a choice of shapes: each is tried briefly, the best refined. A record
    # may name the one a full search chose (`head_shape_option`), which keeps the check quick.
    start = np.concatenate([*cams, side0, centre])
    if 'head_shape_option' in cfg:
        options = [cfg['head_shape_option']]
    for option in options:
        trial = run(option, start, 2)
        if best is None or trial[0].cost < best[0].cost - 1e-9:
            best = trial
    r, option, srows, pairs, w = run(best[1], best[0].x, PROFILE_ITERATIONS)
    p = r.x
    v = p[6 * nf + 6:]
    X = shape(v, option)
    cam = p[:6]
    pix = project(fronts[0][0] @ X, cam) - obs
    n_data = sum(2 * len(ob) for _, ob, _ in fronts) + 2 * len(side_ob) + len(srows)
    J = r.jac[:n_data, 6 * nf + 6:]
    info = (J ** 2).sum(0)
    cs = p[6 * nf:6 * nf + 6]
    side_miss = np.abs(((project(X[srows], cs) - pairs[0]) * pairs[1]).sum(1))
    values = {aid: round(float(v[k]), 3) + 0.0 for k, aid in enumerate(fitted)}
    values.update({k: round(float(x), 3) + 0.0 for k, x in held.items()})
    if 'head_shape' in fitted:
        values['head_shape.option'] = int(option)
    base_lm = fronts[0][0] @ base
    return {
        'portrait': portrait, 'values': values, 'held': sorted(held),
        'constrained': {aid: bool(info[k] > 1 / spreads[k] ** 2) for k, aid in enumerate(fitted)},
        'info_ratio': {aid: float(info[k] * spreads[k] ** 2) for k, aid in enumerate(fitted)},
        'camera': {'yaw_deg': round(float(np.degrees(cam[0])), 1), 'pitch_deg': round(float(np.degrees(cam[1])), 1),
                   'roll_deg': round(float(np.degrees(cam[2])), 1), 'px_per_m': round(float(cam[3]), 1),
                   'shift_px': [round(float(cam[4]), 1), round(float(cam[5]), 1)]},
        'rms_px': round(float(np.sqrt((pix ** 2).sum(1).mean())), 2),
        'per_mark_px': {n: round(float(np.hypot(*pix[i])), 1) for i, n in enumerate(names)},
        'views': {
            'fronts_rms_px': [round(float(np.sqrt((((project(W @ X, p[6 * i:6 * i + 6]) - ob)) ** 2).sum(1).mean())), 2)
                              for i, (W, ob, _) in enumerate(fronts)],
            'side_camera': {'yaw_deg': round(float(np.degrees(cs[0])), 1), 'pitch_deg': round(float(np.degrees(cs[1])), 1),
                            'nod_deg': round(float(np.degrees(cs[2])), 1), 'px_per_m': round(float(cs[3]), 1)},
            'side_outline_vertices': int(len(srows)),
            'side_outline_miss_mm': round(float(side_miss.mean() / cs[3] * 1000), 2),
        },
        'landmarks': {n: lm[n] if isinstance(lm[n], int) else list(lm[n]) for n in names},
        'projected': project(fronts[0][0] @ X, cam).tolist(),
        'projected_unfitted': project(base_lm, cam).tolist(),
        'obs': obs.tolist(), 'names': names,
    }


def record(person, f):
    p = f['portrait']
    if p.get('stand_in') and p['grade'] != 'reconstructed':
        sys.exit(f"{person}: a face fitted to a stand-in's photograph is reconstructed, not {p['grade']}")
    src = json.loads((ROOT / 'data/sources' / f"{p['source']}.json").read_text())
    return {
        'format': 'chicago4d_human_face_fit_v1',
        'ticket': 'T-3413',
        'person_id': person,
        'scene': p['scene'],
        'generated_by': 'tools/fit_portrait_face.py',
        '_doc': 'Regenerate with tools/fit_portrait_face.py from the portrait record; never edit by hand.',
        'grade': p['grade'],
        'sources': [p['source']],
        'portrait': f'data/humans/variation/portraits/{person}.json',
        'basis': p['basis'],
        'liberty': 'L-human-variation-3412',
        'values': f['values'],
        # Read: the marks carry more information on the axis than its prior does. Mostly
        # prior: the value moved from the average only as far as weak evidence allows.
        'read_from_picture': sorted(k for k, c in f['constrained'].items() if c),
        'mostly_prior': sorted(k for k, c in f['constrained'].items() if not c),
        **({'read_by_eye': sorted((p.get('read_by_eye') or {}).get('values', {}))} if p.get('read_by_eye') else {}),
        **({'held_by_eye': f['held']} if f['held'] else {}),
        'fit': {'rms_px': f['rms_px'], 'per_mark_px': f['per_mark_px'], 'camera': f['camera'],
                **({'views': f['views']} if f.get('views') else {}),
                'landmark_vertices': f['landmarks']},
        'not_modelled': p['not_modelled'],
        # What the person's card shows: the source as cited, the two pictures as published
        # (publish.sh serves assets/humans/web/ at data/humans/web/), and the residual in
        # millimetres on the face (pixels over the fitted scale).
        'card': {
            'source_citation': src['citation'], 'source_url': src.get('url', ''),
            'rms_mm': round(f['rms_px'] / f['camera']['px_per_m'] * 1000, 1),
            'marks': len(f['names']),
            'portrait': p['card']['portrait'].replace('assets/humans/web/', 'humans/web/'),
            'model': p['card']['model'].replace('assets/humans/web/', 'humans/web/'),
            # T-3478: a stand-in's photograph (no picture of the person is known) says so on the card.
            **({'stand_in': p['stand_in']['card_note']} if p.get('stand_in') else {}),
        } if p.get('card') else None,
    }


def overlay(person, out, crop):
    from PIL import Image, ImageDraw
    f = fit(person)
    p = f['portrait']
    im = Image.open(crop).convert('RGB')
    d = ImageDraw.Draw(im)
    for (ox, oy), (fx, fy), (ux, uy) in zip(f['obs'], f['projected'], f['projected_unfitted']):
        d.ellipse([ux - 3, uy - 3, ux + 3, uy + 3], outline=(80, 140, 255))
        d.ellipse([ox - 4, oy - 4, ox + 4, oy + 4], outline=(255, 220, 0), width=2)
        d.line([ox, oy, fx, fy], fill=(255, 60, 60), width=1)
        d.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=(255, 60, 60))
    im.save(out)
    print(json.dumps({k: f[k] for k in ('values', 'camera', 'rms_px', 'per_mark_px')}, indent=1))


# How far a refit may land from the committed fit and still be the same fit: a tenth of the
# smallest step anyone would read off a face (0.01 of an axis), a fifth of a degree, a pixel.
FIT_TOLERANCE = (
    ('values.', 0.01), ('fit.per_mark_px.', 0.5), ('fit.camera.yaw_deg', 0.2), ('fit.camera.pitch_deg', 0.2),
    ('fit.camera.roll_deg', 0.2), ('fit.camera.px_per_m', 2.0), ('fit.camera.shift_px', 1.0), ('fit.rms_px', 0.1),
)


# An axis the picture hardly decides (`mostly_prior`) sits in a flat valley of the fit, and where a
# solver stops in it follows the build (CI landed brow_ridge at 0.0 where a local run had 0.014).
# Its tolerance is the width it was never pinned to, still far inside its prior's spread.
LOOSE_AXIS_TOLERANCE = 0.05
# Whether the picture decides an axis is its data information against the prior's (a ratio, 1 the
# line). An axis whose ratio is within this band of the line can read either way on another build
# (CI moved one of Mary Reynolds' axes across it, T-3486), so --check lets such an axis sit in
# either `read_from_picture` or `mostly_prior`, and holds its value to LOOSE_AXIS_TOLERANCE.
BORDERLINE_RATIO = (0.5, 2.0)


def sides(rec, borderline):
    """The record with its borderline axes taken out of both reading lists, for comparison only."""
    out = dict(rec)
    for key in ('read_from_picture', 'mostly_prior'):
        if isinstance(out.get(key), list):
            out[key] = [a for a in out[key] if a not in borderline]
    return out


def differences(want, got, path='', loose=frozenset()):
    """Where a refit differs from the committed fit beyond FIT_TOLERANCE (exact for everything else);
    `loose` names the axes held to LOOSE_AXIS_TOLERANCE instead."""
    if isinstance(want, dict) and isinstance(got, dict):
        out = [f'{path}{k}: missing or extra' for k in sorted(set(want) ^ set(got))]
        for k in sorted(set(want) & set(got)):
            out += differences(want[k], got[k], f'{path}{k}.' if isinstance(want[k], (dict, list)) else f'{path}{k}', loose)
        return out
    if isinstance(want, list) and isinstance(got, list) and len(want) == len(got):
        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in want + got):
            tol = next((t for pre, t in FIT_TOLERANCE if path.rstrip('.').startswith(pre.rstrip('.'))), 0)
            return [f'{path.rstrip(".")}: {want} -> {got}'] if any(abs(a - b) > tol + 1e-9 for a, b in zip(want, got)) else []
        out = []
        for i, (a, b) in enumerate(zip(want, got)):
            out += differences(a, b, f'{path}{i}.', loose)
        return out
    if isinstance(want, (int, float)) and isinstance(got, (int, float)) and not isinstance(want, bool):
        tol = next((t for pre, t in FIT_TOLERANCE if path.startswith(pre)), 0)
        if path.startswith('values.') and path[len('values.'):] in loose:
            tol = LOOSE_AXIS_TOLERANCE
        return [] if abs(want - got) <= tol + 1e-9 else [f'{path}: {want} -> {got}']
    return [] if want == got else [f'{path.rstrip(".")}: {str(want)[:40]} -> {str(got)[:40]}']



def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--overlay', nargs=3, metavar=('OUT', 'PERSON', 'CROP_IMAGE'))
    args = ap.parse_args()
    if args.overlay:
        overlay(args.overlay[1], args.overlay[0], args.overlay[2])
        return 0
    bad = []
    for path in sorted(PORTRAITS.glob('*.json')):
        person = path.stem
        f = fit(person)
        rec = record(person, f)
        text = json.dumps(rec, indent=1) + '\n'
        out = FITS / f'{person}.json'
        if args.check:
            # The optimiser's last digits follow the numpy/scipy/BLAS build, so a refit is held to
            # the committed fit within FIT_TOLERANCE, not byte for byte (CI and a local run differ).
            committed = out.read_text() if out.exists() else None
            borderline = {a for a, r in f['info_ratio'].items() if BORDERLINE_RATIO[0] < r < BORDERLINE_RATIO[1]}
            drift = [] if committed is None else differences(
                *(sides(x, borderline) for x in (json.loads(committed), rec)),
                loose=set(rec.get('mostly_prior', [])) | borderline)
            if committed is None or drift:
                bad.append(f"{out.relative_to(ROOT)}{' (' + '; '.join(drift[:6]) + ')' if drift else ''}")
            card = json.loads(path.read_text()).get('card')
            if card and committed is not None:
                side = ROOT / card['model'].replace('.jpg', '.json')
                made = json.loads(side.read_text()).get('fit_sha256') if side.exists() else None
                if not (ROOT / card['portrait']).exists() or made != hashlib.sha256(committed.encode()).hexdigest():
                    bad.append(f"{card['model']} (not made from this fit: run node tools/portrait_still.mjs {person})")
        else:
            FITS.mkdir(parents=True, exist_ok=True)
            out.write_text(text)
            print(f'wrote {out.relative_to(ROOT)}')
    if bad:
        print('FAIL face fit is stale:', *bad, '- run python3 tools/fit_portrait_face.py, then tools/human_variation_kit.py')
        return 1
    if args.check:
        print('ok face fits reproduce')
    return 0


if __name__ == '__main__':
    sys.exit(main())
