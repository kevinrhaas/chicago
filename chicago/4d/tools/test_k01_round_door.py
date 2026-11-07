#!/usr/bin/env python3
"""T-3283: a brick front's principal door may be cut round-headed (`street_front_round_heads.door`).

The Chicago Tribune's 'Famous Homes' photograph of 29 July 1928 shows 1945 Prairie's door under a
round arch in its brick front, beside the corner block's round-headed lights. A stone front lays
such a door's voussoirs in its courses (`entrance_kit.arch`); a brick front had no way to, so the
door stood square-headed under a flat lintel. This holds the kit and the record to it:

  * `street_front_round_heads.door: true` cuts the door's hole round on the round lights' curve
    (spring a half span under the crown) and asks K07 for a round-headed entrance;
  * the door is dressed with K06's arch band for the front's round-headed light and the round
    heads' key on its crown, and no flat lintel;
  * `entrance_kit.opening_m` may size that hole, as it does an arched stone door's;
  * refused: on a stone front, beside `entrance_kit.arch`, with no key, on a segmental head,
    as anything but true, and with a flat-headed K07 variant;
  * without it, a brick front's door is still a rectangular hole (1945's record minus the key).

    python3 tools/test_k01_round_door.py
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

SID = "armour_corwith_house_1945_prairie"
DOOR = "k01.opening.door_leaf"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def refused(phase, what):
    try:
        KP.from_phase(phase, st)
    except (KP.ParamError, ValueError):
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what}")


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]
form = ph["form"]

check(form["street_front_round_heads"]["value"].get("door") is True,
      "1945's record cuts its door round-headed (the 1928 photograph)")
check(form["entrance_kit"]["value"][DOOR]["variant"] == "k07.entrance.double_door_deep_arch",
      "1945's door is K07's round-headed double door")

p = KP.from_phase(ph, st)
door = next(o for o in p.openings if o.component == DOOR)
check(door.round_head, "the door opening is marked round-headed")
check((door.width_m, door.height_m) == (1.3, 3.4), "entrance_kit.opening_m sizes the hole: 1.3 by 3.4 m")
h = K1.hole(door)
check(len(h) == 5 and abs(h[3] - (door.head_m - door.width_m / 2)) < 1e-9,
      "its hole is cut round, springing a half span under the crown")
check(max(q[1] for q in h[4]) <= door.head_m + 1e-9 and max(q[1] for q in h[4]) > door.head_m - 0.01,
      "the hole's curve rises to the door's crown and no further")

a = K1.build(p, SID)
check(a is not None, "1945 builds")

# -- without the door flag, a brick front's door is a rectangular hole ------------------------
ph_flat = copy.deepcopy(ph)
del ph_flat["form"]["street_front_round_heads"]["value"]["door"]
ph_flat["form"]["entrance_kit"]["value"][DOOR] = {"variant": "k07.entrance.panel_door_stoop", "front_yard_m": 9.5}
pf = KP.from_phase(ph_flat, st)
df = next(o for o in pf.openings if o.component == DOOR)
check(not df.round_head and len(K1.hole(df)) == 4, "without it the door is a rectangular hole, as before")

# -- refusals ---------------------------------------------------------------------------------
x = copy.deepcopy(ph)
x["form"]["street_front_round_heads"]["value"]["door"] = "yes"
refused(x, "door named as anything but true")

x = copy.deepcopy(ph)
del x["form"]["street_front_round_heads"]["value"]["key"]
x["form"]["street_front_round_heads"]["value"]["hood"] = {"variant": KP.ROUND_HEAD_HOOD, "overhang_m": 0.1}
refused(x, "a round door with no key to stand on its arch band")

x = copy.deepcopy(ph)
x["form"]["street_front_round_heads"]["value"].update(head="segmental", rise_over_span=0.2)
refused(x, "a round door on a segmental head")

x = copy.deepcopy(ph)
x["form"]["entrance_kit"]["value"][DOOR] = {"variant": "k07.entrance.panel_door_stoop", "front_yard_m": 9.5}
refused(x, "a round door hung with a flat-headed K07 entrance")

x = copy.deepcopy(ph_flat)
x["form"]["entrance_kit"]["value"][DOOR]["opening_m"] = [1.3, 3.4]
refused(x, "entrance_kit.opening_m on a door neither arched nor round-headed")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall checks pass")
