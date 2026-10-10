#!/usr/bin/env python3
"""Hold the K11 ironwork kit to its data, and every built member to the one that carries it (T-2318).

    python3 tools/check_ironwork_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_ironwork_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k11_ironwork.json and the
generator (generators/archetypes/k11_ironwork.py) builds every variant from them. This
rebuilds each variant in memory and measures the BUILT geometry, not the data's
promises. The K11 acceptance asks that the silhouette read at walking distance without
wire shimmer and that no fence cross an entrance; each clause is a rule here:

  data       every part and variant states a confidence and a note; the picket pitch's
             clear gap inside its range; both restrictions stated (no generic pattern in
             place of a documented one; no run across an entrance)
  seated     no piece has an open edge in the air (tools/check_trim_kit.py's rule)
  rooted     every closed piece passes through its host's surface: a picket through its
             rail, a rail into its post, a post into its curb, a curb, pier or wall past
             grade, a spear, finial, urn, cap or coping into what carries it (K09's rule)
  doubled    no two coplanar faces overlap (K09's rule)
  shimmer    no iron member thinner, across any of its own faces, than the floor the
             data derives from the walking distance, the lens and the viewport
  rhythm     the pickets, bars and balusters of every panel evenly spaced, their clear
             gap inside the data's range
  gate       at least two hinges; the opening between the piers at least the data's
             clear width; no piece but the gate's own inside that opening; the leaf on
             the yard side of the line as drawn, and clear of its hinge pier through
             its whole swing
  wall       piers no further apart than the data allows; the coping overhanging both
             faces by at least its drip
  canopy     the glass falling away from the wall by at least the data's pitch; rafters
             no further apart than the data allows
  costs      every variant inside its triangle budget
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

from archetypes import k11_ironwork as K  # noqa: E402
from check_trim_kit import cross, dot, rule_doubled, rule_rooted, rule_seated, sub, tris  # noqa: E402

CONF = ("attested", "inferred", "reconstructed")
GATE_TOL = 1e-3


def shimmer_floor(data) -> float:
    S = data["parts"]["shimmer"]
    px_per_m = S["viewport_px"] / (2 * S["walking_distance_m"] * math.tan(math.radians(S["fov_deg"] / 2)))
    return S["min_px"] / px_per_m


def rule_data(data):
    out = []
    for name, part in data["parts"].items():
        if name.startswith("_"):
            continue
        if part.get("confidence") not in CONF or not part.get("note"):
            out.append(f"part {name}: no confidence and note")
    K_ = data["parts"]["picket"]
    lo, hi = K_["clear_range_m"]
    if not lo <= K_["pitch_m"] - K_["section_m"] <= hi:
        out.append(f"picket pitch {K_['pitch_m']} m leaves {K_['pitch_m'] - K_['section_m']:.3f} m clear, "
                   f"outside {lo}-{hi} m")
    for v in data["variants"]:
        if v.get("confidence") not in CONF or not v.get("note"):
            out.append(f"{v['id']}: no confidence and note")
        if v.get("class") not in data["costs"]["max_triangles"]:
            out.append(f"{v['id']}: class {v.get('class')!r} has no triangle budget")
    rules = {r["rule"] for r in data["restrictions"]}
    for need in ("never_replaces_landmark", "never_crosses_entrance"):
        if need not in rules:
            out.append(f"restriction {need} is not stated")
    return out


def thinnest(piece) -> float:
    """The piece's least extent along any of its own face normals: a bar's section."""
    pts = piece.mesh.pos
    best = math.inf
    seen = set()
    for t in tris(piece):
        n = cross(sub(t[1], t[0]), sub(t[2], t[0]))
        nn = math.sqrt(dot(n, n))
        if nn < 1e-12:
            continue
        n = tuple(round(c / nn, 4) for c in n)
        if n in seen or tuple(-c for c in n) in seen:
            continue
        seen.add(n)
        d = [dot(q, n) for q in pts]
        best = min(best, max(d) - min(d))
    return best


def rule_shimmer(var, data):
    floor = shimmer_floor(data)
    out = []
    for p in var.pieces:
        if p.role != "iron" or not p.mesh.idx:
            continue
        w = thinnest(p)
        if w < floor - 1e-6:
            out.append(f"{p.name}: {w * 1000:.1f} mm thick, under the {floor * 1000:.1f} mm walking-distance floor "
                       f"(it would shimmer)")
    return out[:3]


def rule_rhythm(var, data):
    """Centres measured on the built members, by panel."""
    lo, hi = data["parts"]["picket"]["clear_range_m"]
    out = []
    for group, g in var.meta.get("rhythm", {}).items():
        ax = g["axis"]
        mine = [p for p in var.pieces if p.meta.get("rhythm") == group]
        mid = lambda p, k: (min(q[k] for q in p.mesh.pos) + max(q[k] for q in p.mesh.pos)) / 2
        if group == "leaf":       # the leaf is drawn open: measure along it, from its hinge axis
            hx, hz = var.meta["gate"]["hinge"]
            cs = sorted(math.hypot(mid(p, 0) - hx, mid(p, 2) - hz) for p in mine)
        else:
            cs = sorted(mid(p, ax) for p in mine)
        if len(cs) < 2:
            continue
        gaps = [b - a for a, b in zip(cs, cs[1:])]
        if max(gaps) - min(gaps) > 2e-3:
            out.append(f"{group}: centres {min(gaps):.3f}-{max(gaps):.3f} m apart, not evenly spaced")
        clear = min(gaps) - g["member"], max(gaps) - g["member"]
        if clear[1] > hi + 1e-6:
            out.append(f"{group}: {clear[1] * 1000:.0f} mm clear, over {hi * 1000:.0f} mm")
        if clear[0] < lo - 1e-6:
            out.append(f"{group}: {clear[0] * 1000:.0f} mm clear, under {lo * 1000:.0f} mm (closed up)")
    return out


def rule_gate(var, data):
    G = var.meta.get("gate")
    if not G:
        return []
    out = []
    Gd = data["parts"]["gate"]
    xa, xb = G["opening"]
    Gd_cap = data["parts"]["pier"]["cap_overhang_m"]
    if xb - xa < Gd["clear_min_m"] - 1e-6:
        out.append(f"the opening is {xb - xa:.3f} m clear, under {Gd['clear_min_m']} m")
    hinges = [p for p in var.pieces if p.meta.get("hinge")]
    if len(hinges) < 2:
        out.append(f"the leaf hangs on {len(hinges)} hinge(s), not two")
    for p in var.pieces:            # nothing but the gate inside the opening it guards
        if p.meta.get("gate") or p.role in K.BOARD_ROLES:
            continue
        inside = [q for q in p.mesh.pos if xa + GATE_TOL < q[0] < xb - GATE_TOL and q[1] > 0.01]
        if not inside:
            continue
        depth = max(min(q[0] - xa, xb - q[0]) for q in inside)
        if min(q[1] for q in p.mesh.pos) >= Gd["height_m"] and depth <= Gd_cap + GATE_TOL:
            continue        # a pier's cap overhanging the opening by its own overhang, above the gate
        out.append(f"{p.name} stands {depth * 1000:.0f} mm inside the gate's opening (a run across the entrance)")
        break
    leaf = [p for p in var.pieces if p.meta.get("leaf")]
    hx, hz = G["hinge"]
    reach = Gd["stile_m"] / 2 + Gd["hinge_radius_m"]
    if any(q[2] - hz > reach for p in leaf for q in p.mesh.pos):
        out.append("the leaf as drawn stands over the street side of the line (it swings over the walk)")
    x0, x1, z0, z1 = G["pier"]
    th0 = math.radians(G["drawn_deg"])
    for step in range(0, int(Gd["swing_deg"]) + 1, 5):
        d = math.radians(step) - th0
        c, s = math.cos(d), math.sin(d)
        hit = False
        for p in leaf:
            for x, _, z in p.mesh.pos:
                rx, rz = hx + (x - hx) * c + (z - hz) * s, hz - (x - hx) * s + (z - hz) * c
                if x0 + GATE_TOL < rx < x1 - GATE_TOL and z0 + GATE_TOL < rz < z1 - GATE_TOL:
                    hit = True
                    break
            if hit:
                break
        if hit:
            out.append(f"the leaf strikes its hinge pier at {step} degrees of its {Gd['swing_deg']} degree swing")
            break
    return out


def rule_wall(var, data):
    if "piers" not in var.meta:
        return []
    W = data["parts"]["wall"]
    out = []
    xs = sorted((min(q[0] for q in p.mesh.pos) + max(q[0] for q in p.mesh.pos)) / 2
                for p in var.pieces if p.meta.get("pier"))
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    if not gaps:
        out.append("a wall with fewer than two piers")
    elif max(gaps) > W["pier_spacing_max_m"] + 1e-6:
        out.append(f"piers {max(gaps):.3f} m apart, over {W['pier_spacing_max_m']} m")
    t = var.meta["wall"]["t"] / 2
    for p in var.pieces:
        if not p.meta.get("coping"):
            continue
        zs = [q[2] for q in p.mesh.pos]
        drip = min(max(zs) - t, -min(zs) - t)
        if drip < W["drip_min_m"] - 1e-6:
            out.append(f"{p.name}: overhangs the wall by {drip * 1000:.0f} mm, under the {W['drip_min_m'] * 1000:.0f} mm drip")
    return out


def rule_canopy(var, data):
    if "canopy" not in var.meta:
        return []
    C = data["parts"]["canopy"]
    out = []
    gl = next((p for p in var.pieces if p.meta.get("glass")), None)
    if gl is None:
        return ["no glass"]
    bottom = [q for q in gl.mesh.pos]
    zb = min(q[2] for q in bottom)
    zf = max(q[2] for q in bottom)
    yb = min(q[1] for q in bottom if abs(q[2] - zb) < 1e-6)
    yf = min(q[1] for q in bottom if abs(q[2] - zf) < 1e-6)
    pitch = math.degrees(math.atan2(yb - yf, zf - zb))
    if pitch < C["pitch_min_deg"] - 1e-6:
        out.append(f"the glass falls {pitch:.1f} degrees from the wall, under {C['pitch_min_deg']} (it holds water)")
    xs = sorted((min(q[0] for q in p.mesh.pos) + max(q[0] for q in p.mesh.pos)) / 2
                for p in var.pieces if p.meta.get("rafter"))
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    if gaps and max(gaps) > C["rafter_spacing_max_m"] + 1e-6:
        out.append(f"rafters {max(gaps):.3f} m apart, over {C['rafter_spacing_max_m']} m")
    return out


def rule_costs(var, v, data):
    cap = data["costs"]["max_triangles"].get(v["class"], 0)
    n = K.triangles(var)
    return [f"{n} triangles over the {v['class']} budget of {cap}"] if n > cap else []


def build_all(data):
    return [K.build_variant(v, data, index=i) for i, v in enumerate(data["variants"])]


def check(data, built=None, glb=True):
    fails = [f"data: {m}" for m in rule_data(data)]
    built = built or build_all(data)
    for var in built:
        v = var.v
        for name, msgs in (("seated", rule_seated(var)), ("rooted", rule_rooted(var)),
                           ("doubled", rule_doubled(var)), ("shimmer", rule_shimmer(var, data)),
                           ("rhythm", rule_rhythm(var, data)), ("gate", rule_gate(var, data)),
                           ("wall", rule_wall(var, data)), ("canopy", rule_canopy(var, data)),
                           ("costs", rule_costs(var, v, data))):
            fails += [f"{v['id']} {name}: {m}" for m in msgs]
    if glb:
        blob = K.to_glb(K.build_kit(data), data)
        spec = ROOT / data["specimen"]
        if not spec.exists() or spec.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes "
                         f"(run python3 generators/archetypes/k11_ironwork.py)")
    return fails, built


def self_test(data) -> int:
    def var_of(built, vid):
        return next(b for b in built if b.v["id"] == vid)

    def piece(built, vid, name):
        return next(p for p in var_of(built, vid).pieces if p.name == name)

    def d_pitch(d):
        d["parts"]["picket"]["pitch_m"] = 0.2

    def d_note(d):
        d["variants"][0]["note"] = ""

    def d_restrict(d):
        d["restrictions"] = [r for r in d["restrictions"] if r["rule"] != "never_crosses_entrance"]

    def d_budget(d):
        d["costs"]["max_triangles"]["fence"] = 100

    def d_thin(d):
        d["parts"]["rail"]["thickness_m"] = 0.006

    def d_outward(d):
        d["parts"]["gate"]["drawn_deg"] = -30

    def d_swing(d):
        d["parts"]["gate"]["swing_deg"] = 180

    def d_narrow(d):
        next(v for v in d["variants"] if v["kind"] == "gate")["clear_m"] = 0.7

    def d_drip(d):
        d["parts"]["wall"]["coping_overhang_m"] = 0.01

    def d_flat(d):
        d["parts"]["canopy"]["pitch_deg"] = 2


    def g_pier(built):      # the wall's middle pier taken out
        var = var_of(built, "k11.wall.brick_with_piers")
        var.pieces = [p for p in var.pieces if p.name != "pier 2"]

    def g_lift(built):      # a picket lifted clear of its rails
        p = piece(built, "k11.fence.spear_on_curb", "picket 3")
        p.mesh.pos = [(x, y + 1.5, z) for x, y, z in p.mesh.pos]

    def g_cross(built):     # a curb carried across the gate's opening
        var = var_of(built, "k11.gate.walk_gate_on_piers")
        p = next(p for p in var.pieces if p.name == "curb 1")
        p.mesh.pos = [(x + 0.6, y, z) for x, y, z in p.mesh.pos]

    def g_hinge(built):     # a hinge taken off
        var = var_of(built, "k11.gate.walk_gate_on_piers")
        var.pieces = [p for p in var.pieces if p.name != "hinge 2"]

    def g_short(built):     # a grille bar stopped short of the reveal's head and sill
        p = piece(built, "k11.grille.basement_window", "bar 2")
        ys = [q[1] for q in p.mesh.pos]
        lo, hi = min(ys), max(ys)
        p.mesh.pos = [(x, lo + 0.1 if y == lo else hi - 0.1, z) for x, y, z in p.mesh.pos]

    def g_doubled(built):   # a second face laid on a newel's front
        p = piece(built, "k11.rail.stoop_rail", "newel 1")
        zf = max(q[2] for q in p.mesh.pos)
        xs = sorted({q[0] for q in p.mesh.pos})
        ys = sorted({q[1] for q in p.mesh.pos})
        q = K.Piece("doubled face", "iron", "open")
        q.mesh.poly([(xs[0], ys[0], zf), (xs[-1], ys[0], zf), (xs[-1], ys[-1], zf), (xs[0], ys[-1], zf)], (0, 0, 1))
        var_of(built, "k11.rail.stoop_rail").pieces.append(q)

    def g_uneven(built):    # one baluster moved 40 mm along the stair
        p = piece(built, "k11.rail.stoop_rail", "baluster 4")
        p.mesh.pos = [(x, y, z - 0.04) for x, y, z in p.mesh.pos]

    cases = [("pickets at a 0.20 m pitch", d_pitch, None, "data"),
             ("a variant with no note", d_note, None, "data"),
             ("the entrance restriction dropped", d_restrict, None, "data"),
             ("a fence budget of 100 triangles", d_budget, None, "costs"),
             ("a 6 mm rail", d_thin, None, "shimmer"),
             ("a gate drawn open over the walk", d_outward, None, "gate"),
             ("a gate swung 180 degrees", d_swing, None, "gate"),
             ("a 0.70 m gate opening", d_narrow, None, "gate"),
             ("a 10 mm coping overhang", d_drip, None, "wall"),
             ("canopy glass at 2 degrees", d_flat, None, "canopy"),
             ("a wall with its middle pier taken out", None, g_pier, "wall"),
             ("a picket lifted off its rails", None, g_lift, "rooted"),
             ("a curb across the gate's opening", None, g_cross, "gate"),
             ("a gate on one hinge", None, g_hinge, "gate"),
             ("a grille bar short of its reveal", None, g_short, "rooted"),
             ("a face laid on a newel's face", None, g_doubled, "doubled"),
             ("a baluster out of rhythm", None, g_uneven, "rhythm")]
    bad = 0
    for label, dmut, gmut, rule in cases:
        d = copy.deepcopy(data)
        if dmut:
            dmut(d)
        built = build_all(d)
        if gmut:
            gmut(built)
        fails, _ = check(d, built, glb=False)
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
    print(f"ok   K11 ironwork kit: {len(built)} variants, {n} pieces rooted in what carries them, no doubled face, "
          f"no member under the {shimmer_floor(data) * 1000:.1f} mm shimmer floor, panel rhythm, gate opening and "
          f"swing, wall piers and drip, canopy fall, budgets and the specimen hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
