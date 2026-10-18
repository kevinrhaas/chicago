#!/usr/bin/env python3
"""T-2749: can a LEVEL camera on the 1888 Keith plate draw the loggia at its built size?

T-2725 ruled Keith's loggia column at 2.5 m and laid the plate's 7-9 % long column on its
camera (T-1883: pitched 12.5 degrees up, six controls all on the front's plane), and asked for
a level re-fit with controls off the front's plane. This fits that camera: verticals vertical
(the print's north arris stands at x 1060-1061 from y 870 to y 1250), heading, eye, focal
length and principal point free, pixel aspect free or square, on

  * the front's own controls: the two corner pinnacles' axes, the north arris, and the six
    third-storey lights' heads and sills (their openings, 10.41-12.70 m, as T-2725 read them);
  * the loggia's: the south and north pairs' capital tops and pedestal-cap arrises (heights),
    the north pedestal's north-east arris (its offset from the front's north corner) and the
    south pedestal's south face (both its arrises),

every one read at the plate's native 1559 x 2400 px against the committed GLB's own point
(GLB_SHA256 below; a rebuilt GLB moves the points, and this refuses to run on one until they
are re-read). The fit is repeated on four control sets, because the question is whether the
loggia's scale is the camera's or the model's: a set that leaves the loggia's heights OUT
predicts them instead of fitting them.

  python3 tools/keith_plate_level_fit.py            # print the table
  python3 tools/keith_plate_level_fit.py --write    # and write REPORT

What it does not do: fit house geometry, lens distortion, or a pitched camera; replace the
camera in data/reference_views/keith_house_1808_prairie/inland-1888.json (the eye is not
determined well enough for that, which is one of the things the report shows).
"""
from pathlib import Path
import argparse, hashlib, json, math
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / 'assets/gltf/keith_house_1808_prairie__as_built_1886.glb'
GLB_SHA256 = 'c2153d603a3cfa933a713747db094a38e4762f890dbefc40cb08b50f6099326d'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/inland-1888-level-fit.json'
PRINT_PX = [1559, 2400]

# (label, world [u east, v north, y over grade] read off the GLB, print (x | None, y | None))
FRONT = [
    ('south-east pinnacle axis', [17.86, 0.168, 17.07], (292.5, None)),
    ('north-east pinnacle axis', [17.86, 10.232, 17.07], (1039.0, None)),
    ('front north arris at 12.0 m', [18.0, 10.4, 12.0], (1060.0, None)),
    ('front north arris at 9.5 m', [18.0, 10.4, 9.5], (1061.0, None)),
    ('third-storey light 1 head', [17.8, 2.40, 12.70], (471.0, 810.0)),
    ('third-storey light 1 sill', [17.8, 2.40, 10.41], (None, 975.0)),
    ('third-storey light 2 head', [17.8, 3.52, 12.70], (566.5, 818.0)),
    ('third-storey light 2 sill', [17.8, 3.52, 10.41], (None, 982.0)),
    ('third-storey light 3 head', [17.8, 4.64, 12.70], (638.5, 827.0)),
    ('third-storey light 3 sill', [17.8, 4.64, 10.41], (None, 990.0)),
    ('third-storey light 4 head', [17.8, 5.76, 12.70], (720.0, 838.0)),
    ('third-storey light 4 sill', [17.8, 5.76, 10.41], (None, 995.0)),
    ('third-storey light 5 head', [17.8, 6.88, 12.70], (797.0, 848.0)),
    ('third-storey light 6 head', [17.8, 8.00, 12.70], (866.0, 860.0)),
]
# the loggia as built: front face u 20.7 (out_m 2.7), pedestals 0.9 x 0.6 m at v 7.0-7.9 and
# 9.5-10.4 on a deck at 2.0 m, their cap arris at u 20.78, y 3.0; the paired capitals' top
# front edge at u 20.76, y 5.59
LOGGIA = [
    ('south pair capital top', [20.76, 7.45, 5.59], (None, 1383.5)),
    ('south pedestal cap arris', [20.78, 7.45, 3.0], (None, 1575.0)),
    ('north pair capital top', [20.76, 9.95, 5.59], (None, 1392.0)),
    ('north pedestal cap arris', [20.78, 9.95, 3.0], (None, 1577.0)),
    ('north pedestal north-east arris', [20.7, 10.4, 2.5], (1157.5, None)),
    ('south pedestal south-east arris', [20.7, 7.0, 2.5], (893.0, None)),
    ('south pedestal south-west edge', [20.1, 7.0, 2.5], (868.0, None)),
]
# the print's loggia lengths (capital top to pedestal cap; pedestal cap to its foot on the deck)
PRINT_LENGTHS = {'south': [191.5, 77.0], 'north': [185.0, None]}
HEIGHT = lambda lab: 'capital top' in lab or 'cap arris' in lab
SETS = {
    'all controls': lambda lab: True,
    'loggia heights left out (predicted)': lambda lab: not HEIGHT(lab),
    'sills left out': lambda lab: 'sill' not in lab,
    'sills and loggia heights left out': lambda lab: 'sill' not in lab and not HEIGHT(lab),
}


def project(p, P, aspect):
    eu, ev, ey, yaw, f, cx, cy = p[:7]
    a = p[7] if aspect else 1.0
    t = math.radians(yaw)
    d = np.asarray(P, float) - (eu, ev, ey)
    z = d[0] * math.sin(t) + d[1] * math.cos(t)
    return cx + a * f * (d[0] * math.cos(t) - d[1] * math.sin(t)) / z, cy - f * d[2] / z


def fit(controls, aspect):
    def resid(p):
        r = []
        for _, P, (x, y) in controls:
            px, py = project(p, P, aspect)
            r += ([px - x] if x is not None else []) + ([py - y] if y is not None else [])
        return np.array(r)
    lo = [25, -40, 0.0, 240, 300, -6000, 0] + ([0.6] if aspect else [])
    hi = [90, 15, 5.0, 310, 9000, 9000, 2400] + ([1.4] if aspect else [])
    best = None
    for yaw0 in (272, 280, 290):
        for d0 in (25, 35, 50):
            p0 = [18 + d0, -2, 1.7, yaw0, 72 * d0, 780, 1640] + ([1.0] if aspect else [])
            p0 = [min(max(v, l + 1e-3), h - 1e-3) for v, l, h in zip(p0, lo, hi)]
            s = least_squares(resid, p0, x_scale='jac', max_nfev=20000, bounds=(lo, hi))
            if best is None or s.cost < best.cost:
                best = s
    r = resid(best.x)
    at_bound = [n for n, v, l, h in zip(['eye u', 'eye v', 'eye y', 'yaw', 'f', 'cx', 'cy', 'aspect'],
                                       best.x, lo, hi) if min(v - l, h - v) < 1e-2 * (h - l)]
    return best.x, r, at_bound


def lengths(p, aspect):
    out = {}
    for side, v in (('south', 7.45), ('north', 9.95)):
        _, top = project(p, [20.76, v, 5.59], aspect)
        _, cap = project(p, [20.78, v, 3.0], aspect)
        _, foot = project(p, [20.7, v, 2.0], aspect)
        out[side] = [round(cap - top, 1), round(foot - cap, 1)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    sha = hashlib.sha256(GLB.read_bytes()).hexdigest()
    if sha != GLB_SHA256:
        raise SystemExit(f'{GLB.name} is {sha[:12]}, not the {GLB_SHA256[:12]} these world points were read '
                         'off: re-read them from the rebuilt GLB before fitting')
    rows = []
    for name, keep in SETS.items():
        controls = [c for c in FRONT + LOGGIA if keep(c[0])]
        for aspect in (False, True):
            p, r, at_bound = fit(controls, aspect)
            L = lengths(p, aspect)
            rows.append({
                'controls': name, 'pixel_aspect': 'free' if aspect else 'square', 'n': len(r),
                'rms_px': round(float(np.sqrt((r ** 2).mean())), 2), 'max_px': round(float(abs(r).max()), 2),
                'eye_uvy': [round(float(v), 2) for v in p[:3]], 'yaw_deg': round(float(p[3]), 2),
                'focal_px': round(float(p[4]), 1), 'principal_px': [round(float(p[5]), 1), round(float(p[6]), 1)],
                'aspect': round(float(p[7]), 3) if aspect else 1.0, 'at_bound': at_bound,
                'loggia_px': L,
                'column_long_pct': {s: round(100 * (L[s][0] / PRINT_LENGTHS[s][0] - 1), 1) for s in L},
            })
            q = rows[-1]
            print(f"{name:38s} {q['pixel_aspect']:6s} RMS {q['rms_px']:5.1f} px (n {q['n']})  eye "
                  f"{q['eye_uvy']} yaw {q['yaw_deg']:.0f} f {q['focal_px']:.0f} a {q['aspect']:.2f}  "
                  f"capital-top->cap px S {L['south'][0]:.0f} N {L['north'][0]:.0f} (print 191.5 / 185: "
                  f"{q['column_long_pct']['south']:+.1f} / {q['column_long_pct']['north']:+.1f} %)"
                  + (f"  at bound: {', '.join(at_bound)}" if at_bound else ''))
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_plate_level_fit.py (T-2749): level cameras fitted to the 1888 Keith '
                    'plate on four control sets; read the tool\'s docstring for what is fitted and what is not.',
            'print': 'data/sources/assets/inland_architect_1888_02_keith/plate.jpg', 'print_px': PRINT_PX,
            'glb': str(GLB.relative_to(ROOT)), 'glb_sha256': GLB_SHA256,
            'controls': [{'label': l, 'world_uvy': P, 'print_xy': list(xy)} for l, P, xy in FRONT + LOGGIA],
            'print_loggia_px': PRINT_LENGTHS, 'fits': rows}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
