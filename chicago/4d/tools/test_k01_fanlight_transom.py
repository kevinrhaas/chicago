#!/usr/bin/env python3
"""T-3364 (T-1914): a K01 door under a flat arch, glazed as a fanlight over a transom bar.

2009 Prairie's record carries it, off the Chicagology photograph: one dark leaf under a two-light
fanlight on a bar 0.25 m under the spring of an elliptical head. The `fanlight_transom` key on
`entrance_kit["k01.opening.door_leaf"]` builds it. This holds the committed record to that:

  * the door variant K07 is handed carries the record's bar, lights and one leaf;
  * K07 builds one leaf and a fanlight over the bar, under the elliptical head;
  * refused: the key on a round head (K07 glazes its own radial fanlight there), with a side
    light, a bar out of its range, a leaf shorter than 1.7 m, an unknown key, three leaves.

    python3 tools/test_k01_fanlight_transom.py
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
from archetypes import k07_entrances as K7  # noqa: E402

SID = "mayer_house_2009_prairie"
failures = []


def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


record = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
phase = record["phases"][0]
p = KP.from_phase(phase, record)
ft = p.entrance_kit.get("fanlight_transom")
check(ft == {"height_m": 0.25, "lights": 2, "leaves": 1}, f"the record's fanlight_transom resolves ({ft})")

a = K1.build(p, SID)
v = a.door_variant()
check((v.get("transom_m"), v.get("transom_lights"), v.get("leaves")) == (0.25, 2, 1),
      f"K07's variant carries the bar, the lights and one leaf ({v.get('transom_m')}, {v.get('transom_lights')}, {v.get('leaves')})")
check(v.get("head") == "elliptical", f"under the elliptical head ({v.get('head')})")
o = K7.Entrance(v, a._entrances)
o.build()
check(o.meta.get("stair", {}).get("risers") == p.risers, "K07 builds the door and its stoop on the K01 stair")


def refused(mutate, what):
    r = copy.deepcopy(record)
    mutate(r["phases"][0]["form"]["entrance_kit"]["value"]["k01.opening.door_leaf"])
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it resolved)")


def round_head(d):
    d["arch"].pop("head"); d["arch"].pop("rise_over_span")


refused(round_head, "on a round head")
refused(lambda d: d.update(side_light={"width_m": 0.5, "pier_m": 0.2, "sill_m": 0.5}), "beside a side light")
refused(lambda d: d["fanlight_transom"].update(height_m=0.05), "a bar 0.05 m under the spring")
refused(lambda d: d["fanlight_transom"].update(height_m=0.5), "a leaf shorter than 1.7 m")
refused(lambda d: d["fanlight_transom"].update(leaves=3), "three leaves")
refused(lambda d: d["fanlight_transom"].update(bars=2), "an unknown key")

if failures:
    print(f"FAIL  {len(failures)} check(s)")
    sys.exit(1)
print("PASS  fanlight_transom")
