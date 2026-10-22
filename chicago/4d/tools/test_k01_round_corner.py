#!/usr/bin/env python3
"""T-3006: K01 rounds a corner of the front block, held on 1811 Prairie's record
(T-3007: and its oriel carried out over the round).

The 1888 Inland Architect plate shows 1811's entrance block turning its south corner
(K01's 'north') on a round of about 0.9 m, and its corner downpipe running down the round.
So:

  * `round_corner` lays a quarter round tangent to the street front and the side wall, in
    the front's stone, coursed on the front's beds and corbelled out to the square in its
    last course; the front and the side wall stop at its tangents up to the stone's top;
  * a front pipe may stand behind the front's plane only on the round, clear of its face;
  * every refusal round it says why.

    python3 tools/test_k01_round_corner.py
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

SID = "coleman_ames_house_1811_prairie"
failures = []


def check(ok, what):
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok:
        failures.append(what)


def refused(rec, why, needle):
    try:
        KP.from_phase(rec["phases"][0], rec)
    except KP.ParamError as e:
        check(needle in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (it was accepted)")


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(st["phases"][0], st)
check(p.round_corner == {"corner": "north", "radius_m": 0.9}, "1811's record rounds K01's north corner on 0.9 m")
a = K1.build(p, SID)
rc = a.components.get("k01.wall.round_corner")
check(rc is not None and len(rc["instances"]) == 1, "the build lays one k01.wall.round_corner")
inst = rc["instances"][0]["params"] if rc else {}
check(abs(inst.get("length_m", 0) - 0.9 * math.pi / 2) < 1e-3 and abs(inst.get("height_m", 0) - a.front_ytop) < 1e-3,
      "the round is a quarter circle to the stone's top")
check(a.front_courses[-1][0] < a.front_ytop - 0.2, "the corbel takes the front's last course")

# the round's stones stand on the curve: every rough stone vertex near the corner sits on
# or outside the radius, inside its rock face, and none inside the square corner's walls
cu, cv = KP.round_corner_spans(p.round_corner, p.depth_m, p.width_m)["centre"]
stone = a.prims["rough_stone_trim"].pos
near = [q for q in stone if q[0] > cu - 1e-6 and -q[2] > cv - 1e-6 and q[1] < a.front_courses[-1][0] - 1e-6]
rad = [math.hypot(q[0] - cu, -q[2] - cv) for q in near]
check(bool(near) and min(rad) > 0.9 - 0.02 and max(rad) < 0.9 + 0.05,
      f"the round's rock faces lie on its radius ({min(rad, default=0):.3f}-{max(rad, default=0):.3f} m)")

# T-3007: the oriel reaches onto the round from the flat front, its south return splayed back
# to the wall plane 0.23 m off the curve, and its back is closed on that plane over the round
ori = next(b for b in p.bays if b["id"] == "oriel")
gap = KP.round_corner_gap(p.round_corner, p.depth_m, p.width_m, ori)
check(gap is not None and gap[0] == 9.5 and abs(gap[1] - 10.1) < 1e-6 and 0.2 < gap[2] < 0.25,
      f"the oriel stands over the round from its tangent to its junction, {gap and gap[2]} m off the curve")
bo = [q for q in a.prims["bay_stone"].pos] if "bay_stone" in a.prims else []
check(any(abs(q[0] - p.depth_m) < 1e-6 and 9.5 - 1e-6 <= -q[2] <= 10.1 + 1e-6 and q[1] > 5.0 for q in bo),
      "its back is closed on the wall plane over the round")

# the house without its round: the front and the side wall meet square, nothing else moves
plain = copy.deepcopy(st)
form = plain["phases"][0]["form"]
del form["round_corner"]
form["rainwater"]["value"]["front_pipes"][1].update({"s_m": 10.25, "proud_m": 0.0})
b = K1.build(KP.from_phase(plain["phases"][0], plain), SID)
check("k01.wall.round_corner" not in b.components, "a record without round_corner lays no round")

# refusals
def variant(fn):
    r = copy.deepcopy(st)
    fn(r["phases"][0]["form"])
    return r

refused(variant(lambda f: f["round_corner"]["value"].update(radius_m=3.0)), "a radius past a quarter of the block",
        "radius_m")
refused(variant(lambda f: f["round_corner"]["value"].update(shape="ogee")), "an unknown key", "takes corner")
refused(variant(lambda f: f["round_corner"]["value"].update(corner="east")), "a corner K01 does not name",
        "takes corner")
refused(variant(lambda f: f["rainwater"]["value"]["front_pipes"][1].update(proud_m=0.0)),
        "a pipe before the front's plane over the round", "stands on the round")
refused(variant(lambda f: f["rainwater"]["value"]["front_pipes"][1].update(proud_m=-0.45)),
        "a pipe buried in the round", "stands on the round")
refused(variant(lambda f: f["rainwater"]["value"]["front_pipes"][0].update(proud_m=-0.2)),
        "a pipe behind the flat front", "stands on the round")
refused(variant(lambda f: f["round_corner"]["value"].update(radius_m=1.5)), "a bay standing on the round",
        "the bay oriel")
refused(variant(lambda f: f.pop("stone_front")), "a round with no stone front", "stone")


def oriel_plan(f, pts, asym=True):
    e = next(b for b in f["bays"]["value"] if b["id"] == "oriel")
    e["plan"] = {"kind": "polyline", "points": pts, **({"asymmetric": True} if asym else {})}


refused(variant(lambda f: f["round_corner"]["value"].update(radius_m=1.2)),
        "an oriel whose junction stands 0.41 m off a 1.2 m round", "within 0.3 m of the curve")
refused(variant(lambda f: oriel_plan(f, [[-1.08, 0.0], [-1.08, 0.6], [1.79, 0.6], [2.2, 0.0]], asym=False)),
        "an asymmetric oriel plan that does not say so", "sizes its oriel's plan")

if failures:
    print(f"test_k01_round_corner: {len(failures)} failure(s)")
    sys.exit(1)
print("test_k01_round_corner: all passed")
