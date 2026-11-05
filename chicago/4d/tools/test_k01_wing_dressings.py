#!/usr/bin/env python3
"""T-3353: a K01 brick rear wing's stone dressings — belts in place of the brick course, and
quoins at its corners.

1919 Prairie's two rear ranges are quoined at their north-east corners and carry the main
block's three stone courses across their north walls and stepped-out faces, as the 1919
programme plate draws them pale against the brick. Held on the committed record:

  * each range registers its quoins, one instance a corner, its courses running from the
    quoins' foot to the wing's wall top, and limestone stands proud at the corner over that
    height on both faces;
  * the garage, which the plate shows no dressings on, is left undressed;
  * refused: a corner the wing does not have, a quoin through a light, a belt through a light,
    a belt on a wall the wing has not got, dressings on a frame wing, and stones out of bounds.

    python3 tools/test_k01_wing_dressings.py
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
        check(says in str(e), f"{why}: refused ({str(e)[:110]}...)")
        return
    check(False, f"{why}: refused")


st, phase = committed()
p = KP.from_phase(phase, st)
a = K1.build(p, SID)
stone = a.prims["limestone_trim"].pos

for wid in ("middle_range", "rear_range"):
    w = next(x for x in p.rear_wings if x["id"] == wid)
    dr = w.get("dressings") or {}
    q = dr.get("quoins")
    check(bool(q) and q["corners"] == ("south_front",), f"{wid} names its quoins at its north-east corner")
    check(set(dr.get("belt_sides", ())) == {"south", "front"} and len(dr.get("belts", ())) == 3,
          f"{wid} carries three stone belts on its north wall and stepped-out face")
    c = a.components.get(f"k01.wall.wing.{wid}.quoins")
    ok = c is not None and len(c["instances"]) == 1
    check(ok, f"{wid} registers one quoin instance, its corner's")
    if ok:
        prm = c["instances"][0]["params"]
        check(abs(prm["courses"] * prm["course_m"] - (w["top_m"] - q["from_m"])) < 0.01,
              f"{wid}'s {prm['courses']} courses run from {q['from_m']} m to its wall top {w['top_m']} m")
    # proud stone at the corner (u1, v0): K01's frame is +X = u, -Z = v
    u0, u1, v0, v1 = w["rect"]
    at = [s for s in stone if abs(s[0] - u1) < q["long_m"] + 0.05 and abs(-s[2] - v0) < q["long_m"] + 0.05]
    ys = sorted(s[1] for s in at)
    check(bool(ys) and ys[0] <= q["from_m"] + 0.01 and ys[-1] >= w["top_m"] - 0.01,
          f"{wid}'s corner stands in limestone from {ys[0] if ys else '-'} to {ys[-1] if ys else '-'} m")
    proud = [s for s in at if -s[2] < v0 - q["proud_m"] + 1e-6] + [s for s in at if s[0] > u1 + q["proud_m"] - 1e-6]
    check(len(proud) > 0, f"{wid}'s quoins stand proud of both faces at the corner")

garage = next(x for x in p.rear_wings if x["id"] == "garage")
check("dressings" not in garage, "the garage is undressed")

def wings(f):
    return {w["id"]: w for w in f["rear_wings"]["value"]}


def dress(f):
    return wings(f)["middle_range"]["dressings"]


# T-3354: the garage runs past the rear range's north pile now, so it has a front; the south pile has none
refused(lambda f: wings(f)["rear_range_south"].update(
            dressings={"quoins": dict(dress(f)["quoins"], corners=["south_front"])}),
        "a corner on a wall the wing has not got (the rear range's south pile has no stepped-out face)",
        "has no south_front corner")
refused(lambda f: dress(f)["quoins"].update(corners=["south_rear", "south_rear"]), "a corner named twice",
        "once each")
refused(lambda f: dress(f)["quoins"].update(long_m=1.6), "a quoin out of bounds", "short < long")
refused(lambda f: wings(f)["rear_range"]["dressings"]["quoins"].update(long_m=0.9),
        "a quoin through the rear range's light at s 8.2", "through the light at s 8.2")
refused(lambda f: dress(f).update(belts=[{"from_m": 3.0, "to_m": 3.2, "proud_m": 0.05}]),
        "a belt through the lights", "runs through the light")
refused(lambda f: dress(f).update(belt_sides=["south", "nowhere"]), "a belt on a wall the wing has not got",
        "name the walls")
refused(lambda f: dress(f).update(colour="red"), "an unknown dressing", "dressings take")
refused(lambda f: wings(f)["middle_range"].update(fabric="frame"), "dressings on a frame wing",
        "brick wing")

print(f"test_k01_wing_dressings: {'all passed' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
