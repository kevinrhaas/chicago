"""T-3144: a swept stoop's cheek may be drawn in to its foot, and a cheek pierced under its top.

1812 Prairie's stair in Levy's print: the south newel stands about 0.2 m north of where the
build had it while the north newel and both cheeks at the landing agree, and the north cheek's
inner face is pierced by a row of small openings under its coping. The record names
`cheek_form.flare` one a side (a negative `out_m` draws a cheek in) and `cheek_form.pierced`
{side, count, hole_m, under_m}; this holds the kit to them:

  * 1812 built so: the south newel 0.2 m in from the cheek's line at the landing, the treads'
    south ends on the drawn-in cheek's inner face, ten openings meta-recorded on the north cheek;
  * open: a ray across the north cheek through each opening's middle meets nothing of the cheek,
    and one between two openings meets both of its faces;
  * as-was: without `pierced` and the left flare, no openings and the south newel back on its line;
  * refused: a flare named twice on one side, a cheek drawn in past 0.5 m, openings that do not
    fit the sweep or whose sills come within 0.05 m of a tread, and an unknown `pierced` key.

    python3 tools/test_k07_stair_foot.py
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
from archetypes import k07_entrances as K7  # noqa: E402

SID = "wheeler_house_1812_prairie"
failures = []


def check(ok, what):
    print(f"  {'ok  ' if ok else 'FAIL'} {what}")
    if not ok:
        failures.append(what)


def record():
    return json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def cheek_form(st):
    return st["phases"][0]["form"]["entrance_kit"]["value"]["k01.opening.door_leaf"]["cheek_form"]


def entrance(st):
    ph = next(p for p in st["phases"] if "form" in p)
    a = K1.Assembly(SID, KP.from_phase(ph, st))
    v = a.door_variant()
    o = K7.Entrance(v, a._entrances)
    o.build()
    return o, v


def ray_hits(o, orig, d, roles=("cheek",)):
    """Distances along `d` from `orig` at which the ray meets a triangle of `roles`."""
    out = []
    for role in roles:
        pr = o.prims.get(role)
        if not pr:
            continue
        for i in range(0, len(pr.idx), 3):
            p0, p1, p2 = (pr.pos[pr.idx[i + k]] for k in range(3))
            e1 = [p1[k] - p0[k] for k in range(3)]
            e2 = [p2[k] - p0[k] for k in range(3)]
            h = [d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]]
            A = sum(e1[k] * h[k] for k in range(3))
            if abs(A) < 1e-12:
                continue
            s = [orig[k] - p0[k] for k in range(3)]
            u = sum(s[k] * h[k] for k in range(3)) / A
            q = [s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0]]
            w = sum(d[k] * q[k] for k in range(3)) / A
            t = sum(e2[k] * q[k] for k in range(3)) / A
            if u >= 0 and w >= 0 and u + w <= 1 and t > 0:
                out.append(t)
    return out


def refused(change, what, err=(ValueError, KP.ParamError)):
    st = record()
    change(cheek_form(st))
    try:
        entrance(st)
    except err:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it built)")


print("== 1812's stair, built to the Levy print")
st = record()
o, v = entrance(st)
sw = v["stair"]["swept"]
c, half = v["stair"]["axis_s_m"], v["stair"]["width_m"] / 2
newels = sorted(o.meta["newels"], key=lambda n: n["s_m"][0])
check(abs(newels[0]["s_m"][1] - (c - half + 0.2)) < 1e-6,
      f"the south newel's inner face 0.2 m in from the cheek's line at the landing ({newels[0]['s_m']})")
check(abs(newels[1]["s_m"][0] - (c + half + 0.55)) < 1e-6,
      f"the north newel still on the 0.55 m flare ({newels[1]['s_m']})")
pc = o.meta.get("pierced_cheek") or {}
check(pc.get("side") == "right" and pc.get("openings") == 10, f"ten openings on the north cheek ({pc})")
# the lowest tread's south end on the drawn-in cheek's face
tr = o.prims["tread"]
low = min(p[1] for p in tr.pos)
s_low = min(p[0] for p in tr.pos if abs(p[1] - low) < 1e-9)
check(s_low > c - half + 0.1, f"the treads narrow over the drawn-in cheek (the lowest from s {s_low:.3f})")

print("== the openings are open")
L, F, n, g = v["stair"]["landing_m"], o.meta["stair"]["foot_out_m"], o.meta["stair"]["risers"], v["stair"]["going_m"]
r = o.meta["stair"]["riser_m"]
o1 = F - sw["block_m"]
h0, yF = sw["head_m"], -v["stair"]["floor_m"] + sw["foot_m"]
top = lambda q: h0 if q <= L else yF if q >= o1 else yF + (h0 - yF) * (1 + math.cos(math.pi * (q - L) / (o1 - L))) / 2
flare = o._flare_at(sw, L, F, n, g, "right")[0]
holes = o._cheek_holes(sw, "right", L, o1, top, n, r, g)
u0, hh = sw["pierced"]["under_m"], sw["pierced"]["hole_m"][1]
clear = 0
for a, b in holes:
    m = (a + b) / 2
    y = top(m) - u0 - hh / 2
    s = c + half + flare(m)
    clear += not ray_hits(o, (s - 0.5, y, m), (1.0, 0.0, 0.0))
check(clear == len(holes), f"a ray through each opening's middle meets no cheek ({clear} of {len(holes)})")
a, b = holes[3][1], holes[4][0]
m = (a + b) / 2
hits = ray_hits(o, (c + half + flare(m) - 0.5, top(m) - u0 - hh / 2, m), (1.0, 0.0, 0.0))
check(len(hits) >= 2, f"between two openings the cheek is solid ({len(hits)} faces met)")

print("== as-was without them")
st0 = record()
cf0 = cheek_form(st0)
cf0["flare"] = {"side": "right", "out_m": 0.55}
del cf0["pierced"]
o0, _ = entrance(st0)
check("pierced_cheek" not in o0.meta, "no openings without `pierced`")
n0 = sorted(o0.meta["newels"], key=lambda n: n["s_m"][0])
check(abs(n0[0]["s_m"][1] - (c - half)) < 1e-6, f"the south newel back on the cheek's line ({n0[0]['s_m']})")
check(len(o.prims["cheek"].pos) > len(o0.prims["cheek"].pos), "the openings' reveals add to the cheek")

print("== refused")
refused(lambda cf: cf.__setitem__("flare", [{"side": "right", "out_m": 0.55}, {"side": "right", "out_m": 0.2}]),
        "a flare named twice on one side")
refused(lambda cf: cf.__setitem__("flare", [{"side": "right", "out_m": 0.55}, {"side": "left", "out_m": -0.7}]),
        "a cheek drawn in past 0.5 m")
refused(lambda cf: cf["pierced"].__setitem__("count", 24), "24 openings 0.11 m along a 2.07 m sweep")
refused(lambda cf: cf["pierced"].__setitem__("under_m", 0.4) or cf["pierced"].__setitem__("hole_m", [0.11, 0.3]),
        "openings whose sills run down onto the treads")
refused(lambda cf: cf["pierced"].__setitem__("shape", "round"), "an unknown `pierced` key")

print()
if failures:
    print(f"FAIL: {len(failures)} check(s): " + "; ".join(failures))
    sys.exit(1)
print("PASS: 1812's south cheek drawn in to its newel and its north cheek pierced under its top (T-3144)")
