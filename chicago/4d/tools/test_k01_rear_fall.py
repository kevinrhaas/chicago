#!/usr/bin/env python3
"""T-3063: a K01 gable roof's rear slope may fall steeply to a flat deck under a level coping.

1811 Prairie's south wall behind its tall stack: the 1888 plate and the Chicagology print both
draw its coping LEVEL at about 10.95 m back to the front block's rear wall, with no roof over
it, where K01's coped parapet followed the rear slope down to the rear eave. The record names
`gable_roof.rear_fall` (wall_head_m, pitch_deg, head_back_m); this holds the kit to it:

  * resolved: the deck stands a coping and K05's upstand under the wall head, and the fall
    meets it where the fall's pitch from the ridge puts it;
  * the line: level at the wall head's slab from the rear wall to the fall's foot, the head
    `head_back_m` behind the ridge, and every point clearing the covering under it by the
    upstand; the 1811 build carries that line;
  * as-was: without rear_fall the coped line is T-2459's, point for point;
  * refused: a rear fall over stepped ends, a fall shallower than the plain rear slope + 15
    or steeper than 75 degrees, a deck over the ridge, a head run out of range.

    python3 tools/test_k01_rear_fall.py
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
from archetypes import k01_gable_roof as KG  # noqa: E402

SID = "coleman_ames_house_1811_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    return json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def params(st):
    ph = next(p for p in st["phases"] if "form" in p)
    return KP.from_phase(ph, st)


def refused(change, what):
    st = record()
    change(st["phases"][0]["form"]["gable_roof"]["value"])
    try:
        params(st)
    except KP.ParamError as e:
        check(True, f"refused: {what} ({str(e)[:90]})")
        return
    check(False, f"refused: {what}")


p = params(record())
g, rf = p.gable, p.gable["rear_fall"]
up, cop = g["upstand_m"], g["coping_m"]
check(abs(rf["deck_m"] - (rf["wall_head_m"] - cop - up)) < 1e-6,
      f"the deck {rf['deck_m']} m stands a coping and the upstand under the {rf['wall_head_m']} m wall head")
xr = p.depth_m - g["ridge_back_m"]
run = (g["ridge_m"] - rf["deck_m"]) / math.tan(math.radians(rf["pitch_deg"]))
check(abs(rf["deck_from_m"] - (xr - run)) < 1e-3,
      f"the fall meets the deck {rf['deck_from_m']} m from the rear wall, {run:.2f} m behind the ridge")

tf = math.tan(math.radians(p.roof_pitch_deg))
top = g["ridge_m"] + g["top_above_ridge_m"]
E = g["ridge_m"] - g["ridge_back_m"] * tf
ln = KG.line("coped", 0, p.depth_m, xr, E, tf, math.tan(math.radians(g["back_pitch_deg"])), up, top, fall=rf)
y0 = rf["deck_m"] + up
check(ln[0] == (0.0, y0) and ln[1] == (rf["deck_from_m"], y0),
      f"the line runs level at {y0:.3f} m (the coping's top {y0 + cop:.2f}) to the fall's foot")
check(abs(ln[2][0] - (xr - rf["head_back_m"])) < 1e-9 and ln[2][1] == top,
      f"its head starts {rf['head_back_m']} m behind the ridge at {top:.3f} m")


def covering(x):
    """The attic's top over u x: the street slope, the fall and the deck."""
    if x >= xr:
        return E + (p.depth_m - x) * tf
    return max(rf["deck_m"], g["ridge_m"] - (xr - x) * math.tan(math.radians(rf["pitch_deg"])))


def at(x):
    for (a, ya), (b, yb) in zip(ln, ln[1:]):
        if a - 1e-9 <= x <= b + 1e-9:
            return ya if b == a else ya + (yb - ya) * (x - a) / (b - a)
    return None


worst = min(at(x) - covering(x) for x in [i * p.depth_m / 400 for i in range(401)])
check(worst >= up - 1e-6, f"every point of the line clears the covering by the {up} m upstand (least {worst:.3f})")

a = K1.build(p, SID)
built = a.gable_roof["parapet_lines"]["north"]
check(built[0] == [0.0, round(y0, 4)] and built[1][1] == round(y0, 4),
      f"1811's south parapet is built level at {y0:.3f} m from its rear wall")

old = KG.line("coped", 0, 7.57, 6.17, 9.14, tf, 0.41, 0.3, 11.99)
check(old == [(0.0, 9.14 + 0.3), (6.17 - KG.TOP_HALF_M, 11.99), (6.17 + KG.TOP_HALF_M, 11.99), (7.57, 9.14 + 0.3)],
      "without a rear fall the coped line is T-2459's, point for point")

refused(lambda v: v["ends"]["north"].update({"style": "stepped", "steps": 3}), "a rear fall over stepped ends")
refused(lambda v: v["rear_fall"].update({"pitch_deg": 30.0}), "a fall under the plain rear slope + 15 degrees")
refused(lambda v: v["rear_fall"].update({"pitch_deg": 80.0}), "a fall steeper than 75 degrees")
refused(lambda v: v["rear_fall"].update({"wall_head_m": 12.5}), "a deck over the ridge")
refused(lambda v: v["rear_fall"].update({"head_back_m": 0.6}), "a head run past K01's coped head")

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
