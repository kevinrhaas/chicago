#!/usr/bin/env python3
"""T-3365 (T-1914): two K01 dressings 2009 Prairie's photograph asked for.

  * `shaped_gable.finial.form: "crest"` — a carved block on a flat-topped gable's apex in
    place of a turned finial, `foot_m` under the apex;
  * `entrance_kit.arch.pilasters.pinnacles` — a door's pilasters carried on over their
    capitals as shafts to a course under spires, and a stem and bud over the arch's crown.

Held on the committed record (the build draws them: the crest's stone stands to its top over
the apex, the pinnacles' spires reach their tops); each refused out of its range.

    python3 tools/test_k01_crest_pinnacles.py
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
fn = p.shaped_gable["finial"]
check(fn.get("form") == "crest" and fn["foot_m"] == 0.22, f"the gable's finial is a crest ({fn})")
pk = p.entrance_kit["arch"]["pilasters"]["pinnacles"]
check(pk["shaft_to_m"] == 5.25 and pk["top_m"] == 5.6 and pk["crown"]["top_m"] == 5.7,
      f"the door's pilasters carry their pinnacles ({pk})")
grp = p.arched_front["groups"][0]
check(grp["pilasters"]["pinnacles"] == pk if "pilasters" in grp else True,
      "the arched front's door group carries the same pinnacles")

a = K1.build(p, SID)
check(len(a.components["k01.roof.gable_finial"]["instances"]) == 1, "one crest on the apex")
check(len(a.components["k01.opening.door_pilaster"]["instances"]) == 1, "the door's pilasters drawn once")


def refused(mutate, what):
    r = copy.deepcopy(record)
    mutate(r["phases"][0]["form"])
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it resolved)")


def fin(f):
    return f["shaped_gable"]["value"]["finial"]


def pn(f):
    return f["entrance_kit"]["value"]["k01.opening.door_leaf"]["arch"]["pilasters"]["pinnacles"]


refused(lambda f: fin(f).update(form="obelisk"), "an unknown finial form")
refused(lambda f: fin(f).update(foot_m=0.4), "a crest standing under its own height")
refused(lambda f: fin(f).update(radius_m=0.1), "a crest narrower than 0.3 m")
refused(lambda f: fin(f).update(form="urn"), "a foot_m on an urn")
refused(lambda f: pn(f).update(shaft_m=0.3), "a pinnacle shaft as broad as its pilaster")
refused(lambda f: pn(f).update(shaft_to_m=4.6), "pinnacle shafts ending at the keystone's top")
refused(lambda f: pn(f).update(top_m=7.0), "a spire over a metre tall")
refused(lambda f: pn(f)["crown"].update(stem_m=0.3), "a crown stem broader than its bud")
refused(lambda f: pn(f)["crown"].pop("top_m"), "a crown with no top")
refused(lambda f: pn(f).update(colour="red"), "an unknown pinnacles key")

if failures:
    print(f"FAIL  {len(failures)} check(s)")
    sys.exit(1)
print("PASS  gable crest, door pinnacles")
