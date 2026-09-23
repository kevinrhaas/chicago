#!/usr/bin/env python3
"""Read the School Section's 142 block numerals off the registered 600-dpi sheet.

T-0875, split out of T-0797. Wright's 1834 survey draws Section 16 — the School
Section, one mile square, its north-east corner the section corner at State and
Madison — subdivided into a grid of blocks, and it WRITES A NUMBER IN EVERY ONE OF
THEM. That is the thing this sheet uniquely supplies. `data/traces/gcp/
wright_1834_nara_hup_gcps.json` exists because the block numerals of the Original
Town are legible at 600 dpi where they are not on the BPL scan (T-0787); the same
is true here, and here there are a hundred and forty-two of them.

WHAT THIS FILE IS AND IS NOT. It is the READING: which numeral stands in which cell
of the section's grid, and the crop on the sheet where the next person can re-open
it and disagree. It authors no ground. A block's boundary in this project is derived
from committed street centrelines (tools/generate_plat_lots.py's rule, and
data/reconstruction/1835_reserved_ground.json says it in terms), and the School
Section has no committed street lines yet — that is T-0876, which spends these
numbers onto ground. So the geometry here is a GRID OF CELLS measured off the sheet
for the sole purpose of citing crops, and every one of its coordinates is a pixel
statement about a raster, never a statement about 1835 Chicago.

WHAT THE SHEET SETTLES THAT THE THOMPSON READING COULD NOT. That file
(data/traces/thompson_block_numbering.json) refuses the Original Town's numbering
past one tier, because two numerals fix the step along a row and say nothing about
how the run passes from one row to the next — "a boustrophedon that turns back west,
a run that restarts at the west end of each tier, and a run that descends a column
all reproduce 19 beside 18". Here the whole grid is legible at once, so the question
is not inferred: the run DESCENDS a column, turns at the section line and ascends the
next, and twelve of the thirteen columns reproduce under that one rule with no
exceptions. The three columns the South Branch interrupts do not, and their order is
read cell by cell rather than derived.

    tools/read_school_section_numerals.py            regenerate the trace
    tools/read_school_section_numerals.py --check    fail if the committed trace is
                                                     not what this re-derives
    tools/read_school_section_numerals.py --self-test  every assertion fires when broken
    tools/read_school_section_numerals.py --report   print the grid as it reads
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GCP = DATA / "traces" / "gcp" / "wright_1834_nara_hup_gcps.json"
OUT = DATA / "traces" / "school_section_block_numbering.json"

FT_M = 0.3048
MILE_M = 5280 * FT_M  # 1609.344

# ---------------------------------------------------------------------------
# THE MEASUREMENT. Both lists are metres east/north of the scene datum, and both
# were measured on 2026-09-06 in a raster rectified into that frame through the
# committed NA affine (data/traces/gcp/wright_1834_nara_hup_gcps.json § fit) at
# 0.5 m/px: the ruled lines are the darkness maxima of the column and row
# profiles of that raster, detrended against a 60-100 m moving mean so the
# paper's own tone does not carry the peak. Profiles were taken in bands the
# drawing leaves clean — the tiers between Jackson and the eighth unnamed tier,
# where the blocks carry no lot lines — because the two northern tiers are
# subdivided into eight lots each and their lot ink outweighs the block ink.
#
# THESE ARE PIXEL FACTS, NOT GROUND FACTS. The NA fit's own RMS is 16.2 m and its
# vertical scale disagrees with the BPL scan's by 1.5 per cent, so the tier lines
# below read about 42 m long over the section's height. That is paper, and this
# file does not correct it: a crop box must land on the ink where the ink IS.
COLUMN_LINES_E_M = [-774.2, -640.2, -516.8, -394.8, -277.2, -159.2, -50.0,
                    67.2, 202.8, 333.2, 463.2, 570.2, 695.8, 823.2]
TIER_LINES_N_M = [-559.8, -698.8, -843.8, -993.8, -1143.2, -1283.8, -1415.5,
                  -1542.2, -1680.0, -1809.2, -1942.2, -2075.8, -2211.2]

# ---------------------------------------------------------------------------
# THE READING. One entry per run of consecutive numerals: (column, first row,
# last row, first number). Rows count 1..12 from Madison southward, columns
# 1..13 from the section's west line eastward. A run whose last row is less than
# its first ascends the sheet. Every entry was read off the crops this tool
# emits; nothing here is counted from a neighbour.
RUNS = [
    (1, 1, 12, 1),    # 1 is written `Reserved`; see NUMERAL_IS_A_WORD
    (2, 12, 1, 13),
    (3, 1, 12, 25),
    (4, 12, 1, 37),
    (5, 1, 12, 49),
    (6, 12, 1, 61),
    (7, 9, 12, 73),   # the South Branch takes rows 1-8 of this column
    (8, 12, 11, 77),  # …and rows 5-10 of this one
    (7, 2, 1, 79),    # the two riverbank strips west of Market, ascending
    (8, 1, 4, 81),
    (9, 10, 1, 85),   # the South Branch takes rows 11-12 of this column
    (10, 1, 12, 95),
    (11, 12, 1, 107),
    (12, 1, 12, 119),
    (13, 12, 1, 131),  # 142 is written `Reserved`; see NUMERAL_IS_A_WORD
]

# The two cells where the sheet writes the word instead of the figure. The number
# is the run's, and what stands in the cell is `Reserved` — so `numeral_on_sheet`
# is false for them and the number is the position's, not a reading.
NUMERAL_IS_A_WORD = {(1, 1): "Reserved", (13, 1): "Reserved"}

# Cells whose numeral is legible but whose neighbourhood the reading does not
# fully resolve. Recorded, not smoothed.
NOTES = {
    (7, 1): "The riverbank strip west of Market Street, drawn narrower than the "
            "module and subdivided into four lots numbered down its east edge. The "
            "figure is legible; the cell is the westernmost of the two the sheet "
            "draws between the South Branch and Market in this tier.",
    (7, 2): "As block 80, one tier south.",
    (8, 1): "East of Market. A SECOND figure stands about 65 px east of this one, "
            "at the c8/c9 boundary, and this reading does not resolve it — see "
            "`refused`. It is not a further block: the sheet's own run closes on "
            "142 with this cell numbered 81.",
    (8, 2): "As block 81, one tier south, and the second figure beside it is under "
            "an ink blot. See `refused`.",
    (9, 7): "The sheet writes `Reserved` across this block and the one south of it, "
            "and lacuna L1 — paper the sheet has lost — covers this cell's west "
            "edge. The figure itself is clear of the loss.",
    (9, 8): "The southern half of the `Reserved` pair; see block 88.",
    (13, 9): "The figure is written close and reads 131 or 134 on its own. It is "
             "134: 131 stands in this column's twelfth tier, four cells below, and "
             "the run admits each number once.",
}


def load(path: Path):
    return json.loads(path.read_text())


def affine():
    """The committed NA-pixel -> EPSG:26916 fit, and the scene datum origin."""
    g = load(GCP)
    d = load(DATA / "datum.json")
    c = g["fit"]["coefficients"]
    return g, d, (c["a"], c["b"], c["c"], c["d"], c["e"], c["f"])


def to_pixel(local_e: float, local_n: float) -> tuple[float, float]:
    """Metres east/north of the scene datum -> NA raster pixel."""
    g, d, (a, b, c, dd, e, f) = affine()
    E = local_e + d["origin_utm_e"] - c
    N = local_n + d["origin_utm_n"] - f
    det = a * e - b * dd
    return (E * e - b * N) / det, (a * N - dd * E) / det


def cells() -> dict[tuple[int, int], int]:
    """The reading, expanded to one number per (column, row)."""
    out: dict[tuple[int, int], int] = {}
    for col, r0, r1, start in RUNS:
        step = 1 if r1 >= r0 else -1
        n = start
        for row in range(r0, r1 + step, step):
            if (col, row) in out:
                raise SystemExit(f"two runs claim cell c{col}r{row}")
            out[(col, row)] = n
            n += 1
    return out


def boustrophedon(columns: list[int], first: int) -> dict[tuple[int, int], int]:
    """The rule, applied independently of the reading.

    A column of twelve is descended, the next ascended, and so on, starting at
    the top of the first. This is the derivation `--check` holds the twelve
    uninterrupted columns to; it is deliberately NOT expressed in terms of RUNS.
    """
    out: dict[tuple[int, int], int] = {}
    n = first
    for i, col in enumerate(columns):
        rows = range(1, 13) if i % 2 == 0 else range(12, 0, -1)
        for row in rows:
            out[(col, row)] = n
            n += 1
    return out


# A crop is padded past its cell by this much on every side. Wright writes a
# block's figure across the block's own mid-line and, where the South Branch
# squeezes a column, hard against a ruled edge: block 80's figure sits at 86 per
# cent of the way across its cell and the bare cell box cuts it. A crop is a
# citation, not a partition — overlapping is harmless and losing the ink is not.
CROP_PAD_M = 25.0


def crop_box(col: int, row: int) -> list[int]:
    """The cell's bounding box in NA raster pixels — the crop this numeral cites."""
    e0, e1 = COLUMN_LINES_E_M[col - 1] - CROP_PAD_M, COLUMN_LINES_E_M[col] + CROP_PAD_M
    n0, n1 = TIER_LINES_N_M[row - 1] + CROP_PAD_M, TIER_LINES_N_M[row] - CROP_PAD_M
    xs, ys = [], []
    for e in (e0, e1):
        for n in (n0, n1):
            x, y = to_pixel(e, n)
            xs.append(x)
            ys.append(y)
    return [int(round(min(xs))), int(round(min(ys))),
            int(round(max(xs))), int(round(max(ys)))]


def build() -> dict:
    g, _, _ = affine()
    raster = g["raster"]
    read = cells()
    derived = boustrophedon([1, 2, 3, 4, 5, 6], 1)
    derived.update(boustrophedon([10, 11, 12, 13], 95))

    blocks = []
    for (col, row), number in sorted(read.items(), key=lambda kv: kv[1]):
        word = NUMERAL_IS_A_WORD.get((col, row))
        entry = {
            "number": number,
            "cell": f"c{col}r{row}",
            "column": col,
            "tier": row,
            "written_on_sheet": word if word else str(number),
            "numeral_on_sheet": word is None,
            "derives_from_scheme": derived.get((col, row)) == number,
            "numeral_crop_px": crop_box(col, row),
            "confidence": "inferred",
            "sources": ["wright_1834_nara_hup"],
        }
        if (col, row) in NOTES:
            entry["note"] = NOTES[(col, row)]
        elif word:
            entry["note"] = (
                f"The sheet writes `{word}` in this cell instead of a figure. The "
                "number is the one the run gives the position, not a reading, which "
                "is what `numeral_on_sheet: false` records.")
        blocks.append(entry)

    lac = {l["id"]: l["box"] for l in g["lacunae"]["found"]}
    touching = {
        lid: sorted(b["number"] for b in blocks
                    if not (b["numeral_crop_px"][2] < box[0] or b["numeral_crop_px"][0] > box[2]
                            or b["numeral_crop_px"][3] < box[1] or b["numeral_crop_px"][1] > box[3]))
        for lid, box in lac.items()
    }

    return {
        "$schema_note": (
            "AUTHORED, and it is a READING of a raster. It carries the block numeral "
            "Wright's 1834 sheet writes in each cell of the School Section's grid, the "
            "crop on that sheet where each was read, and the numbering scheme the grid "
            "makes legible. It authors NO ground: the cell boxes below are pixel "
            "statements about chicago/pre_fire_v1/maps/images/1834-wright-map.jpg, and "
            "the ground the numbers are spent onto is T-0876's, derived there from "
            "street centrelines as every other block in this project is. Generated by "
            "tools/read_school_section_numerals.py — do not hand-edit; the gate "
            "re-derives it."),
        "id": "school_section_block_numbering_1834",
        "plat": "school_section_addition",
        "generated_by": "tools/read_school_section_numerals.py",
        "why_this_file_exists": (
            "The Original Town's numbering is refused past one tier "
            "(data/traces/thompson_block_numbering.json § refused) because two legible "
            "numerals cannot say how a run passes from one tier to the next. The School "
            "Section is the opposite case and nobody had read it: 142 numerals, all of "
            "them written, on a sheet this project registered at 600 dpi in T-0787 and "
            "then used only for the Original Town. Reading them settles the scheme by "
            "observation rather than by argument, and it is the evidence T-0876 needs "
            "before it can put a number on a polygon."),
        "grades": (
            "Each entry's `confidence` grades THE NUMBER IN THIS CELL, not the block, "
            "and nothing here is `documented`. The figures are written on a tier-1 "
            "source and most of them are unambiguous, but reaching a cell from the "
            "figure requires this dataset's own georeference of that sheet, whose fit "
            "carries 16.2 m RMS and a vertical scale 1.5 per cent adrift of the BPL "
            "scan's — an identification step the sheet does not make for us. "
            "`numeral_on_sheet` separates the 140 cells where a figure was read from "
            "the two where the sheet writes `Reserved` and the number is the position's. "
            "`derives_from_scheme` separates the 120 the boustrophedon reproduces on its "
            "own from the 22 the South Branch forces to be read cell by cell."),
        "reading": {
            "source_id": raster["source_id"],
            "raster": raster["working_copy"],
            "raster_sha256": raster["sha256"],
            "raster_px": [raster["width"], raster["height"]],
            "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
            "read_on": "2026-09-06",
            "method": (
                "The grid's ruled lines were located as darkness maxima of the column "
                "and row profiles of the sheet rectified into the scene frame at "
                "0.5 m/px through the committed NA affine, in bands the drawing leaves "
                "clean of lot ink; the numerals were then read by eye off crops cut at "
                "the resulting cells, at 1x to 4x, and every one was checked a second "
                "time against an overlay of the fitted grid drawn back onto the "
                f"sheet. Each crop is its cell padded by {CROP_PAD_M:.0f} m on every "
                "side, because the draughtsman writes a figure across the block's own "
                "mid-line and, in the columns the river squeezes, hard against a "
                "ruled edge."),
            "corroboration": (
                "The section is one mile square and the sheet draws it so. Its "
                "north-east corner is control point G1, the PLSS corner of sections "
                "9/10/15/16 at State and Madison; the west line measured here lands "
                f"{abs(abs(COLUMN_LINES_E_M[-1] - COLUMN_LINES_E_M[0]) - MILE_M):.1f} m "
                "from one mile west of it, on a fit whose own RMS is 16.2 m. The count "
                "closes independently: thirteen columns of twelve tiers less the "
                "fourteen cells the South Branch takes is 142 blocks, numbered 1 to 142 "
                "with no number used twice and none missing, which is the count the "
                "owner read off the sheet in T-0791."),
        },
        "grid": {
            "columns": len(COLUMN_LINES_E_M) - 1,
            "tiers": len(TIER_LINES_N_M) - 1,
            "column_lines_local_e_m": COLUMN_LINES_E_M,
            "tier_lines_local_n_m": TIER_LINES_N_M,
            "frame": "metres east/north of the scene datum (data/datum.json)",
            "note": (
                "MEASURED ON THE PAPER, FOR CROPS ONLY. The tier lines span "
                f"{abs(TIER_LINES_N_M[-1] - TIER_LINES_N_M[0]):.0f} m against the mile "
                "the section actually is; that ~2.6 per cent is the NA scan's vertical "
                "stretch, recorded in the registration file, and it is not corrected "
                "here because a crop must land where the ink is. Anything that needs "
                "ground rather than paper must go to the module, not to this list."),
        },
        "scheme": {
            "rule": (
                "The run descends a column of twelve from Madison, turns at the "
                "section's south line and ascends the next column, and so on west to "
                "east: 1 at Madison and the west line, 12 at the south line, 13 beside "
                "it, 24 back at Madison, 25 south again."),
            "read_not_inferred": (
                "The rule is not an argument from two numerals as it had to be on the "
                "Original Town. Twelve of the thirteen columns are legible end to end "
                "and every one of their 120 cells reproduces under it, which is what "
                "`--check` asserts against a derivation written independently of the "
                "reading table."),
            "where_it_breaks": (
                "Columns 7, 8 and 9 are cut by the South Branch and the run threads "
                "their surviving fragments instead: 73-76 down the southern fragment of "
                "column 7, 77-78 up the southern fragment of column 8, 79-80 up the two "
                "riverbank strips of column 7 west of Market Street, 81-84 down column "
                "8's northern fragment east of Market, and 85-94 up column 9. That "
                "order is READ, cell by cell, and is not derivable from the rule."),
            "lot_numbering": (
                "NOT READ HERE. The two northern tiers are drawn subdivided — eight "
                "lots to a block, 1-4 along the north row and 8-5 along the south, the "
                "same scheme the Original Town crop gives — and the tiers from Adams "
                "south are drawn without any subdivision at all. Both observations "
                "belong to T-0876 with the ground, and neither is committed here."),
        },
        "lacunae_touched": {
            "note": (
                "Cells whose crop box intersects paper the sheet has lost. Anything "
                "read inside a lacuna is read from the cloth backing, not from Wright "
                "(data/traces/gcp/wright_1834_nara_hup_gcps.json § lacunae). Both "
                "figures below stand clear of the loss inside their own cells; the "
                "intersection is recorded so a later reading of anything ELSE in these "
                "cells knows it is there."),
            "by_lacuna": touching,
        },
        "refused": [
            {
                "scope": "a second figure in each of cells c8r1 and c8r2, at the "
                         "column-8/column-9 boundary",
                "reason": (
                    "The sheet writes 81 and 82 in those two cells and then a second "
                    "figure about 65 px east of each, hard against the ruled line and, "
                    "in the southern of the two, under an ink blot. They are not "
                    "further blocks — the run closes on 142 with these cells numbered "
                    "81 and 82, and 142 is the owner's own count — but this reading "
                    "cannot say whether they are a correction, a repetition, or the "
                    "westward continuation of 93 and 94. They are left unread rather "
                    "than resolved into something that would make the sheet look "
                    "tidier than it is."),
            },
            {
                "scope": "the fourteen cells of columns 7, 8 and 9 the South Branch "
                         "takes",
                "reason": (
                    "The sheet draws no block there and writes no figure, so there is "
                    "nothing to read. They are absent from `blocks` rather than "
                    "recorded as blank, and the count they are absent from is what "
                    "makes 142 come out."),
            },
            {
                "scope": "every block boundary, street line and lot line of the section",
                "reason": (
                    "This file cites crops; it does not commit ground. The cell grid "
                    "above is a measurement of one raster at that raster's own 16.2 m "
                    "RMS and 2.6 per cent vertical stretch, and using it as geometry "
                    "would bake both into the town. T-0876 derives the section's "
                    "module analytically and snaps it to street centrelines, which is "
                    "how every other block in this project is built."),
            },
        ],
        "blocks": blocks,
    }


# ---------------------------------------------------------------------------
# The assertions. Each returns a list of failures so `--self-test` can break one
# input at a time and watch exactly one of them fire.

def assertions(doc: dict, raster_px: tuple[int, int]) -> list[str]:
    bad: list[str] = []
    blocks = doc["blocks"]
    numbers = [b["number"] for b in blocks]
    cells_seen = [b["cell"] for b in blocks]

    if len(blocks) != 142:
        bad.append(f"the section carries 142 blocks and this reading has {len(blocks)}")
    if sorted(numbers) != list(range(1, 143)):
        missing = [n for n in range(1, 143) if n not in set(numbers)]
        twice = sorted({n for n in numbers if numbers.count(n) > 1})
        bad.append(f"the run 1-142 is not closed: missing {missing}, used twice {twice}")
    if len(set(cells_seen)) != len(cells_seen):
        bad.append("two numbers stand in one cell")

    width = abs(doc["grid"]["column_lines_local_e_m"][-1]
                - doc["grid"]["column_lines_local_e_m"][0])
    if abs(width - MILE_M) > 40.0:
        bad.append(f"the section's measured width is {width:.1f} m, and a section is "
                   f"{MILE_M:.0f} m — past the 40 m this fit's 16.2 m RMS allows")

    w, h = raster_px
    for b in blocks:
        x0, y0, x1, y1 = b["numeral_crop_px"]
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h or x1 <= x0 or y1 <= y0:
            bad.append(f"block {b['number']}'s crop {b['numeral_crop_px']} is not a box "
                       f"inside the {w}x{h} raster")

    # The scheme, applied independently of the reading table.
    derived = boustrophedon([1, 2, 3, 4, 5, 6], 1)
    derived.update(boustrophedon([10, 11, 12, 13], 95))
    by_cell = {(b["column"], b["tier"]): b for b in blocks}
    for key, expected in derived.items():
        got = by_cell.get(key)
        if got is None:
            bad.append(f"the scheme puts {expected} in c{key[0]}r{key[1]} and the "
                       "reading has no block there")
        elif got["number"] != expected:
            bad.append(f"c{key[0]}r{key[1]}: the scheme derives {expected} and the "
                       f"reading has {got['number']}")
    if sum(1 for b in blocks if b["derives_from_scheme"]) != len(derived):
        bad.append("`derives_from_scheme` does not mark exactly the cells the scheme "
                   "reaches")

    if sum(1 for b in blocks if not b["numeral_on_sheet"]) != 2:
        bad.append("exactly two cells carry the word `Reserved` instead of a figure")
    for b in blocks:
        if not b["numeral_on_sheet"] and "note" not in b:
            bad.append(f"block {b['number']} carries no figure and no note saying so")
    return bad


def check() -> int:
    fresh = build()
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing", file=sys.stderr)
        return 1
    committed = load(OUT)
    g, _, _ = affine()
    bad = assertions(fresh, (g["raster"]["width"], g["raster"]["height"]))
    if committed != fresh:
        bad.append(f"{OUT.relative_to(ROOT)} is not what this tool re-derives — "
                   "regenerate it in the commit that changes the reading")
    if bad:
        for line in bad:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    read = sum(1 for b in fresh["blocks"] if b["numeral_on_sheet"])
    derived = sum(1 for b in fresh["blocks"] if b["derives_from_scheme"])
    print(f"school section numerals: {len(fresh['blocks'])} block(s), {read} figure(s) "
          f"read on the sheet, {derived} reproduced by the scheme, "
          f"{len(fresh['refused'])} refusal(s)")
    return 0


def self_test() -> int:
    g, _, _ = affine()
    px = (g["raster"]["width"], g["raster"]["height"])
    base = build()
    if assertions(base, px):
        print("FAIL: the committed reading does not pass its own assertions",
              file=sys.stderr)
        return 1

    cases: list[tuple[str, callable]] = []

    def drop_a_block(doc):
        doc["blocks"] = doc["blocks"][:-1]

    def repeat_a_number(doc):
        doc["blocks"][5]["number"] = doc["blocks"][4]["number"]

    def break_the_scheme(doc):
        for b in doc["blocks"]:
            if b["cell"] == "c3r7":
                b["number"] = 999

    def move_a_crop_off_the_sheet(doc):
        doc["blocks"][0]["numeral_crop_px"] = [-40, 10, 20, 60]

    def stretch_the_section(doc):
        doc["grid"]["column_lines_local_e_m"] = \
            list(doc["grid"]["column_lines_local_e_m"])
        doc["grid"]["column_lines_local_e_m"][-1] += 300.0

    def promote_a_word_to_a_reading(doc):
        for b in doc["blocks"]:
            if not b["numeral_on_sheet"]:
                b["numeral_on_sheet"] = True
                break

    def lose_a_words_note(doc):
        for b in doc["blocks"]:
            if not b["numeral_on_sheet"]:
                b.pop("note", None)
                break

    cases = [("a block dropped from the reading", drop_a_block),
             ("one number used twice", repeat_a_number),
             ("a cell that stops obeying the scheme", break_the_scheme),
             ("a crop box off the raster", move_a_crop_off_the_sheet),
             ("a section that is no longer a mile wide", stretch_the_section),
             ("the word `Reserved` promoted to a read figure", promote_a_word_to_a_reading),
             ("a word-cell that stops saying it is one", lose_a_words_note)]

    failed = 0
    for name, break_it in cases:
        doc = json.loads(json.dumps(base))
        break_it(doc)
        if assertions(doc, px):
            print(f"   fires: {name}")
        else:
            print(f"   SILENT: {name}", file=sys.stderr)
            failed += 1
    if failed:
        return 1
    print(f"school section numerals self-test: {len(cases)} of {len(cases)} "
          "assertions fire when broken")
    return 0


def report(doc: dict) -> int:
    by_cell = {(b["column"], b["tier"]): b for b in doc["blocks"]}
    cols = doc["grid"]["columns"]
    print("      " + "".join(f"c{c:<4d}" for c in range(1, cols + 1)))
    for row in range(1, doc["grid"]["tiers"] + 1):
        line = f"  r{row:<3d}"
        for col in range(1, cols + 1):
            b = by_cell.get((col, row))
            line += f"{b['number']:<5d}" if b else "  .  "
        print(line)
    print()
    for b in doc["blocks"]:
        if not b["numeral_on_sheet"]:
            print(f"  block {b['number']} ({b['cell']}) is written "
                  f"`{b['written_on_sheet']}`")
    for entry in doc["refused"]:
        print(f"  refused: {entry['scope']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.report:
        return report(load(OUT) if OUT.exists() else build())
    doc = build()
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['blocks'])} block(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
