#!/usr/bin/env python3
"""T-3354: a rear wing's lights cut as stone-mullioned groups (`rear_wings[].mullioned`).

The 1919 programme and 1913 Almanac plates of 1919 Prairie draw a two-light window, a pair of
lights either side of a mullion, in each storey of the 3.1 m street face the middle range stands
out north of the front block. Held on the committed record:

  * the middle range's front carries one WING_MULLIONED opening in each storey at s 1.6 m, its
    width the kit variant's two 0.8 m lights and 0.2 m mullion, and no other wall's lights move;
  * the wall is cut one hole to a light, so its brick stands between them, and a stone mullion
    from sill to head and a stone lintel over the group stand proud of that face;
  * T-3354 (fourth run): the middle range's north face (K01's `south` wall) carries one
    WING_MULLIONED_TRIPLE group in each storey at s 2.2 m, three 1.1 m lights on 0.2 m mullions
    (`mullioned.triple`), the group of three the same plates draw there, cut one hole to a light;
  * refused: a mullioned side whose windows the wing does not list, or that it cuts round-headed,
    a window kit naming no grouped flat-headed variant for it, lights out of the ordinary width,
    and keys it does not take.

    python3 tools/test_k01_wing_mullions.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "marshall_field_jr_house_1919_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def committed():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


def refused(edit, why, says):
    st, _ = committed()
    st = copy.deepcopy(st)
    phase = st["phases"][-1]
    edit(phase["form"])
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:100]}...)")
        return
    check(False, f"{why}: refused")


st, phase = committed()
p = KP.from_phase(phase, st)
mid = next(w for w in p.rear_wings if w["id"] == "middle_range")
front = [o for o in mid["openings"] if o.wall == "k01.wall.wing.middle_range.front"]
check(len(front) == 2 and all(o.component == KP.WING_MULLIONED for o in front),
      f"the middle range's street face carries one mullioned group in each storey ({len(front)})")
check(all(abs(o.s_m - 1.6) < 1e-9 and abs(o.width_m - 1.8) < 1e-9 for o in front),
      "each stands at s 1.6 m, two 0.8 m lights and a 0.2 m mullion across")
others = [o for w in p.rear_wings for o in w["openings"] if o.wall != "k01.wall.wing.middle_range.front"]
north = [o for o in mid["openings"] if o.wall == "k01.wall.wing.middle_range.south"]
check(len(north) == 2 and all(o.component == KP.WING_MULLIONED_TRIPLE for o in north),
      f"the middle range's north face carries one three-light group in each storey ({len(north)})")
check(all(abs(o.s_m - 2.2) < 1e-9 and abs(o.width_m - 3.7) < 1e-9 for o in north),
      "each stands at s 2.2 m, three 1.1 m lights and two 0.2 m mullions across")
others = [o for o in others if o.wall != "k01.wall.wing.middle_range.south"]
check(all(o.component not in KP.WING_GROUPED for o in others), "no other wing wall's lights are grouped")
check(p.window_kit[KP.WING_MULLIONED_TRIPLE]["variant"] == "k06.opening.sash_triple_flat",
      "the three-light group is the kit's triple flat sash")
check(p.window_kit[KP.WING_MULLIONED]["variant"] == "k06.opening.sash_paired_flat",
      "the group is the kit's paired flat sash")

a = K1.build(p, SID)
check(len(a.components.get(KP.WING_MULLIONED, {"instances": []})["instances"]) == 2,
      "both groups register their K06 opening")
holes = [h for o in front for h in a.group_holes(o)]
check(len(holes) == 4 and all(abs((h[1] - h[0]) - 0.8) < 1e-9 for h in holes),
      "the wall is cut one 0.8 m hole to each light")
check(all(abs(holes[i + 1][0] - holes[i][1] - 0.2) < 1e-9 for i in (0, 2)),
      "the brick stands 0.2 m between each group's two holes")
nholes = [h for o in north for h in a.group_holes(o)]
check(len(nholes) == 6 and all(abs((h[1] - h[0]) - 1.1) < 1e-9 for h in nholes),
      "the north face is cut one 1.1 m hole to each of the six lights")
check(all(abs(nholes[i + 1][0] - nholes[i][1] - 0.2) < 1e-9 for i in (0, 1, 3, 4)),
      "the brick stands 0.2 m between each three-light group's holes")
check(len(a.components.get(KP.WING_MULLIONED_TRIPLE, {"instances": []})["instances"]) == 2,
      "both three-light groups register their K06 opening")
# the front's frame: O = (u1, 0, -v0), along -Z, so a point s along it is at z = -v0 - s, out at +X
v0, u1 = mid["rect"][2], mid["rect"][1]
stone = a.prims["limestone_trim"].pos
for o in front:
    zc = -v0 - o.s_m
    mull = [q for q in stone if u1 < q[0] <= u1 + KP.WING_MULLION_PROUD_M + 1e-6
            and zc - 0.1 - 1e-6 <= q[2] <= zc + 0.1 + 1e-6 and o.sill_m - 1e-6 <= q[1] <= o.head_m + 1e-6]
    check(len(mull) >= 4, f"a stone mullion stands proud up the group at {o.sill_m:.2f} m from sill to head")
    lint = [q for q in stone if u1 < q[0] <= u1 + KP.WING_MULLION_PROUD_M + 1e-6
            and abs(q[1] - (o.head_m + KP.WING_LINTEL_M)) < 1e-6
            and abs(abs(q[2] - zc) - (o.width_m / 2 + KP.WING_LINTEL_EAR_M)) < 1e-6]
    check(len(lint) >= 2, f"a stone lintel lies over the group, {KP.WING_LINTEL_EAR_M} m past each side")


# refusals
def mr(f):
    return next(w for w in f["rear_wings"]["value"] if w["id"] == "middle_range")


refused(lambda f: mr(f)["mullioned"].update(sides=["rear"]), "a mullioned side with no windows listed",
        "is one whose windows it lists")
refused(lambda f: mr(f).update(round_heads=["front"]), "a mullioned side cut round-headed",
        "is one whose windows it lists")
refused(lambda f: f["window_kit"]["value"].pop(KP.WING_MULLIONED), "no kit variant for the group",
        "grouped K06 variant")
refused(lambda f: f["window_kit"]["value"].update({KP.WING_MULLIONED: "k06.opening.sash_2over2_flat"}),
        "a single sash for the group", "grouped K06 variant")
refused(lambda f: mr(f)["mullioned"].update(light_m=1.4), "lights wider than the ordinary sash",
        "mullioned.light_m")
refused(lambda f: mr(f)["mullioned"]["triple"].update(sides=["front"]), "a side grouped both ways",
        "none of mullioned's own")
refused(lambda f: f["window_kit"]["value"].update({KP.WING_MULLIONED_TRIPLE: "k06.opening.sash_paired_flat"}),
        "a two-light variant for the three-light group", "grouped K06 variant of 3 lights")
refused(lambda f: mr(f)["mullioned"]["triple"].update(light_m=1.4), "three-light lights wider than the ordinary sash",
        "mullioned.triple.light_m")
refused(lambda f: mr(f)["mullioned"].update(head="arch"), "a key it does not take", "takes sides")

print(f"test_k01_wing_mullions: {'all passed' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
