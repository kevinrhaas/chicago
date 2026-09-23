#!/usr/bin/env python3
"""Convert Wright-1834 raster pixels to local ENU metres, and back.

The affine was fitted once, from the eight ground-control points in
`data/traces/gcp/wright_1834_gcps.json`, and is the same transform
`tools/rederive_datum.py` checks the datum against on every commit. Nothing here
re-fits anything: this is the read side, so a feature read off the sheet lands in
the same frame as everything else in the project.

    tools/wright_px.py 3080 1540            # one point
    tools/wright_px.py --inverse 1152 221   # local ENU -> pixel
    tools/wright_px.py --region -400 -700 1900 700   # IIIF region for a bbox

Why pixels are committed rather than only the resulting metres: a reading taken
by eye off a raster is evidence about the raster, and the next person needs to be
able to re-open the sheet at that spot and disagree with it. Metres alone hide
where the number came from.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    g = json.loads((ROOT / "data/traces/gcp/wright_1834_gcps.json").read_text())
    d = json.loads((ROOT / "data/datum.json").read_text())
    c = g["fit"]["coefficients"]
    return g, d, (c["a"], c["b"], c["c"], c["d"], c["e"], c["f"])


def to_local(px: float, py: float) -> tuple[float, float]:
    """Raster pixel -> metres east/north of the scene datum."""
    g, d, (a, b, c, dd, e, f) = _load()
    E = a * px + b * py + c
    N = dd * px + e * py + f
    return E - d["origin_utm_e"], N - d["origin_utm_n"]


def to_pixel(local_e: float, local_n: float) -> tuple[float, float]:
    """Metres east/north of the datum -> raster pixel."""
    g, d, (a, b, c, dd, e, f) = _load()
    E = local_e + d["origin_utm_e"] - c
    N = local_n + d["origin_utm_n"] - f
    det = a * e - b * dd
    return (E * e - b * N) / det, (a * N - dd * E) / det


def iiif_region(e0, n0, e1, n1, width=1400):
    """The IIIF region URL covering a local-ENU bounding box."""
    g, _, _ = _load()
    xs, ys = [], []
    for le, ln in ((e0, n0), (e1, n0), (e1, n1), (e0, n1)):
        x, y = to_pixel(le, ln)
        xs.append(x)
        ys.append(y)
    W, H = g["raster"]["width"], g["raster"]["height"]
    x0, y0 = max(0, int(min(xs))), max(0, int(min(ys)))
    x1, y1 = min(W, int(max(xs))), min(H, int(max(ys)))
    return f"{g['raster']['iiif_image']}/{x0},{y0},{x1-x0},{y1-y0}/{width},/0/default.jpg"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("values", nargs="*", type=float)
    ap.add_argument("--inverse", action="store_true", help="local ENU -> pixel")
    ap.add_argument("--region", action="store_true",
                    help="four values e0 n0 e1 n1 -> the IIIF region URL for that box")
    args = ap.parse_args()

    if args.region:
        if len(args.values) != 4:
            print("--region needs e0 n0 e1 n1", file=sys.stderr)
            return 2
        print(iiif_region(*args.values))
        return 0
    if len(args.values) != 2:
        print("give two values (px py, or local_e local_n with --inverse)", file=sys.stderr)
        return 2
    if args.inverse:
        x, y = to_pixel(*args.values)
        print(f"pixel {x:.0f} {y:.0f}")
    else:
        le, ln = to_local(*args.values)
        print(f"local E {le:+.1f}  N {ln:+.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
