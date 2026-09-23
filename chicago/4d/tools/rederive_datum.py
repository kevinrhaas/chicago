#!/usr/bin/env python3
"""Re-derive the datum origin from the committed ground-control traces.

The datum is not a number someone typed — it is the output of a computation whose
inputs are all in the repo. This script re-runs that computation from
data/traces/gcp/*.json and asserts data/datum.json still matches, so the
derivation can never silently drift from its evidence.

    python3 tools/rederive_datum.py            re-derive and compare
    python3 tools/rederive_datum.py --print    also print transforms and residuals

Needs pyproj (pip install pyproj). check.sh treats a missing pyproj as a skip,
not a failure, so agent sandboxes without it still gate on everything else.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The derived origin may drift from a re-fit by at most this much before the
# check fails. Fit RMS is ~18 m; a tolerance of 1 m catches data edits while
# ignoring floating-point noise.
TOLERANCE_M = 1.0


def lstsq_affine(rows):
    """Least-squares affine (x,y)->(E,N) via normal equations. rows: (x, y, E, N)."""
    def solve3(ata, atb):
        m = [ata[i][:] + [atb[i]] for i in range(3)]
        for i in range(3):
            p = max(range(i, 3), key=lambda r: abs(m[r][i]))
            m[i], m[p] = m[p], m[i]
            for r in range(3):
                if r != i:
                    f = m[r][i] / m[i][i]
                    m[r] = [m[r][k] - f * m[i][k] for k in range(4)]
        return [m[i][3] / m[i][i] for i in range(3)]

    ata = [[0.0] * 3 for _ in range(3)]
    ate, atn = [0.0] * 3, [0.0] * 3
    for x, y, e, n in rows:
        v = [x, y, 1.0]
        for i in range(3):
            for j in range(3):
                ata[i][j] += v[i] * v[j]
            ate[i] += v[i] * e
            atn[i] += v[i] * n
    return solve3(ata, ate), solve3(ata, atn)


def fit_from_traces(path, transformer):
    doc = json.loads((ROOT / path).read_text())
    rows = []
    for g in doc["gcps"]:
        e, n = transformer.transform(g["modern"]["lon"], g["modern"]["lat"])
        rows.append((g["pixel"][0], g["pixel"][1], e, n))
    (a, b, c), (d, e_, f) = lstsq_affine(rows)
    sq = sum((a * x + b * y + c - E) ** 2 + (d * x + e_ * y + f - N) ** 2
             for x, y, E, N in rows)
    rms = math.sqrt(sq / len(rows))
    return (a, b, c, d, e_, f), rms, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="verbose", action="store_true")
    args = ap.parse_args()

    try:
        from pyproj import Transformer
    except ImportError:
        print("SKIP: pyproj not installed (pip install pyproj); datum re-derivation not run")
        return 0

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    if not datum.get("verified"):
        print("datum is not verified; nothing to re-derive against")
        return 0

    t = Transformer.from_crs(4326, 26916, always_xy=True)
    inv = Transformer.from_crs(26916, 4326, always_xy=True)

    coef, rms, rows = fit_from_traces("data/traces/gcp/wright_1834_gcps.json", t)
    a, b, c, d, e_, f = coef

    fx, fy = datum["derivation"]["forks_pixel_wright"]
    E, N = a * fx + b * fy + c, d * fx + e_ * fy + f

    dE = E - datum["origin_utm_e"]
    dN = N - datum["origin_utm_n"]
    drift = math.hypot(dE, dN)

    if args.verbose:
        print(f"refit affine: E={a:.6f}x{b:+.6f}y{c:+.3f}  N={d:.6f}x{e_:+.6f}y{f:+.3f}")
        print(f"refit RMS {rms:.1f} m over {len(rows)} GCPs")
        print(f"forks pixel ({fx},{fy}) -> E {E:.1f}  N {N:.1f}")
        lon, lat = inv.transform(E, N)
        print(f"                          = {lat:.6f}, {lon:.6f}")

    print(f"re-derived origin drift vs datum.json: {drift:.2f} m "
          f"(tolerance {TOLERANCE_M} m); fit RMS {rms:.1f} m "
          f"(recorded {datum['derivation']['residual_m']} m)")

    if drift > TOLERANCE_M:
        print("FAIL: the committed datum no longer matches its own ground control. "
              "Either the traces were edited (re-run the derivation deliberately and "
              "update datum.json + the memo) or datum.json was hand-edited (revert it).")
        return 1
    print("OK: datum.json matches its ground control")
    return 0


if __name__ == "__main__":
    sys.exit(main())
