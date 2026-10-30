#!/usr/bin/env python3
"""Gate: K01 lays an all-stone house (T-2788).

A K01 record naming `construction: "stone"` is a stone house, not a stone front on a brick
box: its K02 `stone_front` (fabric, dressing, coursing) is laid round every face. No record
names it yet (1801 Prairie, T-2789, is the first to move onto it), so this builds the K01
houses that already carry a K02 front — smooth Bedford and Lemont, smooth and rock-faced
brownstone, with rear wings, north bays, hip, gable and flat roofs — as all-stone, in
memory, through generators/archetypes/k01_frontage.py, and measures what was built:

  round     every wall component of the house (the street front, both flanks, the rear and
            every rear wing's walls) is laid as K02 coursed stone in the record's fabric
  no brick  no K03 brick slot (walls, a bay's brick, a brick head's or string course's
            units) has a vertex under the main eave: what brick is left is a K15 stack's
  level     every face's courses are struck on the street front's own bed lines (and its
            own wall top), so each course runs level round every corner
  dressed   every window and door on every face sits on its K06 stone sill or K07 stoop
            under a K02 flat arch: an opening in stone takes a stone head, never brick
  closed    no coincident face on K01's 1 mm grid (the contract's coincident_rule)
  refused   an all-stone record naming a quoin bond, a brick bay or no stone_front
  as-was    every K01 record as committed still builds its flanks and rear in K03 brick
            (the bytes are validate.py --stale's: they hash this generator)

    python3 tools/check_stone_house_kit.py --check       the gate
    python3 tools/check_stone_house_kit.py --self-test   break each rule in memory; each must fail
"""
from __future__ import annotations

import copy
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))

FIXTURES = ("house_1621_prairie", "house_1619_prairie", "house_1634_prairie",
            "coleman_ames_house_1811_prairie")
BRICK = ("brick", "bay_brick")
COURSES = ("k01.wall.stone_course", "k01.wall.rusticated_base", "k01.wall.coping")


def records():
    import k01_emit
    return {st["id"]: (st, phase) for st, phase, _ in k01_emit.records()}


def as_stone(phase):
    q = copy.deepcopy(phase)
    q["form"]["construction"]["value"] = "stone"
    return q


def build(st, phase):
    from archetypes import k01_frontage, k01_frontage_params
    return k01_frontage.build(k01_frontage_params.from_phase(phase, st), st["id"])


def walls_of(a):
    """The house's wall components (not a dormer's face): each registers its construction."""
    return [cid for cid, c in a.components.items()
            if cid.startswith("k01.wall.") and "construction" in c["instances"][0]["params"]
            and cid != "k01.wall.dormer_face"]


def verdicts(name, a):
    """[(ok, rule, detail)] for one all-stone build."""
    from archetypes import k01_frontage_params as P
    k = a.p.stone
    out = []
    walls = walls_of(a)
    # a timber wing (T-2417) stays timber on a stone house, as a frame bay does
    timber = {cid for cid in walls if a.components[cid]["instances"][0]["params"]["construction"] == "frame"}
    plain = [cid for cid in walls if cid not in timber
             and a.components[cid]["instances"][0]["params"].get("fabric") != k["fabric"]]
    wings = [cid for cid in walls if ".wing." in cid]
    out.append((not plain and len(walls) - len(timber) >= 4, f"{name} round",
                f"{len(walls) - len(timber)} walls ({len(wings)} wing walls, {len(timber)} timber) in {k['fabric']}"
                + (f"; not coursed: {plain}" if plain else "")))
    E = a.p.eave_m
    low = {n: sum(1 for q in pr.pos if q[1] < E - 1e-6) for n, pr in a.prims.items()
           if n in BRICK or n.startswith("brick_unit_")}
    low = {n: c for n, c in low.items() if c}
    out.append((not low, f"{name} no brick", f"brick vertices under the {E} m eave: {low or 'none'}"))
    beds = {round(y, 4) for y in a.front_course_beds}
    tops = {round(w["top_m"], 4) for w in a.p.rear_wings} | {round(a.soffit_m, 4)}
    off = []
    for cid in COURSES:
        for inst in a.components.get(cid, {}).get("instances", []):
            b, t = inst["sockets"]["bed"][1], inst["sockets"]["top"][1]
            for y in (round(b, 4), round(t, 4)):
                # T-2542: over the front's soffit the front lays no bed to keep level with,
                # so a wing standing taller than the front's eave (1811's range, three
                # storeys behind a front whose third is in its roof) courses on its own
                if y not in beds and y not in tops and y <= round(a.soffit_m, 4):
                    off.append(y)
    out.append((not off, f"{name} level",
                f"{len(beds)} front beds; course lines off them: {sorted(set(off))[:6] or 'none'}"))
    arches = a.components.get("k01.opening.flat_arch", {}).get("instances", [])
    spans = [(i["sockets"]["springing"], i["sockets"]["crown"]) for i in arches]
    # each opening's frame: the main walls' and every wing wall's (origin, run)
    frames = {cid: (O, R) for cid, (_m, O, R, *_r) in a._walls.items()}
    for w in a.p.rear_wings:
        frames |= {f"k01.wall.wing.{w['id']}.{side}": (O, R) for side, (O, R, _l) in P.wing_walls(w).items()}
    bare = []
    for o in [*a.p.openings, *[x for w in a.p.rear_wings for x in w["openings"]]]:
        if o.wall in ("k01.wall.street_front", "k01.wall.dormer_face") or o.wall in timber:
            continue   # the front keeps its own K09 heads; a dormer's face is the roof's; timber is cased
        if o.component in P.ROUND_CUT:
            continue   # T-3133: a round head is K06's arch band, or plain as its picture draws it (T-2884)
        O, R = frames[o.wall]
        s0 = o.s_m - o.width_m / 2 - 0.12   # the arch's springing, seated 0.12 m into the wall
        want = (O[0] + R[0] * s0, o.head_m, O[2] + R[2] * s0)
        if not any(max(abs(x - y) for x, y in zip(sp, want)) < 1e-3 for sp, _ in spans):
            bare.append(f"{o.wall}@{o.s_m}")
    out.append((not bare, f"{name} dressed",
                f"{len(arches)} flat arches; openings with no stone head: {bare[:4] or 'none'}"))
    grid = Counter()
    for pr in a.prims.values():
        for i in range(0, len(pr.idx), 3):
            grid[tuple(sorted(tuple(round(x * 1000) for x in pr.pos[pr.idx[i + j]]) for j in range(3)))] += 1
    doubled = sum(1 for v in grid.values() if v > 1)
    out.append((doubled == 0, f"{name} closed", f"{doubled} coincident triangle(s) of {sum(grid.values())}"))
    return out


def refusals(st, phase):
    """[(ok, rule, detail)]: what an all-stone record may not name."""
    from archetypes import k01_frontage_params as P
    out = []

    def refused(what, mutate):
        q = as_stone(phase)
        mutate(q["form"])
        try:
            P.from_phase(q, st)
        except P.ParamError as e:
            return out.append((True, f"refused {what}", str(e)[:90]))
        out.append((False, f"refused {what}", "built"))

    refused("a quoin bond", lambda f: f["stone_front"]["value"].__setitem__("corner_bond", ["south"]))
    refused("no stone_front", lambda f: f.pop("stone_front"))
    bays = (phase["form"].get("bays") or {}).get("value")
    if bays:
        def brick_bay(f):
            f["bays"]["value"][0]["fabric"] = "brick"
        refused("a brick bay", brick_bay)
    return out


def as_was(recs):
    """Every committed record still lays its flanks and rear as before: brick, unless its own
    record says stone."""
    out = []
    for sid, (st, phase) in sorted(recs.items()):
        if phase["form"]["construction"]["value"] == "stone":
            continue
        a = build(st, phase)
        # T-3006: a rounded corner is the street front's own stone turning the corner, not a flank;
        # T-3112: nor is a pier at the front's end, laid apart from it in the same stone
        stone = [cid for cid in walls_of(a) if cid not in ("k01.wall.street_front", "k01.wall.round_corner",
                                                          "k01.wall.front_pier")
                 and a.components[cid]["instances"][0]["params"].get("fabric")]
        out.append((not stone, f"{sid} as-was", f"stone-coursed side walls: {stone or 'none'}"))
    return out


def run_check() -> int:
    recs = records()
    out = []
    for sid in FIXTURES:
        st, phase = recs[sid]
        out += verdicts(sid, build(st, as_stone(phase)))
    st, phase = recs[FIXTURES[0]]
    out += refusals(st, phase)
    out += as_was(recs)
    bad = [x for x in out if not x[0]]
    for ok, rule, detail in out:
        if not ok or "--verbose" in sys.argv:
            print(f"  {'ok  ' if ok else 'FAIL'} {rule}: {detail}")
    print(f"{'ok  ' if not bad else 'FAIL'} K01 all-stone house: {len(out) - len(bad)}/{len(out)} "
          f"rule(s) on {len(FIXTURES)} fixture(s) and {len(recs)} record(s)")
    return 1 if bad else 0


def run_self_test() -> int:
    """Break each rule in memory; each must fail."""
    from archetypes import k01_frontage as F
    recs = records()
    st, phase = recs["house_1621_prairie"]
    failed = 0

    def case(label, rule, fn):
        nonlocal failed
        hit = [x for x in fn() if not x[0] and rule in x[1]]
        if hit:
            print(f"   self-test | ok   {label}: '{rule}' fails ({hit[0][2][:70]})")
        else:
            failed += 1
            print(f"   self-test | FAIL {label}: the '{rule}' rule let it through")

    # a stone front on a brick box: the record says stone, the kit lays the old house
    def front_only():
        from archetypes import k01_frontage_params as P
        p = P.from_phase(as_stone(phase), st)
        p.stone.pop("all_round")
        a = F.build(p, st["id"])
        a.front_course_beds = getattr(a, "front_course_beds", [])
        return verdicts("1621 front only", a)
    case("the flanks left in brick", "round", front_only)
    case("the flanks left in brick", "no brick", front_only)

    # a flank struck on its own lines: the courses step at the corner
    def own_lines():
        real = F.Assembly._course_plan

        def plan(self, frame, openings, yf, beds=None, extra=()):
            if beds is not None:
                beds = [round(y + 0.05, 4) if 2.0 < y < yf - 0.5 else y for y in beds]
            return real(self, frame, openings, yf, beds, extra)
        F.Assembly._course_plan = plan
        try:
            return verdicts("1621 own lines", build(st, as_stone(phase)))
        finally:
            F.Assembly._course_plan = real
    case("a flank's courses off the front's beds", "level", own_lines)

    # a side opening left with no head
    def headless():
        real = F.Assembly.flat_arch
        F.Assembly.flat_arch = lambda self, frame, *a_, **k_: None if frame[0][0] <= 0.0 else real(self, frame, *a_, **k_)
        try:
            return verdicts("1621 headless", build(st, as_stone(phase)))
        finally:
            F.Assembly.flat_arch = real
    case("the rear and wing openings left headless", "dressed", headless)

    # a face laid twice
    def doubled():
        a = build(st, as_stone(phase))
        pr = a.prims["rough_stone_trim"]
        n = len(pr.pos)
        pr.pos += pr.pos[:3]
        pr.idx += [n, n + 1, n + 2]
        return verdicts("1621 doubled", a)
    case("a stone's face laid twice", "closed", doubled)

    # the refusal let go: a quoin returned into brick on an all-stone house
    # a kit that quietly lays a refused record as a stone front on brick instead of refusing it
    def downgraded():
        from archetypes import k01_frontage_params as P
        real = P.from_phase

        def lax(q, record=None):
            q = copy.deepcopy(q)
            if q["form"]["construction"]["value"] == "stone":
                q["form"]["construction"]["value"] = "brick_with_stone_front" if q["form"].get("stone_front") else "brick"
            return real(q, record)
        P.from_phase = lax
        try:
            return refusals(st, phase)
        finally:
            P.from_phase = real
    case("a refused record built anyway", "refused", downgraded)

    # and the true kit passes every rule
    clean = [x for x in verdicts("1621", build(st, as_stone(phase))) if not x[0]]
    if clean:
        failed += 1
        print(f"   self-test | FAIL the unbroken kit fails {len(clean)} rule(s): {clean[0][1]}")
    else:
        print("   self-test | ok   the unbroken kit holds every rule")
    print(f"{'ok  ' if not failed else 'FAIL'} K01 all-stone house self-test: {7 - failed}/7")
    return 1 if failed else 0


def main(argv) -> int:
    if "--check" in argv:
        return run_check()
    if "--self-test" in argv:
        return run_self_test()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
