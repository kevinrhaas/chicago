#!/usr/bin/env python3
"""Hold the K06 window kit to its data, and every built window to being a window (T-2297).

    python3 tools/check_window_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_window_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k06_windows.json and the
generator (generators/archetypes/k06_windows.py) builds every variant from them. This
rebuilds each variant in memory and measures the BUILT geometry, not the data's
promises. The K06 acceptance is "at 2-5 m the opening reads as a recess, glass reflects
and transmits plausibly and blinds remain behind it; zero floating painted rectangles
or unbounded transparency sorting", and each clause is a rule here:

  depth      every stage of data `depth_order` strictly deeper than the last, measured
             per opening; the reveal no deeper than the host wall
  recess     every edge of every hole, at the outer face and at the frame, is closed by
             a reveal or sill face, so the opening is a hole with sides, never a panel
  enclosed   every point of every pane has the dark backing's cap behind it: no ray
             through glass reaches the sky
  one layer  glass is the only transparent material, and no two panes of an opening
             overlap: one transparency per line of sight, so nothing sorts against
             anything
  doubled    no two coplanar faces overlap (the back-to-back coincidence K01 refuses)
  sash       muntins divide each sash's panes evenly; ordinary sashes inside the
             reconstruction rules' range; arches true to their kind; the sill's drip
             under its nose; leaded lights only where the restriction allows
  costs      every opening inside its triangle budget
  metric     TEXCOORD_0 is surface metres (K01 scale_uv with an untextured tile of 1 m)
  specimen   the committed specimen GLB is the generator's bytes
"""

from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k06_windows as K  # noqa: E402

EPS = 1e-6
TRANSPARENT = {"glass"}


def r6(p):
    return tuple(round(c, 6) for c in p)


def faces(o, roles=None):
    """(role, [vertices]) per triangle of the built opening."""
    for role, pr in o.prims.items():
        if roles and role not in roles:
            continue
        for i in range(0, len(pr.idx), 3):
            yield role, [pr.pos[pr.idx[i + k]] for k in range(3)]


def zrange(o, role):
    zs = [p[2] for _, tri in faces(o, {role}) for p in tri]
    return (min(zs), max(zs)) if zs else None


def tri_area2d(t):
    return abs(K.area2(t))


def overlap2d(a, b) -> float:
    """Overlap area of two convex 2D polygons (either winding)."""
    a = a if K.area2(a) > 0 else a[::-1]
    b = b if K.area2(b) > 0 else b[::-1]
    c = K.clip(a, b)
    return abs(K.area2(c)) if len(c) >= 3 else 0.0


def inside(pt, poly) -> bool:
    poly = poly if K.area2(poly) > 0 else poly[::-1]
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0]) < -1e-7:
            return False
    return True


# -- the rules, each returning failure strings -------------------------------------------------

def rule_depth(o, data):
    out = []
    rev = o.meta["reveal_depth_m"]
    wall = data["host_wall"]["thickness_m"]
    if not 0 < rev <= wall:
        out.append(f"depth: reveal {rev} m is not inside (0, host wall {wall} m]")
    stages = [("outer_face", 0.0)]
    probes = [("frame_face", "frame"), ("outer_sash_face", "sash_outer"), ("outer_glass", "glass_outer"),
              ("inner_sash_face", "sash_inner"), ("inner_glass", "glass_inner"), ("blind", "blind"),
              ("curtain", "curtain")]
    for name, role in probes:
        zr = zrange(o, role)
        if zr is not None:
            stages.append((name, zr[1]))      # a stage's front, out of the wall
    zb = zrange(o, "backing")
    if zb is None:
        out.append("depth: no backing — the room behind the glass is missing")
    else:
        stages.append(("backing", zb[0]))     # the backing's cap, its deepest face
    for (na, za), (nb, zb_) in zip(stages, stages[1:]):
        if not zb_ < za - EPS:
            out.append(f"depth: {nb} (z {zb_:.4f}) is not behind {na} (z {za:.4f})")
    glass = [zrange(o, r) for r in ("glass_outer", "glass_inner") if zrange(o, r)]
    deepest_glass = min(g[0] for g in glass)
    for role in ("blind", "curtain"):
        zr = zrange(o, role)
        if zr and zr[1] > deepest_glass - EPS:
            out.append(f"depth: the {role} reaches z {zr[1]:.4f}, in front of the innermost glass "
                       f"(z {deepest_glass:.4f})")
    need = data["parts"]["backing"]["depth_m"]
    if zb and deepest_glass - zb[0] < need - 1e-4:
        out.append(f"depth: the backing cap is {deepest_glass - zb[0]:.3f} m behind the innermost glass, "
                   f"under backing.depth_m {need}")
    return out


def rule_recess(o, data):
    """Each hole edge is an edge of some reveal or sill face: the hole is closed."""
    out = []
    edges = set()
    for _, tri in faces(o, {"reveal", "sill"}):
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges.add(frozenset((r6(a), r6(b))))
    # a quad is fanned from its first vertex, so each of its four edges is a triangle edge
    rev = o.meta["reveal_depth_m"]
    yf = o.meta["sill_top_at_frame_m"]
    for hole in o.holes:
        for i, a in enumerate(hole):
            b = hole[(i + 1) % len(hole)]
            for d, lift in ((0.0, False), (rev, True)):
                pa = o.P(a[0], yf if lift and abs(a[1]) < 1e-9 else a[1], d)
                pb = o.P(b[0], yf if lift and abs(b[1]) < 1e-9 else b[1], d)
                if frozenset((r6(pa), r6(pb))) not in edges:
                    out.append(f"recess: the hole's edge {a}->{b} at depth {d} m has no reveal or sill face "
                               f"— an open slot, not a recess")
                    return out
    return out


def rule_enclosed(o, data):
    out = []
    caps = [tri for _, tri in faces(o, {"backing"}) if abs(tri[0][2] - tri[1][2]) < EPS
            and abs(tri[1][2] - tri[2][2]) < EPS]
    if not caps:
        return ["enclosed: the backing has no cap"]
    zcap = min(t[0][2] for t in caps)
    cap2 = [[(p[0] - o.O[0], p[1] - o.O[1]) for p in t] for t in caps if abs(t[0][2] - zcap) < EPS]
    for pane in o.panes:
        poly = pane["poly"]
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        for fx, fy in itertools.product((0.1, 0.5, 0.9), (0.1, 0.5, 0.9)):
            pt = (min(xs) + fx * (max(xs) - min(xs)), min(ys) + fy * (max(ys) - min(ys)))
            if not inside(pt, poly):
                continue
            if not any(inside(pt, t) for t in cap2):
                out.append(f"enclosed: a ray through the {pane['sash']} pane at {tuple(round(c, 3) for c in pt)} "
                           f"meets no backing — it reaches the sky")
                return out
    return out


def rule_one_layer(o, data, mats):
    out = []
    for role in o.prims:
        m = mats[K.ROLE_MATERIAL[role]]
        if m.get("alpha", 1.0) < 1.0 and K.ROLE_MATERIAL[role] not in TRANSPARENT:
            out.append(f"one layer: {role} ({K.ROLE_MATERIAL[role]}) is transparent; only glass may be")
    for a, b in itertools.combinations(o.panes, 2):
        if overlap2d(a["poly"], b["poly"]) > EPS:
            out.append(f"one layer: the {a['sash']} and {b['sash']} panes overlap in elevation — two "
                       f"transparencies on one line of sight")
            break
    glass_area = sum(tri_area2d([(p[0], p[1]) for p in t]) for _, t in faces(o, {"glass_outer", "glass_inner"}))
    pane_area = sum(abs(K.area2(p["poly"])) for p in o.panes)
    if abs(glass_area - pane_area) > 1e-5:
        out.append(f"one layer: the glass drawn ({glass_area:.4f} m2) is not the panes recorded ({pane_area:.4f} m2)")
    return out


def rule_doubled(o, data):
    buckets = {}
    for role, tri in faces(o):
        a, b, c = tri
        n = K._cross(K._sub(b, a), K._sub(c, a))
        ln = math.sqrt(K._dot(n, n))
        if ln < 1e-12:
            continue
        n = K._mul(n, 1 / ln)
        k = max(range(3), key=lambda i: abs(n[i]))
        if n[k] < 0:
            n = K._mul(n, -1)
        key = (round(n[0], 3), round(n[1], 3), round(n[2], 3), round(K._dot(n, a), 3))
        buckets.setdefault(key, []).append((role, tri, k))
    for key, items in buckets.items():
        if len(items) < 2:
            continue
        for (ra, ta, k), (rb, tb, _) in itertools.combinations(items, 2):
            ax = [i for i in range(3) if i != k]
            pa = [(p[ax[0]], p[ax[1]]) for p in ta]
            pb = [(p[ax[0]], p[ax[1]]) for p in tb]
            if overlap2d(pa, pb) > 1e-6:
                return [f"doubled: a {ra} face and a {rb} face are coplanar and overlap "
                        f"(plane {key}) — z-fighting, a face drawn twice"]
    return []


def rule_sash(o, v, data):
    out = []
    by = {}
    for p in o.panes:
        if p["sash"] == "fanlight":
            continue
        xs = [q[0] for q in p["poly"]]
        by.setdefault((p["sash"], round(min(q[1] for q in p["poly"]), 3)), []).append(max(xs) - min(xs))
    for (sash, _), widths in by.items():
        if max(widths) - min(widths) > 1e-3:
            out.append(f"sash: the {sash} sash's panes are uneven ({[round(w, 3) for w in widths]} m) — "
                       f"the muntins must divide it evenly")
    rg = data["ranges"]
    if v["ordinary"]:
        w = o.meta["bay_width_m"]
        if not (rg["ordinary_clear_width_m"][0] <= w <= rg["ordinary_clear_width_m"][1]
                and rg["ordinary_clear_height_m"][0] <= v["clear_height_m"] <= rg["ordinary_clear_height_m"][1]):
            out.append(f"sash: an ordinary sash {w} x {v['clear_height_m']} m is outside the reconstruction rules' "
                       f"range {rg['ordinary_clear_width_m']} x {rg['ordinary_clear_height_m']}")
    elif not v.get("why_not_ordinary"):
        out.append("sash: a variant that is not ordinary must say why (why_not_ordinary)")
    for h in o.meta["heads"]:
        span, rise, kind = h["span_m"], h["rise_m"], h["kind"]
        ok = {"flat": rise == 0, "segmental": 0 < rise < span / 2 - 1e-4,
              "round": abs(rise - span / 2) < 1e-3, "pointed": rise > span / 2 + 1e-4}[kind]
        if not ok:
            out.append(f"sash: a {kind} head of span {span} m rises {rise} m, untrue to its kind")
    dr = data["parts"]["sill"]["drip"]
    pr = data["parts"]["sill"]["projection_m"]
    if not (0 < dr["from_front_m"] and dr["from_front_m"] + dr["width_m"] < pr):
        out.append(f"sash: the sill's drip ({dr}) is not under its {pr} m nose")
    if v["operation"] == "fixed_leaded":
        res = next(r for r in data["restrictions"] if r["part"] == "leaded")
        area = v["clear_width_m"] * v["clear_height_m"]
        if v["use"] not in res["allowed_uses"] or area > res["max_area_m2"]:
            out.append(f"sash: a leaded light in a {v['use']} position of {area:.2f} m2 breaks the restriction "
                       f"({res['allowed_uses']}, max {res['max_area_m2']} m2)")
    if (v.get("bays", 1) > 1 or v.get("well")) and v["ordinary"]:
        out.append("sash: a grouped or well-set opening cannot be marked ordinary")
    return out


def rule_costs(o, v, data):
    cls = "leaded" if v["operation"] == "fixed_leaded" else (
        "grouped" if v.get("bays", 1) > 1 or v.get("well") else "ordinary")
    cap = data["costs"]["max_triangles"][cls]
    t = K.triangles(o)
    return [] if t <= cap else [f"costs: {v['id']} is {t} triangles, over its {cls} budget of {cap}"]


def rule_metric(o, data):
    for role, pr in o.prims.items():
        for i in range(0, len(pr.idx), 3):
            a, b = pr.idx[i], pr.idx[i + 1]
            dp = math.dist(pr.pos[a], pr.pos[b])
            du = math.dist(pr.uv[a], pr.uv[b])
            if dp > 1e-4 and abs(du / dp - 1) > 1e-3:
                return [f"metric: a {role} face maps {du / dp:.3f} UV units per metre, not 1"]
    return []


def rule_data(data):
    out = []
    ids = [v["id"] for v in data["variants"]]
    if len(set(ids)) != len(ids):
        out.append("data: variant ids repeat")
    for i in ids:
        if not i.startswith("k06.opening."):
            out.append(f"data: {i} is not a k06.opening.* id")
    for v in data["variants"]:
        if v.get("confidence") not in ("attested", "inferred", "reconstructed"):
            out.append(f"data: {v['id']} has no confidence")
        elif v["confidence"] != "attested" and not v.get("note"):
            out.append(f"data: {v['id']} is {v['confidence']} with no note")
        for sid in [s for s in v.get("sources", [])]:
            if not (ROOT / "data" / "sources" / f"{sid}.json").exists():
                out.append(f"data: {v['id']} cites {sid}, which data/sources/ does not hold")
    return out


def check(data, glb_check=True):
    fails = list(rule_data(data))
    mats = K.materials(data)
    for v in data["variants"]:
        try:
            o = K.build_variant(v, data, board=False)
        except Exception as e:  # a variant the generator cannot build is a failure, not a crash
            fails.append(f"build: {v['id']} does not build ({e})")
            continue
        for f in (rule_depth(o, data) + rule_recess(o, data) + rule_enclosed(o, data)
                  + rule_one_layer(o, data, mats) + rule_doubled(o, data) + rule_sash(o, v, data)
                  + rule_costs(o, v, data) + rule_metric(o, data)):
            fails.append(f"{v['id']}: {f}")
    if glb_check:
        blob = K.to_glb(K.build_kit(data), data)
        out = ROOT / data["specimen"]
        if not out.exists() or out.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes — run "
                         f"python3 generators/archetypes/k06_windows.py")
    return fails


# -- the self-test: each rule broken in memory, each refused for its own reason ------------------

def _v(data, vid):
    return next(v for v in data["variants"] if v["id"] == vid)


def self_test(data) -> int:
    def m_reveal(d):
        d["parts"]["reveal_depth_m"]["value"] = 0.5

    def m_blind(d):
        d["parts"]["blind"]["gap_m"] = -0.09

    def m_backing(d):
        d["parts"]["backing"]["depth_m"] = 0.05

    def m_width(d):
        _v(d, "k06.opening.sash_2over2_flat")["clear_width_m"] = 1.4

    def m_rise(d):
        d["arch"]["segmental"]["working_rise_over_span"] = 0.6

    def m_leaded(d):
        _v(d, "k06.opening.leaded_stair")["use"] = "principal"

    def m_cost(d):
        d["costs"]["max_triangles"]["ordinary"] = 100

    def m_why(d):
        _v(d, "k06.opening.sash_paired_flat").pop("why_not_ordinary")

    def m_drip(d):
        d["parts"]["sill"]["drip"]["from_front_m"] = 0.2

    cases = [
        ("a reveal deeper than its wall", m_reveal, "depth: reveal"),
        ("a blind in front of the glass", m_blind, "in front of the innermost glass"),
        ("a backing that stops short of the curtain", m_backing, "depth: backing"),
        ("an ordinary sash too wide", m_width, "outside the reconstruction rules' range"),
        ("a segmental arch risen past a semicircle", m_rise, "untrue to its kind"),
        ("a leaded light on a street front", m_leaded, "breaks the restriction"),
        ("an opening over budget", m_cost, "over its ordinary budget"),
        ("a grouped window that does not say why", m_why, "must say why"),
        ("a drip groove outside the sill", m_drip, "drip"),
    ]
    bad = 0
    for name, mut, want in cases:
        d = copy.deepcopy(data)
        mut(d)
        got = check(d, glb_check=False)
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> {'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit

    # geometry breaks, made on a built opening
    v = _v(data, "k06.opening.sash_round_fanlight")
    mats = K.materials(data)

    def built():
        return K.build_variant(v, data, board=False)

    geo = []
    o = built()
    rv = o.prims["reveal"]
    rv.idx = rv.idx[6:]                       # drop a jamb
    geo.append(("a jamb missing from the reveal", rule_recess(o, data), "open slot"))
    o = built()
    bk = o.prims["backing"]
    bk.idx = bk.idx[:-3 * 6]                   # drop the cap's last triangles
    geo.append(("a backing cap with a hole in it", rule_enclosed(o, data), "reaches the sky"))
    o = built()
    gl = o.prims["glass_inner"]
    gl.idx = gl.idx + gl.idx[-3:]              # a pane drawn twice
    geo.append(("a pane drawn twice", rule_doubled(o, data), "coplanar and overlap"))
    o = built()
    mats2 = copy.deepcopy(mats)
    mats2["curtain"]["alpha"] = 0.5
    geo.append(("a transparent curtain", rule_one_layer(o, data, mats2), "only glass may be"))
    o = built()
    o.panes.append(dict(o.panes[0]))
    geo.append(("two panes on one line of sight", rule_one_layer(o, data, mats), "overlap in elevation"))
    v22 = _v(data, "k06.opening.sash_2over2_flat")
    o = K.build_variant(v22, data, board=False)
    p0 = o.panes[0]                            # the upper sash's left pane, made narrower
    x0 = min(q[0] for q in p0["poly"])
    p0["poly"] = [(x0 + (x - x0) * 0.8, y) for x, y in p0["poly"]]
    geo.append(("muntins that divide a sash unevenly", rule_sash(o, v22, data), "uneven"))
    o = built()
    pr = o.prims["frame"]
    pr.uv = [(u * 2, w * 2) for u, w in pr.uv]
    geo.append(("a face mapped at twice its size", rule_metric(o, data), "UV units per metre"))
    for name, got, want in geo:
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> {'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit
    clean = check(data, glb_check=False)
    print(f"self-test | {'ok  ' if not clean else 'FAIL'} the committed kit passes ({len(clean)} failures)")
    bad += bool(clean)
    print(f"{'PASS' if not bad else 'FAIL'} — {len(cases) + len(geo) + 1 - bad} of {len(cases) + len(geo) + 1} "
          f"self-test cases refused as they should be")
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
        print(f"FAIL — {len(fails)} K06 window kit rule(s) broken")
        return 1
    n = len(data["variants"])
    tris = [K.triangles(K.build_variant(v, data, board=False)) for v in data["variants"]]
    print(f"ok   the K06 window kit: {n} variants, each a recess with a closed reveal, its stages in depth order, "
          f"one glass layer per line of sight over an enclosed room, no doubled face; {min(tris)}-{max(tris)} "
          f"triangles an opening; the specimen GLB is the generator's bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
