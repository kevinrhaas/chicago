#!/usr/bin/env python3
"""T-3626: an open, roofed porch on a K01 rear wing's deck (k01_wing_porch).

2013 Prairie's record carries one on its rear block (`rear_2b`), off the 2003 nomination's
north-side and rear photographs ("the top floor of the rear section is open to provide a
terrace"). This holds the committed record's assembly to what the ticket says:

  * the porch is built on the rear block's deck: a post at each rear corner and at each
    listed station, balusters along its railed sides, one registered instance;
  * its floor is the wing's deck, its roof the record's storey over it, and the roof tops out
    no higher than the deck of the narrower part it stands against;
  * nothing of it stands outside the wing's plan by more than the roof's overhang;
  * refused: a porch on a pitched wing, a roof over the host's deck, a post within 0.6 m of a
    corner, a railing on an unknown side, and an unknown key.

    python3 tools/test_k01_wing_porch.py
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

SID = "reid_house_2013_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record(edit=None):
    st = copy.deepcopy(json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text()))
    phase = st["phases"][-1]
    wings = phase["form"]["rear_wings"]["value"]
    if edit:
        edit(next(w for w in wings if w["id"] == "rear_2b"))
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
w = next(x for x in p.rear_wings if x["id"] == "rear_2b")
host = next(x for x in p.rear_wings if x["id"] == "rear_3b")
P = w.get("roof_porch")
check(bool(P), "2013's rear block resolves a roof porch")
check(P and abs(P["floor_m"] - w["deck_m"]) < 1e-6, f"its floor is the rear block's deck ({w['deck_m']} m)")
check(P and P["top_m"] <= host["deck_m"] + 1e-6,
      f"its roof tops out at {P and P['top_m']} m, under the 3B part's deck at {host['deck_m']} m")
check(not any(x.get("roof_porch") for x in p.rear_wings if x["id"] != "rear_2b"), "no other wing carries one")
a = K1.build(p, st["id"])
m = (getattr(a, "wing_porch_meta", None) or {}).get("rear_2b")
check(m is not None, "the assembly dressed the porch")
want = 2 + sum(len(x) for x in P["posts"].values())
check(m and m["posts"] == want, f"a post at each outer corner and listed station ({m and m['posts']} of {want})")
check(m and m["balusters"] > 60, f"balusters along its three railed sides ({m and m['balusters']})")
comp = a.components.get("k01.roof_porch.wing.rear_2b")
check(comp is not None and len(comp["instances"]) == 1, "one k01.roof_porch.wing.rear_2b instance is registered")
if comp:
    sk = comp["instances"][0]["sockets"]
    check(abs(sk["floor"][1] - P["floor_m"]) < 1e-3 and abs(sk["roof"][1] - P["top_m"]) < 1e-3,
          "its sockets stand at the floor and the roof's top")
# the porch's iron, above the deck: inside the wing's plan
u0, u1, v0, v1 = w["rect"]
iron = [q for q in a.prims["iron"].pos if q[1] > w["deck_m"] + 1e-3] if a.prims.get("iron") else []
check(len(iron) > 500, f"the porch's posts and railings are laid over the deck ({len(iron)} vertices)")
if iron:
    check(all(u0 - 1e-3 <= q[0] <= u1 + 1e-3 and -v1 - 1e-3 <= q[2] <= -v0 + 1e-3 for q in iron),
          "its posts and railings stand inside the rear block's plan")

try:
    from archetypes import k01_wing_porch as WP
    WP.resolve("rear_2b", copy.deepcopy(record()[1]["form"]["rear_wings"]["value"][1]["roof_porch"]),
               rect=w["rect"], deck=w["deck_m"], roof_kind="hip", host_top=host["deck_m"])
    check(False, "refused: a porch on a pitched wing — it was accepted")
except WP.ParamError as e:
    check("flat deck" in str(e), f"refused: a porch on a pitched wing ({e})")
refused(lambda e: e["roof_porch"].update(storey_m=3.6), "over the", "a roof standing over the host's deck")
refused(lambda e: e["roof_porch"]["posts"].update(south=[-9.9]), "within 0.6 m of a corner post",
        "a post crowding a corner")
refused(lambda e: e["roof_porch"]["railing"].update(sides=["front"]), "railing", "a railing on a side it has not")
refused(lambda e: e["roof_porch"].update(deck=True), "roof_porch takes", "an unknown key")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_wing_porch — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
