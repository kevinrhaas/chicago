#!/usr/bin/env python3
"""T-1890: a K01 wing's hip may pitch its ends steeper than its sides, and a wing may carry
stacks of its own.

HABS photograph 2 (1965) of 1801 Prairie shows the east range's slate rising steeply from its
18th Street eave to an apex about 2.7 m back from that wall (the range's 45-degree sides would
put it 4.7 m back), and a pale stone stack under a moulded cap standing on that apex. This holds
the kit and the record to it:

  * `rear_wings[].roof.end_pitch_deg` names a hip's south (v0) and/or north (v1) end and pitches
    it from the sides' pitch to 60 degrees; the ridge keeps its height and only its ends move.
    It is refused on a gable, on a hip whose ridge runs across the wing, under the sides' pitch,
    over 60, for an end it does not know, and where the ends would meet with no ridge;
  * `rear_wings[].stacks` stand inside the wing's wall line on a pitched roof, their caps clear
    of the covering under them with at least 0.3 m of shaft on the low side; a stone stack is
    built in the walls' stone, its cap in the trim's;
  * a wing without either builds exactly as before;
  * 1801's r2: its south end at 60 degrees, one stone stack 0.8 m square at u -13.45, v 2.6,
    its top at 11.4 m.

    python3 tools/test_k01_wing_stack.py
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

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][0]


def r2_of(phase):
    return next(w for w in phase["form"]["rear_wings"]["value"] if w["id"] == "r2")


def wing(params, wid="r2"):
    return next(w for w in params.rear_wings if w["id"] == wid)


def instance(asm, wid="r2"):
    inst = asm.components.get(f"k01.roof.wing.{wid}", {}).get("instances", [])
    return inst[0] if inst else None


def tris(asm, mat):
    return len(asm.prims[mat].idx) // 3 if mat in asm.prims else 0


st, ph = record()
r2 = r2_of(ph)
check(r2["roof"].get("end_pitch_deg") == {"south": 60}, f"r2's 18th Street end is pitched 60 deg ({r2['roof'].get('end_pitch_deg')})")
check(r2.get("stacks") == [{"u_m": -13.45, "v_m": 2.6, "plan_m": [0.8, 0.8], "top_m": 11.4, "cap_proud_m": 0.1,
                            "cap_depth_m": 0.45, "fabric": "stone"}],
      "r2 carries HABS 2's stone stack: 0.8 m square at u -13.45, v 2.6, its top at 11.4 m")

# -- the resolved wing: the ridge unchanged, the covering over the plan ------------------------
p = KP.from_phase(ph, st)
w = wing(p)
check(w["roof"]["end_pitch_deg"] == {"south": 60.0} and abs(w["roof"]["ridge_m"] - 11.05) < 1e-6,
      f"the ridge keeps its 11.05 m; only the south end steepens ({w['roof']['ridge_m']})")
apex_v = (9.4 / 2) / math.tan(math.radians(60))           # at the wall line, the overhang aside
check(abs(KP.wing_cover_m(w, -13.2, apex_v) - 11.05) < 1e-6
      and abs(KP.wing_cover_m(w, -13.2, apex_v - 1.0) - (11.05 - math.tan(math.radians(60)))) < 1e-6,
      f"the south end rises at 60 deg to the apex {apex_v:.2f} m back from the wall")
check(abs(KP.wing_cover_m(w, -13.2, 18.3 - 2.0) - (11.05 - 2.7)) < 1e-6,
      "the north end keeps the sides' 45 deg")
s = w["stacks"][0]
check(s["stone"] and s["top_m"] == 11.4 and s["base_m"] == round(w["top_m"] - 0.3, 4),
      f"the stack is stone, tops at 11.4 m and rises from inside the roof at {s['base_m']} m")

# -- the build: the wing roof's instance and the stack's stone ---------------------------------
a = K1.build(p, SID)
inst = instance(a)
check(inst is not None and inst["params"].get("end_pitch_deg") == {"south": 60.0} and inst["params"].get("stacks") == 1,
      f"r2's roof instance records its end pitch and its stack ({inst and {k: inst['params'].get(k) for k in ('end_pitch_deg', 'stacks')}})")

ph0 = copy.deepcopy(ph)
del r2_of(ph0)["roof"]["end_pitch_deg"]
del r2_of(ph0)["stacks"]
p0 = KP.from_phase(ph0, st)
a0 = K1.build(p0, SID)
i0 = instance(a0)
check(i0 is not None and "end_pitch_deg" not in i0["params"] and "stacks" not in i0["params"]
      and "stacks" not in wing(p0) and "end_pitch_deg" not in wing(p0)["roof"],
      "a wing without either resolves and records exactly as before")
check(tris(a, "rough_stone_trim") > tris(a0, "rough_stone_trim") and tris(a, "limestone_trim") > tris(a0, "limestone_trim"),
      f"the stack's shaft is laid in the walls' stone and its cap in the trim "
      f"(+{tris(a, 'rough_stone_trim') - tris(a0, 'rough_stone_trim')} / +{tris(a, 'limestone_trim') - tris(a0, 'limestone_trim')} triangles)")
k5 = __import__("archetypes.k05_roofs", fromlist=["x"])
hip_old, _ = k5.hip_element(-17.9, -8.5, -18.3, 0.0, 6.35, 1.0, 0.05, 0.3)
hip_eq, _ = K1.Assembly.wing_hip_ends(k5, {"pitch_deg": 45.0, "end_pitch_deg": {"south": 45.0}},
                                      -17.9, -8.5, -18.3, 0.0, 6.35, 1.0, 0.05, 0.3)
def rounded(x):
    if hasattr(x, "v") and hasattr(x, "role"):   # a K05 Poly: its role and its vertices
        return (x.role, rounded(x.v))
    if isinstance(x, float):
        return round(x, 6) + 0.0
    if isinstance(x, (list, tuple)):
        return tuple(rounded(y) for y in x)
    if isinstance(x, dict):
        return tuple(sorted((k, rounded(v)) for k, v in x.items()))
    return x


check(hip_eq is not None and sorted(map(repr, map(rounded, hip_eq))) == sorted(map(repr, map(rounded, hip_old))),
      "an end pitched at the sides' own pitch builds K05's hip exactly")


# -- refusals --------------------------------------------------------------------------------
def refused(mutate, why, key):
    phb = copy.deepcopy(ph)
    mutate(r2_of(phb))
    try:
        KP.from_phase(phb, st)
        check(False, f"{why} is refused")
    except (KP.ParamError, ValueError) as e:
        check(key in str(e), f"{why} is refused ({str(e)[:100]})")


refused(lambda r: r["roof"].update(end_pitch_deg={"south": 40}), "an end under the sides' pitch", "end_pitch_deg")
refused(lambda r: r["roof"].update(end_pitch_deg={"south": 65}), "an end over 60 deg", "end_pitch_deg")
refused(lambda r: r["roof"].update(end_pitch_deg={"east": 55}), "an end it does not know", "end_pitch_deg")
refused(lambda r: r["roof"].update(kind="gable", gable_to="north", end_pitch_deg={"south": 55}), "an end pitch on a gable",
        "end_pitch_deg")
refused(lambda r: r["stacks"][0].update(u_m=-8.6), "a stack past the wall line", "inside the wing's wall line")
refused(lambda r: r["stacks"][0].update(top_m=10.6), "a stack whose cap does not clear the slate", "does not clear")
refused(lambda r: r["stacks"][0].update(colour="red"), "a stack with an unknown key", "stack takes")
refused(lambda r: r["stacks"][0].update(plan_m=[0.3, 0.8]), "a stack under 0.5 m across", "plan is 0.5-2.0")
refused(lambda r: r["stacks"][0].update(fabric="timber"), "a stack in an unknown fabric", "fabric")

print(f"\n{'FAIL' if failures else 'PASS'} — wing end pitch and stacks: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
