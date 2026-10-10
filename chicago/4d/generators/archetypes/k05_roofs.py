"""The K05 roof-construction kit: every roof a closed solid, written straight to glTF.

TICKET T-2301 (piece 1 of T-1847, K05). The kit's sizes are data in
`data/components/prairie_1904/k05_roofs.json`; this module reads them and builds each
variant the way T-2302 will build the 1808 exemplar's roof:

  elements   each part of a roof is a CLOSED polyhedron of convex faces: a hipped,
             mansard or tower roof is a stack of rings (soffit, fascia, covering up to
             the ridge or apex); a gable body is extruded along its ridge (the attic
             with its eave boxes, a verge strip past each gable, a return at each
             eave foot); a parapet and its coping are the gable's outline extruded
             through the wall's thickness; a dormer is a small gable body.
  union      the elements are joined by a BSP boolean union (the csg.js algorithm),
             so a valley, an abutment or a plane meeting a gable is cut along the
             line where the two surfaces really meet. Nothing is trimmed by hand.
  closure    the union's polygons are welded, every vertex lying on another
             polygon's edge is inserted into that edge (no T-junctions), and each
             polygon is triangulated. The result must be watertight: the check
             (tools/check_roof_kit.py) counts every edge.
  graph      ridges, hips, valleys, curbs, eaves, verges and abutments are READ off
             the built surface by dihedral angle and by which parts meet, and are
             exported on each node for K04 to lay caps, valley flashing and aprons on.

WHY PURE PYTHON: the reasons k01_frontage.py and k06_windows.py give. The gate measures
vertices and edges, and they are easiest to hold when this module writes them. `Prim`
and the vector helpers are K01's own.

    python3 generators/archetypes/k05_roofs.py           write the specimen GLB
    python3 generators/archetypes/k05_roofs.py --check   refuse if it is stale
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archetypes.k01_frontage import Prim, _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json"
GENERATOR = "chicago-4d generators/archetypes/k05_roofs.py (K05, T-2301)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]
VARIANT_GAP = 4.0     # metres of ground between two variants on the specimen board

sys.setrecursionlimit(20000)

# Role -> material. A role is what the gate and the graph read (which part a face is);
# a material is what a renderer binds. Fixed order: the file is the same bytes every run.
ROLE_MATERIAL = {
    "covering": "covering", "fascia": "trim", "verge": "trim", "return": "trim",
    "soffit": "soffit", "gable": "masonry", "parapet": "masonry", "coping": "coping",
    "cheek": "trim", "dormer_face": "trim", "wall": "masonry", "base": "base",
}
# The board, not the roof: excluded from a roof's costs.
BOARD_ROLES = ("wall", "base")
# A covering edge against one of these is an abutment: where K04's flashing goes.
ABUTTING = ("gable", "parapet", "coping", "cheek", "dormer_face", "wall")


def materials() -> dict:
    return {
        "covering": {"color": (0.21, 0.22, 0.25), "roughness": 0.78},
        "trim": {"color": (0.80, 0.76, 0.66), "roughness": 0.7},
        "soffit": {"color": (0.86, 0.83, 0.75), "roughness": 0.8},
        "masonry": {"color": (0.55, 0.31, 0.23), "roughness": 0.9},
        "coping": {"color": (0.78, 0.74, 0.66), "roughness": 0.85},
        "base": {"color": (0.30, 0.28, 0.26), "roughness": 1.0},
    }


def seed_of(component_id: str, index: int = 0, structure_id: str = "k05_roof_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


# -- polygons and the BSP union (csg.js, Evan Wallace, MIT; re-expressed here) ---------------

EPS = 1e-5
COPLANAR, FRONT, BACK, SPANNING = 0, 1, 2, 3


def _newell(pts):
    n = (0.0, 0.0, 0.0)
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                     (a[0] - b[0]) * (a[1] + b[1])))
    return n


class Plane:
    __slots__ = ("n", "w")

    def __init__(self, n, w):
        self.n, self.w = n, w

    def flipped(self):
        return Plane(_mul(self.n, -1.0), -self.w)

    def split(self, poly, cof, cob, front, back):
        n, w = self.n, self.w
        ptype, types = 0, []
        for v in poly.v:
            t = n[0] * v[0] + n[1] * v[1] + n[2] * v[2] - w
            k = BACK if t < -EPS else FRONT if t > EPS else COPLANAR
            ptype |= k
            types.append(k)
        if ptype == COPLANAR:
            (cof if _dot(n, poly.plane.n) > 0 else cob).append(poly)
        elif ptype == FRONT:
            front.append(poly)
        elif ptype == BACK:
            back.append(poly)
        else:
            f, b = [], []
            m = len(poly.v)
            for i in range(m):
                j = (i + 1) % m
                ti, tj, vi, vj = types[i], types[j], poly.v[i], poly.v[j]
                if ti != BACK:
                    f.append(vi)
                if ti != FRONT:
                    b.append(vi)
                if (ti | tj) == SPANNING:
                    d = _sub(vj, vi)
                    t = (w - _dot(n, vi)) / _dot(n, d)
                    x = _add(vi, _mul(d, t))
                    f.append(x)
                    b.append(x)
            if len(f) >= 3:
                front.append(Poly(f, poly.role, poly.plane))
            if len(b) >= 3:
                back.append(Poly(b, poly.role, poly.plane))


class Poly:
    __slots__ = ("v", "role", "plane")

    def __init__(self, v, role, plane=None):
        self.v, self.role = list(v), role
        if plane is None:
            n = _unit(_newell(self.v))
            plane = Plane(n, _dot(n, self.v[0]))
        self.plane = plane

    def flipped(self):
        return Poly(list(reversed(self.v)), self.role, self.plane.flipped())


def oriented(pts, role, hint):
    """A convex planar polygon whose normal points along `hint` (or None if degenerate)."""
    clean = []
    for p in pts:
        if not clean or max(abs(p[k] - clean[-1][k]) for k in range(3)) > 1e-9:
            clean.append(p)
    if len(clean) > 1 and max(abs(clean[0][k] - clean[-1][k]) for k in range(3)) <= 1e-9:
        clean.pop()
    if len(clean) < 3:
        return None
    n = _newell(clean)
    if math.sqrt(_dot(n, n)) < 1e-10:
        return None
    if _dot(n, hint) < 0:
        clean.reverse()
    return Poly(clean, role)


class Node:
    __slots__ = ("plane", "front", "back", "polys")

    def __init__(self, polys=None):
        self.plane, self.front, self.back, self.polys = None, None, None, []
        if polys:
            self.build(polys)

    def invert(self):
        self.polys = [p.flipped() for p in self.polys]
        self.plane = self.plane.flipped()
        if self.front:
            self.front.invert()
        if self.back:
            self.back.invert()
        self.front, self.back = self.back, self.front

    def clip_polys(self, polys):
        if self.plane is None:
            return list(polys)
        front, back = [], []
        for p in polys:
            self.plane.split(p, front, back, front, back)
        if self.front:
            front = self.front.clip_polys(front)
        back = self.back.clip_polys(back) if self.back else []
        return front + back

    def clip_to(self, bsp):
        self.polys = bsp.clip_polys(self.polys)
        if self.front:
            self.front.clip_to(bsp)
        if self.back:
            self.back.clip_to(bsp)

    def all_polys(self):
        out = list(self.polys)
        if self.front:
            out += self.front.all_polys()
        if self.back:
            out += self.back.all_polys()
        return out

    def build(self, polys):
        if not polys:
            return
        if self.plane is None:
            self.plane = polys[0].plane
        front, back = [], []
        for p in polys:
            self.plane.split(p, self.polys, self.polys, front, back)
        if front:
            if self.front is None:
                self.front = Node()
            self.front.build(front)
        if back:
            if self.back is None:
                self.back = Node()
            self.back.build(back)


def union(a_polys, b_polys):
    a, b = Node(a_polys), Node(b_polys)
    a.clip_to(b)
    b.clip_to(a)
    b.invert()
    b.clip_to(a)
    b.invert()
    a.build(b.all_polys())
    return a.all_polys()


def union_all(solids):
    out = list(solids[0])
    for s in solids[1:]:
        out = union(out, s)
    return out


# -- elements: closed polyhedra of convex faces ----------------------------------------------

def _clean2(pts, tol=1e-9):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > tol or abs(p[1] - out[-1][1]) > tol:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) <= tol and abs(out[0][1] - out[-1][1]) <= tol:
        out.pop()
    # drop collinear points
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 1e-12:
                out.pop(i)
                changed = True
                break
    return out


def _area2d(pts):
    return sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1])) / 2


def _convex2d(pts):
    s = 0
    for i in range(len(pts)):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) < 1e-12:
            continue
        if s == 0:
            s = 1 if cr > 0 else -1
        elif (cr > 0) != (s > 0):
            return False
    return True


def earclip(pts):
    """Triangles of a simple CCW polygon (no three consecutive points collinear)."""
    idx = list(range(len(pts)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12:
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = pts[j]
                d1 = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
                d2 = (c[0] - b[0]) * (p[1] - b[1]) - (c[1] - b[1]) * (p[0] - b[0])
                d3 = (a[0] - c[0]) * (p[1] - c[1]) - (a[1] - c[1]) * (p[0] - c[0])
                if d1 >= -1e-12 and d2 >= -1e-12 and d3 >= -1e-12:
                    inside = True
                    break
            if inside:
                continue
            tris.append([a, b, c])
            idx.pop(k)
            break
        else:
            raise ValueError("earclip: no ear found (polygon not simple?)")
    tris.append([pts[i] for i in idx])
    return tris


def by_edge(top, bottom, side, inner=None):
    """Name an extruded outline's faces by which way each edge faces: up (top), down
    (bottom) or sideways (side); a vertical edge at a == inner is a hidden joint."""
    def f(i, p, q):
        if abs(p[0] - q[0]) < 1e-9:
            return "hidden" if inner is not None and abs(p[0] - inner) < 1e-9 else side
        return top if (p[0] - q[0]) > 0 else bottom   # outward b of a CCW edge is p.a - q.a
    return f


def frame(axis: str, du=0.0, dw=0.0):
    """A map (a, b, c) -> world for an element whose ridge runs along `axis`: a is across
    the ridge, b is height, c is along the ridge. Axis permutations only, so the linear
    part maps hints exactly."""
    if axis == "x":
        return lambda a, b, c: (c + du, b, a + dw)
    return lambda a, b, c: (a + dw, b, c + du)


def _lin(P, v):
    o = P(0.0, 0.0, 0.0)
    return _sub(P(*v), o)


def extrude(outline, c0, c1, P, side_role, lo_role, hi_role):
    """A closed prism: the simple polygon `outline` in (a, b) extruded along c from c0 to
    c1. side_role(i, p, q) names the face on edge i; the two ends are lo_role, hi_role
    (None for a hidden end, which is still built: the solid must be closed)."""
    pts = _clean2(outline)
    if _area2d(pts) < 0:
        pts.reverse()
    polys = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        out2 = (q[1] - p[1], -(q[0] - p[0]))   # right of a CCW edge: outward
        quad = [P(p[0], p[1], c0), P(q[0], q[1], c0), P(q[0], q[1], c1), P(p[0], p[1], c1)]
        r = side_role(i, p, q) if callable(side_role) else side_role
        pl = oriented(quad, r, _lin(P, (out2[0], out2[1], 0.0)))
        if pl:
            polys.append(pl)
    pieces = [pts] if _convex2d(pts) else earclip(pts)
    for c, role, s in ((c0, lo_role, -1.0), (c1, hi_role, 1.0)):
        for piece in pieces:
            pl = oriented([P(a, b, c) for a, b in piece], role or "hidden", _lin(P, (0.0, 0.0, s)))
            if pl:
                polys.append(pl)
    return polys


def ring_stack(rings, band_roles, bottom_role, top_role="covering"):
    """A closed solid from horizontal rings [(y, [(x, z), ...]), ...] of equal vertex count:
    a bottom cap, a band of faces between each ring and the next, and a top cap if the
    last ring has area (an apex or a ridge closes itself)."""
    polys = []
    n = len(rings[0][1])
    cx = sum(p[0] for p in rings[0][1]) / n
    cz = sum(p[1] for p in rings[0][1]) / n
    y0, r0 = rings[0]
    pl = oriented([(x, y0, z) for x, z in r0], bottom_role, (0.0, -1.0, 0.0))
    if pl:
        polys.append(pl)
    for j in range(len(rings) - 1):
        (ya, ra), (yb, rb) = rings[j], rings[j + 1]
        for i in range(n):
            k = (i + 1) % n
            quad = [(ra[i][0], ya, ra[i][1]), (ra[k][0], ya, ra[k][1]),
                    (rb[k][0], yb, rb[k][1]), (rb[i][0], yb, rb[i][1])]
            mx, mz = (ra[i][0] + ra[k][0]) / 2, (ra[i][1] + ra[k][1]) / 2
            pl = oriented(quad, band_roles[j], (mx - cx, 0.0, mz - cz))
            if pl:
                polys.append(pl)
    yt, rt = rings[-1]
    if abs(_area2d(rt)) > 1e-8:
        pl = oriented([(x, yt, z) for x, z in rt], top_role, (0.0, 1.0, 0.0))
        if pl:
            polys.append(pl)
    return polys


def inset_rect(x0, x1, z0, z1, d):
    """An axis-aligned rectangle inset by d (clamped at its centre lines), CCW from above."""
    xa, xb = min(x0 + d, (x0 + x1) / 2), max(x1 - d, (x0 + x1) / 2)
    za, zb = min(z0 + d, (z0 + z1) / 2), max(z1 - d, (z0 + z1) / 2)
    return [(xa, za), (xb, za), (xb, zb), (xa, zb)]


def body_box(x0, x1, z0, z1, y0, y1, role="wall", base="base"):
    P = frame("z")
    return extrude([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, P,
                   lambda i, p, q: base if i == 0 else ("hidden" if i == 2 else role), role, role)


def hip_element(x0, x1, z0, z1, eave_y, t, o, f):
    """A hipped roof over the wall-line rectangle, its eaves overhanging by o."""
    hs, he = eave_y - o * t - f, eave_y - o * t
    X0, X1, Z0, Z1 = x0 - o, x1 + o, z0 - o, z1 + o
    d = min(X1 - X0, Z1 - Z0) / 2
    rings = [(hs, inset_rect(X0, X1, Z0, Z1, 0.0)), (he, inset_rect(X0, X1, Z0, Z1, 0.0)),
             (he + d * t, inset_rect(X0, X1, Z0, Z1, d))]
    return ring_stack(rings, ["fascia", "covering"], "soffit"), hs


def gable_element(u0, u1, w0, w1, eave_y, t, o, v, f, base_y, axis, verge_ends=("lo", "hi"),
                  return_len=0.0, wall_role="wall", end_role="gable", body_end_role="wall",
                  du=0.0, dw=0.0):
    """A gable body whose ridge runs along `axis` from u0 to u1 across w0..w1 (wall line).
    The attic prism carries both eave boxes; each end in verge_ends gets a verge strip
    (covering, rake board, rake soffit) and, if return_len, a return at each eave foot."""
    P = frame(axis, du, dw)
    hs, he = eave_y - o * t - f, eave_y - o * t
    wc, half = (w0 + w1) / 2, (w1 - w0) / 2
    ry = eave_y + half * t
    W0, W1 = w0 - o, w1 + o
    solids = []
    attic = [(W0, hs), (W1, hs), (W1, he), (wc, ry), (W0, he)]
    solids.append(extrude(attic, u0, u1, P, by_edge("covering", "soffit", "fascia"), end_role, end_role))
    solids.append(extrude([(w0, base_y), (w1, base_y), (w1, hs), (w0, hs)], u0, u1, P,
                          lambda i, p, q: "base" if i == 0 else ("hidden" if i == 2 else wall_role),
                          body_end_role, body_end_role))
    for end in verge_ends:
        c0, c1 = (u0 - v, u0) if end == "lo" else (u1, u1 + v)
        lo, hi = ("verge", "hidden") if end == "lo" else ("hidden", "verge")
        # each slope's strip is a parallelogram: covering above, rake soffit f below it
        for strip in ([(W0, hs), (wc, ry - f), (wc, ry), (W0, he)],
                      [(wc, ry - f), (W1, hs), (W1, he), (wc, ry)]):
            solids.append(extrude(strip, c0, c1, P, by_edge("covering", "soffit", "fascia", inner=wc), lo, hi))
        if return_len > 0:
            for ws, we in ((W0, w0 + return_len), (w1 - return_len, W1)):
                solids.append(extrude([(ws, hs), (we, hs), (we, he), (ws, he)], c0, c1, P,
                                      "return", lo and "return", "return"))
    return solids, hs, he, ry


def parapet_outline(variant, w0, w1, eave_y, t, o, up, top_above):
    """The parapet's top line across the gable, from the front eave to the back, as a
    list of (w, y), and the derived numbers. Every point clears the roof by `up`."""
    wc, half = (w0 + w1) / 2, (w1 - w0) / 2
    ry = eave_y + half * t
    W0, W1 = w0 - o, w1 + o
    roof = lambda w: eave_y + (min(w, 2 * wc - w) - w0) * t
    top = ry + top_above
    style = variant["style"]
    left = []
    meta = {}
    if style == "stepped":
        n = variant["steps"]
        th = variant.get("top_half_m", 0.45)
        ws = [W0 + (wc - th - W0) * k / n for k in range(n + 1)]
        for k in range(n):
            h = roof(ws[k + 1]) + up
            left += [(ws[k], h), (ws[k + 1], h)]
        left += [(wc - th, top), (wc, top)]
        meta["step_going_m"] = round(ws[1] - ws[0], 4)
    else:
        kn, th, segs = variant["kneeler_m"], variant["top_half_m"], variant["segments"]
        zs, ze = W0 + kn, wc - th
        s = lambda u: (1 - math.cos(math.pi * u)) / 2
        need = []
        for i in range(0, 201):
            u = i / 200
            w = zs + (ze - zs) * u
            if s(u) < 0.999:
                need.append((roof(w) + up - top * s(u)) / (1 - s(u)))
        hk = max([roof(zs) + up] + need)
        hk = math.ceil(hk * 1000) / 1000
        left.append((W0, hk))
        for i in range(segs + 1):
            u = i / segs
            left.append((zs + (ze - zs) * u, hk + (top - hk) * s(u)))
        left.append((wc, top))
        meta["kneeler_top_m"] = round(hk, 4)
    right = [(2 * wc - w, y) for w, y in reversed(left)]
    line = left + right[1:] if abs(left[-1][0] - wc) < 1e-12 else left + right
    meta["top_m"] = round(top, 4)
    return line, meta


def parapet_element(variant, line, side_u, P_axis, tw, base_y, coping_t, drip, du, dw):
    """The parapet slab (outline extruded through the wall) and its coping, at one end."""
    P = frame(P_axis, du, dw)
    c0, c1 = side_u
    solids = []
    W0, W1 = line[0][0], line[-1][0]
    outline = [(W0, base_y), (W1, base_y)] + list(reversed(line))
    solids.append(extrude(outline, c0, c1, P,
                          lambda i, p, q: "base" if i == 0 else "parapet", "parapet", "parapet"))
    if any(abs(wb - wa) < 1e-9 for (wa, _), (wb, _) in zip(line, line[1:])):
        # a stepped line: a coping slab on each step's top; a riser is the parapet's own face
        for (wa, ya), (wb, yb) in zip(line, line[1:]):
            if abs(wb - wa) < 1e-9:
                continue
            quad = [(wa, ya), (wb, yb), (wb, yb + coping_t), (wa, ya + coping_t)]
            solids.append(extrude(quad, c0 - drip, c1 + drip, P, "coping", "coping", "coping"))
    else:
        # a continuous line: one coping band following it, drip-wide on both faces
        band = list(line) + [(w, y + coping_t) for w, y in reversed(line)]
        solids.append(extrude(band, c0 - drip, c1 + drip, P, "coping", "coping", "coping"))
    return solids


# -- the variants -------------------------------------------------------------------------------

def variant_solids(v: dict, data: dict):
    """The closed elements of one variant, in the variant's own frame (wall line from
    (0, 0) to (width, depth), front +z), and the numbers they were built to."""
    p = data["parts"]
    o, f = p["eave"]["overhang_m"], p["eave"]["fascia_depth_m"]
    vg, rl = p["verge"]["overhang_m"], p["return"]["length_m"]
    W, D, E = v.get("width_m"), v.get("depth_m"), v["eave_m"]
    kind = v["kind"]
    meta: dict = {}
    solids = []
    if kind in ("hip", "cross_gable", "dormer"):
        t = math.tan(math.radians(v["pitch_deg"]))
        roof, hs = hip_element(0.0, W, 0.0, D, E, t, o, f)
        solids += [roof, body_box(0.0, W, 0.0, D, 0.0, hs)]
        meta["ridge_m"] = round(E - o * t + (min(W, D) / 2 + o) * t, 4)
        if kind == "cross_gable":
            wc, ww, L = W / 2, v["wing_width_m"], v["wing_projection_m"]
            back = ww / 2 + 0.5           # the wing's ridge dies into the main plane before this
            g, *_ = gable_element(D - back, D + L, wc - ww / 2, wc + ww / 2, E, t, o, vg, f, 0.0, "z",
                                  verge_ends=("hi",), return_len=rl)
            solids += g
        if kind == "dormer":
            dt = math.tan(math.radians(v["dormer_pitch_deg"]))
            dp = p["dormer"]
            dw, sb, up = v["dormer_width_m"], v["dormer_setback_m"], v["dormer_eave_above_m"]
            de = E + up
            front = D - sb
            dhalf = dw / 2 + dp["overhang_m"]
            ridge = de + (dw / 2) * dt
            back = D - (ridge - E) / t - 0.5   # where the main front plane has risen past the ridge
            g, dhs, *_ = gable_element(back, front, W / 2 - dw / 2, W / 2 + dw / 2, de, dt, dp["overhang_m"],
                                       dp["verge_m"], dp["fascia_depth_m"], hs, "z", verge_ends=("hi",),
                                       wall_role="cheek", end_role="dormer_face", body_end_role="dormer_face")
            solids += g
            meta["dormer_ridge_m"] = round(ridge, 4)
            meta["dormer_half_span_m"] = round(dhalf, 4)
    elif kind == "gable":
        t = math.tan(math.radians(v["pitch_deg"]))
        g, hs, he, ry = gable_element(0.0, D, 0.0, W, E, t, o, vg, f, 0.0, "z", return_len=rl)
        solids += g
        meta["ridge_m"] = round(ry, 4)
    elif kind == "parapet_gable":
        t = math.tan(math.radians(v["pitch_deg"]))
        pp, cp = p["parapet"], p["coping"]
        tw = pp["thickness_m"]
        g, hs, he, ry = gable_element(0.0, D, 0.0, W, E, t, o, vg, f, 0.0, "z", verge_ends=())
        solids += g
        line, m = parapet_outline(v, 0.0, W, E, t, o, pp["upstand_min_m"], pp["top_above_ridge_m"])
        for ends in ((0.0, tw), (D - tw, D)):
            solids += parapet_element(v, line, ends, "z", tw, 0.0, cp["thickness_m"], cp["drip_m"], 0.0, 0.0)
        meta.update(m)
        meta["ridge_m"] = round(ry, 4)
        meta["parapet_line"] = [[round(a, 4), round(b, 4)] for a, b in line]
    elif kind == "mansard":
        lt = math.tan(math.radians(v["lower_pitch_deg"]))
        ut = math.tan(math.radians(v["upper_pitch_deg"]))
        rise = v["lower_rise_m"]
        run = rise / lt
        hs, he = E - f, E   # a mansard's eave is its cornice: eave_m is the fascia's top
        X0, X1, Z0, Z1 = -o, W + o, -o, D + o
        # the lower face: a quadratic curve from the fascia's top (inset 0) to the curb
        L = math.hypot(run, rise)
        P0, P2 = (0.0, he), (run, E + rise)
        nrm = (-(P2[1] - P0[1]) / L, (P2[0] - P0[0]) / L)   # outward: less inset, more height
        sgn = 1.0 if v["profile"] == "convex" else -1.0
        mid = ((P0[0] + P2[0]) / 2, (P0[1] + P2[1]) / 2)
        P1 = (mid[0] + sgn * v["bulge"] * L * nrm[0], mid[1] + sgn * v["bulge"] * L * nrm[1])
        rings = [(hs, inset_rect(X0, X1, Z0, Z1, 0.0)), (he, inset_rect(X0, X1, Z0, Z1, 0.0))]
        n = v["segments"]
        for k in range(1, n + 1):
            u = k / n
            ins = (1 - u) ** 2 * P0[0] + 2 * (1 - u) * u * P1[0] + u * u * P2[0]
            y = (1 - u) ** 2 * P0[1] + 2 * (1 - u) * u * P1[1] + u * u * P2[1]
            rings.append((y, inset_rect(X0, X1, Z0, Z1, ins)))
        d = min(X1 - X0, Z1 - Z0) / 2
        rings.append((E + rise + (d - run) * ut, inset_rect(X0, X1, Z0, Z1, d)))
        roof = ring_stack(rings, ["fascia"] + ["covering"] * (len(rings) - 2), "soffit")
        solids += [roof, body_box(0.0, W, 0.0, D, 0.0, hs)]
        meta["curb_m"] = round(E + rise, 4)
        meta["ridge_m"] = round(rings[-1][0], 4)
    elif kind == "tower":
        n, R = v["sides"], v["radius_m"]
        t = math.tan(math.radians(v["pitch_deg"]))
        rin = R * math.cos(math.pi / n)
        Ro = (rin + o) / math.cos(math.pi / n)
        hs, he = E - o * t - f, E - o * t
        cx = cz = R
        ang = [2 * math.pi * (k + 0.5) / n for k in range(n)]
        ring = lambda r: [(cx + r * math.cos(a), cz - r * math.sin(a)) for a in ang]
        apex = he + (rin + o) * t
        rings = [(hs, ring(Ro)), (he, ring(Ro)), (apex, [(cx, cz)] * n)]
        solids.append(ring_stack(rings, ["fascia", "covering"], "soffit"))
        wall_ring = ring(R)
        solids.append(_plan_prism(wall_ring, 0.0, hs))
        meta["apex_m"] = round(apex, 4)
    else:
        raise ValueError(f"unknown kind {kind}")
    return solids, meta


def _plan_prism(ring, y0, y1):
    """A vertical prism over a convex plan polygon (x, z): walls, a base, a hidden top."""
    pts = list(ring)
    if _area2d(pts) < 0:
        pts.reverse()
    cx = sum(p[0] for p in pts) / len(pts)
    cz = sum(p[1] for p in pts) / len(pts)
    polys = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        pl = oriented([(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], "wall",
                      ((a[0] + b[0]) / 2 - cx, 0.0, (a[1] + b[1]) / 2 - cz))
        if pl:
            polys.append(pl)
    polys.append(oriented([(x, y0, z) for x, z in pts], "base", (0.0, -1.0, 0.0)))
    polys.append(oriented([(x, y1, z) for x, z in pts], "hidden", (0.0, 1.0, 0.0)))
    return polys


# -- closure: weld, repair T-junctions, triangulate --------------------------------------------

class Weld:
    """Vertices merged within `tol` (a grid hash, neighbours searched)."""

    def __init__(self, tol=1e-5):
        self.tol, self.cell, self.pts, self.grid = tol, tol * 4, [], {}

    def key(self, p):
        return tuple(int(math.floor(c / self.cell)) for c in p)

    def add(self, p):
        k = self.key(p)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for i in self.grid.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        q = self.pts[i]
                        if abs(p[0] - q[0]) <= self.tol and abs(p[1] - q[1]) <= self.tol and abs(p[2] - q[2]) <= self.tol:
                            return i
        self.pts.append(p)
        self.grid.setdefault(k, []).append(len(self.pts) - 1)
        return len(self.pts) - 1


def close(polys, tol=1e-5):
    """The union's polygons as a T-junction-free triangle list: [(i, j, k, role, normal)]
    over the welded points. Hidden faces never survive a correct union; one that does is
    kept, under its own role, for the check to refuse."""
    wd = Weld(tol)
    rings = []
    for pl in polys:
        r = []
        for p in pl.v:
            i = wd.add(p)
            if not r or r[-1] != i:
                r.append(i)
        if len(r) > 1 and r[0] == r[-1]:
            r.pop()
        if len(r) >= 3:
            rings.append((r, pl))
    pts = wd.pts
    order = sorted(range(len(pts)), key=lambda i: pts[i][0])
    xs = [pts[i][0] for i in order]
    import bisect
    tris, filled = [], []
    for r, pl in rings:
        full = []
        for a_i, b_i in zip(r, r[1:] + r[:1]):
            a, b = pts[a_i], pts[b_i]
            full.append(a_i)
            d = _sub(b, a)
            ll = _dot(d, d)
            if ll < 1e-20:
                continue
            lo, hi = min(a[0], b[0]) - tol, max(a[0], b[0]) + tol
            ins = []
            for j in order[bisect.bisect_left(xs, lo):bisect.bisect_right(xs, hi)]:
                if j == a_i or j == b_i:
                    continue
                q = pts[j]
                s = _dot(_sub(q, a), d) / ll
                if s <= 1e-9 or s >= 1 - 1e-9:
                    continue
                x = _add(a, _mul(d, s))
                e = _sub(q, x)
                if _dot(e, e) <= tol * tol:
                    ins.append((s, j))
            full += [j for s, j in sorted(ins)]
        filled.append((full, pl))
    # the BSP leaves each plane in many fragments; re-merge each (role, plane) group into
    # the region it covers and triangulate its boundary once, when that boundary is one
    # simple loop. Anything else keeps its fragments.
    groups: dict = {}
    for full, pl in filled:
        n = pl.plane.n
        key = (pl.role, round(n[0], 6), round(n[1], 6), round(n[2], 6), round(_dot(n, pts[full[0]]), 5))
        groups.setdefault(key, []).append((full, pl))
    # 1. each group as its merged loops (all outer), or else its own fragments
    faces = []   # (loops, role, n, merged)
    for key in sorted(groups, key=str):
        members = groups[key]
        n = members[0][1].plane.n
        loops = _boundary_loops([m[0] for m in members]) if len(members) > 1 else [list(members[0][0])]
        if loops and all(_poly_area(pts, lp, n) > 0 for lp in loops):
            faces.append((loops, key[0], n, True))
        else:
            faces.append(([list(m[0]) for m in members], key[0], n, False))
    # 2. a point that lies on a straight run in EVERY loop using it is only a split point
    #    the BSP left on an edge: the two faces either side both drop it
    def straight_at(lp, k, n):
        a, b, c = pts[lp[k - 1]], pts[lp[k]], pts[lp[(k + 1) % len(lp)]]
        x = _cross(_sub(b, a), _sub(c, b))
        return abs(_dot(x, n)) < 1e-12 and _dot(_sub(b, a), _sub(c, b)) > 0
    for _ in range(4):
        corner = set()
        for loops, role, n, merged in faces:
            for lp in loops:
                for k in range(len(lp)):
                    if not straight_at(lp, k, n):
                        corner.add(lp[k])
        changed = False
        for loops, role, n, merged in faces:
            for j, lp in enumerate(loops):
                keep = [i for i in lp if i in corner]
                if len(keep) != len(lp) and len(keep) >= 3:
                    loops[j] = keep
                    changed = True
        if not changed:
            break
    # 3. triangulate: ear-clip a merged face, checking its area; a fragment by fan
    for loops, role, n, merged in faces:
        tri = []
        if merged:
            area_in = sum(_poly_area(pts, lp, n) for lp in loops)
            for lp in loops:
                t = _earclip_loop(pts, lp, n)
                if t is None:
                    tri = None
                    break
                tri += t
            if tri is not None and abs(area_in - sum(_poly_area(pts, t, n) for t in tri)) <= 1e-6 * max(1.0, area_in):
                tris += [(a, b, c, role, n) for a, b, c in tri]
                continue
        for lp in loops:
            tris += _fan(wd, lp, Poly([pts[i] for i in lp], role, Plane(n, _dot(n, pts[lp[0]]))))
            pts = wd.pts
    return wd.pts, tris


def _fan(wd, full, pl):
    """One polygon's triangles: a plain fan, or, if any point lies on a straight run
    (inserted, or a split point the BSP left on an edge), a fan from its centroid."""
    pts = wd.pts
    n = pl.plane.n
    P = [pts[i] for i in full]
    straight = any(abs(_dot(_cross(_sub(P[k], P[k - 1]), _sub(P[(k + 1) % len(P)], P[k])), n)) < 1e-12
                   for k in range(len(P)))
    if len(full) == 3 or not straight:
        return [(full[0], full[k], full[k + 1], pl.role, n) for k in range(1, len(full) - 1)]
    cen = tuple(sum(q[c] for q in P) / len(P) for c in range(3))
    ci = wd.add(cen)
    out = []
    for k in range(len(full)):
        a_i, b_i = full[k], full[(k + 1) % len(full)]
        ab = _cross(_sub(wd.pts[a_i], cen), _sub(wd.pts[b_i], cen))
        if _dot(ab, ab) >= 1e-24:
            out.append((ci, a_i, b_i, pl.role, n))
    return out


def _boundary_loops(rings):
    """The boundary loops of a set of polygons sharing a plane, or None where a boundary
    point is pinched (two loops through one point)."""
    edges = {}
    for r in rings:
        for a, b in zip(r, r[1:] + r[:1]):
            if (b, a) in edges:
                edges[(b, a)] -= 1
                if not edges[(b, a)]:
                    del edges[(b, a)]
            else:
                edges[(a, b)] = edges.get((a, b), 0) + 1
    nxt = {}
    for (a, b), c in edges.items():
        if c != 1 or a in nxt:
            return None
        nxt[a] = b
    loops, left = [], set(nxt)
    while left:
        start = min(left)
        loop, cur = [start], nxt[start]
        left.discard(start)
        while cur != start:
            if cur not in left:
                return None
            loop.append(cur)
            left.discard(cur)
            cur = nxt[cur]
        loops.append(loop)
    return loops or None


def _poly_area(pts, ring, n):
    s = (0.0, 0.0, 0.0)
    for a, b in zip(ring, ring[1:] + ring[:1]):
        s = _add(s, _cross(pts[a], pts[b]))
    return _dot(s, n) / 2


def _earclip_loop(pts, loop, n):
    """Ear-clip a planar loop (CCW about n) that may carry collinear points, keeping every
    point (a neighbour may share it). None if it cannot."""
    au = _cross((0.0, 1.0, 0.0), n)
    au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
    av = _cross(n, au)
    P = {i: (_dot(pts[i], au), _dot(pts[i], av)) for i in loop}
    idx = list(loop)
    out = []
    cr = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    guard = 0
    while len(idx) > 3:
        guard += 1
        if guard > 4 * len(loop) * len(loop):
            return None
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = P[i0], P[i1], P[i2]
            if cr(a, b, c) <= 1e-10:
                continue
            blocked = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = P[j]
                if cr(a, b, p) >= -1e-10 and cr(b, c, p) >= -1e-10 and cr(c, a, p) >= -1e-10:
                    blocked = True
                    break
            if blocked:
                continue
            out.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            return None
    a, b, c = (P[i] for i in idx)
    if cr(a, b, c) <= 1e-10:
        return None
    out.append(tuple(idx))
    return out


# -- the roof graph -------------------------------------------------------------------------------

def _tri_normal(pts, t):
    a, b, c = pts[t[0]], pts[t[1]], pts[t[2]]
    n = _cross(_sub(b, a), _sub(c, a))
    l = math.sqrt(_dot(n, n))
    return _mul(n, 1 / l) if l > 0 else (0.0, 0.0, 0.0)


def graph(pts, tris, data):
    """Every line where the covering meets itself or another part, classed, with
    collinear touching edges of one kind merged into one line."""
    g = data["graph"]
    seam = math.radians(g["seam_max_deg"])
    lvl = g["level_tolerance"]
    edges = {}
    for ti, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges.setdefault((min(a, b), max(a, b)), []).append(ti)
    found = []   # (kind, a, b)
    seams = 0
    for (a, b), ts in edges.items():
        if len(ts) != 2:
            continue
        t1, t2 = tris[ts[0]], tris[ts[1]]
        r1, r2 = t1[3], t2[3]
        if "covering" not in (r1, r2):
            continue
        if r1 == r2 == "covering":
            n1, n2 = _tri_normal(pts, t1), _tri_normal(pts, t2)
            ang = math.acos(max(-1.0, min(1.0, _dot(n1, n2))))
            if ang < 1e-6:
                continue
            if ang < seam:
                seams += 1
                continue
            c2 = tuple(sum(pts[i][k] for i in t2[:3]) / 3 for k in range(3))
            convex = _dot(n1, _sub(c2, pts[a])) < 0
            d = _sub(pts[b], pts[a])
            level = abs(d[1]) <= lvl * math.sqrt(_dot(d, d))
            h = n1[0] * n2[0] + n1[2] * n2[2]
            if convex:
                kind = ("ridge" if h < 0 else "curb") if level else "hip"
            else:
                kind = "kick" if level else "valley"
        else:
            (other, ot), ct = ((r2, t2), t1) if r1 == "covering" else ((r1, t1), t2)
            oc = tuple(sum(pts[i][k] for i in ot[:3]) / 3 for k in range(3))
            # in front of the covering's plane: the part stands on the roof; behind it,
            # the part hangs under the covering's edge (a fascia, a rake board)
            standing = _dot(_tri_normal(pts, ct), _sub(oc, pts[a])) > 1e-6
            if other in ABUTTING or standing and other in ("fascia", "verge", "return", "soffit"):
                kind = "abutment"   # a part standing on the covering: where flashing goes
            else:
                kind = {"fascia": "eave", "verge": "verge", "return": "return"}.get(other, f"covering|{other}")
        found.append((kind, a, b))
    # merge collinear touching edges of one kind
    parent = list(range(len(found)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    at = {}
    for i, (k, a, b) in enumerate(found):
        at.setdefault((k, a), []).append(i)
        at.setdefault((k, b), []).append(i)
    for (k, v), ids in at.items():
        for x in ids:
            for y in ids:
                if x >= y:
                    continue
                _, a1, b1 = found[x]
                _, a2, b2 = found[y]
                d1 = _unit(_sub(pts[b1], pts[a1]))
                d2 = _unit(_sub(pts[b2], pts[a2]))
                # one straight line; a hip or valley may also bend gently along a curve
                lim = 1 - 1e-6 if k not in ("hip", "valley") else math.cos(seam)
                if abs(_dot(d1, d2)) >= lim:
                    parent[root(x)] = root(y)
    lines: dict[int, dict] = {}
    for i, (k, a, b) in enumerate(found):
        L = lines.setdefault(root(i), {"kind": k, "pts": set()})
        L["pts"] |= {a, b}
    out = []
    for L in lines.values():
        ps = [pts[i] for i in L["pts"]]
        d = _sub(ps[-1], ps[0]) if len(ps) > 1 else (1.0, 0.0, 0.0)
        # the two extreme points along the line
        key = lambda q: _dot(_sub(q, ps[0]), d)
        e0, e1 = min(ps, key=key), max(ps, key=key)
        out.append({"kind": L["kind"], "from": [round(c, 4) for c in e0], "to": [round(c, 4) for c in e1],
                    "length_m": round(math.dist(e0, e1), 4)})
    out.sort(key=lambda e: (e["kind"], e["from"], e["to"]))
    counts: dict[str, int] = {}
    for e in out:
        counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    return {"lines": out, "counts": dict(sorted(counts.items())), "seam_edges": seams}


# -- build ------------------------------------------------------------------------------------------

class Roof:
    def __init__(self, v, pts, tris, meta, origin, solids):
        self.v, self.pts, self.tris, self.meta, self.O = v, pts, tris, meta, origin
        self.n_solids = solids
        self.seed = seed_of(v["id"])


def _shift(polys, dx):
    return [Poly([(p[0] + dx, p[1], p[2]) for p in pl.v], pl.role) for pl in polys]


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), joined: bool = True) -> Roof:
    solids, meta = variant_solids(v, data)
    solids = [_shift(s, origin[0]) for s in solids] if origin[0] else solids
    polys = union_all(solids) if joined else [p for s in solids for p in s]
    pts, tris = close(polys)
    return Roof(v, pts, tris, meta, origin, len(solids))


def footprint_span(v: dict, data: dict):
    solids, _ = variant_solids(v, data)
    xs = [p[0] for s in solids for pl in s for p in pl.v]
    return min(xs), max(xs)


def build_kit(data: dict | None = None) -> list[Roof]:
    data = data or load()
    out, x = [], 0.0
    for v in data["variants"]:
        lo, hi = footprint_span(v, data)
        out.append(build_variant(v, data, origin=(x - lo, 0.0, 0.0)))
        x += (hi - lo) + VARIANT_GAP
    return out


def load() -> dict:
    return json.loads(DATA.read_text())


def triangles(r: Roof, include_board: bool = False) -> int:
    return sum(1 for t in r.tris if include_board or t[3] not in BOARD_ROLES)


# -- glTF ---------------------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def _prims(r: Roof) -> dict[str, Prim]:
    """Flat-shaded per triangle, metric UVs on each face's own contour and uphill axes from
    the world origin, so a covering's courses run on unbroken across every fragment of
    one plane the union left."""
    prims: dict[str, Prim] = {}
    Y = (0.0, 1.0, 0.0)
    for a, b, c, role, n in r.tris:
        tn = _tri_normal(r.pts, (a, b, c))
        au = _cross(Y, tn)
        au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
        av = _cross(tn, au)
        pr = prims.setdefault(role, Prim(role))
        pr.face([r.pts[a], r.pts[b], r.pts[c]], tn, ((0.0, 0.0, 0.0), au, av, 1.0, 1.0, 0.0, 0.0), RECONSTRUCTED)
    return prims


def to_glb(kit: list[Roof], data: dict) -> bytes:
    mats = materials()
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

    mat_names = list(mats)
    materials_out = [{"name": f"k05_{name}", "pbrMetallicRoughness": {
        "baseColorFactor": [*[round(c, 4) for c in mats[name]["color"]], 1.0],
        "metallicFactor": 0.0, "roughnessFactor": mats[name]["roughness"]}} for name in mat_names]
    for r in kit:
        prims = _prims(r)
        by_mat: dict[str, list[Prim]] = {}
        for role in ROLE_MATERIAL:   # fixed order
            if role in prims and prims[role].idx:
                by_mat.setdefault(ROLE_MATERIAL[role], []).append(prims[role])
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            pos, nrm, uv, conf, idx = [], [], [], [], []
            for pr in by_mat[name]:
                base = len(pos)
                pos += [tuple(round(c, 5) for c in q) for q in pr.pos]
                nrm += [tuple(round(c, 6) for c in q) for q in pr.nrm]
                uv += [tuple(round(c, 5) for c in q) for q in pr.uv]
                conf += pr.conf
                idx += [base + i for i in pr.idx]
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        meshes.append({"name": r.v["id"], "primitives": prims_out})
        gr = graph(r.pts, r.tris, data)
        W, D = r.v.get("width_m"), r.v.get("depth_m")
        nodes.append({"name": r.v["id"], "mesh": len(meshes) - 1, "extras": {
            "component_id": r.v["id"], "family": "roof", "kind": r.v["kind"], "seed": r.seed,
            "origin": [round(c, 4) for c in r.O],
            "triangles_roof": triangles(r), "triangles_with_board": triangles(r, True),
            "sockets": {"eave": [round(r.O[0], 4), r.v["eave_m"], round(D if D else 0.0, 4)],
                        "ridge": [round(c, 4) for c in _ridge_socket(gr, r)]},
            "measured": {k: v for k, v in r.meta.items() if k != "parapet_line"},
            "graph": gr}})
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
        "extras": {"k05": {"data": "data/components/prairie_1904/k05_roofs.json", "ticket": "T-2301",
                           "contract": "data/components/prairie_1904/k01_contract.json"}},
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)


def _ridge_socket(gr, r):
    """The highest point of the roof's highest ridge (or its apex): K01's ridge socket."""
    ridges = [e for e in gr["lines"] if e["kind"] == "ridge"]
    if ridges:
        e = max(ridges, key=lambda e: (e["from"][1], e["length_m"]))
        return [(e["from"][k] + e["to"][k]) / 2 for k in range(3)]
    top = max((p for t in r.tris if t[3] == "covering" for p in (r.pts[t[0]], r.pts[t[1]], r.pts[t[2]])),
              key=lambda p: p[1])
    return list(top)


def main(argv) -> int:
    data = load()
    blob = to_glb(build_kit(data), data)
    out = ROOT / data["specimen"]
    if "--check" in argv:
        if not out.exists() or out.read_bytes() != blob:
            print(f"FAIL {out.relative_to(ROOT)} is not what the generator builds from "
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k05_roofs.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
