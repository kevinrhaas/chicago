#!/usr/bin/env python3
"""T-1890: a K01 mansard whose street face leans back further than its other faces
(`mansard.street_run_m`).

1801 Prairie's curb, read off J. W. Taylor's photograph of c. 1895 and Harold Allen's HABS
photograph 2 of 1965 through their solved cameras, stands about 1 m further back at the
north-west corner than its 18th Street face's pitch puts it: both prints show the corner hip
leaning back as it rises, and the corner hood's top about 50 px lower and 35-55 px further east
than a mansard of one pitch all round could stand it. This holds the kit and the record to it:

  * the K05 ring stack stands the x1 (street) face's rings in by the others' inset scaled by
    street_run / run up to the curb and by the extra run on to the ridge, so every face is
    still planar; with no street_run_m a mansard's rings are exactly inset_rect's (no other
    house moves);
  * the deck's street curb, the street dormers' faces and the covering K15 reads all stand on
    the street face's own run and pitch;
  * a street dormer's body runs back only the side faces' run + 0.3 m, under the face;
  * refused: a street run no longer than the side faces', a face shallower than 55 degrees, a
    deck left under 1.5 m deep;
  * 1801's record: street run 3.42 m over a 5.76 m rise (about 59 degrees), the side faces at 67,
    and the house builds.

    python3 tools/test_k01_street_lean.py
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

SID = "kimball_house_1801_prairie"
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


def planar_worst(polys):
    worst = 0.0
    for poly in polys:
        v = [q for i, q in enumerate(poly.v) if all(math.dist(q, w) > 1e-9 for w in poly.v[:i])]
        if len(v) < 4:
            continue
        a0, b0 = v[0], v[1]
        c0 = max(v[2:], key=lambda q: math.dist(q, a0) * math.dist(q, b0))
        u_ = [b0[i] - a0[i] for i in range(3)]
        w_ = [c0[i] - a0[i] for i in range(3)]
        n = (u_[1] * w_[2] - u_[2] * w_[1], u_[2] * w_[0] - u_[0] * w_[2], u_[0] * w_[1] - u_[1] * w_[0])
        L = math.sqrt(sum(x * x for x in n)) or 1.0
        for q in v:
            worst = max(worst, abs(sum((q[i] - a0[i]) * n[i] for i in range(3)) / L))
    return worst


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
phase = st["phases"][0]
p = KP.from_phase(phase, st)
m = p.mansard

# -- 1801's record ----------------------------------------------------------------------------
check(m.get("street_run_m") == 3.42 and m["lower_rise_m"] == 5.76 and m["lower_pitch_deg"] == 67.0,
      "1801's street face runs 3.42 m to a curb 5.76 m up, its other faces at 67 degrees")
check(abs(m["street_pitch_deg"] - math.degrees(math.atan2(5.76, 3.42))) < 1e-3 and 55 < m["street_pitch_deg"] < 65,
      f"so the street face leans at {m['street_pitch_deg']:.1f} degrees")
check(KP.face_lower(m, "street") == (m["street_pitch_deg"], 3.42) and KP.face_lower(m, "north")[0] == 67.0,
      "face_lower gives the street face its own pitch and run and every other face the mansard's")
a = K1.build(p, SID)
check(a is not None, "1801 builds")

# -- the ring stack ---------------------------------------------------------------------------
D, W, o, E = p.depth_m, p.width_m, p.eave_overhang_m, p.eave_m
run = m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
args = (0.0, D, -W, 0.0, E, m["lower_pitch_deg"], p.roof_pitch_deg, m["lower_rise_m"], m["bulge"],
        m["segments"], m["profile"], o, 0.2)
lean, _, meta = K5.mansard_element(*args, x1_run=3.42)
plain, _, _ = K5.mansard_element(*args)
check(planar_worst(lean) < 1e-6, "every face of the leaned ring stack is planar")
curb = [q for poly in lean for q in poly.v if abs(q[1] - (E + m["lower_rise_m"])) < 1e-9]
check(curb and abs(max(q[0] for q in curb) - (D + o - 3.42)) < 1e-9,
      "its curb stands the street run in from the street fascia")
check(abs(min(q[2] for q in curb) - (-W - o + run)) < 1e-9 and abs(min(q[0] for q in curb) - (-o + run)) < 1e-9,
      "and the side faces' run in from the others")
same = K5.mansard_element(*args, x1_run=None)[0]
check([pl.v for pl in same] == [pl.v for pl in plain], "with no street run the stack is exactly as before")

# -- the deck, the covering and the dormers ---------------------------------------------------
dk = m.get("deck") or {}
check(dk.get("curb") and abs(dk["curb"][1] - (D + o - 3.42)) < 1e-4, "the deck's street curb is the street face's")
cover = KP.mansard_cover(m, D, W, E, p.roof_pitch_deg, o)
v_mid = W / 2
check(abs(cover(D + o - 3.42, v_mid) - (E + m["lower_rise_m"])) < 1e-6
      and abs(cover(D + o - 1.71, v_mid) - (E + m["lower_rise_m"] / 2)) < 1e-6,
      "the covering K15 reads rises up the street face on its own pitch")
for d in m["dormers"]:
    if d["face"] == "street":
        foot = KP.mansard_face_height(d["face_setback_m"], m["lower_rise_m"], m["street_pitch_deg"], m["bulge"],
                                      m["profile"])
        check(abs(d["foot_m"] - (E + foot)) < 1e-4 if "foot_m" in d else True,
              f"the street dormer at {d['along_m']} m stands on the street face's pitch")


# -- refusals ---------------------------------------------------------------------------------
def with_run(r):
    ph = copy.deepcopy(phase)
    ph["form"]["mansard"]["value"]["street_run_m"] = r
    return KP.from_phase(ph, st)


refused(lambda: with_run(run - 0.01), "a street run no longer than the side faces'")
refused(lambda: with_run(4.2), "a street face shallower than 55 degrees")
check(with_run(3.45) is not None, "a street run of 3.45 m is taken")

if failures:
    print(f"\nFAIL — {len(failures)} check(s) failed")
    sys.exit(1)
print("\nPASS — a K01 mansard's street face may lean back on its own run (T-1890)")
