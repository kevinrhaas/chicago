#!/usr/bin/env python3
"""T-3634: a mansard deck's cresting may be a row of square merlons on a solid band, in iron.

Chicagology's photograph of 2017 Prairie shows the crest along the mansard's curb as square
crenellations, not the K10 kit's pierced scroll cresting. This holds the kit and the record to it:

  * `mansard.deck.cresting.pattern: "crenellated"` takes merlon_m 0.08-0.4, pitch_m 0.2-1.0 and
    rise_m 0.04-0.3, a crenel of at least 0.06 m between merlons and a band of at least 0.05 m
    under them, and a height down to 0.15 m (the scroll cresting's least is 0.3 m); it is iron,
    so `painted`, `joined` and a fret's `panel_m` are refused with it, and merlon_m, pitch_m and
    rise_m are refused without it;
  * each run is one closed iron plate with a merlon at each end and its foot let into the deck,
    its top at the record's height over the deck;
  * 2017's record builds it on the street curb, stopped either side of its two dormers;
  * a record that names no pattern builds K10's iron cresting exactly as before.

    python3 tools/test_k01_deck_crenellation.py
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
from archetypes import k01_mansard_deck as MD  # noqa: E402

SID = "house_2017_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]


def cresting(phase):
    return phase["form"]["mansard"]["value"]["deck"]["cresting"]


# -- the record ---------------------------------------------------------------------------------
cr = cresting(ph)
check(cr.get("pattern") == "crenellated", "2017's cresting is crenellated, as its photograph's")
dk = KP.from_phase(ph, st).mansard["deck"]["cresting"]
check(dk["pattern"] == "crenellated" and dk["merlon_m"] == 0.15 and dk["pitch_m"] == 0.34 and dk["rise_m"] == 0.09,
      f"it resolves with its merlons as the record sizes them ({dk})")

a = K1.build(KP.from_phase(ph, st), SID)
runs = a.deck["cresting"]
check(bool(runs) and all(r.get("pattern") == "crenellated" for r in runs), f"every run is crenellated ({len(runs)})")
street = [r for r in runs if r["side"] == "street"]
gaps = KP.from_phase(ph, st).mansard["deck"]["dormer_gaps"]
check(len(gaps) == 2 and len(street) >= 2
      and all(r["to_m"] <= g0 + 1e-3 or r["from_m"] >= g1 - 1e-3 for r in street for g0, g1 in gaps),
      f"the street run stops either side of the two dormers over the curb ({len(street)} pieces)")
check(all(r["merlons"] >= 2 for r in runs), "every run has a merlon at each end")

# -- the plate ----------------------------------------------------------------------------------
pieces, n = MD.crenel_pieces(3.4, 10.0, 0.2, 0.15, 0.34, 0.09, "test")
m = pieces[0].mesh
ys = [q[1] for q in m.pos]
xs = [q[0] for q in m.pos]
check(len(pieces) == 1 and pieces[0].role == "iron" and pieces[0].rests == "rooted", "one rooted iron plate")
check(n == 11, f"3.4 m at about 0.34 m centres carries eleven merlons ({n})")
check(abs(max(ys) - 10.2) < 1e-9 and abs(min(ys) - (10.0 - MD.CRENEL["let_in_m"])) < 1e-9,
      "its top stands the height over its foot, its foot let into the deck")
check(abs(min(xs) + 1.7) < 1e-9 and abs(max(xs) - 1.7) < 1e-9, "it runs the length given, end to end")
tops = sorted({round(q[0], 6) for q in m.pos if abs(q[1] - 10.2) < 1e-9})
check(abs(tops[0] + 1.7) < 1e-9 and abs(tops[-1] - 1.7) < 1e-9, "a merlon stands at each end")
check(len(m.idx) % 3 == 0 and len(m.idx) > 0, "it is triangulated")

# -- refusals -----------------------------------------------------------------------------------
for why, patch in [
    ("merlons wider than their centres leave a crenel", {"merlon_m": 0.3, "pitch_m": 0.32}),
    ("a rise past the band's least", {"height_m": 0.15, "rise_m": 0.12}),
    ("a merlon past 0.4 m", {"merlon_m": 0.5, "pitch_m": 0.9}),
    ("a crenellated cresting painted", {"painted": True}),
    ("a crenellated cresting joined", {"joined": True}),
    ("a crenellated cresting sized as a fret", {"panel_m": 1.0}),
    ("a height under 0.15 m", {"height_m": 0.1, "rise_m": 0.04}),
]:
    phb = copy.deepcopy(ph)
    cresting(phb).update(patch)
    try:
        KP.from_phase(phb, st)
        check(False, f"{why} is refused")
    except (MD.ParamError, KP.ParamError, ValueError) as e:
        check("cresting" in str(e), f"{why} is refused ({str(e)[:90]})")

phb = copy.deepcopy(ph)
c = cresting(phb)
c.pop("pattern")
c["height_m"] = 0.3
try:
    KP.from_phase(phb, st)
    check(False, "merlons named without the crenellated pattern are refused")
except (MD.ParamError, KP.ParamError, ValueError) as e:
    check("crenellated" in str(e), f"merlons named without the crenellated pattern are refused ({str(e)[:90]})")

# -- without the pattern: the kit's iron, as before ---------------------------------------------
phb = copy.deepcopy(ph)
cresting(phb).clear()
cresting(phb).update({"height_m": 0.3, "inset_m": 0.08})
a0 = K1.build(KP.from_phase(phb, st), SID)
check(all("posts" in r and "pattern" not in r for r in a0.deck["cresting"]),
      "a cresting naming no pattern is K10's iron cresting, as before")

print(f"\n{'FAIL' if failures else 'PASS'} — deck crenellation: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
