#!/usr/bin/env python3
"""T-2771: is the Glessner-front view's deep crown stack the camera's or Keith's?

The Glessner-front view's match record (a18-gh-glessner-front-with-keith) left one item open
after T-2680: with the lattice rows in register, the stack from the lower row down to the head
band reads about 15 px (0.2 m) deeper in the render than in the print, and the record laid the
rest on the camera, "fitted to the two pinnacle apexes alone in height". This rules that.

The test needs no camera fit. Every camera here is LEVEL (verticals vertical; T-2680 found the
Glessner-front print's north arris at x 138 on every row from the coping down to the band), and
under a level camera a vertical line on the front images as a straight, evenly scaled line: its
pixel y is linear in height, whatever the eye's height, distance, focal length or principal
point. So on one image column, the stack's length over the lattice's own row pitch (the lower
row's sill to the upper row's, 0.40 m in the model) is a ratio no level camera can change; this
reads it in each print and in the model, and prints the pitch a tilted camera would need to make
the difference instead.

  python3 tools/keith_crown_stack.py            # print the table
  python3 tools/keith_crown_stack.py --write    # and write REPORT

The model's heights are derived from the structure record (wall head = principal floor + storey
heights; the lattice's foot 0.12 m over it, k01_frontage's cornice box; its rail and openings from
stone_finish.lattice; the head band's top from stone_finish.diaper), so a record change re-derives
them. The print readings are luminance edges read on the named columns at the prints' native size
(mean over the columns, 1 px rows): the bottom edges of the two lattice rows' openings (their
sills) and the top of the head band, where the lit plain ground over it meets the band's moulding.
"""
from pathlib import Path
import argparse, json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SID = 'keith_house_1808_prairie'
VIEWS = ROOT / 'data/reference_views' / SID
REPORT = ROOT / 'docs/RESEARCH/photo-match' / SID / 'a18-gh-glessner-front-with-keith-stack.json'

# view -> the image columns read, and the print's rows: upper sill, lower sill, head band top
READINGS = {
    'a18-gh-glessner-front-with-keith': {
        'columns': [15, 95], 'print': [115.0, 145.0, 263.0],
        'how': 'the openings show sky: the sills are where the rows\' light ends (column sd falls 114-116 '
               'and 144-146); the head band\'s top is the foot of the lit plain ground (mean 119 at y 262, '
               '71 at y 264), with the checker\'s rows over it and the band\'s shadowed moulding under it',
    },
    'a18-gh-florian-1948-northeast-overall': {
        'columns': [204, 214], 'print': [226.5, 244.5, 318.5],
        'how': 'the openings read dark on the lit lattice (upper rows y 216-226, lower y 233-244); the head '
               'band\'s top is the foot of the lit plain ground (y 298-317), the first dip of its moulding at '
               'y 318-319 over its shadow at y 321-326',
    },
}
# The 1888 Keith plate is read too, and does not rule: its crown stands behind bare branches, and
# its openings' edges on the clearest column (x 520-540) can be taken anywhere in y 597-601 and
# 627-631, a pitch of 26-34 px, so its ratio spans the model's and the other prints' alike.
PLATE = {'view': 'inland-1888', 'columns': [520, 540], 'print': [[597, 601], [627, 631], [744, 752]]}


def camera(view):
    c = json.loads((VIEWS / f'{view}.json').read_text())
    if 'basis_right_up_forward' in c:
        right, up, fwd = (np.array(v, float) for v in c['basis_right_up_forward'])
    else:
        t = math.radians(c['yaw_deg'])
        right, up, fwd = (np.array([math.cos(t), -math.sin(t), 0.]), np.array([0., 0., 1.]),
                          np.array([math.sin(t), math.cos(t), 0.]))
    return c, right, up, fwd


def project(view, P, pitch_deg=0.0):
    """The camera's own projection (photo_match.mjs), optionally pitched about its right axis."""
    c, right, up, fwd = camera(view)
    a = math.radians(pitch_deg)
    fwd, up = math.cos(a) * fwd + math.sin(a) * up, math.cos(a) * up - math.sin(a) * fwd
    d = np.asarray(P, float) - np.asarray(c['eye'], float)
    z = d @ fwd
    cx, cy = c['principal_px']
    return cx + c.get('pixel_aspect', 1) * c['focal_px'] * (d @ right) / z, cy - c['focal_px'] * (d @ up) / z


def model_levels():
    rec = json.loads((ROOT / f'data/structures/{SID}.json').read_text())
    form = rec['phases'][0]['form']
    E = form['principal_floor_m']['value'] + sum(form['storey_heights_m']['value'])
    sf = form['stone_finish']['value']
    lat, di = sf['lattice'], sf['diaper']
    lower = E + .12 + lat['bar_m']                     # k01_frontage: the lattice's foot at E + 0.12
    opening = (lat['height_m'] - 2 * lat['bar_m'] - lat.get('head_m', lat['bar_m'])) / 2
    return {'wall_head_m': round(E, 3), 'upper_sill_m': round(lower + lat['bar_m'] + opening, 3),
            'lower_sill_m': round(lower, 3), 'head_band_top_m': round(di['bottom_m'] - di.get('gap_m', 0), 3)}


def front_v_at(view, x, y_m):
    """The point on the front's plane (u 18) that the column x sees at height y_m."""
    lo, hi = 0.0, 10.4
    f = lambda v: project(view, [18.0, v, y_m])[0] - x
    if f(lo) * f(hi) > 0:
        raise SystemExit(f'{view}: column {x} does not see the front')
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(lo) * f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def read(view, cols, print_rows, M):
    x = sum(cols) / 2
    v = front_v_at(view, x, M['lower_sill_m'])
    heights = [M['upper_sill_m'], M['lower_sill_m'], M['head_band_top_m']]
    model = [project(view, [18.0, v, h])[1] for h in heights]
    pitch_m, stack_m = heights[0] - heights[1], heights[1] - heights[2]
    p_pitch, p_stack = print_rows[1] - print_rows[0], print_rows[2] - print_rows[1]
    m_pitch, m_stack = model[1] - model[0], model[2] - model[1]
    scale = m_stack / stack_m                           # the camera's px per m at the stack
    return {'column_x': x, 'front_v_m': round(v, 2), 'print_px': print_rows,
            'model_px': [round(y, 1) for y in model],
            'camera_px_per_m': round(scale, 1), 'print_pitch_px_per_m': round(p_pitch / pitch_m, 1),
            'ratio_stack_over_pitch': {'print': round(p_stack / p_pitch, 3), 'model': round(m_stack / m_pitch, 3)},
            'stack_m': {'model': round(stack_m, 3),
                        'print_by_pitch': round(pitch_m * p_stack / p_pitch, 3),
                        'print_by_camera': round(p_stack / scale, 3)},
            'stack_deeper_in_model_px': round(m_stack - p_stack, 1)}


def pitch_needed(view, x, target, M):
    """The camera pitch (about its own right axis, with the eye kept) that would draw the model's
    stack over its pitch at the print's ratio, and how far that camera leans the front's arris."""
    v = front_v_at(view, x, M['lower_sill_m'])
    hs = [M['upper_sill_m'], M['lower_sill_m'], M['head_band_top_m']]
    def ratio(a):
        y = [project(view, [18.0, v, h], a)[1] for h in hs]
        return (y[2] - y[1]) / (y[1] - y[0])
    best = min((abs(ratio(a / 10) - target), a / 10) for a in range(-800, 801))
    a = best[1]
    def lean(t):
        x0, x1 = (project(view, [18.0, 10.4, h], t)[0] for h in (M['head_band_top_m'] - 1.0, M['upper_sill_m'] + 0.5))
        return x1 - x0
    return {'pitch_deg': a, 'ratio_reached': round(ratio(a), 3), 'reached': bool(best[0] < .01),
            'arris_lean_px': round(float(lean(a) - lean(0.0)), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    M = model_levels()
    print(f"model: wall head {M['wall_head_m']} m; sills {M['upper_sill_m']} / {M['lower_sill_m']} m; "
          f"head band top {M['head_band_top_m']} m")
    rows = {}
    for view, r in READINGS.items():
        q = rows[view] = read(view, r['columns'], r['print'], M)
        q['how'] = r['how']
        q['camera_pitch_that_would_explain_it'] = pitch_needed(view, q['column_x'], q['ratio_stack_over_pitch']['print'], M)
        s, k = q['stack_m'], q['camera_pitch_that_would_explain_it']
        print(f"{view:40s} x {q['column_x']:.0f}: stack/pitch print {q['ratio_stack_over_pitch']['print']:.2f} "
              f"model {q['ratio_stack_over_pitch']['model']:.2f}; stack {s['print_by_pitch']:.2f} m (by pitch) / "
              f"{s['print_by_camera']:.2f} m (by camera, {q['camera_px_per_m']} px/m; the print's pitch gives "
              f"{q['print_pitch_px_per_m']}) against {s['model']:.2f} m; {q['stack_deeper_in_model_px']:+.1f} px. "
              f"A tilt would need {k['pitch_deg']:+.1f} deg, leaning the north arris {k['arris_lean_px']:+.0f} px "
              f"between 1 m under the head band and the coping")
    x = sum(PLATE['columns']) / 2
    v = front_v_at(PLATE['view'], x, M['lower_sill_m'])
    (u0, u1), (l0, l1), (h0, h1) = PLATE['print']
    lo, hi = (h0 - l1) / (l1 - u0), (h1 - l0) / (l0 - u1)
    pitch_m = M['upper_sill_m'] - M['lower_sill_m']
    plate = {**PLATE, 'front_v_m': round(v, 2), 'ratio_range': [round(lo, 2), round(hi, 2)],
             'stack_m_range': [round(lo * pitch_m, 2), round(hi * pitch_m, 2)]}
    print(f"{PLATE['view']:40s} x {x:.0f}: stack/pitch {lo:.2f}-{hi:.2f}, stack {plate['stack_m_range'][0]}-"
          f"{plate['stack_m_range'][1]} m: the branches leave it unable to rule")
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_crown_stack.py (T-2771): the crown stack (the lattice\'s lower sill to '
                    'the head band\'s top) over the lattice\'s row pitch, read on one column of each print and of the '
                    'model through the view\'s own camera; a ratio no level camera can change. Read the tool\'s docstring.',
            'model': M, 'views': rows, 'plate_not_ruling': plate}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
