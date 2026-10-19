#!/usr/bin/env python3
"""T-2881 (piece 1 of T-2877): Keith's loggia's rear row read off the 1888 plate and the plan under it.

T-2876 found the plate draws a second row of paired shafts behind the front pairs, which the model
did not build. This reads where they stand.

  1. THE PLATE, at its native 1559 x 2400 px, through inland-1888's camera (T-2845's level fit,
     4.49 px RMS). Each rear shaft's middle is read as the middle of its half-max run along a band
     of rows where the shaft shows (the south pair in shade, x 812-856, rows 1440-1520; the north
     pair's lit feet, x 1015-1058, rows 1540-1560). The pair's depth off the wall (axis) and its
     pitch are fitted to the four middles with each pair at its FRONT pair's v (7.05, 9.9).
     The south rear pedestal's lit front face is read the same way (rows 1600-1630), and each
     edge is turned into the depth of that face for a 0.6 m pedestal.

  2. THE PLAN under the plate (23.17 px/m between its side walls, T-2844): the dark block at the
     wall behind each front pedestal, read across (rows 2200-2212, the south one) and down
     (x 664-670) at half-max, for its depth off the wall and its place along the front.

  python3 tools/keith_loggia_rear_read.py            # print the reading
  python3 tools/keith_loggia_rear_read.py --write    # and write REPORT

What it does not do: move the model. The K07 kit's `loggia.rear` builds what is ruled.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PLATE = ROOT / 'data/sources/assets/inland_architect_1888_02_keith/plate.jpg'
CAMERA = ROOT / 'data/reference_views/keith_house_1808_prairie/inland-1888.json'
RECORD = ROOT / 'data/structures/keith_house_1808_prairie.json'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/keith-loggia-rear-read.json'
FRONT_U = 18.0            # the street front's plane in the camera's frame
PAIRS_V = (7.05, 9.9)     # the front pairs' middles as built (T-2845)
PLAN_PPM, PLAN_SOUTH = 23.17, 2046.5   # the plan's scale and its south wall's row (T-2844)
SHAFT_Y = 3.9             # a height on the shafts, m over grade (the deck at 2.0 m)


def camera():
    c = json.loads(CAMERA.read_text())
    (eu, ev, ey), t = c['eye'], math.radians(c['yaw_deg'])
    f, (cx, cy) = c['focal_px'], c['principal_px']

    def project(u, v, y):
        du, dv, dy = u - eu, v - ev, y - ey
        z = du * math.sin(t) + dv * math.cos(t)
        return cx + f * (du * math.cos(t) - dv * math.sin(t)) / z, cy - f * dy / z
    return project


def runs(profile, x0, level):
    """Half-max runs over `level`: [(start, end)] in image x, edges interpolated."""
    out, on = [], None
    for i in range(1, len(profile)):
        a, b = profile[i - 1], profile[i]
        if (a < level) != (b < level):
            x = x0 + i - 1 + (level - a) / (b - a)
            if b >= level:
                on = x
            elif on is not None:
                out.append((round(on, 1), round(x, 1)))
                on = None
    return out


def read_plate(img):
    a = np.asarray(img, float)
    south = a[1440:1520, 806:860].mean(0)
    north = a[1540:1560, 1015:1058].mean(0)
    face = a[1600:1630, 800:868].mean(0)
    s_runs = runs(south, 806, (south.max() + south.min()) / 2)
    n_runs = runs(north, 1015, (north.max() + north.min()) / 2)
    f_runs = runs(face, 800, (face.max() + face.min()) / 2)
    # the face: its lit field and border, from the first rise to the last fall
    return {'south_shafts_x': s_runs, 'north_shafts_x': n_runs,
            'south_pedestal_face_x': [f_runs[0][0], f_runs[-1][1]]}


def fit(P, mids):
    obs = [(PAIRS_V[0], -1, mids[0]), (PAIRS_V[0], 1, mids[1]), (PAIRS_V[1], -1, mids[2]), (PAIRS_V[1], 1, mids[3])]
    best = None
    for o in np.arange(0.05, 1.2, 0.005):
        for p in np.arange(0.2, 0.45, 0.0025):
            e = [P(FRONT_U + o, v + s * p / 2, SHAFT_Y)[0] - x for v, s, x in obs]
            r = math.sqrt(sum(x * x for x in e) / len(e))
            if best is None or r < best[0]:
                best = (r, o, p, e)
    r, o, p, e = best
    return {'axis_m': round(float(o), 3), 'pitch_m': round(float(p), 4), 'rms_px': round(r, 2),
            'residuals_px': [round(float(x), 1) for x in e]}


def face_depth(P, edges, width=0.6):
    out = []
    for x, v in zip(edges, (PAIRS_V[0] - width / 2, PAIRS_V[0] + width / 2)):
        os_ = np.arange(0.0, 1.2, 0.005)
        xs = [P(FRONT_U + o, v, 2.5)[0] for o in os_]
        out.append(round(float(os_[int(np.argmin([abs(q - x) for q in xs]))]), 3))
    return out


def read_plan(img):
    a = np.asarray(img, float)
    across = a[2200:2212, 655:680].mean(0)       # the south block, from the deck into the wall
    down = a[2190:2230, 664:670].mean(1)         # along the front, through the south block
    lvl = 125.0
    front = next(655 + i - 1 + (lvl - across[i - 1]) / (across[i] - across[i - 1])
                 for i in range(1, len(across)) if across[i - 1] >= lvl > across[i])
    # the block's back is the faint light line between it and the wall's own dark (x 671)
    back = 655 + int(np.argmax(across[14:18])) + 14
    r = runs(255 - down, 2190, 255 - lvl)[0]
    v = [round((x - PLAN_SOUTH) / PLAN_PPM, 2) for x in r]
    return {'south_block_front_x': round(float(front), 1), 'south_block_back_x': back,
            'south_block_depth_m': round((back - front) / PLAN_PPM, 2),
            'south_block_rows': list(r), 'south_block_v_m': v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    img = Image.open(PLATE).convert('L')
    P = camera()
    plate = read_plate(img)
    mids = [round((a + b) / 2, 1) for a, b in plate['south_shafts_x'][:2] + plate['north_shafts_x'][-2:]]
    f = fit(P, mids)
    face = face_depth(P, plate['south_pedestal_face_x'])
    plan = read_plan(img)
    # the record's built rear row through the same camera, against the print's middles
    lg = json.loads(RECORD.read_text())['phases'][0]['form']['entrance_kit']['value'][
        'k01.opening.door_leaf']['terrace']['loggia']
    ax, pt = lg['rear']['axis_m'], lg['rear']['pitch_m']
    bx = [P(FRONT_U + ax, v + s * pt / 2, SHAFT_Y)[0] for v in PAIRS_V for s in (-1, 1)]
    built = {'axis_m': ax, 'pitch_m': pt, 'middles_x': [round(x, 1) for x in bx],
             'minus_print_px': [round(x - y, 1) for x, y in zip(bx, mids)]}
    rep = {'ticket': 'T-2881', 'camera': str(CAMERA.relative_to(ROOT)), 'plate': plate,
           'shaft_middles_x': mids, 'fit_at_front_pairs_v': f,
           'south_pedestal_face_depth_m_from_each_edge': face, 'plan': plan,
           'built': built}
    print(json.dumps(rep, indent=1))
    if args.write:
        REPORT.write_text(json.dumps(rep, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
