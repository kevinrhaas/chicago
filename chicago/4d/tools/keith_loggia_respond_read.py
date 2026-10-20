#!/usr/bin/env python3
"""T-2882 (piece 2 of T-2877): what stands at the wall behind Keith's loggia's rear pairs.

T-2881 built the rear row and left two things it could not account for: the first-floor plan
under the 1888 plate draws the block at the wall behind each front pedestal only about 0.21 m
deep, where a pedestal carrying the pair the plate reads is about 0.55 m; and the plate draws
a lit upright at x 997-1009, rows 1522-1587, just south of the north rear pair. This reads
both and weighs what each could be.

  1. THE UPRIGHT, on the plate at its native 1559 x 2400 px: its lit run across (half-max, rows
     1525-1582), the dim strip beside it, and its top and foot (half-max down x 999-1007).
     Projected through inland-1888's camera (T-2845's level fit, 4.49 px RMS), the candidates:
       - the door's north reveal (the built hole, 1.20 m wide on the bay at v 8.7, its reveal
         running 0.45 m into the front wall);
       - a flat face on the line of the north rear pedestal's south side (v 9.6), standing
         off the wall by 0.0-0.4 m;
     and the height its top and foot stand at on that face.
  2. THE PLAN (23.17 px/m between its side walls, T-2844): each block at the wall, read across
     at half-max from the deck to the light line the plan draws between it and the wall's own
     dark, and down along the front for its width and the lobes in it.

  python3 tools/keith_loggia_respond_read.py            # print the reading
  python3 tools/keith_loggia_respond_read.py --write    # and write REPORT

What it does not do: move the model. The K07 kit's `loggia.rear.respond_m` builds what is ruled.
"""
from pathlib import Path
import argparse, json
import numpy as np
from PIL import Image
from keith_loggia_rear_read import camera, runs, PLATE, FRONT_U, PLAN_PPM, PLAN_SOUTH

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/keith-loggia-respond-read.json'
DOOR_V, DOOR_W, WALL_T = 8.7, 1.20, 0.45   # the built door hole's bay, width, the front wall
REAR_SOUTH_V = 9.6                          # the north rear pedestal's south side as built


def read_upright(a):
    p = a[1525:1582, 985:1018].mean(0)
    lit = runs(p, 985, (p.max() + p.min()) / 2)[0]
    # the dim strip beyond the lit run, down to a quarter of the peak
    q = p.max() / 4
    end = next(985 + i for i in range(int(lit[1]) - 985, len(p)) if p[i] < q)
    col = a[1490:1610, 999:1007].mean(1)
    lvl = (col[30:100].max() + col[:10].mean()) / 2
    top = next(1490 + i for i in range(len(col)) if col[i] >= lvl)
    foot = next(1490 + i for i in range(len(col) - 1, 0, -1) if col[i] >= lvl)
    return {'lit_x': list(lit), 'dim_strip_to_x': end, 'top_row': top, 'foot_row': foot,
            'profile_rows_1525_1582': [int(x) for x in p]}


def y_at_row(P, u, v, row):
    ys = np.arange(1.5, 6.0, 0.005)
    return round(float(ys[int(np.argmin([abs(P(u, v, y)[1] - row) for y in ys]))]), 2)


def u_at_x(P, v, x, y=3.4):
    us = np.arange(FRONT_U - 0.6, FRONT_U + 0.8, 0.005)
    return round(float(us[int(np.argmin([abs(P(u, v, y)[0] - x) for u in us]))]) - FRONT_U, 3)


def read_plan_block(a, rows, name):
    across = a[rows[0]:rows[1], 655:680].mean(0)
    lvl = 125.0
    front = next(655 + i - 1 + (lvl - across[i - 1]) / (across[i] - across[i - 1])
                 for i in range(1, len(across)) if across[i - 1] >= lvl > across[i])
    line = 655 + 12 + int(np.argmax(across[12:19]))     # the light line before the wall's dark
    down = a[rows[0] - 12:rows[1] + 12, 664:669].mean(1)
    r = runs(255 - down, rows[0] - 12, 255 - lvl)
    span = [r[0][0], r[-1][1]]
    return {'block': name, 'front_x': round(float(front), 1), 'light_line_x': line,
            'depth_m': round((line - front) / PLAN_PPM, 2),
            'dark_runs_rows': [list(x) for x in r],
            'v_m': [round((x - PLAN_SOUTH) / PLAN_PPM, 2) for x in span],
            'light_line_peak': int(across[line - 655]), 'across': [int(x) for x in across]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    a = np.asarray(Image.open(PLATE).convert('L'), float)
    P = camera()
    up = read_upright(a)
    jamb = DOOR_V + DOOR_W / 2
    cands = {
        'door north reveal (v %.2f, 0.45 m into the wall)' % jamb:
            [round(P(FRONT_U - d, jamb, 3.4)[0], 1) for d in (0.0, WALL_T)],
        'a face on the rear pedestal\'s south side (v %.2f), 0.0-0.4 m off the wall' % REAR_SOUTH_V:
            [round(P(FRONT_U + d, REAR_SOUTH_V, 3.4)[0], 1) for d in (0.0, 0.1, 0.2, 0.3, 0.4)],
    }
    off = {'lit_run_near_edge_m': u_at_x(P, REAR_SOUTH_V, up['lit_x'][0]),
           'lit_run_far_edge_m': u_at_x(P, REAR_SOUTH_V, up['lit_x'][1]),
           'dim_strip_far_edge_m': u_at_x(P, REAR_SOUTH_V, up['dim_strip_to_x'])}
    mid_u = FRONT_U + off['lit_run_far_edge_m'] / 2
    heights = {'top_m': y_at_row(P, mid_u, REAR_SOUTH_V, up['top_row']),
               'foot_m': y_at_row(P, mid_u, REAR_SOUTH_V, up['foot_row'])}
    plan = [read_plan_block(a, (2203, 2215), 'south'), read_plan_block(a, (2268, 2284), 'north')]
    rep = {'ticket': 'T-2882', 'camera': 'data/reference_views/keith_house_1808_prairie/inland-1888.json',
           'upright': up, 'candidates_x_at_3_4_m': cands, 'upright_off_wall_on_v_9_6': off,
           'upright_heights_over_grade': heights, 'plan_blocks': plan}
    print(json.dumps(rep, indent=1))
    if args.write:
        REPORT.write_text(json.dumps(rep, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
