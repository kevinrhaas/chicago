#!/usr/bin/env python3
"""T-3370: 1936 Prairie's balconies as Chicagology's photograph draws them.

The print draws the verandah's balcony as a pale balustrade over a cornice carried on a row of
modillions hanging down to the arcade's crowns, and the porch's balcony pale over its cornice,
both in the window dressings' tone. So:

  * `corner_porch.entablature.modillions` takes width_m, drop_m, out_m (to the cornice's proud)
    and spacing_m, and nothing else; refused past the front arches' crowns, under a cornice
    standing less than 0.1 m proud, or out past it;
  * `corner_porch.dressings: trim` lays the entablature, the modillions and the balustrade in
    the front's trim stone (`dress_stone`); any other value is refused;
  * `entrance_kit.hood.railing_fabric: trim` lays a stone hood's railing in the same stone;
  * 1936's record builds both; 1701's corner porch, naming neither, has no modillions and no
    trim (its mesh's bytes are held by `generators/k01_emit.py --check`).

    python3 tools/test_k01_porch_balcony.py
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

SID = "house_1918_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def variant(edit):
    r = copy.deepcopy(st)
    edit(r["phases"][0]["form"])
    return r


def refused(edit, why, needle):
    r = variant(edit)
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError as e:
        check(needle in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (it was accepted)")


p = KP.from_phase(st["phases"][0], st)
cp = p.corner_porch
check(cp.get("modillions") == {"width_m": 0.12, "drop_m": 0.25, "out_m": 0.15, "spacing_m": 0.42},
      f"1936's verandah cornice stands on modillions: {cp.get('modillions')}")
check(cp.get("dressings") == "trim", "1936's verandah dressings are the front's trim stone")
check(p.entrance_kit["hood"].get("railing_fabric") == "trim", "1936's porch railing is the front's trim stone")
crown = max(cp["spring_m"] + a["span_m"] / 2 for a in cp["arches"] if a["face"] == "front")
check(cp["head_m"] - cp["modillions"]["drop_m"] >= crown - 1e-9,
      f"the modillions hang to {cp['head_m'] - cp['modillions']['drop_m']:.2f} m, not past the crowns ({crown:.2f} m)")

a = K1.build(p, SID)
m = a.corner_porch_meta
check(m.get("modillions", 0) >= 15 and m.get("dressings") == "trim" and abs(m["top_m"] - 7.22) < 1e-6,
      f"the verandah builds its modillions and balustrade in trim stone to 7.22 m: {m}")
check(a.hood_meta.get("railing_fabric") == "trim" and abs(a.hood_meta["top_m"] - 7.05) < 1e-6,
      f"the porch's railing in trim stone tops at 7.05 m: {a.hood_meta}")
check("dress_stone" in a.prims and len(a.prims["dress_stone"].idx) > 0, "the trim stone carries triangles")

# without dressings the balcony stays in the porch's own stone, the modillions with it
plain = variant(lambda f: f["corner_porch"]["value"].pop("dressings"))
b = K1.build(KP.from_phase(plain["phases"][0], plain), SID)
check(len(b.prims["bay_stone"].idx) > len(a.prims["bay_stone"].idx)
      and len(b.prims["dress_stone"].idx) < len(a.prims["dress_stone"].idx),
      "without dressings the entablature and balustrade go back to the porch's stone")
# without modillions, none are built
bare = variant(lambda f: f["corner_porch"]["value"]["entablature"].pop("modillions"))
c = K1.build(KP.from_phase(bare["phases"][0], bare), SID)
check("modillions" not in c.corner_porch_meta, "without modillions the cornice is a plain slab again")

# 1701's corner porch names neither
h = json.loads((ROOT / "data" / "structures" / "hibbard_house_1701_prairie.json").read_text())
hp = KP.from_phase(h["phases"][0], h).corner_porch
check("modillions" not in hp and "dressings" not in hp, "1701's corner porch takes neither")

M = lambda f: f["corner_porch"]["value"]["entablature"]["modillions"]
refused(lambda f: M(f).update(drop_m=0.45), "modillions hanging past the crowns", "past the front arches' crowns")
refused(lambda f: M(f).update(out_m=0.35), "modillions out past the cornice", "to the cornice's proud")
refused(lambda f: M(f).pop("out_m"), "modillions with no projection", "modillions takes")
refused(lambda f: M(f).update(spacing_m=0.15), "modillions closer than 0.1 m apart", "0.1 m apart")
refused(lambda f: f["corner_porch"]["value"]["entablature"].update(proud_m=0.05), "modillions under a 0.05 m proud",
        "0.05 m out to the cornice's proud")
refused(lambda f: f["corner_porch"]["value"].update(dressings="marble"), "dressings in another stone", "dressings: trim")
refused(lambda f: f["entrance_kit"]["value"]["k01.opening.door_leaf"]["hood"].update(railing_fabric="slate"),
        "a railing in slate", "railing_fabric")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_porch_balcony — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
