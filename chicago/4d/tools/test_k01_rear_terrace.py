#!/usr/bin/env python3
"""T-1881: a raised stone terrace under a striped awning on a K01 house's rear wall.

1729 Prairie's record carries one, off J. W. Taylor's photographs nos. 16555 and 16554: the
`rear_terrace` k01_rear_terrace builds against the main rear wall at its 18th Street end, where
the 1911 sheet's one-storey block was built as a brick box until now. This holds the committed
record's assembly to what the ticket says:

  * the terrace is built: one k01.rear_terrace instance, its floor at the record's height,
    pedestals, balusters, the awning's posts and its stripes all laid;
  * nothing of it stands inside the main block (u > 0) or past its run along the wall, and the
    old brick block is gone (the house carries no rear wing);
  * the awning pitches down from the wall to its eave, over the balustrade's top;
  * refused: a floor high over the principal floor, an awning whose eave is under the
    balustrade, a run past the wall's end, and an unknown key.

    python3 tools/test_k01_rear_terrace.py
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
from archetypes import k01_rear_terrace as RT  # noqa: E402

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
        edit(phase["form"]["rear_terrace"]["value"])
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
T = p.rear_terrace
check(bool(T) and T["wall"] == "k01.wall.rear_service", "1729's record resolves a terrace on the main rear wall")
check(not p.rear_wings, "the sheet's south-east block is no longer built as a brick rear wing")
a = K1.build(p, st["id"])
m = getattr(a, "rear_terrace_meta", None)
check(m is not None, "the assembly dressed the terrace")
check(m and m["pedestals"] >= 4 and m["balusters"] > 40,
      f"pedestals and balusters round its open sides ({m and m['pedestals']} pedestals, {m and m['balusters']} balusters)")
check(m and m["posts"] == T["awning"]["posts"], f"the awning stands on its {T['awning']['posts']} posts")
check(m and m["stripes"] >= 10, f"the awning's canvas is laid in stripes ({m and m['stripes']})")
check(m and m["awning_m"][0] > m["top_m"] + 0.5 and m["awning_m"][1] > m["awning_m"][0],
      "the awning pitches down from the wall to an eave over the balustrade's top")
comp = a.components.get("k01.rear_terrace")
check(comp is not None and len(comp["instances"]) == 1, "one k01.rear_terrace instance is registered")
if comp:
    sk = comp["instances"][0]["sockets"]
    check(abs(sk["floor"][1] - T["floor_m"]) < 1e-3, "its floor stands at the record's height")
# nothing of the terrace inside the main block or past its run: read the vertices its slots lay
# behind the rear wall. The stone and iron slots are shared with the house's other dressings
# (the cornice's and the deck's cresting overhang the wall), so read those up to the
# pedestals' caps only; the canvas slots carry nothing else behind the wall.
top = T["floor_m"] + T["balustrade"]["height_m"] + 0.12
behind = []
for name in (RT.STONE, RT.IRON) + RT.CANVAS:
    pr = a.prims.get(name)
    for q in (pr.pos if pr is not None else []):
        if q[0] < -1e-6 and (name in RT.CANVAS or q[1] <= top + 1e-6):
            behind.append(q)
check(len(behind) > 1000, f"the terrace's faces are laid behind the rear wall ({len(behind)} vertices)")
if behind:
    zs = [q[2] for q in behind]
    xs = [q[0] for q in behind]
    reach = T["out_m"] + T["awning"]["reach_m"] + 0.1
    check(-T["v_m"][1] - reach <= min(zs) and max(zs) <= -T["v_m"][0] + 0.1,
          f"behind the rear wall it stands within v {T['v_m'][0]}-{T['v_m'][1]} (and the awning's reach) "
          f"(z {min(zs):.2f}..{max(zs):.2f})")
    check(min(xs) >= -reach, f"and no further out than its {T['out_m']} m and the awning's reach")

refused(lambda v: v.update(floor_m=3.5), "rear_terrace", "a floor high over the principal floor")
refused(lambda v: v["awning"].update(eave_m=3.0), "rear_terrace.awning", "an eave under the balustrade's top")
refused(lambda v: v.update(v_m=[11.63, 19.0]), "rear_terrace.v_m", "a run past the wall's end")
refused(lambda v: v.update(steps=True), "rear_terrace takes", "an unknown key")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_rear_terrace — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
