#!/usr/bin/env python3
"""The forge stack: where it stands, how high it reaches, and what it refuses (T-1680).

WHY THIS EXISTS. Family W1 in the archetype crosswalk is the blacksmith shop,
`outbuilding` draws it, and its required variant is `blacksmith_forge` — *"wide work
door; forge chimney; soot; detached"*. The wide door this archetype has always had.
The chimney it did not, so the town's smithies came out of the bake as sheds with a
doorway and no flue, which `pierce_blacksmith_shop` has said on its own record in a
`geometry: absent` note ever since it was written.

WHAT WOULD DRIFT WITHOUT A TEST, and none of it would make an invalid mesh:

  * **The clearance.** The Trustees' ordinance of 5 August 1835 section 18 wants
    eighteen inches of stack above the roof it passes through, and Andreas remembered
    no Chicago chimney four feet above any roof. `tools/measure_stack_ordinance.py`
    gates the floor, and it gates it on the BAKED master — so a stack authored under
    the floor is caught a bake later, by a gate that cannot say which archetype broke
    it. This holds both ends of the bracket on the parameters, before anything bakes.
  * **Which wall it stands against.** `stack_wall` picks an END — a gable on a gable
    roof, so the flue rises under the ridge and takes the shortest way out — and the
    end that does NOT carry the main door. Nothing else in the gate would notice a
    stack standing in the doorway: it is a valid mesh of a building nobody could work.
  * **The refusals.** A count on a privy, a second flue, a stack with no wall to
    stand against. Each is a claim the archetype cannot carry, and an archetype that
    quietly draws nothing on a record that counts one leaves the ordinance gate
    reading that record as an offender — the wrong failure, one step removed.

    python3 tools/test_outbuilding_forge.py
    python3 tools/test_outbuilding_forge.py --self-test   # the assertions must fire
"""
from __future__ import annotations

import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "generators"))

# The builder imports `common.mesh`, which imports Blender. `check.sh` runs on a bare
# Python with no bpy, so the module is stubbed exactly as `measure_stack_projection`
# stubs it — nothing below asks the mesh for anything but the boxes it was handed.
sys.modules.setdefault("bpy", types.ModuleType("bpy"))

from archetypes import outbuilding as OBB  # noqa: E402
from archetypes import outbuilding_params as OB  # noqa: E402

FAILED: list = []

#: The by-law's floor and Andreas's ceiling, in metres. Both are retyped from
#: docs/RESEARCH/chimneys.md § the ordinance rather than imported, so this file says
#: which two numbers it is holding the stack between.
ORDINANCE_FLOOR_M = 18 * 0.0254
ANDREAS_CEILING_M = 48 * 0.0254


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"   — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def shop(width: float = 9.0, depth: float = 7.0, wall: float = 3.0,
         door_side: str = "front", chimneys: int = 1, door: str = "stable",
         open_sides: tuple = ()) -> OB.OutbuildingParams:
    return OB.OutbuildingParams(width_m=width, depth_m=depth, wall_height_m=wall,
                                construction="light_frame", door=door,
                                door_side=door_side, chimneys=chimneys,
                                open_sides=open_sides)


class Boxes:
    """The smallest thing `_forge_stack` can draw into: it only calls `add_box`."""

    def __init__(self) -> None:
        self.boxes: list = []

    def add_box(self, x0, y0, z0, x1, y1, z1, conf, mat, skip=()) -> None:
        self.boxes.append((x0, y0, z0, x1, y1, z1))


def stack_of(p: OB.OutbuildingParams) -> list:
    b = Boxes()
    OBB._forge_stack(b, p, 1.0, OBB.M_CHIMNEY)
    return b.boxes


def refuses(label: str, **kw) -> None:
    try:
        shop(**kw).validate()
    except OB.ParamError as e:
        check(label, True, str(e).split(".")[0][:72])
        return
    check(label, False, "the archetype accepted it")


def main(break_it: bool = False) -> int:
    print("THE FORGE STACK (T-1680)")
    print()

    # --- the clearance bracket, on every plan the family's own band admits ---------
    # W1's authored footprint band is 16x22-24x34 ft and its eave 9-12 ft
    # (data/reconstruction/1835_family_archetype_crosswalk.json). Retyped as feet and
    # converted, so the test says what it is holding the stack to.
    ft = 0.3048
    worst = None
    ok = True
    for w_ft, d_ft in ((16, 22), (24, 34), (22, 16), (34, 24)):
        for wall_ft in (9, 12):
            p = shop(round(w_ft * ft, 3), round(d_ft * ft, 3), round(wall_ft * ft, 3))
            p.validate()
            boxes = stack_of(p)
            top = max(b[5] for b in boxes)
            above = top - p.apex_z_m
            if break_it:
                above = ORDINANCE_FLOOR_M - 0.01
            if not ORDINANCE_FLOOR_M <= above <= ANDREAS_CEILING_M:
                ok = False
            if worst is None or above < worst:
                worst = above
    check("every W1 plan in the band stands its head inside the 18 in - 4 ft bracket",
          ok, f"least {worst:.3f} m above the apex, floor {ORDINANCE_FLOOR_M:.3f} m")

    # --- three blocks, and the flue is narrower than the hearth --------------------
    p = shop()
    p.validate()
    boxes = stack_of(p)
    check("the stack is three blocks — hearth, flue, head", len(boxes) == 3,
          f"{len(boxes)} box(es)")
    spans = [(round(b[3] - b[0], 3), round(b[4] - b[1], 3)) for b in boxes]
    hearth, flue, head = spans
    # index 0 is x and 1 is y; the stack's CROSS axis runs along the wall it is
    # built against, so it is y for an end wall on x and x for one on y.
    cross = 1 if p.stack_wall in ("left", "right") else 0
    check("the flue gathers in from the hearth on both axes",
          flue[0] < hearth[0] and flue[1] < hearth[1], f"hearth {hearth}, flue {flue}")
    check("the head oversails the flue", head[cross] > flue[cross],
          f"flue {flue[cross]} m, head {head[cross]} m across the wall")
    check("the hearth stands on the ground", min(b[2] for b in boxes) == 0.0)

    # --- which wall, and it is never the door's --------------------------------
    # A gable roof puts the ends on the ridge's own axis, so the flue rises under the
    # ridge; the door's end is refused whichever one it is.
    wide = shop(9.0, 7.0)            # ridge along x -> ends are left/right
    deep = shop(7.0, 9.0)            # ridge along y -> ends are back/front
    check("a gable's stack takes an end wall on the ridge's axis",
          wide.stack_wall in ("left", "right") and deep.stack_wall in ("back", "front"),
          f"{wide.width_m}x{wide.depth_m} -> {wide.stack_wall}, "
          f"{deep.width_m}x{deep.depth_m} -> {deep.stack_wall}")
    check("the stack never stands on the wall the main door is cut into",
          all(shop(7.0, 9.0, door_side=s).stack_wall != s for s in ("back", "front")),
          "back and front tried in turn")

    # --- the refusals ---------------------------------------------------------
    # A man door, so the refusal that fires is the chimney's own and not the
    # doorway's — a 1.35 m stable door does not fit a 2.4 m wall either.
    refuses("a chimney on a privy is refused", width=2.4, depth=2.4, wall=2.0,
            door="man")
    refuses("a second flue is refused", chimneys=2)
    refuses("a fractional count is refused", chimneys=True)
    # Both ends open and the door somewhere else, so the refusal that fires is the
    # stack's own: there is no end wall left for it to be built against.
    refuses("a stack with no wall to stand against is refused",
            width=7.0, depth=9.0, door_side="left", open_sides=("back", "front"))

    # --- and nothing is drawn where nothing is counted -------------------------
    check("a record that counts no chimney gets no stack",
          stack_of(shop(chimneys=0)) == [])

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"W1's forge stack OK — head {worst:.3f} m clear of the apex at the tightest "
          f"plan in the band")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("SELF-TEST: the head is dropped under the by-law; the bracket must fire.")
        rc = main(break_it=True)
        if rc == 0:
            print("SELF-TEST FAILED: the assertions passed on a stack under the floor.")
            sys.exit(1)
        print("self-test OK — the assertions fire when the stack drops under the by-law.")
        sys.exit(0)
    sys.exit(main())
