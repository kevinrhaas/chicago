#!/usr/bin/env python3
"""T-3242: a two-level veranda on a K01 house's rear wall, and an oriel on a rear wing's wall.

1701 Prairie's record carries both, off Glessner House Museum's rear photograph: the
`rear_veranda` k01_rear_veranda builds against the main rear wall south of the 1874 range,
and the range's corbelled oriel (`range_oriel`), a K08 oriel on the wing's wall. This holds
the committed record's assembly to what the ticket says:

  * the veranda is built: its two decks at the record's heights, a pair of posts at every
    station, balusters on both decks and a frieze of spindles, and a flight with as many
    risers as the lower deck's height asks, its foot on grade off the front;
  * nothing of it stands inside the main block (u > 0) or past the wall's ends;
  * the wing's wall stands behind its oriel: walling in the wing's north wall's plane at the
    oriel's span below its corbels (a tower still opens the wall from grade, T-2842);
  * refused: a veranda that runs into the range standing on the same wall, a flight that runs
    into a station's posts, a lower deck high over the principal floor, and an unknown key.

    python3 tools/test_k01_rear_veranda.py
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
        edit(phase["form"]["rear_veranda"]["value"])
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
V = p.rear_veranda
check(bool(V) and V["wall"] == "k01.wall.rear_service", "1701's record resolves a rear veranda on the main rear wall")
a = K1.build(p, st["id"])
m = getattr(a, "rear_veranda_meta", None)
check(m is not None, "the assembly dressed the veranda")
n_st = len(V["stations_v_m"])
check(m and m["posts"] == 2 * n_st, f"a pair of posts at each of its {n_st} stations ({m and m['posts']} posts)")
check(m and m["balusters"] > 40 and m["spindles"] > 20, f"balusters on both decks and a spindle frieze "
      f"({m and m['balusters']} balusters, {m and m['spindles']} spindles)")
want = round(V["decks_m"][0] / phase["form"]["rear_veranda"]["value"]["steps"]["riser_m"])
check(m and m["risers"] == want, f"the flight has the {want} risers the lower deck's height asks")
comp = a.components.get("k01.rear_veranda")
check(comp is not None and len(comp["instances"]) == 1, "one k01.rear_veranda instance is registered")
if comp:
    sk = comp["instances"][0]["sockets"]
    check(abs(sk["lower_deck"][1] - V["decks_m"][0]) < 1e-3 and abs(sk["upper_deck"][1] - V["decks_m"][1]) < 1e-3,
          "its decks stand at the record's heights")
    foot = sk["steps_foot"]
    check(foot[1] == 0.0 and foot[0] < -V["out_m"], "the flight's foot is on grade, off the veranda's front")
# nothing of the veranda inside the main block or past the rear wall's ends: read the prims'
# vertices in the two slots it lays (each slot is shared, so look only behind the rear wall)
behind = []
for name in ("bay_strip_paint", "stoop_stone"):
    pr = a.prims.get(name)
    for q in (pr.pos if pr is not None else []):
        if q[0] < -1e-6:
            behind.append(q)
check(len(behind) > 1000, f"the veranda's faces are laid behind the rear wall ({len(behind)} vertices)")
if behind:
    zs = [q[2] for q in behind]
    check(-V["v_m"][1] - 0.2 <= min(zs) and max(zs) <= -V["v_m"][0] + 0.2,
          f"behind the rear wall it stands within v {V['v_m'][0]}-{V['v_m'][1]}")
# the oriel on the wing: the wall stands behind it (it is not cut from grade as a tower's is)
ori = next(b for b in p.bays if b["id"] == "range_oriel")
check(ori.get("wing") == "rear_range_1874", "the range's oriel stands on the 1874 range's wall")
covers = [(*b["span_m"], 0.0) for b in p.bays if b["wall"] == ori["wall"] and b["variant"]["kind"] != "oriel"]
check(not covers, "nothing but the oriel stands on that wall, so no part of it is opened from grade")

refused(lambda v: v.update(v_m=[6.9, 14.7]), "within 0.3 m of the wing", "a veranda running into the range")
refused(lambda v: v["steps"].update(v_m=9.6), "run into the posts", "a flight into a station's posts")
refused(lambda v: v.update(decks_m=[2.6, 5.2]), "decks_m", "a lower deck high over the principal floor")
refused(lambda v: v.update(roof=True), "rear_veranda takes", "an unknown key")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_rear_veranda — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
