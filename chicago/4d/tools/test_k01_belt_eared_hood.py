#!/usr/bin/env python3
"""T-1881: 1729 Prairie's belt course and its dormers' eared hoods.

Taylor's photograph no. 1445 and the 1890 Albertype plate draw the Pullman house with a deep
moulded belt course under the second storey's sills, round the front, its projections and the
18th Street flank, and every dormer under an eared architrave and hood. This holds the kit and the
record to what the ticket built:

  * `street_front_pavilions.belt` takes bed_m, a profile from the wall's face at its bed back to
    the wall at its top, and runs (a wall and a stretch of it); a profile that turns back down,
    stands more than 0.3 m out or runs through an opening is refused;
  * a run's path steps out round every square projection on it and, at a projection flush with
    the run's end, carries on along the projection's face to the corner;
  * a round dormer may name `eared_hood` (band_m, proud_m, ear_m, drop_m, an optional rise_m)
    inside its bounds, and on no other head; its solid is closed, stands proud_m out of the face
    and reaches ear_m past the band each side;
  * an eared hood may carry a broken `pediment`: two closed raking arms standing further out
    than the hood, never in the light, under the crown; one that would close over the crown is
    refused, and on 1729 the large Prairie dormer alone carries one;
  * 1729's record builds a belt with a break over its corner pier and every dormer hooded;
  * a square projection's own mansard may carry `mansard_dormers` (the main mansard's round
    dormer, at_m from the front's centre): one on a projection with no mansard, one crossing the
    face's hips, two meeting and one whose head meets the curb are refused; 1729's forward block
    carries one and its 18th Street pavilion two, built as stone faces on the projections' fronts.

    python3 tools/test_k01_belt_eared_hood.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k01_pavilions as PV  # noqa: E402
from archetypes import k05_roofs as k5  # noqa: E402
from archetypes import k10_frontage  # noqa: E402

SID = "pullman_house_1729_prairie"
PROFILE = [[0, 0], [0.1, 0], [0.17, 0.2], [0.17, 0.32], [0.07, 0.36], [0.07, 0.9], [0, 0.95]]
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def refused(fn, what):
    try:
        fn()
    except (PV.ParamError, KP.ParamError):
        check(True, what)
        return
    check(False, what)


class _Op:
    def __init__(self, wall, s, sill, head):
        self.wall, self.s_m, self.sill_m, self.head_m, self.component = wall, s, sill, head, "k01.opening.sash"


def bay(wall, s0, s1, d, bid="b"):
    pts = [[-(s1 - s0) / 2, 0.0], [-(s1 - s0) / 2, d], [(s1 - s0) / 2, d], [(s1 - s0) / 2, 0.0]]
    return {"id": bid, "wall": wall, "span_m": (s0, s1), "variant": {"kind": "projection", "plan": {"points": pts}}}


def belt(spec, openings=(), bays=()):
    return PV._resolve_belt(spec, width=18.0, depth=28.0, openings=list(openings), eave=12.6, bays=bays)


FRONT = "k01.wall.street_front"
ok_spec = {"bed_m": 6.7, "profile": PROFILE, "runs": [{"wall": FRONT, "s_m": [0, 18]}]}
r = belt(ok_spec)
check(r["height_m"] == 0.95 and r["bed_m"] == 6.7, "a belt resolves its bed and its profile's height")
refused(lambda: belt({**ok_spec, "profile": [[0, 0], [0.1, 0.5], [0.1, 0.2], [0, 0.6]]}), "a profile turning back down is refused")
refused(lambda: belt({**ok_spec, "profile": [[0, 0], [0.4, 0.1], [0, 0.6]] + [[0, 0.6]]}), "a profile 0.4 m out is refused")
refused(lambda: belt(ok_spec, openings=[_Op(FRONT, 5.0, 7.2, 9.0)]), "a belt through a window is refused")
check(belt(ok_spec, openings=[_Op(FRONT, 5.0, 7.7, 9.0)]) is not None, "a belt under a window's sill is laid")
refused(lambda: belt({**ok_spec, "runs": [{"wall": FRONT, "s_m": [0, 19]}]}), "a run past its wall's end is refused")

# the path round a projection, and on along a corner projection's face to the next wall
P = type("P", (), {"depth_m": 28.0, "width_m": 18.0})()
runs = {x.name: x for x in k10_frontage.runs(P)}
r = belt(ok_spec, bays=(bay(FRONT, 2.0, 8.5, 2.95),))
path = PV.belt_path(runs[FRONT], r["runs"][0], 6.7)
plan = [(round(q[0], 3), round(q[2], 3)) for q in path]
check(plan == [(28.0, 0.0), (28.0, -2.0), (30.95, -2.0), (30.95, -8.5), (28.0, -8.5), (28.0, -18.0)],
      f"the path steps out round the forward block and back ({plan})")
south = "k01.wall.side.south"
spec2 = {"bed_m": 6.7, "profile": PROFILE, "runs": [{"wall": south, "s_m": [21.8, 28]}, {"wall": FRONT, "s_m": [0, 18]}]}
r2 = belt(spec2, bays=(bay(south, 23.05, 28.0, 1.2, "nw"),))
paths = [PV.belt_path(runs[x["wall"]], x, 6.7) for x in r2["runs"]]
joined = PV._join(r2["runs"], paths, {n: x.L for n, x in runs.items()})
plan = [(round(q[0], 3), round(q[2], 3)) for q in joined[0]]
check(len(joined) == 1 and plan[:4] == [(21.8, 0.0), (23.05, 0.0), (23.05, 1.2), (28.0, 1.2)] and plan[4] == (28.0, -18.0),
      f"a flush corner projection carries the belt round onto the front in one mitred run ({plan})")

# the eared hood: bounds, heads, and its solid
dorm = {"face": "street", "along_m": 1.5, "head": "round", "surround_m": 0.3, "face_setback_m": 0.1,
        "sash": {"variant": "k06.opening.sash_round_fanlight", "width_m": 0.8, "height_m": 1.6, "sill_m": 0.1}}
eh = {"band_m": 0.15, "proud_m": 0.08, "ear_m": 0.2, "drop_m": 0.25, "rise_m": 0.4}
got = KP._round_dormer({**dorm, "eared_hood": eh}, "d", 1.0)
check(got["eared_hood"]["rise_m"] == 0.4, "a round dormer takes an eared hood")
check("eared_hood" not in KP._round_dormer(dorm, "d", 1.0), "a dormer without one builds as before")
refused(lambda: KP._round_dormer({**dorm, "eared_hood": {**eh, "ear_m": 0.5}}, "d", 1.0), "ears 0.5 m out are refused")
refused(lambda: KP._round_dormer({**dorm, "eared_hood": {**eh, "rise_m": 0.7}}, "d", 1.0), "ears over the arch's meeting with the face are refused")
refused(lambda: KP._round_dormer({**dorm, "eared_hood": {**eh, "bands": 1}}, "d", 1.0), "an unknown key is refused")


class _Host:
    EAR_BED_M = K1.Assembly.EAR_BED_M
    HOOD_BACK_M = K1.Assembly.HOOD_BACK_M
    PEDIMENT_BACK_M = K1.Assembly.PEDIMENT_BACK_M
    dormer_broken_pediment = K1.Assembly.dormer_broken_pediment


solid = K1.Assembly.dormer_eared_hood(_Host(), got, k5, "x", 1.0, 30.0, 28.0, -1.5, 0.7, 13.0, 14.3)[0]
xs = [v[0] for pl in solid for v in pl.v]
zs = [v[2] for pl in solid for v in pl.v]
check(abs(max(xs) - 30.08) < 1e-6, f"the hood stands proud_m out of the face ({max(xs):.3f})")
check(abs((max(zs) - min(zs)) - 2 * (0.7 + 0.15 + 0.2)) < 1e-6, f"its ears reach ear_m past the band each side ({max(zs) - min(zs):.3f})")
edges = {}
for pl in solid:
    n = len(pl.v)
    for i in range(n):
        a, b = tuple(round(c, 6) for c in pl.v[i]), tuple(round(c, 6) for c in pl.v[(i + 1) % n])
        edges[(a, b)] = edges.get((a, b), 0) + 1
check(all(edges.get((b, a), 0) == c for (a, b), c in edges.items()), "the hood is one closed solid")

# the broken pediment over an eared hood (1729's large Prairie dormer)
ped = {"pitch_deg": 18, "reach_m": 1.1, "foot_m": 0.15, "depth_m": 0.15, "proud_m": 0.15}
got_p = KP._round_dormer({**dorm, "eared_hood": {**eh, "pediment": ped}}, "d", 1.0)
check(got_p["eared_hood"]["pediment"]["pitch_deg"] == 18.0, "an eared hood takes a broken pediment")
refused(lambda: KP._round_dormer({**dorm, "eared_hood": {**eh, "pediment": {**ped, "pitch_deg": 35, "depth_m": 0.4}}}, "d", 1.0),
        "a pediment whose arms meet over the crown is refused: it is not broken")
refused(lambda: KP._round_dormer({**dorm, "eared_hood": {**eh, "pediment": {**ped, "proud_m": 0.05}}}, "d", 1.0),
        "a pediment standing no further out than its hood is refused")
refused(lambda: KP._round_dormer({**dorm, "eared_hood": {**eh, "pediment": {**ped, "tympanum": 1}}}, "d", 1.0),
        "a pediment's unknown key is refused")
parts = K1.Assembly.dormer_eared_hood(_Host(), got_p, k5, "x", 1.0, 30.0, 28.0, -1.5, 0.7, 13.0, 14.3)
check(len(parts) == 3, f"the hood and the pediment's two arms ({len(parts)} solids)")
ri_p = 0.7 - K1.Assembly.EAR_BED_M
for arm in parts[1:]:
    e2 = {}
    for pl in arm:
        n = len(pl.v)
        for i in range(n):
            a, b = tuple(round(c, 6) for c in pl.v[i]), tuple(round(c, 6) for c in pl.v[(i + 1) % n])
            e2[(a, b)] = e2.get((a, b), 0) + 1
    vs = [v for pl in arm for v in pl.v]
    check(all(e2.get((b, a), 0) == c for (a, b), c in e2.items()), "an arm is one closed solid")
    check(abs(max(v[0] for v in vs) - 30.15) < 1e-6, "an arm stands its proud_m out of the face")
    check(min(((v[2] + 1.5) ** 2 + (v[1] - 14.3) ** 2) ** 0.5 for v in vs) > ri_p,
          "an arm never enters the light inside the hood's band")
    check(max(v[1] for v in vs) < 14.3 + 0.7 + 0.15, "an arm stays under the arch's crown, so the pediment is broken")

# 1729's record
st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(st["phases"][0], st)
check(bool(p.pavilions.get("belt")) and len(p.pavilions["belt"]["runs"]) == 3, "1729 lays its belt on three walls")
check(all("eared_hood" in d for d in p.mansard["dormers"]), "every one of 1729's dormers is hooded")
check(sum(1 for d in p.mansard["dormers"] if d["eared_hood"].get("pediment")) == 1,
      "1729's large Prairie dormer, and it alone, carries the broken pediment")
check(p.mansard.get("dormer_fabric") == "front_stone", "1729's dormers are faced in its brownstone")

# a square projection's own mansard dormers
spec = {"variant": "k06.opening.sash_round_fanlight", "width_m": 0.7, "height_m": 1.6, "sill_m": 0.1}
dorm = lambda at, **kw: {"at_m": at, "head": "round", "sash": dict(spec, **kw), "surround_m": 0.2, "face_setback_m": 0.1}
proj = {"kind": "projection", "plan": {"kind": "polyline", "points": [[-5.125, 0.0], [-5.125, 2.47], [5.125, 2.47], [5.125, 0.0]]},
        "roof": {"kind": "hip", "pitch": 0.1, "mansard": {"rise_m": 4.0, "lower_pitch_deg": 75}},
        "overrides": {"eaves": {"overhang_m": 0.35}}}
got = KP._bay_mansard_dormers({"id": "p", "mansard_dormers": [dorm(-3.425), dorm(1.975)]}, proj)
check([d["at_m"] for d in got] == [-3.425, 1.975] and got[0]["width_m"] == 1.1, "a projection's mansard takes two dormers")
refused(lambda: KP._bay_mansard_dormers({"id": "p", "mansard_dormers": [dorm(0.0)]},
                                        {**proj, "roof": {"kind": "hip", "pitch": 1.0}}), "no dormer on a projection without a mansard")
refused(lambda: KP._bay_mansard_dormers({"id": "p", "mansard_dormers": [dorm(-3.8)]}, proj), "a dormer crossing the face's hip is refused")
refused(lambda: KP._bay_mansard_dormers({"id": "p", "mansard_dormers": [dorm(0.0), dorm(0.9)]}, proj), "two dormers meeting are refused")
refused(lambda: KP._bay_mansard_dormers({"id": "p", "mansard_dormers": [dorm(0.0, height_m=2.4, sill_m=0.6)]},
                                        {**proj, "roof": {"kind": "hip", "pitch": 0.1, "mansard": {"rise_m": 2.5, "lower_pitch_deg": 75}}}),
        "a dormer whose head meets the curb is refused")
bays_ = {b["id"]: b for b in p.bays}
check(len(bays_["p_forward"].get("mansard_dormers", ())) == 1 and len(bays_["p_18th"].get("mansard_dormers", ())) == 2,
      "1729's forward block carries one dormer and its 18th Street pavilion two")
check(not any(d["face"] == "street" and d["along_m"] < 2.0 for d in p.mansard["dormers"]),
      "1729's north-west dormer no longer stands on the main mansard behind the forward block")
asm = K1.build(p, SID)
face = asm.prims["dormer_stone"].pos
fw = [q for q in face if abs(q[0] - 30.92) < 0.03 and -5.0 < q[2] < -3.4]
pv = [q for q in face if abs(q[2] + 20.62) < 0.03 and (17.0 < q[0] < 18.5 or 11.6 < q[0] < 13.1)]
check(len(fw) > 20, f"the forward block's dormer face stands on its front ({len(fw)} vertices)")
check(len(pv) > 40, f"the pavilion's two dormer faces stand on its front ({len(pv)} vertices)")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall belt, eared-hood and projection-dormer checks pass")
