"""T-2985: Glessner's Prairie second-floor sills and the carved band, read on HABS sheet 6.

Reads the committed 400-dpi scan (prairie_1904_v1/research/public/glessner-habs-sheet-6.png)
on T-2974's scale: printed 0.00 (y 5952) and 24.30 (y 4127), 75.1 px a foot; horizontally
T-2857's scale bar, 75.5 px a foot from x 8109. Each light is read from its heavy head line
to its heavy sill line, and the sill is then put under the printed 24.30, because the scan's
turn shifts both lines alike along the front.

    python3 docs/RESEARCH/glessner-second-floor-sills-T-2985/read_sills.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[4]
SHEET = ROOT / "prairie_1904_v1/research/public/glessner-habs-sheet-6.png"
H = lambda y: (5952 - y) / 75.1
Y = lambda h: int(round(5952 - h * 75.1))
X = lambda s: int(round(8109 - s * 75.5))
LIGHTS = {"single": [(64.81, 67.50)],
          "three, north": [(54.44, 56.30), (50.69, 52.41), (46.85, 48.32)],
          "four": [(37.67, 39.39), (33.95, 35.60), (29.95, 31.71), (26.25, 27.92)],
          "three, south": [(16.85, 18.68), (13.15, 14.75), (9.30, 11.05)]}


def heavy(im, c0, c1, h0, h1):
    ya, yb = Y(h1), Y(h0)
    p = im[ya:yb, c0:c1].mean(1)
    i = int(np.argmax(p))
    near = [j for j in range(max(0, i - 3), min(len(p), i + 4)) if p[j] > 0.6 * p[i]]
    return H(ya + float(np.mean(near)))


def main():
    im = np.array(Image.open(SHEET)) < 128
    print("group          light S        head    sill  | height  sill under 24.30")
    for g, ls in LIGHTS.items():
        for a, b in ls:
            c0, c1 = X(b) + 25, X(a) - 25
            sill = heavy(im, c0, c1, 19.0, 19.6)
            head = heavy(im, c0, c1, sill + 4.95, sill + 5.22)   # the soffit, not the cornice above
            print(f"{g:13s} {a:5.2f}-{b:5.2f}  {head:6.2f}  {sill:6.2f}  |  {head - sill:5.2f}   {24.30 - (head - sill):6.2f}")
    # The carved band under the group of four: its course at S 33, and its two end blocks.
    c0, c1 = X(33.5), X(32.5)
    sill = heavy(im, c0, c1, 19.0, 19.6)
    bottom = heavy(im, c0, c1, 18.1, 18.45)
    print(f"band at S 33: top (the sill line) {sill:.2f}, bottom {bottom:.2f}, {sill - bottom:.2f} ft deep")
    for lo, hi in ((22.5, 26.5), (39.0, 43.2)):
        col = im[Y(19.2):Y(18.45), X(hi):X(lo)].mean(0)
        edges = [round((8109 - (X(hi) + i)) / 75.5, 2) for i, v in enumerate(col) if v > 0.75]
        print(f"end block edges between S {lo} and {hi}:", sorted(set(round(e, 1) for e in edges)))


if __name__ == "__main__":
    main()
