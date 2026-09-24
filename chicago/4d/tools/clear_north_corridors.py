#!/usr/bin/env python3
"""Move the north bank's invented roofs out of the streets the corridor layer just read.

T-1191. Until 2026-09-19 `plat_corridors.corridors()` returned nothing north of the
main stem, because one pair of street lists in `generate_plat_lots.py` decided both
which streets a BLOCK may be cut between and which streets a BUILDING may be reported
standing in. The north bank had neither, so every north-side placement test passed by
asking a question about ground it did not cover:

* `generate_north_infill.py` asks `plat_corridors.intrusion()` of all sixty roofs in
  the North Division parcel, and says so in a comment that ends *"The day that control
  arrives, this parcel is already inside the rule rather than waiting to be found in
  the road by a report."* The control arrived with T-1191 and eight of the sixty were
  in the road.
* `inf_labourer_shanty_north_a`, `inf_labourer_shanty_north_b` and
  `inf_mason_dwelling_north` each carry a position note saying the centre was tested
  *"against the platted street corridors of the K7 block grid so that no invented
  building stands in the roadway"*. The K7 grid is nineteen South and West Division
  blocks. All three stood on Kinzie Street's centreline. THEY ARE NOT THIS TOOL'S,
  and the first pass of T-1191 moved them here by hand before noticing: they are
  DERIVED by `tools/generate_inferred_households.py` out of the inferred-household
  programme, and that pass has owned a `corridor_clearance` declaration since T-1227
  precisely so a corridor can move one of its roofs without anybody hand-editing the
  file it writes. All three now declare one, against `kinzie`, with their own reason.
  What this tool owns is the sixty-roof North Division parcel and nothing else.

THE RULE, and it is the whole tool. A body whose only claim to its coordinate is that
the ground was free is moved the SHORTEST DISTANCE ALONG THE OFFENDING CORRIDOR'S OWN
CROSS-AXIS that puts its whole footprint clear of every platted corridor, plus
`MARGIN_M`. Nothing rotates, nothing resizes, nothing changes family, class or
frontage band, and no body with a SOURCE for its position is touched — the baseline's
own sentence governs that: *"Never move a documented building to make an entry
smaller: a position with a source outranks a corridor this project derived."*
`watkins_school_house` and `north_bank_shed_dearborn_e1` are therefore left exactly
where they stand and enter the intrusion baseline as the debt they are.

Every move here is inside the recipe's own stated placement uncertainty — the North
parcel declares `working_horizontal_uncertainty_m: 25` and *"every placement remains
conjectural"* — so no move spends evidence. The largest is reported by `--check`.

    tools/clear_north_corridors.py            what laps, and what would clear it
    tools/clear_north_corridors.py --write    move them, in the recipe and the records

NOT WIRED INTO tools/check.sh ON PURPOSE. `measure_corridor_intrusion.py --gate`
already asserts that no generated roof laps a corridor, absolutely and at zero, and a
second gate over the same invariant would only be a second thing to keep true.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from plat_corridors import corridors, intrusion  # noqa: E402

DATA = ROOT / "data"
RECIPE = DATA / "reconstruction" / "1835_north_division_initial_parcel.json"
STRUCTURES = DATA / "structures"

# How far outside a corridor edge a cleared footprint is put. The corridor ring is an
# offset polyline and the recipe's coordinates are quoted to the centimetre, so a body
# parked exactly on the edge is one rounding away from being back in the road. Half a
# metre is far enough to be unambiguous and far below the 25 m the recipe declares.
MARGIN_M = 0.5

# The search is a walk out along the cross-axis at this pitch, both ways, and the
# nearer clear station wins. It is not a solver: the answer wanted is the SMALLEST
# move, and stepping is the way to be sure the one returned is it.
STEP_M = 0.1
REACH_M = 60.0


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def polygon_at(footprint: list, centre_e: float, centre_n: float,
               rotation_deg: float = 0.0) -> list:
    """A footprint's world polygon with its ANCHOR at the given point.

    The recipe anchors on the footprint centre and the structure records anchor on the
    polygon's own origin, so the caller hands in the offset it means and this only
    rotates and translates.
    """
    import math
    theta = math.radians(rotation_deg)
    cos, sin = math.cos(theta), math.sin(theta)
    return [(centre_e + u * cos + v * sin, centre_n - u * sin + v * cos)
            for u, v in footprint]


def worst(polygon: list, lane_sets: list[dict]) -> tuple[str | None, float]:
    """The deepest lap into ANY of the corridor readings this project holds.

    TWO READINGS, AND A CLEARED BODY IS CLEAR OF BOTH. T-0009 split them on the owner's
    ruling of 2026-08-29: the intrusion TABLE measures against corridors centred on each
    street's committed CONTROL, while every generator keeps measuring against the
    corridor as DRAWN, because a visitor walks the committed centreline. North of the
    river the two are not the same question — Kinzie Street holds control at
    `kinzie_canal` and its control-centred corridor stands 2.91 m north of its drawn
    line — and a body cleared of one alone is still in the road on the other. That is
    exactly what happened on the first pass of this tool: three shanties cleared the
    drawn corridor and the gate still found them 2.3 m inside the platted one.
    """
    street, depth = None, 0.0
    for lanes in lane_sets:
        sid, d = intrusion(polygon, lanes)
        if sid is not None and d > depth:
            street, depth = sid, d
    return street, depth


def clear_offset(polygon: list, axis: str, lane_sets: list[dict]
                 ) -> tuple[float, str | None, float]:
    """The shortest move along `axis` that takes this polygon out of every corridor.

    Returns the signed offset, the street it was in, and the depth it was in by.
    An offset of 0.0 means it was already clear.
    """
    street, depth = worst(polygon, lane_sets)
    if street is None:
        return 0.0, None, 0.0
    steps = int(REACH_M / STEP_M)
    for k in range(1, steps + 1):
        for sign in (1.0, -1.0):
            shift = sign * k * STEP_M
            moved = ([(e + shift, n) for e, n in polygon] if axis == "e"
                     else [(e, n + shift) for e, n in polygon])
            if worst(moved, lane_sets)[0] is None:
                # Clear at `shift`; push MARGIN_M further out in the same direction.
                return round(shift + sign * MARGIN_M, 2), street, depth
    raise SystemExit(f"no station within {REACH_M} m on the {axis} axis clears every "
                     f"corridor; this body needs a decision, not a nudge")


def axis_of(street: str, lanes: dict) -> str:
    """Which local axis the corridor's cross-axis is."""
    from generate_plat_lots import CORRIDOR_EW  # noqa: PLC0415
    return "n" if street in CORRIDOR_EW else "e"


def recipe_rows(recipe: dict) -> list[dict]:
    fields = recipe["placement_fields"]
    return [dict(zip(fields, row)) for row in recipe["placements"]]


def main() -> int:
    write = "--write" in sys.argv
    lanes = corridors()
    lane_sets = [lanes, corridors(from_control=True)]
    recipe = load(RECIPE)
    fields = recipe["placement_fields"]
    moves: list[tuple[str, str, float, float, float]] = []

    # ---- the North Division parcel, in the recipe ----------------------------------
    #
    # The polygon is the GENERATOR'S own, through its own `make_record`/`world_polygon`,
    # not a rectangle rebuilt from the recipe's width and depth columns: those columns
    # hold one production rectangle per family and the record draws its massing inside
    # it, and `TERRAIN_ADJUSTMENTS` moves some sequences again after the recipe is read.
    # A tool that measured its own rectangle would clear a body this project does not
    # draw. `records_from_inputs()` is not used because it runs `validate()`, which is
    # the very assertion this tool exists to satisfy.
    from generate_north_infill import (  # noqa: PLC0415
        deal_siding, make_record, world_polygon,
    )
    datum_doc = load(DATA / "datum.json")
    records = [make_record(row, datum_doc) for row in recipe["placements"]]
    deal_siding(records)
    idx_e, idx_n = fields.index("center_e_m"), fields.index("center_n_m")
    for row, record in zip(recipe["placements"], records):
        poly = world_polygon(record, datum_doc)
        street, depth = worst(poly, lane_sets)
        if street is None:
            continue
        axis = axis_of(street, lanes)
        shift, _, _ = clear_offset(poly, axis, lane_sets)
        moves.append((record["id"], street, depth, shift, abs(shift)))
        idx = idx_e if axis == "e" else idx_n
        row[idx] = round(float(row[idx]) + shift, 2)

    record_edits: list = []

    if not moves:
        print("every invented north-bank roof is clear of every platted corridor")
        return 0

    print(f"{len(moves)} invented north-bank roof(s) lap a platted corridor:")
    for sid, street, depth, shift, _ in sorted(moves, key=lambda m: -m[2]):
        print(f"  {sid:34s} in {street:16s} by {depth:5.2f} m -> move {shift:+6.2f} m")
    print(f"  largest move {max(m[4] for m in moves):.2f} m; the recipe declares "
          f"{recipe['coordinate_basis']['working_horizontal_uncertainty_m']} m of "
          f"working horizontal uncertainty")

    if not write:
        print("  (nothing written; re-run with --write)")
        return 0

    RECIPE.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"  wrote {RECIPE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
