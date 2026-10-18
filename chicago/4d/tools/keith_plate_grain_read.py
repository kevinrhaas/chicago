#!/usr/bin/env python3
"""T-2772: what Keith's 1888 plate resolves of the front's joints, upper capitals and head bands.

The four front views of keith_house_1808_prairie (inland-1888 and three smaller reproductions
of the same photograph) each carried one open item, "the individual joints, the upper capitals'
carving and the head bands' exact sections are drawn to the photograph's shadows rather than
read". This reads them, at the plate's native 1559 x 2400 px, against the committed render of
that camera (the right half of inland-1888's side-by-side), and states the grain at each one:

  * JOINTS: the bed joints below the principal storey's transoms, where the street tree's
    branches thin, on two vertical strips side by side on the same courses: the front's south
    strip and the bow's south flank. Each strip is the median across its width, smoothed, and a
    candidate bed is a dark minimum; in the print a bed is one both strips agree on (or one is
    sure of), so a rock face's own shadow is not read as a joint. The render (clean, and its bow
    coursed apart from its front) is read on the front's strip. Print and render are compared
    course by course from the principal sill: how many courses, how tall, deep and thin in turn,
    and whether the bow's beds lie level with the front's.
  * CAPITALS: the five third-storey colonnettes' capitals, where the camera puts them.
  * HEAD BANDS: the crown read along its own courses (the print's and the render's rows slope
    differently, so each is sheared by the slope that sharpens its profile most), the head band's
    shadow measured from the lattice's lower openings, scaled by the lattice's row pitch.

  python3 tools/keith_plate_grain_read.py            # print the reading
  python3 tools/keith_plate_grain_read.py --write    # and write REPORT

It refuses a side-by-side that is not the committed GLB's render (the match record's
glb_sha256): re-render with tools/photo_match.mjs first. It changes no geometry.
"""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'data/reference_views/keith_house_1808_prairie'
SBS = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/inland-1888-side-by-side.jpg'
GLB = ROOT / 'assets/gltf/keith_house_1808_prairie__as_built_1886.glb'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/inland-1888-grain-read.json'
FRONT_VIEWS = ['inland-1888', 'cgn-1808-inland-1888-keith-copy', 'a18-rba-ia-1888-keith-1808',
               'a18-gh-1808-keith-field-front']

# The two strips a bed is read on, side by side on the same courses (the front's south strip and
# the bow's south flank; the street tree leaves both clear below the principal storey's
# transoms), for the print and for the render: (label, x0..x1) at native px, over Y
STRIPS = {
    'print': [("front's south strip", (272, 322)), ("bow's south flank", (335, 395))],
    'render': [("front's south strip", (285, 360)), ("bow's south flank", (385, 435))],
}
Y = {'print': (1425, 1790), 'render': (1385, 1815)}
# the bow's first pier, read in the print only, as a check on the courses above the sill
PIER = ("bow's first pier", (482, 500), (1470, 1625))
# the principal storey's sill bed, read off the bow's lights in each raster: the beds below it
# are the basement's
SILL = {'print': 1617, 'render': 1617}
UP = 7                # courses read up from the sill: as high as both strips stay clear
THIN_PX = 25          # a course under 25 px is a thin one (the model's render 14-16, its deep 35-40)
PROM, SURE = 6, 15    # a bed is a dark line this prominent (grey levels) in BOTH strips within
PROM_RENDER = 8
TOL = 3               # TOL px of each other, or SURE-prominent in one: a bed runs across the wall
# the model's alternating pair on the front's south strip, where the render is read
# (data/structures/keith_house_1808_prairie.json stone_front.coursing; T-2773, from 0.49 / 0.195)
MODEL_DEEP_M, MODEL_THIN_M = 0.418, 0.226
# the crown: (x0, x1, xref, y0, y1) and each raster's row slope (the one that sharpens it most)
CROWN = (330, 560, 700, 560, 880)
SLOPES = np.arange(0.04, 0.16, 0.005)
# the upper colonnettes (stone_finish.colonnettes): axes v, the capital zone under the 12.82 m top
COLONNETTE_V = [2.96, 4.08, 5.2, 6.32, 7.44]
# where the grain is stated: (feature, footprint point u, v, y)
GRAIN_AT = [('lower joints', [17.9, 0.5, 3.0]), ('bow piers', [19.06, 3.2, 3.0]),
            ('upper capitals', [17.8, 5.2, 12.7]), ('head band', [17.8, 5.0, 13.42])]


def camera(view):
    c = json.loads((VIEWS / f'{view}.json').read_text())
    e = np.array(c['eye']); f = c['focal_px']; cx, cy = c['principal_px']; a = c.get('pixel_aspect', 1)
    if 'basis_right_up_forward' in c:
        R = np.array(c['basis_right_up_forward'])
    else:  # a level camera: yaw clockwise from north, as photo_match.mjs reads it
        t = np.radians(c['yaw_deg'])
        R = np.array([[np.cos(t), -np.sin(t), 0], [0, 0, 1], [np.sin(t), np.cos(t), 0]])

    def proj(P):
        d = np.asarray(P, float) - e
        return cx + a * f * (R[0] @ d) / (R[2] @ d), cy - f * (R[1] @ d) / (R[2] @ d)
    return proj


def candidates(a, xs, ys, prom=PROM):
    p = gaussian_filter1d(np.median(a[ys[0]:ys[1], xs[0]:xs[1]], axis=1), 1.5)
    pk, pr = find_peaks(-p, prominence=prom, distance=12)
    return [(ys[0] + int(i), float(q)) for i, q in zip(pk, pr['prominences'])]


def beds(side, a):
    """The print's beds: those both strips agree on (or one is sure of), as their mean place."""
    (_, xa), (_, xb) = STRIPS[side]
    ca, cb = candidates(a, xa, Y[side]), candidates(a, xb, Y[side])
    out = []
    for y, q in ca + cb:
        other = cb if (y, q) in ca else ca
        near = [o for o, _ in other if abs(o - y) <= TOL]
        if near or q >= SURE:
            m = (y + near[0]) / 2 if near else y
            if not any(abs(m - o) <= TOL for o in out):
                out.append(m)
    return sorted(round(y) for y in out), {'a': ca, 'b': cb}


def courses(bs, sill):
    """From the sill bed: UP courses above it, and every course below it, each [px, kind]."""
    k = min(range(len(bs)), key=lambda i: abs(bs[i] - sill))
    up = [[bs[i] - bs[i - 1], 'thin' if bs[i] - bs[i - 1] < THIN_PX else 'deep'] for i in range(k, max(k - UP, 0), -1)]
    down = [bs[i + 1] - bs[i] for i in range(k, len(bs) - 1)]
    return {'sill_bed': bs[k], 'up_from_sill': up, 'below_sill': down}


def sheared(a, slope):
    x0, x1, xref, y0, y1 = CROWN
    X, Y = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1, 0.5))
    v = map_coordinates(a, [Y + slope * (X - xref), X], order=1)
    return np.arange(y0, y1, 0.5), gaussian_filter1d(np.median(v, axis=1), 2.0)


def crown(a):
    slope = max(SLOPES, key=lambda s: np.std(np.diff(sheared(a, s)[1])))
    ys, p = sheared(a, slope)
    # the lattice's two rows of openings: the two brightest peaks above the checker band
    hi, _ = find_peaks(p, prominence=20)
    rows = sorted(sorted((i for i in hi if ys[i] < 665), key=lambda i: -p[i])[:2])
    pitch = float(ys[rows[1]] - ys[rows[0]])
    # the head band's shadow: the darkest trough between the checker band and the lights' heads
    win = (ys > 765) & (ys < 800)
    k = int(np.flatnonzero(win)[np.argmin(p[win])])
    lo_y = float(ys[k])
    # its depth at half its fall from the plain band above it
    above = float(p[(ys > 755) & (ys < lo_y)].max())
    half = (above + p[k]) / 2
    j = k
    while j > 0 and p[j] < half: j -= 1
    m = k
    while m < len(p) - 1 and p[m] < half: m += 1
    return {'row_slope': round(float(slope), 3), 'lattice_lower_openings_y': float(ys[rows[1]]),
            'lattice_row_pitch_px': pitch, 'head_band_shadow_y': lo_y,
            'shadow_below_openings_px': round(lo_y - float(ys[rows[1]]), 1),
            'shadow_depth_px': round(float(ys[m] - ys[j]), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    rec = json.loads((VIEWS / 'inland-1888.match.json').read_text())
    sha = hashlib.sha256(GLB.read_bytes()).hexdigest()
    if rec['glb_sha256'] != sha:
        raise SystemExit(f'inland-1888 side-by-side is of GLB {rec["glb_sha256"][:12]}, the tree holds '
                         f'{sha[:12]}: re-render it (tools/photo_match.mjs) before reading it')
    cam = json.loads((VIEWS / 'inland-1888.json').read_text())
    sbs = np.asarray(Image.open(SBS).convert('L'), float)
    w = cam['image_px'][0]
    ras = {'print': np.asarray(Image.open((VIEWS / cam['photo']).resolve()).convert('L'), float),
           'render': sbs[:, sbs.shape[1] - w:]}

    # The print's front and bow lay one set of beds (a bed is read where both strips agree), the
    # model's front and bow each lay their own (T-2584 courses the bow from its own bed up), so
    # the render is read on the front's strip, where the print's beds are too, and the bow's
    # flank is reported beside it. The render is clean: a bed is any line PROM_RENDER deep.
    bs, cand = beds('print', ras['print'])
    read = {'print': {'strips': [l for l, _ in STRIPS['print']], 'beds': bs, **courses(bs, SILL['print']),
                      'strip_beds': {l: [y for y, _ in cand[k]] for (l, _), k in zip(STRIPS['print'], 'ab')}}}
    rb = {l: [y for y, _ in candidates(ras['render'], xs, Y['render'], PROM_RENDER)] for l, xs in STRIPS['render']}
    front = rb[STRIPS['render'][0][0]]
    read['render'] = {'strips': [STRIPS['render'][0][0]], 'beds': front, **courses(front, SILL['render']),
                      'strip_beds': rb}
    pier = candidates(ras['print'], PIER[1], PIER[2])
    read['print']['first_pier_beds'] = [y for y, q in pier if q >= 8]

    summ = {}
    for side in ('print', 'render'):
        up = read[side]['up_from_sill']
        deep = [c[0] for c in up if c[1] == 'deep']; thin = [c[0] for c in up if c[1] == 'thin']
        summ[side] = {'sequence_up_from_sill': ''.join(c[1][0].upper() for c in up),
                      'deep_px': round(float(np.mean(deep)), 1), 'thin_px': round(float(np.mean(thin)), 1),
                      'pair_px': round(float(np.mean(deep) + np.mean(thin)), 1),
                      'courses_below_sill': len(read[side]['below_sill'])}
        # does the bow's flank lay its beds level with the front's? (beds over the sill's ten courses)
        fa, fb = (read[side]['strip_beds'][l] for l, _ in STRIPS[side])
        lo, hi = read[side]['sill_bed'] - 180, read[side]['sill_bed'] + 4
        fa = [y for y in fa if lo <= y <= hi]
        summ[side]['front_beds_with_a_bow_bed_within_3px'] = f"{sum(any(abs(y - o) <= TOL for o in fb) for y in fa)} of {len(fa)}"
    # the render's own px per metre on these courses, from the model's built pair
    k = summ['render']['pair_px'] / (MODEL_DEEP_M + MODEL_THIN_M)
    summ['print_m'] = {'deep_m': round(summ['print']['deep_px'] / k, 2),
                       'thin_m': round(summ['print']['thin_px'] / k, 2),
                       'below_sill_m': [round(c / k, 2) for c in read['print']['below_sill']],
                       'render_px_per_m': round(k, 1)}

    cr = {side: crown(ras[side]) for side in ('print', 'render')}
    scale = cr['print']['lattice_row_pitch_px'] / cr['render']['lattice_row_pitch_px']
    cr['print_over_render_scale'] = round(scale, 3)
    cr['render_shadow_below_openings_scaled_px'] = round(cr['render']['shadow_below_openings_px'] * scale, 1)

    proj = camera('inland-1888')
    caps = []
    for v in COLONNETTE_V:
        x, y = proj([17.8, v, 12.82]); _, yb = proj([17.8, v, 12.52]); x2, _ = proj([17.8, v + 0.11, 12.82])
        caps.append({'v': v, 'top_px': [round(x), round(y)], 'capital_0.3m_px': round(yb - y, 1),
                     'shaft_px': round(2 * (x2 - x), 1)})

    grain = {}
    for view in FRONT_VIEWS:
        p = camera(view)
        grain[view] = {f: round(10 * (p(P)[1] - p([P[0], P[1], P[2] + 0.1])[1]), 1) for f, P in GRAIN_AT}

    out = {'_what': 'T-2772: Keith\'s front joints, upper capitals and head bands read at the 1888 plate\'s '
                    'native 1559 px against the committed render of inland-1888 (tools/keith_plate_grain_read.py)',
           'glb_sha256': sha, 'beds': read, 'courses': summ, 'crown': cr,
           'upper_capitals_at': caps, 'grain_px_per_m': grain}
    print(json.dumps({k: out[k] for k in ('courses', 'crown', 'grain_px_per_m')}, indent=1))
    for side in ('print', 'render'):
        r = read[side]
        print(f"{side:6s} beds {r['beds']}\n       up from sill {r['up_from_sill']}  below {r['below_sill']}")
    print('first pier beds (print)', read['print']['first_pier_beds'])
    if args.write:
        REPORT.write_text(json.dumps(out, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
