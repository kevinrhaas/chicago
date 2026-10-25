#!/usr/bin/env python3
"""T-3006: K01 rounds a corner of the front block, held on 1811 Prairie's record
(T-3007: and its oriel carried out over the round; T-2991: and the porch's arcade round it;
T-3129: stepped down round the curve).

The 1888 Inland Architect plate shows 1811's entrance block turning its south corner
(K01's 'north') on a round of about 0.9 m, and its corner downpipe running down the round.
So:

  * `round_corner` lays a quarter round tangent to the street front and the side wall, in
    the front's stone, coursed on the front's beds and corbelled out to the square in its
    last course; the front and the side wall stop at its tangents up to the stone's top;
  * a front pipe may stand behind the front's plane only on the round, clear of its face;
  * the porch's arcade (`entrance_kit.loggia.round_arcade`) cuts its lights through the round's
    courses between the springing's bed and the next bed over their crowns, each over a
    colonnette standing as the mouth's columns stand;
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
# (but the arcade's lights, whose reveals run into the wall: below)
cu, cv = KP.round_corner_spans(p.round_corner, p.depth_m, p.width_m)["centre"]
stone = a.prims["rough_stone_trim"].pos
ra = p.entrance_kit["loggia"]["round_arcade"]
band = a.round_arcade_band(ra, 0.9, 0.9 * math.pi / 2, a.front_courses)
near = [q for q in stone if q[0] > cu - 1e-6 and -q[2] > cv - 1e-6 and q[1] < a.front_courses[-1][0] - 1e-6
        and not band["y_lo"] - 1e-6 <= q[1] <= band["y"][1] + 1e-6]
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

# T-2991: the porch's arcade round the curve, on the plate's three colonnettes
arc_ = a.components.get("k01.wall.round_arcade")
check(arc_ is not None and len(arc_["instances"]) == 1 and arc_["instances"][0]["params"]["lights"] == 3,
      "the build lays one k01.wall.round_arcade of three lights")
check(band["y"] == (3.15, 4.05) and abs(band["s"][0]) < 1e-9 and abs(band["s"][1] - (0.9 * math.radians(44) + 0.21)) < 1e-6,
      f"its lights' band runs from the springing's bed to the first bed over the crowns, from the tangent "
      f"to past the last light ({band['y']}, {band['s']})")
inband = [q for q in stone if q[0] > cu - 1e-6 and -q[2] > cv - 1e-6 and band["y_lo"] - 1e-6 <= q[1] <= band["y"][1] + 1e-6]
rin = [math.hypot(q[0] - cu, -q[2] - cv) for q in inband]
check(bool(rin) and min(rin) > 0.9 - ra["reveal_m"] - 1e-6 and max(rin) < 0.9 + 0.05,
      f"its stones (and the rock faces beside them) lie on the round and the lights run {ra['reveal_m']} m into it "
      f"({min(rin, default=0):.3f}-{max(rin, default=0):.3f} m)")
dark = [q for q in a.prims["backing"].pos if q[0] > cu - 1e-6 and -q[2] > cv - 1e-6 and 2.9 < q[1] < 4.0]
check(len(dark) > 0 and all(abs(math.hypot(q[0] - cu, -q[2] - cv) - (0.9 - ra["reveal_m"])) < 1e-6 for q in dark),
      "each light's back stands dark at the reveal's depth")
# T-3129: the plate and the Chicagology photograph step the arcade down round the curve, so each
# light, its colonnette and the plinth band under it stand `drops_m` lower, the band's stones
# reaching down to the first bed under the lowest sill
check(ra.get("drops_m") == [0.0, 0.1, 0.2] and band["drops"] == [0.0, 0.1, 0.2] and abs(band["y_lo"] - 2.708) < 1e-3,
      f"the arcade steps down 0, 0.1 and 0.2 m round the curve, its stones from the bed at {band['y_lo']:.3f}")
sills = sorted({round(q[1], 4) for q in a.prims["backing"].pos if q[0] > cu - 1e-6 and -q[2] > cv - 1e-6 and 2.9 < q[1] < 3.2})
check(sills == [2.95, 3.05, 3.15], f"the lights' backs start at their stepped sills ({sills})")
dress = [q for q in a.prims["dress_stone"].pos if q[0] > cu + 0.05 and -q[2] > cv + 0.05]
check(any(abs(q[1] - (ra["sill_m"])) < 1e-6 for q in dress) and any(abs(q[1] - (1.35 + 0.86)) < 1e-6 for q in dress),
      "the colonnettes stand on the plinth's top under abaci at the lights' sill")

# the house without its round: the front and the side wall meet square, nothing else moves
plain = copy.deepcopy(st)
form = plain["phases"][0]["form"]
del form["round_corner"]
del form["entrance_kit"]["value"]["k01.opening.door_leaf"]["loggia"]["round_arcade"]
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
# T-2997: front_pipes[0] stands on the bay's return, so the flat-front case is a plain pipe
refused(variant(lambda f: f["rainwater"]["value"]["front_pipes"].__setitem__(
            0, {"s_m": 6.24, "head_m": 7.85, "foot_m": 0.0, "proud_m": -0.2})),
        "a pipe behind the flat front", "stands on the round")
refused(variant(lambda f: f["rainwater"]["value"]["front_pipes"][0].update(s_m=6.24)),
        "a return pipe where no projection's return stands (T-2997)", "square high-s return")
refused(variant(lambda f: f["rainwater"]["value"]["front_pipes"][0].update(proud_m=0.9)),
        "a return pipe past the return's depth (T-2997)", "square high-s return")
refused(variant(lambda f: f["round_corner"]["value"].update(radius_m=1.5)), "a bay standing on the round",
        "the bay oriel")
refused(variant(lambda f: f.pop("stone_front")), "a round with no stone front", "stone")


def arcade(f):
    return f["entrance_kit"]["value"]["k01.opening.door_leaf"]["loggia"]["round_arcade"]


refused(variant(lambda f: f.pop("round_corner")), "an arcade with no round to stand on (T-2991)",
        "stands on a rounded corner")
refused(variant(lambda f: f["entrance_kit"]["value"]["k01.opening.door_leaf"]["loggia"].pop("columns")),
        "an arcade with no mouth's columns to carry round (T-2991)", "needs columns")
refused(variant(lambda f: arcade(f).update(angles_deg=[8, 20, 44])), "lights crowding each other (T-2991)",
        "crowd each other")
refused(variant(lambda f: arcade(f).update(angles_deg=[1, 27, 44])), "a light over the front's tangent (T-2991)",
        "crowd each other")
refused(variant(lambda f: arcade(f).update(angles_deg=[8, 27, 72])), "a light's frame on the side wall (T-2991)",
        "runs onto the side wall")
refused(variant(lambda f: arcade(f).update(angles_deg=[27, 8, 44])), "angles out of order (T-2991)",
        "rising from the front's tangent")
refused(variant(lambda f: arcade(f).update(band_m=1.2)), "a plinth band deeper than the mouth's plinth (T-2991)",
        "band_m")
refused(variant(lambda f: arcade(f).update(arches="pointed")), "an unknown arcade key (T-2991)",
        "round_arcade takes")
refused(variant(lambda f: arcade(f).update(drops_m=[0.2, 0.1, 0.0])), "an arcade rising round the curve (T-3129)",
        "drops_m")
refused(variant(lambda f: arcade(f).update(drops_m=[0.0, 0.1])), "a drop missing for a light (T-3129)",
        "drops_m")
refused(variant(lambda f: f["entrance_kit"]["value"]["k01.opening.door_leaf"]["loggia"].update(v_m=[6.75, 9.8])),
        "a loggia running on past the round's tangent (T-2991)", "short of the north round's tangent")


def oriel_plan(f, pts, asym=True):
    e = next(b for b in f["bays"]["value"] if b["id"] == "oriel")
    e["plan"] = {"kind": "polyline", "points": pts, **({"asymmetric": True} if asym else {})}


refused(variant(lambda f: f["round_corner"]["value"].update(radius_m=1.2)),
        "an oriel whose junction stands 0.41 m off a 1.2 m round", "within 0.3 m of the curve")
refused(variant(lambda f: oriel_plan(f, [[-1.08, 0.0], [-1.08, 0.6], [1.79, 0.6], [2.2, 0.0]], asym=False)),
        "an asymmetric oriel plan that does not say so", "sizes its oriel's plan")

# T-3133: the south flank (K01's 'north') as the Chicagology print draws it — each wing's
# flank lights round-headed in the wall's brick, and a round-headed basement light under each
for w in p.rear_wings:
    flank = [o for o in w["openings"] if o.wall == f"k01.wall.wing.{w['id']}.north"]
    lights = [o for o in flank if o.component == KP.ROUND_HOODED]
    under = [o for o in flank if o.component == KP.ROUND_PLAIN]
    check(lights and not [o for o in flank if o.component not in KP.ROUND_CUT],
          f"{w['id']}'s flank lights are all round-headed ({len(lights)})")
    check(sorted(o.s_m for o in under) == sorted({o.s_m for o in lights})
          and all(o.plain and o.sill_m == 0.3 and abs(o.head_m - 1.35) < 1e-9 for o in under),
          f"{w['id']} stands a plain round-headed basement light, 0.30-1.35 m, under each flank light")
    check(all(o.component == "k01.opening.sash_flat" for o in w["openings"] if not o.wall.endswith(".north")),
          f"{w['id']}'s unseen sides keep the brick wall's own heads")
bay0 = next(b for b in st["phases"][0]["form"]["bays"]["value"] if b["id"] == "north_bay")["storeys"][0]["windows"]
check(all(abs(x["sill_m"] - 0.17) < 1e-9 and abs(x["sill_m"] + x["clear_height_m"] - 1.22) < 1e-9 for x in bay0),
      "the bay's basement lights stand on its halved plinth, their heads kept at 1.22 m (T-3133)")


def wing(f, j=0):
    return f["rear_wings"]["value"][j]


refused(variant(lambda f: wing(f).update(round_heads=["east"])), "round heads on a side with no windows (T-3133)",
        "round_heads and basement_lights name a side")
refused(variant(lambda f: wing(f)["basement_lights"]["north"].update(height_m=1.4)),
        "a basement light whose crown runs up to the first floor's sills (T-3133)", "0.45 m under the first floor")
refused(variant(lambda f: wing(f)["basement_lights"]["north"].update(sill_m=0.05)),
        "a basement light on the ground (T-3133)", "at least 0.15 m up")
refused(variant(lambda f: wing(f)["basement_lights"]["north"].update(well=True)),
        "an unknown basement light key (T-3133)", "takes sill_m, width_m and height_m")

if failures:
    print(f"test_k01_round_corner: {len(failures)} failure(s)")
    sys.exit(1)
print("test_k01_round_corner: all passed")
