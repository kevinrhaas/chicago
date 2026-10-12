#!/usr/bin/env python3
"""Relief in shade, before against after, on the T-2209 Glessner stands (T-2393).

    python3 tools/measure_glessner_shade_relief.py BEFORE_DIR AFTER_DIR [stand,stand,...]

Reads `before-desktop-<stand>.png` and `after-desktop-<stand>.png` as written by
`QA_TAG=before- / after- QA_VIEWPORT=desktop node tools/qa_glessner_t2209.mjs` and
prints, over the frame minus the HUD: mean luminance, the mean |Laplacian| T-2209
reported, and the mid-band contrast (std of a 1.5 px minus 12 px Gaussian difference),
which is the 1-5 cm crease scale at these distances. Both contrasts fall with
luminance alone, so each is also given relative to the mean. Needs numpy, scipy, Pillow.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, laplace

STANDS = ("north-close", "north-mid", "north-shaded", "west-alley", "prairie-jambs")


def luminance(path: Path) -> np.ndarray:
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]


def frame(lum: np.ndarray) -> np.ndarray:
    """The 1280x800 frame without the status card, minimap and toolbar."""
    m = np.ones_like(lum, bool)
    m[:215, :270] = False
    m[:60, 770:] = False
    return m


def measure(lum: np.ndarray, m: np.ndarray) -> tuple[float, float, float]:
    lap = float(np.abs(laplace(lum))[m].mean())
    mid = float((gaussian_filter(lum, 1.5) - gaussian_filter(lum, 12))[m].std())
    return float(lum[m].mean()), lap, mid


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    before, after = Path(argv[0]), Path(argv[1])
    stands = argv[2].split(",") if len(argv) > 2 else STANDS
    print("| stand | luminance | mean abs Laplacian | (relative) | mid-band | (relative) |")
    print("|---|---|---|---|---|---|")
    for stand in stands:
        b = luminance(before / f"before-desktop-{stand}.png")
        a = luminance(after / f"after-desktop-{stand}.png")
        m = frame(b)
        (lb, pb, qb), (la, pa, qa) = measure(b, m), measure(a, m)
        pct = lambda x, y: f"{(y / x - 1) * 100:+.1f} %"
        print(f"| {stand} | {lb:.2f} → {la:.2f} ({pct(lb, la)}) | {pb:.2f} → {pa:.2f} ({pct(pb, pa)}) "
              f"| {pct(pb / lb, pa / la)} | {qb:.2f} → {qa:.2f} ({pct(qb, qa)}) | {pct(qb / lb, qa / la)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
