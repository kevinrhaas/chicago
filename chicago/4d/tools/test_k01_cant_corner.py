#!/usr/bin/env python3
"""T-3186: K01 cuts a corner of the main body on a canted face, held on 1901 Prairie's record.

Both Chicagology photographs of the Ream house show its south-west corner (K01's 'north') cut
on a canted face square to the corner, its own window column on both storeys and its own
pedimented dormer, the cornice and the mansard carried round it; the south-west view's camera
reads the cut about 1.83 m back each way. So:

  * `cant_corner` cuts the street front and the side wall back to the face, from grade to the
    wall head, and lays the face as a wall of its own (`k01.wall.cant`) in the front's stone,
    a window at its middle in every storey and a basement light under them;
  * the mansard's rings, the wall head under them, the moulded cornice, the eave gutter and
    the curb's cresting are all cut on the face's line, so nothing stands past it;
  * a dormer may stand on the face (`face: "cant"`), centred and clear of its hips;
  * every refusal round it says why.

    python3 tools/test_k01_cant_corner.py
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "ream_house_1901_prairie"
failures = []


def check(ok, what):
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok:
        failures.append(what)


def refused(rec, why, needle):
    try:
        KP.from_phase(rec["phases"][0], rec)
    except KP.ParamError as e:
        check(needle in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (it was accepted)")


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(st["phases"][0], st)
cc = p.cant_corner
check(cc.get("corner") == "north" and cc.get("cut_m") == 1.83 and abs(cc.get("face_m", 0) - 1.83 * math.sqrt(2)) < 1e-3,
      f"1901's record cuts K01's north corner 1.83 m each way, its face {cc.get('face_m')} m across")
ops = [o for o in p.openings if o.wall == KP.CANT_WALL]
check(sorted(o.component for o in ops) == ["k01.opening.area_light", "k01.opening.sash_flat", "k01.opening.sash_flat"]
      and all(abs(o.s_m - cc["face_m"] / 2) < 1e-3 for o in ops),
      "the face carries a window in each storey and a basement light, all at its middle")

a = K1.build(p, SID)
wall = a.components.get(KP.CANT_WALL)
check(wall is not None and len(wall["instances"]) == 1 and wall["instances"][0]["params"].get("fabric") == "limestone_bedford",
      "the build lays one k01.wall.cant in the front's stone")

# nothing stands past the face's line: walls, cornice, roof, gutter and cresting all keep inside
# it by at most the eave's reach (the overhang, the gutter and its brackets)
plan = KP.cant_corner_plan(cc, p.depth_m, p.width_m)
(u0, v0), _ = plan["ends"]
nu, nv = plan["normal"]
k = nu * u0 + nv * v0
past = lambda q: nu * q[0] + nv * -q[2] - k   # how far out of the face's plane, in plan
# (over 3 m, clear of the yard, the fence on the street line and the stoop, which stand forward)
reach = {name: max((past(q) for q in pr.pos if q[1] > 3.0), default=-9.0) for name, pr in a.prims.items()}
wall_mats = ("rough_stone_trim", "limestone_trim")
walls = max((past(q) for m_ in wall_mats for q in a.prims[m_].pos if 0.05 < q[1] < a.soffit_m), default=-9.0)
check(walls < 0.35, f"the walls' stone stands no more than a sill's or a head's reach past the face ({walls:.3f} m)")
eave = p.eave_overhang_m + 0.2
worst = max(reach.values())
check(worst < eave, f"nothing stands past the face by more than the eave and its gutter ({worst:.3f} m < {eave:.2f} m)")
check(any(c["side"] == "cant" for c in a.deck["cresting"]), "the curb's cresting runs along the canted face too")
check(a.wall_head.get("cornice") == "k10.cornice.moulded_stone" and len(a.wall_head["stretches"]) >= 1,
      "the moulded cornice still runs round the walls the record names")
cant_dormers = [g for g in a.round_dormers if g["d"]["face"] == "cant"]
check(len(cant_dormers) == 1 and abs(past(cant_dormers[0]["sill_pt"]) - (p.eave_overhang_m - 0.05)) < 0.01,
      "the cant dormer's face stands on the canted face's lower slope, its setback in from the fascia")

# the house without its cut: the front and the side wall meet square, and the square corner's
# stone stands where the cut took it
plain = copy.deepcopy(st)
form = plain["phases"][0]["form"]
del form["cant_corner"]
form["mansard"]["value"]["dormers"] = [d for d in form["mansard"]["value"]["dormers"] if d["face"] != "cant"]
q = KP.from_phase(plain["phases"][0], plain)
b = K1.build(q, SID)
check(KP.CANT_WALL not in b.components and max(past(x) for x in b.prims["rough_stone_trim"].pos) > 1.0,
      "without cant_corner the corner stands square")

# refusals
def variant(edit):
    r = copy.deepcopy(st)
    edit(r["phases"][0]["form"])
    return r


refused(variant(lambda f: f["cant_corner"]["value"].update(cut_m=3.0)), "a cut past 2.5 m", "cut_m 3.0")
refused(variant(lambda f: f["cant_corner"]["value"].update(radius_m=1.0)), "a stray key", "takes corner")
refused(variant(lambda f: f["north_bays"].update(value=[2.4, 5.6])), "a flank window within the pier of the cut",
        "within 0.2 m of the cut")
refused(variant(lambda f: f["construction"].update(value="brick_with_stone_front")),
        "a brick house's flanks", "all-stone house")
refused(variant(lambda f: f["mansard"]["value"]["dormers"][-1].update(along_m=0.4)),
        "a cant dormer off the face's middle", "centred")
refused(variant(lambda f: (f["mansard"]["value"]["dormers"][-1].update(surround_m=0.4),
                           f["mansard"]["value"]["dormers"][-1]["sash"].update(width_m=1.2))),
        "a cant dormer too wide for the face's hips", "leaves the canted face's hips")

print()
if failures:
    print(f"FAIL — {len(failures)} check(s)")
    sys.exit(1)
print("OK — K01's canted corner holds on 1901 Prairie")
