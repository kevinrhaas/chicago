"""A frontage built from K01 components, written straight to glTF — no Blender.

TICKET T-2266: the first assembly built to the Prairie 1904 K01 metric component
contract (`data/components/prairie_1904/k01_contract.json`), beside the canonical
Glessner asset it is measured against.

WHY PURE PYTHON. The contract's measures are about vertices — 1 mm grid identity,
no doubled or back-to-back faces, the envelope on the footprint, metric UVs — and
every one of them is easier to HOLD when this module writes the vertices itself
than when an exporter re-indexes, re-normals and re-orders them. It also keeps
this asset out of `generators/emit.py`, whose bytes are in the input hash of all
704 baked meshes: registering an archetype there would stale the whole town for a
change that moves none of its vertices (the false positive T-1654 split that file
to remove). `generators/k01_emit.py` is the command; `mesh_inputs` hashes this
module and its parameter module, and nothing else, for this archetype.

THE COMPONENTS (k01_contract.json `families`), each built about its own socket:

  k01.wall.street_front     the stone front, its openings cut through it
  k01.wall.side.north       the party side against the Glessner court: blank brick
  k01.wall.side.south       common brick, four bays a storey
  k01.wall.rear_service     common brick, two bays a storey
  k01.opening.sash_flat     reveal, sash ring, meeting rail, glass, dark backing,
                            stone sill and flat lintel
  k01.opening.area_light    the basement lights: the same, no meeting rail
  k01.opening.door_leaf     reveal, threshold and a recessed oak leaf
  k01.stair.straight_stoop  whole risers from the walk to the principal floor
  k01.roof.hip              four planes on true hips, fascia and soffit; since
                            T-2293 slated from the K04 library (courses registered
                            at the eave, a cut edge and its underside), copper
                            rolls on every hip and the ridge, a half-round gutter
                            on iron brackets round the eave, outlets, downpipes
                            and shoes over splash stones at grade
  k01.roof.dormer_gable     the front dormer: slated cheeks and roof, a stone face
                            with its sash, bargeboards and verge soffits, copper
                            ridge roll, open valleys, apron and step flashing
  k01.wall.dormer_face      the dormer's face, its sash cut through it

  and, since T-2289, the stone street front laid from the K02 stone library
  (`data/components/prairie_1904/k02_stone_profiles.json`, read through the record's
  `stone_front`) instead of drawn as one flat face:

  k01.wall.stone_course     one course of the street front: rock-faced blocks of its
                            own height, each sampling its own window of the fabric
                            (seeded offset and mirror), joints recessed to the
                            mortar, a bevelled arris and sparse chipped corners
  k01.wall.rusticated_base  the base courses, channel-jointed
  k01.wall.coping           the weathered coping over the base: fall, overhang and a
                            drip groove under its nose
  k01.wall.corner_bond      a quoin on the south return, long and short in turn
                            against the front's own corner stone
  k01.opening.flat_arch     voussoirs over every front opening, their joints radiating
                            and each stone's bed turned along its radial joint

A wall is the cell grid its openings cut, so no face is ever drawn twice and no
cell straddles an opening edge (T-junction free inside the wall). Faces that sit
against another surface — a stone's back on the wall, the stoop's back and
bottom — are not emitted at all: a hidden face is the back-to-back coincidence
the contract's measure refuses.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "assets" / "textures" / "glessner-v4"
ROOFS = ROOT / "assets" / "textures" / "prairie_1904_roofs"   # K04, T-2292
STONE = ROOT / "assets" / "textures" / "prairie_1904_stone"   # K02, T-2288
GENERATOR = "chicago-4d generators/archetypes/k01_frontage.py (K01, T-2266)"

Y = (0.0, 1.0, 0.0)


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


def seed_of(structure_id: str, component_id: str, index: int) -> int:
    """k01_contract.json `seed.rule`, verbatim."""
    h = hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()
    return int(h[:8], 16)


# The material slots. A fabric names the library image whose `tile_m` the UVs are
# divided by (k01_contract.json scale_uv); the rest are flat colours. Names matter
# to the contract's measure: walls the envelope reads begin with an envelope
# material (`^(granite|brick|limestone_trim|rough_stone_trim|mortar)`), and the
# stoop — which stands proud of the front by metres — must NOT, or the envelope
# would read the stair as wall.
MATERIALS = {
    "rough_stone_trim": {"fabric": "limestone", "color": (0.90, 0.85, 0.76), "roughness": 0.92},
    "brick": {"fabric": "brick", "color": (1.0, 0.985, 0.94), "roughness": 0.9},  # Glessner's brick_buff
    "limestone_trim": {"fabric": "limestone", "color": (1.0, 0.97, 0.90), "roughness": 0.85},
    # T-2289: what a K02 joint is recessed to — Glessner's sandy lime, as the profiles say
    "mortar": {"fabric": "mortar", "color": (1.0, 1.0, 1.0), "roughness": 0.95},
    "stoop_stone": {"fabric": "limestone", "color": (0.95, 0.92, 0.86), "roughness": 0.88},
    "sash": {"color": (0.12, 0.19, 0.14), "roughness": 0.6},
    "glass": {"color": (0.045, 0.055, 0.065), "roughness": 0.08},
    "backing": {"color": (0.018, 0.017, 0.016), "roughness": 1.0},
    "door_leaf": {"color": (0.29, 0.17, 0.085), "roughness": 0.62},
    "fascia": {"color": (0.27, 0.24, 0.20), "roughness": 0.7},
    # T-2293: the K04 roof. The covering's fabric is the record's (roof_covering), so
    # this entry's is only a default; flashing and rainwater are named by fabric.
    "slate_covering": {"fabric": "slate_pennsylvania", "color": (1.0, 1.0, 1.0), "roughness": 0.62},
    # the dormer face: dressed stone a shade off the trim, and a name outside the
    # envelope materials, since the envelope is the walls and not what stands on the roof
    "dormer_stone": {"fabric": "limestone", "color": (0.96, 0.93, 0.86), "roughness": 0.8},
    "k04_copper_sheet": {"fabric": "copper_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.48, "metallic": 0.3},
    "k04_lead_sheet": {"fabric": "lead_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.7, "metallic": 0.2},
    "k04_zinc_sheet": {"fabric": "zinc_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.6, "metallic": 0.3},
    "k04_painted_tin_sheet": {"fabric": "painted_tin_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.6},
    "iron": {"color": (0.055, 0.055, 0.06), "roughness": 0.55},
}


def _tiles() -> dict:
    lib = json.loads((LIBRARY / "material-library.json").read_text())["materials"]
    out = {m["name"]: tuple(m["tile_m"]) for m in lib}
    for m in json.loads((ROOFS / "manifest.json").read_text())["materials"]:
        out[m["id"]] = tuple(m["tile_m"])
    for m in json.loads((STONE / "manifest.json").read_text())["materials"]:
        out[m["id"]] = tuple(m["tile_m"])
    return out


def _k04_fabric(fab: str) -> dict | None:
    """A K04 fabric's material.json, or None for a Glessner-library fabric."""
    f = ROOFS / fab / "material.json"
    return json.loads(f.read_text()) if f.exists() else None


def _k02_fabric(fab: str) -> dict | None:
    """A K02 stone fabric's material.json (T-2289), or None."""
    f = STONE / fab / "material.json"
    return json.loads(f.read_text()) if f.exists() else None


def _inset(poly, dist):
    """A convex (s, y) polygon, counter-clockwise, each edge moved inward by its own
    distance (`dist[i]` for the edge from vertex i to i + 1): the moved edges' meets."""
    n = len(poly)
    lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ex, ey)
        ex, ey = ex / ln, ey / ln
        lines.append(((a[0] - ey * dist[i], a[1] + ex * dist[i]), (ex, ey)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def _lay(rng, a, b, lo, hi, first=None, avoid=()):
    """Cut a run [a, b] into stones of lo..hi metres, the first `first` long when the
    run starts on a bonded corner; joints kept 0.1 m off the course below's where
    twelve draws allow (a straight joint through two courses is the fault to avoid)."""
    best = None
    for _ in range(12):
        cuts, x = [], a
        if first is not None and (b - a - first >= lo or abs(b - a - first) < 1e-9):
            x = a + first
            if b - x > 1e-9:
                cuts.append(x)
        while b - x > hi:
            x += rng.uniform(lo, min(hi, b - x - lo))
            cuts.append(x)
        score = min((abs(c - v) for c in cuts for v in avoid), default=1.0)
        if best is None or score > best[0]:
            best = (score, cuts)
        if score >= 0.1:
            break
    edges = [a, *best[1], b]
    return list(zip(edges[:-1], edges[1:]))


class Prim:
    """One primitive: one material, flat-shaded faces, metric UVs, a confidence."""

    def __init__(self, name: str):
        self.name = name
        self.pos, self.nrm, self.uv, self.conf, self.idx = [], [], [], [], []

    def face(self, pts, normal, basis, conf):
        """A convex planar polygon. `basis` = (origin, u axis, v axis, tile_u, tile_v,
        offset_u, offset_v): TEXCOORD_0 is metres along each axis over the tile."""
        n = (0.0, 0.0, 0.0)
        for i, a in enumerate(pts):  # Newell: the polygon's own winding
            b = pts[(i + 1) % len(pts)]
            n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                         (a[0] - b[0]) * (a[1] + b[1])))
        if _dot(n, normal) < 0:
            pts = list(reversed(pts))
        o, au, av, tu, tv, ou, ov = basis
        base = len(self.pos)
        for p in pts:
            d = _sub(p, o)
            self.pos.append(p)
            self.nrm.append(normal)
            # glTF's v runs down the image, so height goes in negated: courses upright
            self.uv.append((_dot(d, au) / tu + ou, -_dot(d, av) / tv + ov))
            self.conf.append(conf)
        for i in range(1, len(pts) - 1):
            self.idx += [base, base + i, base + i + 1]

    def quad(self, a, b, c, d, hint, basis, conf):
        """Two triangles, each with its own true normal turned towards `hint`: a
        strip that is not quite planar (a gutter falling into a mitre) stays honest."""
        for t in ((a, b, c), (a, c, d)):
            n = _cross(_sub(t[1], t[0]), _sub(t[2], t[0]))
            if _dot(n, n) < 1e-18:
                continue
            n = _unit(n)
            self.face(list(t), n if _dot(n, hint) >= 0 else _mul(n, -1), basis, conf)


class Assembly:
    def __init__(self, structure_id: str, params):
        self.sid = structure_id
        self.p = params
        self.tiles = _tiles()
        self.prims: dict[str, Prim] = {}
        self.components: dict[str, dict] = {}
        self.fabric = {k: v.get("fabric") for k, v in MATERIALS.items()}
        if params.roof:
            self.fabric["slate_covering"] = params.roof["covering"]
        # T-2289: a coursed stone front lays its walling and its trim in K02 fabrics,
        # whose maps carry their own colour, so the factors go to white
        self.spec = {k: dict(v) for k, v in MATERIALS.items()}
        if params.stone:
            st = params.stone
            for slot, fab, rough in (("rough_stone_trim", st["fabric"], st["fabric_roughness"]),
                                     ("limestone_trim", st["trim"], st["trim_roughness"])):
                self.fabric[slot] = fab
                self.spec[slot] |= {"color": (1.0, 1.0, 1.0), "roughness": rough}

    def prim(self, name):
        if name not in self.prims:
            self.prims[name] = Prim(name)
        return self.prims[name]

    def instance(self, cid, family, params, sockets):
        """Register one instance of a component; return its seed."""
        c = self.components.setdefault(cid, {"id": cid, "family": family, "instances": []})
        i = len(c["instances"])
        seed = seed_of(self.sid, cid, i)
        c["instances"].append({"index": i, "seed": seed,
                               "params": {k: round(v, 4) if isinstance(v, float) else v
                                          for k, v in params.items()},
                               "sockets": {k: [round(x, 4) for x in v] for k, v in sockets.items()}})
        return seed

    def basis(self, mat, origin, au, av, seed, course_v=None):
        fab = self.fabric[mat]
        tu, tv = self.tiles[fab] if fab else (1.0, 1.0)
        # the seed moves the fabric, so two instances of one component differ
        ov = (seed >> 16) / 65536.0
        if course_v is not None:
            # T-2293: a coursed covering is NOT moved up the slope: its first butt is put
            # on the origin (the eave), by the map's own course phase, so a course is
            # never cut at the eave and every course is a whole exposure
            ov = (-course_v / tv) % 1.0
        return (origin, au, av, tu, tv, (seed & 0xFFFF) / 65536.0, ov)

    # -- boxes proud of a wall: front, top, bottom and ends; never the back --------
    def proud_box(self, mat, frame, s0, s1, y0, y1, d, seed, conf):
        O, R, N = frame
        P = lambda s, y, dd: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, dd))
        b = self.basis(mat, O, R, Y, seed)
        pr = self.prim(mat)
        pr.face([P(s0, y0, d), P(s1, y0, d), P(s1, y1, d), P(s0, y1, d)], N, b, conf)
        bh = self.basis(mat, O, R, N, seed)
        pr.face([P(s0, y1, 0), P(s1, y1, 0), P(s1, y1, d), P(s0, y1, d)], Y, bh, conf)
        pr.face([P(s0, y0, 0), P(s1, y0, 0), P(s1, y0, d), P(s0, y0, d)], _mul(Y, -1), bh, conf)
        be = self.basis(mat, O, N, Y, seed)
        pr.face([P(s0, y0, 0), P(s0, y0, d), P(s0, y1, d), P(s0, y1, 0)], _mul(R, -1), be, conf)
        pr.face([P(s1, y0, 0), P(s1, y0, d), P(s1, y1, d), P(s1, y1, 0)], R, be, conf)

    # -- k01.wall.* ----------------------------------------------------------------
    def wall(self, cid, mat, O, R, length, height, thickness, holes, extra_breaks=(), bands=()):
        p = self.p
        N = _cross(R, Y)
        conf = p.worst_conf("footprint", "stories", "storey_heights_m", "construction")
        seed = self.instance(cid, "wall", {"length_m": length, "height_m": height,
                                           "thickness_m": thickness, "construction": "masonry",
                                           "openings": len(holes)},
                             {"base": O, "top": _add(O, _mul(Y, height))})
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        sb = sorted({0.0, length, *[e for h in holes for e in (h[0], h[1])]})
        yb = sorted({0.0, height, *extra_breaks, *[e for h in holes for e in (h[2], h[3])]})
        b = self.basis(mat, O, R, Y, seed)
        pr = self.prim(mat)
        for i in range(len(sb) - 1):
            for j in range(len(yb) - 1):
                sc, yc = (sb[i] + sb[i + 1]) / 2, (yb[j] + yb[j + 1]) / 2
                if any(h[0] < sc < h[1] and h[2] < yc < h[3] for h in holes):
                    continue
                pr.face([P(sb[i], yb[j], 0), P(sb[i + 1], yb[j], 0),
                         P(sb[i + 1], yb[j + 1], 0), P(sb[i], yb[j + 1], 0)], N, b, conf)
        for (y0, y1, proud) in bands:  # belt courses, part of the wall component
            self.proud_box("limestone_trim", (O, R, N), 0.0, length, y0, y1, proud, seed, conf)
        return (O, R, N), thickness

    # -- k01.opening.* ---------------------------------------------------------------
    def opening(self, op, frame, thickness, body_mat, stone_trim, coursed=False):
        p = self.p
        O, R, N = frame
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        s0, s1 = op.s_m - op.width_m / 2, op.s_m + op.width_m / 2
        y0, y1 = op.sill_m, op.head_m
        conf = p.worst_conf("footprint", "sash_by_storey", "front_bays", "side_bays", "rear_bays")
        door = op.component == "k01.opening.door_leaf"
        recess = 0.22 if door else thickness
        seed = self.instance(op.component, "opening",
                             {"clear_width_m": op.width_m, "clear_height_m": op.height_m,
                              "reveal_m": recess, "wall": op.wall},
                             {"sill": P(op.s_m, y0, 0), "head": P(op.s_m, y1, 0),
                              "sash_plane": P(op.s_m, y0, -0.10)})
        # the reveal, in the wall's own body
        pr = self.prim(body_mat)
        bj = self.basis(body_mat, O, N, Y, seed)
        bh = self.basis(body_mat, O, R, N, seed)
        pr.face([P(s0, y0, 0), P(s0, y0, -recess), P(s0, y1, -recess), P(s0, y1, 0)], R, bj, conf)
        pr.face([P(s1, y0, 0), P(s1, y0, -recess), P(s1, y1, -recess), P(s1, y1, 0)], _mul(R, -1), bj, conf)
        pr.face([P(s0, y1, 0), P(s1, y1, 0), P(s1, y1, -recess), P(s0, y1, -recess)], _mul(Y, -1), bh, conf)
        sill_mat = "stoop_stone" if door else body_mat
        self.prim(sill_mat).face([P(s0, y0, 0), P(s1, y0, 0), P(s1, y0, -recess), P(s0, y0, -recess)], Y,
                                 self.basis(sill_mat, O, R, N, seed), conf)
        if door:
            self.prim("door_leaf").face([P(s0, y0, -recess), P(s1, y0, -recess), P(s1, y1, -recess),
                                         P(s0, y1, -recess)], N, self.basis("door_leaf", O, R, Y, seed), conf)
        else:
            self.prim("backing").face([P(s0, y0, -recess), P(s1, y0, -recess), P(s1, y1, -recess),
                                       P(s0, y1, -recess)], N, self.basis("backing", O, R, Y, seed), conf)
            # the sash: a ring at the sash plane, a meeting rail, glass just behind it
            r, f, g = 0.10, 0.065, 0.03
            sp = self.prim("sash")
            bs = self.basis("sash", O, R, Y, seed)
            ring = [(s0, s1, y0, y0 + f), (s0, s1, y1 - f, y1), (s0, s0 + f, y0 + f, y1 - f),
                    (s1 - f, s1, y0 + f, y1 - f)]
            if op.meeting_rail:
                ym = (y0 + y1) / 2
                ring.append((s0 + f, s1 - f, ym - 0.028, ym + 0.028))
            for (a, b_, c, d) in ring:
                sp.face([P(a, c, -r), P(b_, c, -r), P(b_, d, -r), P(a, d, -r)], N, bs, conf)
            bi = self.basis("sash", O, N, Y, seed)
            bih = self.basis("sash", O, R, N, seed)
            ia, ib, ic, id_ = s0 + f, s1 - f, y0 + f, y1 - f
            sp.face([P(ia, ic, -r), P(ia, ic, -r - g), P(ia, id_, -r - g), P(ia, id_, -r)], R, bi, conf)
            sp.face([P(ib, ic, -r), P(ib, ic, -r - g), P(ib, id_, -r - g), P(ib, id_, -r)], _mul(R, -1), bi, conf)
            sp.face([P(ia, id_, -r), P(ib, id_, -r), P(ib, id_, -r - g), P(ia, id_, -r - g)], _mul(Y, -1), bih, conf)
            sp.face([P(ia, ic, -r), P(ib, ic, -r), P(ib, ic, -r - g), P(ia, ic, -r - g)], Y, bih, conf)
            self.prim("glass").face([P(ia, ic, -r - g), P(ib, ic, -r - g), P(ib, id_, -r - g),
                                     P(ia, id_, -r - g)], N, self.basis("glass", O, R, Y, seed), conf)
            # a stone sill, proud of the face (a coursed front lays its own: T-2289)
            if not coursed:
                self.proud_box(stone_trim, frame, s0 - 0.08, s1 + 0.08, y0 - 0.10, y0, 0.06, seed, conf)
        # a flat lintel over every opening; a coursed front's is a flat arch (T-2289)
        if not coursed:
            self.proud_box(stone_trim, frame, s0 - 0.12, s1 + 0.12, y1, y1 + 0.30, 0.03, seed, conf)

    # -- K02 masonry: the coursed stone front (T-2289) -------------------------------
    # Every number below a stone is laid to — course height, block length, joint,
    # recess, arris bevel, chips, rock-faced projection, quoin return, channel, the
    # coping's fall, overhang and drip — is the K02 profile's, resolved into
    # `params.stone` by k01_frontage_params._k02. What is this module's own: the slip
    # sill's 0.10 m and 0.06 m, the flat arch's 0.12 m seat, 0.30 m depth and ~0.2 m
    # voussoirs, and the trim's projection — the K01 lintel and sill they replace,
    # carried over — and they are said in docs/LIBERTIES.md L-k02-1808-stone-2289.

    def _stone_seed(self, cid, inst, j):
        """k01_contract.json seed rule, one level down: a stone's seed is its
        component id, the component's instance and the stone's index in it."""
        return seed_of(self.sid, f"{cid}#{inst}", j)

    def _sface(self, mat, pts, hint, origin, bed, seed, mirror, conf, project=True):
        """One planar face of a stone: its true normal turned towards `hint`, its UVs
        metres along the stone's bed (u) and across it (v) from the stone's own
        origin, so every face of one stone samples one window of the fabric. A face
        tilted off the wall (a bevel, a sill's top) projects the bed into its own
        plane, which keeps it metric; a rock face's facets take the wall's own axes,
        which keeps the fabric continuous across them."""
        n = (0.0, 0.0, 0.0)
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                         (a[0] - b[0]) * (a[1] + b[1])))
        if _dot(n, n) < 1e-16:
            return
        n = _unit(n)
        if _dot(n, hint) < 0:
            n = _mul(n, -1)
        plane = n if project else _unit(hint)
        au = _sub(bed, _mul(plane, _dot(bed, plane)))
        if _dot(au, au) < 1e-8:
            au = _sub(Y, _mul(plane, _dot(Y, plane)))
        au = _unit(au)
        av = _unit(_cross(plane, au))
        if mirror:
            au = _mul(au, -1)
        self.prim(mat).face(pts, n, self.basis(mat, origin, au, av, seed), conf)

    def stone(self, frame, poly, joints, mat, seed, conf, *, recess, bevel, F=0.0, rock=0.0,
              bed=None, chips=None, skip=frozenset()):
        """One stone in a wall: `poly` its cell, (s, y) counter-clockwise, `joints[i]`
        the half joint on edge i (0 where it ends a wall). The arris is the cell less
        its joints, recessed to the mortar at -recess; the face is the arris less the
        bevel, at F proud of the wall line, and a rock face rises `rock` further at a
        point near its middle. The mortar fills the whole cell at -recess, so every
        joint has a floor and no stone is open behind. Chipped corners, drawn from the
        stone's seed at the profile's rate along its arris, skip the corners in `skip`
        (the stone before's), and are returned."""
        O, R, N = frame
        P = lambda q, d: _add(_add(_add(O, _mul(R, q[0])), _mul(Y, q[1])), _mul(N, d))
        rng = random.Random(seed)
        bed = bed or R
        mirror = bool(seed >> 31)
        origin = P(poly[0], 0.0)
        n = len(poly)
        rect = _inset(poly, joints)
        front = _inset(rect, [bevel] * n)
        chipped = {}
        if chips and chips["chips_per_m"] > 0:
            perim = sum(math.dist(front[i], front[(i + 1) % n]) for i in range(n))
            mean, want, acc = chips["chips_per_m"] * perim, 0, rng.random()
            while acc > math.exp(-mean) and want < n:
                want += 1
                acc *= rng.random()
            free = [c for c in range(n) if c not in skip]
            for c in sorted(rng.sample(free, min(want, len(free)))):
                a, b, m = front[c - 1], front[(c + 1) % n], front[c]
                room = 0.3 * min(math.dist(a, m), math.dist(b, m))
                cl = min(rng.uniform(*chips["chip_length_m"]), room)
                cd = rng.uniform(*chips["chip_depth_m"])
                ua = ((a[0] - m[0]) / math.dist(a, m), (a[1] - m[1]) / math.dist(a, m))
                ub = ((b[0] - m[0]) / math.dist(b, m), (b[1] - m[1]) / math.dist(b, m))
                cA, cB = (m[0] + ua[0] * cl, m[1] + ua[1] * cl), (m[0] + ub[0] * cl, m[1] + ub[1] * cl)
                # the chip's floor must lie behind the plane its three rims make, or it is
                # a bump, not a chip: deepen it to that plane, and drop it if that would
                # take it through the joint's floor
                A3, B3, C3 = P(cA, F), P(cB, F), P(rect[c], -recess)
                nn = _cross(_sub(B3, A3), _sub(C3, A3))
                den = _dot(nn, N)
                if abs(den) < 1e-12:
                    continue
                d_plane = -_dot(nn, _sub(P(m, 0.0), A3)) / den
                dq = min(F - cd, d_plane - 0.001)
                if dq < -recess + 0.001 or cl < 0.004:
                    continue
                chipped[c] = (cA, cB, dq)
        ring = []  # the face's outline, chips cut out of its corners
        for c in range(n):
            ring += [chipped[c][0], chipped[c][1]] if c in chipped else [front[c]]
        if rock > 0:
            cs = sum(q[0] for q in front) / n + rng.uniform(-0.15, 0.15) * (max(q[0] for q in front) - min(q[0] for q in front))
            cy = sum(q[1] for q in front) / n + rng.uniform(-0.15, 0.15) * (max(q[1] for q in front) - min(q[1] for q in front))
            apex = P((cs, cy), F + rock)
            for i in range(len(ring)):
                self._sface(mat, [P(ring[i], F), P(ring[(i + 1) % len(ring)], F), apex], N, origin, bed, seed,
                            mirror, conf, project=False)
        else:
            self._sface(mat, [P(q, F) for q in ring], N, origin, bed, seed, mirror, conf)
        for i in range(n):
            j = (i + 1) % n
            st = chipped[i][1] if i in chipped else front[i]
            en = chipped[j][0] if j in chipped else front[j]
            ex, ey = rect[j][0] - rect[i][0], rect[j][1] - rect[i][1]
            out = _add(_add(_mul(R, ey), _mul(Y, -ex)), _mul(N, 0.05 * math.hypot(ex, ey)))
            self._sface(mat, [P(st, F), P(en, F), P(rect[j], -recess), P(rect[i], -recess)], out,
                        origin, bed, seed, mirror, conf)
        for c, (cA, cB, dq) in chipped.items():
            Q, Rk = P(front[c], dq), P(rect[c], -recess)
            out = _add(_add(_mul(R, rect[c][0] - front[c][0]), _mul(Y, rect[c][1] - front[c][1])), _mul(N, 0.01))
            for tri in ((P(cA, F), Rk, Q), (Rk, P(cB, F), Q), (P(cB, F), P(cA, F), Q)):
                self._sface(mat, list(tri), out, origin, bed, seed, mirror, conf)
        self.prim("mortar").face([P(q, -recess) for q in poly], N,
                                 self.basis("mortar", O, R, Y, seed), conf)
        return frozenset(chipped)

    def coping_piece(self, frame, sa, sb, yb, yt, joints, seed, conf, recess):
        """One stone of the base's coping: its top weathered at the profile's fall
        out from the wall line, its nose `overhang` past the base's rock faces, a drip
        groove cut up under the nose; mortar behind its cell."""
        O, R, N = frame
        k = self.p.stone
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        jb, jr, jt, jl = joints
        s0, s1, y0, top0 = sa + jl, sb - jr, yb + jb, yt - jt
        Fc = k["rock_face_m"][1] + k["coping_overhang_m"]
        dg = k["drip_groove_m"]
        x1, x2 = Fc - 0.03 - dg, Fc - 0.03
        top = lambda d: top0 - k["coping_fall"] * d
        mat, mirror, origin = "limestone_trim", bool(seed >> 31), P(sa, yb, 0.0)
        f = lambda pts, hint: self._sface(mat, pts, hint, origin, R, seed, mirror, conf)
        f([P(s0, top0, 0.0), P(s1, top0, 0.0), P(s1, top(Fc), Fc), P(s0, top(Fc), Fc)], Y)
        f([P(s0, y0, Fc), P(s1, y0, Fc), P(s1, top(Fc), Fc), P(s0, top(Fc), Fc)], N)
        down = _mul(Y, -1)
        f([P(s0, y0, 0.0), P(s1, y0, 0.0), P(s1, y0, x1), P(s0, y0, x1)], down)
        f([P(s0, y0, x2), P(s1, y0, x2), P(s1, y0, Fc), P(s0, y0, Fc)], down)
        f([P(s0, y0 + dg, x1), P(s1, y0 + dg, x1), P(s1, y0 + dg, x2), P(s0, y0 + dg, x2)], down)
        f([P(s0, y0, x1), P(s1, y0, x1), P(s1, y0 + dg, x1), P(s0, y0 + dg, x1)], N)
        f([P(s0, y0, x2), P(s1, y0, x2), P(s1, y0 + dg, x2), P(s0, y0 + dg, x2)], _mul(N, -1))
        for s, hint in ((s0, _mul(R, -1)), (s1, R)):
            for quad in (((0.0, y0), (x1, y0), (x1, top(x1)), (0.0, top0)),
                         ((x1, y0 + dg), (x2, y0 + dg), (x2, top(x2)), (x1, top(x1))),
                         ((x2, y0), (Fc, y0), (Fc, top(Fc)), (x2, top(x2)))):
                f([P(s, y, d) for d, y in quad], hint)
        self.prim("mortar").face([P(sa, yb, -recess), P(sb, yb, -recess), P(sb, yt, -recess), P(sa, yt, -recess)],
                                 N, self.basis("mortar", O, R, Y, seed), conf)

    def flat_arch(self, frame, s0, s1, y1, h, conf, recess):
        """k01.opening.flat_arch: voussoirs over an opening, seated 0.12 m into the wall
        each side, their joints radiating from a point below so each wedge is wider
        at its back than its face; each stone's bed turned along its radial joint
        (k02_stone_profiles.json common.bed_orientation), the keystone proud."""
        O, R, N = frame
        t = self.p.stone["trim_edges"]
        a, b = s0 - 0.12, s1 + 0.12
        w = b - a
        n = max(5, int(round(w / 0.2)) | 1)
        c = (a + b) / 2
        r0 = (w / 2) / math.tan(math.radians(12.0))
        xs = [a + w * i / n for i in range(n + 1)]
        xt = [a] + [x + (x - c) * h / r0 for x in xs[1:-1]] + [b]
        cid = "k01.opening.flat_arch"
        self.instance(cid, "opening", {"voussoirs": n, "span_m": w, "depth_m": h, "seat_m": 0.12,
                                       "springing": "radial from 12 degrees", "fabric": self.p.stone["trim"]},
                      {"springing": _add(_add(O, _mul(R, a)), _mul(Y, y1)),
                       "crown": _add(_add(O, _mul(R, c)), _mul(Y, y1 + h))})
        inst = len(self.components[cid]["instances"]) - 1
        hj = t["joint_m"] / 2
        for j in range(n):
            poly = [(xs[j], y1), (xs[j + 1], y1), (xt[j + 1], y1 + h), (xt[j], y1 + h)]
            mb = ((xs[j] + xs[j + 1]) / 2, y1)
            mt = ((xt[j] + xt[j + 1]) / 2, y1 + h)
            bed = _unit(_add(_mul(R, mt[0] - mb[0]), _mul(Y, mt[1] - mb[1])))
            self.stone(frame, poly, [hj] * 4, "limestone_trim", self._stone_seed(cid, inst, j), conf,
                       recess=recess, bevel=t["bevel_m"], F=0.05 if j == n // 2 else 0.03, bed=bed)

    def stone_front(self, cid, O, R, length, E, yf, thickness, openings):
        """The street front as K02 coursed ashlar. Course lines are struck on the
        base, the coping, every slip sill's bed, every head and arch top and the
        belts, and the walling between them is cut into equal courses inside the
        profile's range; an opening, its sill or its arch is a hole in a course, and
        where one fills only part of a course's height the stone over or under it is
        cut to what is left. Returns the south corner's quoins for the side wall."""
        p, k = self.p, self.p.stone
        N = _cross(R, Y)
        frame = (O, R, N)
        conf = p.worst_conf("footprint", "stories", "storey_heights_m", "construction", "stone_front")
        floors = p.floors_m
        wk, tk = k["wall"], k["trim_edges"]
        r_wall, r_base = wk["recess_m"], k["channel_depth_m"]
        bc = k["base_course_m"]
        base_top = bc * k["base_courses"]
        cop_top = k["coping_top_m"]
        self.instance(cid, "wall", {"length_m": length, "height_m": E, "thickness_m": thickness,
                                    "construction": "masonry", "openings": len(openings),
                                    "fabric": k["fabric"], "dressing": k["dressing"]},
                      {"base": O, "top": _add(O, _mul(Y, E))})
        holes, sills, arches = [], [], []
        heads = sorted({o.head_m for o in openings if o.component == "k01.opening.sash_flat"})
        for o in openings:
            s0, s1 = o.s_m - o.width_m / 2, o.s_m + o.width_m / 2
            holes.append((s0, s1, o.sill_m, o.head_m))
            if o.component != "k01.opening.door_leaf":
                sills.append((s0, s1, round(o.sill_m - 0.10, 4), o.sill_m))
            h = 0.30
            if o.component == "k01.opening.door_leaf":
                # a door's arch tops out on its storey's window heads, one course line
                h = next((wh - o.head_m for wh in heads
                          if k["trim_course_m"][0] <= wh - o.head_m <= k["trim_course_m"][1]), h)
            arches.append((s0, s1, o.head_m, round(o.head_m + h, 4)))
        belts = [(floors[1] - 0.20, floors[1])] + ([(floors[2] - 0.15, floors[2])] if len(floors) > 2 else [])
        lines = {0.0, cop_top, yf, *[bc * i for i in range(1, k["base_courses"] + 1)]}
        lines |= {y for (_, _, y, _) in sills if y > cop_top + 1e-6}
        lines |= {y for (_, _, _, y) in holes + arches if y > cop_top + 1e-6}
        lines |= {y for band in belts for y in band}
        merged = []
        for y in sorted(round(y, 4) for y in lines if y <= yf + 1e-6):
            if not merged or y - merged[-1] >= 0.02:
                merged.append(y)
        courses = []
        lo_c, hi_c = k["course_m"]
        for ya, yb in zip(merged, merged[1:]):
            if yb <= base_top + 1e-6:
                courses.append((ya, yb, "base"))
            elif abs(ya - base_top) < 1e-6 and abs(yb - cop_top) < 1e-6:
                courses.append((ya, yb, "coping"))
            elif any(abs(ya - b0) < 1e-6 and abs(yb - b1) < 1e-6 for b0, b1 in belts):
                courses.append((ya, yb, "belt"))
            elif yb - ya < lo_c - 1e-9:
                courses.append((ya, yb, "band"))   # too thin for the walling: a dressed band
            else:
                m = math.ceil((yb - ya) / hi_c - 1e-9)
                courses += [(ya + (yb - ya) * i / m, ya + (yb - ya) * (i + 1) / m, "walling") for i in range(m)]
        rects = holes + sills + arches
        quoins, prev_joints, parity = [], [], 0
        for ya, yb, kind in courses:
            trim = kind in ("coping", "belt", "band")
            mat = "limestone_trim" if trim else "rough_stone_trim"
            spec = tk if trim else wk
            lo, hi = k["trim_block_m"] if trim else k["block_m"]
            r = r_base if kind == "base" else r_wall
            jh = (k["channel_m"] if kind == "base" else spec["joint_m"]) / 2
            jv = spec["joint_m"] / 2
            ccid = {"base": "k01.wall.rusticated_base", "coping": "k01.wall.coping"}.get(kind, "k01.wall.stone_course")
            cparams = {"bed_m": ya, "height_m": yb - ya, "kind": kind,
                       "fabric": k["trim"] if trim else k["fabric"]}
            if kind == "base":
                cparams |= {"channel_width_m": k["channel_m"], "channel_depth_m": r_base}
            if kind == "coping":
                cparams |= {"fall": k["coping_fall"], "overhang_m": k["coping_overhang_m"],
                            "drip_groove_m": k["drip_groove_m"]}
            cseed = self.instance(ccid, "wall", cparams,
                                  {"bed": _add(O, _mul(Y, ya)), "top": _add(O, _mul(Y, yb))})
            inst = len(self.components[ccid]["instances"]) - 1
            rng = random.Random(cseed)
            obs = [o for o in rects if o[2] < yb - 1e-6 and o[3] > ya + 1e-6]
            S = sorted({0.0, length, *[min(max(x, 0.0), length) for o in obs for x in (o[0], o[1])]})
            spans = []
            for sa, sb in zip(S, S[1:]):
                if sb - sa < 1e-6:
                    continue
                mid = (sa + sb) / 2
                free, y = [], ya
                for c0, c1 in sorted((o[2], o[3]) for o in obs if o[0] < mid < o[1]):
                    if c0 > y + 1e-6:
                        free.append((y, min(c0, yb)))
                    y = max(y, c1)
                if y < yb - 1e-6:
                    free.append((y, yb))
                if spans and spans[-1][2] == free and abs(spans[-1][1] - sa) < 1e-9:
                    spans[-1][1] = sb
                else:
                    spans.append([sa, sb, free])
            joints_here, j = [], 0
            corner = "south" in k["corners"] and kind in ("base", "walling")
            for sa, sb, free in spans:
                for fy0, fy1 in free:
                    first = None
                    if corner and sa == 0.0 and abs(fy0 - ya) < 1e-9 and abs(fy1 - yb) < 1e-9:
                        rlo, rhi = k["quoin_return_m"]
                        long_side = parity % 2 == 0
                        # to the centimetre, so two returns never leave the brick a sliver
                        ret = round(rng.uniform(0.8 * rhi, rhi) if long_side else rng.uniform(rlo, 1.2 * rlo), 2)
                        first = lo if long_side else min(hi, 0.75 * hi)
                        quoins.append((ret, ya, yb, kind, jh, jv, r))
                        parity += 1
                    full = abs(fy0 - ya) < 1e-9 and abs(fy1 - yb) < 1e-9
                    pieces = _lay(rng, sa, sb, lo, hi, first, prev_joints if full else ())
                    skip = frozenset()
                    for s0, s1 in pieces:
                        joints = [0.0 if fy0 <= 1e-9 else jh, 0.0 if s1 >= length - 1e-9 else jv,
                                  0.0 if fy1 >= yf - 1e-9 else jh, 0.0 if s0 <= 1e-9 else jv]
                        bseed = self._stone_seed(ccid, inst, j)
                        j += 1
                        if kind == "coping":
                            self.coping_piece(frame, s0, s1, fy0, fy1, joints, bseed, conf, r)
                        else:
                            brng = random.Random(bseed ^ 0x5EED)
                            rock = brng.uniform(*k["rock_face_m"]) if not trim else 0.0
                            skip = self.stone(frame, [(s0, fy0), (s1, fy0), (s1, fy1), (s0, fy1)], joints, mat,
                                              bseed, conf, recess=r, bevel=spec["bevel_m"],
                                              F=0.05 if kind == "belt" else 0.0, rock=rock,
                                              chips=None if trim else spec, skip=skip)
                        if kind == "base" and abs(fy1 - base_top) < 1e-6:
                            # the rusticated base's channels are deeper than the joints over
                            # it: a ledge closes the step between the two mortar floors
                            self.prim("mortar").face([_add(_add(O, _mul(R, s)), _add(_mul(Y, base_top), _mul(N, d)))
                                                      for s, d in ((s0, -r_base), (s1, -r_base), (s1, -r_wall), (s0, -r_wall))],
                                                     _mul(Y, -1), self.basis("mortar", O, R, N, bseed), conf)
                        if 1e-9 < s1 < length - 1e-9:
                            joints_here.append(s1)
            prev_joints = joints_here
        for s0, s1, y0, y1 in sills:
            sc = "k01.opening.slip_sill"
            self.instance(sc, "opening", {"width_m": s1 - s0, "height_m": y1 - y0, "projection_m": 0.06,
                                          "fabric": k["trim"]},
                          {"bed": _add(_add(O, _mul(R, (s0 + s1) / 2)), _mul(Y, y0))})
            inst = len(self.components[sc]["instances"]) - 1
            self.stone(frame, [(s0, y0), (s1, y0), (s1, y1), (s0, y1)], [tk["joint_m"] / 2] * 4, "limestone_trim",
                       self._stone_seed(sc, inst, 0), conf, recess=r_base if y1 <= cop_top + 1e-6 else r_wall,
                       bevel=tk["bevel_m"], F=0.06)
        for s0, s1, y1, y2 in arches:
            self.flat_arch(frame, s0, s1, y1, y2 - y1, conf, r_wall)
        # the wall behind the soffit, up to the eave: inside the roof, one plain face
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        if E - yf > 1e-6:
            self.prim("rough_stone_trim").face([P(0.0, yf, 0.0), P(length, yf, 0.0), P(length, E, 0.0), P(0.0, E, 0.0)],
                                               N, self.basis("rough_stone_trim", O, R, Y, 0), conf)
        return frame, quoins

    def quoins(self, frame, length, quoins):
        """k01.wall.corner_bond: the front's corner stones returned on the south wall,
        long and short in turn, laid in its brick; a step closes each one's mortar
        floor to the brick face beside, above and below it."""
        O, R, N = frame
        k = self.p.stone
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        conf = self.p.worst_conf("footprint", "stories", "storey_heights_m", "construction", "stone_front")
        cid = "k01.wall.corner_bond"
        rows = sorted(quoins, key=lambda q: q[1])
        for i, (ret, ya, yb, kind, jh, jv, r) in enumerate(rows):
            seed = self.instance(cid, "wall", {"return_m": ret, "bed_m": ya, "height_m": yb - ya, "kind": kind,
                                               "fabric": k["fabric"]},
                                 {"corner": P(length, ya, 0.0)})
            inst = len(self.components[cid]["instances"]) - 1
            s0 = length - ret
            rock = random.Random(seed ^ 0x5EED).uniform(*k["rock_face_m"])
            self.stone(frame, [(s0, ya), (length, ya), (length, yb), (s0, yb)],
                       [0.0 if ya <= 1e-9 else jh, 0.0, jh, jv], "rough_stone_trim",
                       self._stone_seed(cid, inst, 0), conf, recess=r, bevel=k["wall"]["bevel_m"],
                       rock=rock, chips=k["wall"])
            steps = [((s0, yb, -r), (s0, ya, -r), (s0, ya, 0.0), (s0, yb, 0.0), R)]
            below = rows[i - 1] if i > 0 and abs(rows[i - 1][2] - ya) < 1e-6 else None
            above = rows[i + 1] if i + 1 < len(rows) and abs(rows[i + 1][1] - yb) < 1e-6 else None
            ob = length - (above[0] if above else 0.0)
            if ob > s0 + 1e-6:
                steps.append(((s0, yb, -r), (ob, yb, -r), (ob, yb, 0.0), (s0, yb, 0.0), _mul(Y, -1)))
            ub = length - (below[0] if below else 0.0)
            if ya > 1e-9 and ub > s0 + 1e-6:
                steps.append(((s0, ya, -r), (ub, ya, -r), (ub, ya, 0.0), (s0, ya, 0.0), Y))
            for *pts, hint in steps:
                self.prim("mortar").face([P(*q) for q in pts], hint, self.basis("mortar", O, R, Y, seed), conf)

    # -- k01.stair.straight_stoop ------------------------------------------------------
    def stoop(self, frame, s_c):
        p = self.p
        O, R, N = frame
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        n, r, t, L = p.risers, p.riser_m, p.tread_m, p.landing_depth_m
        sa, sb = s_c - p.stoop_width_m / 2, s_c + p.stoop_width_m / 2
        conf = p.worst_conf("principal_floor_m", "stair_tread_m", "stair_landing_depth_m", "stoop_width_m")
        foot = L + (n - 1) * t
        seed = self.instance("k01.stair.straight_stoop", "stair",
                             {"riser_m": r, "tread_m": t, "risers": n, "landing_depth_m": L,
                              "width_m": p.stoop_width_m},
                             {"foot": P(s_c, 0.0, foot), "landing": P(s_c, n * r, 0.0)})
        pr = self.prim("stoop_stone")
        bt = self.basis("stoop_stone", O, R, N, seed)
        bv = self.basis("stoop_stone", O, R, Y, seed)
        bs = self.basis("stoop_stone", O, N, Y, seed)
        # columns, landing first: (near d, far d, top y)
        cols = [(0.0, L, n * r)] + [(L + (n - 1 - k) * t, L + (n - k) * t, k * r) for k in range(n - 1, 0, -1)]
        for (d0, d1, top) in cols:
            pr.face([P(sa, top, d0), P(sb, top, d0), P(sb, top, d1), P(sa, top, d1)], Y, bt, conf)
            low = top - r
            pr.face([P(sa, low, d1), P(sb, low, d1), P(sb, top, d1), P(sa, top, d1)], N, bv, conf)
            pr.face([P(sa, 0, d0), P(sa, 0, d1), P(sa, top, d1), P(sa, top, d0)], _mul(R, -1), bs, conf)
            pr.face([P(sb, 0, d0), P(sb, 0, d1), P(sb, top, d1), P(sb, top, d0)], R, bs, conf)
        # A column's riser runs only from the next column's tread to its own: below
        # that is the inside of the stoop, between two columns, and is not drawn.

    # -- k01.roof.hip ------------------------------------------------------------------
    def roof(self):
        p = self.p
        D, W, E, o = p.depth_m, p.width_m, p.eave_m, p.eave_overhang_m
        tp = math.tan(math.radians(p.roof_pitch_deg))
        ye = E - o * tp
        yf = ye - 0.20
        yr = p.ridge_m
        conf = p.worst_conf("footprint", "roof_form", "roof_pitch_deg", "eave_overhang_m", "roof_covering")
        seed = self.instance("k01.roof.hip", "roof",
                             {"pitch_deg": p.roof_pitch_deg, "eave_overhang_m": o,
                              "eave_datum_m": E, "ridge_datum_m": yr,
                              **({"covering": p.roof["covering"], "flashing": p.roof["flashing"]} if p.roof else {}),
                              **({"gutter_diameter_m": p.rainwater["gutter_diameter_m"], "gutter_fall": p.rainwater["fall"],
                                  "downpipes": len(p.rainwater["downpipes"]),
                                  "pipe_diameter_m": p.rainwater["pipe_diameter_m"]} if p.rainwater else {})},
                             {"eave": (0.0, E, 0.0), "ridge": (W / 2, yr, -W / 2)})
        k = p.roof or {}
        # T-2293: the slates run 50 mm past the fascia (k04 cut_edges.eave) on the same plane
        o2 = o + k.get("eave_overhang_m", 0.0)
        ye2 = E - o2 * tp
        SWe, SEe, NEe, NWe = (-o2, ye2, o2), (D + o2, ye2, o2), (D + o2, ye2, -W - o2), (-o2, ye2, -W - o2)
        RW, RE = (W / 2, yr, -W / 2), (D - W / 2, yr, -W / 2)
        phase = (_k04_fabric(k["covering"]) or {}).get("course_phase_m", [0.0, 0.0])[1] if k else None
        pr = self.prim("slate_covering")
        planes = {}
        for name, pts, contour, out in (("south", [SWe, SEe, RE, RW], (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                                        ("north", [NEe, NWe, RW, RE], (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
                                        ("east", [SEe, NEe, RE], (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)),
                                        ("west", [NWe, SWe, RW], (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))):
            nrm = _unit(_cross(_sub(pts[1], pts[0]), _sub(pts[-1], pts[0])))
            uphill = _unit(_cross(nrm, contour))
            planes[name] = nrm
            pr.face(pts, nrm, self.basis("slate_covering", pts[0], contour, uphill, seed, phase), conf)
            if not k:
                continue
            # the cut edge: the doubled eave course's butt, two slates thick, and the
            # underside of the 50 mm the slates overhang the fascia
            te = 2 * k["slate_thickness_m"]
            a, b = pts[0], pts[1]
            dn = (0.0, -te, 0.0)
            pr.face([a, b, _add(b, dn), _add(a, dn)], out, self.basis("slate_covering", a, contour, Y, seed), conf)
            # the fascia line, on the covering plane: where the slates leave the fascia
            ia = (a[0] - out[0] * (o2 - o) + contour[0] * (o2 - o), ye, a[2] - out[2] * (o2 - o) + contour[2] * (o2 - o))
            ib = (b[0] - out[0] * (o2 - o) - contour[0] * (o2 - o), ye, b[2] - out[2] * (o2 - o) - contour[2] * (o2 - o))
            pr.face([_add(a, dn), _add(b, dn), _add(ib, dn), _add(ia, dn)], _mul(nrm, -1),
                    self.basis("slate_covering", a, contour, _mul(uphill, -1), seed), conf)
        # fascia and soffit close the eave
        fa = self.prim("fascia")
        down = (0.0, -1.0, 0.0)
        walls = [(0, 0), (D, 0), (D, -W), (0, -W)]
        eaves = [(-o, o), (D + o, o), (D + o, -W - o), (-o, -W - o)]
        outs = [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (-1.0, 0.0, 0.0)]
        for i in range(4):
            j = (i + 1) % 4
            a, b = eaves[i], eaves[j]
            along = _unit((b[0] - a[0], 0.0, b[1] - a[1]))
            fa.face([(a[0], yf, a[1]), (b[0], yf, b[1]), (b[0], ye, b[1]), (a[0], ye, a[1])], outs[i],
                    self.basis("fascia", (a[0], yf, a[1]), along, Y, seed), conf)
            wa, wb = walls[i], walls[j]
            fa.face([(a[0], yf, a[1]), (b[0], yf, b[1]), (wb[0], yf, wb[1]), (wa[0], yf, wa[1])], down,
                    self.basis("fascia", (0.0, yf, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), seed), conf)
        if not k:
            return yf
        # copper rolls on the four hips (trimmed to the eave) and the ridge
        lift = 2 * k["slate_thickness_m"]
        for (A, B, n1, n2, e1, e2) in ((SEe, RE, planes["south"], planes["east"], (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
                                       (NEe, RE, planes["north"], planes["east"], (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
                                       (NWe, RW, planes["north"], planes["west"], (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                                       (SWe, RW, planes["south"], planes["west"], (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))):
            self.cap(A, B, n1, n2, lift, seed, conf, eave=(e1, e2))
        self.cap(RW, RE, planes["south"], planes["north"], lift + 0.002, seed, conf)
        if p.dormer:
            self.dormer(planes["east"], seed)
        if p.rainwater:
            self.rainwater(ye, yf, seed)
        return yf

    def _flashing(self):
        return "k04_" + self.p.roof["flashing"]

    # -- caps: a copper roll on wood, its flanges dressed over the top courses ----------
    def cap(self, A, B, n1, n2, lift, seed, conf, eave=None):
        k = self.p.roof
        mat = self._flashing()
        pr = self.prim(mat)
        L = _unit(_sub(B, A))
        w = k["cap_flange_m"]
        for i, (n, e) in enumerate(((n1, eave[0] if eave else None), (n2, eave[1] if eave else None))):
            q = _unit(_cross(n, L))
            if q[1] > 0:
                q = _mul(q, -1)  # into the plane: downhill from a convex hip or ridge
            a0, b0 = _add(A, _mul(n, lift)), _add(B, _mul(n, lift))
            a1, b1 = _add(a0, _mul(q, w)), _add(b0, _mul(q, w))
            if e is not None:
                # trim the flange's outer edge to the eave line through A
                # solve a1 + t L = a0 + u e  (both lines lie in the lifted plane)
                d = _sub(a0, a1)
                LL, Le, ee = _dot(L, L), _dot(L, e), _dot(e, e)
                dL, de = _dot(d, L), _dot(d, e)
                den = LL * ee - Le * Le
                t = (dL * ee - de * Le) / den
                a1 = _add(a1, _mul(L, t))
            pr.face([a0, b0, b1, a1], n, self.basis(mat, a0, L, q, seed), conf)
        # the roll: an arc over the line on the flanges' bisector
        bis = _unit(_add(n1, n2))
        side = _unit(_cross(L, bis))
        rr = k["cap_roll_diameter_m"] / 2
        c0, c1 = _add(A, _mul(bis, lift + rr * 0.4)), _add(B, _mul(bis, lift + rr * 0.4))
        angs = [math.radians(-105 + 35 * j) for j in range(7)]
        ring = [_add(_mul(bis, math.cos(t) * rr), _mul(side, math.sin(t) * rr)) for t in angs]
        for j in range(len(ring) - 1):
            mid = _unit(_add(ring[j], ring[j + 1]))
            pr.quad(_add(c0, ring[j]), _add(c1, ring[j]), _add(c1, ring[j + 1]), _add(c0, ring[j + 1]), mid,
                    self.basis(mat, _add(c0, ring[j]), L, _unit(_sub(ring[j + 1], ring[j])), seed), conf)
        for c, nn in ((c0, _mul(L, -1)), (c1, L)):
            pr.face([_add(c, r) for r in ring], nn, self.basis(mat, c, side, bis, seed), conf)

    # -- k01.roof.dormer_gable --------------------------------------------------------
    def dormer(self, n_main, roof_seed):
        p, d, k = self.p, self.p.dormer, self.p.roof
        D, W, E = p.depth_m, p.width_m, p.eave_m
        tp = math.tan(math.radians(p.roof_pitch_deg))
        dp = math.tan(math.radians(d["pitch_deg"]))
        wd, sb, hf, vo = d["width_m"], d["face_setback_m"], d["face_height_m"], d["verge_m"]
        xf = D - sb
        ys = E + sb * tp                      # the face's foot, on the street hip
        yde = ys + hf                         # the dormer's eave
        ydr = yde + wd / 2 * dp               # its ridge
        xl = D - (yde - E) / tp               # where a cheek's top meets the hip
        xr = D - (ydr - E) / tp               # where the dormer ridge dies into it
        zc = -W / 2
        zs, zn = zc + wd / 2, zc - wd / 2
        if xr - (D - W / 2) < wd / 2 + 0.3:
            raise ValueError("the dormer does not fit inside the street hip")
        conf = p.worst_conf("roof_form", "roof_pitch_deg", "dormer")
        seed = self.instance("k01.roof.dormer_gable", "roof",
                             {"pitch_deg": d["pitch_deg"], "width_m": wd, "face_height_m": hf,
                              "face_setback_m": sb, "verge_m": vo},
                             {"eave": (xf, yde, zs), "ridge": (xf, ydr, zc)})
        # the face, its sash cut through it, and the gable over it
        from archetypes.k01_frontage_params import Opening
        frame, t = self.wall("k01.wall.dormer_face", "dormer_stone", (xf, ys, zs), (0.0, 0.0, -1.0), wd, hf,
                             d["face_thickness_m"],
                             [(wd / 2 - d["sash"]["width_m"] / 2, wd / 2 + d["sash"]["width_m"] / 2,
                               d["sash"]["sill_m"], d["sash"]["sill_m"] + d["sash"]["height_m"])])
        self.opening(Opening("k01.opening.sash_flat", "k01.wall.dormer_face", wd / 2, d["sash"]["sill_m"],
                             d["sash"]["width_m"], d["sash"]["height_m"]), frame, t, "dormer_stone", "limestone_trim")
        X = (1.0, 0.0, 0.0)
        self.prim("dormer_stone").face([(xf, yde, zs), (xf, yde, zn), (xf, ydr, zc)], X,
                                       self.basis("dormer_stone", (xf, yde, zs), (0.0, 0.0, -1.0), Y, seed), conf)
        # roof planes, slated, from the verge back to the valleys
        pr = self.prim("slate_covering")
        phase = (_k04_fabric(k["covering"]) or {}).get("course_phase_m", [0.0, 0.0])[1]
        sides = {}
        for z_e, sgn in ((zs, 1.0), (zn, -1.0)):
            pts = [(xf + vo, yde, z_e), (xl, yde, z_e), (xr, ydr, zc), (xf + vo, ydr, zc)]
            nrm = _unit((0.0, 1.0, sgn * dp))
            contour = (-1.0, 0.0, 0.0)
            uphill = _unit(_cross(nrm, contour))
            if uphill[1] < 0:
                uphill = _mul(uphill, -1)
            pr.face(pts, nrm, self.basis("slate_covering", pts[0], contour, uphill, seed, phase), conf)
            sides[sgn] = (nrm, z_e)
            # the cheek under it: slated, a triangle standing on the hip
            pr.face([(xf, ys, z_e), (xf, yde, z_e), (xl, yde, z_e)], (0.0, 0.0, sgn),
                    self.basis("slate_covering", (xf, ys, z_e), (-1.0, 0.0, 0.0), Y, seed, 0.0), conf)
            # bargeboard and the verge's soffit
            fa = self.prim("fascia")
            top0, top1 = (xf + vo, yde, z_e), (xf + vo, ydr, zc)
            dn = (0.0, -0.15, 0.0)
            fa.face([top0, top1, _add(top1, dn), _add(top0, dn)], X,
                    self.basis("fascia", top0, (0.0, 0.0, -sgn), Y, seed), conf)
            fa.face([_add(top0, dn), _add(top1, dn), (xf, ydr - 0.15, zc), (xf, yde - 0.15, z_e)], _mul(nrm, -1),
                    self.basis("fascia", top0, X, (0.0, 0.0, -sgn), seed), conf)
        lift = 2 * k["slate_thickness_m"]
        self.cap((xf + vo, ydr, zc), (xr, ydr, zc), sides[1.0][0], sides[-1.0][0], lift, seed, conf)
        # the valleys: open, widening downhill, a crimped rib up the middle
        mat = self._flashing()
        fl = self.prim(mat)
        V1 = (xr, ydr, zc)
        for sgn in (1.0, -1.0):
            nd, z_e = sides[sgn]
            V0 = (xl, yde, z_e)
            Lv = _unit(_sub(V1, V0))
            length = math.dist(V0, V1)
            half0 = (k["valley_exposed_at_top_m"] + k["valley_widening_per_m"] * length) / 2
            half1 = k["valley_exposed_at_top_m"] / 2
            for n, test in ((n_main, (0.0, 0.0, sgn)), (nd, X)):
                q = _unit(_cross(n, Lv))
                if _dot(q, test) < 0:
                    q = _mul(q, -1)
                a0, a1 = _add(V0, _mul(n, lift)), _add(V1, _mul(n, lift))
                fl.face([a0, a1, _add(a1, _mul(q, half1)), _add(a0, _mul(q, half0))], n,
                        self.basis(mat, a0, Lv, q, seed), conf)
                rib = _unit(_add(n_main, nd))
                b0, b1 = _add(a0, _mul(q, 0.012)), _add(a1, _mul(q, 0.012))
                c0, c1 = _add(V0, _mul(rib, lift + k["valley_crimp_m"])), _add(V1, _mul(rib, lift + k["valley_crimp_m"]))
                fl.quad(b0, b1, c1, c0, _add(n, _mul(q, -1)), self.basis(mat, b0, Lv, _unit(_sub(c0, b0)), seed), conf)
        # the apron over the course below the face, and its upstand
        dd = _unit((1.0, -tp, 0.0))
        a_s = _add((xf, ys, zs + k["step_leg_m"]), _mul(n_main, lift))
        a_n = _add((xf, ys, zn - k["step_leg_m"]), _mul(n_main, lift))
        fl.face([a_s, a_n, _add(a_n, _mul(dd, k["apron_lap_m"])), _add(a_s, _mul(dd, k["apron_lap_m"]))], n_main,
                self.basis(mat, a_s, (0.0, 0.0, -1.0), _mul(dd, -1), seed), conf)
        ux = a_s[0]
        fl.face([(ux, a_s[1], zs), (ux, a_s[1], zn), (ux, ys + k["apron_upstand_m"], zn), (ux, ys + k["apron_upstand_m"], zs)], X,
                self.basis(mat, (ux, a_s[1], zs), (0.0, 0.0, -1.0), Y, seed), conf)
        # step flashing at each cheek: a leg on the hip, an upstand on the cheek
        for sgn, z_e in ((1.0, zs), (-1.0, zn)):
            f0 = _add((xf, ys, z_e), _mul(n_main, lift + 0.002))
            f1 = _add((xl, yde, z_e), _mul(n_main, lift + 0.002))
            Ls = _unit(_sub(f1, f0))
            out = (0.0, 0.0, sgn)
            fl.face([f0, f1, _add(f1, _mul(out, k["step_leg_m"])), _add(f0, _mul(out, k["step_leg_m"]))], n_main,
                    self.basis(mat, f0, Ls, out, seed), conf)
            u0, u1 = (xf, ys, z_e + sgn * 0.006), (xl, yde, z_e + sgn * 0.006)
            up = (0.0, k["step_upstand_m"], 0.0)
            fl.face([u0, u1, _add(u1, up), _add(u0, up)], out, self.basis(mat, u0, Ls, Y, seed), conf)

    # -- rainwater: gutter, brackets, outlets, downpipes, shoes, splash stones -----------
    def rainwater(self, ye, yf, seed):
        p, r = self.p, self.p.rainwater
        D, W, o = p.depth_m, p.width_m, p.eave_overhang_m
        conf = p.worst_conf("rainwater", "eave_overhang_m")
        mat = "k04_" + r["fabric"]
        ri = r["gutter_diameter_m"] / 2
        ro = ri + 0.004
        c = ro + 0.006                        # axis off the fascia: room for the bracket's band
        A = o + c
        corners = [(D + A, A), (D + A, -W - A), (-A, -W - A), (-A, A)]          # SE NE NW SW, (x, z)
        dirs = [(0.0, 0.0, -1.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)]
        outs = [(1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)]
        lens = [W + 2 * A, D + 2 * A, W + 2 * A, D + 2 * A]
        starts = [sum(lens[:i]) for i in range(4)]
        P = sum(lens)
        side_of = {"k01.wall.street_front": 0, "k01.wall.rear_service": 2, "k01.wall.side.south": 3}
        outlets = sorted(starts[side_of[x["wall"]]] + A + x["s_m"] for x in r["downpipes"])
        gaps = [((outlets[(i + 1) % len(outlets)] - outlets[i]) % P) or P for i in range(len(outlets))]
        highs = [(outlets[i] + gaps[i] / 2) % P for i in range(len(outlets))]
        reach = max(gaps) / 2
        self.rain_runs = [round(g, 3) for g in gaps]   # read by the emitter's extras
        y_top = ye - 0.06
        y_low = y_top - r["fall"] * reach

        def cyc(a, b):
            d = abs(a - b) % P
            return min(d, P - d)

        def y_at(sv):
            return y_low + r["fall"] * min(cyc(sv, x) for x in outlets)

        def at(sv):
            sv %= P
            i = max(j for j in range(4) if starts[j] <= sv + 1e-9)
            t = sv - starts[i]
            cx, cz = corners[i]
            return (cx + dirs[i][0] * t, y_at(sv), cz + dirs[i][2] * t), i, t

        n_seg = 8
        secs = [k_ * math.pi / n_seg for k_ in range(n_seg + 1)]

        def ring(sv, rad):
            pt, i, t = at(sv)
            out = outs[i]
            if t < 1e-6:  # a corner: the mitre between the side before and this one
                prev = outs[(i - 1) % 4]
                out = (out[0] + prev[0], 0.0, out[2] + prev[2])
            return [(pt[0] - math.cos(a) * rad * out[0], pt[1] - math.sin(a) * rad, pt[2] - math.cos(a) * rad * out[2])
                    for a in secs], pt

        stations = sorted({*(round(x % P, 6) for x in starts), *(round(x, 6) for x in outlets),
                           *(round(x, 6) for x in highs)})
        pr = self.prim(mat)
        for a_, b_ in zip(stations, stations[1:] + [stations[0] + P]):
            (Ro, pa), (Rb, pb) = ring(a_, ro), ring(b_, ro)
            Ri, Rj = ring(a_, ri)[0], ring(b_, ri)[0]
            along = _unit(_sub(pb, pa))
            for j in range(n_seg):
                mo = _sub(_mul(_add(Ro[j], Ro[j + 1]), 0.5), pa)
                pr.quad(Ro[j], Rb[j], Rb[j + 1], Ro[j + 1], mo,
                        self.basis(mat, Ro[j], along, _unit(_sub(Ro[j + 1], Ro[j])), seed), conf)
                pr.quad(Ri[j], Rj[j], Rj[j + 1], Ri[j + 1], _mul(mo, -1),
                        self.basis(mat, Ri[j], along, _unit(_sub(Ri[j + 1], Ri[j])), seed), conf)
            for j in (0, n_seg):  # the two rims, inner skin to outer
                pr.quad(Ri[j], Rj[j], Rb[j], Ro[j], Y, self.basis(mat, Ri[j], along, _unit(_sub(Ro[j], Ri[j])), seed), conf)
        # wrought-iron hangers at the bracket spacing, a band under the gutter and a leg
        # up the fascia, clear of the outlets
        iron = self.prim("iron")
        bw = r["bracket_section_m"][0] / 2
        rb = ro + r["bracket_section_m"][1] * 0.6
        for i in range(4):
            t = 0.30
            while t < lens[i] - 0.30:
                sv = starts[i] + t
                t += r["bracket_spacing_m"]
                if min(cyc(sv, x) for x in outlets) < 0.15:
                    continue
                pt, _, _ = at(sv)
                d, out = dirs[i], outs[i]
                band = [(pt[0] - math.cos(a) * rb * out[0], pt[1] - math.sin(a) * rb, pt[2] - math.cos(a) * rb * out[2])
                        for a in secs]
                for j in range(n_seg):
                    m0, m1 = band[j], band[j + 1]
                    mo = _sub(_mul(_add(m0, m1), 0.5), pt)
                    iron.quad(_add(m0, _mul(d, -bw)), _add(m0, _mul(d, bw)), _add(m1, _mul(d, bw)), _add(m1, _mul(d, -bw)),
                              mo, self.basis("iron", m0, d, _unit(_sub(m1, m0)), seed), conf)
                leg0 = band[0]
                leg1 = (leg0[0], min(leg0[1] + 0.06, ye - 0.01), leg0[2])
                iron.face([_add(leg0, _mul(d, -bw)), _add(leg0, _mul(d, bw)), _add(leg1, _mul(d, bw)), _add(leg1, _mul(d, -bw))],
                          out, self.basis("iron", leg0, d, Y, seed), conf)
        # an outlet, a swan neck back under the soffit, the pipe down the wall, a shoe
        # kicked out over a splash stone: every pipe ends at ground
        walls = {"k01.wall.street_front": ((D, 0.0, 0.0), (0.0, 0.0, -1.0)),
                 "k01.wall.rear_service": ((0.0, 0.0, -W), (0.0, 0.0, 1.0)),
                 "k01.wall.side.south": ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))}
        rp = r["pipe_diameter_m"] / 2
        kick = math.radians(r["shoe_kick_deg"])
        for x in r["downpipes"]:
            O, R = walls[x["wall"]]
            N = _cross(R, Y)
            # clear of anything proud of the wall: the street front's belt courses
            off = r["pipe_offset_from_wall_m"] + (0.05 if x["wall"] == "k01.wall.street_front" else 0.0)
            lat = off + rp
            base = _add(O, _mul(R, x["s_m"]))
            sv = starts[side_of[x["wall"]]] + A + x["s_m"]
            gy = y_at(sv)
            at_wall = lambda l, y: (base[0] + N[0] * l, y, base[2] + N[2] * l)
            p0 = at_wall(A, gy - ro + 0.002)
            p1 = at_wall(A, gy - ro - 0.12)
            p2 = at_wall(lat, p1[1] - (A - lat))
            # the shoe's lowest lip, not its axis, stands end_above_grade over the ground
            y4 = r["shoe_end_above_grade_m"] + rp * math.cos(kick)
            y3 = y4 + r["shoe_length_m"] * math.sin(kick)
            p3 = at_wall(lat, y3)
            p4 = at_wall(lat + r["shoe_length_m"] * math.cos(kick), y4)
            if p2[1] > yf - 0.05:
                raise ValueError("a swan neck runs into the soffit")
            self.tube(mat, [p0, p1, p2, p3, p4], rp, R, seed, conf, cap_end=True)
            # straps, every strap spacing down the straight run
            yy = p2[1] - 0.4
            while yy > p3[1] + 0.3:
                c0 = at_wall(lat, yy)
                band = [_add(c0, _add(_mul(R, math.cos(a) * (rp + 0.004)), _mul(N, math.sin(a) * (rp + 0.004))))
                        for a in [2 * math.pi * j / 8 for j in range(9)]]
                for j in range(8):
                    mo = _sub(_mul(_add(band[j], band[j + 1]), 0.5), c0)
                    iron.quad(band[j], band[j + 1], _add(band[j + 1], (0.0, 0.03, 0.0)), _add(band[j], (0.0, 0.03, 0.0)),
                              mo, self.basis("iron", band[j], _unit(_sub(band[j + 1], band[j])), Y, seed), conf)
                yy -= r["strap_spacing_m"]
            # the splash stone the shoe discharges onto, its bottom on the ground
            st = self.prim("stoop_stone")
            l0, l1 = lat + 0.05, lat + r["shoe_length_m"] * math.cos(kick) + 0.30
            s0, s1 = -0.17, 0.17
            h = 0.04
            Q = lambda l, s, y: _add(at_wall(l, y), _mul(R, s))
            bt = self.basis("stoop_stone", Q(l0, s0, h), R, N, seed)
            st.face([Q(l0, s0, h), Q(l0, s1, h), Q(l1, s1, h), Q(l1, s0, h)], Y, bt, conf)
            bs = self.basis("stoop_stone", Q(l0, s0, 0), R, Y, seed)
            st.face([Q(l1, s0, 0), Q(l1, s1, 0), Q(l1, s1, h), Q(l1, s0, h)], N, bs, conf)
            st.face([Q(l0, s0, 0), Q(l0, s1, 0), Q(l0, s1, h), Q(l0, s0, h)], _mul(N, -1), bs, conf)
            be = self.basis("stoop_stone", Q(l0, s0, 0), N, Y, seed)
            st.face([Q(l0, s0, 0), Q(l1, s0, 0), Q(l1, s0, h), Q(l0, s0, h)], _mul(R, -1), be, conf)
            st.face([Q(l0, s1, 0), Q(l1, s1, 0), Q(l1, s1, h), Q(l0, s1, h)], R, be, conf)

    def tube(self, mat, path, rad, ref, seed, conf, cap_end=False, sides=8):
        """A round pipe along a polyline lying in a plane normal to `ref`: rings mitred
        on the bisector at every bend, so each side is a planar strip."""
        pr = self.prim(mat)
        dirs = [_unit(_sub(b, a)) for a, b in zip(path, path[1:])]
        angs = [2 * math.pi * j / sides for j in range(sides + 1)]
        rings = []
        for i, J in enumerate(path):
            d_in = dirs[max(i - 1, 0)]
            d_out = dirs[min(i, len(dirs) - 1)]
            d = d_out if i < len(dirs) else d_in
            e2 = _unit(_cross(d, ref))
            m = _unit(_add(d_in, d_out))
            pts = []
            for a in angs:
                q = _add(_mul(ref, math.cos(a) * rad), _mul(e2, math.sin(a) * rad))
                # slide along the segment's own axis onto the mitre plane
                q = _sub(q, _mul(d, _dot(q, m) / _dot(d, m)))
                pts.append(_add(J, q))
            rings.append(pts)
        for i, d in enumerate(dirs):
            A_, B_ = rings[i], rings[i + 1]
            for j in range(sides):
                mo = _sub(_mul(_add(A_[j], A_[j + 1]), 0.5), path[i])
                pr.quad(A_[j], B_[j], B_[j + 1], A_[j + 1], mo,
                        self.basis(mat, A_[j], d, _unit(_sub(A_[j + 1], A_[j])), seed), conf)
        if cap_end:
            self.prim("backing").face(rings[-1][:-1], dirs[-1], self.basis("backing", path[-1], ref, Y, seed), conf)


def build(params, structure_id: str):
    """The assembly: walls with their openings cut, the stoop, the roof."""
    p = params
    a = Assembly(structure_id, p)
    D, W, E = p.depth_m, p.width_m, p.eave_m
    yf = E - p.eave_overhang_m * math.tan(math.radians(p.roof_pitch_deg)) - 0.20
    floors = p.floors_m
    belts = [(floors[1] - 0.20, floors[1], 0.05)] + ([(floors[2] - 0.15, floors[2], 0.05)] if len(floors) > 2 else [])

    def holes(wall_id):
        return [(o.s_m - o.width_m / 2, o.s_m + o.width_m / 2, o.sill_m, o.head_m)
                for o in p.openings if o.wall == wall_id]

    # The four walls, each about its base socket: outer face, left end (seen from
    # outside), at grade. +X is east (footprint u), -Z is north (footprint v).
    walls = {
        "k01.wall.street_front": ("rough_stone_trim", (D, 0.0, 0.0), (0.0, 0.0, -1.0), W, p.front_thickness_m, belts),
        "k01.wall.side.north": ("brick", (D, 0.0, -W), (-1.0, 0.0, 0.0), D, p.side_thickness_m, ()),
        "k01.wall.rear_service": ("brick", (0.0, 0.0, -W), (0.0, 0.0, 1.0), W, p.side_thickness_m, ()),
        "k01.wall.side.south": ("brick", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), D, p.side_thickness_m, ()),
    }
    frames, quoins = {}, []
    if p.stone:
        # T-2289: the street front laid as K02 coursed ashlar, its belts courses of it
        front = [o for o in p.openings if o.wall == "k01.wall.street_front"]
        frame, quoins = a.stone_front("k01.wall.street_front", (D, 0.0, 0.0), (0.0, 0.0, -1.0), W, E, yf,
                                      p.front_thickness_m, front)
        frames["k01.wall.street_front"] = ((frame, p.front_thickness_m), "rough_stone_trim")
    for cid, (mat, O, R, length, t, bands) in walls.items():
        if cid in frames:
            continue
        # the south corner's quoins are cut out of the brick they return into
        bond = [(D - q[0], D, q[1], q[2]) for q in quoins] if cid == "k01.wall.side.south" else []
        frames[cid] = (a.wall(cid, mat, O, R, length, E, t, holes(cid) + bond, (yf,), bands), mat)
    if quoins:
        a.quoins(frames["k01.wall.side.south"][0][0], D, quoins)
    for op in p.openings:
        (frame, t), mat = frames[op.wall]
        a.opening(op, frame, t, mat, "limestone_trim", coursed=bool(p.stone) and op.wall == "k01.wall.street_front")
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf")
    a.stoop(frames["k01.wall.street_front"][0][0], door.s_m)
    a.roof()
    return a


# -----------------------------------------------------------------------------------
# glTF 2.0 binary
# -----------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def to_glb(a: Assembly, structure_id: str, phase_id: str, scene_ids, extras: dict) -> bytes:
    bin_ = bytearray()
    views, accessors = [], []

    def view(data: bytes, target=None):
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(data)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        views.append(v)
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False):
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5125: "I", 5123: "H"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [min(v[k] for v in values) for k in range(comps)]
            acc["max"] = [max(v[k] for v in values) for k in range(comps)]
            # min/max must bound the float32 the file holds, not the float64 we hold
            acc["min"] = [struct.unpack("<f", struct.pack("<f", x))[0] for x in acc["min"]]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", x))[0] for x in acc["max"]]
        accessors.append(acc)
        return len(accessors) - 1

    images, textures, image_of = [], [], {}
    materials, primitives = [], []
    for name in MATERIALS:  # fixed order: the file is the same bytes every run
        pr = a.prims.get(name)
        if pr is None or not pr.idx:
            continue
        spec = a.spec[name]
        mat = {"name": name, "pbrMetallicRoughness": {
            "baseColorFactor": [*spec["color"], 1.0], "metallicFactor": spec.get("metallic", 0.0),
            "roughnessFactor": spec["roughness"]}}
        if tuple(spec["color"]) == (1.0, 1.0, 1.0):
            # the glTF default, written as an absence: the web tier's optimiser drops a
            # default factor, and the derivative gate would read that as a lost colour
            del mat["pbrMetallicRoughness"]["baseColorFactor"]
        fab = a.fabric[name]

        def texture(key, path):
            if key not in image_of:
                images.append({"name": key, "mimeType": "image/jpeg", "bufferView": view(path.read_bytes())})
                textures.append({"sampler": 0, "source": len(images) - 1})
                image_of[key] = len(textures) - 1
            return image_of[key]

        if fab:
            k04, k02 = _k04_fabric(fab), _k02_fabric(fab)
            if k04 is None and k02 is None:
                mat["pbrMetallicRoughness"]["baseColorTexture"] = {
                    "index": texture(f"{fab}_basecolor", LIBRARY / f"{fab}_basecolor.jpg"), "texCoord": 0}
            else:
                # T-2293: a K04 fabric binds its web base colour and its OpenGL normal map,
                # the relief a raking sun reads on slate courses and dressed copper; and
                # since T-2289 a K02 stone does the same, for the grain of a rock face
                lib, kx = (ROOFS, k04) if k04 is not None else (STONE, k02)
                mat["pbrMetallicRoughness"]["baseColorTexture"] = {
                    "index": texture(f"{fab}_basecolor", lib / fab / kx["web"]["basecolor"]), "texCoord": 0}
                mat["normalTexture"] = {"index": texture(f"{fab}_normal_gl", lib / fab / kx["web"]["normal_gl"]),
                                        "texCoord": 0}
        materials.append(mat)
        ctype = 5123 if len(pr.pos) < 65536 else 5125
        primitives.append({
            "attributes": {
                "POSITION": accessor(pr.pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(pr.nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(pr.uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(pr.conf, 5126, "SCALAR", 1, 34962),
            },
            "indices": accessor(pr.idx, ctype, "SCALAR", 1, 34963),
            "material": len(materials) - 1,
        })
    name = f"{structure_id}__{phase_id}"
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0, "extras": {
            "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids), **extras,
            "k01": {"contract": "data/components/prairie_1904/k01_contract.json",
                    "components": [a.components[k] for k in sorted(a.components)]}}}],
        "meshes": [{"name": name, "primitives": primitives}],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
    }
    if images:
        gltf |= {"images": images, "textures": textures,
                 "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]}
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)
