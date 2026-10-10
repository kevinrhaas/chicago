#!/usr/bin/env python3
"""Hold the K16 timber kit to its data, and every built sample to being timber (T-2322).

    python3 tools/check_timber_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_timber_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k16_timber.json and the
generator (generators/archetypes/k16_timber.py) builds every sample from them. This
rebuilds each sample in memory and measures the BUILT geometry, not the data's promises.
The K16 acceptance is "board scale, cutout depth and coherent joinery ... do not apply
masonry thickness or stone texture to a timber facade", and each clause is a rule here:

  scale      clapboard and shingle exposure inside the reconstruction rules' range, the
             frame wall inside the K01 contract's frame range (never a masonry wall's)
  lapped     every course's butt measured one exposure above the last, its underside a
             shadow line, resting exactly on the course below — no gap, no board through
             a board
  stagger    no joint in one course within the stagger distance of a joint in the next;
             no clapboard longer than the board the data names
  batten     every board-and-batten gap covered by a batten bearing on both boards
  proud      trim stands proud of the cladding that stops against it
  pierced    every bargeboard piercing open (no board face across it) and cut through,
             its cut edges built the board's whole thickness
  end grain  every clapboard end at a joint is an end-grain face, both sides of it
  timber     every timber part bound to a painted, stained or end-grain material; the
             three classes all present and distinct; no masonry on a timber role
  wear       paint wear is a restrained per-board tone inside the data's range
  doubled    no two coplanar faces overlap (the back-to-back coincidence K01 refuses)
  costs      every sample inside its triangle budget
  metric     TEXCOORD_0 is surface metres (K01 scale_uv with an untextured tile of 1 m)
  data       ids, confidences and notes; restricted parts only where the data allows
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

from archetypes import k16_timber as K  # noqa: E402

EPS = 1e-6
TIMBER_CLASSES = ("painted", "stained", "end_grain", "unpainted")


def r6(p):
    return tuple(round(c, 6) for c in p)


def tris(sm, roles=None):
    for role, pr in sm.prims.items():
        if roles and role not in roles:
            continue
        for i in range(0, len(pr.idx), 3):
            yield role, [pr.pos[pr.idx[i + k]] for k in range(3)], pr.nrm[pr.idx[i]]


def frames(sm):
    return {f["name"]: K.Frame(f["name"], tuple(f["origin"]), tuple(f["u"]), tuple(f["n"])) for f in sm.meta["frames"]}


def in_frame(fr, rec, pts, nrm=None, front=False):
    """Do these world points belong to this cladding run (by its own s and z)?"""
    loc = [fr.local(p) for p in pts]
    s0, s1 = rec["s"]
    if not all(s0 - 1e-6 <= q[0] <= s1 + 1e-6 and -1e-6 <= q[2] <= 0.1 for q in loc):
        return None
    if front and _dot3(nrm, fr.n) < 0.5:
        return None
    return loc


def _dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def overlap2d(a, b) -> float:
    a = K.ccw(a)
    b = K.ccw(b)
    c = K.K06.clip(a, b)
    return abs(K.area2(c)) if len(c) >= 3 else 0.0


def k01_frame_range():
    c = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k01_contract.json").read_text())
    wall = next(f for f in c["families"] if f["family"] == "wall")
    return wall["parameters"]["thickness_m"]["ranges"]


# -- the rules, each returning failure strings -------------------------------------------------

def rule_scale(data):
    out = []
    cl = data["cladding"]["clapboard"]
    lo, hi = cl["range_exposure_m"]
    if not lo <= cl["exposure_m"] <= hi:
        out.append(f"scale: clapboard exposure {cl['exposure_m']} m is outside the reconstruction rules' range [{lo}, {hi}]")
    lo, hi = cl["range_board_length_m"]
    if not lo <= cl["board_length_m"] <= hi:
        out.append(f"scale: clapboard board length {cl['board_length_m']} m is outside [{lo}, {hi}]")
    rng = k01_frame_range()
    t = data["wall"]["thickness_m"]
    flo, fhi = rng["frame"]
    if not flo <= t <= fhi:
        out.append(f"scale: the wall is {t} m thick, outside the K01 frame range [{flo}, {fhi}]"
                   + (" — a masonry wall's thickness on a timber facade" if t >= rng["masonry"][0] else ""))
    go = data["gothic"]
    lo, hi = go["range_pitch_deg"]
    if not lo <= go["pitch_deg"] <= hi:
        out.append(f"scale: gable pitch {go['pitch_deg']} deg is outside the steep Gothic range [{lo}, {hi}]")
    return out


def rule_thickness(sm, data):
    """The wall's interior face, measured: as far behind the sheathing as the frame range allows."""
    zs = [p[2] for _, tri, n in tris(sm, {"interior"}) for p in tri if n[2] < -0.9]
    if not zs:
        return []
    T = -min(zs) + sm.O[2]
    flo, fhi = k01_frame_range()["frame"]
    if not flo - EPS <= T <= fhi + EPS:
        return [f"scale: the built wall stands {T:.3f} m thick, outside the K01 frame range [{flo}, {fhi}] — "
                f"a masonry wall's thickness on a timber facade"]
    return []


def rule_lapped(sm, data):
    out = []
    fr = frames(sm)
    for rec in sm.meta["frames"]:
        F = fr[rec["name"]]
        fam = data["cladding"][rec["family"]]
        face_role, butt_role = ("clapboard", "clapboard_butt") if rec["family"] == "clapboard" else ("shingle", "shingle_butt")
        butts = {}
        for _, tri, n in tris(sm, {butt_role}):
            loc = in_frame(F, rec, tri)
            if loc is None:
                continue
            lowest = min(q[1] for q in loc)
            zs = [q[2] for q in loc]
            butts.setdefault(round(lowest, 5), []).append((min(zs), max(zs), loc))
        if not butts:
            out.append(f"lapped: the {rec['family']} run on {rec['name']} has no butt faces — a slab, not courses")
            continue
        ys = sorted(butts)
        if rec["family"] == "clapboard":
            for a, b in zip(ys, ys[1:]):
                if abs((b - a) - fam["exposure_m"]) > 1e-4:
                    out.append(f"lapped: clapboard butts on {rec['name']} at y {a:.4f} and {b:.4f} are "
                               f"{b - a:.4f} m apart, not one exposure ({fam['exposure_m']} m)")
                    break
        for y in ys:
            lo = min(z0 for z0, _, _ in butts[y])
            hi = max(z1 for _, z1, _ in butts[y])
            if hi - lo < fam["min_shadow_m"] - 1e-6:
                out.append(f"lapped: the {rec['family']} butt at y {y:.4f} on {rec['name']} is {hi - lo:.4f} m deep, "
                           f"under min_shadow_m {fam['min_shadow_m']} — no shadow line")
                break
        # each course rests on the one below: the face under a butt line meets the butt's inner edge
        if rec["family"] == "clapboard":
            tops = {}                 # the top edge of every face, by its height
            for _, tri, n in tris(sm, {face_role}):
                loc = in_frame(F, rec, tri, n, front=True)
                if loc is None:
                    continue
                ytop = max(q[1] for q in loc)
                for q in loc:
                    if abs(q[1] - ytop) < 1e-7:
                        tops.setdefault(round(ytop, 5), set()).add(round(q[2], 5))
            for y in ys[1:]:
                below = tops.get(y)
                for z0, _, _ in butts[y]:
                    if not below or any(abs(z - z0) > 1e-4 for z in below):
                        out.append(f"lapped: the clapboard course with its butt at y {y:.4f} on {rec['name']} does not "
                                   f"rest on the course below (its underside at z {z0:.4f}, the face below at "
                                   f"{sorted(below) if below else 'nothing'})")
                        return out
    return out


def rule_stagger(sm, data):
    out = []
    by = {}
    for c in sm.meta["courses"]:
        by.setdefault((c["family"], c["frame"]), []).append(c)
    for (fam, frm), cs in by.items():
        need = data["cladding"][fam].get("min_stagger_m", 0.0)
        cs = sorted(cs, key=lambda c: c["y0"])
        for a, b in zip(cs, cs[1:]):
            for ja in a["joints"]:
                for jb in b["joints"]:
                    if abs(ja - jb) < need - 1e-6:
                        out.append(f"stagger: {fam} joints at s {ja:.3f} and {jb:.3f} on {frm} stand "
                                   f"{abs(ja - jb):.3f} m apart in neighbouring courses, under {need} m")
                        return out
        if fam == "clapboard":
            L = data["cladding"]["clapboard"]["board_length_m"]
            for c in cs:
                for p, q in c["pieces"]:
                    if q - p > L + 1e-6:
                        out.append(f"stagger: a clapboard on {frm} runs {q - p:.3f} m, longer than the {L} m board")
                        return out
    return out


def rule_batten(sm, data):
    bb = data["cladding"]["board_and_batten"]
    boards, battens = sm.meta["boards"], sm.meta["battens"]
    out = []
    for (a0, a1), (b0, b1) in zip(boards, boards[1:]):
        cover = [bt for bt in battens if bt[0] <= a1 - bb["min_bearing_m"] + 1e-9 and bt[1] >= b0 + bb["min_bearing_m"] - 1e-9]
        if not cover:
            out.append(f"batten: the gap between boards at s {a1:.3f}-{b0:.3f} has no batten bearing "
                       f"{bb['min_bearing_m']} m on both boards — an open joint")
            break
    return out


def rule_proud(sm, data):
    """Trim stands proud of the cladding it stops: measured in each cladding frame."""
    out = []
    need = 0.005
    fr = frames(sm)
    for rec in sm.meta["frames"]:
        F = fr[rec["name"]]
        role = "clapboard" if rec["family"] == "clapboard" else "shingle"
        clad = [q[2] for _, tri, n in tris(sm, {role}) for q in [F.local(p) for p in tri]
                if _dot3(n, F.n) > 0.5 and rec["s"][0] - 1e-6 <= q[0] <= rec["s"][1] + 1e-6]
        if not clad:
            continue
        top = max(clad)
        # what stops each family: clapboard runs into corner boards and casings and up
        # under a frieze or a belt; shingles stop against the rake boards and sit on the
        # belt's drip cap, which is proud of them by construction
        trims = (("corner_board", "casing", "apron", "frieze", "belt") if role == "clapboard" else ("rake_board",))
        for t in trims:
            zs = [F.local(p)[2] for _, tri, n in tris(sm, {t}) for p in tri if _dot3(n, F.n) > 0.9]
            zs = [z for z in zs if -1e-6 <= z <= 0.1]
            if zs and max(zs) < top + need - 1e-6:
                out.append(f"proud: the {t} face on {rec['name']} stands {max(zs):.4f} m out, not {need} m proud of "
                           f"the {role} it stops ({top:.4f} m) — the cladding would run over it")
    return out


def rule_pierced(sm, data):
    out = []
    edges = set()
    for _, tri, _ in tris(sm, {"cutout"}):
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges.add(frozenset((r6(a), r6(b))))
    board = [(tri, n) for _, tri, n in tris(sm, {"bargeboard"}) if abs(n[2]) > 0.9]
    for h in sm.meta["piercings"]:
        hole = [tuple(p) for p in h["hole"]]
        cx = sum(p[0] for p in hole) / len(hole)
        cy = sum(p[1] for p in hole) / len(hole)
        for tri, n in board:
            t2 = [((p[0] - sm.O[0]), p[1]) for p in tri]
            if abs(K.area2(t2)) > 1e-12 and _inside((cx, cy), t2):
                out.append(f"pierced: a bargeboard face covers the piercing at ({cx:.3f}, {cy:.3f}) — the hole is not open")
                return out
        for i, a in enumerate(hole):
            b = hole[(i + 1) % len(hole)]
            for z in (h["front_z"], h["back_z"]):
                pa, pb = sm.F.P(a[0], a[1], z), sm.F.P(b[0], b[1], z)
                if frozenset((r6(pa), r6(pb))) not in edges:
                    out.append(f"pierced: the piercing at ({cx:.3f}, {cy:.3f}) has no cut edge along {a}->{b} at z {z} "
                               f"— not cut through the board")
                    return out
    return out


def _inside(pt, poly) -> bool:
    poly = K.ccw(poly)
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0]) < -1e-9:
            return False
    return True


def rule_end_grain(sm, data):
    out = []
    fr = frames(sm)
    gap = data["cladding"]["clapboard"]["joint_gap_m"]
    ends = []
    for _, tri, n in tris(sm, {"end_grain"}):
        ends.append((tri, n))
    for c in sm.meta["courses"]:
        if c["family"] != "clapboard":
            continue
        F = fr[c["frame"]]
        for j in c["joints"]:
            for side in (-1, 1):
                s_e = j + side * gap / 2
                hit = False
                for tri, n in ends:
                    loc = [F.local(p) for p in tri]
                    if all(abs(q[0] - s_e) < 1e-5 for q in loc) and all(c["y0"] - 1e-6 <= q[1] <= c["y1"] + 1e-6 for q in loc):
                        hit = True
                        break
                if not hit:
                    out.append(f"end grain: the clapboard joint at s {j:.3f} (course at y {c['y0']:.3f}, {c['frame']}) "
                               f"has no end-grain face on its {'left' if side < 0 else 'right'} board")
                    return out
    return out


def rule_timber(sm, data, mats, role_material=None):
    rm = role_material or K.ROLE_MATERIAL
    out = []
    for role in sm.prims:
        if role in K.NOT_TIMBER:
            continue
        m = rm.get(role)
        cls = mats.get(m, {}).get("class")
        if cls not in TIMBER_CLASSES:
            out.append(f"timber: the {role} faces are bound to {m} ({cls}) — "
                       + ("masonry on a timber facade" if cls == "masonry" else "not a timber material"))
    return out


def rule_classes(data, mats):
    out = []
    cls = {}
    for name, m in mats.items():
        cls.setdefault(m["class"], []).append((name, tuple(m["color"])))
    for need in ("painted", "stained", "end_grain"):
        if need not in cls:
            out.append(f"timber: no {need} material — painted softwood, stained joinery and end grain are kept apart")
    cols = {}
    for c in ("painted", "stained", "end_grain"):
        for name, col in cls.get(c, []):
            cols.setdefault(col, set()).add(c)
    for col, cs in cols.items():
        if len(cs) > 1:
            out.append(f"timber: {sorted(cs)} share the colour {col} — the classes must read apart")
    return out


def rule_wear(sm, data):
    lo, hi = data["paint"]["wear"]["tone_range"]
    tones = set()
    for role in ("clapboard", "shingle", "board", "batten", "porch_floor"):
        if role in sm.prims:
            for t in sm.prims[role].tone:
                tones.add(t)
                if not lo - EPS <= t <= hi + EPS:
                    return [f"wear: a {role} carries a paint tone {t}, outside the restrained range [{lo}, {hi}]"]
    if len(tones) == 1:
        return ["wear: every board carries the same paint tone — no per-board wear"]
    return []


def rule_doubled(sm, data):
    buckets = {}
    for role, tri, _ in tris(sm):
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


def rule_costs(sm, data):
    use = sm.v["use"]
    budget = data["costs"]["max_triangles"].get(use)
    n = K.triangles(sm)
    if budget is None:
        return [f"costs: no triangle budget for use {use!r}"]
    if n > budget:
        return [f"costs: {n} triangles, over its {use} budget of {budget}"]
    return []


def rule_metric(sm, data):
    for role, pr in sm.prims.items():
        for i in range(0, len(pr.idx), 3):
            a, b = pr.idx[i], pr.idx[i + 1]
            dp = math.dist(pr.pos[a], pr.pos[b])
            du = math.dist(pr.uv[a], pr.uv[b])
            if dp > 1e-4 and abs(du / dp - 1) > 1e-3:
                return [f"metric: a {role} face maps {du / dp:.3f} UV units per metre, not 1"]
    return []


def rule_data(data):
    out = []
    ids = [v["id"] for v in data["samples"]]
    if len(set(ids)) != len(ids):
        out.append("data: sample ids repeat")
    for v in data["samples"]:
        if not v["id"].startswith("k16."):
            out.append(f"data: {v['id']} is not a k16.* id")
        if v.get("confidence") not in ("attested", "inferred", "reconstructed"):
            out.append(f"data: {v['id']} has no confidence")
        elif v["confidence"] != "attested" and not v.get("note"):
            out.append(f"data: {v['id']} is {v['confidence']} with no note")
        for sid in v.get("sources", []):
            if not (ROOT / "data" / "sources" / f"{sid}.json").exists():
                out.append(f"data: {v['id']} cites {sid}, which data/sources/ does not hold")
    for section in ("cladding", "trim"):
        for name, part in data[section].items():
            if isinstance(part, dict) and part.get("confidence") not in ("attested", "inferred", "reconstructed"):
                out.append(f"data: {section}.{name} has no confidence")
            elif isinstance(part, dict) and part.get("confidence") != "attested" and not part.get("note"):
                out.append(f"data: {section}.{name} is {part.get('confidence')} with no note")
    restr = {r["part"]: r for r in data["restrictions"]}
    for v in data["samples"]:
        uses = []
        if v["kind"] == "gable":
            uses = ["shingle", "pierced_bargeboard"]
        for part in uses:
            r = restr.get(part)
            allowed = r["allowed_uses"] if r else []
            ok = v["use"] in allowed or (part == "pierced_bargeboard" and "gothic" in allowed and "gothic" in v["id"])
            if not ok:
                out.append(f"data: {v['id']} uses {part} as {v['use']!r}, which breaks the restriction ({allowed})")
    return out


def check(data, glb_check=True, mats=None, role_material=None, with_houses=True):
    fails = list(rule_data(data)) + rule_scale(data)
    mats = mats or K.materials(data)
    fails += rule_classes(data, mats)
    for i, v in enumerate(data["samples"]):
        try:
            sm = K.build_variant(v, data, index=i)
        except Exception as e:  # a sample the generator cannot build is a failure, not a crash
            fails.append(f"build: {v['id']} does not build ({type(e).__name__}: {e})")
            continue
        for f in (rule_thickness(sm, data) + rule_lapped(sm, data) + rule_stagger(sm, data)
                  + (rule_batten(sm, data) if v["kind"] == "batten_wall" else [])
                  + rule_proud(sm, data) + rule_pierced(sm, data) + rule_end_grain(sm, data)
                  + rule_timber(sm, data, mats, role_material) + rule_wear(sm, data) + rule_doubled(sm, data)
                  + rule_costs(sm, data) + rule_metric(sm, data)):
            fails.append(f"{v['id']}: {f}")
    if with_houses:
        fails += check_houses(data, mats, role_material)
    if glb_check:
        blob = K.to_glb(K.build_kit(data), data)
        out = ROOT / data["specimen"]
        if not out.exists() or out.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes — run "
                         f"python3 generators/archetypes/k16_timber.py")
    return fails


_HOUSES = []


def houses():
    """[(record, phase)] for every k16_timber record in data/structures/ (T-2323), read once:
    a caller that changes one deep-copies it first."""
    if not _HOUSES:
        for f in sorted((ROOT / "data" / "structures").glob("*.json")):
            text = f.read_text()
            if '"k16_timber"' not in text:     # skip parsing the ~700 records that are not
                continue
            st = json.loads(text)
            if isinstance(st, dict) and st.get("archetype") == "k16_timber":
                _HOUSES.extend((st, ph) for ph in st.get("phases", []))
    return _HOUSES


def check_houses(data, mats=None, role_material=None, records=None):
    """T-2323: every house built from the kit is held to the kit's rules, part by part, as
    generators/k16_emit.py builds it — the gable, the wall and a porch half each measured
    the way their specimen samples are."""
    from archetypes import k16_timber_params as KP
    fails = []
    mats = mats or K.materials(data)
    for st, ph in (houses() if records is None else records):
        rid = f"{st['id']}/{ph['id']}"
        try:
            KP.from_phase(ph, st)
            parts = K.structure_parts(st, ph, data)
            K.structure_house(st, ph, data)
        except Exception as e:  # a record the builder cannot build is a failure, not a crash
            fails.append(f"house: {rid} does not build ({type(e).__name__}: {e})")
            continue
        for k in ("gable", "wing_wall", "porch_right"):
            sm = parts[k]
            for f in (rule_thickness(sm, data) + rule_lapped(sm, data) + rule_stagger(sm, data)
                      + rule_proud(sm, data) + rule_pierced(sm, data) + rule_end_grain(sm, data)
                      + rule_timber(sm, data, mats, role_material) + rule_wear(sm, data) + rule_doubled(sm, data)
                      + rule_costs(sm, data) + rule_metric(sm, data)):
                fails.append(f"house {rid} {k}: {f}")
    return fails


# -- the self-test: each rule broken, each refused for its own reason ---------------------------

def _v(data, vid):
    return next(v for v in data["samples"] if v["id"] == vid)


def self_test(data) -> int:
    def m_exposure(d):
        d["cladding"]["clapboard"]["exposure_m"] = 0.2

    def m_masonry(d):
        d["wall"]["thickness_m"] = 0.36

    def m_proud(d):
        d["trim"]["corner_board"]["thickness_m"] = 0.02

    def m_stagger(d):
        d["cladding"]["clapboard"]["stagger_step_m"] = 0.1

    def m_long(d):
        d["cladding"]["clapboard"]["board_length_m"] = 2.4

    def m_batten(d):
        d["cladding"]["board_and_batten"]["batten_width_m"] = 0.03

    def m_restrict(d):
        _v(d, "k16.gable.gothic_shingle")["use"] = "wall"

    def m_cost(d):
        d["costs"]["max_triangles"]["wall"] = 100

    def m_note(d):
        _v(d, "k16.porch.lattice_post").pop("note")

    def m_wear(d):
        d["paint"]["wear"]["tone_range"] = [1.0, 1.0]

    def m_butt(d):
        d["cladding"]["clapboard"]["butt_m"] = 0.004
        d["cladding"]["clapboard"]["tip_m"] = 0.004

    cases = [
        ("a clapboard laid 8 in to the weather", m_exposure, "outside the reconstruction rules' range"),
        ("a masonry wall's thickness under clapboard", m_masonry, "masonry wall's thickness"),
        ("corner boards thinner than the clapboard butts", m_proud, "proud"),
        ("joints a hand's width apart course over course", m_stagger, "in neighbouring courses"),
        ("battens narrower than their gap allows", m_batten, "open joint"),
        ("decorative shingles as a wall's walling", m_restrict, "breaks the restriction"),
        ("a wall over budget", m_cost, "over its wall budget"),
        ("a reconstructed sample with no note", m_note, "no note"),
        ("every board the same tone", m_wear, "same paint tone"),
        ("a clapboard with no butt to cast a shadow", m_butt, "no shadow line"),
    ]
    bad = 0
    for name, mut, want in cases:
        d = copy.deepcopy(data)
        mut(d)
        got = check(d, glb_check=False, with_houses=False)   # a kit rule, read on the samples
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> {'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit

    # geometry breaks, made on a built sample
    def built(vid):
        i = next(k for k, v in enumerate(data["samples"]) if v["id"] == vid)
        return K.build_variant(data["samples"][i], data, index=i)

    geo = []
    sm = built("k16.gable.gothic_shingle")
    pr = sm.prims["cutout"]
    pr.idx = pr.idx[6:]
    geo.append(("a piercing whose cut edge is missing", rule_pierced(sm, data), "not cut through"))
    sm = built("k16.gable.gothic_shingle")
    h = sm.meta["piercings"][0]
    sm.face("bargeboard", [sm.F.P(x, y, h["front_z"]) for x, y in h["hole"]], (0, 0, 1))
    geo.append(("a piercing covered by a board face", rule_pierced(sm, data), "not open"))
    sm = built("k16.wall.clapboard_corner")
    pr = sm.prims["clapboard_butt"]
    i0 = pr.idx[30]
    for k in range(4):
        x, y, z = pr.pos[i0 + k]
        pr.pos[i0 + k] = (x, y, z + 0.006)
    geo.append(("a course standing off the course below", rule_lapped(sm, data), "does not rest"))
    # T-2323: the builder now puts back a joint min_piece dropped, so no data change makes it
    # lay an over-long board; the break is a wall of 12 ft boards judged by 2.4 m ones
    sm = built("k16.wall.clapboard_corner")
    d = copy.deepcopy(data)
    m_long(d)
    geo.append(("a clapboard longer than its board", rule_stagger(sm, d), "longer than the 2.4 m board"))
    sm = built("k16.wall.clapboard_corner")
    pr = sm.prims["end_grain"]
    pr.idx = []
    geo.append(("joints with no end-grain faces", rule_end_grain(sm, data), "no end-grain face"))
    sm = built("k16.wall.board_and_batten")
    pr = sm.prims["batten"]
    pr.idx = pr.idx + pr.idx[:3]
    geo.append(("a batten face drawn twice", rule_doubled(sm, data), "coplanar and overlap"))
    sm = built("k16.porch.lattice_post")
    pr = sm.prims["lattice"]
    pr.uv = [(u * 2, w * 2) for u, w in pr.uv]
    geo.append(("a face mapped at twice its size", rule_metric(sm, data), "UV units per metre"))
    sm = built("k16.wall.clapboard_corner")
    rm = dict(K.ROLE_MATERIAL, clapboard="foundation")
    geo.append(("clapboard bound to the masonry material", rule_timber(sm, data, K.materials(data), rm), "masonry"))
    mats = K.materials(data)
    mats["stained"] = dict(mats["stained"], color=mats["body"]["color"])
    geo.append(("stained joinery painted the body colour", rule_classes(data, mats), "must read apart"))
    # T-2323: a house front, broken in its record and in its built parts
    if houses():
        st, ph = copy.deepcopy(houses()[0])
        ph["form"]["wing_wall"]["value"]["kind"] = "batten_wall"
        geo.append(("a house whose wall beside the gable is not a clapboard wall",
                    check_houses(data, records=[(st, ph)]), "must be a kit 'clapboard_wall' variant"))
        st, ph = copy.deepcopy(houses()[0])
        ph["form"]["gable"]["value"]["width_m"] = 7.6
        geo.append(("a house gable so wide its shingles break the gable budget",
                    rule_costs(K.structure_parts(st, ph, data)["gable"], data), "over its gable budget"))
    for name, got, want in geo:
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> {'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit
    clean = check(data, glb_check=False)
    print(f"self-test | {'ok  ' if not clean else 'FAIL'} the committed kit passes ({len(clean)} failures)")
    for f in clean:
        print(f"self-test |      {f}")
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
        print(f"FAIL — {len(fails)} K16 timber kit rule(s) broken")
        return 1
    kit = [K.build_variant(v, data, index=i) for i, v in enumerate(data["samples"])]
    tri = [K.triangles(s) for s in kit]
    courses = sum(1 for s in kit for c in s.meta["courses"])
    holes = sum(len(s.meta["piercings"]) for s in kit)
    hs = houses()
    print(f"ok   {len(hs)} house front(s) built from the kit hold to the same rules, part by part (T-2323)")
    print(f"ok   the K16 timber kit: {len(kit)} samples, {courses} lapped courses each resting on the last with a "
          f"shadow line, joints staggered, battens over every joint, trim proud of its cladding, {holes} piercings "
          f"cut through, a {data['wall']['thickness_m']} m frame wall, no doubled face; {min(tri)}-{max(tri)} "
          f"triangles a sample; the specimen GLB is the generator's bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
