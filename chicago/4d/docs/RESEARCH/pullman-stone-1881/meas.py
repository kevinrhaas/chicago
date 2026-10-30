"""T-1881: the print values behind 1729 Prairie's stone (README table).

    curl -L -o /tmp/4a08065u.tif https://cdn.loc.gov/master/pnp/det/4a00000/4a08000/4a08000/4a08065u.tif
    python3 meas.py /tmp/4a08065u.tif

Boxes are in the master scan's pixels (5149 x 4044); the Taylor boxes are in the committed
1200 x 923 copy (data/sources/assets/pullman_1729_taylor_t3161/taylor_1445_album_p69.jpg).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TAYLOR = HERE.parents[2] / "data/sources/assets/pullman_1729_taylor_t3161/taylor_1445_album_p69.jpg"
DETROIT = {   # x0, y0, x1, y1 on the master scan
    "wall, second storey, by the pier": (2403, 1759, 2483, 1879),
    "wall, second storey, centre":      (2168, 1709, 2243, 1879),
    "wall, second storey, north":       (1738, 1719, 1818, 1879),
    "slate mansard, south section":     (2148, 1464, 2228, 1509),
    "slate mansard, centre":            (1928, 1464, 2028, 1509),
    "sky":                              (3500, 100, 4500, 400),
}
TAYLOR_BOXES = {
    "flank wall": (470, 420, 530, 480), "flank wall, east": (580, 400, 640, 470),
    "front wall": (230, 400, 270, 450), "mansard": (560, 255, 620, 290),
    "mansard, front": (250, 255, 300, 290), "coping wall": (100, 660, 280, 690),
}


def boxes(path, table):
    a = np.asarray(Image.open(path).convert("L"))
    for k, (x0, y0, x1, y1) in table.items():
        print(f"  {k:34s} median {np.median(a[y0:y1, x0:x1]):6.1f}")


if len(sys.argv) > 1:
    print("Detroit print, LoC det 4a08065 (master scan)")
    boxes(sys.argv[1], DETROIT)
print("Taylor no. 1445")
boxes(TAYLOR, TAYLOR_BOXES)
print("wall / slate reflectance through a print's tone curve (black 7)")
for w, s in ((128, 87), (120, 73), (135, 101)):
    r = (w - 7) / (s - 7)
    print(f"  wall {w} slate {s}: {r ** 1.8:.2f}-{r ** 2.2:.2f}")
