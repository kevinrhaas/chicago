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
  k01.opening.sash_flat     a K06 window (T-2298): reveal, frame, two sashes in two
                            planes, glass, blind, curtain edges and an enclosed dark
                            room, a stone sill with its drip; and a flat lintel
  k01.opening.area_light    the basement lights: K06's three-light fixed area light
  k01.opening.door_leaf     a K07 entrance (T-2304): reveal, threshold, frame, a
                            four-panel leaf with its knob, a two-light transom with
                            the dark hall behind it; and a flat lintel
  k01.stair.straight_stoop  K07's straight stoop: whole equal risers from grade to the
                            threshold between cheek walls, clear of the public walk
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
  k08.*                     a K08 bay (T-2308): `generators/archetypes/k08_bays.py`
                            builds it in its own wall frame and `bay` lays it on
                            its host wall, which carries no opening behind it

  and, since T-2289, the stone street front laid from the K02 stone library
  (`data/components/prairie_1904/k02_stone_profiles.json`, read through the record's
  `stone_front`) instead of drawn as one flat face. The kits keep what they build —
  K06 its sills, K09 its heads, aprons and entrance, K07 the stoop, K08 the bay — and
  the walling is laid round them, dressed smooth wherever one of them is seated:

  k01.wall.stone_course     one course of the street front: rock-faced blocks of its
                            own height, each sampling its own window of the fabric
                            (seeded offset and mirror), joints recessed to the
                            mortar, a bevelled arris and sparse chipped corners
  k01.wall.rusticated_base  the base courses, channel-jointed
  k01.wall.coping           the weathered coping over the base: fall, overhang and a
                            drip groove under its nose
  k01.wall.corner_bond      a quoin on the south return, long and short in turn
                            against the front's own corner stone
  k01.opening.flat_arch     voussoirs over every front opening K09 leaves a flat
                            head (the area lights, the third floor), their joints
                            radiating and each stone's bed turned along its joint

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

from . import k03_brick
from . import k09_frontage
from . import k10_frontage

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
    # T-2298: K06's glass (k06_windows.json parts.glass): one thin blended layer, so the
    # blind, the curtain edges and the dark room read through it
    "glass": {"color": (0.05, 0.065, 0.075), "roughness": 0.04, "alpha": 0.32},
    "backing": {"color": (0.018, 0.017, 0.016), "roughness": 1.0},
    # T-2298: what a K06 window holds behind its glass (k06_windows.json parts)
    "blind": {"color": (0.80, 0.74, 0.60), "roughness": 0.95},
    "curtain": {"color": (0.42, 0.16, 0.13), "roughness": 0.9},
    "door_leaf": {"color": (0.29, 0.17, 0.085), "roughness": 0.62},
    # T-2304: K07's hardware (k07_entrances.json parts.hardware): the knob on its rose
    "door_iron": {"color": (0.17, 0.16, 0.15), "roughness": 0.45},
    # T-2310: the K09 kit's carving (capital leaves) apart from its dressed trim
    "carved_trim": {"fabric": "limestone", "color": (0.97, 0.94, 0.87), "roughness": 0.88},
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
# T-2291: the side and rear walls are K03 common brick, not Glessner's courtyard
# brick_buff, and the brick heads, string course and units add their own slots.
MATERIALS.update(k03_brick.MATERIALS)
# T-2308: a K08 bay's own slots. None begins with an envelope material: a bay stands
# proud of its wall by up to a metre, and the contract's envelope is the main range on
# its footprint (the stoop's reasoning, above). Stone bays wear the front's limestone,
# brick bays K03's coursed common-bond panel; dressings, joinery, glass and blinds are
# the house's own slots, so a bay adds no draw call for them. The two bodies differ from
# the walls' slots in roughness alone, and must differ in something: the web derivative
# merges identical materials under one name, which handed the bays to the envelope.
MATERIALS.update({
    "bay_stone": dict(MATERIALS["rough_stone_trim"], roughness=0.9),
    "bay_brick": dict(k03_brick.MATERIALS["brick"], roughness=round(k03_brick.MATERIALS["brick"]["roughness"] + 0.02, 2)),
    "bay_copper": {"color": (0.37, 0.52, 0.45), "roughness": 0.45, "metallic": 0.35},
    "bay_tin": {"color": (0.30, 0.22, 0.18), "roughness": 0.7},
})
# K08 role -> slot; `body` is the bay's fabric (bay_stone or bay_brick), `cover` its
# roof's K04 covering. A came is a leaded light's, which no K01 bay glazes.
K08_ROLES = {"wall": "body", "reveal": "body", "mullion": "body", "roof_back": "body",
             "plinth": "bay_stone", "band": "bay_stone", "corbel": "bay_stone",
             "sill": "bay_stone", "head": "bay_stone", "soffit": "fascia", "fascia": "fascia",
             "frame": "sash", "sash_outer": "sash", "sash_inner": "sash",
             "glass_outer": "glass", "glass_inner": "glass", "blind": "blind",
             "curtain": "curtain", "backing": "backing", "roof": "cover", "finial": "cover"}
SLIVER_M = 0.0025   # T-2308: a bay triangle with an edge shorter than this is a sliver
K08_COVERS = {"copper_standing_seam": "bay_copper", "copper_sheet": "bay_copper",
              "tin_flat_seam_painted": "bay_tin"}


def _tiles() -> dict:
    lib = json.loads((LIBRARY / "material-library.json").read_text())["materials"]
    out = {m["name"]: tuple(m["tile_m"]) for m in lib} | k03_brick.TILES
    for m in json.loads((ROOFS / "manifest.json").read_text())["materials"]:
        out[m["id"]] = tuple(m["tile_m"])
    for m in json.loads((STONE / "manifest.json").read_text())["materials"]:
        out[m["id"]] = tuple(m["tile_m"])
    return out


def _k04_fabric(fab: str) -> dict | None:
    """A K04 fabric's material.json, or None for a fabric from another library."""
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


def _images(fab: str) -> dict:
    """The JPEG(s) a fabric embeds: K03's and K04's from their own libraries (base colour
    and OpenGL normal map), the rest Glessner's base colour alone."""
    if fab in k03_brick.IMAGES:
        return k03_brick.IMAGES[fab]
    k04 = _k04_fabric(fab)
    if k04 is not None:
        # T-2293: the relief a raking sun reads on slate courses and dressed copper
        return {"basecolor": ROOFS / fab / k04["web"]["basecolor"],
                "normal": ROOFS / fab / k04["web"]["normal_gl"]}
    k02 = _k02_fabric(fab)
    if k02 is not None:
        # T-2289: and a K02 stone's, for the grain of a rock face and a dressed arris
        return {"basecolor": STONE / fab / k02["web"]["basecolor"],
                "normal": STONE / fab / k02["web"]["normal_gl"]}
    return {"basecolor": LIBRARY / f"{fab}_basecolor.jpg"}


class Prim:
    """One primitive: one material, flat-shaded faces, metric UVs, a confidence."""

    def __init__(self, name: str, tone=None):
        self.name = name
        self.pos, self.nrm, self.uv, self.conf, self.idx = [], [], [], [], []
        self.tone_of, self.tone = tone, []   # T-2291: the soot/damp mask, per vertex

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
            self.tone.append(self.tone_of(p[1]) if self.tone_of else 1.0)
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
        self.soffit_m = None   # set by build(); the soot band hangs from it
        self.trim_triangles: dict[str, int] = {}   # T-2310: K09 trim, per kit id
        # T-2289: a coursed stone front lays its walling and its trim in K02 fabrics,
        # whose maps carry their own colour, so the factors go to white
        self.spec = {k: dict(v) for k, v in MATERIALS.items()}
        if params.stone:
            st = params.stone
            for slot, fab, rough in (("rough_stone_trim", st["fabric"], st["fabric_roughness"]),
                                     ("limestone_trim", st["trim"], st["trim_roughness"])):
                self.fabric[slot] = fab
                self.spec[slot] |= {"color": (1.0, 1.0, 1.0), "roughness": rough}
        # T-2289: what each kit seats on a wall, as (s0, s1, y0, y1, kind) in that wall's
        # frame, keyed by the frame's origin: the coursed front dresses the stone under it
        self.footprints: dict[tuple, list] = {}

    def seat(self, frame, pts, kind):
        """Note the (s, y) extent of what a kit laid on a wall's face — its points at or
        proud of the face, in the wall's own frame (s along it, y up, d out of it)."""
        on = [q for q in pts if q[2] > -1e-3]
        if on:
            self.footprints.setdefault(tuple(frame[0]), []).append(
                (min(q[0] for q in on), max(q[0] for q in on), min(q[1] for q in on), max(q[1] for q in on), kind))

    def prim(self, name):
        if name not in self.prims:
            tone = None
            if MATERIALS[name].get("condition"):
                tone = lambda y: k03_brick.tone(y, self.soffit_m)
            self.prims[name] = Prim(name, tone)
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

    def basis(self, mat, origin, au, av, seed, phase_u=None, course_v=None):
        fab = self.fabric[mat]
        tu, tv = self.tiles[fab] if fab else (1.0, 1.0)
        if MATERIALS[mat].get("courses"):
            # a coursed fabric (T-2291): v = 0 on a bed joint at grade on every wall, so
            # courses run level round a corner; u is the wall's corner phase, or the
            # seed's whole-module step where no corner sets one
            if phase_u is None:
                phase_u = (seed % 4) / 4.0
            return (origin, au, av, tu, tv, phase_u, 0.0)
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
    def wall(self, cid, mat, O, R, length, height, thickness, holes, extra_breaks=(), bands=(), gaps=()):
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
        phase = None
        if MATERIALS[mat].get("courses"):  # T-2291: the bond turns the quoin
            phase = k03_brick.phase_u(cid, length, self.tiles[MATERIALS[mat]["fabric"]][0])
        b = self.basis(mat, O, R, Y, seed, phase)
        pr = self.prim(mat)
        for i in range(len(sb) - 1):
            for j in range(len(yb) - 1):
                sc, yc = (sb[i] + sb[i + 1]) / 2, (yb[j] + yb[j + 1]) / 2
                if any(h[0] < sc < h[1] and h[2] < yc < h[3] for h in holes):
                    continue
                pr.face([P(sb[i], yb[j], 0), P(sb[i + 1], yb[j], 0),
                         P(sb[i + 1], yb[j + 1], 0), P(sb[i], yb[j + 1], 0)], N, b, conf)
        for (y0, y1, proud) in bands:  # belt courses, part of the wall component
            for s0, s1 in _pieces(0.0, length, gaps):   # T-2308: stopped against a bay
                self.proud_box("limestone_trim", (O, R, N), s0, s1, y0, y1, proud, seed, conf)
        return (O, R, N), thickness

    # -- k01.opening.* ---------------------------------------------------------------
    def opening(self, op, frame, thickness, body_mat, stone_trim, cut=False, coursed=False):
        """`cut`: the reveal is already a solid's (a recess the K05 union cut, T-2302, to
        K06's reveal depth), so K06 sets everything behind it, and its sill and lintel.
        `coursed`: the wall is K02 coursed stone, which lays a flat arch of voussoirs where
        K09 leaves a flat head (T-2289), so no K01 lintel is drawn here."""
        p = self.p
        O, R, N = frame
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        s0, s1 = op.s_m - op.width_m / 2, op.s_m + op.width_m / 2
        y0, y1 = op.sill_m, op.head_m
        conf = p.worst_conf("footprint", "sash_by_storey", "front_bays", "side_bays", "rear_bays")
        door = op.component == "k01.opening.door_leaf"
        if MATERIALS[body_mat].get("courses"):
            conf = max(conf, p.conf("service_wall_brick"))
        recess = self.door_reveal() if door else self.kit_reveal(op)
        params = {"clear_width_m": op.width_m, "clear_height_m": op.height_m, "reveal_m": recess,
                  "wall": op.wall}
        if door:
            params["k07_variant"] = p.entrance_kit["variant"]
        else:
            params["k06_variant"] = p.window_kit[op.component]["variant"]
        seed = self.instance(op.component, "opening", params,
                             {"sill": P(op.s_m, y0, 0), "head": P(op.s_m, y1, 0),
                              "sash_plane": P(op.s_m, y0, -(recess if door else recess + 0.012))})
        if not door:
            # T-2298: a window is a K06 opening — reveal, sill, frame, sashes, glass,
            # blind, curtain and an enclosed room — built about this hole's sill socket
            self.glaze(op, frame, body_mat, stone_trim, seed, conf, skip=("reveal",) if cut else ())
        else:
            # T-2304: the door is a K07 entrance and its stoop, built about the threshold
            self.enter(op, frame, body_mat, seed, conf)
        if MATERIALS[body_mat].get("courses") and not door:
            # T-2291: a brick wall's opening takes a brick head, not the front's stone
            # lintel — two rowlock rings on a segmental arch, or a soldier flat head
            # where the eave leaves no room for the rings and their rise
            crown = y1 + k03_brick.RISE_TO_SPAN * op.width_m + k03_brick.RINGS * (k03_brick.BED + k03_brick.JOINT)
            if crown < self.soffit_m - k03_brick.COURSE:
                k03_brick.segmental_head(self, seed, frame, s0, s1, y1, conf)
            else:
                k03_brick.soldier_head(self, seed, frame, s0, s1, y1, conf)
            return
        # T-2310: a K09 head where the record names one; else a flat lintel
        if k09_frontage.dress(self, op, frame, max(conf, p.conf("street_front_trim"))) or coursed:
            return
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
            # a split face, not a pyramid: an inner ring of points drawn in towards a
            # wandering crown, each at its own height under the stone's projection, so
            # the facets a raking sun picks out differ from stone to stone
            ws = max(q[0] for q in front) - min(q[0] for q in front)
            hs = max(q[1] for q in front) - min(q[1] for q in front)
            cs = sum(q[0] for q in front) / n + rng.uniform(-0.2, 0.2) * ws
            cy = sum(q[1] for q in front) / n + rng.uniform(-0.2, 0.2) * hs
            apex = P((cs, cy), F + rock)
            inner = []
            for q in ring:
                k_ = rng.uniform(0.35, 0.7)
                inner.append(P((cs + (q[0] - cs) * k_, cy + (q[1] - cy) * k_), F + rock * rng.uniform(0.35, 0.9)))
            m_ = len(ring)
            for i in range(m_):
                a_, b_ = P(ring[i], F), P(ring[(i + 1) % m_], F)
                ia, ib = inner[i], inner[(i + 1) % m_]
                for tri in ((a_, b_, ib), (a_, ib, ia), (ia, ib, apex)):
                    self._sface(mat, list(tri), N, origin, bed, seed, mirror, conf, project=False)
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
        """The street front as K02 coursed ashlar, laid round what the kits have already
        seated on it (`self.footprints`: K06 sills, K07's stoop, K09's heads, aprons and
        entrance, K08's bay). Course lines are struck on the base, the coping, every K06
        sill's bed, every head and flat-arch top and the belts, and the walling between
        them is cut into equal courses inside the profile's range. An opening or a flat
        arch is a hole in a course; where a kit is seated, the course goes on but its
        stones are dressed smooth and laid flush (no rock face, no chip, a belt not
        proud), so every kit piece stands on a plane face, never on a rock face that
        would bury its foot. Returns the south corner's quoins for the side wall."""
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
        holes = [(o.s_m - o.width_m / 2, o.s_m + o.width_m / 2, o.sill_m, o.head_m) for o in openings]
        # a flat arch where K09 leaves a flat head: the area lights and the third floor
        arches = [(s0, s1, y1, round(y1 + 0.30, 4)) for o, (s0, s1, _, y1) in zip(openings, holes)
                  if k09_frontage.head(p, o) == k09_frontage.FLAT]
        # what the kits seat on this face, widened by a joint and an arris so a piece's
        # edge never stands over a bevel; K06's sill beds are course lines
        m = wk["joint_m"] / 2 + wk["bevel_m"] + 0.01
        seats = [(a0 - m, a1 + m, b0 - m, b1 + m, kind) for a0, a1, b0, b1, kind in self.footprints.get(tuple(O), [])]
        sill_beds = {round(b0 + m, 4) for _, _, b0, _, kind in seats if kind == "K06.sill"}
        belts = [(floors[1] - 0.20, floors[1])] + ([(floors[2] - 0.15, floors[2])] if len(floors) > 2 else [])
        lines = {0.0, cop_top, yf, *[bc * i for i in range(1, k["base_courses"] + 1)]}
        lines |= {y for y in sill_beds if y > cop_top + 1e-6}
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
                n_ = math.ceil((yb - ya) / hi_c - 1e-9)
                courses += [(ya + (yb - ya) * i / n_, ya + (yb - ya) * (i + 1) / n_, "walling") for i in range(n_)]
        rects = holes + arches
        quoins, prev_joints, parity = [], [], 0
        for ya, yb, kind in courses:
            trim = kind in ("coping", "belt", "band")
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
            here = [q for q in seats if q[2] < yb - 1e-6 and q[3] > ya + 1e-6]
            # a seat's edge cuts the course too, unless it falls within 0.08 m of a harder
            # edge (a wall end, an opening, an arch) or of another seat's: no sliver stones
            S = sorted({0.0, length, *[min(max(x, 0.0), length) for o in obs for x in (o[0], o[1])]})
            for x in sorted(min(max(x, 0.0), length) for q in here for x in (q[0], q[1])):
                if all(abs(x - e) >= 0.08 for e in S):
                    S = sorted([*S, x])
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
                if spans and spans[-1][2] == free and abs(spans[-1][1] - sa) < 1e-9 \
                        and spans[-1][3] == self._seated(here, sa, sb):
                    spans[-1][1] = sb
                else:
                    spans.append([sa, sb, free, self._seated(here, sa, sb)])
            joints_here, j = [], 0
            corner = "south" in k["corners"] and kind in ("base", "walling")
            for sa, sb, free, _ in spans:
                for fy0, fy1 in free:
                    first = None
                    if corner and sa == 0.0 and abs(fy0 - ya) < 1e-9 and abs(fy1 - yb) < 1e-9 \
                            and not self._seated(here, 0.0, min(sb, hi), fy0, fy1):
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
                        # a kit seated on this stone: dressed smooth and flush, of the trim
                        flush = self._seated(here, s0, s1, fy0, fy1)
                        if kind == "coping" and not flush:
                            self.coping_piece(frame, s0, s1, fy0, fy1, joints, bseed, conf, r)
                        else:
                            dressed = trim or flush
                            brng = random.Random(bseed ^ 0x5EED)
                            rock = brng.uniform(*k["rock_face_m"]) if not dressed else 0.0
                            skip = self.stone(frame, [(s0, fy0), (s1, fy0), (s1, fy1), (s0, fy1)], joints,
                                              "limestone_trim" if dressed else "rough_stone_trim",
                                              bseed, conf, recess=r, bevel=(tk if dressed else wk)["bevel_m"],
                                              F=0.05 if kind == "belt" and not flush else 0.0, rock=rock,
                                              chips=None if dressed else spec, skip=skip if not dressed else frozenset())
                        if kind == "base" and abs(fy1 - base_top) < 1e-6:
                            # the rusticated base's channels are deeper than the joints over
                            # it: a ledge closes the step between the two mortar floors
                            self.prim("mortar").face([_add(_add(O, _mul(R, s)), _add(_mul(Y, base_top), _mul(N, d)))
                                                      for s, d in ((s0, -r_base), (s1, -r_base), (s1, -r_wall), (s0, -r_wall))],
                                                     _mul(Y, -1), self.basis("mortar", O, R, N, bseed), conf)
                        if 1e-9 < s1 < length - 1e-9:
                            joints_here.append(s1)
            prev_joints = joints_here
        for s0, s1, y1, y2 in arches:
            self.flat_arch(frame, s0, s1, y1, y2 - y1, conf, r_wall)
        # the wall behind the soffit, up to the eave: inside the roof, one plain face
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        if E - yf > 1e-6:
            self.prim("rough_stone_trim").face([P(0.0, yf, 0.0), P(length, yf, 0.0), P(length, E, 0.0), P(0.0, E, 0.0)],
                                               N, self.basis("rough_stone_trim", O, R, Y, 0), conf)
        return frame, quoins

    @staticmethod
    def _seated(seats, s0, s1, y0=None, y1=None) -> bool:
        """Does any kit stand on the cell [s0, s1] x [y0, y1] (any height if y is None)?"""
        return any(q[0] < s1 - 1e-6 and q[1] > s0 + 1e-6
                   and (y0 is None or (q[2] < y1 - 1e-6 and q[3] > y0 + 1e-6)) for q in seats)

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

    # -- K06 glazing (T-2298) ------------------------------------------------------------
    # K06 role -> this assembly's material. The reveal is the wall's own body and the
    # sill the front's stone trim; the head band is left out, since the K01 lintel (or a
    # brick wall's own head) dresses the head. A role not named here — a mullion, a
    # came, a well — is one this house's variants do not build, and is refused.
    K06_ROLES = {"reveal": None, "sill": "stone", "frame": "sash", "sash_outer": "sash",
                 "sash_inner": "sash", "glass_outer": "glass", "glass_inner": "glass",
                 "blind": "blind", "curtain": "curtain", "backing": "backing"}

    def kit_variant(self, op) -> dict:
        from . import k06_windows
        if not hasattr(self, "_kit"):
            self._kit = k06_windows.load()
        entry = self.p.window_kit[op.component]
        v = dict(next(x for x in self._kit["variants"] if x["id"] == entry["variant"]))
        v["clear_width_m"], v["clear_height_m"] = op.width_m, op.height_m
        if not entry["well"]:
            v["well"] = False
        return v

    def kit_reveal(self, op) -> float:
        self.kit_variant(op)
        v = next(x for x in self._kit["variants"] if x["id"] == self.p.window_kit[op.component]["variant"])
        return v.get("overrides", {}).get("reveal_depth_m", self._kit["parts"]["reveal_depth_m"]["value"])

    def glaze(self, op, frame, body_mat, stone_trim, seed, conf, skip=()):
        from . import k06_windows
        O, R, N = frame
        # T-2310: under a K09 architrave the sill's horns run past its outer edge, so the
        # architrave's open feet stand on the sill and never hang over the wall
        kit, reach = self._kit, k09_frontage.sill_reach(self.p, op)
        if reach > kit["parts"]["sill"]["horn_m"]:
            kit = dict(kit, parts=dict(kit["parts"], sill=dict(kit["parts"]["sill"], horn_m=reach)))
        o = k06_windows.Opening(self.kit_variant(op), kit)
        o.seed = seed                      # the blind's drop follows this instance, not the kit's
        o.build()
        roles = {r: (stone_trim if m == "stone" else (m or body_mat)) for r, m in self.K06_ROLES.items()}
        self.graft(o, "K06", roles, frame, op, lambda role: (seed, conf), skip)

    def graft(self, o, kit, roles, frame, op, seed_conf, skip=()):
        """Carry a kit's built opening into this assembly. A kit's frame is +X along the
        wall, +Y up, +Z out of it, its origin at the opening's socket on the outer face (a
        K06 sill, a K07 threshold); `roles` maps each kit role to this assembly's material.
        The head band is left out: the K01 flat lintel (or a brick wall's own head)
        dresses every head."""
        O, R, N = frame
        base = _add(O, _add(_mul(R, op.s_m), _mul(Y, op.sill_m)))
        W = lambda q: _add(base, _add(_add(_mul(R, q[0]), _mul(Y, q[1])), _mul(N, q[2])))
        for role, src in o.prims.items():
            if role == "head" or role in skip:   # `skip`: a role a solid already carries
                continue
            if role not in roles:
                raise ValueError(f"{kit} role {role!r} has no material on a K01 frontage")
            mat = roles[role]
            seed, conf = seed_conf(role)
            fab = self.fabric[mat]
            tu, tv = self.tiles[fab] if fab else (1.0, 1.0)
            _, _, _, _, _, ou, ov = self.basis(mat, O, R, Y, seed)
            dst = self.prim(mat)
            off = len(dst.pos)
            for q, n, uv in zip(src.pos, src.nrm, src.uv):
                dst.pos.append(W(q))
                dst.nrm.append(_add(_add(_mul(R, n[0]), _mul(Y, n[1])), _mul(N, n[2])))
                # K06 writes metres (tile 1, no offset); a fabric divides by its own tile
                dst.uv.append((uv[0] / tu + ou, uv[1] / tv + ov) if fab else uv)
                dst.conf.append(conf)
                dst.tone.append(dst.tone_of(dst.pos[-1][1]) if dst.tone_of else 1.0)  # T-2291's mask
            dst.idx += [off + i for i in src.idx]
            if role != "reveal":   # the reveal is the hole's own edge
                self.seat(frame, [(op.s_m + q[0], op.sill_m + q[1], q[2]) for q in src.pos], f"{kit}.{role}")

    # -- k08.* bays (T-2308) -------------------------------------------------------------
    def bay(self, b, frame) -> tuple:
        """Lay one K08 bay on its host wall; return where its roof meets the wall, and
        the stretch of the wall (s from, s to) the bay's eaves and bands reach along it.

        `k08_bays.Bay` builds the bay in its own frame — +X along the wall to the right
        seen from outside, +Y up, +Z out of the wall's face — which is a K01 wall's
        (R, Y, N) about the bay's centre, so the map is a translation and no winding
        turns. A brick bay's courses are re-anchored to grade, as the K03 wall's are,
        so the two meet course for course at each junction."""
        from . import k08_bays as K8
        p = self.p
        O, R, N = frame
        v = b["variant"]
        built = K8.Bay(v, K8.load(), "full").build(board=False)
        conf = p.conf("bays")
        seed = self.instance(f"k08.{v['kind']}", "bay",
                             {"k08_variant": b["id"], "plan": v["plan"]["kind"], "storeys": len(v["storeys"]),
                              "wall_top_m": built.meta["wall_top_m"], "projection_m": built.meta["plan"]["projection_m"],
                              "windows": len(built.windows), "wall": b["wall"]},
                             {"junction_left": _add(O, _mul(R, b["span_m"][0])),
                              "junction_right": _add(O, _mul(R, b["span_m"][1]))})
        base = _add(O, _mul(R, b["s_m"]))
        W = lambda q: _add(base, _add(_add(_mul(R, q[0]), _mul(Y, q[1])), _mul(N, q[2])))
        body = "bay_brick" if b["fabric"] == "brick" else "bay_stone"
        cover = K08_COVERS[v["roof"]["covering"]]
        for role, src in built.prims.items():
            if role not in K08_ROLES:
                raise ValueError(f"K08 role {role!r} has no material on a K01 frontage")
            mat = {"body": body, "cover": cover}.get(K08_ROLES[role], K08_ROLES[role])
            spec = MATERIALS[mat]
            fab = self.fabric[mat]
            tu, tv = self.tiles[fab] if fab else (1.0, 1.0)
            _, _, _, _, _, ou, ov = self.basis(mat, O, R, Y, seed)
            dst = self.prim(mat)
            off = len(dst.pos)
            # On the contract's 1 mm grid (k01_contract.json `quantum_m`): the web
            # derivative quantizes positions to a third of that, so a vertex already on
            # the grid keeps its millimetre there and the two tiers read the same faces.
            world = [tuple(round(c * 1000) / 1000 for c in W(q)) for q in src.pos]
            for q, n, uv, w in zip(src.pos, src.nrm, src.uv, world):
                dst.pos.append(w)
                dst.nrm.append(_add(_add(_mul(R, n[0]), _mul(Y, n[1])), _mul(N, n[2])))
                if spec.get("courses") and abs(n[1]) < 0.5:
                    dst.uv.append((uv[0] / tu + ou, -q[1] / tv))   # v = 0 at grade, as K03's walls
                else:
                    dst.uv.append((uv[0] / tu + ou, uv[1] / tv + ov) if fab else uv)
                dst.conf.append(conf)
                dst.tone.append(dst.tone_of(dst.pos[-1][1]) if dst.tone_of else 1.0)
            # A sliver is not a face (the contract's coincidence measure): where the kit's
            # slab cuts leave a triangle with an edge under SLIVER_M, it is dropped rather
            # than shipped. Such a triangle is never wider than that edge, and the web
            # derivative collapses it to a degenerate one anyway (T-2308 measured 46 there).
            for t in range(0, len(src.idx), 3):
                i, j, k = src.idx[t:t + 3]
                if min(math.dist(world[i], world[j]), math.dist(world[j], world[k]),
                       math.dist(world[i], world[k])) >= SLIVER_M:
                    dst.idx += [off + i, off + j, off + k]
        # T-2289: everything the bay stands against its wall with, junctions to roof
        self.seat(frame, [(b["s_m"] + q[0], q[1], 0.0 if q[2] < 0.02 else -1.0)
                          for pr in built.prims.values() for q in pr.pos], "k08")
        roof = built.prims.get("roof")
        top = max(q[1] for q in roof.pos if abs(q[2]) < 1e-6) if roof else built.meta["eave_m"]
        xs = [q[0] for pr in built.prims.values() for q in pr.pos]
        return top, (b["s_m"] + min(xs), b["s_m"] + max(xs))

    # -- K07 entrance (T-2304) ------------------------------------------------------------
    # K07 role -> this assembly's material: the reveal in the front's own stone, the
    # threshold and every part of the stoop in the stoop stone, the frame, leaf and transom
    # sash in the door's joinery, the knob iron, the transom's glass and the dark hall
    # behind it the windows' own. A role not named here — a porch, an area wall, a guard
    # stone — is one this house's variant does not build, and is refused.
    K07_ROLES = {"reveal": None, "threshold": "stoop_stone", "landing": "stoop_stone",
                 "tread": "stoop_stone", "riser": "stoop_stone", "stair_end": "stoop_stone",
                 "cheek": "stoop_stone", "frame": "door_leaf", "leaf": "door_leaf",
                 "sash_outer": "door_leaf", "glass_outer": "glass", "glass_leaf": "glass",
                 "hardware": "door_iron", "backing": "backing"}
    STAIR_ROLES = frozenset({"landing", "tread", "riser", "stair_end", "cheek"})

    def door_variant(self) -> dict:
        """The record's K07 variant at this house's own door and stoop: the K01 hole's clear
        size, and the stair solved from its principal floor, tread, landing and width."""
        from . import k07_entrances
        p = self.p
        if not hasattr(self, "_entrances"):
            self._entrances = k07_entrances.load()
        v = dict(next(x for x in self._entrances["variants"] if x["id"] == p.entrance_kit["variant"]))
        door = next(o for o in p.openings if o.component == "k01.opening.door_leaf")
        v["clear_width_m"], v["clear_height_m"] = door.width_m, door.height_m
        v["stair"] = dict(v["stair"], floor_m=p.principal_floor_m, going_m=p.tread_m,
                          landing_m=p.landing_depth_m, width_m=p.stoop_width_m)
        v["front_yard_m"] = p.entrance_kit["front_yard_m"]
        return v

    def door_reveal(self) -> float:
        v = self.door_variant()
        return v.get("reveal_depth_m", self._entrances["parts"]["reveal_depth_m"]["value"])

    def enter(self, op, frame, body_mat, seed, conf):
        from . import k07_entrances
        p = self.p
        O, R, N = frame
        o = k07_entrances.Entrance(self.door_variant(), self._entrances)
        o.seed = seed
        o.build()
        st = o.meta["stair"]
        if st["risers"] != p.risers:
            raise ValueError(f"K07 built {st['risers']} risers and the K01 stair solves {p.risers}")
        # the walk rule, on the built mesh: nothing the entrance builds reaches the walk
        reach = max(q[2] for pr in o.prims.values() for q in pr.pos)
        if reach >= p.entrance_kit["front_yard_m"]:
            raise ValueError(f"the entrance reaches {reach:.3f} m from the front, onto the walk at "
                             f"{p.entrance_kit['front_yard_m']} m")
        stair_conf = p.worst_conf("principal_floor_m", "stair_tread_m", "stair_landing_depth_m", "stoop_width_m")
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        stair_seed = self.instance("k01.stair.straight_stoop", "stair",
                                   {"riser_m": st["riser_m"], "tread_m": st["going_m"], "risers": st["risers"],
                                    "landing_depth_m": p.landing_depth_m, "width_m": p.stoop_width_m,
                                    "k07_variant": p.entrance_kit["variant"], "cheeks": True,
                                    "front_yard_m": p.entrance_kit["front_yard_m"]},
                                   {"foot": P(op.s_m, 0.0, st["foot_out_m"]), "landing": P(op.s_m, op.sill_m, 0.0),
                                    **{f"{k}_{end}": P(op.s_m + q[0], op.sill_m + q[1], q[2])
                                       for k, ends in sorted(o.sockets.items())
                                       for end, q in zip(("top", "foot"), ends)}})
        roles = {r: (m or body_mat) for r, m in self.K07_ROLES.items()}
        self.graft(o, "K07", roles, frame, op,
                   lambda role: (stair_seed, stair_conf) if role in self.STAIR_ROLES else (seed, conf))

    # -- k01.roof.hip, built from the K05 roof-construction kit (T-2302) -------------
    def roof(self):
        """The roof as ONE closed solid (K05, T-2302). The hip, the street dormer and the
        chimney stacks are each a closed element from `k05_roofs`, joined by the kit's
        boolean union, and the dormer's sash recess is cut out of the result, so every
        valley, cheek, stack and reveal is cut where its surfaces really meet: no plane
        crosses another, nothing floats and no face is drawn twice. The K04 dressing
        (caps, valley flashing, apron, step flashing) is then laid on the ROOF GRAPH read
        off that surface, not on numbers of its own."""
        from . import k05_roofs as k5
        p, k = self.p, self.p.roof or {}
        kit = k5.load()
        D, W, E, o = p.depth_m, p.width_m, p.eave_m, p.eave_overhang_m
        tp = math.tan(math.radians(p.roof_pitch_deg))
        f = kit["parts"]["eave"]["fascia_depth_m"]
        ye = E - o * tp
        yf = ye - f
        yr = p.ridge_m
        conf = p.worst_conf("footprint", "roof_form", "roof_pitch_deg", "eave_overhang_m", "roof_covering")
        seed = self.instance("k01.roof.hip", "roof",
                             {"pitch_deg": p.roof_pitch_deg, "eave_overhang_m": o,
                              "eave_datum_m": E, "ridge_datum_m": yr, "construction": "k05",
                              "fascia_depth_m": f, "chimneys": len(p.chimneys),
                              **({"covering": k["covering"], "flashing": k["flashing"]} if k else {}),
                              **({"gutter_diameter_m": p.rainwater["gutter_diameter_m"], "gutter_fall": p.rainwater["fall"],
                                  "downpipes": len(p.rainwater["downpipes"]),
                                  "pipe_diameter_m": p.rainwater["pipe_diameter_m"]} if p.rainwater else {})},
                             {"eave": (0.0, E, 0.0), "ridge": (W / 2, yr, -W / 2)})
        # the elements: the hip over the wall line, a body under it (the walls' tops,
        # so the soffit is a ring and not a lid; never emitted), the dormer, the stacks
        hip, hs = k5.hip_element(0.0, D, -W, 0.0, E, tp, o, f)
        solids = [hip, k5.body_box(0.0, D, -W, 0.0, hs - 1.0, hs)]
        recess = None
        d = p.dormer
        if d:
            dp = kit["parts"]["dormer"]
            dt = math.tan(math.radians(d["pitch_deg"]))
            wd, sb, hf = d["width_m"], d["face_setback_m"], d["face_height_m"]
            xf = D - sb                       # the face, on the street hip
            ys = E + sb * tp                  # its foot, where it leaves the covering
            yde = ys + hf                     # the dormer's eave, at its wall line
            zc = -W / 2
            back = D - (yde + wd / 2 * dt - E) / tp - 0.5   # behind where its ridge dies
            g, dhs, dhe, dry = k5.gable_element(back, xf, zc - wd / 2, zc + wd / 2, yde, dt, dp["overhang_m"],
                                                d["verge_m"], dp["fascia_depth_m"], hs, "x", verge_ends=("hi",),
                                                wall_role="cheek", end_role="dormer_face",
                                                body_end_role="dormer_face")
            solids += g
            sw, ss, sh = d["sash"]["width_m"], d["sash"]["sill_m"], d["sash"]["height_m"]
            P = k5.frame("z")
            # the recess is K06's reveal, cut to K06's depth: its back is where the K06
            # frame, sashes and dark room stand (`window`, never emitted; dormer_sash)
            from types import SimpleNamespace
            rev = self.kit_reveal(SimpleNamespace(component="k01.opening.sash_flat", width_m=sw, height_m=sh))
            recess = k5.extrude([(xf - rev, ys + ss), (xf + 0.05, ys + ss),
                                 (xf + 0.05, ys + ss + sh), (xf - rev, ys + ss + sh)],
                                zc - sw / 2, zc + sw / 2, P,
                                lambda i, p_, q_: "window" if i == 3 else "reveal", "reveal", "reveal")
            self.dormer_geom = {"xf": xf, "ys": ys, "yde": yde, "dhs": dhs, "dhe": dhe, "ridge": dry,
                                "zs": zc + wd / 2, "zn": zc - wd / 2}
        for c in p.chimneys:
            sx, sz = c["plan_m"]
            u, z = c["u_m"], -c["v_m"]
            top = c["top_m"]
            P = k5.frame("z")
            cp, cd = c["cap_proud_m"], c["cap_depth_m"]
            # the stack stops inside its cap, so the two never share a face
            solids.append(k5.extrude([(u - sx / 2, hs - 0.5), (u + sx / 2, hs - 0.5), (u + sx / 2, top - cd / 2),
                                      (u - sx / 2, top - cd / 2)], z - sz / 2, z + sz / 2, P,
                                     lambda i, p_, q_: "chimney" if i != 2 else "hidden", "chimney", "chimney"))
            solids.append(k5.extrude([(u - sx / 2 - cp, top - cd), (u + sx / 2 + cp, top - cd),
                                      (u + sx / 2 + cp, top), (u - sx / 2 - cp, top)],
                                     z - sz / 2 - cp, z + sz / 2 + cp, P, "coping", "coping", "coping"))
        polys = k5.union_all(k5._snap(solids))
        if recess is not None:
            polys = k5.subtract(polys, k5._snap([recess])[0])
        pts, tris = k5.close(polys)
        self.roof_shell = (pts, tris)
        self.roof_graph = k5.graph(pts, tris, kit)
        self._emit_shell(pts, tris, seed, conf)
        if d:
            self.dormer_sash(seed)
        if k:
            self.dress(pts, tris, seed, conf)
        if p.rainwater:
            self.rainwater(ye, yf, seed)
        return yf

    # role -> material: what the union named each face, and what a renderer binds to it
    SHELL = {"covering": "slate_covering", "cheek": "slate_covering", "fascia": "fascia",
             "soffit": "fascia", "verge": "fascia", "return": "fascia", "dormer_face": "dormer_stone",
             "reveal": "dormer_stone", "backing": "backing", "chimney": "brick", "coping": "limestone_trim"}
    BOARD = ("wall", "base")   # the body under the roof: the walls' own business
    OPEN = ("window",)         # the sash recess's back: the K06 opening set in it closes it

    def _emit_shell(self, pts, tris, seed, conf):
        """Each triangle into its material, with metric UVs: a covering's courses run up
        its own plane from that plane's lowest point (its eave), so a course is never cut
        at the eave and every fragment the union left of one plane registers."""
        k = self.p.roof or {}
        phase = (_k04_fabric(k["covering"]) or {}).get("course_phase_m", [0.0, 0.0])[1] if k else None
        planes = {}
        for a, b, c, role, n in tris:
            if role == "covering":
                key = tuple(round(x, 5) for x in n) + (round(_dot(n, pts[a]), 4),)
                low = min((pts[a], pts[b], pts[c]), key=lambda q: q[1])
                if key not in planes or low[1] < planes[key][1]:
                    planes[key] = low
        for a, b, c, role, n in tris:
            if role in self.BOARD or role in self.OPEN:
                continue
            if role not in self.SHELL:
                raise ValueError(f"the K05 union left a {role!r} face on the roof")
            mat = self.SHELL[role]
            tri = [pts[a], pts[b], pts[c]]
            if role == "covering":
                key = tuple(round(x, 5) for x in n) + (round(_dot(n, pts[a]), 4),)
                up = _unit(_sub(Y, _mul(n, n[1])))
                contour = _unit(_cross(up, n))
                b_ = self.basis(mat, planes[key], contour, up, seed, course_v=phase)
            elif abs(n[1]) > 0.999:
                b_ = self.basis(mat, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), seed)
            else:
                au = _unit(_cross(Y, n))
                b_ = self.basis(mat, (0.0, 0.0, 0.0), au, _cross(n, au), seed)
            self.prim(mat).face(tri, n, b_, conf)

    def dormer_sash(self, roof_seed):
        """The dormer's face: a K01 wall component whose surface is the union's, and its
        sash set in the recess the union cut (the reveal is the solid's, K06 the rest)."""
        p, d, g = self.p, self.p.dormer, self.dormer_geom
        from archetypes.k01_frontage_params import Opening
        wd, hf = d["width_m"], d["face_height_m"]
        O = (g["xf"], g["ys"], g["zs"])
        R = (0.0, 0.0, -1.0)
        self.instance("k01.wall.dormer_face", "wall", {"length_m": wd, "height_m": hf,
                                                       "thickness_m": d["face_thickness_m"],
                                                       "construction": "masonry", "openings": 1},
                      {"base": O, "top": _add(O, _mul(Y, hf))})
        self.opening(Opening("k01.opening.sash_flat", "k01.wall.dormer_face", wd / 2, d["sash"]["sill_m"],
                             d["sash"]["width_m"], d["sash"]["height_m"]), (O, R, _cross(R, Y)),
                     d["face_thickness_m"], "dormer_stone", "limestone_trim", cut=True)

    # -- K04 on the K05 graph: caps on ridges and hips, flashing in valleys -------------
    def _line_planes(self, pts, tris, A, B):
        """The covering planes meeting along the line A-B: their normals, in order."""
        L = _sub(B, A)
        LL = _dot(L, L)
        out = []
        for a, b, c, role, n in tris:
            if role != "covering":
                continue
            on = 0
            for q in (pts[a], pts[b], pts[c]):
                s = _dot(_sub(q, A), L) / LL
                e = _sub(_sub(q, A), _mul(L, s))
                on += -1e-6 <= s <= 1 + 1e-6 and _dot(e, e) < 1e-8
            if on >= 2 and not any(_dot(n, m) > 0.9999 for m in out):
                out.append(n)
        return out

    def dress(self, pts, tris, seed, conf):
        k = self.p.roof
        lift = 2 * k["slate_thickness_m"]
        self.dressed = {"ridge": 0, "hip": 0, "valley": 0}
        for line in self.roof_graph["lines"]:
            kind = line["kind"]
            if kind not in ("ridge", "hip", "valley"):
                continue
            A, B = tuple(line["from"]), tuple(line["to"])
            if A[1] > B[1]:
                A, B = B, A                       # A is the low end: the eave's, on a hip
            ns = self._line_planes(pts, tris, A, B)
            if len(ns) != 2:
                raise ValueError(f"the {kind} {A}-{B} does not part two covering planes ({len(ns)})")
            n1, n2 = ns
            if kind == "valley":
                self.valley(A, B, n1, n2, lift, seed, conf)
            elif kind == "hip":
                eaves = tuple(_unit((n[2], 0.0, -n[0])) for n in ns)
                self.cap(A, B, n1, n2, lift, seed, conf, eave=eaves)
            else:
                self.cap(A, B, n1, n2, lift + 0.002, seed, conf)
            self.dressed[kind] += 1
        if self.p.dormer:
            self.dormer_flashing(seed, lift)

    def valley(self, V0, V1, nA, nB, lift, seed, conf):
        """An open valley: a sheet on each plane widening downhill, a crimped rib up the middle."""
        k = self.p.roof
        mat = self._flashing()
        fl = self.prim(mat)
        Lv = _unit(_sub(V1, V0))
        length = math.dist(V0, V1)
        half0 = (k["valley_exposed_at_top_m"] + k["valley_widening_per_m"] * length) / 2
        half1 = k["valley_exposed_at_top_m"] / 2
        rib = _unit(_add(nA, nB))
        for n, other in ((nA, nB), (nB, nA)):
            q = _unit(_cross(n, Lv))
            if _dot(q, other) < 0:
                q = _mul(q, -1)               # up this plane, away from the valley
            a0, a1 = _add(V0, _mul(n, lift)), _add(V1, _mul(n, lift))
            fl.face([a0, a1, _add(a1, _mul(q, half1)), _add(a0, _mul(q, half0))], n,
                    self.basis(mat, a0, Lv, q, seed), conf)
            b0, b1 = _add(a0, _mul(q, 0.012)), _add(a1, _mul(q, 0.012))
            c0, c1 = _add(V0, _mul(rib, lift + k["valley_crimp_m"])), _add(V1, _mul(rib, lift + k["valley_crimp_m"]))
            fl.quad(b0, b1, c1, c0, _add(n, _mul(q, -1)), self.basis(mat, b0, Lv, _unit(_sub(c0, b0)), seed), conf)

    def dormer_flashing(self, seed, lift):
        """The apron under the face and step flashing up each cheek, on the abutment
        lines the K05 dormer leaves on the street hip."""
        p, k, g = self.p, self.p.roof, self.dormer_geom
        conf = p.worst_conf("roof_form", "roof_pitch_deg", "dormer")
        D, E = p.depth_m, p.eave_m
        tp = math.tan(math.radians(p.roof_pitch_deg))
        n_main = _unit((tp, 1.0, 0.0))
        mat = self._flashing()
        fl = self.prim(mat)
        X = (1.0, 0.0, 0.0)
        xf, ys, zs, zn = g["xf"], g["ys"], g["zs"], g["zn"]
        dd = _unit((1.0, -tp, 0.0))
        a_s = _add((xf, ys, zs + k["step_leg_m"]), _mul(n_main, lift))
        a_n = _add((xf, ys, zn - k["step_leg_m"]), _mul(n_main, lift))
        fl.face([a_s, a_n, _add(a_n, _mul(dd, k["apron_lap_m"])), _add(a_s, _mul(dd, k["apron_lap_m"]))], n_main,
                self.basis(mat, a_s, (0.0, 0.0, -1.0), _mul(dd, -1), seed), conf)
        ux = xf + 0.006
        fl.face([(ux, ys, zs), (ux, ys, zn), (ux, ys + k["apron_upstand_m"], zn), (ux, ys + k["apron_upstand_m"], zs)], X,
                self.basis(mat, (ux, ys, zs), (0.0, 0.0, -1.0), Y, seed), conf)
        # the cheek stands on the hip from the face's foot up to the dormer's soffit
        xl = D - (g["dhs"] - E) / tp
        for sgn, z_e in ((1.0, zs), (-1.0, zn)):
            f0 = _add((xf, ys, z_e), _mul(n_main, lift + 0.002))
            f1 = _add((xl, g["dhs"], z_e), _mul(n_main, lift + 0.002))
            Ls = _unit(_sub(f1, f0))
            out = (0.0, 0.0, sgn)
            fl.face([f0, f1, _add(f1, _mul(out, k["step_leg_m"])), _add(f0, _mul(out, k["step_leg_m"]))], n_main,
                    self.basis(mat, f0, Ls, out, seed), conf)
            u0, u1 = (xf, ys, z_e + sgn * 0.006), (xl, g["dhs"], z_e + sgn * 0.006)
            up = (0.0, min(k["step_upstand_m"], g["dhs"] - ys), 0.0)
            fl.face([u0, u1, _add(u1, up), _add(u0, up)], out, self.basis(mat, u0, Ls, Y, seed), conf)

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


def _pieces(s0, s1, gaps):
    """[s0, s1] less every (a, b) gap: what is left of a course a bay stops."""
    out, at = [], s0
    for a, b in sorted(gaps):
        if a > at:
            out.append((at, min(a, s1)))
        at = max(at, b)
    if at < s1:
        out.append((at, s1))
    return [(a, b) for a, b in out if b - a > 1e-6]


def build(params, structure_id: str):
    """The assembly: walls with their openings cut, the entrance and its stoop, the roof."""
    p = params
    a = Assembly(structure_id, p)
    D, W, E = p.depth_m, p.width_m, p.eave_m
    yf = E - p.eave_overhang_m * math.tan(math.radians(p.roof_pitch_deg)) - 0.20
    a.soffit_m = yf
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
    gaps = {cid: [bay["span_m"] for bay in p.bays if bay["wall"] == cid] for cid in walls}
    frames, laid = {}, {}
    if p.stone:
        # T-2289: a coursed stone front is laid round what the kits seat on it, so the
        # openings and the bays are built first, each noting its footprint on its wall
        frames = {cid: (((O, R, _cross(R, Y)), t), mat) for cid, (mat, O, R, length, t, bands) in walls.items()}
        for op in p.openings:
            (frame, t), mat = frames[op.wall]
            a.opening(op, frame, t, mat, "limestone_trim", coursed=op.wall == "k01.wall.street_front")
        for bay in p.bays:
            laid[bay["id"]] = a.bay(bay, frames[bay["wall"]][0][0])
        mat, O, R, length, t, _ = walls["k01.wall.street_front"]
        front = [o for o in p.openings if o.wall == "k01.wall.street_front"]
        frame, quoins = a.stone_front("k01.wall.street_front", O, R, length, E, yf, t, front)
        for cid, (mat, O, R, length, t, bands) in walls.items():
            if cid == "k01.wall.street_front":
                continue
            breaks = (yf, *k03_brick.condition_breaks(yf)) if MATERIALS[mat].get("condition") else (yf,)
            # the south corner's quoins are cut out of the brick they return into
            bond = [(length - q[0], length, q[1], q[2]) for q in quoins] if cid == "k01.wall.side.south" else []
            a.wall(cid, mat, O, R, length, E, t, holes(cid) + bond, breaks, bands, gaps[cid])
        if quoins:
            a.quoins(frames["k01.wall.side.south"][0][0], D, quoins)
    for cid, (mat, O, R, length, t, bands) in walls.items():
        if cid in frames:
            continue
        breaks = (yf, *k03_brick.condition_breaks(yf)) if MATERIALS[mat].get("condition") else (yf,)
        frames[cid] = (a.wall(cid, mat, O, R, length, E, t, holes(cid), breaks, bands, gaps[cid]), mat)
    for op in p.openings:
        if p.stone:
            break
        (frame, t), mat = frames[op.wall]
        a.opening(op, frame, t, mat, "limestone_trim")
    # T-2291: a projecting stretcher course at the second-floor line on the south wall
    # and the rear, the south one run out past the quoin so the two meet; the north
    # wall is a blank party wall against the Glessner court and carries none
    sc_conf = p.worst_conf("storey_heights_m", "construction", "service_wall_brick")
    for cid, s_from, s_to in (("k01.wall.side.south", -k03_brick.STRING_PROUD, D),
                              ("k01.wall.rear_service", 0.0, W)):
        frame = frames[cid][0][0]
        for s0, s1 in _pieces(s_from, s_to, gaps[cid]):   # T-2308: stopped against a bay
            k03_brick.string_course(a, seed_of(structure_id, cid, 0), frame, s0, s1, floors[1], sc_conf)
    a.roof()
    # T-2308: the K08 bays, each on its wall. Its roof leans on that wall, so an opening
    # left above it must clear the roof — the K06 sill (0.10 m) and 0.05 m of flashing.
    # A downpipe on the bay's wall must stand clear of everything the bay reaches along
    # it (its eaves above all): T-2293's pipes run from the main gutter down to grade.
    reach = []
    for bay in p.bays:
        top, (s0, s1) = laid.get(bay["id"]) or a.bay(bay, frames[bay["wall"]][0][0])
        reach.append((bay["wall"], s0, s1, top))
        rp = p.rainwater["pipe_diameter_m"] / 2 if p.rainwater else 0.0
        for x in (p.rainwater or {}).get("downpipes", []):
            if x["wall"] == bay["wall"] and x["s_m"] + rp + 0.03 > s0 and x["s_m"] - rp - 0.03 < s1:
                raise ValueError(f"{bay['id']} reaches s {s0:.3f}..{s1:.3f} along {x['wall']}, into the "
                                 f"downpipe at s {x['s_m']}")
        for o in p.openings:
            if o.wall == bay["wall"] and bay["span_m"][0] < o.s_m < bay["span_m"][1] \
                    and o.sill_m - 0.15 < top:
                raise ValueError(f"{bay['id']}'s roof meets {o.wall} at {top:.3f} m, under the "
                                 f"opening at s {o.s_m} whose sill is {o.sill_m} m")
    # T-2317: the K10 wall head — brackets and a bed moulding under the soffit, every
    # corner turned and every head, pipe and bay stood clear of; cresting on the ridge
    k10_frontage.dress(a, reach)
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
            "baseColorFactor": [*spec["color"], spec.get("alpha", 1.0)], "metallicFactor": spec.get("metallic", 0.0),
            "roughnessFactor": spec["roughness"]}}
        if "alpha" in spec:
            mat["alphaMode"] = "BLEND"
        if tuple(spec["color"]) == (1.0, 1.0, 1.0):
            # glTF's default, which gltf-transform drops from the web derivative: write
            # it the same way here, so master and derivative name the same colours
            del mat["pbrMetallicRoughness"]["baseColorFactor"]
        fab = a.fabric[name]
        if fab:
            imgs = _images(fab)
            for role, src in imgs.items():
                if (fab, role) not in image_of:
                    images.append({"name": src.stem.removesuffix("_web"), "mimeType": "image/jpeg",
                                   "bufferView": view(src.read_bytes())})
                    textures.append({"sampler": 0, "source": len(images) - 1})
                    image_of[(fab, role)] = len(textures) - 1
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": image_of[(fab, "basecolor")], "texCoord": 0}
            if spec.get("normal") or ((_k04_fabric(fab) or _k02_fabric(fab)) is not None and "normal" in imgs):
                mat["normalTexture"] = {"index": image_of[(fab, "normal")], "texCoord": 0}
        materials.append(mat)
        ctype = 5123 if len(pr.pos) < 65536 else 5125
        primitives.append({
            "attributes": {
                "POSITION": accessor(pr.pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(pr.nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(pr.uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(pr.conf, 5126, "SCALAR", 1, 34962),
                **({"_TONE": accessor(pr.tone, 5126, "SCALAR", 1, 34962)} if pr.tone_of else {}),
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
