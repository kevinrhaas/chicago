#!/usr/bin/env python3
"""Hold the K13 conservatory kit to its data, and every built house to being legible (T-2305).

    python3 tools/check_conservatory_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_conservatory_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k13_conservatories.json and the
generator (generators/archetypes/k13_conservatories.py) builds every variant from them.
This rebuilds each variant in memory and measures the BUILT geometry, not the data's
promises. The K13 acceptance is "glazing and frame hierarchy remain legible in browser;
avoid overlapping transparency and a full interior plant scene", and each clause is a
rule here:

  hierarchy  every primary member stands prouder and is wider than every secondary,
             and every secondary than every glazing bar, measured on the built members
  panes      every pane between its bars inside the glass range, and the bars of each
             run dividing it evenly
  envelope   the transparent glass of a house is ONE convex envelope, every pane facing
             out and single-sided, so a line of sight from outside enters by one pane
             and every other pane on it faces away and is not drawn: one transparency
             per line of sight. Only the glass is transparent
  plinth     the plinth's height inside its range, and no glass below its coping
  rainwater  every eave sheds into a K04 gutter falling to an outlet no more than K04's
             spacing away; every outlet leads to a pipe that starts inside the gutter,
             clears the coping by K04's offset and ends at K04's height over grade
  planting   the staging and its plants opaque, inside the glass by a clearance, below
             the eave by a margin, and inside a triangle budget: backing, not a scene
  curve      a curvilinear roof's facets meet on the declared quarter-ellipse and no
             chord falls further inside it than the data allows; a rib on every facet
  doubled    no two coplanar faces overlap (the back-to-back coincidence K01 refuses)
  costs      every house inside its triangle budget
  metric     TEXCOORD_0 is surface metres (K01 scale_uv with an untextured tile of 1 m)
  specimen   the committed specimen GLB is the generator's bytes, its glass single-sided
"""

from __future__ import annotations

import copy
import itertools
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k13_conservatories as K  # noqa: E402
from archetypes.k06_windows import area2, clip  # noqa: E402

EPS = 1e-6
TRANSPARENT = {"glass"}


def tris(h, roles=None):
    """(role, [vertices], normal) per triangle of the built house (local frame)."""
    for role, pr in h.prims.items():
        if roles and role not in roles:
            continue
        for i in range(0, len(pr.idx), 3):
            ids = [pr.idx[i + k] for k in range(3)]
            yield role, [K._sub(pr.pos[j], h.O) for j in ids], pr.nrm[ids[0]]


def overlap2d(a, b) -> float:
    a = a if area2(a) > 0 else a[::-1]
    b = b if area2(b) > 0 else b[::-1]
    c = clip(a, b)
    return abs(area2(c)) if len(c) >= 3 else 0.0


def seg_dist(p, a, b):
    ab = (b[0] - a[0], b[1] - a[1])
    ll = ab[0] ** 2 + ab[1] ** 2
    t = 0.0 if ll < 1e-12 else max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / ll))
    return math.hypot(p[0] - a[0] - t * ab[0], p[1] - a[1] - t * ab[1])


# -- the rules, each returning failure strings -------------------------------------------------

def rule_hierarchy(h, data):
    out = []
    by = {t: [m for m in h.members if m["tier"] == t] for t in K.TIERS}
    for t in K.TIERS:
        if not by[t]:
            out.append(f"hierarchy: no {t} member was built")
    if out:
        return out
    for hi, lo in (("primary", "secondary"), ("secondary", "tertiary")):
        s_lo = max(m["standing"] for m in by[lo])
        s_hi = min(m["standing"] for m in by[hi])
        if not s_hi > s_lo + EPS:
            out.append(f"hierarchy: a {lo} member stands {s_lo:.4f} m proud, not below every {hi} "
                       f"({s_hi:.4f} m) — the tiers do not read in order")
        w_lo = max(m["width"] for m in by[lo])
        w_hi = min(m["width"] for m in by[hi])
        if not w_hi > w_lo + EPS:
            out.append(f"hierarchy: a {lo} member is {w_lo:.4f} m wide, not narrower than every {hi} ({w_hi:.4f} m)")
    for m in h.members:
        if m["standing"] <= EPS or m["behind"] <= EPS:
            out.append(f"hierarchy: a {m['tier']} {m['kind']} on {m['panel']} does not stand proud of and run "
                       f"behind the glass")
            break
    return out


def rule_panes(h, data):
    out = []
    lo, hi = data["glass"]["pane_width_m"]["min"], data["glass"]["pane_width_m"]["max"]
    if not h.panes:
        return ["panes: no glass was built"]
    for p in h.panes:
        if not lo - EPS <= p["u_width"] <= hi + EPS:
            out.append(f"panes: a pane on {p['panel']} is {p['u_width']:.3f} m between its bars, outside "
                       f"{lo}-{hi} m")
            break
    runs = {}
    for p in h.panes:
        runs.setdefault((p["panel"], p["segment"]), []).append(p["u_width"])
    for (panel, seg), ws in runs.items():
        if max(ws) - min(ws) > 1e-6:
            out.append(f"panes: the bars on {panel} (run {seg}) divide it unevenly ({sorted(round(w, 4) for w in ws)})")
            break
    return out


def rule_envelope(h, data, mats):
    out = []
    for role in h.prims:
        m = mats[K.ROLE_MATERIAL[role]]
        if m.get("alpha", 1.0) < 1.0 and K.ROLE_MATERIAL[role] not in TRANSPARENT:
            out.append(f"envelope: {role} ({K.ROLE_MATERIAL[role]}) is transparent; only glass may be")
    if data["glass"].get("double_sided", False):
        out.append("envelope: the glass is declared double-sided; a pane leaving the house would be drawn too")
    glass = [(t, n) for _, t, n in tris(h, {"glass"})]
    if not glass:
        return out + ["envelope: no transparent glass"]
    verts = [p for t, _ in glass for p in t]
    c = tuple(sum(p[k] for p in verts) / len(verts) for k in range(3))
    planes = {}
    for t, n in glass:
        cen = tuple(sum(p[k] for p in t) / 3 for k in range(3))
        if K._dot(K._sub(cen, c), n) <= 0:
            out.append(f"envelope: a pane at {tuple(round(x, 2) for x in cen)} faces into the house, not out")
            return out
        planes.setdefault(tuple(round(x, 4) for x in n) + (round(K._dot(n, t[0]), 4),), (n, t[0]))
    for n, p0 in planes.values():
        worst = max(K._dot(K._sub(p, p0), n) for p in verts)
        if worst > 1e-5:
            out.append(f"envelope: glass stands {worst:.3f} m outside the plane of another pane — the envelope "
                       f"is not convex, so one line of sight can cross two transparent panes")
            return out
    return out


def rule_plinth(h, data):
    out = []
    pl = data["plinth"]
    if not pl["range_m"][0] <= pl["height_m"] <= pl["range_m"][1]:
        out.append(f"plinth: height {pl['height_m']} m is outside its range {pl['range_m']}")
    low = min((p[1] for _, t, _ in tris(h, {"glass"}) for p in t), default=None)
    if low is not None and low < pl["height_m"] - EPS:
        out.append(f"plinth: glass reaches {low:.3f} m, below the coping at {pl['height_m']} m")
    if not any(r in h.prims for r in ("plinth", "coping")):
        out.append("plinth: no plinth was built")
    return out


def rule_rainwater(h, data):
    out = []
    k04 = h.k04
    spacing = k04["gutter"]["outlet"]["spacing_max_m"]
    end_above = k04["downpipe"]["shoe"]["end_above_grade_m"]
    clear = k04["downpipe"]["offset_from_wall_m"]
    pt = data["plinth"]["height_m"]
    for e in h.edges:
        if e["kind"] != "eave" or any(p.lantern for p, _ in e["owners"]):
            continue
        mid = K.plan(tuple((a + b) / 2 for a, b in zip(e["a"], e["b"])))
        if not any(min(seg_dist(mid, K.plan(a), K.plan(b)) for a, b in zip(g["path"], g["path"][1:]))
                   < g["offset_m"] + 0.1 for g in h.gutters):
            out.append(f"rainwater: the eave at {tuple(round(x, 2) for x in e['a'])} sheds into no gutter")
            return out
    for g in h.gutters:
        pipes = [p for p in h.pipes if p["gutter"] == g["eave"]]
        if not pipes:
            out.append(f"rainwater: the {g['eave']} gutter has no outlet pipe")
            continue
        if g["length_m"] / len(pipes) > spacing + EPS:
            out.append(f"rainwater: the {g['eave']} gutter runs {g['length_m']:.2f} m to {len(pipes)} outlet(s), "
                       f"over K04's {spacing} m an outlet")
        rims = g["rim_m"]
        ends = {"end": [rims[-1]], "start": [rims[0]], "both": [rims[0], rims[-1]]}[g["outlet"]]
        if not max(ends) < max(rims) - EPS:
            out.append(f"rainwater: the {g['eave']} gutter does not fall to its outlet")
        for p in pipes:
            top, bot = p["stations"][0], p["stations"][-1]
            d = min(seg_dist(K.plan(top), K.plan(a), K.plan(b)) for a, b in zip(g["path"], g["path"][1:]))
            y_rim = p["outlet"][1]
            if d > g["radius_m"] - p["radius_m"] + EPS or not y_rim - g["radius_m"] - EPS <= top[1] <= y_rim:
                out.append(f"rainwater: the {g['eave']} pipe does not start inside its gutter")
            if abs(bot[1] - end_above) > 1e-6:
                out.append(f"rainwater: the {g['eave']} pipe ends {bot[1]:.3f} m over grade, not at K04's "
                           f"{end_above} m — it does not reach the ground")
            for s in p["stations"]:
                if s[1] > pt + 0.1:
                    continue
                dd = min(seg_dist(K.plan(s), a, b) for a, b in h.coping_lines)
                if dd < p["radius_m"] + clear - 1e-6:
                    out.append(f"rainwater: the {g['eave']} pipe passes {dd - p['radius_m']:.3f} m from the coping, "
                               f"inside K04's {clear} m")
                    break
    return out


def rule_planting(h, data):
    out = []
    st = data["staging"]
    glass = [(t, n) for _, t, n in tris(h, {"glass"})]
    planes = {tuple(round(x, 4) for x in n) + (round(K._dot(n, t[0]), 4),): (n, t[0]) for t, n in glass}
    verts = [p for _, t, _ in tris(h, {"plant", "bench"}) for p in t]
    if not verts:
        return ["planting: no staging or plants"]
    for n, p0 in planes.values():
        worst = max(K._dot(K._sub(p, p0), n) for p in verts)
        if worst > -st["clear_of_glass_m"] + EPS:
            out.append(f"planting: a plant or bench comes within {-worst:.3f} m of the glass, inside "
                       f"clear_of_glass_m {st['clear_of_glass_m']}")
            break
    top = max(p[1] for _, t, _ in tris(h, {"plant"}) for p in t)
    cap = h.meta["eave_m"] - st["below_eave_m"]
    if top > cap + EPS:
        out.append(f"planting: a plant rises to {top:.2f} m, within {st['below_eave_m']} m of the eave — a plant "
                   f"scene, not a backing")
    n = sum(len(h.prims[r].idx) // 3 for r in ("plant", "bench") if r in h.prims)
    if n > st["max_triangles"]:
        out.append(f"planting: {n} triangles of staging and plants, over its {st['max_triangles']}")
    return out


def rule_curve(h, data):
    if h.v["form"] != "curvilinear_lean_to":
        return []
    out = []
    v = h.v
    D, he, rise = v["depth_m"], v["eave_m"], v["rise_m"]
    facets = [p for p in h.panels if p.name.startswith("facet_")]
    for p in facets:
        for q in p.pts:
            r = (q[2] / D) ** 2 + ((q[1] - he) / rise) ** 2
            if abs(r - 1) > 1e-6:
                return [f"curve: {p.name} has a corner off the quarter-ellipse ({r:.4f})"]
    sag = 0.0
    for p in facets:
        (z0, y0), (z1, y1) = sorted({(round(q[2], 9), round(q[1], 9)) for q in p.pts})[:2]
        t0, t1 = math.atan2((y0 - he) / rise, z0 / D), math.atan2((y1 - he) / rise, z1 / D)
        for k in range(1, 16):
            t = t0 + (t1 - t0) * k / 16
            z, y = D * math.cos(t), he + rise * math.sin(t)
            sag = max(sag, seg_dist((z, y), (z0, y0), (z1, y1)))
    if sag > data["curve"]["max_sag_m"] + EPS:
        out.append(f"curve: a facet's chord falls {sag:.3f} m inside the curve, over max_sag_m "
                   f"{data['curve']['max_sag_m']}")
    per = {}
    for name, _ in h.ribs:
        per[name] = per.get(name, 0) + 1
    if any(per.get(p.name, 0) != v["bays"] - 1 for p in facets):
        out.append("curve: a facet is missing its ribs")
    return out


def rule_vent(h, data):
    if not h.v.get("ridge_vent"):
        return []
    if not h.meta.get("vents") or "vent" not in h.prims:
        return ["vent: ridge_vent is declared and no ventilator was built"]
    return []


def rule_doubled(h, data):
    buckets = {}
    for role, tri, _ in tris(h):
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


def rule_costs(h, data):
    cap = data["costs"]["max_triangles"]
    t = K.triangles(h)
    return [] if t <= cap else [f"costs: {h.v['id']} is {t} triangles, over its budget of {cap}"]


def rule_metric(h, data):
    for role, pr in h.prims.items():
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
    for v in data["variants"]:
        if not v["id"].startswith(("k13.house.", "k13.bay.")):
            out.append(f"data: {v['id']} is not a k13.house.* or k13.bay.* id")
        if v.get("form") not in K.FORMS:
            out.append(f"data: {v['id']} has no known form ({v.get('form')})")
        if v.get("confidence") not in ("attested", "inferred", "reconstructed"):
            out.append(f"data: {v['id']} has no confidence")
        elif v["confidence"] != "attested" and not v.get("note"):
            out.append(f"data: {v['id']} is {v['confidence']} with no note")
        for sid in v.get("sources", []):
            if not (ROOT / "data" / "sources" / f"{sid}.json").exists():
                out.append(f"data: {v['id']} cites {sid}, which data/sources/ does not hold")
    t = data["tiers"]
    for hi, lo in (("primary", "secondary"), ("secondary", "tertiary")):
        for k in ("width_m", "proud_m"):
            if not t[hi][k] > t[lo][k]:
                out.append(f"data: tier {hi} {k} {t[hi][k]} is not over {lo}'s {t[lo][k]}")
    if not t["primary"]["edge_half_m"] > t["secondary"]["edge_half_m"]:
        out.append("data: the primary edge member is not wider than the secondary")
    return out


def scene_houses(data, fails):
    """[(structure id, phase id, house)] for every k13_conservatories record, built as
    generators/k13_emit.py builds it (T-2306)."""
    out = []
    for p in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = json.loads(p.read_text())
        if not isinstance(st, dict) or st.get("archetype") != "k13_conservatories":
            continue
        for phase in st.get("phases", []):
            v = (phase.get("form", {}).get("conservatory") or {}).get("value") or {}
            if not str(v.get("id", "")).startswith("k13."):
                fails.append(f"{st['id']}/{phase['id']}: its conservatory is not a k13.* component")
            if v.get("form") not in K.FORMS:
                fails.append(f"{st['id']}/{phase['id']}: its conservatory has no known form ({v.get('form')})")
                continue
            try:
                out.append((st["id"], phase["id"], K.structure_house(st, phase, data)))
            except Exception as e:  # noqa: BLE001
                fails.append(f"{st['id']}/{phase['id']}: does not build ({type(e).__name__}: {e})")
    return out


def check(data, glb_check=True):
    fails = list(rule_data(data))
    mats = K.materials(data)
    for i, v in enumerate(data["variants"]):
        try:
            h = K.build_variant(v, data, with_board=False, index=i)
        except Exception as e:  # a variant the generator cannot build is a failure, not a crash
            fails.append(f"build: {v['id']} does not build ({type(e).__name__}: {e})")
            continue
        for f in (rule_hierarchy(h, data) + rule_panes(h, data) + rule_envelope(h, data, mats)
                  + rule_plinth(h, data) + rule_rainwater(h, data) + rule_planting(h, data)
                  + rule_curve(h, data) + rule_vent(h, data) + rule_doubled(h, data)
                  + rule_costs(h, data) + rule_metric(h, data)):
            fails.append(f"{v['id']}: {f}")
    # T-2306: and every house a structure record builds from the kit, held to the same rules
    for sid, phase_id, h in scene_houses(data, fails):
        for f in (rule_hierarchy(h, data) + rule_panes(h, data) + rule_envelope(h, data, mats)
                  + rule_plinth(h, data) + rule_rainwater(h, data) + rule_planting(h, data)
                  + rule_curve(h, data) + rule_vent(h, data) + rule_doubled(h, data)
                  + rule_costs(h, data) + rule_metric(h, data)):
            fails.append(f"{sid}/{phase_id}: {f}")
    if glb_check:
        blob = K.to_glb(K.build_kit(data), data)
        out = ROOT / data["specimen"]
        if not out.exists() or out.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes — run "
                         f"python3 generators/archetypes/k13_conservatories.py")
        else:
            n = struct.unpack("<I", blob[12:16])[0]
            gltf = json.loads(blob[20:20 + n])
            if any(m.get("doubleSided") for m in gltf["materials"]):
                fails.append("specimen: a material is double-sided; the glass must be drawn from outside only")
    return fails


# -- the self-test: each rule broken in memory, each refused for its own reason ------------------

def _v(data, vid):
    return next(v for v in data["variants"] if v["id"] == vid)


def self_test(data) -> int:
    def m_bar(d):
        d["tiers"]["tertiary"]["width_m"] = 0.06
        d["tiers"]["tertiary"]["proud_m"] = 0.045

    def m_pane(d):
        d["glass"]["pane_width_m"]["min"] = 0.36

    def m_plinth(d):
        d["plinth"]["height_m"] = 1.2

    def m_gutter(d):
        _v(d, "k13.house.lean_to")["gutters"] = []

    def m_plants(d):
        d["staging"]["border"]["height_m"] = [1.9, 2.4]

    def m_cost(d):
        d["costs"]["max_triangles"] = 1000

    def m_facets(d):
        d["curve"]["facets"] = 3

    def m_lantern(d):
        d["lantern"]["glazing"] = "glass"

    def m_vent(d):
        _v(d, "k13.house.span")["ridge_vent"] = False
        _v(d, "k13.house.span")["ridge_vent_required"] = True

    def m_double(d):
        d["glass"]["double_sided"] = True

    cases = [
        ("glazing bars as heavy as the plates", m_bar, "hierarchy"),
        ("panes narrower than the glass range", m_pane, "outside"),
        ("a plinth taller than its range", m_plinth, "plinth: height"),
        ("a lean-to with no gutter on its eave", m_gutter, "sheds into no gutter"),
        ("a border grown up into the roof", m_plants, "a plant scene"),
        ("a house over budget", m_cost, "over its budget"),
        ("a curvilinear roof of three facets", m_facets, "chord falls"),
        ("a lantern glazed with transparent glass", m_lantern, "not convex"),
        ("double-sided glass", m_double, "double-sided"),
    ]
    bad = 0
    for name, mut, want in cases:
        d = copy.deepcopy(data)
        mut(d)
        got = check(d, glb_check=False)
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> "
              f"{'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit

    # geometry breaks, made on a built house
    mats = K.materials(data)
    vs = _v(data, "k13.house.span")
    vl = _v(data, "k13.house.lean_to")

    def built(v=vs):
        return K.build_variant(v, data, with_board=False, index=data["variants"].index(v))

    geo = []
    h = built()
    g = h.prims["glass"]
    a, b, c = g.idx[0:3]
    g.idx[0:3] = [a, c, b]
    for j in (a, b, c):
        g.nrm[j] = K._mul(g.nrm[j], -1)
    geo.append(("a pane turned to face into the house", rule_envelope(h, data, mats), "faces into the house"))
    h = built()
    g = h.prims["glass"]
    g.idx = g.idx + g.idx[-3:]
    geo.append(("a pane drawn twice", rule_doubled(h, data), "coplanar and overlap"))
    h = built()
    m2 = copy.deepcopy(mats)
    m2["foliage"]["alpha"] = 0.5
    geo.append(("transparent foliage", rule_envelope(h, data, m2), "only glass may be"))
    h = built(vl)
    p = h.pipes[0]
    p["stations"][-1] = (p["stations"][-1][0], 0.6, p["stations"][-1][2])
    geo.append(("a pipe stopped short of grade", rule_rainwater(h, data), "does not reach the ground"))
    h = built()
    for m in h.members:
        if m["tier"] == "tertiary":
            m["standing"] = 0.06
            break
    geo.append(("a glazing bar standing prouder than a post", rule_hierarchy(h, data), "do not read in order"))
    h = built()
    pr = h.prims["primary"]
    pr.uv = [(u * 2, w * 2) for u, w in pr.uv]
    geo.append(("a face mapped at twice its size", rule_metric(h, data), "UV units per metre"))
    h = built()
    h.panes[0] = dict(h.panes[0], u_width=h.panes[0]["u_width"] * 0.8)
    geo.append(("bars that divide a run unevenly", rule_panes(h, data), "unevenly"))
    for name, got, want in geo:
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> "
              f"{'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit
    clean = check(data, glb_check=False)
    print(f"self-test | {'ok  ' if not clean else 'FAIL'} the committed kit passes ({len(clean)} failures)")
    bad += bool(clean)
    total = len(cases) + len(geo) + 1
    print(f"{'PASS' if not bad else 'FAIL'} — {total - bad} of {total} self-test cases refused as they should be")
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
        print(f"FAIL — {len(fails)} K13 conservatory kit rule(s) broken")
        return 1
    n = len(data["variants"])
    ts = [K.triangles(K.build_variant(v, data, with_board=False, index=i)) for i, v in enumerate(data["variants"])]
    print(f"ok   the K13 conservatory kit: {n} houses, each a three-tier frame over one convex single-sided glass "
          f"envelope on a plinth, every eave to a gutter and every pipe to grade, a restrained planting inside; "
          f"{min(ts)}-{max(ts)} triangles a house; the specimen GLB is the generator's bytes; "
          f"{len(scene_houses(data, []))} house(s) in the scene held to the same rules")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
