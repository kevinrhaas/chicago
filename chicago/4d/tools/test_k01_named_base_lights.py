#!/usr/bin/env python3
"""T-3365 (T-1914): three K01 street-front dressings 2009 Prairie's photograph asked for.

  * `basement_lights.at_m` — a front that names its street windows one by one
    (`street_front_windows`) names its basement lights the same way, each centre along the
    front, standing in the rusticated base under its coping;
  * `street_front_windows.corner_stone` — the front's low-s corner dressed in stone from a
    height to the wall head, returned on the side wall;
  * `carved_bands[k].panel` — a carved band laid as a panel over its own run, not as a course
    across the whole front.

Held on the committed record; each refused out of its range.

    python3 tools/test_k01_named_base_lights.py
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

SID = "mayer_house_2009_prairie"
failures = []


def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


record = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(record["phases"][0], record)
lights = sorted((o.s_m, o.sill_m, o.height_m) for o in p.openings if o.component == "k01.opening.area_light")
check([s for s, _, _ in lights] == [1.96, 3.02, 4.05], f"three basement lights at the named centres ({lights})")
check(all(abs(sill + h - (p.stone["coping_top_m"] - p.stone["coping_height_m"])) < 1e-6 for _, sill, h in lights),
      "their heads on the rusticated base's top, under its coping")
check(abs(p.stone["coping_top_m"] - 1.25) < 1e-6, f"the coping keeps the front's plinth line ({p.stone['coping_top_m']})")
check(all(b != (4.65, 5.25) for b in p.street_dress["belts"]), "the carved panel is not a belt across the front")

a = K1.build(p, SID)
cs = a.components["k01.wall.corner_stone"]["instances"]
check(len(cs) == 1 and cs[0]["params"]["from_m"] == 9.2 and cs[0]["params"]["to_m"] == p.eave_m,
      "one corner stone, from the string course to the wall head")
cb = a.components["k01.wall.carved_band"]["instances"]
check(len(cb) == 1 and cb[0]["params"].get("panel") is True and cb[0]["params"]["rings"] > 0,
      "the carving is laid as a panel and carved")


def refused(mutate, what):
    r = copy.deepcopy(record)
    mutate(r["phases"][0]["form"])
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it resolved)")


def bl(f):
    return f["basement_lights"]["value"]


def sfw(f):
    return f["street_front_windows"]["value"]


refused(lambda f: bl(f).pop("at_m"), "basement lights on a named-window front without their centres")
refused(lambda f: bl(f).update(at_m=[3.02, 1.96, 4.05]), "centres out of order")
refused(lambda f: bl(f).update(at_m=[1.96, 2.5, 4.05]), "two lights with no pier between them")
refused(lambda f: bl(f).update(at_m=[1.96, 3.02, 6.18]), "a light under the stoop")
refused(lambda f: bl(f).update(height_m=0.9), "a light rising into the coping")
refused(lambda f: sfw(f)["corner_stone"].update(width_m=1.5), "a corner stone 1.5 m along the front")
refused(lambda f: sfw(f)["corner_stone"].update(from_m=1.0), "a corner stone from under the principal floor")
refused(lambda f: sfw(f)["corner_stone"].update(colour="red"), "an unknown corner_stone key")
refused(lambda f: sfw(f)["carved_bands"][0].pop("s_m"), "a carved panel with no run")
refused(lambda f: sfw(f)["carved_bands"][0].update(panel="yes"), "panel not true or false")

if failures:
    print(f"FAIL  {len(failures)} check(s)")
    sys.exit(1)
print("PASS  named basement lights, corner stone, carved panel")
