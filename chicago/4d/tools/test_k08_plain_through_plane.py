#!/usr/bin/env python3
"""T-3616: a K08 light may be PLAIN, and near the ends of a round tower standing into its wall,
over the eave, THROUGH-PLANE.

2011 Prairie's turret carries a band of small square lights round its top stage. The Chicagology
photograph (from the north-west) and the Inland Architect plate of February 1895 (from the
south-west) each show three of them, about 1.0 m apart, cut square in the stone with no sill or
lintel of their own, and between them they run from one of the drum's junctions with the front
to the other. The kit could not build that: a K06 light's projecting sill and lintel cost so much
that three of them filled the tower's light-tier budget, and a light near the junction of a
tower whose centre stands inside its wall (2011's, 0.8 m in) was refused, its recess running
behind the wall's face. This holds the kit and the record to what the ticket says:

  * 2011's band is five plain lights evenly round the drum, the end two through-plane, and the
    tower passes check_bay_kit with them at both tiers, inside its budgets;
  * a plain light keeps its reveal, frame, sashes and glass and of its sill only the top inside
    the reveal (nothing proud of the face), and has no head band; a kit light keeps both;
  * a through-plane light's recess runs behind the wall plane inside a hole its host opens
    (`host_holes`), and the gate refuses it when the hole is taken away, and refuses a plain
    light's recess behind the plane when it is not marked;
  * the record is refused a plain light with a dressing or no reason, and a through-plane light
    that is not plain, not on an inset round tower, or with its sill more than 0.5 m under the
    eave.

    python3 tools/test_k08_plain_through_plane.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402
import check_bay_kit as C  # noqa: E402

SID = "house_2011_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][0]


def turret_variant(st=None, phase=None):
    if st is None:
        st, phase = record()
    return next(b for b in KP.from_phase(phase, st).bays if b["id"] == "turret")["variant"]


def refused(mutate, what):
    st, phase = record()
    e = next(b for b in phase["form"]["bays"]["value"] if b["id"] == "turret")
    mutate(e)
    try:
        KP.from_phase(phase, st)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what}")


data = K8.load()
v = turret_variant()
band = v["storeys"][-1]["windows"]
angles = sorted(a for w in band for a in w["at_deg"])
check(angles == [-57, -28.5, 0, 28.5, 57], f"2011's band is five lights at -57, -28.5, 0, 28.5, 57 (is {angles})")
check(all(w.get("plain") for w in band), "every band light is plain")
thru = sorted(a for w in band if w.get("through_plane") for a in w["at_deg"])
check(thru == [-57, 57], f"the end two are through-plane (are {thru})")

full = K8.build_variant(v, data, "full", board=True)
light = K8.build_variant(v, data, "light", board=False)
fails = C.check_variant(v, data, full, light)
check(not fails, f"the turret passes check_bay_kit at both tiers ({fails[:2]})")
cap = data["costs"]["max_triangles"]
check(K8.triangles(full) <= cap["full"] and K8.triangles(light) <= cap["light"],
      f"inside its budgets: {K8.triangles(full)} / {K8.triangles(light)} against {cap['full']} / {cap['light']}")
check(len(full.host_holes) == 2, f"its host opens one hole for each through-plane light ({len(full.host_holes)})")
recs = [w for w in full.windows if w.get("through_plane")]
check(len(recs) == 2 and all(min(p[1] for p in w["footprint"]) < -0.01 for w in recs),
      "each through-plane light's recess runs back behind the wall plane")

# a plain light against a kit light: no head band, nothing of its sill proud of the face
w0 = {"opening": "k06.opening.sash_2over2_flat", "clear_width_m": 0.55, "clear_height_m": 0.8, "sill_m": 0.25}
kit = K8.window(w0, 0.0, 0.0, 0.55)
plain = K8.window({**w0, "plain": True}, 0.0, 0.0, 0.55)
check(len(kit.prims["head"].idx) > 0 and len(plain.prims["head"].idx) == 0, "a plain light has no head band")
check(any(p[2] > 1e-6 for p in kit.prims["sill"].pos) and plain.prims["sill"].idx
      and all(p[2] <= 1e-9 for p in plain.prims["sill"].pos),
      "a plain light keeps its sill's top inside the reveal and nothing proud of the face")
check(all(len(kit.prims[r].idx) == len(plain.prims[r].idx) for r in ("reveal", "frame", "glass_outer", "backing")),
      "a plain light's reveal, frame, glass and recess are the kit light's")

# the gate: a through-plane light with its host's hole taken away; an unmarked one behind the plane
holed = K8.build_variant(v, data, "full", board=True)
holed.host_holes = []
check(any(f.startswith("through:") for f in C.rule_through(holed)), "the gate refuses a through-plane recess with no hole")
bare = copy.deepcopy(v)
for w in bare["storeys"][-1]["windows"]:
    w.pop("through_plane", None)
bb = K8.build_variant(bare, data, "full", board=True)
check(any("behind" in f for f in C.check_variant(bare, data, bb)), "an unmarked light's recess behind the plane is refused")

# the record
refused(lambda e: e["storeys"][-1]["windows"][0].update(plain="yes"), "plain must be true")
refused(lambda e: e["storeys"][-1]["windows"][0].update(shutters={"width_m": 0.3, "louvre_m": 0.1}),
        "a plain light with a dressing")
refused(lambda e: e["storeys"][-1]["windows"][0].pop("why_not_ordinary"), "a plain light that does not say why")
refused(lambda e: e["storeys"][-1]["windows"][1].pop("plain"), "a through-plane light that is not plain")
refused(lambda e: e["plan"].update(centre_proud_m=0.3), "a through-plane light on a tower standing proud of its wall")
refused(lambda e: e["storeys"][-1]["windows"][1].update(sill_m=-0.4), "a through-plane light more than 0.5 m under the eave")
refused(lambda e: e["storeys"][1]["windows"][0].update(through_plane=True, plain=True),
        "a through-plane light in a storey under the eave")

print()
if failures:
    print(f"FAIL — {len(failures)} check(s) failed")
    sys.exit(1)
print("PASS — a K08 light may be plain, and through-plane over the eave on an inset round tower (T-3616)")
