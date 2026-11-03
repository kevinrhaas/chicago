#!/usr/bin/env python3
"""T-3255: a K01 wall's round-headed lights under eared and crested stone hoods, and the main
block's corner pilasters (k01_dressings).

1701 Prairie's record carries both, off Chicagology's photograph: `eared_round_heads` on the
front and the south flank (K01's north wall), and `corner_pilasters` on the front's south-west
corner. This holds the committed record's assembly to what the ticket says:

  * every round-headed light on the walls the record names is hooded, and no other;
  * a pair of hooded lights meets ear to ear and never overlaps (the flank's pairs);
  * every crest stands under the eave and clear of the light over it;
  * the corner pilaster stands on the corner, wrapped round both faces, from the record's foot
    to its head, and is registered as a k01.corner_pilaster instance;
  * the front's round heads keep no key block under the crest;
  * refused: an unknown key, a wall with no round light, a crest into the eave, an unknown
    corner, a pilaster over the eave, and a key or hood named beside an eared front.

    python3 tools/test_k01_dressings.py
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

SID = "hibbard_house_1701_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record(edit=None):
    st = copy.deepcopy(json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text()))
    phase = st["phases"][-1]
    if edit:
        edit(phase["form"])
    return st, phase


def refused(edit, says, what):
    st, phase = record(edit)
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"refused: {what} ({e})")
        return
    check(False, f"refused: {what} — it was accepted")


st, phase = record()
p = KP.from_phase(phase, st)
H, C = p.eared_hoods, p.corner_pilasters
check(H and H["walls"] == ("k01.wall.street_front", "k01.wall.side.north"),
      "1701's record hoods the front and the south flank (K01's north wall)")
check(not p.round_heads.get("key"), "the front's round heads carry no key block under the crest")
a = K1.build(p, st["id"])
meta = getattr(a, "eared_hood_meta", [])
want = [o for o in p.openings if o.wall in H["walls"] and o.component in KP.ROUND_CUT]
check(len(meta) == len(want) == 11, f"every round-headed light on those walls is hooded ({len(meta)} of {len(want)})")
check(all(m["wall"] in H["walls"] for m in meta), "no light on another wall is hooded")
eave = p.principal_floor_m + sum(p.storey_heights_m)
check(all(m["crest_top_m"] <= eave - 0.3 for m in meta), f"every crest stands under the {eave} m eave")
for wall in H["walls"]:
    row = sorted((m for m in meta if m["wall"] == wall), key=lambda m: (m["crest_top_m"], m["s_m"]))
    clash = [(x["s_m"], y["s_m"]) for x, y in zip(row, row[1:])
             if x["crest_top_m"] == y["crest_top_m"] and x["ears_m"][1] > y["ears_m"][0] + 1e-9]
    check(not clash, f"no two hoods on {wall} overlap ear over ear {clash or ''}")
met = [m for m in meta if m["wall"] == "k01.wall.side.north" and m["s_m"] in (9.9, 11.15)]
check(len(met) == 4 and all(abs(m["ears_m"][1 if m["s_m"] == 9.9 else 0] - 10.525) < 1e-6 for m in met),
      "the flank's rear pairs meet ear to ear half way between their lights")
for m in meta:
    over = [o for o in p.openings if o.wall == m["wall"] and abs(o.s_m - m["s_m"]) < 0.01 and
            o.sill_m > m["crest_top_m"] - 1.0 and o.sill_m > 5.0 and m["crest_top_m"] < 6.0]
    if any(o.sill_m - 0.15 < m["crest_top_m"] for o in over):
        check(False, f"the crest at s {m['s_m']} on {m['wall']} reaches into the sill over it")
cp = getattr(a, "corner_pilaster_meta", [])
check(C and C["corners"] == ("street_south",) and len(cp) == 1, "one corner pilaster, on the front's south corner")
comp = a.components.get("k01.corner_pilaster")
check(comp is not None and len(comp["instances"]) == 1, "one k01.corner_pilaster instance is registered")
if comp:
    sk = comp["instances"][0]["sockets"]
    D, W = p.depth_m, p.width_m
    check(abs(sk["foot"][0] - D) < 1e-6 and abs(sk["foot"][2] + W) < 1e-6 and abs(sk["foot"][1] - C["from_m"]) < 1e-6
          and abs(sk["head"][1] - C["to_m"]) < 1e-6, "it stands on the corner from the record's foot to its head")
# the pilaster's faces stand proud of both walls at the corner
stone = a.prims["limestone_trim"].pos
D, W, d = p.depth_m, p.width_m, C["proud_m"]
front = [q for q in stone if abs(q[0] - (D + d)) < 1e-6 and -W - d - 1e-6 <= q[2] <= -W + C["width_m"] + 1e-6]
flank = [q for q in stone if abs(q[2] - (-W - d)) < 1e-6 and D - C["width_m"] - 1e-6 <= q[0] <= D + d + 1e-6]
check(front and flank, f"its shaft's faces stand {d} m proud of the front and of the flank, round the corner")

refused(lambda f: f["eared_round_heads"]["value"].update(cresting=True), "eared_round_heads takes", "an unknown key")
refused(lambda f: f["eared_round_heads"]["value"].update(walls=["k01.wall.street_front", "k01.wall.side.north",
                                                                  "k01.wall.side.south"]), "has no round-headed light",
        "a wall with no round light")
refused(lambda f: f["eared_round_heads"]["value"]["crest"].update(height_m=0.5, width_m=0.3) or
        f["eared_round_heads"]["value"].update(band_m=0.3), "inside 0.3 m of the", "a crest into the eave")
refused(lambda f: f["corner_pilasters"]["value"].update(corners=["street_west"]), "corner_pilasters.corners",
        "an unknown corner")
refused(lambda f: f["corner_pilasters"]["value"].update(to_m=10.5), "under the", "a pilaster over the eave")
refused(lambda f: f["street_front_round_heads"]["value"].update(key={"width_m": 0.24, "height_m": 0.3, "proud_m": 0.07}),
        "neither under eared_round_heads", "a key block named beside an eared front")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_dressings — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
