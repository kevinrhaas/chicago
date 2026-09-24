"""frame_tavern — a two-storey frame tavern with an optional attached log wing.

The Sauganash is the reference case, and it is deliberately the first archetype
because it exercises the whole confidence model in one building: the white
two-storey block and its blue shutters are documented, the footprint and roof are
invented, and the attached log wing is inferred from two derivative images.

On construction: balloon framing was developed in Chicago in 1832-33 and became
the dominant local method, but the Sauganash frame block predates that by a year,
so `braced_frame` is the better reading. The geometry that follows is exterior
massing and cladding — the framing question changes stud rhythm behind the
sheathing, which is not modelled at this LOD. Recorded here so the next person
does not assume it was overlooked; see docs/RESEARCH/sauganash_hotel.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from common.mesh import (  # noqa: E402
    SHUTTER_RGBA, MeshBuilder, simple_material,
)
from archetypes.frame_tavern_params import FrameTavernParams  # noqa: E402

#: This archetype's roof COVERING, off the sheet's dealing rule (T-1487).
#: `materials.roof_substrate` holds the argument for why it is this one and
#: which half of it is graded by materials.md §2.2 and which half is L266.
_ROOF = materials.roof_substrate("frame_tavern")


# Materials are indices into the list passed to to_object(), in this order.
M_WALL, M_ROOF, M_LOG, M_SHUTTER, M_GLASS = 0, 1, 2, 3, 4
# Appended wherever the record counts a stack. It was appended only when a record
# STATED brick (chimney_material, T-0092) until T-0008 discharged R-W2a finding 1:
# every other tavern's stacks were taking M_ROOF and coming out painted their own
# roof's weathering condition. A tavern is a framed block and its stacks rise on the
# ridge line through the roof, so they are masonry on the same argument as the
# Sauganash's — see common/materials.py § the chimney stack. Still appended
# CONDITIONALLY, so a tavern with no stack keeps its exact five-material list.
M_BRICK = 5

# Colours the record can select beyond common.mesh's stock set. This block used to
# say they were local to this archetype ON PURPOSE — `common/` bytes are hashed into
# every archetype's mesh inputs, so a colour only frame taverns read did not belong
# in a file whose edit stales the whole town.
#
# T-0008 MOVED THE BRICK OUT ANYWAY, and the reason the trade-off flipped is worth
# stating rather than silently reversing. It is no longer a colour only frame taverns
# read: 112 framed buildings across three more archetypes now carry the same stack,
# so a copy per archetype is materials.md §2.3's own complaint made four times over
# — the shape T-0007 already refused for the hewn log. And the cost that argued for
# the copy is smaller than it was: Blender has been on the improve runner since
# 2026-08-19, so a `common/` edit is a two-and-a-half-minute rebuild of 245 masters
# in the same commit rather than a parcel that cannot go green. The value itself is
# UNCHANGED, so the Sauganash's masters come out byte-for-byte identical — which is
# the check that this was a move and not a repaint.
# T-0332: ASKED, not named. This stack rises inside the building and breaks the
# roof at the ridge, so the question the sheet answers is `chimney_finish
# ("interior")` — the disposition this archetype actually builds — and the row
# behind it can be renamed (it has been: `CHIMNEY_BRICK` is `BRICK` now) without
# this module knowing. materials.md §8.3 argued the shape; §10 applied it here.
BRICK = materials.chimney_finish("interior")
BRICK_RGBA = BRICK.rgba
ROOF_MOSS_RGBA = (0.20, 0.26, 0.17, 1.0)   # the Petford view's dark green/moss shingle

# The exposed face per course is `params.siding_exposure_m` — a record's own mill
# stock since T-0049, defaulting to 0.14 m (~5.5 in), which was a constant here.
CORNER_LOG_D = 0.22         # hewn log face
ROOF_OVERHANG = 0.25        # add_gable_roof's default; the gable triangles sit
                            # this far proud of the wall plane, so anything drawn
                            # ON a gable (the attic lights) must sit past it.


def build(params: FrameTavernParams, name: str):
    """Build the tavern. Returns a Blender object at the local origin, y-up handled
    by the exporter (Blender is z-up internally)."""
    params.validate()
    b = MeshBuilder(name)

    w, d = params.width_m, params.depth_m

    # Massing confidence describes the building's CHARACTER, not the precision of
    # its dimensions. Those are two different kinds of not-knowing, and folding
    # them together misrepresents the evidence.
    #
    # The Sauganash forced the distinction. Wau-Bun documents "a pretentious
    # white two-story building, with bright-blue wooden shutters" — we know what
    # this building WAS. What no source gives is a dimension. The first version
    # of this rule drove the massing off the footprint, so a conjectural size
    # dithered the entire building into ghost massing, which told a viewer we
    # knew nothing about a comparatively well-attested structure. That is a
    # misrepresentation in the direction of false modesty, and it is just as
    # wrong as overclaiming.
    #
    # So: the massing takes the confidence of the attributes that say what the
    # building was — its storey count, how it was built, what it was clad in.
    # Dimensional uncertainty is real and is carried honestly elsewhere: the
    # footprint keeps its own confidence in the sidecar, and the placement
    # carries uncertainty_m. Both surface in the popup.
    c_mass = params.worst_conf("stories", "construction", "cladding")
    c_roof = params.worst_conf("roof_type", "roof_pitch_deg")
    c_clad = params.worst_conf("cladding", "paint")

    wall_z = params.wall_height_m

    # main block — omit the bottom, it is never seen and costs two triangles per
    # building across the whole town
    b.add_box(0, 0, 0, w, d, wall_z, c_mass, M_WALL, skip=("bottom",))

    # clapboard courses as shallow relief. Cheap geometry, but it is what makes
    # a frame building read as frame rather than as a painted box at walking
    # distance. The original scheme laps only the two y faces — for a
    # frontage-scheme building those are the show elevations; the gable_front
    # scheme laps the eaves elevations too, because there the x faces ARE the
    # long street elevations and a bare one reads as a painted box (T-0083's
    # before frame shows exactly that).
    _clapboard(b, w, d, wall_z, c_clad, params.siding_exposure_m)
    if params.elevation_scheme == "gable_front":
        _clapboard_eaves(b, w, d, wall_z, c_clad, params.siding_exposure_m)

    ridge_z = b.add_gable_roof(0, 0, w, d, wall_z, params.roof_pitch_deg, c_roof,
                               M_ROOF, ridge_along_x=(w >= d))

    # windows. "frontage": five bays upper, four plus a centred door below — the
    # arrangement both Sauganash depictions show. "gable_front": even bays along
    # the eaves elevations and doors on the gable faces — the arrangement plate
    # "11" draws for the Green Tree (T-0083). Fenestration is not separately
    # attested, so it inherits the record's scheme confidence at best.
    c_fen = params.conf("fenestration", "reconstructed")
    if params.elevation_scheme == "gable_front":
        _fenestration_gable_front(
            b, params, w, d, wall_z, ridge_z,
            max(c_fen, params.conf("elevation_scheme")))
    else:
        _fenestration(b, params, w, d, wall_z, c_fen)

    if params.log_wing:
        _log_wing(b, params, d)
    if params.rear_ell:
        _rear_ell(b, params, w)
    if params.cross_wing:
        _cross_wing(b, params, w, d, wall_z, ridge_z)

    # chimneys — as many stacks as the record counts. "frontage" spaces them
    # across the frontage at the depth midline (the original arrangement, kept
    # exactly so no committed building moves); "gable_ends" stands one ON the
    # ridge line at each gable end, which is what plate "11" draws.
    #
    # EVERY stack here is brick since T-0008, not only the Sauganash's. A tavern is
    # a framed block and these stacks rise on the ridge line through the roof, which
    # is the argument common/materials.py § the chimney stack makes for the whole
    # framed town; before it, nine of these ten buildings were drawing their stacks
    # in the roof material. What `chimney_material` still does is CONFIDENCE: where
    # a record states the fabric (the Sauganash's brick, off the Petford view —
    # T-0092) that claim folds into the worst-of, and where it does not, the
    # attribute stays out of it, because an absent key reads as `reconstructed` and
    # would degrade every committed stack for a rule rather than for a claim.
    ch_attrs = ["chimneys"] + (["chimney_material"] if params.chimney_material else [])
    m_ch = M_BRICK if params.chimneys > 0 else M_ROOF
    if params.chimney_placement == "gable_ends":
        c_ch = params.worst_conf(*ch_attrs, "chimney_placement")
        inset = 0.6
        spots = ([(inset, d / 2), (w - inset, d / 2)] if w >= d
                 else [(w / 2, inset), (w / 2, d - inset)])
        for cx, cy in spots:
            b.add_box(cx - 0.45, cy - 0.45, wall_z, cx + 0.45, cy + 0.45,
                      ridge_z + 0.55, c_ch, m_ch, skip=("bottom",))
    else:
        c_ch = params.worst_conf(*ch_attrs) if len(ch_attrs) > 1 else params.conf("chimneys")
        for fx in _stack_fractions(params.chimneys):
            cx = w * fx
            b.add_box(cx - 0.45, d / 2 - 0.45, wall_z, cx + 0.45, d / 2 + 0.45,
                      ridge_z + 0.55, c_ch, m_ch, skip=("bottom",))

    # The roof keeps the archetype's weathered grey unless the record states a
    # colour — only the Petford watercolour is a coloured witness to any of
    # these roofs, and only the building it paints wears its tone (T-0092). Failing
    # that it takes the sheet's weathering CONDITION where the record deals one, and
    # the town's default tone where it does not; neither claims a covering.
    roof_rgba = (ROOF_MOSS_RGBA if params.roof_colour == "moss_green"
                 else materials.roof_finish(params.roof_condition).rgba)

    # The wall, off the sheet (T-0007). The Sauganash's `paint: white` is the one
    # ATTESTED paint in the whole dataset and it still wins here — what changes is
    # its gloss: the sheet gives lead paint 0.60, "the only smooth wall in Chicago,
    # and that is the point", against the 0.75 every tavern wall used to share with
    # every unpainted one.
    wall_finish = materials.wall_finish(params.paint, params.finish_key)
    wall_rgba, wall_rough = materials.resolve(
        materials.wall_substrate(cladding="clapboard"), wall_finish)

    mats = [
        simple_material("wall", wall_rgba, roughness=wall_rough),
        # A shingle field, named (T-1487). §2.2 grades it inferred for a framed
        # building; the roughness is `shingle`'s and is the 0.9 this always shipped.
        simple_material(materials.roof_material_name(_ROOF), roof_rgba,
                        roughness=_ROOF.roughness),
        # materials.md finding 2: this archetype was the last importer of the paler
        # of the project's two hewn-log values, which made the Sauganash's wing the
        # ONE log wall in Chicago built from a different timber than the other 52 —
        # in front of the station named after it. It now uses the town's log.
        simple_material("log", materials.HEWN_LOG.rgba,
                        roughness=materials.SUBSTRATES["hewn_log"].roughness),
        simple_material("shutter",
                        SHUTTER_RGBA.get(params.shutters or "", SHUTTER_RGBA["green"])),
        # The town's glazing, on the sheet since T-0126 (`GLASS`) at exactly the
        # value this archetype and frame_storefront already agreed on across all 48
        # shipped slots — brought onto the sheet rather than re-argued. The one
        # attested pane in the dataset is the Green Tree's 6x8 lights and the one
        # depicted sash is the Sauganash's, and both are this archetype's buildings.
        simple_material("glass", materials.GLASS.rgba,
                        roughness=materials.GLASS.roughness),
    ]
    if params.chimneys > 0:
        mats.append(simple_material("brick", BRICK_RGBA,
                                    roughness=BRICK.roughness))
    return b.to_object(mats)


def _stack_fractions(n: int) -> tuple[float, ...]:
    """Where n stacks stand, as fractions of the frontage.

    The pair sits at 0.22 and 0.78 — the positions this archetype has always used,
    read off the two retrospective depictions of the Sauganash, and kept exactly so
    that making the count a parameter does not quietly move the buildings that
    already had the number the record states. More than two spaces evenly between
    the same two ends; one goes to 0.22 rather than to the middle, because a single
    stack on a central-hall block stands at an end of the block and not in the hall.

    None of these positions is attested for any building in the dataset. The count
    is the record's and the arrangement is the archetype's; docs/LIBERTIES.md says so.
    """
    if n <= 0:
        return ()
    if n == 1:
        return (0.22,)
    step = (0.78 - 0.22) / (n - 1)
    return tuple(0.22 + i * step for i in range(n))


def _clapboard(b: MeshBuilder, w: float, d: float, wall_z: float, conf: float,
               course: float) -> None:
    """Horizontal lap courses, modelled as a thin proud lip per course. `course`
    is the record's own mill stock (params.siding_exposure_m)."""
    lip = 0.018
    n = int(wall_z / course)
    for i in range(1, n):
        z = i * course
        for y, ny in ((0.0, -lip), (d, d + lip)):
            b.add_poly([(0, y, z), (w, y, z), (w, ny, z - 0.02), (0, ny, z - 0.02)],
                       conf, M_WALL)


def _clapboard_eaves(b: MeshBuilder, w: float, d: float, wall_z: float,
                     conf: float, course: float) -> None:
    """Lap courses on the two x faces — the eaves elevations of a gable-front
    building, which are its long street walls and must read as clapboard."""
    lip = 0.018
    n = int(wall_z / course)
    for i in range(1, n):
        z = i * course
        for x, nx in ((0.0, -lip), (w, w + lip)):
            b.add_poly([(x, 0, z), (x, d, z), (nx, d, z - 0.02), (nx, 0, z - 0.02)],
                       conf, M_WALL)


def _fenestration_gable_front(b: MeshBuilder, params: FrameTavernParams, w: float,
                              d: float, wall_z: float, ridge_z: float,
                              conf: float) -> None:
    """The gable-front dress, read off plate "11" of the 2026-08-11 reference set
    (data/sources/assets/prefire_views_kevin_2026_08/p6_0.png, T-0083): even
    sash bays along both eaves elevations, the front gable carrying a centred
    door with flanking windows, and a small attic light in each gable peak —
    the one John Gray attests. The BAY COUNT is the archetype's arithmetic on
    the footprint, not a record's; docs/LIBERTIES.md L149 owns the arrangement.

    Windows are recesses rather than holes, same as _fenestration; the scheme
    draws no shutters (validate refuses the combination rather than guessing).
    """
    story_h = wall_z / max(params.stories, 1)
    win_w, win_h, depth = 0.85, 1.35, 0.06

    # ---- even bays along the two eaves elevations (the x faces) ----------- #
    bays = max(3, min(7, round(d / 2.2)))
    for face, x_wall, sgn in (("x_min", 0.0, -1.0), ("x_max", w, 1.0)):
        xx = x_wall + sgn * depth
        for story in range(params.stories):
            z0 = story * story_h + story_h * 0.30
            for i in range(bays):
                cy = d * (i + 0.5) / bays
                # the attested second entrance, about the middle of the eaves
                # elevation the record names — a door instead of that bay
                if story == 0 and face == params.side_entrance_face and i == bays // 2:
                    y0q, y1q = ((cy + 0.6, cy - 0.6) if sgn < 0
                                else (cy - 0.6, cy + 0.6))
                    b.add_poly([(xx, y0q, 0), (xx, y1q, 0),
                                (xx, y1q, 2.1), (xx, y0q, 2.1)], conf, M_GLASS)
                    continue
                y0q, y1q = ((cy + win_w / 2, cy - win_w / 2) if sgn < 0
                            else (cy - win_w / 2, cy + win_w / 2))
                b.add_poly([(xx, y0q, z0), (xx, y1q, z0),
                            (xx, y1q, z0 + win_h), (xx, y0q, z0 + win_h)],
                           conf, M_GLASS)

    # ---- the front gable: centred door, flanking bays ---------------------- #
    yy = d + depth
    b.add_poly([(w / 2 + 0.6, yy, 0), (w / 2 - 0.6, yy, 0),
                (w / 2 - 0.6, yy, 2.1), (w / 2 + 0.6, yy, 2.1)], conf, M_GLASS)
    for story in range(params.stories):
        z0 = story * story_h + story_h * 0.30
        for cx in (w * 0.22, w * 0.78):
            b.add_poly([(cx + win_w / 2, yy, z0), (cx - win_w / 2, yy, z0),
                        (cx - win_w / 2, yy, z0 + win_h),
                        (cx + win_w / 2, yy, z0 + win_h)], conf, M_GLASS)

    # ---- the rear gable ---------------------------------------------------- #
    # With a rear ell the storey windows would open into the ell's roof space;
    # the plate never shows this face, so the ell keeps the wall and only the
    # attic light above it is drawn.
    if not params.rear_ell:
        for story in range(params.stories):
            z0 = story * story_h + story_h * 0.30
            for cx in (w * 0.22, w * 0.78):
                b.add_poly([(cx - win_w / 2, -depth, z0), (cx + win_w / 2, -depth, z0),
                            (cx + win_w / 2, -depth, z0 + win_h),
                            (cx - win_w / 2, -depth, z0 + win_h)], conf, M_GLASS)

    # ---- an attic light in each gable peak --------------------------------- #
    # John Gray: "There should also be a small attic window in the gable end,
    # for we used the attic, too." The gable triangles sit ROOF_OVERHANG proud
    # of the wall plane, so the lights sit just past them.
    aw, ah = 0.55, 0.65
    z0 = wall_z + 0.45
    for yy2, order in ((d + ROOF_OVERHANG + 0.02, 1.0), (-ROOF_OVERHANG - 0.02, -1.0)):
        b.add_poly([(w / 2 + order * aw / 2, yy2, z0),
                    (w / 2 - order * aw / 2, yy2, z0),
                    (w / 2 - order * aw / 2, yy2, z0 + ah),
                    (w / 2 + order * aw / 2, yy2, z0 + ah)], conf, M_GLASS)


def _cross_wing(b: MeshBuilder, params: FrameTavernParams, w: float, d: float,
                wall_z: float, main_ridge_z: float) -> None:
    """The second two-storey mass — the Sauganash's rear wing, off one gable end,
    its ridge running BACK at right angles and meeting the main ridge at a shared
    apex.

    THE APEX IS WHY THIS FUNCTION TAKES NO SPAN. Braunhold's plate draws two lines
    out of one apex; `tools/sauganash_apex_lines.py` puts both of them at world
    horizontal (1.35 deg and 0.11 deg, against the 1.99 image slope a 38 deg rake
    would have been drawn at), so they are two RIDGES. Two gable ridges of one wall
    height and one pitch meet at a point only when they span the same width, so the
    wing's span is the main block's own depth and nothing here may choose it. What
    the plate cannot give is how far the wing runs back — one sheet gives no depth —
    and that single number is the record's, claimed at docs/LIBERTIES.md.

    Everything the wing is CLAD and PIERCED with is the archetype's: the same
    clapboard exposure as the block it grows out of, two lights in the far gable and
    one in the attic above them. No stack: T-0617 counted the stacks that clear the
    roof line and found two, both on the main block, and a third invented here would
    be this archetype adding a claim the plate was asked for and did not make.
    """
    c = params.worst_conf("cross_wing", "stories", "construction", "cladding")
    c_roof = params.worst_conf("cross_wing", "roof_type", "roof_pitch_deg")
    c_clad = params.worst_conf("cross_wing", "cladding", "paint")
    p = params.cross_wing_depth_m
    x0 = w - d if params.cross_wing_end == "x_max" else 0.0
    x1 = x0 + d

    # walls. y = 0 is the main block's own rear wall, so its face is skipped.
    b.add_box(x0, -p, 0, x1, 0, wall_z, c, M_WALL, skip=("bottom", "back"))

    # clapboard on the three exposed walls, the block's own stock
    course = params.siding_exposure_m
    lip = 0.018
    for i in range(1, int(wall_z / course)):
        z = i * course
        b.add_poly([(x1, -p, z), (x0, -p, z),
                    (x0, -p - lip, z - 0.02), (x1, -p - lip, z - 0.02)], c_clad, M_WALL)
        b.add_poly([(x0, 0, z), (x0, -p, z),
                    (x0 - lip, -p, z - 0.02), (x0 - lip, 0, z - 0.02)], c_clad, M_WALL)
        b.add_poly([(x1, -p, z), (x1, 0, z),
                    (x1 + lip, 0, z - 0.02), (x1 + lip, -p, z - 0.02)], c_clad, M_WALL)

    # its own gable, ridge along the deep axis. The span is d, so this returns the
    # main block's own ridge height and the two meet at the apex the plate draws.
    ridge_z = b.add_gable_roof(x0, -p, x1, 0, wall_z, params.roof_pitch_deg,
                               c_roof, M_ROOF, ridge_along_x=False)
    if abs(ridge_z - main_ridge_z) > 0.01:
        raise ValueError(
            f"the cross wing's ridge came out at {ridge_z:.3f} m against the main "
            f"block's {main_ridge_z:.3f} m — the shared apex the plate draws is the "
            f"whole reason this wing is built, and it has stopped being shared")

    # the far gable: two lights at first-floor level and one in the attic above
    cx = (x0 + x1) / 2
    yy = -p - 0.06
    for sgn in (-1.0, 1.0):
        gx = cx + sgn * d / 5.0
        b.add_poly([(gx - 0.45, yy, 3.05), (gx + 0.45, yy, 3.05),
                    (gx + 0.45, yy, 4.45), (gx - 0.45, yy, 4.45)], c, M_GLASS)
    yg = -p - ROOF_OVERHANG - 0.06
    b.add_poly([(cx - 0.40, yg, ridge_z - 2.05), (cx + 0.40, yg, ridge_z - 2.05),
                (cx + 0.40, yg, ridge_z - 1.15), (cx - 0.40, yg, ridge_z - 1.15)],
               c, M_GLASS)


def _rear_ell(b: MeshBuilder, params: FrameTavernParams, w: float) -> None:
    """The low gabled tail off the rear gable end — John Gray's one-storey
    addition, drawn to the two retrospective views: clapboard like the house,
    its own lower gable continuing the main axis, and a wide carriage door in
    the far gable opening to the yard where the wagons stand. Everything here
    is `reconstructed` and docs/LIBERTIES.md L149 owns the sizes.
    """
    c = params.conf("rear_ell", "reconstructed")
    ew, ed, eh = params.rear_ell_width_m, params.rear_ell_depth_m, params.rear_ell_wall_m
    x0e, x1e = (w - ew) / 2, (w + ew) / 2
    cxe = w / 2

    # walls — the y=0 plane is the main block's own rear wall, so skip "back"
    b.add_box(x0e, -ed, 0, x1e, 0, eh, c, M_WALL, skip=("bottom", "back"))

    # clapboard courses on the three exposed walls
    course = params.siding_exposure_m
    lip = 0.018
    for i in range(1, int(eh / course)):
        z = i * course
        b.add_poly([(x1e, -ed, z), (x0e, -ed, z),
                    (x0e, -ed - lip, z - 0.02), (x1e, -ed - lip, z - 0.02)],
                   c, M_WALL)
        b.add_poly([(x0e, 0, z), (x0e, -ed, z),
                    (x0e - lip, -ed, z - 0.02), (x0e - lip, 0, z - 0.02)],
                   c, M_WALL)
        b.add_poly([(x1e, -ed, z), (x1e, 0, z),
                    (x1e + lip, 0, z - 0.02), (x1e + lip, -ed, z - 0.02)],
                   c, M_WALL)

    # its own gable roof, ridge continuing the main axis at the lower eave.
    # The attachment-side triangle lands inside the main block and is unseen.
    b.add_gable_roof(x0e, -ed, x1e, 0, eh, 34.0, c, M_ROOF, ridge_along_x=False)

    # the wide carriage door, centred in the far gable
    yy = -ed - 0.06
    b.add_poly([(cxe - 1.2, yy, 0), (cxe + 1.2, yy, 0),
                (cxe + 1.2, yy, 2.2), (cxe - 1.2, yy, 2.2)], c, M_GLASS)

    # one small light on each eaves wall
    cy = -ed / 2
    for x_wall, sgn in ((x0e, -1.0), (x1e, 1.0)):
        xx = x_wall + sgn * 0.06
        y0q, y1q = (cy + 0.35, cy - 0.35) if sgn < 0 else (cy - 0.35, cy + 0.35)
        b.add_poly([(xx, y0q, 0.9), (xx, y1q, 0.9),
                    (xx, y1q, 1.9), (xx, y0q, 1.9)], c, M_GLASS)


def _fenestration(b: MeshBuilder, params: FrameTavernParams, w: float, d: float,
                  wall_z: float, conf: float) -> None:
    """Recessed window reveals plus shutters where attested.

    Windows are recesses rather than holes: at this LOD an opening would show the
    inside of the far wall, and interiors are out of scope.
    """
    story_h = wall_z / max(params.stories, 1)
    win_w, win_h, depth = 0.85, 1.35, 0.06
    c_shut = params.conf("shutters", "reconstructed")

    for story in range(params.stories):
        z0 = story * story_h + story_h * 0.30
        bays = 5
        for i in range(bays):
            cx = w * (i + 0.5) / bays
            # Ground-floor centre bay is the entrance instead of a window. The
            # entrance is on the FACADE, which is the +y face in Blender and
            # therefore faces north once exported — bearing 0 per the contract.
            if story == 0 and i == bays // 2:
                yy = d + depth
                b.add_poly([(cx + 0.6, yy, 0), (cx - 0.6, yy, 0),
                            (cx - 0.6, yy, 2.1), (cx + 0.6, yy, 2.1)],
                           conf, M_GLASS)
                if params.entrance_frontispiece:
                    _frontispiece(b, params, cx, d)
                continue
            for y, sgn in ((0.0, -1.0), (d, 1.0)):
                yy = y + sgn * depth
                # Wind by the elevation's outward normal. Using one point order
                # for both faces leaves the +y openings facing INTO the building;
                # that was invisible only because the exporter writes
                # doubleSided by default, which is not a guarantee to build on.
                x0q, x1q = ((cx - win_w / 2, cx + win_w / 2) if sgn < 0
                            else (cx + win_w / 2, cx - win_w / 2))
                b.add_poly([(x0q, yy, z0), (x1q, yy, z0),
                            (x1q, yy, z0 + win_h), (x0q, yy, z0 + win_h)],
                           conf, M_GLASS)
                if params.shutters:
                    for side in (-1, 1):
                        x0 = cx + side * (win_w / 2)
                        x1 = x0 + side * (win_w * 0.42)
                        yl = y + sgn * (depth * 0.4)
                        lo, hi = min(x0, x1), max(x0, x1)
                        a_, b_ = (lo, hi) if sgn < 0 else (hi, lo)
                        b.add_poly([(a_, yl, z0), (b_, yl, z0),
                                    (b_, yl, z0 + win_h), (a_, yl, z0 + win_h)],
                                   c_shut, M_SHUTTER)
                        if params.shutter_type == "louvred":
                            _louvres(b, params, lo, hi, yl, sgn, z0, win_h)


def _frontispiece(b: MeshBuilder, params: FrameTavernParams, cx: float,
                  d: float) -> None:
    """The small flat-hooded entrance surround on the facade's centred door —
    the Sauganash's, drawn by both street views of the 2026-08-18 owner brief
    (images 8 and 9; T-0092): a flat pilaster each side of the leaf and a
    shallow flat hood over it, all in the wall's own paint. The views give the
    FORM; every dimension here is the archetype's, and docs/LIBERTIES.md L154
    owns the invention. Carries the frontispiece attribute's own confidence,
    which is weaker than the attested paint it is drawn in.
    """
    c = params.conf("entrance_frontispiece")
    # flanking pilasters, just outside the 1.2 m door leaf
    for side in (-1, 1):
        x_in = cx + side * 0.62
        x_out = cx + side * 0.85
        b.add_box(min(x_in, x_out), d, 0, max(x_in, x_out), d + 0.09, 2.18,
                  c, M_WALL, skip=("bottom", "front"))
    # the flat hood: a shallow slab across the pilasters, and a thinner crown
    # proud of it — "small" and "flat" are the whole of what the views state
    b.add_box(cx - 0.95, d, 2.18, cx + 0.95, d + 0.42, 2.26, c, M_WALL,
              skip=("front",))
    b.add_box(cx - 1.02, d, 2.26, cx + 1.02, d + 0.47, 2.31, c, M_WALL,
              skip=("front",))


def _louvres(b: MeshBuilder, params: FrameTavernParams, lo: float, hi: float,
             yl: float, sgn: float, z0: float, win_h: float) -> None:
    """Slat relief on one shutter leaf — the louvred construction only the
    Trowbridge drawing resolves (image 10 of the 2026-08-18 owner brief, the
    weakest of the three views' claims; T-0092). The slats therefore carry the
    shutter_type attribute's own confidence, NOT the attested colour's: the
    leaf stays as documented and the louvres admit what they rest on. Slat
    count and pitch are the archetype's numbers (docs/LIBERTIES.md L154).
    """
    c = params.worst_conf("shutters", "shutter_type")
    n = 8
    x0s, x1s = lo + 0.025, hi - 0.025
    a_, b_ = (x0s, x1s) if sgn < 0 else (x1s, x0s)
    y_in = yl + sgn * 0.008     # slat's upper edge, near the leaf
    y_out = yl + sgn * 0.028    # lower edge, canted proud — a louvre sheds rain
    top, bot = z0 + win_h - 0.10, z0 + 0.10
    pitch = (top - bot) / (n - 1)
    for i in range(n):
        zt = top - i * pitch
        b.add_poly([(a_, y_out, zt - 0.09), (b_, y_out, zt - 0.09),
                    (b_, y_in, zt), (a_, y_in, zt)], c, M_SHUTTER)


def _log_wing(b: MeshBuilder, params: FrameTavernParams, main_d: float) -> None:
    """The 1829 log cabin surviving as an attached single-storey wing.

    Both surviving depictions (Braunhold's engraving in Andreas 1884 and Kurz &
    Allison panel 14, 1893) show it at the left front of the frame block, log
    courses and corner notching plainly drawn. They are not independent — the
    later composition follows the earlier — so this is `inferred`, and the wing
    carries that confidence rather than the main block's.
    """
    c = params.conf("log_wing", "reconstructed")
    ww, wd, wh = params.log_wing_width_m, params.log_wing_depth_m, params.log_wing_height_m

    # Projects forward from the facade, which is +y in Blender (north once
    # exported). y1 is the wall it abuts, y0 the far face.
    y1, y0 = main_d, main_d + wd
    b.add_box(0, y1, 0, ww, y0, wh, c, M_LOG, skip=("bottom", "front"))

    # individual log courses, so it reads as log and not as a stained box
    course = 0.30
    n = int(wh / course)
    for i in range(1, n):
        z = i * course
        b.add_poly([(ww, y0, z), (0, y0, z), (0, y0 + 0.015, z - 0.015),
                    (ww, y0 + 0.015, z - 0.015)], c, M_LOG)
        for x in (0.0, ww):
            sgn = -1 if x == 0.0 else 1
            b.add_poly([(x, y1, z), (x, y0, z), (x + sgn * 0.015, y0, z - 0.015),
                        (x + sgn * 0.015, y1, z - 0.015)], c, M_LOG)
        # protruding notched log ends at the corners
        for x in (0.0, ww):
            sgn = -1 if x == 0.0 else 1
            b.add_box(min(x, x + sgn * CORNER_LOG_D), y0, z - course * 0.5,
                      max(x, x + sgn * CORNER_LOG_D), y0 + CORNER_LOG_D,
                      z - course * 0.5 + 0.16, c, M_LOG)

    # lean-to roof, tight to the wing and sloping up to meet the frame block
    oh, rise, thk = 0.12, 0.5, 0.09
    yf, yb = y0 + oh, y1
    for dz in (0.0, -thk):                      # upper and lower faces
        b.add_poly([(-oh, yf, wh + dz), (ww + oh, yf, wh + dz),
                    (ww + oh, yb, wh + rise + dz), (-oh, yb, wh + rise + dz)], c, M_ROOF)
    # fascia along the eave, and closed rake edges — a roof with an edge reads as
    # a roof; a single plane reads as a floating slab
    b.add_poly([(-oh, yf, wh - thk), (ww + oh, yf, wh - thk),
                (ww + oh, yf, wh), (-oh, yf, wh)], c, M_ROOF)
    for x in (-oh, ww + oh):
        b.add_poly([(x, yf, wh - thk), (x, yf, wh),
                    (x, yb, wh + rise), (x, yb, wh + rise - thk)], c, M_ROOF)

    # The wing's own door, direct to grade in its street face — the 1829 cabin
    # kept its entrance when the frame block was built on (images 9 and 10 of
    # the 2026-08-18 owner brief; T-0092). A recess like every opening at this
    # LOD, centred on the wing; leaf size is the archetype's (L154). Carries
    # the door attribute's own confidence, not the wing's.
    if params.log_wing_door:
        c_d = params.conf("log_wing_door")
        cxw = ww / 2
        yd = y0 + 0.02
        b.add_poly([(cxw + 0.5, yd, 0), (cxw - 0.5, yd, 0),
                    (cxw - 0.5, yd, 1.85), (cxw + 0.5, yd, 1.85)], c_d, M_GLASS)

    # The shed-roofed porch hood over that door, on two slim posts to grade —
    # only the Braunhold engraving (image 9) draws it, and the geometry carries
    # that single-view claim's own confidence. Plank pitch, projection and the
    # posts are the archetype's numbers (L154).
    if params.log_wing_porch_hood:
        c_h = params.conf("log_wing_porch_hood")
        cxw = ww / 2
        hw, hp, thk2 = 0.85, 0.80, 0.055    # half-width, projection, plank
        zw, zo = 2.12, 1.90                 # z at the wall / at the outer eave
        x0h, x1h = cxw - hw, cxw + hw
        yo = y0 + hp
        for dz in (0.0, -thk2):             # upper and lower faces
            b.add_poly([(x0h, yo, zo + dz), (x1h, yo, zo + dz),
                        (x1h, y0, zw + dz), (x0h, y0, zw + dz)], c_h, M_ROOF)
        # fascia along the outer eave, closed rake edges — same rule as the
        # wing's own lean-to: a roof needs an edge or it reads as a slab
        b.add_poly([(x0h, yo, zo - thk2), (x1h, yo, zo - thk2),
                    (x1h, yo, zo), (x0h, yo, zo)], c_h, M_ROOF)
        for x in (x0h, x1h):
            b.add_poly([(x, yo, zo - thk2), (x, yo, zo),
                        (x, y0, zw), (x, y0, zw - thk2)], c_h, M_ROOF)
        # the posts: hewn stuff like the wing, standing on the ground the door
        # opens onto
        for x in (x0h + 0.06, x1h - 0.06):
            b.add_box(x - 0.045, yo - 0.135, 0, x + 0.045, yo - 0.045,
                      zo - thk2, c_h, M_LOG, skip=("bottom", "top"))
