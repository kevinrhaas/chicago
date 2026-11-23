#!/usr/bin/env python3
"""T-3713: a mansard crown over a pavilion may carry iron cresting round its own deck.

The Armour photograph of 2115 Prairie shows the pavilion's taller mansard crown with a rail of
iron cresting round its deck, as the main deck has; K01 dressed the main deck only. This holds
the kit and the record to it:

  * `mansard.crown.cresting` (height_m 0.3-1.0, inset_m 0.03-0.3, nothing else) resolves onto the
    crown's own curb — its fascia's rectangle drawn in by its lower faces' run — at its curb height;
  * a crown cresting on a house whose main deck is not dressed is refused;
  * 2115's build lays a rail on all four sides of the crown's curb, each a K10 iron cresting
    standing on the crown's deck, its top the record's height over the deck;
  * the main deck's own cresting is built exactly as without it.

    python3 tools/test_k01_crown_cresting.py
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

SID = "armour_house_2115_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]


def crown(phase):
    return phase["form"]["mansard"]["value"]["crown"]


# -- the record ---------------------------------------------------------------------------------
check(crown(ph).get("cresting") == {"height_m": 0.6, "inset_m": 0.08}, "2115's crown names its cresting")
p = KP.from_phase(ph, st)
cr = p.mansard["crown"]
cd = cr["deck"]
run = cr["lower_rise_m"] / math.tan(math.radians(cr["lower_pitch_deg"]))
co = cr["overhang_m"]
want = [cr["x0"] - co + run, cr["x1"] + co - run, -(cr["z1"] + co - run), -(cr["z0"] - co + run)]
check(all(abs(a - b) < 1e-3 for a, b in zip(cd["curb"], want)),
      f"the crown's curb is its fascia drawn in by its faces' run ({cd['curb']})")
check(cd["curb_m"] == cr["curb_m"] and cd["curb_m"] > p.mansard["curb_m"], "the crown's deck stands at its own, higher curb")

# -- the build ----------------------------------------------------------------------------------
a = K1.build(p, SID)
runs = a.deck["crown"]["cresting"]
check(sorted(r["side"] for r in runs) == ["north", "rear", "south", "street"], f"a rail on all four sides ({len(runs)})")
u0, u1, v0, v1 = cd["curb"]
check(all(r["from_m"] >= (u0 if r["side"] in ("south", "north") else v0) + MD.CROWN_STOP_M - 1e-3
          and r["to_m"] <= (u1 if r["side"] in ("south", "north") else v1) - MD.CROWN_STOP_M + 1e-3 for r in runs),
      "each run stops short of the crown's corners")
check(all(r["posts"] >= 2 for r in runs), "each run is the kit's iron, on posts")
main = a.deck["cresting"]
check(bool(main) and all(r.get("posts") for r in main), "the main deck keeps its own cresting")

# -- without it: the main deck as before --------------------------------------------------------
phb = copy.deepcopy(ph)
crown(phb).pop("cresting")
pb = KP.from_phase(phb, st)
check("deck" not in pb.mansard["crown"], "a crown naming no cresting carries no deck dress")
a0 = K1.build(pb, SID)
check("crown" not in a0.deck and a0.deck["cresting"] == main, "the main deck's cresting is built exactly as with it")

# -- refusals -----------------------------------------------------------------------------------
for why, patch in [("a rail under 0.3 m", {"height_m": 0.2}), ("a rail over 1 m", {"height_m": 1.2}),
                   ("an inset past 0.3 m", {"inset_m": 0.4}), ("a pattern it does not build", {"pattern": "fret"})]:
    phb = copy.deepcopy(ph)
    crown(phb)["cresting"] = {"height_m": 0.6, "inset_m": 0.08, **patch}
    try:
        KP.from_phase(phb, st)
        check(False, f"{why} is refused")
    except (MD.ParamError, KP.ParamError, ValueError) as e:
        check("crown.cresting" in str(e), f"{why} is refused ({str(e)[:90]})")
phb = copy.deepcopy(ph)
phb["form"]["mansard"]["value"].pop("deck")
try:
    KP.from_phase(phb, st)
    check(False, "a crown cresting over an undressed main deck is refused")
except (MD.ParamError, KP.ParamError, ValueError) as e:
    check("mansard.deck" in str(e), f"a crown cresting over an undressed main deck is refused ({str(e)[:90]})")

print(f"\n{'FAIL' if failures else 'PASS'} — crown cresting: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
