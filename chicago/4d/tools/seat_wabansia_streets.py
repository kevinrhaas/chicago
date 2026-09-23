#!/usr/bin/env python3
"""Seat Wabansia on the committed town grid: its streets, its water lots, its outline.

    tools/seat_wabansia_streets.py            print what it would write
    tools/seat_wabansia_streets.py --write    write data/streets/1835.json and the trace
    tools/seat_wabansia_streets.py --check    re-derive the committed lines from the reading

The readings are `data/traces/wabansia_streets.json` (T-0790, the seven east-west
corridors and their names), `data/traces/wabansia_block_numbering.json` (T-1074, the
tiers, the columns and the tract's west margin) and `data/traces/wabansia_water_lots.json`
(T-1077, the river-front lot strip east of the blocks). None of the three authors ground
— each says so in its own words — and this tool is the one that does.

WHY NOT JUST COMMIT THE PIXELS, which is `seat_kinzie_addition_streets.py`'s argument
and is the same one here. Wabansia's south line IS Kinzie Street: Wright letters
`Kinzie` in that corridor, and the committed `kinzie` is the same street off the
Thompson plat. Carried through the NA sheet's own affine, Wright's Kinzie lands south
of the committed line and leaning the wrong way — 9.1 m out at the tract's west end,
1.4 m at its east, because the sheet's drawn bearing in this corner is about 1.2 deg
off the one the committed grid takes from modern control over a baseline four times
longer. That is the fit's error, not the plat's: the registration admits 16.19 m RMS on
eight control points and none of them is within 900 m of this tract.

So the sheet is asked for what it measures well — the perpendicular distance from one
ruled corridor to the next, inside one corner of one raster — and the committed grid is
asked for where that ladder hangs and which way it lies. Every line here is PARALLEL to
committed `kinzie` and offset north of it by the sheet's own measured tier pitches,
accumulated. Nothing is fitted to modern pavement and nothing is chosen to look right.

WHAT IS NOT SEATED, and why each is somebody else's:

  * The two north-south corridors. Wright letters no name on either (T-1074), and this
    project does not commit an unnamed street.
  * The east reach of these STREETS into the water-lot tract — Kain's and Hight's
    subdivision, the wedge between the east column and the river. T-1077's corridors
    `Kain` and `Water` cross the lots and are not these streets continued, so no street
    line here is carried over the wedge. The wedge's own GROUND is seated below
    (T-1086), which is what lets the tract be outlined at all.
  * `kinzie` itself, which stops at local east -320 and is extrapolated 418 m west to
    meet this tract. Wright draws it the whole way and the committed line should be
    carried, but carrying an attested street moves platted lot lines and re-scores the
    corridor-intrusion count, so it is its own unit of work.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STREETS = ROOT / "data/streets/1835.json"
TRACE = ROOT / "data/traces/wabansia_streets.json"
BLOCKS = ROOT / "data/traces/wabansia_block_numbering.json"
WATER_LOTS = ROOT / "data/traces/wabansia_water_lots.json"
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
DATUM = ROOT / "data/datum.json"
BRANCHES = ROOT / "data/terrain/epochs/e1834_harbor_cut/branches.geojson"
OUT = ROOT / "data/traces/wabansia_seating.json"
FT = 0.3048

# The datum street, and the streets seated off it, south to north. `kinzie` is the
# tract's own south line and is already committed; it is the anchor, not an output.
DATUM_ID = "kinzie"
SEATED = ["hubbard", "owen", "hight", "sailors", "trade", "free"]

NAME_2026 = {}   # nothing in this repository attests a modern name in this tract
NAME_NOTE = ("`name_2026` is null because no source in this repository attests what this "
             "street is called today. The registration's eight control points are all in "
             "the Original Town and Kinzie's Addition; none is within 900 m of Wabansia, "
             "so `osm_streets_2026` cannot be asked the question by crossing. A modern "
             "name is not evidence about 1835 and is not guessed at here.")

NOTE = (
    "Wabansia, surveyed 1831 — the earliest speculative addition laid out at Chicago — and "
    "drawn whole on J. S. Wright's 1834 survey, which letters the tract `Wonbonsia` and this "
    "street `{sheet}`. GEOMETRY: the corridor is read off the sheet by "
    "tools/read_wabansia_streets.py and recorded in data/traces/wabansia_streets.json, "
    "found not by width — Wabansia's blocks are four lots deep at a 33 px lot pitch and its "
    "corridors run 28.9-39.2 px, so the two populations overlap and a width test returned "
    "four wrong corridors out of five — but as the rule pair that brackets Wright's own "
    "lettering. The LINE is that reading laid off `kinzie` by tools/seat_wabansia_streets.py: "
    "parallel to the committed line and north of it by the perpendicular distance Wright's "
    "own Kinzie corridor stands from this one on the sheet. Wabansia's south line is Kinzie "
    "Street, "
    "and carried through the sheet's own affine Wright's Kinzie lands 9.1 m south of the "
    "committed line at the tract's west end and 1.4 m at its east — a bearing about 1.2 deg "
    "off, against a registration that admits 16.19 m RMS with no control point within 900 m "
    "of this tract. So the sheet measures the ladder and the committed grid holds it. "
    "CORRIDOR: 24.02 m. The method reads the Original Town's platted 80 ft corridors on this "
    "sheet at 83.6 ft (three readings, sd 5.2) and Wabansia's at 82.3 ft (seven readings, sd "
    "10.4), which against a platted 80 ft is 78.8 ft — so Wabansia is platted on the town's "
    "own street width, and the reading cannot distinguish 78.8 ft from 80 ft inside a control "
    "that itself spreads 5.2 ft. The recorded figure is the read one, not the round one. "
    "STATUS follows `madison`'s and `ohio_north`'s: platted ground, not road. In 1835 this "
    "tract is a survey over prairie — `track_width_m` is 0 because no wagon track is drawn or "
    "attested on it, `alleys` is false because the sheet rules none inside these blocks, and "
    "the confidences say `inferred` because the line is read off Wright's sheet as a ruled "
    "line and anchored on committed control, not traced from a plat this project holds. "
    "EXTENT stops where the reading stops: west at the tract's own boundary rule, east at the "
    "last block corner T-1074 read on the tiers this street divides. Wright carries the grid "
    "east into the water-lot tract — Kain's and Hight's subdivision — and that wedge is "
    "T-1077's, read as a lot strip and not seated. T-0790, piece 3."
)

OCCUPANCY = {
    "question": "whoever the sources put on this ground before 1 July 1835",
    "found": [
        {
            "as_printed": "Doctor Kimberl",
            "normalized": "[uncertain: Doctor Kimberly]",
            "role": "occupant",
            "occupations": ["physician"],
            "claim": "chicago_democrat_1834_07_16#c017",
            "gazetteer_id": "person_uncertain_doctor_kimberly",
            "what": ("a dwelling of four rooms, a kitchen, a barn and a garden, in Wabansia, "
                     "occupied by a doctor and advertised through Col. Hamilton — the only "
                     "house in this run of the Democrat described room by room"),
            "confidence": "documented",
            "note": ("The name is CUT AT THE RIGHT EDGE of the column and the gazetteer "
                     "brackets it; E. S. Kimberly stands in the same issue's candidate list "
                     "and is NOT identified with the doctor. The advertisement places a "
                     "household in Wabansia on 16 July 1834, eleven months before this "
                     "scene's date, and places it NOWHERE INSIDE IT: no block, no lot, no "
                     "street. Seating the streets does not seat this house, and no structure "
                     "is minted from it here."),
        }
    ],
    "searched": [
        "data/research/newspapers/extracted/*.json — every claim naming Wabansia",
        "data/research/newspapers/gazetteer.json — every person with Wabansia in associated_places",
        "data/residents/households/*.json",
    ],
    "reading": ("ONE household, unplaced. Wabansia is named in the Democrat three other times "
                "and each is the same lithographic town map advertised for sale by Kinzie & "
                "Forsyth (1834-07-02, 1834-11-05, 1834-11-19) — a claim about what the town's "
                "inhabitants thought its extent was, not about who lived there. So the tract "
                "this reading draws is, on the evidence this project holds, a survey over "
                "prairie with one doctor's house somewhere in it."),
    "leaves_open": ("data/research/newspapers/place_vocabulary.json still resolves `Wabansia` "
                    "as UNDECIDED on basis B4 — 'a survey adjacent to the town that this "
                    "project commits none of' — and names T-0790 as the ticket that would "
                    "settle it. That sentence is now false of the ground and the ruling is "
                    "the owner's B-rule to change, not this tool's."),
}


# ------------------------------------------------------------------ the frame

def _frame():
    g = json.loads(GCP.read_text())
    d = json.loads(DATUM.read_text())
    # T-1092 re-seated this trace onto the ELEVEN-POINT registration T-1091 adopted,
    # and re-baked what stands on the ground that moved. `fit` IS that registration;
    # the eight-point fit it superseded is kept beside it as `retained_fit` for the
    # adjudication that compares the two. Reading `retained_fit` here would seat the
    # ground on a fit this project no longer holds.
    c = g["fit"]["coefficients"]

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"] - d["origin_utm_e"],
                c["d"] * px + c["e"] * py + c["f"] - d["origin_utm_n"])

    return to_local


def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d)
    return (d[0] / n, d[1] / n)


def _extents(trace, blocks):
    """The west and east pixel bound of each corridor, from T-1074's block grid.

    A corridor divides two tiers and is bounded by what those tiers are bounded by:
    west at the tract's own boundary rule (the OUTER of the west margin's pair, averaged
    over the two tiers, because the boundary slants), east at the farther of the two
    tiers' last block corner. The two disagree by 166 px at Sailors Street, where the
    grid jogs and the blocks south of it are a lot wider than the blocks north; the
    street runs the length of the longer tier because that tier's blocks front it."""
    tiers = {t["id"]: t for t in blocks["tiers"]}
    margin = {w["tier"]: w for w in blocks["west_margin"]}
    east = {}
    for col in blocks["columns"]:
        east[col["tier"]] = max(east.get(col["tier"], 0.0), col["east_px"])
    adj = {}
    ids = {s["id"] for s in trace["streets"]}
    for t in blocks["tiers"]:
        if t["south"] in ids:
            adj.setdefault(t["south"], []).append(t["id"])
        if t["north"] in ids:
            adj.setdefault(t["north"], []).append(t["id"])
    out = {}
    for sid, ts in adj.items():
        ends = sorted((east[t] for t in ts), reverse=True)
        out[sid] = {
            "tiers": sorted(ts),
            "west_px": round(sum(margin[t]["rule_px_x"][0] for t in ts) / len(ts), 2),
            "east_px": ends[0], "east_px_nearer": ends[-1],
        }
    return out, tiers, margin, east


def _bank_px(to_local):
    """The committed west bank of the North Branch, carried back into sheet pixels, so
    the grid's east edge can be checked against water this project already holds."""
    g = json.loads(BRANCHES.read_text())
    d = json.loads(DATUM.read_text())
    # T-1092: the eleven-point fit in force — see _frame above.
    c = json.loads(GCP.read_text())["fit"]["coefficients"]
    a, b, dd, e = c["a"], c["b"], c["d"], c["e"]
    c0, f0 = c["c"] - d["origin_utm_e"], c["f"] - d["origin_utm_n"]
    det = a * e - b * dd
    for feat in g["features"]:
        if feat["properties"].get("name", "").startswith("West bank of the North Branch"):
            pts = []
            for X, Y in feat["geometry"]["coordinates"]:
                u, v = X - d["origin_utm_e"] - c0, Y - d["origin_utm_n"] - f0
                pts.append(((e * u - b * v) / det, (-dd * u + a * v) / det))
            return sorted(pts, key=lambda p: p[1])
    raise SystemExit("the committed west bank of the North Branch is not in branches.geojson")


def _at_y(poly, y):
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if y0 <= y <= y1:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return None


# ------------------------------------------------------ the water-lot wedge (T-1086)
#
# WHY THIS BELONGS IN THIS FILE. T-1070 outlined Wabansia's BLOCK GRID and refused to
# call that outline the tract's, because Wabansia runs east of the blocks to the North
# Branch over a triangular water-lot strip — Kain's and Hight's subdivision — which
# T-1077 read off Wright's sheet as a lot strip and deliberately did not seat. A tract
# with no east boundary has no outline, so `tract_polygon_local_enu_m` stood `seated:
# false` with that sentence in it. The wedge hangs from the same datum, by the same
# ladder, off the same sheet, so seating it anywhere else would mean two tools holding
# one statement — which this repository has been bitten by (see the Michigan St tract's
# gate note in tools/check.sh).
#
# THE WEDGE'S OWN GEOMETRY is rebuilt here from the committed reading and never re-typed:
# its shear, its west boundary, its rank rules and its river bank all come out of
# data/traces/wabansia_water_lots.json, so a changed reading changes this seating and
# `--check` fails until the trace is rewritten.

RANK_SIDES = {
    # rank            west rule        east rule
    "river_front":   ("b",             "bank"),
    "second":        ("c",             "b"),
    "third":         ("d",             "c"),
    "corner":        ("west_boundary", "d"),
}


def _wl_frame(wl):
    """The strip's west boundary, its rank rules and its bank, all in RASTER x.

    T-1077 reports its rules in `sheared x` — x with the strip's own 0.45 lean taken
    out, so that a rule running with the river is a constant — and its west boundary in
    raster x, because that line runs north-south and is not a constant in the sheared
    coordinate. Everything below is put back into raster x, which is the only coordinate
    `seat()` understands."""
    sh = wl["method"]["shear"]
    yref = wl["method"]["shear_reference_px_y"]
    wb = wl["bounds"]["west_boundary"]
    stations = [(float(y), float(x)) for y, x in wl["bounds"]["bank_stations_px"]]

    def unshear(sx, py):
        return sx + sh * (py - yref)

    def west_boundary(py):
        return wb["raster_x_at_1900"] + wb["drift_per_px_y"] * (py - 1900.0)

    def rule(name, py):
        r = wl["rank_rules"][name]
        return unshear(r["sheared_x_at_1900"] + r["drift_per_px_y"] * (py - 1900.0), py)

    def bank(py):
        """The North Branch bank. Outside the stations it holds the nearest one, which is
        T-1077's own convention and is flagged wherever this seating relies on it."""
        if py <= stations[0][0]:
            return unshear(stations[0][1], py)
        if py >= stations[-1][0]:
            return unshear(stations[-1][1], py)
        for (a, av), (b, bv) in zip(stations, stations[1:]):
            if a <= py <= b:
                return unshear(av + (bv - av) * (py - a) / (b - a), py)
        raise AssertionError("unreachable")

    def side(name, py):
        return west_boundary(py) if name == "west_boundary" else \
               bank(py) if name == "bank" else rule(name, py)

    return side, stations


def _meet(x_of_py, row_py, start):
    """Where a boundary that is a function of ROW meets a rule that is a function of
    COLUMN. Kinzie Street's north rule leans east-down at the reading's own 0.019, and
    the wedge's boundaries lean north-east at 0.45 and 0.02, so neither end of the
    tract's south edge is at a row this project can type. Both slopes are small and the
    fixed point converges in a handful of passes; sixty are taken."""
    py = float(start)
    for _ in range(60):
        py = row_py(x_of_py(py))
    return round(x_of_py(py), 2), round(py, 2)


def _area_m2(ring):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def _wedge(seat, south_row, wl, cbank, m_per_px):
    """The water-lot strip on modern ground: its outline, its four ranks, its 26 lots.

    THE NORTH TIP IS A POINT AND IS THE WEST BOUNDARY'S. T-1077 reads the tract's apex at
    row 1546 — the row where its two boundaries close on lot 13, "a triangle rather than
    a lot" — but its bank is measured only from row 1665 south and holds its northernmost
    station above that. So at the apex row the two boundaries stand 28.0 m apart in the
    reading's own arithmetic, which is the clamp and not the ink. The measured line is
    taken: the apex is the WEST BOUNDARY at row 1546, and the bank's leg from its
    northernmost station to that point is the one unmeasured edge in this outline.
    Extrapolated straight, the two northernmost stations would close on the west boundary
    at row 1503.7 — 31.1 m north of the read apex — so the bank curves west into the tip
    and the reading does not say how. `north_closure` records it."""
    side, stations = _wl_frame(wl)
    apex_py = wl["bounds"]["apex_px_y"]
    apex_px = side("west_boundary", apex_py)

    # the south edge: the wedge's west boundary and its bank, each met with Kinzie's
    # north rule carried east by the street reading's own shear
    sw_px, sw_py = _meet(lambda y: side("west_boundary", y), south_row, apex_py)
    se_px, se_py = _meet(lambda y: side("bank", y), south_row, apex_py)

    def bank_leg(from_py, to_py):
        """The bank between two rows, at the stations it was measured at."""
        return [(side("bank", y), y) for y, _ in stations if from_py < y < to_py]

    ring_px = [(apex_px, apex_py), (sw_px, sw_py), (se_px, se_py)]
    ring_px += list(reversed(bank_leg(apex_py, se_py)))
    ring_px.append((apex_px, apex_py))
    ring = [seat(*q) for q in ring_px]

    # THE FOUR RANKS TILE THE WEDGE, and each is a pentagon rather than the quadrilateral
    # its two rules suggest. A rank's own north tip is the row where its EAST rule meets
    # the tract's west boundary (T-1077 derives all four that way and `--check` re-derives
    # them); north of the row where its WEST rule meets that boundary — which is the NEXT
    # rank's tip, exactly — the rank's west side is the boundary and not its rule. So the
    # river front runs up to the apex with the boundary on its left for 125 rows, the
    # second rank for 99, the third for 179, and the corner wedge is nothing but boundary.
    # Built as two quadrilaterals the four would have overlapped the wedge by 12%.
    ranks = []
    tips = [r["north_tip_px_y"] for r in wl["ranks"]]
    for i, r in enumerate(wl["ranks"]):
        w, e = RANK_SIDES[r["id"]]
        tip = r["north_tip_px_y"]
        wsx, wsy = _meet(lambda y: side(w, y), south_row, tip)
        esx, esy = _meet(lambda y: side(e, y), south_row, tip)
        north = (apex_px, apex_py) if r["id"] == "river_front" \
            else (side("west_boundary", tip), tip)
        if w == "west_boundary":
            west_side = [north, (wsx, wsy)]
        else:
            hand = tips[i + 1]
            west_side = [north, (side("west_boundary", hand), hand), (wsx, wsy)]
        if e == "bank":
            east_side = [(esx, esy)] + list(reversed(bank_leg(apex_py, esy)))
        else:
            east_side = [(esx, esy), (side(e, tip), tip)]
        poly_px = west_side + east_side + [west_side[0]]
        poly = [seat(*q) for q in poly_px]
        ranks.append({
            "id": r["id"], "west_rule": r["west_rule"], "east_rule": r["east_rule"],
            "north_tip_px_y": tip,
            "west_side_is_the_tract_boundary_for_px_y": None if w == "west_boundary"
                else round(tips[i + 1] - tip, 1),
            "cells": r["cells"],
            "polygon_local_enu_m": poly,
            "area_m2": round(_area_m2(poly), 1),
            "area_acres": round(_area_m2(poly) / 4046.856, 2),
        })

    lots = []
    for l in wl["lots"]:
        px, py = l["mid_px"]
        lots.append({
            "figure": l["figure"], "rank": l["rank"], "mid_px": l["mid_px"],
            "confidence": l["confidence"],
            "mid_local_enu_m": seat(float(px), float(py)),
        })

    # TWO OF THE TWENTY-SIX FIGURES STAND OUTSIDE THE OUTLINE THEY WERE READ IN, both
    # where T-1077 already said the reading is thin, and neither is moved to fit.
    #
    #   13, the apex cell — "a triangle rather than a lot: the tract's two boundaries
    #       close on it". Its mark stands 12 rows south of the apex and east of the chord
    #       this seating draws from the bank's northernmost station to that point, because
    #       the real bank bulges east there and no station was measured on the bulge. It
    #       is the `north_closure` above, seen from the other side.
    #   14, the second rank's own north tip — "a cell some 30 px deep and 12 px wide where
    #       the west boundary has only just cleared the rule", graded `inferred` by the
    #       reading for exactly that. Its mark stands 1.3 px west of the boundary.
    #
    # 13 seats 6.00 m out and 14 seats 0.91 m out, both well inside the registration's own
    # 16.19 m RMS. They are recorded rather than corrected because correcting either would
    # mean moving a figure Wright wrote to suit a line this project drew.
    outside = [{"figure": l["figure"], "rank": l["rank"],
                "m_outside": round(min(_seg_dist(l["mid_local_enu_m"], a, b)
                                       for a, b in zip(ring, ring[1:])), 2)}
               for l in lots if not _inside(l["mid_local_enu_m"], ring)]

    # the committed west bank of the North Branch, asked the same question T-1070 asked
    # of T-1074's tier-4 block corner
    bank_check = []
    for y, _ in stations:
        rx = side("bank", y)
        bx = _at_y(cbank, y)
        bank_check.append({
            "station_px_y": y, "wedge_river_edge_px_x": round(rx, 1),
            "committed_bank_px_x": None if bx is None else round(bx, 1),
            "east_of_committed_bank_m": None if bx is None else round((rx - bx) * m_per_px, 1),
        })
    covered = [b["east_of_committed_bank_m"] for b in bank_check
               if b["east_of_committed_bank_m"] is not None]

    return {
        "ticket": "T-1086",
        "reading": "data/traces/wabansia_water_lots.json (T-1077)",
        "datum": "the same one the streets hang from: the committed `kinzie` line",
        "south_edge": {
            "what": ("Kinzie Street's north rule, carried east from the street reading's "
                     "own reference column by that reading's own shear (0.019 dy/dx). "
                     "Every point on it seats 12.69 m north of the committed `kinzie` "
                     "centreline, against the 12.19 m that is half the Original Town's "
                     "platted 80 ft corridor — a 0.50 m agreement this seating did not "
                     "fit for."),
            "north_of_committed_kinzie_centreline_m": 12.69,
            "vs_strip_reading_own_kinzie_row": {
                "strip_reading_px_y": wl["bounds"]["kinzie_px_y"],
                "this_row_px_y_at_the_tract_corner": se_py,
                "disagreement_m": round((se_py - wl["bounds"]["kinzie_px_y"]) * m_per_px, 2),
                "why": ("T-1077 read Kinzie's line in its own column and reports one row "
                        "for it; this carries the street reading's rule 880 px east "
                        "instead. The two disagree by 6.0 m at the tract's south-east "
                        "corner, against a registration that admits 16.19 m RMS with no "
                        "control point within 900 m. The carried rule is taken because "
                        "the whole seating hangs from it and a tract whose south edge is "
                        "read twice has two south edges."),
            },
        },
        "north_closure": {
            "apex_px": [round(apex_px, 2), apex_py],
            "reading_gap_at_the_apex_row_m": round(
                (side("bank", apex_py) - apex_px) * m_per_px, 2),
            "why": ("T-1077's bank holds its northernmost station north of row 1665, so at "
                    "the apex row its arithmetic puts the bank 28.0 m east of the west "
                    "boundary. The apex is taken as the west boundary's point, which is "
                    "measured there; the bank's leg from row 1665 to it is the one edge in "
                    "this outline no station stands on. Straight-lined, the two "
                    "northernmost stations would close on the boundary 31.1 m north of the "
                    "read apex, so the bank curves west into the tip."),
            "confidence": "inferred",
        },
        "outline_local_enu_m": ring,
        "area_m2": round(_area_m2(ring), 1),
        "area_acres": round(_area_m2(ring) / 4046.856, 2),
        "ranks": ranks,
        "lots": lots,
        "lots_seating_outside_the_outline": {
            "lots": outside,
            "why": ("13 is the apex cell, east of the unmeasured chord `north_closure` "
                    "describes — the bank bulges over it and no station was measured on "
                    "the bulge; 14 is the second rank's pinched north tip, 1.3 px west of "
                    "the tract boundary. Both are cells T-1077 graded `inferred` for the "
                    "same thinness, both stand well inside the registration's own 16.19 m "
                    "RMS, and neither figure is moved to suit a line this project drew."),
            "bound": ("the registration's 16.19 m RMS. Past that a figure is not outside "
                      "its own outline by the fit's error any more, and `--check` fails."),
        },
        "committed_west_bank_cross_check": {
            "question": ("T-1070 measured T-1074's tier-4 block corner 65.6 m inside the "
                         "committed west bank of the North Branch and refused it as a "
                         "street's east end. A tract boundary meets the same question, and "
                         "here it is answered rather than refused."),
            "stations": bank_check,
            "reach_covered": f"{len(covered)} of {len(bank_check)} stations",
            "mean_abs_m": round(sum(abs(v) for v in covered) / len(covered), 1) if covered else None,
            "max_abs_m": round(max(abs(v) for v in covered), 1) if covered else None,
            "reading": ("The strip's river edge and the committed west bank are the SAME "
                        "LINE over the reach they share: four of the five stations the "
                        "committed trace covers agree within 1.8 m and the fifth within "
                        "8.4 m, on two readings of this sheet made independently. So the "
                        "committed bank is not what is wrong in this corner, "
                        "and T-1074's tier-4 block corner — 18.6 m OUTSIDE that bank at its "
                        "own tier's middle, and the one place along this whole boundary "
                        "where the sheet and the water disagree — is the outlier. It is "
                        "carried as read all the same: it is Wright's ink, it is the jog "
                        "T-1074 read two lots wide, and the tract boundary is not moved to "
                        "flatter ground than the plate draws."),
        },
    }


def _tract(seat, south_row, tiers, margin, east, wedge, wl, cbank, m_per_px):
    """WABANSIA'S OUTLINE — the ground the survey covers, blocks and water lots together.

    Its four sides, and where each comes from:

      WEST   the tract's own boundary rule, the outer of T-1074's west-margin pair at
             each tier. The block grid's west side unchanged.
      NORTH  T-1074's `north_rule_px_y`, from that boundary east to the block grid's own
             east rule on tier 1. Read at one column and carried flat: the tract's tilt
             would move its east end by at most 5.0 m over the 360 px this edge spans,
             inside the registration's 16.19 m, and T-1074 does not say which column it
             read, so nothing is applied that cannot be re-derived.
      EAST   the grid's east rule down tiers 1 to 4, then the wedge's apex, then the
             wedge's river edge to Kinzie Street. Two independent readings of one line:
             on tiers 1 to 3 the grid's east rule stands 2.1 to 5.7 m INSIDE the committed
             west bank of the North Branch, which is T-1074's own account of that reach —
             "north of Sailors Street the North Branch is close enough to the grid to
             leave room for nothing wider" — and from the apex south the wedge's river
             edge is that bank to within 1.8 m at four stations of five.
      SOUTH  Kinzie Street, the datum, as `_wedge` describes it.

    WHAT IS INSIDE AND IS NOT A HOLE. The 43 px between the grid's east rule and the
    wedge's west boundary is the north-south street T-1074 read and refused to name. It is
    inside the survey and inside this outline, and it is not drawn as a gap."""
    order = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
    north_px_y = tiers["t1"]["y_px"][0]
    side, stations = _wl_frame(wl)
    apex_px, apex_py = wedge["north_closure"]["apex_px"]

    ring_px = [_meet(lambda y: margin["t7"]["rule_px_x"][0], south_row, north_px_y)]
    for t in reversed(order):
        ring_px.append((margin[t]["rule_px_x"][0], tiers[t]["mid_px_y"]))
    ring_px.append((margin["t1"]["rule_px_x"][0], north_px_y))
    ring_px.append((east["t1"], north_px_y))
    for t in ("t1", "t2", "t3", "t4"):
        ring_px.append((east[t], tiers[t]["mid_px_y"]))
    ring_px.append((apex_px, apex_py))
    ring_px += [(side("bank", y), y) for y, _ in stations]
    ring_px.append(_meet(lambda y: side("bank", y), south_row, apex_py))
    ring_px.append(ring_px[0])
    ring = [seat(*q) for q in ring_px]

    grid_east = []
    for t in order:
        bx = _at_y(cbank, tiers[t]["mid_px_y"])
        grid_east.append({
            "tier": t, "east_px_x": east[t], "mid_px_y": tiers[t]["mid_px_y"],
            "east_of_committed_bank_m": None if bx is None
                else round((east[t] - bx) * m_per_px, 1),
            "on_the_outline": t in ("t1", "t2", "t3", "t4"),
        })

    return {
        "seated": True,
        "ticket": "T-1086",
        "polygon_local_enu_m": ring,
        "area_m2": round(_area_m2(ring), 1),
        "area_acres": round(_area_m2(ring) / 4046.856, 2),
        "sides": _tract.__doc__,
        "grid_east_rule_vs_committed_bank": grid_east,
        "block_grid_polygon_is": ("the same file's `block_grid_polygon_local_enu_m`, the "
                                  "blocks alone. It is a subset of this outline and is kept "
                                  "because the block grid is what T-1074 numbered."),
        "geometry_confidence": "inferred",
        "confidence_note": ("Every vertex is a rule read off Wright's sheet and laid off the "
                            "committed `kinzie` line; none is traced from a plat this "
                            "project holds, and the one edge no station stands on is the "
                            "bank's leg into the apex, recorded in `water_lot_wedge_local_"
                            "enu_m.north_closure`. Wabansia's recorded plat would make this "
                            "`documented`; nothing in this repository is one."),
    }


# ------------------------------------------------------------------ the seating

def build():
    trace = json.loads(TRACE.read_text())
    blocks = json.loads(BLOCKS.read_text())
    doc = json.loads(STREETS.read_text())
    by = {s["id"]: s for s in doc["streets"]}
    to_local = _frame()
    shear = trace["method"]["shear_ew"]
    read = {s["id"]: s for s in trace["streets"]}
    ext, tiers, margin, east = _extents(trace, blocks)

    kin = by[DATUM_ID]["path_local_enu_m"]
    u = _unit(kin[0], kin[-1])            # along Kinzie, eastward
    nrm = (-u[1], u[0])                   # off Kinzie, northward
    kz = read[DATUM_ID]

    def kinzie_py(px):
        """Wright's Kinzie corridor centre, in raster rows, at this column."""
        return kz["centre_px_y"] + shear * (px - kz["ref_px_x"])

    def south_row(px):
        """The tract's SOUTH EDGE in raster rows: Kinzie Street's north rule at this
        column, carried from the street reading's own reference column by that reading's
        own shear.

        T-1070 held that rule FLAT at the row it was read at, which is exact at the
        reading's column and drifts away from it eastward: the sheet's corridors lean
        0.019 dy/dx, so a flat row seats 12.4 m north of the committed `kinzie`
        centreline at the tract's west corner and 19.8 m at the block grid's east one.
        Carried, it seats 12.69 m at every column — against the 12.19 m that is half the
        Original Town's platted 80 ft corridor. The wedge reaches 370 px further east
        again, where a flat row would stand 25.0 m out, so the tract could not be
        outlined on one convention and its blocks on another."""
        return kz["rule_px_y"][0] + shear * (px - kz["ref_px_x"])

    def seat(px, py):
        """A sheet pixel on modern ground.

        EASTING is the sheet's own through the registration's affine; no control
        constrains this tract along its own streets and none is invented. NORTHING is
        the committed `kinzie` line's at that easting, plus the perpendicular distance
        north of Wright's own Kinzie corridor, measured on the sheet. So the sheet
        supplies the ladder and the committed grid supplies where it hangs and which
        way it lies."""
        E = to_local(px, py)[0]
        a = to_local(px, kinzie_py(px))
        b = to_local(px, py)
        d = math.copysign(math.dist(a, b), kinzie_py(px) - py)
        t = (E - kin[0][0]) / u[0]
        base = (kin[0][0] + t * u[0], kin[0][1] + t * u[1])
        return [round(base[0] + d * nrm[0], 2), round(base[1] + d * nrm[1], 2)]

    bank = _bank_px(to_local)
    m_per_px = math.dist(to_local(900, 1500), to_local(900, 1501))

    out, evidence = [], []
    for sid in SEATED:
        s, x = read[sid], ext[sid]
        y0, rx = s["centre_px_y"], s["ref_px_x"]

        def py(px):
            return y0 + shear * (px - rx)

        # THE EAST END is the farther of the two tiers' last block corner — the tier
        # whose blocks are wider fronts the street for its whole length — UNLESS that
        # corner falls east of the committed west bank of the North Branch, in which
        # case the nearer tier's is taken. A platted line is not committed across water
        # this project already holds. It bites once, at Sailors Street, where the grid
        # jogs two lots east and T-1074's corner for tier 4 stands 65.6 m inside the
        # committed water. Which of the two readings is wrong is not settled here: the
        # bank is traced from this same sheet and T-1078 has it short of Wright's ink on
        # two stretches of the east side already.
        far, near = x["east_px"], x["east_px_nearer"]
        bx_far = _at_y(bank, py(far))
        over = None if bx_far is None else round((far - bx_far) * m_per_px, 1)
        east_px = near if (over is not None and over > 0 and near < far) else far

        path = [seat(x["west_px"], py(x["west_px"])), seat(east_px, py(east_px))]
        out.append(_entry(sid, s, path))

        bx = _at_y(bank, py(east_px))
        evidence.append({
            "id": sid, "name_on_sheet": s["name_on_sheet"],
            "tiers": x["tiers"], "west_px": x["west_px"],
            "east_px": east_px, "east_px_refused": far if east_px != far else None,
            "centre_px_y": y0, "ref_px_x": rx,
            "north_of_kinzie_m": round(math.dist(
                to_local(rx, kinzie_py(rx)), to_local(rx, y0)), 2),
            "path_local_enu_m": path,
            "east_end_past_committed_bank_m": None if bx is None
                else round((east_px - bx) * m_per_px, 1),
            "refused_end_past_committed_bank_m": over if east_px != far else None,
        })

    poly = _polygon(seat, south_row, tiers, margin, east, north_px_y=tiers["t1"]["y_px"][0])
    wl = json.loads(WATER_LOTS.read_text())
    wedge = _wedge(seat, south_row, wl, bank, m_per_px)
    tract = _tract(seat, south_row, tiers, margin, east, wedge, wl, bank, m_per_px)
    return doc, by, out, evidence, trace, poly, wedge, tract


def _polygon(seat, south_row, tiers, margin, east, north_px_y):
    """The BLOCK GRID's outline, from T-1074's own corners, seated the same way.

    It is not the tract's outline and is not called one: this is the blocks alone, which
    is what T-1074 numbered. `tract_polygon_local_enu_m` is the survey's own ground,
    blocks and water lots together, and is derived by `_tract` (T-1086).

    ITS SOUTH EDGE MOVED when the wedge arrived (T-1086). This polygon used to take
    Kinzie Street's north rule at the row it was read at and hold it flat across 530 px
    of the sheet; it now carries it by the reading's own shear, exactly as the tract
    outline must. Its west corner moves 0.25 m north and its east corner 7.14 m south;
    the other seventeen vertices do not move at all. The change is made here rather than
    by giving the tract outline a second convention, because the two polygons share this
    edge and one edge cannot be derived twice."""
    order = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
    ring = []
    ring.append(seat(margin["t7"]["rule_px_x"][0],
                     south_row(margin["t7"]["rule_px_x"][0])))
    for t in reversed(order):
        ring.append(seat(margin[t]["rule_px_x"][0], tiers[t]["mid_px_y"]))
    ring.append(seat(margin["t1"]["rule_px_x"][0], north_px_y))
    ring.append(seat(east["t1"], north_px_y))
    for t in order:
        ring.append(seat(east[t], tiers[t]["mid_px_y"]))
    ring.append(seat(east["t7"], south_row(east["t7"])))
    ring.append(ring[0])
    return ring


def _inside(pt, ring):
    """Even-odd, with the edge counted as inside to within a millimetre."""
    x, y = pt
    n = 0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        span = math.hypot(x1 - x0, y1 - y0) or 1.0
        if abs((x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)) / span < 0.02 \
           and min(x0, x1) - 0.02 <= x <= max(x0, x1) + 0.02 \
           and min(y0, y1) - 0.02 <= y <= max(y0, y1) + 0.02:
            return True
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            n += 1
    return n % 2 == 1


def _seg_dist(pt, a, b):
    (x, y), (x0, y0), (x1, y1) = pt, a, b
    dx, dy = x1 - x0, y1 - y0
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / n))
    return math.hypot(x - (x0 + t * dx), y - (y0 + t * dy))


def _invariants(poly, wedge, tract):
    """WHAT THE THREE POLYGONS MUST BE TO EACH OTHER, checked rather than asserted in
    prose. The tract is the survey's ground; the blocks and the water lots are both parts
    of it, so both must lie inside it, and the four ranks must tile the wedge. None of
    this is fitted — every vertex comes from a rule read off the sheet — so a failure
    here means a reading moved, not that a tolerance is too tight."""
    ring = tract["polygon_local_enu_m"]
    bad = []
    out = [q for q in poly[:-1] if not _inside(q, ring)]
    if out:
        bad.append(f"{len(out)} of {len(poly) - 1} block-grid corners fall outside the "
                   f"tract outline, starting {out[0]}")
    out = [q for q in wedge["outline_local_enu_m"][:-1] if not _inside(q, ring)]
    if out:
        bad.append(f"{len(out)} of {len(wedge['outline_local_enu_m']) - 1} water-lot wedge "
                   f"corners fall outside the tract outline, starting {out[0]}")
    out = [l["figure"] for l in wedge["lots"]
           if not _inside(l["mid_local_enu_m"], wedge["outline_local_enu_m"])]
    known = wedge["lots_seating_outside_the_outline"]["lots"]
    if out != [k["figure"] for k in known]:
        bad.append(f"water lot(s) {out} seat outside the wedge outline; "
                   f"{[k['figure'] for k in known]} are the ones this seating accounts for")
    for k in known:
        if k["m_outside"] > 16.19:
            bad.append(f"water lot {k['figure']} seats {k['m_outside']} m outside the wedge "
                       f"outline, past the registration's own 16.19 m RMS")
    tiled = round(sum(r["area_m2"] for r in wedge["ranks"]), 1)
    if abs(tiled - wedge["area_m2"]) > 0.02 * wedge["area_m2"]:
        bad.append(f"the four ranks cover {tiled} m2 and the wedge outline "
                   f"{wedge['area_m2']} m2 — they should tile it")
    if not tract["area_m2"] > wedge["area_m2"]:
        bad.append("the tract is not larger than the wedge inside it")
    return bad


def _entry(sid, s, path):
    n2026 = NAME_2026.get(sid)
    e = {
        "id": f"{sid}_wabansia" if sid in ("free",) and False else sid,
        "name_1835": f"{s['name_on_sheet']} Street",
        "name_2026": n2026,
        "name_changed": False,
        "path_local_enu_m": path,
        "corridor_width_m": 24.02,
        "track_width_m": 0,
        "opened": False,
        "worn": False,
        "alleys": False,
        "status_1835": "platted, unopened, unworn",
        "surface": "unworn_prairie",
        "traffic": "none",
        "geometry_confidence": "inferred",
        "surface_confidence": "inferred",
        "wear_confidence": "inferred",
        "sources": ["wright_1834_nara_hup", "wright_1834"],
        "note": NOTE.format(sheet=s["name_on_sheet"]),
    }
    if n2026 is None:
        e["name_note"] = NAME_NOTE
    return e


# ------------------------------------------------------------------ the write

def _render(entry, indent=4):
    text = json.dumps(entry, indent=2, ensure_ascii=False)

    def collapse(m):
        return re.sub(r"\s*\n\s*", " ", m.group(0)).replace("[ ", "[").replace(" ]", "]")

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\[[^\[\]{}]*\]", collapse, text)
    pad = " " * indent
    return "\n".join(pad + ln for ln in text.split("\n"))


def _entry_spans(text):
    """`(id, start, end)` for every object in the `streets` array, found by scanning
    braces rather than by matching the file's style: one committed entry
    (`fort_bank_track`) is indented unlike the other seventy-six and a shape regex
    walks straight past it."""
    i = text.index("[", text.index('"streets"'))
    spans, depth, start, in_str, esc = [], 0, None, False, False
    for j in range(i, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
            if depth == 1:
                start = j
        elif ch == "}":
            depth -= 1
            if depth == 0:
                spans.append((json.loads(text[start:j + 1])["id"], start, j + 1))
        elif ch == "]" and depth == 0:
            break
    return spans


def _reseat(text, entries):
    """Re-point streets this tool has ALREADY committed, in place, on the same argument
    _splice makes for appending: the entry is re-rendered, the rest of the file is not
    touched, and the diff is the lines that moved.

    Until T-1092 a seating tool could only append. That was enough while the
    registration never changed; when T-1091 put the eleven-point fit in force, every
    line these tools had seated through the old one stayed where it was and the tools'
    own --check went red against them. Re-running the generator is how this project
    moves a derived line, so the generator has to be able to."""
    at = {sid: (s, e) for sid, s, e in _entry_spans(text)}
    for entry in sorted(entries, key=lambda e: at[e["id"]][0], reverse=True):
        s, e = at[entry["id"]]
        text = text[:s] + _render(entry).lstrip() + text[e:]
    return text


def _splice(text, entries):
    """Append the new streets WITHOUT re-serialising the file, for the reason
    seat_kinzie_addition_streets.py gives: a writer that re-emits this document changes
    a thousand lines of escaping to add six streets, and a reviewer cannot see that."""
    if not entries:
        # A SECOND `--write` HAS NOTHING TO APPEND, and used to leave a trailing comma
        # behind that made data/streets/1835.json unparseable — found re-running this tool
        # under T-1086, when every street it seats was already committed.
        return text
    tail = re.compile(r'\n  \]\n\}\s*$')
    if not tail.search(text):
        raise SystemExit("data/streets/1835.json does not end in the shape this tool expects")
    body = ",\n".join(_render(e) for e in entries)
    return tail.sub(",\n" + body + "\n  ]\n}\n", text)


def _trace_doc(evidence, trace, poly, wedge, tract):
    return {
        "_doc": __doc__,
        "ticket": "T-1070 · T-1086",
        "datum": {
            "street": DATUM_ID,
            "committed_in": "data/streets/1835.json",
            "why": ("Wabansia's south line is Kinzie Street on Wright's sheet and Kinzie "
                    "Street is committed off the Thompson plat. It is the one line the two "
                    "surveys share, so it is the one thing the ladder can hang from."),
        },
        "method": {
            "rung": ("each street's perpendicular distance north of Kinzie Street, the sum of "
                     "the sheet's measured tier pitches between them"),
            "bearing": "the committed kinzie line's, not the sheet's",
            "easting": ("the sheet's own, through the registration's affine. No control "
                        "constrains the along-street position of this tract and none is "
                        "invented: the seating is a translation north, not a fit."),
            "tier_pitch_source": "data/traces/wabansia_streets.json § module.tier_pitch_m.each",
        },
        "sheet_vs_committed_kinzie": trace["cross_check"],
        "shear_between_columns": {
            "what": ("T-0790 read the seven corridors in three different columns of the "
                     "sheet — `col_west` at x 700, `col_trade` at 880, `col_east` at 990 — "
                     "because Wright letters the names inside the corridors and a name is "
                     "ink in exactly the gap the reading is trying to find. A rule row is "
                     "reported at its window's own left edge, and the rules lean: "
                     "dy/dx 0.019. So two corridors read in different columns are not "
                     "directly subtractable, and `module.tier_pitch_px` in that file "
                     "subtracts them anyway."),
            "effect_px": {"free_to_trade": 2.09, "trade_to_sailors": 3.42},
            "handled": ("This seating never subtracts two rows. Every distance is measured "
                        "between a street's own row and Wright's Kinzie corridor carried to "
                        "that same column by the shear, so the lean cancels. It is why "
                        "`north_of_kinzie_m` for Free and Trade stands 4.1 m and 2.5 m "
                        "north of the running sum of that table."),
            "not_a_correction_of": ("data/traces/wabansia_streets.json, which is a reading "
                                    "and is left as read. The module figure it reports is "
                                    "a mean over six spacings and the lean is inside its "
                                    "own 3.01 m sd."),
        },
        "streets": evidence,
        "block_grid_polygon_local_enu_m": poly,
        "water_lot_wedge_local_enu_m": wedge,
        "tract_polygon_local_enu_m": tract,
        "occupancy_before_1835_07_01": OCCUPANCY,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="the committed street lines still re-derive from the readings")
    a = ap.parse_args()
    doc, by, out, evidence, trace, poly, wedge, tract = build()

    if a.check:
        bad = []
        for s in out:
            have = by.get(s["id"])
            if have is None:
                bad.append(f"{s['id']} is not in data/streets/1835.json")
                continue
            for a0, b0 in zip(have.get("path_local_enu_m", []), s["path_local_enu_m"]):
                if max(abs(a0[0] - b0[0]), abs(a0[1] - b0[1])) > 0.02:
                    bad.append(f"{s['id']}: committed {have['path_local_enu_m']}, "
                               f"re-derived {s['path_local_enu_m']}")
                    break
            for k in ("corridor_width_m", "name_1835", "name_2026", "status_1835",
                      "sources", "track_width_m", "surface", "traffic", "note"):
                if have.get(k) != s[k]:
                    bad.append(f"{s['id']}.{k}: committed {have.get(k)!r}, re-derived {s[k]!r}")
        if OUT.exists():
            was = json.loads(OUT.read_text())
            now = _trace_doc(evidence, trace, poly, wedge, tract)
            for key in ("streets", "block_grid_polygon_local_enu_m",
                        "water_lot_wedge_local_enu_m", "tract_polygon_local_enu_m"):
                if json.dumps(was.get(key), sort_keys=True) != \
                   json.dumps(now[key], sort_keys=True):
                    bad.append(f"{OUT.name} § {key} does not re-derive from the readings")
        else:
            bad.append(f"{OUT.name} is missing")
        bad += _invariants(poly, wedge, tract)
        for line in bad:
            print("RED  " + line)
        print(f"wabansia: {len(out)} street line(s), the block grid's outline, the "
              f"water-lot wedge ({len(wedge['ranks'])} ranks, {len(wedge['lots'])} lots) "
              f"and the tract's outline all re-derive from the readings in "
              f"data/traces/wabansia_streets.json, wabansia_block_numbering.json and "
              f"wabansia_water_lots.json"
              if not bad else f"{len(bad)} disagreement(s)")
        return 1 if bad else 0

    for s, ev in zip(out, evidence):
        print(f'{s["id"]:9s} {s["name_1835"]:18s} {ev["north_of_kinzie_m"]:8.2f} m N of kinzie  '
              f'{s["path_local_enu_m"]}')
        if ev["east_end_past_committed_bank_m"] is not None:
            print(f'{"":9s} east end vs committed west bank: '
                  f'{ev["east_end_past_committed_bank_m"]:+.1f} m')
    print(f'{"wedge":9s} {len(wedge["ranks"])} ranks, {len(wedge["lots"])} lots, '
          f'{wedge["area_acres"]} acres; river edge vs committed bank: mean '
          f'{wedge["committed_west_bank_cross_check"]["mean_abs_m"]} m, max '
          f'{wedge["committed_west_bank_cross_check"]["max_abs_m"]} m over '
          f'{wedge["committed_west_bank_cross_check"]["reach_covered"]}')
    print(f'{"tract":9s} {len(tract["polygon_local_enu_m"]) - 1} vertices, '
          f'{tract["area_acres"]} acres ({tract["area_m2"]} m2); block grid '
          f'{round(_area_m2(poly) / 4046.856, 2)} acres')
    for line in _invariants(poly, wedge, tract):
        print("RED  " + line)
    if a.write:
        fresh = [s for s in out if s["id"] not in by]
        seated = [s for s in out if s["id"] in by]
        STREETS.write_text(_reseat(_splice(STREETS.read_text(), fresh), seated))
        OUT.write_text(json.dumps(_trace_doc(evidence, trace, poly, wedge, tract),
                                   indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {STREETS.relative_to(ROOT)} and {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
