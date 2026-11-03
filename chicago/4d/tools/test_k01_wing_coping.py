#!/usr/bin/env python3
"""T-3337: a flat-topped K08 projection on a K01 rear wing's gable end, and a wing's stone-coped gables.

1919 Prairie's rear range carries the 1911 sheet's canted north bay on its north wall, which is
the range's gable end, flat-topped under a balustrade with the gable standing back over it; and
both ranges' gables are carried up in a stone coping with kneelers and finials (both Gatlin
Institute plates). Held on the committed record:

  * the bay is laid on k01.wall.wing.rear_range.south, inside its wall, its flat top at the
    range's wall top, and the range's light behind it is dropped;
  * every coped end registers its coping, whose apex stands over the slate's apex by the
    coping's plumb depth, and limestone rises past the apex by the finial;
  * refused: a pitched projection, a tower and a projection run past its wall's end on a gable
    end; a coping on a hip, on a gable to the rear, out of its bounds, or naming no end.

    python3 tools/test_k01_wing_coping.py
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
a = K1.build(p, SID)

# the bay on the rear range's gable end
bay = next(b for b in p.bays if b["id"] == "north_bay")
rr = next(w for w in p.rear_wings if w["id"] == "rear_range")
length = KP.wing_walls(rr)["south"][2]
s0, s1 = bay["span_m"]
check(bay.get("wing") == "rear_range" and bay["wall"] == "k01.wall.wing.rear_range.south",
      "the north bay stands on the rear range's north wall (K01's south), a gable end")
check("south" in KP._gable_walls(rr["roof"]), "that wall is the range's gable end")
check(0.0 < s0 < s1 < length, f"the bay lies inside its wall (s {s0:.2f}-{s1:.2f} of {length:.2f} m)")
top = sum(x["height_m"] for x in bay["variant"]["storeys"])
check(abs(top - rr["top_m"]) < 1e-6, f"its flat top stands at the range's wall top ({top:.2f} m)")
check(float(bay["variant"]["roof"]["pitch"]) == 0.0 and bay["variant"].get("balcony"),
      "its top is flat, under its balustrade")
lights = [o for o in rr["openings"] if o.wall == "k01.wall.wing.rear_range.south"]
check(all(o.s_m + o.width_m / 2 < s0 or o.s_m - o.width_m / 2 > s1 for o in lights)
      and sorted({round(o.s_m, 2) for o in lights}) == [1.0, 8.2],
      f"the range's lights stand clear of it ({sorted({round(o.s_m, 2) for o in lights})})")

# the coped gables
inst = a.components
for w in p.rear_wings:
    cp = w["roof"].get("coping")
    if not cp:
        continue
    for end in cp["ends"]:
        cid = f"k01.roof.wing_coping.{w['id']}.{end}"
        c = inst.get(cid)
        ok = c is not None and len(c["instances"]) == 1
        check(ok, f"{w['id']}'s {end} gable registers its coping")
        if not ok:
            continue
        t = math.tan(math.radians(w["roof"]["pitch_deg"]))
        apex = c["instances"][0]["sockets"]["apex"][1]
        want = w["roof"]["ridge_m"] + cp["thickness_m"] * math.sqrt(1 + t * t)
        check(abs(apex - want) < 1e-3, f"{w['id']}'s {end} coping's apex {apex:.3f} m stands its plumb depth "
                                       f"over the ridge ({want:.3f} m)")
stone = a.prims["limestone_trim"].pos
hi = max(w["roof"]["ridge_m"] for w in p.rear_wings if w["roof"].get("coping"))
check(any(q[1] > hi + 0.5 for q in stone), "the finials rise past the highest coped apex")

# refusals
def wings(f):
    return {w["id"]: w for w in f["rear_wings"]["value"]}


def bays(f):
    return {b["id"]: b for b in f["bays"]["value"]}


refused(lambda f: bays(f)["north_bay"].update(roof={"kind": "hip", "pitch": 0.6, "covering": "slate_pennsylvania"}),
        "a pitched projection on a gable end", "a gable end")
refused(lambda f: f["bays"]["value"].append({"id": "t", "variant": "k08.tower.round", "s_m": 8.0,
                                             "wall": "k01.wall.wing.middle_range.south",
                                             "plan": {"radius_m": 1.2, "centre_proud_m": 0.5}}),
        "a tower on a gable end", "a gable end")
refused(lambda f: bays(f)["north_bay"].update(past_end="left"), "a flat projection run past a gable end's end",
        "a gable end")
refused(lambda f: wings(f)["rear_range"]["roof"]["coping"].update(thickness_m=0.5), "a coping out of its bounds",
        "a 0.1-0.3 m stone")
refused(lambda f: wings(f)["rear_range"]["roof"]["coping"].update(ends=[]), "a coping naming no end",
        "coping.ends")
refused(lambda f: wings(f)["rear_range"]["roof"]["coping"].update(ends=["rear"]), "a coping on a rear end",
        "coping.ends")
refused(lambda f: wings(f)["middle_range"]["roof"].update(kind="hip", gable_to=None) or
        wings(f)["middle_range"]["roof"].pop("gable_to"), "a coping on a hip", "gable facing a flank")
refused(lambda f: wings(f)["garage"]["roof"].update(coping={"thickness_m": 0.18}), "a coping on a flat deck",
        "gable facing a flank")

print(f"test_k01_wing_coping: {'all passed' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
