#!/usr/bin/env python3
"""Re-derive blocks 14 and 15 — the last two of Wright's fifty-eight — and settle
the collision T-1098 left inside block 7's box.

T-1099, piece 2 of 2 of T-1095. Fifty-six of the fifty-eight block numerals were
read by cutting each crop from that block's OWN committed street lines (T-0788,
T-1088, T-1094, T-1098). Two were left, and they were left because the tier they
belong to — Carroll to Fulton — was believed to stop at the North Branch: "no
committed street line reaches it, so no crop can be cut".

WHAT THE SHEET ACTUALLY SHOWS. Both numerals are there, and they are in the wedge
between the North Branch, the Main Branch and Market Street:

  14  the block south of Carroll and north of the bank, between the North Branch
      and Market Street — the one the sheet draws with its south-east corner cut
      off along the bank
  15  the small right triangle east of Market Street, between North Water Street
      and the bank at the river's bend

AND THE COLLISION, which is the reason this ticket existed. The glyph reading 14
stands at raster px 1464, 1697 — local east +24.6, north +83.8 — INSIDE the box
T-1088 cites for block 7 (`1376,1452,178,298`), whose own numeral was read two
hundred pixels north of it. Two block numerals cannot stand in one block. The
answer is the first of the two the ticket offered: **that column is two blocks,
and T-1088's box is too tall.** Both readings stand; the box spans them.

WHY THE BOX RAN LONG, stated so the fault is a rule and not a typo. T-1088's
south rule is "the southern endpoint of the flanking platted lines, where they
stop at the river — taking the NORTHERN of the two so the box does not reach
across the bank". Block 7 is the one block in that tier with a single flank: its
west side is the North Branch, not a street. With one endpoint there is no
northern of the two, so the rule degenerated to that one endpoint — and Market
Street is exactly the line that does NOT stop at the tier, because it runs on
south to the bank at the forks (`market_north` ends at north +46.35 m, where its
neighbour `franklin_north` ends at +151.61 m, a whole tier higher). The box
therefore reached 89 m past its own block and swallowed the next one.

THE FOURTH SIDE, AND THE ONLY THING HERE THAT IS NOT COMMITTED GROUND. Carroll
Street is committed — `data/streets/1835.json`, east end at (-104.96, +136.47) —
and it stops at the North Branch's west bank. It is CONTINUED EAST along the
bearing of its own committed path to give block 7 its south side and block 14 its
north side, the same continuation T-1094 and T-1098 make along a clipped line's
own bearing. The continuation runs 68 to 192 m past the committed end for block
14, and 192 to 315 m for block 15.

WHAT CORROBORATES IT. Wright draws a street between the two blocks; its block
faces are read off the sheet at north +155.7 (block 7's south face) and +130.5
(block 14's north face) at local east +40, and at +153.0 (block 6's south face)
and +120 (block 15's north face) east of Market. Carroll continued lands at
+135.5 and +134.5 — inside the drawn street at both longitudes, and on the same
side of its centre at both. That is stated in the memo and is not gated here,
because a block face read off a raster by eye is not something a gate can re-cut.
What IS gated is every other side, the two read windows lying inside their boxes,
and the boustrophedon.

AND THE BOUSTROPHEDON IS THE REAL CHECK. `tools/read_west_division_numerals.py`
asserts that each tier band, read west to east, is monotonic and reverses the
band above it, and it asserts it across the blocks other tickets read. The
Carroll–Fulton band runs 11 12 13 rising eastward; 14 and 15 are added to that
band's tail there, so the two numerals read here have to continue a run three
other blocks already fix, with the band above (10 … 1) falling and the band below
(25 24 23 22) falling. A numeral misread, or a box cut onto the wrong block,
breaks it. That is the fifty-eighth block and the run closes on it.

    tools/read_wolf_point_numerals.py            print the derivation
    tools/read_wolf_point_numerals.py --check    fail if the committed crops are
                                                 not what this re-derives
    tools/read_wolf_point_numerals.py --self-test  the check fires when broken
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_north_division_numerals as north  # noqa: E402
import wright_px  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / "data" / "traces" / "thompson_block_numbering.json"
TIER = "carroll_to_the_bank_east_of_the_north_branch"

# (number, how many modules east of Market Street the box's west side sits).
# Block 14 is flanked west by the North Branch and east by Market Street; block
# 15 is flanked west by Market Street and east by the river's bend. Neither
# river side is a street, so each takes Market stepped ONE module — block 7's
# own rule in T-1088, and blocks 22, 51 and 52's in T-1098 and T-1094.
BLOCKS = [(14, -1), (15, 0)]


def carroll_east(streets, x: float) -> float:
    """Carroll Street's northing at a given east, continued past its committed
    east end along the bearing of its own committed path."""
    path = streets["carroll"]["path_local_enu_m"]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if min(x0, x1) <= x <= max(x0, x1):
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    (x0, y0), (x1, y1) = path[-2], path[-1]
    return y1 + (y1 - y0) * (x - x1) / (x1 - x0)


def boxes(streets) -> dict[int, tuple[str, tuple[float, float, float, float]]]:
    out = {}
    mod = north.module(streets)
    market_x, market_south = streets["market_north"]["path_local_enu_m"][0]
    for number, step in BLOCKS:
        x0, x1 = market_x + step * mod, market_x + (step + 1) * mod
        # the south side is where Market Street's platted line stops at the
        # river; the north side is Carroll continued, taken where it runs
        # furthest south so the box does not reach over the street into block 7.
        south, north_y = market_south, min(carroll_east(streets, x0), carroll_east(streets, x1))
        url = wright_px.iiif_region(x0, south, x1, north_y)
        out[number] = (url.split("js957744g/")[1].split("/")[0], (x0, south, x1, north_y))
    return out


def committed() -> dict[int, dict]:
    trace = json.loads(TRACE.read_text())
    return {r["number"]: r for r in trace["blocks_not_in_the_grid"]["readings"]
            if r.get("tier") == TIER}


def overhang_px(inner: str, outer: str) -> int:
    """How far the read window sticks out of the box it is cited under, in pixels."""
    ix, iy, iw, ih = (int(v) for v in inner.split(","))
    ox, oy, ow, oh = (int(v) for v in outer.split(","))
    return max(0, ox - ix, oy - iy, (ix + iw) - (ox + ow), (iy + ih) - (oy + oh))


def check(streets=None) -> list[str]:
    streets = streets or north._streets()
    derived, held = boxes(streets), committed()
    problems = []
    if sorted(held) != sorted(derived):
        problems.append(f"the trace holds {sorted(held)} for this tier; the rule cuts {sorted(derived)}")
    for number, (region, _box) in sorted(derived.items()):
        if number not in held:
            continue
        crop = held[number]["crop"]
        if crop["iiif_region"] != region:
            problems.append(f"block {number}: trace cites {crop['iiif_region']}, the rule cuts {region}")
            continue
        over = overhang_px(crop["read_at"], region)
        if over:
            problems.append(f"block {number}: the read window stands {over} px outside its own box")
    # THE FAULT THIS FILE FIXES, asserted directly: neither block's numeral may
    # lie inside the other's crop. The two boxes abut on Carroll and round to a
    # two-pixel seam, which is a rounding artefact and not a second numeral; what
    # cannot happen again is one crop citing both readings.
    seven = {r["number"]: r for r in json.loads(TRACE.read_text())["blocks_not_in_the_grid"]["readings"]
             if r.get("tier") == "north_division_kinzie_to_the_river"}.get(7)
    if seven and 14 in held and 14 in derived:
        pairs = [("7", seven["crop"]["read_at"], "14", derived[14][0]),
                 ("14", held[14]["crop"]["read_at"], "7", seven["crop"]["iiif_region"])]
        for a, window, b, region in pairs:
            if not overhang_px(window, region):
                problems.append(f"block {a}'s numeral lies wholly inside the crop cited for block "
                                f"{b}; two block numerals in one crop is the fault T-1099 settled")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        streets = north._streets()
        streets["carroll"]["path_local_enu_m"][-1][1] += 40.0
        if not check(streets):
            print("SELF-TEST FAILED: Carroll's east end moved 40 m and the crop check stayed silent")
            return 1
        print("self-test: moving Carroll's east end 40 m breaks the crop check, as it must")
        return 0

    problems = check()
    if args.check:
        for p in problems:
            print(f"  {p}")
        if problems:
            print(f"{len(problems)} Wolf Point numeral crop(s) no longer cut from the committed lines")
            return 1
        print("blocks 14 and 15 re-cut from Market Street and Carroll continued east")
        return 0

    streets = north._streets()
    print(f"module (mean flank spacing): {north.module(streets):.2f} m")
    print(f"Carroll's committed east end: {streets['carroll']['path_local_enu_m'][-1]}")
    for number, (region, (x0, s, x1, n)) in sorted(boxes(streets).items()):
        print(f"  block {number}: x[{x0:8.2f},{x1:8.2f}] y[{s:7.2f},{n:7.2f}]  region {region}")
    print("committed:" if not problems else "DRIFTED:")
    for p in problems:
        print(f"  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
