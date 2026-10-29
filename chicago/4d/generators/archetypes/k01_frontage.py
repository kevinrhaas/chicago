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

  k01.wall.street_front     the stone front, its openings cut through it; or, for a
                            record with no `stone_front` (T-2341), a front of the
                            side walls' K03 brick whose openings keep their stone
                            sills, K09 heads or flat lintels, under stone belts
  k01.wall.side.north       the party side against the Glessner court: blank brick; or, on a
                            record naming `north_bays` (T-2342), a corner house's street
                            side, windowed like the south wall
  k01.wall.side.south       common brick, four bays a storey
  k01.wall.rear_service     common brick, two bays a storey; on an all-stone house
                            (T-2788, `construction: "stone"`) the flanks, the rear and
                            every masonry wing are the front's K02 coursing, on its beds
  k01.wall.round_corner     a corner of the front block rounded from grade (T-3006,
                            `round_corner`): the front's stone, coursed on its beds and
                            curved stone by stone, corbelled out to the square in its last
                            course under the cornice, the eave and the gable end
  k01.wall.cant             a corner of the main body cut on a canted face (T-3186,
                            `cant_corner`): the front's stone on its beds, its own window
                            column and basement light, the front and the side wall stopped
                            at it, and the cornice, the mansard's rings, the gutter and the
                            curb's cresting turned round it on two mitres
  k01.wall.round_arcade     the porch's arcade round that corner (T-2991, the loggia's
                            `round_arcade`): round-headed lights cut through the round's
                            courses into the porch's shadow, each over a colonnette
                            standing as the mouth's columns stand, on a plinth band
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
  k01.opening.gable_light   a WALL GABLE's light (T-2428, `k01_wall_gable`): the dormer's
                            face on the wall's plane, K06 lights cut to their own heads
  k01.opening.segmental_arch  the radiating voussoirs over a wall gable's light
  k01.opening.gable_arch    a wall gable's GREAT ARCH (T-2917): its ring of voussoirs on
                            the cornice, the tympanum recessed under it and its round-
                            headed lights cut through that
  k01.wall.gable_colonnette a colonnette between or beside the lights under the great arch
  k01.roof.gable_pinnacle   a wall gable's pinnacle: square shaft, cap and pyramid
  k01.roof.gable_finial     a wall gable's turned finial on the ridge at its apex
  k01.opening.sash_round    a mansard crown's round-headed dormer sash (T-2404): K06's
                            round-arched variant in the recess the roof's union cut
  k01.opening.sash_round_hooded
                            a brick street front's round-headed window (T-2410): K06's
                            round sash in a round hole the wall cuts (a rectangle to the
                            spring, strips from the head's curve over it), under the kit's
                            arch band as its hood, with a key block on the crown; or
                            (T-2960) cut segmental on its K06 sash's rise, under K09's
                            cornice hood on two consoles in place of band and key
  k01.opening.sash_round_plain
                            a side wall's round-headed light whose picture shows its head
                            plain (T-2884, 1625's lower lights): the same round hole and
                            K06 sash, under no hood and no brick arch
  k08.*                     a K08 bay (T-2308): `generators/archetypes/k08_bays.py`
                            builds it in its own wall frame and `bay` lays it on
                            its host wall, which carries no opening behind it; a
                            projection may stand flush with a corner and carry a
                            mansard `crown` over it (T-2404)

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
                            against the front's own corner stone (T-2581: or a straight
                            strip, stone_front.south_return_m, on every course)
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

import dataclasses
import hashlib
import itertools
import json
import math
import random
import struct
from pathlib import Path

from . import k01_arched_front
from . import k03_brick
from . import k09_frontage
from . import k10_frontage
from . import k11_frontage
from . import k14_yard
from . import k01_frontage_params
from .k01_frontage_params import EAVE_FASCIA_M, ROUND_CUT, ROUND_HOODED, STREET_WINDOW, STRIP_FABRICS, wing_walls

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "assets" / "textures" / "glessner-v4"
ROOFS = ROOT / "assets" / "textures" / "prairie_1904_roofs"   # K04, T-2292
STONE = ROOT / "assets" / "textures" / "prairie_1904_stone"   # K02, T-2288
GENERATOR = "chicago-4d generators/archetypes/k01_frontage.py (K01, T-2266)"
# T-2358: where a gutter outlet's trail starts, and how far a vertex may lie off a wall's
# plane and still weather as that wall. Reconstructed (L-k14-1808-walls-2358): the swan neck
# meets the wall just under the soffit and wets it either side of the pipe; a K08 bay stands
# up to a metre proud and a reveal goes the wall's thickness in.
K14_OUTLET_BELOW_SOFFIT_M = 0.15
K14_OUTLET_MARGIN_M = 0.03
K14_REACH_OUT_M, K14_REACH_IN_M = 1.2, 1.0
# T-2364: a brick house's stone dressings (its K06 sills, K09 heads and belts, a brick K08
# bay's plinth, bands, sills and heads) weather as the kit's dressed trim, as a stone front's
# trim does: the same cut limestone, whatever wall it sits in
K14_BRICK_HOUSE_TRIM = "dressed_trim"
# T-2359: a K15 stack's plume (k14_condition.json `chimney_soot`) is laid on the covering's
# vertices, so the roof shell is cut with plan rows across the plume's reach: this many to its
# length, each way, which puts a vertex every 0.23 m of 1808's 1.35 m plume. The plume is a
# cone fading linearly to its tip and to its sides, so a vertex grid that fine carries it.
K14_PLUME_ROWS = 6
# a vertex within this of a row is ON it, so no row leaves a sliver the 2 mm weld collapses
K14_ROW_SNAP_M = 0.005

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
    # T-3236: a record's own leaves in their own finish (entrance_kit leaf.color), the joinery's
    # colour until one names it
    "door_leaf_varnish": {"color": (0.29, 0.17, 0.085), "roughness": 0.55},
    # T-2304: K07's hardware (k07_entrances.json parts.hardware): the knob on its rose
    "door_iron": {"color": (0.17, 0.16, 0.15), "roughness": 0.45},
    # T-2310: the K09 kit's carving (capital leaves) apart from its dressed trim
    "carved_trim": {"fabric": "limestone", "color": (0.97, 0.94, 0.87), "roughness": 0.88},
    "fascia": {"color": (0.27, 0.24, 0.20), "roughness": 0.7},
    # T-2293: the K04 roof. The covering's fabric is the record's (roof_covering), so
    # this entry's is only a default; flashing and rainwater are named by fabric.
    "slate_covering": {"fabric": "slate_pennsylvania", "color": (1.0, 1.0, 1.0), "roughness": 0.62},
    # T-2406: a mansard's lower faces when they are slated over a metal upper hip (1620)
    "mansard_slate": {"fabric": "slate_pennsylvania", "color": (1.0, 1.0, 1.0), "roughness": 0.62},
    # T-2841: a rear wing's hipped or gabled roof, in its own K04 slate (rear_wings[].roof).
    # T-2843: a shade rougher than the main roof's, as dormer_stone is off the trim: where
    # a wing is slated in the main roof's own slate (1801's, under its mansard faces) the two
    # were one material in all but name, and the publish path's dedup merged the name away
    "wing_slate": {"fabric": "slate_pennsylvania", "color": (1.0, 1.0, 1.0), "roughness": 0.64},
    # the dormer face: dressed stone a shade off the trim, and a name outside the
    # envelope materials, since the envelope is the walls and not what stands on the roof
    "dormer_stone": {"fabric": "limestone", "color": (0.96, 0.93, 0.86), "roughness": 0.8},
    "k04_copper_sheet": {"fabric": "copper_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.48, "metallic": 0.3},
    "k04_lead_sheet": {"fabric": "lead_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.7, "metallic": 0.2},
    "k04_zinc_sheet": {"fabric": "zinc_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.6, "metallic": 0.3},
    "k04_painted_tin_sheet": {"fabric": "painted_tin_sheet", "color": (1.0, 1.0, 1.0), "roughness": 0.6},
    "iron": {"color": (0.055, 0.055, 0.06), "roughness": 0.55},
    # T-2578: a roof ventilator's galvanized sheet, pale as the 1887-89 prints show it beside
    # the granite; a plain colour, so a pipe costs no texture (the colour is reconstructed)
    "vent_galvanized": {"color": (0.60, 0.61, 0.60), "roughness": 0.5},
    # T-2406: a yard's close-boarded fence, weathered timber (k11_frontage `side_fence`)
    "fence_boards": {"color": (0.40, 0.36, 0.30), "roughness": 0.92},
    # T-2366: what stands proud of a stone front (keystones, pilasters, a hood, a portico):
    # the dressed stone, under a name outside the envelope materials, since the contract's
    # envelope is the wall and a portico stands metres before it (the stoop's reasoning)
    "dress_stone": {"fabric": "limestone", "color": (0.98, 0.95, 0.88), "roughness": 0.86},
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
    # T-2904: an oriel's apron, in the bay's stone unless its record lays it in the front's
    # (Assembly): a shade rougher than the bay's, the web derivative's reason above
    "bay_apron": dict(MATERIALS["rough_stone_trim"], roughness=0.91),
    "bay_brick": dict(k03_brick.MATERIALS["brick"], roughness=round(k03_brick.MATERIALS["brick"]["roughness"] + 0.02, 2)),
    "bay_copper": {"color": (0.37, 0.52, 0.45), "roughness": 0.45, "metallic": 0.35},
    "bay_tin": {"color": (0.30, 0.22, 0.18), "roughness": 0.7},
    # T-2408: a bay's slated hood, the K08 kit's own slate colour (k08_bays.json `roofs`)
    "bay_slate": {"color": (0.16, 0.17, 0.19), "roughness": 0.75},
    # T-2356: a frame bay's body is painted timber — the library's painted joinery, the
    # sash's dark green paint on boards — over a brick plinth, its bands, sills and heads
    # the fascia's painted trim. No lap is modelled: a bay of the period was boarded and
    # panelled, and its boards are the texture's, not geometry (liberty L-k01-1626-*).
    "bay_frame": {"fabric": "painted_wood", "color": (1.0, 1.0, 1.0), "roughness": 0.78},
    # T-2451: a frame bay's pilaster strips, painted light against its dark boards, as both of
    # 1620's pictures draw them; the colour is the reconstruction's (the pictures are monochrome)
    "bay_strip_paint": {"color": (0.74, 0.70, 0.60), "roughness": 0.74},
})
# T-2313: a K15 stack's soot band (k15_chimneys.json `soot`): the K03 brick darkened, so
# its courses and texture run on through the band; and the clay pot, should a source show one
MATERIALS["chimney_soot"] = dict(k03_brick.MATERIALS["brick"], color=(0.48, 0.40, 0.37))
MATERIALS["chimney_pot"] = {"color": (0.66, 0.36, 0.22), "roughness": 0.8}
# T-3093: a street front's brick toned apart from the side walls' (`street_front_brick`); its
# name begins "brick" because it is the envelope's wall, and its colour is the record's tone
MATERIALS["brick_front"] = dict(k03_brick.MATERIALS["brick"])
# T-2319: the K11 boundary wall's brick. Its own slot for the bays' reason: "brick" is an
# envelope material, and the contract reads grade off its lowest vertex, so a boundary wall
# sunk 0.10 m in it would move the house's origin and stretch its envelope to the street.
MATERIALS["k11_wall_brick"] = dict(k03_brick.MATERIALS["brick"],
                                   roughness=round(k03_brick.MATERIALS["brick"]["roughness"] + 0.04, 2))
# T-2903: an area's walls under grade (k01_rear_section.area), K03 brick under a name outside
# the wall-base materials, for the boundary wall's reason: the brick's lowest vertex is grade
MATERIALS["area_brick"] = dict(k03_brick.MATERIALS["brick"],
                               roughness=round(k03_brick.MATERIALS["brick"]["roughness"] + 0.06, 2))
# T-2360: the K14 yard's ground (k14_yard.py). Glessner's own turf and gravel maps, the
# cinder darker than its drive; the bare earth a flat colour, the K14 study's (104, 90, 70)
# in linear. The front walk's flags are the stoop's stone and take no slot of their own.
MATERIALS["yard_turf"] = {"fabric": "turf", "color": (1.0, 1.0, 1.0), "roughness": 0.96}
MATERIALS["yard_earth"] = {"color": (0.139, 0.102, 0.061), "roughness": 1.0}
MATERIALS["yard_cinder"] = {"fabric": "gravel", "color": (0.52, 0.50, 0.47), "roughness": 0.93}
# T-2369: the white-painted panel behind a frieze light that reads white in its photograph
MATERIALS["frieze_panel"] = {"color": (0.74, 0.73, 0.70), "roughness": 0.6}
# T-2887: louvred shutters at a window over a bay (1637's), read dark in a monochrome
# photograph: a deep painted green, the colour reconstructed (L-k01-1637-bay-dress-2887)
MATERIALS["shutter"] = {"color": (0.045, 0.08, 0.05), "roughness": 0.7}
# K08 role -> slot; `body` is the bay's fabric (bay_stone, bay_brick or bay_frame), `cover`
# its roof's K04 covering. A came is a leaded light's, which no K01 bay glazes.
#: T-2964: a mansard bay's cresting stops this far short of each corner of its curb
CREST_STOP_M = 0.2
K08_ROLES = {"wall": "body", "masonry_relief": "body", "reveal": "body", "mullion": "body", "roof_back": "body",
             "plinth": "bay_stone", "band": "bay_stone", "corbel": "bay_stone", "apron": "bay_apron",
             "sill": "bay_stone", "head": "bay_stone", "soffit": "fascia", "fascia": "fascia",
             "frame": "sash", "sash_outer": "sash", "sash_inner": "sash",
             "glass_outer": "glass", "glass_inner": "glass", "blind": "blind",
             "curtain": "curtain", "backing": "backing", "roof": "cover", "finial": "cover",
             "bracket": "fascia",   # T-2408: a hood's consoles and modillions, the eaves' joinery
             "carving": "carved_trim",   # T-2931: a pilaster's carved lozenges
             "iron": "iron",        # T-2525: a bow's balcony rail and a light's grille
             "shutter": "shutter",   # T-1879: a bay light's louvred shutters
             "cheek": "mansard_slate"}  # T-3197: a storey's slated cheeks, the mansard's slate (1827's attic)
SLIVER_M = 0.0025   # T-2308: a bay triangle with an edge shorter than this is a sliver


def _shield_outline():
    """T-3093: a carved shield's outline in a unit box, anticlockwise from its right shoulder
    as the oval's ellipse runs: square shoulders at 0.2 under a level head, and two arcs
    (centred 0.22 across the axis, radius 1.22) drawn in to a point at the foot. Convex, so
    the boss's field is one fan."""
    pts = [(1.0, 0.2), (1.0, 0.6), (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (-0.5, 1.0), (-1.0, 1.0), (-1.0, 0.6),
           (-1.0, 0.2)]
    c, r = 0.22, 1.22
    end = math.acos(c / r)                     # where an arc meets the axis, under the centre's side
    for k in range(1, 7):                      # the left arc, its centre right of the axis
        t = math.pi + end * k / 6
        pts.append((c + r * math.cos(t), 0.2 + r * math.sin(t)))
    for k in range(5, 0, -1):                  # and the right, back up to the shoulder
        t = -end * k / 6
        pts.append((-c + r * math.cos(t), 0.2 + r * math.sin(t)))
    return tuple((round(x, 6), round(y, 6)) for x, y in pts)


SHIELD_OUTLINE = _shield_outline()


def entrance_cut(p):
    """T-3135: the projection the porch arch is cut into (`cut_by_entrance`), or None: the
    bay, the arched door group, which side of the mouth the bay stands (`left`: its jamb
    inside the bay, the bay to the south), and how far the bay stands proud."""
    bays = [b for b in p.bays if b.get("cut_by_entrance")]
    if not bays:
        return None
    b, = bays
    g = next(g for g in (p.arched_front or {}).get("groups", ()) if g["component"] == "k01.opening.door_leaf")
    (s0, s1, _sp, _r, _f), = g["lights"]
    side = "left" if b["span_m"][0] < s0 < b["span_m"][1] else "right"
    return {"bay": b, "group": g, "side": side, "corner_s_m": b["span_m"][1] if side == "left" else b["span_m"][0],
            "proud_m": max(float(q[1]) for q in b["variant"]["plan"]["points"])}


def _cut_convex(src, hs, eps=1e-7):
    """T-3135: `src`'s triangles less the convex region where dot(n, p) <= c for every (n, c)
    in `hs`: each triangle split into the convex pieces outside one plane after another (the
    rest inside them all is gone), its normal kept and its UVs carried linearly."""
    out = Prim(src.name)
    out.tone_of = src.tone_of
    has_conf, has_tone = len(src.conf) == len(src.pos), len(src.tone) == len(src.pos)

    def clip(poly, n, c, keep_in):
        # a vertex within eps of the plane is inside it, for both halves alike, so a face
        # lying on the plane goes on with the rest and is never emitted twice
        res = []
        for i, a in enumerate(poly):
            b_ = poly[(i + 1) % len(poly)]
            da, db = _dot(n, a[0]) - c, _dot(n, b_[0]) - c
            oa, ob = da > eps, db > eps
            if oa != keep_in:
                res.append(a)
            if oa != ob and abs(da - db) > 1e-12:
                t = da / (da - db)
                res.append((tuple(a[0][j] + (b_[0][j] - a[0][j]) * t for j in range(3)),
                            tuple(a[1][j] + (b_[1][j] - a[1][j]) * t for j in range(2)),
                            a[2] + (b_[2] - a[2]) * t, a[3] + (b_[3] - a[3]) * t))
        return res

    def emit(poly, nrm, conf):
        base = len(out.pos)
        for q, uv, cf, tn in poly:
            out.pos.append(q)
            out.nrm.append(nrm)
            out.uv.append(uv)
            if has_conf:
                out.conf.append(conf)
            if has_tone:
                out.tone.append(tn)
        for i in range(1, len(poly) - 1):
            out.idx += [base, base + i, base + i + 1]

    for t in range(0, len(src.idx), 3):
        ids = src.idx[t:t + 3]
        poly = [(tuple(src.pos[i]), tuple(src.uv[i]), 0.0, src.tone[i] if has_tone else 1.0) for i in ids]
        nrm, conf = src.nrm[ids[0]], (src.conf[ids[0]] if has_conf else None)
        if not any(_dot(n, q[0]) - c > eps for n, c in hs for q in poly):
            continue   # wholly inside the cut
        rest = poly
        for n, c in hs:
            if len(rest) < 3:
                break
            piece = clip(rest, n, c, keep_in=False)
            if len(piece) >= 3:
                emit(piece, nrm, conf)
            rest = clip(rest, n, c, keep_in=True)
    return out
#: T-2914: the cells a coursed front dresses in stone by intent, kept stone over a brick line
DRESSED_CELLS = ("K01.surround", "K01.quoin", "K01.panel")
# T-2356: a frame bay has no stone in it. Its dressings are painted timber (the fascia's
# slot) and its plinth the house's brick carried out under it, as a timber bay on a
# masonry basement stands.
K08_FRAME_ROLES = {"plinth": "bay_brick", "band": "fascia", "corbel": "fascia",
                   "sill": "fascia", "head": "fascia"}
K08_COVERS = {"copper_standing_seam": "bay_copper", "copper_sheet": "bay_copper",
              "tin_flat_seam_painted": "bay_tin", "slate_pennsylvania": "bay_slate"}


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


#: T-2476: the linear colour of each K04 tin paint other than the red oxide its maps are
#: drawn in — weathered black and dark green paint on terne, as a dark roof reads
TIN_PAINT = {"black": (0.030, 0.030, 0.026), "dark_green": (0.022, 0.040, 0.026)}



def k01_mansard_straight_on(st, cid, s, depth):
    """T-2995: which points along wall `cid` (at `s` along it) stand under a straight wall head."""
    import numpy as np
    s = np.asarray(s, dtype=np.float64)
    if cid == "k01.wall.rear_service":
        return np.ones(len(s), dtype=bool)
    if cid == "k01.wall.side.north":   # its s runs from the front
        return s >= depth - st["north_u_m"] - 1e-6
    if cid == "k01.wall.side.south":   # its s runs from the rear
        return s <= st["south_u_m"] + 1e-6
    return np.zeros(len(s), dtype=bool)

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
            if params.roof.get("lower_covering"):
                self.fabric["mansard_slate"] = params.roof["lower_covering"]
        for w in params.rear_wings:   # T-2841: one slate for every pitched wing (k01_frontage_params)
            if w["roof"]["kind"] != "flat":
                self.fabric["wing_slate"] = w["roof"]["covering"]
        self.soffit_m = None   # set by build(); the soot band hangs from it
        # T-2358: a record that names the K14 condition kit weathers to its own age in 1904
        # instead of wearing K03's fixed full-age mask; its walls are registered by build()
        self.k14, self.k14_walls = None, {}
        # T-2364: the sills a brick house's trails hang from, read before its walls are cut
        self.k14_sills = None
        if params.condition:
            from . import k14_condition
            self.k14 = k14_condition.Condition()
            self.k14_seed = k14_condition.property_seed(structure_id)
            self.k14_built = params.condition["built"]
        self.trim_triangles: dict[str, int] = {}   # T-2310: K09 trim, per kit id
        # T-2289: a coursed stone front lays its walling and its trim in K02 fabrics,
        # whose maps carry their own colour, so the factors go to white
        self.spec = {k: dict(v) for k, v in MATERIALS.items()}
        # T-2369: a record that reads its cornice's paint off a source (1612's dark cornice)
        # paints the eave's timber — fascia, soffit, brackets, bed moulding, frieze — in it
        paint = (params.wall_head or {}).get("paint")
        if paint:
            self.spec["fascia"]["color"] = tuple(float(x) for x in paint["color"])
        # T-2476: a tin covering painted other than its map (K04's paint_alternatives): the
        # map's own mean is taken to the paint's colour, so its seams and wear still read
        if params.roof and params.roof.get("paint"):
            meta = json.loads((_images(self.fabric["slate_covering"])["basecolor"].parent / "material.json").read_text())
            mean = [((c / 255 + 0.055) / 1.055) ** 2.4 for c in meta["mean_basecolor"]]
            self.spec["slate_covering"]["color"] = tuple(
                round(min(1.0, t / m), 4) for t, m in zip(TIN_PAINT[params.roof["paint"]], mean))
        # T-2476: a painted brick house (1620) wears its paint over every brick slot it lays —
        # walls, the pavilion's brick, the stacks and K03's units, the soot left dark — the map still under it
        if params.wall_paint:
            for slot in ("brick", "bay_brick", *(k for k in MATERIALS if k.startswith("brick_unit_"))):
                self.spec[slot]["color"] = tuple(round(c * f, 4) for c, f in zip(self.spec[slot]["color"], params.wall_paint))
                # T-2933: an opaque paint is the slot's colour itself, with no brick map under it;
                # a K03 unit keeps its tint's ratio to the units' mean over it, so the four stay
                # four materials (the web derivative merges identical ones and loses their names)
                if params.wall_paint_opaque:
                    tint = MATERIALS[slot]["color"]
                    if slot.startswith("brick_unit_"):
                        units = [MATERIALS[k]["color"] for k in MATERIALS if k.startswith("brick_unit_")]
                        tint = tuple(t / (math.fsum(u[i] for u in units) / len(units)) for i, t in enumerate(tint))
                    else:
                        tint = (1.0, 1.0, 1.0)
                    self.spec[slot]["color"] = tuple(round(min(1.0, f * t), 4)
                                                     for f, t in zip(params.wall_paint, tint))
                    self.fabric[slot] = None
        # T-3236: the door's leaves in their own finish (1812's dark varnish, as both photographs
        # show them), their frame and the fanlight's bars keeping the joinery's own
        lc = ((params.entrance_kit or {}).get("leaf") or {}).get("color")
        if lc:
            self.spec["door_leaf_varnish"]["color"] = tuple(float(x) for x in lc)
        # T-3093: the front's brick toned (1812's), its brick bays with it
        self.front_brick = "brick_front" if params.front_brick_tone else "brick"
        if params.front_brick_tone:
            for slot in ("brick_front", "bay_brick"):
                self.spec[slot]["color"] = tuple(round(c * f, 4) for c, f in
                                                 zip(self.spec[slot]["color"], params.front_brick_tone))
        if params.stone:
            st = params.stone
            for slot, fab, rough in (("rough_stone_trim", st["fabric"], st["fabric_roughness"]),
                                     ("limestone_trim", st["trim"], st["trim_roughness"]),
                                     # T-2366: the dressings proud of the front, the trim's stone
                                     ("dress_stone", st["trim"], round(st["trim_roughness"] + 0.02, 3))):
                self.fabric[slot] = fab
                self.spec[slot] |= {"color": (1.0, 1.0, 1.0), "roughness": rough}
            # T-2350: a bay laid in the front's own stone (`front_stone`) wears its K02 fabric
            # too, a shade rougher so the web derivative keeps the bay's slot its own
            # T-2788: and on an all-stone house every stone bay and a timber bay's plinth
            if st.get("all_round") or any(b["fabric"] == "front_stone" for b in params.bays):
                self.fabric["bay_stone"] = st["fabric"]
                self.spec["bay_stone"] |= {"color": (1.0, 1.0, 1.0), "roughness": round(st["fabric_roughness"] + 0.02, 3)}
        # T-2917: a wall gable the record lays in the front's stone (1811's, smooth ashlar on
        # the plate) wears the front's K02 fabric, a shade rougher than the walling's own slot
        if params.dormer and params.dormer.get("wall_gable", {}).get("face_fabric") == "front_stone":
            if not params.stone:
                raise ValueError("a wall gable in the front's stone needs a stone front")
            self.fabric["dormer_stone"] = params.stone["fabric"]
            self.spec["dormer_stone"] = dict(self.spec["dormer_stone"], fabric=params.stone["fabric"], color=(1.0, 1.0, 1.0),
                                             roughness=round(params.stone["fabric_roughness"] + 0.01, 3))
        # T-2289: what each kit seats on a wall, as (s0, s1, y0, y1, kind) in that wall's
        # frame, keyed by the frame's origin: the coursed front dresses the stone under it
        if params.stone_finish:
            self.spec["sash"]["color"] = (.11,.09,.065)
            for slot in ("stoop_stone", "bay_stone", "carved_trim"):
                fab = params.stone["fabric"] if slot == "bay_stone" else params.stone["trim"]
                self.fabric[slot] = fab
                self.spec[slot] = dict(self.spec[slot], fabric=fab, color=(1.0,1.0,1.0))
        # T-2904: an apron the record lays in the front's stone (1625's print reads it darker
        # than the oriel's dressed walls and stippled, as the rock-faced front is) wears the
        # front's K02 walling, a shade rougher; any other wears the bay's own stone, as it did
        # when the apron was the corbel's role
        if any(b.get("apron_fabric") == "front_stone" for b in params.bays):
            self.fabric["bay_apron"] = params.stone["fabric"]
            self.spec["bay_apron"] = dict(self.spec["bay_apron"], fabric=params.stone["fabric"], color=(1.0, 1.0, 1.0),
                                          roughness=round(params.stone["fabric_roughness"] + 0.03, 3))
        else:
            self.fabric["bay_apron"] = self.fabric["bay_stone"]
            self.spec["bay_apron"] = dict(self.spec["bay_stone"], roughness=round(self.spec["bay_stone"]["roughness"] + 0.01, 3))
        self.footprints: dict[tuple, list] = {}
        self.bay_holes: dict[str, list] = {}   # T-3047: a shallow bay's recesses, by host wall

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
            if self.k14 is not None and self.k14_fabric(name):
                tone = lambda y: 1.0   # T-2358: evaluated over every vertex by condition_tones
            elif MATERIALS[name].get("condition"):
                tone = lambda y: k03_brick.tone(y, self.soffit_m)
            self.prims[name] = Prim(name, tone)
        return self.prims[name]

    # -- T-2358: the K14 condition kit --------------------------------------------------
    def k14_fabric(self, name):
        """The K02/K03 fabric id a slot weathers as, or None for a slot the kit leaves alone:
        every K03 brick slot, and the K02 walling and trim of a stone front and its bays."""
        st = self.p.stone
        if MATERIALS[name].get("condition"):
            return k03_brick.FABRIC
        if st and name in ("rough_stone_trim", "bay_stone", "bay_apron"):
            return st["fabric"]
        if st and name == "limestone_trim":
            return st["trim"]
        if name in ("limestone_trim", "bay_stone", "bay_apron"):   # T-2364: a brick house's stone dressings
            return K14_BRICK_HOUSE_TRIM
        return None

    def k14_sources(self, cid):
        """A wall's water-trail sources, in its own frame: every K06 sill seated on it (its
        proud extent, horns and all, the trail hanging from its underside) and every gutter
        outlet whose downpipe runs down it, the trail from just under the soffit where the
        swan neck meets the wall. Sills first along the wall, then outlets: the order is the
        trail's index, and so its draw from the property's seed."""
        O = self.k14_walls[cid][0]
        seated = self.footprints if self.k14_sills is None else self.k14_sills
        sills = sorted((s0, s1, y0) for s0, s1, y0, _, kind in seated.get(tuple(O), [])
                       if kind == "K06.sill")
        out = [{"kind": "sill", "x0": round(s0, 4), "x1": round(s1, 4), "y": round(y0, 4)}
               for s0, s1, y0 in sills]
        r = self.p.rainwater
        if r:
            half = r["pipe_diameter_m"] / 2 + K14_OUTLET_MARGIN_M
            out += [{"kind": "outlet", "x0": round(x["s_m"] - half, 4), "x1": round(x["s_m"] + half, 4),
                     "y": round(self.soffit_m - K14_OUTLET_BELOW_SOFFIT_M, 4)}
                    for x in sorted(r["downpipes"], key=lambda x: x["s_m"]) if x["wall"] == cid]
        return out

    def k14_breaks(self, cid):
        """The rows and columns a wall needs so `_TONE` can carry the kit's layers: the
        kit's own rows (damp top, soot band, each trail's head and foot) and, for each
        trail, its two edges, their soft fall-off and its centre line."""
        L = self.k14_walls[cid][3]
        src = self.k14_sources(cid)
        rows = self.k14.wall_breaks(self.soffit_m, built=self.k14_built, sources=tuple(src), seed=self.k14_seed)
        soft = self.k14.layers["water_trails"]["edge_soft_m"]
        cols = {round(min(max(x, 0.0), L), 4) for t in src
                for x in (t["x0"] - soft, t["x0"], (t["x0"] + t["x1"]) / 2, t["x1"], t["x1"] + soft)}
        return tuple(rows), tuple(sorted(cols))

    def condition_tones(self):
        """Every weathering slot's `_TONE`, once everything is laid: each vertex is read in
        the frame of the wall whose plane it is nearest (on the face, in a reveal, or on a
        kit piece standing proud of it), so its trails and its damp line's wobble are that
        wall's; a vertex off every wall (a boundary wall, a stack over the roof) takes the
        height layers alone."""
        if self.k14 is None:
            return
        import numpy as np
        walls = list(self.k14_walls.items())
        srcs = [tuple(self.k14_sources(cid)) for cid, _ in walls]
        for name in sorted(self.prims):
            pr, fab = self.prims[name], self.k14_fabric(name)
            if fab is None or not pr.pos:
                continue
            P = np.asarray(pr.pos, dtype=np.float64)
            best = np.full(len(P), np.inf)
            on = np.full(len(P), -1)
            xs = np.zeros(len(P))
            for i, (_, (O, R, N, L)) in enumerate(walls):
                v = P - np.asarray(O)
                sv, dv = v @ np.asarray(R), v @ np.asarray(N)
                ok = (sv >= -0.02) & (sv <= L + 0.02) & (dv >= -K14_REACH_IN_M) & (dv <= K14_REACH_OUT_M) \
                    & (np.abs(dv) < best)
                best[ok], on[ok], xs[ok] = np.abs(dv[ok]), i, sv[ok]
            tone = np.ones(len(P))
            st = (self.p.mansard or {}).get("straight")
            for i in range(-1, len(walls)):
                m = on == i
                if m.any():
                    # T-2995: a straight wall has no eave over it; its soot hangs from its parapet's top
                    head = self.soffit_m if not st or i < 0 else np.where(
                        k01_mansard_straight_on(st, walls[i][0], xs[m], self.p.depth_m),
                        self.p.mansard["curb_m"] + st["upstand_m"], self.soffit_m)
                    tone[m] = self.k14.wall_tone(P[m, 1], head, built=self.k14_built, fabric=fab,
                                                 seed=self.k14_seed, x=xs[m] if i >= 0 else 0.0,
                                                 sources=srcs[i] if i >= 0 else ())
            pr.tone = [round(float(t), 4) for t in tone]
        # T-2359: the chimney plume on the slate, leeward of each K15 stack
        pr, plumes = self.prims.get("slate_covering"), self.k14_plumes()
        if pr is not None and pr.pos and plumes:
            P = np.asarray(pr.pos, dtype=np.float64)
            rot = math.radians(self.p.condition["rotation_deg"])
            tone = np.ones(len(P))
            for x0, z0, _ in plumes:
                dxl, dnl = P[:, 0] - x0, z0 - P[:, 2]   # east and north in the house's frame
                tone = tone * self.k14.roof_tone(dxl * math.cos(rot) + dnl * math.sin(rot),
                                                 dnl * math.cos(rot) - dxl * math.sin(rot),
                                                 built=self.k14_built)
            pr.tone = [round(float(t), 4) for t in np.maximum(tone, self.k14.floor)]

    def k14_plumes(self):
        """T-2359: each K15 stack's plume as (x, z, length) in this frame: the stack's centre
        and how far its plume reaches at the house's age. Empty for a record that names no
        condition kit or no K15 stack."""
        if self.k14 is None or not getattr(self, "stacks", None):
            return []
        from .k14_condition import _lerp
        L = _lerp(self.k14.layers["chimney_soot"]["length_m"], self.k14.factor(self.k14_built))
        if L <= 0.0:
            return []
        return [(s["centre"][0], -s["centre"][1], L) for s in self.stacks]

    def k14_roof_rows(self, pts, tris):
        """T-2359: the roof shell cut with the rows a chimney plume needs. The joined shell's
        covering is a few large triangles, and `_TONE` is read at vertices, so a plume a metre
        and a half long has nothing to ride. Each plume's wedge (its bearing, half-angle and
        length, turned into this frame by the record's rotation) is boxed in plan; the covering
        is cut on the box's four sides and, inside it, by the plan lines x = c and z = c,
        K14_PLUME_ROWS to the plume's length. Nothing but covering inside a box is cut, so a
        stack, its flashing and the rest of the roof keep their triangles. A face that a cut
        put a point on the edge of (a flashing, a stack's foot, the covering just outside the
        box) takes that point and is fanned from its centroid, so every edge still has a face
        on each side and the shell stays closed. The K05 solid the gates read (`roof_shell`)
        is the uncut one; this is what is emitted."""
        plumes = self.k14_plumes()
        if not plumes:
            return pts, tris
        import numpy as np
        L = self.k14.layers["chimney_soot"]
        rot = self.p.condition["rotation_deg"]
        P = [tuple(q) for q in pts]
        made = {}

        def point(i, j, axis, c):
            key = (min(i, j), max(i, j), axis, c)
            if key not in made:
                a, b = P[key[0]], P[key[1]]
                t = (c - a[axis]) / (b[axis] - a[axis])
                q = [a[n] + (b[n] - a[n]) * t for n in range(3)]
                q[axis] = c
                made[key] = len(P)
                P.append(tuple(q))
            return made[key]

        def split(ids, axis, c):
            """A convex polygon cut on the plan line `axis` = c: its pieces, one or two."""
            side = [P[i][axis] - c for i in ids]
            if all(x >= -K14_ROW_SNAP_M for x in side) or all(x <= K14_ROW_SNAP_M for x in side):
                return [ids]
            lo, hi = [], []
            for k, i in enumerate(ids):
                j, si, sj = ids[(k + 1) % len(ids)], side[k], side[(k + 1) % len(ids)]
                if abs(si) <= K14_ROW_SNAP_M:
                    lo.append(i)
                    hi.append(i)
                else:
                    (lo if si < 0 else hi).append(i)
                if (si < -K14_ROW_SNAP_M and sj > K14_ROW_SNAP_M) or (si > K14_ROW_SNAP_M and sj < -K14_ROW_SNAP_M):
                    m = point(i, j, axis, c)
                    lo.append(m)
                    hi.append(m)
            return [lo, hi]
        polys = [(list(t[:3]), tuple(t[3:])) for t in tris]
        for x0, z0, length in plumes:
            step = length / K14_PLUME_ROWS
            arc = [L["lee_bearing_deg"] - L["half_angle_deg"] + i for i in range(2 * L["half_angle_deg"] + 1)]
            ring = [(x0, z0)] + [(x0 + length * math.sin(math.radians(b - rot)),
                                  z0 - length * math.cos(math.radians(b - rot))) for b in arc]
            # the box, on whole rows from the stack's centre, and the rows inside it
            box, rows = {}, []
            for axis, c0, k in ((0, x0, 0), (2, z0, 1)):
                i0 = math.floor((min(q[k] for q in ring) - c0) / step)
                i1 = math.ceil((max(q[k] for q in ring) - c0) / step)
                box[axis] = (round(c0 + i0 * step, 4), round(c0 + i1 * step, 4))
                rows += [(axis, round(c0 + i * step, 4)) for i in range(i0 + 1, i1)]
            rows = [(axis, c) for axis in (0, 2) for c in box[axis]] + rows   # its sides first
            nxt = []
            for ids, rest in polys:
                if rest[0] != "covering" or any(
                        max(P[i][axis] for i in ids) <= box[axis][0] + K14_ROW_SNAP_M
                        or min(P[i][axis] for i in ids) >= box[axis][1] - K14_ROW_SNAP_M for axis in (0, 2)):
                    nxt.append((ids, rest))
                    continue
                pieces = [ids]
                for axis, c in rows:
                    inside = []
                    for q in pieces:
                        if c in box[axis] or all(box[ax][0] - K14_ROW_SNAP_M <= P[i][ax] <= box[ax][1] + K14_ROW_SNAP_M
                                                     for i in q for ax in (0, 2)):
                            inside += split(q, axis, c)   # a side cuts the whole face; a row, the box
                        else:
                            inside.append(q)
                    pieces = inside
                nxt += [(q, rest) for q in pieces]
            polys = nxt
        # every edge a made point lies inside takes it, and that face is fanned from its centroid
        new = np.asarray(P[len(pts):], dtype=np.float64)
        out = []
        for ids, rest in polys:
            ring, mended = [], False
            for k, i in enumerate(ids):
                ring.append(i)
                a, b = np.asarray(P[i]), np.asarray(P[ids[(k + 1) % len(ids)]])
                ab = b - a
                t = (new - a) @ ab / (ab @ ab)
                off = np.linalg.norm(new - (a + np.outer(t, ab)), axis=1)
                on = np.nonzero((t > 1e-9) & (t < 1 - 1e-9) & (off < 1e-6))[0]
                if len(on):
                    mended = True
                    ring += [len(pts) + int(n) for n in on[np.argsort(t[on], kind="stable")]]
            if mended:
                c = len(P)
                P.append(tuple(float(np.mean([P[i][n] for i in ring])) for n in range(3)))
                fan = [(c, ring[k], ring[(k + 1) % len(ring)]) for k in range(len(ring))]
            else:
                fan = [(ids[0], ids[k], ids[k + 1]) for k in range(1, len(ids) - 1)]
            for f in fan:
                a, b, c = P[f[0]], P[f[1]], P[f[2]]
                n = _cross(_sub(b, a), _sub(c, a))
                if _dot(n, n) > 1e-14:
                    out.append(f + rest)
        return _weld_shell(P, out)

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
    def wall(self, cid, mat, O, R, length, height, thickness, holes, extra_breaks=(), bands=(), gaps=(), cols=(),
             construction="masonry"):
        p = self.p
        N = _cross(R, Y)
        conf = p.worst_conf("footprint", "stories", "storey_heights_m", "construction")
        seed = self.instance(cid, "wall", {"length_m": length, "height_m": height,
                                           "thickness_m": thickness, "construction": construction,
                                           "openings": len(holes)},
                             {"base": O, "top": _add(O, _mul(Y, height))})
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        sb = _breaks({0.0, length, *cols, *[e for h in holes for e in (h[0], h[1])]})
        yb = _breaks({0.0, height, *extra_breaks, *[e for h in holes for e in (h[2], h[3])]})
        # T-2410: a round-headed hole (s0, s1, sill, spring, its head right -> left) is cut as
        # a rectangle to its spring; over it, up to the first row clear of its crown, the
        # cells are left out and strips from the head's curve to that row fill them (K08's
        # wall_cells), so the reveal K06 builds on the same curve meets the wall edge to edge
        over = [(h[0], h[1], h[3], next(y for y in yb if y > max(q[1] for q in h[4]) + 0.01), h[4])
                for h in holes if len(h) > 4]
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
                if any(s0 < sc < s1 and sp < yc < top for s0, s1, sp, top, _c in over):
                    continue
                pr.face([P(sb[i], yb[j], 0), P(sb[i + 1], yb[j], 0),
                         P(sb[i + 1], yb[j + 1], 0), P(sb[i], yb[j + 1], 0)], N, b, conf)
        for _s0, _s1, _sp, top, curve in over:
            for q0, q1 in zip(curve, curve[1:]):    # q0 right of q1
                pr.face([P(q1[0], q1[1], 0), P(q0[0], q0[1], 0), P(q0[0], top, 0), P(q1[0], top, 0)], N, b, conf)
        for band in bands:  # belt courses, part of the wall component
            y0, y1, proud = band[:3]
            # T-3184: a basement's facing (side_base) framing the lights cut through it
            lights = band[3] if len(band) > 3 else ()
            for s0, s1 in _pieces(0.0, length, list(gaps) + [(h0, h1) for h0, h1, _, _ in lights]):   # T-2308: stopped against a bay
                self.proud_box("limestone_trim", (O, R, N), s0, s1, y0, y1, proud, seed, conf)
            for h0, h1, hs, hh in lights:
                self.proud_box("limestone_trim", (O, R, N), h0, h1, y0, hs, proud, seed, conf)
                self.proud_box("limestone_trim", (O, R, N), h0, h1, hh, y1, proud, seed, conf)
        return (O, R, N), thickness

    # -- k01.wall.wing.* (T-2343) ------------------------------------------------------
    def wing(self, w, sc_conf):
        """One rear wing: its south, north and rear walls in the K03 brick with their K06
        windows cut, the second-floor string course carried round from the main walls, and
        a flat deck, or since T-2841 a slated hip or gable (`wing_roof`). Its front stands on its host wall, which is not drawn behind it, so it
        has no front wall of its own; a later wing standing on its rear is cut out the same
        way. Its brick heads and its soot band take their datum from its own wall top.
        T-2417: a `frame` wing's walls are painted timber, the frame bay's (T-2356), its
        windows cased in the painted trim, with no brick course carried round it."""
        from .k01_frontage_params import wing_walls, FRAME_WALL_M
        p = self.p
        frame_wing = w.get("fabric") == "frame"
        keep, self.soffit_m = self.soffit_m, w["top_m"]
        on_rear = [(*x["host_span_m"], 0.0, x["deck_m"]) for x in p.rear_wings
                   if x["host_wall"] == f"k01.wall.wing.{w['id']}.rear"]
        # T-2900: a wing longer than its host wall has a front where it runs past the host;
        # along the host it is the host's wall, so it is not drawn there
        hv0, hv1 = w["host_v_m"]
        v0 = w["rect"][2]
        on_host = [(max(hv0, v0) - v0, min(hv1, w["rect"][3]) - v0, 0.0, w["top_m"])]
        walls = wing_walls(w)
        # T-3001: a wing standing taller than its host under a ridge along it (1801's gabled
        # section, three storeys on a host whose cornice is at 8.3 m) has a front where it
        # rises past the host's top: its roof's end comes down to the eave there, so the
        # cut in the host plane closes no more than the eave box, and the wall under it is
        # this wing's own, from the host's top to its wall top
        host = next((x for x in p.rear_wings if w["host_wall"] == f"k01.wall.wing.{x['id']}.rear"), None)
        host_top = p.eave_m if host is None else host["top_m"]
        if "front" not in walls and w["roof"]["kind"] != "flat" and w["roof"]["axis"] == "v" \
                and w["top_m"] > host_top + 1e-6:
            u1, v1 = w["rect"][1], w["rect"][3]
            walls["front"] = ((u1, 0.0, -v0), (0.0, 0.0, -1.0), v1 - v0)
            on_host = [(0.0, v1 - v0, 0.0, host_top)]
        for side, (O, R, length) in walls.items():
            cid = f"k01.wall.wing.{w['id']}.{side}"
            ops = [o for o in w["openings"] if o.wall == cid]
            # T-2842: and where a K08 tower stands on it, from grade to the wing's wall top
            cover = (on_rear if side == "rear" else on_host if side == "front" else []) \
                + [(*b["span_m"], 0.0, w["top_m"]) for b in p.bays if b["wall"] == cid]
            # T-3133: a round-headed light is cut on its head's curve, as the main walls cut it
            hs = [hole(o) for o in ops] + cover
            if frame_wing:
                frame, t = self.wall(cid, "bay_frame", O, R, length, w["top_m"], FRAME_WALL_M, hs,
                                     (w["top_m"],), construction="frame")
                for o in ops:
                    self.opening(o, frame, t, "bay_frame", "fascia")
                continue
            if p.stone.get("all_round"):
                # T-2788: an all-stone house's wing is coursed as its main walls are, on the
                # front's beds up to the wing's own wall top, its belts run round below it
                frame, t = (O, R, _cross(R, Y)), p.side_thickness_m
                for o in ops:
                    self.opening(o, frame, t, "rough_stone_trim", "limestone_trim", coursed=True)
                self.stone_front(cid, O, R, length, w["top_m"], w["top_m"], t, ops,
                                 self.front_course_beds, cover)
                continue
            breaks = (w["top_m"], *k03_brick.condition_breaks(w["top_m"]))
            frame, t = self.wall(cid, "brick", O, R, length, w["top_m"], p.side_thickness_m, hs, breaks)
            for o in ops:
                self.opening(o, frame, t, "brick", "limestone_trim")
            # the string course at its second floor, on the south and rear walls as the main
            # body's: the south one stops short of the front by the course's own projection,
            # so it never doubles a course the main south wall runs out past its quoin
            if side in ("south", "rear") and len(w["floors_m"]) > 1:
                s_from, s_to = (-k03_brick.STRING_PROUD, length - k03_brick.STRING_PROUD) if side == "south" \
                    else (0.0, length)
                for s0, s1 in _pieces(s_from, s_to, [c[:2] for c in cover]):
                    k03_brick.string_course(self, seed_of(self.sid, cid, 0), frame, s0, s1, w["floors_m"][1], sc_conf)
        self.soffit_m = keep
        if w["roof"]["kind"] == "flat":
            self.wing_deck(w)
        else:
            self.wing_roof(w)

    def wing_deck(self, w):
        """The wing's flat deck: a slab from its wall top to the fascia's top, run out over
        the south, north and rear walls by its overhang — painted tin on top, a painted
        soffit under, a fascia round the edge — and closed at the front end wherever the
        deck runs past the ends of the wall it stands on."""
        p = self.p
        u0, u1, v0, v1 = w["rect"]
        ov, yt, yd = w["overhang_m"], w["top_m"], w["deck_m"]
        hv0, hv1 = w["host_v_m"]
        conf = p.worst_conf("rear_wings", "footprint")
        seed = self.instance(f"k01.roof.wing.{w['id']}", "roof",
                             {"kind": "flat", "overhang_m": ov, "fascia_m": w["fascia_m"],
                              "covering": "painted_tin_sheet", "deck_datum_m": yd},
                             {"base": (u0, yt, -v1), "top": (u0, yd, -v1)})
        a0, a1, b0, b1 = u0 - ov, u1, v0 - ov, v1 + ov
        X = lambda u, y, v: (u, y, -v)
        tin, fas = "k04_painted_tin_sheet", "fascia"
        E, NZ = (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
        self.prim(tin).face([X(a0, yd, b0), X(a1, yd, b0), X(a1, yd, b1), X(a0, yd, b1)], Y,
                            self.basis(tin, X(a0, yd, b0), E, NZ, seed), conf)
        under = self.basis(fas, X(a0, yt, b0), E, NZ, seed)
        self.prim(fas).face([X(a0, yt, b0), X(a1, yt, b0), X(a1, yt, b1), X(a0, yt, b1)], (0.0, -1.0, 0.0), under, conf)
        edge = lambda O, R: self.basis(fas, O, R, Y, seed)
        self.prim(fas).face([X(a0, yt, b0), X(a1, yt, b0), X(a1, yd, b0), X(a0, yd, b0)], (0.0, 0.0, 1.0),
                            edge(X(a0, yt, b0), E), conf)
        self.prim(fas).face([X(a0, yt, b1), X(a1, yt, b1), X(a1, yd, b1), X(a0, yd, b1)], NZ,
                            edge(X(a1, yt, b1), (-1.0, 0.0, 0.0)), conf)
        self.prim(fas).face([X(a0, yt, b0), X(a0, yt, b1), X(a0, yd, b1), X(a0, yd, b0)], (-1.0, 0.0, 0.0),
                            edge(X(a0, yt, b1), (0.0, 0.0, 1.0)), conf)
        for c0, c1 in ((b0, min(hv0, b1)), (max(hv1, b0), b1)):
            if c1 - c0 > 1e-6:
                self.prim(fas).face([X(a1, yt, c0), X(a1, yt, c1), X(a1, yd, c1), X(a1, yd, c0)], E,
                                    edge(X(a1, yt, c1), (0.0, 0.0, 1.0)), conf)

    def wing_roof(self, w):
        """T-2841: a wing's hipped or gabled roof, slated (rear_wings[].roof): K05's hip or
        gable element over the wing's wall line, its eaves out by the deck's overhang on the
        deck's fascia, cut off in the host wall's plane. Where the ridge runs across the wing
        the cut takes the roof's whole section, so the ridge dies into the host wall; where it
        runs along the wing the front slope comes down to the wall at the wing's wall top.

        The junction is closed above the host's own top (the main eave, or the host wing's
        wall top): there nothing stands behind the cut, so it is drawn — in the wing's walling
        across the wing (its front wall, where the wing stands over its host, and the roof's
        end over it), in the eave's timber where the eaves run past its side walls. Below the
        host's top the host wall is drawn in that plane and the cut is behind it. A gable's end
        is the wing's walling above its wall top, and the eave's timber past its corners."""
        from . import k05_roofs as k5
        p, r = self.p, w["roof"]
        u0, u1, v0, v1 = w["rect"]
        o, f, top = w["overhang_m"], w["fascia_m"], w["top_m"]
        t = math.tan(math.radians(r["pitch_deg"]))
        z0, z1 = -v1, -v0
        host = next((x for x in p.rear_wings if w["host_wall"] == f"k01.wall.wing.{x['id']}.rear"), None)
        host_top = p.eave_m if host is None else host["top_m"]
        conf = p.worst_conf("rear_wings", "footprint")
        seed = self.instance(f"k01.roof.wing.{w['id']}", "roof",
                             {"kind": r["kind"], "pitch_deg": r["pitch_deg"], "ridge_along": r["axis"],
                              **({"gable_to": r["gable_to"]} if "gable_to" in r else {}),
                              "overhang_m": o, "fascia_m": f, "covering": r["covering"],
                              "eave_datum_m": top, "ridge_datum_m": r["ridge_m"], "host_top_m": host_top,
                              "construction": "k05"},
                             {"eave": (u0, top, z1), "ridge": ((u0 + u1) / 2, r["ridge_m"], (z0 + z1) / 2)})
        # a ridge across the wing is built past the host wall by more than the roof's span,
        # so its far end lies wholly beyond the cut and the ridge runs straight into it
        far = u1 + (v1 - v0) + 2 * o + 1.0 if r["axis"] == "u" else u1
        base = min(host_top, top - o * t - f) - 0.5
        if r["kind"] == "hip":
            hip, hs = k5.hip_element(u0, far, z0, z1, top, t, o, f)
            solids = [hip, k5.body_box(u0, far, z0, z1, base, hs)]
        elif r["axis"] == "u":   # a gable to the rear: the one verge, on the rear wall
            solids, _, _, _ = k5.gable_element(u0, far, z0, z1, top, t, o, o, f, base, "x", verge_ends=("lo",))
        else:                    # a gable to a flank: the ridge along the wing, a gable at each end
            solids, _, _, _ = k5.gable_element(z0, z1, u0, u1, top, t, o, o, f, base, "z")
        hi, end = r["ridge_m"] + 1.0, far + o + 2.0
        # T-2900: a wing longer than its host wall is cut only along the host: past it, its
        # eaves and its hip run round its own front
        hv0, hv1 = w["host_v_m"]
        c0 = -hv1 if v1 > hv1 + 1e-9 else z0 - o - 2.0
        c1 = -hv0 if v0 < hv0 - 1e-9 else z1 + o + 2.0
        cut = k5.extrude([(u1, base - 1.0), (end, base - 1.0), (end, hi), (u1, hi)], c0, c1,
                         k5.frame("z"), "host_end", "host_end", "host_end")
        pts, tris = _weld_shell(*k5.close(k5.subtract(k5.union_all(k5._snap(solids)), k5._snap([cut])[0])))
        walling = "bay_frame" if w.get("fabric") == "frame" else \
            "rough_stone_trim" if p.stone.get("all_round") else "brick"
        phase = (_k04_fabric(r["covering"]) or {}).get("course_phase_m", [0.0, 0.0])[1]
        planes = {}   # each covering plane's lowest point, its eave, where its courses start
        for a, b, c, role, n in tris:
            if role == "covering":
                key = tuple(round(x, 5) for x in n) + (round(_dot(n, pts[a]), 4),)
                low = min((pts[a], pts[b], pts[c]), key=lambda q: q[1])
                if key not in planes or low[1] < planes[key][1]:
                    planes[key] = low
        upright = lambda mat, n: self.basis(mat, (0.0, 0.0, 0.0), _unit(_cross(Y, n)),
                                            _cross(n, _unit(_cross(Y, n))), seed)
        for a, b, c, role, n in tris:
            tri = [pts[a], pts[b], pts[c]]
            if role in self.BOARD or role == "hidden":
                continue
            if role == "covering":
                key = tuple(round(x, 5) for x in n) + (round(_dot(n, pts[a]), 4),)
                up = _unit(_sub(Y, _mul(n, n[1])))
                self.prim("wing_slate").face(tri, n, self.basis("wing_slate", planes[key], _unit(_cross(up, n)), up,
                                                                seed, course_v=phase), conf)
            elif role in ("fascia", "soffit", "verge", "return"):
                b_ = self.basis("fascia", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), seed) \
                    if abs(n[1]) > 0.999 else upright("fascia", n)
                self.prim("fascia").face(tri, n, b_, conf)
            elif role in ("gable", "host_end"):
                # across the wall line it is walling, from the wing's wall top (a gable) or the
                # host's top (the junction) up; past the corners it is the eave's end
                k, (lo, hi_) = (2, (z0, z1)) if abs(n[0]) > abs(n[2]) else (0, (u0, u1))
                floor = top if role == "gable" else host_top
                eave_floor = -math.inf if role == "gable" else host_top
                pieces = ((_clip_half(_clip_half(_clip_half(tri, k, lo, 1), k, hi_, -1), 1, floor, 1), walling),
                          (_clip_half(_clip_half(tri, k, lo, -1), 1, eave_floor, 1), "fascia"),
                          (_clip_half(_clip_half(tri, k, hi_, 1), 1, eave_floor, 1), "fascia"))
                for piece, mat in pieces:
                    if len(piece) >= 3 and _poly_area(piece) > 1e-6:
                        self.prim(mat).face(piece, n, upright(mat, n), conf)
            else:
                raise ValueError(f"the K05 union left a {role!r} face on {w['id']}'s roof")

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
        if op.wall == "k01.wall.side.north":
            conf = max(conf, p.conf("north_bays"))
        elif op.wall.startswith("k01.wall.wing."):   # T-2343: a rear wing's own windows
            conf = max(conf, p.conf("rear_wings"))
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
        if op.component == ROUND_HOODED:
            # T-2410: a round-headed street window keeps K06's arch band as its moulded hood,
            # spring to spring, and stands a key block on the hood's crown
            # T-2780: or the window over a bay on its host wall (`window_over`), with no key
            # block unless the street front's round heads name one
            street = op.wall == "k01.wall.street_front"
            # T-3133: or a rear wing's flank light its picture draws round-headed (`round_heads`)
            conf = max(conf, p.conf("street_front_round_heads" if street else
                                    "rear_wings" if op.wall.startswith("k01.wall.wing.") else "bays"))
            if street and p.round_heads.get("hood"):
                # T-2960: K09's cornice hood on its two consoles over the head (1736's upper
                # lights, the c. 1890 photograph), which dresses it in place of the arch band
                self.glaze(op, frame, body_mat, stone_trim, seed, conf)
                k09_frontage.dress(self, op, frame, max(conf, p.conf("street_front_trim")))
                return
            # T-3133: a rear wing's round head is turned in its own brick, as its picture draws
            # it (1811's flank), where a front's or a bay's hood is the trim's stone
            wing = op.wall.startswith("k01.wall.wing.") and MATERIALS[body_mat].get("courses")
            self.glaze(op, frame, body_mat, stone_trim, seed, conf, head=True,
                       head_mat=body_mat if wing else None)
            k = p.round_heads.get("key") if street else None
            if k:
                self.proud_box(stone_trim, frame, op.s_m - k["width_m"] / 2, op.s_m + k["width_m"] / 2,
                               y1, y1 + k["height_m"], k["proud_m"], seed, conf)
            return
        if getattr(op, "plain", False):
            # T-2884: a head its picture shows plain (1625's south wall): the light, its hole cut
            # square or round, and nothing laid over it — no hood, no K03 arch, no lintel
            self.glaze(op, frame, body_mat, stone_trim, seed,
                       max(conf, p.conf("north_bays" if op.wall == "k01.wall.side.north" else
                                        "rear_wings" if op.wall.startswith("k01.wall.wing.") else "side_bays")))
            return
        if not door:
            # T-2298: a window is a K06 opening — reveal, sill, frame, sashes, glass,
            # blind, curtain and an enclosed room — built about this hole's sill socket
            self.glaze(op, frame, body_mat, stone_trim, seed, conf, skip=("reveal",) if cut else ())
        else:
            # T-2304: the door is a K07 entrance and its stoop, built about the threshold
            self.enter(op, frame, body_mat, seed, conf)
            if p.entrance_kit.get("hood"):
                self.door_hood(op, frame)   # T-2480
        brick_head = op.wall != "k01.wall.street_front" or p.street_front_trim.get("brick_heads") == "segmental"
        if MATERIALS[body_mat].get("courses") and not door and brick_head:
            # T-2291: a brick wall's opening takes a brick head, not the front's stone
            # lintel — two rowlock rings on a segmental arch, or a soldier flat head
            # where the eave leaves no room for the rings and their rise. A brick STREET
            # front (T-2341) keeps the front's stone dressings: its K09 head or the lintel,
            # unless its record arches them in the brick too (T-1861, `brick_heads`)
            crown = y1 + k03_brick.RISE_TO_SPAN * op.width_m + k03_brick.RINGS * (k03_brick.BED + k03_brick.JOINT)
            if crown < self.soffit_m - k03_brick.COURSE:
                k03_brick.segmental_head(self, seed, frame, s0, s1, y1, conf)
            else:
                k03_brick.soldier_head(self, seed, frame, s0, s1, y1, conf)
            return
        # T-3197: a carved tympanum on a stone lintel where the record names one for this light
        ty = self.front_tympanum(op)
        if ty is not None:
            self.tympanum_head(op, frame, ty, stone_trim, seed, max(conf, p.conf("street_front_trim")))
            return
        # T-2310: a K09 head where the record names one; else a flat lintel
        if k09_frontage.dress(self, op, frame, max(conf, p.conf("street_front_trim"))) or coursed:
            return
        # T-2326: a dormer whose face K10 dresses takes the kit's pediment cornice as its head
        if op.wall == "k01.wall.dormer_face" and k10_frontage.dresses_dormer(p):
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

    def _course_plan(self, frame, openings, yf, beds=None, extra=()):
        """The street front's course lines struck and cut into courses, bottom up: the
        holes and flat arches the courses are laid round, the seats the kits leave on it,
        the belts, and every (bed, top, kind). Struck before the front is laid so that a
        bay coursed on the front's own beds (T-2773) reads the same lines the front is
        cut on. T-2788: an all-stone house's other faces pass the front's `beds`, so a
        course runs level round every corner, and `extra` holes (a rear wing's span on its
        host wall) the courses stop at; their openings cut the courses wherever they fall."""
        p, k = self.p, self.p.stone
        O = frame[0]
        floors = p.floors_m
        wk = k["wall"]
        bc = k["base_course_m"]
        base_top = bc * k["base_courses"]
        cop_top = k["coping_top_m"]
        # T-2366: a round-arched group is laid by k01_arched_front, round its own hole and
        # voussoir block; every other opening is a rectangle with its flat arch
        af = p.arched_front if beds is None else None
        # T-2753: a proud frontispiece: the coursing and the openings on it laid on its face
        # (the street front's only; T-2788's other faces carry none)
        fp = p.frontispiece if beds is None else None
        frame_fp = self.frontispiece_frame(frame) if fp else None
        fs0, fbed = (fp["s_m"], fp["hood"]["bed_m"]) if fp else (None, None)
        grouped = {id(p.openings[i]) for i in k01_arched_front.grouped_ops(p)}
        square = [o for o in openings if id(o) not in grouped]
        holes = [(o.s_m - o.width_m / 2, o.s_m + o.width_m / 2, o.sill_m, o.head_m) for o in square]
        # T-2752: a window named off a photograph (`street_front_windows`) stands in the coursing
        # where the picture puts it, under no flat arch, and strikes no course line of its own:
        # its heads and sills differ window to window, and lines at each would band the front
        # T-3097: and on an all-stone house's other faces, a window read off a picture with its
        # head plain or round (`north_bays`/`side_bays`), which has no lintel to lay
        named = [o for o in square if o.component.startswith(STREET_WINDOW) or (beds is not None and o.plain)]
        lined = [h for o, h in zip(square, holes) if o not in named]
        # a flat arch where K09 leaves a flat head: the area lights and the third floor
        arches = [(s0, s1, y1, round(y1 + 0.30, 4)) for o, (s0, s1, _, y1) in zip(square, holes)
                  if k09_frontage.head(p, o) == k09_frontage.FLAT and o not in named
                  and not (fp and o.component == "k01.opening.door_leaf")]   # T-2753: its surround's lintel
        if af:
            rects = k01_arched_front.plan(self, frame)
            holes += rects
            lined += rects
        holes += [tuple(h[:4]) for h in extra]
        # what the kits seat on this face, widened by a joint and an arris so a piece's
        # edge never stands over a bevel; K06's sill beds are course lines
        m = wk["joint_m"] / 2 + wk["bevel_m"] + 0.01
        seats = [(a0 - m, a1 + m, b0 - m, b1 + m, kind) for a0, a1, b0, b1, kind in self.footprints.get(tuple(O), [])
                 + (self.footprints.get(tuple(frame_fp[0]), []) if fp else [])]
        sill_beds = {round(b0 + m, 4) for a0, a1, b0, b1, kind in seats if kind == "K06.sill"
                     and not any(a0 < o.s_m < a1 and o.sill_m - 0.3 < b1 - m < o.sill_m + 0.3 for o in named)}
        belts = [(floors[1] - 0.20, floors[1])] + ([(floors[2] - 0.15, floors[2])] if len(floors) > 2 else [])
        if af and af["belts"] is not None:   # T-2526: a door's arch alone keeps these
            belts = list(af["belts"])
        if "belts" in p.street_dress:   # T-2753: the photograph's own string course
            belts = list(p.street_dress["belts"])
        if "belts" in k:   # T-3184: the belts a brick front's picture draws, or none
            belts = list(k["belts"])
        # T-2366: a frieze stands between the stone's top and the soffit
        ytop = af["stone_top_m"] if af else yf
        lines = {0.0, cop_top, ytop, *[bc * i for i in range(1, k["base_courses"] + 1)]}
        lines |= {y for y in sill_beds if y > cop_top + 1e-6}
        lines |= {y for (_, _, _, y) in lined + arches if y > cop_top + 1e-6}
        lines |= {y for band in belts for y in band}
        if fp:   # T-2753: the hood's bed, the door surround's lintel and the carved panel
            pa = fp["panel"]
            lines |= {fbed, fp["door_surround"]["top_m"], pa["bed_m"], pa["bed_m"] + pa["height_m"]}
        if (k.get("coursing") or {}).get("even_below_m"):   # T-2773: the principal sill's bed
            lines.add(float(k["coursing"]["even_below_m"]))
        if (k.get("coursing") or {}).get("rhythm") == "even":   # T-2819: where the face turns smoother
            lines.add(float(k["coursing"]["even_above_m"]))
        if k.get("brick_above_m") is not None and beds is None:   # T-2914: where the brick begins
            lines.add(float(k["brick_above_m"]))
        if beds is not None:   # T-2788: the front's own lines, up to this face's top
            lines = {y for y in beds if y < ytop - 0.02} | {0.0, ytop}
        merged = []
        for y in sorted(round(y, 4) for y in lines if y <= ytop + 1e-6):
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
            elif yb - ya < lo_c - 1e-9 and not ("belts" in k and beds is None and ya >= k["brick_above_m"] - 1e-6):
                courses.append((ya, yb, "band"))   # too thin for the walling: a dressed band
            elif yb - ya < lo_c - 1e-9:
                courses.append((ya, yb, "walling"))   # T-3184: in the brick, brick (stone_front.belts)
            else:
                courses += [(a_, b_, "walling") for a_, b_ in self._walling(ya, yb)]
        return holes, arches, seats, belts, courses, square, ytop

    def front_beds(self):
        """T-2773: the bed lines of the street front's courses, bottom up, for a bay laid
        on them; the openings must already be seated (their K06 sills strike lines)."""
        if self.p.arched_front:
            raise ValueError("a bay coursed on the street front's beds needs a front with no arched group")
        mat, O, R, length, t, _ = self._walls["k01.wall.street_front"]
        front = [o for o in self.p.openings if o.wall == "k01.wall.street_front"]
        courses = self._course_plan((O, R, _cross(R, Y)), front, self._yf)[4]
        return sorted({y for ya, yb, _ in courses for y in (ya, yb)})

    def stone_front(self, cid, O, R, length, E, yf, thickness, openings, beds=None, extra=()):
        """The street front as K02 coursed ashlar, laid round what the kits have already
        seated on it (`self.footprints`: K06 sills, K07's stoop, K09's heads, aprons and
        entrance, K08's bay). Course lines are struck on the base, the coping, every K06
        sill's bed, every head and flat-arch top and the belts, and the walling between
        them is cut into equal courses inside the profile's range. An opening or a flat
        arch is a hole in a course; where a kit is seated, the course goes on but its
        stones are dressed smooth and laid flush (no rock face, no chip, a belt not
        proud), so every kit piece stands on a plane face, never on a rock face that
        would bury its foot. Returns the south corner's quoins for the side wall.
        T-2788: an all-stone house lays its flanks, rear and wings here too, each on the
        front's `beds` (`_course_plan`), with no arched group, quoin or named window."""
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
        holes, arches, seats, belts, courses, square, ytop = self._course_plan(frame, openings, yf, beds, extra)
        if beds is None:
            self.front_course_beds = sorted({y for ya, yb, _ in courses for y in (ya, yb)})
            self.front_courses, self.front_ytop = courses, ytop   # T-3006: a round corner's beds
        af = p.arched_front if beds is None else None
        # T-2753: a proud frontispiece: the courses and flat arches on it laid on its face
        fp = p.frontispiece if beds is None else None
        frame_fp = self.frontispiece_frame(frame) if fp else None
        fs0, fbed = (fp["s_m"], fp["hood"]["bed_m"]) if fp else (None, None)
        rects = holes + arches
        quoins, prev_joints, parity = [], [], 0
        # T-2914: over this line the walling is the K03 brick, its bond turned at the corner
        # as a brick wall's; only the dressed cells (surrounds, quoins, a panel) are stone in it
        brick = k.get("brick_above_m") if beds is None else None
        if brick is not None:
            P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
            bb = self.basis(self.front_brick, O, R, Y, 0, k03_brick.phase_u(cid, length, self.tiles[MATERIALS["brick"]["fabric"]][0]))
        for ci, (ya, yb, kind) in enumerate(courses):
            trim = kind in ("coping", "belt", "band")
            spec = tk if trim else wk
            lo, hi = k["trim_block_m"] if trim else k["block_m"]
            r = r_base if kind == "base" else r_wall
            jh = (k["channel_m"] if kind == "base" else spec["joint_m"]) / 2
            jv = spec["joint_m"] / 2
            if af and af["banded"] and kind in ("base", "walling"):
                jv = af["banded"]["vertical_joint_m"] / 2   # T-2366: banded, its rising joints hairlines
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
            # T-2753: the dressed stones of the surrounds and the frontispiece's quoins, this course's
            here += [q for q in self.dress_cells(square, ya, yb, ci, kind, length) if q[2] < yb - 1e-6 and q[3] > ya + 1e-6]
            in_brick = brick is not None and kind == "walling" and ya >= brick - 1e-6
            if in_brick:   # T-2914: a kit's seat on the brick is brick behind it, as on a brick wall
                here = [q for q in here if q[4] in DRESSED_CELLS]
            on_fp = bool(fp) and yb <= fbed + 1e-6
            # a seat's edge cuts the course too, unless it falls within 0.08 m of a harder
            # edge (a wall end, an opening, an arch) or of another seat's: no sliver stones
            S = sorted({0.0, length, *[min(max(x, 0.0), length) for o in obs for x in (o[0], o[1])],
                        *((fs0,) if on_fp else ())})
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
                        and spans[-1][3] == self._seated(here, sa, sb) and not (on_fp and abs(sa - fs0) < 1e-9):
                    spans[-1][1] = sb
                else:
                    spans.append([sa, sb, free, self._seated(here, sa, sb)])
            joints_here, j = [], 0
            corner = "south" in k["corners"] and kind in ("base", "walling")
            for sa, sb, free, _ in spans:
                for fy0, fy1 in free:
                    if in_brick and not self._seated(here, sa, sb, fy0, fy1):
                        self.prim(self.front_brick).face([P(sa, fy0, 0.0), P(sb, fy0, 0.0), P(sb, fy1, 0.0), P(sa, fy1, 0.0)],
                                                N, bb, conf)
                        continue
                    first = None
                    if corner and sa == 0.0 and abs(fy0 - ya) < 1e-9 and abs(fy1 - yb) < 1e-9 \
                            and not self._seated(here, 0.0, min(sb, hi), fy0, fy1):
                        rlo, rhi = k["quoin_return_m"]
                        long_side = parity % 2 == 0
                        # to the centimetre, so two returns never leave the brick a sliver
                        ret = round(rng.uniform(0.8 * rhi, rhi) if long_side else rng.uniform(rlo, 1.2 * rlo), 2)
                        first = lo if long_side else min(hi, 0.75 * hi)
                        if "south_return_m" not in k:   # T-2581: a strip is laid below
                            quoins.append((ret, ya, yb, kind, jh, jv, r))
                        parity += 1
                    full = abs(fy0 - ya) < 1e-9 and abs(fy1 - yb) < 1e-9
                    pieces = _lay(rng, sa, sb, lo, hi, first, prev_joints if full else ())
                    skip = frozenset()
                    for s0, s1 in pieces:
                        proud = on_fp and s0 >= fs0 - 1e-9
                        fr = frame_fp if proud else frame
                        joints = [0.0 if fy0 <= 1e-9 else jh, 0.0 if s1 >= length - 1e-9 else jv,
                                  0.0 if fy1 >= ytop - 1e-9 else jh,
                                  0.0 if s0 <= 1e-9 or (proud and abs(s0 - fs0) < 1e-9) else jv]
                        bseed = self._stone_seed(ccid, inst, j)
                        j += 1
                        # a kit seated on this stone: dressed smooth and flush, of the trim
                        flush = self._seated(here, s0, s1, fy0, fy1)
                        if kind == "coping" and not flush:
                            self.coping_piece(fr, s0, s1, fy0, fy1, joints, bseed, conf, r)
                        else:
                            dressed = trim or flush
                            brng = random.Random(bseed ^ 0x5EED)
                            rock = brng.uniform(*self._rock_range(ya, yb)) if not dressed else 0.0
                            skip = self.stone(fr, [(s0, fy0), (s1, fy0), (s1, fy1), (s0, fy1)], joints,
                                              "limestone_trim" if dressed else "rough_stone_trim",
                                              bseed, conf, recess=r, bevel=(tk if dressed else wk)["bevel_m"],
                                              F=0.05 if kind == "belt" and not flush else 0.0, rock=rock,
                                              chips=None if dressed else spec, skip=skip if not dressed else frozenset())
                        if kind == "base" and abs(fy1 - base_top) < 1e-6:
                            # the rusticated base's channels are deeper than the joints over
                            # it: a ledge closes the step between the two mortar floors
                            self.prim("mortar").face([_add(_add(fr[0], _mul(R, s)), _add(_mul(Y, base_top), _mul(N, d)))
                                                      for s, d in ((s0, -r_base), (s1, -r_base), (s1, -r_wall), (s0, -r_wall))],
                                                     _mul(Y, -1), self.basis("mortar", O, R, N, bseed), conf)
                        if 1e-9 < s1 < length - 1e-9:
                            joints_here.append(s1)
            prev_joints = joints_here
            if "south_return_m" in k:
                # T-2581: every course turns the corner the same length, the strip's edge
                # straight against the brick, up to the wall head
                quoins.append((k["south_return_m"], ya, yb, kind, jh, jv, r))
        if "south_return_m" in k and E - ytop > 0.02:
            quoins.append((k["south_return_m"], ytop, E, "walling", wk["joint_m"] / 2, wk["joint_m"] / 2, r_wall))
        for s0, s1, y1, y2 in arches:
            self.flat_arch(frame_fp if fp and s0 >= fs0 and y2 <= fbed else frame, s0, s1, y1, y2 - y1, conf, r_wall)
        if beds is None:
            self.street_window_dress(frame, square, conf, r_wall)
        elif any(o.plain for o in square):   # T-3097: a read round head's spandrels on a side face
            self.street_window_dress(frame, [o for o in square if o.plain], conf, r_wall, read=True)
        if beds is None:
            if p.street_dress.get("carved_bands"):   # T-2915: the belts carved off a picture
                k01_arched_front.street_carved_bands(self, frame, p.street_dress["carved_bands"], conf)
        if fp:
            self.frontispiece(frame, length, conf)
        if af:
            k01_arched_front.lay(self, frame, yf, length, conf, r_wall)
        if beds is None and p.street_iron:   # T-3184: a brick front's balconettes and stoop rails
            k01_arched_front.street_iron(self, frame, p.street_iron, conf)
        # the wall behind the soffit, up to the eave: inside the roof, one plain face
        # (T-3112: from the pier's side, which stops under the cap)
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        s_lo = p.front_pier["to_m"] if p.front_pier and beds is None else 0.0
        s_hi = length
        if p.cant_corner:   # T-3186: and stopped where a canted corner cuts the wall
            c0, c1 = k01_frontage_params.cant_corner_plan(p.cant_corner, p.depth_m, p.width_m)["walls"].get(
                cid, (length, length))
            s_lo, s_hi = (max(s_lo, c1), s_hi) if c0 <= 1e-9 else (s_lo, min(s_hi, c0))
        if E - yf > 1e-6:
            if brick is not None:   # T-2914: brick up to the eave
                self.prim(self.front_brick).face([P(s_lo, yf, 0.0), P(length, yf, 0.0), P(length, E, 0.0), P(s_lo, E, 0.0)], N, bb, conf)
            else:
                self.prim("rough_stone_trim").face([P(s_lo, yf, 0.0), P(s_hi, yf, 0.0), P(s_hi, E, 0.0), P(s_lo, E, 0.0)],
                                                   N, self.basis("rough_stone_trim", O, R, Y, 0), conf)
        return frame, quoins

    def street_window_dress(self, frame, openings, conf, recess, read=False):
        """T-2752: what the coursing leaves in a named street window's hole (`street_front_windows`):
        a mullion between its lights, one dressed stone from sill to head, and over a segmental
        head the spandrels from K06's curve up to the hole's top, flush strips of the walling
        (the photograph draws the head as a plain line in the ashlar, under no band or block).
        K06 builds each light's reveal, so the mullion's sides and the head's soffit are its."""
        from . import k06_windows
        wall_frame = frame
        hj = self.p.stone["wall"]["joint_m"] / 2
        cid = "k01.opening.street_dress"
        for op in openings:
            # T-3097: `read`, a side face's plain or round-headed window read off a picture
            # T-3184: or a stone basement's round-headed light read off a picture (1834's)
            if not (op.component.startswith(STREET_WINDOW) or (read and op.plain)
                    or (op.plain and op.component == "k01.opening.sash_round_plain" and op.wall == "k01.wall.street_front")):
                continue
            # T-2753: a window on the frontispiece is dressed on its face
            frame = self.frontispiece_frame(wall_frame) if self.p.on_frontispiece(op) else wall_frame
            O, R, N = frame
            P = lambda s, y: _add(_add(O, _mul(R, s)), _mul(Y, y))
            v = self.kit_variant(op)
            bays, mull = v.get("bays", 1), v.get("mullion_m", 0.0)
            if bays == 1 and v["head"] == "flat":
                continue
            s0, s1, y0, y1 = op.s_m - op.width_m / 2, op.s_m + op.width_m / 2, op.sill_m, op.head_m
            self.instance(cid, "opening", {"of": op.component, "bays": bays, "mullion_m": mull, "head": v["head"]},
                          {"sill": P(op.s_m, y0), "head": P(op.s_m, y1)})
            inst, j = len(self.components[cid]["instances"]) - 1, 0
            bw = (op.width_m - mull * (bays - 1)) / bays
            for b in range(1, bays):
                m0 = s0 + b * bw + (b - 1) * mull
                self.stone(frame, [(m0, y0), (m0 + mull, y0), (m0 + mull, y1), (m0, y1)], [hj, 0.0, hj, 0.0],
                           "dress_stone", self._stone_seed(cid, inst, j), conf, recess=recess, bevel=0.0)
                j += 1
            if v["head"] in ("segmental", "round"):   # T-2889: a round head's spandrels too
                ros = k06_windows.rise_over_span(v, self._kit)
                rr = v.get("head_radius_ratio", 1.0)
                rise = k06_windows.Head(v["head"], s0, s1, 0.0, ros, rr).rise
                hd = k06_windows.Head(v["head"], s0, s1, y1 - rise, ros, rr)
                curve = hd.curve(0.0, s1, s0)
                for q0, q1 in zip(curve, curve[1:]):    # q0 right of q1
                    pts = []
                    for q in ((q1[0], q1[1]), (q0[0], q0[1]), (q0[0], y1), (q1[0], y1)):
                        if not pts or math.dist(pts[-1], q) > 1e-4:
                            pts.append(q)
                    if math.dist(pts[0], pts[-1]) < 1e-4:
                        pts.pop()
                    if len(pts) < 3 or max(y1 - q0[1], y1 - q1[1]) < 0.003:
                        continue
                    ba = self.p.stone.get("brick_above_m")
                    if ba is not None and min(q[1] for q in pts) >= ba - 1e-6:
                        # T-2914: a spandrel over the brick line is brick, flush, its bond the wall's
                        bb = self.basis(self.front_brick, O, R, Y, 0, k03_brick.phase_u(
                            "k01.wall.street_front", self.p.width_m, self.tiles[MATERIALS["brick"]["fabric"]][0]))
                        self.prim(self.front_brick).face([P(*q) for q in pts], N, bb, conf)
                        continue
                    self.stone(frame, pts, [0.0] * len(pts), "rough_stone_trim", self._stone_seed(cid, inst, j), conf,
                               recess=recess, bevel=0.0)
                    j += 1
                ring = next((r for r in self.p.street_dress.get("voussoirs", ())
                             if abs(r["s_m"] - op.s_m) < 1e-6 and abs(r["sill_m"] - op.sill_m) < 1e-6), None)
                if ring:
                    self.street_voussoirs(frame, hd, ring, conf, recess, cid, inst, j)

    KEYSTONE_PROUD_M = 0.03   # T-2889: a keystone stands this far before its ring

    def street_voussoirs(self, frame, hd, ring, conf, recess, cid, inst, j):
        """T-2889: a named window's arch turned in `ring["stones"]` dressed voussoirs between
        the head's curve and a ring `ring_m` outside it, each cut on radii from the head's own
        centre and standing `proud_m` before the wall, so that where the ring rises past a
        shaped gable's foot it stands before the gable's face as well; the middle stone is the
        keystone, carried up to `key_m` over the crown and a little prouder (1812 Prairie's
        third storey, its photograph)."""
        wk = self.p.stone["wall"]
        hj = wk["joint_m"] / 2
        r0, r1 = hd.R, hd.R + ring["ring_m"]
        cy = hd.cy
        ta = math.atan2(hd.spring - cy, hd.s1 - hd.cx)
        n = ring["stones"]
        angs = [ta + (math.pi - 2 * ta) * i / n for i in range(n + 1)]
        P = lambda r_, t: (hd.cx + r_ * math.cos(t), cy + r_ * math.sin(t))
        kw, kh = ring["key_m"]
        crown = hd.apex()
        for i, (a0, a1) in enumerate(zip(angs, angs[1:])):
            mid = (a0 + a1) / 2
            bed = _unit(_add(_mul(frame[1], math.cos(mid)), _mul(Y, math.sin(mid))))
            if i == n // 2:   # the keystone
                pts = [P(r0, a0), (hd.cx + kw / 2, crown + kh), (hd.cx - kw / 2, crown + kh), P(r0, a1)]
                F = ring["proud_m"] + self.KEYSTONE_PROUD_M
            else:
                # T-3091: long and short in turn, the keystone's neighbours short
                r_ = r0 + ring["short_m"] if "short_m" in ring and (i - n // 2) % 2 else r1
                pts = [P(r0, a0), P(r_, a0), P(r_, a1), P(r0, a1)]
                F = ring["proud_m"]
            self.stone(frame, pts, [hj] * 4, "dress_stone", self._stone_seed(cid, inst, j), conf,
                       recess=recess, bevel=wk["bevel_m"], F=F, bed=bed)
            j += 1
        return j

    # -- T-2753: the dressed surrounds and the proud frontispiece --------------------------
    def frontispiece_frame(self, frame):
        """The street front's frame moved out to the frontispiece's face."""
        O, R, N = frame
        return (_add(O, _mul(N, self.p.frontispiece["proud_m"])), R, N)

    def dress_cells(self, openings, ya, yb, ci, kind, length):
        """The cells of course `ci` [ya, yb] whose stones are dressed smooth and laid flush, as
        a kit's seat is: each surrounded window's jambs, a stone `returns_m` long and short in
        turn up the courses, and its lintel course over the head, the short return past each
        jamb (`street_dress.surrounds`);
        the frontispiece's two arrises quoined the same way from the coping up; the door's
        surround, a band round it and its lintel; and the carved panel's bed. Empty for a
        front with none of them, so every other house's coursing is untouched."""
        p, out = self.p, []
        su, fp = p.street_dress.get("surrounds"), p.frontispiece
        if su:
            ret = su["returns_m"][ci % 2]
            for o in openings:
                if not o.component.startswith(STREET_WINDOW) or not any(
                        p.floors_m[k] <= o.sill_m < (p.floors_m[k + 1] if k + 1 < len(p.floors_m) else 1e9)
                        for k in su["storeys"]):
                    continue
                s0, s1 = o.s_m - o.width_m / 2, o.s_m + o.width_m / 2
                if min(yb, o.head_m) - max(ya, o.sill_m) >= 0.05:
                    out += [(max(s0 - ret, 0.0), s0, o.sill_m, o.head_m, "K01.surround"),
                            (s1, min(s1 + ret, length), o.sill_m, o.head_m, "K01.surround")]
                lo = su["returns_m"][0]   # the lintel runs the short return past each jamb
                out.append((max(s0 - lo, 0.0), min(s1 + lo, length), o.head_m, o.head_m + su["lintel_m"], "K01.surround"))
        if fp:
            bed, q = fp["hood"]["bed_m"], fp["quoins_m"][ci % 2]
            if kind != "base" and kind != "coping" and yb <= bed + 1e-6:
                out += [(fp["s_m"], fp["s_m"] + q, ya, yb, "K01.quoin"), (length - q, length, ya, yb, "K01.quoin")]
            door = next(o for o in openings if o.component == "k01.opening.door_leaf")
            ds = fp["door_surround"]
            d0, d1 = door.s_m - door.width_m / 2, door.s_m + door.width_m / 2
            out += [(d0 - ds["band_m"], d0, door.sill_m, door.head_m, "K01.surround"),
                    (d1, d1 + ds["band_m"], door.sill_m, door.head_m, "K01.surround"),
                    (d0 - ds["band_m"], d1 + ds["band_m"], door.head_m, ds["top_m"], "K01.surround")]
            pa = fp["panel"]
            out.append((pa["s_m"] - pa["width_m"] / 2, pa["s_m"] + pa["width_m"] / 2, pa["bed_m"],
                        pa["bed_m"] + pa["height_m"], "K01.panel"))
        return out

    def frontispiece(self, frame, length, conf):
        """k01.wall.street_frontispiece: what closes the step the frontispiece's face makes —
        its returns at both arrises, grade to the hood's bed — and the hood mould capping
        it over its window, out past its face and its north arris; and the carved panel over
        the door: a raised moulded border and, inside it, a raised oval cartouche standing
        for the carving (the print's figures are not modelled)."""
        p, fp = self.p, self.p.frontispiece
        O, R, N = frame
        Of = self.frontispiece_frame(frame)
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        s0, pr, h = fp["s_m"], fp["proud_m"], fp["hood"]
        conf = max(conf, p.conf("street_front_frontispiece"))
        seed = self.instance("k01.wall.street_frontispiece", "wall",
                             {"s_m": s0, "proud_m": pr, "quoins_m": list(fp["quoins_m"]),
                              "hood_m": [h["bed_m"], h["top_m"]], "hood_overhang_m": h["overhang_m"],
                              "door_surround_band_m": fp["door_surround"]["band_m"]},
                             {"north_arris": P(s0, 0.0, pr), "hood": P((s0 + length) / 2, h["bed_m"], pr)})
        cop = p.stone["coping_top_m"]
        for s, hint in ((s0, _mul(R, -1)), (length, R)):
            for y0, y1, mat in ((0.0, cop, "rough_stone_trim"), (cop, h["bed_m"], "limestone_trim")):
                self.prim(mat).face([P(s, y0, 0.0), P(s, y0, pr), P(s, y1, pr), P(s, y1, 0.0)], hint,
                                    self.basis(mat, O, N, Y, seed), conf)
        # the hood mould: a weathered slab, its drip a fillet under its front edge
        ov = h["overhang_m"]
        self.proud_box("limestone_trim", frame, s0 - ov, length, h["bed_m"] + 0.05, h["top_m"], pr + ov, seed, conf)
        self.proud_box("limestone_trim", frame, s0 - ov + 0.03, length, h["bed_m"], h["bed_m"] + 0.05, pr + ov - 0.03,
                       seed, conf)
        # the carved panel, on the frontispiece's face
        pa = fp["panel"]
        cs = self.instance("k01.wall.carved_panel", "wall",
                           {"width_m": pa["width_m"], "height_m": pa["height_m"], "proud_m": pa["proud_m"],
                            "carving": "an oval cartouche standing for the print's figures"},
                           {"centre": P(pa["s_m"], pa["bed_m"] + pa["height_m"] / 2, pr)})
        a0, a1 = pa["s_m"] - pa["width_m"] / 2, pa["s_m"] + pa["width_m"] / 2
        b0, b1 = pa["bed_m"], pa["bed_m"] + pa["height_m"]
        e, dp = 0.06, pa["proud_m"]
        for c0, c1, r0, r1 in ((a0, a1, b0, b0 + e), (a0, a1, b1 - e, b1), (a0, a0 + e, b0 + e, b1 - e),
                               (a1 - e, a1, b0 + e, b1 - e)):
            self.proud_box("limestone_trim", Of, c0, c1, r0, r1, dp, cs, conf)
        cx, cy = pa["s_m"], (b0 + b1) / 2
        rx, ry = (a1 - a0) / 2 - e - 0.06, (b1 - b0) / 2 - e - 0.04
        ring = [(cx + rx * math.cos(2 * math.pi * i / 16), cy + ry * math.sin(2 * math.pi * i / 16)) for i in range(16)]
        Pf = lambda q, d: _add(_add(_add(Of[0], _mul(R, q[0])), _mul(Y, q[1])), _mul(N, d))
        pm = self.prim("limestone_trim")
        pm.face([Pf(q, dp) for q in ring], N, self.basis("limestone_trim", Of[0], R, Y, cs), conf)
        for i in range(16):
            qa, qb = ring[i], ring[(i + 1) % 16]
            out = _unit(_add(_mul(R, qb[1] - qa[1]), _mul(Y, qa[0] - qb[0])))
            pm.face([Pf(qa, 0.0), Pf(qb, 0.0), Pf(qb, dp), Pf(qa, dp)], out,
                    self.basis("limestone_trim", Of[0], R, N, cs), conf)

    def _walling(self, ya, yb):
        """The walling courses between two struck lines. Equal courses, as few as the
        profile's tallest allows; or, where the record's `coursing` reads the photograph's
        rhythm (T-2566), a high course and a low one in turn from the bed up, the low one
        `low_ratio` of the high (or the profile's least course, if that is more), both
        inside the profile's course range. Every span from `even_above_m` up is laid even,
        and (T-2773) every span under `even_below_m`, where one is named, as the 1888 plate
        lays Keith's front from the principal sill down; `deep_max_m`, where named, holds the
        high course under the photograph's reading rather than the profile's tallest."""
        k = self.p.stone
        lo_c, hi_c = k["course_m"]
        h = yb - ya
        c = k.get("coursing")
        if c and c["rhythm"] == "alternating" and ya < c["even_above_m"] - 1e-6 \
                and not yb <= c.get("even_below_m", 0.0) + 1e-6:
            r = c["low_ratio"]
            deep_max = min(hi_c, c.get("deep_max_m", hi_c))   # T-2773: the photograph's deep course
            for n in range(1, 64):
                high, low = (n + 1) // 2, n // 2
                th = h / (high + r * low)
                tl = r * th
                if low and tl < lo_c:   # the low course at the profile's least, the high ones take the rest
                    tl = lo_c
                    th = (h - low * tl) / high
                if th > deep_max + 1e-9:
                    continue
                if th < tl - 1e-9:
                    break
                out, y = [], ya
                for i in range(n):
                    step = th if i % 2 == 0 else tl
                    out.append((y, yb if i == n - 1 else y + step))
                    y += step
                return out
        n_ = math.ceil(h / hi_c - 1e-9)
        return [(ya + h * i / n_, ya + h * (i + 1) / n_) for i in range(n_)]

    def _rock_range(self, ya, yb):
        """The rock face a walling stone may rise, inside the profile's range: the whole
        range without a `coursing`; with one (T-2566), the upper half on a high course
        and the lower half on a low one, as the photograph's deep and shallow courses
        read, and the bottom `even_rock_share` of it on the even courses above
        `even_above_m`."""
        lo, hi = self.p.stone["rock_face_m"]
        c = self.p.stone.get("coursing")
        if not c or hi <= lo:
            return lo, hi
        if ya >= c["even_above_m"] - 1e-6:
            return lo, lo + (hi - lo) * c["even_rock_share"]
        if c["rhythm"] == "even":   # T-2819: no high and low courses, the whole range below the line
            return lo, hi
        mid = (lo + hi) / 2
        lo_c, hi_c = self.p.stone["course_m"]
        return (mid, hi) if yb - ya >= (lo_c + hi_c) / 2 else (lo, mid)

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
        strip = "south_return_m" in k
        prev = ()
        for i, (ret, ya, yb, kind, jh, jv, r) in enumerate(rows):
            seed = self.instance(cid, "wall", {"return_m": ret, "bed_m": ya, "height_m": yb - ya, "kind": kind,
                                               "fabric": k["fabric"]},
                                 {"corner": P(length, ya, 0.0)})
            inst = len(self.components[cid]["instances"]) - 1
            s0 = length - ret
            if not strip:
                rock = random.Random(seed ^ 0x5EED).uniform(*self._rock_range(ya, yb))
                self.stone(frame, [(s0, ya), (length, ya), (length, yb), (s0, yb)],
                           [0.0 if ya <= 1e-9 else jh, 0.0, jh, jv], "rough_stone_trim",
                           self._stone_seed(cid, inst, 0), conf, recess=r, bevel=k["wall"]["bevel_m"],
                           rock=rock, chips=k["wall"])
            else:
                # T-2581: a straight strip is cut into the front's own blocks, its rising
                # joints kept off the course below's; a trim course turns as dressed trim
                trim = kind in ("coping", "belt", "band")
                spec = k["trim_edges"] if trim else k["wall"]
                lo, hi = k["trim_block_m"] if trim else k["block_m"]
                pieces = _lay(random.Random(seed), s0, length, lo, hi, None, prev)
                prev = [b for _, b in pieces[:-1]]
                top = i + 1 == len(rows)
                for j, (a0, a1) in enumerate(pieces):
                    bseed = self._stone_seed(cid, inst, j)
                    rock = 0.0 if trim else random.Random(bseed ^ 0x5EED).uniform(*self._rock_range(ya, yb))
                    self.stone(frame, [(a0, ya), (a1, ya), (a1, yb), (a0, yb)],
                               [0.0 if ya <= 1e-9 else jh, 0.0 if a1 >= length - 1e-9 else jv,
                                0.0 if top else jh, jv], "limestone_trim" if trim else "rough_stone_trim",
                               bseed, conf, recess=r, bevel=spec["bevel_m"], rock=rock,
                               chips=None if trim else spec)
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
                 "blind": "blind", "curtain": "curtain", "backing": "backing",
                 # T-3091: a pictured leaded light's cames (1812's small arched window), in the iron
                 "came": "iron"}

    # -- k01.wall.front_pier (T-3112) ---------------------------------------------------
    PIER_LIP_M = 0.03   # the weathering's slate stands this far over the cap at its front edge

    def pier_slope(self):
        """T-3112: the weathering's top over the pier, as y(u): from the cap's front edge,
        PIER_LIP_M over the cap's top, rising back at the record's pitch."""
        fp = self.p.front_pier
        tp = math.tan(math.radians(fp["weathering_pitch_deg"]))
        front, yt = self.p.depth_m + fp["cap_proud_m"], fp["cap_m"][1]
        return lambda u: yt + self.PIER_LIP_M + (front - u) * tp

    def front_pier(self, thickness):
        """T-3112: the pier at the street front's low-s end (`front_pier`), laid after the
        front (whose courses stop at it): the front's base and coping, then rock-faced
        walling in courses of the front's own range, unbroken by the front's belts, up to a
        dressed band, one rock-faced course and a moulded cap, the band and the cap proud of
        the pier and returned along the side wall as far back as the weathering over them
        reaches the soffit. The weathering, and the eave cut back over it, are the roof's."""
        p, k, fp = self.p, self.p.stone, self.p.front_pier
        D, to = p.depth_m, fp["to_m"]
        (b0, b1), (c0, c1) = fp["band_m"], fp["cap_m"]
        conf = p.worst_conf("footprint", "stories", "storey_heights_m", "construction", "stone_front", "front_pier")
        cid = "k01.wall.front_pier"
        seed0 = self.instance(cid, "wall", {"length_m": to, "height_m": c1, "thickness_m": thickness,
                                            "construction": "masonry", "fabric": k["fabric"],
                                            "dressing": k["dressing"], "band_m": list(fp["band_m"]),
                                            "cap_m": list(fp["cap_m"]), "cap_proud_m": fp["cap_proud_m"]},
                              {"base": (D, 0.0, 0.0), "top": (D, c1, 0.0)})
        inst = len(self.components[cid]["instances"]) - 1
        rng = random.Random(seed0)
        frame = ((D, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0))
        wk, tk = k["wall"], k["trim_edges"]
        base_top, cop_top = k["base_course_m"] * k["base_courses"], k["coping_top_m"]
        # the front's own bed lines below the band, less its belts', walled anew between them
        belts = {y for ya, yb, kind in self.front_courses if kind == "belt" for y in (ya, yb)}
        lines = sorted({0.0, b0, *[y for ya, yb, _ in self.front_courses for y in (ya, yb)
                                   if y < b0 - 0.1 and all(abs(y - e) > 1e-6 for e in belts)]})
        courses = []
        for ya, yb in zip(lines, lines[1:]):
            if yb <= base_top + 1e-6:
                courses.append((ya, yb, "base"))
            elif abs(ya - base_top) < 1e-6 and abs(yb - cop_top) < 1e-6:
                courses.append((ya, yb, "coping"))
            else:
                courses += [(a_, b_, "walling") for a_, b_ in self._walling(ya, yb)]
        courses += [(b0, b1, "band"), (b1, c0, "walling"), (c0, c1, "cap")]
        prev, j = (), 0
        for ya, yb, kind in courses:
            trim = kind in ("coping", "band", "cap")
            spec = tk if trim else wk
            lo, hi = k["trim_block_m"] if trim else k["block_m"]
            r = k["channel_depth_m"] if kind == "base" else wk["recess_m"]
            jh = (k["channel_m"] if kind == "base" else spec["joint_m"]) / 2
            jv = spec["joint_m"] / 2
            pieces = [(0.0, to)] if trim else _lay(rng, 0.0, to, lo, max(lo, min(hi, to)), None, prev)
            prev = [s1 for _, s1 in pieces[:-1]]
            for s0, s1 in pieces:
                bseed = self._stone_seed(cid, inst, j)
                j += 1
                joints = (0.0 if ya <= 1e-9 else jh, 0.0 if s1 >= to - 1e-9 else jv, jh, 0.0 if s0 <= 1e-9 else jv)
                if kind == "coping":
                    self.coping_piece(frame, s0, s1, ya, yb, joints, bseed, conf, r)
                elif kind in ("band", "cap"):
                    continue
                else:
                    rock = random.Random(bseed ^ 0x5EED).uniform(*self._rock_range(ya, yb))
                    self.stone(frame, [(s0, ya), (s1, ya), (s1, yb), (s0, yb)], joints, "rough_stone_trim",
                               bseed, conf, recess=r, bevel=spec["bevel_m"], rock=rock, chips=spec)
        # the band and the cap: dressed, proud, and turned onto the side wall back to where the
        # weathering over them meets the soffit; the cap's lower member a narrower fillet
        L = self.pier_slope()
        back = max(0.3, D - (self.soffit_m - (c1 + self.PIER_LIP_M)) /
                   math.tan(math.radians(fp["weathering_pitch_deg"])) + fp["cap_proud_m"])
        side = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        cp, bp = fp["cap_proud_m"], fp["band_proud_m"]
        for y0, y1, d, sd in ((b0, b1, bp, 0), (c0, c0 + 0.4 * (c1 - c0), 0.6 * cp, 1), (c0 + 0.4 * (c1 - c0), c1, cp, 2)):
            self.proud_box("limestone_trim", frame, -d, to, y0, y1, d, seed0 + sd, conf)
            self.proud_box("limestone_trim", side, back, D, y0, y1, d, seed0 + sd, conf)
        self.pier_back_u = back
        assert L(D) > c1

    # -- k01.wall.round_corner (T-3006) -------------------------------------------------
    def round_stone(self, C, rad, a0, a1, y0, y1, joints, mat, seed, conf, *, recess, bevel, F=0.0, rock=0.0):
        """One stone of a rounded corner: the cell [a0, a1] x [y0, y1] on the radius `rad`
        about the plan centre C (x, z), its angle a turned from +x towards -z, `joints` its
        half joints (bottom, a1 end, top, a0 end). Laid as `stone` lays a plane one: the
        arris is the cell less its joints, recessed to the mortar at -recess; the face is
        the arris less the bevel, F proud of the round, and a rock face rises `rock` further
        along a crest up its middle. Every face follows the curve in facets of at most 7.5
        degrees, so the round reads round and not as a polygon of plane stones."""
        rng = random.Random(seed)
        P = lambda a, y, d: (C[0] + (rad + d) * math.cos(a), y, C[1] - (rad + d) * math.sin(a))
        radial = lambda a: (math.cos(a), 0.0, -math.sin(a))
        tangent = lambda a: (-math.sin(a), 0.0, -math.cos(a))   # towards a rising
        jb, jr, jt, jl = joints
        A0, A1, B0, B1 = a0 + jl / rad, a1 - jr / rad, y0 + jb, y1 - jt
        f0, f1, g0, g1 = A0 + bevel / rad, A1 - bevel / rad, B0 + bevel, B1 - bevel
        n = max(2, math.ceil((a1 - a0) / math.radians(7.5)))
        fa = [f0 + (f1 - f0) * i / n for i in range(n + 1)]
        aa = [A0 + (A1 - A0) * i / n for i in range(n + 1)]
        am = (a0 + a1) / 2
        origin, bed, mirror = P(a0, y0, 0.0), tangent(am), bool(seed >> 31)

        def face(pts, hint, project=True):
            self._sface(mat, pts, hint, origin, bed, seed, mirror, conf, project)
        if rock > 0:
            # a split face: a crest up the stone near its middle, each of its points at its
            # own height, the face falling from it to the arris on every side
            tc = 0.5 + rng.uniform(-0.2, 0.2)
            ym = (g0 + g1) / 2 + rng.uniform(-0.2, 0.2) * (g1 - g0)
            crest = [P(fa[i], ym, F + rock * min(i / n / tc, (1 - i / n) / (1 - tc)) * rng.uniform(0.6, 1.0))
                     for i in range(n + 1)]
            for i in range(n):
                for lo_, hi_ in (((P(fa[i], g0, F), P(fa[i + 1], g0, F)), (crest[i], crest[i + 1])),
                                 ((crest[i], crest[i + 1]), (P(fa[i], g1, F), P(fa[i + 1], g1, F)))):
                    for tri in ((lo_[0], lo_[1], hi_[1]), (lo_[0], hi_[1], hi_[0])):
                        face(list(tri), radial(am), project=False)
        else:
            for i in range(n):
                face([P(fa[i], g0, F), P(fa[i + 1], g0, F), P(fa[i + 1], g1, F), P(fa[i], g1, F)],
                     radial((fa[i] + fa[i + 1]) / 2))
        for i in range(n):   # the bevels down to the arris, under the face and over it
            out = _mul(radial((fa[i] + fa[i + 1]) / 2), 0.05)
            face([P(fa[i], g0, F), P(fa[i + 1], g0, F), P(aa[i + 1], B0, -recess), P(aa[i], B0, -recess)],
                 _add(_mul(Y, -1), out))
            face([P(fa[i], g1, F), P(fa[i + 1], g1, F), P(aa[i + 1], B1, -recess), P(aa[i], B1, -recess)],
                 _add(Y, out))
        face([P(f0, g0, F), P(f0, g1, F), P(A0, B1, -recess), P(A0, B0, -recess)], _mul(tangent(a0), -1))
        face([P(f1, g0, F), P(f1, g1, F), P(A1, B1, -recess), P(A1, B0, -recess)], tangent(a1))
        mb = self.basis("mortar", origin, bed, Y, seed)
        for i in range(n):   # the mortar fills the whole cell, so every joint has a floor
            b0_, b1_ = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
            self.prim("mortar").face([P(b0_, y0, -recess), P(b1_, y0, -recess), P(b1_, y1, -recess),
                                      P(b0_, y1, -recess)], radial((b0_ + b1_) / 2), mb, conf)

    def round_corner(self, thickness):
        """T-3006: the front block's rounded corner (`round_corner`), laid after the street
        front: a quarter round of the radius from the front's tangent to the side wall's,
        coursed on the front's own beds (its base, coping, belts and walling, rock-faced as
        the front is), up to the bed of the front's last course; over that, one course high,
        a dressed corbel rising from the round to the square, so the last course, the
        cornice, the eave and the gable end stand on the square corner as they did. The
        walls it replaces are cut away to that course's top (`build`)."""
        p, k = self.p, self.p.stone
        rc = k01_frontage_params.round_corner_spans(p.round_corner, p.depth_m, p.width_m)
        rad = p.round_corner["radius_m"]
        cu, cv = rc["centre"]
        C = (cu, -cv)
        a_lo = 0.0 if p.round_corner["corner"] == "north" else -math.pi / 2
        arc = rad * math.pi / 2
        conf = p.worst_conf("footprint", "stories", "storey_heights_m", "construction", "stone_front", "round_corner")
        wk, tk = k["wall"], k["trim_edges"]
        courses, ytop = self.front_courses, self.front_ytop
        y_sq = courses[-1][0]
        cid = "k01.wall.round_corner"
        self.instance(cid, "wall", {"length_m": arc, "height_m": ytop, "thickness_m": thickness,
                                    "construction": "masonry", "openings": 0, "radius_m": rad,
                                    "corner": p.round_corner["corner"], "fabric": k["fabric"],
                                    "dressing": k["dressing"]},
                      {"base": (cu + rad * math.cos(a_lo + math.pi / 4), 0.0, -(cv + rad * math.sin(a_lo + math.pi / 4))),
                       "top": (cu + rad * math.cos(a_lo + math.pi / 4), ytop, -(cv + rad * math.sin(a_lo + math.pi / 4)))})
        inst = len(self.components[cid]["instances"]) - 1
        rng = random.Random(seed_of(self.sid, cid, inst))
        af = p.arched_front
        # T-2991: the porch's arcade round the curve takes its lights' courses over the stretch it
        # stands on, from the springing's bed to the first bed over its crowns
        ra = ((p.entrance_kit or {}).get("loggia") or {}).get("round_arcade")
        band = self.round_arcade_band(ra, rad, arc, courses) if ra else None
        prev, j = (), 0
        for ya, yb, kind in courses:
            if ya >= y_sq - 1e-6:
                break
            trim = kind in ("coping", "belt", "band")
            spec = tk if trim else wk
            lo, hi = k["trim_block_m"] if trim else k["block_m"]
            r = k["channel_depth_m"] if kind == "base" else wk["recess_m"]
            jh = (k["channel_m"] if kind == "base" else spec["joint_m"]) / 2
            jv = spec["joint_m"] / 2
            if af and af["banded"] and kind in ("base", "walling"):
                jv = af["banded"]["vertical_joint_m"] / 2
            F = {"coping": k["coping_overhang_m"], "belt": 0.05}.get(kind, 0.0)
            pieces = _lay(rng, 0.0, arc, lo, max(lo, min(hi, 0.65 * arc)), None, prev)
            if band and band["y_lo"] - 1e-6 <= ya < band["y"][1] - 1e-6:
                f0, f1 = (band["s"][1], arc) if p.round_corner["corner"] == "north" else (0.0, band["s"][0])
                pieces = _lay(rng, f0, f1, lo, max(lo, min(hi, 0.65 * arc)), None, prev)
            prev = [s1 for _, s1 in pieces[:-1]]
            for s0, s1 in pieces:
                bseed = self._stone_seed(cid, inst, j)
                j += 1
                brng = random.Random(bseed ^ 0x5EED)
                rock = brng.uniform(*self._rock_range(ya, yb)) if not trim else 0.0
                self.round_stone(C, rad, a_lo + s0 / rad, a_lo + s1 / rad, ya, yb,
                                 (0.0 if ya <= 1e-9 else jh, jv, jh, jv),
                                 "limestone_trim" if trim else "rough_stone_trim", bseed, conf,
                                 recess=r, bevel=spec["bevel_m"], F=F, rock=rock)
        if band:
            self.round_arcade(ra, band, C, rad, a_lo, conf, cid, inst, j)
        # the corbel: ruled from the round at y_sq out to the square corner at ytop
        steps = 12
        phis = [a_lo + (math.pi / 2) * i / steps for i in range(steps + 1)]
        pr, seed = self.prim("limestone_trim"), self._stone_seed(cid, inst, j)
        b = self.basis("limestone_trim", (cu, y_sq, -cv), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), seed)
        ring = [(cu + rad * math.cos(f), y_sq, -(cv + rad * math.sin(f))) for f in phis]
        sq = [(cu + rad / max(abs(math.cos(f)), abs(math.sin(f))) * math.cos(f), ytop,
               -(cv + rad / max(abs(math.cos(f)), abs(math.sin(f))) * math.sin(f))) for f in phis]
        for i in range(steps):
            fm = (phis[i] + phis[i + 1]) / 2
            pr.quad(ring[i], ring[i + 1], sq[i + 1], sq[i], (math.cos(fm), -1.0, -math.sin(fm)), b, conf)

    # -- k01.wall.round_arcade (T-2991) -------------------------------------------------
    def round_arcade_band(self, ra, rad, arc, courses) -> dict:
        """T-2991: where the arcade's lights stand on the round: each light's centre `s` round the
        curve (s from the round's start, a_lo), the dressed band they are cut in, from the round's
        tangent with the front to `ROUND_ARCADE_MARGIN_M` past the last light, and from the
        springing's bed (the lights' sill) to the first bed clear of the crowns."""
        north = self.p.round_corner["corner"] == "north"
        sc = [rad * math.radians(t) if north else arc - rad * math.radians(t) for t in ra["angles_deg"]]
        beds = [ya for ya, _, _ in courses]
        y0 = ra["sill_m"]
        if not any(abs(b - y0) < 1e-6 for b in beds):
            raise ValueError(f"round_arcade: the lights' sill ({y0} m, the mouth's springing) is not a bed of the "
                             f"front's courses ({[round(b, 3) for b in beds]})")
        top = y0 + ra["crown_m"] + 0.08
        y1 = next((ya for ya, _, _ in courses if ya >= top - 1e-6), None)
        if y1 is None or y1 > self.front_courses[-1][0] + 1e-6:
            raise ValueError(f"round_arcade: no bed of the round clears the lights' crowns ({top:.3f} m) under "
                             f"its corbel")
        # T-3129: a light stepped down (`drops_m`) takes its stone down to the first bed under its sill
        drops = ra.get("drops_m") or [0.0] * len(sc)
        lo = y0 - max(drops)
        y_lo = max((ya for ya, _, _ in courses if ya <= lo + 1e-6), default=None)
        if y_lo is None:
            raise ValueError(f"round_arcade: no bed of the round stands under the lowest light's sill ({lo:.3f} m)")
        m = ra["clear_width_m"] / 2 + k01_frontage_params.ROUND_ARCADE_MARGIN_M
        s = (0.0, max(sc) + m) if north else (min(sc) - m, arc)
        order = sorted(range(len(sc)), key=lambda i: sc[i])
        cuts = [s[0]] + [(a + b) / 2 for a, b in zip(sorted(sc), sorted(sc)[1:])] + [s[1]]
        return {"s": s, "y": (y0, y1), "y_lo": y_lo, "lights": sorted(sc), "cuts": cuts,
                "drops": [drops[i] for i in order]}

    def round_arcade(self, ra, band, C, rad, a_lo, conf, cid, inst, j):
        """T-2991: 1811's porch arcade round its rounded corner (the Inland Architect plate of
        1888): the band of the lights' courses in dressed stones, one a light, each cut through by
        a round-headed light `reveal_m` deep into the porch's shadow; under each light a colonnette
        as the mouth's columns stand (a square base, a shaft, a necking ring, a flared bell and an
        abacus whose top is the light's sill), on a dressed plinth band carried round the curve
        from the mouth's plinth. The plate's capitals are carved leafage finer than its 2.3 cm a
        pixel and the porch behind the lights is dark; what stands for both is reconstructed
        (docs/LIBERTIES.md L-k01-1811-round-arcade-2991)."""
        AF = k01_arched_front
        p, k = self.p, self.p.stone
        cl = p.entrance_kit["loggia"]["columns"]
        wk = k["wall"]
        y0, y1 = band["y"]
        yl, drops = band["y_lo"], band["drops"]
        w, crown, rev = ra["clear_width_m"], ra["crown_m"], ra["reveal_m"]
        hw = w / 2
        rs, pr = cl["radius_m"], cl["proud_m"]
        ph, bh, ch = cl["plinth_m"], cl["base_m"], cl["capital_m"]
        yp = ra["floor_m"] + ph
        ang = lambda s_: a_lo + s_ / rad
        P = lambda a, y, d: (C[0] + (rad + d) * math.cos(a), y, C[1] - (rad + d) * math.sin(a))
        radial = lambda a: (math.cos(a), 0.0, -math.sin(a))
        tangent = lambda a: (-math.sin(a), 0.0, -math.cos(a))
        seed = self.instance("k01.wall.round_arcade", "wall",
                             {"of": "k01.wall.round_corner", "lights": len(band["lights"]), "clear_width_m": w,
                              "sill_m": round(y0, 4), "crown_m": round(y0 + crown, 4), "reveal_m": rev,
                              "angles_deg": ra["angles_deg"], "colonnette_radius_m": rs,
                              "plinth_top_m": round(yp, 4), "band_m": ra["band_m"],
                              "carving": "a necking ring, a flared bell and an abacus standing for the plate's leafage",
                              **({"drops_m": drops} if any(drops) else {})},
                             {"sill": P(ang(band["lights"][0]), y0, 0.0)})
        # the lights' stones: each from cut to cut, the band's two courses high, its face on the
        # round, dressed, with the light's round-headed hole through it
        jh, jv = wk["joint_m"] / 2, wk["joint_m"] / 2
        recess = wk["recess_m"]
        steps = 8   # the head's semicircle
        for i, sl in enumerate(band["lights"]):
            s0, s1 = band["cuts"][i] + (0.0 if i == 0 else jv), band["cuts"][i + 1] - jv
            sill = y0 - drops[i]           # T-3129: the light stepped down with its colonnette
            spring = sill + crown - hw
            bseed = self._stone_seed(cid, inst, j + i)
            a0 = ang(s0)
            origin, bed, mirror = P(a0, y0, 0.0), tangent(ang((s0 + s1) / 2)), bool(bseed >> 31)

            def face(pts, hint, mat="rough_stone_trim"):
                self._sface(mat, pts, hint, origin, bed, bseed, mirror, conf)
            head = lambda x: spring + math.sqrt(max(0.0, hw * hw - x * x))
            xs = sorted({s0, s1, sl - hw, sl + hw, *[sl - hw + w * q / steps for q in range(1, steps)],
                         *[s0 + (s1 - s0) * q / 6 for q in range(1, 6)]})
            g0, g1 = yl + jh, y1 - jh
            for xa, xb in zip(xs, xs[1:]):
                am = ang((xa + xb) / 2)
                inside = sl - hw - 1e-9 <= xa and xb <= sl + hw + 1e-9
                lo_a, lo_b = (head(xa - sl), head(xb - sl)) if inside else (g0, g0)
                face([P(ang(xa), lo_a, 0.0), P(ang(xb), lo_b, 0.0), P(ang(xb), g1, 0.0), P(ang(xa), g1, 0.0)],
                     radial(am))
                # the bed joints, over the stone and (beside the light) under it, back to the mortar
                face([P(ang(xa), g1, 0.0), P(ang(xb), g1, 0.0), P(ang(xb), g1, -recess), P(ang(xa), g1, -recess)],
                     Y)
                if not inside:
                    face([P(ang(xa), g0, 0.0), P(ang(xb), g0, 0.0), P(ang(xb), g0, -recess),
                          P(ang(xa), g0, -recess)], _mul(Y, -1))
                    self.prim("mortar").face([P(ang(xa), yl, -recess), P(ang(xb), yl, -recess),
                                              P(ang(xb), y1, -recess), P(ang(xa), y1, -recess)], radial(am),
                                             self.basis("mortar", origin, bed, Y, bseed), conf)
                else:
                    if sill > g0 + 1e-6:   # the stone under a light whose sill stands over the band's foot
                        face([P(ang(xa), g0, 0.0), P(ang(xb), g0, 0.0), P(ang(xb), sill, 0.0), P(ang(xa), sill, 0.0)],
                             radial(am))
                        face([P(ang(xa), g0, 0.0), P(ang(xb), g0, 0.0), P(ang(xb), g0, -recess),
                              P(ang(xa), g0, -recess)], _mul(Y, -1))
                        self.prim("mortar").face([P(ang(xa), yl, -recess), P(ang(xb), yl, -recess),
                                                  P(ang(xb), sill, -recess), P(ang(xa), sill, -recess)], radial(am),
                                                 self.basis("mortar", origin, bed, Y, bseed), conf)   # the light: its head's soffit, its sill and its back in the porch's shadow
                    face([P(ang(xa), lo_a, 0.0), P(ang(xb), lo_b, 0.0), P(ang(xb), lo_b, -rev),
                          P(ang(xa), lo_a, -rev)], (0.0, -1.0, 0.0))
                    face([P(ang(xa), sill, 0.0), P(ang(xb), sill, 0.0), P(ang(xb), sill, -rev), P(ang(xa), sill, -rev)],
                         (0.0, 1.0, 0.0))
                    self.prim("backing").face([P(ang(xa), sill, -rev), P(ang(xb), sill, -rev),
                                               P(ang(xb), lo_b, -rev), P(ang(xa), lo_a, -rev)], radial(am),
                                              self.basis("backing", origin, bed, Y, bseed), conf)
                    self.prim("mortar").face([P(ang(xa), lo_a, -recess), P(ang(xb), lo_b, -recess),
                                              P(ang(xb), y1, -recess), P(ang(xa), y1, -recess)], radial(am),
                                             self.basis("mortar", origin, bed, Y, bseed), conf)
            for x, sg in ((s0, -1.0), (s1, 1.0)):   # the stone's two ends, back to the mortar
                face([P(ang(x), g0, 0.0), P(ang(x), g1, 0.0), P(ang(x), g1, -recess), P(ang(x), g0, -recess)],
                     _mul(tangent(ang(x)), sg))
            for x, sg in ((sl - hw, 1.0), (sl + hw, -1.0)):   # the light's jambs, sill to spring
                face([P(ang(x), sill, 0.0), P(ang(x), spring, 0.0), P(ang(x), spring, -rev), P(ang(x), sill, -rev)],
                     _mul(tangent(ang(x)), sg))
        # the plinth band: the mouth's plinth carried round under the colonnettes, its face as
        # proud of the round as the plinth's is of the front, `band_m` deep under its top
        bw, aw = rs + 0.03, rs * 1.55
        out = pr + bw + 0.04
        pseed = self._stone_seed(cid, inst, j + len(band["lights"]))
        if not any(drops):
            self.round_stone(C, rad, ang(band["s"][0]), ang(band["s"][1]), yp - ra["band_m"], yp, (0.0, 0.0, 0.0, 0.0),
                             "dress_stone", pseed, conf, recess=0.02, bevel=0.0, F=out)
        else:   # T-3129: stepped down under each colonnette, as the plate and the photograph step it
            for i, dr in enumerate(drops):
                self.round_stone(C, rad, ang(band["cuts"][i]), ang(band["cuts"][i + 1]), yp - dr - ra["band_m"],
                                 yp - dr, (0.0, 0.0, 0.0, 0.0), "dress_stone", pseed + i, conf, recess=0.02,
                                 bevel=0.0, F=out)
        # the colonnettes, each in the frame of the round at its own angle: +R along the curve,
        # +N out of it; each abacus kept clear of its neighbours'
        ss = band["lights"]
        for i, sl in enumerate(ss):
            a = ang(sl)
            frame = (P(a, 0.0, 0.0), tangent(a), radial(a))
            room = min([abs(sl - x) for x in ss if x != sl] or [2 * aw]) / 2 - 0.005
            awi = min(aw, room)
            ypi, sill = yp - drops[i], y0 - drops[i]
            yb, yc = ypi + bh, sill - ch
            AF._box(self, "dress_stone", frame, -bw, bw, ypi, yb, pr - bw, pr + bw, seed, conf, skip=("bottom",))
            AF._frustum(self, "dress_stone", frame, 0.0, pr, yb, yc, rs, rs * 0.92, seed, conf)
            AF._frustum(self, "dress_stone", frame, 0.0, pr, yc, yc + 0.04, rs * 1.08, rs * 1.08, seed, conf)
            AF._frustum(self, "dress_stone", frame, 0.0, pr, yc + 0.04, sill - 0.06, rs * 0.92, awi, seed, conf)
            AF._box(self, "dress_stone", frame, -awi, awi, sill - 0.06, sill, pr - awi, pr + awi, seed, conf)

    def kit_variant(self, op) -> dict:
        from . import k06_windows
        if not hasattr(self, "_kit"):
            self._kit = k06_windows.load()
        entry = self.p.window_kit[op.component]
        v = dict(next(x for x in self._kit["variants"] if x["id"] == entry["variant"]))
        v["clear_width_m"], v["clear_height_m"] = op.width_m, op.height_m
        if getattr(op, "rise_over_span", 0.0):   # T-2960: the sash to the hole's own segmental rise
            v["rise_over_span"] = op.rise_over_span
        if getattr(op, "narrow", False):   # T-2884: a light under the ordinary sash's width is one light a sash
            v["panes"] = [1, 1]
        lt = k09_frontage.light(self.p, op)
        if lt and lt.get("tiers"):   # T-1890: its transom where its picture draws it (`street_front_trim.lights`)
            v["tiers"] = dict(lt["tiers"])
        if not entry["well"]:
            v["well"] = False
        return v

    def kit_reveal(self, op) -> float:
        self.kit_variant(op)
        v = next(x for x in self._kit["variants"] if x["id"] == self.p.window_kit[op.component]["variant"])
        return v.get("overrides", {}).get("reveal_depth_m", self._kit["parts"]["reveal_depth_m"]["value"])

    def glaze(self, op, frame, body_mat, stone_trim, seed, conf, skip=(), head=False, head_mat=None):
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
        g = self.p.window_kit.get(op.component, {}).get("grille")
        if g:   # T-3195: a basement light's bars, K08's grille in the K06 reveal
            from . import k08_bays
            k08_bays.grille(o, g)
            roles["iron"] = "iron"
        if head:   # T-2410: the kit's arch band is this head's hood
            roles["head"] = head_mat or stone_trim
        if o.v.get("tiers"):   # T-1890: a tier's bar is the wall's dressed stone, as K08's is the bay's
            roles["mullion"] = stone_trim
        self.graft(o, "K06", roles, frame, op, lambda role: (seed, conf), skip, head)

    def front_tympanum(self, op):
        """T-3197: the `street_front_trim.tympana` entry that dresses this street light, or None."""
        p = self.p
        if op.wall != "k01.wall.street_front" or op.component != "k01.opening.sash_flat":
            return None
        k = k09_frontage._storey(p, op)
        return next((e for e in (p.street_front_trim or {}).get("tympana", ())
                     if abs(e["s_m"] - op.s_m) < 1e-6 and k in e["storeys"]), None)

    def tympanum_head(self, op, frame, e, stone_trim, seed, conf):
        """T-3197: a light's head as 1827's window bay has it in the Doane photograph: a stone
        lintel `lintel_m` deep and `lintel_proud_m` out, reaching K01's 0.12 m past each jamb,
        and on it K08's carved tympanum (`k08_bays.tympanum`), laid as a kit is."""
        from . import k06_windows, k08_bays
        ext = 0.12
        a, b = -op.width_m / 2 - ext, op.width_m / 2 + ext
        self.proud_box(stone_trim, frame, op.s_m + a, op.s_m + b, op.head_m, op.head_m + e["lintel_m"],
                       e["lintel_proud_m"], seed, conf)
        self.seat(frame, [(op.s_m + a, op.head_m, 0.0), (op.s_m + b, op.head_m + e["lintel_m"], e["lintel_proud_m"])],
                  "K01.lintel")
        o = k06_windows.Opening({"id": f"{op.component}|tympanum"}, k06_windows.load())
        k08_bays.tympanum(o, e["tympanum"], a, b, op.height_m + e["lintel_m"], 0.0, "full")
        self.graft(o, "K08.tympanum", {"head": stone_trim, "carving": "carved_trim"}, frame, op,
                   lambda role: (seed, conf), head=True)

    def graft(self, o, kit, roles, frame, op, seed_conf, skip=(), head=False):
        """Carry a kit's built opening into this assembly. A kit's frame is +X along the
        wall, +Y up, +Z out of it, its origin at the opening's socket on the outer face (a
        K06 sill, a K07 threshold); `roles` maps each kit role to this assembly's material.
        The head band is left out: the K01 flat lintel (or a brick wall's own head)
        dresses every head — but a round-headed street window's (`head`, T-2410)."""
        O, R, N = frame
        base = _add(O, _add(_mul(R, op.s_m), _mul(Y, op.sill_m)))
        W = lambda q: _add(base, _add(_add(_mul(R, q[0]), _mul(Y, q[1])), _mul(N, q[2])))
        for role, src in o.prims.items():
            if (role == "head" and not head) or role in skip:   # `skip`: a role a solid already carries
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
        # T-3108: a bow on a chamfered pavilion's canted face: the cant is its wall, so its frame
        # is the cant's (R along it, N out of it) and its s_m is measured along the cant
        # T-1878: or a bay on a forward block's front, the same frame with no cant
        cant = b.get("on_chamfer") or b.get("on_face")
        s_at = b["s_m"]
        if cant:
            (ox, oz), (ex, ez), (nx, nz) = cant["origin"], cant["along"], cant["out"]
            O, R, N = (_add(O, _add(_mul(R, ox), _mul(N, oz))), _add(_mul(R, ex), _mul(N, ez)),
                       _add(_mul(R, nx), _mul(N, nz)))
            s_at = cant["s_m"]
        c = (v.get("masonry") or {}).get("coursing")
        if c and c["rhythm"] == "street_front":
            # T-2773: the bay's courses on the street front's own beds, as the 1888 plate
            # lays Keith's bow, its thin courses the front's (`_rock_range`'s line)
            lo_c, hi_c = p.stone["course_m"]
            v = {**v, "masonry": {**v["masonry"], "coursing": {**c, "beds_m": self.front_beds(),
                                                                "thin_below_m": (lo_c + hi_c) / 2}}}
        # T-3007: an oriel carried out over a rounded corner (1811's south return): its back is
        # closed on the wall plane over the round, from its support's foot to the round's top
        # (where the round's corbel has squared it out), since the curve falls away behind it
        g = (k01_frontage_params.round_corner_gap(p.round_corner, p.depth_m, p.width_m, b)
             if p.round_corner and v["kind"] == "oriel" else None)
        if g is not None:
            # the round's top, as build() cuts the front for it (`y_round`)
            y_round = p.arched_front["stone_top_m"] if p.arched_front else self.soffit_m
            v = {**v, "back_over": {"x": [g[0] - b["s_m"], g[1] - b["s_m"]],
                                    "y": [K8.support_bottom(v), y_round]}}
        built = K8.Bay(v, K8.load(), "full").build(board=False)
        if b.get("cut_by_entrance"):
            self.cut_by_entrance(b, built)
        conf = p.conf("bays")
        lo_, hi_ = k01_frontage_params._bay_span(v["plan"])
        seed = self.instance(f"k08.{v['kind']}", "bay",
                             {"k08_variant": b["id"], "plan": v["plan"]["kind"], "storeys": len(v["storeys"]),
                              "wall_top_m": built.meta["wall_top_m"], "projection_m": built.meta["plan"]["projection_m"],
                              "windows": len(built.windows), "wall": b["wall"],
                              **({"on_chamfer": cant["host"]} if b.get("on_chamfer") else {}),
                              **({"on_front": cant["host"]} if b.get("on_face") else {})},
                             {"junction_left": _add(O, _mul(R, s_at + lo_ if cant else b["span_m"][0])),
                              "junction_right": _add(O, _mul(R, s_at + hi_ if cant else b["span_m"][1]))})
        base = _add(O, _mul(R, s_at))
        W = lambda q: _add(base, _add(_add(_mul(R, q[0]), _mul(Y, q[1])), _mul(N, q[2])))
        body = {"brick": "bay_brick", "frame": "bay_frame"}.get(b["fabric"], "bay_stone")
        roles = K08_ROLES | (K08_FRAME_ROLES if b["fabric"] == "frame" else {})
        if b["fabric"] == "frame" and self.p.stone.get("all_round"):
            roles = roles | {"plinth": "bay_stone"}   # T-2788: the house's stone carried out under it
        cover = K08_COVERS[v["roof"]["covering"]]
        if b.get("finial_fabric"):   # T-1890: a finial in a sheet metal of its own, not the cap's slate
            roles = roles | {"finial": k01_frontage_params.FINIAL_FABRICS[b["finial_fabric"]]}
        for role, src in built.prims.items():
            if role not in roles:
                raise ValueError(f"K08 role {role!r} has no material on a K01 frontage")
            mat = {"body": body, "cover": cover}.get(roles[role], roles[role])
            tris = range(0, len(src.idx), 3)
            parts = [(mat, tris, range(len(src.pos)))]
            if role == "wall" and b.get("brick_above_m") is not None:
                # T-2914: the bay's wall over its line is brick, each triangle by where its
                # middle stands (the line is a storey line, a vertex row of the kit's wall)
                ba = b["brick_above_m"]
                up = {t for t in tris if (src.pos[src.idx[t]][1] + src.pos[src.idx[t + 1]][1] + src.pos[src.idx[t + 2]][1]) / 3 > ba}
                parts = [(m_, ts, sorted({src.idx[t + i] for t in ts for i in range(3)}))
                         for m_, ts in ((mat, [t for t in tris if t not in up]),
                                        ("bay_brick", [t for t in tris if t in up])) if ts]
            for mat, tris, keep in parts:
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
                remap = {v_: k_ for k_, v_ in enumerate(keep)}
                for q, n, uv, w in ((src.pos[v_], src.nrm[v_], src.uv[v_], world[v_]) for v_ in keep):
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
                for t in tris:
                    i, j, k = src.idx[t:t + 3]
                    if min(math.dist(world[i], world[j]), math.dist(world[j], world[k]),
                           math.dist(world[i], world[k])) >= SLIVER_M:
                        dst.idx += [off + remap[i], off + remap[j], off + remap[k]]
        # T-2964: a mansard bay's iron cresting along its curb (1816's two crowns)
        mn = (built.meta.get("roof") or {}).get("mansard")
        if mn and (v["roof"].get("mansard") or {}).get("cresting"):
            self.bay_cresting(v, mn, W, R, N, conf)
        # T-2451: the strips down its corners, each a box proud of one run of the plan
        if b.get("strips"):
            pts = v["plan"]["points"]
            for j, q in enumerate(b["strips"]):
                (x0, z0), (x1, z1) = pts[q["run"]], pts[q["run"] + 1]
                L = math.hypot(x1 - x0, z1 - z0)
                tx, tz = (x1 - x0) / L, (z1 - z0) / L
                Rw = _add(_mul(R, tx), _mul(N, tz))
                Nw = _add(_mul(R, -tz), _mul(N, tx))     # the run's outward normal
                w = q["width_m"]
                spans = {"start": [(0.0, w)], "end": [(L - w, L)], "both": [(0.0, w), (L - w, L)]}[q["at"]]
                for s0, s1 in spans:
                    self.proud_box(STRIP_FABRICS[q["fabric"]], (W((x0, 0.0, z0)), Rw, Nw), s0, s1,
                                   q["from_m"], q["to_m"], q["proud_m"], seed + j, conf)
        # T-2781: its engaged columns, each a square base, a shaft and a square capital
        if b.get("columns"):
            self.bay_columns(b, v["plan"]["points"], W, R, N, body, seed, conf)
        # T-2887: its carved dress — bands, frieze ovals, the consoles' scrolls, shutters
        if b.get("dress"):
            # T-2915: a bay in the front's stone is dressed in the front's dressed trim, as
            # the front's own belts and surrounds are (1812's projection, its print's quoins)
            dmat = "limestone_trim" if b["fabric"] == "front_stone" else body
            self.bay_dress(b["dress"], v["plan"]["points"], W, R, N, dmat, seed, conf)
        # T-2787: a tower rises past the main eave, and the wall that closes its ring below
        # stops at the wall head. Above that its ring is closed where the wall's plane cuts
        # it, facing the roof behind: from the wall head to the tower's wall top across the
        # ring's junctions, and on to its eave across its eaves' (K08 closes its cap from
        # there). A millimetre behind the plane, so no face lies on the kit's cut ends
        # T-2843: a pavilion carried up past the main eave (1801's south pavilion and its flank
        # section, three storeys to 13.9 m against an 8.1 m cornice, in the Taylor photograph)
        # is closed the same way, and so is its hipped cap's end on the plane, which K08
        # leaves open on a projection (a projection's cap otherwise dies into the wall over it)
        past = v["kind"] == "projection" and built.meta["wall_top_m"] > p.eave_m + 1e-6
        # T-2900: a corner turret's eaves are its wing's and its cone is whole over the wing's
        # roof, so nothing of it stands over the wall head to close
        # T-3047: a shallow projection's window recesses run back through the wall plane: the
        # host's face is opened round each (the coursed front below its soffit, `bay_holes`, and
        # the back closed over its eave here), and its gable's parapet closes its own top
        shallow = bool(v.get("shallow"))
        if built.host_holes:
            self.bay_holes.setdefault(b["wall"], []).extend(
                (b["s_m"] + x0, b["s_m"] + x1, y0, y1) for x0, x1, y0, y1 in built.host_holes)
        # T-3176: a tower across its corner closes its own back on both planes (K08's _corner_back)
        if (v["kind"] == "tower" and not b.get("corner") and not b.get("across_corner")) or past:
            back = _mul(N, -1)
            wall_top, eave = built.meta["wall_top_m"], built.meta["eave_m"]
            pr = self.prim(body)
            bb = self.basis(body, O, R, Y, seed)
            snap = lambda x, y: tuple(round(c * 1000) / 1000 for c in W((x, y, -0.001)))
            # T-2842: on a rear wing's wall it is closed from the wing's wall top (`eave_m`)
            closes = [((b["span_m"][0] - b["s_m"], b["span_m"][1] - b["s_m"]), (b.get("eave_m", p.eave_m), wall_top))]
            ch = k01_frontage_params.chamfer_of(b)
            if ch is not None:   # T-3048: short of where a chamfer's face crosses the plane
                (x0, x1), ys = closes[0]
                closes = [((x0 + ch[3], x1) if ch[0] == "left" else (x0, x1 - ch[3]), ys)]
            # T-1890: a staged tower's ring is the stage's from its lowest corbel course up, wider
            # than the shaft's, so it is closed there across the stage's junctions
            sg = built.meta.get("stage")
            if sg is not None:
                (x0, x1), (y0, y1) = closes[0]
                y_c = max(y0, sg["bottom_m"])
                closes = [c for c in (((x0, x1), (y0, y_c)), (tuple(sg["junctions_x"]), (y_c, y1)))
                          if c[1][1] - c[1][0] > 1e-6]
            # T-3156: a pavilion under a raised crown has no soffit of its own: the crown's is over it
            if not shallow and "soffit" in built.prims:
                on = [q[0] for q in built.prims["soffit"].pos if abs(q[2]) < 1e-6]
                closes.append(((min(on), max(on)), (wall_top, eave)))
            for (x0, x1), (y0, y1) in closes:
                for (xa, xb), (ya, yb) in K8.host_cells((x0, x1), (y0, y1), built.host_holes):
                    pr.face([snap(x, y) for x, y in ((xa, ya), (xb, ya), (xb, yb), (xa, yb))], back, bb, conf)
            # T-3048: a shallow pavilion flush with a corner: over the eave the main roof is cut
            # away behind it as deep as its recesses reach (shallow_bay_cutters), and from its
            # side that cut showed as a slot through the roof; its side wall is carried back over
            # the slot, in the side wall's plane, from its cheek (a chamfer's back) to the cut's
            ch = k01_frontage_params.chamfer_of(b)
            if shallow and b.get("flush_corner"):
                right = b["flush_corner"] == "right"
                xs = (b["span_m"][1] if right else b["span_m"][0]) - b["s_m"]
                proud = max(float(q[1]) for q in v["plan"]["points"])
                deep = -(K8.part(v, K8.load(), "recess")["depth_m"] - proud + 0.05)
                zc = -ch[2] if ch is not None else 0.0
                y0, y1 = b.get("eave_m", p.eave_m), wall_top
                pr.face([W((xs, y0, deep)), W((xs, y0, zc)), W((xs, y1, zc)), W((xs, y1, deep))],
                        R if right else _mul(R, -1), self.basis(body, W((xs, y0, deep)), N, Y, seed), conf)
            if past and not shallow:
                cap = sorted({(round(q[0], 6), round(q[1], 6)) for q in built.prims["roof"].pos
                              if abs(q[2]) < 1e-6})
                pr.face([snap(x, y) for x, y in cap], back, bb, conf)
        # T-2289: everything the bay stands against its wall with, junctions to roof
        # T-3101: a CANTED cheek leaves the wall further along than the bay's cornice and deck
        # reach over it, so one box round the whole bay took the front's coursing off the wall
        # the cheek leaves bare under them (1811's north pier, rock-faced on its plate and its
        # photographs, built as plain trim); such a bay seats its walls, up to their top, apart
        # from the cornice and deck over them
        pts = [q for pr in built.prims.values() for q in pr.pos]
        parts = [pts]
        # T-3236: and so does a bay set `seat_walls` (1812's projection: its cornice's 0.2 m over
        # the porch arch's south pier dressed that pier's stones smooth from the floor up, where the
        # north pier is rock-faced like the rest of the front)
        if b.get("canted") or b.get("seat_walls"):
            wt = built.meta["wall_top_m"]
            low = [q for q in pts if q[1] < wt - 0.01 and q[2] < 0.02]
            parts = [low + [(min(q[0] for q in low), wt, 0.0)], [q for q in pts if q[1] >= wt - 0.01]]
        for part in parts if not cant else ():   # T-3108: the chamfer cut the front's courses there
            self.seat(frame, [(b["s_m"] + q[0], q[1], 0.0 if q[2] < 0.02 else -1.0) for q in part], "k08")
        roof = built.prims.get("roof")
        on_wall = [q[1] for q in roof.pos if abs(q[2]) < 1e-6] if roof else []
        top = max(on_wall) if on_wall else built.meta["eave_m"]
        xs = [q[0] for pr in built.prims.values() for q in pr.pos]
        if cant:   # T-3108: on its host wall it reaches over the cant's span
            return top, tuple(b["span_m"])
        return top, (b["s_m"] + min(xs), b["s_m"] + max(xs))

    def cut_by_entrance(self, b, built):
        """T-3135: the porch arch cut into a projection's corner (1812's: the Levy print and the
        c. 1955 photograph draw its south jamb and moulding on the projection's own face). In
        the bay's frame, everything the kit built under the arch's head from the door's floor,
        between the jamb inside the projection and its cheek, is cut away through its whole
        depth, and the cut is closed in the bay's stone: the jamb carried forward from the
        door's reveal, the head's soffit on the reveal's own polyline (k06_windows.Head, the
        hole K07 cuts), and the floor at the door's."""
        from . import k06_windows
        cut = entrance_cut(self.p)
        if cut is None or cut["bay"] is not b:
            raise ValueError(f"{b['id']} is cut_by_entrance and the entrance's mouth does not reach it")
        g, side, proud = cut["group"], cut["side"], cut["proud_m"]
        (s0, s1, spring, rise, floor), = g["lights"]
        kind = "elliptical" if g.get("elliptical") else "segmental" if g.get("segmental") else "round"
        head = k06_windows.Head(kind, s0, s1, spring, rise / (s1 - s0)).curve(0.0, s1, s0)[::-1]
        k = 1.0 if side == "left" else -1.0       # x measured into the mouth from the jamb
        jamb = (s0 if side == "left" else s1) - b["s_m"]
        edge = (b["span_m"][1] if side == "left" else b["span_m"][0]) - b["s_m"]
        arc = [(x - b["s_m"], y) for x, y in head]
        if side == "right":
            arc = arc[::-1]
        # the region cut, a convex prism: past the jamb, over the floor, under every chord
        # of the head, from behind the wall's plane to past the bay's face and cheek
        X = lambda x: k * (x - jamb)               # 0 at the jamb, rising into the mouth
        hs = [((-k, 0.0, 0.0), -k * jamb), ((k, 0.0, 0.0), k * edge + 0.3),
              ((0.0, -1.0, 0.0), -floor), ((0.0, 0.0, -1.0), 0.01), ((0.0, 0.0, 1.0), proud + 0.3)]
        for (xa, ya), (xb, yb) in zip(arc, arc[1:]):
            if X(xa) > X(edge) + 0.3:
                break
            # under the chord: the line's upward normal, (-(yb - ya), xb - xa) turned to +y
            nx, ny = -(yb - ya), (xb - xa)
            if ny < 0:
                nx, ny = -nx, -ny
            hs.append(((nx, ny, 0.0), nx * xa + ny * ya))
        for role, src in built.prims.items():
            built.prims[role] = _cut_convex(src, hs)
        # the cut's own faces, in the bay's stone (K08's `reveal`, never its brick `wall`)
        pr = built.prims.setdefault("reveal", Prim("reveal"))
        on = [(x, y) for x, y in arc if X(x) < X(edge) - 1e-6]
        (xa, ya), (xb, yb) = next(((a_, b_) for a_, b_ in zip(arc, arc[1:]) if X(b_[0]) >= X(edge) - 1e-6))
        t = (X(edge) - X(xa)) / (X(xb) - X(xa))
        on.append((edge, ya + (yb - ya) * t))
        basis = lambda o, au, av: (o, au, av, 1.0, 1.0, 0.0, 0.0)
        sx = (k, 0.0, 0.0)
        pr.face([(jamb, floor, 0.0), (jamb, on[0][1], 0.0), (jamb, on[0][1], proud), (jamb, floor, proud)],
                sx, basis((jamb, floor, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)), None)
        for (xa, ya), (xb, yb) in zip(on, on[1:]):
            n = _unit((yb - ya, -(xb - xa), 0.0))
            if n[1] > 0:
                n = _mul(n, -1)
            L = math.hypot(xb - xa, yb - ya)
            pr.face([(xa, ya, 0.0), (xb, yb, 0.0), (xb, yb, proud), (xa, ya, proud)], n,
                    basis((xa, ya, 0.0), ((xb - xa) / L, (yb - ya) / L, 0.0), (0.0, 0.0, 1.0)), None)
        pr.face([(jamb, floor, 0.0), (edge, floor, 0.0), (edge, floor, proud), (jamb, floor, proud)], Y,
                basis((jamb, floor, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), None)

    def bay_cresting(self, v, mn, W, R, N, conf):
        """T-2964: K10's iron cresting (`k10.cresting.iron_ridge`, as 1801's deck carries it,
        k01_mansard_deck) along each run of a K08 mansard bay's curb, `inset_m` onto its deck
        and stretched to `height_m`, stopped `CREST_STOP_M` short of every corner and of the
        wall plane behind. Each run is built along X about the origin and turned onto the run
        in the bay's frame (X along it, Z its inward normal's opposite), which W carries home."""
        from . import k10_frontage
        from .k01_mansard_deck import _stretch
        cr = v["roof"]["mansard"]["cresting"]
        h, ins = float(cr["height_m"]), float(cr["inset_m"])
        if not 0.3 <= h <= 1.0 or not 0.03 <= ins <= 0.3:
            raise ValueError(f"{v['id']}: a mansard bay's cresting stands 0.3-1.0 m high, 0.03-0.3 m inside its curb")
        K = k10_frontage._kit()
        data = K.load()
        crest = next(x for x in data["variants"] if x["id"] == "k10.cresting.iron_ridge")
        y_cap = mn["curb_m"] + float(v["roof"]["pitch"]) * ins
        pts = mn["curb"]
        laid = []
        for j in range(len(pts) - 1):
            (x0, z0), (x1, z1) = pts[j], pts[j + 1]
            L0 = math.hypot(x1 - x0, z1 - z0)
            tx, tz = (x1 - x0) / L0, (z1 - z0) / L0
            kx, kz = -tz, tx          # local +Z, the run's outward side (the curb runs left to right)
            L = L0 - 2 * CREST_STOP_M
            if L < k10_frontage.MIN_CRESTING_M:
                continue
            mx, mz = (x0 + x1) / 2 - kx * ins, (z0 + z1) / 2 - kz * ins
            seed = self.instance("k10.cresting.iron_ridge", "cresting",
                                 {"length_m": round(L, 4), "ridge_cap_top_m": round(y_cap, 4), "height_m": h,
                                  "host": f"bay {v['id']} curb", "run": j}, {"ridge": W((mx, y_cap, mz))})
            var = K.Variant(dict(crest), data)
            var.seed, var.rng = seed, random.Random(seed)
            var.cresting(0.0, L, y_cap, 0.0, host=f"bay {v['id']} curb")
            top = max(q[1] for pc in var.pieces for q in pc.mesh.pos)
            _stretch(var.pieces, y_cap - 0.007, h / (top - (y_cap - 0.007)))
            for pc in var.pieces:
                m = pc.mesh
                m.pos = [W((mx + q[0] * tx + q[2] * kx, q[1], mz + q[0] * tz + q[2] * kz)) for q in m.pos]
                m.nrm = [_add(_add(_mul(R, n[0] * tx + n[2] * kx), _mul(Y, n[1])), _mul(N, n[0] * tz + n[2] * kz))
                         for n in m.nrm]
            k10_frontage._lay(self, var.pieces, conf, "k10.cresting.iron_ridge")
            laid.append({"run": j, "length_m": round(L, 3)})
        self.bay_crests = getattr(self, "bay_crests", []) + [{"bay": v["id"], "runs": laid}]

    def bay_columns(self, b, pts, W, R, N, mat, seed, conf):
        """T-2781: a stone bay's engaged columns (1637's south bay, the Grosvenor photograph).
        Each stands on its run's face `s_m` along it, or on a corner's bisector at a run's end,
        its axis a quarter of its diameter out, so three quarters of the shaft stand clear of
        the wall: a square base, a round shaft and a square capital twice the base's spread,
        each turned to its run."""
        c = b["columns"]
        r = c["diameter_m"] / 2
        y0, y1, hb, hc = c["from_m"], c["to_m"], c["base_m"], c["capital_m"]
        runs = []
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, z1 - z0)
            runs.append(((x0, z0), ((x1 - x0) / L, (z1 - z0) / L), L))
        for j, q in enumerate(c["at"]):
            (x0, z0), (tx, tz), L = runs[q["run"]]
            nx, nz = tz, -tx      # out of the bay: the plan runs left to right seen from outside
            if nx * (x0 - (pts[0][0] + pts[-1][0]) / 2) + nz * z0 < 0:
                nx, nz = -nx, -nz
            nb = None
            if q["s_m"] < 1e-3 and q["run"] > 0:
                nb = runs[q["run"] - 1][1]
            elif q["s_m"] > L - 1e-3 and q["run"] < len(runs) - 1:
                nb = runs[q["run"] + 1][1]
            if nb is not None:    # a corner: out along the bisector of the two runs' normals
                mx, mz = nb[1], -nb[0]
                if mx * nx + mz * nz < 0:
                    mx, mz = -mx, -mz
                nx, nz = nx + mx, nz + mz
                k = math.hypot(nx, nz)
                nx, nz = nx / k, nz / k
            ax = (x0 + tx * q["s_m"] + nx * r / 2, z0 + tz * q["s_m"] + nz * r / 2)
            Rw = _add(_mul(R, tx), _mul(N, tz))
            Nw = _add(_mul(R, nx), _mul(N, nz))
            carved = (b.get("dress") or {}).get("capitals")
            blocks = ((r + 0.04, y0, y0 + hb),) + (((r + 0.08, y1 - carved["abacus_m"], y1),) if carved
                                                   else ((r + 0.08, y1 - hc, y1),))
            for (h, ya, yb) in blocks:
                self.column_block(mat, W((ax[0], 0.0, ax[1])), Rw, _cross(Rw, Y), h, ya, yb, seed + j, conf)
            if carved:   # T-2887: a bell of leaves under the abacus, each tier's crown scalloped
                ya, yb, k = y1 - hc, y1 - carved["abacus_m"], carved["tiers"]
                for t in range(k):
                    lo, hi = ya + (yb - ya) * t / k, ya + (yb - ya) * (t + 1) / k
                    self.bell("carved_trim", W((ax[0], 0.0, ax[1])), Rw, _cross(Rw, Y), lo, hi,
                              r + 0.01 + 0.02 * t, r + 0.05 + 0.025 * t, seed + j, conf)
            foot, head = W((ax[0], y0 + hb, ax[1])), W((ax[0], y1 - hc, ax[1]))
            self.tube(mat, [foot, head], r, Rw, seed + j, conf, sides=12)

    def bell(self, mat, C, A, B, y0, y1, r0, r1, seed, conf, sides=16, scallop=0.22):
        """T-2887: a carved capital's tier of leaves about the vertical through C: a ring
        flaring from r0 at y0 to r1 at y1, its crown scalloped (every other point drawn in by
        `scallop` of r1), so the tier's top edge reads as leaf tips against the abacus."""
        pr = self.prim(mat)
        ring = lambda r, y, sc: [_add(_add((C[0], y, C[2]), _mul(A, math.cos(2 * math.pi * j / sides) * r
                                                                  * (1 - sc * (j % 2)))),
                                      _mul(B, math.sin(2 * math.pi * j / sides) * r * (1 - sc * (j % 2))))
                                 for j in range(sides)]
        lo, hi = ring(r0, y0, 0.0), ring(r1, y1, scallop)
        for j in range(sides):
            a, b_, c, d = lo[j], lo[(j + 1) % sides], hi[(j + 1) % sides], hi[j]
            mid = _sub(_mul(_add(a, c), 0.5), (C[0], (y0 + y1) / 2, C[2]))
            pr.quad(a, b_, c, d, mid, self.basis(mat, a, _unit(_sub(b_, a)), Y, seed), conf)

    def drum(self, mat, C, axis, ref, rad, half, seed, conf, sides=12):
        """T-2887: a closed cylinder about C along `axis`, `half` either way, `ref` one of its
        radial directions: a console's scroll seen end on."""
        pr = self.prim(mat)
        e2 = _unit(_cross(axis, ref))
        rings = [[_add(_add(C, _mul(axis, k * half)), _add(_mul(ref, math.cos(2 * math.pi * j / sides) * rad),
                                                             _mul(e2, math.sin(2 * math.pi * j / sides) * rad)))
                  for j in range(sides)] for k in (-1, 1)]
        for j in range(sides):
            a, b_ = rings[0][j], rings[0][(j + 1) % sides]
            mid = _sub(_mul(_add(a, b_), 0.5), _add(C, _mul(axis, -half)))
            pr.quad(a, b_, rings[1][(j + 1) % sides], rings[1][j], mid,
                    self.basis(mat, a, _unit(_sub(b_, a)), axis, seed), conf)
        for k, ring in ((-1, rings[0]), (1, rings[1])):
            pr.face(ring, _mul(axis, k), self.basis(mat, ring[0], ref, e2, seed), conf)

    def bay_dress(self, d, pts, W, R, N, mat, seed, conf):
        """T-2887: a stone bay's carved dress (1637's south bay, the Grosvenor photograph), on
        the bay's own plan: mitred bands proud of its faces (from `in_m` out to `proud_m`, so a
        band can stand on the eaves' fascia too), oval panels sunk in a moulded ring (dark, or a
        stone `field`, T-2909), a roll at each end of every corner console, and open louvred
        shutters either side of the window over it on the host wall."""
        V = lambda x, z: _add(_mul(R, x), _mul(N, z))     # a plan direction in the world
        runs = []
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, z1 - z0)
            tx, tz = (x1 - x0) / L, (z1 - z0) / L
            runs.append(((x0, z0), (tx, tz), (-tz, tx), L))   # out: left of the run seen from above
        def offset(dd):
            """The plan offset `dd` out, mitred at its corners, its ends on the host wall."""
            out = []
            for i, ((x0, z0), (tx, tz), (nx, nz), L) in enumerate(runs):
                if i == 0:
                    sa = -(z0 + nz * dd) / tz if abs(tz) > 1e-9 else 0.0
                    out.append((x0 + nx * dd + tx * sa, z0 + nz * dd + tz * sa))
                else:
                    (mx, mz) = runs[i - 1][2]
                    k = dd / (1.0 + mx * nx + mz * nz)
                    out.append((x0 + (mx + nx) * k, z0 + (mz + nz) * k))
            (x0, z0), (tx, tz), (nx, nz), L = runs[-1]
            x1, z1 = x0 + tx * L, z0 + tz * L
            sb = -(z1 + nz * dd) / tz if abs(tz) > 1e-9 else 0.0
            out.append((x1 + nx * dd + tx * sb, z1 + nz * dd + tz * sb))
            return out
        for q in d.get("bands", ()):
            y0, y1 = q["from_m"], q["to_m"]
            pi, po = offset(q["in_m"]), offset(q["proud_m"])
            pr = self.prim(mat)
            for i, (_, (tx, tz), (nx, nz), _L) in enumerate(runs):
                Rw, Nw = V(tx, tz), V(nx, nz)
                a, b_ = po[i], po[i + 1]
                f = [W((a[0], y0, a[1])), W((b_[0], y0, b_[1])), W((b_[0], y1, b_[1])), W((a[0], y1, a[1]))]
                pr.face(f, Nw, self.basis(mat, f[0], Rw, Y, seed), conf)
                for y, ny in ((y1, Y), (y0, _mul(Y, -1))):
                    h = [W((pi[i][0], y, pi[i][1])), W((pi[i + 1][0], y, pi[i + 1][1])),
                         W((b_[0], y, b_[1])), W((a[0], y, a[1]))]
                    pr.face(h, ny, self.basis(mat, h[0], Rw, Nw, seed), conf)
        for j, q in enumerate(d.get("ovals", ())):
            (x0, z0), (tx, tz), (nx, nz), _L = runs[q["run"]]
            Rw, Nw = V(tx, tz), V(nx, nz)
            C = W((x0 + tx * q["s_m"], q["y_m"], z0 + tz * q["s_m"]))
            a, b_, rim, n = q["width_m"] / 2, q["height_m"] / 2, 0.035, 20
            unit = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
            if q.get("shape") == "shield":
                unit = SHIELD_OUTLINE
                n = len(unit)
            E = lambda aa, bb, k, dd: _add(_add(C, _mul(Nw, dd)), _add(_mul(Rw, aa * unit[k % n][0]),
                                                                     _mul(Y, bb * unit[k % n][1])))
            pr, dark = self.prim(mat), self.prim("backing")
            sunk, dd = 0.015, q["proud_m"]
            boss = q.get("field") == "boss"      # T-2915: the field raised past the ring, a boss
            if boss:
                sunk = dd + 0.025
            for k in range(n):
                o0, o1 = E(a, b_, k, dd), E(a, b_, k + 1, dd)
                i0, i1 = E(a - rim, b_ - rim, k, dd), E(a - rim, b_ - rim, k + 1, dd)
                pr.face([o0, o1, i1, i0], Nw, self.basis(mat, o0, Rw, Y, seed + j), conf)
                f0, f1 = E(a, b_, k, 0.0), E(a, b_, k + 1, 0.0)
                pr.quad(f0, f1, o1, o0, _sub(_mul(_add(f0, o1), 0.5), C), self.basis(mat, f0, Nw, Y, seed + j), conf)
                s0, s1 = E(a - rim, b_ - rim, k, sunk), E(a - rim, b_ - rim, k + 1, sunk)
                inward = _sub(C, _mul(_add(s0, i1), 0.5))
                pr.quad(s0, s1, i1, i0, _mul(inward, -1) if boss else inward, self.basis(mat, s0, Nw, Y, seed + j), conf)
            disc = [E(a - rim, b_ - rim, k, sunk) for k in range(n)]
            if q.get("field") in ("stone", "boss"):   # T-2909: a sunk stone field, not a dark one
                pr.face(disc, Nw, self.basis(mat, disc[0], Rw, Y, seed + j), conf)
            else:
                dark.face(disc, Nw, self.basis("backing", disc[0], Rw, Y, seed + j), conf)
        # T-2915: a window's quoined jambs, each stone a box `returns_m` out from its jamb,
        # short and long in turn from the foot, a 10 mm joint between courses
        for j, q in enumerate(d.get("quoins", ())):
            (x0, z0), (tx, tz), (nx, nz), _L = runs[q["run"]]
            fr = (W((x0, 0.0, z0)), V(tx, tz), V(nx, nz))
            a, b_ = q["jambs_m"]
            h = (q["to_m"] - q["from_m"]) / q["courses"]
            for k in range(q["courses"]):
                ret = q["returns_m"][k % 2]
                ya, yb = q["from_m"] + k * h + 0.005, q["from_m"] + (k + 1) * h - 0.005
                self.proud_box(mat, fr, a - ret, a, ya, yb, q["proud_m"], seed + j, conf)
                self.proud_box(mat, fr, b_, b_ + ret, ya, yb, q["proud_m"], seed + j, conf)
        # T-2915: a band along one run, broken at its gaps (a window and its arch's ring)
        for j, q in enumerate(d.get("run_bands", ())):
            (x0, z0), (tx, tz), (nx, nz), L = runs[q["run"]]
            fr = (W((x0, 0.0, z0)), V(tx, tz), V(nx, nz))
            cuts = [0.0, *[x for g in q["gaps_m"] for x in g], L]
            for s0, s1 in zip(cuts[0::2], cuts[1::2]):
                if s1 - s0 > 1e-6:   # T-3135: a gap may run to the run's end (an arch cut into the corner)
                    self.proud_box(mat, fr, s0, s1, q["from_m"], q["to_m"], q["proud_m"], seed + j, conf)
        # T-3091: dressed blocks along one run (a pier, a hood, a cap under the cornice)
        for j, q in enumerate(d.get("blocks", ())):
            (x0, z0), (tx, tz), (nx, nz), L = runs[q["run"]]
            fr = (W((x0, 0.0, z0)), V(tx, tz), V(nx, nz))
            self.proud_box(mat, fr, q["s_m"][0], q["s_m"][1], q["from_m"], q["to_m"], q["proud_m"], seed + j, conf)
        vo = d.get("volutes")
        if vo:
            rv, Rc, D, t = vo["radius_m"], vo["reach_m"], vo["drop_m"], vo["thickness_m"] / 2 + 0.02
            top = d["soffit_m"]
            for i in range(1, len(runs)):
                (mx, mz), (nx, nz) = runs[i - 1][2], runs[i][2]
                bx, bz = mx + nx, mz + nz
                k = math.hypot(bx, bz)
                bx, bz = bx / k, bz / k
                (cx, cz) = runs[i][0]
                axis, out = V(-bz, bx), V(bx, bz)
                for r_, y_, rad in ((rv, top - D + rv, rv), (Rc - 0.7 * rv, top - 0.7 * rv, 0.7 * rv)):
                    self.drum("fascia", W((cx + bx * r_, y_, cz + bz * r_)), axis, out, rad, t, seed + i, conf)
        sh = d.get("shutters")
        if sh:
            frame = (W((0.0, 0.0, 0.0)), R, N)
            y0, y1, w, lv = sh["from_m"], sh["to_m"], sh["width_m"], sh["louvre_m"]
            c = sh.get("centre_m", 0.0)     # T-2909: the window's offset off the bay's centre
            for sg in (-1.0, 1.0):
                e0, e1 = c + sg * (sh["half_m"] + 0.03), c + sg * (sh["half_m"] + 0.03 + w)
                s0, s1 = min(e0, e1), max(e0, e1)
                self.proud_box("shutter", frame, s0, s1, y0, y1, 0.035, seed, conf)
                rows = int((y1 - y0 - 0.16) / lv)
                for k in range(rows):
                    ya = y0 + 0.08 + k * lv
                    self.proud_box("shutter", frame, s0 + 0.05, s1 - 0.05, ya, ya + lv * 0.5, 0.05, seed, conf)

    def window_shutters(self, frames):
        """T-1879: open louvred shutters folded back flat beside a wall's lights (1721's, the
        1891 plate), as T-2887's at a bay's window over: a pair of boards `width_m` wide,
        SHUTTER_GAP_M off each side of the light from its sill to its head, slats across them."""
        sh, conf = self.p.shutters, self.p.conf("window_shutters")
        w, lv, gap = sh["width_m"], sh["louvre_m"], k01_frontage_params.SHUTTER_GAP_M
        for cid, a, b, y0, y1 in sh["lights"]:
            seed = self.instance("k01.window.shutters", "shutters", {"width_m": w, "louvre_m": lv},
                                 {"sill": _add(frames[cid][0], _mul(frames[cid][1], (a + b) / 2))})
            for s0, s1 in ((a - gap - w, a - gap), (b + gap, b + gap + w)):
                self.proud_box("shutter", frames[cid], s0, s1, y0, y1, 0.035, seed, conf)
                for k in range(int((y1 - y0 - 0.16) / lv)):
                    ya = y0 + 0.08 + k * lv
                    self.proud_box("shutter", frames[cid], s0 + 0.05, s1 - 0.05, ya, ya + lv * 0.5, 0.05, seed, conf)

    def column_block(self, mat, C, A, B, h, y0, y1, seed, conf):
        """A square block about the vertical through C, `h` either side along A and B, from
        y0 to y1 over grade: its four faces and its top (its foot stands on a band)."""
        pr = self.prim(mat)
        P = lambda a, b_, y: _add(_add(_add((C[0], 0.0, C[2]), _mul(A, a)), _mul(B, b_)), (0.0, y, 0.0))
        for along, ax_ in ((True, A), (True, _mul(A, -1)), (False, B), (False, _mul(B, -1))):
            side_ = B if along else A
            e = _mul(side_, h)
            c0 = _add((C[0], 0.0, C[2]), _mul(ax_, h))
            pts = [_add(_sub(c0, e), (0.0, y0, 0.0)), _add(_add(c0, e), (0.0, y0, 0.0)),
                   _add(_add(c0, e), (0.0, y1, 0.0)), _add(_sub(c0, e), (0.0, y1, 0.0))]
            pr.face(pts, ax_, self.basis(mat, pts[0], side_, Y, seed), conf)
        top = [P(-h, -h, y1), P(h, -h, y1), P(h, h, y1), P(-h, h, y1)]
        pr.face(top, Y, self.basis(mat, top[0], A, B, seed), conf)

    # -- K07 entrance (T-2304) ------------------------------------------------------------
    # K07 role -> this assembly's material: the reveal in the front's own stone, the
    # threshold and every part of the stoop in the stoop stone, the frame, leaf and transom
    # sash in the door's joinery, the knob iron, the transom's glass and the dark hall
    # behind it the windows' own. A role not named here — a porch, an area wall, a guard
    # stone — is one this house's variant does not build, and is refused.
    K07_ROLES = {"reveal": None, "porch_back": None, "threshold": "stoop_stone", "landing": "stoop_stone",
                 "tread": "stoop_stone", "riser": "stoop_stone", "stair_end": "stoop_stone",
                 "cheek": "stoop_stone", "frame": "door_leaf", "leaf": "door_leaf",
                 # T-3134: a broad mouth's heavy transom beam, in the stoop's dressed stone
                 "transom_beam": "stoop_stone",
                 "sash_outer": "door_leaf", "glass_outer": "glass", "glass_leaf": "glass",
                 "hardware": "door_iron", "backing": "backing",
                 # T-2409: a terrace beside the landing and turned balustrades, in the stoop's stone
                 "terrace": "stoop_stone", "terrace_face": "stoop_stone", "baluster": "stoop_stone",
                 "newel": "stoop_stone", "rail": "stoop_stone",
                 # T-2500: a stone loggia on the terrace, its basement arch's void the hall's backing
                 "pedestal": "stoop_stone", "column": "stoop_stone", "entablature": "stoop_stone",
                 "loggia_wall": "stoop_stone", "balcony": "stoop_stone", "arch_reveal": "stoop_stone",
                 "arch_back": "backing",
                 # T-2933: a timber veranda's posts, beam and roof, painted with the walls (as a
                 # K08 frame bay's walls are the body's)
                 "post": None, "beam": None, "porch_roof": None,
                 # T-2960: and the skirt of a deck open beneath it, over the void's dark
                 "skirt": None,
                 # T-2961: and its roof's slopes in the house's roof covering
                 "porch_roof_top": "slate_covering"}
    STAIR_ROLES = frozenset({"landing", "tread", "riser", "stair_end", "cheek",
                             "terrace", "terrace_face", "baluster", "newel", "rail",
                             "pedestal", "column", "entablature", "loggia_wall", "balcony", "arch_reveal",
                             "post", "beam", "porch_roof", "skirt", "porch_roof_top"})

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
        # T-2952: a segmental porch arch, and a side light beside the door under its transom
        ros = (p.entrance_kit.get("arch") or {}).get("rise_over_span")
        if ros:   # T-3134: or a half ellipse (`arch.head`)
            v["head"], v["rise_over_span"] = (p.entrance_kit.get("arch") or {}).get("head", "segmental"), ros
        if p.entrance_kit.get("side_light"):
            v["side_light"] = p.entrance_kit["side_light"]
        # T-3134: the mouth's heavy transom beam and its fanlight's columns of small panes
        for k in ("transom_beam", "fanlight_columns"):
            if p.entrance_kit.get(k):
                v[k] = p.entrance_kit[k]
        # T-3236: the leaves' own panels, rails and raised fields
        lv = p.entrance_kit.get("leaf")
        if lv:
            v["panels"], v["rails_y_m"] = lv["panels"], lv["rails_y_m"]
            v["leaf"] = {k: lv[k] for k in ("panel_recess_m", "raised_field") if k in lv}
        # T-2817: a porch's door at the back of the arch, off its axis
        pd = p.entrance_kit.get("porch_door")
        if pd:
            v["porch_door"] = {"s_m": pd["offset_m"], **{k: x for k, x in pd.items() if k != "offset_m"}}
        v["stair"] = dict(v["stair"], floor_m=p.door_floor_m, going_m=p.tread_m,
                          landing_m=p.landing_depth_m, width_m=p.stoop_width_m)
        # T-3135: the door's end over the floor of a projection its arch is cut into
        cut = entrance_cut(p)
        if cut is not None:
            v["stair"]["carried"] = [cut["side"]]
        # T-2463: a stoop off its door's axis
        if p.stoop_s_m(door.s_m) != door.s_m:
            v["stair"]["axis_s_m"] = p.stoop_s_m(door.s_m) - door.s_m
        # T-2409: the terrace's reach and steps, from the front's s into the door's own frame
        # T-2450: a left terrace's s run from the door AWAY from the stoop (K07 mirrors it),
        # and where it passes the front's end K07 faces its back
        t = p.entrance_kit.get("terrace")
        porches = []
        for q in (t if isinstance(t, list) else [t] if t else []):
            k = 1.0 if q["side"] == "right" else -1.0
            end = p.width_m - door.s_m if k > 0 else door.s_m
            porches.append({"side": q["side"], "to_s_m": k * (q["to_v_m"] - door.s_m),
                            "back": [[k * (s - door.s_m), o] for s, o in q["back"]],
                            **({"wall_to_s_m": end} if k * (q["to_v_m"] - door.s_m) > end else {}),
                            # T-2500: a terrace deeper than the landing, and the loggia standing on it
                            **({"out_m": q["out_m"]} if "out_m" in q else {}),
                            **({"loggia": q["loggia"]} if "loggia" in q else {}),
                            **({"parapet": q["parapet"]} if "parapet" in q else {}),
                            **({"balustrade": p.entrance_kit["balustrade"]}
                               if p.entrance_kit.get("balustrade") else {})})
        if porches:
            v["stair"]["porch"] = porches[0] if len(porches) == 1 else porches
        if p.entrance_kit.get("balustrade"):
            v["stair"]["balustrade"] = p.entrance_kit["balustrade"]
        # T-2933: the veranda's posts from the front's v into the door's own frame
        if p.entrance_kit.get("veranda"):
            vr = p.entrance_kit["veranda"]
            v["stair"]["veranda"] = {**{k: x for k, x in vr.items() if k != "posts_v_m"},
                                     "posts_s_m": [x - door.s_m for x in vr["posts_v_m"]]}
        v["front_yard_m"] = p.entrance_kit["front_yard_m"]
        # T-2369: the record's own stoop ends (iron rails, no cheeks) and the door's depth
        if "cheeks" in p.entrance_kit:
            v["stair"]["cheeks"] = p.entrance_kit["cheeks"]
        if "reveal_depth_m" in p.entrance_kit:
            v["reveal_depth_m"] = p.entrance_kit["reveal_depth_m"]
        # T-2910: a loggia behind the arch, its door in the back wall, and a stoop's swept cheeks
        lg = p.entrance_kit.get("loggia")
        if lg:
            v["loggia"] = {k: x for k, x in lg.items() if k not in ("side_arch", "round_arcade")}
            sa = lg.get("side_arch")
            if sa:
                v["loggia"]["side_arch"] = {k: sa[k] for k in ("side", "centre_m", "clear_width_m", "clear_height_m",
                                                                "wall_m", "balcony") if k in sa}
            v["reveal_depth_m"] = lg["depth_m"]
        if p.entrance_kit.get("cheek_form"):
            cf = p.entrance_kit["cheek_form"]
            v["stair"]["cheek_form"] = cf["kind"]
            if cf["kind"] == "swept":   # T-2918: a scrolled cheek takes no sizes of its own
                v["stair"]["swept"] = {k: cf[k] for k in ("head_m", "foot_m", "block_m", "flare", "newel", "pierced") if k in cf}
            else:
                if "foot_block_m" in cf:   # T-2984: but its roll may stand on a foot block
                    v["stair"]["scroll_block_m"] = cf["foot_block_m"]
                if "bow" in cf:   # T-3186: and its sweep fall straighter than the square's
                    v["stair"]["scroll_bow"] = cf["bow"]
                if "pierced" in cf:   # T-3186: and both pierced under their coping
                    v["stair"]["scroll_pierced"] = cf["pierced"]
        # T-2530: a side stoop's landing, from the front's s into run coordinates about the door
        ss = p.entrance_kit.get("side_stoop")
        if ss:
            k = 1.0 if ss["run"] == "right" else -1.0
            ends = sorted(k * (x - door.s_m) for x in ss["landing_v_m"])
            v["stair"]["side"] = {"run": ss["run"], "landing_s_m": ends, "out_m": ss["out_m"],
                                  **({"cheek_above_nosing_m": ss["cheek_above_nosing_m"]}
                                     if "cheek_above_nosing_m" in ss else {})}
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
        stair_conf = p.worst_conf("principal_floor_m", "stair_tread_m", "stair_landing_depth_m", "stoop_width_m",
                                  *(("entrance_floor_m",) if p.entrance_floor_m else ()))
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        stair_seed = self.instance("k01.stair.straight_stoop", "stair",
                                   {"riser_m": st["riser_m"], "tread_m": st["going_m"], "risers": st["risers"],
                                    "landing_depth_m": p.landing_depth_m, "width_m": p.stoop_width_m,
                                    "k07_variant": p.entrance_kit["variant"], "cheeks": o.v["stair"].get("cheeks", False),
                                    "front_yard_m": p.entrance_kit["front_yard_m"],
                                    **({"side_stoop": dict(p.entrance_kit["side_stoop"])}
                                       if p.entrance_kit.get("side_stoop") else {}),
                                    **({"terrace_to_v_m": (p.entrance_kit["terrace"]["to_v_m"]
                                                           if isinstance(p.entrance_kit["terrace"], dict)
                                                           else [q["to_v_m"] for q in p.entrance_kit["terrace"]])}
                                       if p.entrance_kit.get("terrace") else {}),
                                    **({"balusters": o.meta.get("balusters", 0),
                                        "balustrade_height_m": p.entrance_kit["balustrade"]["height_m"]}
                                       if p.entrance_kit.get("balustrade") else {})},
                                   {"foot": P(op.s_m + st["foot_s_m"] if "foot_s_m" in st else p.stoop_s_m(op.s_m),
                                              0.0, st["foot_out_m"]), "landing": P(op.s_m, op.sill_m, 0.0),
                                    **{f"{k}_{end}": P(op.s_m + q[0], op.sill_m + q[1], q[2])
                                       for k, ends in sorted(o.sockets.items())
                                       for end, q in zip(("top", "foot"), ends)}})
        roles = {r: (m or body_mat) for r, m in self.K07_ROLES.items()}
        if ((p.entrance_kit or {}).get("leaf") or {}).get("color"):   # T-3236
            roles["leaf"] = "door_leaf_varnish"
        # T-2960: a painted timber balustrade, and the deck of a veranda open beneath, in the
        # walls' paint as the veranda's posts are
        if (p.entrance_kit.get("balustrade") or {}).get("fabric") == "painted_timber":
            roles.update(baluster=body_mat, newel=body_mat, rail=body_mat)
        if (p.entrance_kit.get("veranda") or {}).get("open_under"):
            roles["terrace"] = body_mat
        self.graft(o, "K07", roles, frame, op,
                   lambda role: (stair_seed, stair_conf) if role in self.STAIR_ROLES else (seed, conf))

    # -- the door's hood (T-2480) ---------------------------------------------------------
    def door_hood(self, op, frame):
        """A timber hood over the door in a K08 bay hood's joinery: a fascia box `out_m` from
        the wall, a cornice slab over it standing `proud_m` past its front and ends, a row of
        the bay's modillions under that overhang and one of the bay's consoles under the
        soffit at each end, against the wall; on the slab's flat top a low railing on three
        sides, posts at its corners, square balusters under a rail. All of it the eaves'
        painted joinery (the `fascia` slot, as K08's hood is on a K01 front). A box's faces
        against the wall, against the slab, or under the slab are not drawn."""
        p = self.p
        h = p.entrance_kit["hood"]
        O, R, N = frame
        P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
        conf = p.conf("entrance_kit")
        # T-3159: a portico in the front's stone (1729's), laid in its bays' walling slot
        mat = "bay_stone" if h.get("fabric") == "stone" else "fascia"
        pr = self.prim(mat)
        tri0 = len(pr.idx) // 3
        c, W, out = op.s_m + h.get("offset_m", 0.0), h["width_m"], h["out_m"]   # T-1871: off the door's axis
        y0 = h["soffit_m"]
        y1 = y0 + h["fascia_m"]
        cp = h["cornice"]["proud_m"]
        y2 = y1 + h["cornice"]["height_m"]
        rl = h["railing"]
        y3 = y2 + rl["height_m"]
        s0, s1 = c - W / 2, c + W / 2
        S0, S1, D = s0 - cp, s1 + cp, out + cp          # the slab's plan
        if y0 < op.head_m + 0.30 + 0.05:
            raise ValueError(f"the door hood's soffit ({y0} m) is not clear of the door's lintel")
        for o in p.openings:   # nothing on the front it stands before
            if h.get("columns") and o.head_m + 0.30 <= y0:
                continue   # T-1871: a window behind a porch on columns, its lintel under the soffit
            if o.wall == op.wall and o is not op and o.s_m + o.width_m / 2 + 0.08 > S0 \
                    and o.s_m - o.width_m / 2 - 0.08 < S1 and o.sill_m - 0.12 < y3 and o.head_m > y0 - 1.0:
                raise ValueError(f"the door hood ({S0:.2f}-{S1:.2f} m, {y0}-{y3:.2f} m) runs into "
                                 f"the opening at s = {o.s_m}")
        for b in p.bays:   # nor the pavilion's walls (a bay's hood it may run into, as drawn)
            if b["wall"] == op.wall and b["variant"]["kind"] != "bay" and \
                    b["span_m"][0] < S1 + 0.05 and b["span_m"][1] > S0:
                raise ValueError(f"the door hood ({S0:.2f}-{S1:.2f} m) runs into {b['id']}")
        con, mod = h["consoles"], h["modillions"]
        seed = self.instance("k01.hood.door_bracketed", "hood",
                             {"width_m": W, "out_m": out, "soffit_m": y0, "top_m": y2, "railing_m": rl["height_m"],
                              "k08_brackets": h["brackets"]},
                             {"soffit": P(c, y0, 0.0), "deck": P(c, y2, 0.0)})
        bf = self.basis(mat, O, R, Y, seed)          # faces along the wall
        bh = self.basis(mat, O, R, N, seed)          # level faces
        be = self.basis(mat, O, N, Y, seed)          # end faces
        quad = lambda pts, n, b: pr.face(pts, n, b, conf)
        down, up, left, right = _mul(Y, -1), Y, _mul(R, -1), R

        def box(a0, a1, b0, b1, d0, d1, skip=()):
            """A box s a0..a1, y b0..b1, d d0..d1, less the faces named in `skip`."""
            f = {"front": ([P(a0, b0, d1), P(a1, b0, d1), P(a1, b1, d1), P(a0, b1, d1)], N, bf),
                 "back": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b1, d0), P(a0, b1, d0)], _mul(N, -1), bf),
                 "top": ([P(a0, b1, d0), P(a1, b1, d0), P(a1, b1, d1), P(a0, b1, d1)], up, bh),
                 "bottom": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b0, d1), P(a0, b0, d1)], down, bh),
                 "left": ([P(a0, b0, d0), P(a0, b0, d1), P(a0, b1, d1), P(a0, b1, d0)], left, be),
                 "right": ([P(a1, b0, d0), P(a1, b0, d1), P(a1, b1, d1), P(a1, b1, d0)], right, be)}
            for k, (pts, n, b) in f.items():
                if k not in skip:
                    quad(pts, n, b)

        # the fascia box, its top under the slab and its back on the wall
        box(s0, s1, y0, y1, 0.0, out, skip=("back", "top"))
        # the cornice slab: its underside only where it stands past the box
        box(S0, S1, y1, y2, 0.0, D, skip=("back", "bottom"))
        quad([P(S0, y1, out), P(S1, y1, out), P(S1, y1, D), P(S0, y1, D)], down, bh)
        quad([P(S0, y1, 0.0), P(s0, y1, 0.0), P(s0, y1, out), P(S0, y1, out)], down, bh)
        quad([P(s1, y1, 0.0), P(S1, y1, 0.0), P(S1, y1, out), P(s1, y1, out)], down, bh)
        # the modillions under the slab's overhang, along the front between the returns
        mw, md = mod["width_m"], mod["drop_m"]
        mo = min(mod["out_m"], cp)
        n = max(1, math.floor((W - 2 * mod["margin_m"] - mw) / mod["spacing_m"] + 1e-9) + 1)
        gap = (W - 2 * mod["margin_m"] - n * mw) / max(n - 1, 1)
        for k in range(n):
            a0 = s0 + mod["margin_m"] + k * (mw + gap) if n > 1 else c - mw / 2
            box(a0, a0 + mw, y1 - md, y1, out, out + mo, skip=("back", "top"))
        # a console under the soffit at each end: its top on the soffit, its back on the
        # wall, its underside a quarter ellipse from the soffit's front in and down to the wall
        Rr, Dd, t = con["reach_m"], con["drop_m"], con["thickness_m"]
        kseg = con["segments"]
        arc = [(Rr - Rr * math.sin(math.pi / 2 * j / kseg), -Dd + Dd * math.cos(math.pi / 2 * j / kseg))
               for j in range(kseg + 1)]
        inset = 0.05
        # T-3210: none on an end an arch is turned across (its spandrel wall stands there)
        ends = (h.get("columns") and h.get("arches") or {}).get("faces", ())
        for a0 in [x for x, e in ((s0 + inset, "left"), (s1 - inset - t, "right")) if e not in ends]:
            for s_, n_ in ((a0, left), (a0 + t, right)):
                for j in range(kseg):
                    quad([P(s_, y0, 0.0), P(s_, y0 + arc[j][1], arc[j][0]), P(s_, y0 + arc[j + 1][1], arc[j + 1][0])],
                         n_, be)
            for j in range(kseg):
                (r0, q0), (r1, q1) = arc[j], arc[j + 1]
                hr, hy = Rr - (r0 + r1) / 2, -Dd - (q0 + q1) / 2   # facing the ellipse's centre
                nn = _unit(_add(_mul(N, hr), _mul(Y, hy)))
                quad([P(a0, y0 + q0, r0), P(a0 + t, y0 + q0, r0), P(a0 + t, y0 + q1, r1), P(a0, y0 + q1, r1)],
                     nn, bh)
        # T-2963: a porch's columns, under the soffit at the deck's front corners (built
        # before the railing, which may change the material the boxes are laid in)
        cols = h.get("columns")
        if cols:
            self._hood_columns(cols, op, P, quad, box, bf, bh, be, s0, s1, out, y0, R, N, seed, conf, h.get("arches"))
        tri_fascia = len(pr.idx) // 3 - tri0
        # the railing on the slab: posts at the front corners and against the wall, a rail
        # over square balusters along the front and both returns. T-2963: in iron if the
        # record says so (1816's balcony), the K01 iron every other railing wears
        if h.get("railing_fabric") == "iron":
            pr = self.prim("iron")
            tri1 = len(pr.idx) // 3
            bf, bh, be = (self.basis("iron", O, a, b, seed) for a, b in ((R, Y), (R, N), (N, Y)))
        pm, bm = rl["post_m"], rl["baluster_m"]
        rw, rd = rl["rail_m"]
        e = 0.04                                   # the railing's line in from the slab's edge
        L, Rs, F = S0 + e, S1 - e, D - e           # its outer edges: left, right, front
        posts = [(L, F - pm), (Rs - pm, F - pm), (L, 0.0), (Rs - pm, 0.0)]
        for a0, d0 in posts:
            box(a0, a0 + pm, y2, y3, d0, d0 + pm, skip=("bottom",) + (("back",) if d0 == 0.0 else ()))
        yr = y3 - rd
        mid = lambda a, b: (a + b) / 2
        # the rail: front run between the front posts, each return from the wall post to the front post
        fr = (F - pm / 2 - rw / 2, F - pm / 2 + rw / 2)
        box(L + pm, Rs - pm, yr, y3 - 0.02, *fr, skip=("left", "right"))
        for a in (L, Rs - pm):
            ac = (mid(a, a + pm) - rw / 2, mid(a, a + pm) + rw / 2)
            box(*ac, yr, y3 - 0.02, pm, F - pm, skip=("back", "front"))

        def balusters(a, b, along_s, fixed):
            n = max(1, math.floor((b - a) / rl["pitch_m"]))
            step = (b - a) / (n + 1)
            for i in range(1, n + 1):
                m = a + i * step
                if along_s:
                    box(m - bm / 2, m + bm / 2, y2, yr, fixed - bm / 2, fixed + bm / 2, skip=("bottom", "top"))
                else:
                    box(fixed - bm / 2, fixed + bm / 2, y2, yr, m - bm / 2, m + bm / 2, skip=("bottom", "top"))
            return n
        nb = balusters(L + pm, Rs - pm, True, mid(*fr))
        for a in (L, Rs - pm):
            nb += balusters(pm, F - pm, False, mid(a, a + pm))
        self.trim_triangles["k01.hood.door_bracketed"] = (
            tri_fascia + len(pr.idx) // 3 - tri1 if h.get("railing_fabric") == "iron" else len(pr.idx) // 3 - tri0)
        self.seat(frame, [(s, y, 0.0) for s in (S0, S1) for y in (y0 - Dd, y3)], "k01.hood")
        self.hood_meta = {"modillions": n, "consoles": 2 - len({"left", "right"} & set(ends)), "balusters": nb,
                          "top_m": round(y3, 4),
                          **({"columns": len(cols.get("at_s_m", (0, 0)))} if cols else {}),
                          **({"arches": self._arch_count} if cols and h.get("arches") else {}),
                          **({"fabric": "stone"} if mat == "bay_stone" else {}),
                          **({"railing_fabric": h["railing_fabric"]} if h.get("railing_fabric") else {})}

    def _hood_columns(self, co, op, P, quad, box, bf, bh, be, s0, s1, out, y0, R, N, seed, conf, arches=None):
        """T-2963: two turned columns carrying a door hood as a porch (1816's): each a square
        plinth on the stoop's landing, a twelve-sided shaft and a square capital block under
        the soffit, at the deck's front corners, and a flat respond against the wall behind
        it. In the hood's own painted joinery. T-3159: or a row of them where a picture puts
        them (`at_s_m`, from the door's axis), on the landing and the terraces beside it.
        T-3186: or each capital carved, a bell of leaves under its abacus (`carved`).
        T-3210: or under an arcade (`arches`), the capitals at its springing."""
        dia, (pw, ph), cap, rsp = co["diameter_m"], co["plinth_m"], co["capital_m"], co["respond_m"]
        cv = co.get("carved")
        yl = op.sill_m                                   # the landing, the door's own sill
        r, seg = dia / 2, 12
        cd = out - pw / 2 - 0.05
        cw = min(pw, dia + 0.14) / 2
        ys = arches["spring_m"] if arches else y0        # the capitals' top
        at = [op.s_m + a for a in co["at_s_m"]] if co.get("at_s_m") else (s0 + pw / 2 + 0.05, s1 - pw / 2 - 0.05)
        for cs in at:
            if not s0 + pw / 2 + 0.05 - 1e-6 <= cs <= s1 - pw / 2 - 0.05 + 1e-6:
                raise ValueError(f"the hood's column at s {cs:.3f} stands past its ends ({s0:.3f}-{s1:.3f})")
            box(cs - pw / 2, cs + pw / 2, yl, yl + ph, cd - pw / 2, cd + pw / 2, skip=("bottom",))
            box(cs - cw, cs + cw, ys - (cv["abacus_m"] if cv else cap), ys, cd - cw, cd + cw,
                skip=("top",) if not arches else ())
            if cv:   # T-3186: the bay columns' bell of leaves (T-2887), its crown under the abacus
                C, ya, yb, k = P(cs, 0.0, cd), ys - cap, ys - cv["abacus_m"], cv["tiers"]
                for t in range(k):
                    lo, hi = ya + (yb - ya) * t / k, ya + (yb - ya) * (t + 1) / k
                    self.bell("carved_trim", C, R, N, C[1] + lo, C[1] + hi, r + 0.01 + 0.02 * t,
                              r + 0.05 + 0.025 * t, seed, conf)
            ya, yb = yl + ph, ys - cap
            for k in range(seg):
                a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
                am = (a0 + a1) / 2
                q = [(cs + r * math.cos(a), cd + r * math.sin(a)) for a in (a0, a1)]
                quad([P(q[0][0], ya, q[0][1]), P(q[1][0], ya, q[1][1]), P(q[1][0], yb, q[1][1]), P(q[0][0], yb, q[0][1])],
                     self._hood_dir(P, am), bf)
            # the respond: a flat pilaster on the wall behind the column, landing to soffit
            box(cs - pw / 2 + 0.05, cs + pw / 2 - 0.05, yl, y0, 0.0, rsp, skip=("back", "bottom", "top"))
        if arches:
            self._arch_count = self._hood_arcade(arches, P, quad, bf, bh, be, sorted(at), s0, s1, cd, cw, rsp, y0)

    def _hood_arcade(self, A, P, quad, bf, bh, be, at, s0, s1, cd, cw, rsp, y0):
        """T-3210: round arches on a porch's columns (1827's, the Doane photograph). On the
        front a spandrel wall as thick as the capitals, on the columns' line from the hood's one
        end to the other and from the springing to the soffit, an arch cut in it between each
        pair of columns from capital to capital. On an end named in `faces`, the same wall
        across the end column's line from the house's wall back to the front's, its arch from
        the respond to the end column's capital. Each arch a half ellipse `rise_m` high over its
        clear span, drawn in `K` facets. Its top under the fascia and its foot on the capitals
        are not drawn; nor the end wall's face on the house's wall or on the front's."""
        K, ys, ri = 12, A["spring_m"], A["rise_m"]
        o = P(0.0, 0.0, 0.0)
        R_, Y_, N_ = (_sub(P(*e), o) for e in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
        n = 0

        def wall(spans, lo, hi, face, inn, out_, nf, bfc):
            """A spandrel wall from `lo` to `hi` along its run, `inn`..`out_` through it, its
            faces normal to `nf`; `face(x, y, t)` places run x, height y and depth t. Each
            span (a, b) an arch cut from it."""
            pieces, x = [], lo
            for a, b in spans:
                pieces.append(("pier", x, a))
                pieces.append(("arch", a, b))
                x = b
            pieces.append(("pier", x, hi))
            for kind, a, b in pieces:
                if b - a < 1e-6:
                    continue
                if kind == "pier":
                    for t, sg in ((out_, 1.0), (inn, -1.0)):
                        quad([face(a, ys, t), face(b, ys, t), face(b, y0, t), face(a, y0, t)], _mul(nf, sg), bfc)
                    continue
                m, hs = (a + b) / 2, (b - a) / 2
                arc = [(m - hs * math.cos(math.pi * j / K), ys + ri * math.sin(math.pi * j / K)) for j in range(K + 1)]
                for j in range(K):
                    (xa, ya_), (xb, yb_) = arc[j], arc[j + 1]
                    for t, sg in ((out_, 1.0), (inn, -1.0)):
                        quad([face(xa, ya_, t), face(xb, yb_, t), face(xb, y0, t), face(xa, y0, t)], _mul(nf, sg), bfc)
                    # the intrados, facing the arch's centre
                    xm, ym = (xa + xb) / 2, (ya_ + yb_) / 2
                    dn = _unit(_add(_mul(face(1.0, 0.0, 0.0, vec=True), (m - xm) / hs ** 2),
                                    _mul(Y_, (ys - ym) / ri ** 2)))
                    quad([face(xa, ya_, inn), face(xb, yb_, inn), face(xb, yb_, out_), face(xa, ya_, out_)], dn, bh)

        # the front: from end to end of the hood, its arches between the capitals
        spans = [(a + cw, b - cw) for a, b in zip(at, at[1:])]
        front = lambda x, y, t, vec=False: R_ if vec else P(x, y, t)
        if "front" in A["faces"]:
            wall(spans, s0, s1, front, cd - cw, cd + cw, N_, bf)
            n += len(spans)
            # the wall's underside past the end columns, and its ends
            for a, b in ((s0, at[0] - cw), (at[-1] + cw, s1)):
                if b - a > 1e-6:
                    quad([P(a, ys, cd - cw), P(b, ys, cd - cw), P(b, ys, cd + cw), P(a, ys, cd + cw)], _mul(Y_, -1.0), bh)
            for x, sg in ((s0, -1.0), (s1, 1.0)):
                quad([P(x, ys, cd - cw), P(x, ys, cd + cw), P(x, y0, cd + cw), P(x, y0, cd - cw)], _mul(R_, sg), be)
        # the ends: across the end column's line, from the wall to the front's wall
        d1 = cd - cw if "front" in A["faces"] else cd + cw
        for side, cs in (("left", at[0]), ("right", at[-1])):
            if side not in A["faces"]:
                continue
            end = lambda x, y, t, vec=False, cs=cs: N_ if vec else P(cs + t, y, x)
            wall([(rsp, cd - cw)], 0.0, d1, end, -cw, cw, R_, be)
            n += 1
            if "front" not in A["faces"]:
                quad([P(cs - cw, ys, d1), P(cs + cw, ys, d1), P(cs + cw, y0, d1), P(cs - cw, y0, d1)], N_, bf)
        return n

    @staticmethod
    def _hood_dir(P, a):
        """The outward unit normal of a column face at angle `a` in the hood's (s, d) plane."""
        o, e, n = P(0.0, 0.0, 0.0), P(1.0, 0.0, 0.0), P(0.0, 0.0, 1.0)
        R_ = tuple(x - y for x, y in zip(e, o))
        N_ = tuple(x - y for x, y in zip(n, o))
        return _unit(_add(_mul(R_, math.cos(a)), _mul(N_, math.sin(a))))

    # -- k01.roof.hip, built from the K05 roof-construction kit (T-2302) -------------
    def roof(self):
        """The roof as ONE closed solid (K05, T-2302). The hip, the street dormer and the
        chimney stacks are each a closed element from `k05_roofs`, joined by the kit's
        boolean union, and the dormer's sash recess is cut out of the result, so every
        valley, cheek, stack and reveal is cut where its surfaces really meet: no plane
        crosses another, nothing floats and no face is drawn twice. The K04 dressing
        (caps, valley flashing, apron, step flashing) is then laid on the ROOF GRAPH read
        off that surface, not on numbers of its own."""
        if self.p.roof_form == "flat":
            return self.flat_roof()
        from . import k05_roofs as k5
        p, k = self.p, self.p.roof or {}
        kit = k5.load()
        D, W, E, o = p.depth_m, p.width_m, p.eave_m, p.eave_overhang_m
        tp = math.tan(math.radians(p.roof_pitch_deg))
        f = kit["parts"]["eave"]["fascia_depth_m"]
        m = p.mansard
        # T-2370: a mansard's eave is its cornice, the fascia's top on the wall head; a
        # hip's eave drops by the overhang's run down the slope
        ye = E if m else E - o * tp
        yf = ye - f
        yr = p.ridge_m
        gb = p.gable                          # T-2459: a ridge along the front, parapets each side
        conf = p.worst_conf("footprint", "roof_form", "roof_pitch_deg", "eave_overhang_m", "roof_covering",
                            *(("mansard",) if m else ()), *(("gable_roof",) if gb else ()))
        seed = self.instance("k01.roof.mansard" if m else "k01.roof.gable" if gb else "k01.roof.hip", "roof",
                             {"pitch_deg": p.roof_pitch_deg, "eave_overhang_m": o,
                              **({"variant": m["variant"], "lower_pitch_deg": m["lower_pitch_deg"],
                                  "lower_rise_m": m["lower_rise_m"], "curb_datum_m": m["curb_m"]} if m else {}),
                              **({"side_parapet": {"wall": m["side_parapet"]["wall"],
                                                   "top_m": m["side_parapet"]["top_m"]}}
                                 if (m or {}).get("side_parapet") else {}),
                              **({"ridge_back_m": gb["ridge_back_m"], "back_pitch_deg": gb["back_pitch_deg"],
                                  "parapets": {k_: e["style"] for k_, e in gb["ends"].items()},
                                  "parapet_top_m": round(yr + gb["top_above_ridge_m"], 4),
                                  **({"rear_fall": gb["rear_fall"]} if gb.get("rear_fall") else {})} if gb else {}),
                              "eave_datum_m": E, "ridge_datum_m": yr, "construction": "k05",
                              "fascia_depth_m": f, "chimneys": len(p.chimneys),
                              **({"covering": k["covering"], "flashing": k["flashing"]} if k else {}),
                              **({"gutter_diameter_m": p.rainwater["gutter_diameter_m"], "gutter_fall": p.rainwater["fall"],
                                  "downpipes": len(p.rainwater["downpipes"]),
                                  "pipe_diameter_m": p.rainwater["pipe_diameter_m"]} if p.rainwater else {})},
                             {"eave": (0.0, E, 0.0), "ridge": (W / 2, yr, -W / 2)})
        # the elements: the hip over the wall line, a body under it (the walls' tops,
        # so the soffit is a ring and not a lid; never emitted), the dormer, the stacks
        if m:   # T-2370: K05's mansard ring stack, the lower faces curved to the curb
            # T-3186: a canted corner cuts every ring on its face's line, out to the fascia
            cut = ((lambda ring, out: k01_frontage_params.cant_ring(ring, p.cant_corner, D, W, out)),
                   o + p.cant_corner["cut_m"] / (2.0 - math.sqrt(2.0))) if p.cant_corner else None
            hip, hs, _ = k5.mansard_element(0.0, D, -W, 0.0, E, m["lower_pitch_deg"], p.roof_pitch_deg,
                                            m["lower_rise_m"], m["bulge"], m["segments"], m["profile"], o, f,
                                            cut=cut)
        elif gb:   # T-2459: the parapets first, so the union keeps their faces on the walls' planes
            from . import k01_gable_roof
            solids, hs, _, self.gable_roof = k01_gable_roof.elements(p, k5, E, o, f)
        else:
            hip, hs = k5.hip_element(0.0, D, -W, 0.0, E, tp, o, f)
        if not gb:
            solids = [hip, k5.body_box(0.0, D, -W, 0.0, hs - 1.0, hs)]
        if p.cant_corner:   # T-3186: and the walls' tops under it cut on the face's own line
            ring = k01_frontage_params.cant_ring(k5.inset_rect(0.0, D, -W, 0.0, 0.0), p.cant_corner, D, W, 0.0)
            solids[1] = k5.ring_stack([(hs - 1.0, ring), (hs, ring)], ["wall"], "base", top_role="hidden")
        spp = (m or {}).get("side_parapet")
        if spp:
            # T-3061: a side wall carried up past the curb as a coped parapet, joined FIRST so
            # the union keeps its faces on the wall's plane; its front end stops just behind
            # the street wall's, as a gable roof's parapets do (k01_gable_roof.FRONT_SET_M)
            from .k01_gable_roof import FRONT_SET_M
            tw, slab = spp["thickness_m"], spp["top_m"] - spp["coping_m"]
            c0, c1 = (-tw, 0.0) if spp["wall"] == "south" else (-W, -W + tw)
            solids = k5.parapet_element({}, [(0.0, slab), (D - FRONT_SET_M, slab)], (c0, c1), "z", tw, hs,
                                        spp["coping_m"], spp["drip_m"], 0.0, 0.0) + solids
        straight_cut = []
        if (m or {}).get("straight"):   # T-2995: the straight walls' parapets, and their cutters
            from . import k01_mansard_straight
            more, straight_cut, _ = k01_mansard_straight.elements(p, k5, hs)
            solids = more + solids
        cr = (m or {}).get("crown")
        if cr and cr.get("form") == "hip":   # T-2465: a crown hipped to its own ridge
            crown, _, _ = k5.hip_crown_element(cr["x0"], cr["x1"], cr["z0"], cr["z1"], cr.get("eave_m", E), cr["pitch_deg"],
                                               cr["end_pitch_deg"], cr["overhang_m"], f)
            solids.append(crown)
        elif cr:  # T-2404: the pavilion's crown, a taller mansard joined into the main one
            crown, _, _ = k5.mansard_element(cr["x0"], cr["x1"], cr["z0"], cr["z1"], E, cr["lower_pitch_deg"],
                                             p.roof_pitch_deg, cr["lower_rise_m"], cr["bulge"], m["segments"],
                                             m["profile"], cr["overhang_m"], f)
            solids.append(crown)
        recess, recesses = None, []
        self.round_dormers = []
        if cr and cr.get("dormer"):
            g = self.crown_dormer_body(cr, E, f)
            solids.append(g["body"])
            recesses.append(g["recess"])
        if m and m.get("dormers"):   # T-2411: the main mansard's lower-face dormers
            for g in self.mansard_dormer_bodies(m, E):
                solids.append(g["body"])
                solids += g.get("hood", [])   # T-3000: a hooded dormer's shelf and hood
                recesses.append(g["recess"])
        if p.slope_dormers:   # T-2866: dormers on the hip's side slopes
            for g in self.slope_dormer_bodies(E, tp):
                solids += [g["body"], g["roof"]] if g["roof"] else [g["body"]]
                recesses.append(g["recess"])
        d = p.dormer
        if d:
            dp = kit["parts"]["dormer"]
            dt = math.tan(math.radians(d["pitch_deg"]))
            wd, sb, hf = d["width_m"], d["face_setback_m"], d["face_height_m"]
            xf = D - sb                       # the face, on the street hip
            ys = E + sb * tp                  # its foot, where it leaves the covering
            yde = ys + hf                     # the dormer's eave, at its wall line
            zc = -d.get("v_m", W / 2)        # T-2428: a wall gable may stand off the front's centre
            back = D - (yde + wd / 2 * dt - E) / tp - 0.5   # behind where its ridge dies
            g, dhs, dhe, dry = k5.gable_element(back, xf, zc - wd / 2, zc + wd / 2, yde, dt, dp["overhang_m"],
                                                d["verge_m"], dp["fascia_depth_m"], hs, "x", verge_ends=("hi",),
                                                wall_role="cheek", end_role="dormer_face",
                                                body_end_role="dormer_face")
            solids += g
            self.dormer_geom = {"xf": xf, "ys": ys, "yde": yde, "dhs": dhs, "dhe": dhe, "ridge": dry,
                                "zs": zc + wd / 2, "zn": zc - wd / 2, "dt": dt, "overhang": dp["overhang_m"],
                                "back": back}
            if d.get("wall_gable"):
                # T-2428: a wall gable's lights, cut to K06's own head, and its pediment panel
                from . import k01_wall_gable
                recesses += k01_wall_gable.cutters(self, k5, k5.frame("x"), xf, ys, zc)
            else:
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
        if p.rear_section:   # T-2820: the rear section's attic, its end parapets and dormers
            from . import k01_rear_section
            more, cut = k01_rear_section.elements(self, k5, f)
            solids += more
            recesses += cut
        if p.shaped_gable:   # T-2543: the front carried up as a shaped gable, joined like a stack
            from . import k01_shaped_gable
            solids.append(k01_shaped_gable.element(self, k5, ye))
            recesses += k01_shaped_gable.cutters(self, k5)
        # T-2302's plain stacks, for a record that names no K15 variant (1612 Goodman)
        self.stone_stack_boxes = []
        plain_stacks = []
        for c in p.chimneys:
            if "k15" in c or "k15_head" in c:
                continue
            sx, sz = c["plan_m"]
            u, z = c["u_m"], -c["v_m"]
            top = c["top_m"]
            P = k5.frame("z")
            cp, cd = c["cap_proud_m"], c["cap_depth_m"]
            # the stack stops inside its cap, so the two never share a face; one on a
            # mansard's cornice (T-2406) rises from the cornice's top, not under the soffit
            y0 = hs - 0.5 if c.get("base_m") is None else c["base_m"]
            if c.get("head"):   # T-3109: the dressed base, collar, latticed stage and cap
                more = self.dressed_stack(k5, c, y0)
                solids += more
                plain_stacks += more
                continue
            solids.append(k5.extrude([(u - sx / 2, y0), (u + sx / 2, y0), (u + sx / 2, top - cd / 2),
                                      (u - sx / 2, top - cd / 2)], z - sz / 2, z + sz / 2, P,
                                     lambda i, p_, q_: "chimney" if i != 2 else "hidden", "chimney", "chimney"))
            if c.get("stone"):   # T-3003: its shaft in the walls' stone (_emit_shell reads the box)
                self.stone_stack_boxes.append((u - sx / 2 - 1e-3, u + sx / 2 + 1e-3, z - sz / 2 - 1e-3, z + sz / 2 + 1e-3))
            solids.append(k5.extrude([(u - sx / 2 - cp, top - cd), (u + sx / 2 + cp, top - cd),
                                      (u + sx / 2 + cp, top), (u - sx / 2 - cp, top)],
                                     z - sz / 2 - cp, z + sz / 2 + cp, P, "coping", "coping", "coping"))
            plain_stacks += solids[-2:]
        polys = k5.union_all(k5._snap(solids))
        # T-2313: each stack from the K15 kit, built in this roof as the kit builds its
        # specimen's (k15_chimneys.build_variant): its parts joined and its flues cut on
        # their own, then joined to the roof, so the shaft is cut where it passes through
        # the slate, the flashing where it lies on it and the cricket where it meets it
        self.stacks = []
        k15s = [c for c in p.chimneys if "k15" in c]
        if k15s:
            from . import k15_chimneys as k15
            data = k15.load()

            def cover(x, z):   # the hip's covering over a plan point (x = u, z = -v)
                return E + tp * max(0.0, min(x, D - x, -z, W + z))
            for c in k15s:
                s = dict(c["k15"], x=c["u_m"], z=-c["v_m"])
                parts, meta = k15.stack_solids(s, k15.Frame(s, cover), data, tp)
                parts = {key: (k5._snap(x) if isinstance(x, list) else x) for key, x in parts.items()}
                polys = k5.union(polys, k15.join_stack(parts))
                self.stacks.append(dict(meta, id=c["id"], centre=[c["u_m"], c["v_m"]]))
        # T-2466: a mansard's plain stack with the K15 kit's head (its sunk panels, corbelled
        # courses and cap), built by the kit with its flashing off, since the kit's flashing
        # reads one slope and a mansard stack stands on a cornice or a steep face. Its shaft
        # rises from where the plain stack's did, and the covering it measures its panels and
        # sooted band from is the highest under it (k01_frontage_params.mansard_cover)
        heads = [c for c in p.chimneys if "k15_head" in c]
        if heads:
            from . import k15_chimneys as k15
            data = k15.load()
            for c in heads:
                s = dict(c["k15_head"], x=c["u_m"], z=-c["v_m"])
                y0 = hs - 0.5 if c.get("base_m") is None else c["base_m"]
                parts, _ = k15.stack_solids(s, k15.Frame(s, lambda x, z, h=c["cover_high_m"]: h), data, tp,
                                            bottom=y0, flashing=False)
                parts = {key: (k5._snap(x) if isinstance(x, list) else x) for key, x in parts.items()}
                polys = k5.union(polys, k15.join_stack(parts))
        recesses += self.through_eave_cutters(k5, yf)
        recesses += straight_cut
        recesses += self.shallow_bay_cutters(k5, yf)
        for rc in ([recess] if recess is not None else []) + recesses:
            polys = k5.subtract(polys, k5._snap([rc])[0])
        if p.front_pier:   # T-3112: the eave cut back over the pier and its weathering joined
            cut, hood = self.pier_roof(k5, yf)
            polys = k5.union(k5.subtract(polys, cut), k5._snap([hood])[0])
            # a stack standing in the cut (1811's at u 1.0, v 0.9) is the stack's, not the slope's
            for st in plain_stacks:
                polys = k5.union(polys, k5._snap([st])[0])
        pts, tris = _weld_shell(*k5.close(polys))
        self.roof_shell = (pts, tris)
        # the graph reads a stack's every part as `chimney`, which K05 already classes as
        # an abutment: the K15 flashing and cricket ARE what dresses the covering there
        dressed = any(c.get("head") for c in p.chimneys)
        self.roof_graph = k5.graph(pts, tris if not (k15s or heads or dressed) else
                                   [t[:3] + (("chimney" if t[3] in self.STACK else t[3]),) + t[4:] for t in tris],
                                   kit)
        self._emit_shell(*self.k14_roof_rows(pts, tris), seed, conf)   # T-2359: the plume's rows
        if d:
            self.dormer_sash(seed)
        if p.shaped_gable:
            from . import k01_shaped_gable
            k01_shaped_gable.dress(self, seed)
        for g in self.round_dormers:
            self.round_dormer_sash(g, conf)
        if k:
            self.dress(pts, tris, seed, conf)
        if p.rainwater:
            self.rainwater(ye, yf, seed)
        return yf

    def pier_roof(self, k5, yf):
        """T-3112: over the pier (`front_pier`) the roof is cut down to the weathering's slope
        across the pier's width and the side eave beside it, from in front of the street eave
        back to where the slope has risen out of the roof (the cut's end face, in the pier's
        side of the bay, is slate, as a dormer's cheek); and the weathering itself is joined:
        a slated wedge from the cap's top to that slope, out over the cap's front and side,
        back to where the slope stands over the soffit, its front a fascia's lip, its back
        returned under the side eave. K05's frame: (u, y, -v)."""
        p, fp = self.p, self.p.front_pier
        D, to, cp = p.depth_m, fp["to_m"], fp["cap_proud_m"]
        L, yt = self.pier_slope(), fp["cap_m"][1]
        tp = math.tan(math.radians(fp["weathering_pitch_deg"]))
        P = k5.frame("z")
        top = p.ridge_m + 10.0
        u_far = D + cp - (top - yt) / tp
        cut = k5.extrude([(u_far, top), (D + cp, yt + self.PIER_LIP_M - 0.002), (D + 3.0, yt + self.PIER_LIP_M - 0.002),
                          (D + 3.0, top)], -to, 3.0, P, k5.by_edge("hidden", "covering", "hidden"), "cheek", "hidden")
        back = D + cp - (yf + 0.05 - yt - self.PIER_LIP_M) / tp
        hood = k5.extrude([(D + cp, yt), (back, yt), (back, L(back)), (D + cp, yt + self.PIER_LIP_M)],
                          -to, cp, P, lambda i, a, b: (("fascia" if a[0] > back + 1e-6 else "return")
                                                       if abs(a[0] - b[0]) < 1e-9 else
                                                       "covering" if a[0] > b[0] else "soffit"), "cheek", "cheek")
        # beside the weathering the side eave box, which stands out past it, stops square where
        # the slope has risen over its fascia, its end closed in the eave's trim
        he = p.eave_m - p.eave_overhang_m * math.tan(math.radians(p.roof_pitch_deg))
        u_e = D + cp - (he + 0.05 - yt - self.PIER_LIP_M) / tp
        side = k5.extrude([(u_e, yt), (D + 3.0, yt), (D + 3.0, top), (u_e, top)], cp, 3.0, P,
                          lambda i, a, b: "return" if abs(a[0] - u_e) < 1e-9 and abs(b[0] - u_e) < 1e-9 else "hidden",
                          "return", "hidden")
        return k5.union(k5._snap([cut])[0], k5._snap([side])[0]), hood

    THROUGH_EAVE_INSET_M = 0.05   # T-2778: the eave runs this far into the oriel's walls

    def through_eave_plan(self, b, inset):
        """T-2778: an oriel's plan on the street front, every run's line moved `inset` in
        and its back `inset` / 25 off the wall plane, as (s along the front, out) points."""
        pts = [tuple(map(float, q)) for q in b["variant"]["plan"]["points"]]
        lines = []
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, z1 - z0)
            e = ((x1 - x0) / L, (z1 - z0) / L)
            n = (e[1], -e[0])                   # the run's inward side (the plan runs left to right)
            lines.append(((x0 + n[0] * inset, z0 + n[1] * inset), e))
        lines = [((-1.0, inset / 25), (1.0, 0.0))] + lines + [((1.0, inset / 25), (-1.0, 0.0))]
        out = []
        for (a1, e1), (a2, e2) in zip(lines, lines[1:]):
            den = e1[0] * e2[1] - e1[1] * e2[0]
            t = ((a2[0] - a1[0]) * e2[1] - (a2[1] - a1[1]) * e2[0]) / den
            out.append((b["s_m"] + a1[0] + t * e1[0], a1[1] + t * e1[1]))
        return out

    def through_eave_cutters(self, k5, yf):
        """T-2778: where an oriel is carried up through the eave (k01_frontage_params._bays,
        `through_eave`), the hip's eave, soffit and the covering's lip in front of the wall
        are cut away inside its plan, its runs moved THROUGH_EAVE_INSET_M in, so the eave
        dies into its cants and runs on a few centimetres inside their walls. The cut faces
        are walls (never emitted): the oriel's own walls stand in front of them."""
        out = []
        for b in self.p.bays:
            if not b.get("through_eave"):
                continue
            # T-2542: or a gable's (1811's): its street eave box is the hip's, out `o` past the
            # wall from the same soffit, so the same prism cuts it
            if b["wall"] != "k01.wall.street_front" or self.p.mansard or self.p.roof_form not in ("hip", "gable"):
                raise ValueError(f"{b['id']}: an oriel is carried through a hip's or a gable's eave on the street front")
            D = self.p.depth_m
            plan = [(D + z, s) for s, z in self.through_eave_plan(b, self.THROUGH_EAVE_INSET_M)]
            # (a, b) = (u, s): K05's world is (u, y, -s); the prism stands from under the soffit
            # to over the covering's lip, which is all the hip has in front of the wall
            out.append(k5.extrude(plan, yf - 0.5, self.p.eave_m + 1.0, lambda a, b_, c: (a, c, -b_),
                                  "wall", "wall", "wall"))
        return out

    def shallow_bays(self):
        """T-3047: the street front's shallow pavilions carried up past a mansard's eave, each as
        (bay, s0, s1, proud, behind): its cheeks along the front, how far it stands proud, and
        how far behind the wall plane its windows' recesses reach (with 0.05 m to spare)."""
        from . import k08_bays as K8
        out = []
        for b in self.p.bays:
            v = b["variant"]
            # T-3001: a shallow pavilion on a rear wing's wall (1801's gabled section) stands
            # clear of the main roof, so there is nothing of the mansard's to cut for it
            if not v.get("shallow") or b.get("wing"):
                continue
            top = math.fsum(float(st["height_m"]) for st in v["storeys"])
            if b["wall"] != "k01.wall.street_front" or not self.p.mansard or top <= self.p.eave_m + 1e-6:
                raise ValueError(f"{b['id']}: a shallow pavilion stands on the street front, carried up past "
                                 f"a mansard's eave")
            proud = max(float(q[1]) for q in v["plan"]["points"])
            behind = K8.part(v, K8.load(), "recess")["depth_m"] - proud + 0.05
            out.append((b, b["span_m"][0], b["span_m"][1], proud, behind))
        return out

    def shallow_bay_cutters(self, k5, yf):
        """T-3047: in front of a shallow pavilion the mansard's eave box, gutter and covering's
        foot would stand out past its face, and its windows' recesses run back into the steep
        lower face: cut them away. Inside it, and behind the wall plane as deep as its recesses
        reach, they are cut on hidden faces (its walls and its back, closed on the plane, stand
        in front of them); in front of its face the eave box stops square at its cheek and, past
        a corner it is flush with, at its face, each end closed in the eave's trim (`return`)."""
        out = []
        D, P = self.p.depth_m, lambda a, b_, c: (a, c, -b_)
        cr = (self.p.mansard or {}).get("crown") or {}
        cut = list(self.shallow_bays())
        if cr.get("eave_m"):   # T-3156: and a pavilion carried up an attic under a raised crown
            b = next(x for x in self.p.bays if x["id"] == cr["over_bay"])
            if not b["variant"].get("shallow"):
                proud = max(float(q[1]) for q in b["variant"]["plan"]["points"])
                cut.append((b, b["span_m"][0], b["span_m"][1], proud, 0.05))
        for b, s0, s1, proud, behind in cut:
            # T-3156: under a crown raised over its attic the cuts stop at the crown's soffit
            top = (cr["eave_m"] - (self.p.eave_m - yf) - 0.005
                   if cr.get("eave_m") and cr["over_bay"] == b["id"] else self.p.eave_m + 10.0)
            far = s1 + 1.0 if b.get("flush_corner") == "right" else s1
            near = s0 - 1.0 if b.get("flush_corner") == "left" else s0
            inner = [(D - behind, s0 + 0.005), (D + proud + 0.005, s0 + 0.005), (D + proud + 0.005, s1 - 0.005),
                     (D - behind, s1 - 0.005)]
            if b.get("flush_corner") == "right":
                inner[2:] = [(D + proud + 0.005, s1), (D - behind, s1)]
            if b.get("flush_corner") == "left":
                inner[:2] = [(D - behind, s0), (D + proud + 0.005, s0)]
            out.append(k5.extrude(inner, yf - 0.5, top, P, "wall", "wall", "wall"))
            outer = [(D + proud, near), (D + 2.0, near), (D + 2.0, far), (D + proud, far)]
            out.append(k5.extrude(outer, yf - 0.5, top, P, "return", "wall", "wall"))
            # T-3048: and outside a chamfered corner's canted face, back to the side wall where
            # it meets it, `behind_m` behind the front; the side's eave box stops square there
            ch = k01_frontage_params.chamfer_of(b)
            if ch is not None:
                side, along, behind, _ = ch
                cut = ([(D + proud, s1 - along), (D + 2.0, s1 - along), (D + 2.0, s1 + 1.0), (D - behind, s1 + 1.0),
                        (D - behind, s1)] if side == "right" else
                       [(D - behind, s0 - 1.0), (D + 2.0, s0 - 1.0), (D + 2.0, s0 + along), (D + proud, s0 + along),
                        (D - behind, s0)])
                out.append(k5.extrude(cut, yf - 0.5, top, P, "return", "wall", "wall"))
        return out

    def flat_roof(self):
        """The stone-front rowhouse's flat roof as ONE closed solid (T-2350), from K05's
        `k05.roof.flat_parapet` (T-2349) laid on this house: the tin deck falling from behind
        the street front to the rear wall, its rear fascia standing on the wall head; a coped
        parapet on each side wall and a blocking course over the street front, level, built
        into the deck so the union cuts it at their inner faces; under the blocking course the
        street cornice's box (soffit, fascia and top) projecting `eave_overhang_m`, which K10's
        brackets carry; and the plain stacks. One union, as the hip is: nothing floats and no
        face is drawn twice. There is no hip or ridge to cap and no gutter (k01_frontage_params)."""
        from . import k05_roofs as k5
        p, fl = self.p, self.p.flat
        kit = k5.load()
        D, W, E, o = p.depth_m, p.width_m, p.eave_m, p.eave_overhang_m
        t = math.tan(math.radians(p.roof_pitch_deg))
        f, tw, er = fl["fascia_m"], fl["parapet_m"], fl["deck_eave_m"]
        top, high = fl["parapet_top_m"], fl["deck_high_m"]
        finish = p.stone_finish
        deck_bottom = E
        if finish:
            drop = finish["deck_drop_m"]
            er, high, deck_bottom = er - drop, high - drop, E - drop
            top = E + .12
        yf = self.soffit_m                            # the cornice's soffit (build: the wall head)
        conf = p.worst_conf("footprint", "roof_form", "roof_pitch_deg", "eave_overhang_m", "roof_covering")
        k = p.roof or {}
        seed = self.instance("k01.roof.flat", "roof",
                             {"pitch_deg": p.roof_pitch_deg, "eave_overhang_m": o, "eave_datum_m": E,
                              "ridge_datum_m": high, "construction": "k05", "variant": fl["variant"],
                              "fascia_depth_m": f, "parapet_thickness_m": tw, "parapet_top_m": top,
                              "upstand_m": fl["upstand_m"], "chimneys": len(p.chimneys),
                              **({"covering": k["covering"], "flashing": k["flashing"]} if k else {})},
                             {"eave": (0.0, E, 0.0), "ridge": (D - tw, high, -W / 2)})
        # the K01 frame: x is u (rear wall 0, street front D), z is -v (south 0, north -W).
        # The deck's outline runs counter-clockwise in (u, y) from the rear foot: soffit (on
        # the wall head, under which the body stands), the end buried in the blocking course,
        # the covering, and the fascia over the rear wall
        P = k5.frame("z")
        zf = D - tw / 2
        # T-1879: where the course is pierced as a balustrade its buried end is seen between the
        # balusters, so over a pierced course that end is the deck's fascia
        bal = fl.get("balustrade")
        deck = k5.extrude([(0.0, deck_bottom), (zf, deck_bottom), (zf, er + zf * t), (0.0, er)], -W + tw / 2, -tw / 2, P,
                          lambda i, p_, q_: ("soffit", "fascia" if bal else "hidden", "covering", "fascia")[i],
                          "hidden", "hidden")
        # T-2564: where the stone finish lays the north return in dressed courses, the brick
        # parapet stops at the return's back rather than running across its face, and the
        # wall head it stood on is the return's (the stone core caps it, so it is no roof face)
        north_end = D - finish["lattice"]["return_m"] if finish and finish.get("return_ashlar") else D
        solids = [deck, k5.body_box(0.0, D, -W, 0.0, E - 1.0, E)] if not finish else [deck,
            k5.body_box(0, D, -tw, 0, deck_bottom-.2, E),
            k5.body_box(0, north_end, -W, -W+tw, deck_bottom-.2, E),
            k5.body_box(0, tw, -W, 0, deck_bottom-.2, E),
            k5.body_box(D-tw, D, -W, 0, deck_bottom-.2, E)]
        if north_end < D:
            solids.append(k5.extrude([(north_end, deck_bottom-.2), (D, deck_bottom-.2), (D, E), (north_end, E)],
                                     -W, -W+tw+.05, k5.frame("z"), lambda i, p_, q_: "base" if i == 0 else "wall",
                                     "wall", "wall"))   # 5 cm wider than the wall: the north stack
                                                        # joins it as it joined the coping's drip
        cp, dr = fl["coping_m"], fl["drip_m"]
        for ends, end in (((-tw, 0.0), D), ((-W, -W + tw), north_end)):   # the south and north parapets
            solids += k5.parapet_element({}, [(0.0, top), (end, top)], ends, "z", tw, E, cp, dr, 0.0, 0.0)
        # the blocking course over the street front
        if bal:   # T-1879: stopped at a plinth where it is pierced as a balustrade (1721's)
            z0, z1, ptop = -bal["to_s_m"], -bal["from_s_m"], E + bal["plinth_m"]
            for path in ([(-W, top), (z0, top)], [(z0, ptop), (z1, ptop)], [(z1, top), (0.0, top)]):
                if path[1][0] - path[0][0] > 1e-6:
                    solids += k5.parapet_element({}, path, (D - tw, D), "x", tw, E, cp, dr, 0.0, 0.0)
        else:
            solids += k5.parapet_element({}, [(-W, top), (0.0, top)], (D - tw, D), "x", tw, E, cp, dr, 0.0, 0.0)
        if finish:
            solids += k5.parapet_element({}, [(-W, top), (0.0, top)], (0, tw), "x", tw, E, cp, dr, 0.0, 0.0)
        # the cornice box: from the front wall's face out `o`, its soffit at the wall head's
        # line and its top at the deck's rear eave, ended flush with the side walls' planes
        cornice_top = E + .12 if finish else er
        # T-2679: a stone finish may read the box as a narrow fillet under its lattice
        ob = finish.get("cornice_box_m", o) if finish else o
        # T-2680: over a stone cornice lifted toward the lattice, the box stands on its top
        yb = yf + float((p.wall_head or {}).get("lift_m", 0.0))
        box = k5.extrude([(D, yb), (D + ob, yb), (D + ob, cornice_top), (D, cornice_top)], -W, 0.0, P,
                         lambda i, p_, q_: ("soffit", "fascia", "fascia", "hidden")[i], "fascia", "fascia")
        solids.append(box)
        for c in p.chimneys:
            sx, sz = c["plan_m"]
            u, z = c["u_m"], -c["v_m"]
            ctop = c["top_m"]
            cpp, cd = c["cap_proud_m"], c["cap_depth_m"]
            solids.append(k5.extrude([(u - sx / 2, E - 0.5), (u + sx / 2, E - 0.5), (u + sx / 2, ctop - cd / 2),
                                      (u - sx / 2, ctop - cd / 2)], z - sz / 2, z + sz / 2, P,
                                     lambda i, p_, q_: "chimney" if i != 2 else "hidden", "chimney", "chimney"))
            solids.append(k5.extrude([(u - sx / 2 - cpp, ctop - cd), (u + sx / 2 + cpp, ctop - cd),
                                      (u + sx / 2 + cpp, ctop), (u - sx / 2 - cpp, ctop)],
                                     z - sz / 2 - cpp, z + sz / 2 + cpp, P, "coping", "coping", "coping"))
        polys = k5.union_all(k5._snap(solids))
        pts, tris = _weld_shell(*k5.close(polys))
        self.stacks = []
        self.roof_shell = (pts, tris)
        self.roof_graph = k5.graph(pts, tris, kit)
        self.dressed = {"ridge": 0, "hip": 0, "valley": 0}   # a deck has no line for K04 to cap
        self.front_parapet_u = D - tw - 1e-6          # _emit_shell: the blocking course is the front's
        # T-2577: under a stone finish the street cornice box is the front's dressed stone, as
        # every picture of the front shows it under the lattice, not the eave's painted timber
        self.stone_cornice_u = D - 1e-6 if finish else math.inf
        self._emit_shell(*self.k14_roof_rows(pts, tris), seed, conf)
        if bal:
            self.flat_balustrade(bal, D, W, E + bal["plinth_m"] + cp, top, tw, seed, conf)
        return yf

    def flat_balustrade(self, bal, D, W, y0, top, tw, seed, conf):
        """T-1879: the balusters and rail of a blocking course pierced as a balustrade (1721's
        recessed front, the 1891 plate), in the front's trim stone: square balusters on the
        plinth's coping, centred in the course's thickness, under a rail the course's thickness
        and `rail_m` deep whose top is the course's, run between the solid lengths either side."""
        s0, s1, b, rail = bal["from_s_m"], bal["to_s_m"], bal["bar_m"], bal["rail_m"]
        # the street front's frame: u = D its face, s along it to the north (-z), N out to the street
        R, N = (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)
        self.proud_box("limestone_trim", ((D - tw, 0.0, 0.0), R, N), s0, s1, top - rail, top, tw, seed, conf)
        n = max(1, round((s1 - s0) / bal["pitch_m"]) - 1)
        pitch = (s1 - s0) / (n + 1)
        for i in range(1, n + 1):
            x = s0 + i * pitch
            self.proud_box("limestone_trim", ((D - tw / 2 - b / 2, 0.0, 0.0), R, N), x - b / 2, x + b / 2,
                           y0, top - rail, b, seed, conf)

    # role -> material: what the union named each face, and what a renderer binds to it
    SHELL = {"covering": "slate_covering", "cheek": "slate_covering", "fascia": "fascia",
             "soffit": "fascia", "verge": "fascia", "return": "fascia", "dormer_face": "dormer_stone",
             "reveal": "dormer_stone", "backing": "backing", "chimney": "brick", "coping": "limestone_trim",
             "parapet": "brick"}   # T-2350: a flat roof's side parapets; its blocking course is the front's
    # T-2313: the K15 stack's roles. Shaft and courses wear the side walls' K03 brick, the
    # cap the front's limestone trim, the flues the dark of a window's backing, the
    # flashing and cricket the roof's own K04 flashing (`_flashing`); soot is its own slot
    STACK = {"shaft_brick": "brick", "corbel_brick": "brick", "panel": "brick", "soot": "chimney_soot",
             "shaft_stone": "rough_stone_trim", "corbel_stone": "rough_stone_trim",
             "cap_stone": "limestone_trim", "band": "limestone_trim", "dentil": "limestone_trim",
             "cap_cement": "limestone_trim", "flue": "backing", "pot": "chimney_pot",
             "flashing": None, "cricket": None}
    BOARD = ("wall", "base")   # the body under the roof: the walls' own business
    OPEN = ("window",)         # the sash recess's back: the K06 opening set in it closes it

    def dressed_stack(self, k5, c, y0):
        """T-3109: a stone stack with a dressed base and head (1801's two south stacks, HABS
        photograph 1): one solid of plan rings from the cornice up, the base `base_proud_m`
        proud to `base_top_m` and weathered back to the shaft, a moulded collar, the stage
        over it and the moulded cap, each step splayed a few centimetres rather than
        stepped flat; then the stage's diamond lattice, two crossed zigzags of raised ribs
        on each face, `diamonds` whole diamonds across it."""
        h = c["head"]
        sx, sz = c["plan_m"]
        u, z, top = c["u_m"], -c["v_m"], c["top_m"]
        cp, cd = c["cap_proud_m"], c["cap_depth_m"]

        def ring(d):
            return [(u - sx / 2 - d, z - sz / 2 - d), (u + sx / 2 + d, z - sz / 2 - d),
                    (u + sx / 2 + d, z + sz / 2 + d), (u - sx / 2 - d, z + sz / 2 + d)]
        sp = 0.03                                    # a moulding's splay
        ys1 = top - cd                               # the stage's top, under the cap
        yc1 = ys1 - h["stage_depth_m"]               # the collar's top
        yc0 = yc1 - h["collar_depth_m"]
        bp, cl, st = h["base_proud_m"], h["collar_proud_m"], h["stage_proud_m"]
        rings = [(y0, ring(bp)), (h["base_top_m"] - h["weathering_m"], ring(bp)), (h["base_top_m"], ring(0.0)),
                 (yc0, ring(0.0)), (yc0 + sp, ring(cl)), (yc1 - sp, ring(cl)), (yc1, ring(st)),
                 (ys1, ring(st)), (ys1 + min(0.08, cd / 3), ring(cp)), (top, ring(cp))]
        roles = ["shaft_stone", "corbel_stone", "shaft_stone", "band", "band", "band", "shaft_stone",
                 "cap_stone", "cap_stone"]
        solids = [k5.ring_stack(rings, roles, "shaft_stone", "cap_stone")]
        n = h["diamonds"]
        if not n:
            return solids
        ya, yb, rw, rp = yc1, ys1, h["rib_m"], h["rib_proud_m"]

        def clip(poly, lo, hi):   # Sutherland-Hodgman against lo <= a <= hi
            for keep, edge in ((lambda q: q[0] >= lo, lo), (lambda q: q[0] <= hi, hi)):
                out = []
                for i, q in enumerate(poly):
                    p_ = poly[i - 1]
                    if keep(q) != keep(p_):
                        t = (edge - p_[0]) / (q[0] - p_[0])
                        out.append((edge, p_[1] + t * (q[1] - p_[1])))
                    if keep(q):
                        out.append(q)
                poly = out
            return poly
        # each face: (frame, the face's own across-centre, its half width, its plane, outward sign)
        faces = [(k5.frame("z"), u, sx / 2 + st, z + sz / 2 + st, 1.0), (k5.frame("z"), u, sx / 2 + st, z - sz / 2 - st, -1.0),
                 (k5.frame("x"), z, sz / 2 + st, u + sx / 2 + st, 1.0), (k5.frame("x"), z, sz / 2 + st, u - sx / 2 - st, -1.0)]
        for P, mid, half, plane, sgn in faces:
            step = 2 * half / n
            for i in range(n):
                a0 = mid - half + i * step
                for (pa, pb) in (((a0, ya), (a0 + step / 2, yb)), ((a0 + step / 2, yb), (a0 + step, ya)),
                                 ((a0, yb), (a0 + step / 2, ya)), ((a0 + step / 2, ya), (a0 + step, yb))):
                    poly = clip([(pa[0] - rw / 2, pa[1]), (pa[0] + rw / 2, pa[1]),
                                 (pb[0] + rw / 2, pb[1]), (pb[0] - rw / 2, pb[1])], mid - half, mid + half)
                    c0, c1 = sorted((plane - sgn * 0.01, plane + sgn * rp))
                    solids.append(k5.extrude(poly, c0, c1, P, "band", "band", "band"))
        return solids

    def _in_stone_stack(self, tri):
        """T-3003: whether a stack face's centroid lies in a stone stack's plan box."""
        cx, cz = (tri[0][0] + tri[1][0] + tri[2][0]) / 3, (tri[0][2] + tri[1][2] + tri[2][2]) / 3
        return any(b[0] <= cx <= b[1] and b[2] <= cz <= b[3] for b in getattr(self, "stone_stack_boxes", ()))

    def _in_gable_dormer(self, tri):
        """T-2452: whether a face's centroid lies in a gabled lower-face dormer's plan box."""
        cx, cz = (tri[0][0] + tri[1][0] + tri[2][0]) / 3, (tri[0][2] + tri[1][2] + tri[2][2]) / 3
        # T-3186: a turned dormer's box is tested in the frame it was built in
        turned = [((cx - mx) * nx + (cz - mz) * nz, -(cx - mx) * nz + (cz - mz) * nx, b)
                  for mx, mz, nx, nz, b in getattr(self, "gable_dormer_turns", ())]
        return any(b[0] - 1e-6 <= cx <= b[1] + 1e-6 and b[2] - 1e-6 <= cz <= b[3] + 1e-6
                   for b in getattr(self, "gable_dormer_boxes", ())) or \
            any(b[0] - 1e-6 <= x <= b[1] + 1e-6 and b[2] - 1e-6 <= z <= b[3] + 1e-6 for x, z, b in turned)

    def _emit_shell(self, pts, tris, seed, conf):
        """Each triangle into its material, with metric UVs: a covering's courses run up
        its own plane from that plane's lowest point (its eave), so a course is never cut
        at the eave and every fragment the union left of one plane registers."""
        k = self.p.roof or {}
        phase = (_k04_fabric(k["covering"]) or {}).get("course_phase_m", [0.0, 0.0])[1] if k else None
        # T-2406: a mansard whose lower faces are slated: every covering face steeper than
        # 45 degrees is a lower face (the crown's too); the upper hip keeps the covering
        lower = k.get("lower_covering")
        lower_phase = (_k04_fabric(lower) or {}).get("course_phase_m", [0.0, 0.0])[1] if lower else None
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
            if role in self.STACK:
                mat = self.STACK[role] or self._flashing()
            elif role == "parapet" and self.p.stone and (self.p.stone.get("all_round") or min(
                    q[0] for q in (pts[a], pts[b], pts[c])) >= getattr(self, "front_parapet_u", math.inf)):
                mat = "rough_stone_trim"                  # T-2350: the blocking course, in the front's stone;
                                                          # T-2788: every parapet, on an all-stone house
            elif role == "parapet" and self.front_brick != "brick" and min(
                    q[0] for q in (pts[a], pts[b], pts[c])) >= getattr(self, "front_gable_u", math.inf):
                mat = self.front_brick                    # T-3093: the shaped gable's brick, the front's
            elif role in ("soffit", "fascia") and min(q[0] for q in (pts[a], pts[b], pts[c])) \
                    >= getattr(self, "stone_cornice_u", math.inf):
                mat = "dress_stone"                       # T-2577: the cornice box, in the front's stone
            elif role == "chimney" and self._in_stone_stack((pts[a], pts[b], pts[c])):
                mat = "rough_stone_trim"                  # T-3003: a stack laid in the walls' stone
            elif role not in self.SHELL:
                raise ValueError(f"the K05 union left a {role!r} face on the roof")
            else:
                mat = self.SHELL[role]
            if role == "cheek" and lower and self._in_gable_dormer((pts[a], pts[b], pts[c])):
                mat = "mansard_slate"
            tri = [pts[a], pts[b], pts[c]]
            steep = role == "covering" and lower and n[1] < math.cos(math.radians(45))
            if steep:
                mat = "mansard_slate"
            if role == "covering":
                key = tuple(round(x, 5) for x in n) + (round(_dot(n, pts[a]), 4),)
                up = _unit(_sub(Y, _mul(n, n[1])))
                contour = _unit(_cross(up, n))
                b_ = self.basis(mat, planes[key], contour, up, seed, course_v=lower_phase if steep else phase)
            elif abs(n[1]) > 0.999:
                b_ = self.basis(mat, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), seed)
            else:
                au = _unit(_cross(Y, n))
                b_ = self.basis(mat, (0.0, 0.0, 0.0), au, _cross(n, au), seed)
            self.prim(mat).face(tri, n, b_, conf)

    # T-2411: a lower face's frame — the axis its dormers run back along ("x" or "z", the
    # K05 frame), its outward sign on that axis, and R, the wall direction a viewer facing
    # the face reads to the right (the K01 walls' own: k01_frontage.walls)
    DORMER_FACES = {"street": ("x", 1.0, (0.0, 0.0, -1.0)), "rear": ("x", -1.0, (0.0, 0.0, 1.0)),
                    "north": ("z", -1.0, (-1.0, 0.0, 0.0)), "south": ("z", 1.0, (1.0, 0.0, 0.0))}

    def round_dormer_body(self, d, face, fascia, centre, rise, lower_pitch_deg, bulge, E, profile=None,
                          back_at=None):
        """A round-headed dormer as a closed solid for the roof's union (T-2404's crown
        dormer; T-2411 on the main mansard's lower faces) — a stone face on the lower face,
        `face_setback_m` in from the fascia's face (`fascia`, on the face's axis), its head
        the sash's own arch carried out by the surround, run back through the lower face —
        and the recess its K06 sash stands in, cut to K06's own outline so the opening's
        reveal is the solid's. `centre` is its centre along the face, in the K01 frame."""
        from . import k05_roofs as k5
        from . import k06_windows
        from archetypes.k01_frontage_params import HIPPED_HEADS, mansard_face_height
        axis, sg, R = self.DORMER_FACES[face]
        ra = R[2] if axis == "x" else R[0]           # R along the face's own coordinate
        run = rise / math.tan(math.radians(lower_pitch_deg))
        ys = E + mansard_face_height(d["face_setback_m"], rise, lower_pitch_deg, bulge,
                                     profile or self.p.mansard["profile"])
        nf = fascia - sg * d["face_setback_m"]       # the face's plane
        # K06's own hole: the sash's outline at the outer face, about its sill socket
        v = dict(next(x for x in k06_windows.load()["variants"] if x["id"] == d["variant"]))
        v["clear_width_m"], v["clear_height_m"] = d["sash_width_m"], d["sash_height_m"]
        o = k06_windows.Opening(v, k06_windows.load())
        o.build()
        hole = o.holes[0]
        sill = ys + d["sill_m"]
        r = d["width_m"] / 2
        top = sill + d["head_m"]
        if d.get("head") == "gable":
            # T-2452: jambs to the surround's head over the square-headed sash, then the
            # pediment's two slopes to its apex, slated as the cheeks are
            eaves = sill + d["sash_height_m"] + d["surround_m"]
            head = [(centre + r, eaves), (centre, top), (centre - r, eaves)]
        elif d.get("head") in HIPPED_HEADS:
            # T-2866: square to the face's wall head; the hip (T-2902: or flat hood) over it is joined below
            head = [(centre + r, top), (centre - r, top)]
        elif d.get("head") == "hood":
            # T-3000: square to the face's wall head under the shelf; the hood over it is joined below
            eaves = sill + d["sash_height_m"] + d["surround_m"]
            head = [(centre + r, eaves), (centre - r, eaves)]
        else:
            # the face's outline across the face: jambs to the sash's spring, then a half
            # circle struck from the sash's own centre, `surround_m` outside its arch
            spring = sill + d["sash_height_m"] - d["sash_width_m"] / 2
            head = [(centre + r * math.cos(math.pi * i / 12), spring + r * math.sin(math.pi * i / 12))
                    for i in range(13)]
        outline = [(centre - r, ys - 0.4), (centre + r, ys - 0.4)] + head
        back = fascia - sg * (run + 0.3) if back_at is None else back_at
        P = k5.frame(axis)
        ends = ("hidden", "dormer_face") if sg > 0 else ("dormer_face", "hidden")
        # T-2866: a hipped dormer's cheeks are its face's (1625's print draws both pale, where
        # its slates read dark); the others' are slated, as the K01 dormer's are
        slated = (d.get("hood") or {}).get("face") == "slate"   # T-1890: 1801's slated faces
        body = k5.extrude(outline, min(back, nf), max(back, nf), P,
                          "dormer_face" if d.get("head") in HIPPED_HEADS + ("hood",) and not slated else "cheek",
                          *(("hidden", "cheek") if sg > 0 else ("cheek", "hidden")) if slated else ends)
        if d.get("head") == "gable":
            # T-2452: its cheeks and pediment slopes are slated as the lower faces are (_emit_shell
            # reads a cheek inside this box as one of them), its plan box in the K01 frame
            a0, a1 = sorted((back, nf))
            box = (a0, a1, centre - r, centre + r) if axis == "x" else (centre - r, centre + r, a0, a1)
            self.gable_dormer_boxes = getattr(self, "gable_dormer_boxes", []) + [box]
        rev = v.get("overrides", {}).get("reveal_depth_m", k06_windows.load()["parts"]["reveal_depth_m"]["value"])
        # the hole in the kit's frame is (+X along the wall, +Y up), +X being the face's R
        rec = [(centre + ra * q[0], sill + q[1]) for q in hole]
        inner, outer = nf - sg * rev, nf + sg * 0.05
        recess = k5.extrude(rec, min(inner, outer), max(inner, outer), P, "reveal",
                            *(("window", "reveal") if sg > 0 else ("reveal", "window")))
        at = lambda along, y, n: (n, y, along) if axis == "x" else (along, y, n)
        roof, hood = None, []
        if d.get("head") in HIPPED_HEADS:
            # T-2866: K05's hip over the dormer's wall-line rectangle, its soffit on the face's
            # wall head and its eaves the kit's dormer overhang; its back end dies into the
            # main roof, which the record's resolve ran the body far enough back to bury
            a0, a1 = sorted((back, nf))
            x0, x1, z0, z1 = (a0, a1, centre - r, centre + r) if axis == "x" else (centre - r, centre + r, a0, a1)
            t = math.tan(math.radians(d["hip_pitch_deg"]))
            roof, _ = k5.hip_element(x0, x1, z0, z1, top + d["overhang_m"] * t + d["fascia_m"], t,
                                     d["overhang_m"], d["fascia_m"])
        if d.get("head") == "hood":
            hood = self.dormer_hood(d, k5, axis, sg, nf, back, centre, r, eaves, top)
            top = eaves   # the face, as the K01 dormer face is registered, stops under the shelf
            if slated:
                hood += self.dormer_frame(d, k5, axis, sg, nf, centre, sill)
        return {"body": body, "recess": recess, "roof": roof, **({"hood": hood} if hood else {}),
                "geom": {"O": at(centre - ra * r, ys, nf), "R": R, "ys": ys, "sill": sill,
                         "sill_pt": at(centre, sill, nf), "top_pt": at(centre, top, nf),
                         "width": 2 * r, "top": top, "variant": v, "d": d}}

    HOOD_LIP_M = 0.03    # T-3000: the shelf stands this far past the face's cheeks
    HOOD_BED_M = 0.03    # ... and is bedded this far down the face's head, so the two overlap
    HOOD_BACK_M = 0.05   # ... and both it and the hood stop this far short of the face's back,
                         # all three buried in the roof

    def dormer_hood(self, d, k5, axis, sg, nf, back, centre, r, eaves, top):
        """T-3000: a hooded dormer's shelf and hood as closed solids for the roof's union. The
        shelf is `shelf_m` deep over the face's head, `shelf_proud_m` out of its front and
        HOOD_LIP_M past its cheeks. The hood stands on it, as wide as the face at its foot,
        and rises `rise_m` to a level top that runs on into the roof (which buries it), its
        slated front falling `lean_m` back and each cheek leaning `taper_m` in, so the front
        narrows as it climbs, as the print's do. T-1890: a hood with `flare_m` stands that much
        wider than the face each side at its foot and that much out in front of it, its shelf
        with it, and sweeps in from there to the same top. Both plan boxes are a gabled
        dormer's: the hood's slate is the lower faces' own."""
        h = d["hood"]
        fl = h.get("flare_m", 0.0)
        y0, y1 = eaves - self.HOOD_BED_M, eaves + h["shelf_m"]
        bk = back + sg * self.HOOD_BACK_M
        out = nf + sg * (h["shelf_proud_m"] + fl)
        rh, rt = r + fl + self.HOOD_LIP_M, r - h["taper_m"]
        P = k5.frame("z" if axis == "x" else "x")   # (out, up, along) for a face whose out is `axis`
        shelf = k5.extrude([(bk, y0), (out, y0), (out, y1), (bk, y1)], centre - rh, centre + rh, P,
                           lambda i, p_, q_: "hidden" if abs(p_[0] - bk) < 1e-9 and abs(q_[0] - bk) < 1e-9
                           else "dormer_face", "dormer_face", "dormer_face")
        # the hood: bedded HOOD_BED_M into the shelf, its eight corners (out, up, along)
        yb, nt, hb = y1 - self.HOOD_BED_M, nf - sg * h["lean_m"], bk + sg * 0.02
        nb = nf + sg * fl
        c = {(f, t, s): P(*((nb if f else hb) if not t else (nt if f else hb),
                            top if t else yb, centre + s * (rt if t else r + fl)))
             for f in (0, 1) for t in (0, 1) for s in (-1, 1)}
        mid = P((nf + hb) / 2, (yb + top) / 2, centre)
        hood = []
        for quad, role in (([c[0, 0, -1], c[1, 0, -1], c[1, 0, 1], c[0, 0, 1]], "hidden"),   # its bed
                           ([c[0, 1, -1], c[1, 1, -1], c[1, 1, 1], c[0, 1, 1]], "cheek"),    # its top
                           ([c[1, 0, -1], c[1, 0, 1], c[1, 1, 1], c[1, 1, -1]], "cheek"),    # its front
                           ([c[0, 0, -1], c[0, 0, 1], c[0, 1, 1], c[0, 1, -1]], "hidden"),   # its back
                           ([c[0, 0, -1], c[1, 0, -1], c[1, 1, -1], c[0, 1, -1]], "cheek"),  # a cheek
                           ([c[0, 0, 1], c[1, 0, 1], c[1, 1, 1], c[0, 1, 1]], "cheek")):     # the other
            ctr = tuple((quad[0][k] + quad[1][k] + quad[2][k] + quad[3][k]) / 4 for k in range(3))
            pl = k5.oriented(quad, role, tuple(ctr[k] - mid[k] for k in range(3)))
            if pl:
                hood.append(pl)
        a0, a1 = sorted((bk, out))
        box = (a0, a1, centre - rh, centre + rh) if axis == "x" else (centre - rh, centre + rh, a0, a1)
        self.gable_dormer_boxes = getattr(self, "gable_dormer_boxes", []) + [box]
        return [shelf, hood]

    FRAME_PROUD_M = 0.04   # T-1890: a slated face's stone frame stands this far out of it
    FRAME_BED_M = 0.02     # ... and is bedded this far into it

    def dormer_frame(self, d, k5, axis, sg, nf, centre, sill):
        """T-1890: a slated dormer face's pale stone frame round its light, as closed solids for
        the roof's union: a sill, a head and two jambs `frame_m` wide, standing FRAME_PROUD_M
        out of the face round the sash's square outline (1801's, the Taylor print and HABS 1)."""
        fm, sw, sht = d["hood"]["frame_m"], d["sash_width_m"], d["sash_height_m"]
        a, b = sorted((nf - sg * self.FRAME_BED_M, nf + sg * self.FRAME_PROUD_M))
        P = k5.frame(axis)
        x0, x1, y0, y1 = centre - sw / 2, centre + sw / 2, sill, sill + sht
        bars = ([(x0 - fm, y0 - fm), (x1 + fm, y0 - fm), (x1 + fm, y0), (x0 - fm, y0)],     # its sill
                [(x0 - fm, y1), (x1 + fm, y1), (x1 + fm, y1 + fm), (x0 - fm, y1 + fm)],     # its head
                [(x0 - fm, y0), (x0, y0), (x0, y1), (x0 - fm, y1)],                         # a jamb
                [(x1, y0), (x1 + fm, y0), (x1 + fm, y1), (x1, y1)])                         # the other
        ends = ("hidden", "dormer_face") if sg > 0 else ("dormer_face", "hidden")
        return [k5.extrude(q, a, b, P, "dormer_face", *ends) for q in bars]

    def crown_dormer_body(self, cr, E, f):
        """T-2404: the crown's round-headed dormer, on the crown's street face, centred on it."""
        g = self.round_dormer_body(cr["dormer"], "street", cr["x1"] + cr["overhang_m"], (cr["z0"] + cr["z1"]) / 2,
                                   cr["lower_rise_m"], cr["lower_pitch_deg"], cr["bulge"], E)
        self.round_dormers.append(g["geom"])
        return g

    def mansard_dormer_bodies(self, m, E):
        """T-2411: the main mansard's lower-face dormers, each on the face the record names."""
        D, W, o = self.p.depth_m, self.p.width_m, self.p.eave_overhang_m
        fascia = {"street": D + o, "rear": -o, "north": -W - o, "south": o}
        out = []
        for d in m.get("dormers", ()):
            if d["face"] == "cant":   # T-3186: a street dormer, turned onto the canted face
                g = self.cant_dormer_body(d, m, E)
                self.round_dormers.append(g["geom"])
                out.append(g)
                continue
            centre = d["along_m"] if self.DORMER_FACES[d["face"]][0] == "z" else -d["along_m"]
            g = self.round_dormer_body(d, d["face"], fascia[d["face"]], centre, m["lower_rise_m"],
                                       m["lower_pitch_deg"], m["bulge"], E)
            self.round_dormers.append(g["geom"])
            out.append(g)
        return out

    def cant_dormer_body(self, d, m, E):
        """T-3186: the canted corner's dormer: built as a street dormer whose face's fascia line
        crosses the axis at the origin, then turned about the vertical onto the canted face's
        normal and moved to the middle of the face's fascia line, its sash's frame with it. A
        gabled one's plan box goes with its turn (`gable_dormer_turns`), so its cheeks are slated."""
        from . import k05_roofs as k5
        D, W, o = self.p.depth_m, self.p.width_m, self.p.eave_overhang_m
        plan = k01_frontage_params.cant_corner_plan(self.p.cant_corner, D, W)
        (u0, v0), (u1, v1) = plan["ends"]
        nx, nz = plan["normal"][0], -plan["normal"][1]
        mx, mz = (u0 + u1) / 2 + nx * o, -(v0 + v1) / 2 + nz * o
        boxes = len(getattr(self, "gable_dormer_boxes", []))
        g = self.round_dormer_body(d, "street", 0.0, 0.0, m["lower_rise_m"], m["lower_pitch_deg"], m["bulge"], E)
        turn = lambda q: (mx + q[0] * nx - q[2] * nz, q[1], mz + q[0] * nz + q[2] * nx)
        vec = lambda q: (q[0] * nx - q[2] * nz, q[1], q[0] * nz + q[2] * nx)
        for key in ("body", "recess"):
            g[key] = [k5.Poly([turn(q) for q in pl.v], pl.role) for pl in g[key]]
        for key in ("O", "sill_pt", "top_pt"):
            g["geom"][key] = turn(g["geom"][key])
        g["geom"]["R"] = vec(g["geom"]["R"])
        if len(getattr(self, "gable_dormer_boxes", [])) > boxes:
            self.gable_dormer_turns = getattr(self, "gable_dormer_turns", []) + \
                [(mx, mz, nx, nz, self.gable_dormer_boxes.pop())]
        return g

    def slope_dormer_bodies(self, E, tp):
        """T-2866: the hip's side-slope dormers (1625's on its open south side), each the
        lower-face dormer's construction on the hip's plane: the covering at the fascia's face
        stands `o` of run under the wall head, so a face `face_setback_m` in from it leaves the
        slope where the straight chord says, and its body runs `back_m` in from the wall line."""
        W, o = self.p.width_m, self.p.eave_overhang_m
        fascia = {"north": -W - o, "south": o}
        wall = {"north": -W, "south": 0.0}
        out = []
        for d in self.p.slope_dormers:
            sg = self.DORMER_FACES[d["face"]][1]
            g = self.round_dormer_body(d, d["face"], fascia[d["face"]], d["along_m"], W / 2 * tp,
                                       self.p.roof_pitch_deg, 0.0, E - o * tp, profile="convex",
                                       back_at=wall[d["face"]] - sg * d["back_m"])
            self.round_dormers.append(g["geom"])
            out.append(g)
        return out

    def round_dormer_sash(self, g, conf):
        """A lower-face dormer's K06 sash in the recess the union cut (its reveal is the
        solid's), the face registered as the K01 dormer face it is (T-2404, T-2411; a
        gabled one's square-headed sash, T-2452)."""
        from . import k06_windows
        from archetypes.k01_frontage_params import Opening
        d, O, R = g["d"], g["O"], g["R"]
        head = d.get("head", "round")
        self.instance("k01.wall.dormer_face", "wall", {"length_m": g["width"], "height_m": round(g["top"] - g["ys"], 4),
                                                       "construction": "masonry", "openings": 1, "head": head},
                      {"base": O, "top": g["top_pt"]})
        op = Opening("k01.opening.sash_round" if head == "round" else "k01.opening.sash_flat",
                     "k01.wall.dormer_face", g["width"] / 2, g["sill"] - g["ys"],
                     d["sash_width_m"], d["sash_height_m"])
        frame = (O, R, _cross(R, Y))
        seed = self.instance(op.component, "opening", {"clear_width_m": op.width_m, "clear_height_m": op.height_m,
                                                       "k06_variant": d["variant"], "wall": op.wall},
                             {"sill": g["sill_pt"]})
        if not hasattr(self, "_kit"):
            self._kit = k06_windows.load()
        o = k06_windows.Opening(g["variant"], self._kit)
        o.seed = seed
        o.build()
        roles = {r: ("limestone_trim" if m == "stone" else (m or "dormer_stone")) for r, m in self.K06_ROLES.items()}
        self.graft(o, "K06", roles, frame, op, lambda role: (seed, conf), ("reveal",))

    def dormer_sash(self, roof_seed):
        """The dormer's face: a K01 wall component whose surface is the union's, and its
        sash set in the recess the union cut (the reveal is the solid's, K06 the rest)."""
        p, d, g = self.p, self.p.dormer, self.dormer_geom
        if d.get("wall_gable"):     # T-2428: its lights, voussoirs, pinnacles and finial
            from . import k01_wall_gable
            return k01_wall_gable.dress(self, roof_seed)
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
            # a triangle whose edge on the line overlaps A-B: T-2404's crown is cut by the main
            # roof's union mid-hip, so a hip's short piece can lie inside a longer edge
            on = []
            for q in (pts[a], pts[b], pts[c]):
                s = _dot(_sub(q, A), L) / LL
                e = _sub(_sub(q, A), _mul(L, s))
                if _dot(e, e) < 1e-8:
                    on.append(s)
            if len(on) >= 2 and min(on) < 1 - 1e-6 and max(on) > 1e-6 \
                    and not any(_dot(n, m) > 0.9999 for m in out):
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
            # T-2370: a mansard's lower hip bends with the face's curve, and K05's graph keeps
            # only its ends, so it is capped a segment at a time, ring corner to ring corner
            # T-2404: a crown's faces meet the main roof's curved faces in a bent valley too
            spans = (self._bent_hip(pts, tris, A, B) if kind == "hip" else self._bent_valley(pts, tris, A, B)) \
                if self.p.mansard and kind in ("hip", "valley") else [(A, B)]
            for A, B in spans:
                ns = self._line_planes(pts, tris, A, B)
                if len(ns) == 1:
                    # T-2866: a SEAM, not a fold — one covering plane on both sides of the line.
                    # The union's BSP splits a face by every other solid's planes, and a split
                    # can leave a sliver whose three corners are all but collinear, so the
                    # normal K05's graph computes from them is noise and it reads a ridge, hip
                    # or valley there (1625's attic face, once its south dormer joined). The
                    # face's own plane says it is flat; there is nothing to cap or flash
                    continue
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

    @staticmethod
    def _bent_hip(pts, tris, A, B):
        """The segments of a hip from A up to B through the covering's vertices on its
        vertical plane: one span on a straight hip, a span per ring on a mansard's curved
        lower hip."""
        dx, dz = B[0] - A[0], B[2] - A[2]
        L = math.hypot(dx, dz)
        if L < 1e-9:
            return [(A, B)]
        # the shell's own vertices, unrounded (the graph's ends are rounded to 0.1 mm, too
        # coarse for a span this short to find its planes)
        used = sorted({i for t in tris if t[3] == "covering" for i in t[:3]})
        snap = lambda e: min(used, key=lambda i: math.dist(pts[i], e))
        plane = lambda q: abs((q[0] - A[0]) * dz - (q[2] - A[2]) * dx) / L < 1e-3
        # T-2404: walk the covering's own edges up the hip's vertical plane. Every vertex on
        # that plane used to be chained by height, which held while the hip was the only
        # thing there; a crown joined into the roof leaves intersection vertices on the same
        # plane that are not on the hip, and a chain through them is no line of the roof
        adj = {}
        for t in tris:
            if t[3] == "covering":
                for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    adj.setdefault(a, set()).add(b)
                    adj.setdefault(b, set()).add(a)
        cur, end = snap(A), snap(B)
        chain = [cur]
        while cur != end:
            nxt = [j for j in adj.get(cur, ()) if plane(pts[j]) and pts[cur][1] + 1e-6 < pts[j][1] <= pts[end][1] + 1e-4]
            if not nxt:
                break
            cur = min(nxt, key=lambda j: pts[j][1])
            chain.append(cur)
        if chain[-1] != end:   # no edge path: the old reading, every vertex on the plane
            on = {snap(A), end} | {i for i in used if A[1] + 1e-4 < pts[i][1] < B[1] - 1e-4 and plane(pts[i])}
            chain = sorted(on, key=lambda i: pts[i][1])
        chain = [tuple(pts[i]) for i in chain]
        return list(zip(chain, chain[1:]))

    @staticmethod
    def _bent_valley(pts, tris, A, B):
        """T-2404: the segments of a valley from A up to B along the covering's own creases.
        Where a crown's curved face meets the main mansard's curved face the valley bends at
        every ring of either, and K05's graph keeps only its ends; each step takes the crease
        edge that climbs and comes nearer B."""
        cov = [t for t in tris if t[3] == "covering"]
        faces = {}
        for t in cov:
            n = t[4]
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                faces.setdefault((min(a, b), max(a, b)), []).append(n)
        adj = {}
        for (a, b), ns in faces.items():
            if len(ns) == 2 and _dot(ns[0], ns[1]) < 0.9999:
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
        if not adj:
            return [(A, B)]
        ends = sorted(adj)
        cur = min(ends, key=lambda i: math.dist(pts[i], A))
        end = min(ends, key=lambda i: math.dist(pts[i], B))
        chain = [cur]
        while cur != end:
            nxt = [j for j in adj[cur] if pts[cur][1] + 1e-6 < pts[j][1] <= pts[end][1] + 1e-4
                   and math.dist(pts[j], pts[end]) < math.dist(pts[cur], pts[end])]
            if not nxt:
                return [(A, B)]
            cur = min(nxt, key=lambda j: math.dist(pts[j], pts[end]))
            chain.append(cur)
        chain = [tuple(pts[i]) for i in chain]
        return list(zip(chain, chain[1:]))

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
    def cant_gutter(self, A):
        """T-3186: the eave gutter's runs round a house with a canted corner: the wall line's five
        sides (the face between the two walls it cuts) each moved `A` out, as rainwater() reads
        them — each run's start, direction, outward side and length, the run each wall's pipes
        stand on, and how far along it that wall's s = 0 stands."""
        D, W = self.p.depth_m, self.p.width_m
        (u0, v0), (u1, v1) = k01_frontage_params.cant_corner_plan(self.p.cant_corner, D, W)["ends"]
        line = [(D, 0.0), (D, -W), (0.0, -W), (0.0, 0.0)]
        names = ["k01.wall.street_front", "k01.wall.side.north", "k01.wall.rear_service", "k01.wall.side.south"]
        origin = dict(zip(names, line))
        i = 1 if self.p.cant_corner["corner"] == "north" else 0
        line[i:i + 1] = [(u0, -v0), (u1, -v1)]
        if i == 0:   # the south corner: the front starts at the face's end, the face closes the loop
            line = line[1:] + line[:1]
        names.insert(1 if i == 1 else 4, k01_frontage_params.CANT_WALL)
        n = len(line)
        sides = []
        for j in range(n):
            (ax, az), (bx, bz) = line[j], line[(j + 1) % n]
            L = math.hypot(bx - ax, bz - az)
            d = ((bx - ax) / L, (bz - az) / L)
            o = (-d[1], d[0])                               # outward: the wall line runs clockwise from above
            sides.append(((ax + o[0] * A, az + o[1] * A), d, o))
        corners = []
        for j in range(n):
            (pa, da, _), (pb, db, _) = sides[j - 1], sides[j]
            den = da[0] * db[1] - da[1] * db[0]
            t = ((pb[0] - pa[0]) * db[1] - (pb[1] - pa[1]) * db[0]) / den
            corners.append((pa[0] + da[0] * t, pa[1] + da[1] * t))
        lens = [math.hypot(corners[(j + 1) % n][0] - corners[j][0], corners[(j + 1) % n][1] - corners[j][1])
                for j in range(n)]
        dirs = [(d[0], 0.0, d[1]) for _, d, _ in sides]
        outs = [(o[0], 0.0, o[1]) for _, _, o in sides]
        side_of = {w: j for j, w in enumerate(names)}
        lead = {w: (origin[w][0] - corners[side_of[w]][0]) * dirs[side_of[w]][0]
                + (origin[w][1] - corners[side_of[w]][1]) * dirs[side_of[w]][2] for w in origin}
        return corners, dirs, outs, lens, side_of, lead

    def rainwater(self, ye, yf, seed):
        p, r = self.p, self.p.rainwater
        if not r["downpipes"]:   # T-2919: a gable's front pipes alone, each from its own head
            self.rain_runs = []
            for x in r["front_pipes"]:
                self.front_pipe(x, "k04_" + r["fabric"], r["pipe_diameter_m"] / 2,
                                math.radians(r["shoe_kick_deg"]), p.worst_conf("rainwater", "eave_overhang_m"), seed)
            return
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
        side_of = {"k01.wall.street_front": 0, "k01.wall.side.north": 1, "k01.wall.rear_service": 2,
                   "k01.wall.side.south": 3}
        lead = {w: A for w in side_of}       # how far along its run a wall's s = 0 stands
        if p.cant_corner:
            corners, dirs, outs, lens, side_of, lead = self.cant_gutter(A)
        n_runs = len(lens)
        starts = [sum(lens[:i]) for i in range(n_runs)]
        P = sum(lens)
        outlets = sorted(starts[side_of[x["wall"]]] + lead[x["wall"]] + x["s_m"] for x in r["downpipes"])
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
            i = max(j for j in range(n_runs) if starts[j] <= sv + 1e-9)
            t = sv - starts[i]
            cx, cz = corners[i]
            return (cx + dirs[i][0] * t, y_at(sv), cz + dirs[i][2] * t), i, t

        n_seg = 8
        secs = [k_ * math.pi / n_seg for k_ in range(n_seg + 1)]

        def ring(sv, rad):
            pt, i, t = at(sv)
            out = outs[i]
            if t < 1e-6:  # a corner: the mitre between the side before and this one
                prev = outs[(i - 1) % n_runs]
                out = (out[0] + prev[0], 0.0, out[2] + prev[2])
                if p.cant_corner:   # T-3186: a canted corner's 135-degree turns, mitred true
                    k_ = 2.0 / (out[0] * out[0] + out[2] * out[2])
                    out = (out[0] * k_, 0.0, out[2] * k_)
            return [(pt[0] - math.cos(a) * rad * out[0], pt[1] - math.sin(a) * rad, pt[2] - math.cos(a) * rad * out[2])
                    for a in secs], pt

        # T-2778: the gutter stops in the cants of an oriel carried through the eave, each
        # end run into its wall where the gutter's outer lip meets it, and no hanger stands
        # inside it
        dead = []
        for b in p.bays:
            if b.get("through_eave"):
                q = self.through_eave_plan(b, self.THROUGH_EAVE_INSET_M)
                zo = A + ro + 0.01
                xs = [a[0] + (zo - a[1]) / (b_[1] - a[1]) * (b_[0] - a[0]) for a, b_ in zip(q, q[1:])
                      if (a[1] - zo) * (b_[1] - zo) < 0]
                if len(xs) != 2:
                    raise ValueError(f"{b['id']}: the gutter's lip at {zo:.3f} m out does not cross its cants")
                dead.append((A + min(xs), A + max(xs)))
        # T-3047: and across a shallow pavilion carried up past the eave, from its cheek to its
        # face round a corner it is flush with, each end stopped (`stop_ends`)
        stop_ends = []
        for b, s0, s1, proud, _ in self.shallow_bays():
            d0 = starts[3] + D + A + proud if b.get("flush_corner") == "left" else A + s0
            d1 = starts[1] + A - proud if b.get("flush_corner") == "right" else A + s1
            ch = k01_frontage_params.chamfer_of(b)   # T-3048: round a chamfer, at its back
            if ch is not None:
                d0, d1 = (starts[3] + D + A - ch[2], d1) if ch[0] == "left" else (d0, starts[1] + A + ch[2])
            if d0 > d1:
                dead += [(d0, P), (0.0, d1)]
            else:
                dead.append((d0, d1))
            stop_ends += [(d0 % P, 1.0), (d1 % P, -1.0)]
        if (p.shaped_gable or {}).get("takes_gutter"):
            # T-2889: no gutter across a front carried up as a shaped gable: the street run is
            # not built and each side run dies into the gable's base at its back (k01_shaped_gable)
            xb = self.shaped_gable_geom["xb"]
            dead += [(starts[3] + xb + A, P), (0.0, starts[1] + D + A - xb)]
        spp = (p.mansard or {}).get("side_parapet")
        if spp:
            # T-3061: no gutter along a side wall carried up as a parapet: the runs beside it
            # stop at the wall's outer plane, each end stopped where the run beside it is live
            i = 3 if spp["wall"] == "south" else 1
            d0, d1 = starts[i] - A, starts[i] + lens[i] + A
            live = lambda sv: not any(a - 1e-6 <= sv % P <= b + 1e-6 for a, b in dead)
            for sv, sign in ((d0, 1.0), (d1 % P, -1.0)):
                if live(sv - sign * 0.01):
                    stop_ends.append((sv % P, sign))
            dead += [(d0, P), (0.0, d1 - P)] if d1 > P else [(d0, d1)]
        if (p.mansard or {}).get("straight"):   # T-2995: no gutter along a straight wall's head
            from . import k01_mansard_straight
            more, ends = k01_mansard_straight.gutter_dead(p, A, starts, P)
            dead += more
            stop_ends += ends
        stations = sorted({*(round(x % P, 6) for x in starts), *(round(x, 6) for x in outlets),
                           *(round(x, 6) for x in highs), *(round(x, 6) for d in dead for x in d)})
        pr = self.prim(mat)
        for a_, b_ in zip(stations, stations[1:] + [stations[0] + P]):
            if any(d0 - 1e-6 <= (a_ + b_) / 2 <= d1 + 1e-6 for d0, d1 in dead):
                continue
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
        for sv, sign in stop_ends:   # T-3047: a stop end, the half-round closed across its lips
            arc, _ = ring(sv, ro)
            i = max(j for j in range(n_runs) if starts[j] <= sv + 1e-9)
            n = _mul(dirs[i], sign)
            pr.face(arc, n, self.basis(mat, arc[0], _unit(_sub(arc[-1], arc[0])), Y, seed), conf)
        # wrought-iron hangers at the bracket spacing, a band under the gutter and a leg
        # up the fascia, clear of the outlets
        iron = self.prim("iron")
        bw = r["bracket_section_m"][0] / 2
        rb = ro + r["bracket_section_m"][1] * 0.6
        for i in range(n_runs):
            t = 0.30
            while t < lens[i] - 0.30:
                sv = starts[i] + t
                t += r["bracket_spacing_m"]
                if min(cyc(sv, x) for x in outlets) < 0.15 or any(d0 - 0.1 <= sv <= d1 + 0.1 for d0, d1 in dead):
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
                 "k01.wall.side.south": ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
                 "k01.wall.side.north": ((D, 0.0, -W), (-1.0, 0.0, 0.0))}   # T-2753
        rp = r["pipe_diameter_m"] / 2
        kick = math.radians(r["shoe_kick_deg"])
        for x in r["downpipes"]:
            O, R = walls[x["wall"]]
            N = _cross(R, Y)
            # clear of anything proud of the wall: the street front's belt courses
            off = r["pipe_offset_from_wall_m"] + (0.05 if x["wall"] == "k01.wall.street_front" else 0.0)
            lat = off + rp
            base = _add(O, _mul(R, x["s_m"]))
            sv = starts[side_of[x["wall"]]] + lead[x["wall"]] + x["s_m"]
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
        for x in r.get("front_pipes", []):
            self.front_pipe(x, mat, rp, kick, conf, seed)

    def front_pipe(self, x, mat, rp, kick, conf, seed):
        """T-2953: a pipe down the street front from its own rainwater head (no eave gutter
        reaches it): a box head `head_m` up, the pipe straight down the face `proud_m` before
        the main front, strapped, to a shoe kicked out over a splash stone at grade, or (a
        `foot_m` over grade) over the lower roof it discharges onto.

        T-2997: `on: "return"` stands it on a projection's high-s return instead, `s_m` that
        face and `proud_m` its place along it: the same pipe built in the return's own frame
        (the front's turned a quarter about the vertical), so a front pipe is unchanged."""
        p, r = self.p, self.p.rainwater
        R, N = (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)
        if x.get("on") == "return":
            P = lambda l, y, z: (z, y, -l)            # l off the return (+s), z along it (u)
            V = lambda v: (v[2], v[1], -v[0])
            lat = x["s_m"] + r["pipe_offset_from_wall_m"] + 0.05 + rp
            zc = p.depth_m + x["proud_m"]
        else:
            P = lambda l, y, z: (l, y, z)
            V = lambda v: v
            lat = p.depth_m + x["proud_m"] + r["pipe_offset_from_wall_m"] + 0.05 + rp
            zc = -x["s_m"]
        R_, N_ = V(R), V(N)
        at_wall = lambda l, y: P(l, y, zc)
        hw, hh, hd = 0.14, 0.24, 0.09               # the head: half its width, its height, half its depth
        y_head = x["head_m"] - hh
        y4 = x["foot_m"] + r["shoe_end_above_grade_m"] + rp * math.cos(kick)
        y3 = y4 + r["shoe_length_m"] * math.sin(kick)
        self.tube(mat, [at_wall(lat, y_head + 0.02), at_wall(lat, y3),
                        at_wall(lat + r["shoe_length_m"] * math.cos(kick), y4)], rp, R_, seed, conf, cap_end=True)
        hp = self.prim(mat)
        lo, hi = (lat - hd, lat + hd), (y_head, x["head_m"])
        z0, z1 = zc - hw, zc + hw
        bx = P
        b = self.basis(mat, at_wall(lat, y_head), R_, Y, seed)
        hp.face([bx(lo[1], hi[0], z1), bx(lo[1], hi[0], z0), bx(lo[1], hi[1], z0), bx(lo[1], hi[1], z1)], N_, b, conf)
        hp.face([bx(lo[0], hi[0], z0), bx(lo[1], hi[0], z0), bx(lo[1], hi[1], z0), bx(lo[0], hi[1], z0)], R_, b, conf)
        hp.face([bx(lo[1], hi[0], z1), bx(lo[0], hi[0], z1), bx(lo[0], hi[1], z1), bx(lo[1], hi[1], z1)],
                _mul(R_, -1), b, conf)
        hp.face([bx(lo[0], hi[0], z0), bx(lo[0], hi[0], z1), bx(lo[1], hi[0], z1), bx(lo[1], hi[0], z0)],
                (0.0, -1.0, 0.0), b, conf)
        hp.face([bx(lo[0], hi[1], z1), bx(lo[0], hi[1], z0), bx(lo[1], hi[1], z0), bx(lo[1], hi[1], z1)], Y, b, conf)
        iron = self.prim("iron")
        yy = y_head - 0.4
        while yy > y3 + 0.3:
            c = at_wall(lat, yy)
            band = [_add(c, _add(_mul(R_, math.cos(a) * (rp + 0.004)), _mul(N_, math.sin(a) * (rp + 0.004))))
                    for a in [2 * math.pi * j / 8 for j in range(9)]]
            for j in range(8):
                mo = _sub(_mul(_add(band[j], band[j + 1]), 0.5), c)
                iron.quad(band[j], band[j + 1], _add(band[j + 1], (0.0, 0.03, 0.0)), _add(band[j], (0.0, 0.03, 0.0)),
                          mo, self.basis("iron", band[j], _unit(_sub(band[j + 1], band[j])), Y, seed), conf)
            yy -= r["strap_spacing_m"]
        if x["foot_m"] > 0.0:
            return
        st = self.prim("stoop_stone")
        l0, l1 = lat + 0.05, lat + r["shoe_length_m"] * math.cos(kick) + 0.30
        s0, s1, h = -0.17, 0.17, 0.04
        Q = lambda l, s, y: _add(at_wall(l, y), _mul(R_, s))
        bt = self.basis("stoop_stone", Q(l0, s0, h), R_, N_, seed)
        st.face([Q(l0, s0, h), Q(l0, s1, h), Q(l1, s1, h), Q(l1, s0, h)], Y, bt, conf)
        bs = self.basis("stoop_stone", Q(l0, s0, 0), R_, Y, seed)
        st.face([Q(l1, s0, 0), Q(l1, s1, 0), Q(l1, s1, h), Q(l1, s0, h)], N_, bs, conf)
        st.face([Q(l0, s0, 0), Q(l0, s1, 0), Q(l0, s1, h), Q(l0, s0, h)], _mul(N_, -1), bs, conf)
        be = self.basis("stoop_stone", Q(l0, s0, 0), N_, Y, seed)
        st.face([Q(l0, s0, 0), Q(l1, s0, 0), Q(l1, s0, h), Q(l0, s0, h)], _mul(R_, -1), be, conf)
        st.face([Q(l0, s1, 0), Q(l1, s1, 0), Q(l1, s1, h), Q(l0, s1, h)], R_, be, conf)

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


# T-2313: what the joined roof is welded on before it is emitted. A K15 apron's planes, 6 and
# 10 mm off a stack's face, cut contour lines across the whole slope, and where they cross a
# hip the union leaves points a millimetre or so apart. The contract reads every tier on a
# 1 mm grid (k01_contract.json measures.quantum_m), and two points can share one of its cells
# only if they lie within its diagonal (sqrt(3) mm); the web tier's 16-bit positions move a
# point by a fraction of a millimetre more. So the shell is welded at 2 mm, which no part of
# the roof is built finer than (the thinnest is K15's 6 mm flashing).
SHELL_WELD_M = 0.002


def _clip_half(poly, k, value, sign):
    """T-2841: a convex polygon cut to the side of the plane `coordinate k = value` that
    `sign` points to (+1 keeps k >= value, -1 keeps k <= value); [] when none of it is."""
    if value in (math.inf, -math.inf):
        return list(poly) if (sign > 0) == (value < 0) else []
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        dp, dq = sign * (p[k] - value), sign * (q[k] - value)
        if dp >= -1e-9:
            out.append(p)
        if (dp > 1e-9 and dq < -1e-9) or (dp < -1e-9 and dq > 1e-9):
            s_ = dp / (dp - dq)
            out.append(tuple(a + (b - a) * s_ for a, b in zip(p, q)))
    return out


def _poly_area(poly):
    """T-2841: a planar polygon's area (Newell)."""
    n = (0.0, 0.0, 0.0)
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
    return math.sqrt(_dot(n, n)) / 2


def _weld_shell(pts, tris):
    """Merge the shell's points that lie within SHELL_WELD_M of each other (into the lowest
    index) and drop the triangles that collapse: the edge collapse a 1 mm quantum would
    otherwise read as a degenerate face. The roof gate (check_roof_kit.py) proves the
    result still closed and one shell."""
    cell = {}
    for i, p in enumerate(pts):
        cell.setdefault(tuple(math.floor(c / SHELL_WELD_M) for c in p), []).append(i)
    root = list(range(len(pts)))

    def find(i):
        while root[i] != i:
            root[i] = root[root[i]]
            i = root[i]
        return i
    for key, ids in cell.items():
        near = [j for d in itertools.product((-1, 0, 1), repeat=3)
                for j in cell.get((key[0] + d[0], key[1] + d[1], key[2] + d[2]), ())]
        for i in ids:
            for j in near:
                if j < i and math.dist(pts[i], pts[j]) <= SHELL_WELD_M:
                    a, b = find(i), find(j)
                    if a != b:
                        root[max(a, b)] = min(a, b)
    if all(find(i) == i for i in range(len(pts))):
        return pts, tris
    out = []
    for a, b, c, role, n in tris:
        a, b, c = find(a), find(b), find(c)
        if len({a, b, c}) == 3:
            out.append((a, b, c, role, n))
    return pts, out


def _breaks(xs):
    """Sorted cell lines, a line within half the K01 measure's 1 mm face quantum of the one
    before it dropped (T-2499): two datums that agree to the millimetre but not to the float
    (1808's second-storey heads, 5.9 + 0.75 + 2.2, and the band at 8.85 m) otherwise leave a
    row of quads 1e-5 m tall, which the measure counts as degenerate faces."""
    out = []
    for x in sorted(set(xs)):
        if not out or x - out[-1] >= 5e-4:
            out.append(x)
    return out


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


def hole(o):
    """An opening's hole in its wall: (s0, s1, sill, head), or for a round-headed one (T-2410)
    (s0, s1, sill, spring, its head right -> left) on K06's own curve for that span."""
    s0, s1 = o.s_m - o.width_m / 2, o.s_m + o.width_m / 2
    if o.component not in ROUND_CUT:
        return (s0, s1, o.sill_m, o.head_m)
    from . import k06_windows
    if o.rise_over_span:   # T-2960: cut segmental, on its K06 sash's own rise
        spring = o.head_m - o.width_m * o.rise_over_span
        head = k06_windows.Head("segmental", s0, s1, spring, o.rise_over_span)
        return (s0, s1, o.sill_m, spring, head.curve(0.0, s1, s0))
    spring = o.head_m - o.width_m / 2
    return (s0, s1, o.sill_m, spring, k06_windows.Head("round", s0, s1, spring).curve(0.0, s1, s0))


def loggia_side_arch(p):
    """T-2910: the loggia's side arch as an arched group on its end wall's own s (the side
    wall's s runs from the rear to the front, so the arch `centre_m` behind the front stands
    at depth - centre_m), or None."""
    sa = ((p.entrance_kit or {}).get("loggia") or {}).get("side_arch")
    if not sa:
        return None
    c = p.depth_m - sa["centre_m"] if sa["wall"] == "k01.wall.side.south" else sa["centre_m"]
    w, h, ring = sa["clear_width_m"], sa["clear_height_m"], sa["ring_m"]
    floor = p.door_floor_m
    spring = round(floor + h - w / 2, 5)
    s0, s1 = round(c - w / 2, 5), round(c + w / 2, 5)
    top = round(spring + w / 2 + ring, 5)
    return {"wall": sa["wall"], "group": {
        "component": "k01.opening.loggia_side_arch", "lights": ((s0, s1, spring, round(w / 2, 5), floor),),
        "sill_m": floor, "spring_m": spring, "top_m": top, "cuts": (round(s0 - ring, 5), round(s1 + ring, 5)),
        "piers": (), "keystone": {"s_m": round(c, 5), "bed_m": round(spring + w / 2, 5),
                                  "top_m": sa["keystone_top_m"], "width_m": tuple(sa["keystone_m"])}}}


def build(params, structure_id: str):
    """The assembly: walls with their openings cut, the entrance and its stoop, the roof."""
    p = params
    a = Assembly(structure_id, p)
    if a.k14 is not None and not p.stone:
        # T-2364: a stone front lays its openings before it cuts its walls; a brick house cuts
        # its walls first, so the K06 sills its trails hang from are not seated yet when the
        # walls need their trail columns. Read them off a build of the same record without
        # the kit: the same seats, laid by the same calls, and nothing else is taken from it
        a.k14_sills = build(dataclasses.replace(p, condition={}), structure_id).footprints
    D, W, E = p.depth_m, p.width_m, p.eave_m
    # T-2528: the soffit the roof builds (Assembly.roof): a hip's drops by the overhang's run
    # down its slope, a mansard's stands on the wall head (T-2370), the fascia's depth under E
    drop = 0.0 if p.mansard else p.eave_overhang_m * math.tan(math.radians(p.roof_pitch_deg))
    yf = E - drop - EAVE_FASCIA_M
    a.soffit_m = yf
    floors = p.floors_m
    # T-3006: a rounded corner replaces the square one on the front and its side wall up to
    # the stone's top (the round's corbel squares it there); `round_corner` lays it
    rounded = k01_frontage_params.round_corner_spans(p.round_corner, D, W)["walls"] if p.round_corner else {}
    # T-3048: and a chamfered pavilion's canted face stands where the square corner was, from
    # grade, so the front and its side wall are cut back to it as far up
    rounded = {**rounded, **k01_frontage_params.chamfer_spans(p.bays, D, W)}
    # T-3186: a canted corner cuts the front and its side wall back to its face, to the wall head
    cant = k01_frontage_params.cant_corner_plan(p.cant_corner, D, W) if p.cant_corner else None
    cant_cut = {w: (*sp, 0.0, E) for w, sp in cant["walls"].items()} if cant else {}
    y_round = p.arched_front["stone_top_m"] if p.arched_front else yf
    belts = [(floors[1] - 0.20, floors[1], 0.05)] + ([(floors[2] - 0.15, floors[2], 0.05)] if len(floors) > 2 else [])

    def stops(wall_id):
        """What leaves a wall undrawn other than its openings: (finish gap, rear wings)."""
        # T-2343: where a rear wing stands on this wall, the wall is behind it and not drawn
        finish_gap = [(0., p.stone_finish["stone_return_m"], p.floors_m[2]+.1, E)] if p.stone_finish and wall_id == "k01.wall.side.north" else []
        # T-2820: and where the rear section stands beside it, to the wall head
        if side_arch and side_arch["wall"] == wall_id:
            g = side_arch["group"]
            finish_gap = finish_gap + [(g["lights"][0][0], g["lights"][0][1], g["sill_m"], g["spring_m"]),
                                       (g["cuts"][0], g["cuts"][-1], g["spring_m"], g["top_m"])]
        if wall_id in rounded:
            finish_gap = finish_gap + [(*rounded[wall_id], 0.0, y_round)]
        if wall_id in cant_cut:
            finish_gap = finish_gap + [cant_cut[wall_id]]
        # T-3112: the side wall beside the pier stepped down under its weathering's slope
        if p.front_pier and wall_id == "k01.wall.side.south":
            L, step = a.pier_slope(), 0.1
            u = D
            while u > 0.0 and L(u) < E:
                finish_gap = finish_gap + [(max(0.0, u - step), u, L(u) - 0.01, E)]
                u -= step
        return finish_gap, [(*w["host_span_m"], 0.0, w["deck_m"]) for w in p.rear_wings if w["host_wall"] == wall_id] + \
               ([(*p.rear_section["host_span_m"], 0.0, E)] if p.rear_section and p.rear_section["host_wall"] == wall_id
                else [])

    # T-2910: the loggia's side arch, an arched group on its end wall: the courses stop at its
    # clear hole and its voussoir block, and k01_arched_front lays the block's stones
    side_arch = loggia_side_arch(p)

    def holes(wall_id):
        finish_gap, wings = stops(wall_id)
        return finish_gap + [hole(o) for o in p.openings if o.wall == wall_id] + wings

    # The four walls, each about its base socket: outer face, left end (seen from
    # outside), at grade. +X is east (footprint u), -Z is north (footprint v).
    # T-2788: an all-stone house lays its side and rear walls in the front's K02 stone too
    all_round = bool(p.stone.get("all_round"))
    side = "rough_stone_trim" if all_round else "brick"

    def side_belts(which):   # T-2781: a side wall's stone belt, laid as the front's are
        return tuple((b["from_m"], b["to_m"], b["proud_m"]) for b in p.side_belts if b["wall"] == f"k01.wall.side.{which}") \
            + tuple((0.0, b["to_m"], b["proud_m"], tuple((o.s_m - o.width_m / 2, o.s_m + o.width_m / 2, o.sill_m, o.head_m)
                                                          for o in p.openings if o.wall == f"k01.wall.side.{which}"
                                                          and o.sill_m < b["to_m"]))
                    for b in p.side_base if b["wall"] == f"k01.wall.side.{which}")   # T-3184
    walls = {
        # T-2341: a record with no K02 stone front is a brick house, its front in the K03 brick
        "k01.wall.street_front": ("rough_stone_trim" if p.stone else "brick", (D, 0.0, 0.0), (0.0, 0.0, -1.0),
                                  W, p.front_thickness_m, belts),
        "k01.wall.side.north": (side, (D, 0.0, -W), (-1.0, 0.0, 0.0), D, p.side_thickness_m, side_belts("north")),
        "k01.wall.rear_service": (side, (0.0, 0.0, -W), (0.0, 0.0, 1.0), W, p.side_thickness_m, ()),
        "k01.wall.side.south": (side, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), D, p.side_thickness_m, side_belts("south")),
    }
    if cant:   # T-3186: the canted face, from the end of the wall before it to the start of the next
        (u0, v0), (u1, v1) = cant["ends"]
        walls[k01_frontage_params.CANT_WALL] = (side, (u0, 0.0, -v0), _unit((u1 - u0, 0.0, v0 - v1)),
                                                p.cant_corner["face_m"], p.front_thickness_m, belts)
    gaps = {cid: [bay["span_m"] for bay in p.bays if bay["wall"] == cid]
                 + [w["host_span_m"] for w in p.rear_wings if w["host_wall"] == cid]
                 + ([p.rear_section["host_span_m"]] if p.rear_section and p.rear_section["host_wall"] == cid else [])
             for cid in walls}
    if a.k14 is not None:   # T-2358: each wall's frame, for its trails and its damp line
        a.k14_walls = {cid: (O, R, _cross(R, Y), length) for cid, (mat, O, R, length, t, bands) in walls.items()}

    def breaks_of(cid, mat):
        """A wall's vertex rows (and, under the K14 kit, its trail columns)."""
        if a.k14 is not None and a.k14_fabric(mat):
            rows, cols = a.k14_breaks(cid)
            return (yf, *rows), cols
        return ((yf, *k03_brick.condition_breaks(yf)) if MATERIALS[mat].get("condition") else (yf,)), ()
    frames, laid = {}, {}
    if p.stone:
        # T-2289: a coursed stone front is laid round what the kits seat on it, so the
        # openings and the bays are built first, each noting its footprint on its wall
        frames = {cid: (((O, R, _cross(R, Y)), t), mat) for cid, (mat, O, R, length, t, bands) in walls.items()}
        for op in p.openings:
            (frame, t), mat = frames[op.wall]
            if p.on_frontispiece(op):   # T-2753: laid on the proud frontispiece's face
                frame = a.frontispiece_frame(frame)
            a.opening(op, frame, t, mat, "limestone_trim", coursed=all_round or op.wall == "k01.wall.street_front")
        a._walls, a._yf = walls, yf   # T-2773: a bay coursed on the front's beds strikes them first
        for bay in p.bays:
            if not bay.get("wing"):   # T-2842: a wing's tower is laid before its wing, below
                laid[bay["id"]] = a.bay(bay, frames[bay["wall"]][0][0])
        mat, O, R, length, t, _ = walls["k01.wall.street_front"]
        front = [o for o in p.openings if o.wall == "k01.wall.street_front"]
        frame, quoins = a.stone_front("k01.wall.street_front", O, R, length, E, yf, t, front,
                                      extra=([(*rounded["k01.wall.street_front"], 0.0, y_round)] if rounded else [])
                                      + ([(0.0, p.front_pier["to_m"], 0.0, E)] if p.front_pier else [])
                                      + ([cant_cut["k01.wall.street_front"]] if cant else [])
                                      + a.bay_holes.get("k01.wall.street_front", []))
        if p.round_corner:
            a.round_corner(t)
        if p.front_pier:   # T-3112: the pier the front's courses stopped at
            a.front_pier(t)
        for cid, (mat, O, R, length, t, bands) in walls.items():
            if cid == "k01.wall.street_front":
                continue
            if all_round:
                # T-2788: each face coursed on the front's beds, its K06 sills seated, a flat
                # arch over every opening, its belts the front's run round, dressed where a
                # kit stands and stopped where a rear wing stands on it
                a.stone_front(cid, O, R, length, E, yf, t, [o for o in p.openings if o.wall == cid],
                              a.front_course_beds, [*stops(cid)[0], *stops(cid)[1]])
                if side_arch and side_arch["wall"] == cid:
                    k01_arched_front.side_arch(a, frames[cid][0][0], side_arch["group"])
                continue
            breaks, cols = breaks_of(cid, mat)
            # the south corner's quoins are cut out of the brick they return into
            bond = [(length - q[0], length, q[1], q[2]) for q in quoins] if cid == "k01.wall.side.south" else []
            a.wall(cid, mat, O, R, length, E, t, holes(cid) + bond, breaks, bands, gaps[cid], cols)
        if quoins:
            a.quoins(frames["k01.wall.side.south"][0][0], D, quoins)
    for cid, (mat, O, R, length, t, bands) in walls.items():
        if cid in frames:
            continue
        breaks, cols = breaks_of(cid, mat)
        frames[cid] = (a.wall(cid, mat, O, R, length, E, t, holes(cid), breaks, bands, gaps[cid], cols), mat)
    for op in p.openings:
        if p.stone:
            break
        (frame, t), mat = frames[op.wall]
        a.opening(op, frame, t, mat, "limestone_trim")
    if not p.stone and p.street_iron:
        # T-1871: a brick front with no stone front wears its iron too (1700's and 1706's
        # balconettes, Chicagology's photograph), as stone_front lays it on 1834's
        k01_arched_front.street_iron(a, frames["k01.wall.street_front"][0][0], p.street_iron,
                                     p.worst_conf("footprint", "stories", "storey_heights_m", "construction"))
    # T-2291: a projecting stretcher course at the second-floor line on the south wall
    # and the rear, the south one run out past the quoin so the two meet; the north
    # wall is a blank party wall against the Glessner court and carries none. A windowed
    # north wall (T-2342, a street side) takes one, run out past the north-west corner
    # to meet the rear's as the south one meets it at the south-west
    sc_conf = p.worst_conf("storey_heights_m", "construction", "service_wall_brick")
    # A blank south wall (T-2350: 1634's party wall with 1636) carries none, as the north one
    south_to = D - p.stone["south_return_m"] if p.stone and "south_return_m" in p.stone else D   # T-2581
    south_to = min(south_to, rounded.get("k01.wall.side.south", (D, D))[0])   # T-3006: to the round
    courses = ([("k01.wall.side.south", -k03_brick.STRING_PROUD, south_to)] if p.side_bays else []) \
        + [("k01.wall.rear_service", 0.0, W)]
    if p.north_bays:
        courses.append(("k01.wall.side.north", rounded.get("k01.wall.side.north", (0.0, 0.0))[1],
                        D + k03_brick.STRING_PROUD))
    if all_round:
        courses = []   # T-2788: no brick to run a brick course in; the front's belts go round
    for cid, s_from, s_to in courses:
        frame = frames[cid][0][0]
        for s0, s1 in _pieces(s_from, s_to, gaps[cid]):   # T-2308: stopped against a bay
            k03_brick.string_course(a, seed_of(structure_id, cid, 0), frame, s0, s1, floors[1], sc_conf)
    # T-2343: the rear wings, each a brick box on its host wall under its own flat deck
    # (T-2841: or its own slated hip or gable)
    # T-2842: a K08 tower on a wing's wall is laid first, so a coursed wing is laid round it
    for bay in p.bays:
        if bay.get("wing"):
            w = next(x for x in p.rear_wings if x["id"] == bay["wing"])
            O, R, _ = wing_walls(w)[bay["wall"].rsplit(".", 1)[1]]
            laid[bay["id"]] = a.bay(bay, (O, R, _cross(R, Y)))
    for w in p.rear_wings:
        a.wing(w, sc_conf)
    if p.rear_section:   # T-2820: the rear section's step-out walls; its attic is the roof's
        from . import k01_rear_section
        k01_rear_section.walls(a)
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
        # T-2541: an oriel stands on its corbels, so an opening wholly under its lowest
        # course is in front of nothing (1811's door, under the arch its oriel is carried
        # over) — the clearance k01_frontage_params._bays already reads its host openings by
        under = None
        if bay["variant"]["kind"] == "oriel":
            from . import k08_bays as K8
            under = K8.support_bottom(bay["variant"])   # T-2883: its apron's foot, or its corbels
        for o in p.openings:
            if under is not None and o.head_m + 0.30 <= under:
                continue
            if o.wall == bay["wall"] and bay["span_m"][0] < o.s_m < bay["span_m"][1] \
                    and o.sill_m - 0.15 < top:
                raise ValueError(f"{bay['id']}'s roof meets {o.wall} at {top:.3f} m, under the "
                                 f"opening at s {o.s_m} whose sill is {o.sill_m} m")
    if p.shutters:   # T-1879: open louvred shutters beside the named walls' lights
        a.window_shutters({cid: frames[cid][0][0] for cid in frames})
    # T-2317: the K10 wall head — brackets and a bed moulding under the soffit, every
    # corner turned and every head, pipe and bay stood clear of; cresting on the ridge
    k10_frontage.dress(a, reach)
    if p.pavilions:
        # T-3158: the front's pavilions — piers, frieze panels, modillions under the cornice
        # just laid, and the mansard's ribs over the piers (1729's, the Detroit print)
        from . import k01_pavilions
        k01_pavilions.dress(a)
    if p.porte_cochere:
        # T-3160: the side wall's arcaded porte-cochere under its balustraded deck (1729's)
        from . import k01_porte_cochere
        k01_porte_cochere.dress(a)
    if (p.mansard or {}).get("deck"):
        # T-3000: the deck's cresting and finials, the K10 kit's iron on the curb
        from . import k01_mansard_deck
        k01_mansard_deck.dress(a, p.mansard["deck"], max(p.conf("mansard"), p.conf("roof_form")))
    if ((p.mansard or {}).get("crown") or {}).get("finial"):
        # T-3175: a hipped crown's finial on its ridge's street end (1827's pavilion)
        from . import k01_mansard_deck
        k01_mansard_deck.crown_finial(a, p.mansard["crown"], max(p.conf("mansard"), p.conf("roof_form")))
    # T-2319: the K11 boundary — the front fence on the street line, a pair of gates on the
    # walk to the stoop, a gate across the side passage, the south boundary wall
    from . import k01_stone_finish
    k01_stone_finish.dress(a)
    k11_frontage.dress(a)
    # T-2360: the K14 yard inside that boundary — the lawn and its bare strip at the wall
    # foot, earth under the open stoop, the front walk's flags and the side passage's cinder
    k14_yard.dress(a)
    a.condition_tones()   # T-2358: last, so every sill and kit piece is laid and toned
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
                # T-2360: and a prim whose tones were laid point by point (a K14 walk's wear)
                **({"_TONE": accessor(pr.tone, 5126, "SCALAR", 1, 34962)}
                   if pr.tone_of or any(t != 1.0 for t in pr.tone) else {}),
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
