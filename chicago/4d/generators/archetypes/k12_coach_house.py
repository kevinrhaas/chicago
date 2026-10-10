"""The K12 coach-house kit: a two-storey brick coach house, its stable fittings and its
service wings, every piece real geometry written straight to glTF.

TICKET T-2320 (piece 1 of T-1854, K12). The kit's sizes are data in
`data/components/prairie_1904/k12_coach_house.json`; this module reads them and builds
each variant on a specimen lot the way T-2321 will build one behind a named house:

  shell          an alley wall and a yard wall, an open gable and a party wall on the lot
                 line, each a solid with its openings cut through it, over a basement
  roof           a gable roof slab dying into the party wall, which rises above it and
                 returns past both eaves under a weathered stone coping
  carriage bay   a pair of boarded leaves on strap hinges under a boarded head panel, in a
                 segmental opening with a brick ring two rowlocks deep
  loft hatch     a pair of leaves, and over it a hoist beam let into the wall with a hook
  sash, doors    four-light stable sash, boarded doors, a two-leaf stable (Dutch) door,
                 stone sills and lintels
  ramp           a cleated ramp down to a basement door between two retaining walls
  stair          an external stair to a loft door: stringers, treads, a landing on posts,
                 a newel and a handrail
  lean-to        a one-storey lean-to whose single-pitch roof dies into the yard wall
  wing           a flat-roofed connecting wing from the yard wall to the house's rear wall

EVERY PIECE STANDS ON SOMETHING, as in K09 and K10 (whose mesh primitives this module
reuses): an open piece leaves its open edges lying on another surface (a wall's foot on the
ground, a wall's end on the wall it meets, a gable's rake on the roof's underside, a leaf's
edge on its reveal), a closed piece (a hinge, the hoist beam, the coping, a cleat) passes
through what carries it, and nothing lays a face on another face. Openings are holes: the
wall's faces go round them and a reveal lines all their sides. `tools/check_coach_house_kit.py`
measures all of it on the built geometry.

    python3 generators/archetypes/k12_coach_house.py           write the specimen GLB
    python3 generators/archetypes/k12_coach_house.py --check   refuse if it is stale
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

from archetypes.k09_trim import (Mesh, Piece, _basis, _cr, _cross_seg, _in_tri, _newell, _pad,  # noqa: E402
                                 area2, box, prism, tube)
from archetypes.k01_frontage import _dot, _mul, _unit  # noqa: E402
from archetypes.k10_cornices import sweep  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k12_coach_house.json"
GENERATOR = "chicago-4d generators/archetypes/k12_coach_house.py (K12, T-2320)"

X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)

# Role -> material, in a fixed order so the file is the same bytes every run.
ROLE_MATERIAL = {"brick": "brick", "arch": "rubbed_brick", "stone": "dressed_stone", "roof": "slate",
                 "lean_roof": "tarred_felt", "timber": "painted_timber", "stair": "weathered_timber",
                 "sash": "white_sash", "glass": "glass", "iron": "wrought_iron", "paving": "brick_paving",
                 "ground": "ground", "backing": "house_wall"}
BOARD_ROLES = ("ground", "backing")
MATERIALS = {
    "brick": {"color": (0.52, 0.30, 0.22), "roughness": 0.92, "metallic": 0.0},
    "rubbed_brick": {"color": (0.60, 0.33, 0.24), "roughness": 0.85, "metallic": 0.0},
    "dressed_stone": {"color": (0.72, 0.67, 0.58), "roughness": 0.85, "metallic": 0.0},
    "slate": {"color": (0.24, 0.25, 0.28), "roughness": 0.8, "metallic": 0.0},
    "tarred_felt": {"color": (0.21, 0.20, 0.19), "roughness": 1.0, "metallic": 0.0},
    "painted_timber": {"color": (0.30, 0.36, 0.28), "roughness": 0.7, "metallic": 0.0},
    "weathered_timber": {"color": (0.46, 0.40, 0.33), "roughness": 0.9, "metallic": 0.0},
    "white_sash": {"color": (0.86, 0.84, 0.78), "roughness": 0.6, "metallic": 0.0},
    "glass": {"color": (0.06, 0.08, 0.09), "roughness": 0.08, "metallic": 0.0, "double": True},
    "wrought_iron": {"color": (0.07, 0.07, 0.075), "roughness": 0.6, "metallic": 0.6},
    "brick_paving": {"color": (0.45, 0.30, 0.25), "roughness": 0.95, "metallic": 0.0},
    "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0, "metallic": 0.0},
    "house_wall": {"color": (0.62, 0.55, 0.46), "roughness": 0.95, "metallic": 0.0},
}


class VentilatorRefused(ValueError):
    """A variant asked for a roof ventilator with no source showing one (the restriction)."""


def seed_of(component_id: str, index: int, structure_id: str = "k12_coach_house_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


class Frame:
    """A wall's own frame: s along it from `origin` in direction `t`, y up, n out of its
    outer face along `o` (t x Y = o, so a face wound in the frame keeps its side)."""

    def __init__(self, origin, t, o):
        self.O, self.t, self.o = origin, t, o

    def P(self, p):
        s, y, n = p
        return (self.O[0] + self.t[0] * s + self.o[0] * n, self.O[1] + y,
                self.O[2] + self.t[2] * s + self.o[2] * n)

    def V(self, v):
        return (self.t[0] * v[0] + self.o[0] * v[2], v[1], self.t[2] * v[0] + self.o[2] * v[2])

    def apply(self, m: Mesh, start: int = 0):
        m.pos[start:] = [self.P(p) for p in m.pos[start:]]
        m.nrm[start:] = [self.V(v) for v in m.nrm[start:]]


WORLD_E = Frame((0.0, 0.0, 0.0), (0.0, 0.0, -1.0), X)     # s = -z, n = x: sections across the ridge


def triangulate(outer, holes=()):
    """K09's ear clipping with one fix for walls with many openings. K09 bridges each hole
    to the nearest visible vertex of the ring; when two holes bridge to the same vertex it
    appears in the ring twice, and K09 took whichever copy sorted first, which can splice
    the second bridge in outside the polygon and leave no ear to clip. Here a bridge goes
    only to a copy whose interior wedge the bridge enters."""
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
    tau = 2 * math.pi

    def inside_wedge(j, m):
        v, p, n = pts[ring[j]], pts[ring[j - 1]], pts[ring[(j + 1) % len(ring)]]
        an = math.atan2(n[1] - v[1], n[0] - v[0])
        ap = math.atan2(p[1] - v[1], p[0] - v[0])
        ad = math.atan2(m[1] - v[1], m[0] - v[0])
        return 1e-12 < (ad - an) % tau < (ap - an) % tau - 1e-12 or (ap - an) % tau < 1e-12

    rings.sort(key=lambda r: -max(pts[i][0] for i in r))
    for k_, hr in enumerate(rings):
        k = max(range(len(hr)), key=lambda j: (pts[hr[j]][0], pts[hr[j]][1]))
        m = pts[hr[k]]
        blockers = edges(ring) + [e for r in rings[k_:] for e in edges(r)]
        best = None
        for j in sorted(range(len(ring)), key=lambda j: (pts[ring[j]][0] - m[0]) ** 2 + (pts[ring[j]][1] - m[1]) ** 2):
            v = pts[ring[j]]
            if not inside_wedge(j, m):
                continue
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
        if not cut:
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


def face(m: Mesh, outer, hint, holes=()):
    """Mesh.poly, triangulated by the function above."""
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
    base = len(m.pos)
    for p in allp:
        m._vert(p, n, au, av)
    for a, b, c in tris:
        m.idx += [base + a, base + b, base + c]


def slab(m: Mesh, outline, holes, n0, n1, open_edges=()):
    """A wall: `outline` (s, y) carried from n0 to n1 with `holes` cut through it. Its outer
    (n1) and inner (n0) faces go round every hole, a reveal lines each hole, and every edge
    of the outline gets a side face except the `open_edges` (by index), which are left
    open to lie on whatever the wall meets there."""
    outline = list(outline)
    if area2(outline) < 0:
        k = len(outline)
        outline = list(reversed(outline))
        open_edges = {(k - 2 - i) % k for i in open_edges}
    face(m, [(s, y, n1) for s, y in outline], Z, holes=[[(s, y, n1) for s, y in h] for h in holes])
    face(m, [(s, y, n0) for s, y in outline], (0.0, 0.0, -1.0), holes=[[(s, y, n0) for s, y in h] for h in holes])
    for i in range(len(outline)):
        if i in open_edges:
            continue
        a, b = outline[i], outline[(i + 1) % len(outline)]
        out = (b[1] - a[1], -(b[0] - a[0]), 0.0)
        m.poly([(a[0], a[1], n0), (b[0], b[1], n0), (b[0], b[1], n1), (a[0], a[1], n1)], out)
    for h in holes:
        tube(m, h, n0, n1, inward=True)


def segment_arc(s0, s1, head, rise, n=12, extra=0.0):
    """A segmental arch springing at (s0, head) and (s1, head) with `rise`, from s1 over
    the crown to s0, at radius R + extra. Returns the points and (centre, R)."""
    span = s1 - s0
    R = (span * span / 4 + rise * rise) / (2 * rise)
    cs, cy = (s0 + s1) / 2, head + rise - R
    a1 = math.atan2(head - cy, s1 - cs)
    a0 = math.pi - a1
    pts = []
    for i in range(n + 1):
        a = a1 + (a0 - a1) * i / n
        pts.append((cs + (R + extra) * math.cos(a), cy + (R + extra) * math.sin(a)))
    if not extra:
        pts[0], pts[-1] = (s1, head), (s0, head)
    return pts, (cs, cy, R)


class Variant:
    def __init__(self, v, data, origin=(0.0, 0.0, 0.0), index=0):
        self.v, self.data, self.O = v, data, origin
        self.P = data["parts"]
        self.seed = seed_of(v["id"], index)
        self.pieces: list[Piece] = []
        self.walls: dict = {}
        self.meta: dict = {"openings": [], "stands": []}

    def piece(self, name, role, rests, host=None, **meta):
        p = Piece(name, role, rests, host, **meta)
        self.pieces.append(p)
        return p

    # -- the shell ------------------------------------------------------------------------

    def build(self):
        v, P = self.v, self.P
        if v.get("ventilator") and not P["ventilator"].get("evidence"):
            raise VentilatorRefused(f"{v['id']} asks for a roof ventilator and no source shows one "
                                    "(restriction ventilator_needs_evidence)")
        if v.get("ventilator"):
            raise VentilatorRefused(f"{v['id']}: the kit builds no ventilator; a named target with its "
                                    "evidence authors one")
        W, D = v["width_m"], v["depth_m"]
        t, tp = P["wall"]["brick_m"], P["wall"]["brick_m"]
        B = P["basement"]["depth_m"]
        E = P["storeys"]["ground_m"] + P["storeys"]["loft_m"]
        R = P["roof"]
        tan = math.tan(math.radians(R["pitch_deg"]))
        dr = R["thickness_m"] / math.cos(math.radians(R["pitch_deg"]))
        self.dims = dict(W=W, D=D, t=t, tp=tp, B=B, E=E, tan=tan, dr=dr)
        yu = lambda s: E + min(s, D - s) * tan          # roof underside, s back from the alley face
        L = W - tp

        # the alley wall, the yard wall: full length from the party wall to the open gable
        self.wall("alley", Frame((-W / 2 + tp, 0.0, 0.0), X, Z),
                  [(0.0, -B), (L, -B), (L, E), (0.0, E)], t, open_edges={0, 3})
        self.wall("yard", Frame((W / 2, 0.0, -D), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
                  [(0.0, -B), (L, -B), (L, E), (0.0, E)], t, open_edges={0, 1})
        # the open gable: between the eave walls below the eave, over their tops above it
        self.wall("gable", Frame((W / 2, 0.0, 0.0), (0.0, 0.0, -1.0), X),
                  [(t, -B), (D - t, -B), (D - t, E), (D, E), (D / 2, yu(D / 2)), (0.0, E), (t, E)], t,
                  open_edges=set(range(7)))
        # the party wall on the lot line: past both eaves and above the roof by the parapet
        PW = P["party_wall"]
        ret, par = PW["return_m"], PW["parapet_m"]
        Lp = D + 2 * ret
        yt = lambda s: yu(s - ret) + dr + par
        self.wall("party", Frame((-W / 2, 0.0, -D - ret), Z, (-1.0, 0.0, 0.0)),
                  [(0.0, -B), (Lp, -B), (Lp, yt(Lp)), (Lp / 2, yt(Lp / 2)), (0.0, yt(0.0))], tp,
                  open_edges={0})
        xc = -W / 2 + tp / 2
        cop = self.piece("party wall coping", "stone", "rooted", host="party wall")
        sweep(cop.mesh, [(xc, yt(s), s - D - ret) for s in (0.0, Lp / 2, Lp)], X, PW["coping"]["points"],
              closed=True, caps=(True, True))

        # the roof: one slab across the ridge, dying into the party wall, a verge at the gable
        o = R["eave_m"]
        sec = [(-o, yu(-o)), (D / 2, yu(D / 2)), (D + o, yu(D + o)),
               (D + o, yu(D + o) + dr), (D / 2, yu(D / 2) + dr), (-o, yu(-o) + dr)]
        roof = self.piece("roof", "roof", "open")
        prism(roof.mesh, sec, -W / 2 + tp, W / 2 + R["verge_m"], back=False)
        WORLD_E.apply(roof.mesh)
        self.meta["roof"] = {"E": E, "tan": tan, "D": D}

        self.ramp()
        self.stair()
        self.lean_to()
        self.wing()
        for op in v["openings"]:
            self.fit(op)
        self.boards()
        self.stands()
        return self

    def wall(self, key, frame, outline, thick, open_edges=(), name=None):
        name = name or f"{key} wall"
        holes = [self.outline_of(op) for op in self.v["openings"] if op["wall"] == key]
        p = self.piece(name, "brick", "open", wall=key)
        slab(p.mesh, outline, holes, -thick, 0.0, open_edges)
        frame.apply(p.mesh)
        self.walls[key] = {"frame": frame, "thick": thick, "piece": name, "outline": outline}

    def outline_of(self, op):
        s0, s1, y0, y1 = op["s0"], op["s1"], op["sill"], op["head"]
        if op["kind"] == "carriage":
            arc, _ = segment_arc(s0, s1, y1, self.P["carriage"]["rise_m"])
            return [(s0, y0), (s1, y0)] + arc[:-1] + [(s0, y1)]
        return [(s0, y0), (s1, y0), (s1, y1), (s0, y1)]

    # -- what fills an opening --------------------------------------------------------------

    def fit(self, op):
        w = self.walls[op["wall"]]
        fr, O = w["frame"], self.P["opening"]
        s0, s1, y0, y1 = op["s0"], op["s1"], op["sill"], op["head"]
        set_, lf, gap = O["leaf_set_m"], O["leaf_m"], O["meeting_gap_m"]
        n1, n0 = -set_, -set_ - lf
        kind, oid = op["kind"], op["id"]
        self.meta["openings"].append({**op, "thick": w["thick"], "piece": w["piece"]})

        def made(p, start=0):
            fr.apply(p.mesh, start)
            return p

        def strap(leaf, s_hinge, inward, y, length):
            Ld, Wd, Td = self.P["carriage"]["strap"]
            length = min(length, Ld)
            a = s_hinge + 0.03 * inward
            b = a + length * inward
            p = self.piece(f"{leaf.name} strap {round(y - y0, 2)}", "iron", "rooted", host=leaf.name)
            box(p.mesh, min(a, b), max(a, b), y, y + Wd, n1 - 0.006, n1 - 0.006 + Td)
            made(p)

        def pair(top_skip=True, heights=()):
            mid = (s0 + s1) / 2
            for side, (a, b), outer in (("left", (s0, mid - gap / 2), "left"), ("right", (mid + gap / 2, s1), "right")):
                leaf = self.piece(f"{oid} leaf {side}", "timber", "open")
                box(leaf.mesh, a, b, y0, y1, n0, n1, skip=(outer, "bottom", "top") if top_skip else (outer, "bottom"))
                made(leaf)
                for h in heights:
                    strap(leaf, s0 if side == "left" else s1, 1 if side == "left" else -1, y0 + h, 0.75 * (b - a))

        def stone(name, s_a, s_b, y_a, y_b, proud):
            p = self.piece(name, "stone", "open")
            box(p.mesh, s_a, s_b, y_a, y_b, 0.0, proud, skip=("back",))
            made(p)

        if kind == "carriage":
            C = self.P["carriage"]
            pair(heights=C["hinges"])
            arc, (cs, cy, R) = segment_arc(s0, s1, y1, C["rise_m"])
            head = self.piece(f"{oid} head panel", "timber", "open")
            prism(head.mesh, arc, n0, n1, back=True, open_edges=set(range(len(arc) - 1)))
            made(head)
            outer, _ = segment_arc(s0, s1, y1, C["rise_m"], extra=C["ring_m"])
            ring = self.piece(f"{oid} ring", "arch", "open")
            prism(ring.mesh, arc + list(reversed(outer)), 0.0, C["ring_proud_m"], back=False)
            made(ring)
            self.meta["carriage"] = {"clear_m": s1 - s0, "id": oid}
        elif kind == "hatch":
            pair(heights=(0.25, y1 - y0 - 0.31))
            sx, sy, sp = O["sill"]
            stone(f"{oid} sill", s0 - sx, s1 + sx, y0 - sy, y0, sp)
            H = self.P["hoist"]
            bw, bh = H["section"]
            mid = (s0 + s1) / 2
            yb = y1 + H["above_head_m"]
            beam = self.piece(f"{oid} hoist beam", "timber", "rooted", host=w["piece"])
            box(beam.mesh, mid - bw / 2, mid + bw / 2, yb, yb + bh, -H["embed_m"], H["projection_m"])
            made(beam)
            hook = self.piece(f"{oid} hoist hook", "iron", "rooted", host=beam.name)
            e = H["projection_m"] - 0.12
            box(hook.mesh, mid - 0.03, mid + 0.03, yb - 0.25, yb + 0.03, e - 0.03, e + 0.03)
            made(hook)
            self.meta["hoist"] = {"beam": beam.name, "y": yb}
        elif kind in ("door", "dutch"):
            if kind == "door":
                leaf = self.piece(f"{oid} leaf", "timber", "open")
                box(leaf.mesh, s0, s1, y0, y1, n0, n1, skip=("left", "right", "bottom", "top"))
                made(leaf)
                for h in (0.3, y1 - y0 - 0.36):
                    strap(leaf, s0, 1, y0 + h, 0.75 * (s1 - s0))
            else:
                ym = y0 + 1.1
                low = self.piece(f"{oid} lower leaf", "timber", "open")
                box(low.mesh, s0, s1, y0, ym, n0, n1, skip=("left", "right", "bottom"))
                made(low)
                up = self.piece(f"{oid} upper leaf", "timber", "open")
                box(up.mesh, s0, s1, ym, y1, n0, n1, skip=("left", "right", "bottom", "top"))
                made(up)
                strap(low, s0, 1, y0 + 0.3, 0.75 * (s1 - s0))
                strap(up, s0, 1, y1 - 0.36, 0.75 * (s1 - s0))
            lx, ly, lp = O["lintel"]
            stone(f"{oid} lintel", s0 - lx, s1 + lx, y1, y1 + ly, lp)
        elif kind == "sash":
            S = self.P["sash"]
            b, mb = S["bar_m"], S["muntin_m"]
            a1, a0 = -S["set_m"], -S["set_m"] - S["depth_m"]
            sm, ym = (s0 + s1) / 2, (y0 + y1) / 2
            bars = [("stile left", (s0, s0 + b, y0, y1), ("left", "top", "bottom")),
                    ("stile right", (s1 - b, s1, y0, y1), ("right", "top", "bottom")),
                    ("head rail", (s0 + b, s1 - b, y1 - b, y1), ("top", "left", "right")),
                    ("bottom rail", (s0 + b, s1 - b, y0, y0 + b), ("bottom", "left", "right")),
                    ("meeting rail", (s0 + b, s1 - b, ym - mb / 2, ym + mb / 2), ("left", "right")),
                    ("muntin lower", (sm - mb / 2, sm + mb / 2, y0 + b, ym - mb / 2), ("top", "bottom")),
                    ("muntin upper", (sm - mb / 2, sm + mb / 2, ym + mb / 2, y1 - b), ("top", "bottom"))]
            for name, (xa, xb, ya, yb), skip in bars:
                p = self.piece(f"{oid} {name}", "sash", "open")
                box(p.mesh, xa, xb, ya, yb, a0, a1, skip=skip)
                made(p)
            zg = (a0 + a1) / 2
            for k, (xa, xb, ya, yb) in enumerate(((s0 + b, sm - mb / 2, y0 + b, ym - mb / 2),
                                                  (sm + mb / 2, s1 - b, y0 + b, ym - mb / 2),
                                                  (s0 + b, sm - mb / 2, ym + mb / 2, y1 - b),
                                                  (sm + mb / 2, s1 - b, ym + mb / 2, y1 - b))):
                p = self.piece(f"{oid} pane {k + 1}", "glass", "open")
                p.mesh.poly([(xa, ya, zg), (xb, ya, zg), (xb, yb, zg), (xa, yb, zg)], Z)
                made(p)
            sx, sy, sp = O["sill"]
            stone(f"{oid} sill", s0 - sx, s1 + sx, y0 - sy, y0, sp)
            lx, ly, lp = O["lintel"]
            stone(f"{oid} lintel", s0 - lx, s1 + lx, y1, y1 + ly, lp)
        else:
            raise ValueError(f"{oid}: no builder for an opening of kind {kind!r}")

    # -- the ramp to the basement -----------------------------------------------------------

    def ramp(self):
        d, RP, r = self.dims, self.P["ramp"], self.v["ramp"]
        D, B = d["D"], d["B"]
        x0, x1 = r["x0"], r["x0"] + RP["width_m"]
        fall, grade = r["fall_m"], r["grade"]
        run = fall / grade
        zl = -D - RP["landing_m"]
        zt = zl - run
        tw, curb = RP["retaining_m"], RP["curb_m"]
        for side, (a, b) in (("west", (x0 - tw, x0)), ("east", (x1, x1 + tw))):
            p = self.piece(f"ramp retaining wall {side}", "brick", "open")
            box(p.mesh, a, b, -B, curb, zt, -D, skip=("front", "bottom"))
        p = self.piece("ramp", "paving", "open")
        p.mesh.poly([(x0, 0.0, zt), (x0, -fall, zl), (x1, -fall, zl), (x1, 0.0, zt)], Y)
        L = math.hypot(run, fall)
        cw, ch = RP["cleat"]
        n = int((L - 0.3) // RP["cleat_pitch_m"])
        for k in range(1, n + 1):
            q = k * RP["cleat_pitch_m"] / L
            zc = zl - run * q
            yc = -fall + fall * q
            c = self.piece(f"ramp cleat {k}", "timber", "rooted", host="ramp")
            box(c.mesh, x0 + 0.05, x1 - 0.05, yc - ch, yc + ch, zc - cw / 2, zc + cw / 2)
        self.meta["ramp"] = {"x": (x0, x1), "zt": zt, "zl": zl, "fall": fall, "grade": grade, "cleats": n}

    # -- the stair to the loft door ---------------------------------------------------------

    def stair(self):
        d, SP, st = self.dims, self.P["stair"], self.v["stair"]
        W = d["W"]
        g, r, nose, tt = SP["going_m"], st["rise_m"], SP["nosing_m"], SP["tread_m"]
        n = st["risers"]
        yL = n * r
        ss = st["foot_s"]
        sw, sd = SP["stringer"]
        width = SP["width_m"]
        Ll, Lt = SP["landing"]
        c = 0.06
        cosa = g / math.hypot(g, r)
        drop = sd / cosa
        sL0 = ss + (n - 1) * g
        ytop = lambda s: (s - ss) * (r / g) + r + c
        sa = ss - (r + c) * g / r
        sb = sa + drop * g / r
        st_ = ss + (yL - r - c) * g / r
        poly = [(sa, 0.0), (sb, 0.0), (sL0, ytop(sL0) - drop), (sL0, yL), (st_, yL)]
        xs = W / 2
        for name, (a, b), back in (("stringer wall", (xs, xs + sw), False),
                                   ("stringer outer", (xs + width - sw, xs + width), True)):
            p = self.piece(name, "stair", "open")
            prism(p.mesh, poly, a, b, back=back, open_edges={0, 2})
            WORLD_E.apply(p.mesh)
        for k in range(1, n):
            p = self.piece(f"tread {k}", "stair", "open")
            skip = ("left", "right", "back") if k == n - 1 else ("left", "right")
            box(p.mesh, xs + sw, xs + width - sw, k * r - tt, k * r, -(ss + k * g), -(ss + (k - 1) * g - nose),
                skip=skip)
        land = self.piece("landing", "stair", "open")
        xo = xs + width + 0.14
        box(land.mesh, xs, xo, yL - Lt, yL, -(sL0 + Ll), -sL0, skip=("left",))
        pw = 0.08
        hr = SP["rail_m"]
        for k, (za, zb) in enumerate(((-sL0 - pw, -sL0), (-sL0 - Ll, -sL0 - Ll + pw))):
            p = self.piece(f"landing post {k + 1}", "stair", "open")
            box(p.mesh, xo - pw, xo, 0.0, yL - Lt, za, zb, skip=("top", "bottom"))
            p = self.piece(f"rail post {k + 1}", "stair", "open")
            box(p.mesh, xo - pw, xo, yL, yL + hr + 0.15, za, zb, skip=("bottom",))
        ra, rb = xo - pw + 0.01, xo - 0.01
        p = self.piece("landing rail", "stair", "open")
        box(p.mesh, ra, rb, yL + hr + 0.06, yL + hr + 0.12, -sL0 - Ll + pw, -sL0 - pw, skip=("front", "back"))
        p = self.piece("landing end rail", "stair", "open")
        box(p.mesh, xs, xo - pw, yL + hr + 0.06, yL + hr + 0.12, -sL0 - Ll + 0.01, -sL0 - Ll + pw - 0.01,
            skip=("left", "right"))
        sn = 0.10
        newel = self.piece("newel", "stair", "open")
        box(newel.mesh, xo - pw, xo, 0.0, 1.1, -(sn + pw), -sn, skip=("bottom",))
        h = lambda s: (s - ss) * (r / g) + r + hr
        se = sn + pw
        rail = self.piece("handrail", "stair", "open")
        prism(rail.mesh, [(se, h(se) - 0.06), (sL0, h(sL0) - 0.06), (sL0, h(sL0)), (se, h(se))], ra, rb,
              back=True, open_edges={1, 3})
        WORLD_E.apply(rail.mesh)
        self.meta["stair"] = {"risers": n, "rise": r, "going": g, "landing_y": yL, "foot": sa}

    # -- the lean-to and the wing -----------------------------------------------------------

    def lean_to(self):
        d, LP, lv = self.dims, self.P["lean_to"], self.v["lean_to"]
        D = d["D"]
        x0, x1, dl, yh = lv["x0"], lv["x1"], lv["depth_m"], lv["high_m"]
        lt = self.P["wall"]["service_brick_m"]
        tan = math.tan(math.radians(LP["pitch_deg"]))
        yl = yh - dl * tan
        self.wall("lean_to", Frame((x1, 0.0, -D - dl), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
                  [(0.0, 0.0), (x1 - x0, 0.0), (x1 - x0, yl), (0.0, yl)], lt, open_edges={0},
                  name="lean-to front wall")
        self.wall("lean_to_east", Frame((x1, 0.0, -D), (0.0, 0.0, -1.0), X),
                  [(0.0, 0.0), (dl - lt, 0.0), (dl - lt, yl), (dl, yl), (0.0, yh)], lt,
                  open_edges=set(range(5)), name="lean-to east wall")
        self.wall("lean_to_west", Frame((x0, 0.0, -D - dl), Z, (-1.0, 0.0, 0.0)),
                  [(lt, 0.0), (dl, 0.0), (dl, yh), (0.0, yl), (lt, yl)], lt,
                  open_edges=set(range(5)), name="lean-to west wall")
        e, dr = LP["eave_m"], LP["thickness_m"] / math.cos(math.radians(LP["pitch_deg"]))
        ye = yh - (dl + e) * tan
        roof = self.piece("lean-to roof", "lean_roof", "open")
        prism(roof.mesh, [(D, yh), (D + dl + e, ye), (D + dl + e, ye + dr), (D, yh + dr)],
              x0 - LP["verge_m"], x1 + LP["verge_m"], back=True, open_edges={3})
        WORLD_E.apply(roof.mesh)

    def wing(self):
        d, WP, wv = self.dims, self.P["wing"], self.v["wing"]
        D = d["D"]
        x0, x1, Lw, yw = wv["x0"], wv["x1"], wv["length_m"], wv["height_m"]
        wt = self.P["wall"]["service_brick_m"]
        rect = [(0.0, 0.0), (Lw, 0.0), (Lw, yw), (0.0, yw)]
        self.wall("wing_east", Frame((x1, 0.0, -D), (0.0, 0.0, -1.0), X), rect, wt,
                  open_edges=set(range(4)), name="wing east wall")
        self.wall("wing_west", Frame((x0, 0.0, -D - Lw), Z, (-1.0, 0.0, 0.0)), rect, wt,
                  open_edges=set(range(4)), name="wing west wall")
        ov = WP["overhang_m"]
        roof = self.piece("wing roof", "lean_roof", "open")
        box(roof.mesh, x0 - ov, x1 + ov, yw, yw + WP["roof_m"], -D - Lw, -D, skip=("front", "back"))
        self.meta["wing"] = {"z_house": -D - Lw}

    # -- the specimen lot --------------------------------------------------------------------

    def boards(self):
        d = self.dims
        W, D, tp, B = d["W"], d["D"], d["tp"], d["B"]
        ret = self.P["party_wall"]["return_m"]
        rm = self.meta["ramp"]
        (rx0, rx1), zt = rm["x"], rm["zt"]
        hole = [(-W / 2, ret), (-W / 2 + tp, ret), (-W / 2 + tp, 0.0), (W / 2, 0.0), (W / 2, -D), (rx1, -D),
                (rx1, zt), (rx0, zt), (rx0, -D), (-W / 2 + tp, -D), (-W / 2 + tp, -D - ret), (-W / 2, -D - ret)]
        x_lo, x_hi, z_lo, z_hi = -W / 2 - 16.0, W / 2 + 16.0, zt - 14.0, ret + 18.0     # past every stand
        g = self.piece("ground (board)", "ground", "board")
        face(g.mesh, [(x_lo, 0.0, z_hi), (x_hi, 0.0, z_hi), (x_hi, 0.0, z_lo), (x_lo, 0.0, z_lo)], Y,
                    holes=[[(x, 0.0, z) for x, z in hole]])
        f = self.piece("basement floor (board)", "ground", "board")
        f.mesh.poly([(-W / 2 - 0.1, -B, ret + 0.1), (W / 2 + 0.1, -B, ret + 0.1), (W / 2 + 0.1, -B, zt - 0.1),
                     (-W / 2 - 0.1, -B, zt - 0.1)], Y)
        wv = self.v["wing"]
        zh = self.meta["wing"]["z_house"]
        h = self.piece("house rear wall (board)", "backing", "board")
        box(h.mesh, wv["x0"] - 0.7, wv["x1"] + 0.7, 0.0, 4.6, zh - 0.33, zh, skip=("bottom",))
        self.meta["head"] = max(q[1] for p in self.pieces for q in p.mesh.pos)

    def stands(self):
        """The study's stands: (name, eye, target, light). Near ones at 2-5 m from the part."""
        d = self.dims
        W, D, E = d["W"], d["D"], d["E"]
        rm = self.meta["ramp"]
        cx = (rm["x"][0] + rm["x"][1]) / 2
        cb = next(o for o in self.meta["openings"] if o["id"] == "carriage")
        cs = cb["s0"] - (W / 2 - d["tp"]) + (cb["s1"] - cb["s0"]) / 2
        self.meta["stands"] = [
            ("alley front, 14 m", (0.5, 1.6, 14.0), (0.0, 4.2, -3.0), "diffuse"),
            ("alley oblique, 15 m, raking sun", (12.0, 2.0, 9.5), (0.0, 4.0, -3.3), "raking"),
            ("yard side, 17 m", (-2.0, 2.4, -24.0), (0.0, 3.0, -8.0), "diffuse"),
            ("gable and stair, 12 m", (16.0, 1.8, -1.0), (W / 2, 3.6, -3.4), "diffuse"),
            ("from above, 40 degrees", (14.0, 17.0, 12.0), (0.0, 3.0, -6.0), "diffuse"),
            ("carriage bay, 3 m, raking", (cs + 1.4, 1.6, 2.7), (cs, 1.7, 0.0), "raking"),
            ("loft hatch and hoist, 4 m", (cs + 2.6, 3.4, 3.2), (cs, 5.0, 0.3), "diffuse"),
            ("party wall return and coping, 4 m", (-W / 2 - 2.6, E + 2.4, 3.0), (-W / 2, E + 0.4, 0.2), "diffuse"),
            ("stair foot and landing, 4 m", (W / 2 + 3.6, 1.7, 1.2), (W / 2 + 0.5, 1.6, -2.2), "raking"),
            ("ramp to the basement, 4 m", (cx + 2.6, 1.7, rm["zl"] - 4.6), (cx, -0.9, rm["zl"] - 0.8), "diffuse"),
            ("lean-to and its stable door, 4 m", (2.6, 1.7, -D - 5.6), (0.5, 1.6, -D - 2.2), "diffuse"),
            ("wing door, from the workyard, 3 m", (1.2, 1.7, -D - 4.6), (-1.4, 1.5, -D - 3.15), "diffuse"),
        ]
        self.meta["focus"] = [0.0, E / 2, 0.0]


def load() -> dict:
    return json.loads(DATA.read_text())


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0) -> Variant:
    return Variant(v, data, origin, index).build()


def build_kit(data: dict | None = None) -> list[Variant]:
    data = data or load()
    return [build_variant(v, data, index=i) for i, v in enumerate(data["variants"])]


def triangles(var: Variant, include_board: bool = False) -> int:
    return sum(p.mesh.triangles() for p in var.pieces if include_board or p.role not in BOARD_ROLES)


# -- glTF -------------------------------------------------------------------------------------

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
    materials_out = []
    for n in mat_names:
        m = {"name": f"k12_{n}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in MATERIALS[n]["color"]], 1.0],
            "metallicFactor": MATERIALS[n]["metallic"], "roughnessFactor": MATERIALS[n]["roughness"]}}
        if MATERIALS[n].get("double"):
            m["doubleSided"] = True
        materials_out.append(m)
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
        top = max(q[1] for p in var.pieces for q in p.mesh.pos)
        r4 = lambda q: [round(c, 4) for c in q]
        nodes.append({"name": var.v["id"], "mesh": len(meshes) - 1, "extras": {
            "component_id": var.v["id"], "family": "service", "kind": var.v["kind"],
            "seed": var.seed, "origin": r4(var.O),
            "pieces": sum(1 for p in var.pieces if p.role not in BOARD_ROLES),
            "triangles_kit": triangles(var), "triangles_with_board": triangles(var, True),
            "head_m": round(var.meta["head"], 4), "focus": r4(var.meta["focus"]),
            "stands": [{"name": n, "eye": r4(e), "at": r4(a), "light": li} for n, e, a, li in var.meta["stands"]],
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
        "extras": {"k12": {"data": "data/components/prairie_1904/k12_coach_house.json", "ticket": "T-2320",
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k12_coach_house.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
