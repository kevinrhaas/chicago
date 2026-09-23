#!/usr/bin/env python3
"""Read Wabansia's river-front water lots off Wright's 1834 survey, as a lot strip.

    tools/read_wabansia_water_lots.py               print the reading
    tools/read_wabansia_water_lots.py --write       write the trace
    tools/read_wabansia_water_lots.py --check       re-derive it from the committed pixels
    tools/read_wabansia_water_lots.py --check-sheet  re-measure every rule off the raster
    tools/read_wabansia_water_lots.py --self-test   break each assertion and watch it fire

WHAT THIS FILE IS AND IS NOT. It is the READING of the triangular water-lot tract wedged
between Wabansia's east column of blocks and the North Branch — the strip T-1074 named as
"not read, and somebody else's". Every number below is a PIXEL statement about
chicago/pre_fire_v1/maps/images/1834-wright-map.jpg. It authors NO ground: seating
Wabansia on modern ground is T-1070's, and nothing here should be read as having done it.

WHY A LOT STRIP AND NOT A GRID, which is the whole reason this tract needed its own
ticket. Wabansia's blocks are a grid and T-1074 could read them as one: tiers crossed by
columns, every cell the rectangle two rules leave. This tract is not. Its lot rules run
PARALLEL TO THE RIVER, at a raster dx/dy of 0.45 — about N24E — while the tract's west
boundary runs very nearly straight north-south at x 1255, a fiftieth of a pixel of drift
per pixel of y. Two lines that are not parallel open a wedge, and the wedge is the tract: nothing
at the apex, four ranks of lots wide at Kinzie Street. So the ranks do not all exist over
the same ground, and a rank BEGINS, geometrically, where the west boundary has drawn far
enough away from that rank's own east rule to leave room for one lot. That derivation is
in `ranks[].north_tip_px_y` and `--check` re-derives it rather than trusting the table.

THE READING, rank by rank, east to west, with the run written in Wright's own hand:

    rank            rules (sheared x at y 1900)        cells   figures read
    river front     rule b 1210 .. the bank               13    1-13, south to north
    second          rule c 1154 .. rule b                  9    14-22, north to south
    third           rule d 1065 .. rule c                  8    25, 26, 27, 28, four refused
    corner wedge    the west boundary .. rule d            3    none legible

which makes the strip a BOUSTROPHEDON like the block grid beside it, and turning the same
way: it starts at the south-east corner, where Kinzie Street meets the North Branch, runs
NORTH up the river front to 13 at the tract's apex, turns west and runs SOUTH down the
second rank to 22 at Kinzie Street again, and turns west once more.

THE RULE CLOSES TWO RANKS AND NOT THE THIRD, and that is the finding worth carrying out of
here. 1-13 and 14-22 are what Wright writes, cell for cell, in the order the rule puts
them. The rule then hands the third rank's southernmost cell 23 — and Wright writes 25
there, with 26, 27 and 28 rising north of it. TWO FIGURES ARE UNACCOUNTED FOR. Either the
corner wedge is numbered before the third rank, which would put 23 and 24 on the ground
Wright's Kinzie Street band has obliterated, or he skipped two — as this same sheet skips
FOUR between Kinzie's Addition's 54 and Wabansia's 59 (T-1074). Both readings fit every
legible figure in the strip and nothing here separates them, so `run.disagreement` records
the gap and refuses to choose.

WHAT THE SHEET WILL NOT SETTLE, and is refused here rather than guessed. TWENTY-SIX of
the strip's thirty-three cells carry a figure this reading will stand behind. The other
seven are the tract's south-west corner and the third rank's north end, and they are
crossed by three things at once: Wright's Kinzie Street band, the tract's own red
boundary wash, and the west boundary rule drawn hard against the block grid. At 600 dpi
their figures are ink and not numerals. TWENTY-THREE AND TWENTY-FOUR are the two the run
most wants — they are what stands between 22 at the foot of the second rank and 25 at the
foot of the third — and neither is legible. This file does NOT put them on a cell. A
recorded plat of Wabansia, or the Democrat selling a numbered water lot there, would.

THE TWO NAMES WRIGHT LETTERS INSIDE THE TRACT, and what the strip's geometry says about
them. T-1068 read `Kain` and `Water` off the registered scan and recorded them as names
only, with a note that Wright "letters a Water Street inside the triangle, fronting the
North Branch, as he does on both banks downstream". The strip refuses the second half of
that. Both names sit in CORRIDORS THAT CROSS THE STRIP — gaps that open in every rank at
once, running with the lot lines and square to the ranks, from the block grid to the
water. Neither runs along the river. Kain's gap stands between lots 10 and 9 on the river
front and between 15 and 16 in the second rank; Water's between 6 and 5, between 19 and
20, and between 27 and 26. That is a measurement, not a re-reading of the lettering: the
names are T-1068's and stand. What changes is what they are names OF.
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
NUMERALS = ROOT / "data/traces/wabansia_block_numbering.json"
ADDITION = ROOT / "data/traces/kinzie_addition_street_grid.json"
OUT = ROOT / "data/traces/wabansia_water_lots.json"
FT = 0.3048

# THE STRIP'S OWN SHEAR. The lot rules run with the river, not with the block grid: the
# slope that stacks them into one bin, scanned the way T-1068 scanned its corridors.
SHEAR = 0.45
# Sheared x below always means x - SHEAR * (y - YREF), so a rule parallel to the lots is
# a constant and the tract's north-south west boundary is not.
YREF = 1530.0

# THE TRACT'S BOUNDS. The west boundary is the block grid's east margin and is a straight
# north-south line on the raster; the north apex and the Kinzie Street line close the
# wedge; the east boundary is the North Branch and is not straight at all, so it is
# committed as the stations it was measured at.
WEST_BOUNDARY_PX_X = (1255.3, 0.020)   # raster x at y 1900, drift per pixel of y
APEX_PX_Y = 1546.0
KINZIE_PX_Y = 2070.0
BANK_STATIONS = [(1665, 1279.0), (1722, 1286.0), (1792, 1285.0), (1838, 1283.0),
                 (1895, 1288.0), (1970, 1307.0), (2015, 1318.0), (2047, 1338.0)]

# THE RANK RULES, in sheared x, each fitted through the peaks it was measured at over the
# y range it exists on: (value at y 1900, drift per pixel of y). They are not quite
# constants — the tract's own tilt leaks through at a tenth of a pixel per pixel.
RANK_RULES = {
    "b": (1209.8, 0.100),   # river front | second rank
    "c": (1154.4, 0.078),   # second      | third rank
    "d": (1065.0, 0.050),   # third       | corner wedge
}

# THE READING. mid_px is where the figure stands on the raster; `legibility` is about the
# ink and nothing else, `confidence` is this project's grade. A `None` figure is a cell
# this reading looked at and refused.
RANKS = ["river_front", "second", "third", "corner"]
READING = [
    # rank          mid_px          figure  legibility   confidence     note
    ("river_front", (1555, 2064), 1, "obliterated", "inferred",
     "The strip's south-east corner cell, where Wright's Kinzie Street band, the tract's "
     "boundary wash and the river bank all cross. A stroke stands in it; a figure does "
     "not resolve. It is the one cell the run can carry without choosing: the river "
     "front holds thirteen cells, twelve of them read 2-13 rising northward, and this is "
     "the end the run starts from. Graded `inferred` for that and not upgraded."),
    ("river_front", (1528, 2038), 2, "clear", "documented", None),
    ("river_front", (1507, 2008), 3, "clear", "documented", None),
    ("river_front", (1480, 1970), 4, "clear", "documented", None),
    ("river_front", (1455, 1938), 5, "clear", "documented", None),
    ("river_front", (1400, 1858), 6, "clear", "documented", None),
    ("river_front", (1390, 1820), 7, "clear", "documented", None),
    ("river_front", (1365, 1785), 8, "clear", "documented", None),
    ("river_front", (1355, 1745), 9, "clear", "documented", None),
    ("river_front", (1320, 1688), 10, "faint", "documented",
     "Read again at 10x: the second glyph is a closed round bowl with no bar over it, "
     "which is this hand's 0 and not its 5 — Wright's 5 carries a flat top bar and an "
     "open bowl, as the 5 on the river front four cells south does."),
    ("river_front", (1305, 1652), 11, "clear", "documented", None),
    ("river_front", (1266, 1605), 12, "clear", "documented", None),
    ("river_front", (1268, 1558), 13, "clear", "documented",
     "The apex cell, a triangle rather than a lot: the tract's two boundaries close on it."),
    ("second", (1250, 1700), 14, "pinched", "inferred",
     "The second rank's north tip, a cell some 30 px deep and 12 px wide where the west "
     "boundary has only just cleared the rule. Two strokes stand in it and neither "
     "resolves at 600 dpi. The figure is the run's, not the ink's, and is graded for it."),
    ("second", (1253, 1730), 15, "pinched", "inferred",
     "The same as 14 one cell south, and refused for the same reason: a mark the width of "
     "the cell, not a numeral. Carried by the run between 14 and 16."),
    ("second", (1290, 1783), 16, "clear", "documented", None),
    ("second", (1315, 1822), 17, "clear", "documented", None),
    ("second", (1331, 1858), 18, "clear", "documented", None),
    ("second", (1345, 1898), 19, "clear", "documented", None),
    ("second", (1377, 1962), 20, "faint", "documented",
     "Written small against the cell's north line, under the tail of Wright's `Water`. "
     "Two glyphs, the second a closed bowl: 20, and the rank's run puts it between 19 "
     "and 21."),
    ("second", (1390, 2005), 21, "clear", "documented", None),
    ("second", (1410, 2040), 22, "clear", "documented", None),
    ("third", (1334, 2038), 25, "clear", "documented", None),
    ("third", (1316, 2000), 26, "clear", "documented", None),
    ("third", (1285, 1930), 27, "clear", "documented", None),
    ("third", (1262, 1900), 28, "faint", "documented",
     "Half a stroke lighter than the 27 one cell south and crowded against the boundary "
     "wash; two closed bowls in the second glyph, no descender, so it is an 8."),
]

# THE CELLS THE STRIP HOLDS, rank by rank, counted off the lot lines rather than off the
# figures — so a rank with more cells than figures says so in arithmetic.
CELLS_PER_RANK = {"river_front": 13, "second": 9, "third": 8, "corner": 3}

# WHAT IS REFUSED. Written down because a strip with a hole in its run has to say where
# the hole is, and what would close it.
REFUSED = {
    "figures": [23, 24],
    "cells": 7,
    "where": "the tract's south-west corner and the third rank's north end — seven cells "
             "in all, four in the third rank above 28 and three in the corner wedge",
    "why": "Wright's Kinzie Street band, the tract's red boundary wash and the west "
           "boundary rule drawn hard against the block grid all cross this ground, and "
           "at 600 dpi what stands in those cells is ink rather than numerals",
    "what_would_settle_it": "a recorded plat of Wabansia, or a Democrat notice selling a "
                            "numbered water lot in the tract with its rank named",
}

# THE TWO CROSSING CORRIDORS. Each is committed as the gap it opens in every rank it
# crosses: (rank, north lot, south lot, y of the gap's north edge, y of its south edge).
# Wright's names are T-1068's and are quoted, not re-read.
CORRIDORS = [
    {"id": "kain", "name_on_sheet": "Kain", "from": "T-1068",
     "gaps": [("river_front", 10, 9, 1706.0, 1740.0),
              ("second", 15, 16, 1745.0, 1768.0)]},
    {"id": "water", "name_on_sheet": "Water", "from": "T-1068",
     "gaps": [("river_front", 6, 5, 1872.0, 1918.0),
              ("second", 19, 20, 1915.0, 1948.0),
              ("third", 27, 26, 1948.0, 1985.0)]},
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
    """The price of this method on this sheet, borrowed from T-1060 exactly as T-1068 and
    T-1074 borrowed it: the Original Town's corridors are platted at 80 ft and read 83.6
    ft here, so every foot figure is reported raw AND divided by that ratio."""
    a = json.loads(ADDITION.read_text())["control_summary"]
    return a["method_over_read"], a["original_town_read_ft"]


def sheared(px: float, py: float) -> float:
    """A pixel's x with the strip's own shear taken out. A rule parallel to the lots is a
    constant in this coordinate; the tract's north-south west boundary is not."""
    return px - SHEAR * (py - YREF)


def rule_x(rule: str, py: float) -> float:
    at1900, drift = RANK_RULES[rule]
    return at1900 + drift * (py - 1900.0)


def west_x(py: float) -> float:
    """The tract's west boundary in sheared x. It runs very nearly straight north-south on
    the raster — a fiftieth of a pixel of drift per pixel of y, against the lot rules'
    0.45 — so it slopes steeply here, and that slope is the whole shape of the tract."""
    at1900, drift = WEST_BOUNDARY_PX_X
    return sheared(at1900 + drift * (py - 1900.0), py)


def bank_x(py: float) -> float:
    """The North Branch bank in sheared x, interpolated between the stations it was
    measured at. Outside them it holds the nearest station, which is what the apex and
    the Kinzie line need."""
    xs = [s[0] for s in BANK_STATIONS]
    ys = [s[1] for s in BANK_STATIONS]
    if py <= xs[0]:
        return ys[0]
    if py >= xs[-1]:
        return ys[-1]
    for (a, av), (b, bv) in zip(BANK_STATIONS, BANK_STATIONS[1:]):
        if a <= py <= b:
            return av + (bv - av) * (py - a) / (b - a)
    raise AssertionError("unreachable")


def rank_bounds(rank: str, py: float) -> tuple[float, float]:
    """A rank's west and east rule in sheared x at a given raster y. The river front's
    east rule is the water; the corner wedge's west rule is the tract boundary."""
    if rank == "river_front":
        return rule_x("b", py), bank_x(py)
    if rank == "second":
        return rule_x("c", py), rule_x("b", py)
    if rank == "third":
        return rule_x("d", py), rule_x("c", py)
    return west_x(py), rule_x("d", py)


def north_tip(rank: str) -> float:
    """WHERE A RANK BEGINS, derived and not typed. The tract's west boundary runs north-
    south and the rank rules run with the river, so the two converge northward: a rank
    exists only south of the y where the boundary crosses its own east rule. For the
    river front that crossing is the tract's apex itself."""
    if rank == "river_front":
        return APEX_PX_Y
    east = {"second": "b", "third": "c", "corner": "d"}[rank]
    lo, hi = APEX_PX_Y, KINZIE_PX_Y
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if west_x(mid) < rule_x(east, mid):
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2.0, 1)


def crop_px(mid: tuple[float, float]) -> list[float]:
    """The box a figure was read in: the numerals in this tract are half the height of
    the block grid's, so the crop is half the size of T-1074's and centred on the mark."""
    x, y = mid
    return [round(x - 22.0, 1), round(y - 16.0, 1), round(x + 22.0, 1), round(y + 16.0, 1)]


def _span(to_local, ax, ay, bx, by) -> float:
    e0, n0 = to_local(ax, ay)
    e1, n1 = to_local(bx, by)
    return math.hypot(e1 - e0, n1 - n0)


def run_scheme() -> dict:
    """The run, derived from the boustrophedon rule alone so the reading can be checked
    against it rather than against itself — and the point where the rule and the ink part
    company, which is the finding this file carries out of the strip.

    The rule: start in the south-east corner, where Kinzie Street meets the North Branch,
    run NORTH up the river front, turn west at the apex, run SOUTH down the second rank,
    turn west at Kinzie Street and run north again. That is the block grid's own turn
    (T-1074), read on a strip instead of a grid, and starting from the same corner.

    It closes the first two ranks exactly: 1-13 and 14-22 are what the sheet reads, cell
    for cell, in the order the rule puts them. It does NOT close the third. The rule
    hands the third rank's southernmost cell 23; Wright writes 25 there, and 26, 27 and 28
    rise north of it on the four cells above. Two figures are unaccounted for, and this
    file does not choose between the two readings that would account for them — see
    `disagreement`."""
    legs = []
    n = 1
    for rank, direction in (("river_front", "south to north"),
                            ("second", "north to south")):
        count = CELLS_PER_RANK[rank]
        legs.append({"rank": rank, "from": n, "to": n + count - 1, "direction": direction,
                     "closed_by_the_sheet": True})
        n += count
    return {
        "legs": legs,
        "first": 1,
        "cells": sum(CELLS_PER_RANK.values()),
        "rule": "a boustrophedon from the south-east corner, north up the river front and "
                "south down the rank behind it, turning west at each end",
        "disagreement": {
            "rank": "third",
            "run_would_give_its_foot": n,
            "sheet_reads_at_its_foot": 25,
            "unaccounted": [23, 24],
            "readings_on_offer": [
                "the corner wedge's cells are numbered before the third rank's, which "
                "would put 23 and 24 on ground the Kinzie Street band has obliterated",
                "Wright skipped two, as this same sheet skips four between Kinzie's "
                "Addition's 54 and Wabansia's 59 (T-1074, data/traces/"
                "wabansia_block_numbering.json § arithmetic)",
            ],
            "refused": "this file does not choose. Both readings are consistent with "
                       "every legible figure in the strip, and nothing on the sheet "
                       "separates them.",
        },
    }


def read() -> dict:
    to_local = _frame()
    ratio, read_ft = _control()

    ranks = []
    for rank in RANKS:
        tip = north_tip(rank)
        mid_y = (tip + KINZIE_PX_Y) / 2.0
        w, e = rank_bounds(rank, mid_y)
        width_m = _span(to_local, w + SHEAR * (mid_y - YREF), mid_y,
                        e + SHEAR * (mid_y - YREF), mid_y)
        ranks.append({
            "id": rank,
            "west_rule": {"river_front": "b", "second": "c", "third": "d",
                          "corner": "tract west boundary"}[rank],
            "east_rule": {"river_front": "the North Branch bank", "second": "b",
                          "third": "c", "corner": "d"}[rank],
            "north_tip_px_y": tip,
            "south_line_px_y": KINZIE_PX_Y,
            "length_px": round(KINZIE_PX_Y - tip, 1),
            "cells": CELLS_PER_RANK[rank],
            "depth_px_at_mid": round(e - w, 1),
            "depth_m_at_mid": round(width_m, 2),
            "depth_ft_raw": round(width_m / FT, 1),
            "depth_ft_controlled": round(width_m / FT / ratio, 1),
        })

    lots = []
    for rank, mid, figure, legibility, confidence, note in READING:
        w, e = rank_bounds(rank, mid[1])
        rec = {
            "figure": figure,
            "rank": rank,
            "mid_px": [float(mid[0]), float(mid[1])],
            "sheared_x": round(sheared(*mid), 1),
            "rank_bounds_sheared_x": [round(w, 1), round(e, 1)],
            "numeral_crop_px": crop_px(mid),
            "legibility": legibility,
            "confidence": confidence,
        }
        if note:
            rec["note"] = note
        lots.append(rec)

    # The lot pitch, measured along each rank between the figures it actually carries, so
    # a frontage is a distance between two committed marks and not a division.
    pitch = []
    for rank in RANKS:
        seq = [l for l in lots if l["rank"] == rank]
        seq.sort(key=lambda l: l["mid_px"][1])
        split = {tuple(sorted(g[1:3])) for c in CORRIDORS for g in c["gaps"]
                 if g[0] == rank}
        gaps = []
        for a, b in zip(seq, seq[1:]):
            pair = tuple(sorted((a["figure"], b["figure"])))
            if pair[1] - pair[0] != 1 or pair in split:
                continue          # a corridor stands between them, not a lot line
            gaps.append(_span(to_local, a["mid_px"][0], a["mid_px"][1],
                              b["mid_px"][0], b["mid_px"][1]))
        if gaps:
            m = sum(gaps) / len(gaps)
            pitch.append({"rank": rank, "adjacent_pairs": len(gaps),
                          "pitch_m": round(m, 2), "pitch_ft_raw": round(m / FT, 1),
                          "pitch_ft_controlled": round(m / FT / ratio, 1)})

    corridors = []
    for c in CORRIDORS:
        gaps = []
        for rank, north, south, y0, y1 in c["gaps"]:
            mid_y = (y0 + y1) / 2.0
            w, e = rank_bounds(rank, mid_y)
            gaps.append({
                "rank": rank, "between": [north, south],
                "px_y": [y0, y1], "width_px": round(y1 - y0, 1),
                "width_m": round(_span(to_local, e + SHEAR * (y0 - YREF), y0,
                                       e + SHEAR * (y1 - YREF), y1), 2),
                "rank_bounds_sheared_x": [round(w, 1), round(e, 1)],
            })
        corridors.append({
            "id": c["id"], "name_on_sheet": c["name_on_sheet"],
            "name_from": "data/traces/wabansia_streets.json § water_lot_tract_streets "
                         "(T-1068)",
            "bearing": "across the strip, square to the ranks and with the lot lines",
            "gaps": gaps,
            "crosses_ranks": [g["rank"] for g in gaps],
        })

    return {
        "bounds": {
            "west_boundary": {"raster_x_at_1900": WEST_BOUNDARY_PX_X[0],
                              "drift_per_px_y": WEST_BOUNDARY_PX_X[1]},
            "west_boundary_note": "very nearly straight north-south on the raster, and "
                                  "the line every rank diverges from. It stands some 40 "
                                  "px east of the block grid's own east rule (T-1074 § "
                                  "columns C east), so the two are not the same line and "
                                  "what lies between them is the north-south street that "
                                  "reading refused to name",
            "apex_px_y": APEX_PX_Y,
            "kinzie_px_y": KINZIE_PX_Y,
            "bank_stations_px": [[a, b] for a, b in BANK_STATIONS],
        },
        "rank_rules": {k: {"sheared_x_at_1900": v[0], "drift_per_px_y": v[1]}
                       for k, v in RANK_RULES.items()},
        "ranks": ranks,
        "lots": lots,
        "pitch": pitch,
        "corridors": corridors,
        "run": run_scheme(),
        "refused": REFUSED,
        "control_summary": {"method_over_read": ratio, "original_town_read_ft": read_ft},
        "not_read": [
            "the seating of any of this on modern ground (T-1070)",
            "the tract polygon the legend colours red (T-0792)",
            "whether the strip's lots were sold, and to whom, before 1 July 1835 (T-0790)",
            "the figures in the third rank above 28 and in the corner wedge, refused above",
        ],
    }


def _wrap(doc):
    g = json.loads(GCP.read_text())
    return {
        "_doc": __doc__,
        "ticket": "T-1077",
        "raster": {k: g["raster"][k] for k in
                   ("working_copy", "width", "height", "dpi", "sha256", "source_id")},
        "registration": {"gcp_file": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
                         "rms_m": g["fit"].get("rms_m", g["fit"].get("residual_rms_m"))},
        "method": {
            "shear": SHEAR,
            "shear_reference_px_y": YREF,
            "blocks_from": "data/traces/wabansia_block_numbering.json (T-1074)",
            "names_from": "data/traces/wabansia_streets.json (T-1068)",
            "discrimination": "a rank rule runs with the river and is a constant in "
                              "sheared x; the tract's west boundary runs north-south and "
                              "is not, and the wedge the two open is what decides how "
                              "many ranks stand on any piece of this ground",
        },
        **doc,
    }


# ------------------------------------------------------------------ the assertions

def assertions(doc: dict) -> list[str]:
    """Each failure is its own string so `--self-test` can break one input at a time and
    watch exactly one of them fire."""
    bad: list[str] = []
    lots = doc["lots"]
    w, h = doc["raster"]["width"], doc["raster"]["height"]
    ranks = {r["id"]: r for r in doc["ranks"]}

    figures = [l["figure"] for l in lots]
    if len(set(figures)) != len(figures):
        twice = sorted({f for f in figures if figures.count(f) > 1})
        bad.append(f"a figure stands on two cells: {twice}")

    front = sorted([l for l in lots if l["rank"] == "river_front"],
                   key=lambda l: -l["mid_px"][1])
    if [l["figure"] for l in front] != list(range(1, 14)):
        bad.append("the river front does not read 1-13 south to north: "
                   f"{[l['figure'] for l in front]}")
    second = sorted([l for l in lots if l["rank"] == "second"], key=lambda l: l["mid_px"][1])
    if [l["figure"] for l in second] != list(range(14, 23)):
        bad.append("the second rank does not read 14-22 north to south: "
                   f"{[l['figure'] for l in second]}")
    third = sorted([l for l in lots if l["rank"] == "third"], key=lambda l: -l["mid_px"][1])
    if [l["figure"] for l in third] != [25, 26, 27, 28]:
        bad.append("the third rank's legible figures are no longer 25-28 rising "
                   f"northward: {[l['figure'] for l in third]}")
    if any(l["rank"] == "corner" for l in lots):
        bad.append("a figure has been placed in the corner wedge, which this reading "
                   "refuses in writing")

    for leg in doc["run"]["legs"]:
        seq = [l for l in lots if l["rank"] == leg["rank"]]
        placed = sorted(l["figure"] for l in seq)
        if placed != list(range(leg["from"], leg["to"] + 1)):
            bad.append(f"the {leg['rank']} rank carries {placed} and the run gives it "
                       f"{leg['from']}-{leg['to']}; that leg is committed as closed")
        if len(seq) != CELLS_PER_RANK[leg["rank"]]:
            bad.append(f"the {leg['rank']} leg is committed as closed by the sheet and "
                       f"{len(seq)} of its {CELLS_PER_RANK[leg['rank']]} cells carry a "
                       "figure")
    dis = doc["run"]["disagreement"]
    foot = max((l for l in lots if l["rank"] == dis["rank"]),
               key=lambda l: l["mid_px"][1])["figure"]
    if foot != dis["sheet_reads_at_its_foot"]:
        bad.append(f"the {dis['rank']} rank's southernmost figure is {foot} and the "
                   f"disagreement is written against {dis['sheet_reads_at_its_foot']}")
    if dis["sheet_reads_at_its_foot"] - dis["run_would_give_its_foot"] != len(
            dis["unaccounted"]):
        bad.append("the run and the sheet part by a different number of figures than "
                   f"{dis['unaccounted']} accounts for")
    if len(dis["readings_on_offer"]) < 2 or not dis.get("refused"):
        bad.append("the disagreement has stopped offering two readings and refusing to "
                   "choose between them")
    if doc["run"]["cells"] != sum(r["cells"] for r in doc["ranks"]):
        bad.append("the run counts a different number of cells than the ranks hold")

    for l in lots:
        x0, y0, x1, y1 = l["numeral_crop_px"]
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h or x1 <= x0 or y1 <= y0:
            bad.append(f"lot {l['figure']}'s crop {l['numeral_crop_px']} is not a box "
                       f"inside the {w}x{h} raster")
        lo, hi = l["rank_bounds_sheared_x"]
        if not lo < l["sheared_x"] < hi:
            bad.append(f"lot {l['figure']} stands at sheared x {l['sheared_x']}, outside "
                       f"its own {l['rank']} rank [{lo}, {hi}]")
        if not ranks[l["rank"]]["north_tip_px_y"] <= l["mid_px"][1] <= KINZIE_PX_Y:
            bad.append(f"lot {l['figure']} stands at y {l['mid_px'][1]}, off the "
                       f"{l['rank']} rank's own length")
        if l["confidence"] not in ("documented", "inferred"):
            bad.append(f"lot {l['figure']} is graded `{l['confidence']}`")
        if l["confidence"] != "documented" and "note" not in l:
            bad.append(f"lot {l['figure']} is not documented and says nothing about why")
        if l["legibility"] not in ("clear", "faint", "pinched", "obliterated"):
            bad.append(f"lot {l['figure']} is graded `{l['legibility']}`")
        if l["legibility"] != "clear" and "note" not in l:
            bad.append(f"lot {l['figure']} is graded `{l['legibility']}` and says "
                       "nothing about why")
        if l["legibility"] in ("pinched", "obliterated") and l["confidence"] == "documented":
            bad.append(f"lot {l['figure']} is documented off a figure the sheet does not "
                       "resolve — the run may carry it, and carrying is `inferred`")

    # THE WEDGE. Each rank begins where the tract's west boundary clears that rank's own
    # east rule, and the four tips therefore run north to south in rank order. A rank
    # whose tip has stopped deriving is a rank rule that has moved.
    tips = [ranks[r]["north_tip_px_y"] for r in RANKS]
    if tips != sorted(tips):
        bad.append(f"the ranks no longer open northward in order: {tips}")
    for r in RANKS:
        if abs(north_tip(r) - ranks[r]["north_tip_px_y"]) > 0.2:
            bad.append(f"the {r} rank's north tip {ranks[r]['north_tip_px_y']} is not "
                       f"where the boundary crosses its rule ({north_tip(r)})")
        if ranks[r]["length_px"] <= 0:
            bad.append(f"the {r} rank has no length")
        if ranks[r]["depth_px_at_mid"] <= 0:
            bad.append(f"the {r} rank's rules are not west-then-east at its midpoint")
    if not west_x(APEX_PX_Y) > rule_x("b", APEX_PX_Y):
        bad.append("the tract's west boundary no longer stands east of the river front's "
                   "rule at the apex — the wedge has stopped closing and the strip would "
                   "be a grid")
    if not west_x(KINZIE_PX_Y) < rule_x("d", KINZIE_PX_Y):
        bad.append("the corner wedge has closed at Kinzie Street, where the sheet draws "
                   "four ranks")

    for p in doc["pitch"]:
        if not 8.0 <= p["pitch_m"] <= 40.0:
            bad.append(f"the {p['rank']} rank's lots front {p['pitch_m']} m each — a "
                       "water lot on this sheet is neither a footpath nor a block")
    # THE STRIP'S OWN CROSS-CHECK. Three ranks, measured independently between figures
    # Wright wrote, and they agree on the lot module to within a couple of metres. Ranks
    # that stop agreeing mean a rank rule has been taken off a lot line.
    if doc["pitch"]:
        span = max(p["pitch_m"] for p in doc["pitch"]) - min(p["pitch_m"]
                                                             for p in doc["pitch"])
        if span > 5.0:
            bad.append(f"the ranks' frontages disagree by {span:.2f} m — they agreed to "
                       "within 2.5, and a rank that has drifted off that is a rule taken "
                       "off a lot line")

    for c in doc["corridors"]:
        if len(c["gaps"]) < 2:
            bad.append(f"the {c['id']} corridor is committed on one rank only, which is "
                       "a gap between two lots and not a street across the strip")
        ys = [g["px_y"][0] for g in c["gaps"]]
        if ys != sorted(ys):
            bad.append(f"the {c['id']} corridor's gaps do not step southward as they go "
                       f"west: {ys}")
        for g in c["gaps"]:
            if not 15.0 <= g["width_px"] <= 60.0:
                bad.append(f"the {c['id']} corridor's gap in the {g['rank']} rank "
                           f"measures {g['width_px']} px — outside that it is a lot line "
                           "or a missed rule, not a corridor")
        if "fronting" in json.dumps(c):
            bad.append(f"the {c['id']} corridor has gone back to fronting the river; the "
                       "strip's own geometry is what refused that")

    r = doc["refused"]
    if sorted(r["figures"]) != sorted(doc["run"]["disagreement"]["unaccounted"]):
        bad.append(f"the refusal names {r['figures']} and the run's disagreement is "
                   f"written about {doc['run']['disagreement']['unaccounted']}")
    if not r.get("what_would_settle_it"):
        bad.append("the refusal has stopped saying what would settle it")
    placed = {l["figure"] for l in lots}
    if placed & set(r["figures"]):
        bad.append("a refused figure has been placed on a cell after all")
    if len(lots) + r["cells"] != doc["run"]["cells"]:
        bad.append(f"{len(lots)} cells carry a figure and {r['cells']} are refused, "
                   f"against {doc['run']['cells']} the ranks hold — the arithmetic of "
                   "what this reading did not settle no longer adds up")
    return bad


# ------------------------------------------------------------------ the gates

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
    n = sum(1 for l in fresh["lots"] if l["confidence"] == "documented")
    print(f"wabansia water lots: {fresh['run']['cells']} cell(s) in four ranks, "
          f"{len(fresh['lots'])} numbered, {n} read off the sheet, "
          f"{fresh['refused']['cells']} refused")
    return 0


def _maxima(prof, floor: float = 12.0):
    """Every local maximum of an imported profile, with no width test — T-1074's, and for
    its reason: this tract's rules are drawn against a boundary wash and a width test
    returns them as one blob or as nothing."""
    vals = [v for _, v in prof]
    return [(prof[i][0], vals[i]) for i in range(1, len(prof) - 1)
            if vals[i] >= vals[i - 1] and vals[i] > vals[i + 1] and vals[i] >= floor]


def check_sheet() -> int:
    """The raster half: every rule this reading committed is still a peak where the sheet
    puts it. Opens the 5050 x 6628 scan, so the PR runs it and tools/check.sh does not."""
    _, img = _k._sheet()
    bad = []
    tol = 6.0
    # `_profile`'s shear is measured from the window's own y0, so a window opened at YREF
    # puts a rule parallel to the lots in the bin its sheared x names.
    stations = [(1640, 1690, ["b"]), (1780, 1830, ["c", "b"]),
                (1880, 1930, ["c", "b"]), (1960, 2000, ["d", "c", "b"]),
                (2000, 2045, ["d", "c", "b"])]
    for y0, y1, want in stations:
        # `_profile` bins raw x and shears from the window's own y0, so the window has to
        # be opened around the sheared range wanted, offset by that same shear.
        off = SHEAR * (y0 - YREF)
        prof = _k._profile(img, int(1000 + off), y0, int(1300 + off), y1, "v", SHEAR)
        peaks = [(x - off, v) for x, v in _maxima(prof, floor=25.0)]
        mid = (y0 + y1) / 2.0
        checks = [("the tract's west boundary", west_x(mid))]
        checks += [(f"rank rule {r}", rule_x(r, mid)) for r in want]
        for name, x in checks:
            near = min(peaks, key=lambda p: abs(p[0] - x)) if peaks else None
            if near is None or abs(near[0] - x) > tol:
                bad.append(f"y {y0}-{y1}: {name}: committed sheared x {x:.1f}, nearest "
                           f"sheet peak {near[0]:.1f}" if near else
                           f"y {y0}-{y1}: {name}: committed sheared x {x:.1f}, no peak")

    # And the two horizontals that close the wedge.
    for name, y, x0, x1 in (("the tract's apex", APEX_PX_Y, 1255, 1290),
                            ("Kinzie Street's north line", KINZIE_PX_Y, 1300, 1420)):
        prof = _k._profile(img, x0, int(y - 18), x1, int(y + 18), "h", 0.0)
        peaks = _maxima(prof, floor=20.0)
        near = min(peaks, key=lambda p: abs(p[0] - y)) if peaks else None
        if near is None or abs(near[0] - y) > tol:
            bad.append(f"{name}: committed y {y}, nearest sheet peak "
                       f"{near[0] if near else None}")

    if bad:
        for line in bad:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    print(f"wabansia water lots: every committed rule is still a peak on the raster "
          f"within {tol:.0f} px, and so are the apex and the Kinzie line")
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

    d = copy.deepcopy(base)
    for l in d["lots"]:
        if l["figure"] == 6:
            l["figure"] = 5
    cases.append(("a figure written twice", d, "stands on two cells"))

    d = copy.deepcopy(base)
    for l in d["lots"]:
        if l["figure"] == 13:
            l["mid_px"][1] = 2060.0
    cases.append(("the river front's run turned over", d, "does not read 1-13"))

    d = copy.deepcopy(base)
    for l in d["lots"]:
        if l["figure"] == 28:
            l["figure"] = 29
    cases.append(("the third rank pushed off 25-28", d, "no longer 25-28"))

    d = copy.deepcopy(base)
    d["lots"].append(dict(d["lots"][0], rank="corner", figure=23))
    cases.append(("a figure guessed into the corner", d, "which this reading refuses"))

    d = copy.deepcopy(base)
    for l in d["lots"]:
        if l["legibility"] == "pinched":
            l["confidence"] = "documented"
    cases.append(("a pinched figure upgraded", d, "carrying is `inferred`"))

    d = copy.deepcopy(base)
    for l in d["lots"]:
        if l["legibility"] == "faint":
            l.pop("note", None)
    cases.append(("a faint figure's note dropped", d, "says nothing about why"))

    d = copy.deepcopy(base)
    for l in d["lots"]:
        if l["figure"] == 16:
            l["sheared_x"] = 900.0
    cases.append(("a lot moved out of its rank", d, "outside"))

    d = copy.deepcopy(base)
    for r in d["ranks"]:
        if r["id"] == "third":
            r["north_tip_px_y"] = 1600.0
    cases.append(("a rank's tip typed instead of derived", d, "is not where the boundary"))

    d = copy.deepcopy(base)
    for r in d["ranks"]:
        if r["id"] == "corner":
            r["north_tip_px_y"] = 1540.0
    cases.append(("the wedge opened in the wrong order", d, "open northward in order"))

    d = copy.deepcopy(base)
    d["pitch"][0]["pitch_m"] = 2.0
    cases.append(("a frontage collapsed to a footpath", d, "neither a footpath nor a block"))

    d = copy.deepcopy(base)
    d["pitch"][0]["pitch_m"] = 39.0
    cases.append(("one rank's frontage drifted off the others", d, "frontages disagree"))

    d = copy.deepcopy(base)
    d["corridors"][1]["gaps"] = d["corridors"][1]["gaps"][:1]
    cases.append(("a crossing corridor reduced to one rank", d, "not a street across"))

    d = copy.deepcopy(base)
    d["corridors"][0]["bearing"] = "fronting the North Branch"
    cases.append(("the refuted river-front reading restored", d, "back to fronting"))

    d = copy.deepcopy(base)
    d["corridors"][0]["gaps"][0]["width_px"] = 4.0
    cases.append(("a corridor closed to a lot line", d, "not a corridor"))

    d = copy.deepcopy(base)
    d["refused"]["figures"] = []
    cases.append(("the refusal emptied", d, "the run's disagreement is"))

    d = copy.deepcopy(base)
    d["refused"]["what_would_settle_it"] = ""
    cases.append(("the refusal stopped saying what would close it",
                  d, "what would settle it"))

    d = copy.deepcopy(base)
    d["refused"]["cells"] = 0
    cases.append(("the refused cells uncounted", d, "no longer adds up"))

    d = copy.deepcopy(base)
    d["lots"][0]["numeral_crop_px"][0] = -5.0
    cases.append(("a crop pushed off the raster", d, "not a box inside"))

    ok = True
    for name, doc, want in cases:
        fired = [b for b in assertions(doc) if want in b]
        if not fired:
            print(f"FAIL: `{name}` fired nothing matching {want!r}", file=sys.stderr)
            ok = False
    if not ok:
        return 1
    print(f"wabansia water lots self-test: {len(cases)} broken inputs, each caught by "
          "its own assertion")
    return 0


def report(doc: dict) -> int:
    print(f"Wabansia's water-lot strip — {doc['run']['cells']} cells in "
          f"{len(doc['ranks'])} ranks, {len(doc['lots'])} numbered\n")
    for r in doc["ranks"]:
        print(f"  {r['id']:<12} y {r['north_tip_px_y']:>6} → {r['south_line_px_y']}, "
              f"{r['cells']:>2} cells, {r['depth_m_at_mid']:>6} m deep at its midpoint "
              f"({r['depth_ft_controlled']} ft controlled)")
    print()
    for leg in doc["run"]["legs"]:
        print(f"  {leg['rank']:<12} {leg['from']}-{leg['to']}, {leg['direction']}")
    dis = doc["run"]["disagreement"]
    print(f"  {dis['rank']:<12} the run gives its foot {dis['run_would_give_its_foot']}, "
          f"the sheet reads {dis['sheet_reads_at_its_foot']} — "
          f"{dis['unaccounted']} unaccounted")
    print()
    for p in doc["pitch"]:
        print(f"  {p['rank']:<12} lots front {p['pitch_m']} m "
              f"({p['pitch_ft_controlled']} ft controlled) over {p['adjacent_pairs']} pairs")
    print()
    for c in doc["corridors"]:
        where = ", ".join(f"{g['rank']} {g['between'][0]}|{g['between'][1]}"
                          for g in c["gaps"])
        print(f"  {c['name_on_sheet']:<6} crosses the strip: {where}")
    r = doc["refused"]
    print(f"\n  refused: {r['cells']} cells, and the figures {r['figures']} with them")
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
