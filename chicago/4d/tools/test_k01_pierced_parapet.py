#!/usr/bin/env python3
"""T-3634: 2017 Prairie's porch parapet and north stack as Chicagology's photograph shows them.

The photograph draws the porch's parapet as a coped solid band pierced with five rings between
its corner pedestals, a ball finial on each front corner, and the north stack at its left edge,
rising past the mansard's curb from the cornice. So:

  * `entrance_kit.hood.railing.pierced` {rings, diameter_m} builds the band in place of the
    balusters (and then the railing names no baluster_m or pitch_m); refused when its rings do
    not clear the band or their cells, or on a narrow rail;
  * `entrance_kit.hood.railing.finials` {plinth_m, ball_m} sets a plinth and a ball on each
    front corner post; refused oversized;
  * a stack `on_cornice` astride a side wall may stand through a mansard deck's curb, and that
    side's cresting stops either side of it; one too near the curb's corner is still refused.

    python3 tools/test_k01_pierced_parapet.py
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

SID = "house_2017_prairie"
DOOR = "k01.opening.door_leaf"
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


def railing(f):
    return f["entrance_kit"]["value"][DOOR]["hood"]["railing"]


def refused(edit, why, needle):
    r = variant(edit)
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError as e:
        check(needle in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (it was accepted)")


p = KP.from_phase(st["phases"][0], st)
rl = p.entrance_kit["hood"]["railing"]
check(rl.get("pierced") == {"rings": 5, "diameter_m": 0.27} and "baluster_m" not in rl,
      f"2017's porch railing is a band pierced with five rings: {rl}")
check(rl.get("finials") == {"plinth_m": [0.32, 0.1], "ball_m": 0.34}, f"...under two ball finials: {rl.get('finials')}")
a = K1.build(p, SID)
m = a.hood_meta
# five on the front, three on each return at the front's spacing
check(m.get("rings") == 11 and "balusters" not in m and m.get("finials") == 2,
      f"the hood builds eleven rings and two finials, no balusters: {m}")
check(abs(m["finial_top_m"] - (m["top_m"] + 0.1 + 0.34)) < 1e-6, f"the finials top out over the posts: {m}")
st0 = next(c for c in p.chimneys if c.get("on_cornice"))
check(st0["v_m"] == 0.0 and st0["top_m"] == 12.5, f"the north stack stands on the cornice astride the wall: {st0}")

refused(lambda f: railing(f).update(pierced={"rings": 5, "diameter_m": 0.4}),
        "rings taller than the band", "do not fit a band")
refused(lambda f: railing(f).update(pierced={"rings": 9, "diameter_m": 0.27}),
        "rings wider than their cells", "do not fit a band")
refused(lambda f: railing(f).update(pierced={"rings": 5}), "a pierced band without its diameter", "takes rings")
refused(lambda f: railing(f).update(baluster_m=0.06, pitch_m=0.25), "balusters and a pierced band at once",
        "entrance_kit.hood takes")
refused(lambda f: railing(f).update(rail_m=[0.1, 0.08]), "a pierced band under a narrow rail", "0.12 m wide")
refused(lambda f: railing(f).update(finials={"plinth_m": [0.6, 0.1], "ball_m": 0.34}), "a plinth wider than the post",
        "a plinth 0.1-")
refused(lambda f: railing(f).update(finials={"plinth_m": [0.32, 0.1], "ball_m": 0.5}), "a ball wider than its plinth",
        "a plinth 0.1-")


def corner_stack(f):
    f["chimneys"]["value"]["stacks"][0]["u_m"] = 0.85


refused(corner_stack, "a stack on the cornice through the curb's corner", "stands on the curb")

# the cresting: the deck's south run (v 0, the stack's side) breaks round the stack
laid = getattr(a, "deck", None) or {}
runs = [c for c in (laid.get("cresting") or []) if c.get("side") == "south"]
check(bool(runs), f"the deck lays a south cresting: {laid.get('cresting')}")
if runs:
    u0, u1 = st0["u_m"] - st0["plan_m"][0] / 2, st0["u_m"] + st0["plan_m"][0] / 2
    # it stops 0.1 m short of the stack; past it the run to the street corner is under the
    # cresting's least length, so none is laid there
    check(not any(r["from_m"] < u1 and r["to_m"] > u0 for r in runs)
          and any(abs(r["to_m"] - (u0 - 0.1)) < 2e-3 for r in runs),
          f"the south cresting stops short of the stack: {runs}")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("\nall passed")
