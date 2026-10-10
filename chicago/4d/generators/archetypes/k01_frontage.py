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
  k01.opening.door_leaf     reveal, threshold and a recessed oak leaf
  k01.stair.straight_stoop  whole risers from the walk to the principal floor
  k01.roof.hip              four planes on true hips, fascia and soffit
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

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "assets" / "textures" / "glessner-v4"
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
    "fascia": {"color": (0.27, 0.24, 0.20), "roughness": 0.7},
    "slate_covering": {"color": (0.20, 0.215, 0.24), "roughness": 0.78},
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
    return {m["name"]: tuple(m["tile_m"]) for m in lib} | k03_brick.TILES


def _images(fab: str) -> dict:
    """The JPEG(s) a fabric embeds: K03's from its own library, the rest Glessner's."""
    if fab in k03_brick.IMAGES:
        return k03_brick.IMAGES[fab]
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


class Assembly:
    def __init__(self, structure_id: str, params):
        self.sid = structure_id
        self.p = params
        self.tiles = _tiles()
        self.prims: dict[str, Prim] = {}
        self.components: dict[str, dict] = {}
        self.soffit_m = None   # set by build(); the soot band hangs from it

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

    def basis(self, mat, origin, au, av, seed, phase_u=None):
        fab = MATERIALS[mat].get("fabric")
        tu, tv = self.tiles[fab] if fab else (1.0, 1.0)
        if MATERIALS[mat].get("courses"):
            # a coursed fabric (T-2291): v = 0 on a bed joint at grade on every wall, so
            # courses run level round a corner; u is the wall's corner phase, or the
            # seed's whole-module step where no corner sets one
            if phase_u is None:
                phase_u = (seed % 4) / 4.0
            return (origin, au, av, tu, tv, phase_u, 0.0)
        # the seed moves the fabric, so two instances of one component differ
        return (origin, au, av, tu, tv, (seed & 0xFFFF) / 65536.0, (seed >> 16) / 65536.0)

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
    def opening(self, op, frame, thickness, body_mat, stone_trim):
        p = self.p
        O, R, N = frame
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        s0, s1 = op.s_m - op.width_m / 2, op.s_m + op.width_m / 2
        y0, y1 = op.sill_m, op.head_m
        conf = p.worst_conf("footprint", "sash_by_storey", "front_bays", "side_bays", "rear_bays")
        door = op.component == "k01.opening.door_leaf"
        if MATERIALS[body_mat].get("courses"):
            conf = max(conf, p.conf("service_wall_brick"))
        recess = 0.22 if door else self.kit_reveal(op)
        params = {"clear_width_m": op.width_m, "clear_height_m": op.height_m, "reveal_m": recess,
                  "wall": op.wall}
        if not door:
            params["k06_variant"] = p.window_kit[op.component]["variant"]
        seed = self.instance(op.component, "opening", params,
                             {"sill": P(op.s_m, y0, 0), "head": P(op.s_m, y1, 0),
                              "sash_plane": P(op.s_m, y0, -(recess if door else recess + 0.012))})
        if not door:
            # T-2298: a window is a K06 opening — reveal, sill, frame, sashes, glass,
            # blind, curtain and an enclosed room — built about this hole's sill socket
            self.glaze(op, frame, body_mat, stone_trim, seed, conf)
        else:
            # the reveal, in the wall's own body
            pr = self.prim(body_mat)
            bj = self.basis(body_mat, O, N, Y, seed)
            bh = self.basis(body_mat, O, R, N, seed)
            pr.face([P(s0, y0, 0), P(s0, y0, -recess), P(s0, y1, -recess), P(s0, y1, 0)], R, bj, conf)
            pr.face([P(s1, y0, 0), P(s1, y0, -recess), P(s1, y1, -recess), P(s1, y1, 0)], _mul(R, -1), bj, conf)
            pr.face([P(s0, y1, 0), P(s1, y1, 0), P(s1, y1, -recess), P(s0, y1, -recess)], _mul(Y, -1), bh, conf)
            self.prim("stoop_stone").face([P(s0, y0, 0), P(s1, y0, 0), P(s1, y0, -recess), P(s0, y0, -recess)],
                                          Y, self.basis("stoop_stone", O, R, N, seed), conf)
            self.prim("door_leaf").face([P(s0, y0, -recess), P(s1, y0, -recess), P(s1, y1, -recess),
                                         P(s0, y1, -recess)], N, self.basis("door_leaf", O, R, Y, seed), conf)
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
        # a flat lintel over every opening
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

    def glaze(self, op, frame, body_mat, stone_trim, seed, conf):
        from . import k06_windows
        O, R, N = frame
        o = k06_windows.Opening(self.kit_variant(op), self._kit)
        o.seed = seed                      # the blind's drop follows this instance, not the kit's
        o.build()
        # K06's frame: +X along the wall, +Y up, +Z out of it, the origin at the sill socket
        base = _add(O, _add(_mul(R, op.s_m), _mul(Y, op.sill_m)))
        W = lambda q: _add(base, _add(_add(_mul(R, q[0]), _mul(Y, q[1])), _mul(N, q[2])))
        for role, src in o.prims.items():
            if role == "head":
                continue
            if role not in self.K06_ROLES:
                raise ValueError(f"K06 role {role!r} has no material on a K01 frontage")
            mat = self.K06_ROLES[role] or body_mat
            mat = stone_trim if mat == "stone" else mat
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
    def bay(self, b, frame) -> float:
        """Lay one K08 bay on its host wall; return where its roof meets the wall.

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
        return max(q[1] for q in roof.pos if abs(q[2]) < 1e-6) if roof else built.meta["eave_m"]

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
        conf = p.worst_conf("footprint", "roof_form", "roof_pitch_deg", "eave_overhang_m")
        seed = self.instance("k01.roof.hip", "roof",
                             {"pitch_deg": p.roof_pitch_deg, "eave_overhang_m": o,
                              "eave_datum_m": E, "ridge_datum_m": yr},
                             {"eave": (0.0, E, 0.0), "ridge": (W / 2, yr, -W / 2)})
        SWe, SEe, NEe, NWe = (-o, ye, o), (D + o, ye, o), (D + o, ye, -W - o), (-o, ye, -W - o)
        RW, RE = (W / 2, yr, -W / 2), (D - W / 2, yr, -W / 2)
        pr = self.prim("slate_covering")
        for pts, contour in (([SWe, SEe, RE, RW], (1.0, 0.0, 0.0)), ([NEe, NWe, RW, RE], (-1.0, 0.0, 0.0)),
                             ([SEe, NEe, RE], (0.0, 0.0, -1.0)), ([NWe, SWe, RW], (0.0, 0.0, 1.0))):
            nrm = _unit(_cross(_sub(pts[1], pts[0]), _sub(pts[-1], pts[0])))
            uphill = _unit(_cross(nrm, contour))
            pr.face(pts, nrm, self.basis("slate_covering", pts[0], contour, uphill, seed), conf)
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
        return yf


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
    """The assembly: walls with their openings cut, the stoop, the roof."""
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
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf")
    a.stoop(frames["k01.wall.street_front"][0][0], door.s_m)
    a.roof()
    # T-2308: the K08 bays, each on its wall. Its roof leans on that wall, so an opening
    # left above it must clear the roof — the K06 sill (0.10 m) and 0.05 m of flashing.
    for bay in p.bays:
        top = a.bay(bay, frames[bay["wall"]][0][0])
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
        fab = spec.get("fabric")
        if fab:
            for role, src in _images(fab).items():
                if (fab, role) not in image_of:
                    images.append({"name": src.stem.removesuffix("_web"), "mimeType": "image/jpeg",
                                   "bufferView": view(src.read_bytes())})
                    textures.append({"sampler": 0, "source": len(images) - 1})
                    image_of[(fab, role)] = len(textures) - 1
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": image_of[(fab, "basecolor")], "texCoord": 0}
            if spec.get("normal"):
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
