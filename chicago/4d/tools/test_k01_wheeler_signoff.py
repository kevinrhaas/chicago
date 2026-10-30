#!/usr/bin/env python3
"""T-3093: 1812 Prairie's sign-off keys, held on its own record.

Levy's print and the c. 1955 photograph read 1812's stone lighter than its brick, its frieze an
interlace of crossing straps, the bosses under the south projection's jambs carved shields, and
its side wall paler than its front. So:

  * `street_front_brick.tone` lays the street front's brick (over the stone line, in the shaped
    gable and in a brick bay) in its own slot, toned, and leaves the side and rear walls in the
    K03 common brick; a front with no stone line names none;
  * a carved band's `interlace` lays two straps crossing every half wavelength, a whole number
    of half waves on the run;
  * a dress oval's `shape: shield` is a convex outline, square-headed and pointed;
  * a record naming none of them builds as before;
  * every refusal says why.

    python3 tools/test_k01_wheeler_signoff.py
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

SID = "wheeler_house_1812_prairie"
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
p = KP.from_phase(st["phases"][0], st)
check(p.front_brick_tone == (0.78, 0.56, 0.52), "1812's record tones its street front's brick")
a = K1.build(p, SID)
check("brick_front" in a.prims and len(a.prims["brick_front"].pos) > 0, "the street front's brick is its own slot")
check("brick" in a.prims and len(a.prims["brick"].pos) > 0, "the side and rear walls keep the K03 brick")
check(a.spec["brick_front"]["color"] == (0.78, 0.56, 0.52) and a.spec["brick"]["color"] == (1.0, 1.0, 1.0),
      "the tone is the front slot's colour, the side walls' left white over the map")
front_u = max(q[0] for q in a.prims["brick_front"].pos)
check(any(q[1] > 13.0 for q in a.prims["brick_front"].pos), "the shaped gable's brick is the front's")
check(not any(q[0] > front_u - 0.5 and q[1] > 13.0 for q in a.prims["brick"].pos if -q[2] > 1.0),
      "no gable brick is left in the side walls' slot")

cb = next(b for b in a.components["k01.wall.carved_band"]["instances"] if b["params"]["carving"] == "interlace")
il = p.street_dress["carved_bands"][0]["interlace"]
s0, s1 = p.street_dress["carved_bands"][0]["s_m"]
halves = round((s1 - s0) / (il["wavelength_m"] / 2))
check(cb["params"].get("crossings") == halves + 1,
      f"the interlace crosses {halves + 1} times on its {s1 - s0:.2f} m run ({cb['params'].get('crossings')})")

shield = K1.SHIELD_OUTLINE
cross = [(shield[i][0] - shield[i - 1][0]) * (shield[(i + 1) % len(shield)][1] - shield[i][1])
         - (shield[i][1] - shield[i - 1][1]) * (shield[(i + 1) % len(shield)][0] - shield[i][0])
         for i in range(len(shield))]
check(all(c >= -1e-9 for c in cross), "the shield's outline is convex and anticlockwise, so its field is one fan")
check(max(y for _, y in shield) == 1.0 and min(y for _, y in shield) == -1.0 and (0.0, -1.0) in shield,
      "it fills its box, level-headed and pointed at the foot")
ovals = [o for b in p.bays for o in b.get("dress", {}).get("ovals", ())]
jambs = [o for o in ovals if abs(o["y_m"] - 5.89) < 1e-6]
check(len(jambs) == 2 and all(o.get("shape") == "shield" for o in jambs)
      and not any(o.get("shape") for o in ovals if o not in jambs),
      "1812's two bosses under the jambs are shields, the caps' bosses still ovals")

# without the keys: one slot, rings, ovals
plain = copy.deepcopy(st)
form = plain["phases"][0]["form"]
del form["street_front_brick"]
band = form["street_front_windows"]["value"]["carved_bands"][0]
del band["interlace"]
band["guilloche"] = {"radius_m": 0.15, "ring_width_m": 0.035, "ring_proud_m": 0.03, "margin_m": 0.03,
                     "pitch": 1.5, "segments": 16}
for o in form["bays"]["value"][0]["dress"]["ovals"]:
    del o["shape"]
b = K1.build(KP.from_phase(plain["phases"][0], plain), SID)
check("brick_front" not in b.prims, "with no tone the front's brick is the walls' own slot")
check(all(i["params"]["carving"] != "interlace" for i in b.components["k01.wall.carved_band"]["instances"]),
      "with a guilloche named the band carves rings")

bad = copy.deepcopy(st)
bad["phases"][0]["form"]["street_front_brick"]["value"] = {"tone": [0.1, 0.5, 0.5]}
refused(bad, "a tone outside [0.2, 1]", "three factors")
bad = copy.deepcopy(st)
del bad["phases"][0]["form"]["stone_front"]["value"]["brick_above_m"]
refused(bad, "a toned front with no stone line", "brick_above_m")
bad = copy.deepcopy(st)
bad["phases"][0]["form"]["street_front_windows"]["value"]["carved_bands"][0]["interlace"]["strap_m"] = 0.3
refused(bad, "straps wider than a quarter of the band", "interlace")
bad = copy.deepcopy(st)
bad["phases"][0]["form"]["bays"]["value"][0]["dress"]["ovals"][0]["shape"] = "lozenge"
refused(bad, "a boss shape the kit does not draw", "shape (oval or shield)")

if failures:
    print(f"\n{len(failures)} check(s) failed")
    sys.exit(1)
print("\nall checks passed")
