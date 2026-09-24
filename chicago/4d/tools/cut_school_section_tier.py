#!/usr/bin/env python3
"""Cut the School Section's northernmost tier into the lots the 1833 sale witnesses.

T-1477, piece 1 of 2 of T-1456, itself piece 3 of 3 of T-1438. The tier is the thirteen
blocks between MADISON and MONROE — the row of Section 16 that faces the Town of Chicago
across Madison Street, which is the town's own south line. T-0797 committed the block
grid (`data/traces/vectors/school_section_blocks_1834.json`, 142 blocks read off Wright's
1834 sheet and anchored on the PLSS section). It stopped at blocks. This module divides
the one tier a 1835 scene can see into LOTS, and every figure it uses comes from a
committed file.

WHERE THE LOT COUNT COMES FROM, AND IT IS NOT A MODULE. The state sold the school section
lot by lot in October 1833, and this project already holds the register of that sale:
`data/research/land_sales/entries.json`, 337 rows of `type_of_sale` SC in section 16 of
T39N R14E. Those rows print the plat's own language — `LOT3BL71`, `BL106` — so the
register SAYS how many lots each block was cut into, block by block, in a record made by
the seller at the moment of sale. Nine blocks of this tier sold lots 1 through 8; two
sold lots 1 through 4 and never a fifth; the two the sheet letters *Reserved* sold
nothing at all and are left whole here. Nothing is typed into this file: the counts are
read out of the register at run time, and a block whose witnessed lot numbers are not a
contiguous run from 1 is refused rather than filled in.

THE FOUR-LOT BLOCKS ARE THE RIVER'S. Blocks 72 and 80 are the two of the tier nearest the
SOUTH BRANCH, and they are the two the register cuts into four. That is not this module's
claim about why — it is the arrangement two independent records agree on: the sale's own
rows, and the committed heightfield, which puts 187 of block 80's 396 lattice samples
BELOW DATUM and finds no other block on the tier with a single wet sample. A bigger
parcel on the water and a town lot inland is what the sale sold, and the sale is the one
that says so.

WHAT IS MEASURED, WHAT IS READ AND WHAT IS ADOPTED — the three grades this file carries.

* A BLOCK'S BOUNDARY is the committed one, quoted from the block grid unchanged. This
  module cuts no ground, moves no line and re-reads no raster. The tier is drawn LEVEL
  because the committed grid draws it level, and `school_section_tier_skew_1834.json`
  is why: it re-measured all thirteen east-west rules keeping the bands, and found the
  section's own PLSS boundaries — lines that run true east-west on the ground by
  definition — tilting with the interior ones. The tilt belongs to the registered frame,
  not to Wright's survey. `inferred`, the grade the block grid already carries.
* A LOT COUNT is `documented`. The October 1833 register is a source record, and what it
  witnesses is exactly a count: eight lots in this block, four in that one.
* THE DIVISION — two rows of lots either side of a mid-block alley, fronting Madison on
  the north and Monroe on the south — is `inferred`. It is the module this project cuts
  the Original Town on (`tools/generate_plat_lots.py`, an 18 ft alley centred in the
  block), applied here because it is the town's own practice and the only one this
  project holds. Wright rules the section into blocks and letters their numbers; he does
  not rule lot lines inside them, so no reading of the sheet can settle this.
* A LOT NUMBER is `conjectural`, and that is a grade LOWER than the North Division
  tier's. There, the sheet letters 4 on a known lot in every block read. Here nothing
  places a School Section lot number on the ground at all: the register prints numbers
  and no positions. The run adopted is the Original Town's one read block — block 18,
  north row 4 3 2 and south row 5 6 7 (`docs/RESEARCH/clark_reach_bulge_1834.md` § 8) —
  so the north row runs 4-3-2-1 west to east and the south row 5-6-7-8 west to east. It
  is a convention carried from another plat onto this one, and it says so on every lot.

WHAT THIS DOES NOT SAY. It does not seat a building, does not re-grade a street, does not
touch the block grid, and does not claim the tier was built on: the school section in
1835 was sold ground, mostly empty, and where anything stood on it is a placement
ticket's question. It also makes no use of the register's ACRES column, and § `acreage`
below is the measurement that refused it.

    tools/cut_school_section_tier.py              regenerate the committed file
    tools/cut_school_section_tier.py --check      fail if the committed file is not what
                                                  this module and its committed inputs
                                                  re-derive
    tools/cut_school_section_tier.py --self-test  the assertions this cut has to satisfy
    tools/cut_school_section_tier.py --report     print the tier as it cuts
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_PATH = DATA / "traces" / "vectors" / "school_section_tier_lots.json"
BLOCKS_PATH = DATA / "traces" / "vectors" / "school_section_blocks_1834.json"
SALE_PATH = DATA / "research" / "land_sales" / "entries.json"
SKEW_PATH = DATA / "traces" / "vectors" / "school_section_tier_skew_1834.json"

sys.path.insert(0, str(ROOT / "tools"))
# The ground reading is the South Division generator's, not a second one written here: a
# block on this tier has to report its ground the same way a block on that grid does, or
# the placement tickets that read both get two different answers to one question.
import generate_plat_lots as south_division  # noqa: E402

FT_M = south_division.FT_M
ALLEY_FT = south_division.ALLEY_FT
ACRE_M2 = 4046.8564224
# The tier is the row of blocks between Madison and Monroe: every block of the committed
# grid with a cell in row 0. Named by the grid's own row index rather than by a list of
# block numbers, so a re-read of the sheet that moved a numeral cannot leave this stale.
TIER_ROW = 0
# The section's rows of the register. `SC` and section 16 of T39N R14E are the same rows
# — tools/school_section_sale.py asserts that — so the code is what selects them.
SALE_CODE = "SC"
LOT_ROW = re.compile(r"^LOT(\d+)BL(\d+)(VOID)?$")
BLOCK_ROW = re.compile(r"^BL(\d+)(VOID)?$")


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rounded(points, places: int = 2):
    return [[round(e, places), round(n, places)] for e, n in points]


def polygon_area(ring) -> float:
    total = 0.0
    for (e0, n0), (e1, n1) in zip(ring, ring[1:] + ring[:1]):
        total += e0 * n1 - e1 * n0
    return abs(total) / 2.0


def sale_rows() -> tuple[dict[int, set[int]], dict[int, list[float]]]:
    """{block: the lot numbers the register witnesses} and {block: its whole-block acres}.

    A VOID row is kept. The sale voided and resold lots, and a voided row is still the
    register stating that this block was cut into lots and that this was one of them —
    which is the only thing read here. Who held the lot afterwards is a different
    question and no part of this cut.
    """
    lots: dict[int, set[int]] = {}
    acres: dict[int, list[float]] = {}
    for row in load(SALE_PATH)["entries"]:
        if row.get("type_of_sale") != SALE_CODE:
            continue
        printed = row["aliquot_or_lot_as_read"].replace(" ", "")
        lot = LOT_ROW.match(printed)
        block = BLOCK_ROW.match(printed)
        if lot:
            lots.setdefault(int(lot.group(2)), set()).add(int(lot.group(1)))
        elif block:
            acres.setdefault(int(block.group(1)), []).append(float(row["acres"]))
    return lots, acres


def witnessed_count(number: int, lots: dict[int, set[int]]) -> int | None:
    """How many lots the register witnesses in this block, or None if it witnesses none.

    REFUSES a run with a hole in it. A block the register names lots 1, 2 and 4 in has
    not told us it holds four lots — it has told us three sold and that the numbering
    reaches at least 4 — and filling the hole would be this module inventing the one
    thing it is here to read. No block of this tier is in that position; the refusal is
    here so that a re-read of the register which put one there would stop the build
    rather than be absorbed.
    """
    seen = lots.get(number)
    if not seen:
        return None
    if sorted(seen) != list(range(1, max(seen) + 1)):
        raise SystemExit(
            f"block {number}: the register witnesses lots {sorted(seen)}, which is not a "
            "contiguous run from 1. The lot count is READ and may not be filled in.")
    if max(seen) % 2:
        raise SystemExit(
            f"block {number}: the register witnesses {max(seen)} lots, an odd number, and "
            "the two-row module cannot divide it. This needs a reading, not a rule.")
    return max(seen)


def numbering(count: int) -> dict[str, list[int]]:
    """The Original Town's read run, carried onto a block of `count` lots.

    Block 18 of the Original Town is the one block in this project whose lot numerals are
    read: north row 4 3 2, south row 5 6 7. So the north row descends west to east to 1
    at its east end, and the south row ascends from the next number west to east. On a
    four-lot block that is 2 1 north and 3 4 south.
    """
    per_face = count // 2
    return {"north": list(range(per_face, 0, -1)),
            "south": list(range(per_face + 1, count + 1))}


def heightfield():
    from heightfield import Heightfield  # noqa: PLC0415
    return Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")


def rectangle(ring) -> tuple[float, float, float, float]:
    """(west, east, south, north) of a committed block boundary.

    The committed grid draws every block of this tier as an axis-aligned rectangle —
    asserted below rather than assumed — so the four extremes ARE the four faces and a
    lot cut between them is cut between the committed lines themselves.
    """
    eastings = [e for e, _ in ring]
    northings = [n for _, n in ring]
    return min(eastings), max(eastings), min(northings), max(northings)


def derive() -> dict:
    grid = load(BLOCKS_PATH)
    lots_witnessed, acres = sale_rows()
    field = heightfield()
    alley_m = ALLEY_FT * FT_M

    tier = [b for b in grid["blocks"] if any(c[1] == TIER_ROW for c in b["cells"])]
    tier.sort(key=lambda b: min(c[0] for c in b["cells"]))

    blocks = []
    for block in tier:
        ring = [tuple(p) for p in block["boundary_local_enu_m"]]
        west, east, south, north = rectangle(ring)
        frontage_m, depth_m = east - west, north - south
        count = witnessed_count(block["block_number"], lots_witnessed)

        entry = {
            "id": f"blk_school_section_tier_{block['block_number']}",
            "school_section_block_number": block["block_number"],
            "grid": "school_section_tier",
            "plat": "wright_1834_school_section",
            "bounded_by": dict(block["bounded_by"]),
            "boundary_local_enu_m": rounded(ring),
            "area_m2": round(polygon_area(ring), 1),
            "area_acres": round(polygon_area(ring) / ACRE_M2, 2),
            "frontage_m": round(frontage_m, 2),
            "frontage_ft": round(frontage_m / FT_M, 1),
            "depth_m": round(depth_m, 2),
            "depth_ft": round(depth_m / FT_M, 1),
            "ground": south_division.ground_reading(rounded(ring), field),
        }

        if count is None:
            entry["lots_per_face"] = 0
            entry["lots"] = []
            entry["subdivision_withheld"] = (
                "The sheet letters *Reserved* across this block and the October 1833 sale "
                "never names it — the two records agree, and neither of them cuts it into "
                "lots. It is carried here whole, because the tier's ground is the tier's "
                "ground whether it sold or not, and a reserved block that vanished from "
                "the file would read as ground nobody has looked at.")
            entry["confidence"] = {
                "boundary": block["geometry_confidence"],
                "lot_lines": "none — the block is not divided",
                "lot_numbers": "none — the block is not divided",
            }
            blocks.append(entry)
            continue

        per_face = count // 2
        numbers = numbering(count)
        row_depth_m = (depth_m - alley_m) / 2.0
        lot_frontage_m = frontage_m / per_face
        lots = []
        for index in range(per_face):
            left = west + index * lot_frontage_m
            right = west + (index + 1) * lot_frontage_m
            for face, top, bottom in (("north", north, north - row_depth_m),
                                      ("south", south + row_depth_m, south)):
                lots.append({
                    "face": face,
                    "fronts": block["bounded_by"][face],
                    "lot": numbers[face][index],
                    "frontage_m": round(right - left, 2),
                    "frontage_ft": round((right - left) / FT_M, 1),
                    "depth_m": round(bottom - top if bottom > top else top - bottom, 2),
                    "depth_ft": round(abs(top - bottom) / FT_M, 1),
                    "area_acres": round(abs(top - bottom) * (right - left) / ACRE_M2, 3),
                    "polygon": rounded([(left, top), (right, top),
                                        (right, bottom), (left, bottom)]),
                })

        entry["lots_per_face"] = per_face
        entry["rows"] = {
            "row_depth_m": round(row_depth_m, 2),
            "row_depth_ft": round(row_depth_m / FT_M, 1),
            "alley_m": round(alley_m, 2),
            "alley_ft": ALLEY_FT,
            "alley_runs": "east-west, mid-block — the Original Town's module, centred",
        }
        entry["alley_local_enu_m"] = rounded([
            (west, north - row_depth_m), (east, north - row_depth_m),
            (east, south + row_depth_m), (west, south + row_depth_m)])
        entry["lots"] = lots
        entry["witnessed_by_the_sale"] = {
            "lots_witnessed": sorted(lots_witnessed[block["block_number"]]),
            "count": count,
            "note": (f"The October 1833 register prints lots 1-{count} in block "
                     f"{block['block_number']} of section 16 and never a lot {count + 1}. "
                     "The count is the register's; where each number stands is not."),
        }
        entry["confidence"] = {
            "boundary": block["geometry_confidence"],
            "lot_count": "documented",
            "lot_lines": "inferred",
            "lot_numbers": "conjectural",
        }
        if entry["ground"]["below_datum"]:
            entry["wet_ground"] = (
                f"{entry['ground']['below_datum']} of {entry['ground']['samples']} "
                "lattice samples inside this block stand below datum on the committed "
                "heightfield — the only block of the thirteen that has one. It is also "
                "one of the two the register cuts into four lots instead of eight. The "
                "block is cut anyway: the sale sold it and the register says into how "
                "many pieces. What can stand on the wet part is a placement question and "
                "this record is where it will be asked.")
        blocks.append(entry)

    return {"grid": grid, "blocks": blocks, "acres": acres,
            "lots_witnessed": lots_witnessed, "alley_m": alley_m}


def acreage() -> dict:
    """The register's ACRES column against this grid's blocks, and why it is not a check.

    118 rows of the sale buy a whole block and print an acreage, which looks like a free
    independent measurement of every block in the section. It is not one. Against the 74
    blocks that both carry an acreage and are drawn here, the register runs 20 % LARGE at
    the median and scatters from 0.72x to 3.26x — nine of the seventy-four inside 5 %.
    A column with that spread cannot tell a good block from a bad one, so this module
    does not use it, does not assert on it, and prints the measurement here so that the
    next person does not have to re-take it to find the same thing out.
    """
    d = derive()
    ratios = []
    for block in d["grid"]["blocks"]:
        rows = d["acres"].get(block["block_number"]) or []
        best = max(rows) if rows else 0.0
        if best > 0:
            ratios.append(round(best / (block["area_m2"] / ACRE_M2), 4))
    ratios.sort()
    middle = ratios[len(ratios) // 2]
    return {
        "blocks_with_a_whole_block_acreage": len(ratios),
        "register_over_derived_median": middle,
        "register_over_derived_min": ratios[0],
        "register_over_derived_max": ratios[-1],
        "within_five_per_cent": sum(1 for r in ratios if abs(r - 1) < 0.05),
        "not_used": (
            "The cut takes the register's COUNT and not its acreage. A column that runs "
            "from three quarters of a block to three and a quarter of one is not "
            "measuring what this grid draws, and reading it as if it were would make the "
            "grid look checked when it is not."),
    }


def document() -> dict:
    d = derive()
    blocks = d["blocks"]
    divided = [b for b in blocks if b["lots"]]
    skew = load(SKEW_PATH)["verdict"]
    return {
        "$schema_note": (
            "DERIVED, and re-derived by the gate. Every number in this file is computed "
            "by tools/cut_school_section_tier.py from committed inputs — the block grid "
            "in data/traces/vectors/school_section_blocks_1834.json, the October 1833 "
            "register in data/research/land_sales/entries.json, and the committed "
            "heightfield — and nothing in it is authored. "
            "tools/cut_school_section_tier.py --check fails if the committed file is not "
            "what those inputs re-derive."),
        "id": "school_section_tier_lots_1834",
        "plat": "wright_1834_school_section",
        "ticket": "T-1477",
        "parent_ticket": "T-1456",
        "generated_by": "tools/cut_school_section_tier.py",
        "reads": [
            "data/traces/vectors/school_section_blocks_1834.json",
            "data/research/land_sales/entries.json",
            "data/traces/vectors/school_section_tier_skew_1834.json",
            "data/terrain/epochs/e1834_harbor_cut",
        ],
        "what_the_tier_is": (
            "The row of thirteen blocks between MADISON and MONROE, the northernmost of "
            "the School Section's twelve. Madison is the Town of Chicago's own south "
            "line, so this tier is the ground a visitor standing at the south edge of the "
            "town looks across. It is the only tier of Section 16 a 1835 scene reaches, "
            "which is why it is cut first and alone."),
        "why_this_file_and_not_thompson_lots": (
            "tools/generate_plat_lots.py cuts a block between two committed STREET "
            "centrelines. The School Section's faces are not streets of that table: they "
            "are the ruled lines of Wright's 1834 grid, seated by "
            "tools/generate_school_section_grid.py and anchored on the PLSS section "
            "rather than on any of this project's corridors. The block boundaries are "
            "already committed by that module and are quoted here unchanged, so this cut "
            "divides ground it does not draw."),
        "where_the_lot_count_comes_from": {
            "source": "data/research/land_sales/entries.json",
            "record": ("the Illinois State Archives' tract register of the October 1833 "
                       "school-section sale, 337 rows of type_of_sale SC in section 16 of "
                       "T39N R14E"),
            "read_as": ("the highest lot number the register prints in each block, after "
                        "refusing any block whose witnessed numbers are not a contiguous "
                        "run from 1"),
            "blocks_the_register_cuts_into_eight": [
                b["school_section_block_number"] for b in divided
                if len(b["lots"]) == 8],
            "blocks_the_register_cuts_into_four": [
                b["school_section_block_number"] for b in divided
                if len(b["lots"]) == 4],
            "blocks_the_register_never_names": [
                b["school_section_block_number"] for b in blocks if not b["lots"]],
            "the_four_lot_blocks_are_the_river_s": (
                "Blocks 72 and 80 are the two of this tier nearest the South Branch, and "
                "they are the two the register cuts into four rather than eight. The "
                "committed heightfield agrees about which ground that is without sharing "
                "any arithmetic with the register: block 80 is the only block of the "
                "thirteen with a lattice sample below datum, and nearly half of it is. "
                "This file records the agreement; it does not claim to know the seller's "
                "reason."),
        },
        "module": {
            "module": "original_town_thompson_1830, carried",
            "division": ("two rows of lots either side of a mid-block east-west alley, "
                         "fronting Madison on the north and Monroe on the south"),
            "alley_ft": ALLEY_FT,
            "lots_per_face": sorted({b["lots_per_face"] for b in divided}),
            "lot_frontage_ft": {
                "min": min(lot["frontage_ft"] for b in divided for lot in b["lots"]),
                "max": max(lot["frontage_ft"] for b in divided for lot in b["lots"]),
            },
            "lot_depth_ft": {
                "min": min(lot["depth_ft"] for b in divided for lot in b["lots"]),
                "max": max(lot["depth_ft"] for b in divided for lot in b["lots"]),
            },
            "why_this_module": (
                "Wright rules the section into blocks and letters their numbers; he does "
                "not rule lot lines inside them. So the division cannot be read off the "
                "sheet, and what is applied instead is the module this project already "
                "cuts the Original Town on — an 18 ft alley centred in the block, lots "
                "fronting the east-west streets. It is the town's own practice, half a "
                "mile away and five years earlier, and it is `inferred` for exactly that "
                "reason."),
            "lot_numbering": (
                "conjectural, and a grade below the North Division tier's. Nothing places "
                "a School Section lot number on the ground: the register prints numbers "
                "and no positions, and the sheet letters none. The run adopted is the one "
                "block of the Original Town whose lot numerals ARE read — block 18, north "
                "row 4 3 2 and south row 5 6 7, docs/RESEARCH/clark_reach_bulge_1834.md "
                "section 8 — so the north row runs 4-3-2-1 west to east and the south row "
                "5-6-7-8 west to east. A convention carried from another plat."),
        },
        "level_because_the_tilt_is_the_frame_s": {
            "ew_median_skew_deg": skew["ew_median_skew_deg"],
            "is_a_rigid_rotation": skew["is_a_rigid_rotation"],
            "why": ("The tier is drawn level because the committed block grid draws it "
                    "level, and T-0959's re-measurement is the reason that stands: it "
                    "found Section 16's own PLSS boundaries — lines that run true "
                    "east-west on the ground by definition — tilting with the interior "
                    "ones. A tilt the cardinal control carries belongs to the registered "
                    "frame and not to Wright's survey, so it is not put into the lots."),
        },
        "acreage": acreage(),
        "blocks": blocks,
        "counts": {
            "blocks": len(blocks),
            "blocks_divided": len(divided),
            "blocks_left_whole": len(blocks) - len(divided),
            "lots": sum(len(b["lots"]) for b in blocks),
            "tier_ground_m2": round(math.fsum(b["area_m2"] for b in blocks), 1),
            "tier_ground_acres": round(math.fsum(b["area_m2"] for b in blocks) / ACRE_M2, 1),
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
            "NOTHING ABOUT WHO BUILT HERE. The school section in 1835 was ground that had "
            "been sold, and mostly empty ground at that; this file says where the lots "
            "were, not that anything stood on them. It seats no structure, names no "
            "purchaser onto a lot — the register's buyers are a research question the "
            "resident rulings own — and re-grades no street. It also says nothing about "
            "the other eleven tiers of the section, which are drawn as blocks and remain "
            "undivided."),
    }


def write() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(document(), indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(ROOT.parent.parent)}")


def check() -> int:
    if not OUT_PATH.exists():
        print(f"MISSING {OUT_PATH}")
        return 1
    fresh = json.dumps(document(), indent=2, ensure_ascii=False) + "\n"
    if OUT_PATH.read_text(encoding="utf-8") != fresh:
        print(f"STALE {OUT_PATH.name} — the committed file is not what "
              "tools/cut_school_section_tier.py re-derives from the committed block grid "
              "and the committed register. Regenerate it in the same commit.")
        return 1
    print(f"ok {OUT_PATH.name} re-derives")
    return 0


def self_test(quiet: bool = False) -> int:
    doc = document()
    blocks = {b["school_section_block_number"]: b for b in doc["blocks"]}
    grid = load(BLOCKS_PATH)
    committed = {b["block_number"]: b for b in grid["blocks"]}
    failures = []

    def want(label, condition, detail=""):
        if not condition:
            failures.append(f"{label}{': ' + detail if detail else ''}")
        elif not quiet:
            print(f"  ok  {label}")

    want("the tier is thirteen blocks wide", len(blocks) == 13, f"{len(blocks)} cut")
    want("the tier runs between Madison and Monroe and nothing else",
         all(b["bounded_by"]["north"] == "madison"
             and b["bounded_by"]["south"] == "monroe" for b in blocks.values()))

    # The two records that decide which blocks are divided, against each other. The
    # sheet letters *Reserved* on two corners; the sale never names them. Neither
    # record was consulted about the other.
    reserved = sorted(n for n, b in committed.items()
                      if b.get("reserved") and n in blocks)
    unsold = sorted(n for n, b in blocks.items() if not b["lots"])
    want("the blocks the sale never names are exactly the blocks the sheet reserves",
         reserved == unsold, f"reserved {reserved}, unsold {unsold}")

    # Every block the register does name is divided, and into the number it witnesses.
    for number, block in blocks.items():
        if not block["lots"]:
            continue
        witnessed = block["witnessed_by_the_sale"]
        want(f"block {number} is cut into the {witnessed['count']} lots the register "
             "witnesses",
             len(block["lots"]) == witnessed["count"],
             f"{len(block['lots'])} cut")
        want(f"block {number}'s lot numbers are 1 to {witnessed['count']}, once each",
             sorted(lot["lot"] for lot in block["lots"])
             == list(range(1, witnessed["count"] + 1)))

    want("nine blocks are cut into eight lots and two into four",
         sorted(len(b["lots"]) for b in blocks.values() if b["lots"])
         == [4, 4] + [8] * 9,
         str(sorted(len(b["lots"]) for b in blocks.values() if b["lots"])))

    # The four-lot blocks and the wet block, the agreement the file reports.
    four = sorted(n for n, b in blocks.items() if len(b["lots"]) == 4)
    wet = doc["counts"]["blocks_with_ground_below_datum"]
    want("the two four-lot blocks are neighbours at the South Branch end of the tier",
         four == [72, 80], str(four))
    want("the one block with wet ground is one of the two four-lot blocks",
         len(wet) == 1 and wet[0] in four, f"wet {wet}, four-lot {four}")

    # Geometry. The committed grid draws this tier as rectangles — if it ever stops,
    # `rectangle()` is silently wrong and this is what says so.
    for number, block in blocks.items():
        ring = block["boundary_local_enu_m"]
        west, east, south, north = rectangle([tuple(p) for p in ring])
        corners = {(round(west, 2), round(south, 2)), (round(west, 2), round(north, 2)),
                   (round(east, 2), round(south, 2)), (round(east, 2), round(north, 2))}
        want(f"block {number}'s committed boundary is an axis-aligned rectangle",
             len(ring) == 4 and {(p[0], p[1]) for p in ring} == corners)

    # The boundary is QUOTED, not recomputed: every vertex is the committed grid's own.
    worst = max(
        abs(a - b)
        for number, block in blocks.items()
        for p, q in zip(block["boundary_local_enu_m"],
                        committed[number]["boundary_local_enu_m"])
        for a, b in zip(p, q))
    want("every block boundary is the committed grid's own, vertex for vertex",
         worst == 0.0, f"worst vertex moves {worst} m")

    # The lots and the alley account for the block, and no lot leaves it.
    for number, block in blocks.items():
        if not block["lots"]:
            continue
        covered = sum(polygon_area(lot["polygon"]) for lot in block["lots"])
        covered += polygon_area(block["alley_local_enu_m"])
        want(f"block {number}'s lots and alley account for its ground",
             abs(covered - block["area_m2"]) / block["area_m2"] < 0.005,
             f"{covered:.0f} m2 of {block['area_m2']:.0f}")
        west, east, south, north = rectangle(
            [tuple(p) for p in block["boundary_local_enu_m"]])
        outside = [lot["lot"] for lot in block["lots"]
                   if min(p[0] for p in lot["polygon"]) < west - 0.01
                   or max(p[0] for p in lot["polygon"]) > east + 0.01
                   or min(p[1] for p in lot["polygon"]) < south - 0.01
                   or max(p[1] for p in lot["polygon"]) > north + 0.01]
        want(f"every lot of block {number} lies inside the block", not outside,
             f"lots {outside} cross a face")

    # The numbering convention, as block 18 letters it: the north row descends to 1 at
    # its east end and the south row ascends from there.
    for number, block in blocks.items():
        if not block["lots"]:
            continue
        north_row = sorted((lot for lot in block["lots"] if lot["face"] == "north"),
                           key=lambda lot: min(p[0] for p in lot["polygon"]))
        want(f"block {number}'s north row descends west to east and ends at lot 1",
             [lot["lot"] for lot in north_row]
             == list(range(len(north_row), 0, -1)))

    # The lots are big. A School Section lot is not a town lot, and the figure is the
    # reason this cut is worth making: eight of them to a block of 2.5 acres.
    smallest = min(lot["area_acres"] for b in blocks.values() for lot in b["lots"])
    largest = max(lot["area_acres"] for b in blocks.values() for lot in b["lots"])
    want("every lot on the tier is between a third and three quarters of an acre",
         0.30 < smallest and largest < 0.75, f"{smallest} to {largest} acres")

    # The register's acreage column, refused rather than ignored.
    want("the register's whole-block acreage does not measure this grid",
         doc["acreage"]["within_five_per_cent"] * 2
         < doc["acreage"]["blocks_with_a_whole_block_acreage"],
         f"{doc['acreage']['within_five_per_cent']} of "
         f"{doc['acreage']['blocks_with_a_whole_block_acreage']} inside 5 %")

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
    print(f"{'blk':>4} {'west':>26} {'east':>26} {'frontage':>9} {'depth':>8} "
          f"{'acres':>6}  lots")
    for b in doc["blocks"]:
        print(f"{b['school_section_block_number']:>4} "
              f"{b['bounded_by']['west'][:26]:>26} {b['bounded_by']['east'][:26]:>26} "
              f"{b['frontage_ft']:>7.1f}ft {b['depth_ft']:>6.1f}ft "
              f"{b['area_acres']:>6.2f}  "
              + (f"{len(b['lots'])} ({b['lots_per_face']} to a face)"
                 if b["lots"] else "reserved, left whole"))
    counts = doc["counts"]
    print()
    print(f"{counts['blocks']} blocks, {counts['lots']} lots, "
          f"{counts['tier_ground_acres']:.1f} acres of platted ground.")


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
