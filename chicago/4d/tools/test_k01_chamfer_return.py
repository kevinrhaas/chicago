#!/usr/bin/env python3
"""T-1890: a chamfered pavilion's stone cheek may run back as a RETURN, hold a LIGHT, and the
house's slate is set back behind it over the corner.

HABS photograph 1 of 1801 Prairie shows the south pavilion's return running back from its
corner pier, over the round bay's balcony, to the slate: a deep-set light in it beside the
pier, a moulded course along its top under the pier's capital, slate over it. The build's
front slate came down at the wall plane in front of all but the return's first 0.8 m. This
holds the kit and the record to it:

  * `plan.chamfer.return` takes back_m [at its foot, at its top] (each past the cant's back,
    at most 3 m), top_m (a metre or more over the chamfer's top_m) and pier_m (0.2 m up to
    the front's proud), on a right chamfer with a top_m; anything else is refused;
  * `plan.chamfer.light` needs the chamfer's top_m, takes K06's opening, clear sizes, sill_m,
    back_m and why_not_ordinary (and recess_m), and must stand clear of the pier and of the
    stone's back, between the chamfer's top and the return's top;
  * the light is laid as a window of the bay (its panes face out of the side, +x), the
    return's meta records its back edge and top, and the cross roof's slated cheek is
    opened round the light's recess;
  * the house's roof keeps no slate in front of the return's back edge between the cant's
    top and the return's top, south of the return's plane; without a return it does;
  * a chamfer without either builds its cheek as one plain face, as before.

    python3 tools/test_k01_chamfer_return.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def phase_with(mutate):
    s = copy.deepcopy(st)
    ch = s["phases"][0]["form"]["bays"]["value"][0]["plan"]["chamfer"]
    mutate(ch)
    return s, s["phases"][0]


def bay_of(params):
    b = next(x for x in params.bays if x["id"] == "p_south")
    return b, K8.Bay(b["variant"], K8.load(), "full").build(board=False)


def refused(mutate, what):
    s, ph = phase_with(mutate)
    try:
        bay_of(KP.from_phase(ph, s))
        check(False, what)
    except (KP.ParamError, ValueError):
        check(True, what)


# -- the record ------------------------------------------------------------------------------
ch0 = st["phases"][0]["form"]["bays"]["value"][0]["plan"]["chamfer"]
check(ch0.get("return") == {"back_m": [1.4, 2.0], "top_m": 11.7, "pier_m": 0.4},
      "1801's return runs 1.4-2.0 m behind the wall, tops out at 11.7 m, its pier 0.4 m deep")
lt0 = ch0.get("light") or {}
check(lt0.get("clear_width_m") == 1.1 and lt0.get("clear_height_m") == 0.85 and lt0.get("sill_m") == 10.45
      and lt0.get("back_m") == 1.2, "1801's light is 1.1 by 0.85 m on a 10.45 m sill, 1.2 m behind the face")

p = KP.from_phase(st["phases"][0], st)
b, built = bay_of(p)
m = built.meta
check(m.get("chamfer_return", {}).get("top_m") == 11.7 and m["chamfer_return"]["back_m"] == [1.4, 2.0],
      "the bay's meta records the return's top and back edge")
check("chamfer_light" in m and m["chamfer_light"]["recess_m"] == 0.35, "the bay's meta records the light")
lights = [w for w in built.windows if w["run"] == -1]
check(len(lights) == 1 and all(pn["out"][0] > 0.99 for pn in lights[0]["panes"]),
      "the light is one window of the bay, its panes facing out of the side")
check(getattr(built, "cheek_hole", None) is not None, "the cross roof's slated cheek is opened round its recess")

# -- the slate set back ----------------------------------------------------------------------
v = b["variant"]
D, s1 = p.depth_m, b["span_m"][1]
along = float(ch0["along_m"])
ct, rt = float(ch0["top_m"]), 11.7
b0, b1 = 1.4, 2.0


c0 = (D + p.eave_overhang_m, s1 + p.eave_overhang_m, p.eave_m)       # the eave's corner, the hip's foot
r0, r1 = (D - b0, s1 - along, ct), (D - b1, s1 - along, rt)          # the return's back edge
e0, e1 = [r0[i] - c0[i] for i in range(3)], [r1[i] - c0[i] for i in range(3)]
nrm = (e0[1] * e1[2] - e0[2] * e1[1], e0[2] * e1[0] - e0[0] * e1[2], e0[0] * e1[1] - e0[1] * e1[0])
side = lambda q: sum(nrm[i] * (q[i] - c0[i]) for i in range(3))
far = side((D + 2.0, s1 + 2.0, ct))
L = sum(x * x for x in nrm) ** 0.5


def slate_in_front(params):
    """Roof faces standing on the corner's side of the cut plane, past a 5 cm margin, between
    the cant's top and the return's top and south of the return's plane."""
    a = K1.build(params, SID)
    pts, tris = a.roof_shell
    n = 0
    for t in tris:
        c = [sum(pts[i][k] for i in t[:3]) / 3.0 for k in range(3)]
        q = (c[0], -c[2], c[1])                                       # (u, v, y)
        if ct + 0.1 < q[2] < rt - 0.1 and s1 - along + 0.1 < q[1] < s1 + 1.0 \
                and side(q) * (1.0 if far > 0.0 else -1.0) / L > 0.05:   # metres past the plane
            n += 1
    return n


check(slate_in_front(p) == 0, "no slate stands in front of the return's back edge over the corner")
s_, ph_ = phase_with(lambda ch: (ch.pop("return"), ch.pop("light")))
check(slate_in_front(KP.from_phase(ph_, s_)) > 0, "without a return the front slate comes down there, as before")
_, plain = bay_of(KP.from_phase(ph_, s_))
check("chamfer_return" not in plain.meta and "chamfer_light" not in plain.meta
      and not [w for w in plain.windows if w["run"] == -1], "a chamfer without either keeps its plain cheek")

# -- refusals --------------------------------------------------------------------------------
refused(lambda ch: ch["return"].update(back_m=[0.5, 2.0]), "a return ending in front of the cant's back is refused")
refused(lambda ch: ch["return"].update(top_m=10.6), "a return topping out under a metre over its foot is refused")
refused(lambda ch: ch["return"].update(pier_m=1.5), "a pier deeper than the front stands proud is refused")
refused(lambda ch: ch["return"].update(extra=1), "a return with an unknown key is refused")
refused(lambda ch: ch.update(corner="left"), "a return on a left chamfer is refused")
refused(lambda ch: ch.pop("top_m"), "a return or light on a chamfer with no top_m is refused")
refused(lambda ch: ch["light"].update(back_m=0.5), "a light reaching into the corner pier is refused")
refused(lambda ch: ch["light"].update(sill_m=11.0), "a light rising past the return's top is refused")
refused(lambda ch: ch["light"].update(back_m=2.0), "a light past the stone's back is refused")
refused(lambda ch: ch["light"].update(glazing="x"), "a light with an unknown key is refused")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall checks pass")
