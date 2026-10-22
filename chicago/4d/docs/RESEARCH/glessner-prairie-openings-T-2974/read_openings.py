"""T-2974: Glessner's Prairie openings read on HABS sheet 6 against its own drawn bed joints.

Reads the committed 400-dpi scan (prairie_1904_v1/research/public/glessner-habs-sheet-6.png).
Vertical scale from the sheet's printed 0.00 (y 5952) and 24.30 (y 4127): 75.1 px a foot.
Horizontal from T-2857's scale bar and north corner (75.5 px a foot, x 8109).

The scan is turned slightly (the walk reads -0.72 at light A and -0.85 at light D), so each
opening is also read against the bed the sheet draws seventh beside it, the door head's
joint, which the printed string sets at 7.50: relative = reading - local bed 7 + 7.50.

    python3 docs/RESEARCH/glessner-prairie-openings-T-2974/read_openings.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[4]
SHEET = ROOT / "prairie_1904_v1/research/public/glessner-habs-sheet-6.png"
COURSES_IN = [18, 18, 15.5, 9.5, 13.5, 14.5, 7.5, 14.5, 7.5, 11.5, 7.5, 11.5, 7.5, 9.5, 7.5, 20]

H = lambda y: (5952 - y) / 75.1
Y = lambda h: 5952 - h * 75.1
X = lambda s: 8109 - s * 75.5          # s: feet from the north end


def beds():
    z, out = -0.54, []
    for c in COURSES_IN:
        z += c / 12
        out.append(round(z, 3))
    return out


def lines(im, x0, x1, h0, h1, thr):
    y0, y1 = int(Y(h1)), int(Y(h0))
    s = im[y0:y1, x0:x1].mean(1)
    groups = []
    for i, v in enumerate(s):
        if v > thr:
            if groups and i - groups[-1][-1] <= 2:
                groups[-1].append(i)
            else:
                groups.append([i])
    return [round(H(y0 + float(np.mean(g))), 2) for g in groups]


def main():
    im = np.array(Image.open(SHEET)) < 128
    print("printed string, beds over the door datum:", beds())
    lights = {"A": (7.19, 11.65), "B": (16.28, 20.67), "C": (44.87, 49.21), "D": (53.98, 58.40)}
    grilles = {"A": (7.47, 11.37), "B": (16.53, 20.43), "C": (45.09, 48.99), "D": (54.24, 58.14)}
    print("light  bed7   sill   head  | relative: sill   head  height")
    for k, (n, s) in lights.items():
        xa, xb = X(s), X(n)
        x0, x1 = int(xa + 0.12 * (xb - xa)), int(xa + 0.32 * (xb - xa))
        ls = lines(im, x0, x1, 8.0, 15.5, 0.6)
        b7 = np.mean(lines(im, int(xb) + 0, int(xb) + 120, 7.2, 8.0, 0.45))
        sill, head = ls[-1], ls[0]
        print(f"  {k}   {b7:5.2f}  {sill:5.2f}  {head:5.2f}  |          {sill - b7 + 7.5:5.2f}  "
              f"{head - b7 + 7.5:5.2f}  {head - sill:5.2f}")
    print("grille  head   bed7 | relative head")
    for k, (n, s) in grilles.items():
        xa, xb = X(s), X(n)
        x0, x1 = int(xa + 0.12 * (xb - xa)), int(xa + 0.32 * (xb - xa))
        head = lines(im, x0, x1, 0.3, 5.2, 0.6)[0]
        b7 = np.mean(lines(im, int(xb) + 0, int(xb) + 120, 7.2, 8.0, 0.45))
        print(f"  {k}    {head:5.2f}  {b7:5.2f} |  {head - b7 + 7.5:5.2f}")


if __name__ == "__main__":
    main()
