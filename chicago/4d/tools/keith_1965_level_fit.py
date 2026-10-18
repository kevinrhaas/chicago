#!/usr/bin/env python3
"""T-2764: the 1965 close view of Keith's loggia (a18-gh-1808-porch-1965) fitted with depth at the loggia.

T-2579 fitted this view with a level camera on seven controls, only one of them on the loggia, so
its depth there was under-determined: T-2725 found it drew the loggia's column and pedestal
alike 12-15 % short, and T-2763 then lowered the loggia to 0.88 of its height on the 1888 plate's
level fits. T-2765 moved the bow's lights to the second storey's bearings, so the camera's three
bow controls stood on lights that no longer exist. This re-fits the camera (level, roll fitted,
principal x at the frame's centre) on

  * the bow, re-picked on the rebuilt GLB: the three principal lights it sees (-33, -11 and
    11 degrees) by both jambs, read across the sashes at y 205-225 as where the white frame
    meets the stone, and by their heads; the three basement lights by both jambs (y 296-304)
    and the first two by their heads; the bow's north junction with the flat front;
  * the loggia's PLAN, which is what gives the camera depth there: both pairs' shafts by
    their outer silhouettes at 4.0 m (y 180-190), and the south pedestal's silhouette (y 245-255);
  * the loggia's HEIGHTS: both pairs' capital tops (the abacus, as T-2763 took it on the plate)
    and both pedestals' cap arrises,

every edge read off the 675 x 456 slide by luminance profile (the numbers below), and every
world point off the committed GLB (GLB_SHA256; a rebuilt GLB moves them, and this refuses to
run on one until they are re-read). A jamb is drawn where the frame meets the stone, so its
model edge is whichever of the sash's edge (r 3.09) and the face's arris (r 3.204) the camera
sees: the inner of the two. A shaft's or the pedestal's silhouette is its extreme seen from the
eye, computed for the eye being fitted.

The fit is repeated on control sets that leave the loggia's heights OUT, so they are predicted
rather than fitted — the question is whether a camera given depth at the loggia draws the
as-built pedestal (0.88 m, cap 2.88 over a 2.0 m deck) at the print's ~38-41 px — with the eye's
height fixed at 1.7 m (T-2579's) and free. LOGGIA_SCALE adds one free factor k on the loggia's
heights over its deck, as tools/keith_plate_level_fit.py does on the plate.

  python3 tools/keith_1965_level_fit.py            # print the table
  python3 tools/keith_1965_level_fit.py --write    # and write REPORT
  python3 tools/keith_1965_level_fit.py --camera   # print the chosen fit as a camera file

What it does not do: fit lens distortion, house geometry, or a pitched camera.
"""
from pathlib import Path
import argparse, hashlib, json, math
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / 'assets/gltf/keith_house_1808_prairie__as_built_1886.glb'
GLB_SHA256 = '8f38ad9020c2156e21229cd6f2a729365c0f6a6a457acc385162951b76c8663e'  # T-2765's bow, T-2763's loggia
CAMERA = ROOT / 'data/reference_views/keith_house_1808_prairie/a18-gh-1808-porch-1965.json'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/a18-gh-1808-porch-1965-level-fit.json'
PRINT_PX = [675, 456]
CX = 337.0
CHOSEN = 'bow and loggia plan, heights predicted', 'fixed'   # the set the camera file takes: the eye's
# height is not determined by these controls (free, it wanders to 0.6 m with cy 320), so it keeps T-2579's 1.7 m

# the bow (tools/keith_bow_lights_read.py): chord 5.0 m, rise 1.2 m; the face at r 3.204, the
# sash's outer edge at r 3.09; principal lights 0.9 m (8.05 degrees half-width on the face),
# head 5.30, sill 2.358; basement lights 0.73 m (6.53), head 1.30
R = (2.5 ** 2 + 1.2 ** 2) / (2 * 1.2)
CU, CV = 18.0 + 1.2 - R, 3.7
R_SASH = 3.09
# (label, bearing, half-width deg, height read at, (left x, right x))
JAMBS = [
    ('principal light -33', -33, 8.05, 4.0, (154.5, 194.5)),
    ('principal light -11', -11, 8.05, 4.0, (214.5, 239.5)),
    ('principal light 11', 11, 8.05, 4.0, (257.5, 267.5)),
    ('basement light -33', -33, 6.53, 0.8, (160.5, 187.5)),
    ('basement light -11', -11, 6.53, 0.8, (217.5, 235.5)),
    ('basement light 11', 11, 6.53, 0.8, (259.5, 269.5)),
]
# (label, bearing, height, print y) — read down each light's centre
HEADS = [
    ('principal light -33 head', -33, 5.30, 134.0),
    ('principal light -33 sill', -33, 2.358, 244.5),
    ('principal light -11 head', -11, 5.30, 140.0),
    ('principal light 11 head', 11, 5.30, 147.5),
    ('basement light -33 head', -33, 1.30, 292.0),
    ('basement light -11 head', -11, 1.30, 291.5),
]
FRONT = [('bow north junction', [18.0, 6.2, 4.0], (284.5, None))]
# the loggia as built (T-2763): shafts r 0.151 at 4.0 m, centres u 20.40 at v 7.22 / 7.675 (south
# pair) and 9.72 / 10.175 (north pair); the south pedestal 20.1-20.7 x 7.0-7.9; the abacus's front
# edge u 20.625 at 5.095; the pedestals' cap arris u 20.7 at 2.88 over the deck at 2.0
SHAFT_R, SHAFT_Y = 0.151, 4.0
SILHOUETTES = [  # (label, kind, centres or corners, side, print x)
    ('south pair south shaft, left silhouette', 'shaft', [(20.40, 7.22)], 'left', 355.8),
    ('south pair north shaft, right silhouette', 'shaft', [(20.40, 7.675)], 'right', 383.6),
    ('north pair south shaft, left silhouette', 'shaft', [(20.40, 9.72)], 'left', 408.5),
    ('north pair north shaft, right silhouette', 'shaft', [(20.40, 10.175)], 'right', 432.5),
    ('south pedestal, left silhouette', 'box', [(20.1, 7.0), (20.7, 7.0), (20.1, 7.9), (20.7, 7.9)], 'left', 352.5),
    ('south pedestal, right silhouette', 'box', [(20.1, 7.0), (20.7, 7.0), (20.1, 7.9), (20.7, 7.9)], 'right', 386.5),
]
HEIGHTS = [
    ('south pair capital top', [20.625, 7.45, 5.095], 134.5),
    ('north pair capital top', [20.625, 9.95, 5.095], 152.5),
    ('south pedestal cap arris', [20.7, 7.45, 2.88], 235.5),
    ('north pedestal cap arris', [20.7, 9.95, 2.88], 241.0),
]
DECK = 2.0
# the print's loggia lengths: capital top to cap arris, and cap arris to the joint at the
# pedestal's foot (y 273-274 under the south pair; T-2725 read about 41 px from y 234.5)
PRINT_LENGTHS = {'south': [101.0, 38.5], 'north': [88.5, None]}
SETS = {
    'bow only (T-2579\'s kind, re-picked)': ('bow',),
    'bow and loggia plan, heights predicted': ('bow', 'plan'),
    'all controls': ('bow', 'plan', 'heights'),
}


def basis(yaw, roll):
    t, r = math.radians(yaw), math.radians(roll)
    fwd = np.array([math.sin(t), math.cos(t), 0.0])
    right0, up0 = np.array([math.cos(t), -math.sin(t), 0.0]), np.array([0.0, 0.0, 1.0])
    return math.cos(r) * right0 + math.sin(r) * up0, -math.sin(r) * right0 + math.cos(r) * up0, fwd


def project(p, P):
    """p = eye u, v, y, yaw, roll, f, cy, and optionally a pixel aspect (horizontal over vertical)."""
    eu, ev, ey, yaw, roll, f, cy = p[:7]
    a = p[7] if len(p) > 7 else 1.0
    right, up, fwd = basis(yaw, roll)
    d = np.asarray(P, float) - (eu, ev, ey)
    z = d @ fwd
    return CX + a * f * (d @ right) / z, cy - f * (d @ up) / z


def on_bow(deg, r, y):
    t = math.radians(deg)
    return [CU + r * math.cos(t), CV + r * math.sin(t), y]


def jamb_x(p, deg, half, y):
    """The visible opening's left and right x: the inner of the sash's and the face's edges."""
    xs = {r: (project(p, on_bow(deg - half, r, y))[0], project(p, on_bow(deg + half, r, y))[0])
          for r in (R_SASH, R)}
    a, b = xs[R_SASH], xs[R]
    return max(min(a), min(b)), min(max(a), max(b))


def silhouette_x(p, kind, pts, side):
    if kind == 'box':
        xs = [project(p, [u, v, 2.5])[0] for u, v in pts]
        return min(xs) if side == 'left' else max(xs)
    (u, v), = pts
    d = np.array([u - p[0], v - p[1]])
    n = np.array([-d[1], d[0]]) / np.linalg.norm(d)      # perpendicular to the sightline, in plan
    xs = [project(p, [u + s * SHAFT_R * n[0], v + s * SHAFT_R * n[1], SHAFT_Y])[0] for s in (-1, 1)]
    return min(xs) if side == 'left' else max(xs)


def scaled(P, k):
    return [P[0], P[1], DECK + k * (P[2] - DECK)]


def residuals(p, groups, k=1.0):
    out = []
    if 'bow' in groups:
        for lab, deg, half, y, (xl, xr) in JAMBS:
            a, b = jamb_x(p, deg, half, y)
            out += [(lab + ' left jamb', a - xl), (lab + ' right jamb', b - xr)]
        for lab, deg, y, py in HEADS:
            out.append((lab, project(p, on_bow(deg, R_SASH, y))[1] - py))
        for lab, P, (x, _) in FRONT:
            out.append((lab, project(p, P)[0] - x))
    if 'plan' in groups:
        for lab, kind, pts, side, x in SILHOUETTES:
            out.append((lab, silhouette_x(p, kind, pts, side) - x))
    if 'heights' in groups:
        for lab, P, y in HEIGHTS:
            out.append((lab, project(p, scaled(P, k))[1] - y))
    return out


def fit(groups, free_height, with_k=False, aspect=False):
    """Level camera, roll fitted (prior 0 +/- 1.5 degrees, as T-2579); returns params, k, residuals."""
    names = ['eye u', 'eye v', 'eye y', 'yaw', 'roll', 'f', 'cy'] + (['aspect'] if aspect else []) + \
            (['k'] if with_k else [])

    def unpack(q):
        n = 7 if free_height else 6
        p = list(q[:7]) if free_height else [q[0], q[1], 1.7, *q[2:6]]
        return p + ([q[n]] if aspect else []), (q[-1] if with_k else 1.0)

    def resid(q):
        p, k = unpack(q)
        return np.array([r for _, r in residuals(p, groups, k)] + [p[4] / 1.5])
    lo = [22, -30] + ([0.5] if free_height else []) + [270, -4, 250, 100] + ([0.8] if aspect else []) + \
         ([0.6] if with_k else [])
    hi = [60, 15] + ([4.0] if free_height else []) + [340, 4, 2500, 450] + ([1.25] if aspect else []) + \
         ([1.4] if with_k else [])
    best = None
    for yaw0 in (300, 308, 316):
        for d0 in (10, 16, 24):
            t = math.radians(yaw0)
            q0 = [20.0 - d0 * math.sin(t), 4.0 - d0 * math.cos(t)] + ([1.7] if free_height else []) + \
                 [yaw0, 1.0, 38 * d0, 277] + ([1.0] if aspect else []) + ([1.0] if with_k else [])
            q0 = [min(max(v, l + 1e-3), h - 1e-3) for v, l, h in zip(q0, lo, hi)]
            s = least_squares(resid, q0, x_scale='jac', max_nfev=20000, bounds=(lo, hi))
            if best is None or s.cost < best.cost:
                best = s
    p, k = unpack(best.x)
    free = [n for n in names if free_height or n != 'eye y']
    at_bound = [n for n, v, l, h in zip(free, best.x, lo, hi) if min(v - l, h - v) < 1e-2 * (h - l)]
    return p, k, residuals(p, groups, k), at_bound


def lengths(p, k=1.0):
    out = {}
    for side, v in (('south', 7.45), ('north', 9.95)):
        top = project(p, scaled([20.625, v, 5.095], k))[1]
        cap = project(p, scaled([20.7, v, 2.88], k))[1]
        foot = project(p, [20.7, v, DECK])[1]
        out[side] = [round(cap - top, 1), round(foot - cap, 1)]
    return out


def predicted(p, k=1.0):
    return [{'control': lab, 'print_y': y, 'model_y': round(float(project(p, scaled(P, k))[1]), 1),
             'dy_px': round(float(project(p, scaled(P, k))[1] - y), 1)} for lab, P, y in HEIGHTS]


def row(name, height, p, k, res, at_bound):
    r = np.array([v for _, v in res])
    L = lengths(p, k)
    return {'controls': name, 'eye_height': height, 'n': len(r),
            'rms_px': round(float(np.sqrt((r ** 2).mean())), 2), 'max_px': round(float(abs(r).max()), 2),
            'eye_uvy': [round(float(v), 2) for v in p[:3]], 'yaw_deg': round(float(p[3]), 2),
            'roll_deg': round(float(p[4]), 2), 'focal_px': round(float(p[5]), 1),
            'principal_px': [CX, round(float(p[6]), 1)], 'k': round(float(k), 3), 'at_bound': at_bound,
            'loggia_px': L, 'print_loggia_px': PRINT_LENGTHS,
            'column_short_pct': {s: round(100 * (L[s][0] / PRINT_LENGTHS[s][0] - 1), 1) for s in L},
            'pedestal_short_pct': round(100 * (L['south'][1] / PRINT_LENGTHS['south'][1] - 1), 1),
            'loggia_heights': predicted(p, k),
            'residual_px': {lab: round(float(v), 1) for lab, v in res}}


def inside_the_loggia(p):
    """Each of the loggia's own print lengths over its built length, in px per metre: the column and
    the pedestal by height, and the south pair's and the south pedestal's silhouettes by their widths
    across the sightline from the chosen eye (which only the heading enters). One object at one depth
    reads one scale; a spread is the model's proportions disagreeing with the print's."""
    d = np.array([20.40 - p[0], 7.45 - p[1]])
    s = np.array([-d[1], d[0]]) / np.linalg.norm(d)          # across the sightline, in plan
    across = lambda pts: max(np.dot(pt, s) for pt in pts) - min(np.dot(pt, s) for pt in pts)
    ped = across([np.array(c) for c in SILHOUETTES[4][2]])
    pair = across([np.array([20.40, 7.22]), np.array([20.40, 7.675])]) + 2 * SHAFT_R
    reads = [('column, capital top to cap', PRINT_LENGTHS['south'][0], 5.095 - 2.88),
             ('pedestal, cap to foot', PRINT_LENGTHS['south'][1], 2.88 - DECK),
             ('south pair, silhouette across', 383.6 - 355.8, pair),
             ('south pedestal, silhouette across', 386.5 - 352.5, ped)]
    return [{'what': w, 'print_px': round(px, 1), 'built_m': round(float(m), 3), 'px_per_m': round(float(px / m), 1)}
            for w, px, m in reads]


def camera(p):
    right, up, fwd = basis(p[3], p[4])
    cam = json.loads(CAMERA.read_text())
    cam.update({'principal_px': [CX, float(p[6])], 'focal_px': float(p[5]), 'eye': [float(v) for v in p[:3]],
                'yaw_deg': float(p[3]) % 360, 'basis_right_up_forward': [right.tolist(), up.tolist(), fwd.tolist()]})
    return cam


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    ap.add_argument('--camera', action='store_true', help='print the chosen fit as a camera file')
    args = ap.parse_args()
    sha = hashlib.sha256(GLB.read_bytes()).hexdigest()
    if sha != GLB_SHA256:
        raise SystemExit(f'{GLB.name} is {sha[:12]}, not the {GLB_SHA256[:12]} these world points were read '
                         'off: re-read them from the rebuilt GLB before fitting')
    rows, chosen = [], None
    for name, groups in SETS.items():
        for free_height in (False, True):
            p, k, res, at_bound = fit(groups, free_height)
            q = row(name, 'free' if free_height else 'fixed 1.7 m', p, k, res, at_bound)
            rows.append(q)
            if (name, 'free' if free_height else 'fixed') == CHOSEN:
                chosen = p
            L = q['loggia_px']
            print(f"{name:40s} h {q['eye_height']:11s} RMS {q['rms_px']:4.1f} max {q['max_px']:4.1f} px (n {q['n']}) "
                  f"eye {q['eye_uvy']} yaw {q['yaw_deg']:.1f} roll {q['roll_deg']:+.2f} f {q['focal_px']:.0f} "
                  f"cy {q['principal_px'][1]:.0f} | column S {L['south'][0]:.0f}/101 N {L['north'][0]:.0f}/88.5, "
                  f"pedestal {L['south'][1]:.0f}/38.5 px" + (f"  at bound: {', '.join(at_bound)}" if at_bound else ''))
    scale = []
    for label, free_height, with_k, aspect in (
            ('all controls, the loggia\'s heights scaled by k over its deck', False, True, False),
            ('all controls, the loggia\'s heights scaled by k over its deck', True, True, False),
            ('all controls, pixel aspect free (a resampled scan?)', False, False, True),
            ('all controls, pixel aspect free and k', False, True, True)):
        p, k, res, at_bound = fit(SETS['all controls'], free_height, with_k=with_k, aspect=aspect)
        q = row(label, 'free' if free_height else 'fixed 1.7 m', p, k, res, at_bound)
        q['aspect'] = round(float(p[7]), 3) if aspect else 1.0
        scale.append(q)
        print(f"{label[:40]:40s} h {q['eye_height']:11s} RMS {q['rms_px']:4.1f} max {q['max_px']:4.1f} px "
              f"eye {q['eye_uvy']} yaw {q['yaw_deg']:.1f} f {q['focal_px']:.0f}  k {q['k']:.3f}  aspect {q['aspect']:.3f}"
              + (f"  at bound: {', '.join(at_bound)}" if at_bound else ''))
    within = inside_the_loggia(chosen)
    print('read inside the loggia, no camera but its heading (px per metre at the loggia):',
          ', '.join(f"{w['what']} {w['px_per_m']}" for w in within))
    if args.camera:
        print(json.dumps(camera(chosen), indent=2))
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_1965_level_fit.py (T-2764): level cameras fitted to the 1965 close '
                    'view of Keith\'s loggia with controls on the loggia\'s plan; read the tool\'s docstring '
                    'for what is fitted and what is not.',
            'print': 'data/sources/assets/inland_architect_1888_02_keith/a18-gh-1808-porch-1965.jpg',
            'print_px': PRINT_PX, 'glb': str(GLB.relative_to(ROOT)), 'glb_sha256': GLB_SHA256,
            'chosen': {'controls': CHOSEN[0], 'eye_height': CHOSEN[1]},
            'fits': rows, 'loggia_scale_fits': scale,
            'inside_the_loggia': within}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
