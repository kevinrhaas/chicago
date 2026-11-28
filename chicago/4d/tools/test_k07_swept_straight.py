"""T-3634: a swept stoop's cheek may fall in one straight rake instead of the kit's reversed curve.

2021 Prairie's stoop in the Chicagology photograph: the flight runs straight out of the arch,
and each cheek's snowy coping falls in one straight line from beside the landing to a block at
the flight's foot. The record names `cheek_form.fall: "straight"`; this holds the kit to it:

  * 2021 built so: its foot 3.62 m out (0.5 m landing, twelve 0.26 m goings), each cheek's top
    one strip from the landing's end to the block, at the straight line's height midway;
  * as-was: without `fall`, the reversed curve's strips are back, and the top midway is the
    curve's (its mean, (head + foot) / 2, only at the exact middle; a quarter down it is higher);
  * refused: a `fall` that is not "straight", and a straight fall that would come within 0.1 m
    of a tread (head level with the landing).

    python3 tools/test_k07_swept_straight.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k07_entrances as K7  # noqa: E402

SID = "high_house_2021_prairie"
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


def top_at(o, out):
    """The cheek's highest point at `out` m from the face (its coping), from its faces' vertices
    and the straight edges between them."""
    best = None
    pr = o.prims["cheek"]
    for i in range(0, len(pr.idx), 3):
        tri = [pr.pos[pr.idx[i + k]] for k in range(3)]
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            if (a[2] - out) * (b[2] - out) > 0 or abs(a[2] - b[2]) < 1e-9:
                continue
            t = (out - a[2]) / (b[2] - a[2])
            y = a[1] + t * (b[1] - a[1])
            best = y if best is None else max(best, y)
    return best


def inner_cuts(o, L, o1):
    return sorted({round(p[2], 6) for p in o.prims["cheek"].pos if L + 1e-4 < p[2] < o1 - 1e-4})


def refused(change, what, err=(ValueError, KP.ParamError)):
    st = record()
    change(cheek_form(st))
    try:
        entrance(st)
    except err:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it built)")


print("== 2021's stoop, built to the Chicagology photograph")
st = record()
cf = cheek_form(st)
check(cf.get("fall") == "straight", f"the record names a straight fall ({cf})")
o, v = entrance(st)
sw = v["stair"]["swept"]
L, F = v["stair"]["landing_m"], o.meta["stair"]["foot_out_m"]
o1 = F - sw["block_m"]
h0, yF = sw["head_m"], -v["stair"]["floor_m"] + sw["foot_m"]
check(abs(F - 3.62) < 1e-6, f"the flight's foot 3.62 m out ({F:.3f})")
check(inner_cuts(o, L, o1) == [], f"each cheek's top one strip from the landing to the block ({inner_cuts(o, L, o1)[:4]})")
for frac in (0.25, 0.5, 0.75):
    out = L + frac * (o1 - L)
    want, got = h0 + frac * (yF - h0), top_at(o, out)
    check(got is not None and abs(got - want) < 1e-6, f"the top {frac:.2f} down the fall on the straight line "
                                                       f"({got:.3f} against {want:.3f})")

print("== as-was: the kit's reversed curve without `fall`")
st = record()
del cheek_form(st)["fall"]
o, v = entrance(st)
check(len(inner_cuts(o, L, o1)) >= 20, f"the curve's strips are back ({len(inner_cuts(o, L, o1))})")
out = L + 0.25 * (o1 - L)
got = top_at(o, out)
check(got > h0 + 0.25 * (yF - h0) + 0.1, f"a quarter down, the curve stands over the straight line ({got:.3f})")

print("== refused")
refused(lambda c: c.__setitem__("fall", "curved"), "a fall that is not 'straight'")
refused(lambda c: c.__setitem__("head_m", 0.0), "a straight fall from the landing's level, inside 0.1 m of the first tread")

if failures:
    print(f"FAIL {len(failures)}: " + "; ".join(failures))
    sys.exit(1)
print("PASS a swept cheek falls straight where the record says so")
