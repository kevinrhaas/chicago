#!/usr/bin/env python3
"""T-2836: Keith's loggia's place in plan ruled between the first-floor plan, the 1888 plate and the
1965 slide, and the slide's camera re-solved with the bow's principal heads at 4.70 m.

T-2831 found the 1965 slide (a18-gh-1808-porch-1965) glazes its principal lights only to the middle
light's head (4.70 m); re-fitted with the heads there, the loggia's height factor fell to k 1.15,
and with the whole loggia free to move in plan to k 1.04 at about 0.7-0.8 m south. The 1888 plate's
record says its south pair stands about 30 px south of the model's, and that the pedestals are
0.9 m built against about 0.6 m in the plan and the print. This reads the plan and asks which
place the house is built to.

  1. THE PLAN, read off plate.jpg at its native 1559 x 2400 px (the first-floor plan printed under
     the plate; front to the left, south up). The house's side walls, outer faces, are dark runs
     down a column through the plan's hall (x 690-700): their 240 px is the front's 10.4 m, so
     v = (row - south wall) / (px per m). Down x 612-626, through the loggia's front pedestals,
     each pedestal is a dark run (luminance under HALF, a half-max edge); each one's middle is
     its pair's centre (the plan draws the pair as one block on its pedestal).

  2. THE PLATE RE-FITTED (tools/keith_plate_level_fit.py's level camera, square pixels, its 27
     coordinates) with the loggia's world points moved to the plan's: the pairs' capital tops and
     cap arrises over the plan's centres, the south pedestal's south face and the north
     pedestal's north face at the plan's. The front's controls are unchanged, so what moves
     the fit is only the loggia's place.

  3. THE 1965 SLIDE RE-FITTED (tools/keith_1965_cause_fit.py's level camera on T-2764's 29
     coordinates) with the principal heads at 4.70 m (T-2831), on the built layout and on the
     plan's: shafts at their pair's centre +-0.225 m as built, the south pedestal's box at the
     plan's v extent; with nothing more free, with k on the loggia's heights, and with the whole
     loggia free to move in plan (dv).

  python3 tools/keith_loggia_plan_rule.py            # print the reading
  python3 tools/keith_loggia_plan_rule.py --write    # and write REPORT
  python3 tools/keith_loggia_plan_rule.py --camera   # and write the 1965 camera file the ruling takes

What it does not do: move the model. A ruling that moves the loggia is the K07 kit's to build.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keith_1965_level_fit as lf  # noqa: E402  T-2764's controls
import keith_1965_cause_fit as cf  # noqa: E402  T-2830's fitter
import keith_plate_level_fit as pf  # noqa: E402  T-2763's plate fitter

ROOT = Path(__file__).resolve().parents[1]
PLATE = ROOT / 'data/sources/assets/inland_architect_1888_02_keith/plate.jpg'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/keith-loggia-plan-rule.json'
FRONT_M = 10.4
HALF = 128            # a dark run's edge: luminance under half of white
WALLS_X = (690, 701)  # a column through the plan's hall, crossing both side walls
WALLS_ROWS = (2030, 2294)  # the page's rule under the plan is dark from 2297
PEDS_X = (612, 627)   # a column through the loggia's two front pedestals
PEDS_ROWS = (2190, 2300)
# the built loggia (T-2763/K07): pedestals 0.9 x 0.6 m flush with the deck's corners, v 7.0-7.9
# and 9.5-10.4, the deck's front at u 20.7, the shafts at u 20.40, +-0.225 m about each pair
BUILT = {'south': (7.0, 7.9), 'north': (9.5, 10.4)}
# the plate's own pedestals, at the width it and the plan draw (0.6 m) but flush with the deck's
# corners as K07 lays them: what the plate's committed camera reads (its fronts x 889-937 and
# 1112-1155, 48 and 44 px, from the south face at v 7.0 and to the north face at 10.4)
FLUSH = {'south': (7.0, 7.6), 'north': (9.8, 10.4)}
DECK_FRONT, PED_DEPTH, SHAFT_OFF = 20.7, 0.6, 0.225


def dark_runs(x, rows):
    a = np.asarray(Image.open(PLATE).convert('L'), float)
    col = a[rows[0]:rows[1], x[0]:x[1]].mean(1)
    runs, start = [], None
    for i, v in enumerate(col):
        if v < HALF and start is None:
            start = i
        if v >= HALF and start is not None:
            runs.append((rows[0] + start - 0.5, rows[0] + i - 0.5))
            start = None
    if start is not None:
        runs.append((rows[0] + start - 0.5, rows[1] - 0.5))
    return runs


def read_plan():
    walls = dark_runs(WALLS_X, WALLS_ROWS)
    south, north = walls[0][0], walls[-1][1]   # the side walls' outer faces
    ppm = (north - south) / FRONT_M
    peds = [r for r in dark_runs(PEDS_X, PEDS_ROWS) if r[1] - r[0] >= 6]
    if len(peds) != 2:
        raise SystemExit(f'expected two pedestal runs down x {PEDS_X}, read {peds}')
    v = lambda y: round((y - south) / ppm, 3)
    plan = {k: (v(a), v(b)) for k, (a, b) in zip(('south', 'north'), peds)}
    return {'walls_rows': [south, north], 'px_per_m': round(ppm, 2),
            'pedestal_rows': {k: list(r) for k, r in zip(('south', 'north'), peds)},
            'pedestals_v': {k: list(p) for k, p in plan.items()},
            'pedestal_widths_m': {k: round(p[1] - p[0], 2) for k, p in plan.items()},
            'pair_centres_v': {k: round((p[0] + p[1]) / 2, 3) for k, p in plan.items()}}, plan


def centre(p):
    return (p[0] + p[1]) / 2


# --- the plate --------------------------------------------------------------------------------
def plate_controls(lay):
    s, n = centre(lay['south']), centre(lay['north'])
    moved = {'south pair capital top': [20.625, s, 5.095], 'south pedestal cap arris': [20.7, s, 2.88],
             'north pair capital top': [20.625, n, 5.095], 'north pedestal cap arris': [20.7, n, 2.88],
             'north pedestal north-east arris': [20.7, lay['north'][1], 2.5],
             'south pedestal south-east arris': [20.7, lay['south'][0], 2.5],
             'south pedestal south-west edge': [20.1, lay['south'][0], 2.5]}
    return pf.FRONT + [(lab, moved[lab], xy) for lab, _, xy in pf.LOGGIA]


def plate_fit(lay):
    controls = plate_controls(lay)
    p, r, at_bound = pf.fit(controls, False)
    labels = [lab + suf for lab, _, (x, y) in controls
              for suf, c in ((' x', x), (' y', y)) if c is not None]
    lp = {lab: round(float(v), 1) for lab, v in zip(labels, r)
          if ('pedestal' in lab or 'pair' in lab)}
    # where this camera draws each pair's centre, against the print's (the pair's shafts' outer
    # silhouettes' middle, read off the plate at x 875-932 and 1095-1148 on the shafts' mid rows)
    xs = {k: round(pf.project(p, [20.4, centre(lay[k]), 4.0], False)[0], 1) for k in ('south', 'north')}
    return {'rms_px': round(float(np.sqrt((r ** 2).mean())), 2), 'max_px': round(float(abs(r).max()), 2),
            'eye': [round(float(v), 3) for v in p[:3]], 'yaw': round(float(p[3]), 2), 'at_bound': at_bound,
            'loggia_residuals_px': lp, 'pair_centre_x': xs}


# --- the 1965 slide -------------------------------------------------------------------------
def slide_points(lay):
    s, n = centre(lay['south']), centre(lay['north'])
    sil = [('south pair south shaft, left silhouette', 'shaft', [(20.40, s - SHAFT_OFF)], 'left', 355.8),
           ('south pair north shaft, right silhouette', 'shaft', [(20.40, s + SHAFT_OFF)], 'right', 383.6),
           ('north pair south shaft, left silhouette', 'shaft', [(20.40, n - SHAFT_OFF)], 'left', 408.5),
           ('north pair north shaft, right silhouette', 'shaft', [(20.40, n + SHAFT_OFF)], 'right', 432.5)]
    box = [(DECK_FRONT - PED_DEPTH, lay['south'][0]), (DECK_FRONT, lay['south'][1])]
    sil += [('south pedestal, left silhouette', 'box', box, 'left', 352.5),
            ('south pedestal, right silhouette', 'box', box, 'right', 386.5)]
    hts = [('south pair capital top', [20.625, s, 5.095], 134.5), ('north pair capital top', [20.625, n, 5.095], 152.5),
           ('south pedestal cap arris', [20.7, s, 2.88], 235.5), ('north pedestal cap arris', [20.7, n, 2.88], 241.0)]
    return sil, hts, (s, n)


def residuals_for(lay):
    sil, hts, pairs = slide_points(lay)
    mid = (pairs[0] + pairs[1]) / 2

    def residuals(c):
        out = []
        for lab, deg, half, y, (xl, xr) in lf.JAMBS:
            xs = {r: (cf.project(c, lf.on_bow(deg - half, r, y))[0], cf.project(c, lf.on_bow(deg + half, r, y))[0])
                  for r in (lf.R_SASH, lf.R)}
            a, b = xs[lf.R_SASH], xs[lf.R]
            out += [(lab + ' left jamb', max(min(a), min(b)) - xl), (lab + ' right jamb', min(max(a), max(b)) - xr)]
        for lab, deg, y, py in lf.HEADS:
            y = c['hh'] if ('principal' in lab and 'head' in lab) else y
            out.append((lab, cf.project(c, lf.on_bow(deg, lf.R_SASH, y))[1] - py))
        for lab, P, (x, _) in lf.FRONT:
            out.append((lab, cf.project(c, P)[0] - x))
        for lab, kind, pts, side, x in sil:
            if kind == 'box':
                (u0, v0), (u1, v1) = pts
                xs = [cf.project(c, [u + c['du'], v + c['dv'], 2.5])[0] for u in (u0, u1) for v in (v0, v1)]
            else:
                (u, v), = pts
                u, v = u + c['du'], v + c['dv']
                d = np.array([u - c['u'], v - c['v']])
                nrm = np.array([-d[1], d[0]]) / np.linalg.norm(d)
                xs = [cf.project(c, [u + s * lf.SHAFT_R * nrm[0], v + s * lf.SHAFT_R * nrm[1], lf.SHAFT_Y])[0]
                      for s in (-1, 1)]
            out.append((lab, (min(xs) if side == 'left' else max(xs)) - x))
        for lab, P, y in hts:
            out.append((lab, cf.project(c, [P[0] + c['du'], P[1] + c['dv'], lf.DECK + c['k'] * (P[2] - lf.DECK)])[1] - y))
        return out
    return residuals, mid


SLIDE_FITS = [([], 'nothing more free'), (['k'], 'k on the loggia\'s heights'), (['dv'], 'the loggia moved in plan (dv)'),
              (['dv', 'k'], 'dv and k')]


def slide_fit(lay, free):
    residuals, _ = residuals_for(lay)
    keep = cf.residuals
    cf.residuals, cf.DEFAULT['hh'] = residuals, 4.70
    try:
        c, res, at_bound = cf.fit(free)
    finally:
        cf.residuals, cf.DEFAULT['hh'] = keep, 5.30
    r = np.array([v for _, v in res])
    d = dict(res)
    return c, {'free': free, 'rms_px': round(float(np.sqrt((r ** 2).mean())), 2), 'max_px': round(float(abs(r).max()), 2),
               'worst': max(d, key=lambda k: abs(d[k])),
               'params': {n: round(float(c[n]), 3) for n in free}, 'eye_uv': [round(float(c['u']), 2), round(float(c['v']), 2)],
               'yaw': round(float(c['yaw']), 2), 'at_bound': at_bound,
               'loggia_dx_px': {k: round(float(v), 1) for k, v in d.items() if 'silhouette' in k},
               'loggia_dy_px': {k: round(float(v), 1) for k, v in d.items() if 'capital' in k or 'cap arris' in k},
               'bow_heads_dy_px': {k: round(float(v), 1) for k, v in d.items() if 'principal' in k and ('head' in k or 'sill' in k)}}


SOLVE = ("T-2836 re-solve (tools/keith_loggia_plan_rule.py; report docs/RESEARCH/photo-match/keith_house_1808_prairie/"
         "keith-loggia-plan-rule.json): T-2764's level camera (roll fitted, prior 0 +/- 1.5 degrees; eye height 1.7 m "
         "kept; principal x 337) on all 29 of its coordinates, read off the slide by luminance profile, with two "
         "changes. The bow's three principal heads are paired with the middle light's head, 4.70 m, where this slide "
         "stops the glass (T-2831: 0.664 of the sill-to-string-course span; the top lights are blind by 1965), not the "
         "5.30 m head the 1888 plate glazes. The loggia's world points stand at the first-floor plan's place "
         "(T-2836's ruling): its front pedestals about 0.6 m across at v {s0:.2f}-{s1:.2f} and {n0:.2f}-{n1:.2f}, the "
         "pairs over their middles, where the GLB still stands them 0.9 m wide at v 7.0-7.9 and 9.5-10.4, so this "
         "camera does not lean on the loggia the plan refuses. Free: u, v, yaw, roll, f, cy. Coordinate RMS "
         "{rms:.2f} px, max {mx:.1f} px ({worst}). On the as-built loggia the same controls fit at 4.66 px RMS (max "
         "10.2). Replaces T-2764's fit (3.47 px on the 5.30 m heads). 1965 colour photograph, Glessner House Museum. "
         "The print is blue-cast and the fa\u00e7ade in shade; ratios constrain a pale neutral granite, not a "
         "calibrated quarry colour. Later iron infill and ivy are not copied into 1904.")


def camera_file(c, q, plan):
    cam = json.loads(lf.CAMERA.read_text())
    right, up, fwd = cf.basis(c['yaw'], c['roll'], 0.0)
    cam.update({'principal_px': [float(c['cx']), float(c['cy'])], 'focal_px': float(c['f']),
                'eye': [float(c['u']), float(c['v']), float(c['y'])], 'yaw_deg': float(c['yaw']),
                'basis_right_up_forward': [list(map(float, right)), list(map(float, up)), list(map(float, fwd))]})
    cam['solve'] = SOLVE.format(
        s0=plan['south'][0], s1=plan['south'][1], n0=plan['north'][0], n1=plan['north'][1],
        rms=q['rms_px'], mx=q['max_px'], worst=q['worst'])
    return cam


# --- the slide's grain (the joints, the upper capitals and the head bands) -------------------
# heights over grade, as built: the third storey's sills and heads (T-2763/T-2813), the course
# pair the front and bow lay below the third floor (T-2584: 0.49 and 0.195 m), a 10 mm joint
GRAIN_HEIGHTS = {'third-storey sill (projecting arris)': 10.36, 'third-storey head': 12.655}


def grain(c):
    """Where the crown's members fall in this frame, and what a course and a joint come to."""
    out = {}
    for lab, z in GRAIN_HEIGHTS.items():
        out[lab + ', row on the flat front (u 18.0, v 8.0)'] = round(cf.project(c, [18.0, 8.0, z])[1], 1)
        out[lab + ', row on the bow (-33 degree light)'] = round(cf.project(c, lf.on_bow(-33, lf.R, z))[1], 1)
    for lab, P in (('bow face, -33 degree light', lf.on_bow(-33, lf.R, 4.0)), ('loggia, south pair', [20.4, 7.03, 4.0])):
        ppm = abs(cf.project(c, [P[0], P[1], P[2] + 0.5])[1] - cf.project(c, [P[0], P[1], P[2] - 0.5])[1])
        out[f'px per m, vertical, {lab}'] = round(ppm, 1)
        out[f'thin course (0.195 m), {lab}, px'] = round(0.195 * ppm, 1)
        out[f'a 10 mm joint, {lab}, px'] = round(0.01 * ppm, 2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    ap.add_argument('--camera', action='store_true', help='print the chosen 1965 camera file')
    args = ap.parse_args()
    reading, plan = read_plan()
    print(f"plan: walls at rows {reading['walls_rows']} ({reading['px_per_m']} px/m); pedestals "
          f"{reading['pedestals_v']} (widths {reading['pedestal_widths_m']}), pair centres {reading['pair_centres_v']} "
          f"against the built {dict((k, centre(v)) for k, v in BUILT.items())}")
    layouts = {'built': BUILT, 'flush 0.6': FLUSH, 'plan': plan}
    plate = {k: plate_fit(lay) for k, lay in layouts.items()}
    for k, q in plate.items():
        print(f"plate, {k:9s} RMS {q['rms_px']:5.2f} max {q['max_px']:5.1f} eye {q['eye']} pairs drawn at x {q['pair_centre_x']}"
              f"  loggia {q['loggia_residuals_px']}")
    slide, cams = {}, {}
    for k, lay in layouts.items():
        for free, label in SLIDE_FITS:
            c, q = slide_fit(lay, free)
            slide[f'{k}: {label}'] = q
            cams[(k, tuple(free))] = c
            print(f"1965, heads 4.70, {k:9s} {label:30s} RMS {q['rms_px']:5.2f} max {q['max_px']:5.1f} {q['params']} "
                  f"eye {q['eye_uv']}  heights {list(q['loggia_dy_px'].values())}  worst {q['worst']}")
    chosen = slide['plan: nothing more free']
    g = grain(cams[('plan', ())])
    for k, v in g.items():
        print(f'grain: {k}: {v}')
    if args.camera:
        lf.CAMERA.write_text(json.dumps(camera_file(cams[('plan', ())], chosen, plan), indent=2) + '\n')
        print(f'wrote {lf.CAMERA.relative_to(ROOT)}')
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_loggia_plan_rule.py (T-2836): the loggia\'s front pedestals read off the '
                    'first-floor plan under the 1888 plate; the plate and the 1965 slide (principal heads at 4.70 m) '
                    're-fitted with the loggia as built and at the plan\'s place. Read the tool\'s docstring.',
            'glb': str(lf.GLB.relative_to(ROOT)), 'glb_sha256': hashlib.sha256(lf.GLB.read_bytes()).hexdigest(),
            'built': {k: list(v) for k, v in BUILT.items()}, 'plan': reading,
            'plate_refits': plate, 'slide_refits': slide, 'camera_chosen': 'plan: nothing more free',
            'slide_grain_on_the_chosen_camera': g}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
