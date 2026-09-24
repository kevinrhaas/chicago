#!/usr/bin/env python3
"""Generate the platted block and lot grid from the module, not from a trace.

ROADMAP K7. The 1830 Thompson plat is a PARAMETER source in this dataset — no open
high-resolution scan of it exists and the surviving artifact is a Canal Commissioners'
working copy — so its geometry is generated analytically from the module it fixes
(80-ft streets, 18-ft alleys) and snapped to the street lines this project has already
committed. Tracing the 1834 sheets instead would bake their 3.7-4.5% anisotropic paper
stretch into every block face: the corridors those draughtsmen drew run about 5 ft wide
of 80 on both sheets, which is stretch and pen placement rather than a wider street.

What each part of the output is entitled to claim, and why:

* A **block boundary** is a street centreline offset by half the platted corridor. The
  centrelines are `data/streets/1835.json`, whose own geometry confidence is `inferred`,
  and the half-width is the module. Arithmetic on inferred inputs is inferred, so that is
  what the block edges carry.
* A **lot line** is `conjectural` and stays that way. Four lots to a block face is read
  off the owner's crop of Wright's sheet at the Clark reach — block 18's north row runs
  4 3 2 and its south row 5 6 7 (`docs/RESEARCH/clark_reach_bulge_1834.md` § 8) — and a
  reading of ONE block does not document the subdivision of the other seventeen. The
  alley is worse off: 18 ft is the module, but nothing in `data/sources/` says which
  blocks were alleyed or where the alley ran inside them.
* A block is emitted only where the committed centrelines of all four of its bounding
  streets actually REACH it. Extending a street line past where this project has drawn it
  would be an invention dressed as geometry, so those blocks are listed in `omitted` with
  the street that falls short — which is the same list as the street control still owed
  under ROADMAP § S9.

Thompson's block NUMBERS reach six blocks of this grid and no more. The owner's crop
carries two numerals side by side in the South Water tier — 19 west of 18, the stream in
the La Salle corridor between them — and that fixes the step (one per block) and the
direction (falling eastward) along a row. Counting along that row numbers the tier's six
blocks, and block 16 lands on Dearborn-State, where G. Spring's 'LOT No. 7, in block No.
16 ... on Lake street' and the Mansion House's own Andreas-and-Botsford placement already
agree it should. Nothing outside the tier is numbered: how the run passes from one row to
the next is not readable from two numerals in one row. The judgement, the identification
and the refusals live in `data/traces/thompson_block_numbering.json`; this module only
stamps them. Block ids stay named for the streets that bound them, which is a description
that never goes wrong.

    tools/generate_plat_lots.py            regenerate data/traces/vectors/thompson_lots.json
    tools/generate_plat_lots.py --check    fail if the committed file is not what the
                                           module and the street lines re-derive
    tools/generate_plat_lots.py --report   where the dataset's structures fall on the grid
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from exact_sums import consistent_reading  # noqa: E402  (same directory)
DATA = ROOT / "data"
OUT_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
SIDECARS = DATA / "sidecars" / "1835"

FT_M = 0.3048
ALLEY_FT = 18.0
LOT_FRONTAGE_FT = 80.0

# The plat's module pitch runs 116-143 m; every larger gap between two consecutive
# streets in this table is the river, not a block. Named rather than tuned: it is the
# rule that keeps a "block" from being generated across the South Branch.
MAX_PITCH_M = 200.0

# The lattice a block's ground is read on. 2.5 m is the heightfield's own cell and 5 m is
# two of them: fine enough that the smallest block on this grid still carries hundreds of
# samples, coarse enough that the reading costs nothing to re-derive on every commit.
GROUND_STEP_M = 5.0

# Ordered north to south, and west to east. Restricted to the South and West Division
# grid on purpose: these are the streets a BLOCK may be generated between, and a block
# generated between two lines that are not yet fixed would look exactly like one that is.
# The north-side streets are NOT here and T-1194 is the ticket that would add them: the
# plat draws seven numbered blocks in the North Division and one of them, block 6, is
# drawn across the slough (T-0452 § 4).
EW_STREETS = ["south_water", "lake", "randolph", "washington"]
NS_STREETS = ["clinton", "canal", "market", "franklin", "wells", "lasalle", "clark",
              "dearborn", "state"]

# --------------------------------------------------------------- the corridor layer
#
# T-1191. A CORRIDOR IS NOT A BLOCK, and until 2026-09-19 this file could not say so:
# one pair of lists decided both which streets a block may be cut between AND which
# streets a building may be reported standing in, so the north bank had neither. That
# is why `plat_corridors.corridors()` returned nothing north of the river and why the
# comment above used to give the block rule as the reason for the corridor gap.
#
# The two questions have different evidence bars. Cutting a block needs BOTH bounding
# lines fixed and the ground between them read. Asking whether a point is in a platted
# roadway needs only that one street's own corridor be read off a sheet — which the
# north bank's are, and have been since T-0451 and T-1060:
#
#   * the Thompson North Division tier — the plat letters the figure 80 at the head of
#     every one of its six corridors, on the Kinzie line, and nothing else
#     (`data/traces/thompson_north_division_streets.json` § lettering); the same sheet's
#     own fit returns an 80 ft corridor as 45.6 px = 24.4 m against the platted 24.384
#     (`docs/RESEARCH/north_division_streets.md` § 3);
#   * Kinzie's Addition — 22.17 m, read corridor by corridor off Wright's 1834 survey
#     and scaled against the Original Town's corridors on the same sheet
#     (`data/traces/kinzie_addition_street_grid.json` § control_summary).
#
# Each record carries its own `corridor_width_m` and this module uses it, because the
# Addition's corridor is 2.2 m narrower than the Original Town's and one town-wide
# half-width would have drawn the Addition's roadways over its own lot lines.
#
# NORTH WATER STREET IS DELIBERATELY NOT IN THE LAYER, and neither is Wabansia, and
# the control file says so in its own `not_in_the_corridor_layer` block with the
# reason per street. The short of it: North Water's line is cut from the river bank
# rather than from a platted rule, so offsetting it by half a module would invent a
# rectangle no sheet draws; Wabansia and the West Division are T-1192's ground.
def _north_bank_axes() -> tuple[list[str], list[str]]:
    """The north-bank corridor streets, by axis, READ OUT OF THE CONTROL FILE.

    No street id is written here, which is the same principle
    `plat_corridors.control_offsets` states for its refusals: a street acquires or
    loses a corridor by what the control says, not by being named in a tool. The
    tiers, their sheets, their widths, the streets excluded and why, and the alley
    finding are all in `data/traces/street_control.json` § `north_bank`.
    """
    # json directly rather than `load`, which this module defines further down: the
    # constants below are module-level because `plat_corridors` imports them as such.
    control = json.loads((DATA / "traces" / "street_control.json").read_text(
        encoding="utf-8"))
    ew: list[str] = []
    ns: list[str] = []
    for tier in (control.get("north_bank") or {}).get("tiers", {}).values():
        ew += list(tier.get("axis", {}).get("ew") or [])
        ns += list(tier.get("axis", {}).get("ns") or [])
    return ew, ns


NORTH_EW_STREETS, NORTH_NS_STREETS = _north_bank_axes()


def _addition_axes() -> tuple[list[str], list[str]]:
    """Kinzie's Addition's BLOCK grid, by axis, READ OUT OF THE COMMITTED FILES.

    T-1437. The Addition's own eleven streets come from the same corridor control
    `_north_bank_axes` reads. The two lines that close its grid on the south and the
    west are not the Addition's — they are the Original Town's `michigan_north` and
    `wolcott` — and they are read here from the Addition's own SEATING block, which is
    the file that says which committed lines the sheet's module was hung on. No street
    id is written in this module, for the reason stated above: a street joins or leaves
    a grid by what the committed control says, not by being named in a tool.
    """
    control = json.loads((DATA / "traces" / "street_control.json").read_text(
        encoding="utf-8"))
    tier = (control.get("north_bank") or {}).get("tiers", {}).get("kinzies_addition") or {}
    axis = tier.get("axis") or {}
    seating = json.loads((DATA / "traces" / "kinzie_addition_street_grid.json").read_text(
        encoding="utf-8"))["seating"]
    # The seating block names each datum as "<street id> in data/streets/1835.json";
    # the id is the first token and the rest is the file it says to look in.
    ew_datum = str(seating["east_west_datum"]).split()[0]
    ns_datum = str(seating["north_south_datum"]).split()[0]
    return ([ew_datum] + list(axis.get("ew") or []),
            [ns_datum] + list(axis.get("ns") or []))


ADDITION_EW_STREETS, ADDITION_NS_STREETS = _addition_axes()


# The sheet spells it Des Pleins and this project's street table spells it des_plaines.
# One entry, written down rather than normalised by a rule, because a rule that rewrites
# street names would quietly reconcile two streets that are genuinely different.
WEST_TRACE_SPELLING = {"des_pleins": "des_plaines"}


def _west_tier_line(name: str) -> str | None:
    """The committed street id a West Division tier name stands for, or None.

    The tiers of `thompson_west_division_lots.json` are named for the two lines they
    lie between — "Lake - Randolph", "Washington - south town line". Four of the six
    names on each side are streets this project commits; the town lines are not streets
    at all and this project holds no line for either, so they return None and the tiers
    that lean on them are carried in `omitted` rather than cut against a line nobody
    has drawn.
    """
    key = name.strip().lower()
    if key.endswith("town line"):
        return None
    return WEST_TRACE_SPELLING.get(key.replace(" ", "_"), key.replace(" ", "_"))


def _west_division_axes() -> tuple[list[str], list[str]]:
    """The West Division's own tier and column lines, READ OUT OF THE COMMITTED TRACE.

    T-1455. No street id is written here, for the reason `_north_bank_axes` states: a
    street joins or leaves a grid by what the committed files say. Every column comes
    from a block entry's own `bounded_west_by`/`bounded_east_by` and every row from its
    `tier`, so the grid is exactly as wide as the sheet reading is and no wider. The
    river appears in that table as a bound ("south branch of the Chicago River") and is
    dropped here: it is not a street and this grid cuts cells between street lines.
    """
    doc = json.loads(WEST_DIVISION_PATH.read_text(encoding="utf-8"))
    columns, rows = set(), set()
    for entry in doc["blocks"]:
        for side in ("bounded_west_by", "bounded_east_by"):
            name = str(entry[side]).strip().lower()
            if " " in name:      # the river, written out in words
                continue
            columns.add(WEST_TRACE_SPELLING.get(name, name))
        for part in str(entry["tier"]).split(" - "):
            line = _west_tier_line(part)
            if line:
                rows.add(line)
    return sorted(rows), sorted(columns)


def grids() -> list[dict]:
    """The platted grids a block may be cut inside, and what each one may be divided on.

    ONE PAIR OF STREET LISTS PER PLAT. Until T-1437 there was one pair for the whole
    town, which is why the only lots in this file stop at the river: a block could be
    cut only between two Original Town lines. A block may still be cut only between two
    lines of ONE plat — the modules differ, the corridors differ (22.17 m against
    24.384), and a cell straddling two sheets is not a cell either sheet draws.

    `subdivides` is the second half of the same discipline. The Original Town's
    four-to-a-face module is a reading of an Original Town block; nothing in
    `data/traces/kinzie_addition_street_grid.json` reads a lot rule for the Addition,
    which measures a tier pitch and a column pitch and stops. So the Addition's blocks
    are built and NOT divided, and each one says so on itself.

    AND A THIRD PAIR SINCE T-1455, on the same sheet as the first. The West Division is
    not a different plat — Thompson drew it — but it is a different BLOCK: two columns
    of lots backing onto a north-south alley, five rows of 75 3/5 ft, against the
    Original Town's four-to-a-face with an east-west one. Cutting it inside the Original
    Town's pair is what produced the two blocks that stand in this file today carrying
    South Division lots and a `west_division_module_refused` note beside them, because
    one pair of lists cannot hold two arrangements. Its lines are read out of
    `data/traces/thompson_west_division_lots.json` by `_west_division_axes`, so the grid
    is exactly as wide as that reading and no wider.

    Read at call time rather than frozen at import: `tools/measure_southern_ground.py`
    widens `EW_STREETS` for the length of one measurement and a list captured at import
    would not see it.
    """
    west_rows, west_columns = _west_division_axes()
    return [
        {
            "id": "original_town",
            "plat": "thompson_plat_1830",
            "name": "the Original Town of Chicago, Thompson 1830",
            "rows": list(EW_STREETS),
            "columns": list(NS_STREETS),
            "subdivides": True,
            "divides_on": "the South Division module, four lots to a face",
        },
        {
            "id": "kinzies_addition",
            "plat": "kinzie_addition",
            "name": "Kinzie's Addition, Wright 1834",
            "rows": list(ADDITION_EW_STREETS),
            "columns": list(ADDITION_NS_STREETS),
            "subdivides": False,
            "divides_on": None,
        },
        {
            "id": "west_division",
            "plat": "thompson_plat_1830",
            "name": "the West Division, Thompson 1830",
            "rows": west_rows,
            "columns": west_columns,
            "subdivides": True,
            "divides_on": ("each block's OWN printed frontage or depth, with the "
                           "arrangement and the lot numerals read off the sheet "
                           "block by block — and no lots at all where the block "
                           "prints neither figure"),
        },
    ]

# What `corridor_rings` covers, and therefore what `plat_corridors.intrusion` can
# report. A superset of the block lists above, never a substitute for them.
CORRIDOR_EW = EW_STREETS + NORTH_EW_STREETS
CORRIDOR_NS = NS_STREETS + NORTH_NS_STREETS

SOURCE_IDS = ["thompson_plat_1830", "hathaway_1834", "wright_1834", "osm_streets_2026"]

RESERVED_PATH = DATA / "reconstruction" / "1835_reserved_ground.json"
NUMBERING_PATH = DATA / "traces" / "thompson_block_numbering.json"
TRACTS_PATH = DATA / "reconstruction" / "1835_survey_tracts.json"
WEST_DIVISION_PATH = DATA / "traces" / "thompson_west_division_lots.json"

# T-1104's precedence clause, carried here rather than re-invented, because the layer is
# not a partition: a tract whose ring is defined as what another tract leaves over yields
# any block a non-residual tract covers at least half of. Named, not inferred from the
# grade — `canal_section_9_remainder`'s own `boundary_from` says it is the residual.
RESIDUAL_TRACTS = {"canal_section_9_remainder"}
MAJORITY = 0.50
# Below this an overlap is the clip's own rounding, not a statement that a block is on a
# tract. 1 m2 against blocks of 10,000 m2 and up.
TOUCH_M2 = 1.0


def block_numbering() -> dict:
    """Thompson's own block numbers, for the blocks this project can reach them.

    Authored in `data/traces/thompson_block_numbering.json` and read here, the same
    shape as `reserved_blocks()`: the file carries a reading and a judgement, this
    module carries none, and the numbers land on blocks whose geometry is derived
    exactly as it was before. T-0358.

    The numerals are read off the georeferenced BPL scan of Wright's 1834 sheet, one
    crop per block, cut from that block's own committed street lines — so which block
    carries a numeral is settled by the fit and not by counting from a neighbour. The
    run turns out to REVERSE tier by tier (South Water falls eastward, Lake rises,
    Randolph falls), which is why the earlier reading was right to refuse to count
    across a tier. Blocks outside the reach of the committed grid stay unnumbered.
    """
    doc = load(NUMBERING_PATH)
    return {b["block_id"]: b for b in doc["blocks"]}, doc


ADDITION_NUMBERING_PATH = DATA / "traces" / "kinzie_addition_block_numbering.json"


def addition_numbering(rows: list[str], columns: list[str], lines: dict):
    """Kinzie's Addition's block numbers, turned into this grid's block ids.

    Authored in `data/traces/kinzie_addition_block_numbering.json` and read here, the
    same way `block_numbering()` reads the Original Town's: the file carries the
    reading and the judgement, this module carries neither.

    A cell is named there by its COLUMN and its TIER, and both are turned into streets
    without a street id being typed:

    * the column is `column_name` — `wolcott_cass`, `cass_rush`, `rush_pine`,
      `pine_sand` — whose two halves ARE the ids of the lines the cell stands between.
      `west_gore` and `east_of_sand` name no second line, because there is none: the
      Addition's west boundary rule and the lake shore are not streets;
    * the tier is numbered from the river upward under the file's own `scheme` — *"West
      to east along the river tier (3-7) ... turning at every tier and climbing to the
      Superior tier (50-54)"*. Tier 9 is therefore the ground SOUTH of the southernmost
      committed east-west line and tier 1 the ground north of the northernmost, and
      neither has a committed line on its outer side.

    Returns the numbers this grid can reach, keyed by block id, and the cells it cannot,
    which are carried on the omissions so that all fifty-two are accounted for.
    """
    doc = load(ADDITION_NUMBERING_PATH)
    south_to_north = sorted(rows, key=lambda s: lines[s]["mean_n"])
    ordered_columns = sorted(columns, key=lambda s: lines[s]["mean_e"])
    top = len(south_to_north)

    by_id, unreachable = {}, []
    for record in doc["blocks"]:
        # tier `t` stands between south_to_north[top - t] and south_to_north[top - t + 1]
        south_index = top - int(record["tier"])
        north_index = south_index + 1
        north = south_to_north[north_index] if 0 <= north_index < top else None
        south = south_to_north[south_index] if 0 <= south_index < top else None
        pair = str(record["column_name"]).split("_")
        west, east = (pair + [None, None])[:2]
        if west not in ordered_columns or east not in ordered_columns:
            west = east = None
        if north is None or south is None or west is None:
            unreachable.append((record, north, south, record["column_name"]))
            continue
        by_id[f"blk_{north}_{west}"] = record
    return by_id, unreachable, doc


def ground_reading(ring: list, field) -> dict:
    """What the committed heightfield says about the ground inside a block.

    T-1437 acceptance 5, and the parent's *"buildable reading ... wet, sloping or in a
    water lot recorded, not silently skipped"*. The lattice is cut from the ring's own
    bounding box snapped to the step, so the reading is a property of the block and not
    of the order the generator happened to build it in.

    THE MEAN IS SUMMED EXACTLY, and the three figures are asserted against each other.
    `sum()` accumulates left to right and drifts by a few parts in 10^15, which is
    nothing on a height until the true value sits on a rounding boundary. The School
    Section's blocks 95, 118 and 119 are each perfectly flat at 0.885 m: `min` and `max`
    round that up to 0.89, while the drifted mean of 418 identical samples landed
    0.8849999999999949 and rounded DOWN to 0.88 — a record printing a mean outside its
    own min and max. Which of the two a machine printed turned out to depend on the
    INTERPRETER, not on the data (measured under T-1486): CPython 3.12 gave `sum()`
    Neumaier compensation for floats and agrees with `math.fsum` on these samples, while
    the 3.11 this project's CI pins does not — so a re-derivation looked correct where it
    ran and stale where it did not. `math.fsum` is correctly rounded and order-independent
    on every version, so the same block reads the same on every machine; the shared
    refusal in tools/exact_sums.py then declines a reading that is arithmetically
    impossible rather than committing one, and tools/check_exact_sums.py mutation-tests
    that refusal by restoring the uncompensated sum and watching it fire.
    """
    es = [p[0] for p in ring]
    ns = [p[1] for p in ring]
    step = GROUND_STEP_M
    heights, below, off = [], 0, 0
    e = math.floor(min(es) / step) * step
    while e <= max(es):
        n = math.floor(min(ns) / step) * step
        while n <= max(ns):
            if point_in_polygon((e, n), ring):
                if not field.covers(e, n):
                    off += 1
                else:
                    height = field.height(e, n)
                    heights.append(height)
                    if height < 0.0:
                        below += 1
            n += step
        e += step
    reading = {
        "epoch": "e1834_harbor_cut",
        "sampled_every_m": step,
        "samples": len(heights) + off,
        "off_the_modelled_field": off,
        "below_datum": below,
    }
    if heights:
        lo, mean, hi = consistent_reading(heights, 2, label="ground reading (m)")
        reading["min_m"], reading["max_m"], reading["mean_m"] = lo, hi, mean
    reading["reading"] = (
        "dry: every sample stands above datum on the modelled field"
        if heights and not below and not off else
        f"{below} sample(s) below datum and {off} off the modelled field")
    return reading


def reserved_blocks() -> dict[str, dict]:
    """Blocks this project holds evidence were not private building ground.

    The module knows how to subdivide a block and has no way to ask whether the block
    was ever offered in lots. Four lots to a face is the plat's rule for ground for
    sale; drawing it on ground the town held in common asserts a sale that never
    happened, and the 665-roof programme reads the result as somewhere to build.
    So a reserved block keeps its BOUNDARY — which is derived from the street lines
    like every other block's and is not in question — and loses its SUBDIVISION.
    """
    if not RESERVED_PATH.exists():
        return {}
    return {b["block_id"]: b for b in load(RESERVED_PATH)["blocks"]}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------- the survey tract under a block


def survey_tracts() -> list[dict]:
    """The placed rings of `data/reconstruction/1835_survey_tracts.json`, and nothing else.

    T-1101 built the layer that says WHO SURVEYED WHAT GROUND. Until it existed this
    module had no way to ask which survey a block stood in, so it chose one street width
    and one block module for the whole town and said so nowhere. It can ask now. Reading
    the layer is not the same as obeying it — what the answer is worth is decided in
    `module_for`, on the arithmetic, and both are written onto every block.
    """
    doc = load(TRACTS_PATH)
    return [{
        "id": t["id"],
        "ring": [(float(e), float(n)) for e, n in t["polygon_local_enu_m"]],
        "geometry_confidence": t["geometry_confidence"],
        "residual": t["id"] in RESIDUAL_TRACTS,
    } for t in doc["tracts"] if t.get("placed") and t.get("polygon_local_enu_m")]


def tract_of(ring: list, tracts: list[dict]) -> dict:
    """Which survey tract a block stands in, under T-1104's precedence clause.

    The clipper is imported from `tools/sort_land_sales_onto_tracts.py` rather than
    written again: two implementations of the same overlap would be two answers to the
    same question, and that file's `--self-test` already holds this one to six
    constructed cases.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    from sort_land_sales_onto_tracts import overlap_area  # noqa: PLC0415

    area = polygon_area(ring)
    shares = []
    for tract in tracts:
        overlap = overlap_area(ring, tract["ring"])
        if overlap > TOUCH_M2:
            shares.append({"tract": tract["id"], "share": round(overlap / area, 4),
                           "residual": tract["residual"],
                           "geometry_confidence": tract["geometry_confidence"]})
    if not shares:
        return {"tract": None, "share": 0.0, "on": [],
                "why": "no placed tract ring in the layer covers this block"}
    shares.sort(key=lambda s: -s["share"])
    best = shares[0]
    clause = None
    if best["residual"]:
        outright = [s for s in shares[1:]
                    if not s["residual"] and s["share"] >= MAJORITY]
        if outright:
            best = outright[0]
            clause = ("the residual yielded: a non-residual tract covers this block by "
                      f"{best['share']:.0%} and canal_section_9_remainder is the layer's "
                      "only residual ring")
    return {
        "tract": best["tract"],
        "share": best["share"],
        "geometry_confidence": best["geometry_confidence"],
        "on": [s["tract"] for s in shares],
        "precedence_clause_fired": clause,
    }


# ------------------------------------------------------ the module under a block


def west_division() -> dict:
    """The West Division's own module, as the Thompson sheet PRINTS it (T-0689).

    Two columns of 180-ft lots backing onto a north-south alley, five 75 3/5-ft lots to
    a column, and the block square at 378 ft — a different ARRANGEMENT from the South
    Division's four-to-a-face with an east-west alley, not just a different frontage.
    The street set is taken from the block table's own `bounded_*_by` fields, so which
    streets are West Division streets is read off that file too and not asserted here.
    """
    doc = load(WEST_DIVISION_PATH)
    streets = set()
    for entry in doc["blocks"]:
        streets.add(entry["bounded_west_by"])
        streets.add(entry["bounded_east_by"])
    figures = doc["the_west_division_block"]
    return {
        "streets": {s for s in streets if s.replace("_", "").isalpha()},
        "lot_frontage_ft": float(figures["lot_frontage_ft"]),
        "lot_depth_ft": float(figures["lot_depth_ft"]),
        "alley_width_ft": float(figures["alley_width_ft"]),
        "block_east_west_ft": float(figures["block_east_west_ft"]),
        "block_north_south_ft": float(figures["block_north_south_ft_five_row_tiers"]),
        "street_module_ft": float(figures["north_south_street_module_ft"]),
        "confidence": figures["confidence"],
        "printed_frontage": figures["lot_frontage_as_printed"],
        "authored_in": "data/traces/thompson_west_division_lots.json",
    }


def west_number_record(record: dict) -> dict:
    """The sheet's block numeral, carried onto a cell with the grade the reading holds.

    `documented` where the entry states it and `documented` where it does not, and the
    difference is recorded rather than smoothed. The per-entry `confidence` field in the
    authored file grades that entry's FIGURES — block 22 says so in its own words — so
    the eleven entries that print no figure state none. What every one of the twenty-two
    does carry is a numeral counted in its own cited crop (`counts.blocks_read` is 22 and
    `lots_read` is 203), which is the same kind of reading and takes the same grade. The
    field that says which of the two applies travels with the number.
    """
    stated = record.get("confidence")
    return {
        "number": record["plat_block_number"],
        "confidence": stated or "documented",
        "confidence_stated_on_the_entry": bool(stated),
        "graded_by": (
            "the entry's own `confidence`" if stated else
            "the file's reading rule — this entry states no confidence because it prints "
            "no dimension to grade, and the grade here is of the NUMERAL, counted in the "
            f"crop the entry cites at {record.get('region')}"),
        "numeral_on_sheet": True,
        "lot_numerals_read": record["lot_count"],
        "sources": ["thompson_plat_1830"],
        "authored_in": "data/traces/thompson_west_division_lots.json",
        "note": record.get("note") or f"block of the {record['tier']} tier",
    }


def west_division_table() -> tuple[dict, dict]:
    """The sheet's West Division blocks, keyed by the four lines that bound each one.

    T-1455. `west_division()` above reads the tract-wide figures — the module the plat
    PRINTS once and lets a whole division inherit. This reads the other half of the same
    file: the twenty-two block entries, each with its own numerals, its own lot count,
    and its own dimension figures or its own refusal of them. The key is the four
    committed street ids, so a cell of the grid finds its record by the lines it stands
    between and never by counting along a row.

    A bound written out in words is the river, not a street; it is carried as None so
    that the cell it closes is refused by the grid rather than matched to a line.
    """
    doc = load(WEST_DIVISION_PATH)

    def line(name: str) -> str | None:
        key = str(name).strip().lower()
        if " " in key:
            return None
        return WEST_TRACE_SPELLING.get(key, key)

    table = {}
    for entry in doc["blocks"]:
        north, south = (_west_tier_line(part) for part in str(entry["tier"]).split(" - "))
        table[(north, south, line(entry["bounded_west_by"]),
               line(entry["bounded_east_by"]))] = entry
    return table, doc


def west_lot_figure(record: dict) -> dict | None:
    """The block's OWN printed dimension, or None if it prints none that resolves.

    This is the whole gate T-1455 asks for. Fourteen of the twenty-two blocks print no
    dimension at all — a draughtsman dimensions the first block of a tier and lets the
    rest inherit — and five more print a figure the committed scan cannot resolve to a
    digit. The authored file has already made both judgements, block by block, and
    records the crops it tried; this function does not re-make them. It reads the two
    fields that file sets to a number only when a number was read, and where both are
    null the block gets no lots.

    Two blocks print TWO depths rather than one (44 at 180 and 150, 51 at 180 and 88 —
    the South Branch eating into the east column) and the authored file deliberately
    leaves `lot_depth_ft` null on both rather than average them. They fall here with the
    fourteen, which is the file's own refusal honoured rather than worked around.
    """
    if record.get("lot_frontage_ft") is not None:
        return {"figure": "lot_frontage_ft", "ft": float(record["lot_frontage_ft"]),
                "printed": record.get("frontage_figures_read"),
                "region": record.get("frontage_region"),
                "governs": "the north-south frontage of a lot, and so the row pitch"}
    if record.get("lot_depth_ft") is not None:
        return {"figure": "lot_depth_ft", "ft": float(record["lot_depth_ft"]),
                "printed": record.get("depth_figures_read"),
                "region": record.get("depth_region"),
                "governs": "the east-west depth of a lot, and so the two columns and the alley"}
    return None


def subdivide_west(block: dict, alley_m: float, rows: int) -> dict:
    """The West Division block: two columns of lots backing onto a NORTH-SOUTH alley.

    The transpose of `subdivide`, and a separate function rather than a flag on it,
    because the two arrangements share no line: this one's alley runs with the block's
    north-south axis and its lots front the north-south streets on either side, where
    the South Division's runs across and its lots front the east-west streets.

    What comes from the sheet and what comes from the committed lines is worth keeping
    straight. THE ARRANGEMENT and THE COUNT are read — two columns, `rows` rows, the
    numerals counted in the block itself. THE POSITIONS are the committed street lines
    divided, exactly as they are for every other lot in this file, and they carry the
    same `conjectural` grade. The printed dimension is not seated at its printed size
    and this function does not pretend to: the closure between the two is computed by
    the caller and carried on the block, so a reader sees by how much the ground this
    project holds falls short of the ground the draughtsman wrote down.
    """
    north_chain, south_chain = block["north_chain"], block["south_chain"]
    face = (chain_length(north_chain) + chain_length(south_chain)) / 2.0
    # The alley is centred on the block's east-west face, so each column takes half of
    # what is left of that face. In `u` — the fraction along the chains, west to east.
    half = alley_m / (2.0 * face) if face else 0.0
    edges_u = [(0.0, 0.5 - half), (0.5 + half, 1.0)]

    def point(u: float, v: float) -> tuple:
        top = resample(north_chain, u)
        bottom = resample(south_chain, u)
        return (top[0] + (bottom[0] - top[0]) * v, top[1] + (bottom[1] - top[1]) * v)

    lots = []
    for column, (u0, u1) in zip(("west", "east"), edges_u):
        for index in range(rows):
            v0, v1 = index / rows, (index + 1) / rows
            ring = [point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)]
            lots.append({
                "tier": column,
                "column": column,
                "row": index + 1,
                "frontage_m": round((math.dist(ring[0], ring[3])
                                     + math.dist(ring[1], ring[2])) / 2.0, 2),
                "depth_m": round((math.dist(ring[0], ring[1])
                                  + math.dist(ring[3], ring[2])) / 2.0, 2),
                "polygon": rounded(ring),
            })
    alley = rounded([point(edges_u[0][1], 0.0), point(edges_u[1][0], 0.0),
                     point(edges_u[1][0], 1.0), point(edges_u[0][1], 1.0)])
    return {"lots": lots, "alley": alley, "frontage_m": face, "count": rows}


def stamp_west_numbers(entry: dict, record: dict) -> None:
    """The sheet's own block numeral, and its own lot numerals, onto a cut cell.

    A third sibling of `stamp_number`, and for the third time not the same function:
    these lot numbers are READ rather than schemed. `lot_numerals_north_to_south` is the
    block's numerals row by row from the north, west numeral first — block 26 runs
    2|1, 3|4, 6|5, 7|8, 10|9 — so a lot's number comes off the sheet at its own position
    and nothing is counted from a neighbour. Where the reading and the cut disagree on
    how many lots there are, none is numbered and the disagreement is stated.
    """
    entry["plat_block_number"] = west_number_record(record)
    numerals = record["lot_numerals_north_to_south"]
    lots = entry.get("lots") or []
    if not lots:
        return
    if len(lots) != sum(len(row) for row in numerals) or any(len(r) != 2 for r in numerals):
        entry["plat_block_number"]["lots_not_numbered"] = (
            f"the sheet reads {sum(len(r) for r in numerals)} numeral(s) in this block "
            f"and the cut gives {len(lots)} lot(s); a numeral moved to make the two "
            "agree is an invention")
        return
    for lot in lots:
        row = numerals[lot["row"] - 1]
        lot["plat_lot_number"] = row[0] if lot["column"] == "west" else row[1]
        # The NUMERAL is documented — it is ink in this block, counted at its own
        # position. The LINE it numbers is not, and keeps the grade every lot line in
        # this file carries.
        lot["plat_lot_confidence"] = "documented"
        lot["plat_lot_numeral_read_in"] = "data/traces/thompson_west_division_lots.json"


def addition_module() -> dict:
    """Kinzie's Addition's own module, as Wright's sheet MEASURES it (T-1060, T-1437).

    A tier pitch, a column pitch and a corridor, and no lot rule — which is the whole
    reason the Addition's blocks are built and not divided. The figures are read from
    the committed street grid rather than restated here.
    """
    doc = load(DATA / "traces" / "kinzie_addition_street_grid.json")
    control = json.loads((DATA / "traces" / "street_control.json").read_text(
        encoding="utf-8"))["north_bank"]["tiers"]["kinzies_addition"]
    return {
        "module": "kinzies_addition_wright_1834",
        "authored_in": "data/traces/kinzie_addition_street_grid.json",
        "tier_pitch_m": doc["module"]["tier_pitch_m"]["mean"],
        "column_pitch_m": doc["module"]["column_pitch_m"]["mean"],
        "corridor_m": control["corridor_m"],
        "corridor_confidence": control["confidence"],
        "seated_on": [str(doc["seating"]["east_west_datum"]).split()[0],
                      str(doc["seating"]["north_south_datum"]).split()[0]],
        "seated_on_note": ("the Addition's module is hung on the two committed lines it "
                           "shares with the town it adjoins, not on this sheet's own fit "
                           "— read straight through that fit Michigan Street lands "
                           "19.8 m south of `michigan_north`, which is the same street"),
        "division": "north",
        "chosen_by": ("the Addition's own measured module, seated on the two committed "
                      "lines it shares with the town it adjoins"),
        "lot_subdivision_withheld": {
            "why": ("NO LOT RULE HAS BEEN READ FOR THIS PLAT. The Addition's street grid "
                    "measures a tier pitch and a column pitch and stops there; the "
                    "four-to-a-face 80 ft module this generator can seat is a reading of "
                    "ONE Original Town block (docs/RESEARCH/clark_reach_bulge_1834.md "
                    "section 8) and carrying it across the river would be a guess dressed "
                    "as arithmetic. The parent ticket asks for the lots of each plat to "
                    "come from that plat's own module, and this one's has not been read."),
            "what_would_settle_it": ("the lot lines and lot numerals Wright draws inside "
                                     "the Addition's cells, read off wright_1834_nara_hup "
                                     "the way tools/read_kinzie_addition_numerals.py reads "
                                     "the block numerals — the same raster, the same "
                                     "registration, one crop per cell"),
            "meanwhile": ("the block stands with its boundary, its numeral and its ground, "
                          "which is what a placement ticket needs to name it"),
        },
    }


def west_module_for(entry: dict, record: dict, figure: dict | None, west: dict) -> dict:
    """The module a West Division block is cut on, and the closure against the sheet.

    T-1455. `module_for` REFUSES this arrangement for the two West Division blocks the
    Original Town's grid reaches, and that refusal is about seating the printed module
    AT ITS PRINTED SIZE: 180 + 18 + 180 needs 378 ft of face and the committed lines do
    not give it. This grid does something different and says so here. It cuts the
    printed ARRANGEMENT and the counted ROWS into the block the committed lines do give,
    which is exactly what every other lot line in this file is, and then reports by how
    much that block falls short of the figure the draughtsman wrote. Neither the module
    nor the lines are bent to meet; the gap between them is published instead.
    """
    taken = {
        "module": "west_division_thompson_1830",
        "authored_in": west["authored_in"],
        "confidence_of_the_figures": west["confidence"],
        "division": "west",
        "arrangement": (
            f"two columns of lots backing onto an {west['alley_width_ft']:.0f} ft "
            "NORTH-SOUTH alley, each lot fronting the north-south street on the outer "
            "side of its column"),
        "rows_read": len(record["lot_numerals_north_to_south"]),
        "lots_read": record["lot_count"],
        "chosen_by": ("this block's own entry on the sheet reading — its numerals, its "
                      "row count and its own dimension figure"),
    }
    if figure is None:
        taken["lot_subdivision_withheld"] = {
            "why": ("THIS BLOCK PRINTS NO DIMENSION THAT RESOLVES. The sheet dimensions "
                    "the first block of a tier and lets the rest of the tier inherit, so "
                    "fourteen of the twenty-two carry no figure at all and five more "
                    "carry one the committed scan cannot resolve to a digit. Inheriting "
                    "a tier-mate's figure is the one move `what_this_refutes` in the "
                    "authored file exists to refuse — carrying the South Division's 80 ft "
                    "west would have mis-sized every lot line, and carrying a neighbour's "
                    "75 3/5 along a tier is the same mistake one street shorter."),
            "this_block_refused": record.get("refused"),
            "what_would_settle_it": ("a scan of the same sheet that resolves this block's "
                                     "own marginal figures; the authored file names the "
                                     "crop region and the enlargements already tried"),
            "meanwhile": ("the block stands with its boundary, its numeral, its lot COUNT "
                          "and its ground, which is what a placement ticket needs to name "
                          "it — it is the lot LINES that are withheld, not the block"),
        }
        return taken

    taken["figure_read_on_this_block"] = figure
    face_ft = entry["frontage_ft"]
    depth_ft = entry["depth_m"] / FT_M
    if figure["figure"] == "lot_frontage_ft":
        rows = taken["rows_read"]
        asks_ft = rows * figure["ft"]
        has_ft, axis = depth_ft, "north to south"
    else:
        asks_ft = 2 * figure["ft"] + west["alley_width_ft"]
        has_ft, axis = face_ft, "east to west"
    taken["closure_against_the_committed_lines"] = {
        "axis": axis,
        "the_sheet_asks_ft": round(asks_ft, 1),
        "the_committed_lines_give_ft": round(has_ft, 1),
        "short_by_ft": round(asks_ft - has_ft, 1),
        "so": ("the lot lines below divide the block the committed lines give, in the "
               "arrangement and the count the sheet reads, and are NOT the printed "
               "figure seated at its printed size. What is short is this project's West "
               "Division street spacing and not the module — T-0445 is the ticket that "
               "would move those centrelines, and T-0444 and "
               "tools/measure_west_division_module.py report the same gap."),
    }
    return taken


def module_for(entry: dict, bounded_by: dict, west: dict, spacing_ft: float) -> dict:
    """Which module this block was subdivided on, and — where another one is held — why not it.

    T-1105. The South Division module is the only one this file can BUILD, and for
    nineteen blocks out of nineteen that is also the only one the evidence allows. Two of
    them stand west of the river, where the plat prints a different arrangement; the
    arithmetic that refuses it is computed here and carried on the block, so a reader
    sees a refusal with a figure rather than a silent 80 ft.
    """
    taken = {
        "module": "south_division_thompson_1830",
        "lot_frontage_ft": LOT_FRONTAGE_FT,
        "alley_width_ft": ALLEY_FT,
        "alley_runs": "east-west, mid-block",
        "chosen_by": "the only module this generator can seat on the committed street lines",
    }
    if not {bounded_by["west"], bounded_by["east"]} <= west["streets"]:
        taken["division"] = "south"
        return taken

    taken["division"] = "west"
    face_ft = entry["frontage_m"] / FT_M
    depth_ft = entry["depth_m"] / FT_M
    columns_ft = 2 * west["lot_depth_ft"] + west["alley_width_ft"]
    rows = depth_ft / west["lot_frontage_ft"]
    taken["west_division_module_refused"] = {
        "module": "west_division_thompson_1830",
        "authored_in": west["authored_in"],
        "confidence_of_the_figures": west["confidence"],
        "what_it_asks_for": (
            f"two columns of {west['lot_depth_ft']:.0f} ft lots backing onto an "
            f"{west['alley_width_ft']:.0f} ft north-south alley — {columns_ft:.0f} ft "
            f"east to west — and {west['printed_frontage']} ft of frontage to a lot, "
            f"{west['block_north_south_ft']:.0f} ft north to south"),
        "what_the_committed_lines_give": {
            "east_west_face_ft": round(face_ft, 1),
            "north_south_depth_ft": round(depth_ft, 1),
        },
        "the_arithmetic": (
            f"the two lot columns alone need {2 * west['lot_depth_ft']:.0f} ft and this "
            f"block's face is {face_ft:.1f} ft, so the arrangement does not fit before "
            f"the alley is cut; {west['block_east_west_ft']:.0f} ft is "
            f"{west['block_east_west_ft'] - face_ft:.1f} ft more than the block has. "
            f"North to south {depth_ft:.1f} ft divides into {rows:.2f} lots of "
            f"{west['printed_frontage']} ft, and a plat does not print a fifth of a lot."),
        "why_the_lines_and_not_the_module": (
            "the module is `documented` — figures printed on the sheet and numerals "
            f"counted in a block — and it closes exactly at {west['block_east_west_ft']:.0f} "
            "ft each way. What does not close is this project's West Division street "
            f"spacing: Clinton to Canal is committed at {spacing_ft:.1f} ft against "
            f"the plat's own {west['street_module_ft']:.0f} ft. Seating the printed module "
            "would mean moving those lines, which is T-0445's ticket and not this one's, "
            "and the same short spacing is what T-0444 reported."),
        "so": ("this block keeps the South Division subdivision it was already built on, "
               "and says here that it is not the module the West Division plat prints"),
    }
    return taken


# ---------------------------------------------------------------- geometry helpers

def unit(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy)
    if length == 0:
        raise SystemExit("a street segment of zero length cannot carry a direction")
    return dx / length, dy / length


def offset_polyline(points: list[tuple[float, float]], distance: float,
                    toward: tuple[float, float]) -> list[tuple[float, float]]:
    """Shift a polyline `distance` metres to the side `toward` points at.

    Each vertex moves along its own segment normal; consecutive offset segments are
    joined by intersecting them (a miter), which is exact for the near-straight lines
    these streets are and does not fold on the shallow bends South Water carries.
    """
    segments = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        ux, uy = unit(bx - ax, by - ay)
        nx, ny = -uy, ux
        if nx * toward[0] + ny * toward[1] < 0:
            nx, ny = -nx, -ny
        segments.append(((ax + nx * distance, ay + ny * distance),
                         (bx + nx * distance, by + ny * distance)))
    out = [segments[0][0]]
    for first, second in zip(segments, segments[1:]):
        crossing = line_intersection(first[0], first[1], second[0], second[1])
        out.append(crossing if crossing else first[1])
    out.append(segments[-1][1])
    return out


def line_intersection(p1, p2, p3, p4):
    """Intersection of the infinite lines through p1p2 and p3p4, or None if parallel."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-9:
        return None
    a = x1 * y2 - y1 * x2
    b = x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / denominator,
            (a * (y3 - y4) - (y1 - y2) * b) / denominator)


def cross_polyline(polyline: list[tuple[float, float]], line: tuple, reach_m: float):
    """Where `polyline` crosses the infinite `line`, and the vertex it happens after.

    Returns (point, index, extrapolated_m). A crossing found on one of the polyline's
    own segments is a street that reaches the block. A crossing beyond its ends is
    reported with how far past the drawn end it lies, so the caller can refuse it.
    """
    (lx1, ly1), (lx2, ly2) = line

    def side(p):
        return (lx2 - lx1) * (p[1] - ly1) - (ly2 - ly1) * (p[0] - lx1)

    for index, (a, b) in enumerate(zip(polyline, polyline[1:])):
        sa, sb = side(a), side(b)
        if sa == 0 or sb == 0 or (sa > 0) != (sb > 0):
            point = line_intersection(a, b, (lx1, ly1), (lx2, ly2))
            if point:
                return point, index, 0.0
    # No segment straddles it: extend the nearer end and measure the reach.
    best = None
    for end, neighbour, index in ((polyline[0], polyline[1], -1),
                                  (polyline[-1], polyline[-2], len(polyline) - 1)):
        point = line_intersection(end, neighbour, (lx1, ly1), (lx2, ly2))
        if point is None:
            continue
        gap = math.dist(point, end)
        if best is None or gap < best[2]:
            best = (point, index, gap)
    if best is None or best[2] > reach_m:
        return None, None, (best[2] if best else float("inf"))
    return best


def polyline_between(polyline, start, start_index, end, end_index):
    """The run of `polyline` from one crossing to the other, ends included."""
    if start_index <= end_index:
        middle = polyline[start_index + 1:end_index + 1]
    else:
        middle = list(reversed(polyline[end_index + 1:start_index + 1]))
    return [start] + middle + [end]


def resample(chain: list[tuple[float, float]], fraction: float) -> tuple[float, float]:
    """The point `fraction` of the way along a chain, by arc length."""
    lengths = [math.dist(a, b) for a, b in zip(chain, chain[1:])]
    target = sum(lengths) * fraction
    for (a, b), length in zip(zip(chain, chain[1:]), lengths):
        if target <= length or length == 0:
            t = 0.0 if length == 0 else target / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        target -= length
    return chain[-1]


def chain_length(chain) -> float:
    return sum(math.dist(a, b) for a, b in zip(chain, chain[1:]))


def polygon_area(ring) -> float:
    total = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total) / 2.0


def point_in_polygon(point, ring) -> bool:
    e, n = point
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > n) != (by > n):
            x = ax + (n - ay) * (bx - ax) / (by - ay)
            if x > e:
                inside = not inside
    return inside


def rounded(points, places: int = 2):
    return [[round(e, places), round(n, places)] for e, n in points]


# ---------------------------------------------------------------- the grid itself

def street_lines(streets: dict) -> dict:
    """Every committed centreline, with the corridor width its own record declares.

    T-1191 added `corridor_m`. The layer's top-level `corridor_width_m` is the Original
    Town's 80 ft module and stays the default, so every street that does not declare one
    reads exactly as it did; Kinzie's Addition and the Michigan Street tract declare
    narrower and wider ones off Wright's sheet and are now measured at those widths
    rather than at the town's.
    """
    default = float(streets.get("corridor_width_m", 24.384))
    lines = {}
    for street in streets["streets"]:
        points = [(float(e), float(n)) for e, n in street["path_local_enu_m"]]
        corridor = float(street.get("corridor_width_m", default))
        lines[street["id"]] = {
            "id": street["id"],
            "name": street["name_1835"],
            "points": points,
            "mean_e": sum(p[0] for p in points) / len(points),
            "mean_n": sum(p[1] for p in points) / len(points),
            "confidence": street.get("geometry_confidence", "reconstructed"),
            "corridor_m": corridor,
            "half_width_m": corridor / 2.0,
        }
    return lines


def _half_width(street: dict, fallback: float) -> float:
    """A street's own half corridor, or the module's where the record declares none."""
    value = street.get("half_width_m")
    return fallback if value is None else float(value)


def block_edges(lines: dict, half_width: float) -> dict:
    """Both platted edges of every street: the block faces the corridor is cut between."""
    edges = {}
    # The union across every grid, read at call time so a caller that widens one of the
    # lists (measure_southern_ground) still gets edges for the street it added. Taken
    # from `grids()` rather than from the constants since T-1455: a grid whose lines are
    # read out of a committed file has no constant to name here, and a list that has to
    # be extended by hand every time a grid is added is a list that will be forgotten.
    ew = [s for layer in grids() for s in layer["rows"]]
    ns = [s for layer in grids() for s in layer["columns"]]
    for street_id, street in lines.items():
        own = _half_width(street, half_width)
        if street_id in ew:
            edges[street_id] = {
                "south": offset_polyline(street["points"], own, (0.0, -1.0)),
                "north": offset_polyline(street["points"], own, (0.0, 1.0)),
            }
        elif street_id in ns:
            edges[street_id] = {
                "east": offset_polyline(street["points"], own, (1.0, 0.0)),
                "west": offset_polyline(street["points"], own, (-1.0, 0.0)),
            }
    return edges


def build_block(north_id, south_id, west_id, east_id, lines, edges, reach_m):
    """The quadrilateral between four platted corridors, or why it cannot be built."""
    north_edge = edges[north_id]["south"]
    south_edge = edges[south_id]["north"]
    west_edge = edges[west_id]["east"]
    east_edge = edges[east_id]["west"]
    west_line = (west_edge[0], west_edge[-1])
    east_line = (east_edge[0], east_edge[-1])
    north_line = (north_edge[0], north_edge[-1])
    south_line = (south_edge[0], south_edge[-1])

    nw, nw_i, nw_gap = cross_polyline(north_edge, west_line, reach_m)
    ne, ne_i, ne_gap = cross_polyline(north_edge, east_line, reach_m)
    sw, sw_i, sw_gap = cross_polyline(south_edge, west_line, reach_m)
    se, se_i, se_gap = cross_polyline(south_edge, east_line, reach_m)
    for point, gap, street_id in ((nw, nw_gap, north_id), (ne, ne_gap, north_id),
                                  (sw, sw_gap, south_id), (se, se_gap, south_id)):
        if point is None:
            return None, (f"{lines[street_id]['name']}'s committed centreline stops "
                          f"{gap:.0f} m short of this block")
    for edge_id, edge, near, far in ((west_id, west_edge, north_line, south_line),
                                     (east_id, east_edge, north_line, south_line)):
        for line in (near, far):
            point, _, gap = cross_polyline(edge, line, reach_m)
            if point is None:
                return None, (f"{lines[edge_id]['name']}'s committed centreline stops "
                              f"{gap:.0f} m short of this block")

    # AND THE TWO ROWS MUST NOT HAVE CROSSED. Four crossings can all be found and still
    # describe no block: where an east-west street bends onto the dry bank it can converge
    # on the row below it to less than a corridor, and then the block's north-west corner
    # falls SOUTH of its south-west one. The ring is a bowtie, `polygon_area` returns the
    # difference of its two lobes rather than nothing, and the block is emitted with a
    # plausible area and a plausible depth. Measured 2026-08-29 by T-0183 at
    # blk_south_water_market, where closing South Water's west end onto Market's corridor
    # produced a 4,411 m2 "block" 36.85 m deep whose north-west corner stood 14.9 m south
    # of its south-west one. It is `node_rule`'s own failure mode one layer down — an
    # answer that looks right rather than no answer — so it is refused here by name.
    for corner_n, corner_s, side in ((nw, sw, "west"), (ne, se, "east")):
        depth = corner_n[1] - corner_s[1]
        if depth <= 0.0:
            return None, (f"{lines[north_id]['name']} and {lines[south_id]['name']} have "
                          f"crossed by this block's {side} corner \u2014 their platted "
                          f"corridors overlap by {-depth:.1f} m there, so what lies between "
                          "them is not a block")

    north_chain = polyline_between(north_edge, nw, nw_i, ne, ne_i)
    south_chain = polyline_between(south_edge, sw, sw_i, se, se_i)
    ring = north_chain + list(reversed(south_chain))
    return {"ring": ring, "north_chain": north_chain, "south_chain": south_chain}, None


def subdivide(block: dict, alley_m: float, frontage_m: float) -> dict:
    """Two tiers of lots either side of a mid-block alley, fronting the E-W streets."""
    north_chain, south_chain = block["north_chain"], block["south_chain"]
    frontage = (chain_length(north_chain) + chain_length(south_chain)) / 2.0
    count = max(1, round(frontage / frontage_m))
    stations = []
    for index in range(count + 1):
        fraction = index / count
        top = resample(north_chain, fraction)
        bottom = resample(south_chain, fraction)
        depth = math.dist(top, bottom)
        # The alley is centred, so each tier is (depth - alley) / 2 deep at this station.
        a = (0.5 - alley_m / (2 * depth)) if depth else 0.0
        b = (0.5 + alley_m / (2 * depth)) if depth else 1.0
        stations.append({
            "top": top,
            "alley_north": (top[0] + (bottom[0] - top[0]) * a,
                            top[1] + (bottom[1] - top[1]) * a),
            "alley_south": (top[0] + (bottom[0] - top[0]) * b,
                            top[1] + (bottom[1] - top[1]) * b),
            "bottom": bottom,
            "depth": depth,
        })
    lots = []
    for index in range(count):
        left, right = stations[index], stations[index + 1]
        lots.append({
            "tier": "north",
            "frontage_m": round(math.dist(left["top"], right["top"]), 2),
            "depth_m": round((left["depth"] + right["depth"]) / 2 / 2 - alley_m / 2, 2),
            "polygon": rounded([left["top"], right["top"],
                                right["alley_north"], left["alley_north"]]),
        })
        lots.append({
            "tier": "south",
            "frontage_m": round(math.dist(left["bottom"], right["bottom"]), 2),
            "depth_m": round((left["depth"] + right["depth"]) / 2 / 2 - alley_m / 2, 2),
            "polygon": rounded([left["alley_south"], right["alley_south"],
                                right["bottom"], left["bottom"]]),
        })
    alley = rounded([stations[0]["alley_north"], stations[-1]["alley_north"],
                     stations[-1]["alley_south"], stations[0]["alley_south"]])
    return {"lots": lots, "alley": alley, "frontage_m": frontage, "count": count}


def stamp_number(entry: dict, record: dict, scheme: dict) -> None:
    """Put the plat's number on a block, and the scheme's numbers on its lots.

    The lots are numbered by where they LIE, not by the order the subdivision
    emitted them: the scheme runs 1-4 east to west along the north row and 5-8 west
    to east along the south row, and reading that off a list index would make the
    numbering depend on which way `data/streets/1835.json` happens to draw a street.
    """
    entry["plat_block_number"] = {
        "number": record["number"],
        "confidence": record["confidence"],
        "numeral_on_sheet": record["numeral_on_sheet"],
        "sources": record["sources"],
        "authored_in": "data/traces/thompson_block_numbering.json",
        "note": record["note"],
    }
    lots = entry.get("lots") or []
    per_face = len(lots) // 2
    if per_face != 4 or len(lots) != 2 * per_face:
        # The scheme is 1-4 and 5-8. A block the module divided some other way is
        # left unnumbered rather than renumbered to fit, and says so.
        entry["plat_block_number"]["lots_not_numbered"] = (
            f"the module divided this block into {len(lots)} lot(s), and the scheme read "
            "off block 18 numbers four to a face; a scheme stretched to fit is an invention")
        return
    north = sorted((l for l in lots if l["tier"] == "north"),
                   key=lambda l: -sum(pt[0] for pt in l["polygon"]) / len(l["polygon"]))
    south = sorted((l for l in lots if l["tier"] == "south"),
                   key=lambda l: sum(pt[0] for pt in l["polygon"]) / len(l["polygon"]))
    for index, lot in enumerate(north + south):
        lot["plat_lot_number"] = index + 1
        lot["plat_lot_confidence"] = scheme["confidence"]


def stamp_addition_number(entry: dict, record: dict) -> None:
    """Put Kinzie's Addition's own block numeral on a cell of this grid.

    A sibling of `stamp_number` and deliberately not the same function: the Addition's
    reading carries fields the Original Town's does not (`cell`, `legibility`,
    `written_on_sheet`, and a `derives_from_scheme` flag that separates a numeral READ in
    its cell from one the run supplies), and it numbers no lots because this grid draws
    none inside the Addition. Nothing is judged here; the fields are carried across.
    """
    entry["plat_block_number"] = {
        "number": record["number"],
        "confidence": record["confidence"],
        "numeral_on_sheet": record["numeral_on_sheet"],
        "written_on_sheet": record.get("written_on_sheet"),
        "legibility": record.get("legibility"),
        "cell": record["cell"],
        "sources": record["sources"],
        "authored_in": "data/traces/kinzie_addition_block_numbering.json",
        "note": record.get("note") or record["bounded_by"],
    }
    if entry.get("lots") == [] and "lots_per_face" not in entry:
        entry["plat_block_number"]["lots_not_numbered"] = (
            "this grid draws no lot lines inside the Addition, so there is nothing here "
            "to number; the Democrat's land notices sell by block AND lot, and only the "
            "block half of that address is placeable today")


# ------------------------------------------------------------- the seated tracts
#
# T-1454. A THIRD KIND OF GRID, and it exists because the two above cannot reach it.
# `grids()` cuts a cell between four committed street CENTRELINES and that is the whole
# of what it can do. The Michigan Street tract north of Kinzie Street and Wabansia on
# the North Branch are each ruled by lines this project has never committed as streets —
# the tract's own borders and its mid-block alleys, Wabansia's three block columns and
# its own west margin — so neither has ever carried a block in this file, let alone a
# lot, and every placement ticket that wanted to name one had nothing to name.
#
# What both DO have is a committed SEATING: a tool that has already hung that sheet's
# own ladder on the committed grid and written the answer down —
# `tools/seat_michigan_st_tract.py` into `data/traces/michigan_st_tract_seated.json`
# (T-1079), `tools/seat_wabansia_streets.py` into `data/traces/wabansia_seating.json`
# (T-1070, T-1086). The cells below are cut on THAT seating and never on a second one.
# Wabansia's corners come out of `seat_wabansia_streets.seating()` itself, the same
# closure that placed its six streets; the Michigan tract's out of the four corners its
# seating committed. One edge cannot be derived twice, which is the rule that file's own
# `_polygon` states about the one edge it shares with the tract outline, one layer up.
#
# AND THE LOTS ARE THE SHEET'S OWN. This is the half of the parent ticket Kinzie's
# Addition could not answer — there, no lot rule has been read, so its blocks stand
# undivided and say so. Here Wright rules lot lines inside both tracts and both readings
# measured them: thirty-two lot frontages in the Michigan Street tract, west column and
# east, front row and back (`michigan_st_tract_grid.json` § readings.north_south), and
# one column divider per Wabansia block in the tiers where the sheet draws one
# (`wabansia_block_numbering.json` § columns, `lots_wide` and `lot_divider_px`).
#
# NOTHING IS STRETCHED TO FILL. A face the reading did not reach keeps
# `subdivision_withheld` with the reason, the same way the Addition's blocks do — three
# of the Michigan tract's eight faces are in that position. And Wabansia's blocks are
# divided ACROSS ONLY: the sheet draws a north-south lot line and no east-west one, so
# each lot runs the full depth of its tier and the block says that is what the reading
# gives rather than cutting a back row nobody drew.

# The anisotropic stretch the 1834 sheets carry, which this file's header names as the
# reason a block face is generated and never traced. It is the bar a read lot row has to
# close inside before its scale is a fit rather than a disagreement.
SHEET_STRETCH = 0.045

MICHIGAN_READING_PATH = DATA / "traces" / "michigan_st_tract_grid.json"
MICHIGAN_SEATING_PATH = DATA / "traces" / "michigan_st_tract_seated.json"
WABANSIA_NUMBERING_PATH = DATA / "traces" / "wabansia_block_numbering.json"
WABANSIA_SEATING_PATH = DATA / "traces" / "wabansia_seating.json"
WABANSIA_TRACE_PATH = DATA / "traces" / "wabansia_streets.json"


def _tract_frame(corners: dict, east_span: tuple, north_span: tuple):
    """A ladder coordinate on the ground, by the four corners the seating committed.

    `place(u, v)` takes metres east of the tract's north-south datum and metres north of
    its east-west one — which is exactly the frame `ladder_m` is written in — and returns
    local ENU by bilinear interpolation of `corners_local_enu_m`. The tract is a
    parallelogram on the ground because the committed grid it is hung on is not
    axis-aligned, so interpolating the corners carries that tilt rather than ignoring it,
    and lands exactly on each corner at the ladder's own extremes.
    """
    w_e, e_e = east_span
    s_n, n_n = north_span

    def place(u, v):
        s = (u - w_e) / (e_e - w_e)
        t = (v - s_n) / (n_n - s_n)
        south = (corners["sw"][0] + (corners["se"][0] - corners["sw"][0]) * s,
                 corners["sw"][1] + (corners["se"][1] - corners["sw"][1]) * s)
        north = (corners["nw"][0] + (corners["ne"][0] - corners["nw"][0]) * s,
                 corners["nw"][1] + (corners["ne"][1] - corners["nw"][1]) * s)
        return (south[0] + (north[0] - south[0]) * t,
                south[1] + (north[1] - south[1]) * t)
    return place


def _face_lots(place, fronts: list, u0: float, u1: float, v_front: float,
               v_back: float, row_id: str, faces_what: str) -> tuple[list, dict]:
    """One row of lots along a block face, from the frontages the sheet was read at.

    The read frontages are laid west to east in the order the reading lists them, scaled
    so that the row closes on the block's own seated face. THE SCALE IS REPORTED, not
    hidden: it is the sheet's fit against the committed seating over this one face, and
    the five rows the Michigan Street tract was read on run from 0.8 per cent under
    unity to 2.8 per cent over — inside the 3.7-4.5 per cent of anisotropic stretch the
    1834 sheets are known to carry, which is the figure this file's own header refuses to
    trace block faces through. A row stretched further than that is a row whose lot lines
    may not belong to this block at all, and it is flagged on its own evidence rather
    than quietly divided into the difference.
    """
    read_total = sum(fronts)
    width = u1 - u0
    scale = width / read_total
    lots, u = [], u0
    for index, front in enumerate(fronts):
        a, b = u, u + front * scale
        polygon = [place(a, v_front), place(b, v_front),
                   place(b, v_back), place(a, v_back)]
        lots.append({
            "tier": "north" if v_front > v_back else "south",
            "frontage_m": round(math.dist(polygon[0], polygon[1]), 2),
            "depth_m": round(math.dist(polygon[1], polygon[2]), 2),
            "polygon": rounded(polygon),
            "read_frontage_m": front,
            "read_in": f"data/traces/michigan_st_tract_grid.json § readings.north_south.{row_id}",
            "plat_lot_confidence": "inferred",
            "order": index + 1,
        })
        u = b
    return lots, {
        "row": row_id,
        "fronts_read": len(fronts),
        "read_total_m": round(read_total, 2),
        "seated_face_m": round(width, 2),
        "scale": round(scale, 4),
        "faces": faces_what,
        "note": ("the lot lines are the sheet's, laid west to east in the order they were "
                 "read and scaled by the figure above so the row closes on the seated "
                 "face; the departure is the sheet's fit, and the sheets carry 3.7-4.5 "
                 "per cent of anisotropic stretch"),
        **({} if abs(scale - 1.0) <= SHEET_STRETCH else {
            "beyond_the_sheets_own_stretch": (
                f"this row had to be scaled {abs(scale - 1.0) * 100:.1f} per cent to close "
                f"on its seated face, past the {SHEET_STRETCH * 100:.1f} per cent the 1834 "
                "sheets are known to stretch by. Either the reading is short a lot line or "
                "the seating is not this row's — it is carried here as a disagreement "
                "rather than absorbed into the lot widths")}),
    }


def michigan_st_tract() -> dict:
    """The four blocks of the tract north of Kinzie Street, and their read lots.

    Two block columns either side of Market Street, two tiers either side of Michigan
    Street, each block ruled through by its own mid-block alley — which no Original Town
    block on this sheet carries, and which is the tract's signature along with its small
    parcels. The ladder, the corners and the identification of both streets as the town's
    own are T-1079's and are read, not re-derived.
    """
    read = load(MICHIGAN_READING_PATH)
    seated = load(MICHIGAN_SEATING_PATH)
    north = seated["ladder_m"]["off_michigan_northward"]
    east = seated["ladder_m"]["off_market_eastward"]
    place = _tract_frame(seated["corners_local_enu_m"],
                         (east["west_border"], east["east_border"]),
                         (north["south_border"], north["north_border"]))
    half_ew = read["module"]["michigan_st_corridor"]["read_m"] / 2.0
    half_ns = read["module"]["north_south_street_corridor"]["read_m"] / 2.0
    alleys = read["readings"]["east_west"]

    # (key, reading's window id, west edge, east edge, what bounds it west, what bounds
    #  it east, the committed street id on the west side, ditto east). The tract's own
    # borders are not streets and carry none.
    columns = [
        ("west", "col_west", east["west_border"], -half_ns,
         "the tract's west border", "Market Street", None, "market_north"),
        ("east", "col_east", half_ns, east["east_border"],
         "Market Street", "the tract's east border", "market_north", None),
    ]
    tiers = [
        ("north", "tier1", half_ew, north["north_border"], "alley_north_tier",
         north["alley_north_tier"], "the tract's north border", "Michigan Street",
         None, "michigan_north"),
        ("south", "tier2", north["south_border"], -half_ew, "alley_south_tier",
         north["alley_south_tier"], "Michigan Street", "the tract's south border",
         "michigan_north", None),
    ]

    cells = []
    for col_key, col_id, u0, u1, west_of, east_of, west_id, east_id in columns:
        for (tier_key, row_prefix, v_low, v_high, alley_key, alley_v, north_of, south_of,
             north_id, south_id) in tiers:
            alley_m = alleys[alley_key][col_id]["corridor_m"]
            ring = [place(u0, v_high), place(u1, v_high),
                    place(u1, v_low), place(u0, v_low)]
            lots, rows = [], []
            for which, v_front, v_back in (
                    ("north", v_high, alley_v + alley_m / 2.0),
                    ("south", v_low, alley_v - alley_m / 2.0)):
                row_id = f"{row_prefix}_{which}"
                fronts = (read["readings"]["north_south"][row_id]
                          .get(f"{col_key}_lot_front_m"))
                if not fronts:
                    rows.append({
                        "row": row_id,
                        "subdivision_withheld": (
                            "the reading did not reach this face. T-1076 read the "
                            f"{col_id.split('_')[1]} column's lot lines on "
                            f"{'one row' if col_key == 'west' else 'all four rows'} and "
                            "this is not one of them, and a lot count carried from the "
                            "row above would be a guess dressed as arithmetic — the same "
                            "refusal Kinzie's Addition's blocks carry whole."),
                        "what_would_settle_it": (
                            "one more crop of wright_1834_nara_hup on this row, read the "
                            "way tools/read_michigan_st_tract.py reads the others"),
                    })
                    continue
                face, evidence = _face_lots(place, fronts, u0, u1, v_front, v_back,
                                            row_id, north_of if which == "north"
                                            else south_of)
                lots += face
                rows.append(evidence)
            faces = ((math.dist(ring[0], ring[1]) + math.dist(ring[3], ring[2])) / 2.0)
            area = polygon_area(ring)
            cell = {
                "id": f"blk_michigan_st_tract_{col_key}_{tier_key}",
                "grid": "michigan_st_tract",
                "plat": "michigan_st_tract",
                # ONLY THE SIDES THAT ARE COMMITTED STREETS. `bounded_by` is a
                # contract everything downstream of this file reads as four street ids —
                # tools/derive_hay_limits.py meets two pairs of them to find a block's
                # centre, tools/generate_lot_line_fences.py walks the values — and two of
                # this tract's four sides are its own borders, which no street table
                # carries. Naming them in prose inside that key broke the hay limit on
                # the first run; omitting them lets every consumer that requires four
                # sides skip this block, which is the true answer, and the prose is
                # carried beside it where nothing looks up a street by it.
                "bounded_by": {k: v for k, v in
                               (("north", north_id), ("south", south_id),
                                ("west", west_id), ("east", east_id)) if v},
                "bounded_by_uncommitted": {k: v for k, v in
                                           (("north", north_of if not north_id else None),
                                            ("south", south_of if not south_id else None),
                                            ("west", west_of if not west_id else None),
                                            ("east", east_of if not east_id else None))
                                           if v},
                "boundary_local_enu_m": rounded(ring),
                "area_m2": round(area, 1),
                "frontage_m": round(faces, 2),
                "frontage_ft": round(faces / FT_M, 1),
                "depth_m": round(area / faces, 2),
                "lots_per_face": [f.get("fronts_read", 0) for f in rows],
                "alley_local_enu_m": rounded([
                    place(u0, alley_v + alley_m / 2.0), place(u1, alley_v + alley_m / 2.0),
                    place(u1, alley_v - alley_m / 2.0), place(u0, alley_v - alley_m / 2.0)]),
                "alley_width_m": round(alley_m, 2),
                "alley_read_in": (
                    "data/traces/michigan_st_tract_grid.json § readings.east_west."
                    f"{alley_key}.{col_id} — this block's own alley, read as a pair of "
                    "rules on this column and not carried from another"),
                "lots": lots,
                "lot_rows": rows,
            }
            cells.append(cell)
    return {
        "id": "michigan_st_tract",
        "plat": "michigan_st_tract",
        "name": "the Michigan Street tract north of Kinzie Street, Wright 1834",
        "seated_in": "data/traces/michigan_st_tract_seated.json",
        "read_in": "data/traces/michigan_st_tract_grid.json",
        "cells": cells,
        "module": {
            "module": "michigan_st_tract_wright_1834",
            "authored_in": "data/traces/michigan_st_tract_grid.json",
            "tract_width_m": read["module"]["tract_width_m"]["mean"],
            "tier_depth_by_column_m": read["module"]["tier_depth_by_column_m"],
            "michigan_st_corridor_m": read["module"]["michigan_st_corridor"]["read_m"],
            "north_south_street_corridor_m":
                read["module"]["north_south_street_corridor"]["read_m"],
            "alley_width": read["module"]["alley_width"],
            "lots_per_block_row": read["module"]["lots_per_block_row"],
            "west_column_lot_front_m": read["module"]["west_column_lot_front_m"],
            "east_column_lot_front_m": read["module"]["east_column_lot_front_m"],
            "confidence": read["confidence"],
            "division": "north",
            "chosen_by": ("the tract's own read parcel module, seated on the two "
                          "committed town lines the reading identifies its streets as "
                          "— `michigan_north` and `market_north`"),
            "reading": read["module"]["reading"],
        },
    }


def wabansia() -> dict:
    """Wabansia's twenty-one blocks, their numerals, and the lot line each one carries.

    Seven tiers between six read cross streets and Kinzie Street, three columns, and a
    grid that JOGS two lots east at Sailors Street — the step is the reading's, carried
    here because the columns are read tier by tier and never counted across one.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    from seat_wabansia_streets import seating  # noqa: PLC0415
    frame = seating()
    seat, south_row, tiers = frame["seat"], frame["south_row"], frame["tiers"]
    doc = load(WABANSIA_NUMBERING_PATH)
    trace = load(WABANSIA_TRACE_PATH)
    numerals = {(b["column"], b["tier"]): b for b in doc["blocks"]}
    # Wabansia's six cross streets and Kinzie Street ARE committed — seat_wabansia_streets
    # wrote them into data/streets/1835.json — so a tier bounded by one of them names it.
    # A tier bounded by the tract's own north boundary, or by the `free` ground the sheet
    # leaves between two of them, does not, and says so in `bounded_by_uncommitted`.
    street_ids = {s["id"] for s in load(DATA / "streets" / "1835.json")["streets"]}

    cells = []
    for col in doc["columns"]:
        tier = tiers[col["tier"]]
        on_kinzie = tier["south"] == "kinzie"

        def row(px, which, tier=tier, on_kinzie=on_kinzie):
            # The south edge of the bottom tier is Kinzie Street, and Kinzie Street is
            # carried by the reading's own shear rather than held flat — the convention
            # `seat_wabansia_streets._polygon` settled on, because the block grid's
            # outline and the blocks inside it share that edge.
            if which == "south" and on_kinzie:
                return south_row(px)
            return tier["y_px"][0] if which == "north" else tier["y_px"][1]

        w, e = col["west_px"], col["east_px"]
        ring = [seat(w, row(w, "north")), seat(e, row(e, "north")),
                seat(e, row(e, "south")), seat(w, row(w, "south"))]
        divider = col.get("lot_divider_px")
        if col["lots_wide"] == 2 and divider:
            cuts = [w, float(divider), e]
        else:
            cuts = [w, e]
        lots = []
        for index in range(len(cuts) - 1):
            a, b = cuts[index], cuts[index + 1]
            polygon = [seat(a, row(a, "north")), seat(b, row(b, "north")),
                       seat(b, row(b, "south")), seat(a, row(a, "south"))]
            front = (math.dist(polygon[0], polygon[1])
                     + math.dist(polygon[3], polygon[2])) / 2.0
            lots.append({
                "tier": "the whole block, tier line to tier line",
                "frontage_m": round(front, 2),
                "depth_m": round(abs(polygon_area(polygon)) / front, 2),
                "polygon": rounded(polygon),
                "plat_lot_confidence": "inferred",
                "order": index + 1,
            })
        area = polygon_area(ring)
        faces = (math.dist(ring[0], ring[1]) + math.dist(ring[3], ring[2])) / 2.0
        record = numerals.get((col["column"], col["tier"]))
        cell = {
            "id": f"blk_wabansia_{col['column'].lower()}_{col['tier']}",
            "grid": "wabansia",
            "plat": "wabansia",
            "bounded_by": {k: v for k, v in (("north", tier["north"]),
                                             ("south", tier["south"])) if v in street_ids},
            "bounded_by_uncommitted": {
                **({} if tier["north"] in street_ids
                   else {"north": tier["north"]}),
                **({} if tier["south"] in street_ids
                   else {"south": tier["south"]}),
                "west": f"the west rule of block column {col['column']}",
                "east": f"the east rule of block column {col['column']}",
            },
            "cell": {"column": col["column"], "tier": col["tier"]},
            "boundary_local_enu_m": rounded(ring),
            "area_m2": round(area, 1),
            "frontage_m": round(faces, 2),
            "frontage_ft": round(faces / FT_M, 1),
            "depth_m": round(area / faces, 2),
            "lots_per_face": len(lots),
            "alley_local_enu_m": None,
            "alley_withheld": (
                "the sheet rules no alley inside these blocks, which is what "
                "data/traces/wabansia_streets.json states of the street reading too "
                "(`alleys` is false there for the same reason); an 18 ft alley laid in "
                "here would come from the Original Town's module and not from Wabansia"),
            "lots": lots,
            "lot_rule": {
                "read_in": "data/traces/wabansia_block_numbering.json § columns",
                "lots_wide": col["lots_wide"],
                "lot_divider_px": divider,
                "width_ft_controlled": col["width_ft_controlled"],
                "divided_across_only": (
                    "the sheet draws a north-south lot line in this tract and no "
                    "east-west one, so each lot runs the full depth of its tier. A back "
                    "row cut here would be the Original Town's arrangement applied to a "
                    "survey that does not draw it."),
            },
        }
        if record:
            cell["plat_block_number"] = {
                "number": record["number"],
                "confidence": record["confidence"],
                "numeral_on_sheet": True,
                "legibility": record.get("legibility"),
                "cell": {"column": record["column"], "tier": record["tier"]},
                "derives_from_scheme": record.get("derives_from_scheme"),
                "sources": ["wright_1834"],
                "authored_in": "data/traces/wabansia_block_numbering.json",
                "note": doc["scheme"]["reading"],
            }
        cells.append(cell)
    landed = {c["plat_block_number"]["number"] for c in cells
              if c.get("plat_block_number")}
    lost = sorted(r["number"] for r in doc["blocks"] if r["number"] not in landed)
    if lost:
        raise SystemExit(
            "data/traces/wabansia_block_numbering.json numbers "
            f"{', '.join(str(n) for n in lost)}, which this grid neither builds nor "
            "omits — every one of the twenty-one has to land somewhere or the reading "
            "and the grid disagree in silence")
    return {
        "id": "wabansia",
        "plat": "wabansia",
        "name": "Wabansia, on the west bank of the North Branch, Wright 1834",
        "seated_in": "data/traces/wabansia_seating.json",
        "read_in": "data/traces/wabansia_block_numbering.json",
        "cells": cells,
        "numbering": {
            "authored_in": "data/traces/wabansia_block_numbering.json",
            "scheme": doc["scheme"]["reading"],
            "first": doc["scheme"]["first"],
            "last": doc["scheme"]["last"],
            "cells": doc["scheme"]["cells"],
            "the_jog": doc["jog"]["reading"],
        },
        "module": {
            "module": "wabansia_wright_1834",
            "authored_in": "data/traces/wabansia_streets.json",
            "tier_pitch_m": trace["module"].get("tier_pitch_m"),
            "control": doc["control"],
            "confidence": "inferred",
            "division": "west",
            "chosen_by": ("Wabansia's own read column and tier rules, seated on the one "
                          "line it shares with the town it adjoins — Kinzie Street"),
            "lot_subdivision": (
                "the sheet's own column dividers and nothing else: fifteen of the "
                "twenty-one cells are two lots wide and six are one, read tier by tier "
                "off wright_1834_nara_hup, and no east-west lot rule is drawn"),
        },
        "water_lots": {
            "seated_in": ("data/traces/wabansia_seating.json § "
                          "water_lot_wedge_local_enu_m"),
            "read_in": "data/traces/wabansia_water_lots.json",
            "count": 26,
            "why_they_are_not_here": (
                "T-1077 read the river-front water lots as a lot strip and T-1086 seated "
                "them, polygon by polygon, in the file above. They are lots of this "
                "survey and they are already derived; re-emitting them here would be the "
                "same ground derived twice, which is the one thing a generated layer may "
                "not do. A placement ticket that wants a Wabansia water lot reads them "
                "where they were seated."),
        },
    }


def seated_tracts() -> list[dict]:
    """The grids whose cells are cut from a committed SEATING, not from street lines."""
    return [michigan_st_tract(), wabansia()]


def _seated_blocker(off: list, wet: list, ring: list, field) -> str:
    """Why a seated cell is carried on the omissions, with the figure that decides it."""
    box = (getattr(field, "meta", None) or {}).get("box_local_enu_m")
    if off:
        west = min(p[0] for p in off)
        edge = (f" — the modelled field's west edge stands at local E {box['e'][0]:.1f} "
                f"and this cell's far corner at E {west:.1f}, {box['e'][0] - west:.0f} m "
                "past it") if box else ""
        return (f"{len(off)} of {len(ring)} corners fall beyond the modelled ground{edge}. "
                "T-1193 carried the box out to E -700 for the West Division's held slots "
                "and this survey's west margin stands past even that, so the cell is "
                "carried here rather than emitted onto ground nothing models. Extending "
                "the box is what would build it; a block drawn over the edge would be "
                "dealt roofs that die in tools/generate_block_infill.py.")
    east = max(p[0] for p in wet)
    return (f"{len(wet)} of {len(ring)} corners stand under datum on the committed "
            f"e1834_harbor_cut field, the farthest at local E {east:.1f} — inside the "
            "North Branch this project already holds. tools/seat_wabansia_streets.py "
            "records the same disagreement at Sailors Street, where T-1074's tier-4 "
            "corner and T-1078's traced bank do not agree and neither is settled; the "
            "cell is carried here rather than drawn over the water.")


def grid_from_inputs() -> dict:
    control = load(DATA / "traces" / "street_control.json")
    streets = load(DATA / "streets" / "1835.json")
    module = control["platted_street"]
    half_width = float(module["half_width_m"])
    alley_m = round(ALLEY_FT * FT_M, 4)
    frontage_m = round(LOT_FRONTAGE_FT * FT_M, 4)
    # A crossing may be sought this far past a drawn centreline's end: half a corridor,
    # which is the distance a street line stops short of the far kerb when it is drawn
    # to the junction it ends at rather than through it. Anything further is refused.
    reach_m = half_width

    lines = street_lines(streets)
    layers = grids()
    missing = [s for layer in layers for s in layer["rows"] + layer["columns"]
               if s not in lines]
    if missing:
        raise SystemExit(f"street table is missing {', '.join(sorted(set(missing)))}")
    edges = block_edges(lines, half_width)

    field = None
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from heightfield import Heightfield  # noqa: PLC0415
        field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    except Exception:  # pragma: no cover - the field is committed; absence is reported
        field = None
    if field is None:
        raise SystemExit("cannot build the grid: the committed heightfield is missing")

    reserved = reserved_blocks()
    numbers, numbering_doc = block_numbering()
    tracts = survey_tracts()
    west = west_division()
    west_table, west_doc = west_division_table()
    west_reached: set = set()
    # The one spacing the West Division refusal turns on, re-derived here from the same
    # committed centrelines every block edge is offset from — never a figure typed in.
    spacing_ft = abs(lines["clinton"]["mean_e"] - lines["canal"]["mean_e"]) / FT_M
    blocks, omitted = [], []
    addition = addition_module()
    addition_numbers, addition_unreachable, addition_doc = {}, [], None
    for layer in layers:
      rows = sorted(layer["rows"], key=lambda s: -lines[s]["mean_n"])
      columns = sorted(layer["columns"], key=lambda s: lines[s]["mean_e"])
      if layer["id"] == "kinzies_addition":
          addition_numbers, addition_unreachable, addition_doc = addition_numbering(
              rows, columns, lines)
      for north_id, south_id in zip(rows, rows[1:]):
        pitch_n = abs(lines[north_id]["mean_n"] - lines[south_id]["mean_n"])
        for west_id, east_id in zip(columns, columns[1:]):
            is_west = layer["id"] == "west_division"
            # The West Division's ids carry their grid, because two grids now cut cells
            # between the same committed columns and `blk_lake_canal` is already taken —
            # by an OMISSION of the Original Town's grid, where Canal Street's eastern
            # neighbour is Market across the river rather than West Water beside it.
            block_id = (f"blk_west_{north_id}_{west_id}" if is_west
                        else f"blk_{north_id}_{west_id}")
            pitch_e = abs(lines[east_id]["mean_e"] - lines[west_id]["mean_e"])
            bounded_by = {"north": north_id, "south": south_id,
                          "west": west_id, "east": east_id}
            if is_west:
                west_reached.add((north_id, south_id, west_id, east_id))
            record = (west_table.get((north_id, south_id, west_id, east_id))
                      if is_west else None)
            if is_west and record is None:
                omitted.append({
                    "id": block_id, "grid": layer["id"], "bounded_by": bounded_by,
                    "reason": ("the sheet draws no block between these four lines. "
                               "data/traces/thompson_west_division_lots.json reads every "
                               "block the West Division carries, block by block, and none "
                               "of them stands here; a cell generated where the plat draws "
                               "none would be the grid inventing ground")})
                continue
            if is_west:
                twin = next((b for b in blocks if b.get("grid") == "original_town"
                             and b["bounded_by"] == bounded_by), None)
                if twin is not None:
                    omitted.append({
                        "id": block_id, "grid": layer["id"], "bounded_by": bounded_by,
                        "plat_block_number": west_number_record(record),
                        "already_derived_as": twin["id"],
                        "reason": (
                            f"this ground is already emitted by the Original Town's grid "
                            f"as `{twin['id']}`, and the same ground derived twice is the "
                            "one thing a generated layer may not do. It stands there on "
                            "the SOUTH Division module with a `west_division_module_"
                            "refused` note beside it, which this reading says is the wrong "
                            "arrangement for it — and this block prints no dimension of "
                            "its own, so this grid would withhold its lot lines rather "
                            "than re-cut them. Moving it onto this grid moves lot lines "
                            "that committed structure records are seated against, and that "
                            "is its own ticket rather than this cell's.")})
                    continue
            if pitch_n > MAX_PITCH_M or pitch_e > MAX_PITCH_M:
                omitted.append({
                    "id": block_id, "grid": layer["id"], "bounded_by": bounded_by,
                    "reason": (f"the streets are {max(pitch_n, pitch_e):.0f} m apart, past "
                               f"the {MAX_PITCH_M:.0f} m the plat's module allows a block "
                               f"— what lies between them is the river, not a block")})
                continue
            built, why = build_block(north_id, south_id, west_id, east_id,
                                     lines, edges, reach_m)
            if built is None:
                omitted.append({"id": block_id, "grid": layer["id"],
                                "bounded_by": bounded_by, "reason": why})
                continue
            ring = built["ring"]
            wet = [p for p in ring if not field.covers(*p) or field.height(*p) < 0.0]
            if wet:
                omitted.append({
                    "id": block_id, "grid": layer["id"], "bounded_by": bounded_by,
                    "reason": (f"{len(wet)} of {len(ring)} corners fall on water or beyond "
                               "the modelled ground; a platted block there is not something "
                               "this dataset can stand behind")})
                continue
            figure = west_lot_figure(record) if is_west else None
            if is_west:
                divided = subdivide_west(built, alley_m,
                                         len(record["lot_numerals_north_to_south"]))
            else:
                divided = subdivide(built, alley_m, frontage_m)
            entry = {
                "id": block_id,
                "grid": layer["id"],
                "plat": layer["plat"],
                "bounded_by": bounded_by,
                "boundary_local_enu_m": rounded(ring),
                "area_m2": round(polygon_area(ring), 1),
                "frontage_m": round(divided["frontage_m"], 2),
                "frontage_ft": round(divided["frontage_m"] / FT_M, 1),
                "depth_m": round(polygon_area(ring) / divided["frontage_m"], 2),
            }
            if is_west and figure is None:
                # BUILT, AND DELIBERATELY NOT DIVIDED — the fourteen. The reason is a
                # property of THIS block rather than of the plat, so it is carried on the
                # block's own module with the refusal the authored file wrote for it.
                entry["lots_read_on_the_sheet"] = record["lot_count"]
                entry["subdivision_withheld"] = (
                    "this block prints no dimension that resolves, and a tier-mate's "
                    "figure is not this block's — see `module.lot_subdivision_withheld`")
                entry["alley_local_enu_m"] = None
                entry["lots"] = []
            elif is_west:
                entry["lots_per_column"] = divided["count"]
                entry["alley_local_enu_m"] = divided["alley"]
                entry["lots"] = divided["lots"]
            elif layer["subdivides"]:
                entry["lots_per_face"] = divided["count"]
                entry["alley_local_enu_m"] = divided["alley"]
                entry["lots"] = divided["lots"]
            else:
                # Built, and deliberately NOT divided. The reason is a property of the
                # plat, so it is carried once on the module and pointed at from here.
                entry["subdivision_withheld"] = (
                    "no lot rule has been read for this plat "
                    "— see `module.lot_subdivision_withheld`")
                entry["alley_local_enu_m"] = None
                entry["lots"] = []
            entry["ground"] = ground_reading(ring, field)
            entry["survey_tract"] = tract_of(ring, tracts)
            if is_west:
                entry["module"] = west_module_for(entry, record, figure, west)
                stamp_west_numbers(entry, record)
            else:
                entry["module"] = (dict(addition) if not layer["subdivides"]
                                   else module_for(entry, bounded_by, west, spacing_ft))
            hold = reserved.get(block_id)
            if hold:
                # The boundary stays; the subdivision goes. `lots_per_face` reports what
                # the module WOULD have drawn, so the withdrawal is visible here rather
                # than looking like a block the generator failed on.
                entry["reserved"] = {
                    "reserved_for": hold["reserved_for"],
                    "name": hold["name"],
                    "confidence": hold["confidence"],
                    "sources": hold["sources"],
                    "authored_in": "data/reconstruction/1835_reserved_ground.json",
                    "note": "This block is not subdivided. See the reservation record for "
                            "the evidence and for what may stand here.",
                }
                entry["lots_per_face_withheld"] = entry.pop("lots_per_face")
                entry["alley_local_enu_m"] = None
                entry["lots"] = []
            blocks.append(entry)

    # Kinzie's Addition's fifty-two numerals, each onto the cell its own column and tier
    # name. Every one has to land: on a block, on an omission this grid attempted, or on
    # a cell with no committed line on one of its sides.
    for entry in blocks + omitted:
        if entry.get("grid") != "kinzies_addition":
            continue
        record = addition_numbers.get(entry["id"])
        if record:
            stamp_addition_number(entry, record)
    for record, north, south, column in addition_unreachable:
        sides = []
        if column == "west_gore":
            sides.append("the Addition's west boundary rule")
        elif column == "east_of_sand":
            sides.append("the lake shore")
        if south is None:
            sides.append("the river")
        elif north is None:
            sides.append("the Addition's north boundary")
        side = " and ".join(sides)
        cell = {
            "id": f"kinzies_addition_block_{record['number']}",
            "grid": "kinzies_addition",
            "bounded_by": {"north": north, "south": south,
                           "column": record["column_name"], "tier": record["tier"]},
            "reason": (f"this cell is closed by {side}, which is not a committed "
                       "street line, so this grid has no cell to draw "
                       "— the numeral is carried here rather than lost"),
        }
        stamp_addition_number(cell, record)
        omitted.append(cell)
    if addition_doc is not None:
        landed = {o["plat_block_number"]["number"]
                  for o in blocks + omitted
                  if o.get("grid") == "kinzies_addition" and o.get("plat_block_number")}
        lost = sorted(r["number"] for r in addition_doc["blocks"]
                      if r["number"] not in landed)
        if lost:
            raise SystemExit(
                "data/traces/kinzie_addition_block_numbering.json numbers "
                f"{', '.join(str(n) for n in lost)}, which this grid neither builds "
                "nor omits")

    # AND ALL TWENTY-TWO WEST DIVISION BLOCKS MUST LAND, on a cut cell or on an
    # omission that names what closes it. Seven of them lean on a line this project does
    # not hold — the plat's north and south town lines, and the South Branch where it
    # cuts block 22 to a wedge — so the grid never reaches their cells at all and they
    # would otherwise be absent rather than refused. The Addition's fifty-two numerals
    # are carried the same way and for the same reason: a reading that disappears
    # between two tools is a reading nobody can audit.
    for entry in omitted:
        if entry.get("grid") != "west_division" or entry.get("plat_block_number"):
            continue
        bounded = entry.get("bounded_by") or {}
        found = west_table.get((bounded.get("north"), bounded.get("south"),
                                bounded.get("west"), bounded.get("east")))
        if found:
            # An omission the grid ATTEMPTED — a centreline that stops short, ground the
            # terrain does not model — still had a numeral on the plat. It is carried for
            # the same reason as the cells below, which the grid never reaches at all.
            entry["plat_block_number"] = west_number_record(found)
            entry["lots_the_reading_gives"] = found["lot_count"]
    for key, record in west_table.items():
        if key in west_reached:
            continue
        north, south, column_west, column_east = key
        closed = []
        if north is None or south is None:
            closed.append("the plat's " + ("north" if north is None else "south")
                          + " town line")
        if column_west is None or column_east is None:
            closed.append("the South Branch of the Chicago River")
        cell = {
            "id": f"blk_west_{record['tier'].replace(' ', '_').replace('-', 'to').lower()}"
                  f"_{record['plat_block_number']}",
            "grid": "west_division",
            "bounded_by": {"north": north, "south": south,
                           "west": column_west, "east": column_east,
                           "tier": record["tier"]},
            "plat_block_number": west_number_record(record),
            "reason": (f"this cell is closed by {' and '.join(closed)}, which is not a "
                       "committed street line, so this grid has no cell to draw — the "
                       "block's numerals and its lot count are carried here rather "
                       "than lost"),
            "lots_the_reading_gives": record["lot_count"],
        }
        omitted.append(cell)
    landed = {o["plat_block_number"]["number"]
              for o in blocks + omitted
              if o.get("grid") == "west_division" and o.get("plat_block_number")}
    lost = sorted(r["plat_block_number"] for r in west_table.values()
                  if r["plat_block_number"] not in landed)
    if lost:
        raise SystemExit(
            "data/traces/thompson_west_division_lots.json reads block(s) "
            f"{', '.join(str(n) for n in lost)}, which this grid neither builds nor omits")

    scheme = numbering_doc["lot_numbering"]
    for entry in blocks:
        record = numbers.get(entry["id"])
        if record:
            stamp_number(entry, record, scheme)
    for entry in omitted:
        record = numbers.get(entry["id"])
        if record:
            # A block the grid cannot draw still had a number on the plat. Carrying it
            # here keeps the two facts — the plat numbered it, this project cannot
            # place it — in one place instead of one contradicting the other's absence.
            entry["plat_block_number"] = {
                "number": record["number"],
                "confidence": record["confidence"],
                "numeral_on_sheet": record["numeral_on_sheet"],
                "sources": record["sources"],
                "authored_in": "data/traces/thompson_block_numbering.json",
                "note": record["note"],
            }
    unplaced = sorted(set(numbers) - {b["id"] for b in blocks} - {o["id"] for o in omitted})
    if unplaced:
        raise SystemExit("data/traces/thompson_block_numbering.json numbers "
                         f"{', '.join(unplaced)}, which the grid neither builds nor omits")

    # T-1454. The two seated tracts, cut on their own committed seatings rather than on
    # street centrelines this project does not hold for them. They join the same list as
    # everything above and take the same ground reading, the same survey-tract sort and
    # the same summary, so a placement ticket asks ONE layer for a lot and not three.
    seated = seated_tracts()
    for tract in seated:
        for cell in tract["cells"]:
            ring = cell["boundary_local_enu_m"]
            # THE SAME CORNER RULE THE GRIDS ABOVE ARE HELD TO, and it is not a
            # formality here: eight of Wabansia's twenty-one cells fail it. A cell the
            # plat emits is a cell the roof schedule will deal to, and a placement onto
            # ground the terrain does not model dies inside the infill generator — which
            # is what tools/measure_southern_ground.py --gate refuses on behalf of. So a
            # cell with a corner off the modelled field or under datum is carried in
            # `omitted`, with the blocker named and its numeral still on it.
            off = [p for p in ring if not field.covers(*p)]
            wet = [p for p in ring if field.covers(*p) and field.height(*p) < 0.0]
            if off or wet:
                omission = {
                    "id": cell["id"],
                    "grid": cell["grid"],
                    "bounded_by": cell["bounded_by"],
                    "reason": _seated_blocker(off, wet, ring, field),
                    "would_be_boundary_local_enu_m": ring,
                    "lots_the_reading_gives": len(cell["lots"]),
                }
                if cell.get("plat_block_number"):
                    omission["plat_block_number"] = cell["plat_block_number"]
                omitted.append(omission)
                continue
            cell["ground"] = ground_reading(ring, field)
            cell["survey_tract"] = tract_of(ring, tracts)
            cell["module"] = dict(tract["module"])
            blocks.append(cell)

    return assemble(blocks, omitted, module, alley_m, frontage_m, reach_m, lines,
                    numbering_doc, tracts, west, spacing_ft, layers, addition,
                    addition_doc, seated)


def _count_tracts(blocks: list) -> dict:
    counts: dict[str, int] = {}
    for block in blocks:
        key = block["survey_tract"]["tract"] or "no placed ring covers it"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def assemble(blocks, omitted, module, alley_m, frontage_m, reach_m, lines,
             numbering_doc, tracts, west, spacing_ft, layers, addition,
             addition_doc, seated) -> dict:
    faces = [lot["frontage_m"] for b in blocks for lot in b["lots"]]
    by_grid = {}
    for layer in layers:
        mine = [b for b in blocks if b["grid"] == layer["id"]]
        by_grid[layer["id"]] = {
            "plat": layer["plat"],
            "name": layer["name"],
            "bounded_between": {"east_west": layer["rows"], "north_south": layer["columns"]},
            "blocks": len(mine),
            "omitted": sum(1 for o in omitted if o.get("grid") == layer["id"]),
            "numbered": sum(1 for b in mine if b.get("plat_block_number")),
            "lots": sum(len(b["lots"]) for b in mine),
            "subdivided": layer["subdivides"],
            "divides_on": layer["divides_on"],
            "built_and_not_divided": sum(1 for b in mine if b.get("subdivision_withheld")),
        }
    for tract in seated:
        mine = [b for b in blocks if b["grid"] == tract["id"]]
        by_grid[tract["id"]] = {
            "plat": tract["plat"],
            "name": tract["name"],
            "cut_from": {"seating": tract["seated_in"], "reading": tract["read_in"]},
            "blocks": len(mine),
            "omitted": 0,
            "numbered": sum(1 for b in mine if b.get("plat_block_number")),
            "lots": sum(len(b["lots"]) for b in mine),
            "subdivided": True,
        }
    return {
        "_doc": (
            "The platted block and lot grid, generated from the Thompson module and snapped "
            "to this project's committed street lines — never traced off the 1834 sheets, "
            "whose 3.7-4.5% anisotropic stretch would arrive as 4% of wobble in every block "
            "face. A block edge here is a street centreline from data/streets/1835.json "
            "offset by half the platted corridor; a lot line is the module divided into it. "
            "Written by tools/generate_plat_lots.py, which re-derives this file byte for byte "
            "offline on every commit (tools/check.sh). Block ids name the streets that bound "
            "a block, which is a description and not a claim. Thompson's own block NUMBERS "
            "are carried separately, in `plat_block_number`, read block by block off the "
            "georeferenced Wright 1834 scan — see `block_numbering` below and "
            "data/traces/thompson_block_numbering.json. A block left unnumbered here is one "
            "the sheet was not read on, and the authored file says which and why. "
            "SINCE T-1455 THIS FILE HOLDS FIVE GRIDS, not one: the Original Town south "
            "of the main stem, Kinzie's Addition north of it and the West Division west "
            "of the South Branch, each cut between its own committed street lines at its "
            "own corridor width and divided on its own module; and the Michigan Street "
            "tract and Wabansia, which are cut on their own committed SEATINGS instead, "
            "because the lines that rule them — the tracts' own borders, their mid-block "
            "alleys, Wabansia's block columns — are not streets any street table carries. "
            "Every block says which in `grid`, and `grids` below says where each one was "
            "cut from and what it may be divided on. The Addition's blocks carry no lots "
            "on purpose (`subdivision_withheld`: no lot rule has been read for that "
            "plat); the two seated tracts carry the lot lines Wright rules INSIDE them, "
            "which is the first lot line in this file that is a reading rather than a "
            "module divided into a block; and the West Division is divided BLOCK BY "
            "BLOCK, on each block's own printed figure and its own counted numerals, "
            "with no lot lines at all in the blocks that print no figure."),
        "tool": "tools/generate_plat_lots.py",
        "generated_from": [
            "data/traces/street_control.json",
            "data/streets/1835.json",
            "data/sources/thompson_plat_1830.json",
        ],
        "sources": SOURCE_IDS,
        "grids": by_grid,
        "kinzies_addition": {
            "why_it_is_a_second_grid": (
                "Until T-1437 one pair of street lists decided which lines a block could "
                "be cut between, and both were Original Town lines, so the only lots in "
                "this file stopped at the river. The Addition is a different plat with a "
                "different draughtsman, a different corridor (22.17 m against 24.384) and "
                "a different module, and a cell straddling two sheets is a cell neither "
                "sheet draws. It gets its own pair."),
            "module": {k: v for k, v in addition.items()
                       if k not in ("lot_subdivision_withheld",)},
            "lot_subdivision_withheld": addition["lot_subdivision_withheld"],
            "numbering": {
                "authored_in": "data/traces/kinzie_addition_block_numbering.json",
                "read": (addition_doc or {}).get("why_this_file_exists"),
                "scheme": ((addition_doc or {}).get("scheme") or {}).get("run"),
                "grades": (addition_doc or {}).get("grades"),
                "refused": [r["scope"] for r in ((addition_doc or {}).get("refused") or [])],
                "how_a_numeral_reaches_a_block": (
                    "by the cell's OWN `column_name` and `tier`, never by counting from a "
                    "neighbour: the column names the two lines the cell stands between and "
                    "the tier is numbered from the river upward under the file's own "
                    "scheme. A cell whose column or tier has no committed line on one side "
                    "— the west gore, the ground east of Sand Street, the river tier "
                    "and the tier above Superior Street — reaches no cell of this "
                    "grid, and its numeral is carried on an omission so that all "
                    "fifty-two are accounted for rather than quietly dropped."),
            },
        },
        "module": {
            "street_width_m": module["width_m"],
            "street_width_ft": module["width_ft"],
            "street_confidence": module["confidence"],
            "alley_width_m": alley_m,
            "alley_width_ft": ALLEY_FT,
            "alley_confidence": "reconstructed",
            "alley_note": (
                "18 ft is the module the Thompson plat source record carries and the figure "
                "the 1834 traverses read (17.1-18.7 ft), so the WIDTH is as well attested as "
                "the street. Everything else about it is not: nothing in data/sources/ says "
                "which blocks were alleyed, or whether the alley ran with the long axis of a "
                "block or across it. The mid-block east-west alley generated here is the "
                "arrangement the lot rows on Wright's block 18 imply, and it is a conjecture "
                "in exactly the way its confidence says. The 16 ft dissent recorded in "
                "data/traces/street_control.json is not settled by the traverses: two feet is "
                "inside that method's error."),
            "lot_frontage_m": frontage_m,
            "lot_frontage_ft": LOT_FRONTAGE_FT,
            "lot_confidence": "reconstructed",
            "lot_note": (
                "Four lots to a block face, 80 ft each, is a reading of ONE block: the owner's "
                "crop of Wright's sheet at the Clark reach carries block 18's north row "
                "numbered 4 3 2 and its south row 5 6 7 "
                "(docs/RESEARCH/clark_reach_bulge_1834.md § 8), which is four lots across a "
                "block of about 320 ft. Applying it to the other blocks is inference from a "
                "single instance and it is graded as the conjecture it is. Lots carry a "
                "`plat_lot_number` ONLY inside a numbered block, under the scheme the same "
                "crop shows on block 18 — 1-4 east to west along the north row, 5-8 west to "
                "east along the south row — and that number is `conjectural` wherever it "
                "appears, because it is put on a line no sheet drew. Nothing else in this "
                "file is numbered: a numbering invented to look complete is exactly what "
                "this project does not do."),
        },
        "survey_tract_layer": {
            "why_this_section_exists": (
                "T-1105. Until T-1101 built the survey-tract layer this generator chose ONE "
                "street width and ONE block module for the whole town because there was no "
                "layer to ask, and the choice was invisible: nothing on a block said which "
                "survey it stood in or which module it had been given. Both are now stamped "
                "on every block, so a block that takes the Original Town's module takes it "
                "on the record."),
            "read": "data/reconstruction/1835_survey_tracts.json",
            "rings_read": [t["id"] for t in tracts],
            "rule": (
                "a block takes the tract that covers the most of it, by clipped area, using "
                "the clipper in tools/sort_land_sales_onto_tracts.py"),
            "the_precedence_clause": (
                "EXCEPT that a residual tract — one whose ring is defined as what another "
                "tract leaves over — yields any block a non-residual tract covers at least "
                "50% of. canal_section_9_remainder is the layer's only residual. T-1104 "
                "states this clause for parcels; a second statement of it would be a second "
                "answer, so it is the same clause and the same clipper."),
            "what_the_layer_answers_here": {
                "blocks_sorted": len(blocks),
                "by_tract": _count_tracts(blocks),
                "finding": (
                    "THE LAYER DISCRIMINATES THIS GRID SINCE T-1437, and until then it "
                    "could not. The finding recorded here from T-1105 to 2026-09-20 was "
                    "that all nineteen generated blocks fell in canal_commissioners_1830 "
                    "and no other placed ring touched one, so the question T-1105 asked "
                    "the layer was one the layer could not answer. That was a property of "
                    "the GRID and not of the layer: the generator could only cut blocks "
                    "between Original Town lines, so of course every block stood in the "
                    "Original Town's tract. With Kinzie's Addition's own grid cut, "
                    + ", ".join(f"{n} block(s) stand in {t}"
                                for t, n in sorted(_count_tracts(blocks).items()))
                    + " — and the module each takes is now a per-tract answer rather "
                    "than a single town-wide one. What varies INSIDE the Original Town's "
                    "tract is still the DIVISION, because the river runs through it and "
                    "the plat gives its two sides different blocks."),
                "the_grade_is_inherited": (
                    "canal_commissioners_1830 is `conjectural` — its four bounds are the "
                    "standard account of the 1830 plat and no source record here states "
                    "them. Any module chosen off that ring would be conjectural for that "
                    "reason alone. None is: the module below is chosen off the street "
                    "lines, and the tract is carried as a finding, not used as an input."),
            },
            "the_west_division_module": {
                "held": west["authored_in"],
                "confidence_of_the_figures": west["confidence"],
                "printed": (
                    f"lots {west['printed_frontage']} ft on the front and "
                    f"{west['lot_depth_ft']:.0f} ft deep, two columns backing onto an "
                    f"{west['alley_width_ft']:.0f} ft NORTH-SOUTH alley, the block square "
                    f"at {west['block_east_west_ft']:.0f} ft, the street module "
                    f"{west['street_module_ft']:.0f} ft"),
                "streets_it_governs": sorted(west["streets"]),
                "blocks_of_this_grid_inside_it": sorted(
                    b["id"] for b in blocks
                    if "west_division_module_refused" in b["module"]),
                "refused_on_every_one_of_them": (
                    "and the refusal is arithmetic, not preference. Two lot columns alone "
                    f"need {2 * west['lot_depth_ft']:.0f} ft; the committed faces west of "
                    "the river are "
                    + ", ".join(
                        f"{b['module']['west_division_module_refused']['what_the_committed_lines_give']['east_west_face_ft']:.1f} ft"
                        for b in blocks if "west_division_module_refused" in b["module"])
                    + ". The arrangement does not fit before the alley is cut."),
                "what_is_short_is_the_spacing_not_the_module": (
                    f"Clinton to Canal is committed at {spacing_ft:.1f} ft against the "
                    f"plat's {west['street_module_ft']:.0f} ft — "
                    f"{west['street_module_ft'] - spacing_ft:.1f} ft short, the same "
                    "finding tools/measure_west_division_module.py reports and the owner "
                    "reported on 2026-08-31. Seating the printed module means moving those "
                    "centrelines, which is T-0445 and is deliberately not done here: this "
                    "generator writes what the committed lines give and records what the "
                    "sheet asks for beside it."),
                "what_would_change_if_the_lines_moved": (
                    "these two blocks would be subdivided the other way about — columns "
                    "and a north-south alley instead of faces and an east-west one — so "
                    "this is a refusal that will be worth revisiting the day T-0445 "
                    "settles the spacing, and not before."),
                "and_since_t_1455_the_division_has_its_own_grid": (
                    "`west_division` above cuts the other twenty of the sheet's "
                    "twenty-two West Division blocks, on the West Division's own tier "
                    "lines and in the West Division's own arrangement. It does NOT seat "
                    "the printed module at its printed size either — that is still "
                    "T-0445's — it cuts the printed arrangement and the counted rows into "
                    "the block the committed lines give and publishes the shortfall on "
                    "each block as `closure_against_the_committed_lines`. The two blocks "
                    "listed here are the ones both grids can reach; they stay on this "
                    "grid, because moving them moves lot lines that committed structure "
                    "records are seated against, and they are carried in the West "
                    "Division grid's omissions with that said."),
            },
            "omitted_blocks_carry_no_tract": (
                "an omitted block has no ring to clip, by definition — it is omitted "
                "because the grid could not draw one — so it is sorted onto no tract "
                "rather than onto one guessed from its bounding streets"),
        },
        "method": {
            "block_edge": ("a street centreline offset by half the platted corridor "
                           f"({module['half_width_m']} m), the four offsets intersected"),
            "reach_m": reach_m,
            "reach_note": (
                "A block is emitted only where the committed centrelines of all four of its "
                "bounding streets reach it, allowing at most half a corridor of extension for "
                "a line drawn to a junction rather than through it. Everything refused is in "
                "`omitted` with the street that falls short, which is the same list of street "
                "control ROADMAP § S9 still records as owed."),
            "max_pitch_m": MAX_PITCH_M,
            "water_rule": ("a block with a corner on water or beyond the modelled ground is "
                           "omitted rather than drawn over the river"),
            "ground_reading": (
                f"every block that IS drawn carries a `ground` reading sampled off the "
                f"committed e1834_harbor_cut heightfield on a {GROUND_STEP_M:.0f} m "
                "lattice cut from the block's own bounding box: how many samples stand "
                "below datum and how many fall off the modelled field, with the heights. "
                "The corner rule above refuses a block outright; this says what the "
                "ground is like inside the ones it lets through, which is what a "
                "placement ticket has to ask before it deals a roof onto one."),
            "lot_subdivision": ("the block's north and south faces divided in the same "
                                "proportion, joined station to station, with a centred "
                                "alley taken out of the middle"),
        },
        "block_numbering": {
            "authored_in": "data/traces/thompson_block_numbering.json",
            "read": numbering_doc["reading"]["what_it_carries"],
            "source": numbering_doc["reading"]["source"],
            "step": numbering_doc["reading"]["step"],
            "direction": numbering_doc["reading"]["direction"],
            "lot_scheme": numbering_doc["lot_numbering"]["scheme"],
            "lot_confidence": numbering_doc["lot_numbering"]["confidence"],
            "refused": [r["scope"] for r in numbering_doc["refused"]],
            "note": ("Each numeral is read on a crop cut to that block's own committed "
                     "ground, so the reading is identified by the georeference rather than "
                     "counted from a neighbour. `numeral_on_sheet` on each block says which "
                     "numbers are read and which are not, and the authored file carries the "
                     "reading, the crop regions and the refusals in full."),
        },
        "confidence": "inferred",
        "confidence_note": (
            "The blocks are arithmetic on inferred inputs — street lines whose own geometry "
            "confidence is `inferred`, offset by a module width the street control also grades "
            "`inferred` — so `inferred` is the most this grid can carry. The lots and the "
            "alleys inside those blocks are `conjectural` and are recorded separately for that "
            "reason: a visitor is entitled to know that the block face is a defensible "
            "position and the line dividing it is not."),
        "summary": {
            "blocks": len(blocks),
            "blocks_by_grid": {k: v["blocks"] for k, v in by_grid.items()},
            "omitted": len(omitted),
            "reserved": sum(1 for b in blocks if b.get("reserved")),
            "numbered": sum(1 for b in blocks if b.get("plat_block_number")),
            "numbered_omitted": sum(1 for o in omitted if o.get("plat_block_number")),
            "lots": sum(len(b["lots"]) for b in blocks),
            "numbered_lots": sum(1 for b in blocks for l in b["lots"]
                                 if l.get("plat_lot_number")),
            "block_frontage_ft": {
                "min": round(min((b["frontage_ft"] for b in blocks), default=0.0), 1),
                "median": round(sorted(b["frontage_ft"] for b in blocks)[len(blocks) // 2], 1)
                if blocks else 0.0,
                "max": round(max((b["frontage_ft"] for b in blocks), default=0.0), 1),
            },
            "lot_frontage_ft": {
                "min": round(min(faces, default=0.0) / FT_M, 1),
                "max": round(max(faces, default=0.0) / FT_M, 1),
            },
        },
        "blocks": blocks,
        "omitted": omitted,
    }


# ---------------------------------------------------------------- the cross-check

def corridor_rings(lines: dict, half_width: float) -> dict:
    """The platted corridor of every street in the corridor layer, as a closed ring.

    A corridor is only as long as the centreline this project has committed, so a
    building beyond a street's drawn end is not reported as standing in it.

    Since T-1191 the layer is `CORRIDOR_EW`/`CORRIDOR_NS` — the block grid plus the
    north bank — and each ring is cut at the street's OWN corridor width, so Kinzie's
    Addition's 22.17 m corridors are not drawn as the Original Town's 24.384 m ones.
    `half_width` remains the fallback for records that declare no width of their own.
    """
    rings = {}
    for street_id, street in lines.items():
        if street_id in CORRIDOR_EW:
            left, right = (0.0, 1.0), (0.0, -1.0)
        elif street_id in CORRIDOR_NS:
            left, right = (-1.0, 0.0), (1.0, 0.0)
        else:
            continue
        own = _half_width(street, half_width)
        a = offset_polyline(street["points"], own, left)
        b = offset_polyline(street["points"], own, right)
        rings[street_id] = a + list(reversed(b))
    return rings


def point_to_ring_m(point, ring) -> float:
    """Shortest distance from a point to a ring's edges."""
    best = float("inf")
    px, py = point
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
        best = min(best, math.dist(point, (ax + dx * t, ay + dy * t)))
    return best


def world_footprint(record: dict) -> list:
    """A sidecar's footprint polygon in local ENU, oriented and placed."""
    placement = record["placement"]
    theta = math.radians(float(placement.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0, n0 = float(placement["local_e"]), float(placement["local_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos)
            for u, v in record["footprint"]["polygon"]]


def report(grid: dict) -> int:
    """Where the dataset's own buildings fall on this grid."""
    from plat_corridors import intrusion  # noqa: PLC0415 - avoids an import cycle

    control = load(DATA / "traces" / "street_control.json")
    half_width = float(control["platted_street"]["half_width_m"])
    lines = street_lines(load(DATA / "streets" / "1835.json"))
    corridors = corridor_rings(lines, half_width)
    lanes = {sid: {"name": lines[sid]["name"], "ring": ring, "points": lines[sid]["points"]}
             for sid, ring in corridors.items()}
    rings = {b["id"]: [tuple(p) for p in b["boundary_local_enu_m"]] for b in grid["blocks"]}
    footprint_hits = []

    placed = 0
    in_block, in_street, off_grid = [], [], []
    for path in sorted(SIDECARS.glob("*.json")):
        record = load(path)
        placement = record.get("placement") or {}
        if placement.get("local_e") is None:
            continue
        point = (float(placement["local_e"]), float(placement["local_n"]))
        if point == (0.0, 0.0):
            continue
        placed += 1
        confidence = placement.get("position_confidence")
        home = next((bid for bid, ring in rings.items() if point_in_polygon(point, ring)), None)
        street = next((sid for sid, ring in corridors.items()
                       if point_in_polygon(point, ring)), None)
        if home:
            in_block.append((record["id"], point, confidence, home, 0.0))
        elif street:
            in_street.append((record["id"], point, confidence, street,
                              point_to_ring_m(point, corridors[street])))
        else:
            off_grid.append((record["id"], point, confidence, None, 0.0))
        lane, depth = intrusion(world_footprint(record), lanes)
        if lane:
            footprint_hits.append((record["id"], confidence, lane, depth))

    print(f"{placed} placed structures against {len(rings)} generated blocks:")
    print(f"  {len(in_block):4d} stand inside a block")
    print(f"  {len(in_street):4d} stand INSIDE A PLATTED STREET CORRIDOR")
    print(f"  {len(off_grid):4d} stand outside this grid altogether (the Thompson North "
          "Division tier, the fort, the West Division beyond Clinton, Kinzie's Addition "
          "river tier and the blocks in `omitted`)")
    by_confidence = {}
    for _, _, confidence, _, _ in in_street:
        by_confidence[confidence] = by_confidence.get(confidence, 0) + 1
    if in_street:
        print("\nin a street corridor, by position confidence: "
              + ", ".join(f"{k}: {v}" for k, v in sorted(by_confidence.items(), key=str)))
        print("`depth` is how far the record's centre lies inside the corridor. Anything "
              "under a few metres is inside the georeference's own ±20 m and says little; a "
              "centre 8-12 m in is a building standing in the middle of the street.")
        for sid, point, confidence, street, depth in sorted(in_street, key=lambda r: -r[4]):
            print(f"  - {sid:44s} ({point[0]:8.1f}, {point[1]:8.1f})  "
                  f"{str(confidence):12s} {lines[street]['name']:20s} depth {depth:5.1f} m")

    # A centre in the road is the loud case; a FOOTPRINT in the road is the common one,
    # and it is the question the placement gate in tools/generate_inferred_households.py
    # actually asks. The two lists differ because a building can front a street with its
    # centre well clear of the corridor and half its depth inside it.
    if footprint_hits:
        print(f"\n{len(footprint_hits)} structure(s) put some part of a footprint inside a "
              "platted corridor. The plat is the LEGAL corridor, not the travelled way "
              "(L79: 5.8-10.5 m of visible track inside 80 ft), so this is a measurement "
              "against the plat rather than a list of defects — but no generated placement "
              "is allowed to be here.")
        for sid, confidence, lane, depth in sorted(footprint_hits, key=lambda r: -r[3]):
            print(f"  - {sid:44s} {str(confidence):12s} {lanes[lane]['name']:20s} "
                  f"reaches {depth:5.1f} m in")
    return 0


def self_test() -> int:
    """The crossed-corner refusal fires, and it fires on the case that produced it.

    T-0183. The owner ruled on 2026-08-29 that South Water Street's committed west end
    should be CLOSED onto Market's corridor. Executed on the line as committed, that
    closure does not open `blk_south_water_market`: South Water's west approach has already
    converged onto Lake Street by the time it reaches Market, so the block's north-west
    corner falls south of its south-west one and the ring is a bowtie. This rebuilds that
    exact case from the committed inputs and asserts the refusal, so nobody has to take the
    measurement on trust — and asserts a real block still builds, so the guard cannot pass
    by refusing everything.
    """
    import copy  # noqa: PLC0415

    streets = load(DATA / "streets" / "1835.json")
    control = load(DATA / "traces" / "street_control.json")
    half_width = float(control["platted_street"]["half_width_m"])
    cases, failed = 0, 0

    def build(doc):
        lines = street_lines(doc)
        return lines, build_block("south_water", "lake", "market", "franklin",
                                  lines, block_edges(lines, half_width), half_width)

    # 1. As committed: the north row simply does not reach the block.
    cases += 1
    _, (built, why) = build(streets)
    if built is not None or "stops" not in (why or ""):
        print(f"  NOT REFUSED as committed: {why}")
        failed += 1
    else:
        print(f"  ok:    as committed \u2014 {why}")

    # 2. Closed onto Market's corridor: the crossing is found, and the corners are inverted.
    closed = copy.deepcopy(streets)
    for street in closed["streets"]:
        if street["id"] == "south_water":
            street["path_local_enu_m"] = [[89.27, -101]] + street["path_local_enu_m"]
    cases += 1
    lines, (built, why) = build(closed)
    if built is not None or "have crossed" not in (why or ""):
        print(f"  GUARD DID NOT FIRE on the closed west end: {why}")
        failed += 1
    else:
        print(f"  fires: the closure the ruling asks for \u2014 {why}")

    # 3. And the guard is not refusing everything: the block east of it still builds.
    cases += 1
    lines = street_lines(streets)
    built, why = build_block("south_water", "lake", "franklin", "wells",
                             lines, block_edges(lines, half_width), half_width)
    if built is None:
        print(f"  A REAL BLOCK WAS REFUSED: {why}")
        failed += 1
    else:
        print("  ok:    blk_south_water_franklin still builds "
              f"({polygon_area(built['ring']):.0f} m2)")

    # 4. AND THE GROUND IS THE REASON, not the drawn line. Push South Water as far north
    #    at Market's easting as the committed heightfield allows — its north corridor edge
    #    exactly on the waterline — and measure what is left between it and Lake Street.
    #    If that ever exceeds a lot's own depth the finding recorded on
    #    `refused_control.market_south_water` is stale and wants re-reading.
    cases += 1
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from heightfield import Heightfield  # noqa: PLC0415
        field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    except Exception as exc:  # pragma: no cover - the field is committed
        print(f"  the committed heightfield did not load: {exc}")
        return 1
    market = next(s for s in streets["streets"] if s["id"] == "market")
    lake = next(s for s in streets["streets"] if s["id"] == "lake")
    corner_e = market["path_local_enu_m"][-1][0]
    waterline = -140.0
    while waterline < 60.0:
        if not (field.covers(corner_e, waterline) and field.height(corner_e, waterline) >= 0.0):
            break
        waterline += 0.1
    lake_line = [(float(e), float(n)) for e, n in lake["path_local_enu_m"]]
    lake_n = next(a[1] + (corner_e - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
                  for a, b in zip(lake_line, lake_line[1:]) if a[0] <= corner_e <= b[0])
    headroom = (waterline - 2 * half_width) - (lake_n + half_width)
    if headroom > LOT_FRONTAGE_FT * FT_M:
        print(f"  THE GROUND HAS CHANGED: {headroom:.1f} m of block depth at Market now")
        failed += 1
    else:
        print(f"  ok:    the ground, not the line \u2014 South Water carried as far north at "
              f"Market as the committed waterline (local N {waterline:.1f}) allows leaves "
              f"{headroom:.1f} m between it and Lake Street")

    # 5. T-1105. The survey-tract layer is asked, and the West Division refusal is
    #    re-derived rather than trusted. Both halves matter: that the layer answers the
    #    same tract for every block is the finding, and that the printed West Division
    #    arrangement will not seat on the committed faces is the reason the refusal
    #    stands. If either stops being true this gate should be the thing that says so.
    cases += 1
    tracts = survey_tracts()
    west = west_division()
    lines = street_lines(streets)
    spacing_ft = abs(lines["clinton"]["mean_e"] - lines["canal"]["mean_e"]) / FT_M
    grid = load(OUT_PATH) if OUT_PATH.exists() else None
    if grid is None:
        print("  the committed grid is missing; nothing to check the layer against")
        failed += 1
    else:
        sorted_to = {t["id"] for t in tracts if any(
            b["survey_tract"]["tract"] == t["id"] for b in grid["blocks"])}
        stated = set(grid["survey_tract_layer"]["what_the_layer_answers_here"]["by_tract"])
        if sorted_to != stated:
            print(f"  THE LAYER'S ANSWER MOVED: blocks now sort onto {sorted(sorted_to)}, "
                  f"the record says {sorted(stated)}")
            failed += 1
        else:
            print(f"  ok:    {len(grid['blocks'])} blocks sort onto {sorted(stated)}, "
                  "which is what the record says")

    cases += 1
    columns_ft = 2 * west["lot_depth_ft"] + west["alley_width_ft"]
    west_blocks = [b for b in (grid["blocks"] if grid else [])
                   if "west_division_module_refused" in b["module"]]
    if not west_blocks:
        print("  NO WEST DIVISION BLOCK on this grid — the refusal has nothing to refuse")
        failed += 1
    else:
        seatable = [b for b in west_blocks
                    if b["frontage_m"] / FT_M >= columns_ft]
        if seatable:
            print("  THE REFUSAL IS STALE: the printed West Division arrangement now "
                  f"seats on {', '.join(b['id'] for b in seatable)} — re-read it")
            failed += 1
        else:
            faces = ", ".join(f"{b['frontage_m'] / FT_M:.1f}" for b in west_blocks)
            print(f"  ok:    the West Division arrangement needs {columns_ft:.0f} ft of "
                  f"face and the committed blocks give {faces} ft; Clinton to Canal is "
                  f"{spacing_ft:.1f} ft against the plat's "
                  f"{west['street_module_ft']:.0f} ft")

    # ------------------------------------------------------------- T-1437, the second grid
    # Three things have to hold at once for Kinzie's Addition to be a grid and not a
    # copy of the Original Town's with different street names: every cell the grid cuts
    # carries the Addition's own numeral, none of them carries a lot, and the faces
    # measure the ADDITION's module rather than the town's. The third is the one that
    # catches a regression nobody would see by eye — a 2.2 m corridor difference over an
    # 89 m block face is the kind of thing that hides in a rounded figure.
    cases += 1
    addition_blocks = [b for b in (grid["blocks"] if grid else [])
                       if b["grid"] == "kinzies_addition"]
    if not addition_blocks:
        print("  NO KINZIE'S ADDITION BLOCK on this grid — the second grid built nothing")
        failed += 1
    else:
        unnumbered = [b["id"] for b in addition_blocks if not b.get("plat_block_number")]
        divided = [b["id"] for b in addition_blocks if b["lots"]]
        if unnumbered or divided:
            print(f"  ADDITION GRID WRONG: {len(unnumbered)} unnumbered, "
                  f"{len(divided)} carrying lots")
            failed += 1
        else:
            print(f"  ok:    {len(addition_blocks)} Kinzie's Addition blocks, every one "
                  "numbered off the sheet and none of them divided")

    cases += 1
    numbering = load(ADDITION_NUMBERING_PATH)
    landed = {e["plat_block_number"]["number"]
              for e in (grid["blocks"] + grid["omitted"] if grid else [])
              if e.get("grid") == "kinzies_addition" and e.get("plat_block_number")}
    lost = sorted(r["number"] for r in numbering["blocks"] if r["number"] not in landed)
    if lost:
        print(f"  NUMERALS LOST: {lost} reach neither a block nor an omission")
        failed += 1
    else:
        print(f"  ok:    all {len(numbering['blocks'])} of the Addition's numerals land "
              "— on a block, or on an omission that says which side is not a street")

    cases += 1
    addition = addition_module()
    interior = [b for b in addition_blocks
                if b["bounded_by"]["west"] != addition["seated_on"][1]]
    expected = addition["column_pitch_m"] - addition["corridor_m"]
    town_would_give = addition["column_pitch_m"] - 2 * half_width
    off = [b["id"] for b in interior if abs(b["frontage_m"] - expected) > 1.0]
    if not interior or off:
        print(f"  THE ADDITION IS NOT ON ITS OWN CORRIDOR: {off or 'no interior block'}")
        failed += 1
    else:
        faces = sorted({round(b["frontage_m"], 1) for b in interior})
        print(f"  ok:    the Addition's interior faces read {faces} m against its own "
              f"module's {expected:.1f} m; the Original Town's corridor would have given "
              f"{town_would_give:.1f} m")

    # T-1454. THE SEATED TRACTS LAND ON THEIR OWN SEATINGS, or the ladder this file
    # interpolates is not the one the seating tool committed. Asserted at the ladder's
    # four extremes, which are the only points where the two derivations have to agree
    # exactly: everything between them is this file's interpolation of them.
    cases += 1
    seated = load(MICHIGAN_SEATING_PATH)
    north, east = (seated["ladder_m"]["off_michigan_northward"],
                   seated["ladder_m"]["off_market_eastward"])
    place = _tract_frame(seated["corners_local_enu_m"],
                         (east["west_border"], east["east_border"]),
                         (north["south_border"], north["north_border"]))
    off = []
    for corner, (u, v) in (("nw", (east["west_border"], north["north_border"])),
                           ("ne", (east["east_border"], north["north_border"])),
                           ("sw", (east["west_border"], north["south_border"])),
                           ("se", (east["east_border"], north["south_border"]))):
        gap = math.dist(place(u, v), seated["corners_local_enu_m"][corner])
        if gap > 0.01:
            off.append(f"{corner} {gap:.3f} m")
    if off:
        print(f"  THE LADDER IS NOT THE SEATING'S: {', '.join(off)}")
        failed += 1
    else:
        print("  ok:    the Michigan Street tract's ladder lands on all four corners "
              "tools/seat_michigan_st_tract.py committed, to the millimetre")

    # …AND EVERY READ LOT ROW CLOSES ON ITS BLOCK inside the sheet's own stretch. This is
    # the check that the lot lines belong to the face they were laid on: if a row had to
    # be scaled past 4.5 per cent, either the reading is short a line or the seating is
    # not that row's, and the file flags it rather than absorbing it.
    cases += 1
    grid = load(OUT_PATH)
    rows = [r for b in grid["blocks"] if b["grid"] == "michigan_st_tract"
            for r in b["lot_rows"]]
    read_rows = [r for r in rows if "scale" in r]
    withheld = [r for r in rows if "subdivision_withheld" in r]
    strained = [f"{r['row']} {abs(r['scale'] - 1) * 100:.1f}%" for r in read_rows
                if abs(r["scale"] - 1.0) > SHEET_STRETCH]
    if len(read_rows) != 5 or len(withheld) != 3 or strained:
        print(f"  THE TRACT'S LOT ROWS DO NOT ANSWER: {len(read_rows)} read, "
              f"{len(withheld)} withheld, strained {strained or 'none'}")
        failed += 1
    else:
        worst = max(abs(r["scale"] - 1.0) for r in read_rows) * 100
        print(f"  ok:    {len(read_rows)} read lot rows close on their seated faces "
              f"within {worst:.1f} per cent, under the sheets' own {SHEET_STRETCH * 100:.1f}; "
              f"the {len(withheld)} faces the reading never reached stay withheld")

    # …AND WABANSIA'S TWENTY-ONE NUMERALS ALL LAND, on a block or on the omission that
    # names its blocker. Eight of them are on omissions today — seven because the
    # modelled ground stops short of the survey's west margin and one because its corner
    # stands in the committed North Branch — and an omission that quietly lost its
    # numeral would read as a survey with nineteen blocks.
    cases += 1
    numbering = load(WABANSIA_NUMBERING_PATH)
    landed = {e["plat_block_number"]["number"]
              for e in grid["blocks"] + grid["omitted"]
              if e.get("grid") == "wabansia" and e.get("plat_block_number")}
    lost = sorted(r["number"] for r in numbering["blocks"] if r["number"] not in landed)
    built = sum(1 for b in grid["blocks"] if b["grid"] == "wabansia")
    skipped = sum(1 for o in grid["omitted"] if o["grid"] == "wabansia")
    if lost or built + skipped != len(numbering["blocks"]):
        print(f"  WABANSIA'S NUMERALS LOST: {lost or 'none'}; {built} built and "
              f"{skipped} omitted against {len(numbering['blocks'])} read")
        failed += 1
    else:
        print(f"  ok:    all {len(numbering['blocks'])} of Wabansia's numerals land — "
              f"{built} on a block, {skipped} on an omission that names its blocker")

    if failed:
        print(f"SELF-TEST FAIL — {failed} of {cases}")
        return 1
    print(f"SELF-TEST PASS — the crossed-corner refusal fires on the case that "
          f"produced it, the ground says why, the survey-tract layer's answer and the "
          f"West Division refusal are both re-derived, and the two seated tracts land on "
          f"their own seatings ({cases} cases)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed grid is not what the inputs re-derive")
    parser.add_argument("--report", action="store_true",
                        help="report where the dataset's structures fall on the grid")
    parser.add_argument("--self-test", action="store_true",
                        help="the crossed-corner refusal fires on the case that produced it")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    grid = grid_from_inputs()
    if args.report:
        return report(grid)

    text = json.dumps(grid, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT_PATH.exists():
            print(f"PLAT GRID DRIFT\n  - {OUT_PATH.relative_to(ROOT)} is missing")
            return 1
        if OUT_PATH.read_text(encoding="utf-8") != text:
            print("PLAT GRID DRIFT\n  - data/traces/vectors/thompson_lots.json is not what "
                  "the module and the committed street lines re-derive")
            return 1
    else:
        OUT_PATH.write_text(text, encoding="utf-8")
    mode = "verified" if args.check else "generated"
    print(f"{mode} {grid['summary']['blocks']} platted blocks "
          f"({grid['summary']['lots']} lots, {grid['summary']['omitted']} omitted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
