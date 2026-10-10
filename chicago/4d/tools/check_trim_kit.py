#!/usr/bin/env python3
"""Hold the K09 carved-trim kit to its data, and every built piece to being relief (T-2309).

    python3 tools/check_trim_kit.py --check       the gate (tools/check.sh)
    python3 tools/check_trim_kit.py --self-test   break each rule; each must be refused

The kit's sizes are data in data/components/prairie_1904/k09_trim.json and the
generator (generators/archetypes/k09_trim.py) builds every variant from them. This
rebuilds each variant in memory and measures the BUILT geometry, not the data's
promises. The K09 acceptance asks for arch rings, mouldings, hoods, colonnettes,
tracery and bounded foliate relief as real geometry, and for a bespoke hero entrance
set against a restrained rowhouse surround; each clause is a rule here:

  data       every variant and part states a confidence and a note; voussoir counts
             odd and inside their range; every variant's motif declared; the
             restriction that keeps a generic motif off a documented landmark stated
  seated     every open edge of a piece lies on another surface of the variant (a
             wall face, a block, a floor, a sunk field), never over a hole: nothing
             floats and nothing hangs
  rooted     every closed piece (a capital leaf, a crocket, a finial) passes through
             its host's surface
  doubled    no two coplanar faces overlap (the back-to-back coincidence K01 refuses)
  relief     every piece stands as far from its surface as the data says (1 mm), and
             no piece stands less than the relief floor: no texture panel
  arch       every voussoir's intrados on its arch, its joints radial to its own
             arc's centre, the crown stone centred
  colonnette plinth, base, shaft and abacus in order, the shaft inside its range, the
             abacus wider than the capital it carries
  bounded    every leaf of a foliate panel inside its field less the margin
  compare    the hero entrance has more orders, more pieces and more relief than the
             rowhouse surround, and the rowhouse carries no carving
  costs      every variant inside its triangle budget
  specimen   the committed specimen GLB is the generator's bytes
"""

from __future__ import annotations

import copy
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k09_trim as K  # noqa: E402

TOL = 2e-4      # an open edge "lies on" a surface within 0.2 mm
CELL = 0.1


def tris(piece):
    m = piece.mesh
    for i in range(0, len(m.idx), 3):
        yield [m.pos[m.idx[i + k]] for k in range(3)]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def key(p, nd=5):
    return tuple(round(c, nd) for c in p)


class Index:
    """Triangles in a uniform grid, for point and segment queries."""

    def __init__(self, items):
        self.cells = defaultdict(list)
        for owner, t in items:
            lo = [math.floor((min(q[k] for q in t) - TOL) / CELL) for k in range(3)]
            hi = [math.floor((max(q[k] for q in t) + TOL) / CELL) for k in range(3)]
            for i in range(lo[0], hi[0] + 1):
                for j in range(lo[1], hi[1] + 1):
                    for k in range(lo[2], hi[2] + 1):
                        self.cells[(i, j, k)].append((owner, t))

    def near(self, lo, hi):
        seen = set()
        for i in range(math.floor(lo[0] / CELL), math.floor(hi[0] / CELL) + 1):
            for j in range(math.floor(lo[1] / CELL), math.floor(hi[1] / CELL) + 1):
                for k in range(math.floor(lo[2] / CELL), math.floor(hi[2] / CELL) + 1):
                    for it in self.cells.get((i, j, k), ()):
                        if id(it) not in seen:
                            seen.add(id(it))
                            yield it


def on_triangle(p, t) -> bool:
    n = cross(sub(t[1], t[0]), sub(t[2], t[0]))
    nn = math.sqrt(dot(n, n))
    if nn < 1e-14:
        return False
    n = (n[0] / nn, n[1] / nn, n[2] / nn)
    d = dot(sub(p, t[0]), n)
    if abs(d) > TOL:
        return False
    q = sub(p, (n[0] * d, n[1] * d, n[2] * d))
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        e = sub(b, a)
        c = cross(e, sub(q, a))
        if dot(c, n) < -TOL * math.sqrt(dot(e, e)):
            return False
    return True


def seg_hits(a, b, t) -> bool:
    """Segment a-b crosses triangle t (Moller-Trumbore, the segment's own span)."""
    e1, e2 = sub(t[1], t[0]), sub(t[2], t[0])
    d = sub(b, a)
    h = cross(d, e2)
    det = dot(e1, h)
    if abs(det) < 1e-14:
        return False
    f = 1.0 / det
    s = sub(a, t[0])
    u = f * dot(s, h)
    if u < 0 or u > 1:
        return False
    q = cross(s, e1)
    v = f * dot(d, q)
    if v < 0 or u + v > 1:
        return False
    w = f * dot(e2, q)
    return 0 <= w <= 1


def boundary(piece):
    """Edges used by exactly one triangle of the piece (by welded position)."""
    count = defaultdict(int)
    where = {}
    for t in tris(piece):
        for i in range(3):
            a, b = t[i], t[(i + 1) % 3]
            ka, kb = key(a), key(b)
            if ka == kb:
                continue
            e = (ka, kb) if ka < kb else (kb, ka)
            count[e] += 1
            where[e] = (a, b)
    return [where[e] for e, n in count.items() if n == 1]


# -- rules ------------------------------------------------------------------------------------

def rule_seated(var):
    out = []
    items = [(p.name, t) for p in var.pieces for t in tris(p)]
    idx = Index(items)
    for p in var.pieces:
        if p.rests == "board":
            continue
        loose = 0
        for a, b in boundary(p):
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
            lo, hi = [c - TOL for c in m], [c + TOL for c in m]
            if not any(o != p.name and on_triangle(m, t) for o, t in idx.near(lo, hi)):
                loose += 1
        if p.rests == "rooted" and boundary(p):
            out.append(f"{p.name}: a closed piece has {len(boundary(p))} open edge(s)")
        elif loose:
            out.append(f"{p.name}: {loose} open edge(s) rest on no surface (floating or hanging)")
    return out


def rule_rooted(var):
    out = []
    by = {p.name: p for p in var.pieces}
    for p in var.pieces:
        if p.rests != "rooted":
            continue
        host = by.get(p.host)
        if host is None:
            out.append(f"{p.name}: host {p.host!r} is not a piece of this variant")
            continue
        idx = Index([(host.name, t) for t in tris(host)])
        hit = False
        for t in tris(p):
            for i in range(3):
                a, b = t[i], t[(i + 1) % 3]
                lo = [min(a[k], b[k]) for k in range(3)]
                hi = [max(a[k], b[k]) for k in range(3)]
                if any(seg_hits(a, b, ht) for _, ht in idx.near(lo, hi)):
                    hit = True
                    break
            if hit:
                break
        if not hit:
            out.append(f"{p.name}: does not pass through its host {p.host!r} (floating)")
    return out


def rule_doubled(var):
    planes = defaultdict(list)
    for p in var.pieces:
        for t in tris(p):
            n = cross(sub(t[1], t[0]), sub(t[2], t[0]))
            nn = math.sqrt(dot(n, n))
            if nn < 1e-12:
                continue
            n = tuple(c / nn for c in n)
            k = max(range(3), key=lambda i: abs(n[i]))
            if n[k] < 0:
                n = tuple(-c for c in n)
            planes[(key(n, 3), round(dot(n, t[0]), 4))].append((p.name, t, n))
    out = []
    for (_, _), group in planes.items():
        if len(group) < 2:
            continue
        n = group[0][2]
        au = cross(n, (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0))
        la = math.sqrt(dot(au, au))
        au = tuple(c / la for c in au)
        av = cross(n, au)
        flat = [(o, [(dot(q, au), dot(q, av)) for q in t]) for o, t, _ in group]
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                a, b = flat[i][1], flat[j][1]
                if max(q[0] for q in a) <= min(q[0] for q in b) or max(q[0] for q in b) <= min(q[0] for q in a):
                    continue
                if max(q[1] for q in a) <= min(q[1] for q in b) or max(q[1] for q in b) <= min(q[1] for q in a):
                    continue
                aa = a if K.area2(a) > 0 else list(reversed(a))
                bb = b if K.area2(b) > 0 else list(reversed(b))
                from archetypes.k06_windows import clip
                ov = clip(aa, bb)
                if len(ov) >= 3 and abs(K.area2(ov)) > 1e-7:
                    out.append(f"{flat[i][0]} / {flat[j][0]}: coplanar faces overlap ({abs(K.area2(ov)) * 1e4:.2f} cm2)")
                    if len(out) > 4:
                        return out
    return out


def rule_relief(var, data):
    out = []
    floor = data["relief"]["min_relief_m"]
    for p in var.pieces:
        r = p.meta.get("relief")
        if not r or not p.mesh.pos:
            continue
        got = max(q[2] for q in p.mesh.pos) - r["plane_z"]
        if abs(got - r["proud_m"]) > 1e-3:
            out.append(f"{p.name}: stands {got * 1000:.1f} mm from its surface, data says {r['proud_m'] * 1000:.1f} mm")
        if got < floor:
            out.append(f"{p.name}: {got * 1000:.1f} mm of relief is under the {floor * 1000:.0f} mm floor (a painted panel)")
    for p in var.pieces:
        if p.role == "carving" and p.rests == "rooted":
            zs = [dot(q, (0, 0, 1)) for q in p.mesh.pos]
            span = max(math.dist(p.mesh.pos[0], q) for q in p.mesh.pos)
            if span < floor:
                out.append(f"{p.name}: {span * 1000:.1f} mm across, under the relief floor")
    return out


def rule_arch(var, v):
    out = []
    rings = defaultdict(list)
    for p in var.pieces:
        if "arch" in p.meta:
            rings[p.meta["course"]].append(p)
    for course, stones in rings.items():
        A = stones[0].meta["arch"]
        arch = K.Arch(A["kind"], A["cx"], A["span"], A["spring"], v.get("rise_over_span", 0.125))
        if len(stones) % 2 == 0:
            out.append(f"{course}: {len(stones)} voussoirs, an even ring has a joint at the crown")
        for p in stones:
            a = p.meta["arch"]
            z0 = p.meta["relief"]["plane_z"]
            back = [e for e in boundary(p) if abs(e[0][2] - z0) < 1e-6 and abs(e[1][2] - z0) < 1e-6]
            for e in back:
                ra = [_radius(arch, q) for q in e]
                if abs(ra[0][0] - ra[1][0]) > a["depth"] / 2:       # a joint: intrados to extrados
                    c = ra[0][1]
                    d = (e[1][0] - e[0][0], e[1][1] - e[0][1])
                    r = (e[0][0] - c[0], e[0][1] - c[1])
                    sin = abs(d[0] * r[1] - d[1] * r[0]) / (math.hypot(*d) * math.hypot(*r))
                    if sin > math.sin(math.radians(1.0)):
                        out.append(f"{p.name}: a joint {math.degrees(math.asin(min(1, sin))):.1f} deg off radial")
                        break
            intr = [q for e in back for q in e if abs(_radius(arch, q)[0] - (arch.R + a["inner_off"])) < 1e-3]
            if len(intr) < 2:
                out.append(f"{p.name}: its intrados is not on the arch")
        mid = sorted(stones, key=lambda p: p.meta["index"])[len(stones) // 2]
        xs = [q[0] for q in mid.mesh.pos]
        if abs((min(xs) + max(xs)) / 2 - arch.cx) > 1e-3:
            out.append(f"{course}: the crown stone is not centred on the arch")
    return out


def _radius(arch, q):
    if arch.kind == "pointed":
        c = (arch.s0, arch.spring) if q[0] >= arch.cx else (arch.s1, arch.spring)
        if abs(q[0] - arch.cx) < 1e-9:
            c = (arch.s0, arch.spring)
    else:
        c = (arch.cx, arch.cy)
    return math.hypot(q[0] - c[0], q[1] - c[1]), c


def rule_colonnette(var, data):
    out = []
    co = data["parts"]["colonnette"]
    for p in var.pieces:
        if "shaft" not in p.meta:
            continue
        ax, az = p.meta["shaft"]["axis"]
        y0, y1 = p.meta["shaft"]["y"]
        rad = lambda q: math.hypot(q[0] - ax, q[2] - az)
        mid = [rad(q) for q in p.mesh.pos if y0 + 0.3 < q[1] < y1 - 0.3]
        d = 2 * max(mid) if mid else 0.0
        lo, hi = co["range_shaft_diameter_m"]
        if not lo <= d <= hi:
            out.append(f"{p.name}: shaft {d:.3f} m across, outside {lo}-{hi} m")
        base = max(rad(q) for q in p.mesh.pos if q[1] < y0)
        if not (d / 2 < base <= p.meta["plinth_half"]):
            out.append(f"{p.name}: base {base:.3f} m is not between the shaft and the plinth")
        cap = max(rad(q) for q in p.mesh.pos if q[1] > y1)
        if cap >= p.meta["abacus_half"]:
            out.append(f"{p.name}: the capital ({cap:.3f} m) is wider than the abacus that caps it")
        if abs(max(q[1] for q in p.mesh.pos) - (p.meta["height"] - co["abacus_height_m"])) > 1e-6:
            out.append(f"{p.name}: the capital does not meet the abacus")
    return out


def rule_bounded(var):
    out = []
    f = var.meta.get("field")
    for p in var.pieces:
        if not p.meta.get("bounded"):
            continue
        for q in p.mesh.pos:
            if not (f["x"][0] - 1e-9 <= q[0] <= f["x"][1] + 1e-9 and f["y"][0] - 1e-9 <= q[1] <= f["y"][1] + 1e-9):
                out.append(f"{p.name}: reaches ({q[0]:.3f}, {q[1]:.3f}), outside its field less the margin")
                break
    return out


def rule_costs(var, v, data):
    cap = data["costs"]["max_triangles"][v["class"]]
    n = K.triangles(var)
    return [f"{n} triangles over the {v['class']} budget of {cap}"] if n > cap else []


def rule_data(data):
    out = []
    for name, part in data["parts"].items():
        if name.startswith("_"):
            continue
        parts = part.items() if name in ("profiles", "capital") else [(name, part)]
        for sub_name, pp in parts:
            if sub_name.startswith("_"):
                continue
            if pp.get("confidence") not in ("attested", "inferred", "reconstructed") or not pp.get("note"):
                out.append(f"part {sub_name}: no confidence and note")
    lo, hi = data["parts"]["voussoir"]["count_range"]
    for v in data["variants"]:
        if v.get("confidence") not in ("attested", "inferred", "reconstructed") or not v.get("note"):
            out.append(f"{v['id']}: no confidence and note")
        if v.get("motif") not in ("generic", "composed"):
            out.append(f"{v['id']}: motif {v.get('motif')!r} is neither generic nor composed")
        for k in ("voussoirs", "voussoirs_outer", "voussoirs_order"):
            if k in v and (v[k] % 2 == 0 or not lo <= v[k] <= hi):
                out.append(f"{v['id']}: {k} = {v[k]}, not an odd count in {lo}-{hi}")
    rules = {r["rule"] for r in data["restrictions"]}
    for need in ("never_replaces_landmark", "hero_exceeds_rowhouse"):
        if need not in rules:
            out.append(f"restriction {need} is not stated")
    return out


def rule_compare(built):
    out = []
    hero = [b for b in built if b.v["kind"] == "hero"]
    row = [b for b in built if b.v["kind"] == "rowhouse"]
    if not hero or not row:
        return ["the kit must carry both a hero entrance and a rowhouse surround"]
    h, r = hero[0], row[0]
    pieces = lambda b: sum(1 for p in b.pieces if p.role not in K.BOARD_ROLES)
    if h.meta["orders"] < 2:
        out.append(f"hero: {h.meta['orders']} order(s); a hero entrance steps back in at least two")
    if pieces(h) <= pieces(r):
        out.append(f"hero: {pieces(h)} pieces, no more than the rowhouse's {pieces(r)}")
    if K.relief_depth(h) <= K.relief_depth(r):
        out.append(f"hero: {K.relief_depth(h)} m of relief, no more than the rowhouse's {K.relief_depth(r)} m")
    if any(p.role == "carving" for p in r.pieces):
        out.append("rowhouse: a restrained surround carries carving")
    return out


def build_all(data):
    return [K.build_variant(v, data, index=i) for i, v in enumerate(data["variants"])]


def check(data, built=None, glb=True):
    fails = [f"data: {m}" for m in rule_data(data)]
    built = built or build_all(data)
    for var in built:
        v = var.v
        for name, msgs in (("seated", rule_seated(var)), ("rooted", rule_rooted(var)),
                           ("doubled", rule_doubled(var)), ("relief", rule_relief(var, data)),
                           ("arch", rule_arch(var, v)), ("colonnette", rule_colonnette(var, data)),
                           ("bounded", rule_bounded(var)), ("costs", rule_costs(var, v, data))):
            fails += [f"{v['id']} {name}: {m}" for m in msgs]
    fails += [f"compare: {m}" for m in rule_compare(built)]
    if glb:
        blob = K.to_glb(K.build_kit(data), data)
        spec = ROOT / data["specimen"]
        if not spec.exists() or spec.read_bytes() != blob:
            fails.append(f"specimen: {data['specimen']} is not the generator's bytes "
                         f"(run python3 generators/archetypes/k09_trim.py)")
    return fails, built


def self_test(data) -> int:
    def var_of(built, vid):
        return next(b for b in built if b.v["id"] == vid)

    def d_even(d):
        next(v for v in d["variants"] if v["id"] == "k09.trim.arch_ring_round")["voussoirs"] = 12

    def d_thin(d):
        d["parts"]["voussoir"]["proud_m"] = 0.004

    def d_leaves(d):
        d["parts"]["panel"]["leaf_width_m"] = 0.4

    def d_note(d):
        d["variants"][0]["note"] = ""

    def d_budget(d):
        d["costs"]["max_triangles"]["trim"] = 100

    def d_orders(d):
        next(v for v in d["variants"] if v["kind"] == "hero")["orders"] = 1

    def d_restrict(d):
        d["restrictions"] = [r for r in d["restrictions"] if r["rule"] != "never_replaces_landmark"]

    def g_float(built):     # lift the cornice hood's frieze block 5 mm off the wall
        p = next(p for p in var_of(built, "k09.trim.lintel_cornice_hood").pieces if p.name == "frieze block")
        p.mesh.pos = [(x, y, z + 0.005) for x, y, z in p.mesh.pos]

    def g_drift(built):     # a capital leaf blown 0.1 m off its bell
        p = next(p for p in var_of(built, "k09.trim.colonnette_foliate").pieces if p.name.endswith("leaf 1"))
        p.mesh.pos = [(x + 0.1, y, z + 0.1) for x, y, z in p.mesh.pos]

    def g_doubled(built):   # a stone given a back face on the wall
        var = var_of(built, "k09.trim.arch_ring_round")
        p = next(p for p in var.pieces if p.name == "voussoir 1")
        m = p.mesh
        back = [(x, y, 0.0) for x, y, z in m.pos[:len(m.pos) // 2] if abs(z - 0.035) < 1e-9]
        m.poly(back[:8], (0.0, 0.0, -1.0))

    def g_skew(built):      # a voussoir slid 3 mm along the wall: its joints no longer radial
        var = var_of(built, "k09.trim.arch_ring_segmental")
        p = next(p for p in var.pieces if p.name == "voussoir 2")
        p.mesh.pos = [(x + 0.003, y - 0.003, z) for x, y, z in p.mesh.pos]

    cases = [("an even voussoir count", d_even, None, "data"),
             ("a voussoir 4 mm proud", d_thin, None, "relief"),
             ("panel leaves too wide for the field", d_leaves, None, "bounded"),
             ("a variant with no note", d_note, None, "data"),
             ("a trim budget of 100 triangles", d_budget, None, "costs"),
             ("a hero entrance of one order", d_orders, None, "compare"),
             ("the landmark restriction dropped", d_restrict, None, "data"),
             ("a frieze block lifted 5 mm off the wall", None, g_float, "seated"),
             ("a capital leaf off its bell", None, g_drift, "rooted"),
             ("a stone with a back face on the wall", None, g_doubled, "doubled"),
             ("a voussoir slid off its joints", None, g_skew, "arch")]
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
    print(f"ok   K09 carved-trim kit: {len(built)} variants, {n} pieces seated or rooted, no doubled face, "
          f"relief, arches, colonnettes, bounds, hero/rowhouse comparison, budgets and the specimen hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
