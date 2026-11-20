#!/usr/bin/env python3
"""T-3365 (T-1914): a K08 bay's carved apron band, 2009 Prairie's oriel on its photograph.

  * `bays[].apron_band` — a dressed strip round the bay from `from_m` to `to_m` over its
    floor, under its lowest lights' sill stones, carrying rosettes (a boss and four petals) in
    staggered rows at `pitch_m` along each run.

Held on the committed record (the build lays the band where the record puts it and draws its
rosettes: 15 across the oriel's front, one on each cant), the light tier keeping the strip and
dropping the rosettes; each key refused out of its range, and a band reaching into the lights'
sill stones refused.

    python3 tools/test_k08_apron_band.py
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
from archetypes import k08_bays as K8  # noqa: E402

SID = "mayer_house_2009_prairie"
failures = []


def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


record = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(record["phases"][0], record)
oriel = next(b for b in p.bays if b["id"] == "front_oriel")
ab = oriel["variant"]["apron_band"]
check(ab["from_m"] == 0.0 and ab["to_m"] == 0.34 and ab["rosettes"]["rows"] == 2,
      f"the oriel's apron band resolves ({ab})")

a = K1.build(p, SID)
inst = a.components["k08.oriel"]["instances"][0]["params"]
m = inst.get("apron_band") or {}
# T-3365 (2026-11-12): re-read through the photograph's turned camera, the lights' sills at
# 5.75 m and the band from the oriel's floor (5.3 m) to 5 mm under their sill stones
check(m.get("y_m") == [5.3, 5.64], f"the band stands 5.3-5.64 m, under the lights' sills at 5.75 m ({m})")
check(m.get("rosettes") == 17, f"17 rosettes: 8 and 7 across the front, one on each cant ({m})")

light = K8.Bay(oriel["variant"], K8.load(), "light").build(board=False)
check(light.meta.get("apron_band", {}).get("rosettes") == 0, "the light tier keeps the band and drops the rosettes")


def refused(mutate, what):
    r = copy.deepcopy(record)
    mutate(next(b for b in r["phases"][0]["form"]["bays"]["value"] if b["id"] == "front_oriel"))
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it resolved)")


refused(lambda b: b["apron_band"].update(to_m=0.65), "a band reaching into the lights' sill stones")
refused(lambda b: b["apron_band"].update(to_m=0.6), "a band whose top is the sill stones' bed (one plane drawn twice)")
refused(lambda b: b["apron_band"].update(from_m=0.5), "a band under 0.15 m deep")
refused(lambda b: b["apron_band"].update(proud_m=0.1), "a band 0.1 m proud")
refused(lambda b: b["apron_band"]["rosettes"].update(radius_m=0.25), "a rosette over 0.2 m in radius")
refused(lambda b: b["apron_band"]["rosettes"].update(pitch_m=0.1), "rosettes closer than their own width")
refused(lambda b: b["apron_band"]["rosettes"].update(rows=4), "four rows of rosettes")
refused(lambda b: b["apron_band"].update(colour="red"), "an unknown apron_band key")
refused(lambda b: b["apron_band"]["rosettes"].pop("segments"), "rosettes with no segments")

if failures:
    print(f"FAIL  {len(failures)} check(s)")
    sys.exit(1)
print("PASS  K08 apron band")
