#!/usr/bin/env python3
"""Hold the K08 bay kit to its data, and every built bay to being a closed projection (T-2307).

    python3 tools/check_bay_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_bay_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k08_bays.json and the generator
(generators/archetypes/k08_bays.py) builds every variant from them, its windows from
K06. This rebuilds each variant at both tiers in memory and measures the BUILT geometry,
not the data's promises. The K08 acceptance is "a canted and a curved example preserve
footprint and window rhythm without faceting at near view; light tier retains their
silhouette", with the reconstruction rules' "bays have foundations or corbels", and each
clause is a rule here:

  data       every window inside its run with a pier to spare, clear of its neighbours
             and of its storey's floor bands; a sash outside K06's ordinary range says why
  keyed      the plan starts and ends on the host wall's face, and nothing of the bay
             reaches behind it; the outer wall stands on the declared plan
  closed     from inside the bay every ray meets the bay or its wall: no gap anywhere
             between walls, bands, eaves, roof and supports
  windows    every pane has its own recess behind it, one glass layer deep (a ray in
             through a pane meets something opaque before any second pane); every recess
             inside the bay and clear of every other
  doubled    no two coplanar faces overlap (check_window_kit.py's rule, sifted by box)
  curves     a curved run cut no coarser than its tier allows, its chord within the
             tier's sagitta, every vertex on it carrying the true curve's normal
  support    a bay on grade stands on its plinth; an oriel's corbel courses each oversail
             the one below by no more than the data's ratio and the lowest still bears
  light      the light tier keeps the full tier's silhouette and costs at most a set
             fraction of its triangles (T-1890: a bay holding an open opening, a loggia's,
             may state its own fraction up to 0.65, with its reason)
  costs      every variant inside its triangle budget, at both tiers
  specimen   the committed specimen GLB is the generator's bytes
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import k08_bays as K  # noqa: E402
import check_window_kit as W  # noqa: E402

EPS = 1e-6
GLASS = ("glass_outer", "glass_inner")


# -- rays ----------------------------------------------------------------------------------------

class Tracer:
    """Every triangle of a built bay in a uniform grid, for rays."""

    CELL = 0.5

    def __init__(self, b, roles=None):
        self.tris, self.grid = [], {}
        for role, pr in b.prims.items():
            if roles and role not in roles:
                continue
            for i in range(0, len(pr.idx), 3):
                a, bb, c = (pr.pos[pr.idx[i + k]] for k in range(3))
                t = len(self.tris)
                self.tris.append((a, K._sub(bb, a), K._sub(c, a), role))
                lo = [math.floor(min(a[k], bb[k], c[k]) / self.CELL) for k in range(3)]
                hi = [math.floor(max(a[k], bb[k], c[k]) / self.CELL) for k in range(3)]
                for x in range(lo[0], hi[0] + 1):
                    for y in range(lo[1], hi[1] + 1):
                        for z in range(lo[2], hi[2] + 1):
                            self.grid.setdefault((x, y, z), []).append(t)

    def hits(self, o, d, tmax):
        """Every hit along the ray, nearest first: (t, role)."""
        seen, out = set(), []
        n = int(tmax / (self.CELL / 5)) + 1
        for j in range(n + 1):
            t = tmax * j / n
            p = (o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t)
            key = tuple(math.floor(p[k] / self.CELL) for k in range(3))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for ti in self.grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                            if ti in seen:
                                continue
                            seen.add(ti)
                            a, e1, e2, role = self.tris[ti]
                            h = K._cross(d, e2)
                            det = K._dot(e1, h)
                            if abs(det) < 1e-14:
                                continue
                            s = K._sub(o, a)
                            u = K._dot(s, h) / det
                            if u < -1e-9 or u > 1 + 1e-9:
                                continue
                            q = K._cross(s, e1)
                            v = K._dot(d, q) / det
                            if v < -1e-9 or u + v > 1 + 1e-9:
                                continue
                            tt = K._dot(e2, q) / det
                            if 1e-7 < tt <= tmax:
                                out.append((tt, role))
            if out and min(h[0] for h in out) < t - self.CELL:
                break
        return sorted(out)


def rotate_y(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) + v[2] * math.sin(a), v[1], -v[0] * math.sin(a) + v[2] * math.cos(a))


DIRS = [K._unit((x, y, z)) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)]


# -- the rules ------------------------------------------------------------------------------------

def rule_data(v, data, b):
    fails = []
    pier = data["parts"]["pier_min_m"]
    band = K.part(v, data, "floor_band")
    plinth = K.part(v, data, "plinth")
    k06 = K.K6.load()
    lo_w, hi_w = k06["ranges"]["ordinary_clear_width_m"]
    lo_h, hi_h = k06["ranges"]["ordinary_clear_height_m"]
    levels = b.meta["levels_m"]
    for w in b.windows:
        run = (b.runs + b.stage_runs)[w["run"]]   # T-1890: a staged tower's stage runs on from its shaft's
        a, z = w["s_extent"]
        if a < pier - EPS or z > run.L - pier + EPS:
            fails.append(f"pier: {w['opening']} on run {w['run']} reaches s {a:.3f}..{z:.3f} of a {run.L:.3f} m run, "
                         f"closer than {pier} m to its end")
        k = w["storey"]
        floor = levels[k] + (band["height_m"] / 2 if k else (plinth["height_m"] if v["base"] == "grade" else 0))
        if w.get("door") and k == 0:   # T-1890: a door runs through the plinth, its sill on the step
            floor = levels[0] - k06["parts"]["sill"]["height_m"]
        ceil = levels[k + 1] - (band["height_m"] / 2 if k + 1 < len(levels) - 1 else 0)
        if w["y_all"][0] < floor - EPS or w["y_all"][1] > ceil + EPS:
            fails.append(f"storey: {w['opening']} on storey {k} spans y {w['y_all'][0]:.3f}..{w['y_all'][1]:.3f}, "
                         f"outside its storey's clear wall {floor:.3f}..{ceil:.3f}")
    for i, w1 in enumerate(b.windows):
        for w2 in b.windows[i + 1:]:
            # T-1890: two in one storey overlap only where they share height too (a door under a light)
            if (w1["run"], w1["storey"]) == (w2["run"], w2["storey"]) and \
                    w1["s_extent"][0] < w2["s_extent"][1] and w2["s_extent"][0] < w1["s_extent"][1] and \
                    w1["y_all"][0] < w2["y_all"][1] and w2["y_all"][0] < w1["y_all"][1]:
                fails.append(f"overlap: two windows on run {w1['run']} storey {w1['storey']} share s "
                             f"{max(w1['s_extent'][0], w2['s_extent'][0]):.3f}..{min(w1['s_extent'][1], w2['s_extent'][1]):.3f}")
    for st in v["storeys"]:
        for w in st["windows"]:
            if not (lo_w <= w["clear_width_m"] <= hi_w and lo_h <= w["clear_height_m"] <= hi_h) \
                    and not w.get("why_not_ordinary"):
                fails.append(f"ordinary: a {w['clear_width_m']} x {w['clear_height_m']} m sash is outside the "
                             f"reconstruction rules' range and must say why (why_not_ordinary)")
    if v["base"] != "grade" and not v.get("corbel") and not v.get("apron"):
        fails.append("support: a bay off grade must say what carries it (corbel or apron)")
    return fails


def _across_inside(b, margin=1e-6):
    """T-3176: inside the house a ring across its corner stands on: behind the wall's face and
    inside its end (x < 0 for the right corner), by more than `margin` on both; None if the
    bay is not across a corner."""
    across = b.plan.get("across_corner")
    if across is None:
        return None
    k = 1.0 if across == "right" else -1.0
    return lambda x, z: z < -margin and k * x < -margin


def rule_keyed(b, v):
    fails = []
    inside = _across_inside(b)
    if inside is not None:
        # T-3176: a tower across its house's corner starts on the wall's face and ends on the end
        # wall's plane (or the reverse, at a left corner); nothing of it but its cap, its deck's
        # iron and finials and the soffit closing the cap stands inside the corner
        right = b.plan["across_corner"] == "right"
        a = b.runs[0].world(0.0, 0.0, 0.0)
        e = b.runs[-1].world(b.runs[-1].L, 0.0, 0.0)
        on_face, on_side = (a, e) if right else (e, a)
        if abs(on_face[2]) > 1e-6 or (on_face[0] >= 0) == right:
            fails.append(f"keyed: an across-corner tower's junction {on_face} is not on its wall's face inside its end")
        if abs(on_side[0]) > 1e-6 or on_side[2] >= 0:
            fails.append(f"keyed: an across-corner tower's junction {on_side} is not on its end wall's plane behind the face")
        whole = ("roof", "finial", "iron", "soffit")
        worst = [(role, p) for role, pr in b.prims.items() if role not in K.BOARD_ROLES and role not in whole
                 for p in pr.pos if inside(p[0], p[2])]
        if worst:
            fails.append(f"behind: a {worst[0][0]} vertex stands inside the corner at {worst[0][1]}")
        ring, (cx, cz) = b.plan["ring"], b.plan["centre"]
        n = len(ring)
        reach = math.hypot(ring[0][0] - cx, ring[0][1] - cz) + b.meta["overhang_m"] / math.cos(math.pi / n)
        far = max(math.hypot(p[0] - cx, p[2] - cz) for role in whole for p in b.prims.get(role, K.Prim(role)).pos)
        if far > reach + 1e-6:
            fails.append(f"behind: a whole cap reaches {far:.4f} m from its axis, past its eaves' {reach:.4f} m")
        off = 0.0
        for p in b.prims["wall"].pos:
            off = max(off, min(plan_distance(r, p) for r in b.runs))
        if off > 2e-4:
            fails.append(f"footprint: the outer wall stands {off * 1000:.1f} mm off its declared plan")
        return fails
    # T-3048: a chamfered corner's run ends on its side wall's plane, behind the face, inside
    # the corner its host cuts away under it (k01_frontage_params.chamfer_spans); there, and
    # nowhere else, the bay stands behind the face
    corner = None
    for r, end, side in ((b.runs[0], 0.0, "left"), (b.runs[-1], b.runs[-1].L, "right")):
        p = r.world(end, 0.0, 0.0)
        if "side" in (r.start, r.end) and (r.end if side == "right" else r.start) == "side":
            q = r.world(0.0 if side == "right" else r.L, 0.0, 0.0)
            # T-3108: as far back as a chamfer a round bay stands on may run; the record's params
            # hold a bare one to CHAMFER_BEHIND_M (k01_frontage_params._bays)
            from archetypes import k01_frontage_params as P
            most = P.ROUND_CHAMFER_BEHIND_M
            if not (-most - 1e-6 <= p[2] < -1e-6 and q[2] > 1e-6):
                fails.append(f"keyed: a chamfer's end at x {p[0]:.3f} stands {p[2]:.4f} m off the host wall's "
                             f"face, where it meets its side wall 0-{most} m behind it from a front proud of it")
            cross = p[0] + (q[0] - p[0]) * (-p[2]) / (q[2] - p[2])
            corner = (min(cross, p[0]) - 0.05, max(cross, p[0]) + 1e-6, p[2] - 1e-6)
            continue
        if abs(p[2]) > 1e-6:
            fails.append(f"keyed: the plan's end at x {p[0]:.3f} is {p[2]:.4f} m off the host wall's face")
    # T-2900: a corner turret's cone stands whole over its wing's roof (`cap_whole`), so its
    # roof and finial reach behind the face, inside its eaves' circle and nowhere else
    whole = ("roof", "finial") if v.get("cap_whole") else ()
    # T-3047: a shallow projection's window recesses and its gable's parapet run back through
    # the plane (its host opens its face round the recesses), no deeper than a recess reaches
    through = (*K.WINDOW_ROLES, "band") if v.get("shallow") else ()
    cut = (lambda p: corner[0] <= p[0] <= corner[1] and p[2] >= corner[2]) if corner else (lambda p: False)
    worst = min(((p[2], role) for role, pr in b.prims.items()
                if role not in K.BOARD_ROLES and role not in whole and role not in through for p in pr.pos
                if not cut(p)), default=(0.0, None))
    if worst[0] < -1e-6:
        fails.append(f"behind: a {worst[1]} vertex stands {-worst[0]:.4f} m behind the host wall's face")
    if through:
        deep = b.meta["recess_m"] - max(q[1] for q in v["plan"]["points"])
        far = min(((p[2], role) for role in through for p in b.prims.get(role, K.Prim(role)).pos if not cut(p)),
                  default=(0.0, None))
        if far[0] < -deep - 1e-6:
            fails.append(f"behind: a shallow projection's {far[1]} reaches {-far[0]:.4f} m behind the host wall's "
                         f"face, past its recesses' {deep:.4f} m")
    if whole:
        (cx, cz), reach = b.plan["centre"], b.plan["R"] + b.meta["overhang_m"]
        far = max(math.hypot(p[0] - cx, p[2] - cz) for role in whole for p in b.prims.get(role, K.Prim(role)).pos)
        if far > reach + 1e-6:
            fails.append(f"behind: a whole cap reaches {far:.4f} m from its axis, past its eaves' {reach:.4f} m")
    # the outer wall on the declared plan
    off = 0.0
    for p in b.prims["wall"].pos:
        off = max(off, min(plan_distance(r, p) for r in b.runs + b.stage_runs))
    if off > 2e-4:
        fails.append(f"footprint: the outer wall stands {off * 1000:.1f} mm off its declared plan")
    return fails


def plan_distance(r, p):
    """How far a point is from the run's outer face line or arc, in plan."""
    if r.kind == "arc":
        dr = abs(math.hypot(p[0] - r.c[0], p[2] - r.c[1]) - r.R)
        f = math.atan2(p[2] - r.c[1], p[0] - r.c[0])
        s = ((r.phi0 - f) % (2 * math.pi)) * r.R
        return dr if -1e-6 <= s <= r.L + 1e-6 else 1e9
    s = (p[0] - r.A[0]) * r.e[0] + (p[2] - r.A[1]) * r.e[1]
    if s < -1e-6 or s > r.L + 1e-6:
        return 1e9
    return abs((p[0] - r.A[0]) * r.n[0] + (p[2] - r.A[1]) * r.n[1])


def inside_point(b):
    """A point inside the bay's solid and outside every recess, one per storey."""
    # T-1890: a window centred on a deep projection (1801's p_flank) has its recess's back on
    # z 0.05 under every one of the first four, so a point ON a footprint's edge counts as in
    # it, and the last stands behind every recess (they all end 0.05 m in front of the wall)
    cands = ((0.0, 0.05), (0.0, 0.15), (0.3, 0.1), (-0.3, 0.1), (0.0, 0.025))
    if b.v.get("shallow"):   # T-3047: inside so thin a projection, beside its windows
        (x0, d), (x1, _) = b.v["plan"]["points"][1:3]
        cands = ((x0 + 0.15, d / 2), (x1 - 0.15, d / 2))
    # T-1881: a forward block's door (`door_hole`) is cut clean through its front for K07's
    # door to close, so a ray out through it is the doorway, not a gap; with the door on the
    # block's axis (1729's p_forward) every point above stands behind it, so the points
    # halfway between its jambs and the block's sides are tried too
    dh = b.v.get("door_hole")
    if dh:
        (xa, _), (xb, _) = b.v["plan"]["points"][1:3]
        cands = (*cands, ((dh["x_m"][1] + xb) / 2, 0.1), ((dh["x_m"][0] + xa) / 2, 0.1))
    lv = b.meta["levels_m"]

    def points(cand):
        return [(cand[0], (lv[k] + lv[k + 1]) / 2, cand[1]) for k in range(len(lv) - 1)] + \
               [(cand[0], b.meta["wall_top_m"] + 0.05, cand[1])]

    for cand in cands:
        if not any(in_hull(cand, w["footprint"], edge=True) for w in b.windows) and \
                not any(through_door(b, p, dh) for p in points(cand)):
            break
    return points(cand)


def through_door(b, p, dh):
    """T-1881: whether a ray of DIRS from p meets the block's front inside its door hole."""
    if not dh:
        return False
    zf = b.v["plan"]["points"][1][1]
    for d in DIRS:
        if d[2] <= 0:
            continue
        t = (zf - p[2]) / d[2]
        x, y = p[0] + d[0] * t, p[1] + d[1] * t
        if dh["x_m"][0] - EPS <= x <= dh["x_m"][1] + EPS and dh["y_m"][0] - EPS <= y <= dh["y_m"][1] + EPS:
            return True
    return False


def in_hull(p, h, edge=False):
    n = len(h)
    lim = -1e-9 if edge else 0.0
    return n >= 3 and all((h[(i + 1) % n][0] - h[i][0]) * (p[1] - h[i][1])
                          - (h[(i + 1) % n][1] - h[i][1]) * (p[0] - h[i][0]) > lim for i in range(n))


def rule_closed(b, tracer):
    for o in inside_point(b):
        for d in DIRS:
            hs = tracer.hits(o, d, 80.0)
            if not hs:
                return [f"closed: a ray from inside the bay at {tuple(round(c, 2) for c in o)} toward "
                        f"{tuple(round(c, 2) for c in d)} escapes — a gap in the bay's shell"]
            if hs[0][1] in GLASS:
                return [f"closed: from inside the bay at {tuple(round(c, 2) for c in o)} a ray meets glass first — "
                        f"a recess open to the bay's body"]
    return []


def rule_windows(b, tracer):
    fails = []
    for w in b.windows:
        for pane in w["panes"]:
            ou, al = pane["out"], pane["along"]
            start = tuple(pane["at"][k] + ou[k] * 1e-3 for k in range(3))
            for yaw, pitch in ((0, 0), (35, 0), (-35, 0), (0, 25), (0, -25)):
                d = K._mul(ou, -1)
                d = rotate_y(d, yaw)
                d = K._unit(K._add(K._mul(d, math.cos(math.radians(pitch))), K._mul(K.Y, math.sin(math.radians(pitch)))))
                # T-2499: the 3 mm the ray skips (its own pane, which on a curve is a slab whose
                # chord falls inside the true arc by up to its sagitta) is a depth along the pane's
                # normal, so an oblique ray skips 3 mm / cos(its angle off that normal); measured
                # along the ray, a 3.2 m bow's own glass read as a second pane at 35 degrees
                cos_in = -sum(d[k] * ou[k] for k in range(3))
                hs = [h for h in tracer.hits(start, d, 3.0) if h[0] * cos_in > 3e-3]
                if not hs:
                    fails.append(f"recess: a ray in through a pane of {w['opening']} (run {w['run']}, storey "
                                 f"{w['storey']}) reaches nothing within 3 m — no room behind the glass")
                    break
                if hs[0][1] in GLASS:
                    fails.append(f"one layer: a ray in through a pane of {w['opening']} (run {w['run']}, storey "
                                 f"{w['storey']}) meets a second pane before anything opaque")
                    break
                if hs[0][1] not in K.WINDOW_ROLES:
                    fails.append(f"recess: a ray in through a pane of {w['opening']} (run {w['run']}, storey "
                                 f"{w['storey']}) passes its recess and meets the bay's {hs[0][1]} — the room is open")
                    break
            else:
                continue
            break
    return fails


def rule_recesses(b, v, data):
    fails = []
    m = 0.01
    # T-3047: a shallow projection's recesses run back through the host's plane, which its
    # host opens round them (k01_frontage: bay_holes); in front of the plane its runs still hold them
    floor = -(b.meta["recess_m"] - max(q[1] for q in v["plan"]["points"])) - EPS if v.get("shallow") else m
    for w in b.windows:
        if w["recess_m"] < data["parts"]["recess"]["min_m"] - EPS:
            fails.append(f"recess: {w['opening']} recess {w['recess_m']} m is shallower than the kit's minimum")
        inside = _across_inside(b, -m)   # T-3176: across a corner, behind is inside the corner
        for p in w["footprint"]:
            if (inside(p[0], p[1]) if inside is not None else p[1] < floor):
                fails.append(f"recess: {w['opening']} (run {w['run']}) runs to z {p[1]:.3f}, behind or onto the host wall")
                return fails
            # T-1890: a staged tower's stage window is held inside the stage's ring, not the shaft's
            n0 = len(b.runs)
            ring = list(enumerate(b.stage_runs, n0)) if w["run"] >= n0 else list(enumerate(b.runs))
            for i, r in ring:
                if i == w["run"]:
                    continue
                if r.kind == "arc":
                    out = math.hypot(p[0] - r.c[0], p[1] - r.c[1]) > r.R - m
                else:
                    out = (p[0] - r.A[0]) * r.n[0] + (p[1] - r.A[1]) * r.n[1] > -m
                if out:
                    fails.append(f"recess: {w['opening']} (run {w['run']}) pokes through run {i}'s wall")
                    return fails
    for i, w1 in enumerate(b.windows):
        for w2 in b.windows[i + 1:]:
            if w1["y"][0] < w2["y"][1] and w2["y"][0] < w1["y"][1] and convex_overlap(w1["footprint"], w2["footprint"]):
                fails.append(f"recess: the recesses of two windows on storey {w1['storey']} (runs {w1['run']} and "
                             f"{w2['run']}) run into each other")
    return fails


def convex_overlap(a, b) -> bool:
    for poly in (a, b):
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            n = (q[1] - p[1], p[0] - q[0])
            pa = [n[0] * x + n[1] * y for x, y in a]
            pb = [n[0] * x + n[1] * y for x, y in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def rule_curves(b, data, tier):
    fails = []
    cv = data["curves"][tier]
    tol = math.radians(data["curves"]["full"]["normal_tolerance_deg"])
    for r in b.runs:
        if r.kind != "arc":
            continue
        angs, worst = set(), 0.0
        for role in ("wall", "roof"):
            pr = b.prims.get(role)
            if not pr:
                continue
            for p, n in zip(pr.pos, pr.nrm):
                rr = math.hypot(p[0] - r.c[0], p[2] - r.c[1])
                if role == "wall" and abs(rr - r.R) < 1e-6:
                    f = math.atan2(p[2] - r.c[1], p[0] - r.c[0])
                    angs.add(round((r.phi0 - f) % (2 * math.pi), 9))
                    want = (math.cos(f), 0.0, math.sin(f))
                elif role == "roof" and b.meta["roof"]["kind"] == "cone" and rr > 1e-6:
                    f = math.atan2(p[2] - r.c[1], p[0] - r.c[0])
                    pt = b.meta["roof"]["pitch"]
                    want = K._unit((pt * math.cos(f), 1.0, pt * math.sin(f)))
                else:
                    continue
                worst = max(worst, math.acos(max(-1.0, min(1.0, K._dot(n, want)))))
        if worst > tol:
            fails.append(f"normal: a vertex on the curved run is shaded {math.degrees(worst):.2f} degrees off the true "
                         f"curve's normal (tolerance {math.degrees(tol)}) — the slabs will read as facets")
        a = sorted(angs)
        gap = max((q - p for p, q in zip(a, a[1:])), default=0.0)
        sag = r.R * (1 - math.cos(gap / 2))
        if math.degrees(gap) > cv["max_seg_deg"] + 1e-6 or sag > cv["max_sagitta_m"] + 1e-9:
            fails.append(f"facet: the {tier} tier cuts its {r.R:.3f} m curve into {math.degrees(gap):.2f} degree slabs, "
                         f"a {sag * 1000:.1f} mm sagitta (allowed {cv['max_seg_deg']} degrees, "
                         f"{cv['max_sagitta_m'] * 1000:.0f} mm)")
    return fails


def rule_support(b, v, data):
    fails = []
    sg = b.meta.get("stage")
    if sg is not None:
        # T-1890: a staged tower's corbel courses carry its stage back to its shaft
        cb = K.part(v, data, "corbel")
        if sg["step_m"] > cb["max_oversail_ratio"] * sg["course_height_m"] + 1e-6:
            fails.append(f"oversail: the stage's corbel courses step {sg['step_m']:.3f} m, more than "
                         f"{cb['max_oversail_ratio']} of their {sg['course_height_m']} m height")
        if sg["bearing_m"] < cb["min_bearing_m"] - 1e-6:
            fails.append(f"bearing: the stage's lowest corbel course bears on the shaft by {sg['bearing_m']:.3f} m only")
        if not b.prims.get("corbel") or not b.prims["corbel"].idx:
            fails.append("support: a staged tower has no corbel courses under its stage")
    if v["base"] == "grade":
        pl = b.prims.get("plinth")
        h = K.part(v, data, "plinth")["height_m"]
        if not pl or not pl.idx or abs(min(p[1] for p in pl.pos)) > 1e-6 or max(p[1] for p in pl.pos) < h - 1e-6 \
                or h <= 0:
            return ["foundation: a bay on grade stands on no plinth from grade"]
        return fails
    if v.get("apron"):
        return rule_apron(b, b.prims.get("apron"))   # T-2904: the apron's own role
    cb = b.prims.get("corbel")
    meta = b.meta.get("corbel")
    if not cb or not meta:
        return ["support: an oriel off grade has no corbel courses under it"]
    K_, h = meta["courses"], meta["course_height_m"]
    y0 = b.meta["base_m"]
    ratio = K.part(v, data, "corbel")["max_oversail_ratio"]
    prev = meta["reach_m"]
    for k in range(K_):
        lo, hi = y0 - (k + 1) * h, y0 - k * h
        zs = [p[2] for i, p in enumerate(cb.pos) if lo - 1e-6 <= p[1] <= hi + 1e-6 and abs(cb.nrm[i][1]) < 1e-6]
        if not zs:
            return [f"support: corbel course {k} is missing"]
        z = max(zs)
        if prev - z > ratio * h + 1e-6:
            fails.append(f"oversail: corbel course {k} is oversailed by {prev - z:.3f} m, more than "
                         f"{ratio} of its {h} m height")
        prev = z
    if prev < K.part(v, data, "corbel")["min_bearing_m"] - 1e-6:
        fails.append(f"bearing: the lowest corbel course bears on the wall by {prev:.3f} m only")
    return fails


def rule_apron(b, cb):
    """T-2883: an apron is the bay's own plan carried down to its foot: its face stands from the
    floor to the foot's moulding on every run, and the foot's underside closes it back to the wall."""
    meta = b.meta.get("apron")
    if not cb or not meta:
        return ["support: an oriel on an apron has no apron under it"]
    if meta.get("form") == "round":
        return rule_round_apron(b, cb, meta)
    y0, foot, fh = b.meta["base_m"], meta["foot_m"], meta["foot_height_m"]
    fails = []
    if not foot + fh < y0:
        fails.append(f"apron: its foot at {foot} m leaves no face under the floor at {y0} m")
    under = [i for i, p in enumerate(cb.pos) if abs(p[1] - foot) < 1e-6 and cb.nrm[i][1] < -0.99]
    if not under:
        fails.append(f"apron: nothing closes the apron under its foot at {foot} m")
    for i, run in enumerate(b.runs):
        mid = run.world(run.L / 2, 0.0, 0.0)
        face = [p for k, p in enumerate(cb.pos) if abs(cb.nrm[k][1]) < 1e-6
                and abs((p[0] - mid[0]) * run.n[0] + (p[2] - mid[2]) * run.n[1]) < 1e-6] if run.kind == "line" else cb.pos
        ys = [p[1] for p in face]
        if not ys or min(ys) > foot + fh + 1e-6 or max(ys) < y0 - 1e-6:
            fails.append(f"apron: run {i}'s face does not stand from the foot's moulding to the floor at {y0} m")
    return fails


def rule_round_apron(b, cb, meta):
    """T-3007: a round apron is the bay's plan turned under on a quarter round: on every run its
    surface rises from the foot, its radius behind the face, round to the face at the walls'
    foot, and its underside closes it back to the wall at the foot."""
    foot, R = meta["foot_m"], meta["foot_height_m"]
    fails = []
    under = [i for i, p in enumerate(cb.pos) if abs(p[1] - foot) < 1e-6 and cb.nrm[i][1] < -0.99]
    if not under:
        fails.append(f"apron: nothing closes the round apron under its foot at {foot} m")
    for i, run in enumerate(b.runs):
        mid = run.world(run.L / 2, 0.0, 0.0)
        off = [((p[0] - mid[0]) * run.n[0] + (p[2] - mid[2]) * run.n[1], p[1]) for k, p in enumerate(cb.pos)
               if abs(cb.nrm[k][1]) < 0.999] if run.kind == "line" else []
        top = [d for d, y in off if abs(y - (foot + R)) < 1e-6]
        low = [d for d, y in off if abs(y - foot) < 1e-6]
        if run.kind == "line" and (not top or abs(max(top)) > 1e-6 or not low or abs(max(low) + R) > 1e-6):
            fails.append(f"apron: run {i}'s round does not turn from its face at {foot + R:.3f} m to "
                         f"{R} m behind it at its foot ({foot} m)")
    return fails


def rule_doubled(b):
    """check_window_kit.py's rule (no two coplanar faces overlap), its pairs first sifted by
    their bounding boxes: a bent bay has thousands of faces on one horizontal plane."""
    buckets = {}
    for role, pr in b.prims.items():
        if role in K.BOARD_ROLES:
            continue
        for i in range(0, len(pr.idx), 3):
            a, bb, c = (pr.pos[pr.idx[i + k]] for k in range(3))
            n = K._cross(K._sub(bb, a), K._sub(c, a))
            ln = math.sqrt(K._dot(n, n))
            if ln < 1e-12:
                continue
            n = K._mul(n, 1 / ln)
            r3 = [round(x, 3) for x in n]
            k = max(range(3), key=lambda j: (abs(r3[j]), -j))   # one axis per plane, ties broken alike
            if n[k] < 0:
                n = K._mul(n, -1)
            key = (round(n[0], 3), round(n[1], 3), round(n[2], 3), round(K._dot(n, a), 3))
            ax = [j for j in range(3) if j != k]
            p2 = [(p[ax[0]], p[ax[1]]) for p in (a, bb, c)]
            box = (min(q[0] for q in p2), max(q[0] for q in p2), min(q[1] for q in p2), max(q[1] for q in p2))
            buckets.setdefault(key, []).append((box, role, p2))
    for key, items in buckets.items():
        items.sort()
        for i, (ba, ra, pa) in enumerate(items):
            for bb_, rb, pb in items[i + 1:]:
                if bb_[0] >= ba[1] - 1e-9:
                    break
                if bb_[2] >= ba[3] - 1e-9 or ba[2] >= bb_[3] - 1e-9:
                    continue
                if W.overlap2d(pa, pb) > 1e-6:
                    return [f"doubled: a {ra} face and a {rb} face are coplanar and overlap "
                            f"(plane {key}) — z-fighting, a face drawn twice"]
    return []


#: T-1890: a pier's whole budget, at either tier (a box, its floor bands, cap and plinth)
PIER_MAX_TRIANGLES = 120


def rule_light(full, light, data, v=None):
    fails = []
    cv = data["curves"]["light"]
    ratio = cv["max_triangle_ratio"]
    lt = (v or {}).get("light_tier")
    if lt:
        # T-1890: a bay may state its own ratio, with its reason, only for an OPEN opening it
        # holds (a loggia's: no sash, blind or curtain there for the light tier to drop)
        k06 = {x["id"]: x for x in K.K6.load()["variants"]}
        # ...or for a bay with one light a storey under a cornice swept round it and a mansard
        # (1801's south bay, the main cornice and slate carried round it): both stand whole in
        # either tier, and one light a storey leaves the light tier little sash to drop
        swept = ((v.get("overrides") or {}).get("eaves") or {}).get("profile") or (v.get("eaves") or {}).get("cornice")
        dressed = bool(swept) and bool((v.get("roof") or {}).get("mansard")) \
            and all(sum(len(w.get("at") or [0]) for w in st["windows"]) <= 1 for st in v["storeys"])
        if not dressed and not any(k06.get(w["opening"], {}).get("operation") == "open"
                                   for st in v["storeys"] for w in st["windows"]):
            fails.append("light: a bay states its own light_tier ratio but holds no open opening (or one light "
                         "a storey under a swept cornice and a mansard) to warrant it")
        elif not str(lt.get("why", "")).strip() or not cv["max_triangle_ratio"] < lt["max_triangle_ratio"] <= 0.65:
            fails.append(f"light: a bay's own light_tier ratio {lt.get('max_triangle_ratio')} must lie over "
                         f"{cv['max_triangle_ratio']}, at most 0.65, and say why")
        else:
            ratio = lt["max_triangle_ratio"]
    # T-1890: a PIER (1801's, where its gabled section meets the main block) is a plain stone box,
    # no window, curve or carving on it, so the light tier has nothing to drop: it keeps the full
    # tier's triangles, and is held instead to a box's own few
    pier = bool((v or {}).get("pier"))

    def box(b):
        ps = [p for r, pr in b.prims.items() if r not in K.BOARD_ROLES for p in pr.pos]
        return [min(p[k] for p in ps) for k in range(3)] + [max(p[k] for p in ps) for k in range(3)]
    bf, bl = box(full), box(light)
    dev = max(abs(a - c) for a, c in zip(bf, bl))
    if dev > cv["max_sagitta_m"] + 1e-6:
        fails.append(f"silhouette: the light tier's extent is {dev * 1000:.1f} mm off the full tier's "
                     f"(allowed {cv['max_sagitta_m'] * 1000:.0f} mm)")
    tf, tl = K.triangles(full), K.triangles(light)
    if pier:
        if tl > tf or tf > PIER_MAX_TRIANGLES:
            fails.append(f"light: a pier costs {tf} triangles at the full tier and {tl} at the light; a plain "
                         f"box keeps at most {PIER_MAX_TRIANGLES}, the light tier no more than the full")
    elif tl > ratio * tf:
        fails.append(f"light: the light tier costs {tl} triangles, {tl / tf:.2f} of the full tier's {tf} "
                     f"(allowed {ratio})")
    return fails


def rule_costs(b, data, tier):
    t = K.triangles(b)
    cap = data["costs"]["max_triangles"][tier]
    return [f"costs: {t} triangles at the {tier} tier, over its budget of {cap}"] if t > cap else []


def check_variant(v, data, full=None, light=None):
    full = full or K.build_variant(v, data, "full", board=True)
    light = light or K.build_variant(v, data, "light", board=False)
    tracer = Tracer(full)
    return (rule_data(v, data, full) + rule_keyed(full, v) + rule_closed(full, tracer) + rule_windows(full, tracer)
            + rule_recesses(full, v, data) + rule_doubled(full) + rule_curves(full, data, "full")
            + rule_curves(light, data, "light") + rule_support(full, v, data) + rule_light(full, light, data, v)
            + rule_costs(full, data, "full") + rule_costs(light, data, "light"))


def house_bays():
    """Every K08 bay a K01 frontage record carries, resolved as its builder resolves it (T-2308)."""
    import json
    from archetypes import k01_frontage_params as P
    out = []
    for f in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = json.loads(f.read_text())
        if not isinstance(st, dict) or st.get("archetype") != "k01_frontage":
            continue
        for ph in st.get("phases", []):
            out += [b["variant"] for b in P.from_phase(ph, st).bays]
    return out


def check(data, glb_check=True):
    fails = []
    # T-2308: a bay on a house is held to the same rules as the kit's own, at both tiers
    for v in [*data["variants"], *house_bays()]:
        try:
            got = check_variant(v, data)
        except Exception as e:  # a variant the generator cannot build is a failure, not a crash
            fails.append(f"build: {v['id']} does not build ({type(e).__name__}: {e})")
            continue
        fails += [f"{v['id']}: {f}" for f in got]
    if glb_check:
        blob = K.to_glb(K.build_kit(data), data)
        out = ROOT / data["specimen"]
        if not out.exists() or out.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes — run "
                         f"python3 generators/archetypes/k08_bays.py")
    return fails


# -- the self-test: each rule broken, each refused for its own reason --------------------------------

def _v(data, vid):
    return next(v for v in data["variants"] if v["id"] == vid)


def self_test(data) -> int:
    def w0(d, vid):
        return _v(d, vid)["storeys"][0]["windows"][0]

    def m_pier(d):
        w0(d, "k08.bay.canted")["at"] = [0.02, 0.82]

    def m_overlap(d):
        w0(d, "k08.bay.bowed")["at_deg"] = [-36, 0, 10]

    def m_storey(d):
        w0(d, "k08.bay.rectangular")["sill_m"] = 1.7

    def m_why(d):
        _v(d, "k08.oriel.canted_corbelled")["storeys"][0]["windows"][0].pop("why_not_ordinary")

    def m_recess(d):
        _v(d, "k08.bay.canted")["overrides"] = {"recess": {"depth_m": 1.2}}

    def m_facet(d):
        d["curves"]["full"]["max_seg_deg"] = 12.0

    def m_corbel(d):
        _v(d, "k08.oriel.canted_corbelled")["corbel"]["courses"] = 1

    def m_plinth(d):
        d["parts"]["plinth"]["height_m"] = 0.0

    def m_apron(d):   # T-2883: an apron whose foot stands no lower than its own floor
        v = _v(d, "k08.oriel.canted_corbelled")
        v.pop("corbel")
        v["apron"] = {"foot_m": v["base"] - 0.05}

    def m_round(d):   # T-3007: a round apron turned under on more than half a metre
        v = _v(d, "k08.oriel.canted_corbelled")
        v.pop("corbel")
        v["apron"] = {"foot_m": v["base"], "form": "round", "radius_m": 0.6}

    def m_budget(d):
        d["costs"]["max_triangles"]["full"] = 900

    def m_light(d):
        d["curves"]["light"]["max_seg_deg"] = 3.75
        d["curves"]["light"]["drop_roles"] = []

    def m_coarse(d):
        d["curves"]["light"]["max_seg_deg"] = 40.0

    def m_light_own(d):   # T-1890: a bay's own ratio, with no open opening to warrant it
        _v(d, "k08.bay.canted")["light_tier"] = {"max_triangle_ratio": 0.6, "why": "no reason"}

    def m_light_pier(d):   # T-1890: a bay that calls itself a pier keeps no light tier, but only as a box
        _v(d, "k08.bay.canted")["pier"] = True

    cases = [
        ("a window off the end of its run", m_pier, "k08.bay.canted", "pier:"),
        ("two windows on one run, side by side into each other", m_overlap, "k08.bay.bowed", "overlap:"),
        ("a window whose head band runs into the floor band", m_storey, "k08.bay.rectangular", "storey:"),
        ("a narrow cheek light that does not say why", m_why, "k08.oriel.canted_corbelled", "must say why"),
        ("recesses deep enough to meet behind the angle", m_recess, "k08.bay.canted", "recess:"),
        ("a curve cut into 12 degree facets", m_facet, "k08.bay.bowed", "facet:"),
        ("an oriel on one deep corbel course", m_corbel, "k08.oriel.canted_corbelled", "oversail:"),
        ("a bay on grade with no plinth", m_plinth, "k08.bay.canted", "foundation:"),
        ("an oriel on an apron with no face under its floor", m_apron, "k08.oriel.canted_corbelled", "leaves no face"),
        ("an oriel on a round apron of 0.6 m", m_round, "k08.oriel.canted_corbelled", "a round apron turns under"),
        ("a bay over its budget", m_budget, "k08.bay.bowed", "costs:"),
        ("a light tier as heavy as the full", m_light, "k08.bay.canted", "light:"),
        ("a light tier cut so coarse it loses the silhouette", m_coarse, "k08.bay.bowed", "facet: the light tier"),
        ("a glazed bay stating its own light-tier ratio", m_light_own, "k08.bay.canted", "holds no open opening"),
        ("a glazed bay calling itself a pier to keep its light tier", m_light_pier, "k08.bay.canted", "a pier costs"),
    ]
    bad = 0
    for name, mut, vid, want in cases:
        d = copy.deepcopy(data)
        mut(d)
        try:
            got = check_variant(_v(d, vid), d)
        except Exception as e:
            got = [f"build: {e}"]
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> "
              f"{'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused ' + str(got[:2])}")
        bad += not hit

    # geometry breaks, made on a built bay
    geo = []
    v = _v(data, "k08.bay.canted")

    def built(vv=v):
        return K.build_variant(vv, data, "full", board=True)

    b = built()
    rf = b.prims["roof"]
    rf.idx = rf.idx[3:]                                   # a hole in the roof
    geo.append(("a roof with a triangle missing", rule_closed(b, Tracer(b)), "escapes"))
    b = built()
    bk, w = b.prims["backing"], b.windows[0]

    def ours(t):
        c = [sum(bk.pos[bk.idx[t + k]][j] for k in range(3)) / 3 for j in range(3)]
        return w["y"][0] - 1e-6 <= c[1] <= w["y"][1] + 1e-6 and in_hull((c[0], c[2]), w["footprint"])
    keep = [t for t in range(0, len(bk.idx), 3) if not ours(t)]
    bk.idx = [bk.idx[t + k] for t in keep for k in range(3)]   # one window's room taken out
    geo.append(("a window with its room taken out", rule_windows(b, Tracer(b)), "the room is open"))
    b = built()
    gl = b.prims["glass_inner"]
    gl.idx = gl.idx + gl.idx[-3:]
    geo.append(("a pane drawn twice", rule_doubled(b), "coplanar and overlap"))
    vb = _v(data, "k08.bay.bowed")
    b = built(vb)
    wl = b.prims["wall"]
    wl.nrm = [K._unit((n[0] + 0.05, n[1], n[2])) for n in wl.nrm]
    geo.append(("a curved wall shaded with tilted normals", rule_curves(b, data, "full"), "normal:"))
    b = built()
    wl = b.prims["wall"]
    wl.pos[0] = (wl.pos[0][0], wl.pos[0][1], -0.2)
    geo.append(("a wall vertex pushed behind the host wall", rule_keyed(b, v), "behind:"))
    b = built()
    b.prims["wall"].pos = [(p[0], p[1], p[2] + 0.01) for p in b.prims["wall"].pos]
    geo.append(("a wall moved off its declared plan", rule_keyed(b, v), "footprint:"))
    for name, got, want in geo:
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> "
              f"{'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused ' + str(got[:2])}")
        bad += not hit
    clean = check(data, glb_check=False)
    print(f"self-test | {'ok  ' if not clean else 'FAIL'} the committed kit passes ({len(clean)} failures)")
    bad += bool(clean)
    n = len(cases) + len(geo) + 1
    print(f"{'PASS' if not bad else 'FAIL'} — {n - bad} of {n} self-test cases refused as they should be")
    return 1 if bad else 0


def main(argv) -> int:
    data = K.load()
    if "--self-test" in argv:
        return self_test(data)
    if "--check" not in argv:
        print(__doc__)
        return 2
    fails = check(data)
    if fails:
        for f in fails:
            print(f"FAIL {f}")
        print(f"FAIL — {len(fails)} K08 bay kit rule(s) broken")
        return 1
    tris = {v["id"]: K.triangles(K.build_variant(v, data, "full", board=False)) for v in data["variants"]}
    for v in house_bays():
        t = {tier: K.triangles(K.build_variant(v, data, tier, board=False)) for tier in ("full", "light")}
        print(f"ok   {v['id']}: a {v['plan']['kind']} {v['kind']} on its house, {t['full']} triangles full, "
              f"{t['light']} light, held to every rule below")
    print(f"ok   the K08 bay kit: {len(tris)} variants, each keyed to its wall and closed, every pane over its own "
          f"recess one glass layer deep, curves cut fine with true normals, supported on a plinth or corbels, the "
          f"light tier on the full tier's silhouette; {min(tris.values())}-{max(tris.values())} triangles a variant; "
          f"the specimen GLB is the generator's bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
