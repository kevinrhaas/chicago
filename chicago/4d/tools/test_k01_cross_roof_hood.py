#!/usr/bin/env python3
"""T-1890: a mansard deck's cross roof may end under a slated HOOD, its finial on the apex.

HABS photograph 1 of 1801 Prairie shows the south pavilion's cross roof ending where its
ridge meets the deck under a small slated pyramid, its hips white-flashed, with the finial
on it; the Taylor print, which cannot see the hood behind the ridge, puts the finial's top
about 0.5 m over where it stood on the bare ridge. This holds the kit and the record to it:

  * `mansard.deck.cross_roof.hood` takes base_m 0.5-1.6, rise_m 0.3-2.0 over the ridge and
    flashing_m 0.03-0.12 (or none); anything else, or a base past the curb, is refused;
  * the hood is centred on the ridge's end, its foot under the deck's lowest point beneath
    it (so the deck and the cross roof bury it), its apex `rise_m` over the ridge;
  * the cross roof's finial stands on the apex, and the cresting along the curb the cross
    roof runs through stops short of the hood's foot;
  * a cross roof without a hood builds exactly as before (the finial on the ridge's end);
  * 1801's hood: 1.2 m across, 0.5 m over its 16.3 m ridge, 0.06 m zinc rolls.

    python3 tools/test_k01_cross_roof_hood.py
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

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][0]


def build(phase, st):
    a = K1.build(KP.from_phase(phase, st), SID)
    return a


def deck_of(phase):
    return phase["form"]["mansard"]["value"]["deck"]


st, ph = record()
hood = deck_of(ph)["cross_roof"].get("hood")
check(hood == {"base_m": 1.2, "rise_m": 0.5, "flashing_m": 0.06},
      f"1801's cross roof carries the HABS 1 hood: 1.2 m across, 0.5 m over the ridge, 0.06 m zinc ({hood})")

# -- the record's build: the hood, the finial on it, the cresting stopped short of it ---------
a = build(ph, st)
fin = {f["corner"]: f for f in a.deck["finials"]}
cr = fin.get("cross_roof")
check(cr is not None and cr["on"] == "cross roof hood" and abs(cr["foot_m"] - (16.3 + 0.5 - MD.LET_IN_M)) < 1e-3,
      f"the cross roof's finial stands on the hood's apex, its foot let in under 16.8 m ({cr})")
hoods = [i for i in a.components.get("k01.roof.deck_hood", {}).get("instances", [])
         if i["params"].get("corner") == "cross_roof"]
check(len(hoods) == 1 and abs(hoods[0]["sockets"]["apex"][1] - 16.8) < 1e-3
      and abs(hoods[0]["sockets"]["apex"][0] - 16.0) < 1e-3,
      "one slated hood, its apex over the ridge's end at u 16.0, 16.8 m")
run = next(c for c in a.deck["cresting"] if c["side"] == "north")   # the curb the cross roof crosses
check(run["to_m"] <= 16.0 - 0.6 - MD.CORNER_CLEAR_M + 1e-3,
      f"the cresting along that curb stops short of the hood's foot (to u {run['to_m']})")

# -- the hood's foot is buried: under the deck and the cross roof everywhere ------------------
dk = KP.from_phase(ph, st).mansard["deck"]
xh = dk["cross_roof"]["hood"]
check(xh["foot_m"] < MD.deck_y(dk, 0.0) + 0.04 and xh["foot_m"] < dk["cross_roof"]["ridge_m"] - 0.6,
      f"the hood's foot ({xh['foot_m']} m) stands under the deck's curb line and the cross roof's ridge")

# -- without a hood: exactly the old build ----------------------------------------------------
ph0 = copy.deepcopy(ph)
del deck_of(ph0)["cross_roof"]["hood"]
a0 = build(ph0, st)
f0 = {f["corner"]: f for f in a0.deck["finials"]}["cross_roof"]
check(f0["on"] == "cross roof" and abs(f0["foot_m"] - (16.3 - MD.LET_IN_M)) < 1e-3,
      "a cross roof without a hood stands its finial on the ridge's end, as before")
zn = lambda asm: len(asm.prims["k04_zinc_sheet"].idx) if "k04_zinc_sheet" in asm.prims else 0
check(zn(a) - zn(a0) == 4 * 2 * 2 * 3,
      f"the hood's four hips are each rolled in zinc down both faces ({(zn(a) - zn(a0)) // 3} triangles)")

# -- refusals ---------------------------------------------------------------------------------
for bad, why in (({"base_m": 0.3, "rise_m": 0.5}, "a base under 0.5 m"),
                 ({"base_m": 1.2, "rise_m": 2.5}, "a rise over 2 m"),
                 ({"base_m": 1.2, "rise_m": 0.5, "flashing_m": 0.5}, "a flashing over 0.12 m"),
                 ({"base_m": 1.6, "rise_m": 0.5}, "a base past the curb"),
                 ({"base_m": 1.2, "rise_m": 0.5, "colour": "red"}, "an unknown key")):
    phb = copy.deepcopy(ph)
    deck_of(phb)["cross_roof"]["hood"] = bad
    try:
        KP.from_phase(phb, st)
        check(False, f"{why} is refused")
    except (MD.ParamError, KP.ParamError, ValueError) as e:
        check("cross_roof.hood" in str(e), f"{why} is refused ({str(e)[:90]})")

print(f"\n{'FAIL' if failures else 'PASS'} — cross roof hood: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
