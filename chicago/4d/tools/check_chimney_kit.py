#!/usr/bin/env python3
"""Gate: the K15 chimney kit builds every stack as one closed solid seated in its roof,
with dark recessed flues, flashing on every side and a light tier that keeps location and
height (T-2312).

The kit's sizes are data in data/components/prairie_1904/k15_chimneys.json and are built
by generators/archetypes/k15_chimneys.py. This rebuilds every variant, both tiers, and
measures the BUILT surface, welded on K01's 1 mm quantum (K05's own measure,
tools/check_roof_kit.py):

  closed     every edge shared by exactly two triangles, wound oppositely, and the
             enclosed volume positive: the stack and its roof are one watertight solid
  one shell  every triangle reachable from every other, so no stack, cap, pot, band or
             flashing floats free of the roof
  doubled    no two triangles on the same three grid points, and none degenerate
  crossing   no triangle passes through another: no shaft through a covering it was not
             joined to, no pot through its cap
  hidden     no face of a part's interior survives the union
  seated     no face of a stack shows below the covering it stands in: the shaft is cut
             where it passes through the roof, not stood on it or hung under it
  flue       every declared flue is a recess open at the top, its walls and floor in the
             flue's (near-black) material, at least its declared depth deep
  draught    every stack's top clears the covering within the draught radius by the
             clearance, and the covering where it emerges by the least height
  cricket    a stack on a slope wider than the threshold has a cricket behind it, and
             one narrower (or astride a ridge) has flashing there instead
  flashing   stepped flashing on both sides (at least two steps each, on a slope) and
             flashing or a cricket at the top and bottom of every stack
  light      the light tier's stack stands on the same plan centre and reaches the
             same top as the full stack (to the quantum), within its budget
  budget     every stack's triangles within its budget (the roof excluded)
  specimen   docs/RESEARCH/k15-chimney-kit/k15_chimney_kit.glb is the generator's bytes

    python3 tools/check_chimney_kit.py --check       the gate
    python3 tools/check_chimney_kit.py --self-test   break each rule in memory; each must fail
    python3 tools/check_chimney_kit.py --report      the measured numbers, per variant
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import k05_roofs as K5  # noqa: E402
from archetypes import k15_chimneys as K  # noqa: E402
from check_roof_kit import measure  # noqa: E402

FLUE_MAX_LUMINANCE = 0.06   # a flue reads as a dark hole, not a painted grey


def _clip(poly, axis, bound, keep_above):
    """Sutherland-Hodgman against one axis-aligned half-space, interpolating all three
    coordinates (a covering triangle is planar, so its height interpolates exactly)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        pin = p[axis] >= bound if keep_above else p[axis] <= bound
        qin = q[axis] >= bound if keep_above else q[axis] <= bound
        if pin:
            out.append(p)
        if pin != qin:
            s = (bound - p[axis]) / (q[axis] - p[axis])
            out.append(tuple(p[k] + s * (q[k] - p[k]) for k in range(3)))
    return out


def covering_max(r, cx, cz, half):
    """The highest point of the built covering over the square of half-side `half` about
    (cx, cz), read off the covering triangles."""
    best = None
    for a, b, c, role, _n in r.tris:
        if role != "covering":
            continue
        poly = [r.pts[a], r.pts[b], r.pts[c]]
        for axis, bound, above in ((0, cx - half, True), (0, cx + half, False),
                                   (2, cz - half, True), (2, cz + half, False)):
            poly = _clip(poly, axis, bound, above)
            if not poly:
                break
        for p in poly:
            best = p[1] if best is None else max(best, p[1])
    return best


def _frames(r, data):
    cover, t = K.covering(r.rv)
    return cover, t, [K.Frame(s, cover) for s in r.v["stacks"]]


def _local(F, O, p):
    """A world point in a stack's frame: (a, b, c)."""
    x, z = p[0] - O[0] - F.cx, p[2] - F.cz
    return (x * F.ua[0] + z * F.ua[1], p[1], x * F.uc[0] + z * F.uc[1])


def _tri_centroid(r, t):
    return tuple(sum(r.pts[i][k] for i in t[:3]) / 3 for k in range(3))


def _stack_tris(r, F, O, roles, pad=0.6):
    """The triangles of `roles` near stack F (within its plan plus pad)."""
    out = []
    for t in r.tris:
        if t[3] not in roles:
            continue
        a, _, c = _local(F, O, _tri_centroid(r, t))
        if abs(a) <= F.d / 2 + pad and abs(c) <= F.w / 2 + pad:
            out.append(t)
    return out


def verdicts(kit, data, specimen_ok=True):
    q = data["measure"]["quantum_m"]
    res = []
    caps = data["costs"]["max_triangles"]
    mats = K.materials()
    lum = sum(mats["flue"]["color"]) / 3
    for full, light in kit:
        vid = full.v["id"]
        for r, tier in ((full, "full"), (light, "light")):
            m = measure(r, data)
            res.append((m["open_edges"] == 0 and m["misoriented_edges"] == 0 and m["volume_m3"] > 0,
                        f"{vid} {tier}: closed",
                        f"{m['open_edges']} open, {m['misoriented_edges']} misoriented edge(s), volume {m['volume_m3']}"))
            res.append((m["shells"] == 1, f"{vid} {tier}: one shell", f"{m['shells']} shells"))
            res.append((m["doubled"] == 0 and m["degenerate"] == 0, f"{vid} {tier}: doubled",
                        f"{m['doubled']} doubled, {m['degenerate']} degenerate"))
            res.append((m["crossings"] == 0, f"{vid} {tier}: crossing", f"{m['crossings']} crossing pair(s)"))
            res.append((m["hidden_faces"] == 0, f"{vid} {tier}: hidden", f"{m['hidden_faces']} interior face(s)"))
        cover, t, frames = _frames(full, data)
        O = full.O
        # seated: no stack face below the covering it stands in
        low = 0
        for tri in full.tris:
            if tri[3] in K.STACK_ROLES:
                for i in tri[:3]:
                    p = full.pts[i]
                    if p[1] < cover(p[0] - O[0], p[2]) - q:
                        low += 1
                        break
        res.append((low == 0, f"{vid}: seated", f"{low} stack triangle(s) below the covering"))
        for si, (s, F) in enumerate(zip(full.v["stacks"], frames)):
            tag = f"{vid} stack {si}"
            # flues
            pf = data["pot"]
            flue_tris = _stack_tris(full, F, O, ("flue",), pad=0.0)
            bad = []
            for off, pot in K.flues(s):
                half = pf["bore_m"] if pot else data["parts"]["flue"]["opening_m"] / 2
                mine = [tt for tt in flue_tris
                        if abs(_local(F, O, _tri_centroid(full, tt))[2] - off) <= half + q]
                ys = [full.pts[i][1] for tt in mine for i in tt[:3]]
                top = s["top_m"] + (max(h for h, _ in pf["profiles"][pot]) if pot else 0.0)
                need = s["top_m"] - data["parts"]["flue"]["depth_m"]
                if not mine or min(ys) > need + q or max(ys) < top - q:
                    bad.append(f"flue at {off:+.3f}: " + (f"{len(mine)} faces, {min(ys):.3f}..{max(ys):.3f} m, "
                                                          f"wants {need:.3f}..{top:.3f}" if mine else "no recess"))
            if lum > FLUE_MAX_LUMINANCE:
                bad.append(f"flue material luminance {lum:.3f} > {FLUE_MAX_LUMINANCE}")
            res.append((not bad, f"{tag}: flue", "; ".join(bad) or "ok"))
            # draught
            dr = data["draught"]
            cap_top = max((full.pts[i][1] for tt in _stack_tris(full, F, O, K.STACK_ROLES, pad=0.3)
                           if tt[3] in ("cap_stone", "cap_cement") for i in tt[:3]), default=None)
            cmax = covering_max(full, F.cx + O[0], F.cz, dr["radius_m"])
            own = max(F.cov(a, c) for a in (-F.d / 2, F.d / 2) for c in (-F.w / 2, F.w / 2))
            ok = (cap_top is not None and abs(cap_top - s["top_m"]) <= q and cmax is not None
                  and cap_top >= cmax + dr["clear_m"] - q and cap_top >= own + dr["min_above_own_m"] - q)
            res.append((ok, f"{tag}: draught",
                        f"cap top {cap_top} (declared {s['top_m']}), covering within {dr['radius_m']} m "
                        f"{cmax and round(cmax, 3)} + {dr['clear_m']}, covering at the stack {own:.3f} + "
                        f"{dr['min_above_own_m']}"))
            # cricket and flashing, by which side of the shaft they lie on
            wants = (not F.ridge) and F.w > data["parts"]["cricket"]["min_width_m"]
            ck = _stack_tris(full, F, O, ("cricket",))
            ck_hi = [tt for tt in ck if _local(F, O, _tri_centroid(full, tt))[0] > F.d / 2 - q * 20]
            fl = _stack_tris(full, F, O, ("flashing",), pad=0.3)
            sides = {"low": 0, "high": 0, "-c": 0, "+c": 0}
            steps = {"-c": set(), "+c": set()}
            for tt in fl:
                a, y, c = _local(F, O, _tri_centroid(full, tt))
                if c < -F.w / 2:
                    sides["-c"] += 1
                elif c > F.w / 2:
                    sides["+c"] += 1
                if a < -F.d / 2:
                    sides["low"] += 1
                elif a > F.d / 2:
                    sides["high"] += 1
                n = K5._tri_normal(full.pts, tt[:3])
                if n[1] > 0.999 and abs(c) > F.w / 2 and abs(a) < F.d / 2:
                    steps["-c" if c < 0 else "+c"].add(round(y / q))
            res.append(((len(ck_hi) > 0) == wants and (wants or sides["high"] > 0),
                        f"{tag}: cricket",
                        f"{'wants' if wants else 'wants no'} cricket (width {F.w} m, "
                        f"{'astride a ridge' if F.ridge else 'on a slope'}); built {len(ck_hi)} cricket face(s) "
                        f"behind, {sides['high']} flashing face(s) behind"))
            need_steps = 1 if F.ridge else 2
            okf = sides["-c"] > 0 and sides["+c"] > 0 and sides["low"] > 0 and (sides["high"] > 0 or ck_hi) \
                and len(steps["-c"]) >= need_steps and len(steps["+c"]) >= need_steps
            res.append((okf, f"{tag}: flashing",
                        f"faces by side {sides}, step levels -c {len(steps['-c'])} +c {len(steps['+c'])}"))
            # light: same plan centre, same top
            lt = _stack_tris(light, F, O, ("light_brick", "light_stone"), pad=0.0)
            lp = [light.pts[i] for tt in lt for i in tt[:3]]
            fp = [full.pts[i] for tt in _stack_tris(full, F, O, K.STACK_ROLES, pad=0.3) for i in tt[:3]]
            if lp and fp:
                lc = ((min(p[0] for p in lp) + max(p[0] for p in lp)) / 2, (min(p[2] for p in lp) + max(p[2] for p in lp)) / 2)
                fc = (F.cx + O[0], F.cz)
                ltop, ftop = max(p[1] for p in lp), max(p[1] for p in fp)
                okl = abs(lc[0] - fc[0]) <= q and abs(lc[1] - fc[1]) <= q and abs(ltop - ftop) <= q \
                    and len(lt) <= caps["light"]
                det = (f"light centre ({lc[0]:.3f}, {lc[1]:.3f}) top {ltop:.3f} m, {len(lt)} triangles; full centre "
                       f"({fc[0]:.3f}, {fc[1]:.3f}) top {ftop:.3f} m")
            else:
                okl, det = False, "no light stack built"
            res.append((okl, f"{tag}: light", det))
        n = K.triangles(full)
        cap = caps[full.v["budget"]]
        res.append((n <= cap, f"{vid}: budget", f"{n} stack triangles, budget {cap}"))
    res.append((specimen_ok, "specimen", "the committed GLB is not the generator's bytes: "
                "run python3 generators/archetypes/k15_chimneys.py"))
    return res


def specimen_ok(kit, data) -> bool:
    out = ROOT / data["specimen"]
    return out.exists() and out.read_bytes() == K.to_glb(kit, data)


def run_check() -> int:
    data = K.load()
    kit = K.build_kit(data)
    res = verdicts(kit, data, specimen_ok(kit, data))
    bad = [x for x in res if not x[0]]
    for ok, label, detail in res:
        if not ok:
            print(f"FAIL {label}: {detail}")
    print(f"{'ok  ' if not bad else 'FAIL'} K15 chimney kit: {len(kit)} variants, {len(res) - len(bad)}/{len(res)} rules hold")
    return 1 if bad else 0


def run_report() -> int:
    data = K.load()
    kit = K.build_kit(data)
    for ok, label, detail in verdicts(kit, data, True):
        print(f"{'ok  ' if ok else 'FAIL'} {label}: {detail}")
    for full, light in kit:
        print(full.v["id"], json.dumps({"stack_triangles": K.triangles(full), "light_triangles": K.triangles(light),
                                        "stacks": full.meta["stacks"]}))
    return 0


def _fails(label_part, res):
    return any(not ok and label_part in label for ok, label, _ in res)


class _Mut:
    """A built variant with its points or triangles replaced, for a self-test case."""

    def __init__(self, r, pts=None, tris=None):
        self.v, self.rv, self.meta, self.O, self.light, self.seed = r.v, r.rv, r.meta, r.O, r.light, r.seed
        self.pts = pts if pts is not None else r.pts
        self.tris = tris if tris is not None else r.tris


def run_self_test() -> int:
    data = K.load()
    roofs = K5.load()
    kit = K.build_kit(data, roofs)
    by_id = {f.v["id"]: (f, li) for f, li in kit}
    cases = []

    def case(name, label, fn):
        cases.append((name, label, fn))

    def res_of(pair, d=None):
        return verdicts([pair], d or data, True)

    def rebuilt(vid, d, **kw):
        v = [x for x in d["variants"] if x["id"] == vid][0]
        f, li = by_id[vid]
        return (K.build_variant(v, d, roofs, origin=f.O, **kw), li)

    def hole():
        f, li = by_id["k15.stack.service"]
        return res_of((_Mut(f, tris=f.tris[:-1]), li))
    case("a missing triangle opens the stack", "closed", hole)

    def flipped():
        f, li = by_id["k15.stack.service"]
        a, b, c, role, n = f.tris[0]
        return res_of((_Mut(f, tris=[(a, c, b, role, n)] + f.tris[1:]), li))
    case("one triangle wound inward", "closed", flipped)

    def unjoined():
        return res_of(rebuilt("k15.stack.service", data, joined=False))
    case("the stack laid in the roof without the union", "crossing", unjoined)

    def floating():
        d = copy.deepcopy(data)
        d["parts"]["shaft"]["below_covering_m"] = -1.0
        return res_of(rebuilt("k15.stack.stone", d), d)
    case("a shaft stood a metre clear of its roof", "one shell", floating)

    def sunk():
        f, li = by_id["k15.stack.service"]
        moved = {i for t in f.tris if t[3] == "shaft_brick" for i in t[:3]}
        pts = [(p[0], p[1] - 3.0, p[2]) if i in moved else p for i, p in enumerate(f.pts)]
        return res_of((_Mut(f, pts=pts), li))
    case("a shaft dropped through the roof so it shows below the covering", "seated", sunk)

    def uncut():
        return res_of(rebuilt("k15.stack.ridge", data, cut=False))
    case("flues left uncut: a cap with no openings", "flue", uncut)

    def grey_flue():
        d = copy.deepcopy(data)
        old = K.materials

        def lighter():
            m = old()
            m["flue"] = {"color": (0.5, 0.5, 0.5), "roughness": 1.0}
            return m
        K.materials = lighter
        try:
            return res_of(by_id["k15.stack.stone"], d)
        finally:
            K.materials = old
    case("a flue painted mid-grey", "flue", grey_flue)

    def short():
        d = copy.deepcopy(data)
        [x for x in d["variants"] if x["id"] == "k15.stack.service"][0]["stacks"][0]["top_m"] = 5.75
        return res_of(rebuilt("k15.stack.service", d), d)
    case("a service stack cut down to barely clear its ridge", "draught", short)

    def no_cricket():
        f, li = by_id["k15.stack.service"]
        return res_of((_Mut(f, tris=[t for t in f.tris if t[3] != "cricket"]), li))
    case("the cricket behind a wide stack taken away", "cricket", no_cricket)

    def bare_side():
        f, li = by_id["k15.stack.sherman"]
        F = _frames(f, data)[2][0]
        keep = [t for t in f.tris if not (t[3] == "flashing" and _local(F, f.O, _tri_centroid(f, t))[2] > F.w / 2)]
        return res_of((_Mut(f, tris=keep), li))
    case("one side of a stack left without its flashing", "flashing", bare_side)

    def light_low():
        f, li = by_id["k15.stack.ridge"]
        moved = {i for t in li.tris if t[3] == "light_brick" for i in t[:3]}
        top = max(li.pts[i][1] for i in moved)
        pts = [(p[0], p[1] - 0.4, p[2]) if i in moved and p[1] > top - 1e-6 else p for i, p in enumerate(li.pts)]
        return res_of((f, _Mut(li, pts=pts)))
    case("a light tier that stops short of the pots' height", "light", light_low)

    def light_shifted():
        f, li = by_id["k15.stack.stone"]
        moved = {i for t in li.tris if t[3] == "light_stone" for i in t[:3]}
        pts = [(p[0] + 0.2, p[1], p[2]) if i in moved else p for i, p in enumerate(li.pts)]
        return res_of((f, _Mut(li, pts=pts)))
    case("a light tier moved 0.2 m off its stack", "light", light_shifted)

    def bloated():
        d = copy.deepcopy(data)
        d["costs"]["max_triangles"]["carved"] = 100
        return res_of(by_id["k15.stack.sherman"], d)
    case("a carved stack over its budget", "budget", bloated)

    def stale():
        return verdicts([by_id["k15.stack.stone"]], data, False)
    case("a specimen that is not the generator's bytes", "specimen", stale)

    failed = 0
    for name, label, fn in cases:
        res = fn()
        if _fails(label, res):
            print(f"   self-test | ok   {name}: refused by '{label}'")
        else:
            failed += 1
            print(f"   self-test | FAIL {name}: the '{label}' rule let it through")
    clean = [x for x in verdicts(kit, data, True) if not x[0]]
    if clean:
        failed += 1
        print(f"   self-test | FAIL the unbroken kit fails {len(clean)} rule(s): {clean[0][1]}: {clean[0][2]}")
    else:
        print("   self-test | ok   the unbroken kit holds every rule")
    print(f"{'ok  ' if not failed else 'FAIL'} K15 chimney kit self-test: {len(cases) + 1 - failed}/{len(cases) + 1}")
    return 1 if failed else 0


def main(argv) -> int:
    if "--check" in argv:
        return run_check()
    if "--self-test" in argv:
        return run_self_test()
    if "--report" in argv:
        return run_report()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
