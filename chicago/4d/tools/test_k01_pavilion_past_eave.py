#!/usr/bin/env python3
"""T-2843: the three kit pieces 1801 Prairie's move onto K01 needed, held on its record.

J. W. Taylor's c. 1895 photograph shows the Kimball house's steep slate faces rising from an
8.1 m cornice (T-3002: 8.9 m) to a deck about 17 m up, its south pavilion and its 18th Street section carried
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
import math
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


def K1_bays(phase):
    return KP.from_phase(phase, load(SID)[0]).bays


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
        within = span[0] - 1e-3 <= min(s0, s1, s2) and max(s0, s1, s2) <= span[1] + 1e-3
        # T-1890: its own top, not another bay's on the same plane (1801's south bay, beside
        # the wall gable on the south wall, carries its slate up past the gable's wall top)
        if within:
            top = max(top, max(q[1] for q in tri))
        clip = min(q[1] for q in tri) < y1 - 1e-6 and within
        if clip:
            area += abs((s1 - s0) * (h2 - h0) - (s2 - s0) * (h1 - h0)) / 2
    return area, top


def main() -> int:
    st, phase = load(SID)
    p = KP.from_phase(phase, st)
    m = p.roof.get("mansard") or {}
    check(p.roof_form == "mansard" and abs(p.eave_m - 8.9) < 1e-6,
          f"1801 resolves: a mansard over an {p.eave_m:.2f} m cornice")
    mansard_refused(lambda v: v.pop("storeys"), "a 6.4 m face that names no second storey",
                    "holding 1 storey(s) rises 2.0-4.5 m")
    mansard_refused(lambda v: v.__setitem__("storeys", 3), "a face holding three storeys", "holds 1 storey")
    mansard_refused(lambda v: v.__setitem__("lower_rise_m", 7.8), "a two-storey face rising 7.8 m",
                    "rises 4.5-7.5 m")
    mansard_refused(lambda v: v.__setitem__("lower_rise_m", 4.0), "a two-storey face rising 4.0 m",
                    "rises 4.5-7.5 m")

    a = K1.build(p, SID)
    D, W = p.depth_m, p.width_m
    walls = {"k01.wall.street_front": ((0, D - 0.001), (-1.0, 0.0, 0.0), lambda s: (-s, 0.0)),
             "k01.wall.side.south": ((2, -0.001), (0.0, 0.0, -1.0), lambda s: (s, 0.0)),
             # T-1890: the side wall at v = W (1801's south wall, its rear corner's wall gable)
             "k01.wall.side.north": ((2, -W + 0.001), (0.0, 0.0, 1.0), lambda s: (D - s, 0.0))}
    # T-1890: a roof point (x, y, -v) as (out of its wall's plane, along it), for each wall
    frames = {"k01.wall.street_front": lambda q: (q[0] - D, -q[2]),
              "k01.wall.side.south": lambda q: (q[2], q[0]),
              "k01.wall.side.north": lambda q: (-q[2] - W, D - q[0])}
    for b in p.bays:
        # T-3001: a pavilion on a rear wing's wall stands past no main eave; test_k01_wing_tower
        # holds it to its wing
        if b["variant"]["kind"] != "projection" or b.get("wing"):
            continue
        top = sum(float(x["height_m"]) for x in b["variant"]["storeys"])
        # T-1890: a pier stops under the eave (1801's, under its cornice), so there is nothing
        # past the eave to close; it is held to standing under it
        if b["variant"].get("pier"):
            check(top <= p.eave_m, f"{b['id']}: a pier, its top ({top:.2f} m) under the eave ({p.eave_m:.2f} m)")
            continue
        plane, back, to_axis = walls[b["wall"]]
        s0, s1 = b["span_m"]
        lo, hi = sorted(to_axis(s)[0] for s in (s0, s1))
        area, reach = closed_back(a, plane, back, (lo, hi), p.eave_m, top)
        # T-3048: a chamfered corner's closure stops where its canted face crosses the plane
        ch = KP.chamfer_of(b)
        if ch is not None:
            s0, s1 = (s0 + ch[3], s1) if ch[0] == "left" else (s0, s1 - ch[3])
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
            ns = frames[b["wall"]]
            inside = lambda q: s0 + 0.01 < ns(q)[1] < s1 - 0.01
            check(not any(inside(q) and ns(q)[0] > proud + 1e-3 for q in pts),
                  f"{b['id']}: no eave box or covering in front of its {proud} m face")
            sills = [h for h in holes if h[2] > p.eave_m]
            check(sills and not any(inside(q) and ns(q)[0] > -behind + 1e-3 and min(h[2] for h in sills) - 0.01 < q[1]
                                    < max(h[3] for h in sills) + 0.01 for q in pts),
                  f"{b['id']}: nor in its recesses' {behind:.2f} m behind the plane")
            gut = [q for name, pr in a.prims.items() if name.startswith("k04_") for q in pr.pos
                   if inside(q) and abs(q[1] - p.eave_m) < 0.5 and ns(q)[0] > 0.0]
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

    # T-3048: the south pavilion's south-west corner chamfered as its 1911 sheet draws it, the
    # house's own corner cut under the canted face from grade to the soffit
    D, W = p.depth_m, p.width_m
    bs = next(x for x in p.bays if x["id"] == "p_south")
    ch = KP.chamfer_of(bs)
    # T-3108: cut back 1.3 m along the front and 1.4 m behind it, the round bay standing on the cut
    check(ch is not None and ch[0] == "right" and abs(ch[1] - 1.3) < 1e-9 and abs(ch[2] - 1.4) < 1e-9,
          "1801's pavilion chamfers its corner 1.3 m along its front, back to 1.4 m behind it")
    check(KP.chamfer_spans(p.bays, D, W) == {"k01.wall.street_front": (W - ch[3], W),
                                              "k01.wall.side.north": (0.0, ch[2])},
          f"the front cut from {W - ch[3]:.3f} m to the corner, the side wall back to {ch[2]} m")
    proud = max(float(q[1]) for q in bs["variant"]["plan"]["points"])
    (un, sn), (ub, sb_) = (D + proud, W - ch[1]), (D - ch[2], W)
    side = lambda u, s_: (u - ub) * (sn - sb_) - (s_ - sb_) * (un - ub)
    out = side(D + proud, W)
    # T-3108: what stands in front of the cut inside the round bay's reach (its rise, cornice and
    # balustrade, within the cant's length) is the bay's own, not the house's
    rb = next(x for x in p.bays if x.get("on_chamfer"))
    Lc = math.hypot(un - ub, sn - sb_)
    reach = float(rb["variant"]["plan"]["rise_m"]) + 0.8
    along = lambda u, s_: ((u - un) * (ub - un) + (s_ - sn) * (sb_ - sn)) / Lc
    in_bay = lambda u, s_: -0.05 <= along(u, s_) <= Lc + 0.05 and abs(side(u, s_)) / Lc <= reach
    left = [q for name, pr in a.prims.items() if not name.startswith("bay_") for q in pr.pos
            if q[1] < a.soffit_m - 0.05 and ub <= q[0] <= un and sn <= -q[2] <= W
            and side(q[0], -q[2]) * out > 0 and abs(side(q[0], -q[2])) / Lc > 0.005
            and not in_bay(q[0], -q[2])]
    check(not left, f"no masonry of the house stands outside the canted face under the soffit ({len(left)} vertices)")

    def chamfer_refused(change, why, says):
        st, phase = load(SID)
        st = copy.deepcopy(st)
        phase = st["phases"][-1]
        e = next(x for x in phase["form"]["bays"]["value"] if x["id"] == "p_south")
        change(e)
        try:
            KP.from_phase(phase, st)
        except KP.ParamError as err:
            check(says in str(err), f"{why}: refused ({str(err)[:90]}...)")
            return
        check(False, f"{why}: refused")
    chamfer_refused(lambda e: e["plan"]["chamfer"].__setitem__("corner", "left"),
                    "a chamfer on the corner the pavilion is not flush with", "flush with that corner")
    chamfer_refused(lambda e: e["plan"].pop("shallow"), "a chamfer on a pavilion that is not shallow",
                    "on a shallow pavilion")
    chamfer_refused(lambda e: e["plan"]["chamfer"].__setitem__("behind_m", 1.8),
                    "a chamfer a round bay stands on, 1.8 m behind the wall", "0.1-1.6 m behind the wall")
    chamfer_refused(lambda e: e["plan"]["chamfer"].__setitem__("along_m", 2.2),
                    "a chamfer a round bay stands on, 2.2 m along the front", "0.2-2.0 m")

    # T-3108: a chamfer nothing stands on keeps T-3048's bounds
    def bare(change, why, says):
        st, phase = load(SID)
        phase["form"]["bays"]["value"] = [x for x in phase["form"]["bays"]["value"] if not x.get("on_chamfer")]
        e = next(x for x in phase["form"]["bays"]["value"] if x["id"] == "p_south")
        e["plan"]["chamfer"].update({"along_m": 0.44, "behind_m": 0.35})
        change(e)
        try:
            KP.from_phase(phase, st)
        except KP.ParamError as err:
            check(says in str(err), f"{why}: refused ({str(err)[:90]}...)")
            return
        check(False, f"{why}: refused")
    bare(lambda e: e["plan"]["chamfer"].__setitem__("behind_m", 0.8), "a bare chamfer 0.8 m behind the wall",
         "0.1-0.6 m behind the wall")
    bare(lambda e: e["plan"]["chamfer"].__setitem__("along_m", 1.3), "a bare chamfer 1.3 m along the front",
         "0.2-1.0 m")

    # T-3108: a bay on a chamfer is a bow, and its host must be a chamfered projection laid before it
    def on_cant(change, why, says):
        st, phase = load(SID)
        e = next(x for x in phase["form"]["bays"]["value"] if x.get("on_chamfer"))
        change(e, phase)
        try:
            KP.from_phase(phase, st)
        except KP.ParamError as err:
            check(says in str(err), f"{why}: refused ({str(err)[:90]}...)")
            return
        check(False, f"{why}: refused")
    on_cant(lambda e, ph: ph["form"]["bays"]["value"].append({**copy.deepcopy(e), "id": "x", "on_chamfer": "front_bow"}),
            "a second bay on a bow, not a chamfer", "stands on_chamfer")
    on_cant(lambda e, ph: e["plan"].__setitem__("chord_m", 1.9), "a round bay wider than its cant allows",
            "meets its chamfer")
    lb = load(SID)[1]
    rb = next(x for x in K1_bays(lb) if x.get("on_chamfer"))
    check(abs(rb["on_chamfer"]["length_m"] - math.hypot(1.3, 1.5)) < 1e-3 and rb["span_m"] == (round(W - 1.3, 4), W),
          f"the round bay stands on the {rb['on_chamfer']['length_m']} m cant, over the front's last 1.3 m")

    if failures:
        print(f"test_k01_pavilion_past_eave: {len(failures)} failed")
        return 1
    print("test_k01_pavilion_past_eave: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
