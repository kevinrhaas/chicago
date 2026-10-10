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
import struct
from pathlib import Path

from . import k03_brick
from . import k09_frontage

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "assets" / "textures" / "glessner-v4"
ROOFS = ROOT / "assets" / "textures" / "prairie_1904_roofs"   # K04, T-2292
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
    return out


def _k04_fabric(fab: str) -> dict | None:
    """A K04 fabric's material.json, or None for a fabric from another library."""
    f = ROOFS / fab / "material.json"
    return json.loads(f.read_text()) if f.exists() else None


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
    def opening(self, op, frame, thickness, body_mat, stone_trim, cut=False):
        """`cut`: the reveal is already a solid's (a recess the K05 union cut, T-2302, to
        K06's reveal depth), so K06 sets everything behind it, and its sill and lintel."""
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
        if k09_frontage.dress(self, op, frame, max(conf, p.conf("street_front_trim"))):
            return
        self.proud_box(stone_trim, frame, s0 - 0.12, s1 + 0.12, y1, y1 + 0.30, 0.03, seed, conf)

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
            fab = MATERIALS[mat].get("fabric")
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
            fab = spec.get("fabric")
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
    frames = {}
    for cid, (mat, O, R, length, t, bands) in walls.items():
        breaks = (yf, *k03_brick.condition_breaks(yf)) if MATERIALS[mat].get("condition") else (yf,)
        frames[cid] = (a.wall(cid, mat, O, R, length, E, t, holes(cid), breaks, bands, gaps[cid]), mat)
    for op in p.openings:
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
    for bay in p.bays:
        top, (s0, s1) = a.bay(bay, frames[bay["wall"]][0][0])
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
        spec = MATERIALS[name]
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
            if spec.get("normal") or (_k04_fabric(fab) is not None and "normal" in imgs):
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
