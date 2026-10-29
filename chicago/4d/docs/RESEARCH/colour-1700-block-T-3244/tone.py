"""T-3244: the brick hypotheses' print ratios (README table), and the measured ratios.

    python3 tone.py
"""
import numpy as np

TRIM = np.array([0.91, 0.88, 0.79])          # white lead paint, linear
BANDS = {"blue plate": np.array([0.05, 0.15, 0.80]),
         "ortho plate": np.array([0.05, 0.45, 0.50]),
         "eye": np.array([0.2126, 0.7152, 0.0722])}
# mean linear base colour of each K03 web map, and a neutral slate
H = {"common buff brick": (0.407, 0.256, 0.154), "rough red-brown brick": (0.197, 0.098, 0.068),
     "pressed red brick": (0.177, 0.024, 0.015), "slate (neutral 0.12)": (0.12, 0.12, 0.12)}
for name, c in H.items():
    print(f"{name:24s}", "  ".join(f"{k} {(np.array(c) @ w) / (TRIM @ w):.3f}" for k, w in BANDS.items()))

# measured: (picture, brick, white reference, black) -> reflectance ratio at gamma 1.8 / 2.2
for pic, v, w, b in (("Chicagology", 72, 240, 15), ("Christmas print", 100, 168, 5),
                     ("1901 construction (to stone)", 154, 229, 15)):
    r = (v - b) / (w - b)
    print(f"{pic:30s} {r ** 1.8:.2f}-{r ** 2.2:.2f}")
