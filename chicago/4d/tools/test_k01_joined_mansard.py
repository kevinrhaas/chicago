#!/usr/bin/env python3
"""T-1881: a K01 house's mansarded K08 sections joined to its own mansard, under one rail.

The owner (2026-11-02), of 1729 Prairie: "the roof is contiguous, not broken in the center
towards the north, and make sure that decorative rail is contiguous as well". Each of its four
mansarded sections runs its roof back through the wall plane to the house's curb
(`roof.mansard.back_m`), the entry's runs on past its north end into the north block's
(`roof.mansard.open`), and the house's deck lays one rail round the joined curb
(`mansard.deck.cresting.joined`). This holds the committed record's assembly to that:

  * every mansarded section is joined, its curb at the house's, and none carries a rail of its own;
  * the rail's runs close into one loop round the joined curb: each run starts where the one
    before it ends (less the finials' clearances), and a finial stands at every corner;
  * the entry's deck meets the north block's south curb edge to edge (no notch between them);
  * refused: a section's own cresting on a joined mansard, a section whose curb is not the
    house's, a back reach past 2 m, an open end that is not left or right, and a section that
    stands clear of the house's curb.

    python3 tools/test_k01_joined_mansard.py
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
from archetypes import k01_mansard_deck as MD  # noqa: E402

SID = "pullman_house_1729_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def build(st):
    ph = st["phases"][0]
    return K1.build(KP.from_phase(ph, st), st["id"])


def refused(st, what):
    try:
        build(st)
    except (ValueError, KP.ParamError) as e:
        check(True, f"refused: {what} ({str(e)[:90]})")
        return
    check(False, f"refused: {what}")


rec = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
form = rec["phases"][0]["form"]
a = build(rec)
decks = {d["bay"]: d for d in getattr(a, "joined_decks", [])}
mansarded = [b["id"] for b in form["bays"]["value"] if b["roof"].get("mansard")]
check(sorted(decks) == sorted(mansarded) and len(mansarded) == 4,
      f"every mansarded section is joined ({sorted(decks)})")
curb = form["mansard"]["value"]
check(all(abs(d["curb_m"] - a.p.mansard["curb_m"]) < 1e-3 for d in decks.values()),
      f"each section's curb stands at the house's {a.p.mansard['curb_m']} m")
check(not getattr(a, "bay_crests", None), "no section lays a rail of its own")

laid = a.deck
runs, fins = laid["cresting"], laid["finials"]
check(laid.get("joined") and len(runs) >= 10, f"one joined rail of {len(runs)} runs")
# the loop: each run's end is the next run's start, through a corner or a jog's finial
loop = MD.joined_outline(a.p.mansard["deck"], getattr(a, "joined_decks", []))
fin_at = [tuple(f["at"]) for f in fins]
# every side carries a run, but a jog (one finial at its middle) and a return too short for one
# between its two finials, which then stand within 0.8 m of each other
n = len(loop)
bare = []
for k in range(n):
    p0, p1 = loop[k], loop[(k + 1) % n]
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    on = any(math.dist(mid, ((r["from"][0] + r["to"][0]) / 2, (r["from"][1] + r["to"][1]) / 2)) < 0.3 + math.dist(p0, p1) / 2
             and abs((r["to"][0] - r["from"][0]) * (p1[1] - p0[1]) - (r["to"][1] - r["from"][1]) * (p1[0] - p0[0])) < 1e-6
             for r in runs)
    near = [q for q in fin_at if math.dist(q, mid) < 0.6]
    if not on and not (math.dist(p0, p1) < 0.8 and near):
        bare.append((round(p0[0], 2), round(p0[1], 2)))
check(not bare, f"every side of the joined curb ({n}) carries rail or finials closing it ({bare[:3]})")
gaps = []
for r in runs:
    for end in (r["from"], r["to"]):
        if min(math.dist(end, q) for q in fin_at) > 0.35:
            gaps.append(end)
check(not gaps, f"every run ends at a finial ({gaps[:3]})")

# the entry's deck meets the north block's south curb edge to edge
blk, ent = decks["p_block"]["curb"], decks["p_entry"]["curb"]
check(abs(max(q[1] for q in blk) - min(q[1] for q in ent)) < 1e-3,
      "the entry's deck runs to the north block's south curb (no notch)")

# refusals
bad = copy.deepcopy(rec)
next(b for b in bad["phases"][0]["form"]["bays"]["value"] if b["id"] == "p_entry")["roof"]["mansard"]["cresting"] = \
    {"height_m": 1.0, "inset_m": 0.1}
refused(bad, "a section's own cresting on a joined mansard")
bad = copy.deepcopy(rec)
next(b for b in bad["phases"][0]["form"]["bays"]["value"] if b["id"] == "p_18th")["roof"]["mansard"]["rise_m"] = 4.0
refused(bad, "a section whose curb is not the house's")
bad = copy.deepcopy(rec)
next(b for b in bad["phases"][0]["form"]["bays"]["value"] if b["id"] == "p_18th")["roof"]["mansard"]["back_m"] = 2.5
refused(bad, "a back reach past 2 m")
bad = copy.deepcopy(rec)
next(b for b in bad["phases"][0]["form"]["bays"]["value"] if b["id"] == "p_entry")["roof"]["mansard"]["open"] = \
    {"front": 0.3}
refused(bad, "an open end that is not left or right")
bad = copy.deepcopy(rec)
next(b for b in bad["phases"][0]["form"]["bays"]["value"] if b["id"] == "p_rear")["roof"]["mansard"]["back_m"] = 0.0
refused(bad, "a section clear of the house's curb")

print(f"\n{'ok' if not failures else 'FAIL'}: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
