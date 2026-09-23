#!/usr/bin/env python3
"""How much of this town is drawn standing in its own streets.

ROADMAP K30(a). Every generator in this project asks `plat_corridors.intrusion()` before
it puts a roof anywhere, so no invented building has ever been allowed into a roadway.
Nothing had ever asked the question of the records a PERSON placed. T-A9 measured three of
them by hand, T-A12 added two more, and the entry asked for the distribution rather than
the anecdotes: *"a handful of deep intrusions on one street is a different problem from a
uniform half-metre bias across the grid, and the fix differs accordingly."*

This is the distribution, as a command.

**Two tests, reported separately, because they answer different questions.**

* **lap** — any point of the footprint is inside a platted corridor. This is the drawn
  fault: it is what a visitor standing in the street can see.
* **centroid** — the footprint's centroid is inside one. This is `T-A7`'s test, the one
  that decides whether the lot schedule can see the building at all, and it is a strict
  subset of the lap set.

**A corridor is not the DRAWN LINE either, since T-0009.** The owner ruled on 2026-08-29
that the platted corridor is derived from the street CONTROL rather than from the committed
centreline, because a centreline is a decision about where a street can be DRAWN — South
Water's is offset 8.58 m into the dry half of its own corridor, and measuring bodies against
it reported an intrusion into a corridor the plat does not put there. `--control` prints the
derivation, one line per street; `--drawn` re-runs every mode against the old corridor.

**A corridor is not the travelled way.** `plat_corridors` says so at length and it governs
here too: L79 records the visible tracks running 5.8-10.5 m inside an 80 ft legal corridor,
so a building 1 m inside a corridor edge is a measurement about the plat and the
georeference, not a building in anybody's way. That is why this tool reports a DEPTH and a
distribution and refuses to name a threshold. **The 2-3.5 m gap in the depths is the one
piece of structure in the data**, and it is reported rather than legislated.

**What it must never do is move a building to make its number smaller.** A position with a
source outranks a corridor this project derived from a module and a traced centreline.

    tools/measure_corridor_intrusion.py                the full table
    tools/measure_corridor_intrusion.py --by-street    the distribution only
    tools/measure_corridor_intrusion.py --recentre     K30(a)'s refuted counterfactual
    tools/measure_corridor_intrusion.py --reflect      K30(b)'s cause, REFUTED by --anchors
    tools/measure_corridor_intrusion.py --anchors      K30(d): is the point the kerb or the back
    tools/measure_corridor_intrusion.py --escape       T-0195: which way OUT, and what it costs
    tools/measure_corridor_intrusion.py --control      T-0009: where each corridor is centred
    tools/measure_corridor_intrusion.py --drawn        T-0009: against the pre-ruling line
    tools/measure_corridor_intrusion.py --gate         the ratchet check.sh runs
    tools/measure_corridor_intrusion.py --self-test    break the absolute assertion
    tools/measure_corridor_intrusion.py --write-baseline   only to record a repair

This tool exists in the shape it does because of what K30(a) found about T-A7 and T-A14
found about T-A13: a number derived by hand and thrown away does not reproduce, not even at
the commit that states it. Every figure any parcel quotes about corridor intrusion should
come out of here.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as _dt
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from generate_plat_lots import point_in_polygon, point_to_ring_m  # noqa: E402
from measure_street_frontage import (  # noqa: E402
    LAYERS, layer_of, layer_of_record)
from plat_occupancy import layers, researched_ids  # noqa: E402
from plat_corridors import (  # noqa: E402
    control_offsets, corridors, intrusion, sampled)
from plat_occupancy import world_polygon  # noqa: E402

# WHICH CORRIDOR THIS WHOLE TOOL MEASURES AGAINST — T-0009, and the owner's ruling of
# 2026-08-29 that the platted corridor is derived from the street CONTROL and not from the
# drawn line. `--drawn` puts every mode back on the drawn line, so the before-and-after
# this ticket owes is a command anyone can re-run rather than a checkout of an old commit.
FROM_CONTROL = True


def active_corridors() -> dict:
    """The corridors every mode below measures against, control-derived unless --drawn.

    This tool is the one caller that asks `plat_corridors.corridors()` for the
    control-derived rings; every generator keeps asking the drawn ones, which is the scope
    the ruling itself set. `plat_corridors.corridors` states why at length.
    """
    return corridors(from_control=FROM_CONTROL)


BASELINE = ROOT / "tools" / "corridor_intrusion_baseline.json"
STRUCTURES = ROOT / "data" / "structures"

# A depth is quoted and compared to the centimetre. The corridor ring and the footprint
# are both derived, so the last millimetre is arithmetic rather than evidence, and a
# ratchet that fires on floating-point noise is a ratchet that gets switched off.
PLACES = 2
# The ratchet's tolerance. A depth that grows by less than this is not a new fault; a
# depth that grows by more is a building that moved, or a corridor that did.
TOLERANCE_M = 0.01

# STREET FURNITURE — ROADMAP K30(b) item 2. A bridge standing in a street corridor is the
# bridge doing its job, and counting it as a building in the road is a category error. So
# it is CATEGORISED, not deleted: the row stays in the table, stays in the baseline, and
# stays ratcheted so its depth cannot silently grow — it is simply not counted among the
# buildings drawn standing in their own streets.
#
# The rule is derived from the record's own archetype and function and NEVER from a list
# of ids, which is the whole point: an id list is an allowance that any later parcel can
# quietly extend to silence a defect, and this project has been bitten by hand-maintained
# numbers twice already (K30(a) finding 3, T-A14 on T-A13). To be furniture a record must
# be BOTH a carrying-way archetype AND a crossing function. A store cannot become furniture
# by being renamed, and a bridge cannot stop being one by being moved.
FURNITURE_ARCHETYPES = frozenset({"bridge_timber"})
FURNITURE_FUNCTIONS = frozenset({"street_crossing", "river_crossing"})

# The floor of K30(a)'s DEEP mode. The depths are bimodal with a clean empty gap between
# 1.98 m and 3.48 m, and that gap is a measurement rather than a threshold anybody chose —
# which is why this constant is the observed edge of the upper mode and not a round number.
DEEP_MODE_M = 3.48

# Half the platted street module, read from the same committed control the placements were
# derived from rather than restated here — `data/traces/street_control.json` exists because
# this figure used to live in five paragraphs of prose and nothing checked it.
HALF_WIDTH_M = float(json.loads(
    (ROOT / "data" / "traces" / "street_control.json").read_text(encoding="utf-8")
)["platted_street"]["half_width_m"])


def is_street_furniture(record: dict) -> bool:
    """Does this record exist to CARRY a way rather than to stand beside one?"""
    archetype = record.get("archetype")
    function = (record.get("function") or {}).get("value")
    return archetype in FURNITURE_ARCHETYPES and function in FURNITURE_FUNCTIONS


def placed_phases() -> list[tuple[str, str, dict, list[tuple[float, float]], str]]:
    """(structure_id, phase_id, phase, world polygon, category) per committed placed phase.

    `category` is `furniture` for a record that exists to carry a way and `building` for
    everything else — see `is_street_furniture`.
    """
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        category = "furniture" if is_street_furniture(record) else "building"
        for phase in record.get("phases") or []:
            position = phase.get("position") or {}
            polygon = (phase.get("footprint") or {}).get("polygon") or []
            if position.get("utm_e") is None or len(polygon) < 3:
                continue
            out.append((record["id"], phase["id"], phase,
                        world_polygon(phase, datum), category))
    return out


def centreline_frame(points: list, px: float, py: float) -> tuple[float, tuple, tuple]:
    """Distance to a centreline, the unit direction of its nearest segment, and the foot.

    The frame every cross-street question in this module is asked in. A street is a
    polyline, so "across the street" is only defined against the segment nearest the point
    — which is why this returns the segment's direction rather than assuming the grid's.
    """
    best = (float("inf"), (1.0, 0.0), (px, py))
    for i in range(len(points) - 1):
        ax, ay = points[i]
        bx, by = points[i + 1]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (length * length)))
        qx, qy = ax + t * dx, ay + t * dy
        distance = math.hypot(px - qx, py - qy)
        if distance < best[0]:
            best = (distance, (dx / length, dy / length), (qx, qy))
    return best


def measure(placed: list | None = None) -> dict:
    """Every committed structure's deepest lap into any platted corridor.

    `placed` defaults to the committed tree's placed phases and is a parameter so
    `--self-test` can measure a tree broken in memory — a roof actually moved into a
    roadway, with its depth computed by this same function rather than typed in
    (T-0221).
    """
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    lanes = active_corridors()
    origin_e = float(datum["origin_utm_e"])
    origin_n = float(datum["origin_utm_n"])

    rows: dict[str, dict] = {}
    placed = placed_phases() if placed is None else placed
    for structure_id, phase_id, phase, polygon, category in placed:
        street, depth = intrusion(polygon, lanes)
        if street is None:
            continue
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        position = phase["position"]
        anchor = (float(position["utm_e"]) - origin_e, float(position["utm_n"]) - origin_n)
        # Which corridors each point is in. A point at an intersection is in two, so both
        # are recorded rather than the first one a dict iteration happened to reach —
        # that ambiguity is why T-A7's four named cases have been quoted against two
        # different street names in two different write-ups.
        centroid_in = sorted(s for s, lane in lanes.items()
                             if point_in_polygon((cx, cy), lane["ring"]))
        anchor_in = sorted(s for s, lane in lanes.items()
                           if point_in_polygon(anchor, lane["ring"]))
        # How far the record's own POINT stands from the centreline of the street it laps,
        # and which side of it the body was drawn on. K30(b): for a frontage placement
        # that offset should be the platted half-width, and the body should be on the far
        # side of the point from the street. Where it is not, the drawing crosses the
        # frontage the derivation established, and that is the deep cluster's cause.
        _, axis, foot = centreline_frame(lanes[street]["centre"], *anchor)
        normal = (-axis[1], axis[0])
        anchor_side = ((anchor[0] - foot[0]) * normal[0]
                       + (anchor[1] - foot[1]) * normal[1])
        body_side = ((cx - anchor[0]) * normal[0] + (cy - anchor[1]) * normal[1])
        key = f"{structure_id}:{phase_id}"
        rows[key] = {
            "structure": structure_id,
            "phase": phase_id,
            "layer": layer_of(structure_id),
            "category": category,
            "street": street,
            "depth_m": round(depth, PLACES),
            "centroid_in": centroid_in,
            "anchor_in": anchor_in,
            "anchor_offset_m": round(abs(anchor_side), PLACES),
            "body_toward_street": bool(anchor_side * body_side < 0),
            "position_confidence": position.get("confidence"),
        }
    return {
        "placed_phases": len(placed),
        "corridors": len(lanes),
        "lapping": rows,
    }


def _fmt_table(result: dict) -> str:
    rows = sorted(result["lapping"].values(), key=lambda r: -r["depth_m"])
    lines = [f"{'structure':<44}{'street':<14}{'depth m':>8}  {'centroid':<9}"
             f"{'crosses':<9}{'layer'}"]
    for r in rows:
        centroid = "IN" if r["centroid_in"] else "clear"
        note = "FURNITURE" if r["category"] == "furniture" else (
            "frontage" if r["body_toward_street"] else "")
        lines.append(f"{r['structure']:<44}{r['street']:<14}{r['depth_m']:>8.2f}  "
                     f"{centroid:<9}{note:<9}{r['layer']}")
    return "\n".join(lines)


def _distribution(result: dict) -> str:
    rows = list(result["lapping"].values())
    by_street: dict[str, list[float]] = {}
    by_layer: dict[str, int] = {}
    for r in rows:
        by_street.setdefault(r["street"], []).append(r["depth_m"])
        by_layer[r["layer"]] = by_layer.get(r["layer"], 0) + 1
    lines = ["", "by street (deepest lap):"]
    for street, depths in sorted(by_street.items(), key=lambda kv: -max(kv[1])):
        lines.append(f"   {street:<14}{len(depths):>3} record(s)   "
                     f"deepest {max(depths):>6.2f} m   shallowest {min(depths):>5.2f} m")
    lines.append("")
    lines.append("by evidence layer:")
    for layer in ("research", "inferred_household", "reconstruction"):
        lines.append(f"   {layer:<22}{by_layer.get(layer, 0):>3}")
    centroid = sum(1 for r in rows if r["centroid_in"])
    anchor = sum(1 for r in rows if r["anchor_in"])
    furniture = [r for r in rows if r["category"] == "furniture"]
    buildings = [r for r in rows if r["category"] != "furniture"]
    deep = [r for r in buildings if r["depth_m"] >= DEEP_MODE_M]
    crossing = [r for r in deep if r["body_toward_street"]]
    # K30(b)'s three populations. The split is by where the record's own POINT stands
    # relative to the corridor it laps, because that is what decides whether the depth is
    # the building's own depth (a drawing fault), the corridor disagreeing with the
    # centreline (a tolerance), or a corner clipping an intersection (neither).
    at_kerb = [r for r in buildings if r["anchor_offset_m"] >= HALF_WIDTH_M
               and r["body_toward_street"] and r["depth_m"] >= DEEP_MODE_M]
    point_inside = [r for r in buildings if r["anchor_offset_m"] < HALF_WIDTH_M]
    lines += [
        "",
        f"{len(furniture)} of them are STREET FURNITURE — a carrying-way archetype with a "
        f"crossing function, which belongs in a corridor and is categorised rather than "
        f"counted (ROADMAP K30(b)): {', '.join(r['structure'] for r in furniture) or '—'}",
        f"{len(buildings)} are buildings drawn standing in a street.",
        f"{len(deep)} of those are in the DEEP mode (>= {DEEP_MODE_M} m), and all "
        f"{len(crossing)} of them have their body drawn TOWARD the street from their own "
        f"anchor — K30(b)'s cause. See --reflect.",
        f"{len(point_inside)} have the authored POINT itself inside a corridor "
        f"(< {HALF_WIDTH_M} m from a centreline), by "
        f"{min(HALF_WIDTH_M - r['anchor_offset_m'] for r in point_inside):.2f}-"
        f"{max(HALF_WIDTH_M - r['anchor_offset_m'] for r in point_inside):.2f} m: "
        f"{', '.join(r['structure'] for r in sorted(point_inside, key=lambda r: r['anchor_offset_m'])) or '—'}. "
        f"That penetration is a floor no redrawing can clear — see --reflect.",
        f"{len(at_kerb)} stand at or beyond the platted kerb with the body drawn back "
        f"across it, which is the population the repair is for.",
        "",
        f"{len(rows)} of {result['placed_phases']} placed phases lap a platted corridor.",
        f"{centroid} of them have their CENTROID in one (T-A7's test).",
        f"{anchor} of them have their authored POSITION POINT in one.",
    ]
    return "\n".join(lines)


def recentre() -> str:
    """K30(a)'s refuted counterfactual, kept as a command so it stays refuted.

    `docs/GLB-CONTRACT.md` puts a record's position at its footprint polygon's own origin,
    and 332 of the 333 committed footprints have local `(0, 0)` at a VERTEX. So a building
    derived to a street corner is drawn with a corner on that point and its body extending
    wherever the polygon and its rotation send it — which looks like the systematic cause
    of a building standing in a street, and which 20 of the 29 anchors standing on legal
    ground make look likelier still.

    It is not the cause. This re-measures every lapping footprint CENTRED on its own anchor
    and reports what that would do. Anything that reads this as a proposal has read it
    backwards: it is here so the next parcel does not have to re-derive the refutation.
    """
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    lanes = active_corridors()
    origin_e = float(datum["origin_utm_e"])
    origin_n = float(datum["origin_utm_n"])

    rows = []
    for structure_id, _phase_id, phase, polygon, _category in placed_phases():
        street, depth = intrusion(polygon, lanes)
        if street is None:
            continue
        position = phase["position"]
        ax = float(position["utm_e"]) - origin_e
        ay = float(position["utm_n"]) - origin_n
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        centred = [(p[0] - cx + ax, p[1] - cy + ay) for p in polygon]
        _, moved = intrusion(centred, lanes)
        rows.append((structure_id, street, depth, moved))

    cleared = [r for r in rows if r[3] <= 0]
    worse = [r for r in rows if r[3] > r[2] + TOLERANCE_M]
    better = [r for r in rows if r[3] > 0 and r[3] < r[2] - TOLERANCE_M]

    lines = [f"{'structure':<44}{'street':<14}{'as drawn':>9}{'centred':>9}{'':>3}"]
    for structure_id, street, depth, moved in sorted(rows, key=lambda r: r[3] - r[2]):
        mark = "" if abs(moved - depth) <= TOLERANCE_M else ("WORSE" if moved > depth else "")
        lines.append(f"{structure_id:<44}{street:<14}{depth:>9.2f}{moved:>9.2f}   {mark}")
    lines += [
        "",
        f"centring every footprint on its own anchor: {len(cleared)} clear the corridor, "
        f"{len(better)} get shallower, {len(worse)} get DEEPER.",
        "So the anchor convention is not the cause and recentring is not the fix "
        "(ROADMAP K30(a), finding 4).",
    ]
    if worse:
        top = max(worse, key=lambda r: r[3] - r[2])
        lines.append(f"Worst regression: {top[0]} {top[2]:.2f} -> {top[3]:.2f} m "
                     f"(+{top[3] - top[2]:.2f}).")
    return "\n".join(lines)


def reflect() -> str:
    """K30(b)'s cause — REFUTED 2026-08-22 by `--anchors`. Read that first.

    THIS COMMAND IS NOW A COUNTERFACTUAL LIKE `--recentre`, NOT A DIAGNOSIS. The paragraph
    below is K30(b)'s reasoning, left standing because the command is its evidence and a
    refuted claim is kept, not deleted. What it gets wrong is stated once, here: it reads
    "the body is drawn toward the street from the anchor" as proof that the ANCHOR is on the
    frontage. It is not. `--anchors` measures which face the anchor is, and on all 17 records
    in the deep mode it is the BACK corner — the point is set back by the footprint's own
    depth so that the street-facing FACE lands on the frontage, which is the same convention
    the dataset's machine-checked derivation blocks state. Reflection therefore takes a
    correctly drawn body a full depth BEHIND its own frontage. See ROADMAP K30(d).

    K30(a) refuted the anchor convention by RECENTRING — moving each footprint half its own
    depth. That was the wrong counterfactual for the right suspect. The convention it was
    testing is real and it is universal: 331 of the 333 committed footprints put local
    (0, 0) at the polygon's minimum corner, so every body in this dataset grows NORTH and
    EAST from the point the record was derived to.

    And the hand-placed South Water records were derived to their FRONTAGE — the position
    notes say so in as many words, "the modern intersection centre was read from
    OpenStreetMap and the footprint offset 12.2 m, half an 80 ft platted street". A point
    on the south kerb, with a body that grows north from it, is a building drawn across its
    own frontage and into the roadway by its full depth. That is not a georeference error
    and no coordinate is wrong; the derivation convention and the drawing convention were
    never reconciled with each other.

    So the counterfactual that tests it is a REFLECTION, not a recentring: mirror the
    footprint about the line through its own anchor parallel to the corridor it laps, which
    is the same record with its body on the other side of the frontage it was derived to.

    THIS IS A DIAGNOSIS AND NOT A PROPOSAL, for two reasons that both matter. It changes
    footprint polygons, so it changes every affected mesh and needs a bake this runner
    cannot do; and "the reflection clears the corridor" is evidence about the CAUSE, not
    authority to redraw a documented building. The repair is K30(c)'s, with the bake.
    """
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    origin_e = float(datum["origin_utm_e"])
    origin_n = float(datum["origin_utm_n"])
    lanes = active_corridors()

    rows = []
    for structure_id, _phase_id, phase, polygon, category in placed_phases():
        street, depth = intrusion(polygon, lanes)
        if street is None:
            continue
        position = phase["position"]
        anchor = (float(position["utm_e"]) - origin_e, float(position["utm_n"]) - origin_n)
        _, axis, _foot = centreline_frame(lanes[street]["centre"], *anchor)
        normal = (-axis[1], axis[0])
        mirrored = []
        for x, y in polygon:
            vx, vy = x - anchor[0], y - anchor[1]
            across = vx * normal[0] + vy * normal[1]
            along = vx * axis[0] + vy * axis[1]
            mirrored.append((anchor[0] + along * axis[0] - across * normal[0],
                             anchor[1] + along * axis[1] - across * normal[1]))
        _, moved = intrusion(mirrored, lanes)
        _, _axis_d, foot = centreline_frame(lanes[street]["centre"], *anchor)
        inside = max(0.0, HALF_WIDTH_M - math.dist(anchor, foot))
        # Is the body drawn toward the street from its own point? Reflection is the
        # correction for one that is, and the wrong operation for one that is not — which
        # is why the law below is stated over the CORRECTED drawing and not over this
        # column. Three records are already drawn correctly and reflection ruins them.
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        normal_a = (-_axis_d[1], _axis_d[0])
        anchor_side = ((anchor[0] - foot[0]) * normal_a[0]
                       + (anchor[1] - foot[1]) * normal_a[1])
        body_side = (cx - anchor[0]) * normal_a[0] + (cy - anchor[1]) * normal_a[1]
        toward = anchor_side * body_side < 0
        corrected = moved if toward else depth
        # Rounded to the same places as the table, so `--reflect` and the distribution
        # cannot disagree about which records are in the deep mode. They did, by one
        # record, while this was being written: log_jail is 3.48 m to the centimetre and
        # 3.4799 m in full, so an unrounded comparison put it in a different mode here
        # than in the table — the same class of mismatch K30(a) finding 3 is about.
        rows.append((structure_id, street, round(depth, PLACES), round(moved, PLACES),
                     category, round(inside, PLACES), round(corrected, PLACES), toward))

    buildings = [r for r in rows if r[4] != "furniture"]
    cleared = [r for r in buildings if r[3] <= TOLERANCE_M]
    worse = [r for r in buildings if r[3] > r[2] + TOLERANCE_M]
    deep = [r for r in buildings if r[2] >= DEEP_MODE_M]
    deep_fixed = [r for r in deep if r[3] < 1.0]

    lines = [f"{'structure':<44}{'street':<14}{'as drawn':>9}{'reflected':>10}"
             f"{'pt inside':>10}{'':>3}"]
    for structure_id, street, depth, moved, _c, inside, _corr, _t in sorted(
            rows, key=lambda r: -r[2]):
        mark = "WORSE" if moved > depth + TOLERANCE_M else (
            "clears" if moved <= TOLERANCE_M else "")
        lines.append(f"{structure_id:<44}{street:<14}{depth:>9.2f}{moved:>10.2f}"
                     f"{inside:>10.2f}   {mark}")

    # THE RESIDUAL LAW, which is the other half of this parcel's answer. Once the body is
    # drawn on the correct side of its own point, what is left in the roadway is how far
    # that POINT stands inside the corridor — and that is not a drawing fault at all, it
    # is the derived corridor and the traced centreline disagreeing. Reported as a
    # measured maximum rather than a claimed tolerance.
    # The population is the KERB HALF of the corridor — a point in the outer half stands
    # near the frontage it was derived to, which is what the law is about. A point in the
    # INNER half is not a frontage placement at all and is named rather than averaged in:
    # today that is one record, and it is the one whose own note says its bank is disputed.
    kerb_half = HALF_WIDTH_M / 2
    frontage = [r for r in buildings if 0 < r[5] <= kerb_half]
    inner = [r for r in buildings if r[5] > kerb_half]
    law = max((abs(r[6] - r[5]), r[0]) for r in frontage) if frontage else (0.0, "—")

    lines += [
        "",
        f"reflecting each body about its own anchor: {len(cleared)} of {len(buildings)} "
        f"clear the corridor outright, {len(worse)} get deeper.",
        f"Of the {len(deep)} records in the DEEP mode (>= {DEEP_MODE_M} m), "
        f"{len(deep_fixed)} fall under 1 m.",
        "So the cause of the deep cluster is the frontage crossing, not the georeference "
        "(ROADMAP K30(b)). It is a DIAGNOSIS: the repair changes footprints, needs a bake, "
        "and is K30(c)'s.",
        "",
        f"THE RESIDUAL LAW, over the {len(frontage)} records whose point stands inside the "
        f"KERB half of a corridor: once the body is drawn on the correct side of its own "
        f"point, the depth still left in the roadway IS that penetration, to within "
        f"{law[0]:.2f} m (worst: {law[1]}). The drawing is what puts a body in the "
        f"road; the point is what the corridor and the traced centreline disagree by, and "
        f"it is the irreducible term the repair cannot reach.",
        f"Point in the INNER half, where the law does not apply and the placement is not a "
        f"frontage placement: {', '.join(f'{r[0]} ({r[5]:.2f} m)' for r in inner) or '—'}.",
    ]
    return "\n".join(lines)


def anchors() -> str:
    """K30(d) — WHERE IN ITS OWN BODY DOES THE RECORD'S POINT SIT? The test K30(b) lacked.

    K30(b) read one flag — is the body drawn toward the street from the anchor? — and
    concluded that the anchor stands on the frontage and the body is drawn across it. That
    flag cannot tell the two arrangements apart, because BOTH make it true:

    * **anchor at the KERB.** The point is on the frontage and the body grows across it into
      the roadway by its own full depth. This is the fault K30(b) described.
    * **anchor at the BACK.** The point is set back from the frontage by the footprint's own
      depth, so the body grows FORWARD and its street-facing FACE lands on the frontage.
      This is a correct drawing, and the body is still "toward the street" from the point.

    The two are separated by one measurement nobody had made: how far the anchor stands from
    the corridor centreline, against how far the body's two faces stand from it. If the
    anchor is the NEAR face the point is at the kerb; if it is the FAR face the point is the
    back corner and the face is what was placed.

    It is the far face on every record in the deep mode. The dataset's own derivation model
    says the same thing in words — `sauganash_hotel`'s machine-checked block reads *"the
    depth is in the polygon, so the constraint is on the FACE"* — and `tools/validate.py`
    recomputes five placements from it on every commit.

    So reflecting a body about its own anchor does not put it back on its frontage; it takes
    it a full depth BEHIND the frontage its control was offset to. See ROADMAP K30(d).
    """
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    origin_e = float(datum["origin_utm_e"])
    origin_n = float(datum["origin_utm_n"])
    lanes = active_corridors()

    rows = []
    for structure_id, _phase_id, phase, polygon, category in placed_phases():
        street, depth = intrusion(polygon, lanes)
        if street is None:
            continue
        position = phase["position"]
        anchor = (float(position["utm_e"]) - origin_e, float(position["utm_n"]) - origin_n)
        _, axis, foot = centreline_frame(lanes[street]["centre"], *anchor)
        normal = (-axis[1], axis[0])

        def across(point: tuple) -> float:
            return (point[0] - foot[0]) * normal[0] + (point[1] - foot[1]) * normal[1]

        # Measured on the anchor's own side of the centreline, so "near" is always the face
        # closer to the middle of the street whichever side of it the record stands on.
        side = 1.0 if across(anchor) >= 0 else -1.0
        offsets = [across(p) * side for p in polygon]
        near, far = min(offsets), max(offsets)
        at = abs(across(anchor))
        # Which face the anchor IS, to the centimetre the rest of this module quotes in.
        seat = ("kerb" if abs(at - near) <= abs(at - far) else "back")
        rows.append((structure_id, street, round(depth, PLACES), round(at, PLACES),
                     round(near, PLACES), round(far, PLACES), seat, category))

    buildings = [r for r in rows if r[7] != "furniture"]
    deep = [r for r in buildings if r[2] >= DEEP_MODE_M]
    at_kerb = [r for r in deep if r[6] == "kerb"]

    lines = [f"{'structure':<44}{'street':<14}{'depth':>7}{'anchor':>8}{'near face':>10}"
             f"{'far face':>9}  {'anchor is'}"]
    for structure_id, street, depth, at, near, far, seat, _c in sorted(rows,
                                                                      key=lambda r: -r[2]):
        lines.append(f"{structure_id:<44}{street:<14}{depth:>7.2f}{at:>8.2f}{near:>10.2f}"
                     f"{far:>9.2f}  {'THE KERB FACE' if seat == 'kerb' else 'the back corner'}")
    lines += [
        "",
        "Distances are metres from the corridor's committed centreline, on the anchor's own "
        f"side of it; the platted half-width is {HALF_WIDTH_M:.3f} m.",
        f"{len(at_kerb)} of the {len(deep)} buildings in the DEEP mode (>= {DEEP_MODE_M} m) "
        f"have their point ON the kerb face, which is the arrangement K30(b) attributed the "
        f"whole cluster to: {', '.join(r[0] for r in at_kerb) or '—'}.",
        "The rest carry the point at the BACK corner, a full footprint depth behind the "
        "street-facing face — so the face is what was placed on the frontage and the drawing "
        "is correct. Reflection moves those bodies a depth BEHIND their own frontage, and "
        "K30(c)'s repair is the wrong operation on them (ROADMAP K30(d)).",
    ]
    return "\n".join(lines)


# How close two bearings have to run before this tool will say one is ALONG the other.
# The committed centrelines are traced polylines, not a drafted grid: the cross streets in
# the business core run at 0.34-0.36 degrees and South Water at 89.53-90.93, so a tolerance
# tighter than a degree would call the same relationship "along" on one block and not on
# the next. Five degrees is comfortably inside the smallest angle any two DIFFERENT streets
# in this plat make with each other, which is what the tolerance actually has to separate.
ALONG_TOLERANCE_DEG = 5.0

# The furthest a corridor may be from a footprint's centroid and still be counted as one of
# the streets that footprint stands on. A corner lot's two streets are both within a street
# module of it; the next street over is a block away.
NEIGHBOUR_M = 60.0


def _bearing(vector: tuple[float, float]) -> float:
    """Compass bearing of a local-ENU vector, degrees clockwise from grid north."""
    return math.degrees(math.atan2(vector[0], vector[1])) % 360.0


def _angle_between_lines(a_deg: float, b_deg: float) -> float:
    """The acute angle between two UNDIRECTED bearings — a street has no forward end."""
    delta = abs(a_deg - b_deg) % 180.0
    return min(delta, 180.0 - delta)


def depth_into(polygon: list, lane: dict) -> float:
    """How deep a footprint reaches into ONE named corridor, in metres from its edge.

    `plat_corridors.intrusion()` answers a different question — the DEEPEST corridor of all
    — and a record standing in two of them at once cannot be asked about one of them
    through it. That distinction is not academic: `first_presbyterian_church` laps both
    Clark and Lake, and a search that stops when the deepest corridor merely CHANGES NAME
    reports it escaping Clark in 28 mm when it has done nothing of the kind.
    """
    ring = lane["ring"]
    worst = 0.0
    for point in sampled(polygon):
        if point_in_polygon(point, ring):
            worst = max(worst, point_to_ring_m(point, ring))
    return worst


def escape(json_out: bool = False) -> str:
    """T-0195 — WHICH WAY WOULD A LAPPING RECORD HAVE TO MOVE, AND WHAT DOES THE MOVE SPEND?

    The table above says how deep each record stands in a roadway. It has never said what
    getting it out would COST, and on a corner that is the whole question. A corner lot has
    two streets. The South Water repair (T-0198, T-0199, and T-0127's method before them)
    re-derived eleven records against this project's own committed centreline for the street
    they FRONT, and translated each one along that street's normal. Three of the eleven
    stand on a corner, and the move that answers the frontage street cannot answer the one
    the building turns onto: they lap the CROSS street's corridor by 0.16-0.21 m.

    So this mode measures the way out, per record, and names what the way out runs along:

    * **escape** — the shortest translation along the lapped corridor's own normal, away
      from it, that takes the footprint clear of that corridor. Bisected against
      `plat_corridors.intrusion()` rather than assumed equal to the depth, because a
      corridor is an offset polyline and its ring is not parallel to a building's wall.
    * **vs front** — that escape bearing read against the record's OWN facade bearing, the
      authored `position.rotation_deg`. `across` means the escape runs into or out of the
      building's front, so the move changes its SETBACK. `along` means the escape runs
      sideways across its front, so the move changes WHERE ALONG THE STREET IT STANDS.
      `oblique` is neither, and on this plat only a record whose facade is not square to
      its own street reads that way.

    A grid tempts a looser test — "is there a nearby street parallel to the escape?" — and
    on an orthogonal plat that test is TRUE FOR EVERY RECORD, because the street crossing
    the one you lap always runs the way you have to move. It says nothing. The facade
    bearing is what distinguishes the two cases, because it is the record's own statement
    about which street it stands on the front of.

    That distinction is the whole of T-0195's refusal. Moving a documented record ACROSS
    its front is re-deriving a setback against a better line, which is what T-0127 did and
    defended: the claim does not move, only the line it was derived against. Moving one
    ALONG its front moves the corner attribution itself — the one part of these three
    placements a source actually argues — to make a derived number smaller, which is the
    thing this file's own note forbids in as many words.
    """
    lanes = active_corridors()
    rows = []
    for structure_id, phase_id, _phase, polygon, category in placed_phases():
        street, depth = intrusion(polygon, lanes)
        if street is None:
            continue
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        _, axis, foot = centreline_frame(lanes[street]["centre"], cx, cy)
        normal = (-axis[1], axis[0])
        side = math.copysign(1.0, (cx - foot[0]) * normal[0] + (cy - foot[1]) * normal[1])
        out = (side * normal[0], side * normal[1])

        def moved_by(distance: float) -> list:
            return [(x + out[0] * distance, y + out[1] * distance) for x, y in polygon]

        # Bisect for the clearance, against THIS corridor rather than against whichever is
        # deepest. The upper bound starts at the depth — the answer on a straight corridor —
        # and doubles until the record is actually clear, so a ring that is not parallel to
        # the wall cannot make the search miss.
        high = max(depth, 0.01)
        while depth_into(moved_by(high), lanes[street]) > 0.0 and high < 50.0:
            high *= 2.0
        low = 0.0
        for _ in range(40):
            mid = (low + high) / 2.0
            if depth_into(moved_by(mid), lanes[street]) > 0.0:
                low = mid
            else:
                high = mid
        after_street, after_depth = intrusion(moved_by(high), lanes)

        bearing = _bearing(out)
        facade = float(_phase["position"].get("rotation_deg") or 0.0) % 360.0
        # The acute angle between the escape and the FACADE NORMAL. Zero means the escape
        # runs straight out of the front (or straight into it); ninety means it runs
        # sideways along the front.
        offset = _angle_between_lines(bearing, facade)
        if offset <= ALONG_TOLERANCE_DEG:
            versus = "across"
        elif abs(offset - 90.0) <= ALONG_TOLERANCE_DEG:
            versus = "along"
        else:
            versus = "oblique"
        # The street the facade actually faces, for legibility: the nearest corridor whose
        # axis is square to the facade normal. Named, never listed.
        fronts, fronts_m = None, None
        for other_id, lane in lanes.items():
            distance, other_axis, _foot = centreline_frame(lane["centre"], cx, cy)
            if distance > NEIGHBOUR_M:
                continue
            if abs(_angle_between_lines(facade, _bearing(other_axis)) - 90.0) > ALONG_TOLERANCE_DEG:
                continue
            if fronts_m is None or distance < fronts_m:
                fronts, fronts_m = other_id, distance
        rows.append({
            "structure": structure_id,
            "phase": phase_id,
            "category": category,
            "street": street,
            "depth_m": round(depth, PLACES),
            "escape_m": round(high, 3),
            "escape_bearing_deg": round(bearing, 2),
            "facade_bearing_deg": round(facade, 2),
            "escape_vs_facade": versus,
            "escape_facade_offset_deg": round(offset, 2),
            "fronts": fronts,
            "fronts_m": None if fronts_m is None else round(fronts_m, PLACES),
            "then_laps": after_street,
            "then_depth_m": round(after_depth, PLACES),
        })

    rows.sort(key=lambda r: r["escape_m"])
    if json_out:
        return json.dumps(rows, indent=2, sort_keys=True)

    lines = [f"{'structure':<44}{'laps':<13}{'depth m':>8}{'escape m':>10}"
             f"{'bearing':>9}  {'vs front':<9}fronts"]
    for r in rows:
        fronts = r["fronts"] or "—"
        lines.append(f"{r['structure']:<44}{r['street']:<13}{r['depth_m']:>8.2f}"
                     f"{r['escape_m']:>10.3f}{r['escape_bearing_deg']:>9.2f}  "
                     f"{r['escape_vs_facade']:<9}{fronts}")

    along = [r for r in rows if r["escape_vs_facade"] == "along"]
    lines += [
        "",
        f"{len(along)} of {len(rows)} records can only get clear by sliding SIDEWAYS ACROSS "
        f"their own front, which moves where along the street the record stands:",
    ]
    for r in along:
        lines.append(f"   {r['structure']:<44}{r['escape_m']:.2f} m along "
                     f"{r['fronts'] or 'its frontage'}, to clear {r['street']}")
    lines += [
        "",
        "The rest escape ACROSS their own front, which is the operation T-0127 and the "
        "South Water repairs performed: the setback is re-derived against this project's "
        "own committed centreline and the along-street coordinate never moves.",
        "A record whose escape leaves it lapping a SECOND street cannot be repaired by "
        "translation at all — it would trade one corridor for another.",
    ]
    traded = [r for r in rows if r["then_laps"]]
    for r in traded:
        lines.append(f"   {r['structure']:<44}clears {r['street']} at "
                     f"{r['escape_m']:.2f} m and then laps {r['then_laps']} "
                     f"at {r['then_depth_m']:.2f} m")
    return "\n".join(lines)


def _baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def gate(quiet: bool = False, result: dict | None = None,
         failures_out: list[str] | None = None) -> int:
    """The ratchet. A new intruder fails; a deeper one fails; a shallower one is a repair.

    Plus two ABSOLUTE assertions that are not ratchets. No generated roof may lap a
    corridor at all — every generator already refuses it through the same module, so the
    invariant is enforceable at zero today and any future breach is a regression rather
    than a debt. And no record may CHANGE CATEGORY: street furniture is the one exemption
    in this table, so the way to abuse it is to make a store into a bridge, and that is
    the check which makes the rule safe to have (ROADMAP K30(b) item 2).

    `result` is the measurement to gate, and defaults to the committed tree's. It is a
    parameter so `--self-test` can hand this function a tree broken in memory and watch
    the absolute assertion fire, rather than asserting in prose that it would (T-0221).
    `failures_out`, when given, is filled with the failure lines so a caller can assert
    on WHICH one fired instead of only on the exit code.
    """
    result = measure() if result is None else result
    baseline = _baseline()
    committed = baseline["lapping"]
    failures: list[str] = []

    generated = sorted(k for k, r in result["lapping"].items() if r["layer"] != "research")
    if generated:
        failures.append(
            f"{len(generated)} generated roof(s) lap a platted corridor, which the "
            f"placement gate refuses by construction: {', '.join(generated[:6])}")

    for key, row in sorted(result["lapping"].items()):
        if key not in committed:
            failures.append(f"{key} newly laps {row['street']} by {row['depth_m']:.2f} m")
        elif row["depth_m"] > committed[key]["depth_m"] + TOLERANCE_M:
            failures.append(f"{key} laps {row['street']} deeper: "
                            f"{committed[key]['depth_m']:.2f} -> {row['depth_m']:.2f} m")
        elif row["street"] != committed[key]["street"]:
            failures.append(f"{key} now laps {row['street']}, "
                            f"was {committed[key]['street']}")
        elif row["category"] != committed[key].get("category", "building"):
            failures.append(
                f"{key} changed category "
                f"{committed[key].get('category', 'building')} -> {row['category']}; "
                f"street furniture is an exemption and may not be acquired by editing an "
                f"archetype or a function")

    # A refusal is a written argument attached to a lap (T-0195). It is checked, not
    # trusted: it has to name a lap that is still there, and it may not quietly become the
    # justification for a DIFFERENT number than the one it was written about.
    refused = baseline.get("refused") or {}
    for key, entry in sorted(refused.items()):
        if key not in result["lapping"]:
            failures.append(
                f"{key} is refused in writing but no longer laps anything — withdraw the "
                f"refusal with --write-baseline, and take the paragraph out of the "
                f"record's position.note with it")
            continue
        row = result["lapping"][key]
        if row["street"] != entry.get("street"):
            failures.append(f"{key} is refused for {entry.get('street')} and now laps "
                            f"{row['street']}; the refusal argues about a different street")
        elif row["depth_m"] > float(entry.get("depth_m", 0.0)) + TOLERANCE_M:
            failures.append(f"{key} laps deeper than the depth it was refused at: "
                            f"{entry.get('depth_m')} -> {row['depth_m']:.2f} m")

    repaired = sorted(set(committed) - set(result["lapping"]))
    shallower = sorted(k for k, r in result["lapping"].items()
                       if k in committed and r["depth_m"] < committed[k]["depth_m"] - TOLERANCE_M)

    furniture = sum(1 for r in result["lapping"].values() if r["category"] == "furniture")
    if not quiet or failures:
        print(f"   {len(result['lapping'])} of {result['placed_phases']} placed phases lap "
              f"a platted corridor ({len(committed)} committed)")
        print(f"   {len(result['lapping']) - furniture} buildings, {furniture} street "
              f"furniture (a bridge in a street is not an intrusion)")
        print(f"   generated roofs lapping a corridor: {len(generated)} (must be 0)")
        print(f"   refused in writing: {len(refused)} "
              f"(each one argued in its own record's position.note)")
    if repaired or shallower:
        print(f"   {len(repaired)} cleared and {len(shallower)} shallower than the "
              f"baseline — re-run with --write-baseline to bank the repair")
    for line in failures:
        print(f"   {line}")
    if failures_out is not None:
        failures_out[:] = failures
    return 1 if failures else 0


def _id_prefix_layer(structure_id: str) -> str:
    """The reading T-0221 REMOVED, kept here and nowhere else so it stays refuted.

    `layer_of` answered from the id until 2026-08-28. This is that answer, verbatim, and
    the only thing it is used for is proving that the reading in force is a different one
    and that the difference is the physician's office. Nothing measures with it.
    """
    if structure_id.startswith("recon_1835_"):
        return "reconstruction"
    if structure_id.startswith("inf_"):
        return "inferred_household"
    return "research"


def _moved_into_the_roadway(structure_id: str, street: str) -> list:
    """The committed placed phases, with one record translated onto a street centreline.

    The centreline is the middle of the roadway, so a footprint whose anchor is put on it
    is unambiguously inside the corridor whatever its shape — and the DEPTH is still
    computed by `measure()` from the moved geometry rather than asserted here. Position
    point and world polygon move by the same vector, because `measure()` reads both and a
    fixture that moved only one would be testing a record this project cannot author.
    """
    lanes = active_corridors()
    points = lanes[street]["centre"]
    moved = []
    for sid, phase_id, phase, polygon, category in placed_phases():
        if sid != structure_id:
            moved.append((sid, phase_id, phase, polygon, category))
            continue
        cx = sum(pt[0] for pt in polygon) / len(polygon)
        cy = sum(pt[1] for pt in polygon) / len(polygon)
        _, _, (fx, fy) = centreline_frame(points, cx, cy)
        dx, dy = fx - cx, fy - cy
        shifted = copy.deepcopy(phase)
        shifted["position"]["utm_e"] = float(shifted["position"]["utm_e"]) + dx
        shifted["position"]["utm_n"] = float(shifted["position"]["utm_n"]) + dy
        moved.append((sid, phase_id, shifted,
                      [(x + dx, y + dy) for x, y in polygon], category))
    return moved


def _gate_failures(result: dict | None = None) -> list[str]:
    """The failure lines `gate` would print, with its report swallowed.

    The self-test runs the gate several times and is reading WHICH assertion fired; its
    running commentary would bury the checks it is printing.
    """
    out: list[str] = []
    with contextlib.redirect_stdout(io.StringIO()):
        gate(quiet=True, result=result, failures_out=out)
    return out


def self_test() -> int:
    """The absolute assertion, broken in memory, and the reading it now rests on.

    T-0221. This gate's censuses and its uncrossable clause — no GENERATED roof laps a
    platted corridor — both ask `layer_of` which evidence layer a record belongs to. That
    question used to be answered from the record's ID PREFIX, so a generated record whose
    filename happens to carry no prefix was scored against the RATCHET, which a
    `--write-baseline` may bank, instead of against the absolute, which nothing may. One
    record was in that position. The last two checks below are that record, put in a
    roadway under both readings.
    """
    checks: list[tuple[str, bool, str]] = []
    committed = layers()

    # 1. the reading is off the record, and the record says which programme wrote it
    record = json.loads(
        (STRUCTURES / "physicians_office.json").read_text(encoding="utf-8"))
    # T-0516: the record's own declaration MOVED, and the reading followed it without a
    # line of this module changing — which is the property the test was written to hold.
    # The owner retired the reconstructed resident population on 2026-09-02 and ruled its
    # roofs kept as anonymous stock, so `physicians_office` now declares
    # `inferred_anonymous` and reads as `reconstruction`. It is still the one record whose
    # id says one layer and whose record says another, which is the whole fixture.
    checks.append(("physicians_office reads as the layer its own record declares",
                   layer_of("physicians_office") == "reconstruction"
                   == layer_of_record(record),
                   f"{layer_of('physicians_office')} / "
                   f"{record['reconstruction']['status']}"))
    checks.append(("…and read from its NAME it was research — the fault, reproduced",
                   _id_prefix_layer("physicians_office") == "research",
                   _id_prefix_layer("physicians_office")))
    checks.append(("…so this test distinguishes the fix from the fault",
                   layer_of("physicians_office")
                   != _id_prefix_layer("physicians_office"), "the two readings differ"))

    # 2. and the set they differ on is the RETIRED HOUSEHOLD LAYER, measured rather than
    #    remembered. It was one record until 2026-09-02 — `physicians_office`, the only
    #    roof of that layer the `inf_` convention never reached. The owner then retired
    #    the reconstructed resident population and ruled its roofs kept as anonymous
    #    stock (T-0516), so all 31 now declare `inferred_anonymous` while their names
    #    still say `inf_`. That is the id reading's reach growing thirtyfold, not
    #    shrinking: a name records the programme that MINTED a record and cannot follow
    #    it when the record's own claim moves, which is why nothing measures with it.
    #    Asserted as the layer rather than as a list of 31 ids, so a roof leaving this
    #    layer fails here instead of being papered over by editing the expected list.
    disagree = sorted(sid for sid, layer in committed.items()
                      if layer != _id_prefix_layer(sid))
    retired = sorted(sid for sid in committed
                     if (json.loads((STRUCTURES / f"{sid}.json").read_text(encoding="utf-8"))
                         .get("reconstruction") or {}).get("programme_phase")
                     == "phase2_inferred_households")
    checks.append((f"across all {len(committed)} committed records the name and the "
                   f"record disagree on exactly the {len(retired)} roofs of the retired "
                   f"inferred-household layer",
                   disagree == retired and len(retired) == 31,
                   f"{len(disagree)} disagree, {len(retired)} retired"))

    # 3. one reading, both callers. `researched_ids` used to carry its own copy.
    checks.append(("plat_occupancy.researched_ids is the research layer of the same map",
                   researched_ids()
                   == {sid for sid, layer in committed.items() if layer == "research"},
                   f"{len(researched_ids())} documented"))
    for layer in LAYERS:
        checks.append((f"…and every record lands in a named layer — {layer}",
                       all(v in LAYERS for v in committed.values()),
                       f"{sum(1 for v in committed.values() if v == layer)}"))

    # 4. an id with no record is refused rather than guessed at from its name
    try:
        layer_of("recon_1835_no_such_record")
        refused = False
    except KeyError:
        refused = True
    checks.append(("an id carrying no committed record is refused, not read off its "
                   "prefix", refused, "KeyError" if refused else "answered anyway"))

    # 5. the negative control: the tree as committed crosses nothing
    live = _gate_failures()
    generated = [m for m in live if "generated roof" in m]
    checks.append(("the committed tree passes the absolute assertion",
                   not generated, "; ".join(live) or "clean"))
    checks.append(("…and physicians_office laps no corridor today, so nothing in the "
                   "tree moves under the fix",
                   not any(k.startswith("physicians_office:")
                           for k in measure()["lapping"]), "clear"))

    # 6. put an ANONYMOUS roof in a roadway: the assertion fires. This is the case the
    #    id reading also caught, and it is here as the control for the one below it.
    anonymous = next(sid for sid in sorted(committed)
                     if committed[sid] == "reconstruction"
                     and any(p[0] == sid for p in placed_phases()))
    broken = _gate_failures(measure(_moved_into_the_roadway(anonymous, "lake")))
    checks.append((f"a reconstruction roof moved onto the Lake Street centreline is "
                   f"caught by the absolute assertion — {anonymous}",
                   any("generated roof" in m for m in broken),
                   next((m for m in broken if "generated roof" in m), "NOT CAUGHT")))

    # 7. and now the ticket's record, in the same roadway, under both readings
    crossed = measure(_moved_into_the_roadway("physicians_office", "lake"))
    fixed = _gate_failures(crossed)
    checks.append(("physicians_office moved onto the same centreline is caught by the "
                   "absolute assertion",
                   any("generated roof" in m and "physicians_office" in m
                       for m in fixed),
                   next((m for m in fixed if "generated roof" in m), "NOT CAUGHT")))

    as_named = copy.deepcopy(crossed)
    for row in as_named["lapping"].values():
        row["layer"] = _id_prefix_layer(row["structure"])
    named = _gate_failures(as_named)
    checks.append(("…and read from its NAME the absolute assertion never fires for it — "
                   "the gate's reach, before the fix",
                   not any("generated roof" in m for m in named),
                   next((m for m in named if "generated roof" in m),
                        "no absolute failure; only the ratchet")))
    checks.append(("…which left it to the RATCHET, and a ratchet can be re-baselined",
                   any(m.startswith("physicians_office:") and "newly laps" in m
                       for m in named),
                   next((m for m in named if m.startswith("physicians_office:")),
                        "nothing fired at all")))

    ok = True
    for label, passed, detail in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  {label} — {detail}")
        ok &= passed
    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


CONTROL_VERDICTS = {
    "recentred": "the corridor is CENTRED ON THE CONTROL — the drawn line is offset "
                 "inside it and does not move",
    "centred": "the drawn line reproduces its control to under a centimetre; nothing "
               "moves",
    "disagree": "two or more control points that do not agree on one offset, so no rigid "
                "translation satisfies them and the corridor stays on the drawn line",
    "off_line": "the control point lies beyond this street's own drawn span",
    "no_control": "no committed control point names this street",
}


def _control_point_label(point: dict) -> str:
    """One control point, as `id +8.58 m` — or as the reason it says nothing."""
    if point["offset_m"] is None:
        return f"{point['control']} (off the drawn span)"
    return f"{point['control']} {point['offset_m']:+.2f} m"


def control_report(json_out: bool = False) -> str:
    """Where every street's platted corridor is centred, and on what.

    T-0009. The owner's ruling of 2026-08-29 — *derive the platted corridor from the street
    CONTROL rather than from the drawn line* — is a rule and not a number, so this is the
    rule's output rather than a paragraph restating it. Nothing here reads a list of street
    ids: a street appears in one verdict or another because of what
    `data/traces/street_control.json` and its own committed centreline say.
    """
    offsets = control_offsets()
    if json_out:
        return json.dumps(offsets, indent=2, sort_keys=True)

    lines = ["street          axis  verdict     offset m  control points",
             "-" * 96]
    order = {"recentred": 0, "disagree": 1, "centred": 2, "off_line": 3, "no_control": 4}
    for sid, row in sorted(offsets.items(), key=lambda kv: (order[kv[1]["verdict"]], kv[0])):
        named = ", ".join(_control_point_label(p) for p in row["points"]) or "—"
        lines.append(f"{sid:15s} {row['axis'] or '--':4s}  {row['verdict']:10s} "
                     f"{row['offset_m']:+8.2f}  {named}")
    lines.append("")
    for verdict in ("recentred", "disagree", "centred", "off_line", "no_control"):
        count = sum(1 for r in offsets.values() if r["verdict"] == verdict)
        if count:
            lines.append(f"{count:3d} {verdict:10s} {CONTROL_VERDICTS[verdict]}")
    lines.append("")
    lines.append("A corridor that is re-centred does NOT move its street: "
                 "data/streets/1835.json is not touched by this derivation, and "
                 "`--drawn` re-runs every mode against the drawn line for comparison.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--by-street", action="store_true", help="the distribution only")
    parser.add_argument("--recentre", action="store_true",
                        help="K30(a)'s refuted counterfactual, kept so it stays refuted")
    parser.add_argument("--reflect", action="store_true",
                        help="K30(b)'s confirmed cause — a diagnosis, not a proposal")
    parser.add_argument("--anchors", action="store_true",
                        help="K30(d)'s test — is the point the kerb face or the back corner")
    parser.add_argument("--escape", action="store_true",
                        help="T-0195 — the way out per record, and what the move spends")
    parser.add_argument("--gate", action="store_true", help="the ratchet check.sh runs")
    parser.add_argument("--self-test", action="store_true",
                        help="put a generated roof in a roadway in memory and check the "
                             "absolute assertion fires")
    parser.add_argument("--write-baseline", action="store_true",
                        help="rewrite the committed table — only to record a repair")
    parser.add_argument("--measured", default=None, metavar="YYYY-MM-DD",
                        help="the date to stamp the baseline with; defaults to today")
    parser.add_argument("--control", action="store_true",
                        help="T-0009 — where each street's corridor is centred, and why")
    parser.add_argument("--drawn", action="store_true",
                        help="T-0009 — measure against the DRAWN line, the pre-ruling "
                             "corridor, so a before-and-after is one command")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    global FROM_CONTROL
    FROM_CONTROL = not args.drawn

    if args.control:
        print(control_report(json_out=args.json))
        return 0

    if args.self_test:
        return self_test()

    if args.gate:
        return gate(quiet=args.quiet)

    if args.recentre:
        print(recentre())
        return 0

    if args.reflect:
        print(reflect())
        return 0

    if args.anchors:
        print(anchors())
        return 0

    if args.escape:
        print(escape(json_out=args.json))
        return 0

    result = measure()

    if args.write_baseline:
        baseline = _baseline() if BASELINE.exists() else {}
        baseline["$note"] = (
            "ROADMAP K30(a). Every committed structure phase whose footprint laps a "
            "platted street corridor, with the depth in metres from the corridor's own "
            "edge. DERIVED — regenerate with tools/measure_corridor_intrusion.py "
            "--write-baseline, and only ever to record a repair. This file is a RATCHET: "
            "tools/check.sh fails on an intruder that is not here and on a listed one "
            "whose depth has grown. It is NOT an allowance — K30(b) owns the fix, and "
            "these are the numbers it takes as its baseline. Never move a documented "
            "building to make an entry smaller: a position with a source outranks a "
            "corridor this project derived. `refused` is the other half of that "
            "sentence (T-0195): a lap whose only escape would move a source-argued "
            "coordinate is refused IN WRITING, per record, here and in the record's own "
            "position.note — not tolerated by silence. A refusal may not outlive the lap "
            "it refuses; the gate says so and --write-baseline drops the stale ones. "
            "T-0009, 2026-08-29, ON THE OWNER'S RULING: the corridor these depths are "
            "measured against is DERIVED FROM THE STREET CONTROL and no longer from the "
            "drawn line — `--control` prints where every street's corridor is centred and "
            "why. One street moves, south_water, whose committed line is drawn 8.58 m "
            "inside its own corridor for the dry-ground reason its record states; "
            "`--drawn` re-runs every mode against the pre-ruling corridor. No building "
            "moved and data/streets/1835.json did not move: this table changed because "
            "the question did.")
        # NOT a constant. This read "2026-08-16" for as long as the file existed, and no
        # --measured option was ever defined to override it, so every repair banked since
        # August has been stamped with the date of the first measurement rather than its
        # own. A banked number whose date is a fossil is the shape of fault this tool was
        # written to stop (T-0195).
        baseline["measured"] = args.measured or _dt.date.today().isoformat()
        baseline["placed_phases"] = result["placed_phases"]
        baseline["corridors"] = result["corridors"]
        baseline["lapping"] = result["lapping"]
        # A refusal is an argument about a lap that exists. When the lap goes, so does the
        # argument — otherwise the file accumulates written refusals of nothing, and the
        # gate below would fail forever on work that was actually a repair.
        refused = baseline.get("refused") or {}
        stale = sorted(k for k in refused if k not in result["lapping"])
        for key in stale:
            refused.pop(key)
        if refused or stale:
            baseline["refused"] = refused
        if stale:
            print(f"   dropped {len(stale)} refusal(s) whose lap is gone: "
                  f"{', '.join(stale)}")
        BASELINE.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(f"   wrote {BASELINE.relative_to(ROOT)}: {len(result['lapping'])} record(s)")
        return 0

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if not args.by_street:
        print(_fmt_table(result))
    print(_distribution(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
