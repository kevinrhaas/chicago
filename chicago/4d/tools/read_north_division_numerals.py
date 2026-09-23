#!/usr/bin/env python3
"""Re-derive the North Division tier's seven block-numeral crops from committed street lines.

T-1088, split out of T-0858. Wright writes a numeral across the middle of every
block of the Original Town. T-0788 read twenty-two of them by cutting each crop
from that block's OWN committed street lines — an identification made by the
georeference rather than by the reader's eye — and stopped, because the street
grid reached no further. It reaches further now: `data/streets/1835.json` holds
Kinzie Street and the six north-south lines of the North Division (Market,
Franklin, Wells, La Salle, Clark, Dearborn) and Wolcott closing the tier on the
east, all graded `attested`. So the tier between Kinzie Street and the river can
be cut, and it is: seven numerals, 7 6 5 4 3 2 1 running west to east.

WHAT THIS FILE IS. It is the DERIVATION of the crop boxes, not the reading. The
reading — which numeral stands in which block — lives in
`data/traces/thompson_block_numbering.json` § blocks_not_in_the_grid, one entry
per block, each citing the IIIF region it was read on. This tool recomputes those
regions from the committed street lines and fails if they have drifted, so the
citation stays a re-derivable statement about the georeference rather than a
number somebody once typed. It authors no ground: the North Division has no
generated block cell (tools/generate_plat_lots.py emits the three South Division
tiers and nothing else), which is exactly why the readings sit in the
not-in-the-grid section and wait there for a cell.

THE RULE, stated once so a reader can disagree with it:

  east and west   the two flanking north-south centrelines, at their south ends
  north           Kinzie Street's centreline, at whichever flank it runs lower
  south           the southern endpoint of the flanking streets — the point where
                  the platted line stops at the river — taking the northern of the
                  two so the box does not reach across the bank

Block 7 has no committed street on its west: its west edge is the North Branch.
Its box is therefore cut ONE MODULE west of Market Street, the module being the
mean spacing of the six flanking lines (123.36 m). That is a wider box than the
block, and it is cited as such; the numeral falls inside it and the entry records
the tighter region it was actually read on.

AND ITS SOUTH SIDE IS NOT THE RULE ABOVE — corrected by T-1099. With one flank
there is no "northern of the two", so the rule degenerated to Market Street's own
southern endpoint, and Market is precisely the line that does not stop at this
tier: `market_north` runs on to north +46.35 m at the bank in the forks, where
`franklin_north` beside it stops at +151.61 m. The box ran 89 m past block 7 and
swallowed the block below, whose numeral 14 sat inside the crop this file cited
for 7. Block 7's south is therefore the TIER's own south line — Carroll Street
continued east along the bearing of its committed path, from
`tools/read_wolf_point_numerals.py`, taken where it runs furthest north so the
box does not reach over the street. Both numerals stood; only the box was wrong.

    tools/read_north_division_numerals.py            print the derivation
    tools/read_north_division_numerals.py --check    fail if the committed crops
                                                     are not what this re-derives
    tools/read_north_division_numerals.py --self-test  the check fires when broken
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wright_px  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STREETS = ROOT / "data" / "streets" / "1835.json"
TRACE = ROOT / "data" / "traces" / "thompson_block_numbering.json"

# The tier, west to east. `None` on the west flank is the North Branch.
FLANKS = ["market_north", "franklin_north", "wells_north", "lasalle_north",
          "clark_north", "dearborn_north", "wolcott"]
TIER = [(None, "market_north", 7), ("market_north", "franklin_north", 6),
        ("franklin_north", "wells_north", 5), ("wells_north", "lasalle_north", 4),
        ("lasalle_north", "clark_north", 3), ("clark_north", "dearborn_north", 2),
        ("dearborn_north", "wolcott", 1)]


def _streets():
    return {s["id"]: s for s in json.loads(STREETS.read_text())["streets"]}


def _kinzie_y(streets, x: float) -> float:
    path = streets["kinzie"]["path_local_enu_m"]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if min(x0, x1) <= x <= max(x0, x1):
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return path[-1][1]


def module(streets) -> float:
    xs = [streets[i]["path_local_enu_m"][0][0] for i in FLANKS]
    return statistics.mean(b - a for a, b in zip(xs, xs[1:]))


def boxes(streets) -> dict[int, tuple[str, tuple[float, float, float, float]]]:
    out = {}
    mod = module(streets)
    for west, east, number in TIER:
        e_end = streets[east]["path_local_enu_m"][0]
        if west is None:
            # T-1099: one flank, so no "northern of the two" — the tier's own
            # south line stands in for it. Imported late: read_wolf_point_numerals
            # imports this module for the module width.
            import read_wolf_point_numerals as wolf
            x0, x1 = e_end[0] - mod, e_end[0]
            south = max(wolf.carroll_east(streets, x0), wolf.carroll_east(streets, x1))
        else:
            w_end = streets[west]["path_local_enu_m"][0]
            x0, x1, south = w_end[0], e_end[0], max(w_end[1], e_end[1])
        north = min(_kinzie_y(streets, x0), _kinzie_y(streets, x1))
        url = wright_px.iiif_region(x0, south, x1, north)
        out[number] = (url.split("js957744g/")[1].split("/")[0], (x0, south, x1, north))
    return out


def committed() -> dict[int, str]:
    trace = json.loads(TRACE.read_text())
    out = {}
    for r in trace["blocks_not_in_the_grid"]["readings"]:
        if r.get("tier") == "north_division_kinzie_to_the_river":
            out[r["number"]] = r["crop"]["iiif_region"]
    return out


def check(streets=None) -> list[str]:
    streets = streets or _streets()
    derived, held = boxes(streets), committed()
    problems = []
    if sorted(held) != sorted(derived):
        problems.append(f"the trace holds {sorted(held)} for this tier; the rule cuts {sorted(derived)}")
    for number, (region, _box) in sorted(derived.items()):
        if number not in held:
            continue
        if held[number] != region:
            problems.append(f"block {number}: trace cites {held[number]}, the rule cuts {region}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        streets = _streets()
        streets["clark_north"]["path_local_enu_m"][0][0] += 40.0
        if not check(streets):
            print("SELF-TEST FAILED: a street moved 40 m and the crop check stayed silent")
            return 1
        # block 7's south side is Carroll continued east (T-1099), so the tier now
        # depends on a street outside its own flanks and the gate has to say so.
        streets = _streets()
        streets["carroll"]["path_local_enu_m"][-1][1] += 40.0
        if not check(streets):
            print("SELF-TEST FAILED: Carroll moved 40 m and block 7's crop check stayed silent")
            return 1
        print("self-test: moving Clark Street 40 m, or Carroll's east end 40 m under block 7's "
              "south side, breaks the crop check, as both must")
        return 0

    problems = check()
    if args.check:
        for p in problems:
            print(f"  {p}")
        if problems:
            print(f"{len(problems)} North Division numeral crop(s) no longer cut from the committed streets")
            return 1
        print("the seven North Division numeral crops re-cut from the committed street lines")
        return 0

    streets = _streets()
    print(f"module (mean flank spacing): {module(streets):.2f} m")
    for number, (region, (x0, s, x1, n)) in sorted(boxes(streets).items()):
        print(f"  block {number}: x[{x0:8.2f},{x1:8.2f}] y[{s:7.2f},{n:7.2f}]  region {region}")
    print("committed:" if not problems else "DRIFTED:")
    for p in problems:
        print(f"  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
