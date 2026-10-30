#!/usr/bin/env python3
"""Count the stable roof's courses in the Cornell c. 1887 print against the render (T-3025).

The print and the render on the committed side-by-side share one solved camera, so the same
pixel column crosses the same roof plane in both. The vertical period of the courses is read
per column with a Hann-windowed FFT and the power summed over a band of columns (the phase of
the courses drifts across a band, the period does not). The render lays courses at the record's
5 in exposure (masonry_house_v4_materials.py, 16 rows of 5 in), so the ratio of the two periods
is the print's exposure in units of 5 in.

    python3 docs/RESEARCH/glessner-roof-covering-T-3025/read_courses.py
"""
import json
import pathlib

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[3]
SBS = ROOT / "docs/RESEARCH/photo-match/glessner_house/cornell-northwest-west-windows-side-by-side.jpg"
PHOTO_W = 1800                       # each half of the side-by-side, native pixels
ROWS = {"print": (300, 450), "render": (310, 460)}  # inside the roof field on both halves
BANDS = [(1000, 1030), (1040, 1080), (1090, 1120)]  # columns between the cupola and the gable
EXPOSURE_IN = 5.0                    # the render's course, from the record (HABS data p. 21)


def period(img, x0, x1, y0, y1, xo):
    power = None
    for x in range(x0, x1):
        col = img[y0:y1, x + xo].copy()
        col -= col.mean()
        col *= np.hanning(len(col))
        p = np.abs(np.fft.rfft(col, n=1024)) ** 2
        power = p if power is None else power + p
    f = np.fft.rfftfreq(1024)
    band = (f > 1 / 12) & (f < 1 / 2.5)
    return float(1 / f[np.argmax(power * band)])


def main():
    img = np.asarray(Image.open(SBS).convert("L"), float)
    off = img.shape[1] - PHOTO_W
    rows = []
    for x0, x1 in BANDS:
        pp = period(img, x0, x1, *ROWS["print"], 0)
        pr = period(img, x0, x1, *ROWS["render"], off)
        rows.append({"columns": [x0, x1], "print_px": round(pp, 2), "render_px": round(pr, 2),
                     "ratio": round(pp / pr, 3), "print_exposure_in": round(EXPOSURE_IN * pp / pr, 2)})
    ratios = [r["ratio"] for r in rows]
    out = {"side_by_side": str(SBS.relative_to(ROOT)), "bands": rows,
           "mean_ratio": round(sum(ratios) / len(ratios), 3),
           "print_exposure_in": round(EXPOSURE_IN * sum(ratios) / len(ratios), 2)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
