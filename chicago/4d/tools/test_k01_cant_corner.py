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


refused(variant(lambda f: f["cant_corner"]["value"].update(cut_m=3.6)), "a cut past 3.5 m", "cut_m 3.6")
refused(variant(lambda f: f["cant_corner"]["value"].update(blank=False)), "blank other than true", "blank: true")
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

# T-3261: 1905 Prairie's south-west corner (K01's 'north'), the 1893 plate's: a brick house's
# canted face, blank in both storeys, under the bracketed timber cornice carried round it, its
# largest dormer standing on it
SID5 = "marshall_field_house_1905_prairie"
st5 = json.loads((ROOT / "data" / "structures" / f"{SID5}.json").read_text())
p5 = KP.from_phase(st5["phases"][0], st5)
cc5 = p5.cant_corner
# T-3271: Hunt's plan of the principal floor and the 923 photograph's camera re-read the cut to
# 2.15 m each way (it was 3.2 m, the 1893 plate's camera's reading with its heights held)
check(cc5.get("corner") == "north" and cc5.get("cut_m") == 2.15 and cc5.get("blank") is True,
      f"1905's record cuts K01's north corner 2.15 m each way, the face blank ({cc5})")
check(not [o for o in p5.openings if o.wall == KP.CANT_WALL], "1905's canted face carries no window column")
a5 = K1.build(p5, SID5)
w5 = a5.components.get(KP.CANT_WALL)
face5 = KP.cant_corner_plan(cc5, p5.depth_m, p5.width_m)
(fu, fv), _ = face5["ends"]
belt5 = p5.floors_m[1]   # the stone belt at the chamber floor (6.1 m since T-3271's lower walls)
on_face = lambda q: (abs(face5["normal"][0] * (q[0] - fu) + face5["normal"][1] * (-q[2] - fv)) < 0.01
                     and 3.0 < q[1] < belt5 - 0.3
                     and -q[2] > fv + 0.3 and q[0] < fu - 0.3)   # inside the face, clear of its two ends and the belt
check(w5 is not None and len(w5["instances"]) == 1 and any(on_face(q) for q in a5.prims["brick"].pos)
      and not any(on_face(q) for q in a5.prims["limestone_trim"].pos),
      "the build lays 1905's k01.wall.cant in its brick, blank between the belts")
br = a5.wall_head["bracket_runs"]
check(len(br.get(KP.CANT_WALL, ())) >= 2, f"the timber cornice's pairs turn onto the canted face ({br.get(KP.CANT_WALL)})")
check(max(br["k01.wall.street_front"]) < face5["walls"]["k01.wall.street_front"][0]
      and min(br["k01.wall.side.north"]) > face5["walls"]["k01.wall.side.north"][1],
      "and stop on the front and the flank where the cut begins, in each wall's own s")
check([d["face"] for d in p5.mansard["dormers"]].count("cant") == 1, "1905's large dormer stands on the canted face")
plan5 = face5
(u5, v5), _ = plan5["ends"]
n5u, n5v = plan5["normal"]
k5 = n5u * u5 + n5v * v5
past5 = lambda q: n5u * q[0] + n5v * -q[2] - k5
reach5 = max((past5(q) for pr in a5.prims.values() for q in pr.pos if q[1] > 3.0), default=-9.0)
check(reach5 < p5.eave_overhang_m + 0.25, f"nothing over 3 m stands past the face by more than the eave's reach ({reach5:.3f} m)")


def variant5(edit):
    r = copy.deepcopy(st5)
    edit(r["phases"][0]["form"])
    return r


def refused5(rec, why, needle):
    refused(rec, why, needle)


cut_s5 = face5["walls"]["k01.wall.street_front"][0]   # where the front's cut begins (14.65 m)
refused5(variant5(lambda f: f["street_front_iron"]["value"]["balconettes"][-1].update(to_s_m=round(cut_s5 + 0.15, 2))),
         "a balcony run onto the cut", "runs onto the cut")
refused5(variant5(lambda f: f["wall_head"]["value"].update(walls=["k01.wall.street_front"])),
         "a timber cornice on named walls", "bracketed timber")

print()
if failures:
    print(f"FAIL — {len(failures)} check(s)")
    sys.exit(1)
print("OK — K01's canted corner holds on 1901 Prairie and 1905 Prairie")
