#!/usr/bin/env python3
"""Re-derive the Washington-Madison tier's seven block-numeral crops from committed street lines.

T-1094, split out of T-1089, itself split out of T-0858. Wright writes a numeral
across the middle of every block of the Original Town. T-0788 read twenty-two of
them by cutting each crop from that block's OWN committed street lines — an
identification made by the georeference rather than by the reader's eye — and
T-1088 read the North Division's seven the same way once its streets landed.
Fifty-eight blocks less twenty-nine leaves the Original Town's southernmost tier,
between Washington Street and Madison Street, and this file cuts it.

WHAT MAKES IT CUTTABLE NOW, AND WHAT IS STILL WEAKER THAN THE NORTH DIVISION'S.
`data/streets/1835.json` holds Washington Street across the whole tier and, since
T-0877, Madison Street closing it on the south. The seven north-south lines that
flank the blocks — Market, Franklin, Wells, La Salle, Clark, Dearborn, State —
are committed and `attested`, but every one of them STOPS AT y = -400 m, ten
metres south of Washington and a hundred and thirty-four short of Madison. So
three of each box's four sides are a committed line and the fourth pair is those
same committed lines CONTINUED SOUTH ALONG THEIR OWN BEARING to the tier. That
continuation is a computation from committed endpoints, not a reading and not a
new street: nothing is written into data/streets/1835.json by this file, because
a line this project has no control for should not be published as one. It is
stated here so a reader can disagree with it, and the readings it frames are
graded `inferred` like every other numeral in the file.

THE RULE, stated once:

  east and west   the two flanking north-south centrelines, each continued south
                  along the bearing of its own committed two-point path until it
                  crosses Madison Street
  north           Washington Street's centreline, taken at whichever flank it
                  runs further south, so the box never reaches over the street
  south           Madison Street's centreline

Block 52 has no committed street on its west: its west edge is the South Branch.
Its box is therefore cut ONE MODULE west of Market Street, the module being the
mean spacing of the seven flanking lines at Madison (123.36 m — the same module
the North Division tier measured, to the centimetre). That is a wider box than
the block, and the numeral sits in its eastern sixth; the entry cites the tighter
region it was actually read on.

WHAT THIS FILE IS. It is the DERIVATION of the crop boxes, not the reading. The
reading — which numeral stands in which block — lives in
`data/traces/thompson_block_numbering.json` § blocks_not_in_the_grid, one entry
per block, each citing the IIIF region it was read on. This tool recomputes those
regions from the committed street lines, checks that each `read_at` window still
lies wholly inside the box it is cited under, and fails if either has drifted. It
authors no ground: `tools/generate_plat_lots.py` emits the three South Division
tiers between South Water and Washington and nothing south of Washington, so
there is no cell for these numbers to be stamped onto, and they wait in
`blocks_not_in_the_grid` with the North Division's seven.

    tools/read_washington_madison_numerals.py            print the derivation
    tools/read_washington_madison_numerals.py --check    fail if the committed crops
                                                         are not what this re-derives
    tools/read_washington_madison_numerals.py --self-test  the check fires when broken
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

TIER = "washington_madison_original_town"

# The tier, west to east. `None` on the west flank is the South Branch.
FLANKS = ["market", "franklin", "wells", "lasalle", "clark", "dearborn", "state"]
BLOCKS = [(None, "market", 52), ("market", "franklin", 53), ("franklin", "wells", 54),
          ("wells", "lasalle", 55), ("lasalle", "clark", 56), ("clark", "dearborn", 57),
          ("dearborn", "state", 58)]


def _streets():
    return {s["id"]: s for s in json.loads(STREETS.read_text())["streets"]}


def _y_at(street, x: float) -> float:
    """An east-west street's centreline y where a north-south line crosses it."""
    path = street["path_local_enu_m"]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if min(x0, x1) <= x <= max(x0, x1):
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return path[-1][1]


def _x_at(street, y: float) -> float:
    """A north-south street's centreline x at a given northing, CONTINUED along its
    own bearing past the committed end — see the module docstring."""
    (x0, y0), (x1, y1) = street["path_local_enu_m"][0], street["path_local_enu_m"][-1]
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def madison_y(streets) -> float:
    ys = {p[1] for p in streets["madison"]["path_local_enu_m"]}
    if len(ys) != 1:
        raise SystemExit("Madison Street is no longer a level line; this rule assumes one y")
    return ys.pop()


def module(streets) -> float:
    south = madison_y(streets)
    xs = [_x_at(streets[i], south) for i in FLANKS]
    return statistics.mean(b - a for a, b in zip(xs, xs[1:]))


def boxes(streets) -> dict[int, tuple[str, tuple[float, float, float, float]]]:
    out = {}
    mod = module(streets)
    south = madison_y(streets)
    washington = streets["washington"]
    for west, east, number in BLOCKS:
        x1 = _x_at(streets[east], south)
        x0 = x1 - mod if west is None else _x_at(streets[west], south)
        north = min(_y_at(washington, x0), _y_at(washington, x1))
        url = wright_px.iiif_region(x0, south, x1, north)
        out[number] = (url.split("js957744g/")[1].split("/")[0], (x0, south, x1, north))
    return out


def committed() -> dict[int, dict]:
    trace = json.loads(TRACE.read_text())
    return {r["number"]: r for r in trace["blocks_not_in_the_grid"]["readings"]
            if r.get("tier") == TIER}


def overhang_px(inner: str, outer: str) -> int:
    """How far the read window sticks out of the box it is cited under, in pixels.
    Zero means wholly inside; the entries declare anything larger and the gate
    checks the declaration, so nothing sits outside its own box unannounced."""
    ix, iy, iw, ih = (int(v) for v in inner.split(","))
    ox, oy, ow, oh = (int(v) for v in outer.split(","))
    return max(0, ox - ix, oy - iy, (ix + iw) - (ox + ow), (iy + ih) - (oy + oh))


def check(streets=None) -> list[str]:
    streets = streets or _streets()
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
        else:
            out = overhang_px(crop["read_at"], region)
            if out:
                problems.append(f"block {number}: read_at {crop['read_at']} stands {out} px "
                                f"outside the cited box {region}, and a read window may not")
            declared = crop.get("read_at_overhang_px")
            if declared is not None:
                stated = overhang_px(crop["read_at_overhanging"], region)
                if stated != declared:
                    problems.append(f"block {number}: the entry declares a {declared} px overhang "
                                    f"on {crop['read_at_overhanging']}; it measures {stated} px")
    numbers = [n for _w, _e, n in BLOCKS]
    if numbers != sorted(numbers):
        problems.append("this tier is read as rising eastward; the block list no longer does")
    return problems


def write() -> int:
    """Re-cut the cited boxes from the committed street lines, IN PLACE.

    The crop citation is a derivation, not a reading: the box is four committed lines
    and the rule above, so a street that moves re-cuts it. Until T-1092 there was only a
    gate and no writer, and the run that moved Madison Street — the School Section grid
    re-seated onto the eleven-point registration T-1091 adopted — had nothing to
    regenerate the citation with. The READING is untouched: `read_at` is the window the
    numeral was actually read on and this never writes it. Only the box, its URL, and
    the declared overhang of a window that sticks out of the box are re-derived, and the
    replacement is made on the region STRING so the diff is the lines that moved rather
    than a re-serialisation of a hand-tended file."""
    text = TRACE.read_text()
    derived = boxes(_streets())
    moved = 0
    for r in committed().values():
        region = derived.get(r["number"], (None,))[0]
        crop = r["crop"]
        if region is None or crop["iiif_region"] == region:
            continue
        if overhang_px(crop["read_at"], region) and crop.get("read_at_overhang_px") is None:
            raise SystemExit(
                f"block {r['number']}: the re-cut box {region} no longer holds the read "
                f"window {crop['read_at']}, and this tool will not widen a box to fit a "
                f"reading. Re-read the numeral, or declare the overhang.")
        if text.count(crop["iiif_region"]) != 2:
            raise SystemExit(f"block {r['number']}: {crop['iiif_region']} is not the "
                             f"region string of exactly one entry")
        text = text.replace(crop["iiif_region"], region)
        if crop.get("read_at_overhang_px") is not None:
            was = crop["read_at_overhang_px"]
            now = overhang_px(crop["read_at_overhanging"], region)
            if now != was:
                text = text.replace(f'"read_at_overhang_px": {was},',
                                    f'"read_at_overhang_px": {now},')
        moved += 1
    TRACE.write_text(text)
    print(f"re-cut {moved} of {len(committed())} Washington-Madison numeral crop(s) from "
          f"the committed street lines")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true",
                    help="re-cut the cited boxes from the committed streets, in place")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.write:
        return write()

    if args.self_test:
        failures = []
        streets = _streets()
        streets["clark"]["path_local_enu_m"][0][0] += 40.0
        if not check(streets):
            failures.append("a street moved 40 m and the crop check stayed silent")
        streets = _streets()
        held = committed()
        if held:
            trace = json.loads(TRACE.read_text())
            first = next(r for r in trace["blocks_not_in_the_grid"]["readings"]
                         if r.get("tier") == TIER)
            x, y, w, h = (int(v) for v in first["crop"]["read_at"].split(","))
            box_x = int(first["crop"]["iiif_region"].split(",")[0])
            expected = max(0, box_x - (x - 500))
            if overhang_px(f"{x - 500},{y},{w},{h}", first["crop"]["iiif_region"]) != expected:
                failures.append("a read window slid 500 px west of its box did not measure the "
                                "overhang that slide produces")
        declared = [r for r in committed().values()
                    if r["crop"].get("read_at_overhang_px") is not None]
        if declared:
            r = json.loads(json.dumps(declared[0]))
            r["crop"]["read_at_overhang_px"] += 1
            region = boxes(_streets())[r["number"]][0]
            stated = overhang_px(r["crop"]["read_at_overhanging"], region)
            if stated == r["crop"]["read_at_overhang_px"]:
                failures.append("an overhang declared one pixel wrong still matched its own window")
        for f in failures:
            print(f"SELF-TEST FAILED: {f}")
        if failures:
            return 1
        print("self-test: moving Clark Street 40 m breaks the crop check, and a read window slid "
              "out of its box measures the overhang that slide produces, as they must")
        return 0

    problems = check()
    if args.check:
        for p in problems:
            print(f"  {p}")
        if problems:
            print(f"{len(problems)} Washington-Madison numeral crop(s) no longer cut from the committed streets")
            return 1
        print("the seven Washington-Madison numeral crops re-cut from the committed street lines")
        return 0

    streets = _streets()
    print(f"module (mean flank spacing at Madison): {module(streets):.2f} m")
    for number, (region, (x0, s, x1, n)) in sorted(boxes(streets).items()):
        print(f"  block {number}: x[{x0:8.2f},{x1:8.2f}] y[{s:7.2f},{n:7.2f}]  region {region}")
    print("committed:" if not problems else "DRIFTED:")
    for p in problems:
        print(f"  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
