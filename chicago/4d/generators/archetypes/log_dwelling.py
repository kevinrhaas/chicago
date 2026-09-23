"""log_dwelling — a hewn-log building, optionally with a frame addition and a sign.

The commonest building at the forks in 1835 and therefore the archetype that most of
the town will be made of. It has to cover three attested cases without becoming a
kit-of-parts: Wolf Point Tavern (log core, frame extension, painted wolf sign hung
outside by about 1833), Samuel Miller's house (log cabin with a two-storey frame
addition fronting the river) and Rev. Jesse Walker's meeting house ("a small square
log building, originally designed for a school-house" — Wau-Bun). Evidence and its
disagreements: docs/research/03-structures-north.md §2.1, §2.2, §3.1.

**Orientation.** The facade faces NORTH at rotation_deg 0, per the pinned convention
in docs/GLB-CONTRACT.md. In Blender that is the +y face, because the exporter's
`export_yup=True` maps Blender +Y to glTF -Z, which the contract defines as north. The
door, the sign and any front addition are all on +y. Getting this wrong is a silent
error — the building looks fine and faces the wrong way — so it is stated here as well
as in the contract.

**The sign is a board, and since 2026-08-21 it may carry a picture — T-0072.** The
paragraph this replaces read: *"The wolf sign is documented; what the painted wolf
looked like is not, and no image of it survives. So the geometry is a signboard hanging
from a bracket, and the `sign` parameter carries the subject as a string for the sidecar
to report. Painting a wolf on it would be manufacturing evidence in exactly the way
AGENTS.md rule 1 forbids, and it would be the most-photographed invention in the scene."*
It is kept because its caution was right about the one thing that has not changed — the
DRAUGHTSMANSHIP of the Wolf Point wolf is lost and nothing here recovers it.

What changed is that the sources were read further. chicagology's Wolf's Point note
(`chicagology_prefire273`) says how the board was made, hung and decorated: *"Wentworth
was ambitious, and wanted a sign to attract wayfarers. Lieutenant Allen made one for him
out of a piece of a box. He painted a picture of a wolf on it. The fort blacksmith made
hinges, and the wolf sign was hung on a sapling. The tavern was the first institution to
have a sign board in Chicago."* Three things in that passage are geometry — a board, iron
hinges, and a **sapling** rather than a wall bracket — and the 2026-08-18 owner brief's
engraving of the tavern draws exactly that: a mast-tall pole with a cross-arm, the board
flying from it. `sign_mount` builds it.

So a blank board is now a positive misstatement: a source says a picture of a wolf was on
it, and leaving the board empty asserts the opposite of the evidence. `sign_device` paints
a flat canine silhouette — **the FACT is attested and the OUTLINE is this module's own**,
which is the `reconstructed` tier doing its job (AGENTS.md § RECONSTRUCTED IS A TIER) and
is recorded in docs/LIBERTIES.md. It defaults off, so no other board in the town gains a
picture; nothing here licenses a device on a board whose subject is not attested.

**Log courses and corner notching** come from common/logwork.py, which is
frame_tavern._log_wing's visual language factored out. That is deliberate: the
Sauganash's log wing and the Wolf Point Tavern were built by the same handful of people
within a couple of years of each other, and they should look it.

**A note on face winding.** Every quad here is wound so its normal points out of the
building. Blender's exporter writes `doubleSided: true` for a default material, so a
reversed face is invisible today — but the contract says counter-clockwise and outward,
the palette/meshopt steps are entitled to rely on it, and a renderer that ever enables
culling would find holes rather than a bug report. `_panel` exists so no recessed
opening can get this wrong by hand.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.logwork import (  # noqa: E402
    CHINK_RGBA, HEWN_RGBA, RELIEF_M, hewn_log_wall, log_prism,
)
from common import materials  # noqa: E402
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.log_dwelling_params import (  # noqa: E402
    ADDITION_WIN_HALF_M, DOOR_HALF_M, WIN_AT_FRAC, WIN_HALF_M, LogDwellingParams,
    addition_extent, addition_front_rects, core_extent, core_front_rects,
)

# Materials are indices into the list passed to to_object(), in this order.
M_LOG, M_CHINK, M_ROOF, M_FRAME, M_DARK, M_SIGN, M_PAINT = 0, 1, 2, 3, 4, 5, 6
# The stack (T-0008). Appended LAST, after the conditional M_PAINT, so every
# index above it is fixed and a building with no painted device keeps the shorter
# list — the same discipline M_PAINT itself is held to at the mats list below,
# and for the same reason: an unreferenced slot still reaches the glTF and would
# rewrite masters for a colour they do not use.
M_CHIMNEY_AFTER_SIGN, M_CHIMNEY_AFTER_PAINT = 6, 7

CLAPBOARD_COURSE_M = 0.14   # exposed face of a period clapboard, ~5.5 in
# A weathered board, left deliberately neutral. What colour the Wolf Point signboard
# was painted is unattested; a neutral board makes a claim about as small as geometry
# can make while still being visible.
SIGN_RGBA = (0.60, 0.54, 0.44, 1.0)
# The device painted on a board. Dark and flat — a sign painter at the forks in the
# early 1830s had lampblack in oil and little else, and a silhouette is what reads at
# the distance a pole sign is meant to be read from. Not black: a hand-ground black
# in linseed goes brown-grey, and a true black would read as a hole in the board.
PAINT_RGBA = (0.116, 0.098, 0.086, 1.0)

# --- the sapling pole sign (T-0072) -------------------------------------------
# Every number here is this module's own. The sources give a board made "out of a
# piece of a box", iron hinges, and a sapling to hang it on; they give no dimension
# at all, and the engraving is a tier-5 retrospective that may drive form and never a
# measurement. What bounds them: a sapling stout enough to carry a board and stand a
# lake wind is a young trunk of about this butt diameter, and a sign meant "to attract
# wayfarers" has to clear the tavern's own ridge to be seen down the river bank.
POLE_ABOVE_RIDGE_M = 2.55   # how far the head stands over the roof it advertises
POLE_MIN_TOP_M = 7.4        # ...and a floor under it, for a low building
POLE_BUTT_R = 0.105         # butt radius; a sapling, not a mast
POLE_HEAD_R = 0.072
POLE_SET_M = 0.40           # how deep the butt is set below the wall line
POLE_STANDOFF_M = 1.15      # how far out from the facade it stands
POLE_ARM_M = 1.52           # the cross-arm's reach
POLE_ARM_R = 0.055
SIGN_BOARD = (0.92, 0.68, 0.055)     # width along the arm, drop, thickness
SIGN_HANGER_DROP_M = 0.17            # the hinge straps between arm and board
DEVICE_FRACTION = (0.78, 0.80)       # of the board, before the outline's own aspect
DEVICE_PROUD_M = 0.006


def build(params: LogDwellingParams, name: str):
    """Build the dwelling. Returns a Blender object at the local origin, y-up handled
    by the exporter (Blender is z-up internally)."""
    params.validate()
    b = MeshBuilder(name)

    # Massing takes the confidence of the attributes that say what the building WAS,
    # not the precision of its dimensions. The reasoning is set out at length in
    # frame_tavern.build and is not repeated here; the short form is that an unknown
    # size and an unknown form are different kinds of not-knowing, and dithering a
    # well-attested building into ghost massing because nobody wrote down its width
    # misrepresents the evidence in the direction of false modesty.
    #
    # For a log building the construction IS the cladding, so where frame_tavern
    # reads ("stories", "construction", "cladding") this reads ("stories",
    # "construction") — there is no third attribute, not an omission.
    c_mass = params.worst_conf("stories", "construction")
    c_roof = params.worst_conf("roof_type", "roof_pitch_deg")

    # Where the log core sits inside the footprint once the addition is carved out.
    cx0, cy0, cx1, cy1 = core_extent(params)
    wall_z = params.wall_height_m

    hewn_log_wall(b, cx0, cy0, cx1, cy1, 0.0, wall_z, c_mass, M_LOG, M_CHINK,
                  skip=("bottom", "top"))

    ridge_z = _roof(b, params, cx0, cy0, cx1, cy1, wall_z, c_roof)

    if params.loft:
        _loft_opening(b, params, cx0, cy0, cx1, cy1, wall_z, ridge_z,
                      params.conf("loft"))

    _core_openings(b, params, cx0, cy0, cx1, cy1, wall_z,
                   params.conf("fenestration", "reconstructed"))

    addition_ridge_z = _frame_addition(b, params) if params.frame_addition else None

    painted = bool(params.sign and params.sign_device)
    _chimneys(b, params, cx0, cy0, cx1, cy1, ridge_z, addition_ridge_z,
              params.conf("chimneys", "reconstructed"),
              (M_CHIMNEY_AFTER_PAINT if painted else M_CHIMNEY_AFTER_SIGN)
              if params.chimneys > 0 else M_ROOF)

    if params.sign:
        # The BOARD's confidence is the confidence that a sign hung there. Its size
        # and its bracket are invented, but those are dimensional, and by the
        # convention above dimensions do not drag an object's character down.
        #
        # THE MOUNTING IS A SEPARATE CLAIM and takes its own confidence, because at
        # Wolf Point it is the better-evidenced half: a source says the board hung on
        # a sapling and no source says a board hung on a bracket anywhere. So the
        # pole is built at `sign_mount`'s grade and the board it carries at `sign`'s,
        # least-confident-wins over the pair for the members that are both.
        if params.sign_mount == "sapling_pole":
            _sign_pole(b, params, ridge_z,
                       params.worst_conf("sign", "sign_mount"),
                       params.conf("sign", "reconstructed"),
                       params.conf("sign_device", "reconstructed"))
        else:
            _sign(b, params, params.conf("sign", "reconstructed"))

    # ---- the surfaces, off the sheet (T-0007) --------------------------------
    # The log core is the town's log fabric and does not vary: a cabin's walls ARE
    # its finish. What varies is the FRAME ADDITION, which is a clapboarded wall like
    # any other and now wears the finish the record deals it, and the roof, which
    # takes the weathering condition 218 records state — a condition, never a
    # covering (materials.md finding 2). See `common/materials.py`.
    frame_finish = materials.wall_finish(params.frame_paint, params.finish_key)
    frame_rgba, frame_rough = materials.resolve(
        materials.wall_substrate(cladding="clapboard"), frame_finish)
    mats = [
        simple_material("log", HEWN_RGBA,
                        roughness=materials.SUBSTRATES["hewn_log"].roughness),
        simple_material("chinking", CHINK_RGBA,
                        roughness=materials.SUBSTRATES["chinking"].roughness),
        simple_material("roof", materials.roof_finish(params.roof_condition).rgba,
                        roughness=0.9),
        simple_material("frame", frame_rgba, roughness=frame_rough),
        # ONE DARK (T-0126) — the sheet's `DARK` row, converging the three readings
        # materials.md §2.3 measured. This archetype's door, windows and gable vent
        # are the unglazed end of that family; the sign's iron hinge straps ride on
        # the same slot, which the row's note records rather than hides, because
        # giving them one of their own would add a material to every log cabin.
        simple_material("dark", materials.DARK.rgba,
                        roughness=materials.DARK.roughness),
        simple_material("sign", SIGN_RGBA, roughness=0.85),
    ]
    # M_PAINT is appended only where a device is actually painted, and only ever
    # LAST, so every index above it is fixed. A material slot nothing references
    # still reaches the glTF, and adding one to all 43 log buildings would have
    # rewritten 43 masters — and with them their compressed derivatives and the
    # banked passthrough set — for a colour none of them uses.
    if params.sign and params.sign_device:
        mats.append(simple_material("paint", PAINT_RGBA, roughness=0.72))
    # THE STACK IS NOT THE ROOF (T-0008), and on a log cabin it is not brick either.
    # `_stack` below has always argued the disposition — built against the gable so it
    # can be pulled away from the building when it catches fire — and that is a
    # stick-and-clay or fieldstone stack, not the masonry a framed house carries up
    # inside its wall. `common/materials.py` § the chimney stack holds the tone and
    # docs/RESEARCH/chimneys.md the argument; docs/LIBERTIES.md L168 records that the
    # fabric is invented, as L26 already records that the position is.
    if params.chimneys > 0:
        stack = materials.chimney_finish("exterior_gable")
        mats.append(simple_material("chimney", stack.rgba, roughness=stack.roughness))
    return b.to_object(mats)


# ---------------------------------------------------------------- plan geometry

def _ridge_along_x(x0, y0, x1, y1) -> bool:
    return (x1 - x0) >= (y1 - y0)


#: THE FACADE'S OWN NUMBERS, hoisted out of `_core_openings` (T-0435) and moved on
#: into log_dwelling_params with T-0520, which is where the facade is now set out.
#: They are still named here because the stack placement below reads them: a second
#: stack that lands on a gable-fronted core's FACADE has to go in the band that
#: facade leaves clear, and two copies of these figures would be a silent way for
#: the stack and the door to drift back into each other. These are the params
#: module's values, not a copy of them.
_DOOR_HALF = DOOR_HALF_M
_WIN_HALF = WIN_HALF_M
_WIN_AT = WIN_AT_FRAC
#: Half the stack shaft, and the air left between it and any opening it stands beside.
_STACK_HALF = 0.48
_STACK_CLEAR = 0.04


def _gable_axis(p: LogDwellingParams, x0, y0, x1, y1) -> str:
    """Which axis the log core's two GABLE faces sit on: 'x' or 'y' (T-0435).

    The gables are the ends the ridge runs to, so this is the ridge's own axis. A
    gable roof runs it along the longer plan axis (`_ridge_along_x`). A SHED roof has
    no gable at all in the strict sense, but `_shed_roof` always falls from the -y
    wall to the facade whatever the plan proportions are, so its high edge — the line
    everything here measures a stack against — always runs along x, and its sloping
    ends are always the +/-x faces. Hence the shed case is 'x' unconditionally, and is
    NOT `_ridge_along_x`: reading a shed roof off the plan would move a deep shed
    cabin's stack off the end it correctly stands on. No record in the 1835 scene asks
    for a shed-roofed log dwelling today — all 49 are gable — so this branch is a rule
    stated before it is needed, not a reading of anything committed.
    """
    if p.roof_type == "shed":
        return "x"
    return "x" if _ridge_along_x(x0, y0, x1, y1) else "y"


# ------------------------------------------------------------------ primitives

def _panel(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
           z0: float, z1: float, outward: int, conf: float, mat: int) -> None:
    """One flat rectangle on an axis-aligned plane, wound to face `outward`.

    `axis` names the plane's normal axis ('x' or 'y'); `u0`/`u1` run along the other
    horizontal axis. Every recess in this module goes through here so none of them can
    end up facing into the building.
    """
    if axis == "y":
        pts = [(u0, plane, z0), (u1, plane, z0), (u1, plane, z1), (u0, plane, z1)]
        natural = -1          # this order's normal points -y
    else:
        pts = [(plane, u0, z0), (plane, u1, z0), (plane, u1, z1), (plane, u0, z1)]
        natural = 1           # this order's normal points +x
    if outward != natural:
        pts.reverse()
    b.add_poly(pts, conf, mat)


def _opening(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
             z0: float, z1: float, outward: int, conf: float,
             surround: int = M_FRAME, relief: float = RELIEF_M) -> None:
    """A door or window: a dark opening inside a sawn surround.

    The surround is not decoration. An opening drawn as a bare dark rectangle has to
    sit proud of the log faces to be visible at all, which makes it read as a plaque
    glued to the wall — the first version of this looked exactly like that. A log wall
    cannot have a hole in it without sawn jambs and a head to carry the cut courses,
    so the surround is both the honest detail and the thing that makes the opening
    read as a hole. Two quads, four triangles.

    Both are flat, so the dark panel has to sit very slightly IN FRONT of the surround
    rather than recessed into it — it is entirely inside the surround's outline and
    would otherwise be hidden by it. Six millimetres: enough to order the two reliably,
    little enough that the glass does not visibly bulge out of its own frame.
    """
    off = relief + 0.010
    m = 0.085
    _panel(b, axis, plane + outward * off, u0 - m, u1 + m, z0 - m, z1 + m,
           outward, conf, surround)
    _panel(b, axis, plane + outward * (off + 0.006), u0, u1, z0, z1,
           outward, conf, M_DARK)


def _plate(b: MeshBuilder, x: float, half: float, pts_yz, conf: float,
           mat: int) -> None:
    """A thin flat member lying in a y-z plane, extruded +-`half` in x.

    Both faces and all edges are emitted with outward winding, so a brace read from
    behind is still solid. `pts_yz` is a polygon in (y, z), counter-clockwise as seen
    from +x.
    """
    n = len(pts_yz)
    b.add_poly([(x + half, y, z) for y, z in pts_yz], conf, mat)
    b.add_poly([(x - half, y, z) for y, z in reversed(pts_yz)], conf, mat)
    for i in range(n):
        (ya, za), (yb, zb) = pts_yz[i], pts_yz[(i + 1) % n]
        b.add_poly([(x - half, ya, za), (x - half, yb, zb),
                    (x + half, yb, zb), (x + half, ya, za)], conf, mat)


# ------------------------------------------------------------------------ roof

def _roof(b: MeshBuilder, p: LogDwellingParams, x0, y0, x1, y1,
          eave_z: float, conf: float) -> float:
    """Gable or shed over the log core. Returns the height of the highest point,
    which the chimney needs so its stack clears the ridge."""
    if p.roof_type == "shed":
        return _shed_roof(b, x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf, M_ROOF)
    return b.add_gable_roof(x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf, M_ROOF,
                            ridge_along_x=_ridge_along_x(x0, y0, x1, y1))


def _shed_roof(b: MeshBuilder, x0, y0, x1, y1, eave_z, pitch_deg, conf, mat,
               overhang: float = 0.25, thickness: float = 0.10) -> float:
    """A single plane falling from the back (-y, south) wall to the facade (+y).

    Falling toward the facade rather than away from it is the frontier default: the
    tall wall is the one the chimney and the back rooms go against, and rain runs off
    in front of the door where the ground is trodden hard. It is a convention, not an
    attested fact, and it is only ever reached when a record explicitly says shed.
    """
    x0, y0, x1, y1 = x0 - overhang, y0 - overhang, x1 + overhang, y1 + overhang
    rise = (y1 - y0) * math.tan(math.radians(pitch_deg))
    hi = eave_z + rise
    b.add_poly([(x0, y0, hi), (x1, y0, hi), (x1, y1, eave_z), (x0, y1, eave_z)],
               conf, mat)
    b.add_poly([(x0, y1, eave_z - thickness), (x1, y1, eave_z - thickness),
                (x1, y0, hi - thickness), (x0, y0, hi - thickness)], conf, mat)
    b.add_poly([(x0, y1, eave_z - thickness), (x1, y1, eave_z - thickness),
                (x1, y1, eave_z), (x0, y1, eave_z)], conf, mat)          # eave fascia
    for x, sgn in ((x0, -1), (x1, 1)):
        pts = [(y0, hi - thickness), (y0, hi), (y1, eave_z), (y1, eave_z - thickness)]
        if sgn > 0:
            pts.reverse()
        b.add_poly([(x, y, z) for y, z in pts], conf, mat)
    return hi


# -------------------------------------------------------------------- openings

def _loft_opening(b: MeshBuilder, p: LogDwellingParams, x0, y0, x1, y1,
                  wall_z: float, ridge_z: float, conf: float) -> None:
    """The only external trace a loft leaves: a small opening in one gable.

    Not a dormer. Dormers on log cabins are a later, richer habit, and adding one to
    make the loft more visible would be adding evidence rather than reading it.

    One gable, not both, and specifically the gable the chimney is NOT on. The stack
    stands against the LOW end of the ridge's own axis (`_chimneys`, `_gable_axis`) and
    is wider than this opening, so an opening at both ends buries one of them inside
    masonry — invisible in the render and still costing its triangles. The vent below
    takes the +x or +y end to match, which is why both read the same `_ridge_along_x`.
    """
    if p.roof_type != "gable":
        return
    zc = wall_z + (ridge_z - wall_z) * 0.42
    hw, hh, out = 0.34, 0.30, 0.07
    if _ridge_along_x(x0, y0, x1, y1):
        yc = (y0 + y1) / 2.0
        _panel(b, "x", x1 + out, yc - hw, yc + hw, zc - hh, zc + hh, 1, conf, M_DARK)
    else:
        xc = (x0 + x1) / 2.0
        _panel(b, "y", y1 + out, xc - hw, xc + hw, zc - hh, zc + hh, 1, conf, M_DARK)


def _core_openings(b: MeshBuilder, p: LogDwellingParams, x0, y0, x1, y1,
                   wall_z: float, conf: float) -> None:
    """Door and windows on the log core.

    Surfaces, not holes: at this LOD a real opening would show the inside of the far
    wall, and interiors are out of scope. Openings in a log wall were few and small
    because every one of them cuts the courses and has to be framed — one door and one
    or two small windows is the type, and a cabin elevation with five bays would be a
    frame building wearing logs.

    When a front addition exists it takes the front door, so the core gets a window
    where its door would have been.
    """
    front_taken = p.frame_addition and p.frame_addition_side == "front"
    xm = (x0 + x1) / 2.0
    ym = (y0 + y1) / 2.0
    gable_front = _gable_axis(p, x0, y0, x1, y1) == "y"

    # THE FACADE IS THE PARAMS MODULE'S SET-OUT (T-0520). `core_front_rects` states
    # the door and the storey windows on this wall and the signage layer reads the
    # same list, so a board can no longer be hung over a window this builder drew
    # somewhere else. The rects arrive in the order they are drawn in: the door, then
    # two flanking windows per storey, then the centre window a front addition's
    # facade gets in place of its door. The flanks below are this builder's own and
    # are not stated there, but they take their band from the storey's front windows
    # rather than recomputing it.
    rects = core_front_rects(p)
    i = 0
    if not front_taken:
        _kind, u0, u1, z0, z1 = rects[i]
        i += 1
        _opening(b, "y", y1, u0, u1, z0, z1, 1, conf)

    for story in range(p.stories):
        band = rects[i:i + (3 if front_taken and story == 0 else 2)]
        i += len(band)
        for _kind, u0, u1, z0, z1 in band:
            _opening(b, "y", y1, u0, u1, z0, z1, 1, conf)
        z0, z1 = band[0][3], band[0][4]
        # ONE WINDOW BEHIND, AND NEVER IN A GABLE. The rule this line has always stated
        # is "none on the gable ends: the gables carry the chimney at one end and the
        # notching at both, and a log gable was rarely pierced" — but it was written
        # when the back wall was assumed to be an eave, which it is only on a cabin at
        # least as wide as it is deep. On a GABLE-FRONTED cabin (T-0435) -y is a gable
        # and now carries the stack, so the window goes to the -x eave instead, which
        # is the same rule applied to the roof the building actually has. The facade
        # itself is the one gable that is pierced when it is a gable, and it is pierced
        # because a cabin has to have a door.
        if gable_front:
            _opening(b, "x", x0, ym - _WIN_HALF, ym + _WIN_HALF, z0, z1, -1, conf)
        else:
            _opening(b, "y", y0, xm - _WIN_HALF, xm + _WIN_HALF, z0, z1, -1, conf)


# ------------------------------------------------------------- frame addition

def _frame_addition(b: MeshBuilder, p: LogDwellingParams) -> float:
    """The clapboarded frame block. Returns its ridge height.

    Its confidence is its own — Miller's two-storey addition is documented, Wolf
    Point's frame part is documented only as "partly frame" with no size — and it does
    not inherit the log core's.

    The ridge height goes back to the caller because a second stack stands on this
    block when the record counts two, and a stack has to clear the roof it comes
    through.
    """
    c = p.worst_conf("frame_addition", "frame_addition_stories")
    c_clad = p.conf("frame_addition", "reconstructed")
    c_fen = p.conf("fenestration", "reconstructed")
    ax0, ay0, ax1, ay1 = addition_extent(p)
    az = p.addition_height_m

    b.add_box(ax0, ay0, 0.0, ax1, ay1, az, c, M_FRAME, skip=("bottom", "top"))
    _clapboard(b, ax0, ay0, ax1, ay1, az, c_clad)
    # An end addition abuts the log core, so its roof gets no overhang on that side —
    # `add_gable_roof` grows uniformly, and 0.25 m of eave driven into the core's roof
    # plane is a z-fighting stripe right down the most visible surface of the building.
    rx0 = ax0 + 0.26 if p.frame_addition_side == "end" else ax0
    add_ridge_z = b.add_gable_roof(rx0, ay0, ax1, ay1, az, p.roof_pitch_deg, c, M_ROOF,
                                   ridge_along_x=True)

    rel = 0.026                    # clapboard lip, not log relief
    # THE ADDITION'S FACADE IS THE PARAMS MODULE'S SET-OUT (T-0520), door and
    # windows both, in the order they are drawn in — and it is the same list the
    # signage layer reads when a front addition is the wall a visitor faces.
    front_rects = addition_front_rects(p)
    for _kind, u0, u1, z0, z1 in front_rects:
        _opening(b, "y", ay1, u0, u1, z0, z1, 1, c_fen, relief=rel)
    # The gable end that is not buried in the log core gets one window per storey.
    # An END addition's front wall carries exactly two windows a storey and no door
    # (the core keeps that), so the storey's band is the pair at 2*story — read from
    # the facade rather than recomputed, which is the whole point of T-0520.
    if p.frame_addition_side == "end":
        yc = (ay0 + ay1) / 2.0
        for story in range(p.frame_addition_stories):
            z0, z1 = front_rects[2 * story][3:]
            _opening(b, "x", ax1, yc - ADDITION_WIN_HALF_M, yc + ADDITION_WIN_HALF_M,
                     z0, z1, 1, c_fen, relief=rel)
    return add_ridge_z


def _clapboard(b: MeshBuilder, x0, y0, x1, y1, wall_z: float, conf: float) -> None:
    """Horizontal lap courses as a thin proud lip per course, on the two elevations
    that face the town. Same treatment as frame_tavern, so a frame addition and a
    frame tavern read as the same material at fifty metres."""
    lip = 0.018
    n = int(wall_z / CLAPBOARD_COURSE_M)
    for i in range(1, n):
        z = i * CLAPBOARD_COURSE_M
        b.add_poly([(x0, y0, z), (x1, y0, z),
                    (x1, y0 - lip, z - 0.02), (x0, y0 - lip, z - 0.02)], conf, M_FRAME)
        b.add_poly([(x1, y1, z), (x0, y1, z),
                    (x0, y1 + lip, z - 0.02), (x1, y1 + lip, z - 0.02)], conf, M_FRAME)


# ------------------------------------------------------------ chimney and sign

def _chimneys(b: MeshBuilder, p: LogDwellingParams, cx0, cy0, cx1, cy1,
              ridge_z: float, add_ridge_z: float | None, conf: float,
              mat: int) -> None:
    """As many stacks as the record counts, placed by the archetype.

    The count is the record's; every other property of a stack here is invented, so
    the arrangement needs an argument rather than a preference, and the argument is
    the one the records themselves give:

    - The first stack stands against a GABLE end of the log core — the end the ridge
      runs to, not a fixed compass face. That is the frontier pattern and it is what
      this archetype's prose has always described; until T-0435 the code built it at
      the -x face unconditionally, so a cabin deeper than it is wide (`_roof` runs the
      ridge along the longer plan axis) put its stack against an EAVE instead, and 30
      of the town's 49 log stacks stood in a disposition the archetype argues against.
      Of the two gable ends the stack takes the one AWAY FROM THE STREET: on a
      gable-fronted cabin the facade is a gable, and a chimney is not what that
      elevation carries.
    - The second stands on the FRAME ADDITION when there is one. Miller's record
      counts two because "a two-part building of this size — a former tavern with a
      log cabin behind — would normally carry a stack in each element", and putting
      both on the log core would build a number the record gives while contradicting
      the reasoning it gives for the number. It goes against the addition's outer
      gable, mirroring the core's. The addition's roof is always built ridge-along-x
      (`_frame_addition`), so its gable ends are always its +/-x faces.
    - With no addition, a second stack goes against the core's other gable, which is
      the other end of the one element there is. No record in the dataset asks for
      this case yet.

    docs/LIBERTIES.md L26 owns all of it.
    """
    if p.chimneys <= 0:
        return
    axis = _gable_axis(p, cx0, cy0, cx1, cy1)
    _stack(b, cx0, cy0, cx1, cy1, ridge_z, conf, mat, at_min=True, gable_axis=axis)
    if p.chimneys < 2:
        return
    if p.frame_addition and add_ridge_z is not None:
        ax0, ay0, ax1, ay1 = addition_extent(p)
        _stack(b, ax0, ay0, ax1, ay1, add_ridge_z, conf, mat, at_min=False,
               gable_axis="x")
    else:
        _stack(b, cx0, cy0, cx1, cy1, ridge_z, conf, mat, at_min=False,
               gable_axis=axis,
               cross=_facade_stack_cross(cx1 - cx0) if axis == "y" else 0.0)


def _facade_stack_cross(span: float) -> float:
    """How far a second core stack slides along the FACADE gable to clear the door.

    Only a gable-fronted cabin reaches this (T-0435): its two gable ends are the back
    and the FRONT, so the second stack — the one that takes "the other end of the one
    element there is" — lands on the elevation carrying the front door. `brown_boarding_house`
    is the only record in the 1835 scene that asks for it: two stacks, no frame
    addition, 7.32 m wide and 12.19 m deep.

    Centred, the shaft would stand straight through the doorway. So it takes the clear
    band the facade leaves between the door reveal and the nearer flanking window, and
    stands in the middle of it — which is where an end-wall flue serving the front pen
    would rise anyway, beside the door rather than over it. If that band is too narrow
    to hold a shaft (a cabin under about 4.4 m wide), it goes just outside the door
    reveal instead and `_stack`'s own clamp keeps it inside the wall; no record asks
    for that case today.
    """
    lo = _DOOR_HALF + _STACK_CLEAR + _STACK_HALF
    hi = span * _WIN_AT - _WIN_HALF - _STACK_CLEAR - _STACK_HALF
    return (lo + hi) / 2.0 if hi > lo else lo


def _stack(b: MeshBuilder, x0, y0, x1, y1, ridge_z: float, conf: float, mat: int,
           at_min: bool, gable_axis: str = "x", cross: float = 0.0) -> None:
    """One exterior stack against a gable end — the low end of `gable_axis`, or
    mirrored to the high end.

    Outside the wall, not inside it, which is the frontier pattern: a stick-and-clay
    or fieldstone stack built against the gable can be pulled away from the building
    when it catches fire, and it does not eat floor space. Nothing about the stack is
    attested for any building in the dataset, so it carries the count's confidence
    and no more.

    `cross` slides the stack along its gable, away from centre; see `_facade_stack_cross`.

    `gable_axis` names the axis the ROOF RIDGE runs along, which is the axis whose two
    faces are gables. It is a parameter rather than a constant because it has to
    follow the roof: a gable roof on this archetype runs its ridge along the longer
    plan axis, so on a cabin deeper than it is wide the gables are the +/-y faces and
    a stack pinned to -x would stand against an eave — 2.3 to 3.2 m of flue above the
    roof beside it, and the very disposition docs/RESEARCH/chimneys.md §3 argues the
    cat-and-clay fabric AGAINST. See `_gable_axis`. The geometry below is written in a
    (gable, cross) frame and swapped into world axes at the last step, so the two
    orientations are the same block, not two blocks kept in step by hand.
    """
    glo, ghi, clo, chi = (x0, x1, y0, y1) if gable_axis == "x" else (y0, y1, x0, x1)
    half = _STACK_HALF
    # Centred on its gable unless the caller has to slide it clear of an opening, and
    # never past the wall's own corner.
    room = max((chi - clo) / 2.0 - half, 0.0)
    cc = (clo + chi) / 2.0 + max(-room, min(room, cross))
    face, out = (glo, -1.0) if at_min else (ghi, 1.0)

    def span(inset: float, proud: float) -> tuple[float, float]:
        """(low, high) along the gable axis for a block reaching `proud` out from the
        gable face and `inset` into it, on whichever end of the building this is."""
        a, c = face + out * proud, face - out * inset
        return (a, c) if a < c else (c, a)

    def box(g0: float, g1: float, c0: float, c1: float, z0: float, z1: float) -> None:
        if gable_axis == "x":
            b.add_box(g0, c0, z0, g1, c1, z1, conf, mat, skip=("bottom",))
        else:
            b.add_box(c0, g0, z0, c1, g1, z1, conf, mat, skip=("bottom",))

    sg0, sg1 = span(0.08, 0.72)
    box(sg0, sg1, cc - half, cc + half, 0.0, ridge_z + 0.55)
    # a slight corbel at the head, so it reads as a chimney rather than a post
    hg0, hg1 = span(0.12, 0.82)
    box(hg0, hg1, cc - half - 0.08, cc + half + 0.08, ridge_z + 0.55, ridge_z + 0.72)


def _sign(b: MeshBuilder, p: LogDwellingParams, conf: float) -> None:
    """A signboard hanging from a bracket beside the front door.

    Wolf Point Tavern is the case: a painted sign of a wolf hung outside by about
    1833, and it is the single most distinctive documented thing about the building.
    Everything here except the fact of a hanging board is invention — the arm length,
    the board size, the two hangers — and none of it is a claim about the image, which
    is deliberately absent. See the module docstring.

    It hangs 1.7 m to one side of the front door, on whichever block carries that
    door, and clear of the eave. Two earlier placements failed on looking at them: at
    a fixed fraction of the overall width it landed on the frame extension rather than
    the tavern, and hung on a short arm it read as a placard nailed flat to the wall
    instead of a board swinging off a bracket. A tavern sign has to project — that is
    the whole function of one.
    """
    front = p.frame_addition and p.frame_addition_side == "front"
    if front:
        bx0, _, bx1, face = addition_extent(p)
        eave = p.addition_height_m
    else:
        bx0, _, bx1, face = core_extent(p)
        eave = p.wall_height_m
    x = min((bx0 + bx1) / 2.0 + 1.7, bx1 - 0.6)

    z = min(eave - 0.30, 2.55)
    arm, t = 1.15, 0.045
    bw, bh, bt = 0.88, 0.50, 0.05
    drop = 0.20
    yb = face + arm * 0.72          # the board hangs near the outer end of the arm

    # The arm out from the wall, with a strut under it. Kept slim: an earlier version
    # gave the strut a 0.66 m drop and made it two-thirds the width of the board, and
    # the bracket read as the object with a board attached rather than the other way
    # round. On a tavern the board is the point.
    b.add_box(x - t, face, z, x + t, face + arm, z + 2 * t, conf, M_SIGN,
              skip=("front",))
    _plate(b, x, t * 0.55,
           [(face + 0.02, z - 0.38), (face + 0.62, z), (face + 0.02, z)],
           conf, M_SIGN)
    for hx in (x - bw * 0.32, x + bw * 0.32):
        b.add_box(hx - 0.022, yb - 0.018, z - drop, hx + 0.022, yb + 0.018, z,
                  conf, M_SIGN, skip=("top", "bottom"))
    b.add_box(x - bw / 2, yb - bt / 2, z - drop - bh,
              x + bw / 2, yb + bt / 2, z - drop, conf, M_SIGN)


# --------------------------------------------------------- the pole sign (T-0072)

# THE WOLF, AS AN OUTLINE THIS MODULE OWNS. A canine in profile, facing along -u,
# in a unit box: u runs nose-to-tail, v runs paw-to-ear-tip, and the caller scales
# it onto the board. Counter-clockwise as read in (u, v), which is what `_device`
# needs to wind the front face outward.
#
# WHAT IT DOES AND DOES NOT CLAIM. It claims that a picture of a wolf was painted on
# the board — "He painted a picture of a wolf on it", chicagology_prefire273 — and
# nothing whatever about how Lieutenant Allen drew it. Nobody has seen that board
# since the 1830s. The outline is a plain standing-canine silhouette: ears up, brush
# tail low, no attitude, no snarl and no landscape, because every one of those would
# be a second invention on top of the first. Recorded in docs/LIBERTIES.md.
_WOLF_UV = (
    (0.020, 0.630),   # nose
    (0.050, 0.560), (0.140, 0.575), (0.200, 0.500),   # jaw, chin, throat
    (0.240, 0.390),                                   # chest
    (0.220, 0.200), (0.200, 0.020), (0.290, 0.020), (0.300, 0.220),  # foreleg
    (0.340, 0.340), (0.520, 0.310), (0.600, 0.280),   # belly
    (0.610, 0.020), (0.700, 0.020), (0.690, 0.240),   # hind leg
    (0.780, 0.340), (0.840, 0.400),                   # thigh, tail root
    (0.960, 0.330), (0.990, 0.440), (0.860, 0.520),   # the brush
    (0.800, 0.620), (0.620, 0.650), (0.460, 0.610),   # rump, back, withers
    (0.380, 0.690), (0.310, 0.750),                   # shoulder, neck
    (0.280, 0.870), (0.245, 0.990), (0.215, 0.855),   # rear ear
    (0.175, 0.965), (0.145, 0.830),                   # front ear
    (0.080, 0.730), (0.000, 0.665),                   # muzzle
)
# The outline's own proportion, so a board of any shape gets a wolf and not a
# stretched dog. Read off _WOLF_UV rather than written down twice.
_WOLF_ASPECT = ((max(u for u, _ in _WOLF_UV) - min(u for u, _ in _WOLF_UV))
                / (max(v for _, v in _WOLF_UV) - min(v for _, v in _WOLF_UV)))


def _device(b: MeshBuilder, y: float, half: float, pts_xz, conf: float,
            mat: int) -> None:
    """A thin flat device lying in an x-z plane, extruded +-`half` in y.

    The y-facing twin of `_plate`, and separate from it rather than a generalisation
    of it: `_plate` takes its polygon in (y, z) because every brace in this module
    runs across the building, and a sign faces along it. `pts_xz` is counter-clockwise
    read in (x, z), which puts the front face's normal at -y and the back face's at
    +y; both are emitted, so the board reads painted from either side, which is what
    a sign hanging in the open is.
    """
    n = len(pts_xz)
    b.add_poly([(x, y - half, z) for x, z in pts_xz], conf, mat)
    b.add_poly([(x, y + half, z) for x, z in reversed(pts_xz)], conf, mat)
    for i in range(n):
        (xa, za), (xb, zb) = pts_xz[i], pts_xz[(i + 1) % n]
        b.add_poly([(xa, y + half, za), (xb, y + half, zb),
                    (xb, y - half, zb), (xa, y - half, za)], conf, mat)


def _sign_pole(b: MeshBuilder, p: LogDwellingParams, ridge_z: float,
               conf_pole: float, conf_board: float, conf_device: float) -> None:
    """A signboard flying from a cross-arm at the head of a sapling.

    THE ARRANGEMENT IS THE SOURCE'S, NOT THE ARCHETYPE'S. "The fort blacksmith made
    hinges, and the wolf sign was hung on a sapling" — chicagology's Wolf's Point
    note. A sapling is a young trunk set in the ground, so the board does not hang off
    the tavern at all: it stands beside it, and the 2026-08-18 owner brief's engraving
    of this building draws the pole mast-tall with a cross-arm at the head and the
    board flying from the arm, which the owner read as "almost like a flag". Three
    elements are therefore evidence — pole, hinges, board — and every DIMENSION below
    is invented within the bounds stated at the constants.

    IT CLEARS THE RIDGE ON PURPOSE. A sign wanted "to attract wayfarers" coming down
    the river bank has to be seen over the roof it belongs to, and a pole that stops
    at the eaves is a bracket with extra steps. `POLE_ABOVE_RIDGE_M` is what that
    costs, and the floor under it keeps a low cabin's pole from reading as a stake.

    IT STANDS IN FRONT AND SLIGHTLY OFF THE DOOR, on the facade side (+y, per the
    orientation note in the module docstring), clear of the eave and clear of the
    doorway a visitor walks through. Its butt is set below the wall line, not sitting
    on it: the pole is the only part of this archetype that leaves the footprint
    outline, so the ground under it is whatever the terrain does a metre out, and a
    set butt absorbs that instead of floating over it.
    """
    bx0, _, bx1, face = core_extent(p)
    xm = (bx0 + bx1) / 2.0
    px = min(xm + 1.85, bx1 - 0.55)
    py = face + POLE_STANDOFF_M

    top = max(ridge_z + POLE_ABOVE_RIDGE_M, POLE_MIN_TOP_M)
    mid = top * 0.56
    log_prism(b, (px, py, -POLE_SET_M), (px, py, mid), POLE_BUTT_R, conf_pole,
              M_LOG, sides=8)
    log_prism(b, (px, py, mid), (px, py, top), POLE_HEAD_R, conf_pole, M_LOG,
              sides=8)

    # The cross-arm, lashed across the head and running along the facade so the board
    # presents its face to the bank rather than its edge. A short tail behind the pole
    # so it reads as lashed across rather than socketed into it.
    arm_z = top - 0.30
    log_prism(b, (px - 0.20, py, arm_z), (px + POLE_ARM_M, py, arm_z),
              POLE_ARM_R, conf_pole, M_LOG, sides=6)

    bw, bh, bt = SIGN_BOARD
    cx = px + POLE_ARM_M * 0.62
    board_top = arm_z - POLE_ARM_R - SIGN_HANGER_DROP_M

    # The blacksmith's hinges, which are the one piece of ironwork the sources give
    # this building. Straps, not links: a hinge holds the board to the arm, and a
    # board on chain would swing edge-on in the wind and stop being a sign.
    for hx in (cx - bw * 0.34, cx + bw * 0.34):
        b.add_box(hx - 0.030, py - 0.014, board_top,
                  hx + 0.030, py + 0.014, arm_z + POLE_ARM_R * 0.4,
                  conf_pole, M_DARK)

    b.add_box(cx - bw / 2.0, py - bt / 2.0, board_top - bh,
              cx + bw / 2.0, py + bt / 2.0, board_top, conf_board, M_SIGN)

    if p.sign_device == "wolf":
        fw, fh = DEVICE_FRACTION
        dw = bw * fw
        dh = min(bh * fh, dw / _WOLF_ASPECT)
        dw = dh * _WOLF_ASPECT
        ox = cx - dw / 2.0
        oz = board_top - bh + (bh - dh) / 2.0
        pts = [(ox + u * dw, oz + v * dh) for u, v in _WOLF_UV]
        for side in (-1.0, 1.0):
            _device(b, py + side * (bt / 2.0 + DEVICE_PROUD_M / 2.0),
                    DEVICE_PROUD_M / 2.0, pts, conf_device, M_PAINT)
