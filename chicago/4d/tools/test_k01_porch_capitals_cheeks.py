#!/usr/bin/env python3
"""T-3186: a K01 portico's carved capitals and a scrolled stoop beside open terraces, held on
1901 Prairie's record.

The 1898 Chicagology photograph of the Ream house shows its porch on paired Corinthian shafts
and its stoop between two stone cheeks that fall straight down the rake to a roll at the walk,
the porch's terraces open either side of the stoop. So:

  * `entrance_kit.hood.columns.carved` carves each column's capital as a bell of leaves in
    one or two tiers under an abacus (the bay columns' carving, T-2887), in `carved_trim`;
  * `cheek_form: scrolled` may stand beside open terraces at the landing's depth, and its
    `bow` sets the sweep's fall, 1 straight down the rake to 2, the concave default, and
    `head_m` its head over the landing in place of the kit's 0.85 m;
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
check(p.entrance_kit.get("cheek_form") == {"kind": "scrolled", "foot_block_m": 0.4, "head_m": 0.6, "bow": 1.0,
                                           "pierced": {"count": 5, "hole_m": [0.3, 0.2], "under_m": 0.12, "span_m": 2.0}},
      f"1901's stoop takes scrolled cheeks falling straight, pierced: {p.entrance_kit.get('cheek_form')}")

a = K1.build(p, SID)
carved = a.prims.get("carved_trim")
check(carved is not None and len(carved.idx) // 3 >= 4 * 2 * 16 * 2,
      f"the build carves four capitals in two tiers of leaves ({len(carved.idx) // 3 if carved else 0} triangles)")

# without the carving the capitals are the plain blocks again, and nothing is carved
plain = variant(lambda d: d["hood"]["columns"].pop("carved"))
b = K1.build(KP.from_phase(plain["phases"][0], plain), SID)
check("carved_trim" not in b.prims or not b.prims["carved_trim"].idx,
      "without `carved` the capitals are plain blocks")

# T-3186: the openings cut the cheeks, and only them; a solid cheek has fewer faces
solid = variant(lambda d: d["cheek_form"].pop("pierced"))
e = K1.build(KP.from_phase(solid["phases"][0], solid), SID)
check(len(a.prims["stoop_stone"].idx) > len(e.prims["stoop_stone"].idx) and e.prims["carved_trim"].pos == carved.pos,
      f"the pierced cheeks carry their openings' reveals ({len(a.prims['stoop_stone'].idx) // 3} triangles against "
      f"{len(e.prims['stoop_stone'].idx) // 3} solid), the capitals unmoved")
try:
    long = variant(lambda d: d["cheek_form"]["pierced"].update(span_m=3.7))
    K1.build(KP.from_phase(long["phases"][0], long), SID)
    check(False, "refused: openings run down to the foot, where the cheek is too low over the treads (it was built)")
except ValueError as ex:
    check("within 0.05 m of the tread" in str(ex), f"refused: openings run down to the foot ({ex})")

# T-3186: nor past the roll, onto the foot block (1901's 2.5 m once the flight shortened to 2.2 m)
try:
    past = variant(lambda d: d["cheek_form"]["pierced"].update(span_m=2.5, hole_m=[0.32, 0.2]))
    K1.build(KP.from_phase(past["phases"][0], past), SID)
    check(False, "refused: openings run past the roll (it was built)")
except ValueError as ex:
    check("past its roll" in str(ex), f"refused: openings run past the roll ({ex})")

# the bow moves the cheeks, and only them (a concave fall is too low over the treads for the openings)
bowed = variant(lambda d: (d["cheek_form"].update(bow=2.0), d["cheek_form"].pop("pierced")))
a = e
c = K1.build(KP.from_phase(bowed["phases"][0], bowed), SID)
check(c.prims["stoop_stone"].pos != a.prims["stoop_stone"].pos and c.prims["carved_trim"].pos == carved.pos,
      "the concave bow lays the cheeks apart from the straight one, the capitals unmoved")

# T-3186: the cheeks' heads stand `head_m` over the landing; without it, the kit's 0.85 m and
# the cheeks alone move (the openings follow the top, so the solid cheek is compared)
kitted = variant(lambda d: (d["cheek_form"].pop("head_m"), d["cheek_form"].pop("pierced")))
k = K1.build(KP.from_phase(kitted["phases"][0], kitted), SID)
check(max(y for _, y, _ in k.prims["stoop_stone"].pos) > max(y for _, y, _ in e.prims["stoop_stone"].pos) - 1e-9
      and k.prims["stoop_stone"].pos != e.prims["stoop_stone"].pos and k.prims["carved_trim"].pos == carved.pos,
      "without head_m the cheeks stand at the kit's 0.85 m, higher than 1901's 0.6 m, the capitals unmoved")
refused(variant(lambda d: d["cheek_form"].update(head_m=0.3)), "a cheek's head under 0.5 m", "0.5-1.0 m")
refused(variant(lambda d: d["cheek_form"].update(head_m=1.2)), "a cheek's head over 1.0 m", "0.5-1.0 m")

# refusals
refused(variant(lambda d: d["hood"]["columns"]["carved"].update(tiers=3)), "three tiers of leaves", "tiers (1 or 2)")
refused(variant(lambda d: d["hood"]["columns"]["carved"].update(abacus_m=0.4)), "an abacus deeper than the capital allows",
        "0.08 m short")
refused(variant(lambda d: d["hood"]["columns"]["carved"].update(leaves=8)), "a stray key on the carving", "tiers (1 or 2)")
refused(variant(lambda d: d["cheek_form"].update(bow=0.5)), "a bow under 1 (a convex sweep)", "power of 1")
refused(variant(lambda d: d["cheek_form"].update(bow=2.5)), "a bow over 2", "power of 1")
refused(variant(lambda d: d["cheek_form"]["pierced"].update(count=13)), "thirteen openings to a cheek", "count 1-12")
refused(variant(lambda d: d["cheek_form"]["pierced"].pop("span_m")), "openings with no span along the sweep", "span_m 0.3-6")
refused(variant(lambda d: d["cheek_form"]["pierced"].update(side="left")), "a stray key on the openings", "count 1-12")
refused(variant(lambda d: d["terrace"][0].update(out_m=3.0)), "a scrolled cheek beside a terrace deeper than the landing",
        "only open, at the landing's depth")
refused(variant(lambda d: d["terrace"][1].update(parapet={"height_m": 0.8, "thickness_m": 0.2, "holes": [1, 4], "hole_m": [0.15, 0.15]})),
        "a scrolled cheek beside a terrace behind a parapet", "only open, at the landing's depth")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_porch_capitals_cheeks — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
