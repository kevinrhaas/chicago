"""fort_structure — the buildings and the ground furniture of a garrison post.

Twelve kinds, one builder, because they differ in what the archetype is ALLOWED to
decide rather than in how they are drawn: a magazine gets no windows because a powder
magazine has none, a blockhouse gets a jettied upper storey and loopholes because that
is what makes it a blockhouse rather than a shed, and a parade ground gets no roof
because it is a piece of ground.

**Orientation.** The facade faces NORTH at rotation_deg 0, per the pinned convention
in docs/GLB-CONTRACT.md — in Blender the +y face, because the exporter's
export_yup=True maps Blender +Y to glTF -Z, which the contract defines as north. Every
range inside Fort Dearborn faces the parade, so each record's rotation_deg is the
bearing of the wall that looks inward, and getting it wrong turns a building's back on
the courtyard without anything failing.

**What the log courses look like** comes from common/logwork.py, the same visual
language as the dwellings at the forks. That is deliberate and it is also a claim
worth stating: the fort's log buildings were put up by soldiers with the same tools
and the same timber as the cabins across the river, and there is no evidence they
looked like a different kind of carpentry.

**Openings are surfaces, not holes**, at this level of detail, exactly as in
log_dwelling — an opening cut through would show the inside of the far wall, and
interiors are out of scope.

**Face winding.** Every quad is wound so its normal points out of the solid.
"""

from __future__ import annotations

import math
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.logwork import (  # noqa: E402
    CHINK_RGBA, COURSE_M, HEWN_RGBA, RELIEF_M, hewn_log_wall,
)
from common import materials  # noqa: E402
from common import openings  # noqa: E402
from common.mesh import MeshBuilder, ROOF_RGBA, simple_material  # noqa: E402
from archetypes.fort_structure_params import FortStructureParams, wall_openings, tower_opening_layout  # noqa: E402

#: This archetype's roof COVERING, off the sheet's dealing rule (T-1487).
#: `materials.roof_substrate` holds the argument for why it is this one and
#: which half of it is graded by materials.md §2.2 and which half is L266.
_ROOF = materials.roof_substrate("fort_structure")


M_WALL, M_ROOF, M_DARK, M_TRIM = 0, 1, 2, 3
#: Appended only where a record counts a stack, so the seven chimneyless masters
#: in this archetype keep the four materials they have always had. T-0137.
M_CHIMNEY = 4

WALL_RGBA = {
    "log": HEWN_RGBA,
    "hewn_log": HEWN_RGBA,
    "braced_frame": (0.60, 0.55, 0.46, 1.0),
    # OFF THE SHEET since T-0267, and it was the last brick in the town that was not.
    # This entry carried an archetype-local 0.47/0.26/0.20 that nothing in the
    # repository argued — about 13 % from the sheet in linear green and 18 % in blue,
    # on the same three buildings a visitor sees from the same streets. The sheet's
    # row already declares itself the surface for `construction: brick` AND for every
    # chimney (materials.md §2.1), so a wall reading it is the row doing its job.
    #
    # It is NOT a claim that the fort's 1816 brick and the town's 1833 brick matched.
    # Nothing here shows the colour of any fort surface; the one coloured witness to
    # any Chicago brick is the Petford watercolour of the Sauganash. chimneys.md §6
    # made exactly this argument for the fort's stacks and named this convergence as
    # the parcel that follows it. materials.md §9 is the whole of it.
    #
    # T-0332: and it ASKS for it now rather than naming the row. `materials.wall_colour`
    # is the wall's own question — "what colour is a bare wall of this fabric" — so the
    # sheet could rename the row it answers with (`CHIMNEY_BRICK` -> `BRICK`, because a
    # row named for a chimney was painting two attested brick WALLS) without this table
    # having to be found and edited. materials.md §8.3 is the shape; §10 is the parcel.
    "brick": materials.wall_colour("brick").rgba,
    # STONE and EARTH stay local, and the reason is measured rather than assumed: no
    # source in this repository states the colour of a stone or an earth wall, and no
    # record in the dataset builds one (T-0332 counted: zero of either construction).
    # `wall_colour` therefore answers None for both, which is the sheet saying so out
    # loud instead of dealing the nearest row. These two are this archetype's own
    # unreached fallbacks; if a record ever builds one, that is when the value has to
    # be argued and the argument is what puts it on the sheet. materials.md §10.5.
    "stone": (0.58, 0.56, 0.51, 1.0),
    "earth": (0.34, 0.30, 0.22, 1.0),
}
# A coating over whatever the wall is made of, and OFF THE SHEET since T-0007. This
# module used to carry a THIRD whitewash value — 0.86/0.85/0.80, against the frame
# archetypes' 0.88/0.87/0.83 and the placeholder generator's 0.847/0.820/0.737 — for
# no reason anybody wrote down. materials.md finding 5 is exactly that: the town was
# painted by generators sharing no palette. One limewash now, and it states its own
# gloss because a limewashed wall is the flattest surface in the town (§2.1).
PAINT_OVER = {
    "whitewash": materials.FINISHES["whitewash"].rgba,
    "white": materials.FINISHES["white_paint"].rgba,
}


class TonedBuilder(MeshBuilder):
    """MeshBuilder plus one more float a vertex: `_TONE`, a multiplier on albedo.

    T-2123. The owner, looking at the fort in 1835: "that wood looks pretty plain,
    and we have done better" — and what the better wood does (the plank walk,
    frontage.js § THE WALK'S OWN TIMBER) is give every board its OWN weathering, so
    a run of timber reads as separate pieces of wood rather than one painted slab.
    The fort could not: each log wall was one box, so every course of every wall
    shared one colour to the bit. So each course is now its own band of faces, and
    each band carries a tone the renderer multiplies into the building's colour
    (buildings.js reads `_tone`). 1.0 everywhere is the old building exactly, and
    the attribute is left off a mesh that never leaves 1.0.

    The tone is taken at a face's CENTROID by `fn(point, centroid, material)`, so a
    face is one piece of wood and a course does not shade into the next; `point` is
    there for a gradient WITHIN a piece (a picket darker at its foot than its head),
    and `material` so the chinking between two logs is not dealt a log's tone.

    A copy of this class lives in palisade.py, deliberately: a module in
    generators/common/ is hashed into every asset in the town (code_inputs.py), so
    sharing these thirty lines from there would re-bake 400 buildings for a change
    that moves the fort's vertices only.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.tone: list[float] = []
        self.tone_fn = None

    def add_poly(self, points, confidence: float, mat: int = 0) -> list[int]:
        idx = super().add_poly(points, confidence, mat)
        if self.tone_fn is None:
            self.tone.extend([1.0] * len(points))
        else:
            n = float(len(points))
            c = (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n,
                 sum(p[2] for p in points) / n)
            self.tone.extend(float(self.tone_fn(p, c, mat)) for p in points)
        return idx

    def to_object(self, materials=None):
        ob = super().to_object(materials)
        if any(abs(t - 1.0) > 1e-6 for t in self.tone):
            attr = ob.data.attributes.new(name="_TONE", type="FLOAT", domain="POINT")
            for i, t in enumerate(self.tone):
                attr.data[i].value = t
        return ob


def _unit(name: str, *keys) -> float:
    """A stable number in [0, 1) from a name and some integers: the same building
    weathers the same way on every bake (crc32, not Python's salted hash)."""
    return (zlib.crc32(("|".join([name, *map(str, keys)])).encode()) & 0xFFFFFF) / float(0x1000000)


#: How far one log differs from the next, at most, either way. The plank walk's
#: board span is 0.14 (frontage.js WALK_BOARD_SPAN); a hewn log is a bigger piece
#: of a different tree, so it is allowed a little more. RECONSTRUCTED (L390).
LOG_SPAN = 0.16
#: The sill course sits in the splash and the damp and reads darker than the logs
#: above it; the next one up a little. RECONSTRUCTED (L390).
SILL_K = (0.80, 0.92)


def _log_tone(name: str, z0: float, course: float = COURSE_M):
    """The tone function for a coursed log wall whose grid starts at `z0`."""
    def fn(_p, c, mat):
        if mat != M_WALL:
            return 1.0
        i = int(math.floor((c[2] - z0) / course + 1e-6))
        k = 1.0 + LOG_SPAN * (2.0 * _unit(name, "log", i, round(c[0] / 2.0), round(c[1] / 2.0)) - 1.0)
        if 0 <= i < len(SILL_K):
            k *= SILL_K[i]
        return k
    return fn


def build(params: FortStructureParams, name: str):
    """Build one fort structure. Returns a Blender object at the local origin."""
    params.validate()
    b = TonedBuilder(name)

    if params.kind == "parade":
        _parade(b, params)
    elif params.kind == "root_house":
        _root_house(b, params)
    elif params.kind == "tower":
        _tower(b, params)
    elif params.kind == "flagstaff":
        _flagstaff(b, params)
    else:
        _building(b, params)

    base = WALL_RGBA.get(params.construction, WALL_RGBA["log"])
    wall_rgba = PAINT_OVER.get(params.paint, base)
    # The gloss of a fort wall, by what it is MADE of, off the sheet (T-0007): brick
    # 0.90, rubble stone 0.93, hewn log 0.92, trodden earth 0.95, a sided frame wall
    # 0.86 — against the single 0.92 every fort surface used to share, which put a
    # limewashed magazine and a turf root-house cellar at the same gloss. A coating
    # states its own and overrides the fabric's, which is what puts the whitewashed
    # walls of the fort at the same flat 0.90 as the whitewashed walls of the town.
    substrate = materials.wall_substrate(construction=params.construction,
                                         default="hewn_log")
    _, wall_rough = materials.resolve(
        substrate, materials.wall_finish(paint=params.paint))
    mats = [
        simple_material(params.construction, wall_rgba, roughness=wall_rough),
        # The roof takes the town's default TONE: no fort record deals a weathering
        # condition. Its COVERING is now dealt — a shingle field, on the same L266 the
        # log cabins take, because §2.2 grades shingle for a framed building and the
        # garrison's eight kinds are not all framed. `materials.roof_substrate` holds
        # the argument; the 0.9 is `shingle`'s and is what this always shipped.
        simple_material(materials.roof_material_name(_ROOF), ROOF_RGBA,
                        roughness=_ROOF.roughness),
        # ONE DARK (T-0126) — the sheet's `DARK` row. Loopholes, the root house's
        # plank door and every opening the complex cuts. Two uses on this archetype
        # are not openings and the row's note names them: the sun-dial's brass plate
        # and the lighthouse lantern's glazed drum. Both are dark and small, and
        # splitting either would take this archetype from four materials to five.
        simple_material("dark", materials.DARK.rgba,
                        roughness=materials.DARK.roughness),
        simple_material("chinking", CHINK_RGBA,
                        roughness=materials.SUBSTRATES["chinking"].roughness),
    ]
    # THE STACK IS NOT THE ROOF, AT THE FORT TOO (T-0137). T-0008 gave every framed
    # building's stack brick and every log cabin's stick-and-clay and deliberately
    # left this archetype out, because the second Fort Dearborn is 1816 —
    # seventeen years before Blodgett's brick-yard opened — so the argument that
    # carried the town (a working yard two blocks away) does not reach it. Until this
    # parcel that made the garrison's ten stacks the only ones in Chicago painted the
    # colour of the roof they pass through.
    #
    # The fort answers the question on its own ground, and it needs no third row on
    # the sheet:
    #
    #   1. BRICK IS ATTESTED INSIDE THIS FORT, twice and independently. Hubbard,
    #      standing in it in 1827, gives "the brick building, just within the north
    #      stockade" and "the magazine, of brick"; the 1855 key gives the
    #      commandant's quarters as "(brick, about 25x50 ft.)". The masonry here does
    #      not depend on Blodgett and never did: it is on the record, in 1816, on
    #      federal ground, and `fort_dearborn_commandants_quarters` and
    #      `fort_dearborn_magazine` both carry `construction: brick` ATTESTED
    #      because of it.
    #   2. THE STACKS ARE INTERIOR — see `_chimneys`: the depth midline, from the
    #      ground, through the ridge. That is the disposition `common/materials.py`
    #      § the chimney stack answers with brick, and the reason it does is that a
    #      flue carried up inside a timber building has to be masonry. The other
    #      answer, `log_dwelling`'s cat-and-clay, is argued from a stack built
    #      OUTSIDE the gable so it can be pulled away when it catches fire, and no
    #      building in this fort has one.
    #
    # So the fort takes the sheet's existing brick row, INFERRED, and the tier is the
    # honest one: brick on this ground is attested, brick in these particular flues is
    # reasoned from it and from the disposition. Nothing is reconstructed and
    # docs/LIBERTIES.md needs no new entry — L26 already owns where a stack stands.
    # docs/RESEARCH/chimneys.md §4 is the argument in full;
    # `tools/measure_stack_fabric.py` is the gate that stops it regressing.
    if params.chimneys > 0:
        stack = materials.chimney_finish("interior")
        mats.append(simple_material("chimney", stack.rgba, roughness=stack.roughness))
    ob = b.to_object(mats)
    if params.tower_lantern_detail is not None:
        _configure_cage_glass(ob, params)
    return ob


# ------------------------------------------------------------------ buildings

def _building(b: MeshBuilder, p: FortStructureParams) -> None:
    """A walled building with a roof: the eight garrison kinds.

    Massing takes the confidence of the attributes that say what the building WAS,
    not the precision of its dimensions — the argument is set out at length in
    frame_tavern.build and is not repeated here.
    """
    c_mass = p.worst_conf("kind", "stories", "construction")
    c_roof = p.worst_conf("roof_type", "roof_pitch_deg")
    w, d, wz = p.width_m, p.depth_m, p.wall_height_m
    over = p.overhang_m

    lower_z = wz if over == 0.0 else p.storey_height_m
    log = p.construction in ("log", "hewn_log")
    if log:
        _log_wall(b, b.name, 0.0, 0.0, w, d, 0.0, lower_z, c_mass)
    else:
        b.add_box(0.0, 0.0, 0.0, w, d, lower_z, c_mass, M_WALL,
                  skip=("bottom", "top"))
        if p.construction == "brick":
            _string_course(b, 0.0, 0.0, w, d, lower_z, c_mass)

    if over > 0.0:
        # the jetty: a floor plate on the overhang, then the upper storey
        b.add_box(-over, -over, lower_z, w + over, d + over, lower_z + 0.18,
                  c_mass, M_TRIM, skip=("top",))
        if log:
            _log_wall(b, b.name, -over, -over, w + over, d + over, lower_z + 0.18,
                      wz + 0.18, c_mass)
        else:
            b.add_box(-over, -over, lower_z + 0.18, w + over, d + over, wz + 0.18,
                      c_mass, M_WALL, skip=("bottom", "top"))

    ex = over
    eave = wz + (0.18 if over > 0.0 else 0.0)
    # The course grid the gable infill continues: the top storey's own.
    grid0 = (lower_z + 0.18) if over > 0.0 else 0.0
    ridge = _roof(b, p, -ex, -ex, w + ex, d + ex, eave, c_roof, c_mass, grid0)

    if p.kind == "magazine":
        _magazine_door(b, p, c_mass)
    else:
        _openings(b, p, lower_z, over)
    if p.loopholes:
        _loopholes(b, p, lower_z, over, p.conf("loopholes", "reconstructed"))
    if p.gallery:
        _gallery(b, p, p.conf("gallery", "reconstructed"))
    if p.chimneys:
        _chimneys(b, p, ridge, p.conf("chimneys", "reconstructed"), M_CHIMNEY)


#: How far a pitched roof reaches past the wall at its eaves and its rakes. The
#: 0.25 of `MeshBuilder.add_gable_roof`, a little more, because a log wall is
#: thicker than a frame one and a short overhang on it reads as a lid. RECONSTRUCTED
#: (L390), as every dimension of every roof in this fort already is.
EAVE_M = 0.30
#: The covering's own thickness at its edges: boards and shingles on a deck, seen
#: edge-on from the parade. Without it a roof is a sheet of paper. RECONSTRUCTED.
ROOF_EDGE_M = 0.07
# T-2123 roof weathering (L390): eave-to-ridge tone, per-plane spread, edge shadow.
ROOF_EAVE_K = 0.84
ROOF_RIDGE_K = 1.02
ROOF_PLANE_SPAN = 0.06
ROOF_EDGE_K = 0.85


def _roof(b: MeshBuilder, p: FortStructureParams, x0, y0, x1, y1,
          eave_z: float, conf: float, c_wall: float = None, grid0: float = 0.0) -> float:
    """The roof, with the walls under it carried up to meet it.

    T-2123, on the owner's report that the artillery house's roof was "hovering".
    It was: this function drew a shed roof's high edge 1.6 m above a wall that
    stopped at the eave, with nothing under either end, and every gable roof here
    drew its gable triangles IN ROOF SHINGLE, a quarter-metre outboard of the wall
    and floating at the eave line a hand's breadth above the wall head. A roof sits
    ON its walls: the wall plane under a gable or a shed's high side is the wall,
    built of what the wall is built of (`_gable_wall`), and the roof plane passes
    through the wall head at the wall line and runs on DOWN to its eave, so there
    is no slot of sky between the two.
    """
    c_wall = conf if c_wall is None else c_wall
    t = math.tan(math.radians(p.roof_pitch_deg))
    if p.roof_type == "none":
        return eave_z
    if p.roof_type == "flat":
        b.add_poly([(x0, y0, eave_z), (x0, y1, eave_z), (x1, y1, eave_z),
                    (x1, y0, eave_z)], conf, M_ROOF)
        return eave_z
    if p.roof_type == "gable":
        return _gable_roof(b, p, x0, y0, x1, y1, eave_z, t, conf, c_wall, grid0)
    if p.roof_type == "shed":
        return _shed_roof(b, p, x0, y0, x1, y1, eave_z, t, conf, c_wall, grid0)
    return _hip_roof(b, x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf,
                     pyramid=(p.roof_type == "pyramid"))


def _roof_plane(b: MeshBuilder, pts, conf: float, ridge_edge: int = None) -> None:
    """One plane of covering, counter-clockwise from above, with its edges given
    the covering's thickness. `ridge_edge` names the edge (by its first vertex)
    that meets another plane at the ridge and so shows no edge at all.

    T-2123: a covering weathers from the eave up — the drip edge holds water and
    moss, the ridge dries first — so each plane carries a tone from ROOF_EAVE_K at
    its lowest edge to ROOF_RIDGE_K at its highest, times a per-plane variation so
    the two sides of a ridge do not match to the bit (L390). The thickness faces
    take the eave's tone, darker by the shadow under the edge."""
    zs = [q[2] for q in pts]
    z_lo, z_hi = min(zs), max(zs)
    k_plane = 1.0 + ROOF_PLANE_SPAN * (2.0 * _unit(b.name, "roof", *(round(v, 1) for q in pts[:2] for v in q)) - 1.0)

    def tone(q, _c, _m):
        f = (q[2] - z_lo) / (z_hi - z_lo) if z_hi - z_lo > 1e-6 else 0.0
        return k_plane * (ROOF_EAVE_K + (ROOF_RIDGE_K - ROOF_EAVE_K) * f)

    prev = b.tone_fn
    b.tone_fn = tone
    b.add_poly(pts, conf, M_ROOF)
    b.tone_fn = lambda _q, _c, _m: k_plane * ROOF_EAVE_K * ROOF_EDGE_K
    n = len(pts)
    for i in range(n):
        if i == ridge_edge:
            continue
        a, z = pts[i], pts[(i + 1) % n]
        b.add_poly([a, (a[0], a[1], a[2] - ROOF_EDGE_M),
                    (z[0], z[1], z[2] - ROOF_EDGE_M), z], conf, M_ROOF)
    b.tone_fn = prev


def _gable_roof(b: MeshBuilder, p: FortStructureParams, x0, y0, x1, y1, eave_z: float,
                t: float, conf: float, c_wall: float, grid0: float) -> float:
    o = EAVE_M
    drop = o * t                       # the eave hangs below the wall head by this
    lo = eave_z - drop
    if (x1 - x0) >= (y1 - y0):
        ym = (y0 + y1) / 2.0
        ridge = eave_z + (ym - y0) * t
        _roof_plane(b, [(x0 - o, y0 - o, lo), (x1 + o, y0 - o, lo),
                        (x1 + o, ym, ridge), (x0 - o, ym, ridge)], conf, ridge_edge=2)
        _roof_plane(b, [(x1 + o, y1 + o, lo), (x0 - o, y1 + o, lo),
                        (x0 - o, ym, ridge), (x1 + o, ym, ridge)], conf, ridge_edge=2)
        gable = [(y0, eave_z), (y1, eave_z), (ym, ridge)]
        _gable_wall(b, p, "x", x0, gable, -1, c_wall, grid0)
        _gable_wall(b, p, "x", x1, gable, 1, c_wall, grid0)
    else:
        xm = (x0 + x1) / 2.0
        ridge = eave_z + (xm - x0) * t
        _roof_plane(b, [(xm, y0 - o, ridge), (xm, y1 + o, ridge),
                        (x0 - o, y1 + o, lo), (x0 - o, y0 - o, lo)], conf, ridge_edge=0)
        _roof_plane(b, [(x1 + o, y0 - o, lo), (x1 + o, y1 + o, lo),
                        (xm, y1 + o, ridge), (xm, y0 - o, ridge)], conf, ridge_edge=2)
        gable = [(x0, eave_z), (x1, eave_z), (xm, ridge)]
        _gable_wall(b, p, "y", y0, gable, -1, c_wall, grid0)
        _gable_wall(b, p, "y", y1, gable, 1, c_wall, grid0)
    return ridge


def _shed_roof(b: MeshBuilder, p: FortStructureParams, x0, y0, x1, y1, eave_z: float,
               t: float, conf: float, c_wall: float, grid0: float) -> float:
    """A lean-to: high along the back (y0), falling to the front (y1).

    The back wall is carried up to the high plate and the two end walls are
    carried up under the slope — the three pieces the artillery house was missing.
    """
    o = EAVE_M
    hi = eave_z + (y1 - y0) * t
    _roof_plane(b, [(x0 - o, y0 - o, hi + o * t), (x1 + o, y0 - o, hi + o * t),
                    (x1 + o, y1 + o, eave_z - o * t), (x0 - o, y1 + o, eave_z - o * t)],
                conf)
    _gable_wall(b, p, "y", y0, [(x0, eave_z), (x1, eave_z), (x1, hi), (x0, hi)], -1,
                c_wall, grid0)
    end = [(y0, eave_z), (y1, eave_z), (y0, hi)]
    _gable_wall(b, p, "x", x0, end, -1, c_wall, grid0)
    _gable_wall(b, p, "x", x1, end, 1, c_wall, grid0)
    return hi


def _slice(outline, z: float):
    """The interval a convex outline in (u, z) covers at height `z`, or None."""
    us = []
    n = len(outline)
    for i in range(n):
        (ua, za), (ub, zb) = outline[i], outline[(i + 1) % n]
        if abs(zb - za) < 1e-9:
            if abs(z - za) < 1e-9:
                us += [ua, ub]
            continue
        if min(za, zb) - 1e-9 <= z <= max(za, zb) + 1e-9:
            us.append(ua + (ub - ua) * (z - za) / (zb - za))
    return (min(us), max(us)) if us else None


def _wall_quad(b: MeshBuilder, axis: str, plane: float, lo, hi, za: float, zb: float,
               outward: int, conf: float, mat: int) -> None:
    """A band of wall between heights `za` and `zb`, its edges at `lo` (u0, u1) and
    `hi` (u0, u1), on an axis-aligned plane — wound to face `outward`, as `_panel`.
    A band whose top has closed to a point is a triangle."""
    if axis == "y":
        pt = lambda u, z: (u, plane, z)  # noqa: E731
        natural = -1
    else:
        pt = lambda u, z: (plane, u, z)  # noqa: E731
        natural = 1
    pts = [pt(lo[0], za), pt(lo[1], za), pt(hi[1], zb), pt(hi[0], zb)]
    if hi[1] - hi[0] < 1e-6:
        pts = pts[:3]
    if outward != natural:
        pts.reverse()
    b.add_poly(pts, conf, mat)


def _gable_wall(b: MeshBuilder, p: FortStructureParams, axis: str, plane: float,
                outline, outward: int, conf: float, grid0: float) -> None:
    """The wall above the plate, under a roof: a gable, or a shed's high side.

    Built of what the wall below is built of. A log building's gable carries its
    log courses on up, shortening with the rake, with the same proud chinking at
    every course line and on the same course grid as the wall under it — so a
    course that starts on the eave wall does not jump a few centimetres where it
    turns the corner. That is how a log pen with a log gable is built; the other
    common gable of the period, boards nailed over a frame, is equally possible
    on any one of these buildings and is not attested for any (L390). Brick and
    frame walls get one flat piece of their own material.
    """
    zs = [z for _, z in outline]
    z0, z1 = min(zs), max(zs)
    if p.construction not in ("log", "hewn_log"):
        lo, hi = _slice(outline, z0), _slice(outline, z1)
        _wall_quad(b, axis, plane, lo, hi, z0, z1, outward, conf, M_WALL)
        return
    prev = b.tone_fn
    b.tone_fn = _log_tone(b.name, grid0)
    k0 = int(math.floor((z0 - grid0) / COURSE_M + 1e-6))
    cuts = [z0] + [grid0 + k * COURSE_M for k in range(k0 + 1, k0 + 200)
                   if z0 + 1e-3 < grid0 + k * COURSE_M < z1 - 1e-3] + [z1]
    gap = min(0.055, COURSE_M * 0.22)
    for za, zb in zip(cuts, cuts[1:]):
        lo, hi = _slice(outline, za), _slice(outline, zb)
        if lo is None or hi is None:
            continue
        _wall_quad(b, axis, plane, lo, hi, za, zb, outward, conf, M_WALL)
    b.tone_fn = prev
    # Proud chinking at each course line inside the gable, as hewn_log_wall lays it.
    for zc in cuts[1:-1]:
        za, zb = zc - gap / 2, zc + gap / 2
        sa, sb = _slice(outline, za), _slice(outline, zb)
        if sa is None or sb is None or sb[1] - sb[0] < 0.1:
            continue
        _wall_quad(b, axis, plane + outward * RELIEF_M, sa, sb, za, zb, outward, conf,
                   M_TRIM)


def _hip_roof(b: MeshBuilder, x0, y0, x1, y1, eave_z, pitch_deg, conf,
              pyramid: bool, overhang: float = 0.28) -> float:
    """A hip or a pyramid. A pyramid is the degenerate hip whose ridge is a point,
    and a blockhouse gets one because a four-sided pitched cap over a square plan
    is what every surviving blockhouse of the period carries."""
    x0, y0, x1, y1 = x0 - overhang, y0 - overhang, x1 + overhang, y1 + overhang
    w, d = x1 - x0, y1 - y0
    short = min(w, d)
    t = math.tan(math.radians(pitch_deg))
    # T-2123: the plane passes through the wall head at the wall line and hangs
    # on below it to the eave, as `_roof` explains; it used to start AT the wall
    # head's height out at the eave and so stood clear of the wall it covered.
    eave_z = eave_z - overhang * t
    rise = (short / 2.0) * t
    top = eave_z + rise
    if pyramid or abs(w - d) < 1e-6:
        apex = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, top)
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for i in range(4):
            (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
            b.add_poly([(ax, ay, eave_z), (bx, by, eave_z), apex], conf, M_ROOF)
        return top
    if w > d:
        r0 = (x0 + d / 2.0, (y0 + y1) / 2.0, top)
        r1 = (x1 - d / 2.0, (y0 + y1) / 2.0, top)
        b.add_poly([(x0, y0, eave_z), (x1, y0, eave_z), r1, r0], conf, M_ROOF)
        b.add_poly([(x1, y1, eave_z), (x0, y1, eave_z), r0, r1], conf, M_ROOF)
        b.add_poly([(x0, y0, eave_z), r0, (x0, y1, eave_z)], conf, M_ROOF)
        b.add_poly([(x1, y1, eave_z), r1, (x1, y0, eave_z)], conf, M_ROOF)
    else:
        r0 = ((x0 + x1) / 2.0, y0 + w / 2.0, top)
        r1 = ((x0 + x1) / 2.0, y1 - w / 2.0, top)
        b.add_poly([(x0, y0, eave_z), (x1, y0, eave_z), r0], conf, M_ROOF)
        b.add_poly([(x1, y1, eave_z), (x0, y1, eave_z), r1], conf, M_ROOF)
        b.add_poly([(x1, y0, eave_z), (x1, y1, eave_z), r1, r0], conf, M_ROOF)
        b.add_poly([(x0, y1, eave_z), (x0, y0, eave_z), r0, r1], conf, M_ROOF)
    return top


def _log_wall(b: MeshBuilder, name: str, x0, y0, x1, y1, z0: float, z1: float,
              conf: float) -> None:
    """`hewn_log_wall`, with every course its own band of faces (T-2123).

    The same wall to the vertex — the same outer surface, the same proud chinking
    and the same alternating notched corners, which `hewn_log_wall` still lays —
    except that the log box is cut at each course line, so each log can carry its
    own `_TONE` (TonedBuilder). Twelve triangles a course a building; a nine-course
    barracks is about a hundred more.
    """
    prev = b.tone_fn
    b.tone_fn = _log_tone(name, z0)
    n = max(int((z1 - z0) / COURSE_M), 1)
    cuts = [z0 + i * COURSE_M for i in range(n + 1) if z0 + i * COURSE_M < z1 - 1e-3] + [z1]
    for za, zb in zip(cuts, cuts[1:]):
        b.add_box(x0, y0, za, x1, y1, zb, conf, M_WALL, skip=("bottom", "top"))
    hewn_log_wall(b, x0, y0, x1, y1, z0, z1, conf, M_WALL, M_TRIM,
                  skip=("bottom", "top", "front", "back", "left", "right"))
    b.tone_fn = prev


def _panel(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
           z0: float, z1: float, outward: int, conf: float, mat: int) -> None:
    """One flat rectangle on an axis-aligned plane, wound to face `outward`."""
    if axis == "y":
        pts = [(u0, plane, z0), (u1, plane, z0), (u1, plane, z1), (u0, plane, z1)]
        natural = -1
    else:
        pts = [(plane, u0, z0), (plane, u1, z0), (plane, u1, z1), (plane, u0, z1)]
        natural = 1
    if outward != natural:
        pts.reverse()
    b.add_poly(pts, conf, mat)


def _kit(b: MeshBuilder, board: bool = False) -> openings.Mats:
    """The openings kit's materials (T-2278): casing and sash in the building's pale
    trim, the town's glass (Glessner's dark pane), a door leaf dealt a paint — a
    garrison's doors were painted at public cost — or iron-strapped board for the
    magazine, and strap iron."""
    rgba, rough = openings.WEATHERED_BOARD if board else openings.door_paint(b.name, True)
    key = "board_door" if board else "door"
    return openings.Mats(
        casing=M_TRIM, sash=M_TRIM, dark=M_DARK,
        glass=b.named_mat("glass", *openings.glass_material_spec()),
        door=b.named_mat(key, rgba, rough),
        panel=b.named_mat(key + "_panel", openings.shade(rgba, 0.70), rough),
        iron=b.named_mat("iron", *openings.STRAP_IRON))


def _opening(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
             z0: float, z1: float, outward: int, conf: float, kind: str = "window",
             relief: float = RELIEF_M) -> None:
    """A door or window, built by the shared openings kit (T-2278).

    Before this both were a dark panel inside a sawn surround, so the garrison's
    quarters stood open onto black doorways. A garrison of 1816-35 was glazed — glass
    came up the lakes with every supply schooner — so a window is a cased six-over-six
    sash over the town's dark glass; a door is a closed panelled leaf; the magazine's
    is iron-strapped board.
    """
    w = openings.Wall(axis, plane, outward, relief)
    if kind == "door":
        openings.panelled_door(b, w, u0, u1, z0, z1, conf, _kit(b))
    elif kind == "magazine":
        openings.batten_door(b, w, u0, u1, z0, z1, conf, _kit(b, board=True),
                             seed=b.name, boards=4, cap=True)
    else:
        openings.window(b, w, u0, u1, z0, z1, conf, _kit(b), 3, (2, 2))


def _string_course(b: MeshBuilder, x0, y0, x1, y1, wall_z, conf) -> None:
    """A brick building gets one proud course near the head of the wall.

    The only external difference between a brick building and a log one at fifty
    metres is the colour and the flatness; one string course keeps the flat wall
    from reading as a painted block without inventing a cornice.
    """
    z = wall_z - 0.34
    lip = 0.035
    b.add_poly([(x0, y0, z), (x1, y0, z), (x1, y0 - lip, z - 0.10),
                (x0, y0 - lip, z - 0.10)], conf, M_WALL)
    b.add_poly([(x1, y1, z), (x0, y1, z), (x0, y1 + lip, z - 0.10),
                (x1, y1 + lip, z - 0.10)], conf, M_WALL)


def _openings(b: MeshBuilder, p: FortStructureParams, lower_z: float,
              over: float) -> None:
    """Use explicit range rectangles when present, otherwise retain legacy layout.

    The 1808 folded elevations show range bay counts. Their exact metric set-out,
    doorway identities and unpictured rear layouts remain reconstructed choices.
    """
    if p.face_openings is not None:
        _explicit_openings(b, p)
        return
    conf = p.conf("fenestration", "reconstructed")
    w, d, wz = p.width_m, p.depth_m, p.wall_height_m
    bays = max(2, min(8, int(round(w / 3.4))))
    sh = p.storey_height_m
    xm = w / 2.0
    door = p.kind not in ("magazine",)

    for storey in range(p.stories):
        z0 = storey * sh + sh * 0.30
        hi = z0 + min(1.05, sh * 0.42)
        for i in range(bays):
            u = w * (i + 0.5) / bays
            if storey == 0 and door and abs(u - xm) < w / (2.0 * bays):
                continue
            _opening(b, "y", d, u - 0.36, u + 0.36, z0, hi, 1, conf)
        for i in range(max(1, bays - 1)):
            u = w * (i + 0.5) / max(1, bays - 1)
            _opening(b, "y", 0.0, u - 0.33, u + 0.33, z0, hi, -1, conf)
    if door:
        _opening(b, "y", d, xm - 0.55, xm + 0.55, 0.02, 2.05, 1, conf, kind="door")


def _magazine_door(b: MeshBuilder, p: FortStructureParams, conf: float) -> None:
    """A powder magazine has one door and no windows. That is not a simplification;
    it is the defining fact about the building type."""
    xm = p.width_m / 2.0
    _opening(b, "y", p.depth_m, xm - 0.45, xm + 0.45, 0.02, 1.85, 1, conf,
             kind="magazine")


def _loopholes(b: MeshBuilder, p: FortStructureParams, lower_z: float,
               over: float, conf: float) -> None:
    """Slits for small arms, on the jettied storey of a blockhouse.

    Set high in the wall and spaced along all four faces, which is what a
    blockhouse is for. Nothing at Fort Dearborn attests them; the record turns
    them on and docs/LIBERTIES.md owns the pattern.
    """
    w, d = p.width_m, p.depth_m
    o = p.overhang_m
    z = lower_z + 0.18 + p.storey_height_m * 0.48
    n_w = max(2, int(w / 2.2))
    n_d = max(2, int(d / 2.2))
    for i in range(n_w):
        u = -o + (w + 2 * o) * (i + 0.5) / n_w
        _panel(b, "y", d + o + 0.02, u - 0.05, u + 0.05, z, z + 0.36, 1, conf, M_DARK)
        _panel(b, "y", -o - 0.02, u - 0.05, u + 0.05, z, z + 0.36, -1, conf, M_DARK)
    for i in range(n_d):
        v = -o + (d + 2 * o) * (i + 0.5) / n_d
        _panel(b, "x", w + o + 0.02, v - 0.05, v + 0.05, z, z + 0.36, 1, conf, M_DARK)
        _panel(b, "x", -o - 0.02, v - 0.05, v + 0.05, z, z + 0.36, -1, conf, M_DARK)


def _gallery(b: MeshBuilder, p: FortStructureParams, conf: float) -> None:
    """A covered gallery; the opt-in upper walk leaves the original default intact."""
    if p.gallery_storeys == 2:
        _gallery_two_storeys(b, p, conf)
        return
    w, d, wz = p.width_m, p.depth_m, p.wall_height_m
    reach = 2.1
    head = min(wz - 0.25, p.storey_height_m + 0.15)
    n = max(2, int(round(w / 3.0)))
    for i in range(n + 1):
        x = w * i / n
        b.add_box(x - 0.07, d + reach - 0.14, 0.0, x + 0.07, d + reach, head,
                  conf, M_TRIM, skip=("bottom",))
    b.add_box(0.0, d + reach - 0.16, head, w, d + reach, head + 0.16, conf, M_TRIM)
    b.add_poly([(0.0, d, head + 0.5), (w, d, head + 0.5),
                (w, d + reach + 0.15, head), (0.0, d + reach + 0.15, head)],
               conf, M_ROOF)


def _chimneys(b: MeshBuilder, p: FortStructureParams, ridge_z: float,
              conf: float, mat: int) -> None:
    """As many stacks as the record counts, spaced across the building's length.

    The count is the record's; every other property of a stack is the archetype's,
    exactly as it is for the dwellings, and docs/LIBERTIES.md owns the arrangement.

    **These stacks are INTERIOR**, and the geometry below is the whole of that claim:
    each one stands on the depth midline (`yc`), rises from the ground INSIDE the
    building and breaks the roof at the ridge. That is not the disposition of the log
    cabins across the river — `log_dwelling._stack` builds against the gable, outside
    the wall, precisely so a stick-and-clay flue can be pulled away when it fires —
    and it is what decides the fabric in `build()`. T-0137.
    """
    w, d = p.width_m, p.depth_m
    yc = d / 2.0
    half_x, half_y = 0.46, 0.52
    for i in range(p.chimneys):
        x = w * (i + 0.5) / p.chimneys
        b.add_box(x - half_x, yc - half_y, 0.0, x + half_x, yc + half_y,
                  ridge_z + 0.60, conf, mat, skip=("bottom",))
        b.add_box(x - half_x - 0.08, yc - half_y - 0.08, ridge_z + 0.60,
                  x + half_x + 0.08, yc + half_y + 0.08, ridge_z + 0.78,
                  conf, mat, skip=("bottom",))


# ------------------------------------------------------------ ground furniture

def _parade(b: MeshBuilder, p: FortStructureParams) -> None:
    """The parade ground: a trodden, slightly proud rectangle of bare earth.

    Built at all because a fort with no parade is a courtyard of loose buildings,
    and because the one interior dimension any source gives is the parade's. Six
    centimetres proud is the whole claim: this is ground worn bare and packed by
    a garrison, not a paved surface, and nothing describes it as anything else.
    """
    conf = p.worst_conf("kind")
    w, d = p.width_m, p.depth_m
    b.add_box(0.0, 0.0, 0.0, w, d, 0.06, conf, M_WALL, skip=("bottom",))
    if p.sun_dial:
        _sun_dial(b, p, p.conf("sun_dial", "reconstructed"))


def _sun_dial(b: MeshBuilder, p: FortStructureParams, conf: float) -> None:
    """Robert Fergus's sun-dial: "an 8-inch piece of square timber, imbedded in the
    earth, placed upright, about 2 feet high, upon the top of which was a brass
    plate on which had been a sun-dial". Both dimensions are his; the position on
    the parade is not, and the record says so."""
    x, y = p.width_m / 2.0, p.depth_m * 0.22
    h = 0.61                      # two feet
    s = 0.203 / 2.0               # eight inches
    b.add_box(x - s, y - s, 0.0, x + s, y + s, h, conf, M_TRIM, skip=("bottom",))
    b.add_box(x - s - 0.02, y - s - 0.02, h, x + s + 0.02, y + s + 0.02, h + 0.02,
              conf, M_DARK, skip=("bottom",))


def _root_house(b: MeshBuilder, p: FortStructureParams) -> None:
    """A root house: a cellar banked over with earth, with a plank door in one end.

    Juliette Kinzie puts the garrison's root-houses on the river bank west of the
    fort in 1831 and says nothing else about them. What a root house IS supplies
    the rest: a bank of earth over a cellar, which is why it survives as a mound
    and not as a building.
    """
    conf = p.worst_conf("kind", "construction")
    w, d, h = p.width_m, p.depth_m, p.wall_height_m
    inset = min(w, d) * 0.22
    lo = [(0.0, 0.0), (w, 0.0), (w, d), (0.0, d)]
    hi = [(inset, inset), (w - inset, inset), (w - inset, d - inset), (inset, d - inset)]
    for i in range(4):
        (ax, ay), (bx, by) = lo[i], lo[(i + 1) % 4]
        (cx, cy), (dx, dy) = hi[i], hi[(i + 1) % 4]
        b.add_poly([(ax, ay, 0.0), (bx, by, 0.0), (dx, dy, h), (cx, cy, h)],
                   conf, M_WALL)
    b.add_poly([(x, y, h) for x, y in hi], conf, M_WALL)
    xm = w / 2.0
    _panel(b, "y", d - inset * 0.35, xm - 0.42, xm + 0.42, 0.02, h * 0.72, 1,
           conf, M_TRIM)
    _panel(b, "y", d - inset * 0.35 + 0.01, xm - 0.34, xm + 0.34, 0.06, h * 0.66, 1,
           conf, M_DARK)



def _flagstaff(b: MeshBuilder, p: FortStructureParams) -> None:
    """A bare tapering spar: the garrison flagstaff.

    **Why the mesh stops at the truck.** The flag is not baked here. Andreas has the
    1835 staff fly "a weather-beaten flag ... IN PLEASANT WEATHER AND ON HOLIDAYS",
    so whether it is up is a claim about one forenoon, and since T-2124 the staff's
    record says so in its own attributes (`flag`, `flag_flying`, each graded) and
    the renderer's flags.js hangs and moves the cloth from them. The spar is what is
    attested; the bunting is a separate, separately-graded layer (L390).

    **What is the archetype's.** Everything except the height. No source reached
    gives the second fort's staff a thickness, a taper, a truck or a step, so the
    spar's whole profile is ours and docs/LIBERTIES.md owns it. Eight sides, not
    twelve: this is a 0.3 m pole and the four extra facets buy nothing at any
    distance a visitor can stand at.
    """
    c = p.worst_conf("kind", "wall_height_m", "construction")
    n = 8
    r0 = p.mast_butt_m / 2.0
    r1 = p.mast_truck_m / 2.0
    cx, cy = p.width_m / 2.0, p.depth_m / 2.0
    h = p.wall_height_m

    def ring(r, z):
        return [(cx + r * math.cos(2 * math.pi * i / n),
                 cy + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]

    lo, up = ring(r0, 0.0), ring(r1, h)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([lo[i], lo[j], up[j], up[i]], c, M_WALL)
    b.add_poly(list(reversed(up)), c, M_WALL)

def _tower(b: MeshBuilder, p: FortStructureParams) -> None:
    """A tapering round tower with a gallery and a lantern: the 1832 lighthouse.

    The shaft's dimensions remain the earlier reconstruction. T-2373's
    opt-in lantern profile reads its dome, cage and gallery rail from the
    Castelnau harbour lithograph; exact sections/counts remain reconstructed.
    See docs/LIBERTIES.md L-lighthouse-visible-prototype-2373.
    """
    c = p.worst_conf("kind", "wall_height_m", "construction")
    if p.tower_diameter_m is not None:
        c = max(c, p.conf("tower_diameter_m"), p.conf("footprint"))
    n = 12
    r0 = (p.tower_diameter_m if p.tower_diameter_m is not None else p.width_m) / 2.0
    r1 = r0 * p.taper
    # Keep polygon-origin coordinates; narrowing the disk must not move its centre.
    cx = p.footprint_min_u_m + p.width_m / 2.0
    cy = p.footprint_min_v_m + p.width_m / 2.0
    h = p.wall_height_m
    shaft = h * 0.86
    if p.tower_profile is not None:
        shaft = p.tower_shaft_height_m

    def ring(r, z):
        return [(cx + r * math.cos(2 * math.pi * i / n),
                 cy + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]

    lo, up = ring(r0, 0.0), ring(r1, shaft)
    if p.tower_masonry is not None:
        if p.tower_masonry.get('character','legacy_courses') == 'irregular_rubble':
            _tower_irregular_stone_shaft(b,p,cx,cy,r0,shaft)
        else:
            _tower_stone_shaft(b,p,cx,cy,r0,shaft)
    else:
        for i in range(n):
            j = (i + 1) % n
            b.add_poly([lo[i], lo[j], up[j], up[i]], c, M_WALL)
        if p.tower_openings:
            _tower_apertures(b, p, cx, cy, r0, shaft)

    if not p.lantern:
        b.add_poly(list(reversed(up)), c, M_ROOF)
        return

    if p.lantern_profile == "birdcage_dome":
        _birdcage_lantern(b, p, cx, cy, r1, shaft, h)
        return

    c_l = p.conf("lantern", "reconstructed")
    gal = ring(r1 * 1.34, shaft)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([up[i], up[j], gal[j], gal[i]], c_l, M_TRIM)
    galt = ring(r1 * 1.34, shaft + 0.09)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([gal[i], gal[j], galt[j], galt[i]], c_l, M_TRIM)
    lant = ring(r1 * 0.86, shaft + 0.09)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([galt[i], galt[j], lant[j], lant[i]], c_l, M_TRIM)
    top = ring(r1 * 0.86, h)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([lant[i], lant[j], top[j], top[i]], c_l, M_DARK)
    apex = (cx, cy, h + r1 * 0.7)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([top[i], top[j], apex], c_l, M_ROOF)


def _gallery_two_storeys(b: MeshBuilder, p: FortStructureParams, conf: float) -> None:
    """A covered upper walk over an open ground gallery, after Currey's 1912 plate.

    Occurrence is inferred; the 2.1 m reach (the old gallery's), floor thickness,
    post sections, 0.95 m rail, 0.18 m baluster pitch and roof fall are reconstructed.
    All new pieces therefore carry reconstructed geometry confidence. The draught
    supplies no gallery dimension, and its folded elevations are not height scales.
    """
    w, d, wz = p.width_m, p.depth_m, p.wall_height_m
    reach, post, deck, rail, pitch, baluster = 2.1, 0.14, 0.14, 0.95, 0.18, 0.055
    upper = p.storey_height_m
    # The gallery roof meets the wall at its existing eave and falls 0.45 m.
    # No old ground-level lean-to roof remains underneath the upper walk.
    head = wz - 0.45
    c = max(conf, p.conf("gallery_storeys"), 1.0)
    for x in _gallery_post_centres(p, post):
        b.add_box(x - post / 2, d + reach - post, 0.0,
                  x + post / 2, d + reach, head - post, c, M_TRIM,
                  skip=("bottom",))
    # The canopy falls across reach + its 0.15 m outer projection. Its height
    # above the beam is therefore higher than `head`, the outer roof edge.
    # Keep the beam bottom/posts fixed and meet that same plane with a wedge.
    y0, y1, z0 = d + reach - post, d + reach, head - post
    z1 = wz + (head - wz) * ((y0 - d) / (reach + 0.15))
    z2 = wz + (head - wz) * ((y1 - d) / (reach + 0.15))
    for face in (
        [(0.0, y0, z0), (w, y0, z0), (w, y1, z0), (0.0, y1, z0)],
        [(0.0, y0, z0), (0.0, y0, z1), (w, y0, z1), (w, y0, z0)],
        [(w, y1, z0), (w, y1, z2), (0.0, y1, z2), (0.0, y1, z0)],
        [(0.0, y1, z0), (0.0, y1, z2), (0.0, y0, z1), (0.0, y0, z0)],
        [(w, y0, z0), (w, y0, z1), (w, y1, z2), (w, y1, z0)],
    ):
        b.add_poly(face, c, M_TRIM)
    # The canopy caps the joint. Omit a coplanar timber top: both materials
    # are double-sided, so duplicating that surface would cause z-fighting.
    b.add_box(0.0, d, upper - deck, w, d + reach, upper, c, M_TRIM)
    # Long outer handrail and evenly spaced vertical pales; the two short ends
    # are closed as a safety reconstruction. No external stair is invented.
    b.add_box(0.0, d + reach - post, upper + rail - 0.10,
              w, d + reach, upper + rail, c, M_TRIM)
    count = max(1, math.ceil(w / pitch))
    for i in range(count):
        x = w * (i + 0.5) / count
        b.add_box(x - baluster / 2, d + reach - post / 2 - baluster / 2, upper,
                  x + baluster / 2, d + reach - post / 2 + baluster / 2,
                  upper + rail - 0.10, c, M_TRIM)
    for x in (0.0, w - post):
        b.add_box(x, d, upper + rail - 0.10,
                  x + post, d + reach - post, upper + rail, c, M_TRIM)
        count = max(1, math.ceil((reach - post) / pitch))
        for i in range(count):
            y = d + (reach - post) * (i + 0.5) / count
            b.add_box(x + (post - baluster) / 2, y - baluster / 2, upper,
                      x + (post + baluster) / 2, y + baluster / 2,
                      upper + rail - 0.10, c, M_TRIM)
    b.add_poly([(0.0, d, wz), (w, d, wz),
                (w, d + reach + 0.15, head), (0.0, d + reach + 0.15, head)],
               c, M_ROOF)


def _explicit_openings(b: MeshBuilder, p: FortStructureParams) -> None:
    """The same rectangles returned by the Blender-free facade reader."""
    planes = {"front": ("y", p.depth_m, 1), "back": ("y", 0.0, -1),
              "left": ("x", 0.0, -1), "right": ("x", p.width_m, 1)}
    conf = max(p.conf("face_openings"), 1.0)
    for face, (axis, plane, outward) in planes.items():
        for o in wall_openings(p, face):
            _opening(b, axis, plane, o["u0"], o["u1"], o["z0"], o["z1"],
                     outward, conf, kind=o["kind"])


def _gallery_post_centres(p: FortStructureParams, post: float) -> list[float]:
    """Keep the old support rhythm, projecting explicit-front posts onto solid piers.

    Only the opt-in two-storey gallery calls this. Missing/empty explicit fronts
    retain the exact old grid. Where a front is declared, posts clear the union
    of BOTH storeys' rectangles plus their existing casing/sill horns. Project
    each old interior centre to the nearest permitted interval, left on ties;
    reserve one post width between centres. Count/sections and this placement
    rule remain reconstructed, not joinery measured from Whistler's drawing.
    """
    w = p.width_m
    n = max(2, int(round(w / 3.0)))
    legacy = [w * i / n for i in range(n + 1)]
    front = wall_openings(p, "front")
    if not front:
        return legacy
    # The existing window kit's horn extends farther than its cap or door trim.
    # Include half the actual post section so its whole face clears that kit.
    margin = post / 2 + openings.CASING_W_M + openings.SILL_HORN_M
    for o in front:
        if o["u0"] - margin <= 0 or o["u1"] + margin >= w:
            raise ValueError("explicit gallery front leaves no clear end support")
    spans = [(post, w - post)]

    def subtract(spans, lo, hi):
        out = []
        for a, b in spans:
            if hi <= a or lo >= b:
                out.append((a, b))
            else:
                if a < lo:
                    out.append((a, lo))
                if hi < b:
                    out.append((hi, b))
        return [(a, b) for a, b in out if b >= a]

    for o in front:
        spans = subtract(spans, o["u0"] - margin, o["u1"] + margin)
    result = [0.0, w]
    for wanted in legacy[1:-1]:
        if not spans:
            raise ValueError("explicit gallery front has no clear support pier")
        x = min((min(max(wanted, a), b) for a, b in spans),
                key=lambda v: (abs(v - wanted), v))
        result.append(x)
        spans = subtract(spans, x - post, x + post)
    return sorted(result)


def _birdcage_lantern(b: MeshBuilder, p: FortStructureParams,
                      cx: float, cy: float, r1: float,
                      shaft: float, h: float) -> None:
    """T-2373: a pictured lantern silhouette, with reconstructed scantlings.

    Eight cage uprights, twelve gallery posts, a rounded cap and a finial.
    All counts and sections are choices within the small retrospective view.
    No shaft, footprint, paint, coordinate or reflector is derived here.
    The old upper silhouette limit h + 0.7*r1 is retained: how Andreas's
    forty feet relates to the existing shaft/lantern split remains open.
    """
    if p.tower_profile is not None:
        _birdcage_partitioned(b, p, cx, cy, r1, shaft, h)
        return
    # All emitted members include reconstructed counts, sections and curves.
    c = 1.0
    glass = b.named_mat("lantern_glass", *openings.glass_material_spec())
    n = 12
    gal_r, lantern_r = r1 * 1.34, r1 * 0.86
    floor = shaft + 0.09

    def ring(radius, z, count=n):
        return [(cx + radius * math.cos(2 * math.pi * i / count),
                 cy + radius * math.sin(2 * math.pi * i / count), z)
                for i in range(count)]

    def band(inner, outer, bottom, top, mat):
        li, lo = ring(inner, bottom), ring(outer, bottom)
        ui, up = ring(inner, top), ring(outer, top)
        for i in range(n):
            j = (i + 1) % n
            b.add_poly([li[i], li[j], lo[j], lo[i]], c, mat)
            b.add_poly([ui[i], up[i], up[j], ui[j]], c, mat)
            b.add_poly([lo[i], lo[j], up[j], up[i]], c, mat)
            b.add_poly([li[j], li[i], ui[i], ui[j]], c, mat)

    # Full gallery floor; its underside meets the existing shaft at shaft.
    lower, upper = ring(gal_r, shaft), ring(gal_r, floor)
    b.add_poly(list(reversed(lower)), c, M_TRIM)
    b.add_poly(upper, c, M_TRIM)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([lower[i], lower[j], upper[j], upper[i]], c, M_TRIM)

    # The rail's height, 45 mm square posts and 55 by 50 mm ring are
    # reconstructed. Existing DARK is a neutral frame proxy, not known paint.
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = cx + (gal_r - 0.035) * math.cos(a), cy + (gal_r - 0.035) * math.sin(a)
        b.add_box(x - 0.0225, y - 0.0225, floor,
                  x + 0.0225, y + 0.0225, floor + 0.65, c, M_DARK)
    band(gal_r - 0.055, gal_r, floor + 0.60, floor + 0.65, M_DARK)

    # Pane surface plus visible cage members, using the town's existing
    # dark glossy GLASS row. No new optical or transparency claim.
    bottom, top = ring(lantern_r, floor), ring(lantern_r, h)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([bottom[i], bottom[j], top[j], top[i]], c, glass)
    for i in range(8):
        a = 2 * math.pi * i / 8
        x, y = cx + (lantern_r + 0.012) * math.cos(a), cy + (lantern_r + 0.012) * math.sin(a)
        b.add_box(x - 0.0275, y - 0.0275, floor,
                  x + 0.0275, y + 0.0275, h, c, M_DARK)
    band(lantern_r - 0.025, lantern_r + 0.04, floor, floor + 0.06, M_DARK)
    band(lantern_r - 0.025, lantern_r + 0.04, h - 0.06, h, M_DARK)

    # Six latitudinal bands round the cap instead of the old pointed pyramid.
    # A slight skirt covers the twelve-sided drum below this 24-sided cap.
    cap_r, rise = lantern_r * 1.06, r1 * 0.55
    last = ring(cap_r, h, 24)
    b.add_poly(list(reversed(last)), c, M_ROOF)
    for k in range(1, 6):
        angle = (math.pi / 2.0) * k / 6.0
        current = ring(cap_r * math.cos(angle), h + rise * math.sin(angle), 24)
        for i in range(24):
            j = (i + 1) % 24
            b.add_poly([last[i], last[j], current[j], current[i]], c, M_ROOF)
        last = current
    apex = (cx, cy, h + rise)
    for i in range(24):
        b.add_poly([last[i], last[(i + 1) % 24], apex], c, M_ROOF)

    # Slender finial, its top at the previous profile's maximum height.
    fin_r, fin_h = max(0.025, r1 * 0.025), r1 * 0.15
    lo = ring(fin_r, h + rise, 8)
    hi = ring(fin_r, h + rise + fin_h * 0.8, 8)
    for i in range(8):
        j = (i + 1) % 8
        b.add_poly([lo[i], lo[j], hi[j], hi[i]], c, M_DARK)
        b.add_poly([hi[i], hi[j], (cx, cy, h + rise + fin_h)], c, M_DARK)

class _TowerFacetBuilder:
    """Map the existing openings kit onto one EXISTING tapered shaft facet.

    Local kit y is outward relief; x runs along the facet. Reversing winding
    compensates for this handedness change. No common kit/API is modified.
    """
    def __init__(self, builder, cx, cy, radius, taper, shaft, azimuth_deg):
        self.builder, self.cx, self.cy = builder, cx, cy
        self.radius, self.taper, self.shaft = radius, taper, shaft
        a = math.radians(azimuth_deg)
        self.normal, self.tangent = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))

    def add_poly(self, points, confidence, mat=0):
        mapped = []
        for u, relief, z in points:
            radius = self.radius*(1-(1-self.taper)*z/self.shaft)*math.cos(math.pi/12)
            mapped.append((self.cx+(radius+relief)*self.normal[0]+u*self.tangent[0],
                           self.cy+(radius+relief)*self.normal[1]+u*self.tangent[1], z))
        return self.builder.add_poly(list(reversed(mapped)), confidence, mat)

def _tower_apertures(b: MeshBuilder, p: FortStructureParams, cx: float, cy: float,
                     radius: float, shaft: float) -> None:
    """Three tiny pictured apertures, with reconstructed metric windows/glazing.

    Their trim, one-pane interpretation, facet assignments and vertical fractions
    are choices; the dark source marks do not attest joinery or a ground door.
    """
    mats = openings.Mats(casing=M_TRIM, sash=M_TRIM,
                         glass=b.named_mat("lantern_glass", *openings.glass_material_spec()))
    for o in tower_opening_layout(p):
        mapped = _TowerFacetBuilder(b, cx, cy, radius, p.taper, shaft, o["azimuth_deg"])
        openings.window(mapped, openings.Wall("y", 0., 1), o["u0"], o["u1"],
                        o["z0"], o["z1"], 1.0, mats, 1, None)

def _birdcage_partitioned(b: MeshBuilder, p: FortStructureParams, cx: float, cy: float, r1: float, shaft: float, h: float) -> None:
    """Reconstructed partition from Castelnau controls; same overall envelope.

    Nominal40ft datum remains unresolved. New shaft/cage/cap/rail subdivision
    changes no ground height, footprint, origin, bearing or overall maximum.
    """
    if p.tower_lantern_detail is not None:
        _birdcage_clear_detail(b, p, cx, cy, r1, shaft, h)
        return
    cap_base = p.tower_profile['cap_base_m']
    rail = p.tower_profile['gallery_rail_height_m']
    maximum = h + r1 * 0.7
    cap_total = maximum - cap_base
    c = 1.0
    glass = b.named_mat('lantern_glass', *openings.glass_material_spec())
    n = 12
    gal_r, lantern_r = (r1 * 1.34, r1 * 0.86)
    floor = shaft + 0.09

    def ring(radius, z, count=n):
        return [(cx + radius * math.cos(2 * math.pi * i / count), cy + radius * math.sin(2 * math.pi * i / count), z) for i in range(count)]

    def band(inner, outer, bottom, top, mat):
        li, lo = (ring(inner, bottom), ring(outer, bottom))
        ui, up = (ring(inner, top), ring(outer, top))
        for i in range(n):
            j = (i + 1) % n
            b.add_poly([li[i], li[j], lo[j], lo[i]], c, mat)
            b.add_poly([ui[i], up[i], up[j], ui[j]], c, mat)
            b.add_poly([lo[i], lo[j], up[j], up[i]], c, mat)
            b.add_poly([li[j], li[i], ui[i], ui[j]], c, mat)
    lower, upper = (ring(gal_r, shaft), ring(gal_r, floor))
    b.add_poly(list(reversed(lower)), c, M_TRIM)
    b.add_poly(upper, c, M_TRIM)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([lower[i], lower[j], upper[j], upper[i]], c, M_TRIM)
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = (cx + (gal_r - 0.035) * math.cos(a), cy + (gal_r - 0.035) * math.sin(a))
        b.add_box(x - 0.0225, y - 0.0225, floor, x + 0.0225, y + 0.0225, floor + rail, c, M_DARK)
    band(gal_r - 0.055, gal_r, floor + rail - 0.05, floor + rail, M_DARK)
    bottom, top = (ring(lantern_r, floor), ring(lantern_r, cap_base))
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([bottom[i], bottom[j], top[j], top[i]], c, glass)
    for i in range(8):
        a = 2 * math.pi * i / 8
        x, y = (cx + (lantern_r + 0.012) * math.cos(a), cy + (lantern_r + 0.012) * math.sin(a))
        b.add_box(x - 0.0275, y - 0.0275, floor, x + 0.0275, y + 0.0275, cap_base, c, M_DARK)
    band(lantern_r - 0.025, lantern_r + 0.04, floor, floor + 0.06, M_DARK)
    band(lantern_r - 0.025, lantern_r + 0.04, cap_base - 0.06, cap_base, M_DARK)
    cap_r, rise = (lantern_r * 1.06, cap_total * 0.55 / 0.7)
    last = ring(cap_r, cap_base, 24)
    b.add_poly(list(reversed(last)), c, M_ROOF)
    for k in range(1, 6):
        angle = math.pi / 2.0 * k / 6.0
        current = ring(cap_r * math.cos(angle), cap_base + rise * math.sin(angle), 24)
        for i in range(24):
            j = (i + 1) % 24
            b.add_poly([last[i], last[j], current[j], current[i]], c, M_ROOF)
        last = current
    apex = (cx, cy, cap_base + rise)
    for i in range(24):
        b.add_poly([last[i], last[(i + 1) % 24], apex], c, M_ROOF)
    fin_r, fin_h = (max(0.025, r1 * 0.025), cap_total * 0.15 / 0.7)
    lo = ring(fin_r, cap_base + rise, 8)
    hi = ring(fin_r, cap_base + rise + fin_h * 0.8, 8)
    for i in range(8):
        j = (i + 1) % 8
        b.add_poly([lo[i], lo[j], hi[j], hi[i]], c, M_DARK)
        b.add_poly([hi[i], hi[j], (cx, cy, cap_base + rise + fin_h)], c, M_DARK)

def _birdcage_clear_detail(b: MeshBuilder, p: FortStructureParams, cx: float, cy: float, r1: float, shaft: float, h: float) -> None:
    """Castelnau light cage, fine rail and shallow crown; reconstructed controls.

    Nominal40ft datum remains unresolved. New shaft/cage/cap/rail subdivision
    changes no ground height, footprint, origin, bearing or overall maximum.
    """
    d = p.tower_lantern_detail
    cap_base = p.tower_profile['cap_base_m']
    rail = p.tower_profile['gallery_rail_height_m']
    maximum = h + r1 * 0.7
    cap_total = maximum - cap_base
    c = 1.0
    glass = b.named_mat('lantern_cage_glass', *openings.glass_material_spec())
    n = 12
    gal_r, lantern_r = (r1 * 1.34, r1 * 0.86)
    floor = shaft + 0.09

    def ring(radius, z, count=n):
        return [(cx + radius * math.cos(2 * math.pi * i / count), cy + radius * math.sin(2 * math.pi * i / count), z) for i in range(count)]

    def band(inner, outer, bottom, top, mat):
        li, lo = (ring(inner, bottom), ring(outer, bottom))
        ui, up = (ring(inner, top), ring(outer, top))
        for i in range(n):
            j = (i + 1) % n
            b.add_poly([li[i], li[j], lo[j], lo[i]], c, mat)
            b.add_poly([ui[i], up[i], up[j], ui[j]], c, mat)
            b.add_poly([lo[i], lo[j], up[j], up[i]], c, mat)
            b.add_poly([li[j], li[i], ui[i], ui[j]], c, mat)
    lower, upper = (ring(gal_r, shaft), ring(gal_r, floor))
    b.add_poly(list(reversed(lower)), c, M_TRIM)
    b.add_poly(upper, c, M_TRIM)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([lower[i], lower[j], upper[j], upper[i]], c, M_DARK)
    for i in range(d["gallery_posts"]):
        a = 2 * math.pi * i / d["gallery_posts"]
        x, y = (cx + (gal_r - 0.035) * math.cos(a), cy + (gal_r - 0.035) * math.sin(a))
        b.add_box(x - d["gallery_member_m"]/2, y - d["gallery_member_m"]/2, floor, x + d["gallery_member_m"]/2, y + d["gallery_member_m"]/2, floor + rail, c, M_DARK)
    band(gal_r - d["gallery_member_m"], gal_r, floor + rail - d["gallery_member_m"], floor + rail, M_DARK)
    band(gal_r - d["gallery_member_m"], gal_r, floor + .08, floor + .08 + d["gallery_member_m"], M_DARK)
    bottom, top = (ring(lantern_r, floor + d["sill_height_m"]), ring(lantern_r, cap_base))
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([bottom[i], bottom[j], top[j], top[i]], c, glass)
    for i in range(d["cage_uprights"]):
        a = 2 * math.pi * i / d["cage_uprights"]
        x, y = (cx + (lantern_r + 0.012) * math.cos(a), cy + (lantern_r + 0.012) * math.sin(a))
        b.add_box(x - d["cage_member_m"]/2, y - d["cage_member_m"]/2, floor, x + d["cage_member_m"]/2, y + d["cage_member_m"]/2, cap_base, c, M_DARK)
    band(lantern_r - 0.025, lantern_r + 0.04, floor, floor + d["sill_height_m"], M_DARK)
    band(lantern_r - 0.025, lantern_r + 0.04, cap_base - 0.06, cap_base, M_DARK)
    cap_r, rise = (lantern_r * 1.06, d["dome_rise_m"])
    last = ring(cap_r, cap_base, 24)
    b.add_poly(list(reversed(last)), c, M_DARK)
    for k in range(1, 6):
        angle = math.pi / 2.0 * k / 6.0
        current = ring(cap_r * math.cos(angle), cap_base + rise * math.sin(angle), 24)
        for i in range(24):
            j = (i + 1) % 24
            b.add_poly([last[i], last[j], current[j], current[i]], c, M_DARK)
        last = current
    apex = (cx, cy, cap_base + rise)
    for i in range(24):
        b.add_poly([last[i], last[(i + 1) % 24], apex], c, M_DARK)
    fin_r, fin_h = (d["finial_radius_m"], cap_total-rise)
    lo = ring(fin_r, cap_base + rise, 8)
    hi = ring(fin_r, cap_base + rise + fin_h * 0.8, 8)
    for i in range(8):
        j = (i + 1) % 8
        b.add_poly([lo[i], lo[j], hi[j], hi[i]], c, M_DARK)
        b.add_poly([hi[i], hi[j], (cx, cy, cap_base + rise + fin_h)], c, M_DARK)

def _configure_cage_glass(ob, p: FortStructureParams) -> None:
    """Lantern-only alpha; shaft panes and the common glass sheet stay opaque.

    Alpha is explicitly set on Principled BSDF: Base Color alpha alone is not
    the glTF exporter alpha input. Blender4.5's exporter reads constant Alpha
    into baseColorFactor[3]/alphaMode BLEND; actual GLB+GLTFLoader checks follow.
    No transmission extension or second opaque-scene transmission pass is used.
    """
    opacity = p.tower_lantern_detail["pane_opacity"]
    rows = [m for m in ob.data.materials if m.name == "lantern_cage_glass"]
    if len(rows) != 1:
        raise RuntimeError("expected exactly one lantern-only cage glass")
    m = rows[0]
    node = m.node_tree.nodes.get("Principled BSDF")
    if node is None:
        raise RuntimeError("lantern cage material has no Principled BSDF")
    node.inputs["Alpha"].default_value = opacity
    rgba = tuple(m.diffuse_color)
    m.diffuse_color = (*rgba[:3], opacity)
    m.surface_render_method = "DITHERED"

def _stone_clip(poly, axis, value, keep_above):
    """Convex polygon clip in local tangent/height coordinates, no image data."""
    if not poly:
        return []
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ia = a[axis] >= value if keep_above else a[axis] <= value
        ib = b[axis] >= value if keep_above else b[axis] <= value
        if ia:
            out.append(a)
        if ia != ib:
            t = (value-a[axis])/(b[axis]-a[axis])
            out.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(2)))
    # Remove repeated boundary points before triangulation.
    clean = []
    for q in out:
        if not clean or math.dist(q, clean[-1]) > 1e-10:
            clean.append(q)
    if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-10:
        clean.pop()
    return clean if len(clean)>=3 else []

def _stone_without_apertures(poly, openings):
    """Four disjoint strips subtract each actual aperture rectangle."""
    parts = [poly]
    for o in openings:
        next_parts = []
        for q in parts:
            left = _stone_clip(q,0,o['u0'],False)
            right = _stone_clip(q,0,o['u1'],True)
            middle = _stone_clip(_stone_clip(q,0,o['u0'],True),0,o['u1'],False)
            lower = _stone_clip(middle,1,o['z0'],False)
            upper = _stone_clip(middle,1,o['z1'],True)
            next_parts.extend(p for p in (left,right,lower,upper) if p)
        parts = next_parts
    return parts

def _tower_stone_palette(b, p: FortStructureParams):
    """Reuse a wall material only when its entire stone PBR descriptor agrees.

    The unit-tone bare stone is already M_WALL; a duplicate name would be lost
    by native derivative deduplication. Coated walls keep their separate stone.
    """
    base = WALL_RGBA['stone']
    wall = PAINT_OVER.get(p.paint, WALL_RGBA.get(p.construction, WALL_RGBA['log']))
    substrate = materials.wall_substrate(construction=p.construction, default='hewn_log')
    _, roughness = materials.resolve(substrate, materials.wall_finish(paint=p.paint))
    reuse = wall == base and roughness == .93
    return [M_WALL if t == 1.0 and reuse else b.named_mat(
        'tower_stone_'+str(i), tuple(min(1, v*t) for v in base[:3])+(1.,), .93)
        for i, t in enumerate((.78, .91, 1.0, 1.08, 1.16))]


def _tower_stone_shaft(b, p: FortStructureParams, cx, cy, radius, shaft):
    """Reconstructed masonry inside the EXISTING12 taper facets, not a texture.

    Courses, bond, depth and tone are bounded choices. A thin unchanged base
    band retains every old ground vertex; a top seat retains the gallery joint.
    All relief points lie on or behind the original planes, never outside them.
    """
    d = p.tower_masonry
    base = WALL_RGBA['stone']
    mats = _tower_stone_palette(b, p)
    mortar = b.named_mat('tower_stone_joint',tuple(v*.68 for v in base[:3])+(1.,),.95)
    openings_by_facet = {i:[] for i in range(12)}
    for o in tower_opening_layout(p) or []:
        openings_by_facet[o['facet']].append(o)
    half = lambda z: radius*(1-(1-p.taper)*z/shaft)*math.sin(math.pi/12)
    face_radius = lambda z: radius*(1-(1-p.taper)*z/shaft)*math.cos(math.pi/12)
    for facet in range(12):
        angle = math.radians(15+30*facet)
        nx,ny = math.cos(angle),math.sin(angle)
        tx,ty = -ny,nx
        def point(u,z,depth=0):
            r=face_radius(z)+depth
            return (cx+r*nx+u*tx,cy+r*ny+u*ty,z)
        def emit(poly,depth,mat):
            # Tangent crossed with vertical points outward on this facet.
            b.add_poly([point(u,z,depth) for u,z in poly],1.0,mat)
        foot, head = .06, shaft-.035
        # Use original angular vertices explicitly, so ground-contact bytes agree.
        a=2*math.pi*facet/12;c=2*math.pi*((facet+1)%12)/12
        def old_ring(z):
            r=radius*(1-(1-p.taper)*z/shaft)
            return [(cx+r*math.cos(t),cy+r*math.sin(t),z) for t in (a,c)]
        for z0,z1 in [(0.,foot),(head,shaft)]:
            lo,up=old_ring(z0),old_ring(z1)
            b.add_poly([lo[0],lo[1],up[1],up[0]],1.,M_WALL)
        field=[(-half(foot),foot),(half(foot),foot),(half(head),head),(-half(head),head)]
        holes=openings_by_facet[facet]
        for poly in _stone_without_apertures(field,holes):
            emit(poly,-d['relief_m'],mortar)
        z0=foot;row=0
        while z0<head-1e-9:
            height=d['course_m']*(.8+.4*_unit('lighthouse-stone',d['seed'],row))
            z1=min(head,z0+height)
            if z1-z0<=d['joint_m']*2:
                for poly in _stone_without_apertures([(-half(z0),z0),(half(z0),z0),(half(z1),z1),(-half(z1),z1)],holes):emit(poly,0.,mats[2])
                break
            zlo,zhi=z0+d['joint_m']/2,z1-d['joint_m']/2
            hw=half(zhi);width=d['bond_m']*(.8+.4*_unit('lighthouse-stone-bond',d['seed'],row,facet))
            start=-hw-width*(.3+.4*_unit('lighthouse-stone-stagger',d['seed'],row,facet));col=0
            while start<hw-1e-10:
                end=start+width
                u0=max(-hw,start+d['joint_m']/2);u1=min(hw,end-d['joint_m']/2)
                if u1-u0>.025:
                    poly=[(u0,zlo),(u1,zlo),(u1,zhi),(u0,zhi)]
                    # One facet crown per physical unit; clipped pieces retain tone.
                    tone=min(4,int(_unit('lighthouse-stone-tone',d['seed'],row,facet,col)*5))
                    for piece in _stone_without_apertures(poly,holes):
                        center=(sum(q[0] for q in piece)/len(piece),sum(q[1] for q in piece)/len(piece))
                        distances=[]
                        for i,q in enumerate(piece):
                            nxt=piece[(i+1)%len(piece)];du,dz=nxt[0]-q[0],nxt[1]-q[1]
                            distances.append(abs(du*(center[1]-q[1])-dz*(center[0]-q[0]))/math.hypot(du,dz))
                        # Tiny pieces at an aperture must not turn into needles.
                        crown=min(d['relief_m']*(.5+.2*_unit('lighthouse-stone-face',d['seed'],row,facet,col)),min(distances)*.2)
                        depth=-d['relief_m']*.75+crown
                        for i,q in enumerate(piece):
                            nxt=piece[(i+1)%len(piece)]
                            b.add_poly([point(*center,depth),point(*q,-d['relief_m']*.75),point(*nxt,-d['relief_m']*.75)],1.,mats[tone])
                start=end;col+=1
            z0=z1;row+=1
    _tower_stone_apertures(b,p,cx,cy,radius,shaft)

def _tower_stone_apertures(b,p: FortStructureParams,cx,cy,radius,shaft):
    """Plain dark recesses, not source claims for white sash/casing or a door."""
    glass=b.named_mat('lantern_glass',*openings.glass_material_spec())
    for o in tower_opening_layout(p) or []:
        mapped=_TowerFacetBuilder(b,cx,cy,radius,p.taper,shaft,o['azimuth_deg'])
        u0,u1,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];depth=p.tower_masonry['reveal_m']
        # This adapter expects the kit's opposite local winding; compensate
        # for these manually authored outward (tangent,height) polygons.
        def face(points,mat):
            mapped.add_poly(list(reversed(points)),1.,mat)
        face([(u0,-depth,z0),(u1,-depth,z0),(u1,-depth,z1),(u0,-depth,z1)],glass)
        face([(u0,0,z0),(u1,0,z0),(u1,-depth,z0),(u0,-depth,z0)],M_WALL)
        face([(u1,0,z1),(u0,0,z1),(u0,-depth,z1),(u1,-depth,z1)],M_WALL)
        face([(u0,0,z1),(u0,0,z0),(u0,-depth,z0),(u0,-depth,z1)],M_WALL)
        face([(u1,0,z0),(u1,0,z1),(u1,-depth,z1),(u1,-depth,z0)],M_WALL)

def _tower_irregular_stone_shaft(b, p: FortStructureParams, cx, cy, radius, shaft):
    """Irregular rubble character inside the same old12 planes; no source pixels.

    Courses, bond, depth and tone are bounded choices. A thin unchanged base
    band retains every old ground vertex; a top seat retains the gallery joint.
    All relief points lie on or behind the original planes, never outside them.
    """
    d = p.tower_masonry
    base = WALL_RGBA['stone']
    mats = _tower_stone_palette(b, p)
    mortar = b.named_mat('tower_stone_joint',tuple(v*.68 for v in base[:3])+(1.,),.95)
    openings_by_facet = {i:[] for i in range(12)}
    for o in tower_opening_layout(p) or []:
        openings_by_facet[o['facet']].append(o)
    half = lambda z: radius*(1-(1-p.taper)*z/shaft)*math.sin(math.pi/12)
    face_radius = lambda z: radius*(1-(1-p.taper)*z/shaft)*math.cos(math.pi/12)
    for facet in range(12):
        angle = math.radians(15+30*facet)
        nx,ny = math.cos(angle),math.sin(angle)
        tx,ty = -ny,nx
        def point(u,z,depth=0):
            r=face_radius(z)+depth
            return (cx+r*nx+u*tx,cy+r*ny+u*ty,z)
        def emit(poly,depth,mat):
            # Tangent crossed with vertical points outward on this facet.
            b.add_poly([point(u,z,depth) for u,z in poly],1.0,mat)
        foot, head = .06, shaft-.035
        # Use original angular vertices explicitly, so ground-contact bytes agree.
        a=2*math.pi*facet/12;c=2*math.pi*((facet+1)%12)/12
        def old_ring(z):
            r=radius*(1-(1-p.taper)*z/shaft)
            return [(cx+r*math.cos(t),cy+r*math.sin(t),z) for t in (a,c)]
        for z0,z1 in [(0.,foot),(head,shaft)]:
            lo,up=old_ring(z0),old_ring(z1)
            b.add_poly([lo[0],lo[1],up[1],up[0]],1.,M_WALL)
        field=[(-half(foot),foot),(half(foot),foot),(half(head),head),(-half(head),head)]
        holes=openings_by_facet[facet]
        for poly in _stone_without_apertures(field,holes):
            emit(poly,-d['relief_m'],mortar)
        z0=foot;row=0
        while z0<head-1e-9:
            height=d['course_m']*(.8+.4*_unit('lighthouse-irregular-bed',d['seed'],row,facet))
            z1=min(head,z0+height)
            if z1-z0<=d['joint_m']*2:
                for poly in _stone_without_apertures([(-half(z0),z0),(half(z0),z0),(half(z1),z1),(-half(z1),z1)],holes):emit(poly,0.,mats[2])
                break
            zlo,zhi=z0+d['joint_m']/2,z1-d['joint_m']/2
            hw=half(zhi);width=d['bond_m']*(.8+.4*_unit('lighthouse-stone-bond',d['seed'],row,facet))
            start=-hw-width*(.3+.4*_unit('lighthouse-stone-stagger',d['seed'],row,facet));col=0
            while start<hw-1e-10:
                end=start+width*(.65+.7*_unit('lighthouse-irregular-width',d['seed'],row,facet,col))
                u0=max(-hw,start+d['joint_m']/2);u1=min(hw,end-d['joint_m']/2)
                if u1-u0>.025:
                    # Inset each irregular unit inside its old cell. Bed slopes and
                    # chipped corners are reconstructed, not engraved hatch copies.
                    short=min(u1-u0,zhi-zlo)
                    bevel=min(.06,short*.14)
                    bed=min(.045,short*.08)
                    a,b0,c0,d0=[bevel*(.35+.65*_unit('lighthouse-irregular-corner',d['seed'],row,facet,col,k)) for k in range(4)]
                    bl,br,tr,tl=[bed*_unit('lighthouse-irregular-bededge',d['seed'],row,facet,col,k) for k in range(4)]
                    poly=[(u0+a,zlo+bl),(u1-b0,zlo+br),(u1,zlo+br+b0),
                          (u1,zhi-tr-c0),(u1-c0,zhi-tr),(u0+d0,zhi-tl),
                          (u0,zhi-tl-d0),(u0,zlo+bl+a)]
                    # One facet crown per physical unit; clipped pieces retain tone.
                    tone=min(4,int(_unit('lighthouse-stone-tone',d['seed'],row,facet,col)*5))
                    for piece in _stone_without_apertures(poly,holes):
                        center=(sum(q[0] for q in piece)/len(piece),sum(q[1] for q in piece)/len(piece))
                        distances=[]
                        for i,q in enumerate(piece):
                            nxt=piece[(i+1)%len(piece)];du,dz=nxt[0]-q[0],nxt[1]-q[1]
                            distances.append(abs(du*(center[1]-q[1])-dz*(center[0]-q[0]))/math.hypot(du,dz))
                        # Tiny pieces at an aperture must not turn into needles.
                        crown=min(d['relief_m']*(.5+.2*_unit('lighthouse-stone-face',d['seed'],row,facet,col)),min(distances)*.2)
                        depth=-d['relief_m']*.75+crown
                        for i,q in enumerate(piece):
                            nxt=piece[(i+1)%len(piece)]
                            b.add_poly([point(*center,depth),point(*q,-d['relief_m']*.75),point(*nxt,-d['relief_m']*.75)],1.,mats[tone])
                start=end;col+=1
            z0=z1;row+=1
    _tower_stone_apertures(b,p,cx,cy,radius,shaft)
