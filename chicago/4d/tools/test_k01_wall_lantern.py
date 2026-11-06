#!/usr/bin/env python3
"""T-1881: a hanging lantern on a wrought-iron arm off a K01 house's street front.

1729 Prairie's record carries one (`wall_lanterns`, k01_wall_lanterns), off the 1890 Albertype
plate, hung off the entrance part's south return beside the portico, and a banded pier at the
entrance's inner south angle (`street_front_pavilions`). This holds the committed record's
assembly to what the ticket says:

  * the lantern is built: one k01.wall_lantern instance, its arm springing from the return's
    face and its axis where the record puts it;
  * its glazing and iron hang round that axis, between its foot and its arm, and none of it
    stands inside the return it is fixed to;
  * the pier stands at the inner angle, clear of the big light's sill table;
  * refused: a lantern hung too low to walk under, an arm too short to clear the face, a face
    the kit does not know, and an unknown key.

    python3 tools/test_k01_wall_lantern.py
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k01_wall_lanterns as WL  # noqa: E402

SID = "pullman_house_1729_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record(edit=None):
    st = copy.deepcopy(json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text()))
    phase = st["phases"][-1]
    if edit:
        edit(phase["form"]["wall_lanterns"]["value"][0])
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
check(len(p.wall_lanterns) == 1, "1729's record resolves one wall lantern")
L = p.wall_lanterns[0]
check(L["wall"] == "k01.wall.street_front" and L["faces"] == "+s",
      "it hangs off a return on the street front, looking along it toward 18th Street")
a = K1.build(p, st["id"])
comp = a.components.get("k01.wall_lantern")
check(comp is not None and len(comp["instances"]) == 1, "one k01.wall_lantern instance is registered")
D = p.depth_m
s, o = L["at_m"]
want = (D + o, L["hang_m"], -(s + L["arm_m"]))
meta = getattr(a, "wall_lanterns_meta", [])
check(len(meta) == 1 and all(abs(x - y) < 1e-3 for x, y in zip(meta[0]["axis"], want)),
      f"its axis stands {L['arm_m']} m off the return's face and {o} m out from the main wall ({meta and meta[0]['axis']})")
if comp:
    sk = comp["instances"][0]["sockets"]
    check(abs(sk["bracket"][2] + s) < 1e-3 and abs(sk["bracket"][1] - L["hang_m"]) < 1e-3,
          "its arm springs from the return's face at the record's height")

# the lantern's own faces: the glass slot's vertices round its axis (the slot is shared with every
# window, so read only those within its brim's reach of the axis and between its foot and arm)
R = L["width_m"] / 2
foot = L["hang_m"] - L["height_m"]


def near(q, r):
    return math.hypot(q[0] - want[0], q[2] - want[2]) <= r + 1e-6 and foot - 1e-6 <= q[1] <= L["hang_m"] + 1e-6


glass = [q for q in a.prims[WL.GLASS].pos if near(q, R)]
iron = [q for q in a.prims[WL.IRON].pos if near(q, R)]
check(len(glass) >= 8 * 3, f"its glazing is laid round the axis ({len(glass)} vertices)")
check(len(iron) >= 8 * 4 * 6, f"its cap, base, corner bars and finial are iron ({len(iron)} vertices)")
check(iron and min(q[1] for q in iron) <= foot + 0.01, "its drop finial reaches its foot")
check(all(-q[2] >= s - 1e-6 for q in glass + iron), "none of it stands inside the return it hangs off")

pier = [i for i in a.components.get("k01.pavilion.pier", {"instances": []})["instances"]
        if abs(i["params"]["s0_m"] - 8.8) < 1e-6]
check(len(pier) == 1 and pier[0]["params"]["s1_m"] <= 9.425,
      "a banded pier stands at the entrance's inner south angle, clear of the big light's sill table")

refused(lambda v: v.update(hang_m=2.8), "wall_lanterns[0].hang_m", "a lantern hung too low to walk under")
refused(lambda v: v.update(arm_m=0.2), "wall_lanterns[0]", "an arm too short to clear the face")
refused(lambda v: v.update(faces="up"), "wall_lanterns[0]", "a face the kit does not know")
refused(lambda v: v.update(chain_m=0.3), "wall_lanterns[0] takes", "an unknown key")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_wall_lantern — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
