#!/usr/bin/env python3
"""How much buildable ground the town actually has south of its committed plat.

ROADMAP T-E4 / ticket T-0026. The parcel was opened on a reading of the 1830 sheet —
*"the owner is right that south is where the room is"* — and it told the next run to
widen the eligible ground southward and let `tools/reconcile_665.py` re-apportion the
remainder onto it. Its own acceptance names the condition: a roof may stand only where
the ground is **covered by the heightfield AND historically plausible**.

MEASURED AGAINST THE COMMITTED HEIGHTFIELD, THE PREMISE DID NOT SURVIVE — AND THEN THE
GROUND CAME. What this command reported from 2026-08-24 to 2026-09-13 is kept here
because it is what the schedule was built on: the modelled box ended at local **N -400
m**, that line fell INSIDE Washington Street's own 80 ft corridor, the field held 0.08 ha
of land south of it and none of it in the South Division, Madison Street stood 125 m
further south, and the plat's last tier of blocks was 100 % unmodelled — 0 of its 24
block-boundary points on the field. So the blocker the 665-roof programme named for the
South was the wrong one: it said street control, and street control stopped where the
ground did.

**T-0219 carried the field to N -530 and the tier is on it, at 24 of 24.** The three
figures now read 14.55 ha of land south of Washington's corridor with 9.90 ha of it in
the South Division, Washington's corridor fully on the field, and Madison 4.8 m NORTH of
the field's edge instead of 125 m south of it. `reconcile_665.py` branches on the last of
those and the South's `waiting_on` names STREET CONTROL — the plat's seven north-south
columns are still cut at N -400, the field's OLD south edge, and carrying them to Madison
is now street work on ground that is under them. Ground east of State is still not coming
at any date; it is the United States Reservation (T-E2).

    tools/measure_southern_ground.py             the report
    tools/measure_southern_ground.py --gate      the two assertions
    tools/measure_southern_ground.py --self-test prove both assertions still fire

The two assertions, and why each is worth having:

* **No committed platted block stands off the modelled ground.** Absolute, zero today,
  and it is the assertion that fires the day a centreline is carried south without the
  terrain following: the failure then arrives here, at the commit, naming the block —
  instead of arriving inside a parcel run as a per-placement "falls outside the modelled
  terrain" that reads like a bad recipe.
* **The programme's stated southern coverage is the measured one.** `reconcile_665.py`
  writes these figures into `coverage`; a terrain extension that opens southern ground
  and is not re-derived fails here. This is the same shape as T-E2's under-coverage
  count, and for the same reason: a number that can go stale in silence is a number the
  next parcel will schedule against.

Exit 0 pass, 1 on a failed assertion, 2 if the inputs cannot be read.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

STREETS_PATH = DATA / "streets" / "1835.json"
LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
PROGRAMME_PATH = DATA / "reconstruction" / "1835_665_roof_programme.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"

WATER_SURFACE_M = 0.0

# The plat's southern tier, west to east: the six pairings of committed north-south lines
# that Washington and Madison would bound between the river and the reservation. Market is
# the first column east of the South Branch and State is the plat's east boundary, so this
# is the whole of the tier inside the South Division — nothing is chosen here that the grid
# would not itself propose.
TIER_COLUMNS = ["market", "franklin", "wells", "lasalle", "clark", "dearborn", "state"]


def die(msg: str) -> None:
    print(f"cannot measure: {msg}", file=sys.stderr)
    raise SystemExit(2)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# the two lines this measurement is taken between


def plat_frame() -> tuple[float, tuple[float, float], float]:
    """The plat's bearing, its SE section corner, and the platted half-width.

    All three are inherited rather than re-argued: `plat_bearing` and `section_corner`
    are T-E2's, committed in `tools/measure_no_build_ground.py` and already asserting
    that the plat's own east-west streets agree; the half-width is the module in
    `data/traces/street_control.json` that every block edge in this dataset is offset by.
    """
    from measure_no_build_ground import plat_bearing, section_corner  # noqa: PLC0415

    control = load(DATA / "traces" / "street_control.json")
    return (plat_bearing(), section_corner(),
            float(control["platted_street"]["half_width_m"]))


def madison_line(slope: float, corner: tuple[float, float]):
    """Madison Street's platted centreline, as a function of easting.

    NOT A TRACE, and it is the same construction T-E2 used for the reservation's south
    boundary — which is this same line, continued east of State. `G1` is the PLSS corner
    of sections 9/10/15/16 and the GCP file calls it *the town plat's SE corner*; the
    bearing is the plat's own. Nothing else in this project fixes Madison, and inventing
    a trace for it would be worse than saying where the construction came from.
    """
    ge, gn = corner
    return lambda e: gn + (e - ge) * slope


def perpendicular_offset(half_width: float, slope: float) -> float:
    """Half a corridor, expressed as a northing step on a line of this bearing."""
    return half_width / math.cos(math.atan(slope))


def street_paths() -> dict:
    return {s["id"]: [(float(e), float(n)) for e, n in s["path_local_enu_m"]]
            for s in load(STREETS_PATH)["streets"]}


def line_at(path, e: float) -> float:
    """The northing of a committed straight-ish centreline at this easting.

    Extrapolated beyond the drawn ends on the terminal segment's own bearing. That is a
    construction and it is used for exactly one thing — carrying the plat's columns south
    of where the ground stops, so the tier they would bound can be measured at all. No
    geometry derived from it is committed anywhere.
    """
    for a, b in zip(path, path[1:]):
        if min(a[0], b[0]) - 1e-6 <= e <= max(a[0], b[0]) + 1e-6:
            t = 0.0 if b[0] == a[0] else (e - a[0]) / (b[0] - a[0])
            return a[1] + t * (b[1] - a[1])
    a, b = (path[0], path[1]) if e < path[0][0] else (path[-2], path[-1])
    if b[0] == a[0]:
        return a[1]
    return a[1] + (e - a[0]) / (b[0] - a[0]) * (b[1] - a[1])


# --------------------------------------------------------------------------
# the measurement


def field_or_die():
    try:
        from heightfield import Heightfield  # noqa: PLC0415
        field = Heightfield.load(EPOCH)
    except Exception as exc:  # pragma: no cover — an unreadable field is fatal either way
        die(f"the committed heightfield did not load: {exc}")
    if field is None:
        die("the committed heightfield is missing")
    return field


def refused_rings() -> dict:
    """The two grounds T-E2 withdrew from the buildable town, resolved from the traces."""
    from measure_no_build_ground import bar_ring, reservation_ring  # noqa: PLC0415

    ring, _madison, _section = reservation_ring()
    return {"fort_dearborn_reservation": ring, "river_mouth_sand_bar": bar_ring()}


def south_of_the_plat(field, paths, slope, half_width) -> dict:
    """Every field cell south of Washington's platted corridor, classified.

    The corridor's south edge and not its centreline, because the question is what is
    left for a BUILDER: the roadway is not building ground, and this project has refused
    a roof in it since K7.
    """
    from measure_no_build_ground import inside as point_in_ring  # noqa: PLC0415

    rings = refused_rings()
    dn = perpendicular_offset(half_width, slope)
    washington = paths["washington"]
    cell = field.cell_m
    # Only the rows that can possibly qualify. The corridor's south edge is at its
    # northernmost over the field's west end, so nothing north of that can be south of it.
    limit = max(line_at(washington, field.origin_e) - dn,
                line_at(washington, field.origin_e + (field.cols - 1) * cell) - dn)

    out = {"cells": 0, "land": 0, "water": 0, "refused": 0,
           "land_e_min": None, "land_e_max": None, "land_in_south_division": 0}
    market_e = line_e(paths["market"])
    for j in range(field.rows):
        n = field.origin_n + j * cell
        if n >= limit:
            break
        for i in range(field.cols):
            e = field.origin_e + i * cell
            if n >= line_at(washington, e) - dn:
                continue
            out["cells"] += 1
            if field._at(i, j) <= WATER_SURFACE_M:
                out["water"] += 1
                continue
            if any(point_in_ring((e, n), ring) for ring in rings.values()):
                out["refused"] += 1
                continue
            out["land"] += 1
            out["land_e_min"] = e if out["land_e_min"] is None else min(out["land_e_min"], e)
            out["land_e_max"] = e if out["land_e_max"] is None else max(out["land_e_max"], e)
            if e >= market_e - half_width:
                out["land_in_south_division"] += 1
    area = cell * cell
    out["land_ha"] = out["land"] * area / 1e4
    out["south_division_land_ha"] = out["land_in_south_division"] * area / 1e4
    return out


def line_e(path) -> float:
    """The mean easting of a north-south committed line."""
    return sum(p[0] for p in path) / len(path)


def washington_off_field(field, paths, slope, half_width) -> dict:
    """How much of Washington Street's own platted corridor lies off the modelled ground.

    The corridor is a legal 80 ft strip, so half of it is south of the centreline; the
    field's south edge cuts through that half. Integrated in closed form — the corridor
    edge and the field edge are both straight lines over this reach.
    """
    dn = perpendicular_offset(half_width, slope)
    path = paths["washington"]
    e0, e1 = path[0][0], path[-1][0]
    south_edge = lambda e: line_at(path, e) - dn                       # noqa: E731
    depth = lambda e: max(0.0, field.origin_n - south_edge(e))         # noqa: E731
    # Where the corridor's south edge crosses the field's south edge.
    d0, d1 = depth(e0), depth(e1)
    if d0 > 0 and d1 > 0:
        start = e0
    elif d0 <= 0 and d1 <= 0:
        return {"length_m": 0.0, "area_m2": 0.0, "max_depth_m": 0.0}
    else:
        lo, hi = (e0, e1) if d0 <= 0 else (e1, e0)
        for _ in range(80):
            mid = (lo + hi) / 2
            if depth(mid) > 0:
                hi = mid
            else:
                lo = mid
        start = (lo + hi) / 2
    end = e1 if d1 > 0 else e0
    length = abs(end - start)
    return {"length_m": length,
            "area_m2": length * (depth(start) + depth(end)) / 2.0,
            "max_depth_m": max(d0, d1)}


def tier_blocks(field, paths, slope, corner, half_width) -> dict:
    """The plat's last tier — Washington to Madison, Market to State — and its coverage.

    Built by `tools/generate_plat_lots.py`'s own `build_block`, on two constructions that
    are declared rather than hidden: Madison's centreline from the section corner, and the
    committed north-south lines carried south on their own bearing. Both are needed only
    to say how large the missing tier is; nothing built from them is committed.
    """
    from generate_plat_lots import (  # noqa: PLC0415
        block_edges, build_block, polygon_area, street_lines, subdivide,
    )

    madison = madison_line(slope, corner)
    dn = perpendicular_offset(half_width, slope)
    streets = load(STREETS_PATH)
    lines = street_lines(streets)
    module = load(LOTS_PATH)["module"]

    # Carry the columns south to a little past Madison's far corridor edge, and give
    # Madison a straight centreline across the same span.
    e_lo = min(min(p[0] for p in paths[c]) for c in TIER_COLUMNS) - 2 * half_width
    e_hi = max(max(p[0] for p in paths[c]) for c in TIER_COLUMNS) + 2 * half_width
    reach_n = min(madison(e_lo), madison(e_hi)) - 2 * half_width
    for column in TIER_COLUMNS:
        path = paths[column]
        south, north = (path[0], path[-1]) if path[0][1] < path[-1][1] else (path[-1], path[0])
        de, dnn = south[0] - north[0], south[1] - north[1]
        if dnn == 0:
            die(f"{column}'s committed line has no north-south extent to carry")
        t = (reach_n - north[1]) / dnn
        lines[column]["points"] = [(north[0] + de * t, reach_n), north]
    lines["madison"] = {"id": "madison", "name": "Madison Street",
                        "points": [(e_lo, madison(e_lo)), (e_hi, madison(e_hi))],
                        "mean_e": (e_lo + e_hi) / 2,
                        "mean_n": (madison(e_lo) + madison(e_hi)) / 2,
                        "confidence": "inferred"}

    import generate_plat_lots as plat  # noqa: PLC0415
    saved = plat.EW_STREETS
    try:
        plat.EW_STREETS = list(saved) + ["madison"]
        edges = block_edges(lines, half_width)
    finally:
        plat.EW_STREETS = saved

    rows, area_m2, lots = [], 0.0, 0
    for west, east in zip(TIER_COLUMNS, TIER_COLUMNS[1:]):
        block, why = build_block("washington", "madison", west, east, lines, edges,
                                 half_width)
        if block is None:
            die(f"the plat module refuses blk_washington_{west}: {why}")
        ring = block["ring"]
        a = polygon_area(ring)
        covered = sum(1 for e, n in ring if field.covers(e, n))
        divided = subdivide(block, float(module["alley_width_m"]),
                            float(module["lot_frontage_m"]))
        rows.append({"id": f"blk_washington_{west}", "area_m2": a,
                     "lots": len(divided["lots"]),
                     "ring_points_on_field": covered, "ring_points": len(ring)})
        area_m2 += a
        lots += len(divided["lots"])
    covered_any = sum(r["ring_points_on_field"] for r in rows)
    return {"blocks": rows, "count": len(rows), "area_ha": area_m2 / 1e4,
            "lots": lots, "ring_points_on_field": covered_any,
            "madison_at": {"market": madison(line_e(paths["market"])),
                           "state": madison(line_e(paths["state"]))},
            "madison_corridor_north_edge_at_state": madison(line_e(paths["state"])) + dn}


def committed_blocks_off_field(field) -> list:
    """Committed platted blocks any part of whose boundary is off the modelled ground."""
    off = []
    for block in load(LOTS_PATH)["blocks"]:
        misses = [(e, n) for e, n in block["boundary_local_enu_m"]
                  if not field.covers(e, n)]
        if misses:
            off.append({"id": block["id"], "points_off": len(misses),
                        "points": len(block["boundary_local_enu_m"])})
    return off


def measure() -> dict:
    field = field_or_die()
    paths = street_paths()
    slope, corner, half_width = plat_frame()
    census = south_of_the_plat(field, paths, slope, half_width)
    tier = tier_blocks(field, paths, slope, corner, half_width)
    return {
        "field": {
            "south_edge_n_m": field.origin_n,
            "cell_m": field.cell_m,
            "north_edge_n_m": field.origin_n + (field.rows - 1) * field.cell_m,
        },
        "washington_corridor": washington_off_field(field, paths, slope, half_width),
        "south_of_plat": census,
        "tier": tier,
        "columns_end_n_m": {c: min(p[1] for p in paths[c]) for c in TIER_COLUMNS},
        "off_field_blocks": committed_blocks_off_field(field),
    }


def coverage_figures(m: dict | None = None) -> dict:
    """The figures `tools/reconcile_665.py` carries into the programme's `coverage`.

    Deliberately a small, stable subset: what a scheduler needs in order not to book a
    roof onto ground that is not there. Rounded here, once, so the programme and this
    command cannot disagree at the last decimal.

    The tier's three figures were `unmodelled_tier_*` until T-0219 carried the field
    south to Madison and the tier stopped being unmodelled. They are `last_tier_*` now,
    and they carry the count that decides it: how many of the tier's 24 block-boundary
    points stand on the field. A key that states a conclusion goes stale the day the
    conclusion changes; a key that states a measurement does not.
    """
    m = measure() if m is None else m
    return {
        "field_south_edge_n_m": round(m["field"]["south_edge_n_m"], 1),
        "madison_line_n_m_at_state": round(m["tier"]["madison_at"]["state"], 1),
        "madison_south_of_field_m": round(
            m["field"]["south_edge_n_m"] - m["tier"]["madison_at"]["state"], 1),
        "land_south_of_committed_plat_ha": round(m["south_of_plat"]["land_ha"], 4),
        "south_division_land_south_of_committed_plat_ha": round(
            m["south_of_plat"]["south_division_land_ha"], 4),
        "last_tier_blocks": m["tier"]["count"],
        "last_tier_lots": m["tier"]["lots"],
        "last_tier_area_ha": round(m["tier"]["area_ha"], 2),
        "last_tier_ring_points_on_field": m["tier"]["ring_points_on_field"],
        "last_tier_ring_points": sum(r["ring_points"] for r in m["tier"]["blocks"]),
    }


# --------------------------------------------------------------------------
# report, gate, self-test


def report(m: dict) -> None:
    f, w, c, t = m["field"], m["washington_corridor"], m["south_of_plat"], m["tier"]
    print("the modelled ground's south edge, against the plat")
    print(f"  field south edge                    local N {f['south_edge_n_m']:.1f} m")
    print(f"  Washington's corridor off the field {w['length_m']:.0f} m of its length, "
          f"{w['area_m2'] / 1e4:.2f} ha, up to {w['max_depth_m']:.2f} m deep")
    print(f"  Madison's line at State             local N {t['madison_at']['state']:.1f} m, "
          f"{f['south_edge_n_m'] - t['madison_at']['state']:.1f} m south of the field")
    print(f"  Madison's line at Market            local N {t['madison_at']['market']:.1f} m")
    ends = m["columns_end_n_m"]
    print(f"  the plat's columns end at           local N "
          f"{', '.join(f'{v:.0f}' for v in ends.values())}")

    print("\nground south of Washington's platted corridor, on the committed field")
    area = f["cell_m"] * f["cell_m"]
    print(f"  cells                {c['cells']:>7}   ({c['cells'] * area / 1e4:.2f} ha)")
    print(f"  land above the water {c['land']:>7}   ({c['land_ha']:.4f} ha)")
    print(f"  water                {c['water']:>7}")
    print(f"  refused (T-E2)       {c['refused']:>7}")
    if c["land"]:
        print(f"  that land runs local E {c['land_e_min']:.0f} to {c['land_e_max']:.0f} m")
    print(f"  of it, in the South Division: {c['land_in_south_division']} cell(s), "
          f"{c['south_division_land_ha']:.4f} ha")

    print("\nthe tier the plat has and the ground has not — Washington to Madison")
    print(f"  {'block':<26}{'area m2':>10}{'lots':>6}{'ring pts on field':>20}")
    for row in t["blocks"]:
        print(f"  {row['id']:<26}{row['area_m2']:10.0f}{row['lots']:6d}"
              f"{row['ring_points_on_field']:>13} of {row['ring_points']:<4}")
    print(f"  {t['count']} blocks, {t['lots']} lots, {t['area_ha']:.2f} ha, "
          f"{t['ring_points_on_field']} boundary points on modelled ground")

    print("\ncommitted platted blocks off the modelled ground: "
          f"{len(m['off_field_blocks'])}")
    for row in m["off_field_blocks"]:
        print(f"  {row['id']}: {row['points_off']} of {row['points']} boundary points")


def gate(m: dict) -> int:
    failed = 0
    if m["off_field_blocks"]:
        failed += 1
        names = ", ".join(r["id"] for r in m["off_field_blocks"])
        print(f"\n  FAIL {len(m['off_field_blocks'])} committed platted block(s) stand off "
              f"the modelled ground: {names}. A block the plat emits is a block the "
              "schedule will deal roofs to, and every one of those placements dies in "
              "tools/generate_block_infill.py. Extend the terrain or withdraw the street "
              "control that emitted the block.")

    if not PROGRAMME_PATH.exists():
        print("\n  FAIL the 665-roof programme is missing, so its southern coverage "
              "cannot be held to the ground")
        failed += 1
    else:
        stated = (load(PROGRAMME_PATH).get("coverage") or {}).get("southern_ground")
        measured = coverage_figures(m)
        if stated != measured:
            failed += 1
            print("\n  FAIL the programme's stated southern coverage is not what the "
                  "ground measures.")
            for key in sorted(set(measured) | set(stated or {})):
                want, got = measured.get(key), (stated or {}).get(key)
                if want != got:
                    print(f"       {key}: programme {got!r}, measured {want!r}")
            print("       Re-run tools/reconcile_665.py. If the terrain has reached "
                  "further south, the roofs move with it.")

    print("\nSOUTHERN GROUND PASS" if not failed else "\nSOUTHERN GROUND FAIL")
    return 1 if failed else 0


def self_test() -> int:
    """Prove both assertions fire, by breaking each one in memory."""
    m = measure()
    ok = True

    broken = json.loads(json.dumps(m))
    broken["off_field_blocks"] = [{"id": "blk_washington_clark", "points_off": 5,
                                   "points": 5}]
    if gate(broken) == 0:
        ok = False
        print("  SELF-TEST FAIL: a block off the modelled ground did not fail the gate")

    broken = json.loads(json.dumps(m))
    broken["south_of_plat"]["land_ha"] = m["south_of_plat"]["land_ha"] + 4.0
    if gate(broken) == 0:
        ok = False
        print("  SELF-TEST FAIL: southern ground appearing under the programme's feet "
              "did not fail the gate")

    if gate(m) != 0:
        ok = False
        print("  SELF-TEST FAIL: the committed dataset does not pass its own gate")

    print("\nSELF-TEST PASS" if ok else "\nSELF-TEST FAIL")
    return 0 if ok else 1


KNOWN_ARGS = {"--gate", "--self-test", "--quiet"}


def main() -> int:
    args = set(sys.argv[1:])
    if args - KNOWN_ARGS:
        die(f"unknown argument(s): {' '.join(sorted(args - KNOWN_ARGS))}")
    if "--self-test" in args:
        return self_test()
    m = measure()
    if "--quiet" not in args:
        report(m)
    if "--gate" in args:
        return gate(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
