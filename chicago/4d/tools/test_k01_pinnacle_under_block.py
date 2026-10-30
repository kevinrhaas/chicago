#!/usr/bin/env python3
"""T-3064: a wall gable's pinnacle shaft may stop under its block, held on 1811 Prairie.

The 1888 Inland Architect plate stops 1811's north pinnacle at a band level with the bay
gable's horizontal cornice (about y 342 px, 10.6 m) and lays a scaled stone over it, leaning
in to the moulded block's plinth (about y 320 px); K01 had carried every engaged shaft past
the face's eave (11.09 m). So:

  * a head with a `block` may set its `top_m` at or below the face's eave, its spire rising
    to the block's foot; its stone is a skewed cap from the shaft's cap to the block's
    plinth, laid in courses of scales (`scaled_pyramid`) or plain (`pyramid`);
  * the eave's end, where it leaves the face's edge, must die into that stone;
  * a head that stops low with no block, with a dome, or with its spire short of the block
    is refused, and every refusal says why.

    python3 tools/test_k01_pinnacle_under_block.py
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
from archetypes import k01_wall_gable as WG  # noqa: E402

SID = "coleman_ames_house_1811_prairie"
failures = []


def check(ok, what):
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def variant(fn):
    r = copy.deepcopy(st)
    fn(r["phases"][0]["form"]["dormer"]["value"]["wall_gable"]["pinnacles"]["heads"][0])
    return r


def refused(rec, why, needle):
    try:
        KP.from_phase(rec["phases"][0], rec)
    except KP.ParamError as e:
        check(needle in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (it was accepted)")


p = KP.from_phase(st["phases"][0], st)
h = p.dormer["wall_gable"]["pinnacles"]["heads"][0]
check(h["top_m"] < p.dormer["face_height_m"] and "block" in h and h["spire"] == "scaled_pyramid",
      "1811's north shaft stops below the face's eave, under its block, under scaled stone")
a = K1.build(p, SID)
g = a.dormer_geom
pins = a.components["k01.roof.gable_pinnacle"]["instances"]
north = pins[0]["params"]
check(abs(north["top_m"] - (g["ys"] + h["top_m"])) < 1e-6 and north["top_m"] < g["yde"],
      f"the north shaft's top {north['top_m']} m stands under the face's eave {g['yde']} m")
check(abs(north["top_m"] + 0.1 - g["ys"] - h["block"]["foot_m"] + h["spire_m"]) < 0.05,
      "its stone rises from the cap to the block's foot")
# the stone's courses: SCALE_COURSES levels of limestone between the cap's top and the block's foot
z = pins[0]["sockets"]["foot"][2]
y0, y1 = north["top_m"] + 0.1, g["ys"] + h["block"]["foot_m"]
lv = {round(q[1], 4) for q in a.prims["limestone_trim"].pos if abs(q[2] - z) < 0.7 and y0 - 1e-6 <= q[1] <= y1 + 1e-6}
check(len(lv) >= WG.SCALE_COURSES + 1, f"the stone is laid in {WG.SCALE_COURSES} courses ({len(lv)} levels)")
# the south shaft is untouched: past the eave under its dome
check(pins[1]["params"]["top_m"] > g["yde"] and pins[1]["params"]["spire"] == "dome", "the south shaft keeps its dome")

# a plain stone builds too, in one course
pl = variant(lambda x: x.update(spire="pyramid"))
b = K1.build(KP.from_phase(pl["phases"][0], pl), SID)
check(b.components["k01.roof.gable_pinnacle"]["instances"][0]["params"]["spire"] == "pyramid",
      "a plain stone under the block builds")

# the eave's end must die into the stone: a block set further in leaves it out
far = variant(lambda x: x["block"].update(in_m=0.375))
try:
    K1.build(KP.from_phase(far["phases"][0], far), SID)
    check(False, "refused: a block set in so far the eave's end leaves the stone (it was built)")
except ValueError as e:
    check("eave leaves its pinnacle's stone" in str(e), f"refused: the eave's end leaving the stone ({e})")

refused(variant(lambda x: x.pop("block")), "a shaft stopping below the eave with no block", "only under a block")
refused(variant(lambda x: x.update(spire="dome")), "a dome under the block", "only under a block")
refused(variant(lambda x: x.update(spire_m=0.3)), "a stone stopping short of the block's foot", "block's foot")
refused(variant(lambda x: x.update(top_m=0.3)), "a shaft stopping within 0.5 m of the wall head", "0.5 m over")
refused(variant(lambda x: x.update(spire="cone")), "a spire K01 does not name", "scaled_pyramid")

if failures:
    print(f"test_k01_pinnacle_under_block: {len(failures)} failure(s)")
    sys.exit(1)
print("test_k01_pinnacle_under_block: all passed")
