#!/usr/bin/env python3
"""Cut the School Section's second tier, Monroe to Adams, into the lots the 1833 sale witnesses.

T-2252, piece 1 of 3 of T-2247, on the owner's ruling of 2026-10-09 on that ticket: "(b)
Cross Monroe: cut the School Section's next row (Monroe to Adams, east of the river) into
lots from the October 1833 sale register, as T-1477 did for Madison to Monroe, and build
all six there." The six are the South's gated roofs — D2, D2, D4, D4, D5 and an H3 — that
no named South block and no lot of the Madison-Monroe tier has room left for. This piece
is the cut and only the cut; joining the tier to the platted grid and the roof schedule is
T-2253, and raising the six is T-2254.

THE CUT IS T-1477'S, NOT A SECOND ONE. Every line of arithmetic is
`tools/cut_school_section_tier.py`'s `derive()`, called on the committed grid's row 1
instead of row 0: the same register (`data/research/land_sales/entries.json`, the 337 SC
rows of section 16), the same refusal of a block whose witnessed lot numbers are not a
contiguous run from 1, the same two rows either side of an 18 ft mid-block alley, and the
same conjectural numbering carried from the Original Town's block 18. A second copy of
that arithmetic would be a second place for the two tiers to disagree, so there is none.
The grades are therefore the first tier's: boundary `inferred` (the committed grid's),
lot COUNT `documented` (the register's), lot LINES `inferred` (the town's module) and lot
NUMBERS `conjectural`.

WHAT THE REGISTER SAYS ABOUT THIS ROW. It names all thirteen blocks. Eleven sold lots 1
through 8 and two sold lots 1 through 4 and never a fifth — and the two four-lot blocks
are again the pair at the South Branch end, 71 and 79, directly south of the first tier's
72 and 80. Nothing on this row is reserved: the sheet letters *Reserved* on the section's
two northern corners only, and the register sells lots in both corner blocks of this row.

EAST OF THE RIVER, which is where the ruling builds, is read the way T-2144 read it for
the first tier (`generate_plat_lots.school_section_tier_joins`, imported, not restated):
a block of the South Division's side of the forks (west face east of local easting 0),
cut into lots, with no lattice sample below datum and none off the modelled field. That
is six blocks and forty-eight lots — 82, 93, 96, 117, 120 and 141 — every one of them
eight lots, and their westernmost face is Market, the street that runs the South Branch's
east bank in the town above. The river block 79 is the tier's only wet one.

WHAT THIS DOES NOT SAY. It seats no building, deals no roof, adds no cell to the platted
grid and moves no line of the block grid. The School Section in 1835 was sold ground and
mostly empty ground; this file says where the lots of its second row were, and which six
blocks the owner's ruling may build on. Whether anything stood there is T-2254's
question, and it will be a liberty when it is answered.

    tools/cut_school_section_second_tier.py              regenerate the committed file
    tools/cut_school_section_second_tier.py --check      fail if the committed file is
                                                         not what this module re-derives
    tools/cut_school_section_second_tier.py --self-test  the assertions the cut satisfies
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_PATH = DATA / "traces" / "vectors" / "school_section_second_tier_lots.json"

sys.path.insert(0, str(ROOT / "tools"))
import cut_school_section_tier as first  # noqa: E402
from generate_plat_lots import school_section_tier_joins  # noqa: E402

# The committed grid's row index for the blocks between Monroe and Adams — the row directly
# south of the first tier's row 0. Named by index, as the first tier is, so a re-read of
# the sheet that moved a numeral cannot leave this stale.
TIER_ROW = 1


def document() -> dict:
    d = first.derive(TIER_ROW)
    blocks = d["blocks"]
    divided = [b for b in blocks if b["lots"]]
    east = [b for b in blocks if school_section_tier_joins(b)]
    for block in east:
        block["east_of_the_river"] = (
            "On the South Division's side of the forks, cut into the register's lots, dry "
            "at every lattice sample and on the modelled field — the test T-2144 put to "
            "the first tier (generate_plat_lots.school_section_tier_joins). One of the "
            "blocks the owner's 2026-10-09 ruling on T-2247 builds on.")
    return {
        "$schema_note": (
            "DERIVED, and re-derived by the gate. Every number in this file is computed by "
            "tools/cut_school_section_second_tier.py, which calls "
            "tools/cut_school_section_tier.py's own derive() on the committed grid's row "
            "1, from committed inputs — the block grid in "
            "data/traces/vectors/school_section_blocks_1834.json, the October 1833 "
            "register in data/research/land_sales/entries.json, and the committed "
            "heightfield. Nothing in it is authored. "
            "tools/cut_school_section_second_tier.py --check fails if the committed file "
            "is not what those inputs re-derive."),
        "id": "school_section_second_tier_lots_1834",
        "plat": "wright_1834_school_section",
        "ticket": "T-2252",
        "parent_ticket": "T-2247",
        "generated_by": "tools/cut_school_section_second_tier.py",
        "cut_by": "tools/cut_school_section_tier.py derive(tier_row=1)",
        "reads": [
            "data/traces/vectors/school_section_blocks_1834.json",
            "data/research/land_sales/entries.json",
            "data/terrain/epochs/e1834_harbor_cut",
        ],
        "what_the_tier_is": (
            "The row of thirteen blocks between MONROE and ADAMS, the second of the School "
            "Section's twelve, directly south of the Madison-Monroe tier T-1477 cut. It is "
            "cut on the owner's ruling of 2026-10-09 on T-2247 — cross Monroe — because "
            "every named South block and every lot of the first tier the ruling of "
            "2026-10-05 opened is at its ceiling, and six of the South's roofs still have "
            "nowhere to stand."),
        "ruling": {
            "ticket": "T-2247",
            "answered": "2026-10-09",
            "answer": "b",
            "text": ("Cross Monroe: cut the School Section's next row (Monroe to Adams, "
                     "east of the river) into lots from the October 1833 sale register, "
                     "as T-1477 did for Madison to Monroe, and build all six there"),
        },
        "where_the_lot_count_comes_from": {
            "source": "data/research/land_sales/entries.json",
            "record": ("the Illinois State Archives' tract register of the October 1833 "
                       "school-section sale, 337 rows of type_of_sale SC in section 16 of "
                       "T39N R14E"),
            "read_as": ("the highest lot number the register prints in each block, after "
                        "refusing any block whose witnessed numbers are not a contiguous "
                        "run from 1 — tools/cut_school_section_tier.py witnessed_count()"),
            "blocks_the_register_cuts_into_eight": [
                b["school_section_block_number"] for b in divided if len(b["lots"]) == 8],
            "blocks_the_register_cuts_into_four": [
                b["school_section_block_number"] for b in divided if len(b["lots"]) == 4],
            "blocks_the_register_never_names": [
                b["school_section_block_number"] for b in blocks if not b["lots"]],
            "the_four_lot_blocks_are_the_river_s_again": (
                "Blocks 71 and 79 are the two of this tier nearest the South Branch, and "
                "the two the register cuts into four rather than eight — directly south of "
                "72 and 80, the first tier's four-lot pair. The committed heightfield "
                "agrees without sharing any arithmetic with the register: block 79 is the "
                "only block of this row with a lattice sample below datum. The file "
                "records the agreement; it does not claim to know the seller's reason."),
        },
        "module": "tools/cut_school_section_tier.py — the first tier's module, unchanged",
        "east_of_the_river": {
            "test": ("generate_plat_lots.school_section_tier_joins — the South Division's "
                     "side of the forks (west face east of local easting 0), cut into "
                     "lots, no sample below datum, none off the modelled field"),
            "blocks": [b["school_section_block_number"] for b in east],
            "lots": sum(len(b["lots"]) for b in east),
            "west_face_of_the_westernmost": (
                min(east, key=lambda b: b["boundary_local_enu_m"][0][0])
                ["bounded_by"]["west"] if east else None),
            "note": ("Six blocks, matching the six roofs the ruling sends here, though "
                     "nothing requires one roof to a block: which lot takes which roof is "
                     "the roof schedule's deal (T-2253), and this file says only where "
                     "the lots are."),
        },
        "blocks": blocks,
        "counts": {
            "blocks": len(blocks),
            "blocks_divided": len(divided),
            "blocks_left_whole": len(blocks) - len(divided),
            "lots": sum(len(b["lots"]) for b in blocks),
            "tier_ground_m2": round(math.fsum(b["area_m2"] for b in blocks), 1),
            "tier_ground_acres": round(
                math.fsum(b["area_m2"] for b in blocks) / first.ACRE_M2, 1),
            "lot_ground_acres": round(
                math.fsum(lot["area_acres"] for b in blocks for lot in b["lots"]), 1),
            "blocks_with_ground_below_datum": [
                b["school_section_block_number"] for b in blocks
                if b["ground"]["below_datum"]],
            "blocks_reaching_off_the_modelled_field": [
                b["school_section_block_number"] for b in blocks
                if b["ground"]["off_the_modelled_field"]],
        },
        "what_this_does_not_say": (
            "NOTHING ABOUT WHO BUILT HERE. This file says where the lots of the School "
            "Section's second row were and which six blocks the 2026-10-09 ruling may "
            "build on. It seats no structure, names no purchaser onto a lot, adds no cell "
            "to the platted grid and re-grades no street. The roofs the ruling sends here "
            "are T-2253's to deal and T-2254's to raise, and any of them standing on this "
            "ground in 1835 will be a liberty recorded when it is raised."),
    }


def rendered() -> str:
    return json.dumps(document(), indent=2, ensure_ascii=False) + "\n"


def write() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(rendered(), encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(ROOT.parent.parent)}")


def check() -> int:
    if not OUT_PATH.exists():
        print(f"MISSING {OUT_PATH}")
        return 1
    if OUT_PATH.read_text(encoding="utf-8") != rendered():
        print(f"STALE {OUT_PATH.name} — the committed file is not what "
              "tools/cut_school_section_second_tier.py re-derives from the committed block "
              "grid and the committed register. Regenerate it in the same commit.")
        return 1
    print(f"ok {OUT_PATH.name} re-derives")
    return 0


def self_test(quiet: bool = False) -> int:
    doc = document()
    blocks = {b["school_section_block_number"]: b for b in doc["blocks"]}
    grid = {b["block_number"]: b for b in first.load(first.BLOCKS_PATH)["blocks"]}
    first_tier = {b["school_section_block_number"]: b
                  for b in first.load(first.OUT_PATH)["blocks"]}
    failures = []

    def want(label, condition, detail=""):
        if not condition:
            failures.append(f"{label}{': ' + detail if detail else ''}")
        elif not quiet:
            print(f"  ok  {label}")

    want("the tier is thirteen blocks wide", len(blocks) == 13, f"{len(blocks)} cut")
    want("the tier runs between Monroe and Adams and nothing else",
         all(b["bounded_by"]["north"] == "monroe" and b["bounded_by"]["south"] == "adams"
             for b in blocks.values()))
    want("no block of this tier and the first tier is the same block",
         not set(blocks) & set(first_tier), str(sorted(set(blocks) & set(first_tier))))

    # Directly south of the first tier, face for face: this tier's north face is the
    # first tier's south face, and each block shares its column's east and west lines.
    def column(cells):
        return next(c[0] for c in cells)
    by_column = {column(grid[n]["cells"]): n for n in first_tier}
    for number, block in blocks.items():
        above = first_tier.get(by_column.get(column(grid[number]["cells"])))
        if above is None:
            failures.append(f"block {number} has no first-tier block above it")
            continue
        w0, e0, s0, _ = first.rectangle([tuple(p) for p in above["boundary_local_enu_m"]])
        w1, e1, _, n1 = first.rectangle([tuple(p) for p in block["boundary_local_enu_m"]])
        want(f"block {number} sits under block {above['school_section_block_number']}, "
             "across Monroe and between the same column lines",
             abs(w0 - w1) < 0.01 and abs(e0 - e1) < 0.01 and n1 < s0,
             f"west {w0}/{w1}, east {e0}/{e1}, Monroe {s0}/{n1}")

    # The register: every block named, every block cut into what it witnesses.
    want("the register names every block of this row", all(b["lots"] for b in blocks.values()))
    for number, block in blocks.items():
        witnessed = block["witnessed_by_the_sale"]
        want(f"block {number} is cut into the {witnessed['count']} lots the register "
             "witnesses, numbered 1 to that once each",
             sorted(lot["lot"] for lot in block["lots"])
             == list(range(1, witnessed["count"] + 1)))
    want("eleven blocks are cut into eight lots and two into four",
         sorted(len(b["lots"]) for b in blocks.values()) == [4, 4] + [8] * 11,
         str(sorted(len(b["lots"]) for b in blocks.values())))
    want("nothing on this row is reserved on the sheet",
         not [n for n in blocks if grid[n].get("reserved")])

    # The river's pair, again — and the wet block is one of them, which is what the
    # copied `wet_ground` note says and so what has to stay true for it to be carried.
    four = sorted(n for n, b in blocks.items() if len(b["lots"]) == 4)
    wet = doc["counts"]["blocks_with_ground_below_datum"]
    want("the two four-lot blocks are 71 and 79, under the first tier's four-lot pair",
         four == [71, 79], str(four))
    want("the four-lot blocks sit in the first tier's four-lot columns",
         sorted(column(grid[n]["cells"]) for n in four)
         == sorted(column(grid[n]["cells"]) for n, b in first_tier.items()
                   if len(b["lots"]) == 4))
    want("the one block with wet ground is one of the two four-lot blocks",
         len(wet) == 1 and wet[0] in four, f"wet {wet}, four-lot {four}")

    # Where the ruling builds.
    east = doc["east_of_the_river"]
    want("six blocks stand east of the river, dry and on the modelled field",
         east["blocks"] == [82, 93, 96, 117, 120, 141], str(east["blocks"]))
    want("every block east of the river is cut into eight lots",
         all(len(blocks[n]["lots"]) == 8 for n in east["blocks"]))
    want("the westernmost block east of the river fronts Market on its west",
         east["west_face_of_the_westernmost"] == "market_school_section",
         str(east["west_face_of_the_westernmost"]))
    want("every block east of the river is south of a first-tier block T-2144 joined, "
         "or of the reserved corner",
         all(school_section_tier_joins(first_tier[by_column[column(grid[n]["cells"])]])
             or grid[by_column[column(grid[n]["cells"])]].get("reserved")
             for n in east["blocks"]))

    # Geometry: quoted, rectangular, and fully accounted for by its lots and alley.
    for number, block in blocks.items():
        ring = block["boundary_local_enu_m"]
        worst = max(abs(a - b) for p, q in zip(ring, grid[number]["boundary_local_enu_m"])
                    for a, b in zip(p, q))
        want(f"block {number}'s boundary is the committed grid's own, vertex for vertex",
             worst == 0.0 and len(ring) == 4, f"worst vertex moves {worst} m")
        covered = sum(first.polygon_area(lot["polygon"]) for lot in block["lots"])
        covered += first.polygon_area(block["alley_local_enu_m"])
        want(f"block {number}'s lots and alley account for its ground",
             abs(covered - block["area_m2"]) / block["area_m2"] < 0.005,
             f"{covered:.0f} m2 of {block['area_m2']:.0f}")

    smallest = min(lot["area_acres"] for b in blocks.values() for lot in b["lots"])
    largest = max(lot["area_acres"] for b in blocks.values() for lot in b["lots"])
    want("every lot on the tier is between a third and three quarters of an acre",
         0.30 < smallest and largest < 0.75, f"{smallest} to {largest} acres")

    if failures:
        print("FAIL")
        for line in failures:
            print(f"  FAIL {line}")
        return 1
    if not quiet:
        print("all assertions hold")
    return 0


def report() -> None:
    doc = document()
    print(__doc__.strip().split("\n\n")[0])
    print()
    for b in doc["blocks"]:
        print(f"{b['school_section_block_number']:>4} "
              f"{b['bounded_by']['west'][:26]:>26} {b['frontage_ft']:>7.1f}ft "
              f"{b['depth_ft']:>6.1f}ft {b['area_acres']:>6.2f}  {len(b['lots'])} lots"
              + ("  east of the river" if "east_of_the_river" in b else ""))
    counts = doc["counts"]
    print()
    print(f"{counts['blocks']} blocks, {counts['lots']} lots, "
          f"{counts['tier_ground_acres']:.1f} acres; east of the river: "
          f"{doc['east_of_the_river']['blocks']}, {doc['east_of_the_river']['lots']} lots.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--gate", action="store_true", help="--self-test, quietly")
    args = ap.parse_args()
    if args.check:
        return check()
    if args.gate:
        return self_test(quiet=True)
    if args.self_test:
        return self_test()
    report()
    write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
