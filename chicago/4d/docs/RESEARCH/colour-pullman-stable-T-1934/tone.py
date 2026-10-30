"""T-1934: the Pullman stable's and palm house range's stone, read from three monochrome prints.

    python3 tone.py          (from chicago/4d/)

Measures the median grey of named boxes on the source scans, then sets each surface against
the slate roof and the house's wall in the same light (the method of
docs/RESEARCH/colour-1700-block-T-3244/), and prints each stone hypothesis's ratio to slate on
a blue-sensitive and an orthochromatic plate.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "data" / "sources" / "assets"
PRINTS = {
    "Taylor 16554 (winter, overcast)": (A / "pullman_1729_stable_t3193" / "aic_taylor_16554_pullman_from_sw.jpg", {
        "stable lower wall, south": (910, 517, 937, 543),
        "stable upper wall, south": (903, 467, 937, 480),
        "stable roof slate": (877, 403, 943, 437),
        "palm house range wall, left": (585, 480, 620, 497),
        "palm house range wall, right of drum": (762, 490, 790, 505),
        "house wall": (340, 500, 363, 533),
        "house mansard slate": (330, 350, 363, 383),
        "sky": (600, 100, 800, 200),
    }),
    "Taylor 1445 (overcast)": (A / "pullman_1729_taylor_t3161" / "taylor_1445_print_16399.jpg", {
        "stable upper wall": (957, 580, 995, 590),
        "stable lower wall": (980, 597, 1015, 610),
        "stable roof slate": (902, 537, 977, 562),
        "sky": (900, 150, 1100, 250),
    }),
    "Inland Architect plate 1894 (sun)": (A / "pullman_1729_stable_t3193" / "inland_1894_pullman_palm_house_stable.jpg", {
        "stable south upper wall, lit": (1180, 670, 1260, 700),
        "belvedere wall, lit": (830, 470, 860, 530),
        "stable roof slate, south slope": (1700, 420, 1850, 500),
        "sidewalk": (1000, 1100, 1300, 1120),
        "sky": (700, 200, 1000, 300),
    }),
}
BLACK = 30          # the darkest open shadow in the winter print (windows), a print's black

BANDS = {"blue plate": np.array([0.05, 0.15, 0.80]), "ortho plate": np.array([0.05, 0.45, 0.50])}
SLATE = np.array([0.12, 0.12, 0.12])
# the house's walls since T-1881: K02 sandstone_fawn, mean sRGB 146,131,110 (docs/RESEARCH/pullman-stone-1881/)
FAWN = tuple(((c / 255 + 0.055) / 1.055) ** 2.4 for c in (146, 131, 110))
H = {"brownstone (K02 sandstone_brown, before T-1881)": (0.21, 0.13, 0.10),
     "the house's sandstone_fawn": FAWN,
     "draft stone, as the stable was built": (0.40, 0.36, 0.29),
     "light stone, as the palm house range was built": (0.66, 0.62, 0.54),
     "first reading: draft stone x 0.58": (0.232, 0.209, 0.168),
     "chosen: draft stone x 0.83": (0.332, 0.299, 0.241)}

for name, (path, boxes) in PRINTS.items():
    g = np.asarray(Image.open(path).convert("L")).astype(float)
    print(name)
    for k, (x0, y0, x1, y1) in boxes.items():
        print(f"  {k:40s} {np.median(g[y0:y1, x0:x1]):6.1f}")

print("\nwinter print, reflectance ratios at gamma 1.8-2.2 (print black", BLACK, ")")
for a, b, va, vb in (("stable wall", "house wall", 148, 129), ("stable wall", "its slate roof", 148, 146),
                     ("stable wall", "house mansard slate", 148, 141)):
    r = (va - BLACK) / (vb - BLACK)
    print(f"  {a} / {b}: {r ** 1.8:.2f}-{r ** 2.2:.2f}")

print("\nhypotheses, ratio to slate, and to the house's fawn wall (the print wants 1.37-1.47)")
for name, c in H.items():
    print(f"  {name:48s}", "  ".join(f"{k} {(np.array(c) @ w) / (SLATE @ w):.2f} / {(np.array(c) @ w) / (np.array(FAWN) @ w):.2f}"
                                     for k, w in BANDS.items()))
