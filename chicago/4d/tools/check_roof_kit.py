#!/usr/bin/env python3
"""Gate: the K05 roof-construction kit builds every roof as one closed, uncrossed solid
(T-2301).

The kit's sizes are data in data/components/prairie_1904/k05_roofs.json and are built by
generators/archetypes/k05_roofs.py. This rebuilds every variant and measures the BUILT
surface, welded on K01's 1 mm quantum, against the lessons of the Glessner roof repairs:

  pitch      every pitch inside RECONSTRUCTION-RULES' range for its kind
  closed     every edge shared by exactly two triangles, wound oppositely: watertight,
             no T-junction, no hole, no flap; and the enclosed volume positive
  one shell  every triangle reachable from every other across shared edges, so no
             cornice, return, coping or verge floats free of the roof
  doubled    no two triangles on the same three grid points, and none degenerate
  crossing   no triangle passes through another: no roof plane crosses a gable, a
             parapet or a dormer cheek, and no element pokes through another
  parapet    a parapet gable's covering stops at the parapet's inner face, and every
             point of the parapet's top clears the roof behind it by the upstand
  graph      the ridges, hips, valleys, curbs, eaves, verges, returns and abutments read
             off the built surface are the ones the variant declares
  hidden     no face of an element's interior survives the union
  budget     the roof's triangles inside its budget
  specimen   docs/RESEARCH/k05-roof-kit/k05_roof_kit.glb is the generator's bytes

and, since T-2302, every HOUSE roofed from the kit (each k01_frontage record, as
generators/archetypes/k01_frontage.py builds it): closed, one shell, doubled, crossing
and hidden on its joined roof (dormer, sash recess and chimney stacks included), every
covering edge classed, and every ridge, hip and valley in its graph dressed by K04.

    python3 tools/check_roof_kit.py --check       the gate
    python3 tools/check_roof_kit.py --self-test   break each rule in memory; each must fail
    python3 tools/check_roof_kit.py --report      the measured numbers, per variant
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k05_roofs as K  # noqa: E402


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def weld(r, q):
    """The roof's triangles on the q-metre grid: [(i, j, k, role)] over grid points."""
    ids, pts, out = {}, [], []
    for a, b, c, role, _n in r.tris:
        t = []
        for p in (r.pts[a], r.pts[b], r.pts[c]):
            k = tuple(round(x / q) for x in p)
            if k not in ids:
                ids[k] = len(pts)
                pts.append(tuple(x * q for x in k))
            t.append(ids[k])
        out.append((t[0], t[1], t[2], role))
    return pts, out


def measure(r, data) -> dict:
    q = data["measure"]["quantum_m"]
    pts, tris = weld(r, q)
    m = {"triangles": len(tris), "roof_triangles": sum(1 for t in tris if t[3] not in K.BOARD_ROLES)}
    # degenerate and doubled
    amin = data["measure"]["min_triangle_area_m2"]
    degenerate, seen, doubled = 0, {}, 0
    for t in tris:
        a, b, c = pts[t[0]], pts[t[1]], pts[t[2]]
        n = _cross(_sub(b, a), _sub(c, a))
        if math.sqrt(_dot(n, n)) / 2 < amin or len({t[0], t[1], t[2]}) < 3:
            degenerate += 1
        key = tuple(sorted(t[:3]))
        doubled += seen.get(key, 0)
        seen[key] = seen.get(key, 0) + 1
    m["degenerate"], m["doubled"] = degenerate, doubled
    # closed and oriented
    directed: dict = {}
    for ti, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            directed.setdefault((a, b), []).append(ti)
    open_edges = misoriented = 0
    for (a, b), ts in directed.items():
        if len(ts) > 1:
            misoriented += 1
        back = directed.get((b, a), [])
        if len(back) != len(ts):
            open_edges += 1
    m["open_edges"], m["misoriented_edges"] = open_edges, misoriented
    vol = 0.0
    for t in tris:
        a, b, c = pts[t[0]], pts[t[1]], pts[t[2]]
        vol += _dot(a, _cross(b, c)) / 6
    m["volume_m3"] = round(vol, 3)
    # one shell: triangles joined across shared undirected edges
    parent = list(range(len(tris)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    by_edge: dict = {}
    for ti, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            by_edge.setdefault((min(a, b), max(a, b)), []).append(ti)
    for ts in by_edge.values():
        for x in ts[1:]:
            parent[root(x)] = root(ts[0])
    m["shells"] = len({root(i) for i in range(len(tris))})
    # crossing
    m["crossings"] = crossings(pts, tris)
    m["hidden_faces"] = sum(1 for t in tris if t[3] == "hidden")
    m["roles"] = sorted({t[3] for t in tris})
    return m


def _seg_cuts_tri(p, q, a, b, c, eps=1e-9):
    n = _cross(_sub(b, a), _sub(c, a))
    nn = math.sqrt(_dot(n, n))
    if nn < 1e-15:
        return False
    dp, dq = _dot(n, _sub(p, a)) / nn, _dot(n, _sub(q, a)) / nn
    if dp > -1e-7 and dq > -1e-7 or dp < 1e-7 and dq < 1e-7:
        return False   # both on one side, or touching the plane
    s = dp / (dp - dq)
    x = (p[0] + s * (q[0] - p[0]), p[1] + s * (q[1] - p[1]), p[2] + s * (q[2] - p[2]))
    for u, v in ((a, b), (b, c), (c, a)):
        if _dot(_cross(_sub(v, u), _sub(x, u)), n) / nn < 1e-7:
            return False
    return True


def crossings(pts, tris) -> int:
    """Pairs of triangles sharing no point, one of whose edges passes through the other's
    interior. A sweep on x keeps it to the pairs whose boxes overlap."""
    boxes = []
    for ti, t in enumerate(tris):
        ps = [pts[i] for i in t[:3]]
        boxes.append((min(p[0] for p in ps), max(p[0] for p in ps),
                      min(p[1] for p in ps), max(p[1] for p in ps),
                      min(p[2] for p in ps), max(p[2] for p in ps), ti))
    boxes.sort()
    active, hits = [], 0
    for bx in boxes:
        active = [a for a in active if a[1] >= bx[0] - 1e-9]
        t1 = tris[bx[6]]
        for ax in active:
            if ax[3] < bx[2] - 1e-9 or bx[3] < ax[2] - 1e-9 or ax[5] < bx[4] - 1e-9 or bx[5] < ax[4] - 1e-9:
                continue
            t2 = tris[ax[6]]
            if set(t1[:3]) & set(t2[:3]):
                continue
            A = [pts[i] for i in t1[:3]]
            B = [pts[i] for i in t2[:3]]
            if any(_seg_cuts_tri(A[i], A[(i + 1) % 3], *B) for i in range(3)) or \
               any(_seg_cuts_tri(B[i], B[(i + 1) % 3], *A) for i in range(3)):
                hits += 1
        active.append(bx)
    return hits


def parapet_clearance(r, data):
    """For a parapet gable: how far the covering reaches into the parapet band (must be
    nothing) and the least clear height of the parapet's top above the covering."""
    v = r.v
    tw = data["parts"]["parapet"]["thickness_m"]
    D = v["depth_m"]
    z0 = r.O[2]
    cov = [r.pts[i] for t in r.tris if t[3] == "covering" for i in t[:3]]
    zs = [p[2] - z0 for p in cov]
    intrusion = max(0.0, tw - min(zs), max(zs) - (D - tw))
    # the covering's height at the parapet's inner face, sampled along it
    line = r.meta["parapet_line"]
    least = math.inf
    for w, top in line:
        x = w + r.O[0]
        near = [p[1] for p in cov if abs(p[0] - x) < 0.02 and (abs(p[2] - z0 - tw) < 1e-3 or abs(p[2] - z0 - (D - tw)) < 1e-3)]
        if near:
            least = min(least, top - max(near))
    # and between the line's points, against the analytic roof
    t = math.tan(math.radians(v["pitch_deg"]))
    W, E = v["width_m"], v["eave_m"]
    for (wa, ya), (wb, yb) in zip(line, line[1:]):
        for k in range(11):
            u = k / 10
            w, y = wa + (wb - wa) * u, ya + (yb - ya) * u
            if 0.0 <= w <= W:
                roof = E + min(w, W - w) * t
                least = min(least, y - roof)
    return round(intrusion, 5), round(least, 4)


def verdicts(kit, data, specimen_ok=True):
    """[(ok, label, detail)] for every rule, every variant."""
    out = []
    rng = data["ranges"]
    for r in kit:
        v = r.v
        vid = v["id"]
        if v["kind"] == "mansard":
            lo, hi = rng["mansard_lower_deg"]
            ul, uh = rng["mansard_upper_deg"]
            ok = lo <= v["lower_pitch_deg"] <= hi and ul <= v["upper_pitch_deg"] <= uh
            out.append((ok, f"{vid} pitch", f"lower {v['lower_pitch_deg']} in {lo}-{hi}, upper {v['upper_pitch_deg']} in {ul}-{uh}"))
        else:
            lo, hi = rng["pitch_deg"][v["pitch_range"]]
            out.append((lo <= v["pitch_deg"] <= hi, f"{vid} pitch", f"{v['pitch_deg']} in {v['pitch_range']} {lo}-{hi}"))
        m = measure(r, data)
        out.append((m["open_edges"] == 0 and m["misoriented_edges"] == 0 and m["volume_m3"] > 0, f"{vid} closed",
                    f"open edges {m['open_edges']}, misoriented {m['misoriented_edges']}, volume {m['volume_m3']} m3"))
        out.append((m["shells"] == 1, f"{vid} one shell", f"{m['shells']} shell(s)"))
        out.append((m["doubled"] == 0 and m["degenerate"] == 0, f"{vid} doubled",
                    f"doubled {m['doubled']}, degenerate {m['degenerate']}"))
        out.append((m["crossings"] == 0, f"{vid} crossing", f"{m['crossings']} triangle pair(s) pass through each other"))
        out.append((m["hidden_faces"] == 0, f"{vid} hidden", f"{m['hidden_faces']} interior face(s) survive"))
        if v["kind"] == "parapet_gable":
            intr, least = parapet_clearance(r, data)
            up = data["parts"]["parapet"]["upstand_min_m"]
            out.append((intr <= 1e-3 and least >= up - 1e-3, f"{vid} parapet",
                        f"covering into the parapet {intr} m, least upstand {least} m (min {up})"))
        g = K.graph(r.pts, r.tris, data)
        got = g["counts"]
        want = v["expect"]
        bad = {k: (want.get(k, 0), got.get(k, 0)) for k in set(want) | set(got)
               if k in want and want[k] != got.get(k, 0)}
        stray = [k for k in got if "|" in k]
        out.append((not bad and not stray, f"{vid} graph",
                    f"{got}" + (f"; declared {want}" if bad else "") + (f"; unclassed {stray}" if stray else "")))
        cap = data["costs"]["max_triangles"][v["budget"]]
        out.append((m["roof_triangles"] <= cap, f"{vid} budget", f"{m['roof_triangles']} roof triangles (max {cap})"))
    out.append((specimen_ok, "specimen", "docs/RESEARCH/k05-roof-kit/k05_roof_kit.glb is the generator's bytes"
                if specimen_ok else "the specimen GLB is stale: run python3 generators/archetypes/k05_roofs.py"))
    return out


class _Shell:
    def __init__(self, pts, tris):
        self.pts, self.tris = pts, tris


def houses(build=None):
    """[(name, assembly)] for every k01_frontage record, built as the bake builds it."""
    import k01_emit
    from archetypes import k01_frontage, k01_frontage_params
    build = build or k01_frontage.build
    return [(f"{st['id']}/{phase['id']}", build(k01_frontage_params.from_phase(phase, st), st["id"]))
            for st, phase, _ in k01_emit.records()]


def house_verdicts(name, asm, data):
    """The kit's rules on a house's joined roof (T-2302), and K04 laid on its graph."""
    m = measure(_Shell(*asm.roof_shell), data)
    out = [(m["open_edges"] == 0 and m["misoriented_edges"] == 0 and m["volume_m3"] > 0, f"{name} closed",
            f"open edges {m['open_edges']}, misoriented {m['misoriented_edges']}, volume {m['volume_m3']} m3"),
           (m["shells"] == 1, f"{name} one shell", f"{m['shells']} shell(s)"),
           (m["doubled"] == 0 and m["degenerate"] == 0, f"{name} doubled",
            f"doubled {m['doubled']}, degenerate {m['degenerate']}"),
           (m["crossings"] == 0, f"{name} crossing", f"{m['crossings']} triangle pair(s) pass through each other"),
           (m["hidden_faces"] == 0, f"{name} hidden", f"{m['hidden_faces']} interior face(s) survive")]
    got = asm.roof_graph["counts"]
    stray = [k for k in got if "|" in k]
    out.append((not stray, f"{name} graph", f"{got}" + (f"; unclassed {stray}" if stray else "")))
    want = {k: got.get(k, 0) for k in ("ridge", "hip", "valley")}
    dressed = getattr(asm, "dressed", None)
    if asm.p.roof:
        out.append((dressed == want, f"{name} dressed", f"K04 on {dressed} of {want} graph lines"))
    return out


def specimen_ok(kit, data) -> bool:
    out = ROOT / data["specimen"]
    return out.exists() and out.read_bytes() == K.to_glb(kit, data)


def run_check() -> int:
    data = K.load()
    kit = K.build_kit(data)
    res = verdicts(kit, data, specimen_ok(kit, data))
    built = houses()
    for name, asm in built:
        hr = house_verdicts(name, asm, data)
        print(f"{'ok  ' if all(x[0] for x in hr) else 'FAIL'} {name}: roof from the K05 kit, "
              f"{len(asm.roof_shell[1])} triangles, graph {asm.roof_graph['counts']}")
        res += hr
    bad = [x for x in res if not x[0]]
    for ok, label, detail in res:
        if not ok:
            print(f"FAIL {label}: {detail}")
    print(f"{'ok  ' if not bad else 'FAIL'} K05 roof kit: {len(kit)} roofs and {len(built)} house(s), "
          f"{len(res) - len(bad)}/{len(res)} rules hold")
    return 1 if bad else 0


def run_report() -> int:
    data = K.load()
    for r in K.build_kit(data):
        m = measure(r, data)
        g = K.graph(r.pts, r.tris, data)
        print(r.v["id"], json.dumps({k: m[k] for k in m if k != "roles"}), g["counts"], "seams", g["seam_edges"])
    return 0


def _fails(label_part, res):
    return any(not ok and label_part in label for ok, label, _ in res)


def run_self_test() -> int:
    data = K.load()
    by_id = {v["id"]: v for v in data["variants"]}
    cases = []

    def case(name, label, fn):
        cases.append((name, label, fn))

    def one(vid, d=None, joined=True):
        d = d or data
        return K.build_variant([v for v in d["variants"] if v["id"] == vid][0], d, joined=joined)

    def res_of(r, d=None):
        return verdicts([r], d or data, True)

    # closed: a triangle removed leaves a hole
    def hole():
        r = one("k05.roof.hip")
        r.tris = r.tris[:-1]
        return res_of(r)
    case("a missing triangle opens the roof", "closed", hole)

    # orientation: one triangle wound the wrong way
    def flipped():
        r = one("k05.roof.hip")
        a, b, c, role, n = r.tris[0]
        r.tris[0] = (a, c, b, role, n)
        return res_of(r)
    case("a face wound inward", "closed", flipped)

    # doubled: a face laid twice
    def doubled():
        r = one("k05.roof.gable")
        r.tris = r.tris + [r.tris[5]]
        return res_of(r)
    case("a face laid twice", "doubled", doubled)

    # crossing: the elements laid together without the union (planes run through gables)
    def unjoined():
        return res_of(one("k05.roof.cross_gable", joined=False))
    case("a cross gable laid without the union: planes through planes", "crossing", unjoined)

    def unjoined_parapet():
        return res_of(one("k05.roof.gable_stepped", joined=False))
    case("a stepped gable laid without the union: the roof through its parapet", "crossing", unjoined_parapet)

    # one shell: a return lifted clear of the eave floats
    def floating():
        r = one("k05.roof.gable")
        lifted = []
        for a, b, c, role, n in r.tris:
            lifted.append((a, b, c, role, n))
        # move every return point up 0.3 m: the returns leave the eave box
        moved = {}
        pts = list(r.pts)
        for a, b, c, role, n in r.tris:
            if role == "return":
                for i in (a, b, c):
                    if i not in moved:
                        pts.append((pts[i][0], pts[i][1] + 0.3, pts[i][2]))
                        moved[i] = len(pts) - 1
        r.tris = [((moved[a], moved[b], moved[c]) if role == "return" else (a, b, c)) + (role, n)
                  for a, b, c, role, n in r.tris]
        r.pts = pts
        return res_of(r)
    case("a return lifted off its eave", "one shell", floating)

    # parapet: a parapet too low for its roof
    def low_parapet():
        d = copy.deepcopy(data)
        d["parts"]["parapet"]["upstand_min_m"] = 0.05
        d["parts"]["parapet"]["top_above_ridge_m"] = 0.05
        r = one("k05.roof.gable_stepped", d)
        return res_of(r, data)
    case("a stepped parapet built 0.05 m clear, held to 0.3", "parapet", low_parapet)

    # graph: a declared valley the roof does not have
    def graph_lie():
        d = copy.deepcopy(data)
        [v for v in d["variants"] if v["id"] == "k05.roof.hip"][0]["expect"]["valley"] = 2
        return res_of(one("k05.roof.hip", d), d)
    case("a hip roof declared with two valleys", "graph", graph_lie)

    # pitch: a mansard lower face outside its range
    def steep():
        d = copy.deepcopy(data)
        [v for v in d["variants"] if v["id"] == "k05.roof.mansard_convex"][0]["lower_pitch_deg"] = 85
        return verdicts([one("k05.roof.mansard_convex", d)], d, True)
    case("a mansard's lower face at 85 degrees", "pitch", steep)

    def flat():
        d = copy.deepcopy(data)
        [v for v in d["variants"] if v["id"] == "k05.roof.hip"][0]["pitch_deg"] = 20
        return verdicts([one("k05.roof.hip", d)], d, True)
    case("a hip at 20 degrees", "pitch", flat)

    # hidden: an interior face left in
    def hidden():
        r = one("k05.roof.hip")
        a, b, c, role, n = r.tris[0]
        r.tris[0] = (a, b, c, "hidden", n)
        return res_of(r)
    case("an element's interior face left in the union", "hidden", hidden)

    # budget
    def budget():
        d = copy.deepcopy(data)
        d["costs"]["max_triangles"]["simple"] = 10
        return verdicts([one("k05.roof.hip", d)], d, True)
    case("a hip over a 10-triangle budget", "budget", budget)

    # specimen
    def stale():
        kit = K.build_kit(data)
        return verdicts(kit[:1], data, False)
    case("a stale specimen", "specimen", stale)

    failed = 0
    for name, label, fn in cases:
        res = fn()
        if _fails(label, res):
            print(f"   self-test | ok   {name}: the '{label}' rule refuses it")
        else:
            failed += 1
            print(f"   self-test | FAIL {name}: the '{label}' rule let it through")
    # T-2302: the house's roof laid as loose elements, not joined: its planes cross its
    # dormer and its stacks, which is the failure the house was rebuilt to remove
    def house_unjoined():
        real = K.union_all
        K.union_all = lambda solids: [p for s_ in solids for p in s_]
        try:
            name, asm = houses()[0]
        finally:
            K.union_all = real
        return house_verdicts(name, asm, data)
    case("the 1808 roof laid without the union", "crossing", house_unjoined)

    # and the true kit passes every rule (so the cases above fail for their own reason)
    data2 = K.load()
    kit = K.build_kit(data2)
    clean = [x for x in verdicts(kit, data2, True) if not x[0]]
    if clean:
        failed += 1
        print(f"   self-test | FAIL the unbroken kit fails {len(clean)} rule(s): {clean[0][1]}")
    else:
        print("   self-test | ok   the unbroken kit holds every rule")
    print(f"{'ok  ' if not failed else 'FAIL'} K05 roof kit self-test: {len(cases) + 1 - failed}/{len(cases) + 1}")
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
