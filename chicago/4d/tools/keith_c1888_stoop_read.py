#!/usr/bin/env python3
"""T-2812: does the c. 1888 SW print move Keith's stoop, or is it the print?

T-2748 re-fitted the c. 1888 view looking south-west over 1800-1808 Prairie
(a18-gh-1800-block-looking-sw-c1888) on the crown and the southmost third-storey light, and
through it the stoop read about 35 px left of the render and its arch "a low round-headed
opening" (27 x 20 px against the built 33 x 62). T-2812 was to build that, read beside the 1888
plate and the 1965 porch view. This reads it first, and finds the print cannot carry the move:

  * IN THE PRINT the loggia's front is the built width (the deck front 85 px against 80, the
    pierced parapet 40 px against 40) with its shadowed north side beside it, displaced as one
    block about 35-40 px left and down. Only the head of the arch shows, over a light band at
    y 1032 that runs in front of it; where the block is displaced the built arch's crown lands
    on the print's.
  * NO LEVEL CAMERA HOLDS THE CROWN AND THE LOGGIA TOGETHER. Fitted on the crown, every camera
    leaves the loggia 33-41 px off across and 37-50 px off down; fitted on both, the crown goes
    to 20 px and the south corner's grade 40 px. Only an eye 5-6 m up reaches 7.7 px RMS, and
    the print's own horizon refuses that: Glessner's two identical ground-floor window grids
    scale about y 988, so the eye stands about where the 1.7 m camera puts it.
  * THE OTHER PICTURES PLACE THE LOGGIA AS BUILT, each through a fit that has loggia controls
    in it: the 1888 plate's level fits (T-2762/T-2763, the pedestals' arrises across and their
    caps in height) and the 1965 slide's (T-2764, the shafts' and the south pedestal's
    silhouettes, the pedestal caps predicted within 3-4 px), with the plan under the plate
    giving the deck 2.7 m out. The plate also draws the arch where it is built: crown y 1728
    against 1724, its void 10-15 px inside the built outline in its shadowed reveal.

So the stoop is not moved and the arch not lowered: a 35 px move is about 0.9 m out from the
front or 1.4 m south along it, against three readings that hold it, and lowering the arch to
the print's 20 px would put its crown about 0.4 m over grade where the plate draws it at 1.1 m.

  python3 tools/keith_c1888_stoop_read.py            # print the table
  python3 tools/keith_c1888_stoop_read.py --write    # and write REPORT

The model's points are derived from the structure record (the principal floor, the terrace's
reach and the loggia's pedestal, parapet and arch in entrance_kit), on the street front's plane
at u 18.0. The print readings were taken at the print's native 1733 x 1376 px (6x crops for the
loggia); the window grids' pane rows are read here from the image's luminance. The crown
controls are T-2748's, as its `solve` states them.

What it does not do: fit lens distortion or a pitched camera (the print's verticals are plumb),
or say which of this copy's resampling and the original print's optics displaces the loggia;
change the view's committed camera, the structure record or the GLB.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
from PIL import Image
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
SID = 'keith_house_1808_prairie'
VIEW = ROOT / 'data/reference_views' / SID / 'a18-gh-1800-block-looking-sw-c1888.json'
PRINT = ROOT / 'data/sources/assets/inland_architect_1888_02_keith/a18-gh-1800-block-looking-sw-c1888.jpg'
RECORD = ROOT / 'data/structures' / f'{SID}.json'
PLATE_FIT = ROOT / 'docs/RESEARCH/photo-match' / SID / 'inland-1888-level-fit.json'
SLIDE_FIT = ROOT / 'docs/RESEARCH/photo-match' / SID / 'a18-gh-1808-porch-1965-level-fit.json'
REPORT = ROOT / 'docs/RESEARCH/photo-match' / SID / 'a18-gh-1800-block-looking-sw-c1888-stoop.json'
FRONT_U = 18.0

# T-2748's controls (world [u east, v north, y over grade] -> print (x | None, y | None))
CROWN = [
    ('north-east pinnacle apex', [17.86, 10.251, 17.07], (1135, 105)),
    ('rear pinnacle apex', [12.73, 10.18, 17.268], (1311, 139)),
    ('south-east pinnacle apex', [17.86, 0.187, 17.07], (893, 256)),
    ('north arris at 15.5 m', [18.0, 10.4, 15.5], (1126, None)),
    ('north arris at 12.0 m', [18.0, 10.4, 12.0], (1126, None)),
    ('southmost third-storey light head', [17.8, 2.40, 12.60], (935, 438)),
    ('southmost third-storey light sill', [17.8, 2.40, 10.53], (935, 527)),
]
# the lattice's upper-row opening tops and lower-row bottoms, as lines through two print points
LINES = [(17.72, 15.92, (1110, 172), (920, 287)), (17.72, 15.25, (1110, 205), (920, 321))]
# T-2748's two points it did not fit
CHECK = [
    ('northmost third-storey light head', [17.8, 8.0, 12.6], (1061, 370)),
    ("T-1883's grade at the south corner", [18.0, 0.0, 0.0], (865, 1015)),
]
# Glessner's ground-floor window grids (3 x 3 panes, the same size): the column bands read
GRIDS = {'left': (1150, 1290), 'right': (1655, 1733)}


def record_points():
    """The loggia's front, from the record: (label, world, print reading)."""
    form = json.loads(RECORD.read_text())['phases'][0]['form']
    floor = form['principal_floor_m']['value']
    kit = form['entrance_kit']['value']['k01.opening.door_leaf']
    t, lg = kit['terrace'], kit['terrace']['loggia']
    v0 = kit['stoop_v_m'] + form['stoop_width_m']['value'] / 2   # the flight's north cheek
    u = FRONT_U + t['out_m']
    ped, par, arch = lg['pedestal']['width_m'], lg['parapet']['height_m'], lg['arch']
    vn = t['to_v_m']
    mid = (v0 + vn) / 2
    built = {'principal_floor_m': floor, 'deck_out_m': t['out_m'], 'deck_v_m': [v0, vn],
             'pedestal_width_m': ped, 'parapet_height_m': par, 'arch': arch}
    across = [   # read across only (the print's x)
        ("deck front's south arris", [u, v0, 1.5], (890, None)),
        ("parapet's south end at its coping", [u, v0 + ped, floor + par], (918, None)),
        ("parapet's north end at its coping", [u, vn - ped, floor + par], (958, None)),
        ("deck front's north arris", [u, vn, 1.5], (975, None)),
    ]
    down = [     # and in height
        ("parapet's south end at its coping", [u, v0 + ped, floor + par], (918, 913)),
        ("parapet's north end at its coping", [u, vn - ped, floor + par], (958, 913)),
        ("parapet's south end at the deck", [u, v0 + ped, floor], (918, 965)),
        ("parapet's north end at the deck", [u, vn - ped, floor], (958, 965)),
        ("deck front's south arris", [u, v0, 1.5], (890, None)),
        ("deck front's north arris", [u, vn, 1.5], (975, None)),
    ]
    crown = arch['spring_m'] + arch['span_m'] / 2
    predicted = [
        ("parapet's coping", [u, mid, floor + par], (938, 913)),
        ("parapet's foot (the deck)", [u, mid, floor], (938, 965)),
        ("arch's crown", [u, mid, crown], (922, 1012)),
    ]
    return built, across, down, predicted


def project(c, p):
    u, v, h = c['eye']
    t = math.radians(c['yaw'])
    du, dv, dy = p[0] - u, p[1] - v, p[2] - h
    z = du * math.sin(t) + dv * math.cos(t)
    x = du * math.cos(t) - dv * math.sin(t)
    return c['cx'] + c['a'] * c['f'] * x / z, c['cy'] - c['f'] * dy / z


def residuals(c, sets):
    r = []
    for S in sets:
        for _, w, (x, y) in S:
            X, Y = project(c, w)
            if x is not None:
                r.append(X - x)
            if y is not None:
                r.append(Y - y)
    for u, h, (x1, y1), (x2, y2) in LINES:
        nx, ny = -(y2 - y1), x2 - x1
        n = math.hypot(nx, ny)
        for v in (0.6, 9.8):
            X, Y = project(c, [u, v, h])
            r.append(((X - x1) * nx + (Y - y1) * ny) / n)
    return np.array(r)


def horizon():
    """Where Glessner's two identical window grids scale about: a level camera's horizon."""
    im = np.asarray(Image.open(PRINT).convert('L'), dtype=float)
    rows = {}
    for k, (x0, x1) in GRIDS.items():
        prof = im[940:1085, x0:x1].mean(axis=1)
        dark = prof < prof.max() - 0.35 * (prof.max() - prof.min())
        runs, s = [], None
        for i, d in enumerate(dark):
            y = 940 + i
            if d and s is None:
                s = y
            if not d and s is not None:
                if y - s > 10:          # a pane row, not a stray dark line
                    runs.append((s, y - 1))
                s = None
        rows[k] = runs[-3:]
    L, R = rows['left'], rows['right']
    k = (R[-1][1] - R[0][0]) / (L[-1][1] - L[0][0])
    pairs = [(L[0][0], R[0][0]), (L[-1][1], R[-1][1])] + [((a + b) / 2, (c + d) / 2) for (a, b), (c, d) in zip(L, R)]
    ys = [(yr - k * yl) / (1 - k) for yl, yr in pairs]
    return {'pane_rows_px': rows, 'scale_right_over_left': round(k, 3),
            'horizon_y_px': round(float(np.mean(ys)), 1), 'spread_px': round(float(np.ptp(ys)), 1)}


def fit(name, sets, base, free, fixed=None):
    """A level camera: `free` names the parameters fitted, the rest stay at `base`."""
    fixed = dict(fixed or {})
    keys = ['u', 'v', 'yaw', 'f', 'cy', 'a', 'h']
    p0 = [base[k] for k in free]
    scale = {'u': 1, 'v': 1, 'yaw': 1, 'f': 50, 'cy': 20, 'a': 0.05, 'h': 0.5}

    def cam(p):
        c = dict(base, **fixed)
        c.update(zip(free, (float(x) for x in p)))
        return {'eye': [c['u'], c['v'], c['h']], 'yaw': c['yaw'], 'f': c['f'], 'cx': c['cx'],
                'cy': c['cy'], 'a': c['a']}
    s = least_squares(lambda p: residuals(cam(p), sets), p0, x_scale=[scale[k] for k in free])
    c = cam(s.x)
    r = residuals(c, sets)
    return name, c, r


def describe(name, c, r, across, predicted):
    row = {'fit': name, 'eye_uvy': [round(x, 2) for x in c['eye']], 'yaw_deg': round(c['yaw'], 2),
           'focal_px': round(c['f']), 'horizon_y_px': round(c['cy'], 1), 'pixel_aspect': round(c['a'], 3),
           'rms_px': round(float(np.sqrt((r ** 2).mean())), 1), 'max_px': round(float(abs(r).max()), 1)}
    row['crown_px'] = {lab: [round(project(c, w)[i] - q, 1) for i, q in enumerate(xy) if q is not None]
                       for lab, w, xy in CROWN}
    row['loggia_across_px'] = {lab: round(project(c, w)[0] - x, 1) for lab, w, (x, _) in across}
    row['checks_px'] = {lab: [round(project(c, w)[i] - q, 1) for i, q in enumerate(xy)] for lab, w, xy in CHECK}
    row['predicted'] = {lab: {'render_xy': [round(v) for v in project(c, w)], 'print_xy': list(xy)}
                        for lab, w, xy in predicted}
    return row


def other_pictures():
    """The loggia controls' residuals in the plate's and the 1965 slide's committed level fits."""
    out = {}
    plate = json.loads(PLATE_FIT.read_text())
    labels = [c['label'] for c in plate['controls'] if 'pedestal' in c['label'] or 'capital' in c['label']]
    out['inland-1888 (T-2762/T-2763)'] = {
        'loggia_controls': labels,
        'fits': [{'controls': f['controls'], 'rms_px': f['rms_px'], 'max_px': f['max_px']} for f in plate['fits']]}
    slide = json.loads(SLIDE_FIT.read_text())
    out['a18-gh-1808-porch-1965 (T-2764)'] = {
        'fits': [{'controls': f['controls'], 'rms_px': f['rms_px'],
                  'loggia_px': {k: v for k, v in f['residual_px'].items() if 'pedestal' in k or 'shaft' in k}}
                 for f in slide['fits'] if any('pedestal' in k for k in f['residual_px'])]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    built, across, down, predicted = record_points()
    v = json.loads(VIEW.read_text())
    base = {'u': v['eye'][0], 'v': v['eye'][1], 'h': v['eye'][2], 'yaw': v['yaw_deg'], 'f': v['focal_px'],
            'cx': v['principal_px'][0], 'cy': v['principal_px'][1], 'a': v.get('pixel_aspect', 1.0)}
    hz = horizon()
    committed = {'eye': v['eye'], 'yaw': base['yaw'], 'f': base['f'], 'cx': base['cx'], 'cy': base['cy'], 'a': base['a']}
    fits = [('committed camera (T-2748)', committed, residuals(committed, [CROWN]))]
    fits.append(fit('crown, eye 1.7 m', [CROWN], base, ['u', 'v', 'yaw', 'f', 'cy', 'a']))
    fits.append(fit('crown + loggia across, eye 1.7 m', [CROWN, across], base, ['u', 'v', 'yaw', 'f', 'cy', 'a']))
    fits.append(fit('crown + loggia across and down, eye free', [CROWN, down], base,
                    ['u', 'v', 'yaw', 'f', 'cy', 'a', 'h']))
    hb = dict(base, cy=hz['horizon_y_px'])
    fits.append(fit("crown, horizon held at the grids' reading, eye free", [CROWN], hb, ['u', 'v', 'yaw', 'f', 'a', 'h']))
    fits.append(fit("crown + loggia across and down, horizon held, eye free", [CROWN, down], hb,
                    ['u', 'v', 'yaw', 'f', 'a', 'h']))
    rows = [describe(n, c, r, across, predicted) for n, c, r in fits]
    print(f"horizon from Glessner's window grids: y {hz['horizon_y_px']} (spread {hz['spread_px']} px), "
          f"pane rows {hz['pane_rows_px']}")
    for row in rows:
        print(f"\n{row['fit']}: RMS {row['rms_px']} px, max {row['max_px']}; eye {row['eye_uvy']}, "
              f"yaw {row['yaw_deg']}, f {row['focal_px']}, horizon y {row['horizon_y_px']}, aspect {row['pixel_aspect']}")
        print('  loggia across (render - print):', row['loggia_across_px'])
        print('  checks:', row['checks_px'])
        for lab, p in row['predicted'].items():
            print(f"  {lab}: render {p['render_xy']}  print {p['print_xy']}")
    others = other_pictures()
    for k, o in others.items():
        print(f'\n{k}:', json.dumps(o)[:600])
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_c1888_stoop_read.py (T-2812): the c. 1888 SW print\'s reading of '
                    "Keith's stoop weighed on level cameras and against the plate's and the 1965 slide's fits; "
                    "read the tool's docstring for what is fitted and what is not.",
            'print': str(PRINT.relative_to(ROOT)), 'view': str(VIEW.relative_to(ROOT)),
            'built': built, 'horizon': hz,
            'print_readings': {'loggia_across': [[l, w, xy] for l, w, xy in across],
                               'loggia_down': [[l, w, xy] for l, w, xy in down],
                               'predicted_only': [[l, w, xy] for l, w, xy in predicted]},
            'fits': rows, 'other_pictures': others,
            'ruling': 'not moved: no level camera holds the crown and the loggia together in this print, '
                      'whose horizon refuses the one raised eye that would; the 1888 plate and the 1965 slide, '
                      "each through a fit with loggia controls, and the plan's 2.7 m deck place the stoop and its "
                      "arch as built. The print's 'low arch' is the built arch's head over a light band in front of it.",
        }, indent=1) + '\n')
        print(f'\nwrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
