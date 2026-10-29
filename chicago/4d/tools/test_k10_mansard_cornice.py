#!/usr/bin/env python3
"""T-3002: 1801 Prairie's carved stone, held on its record.

  * K10's moulded stone cornice stands under a mansard when the record names the walls it
    runs round: one course, its top the K05 soffit, turned at the corner between them and
    dying into every K08 bay on them that stands up to it (the bow, the tower, both
    pavilions); refused under a mansard without `walls`, with walls that are not one stretch
    round the house, and `walls` under any other roof;
  * a K08 storey's head frieze lays a band and a roundel on the run it names, and is
    refused where it would stand on a window's head;
  * a K08 coped gable's panel fills the tympanum inside the copings' beds, with its leaves,
    and the light tier keeps the panel and drops the relief.

    python3 tools/test_k10_mansard_cornice.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402
from archetypes import k10_frontage as K10  # noqa: E402

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


def refused(change, why, says, err=(KP.ParamError, ValueError)):
    st, phase = record()
    change(phase["form"])
    try:
        K1.build(KP.from_phase(phase, st), SID)
    except err as e:
        check(says in str(e), f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


st, phase = record()
a = K1.build(KP.from_phase(phase, st), SID)
wh = a.wall_head
check(wh.get("walls") == ["k01.wall.side.south", "k01.wall.street_front", "k01.wall.side.north"],
      f"the cornice runs the 18th Street flank, the avenue front and the south wall ({wh.get('walls')})")
check(abs(wh["cornice_m"][1] - a.soffit_m) < 1e-6, f"its top is the K05 soffit ({wh['cornice_m']} against {a.soffit_m:.3f})")
check(set(wh["dies_into"]) >= {"front_bow", "p_south", "p_flank", "tower", "south_bay"},
      f"it dies into the bow, both pavilions, the tower and the south bay ({wh['dies_into']})")
# T-1890: the south pavilion's chamfer cuts the south wall's corner back, so the course starts
# on that wall where the canted face meets it, not out in the air over the lost corner
behind = KP.chamfer_spans(a.p.bays, a.p.depth_m, a.p.width_m)["k01.wall.side.north"][1]
start = a.p.depth_m + a.p.width_m + float(behind)
check(any(abs(s0 - start) < 1e-3 for s0, _ in wh["stretches"])
      and not any(s0 < start - 1e-3 < s1 and s0 > a.p.depth_m + a.p.width_m - 1e-3 for s0, s1 in wh["stretches"]),
      f"the south wall's course starts {behind} m back, where the chamfer meets it ({wh['stretches']})")
check(abs(wh["cornice_m"][1] - 8.7) < 0.01, f"its top stands level with the bow's cornice, 8.7 m ({wh['cornice_m'][1]})")
check(K10._chain(["k01.wall.street_front", "k01.wall.side.south"]) == ["k01.wall.side.south", "k01.wall.street_front"],
      "the walls are taken in the order a run round the house meets them")
check(K10._chain(["k01.wall.street_front", "k01.wall.rear_service"]) is None, "two walls apart are no one stretch")

refused(lambda f: f["wall_head"]["value"].pop("walls"), "a stone cornice under a mansard with no walls", "names the walls")
refused(lambda f: f["wall_head"]["value"].update(walls=["k01.wall.street_front", "k01.wall.rear_service"]),
        "walls that are not one stretch round the house", "each next to")


def head_on_window(f):
    ps = next(b for b in f["bays"]["value"] if b["id"] == "p_south")
    ps["storeys"][2]["head_frieze"].update(from_m=3.5, to_m=4.5)


refused(head_on_window, "a head frieze over a pair whose head stands at 3.55 m", "stands on a head")

ps = next(b for b in a.p.bays if b["id"] == "p_south")
for tier in ("full", "light"):
    bay = K8.Bay(ps["variant"], K8.load(), tier).build(board=False)
    pn, hf = bay.meta["roof"].get("panel"), bay.meta.get("head_frieze")
    check(pn is not None and hf is not None, f"{tier}: the gable carries its panel and the face its head frieze")
    if tier == "full":
        check(pn["leaves"] >= 6 and "roundel" in hf, f"full: the panel's relief has leaves ({pn['leaves']}) and the band its roundel")
    else:
        check(pn["leaves"] == 0 and "roundel" not in hf, "light: the panel and the band stay, the relief and the roundel go")

# T-3186: 1901 Prairie's frieze and carved blocks under the moulded cornice round its mansard
REAM = "ream_house_1901_prairie"


def ream(change=None):
    st = json.loads((ROOT / "data" / "structures" / f"{REAM}.json").read_text())
    ph = st["phases"][-1]
    if change:
        change(ph["form"]["wall_head"]["value"])
    return K1.build(KP.from_phase(ph, st), REAM)


rw = ream().wall_head
check(rw.get("frieze_m") == [round(rw["cornice_m"][0] - 0.42, 4), rw["cornice_m"][0]],
      f"1901: the frieze stands 0.42 m under the cornice's foot ({rw.get('frieze_m')})")
bl = rw.get("blocks") or {}
check(bl.get("count", 0) >= 50 and bl.get("left_out") == 1,
      f"1901: a course of blocks round the front, the canted corner and both flanks, one left out at a stack ({bl})")
check(bl.get("y_m", [0, 0])[1] > rw["cornice_m"][0] and bl["y_m"][0] > rw["frieze_m"][0],
      f"1901: the blocks stand on the frieze, their tops under the corona ({bl.get('y_m')})")


def ream_refused(change, why, says):
    try:
        ream(change)
    except (KP.ParamError, ValueError) as e:
        check(says in str(e), f"1901: {why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"1901: {why}: refused")


ream_refused(lambda v: v["blocks"].update(projection_m=0.3), "blocks reaching past the corona's soffit", "corona's soffit")
ream_refused(lambda v: v["frieze"].update(height_m=0.6), "a frieze down onto the chamber heads", "reaches the stone cornice's frieze")
ream_refused(lambda v: v["blocks"].update(spacing_m=3.0), "blocks 3 m apart", "spacing_m 0.4-1.6")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall ok")
