#!/usr/bin/env python3
"""Read Wabansia's block numerals off Wright's 1834 survey, on a column grid nobody had.

    tools/read_wabansia_block_numerals.py               print the reading
    tools/read_wabansia_block_numerals.py --write       write the trace
    tools/read_wabansia_block_numerals.py --check       re-derive it from the committed pixels
    tools/read_wabansia_block_numerals.py --check-sheet  re-measure every rule off the raster
    tools/read_wabansia_block_numerals.py --self-test   break each assertion and watch it fire

WHAT THIS FILE IS AND IS NOT. It is the READING: which figure Wright writes in which cell
of Wabansia's block grid, the crop on the sheet where each was read, and the ruled lines
that make the cell. It authors NO ground. Every number below is a PIXEL statement about
chicago/pre_fire_v1/maps/images/1834-wright-map.jpg; seating Wabansia on modern ground is
T-1070's, and nothing here should be read as having done it.

WHY THE GRID COSTS SOMETHING HERE, WHERE IT COST NOTHING IN KINZIE'S ADDITION. T-1061
could read the Addition cell by cell because T-1060 had already committed its eleven
street corridors, so a cell was the rectangle two of them leave. Wabansia has half of
that: T-1068 committed the seven EAST-WEST corridors — Free, Trade, Sailors, Hight,
Owen, Hubbard, Kinzie — and refused the north-south ones, because the discrimination it
used (Wright letters a street's name inside its corridor) has nothing to say about
streets he does not letter, and the width test that would have to stand in its place is
the one this tract defeats. So the tiers are imported from
data/traces/wabansia_streets.json and the COLUMNS are measured here, by the only test
this tract leaves: a north-south rule is a line that appears in EVERY tier at the same
place, drifting east with the tract's own 0.011 px/px tilt. A lot line does that too, and
is kept and marked as one; a numeral's stroke does not.

WHAT THE READING SETTLES, and it is more than the ticket asked. Wabansia's block grid
holds TWENTY-ONE blocks in three columns of seven, and they are numbered 59 to 79 — a
closed run, every number once, none missing:

        west column      middle column    east column
    t1      79                66               65      (north, at the tract boundary)
    t2      78                67               64
    t3      77                68               63
    t4      76                69               62
    t5      75                70               61
    t6      74                71               60
    t7      73                72               59      (south, on Kinzie Street)

which is a boustrophedon read the other way round from the Addition's: it STARTS at the
tract's south-east corner, at Kinzie Street beside the North Branch, runs north up the
east column to 65, turns west and runs south down the middle column to 72, turns west
again and runs north up the west column to 79 at the north-west corner.

THE RUN DOES NOT BEGIN AT 1, and that is the finding worth carrying out of here.
Kinzie's Addition, on this same sheet, is numbered 1-54 (T-1061,
data/traces/kinzie_addition_block_numbering.json). Wabansia begins at 59. Fifty-five to
fifty-eight are in neither reading. This file does NOT claim Wright numbered the sheet
continuously across two surveys — that is a claim about intent and it has no evidence
here. It records the arithmetic and names the only two pieces of ground on this sheet
that could hold four more blocks, both of them open tickets: the Addition's river-front
water lots (T-1063) and the unidentified tract north of Kinzie Street lettered Michigan
St (T-0796). Wabansia's own water-lot triangle is not a candidate: its parcels are
numbered from 1 in a run of their own, which is T-1077's to read.

THREE THINGS THE SHEET DOES THAT A REGULAR GRID WOULD NOT, all measured, none explained:

  * THE JOG. The north-south street between the middle and east columns stands at
    x 957-989 in tiers 1-3 and at x 1035-1076 in tiers 4-7. It steps 78 px — about 54 m —
    EAST at Sailors Street, and the two columns change from one lot wide to two lots wide
    on the same line. The street widens across the step too — 22.6 m north of Sailors
    Street against 28.5 m south of it, where the street between the west and middle
    columns holds 21-22 m the whole way down. North of Sailors Street the North Branch is
    close enough to the grid to leave room for nothing wider.
  * THE NORTH TIER IS SHORT. The tract's north boundary rule runs at y 958, leaving tier 1
    a depth of 106 px against the 128-139 px the tiers below hold — three lot rows, not four.
    Wright's lot figures in tier 1 start at 2, which is the same fact written in his hand.
  * THE WEST MARGIN. Between the tract's west boundary rule and the west column's own
    west rule there is a strip 16-23 px wide, about 12-17 m. That is too narrow for a
    street on this sheet, where T-1068's seven measured corridors run 21-29 m, and no
    figure stands in it. Wright draws the two so close that the rule detector T-1060 left
    behind returns them as one fat blob, which is why `--check-sheet` tests peaks and not
    rules. It is recorded and NOT named; T-1070, which seats the tract, is where it has
    to be settled.

WHAT IS NOT READ, and is somebody else's, not a gap to fill by guessing: the lot figures
inside each block (1-8 in the two-lot-wide blocks, 1-4 in the one-lot-wide ones, read
here only far enough to say which they are); the water-lot triangle (T-1077); the names
of the north-south streets, which Wright letters nowhere in this tract; and the seating
(T-1070).
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_k = importlib.import_module("read_kinzie_addition_streets")

ROOT = Path(__file__).resolve().parents[1]
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
STREETS = ROOT / "data/traces/wabansia_streets.json"
ADDITION = ROOT / "data/traces/kinzie_addition_street_grid.json"
ADDITION_NUMERALS = ROOT / "data/traces/kinzie_addition_block_numbering.json"
OUT = ROOT / "data/traces/wabansia_block_numbering.json"
FT = 0.3048

# The raster dx/dy of Wabansia's north-south rules, fitted the way T-1068 fitted its
# east-west ones: the slope that maximises the variance of the projection. Scanned over
# +/-0.080 in 0.001 steps on the window x 640-1330, tier by tier.
SHEAR_NS = 0.020

# The tract's own bounds, this tool's two measurements that the street reading had no
# reason to want. The north rule is the strongest horizontal in y 930-1010 in BOTH the
# x 700-860 and the x 890-1040 windows; the west rule is the strongest vertical within
# 10 px of the tract edge in each tier.
NORTH_RULE_PX_Y = 958.0
WEST_RULE_PX_X = {"t1": 682.2, "t2": 678.4, "t3": 679.0, "t4": 680.8,
                  "t5": 683.1, "t6": 687.2, "t7": 682.1}

# THE COLUMN GRID. Per tier, per column: (west rule, lot divider or None, east rule) in
# NA raster pixels. A `None` divider is a block one lot wide — the north half of the
# middle and east columns, where the North Branch leaves no room for two.
COLUMNS = {
    "t1": {"A": (698.3, 776.4, 860.6), "B": (892.6, None, 957.8), "C": (989.5, None, 1041.9)},
    "t2": {"A": (696.7, 775.6, 859.6), "B": (889.9, None, 957.0), "C": (990.1, None, 1042.3)},
    "t3": {"A": (696.5, 777.0, 860.6), "B": (891.6, None, 956.7), "C": (989.0, None, 1046.5)},
    "t4": {"A": (698.5, 785.0, 862.2), "B": (893.5, 966.5, 1034.5), "C": (1075.3, 1146.9, 1212.4)},
    "t5": {"A": (700.1, 788.6, 863.8), "B": (895.2, 967.8, 1034.5), "C": (1076.0, 1148.7, 1213.1)},
    "t6": {"A": (705.8, 786.2, 864.7), "B": (895.2, 968.3, 1035.4), "C": (1075.6, 1147.8, 1212.4)},
    "t7": {"A": (704.6, 785.7, 866.1), "B": (898.1, 968.5, 1034.5), "C": (1075.8, 1148.1, 1210.6)},
}

TIER_IDS = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
COLUMN_IDS = ["A", "B", "C"]

# THE READING. `legibility` is about the ink and nothing else; `confidence` is this
# project's grade, and the one figure that is not `documented` says in its note exactly
# what the sheet would not settle.
READING = {
    ("A", "t1"): (79, "clear", "documented", None),
    ("A", "t2"): (78, "faint", "documented",
                  "The 8 is written small and half a stroke lighter than the 7; two "
                  "bowls, closed, and no descender, so it is not a 3 and not a 9."),
    ("A", "t3"): (77, "faint", "documented",
                  "Both figures carry the same hooked top bar and long left-falling "
                  "diagonal; the second is the first written smaller."),
    ("A", "t4"): (76, "clear", "documented", None),
    ("A", "t5"): (75, "clear", "documented",
                  "Read again at 8x against the 7 of block 76 one tier north: the first "
                  "glyph is a hooked bar over a falling diagonal and the second closes a "
                  "bowl at the foot. It is 75, not 55."),
    ("A", "t6"): (74, "clear", "documented", None),
    ("A", "t7"): (73, "clear", "documented", None),
    ("B", "t1"): (66, "clear", "documented", None),
    ("B", "t2"): (67, "clear", "documented", None),
    ("B", "t3"): (68, "clear", "documented", None),
    ("B", "t4"): (69, "crossed", "documented",
                  "Written large across the block's lot divider and over the lot figures "
                  "3, 4, 6 and 5, which are half its height. The 6 and the 9 are the two "
                  "tall strokes."),
    ("B", "t5"): (70, "crossed", "documented",
                  "Written large across the lot divider and over lot figures 3, 4, 6 and "
                  "5, as block 69 is one tier north."),
    ("B", "t6"): (71, "clear", "documented", None),
    ("B", "t7"): (72, "clear", "documented", None),
    ("C", "t1"): (65, "clear", "documented",
                  "The lot figure 3 stands immediately west of the 6 and is not part of "
                  "the block number."),
    ("C", "t2"): (64, "clear", "documented", None),
    ("C", "t3"): (63, "ambiguous", "inferred",
                  "The second glyph is a 3 or a 5 at 600 dpi and the sheet will not "
                  "settle it: this hand writes both with a flat upper bar over a bowl. "
                  "The run does settle it — the tier north reads 64 and the tier south "
                  "reads 62, both clear, and the column is monotone over its other six "
                  "cells. Graded `inferred` for that reason and not upgraded."),
    ("C", "t4"): (62, "clear", "documented", None),
    ("C", "t5"): (61, "clear", "documented", None),
    ("C", "t6"): (60, "clear", "documented", None),
    ("C", "t7"): (59, "clear", "documented", None),
}

# What the Addition's numbering committed, quoted so the arithmetic below is checkable
# without opening the other file.
ADDITION_RUN = (1, 54)

NOT_READ = [
    "the lot figures inside each block, read only far enough to say that the two-lot-wide "
    "blocks carry 1-8 and the one-lot-wide blocks 1-4",
    "the water-lot triangle between the east column and the North Branch (T-1077)",
    "the names of the north-south streets, which Wright letters nowhere in Wabansia",
    "the seating of any of this on modern ground (T-1070)",
]


# ------------------------------------------------------------------ the read

def _frame():
    g = json.loads(GCP.read_text())
    d = json.loads((ROOT / "data/datum.json").read_text())
    c = g["fit"]["coefficients"]

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"] - d["origin_utm_e"],
                c["d"] * px + c["e"] * py + c["f"] - d["origin_utm_n"])

    return to_local


def _control():
    """The price of this method on this sheet, borrowed from T-1060 exactly as T-1068
    borrowed it: the Original Town's corridors are platted at 80 ft and read 83.6 ft here,
    so every foot figure is reported raw AND divided by that ratio."""
    a = json.loads(ADDITION.read_text())["control_summary"]
    return a["method_over_read"], a["original_town_read_ft"]


def _tiers():
    """The tier bands, imported from T-1068's corridors. A corridor that moves there moves
    every cell here, which is what `--check` is for."""
    s = json.loads(STREETS.read_text())["streets"]
    by_order = sorted(s, key=lambda t: t["order"])
    out = [{"id": "t1", "north": "tract boundary", "south": by_order[0]["id"],
            "y_px": [NORTH_RULE_PX_Y, by_order[0]["rule_px_y"][0]]}]
    for a, b in zip(by_order, by_order[1:]):
        out.append({"id": f"t{len(out) + 1}", "north": a["id"], "south": b["id"],
                    "y_px": [a["rule_px_y"][1], b["rule_px_y"][0]]})
    for t in out:
        t["depth_px"] = round(t["y_px"][1] - t["y_px"][0], 1)
        t["mid_px_y"] = round((t["y_px"][0] + t["y_px"][1]) / 2.0, 1)
    return out


def _span_x(to_local, x0, x1, y):
    e0, n0 = to_local(x0, y)
    e1, n1 = to_local(x1, y)
    return math.hypot(e1 - e0, n1 - n0)


def crop_px(col: str, tier: str, mid_y: float) -> list[float]:
    """The box the figure was read in. Where the block has a lot divider the number is
    written across it and the crop is centred on it; where it has none the crop is the
    block's own width. The east column's crop reaches 12 px past its east rule because
    Wright crowds those figures against the bank."""
    west, div, east = COLUMNS[tier][col]
    if div is not None:
        x0, x1 = div - 46.0, div + 46.0
    elif col == "C":
        x0, x1 = west + 8.0, east + 12.0
    else:
        x0, x1 = west + 2.0, east - 2.0
    return [round(x0, 1), round(mid_y - 34.0, 1), round(x1, 1), round(mid_y + 34.0, 1)]


def boustrophedon() -> dict:
    """The run, derived from the scheme alone so the reading can be checked against it.

    Up the east column from the south-east corner, down the middle column, up the west
    column. Written out rather than looped so the direction of each leg is legible."""
    out = {}
    n = 59
    for tier in reversed(TIER_IDS):          # C: t7 -> t1, south to north
        out[("C", tier)] = n
        n += 1
    for tier in TIER_IDS:                    # B: t1 -> t7, north to south
        out[("B", tier)] = n
        n += 1
    for tier in reversed(TIER_IDS):          # A: t7 -> t1, south to north
        out[("A", tier)] = n
        n += 1
    return out


def read() -> dict:
    to_local = _frame()
    ratio, control_read = _control()
    tiers = _tiers()
    by_id = {t["id"]: t for t in tiers}
    scheme = boustrophedon()

    columns, blocks, ns_streets, margin = [], [], [], []
    for tier in TIER_IDS:
        t = by_id[tier]
        y = t["mid_px_y"]
        for col in COLUMN_IDS:
            west, div, east = COLUMNS[tier][col]
            width_px = round(east - west, 1)
            width_m = round(_span_x(to_local, west, east, y), 2)
            columns.append({
                "column": col, "tier": tier,
                "west_px": west, "lot_divider_px": div, "east_px": east,
                "width_px": width_px, "width_m": width_m,
                "width_ft_raw": round(width_m / FT, 1),
                "width_ft_controlled": round(width_m / FT / ratio, 1),
                "lots_wide": 2 if div is not None else 1,
            })
            number, legibility, confidence, note = READING[(col, tier)]
            block = {
                "number": number, "column": col, "tier": tier,
                "numeral_crop_px": crop_px(col, tier, y),
                "legibility": legibility, "confidence": confidence,
                "derives_from_scheme": scheme[(col, tier)] == number,
            }
            if note:
                block["note"] = note
            blocks.append(block)

        for a, b in (("A", "B"), ("B", "C")):
            w = COLUMNS[tier][b][0]
            e = COLUMNS[tier][a][2]
            m = round(_span_x(to_local, e, w, y), 2)
            ns_streets.append({
                "between": f"{a}|{b}", "tier": tier,
                "rule_px_x": [e, w], "corridor_px": round(w - e, 1),
                "corridor_m": m, "corridor_ft_raw": round(m / FT, 1),
                "corridor_ft_controlled": round(m / FT / ratio, 1),
            })
        wr = WEST_RULE_PX_X[tier]
        aw = COLUMNS[tier]["A"][0]
        mm = round(_span_x(to_local, wr, aw, y), 2)
        margin.append({"tier": tier, "rule_px_x": [wr, aw],
                       "width_px": round(aw - wr, 1), "width_m": mm,
                       "width_ft_raw": round(mm / FT, 1)})

    blocks.sort(key=lambda b: b["number"])
    return {
        "tiers": tiers,
        "columns": columns,
        "north_south_streets": ns_streets,
        "west_margin": margin,
        "blocks": blocks,
        "scheme": _scheme_doc(),
        "arithmetic": _arithmetic(blocks),
        "jog": _jog(to_local),
        "control": {
            "original_town_platted_ft": 80.0,
            "original_town_read_ft": control_read,
            "method_over_read": ratio,
            "source": "data/traces/kinzie_addition_street_grid.json § control_summary",
        },
        "not_read": NOT_READ,
    }


def _scheme_doc() -> dict:
    scheme = boustrophedon()
    return {
        "first": 59, "last": 79, "cells": len(scheme),
        "legs": [
            {"column": "C", "from_tier": "t7", "to_tier": "t1", "from": 59, "to": 65,
             "direction": "south to north, up the bank of the North Branch"},
            {"column": "B", "from_tier": "t1", "to_tier": "t7", "from": 66, "to": 72,
             "direction": "north to south"},
            {"column": "A", "from_tier": "t7", "to_tier": "t1", "from": 73, "to": 79,
             "direction": "south to north, up the tract's west edge"},
        ],
        "reading": "A boustrophedon that starts at the tract's south-east corner, on "
                   "Kinzie Street beside the North Branch, and ends at its north-west. "
                   "Kinzie's Addition's own run (T-1061) turns the other way, from the "
                   "river tier northward; the two surveys share a sheet and not a habit.",
    }


def _arithmetic(blocks) -> dict:
    lo, hi = ADDITION_RUN
    mine = sorted(b["number"] for b in blocks)
    gap = list(range(hi + 1, mine[0]))
    return {
        "wabansia_run": [mine[0], mine[-1]],
        "kinzie_addition_run": [lo, hi],
        "unaccounted": gap,
        "candidates": [
            {"ticket": "T-1063",
             "ground": "the Addition's river-front water lots, recorded as a lot strip"},
            {"ticket": "T-0796",
             "ground": "the unidentified tract north of Kinzie Street lettered Michigan St"},
        ],
        "refused": "that Wright numbered this sheet continuously across two surveys. The "
                   "arithmetic is recorded; the intent is not evidenced here, and "
                   "Wabansia's own water-lot triangle is not a candidate because its "
                   "parcels are numbered from 1 in a run of their own (T-1077).",
    }


def _jog(to_local) -> dict:
    north = COLUMNS["t3"]["B"][2], COLUMNS["t3"]["C"][0]
    south = COLUMNS["t4"]["B"][2], COLUMNS["t4"]["C"][0]
    step_px = round(south[0] - north[0], 1)
    step_m = round(_span_x(to_local, north[0], south[0], 1410.0), 2)
    return {
        "at": "Sailors Street, between tier 3 and tier 4",
        "north_rule_px_x": list(north), "south_rule_px_x": list(south),
        "step_px": step_px, "step_m": step_m,
        "lots_wide_north": 1, "lots_wide_south": 2,
        "corridor_px_north": round(north[1] - north[0], 1),
        "corridor_px_south": round(south[1] - south[0], 1),
        "corridor_m_north": round(_span_x(to_local, north[0], north[1], 1328.8), 2),
        "corridor_m_south": round(_span_x(to_local, south[0], south[1], 1492.0), 2),
        "reading": "The north-south street between the middle and east columns is not one "
                   "line. It stands at x 955-989 in tiers 1-3 and at x 1036-1077 in tiers "
                   "4-7, and the blocks either side of it go from one lot wide to two on "
                   "the same tier line. It also widens across the step, from 22.6 m north "
                   "of Sailors Street to 28.5 m south of it, where the A|B street holds "
                   "21-22 m the whole way down. North of Sailors Street the North Branch "
                   "is close enough to the grid to leave room for nothing wider.",
    }


def _wrap(doc):
    g = json.loads(GCP.read_text())
    return {
        "_doc": __doc__,
        "ticket": "T-1074",
        "raster": {k: g["raster"][k] for k in
                   ("working_copy", "width", "height", "dpi", "sha256", "source_id")},
        "registration": {"gcp_file": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
                         "rms_m": g["fit"].get("rms_m", g["fit"].get("residual_rms_m"))},
        "method": {
            "shear_ns": SHEAR_NS,
            "tiers_from": "data/traces/wabansia_streets.json § streets (T-1068)",
            "north_rule_px_y": NORTH_RULE_PX_Y,
            "west_rule_px_x": WEST_RULE_PX_X,
            "discrimination": "a north-south rule is a line that stands in every tier at "
                              "the same place, drifting east with the tract's own tilt; a "
                              "numeral's stroke does not, and a lot line does and is kept "
                              "and marked as one",
        },
        **doc,
    }


# ----------------------------------------------------------------- the gates

def assertions(doc: dict) -> list[str]:
    """Each failure is its own string so `--self-test` can break one input at a time and
    watch exactly one of them fire."""
    bad: list[str] = []
    blocks = doc["blocks"]
    w, h = doc["raster"]["width"], doc["raster"]["height"]
    numbers = [b["number"] for b in blocks]

    if len(blocks) != 21:
        bad.append(f"Wabansia's grid holds 21 cells and this reading has {len(blocks)}")
    if sorted(numbers) != list(range(59, 80)):
        missing = [n for n in range(59, 80) if n not in set(numbers)]
        twice = sorted({n for n in numbers if numbers.count(n) > 1})
        bad.append(f"the run 59-79 is not closed: missing {missing}, used twice {twice}")
    cells = [(b["column"], b["tier"]) for b in blocks]
    if len(set(cells)) != len(cells):
        bad.append("two numbers stand in one cell")

    scheme = boustrophedon()
    by_cell = {(b["column"], b["tier"]): b for b in blocks}
    for key, expected in scheme.items():
        got = by_cell.get(key)
        if got is None:
            bad.append(f"the run puts {expected} in column {key[0]} tier {key[1]} and "
                       "the reading has no block there")
        elif got["number"] != expected:
            bad.append(f"column {key[0]} tier {key[1]}: the run derives {expected} and "
                       f"the reading has {got['number']}")
    if not all(b["derives_from_scheme"] for b in blocks):
        bad.append("`derives_from_scheme` no longer marks every cell — the run and the "
                   "ink have stopped agreeing somewhere and the file is not saying where")

    cols = {(c["column"], c["tier"]): c for c in doc["columns"]}
    for b in blocks:
        x0, y0, x1, y1 = b["numeral_crop_px"]
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h or x1 <= x0 or y1 <= y0:
            bad.append(f"block {b['number']}'s crop {b['numeral_crop_px']} is not a box "
                       f"inside the {w}x{h} raster")
        c = cols[(b["column"], b["tier"])]
        if x0 < c["west_px"] - 1.0 or x1 > c["east_px"] + 13.0:
            bad.append(f"block {b['number']}'s crop leaves its own column "
                       f"[{c['west_px']}, {c['east_px']}]")
        if b["confidence"] not in ("documented", "inferred"):
            bad.append(f"block {b['number']} is graded `{b['confidence']}`")
        if b["confidence"] != "documented" and "note" not in b:
            bad.append(f"block {b['number']} is not documented and says nothing about why")
        if b["legibility"] not in ("clear", "faint", "crossed", "ambiguous"):
            bad.append(f"block {b['number']} is graded `{b['legibility']}`")
        if b["legibility"] != "clear" and "note" not in b:
            bad.append(f"block {b['number']} is graded `{b['legibility']}` and says "
                       "nothing about why")
        if b["legibility"] == "ambiguous" and b["confidence"] == "documented":
            bad.append(f"block {b['number']} is documented off an ambiguous glyph — a "
                       "figure the sheet will not settle cannot be documented")

    for c in doc["columns"]:
        if not c["west_px"] < c["east_px"]:
            bad.append(f"column {c['column']} tier {c['tier']}: rules are not west-then-east")
        d = c["lot_divider_px"]
        if (d is not None) != (c["lots_wide"] == 2):
            bad.append(f"column {c['column']} tier {c['tier']}: `lots_wide` and the "
                       "divider disagree")
        if d is not None:
            mid = (c["west_px"] + c["east_px"]) / 2.0
            if abs(d - mid) > 8.0:
                bad.append(f"column {c['column']} tier {c['tier']}: the lot divider "
                           f"{d} is {abs(d - mid):.1f} px off the block's midpoint — a "
                           "divider that far out is a street, not a lot line")
        if not 45.0 <= c["width_px"] <= 175.0:
            bad.append(f"column {c['column']} tier {c['tier']} measures {c['width_px']} "
                       "px wide, which is neither a one-lot nor a two-lot block here")

    for s in doc["north_south_streets"]:
        if not 24.0 <= s["corridor_px"] <= 45.0:
            bad.append(f"the {s['between']} corridor in {s['tier']} measures "
                       f"{s['corridor_px']} px — T-1068 read this tract's seven named "
                       "corridors at 28.9-39.2 px and a street outside that is a "
                       "mis-taken rule")
    for m in doc["west_margin"]:
        if m["width_px"] > 24.0:
            bad.append(f"the west margin in {m['tier']} measures {m['width_px']} px — "
                       "grown to a corridor's width, it is a street and has to be named")

    tiers = {t["id"]: t for t in doc["tiers"]}
    if [t["id"] for t in doc["tiers"]] != TIER_IDS:
        bad.append("the tiers are not committed north to south")
    for t in doc["tiers"]:
        if t["depth_px"] <= 0:
            bad.append(f"tier {t['id']} has no depth")
    if not tiers["t1"]["depth_px"] < min(tiers[i]["depth_px"] for i in TIER_IDS[1:]):
        bad.append("tier 1 is no longer the short one — the tract's north boundary has "
                   "stopped truncating it and the reading says it does")
    for b in blocks:
        y0, y1 = b["numeral_crop_px"][1], b["numeral_crop_px"][3]
        t = tiers[b["tier"]]
        if y0 < t["y_px"][0] or y1 > t["y_px"][1]:
            bad.append(f"block {b['number']}'s crop leaves its own tier {t['y_px']}")

    a = doc["arithmetic"]
    if a["wabansia_run"] != [59, 79]:
        bad.append(f"the arithmetic says Wabansia runs {a['wabansia_run']}")
    if a["unaccounted"] != [55, 56, 57, 58]:
        bad.append(f"the gap between the Addition's run and Wabansia's is "
                   f"{a['unaccounted']} — it was 55-58 and a changed gap changes what "
                   "the candidates are being offered for")
    if not a.get("refused"):
        bad.append("the continuous-numbering claim has stopped being refused in writing")
    if doc["jog"]["step_px"] < 60.0:
        bad.append(f"the B|C street's jog measures {doc['jog']['step_px']} px — it was "
                   "81, and a jog that has closed means one of the two rules moved")
    return bad


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def check() -> int:
    """The cheap half: everything in the committed file re-derives from the pixels
    committed beside it, through the committed affine. No raster is opened."""
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing", file=sys.stderr)
        return 1
    fresh = _wrap(read())
    bad = assertions(fresh)
    if load(OUT) != fresh:
        bad.append(f"{OUT.relative_to(ROOT)} is not what this tool re-derives — "
                   "regenerate it in the commit that changes the reading")
    if bad:
        for line in bad:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    n = sum(1 for b in fresh["blocks"] if b["confidence"] == "documented")
    print(f"wabansia block numerals: {len(fresh['blocks'])} cell(s) numbered 59-79, "
          f"{n} read off the sheet, {len(fresh['blocks']) - n} carried by the run")
    return 0


def _maxima(prof, floor: float = 12.0):
    """Every local maximum of an imported profile, with no width test.

    `_rules` refuses a peak wider than seven pixels, which is right for T-1060's
    corridor hunt and wrong here: Wabansia's west boundary is drawn double and its
    tract rule is a broad stroke, and both come back as one fat blob or as nothing.
    A rule this tool committed only has to still be a peak."""
    vals = [v for _, v in prof]
    return [(prof[i][0], vals[i]) for i in range(1, len(prof) - 1)
            if vals[i] >= vals[i - 1] and vals[i] > vals[i + 1] and vals[i] >= floor]


def check_sheet() -> int:
    """The raster half: every rule this reading committed is still a peak where the sheet
    puts it. Opens the 5050 x 6628 scan, so the PR runs it and tools/check.sh does not."""
    _, img = _k._sheet()
    bad = []
    doc = _wrap(read())
    tiers = {t["id"]: t for t in doc["tiers"]}
    tol = 5.0
    for tier in TIER_IDS:
        t = tiers[tier]
        y0, y1 = int(t["y_px"][0] + 8), int(t["y_px"][1] - 8)
        peaks = _maxima(_k._profile(img, 640, y0, 1330, y1, "v", SHEAR_NS))
        want = [("west boundary", WEST_RULE_PX_X[tier])]
        for col in COLUMN_IDS:
            west, div, east = COLUMNS[tier][col]
            want.append((f"{col} west", west))
            want.append((f"{col} east", east))
            if div is not None:
                want.append((f"{col} lot divider", div))
        for name, x in want:
            near = min(peaks, key=lambda r: abs(r[0] - x)) if peaks else None
            if near is None or abs(near[0] - x) > tol:
                bad.append(f"{tier} {name}: committed x {x}, nearest sheet peak "
                           f"{near[0] if near else None}")

    peaks = _maxima(_k._profile(img, 700, 930, 1040, 1010, "h", 0.019), floor=40.0)
    near = min(peaks, key=lambda r: abs(r[0] - NORTH_RULE_PX_Y)) if peaks else None
    if near is None or abs(near[0] - NORTH_RULE_PX_Y) > tol:
        bad.append(f"the tract's north boundary: committed y {NORTH_RULE_PX_Y}, nearest "
                   f"sheet peak {near[0] if near else None}")

    if bad:
        for line in bad:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    print(f"wabansia block grid: every committed rule is still a peak on the raster "
          f"within {tol:.0f} px, and so is the tract's north boundary")
    return 0


def self_test() -> int:
    """Break one input at a time and require exactly the assertion that guards it."""
    import copy
    base = _wrap(read())
    if assertions(base):
        for line in assertions(base):
            print(f"FAIL: the untouched reading already fails: {line}", file=sys.stderr)
        return 1

    cases = []

    d = copy.deepcopy(base); d["blocks"].pop()
    cases.append(("a cell dropped", d, "21 cells"))

    d = copy.deepcopy(base); d["blocks"][0]["number"] = 58
    cases.append(("a number moved off the run", d, "59-79 is not closed"))

    d = copy.deepcopy(base)
    for b in d["blocks"]:
        if b["column"] == "C" and b["tier"] == "t3":
            b["confidence"] = "documented"
    cases.append(("the ambiguous figure upgraded", d, "documented off an ambiguous glyph"))

    d = copy.deepcopy(base)
    for b in d["blocks"]:
        if b.get("legibility") == "faint":
            b.pop("note", None)
    cases.append(("a faint figure's note dropped", d, "says nothing about why"))

    d = copy.deepcopy(base)
    for c in d["columns"]:
        if c["lot_divider_px"] is not None:
            c["lot_divider_px"] = c["west_px"] + 12.0
            break
    cases.append(("a lot divider pushed off the midpoint", d, "off the block's midpoint"))

    d = copy.deepcopy(base); d["north_south_streets"][0]["corridor_px"] = 12.0
    cases.append(("a corridor collapsed", d, "mis-taken rule"))

    d = copy.deepcopy(base); d["west_margin"][0]["width_px"] = 40.0
    cases.append(("the west margin widened to a street", d, "has to be named"))

    d = copy.deepcopy(base); d["arithmetic"]["unaccounted"] = []
    cases.append(("the 55-58 gap closed", d, "the gap between"))

    d = copy.deepcopy(base); d["arithmetic"]["refused"] = ""
    cases.append(("the refusal deleted", d, "stopped being refused"))

    d = copy.deepcopy(base); d["jog"]["step_px"] = 4.0
    cases.append(("the jog closed", d, "one of the two rules moved"))

    d = copy.deepcopy(base); d["tiers"][0]["depth_px"] = 999.0
    cases.append(("tier 1 lengthened past the others", d, "no longer the short one"))

    d = copy.deepcopy(base); d["blocks"][0]["numeral_crop_px"][0] = -5.0
    cases.append(("a crop pushed off the raster", d, "not a box inside"))

    ok = True
    for name, doc, want in cases:
        fired = [b for b in assertions(doc) if want in b]
        if not fired:
            print(f"FAIL: `{name}` fired nothing matching {want!r}", file=sys.stderr)
            ok = False
    if not ok:
        return 1
    print(f"wabansia block numerals self-test: {len(cases)} broken inputs, each caught "
          "by its own assertion")
    return 0


def report(doc: dict) -> int:
    print(f"Wabansia block numerals — {len(doc['blocks'])} cells, "
          f"{doc['scheme']['first']}-{doc['scheme']['last']}\n")
    tiers = {t["id"]: t for t in doc["tiers"]}
    print("        " + "".join(f"{c:>10}" for c in COLUMN_IDS))
    by = {(b["column"], b["tier"]): b for b in doc["blocks"]}
    for tier in TIER_IDS:
        row = "".join(f"{by[(c, tier)]['number']:>10}" for c in COLUMN_IDS)
        print(f"  {tier}  {row}   ({tiers[tier]['north']} → {tiers[tier]['south']})")
    print()
    for leg in doc["scheme"]["legs"]:
        print(f"  column {leg['column']}: {leg['from']}-{leg['to']}, {leg['direction']}")
    a = doc["arithmetic"]
    print(f"\n  Kinzie's Addition {a['kinzie_addition_run'][0]}-"
          f"{a['kinzie_addition_run'][1]}, Wabansia {a['wabansia_run'][0]}-"
          f"{a['wabansia_run'][1]}, unaccounted {a['unaccounted']}")
    print(f"  the B|C street jogs {doc['jog']['step_px']} px "
          f"({doc['jog']['step_m']} m) east at Sailors Street")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.check:
        return check()
    if args.check_sheet:
        return check_sheet()
    if args.self_test:
        return self_test()
    doc = _wrap(read())
    if args.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0
    return report(doc)


if __name__ == "__main__":
    raise SystemExit(main())
