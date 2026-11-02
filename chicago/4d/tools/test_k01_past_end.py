#!/usr/bin/env python3
"""T-1890: a wing's shallow projection may run past its wall's end onto the next wing's wall.

HABS photograph 2 (1965) of 1801 Prairie puts the east range's frontispiece on an axis about
1.15 m east of where r3b's 18th Street wall could hold it: the print's straddles the 1911
sheet's junction of r3b and r2, and nothing on the print marks that junction (the two ranges
stand on one wall line, at one height, in one walling). This holds the kit and the record to
it:

  * `bays[].past_end` ("left" or "right", read from outside as the wall is) lets a shallow
    full-height projection on a wing's south or north wall run past that end onto the wall of
    the wing beyond, up to PAST_END_M, when that wing stands on the same wall line on the same
    floors to the same wall top;
  * the stretch it covers on that wall is cut out of it (no wall face stands behind it), as a
    bay's own wall is;
  * refused: on a deep projection, onto a wing on other floors (the junction would show), past
    PAST_END_M, an end it does not know, where no wing stands beyond, and within BAY_PIER_M of
    the other wall's lights or bays; without it, a bay still may not run past its corner;
  * 1801's p_door: at s 0.65 on r3b's wall, 0.85 m onto r2's.

    python3 tools/test_k01_past_end.py
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

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]


def bay_of(phase, bid="p_door"):
    return next(b for b in phase["form"]["bays"]["value"] if b["id"] == bid)


def wing_of(phase, wid):
    return next(w for w in phase["form"]["rear_wings"]["value"] if w["id"] == wid)


rec = bay_of(ph)
check(rec["wall"] == "k01.wall.wing.r3b.south" and rec["s_m"] == 0.65 and rec.get("past_end") == "left",
      f"1801's p_door stands at s 0.65 on r3b's 18th Street wall, past its left end ({rec['s_m']}, {rec.get('past_end')})")

p = KP.from_phase(ph, st)
b = next(x for x in p.bays if x["id"] == "p_door")
check(tuple(b["span_m"]) == (-0.85, 2.15), f"its span on r3b's wall runs 0.85 m past the end ({b['span_m']})")
check(b.get("past_end") == {"wing": "r2", "wall": "k01.wall.wing.r2.south", "span_m": (8.55, 9.4)},
      f"it covers r2's wall from s 8.55 to its end at 9.4 ({b.get('past_end')})")
check(KP.PAST_END_M == 1.5, "a face runs at most 1.5 m onto the next wing's wall")
others = [x["id"] for x in p.bays if x.get("past_end") and x["id"] != "p_door"]
check(not others, f"no other bay of 1801 runs past its wall's end ({others})")


# -- the build: nothing stands in r2's wall plane behind the overrun --------------------------
def in_plane(params, x0=-9.3, x1=-8.55):
    """Triangles lying in the 18th Street wall plane (z = -v0 = 0) over r2's covered stretch."""
    a = K1.build(params, SID)
    n = 0
    for prim in a.prims.values():
        P, idx = prim.pos, prim.idx
        for t in range(0, len(idx), 3):
            vs = [P[idx[t + k]] for k in range(3)]
            if all(abs(v[2]) < 1e-4 for v in vs):
                cx, cy = sum(v[0] for v in vs) / 3, sum(v[1] for v in vs) / 3
                if x0 < cx < x1 and 0.2 < cy < 6.0:
                    n += 1
    return n


check(in_plane(p) == 0, "r2's wall is cut behind the frontispiece's overrun (no face in its plane there)")
p_uncut = KP.from_phase(ph, st)
for x in p_uncut.bays:
    if x["id"] == "p_door":
        x["past_end"] = None
check(in_plane(p_uncut) > 0, "with the cover dropped, r2's walling stands there (the count above measures something)")


# -- refusals ---------------------------------------------------------------------------------
def refused(mutate, why, key):
    phb = copy.deepcopy(ph)
    mutate(phb)
    try:
        KP.from_phase(phb, st)
        check(False, f"{why} is refused")
    except (KP.ParamError, ValueError) as e:
        check(key in str(e), f"{why} is refused ({str(e)[:110]})")


refused(lambda f: bay_of(f).pop("past_end"), "a bay past its wall's corner without past_end", "closer than")
refused(lambda f: bay_of(f).update(past_end="up"), "an end it does not know", "past_end is 'left' or 'right'")
refused(lambda f: bay_of(f)["plan"].pop("shallow"), "past_end on a deep projection", "past_end is 'left' or 'right'")
refused(lambda f: bay_of(f).update(s_m=-0.2), "a face run 1.7 m onto the next wall", "0-1.5 m")
refused(lambda f: wing_of(f, "r2").update(floor_m=0.8, stacks=[]), "onto a wing on other floors",
        "the junction would show")
refused(lambda f: bay_of(f).update(s_m=3.25, past_end="right"), "onto r3, the gabled section on other floors",
        "the junction would show")


def r2_light_near(f):
    w = wing_of(f, "r2")
    w["windows"] = {**w["windows"], "south": [8.2]}


refused(r2_light_near, "within 0.3 m of a light on the wall it runs onto", "within 0.3 m of its light")


def r2_bay_near(f):
    bay_of(f, "p_east_gable")["s_m"] = 6.9


refused(r2_bay_near, "within 0.3 m of a bay on the wall it runs onto", "within 0.3 m of p_east_gable")

print(f"\n{'FAIL' if failures else 'PASS'} — a wing projection past its wall's end: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
