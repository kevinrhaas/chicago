"""The K09 carved-trim kit: arch rings, mouldings, hoods, colonnettes, tracery and
foliate relief, every piece real relief geometry written straight to glTF.

TICKET T-2309 (piece 1 of T-1851, K09). The kit's sizes are data in
`data/components/prairie_1904/k09_trim.json`; this module reads them and builds each
variant on a specimen wall the way T-2310 will build them on a house:

  arch ring      dressed voussoirs cut on joints radial to their own arc's centre,
                 an odd count so one stone stands at the crown, a keystone where the
                 variant asks for one
  moulding       an open section swept along a path (an arch, a jamb-and-head, a
                 block's three faces), mitred at its corners, returned to the wall
  hood           a frieze block, a returned cornice and two scrolled consoles; or a
                 Gothic label with crockets along its back and a finial at its apex
  colonnette     plinth, turned base, shaft with entasis, a Tuscan or a foliate bell
                 capital, a square abacus
  tracery        a pointed slab pierced by two lancets and a quatrefoil
  foliate panel  a tablet with a sunk field, a scrolling stem and seeded leaves
  surrounds      a hero Romanesque entrance (three stepped orders, four foliate
                 colonnettes, a ring on every order, a label over all) and a
                 restrained rowhouse door (architrave, frieze, cornice, consoles)

Every piece RESTS on what carries it. A piece built open (a voussoir has no back, a
moulding's section is open on its seat side, a leaf on a field is a shell) leaves its
open edges lying on another surface, and a piece built closed (a capital leaf, a
crocket, a finial) passes through its host's surface. Nothing lays a face on another
face. `tools/check_trim_kit.py` measures all of it on the built geometry.

WHY PURE PYTHON: the reasons k01_frontage.py and k06_windows.py give. The gate
measures vertices, and they are easiest to hold when this module writes them.

    python3 generators/archetypes/k09_trim.py           write the specimen GLB
    python3 generators/archetypes/k09_trim.py --check   refuse if it is stale
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archetypes.k01_frontage import _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k09_trim.json"
GENERATOR = "chicago-4d generators/archetypes/k09_trim.py (K09, T-2309)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]

X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)

# Role -> material, in a fixed order so the file is the same bytes every run.
ROLE_MATERIAL = {"wall": "masonry", "trim": "dressed_stone", "carving": "carved_stone",
                 "backing": "backing", "ground": "ground"}
BOARD_ROLES = ("wall", "backing", "ground")
MATERIALS = {
    "masonry": {"color": (0.55, 0.36, 0.28), "roughness": 0.92},
    "dressed_stone": {"color": (0.74, 0.69, 0.60), "roughness": 0.85},
    "carved_stone": {"color": (0.70, 0.65, 0.56), "roughness": 0.88},
    "backing": {"color": (0.032, 0.028, 0.025), "roughness": 1.0},
    "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0},
}


def seed_of(component_id: str, index: int, structure_id: str = "k09_carved_trim_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


# -- 2D polygons ------------------------------------------------------------------------------

def area2(poly) -> float:
    a = 0.0
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        a += p[0] * q[1] - q[0] * p[1]
    return a / 2


def _cr(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _in_tri(p, a, b, c) -> bool:
    return _cr(a, b, p) >= -1e-14 and _cr(b, c, p) >= -1e-14 and _cr(c, a, p) >= -1e-14


def _cross_seg(p1, p2, q1, q2) -> bool:
    """Proper intersection of two segments (touching at an end does not count)."""
    d1, d2 = _cr(q1, q2, p1), _cr(q1, q2, p2)
    d3, d4 = _cr(p1, p2, q1), _cr(p1, p2, q2)
    return ((d1 > 1e-14 and d2 < -1e-14) or (d1 < -1e-14 and d2 > 1e-14)) and \
           ((d3 > 1e-14 and d4 < -1e-14) or (d3 < -1e-14 and d4 > 1e-14))


def triangulate(outer, holes=()):
    """Ear clipping, holes bridged in from their right-most vertex. Returns index
    triples into outer + every hole, in that order, wound counter-clockwise."""
    pts = list(outer) + [p for h in holes for p in h]
    ring = list(range(len(outer)))
    if area2(outer) < 0:
        ring.reverse()
    rings, off = [], len(outer)
    for h in holes:
        r = list(range(off, off + len(h)))
        off += len(h)
        if area2(h) > 0:
            r.reverse()
        rings.append(r)
    edges = lambda r: [(r[i], r[(i + 1) % len(r)]) for i in range(len(r))]
    rings.sort(key=lambda r: -max(pts[i][0] for i in r))
    for n, hr in enumerate(rings):
        k = max(range(len(hr)), key=lambda j: (pts[hr[j]][0], pts[hr[j]][1]))
        m = pts[hr[k]]
        blockers = edges(ring) + [e for r in rings[n:] for e in edges(r)]
        best = None
        for j in sorted(range(len(ring)), key=lambda j: (pts[ring[j]][0] - m[0]) ** 2 + (pts[ring[j]][1] - m[1]) ** 2):
            v = pts[ring[j]]
            if not any(_cross_seg(m, v, pts[a], pts[b]) for a, b in blockers
                       if pts[a] != m and pts[b] != m and pts[a] != v and pts[b] != v):
                best = j
                break
        if best is None:
            raise ValueError("no bridge from a hole to its outline")
        ring = ring[:best + 1] + hr[k:] + hr[:k + 1] + ring[best:]
    tris, V = [], ring[:]
    while len(V) > 3:
        n, cut = len(V), False
        for i in range(n):
            a, b, c = V[i - 1], V[i], V[(i + 1) % n]
            pa, pb, pc = pts[a], pts[b], pts[c]
            if _cr(pa, pb, pc) <= 1e-12:
                continue
            if any(_in_tri(pts[w], pa, pb, pc) for w in V
                   if w not in (a, b, c) and pts[w] not in (pa, pb, pc)):
                continue
            tris.append((a, b, c))
            del V[i]
            cut = True
            break
        if not cut:      # only collinear or doubled vertices remain at a bend: drop one
            for i in range(n):
                if abs(_cr(pts[V[i - 1]], pts[V[i]], pts[V[(i + 1) % n]])) <= 1e-12:
                    del V[i]
                    cut = True
                    break
        if not cut:
            raise ValueError("triangulation failed")
    if len(V) == 3 and _cr(pts[V[0]], pts[V[1]], pts[V[2]]) > 1e-12:
        tris.append(tuple(V))
    return tris


# -- meshes -----------------------------------------------------------------------------------

def _newell(pts):
    n = (0.0, 0.0, 0.0)
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
    return n


def _basis(n):
    au = _cross(Y, n)
    au = _unit(au) if _dot(au, au) > 1e-9 else X
    return au, _cross(n, au)


class Mesh:
    """One piece's triangles: shared vertices per polygon, its own normals, metric UVs
    (TEXCOORD_0 is surface metres, K01 scale_uv with an untextured 1 m tile)."""

    def __init__(self):
        self.pos, self.nrm, self.uv, self.conf, self.idx = [], [], [], [], []

    def _vert(self, p, n, au, av):
        self.pos.append(p)
        self.nrm.append(n)
        self.uv.append((_dot(p, au), -_dot(p, av)))
        self.conf.append(RECONSTRUCTED)
        return len(self.pos) - 1

    def poly(self, outer, hint, holes=()):
        """A planar polygon (holes allowed), flat-shaded, facing `hint`."""
        n = _newell(outer)
        if _dot(n, n) < 1e-20:
            return
        n = _unit(n)
        if _dot(n, hint) < 0:
            n = _mul(n, -1)
        au, av = _basis(n)
        flat = lambda ps: [(_dot(p, au), _dot(p, av)) for p in ps]
        allp = list(outer) + [p for h in holes for p in h]
        tris = triangulate(flat(outer), [flat(h) for h in holes])
        base = len(self.pos)
        for p in allp:
            self._vert(p, n, au, av)
        for a, b, c in tris:      # counter-clockwise in (au, av) is facing n
            self.idx += [base + a, base + b, base + c]

    def quad(self, pts, nrms):
        """Four corners with their own normals (smooth along a sweep or a lathe); each
        triangle wound to face its corners' normals, a degenerate one dropped."""
        sn = _add(_add(nrms[0], nrms[1]), _add(nrms[2], nrms[3]))
        au, av = _basis(_unit(sn) if _dot(sn, sn) > 1e-12 else Z)
        ids = [self._vert(p, n, au, av) for p, n in zip(pts, nrms)]
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            g = _cross(_sub(pts[b], pts[a]), _sub(pts[c], pts[a]))
            if _dot(g, g) < 1e-18:
                continue
            if _dot(g, _add(_add(nrms[a], nrms[b]), nrms[c])) < 0:
                b, c = c, b
            self.idx += [ids[a], ids[b], ids[c]]

    def triangles(self) -> int:
        return len(self.idx) // 3


class Piece:
    """One stone, moulding, leaf or board surface. `rests` is how it is held: `open`
    (its open edges lie on another surface), `rooted` (a closed piece passing through
    its `host`'s surface) or `board` (the specimen wall itself)."""

    def __init__(self, name, role, rests, host=None, **meta):
        self.name, self.role, self.rests, self.host, self.meta = name, role, rests, host, meta
        self.mesh = Mesh()


# -- builders ---------------------------------------------------------------------------------

def prism(m: Mesh, poly2, z0, z1, back=False, open_edges=()):
    """`poly2` (x, y) in the wall plane, from depth z0 to z1 (z1 > z0, toward the
    viewer): its front, its sides (all but `open_edges`, by index), its back if asked."""
    if area2(poly2) < 0:
        poly2 = list(reversed(poly2))
        k = len(poly2)
        open_edges = {(k - 2 - i) % k for i in open_edges}
    m.poly([(x, y, z1) for x, y in poly2], Z)
    if back:
        m.poly([(x, y, z0) for x, y in poly2], _mul(Z, -1))
    for i in range(len(poly2)):
        if i in open_edges:
            continue
        a, b = poly2[i], poly2[(i + 1) % len(poly2)]
        out = (b[1] - a[1], -(b[0] - a[0]), 0.0)
        m.poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], out)


def box(m: Mesh, x0, x1, y0, y1, z0, z1, skip=()):
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    faces = {
        "front": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "back": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        "left": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        "right": [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
        "top": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "bottom": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
    }
    for k, f in faces.items():
        if k not in skip:
            fc = tuple(sum(p[i] for p in f) / 4 for i in range(3))
            m.poly(f, _sub(fc, c))


def tube(m: Mesh, outline2, z0, z1, inward=True, closed=True):
    """The sides of an outline carried from depth z0 to z1, facing its inside."""
    n = len(outline2)
    s = 1.0 if area2(outline2) > 0 else -1.0
    for i in range(n if closed else n - 1):
        a, b = outline2[i], outline2[(i + 1) % n]
        out = (s * (b[1] - a[1]), -s * (b[0] - a[0]), 0.0)
        m.poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
               _mul(out, -1) if inward else out)


def sweep(m: Mesh, path, U, profile, side=1.0, smooth=True, caps=(False, False)):
    """An open section `profile` ([n, u] pairs) swept along `path`, a polyline lying in
    a plane whose normal is U: n runs along the in-plane normal (cross(T, U) * side),
    u along U. Mitred at every vertex. Open on its seat; capped only where asked."""
    segN = []
    for j in range(len(path) - 1):
        T = _unit(_sub(path[j + 1], path[j]))
        segN.append(_mul(_unit(_cross(T, U)), side))
    vN, vS = [], []
    for i in range(len(path)):
        if i == 0 or i == len(path) - 1:
            vN.append(segN[0 if i == 0 else -1])
            vS.append(1.0)
        else:
            N = _unit(_add(segN[i - 1], segN[i]))
            vN.append(N)
            vS.append(1.0 / max(0.2, _dot(N, segN[i - 1])))
    rings = [[_add(_add(path[i], _mul(vN[i], n * vS[i])), _mul(U, u)) for n, u in profile]
             for i in range(len(path))]
    sgn = 1.0 if area2(profile) > 0 else -1.0
    for k in range(len(profile) - 1):
        en, eu = profile[k + 1][0] - profile[k][0], profile[k + 1][1] - profile[k][1]
        ln = math.hypot(en, eu) or 1.0
        on, ou = sgn * eu / ln, -sgn * en / ln
        for i in range(len(path) - 1):
            Na, Nb = (vN[i], vN[i + 1]) if smooth else (segN[i], segN[i])
            na = _unit(_add(_mul(Na, on), _mul(U, ou)))
            nb = _unit(_add(_mul(Nb, on), _mul(U, ou)))
            m.quad([rings[i][k], rings[i + 1][k], rings[i + 1][k + 1], rings[i][k + 1]], [na, nb, nb, na])
    for end, cap in zip((0, -1), caps):
        if cap:
            T = _unit(_sub(path[1], path[0])) if end == 0 else _unit(_sub(path[-1], path[-2]))
            m.poly(rings[end], _mul(T, -1) if end == 0 else T)
    return rings


def lathe(m: Mesh, axis, profile, segs):
    """A surface of revolution about the vertical line through `axis` (x, z); profile
    [r, y] runs upward. A point at r = 0 closes the surface there."""
    ax, az = axis
    ang = [2 * math.pi * s / segs for s in range(segs + 1)]
    for k in range(len(profile) - 1):
        (r0, y0), (r1, y1) = profile[k], profile[k + 1]
        dr, dy = r1 - r0, y1 - y0
        ln = math.hypot(dr, dy) or 1.0
        on, oy = dy / ln, -dr / ln
        for s in range(segs):
            a, b = ang[s], ang[s + 1]
            P = lambda r, y, t: (ax + r * math.cos(t), y, az + r * math.sin(t))
            N = lambda t: _unit((on * math.cos(t), oy, on * math.sin(t)))
            m.quad([P(r0, y0, a), P(r0, y0, b), P(r1, y1, b), P(r1, y1, a)], [N(a), N(b), N(b), N(a)])


def leaf(m: Mesh, B, D, Nrm, length, width, relief, curl=0.0, lobes=3, lobe_depth=0.28,
         groove=0.35, nt=8, nu=6, thickness=None, rng=None):
    """The kit's leaf. Midrib from B along D, curling toward Nrm. A shell (thickness
    None) rises from nothing at every edge, so all its edges lie on the surface B sits
    on; a closed leaf has an underside `thickness` below and a capped base."""
    S = _unit(_cross(Nrm, D))
    jit = (lambda: 1.0 + 0.12 * (rng.random() - 0.5)) if rng else (lambda: 1.0)
    lob = [jit() for _ in range(lobes + 1)]

    def frame(t):
        mid = _add(B, _add(_mul(D, length * t), _mul(Nrm, curl * length * t * t)))
        T = _unit(_add(_mul(D, length), _mul(Nrm, 2 * curl * length * t)))
        return mid, _unit(_cross(T, S))

    def w(t):
        env = math.sin(math.pi * min(1.0, max(0.0, t)) ** 0.85) ** 0.7
        if thickness is not None and t < 0.5:
            env = max(env, 0.3)
        k = min(lobes, int(t * lobes))
        return width / 2 * env * (1 - lobe_depth + lobe_depth * abs(math.cos(lobes * math.pi * t)) * lob[k])

    def h(t, u):
        env = math.sin(math.pi * t) ** 0.5 if thickness is None else \
            (0.35 + 0.65 * math.sin(math.pi * min(t, 0.5))) * (1 - t ** 6)
        return relief * env * (1 - u * u) * (1 - groove * math.exp(-(u / 0.18) ** 2))

    us = [-1 + 2 * j / nu for j in range(nu + 1)]
    peak = max((1 - u * u) * (1 - groove * math.exp(-(u / 0.18) ** 2)) for u in us)
    relief = relief / peak          # the crown of the leaf stands `relief` high, as built
    t0 = 0.0
    top = []
    for i in range(nt + 1):
        t = t0 + (1 - t0) * i / nt
        mid, nn = frame(t)
        row = []
        for j in range(nu + 1):
            u = -1 + 2 * j / nu
            row.append(_add(_add(mid, _mul(S, u * w(t))), _mul(nn, h(t, u))))
        top.append(row)

    def surf(grid, flip):
        for i in range(nt):
            for j in range(nu):
                q = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
                g = _newell(q)
                if _dot(g, g) < 1e-20:
                    continue
                n = _unit(g)
                n = _mul(n, -1) if flip else n
                ref = frame((i + 0.5) / nt)[1]
                if (_dot(n, ref) < 0) != flip:
                    n = _mul(n, -1)
                m.quad(q, [n, n, n, n])

    if thickness is None:
        surf(top, False)
        return
    bot = []
    for i in range(nt + 1):
        t = i / nt
        mid, nn = frame(t)
        bot.append([_sub(p, _mul(nn, thickness * (1 - t) ** 0.6)) for p in top[i]])
    surf(top, False)
    surf(bot, True)
    for j in (0, nu):          # the two edges
        for i in range(nt):
            q = [top[i][j], top[i + 1][j], bot[i + 1][j], bot[i][j]]
            g = _newell(q)
            if _dot(g, g) < 1e-20:
                continue
            side = _mul(S, -1 if j == 0 else 1)
            m.poly(q, side)
    m.poly(top[0] + list(reversed(bot[0])), _mul(D, -1))      # the base, closed


class Arch:
    """An arch over the span s0..s1 springing at `spring`. t runs 0 (right spring) to 1
    (left spring); `off` is outward from the curve, along its radius."""

    def __init__(self, kind, cx, span, spring, rise_over_span=0.125):
        self.kind, self.cx, self.span, self.spring = kind, cx, span, spring
        half = span / 2
        self.s0, self.s1 = cx - half, cx + half
        if kind == "round":
            self.R, self.cy, self.rise = half, spring, half
            self.th = (0.0, math.pi)
        elif kind == "segmental":
            self.rise = span * rise_over_span
            self.R = (half * half + self.rise * self.rise) / (2 * self.rise)
            self.cy = spring - (self.R - self.rise)
            a = math.asin(half / self.R)
            self.th = (math.pi / 2 - a, math.pi / 2 + a)
        elif kind == "pointed":
            self.R, self.rise = span, span * math.sqrt(3) / 2
        else:
            raise ValueError(kind)

    def centre(self, t):
        if self.kind != "pointed":
            return (self.cx, self.cy)
        return (self.s0, self.spring) if t <= 0.5 else (self.s1, self.spring)

    def angle(self, t):
        if self.kind != "pointed":
            return self.th[0] + (self.th[1] - self.th[0]) * t
        return math.radians(60) * (2 * t) if t <= 0.5 else math.radians(120) + math.radians(60) * (2 * t - 1)

    def pt(self, t, off=0.0):
        c, a = self.centre(t), self.angle(t)
        return (c[0] + (self.R + off) * math.cos(a), c[1] + (self.R + off) * math.sin(a))

    def radial(self, t):
        a = self.angle(t)
        return (math.cos(a), math.sin(a))

    def apex(self):
        return self.spring + self.rise

    def samples(self, n):
        ts = [i / n for i in range(n + 1)]
        if self.kind == "pointed" and 0.5 not in ts:
            ts = sorted(set(ts) | {0.5})
        return ts

    def length(self, off=0.0):
        ts = self.samples(64)
        return sum(math.dist(self.pt(a, off), self.pt(b, off)) for a, b in zip(ts, ts[1:]))


def doorway(arch_or_none, s0, s1, top, n=24):
    """A doorway outline from the ground: up the left jamb, over the head, down the
    right jamb (open along the floor). As (x, y) from (s0, 0) to (s1, 0)."""
    if arch_or_none is None:
        return [(s0, 0.0), (s0, top), (s1, top), (s1, 0.0)]
    a = arch_or_none
    head = [a.pt(t) for t in reversed(a.samples(n))]
    return [(s0, 0.0)] + head + [(s1, 0.0)]


def window(arch, sill, n=24):
    """A closed window outline: sill, jambs, head (counter-clockwise)."""
    head = [arch.pt(t) for t in arch.samples(n)]
    return [(arch.s0, sill), (arch.s1, sill)] + head


class Variant:
    def __init__(self, v, data, origin=(0.0, 0.0, 0.0), index=0):
        self.v, self.data, self.O = v, data, origin
        self.pieces: list[Piece] = []
        self.seed = seed_of(v["id"], index)
        self.rng = random.Random(self.seed)
        self.meta: dict = {}

    def piece(self, name, role, rests, host=None, **meta):
        p = Piece(name, role, rests, host, **meta)
        self.pieces.append(p)
        return p

    # the specimen wall -----------------------------------------------------------------
    def board(self, x_lo, x_hi, y_hi, door=None, hole=None, recess=0.3, thickness=0.5, floor=None):
        """The wall the trim stands on: its face (with a doorway notch or a window hole),
        the opening's reveal carried back `recess` to a dark back, its returns, the
        ground in front of it."""
        w = self.piece("wall", "wall", "board")
        if door is not None:
            face = [(x_lo, 0.0)] + door + [(x_hi, 0.0), (x_hi, y_hi), (x_lo, y_hi)]
            w.mesh.poly([(x, y, 0.0) for x, y in face], Z)
            if recess:
                tube(w.mesh, door, 0.0, -recess, closed=False)
                bk = self.piece("opening back", "backing", "board")
                bk.mesh.poly([(x, y, -recess) for x, y in door], Z)
                fl = self.piece("threshold", "ground", "board")
                xs = [q[0] for q in door]
                fl.mesh.poly([(min(xs), 0.0, 0.0), (max(xs), 0.0, 0.0), (max(xs), 0.0, -recess),
                              (min(xs), 0.0, -recess)], Y)
        elif hole is not None:
            rect = [(x_lo, 0.0), (x_hi, 0.0), (x_hi, y_hi), (x_lo, y_hi)]
            w.mesh.poly([(x, y, 0.0) for x, y in rect], Z, holes=[[(x, y, 0.0) for x, y in hole]])
        else:
            w.mesh.poly([(x_lo, 0.0, 0.0), (x_hi, 0.0, 0.0), (x_hi, y_hi, 0.0), (x_lo, y_hi, 0.0)], Z)
        for x, hx in ((x_lo, -1.0), (x_hi, 1.0)):
            w.mesh.poly([(x, 0.0, 0.0), (x, y_hi, 0.0), (x, y_hi, -thickness), (x, 0.0, -thickness)], (hx, 0, 0))
        w.mesh.poly([(x_lo, y_hi, 0.0), (x_hi, y_hi, 0.0), (x_hi, y_hi, -thickness), (x_lo, y_hi, -thickness)], Y)
        g = self.piece("ground", "ground", "board")
        g.mesh.poly([(x_lo, 0.0, 0.0), (x_hi, 0.0, 0.0), (x_hi, 0.0, 1.0), (x_lo, 0.0, 1.0)], Y)
        self.meta["panel"] = {"x": [x_lo, x_hi], "y": [0.0, y_hi]}

    # parts -----------------------------------------------------------------------------
    def ring(self, arch, inner_off, depth, count, proud, z0=0.0, keystone=None, name="voussoir"):
        """`count` voussoirs on the face at depth z0, from `inner_off` outside the arch
        curve to `inner_off + depth`, joints radial, the crown stone a keystone if given."""
        P = self.data["parts"]["voussoir"]
        weights = [1.0] * count
        if keystone:
            weights[count // 2] = keystone["width_factor"]
        tot = sum(weights)
        edges = [0.0]
        for wt in weights:
            edges.append(edges[-1] + wt / tot)
        L = arch.length(inner_off + depth / 2)
        g = P["joint_m"] / 2 / L
        stones = []
        for i in range(count):
            ta, tb = edges[i] + (g if i else 0.0), edges[i + 1] - (g if i < count - 1 else 0.0)
            ts = [ta + (tb - ta) * k / 6 for k in range(7)]
            if arch.kind == "pointed" and ta < 0.5 < tb:
                ts = sorted(set(ts) | {0.5})
            key = keystone and i == count // 2
            top = depth + (keystone["rise_above_m"] if key else 0.0)
            pr = proud + (keystone["proud_extra_m"] if key else 0.0)
            intr = [arch.pt(t, inner_off) for t in ts]
            if key:      # its sides run on out along their radii to one level top
                yt = max(arch.pt(tb, inner_off + top)[1], arch.pt(ta, inner_off + top)[1])
                ext = []
                for t in (tb, ta):
                    b0, rd = arch.pt(t, inner_off), arch.radial(t)
                    s_ = (yt - b0[1]) / rd[1]
                    ext.append((b0[0] + rd[0] * s_, yt))
            else:
                ext = [arch.pt(t, inner_off + top) for t in reversed(ts)]
            poly = intr + ext
            p = self.piece(f"{name} {i + 1}", "trim", "open", course=name, index=i,
                           relief={"plane_z": z0, "proud_m": round(pr, 6)},
                           arch={"kind": arch.kind, "cx": arch.cx, "span": arch.span, "spring": arch.spring,
                                 "R": arch.R, "inner_off": inner_off, "depth": top, "keystone": bool(key)})
            prism(p.mesh, poly, z0, z0 + pr)
            stones.append(p)
        return stones

    def label(self, arch, off, stop, crockets=False):
        """A label mould swept round the arch at `off` outside it, returned level at
        both springs by `stop` and capped there; crockets and a finial if asked."""
        prof = self.data["parts"]["profiles"]["label"]["points"]
        n_out = max(n for n, _ in prof)
        L = arch.length(off)
        # no sample nearer a spring than the mould is wide: a short segment beside the
        # stop's mitre would fold the section back over itself
        ts = [t for t in arch.samples(32) if t in (0.0, 1.0) or min(t, 1 - t) * L > 1.2 * n_out]
        path = [(arch.s1 + off + stop, arch.spring)] + [arch.pt(t, off) for t in ts] + [(arch.s0 - off - stop, arch.spring)]
        path3 = [(x, y, 0.0) for x, y in path]
        p = self.piece("label", "trim", "open", relief={"plane_z": 0.0, "proud_m": max(u for _, u in prof)})
        sweep(p.mesh, path3, Z, prof, side=1.0, caps=(True, True))
        if not crockets:
            return p
        C = self.data["parts"]["crocket"]
        Lp = self.data["parts"]["leaf"]
        L = arch.length(off + n_out)
        k = 0
        s = 0.28
        while s < L / 2 - 0.12:
            for t in (s / L, 1 - s / L):
                b = arch.pt(t, off + n_out - 0.012)
                rad = arch.radial(t)
                tang = (-rad[1], rad[0]) if t < 0.5 else (rad[1], -rad[0])   # toward the apex
                D = _unit((tang[0] + 0.35 * rad[0], tang[1] + 0.35 * rad[1], 0.0))
                Nl = _unit((rad[0], rad[1], 0.0))
                Nl = _unit(_sub(Nl, _mul(D, _dot(Nl, D))))
                c = self.piece(f"crocket {k + 1}", "carving", "rooted", host="label")
                leaf(c.mesh, (b[0], b[1], 0.042), D, Nl, C["length_m"], C["width_m"], C["thickness_m"] * 0.8,
                     curl=C["curl"], lobes=Lp["lobes"], lobe_depth=Lp["lobe_depth"], groove=Lp["midrib_groove"],
                     nt=6, nu=4, thickness=C["thickness_m"], rng=self.rng)
                k += 1
            s += C["spacing_m"]
        apex = arch.pt(0.5, off)
        y0 = apex[1] + 0.03
        f = self.piece("finial", "carving", "rooted", host="label")
        lathe(f.mesh, (arch.cx, 0.04), [(0.0, y0), (0.022, y0 + 0.012), (0.03, y0 + 0.05), (0.016, y0 + 0.085),
                                         (0.034, y0 + 0.12), (0.03, y0 + 0.16), (0.012, y0 + 0.185), (0.0, y0 + 0.19)], 12)
        for q in range(4):
            a = math.pi / 4 + q * math.pi / 2
            Nl = (math.cos(a), 0.0, math.sin(a))
            c = self.piece(f"finial leaf {q + 1}", "carving", "rooted", host="finial")
            leaf(c.mesh, (arch.cx + 0.02 * Nl[0], y0 + 0.07, 0.04 + 0.02 * Nl[2]), Y, Nl, 0.07, 0.03,
                 C["thickness_m"] * 0.8, curl=C["curl"], lobes=Lp["lobes"], lobe_depth=Lp["lobe_depth"],
                 groove=Lp["midrib_groove"], nt=6, nu=4, thickness=C["thickness_m"], rng=self.rng)
        return p

    def cornice_hood(self, x_l, x_r, y_b):
        """A frieze block from y_b, a cornice returned round its three faces, and a
        scrolled console under each end."""
        P = self.data["parts"]
        hb, co, cn = P["hood_block"], P["console"], P["profiles"]["cornice"]["points"]
        H, D = hb["height_m"], hb["proud_m"]
        blk = self.piece("frieze block", "trim", "open", relief={"plane_z": 0.0, "proud_m": D})
        box(blk.mesh, x_l, x_r, y_b, y_b + H, 0.0, D, skip=("back",))
        ch = max(u for _, u in cn)
        yc = y_b + H - ch
        cor = self.piece("cornice", "trim", "open", relief={"plane_z": 0.0, "proud_m": D + max(n for n, _ in cn)})
        sweep(cor.mesh, [(x_l, yc, 0.0), (x_l, yc, D), (x_r, yc, D), (x_r, yc, 0.0)], Y, cn, side=1.0, smooth=False)
        h, pj, wd = co["height_m"], co["projection_m"], co["width_m"]
        ss = [i / 14 for i in range(15)]
        front = [(pj * (1 - 0.72 * (3 * s * s - 2 * s ** 3)), y_b - h * s) for s in ss]
        outline = [(0.0, y_b)] + front + [(0.0, y_b - h)]
        for i, (xa, xb) in enumerate(((x_l, x_l + wd), (x_r - wd, x_r))):
            c = self.piece(f"console {i + 1}", "trim", "open", relief={"plane_z": 0.0, "proud_m": pj})
            # the outline in (z, y), extruded along x; open on the wall (z = 0) and under the block (y = y_b)
            for x, hx in ((xa, -1.0), (xb, 1.0)):
                c.mesh.poly([(x, y, z) for z, y in outline], (hx, 0.0, 0.0))
            for k in range(len(outline)):
                a, b = outline[k], outline[(k + 1) % len(outline)]
                if (a[0] == 0.0 and b[0] == 0.0) or (a[1] == y_b and b[1] == y_b):
                    continue
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                out = (0.0, b[0] - a[0], -(b[1] - a[1]))
                if _dot(out, (0.0, mid[1] - (y_b - h / 2), mid[0] - pj / 3)) < 0:
                    out = _mul(out, -1)
                c.mesh.poly([(xa, a[1], a[0]), (xb, a[1], a[0]), (xb, b[1], b[0]), (xa, b[1], b[0])], out)
        return y_b + H

    def colonnette(self, cx, cz, height, order, name="colonnette", abacus_m=None):
        P = self.data["parts"]
        co, cap = P["colonnette"], P["capital"][order]
        rs = co["shaft_diameter_m"] / 2
        p2, ph, a2, ah = co["plinth_m"] / 2, co["plinth_height_m"], (abacus_m or co["abacus_m"]) / 2, co["abacus_height_m"]
        bh, chh = co["base_height_m"], co["capital_height_m"]
        pl = self.piece(f"{name} plinth", "trim", "open")
        box(pl.mesh, cx - p2, cx + p2, 0.0, ph, cz - p2, cz + p2, skip=("bottom",))
        y_ab = height - ah
        y_cap = y_ab - chh
        y_shaft = ph + bh
        base = [(1.32, 0.0), (1.36, 0.12), (1.3, 0.3), (1.12, 0.38), (1.1, 0.5), (1.2, 0.62), (1.18, 0.78),
                (1.06, 0.88), (1.0, 1.0)]
        prof = [(rs * r, ph + bh * y) for r, y in base]
        n_sh = 8
        for i in range(1, n_sh):
            f = i / n_sh
            prof.append((rs + co["entasis_m"] * math.sin(math.pi * f) - 0.08 * rs * f, y_shaft + (y_cap - y_shaft) * f))
        r_top = rs * 0.92
        prof += [(r_top * r, y_cap + chh * y) for r, y in cap["profile"]]
        sh = self.piece(f"{name} shaft", "trim", "open", shaft={"axis": [cx, cz], "r": rs, "y": [y_shaft, y_cap]},
                        plinth_half=p2, abacus_half=a2, height=height)
        lathe(sh.mesh, (cx, cz), prof, co["segments"])
        ab = self.piece(f"{name} abacus", "trim", "open")
        box(ab.mesh, cx - a2, cx + a2, y_ab, height, cz - a2, cz + a2)
        if order == "foliate":
            Lp = P["leaf"]
            prf = cap["profile"]
            yb = y_cap + chh * prf[3][1] + 0.004
            rb = r_top * prf[3][0] - 0.004
            rt = r_top * prf[-2][0]
            yt = y_cap + chh * prf[-2][1]
            for q in range(cap["leaves"]):
                a = 2 * math.pi * (q + 0.5) / cap["leaves"]
                Rd = (math.cos(a), 0.0, math.sin(a))
                D = _unit((Rd[0] * (rt - rb), yt - yb, Rd[2] * (rt - rb)))
                Nl = _unit(_sub(Rd, _mul(D, _dot(Rd, D))))
                lf = self.piece(f"{name} leaf {q + 1}", "carving", "rooted", host=f"{name} shaft")
                leaf(lf.mesh, (cx + rb * Rd[0], yb, cz + rb * Rd[2]), D, Nl,
                     cap["leaf_length_fraction"] * chh, cap["leaf_width_m"], cap["leaf_relief_m"],
                     curl=cap["leaf_curl"], lobes=Lp["lobes"], lobe_depth=Lp["lobe_depth"],
                     groove=Lp["midrib_groove"], nt=Lp["steps_t"], nu=Lp["steps_u"],
                     thickness=cap["leaf_thickness_m"], rng=self.rng)

    # variants --------------------------------------------------------------------------
    def build(self):
        getattr(self, "_" + self.v["kind"])()
        return self

    def _arch(self, W, spring, kind=None):
        v = self.v
        return Arch(kind or v["head"], 0.0, W, spring, v.get("rise_over_span", 0.125))

    def _arch_ring(self):
        v, P = self.v, self.data["parts"]
        vs = P["voussoir"]
        a = self._arch(v["clear_width_m"], v["spring_m"])
        R = vs["ring_depth_m"]
        hw = v["clear_width_m"] / 2 + R + 0.6
        self.board(-hw, hw, a.apex() + R + 0.6, door=doorway(a, a.s0, a.s1, None), recess=P["opening"]["recess_m"])
        self.ring(a, 0.0, R, v["voussoirs"], vs["proud_m"], keystone=P["keystone"] if v.get("keystone") else None)

    def _pointed_hood(self):
        v, P = self.v, self.data["parts"]
        a = self._arch(v["clear_width_m"], v["spring_m"])
        hw = v["clear_width_m"] / 2 + 0.06 + v["label_stop_m"] + 0.7
        self.board(-hw, hw, a.apex() + 0.7, door=doorway(a, a.s0, a.s1, None), recess=P["opening"]["recess_m"])
        self.label(a, 0.06, v["label_stop_m"], crockets=True)

    def _cornice_hood(self):
        v, P = self.v, self.data["parts"]
        W, H = v["clear_width_m"], v["clear_height_m"]
        ov = P["hood_block"]["overhang_m"]
        hw = W / 2 + ov + 0.7
        self.board(-hw, hw, H + 1.1, door=doorway(None, -W / 2, W / 2, H), recess=P["opening"]["recess_m"])
        self.cornice_hood(-W / 2 - ov, W / 2 + ov, H)

    def _colonnette(self):
        v, P = self.v, self.data["parts"]
        co = P["colonnette"]
        self.board(-0.7, 0.7, v["height_m"] + 0.5)
        self.colonnette(0.0, co["abacus_m"] / 2 + 0.03, v["height_m"], v["order"])

    def _tracery(self):
        v, P = self.v, self.data["parts"]
        tr = P["tracery"]
        W, sill, spring = v["clear_width_m"], v["sill_m"], v["spring_m"]
        a = self._arch(W, spring)
        outline = window(a, sill, 24)
        hw = W / 2 + 0.8
        self.board(-hw, hw, a.apex() + 0.7, hole=outline)
        w = self.pieces[0]
        sb, dp = tr["set_back_m"], tr["depth_m"]
        tube(w.mesh, outline, 0.0, -sb)
        mg, mu = tr["margin_m"], tr["mullion_m"]
        lw = (W - 2 * mg - mu) / 2
        lights = []
        for cx in (-(mu + lw) / 2, (mu + lw) / 2):
            la = Arch("pointed", cx, lw, spring)
            lights.append(window(la, sill + mg, 12))
        la_apex = spring + lw * math.sqrt(3) / 2
        inner = Arch("pointed", 0.0, W - 2 * mg, spring)
        cy, Rq = None, None
        top = inner.apex()
        for k in range(200):        # the largest quatrefoil that clears the lancets and the head
            r = (top - la_apex - mg) / 2 * (1 - k / 200)
            c = la_apex + mg + r
            pts = [(r * math.cos(2 * math.pi * i / 24), c + r * math.sin(2 * math.pi * i / 24)) for i in range(24)]
            if all(_inside_arch(inner, p) for p in pts):
                cy, Rq = c, r
                break
        rl = Rq * 0.48
        d = Rq - rl
        s_out = d / math.sqrt(2) + math.sqrt(rl * rl - d * d / 2)
        foil = []
        for q in range(tr["foils"]):
            ca = q * math.pi / 2
            ctr = (d * math.cos(ca), cy + d * math.sin(ca))
            p_from = (s_out * math.cos(ca - math.pi / 4), cy + s_out * math.sin(ca - math.pi / 4))
            p_to = (s_out * math.cos(ca + math.pi / 4), cy + s_out * math.sin(ca + math.pi / 4))
            t0 = math.atan2(p_from[1] - ctr[1], p_from[0] - ctr[0])
            t1 = math.atan2(p_to[1] - ctr[1], p_to[0] - ctr[0])
            while t1 <= t0:
                t1 += 2 * math.pi
            foil += [(ctr[0] + rl * math.cos(t0 + (t1 - t0) * i / 10), ctr[1] + rl * math.sin(t0 + (t1 - t0) * i / 10))
                     for i in range(10)]
        holes = lights + [foil]
        z1, z0 = -sb, -sb - dp
        pl = self.piece("tracery plate", "trim", "open", tracery={"lights": len(lights), "foils": tr["foils"]},
                        relief={"plane_z": z0, "proud_m": dp})
        pl.mesh.poly([(x, y, z1) for x, y in outline], Z, holes=[[(x, y, z1) for x, y in h] for h in holes])
        pl.mesh.poly([(x, y, z0) for x, y in outline], _mul(Z, -1), holes=[[(x, y, z0) for x, y in h] for h in holes])
        for h in holes:
            tube(pl.mesh, h, z1, z0)
        room = P["opening"]["recess_m"] * 2
        tube(w.mesh, outline, z0, z0 - room)
        bk = self.piece("room back", "backing", "board")
        bk.mesh.poly([(x, y, z0 - room) for x, y in outline], Z)

    def _panel(self):
        v, P = self.v, self.data["parts"]
        pn, Lp = P["panel"], P["leaf"]
        W, H, y0 = v["width_m"], v["height_m"], v["base_m"]
        self.board(-W / 2 - 0.6, W / 2 + 0.6, y0 + H + 0.6)
        tp, fr, sk = pn["tablet_proud_m"], pn["frame_m"], pn["field_sink_m"]
        x0, x1, y1 = -W / 2, W / 2, y0 + H
        fx0, fx1, fy0, fy1 = x0 + fr, x1 - fr, y0 + fr, y1 - fr
        zf = tp - sk
        t = self.piece("tablet", "trim", "open", relief={"plane_z": 0.0, "proud_m": tp})
        box(t.mesh, x0, x1, y0, y1, 0.0, tp, skip=("back", "front"))
        field = [(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]
        t.mesh.poly([(x0, y0, tp), (x1, y0, tp), (x1, y1, tp), (x0, y1, tp)], Z,
                    holes=[[(x, y, tp) for x, y in field]])
        tube(t.mesh, field, tp, zf)
        t.mesh.poly([(x, y, zf) for x, y in field], Z)
        mg = pn["margin_m"]
        bx0, bx1, by0, by1 = fx0 + mg, fx1 - mg, fy0 + mg, fy1 - mg
        self.meta["field"] = {"x": [bx0, bx1], "y": [by0, by1], "z": zf}
        yc, amp = (fy0 + fy1) / 2, (fy1 - fy0) * 0.16
        sx0, sx1 = bx0 + 0.02, bx1 - 0.02
        n = 48
        f = lambda x: yc + amp * math.sin(2 * math.pi * pn["waves"] * (x - sx0) / (sx1 - sx0))
        path = [(sx0 + (sx1 - sx0) * i / n, f(sx0 + (sx1 - sx0) * i / n), zf) for i in range(n + 1)]
        r = pn["stem_radius_m"]
        stem = self.piece("stem", "carving", "open", relief={"plane_z": zf, "proud_m": r})
        sweep(stem.mesh, path, Z, [(r * math.cos(math.pi * (1 - k / 8)), r * math.sin(math.pi * (1 - k / 8)))
                                   for k in range(9)], caps=(True, True))
        per = 2 * pn["waves"]
        k = 0
        for i in range(per * 2):
            xs = sx0 + (sx1 - sx0) * (i + 0.5) / (per * 2)
            dydx = amp * 2 * math.pi * pn["waves"] / (sx1 - sx0) * math.cos(2 * math.pi * pn["waves"] * (xs - sx0) / (sx1 - sx0))
            up = 1 if i % 2 == 0 else -1
            T = _unit((1.0, dydx, 0.0))
            Nn = (-T[1] * up, T[0] * up, 0.0)
            ang = math.radians(35 + 20 * (self.rng.random() - 0.5))
            D = _unit(_add(_mul(Nn, math.cos(ang)), _mul(T, math.sin(ang))))
            ln = pn["leaf_length_m"][0] + (pn["leaf_length_m"][1] - pn["leaf_length_m"][0]) * self.rng.random()
            S = (-D[1], D[0])
            reach = lambda L_: [(xs + D[0] * L_ * f_ + S[0] * e, f(xs) + D[1] * L_ * f_ + S[1] * e)
                                for f_ in (0.5, 1.0) for e in (-pn["leaf_width_m"] / 2, pn["leaf_width_m"] / 2)]
            for _ in range(30):         # shorten a leaf until it stays inside its field
                if all(bx0 <= x <= bx1 and by0 <= y <= by1 for x, y in reach(ln)):
                    break
                ln *= 0.95
            lf = self.piece(f"panel leaf {k + 1}", "carving", "open", bounded=True,
                            relief={"plane_z": zf, "proud_m": pn["leaf_relief_m"]})
            leaf(lf.mesh, (xs, f(xs), zf), D, Z, ln, pn["leaf_width_m"], pn["leaf_relief_m"], curl=0.0,
                 lobes=Lp["lobes"], lobe_depth=Lp["lobe_depth"], groove=Lp["midrib_groove"],
                 nt=Lp["steps_t"], nu=Lp["steps_u"], rng=self.rng)
            k += 1

    def _hero(self):
        v, P = self.v, self.data["parts"]
        vs = P["voussoir"]
        n, st, dp = v["orders"], v["order_step_m"], v["order_depth_m"]
        W, spring = v["clear_width_m"], v["spring_m"]
        half = [W / 2 + st * (n - 1 - k) for k in range(n)]
        arches = [Arch("round", 0.0, 2 * h, spring) for h in half]
        outl = [doorway(a, a.s0, a.s1, None, n=28) for a in arches]
        R = vs["ring_depth_m"]
        stop = 0.14
        hw = half[0] + R + 0.07 + 0.1 + stop + 0.6
        rec = P["opening"]["recess_m"]
        self.board(-hw, hw, arches[0].apex() + R + 0.7, door=outl[0], recess=0.0)
        w = self.pieces[0]
        for k in range(n):
            za, zb = -k * dp, -(k + 1) * dp if k < n - 1 else -(n - 1) * dp - rec
            tube(w.mesh, outl[k], za, zb, closed=False)
            fl = self.piece(f"order {k + 1} floor", "ground", "board")
            fl.mesh.poly([(-half[k], 0.0, za), (half[k], 0.0, za), (half[k], 0.0, zb), (-half[k], 0.0, zb)], Y)
            if k < n - 1:
                ring_face = outl[k] + list(reversed(outl[k + 1]))
                w.mesh.poly([(x, y, zb) for x, y in ring_face], Z)
        bk = self.piece("door back", "backing", "board")
        bk.mesh.poly([(x, y, -(n - 1) * dp - rec) for x, y in outl[-1]], Z)
        self.meta["orders"] = n
        self.meta["order_depth_m"] = (n - 1) * dp
        self.ring(arches[0], 0.0, R, v["voussoirs_outer"], vs["proud_m"], name="outer ring")
        for k in range(n - 1):
            gap = half[k] - half[k + 1] - 0.008
            self.ring(arches[k + 1], 0.0, gap, v["voussoirs_order"], vs["proud_m"], z0=-(k + 1) * dp,
                      name=f"order {k + 2} ring")
        co = P["colonnette"]
        p2 = co["plinth_m"] / 2
        for k in range(n - 1):
            for sgn in (-1, 1):
                cx = sgn * (half[k] - p2 - 0.002)
                # the nook abacus is cut to clear its neighbour order's (no face on a face)
                self.colonnette(cx, -(k + 1) * dp + p2 + 0.002, spring - 0.004, "foliate",
                                name=f"nook {k + 1}{'l' if sgn < 0 else 'r'} colonnette",
                                abacus_m=min(co["abacus_m"], st - 0.004))
        self.label(arches[0], R + 0.01, stop)

    def _rowhouse(self):
        v, P = self.v, self.data["parts"]
        W, H = v["clear_width_m"], v["clear_height_m"]
        ar = P["profiles"]["architrave"]["points"]
        aw = max(n for n, _ in ar)
        ov = P["hood_block"]["overhang_m"]
        hw = W / 2 + aw + ov + 0.7
        self.board(-hw, hw, H + aw + 1.0, door=doorway(None, -W / 2, W / 2, H), recess=P["opening"]["recess_m"])
        a = self.piece("architrave", "trim", "open", relief={"plane_z": 0.0, "proud_m": max(u for _, u in ar)})
        sweep(a.mesh, [(-W / 2, 0.0, 0.0), (-W / 2, H, 0.0), (W / 2, H, 0.0), (W / 2, 0.0, 0.0)], Z, ar,
              side=-1.0, smooth=False)
        self.cornice_hood(-W / 2 - aw - ov, W / 2 + aw + ov, H + aw)
        self.meta["orders"] = 1
        self.meta["order_depth_m"] = 0.0


def _inside_arch(arch, p) -> bool:
    if p[0] <= arch.s0 or p[0] >= arch.s1 or p[1] <= arch.spring - 1e3:
        return False
    if p[1] <= arch.spring:
        return True
    if arch.kind == "pointed":
        return math.dist(p, (arch.s0, arch.spring)) < arch.R and math.dist(p, (arch.s1, arch.spring)) < arch.R
    return math.dist(p, (arch.cx, arch.cy)) < arch.R


def load() -> dict:
    return json.loads(DATA.read_text())


PANEL_GAP = 0.6


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0) -> Variant:
    return Variant(v, data, origin, index).build()


def place(var: Variant):
    """Move every piece by the variant's origin (the specimen lays the boards in a row)."""
    ox, oy, oz = var.O
    for p in var.pieces:
        p.mesh.pos = [(x + ox, y + oy, z + oz) for x, y, z in p.mesh.pos]
    return var


def build_kit(data: dict | None = None) -> list[Variant]:
    data = data or load()
    out, x = [], 0.0
    for i, v in enumerate(data["variants"]):
        probe = build_variant(v, data, index=i)
        lo, hi = probe.meta["panel"]["x"]
        probe.O = (x - lo, 0.0, 0.0)
        out.append(place(probe))
        x += (hi - lo) + PANEL_GAP
    return out


def triangles(var: Variant, include_board: bool = False) -> int:
    return sum(p.mesh.triangles() for p in var.pieces if include_board or p.role not in BOARD_ROLES)


def relief_depth(var: Variant) -> float:
    """How far the trim reaches from the wall face, forward and back: the projection of
    the furthest-standing piece plus the depth its stepped orders cut into the wall."""
    zs = [q[2] - var.O[2] for p in var.pieces if p.role not in BOARD_ROLES for q in p.mesh.pos]
    return round(max(zs) + var.meta.get("order_depth_m", 0.0), 4) if zs else 0.0


# -- glTF -------------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def to_glb(kit: list[Variant], data: dict) -> bytes:
    bin_ = bytearray()
    views, accessors, meshes, nodes = [], [], [], []

    def view(blob: bytes, target):
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(blob)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(blob), "target": target})
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False):
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5125: "I", 5123: "H"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [struct.unpack("<f", struct.pack("<f", min(v[k] for v in values)))[0] for k in range(comps)]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", max(v[k] for v in values)))[0] for k in range(comps)]
        accessors.append(acc)
        return len(accessors) - 1

    mat_names = list(MATERIALS)
    materials_out = [{"name": f"k09_{n}", "pbrMetallicRoughness": {
        "baseColorFactor": [*[round(c, 4) for c in MATERIALS[n]["color"]], 1.0],
        "metallicFactor": 0.0, "roughnessFactor": MATERIALS[n]["roughness"]}} for n in mat_names]
    for var in kit:
        by_mat: dict[str, list[Mesh]] = {}
        for role in ROLE_MATERIAL:
            for p in var.pieces:
                if p.role == role and p.mesh.idx:
                    by_mat.setdefault(ROLE_MATERIAL[role], []).append(p.mesh)
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            pos, nrm, uv, conf, idx = [], [], [], [], []
            seen: dict = {}       # weld: one vertex per (position, normal, uv)
            for m in by_mat[name]:
                for i in m.idx:
                    key = (tuple(round(c, 5) for c in m.pos[i]), tuple(round(c, 4) for c in m.nrm[i]),
                           tuple(round(c, 4) for c in m.uv[i]))
                    if key not in seen:
                        seen[key] = len(pos)
                        pos.append(key[0])
                        nrm.append(key[1])
                        uv.append(key[2])
                        conf.append(m.conf[i])
                    idx.append(seen[key])
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        meshes.append({"name": var.v["id"], "primitives": prims_out})
        top = max(q[1] for p in var.pieces if p.role not in BOARD_ROLES for q in p.mesh.pos)
        nodes.append({"name": var.v["id"], "mesh": len(meshes) - 1, "extras": {
            "component_id": var.v["id"], "family": "trim", "kind": var.v["kind"], "motif": var.v["motif"],
            "seed": var.seed, "origin": [round(c, 4) for c in var.O],
            "pieces": sum(1 for p in var.pieces if p.role not in BOARD_ROLES),
            "triangles_trim": triangles(var), "triangles_with_board": triangles(var, True),
            "relief_depth_m": relief_depth(var),
            "sockets": {"base": [0.0, 0.0, 0.0], "top": [0.0, round(top, 4), 0.0]}}})
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials_out,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
        "extras": {"k09": {"data": "data/components/prairie_1904/k09_trim.json", "ticket": "T-2309",
                           "contract": "data/components/prairie_1904/k01_contract.json"}},
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)


def main(argv) -> int:
    data = load()
    blob = to_glb(build_kit(data), data)
    out = ROOT / data["specimen"]
    if "--check" in argv:
        if not out.exists() or out.read_bytes() != blob:
            print(f"FAIL {out.relative_to(ROOT)} is not what the generator builds from "
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k09_trim.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
