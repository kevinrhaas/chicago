#!/usr/bin/env python3
"""Hold the K07 entrance kit to its data, and every built entrance to being one (T-2303).

    python3 tools/check_entrance_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_entrance_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k07_entrances.json and the
generator (generators/archetypes/k07_entrances.py) builds every variant from them. This
rebuilds each variant in memory and measures the BUILT geometry, not the data's
promises. The K07 acceptance is "touches grade and floor correctly and clears public
walks; carriage opening has thickness and lintel, not a texture panel", and each clause
is a rule here:

  floor      the landing, deck or area floor is level with the threshold and meets it at
             the wall's face
  grade      a stoop's last riser, its cheeks, ends and skirt stand on grade; an area
             stair's last riser reaches grade
  risers     every rise between walking levels equal and inside the reconstruction
             rules' riser range, every going equal and inside their tread range
  closed     every tread, every riser and both ends of every step have a face, and every
             handrail socket sits on its cheek or coping
  walk       nothing an entrance builds reaches past its front yard onto the public walk
  carriage   a carriage opening's reveal runs the wall's whole thickness and its lintel
             bears past both jambs and is deep enough to span
  recess     every edge of the hole is closed by a reveal or the threshold, at the face
             and at the frame: a hole with sides, never a panel
  depth      frame behind the face, leaves behind the frame, glass behind the leaves'
             face, the backing a hall's depth behind the glass; the reveal no deeper than
             its wall and any vestibule it declares
  leaf       each door leaf stands clear of the threshold by no more than its gap and
             fills its frame from jamb to jamb
  enclosed   every glass light has the dark backing behind it (K06's rule)
  one layer  glass is the only transparent material and no two lights overlap
  doubled    no two coplanar faces overlap (K06's rule)
  costs      every entrance inside its triangle budget
  metric     TEXCOORD_0 is surface metres (K06's rule)
  specimen   the committed specimen GLB is the generator's bytes
"""

from __future__ import annotations

import copy
import itertools
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import k07_entrances as K  # noqa: E402
import check_window_kit as W  # noqa: E402

EPS = 1e-6
LEVEL_ROLES = ("landing", "tread", "deck", "step_timber")
FOOT_ROLES = ("riser", "step_timber", "cheek", "stair_end", "skirt")


def pts(o, roles):
    return [p for _, tri in W.faces(o, set(roles)) for p in tri]


def on_triangle(p, tri) -> bool:
    a, b, c = tri
    ab, ac, ap = W.K._sub(b, a), W.K._sub(c, a), W.K._sub(p, a)
    n = W.K._cross(ab, ac)
    ln = math.sqrt(W.K._dot(n, n))
    if ln < 1e-12 or abs(W.K._dot(n, ap)) / ln > 1e-5:
        return False
    d00, d01, d11 = W.K._dot(ab, ab), W.K._dot(ab, ac), W.K._dot(ac, ac)
    d20, d21 = W.K._dot(ap, ab), W.K._dot(ap, ac)
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return v >= -1e-6 and w >= -1e-6 and v + w <= 1 + 1e-6


def walked(o, roles):
    """The level, UPWARD-facing triangles of `roles`: what a foot stands on (a deck's
    soffit is level too, and faces down)."""
    for _, tri in W.faces(o, set(roles)):
        if max(p[1] for p in tri) - min(p[1] for p in tri) < EPS and \
                W.K._cross(W.K._sub(tri[1], tri[0]), W.K._sub(tri[2], tri[0]))[1] > 0:
            yield tri


def horizontal_ys(o, roles):
    return {round(tri[0][1] - o.O[1], 5) for tri in walked(o, roles)}


# -- the rules, each returning failure strings -------------------------------------------------

def rule_floor_and_grade(o, v, data):
    out = []
    kind = v["stair"]["kind"]
    if kind == "none":
        return out
    grade = o.meta["grade_m"]
    floor = [p for tri in walked(o, ("landing", "deck")) for p in tri]
    if not floor:
        return ["floor: no landing, deck or area floor"]
    ys = {round(p[1] - o.O[1], 6) for p in floor}
    if ys != {0.0}:
        out.append(f"floor: the landing stands at {sorted(ys)} m, not level with the threshold at 0")
    if not any(abs(p[2] - o.O[2]) < EPS for p in floor):
        out.append("floor: the landing does not meet the threshold at the wall's face")
    if kind == "area":
        top = max(p[1] for p in pts(o, ("riser",))) - o.O[1]
        if abs(top - grade) > EPS:
            out.append(f"grade: the area stair's last riser reaches {top:.4f} m, not grade at {grade} m")
    else:
        foot = min(p[1] for p in pts(o, FOOT_ROLES)) - o.O[1]
        if abs(foot - grade) > EPS:
            out.append(f"grade: the stair's foot stands at {foot:.4f} m, not on grade at {grade} m")
    return out


def rule_risers(o, v, data):
    kind = v["stair"]["kind"]
    if kind == "none":
        return []
    out = []
    sr = data["parts"]["stair"]
    levels = sorted(horizontal_ys(o, LEVEL_ROLES) | {round(o.meta["grade_m"], 5)})
    rises = [b - a for a, b in zip(levels, levels[1:])]
    if not rises:
        return ["risers: the stair has no rise"]
    lo, hi = sr["riser_range_m"]
    if max(rises) - min(rises) > 1e-3:
        out.append(f"risers: the rises are unequal ({[round(r, 4) for r in rises]} m)")
    bad = [round(r, 4) for r in rises if not lo - 1e-6 <= r <= hi + 1e-6]
    if bad:
        out.append(f"risers: a riser of {bad[0]} m is outside the riser range {sr['riser_range_m']}")
    goings = []
    tread_roles = ("tread",) if kind != "porch" else ("step_timber",)
    by_level = {}
    for tri in walked(o, tread_roles):
        by_level.setdefault(round(tri[0][1], 5), []).extend(tri)
    for y, ps in by_level.items():
        mid = [p for p in ps if abs(p[0] - o.O[0]) < 1e-6] or ps
        goings.append(max(p[2] for p in mid) - min(p[2] for p in mid))
    glo, ghi = sr["tread_range_m"]
    if goings and max(goings) - min(goings) > 1e-3:
        out.append(f"risers: the goings are unequal ({[round(g, 4) for g in goings]} m)")
    bad = [round(g, 4) for g in goings if not glo - 1e-6 <= g <= ghi + 1e-6]
    if bad:
        out.append(f"risers: a tread of {bad[0]} m is outside the tread range {sr['tread_range_m']}")
    return out


def rule_closed(o, v, data):
    tris = {}
    for role, tri in W.faces(o):
        tris.setdefault(role, []).append(tri)
    for p, roles, what in o.probes:
        if not any(on_triangle(p, t) for r in roles for t in tris.get(r, [])):
            return [f"closed: {what} has no face at {tuple(round(c - q, 3) for c, q in zip(p, o.O))} — "
                    f"the stair is open there"]
    return []


def rule_walk(o, v, data):
    lim = o.O[2] + v["front_yard_m"]
    far = max(p[2] for r, pr in o.prims.items() if r not in K.BOARD_ROLES for p in pr.pos)
    if far > lim + EPS:
        return [f"walk: the entrance reaches {far - o.O[2]:.3f} m out, past its {v['front_yard_m']} m front "
                f"yard onto the public walk"]
    return []


def rule_carriage(o, v, data):
    if not v.get("carriage"):
        return []
    out = []
    wall = o.meta["host_wall_m"]
    if o.meta["reveal_depth_m"] < wall - EPS:
        out.append(f"carriage: the reveal is {o.meta['reveal_depth_m']} m, not through the {wall} m wall — "
                   f"a carriage opening shows the wall's whole thickness")
    ln = data["parts"]["lintel"]
    hp = pts(o, ("head",))
    if not hp:
        return out + ["carriage: no lintel"]
    s0, s1 = o.meta["daylight_s"][0] - data["parts"]["frame"]["face_m"], o.meta["daylight_s"][1] + \
        data["parts"]["frame"]["face_m"]
    xa, xb = min(p[0] for p in hp) - o.O[0], max(p[0] for p in hp) - o.O[0]
    ya, yb = min(p[1] for p in hp) - o.O[1], max(p[1] for p in hp) - o.O[1]
    if s0 - xa < ln["bearing_min_m"] - EPS or xb - s1 < ln["bearing_min_m"] - EPS:
        out.append(f"carriage: the lintel bears {s0 - xa:.3f} m and {xb - s1:.3f} m past the jambs, under "
                   f"its {ln['bearing_min_m']} m bearing")
    if yb - ya < ln["height_min_m"] - EPS:
        out.append(f"carriage: the lintel is {yb - ya:.3f} m deep, under {ln['height_min_m']} m")
    if abs(ya - v["clear_height_m"]) > EPS:
        out.append(f"carriage: the lintel's soffit is at {ya:.3f} m, not on the opening's head")
    return out


def rule_recess(o, v, data):
    edges = set()
    for _, tri in W.faces(o, {"reveal", "threshold"}):
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges.add(frozenset((W.r6(a), W.r6(b))))
    rev = o.meta["reveal_depth_m"]
    hole = o.holes[0]
    for i, a in enumerate(hole):
        b = hole[(i + 1) % len(hole)]
        for d in (0.0, rev):
            if frozenset((W.r6(o.P(a[0], a[1], d)), W.r6(o.P(b[0], b[1], d)))) not in edges:
                return [f"recess: the hole's edge {a}->{b} at depth {d} m has no reveal or threshold face — "
                        f"an open slot, not a recess"]
    return []


def rule_depth(o, v, data):
    out = []
    rev = o.meta["reveal_depth_m"]
    wall = o.meta["host_wall_m"]
    allow = wall + v.get("vestibule_m", 0.0)
    if not 0 < rev <= allow + EPS:
        out.append(f"depth: reveal {rev} m is not inside (0, wall {wall} m + vestibule {v.get('vestibule_m', 0.0)} m]")
    stages = [("outer_face", o.O[2])]
    for name, roles in (("frame_face", ("frame",)), ("leaf_face", ("leaf",)),
                        ("glass", ("glass_outer", "glass_leaf"))):
        zs = [p[2] for p in pts(o, roles)]
        if zs:
            stages.append((name, max(zs)))
    for (na, za), (nb, zb) in zip(stages, stages[1:]):
        if not zb < za - EPS:
            out.append(f"depth: the {nb} (z {zb:.4f}) is not behind the {na} (z {za:.4f})")
    glass = [p[2] for p in pts(o, ("glass_outer", "glass_leaf"))]
    if glass:
        back = [p[2] for p in pts(o, ("backing",))]
        need = data["parts"]["backing"]["depth_m"]
        if not back:
            out.append("depth: glass with no backing — the hall behind the door is missing")
        elif min(glass) - min(back) < need - 1e-4:
            out.append(f"depth: the backing is {min(glass) - min(back):.3f} m behind the deepest glass, under "
                       f"backing.depth_m {need}")
    return out


def rule_leaf(o, v, data):
    out = []
    lf = data["parts"]["leaf"]
    lp = pts(o, ("leaf",))
    foot = min(p[1] for p in lp) - o.O[1]
    if foot <= EPS:
        out.append(f"leaf: a leaf's foot is at {foot:.4f} m — it binds on the threshold")
    elif foot > lf["max_gap_m"] + EPS:
        out.append(f"leaf: a leaf's foot is {foot:.4f} m above the threshold — it floats, over its "
                   f"{lf['max_gap_m']} m gap")
    xa, xb = min(p[0] for p in lp) - o.O[0], max(p[0] for p in lp) - o.O[0]
    da, db = o.meta["daylight_s"]
    if abs(xa - da) > EPS or abs(xb - db) > EPS:
        out.append(f"leaf: the leaves span {xa:.3f}..{xb:.3f} m, not the frame's {da:.3f}..{db:.3f} m")
    return out


def rule_one_layer(o, v, mats):
    out = []
    for role in o.prims:
        m = mats[K.ROLE_MATERIAL[role]]
        if m.get("alpha", 1.0) < 1.0 and K.ROLE_MATERIAL[role] != "glass":
            out.append(f"one layer: {role} ({K.ROLE_MATERIAL[role]}) is transparent; only glass may be")
    for a, b in itertools.combinations(o.panes, 2):
        if W.overlap2d(a["poly"], b["poly"]) > EPS:
            out.append(f"one layer: the {a['sash']} and {b['sash']} lights overlap in elevation")
            break
    return out


def rule_costs(o, v, data):
    cls = K.cost_class(v)
    cap = data["costs"]["max_triangles"][cls]
    t = K.triangles(o)
    return [] if t <= cap else [f"costs: {v['id']} is {t} triangles, over its {cls} budget of {cap}"]


def rule_data(data):
    out = []
    ids = [v["id"] for v in data["variants"]]
    if len(set(ids)) != len(ids):
        out.append("data: variant ids repeat")
    lo, hi = data["parts"]["raised_floor_range_m"]
    for v in data["variants"]:
        if not v["id"].startswith("k07.entrance."):
            out.append(f"data: {v['id']} is not a k07.entrance.* id")
        if v.get("confidence") not in ("attested", "inferred", "reconstructed"):
            out.append(f"data: {v['id']} has no confidence")
        elif v["confidence"] != "attested" and not v.get("note"):
            out.append(f"data: {v['id']} is {v['confidence']} with no note")
        for sid in v.get("sources", []):
            if not (ROOT / "data" / "sources" / f"{sid}.json").exists():
                out.append(f"data: {v['id']} cites {sid}, which data/sources/ does not hold")
        st = v["stair"]
        if st["kind"] in ("straight", "bowed", "porch") and not lo <= st["floor_m"] <= hi:
            out.append(f"data: {v['id']}'s floor of {st['floor_m']} m is outside the raised-floor range [{lo}, {hi}]")
        if v.get("carriage") and st["kind"] != "none":
            out.append(f"data: {v['id']} is a carriage opening with a stair; its floor is grade")
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
        rules = (rule_floor_and_grade(o, v, data) + rule_risers(o, v, data) + rule_closed(o, v, data)
                 + rule_walk(o, v, data) + rule_carriage(o, v, data) + rule_recess(o, v, data)
                 + rule_depth(o, v, data) + rule_leaf(o, v, data) + rule_one_layer(o, v, mats)
                 + rule_costs(o, v, data) + W.rule_doubled(o, data) + W.rule_metric(o, data))
        if o.panes:
            rules += W.rule_enclosed(o, data)
        fails += [f"{v['id']}: {f}" for f in rules]
    if glb_check:
        blob = K.to_glb(K.build_kit(data), data)
        out = ROOT / data["specimen"]
        if not out.exists() or out.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes — run "
                         f"python3 generators/archetypes/k07_entrances.py")
    return fails


# -- the self-test: each rule broken in memory, each refused for its own reason ------------------

def _v(data, vid):
    return next(v for v in data["variants"] if v["id"] == vid)


def self_test(data) -> int:
    STOOP, ARCH, BOW = "k07.entrance.panel_door_stoop", "k07.entrance.double_door_deep_arch", \
        "k07.entrance.glazed_door_bowed_stoop"
    CAR, PORCH, AREA = "k07.entrance.carriage_doors", "k07.entrance.porch", "k07.entrance.basement_area_stair"

    def m_riser(d):
        d["parts"]["stair"]["riser_target_m"] = 0.3

    def m_going(d):
        _v(d, STOOP)["stair"]["going_m"] = 0.42

    def m_walk(d):
        _v(d, STOOP)["front_yard_m"] = 2.0

    def m_bearing(d):
        _v(d, CAR)["lintel"]["bearing_m"] = 0.05

    def m_through(d):
        _v(d, CAR)["reveal_depth_m"] = 0.2

    def m_gap(d):
        d["parts"]["leaf"]["gap_m"] = 0.04

    def m_reveal(d):
        _v(d, STOOP)["reveal_depth_m"] = 0.5

    def m_vestibule(d):
        _v(d, ARCH).pop("vestibule_m")

    def m_floor(d):
        _v(d, PORCH)["stair"]["floor_m"] = 0.4

    def m_cost(d):
        d["costs"]["max_triangles"]["entrance"] = 150

    def m_note(d):
        _v(d, AREA).pop("note")

    cases = [
        ("risers solved too tall", m_riser, "outside the riser range"),
        ("a going too deep", m_going, "outside the tread range"),
        ("a stoop across the walk", m_walk, "onto the public walk"),
        ("a carriage lintel with no bearing", m_bearing, "under its 0.15 m bearing"),
        ("a carriage opening hung in the wall's face", m_through, "not through"),
        ("a leaf hung high off its threshold", m_gap, "it floats"),
        ("a reveal deeper than its wall", m_reveal, "depth: reveal"),
        ("a deep entrance that declares no vestibule", m_vestibule, "depth: reveal"),
        ("a porch floor under the raised-floor range", m_floor, "raised-floor range"),
        ("an entrance over budget", m_cost, "over its entrance budget"),
        ("a reconstructed variant with no note", m_note, "with no note"),
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

    # geometry breaks, made on a built entrance
    mats = K.materials(data)

    def built(vid):
        v = _v(data, vid)
        return v, K.build_variant(v, data, board=False)

    geo = []
    v, o = built(STOOP)
    rs = o.prims["riser"]
    rs.idx = rs.idx[6:]                                       # the top riser's two triangles
    geo.append(("a riser left out", rule_closed(o, v, data), "riser 1 has no face"))
    v, o = built(STOOP)
    o.prims.pop("cheek")
    geo.append(("a stoop with no cheeks and no ends", rule_closed(o, v, data), "the end of step"))
    v, o = built(BOW)
    o.prims["landing"].pos = [(p[0], p[1] + 0.05, p[2]) for p in o.prims["landing"].pos]
    geo.append(("a landing standing proud of the threshold", rule_floor_and_grade(o, v, data),
                "not level with the threshold"))
    v, o = built(PORCH)
    o.prims["skirt"].pos = [(p[0], p[1] + 0.1 if p[1] < -0.5 else p[1], p[2]) for p in o.prims["skirt"].pos]
    o.prims["step_timber"].pos = [(p[0], p[1] + 0.1 if p[1] < -0.84 else p[1], p[2])
                                  for p in o.prims["step_timber"].pos]
    geo.append(("a porch hanging above grade", rule_floor_and_grade(o, v, data), "not on grade"))
    v, o = built(ARCH)
    o.prims["reveal"].idx = o.prims["reveal"].idx[6:]
    geo.append(("a jamb missing from the reveal", rule_recess(o, v, data), "open slot"))
    v, o = built(BOW)
    bk = o.prims["backing"]
    bk.idx = bk.idx[:-3 * 4]
    geo.append(("a backing cap with a hole in it", W.rule_enclosed(o, data), "reaches the sky"))
    v, o = built(STOOP)
    tr = o.prims["tread"]
    tr.idx = tr.idx + tr.idx[:3]
    geo.append(("a tread drawn twice", W.rule_doubled(o, data), "coplanar and overlap"))
    v, o = built(CAR)
    m2 = copy.deepcopy(mats)
    m2["joinery"]["alpha"] = 0.6
    geo.append(("a see-through door leaf", rule_one_layer(o, v, m2), "only glass may be"))
    v, o = built(AREA)
    pr = o.prims["coping"]
    pr.uv = [(u * 2, w * 2) for u, w in pr.uv]
    geo.append(("a face mapped at twice its size", W.rule_metric(o, data), "UV units per metre"))
    for name, got, want in geo:
        hit = any(want in f for f in got)
        print(f"self-test | {'ok  ' if hit else 'FAIL'} {name} -> "
              f"{'refused: ' + next((f for f in got if want in f), '') if hit else 'NOT refused'}")
        bad += not hit
    clean = check(data, glb_check=False)
    print(f"self-test | {'ok  ' if not clean else 'FAIL'} the committed kit passes ({len(clean)} failures)")
    for f in clean:
        print(f"self-test |      {f}")
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
        print(f"FAIL — {len(fails)} K07 entrance kit rule(s) broken")
        return 1
    n = len(data["variants"])
    tris = [K.triangles(K.build_variant(v, data, board=False)) for v in data["variants"]]
    print(f"ok   the K07 entrance kit: {n} variants, each landing on its threshold and standing on grade with equal "
          f"risers, every step closed, the walk clear, a recess with a closed reveal, its leaves clear of the floor; "
          f"{min(tris)}-{max(tris)} triangles an entrance; the specimen GLB is the generator's bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
