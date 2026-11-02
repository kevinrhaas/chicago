#!/usr/bin/env python3
"""T-3283: a mansard crown over a stretch of the street front (`mansard.crown.over_front`).

The Chicago Tribune's 'Famous Homes' photograph of 29 July 1928 shows 1945 Prairie's corner
block, its two lights a storey and the canted corner beside them, under a mansard about a storey
higher than the rest of the house's, its own lights high in it. K01's crown (T-2404) stood only
over a K08 projection, and a canted corner (T-3186) refused any crown, so 1945 carried its whole
mansard at one height. This holds the kit and the record to the new rule:

  * a crown may stand over a stretch [s0, s1] of the front with no projection under it, its
    front on the wall's plane; run to the end a `cant_corner` cuts, its rings are cut on the
    cant's line out to its own fascia, so it turns the corner;
  * on a crown narrower than the cut, the cut eats the end side it crosses: `cant_ring` closes
    that end face to a point on the far side, and `cant_end_inset` names the inset where it
    goes, which the ring stack takes a ring at so every face stays planar; a ring the cut does
    not reach that far is cut exactly as before (no other house's mesh moves);
  * its `dormers` are the main mansard's lower-face dormers on its own faces, street and cant;
  * refused: a stretch stopping on the cut, a stretch too short, an unknown key, a rise outside
    0.3-2.0 m, a dormer across the crown's hip or over the cut, two that meet, a stack in the
    crown, a dormer on the house's mansard standing in it;
  * 1945's record: the crown from 6.95 m onto the cant, 1.4 m over the main curb, its three
    dormers, and the house builds with every roof face planar.

    python3 tools/test_k01_front_crown.py
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


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
phase = st["phases"][0]
p = KP.from_phase(phase, st)

# -- 1945's record ----------------------------------------------------------------------------
cr = p.mansard.get("crown") or {}
check(cr.get("over_front") == [6.95, 13.25] and cr.get("cant") is True,
      "1945's crown stands over the front from 6.95 m onto the canted corner")
check(abs(cr["curb_m"] - (p.mansard["curb_m"] + 1.4)) < 1e-6,
      "its curb 1.4 m over the house's (the 1928 photograph's corner block)")
check([(d["face"], d["along_m"]) for d in cr.get("dormers", ())] == [("street", 8.3), ("street", 10.0), ("cant", 0.0)],
      "with the corner block's two dormers and the cant's on it")
check(not any(d["face"] in ("street", "cant") and d.get("along_m", 0) > 6.3 for d in p.mansard["dormers"]
              if d["face"] != "cant") and not any(d["face"] == "cant" for d in p.mansard["dormers"]),
      "and none of them left on the house's mansard")
a = K1.build(p, SID)
check(a is not None, "1945 builds")

# -- cant_ring on a narrow ring ---------------------------------------------------------------
cc, D, W = p.cant_corner, p.depth_m, p.width_m
co = cr["overhang_m"]
X0, X1, Z0, Z1 = cr["x0"] - co, cr["x1"] + co, cr["z0"] - co, cr["z1"] + co
t_end = KP.cant_end_inset(cc, D, W, X0, Z0, Z1, co)
check(1.0 < t_end < (X1 - X0) / 2, f"the cut eats the crown's end side at inset {t_end:.3f} m, under its ridge")
plan = KP.cant_corner_plan(cc, D, W)
(u0, v0), _ = plan["ends"]
nx, nz = plan["normal"][0], -plan["normal"][1]
line = lambda q, t: nx * q[0] + nz * q[1] - (nx * u0 + nz * -v0 + co - t)
ring = K5.inset_rect(X0, X1, Z0, Z1, t_end)
check(abs(line(ring[0], t_end)) < 1e-9, "at that inset the end side's far corner stands on the cut's line")
deep = KP.cant_ring(K5.inset_rect(X0, X1, Z0, Z1, t_end + 0.3), cc, D, W, co - (t_end + 0.3))
check(len(deep) == 5 and deep[0] == deep[1] and abs(deep[0][0] - (X0 + t_end + 0.3)) < 1e-9
      and abs(line(deep[0], t_end + 0.3)) < 1e-9,
      "past it the end face closes to one point, on the far side and on the line")
shallow = KP.cant_ring(K5.inset_rect(X0, X1, Z0, Z1, 0.5), cc, D, W, co - 0.5)
check(shallow[0] == K5.inset_rect(X0, X1, Z0, Z1, 0.5)[0] and shallow[1] != shallow[0],
      "short of it the far corner stays where it was")
# the house's own mansard: the cut runs out long before its far corner, so its rings are unchanged
o = p.eave_overhang_m
mx0, mz0, mz1 = -o, -W - o, o
check(KP.cant_end_inset(cc, D, W, mx0, mz0, mz1, o) > min(D, W) / 2 + o,
      "on the house's own mansard the cut never reaches the far corner (its rings are cut as before)")

# -- the roof's faces are planar --------------------------------------------------------------
elem, _, _ = K5.mansard_element(cr["x0"], cr["x1"], cr["z0"], cr["z1"], p.eave_m, cr["lower_pitch_deg"],
                                p.roof_pitch_deg, cr["lower_rise_m"], cr["bulge"], p.mansard["segments"],
                                p.mansard["profile"], co, 0.2,
                                cut=((lambda r, out: KP.cant_ring(r, cc, D, W, out)),
                                     co + cc["cut_m"] / (2 - math.sqrt(2)), t_end))
worst = 0.0
for poly in elem:
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
check(worst < 1e-6, f"every face of the crown's ring stack is planar (worst {worst:.1e} m off its plane)")
# planar is not enough: without a ring at the end inset the closing end face is a triangle, planar
# but tilted off its own pitch. The stack must carry the vertex where it closes: the far corner at
# that inset, on the end face's, the far side's and the cut's planes at once.
run_c = cr["lower_rise_m"] / math.tan(math.radians(cr["lower_pitch_deg"]))
y_end = p.eave_m + cr["lower_rise_m"] + (t_end - run_c) * math.tan(math.radians(p.roof_pitch_deg))
corner = (X0 + t_end, y_end, Z0 + t_end)
check(any(math.dist(q, corner) < 1e-6 for poly in elem for q in poly.v),
      "the stack closes the end face at its far corner, at the end inset's height")


# -- refusals ---------------------------------------------------------------------------------
def with_crown(**kw):
    s = copy.deepcopy(st)
    c = s["phases"][0]["form"]["mansard"]["value"]["crown"]
    for k, v in kw.items():
        if v is None:
            c.pop(k, None)
        else:
            c[k] = v
    return lambda: KP.from_phase(s["phases"][0], s)


dorms = st["phases"][0]["form"]["mansard"]["value"]["crown"]["dormers"]
refused(with_crown(over_front=[6.95, 11.5]), "a stretch that stops on the canted corner")
refused(with_crown(over_front=[11.0, 13.25], dormers=[dorms[2]]), "a stretch under 3 m")
refused(with_crown(finial={"height_m": 1.0, "radius_m": 0.1}), "a key a front crown does not take")
refused(with_crown(rise_above_curb_m=2.5), "a crown 2.5 m over the main curb")
refused(with_crown(dormers=[dict(dorms[0], along_m=7.6), dorms[1], dorms[2]]), "a dormer across the crown's hip")
refused(with_crown(dormers=[dorms[0], dict(dorms[1], along_m=10.8), dorms[2]]), "a dormer over the cut")
refused(with_crown(dormers=[dorms[0], dict(dorms[1], along_m=9.2), dorms[2]]), "two crown dormers that meet")
refused(with_crown(depth_m=8.5), "a crown deeper than half the house")
s2 = copy.deepcopy(st)
s2["phases"][0]["form"]["mansard"]["value"]["dormers"].append(
    dict(dorms[0], face="street", along_m=8.3, face_setback_m=0.05))
refused(lambda: KP.from_phase(s2["phases"][0], s2), "a dormer on the house's mansard standing in the crown")
s3 = copy.deepcopy(st)
s3["phases"][0]["form"]["chimneys"]["value"]["stacks"].append({"u_m": 14.0, "v_m": 9.0})
refused(lambda: KP.from_phase(s3["phases"][0], s3), "a stack standing in the crown")

if failures:
    print(f"\n{len(failures)} check(s) failed")
    sys.exit(1)
print("\nall checks passed")
