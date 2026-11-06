#!/usr/bin/env python3
"""T-3354: a flank gable standing back from a flat end, and pinnacled dormers on a wing's street slope.

All three Gatlin Institute plates of 1919 Prairie stand the middle range's north-west corner
flat-topped with its gable rising behind it, and draw two small pinnacled dormers on the rear
range's slope facing the avenue. Held on the committed record:

  * the middle range's gable stands `flat_end.depth_m` back from its north end (K01's south):
    its coping's apex stands in that plane, and the flat end registers its deck at the wall top;
  * each rear-range dormer registers its body, its coping, two pinnacles and a finial, its face
    stands `setback_m` in from the range's wall line, its apex under the range's ridge, and
    limestone rises past each dormer's apex by its finial;
  * refused: a flat end on a hip or a gable to the rear, one too deep or too shallow; a dormer
    on a hip, out of its bounds, past the gabled span, over the ridge, crowding another, or
    with a light that does not fit its face.

    python3 tools/test_k01_wing_dormers.py
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
inst = a.components
mid = next(w for w in p.rear_wings if w["id"] == "middle_range")
rear = next(w for w in p.rear_wings if w["id"] == "rear_range")

# the middle range's flat end and its set-back gable
fe = mid["roof"].get("flat_end")
check(fe == {"end": "south", "depth_m": 1.6}, f"the middle range stands its gable back from its north end ({fe})")
gv0, gv1 = KP.wing_gable_span(mid)
check(abs(gv0 - (mid["rect"][2] + 1.6)) < 1e-9 and gv1 == mid["rect"][3], f"its gable spans v {gv0}..{gv1}")
cop = inst.get("k01.roof.wing_coping.middle_range.south")
check(cop is not None and abs(cop["instances"][0]["sockets"]["apex"][2] - (-gv0)) < 1e-3,
      "its north gable's coping stands in the set-back plane")
deck = inst.get("k01.roof.wing_flat_end.middle_range")
check(deck is not None and len(deck["instances"]) == 1, "its flat end registers its deck")
if deck:
    base, top = deck["instances"][0]["sockets"]["base"], deck["instances"][0]["sockets"]["top"]
    check(abs(base[1] - mid["top_m"]) < 1e-6 and abs(top[1] - mid["top_m"] - mid["fascia_m"]) < 1e-6,
          f"the deck lies at the wall top ({base[1]:.2f}-{top[1]:.2f} m)")
    check(abs(base[0] - mid["rect"][0]) < 1e-6, "no overhang over its rear, where the rear range stands on it")
    check(abs(top[0] - (mid["rect"][1] + mid["overhang_m"])) < 1e-6, "its overhang runs out over its front, past the host")

# the rear range's dormers
ds = rear["roof"].get("dormers") or ()
check(len(ds) == 2 and [d["v_m"] for d in ds] == [-3.85, -2.3], f"the rear range carries the plates' two dormers")
t = math.tan(math.radians(rear["roof"]["pitch_deg"]))
stone = a.prims["limestone_trim"].pos
for i, d in enumerate(ds):
    body = inst.get(f"k01.roof.wing_dormer.rear_range.{i}")
    check(body is not None and len(body["instances"]) == 1, f"dormer {i} registers its body")
    if not body:
        continue
    foot, apex = body["instances"][0]["sockets"]["foot"], body["instances"][0]["sockets"]["apex"]
    uf = rear["rect"][1] - d["setback_m"]
    check(abs(foot[0] - uf) < 1e-6 and abs(foot[1] - (rear["top_m"] + d["setback_m"] * t)) < 1e-3,
          f"dormer {i}'s face stands {d['setback_m']} m in from the wall line, on the slope")
    check(apex[1] < rear["roof"]["ridge_m"], f"dormer {i}'s apex ({apex[1]:.2f} m) stands under the ridge")
    check(any(abs(q[0] - uf) < 0.3 and abs(q[2] + d["v_m"]) < 0.2 and q[1] > apex[1] + 0.8 * d["finial_m"]
              for q in stone), f"dormer {i}'s finial rises past its apex")
pins = [x for x in inst.get("k01.roof.gable_pinnacle", {"instances": []})["instances"] if x["params"].get("wing")]
check(len(pins) == 4, f"a pinnacle at each edge of each dormer ({len(pins)})")
cops = [x for x in inst.get("k01.roof.dormer_coping", {"instances": []})["instances"] if x["params"].get("wing")]
check(len(cops) == 2, f"each dormer's rakes coped ({len(cops)})")


# refusals
def wings(f):
    return {w["id"]: w for w in f["rear_wings"]["value"]}


def dormer(f, i=0):
    return wings(f)["rear_range"]["roof"]["dormers"][i]


refused(lambda f: wings(f)["middle_range"]["roof"].update(flat_end={"end": "south", "depth_m": 0.2}),
        "a flat end too shallow", "flat_end")
refused(lambda f: wings(f)["middle_range"]["roof"].update(flat_end={"end": "south", "depth_m": 13.0}),
        "a flat end leaving too little gabled", "flat_end")
refused(lambda f: wings(f)["middle_range"]["roof"].update(flat_end={"end": "rear", "depth_m": 1.6}),
        "a flat end on no gable end", "flat_end takes")
refused(lambda f: wings(f)["middle_range"]["roof"].update(gable_to="rear", coping=None) or
        wings(f)["middle_range"]["roof"].pop("coping"), "a flat end on a gable to the rear", "gable facing a flank")
refused(lambda f: dormer(f).update(width_m=2.5), "a dormer out of its bounds", "0.6-1.6 m wide")
refused(lambda f: dormer(f).update(v_m=-4.6), "a dormer past the gabled span", "inside the gabled slope")
refused(lambda f: wings(f)["middle_range"]["roof"].update(
            dormers=[dict(dormer(f), v_m=-2.0)]), "a dormer over a flat end's deck", "inside the gabled slope")
refused(lambda f: dormer(f).update(eave_m=15.0), "a dormer over the ridge", "ridge")
refused(lambda f: dormer(f).update(eave_m=10.5), "a dormer's eave under 1 m over the slope", "1 m over the slope")
refused(lambda f: dormer(f, 1).update(v_m=-3.3), "two dormers crowding", "within 0.3 m of dormers[0]")
refused(lambda f: dormer(f)["light"].update(width_m=0.9), "a light wider than its face allows", ".light")
refused(lambda f: dormer(f).pop("finial_m"), "a dormer missing a key", "takes")

print(f"test_k01_wing_dormers: {'all passed' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
