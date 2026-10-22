"""T-2986: Glessner's granite course string re-read on HABS sheet 5, and set against sheet 6's beds.

Reads two committed 400-dpi scans (prairie_1904_v1/research/public/):

- sheet 5 (1963, D. T. Van Zanten, 1/4" = 1'-0"): the joint pairs the printed string runs between,
  down the 18th Street entrance's elevation (x 1530-1600, clear of the figures), at the sheet's
  own 98.8 px a foot (T-2913: the door frame, 494 x 751 px for 5.0 x 7.60 ft);
- sheet 6 (1965, photogrammetric, plotted at Ohio State): the beds drawn on the Prairie front at
  three clear piers, at 75.1 px a foot from its printed 0.00 (y 5952) and 24.30 (y 4127), as T-2974.

The figures themselves are read by eye (see the README's crop); PRINTED_IN is that reading.

    python3 docs/RESEARCH/glessner-coursing-T-2986/read_coursing.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[4]
PUBLIC = ROOT / "prairie_1904_v1/research/public"

# Sheet 5's string, bottom to top, as printed. The record's v4_detail.ashlar_courses_in has 9.5
# for the 22nd: the sheet prints 8 1/2.
PRINTED_IN = [18, 18, 15.5, 9.5, 13.5, 14.5, 7.5, 14.5, 7.5, 11.5, 7.5, 11.5, 7.5, 9.5, 7.5,
              20, 8.5, 11.5, 17.5, 7.5, 9.5, 8.5, 9.5, 4]
RECORD_IN = PRINTED_IN[:21] + [9.5] + PRINTED_IN[22:]
BASE = -0.54          # the string's base line over the door datum (T-2913, T-2955)
S5_PX_FT = 98.8


def line_rows(im, x0, x1, y0, y1, thr):
    """Rows (scan y) of horizontal lines in a strip, each pair of joint lines merged to its middle."""
    r = im[y0:y1, x0:x1].mean(1)
    runs = []
    for i, v in enumerate(r):
        if v > thr:
            if runs and i - runs[-1][-1] <= 2:
                runs[-1].append(i)
            else:
                runs.append([i])
    ys = [y0 + float(np.mean(g)) for g in runs]
    out = []
    for y in ys:                                   # a joint is drawn as two lines 6-12 px apart
        if out and y - out[-1][-1] <= 13:
            out[-1].append(y)
        else:
            out.append([y])
    return [float(np.mean(g)) for g in out]


def beds(courses):
    z, out = BASE, []
    for c in courses:
        z += c / 12
        out.append(round(z, 2))
    return out


def sheet5():
    im = np.array(Image.open(PUBLIC / "glessner-habs-sheet-5.png")) < 128
    ys = line_rows(im, 1530, 1600, 840, 3270, 0.2)
    # bottom up: the base line (y 3258), 24 course joints, then the band and top line above the string
    ys = sorted(ys, reverse=True)
    base, joints = ys[0], ys[1:25]
    print("SHEET 5 — the printed string against the joints it is written between")
    print(" course  printed  drawn(in)  drawn/printed")
    prev = base
    for k, (c, y) in enumerate(zip(PRINTED_IN, joints), 1):
        d = (prev - y) / S5_PX_FT * 12
        print(f"   {k:2d}    {c:5.1f}    {d:5.1f}      {d / c:4.2f}")
        prev = y
    top = (base - joints[-1]) / S5_PX_FT
    print(f" sum printed {sum(PRINTED_IN)} in = {sum(PRINTED_IN) / 12:.2f} ft;"
          f" drawn base to top joint {base - joints[-1]:.0f} px = {top:.2f} ft"
          f" ({top / (sum(PRINTED_IN) / 12) - 1:+.1%})")
    lo = (base - joints[1]) / S5_PX_FT * 12
    print(f" courses 1-2: drawn {lo:.1f} in against 36; courses 3-24:"
          f" {(joints[1] - joints[-1]) / S5_PX_FT * 12:.1f} in against {sum(PRINTED_IN[2:])}")


def sheet6():
    im = np.array(Image.open(PUBLIC / "glessner-habs-sheet-6.png")) < 128
    H = lambda y: (5952 - y) / 75.1
    Y = lambda h: 5952 - h * 75.1
    X = lambda s: 8109 - s * 75.5
    printed = beds(PRINTED_IN)
    print("\nSHEET 6 — the beds the plot draws on three piers (ft over the door datum, sheet scale)")
    for s0, s1 in [(2.0, 4.0), (22.0, 24.0), (40.0, 43.0)]:
        ys = line_rows(im, int(X(s1)), int(X(s0)), int(Y(24.4)), int(Y(7.3)), 0.5)
        hs = sorted(round(H(y), 2) for y in ys)
        print(f" S {s0:4.1f}-{s1:4.1f}: {hs}")
    print(" printed beds 7-24:", printed[6:])


def main():
    print("record's 22nd course:", RECORD_IN[21], "in; the sheet prints", PRINTED_IN[21], "in;",
          f"bed 23 {beds(RECORD_IN)[22]} -> {beds(PRINTED_IN)[22]} ft over the door datum")
    sheet5()
    sheet6()


if __name__ == "__main__":
    main()
