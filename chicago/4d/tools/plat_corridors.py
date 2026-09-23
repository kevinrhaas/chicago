#!/usr/bin/env python3
"""The platted street corridors, as one question asked in one place.

ROADMAP K7 phase two (a). The grid report found buildings standing in the road; the
generator that put them there had never asked. Both sides now read this module, so the
gate and the report cannot answer differently — which is the same reason
`generators/mesh_inputs.py` exists for the staleness hash.

What a corridor IS here: a committed street centreline from `data/streets/1835.json`,
offset both ways by half the platted module in `data/traces/street_control.json`. It is
therefore only as long as the centreline this project has drawn, and a building beyond a
street's drawn end is not in it. The geometry is `generate_plat_lots.corridor_rings` —
imported rather than copied.

What a corridor IS NOT: the travelled way. L79 records that the visible tracks run
5.8-10.5 m inside an 80 ft legal corridor, so a building inside the corridor is not
necessarily a building in anybody's way. That is exactly why this module reports a DEPTH
and lets each caller set its own bar: an invented placement has no business in the
roadway at all, while an attested frontage that lands a few metres inside it is a
measurement about the georeference and about the plat, not a defect in the record.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from generate_plat_lots import (  # noqa: E402
    DATA, EW_STREETS, NS_STREETS, corridor_rings, load, point_in_polygon,
    point_to_ring_m, street_lines,
)

# Footprint edges are sampled at this pitch before the point test. A corridor is 24 m
# wide and no footprint in this dataset is, so a building cannot straddle one without
# putting a sample inside it; the sampling is there for the corner cases at a corridor's
# drawn END, where the ring turns.
SAMPLE_M = 0.5

# The centimetre this project quotes a corridor depth to. It is not a tolerance anybody
# chose for THIS question: `measure_corridor_intrusion` already refuses to report a depth
# finer than 0.01 m because the ring and the footprint are both derived and the last
# millimetre is arithmetic rather than evidence. The same figure decides here whether a
# control point and the drawn line DISAGREE at all — a street whose line reproduces its
# control to under a centimetre is a street drawn on its control, and re-centring it would
# move the whole town by arithmetic noise.
QUOTED_M = 0.01


def _cross_axis_of_line(points: list, along: float, axis: str) -> float | None:
    """The drawn centreline's cross-axis value where it passes the given along-axis value.

    `axis` is the street's own axis: an east-west street is read for a NORTHING at an
    easting, a north-south street for an EASTING at a northing. Returns None when the
    control point lies outside the span this project has actually drawn — a street's
    corridor is only as long as its committed centreline, so a control point beyond the
    drawn end says nothing about the part of it that exists.
    """
    i, j = (0, 1) if axis == "ew" else (1, 0)
    for a, b in zip(points, points[1:]):
        lo, hi = min(a[i], b[i]), max(a[i], b[i])
        if lo - 1e-9 <= along <= hi + 1e-9:
            t = 0.0 if b[i] == a[i] else (along - a[i]) / (b[i] - a[i])
            return a[j] + (b[j] - a[j]) * t
    return None


def control_offsets(lines: dict | None = None, control: dict | None = None) -> dict:
    """How far each street's committed CONTROL stands off its own drawn centreline.

    T-0009, and the owner's ruling of 2026-08-29 that produced it: *"derive the platted
    corridor from the street CONTROL rather than from the drawn line."*

    A drawn centreline in `data/streets/1835.json` is a reconstruction decision about where
    a street can be DRAWN — south_water's own record says its line east of Franklin "is
    shifted into the dry half of the platted riverfront corridor", 8.28 m perpendicular off
    `control.south_water_franklin`. That shift is not a claim about where the platted
    corridor was, so measuring building bodies against the drawn line reported them
    intruding into a corridor the plat does not put there.

    So the corridor is centred on the control where a street HAS committed control. Per
    street this returns every control point naming it, the cross-axis offset from the drawn
    line to that point, and the verdict:

    * `centred`   — the line reproduces its control to under `QUOTED_M`. Nothing moves.
    * `recentred` — one agreed offset, larger than `QUOTED_M`. The corridor is translated
                    onto the control by it; the drawn line does NOT move.
    * `disagree`  — two or more control points that do not agree on one offset. A rigid
                    translation cannot satisfy them and re-DRAWING the line is exactly what
                    the ruling forbids, so the corridor stays on the drawn line and the
                    spread is recorded rather than averaged away.
    * `off_line`  — the control point lies beyond the drawn centreline's own span.
    * `refused`   — every control point naming the street carries
                    `not_corridor_control_for` naming it, which is the control table's own way of
                    saying that the junction is not evidence of where the PLATTED corridor
                    ran. T-0827 wrote the first one: `lake_market` is West Lake Street
                    crossing North Upper Wacker Drive, and Wacker Drive stands on ground
                    made in 1926 when the river was walled, so re-centring Market's
                    platted corridor onto it is the very error that ticket measured. The
                    refusal lives in the DATA and carries its reason there; nothing here
                    knows a street id, which is the principle below unchanged.

    The verdict is computed from the committed control and the committed lines every time.
    There is no list of street ids anywhere in it: a street acquires or loses a re-centring
    by what its control says, which is the whole point of deriving it.
    """
    control = load(DATA / "traces" / "street_control.json") if control is None else control
    lines = street_lines(load(DATA / "streets" / "1835.json")) if lines is None else lines
    datum = load(DATA / "datum.json")
    origin_e, origin_n = float(datum["origin_utm_e"]), float(datum["origin_utm_n"])

    found: dict = {sid: [] for sid in lines}
    refused: dict = {sid: [] for sid in lines}
    for point_id, point in sorted(control["control"].items()):
        local_e = float(point["utm_e"]) - origin_e
        local_n = float(point["utm_n"]) - origin_n
        for sid in point["streets"]:
            if sid not in lines:
                continue
            # A junction can be good control for one of its two streets and not for the
            # other, and Lake x Market is the case that proved it: the northing is Lake
            # Street, which still runs where it ran, and the easting is Wacker Drive,
            # which does not. So the refusal is per STREET, not per point.
            if sid in (point.get("not_corridor_control_for") or []):
                refused[sid].append(point_id)
                continue
            if sid in EW_STREETS:
                axis, along, control_cross = "ew", local_e, local_n
            elif sid in NS_STREETS:
                axis, along, control_cross = "ns", local_n, local_e
            else:
                continue
            drawn = _cross_axis_of_line(lines[sid]["points"], along, axis)
            found[sid].append({
                "control": point_id,
                "axis": axis,
                "drawn_cross_m": None if drawn is None else round(drawn, 2),
                "offset_m": None if drawn is None else round(control_cross - drawn, 2),
            })

    out = {}
    for sid, points in found.items():
        usable = [p for p in points if p["offset_m"] is not None]
        if not points:
            verdict, offset = ("refused" if refused[sid] else "no_control"), 0.0
        elif not usable:
            verdict, offset = "off_line", 0.0
        else:
            offsets = [p["offset_m"] for p in usable]
            spread = max(offsets) - min(offsets)
            if spread > QUOTED_M:
                verdict, offset = "disagree", 0.0
            elif abs(offsets[0]) <= QUOTED_M:
                verdict, offset = "centred", 0.0
            else:
                verdict, offset = "recentred", round(sum(offsets) / len(offsets), 2)
        out[sid] = {
            "axis": "ew" if sid in EW_STREETS else "ns" if sid in NS_STREETS else None,
            "points": points,
            "spread_m": (round(max(p["offset_m"] for p in points if p["offset_m"] is not None)
                               - min(p["offset_m"] for p in points
                                     if p["offset_m"] is not None), 2)
                         if usable else None),
            "verdict": verdict,
            "refused_as_corridor_control": refused[sid],
            "offset_m": offset,
        }
    return out


def corridors(from_control: bool = False) -> dict:
    """Every grid street's platted corridor, by street id.

    `from_control=True` centres the corridor on the street's committed CONTROL wherever it
    has one the drawn line does not reproduce — see `control_offsets`, and T-0009 for the
    owner's ruling of 2026-08-29 that asked for it.

    **IT IS NOT THE DEFAULT, AND THAT IS THE RULING'S OWN SCOPE.** The ruling says in as
    many words what it changes: *"what changes is what the intrusion TABLE measures
    against"* — whether a body a person placed stands in the platted roadway. It did not
    decide the other question this module is asked, which is where a GENERATOR may put a
    roof, and that one is about the street as DRAWN: a visitor walks the committed
    centreline, not the plat.

    The split is not a convenience. Re-centring south_water town-wide was measured on
    2026-08-29 (T-0009) and moves the corridor 8.58 m off its own block faces, which are
    offset from the drawn line by `generate_plat_lots.block_edges` and do not move. Five
    gates that read a corridor edge AGAINST a block face or a frontage line then disagree
    with the plat — the cross-street face census, the southern-ground stations, the
    block-parcel street-line assertions and the far-timber census all went red. That strip
    between the re-centred corridor and the block face it no longer abuts is a real
    question about the plat, and it is filed rather than settled here.
    """
    control = load(DATA / "traces" / "street_control.json")
    half_width = float(control["platted_street"]["half_width_m"])
    lines = street_lines(load(DATA / "streets" / "1835.json"))
    offsets = (control_offsets(lines, control) if from_control
               else {sid: {"offset_m": 0.0, "verdict": "drawn"} for sid in lines})
    out = {}
    for sid, ring in corridor_rings(lines, half_width).items():
        shift = float(offsets.get(sid, {}).get("offset_m") or 0.0)
        i = 1 if sid in EW_STREETS else 0
        if shift:
            ring = [(e, n + shift) if i else (e + shift, n) for e, n in ring]
        drawn = lines[sid]["points"]
        centre = ([(e, n + shift) if i else (e + shift, n) for e, n in drawn]
                  if shift else drawn)
        out[sid] = {
            "name": lines[sid]["name"],
            "ring": ring,
            # `points` is the line as DRAWN and stays the drawn line: callers that ask
            # where the street is drawn are asking about data/streets/1835.json, which
            # this derivation does not move. `centre` is the corridor's own centre, which
            # is what a question about the PLAT should be asked against.
            "points": drawn,
            "centre": centre,
            "control_offset_m": shift,
            "control_verdict": offsets.get(sid, {}).get("verdict", "no_control"),
        }
    return out


def sampled(polygon: list, pitch: float = SAMPLE_M) -> list:
    """A polygon's vertices plus points along its edges."""
    points = []
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        steps = max(1, int(math.dist(a, b) / pitch))
        points += [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
                   for k in range(steps)]
    return points


def intrusion(polygon: list, lanes: dict | None = None) -> tuple[str | None, float]:
    """The deepest a footprint reaches into any platted corridor.

    Returns the street id and the depth in metres, or `(None, 0.0)` if the footprint is
    clear of every corridor. Depth is measured from the corridor's own edge, so it is how
    far into the roadway the building's worst corner stands — not a distance to the
    centreline.
    """
    lanes = corridors() if lanes is None else lanes
    worst_id, worst = None, 0.0
    points = sampled(polygon)
    for street_id, lane in lanes.items():
        ring = lane["ring"]
        for point in points:
            if point_in_polygon(point, ring):
                depth = point_to_ring_m(point, ring)
                if depth > worst:
                    worst_id, worst = street_id, depth
    return worst_id, worst
