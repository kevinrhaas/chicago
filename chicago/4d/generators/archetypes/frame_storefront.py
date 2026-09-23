"""frame_storefront — a frame store: a shopfront on the street, a loading side, an ell.

The building type 1835 Chicago was mostly made of and the one this project could not
model until now: every mercantile record had to be a log cabin, a frame tavern or a
bridge. The cases it was written for are P. F. W. Peck's two-storey frame store at
South Water & LaSalle with its unfinished loft, Philo Carpenter's "small store" a
block west, and Thomas Church's two-storey frame store on Lake Street. Evidence and
its gaps: docs/research/04-structures-south.md §5, §6, §12, and the parameter
module's docstring, which is where the reasoning for each parameter lives.

**Orientation.** The facade faces NORTH at rotation_deg 0, per the pinned convention
in docs/GLB-CONTRACT.md. In Blender that is the +y face, because the exporter's
`export_yup=True` maps Blender +Y to glTF -Z, which the contract defines as north.
The shopfront, its fascia and its sign are all on +y; the loading end is a gable, +x
unless an end ell has taken that end. Getting this wrong is a silent error — the
building looks right and faces the wrong way.

**The shopfront is a hole, not a decal.** Every other opening in this project's
archetypes is a surface sitting a centimetre proud of the wall, because at this LOD a
real opening would show the inside of the far wall and interiors are out of scope.
The shopfront is the exception and it is worth the geometry: the front elevation is
built AROUND it, the glazing and the door sit back by the thickness of the wall, and
the jambs are modelled. That reveal is the balloon frame made visible — a 4 in stud,
a 1 in board of sheathing and a clapboard come to about five and a half inches, so a
balloon-framed shopfront reads as an opening cut in a thin light wall, which is what
it was. A shopfront drawn flat on the wall reads as a painted sign of a shop.

**The sign board carries nothing.** `sign` names what the board carried so the
sidecar can report it; no lettering, device or image is drawn. Same call, same
reason, as docs/LIBERTIES.md L25 makes for the painted wolf at Wolf Point: firm names
survive from newspaper advertisements, which are not sign boards, and a shop sign
lettered from imagination would be the most conspicuous invention on the street.

**Winding.** Every face here is wound so its normal points out of the building or
away from the wall it sits on, including the cladding lips — the contract says
counter-clockwise and outward, and the exporter's default `doubleSided: true` is not
a guarantee to build on. `_panel` and `_flat` exist so no surface can get it wrong by
hand.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.frame_storefront_params import (  # noqa: E402
    CORNER_BOARD_M, POST_FACE_M, POST_SPACING_M, SHEATHING_M, SHOP_FASCIA_M,
    SHOP_PILASTER_M, SHOP_SILL_Z_M, SIDING_M, STOREY_WIN_H_M, STOREY_WIN_W_M,
    STUD_DEPTH_M, STUD_FACE_M, STUD_SPACING_M, FrameStorefrontParams, ell_extent,
    front_window_rects, main_extent, plain_door_rect, shopfront_extent,
    shopfront_panels, snap, storey_sill_z,
)

#: This archetype's roof COVERING, off the sheet's dealing rule (T-1487).
#: `materials.roof_substrate` holds the argument for why it is this one and
#: which half of it is graded by materials.md §2.2 and which half is L266.
_ROOF = materials.roof_substrate("frame_storefront")


# Materials are indices into the list passed to to_object(), in this order.
M_WALL, M_ROOF, M_TRIM, M_GLASS, M_SIGN, M_TIMBER = 0, 1, 2, 3, 4, 5
# Appended only where the record counts a stack (T-0008) — appended rather than
# inserted, and conditionally, for the reason `log_dwelling` gives at its own mats
# list: a material slot nothing references still reaches the glTF, so adding one
# unconditionally would rewrite every chimneyless master in the archetype.
M_CHIMNEY = 6

# The exposed face per course is `params.siding_exposure_m` — a record's own mill
# stock since T-0049, defaulting to 0.14 m (~5.5 in), which was a constant here.
# MeshBuilder.add_gable_roof's default overhang, and the reason it is named here:
# that helper fills each gable end with a solid triangle standing this far outboard
# of the wall, so anything drawn ON a gable — a loft opening, an open frame — has to
# be drawn against THAT plane or it is built inside the roof and never seen. This is
# not a hypothetical: it is why log_dwelling's loft openings do not appear in
# docs/RESEARCH/archetype-log_dwelling.png.
ROOF_OVERHANG_M = 0.25
BATTEN_SPACING_M = 0.356       # 14 in, the usual set-out for board and batten
CLAD_RELIEF_M = 0.020          # how far the skin stands off the wall plane
SHEATHING_BOARD_M = 0.229      # a 9 in sheathing board, laid horizontally

# The wall's build-up, and therefore the depth of every reveal in the shopfront.
# This is the number a knowledgeable viewer reads without knowing they are reading
# it: a braced frame is a heavier wall than a balloon frame, and the shadow in the
# shop window says which one they are looking at.
BALLOON_WALL_M = STUD_DEPTH_M + SHEATHING_M + SIDING_M
BRACED_WALL_M = 0.165

SIGN_RGBA = (0.60, 0.54, 0.44, 1.0)          # a weathered board; see L25
# Fresh sawn lumber, paler than a wall. On the sheet since T-0126 as `SAWN_FRAMING`,
# the SECOND of the two materials materials.md finding 3 found sharing the name
# `timber` — the other being the outbuilding's weathered heavy stock, 3.2x darker in
# linear red. The value is unchanged and still reaches no GLB (no record in this
# dataset turns `framing_exposed` on); what changes is that it now has a name of its
# own, so the day a storefront does expose its frame beside a shed the two will not
# read as one material.
TIMBER_RGBA = materials.SAWN_FRAMING.rgba
# The town's glazing, on the sheet since T-0126 at exactly this value — the row is a
# record of what already shipped on all 48 slots, not a re-argument of it.
GLASS_RGBA = materials.GLASS.rgba


def build(params: FrameStorefrontParams, name: str):
    """Build the store. Returns a Blender object at the local origin, y-up handled
    by the exporter (Blender is z-up internally)."""
    params.validate()
    p = params
    b = MeshBuilder(name)

    # Massing confidence describes the building's CHARACTER, not the precision of
    # its dimensions — the argument is set out at length in frame_tavern.build and
    # is not repeated here. The short form: an unknown size and an unknown form are
    # different kinds of not-knowing, and dithering a well-attested building into
    # ghost massing because nobody wrote down its frontage misrepresents the
    # evidence in the direction of false modesty. Dimensional uncertainty is
    # carried honestly in the sidecar, where the footprint keeps its own confidence
    # and the placement its uncertainty_m.
    #
    # TWO ATTRIBUTES, NOT frame_tavern's THREE, and the difference is deliberate.
    # That archetype folds `cladding` into the massing because it does not read the
    # value — the wall gets clapboard whatever the record says, so the record's
    # reading of the surface is part of what "we know what this building was" means
    # there. Here `cladding` DRIVES its own geometry and carries its own confidence
    # below, so grading the massing by it would dither the box for a fact about the
    # skin and count the same uncertainty twice. log_dwelling made the same
    # adjustment in the other direction, for the same reason.
    c_mass = p.worst_conf("stories", "construction")
    c_roof = p.worst_conf("roof_type", "roof_pitch_deg")
    c_clad = p.worst_conf("cladding", "paint")
    # The trim and the corner boards are the framing system made visible, so they
    # take the confidence of `construction` and nothing else.
    c_frame = p.conf("construction", "reconstructed")
    c_fen = p.conf("fenestration", "reconstructed")

    mx0, my0, mx1, my1 = main_extent(p)
    wall_z = p.wall_height_m

    # The main block, minus the bottom (never seen) and minus the facade, which is
    # built plane by plane around the shopfront below.
    b.add_box(mx0, my0, 0.0, mx1, my1, wall_z, c_mass, M_WALL, skip=("bottom", "back"))

    shop = shopfront_extent(p, mx0, mx1) if p.shopfront else None
    _front_wall(b, p, mx0, mx1, my1, wall_z, shop, c_mass)
    _skin(b, p, mx0, my0, mx1, my1, wall_z, c_clad, front_gap=shop)

    ridge_z = _roof(b, p, mx0, my0, mx1, my1, wall_z, c_roof)

    # trim: the water table, the frieze, the corner boards, and — on a braced frame
    # only — the girt line at the second floor. See _trim for why the ABSENCE of
    # that line is the balloon frame's signature.
    _trim(b, p, mx0, my0, mx1, my1, wall_z, c_frame, shop)

    if shop is not None:
        _shopfront(b, p, shop, my1, c_fen)
        if p.sign:
            # The BOARD's confidence is the confidence that a sign hung there. Its
            # size and its mounting are the archetype's, but those are dimensional
            # and by the convention above dimensions do not drag an object's
            # character down.
            _sign(b, p, shop, my1, p.conf("sign", "reconstructed"))
    else:
        _plain_door(b, p, mx0, mx1, my1, c_fen)

    _fenestration(b, p, mx0, my0, mx1, my1, wall_z, shop, c_fen)

    if p.goods_door:
        _goods_door(b, p, mx0, my0, mx1, my1, p.conf("goods_door"))

    if p.loft:
        _loft_opening(b, p, mx0, my0, mx1, my1, wall_z, ridge_z, p.conf("loft"))

    if p.ell:
        _ell(b, p, p.worst_conf("ell", "ell_stories"), c_clad)

    if p.framing_exposed:
        _exposed_framing(b, p, mx0, my0, mx1, my1, wall_z, ridge_z, c_frame)

    _chimneys(b, p, mx0, my0, mx1, my1, ridge_z, wall_z, p.conf("chimneys"),
              M_CHIMNEY if p.chimneys > 0 else M_ROOF)

    # ---- the surfaces, off the sheet (T-0007) --------------------------------
    # This is the ONE archetype in the project that already read `cladding`, and it
    # is the one whose walls therefore have three different substrates: clapboard at
    # 0.86, board-and-batten at 0.88, plain vertical board at 0.90. Those are the
    # sheet's roughnesses, each argued from the surface's own rhythm; the store's
    # single 0.85 for all three is what they replace. The colour is the finish — a
    # stated coating first, then the finish the programme dealt, then the committed
    # unpainted tone. See `common/materials.py`.
    finish = materials.wall_finish(p.paint, p.finish_key)
    wall_rgba, wall_rough = materials.resolve(
        materials.wall_substrate(construction=p.construction, cladding=p.cladding),
        finish)
    roof_rgba = materials.roof_finish(p.roof_condition).rgba
    mats = [
        simple_material("wall", wall_rgba, roughness=wall_rough),
        # The COLOUR is a weathering condition and never a covering; the COVERING is
        # now the sheet's, and it is a shingle field (T-1487: §2.2 grades it inferred
        # for a framed building). The roughness is unchanged — `shingle` carries the
        # 0.9 this archetype always shipped.
        simple_material(materials.roof_material_name(_ROOF), roof_rgba,
                        roughness=_ROOF.roughness),
        simple_material("trim", _trim_rgba(wall_rgba), roughness=0.8),
        simple_material("glass", GLASS_RGBA, roughness=materials.GLASS.roughness),
        simple_material("sign", SIGN_RGBA, roughness=0.85),
        simple_material("sawn_framing", TIMBER_RGBA,
                        roughness=materials.SAWN_FRAMING.roughness),
    ]
    # THE STACK IS NOT THE ROOF (T-0008). R-W2a finding 1: every stack this archetype
    # built took `M_ROOF` and came out painted its roof's weathering condition. A
    # store's stack rises on the ridge line through the roof, so it is masonry, and
    # the masonry this town had was brick — `common/materials.py` § the chimney stack,
    # and docs/RESEARCH/chimneys.md.
    if p.chimneys > 0:
        stack = materials.chimney_finish("interior")
        mats.append(simple_material("chimney", stack.rgba, roughness=stack.roughness))
    return b.to_object(mats)


def _trim_rgba(wall):
    """Trim boards, mixed off the wall colour rather than fixed.

    A painted store had lighter trim and an unpainted one had trim that weathered
    paler than the siding, so one rule covers both and neither is a second claim
    about colour on top of the record's `paint`."""
    return tuple(c + (1.0 - c) * 0.42 for c in wall[:3]) + (1.0,)


# ---------------------------------------------------------------- plan geometry

def _loading_sign(p: FrameStorefrontParams) -> float:
    """Which end of the block takes the goods door: +1 for the +x gable.

    The loading end is the one the ell is not on, so the two ends of the building
    do different work and neither elevation carries both. With an end ell at +x the
    free gable is -x; otherwise it is +x.
    """
    return -1.0 if (p.ell and p.ell_side == "end") else 1.0


def _ridge_along_x(p: FrameStorefrontParams) -> bool:
    """False turns the gable to the street. `gable_front` is the record's, and its
    default reproduces the phrase Andreas uses of a frame building on Lake Street —
    'a two-story building, with eaves to the street'."""
    return not p.gable_front


def _wall_thickness(p: FrameStorefrontParams) -> float:
    return BALLOON_WALL_M if p.construction == "balloon_frame" else BRACED_WALL_M


# ------------------------------------------------------------------ primitives

def _panel(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
           z0: float, z1: float, outward: int, conf: float, mat: int) -> None:
    """One flat rectangle on an axis-aligned vertical plane, wound to face
    `outward`. `axis` names the plane's normal axis ('x' or 'y'); `u0`/`u1` run
    along the other horizontal axis."""
    if axis == "y":
        pts = [(u0, plane, z0), (u1, plane, z0), (u1, plane, z1), (u0, plane, z1)]
        natural = -1                       # this order's normal points -y
    else:
        pts = [(plane, u0, z0), (plane, u1, z0), (plane, u1, z1), (plane, u0, z1)]
        natural = 1                        # this order's normal points +x
    if outward != natural:
        pts.reverse()
    b.add_poly(pts, conf, mat)


def _flat(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float, z: float,
          conf: float, mat: int, up: int = 1) -> None:
    """One horizontal rectangle, wound to face up (+1) or down (-1)."""
    pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    if up < 0:
        pts.reverse()
    b.add_poly(pts, conf, mat)


def _opening(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
             z0: float, z1: float, outward: int, conf: float,
             surround: int = M_TRIM, relief: float = CLAD_RELIEF_M) -> None:
    """A door or window on an elevation that is not the shopfront: a dark panel
    inside a sawn surround, both sitting proud of the cladding.

    Surfaces, not holes — at this LOD an opening would show the inside of the far
    wall. The surround is not decoration: an opening drawn as a bare dark rectangle
    has to sit proud of the cladding to be visible at all, which makes it read as a
    plaque glued to the wall.
    """
    off = relief + 0.010
    m = 0.075
    # The surround never dips below grade. GROUND_CONTACT says this archetype's
    # footprint outline meets the terrain at z = 0, and a sill board 55 mm into the
    # ground is a small lie told against exactly the declaration the gate reads.
    _panel(b, axis, plane + outward * off, u0 - m, u1 + m, max(z0 - m, 0.0), z1 + m,
           outward, conf, surround)
    _panel(b, axis, plane + outward * (off + 0.006), u0, u1, z0, z1,
           outward, conf, M_GLASS)


def _board(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
           z0: float, z1: float, conf: float, mat: int,
           skip: tuple[str, ...] = ("bottom",)) -> None:
    """A trim board or a framing member, as a box. Thin by definition, so the only
    face worth skipping is the one against whatever it is nailed to."""
    b.add_box(x0, y0, z0, x1, y1, z1, conf, mat, skip=skip)


# --------------------------------------------------------------------- the skin

def _skin(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
          x1: float, y1: float, wall_z: float, conf: float,
          front_gap: tuple[float, float, float] | None = None) -> None:
    """The exterior siding, on all four elevations of a block.

    Cheap geometry, and it is what makes a frame building read as frame rather than
    as a painted box at walking distance. `front_gap` is the shopfront's span,
    which the siding runs around rather than through.
    """
    gap = None
    if front_gap is not None:
        gx0, gx1, head = front_gap
        gap = (gx0, gx1, head + SHOP_FASCIA_M)
    if p.cladding == "clapboard":
        _clapboard(b, x0, y0, x1, y1, wall_z, conf, gap, p.siding_exposure_m)
    else:
        _vertical_boards(b, p, x0, y0, x1, y1, wall_z, conf, gap)


def _clapboard(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
               wall_z: float, conf: float,
               gap: tuple[float, float, float] | None, course: float) -> None:
    """Horizontal lap courses, modelled as one proud lip per course.

    The lip is wound so its normal points away from the wall and up, which is the
    face a person standing in the street actually sees. `course` is the record's
    own mill stock (params.siding_exposure_m) — the exposed face per course.
    """
    lip = CLAD_RELIEF_M
    drop = 0.022
    n = int(wall_z / course)
    for i in range(1, n):
        z = i * course
        for a, c in _front_spans(x0, x1, z, gap):
            b.add_poly([(a, y1 + lip, z - drop), (c, y1 + lip, z - drop),
                        (c, y1, z), (a, y1, z)], conf, M_WALL)
        b.add_poly([(x1, y0 - lip, z - drop), (x0, y0 - lip, z - drop),
                    (x0, y0, z), (x1, y0, z)], conf, M_WALL)
        b.add_poly([(x0 - lip, y0, z - drop), (x0 - lip, y1, z - drop),
                    (x0, y1, z), (x0, y0, z)], conf, M_WALL)
        b.add_poly([(x1 + lip, y1, z - drop), (x1 + lip, y0, z - drop),
                    (x1, y0, z), (x1, y1, z)], conf, M_WALL)


def _vertical_boards(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
                     x1: float, y1: float, wall_z: float, conf: float,
                     gap: tuple[float, float, float] | None) -> None:
    """Vertical boarding: a batten or a board joint every `BATTEN_SPACING_M`.

    Board and batten stands a full batten proud; plain vertical boarding shows only
    the joint, which is 20 mm of relief rather than 40. That difference is the whole
    of what separates the two claddings from the street, and saying so is more
    honest than giving one of them a texture the record cannot support.
    """
    w = 0.058 if p.cladding == "board_and_batten" else 0.030
    proud = CLAD_RELIEF_M * (2.0 if p.cladding == "board_and_batten" else 1.0)
    n = max(int((x1 - x0) / BATTEN_SPACING_M), 1)
    for i in range(1, n):
        x = x0 + i * (x1 - x0) / n
        top = wall_z
        if gap is not None and gap[0] - w < x < gap[1] + w:
            top = 0.0
        if top > 0.0:
            _board(b, x - w / 2, y1, x + w / 2, y1 + proud, 0.0, top, conf, M_WALL,
                   skip=("bottom", "front"))
        _board(b, x - w / 2, y0 - proud, x + w / 2, y0, 0.0, wall_z, conf, M_WALL,
               skip=("bottom", "back"))
    m = max(int((y1 - y0) / BATTEN_SPACING_M), 1)
    for i in range(1, m):
        y = y0 + i * (y1 - y0) / m
        _board(b, x0 - proud, y - w / 2, x0, y + w / 2, 0.0, wall_z, conf, M_WALL,
               skip=("bottom", "right"))
        _board(b, x1, y - w / 2, x1 + proud, y + w / 2, 0.0, wall_z, conf, M_WALL,
               skip=("bottom", "left"))


def _front_spans(x0: float, x1: float, z: float,
                 gap: tuple[float, float, float] | None) -> list[tuple[float, float]]:
    """The stretches of the facade that carry siding at height `z` — the whole
    frontage above the shopfront, and the piers either side of it below."""
    if gap is None or z > gap[2]:
        return [(x0, x1)]
    out = []
    if gap[0] - x0 > 0.05:
        out.append((x0, gap[0]))
    if x1 - gap[1] > 0.05:
        out.append((gap[1], x1))
    return out


# --------------------------------------------------------------------- the trim

def _trim(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
          x1: float, y1: float, wall_z: float, conf: float,
          shop: tuple[float, float, float] | None = None) -> None:
    """Water table, frieze, corner boards, and the girt line a braced frame has.

    THE ABSENCE OF THE GIRT IS THE POINT. A braced frame is built storey by storey,
    so the second floor lands on a girt that shows in the elevation; a balloon
    frame's studs run sill to plate in one length, so there is nothing there and the
    wall is one plane from water table to frieze. That, and the thin corner board
    standing where a braced frame shows a 6 in post, is what a knowledgeable viewer
    checks first — the studs themselves are behind the sheathing and cannot be seen
    on a finished building at all.
    """
    # The water table stops at the shop's pilasters. A weather board carried
    # straight across a shop door is a detail that looks right in a diagram and
    # wrong on a building.
    gap = (shop[0], shop[1]) if shop is not None else None
    _band(b, x0, y0, x1, y1, 0.24, 0.34, 0.030, conf, M_TRIM, front_gap=gap)
    _band(b, x0, y0, x1, y1, wall_z - 0.22, wall_z, 0.030, conf, M_TRIM)   # frieze

    balloon = p.construction == "balloon_frame"
    face = CORNER_BOARD_M if balloon else POST_FACE_M
    proud = 0.022 if balloon else 0.034
    for cx, sx in ((x0, -1.0), (x1, 1.0)):
        for cy, sy in ((y0, -1.0), (y1, 1.0)):
            _board(b, min(cx, cx + sx * proud), min(cy, cy - sy * face),
                   max(cx, cx + sx * proud), max(cy, cy - sy * face),
                   0.30, wall_z - 0.20, conf, M_TRIM, skip=("bottom", "top"))
            _board(b, min(cx, cx - sx * face), min(cy, cy + sy * proud),
                   max(cx, cx - sx * face), max(cy, cy + sy * proud),
                   0.30, wall_z - 0.20, conf, M_TRIM, skip=("bottom", "top"))

    if not balloon and p.stories > 1:
        gz = p.story_height_m
        _band(b, x0, y0, x1, y1, gz - 0.09, gz + 0.09, 0.026, conf, M_TRIM)


def _band(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
          z0: float, z1: float, proud: float, conf: float, mat: int,
          front_gap: tuple[float, float] | None = None) -> None:
    """A horizontal trim band around all four elevations, with a weathered top.
    `front_gap` interrupts it on the facade, where the shopfront is."""
    _panel(b, "y", y0 - proud, x0 - proud, x1 + proud, z0, z1, -1, conf, mat)
    _panel(b, "x", x0 - proud, y0 - proud, y1 + proud, z0, z1, -1, conf, mat)
    _panel(b, "x", x1 + proud, y0 - proud, y1 + proud, z0, z1, 1, conf, mat)
    _flat(b, x0 - proud, y0 - proud, x1 + proud, y0, z1, conf, mat)
    _flat(b, x0 - proud, y0, x0, y1, z1, conf, mat)
    _flat(b, x1, y0, x1 + proud, y1, z1, conf, mat)
    for a, c in _front_spans(x0 - proud, x1 + proud, z0,
                             None if front_gap is None
                             else (front_gap[0], front_gap[1], z1)):
        _panel(b, "y", y1 + proud, a, c, z0, z1, 1, conf, mat)
        _flat(b, a, y1, c, y1 + proud, z1, conf, mat)


# ---------------------------------------------------------------- the shopfront

def _front_wall(b: MeshBuilder, p: FrameStorefrontParams, x0: float, x1: float,
                y: float, wall_z: float, shop: tuple[float, float, float] | None,
                conf: float) -> None:
    """The facade, built as the wall AROUND the shopfront rather than as one face
    with a picture of a shop on it. With no shopfront it is a single plane."""
    if shop is None:
        _panel(b, "y", y, x0, x1, 0.0, wall_z, 1, conf, M_WALL)
        return
    sx0, sx1, head = shop
    if sx0 - x0 > 1e-6:
        _panel(b, "y", y, x0, sx0, 0.0, wall_z, 1, conf, M_WALL)
    if x1 - sx1 > 1e-6:
        _panel(b, "y", y, sx1, x1, 0.0, wall_z, 1, conf, M_WALL)
    # up from the head, not from the top of the fascia: the fascia is a board
    # nailed ON the wall, and leaving the strip behind it unbuilt is a hole a
    # visitor sees through from an angle.
    _panel(b, "y", y, sx0, sx1, head, wall_z, 1, conf, M_WALL)


def _shopfront(b: MeshBuilder, p: FrameStorefrontParams,
               shop: tuple[float, float, float], y: float, conf: float) -> None:
    """The composed street opening: pilasters, a counter sill, a door and its show
    windows, a fascia over the whole.

    THE COMPOSITION IS THE ARCHETYPE'S, NOT ANY RECORD'S. No source reached
    describes a Chicago shop window in 1835 — what is attested is the trade, the
    counter, the street frontage and, for the Green Tree's rooms, 'small-paned
    windows'. So this is type, argued rather than preferred: a country store front
    is a run of panels between two pilaster boards under one fascia, the glass sits
    above a solid stall riser at counter height because that is where the goods
    stood, and the panes are small because glass came by scow and was sold by the
    light. It is the largest single liberty this archetype takes.
    """
    sx0, sx1, head = shop
    reveal = _wall_thickness(p)

    # pilaster boards at each end, standing proud of the siding
    for a, c in ((sx0, sx0 + SHOP_PILASTER_M), (sx1 - SHOP_PILASTER_M, sx1)):
        _board(b, a, y, c, y + 0.034, 0.0, head, conf, M_TRIM,
               skip=("bottom", "back"))

    # THE RUN OF PANELS IS THE PARAMS MODULE'S SET-OUT (T-0520): `shopfront_panels`
    # states the door and the show windows left to right, and the signage layer reads
    # the same list, so a board can no longer be hung over a bay this builder put
    # somewhere else. Which panel is the door is settled there too — 'centre' cannot
    # be centred against an even number of panels, so it takes the middle-most one
    # and the record can say left or right when a source is more specific than that.
    # The mullions are what is BETWEEN two panels and so are stated by neither: they
    # are the gap from one panel's end to the next one's start.
    panels = shopfront_panels(p, shop)

    # everything left of the first panel and right of the last is pilaster, and the
    # strip under the pilasters is the same board carried to the ground
    _panel(b, "y", y, sx0, panels[0][1], 0.0, head, 1, conf, M_TRIM)
    for i, (kind, u0, u1, _z0, _z1) in enumerate(panels):
        if kind == "shop_door":
            _shop_door(b, y, u0, u1, head, reveal, conf)
        else:
            _show_window(b, y, u0, u1, head, reveal, conf)
        if i + 1 < len(panels):
            m0, m1 = u1, panels[i + 1][1]
            _panel(b, "y", y, m0, m1, 0.0, head, 1, conf, M_TRIM)
            _board(b, m0, y, m1, y + 0.022, SHOP_SILL_Z_M - 0.05,
                   head, conf, M_TRIM, skip=("bottom", "back"))
    _panel(b, "y", y, panels[-1][2], sx1, 0.0, head, 1, conf, M_TRIM)

    # the fascia over the whole opening — the board a sign goes on, and the thing
    # that ties the run of panels into one shopfront
    _board(b, sx0 - 0.04, y, sx1 + 0.04, y + 0.048, head, head + SHOP_FASCIA_M,
           conf, M_TRIM, skip=("bottom", "back"))


def _reveal(b: MeshBuilder, y: float, u0: float, u1: float, z0: float, z1: float,
            depth: float, conf: float) -> None:
    """The four jamb faces of a real opening: head, sill and two sides, running
    back from the wall plane to the glazing. This is where the wall's thickness
    becomes visible, and it is the whole reason the shopfront is built as a hole."""
    yb = y - depth
    _panel(b, "x", u0, yb, y, z0, z1, 1, conf, M_TRIM)      # left jamb, facing in
    _panel(b, "x", u1, yb, y, z0, z1, -1, conf, M_TRIM)     # right jamb
    _flat(b, u0, yb, u1, y, z1, conf, M_TRIM, up=-1)        # head, facing down
    _flat(b, u0, yb, u1, y, z0, conf, M_TRIM, up=1)         # sill, facing up


def _show_window(b: MeshBuilder, y: float, u0: float, u1: float, head: float,
                 reveal: float, conf: float) -> None:
    """One display bay: a solid stall riser to counter height, then glass."""
    sill = SHOP_SILL_Z_M
    top = head - 0.13
    _panel(b, "y", y, u0, u1, 0.0, sill, 1, conf, M_TRIM)          # stall riser
    _panel(b, "y", y, u0, u1, top, head, 1, conf, M_TRIM)          # head board
    _board(b, u0, y, u1, y + 0.040, sill - 0.05, sill + 0.02, conf, M_TRIM,
           skip=("bottom", "back"))                                # counter sill
    _panel(b, "y", y - reveal, u0, u1, sill, top, 1, conf, M_GLASS)
    _reveal(b, y, u0, u1, sill, top, reveal, conf)
    # muntins: small panes, because glass came by scow and was sold by the light
    for f in (0.333, 0.667):
        x = u0 + (u1 - u0) * f
        _board(b, x - 0.014, y - reveal, x + 0.014, y - reveal + 0.020, sill, top,
               conf, M_TRIM, skip=("bottom", "front"))
    zm = sill + (top - sill) * 0.5
    _board(b, u0, y - reveal, u1, y - reveal + 0.018, zm - 0.014, zm + 0.014,
           conf, M_TRIM, skip=("front",))


def _shop_door(b: MeshBuilder, y: float, u0: float, u1: float, head: float,
               reveal: float, conf: float) -> None:
    """The shop door: a panelled leaf set back in the wall, with a light over it."""
    top = min(2.06, head - 0.22)
    _panel(b, "y", y, u0, u1, top, head, 1, conf, M_TRIM)          # head board
    _panel(b, "y", y - reveal, u0, u1, 0.0, top, 1, conf, M_GLASS)
    _reveal(b, y, u0, u1, 0.0, top, reveal, conf)
    # two sunk panels, suggested by the stiles standing proud of the leaf
    for z0, z1 in ((0.12, 0.92), (1.02, top - 0.10)):
        for x in (u0 + 0.10, u1 - 0.10):
            _board(b, x - 0.035, y - reveal, x + 0.035, y - reveal + 0.022, z0, z1,
                   conf, M_TRIM, skip=("bottom", "front"))


def _sign(b: MeshBuilder, p: FrameStorefrontParams,
          shop: tuple[float, float, float], y: float, conf: float) -> None:
    """A signboard on the fascia over the shopfront. IT CARRIES NOTHING.

    The board is the claim: a store put its name over its door. What that name
    looked like — the lettering, the device, the colour — is nowhere recorded for
    any Chicago store in 1835, and painting one would be inventing the piece of
    evidence a visitor walks straight up to. Same decision as docs/LIBERTIES.md L25
    makes for the wolf at Wolf Point, and the `sign` value carries the subject to
    the sidecar so the popup can say what the mesh will not.
    """
    sx0, sx1, head = shop
    w = min((sx1 - sx0) * 0.78, 3.2)
    cx = (sx0 + sx1) / 2.0
    # Standing a little taller than the fascia it is nailed to, and a little
    # further out, so it reads as a board hung on a building rather than as a
    # painted stripe. Those are the two things about a shop sign that are not in
    # dispute: it was a board, and you could see it from the street.
    z0 = head + SHOP_FASCIA_M * 0.06
    z1 = head + SHOP_FASCIA_M + 0.11
    _board(b, cx - w / 2, y + 0.048, cx + w / 2, y + 0.105, z0, z1, conf, M_SIGN,
           skip=("back",))


# -------------------------------------------------------------- the other walls

def _fenestration(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
                  x1: float, y1: float, wall_z: float,
                  shop: tuple[float, float, float] | None, conf: float) -> None:
    """Windows above the shop and on the flanks.

    THE BAY COUNT COMES FROM THE FRONTAGE, not from a constant. Fixing it is the
    defect docs/LIBERTIES.md L23 records against the three frame taverns — one
    five-bay rhythm spread across buildings of three different sizes, which reads
    as a finding about how the town was built and is an artefact of an archetype.
    The centres are then snapped to the framing module, because in a framed wall a
    window lands between studs or it does not land.
    """
    win_w, win_h = STOREY_WIN_W_M, STOREY_WIN_H_M

    # THE FACADE'S WINDOWS ARE THE PARAMS MODULE'S SET-OUT (T-0520), bay count,
    # snapping and clamp together, and the signage layer reads the same list.
    for u0, u1, z0, z1 in front_window_rects(p, x0, x1, shop):
        _opening(b, "y", y1, u0, u1, z0, z1, 1, conf)

    # The flanks: one window per storey per end, and one on the back. A store's
    # side walls were party walls in waiting on a platted street, so they are
    # sparse rather than blank. Three things suppress one: an elevation buried
    # behind the ell, the ground storey of the loading gable where the goods door
    # is, and the free span of the back wall when the goods door is there instead.
    buried_x1 = p.ell and p.ell_side == "end"
    rear_x0 = ell_extent(p)[2] if (p.ell and p.ell_side == "rear") else x0
    goods_end = _loading_sign(p) if (p.goods_door and p.goods_door_side == "end") else 0.0
    yc = (y0 + y1) / 2.0
    xc = (rear_x0 + x1) / 2.0
    for story in range(p.stories):
        z0 = storey_sill_z(p, story)
        for xx, sgn in ((x0, -1), (x1, 1)):
            if sgn > 0 and buried_x1:
                continue
            if story == 0 and sgn == goods_end:
                continue
            _opening(b, "x", xx, yc - win_w / 2, yc + win_w / 2, z0, z0 + win_h,
                     sgn, conf)
        if story == 0 and p.goods_door and p.goods_door_side == "rear":
            continue
        if x1 - rear_x0 > win_w + 0.6:
            _opening(b, "y", y0, xc - win_w / 2, xc + win_w / 2, z0, z0 + win_h,
                     -1, conf)


def _plain_door(b: MeshBuilder, p: FrameStorefrontParams, x0: float, x1: float,
                y: float, conf: float) -> None:
    """The facade of a store with no shopfront — a storehouse door and nothing
    else. Robert Kinzie's Wolf Point 'storehouse' is the case: attested as a place
    that dealt in groceries and Indian goods, with nothing said about a street
    face, and a shop window invented for it would be evidence manufactured out of
    a trade."""
    u0, u1, z0, z1 = plain_door_rect(x0, x1)
    _opening(b, "y", y, u0, u1, z0, z1, 1, conf)


def _goods_door(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
                x1: float, y1: float, conf: float) -> None:
    """The freight opening: a wide board door on the loading side.

    A store advertising dry goods, groceries and hardware, or calling itself a
    forwarding and commission house, took freight off a wagon — and not through the
    door its customers used. That much is type. Which side it stood on, how wide it
    was and whether it was one leaf or two is unattested for every store in the
    dossiers, so the whole thing carries the record's confidence for `goods_door`,
    which defaults to conjectural.
    """
    w, h = 1.85, 2.30
    if p.goods_door_side == "rear":
        # the free stretch of the back wall — a rear ell takes the -x end of it
        gx0 = ell_extent(p)[2] if (p.ell and p.ell_side == "rear") else x0
        cx = (gx0 + x1) / 2.0
        _opening(b, "y", y0, cx - w / 2, cx + w / 2, 0.02, h, -1, conf)
        _board(b, cx - 0.035, y0 - 0.055, cx + 0.035, y0 - 0.030, 0.02, h,
               conf, M_TRIM, skip=("bottom", "back"))
        return
    sgn = _loading_sign(p)
    xx = x1 if sgn > 0 else x0
    yc = (y0 + y1) / 2.0
    _opening(b, "x", xx, yc - w / 2, yc + w / 2, 0.02, h, int(sgn), conf)
    # the meeting stile between the two leaves
    _board(b, min(xx, xx + sgn * 0.055), yc - 0.035, max(xx, xx + sgn * 0.055),
           yc + 0.035, 0.02, h, conf, M_TRIM, skip=("bottom",))


def _loft_opening(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
                  x1: float, y1: float, wall_z: float, ridge_z: float,
                  conf: float) -> None:
    """The only external trace a loft leaves: one opening in a gable.

    Not a dormer and not a hoist beam — log_dwelling's rule, for the same reason.
    Peck's loft is documented and lodged a man; a dormer or a projecting hoist would
    be adding evidence to make the documented thing more visible. It goes in the
    gable the goods door is NOT on, so one elevation does not carry both.
    """
    if p.roof_type != "gable":
        return
    zc = wall_z + (ridge_z - wall_z) * 0.44
    hw, hh = 0.42, 0.46
    if _ridge_along_x(p):
        sgn = -_loading_sign(p)
        xx = (x1 if sgn > 0 else x0) + sgn * ROOF_OVERHANG_M
        yc = (y0 + y1) / 2.0
        _opening(b, "x", xx, yc - hw, yc + hw, zc - hh, zc + hh, int(sgn), conf)
    else:
        xc = (x0 + x1) / 2.0
        _opening(b, "y", y0 - ROOF_OVERHANG_M, xc - hw, xc + hw, zc - hh, zc + hh,
                 -1, conf)


# --------------------------------------------------------------------- the roof

def _roof(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
          x1: float, y1: float, wall_z: float, conf: float) -> float:
    """Gable or shed over the store block. Returns the highest point, which the
    chimneys need so a stack clears the roof it passes through."""
    if p.roof_type == "shed":
        return _shed_roof(b, x0, y0, x1, y1, wall_z, p.roof_pitch_deg, conf)
    return b.add_gable_roof(x0, y0, x1, y1, wall_z, p.roof_pitch_deg, conf, M_ROOF,
                            ridge_along_x=_ridge_along_x(p))


def _shed_roof(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
               eave_z: float, pitch_deg: float, conf: float,
               overhang: float = 0.25, thickness: float = 0.10) -> float:
    """A single plane falling from the back wall to the facade.

    Falling toward the street is log_dwelling's convention and is kept so a shed
    roof on a store and a shed roof on a cabin are the same claim. It is worth
    noting what it costs a shop: the eave drips over the walk in front of the door,
    which is a reason a record should have to SAY shed before it gets one — and it
    does, since this branch is only ever reached when `roof_type` names it.
    """
    x0, y0, x1, y1 = x0 - overhang, y0 - overhang, x1 + overhang, y1 + overhang
    rise = (y1 - y0) * math.tan(math.radians(pitch_deg))
    hi = eave_z + rise
    b.add_poly([(x0, y0, hi), (x1, y0, hi), (x1, y1, eave_z), (x0, y1, eave_z)],
               conf, M_ROOF)
    b.add_poly([(x0, y1, eave_z - thickness), (x1, y1, eave_z - thickness),
                (x1, y0, hi - thickness), (x0, y0, hi - thickness)], conf, M_ROOF)
    b.add_poly([(x0, y1, eave_z - thickness), (x1, y1, eave_z - thickness),
                (x1, y1, eave_z), (x0, y1, eave_z)], conf, M_ROOF)
    for x, sgn in ((x0, -1), (x1, 1)):
        pts = [(y0, hi - thickness), (y0, hi), (y1, eave_z), (y1, eave_z - thickness)]
        if sgn > 0:
            pts.reverse()
        b.add_poly([(x, y, z) for y, z in pts], conf, M_ROOF)
    return hi


# ---------------------------------------------------------------------- the ell

def _ell(b: MeshBuilder, p: FrameStorefrontParams, conf: float,
         c_clad: float) -> None:
    """The working half — storeroom, counting room, kitchen.

    A rear ell gets a lean-to that tucks under the store's eave; an end ell gets
    the ridge run on, which is the cheapest way to lengthen a framed building and
    the same argument log_dwelling's L24 makes for an end addition. Its confidence
    is its own and does not inherit the store block's.
    """
    ex0, ey0, ex1, ey1 = ell_extent(p)
    ez = p.ell_wall_height_m

    if p.ell_side == "end":
        # the abutting face is -x; no siding, no corner boards, no eave overhang
        # driven into the store's roof plane
        b.add_box(ex0, ey0, 0.0, ex1, ey1, ez, conf, M_WALL,
                  skip=("bottom", "top", "left"))
        _clapboard_faces(b, ex0, ey0, ex1, ey1, ez, c_clad,
                         faces=("front", "back", "right"),
                         course=p.siding_exposure_m)
        b.add_gable_roof(ex0 + 0.26, ey0, ex1, ey1, ez, p.roof_pitch_deg, conf,
                         M_ROOF, ridge_along_x=True)
        yc = (ey0 + ey1) / 2.0
        _opening(b, "x", ex1, yc - 0.42, yc + 0.42, ez * 0.34, ez * 0.34 + 1.0,
                 1, conf)
        _opening(b, "y", ey1, (ex0 + ex1) / 2 - 0.42, (ex0 + ex1) / 2 + 0.42,
                 ez * 0.34, ez * 0.34 + 1.0, 1, conf)
        return

    # rear ell: the abutting face is +y, against the store's back wall
    b.add_box(ex0, ey0, 0.0, ex1, ey1, ez, conf, M_WALL,
              skip=("bottom", "top", "back"))
    _clapboard_faces(b, ex0, ey0, ex1, ey1, ez, c_clad,
                     faces=("front", "left", "right"), course=p.siding_exposure_m)
    _lean_to(b, ex0, ey0, ex1, ey1, ez, p.ell_depth_m, conf)
    xc = (ex0 + ex1) / 2.0
    _opening(b, "y", ey0, xc - 0.42, xc + 0.42, ez * 0.34, ez * 0.34 + 0.95,
             -1, conf)
    _opening(b, "x", ex0, (ey0 + ey1) / 2 - 0.42, (ey0 + ey1) / 2 + 0.42,
             ez * 0.34, ez * 0.34 + 0.95, -1, conf)


def _lean_to(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
             eave_z: float, depth: float, conf: float) -> None:
    """A shed roof rising from the ell's outer wall to the store's back wall.

    The pitch is the one the parameter module refuses an ell for exceeding, so the
    roof that gets built and the roof the commit gate checked are the same roof.
    """
    oh, thk = 0.18, 0.09
    rise = depth * 0.2679                                # tan 15 degrees
    xa, xb = x0 - oh, x1 + oh
    yf, yb = y0 - oh, y1
    lo, hi = eave_z, eave_z + rise
    for dz in (0.0, -thk):
        b.add_poly([(xa, yf, lo + dz), (xb, yf, lo + dz),
                    (xb, yb, hi + dz), (xa, yb, hi + dz)], conf, M_ROOF)
    b.add_poly([(xa, yf, lo - thk), (xb, yf, lo - thk),
                (xb, yf, lo), (xa, yf, lo)], conf, M_ROOF)      # eave fascia
    for x in (xa, xb):
        b.add_poly([(x, yf, lo - thk), (x, yf, lo),
                    (x, yb, hi), (x, yb, hi - thk)], conf, M_ROOF)
    # The wedge of wall the rising roof leaves open at each end. Without these the
    # ell is a box with a lid propped up on one side and you can see straight in.
    for x, out in ((x0, -1), (x1, 1)):
        pts = [(x, y0, lo), (x, y1, lo), (x, y1, hi)]
        if out < 0:
            pts.reverse()
        b.add_poly(pts, conf, M_WALL)


def _clapboard_faces(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
                     wall_z: float, conf: float, faces: tuple[str, ...],
                     course: float) -> None:
    """Lap courses on named elevations only — the ell abuts the store on one side
    and siding driven into that joint is a z-fighting stripe down the seam."""
    lip, drop = CLAD_RELIEF_M, 0.022
    for i in range(1, int(wall_z / course)):
        z = i * course
        if "back" in faces:
            b.add_poly([(x0, y1 + lip, z - drop), (x1, y1 + lip, z - drop),
                        (x1, y1, z), (x0, y1, z)], conf, M_WALL)
        if "front" in faces:
            b.add_poly([(x1, y0 - lip, z - drop), (x0, y0 - lip, z - drop),
                        (x0, y0, z), (x1, y0, z)], conf, M_WALL)
        if "left" in faces:
            b.add_poly([(x0 - lip, y0, z - drop), (x0 - lip, y1, z - drop),
                        (x0, y1, z), (x0, y0, z)], conf, M_WALL)
        if "right" in faces:
            b.add_poly([(x1 + lip, y1, z - drop), (x1 + lip, y0, z - drop),
                        (x1, y0, z), (x1, y1, z)], conf, M_WALL)


# ------------------------------------------------------- framing, made visible

def _exposed_framing(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
                     x1: float, y1: float, wall_z: float, ridge_z: float,
                     conf: float) -> None:
    """The loading gable left open: studs at their true centres over board
    sheathing, and the siding stopping short below them.

    THIS IS THE ONE PLACE THE STUD RHYTHM CAN BE COUNTED. On a finished building
    the framing is behind the sheathing and reaches the elevation only as a module
    — see `_trim` and `_snap`. Here it is the elevation: studs 2 in by 4 in at 16 in
    on centre for a balloon frame, 8 ft posts with lighter studs between for a
    braced one, over 9 in horizontal boards. A viewer who knows what balloon
    framing is can check this wall against the thing Chicago invented in 1833.

    Only ever reached when a record says the building was unfinished, which is a
    state the sources describe rather than one this archetype assumes: John Calhoun
    took a building at South Water & Clark for the *Chicago Democrat* in November
    1833 'which was unfinished at the time', and Peck's loft was unfinished when a
    visiting minister lodged in it in May 1833.
    """
    if p.roof_type != "gable":
        return
    balloon = p.construction == "balloon_frame"
    module = STUD_SPACING_M if balloon else POST_SPACING_M / 2.0
    stud_w = STUD_FACE_M if balloon else 0.076

    if _ridge_along_x(p):
        sgn = _loading_sign(p)
        plane = x1 if sgn > 0 else x0
        u0, u1 = y0, y1
        axis = "x"
    else:
        sgn, plane, axis = -1.0, y0, "y"
        u0, u1 = x0, x1

    out = int(sgn)
    # The gable this stands on is the ROOF's filled triangle, which reaches
    # ROOF_OVERHANG_M outboard of the wall on either hand — so the open frame is
    # drawn against that plane and across that width. Building it in the wall plane
    # instead puts the whole thing inside the roof, which is the failure the
    # ROOF_OVERHANG_M note at the top of this module records.
    ge0, ge1 = u0 - ROOF_OVERHANG_M, u1 + ROOF_OVERHANG_M
    um = (ge0 + ge1) / 2.0
    slope = math.tan(math.radians(p.roof_pitch_deg))
    gp = plane + sgn * (ROOF_OVERHANG_M + 0.006)

    def rake_z(u: float) -> float:
        """Height of the roof line above a point across the gable."""
        return ridge_z - abs(u - um) * slope

    # the dark of the open bay, in front of the roof's own gable panel
    if axis == "x":
        pts = [(gp, ge0, wall_z), (gp, ge1, wall_z), (gp, um, ridge_z)]
    else:
        pts = [(ge0, gp, wall_z), (ge1, gp, wall_z), (um, gp, ridge_z)]
    if out < 0:
        pts.reverse()
    b.add_poly(pts, conf, M_GLASS)

    # Board sheathing, nine inches to the board and laid horizontally, which is
    # what came off the St Joseph mills by scow at $12 a thousand. It has reached
    # the lower part of the gable and stopped, and below the plate it stands proud
    # of the clapboards because the clapboards have not been hung there yet.
    line = wall_z + (ridge_z - wall_z) * 0.46          # how far the boarding got
    z = max(wall_z - SHEATHING_BOARD_M * 4, 2.30)
    while z < line:
        if z >= wall_z:
            half = max(ridge_z - z, 0.0) / max(slope, 1e-6)
            a, c, face = um - half, um + half, gp + sgn * 0.006
        else:
            a, c, face = u0, u1, plane + sgn * 0.034
        if c - a > 0.12:
            _panel(b, axis, face, a, c, z, z + SHEATHING_BOARD_M - 0.014,
                   out, conf, M_TIMBER)
        z += SHEATHING_BOARD_M

    # the plate the studs are nailed against, then the studs themselves — real
    # members with a 4 in depth, not stripes painted on a wall
    face = gp + sgn * (0.012 + STUD_DEPTH_M)
    _stick(b, axis, face, sgn, ge0, ge1 - ge0, wall_z - 0.10, wall_z + 0.05, conf)
    u = snap(ge0 + module, ge0, module)
    while u < ge1 - 0.10:
        top = rake_z(u)
        if top - wall_z > 0.14:
            _stick(b, axis, face, sgn, u - stud_w / 2, stud_w,
                   wall_z - 0.04, top - 0.03, conf)
        u += module
    # the rake boards the studs are cut to
    for a, c, za, zc in ((ge0, um, wall_z, ridge_z), (um, ge1, ridge_z, wall_z)):
        _rake(b, axis, face + sgn * 0.006, a, c, za, zc, out, conf)


def _stick(b: MeshBuilder, axis: str, plane: float, sgn: float, u: float,
           width: float, z0: float, z1: float, conf: float) -> None:
    """One framing member standing in an open wall — a stud, or the plate.

    Built as a box with its real depth, so the frame reads as timber standing in
    space rather than as a striped panel. `plane` is the outer face of the wall and
    the member runs back into the building from it.
    """
    back = plane - sgn * STUD_DEPTH_M
    lo, hi = (back, plane) if back < plane else (plane, back)
    if axis == "x":
        b.add_box(lo, u, z0, hi, u + width, z1, conf, M_TIMBER,
                  skip=("bottom", "top"))
    else:
        b.add_box(u, lo, z0, u + width, hi, z1, conf, M_TIMBER,
                  skip=("bottom", "top"))


def _rake(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
          z0: float, z1: float, out: int, conf: float) -> None:
    """A sloping board along a gable's rake, as a thin parallelogram."""
    t = 0.11
    if axis == "x":
        pts = [(plane, u0, z0), (plane, u1, z1), (plane, u1, z1 - t),
               (plane, u0, z0 - t)]
        natural = 1
    else:
        pts = [(u0, plane, z0), (u1, plane, z1), (u1, plane, z1 - t),
               (u0, plane, z0 - t)]
        natural = -1
    if out != natural:
        pts.reverse()
    b.add_poly(pts, conf, M_TIMBER)


# ----------------------------------------------------------------- the chimneys

def _chimneys(b: MeshBuilder, p: FrameStorefrontParams, x0: float, y0: float,
              x1: float, y1: float, ridge_z: float, wall_z: float,
              conf: float, mat: int) -> None:
    """As many stacks as the record counts, on the ridge line.

    The COUNT is the record's and the arrangement is the archetype's, which is what
    docs/LIBERTIES.md L26 owns for every building in this dataset. The fractions are
    frame_tavern's 0.22 and 0.78 deliberately: a store and a tavern standing on the
    same street should not carry visibly different stack logic when neither
    building has a stack described in any source.
    """
    if p.chimneys <= 0:
        return
    half = 0.42
    for f in _stack_fractions(p.chimneys):
        if p.roof_type == "shed":
            cx = x0 + (x1 - x0) * f
            cy = y0 + 0.55
            top = ridge_z + 0.45
        elif _ridge_along_x(p):
            cx = x0 + (x1 - x0) * f
            cy = (y0 + y1) / 2.0
            top = ridge_z + 0.55
        else:
            cx = (x0 + x1) / 2.0
            cy = y0 + (y1 - y0) * f
            top = ridge_z + 0.55
        b.add_box(cx - half, cy - half, wall_z - 0.6, cx + half, cy + half, top,
                  conf, mat, skip=("bottom",))
        b.add_box(cx - half - 0.07, cy - half - 0.07, top,
                  cx + half + 0.07, cy + half + 0.07, top + 0.16,
                  conf, mat, skip=("bottom",))


def _stack_fractions(n: int) -> tuple[float, ...]:
    """Where n stacks stand, as fractions of the ridge. frame_tavern's positions,
    for the reason given in _chimneys."""
    if n <= 0:
        return ()
    if n == 1:
        return (0.22,)
    step = (0.78 - 0.22) / (n - 1)
    return tuple(0.22 + i * step for i in range(n))
