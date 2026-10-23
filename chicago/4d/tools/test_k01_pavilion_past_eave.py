#!/usr/bin/env python3
"""T-2843: the three kit pieces 1801 Prairie's move onto K01 needed, held on its record.

J. W. Taylor's c. 1895 photograph shows the Kimball house's steep slate faces rising from an
8.1 m cornice to a deck about 17 m up, its south pavilion and its 18th Street section carried
up as walls to about 13.9 m, and its wings slated like the main roof. So:

  * a K05 mansard face may hold two storeys (`storeys: 2`) and then rises 4.5-7.5 m; one
    storey stays the attic's 2.0-4.5 m, and a third is refused;
  * a K08 projection carried past the main eave is closed on the wall plane behind it, from
    the eave to its wall top across its junctions, and its cap's end too (K08 leaves both
    open on a projection, whose top otherwise stands at the eave under the main roof);
  * T-3047: a SHALLOW one (1801's south pavilion, 0.1 m proud) is opened on that plane where its
    windows' recesses run through it, its gable's parapet closes its top, and the mansard's
    eave box, covering foot and gutter stop at its cheeks, nothing of them in front of its
    face nor in its recesses behind the plane;
  * a projection that stops at the eave (1812's) gains nothing;
  * a wing slated in the main roof's own slate keeps its own material, so the publish
    path's dedup cannot merge `wing_slate` into `mansard_slate` and lose its name.

    python3 tools/test_k01_pavilion_past_eave.py
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

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def load(sid):
    st = json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text())
    return st, st["phases"][-1]


def mansard_refused(change, why, says):
    st, phase = load(SID)
    st = copy.deepcopy(st)
    phase = st["phases"][-1]
    change(phase["form"]["mansard"]["value"])
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


def closed_back(a, plane, back, span, y0, y1):
    """The bay walling's area facing `back` on the wall plane (axis, value), between the
    junctions `span` (along the other horizontal axis) and from y0 to y1."""
    ax, at = plane
    other = 2 if ax == 0 else 0
    pr = a.prims["bay_stone"]
    area, top = 0.0, 0.0
    for t in range(0, len(pr.idx), 3):
        tri = [pr.pos[i] for i in pr.idx[t:t + 3]]
        n = pr.nrm[pr.idx[t]]
        if sum(n[k] * back[k] for k in range(3)) < 0.99 or not all(abs(q[ax] - at) < 2e-3 for q in tri):
            continue
        if min(q[1] for q in tri) < y0 - 1e-6:
            continue
        (s0, h0), (s1, h1), (s2, h2) = [(q[other], q[1]) for q in tri]
        top = max(top, max(q[1] for q in tri))
        clip = min(q[1] for q in tri) < y1 - 1e-6 and span[0] - 1e-3 <= min(s0, s1, s2) and max(s0, s1, s2) <= span[1] + 1e-3
        if clip:
            area += abs((s1 - s0) * (h2 - h0) - (s2 - s0) * (h1 - h0)) / 2
    return area, top


def main() -> int:
    st, phase = load(SID)
    p = KP.from_phase(phase, st)
    m = p.roof.get("mansard") or {}
    check(p.roof_form == "mansard" and abs(p.eave_m - 8.1) < 1e-6,
          f"1801 resolves: a mansard over an {p.eave_m:.2f} m cornice")
    mansard_refused(lambda v: v.pop("storeys"), "a 7.2 m face that names no second storey",
                    "holding 1 storey(s) rises 2.0-4.5 m")
    mansard_refused(lambda v: v.__setitem__("storeys", 3), "a face holding three storeys", "holds 1 storey")
    mansard_refused(lambda v: v.__setitem__("lower_rise_m", 7.8), "a two-storey face rising 7.8 m",
                    "rises 4.5-7.5 m")
    mansard_refused(lambda v: v.__setitem__("lower_rise_m", 4.0), "a two-storey face rising 4.0 m",
                    "rises 4.5-7.5 m")

    a = K1.build(p, SID)
    D, W = p.depth_m, p.width_m
    walls = {"k01.wall.street_front": ((0, D - 0.001), (-1.0, 0.0, 0.0), lambda s: (-s, 0.0)),
             "k01.wall.side.south": ((2, -0.001), (0.0, 0.0, -1.0), lambda s: (s, 0.0))}
    for b in p.bays:
        if b["variant"]["kind"] != "projection":
            continue
        top = sum(float(x["height_m"]) for x in b["variant"]["storeys"])
        plane, back, to_axis = walls[b["wall"]]
        s0, s1 = b["span_m"]
        lo, hi = sorted(to_axis(s)[0] for s in (s0, s1))
        area, reach = closed_back(a, plane, back, (lo, hi), p.eave_m, top)
        want = (s1 - s0) * (top - p.eave_m)
        # T-3047: a shallow pavilion's back is opened where its windows' recesses run through
        # the plane, and its gable's parapet, carried back past the plane, closes its own top
        shallow = bool(b["variant"].get("shallow"))
        holes = [h for h in a.bay_holes.get(b["wall"], []) if s0 <= h[0] and h[1] <= s1]
        want -= sum((h[1] - h[0]) * max(0.0, min(h[3], top) - max(h[2], p.eave_m)) for h in holes)
        check(abs(area - want) < 0.02 * want,
              f"{b['id']}: closed over the eave on the wall plane ({area:.2f} of {want:.2f} m2"
              + (f", less {len(holes)} recesses" if holes else "") + ")")
        if shallow:
            check(holes and abs(reach - top) < 1e-3,
                  f"{b['id']}: shallow, its recesses open through the plane and no cap's end over its wall top "
                  f"({reach:.2f} m)")
        else:
            check(reach > top + 0.2, f"{b['id']}: and its cap's end ({reach:.2f} m, wall top {top:.2f} m)")
        if shallow:
            # T-3047: the mansard's eave box, covering foot and gutter stop at its cheeks: nothing
            # of the roof stands in front of its face across its span, nor behind the plane as deep
            # as its recesses reach between its third storey's sill and head
            sb = next(x for x in a.shallow_bays() if x[0]["id"] == b["id"])
            _, _, _, proud, behind = sb
            pts, _ = a.roof_shell
            inside = lambda q: s0 + 0.01 < -q[2] < s1 - 0.01
            check(not any(inside(q) and q[0] > D + proud + 1e-3 for q in pts),
                  f"{b['id']}: no eave box or covering in front of its {proud} m face")
            sills = [h for h in holes if h[2] > p.eave_m]
            check(sills and not any(inside(q) and q[0] > D - behind + 1e-3 and min(h[2] for h in sills) - 0.01 < q[1]
                                    < max(h[3] for h in sills) + 0.01 for q in pts),
                  f"{b['id']}: nor in its recesses' {behind:.2f} m behind the plane")
            gut = [q for name, pr in a.prims.items() if name.startswith("k04_") for q in pr.pos
                   if inside(q) and abs(q[1] - p.eave_m) < 0.5 and q[0] > D]
            check(not gut, f"{b['id']}: and no gutter across it ({len(gut)} vertices)")

    # 1812's projection stops at its eave: nothing is added behind it
    st2, ph2 = load("wheeler_house_1812_prairie")
    p2 = KP.from_phase(ph2, st2)
    a2 = K1.build(p2, st2["id"])
    b2 = next(b for b in p2.bays if b["variant"]["kind"] == "projection")
    lo, hi = sorted(-s for s in b2["span_m"])
    area, _ = closed_back(a2, (0, p2.depth_m - 0.001), (-1.0, 0.0, 0.0), (lo, hi), p2.eave_m - 1e-3, 99.0)
    check(area == 0.0, f"1812's projection, at its eave: no back added ({area:.2f} m2)")

    ws, ms = K1.MATERIALS["wing_slate"], K1.MATERIALS["mansard_slate"]
    check(ws["fabric"] == ms["fabric"] and ws != ms,
          "the wing slate is the main roof's fabric and still its own material (dedup keeps its name)")
    check({"wing_slate", "mansard_slate"} <= set(a.prims), "1801 lays both slates")

    if failures:
        print(f"test_k01_pavilion_past_eave: {len(failures)} failed")
        return 1
    print("test_k01_pavilion_past_eave: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
