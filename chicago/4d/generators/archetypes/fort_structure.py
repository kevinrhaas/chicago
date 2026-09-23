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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.logwork import (  # noqa: E402
    CHINK_RGBA, HEWN_RGBA, RELIEF_M, hewn_log_wall,
)
from common import materials  # noqa: E402
from common.mesh import MeshBuilder, ROOF_RGBA, simple_material  # noqa: E402
from archetypes.fort_structure_params import FortStructureParams  # noqa: E402

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


def build(params: FortStructureParams, name: str):
    """Build one fort structure. Returns a Blender object at the local origin."""
    params.validate()
    b = MeshBuilder(name)

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
        # The roof takes the town's default tone: no fort record deals a weathering
        # condition, and none states a covering either (materials.md finding 2).
        simple_material("roof", ROOF_RGBA, roughness=0.9),
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
    return b.to_object(mats)


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
    if p.construction in ("log", "hewn_log"):
        hewn_log_wall(b, 0.0, 0.0, w, d, 0.0, lower_z, c_mass, M_WALL, M_TRIM,
                      skip=("bottom", "top"))
    else:
        b.add_box(0.0, 0.0, 0.0, w, d, lower_z, c_mass, M_WALL,
                  skip=("bottom", "top"))
        if p.construction == "brick":
            _string_course(b, 0.0, 0.0, w, d, lower_z, c_mass)

    if over > 0.0:
        # the jetty: a floor plate on the overhang, then the upper storey
        b.add_box(-over, -over, lower_z, w + over, d + over, lower_z + 0.18,
                  c_mass, M_TRIM, skip=("top",))
        if p.construction in ("log", "hewn_log"):
            hewn_log_wall(b, -over, -over, w + over, d + over, lower_z + 0.18, wz + 0.18,
                          c_mass, M_WALL, M_TRIM, skip=("bottom", "top"))
        else:
            b.add_box(-over, -over, lower_z + 0.18, w + over, d + over, wz + 0.18,
                      c_mass, M_WALL, skip=("bottom", "top"))

    ex = over
    eave = wz + (0.18 if over > 0.0 else 0.0)
    ridge = _roof(b, p, -ex, -ex, w + ex, d + ex, eave, c_roof)

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


def _roof(b: MeshBuilder, p: FortStructureParams, x0, y0, x1, y1,
          eave_z: float, conf: float) -> float:
    if p.roof_type in ("flat", "none"):
        b.add_poly([(x0, y0, eave_z), (x0, y1, eave_z), (x1, y1, eave_z),
                    (x1, y0, eave_z)], conf, M_ROOF)
        return eave_z
    if p.roof_type == "gable":
        return b.add_gable_roof(x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf, M_ROOF,
                                ridge_along_x=(x1 - x0) >= (y1 - y0))
    if p.roof_type == "shed":
        rise = (y1 - y0) * math.tan(math.radians(p.roof_pitch_deg))
        hi = eave_z + rise
        b.add_poly([(x0, y0, hi), (x1, y0, hi), (x1, y1, eave_z), (x0, y1, eave_z)],
                   conf, M_ROOF)
        b.add_poly([(x0, y1, eave_z), (x0, y0, hi), (x1, y0, hi), (x1, y1, eave_z)][::-1],
                   conf, M_ROOF)
        return hi
    return _hip_roof(b, x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf,
                     pyramid=(p.roof_type == "pyramid"))


def _hip_roof(b: MeshBuilder, x0, y0, x1, y1, eave_z, pitch_deg, conf,
              pyramid: bool, overhang: float = 0.28) -> float:
    """A hip or a pyramid. A pyramid is the degenerate hip whose ridge is a point,
    and a blockhouse gets one because a four-sided pitched cap over a square plan
    is what every surviving blockhouse of the period carries."""
    x0, y0, x1, y1 = x0 - overhang, y0 - overhang, x1 + overhang, y1 + overhang
    w, d = x1 - x0, y1 - y0
    short = min(w, d)
    rise = (short / 2.0) * math.tan(math.radians(pitch_deg))
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


def _opening(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
             z0: float, z1: float, outward: int, conf: float,
             relief: float = RELIEF_M) -> None:
    """A door or window: a dark panel inside a sawn surround. Same treatment, and
    the same reasoning, as log_dwelling._opening."""
    off = relief + 0.010
    m = 0.085
    _panel(b, axis, plane + outward * off, u0 - m, u1 + m, z0 - m, z1 + m,
           outward, conf, M_TRIM)
    _panel(b, axis, plane + outward * (off + 0.006), u0, u1, z0, z1,
           outward, conf, M_DARK)


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
    """Door and windows on the facade and the back.

    Bay counts come from the building's own length rather than from a record —
    nothing describes the fenestration of any building in this fort — so the
    confidence is the record's `fenestration` value when it has one, and
    `inferred` otherwise. A range gets a door at its centre and windows spaced
    along the front; the back gets windows only.
    """
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
        _opening(b, "y", d, xm - 0.55, xm + 0.55, 0.02, 2.05, 1, conf)


def _magazine_door(b: MeshBuilder, p: FortStructureParams, conf: float) -> None:
    """A powder magazine has one door and no windows. That is not a simplification;
    it is the defining fact about the building type."""
    xm = p.width_m / 2.0
    _opening(b, "y", p.depth_m, xm - 0.45, xm + 0.45, 0.02, 1.85, 1, conf)


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
    """A covered gallery along the facade: posts, a plate and a lean-to roof."""
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

    **Why it is bare.** Andreas is the source and Andreas is precise about when the
    flag was up — it "flaunted, IN PLEASANT WEATHER AND ON HOLIDAYS", and from the
    southern approach a traveller saw "the flag over the fort, IF PERCHANCE IT WAS
    FLYING". 1835-07-01 is a Wednesday, it is not a holiday, and this project does
    not model weather. A flag drawn on this spar would therefore be a claim about
    one particular forenoon that the source explicitly declines to make, in the same
    way a shut gate is a claim about a garrison being present. The staff is what is
    attested; the bunting is not, so the halyard truck is where this mesh stops.

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

    Everything about the PROFILE is the archetype's. The record carries the one
    documented number — forty feet — and the lantern; no source reached says what
    shape the 1832 tower was or what it was built of. See
    docs/RESEARCH/chicago_lighthouse_1832.md and the liberty that owns it.
    """
    c = p.worst_conf("kind", "wall_height_m", "construction")
    n = 12
    r0 = p.width_m / 2.0
    r1 = r0 * p.taper
    cx, cy = r0, r0
    h = p.wall_height_m
    shaft = h * 0.86

    def ring(r, z):
        return [(cx + r * math.cos(2 * math.pi * i / n),
                 cy + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]

    lo, up = ring(r0, 0.0), ring(r1, shaft)
    for i in range(n):
        j = (i + 1) % n
        b.add_poly([lo[i], lo[j], up[j], up[i]], c, M_WALL)

    if not p.lantern:
        b.add_poly(list(reversed(up)), c, M_ROOF)
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
