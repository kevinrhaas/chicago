#!/usr/bin/env python3
"""T-2857: Glessner's Prairie front read against HABS sheet 6 and its three street photographs.

Re-derives every number in README.md from the picks written below (pixel columns read by eye
off the committed side-by-sides and sheet 6; see README.md for where each was read).
Nothing here is a gate; it prints the reading.

  python3 docs/RESEARCH/glessner-prairie-front-T-2857/read_front.py
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, least_squares

ROOT = Path(__file__).resolve().parents[3]
VIEWS = ROOT / "data/reference_views/glessner_house"
FT = 0.3048
FRONT_U, FRONT_LEN = 49.149, 22.5552          # the Prairie wall plane and its 74'-0" (m)

# The model's Prairie openings (data/structures/glessner_house.json, form.openings_prairie),
# feet from the north end: (label, north jamb, south jamb).
MODEL = {"ff_A": (8.1, 12.0), "ff_B": (16.9, 20.8), "door": (30.4, 35.4), "ff_C": (45.1, 49.0),
         "ff_D": (54.4, 58.3), "2f_trio_N": (9.3, 19.4), "2f_four": (26.2, 40.0),
         "2f_trio_S": (46.7, 56.8), "2f_single": (64.6, 68.0), "ff_pair": (63.5, 69.3),
         "ff_pair_S": (67.0, 69.3)}

# HABS sheet 6 (prairie_1904_v1/research/public/glessner-habs-sheet-6.png, 9626 px wide):
# its feet scale bar reads 0 / 4 / 8 / 12 ft at x 2085 / 2389 / 2686 / 2991.
SHEET_BAR = [(0, 2085), (4, 2389), (8, 2686), (12, 2991)]
SHEET_S_CORNER, SHEET_N_CORNER = 2533, 8109
SHEET_DOWNSPOUT = {"north": (8027, 8056), "south": (2585, 2605)}
SHEET = {"ff_A": (7567, 7231), "ff_B": (6882, 6551), "ff_C": (4727, 4400), "ff_D": (4040, 3707),
         "2f_trio_N": (7432, 6668), "2f_four": (6153, 5103), "2f_trio_S": (4594, 3832),
         "2f_single": (3235, 2985), "ff_pair_S": (3083, 2892), "door_fan_centre": (5657, 5657)}

# Photograph picks: x of each jamb (north, south) on the photograph's own pixels.
PHOTO = {
    "taylor-2135-ne": {"ff_A": (818.5, 761.5), "ff_B": (693.5, 640), "door": (511, 454),
                       "ff_C": (344, 303.5), "ff_D": (248.5, 210), "N_corner": 906.3},
    "habs-17-habs-ne": {"ff_A": (1128, 1087), "ff_B": (1041, 1006), "door": (919, 881),
                        "ff_C": (806, 778), "ff_D": (747, 719), "N_corner": 1195},
    "habs-16-prairie-front": {"ff_A": None, "ff_B": None, "door": (1576, 1494), "ff_C": (1322, 1251),
                              "ff_D": (1171, 1096), "2f_four": (1642, 1412), "2f_trio_S": (1294, 1124),
                              "2f_single": (985, 931), "ff_pair": (1010, 909), "S_corner": 843},
}
# Stack tops and side faces on Taylor 2135, photograph | render (offset 1624 in the side-by-side).
STACKS = {"south": ((317, 413, 272), (None, 391, 274)), "middle": ((667, 742, 227), (646, 723, 226)),
          "north": ((991, 1065, 174), (978, 1050, 175))}


def homography_1d(s, x):
    f = lambda p, t: (p[0] * t + p[1]) / (p[2] * t + 1)
    fit = least_squares(lambda p: f(p, s) - x, [(x[-1] - x[0]) / (s[-1] - s[0]), x[0], 0.0])
    return (lambda t: f(fit.x, t)), f(fit.x, s) - x


def main():
    pxft = np.polyfit([b[0] for b in SHEET_BAR], [b[1] for b in SHEET_BAR], 1)[0]
    print(f"sheet 6: {pxft:.2f} px/ft; Prairie front {(SHEET_N_CORNER - SHEET_S_CORNER) / pxft:.2f} ft (printed 74'-0\")")
    from_n = lambda x: (SHEET_N_CORNER - x) / pxft
    for side, (a, b) in SHEET_DOWNSPOUT.items():
        corner = SHEET_N_CORNER if side == "north" else SHEET_S_CORNER
        print(f"  {side} downspout centre {abs(corner - (a + b) / 2) / pxft:.2f} ft in from its corner")
    print("\nopening      model (ft from N)   sheet 6           centre shift (+ = sheet further north)")
    for k, (xn, xs) in SHEET.items():
        sn, ss = from_n(xn), from_n(xs)
        m = MODEL.get(k) or MODEL["door"]
        print(f"  {k:<16} {m[0]:5.1f}-{m[1]:5.1f}   {sn:5.2f}-{ss:5.2f}   {(m[0] + m[1]) / 2 - (sn + ss) / 2:+.2f}")

    print("\ncamera-free: the photographs' jambs against the model's spacing (1-D projective fit)")
    for view, picks in PHOTO.items():
        s, x = [], []
        for k, v in picks.items():
            if k in MODEL and v:
                s += list(MODEL[k]); x += list(v)
        s, x = np.array(s), np.array(x, float)
        fx, r = homography_1d(s, x)
        line = f"  {view:<22} {len(s)} jambs, rms {np.sqrt(np.mean(r ** 2)):.2f} px"
        for corner, at in (("N_corner", 0.0), ("S_corner", 74.0)):
            if corner in picks:
                where = brentq(lambda t: fx(t) - picks[corner], at - 15, at + 15)
                line += f"; its {corner[0]} corner pick reads at {where:.2f} ft from N (model {at:.0f})"
        print(line)

    cam = json.loads((VIEWS / "taylor-2135-ne.json").read_text())
    e, (R, U, F) = np.array(cam["eye"]), [np.array(t) for t in cam["basis_right_up_forward"]]
    def proj(p):
        d = np.array(p) - e
        z = d @ F
        return cam["principal_px"][0] + cam["focal_px"] * (d @ R) / z
    res = []
    for k in ("ff_A", "ff_B", "ff_C", "ff_D", "door"):
        y = 1.4 if k == "door" else 3.84
        for at, px in zip(MODEL[k], PHOTO["taylor-2135-ne"][k]):
            res.append(proj((FRONT_U, FRONT_LEN - at * FT, y)) - px)
    res = np.array(res)
    print(f"\nTaylor 2135's committed camera, the jambs as withheld checks: rms {np.sqrt(np.mean(res ** 2)):.1f} px, "
          f"mean {res.mean():+.1f} px (render left of the photograph)")
    print("\nTaylor 2135 stacks, photograph vs render: top y, south face x")
    for k, (p, r) in STACKS.items():
        print(f"  {k:<7} top {p[2]} vs {r[2]} ({r[2] - p[2]:+d} px)   right face {p[1]} vs {r[1]} ({r[1] - p[1]:+d} px)")


if __name__ == "__main__":
    main()
