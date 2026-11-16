#!/usr/bin/env python3
"""T-1896: 1827 Prairie's sign-off — three kit additions the Doane photograph asked for.

  * K05's hipped crown may stand its sides on a ledge of its cornice (`side_inset_m`) and
    close to one point (`point`), its back pitched to meet the street end there; a crown
    naming neither builds exactly as before;
  * K08 carves roundels on a storey's wall (`storeys[].roundels`), clear of the run's ends,
    the band over the storey and every light and hood of that storey it shares width with;
  * K01's arcaded porch may stand an arched end's back on a column against the wall in place
    of its respond (`arches.end_columns`) and lay a low parapet across the end between its
    pedestals (`arches.end_parapet_m`);
  * refused: an inset past a quarter of the crown's width, a point whose back would pitch
    past K05's slated range, a point that is not a boolean, a roundel into a light or with an
    unknown key, end columns or a parapet on a porch with no arched end, a parapet over the
    pedestals;
  * 1827's record carries all three, and its house builds.

    python3 tools/test_k01_doane_crown_porch_roundel.py
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
from archetypes import k05_roofs as K5  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402

SID = "doane_house_1827_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def refused(fn, what):
    try:
        fn()
    except (KP.ParamError, ValueError):
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what}")


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def form(s):
    return s["phases"][0]["form"]


def params(s):
    return KP.from_phase(s["phases"][0], s)


def build(s):
    made = []
    init = K8.Bay.__init__

    def hook(self, *a, **k):
        init(self, *a, **k)
        made.append(self)
    K8.Bay.__init__ = hook
    try:
        K1.build(params(s), s["id"])
    finally:
        K8.Bay.__init__ = init
    return made


def edited(fn):
    s = copy.deepcopy(st)
    fn(form(s))
    return s


# -- the crown --------------------------------------------------------------------------------
p = params(st)
cr = p.mansard["crown"]
check(cr.get("point") is True and cr.get("side_inset_m") == 1.35,
      "1827's crown stands its sides 1.35 m in on its cornice and closes to a point")
check(45.0 < cr["back_pitch_deg"] <= 65.0, f"its back pitched in K05's slated range ({cr['back_pitch_deg']:.2f})")
check(abs(cr["ridge_x_m"][0] - cr["ridge_x_m"][1]) < 1e-9, "its ridge has no length: one point")
check(abs(cr["ridge_m"] - (cr["eave_m"] + 15.1 - 12.1)) < 0.1,
      f"its point about 3.0 m over its cornice, as the print's ({cr['ridge_m'] - cr['eave_m']:.2f} m)")

solid, _, meta = K5.hip_crown_element(cr["x0"], cr["x1"], cr["z0"], cr["z1"], cr["eave_m"], cr["pitch_deg"],
                                      cr["end_pitch_deg"], cr["overhang_m"], 0.2,
                                      side_inset=cr["side_inset_m"], back_deg=cr["back_pitch_deg"])
check(abs(meta["ridge_m"] - cr["ridge_m"]) < 1e-6, "the kit's point stands where the record's resolution puts it")
top = max(q[1] for pl in solid for q in pl.v)
tops = {(round(q[0], 6), round(q[2], 6)) for pl in solid for q in pl.v if abs(q[1] - top) < 1e-9}
check(len(tops) == 1, f"every slope meets at the one point ({len(tops)} top vertices)")

# a crown naming neither key builds as before: its ridge from the fascia at the side pitch
plain, _, pm = K5.hip_crown_element(0.0, 6.0, -3.0, 0.0, 10.0, 50.0, 60.0, 0.2, 0.2)
check(abs(pm["ridge_m"] - (10.0 + 1.7 * math.tan(math.radians(50.0)))) < 1e-4,
      "a crown with no ledge and no point keeps its old ridge")

refused(lambda: params(edited(lambda f: f["mansard"]["value"]["crown"].update(side_inset_m=2.0))),
        "a ledge past a quarter of the crown's width")
refused(lambda: params(edited(lambda f: f["mansard"]["value"]["crown"].update(depth_m=1.6))),
        "a point whose back would pitch past 65 degrees")
refused(lambda: params(edited(lambda f: f["mansard"]["value"]["crown"].update(point="yes"))),
        "a point that is not true or false")

# -- the roundel ------------------------------------------------------------------------------
bays = build(st)
tower = next(b for b in bays if b.v["id"].endswith("corner_tower"))
rns = tower.meta.get("roundels", [])
check(len(rns) == 2 and {r["run"] for r in rns} == {1, 2}, "the tower carries a roundel on each of its broad faces")
for r in rns:
    ws = [w for w in tower.windows if w["run"] == r["run"] and w["storey"] == 1]
    check(all(r["y_m"] - r["radius_m"] > w["y_all"][1] for w in ws),
          f"run {r['run']}'s roundel stands over its pair's hoods")


def roundel(**kw):
    def f(fm):
        tw = next(b for b in fm["bays"]["value"] if b["id"] == "corner_tower")
        tw["storeys"][1]["roundels"][0].update(**kw)
    return f


refused(lambda: build(edited(roundel(centre_m=3.0))), "a roundel into its pair's hoods")
refused(lambda: build(edited(roundel(centre_m=3.95))), "a roundel into the band over its storey")
refused(lambda: params(edited(roundel(boss_m=0.1))), "a roundel with a key it does not know")

# -- the porch --------------------------------------------------------------------------------
ar = p.door_kit["hood"]["arches"] if hasattr(p, "door_kit") else None
if ar is None:
    ar = next(v for k, v in vars(p).items() if isinstance(v, dict) and "hood" in v and "arches" in v["hood"])["hood"]["arches"]
check(ar.get("end_columns") is True and ar.get("end_parapet_m") == 0.35,
      "1827's porch stands its south arch on a column against the wall, a parapet across it")


def hood(**kw):
    def f(fm):
        fm["entrance_kit"]["value"]["k01.opening.door_leaf"]["hood"]["arches"].update(**kw)
    return f


refused(lambda: params(edited(hood(faces=["front"]))), "end columns on a porch with no arched end")
refused(lambda: params(edited(hood(end_parapet_m=0.6))), "a parapet over the pedestals")
refused(lambda: params(edited(hood(end_columns=1))), "end columns that are not true")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nPASS: 1827's crown, porch end and tower roundel hold to their kits (T-1896)")
