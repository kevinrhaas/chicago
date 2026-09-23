#!/usr/bin/env python3
"""Read Kinzie's Addition's block numerals off Wright's 1834 survey.

    tools/read_kinzie_addition_numerals.py              print the reading
    tools/read_kinzie_addition_numerals.py --write      write the trace
    tools/read_kinzie_addition_numerals.py --check      re-derive it from the committed pixels
    tools/read_kinzie_addition_numerals.py --check-sheet  re-measure the two bounds off the raster
    tools/read_kinzie_addition_numerals.py --self-test  break each assertion and watch it fire

WHAT THIS FILE IS AND IS NOT. It is the READING: which numeral Wright writes in which
cell of Kinzie's Addition, and the crop on the sheet where each was read. It authors NO
ground. Every cell box below is a PIXEL statement about
chicago/pre_fire_v1/maps/images/1834-wright-map.jpg, and where the ground under a number
goes is somebody else's ticket — the Addition's streets are seated by
tools/seat_kinzie_addition_streets.py (T-1060) and its block parcels are not built yet.

WHY THE GRID COSTS ALMOST NOTHING HERE. T-1060 already measured the Addition's eleven
street corridors on this sheet and committed them as pixel pairs in
data/traces/kinzie_addition_street_grid.json. A cell of the block grid is the rectangle
two consecutive corridors leave between them, so this tool READS that file rather than
re-measuring what is already committed — and a corridor that moves there moves the crops
here, which is what `--check` is for. Only two bounds are this tool's own, because the
street reading had no reason to want them:

  * THE ADDITION'S WEST BOUNDARY RULE. There is a ruled line at NA x 2918 and the next
    one east is Wolcott Street's west kerb at 2943 — so the westernmost column of this
    plat is a gore 25 px wide, about 17 m, and Wright numbers it like any other block.
    He writes its figure OUTSIDE it, in the margin west of the boundary, because 17 m of
    paper will not hold a numeral. That is why `numeral_outside_cell` exists and why the
    crop for column 1 reaches west past its own cell.
  * THE ADDITION'S NORTH BOUNDARY. The 50-54 tier's block tops stand at NA y 1018 and the
    tract's boundary line at about y 970; north of that is blank paper. The tier is short
    — 96 px against the 92-124 px the tiers below run — and it is the last one.

Both are re-measured from the raster by `--check-sheet` (the PR runs it; `--check` is the
cheap half that runs in tools/check.sh on every commit).

WHAT THE READING SETTLES, AND IT IS NOT WHAT THE TICKET ASSUMED. T-0789 summarised the
sheet as numbering the Addition "in tiers from the river northward (1-7 on the river
tier, 8-13, 14-19, 20-26, 27-31, 32-36, 37-43, 44-48, 49-54)". Read cell by cell, the
tiers are NOT those. Every tier from the river to Superior Street holds SIX cells, not a
varying five to seven, and the run is a plain boustrophedon over a six-column grid whose
top and bottom rows lose their east column to the lake and the river:

    r1  50  51  52  53  54   --            north (Superior Street's north side)
    r2  49  48  47  46  45  44
    r3  38  39  40  41  42  43
    r4  37  36  35  34  33  32
    r5  26  27  28  29  30  31
    r6  25  24  23  22  21  20
    r7  14  15  16  17  18  19
    r8  13  12  11  10   9   8
    r9   3   4   5   6   7   --            south (the river bank)
        c1  c2  c3  c4  c5  c6

So the tier boundaries are 20-25, 26-31, 32-37, 38-43 and 44-49, and the summary's
20-26, 27-31, 32-36, 37-43, 44-48 are wrong by one at five places. Fifty-one figures are
written and read; block 11 carries the words `Kinzie Block` instead of a figure and takes
its number from the run, exactly as the School Section's two `Reserved` cells do
(data/traces/school_section_block_numbering.json).

AND BLOCKS 1 AND 2 ARE NOT FOUND. The run puts them west of block 3 in the river tier,
outside the Addition's west boundary rule, where Wright draws the Original Town's north
division instead — two eight-lot blocks that carry their own bold 1 and 2 across their
mid-lines, on ground this plat does not own. Nothing inside the Addition's boundary
carries either figure. They are recorded in § refused rather than counted onto a cell:
a number placed to make a run close is not a reading.

T-1103 THEN ASKED WHOSE THOSE TWO FIGURES ARE, and both halves of the answer are now
derived here rather than described.

  * WHOSE. They are the Original Town's North Division blocks 2 and 1 — Clark to
    Dearborn and Dearborn to Wolcott, Kinzie Street to the river — which T-1088 read
    off the BPL scan from crops cut out of committed street lines, and which
    `where_one_and_two_stand()` re-cuts here and carries into this sheet's pixel space
    through the committed scan-to-scan affine. They land on the ground T-1061 refused.
    The two series are independent, not one series broken: Thompson's North Division
    also prints 3 4 5 6 7 in the same tier band, and so does the Addition.
  * AND THEY ARE NOT EVEN WHERE THE RUN WOULD PUT THEM. Extrapolating the boustrophedon
    west of block 3 asks for two cells in the Addition's river tier, y 2009-2133. The
    figures stand a whole tier lower, y 2141-2351, in a tier the Addition does not have,
    because Kinzie Street is south of Michigan Street and only the Original Town plats
    that ground. So the westward extrapolation never had anything to find.
  * THE DOCUMENTARY TEST T-1061 NAMED RETURNS A MEASURED NEGATIVE. `documentary_sweep()`
    reads every claim in data/research/newspapers/extracted/ that names the Addition and
    asks which name a numbered parcel in it. Every one that does names a WATER LOT — No.
    11 and No. 12 — and not one names a block of the Addition at all, let alone block 1
    or 2. So the notice that would settle it is not in the corpus this project holds.

WHAT IS RULED, therefore: the Addition's own block numbering as this sheet draws it
begins at 3, and blocks 1 and 2 stay refused rather than placed. That is a statement
about the drawing and about a corpus read to exhaustion, not about the recorded plat,
which this project still does not hold — so the grade stays `inferred` and § refused
keeps saying what would overturn it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_north_division_numerals as north_division  # noqa: E402
import wright_px  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "data" / "traces" / "kinzie_addition_street_grid.json"
GCP = ROOT / "data" / "traces" / "gcp" / "wright_1834_nara_hup_gcps.json"
OUT = ROOT / "data" / "traces" / "kinzie_addition_block_numbering.json"

# ---------------------------------------------------------------------------
# THE TWO BOUNDS THIS TOOL MEASURED, in NA raster pixels. Both were taken the way
# T-1060 took the street rules: ink projected onto one axis over a window the
# drawing leaves clean, detrended against a moving mean so the paper's own tone
# does not carry the peak, and a sharp narrow maximum taken as a ruled line.
WEST_BOUNDARY_PX_X = 2918.0      # window y 1525-1600 (the Ontario-Ohio tier), x 2840-3010
NORTH_BLOCK_TOP_PX_Y = 1018.2    # windows x 2990-3090 and x 3150-3250, y 900-1200
# A ruled line is found to about a pixel; `--check-sheet` allows three, which is
# the spread between the two windows the north bound was read in.
SHEET_TOL_PX = 3.0

# The two edges of the plat that are NOT ruled lines, and are conventions for the
# CROP only. The river tier's south edge is the river bank and the east column's
# east edge is the lake shore; both are drawn as freehand water and neither is a
# boundary this reading may claim. They bound a crop box and nothing else.
RIVER_BANK_PX_Y = 2133.0
LAKE_SHORE_PX_X = 3760.0

# WHERE T-1061 SAW THE TWO BOLD FIGURES, in NA raster pixels, quoted from the
# refusal it wrote. T-1103 identifies them, and the identification is checked
# against this span rather than replacing it: a derivation that drifted off the
# ground the refusal was written about would be identifying something else.
T_1061_SPAN_PX = (2610.0, 2140.0, 2930.0, 2320.0)
# The two Original Town blocks the identification names, east to west, as
# tools/read_north_division_numerals.py keys them.
THOMPSON_BLOCKS = (2, 1)

# The corpus the documentary test reads, and the shape of the question put to it.
CORPUS = ROOT / "data" / "research" / "newspapers" / "extracted"
ADDITION_RE = re.compile(r"[Kk]in[sz]i[eo]'?s?\s+[Aa]ddition")
# A numbered parcel named in the same claim. `Water Lot` is kept distinct from
# `Block` because the whole finding is that the corpus only ever says the first.
# Case-insensitive because the Democrat sets these lines in small caps and the
# transcriptions keep it: `WATER Lot No. 12` is the same parcel as `water lot No. 11`.
WATER_LOT_RE = re.compile(r"water\s+lots?\s*(?:No\.?)?\s*(\d+)", re.IGNORECASE)
BLOCK_RE = re.compile(r"blocks?\s*(?:No\.?)?\s*(\d+)", re.IGNORECASE)

# A crop is padded past its cell by this much on every side. Wright writes a
# block's figure across the block's own mid-line, and in the columns the lake
# squeezes he writes it hard against a ruled edge — block 44's figure is half over
# the shore wash. A crop is a citation, not a partition: overlapping is harmless
# and losing the ink is not.
CROP_PAD_PX = 30
# Column 1 is the 17 m gore and its figures are written in the margin WEST of the
# tract, so its crop reaches that far west as well. Measured off the widest of
# them (50, whose ink starts at x 2877).
GORE_CROP_WEST_PX = 70

COLUMNS = [
    (1, "west_gore", "the gore between the Addition's west boundary and Wolcott Street"),
    (2, "wolcott_cass", "Wolcott Street to Cass Street"),
    (3, "cass_rush", "Cass Street to Rush Street"),
    (4, "rush_pine", "Rush Street to Pine Street"),
    (5, "pine_sand", "Pine Street to Sand Street"),
    (6, "east_of_sand", "Sand Street to the lake shore"),
]

# North to south. Each is the pair of streets whose corridors bound the tier; None
# stands for a bound that is not a street (the tract's north boundary, the river).
TIERS = [
    (1, None, "superior"),
    (2, "superior", "huron"),
    (3, "huron", "erie"),
    (4, "erie", "ontario"),
    (5, "ontario", "ohio"),
    (6, "ohio", "indiana"),
    (7, "indiana", "illinois"),
    (8, "illinois", "michigan"),
    (9, "michigan", None),
]

# THE READING. One entry per cell, `(column, tier): number`. Every one was read off
# the crop this tool computes, at 2.2x to 4.6x, and every one was checked a second
# time against the column it stands in and the tier above and below it. The two
# cells the grid has and the plat does not are absent rather than null: at r1c6 and
# r9c6 the water is already there.
READING: dict[tuple[int, int], int] = {}
for _row, _run in {
    1: [50, 51, 52, 53, 54],
    2: [49, 48, 47, 46, 45, 44],
    3: [38, 39, 40, 41, 42, 43],
    4: [37, 36, 35, 34, 33, 32],
    5: [26, 27, 28, 29, 30, 31],
    6: [25, 24, 23, 22, 21, 20],
    7: [14, 15, 16, 17, 18, 19],
    8: [13, 12, 11, 10, 9, 8],
    9: [3, 4, 5, 6, 7],
}.items():
    for _col, _n in enumerate(_run, start=1):
        READING[(_col, _row)] = _n

# The cell where the sheet writes a name instead of a figure. The number is the
# run's, not a reading, which is what `numeral_on_sheet: false` records. The name
# itself, and what the corpus says about it, is T-1062's.
NAME_ON_SHEET = {(3, 8): "Kinzie Block"}

# How legible the ink actually was, for the three cells where the answer is not
# "perfectly". Everything absent from this table is `clear`.
LEGIBILITY = {
    (1, 9): ("obscured", "conjectural"),
    (6, 2): ("cut", "inferred"),
}

NOTES = {
    (1, 9): ("A stain over the boundary rule takes most of this figure with it. What "
             "survives reads as a 3, the run wants a 3, and the two agreeing is not the "
             "same as reading one — so this is the one numeral in the Addition graded "
             "`conjectural`. The BPL copy of the same drawing (`wright_1834`, "
             "commonwealth:js957744g) is a second scan of this ink and has not been cut "
             "at this cell; that is the cheapest thing that would settle it."),
    (6, 2): ("Written small and hard against the shore wash, in the last scrap of block "
             "the lake leaves at this tier — about a third of the cell its neighbours "
             "get. Both figures are legible at 4x and the crop below is the whole of "
             "what is left of the block."),
    (3, 8): ("The sheet letters `Kinzie Block` across this cell in two lines, between "
             "Illinois and Michigan, Cass to Rush, and writes no figure in it. It is the "
             "only block in the Addition given a name and one of two on the whole sheet "
             "— the Public Square is the other. The number is the run's: block 12 stands "
             "west of it and block 10 east of it, in a tier that descends eastward. The "
             "name, and the search of the newspaper and directory corpus for the phrase, "
             "is T-1062's and is not claimed here."),
    (1, 1): ("The gore's figure, like every other in column 1, is written in the margin "
             "WEST of the Addition's boundary rule because the cell is 17 m wide. The "
             "crop reaches west to carry it, which is why it overlaps the ground of "
             "another plat — a citation is not a claim about who owns the paper it "
             "covers."),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def rule_px(readings: dict, street: str, which: int) -> float:
    """The mean of every window that read this street's kerb.

    The sheet is a degree or so off square in this corner, so a corridor read in
    the west window and again in the east window differs by about ten pixels. The
    mean is what a crop should be cut on: it is wrong by five pixels at either end
    of a grid whose crops are padded by thirty.
    """
    windows = readings[street]
    return sum(w["rule_px_x" if "rule_px_x" in w else "rule_px_y"][which]
               for w in windows) / len(windows)


def grid_lines(grid: dict) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """The cell bands, west to east and north to south, in NA raster pixels."""
    ew = grid["readings"]["east_west"]
    ns = grid["readings"]["north_south"]

    cols: list[tuple[float, float]] = [
        (WEST_BOUNDARY_PX_X, rule_px(ns, "wolcott", 0)),
        (rule_px(ns, "wolcott", 1), rule_px(ns, "cass", 0)),
        (rule_px(ns, "cass", 1), rule_px(ns, "rush", 0)),
        (rule_px(ns, "rush", 1), rule_px(ns, "pine", 0)),
        (rule_px(ns, "pine", 1), rule_px(ns, "sand", 0)),
        (rule_px(ns, "sand", 1), LAKE_SHORE_PX_X),
    ]
    rows: list[tuple[float, float]] = []
    for _row, north, south in TIERS:
        y0 = NORTH_BLOCK_TOP_PX_Y if north is None else rule_px(ew, north, 1)
        y1 = RIVER_BANK_PX_Y if south is None else rule_px(ew, south, 0)
        rows.append((y0, y1))
    return cols, rows


def crop_box(cols, rows, col: int, row: int, raster: dict) -> list[int]:
    x0, x1 = cols[col - 1]
    y0, y1 = rows[row - 1]
    x0 -= CROP_PAD_PX + (GORE_CROP_WEST_PX if col == 1 else 0)
    x1 += CROP_PAD_PX
    y0 -= CROP_PAD_PX
    y1 += CROP_PAD_PX
    return [max(0, int(round(x0))), max(0, int(round(y0))),
            min(raster["width"], int(round(x1))), min(raster["height"], int(round(y1)))]


def boustrophedon() -> dict[tuple[int, int], int]:
    """The run, derived from the rule alone and not from the table above.

    It starts at the west end of the river tier, runs east, turns at the end of
    every tier and climbs. The two cells the water takes — the east column of the
    river tier and of the top tier — are simply not in the grid, so the run steps
    past them, which is what makes the turn at r9/r8 and at r2/r1 look like it
    skips. It starts at 3 because 3 is what stands in the first cell; blocks 1 and
    2 are not on this plat's ground and § refused says so.
    """
    out: dict[tuple[int, int], int] = {}
    n = 3
    for row in range(9, 0, -1):
        cols = [c for c in range(1, 7) if (c, row) in READING]
        if row % 2 == 1:          # r9, r7, r5, r3, r1 run west to east
            order = sorted(cols)
        else:                      # r8, r6, r4, r2 run east to west
            order = sorted(cols, reverse=True)
        for col in order:
            out[(col, row)] = n
            n += 1
    return out


def _scan_to_scan(gcp: dict):
    """BPL pixel -> NA pixel, the affine this project already committed.

    T-1088 read the two figures on the BPL master and this file reads the Addition
    on the NA sheet, so an identification has to cross between them. The crossing
    is the committed eight-point affine and it costs that fit's 8.5 px residual —
    which is why the check below allows a whole cell's worth of slop and not a
    pixel's.
    """
    c = gcp["scan_to_scan"]["coefficients"]

    def to_na(x: float, y: float) -> tuple[float, float]:
        return (c["a"] * x + c["b"] * y + c["c"],
                c["d"] * x + c["e"] * y + c["f"])

    return to_na


def where_one_and_two_stand(gcp: dict) -> dict:
    """The two bold figures, identified — re-cut from committed street lines.

    Nothing here is typed in. `read_north_division_numerals.boxes()` cuts each
    Original Town North Division block out of data/streets/1835.json exactly as the
    gate already makes it; `wright_px` puts that on the BPL master; the affine above
    carries it onto this sheet. If a street moves, this moves with it.
    """
    to_na = _scan_to_scan(gcp)
    streets = north_division._streets()
    boxes = north_division.boxes(streets)
    found = []
    for number in THOMPSON_BLOCKS:
        _, (x0, south, x1, north) = boxes[number]
        p0 = wright_px.to_pixel(x0, north)
        p1 = wright_px.to_pixel(x1, south)
        a, b = to_na(*p0), to_na(*p1)
        found.append({
            "number": number,
            "plat": "thompson_plat_1830",
            "tier": "north_division_kinzie_to_the_river",
            "bounded_by": ("Clark Street to Dearborn Street" if number == 2 else
                           "Dearborn Street to Wolcott Street") +
                          ", Kinzie Street to the river",
            "box_in_na_pixel_space": [round(v, 1) for v in (a[0], a[1], b[0], b[1])],
            "read_independently_by": "T-1088, off the BPL scan, at "
                                     "data/traces/thompson_block_numbering.json "
                                     "§ blocks_not_in_the_grid",
        })
    xs = [v for f in found for v in (f["box_in_na_pixel_space"][0], f["box_in_na_pixel_space"][2])]
    ys = [v for f in found for v in (f["box_in_na_pixel_space"][1], f["box_in_na_pixel_space"][3])]
    return {
        "figures": found,
        "union_in_na_pixel_space": [round(min(xs), 1), round(min(ys), 1),
                        round(max(xs), 1), round(max(ys), 1)],
        "the_span_t_1061_refused": list(T_1061_SPAN_PX),
        "why_these_keys_do_not_end_in_px": (
            "tools/adjudicate_wright_na_fit.py harvests every `*_px` key in this trace "
            "as a reading made ON this sheet, and measures how far a change of "
            "registration would move it. These boxes are not that. They start at "
            "committed street lines in metres and arrive here through the scan-to-scan "
            "affine, never through the NA sheet's own fit, so adopting a different fit "
            "would not move them at all and counting them would make that table say "
            "something false."),
        "derivation": (
            "data/streets/1835.json -> tools/read_north_division_numerals.py "
            "§ boxes() -> tools/wright_px.py (BPL pixels) -> this file's "
            "gcps § scan_to_scan (NA pixels). Every step is committed and the "
            "gate re-runs all of them."),
    }


def documentary_sweep() -> dict:
    """The test T-1061 named, put to the corpus and counted.

    'A Democrat notice selling a lot in block 1 or block 2 of the Addition with a
    street named beside it' — this reads every extracted claim that names the
    Addition and records which of them name a numbered parcel with it.
    """
    naming, parcels, blocks = 0, [], []
    for path in sorted(CORPUS.glob("*.json")):
        doc = load(path)
        for claim in doc["claims"]:
            text = (claim.get("normalized") or "").replace("[", "").replace("]", "")
            if not ADDITION_RE.search(text):
                continue
            naming += 1
            water = WATER_LOT_RE.findall(text)
            block = BLOCK_RE.findall(text)
            cite = f"{doc['issue_id']} {claim['id']}"
            for n in water:
                parcels.append({"parcel": f"water lot {n}", "claim": cite})
            for n in block:
                blocks.append({"block": int(n), "claim": cite})
    return {
        "corpus": "data/research/newspapers/extracted/",
        "question": (
            "which claims that name Kinzie's Addition also name a numbered parcel "
            "in it, and does any of them name a block"),
        "method": (
            "Every claim's `normalized` transcription with its restoration brackets "
            "stripped, matched for the Addition's name in the spellings the paper "
            "actually prints (Kinzie's / Kinsie's / Kinzio's, Addition / addition), "
            "then for `Water Lot No. N` and `Block No. N` in the same claim. "
            "Re-run by the gate, so a notice added to the corpus reopens this."),
        "claims_naming_the_addition": naming,
        "parcels_named_with_it": parcels,
        "block_numbers_in_the_same_claim": blocks,
        "finding": (
            "EVERY parcel the corpus names in Kinzie's Addition is a WATER LOT — No. "
            "11 in the Breed v. Hale attachment, and No. 12 in Hiram Pearsons's "
            "stolen-timber notice, its reprint a week later, and his sale notice that "
            "September. Not one claim in the run names a block OF the Addition. The "
            "block numbers listed above stand in the same claim as the Addition's name "
            "and belong elsewhere on both counts: nine of them are the attachment's own "
            "parcels, which that notice puts in section 16 in so many words, and the "
            "tenth is Pearsons's 'Lots 2, 7 and 8 in block 5', printed after his water "
            "lot with no plat named — the same advertiser is offering school-section "
            "lots in the next advertisement. Block 5 is left ambiguous here rather than "
            "annexed: an unattributed block 5 is not evidence about blocks 1 and 2 "
            "either way. The state's town-lot register cannot help and is not cited as "
            "if it could: Kinzie's Addition is private ground and every parcel in "
            "data/research/land_sales/ is coded CHIOT, CHIOTV, CHIV or CHI."),
    }


def build() -> dict:
    grid = load(GRID)
    gcp = load(GCP)
    raster = gcp["raster"]
    identification = where_one_and_two_stand(gcp)
    sweep = documentary_sweep()
    cols, rows = grid_lines(grid)
    derived = boustrophedon()
    col_name = {c: (slug, gloss) for c, slug, gloss in COLUMNS}

    blocks = []
    for (col, row), number in sorted(READING.items(), key=lambda kv: kv[1]):
        name = NAME_ON_SHEET.get((col, row))
        legibility, confidence = LEGIBILITY.get((col, row), ("clear", "inferred"))
        entry = {
            "number": number,
            "cell": f"c{col}r{row}",
            "column": col,
            "column_name": col_name[col][0],
            "tier": row,
            "bounded_by": col_name[col][1],
            "written_on_sheet": name if name else str(number),
            "numeral_on_sheet": name is None,
            "numeral_outside_cell": col == 1,
            "derives_from_scheme": derived.get((col, row)) == number,
            "numeral_crop_px": crop_box(cols, rows, col, row, raster),
            "legibility": legibility,
            "confidence": confidence,
            "sources": ["wright_1834_nara_hup"],
        }
        if (col, row) in NOTES:
            entry["note"] = NOTES[(col, row)]
        blocks.append(entry)

    touched = sorted(
        lac["id"] for lac in gcp["lacunae"]["found"]
        for box in [lac["box"]]
        if any(not (b["numeral_crop_px"][2] < box[0] or b["numeral_crop_px"][0] > box[2]
                    or b["numeral_crop_px"][3] < box[1] or b["numeral_crop_px"][1] > box[3])
               for b in blocks))

    return {
        "$schema_note": (
            "AUTHORED, and it is a READING of a raster. It carries the block numeral "
            "Wright's 1834 sheet writes in each cell of Kinzie's Addition, the crop on "
            "that sheet where each was read, and the run the grid makes legible. It "
            "authors NO ground: the cell boxes below are pixel statements about "
            "chicago/pre_fire_v1/maps/images/1834-wright-map.jpg, and the streets these "
            "cells stand between are seated in data/streets/1835.json by T-1060. "
            "Generated by tools/read_kinzie_addition_numerals.py — do not hand-edit; "
            "the gate re-derives it."),
        "id": "kinzie_addition_block_numbering_1834",
        "plat": "kinzie_addition",
        "ticket": "T-1061 (piece 2 of T-0789)",
        "generated_by": "tools/read_kinzie_addition_numerals.py",
        "why_this_file_exists": (
            "The Democrat's 1834-35 land notices sell lots in Kinzie's Addition by block "
            "and lot number and not one of them can be placed, because nothing in this "
            "project said which block on the ground is block 11. T-1060 put the "
            "Addition's thirteen streets on the sheet's own measure; this puts the "
            "numbers in the cells between them. It also corrects the tiering T-0789 "
            "assumed from a first look: every tier from the river to Superior Street "
            "holds SIX cells, so the runs are 20-25, 26-31, 32-37, 38-43 and 44-49, not "
            "the 20-26, 27-31, 32-36, 37-43, 44-48 the parent ticket wrote down."),
        "grades": (
            "Each entry's `confidence` grades THE NUMBER IN THIS CELL, not the block, "
            "and nothing here is `documented`. The figures are written on a tier-1 "
            "source and fifty of the fifty-one are unambiguous at 4x, but reaching a "
            "CELL from a figure runs through this dataset's own georeference of this "
            "sheet, whose fit carries 16.19 m RMS — an identification step the sheet "
            "does not make for us. `numeral_on_sheet` separates the fifty-one cells "
            "where a figure was read from the one that carries the words `Kinzie Block` "
            "and takes its number from the run. `legibility` says which ink was clear, "
            "which was cut by the lake and which is under a stain."),
        "reading": {
            "source_id": raster["source_id"],
            "raster": raster["working_copy"],
            "raster_sha256": raster["sha256"],
            "raster_px": [raster["width"], raster["height"]],
            "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
            "read_on": "2026-09-12",
            "method": (
                "The cell boxes are the rectangles left between the street corridors "
                "T-1060 committed in data/traces/kinzie_addition_street_grid.json, read "
                "here rather than re-measured; a corridor that moves there moves these "
                "crops. Two bounds are this tool's own and were measured the same way "
                "T-1060 measured the corridors — ink projected onto one axis over a "
                "clean window, detrended against a moving mean, a sharp narrow maximum "
                "taken as a ruled line: the Addition's west boundary rule at NA x 2918 "
                "(window y 1525-1600) and the 50-54 tier's block tops at NA y 1018 "
                "(windows x 2990-3090 and x 3150-3250). Every numeral was then read by "
                "eye off crops cut at the resulting cells, at 2.2x to 4.6x, and checked "
                "a second time against its column and the tiers above and below it. "
                "`--check-sheet` re-measures the two bounds off the raster."),
            "crop_convention": (
                f"A cell padded by {CROP_PAD_PX} px on every side, and by a further "
                f"{GORE_CROP_WEST_PX} px to the WEST in column 1, where Wright writes "
                "the figure outside the cell because the gore is only 17 m across. Two "
                "edges of the plat are not ruled lines and bound a crop only: the river "
                "tier's south edge (NA y 2133) is the river bank and the east column's "
                "east edge (NA x 3760) is the lake shore, both drawn freehand."),
        },
        "grid": {
            "columns": len(COLUMNS),
            "tiers": len(TIERS),
            "column_bands_px_x": [[round(a, 1), round(b, 1)] for a, b in cols],
            "tier_bands_px_y": [[round(a, 1), round(b, 1)] for a, b in rows],
            "west_boundary_px_x": WEST_BOUNDARY_PX_X,
            "north_block_top_px_y": NORTH_BLOCK_TOP_PX_Y,
            "gore_width_px": round(rule_px(grid["readings"]["north_south"], "wolcott", 0)
                                   - WEST_BOUNDARY_PX_X, 1),
            "gore_note": (
                "COLUMN 1 IS A GORE, NOT A BLOCK THE SIZE OF ITS NEIGHBOURS. The "
                "Addition's west boundary rule and Wolcott Street's west kerb leave 25 "
                "px — about 17 m against the plat's 110 m column pitch — and Wright "
                "numbers the strip like any other block, nine times, writing each "
                "figure in the margin outside it. What that strip WAS is not settled "
                "here and is not this reading's to settle: it is a block question and "
                "T-0789's clause 5 forbids drawing a lot line the sheet does not draw."),
        },
        "scheme": {
            "shape": "boustrophedon, ascending northward from the river tier",
            "run": (
                "West to east along the river tier (3-7), then east to west along the "
                "Michigan-Illinois tier (8-13), turning at every tier and climbing to "
                "the Superior tier (50-54). Every tier between the river and Superior "
                "Street holds six cells; the river tier and the top tier lose their east "
                "column to the river and the lake, which is why the run steps from 7 to "
                "8 and from 49 to 50 across the turn rather than through a sixth cell."),
            "reproduces": (
                "All 52 cells. The run is derived in tools/read_kinzie_addition_"
                "numerals.py from the rule alone, independently of the table it checks, "
                "and it agrees with every figure read — so the numbering rests on the "
                "ink AND on the rule, and block 11's missing figure is the one place "
                "only the rule speaks."),
        },
        "lacunae_touched": touched,
        "lacunae_note": (
            "The sheet has lost two pieces of paper and both are recorded in "
            "data/traces/gcp/wright_1834_nara_hup_gcps.json § lacunae. Neither is "
            "anywhere near this plat — the larger sits on the South Branch 2,300 px "
            "south of the Addition's lowest crop — so no numeral here is read off cloth "
            "backing. The list above is empty and is computed, not asserted."),
        "refused": [
            {
                "scope": "blocks 1 and 2",
                "reason": (
                    "NOT FOUND, AND NOT COUNTED IN. The run puts them west of block 3 in "
                    "the river tier, beyond the Addition's west boundary rule, and the "
                    "ground there is the Original Town's north division: two eight-lot "
                    "blocks carrying their own bold 1 and 2 across their mid-lines at NA "
                    "x 2610-2930, y 2140-2320, on a plat this file is not reading. "
                    "Nothing inside the Addition's boundary carries either figure. "
                    "Putting them on those two blocks would be reading one plat's "
                    "numbers onto another's ground to make a run close, and putting them "
                    "on no cell at all is the honest half of the same reading."),
                "identified_2026_09_13": identification,
                "identified_note": (
                    "T-1103. The two figures are NAMED, and the refusal is unchanged by "
                    "it: they are the Original Town's North Division blocks 2 and 1, "
                    "Clark to Dearborn and Dearborn to Wolcott, between Kinzie Street "
                    "and the river. The boxes above are cut from committed street lines "
                    "and carried onto this sheet, and they land on the span T-1061 "
                    "refused. Two things follow. FIRST, the two series are independent "
                    "rather than one series broken across a boundary: Thompson's North "
                    "Division prints 7 6 5 4 3 2 1 west to east in this tier and the "
                    "Addition prints 3 4 5 6 7 west to east in its own, so 3 to 7 are "
                    "written twice on this sheet, on two plats, and neither run "
                    "continues the other. SECOND, the figures are not even where the "
                    "westward extrapolation asks for them: it wants two cells in the "
                    "Addition's river tier at y 2009-2133 and these stand a tier lower, "
                    "because Kinzie Street is south of Michigan Street and only the "
                    "Original Town plats that ground. Neither the Addition's west "
                    "boundary rule nor the legend's tract colouring is impeached by "
                    "them — they were never the Addition's to begin with."),
                "the_documentary_test": sweep,
                "ruling_2026_09_13": (
                    "THE ADDITION'S OWN NUMBERING, AS THIS SHEET DRAWS IT, BEGINS AT 3, "
                    "and blocks 1 and 2 stay refused rather than placed. The sheet "
                    "carries fifty-two cells inside the Addition's boundary and they "
                    "hold 3 to 54 with nothing missing; the ground west of the boundary "
                    "that the run points at belongs to the Original Town and is now "
                    "named; the water lots cannot be the remainder, because T-1063 read "
                    "the river front as one continuous 1-35 lot strip; and the corpus "
                    "names no block of the Addition at all. This is a reading of a "
                    "drawing and of a corpus read to exhaustion, NOT a reading of the "
                    "recorded plat, which this project does not hold — so it is stated "
                    "here and no cell is created for it, and nothing in § blocks "
                    "changes."),
                "what_would_settle_it": (
                    "The recorded plat of Kinzie's Addition itself (Cook County, "
                    "surveyed 1833), which is the only record that can say what the "
                    "surveyor numbered rather than what the draughtsman drew. The "
                    "newspaper half of this test is spent: § the_documentary_test is "
                    "re-run by the gate, so a Democrat issue added to the corpus that "
                    "names a block of the Addition will reopen it by failing this "
                    "file."),
            },
        ],
        "blocks": blocks,
    }


# ---------------------------------------------------------------------------
# The assertions. Each returns a list of failures so `--self-test` can break one
# input at a time and watch exactly one of them fire.

def assertions(doc: dict) -> list[str]:
    bad: list[str] = []
    blocks = doc["blocks"]
    numbers = [b["number"] for b in blocks]
    cells = [b["cell"] for b in blocks]
    w, h = doc["reading"]["raster_px"]

    if len(blocks) != 52:
        bad.append(f"the Addition's grid holds 52 cells and this reading has {len(blocks)}")
    if sorted(numbers) != list(range(3, 55)):
        missing = [n for n in range(3, 55) if n not in set(numbers)]
        twice = sorted({n for n in numbers if numbers.count(n) > 1})
        bad.append(f"the run 3-54 is not closed: missing {missing}, used twice {twice}")
    if len(set(cells)) != len(cells):
        bad.append("two numbers stand in one cell")
    if any(b["number"] in (1, 2) for b in blocks):
        bad.append("blocks 1 and 2 are refused, not placed — one of them has been "
                   "counted onto a cell")

    for b in blocks:
        x0, y0, x1, y1 = b["numeral_crop_px"]
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h or x1 <= x0 or y1 <= y0:
            bad.append(f"block {b['number']}'s crop {b['numeral_crop_px']} is not a box "
                       f"inside the {w}x{h} raster")

    # The scheme, applied independently of the reading table.
    derived = boustrophedon()
    by_cell = {(b["column"], b["tier"]): b for b in blocks}
    for key, expected in derived.items():
        got = by_cell.get(key)
        if got is None:
            bad.append(f"the run puts {expected} in c{key[0]}r{key[1]} and the reading "
                       "has no block there")
        elif got["number"] != expected:
            bad.append(f"c{key[0]}r{key[1]}: the run derives {expected} and the reading "
                       f"has {got['number']}")
    if sum(1 for b in blocks if b["derives_from_scheme"]) != len(blocks):
        bad.append("`derives_from_scheme` no longer marks every cell — the run and the "
                   "ink have stopped agreeing somewhere and the file is not saying where")

    read = [b for b in blocks if b["numeral_on_sheet"]]
    if len(read) != 51:
        bad.append(f"51 figures are written on the sheet and this reading has {len(read)}")
    for b in blocks:
        if not b["numeral_on_sheet"] and "note" not in b:
            bad.append(f"block {b['number']} carries no figure and no note saying so")
        if b["confidence"] == "documented":
            bad.append(f"block {b['number']} is graded `documented` — reaching a cell "
                       "from a figure runs through this project's own georeference and "
                       "cannot be")
        if b["legibility"] != "clear" and "note" not in b:
            bad.append(f"block {b['number']} is graded `{b['legibility']}` and says "
                       "nothing about why")

    # The gore is what makes column 1 odd, and the file has to keep saying it is odd.
    gore = doc["grid"]["gore_width_px"]
    if not 15.0 <= gore <= 35.0:
        bad.append(f"column 1 measures {gore} px wide — it is the gore, and a gore that "
                   "has grown to a block's width means the west boundary has moved")
    if any(b["numeral_outside_cell"] != (b["column"] == 1) for b in blocks):
        bad.append("`numeral_outside_cell` no longer marks exactly the gore's figures")
    if not doc["refused"]:
        bad.append("blocks 1 and 2 have stopped being refused in writing")
        return bad

    # T-1103. The identification of the two figures, and the corpus test that
    # leaves the refusal standing. Both are derived in build(); these say what
    # about them has to stay true.
    refusal = doc["refused"][0]
    ident = refusal.get("identified_2026_09_13")
    if not ident:
        bad.append("the refusal has stopped saying whose the two bold figures are")
    else:
        numbers = [f["number"] for f in ident["figures"]]
        if sorted(numbers) != [1, 2]:
            bad.append(f"the identification names blocks {sorted(numbers)} and it is "
                       "about the Original Town's 1 and 2")
        if any(f["plat"] == doc["plat"] for f in ident["figures"]):
            bad.append("the identification has put the two figures on THIS plat — which "
                       "is the reading the refusal exists to refuse")
        ux0, uy0, ux1, uy1 = ident["union_in_na_pixel_space"]
        sx0, sy0, sx1, sy1 = ident["the_span_t_1061_refused"]
        if ux1 < sx0 or ux0 > sx1 or uy1 < sy0 or uy0 > sy1:
            bad.append(f"the identified figures sit at {ident['union_in_na_pixel_space']} and the "
                       f"span T-1061 refused is {ident['the_span_t_1061_refused']} — "
                       "they no longer overlap, so this is identifying other ground")
        west = doc["grid"]["west_boundary_px_x"]
        river_tier_bottom = doc["grid"]["tier_bands_px_y"][-1][1]
        for f in ident["figures"]:
            x0, y0, x1, y1 = f["box_in_na_pixel_space"]
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            if cx >= west:
                bad.append(f"block {f['number']}'s figure is centred at x {cx:.0f}, "
                           f"inside the Addition's west boundary rule at x {west} — a "
                           "figure inside the boundary is the Addition's to explain")
            if cy <= river_tier_bottom:
                bad.append(f"block {f['number']}'s figure is centred at y {cy:.0f}, "
                           f"inside the river tier, which ends at y {river_tier_bottom} "
                           "— then the run's extrapolation did have somewhere to land")

    test = refusal.get("the_documentary_test")
    if not test:
        bad.append("the refusal has stopped carrying the corpus test that leaves it "
                   "standing")
    else:
        if test["claims_naming_the_addition"] < 1:
            bad.append("the corpus sweep found no claim naming Kinzie's Addition at all "
                       "— it is not reading the corpus")
        if not test["parcels_named_with_it"]:
            bad.append("the corpus sweep found no numbered parcel in the Addition, and "
                       "the finding it reports is that every one of them is a water lot")
        hit = sorted({b["block"] for b in test["block_numbers_in_the_same_claim"]
                      if b["block"] in (1, 2)})
        if hit:
            bad.append(f"a claim naming the Addition now names block {hit} — the "
                       "documentary test T-1061 asked for has been answered and this "
                       "refusal has to be reopened, not regenerated")
    if "ruling_2026_09_13" not in refusal:
        bad.append("the refusal has stopped stating what it rules — that the Addition's "
                   "numbering as drawn begins at 3")
    return bad


def check() -> int:
    fresh = build()
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing", file=sys.stderr)
        return 1
    bad = assertions(fresh)
    if load(OUT) != fresh:
        bad.append(f"{OUT.relative_to(ROOT)} is not what this tool re-derives — "
                   "regenerate it in the commit that changes the reading")
    if bad:
        for line in bad:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    read = sum(1 for b in fresh["blocks"] if b["numeral_on_sheet"])
    print(f"kinzie addition numerals: {len(fresh['blocks'])} cell(s), {read} figure(s) "
          f"read on the sheet, 1 named, {len(fresh['refused'])} refusal(s)")
    return 0


def _peaks(band, axis: int, offset: int, thr: float = 20.0) -> list[float]:
    import numpy as np
    prof = 255.0 - band.mean(axis=axis)
    base = np.convolve(prof, np.ones(61) / 61, mode="same")
    d = prof - base
    out, i = [], 0
    while i < len(d):
        if d[i] > thr:
            j = i
            while j < len(d) and d[j] > thr:
                j += 1
            seg = d[i:j]
            out.append(offset + i + float((seg * np.arange(len(seg))).sum() / seg.sum()))
            i = j
        else:
            i += 1
    return out


def check_sheet() -> int:
    """Re-measure this tool's own two bounds off the raster."""
    import numpy as np
    from PIL import Image

    gcp = load(GCP)
    img = ROOT.parents[1] / gcp["raster"]["working_copy"]
    if not img.exists():
        print(f"FAIL: {img} is not in this checkout", file=sys.stderr)
        return 1
    im = np.asarray(Image.open(img).convert("L"), dtype=float)
    bad = []

    west = _peaks(im[1525:1600, 2840:3010], 0, 2840)
    near = [p for p in west if abs(p - WEST_BOUNDARY_PX_X) <= SHEET_TOL_PX]
    if not near:
        bad.append(f"no ruled line within {SHEET_TOL_PX} px of the committed west "
                   f"boundary {WEST_BOUNDARY_PX_X}; the window found {west}")

    tops = []
    for x0, x1 in ((2990, 3090), (3150, 3250)):
        tops += [p for p in _peaks(im[900:1200, x0:x1], 1, 900)
                 if abs(p - NORTH_BLOCK_TOP_PX_Y) <= SHEET_TOL_PX]
    if not tops:
        bad.append(f"no ruled line within {SHEET_TOL_PX} px of the committed north "
                   f"block top {NORTH_BLOCK_TOP_PX_Y}")

    if bad:
        for line in bad:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    print(f"kinzie addition numerals: both bounds re-measured on the sheet — west "
          f"boundary {near[0]:.1f}, north block top {sum(tops) / len(tops):.1f}")
    return 0


def self_test() -> int:
    base = build()
    if assertions(base):
        print("FAIL: the committed reading does not pass its own assertions",
              file=sys.stderr)
        for line in assertions(base):
            print(f"   {line}", file=sys.stderr)
        return 1

    def drop_a_cell(doc):
        doc["blocks"] = doc["blocks"][:-1]

    def repeat_a_number(doc):
        doc["blocks"][5]["number"] = doc["blocks"][4]["number"]

    def break_the_run(doc):
        for b in doc["blocks"]:
            if b["cell"] == "c3r5":
                b["number"] = 999

    def place_block_one(doc):
        doc["blocks"][0]["number"] = 1

    def move_a_crop_off_the_sheet(doc):
        doc["blocks"][0]["numeral_crop_px"] = [-40, 10, 20, 60]

    def promote_the_name_to_a_reading(doc):
        for b in doc["blocks"]:
            if not b["numeral_on_sheet"]:
                b["numeral_on_sheet"] = True
                break

    def lose_the_names_note(doc):
        for b in doc["blocks"]:
            if not b["numeral_on_sheet"]:
                b.pop("note", None)
                break

    def upgrade_a_grade(doc):
        doc["blocks"][0]["confidence"] = "documented"

    def silence_a_hard_read(doc):
        for b in doc["blocks"]:
            if b["legibility"] != "clear":
                b.pop("note", None)
                break

    def widen_the_gore(doc):
        doc["grid"]["gore_width_px"] = 120.0

    def move_the_gores_figures_inside(doc):
        doc["blocks"][0]["numeral_outside_cell"] = not doc["blocks"][0]["numeral_outside_cell"]

    def stop_refusing_one_and_two(doc):
        doc["refused"] = []

    def lose_the_identification(doc):
        doc["refused"][0].pop("identified_2026_09_13")

    def move_a_figure_inside_the_boundary(doc):
        f = doc["refused"][0]["identified_2026_09_13"]["figures"][0]
        f["box_in_na_pixel_space"] = [3000.0, 2141.0, 3100.0, 2351.0]

    def annex_a_figure_to_this_plat(doc):
        doc["refused"][0]["identified_2026_09_13"]["figures"][0]["plat"] = doc["plat"]

    def drift_off_the_refused_span(doc):
        doc["refused"][0]["identified_2026_09_13"]["union_in_na_pixel_space"] = [10.0, 10.0, 20.0,
                                                                    20.0]

    def find_block_one_in_the_corpus(doc):
        doc["refused"][0]["the_documentary_test"][
            "block_numbers_in_the_same_claim"].append(
                {"block": 1, "claim": "a notice nobody has read"})

    def lose_the_ruling(doc):
        doc["refused"][0].pop("ruling_2026_09_13")

    cases = [("a cell dropped from the reading", drop_a_cell),
             ("one number used twice", repeat_a_number),
             ("a cell that stops obeying the run", break_the_run),
             ("block 1 counted onto a cell", place_block_one),
             ("a crop box off the raster", move_a_crop_off_the_sheet),
             ("`Kinzie Block` promoted to a read figure", promote_the_name_to_a_reading),
             ("the named cell losing the note that says it is one", lose_the_names_note),
             ("a numeral graded `documented`", upgrade_a_grade),
             ("a hard read that stops saying it was hard", silence_a_hard_read),
             ("a gore that has grown to a block", widen_the_gore),
             ("the gore's figures claimed to sit inside their cell",
              move_the_gores_figures_inside),
             ("blocks 1 and 2 quietly stopping being refused", stop_refusing_one_and_two),
             ("the refusal forgetting whose the two figures are", lose_the_identification),
             ("a figure moved inside the Addition's boundary",
              move_a_figure_inside_the_boundary),
             ("a figure annexed to this plat", annex_a_figure_to_this_plat),
             ("the identification drifting off the ground T-1061 refused",
              drift_off_the_refused_span),
             ("a corpus notice turning up that names block 1 of the Addition",
              find_block_one_in_the_corpus),
             ("the refusal losing the ruling it states", lose_the_ruling)]

    failed = 0
    for name, break_it in cases:
        doc = json.loads(json.dumps(base))
        break_it(doc)
        if assertions(doc):
            print(f"   fires: {name}")
        else:
            print(f"   SILENT: {name}", file=sys.stderr)
            failed += 1
    if failed:
        return 1
    print(f"kinzie addition numerals self-test: {len(cases)} of {len(cases)} "
          "assertions fire when broken")
    return 0


def report(doc: dict) -> int:
    by_cell = {(b["column"], b["tier"]): b for b in doc["blocks"]}
    print("      " + "".join(f"c{c:<4d}" for c in range(1, doc["grid"]["columns"] + 1)))
    for row in range(1, doc["grid"]["tiers"] + 1):
        line = f"  r{row:<3d}"
        for col in range(1, doc["grid"]["columns"] + 1):
            b = by_cell.get((col, row))
            line += f"{b['number']:<5d}" if b else "  .  "
        print(line)
    print()
    for b in doc["blocks"]:
        if not b["numeral_on_sheet"]:
            print(f"  block {b['number']} ({b['cell']}) is written "
                  f"`{b['written_on_sheet']}`")
        elif b["legibility"] != "clear":
            print(f"  block {b['number']} ({b['cell']}) is {b['legibility']}, graded "
                  f"{b['confidence']}")
    for entry in doc["refused"]:
        print(f"  refused: {entry['scope']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.check_sheet:
        return check_sheet()
    if args.write:
        doc = build()
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['blocks'])} cell(s)")
        return 0
    return report(build())


if __name__ == "__main__":
    raise SystemExit(main())
