#!/usr/bin/env python3
"""T-3283: a canted bay's own mansard may carry dormers (`bays[].mansard_dormers`).

The Chicago Tribune's 'Famous Homes' photograph of 29 July 1928 shows 1945 Prairie's north bay
carried up past the house's cornice under a crown of its own, two lit dormer lights in it over
the bay's pair of lights. T-1881 let a square projection's mansard carry dormers (1729's); a
canted bay's mansard (1816's, T-2964) carried none, so 1945's bay stopped under the cornice and
its two dormers stood on the house's mansard behind it. This holds the kit and the record to it:

  * a symmetrical four-point canted plan whose middle run is parallel to the wall takes
    dormers on that run, `at_m` from its centre, gabled or round-headed;
  * the hips leave the front face's corners at half the cant's turn, so the face narrows under
    the curb by the run times that half-angle's tangent (on a square projection the tangent is
    1 and the clearance is T-1881's, unchanged);
  * refused: a dormer crossing the face's hip, two that meet, one whose head meets the curb, a
    hooded head, a bay with no mansard, an unsymmetrical cant;
  * 1945's record: the north bay under its own mansard with its two dormers, the house's
    mansard with no street dormer left over the bay, and the house builds.

    python3 tools/test_k08_canted_bay_dormers.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "armour_corwith_house_1945_prairie"
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


spec = {"variant": "k06.opening.sash_2over2_flat", "width_m": 0.6, "height_m": 1.2, "sill_m": 0.15}
dorm = lambda at, **kw: {"at_m": at, "head": kw.pop("head", "gable"), "gable_pitch_deg": 45,
                         "sash": dict(spec, **kw), "surround_m": 0.15, "face_setback_m": 0.05}
cant = {"kind": "bay", "plan": {"kind": "polyline", "points": [[-2.15, 0.0], [-1.45, 0.75], [1.45, 0.75], [2.15, 0.0]]},
        "roof": {"kind": "hip", "pitch": 0.1, "mansard": {"rise_m": 3.0, "lower_pitch_deg": 80}},
        "overrides": {"eaves": {"profile": [[0.0, 0.0], [0.32, 0.36]]}}}
run_ = 3.0 / math.tan(math.radians(80))
half = 1.45 + (0.32 - run_) * math.tan(math.atan2(0.75, 0.7) / 2) - 0.3

got = KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(-0.6), dorm(0.6)]}, cant)
check([d["at_m"] for d in got] == [-0.6, 0.6] and abs(got[0]["width_m"] - 0.9) < 1e-9 and got[0]["head"] == "gable",
      "a canted bay's mansard takes two gabled dormers on its front run")
rnd = {"at_m": 0.0, "head": "round", "surround_m": 0.15, "face_setback_m": 0.05,
       "sash": dict(spec, variant="k06.opening.sash_round_fanlight", height_m=1.4)}
check(len(KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [rnd]}, cant)) == 1,
      "and a round-headed one")
check(abs(half - 1.0589) < 1e-3, f"the front face's clearance under the curb is {half:.3f} m from its centre")
edge = round(half - 0.45 - 0.001, 3)
check(len(KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(edge)]}, cant)) == 1,
      "a dormer just inside the hip is taken")
refused(lambda: KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(round(half - 0.45 + 0.01, 3))]}, cant),
        "a dormer crossing the canted face's hip")
refused(lambda: KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(-0.4), dorm(0.4)]}, cant),
        "two dormers that meet")
refused(lambda: KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(0.0, height_m=2.4)]},
                                        {**cant, "roof": {"kind": "hip", "pitch": 0.1,
                                                          "mansard": {"rise_m": 2.0, "lower_pitch_deg": 80}}}),
        "a dormer whose head meets the curb")
refused(lambda: KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(0.0, head="hood")]}, cant),
        "a hooded head on a bay's mansard")
refused(lambda: KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(0.0)]},
                                        {**cant, "roof": {"kind": "hip", "pitch": 0.25}}),
        "dormers on a canted bay with no mansard")
refused(lambda: KP._bay_mansard_dormers({"id": "b", "mansard_dormers": [dorm(0.0)]},
                                        {**cant, "plan": {"kind": "polyline", "points": [[-2.15, 0.0], [-1.45, 0.75],
                                                                                         [1.45, 0.75], [1.9, 0.0]]}}),
        "an unsymmetrical cant")

# a square projection keeps T-1881's clearance: the half-turn's tangent is 1
sq = {"kind": "projection", "plan": {"kind": "polyline", "points": [[-2.0, 0.0], [-2.0, 1.0], [2.0, 1.0], [2.0, 0.0]]},
      "roof": {"kind": "hip", "pitch": 0.1, "mansard": {"rise_m": 3.0, "lower_pitch_deg": 80}},
      "overrides": {"eaves": {"overhang_m": 0.3}}}
sq_half = 2.0 + 0.3 - run_ - 0.3
check(len(KP._bay_mansard_dormers({"id": "s", "mansard_dormers": [dorm(round(sq_half - 0.451, 3))]}, sq)) == 1,
      "a square projection's dormer just inside T-1881's clearance is still taken")
refused(lambda: KP._bay_mansard_dormers({"id": "s", "mansard_dormers": [dorm(round(sq_half - 0.44, 3))]}, sq),
        "and one just past it still refused")

# -- 1945's record ----------------------------------------------------------------------------
st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(st["phases"][0], st)
nb = next(b for b in p.bays if b["id"] == "north_bay")
check((nb["variant"]["roof"].get("mansard") or {}).get("rise_m") == 3.0,
      "1945's north bay rises under its own mansard (the 1928 photograph)")
check([d["at_m"] for d in nb.get("mansard_dormers") or ()] == [-0.6, 0.6],
      "with its two dormers, 0.6 m either side of its middle")
lo, hi = nb["span_m"]
check(not any(d["face"] == "street" and lo < d["along_m"] < hi for d in p.mansard["dormers"]),
      "no dormer left on the house's mansard over the bay")
a = K1.build(p, SID)
check(a is not None, "1945 builds")

if failures:
    print(f"\n{len(failures)} check(s) failed")
    sys.exit(1)
print("\nall checks passed")
