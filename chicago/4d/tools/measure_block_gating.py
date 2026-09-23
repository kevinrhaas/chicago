#!/usr/bin/env python3
"""Why a platted block the grid refuses is refused: short of control, or never a block.

T-0163. `tools/generate_plat_lots.py` builds the platted grid as the CARTESIAN PRODUCT of
the committed east-west rows and north-south columns, and refuses any pairing whose four
centrelines do not meet. It reports each refusal as a distance — "South Water Street's
committed centreline stops 878 m short of this block" — and `tools/reconcile_665.py` then
re-admits two of those refusals as `platted_block_awaiting_street_control`, carrying 27
roofs of headroom each against street control ROADMAP S9 records as owed.

A DISTANCE CANNOT TELL THOSE TWO CASES APART, and they are not the same case:

  * a corner whose two streets genuinely met, whose centreline simply has not been carried
    that far yet — real ground, waiting on a trace; and
  * a pairing of two streets that never met at all, which no trace will ever join, because
    the row does not run that far and never did.

The second is not gated. It is an artifact of the product, and counting its roofs as
headroom promises ground that street control cannot deliver.

THE DISCRIMINATOR IS THE COMMITTED HEIGHTFIELD, NOT AN OPINION. A street's centreline is
carried toward the block it is supposed to bound, and the straight run between them is
sampled against the committed ground: if that run crosses water, the two are on opposite
banks and the pairing is a product artifact — a row on the south bank cannot bound a block
on the west side of the South Branch, whatever a trace does. If the run stays dry, the gap
is ordinary unfinished control and the block is really waiting.

Water is read the way the plat generator itself reads it (`generate_plat_lots.py`): a
sample is wet where the field does not cover it, or covers it below the datum surface.

    tools/measure_block_gating.py            the report
    tools/measure_block_gating.py --check    fail if a refusal's class has moved

Exit 0 pass, 1 on a classification that disagrees with the committed programme, 2 if the
inputs cannot be read.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

STREETS = DATA / "streets" / "1835.json"
PROGRAMME = DATA / "reconstruction" / "1835_665_roof_programme.json"

# How finely the run between a street and its block is sampled for water. The South Branch
# is ~60 m wide here, so a stride well under that cannot step over it.
STRIDE_M = 5.0


def die(msg: str) -> None:
    print(f"cannot measure: {msg}", file=sys.stderr)
    raise SystemExit(2)


def load_streets() -> dict:
    doc = json.loads(STREETS.read_text())
    return {r["id"]: r for r in doc["streets"]}


def centreline(street: dict) -> list[tuple[float, float]]:
    return [(p[0], p[1]) for p in street["path_local_enu_m"]]


def nearest_on_path(path, point) -> tuple[float, float]:
    """The point on a polyline closest to `point` — including inside a segment."""
    best, best_d = path[0], math.inf
    for a, b in zip(path, path[1:]):
        de, dn = b[0] - a[0], b[1] - a[1]
        length2 = de * de + dn * dn
        if length2 < 1e-9:
            cand = a
        else:
            t = ((point[0] - a[0]) * de + (point[1] - a[1]) * dn) / length2
            t = max(0.0, min(1.0, t))
            cand = (a[0] + t * de, a[1] + t * dn)
        d = math.dist(cand, point)
        if d < best_d:
            best, best_d = cand, d
    return best


def block_centre(bounded_by: dict, streets: dict) -> tuple[float, float]:
    """Where the block WOULD sit: the middle of the box its four centrelines describe.

    The block has no geometry — that is the whole reason it was refused — so its centre is
    taken from the bounding streets themselves. The east-west pair give the northing and
    the north-south pair the easting, each averaged over its own committed path.
    """
    def mean_n(sid):
        pts = centreline(streets[sid])
        return sum(p[1] for p in pts) / len(pts)

    def mean_e(sid):
        pts = centreline(streets[sid])
        return sum(p[0] for p in pts) / len(pts)

    north_n, south_n = mean_n(bounded_by["north"]), mean_n(bounded_by["south"])
    west_e, east_e = mean_e(bounded_by["west"]), mean_e(bounded_by["east"])
    return ((west_e + east_e) / 2.0, (north_n + south_n) / 2.0)


def wet_run(field, start, end) -> tuple[int, int]:
    """Samples along `start`→`end` that fall on water or off the modelled ground."""
    span = math.dist(start, end)
    steps = max(2, int(span / STRIDE_M))
    wet = 0
    for i in range(steps + 1):
        t = i / steps
        e = start[0] + (end[0] - start[0]) * t
        n = start[1] + (end[1] - start[1]) * t
        if not field.covers(e, n) or field.height(e, n) < 0.0:
            wet += 1
    return wet, steps + 1


def classify(unit: dict, streets: dict, field) -> dict:
    bounded = unit["bounded_by"]
    centre = block_centre(bounded, streets)
    # The refusal names a street; measure from that street's own committed centreline.
    named = bounded["north"]
    path = centreline(streets[named])
    foot = nearest_on_path(path, centre)
    gap = math.dist(foot, centre)
    wet, total = wet_run(field, foot, centre)
    return {
        "id": unit["id"], "street": named, "centre": centre, "from": foot,
        "gap_m": gap, "wet": wet, "samples": total,
        "class": "never_platted" if wet else "awaiting_control",
    }


def main() -> int:
    check = "--check" in sys.argv
    try:
        from heightfield import Heightfield
        field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    except Exception as exc:  # pragma: no cover
        die(f"the committed heightfield did not load: {exc}")
    if field is None:
        die("the committed heightfield is missing")

    streets = load_streets()
    programme = json.loads(PROGRAMME.read_text())
    units = [u for u in programme["schedule"]
             if u.get("kind", "").startswith("platted_block_awaiting_street_control")
             or u.get("kind") == "platted_block_never_platted"]
    if not units:
        die("the programme names no street-control refusals to measure")

    print(f"{'block':<28}{'street':<14}{'gap m':>8}{'wet':>7}{'of':>5}  class")
    rows = []
    for unit in units:
        row = classify(unit, streets, field)
        rows.append(row)
        print(f"{row['id']:<28}{row['street']:<14}{row['gap_m']:8.0f}"
              f"{row['wet']:7d}{row['samples']:5d}  {row['class']}")

    print()
    for row in rows:
        if row["class"] == "never_platted":
            print(f"  {row['id']}: {row['street']} is {row['gap_m']:.0f} m away and "
                  f"{row['wet']} of {row['samples']} samples between them are water. "
                  "The two are on opposite banks; no trace joins them.")
        else:
            print(f"  {row['id']}: {row['street']} is {row['gap_m']:.0f} m away over dry "
                  "ground. This block is really waiting on control.")

    if not check:
        return 0

    failed = 0
    expected = {
        "platted_block_awaiting_street_control": "awaiting_control",
        "platted_block_never_platted": "never_platted",
    }
    by_id = {u["id"]: u for u in units}
    for row in rows:
        want = expected[by_id[row["id"]]["kind"]]
        if row["class"] != want:
            failed += 1
            print(f"\n  FAIL {row['id']}: the programme files it as {want!r} and the "
                  f"ground measures {row['class']!r}. Re-run tools/reconcile_665.py; if "
                  "the class really has moved, the roofs move with it.")
    print("\nBLOCK GATING PASS" if not failed else "\nBLOCK GATING FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
