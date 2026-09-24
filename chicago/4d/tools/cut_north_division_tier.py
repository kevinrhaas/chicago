#!/usr/bin/env python3
"""Cut the seven Kinzie-to-the-river blocks, and their four-to-a-face lots.

T-1458, the second half of T-1436. `tools/generate_plat_lots.py` cuts a block only
between two committed street lines, and the North Division tier has one: Kinzie bounds
it north and is `attested`, but its south face is the north line of NORTH WATER STREET,
which `data/traces/street_control.json` refuses a corridor because that street's line is
cut from the river bank rather than from a platted rule. So the tier had a width and no
depth, and no block on it could be cut. T-1457 read the sheet DOWN and supplied the
missing figure, per block, as a DEPTH:

    docs/RESEARCH/north_division_tier_depth.md
    data/traces/thompson_north_division_streets.json § north_tier_horizontals_px

This module is the cut that reading paid for. Nothing here re-reads the sheet and
nothing here is typed: every figure comes from `measure_north_division_tier_depth.py`
(the depths, the rows and the alley) or from `data/streets/1835.json` (the seating).

WHAT EACH PART OF THE OUTPUT IS ENTITLED TO CLAIM

* A block's NORTH FACE is committed Kinzie's south kerb — the `attested` centreline
  offset by the `thompson_module_1830` half-width. `inferred`: arithmetic on a committed
  line and the module.
* A block's EAST and WEST faces are the same offset taken on the tier's `attested`
  north-south centrelines. `inferred`, for the same reason. Block 7 alone has no street
  on its west: it ends on the North Branch, and its west face is T-0451's own px-to-
  easting fit applied to the stroke the scan returns there. That one face is
  `conjectural` and says so on itself.
* A block's SOUTH FACE is its north face carried down by the READ depth. This is the
  whole point of T-1457's refusal to publish northings: a depth is a difference taken at
  one easting and survives the sheet's shear, an absolute northing from up there does
  not. So the south face is parallel to committed Kinzie at the read offset, never fitted
  to the sheet's own southern line. `inferred`, with the reading cited per block.
* The two LOT ROWS and the ALLEY between them come from the same reading, per block, and
  they sum to that block's depth by construction. The tier is a WEDGE: the lower row is
  the 180 ft the sheet letters in every block and the upper row absorbs the difference,
  178.6 ft at Franklin to 232.7 at Wolcott. A South Division subdivision — a centred
  alley, two equal rows — would be wrong here by up to 27 ft a row, which is why this
  module exists rather than a `subdivides: True` flag on the other one.
* A LOT LINE is `inferred`, and that is a grade better than the South Division's
  `conjectural` lot lines: those rest on four-to-a-face read in ONE block and carried to
  eighteen, while every lot line on this tier is a VERTICAL STROKE T-0451's column scan
  returned in that block — five to a block, thirty-four across the seven, one of them
  (block 6's middle) swallowed by the watercourse and carried on the module.
* A LOT NUMBER is `inferred`. The sheet letters 4 on the lower row's west lot in every
  block read; the run of the other seven is not lettered here and is taken from the one
  Original Town block whose lot numerals ARE read (block 18, north row 4 3 2 and south
  row 5 6 7 — `docs/RESEARCH/clark_reach_bulge_1834.md` § 8): a row that carries 4 at its
  west end runs 4-3-2-1 west to east, and the other row runs 5-6-7-8 west to east.

WHAT THIS DOES NOT DO. It does not re-grade North Water Street, does not give that
street the corridor the control refuses it, and does not move a committed line. It says
where the BLOCKS stop, which is the only one of the two the plat draws.

    tools/cut_north_division_tier.py           regenerate the committed file
    tools/cut_north_division_tier.py --check   fail if the committed file is not what
                                               this module and the committed lines
                                               re-derive
    tools/cut_north_division_tier.py --self-test  the assertions this cut has to satisfy
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_PATH = DATA / "traces" / "vectors" / "north_division_tier_lots.json"

sys.path.insert(0, str(ROOT / "tools"))
import measure_north_division_tier_depth as depth_reading  # noqa: E402
# The ground reading is the South Division generator's, not a second one written here:
# a block on this tier has to report its ground the same way a block on that grid does,
# or the placement tickets that read both get two different answers to one question.
import generate_plat_lots as south_division  # noqa: E402

FT_M = 0.3048
# The lower row the sheet letters, once in every block read. Quoted from the reading's
# own `lettering` block rather than typed here.
LETTERED_LOWER_ROW_FT = float(
    depth_reading.LETTERED_LOWER_ROW_FT)

# West to east, and the street that closes each block on either side. Block 7 has no
# street on its west — it ends on the North Branch — and carries None.
TIER = [
    ("7", None, "market_north"),
    ("6", "market_north", "franklin_north"),
    ("5", "franklin_north", "wells_north"),
    ("4", "wells_north", "lasalle_north"),
    ("3", "lasalle_north", "clark_north"),
    ("2", "clark_north", "dearborn_north"),
    ("1", "dearborn_north", "wolcott"),
]
# The block the plat draws its watercourse across: two of its four horizontal lines and
# one of its three interior strokes are lost under the freehand banks (T-0452).
CARRIED_BLOCK = "6"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rounded(points, places: int = 2):
    return [[round(e, places), round(n, places)] for e, n in points]


def polygon_area(ring) -> float:
    total = 0.0
    for (e0, n0), (e1, n1) in zip(ring, ring[1:] + ring[:1]):
        total += e0 * n1 - e1 * n0
    return abs(total) / 2.0


def street_line(streets: dict, sid: str) -> list:
    for s in streets["streets"]:
        if s["id"] == sid:
            return s["path_local_enu_m"]
    raise SystemExit(f"data/streets/1835.json has no street {sid}")


def easting_at(path: list, n: float) -> float:
    """Where a north-south centreline stands at northing `n`.

    The tier's columns are two-point lines that lean about a metre over their length, so
    this is the line itself extended, not a guess about where it would have gone: the
    block faces stand inside the drawn extent of every one of them bar the northern few
    metres of Franklin, whose committed line stops at the Kinzie junction it is drawn to.
    """
    (e0, n0), (e1, n1) = path[0], path[-1]
    if n1 == n0:
        return e0
    return e0 + (n - n0) / (n1 - n0) * (e1 - e0)


def northing_at(path: list, e: float) -> float:
    for (e0, n0), (e1, n1) in zip(path, path[1:]):
        if min(e0, e1) <= e <= max(e0, e1):
            t = 0.0 if e1 == e0 else (e - e0) / (e1 - e0)
            return n0 + t * (n1 - n0)
    raise SystemExit(f"the centreline does not reach easting {e:.1f}")


def kerb_chain(path: list, half_width: float, e_west: float, e_east: float) -> list:
    """Kinzie's south kerb between two eastings, keeping the bends that fall inside it.

    The tier's north face is this line and no other. Taking it as a straight run between
    the two faces would smooth away a vertex where one falls inside a block, so the
    vertices are carried.
    """
    stations = [e_west]
    stations += [e for e, _ in path if e_west < e < e_east]
    stations.append(e_east)
    return [(e, northing_at(path, e) - half_width) for e in stations]


def lot_fractions(strokes: list, faces: list) -> tuple[list, str | None]:
    """Where the lot lines stand across a block face, as fractions of the face.

    The strokes are read in PIXELS and applied as PROPORTIONS, which is the same
    discipline the depths obey: the reading supplies the subdivision, the committed
    street lines supply the seating. Reading the strokes as absolute eastings instead
    would put block 5's west face 1.7 m off committed Franklin.
    """
    west, east = faces
    interior = sorted(x for x in strokes if west < x < east)
    span = east - west
    carried = None
    if len(interior) != 3:
        # The stroke the watercourse swallows. Four to a face is what the other six
        # blocks return and what the sheet letters 80 ft across; the missing line is
        # carried on that module rather than the block being left undivided.
        have = [(x - west) / span for x in interior]
        want = [0.25, 0.5, 0.75]
        filled = []
        for target in want:
            near = [f for f in have if abs(f - target) < 0.08]
            filled.append(near[0] if near else target)
        carried = (f"{3 - len(interior)} of the block's three interior strokes are not "
                   "returned by the scan and are carried on the four-to-a-face module; "
                   "the rest are read")
        return filled, carried
    return [(x - west) / span for x in interior], carried


def heightfield():
    from heightfield import Heightfield  # noqa: PLC0415
    return Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")


def derive() -> dict:
    reading = load(DATA / "traces" / "thompson_north_division_streets.json")
    streets = load(DATA / "streets" / "1835.json")
    control = load(DATA / "traces" / "street_control.json")
    half_width = float(control["platted_street"]["half_width_m"])

    measured = depth_reading.derive()
    rows = {b["id"]: b for b in measured["blocks"]}
    a_s, b_s = measured["south_line"]
    a_n, _ = measured["fit"]
    north_face_line = depth_reading.fit_line(
        [(reading["north_tier_horizontals_px"]["blocks"][i]["x_mid_px"],
          reading["north_tier_horizontals_px"]["blocks"][i]["north_face"])
         for i in depth_reading.TIER_BLOCKS])

    faces_px = reading["north_tier_blocks"]["faces_px"]
    strokes_px = reading["north_tier_strokes_px"]
    kinzie = street_line(streets, "kinzie")
    field = heightfield()
    numbering = {"lower": [4, 3, 2, 1], "upper": [5, 6, 7, 8]}

    blocks = []
    for number, west_id, east_id in TIER:
        px_west, px_east = faces_px[number]
        carried_depth = None
        if number in rows:
            row = rows[number]
            depth_m = row["depth_m"]
            upper_m, alley_m, lower_m = (row["upper_row_m"], row["alley_m"],
                                         row["lower_row_m"])
            depth_from = "read"
        else:
            # Carried on the tier line: the south face fitted through the five blocks
            # that share it, against the north face fitted through the same five, both
            # evaluated at this block's own mid-easting. A difference at one easting, so
            # the reading's refusal to publish northings is not broken by it.
            x_mid = (px_west + px_east) / 2.0
            depth_m = ((a_s * x_mid + b_s)
                       - (north_face_line[0] * x_mid + north_face_line[1])) * -a_n
            lower_m = LETTERED_LOWER_ROW_FT * FT_M
            alley_m = sum(rows[i]["alley_m"] for i in depth_reading.TIER_BLOCKS) / len(
                depth_reading.TIER_BLOCKS)
            upper_m = depth_m - alley_m - lower_m
            depth_from = "carried"
            carried_depth = (
                "block 6's two middle lines are lost under the freehand banks of the "
                "watercourse the plat draws across it (T-0452), so its depth is carried "
                "on the tier line — the south face fitted through blocks 5-1 against the "
                "north face fitted through the same five, differenced at this block's own "
                "mid-easting. The scan DOES return block 6's north face, at 381.44 px "
                "against the 381.36 that fit predicts, which is the check the carry has. "
                "Its rows are the lettered 180 ft lower row and the tier's mean alley, "
                "and the upper row takes the remainder as it does in every other block")

        if west_id is None:
            e_west = depth_reading.A_E * px_west + depth_reading.B_E
            west_from = "the read stroke"
        else:
            e_west = None
            west_from = west_id
        e_east = None

        # Seat east and west on the committed kerbs, at the block's own mid-northing.
        # Solved once on a first pass at the north face and settled on a second: the
        # columns lean under a metre over the tier, so one pass is within 2 cm of the
        # fixed point, and the second removes even that.
        e_mid_guess = (depth_reading.A_E * (px_west + px_east) / 2.0
                       + depth_reading.B_E)
        n_face = northing_at(kinzie, e_mid_guess) - half_width
        n_mid = n_face - depth_m / 2.0
        for _ in range(2):
            if west_id is not None:
                e_west = easting_at(street_line(streets, west_id), n_mid) + half_width
            e_east = easting_at(street_line(streets, east_id), n_mid) - half_width
            n_face = northing_at(kinzie, (e_west + e_east) / 2.0) - half_width
            n_mid = n_face - depth_m / 2.0

        north_chain = kerb_chain(kinzie, half_width, e_west, e_east)
        south_chain = [(e, n - depth_m) for e, n in north_chain]
        ring = north_chain + south_chain[::-1]
        frontage_m = e_east - e_west

        fractions, carried_stroke = lot_fractions(strokes_px, [px_west, px_east])
        cuts = [0.0] + fractions + [1.0]
        lots = []
        for index in range(len(cuts) - 1):
            le = e_west + cuts[index] * frontage_m
            re = e_west + cuts[index + 1] * frontage_m
            for tier_name, top_off, bottom_off in (
                    ("upper", 0.0, upper_m),
                    ("lower", upper_m + alley_m, depth_m)):
                nw = northing_at(kinzie, le) - half_width
                ne = northing_at(kinzie, re) - half_width
                lots.append({
                    "tier": tier_name,
                    "lot": numbering[tier_name][index],
                    "frontage_m": round(re - le, 2),
                    "frontage_ft": round((re - le) / FT_M, 1),
                    "depth_m": round(bottom_off - top_off, 2),
                    "depth_ft": round((bottom_off - top_off) / FT_M, 1),
                    "polygon": rounded([(le, nw - top_off), (re, ne - top_off),
                                        (re, ne - bottom_off), (le, nw - bottom_off)]),
                })

        alley_ring = rounded(
            [(e, n - upper_m) for e, n in north_chain]
            + [(e, n - upper_m - alley_m) for e, n in north_chain][::-1])

        entry = {
            "id": f"blk_kinzie_{west_id or 'north_branch'}",
            "thompson_block_number": int(number),
            "grid": "north_division_tier",
            "plat": "thompson_plat_1830",
            "bounded_by": {
                "north": "kinzie",
                "south": ("the tier's south face — the north line of North Water Street "
                          "as the plat draws it, carried below committed Kinzie at the "
                          "read depth"),
                "west": west_from,
                "east": east_id,
            },
            "boundary_local_enu_m": rounded(ring),
            "area_m2": round(polygon_area(ring), 1),
            "frontage_m": round(frontage_m, 2),
            "frontage_ft": round(frontage_m / FT_M, 1),
            "depth_m": round(depth_m, 2),
            "depth_ft": round(depth_m / FT_M, 1),
            "depth_from": depth_from,
            "rows": {
                "upper_row_m": round(upper_m, 2),
                "upper_row_ft": round(upper_m / FT_M, 1),
                "alley_m": round(alley_m, 2),
                "alley_ft": round(alley_m / FT_M, 1),
                "lower_row_m": round(lower_m, 2),
                "lower_row_ft": round(lower_m / FT_M, 1),
                "alley_runs": "east-west, and NOT mid-block — the tier is a wedge",
            },
            "ground": south_division.ground_reading(
                [tuple(p) for p in rounded(ring)], field),
            "lots_per_face": len(cuts) - 1,
            "alley_local_enu_m": alley_ring,
            "lots": lots,
            "confidence": {
                "north_face": "inferred",
                "east_and_west_faces": ("conjectural" if west_id is None else "inferred"),
                "south_face": "inferred",
                "lot_lines": "inferred",
                "lot_numbers": "inferred",
            },
        }
        if entry["ground"]["below_datum"]:
            entry["wet_ground"] = (
                f"{entry['ground']['below_datum']} of "
                f"{entry['ground']['samples']} lattice samples inside this block stand "
                "below datum on the committed heightfield. It is the ONLY block on the "
                "tier that does, and it is the block the plat draws its watercourse "
                "across (T-0452) — two independent records, a pixel scan of the sheet "
                "and a trace of the 1834 survey, agreeing on which block the water is "
                "in. The block is cut anyway, because the plat draws it and the lots "
                "are on the sheet; what stands on the wet ground is a placement "
                "question and this record is the place it will be asked.")
        if carried_depth:
            entry["depth_carried"] = carried_depth
        if carried_stroke:
            entry["lot_lines_carried"] = carried_stroke
        if number == depth_reading.BRANCH_BLOCK:
            entry["held_out_of_the_tier_line"] = reading[
                "north_tier_horizontals_px"]["block_7_note"]
            entry["west_face_conjectural"] = (
                "block 7 ends on the North Branch and no street closes it there. Its west "
                "face is the stroke T-0451's column scan returns at 1065.0 px put through "
                "that reading's own px-to-easting fit, which is the fit the tier's "
                "committed columns were themselves seated on — so it is the best this "
                "project has and it is still a single stroke read through an extrapolated "
                "fit, which is what `conjectural` says. The bank itself is not the block's "
                "edge: the plat draws a block, the trace draws a bank, and they are two "
                "different claims")
        blocks.append(entry)

    blocks.sort(key=lambda b: -b["thompson_block_number"])
    return {
        "reading": reading, "blocks": blocks, "half_width_m": half_width,
        "measured": measured, "north_face_line": north_face_line,
    }


def document() -> dict:
    d = derive()
    blocks = d["blocks"]
    return {
        "$schema_note": (
            "DERIVED, and re-derived by the gate. Every number in this file is computed "
            "by tools/cut_north_division_tier.py from two committed inputs — the pixel "
            "reading in data/traces/thompson_north_division_streets.json and the "
            "centrelines in data/streets/1835.json — and nothing in it is authored. "
            "tools/cut_north_division_tier.py --check fails if the committed file is not "
            "what those inputs re-derive, which is how it stays that way."),
        "id": "north_division_tier_lots_1830",
        "plat": "thompson_plat_1830",
        "ticket": "T-1458",
        "parent_ticket": "T-1436",
        "generated_by": "tools/cut_north_division_tier.py",
        "reads": [
            "data/traces/thompson_north_division_streets.json",
            "data/streets/1835.json",
            "data/traces/street_control.json",
        ],
        "why_this_file_and_not_thompson_lots": (
            "tools/generate_plat_lots.py cuts a block between two committed street lines "
            "and subdivides it on the South Division's module — four to a face either "
            "side of a CENTRED alley. Neither holds here. The tier's south face is not a "
            "street line this project commits (street_control.json refuses North Water a "
            "corridor, in as many words), and the tier is a wedge whose alley is nowhere "
            "near mid-block: block 1's rows are 232.7 ft over 177.1. Cutting it inside "
            "that generator would have meant either moving a committed line or drawing "
            "eight lots at the wrong depths in every block on the tier."),
        "seating": {
            "north": ("committed Kinzie's south kerb — the attested centreline in "
                      "data/streets/1835.json offset by the thompson_module_1830 "
                      "half-width"),
            "south": ("that same kerb carried down by the READ depth, per block. "
                      "T-1457 publishes depths and refuses northings because the sheet "
                      "shears above its control band: held out of that fit, committed "
                      "Kinzie is missed by +16.8 m at Franklin falling to +0.4 m at "
                      "Wolcott. A depth survives the shear; a northing does not."),
            "east_and_west": ("the tier's attested north-south centrelines, offset by the "
                              "same half-width — except block 7's west face, which has no "
                              "street and carries its own refusal"),
            "subdivision": ("the reading's own strokes and rows, applied as PROPORTIONS "
                            "of the committed face rather than as absolute eastings"),
        },
        "module": {
            "module": "north_division_thompson_1830",
            "lot_frontage_ft": 80.0,
            "lower_row_depth_ft": LETTERED_LOWER_ROW_FT,
            "lower_row_is_lettered": d["reading"]["north_tier_horizontals_px"][
                "lettering"]["lower_row_depth_where"],
            "upper_row_depth_ft": "per block — 178.6 at Franklin to 232.7 at Wolcott",
            "alley_ft": "per block — 20.4 to 22.9, read, not modular",
            "how_it_differs_from_the_south_division": (
                "same four-to-a-face frontage, a WEDGE instead of a rectangle, and an "
                "alley that is read rather than the 18 ft module. The South Division's "
                "alley is centred by construction; this one is not centred in any block "
                "on the tier."),
            "lot_numbering": (
                "the sheet letters 4 on the lower row's west lot in every block read. "
                "The other seven numbers are inferred from the one Original Town block "
                "whose lot numerals are read — block 18, north row 4 3 2 and south row "
                "5 6 7 (docs/RESEARCH/clark_reach_bulge_1834.md section 8): the row "
                "carrying 4 at its west end runs 4-3-2-1 west to east, and the other row "
                "runs 5-6-7-8 west to east."),
        },
        "blocks": blocks,
        "counts": {
            "blocks": len(blocks),
            "blocks_with_a_read_depth": sum(1 for b in blocks
                                            if b["depth_from"] == "read"),
            "blocks_with_a_carried_depth": sum(1 for b in blocks
                                               if b["depth_from"] == "carried"),
            "lots": sum(len(b["lots"]) for b in blocks),
            "lots_per_face": sorted({b["lots_per_face"] for b in blocks}),
            "tier_ground_m2": round(math.fsum(b["area_m2"] for b in blocks), 1),
            "blocks_with_ground_below_datum": [b["thompson_block_number"] for b in blocks
                                               if b["ground"]["below_datum"]],
        },
        "what_this_does_not_say": (
            "NOTHING ABOUT NORTH WATER STREET. The tier's south face is the north line of "
            "that street as the plat draws it, and this file does not re-grade the street, "
            "does not touch tools/derive_north_water.py, and does not give the corridor "
            "street_control.json refuses. Where the blocks stop and where the roadway runs "
            "are two statements and only the first is drawn. It also seats no building: "
            "these are lots, and who stood on them is a placement ticket's question."),
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
              "tools/cut_north_division_tier.py re-derives from the committed reading "
              "and the committed street lines. Regenerate it in the same commit.")
        return 1
    print(f"ok {OUT_PATH.name} re-derives")
    return 0


def self_test(quiet: bool = False) -> int:
    doc = document()
    blocks = {b["thompson_block_number"]: b for b in doc["blocks"]}
    failures = []

    def want(label, condition, detail=""):
        if not condition:
            failures.append(f"{label}{': ' + detail if detail else ''}")
        elif not quiet:
            print(f"  ok  {label}")

    want("the plat's seven blocks are all cut", len(blocks) == 7,
         f"{len(blocks)} cut")
    want("every block is four lots to a face",
         all(b["lots_per_face"] == 4 for b in blocks.values()))
    want("every block carries eight lots",
         all(len(b["lots"]) == 8 for b in blocks.values()))

    # The frontage the committed columns give, against the module the sheet letters.
    widest = max(abs(b["frontage_ft"] / 4 - 80.0) for b in blocks.values())
    want("the committed columns give four 80 ft lots to a face, within 7 ft",
         widest < 7.0, f"worst lot is {widest:.1f} ft off 80")

    # The wedge itself: the lower row holds and the upper row grows eastward.
    lower = [blocks[i]["rows"]["lower_row_ft"] for i in (5, 4, 3, 2, 1)]
    upper = [blocks[i]["rows"]["upper_row_ft"] for i in (5, 4, 3, 2, 1)]
    want("the lower row holds the lettered 180 ft across the tier, within 5 ft",
         max(abs(v - 180.0) for v in lower) < 5.0,
         f"{min(lower):.1f}-{max(lower):.1f} ft")
    want("the upper row grows monotonically eastward",
         all(a < b for a, b in zip(upper, upper[1:])),
         " ".join(f"{v:.1f}" for v in upper))
    want("the upper row is the wedge and the lower row is not",
         (max(upper) - min(upper)) > 5 * (max(lower) - min(lower)),
         f"upper spreads {max(upper) - min(upper):.1f} ft, lower {max(lower) - min(lower):.1f}")

    # The rows and the alley account for the depth, exactly, in every block.
    for number, block in blocks.items():
        rows = block["rows"]
        total = rows["upper_row_m"] + rows["alley_m"] + rows["lower_row_m"]
        want(f"block {number}'s rows and alley sum to its depth",
             abs(total - block["depth_m"]) < 0.02,
             f"{total:.2f} against {block['depth_m']:.2f}")

    # What a centred alley would have cost. The South Division's module splits the
    # depth evenly either side of the alley; on a wedge that puts the alley half the
    # difference between the two rows away from where the sheet draws it, and this is
    # the figure that says cutting the tier inside generate_plat_lots.py was not an
    # option. Nearly right at the west end and badly wrong at the east is exactly what
    # a wedge does, so the assertion is on the worst block, not on every block.
    offsets = [abs(b["rows"]["upper_row_m"] - b["rows"]["lower_row_m"]) / 2.0
               for b in blocks.values()]
    want("a centred alley would stand 8 m or more off the drawn line somewhere on the tier",
         max(offsets) >= 8.0,
         f"the worst block is {max(offsets):.1f} m out")

    # Block 6's carry has a check the sheet gives for free: the scan returns its north
    # face even though it loses the two middle lines.
    read_face = 381.44
    fit = derive()["north_face_line"]
    faces = json.loads((DATA / "traces"
                        / "thompson_north_division_streets.json").read_text(
                            encoding="utf-8"))["north_tier_blocks"]["faces_px"]["6"]
    predicted = fit[0] * (sum(faces) / 2.0) + fit[1]
    want("the tier line predicts block 6's read north face to a fifth of a pixel",
         abs(predicted - read_face) < 0.2,
         f"{predicted:.2f} against {read_face}")

    # Geometry: every lot sits inside its block, and the lots plus the alley account
    # for the block's ground.
    for number, block in blocks.items():
        covered = sum(polygon_area(lot["polygon"]) for lot in block["lots"])
        covered += polygon_area(block["alley_local_enu_m"])
        want(f"block {number}'s lots and alley account for its ground",
             abs(covered - block["area_m2"]) / block["area_m2"] < 0.005,
             f"{covered:.0f} m2 of {block['area_m2']:.0f}")

    # The seating: every block's north face stands on committed Kinzie's kerb.
    streets = load(DATA / "streets" / "1835.json")
    kinzie = street_line(streets, "kinzie")
    half_width = load(DATA / "traces" / "street_control.json")[
        "platted_street"]["half_width_m"]
    worst = 0.0
    for block in doc["blocks"]:
        for e, n in block["boundary_local_enu_m"][:2]:
            worst = max(worst, abs((northing_at(kinzie, e) - half_width) - n))
    want("every block's north face stands on committed Kinzie's south kerb",
         worst < 0.02, f"worst is {worst:.3f} m")

    # The sheet and the terrain, on which block the water is in. Two records that share
    # no arithmetic: a column-and-row scan of the plat, and a trace of Wright's survey
    # baked into the committed heightfield.
    wet = doc["counts"]["blocks_with_ground_below_datum"]
    want("the one block with wet ground is the one the plat draws its watercourse across",
         wet == [int(CARRIED_BLOCK)], f"wet blocks {wet}")

    # Lot numbers: the sheet's one lettered numeral lands where it is lettered.
    west_lower = [
        sorted([lot for lot in b["lots"] if lot["tier"] == "lower"],
               key=lambda lot: min(p[0] for p in lot["polygon"]))[0]["lot"]
        for b in blocks.values()]
    want("lot 4 is the lower row's west lot in every block, as the sheet letters it",
         set(west_lower) == {4}, str(sorted(set(west_lower))))

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
    print(f"{'blk':>3} {'west':>16} {'east':>16} {'frontage':>9} {'depth':>8} "
          f"{'upper':>8} {'alley':>7} {'lower':>8}  lots")
    for b in doc["blocks"]:
        rows = b["rows"]
        print(f"{b['thompson_block_number']:>3} {b['bounded_by']['west'][:16]:>16} "
              f"{b['bounded_by']['east'][:16]:>16} {b['frontage_ft']:>7.1f}ft "
              f"{b['depth_ft']:>6.1f}ft {rows['upper_row_ft']:>6.1f}ft "
              f"{rows['alley_ft']:>5.1f}ft {rows['lower_row_ft']:>6.1f}ft "
              f" {b['lots_per_face']} to a face ({b['depth_from']})")
    counts = doc["counts"]
    print()
    print(f"{counts['blocks']} blocks, {counts['lots']} lots, "
          f"{counts['tier_ground_m2']:.0f} m2 of platted ground.")


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
