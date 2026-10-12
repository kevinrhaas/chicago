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
             fraction of its triangles
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
        run = b.runs[w["run"]]
        a, z = w["s_extent"]
        if a < pier - EPS or z > run.L - pier + EPS:
            fails.append(f"pier: {w['opening']} on run {w['run']} reaches s {a:.3f}..{z:.3f} of a {run.L:.3f} m run, "
                         f"closer than {pier} m to its end")
        k = w["storey"]
        floor = levels[k] + (band["height_m"] / 2 if k else (plinth["height_m"] if v["base"] == "grade" else 0))
        ceil = levels[k + 1] - (band["height_m"] / 2 if k + 1 < len(levels) - 1 else 0)
        if w["y_all"][0] < floor - EPS or w["y_all"][1] > ceil + EPS:
            fails.append(f"storey: {w['opening']} on storey {k} spans y {w['y_all'][0]:.3f}..{w['y_all'][1]:.3f}, "
                         f"outside its storey's clear wall {floor:.3f}..{ceil:.3f}")
    for i, w1 in enumerate(b.windows):
        for w2 in b.windows[i + 1:]:
            if (w1["run"], w1["storey"]) == (w2["run"], w2["storey"]) and \
                    w1["s_extent"][0] < w2["s_extent"][1] and w2["s_extent"][0] < w1["s_extent"][1]:
                fails.append(f"overlap: two windows on run {w1['run']} storey {w1['storey']} share s "
                             f"{max(w1['s_extent'][0], w2['s_extent'][0]):.3f}..{min(w1['s_extent'][1], w2['s_extent'][1]):.3f}")
    for st in v["storeys"]:
        for w in st["windows"]:
            if not (lo_w <= w["clear_width_m"] <= hi_w and lo_h <= w["clear_height_m"] <= hi_h) \
                    and not w.get("why_not_ordinary"):
                fails.append(f"ordinary: a {w['clear_width_m']} x {w['clear_height_m']} m sash is outside the "
                             f"reconstruction rules' range and must say why (why_not_ordinary)")
    if v["base"] != "grade" and not v.get("corbel"):
        fails.append("support: a bay off grade must say what carries it (corbel)")
    return fails


def rule_keyed(b, v):
    fails = []
    for r, end in ((b.runs[0], 0.0), (b.runs[-1], b.runs[-1].L)):
        p = r.world(end, 0.0, 0.0)
        if abs(p[2]) > 1e-6:
            fails.append(f"keyed: the plan's end at x {p[0]:.3f} is {p[2]:.4f} m off the host wall's face")
    worst = min((p[2], role) for role, pr in b.prims.items() if role not in K.BOARD_ROLES for p in pr.pos)
    if worst[0] < -1e-6:
        fails.append(f"behind: a {worst[1]} vertex stands {-worst[0]:.4f} m behind the host wall's face")
    # the outer wall on the declared plan
    off = 0.0
    for p in b.prims["wall"].pos:
        off = max(off, min(plan_distance(r, p) for r in b.runs))
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
    for cand in ((0.0, 0.05), (0.0, 0.15), (0.3, 0.1), (-0.3, 0.1)):
        if not any(in_hull(cand, w["footprint"]) for w in b.windows):
            break
    lv = b.meta["levels_m"]
    return [(cand[0], (lv[k] + lv[k + 1]) / 2, cand[1]) for k in range(len(lv) - 1)] + \
           [(cand[0], b.meta["wall_top_m"] + 0.05, cand[1])]


def in_hull(p, h):
    n = len(h)
    return n >= 3 and all((h[(i + 1) % n][0] - h[i][0]) * (p[1] - h[i][1])
                          - (h[(i + 1) % n][1] - h[i][1]) * (p[0] - h[i][0]) > 0 for i in range(n))


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
                hs = [h for h in tracer.hits(start, d, 3.0) if h[0] > 3e-3]
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
    for w in b.windows:
        if w["recess_m"] < data["parts"]["recess"]["min_m"] - EPS:
            fails.append(f"recess: {w['opening']} recess {w['recess_m']} m is shallower than the kit's minimum")
        for p in w["footprint"]:
            if p[1] < m:
                fails.append(f"recess: {w['opening']} (run {w['run']}) runs to z {p[1]:.3f}, behind or onto the host wall")
                return fails
            for i, r in enumerate(b.runs):
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
    if v["base"] == "grade":
        pl = b.prims.get("plinth")
        h = K.part(v, data, "plinth")["height_m"]
        if not pl or not pl.idx or abs(min(p[1] for p in pl.pos)) > 1e-6 or max(p[1] for p in pl.pos) < h - 1e-6 \
                or h <= 0:
            return ["foundation: a bay on grade stands on no plinth from grade"]
        return []
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


def rule_light(full, light, data):
    fails = []
    cv = data["curves"]["light"]

    def box(b):
        ps = [p for r, pr in b.prims.items() if r not in K.BOARD_ROLES for p in pr.pos]
        return [min(p[k] for p in ps) for k in range(3)] + [max(p[k] for p in ps) for k in range(3)]
    bf, bl = box(full), box(light)
    dev = max(abs(a - c) for a, c in zip(bf, bl))
    if dev > cv["max_sagitta_m"] + 1e-6:
        fails.append(f"silhouette: the light tier's extent is {dev * 1000:.1f} mm off the full tier's "
                     f"(allowed {cv['max_sagitta_m'] * 1000:.0f} mm)")
    tf, tl = K.triangles(full), K.triangles(light)
    if tl > cv["max_triangle_ratio"] * tf:
        fails.append(f"light: the light tier costs {tl} triangles, {tl / tf:.2f} of the full tier's {tf} "
                     f"(allowed {cv['max_triangle_ratio']})")
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
            + rule_curves(light, data, "light") + rule_support(full, v, data) + rule_light(full, light, data)
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

    def m_budget(d):
        d["costs"]["max_triangles"]["full"] = 900

    def m_light(d):
        d["curves"]["light"]["max_seg_deg"] = 3.75
        d["curves"]["light"]["drop_roles"] = []

    def m_coarse(d):
        d["curves"]["light"]["max_seg_deg"] = 40.0

    cases = [
        ("a window off the end of its run", m_pier, "k08.bay.canted", "pier:"),
        ("two windows on one run, side by side into each other", m_overlap, "k08.bay.bowed", "overlap:"),
        ("a window whose head band runs into the floor band", m_storey, "k08.bay.rectangular", "storey:"),
        ("a narrow cheek light that does not say why", m_why, "k08.oriel.canted_corbelled", "must say why"),
        ("recesses deep enough to meet behind the angle", m_recess, "k08.bay.canted", "recess:"),
        ("a curve cut into 12 degree facets", m_facet, "k08.bay.bowed", "facet:"),
        ("an oriel on one deep corbel course", m_corbel, "k08.oriel.canted_corbelled", "oversail:"),
        ("a bay on grade with no plinth", m_plinth, "k08.bay.canted", "foundation:"),
        ("a bay over its budget", m_budget, "k08.bay.bowed", "costs:"),
        ("a light tier as heavy as the full", m_light, "k08.bay.canted", "light:"),
        ("a light tier cut so coarse it loses the silhouette", m_coarse, "k08.bay.bowed", "facet: the light tier"),
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
