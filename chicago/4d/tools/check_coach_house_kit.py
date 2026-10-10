#!/usr/bin/env python3
"""Hold the K12 coach-house kit to its data, and every built piece to standing on what carries it (T-2320).

    python3 tools/check_coach_house_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_coach_house_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k12_coach_house.json and the
generator (generators/archetypes/k12_coach_house.py) builds every variant from them. This
rebuilds each variant in memory and measures the BUILT geometry, not the data's promises.
The K12 acceptance asks for one complete alley asset with every elevation, a believable
workyard connection, and the ventilator only where a source shows one; each clause is a
rule here:

  data       every part and variant states a confidence and a note; the three
             restrictions stated (no 1911 use labels, no ventilator without evidence, no
             generic in place of a documented coach house)
  seated     every open edge of a piece lies on another surface of the variant: a wall's
             foot on the ground, its end on the wall it meets, a gable's rake on the roof,
             a leaf's edge on its reveal, the wing's ends on the coach house and the house
             (tools/check_trim_kit.py's rule, shared with K09 and K10)
  rooted     every closed piece (a hinge strap, the hoist beam and hook, the coping, a ramp
             cleat) passes through what carries it
  doubled    no two coplanar faces overlap
  shell      every elevation is closed: across the alley wall, the yard wall, the gable and
             the party wall, every point of the face above grade that is not an opening is
             wall
  openings   every opening is cut THROUGH its wall (nothing of the wall across it), clear
             of its neighbours and of the wall's ends, and the carriage bay inside the
             data's clear-width range
  grade      the ramp no steeper than the data allows and meeting grade at its head and the
             basement floor at its foot; the stair's risers and goings inside the data's
             limits, its risers adding up to its landing, its stringers on the ground; the
             lean-to's and the wing's walls on the ground
  ventilator no ventilator unless the data carries a source for one (the generator refuses)
  costs      every variant inside its triangle budget
  specimen   the committed specimen GLB is the generator's bytes
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import k12_coach_house as K  # noqa: E402
from check_trim_kit import rule_doubled, rule_rooted, rule_seated, seg_hits, tris  # noqa: E402

CONF = ("attested", "inferred", "reconstructed")
SHELL = ("alley", "yard", "gable", "party")


def shell_of(var):
    """The elevations a variant closes: an east party wall stands where the gable would (T-2321)."""
    return SHELL if var.v.get("east_end", "gable") == "gable" else ("alley", "yard", "party", "party_east")


def rule_data(data):
    out = []
    for name, part in data["parts"].items():
        if name.startswith("_"):
            continue
        if part.get("confidence") not in CONF or not part.get("note"):
            out.append(f"part {name}: no confidence and note")
    for v in data["variants"]:
        if v.get("confidence") not in CONF or not v.get("note"):
            out.append(f"{v['id']}: no confidence and note")
        if v.get("class") not in data["costs"]["max_triangles"]:
            out.append(f"{v['id']}: class {v.get('class')!r} has no triangle budget")
    rules = {r["rule"] for r in data["restrictions"]}
    for need in ("no_1911_use_labels", "ventilator_needs_evidence", "never_replaces_landmark"):
        if need not in rules:
            out.append(f"restriction {need} is not stated")
    return out


def inside(pt, poly):
    x, y = pt
    hit = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def edge_dist(pt, poly):
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2))
        best = min(best, math.hypot(pt[0] - a[0] - t * dx, pt[1] - a[1] - t * dy))
    return best


def through(var, w, s, y):
    """Does the segment straight through wall `w` at (s, y) cross any triangle of its piece?"""
    fr, th = w["frame"], w["thick"]
    a, b = fr.P((s, y, 0.02)), fr.P((s, y, -th - 0.02))
    piece = next((p for p in var.pieces if p.name == w["piece"]), None)
    if piece is None:
        return False
    # a wall is a few hundred large triangles: test them all rather than grid them, whose
    # 0.1 m cells a whole elevation's face would fill by the ten thousand
    cache = var.__dict__.setdefault("_wall_tris", {})
    if piece.name not in cache or cache[piece.name][0] is not piece:
        cache[piece.name] = (piece, list(tris(piece)))
    return any(seg_hits(a, b, t) for t in cache[piece.name][1])


def rule_shell(var, step=0.5):
    out = []
    for key in shell_of(var):
        w = var.walls.get(key)
        if not w:
            out.append(f"{key}: no wall")
            continue
        holes = [K.Variant.outline_of(var, op) for op in var.v["openings"] if op["wall"] == key]
        poly = w["outline"]
        s_lo, s_hi = min(p[0] for p in poly), max(p[0] for p in poly)
        y_hi = max(p[1] for p in poly)
        missing = 0
        s = s_lo + step / 2
        while s < s_hi:
            y = 0.25
            while y < y_hi:
                pt = (s, y)
                if (inside(pt, poly) and edge_dist(pt, poly) > 0.05
                        and not any(inside(pt, h) or edge_dist(pt, h) < 0.05 for h in holes)):
                    if not through(var, w, s, y):
                        missing += 1
                y += step
            s += step
        if missing:
            out.append(f"{key}: {missing} point(s) of the elevation above grade are open (no wall)")
    return out


def rule_openings(var, data):
    out = []
    by_wall: dict = {}
    for op in var.v["openings"]:
        w = var.walls.get(op["wall"])
        if not w:
            out.append(f"{op['id']}: on a wall the variant does not build ({op['wall']})")
            continue
        cs, cy = (op["s0"] + op["s1"]) / 2, (op["sill"] + op["head"]) / 2
        if through(var, w, cs, cy):
            out.append(f"{op['id']}: the wall runs across it (an opening painted on, not cut through)")
        poly = w["outline"]
        ends = [p[0] for p in poly if p[1] <= op["sill"] + 1e-9] or [p[0] for p in poly]
        if op["s0"] < min(ends) + 0.25 - 1e-9 or op["s1"] > max(ends) - 0.25 + 1e-9:
            out.append(f"{op['id']}: within 0.25 m of its wall's end")
        by_wall.setdefault(op["wall"], []).append(op)
    for key, ops in by_wall.items():
        for i, a in enumerate(ops):
            for b in ops[i + 1:]:
                if (a["s0"] < b["s1"] + 0.1 and b["s0"] < a["s1"] + 0.1
                        and a["sill"] < b["head"] + 0.1 and b["sill"] < a["head"] + 0.1):
                    out.append(f"{a['id']} and {b['id']}: closer than 0.1 m on the {key} wall")
    lo, hi = data["parts"]["carriage"]["range_clear_m"]
    C = var.meta.get("carriage")
    if not C:
        out.append("no carriage bay")
    elif not lo - 1e-9 <= C["clear_m"] <= hi + 1e-9:
        out.append(f"carriage bay {C['clear_m']:.2f} m clear, outside {lo}-{hi} m")
    return out


def rule_grade(var, data):
    out = []
    RP, SP = data["parts"]["ramp"], data["parts"]["stair"]
    by = {p.name: p for p in var.pieces}
    ys = lambda name: [q[1] for q in by[name].mesh.pos] if name in by else []
    v = var.v
    # T-2321: the fittings are the variant's to ask for, so each is held only where it is
    # asked for — and a fitting asked for and not built is still a failure
    feet = []
    if v.get("ramp"):
        out += grade_ramp(var, RP, ys, data)
    if v.get("stair"):
        out += grade_stair(var, SP, ys)
        feet += ["stringer wall", "stringer outer", "newel", "landing post 1", "landing post 2"]
    if v.get("lean_to"):
        feet += ["lean-to front wall", "lean-to east wall", "lean-to west wall"]
    if v.get("wing"):
        feet += ["wing east wall", "wing west wall"]
    if v.get("workyard"):
        out += grade_workyard(var, ys)
    for name in feet:
        y = ys(name)
        if not y:
            out.append(f"{name}: not built")
        elif abs(min(y)) > 1e-6:
            out.append(f"{name}: its foot is at {min(y):.3f} m, not on the ground")
    return out


def grade_ramp(var, RP, ys, data):
    out = []
    r = var.meta.get("ramp")
    if not r:
        return ["ramp: asked for and not built"]
    if r["grade"] > RP["max_grade"] + 1e-9:
        out.append(f"ramp at 1 in {1 / r['grade']:.1f}, steeper than 1 in {1 / RP['max_grade']:.1f}")
    ry = ys("ramp")
    B = data["parts"]["basement"]["depth_m"]
    if not ry or abs(max(ry)) > 1e-6:
        out.append("the ramp's head is not at grade")
    if not ry or abs(min(ry) + B) > 1e-6:
        out.append(f"the ramp's foot is not on the basement floor ({-B} m)")
    return out


def grade_workyard(var, ys):
    """The workyard's paving lies on the ground, stays under the yard door's sill, and its
    walk reaches the house's rear wall line from the apron (T-2321)."""
    out = []
    wy = var.meta.get("workyard")
    if not wy:
        return ["workyard: asked for and not built"]
    for name in ("workyard apron", "workyard walk"):
        y = ys(name)
        if not y:
            out.append(f"{name}: not built")
        elif abs(min(y)) > 1e-6:
            out.append(f"{name}: its foot is at {min(y):.3f} m, not on the ground")
    by = {p.name: p for p in var.pieces}
    if "workyard walk" in by:
        zs = [q[2] for q in by["workyard walk"].mesh.pos]
        if abs(min(zs) - wy["z_house"]) > 1e-6:
            out.append(f"the workyard walk stops {min(zs) - wy['z_house']:.3f} m short of the house's rear wall line")
        if abs(max(zs) - wy["apron"][2]) > 1e-6:
            out.append("the workyard walk does not meet the apron")
    for op in var.v["openings"]:
        if op["wall"] == "yard" and op["sill"] < 0.5 and op["sill"] < wy["paving_m"] - 1e-9:
            out.append(f"{op['id']}: its sill ({op['sill']} m) is under the paving ({wy['paving_m']} m)")
    return out


def grade_stair(var, SP, ys):
    out = []
    s = var.meta.get("stair")
    if not s:
        return ["stair: asked for and not built"]
    if s["rise"] > SP["rise_max_m"] + 1e-9:
        out.append(f"stair risers {s['rise']} m, over {SP['rise_max_m']} m")
    if s["going"] < SP["going_min_m"] - 1e-9:
        out.append(f"stair goings {s['going']} m, under {SP['going_min_m']} m")
    if abs(s["risers"] * s["rise"] - s["landing_y"]) > 1e-6:
        out.append("the stair's risers do not add up to its landing")
    door = next((o for o in var.v["openings"] if o["id"] == "loft_door"), None)
    if door and abs(door["sill"] - s["landing_y"]) > 1e-6:
        out.append(f"the landing ({s['landing_y']:.2f} m) is not at the loft door's sill ({door['sill']} m)")
    return out


def rule_costs(var, v, data):
    cap = data["costs"]["max_triangles"].get(v["class"], 0)
    n = K.triangles(var)
    return [f"{n} triangles over the {v['class']} budget of {cap}"] if n > cap else []


def build_all(data):
    built, fails = [], []
    for i, v in enumerate(data["variants"]):
        try:
            built.append(K.build_variant(v, data, index=i))
        except K.VentilatorRefused as e:
            fails.append(f"{v['id']} ventilator: {e}")
    return built, fails


def build_structures(data):
    """Every coach house a k12_coach_house structure record puts in a scene, built in the
    kit's frame, so a named lot is held to the kit's rules (T-2321)."""
    built, fails = [], []
    for p in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = json.loads(p.read_text())
        if not isinstance(st, dict) or st.get("archetype") != "k12_coach_house":
            continue
        for ph in st.get("phases", []):
            try:
                built.append(K.structure_variant(st, ph, data))
            except (K.VentilatorRefused, ValueError, KeyError) as e:
                fails.append(f"{st['id']} ventilator: {e}" if isinstance(e, K.VentilatorRefused)
                             else f"{st['id']}: {e}")
    return built, fails


def check(data, built=None, glb=True):
    fails = [f"data: {m}" for m in rule_data(data)]
    if built is None:
        built, vf = build_all(data)
        sb, sf = build_structures(data)
        built, fails = built + sb, fails + vf + sf
    for var in built:
        v = var.v
        for name, msgs in (("seated", rule_seated(var)), ("rooted", rule_rooted(var)),
                           ("doubled", rule_doubled(var)), ("shell", rule_shell(var)),
                           ("openings", rule_openings(var, data)), ("grade", rule_grade(var, data)),
                           ("costs", rule_costs(var, v, data))):
            fails += [f"{v['id']} {name}: {m}" for m in msgs]
    if glb and not any(" ventilator:" in f for f in fails):
        blob = K.to_glb(K.build_kit(data), data)
        spec = ROOT / data["specimen"]
        if not spec.exists() or spec.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes "
                         f"(run python3 generators/archetypes/k12_coach_house.py)")
    return fails, built


def self_test(data) -> int:
    def piece(built, name):
        return next(p for p in built[0].pieces if p.name == name)

    def d_note(d):
        d["parts"]["hoist"]["note"] = ""

    def d_restrict(d):
        d["restrictions"] = [r for r in d["restrictions"] if r["rule"] != "no_1911_use_labels"]

    def d_budget(d):
        d["costs"]["max_triangles"]["coach_house"] = 1000

    def d_vent(d):
        d["variants"][0]["ventilator"] = True

    def d_steep(d):
        d["variants"][0]["ramp"]["grade"] = 0.4

    def d_riser(d):
        d["variants"][0]["stair"]["rise_m"] = 0.25
        d["variants"][0]["stair"]["risers"] = 15

    def d_narrow(d):
        op = next(o for o in d["variants"][0]["openings"] if o["id"] == "carriage")
        op["s1"] = op["s0"] + 2.2

    def d_crowd(d):
        op = next(o for o in d["variants"][0]["openings"] if o["id"] == "man_door")
        op["s0"] -= 0.75
        op["s1"] -= 0.75

    def g_gap(built):       # the wing's east wall pulled 5 mm off the coach house
        p = piece(built, "wing east wall")
        p.mesh.pos = [(x, y, z - 0.005) for x, y, z in p.mesh.pos]

    def g_beam(built):      # the hoist beam slid out of its wall
        for name in ("loft_hatch hoist beam", "loft_hatch hoist hook"):
            p = piece(built, name)
            p.mesh.pos = [(x, y, z + 0.4) for x, y, z in p.mesh.pos]

    def g_doubled(built):   # a sill given a back face on the wall
        p = piece(built, "stable_sash sill")
        ys = sorted({round(q[1], 6) for q in p.mesh.pos})
        xs = sorted({round(q[0], 6) for q in p.mesh.pos})
        p.mesh.poly([(xs[0], ys[0], 0.0), (xs[-1], ys[0], 0.0), (xs[-1], ys[-1], 0.0), (xs[0], ys[-1], 0.0)],
                    (0.0, 0.0, -1.0))

    def g_open(built):      # the yard wall left out
        built[0].pieces = [p for p in built[0].pieces if p.name != "yard wall"]

    def g_painted(built):   # the carriage bay drawn on the alley wall instead of cut through it
        var = built[0]
        w = var.walls["alley"]
        p = piece(built, "alley wall")
        op = next(o for o in var.v["openings"] if o["id"] == "carriage")
        a = len(p.mesh.pos)
        p.mesh.poly([(op["s0"], 0.0, -0.1), (op["s1"], 0.0, -0.1), (op["s1"], op["head"], -0.1),
                     (op["s0"], op["head"], -0.1)], (0.0, 0.0, 1.0))
        w["frame"].apply(p.mesh, a)

    # T-2321: a named lot's variant — two party walls, no stair or ramp, a workyard
    def named(d):
        st = json.loads((ROOT / "data" / "structures" / "wheeler_house_1812_prairie_coach_house.json").read_text())
        d["variants"][0] = copy.deepcopy(st["phases"][0]["form"]["coach_house"]["value"])
        return d["variants"][0]

    def d_named_sill(d):    # the yard door's sill sunk under the paving
        next(o for o in named(d)["openings"] if o["id"] == "yard_door")["sill"] = 0.02

    def g_named_walk(built):    # the walk stopping 0.3 m short of the house's rear wall line
        p = piece(built, "workyard walk")
        z0 = min(q[2] for q in p.mesh.pos)
        p.mesh.pos = [(x, y, z + 0.3 if abs(z - z0) < 1e-9 else z) for x, y, z in p.mesh.pos]

    def g_named_open(built):    # the east party wall left out
        built[0].pieces = [p for p in built[0].pieces if p.name != "east party wall"]

    def g_lift(built):      # the stair's stringers stood 50 mm above the ground
        for name in ("stringer wall", "stringer outer"):
            p = piece(built, name)
            p.mesh.pos = [(x, y + 0.05, z) for x, y, z in p.mesh.pos]

    cases = [("a part with no note", d_note, None, "data"),
             ("the 1911-use restriction dropped", d_restrict, None, "data"),
             ("a coach-house budget of 1000 triangles", d_budget, None, "costs"),
             ("a ventilator with no source", d_vent, None, "ventilator"),
             ("a ramp at 1 in 2.5", d_steep, None, "grade"),
             ("0.25 m stair risers", d_riser, None, "grade"),
             ("a 2.2 m carriage bay", d_narrow, None, "openings"),
             ("the man door crowding the carriage bay", d_crowd, None, "openings"),
             ("the wing 5 mm off the coach house", None, g_gap, "seated"),
             ("the hoist beam out of its wall", None, g_beam, "rooted"),
             ("a sill with a back face on the wall", None, g_doubled, "doubled"),
             ("the yard elevation left open", None, g_open, "shell"),
             ("a carriage bay painted on, not cut through", None, g_painted, "openings"),
             ("the stair standing off the ground", None, g_lift, "grade"),
             ("1812: the yard door's sill under the paving", d_named_sill, None, "grade"),
             ("1812: the workyard walk short of the house", named, g_named_walk, "grade"),
             ("1812: the east party wall left out", named, g_named_open, "shell")]
    bad = 0
    for label, dmut, gmut, rule in cases:
        d = copy.deepcopy(data)
        if dmut:
            dmut(d)
        built, vf = build_all(d)
        if gmut:
            gmut(built)
        fails, _ = check(d, built, glb=False)
        fails = vf + fails
        hit = [f for f in fails if f.split(":")[0].split(" ")[-1] == rule or f.startswith(rule)]
        if hit:
            print(f"   self-test | ok   {label}: refused ({hit[0][:110]})")
        else:
            bad += 1
            print(f"   self-test | FAIL {label}: NOT refused by {rule} ({len(fails)} other failure(s))")
    print(f"   self-test | {bad} failure(s)")
    return 1 if bad else 0


def main(argv) -> int:
    data = K.load()
    if "--self-test" in argv:
        return self_test(data)
    if "--check" not in argv:
        print(__doc__.strip().splitlines()[2])
        print(__doc__.strip().splitlines()[3])
        return 2
    fails, built = check(data)
    for f in fails:
        print(f"FAIL {f}")
    if fails:
        return 1
    n = sum(len(b.pieces) for b in built)
    print(f"ok   K12 coach-house kit: {len(built)} variant(s), {n} pieces seated or rooted, no doubled face, every "
          f"elevation closed, every opening cut through, ramp and stair at grade, no ventilator, budgets and the "
          f"specimen hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
