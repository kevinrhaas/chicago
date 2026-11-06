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
does in the renderer, so the fitted values are the face's shape, not its years. The one_of
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
    return out


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


def fit(person):
    portrait = json.loads((PORTRAITS / f'{person}.json').read_text())
    header, refs, axes = load_kit()
    spec = {a['id']: a for a in json.loads(AXES.read_text())['axes']}
    lm = landmarks()
    kidx = kit_index()
    names = [m['landmark'] for m in portrait['marks']]
    # A landmark is one vertex or the mean of several (a pupil, between the eye's corners).
    members = [[lm[n]] if isinstance(lm[n], int) else list(lm[n]) for n in names]
    rows = np.array(sorted({kidx[v] for m in members for v in m}))
    W = np.zeros((len(names), len(rows)))
    for k, m in enumerate(members):
        for v in m:
            W[k, list(rows).index(kidx[v])] += 1 / len(m)
    obs = np.array([[m['x'], m['y']] for m in portrait['marks']], float)
    sig = np.array([m['sigma_px'] for m in portrait['marks']], float)
    base = W @ refs[rows]
    # The ageing the renderer drives from the person's age at the picture (human-variation.js).
    age = portrait['age_at_picture_years']
    asset_age = 35
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
            base += W @ delta_at({**axes[a['id']], 'kind': 'signed'}, v, 0, rows)
        else:
            base += W @ delta_at(axes[a['id']], v, 0, rows)
    fitted = [a['id'] for a in header['axes'] if not a.get('drive') and a['id'] in portrait['axes']]
    # Each signed axis is piecewise linear; precompute its two halves at +-1 on the landmark rows.
    halves = {}
    for aid in fitted:
        a = axes[aid]
        if a['kind'] == 'one_of':
            halves[aid] = [W @ delta_at(a, 1.0, o, rows) for o in range(len(a['opts_d']))]
        else:
            halves[aid] = (W @ delta_at(a, 1.0, 0, rows), W @ delta_at(a, -1.0, 0, rows))
    spreads = np.array([spec[aid]['spread'] for aid in fitted]) * PRIOR_WIDEN
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
        return np.concatenate([r, v / spreads])

    # A starting camera from the two eyes' midpoints and spacing.
    e = [names.index(n) for n in ('pupil_r', 'pupil_l')]
    s0 = np.linalg.norm(obs[e[1]] - obs[e[0]]) / np.linalg.norm(base[e[1]] - base[e[0]])
    t0 = obs.mean(0)
    best = None
    options = range(len(axes['head_shape']['opts_d'])) if 'head_shape' in fitted else [0]
    for option in options:
        for yaw0 in (-0.6, -0.3, 0.0, 0.3, 0.6):
            p0 = np.concatenate([[yaw0, 0.0, 0.0, s0, *t0], np.zeros(len(fitted))])
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
    values = {aid: round(float(v[k]), 3) + 0.0 for k, aid in enumerate(fitted)}   # + 0.0: no -0.0
    if 'head_shape' in fitted:
        values['head_shape.option'] = int(option)
    per_mark = {n: round(float(np.hypot(*pix[i])), 1) for i, n in enumerate(names)}
    return {
        'portrait': portrait, 'values': values, 'constrained': constrained,
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


def record(person, f):
    p = f['portrait']
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
        'fit': {'rms_px': f['rms_px'], 'per_mark_px': f['per_mark_px'], 'camera': f['camera'],
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
        rec = record(person, fit(person))
        text = json.dumps(rec, indent=1) + '\n'
        out = FITS / f'{person}.json'
        if args.check:
            # The optimiser's last digits follow the numpy/scipy/BLAS build, so a refit is held to
            # the committed fit within FIT_TOLERANCE, not byte for byte (CI and a local run differ).
            committed = out.read_text() if out.exists() else None
            drift = [] if committed is None else differences(json.loads(committed), rec, loose=set(rec.get('mostly_prior', [])))
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
