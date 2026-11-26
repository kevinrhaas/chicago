#!/usr/bin/env python3
"""T-3725: a front laid by front_bays may name its basement lights' own centres.

The Armour photograph puts 2123 Prairie's basement light beside its bow north of the principal
light over it, not under that light's bay as K01 laid every basement light of a front laid by
`front_bays`. `basement_lights.at_m` (until now only a `street_front_windows` front's) may name
them on such a front too. This holds the kit and the record to it:

  * 2123 names one light at 5.32 m, and its build cuts exactly one area light in the street
    front, there, sized as the record's lights are;
  * without `at_m` the light stands under the bay at 5.75 m (the door's bay keeps none), as before;
  * lights out of order, crowding each other, past the front's ends, under the stoop, or whose
    lintel cuts the bow's junction are refused.

    python3 tools/test_k01_basement_lights_off_bay.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "house_2123_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]


def lights(p):
    return [o for o in p.openings if o.component == "k01.opening.area_light" and o.wall == "k01.wall.street_front"]


bl = ph["form"]["basement_lights"]["value"]
check(bl.get("at_m") == [5.32], f"2123 names its light beside the bow at 5.32 m ({bl.get('at_m')})")
got = lights(KP.from_phase(ph, st))
check([round(o.s_m, 3) for o in got] == [5.32], f"one area light in the front, at 5.32 m ({[o.s_m for o in got]})")
check(all((o.sill_m, o.width_m, o.height_m) == (0.55, 0.9, 1.45) for o in got), "sized as the record's lights")

phb = copy.deepcopy(ph)
phb["form"]["basement_lights"]["value"].pop("at_m")
got = lights(KP.from_phase(phb, st))
check([round(o.s_m, 3) for o in got] == [5.75], f"without at_m, under the bay at 5.75 m as before ({[o.s_m for o in got]})")

for why, at, says in [("lights out of order", [7.0, 5.32], "north to south"),
                      ("lights crowding each other", [5.32, 6.3], "pier"),
                      ("a light past the front's end", [9.2], "inside the front"),
                      ("a light under the stoop", [8.3], "stoop"),
                      ("a light whose lintel cuts the bow's junction", [5.2], "junction")]:
    phb = copy.deepcopy(ph)
    phb["form"]["basement_lights"]["value"]["at_m"] = at
    try:
        KP.from_phase(phb, st)
        check(False, f"{why} is refused")
    except (KP.ParamError, ValueError) as e:
        check(says in str(e), f"{why} is refused ({str(e)[:90]})")

print(f"\n{'FAIL' if failures else 'PASS'} — basement lights off their bays: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
