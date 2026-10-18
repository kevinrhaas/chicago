#!/usr/bin/env python3
"""T-2765: where Keith's bow lights stand on the 1888 plate, judged on T-2762's level fits.

The bow's principal and basement lights were built at -27, 0 and 27 degrees about the bow's
centre (chord 5.0 m, rise 1.2 m, so a 3.204 m radius centred 3.7 m from the south corner), and
the second storey's four at -33, -11, 11 and 33. On the plate, read at its native 1559 px, the
three lights of each lower storey that the street tree leaves visible stand plumb under the
second storey's first three. This reads every opening's edges, then for each of the level
cameras tools/keith_plate_level_fit.py fits (square pixels, the four control sets):

  * the edge residual of the lower storeys' lights at the as-built bearings and widths, and at
    the second storey's bearings with the width that fits best, beside the second storey's own
    residual at its built bearings (the fit's floor at the bow);
  * the heights, read with no camera at all: a level view at one depth draws height linearly,
    so the six heads and sills down the south light's column are fitted to one scale and
    offset and each is printed against its built height.

  python3 tools/keith_bow_lights_read.py            # print
  python3 tools/keith_bow_lights_read.py --write    # and write REPORT

Edges are each opening's dark between its stone reveals, read off median intensity profiles
across the main sash (y 1500-1600), the upper transom (y 1385-1415), the basement lights
(y 1700-1760) and the second storey (y 1120-1260); the third light's north edge is behind the
street tree's trunk in the principal and second storeys and is not used. Heights are read on
the south light's column (x 405-485). It does not fit a camera of its own.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
import keith_plate_level_fit as K

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/inland-1888-bow-lights.json'
R = (2.5 ** 2 + 1.2 ** 2) / (2 * 1.2)      # the bow's plan: chord 5.0 m, rise 1.2 m
CU, CV = 18.0 + 1.2 - R, 3.7                 # its centre in the footprint frame
# storey: (print edges per visible light, south to north; a height on the face to read them at)
EDGES = {
    'second': ([(406, 484), (513, 587), (621, None)], 7.9),
    'principal': ([(407, 482), (515, 588), (620, None)], 3.8),
    'basement': ([(413.5, 474), (518, 579), (623, 674)], 0.8),
}
AS_BUILT = {'second': ([-33, -11, 11], 0.9), 'principal': ([-27, 0, 27], 1.0), 'basement': ([-27, 0, 27], 0.82)}
SECOND = [-33, -11, 11]
# the south light's column: (opening edge, print y, height built before T-2765)
HEIGHTS = [('second-storey head', 1081, 9.15), ('second-storey sill', 1282, 6.65),
           ('principal head', 1382, 5.30), ('principal sill', 1617, 2.35),
           ('basement head', 1692, 1.30), ('basement sill', 1770, 0.30)]
ALSO = [('string course top', 1333), ('string course foot', 1342), ('upper transom bar', 1418),
        ('lower transom bar top', 1468), ('main sash head', 1480), ('cap foot', 1052)]


def edges(p, deg, w, y):
    t = math.radians(deg)
    c = np.array([CU + R * math.cos(t), CV + R * math.sin(t)])
    tn = np.array([-math.sin(t), math.cos(t)])
    return [K.project(p, [*(c - tn * w / 2), y], False)[0], K.project(p, [*(c + tn * w / 2), y], False)[0]]


def resid(p, storey, bearings, w):
    obs, y = EDGES[storey]
    r = []
    for (a, b), deg in zip(obs, bearings):
        e = edges(p, deg, w, y)
        r += [e[0] - a] + ([e[1] - b] if b is not None else [])
    return r


def rms(r):
    return round(float(np.sqrt(np.mean(np.square(r)))), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    fits = []
    for name, keep in K.SETS.items():
        p, _, _ = K.fit([c for c in K.FRONT + K.LOGGIA if keep(c[0])], False)
        row = {'controls': name, 'second_storey_rms_px': rms(resid(p, 'second', *AS_BUILT['second']))}
        for st in ('principal', 'basement'):
            best = min((rms(resid(p, st, SECOND, w)), round(float(w), 2)) for w in np.arange(0.6, 1.205, 0.01))
            row[st] = {'before_rms_px': rms(resid(p, st, *AS_BUILT[st])),
                       'before_residual_px': [round(v) for v in resid(p, st, *AS_BUILT[st])],
                       'at_second_storey_bearings_rms_px': best[0], 'best_width_m': best[1]}
        fits.append(row)
        print(f"{name:38s} second {row['second_storey_rms_px']:5.1f} px | principal before "
              f"{row['principal']['before_rms_px']:5.1f}, at -33/-11/11 {row['principal']['at_second_storey_bearings_rms_px']:5.1f} "
              f"(w {row['principal']['best_width_m']:.2f}) | basement before {row['basement']['before_rms_px']:5.1f}, "
              f"at -33/-11/11 {row['basement']['at_second_storey_bearings_rms_px']:5.1f} (w {row['basement']['best_width_m']:.2f})")
    y = np.array([h[1] for h in HEIGHTS], float)
    h = np.array([h[2] for h in HEIGHTS], float)
    b, a = np.polyfit(h, y, 1)
    heights = [{'edge': n, 'print_y': yy, 'reads_m': round((yy - a) / b, 2), 'built_m': hh,
                'diff_m': round((yy - a) / b - hh, 2)} for n, yy, hh in HEIGHTS]
    also = [{'what': n, 'print_y': yy, 'reads_m': round((yy - a) / b, 2)} for n, yy in ALSO]
    print(f'heights on one level column: {-b:.1f} px/m, grade at y {a:.0f}')
    for q in heights:
        print(f"  {q['edge']:20s} reads {q['reads_m']:5.2f} m, built {q['built_m']:5.2f} ({q['diff_m']:+.2f})")
    for q in also:
        print(f"  {q['what']:20s} reads {q['reads_m']:5.2f} m")
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': "Written by tools/keith_bow_lights_read.py (T-2765): Keith's bow lights on the 1888 plate, "
                    "judged on T-2762's level fits; read the tool's docstring for what is read and how.",
            'print': 'data/sources/assets/inland_architect_1888_02_keith/plate.jpg', 'glb_sha256': K.GLB_SHA256,
            'bow': {'radius_m': round(R, 3), 'centre_uv': [round(CU, 3), CV]},
            'print_edges_px': {k: v[0] for k, v in EDGES.items()}, 'as_built_before': AS_BUILT,
            'fits': fits, 'px_per_m_level_column': round(-b, 2), 'heights': heights, 'also_read': also},
            indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
