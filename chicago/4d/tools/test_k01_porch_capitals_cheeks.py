#!/usr/bin/env python3
"""T-3186: a K01 portico's carved capitals and a scrolled stoop beside open terraces, held on
1901 Prairie's record.

The 1898 Chicagology photograph of the Ream house shows its porch on paired Corinthian shafts
and its stoop between two stone cheeks that fall straight down the rake to a roll at the walk,
the porch's terraces open either side of the stoop. So:

  * `entrance_kit.hood.columns.carved` carves each column's capital as a bell of leaves in
    one or two tiers under an abacus (the bay columns' carving, T-2887), in `carved_trim`;
  * `cheek_form: scrolled` may stand beside open terraces at the landing's depth, and its
    `bow` sets the sweep's fall, 1 straight down the rake to 2, the concave default;
  * a record naming neither builds as before (every other mesh's bytes are held by
    `generators/*_emit.py --check`), and every refusal says why.

    python3 tools/test_k01_porch_capitals_cheeks.py
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

SID = "ream_house_1901_prairie"
failures = []


def check(ok, what):
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok:
        failures.append(what)


def refused(rec, why, needle):
    try:
        KP.from_phase(rec["phases"][0], rec)
    except KP.ParamError as e:
        check(needle in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (it was accepted)")


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
DOOR = "k01.opening.door_leaf"


def door(f):
    return f["entrance_kit"]["value"][DOOR]


def variant(edit):
    r = copy.deepcopy(st)
    edit(door(r["phases"][0]["form"]))
    return r


p = KP.from_phase(st["phases"][0], st)
cols = p.entrance_kit["hood"]["columns"]
check(cols.get("carved") == {"tiers": 2, "abacus_m": 0.1},
      f"1901's porch columns carry carved capitals: {cols.get('carved')}")
check(p.entrance_kit.get("cheek_form") == {"kind": "scrolled", "bow": 1.0},
      f"1901's stoop takes scrolled cheeks falling straight: {p.entrance_kit.get('cheek_form')}")

a = K1.build(p, SID)
carved = a.prims.get("carved_trim")
check(carved is not None and len(carved.idx) // 3 >= 4 * 2 * 16 * 2,
      f"the build carves four capitals in two tiers of leaves ({len(carved.idx) // 3 if carved else 0} triangles)")

# without the carving the capitals are the plain blocks again, and nothing is carved
plain = variant(lambda d: d["hood"]["columns"].pop("carved"))
b = K1.build(KP.from_phase(plain["phases"][0], plain), SID)
check("carved_trim" not in b.prims or not b.prims["carved_trim"].idx,
      "without `carved` the capitals are plain blocks")

# the bow moves the cheeks, and only them
bowed = variant(lambda d: d["cheek_form"].update(bow=2.0))
c = K1.build(KP.from_phase(bowed["phases"][0], bowed), SID)
check(c.prims["stoop_stone"].pos != a.prims["stoop_stone"].pos and c.prims["carved_trim"].pos == carved.pos,
      "the concave bow lays the cheeks apart from the straight one, the capitals unmoved")

# refusals
refused(variant(lambda d: d["hood"]["columns"]["carved"].update(tiers=3)), "three tiers of leaves", "tiers (1 or 2)")
refused(variant(lambda d: d["hood"]["columns"]["carved"].update(abacus_m=0.4)), "an abacus deeper than the capital allows",
        "0.08 m short")
refused(variant(lambda d: d["hood"]["columns"]["carved"].update(leaves=8)), "a stray key on the carving", "tiers (1 or 2)")
refused(variant(lambda d: d["cheek_form"].update(bow=0.5)), "a bow under 1 (a convex sweep)", "power of 1")
refused(variant(lambda d: d["cheek_form"].update(bow=2.5)), "a bow over 2", "power of 1")
refused(variant(lambda d: d["terrace"][0].update(out_m=3.0)), "a scrolled cheek beside a terrace deeper than the landing",
        "only open, at the landing's depth")
refused(variant(lambda d: d["terrace"][1].update(parapet={"height_m": 0.8, "thickness_m": 0.2, "holes": [1, 4], "hole_m": [0.15, 0.15]})),
        "a scrolled cheek beside a terrace behind a parapet", "only open, at the landing's depth")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_porch_capitals_cheeks — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
