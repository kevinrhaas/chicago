#!/usr/bin/env python3
"""Hold the K10 cornice kit to its data, and every built piece to resting on what carries it (T-2316).

    python3 tools/check_cornice_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_cornice_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k10_cornices.json and the
generator (generators/archetypes/k10_cornices.py) builds every variant from them. This
rebuilds each variant in memory and measures the BUILT geometry, not the data's
promises. The K10 acceptance asks for continuous corner returns, no hanging ends and no
roof clashes; each clause is a rule here:

  data       every part, profile and variant states a confidence and a note; the
             bracket spacing inside its range; the two restrictions stated (no generic
             profile in place of a documented one; corner returns continuous)
  seated     every open edge of a piece lies on another surface of the variant (a wall,
             a frieze, a soffit, a deck, a roof): no hanging end, nothing floating
             (tools/check_trim_kit.py's rule, shared with K09)
  rooted     every closed piece (a kneeler, a finial, a ridge cap, every bar of the
             cresting) passes through its host's surface
  doubled    no two coplanar faces overlap
  returns    every swept run reaches round both corners of the face it crowns, by its
             own projection: a cornice that stops at the corner is refused
  projection every swept moulding stands as far from its face as its section says (1 mm)
  brackets   brackets evenly spaced inside the data's range on every run, and one within
             `corner_m` of every corner on BOTH faces
  balustrade the clear gap between balusters under `max_clear_m` and never closed up, a
             pedestal at every corner
  roof       no part of a dormer below the roof it stands on
  cresting   posts no further apart than the data allows
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

from archetypes import k10_cornices as K  # noqa: E402
from check_trim_kit import rule_doubled, rule_rooted, rule_seated  # noqa: E402

CONF = ("attested", "inferred", "reconstructed")


def rule_data(data):
    out = []
    for name, part in data["parts"].items():
        if name.startswith("_"):
            continue
        items = part.items() if name == "profiles" else [(name, part)]
        for sub_name, pp in items:
            if sub_name.startswith("_"):
                continue
            if pp.get("confidence") not in CONF or not pp.get("note"):
                out.append(f"part {sub_name}: no confidence and note")
    B = data["parts"]["bracket"]
    lo, hi = B["range_spacing_m"]
    if not lo <= B["spacing_m"] <= hi:
        out.append(f"bracket spacing {B['spacing_m']} m is outside {lo}-{hi} m")
    for v in data["variants"]:
        if v.get("confidence") not in CONF or not v.get("note"):
            out.append(f"{v['id']}: no confidence and note")
        if v.get("class") not in data["costs"]["max_triangles"]:
            out.append(f"{v['id']}: class {v.get('class')!r} has no triangle budget")
    rules = {r["rule"] for r in data["restrictions"]}
    for need in ("never_replaces_landmark", "corner_returns_continuous"):
        if need not in rules:
            out.append(f"restriction {need} is not stated")
    return out


def rule_returns(var):
    """A run-bearing piece on a pavilion or an eave turns both corners of the front."""
    out = []
    for p in var.pieces:
        names = p.meta.get("run_names")
        pr = p.meta.get("proj")
        if not names or not pr or "front" not in names[len(names) // 2]:
            continue
        if len(names) < 3:
            out.append(f"{p.name}: runs along {names} only; a run crowns its face and both returns")
            continue
        xs = [q[0] - var.O[0] - pr["cx"] for q in p.mesh.pos if q[2] - var.O[2] > pr["face_z"] + pr["m"] - 1e-6]
        need = pr["half"] + pr["m"]
        reach = min(-min(xs), max(xs)) if xs else 0.0
        if reach < need - 1e-3:
            out.append(f"{p.name}: reaches {reach:.3f} m each side of its face's centre, not round its "
                       f"corners ({need:.3f} m)")
    return out


def rule_projection(var):
    out = []
    for p in var.pieces:
        pr = p.meta.get("proj")
        if not pr or not p.mesh.pos:
            continue
        got = max(q[2] - var.O[2] for q in p.mesh.pos) - pr["face_z"]
        if abs(got - pr["m"]) > 1e-3:
            out.append(f"{p.name}: stands {got * 1000:.1f} mm from its face, its section says {pr['m'] * 1000:.1f} mm")
    return out


def rule_brackets(var, data):
    out = []
    B = data["parts"]["bracket"]
    lo, hi = B["range_spacing_m"]
    for name, r in var.meta.get("runs", {}).items():
        pos = r["brackets"]
        if not pos:
            out.append(f"run {name}: no brackets")
            continue
        for a, b in zip(pos, pos[1:]):
            if not lo - 1e-6 <= b - a <= hi + 1e-6:
                out.append(f"run {name}: brackets {b - a:.3f} m apart, outside {lo}-{hi} m")
                break
        if r["corners"][0] and pos[0] > B["corner_m"] + 1e-6:
            out.append(f"run {name}: the first bracket stands {pos[0]:.3f} m from its corner (at most {B['corner_m']})")
        if r["corners"][1] and r["L"] - pos[-1] > B["corner_m"] + 1e-6:
            out.append(f"run {name}: the last bracket stands {r['L'] - pos[-1]:.3f} m from its corner "
                       f"(at most {B['corner_m']})")
    built = sum(1 for p in var.pieces if "bracket" in p.meta)
    if var.meta.get("runs") and not built:
        out.append("brackets placed in the data but none built")
    return out


def rule_balustrade(var, data):
    out = []
    if "balusters" not in var.meta:
        return out
    B = data["parts"]["balustrade"]
    rmax = max(r for r, _ in B["baluster"])
    for bay in var.meta["balusters"]:
        gap = bay["step"] - 2 * rmax
        if gap > B["max_clear_m"] + 1e-6:
            out.append(f"run {bay['run']}: {gap * 1000:.0f} mm clear between balusters, over {B['max_clear_m'] * 1000:.0f} mm")
        if gap < 0.01:
            out.append(f"run {bay['run']}: balusters {gap * 1000:.0f} mm apart, closed up")
    if var.meta.get("corner_pedestals", 0) < 2:
        out.append("a corner without a pedestal")
    return out


def rule_roof(var):
    out = []
    R = var.meta.get("roof")
    if not R:
        return out
    for p in var.pieces:
        if not p.meta.get("on_roof"):
            continue
        worst = min((q[1] - var.O[1]) - R["H"] + (q[2] - var.O[2]) * R["tan"] for q in p.mesh.pos)
        if worst < -1e-6:
            out.append(f"{p.name}: {-worst * 1000:.1f} mm below the roof it stands on (a roof clash)")
    D = var.meta.get("dormer")
    if D and D["z_valley"] < -R["D"] / 2:
        out.append(f"the dormer's valley runs past the ridge ({D['z_valley']:.3f} m)")
    return out


def rule_cresting(var, data):
    """Measured on the posts as built, not on the generator's own list of them."""
    if "cresting" not in var.meta:
        return []
    mx = data["parts"]["cresting"]["post_spacing_max_m"]
    xs = sorted((min(q[0] for q in p.mesh.pos) + max(q[0] for q in p.mesh.pos)) / 2
                for p in var.pieces if p.name.startswith("post ") and not p.name.startswith("post finial"))
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    return [f"posts {g:.3f} m apart, over {mx} m" for g in gaps if g > mx + 1e-6][:1]


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
                           ("doubled", rule_doubled(var)), ("returns", rule_returns(var)),
                           ("projection", rule_projection(var)), ("brackets", rule_brackets(var, data)),
                           ("balustrade", rule_balustrade(var, data)), ("roof", rule_roof(var)),
                           ("cresting", rule_cresting(var, data)), ("costs", rule_costs(var, v, data))):
            fails += [f"{v['id']} {name}: {m}" for m in msgs]
    if glb:
        blob = K.to_glb(K.build_kit(data), data)
        spec = ROOT / data["specimen"]
        if not spec.exists() or spec.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes "
                         f"(run python3 generators/archetypes/k10_cornices.py)")
    return fails, built


def self_test(data) -> int:
    def var_of(built, vid):
        return next(b for b in built if b.v["id"] == vid)

    def piece(built, vid, name):
        return next(p for p in var_of(built, vid).pieces if p.name == name)

    def d_spacing(d):
        d["parts"]["bracket"]["spacing_m"] = 1.2

    def d_note(d):
        d["variants"][0]["note"] = ""

    def d_restrict(d):
        d["restrictions"] = [r for r in d["restrictions"] if r["rule"] != "corner_returns_continuous"]

    def d_budget(d):
        d["costs"]["max_triangles"]["cornice"] = 100

    def d_pitch(d):
        d["parts"]["balustrade"]["pitch_m"] = 0.42

    def d_recess(d):
        d["parts"]["dormer"]["recess_m"] = 0.6

    def g_posts(built):     # a cresting post (and its finial) taken out
        var = var_of(built, "k10.cresting.iron_ridge")
        var.pieces = [p for p in var.pieces if p.name not in ("post 2", "post finial 2")]

    def g_float(built):     # a bracket dropped 5 mm from under its soffit
        p = piece(built, "k10.cornice.bracketed_timber", "bracket 2")
        p.mesh.pos = [(x, y - 0.005, z) for x, y, z in p.mesh.pos]

    def g_drift(built):     # the gable's finial lifted clear of its coping
        p = piece(built, "k10.gable.shaped_coping", "finial")
        p.mesh.pos = [(x, y + 0.2, z) for x, y, z in p.mesh.pos]

    def g_doubled(built):   # a dentil given a back face on its band
        var = var_of(built, "k10.entablature.classical_dentil")
        p = [p for p in var.pieces if p.meta.get("dentil", {}).get("run") == "front"][3]
        back = sorted({q for q in p.mesh.pos if abs(q[2] - var.O[2] - 0.1) < 1e-9})
        if len(back) >= 4:
            xs, ys = sorted({q[0] for q in back}), sorted({q[1] for q in back})
            p.mesh.poly([(xs[0], ys[0], 0.1), (xs[-1], ys[0], 0.1), (xs[-1], ys[-1], 0.1), (xs[0], ys[-1], 0.1)],
                        (0.0, 0.0, -1.0))

    def g_stop(built):      # a crown that stops short of its corners
        var = var_of(built, "k10.cornice.pressed_metal")
        p = next(p for p in var.pieces if p.name == "crown")
        cx = var.O[0]
        p.mesh.pos = [(cx + (x - cx) * 0.85, y, z) for x, y, z in p.mesh.pos]

    def g_proj(built):      # a frieze pushed 4 mm out from its wall
        p = piece(built, "k10.entablature.classical_dentil", "frieze")
        p.mesh.pos = [(x, y, z + 0.004) for x, y, z in p.mesh.pos]

    cases = [("brackets 1.2 m apart", d_spacing, None, "data"),
             ("a variant with no note", d_note, None, "data"),
             ("the corner-return restriction dropped", d_restrict, None, "data"),
             ("a cornice budget of 100 triangles", d_budget, None, "costs"),
             ("balusters at a 0.42 m pitch", d_pitch, None, "balustrade"),
             ("a dormer window recessed 0.6 m into its roof", d_recess, None, "roof"),
             ("a cresting post taken out", None, g_posts, "cresting"),
             ("a bracket 5 mm under its soffit", None, g_float, "seated"),
             ("a finial lifted off its coping", None, g_drift, "rooted"),
             ("a dentil with a back face on its band", None, g_doubled, "doubled"),
             ("a crown that stops short of its corners", None, g_stop, "returns"),
             ("a frieze 4 mm off its wall", None, g_proj, "projection")]
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
    print(f"ok   K10 cornice kit: {len(built)} variants, {n} pieces seated or rooted, no doubled face, corner "
          f"returns, projections, bracket courses, balustrade, roof, cresting, budgets and the specimen hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
