#!/usr/bin/env python3
"""T-3058: the plumb edges of Taylor 2135, read for the camera's pitch and roll.

A freed principal point trades against pitch: on the jambs and the stacks alone the solve
tips the camera about 3 degrees up and drops the principal point to match. The photograph
says how much it is tipped by itself. Every plumb edge in it (a window jamb, a pier's arris,
a downspout, a corner) leans toward the vertical vanishing point, and the lean across the
frame is the pitch; its mean, with the principal point, is the roll.

Each edge is found as a ridge of the horizontal gradient that runs most of a band of rows,
located row by row to a tenth of a pixel and fitted as a line. Trees and the lamp post are
left out by column; a line whose rows scatter more than 0.6 px, or which is not found in
most rows of its band, is not a plumb edge and is dropped. Nothing here is picked by hand.

  python3 docs/RESEARCH/glessner-taylor-camera-T-3058/read_verticals.py   write verticals.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PHOTO = ROOT / "docs/RESEARCH/glessner-rainwater-T-2221/reference/taylor-2135.jpg"
OUT = HERE / "verticals.json"

# Bands of rows on the two lit fronts: the Prairie front's second and first storeys and the
# 18th Street flank's (photograph px). Columns that are not the house: the two street trees
# before the flank, the one before the front, the lamp post, and the frame's edges.
BANDS = ((520, 600), (600, 680), (680, 760), (780, 870))
EXCLUDE = ((0, 60), (335, 385), (860, 895), (1120, 1180), (1215, 1270), (1500, 1600))
MIN_SCORE = 4.0        # mean |gradient| along the band, grey levels per px
MAX_SD = 0.6           # px, the rows' scatter about the fitted line
MIN_ROWS = 0.75        # share of the band's rows the ridge is found in


def edges(g, y0, y1):
    gx = sobel(g, axis=1)[y0:y1]
    score = np.abs(gx.mean(0))          # a straight plumb edge keeps its sign down the band
    found = []
    for x in range(3, g.shape[1] - 3):
        if any(a <= x < b for a, b in EXCLUDE) or score[x] < MIN_SCORE:
            continue
        if score[x] < score[x - 2:x + 3].max():
            continue
        sign = np.sign(gx[:, x].mean())
        xs, ys = [], []
        for i, row in enumerate(gx):
            w = sign * row[x - 3:x + 4]
            k = int(np.argmax(w))
            if 0 < k < 6 and w[k] > 0.5 * score[x]:
                a, b, c = w[k - 1], w[k], w[k + 1]
                xs.append(x - 3 + k + 0.5 * (a - c) / (a - 2 * b + c))
                ys.append(y0 + i)
        if len(ys) < MIN_ROWS * (y1 - y0):
            continue
        ys, xs = np.array(ys, float), np.array(xs)
        ym = ys.mean()
        lean, x_m = np.polyfit(ys - ym, xs, 1)
        sd = float(np.std(xs - (x_m + lean * (ys - ym))))
        if sd <= MAX_SD:
            found.append({"x": round(float(x_m), 2), "y": round(float(ym), 1), "lean": round(float(lean), 5),
                          "rows": int(len(ys)), "sd_px": round(sd, 3), "band": [y0, y1]})
    return found


def main():
    g = gaussian_filter(np.asarray(Image.open(PHOTO).convert("L"), float), 1.0)
    found = [e for y0, y1 in BANDS for e in edges(g, y0, y1)]
    # Robust cut: an edge whose lean departs from the frame's linear trend by more than three
    # robust deviations is a sloped feature (a rake, a hood's return), not a plumb line.
    x = np.array([e["x"] for e in found]); t = np.array([e["lean"] for e in found])
    keep = np.ones(len(found), bool)
    for _ in range(5):
        a = np.polyfit(x[keep], t[keep], 1)
        r = t - np.polyval(a, x)
        mad = 1.4826 * np.median(np.abs(r[keep] - np.median(r[keep])))
        keep = np.abs(r) <= 3 * mad
    kept = [e for e, k in zip(found, keep) if k]
    a = np.polyfit(x[keep], t[keep], 1)
    sd = float(np.std(t[keep] - np.polyval(a, x[keep])))
    out = {
        "ticket": "T-3058",
        "not_a_reading": "an instrument reading of Taylor 2135's plumb edges for its camera; it rules on no unit",
        "photo": str(PHOTO.relative_to(ROOT)),
        "method": __doc__.split("\n\n")[2].replace("\n", " "),
        "bands_px": BANDS, "excluded_columns_px": EXCLUDE,
        "found": len(found), "kept": len(kept),
        "lean_trend": {"at_x0": round(float(a[1]), 6), "per_px": float(f"{a[0]:.4g}")},
        "lean_sd": round(sd, 5),
        "edges": kept,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(kept)} of {len(found)} edges kept, lean sd {sd:.4f}, "
          f"trend {a[0]:.3g}/px")


if __name__ == "__main__":
    main()
