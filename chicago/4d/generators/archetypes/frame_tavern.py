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

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from common import openings  # noqa: E402
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
# The stovepipe's slot follows the brick's when there is one and takes it when there is
# not, so a building drawing no pipe keeps exactly the material list it always had.

# Sheet iron, blacked — the stovepipe's (T-1778). The same weathered wrought-iron tone
# bridge_timber draws its hoist chains in, and like that one NOT ON THE MATERIAL SHEET:
# no source gives the finish of any 1835 Chicago stovepipe.
PIPE_RGBA = (0.118, 0.112, 0.104, 1.0)
PIPE_SIDE = 0.16            # a 6-in pipe, drawn square at this LOD

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
# T-2385: source-specific reconstructed contrast, never a shared stock retune.
# The actual native roof-only trial selected one quarter of the stock linear RGB;
# alpha, roughness, roof geometry and every unselected record remain unchanged.
ROOF_DEEP_BROWN_RGBA = tuple(c * 0.25 for c in materials.roof_finish("darkened").rgba[:3]) + (1.0,)

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
    lines = materials.course_lines(0.0, wall_z, params.siding_exposure_m,
                                   params.siding_lay_m, params.siding_seed)
    _clapboard(b, w, d, lines, c_clad)
    if params.elevation_scheme in ("gable_front", "corner_gable"):
        _clapboard_eaves(b, w, d, lines, c_clad)

    if params.elevation_scheme == "corner_gable":
        ridge_z = _corner_gable_roof(b, params, w, d, wall_z, c_roof)
    elif params.gable_wall_cladding:
        ridge_z = _wall_clad_gable_roof(
            b, params, w, d, wall_z, c_roof, ridge_along_x=(w >= d))
    else:
        ridge_z = b.add_gable_roof(0, 0, w, d, wall_z, params.roof_pitch_deg, c_roof,
                                   M_ROOF, ridge_along_x=(w >= d))

    # windows. "frontage": five bays upper, four plus a centred door below — the
    # arrangement both Sauganash depictions show. "gable_front": even bays along
    # the eaves elevations and doors on the gable faces — the arrangement plate
    # "11" draws for the Green Tree (T-0083). Fenestration is not separately
    # attested, so it inherits the record's scheme confidence at best.
    c_fen = params.conf("fenestration", "reconstructed")
    if params.elevation_scheme == "corner_gable":
        _fenestration_corner_gable(
            b, params, w, d, wall_z,
            max(c_fen, params.conf("elevation_scheme")))
        if params.gable_lunette:
            _corner_lunettes(b, params, w, d, wall_z)
        if params.gable_arch_text:
            _corner_arch_letters(b, params, d, wall_z)
        if params.flagstaff:
            _corner_roof_staff(b, params, w, d, ridge_z)
    elif params.elevation_scheme == "gable_front":
        _fenestration_gable_front(
            b, params, w, d, wall_z, ridge_z,
            max(c_fen, params.conf("elevation_scheme")))
    else:
        _fenestration(b, params, w, d, wall_z, c_fen)
        if params.end_windows:
            _end_windows(b, params, w, d, wall_z)
        if params.main_gable_cornice is not None:
            _main_gable_cornice(b, params, w, d, wall_z, ridge_z)

    if params.log_wing:
        _log_wing(b, params, d)
    if params.rear_ell:
        _rear_ell(b, params, w)
    if params.cross_wing:
        _cross_wing(b, params, w, d, wall_z, ridge_z)
    if params.enclosed_left_annex is not None:
        _enclosed_left_annex(b, params, w, d)

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
    m_pipe = M_BRICK + (1 if params.chimneys > 0 else 0)
    if params.stovepipes:
        _stovepipes(b, params, w, d, wall_z, m_pipe)

    if params.chimney_placement == "slope_offsets":
        _corner_slope_stacks(b, params, w, d, wall_z, m_ch)
    elif params.chimney_placement == "gable_ends":
        c_ch = params.worst_conf(*ch_attrs, "chimney_placement")
        inset = 0.6
        spots = ([(inset, d / 2), (w - inset, d / 2)] if w >= d
                 else [(w / 2, inset), (w / 2, d - inset)])
        half = 0.45
        if params.ridge_end_chimney_section_m is not None:
            half = params.ridge_end_chimney_section_m / 2
            c_ch = params.worst_conf(*ch_attrs, "chimney_placement",
                                     "ridge_end_chimney_section_m")
        head = params.ridge_end_chimney_head
        if head is not None:
            c_ch = params.worst_conf(*ch_attrs, "chimney_placement",
                                     "ridge_end_chimney_section_m", "ridge_end_chimney_head")
        for cx, cy in spots:
            if head is None:
                b.add_box(cx - half, cy - half, wall_z, cx + half, cy + half,
                          ridge_z + 0.55, c_ch, m_ch, skip=("bottom",))
            else:
                top = ridge_z + head["height_above_ridge_m"]
                cap_base = top - head["cap_height_m"]
                b.add_box(cx - half, cy - half, wall_z, cx + half, cy + half,
                          cap_base, c_ch, m_ch, skip=("bottom", "top"))
                cap_half = half + head["cap_overhang_m"]
                b.add_box(cx - cap_half, cy - cap_half, cap_base,
                          cx + cap_half, cy + cap_half, top, c_ch, m_ch)
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
    # The explicit reconstructed dark_brown option reuses stock solely for
    # monochrome contrast, without extending the watercolour's colour evidence.
    roof_rgba = (ROOF_DEEP_BROWN_RGBA if params.roof_colour == "deep_brown"
                 else ROOF_MOSS_RGBA if params.roof_colour == "moss_green"
                 else materials.roof_finish("darkened").rgba
                 if params.roof_colour == "dark_brown"
                 else materials.roof_finish(params.roof_condition).rgba)
    # A named roof can consciously choose an existing dark stock colour without
    # becoming infill or claiming a weathering history. The new colour's own
    # uncertainty reaches EVERY face using that material, including appendages.
    # Legacy/absent colours retain their exact previous confidence treatment.
    if params.roof_colour in ("dark_brown", "deep_brown"):
        c_colour = params.worst_conf("roof_colour")
        for face, material in zip(b.faces, b.mat_index):
            if material == M_ROOF:
                for vertex in face:
                    b.conf[vertex] = max(b.conf[vertex], c_colour)

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
    if params.stovepipes:
        mats.append(simple_material("stovepipe", PIPE_RGBA, roughness=0.62))
    return b.to_object(mats)


def _stovepipes(b: MeshBuilder, params: FrameTavernParams, w: float, d: float,
                wall_z: float, mat: int) -> None:
    """Sheet-iron pipes up through the main roof — one per stove the record counts.

    A boarding house heated its chambers with box stoves, and a stove's pipe went out
    through the roof wherever the stove stood rather than into a brick stack, which is
    why the pipes are scattered where the stacks are paired (T-1778; the crosswalk asks
    for "multiple stovepipes" and for the count to vary). The count is the record's.
    Where each stands — which slope, how far along, how high it rises — is this
    archetype's deal, made from the index alone so it is stable from bake to bake;
    docs/LIBERTIES.md owns it. The roof is the main block's own gable, whichever way
    its ridge runs (`add_gable_roof` puts it along the longer side).
    """
    c = params.conf("stovepipes", "reconstructed")
    n = params.stovepipes
    t = math.tan(math.radians(params.roof_pitch_deg))
    h = PIPE_SIDE / 2
    along_x = w >= d
    run, span = (w, d) if along_x else (d, w)
    for i in range(n):
        # spread along the ridge, nudged off the even spacing so the row does not
        # read as a fence, and alternating slopes a fifth of the span off the ridge
        a = run * (0.14 + 0.72 * (i + 0.5) / n + (0.035 if i % 2 else -0.035))
        s = span * (0.70 if i % 2 == 0 else 0.30)
        z_roof = wall_z + t * (span / 2 - abs(s - span / 2) + 0.25)
        rise = (0.85, 1.20, 1.00, 1.35, 0.95, 1.10)[i % 6]
        cx, cy = (a, s) if along_x else (s, a)
        b.add_box(cx - h, cy - h, z_roof - 0.30, cx + h, cy + h, z_roof + rise,
                  c, mat, skip=("bottom",))


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


def _clapboard(b: MeshBuilder, w: float, d: float, lines: list, conf: float) -> None:
    """Horizontal lap courses, modelled as a thin proud lip per course. `lines` are
    the lap heights `materials.course_lines` lays from the record's own mill stock
    (params.siding_exposure_m) and the fabric rule's lay (FIN-L, T-1962)."""
    lip = 0.018
    for z in lines:
        for y, ny in ((0.0, -lip), (d, d + lip)):
            b.add_poly([(0, y, z), (w, y, z), (w, ny, z - 0.02), (0, ny, z - 0.02)],
                       conf, M_WALL)


def _clapboard_eaves(b: MeshBuilder, w: float, d: float, lines: list,
                     conf: float) -> None:
    """Lap courses on the two x faces — the eaves elevations of a gable-front
    building, which are its long street walls and must read as clapboard."""
    lip = 0.018
    for z in lines:
        for x, nx in ((0.0, -lip), (w, w + lip)):
            b.add_poly([(x, 0, z), (x, d, z), (nx, d, z - 0.02), (nx, 0, z - 0.02)],
                       conf, M_WALL)


LIP_M = 0.018          # a clapboard course's lip: the skin the openings stand on


def _kit(b: MeshBuilder, params: FrameTavernParams, board: bool = False) -> openings.Mats:
    """The openings kit's materials (T-2278). This archetype carried no trim slot —
    its windows were bare glass quads 6 cm proud of the wall — so the casing and sash
    take a named `trim`, the wall's colour lifted the way the sheet lifts every
    frame building's trim. The leaf is dealt a paint, or weathered board for a yard
    or cabin door."""
    finish = materials.wall_finish(params.paint, params.finish_key)
    trim = b.named_mat("trim", materials.trim_rgba(finish), 0.85)
    rgba, rough = openings.WEATHERED_BOARD if board else openings.door_paint(b.name, True)
    key = "board_door" if board else "door"
    return openings.Mats(
        casing=trim, sash=trim, glass=M_GLASS,
        door=b.named_mat(key, rgba, rough),
        panel=b.named_mat(key + "_panel", openings.shade(rgba, 0.55 if board else 0.70),
                          rough),
        iron=b.named_mat("iron", *openings.STRAP_IRON))


def _win(b: MeshBuilder, params: FrameTavernParams, axis: str, plane: float,
         outward: int, u0: float, u1: float, z0: float, z1: float, conf: float,
         skin: float = LIP_M, rows: tuple | None = None) -> None:
    """A cased, silled and capped window with its sash set back over the town's glass.
    A tavern's sash is the Green Tree's: small lights, three across."""
    if rows is None:
        n = max(2, round((z1 - z0 - 0.13) / 0.26))
        rows = ((n + 1) // 2, n - (n + 1) // 2)
    openings.window(b, openings.Wall(axis, plane, outward, skin), u0, u1, z0, z1, conf,
                    _kit(b, params), 3, rows)


def _door(b: MeshBuilder, params: FrameTavernParams, axis: str, plane: float,
          outward: int, u0: float, u1: float, z0: float, z1: float, conf: float,
          kind: str = "front", skin: float = LIP_M) -> None:
    """A closed door: a panelled front door with its transom light, a board door for a
    kitchen or a cabin, a pair of board leaves for a carriage way."""
    w = openings.Wall(axis, plane, outward, skin)
    if kind == "front":
        openings.panelled_door(b, w, u0, u1, z0, z1, conf, _kit(b, params), panels=6)
    elif kind == "carriage":
        openings.batten_door(b, w, u0, u1, z0, z1, conf, _kit(b, params, board=True),
                             leaves=2, cap=True, casing_w=0.11)
    else:
        openings.batten_door(b, w, u0, u1, z0, z1, conf, _kit(b, params, board=True),
                             seed=f"{b.name}|{plane:.2f}|{u0:.2f}", cap=kind != "cabin")


def _corner_shutters(b: MeshBuilder, params: FrameTavernParams, axis: str,
                     plane: float, outward: int, u0: float, u1: float,
                     z0: float, z1: float) -> None:
    """Open leaves on either wall axis; every section/detail is reconstructed.

    Gifford supplies shutter occurrence, not its colour, thickness or joinery.
    Closed boxes keep a visible outward face on both positive/negative walls.
    Existing frontage shutters retain their original geometry below.
    """
    if not params.shutters:
        return
    conf = 1.0  # leaf sections/placement are reconstructed, even when occurrence is known
    leaf_w = (u1 - u0) * 0.42
    for side in (-1, 1):
        inner = (u0 if side < 0 else u1) + side * (openings.CASING_W_M + 0.01)
        outer = inner + side * leaf_w
        lo, hi = sorted((inner, outer))
        n0, n1 = sorted((plane + outward * (LIP_M + 0.010),
                         plane + outward * (LIP_M + 0.035)))
        if axis == "x":
            b.add_box(n0, lo, z0, n1, hi, z1, conf, M_SHUTTER)
        else:
            b.add_box(lo, n0, z0, hi, n1, z1, conf, M_SHUTTER)


def _fenestration_corner_gable(b: MeshBuilder, params: FrameTavernParams,
                              w: float, d: float, wall_z: float,
                              conf: float) -> None:
    """T-2385: three-bay short gables and five-bay long walls, any storey count.

    The pictured pair in Gifford's first Tremont has centred ground entrances
    and evenly spaced upper sashes. The unseen pair repeats them as an explicit
    reconstruction, not evidence for four historical doors. Opening sizes,
    equal stations and floor divisions are the kit's choices. Separate opt-in
    helpers supply raised landings, the arched gable feature and roof staff;
    neither this pattern nor those additions claims an image match.
    """
    story_h = wall_z / params.stories
    win_w, win_h = 0.85, 1.35
    faces = (("x", 0.0, -1, d, 3), ("x", w, 1, d, 3),
             ("y", 0.0, -1, w, 5), ("y", d, 1, w, 5))
    for axis, plane, outward, span, bays in faces:
        for story in range(params.stories):
            if params.first_story_height_m is None:
                base, height = story * story_h, story_h
            elif story == 0:
                base, height = 0.0, params.first_story_height_m
            else:
                height = (wall_z - params.first_story_height_m) / (params.stories - 1)
                base = params.first_story_height_m + (story - 1) * height
            z0 = base + height * 0.30
            for i in range(bays):
                centre = span * (i + 0.5) / bays
                if story == 0 and i == bays // 2:
                    _door(b, params, axis, plane, outward,
                          centre - 0.6, centre + 0.6, params.entry_raise_m,
                          params.entry_raise_m + 2.1, conf)
                    if params.corner_entry_surround:
                        _corner_entry_surround(b, params, axis, plane, outward,
                                               centre, params.entry_raise_m)
                    if params.entry_raise_m > 0:
                        _corner_landing(b, axis, plane, outward, centre,
                                        params.entry_raise_m)
                    continue
                u0, u1 = centre - win_w / 2, centre + win_w / 2
                _win(b, params, axis, plane, outward, u0, u1,
                     z0, z0 + win_h, conf)
                _corner_shutters(b, params, axis, plane, outward,
                                 u0, u1, z0, z0 + win_h)


def _corner_gable_roof(b: MeshBuilder, params: FrameTavernParams,
                       w: float, d: float, wall_z: float, conf: float) -> float:
    """Keep Tremont's existing wide-axis treatment byte-for-byte in geometry."""
    return _wall_clad_gable_roof(b, params, w, d, wall_z, conf,
                                ridge_along_x=True)


def _wall_clad_gable_roof(b: MeshBuilder, params: FrameTavernParams,
                         w: float, d: float, wall_z: float, conf: float,
                         ridge_along_x: bool) -> float:
    """Main roof planes unchanged; wall finish/course relief on end triangles.

    Pictured clapboard informs the opt-in, while course dimensions and unseen
    opposite triangles remain reconstructed. Subsidiary roofs are separate.
    """
    # Work in ridge/run coordinates, swapping only for a deep-axis ridge.
    if not ridge_along_x:
        w, d = d, w

    def poly(points, confidence, material):
        if not ridge_along_x:
            # Swapping x/y reverses handedness; reverse winding back outward.
            points = [(y, x, z) for x, y, z in reversed(points)]
        b.add_poly(points, confidence, material)

    x0,x1,y0,y1 = -ROOF_OVERHANG,w+ROOF_OVERHANG,-ROOF_OVERHANG,d+ROOF_OVERHANG
    mid = d/2
    ridge = wall_z + (d/2+ROOF_OVERHANG)*math.tan(math.radians(params.roof_pitch_deg))
    poly([(x0,y0,wall_z),(x1,y0,wall_z),(x1,mid,ridge),(x0,mid,ridge)],conf,M_ROOF)
    poly([(x1,y1,wall_z),(x0,y1,wall_z),(x0,mid,ridge),(x1,mid,ridge)],conf,M_ROOF)
    for x,outward in ((x0,-1),(x1,1)):
        pts=[(x,y0,wall_z),(x,mid,ridge),(x,y1,wall_z)]
        if outward>0: pts.reverse()
        poly(pts,1.0,M_WALL)
        lines=materials.course_lines(wall_z,ridge,params.siding_exposure_m,
                                     params.siding_lay_m,params.siding_seed)
        for z in lines:
            if z-wall_z<0.02 or z>=ridge: continue
            half=(d/2+ROOF_OVERHANG)*(ridge-z)/(ridge-wall_z)
            lower=(d/2+ROOF_OVERHANG)*(ridge-(z-0.02))/(ridge-wall_z)
            pts=[(x,mid-half,z),(x,mid+half,z),
                 (x+outward*0.018,mid+lower,z-0.02),
                 (x+outward*0.018,mid-lower,z-0.02)]
            if outward>0: pts.reverse()
            poly(pts,1.0,M_WALL)
    return ridge


def _face(b: MeshBuilder, pts, outward, conf: float, mat: int = M_WALL) -> None:
    """One planar face wound so its normal runs with `outward`.

    The cornice below is written in plain (x, y, z) at either gable end, so the
    handedness of its quads flips with the end. Deciding the winding from the
    geometry rather than from a sign the caller remembers to pass is what keeps
    a mirrored copy from coming out inside-out.
    """
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts[0], pts[1], pts[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    if sum(a * b_ for a, b_ in zip(n, outward)) < 0:
        pts = list(reversed(pts))
    b.add_poly(pts, conf, mat)


def _main_gable_cornice(b: MeshBuilder, params: FrameTavernParams, w: float,
                        d: float, wall_z: float, ridge_z: float) -> None:
    """A boxed rake cornice with short horizontal returns on ONE gable end.

    THE PICTURE SHOWS THE ELEMENT; THE PICTURE DOES NOT GIVE ITS SIZE. The
    Andreas/Braunhold plate of the Sauganash draws a boxed band following both
    rakes of the visible gable and a short horizontal return turning the corner
    at each eaves end — a thing the archetype has never built, so the gable has
    been standing with a bare rake the plate does not draw. What the plate
    cannot give is a dimension: it is a retrospective engraving and its own
    scale datum is a standing man, so the three sections here are the record's
    and are RECONSTRUCTED. docs/LIBERTIES.md L-sauganash-main-gable-cornice-2383
    states what bounded them.

    The band is drawn in the wall's own finish, which is what the plate shows:
    a painted boxed cornice, not a shingled one. It hangs UNDER the rake line
    rather than raising it, so the roof planes, the ridge, the eave and the
    silhouette of every other mass are untouched — a building that does not
    select this control comes out byte-for-byte as it did.

    Geometry, at the selected end's roof plane (the gable triangle's own plane,
    one eave overhang proud of the wall):

      - two rake prisms, from each eaves corner up to the apex, their top in
        the rake plane and their soffit `section_m` below it, standing
        `projection_m` proud of the gable;
      - two returns, `return_m` long, running inward from each eaves corner at
        the eave line, closing the assembly with their own end faces.

    The rakes and the returns interpenetrate at the corners, which is the
    mitre a cornice is actually built with; neither floats and neither opens a
    hole. The face against the gable is left off — it is coincident with the
    gable triangle, so drawing it would only z-fight.
    """
    g = params.main_gable_cornice
    section = float(g["section_m"])
    projection = float(g["projection_m"])
    run = float(g["return_m"])

    y0, y1 = -ROOF_OVERHANG, d + ROOF_OVERHANG
    mid = d / 2.0
    outward = 1 if g["end"] == "+x" else -1
    plane = (w + ROOF_OVERHANG) if outward > 0 else -ROOF_OVERHANG
    face = plane + outward * projection
    out_x = (float(outward), 0.0, 0.0)

    # Every section is a working choice, so the whole assembly is painted at
    # the reconstructed tier — 1.0 in _CONFIDENCE, the same value the wall-clad
    # gable triangles take.
    conf = 1.0

    for eave_y in (y0, y1):
        # top (in the rake plane), soffit, and the fascia that faces the street
        _face(b, [(plane, eave_y, wall_z), (face, eave_y, wall_z),
                  (face, mid, ridge_z), (plane, mid, ridge_z)],
              (0.0, 0.0, 1.0), conf)
        _face(b, [(plane, eave_y, wall_z - section), (face, eave_y, wall_z - section),
                  (face, mid, ridge_z - section), (plane, mid, ridge_z - section)],
              (0.0, 0.0, -1.0), conf)
        _face(b, [(face, eave_y, wall_z), (face, eave_y, wall_z - section),
                  (face, mid, ridge_z - section), (face, mid, ridge_z)],
              out_x, conf)

    for eave_y, inward in ((y0, 1.0), (y1, -1.0)):
        stop = eave_y + inward * run
        lo, hi = wall_z - section, wall_z
        # five faces, not six: the one against the gable is coincident with the
        # gable triangle, so drawing it would only z-fight with it.
        _face(b, [(plane, eave_y, hi), (face, eave_y, hi),
                  (face, stop, hi), (plane, stop, hi)], (0.0, 0.0, 1.0), conf)
        _face(b, [(plane, eave_y, lo), (face, eave_y, lo),
                  (face, stop, lo), (plane, stop, lo)], (0.0, 0.0, -1.0), conf)
        _face(b, [(face, eave_y, lo), (face, eave_y, hi),
                  (face, stop, hi), (face, stop, lo)], out_x, conf)
        for y, away in ((eave_y, -inward), (stop, inward)):
            _face(b, [(plane, y, lo), (face, y, lo), (face, y, hi), (plane, y, hi)],
                  (0.0, away, 0.0), conf)


def _corner_wall_box(b: MeshBuilder, axis: str, plane: float, outward: int,
                     u0: float, u1: float, n0: float, n1: float,
                     z0: float, z1: float, mat: int = M_WALL) -> None:
    """A solid box outside either wall normal; sections are reconstructed."""
    lo, hi = sorted((plane + outward * n0, plane + outward * n1))
    if axis == "x":
        b.add_box(lo, u0, z0, hi, u1, z1, 1.0, mat)
    else:
        b.add_box(u0, lo, z0, u1, hi, z1, 1.0, mat)


def _corner_entry_surround(b: MeshBuilder, params: FrameTavernParams,
                           axis: str, plane: float, outward: int,
                           centre: float, raised: float) -> None:
    """Plain broad jamb/header outline; stock and hidden repeats reconstructed.

    Gifford shows an outlined entry, not a measured order of columns. Keep the
    existing door opening/leaf and add neither a pediment nor decorative text.
    """
    trim = _kit(b, params).casing
    half, stock, top = 0.60, 0.14, raised + 2.10
    for side in (-1, 1):
        lo, hi = sorted((centre + side*half, centre + side*(half+stock)))
        _corner_wall_box(b, axis, plane, outward, lo, hi,
                         LIP_M+0.035, LIP_M+0.10, raised, top, trim)
    _corner_wall_box(b, axis, plane, outward, centre-half-stock,
                     centre+half+stock, LIP_M+0.035, LIP_M+0.10,
                     top, top+stock, trim)


def _corner_landing(b: MeshBuilder, axis: str, plane: float, outward: int,
                    centre: float, rise: float) -> None:
    """Raised plank platform, four-step working profile and simple side guards.

    Only occurrence is pictured. Width/depth, risers, stock and the mirrored
    unseen entries are reconstruction. Projections do not enlarge footprint.
    """
    wide, deep = 2.2, 1.2
    lo, hi = centre - wide / 2, centre + wide / 2
    _corner_wall_box(b, axis, plane, outward, lo, hi, 0.025, deep,
                     rise - 0.08, rise)
    for u in (lo + 0.08, hi - 0.08):
        _corner_wall_box(b, axis, plane, outward, u - 0.045, u + 0.045,
                         deep - 0.14, deep - 0.05, 0.0, rise - 0.08)
    count = max(1, math.ceil(rise / 0.18))
    for step in range(1, count + 1):
        top = rise * step / count
        near = deep + (count - step) * 0.28
        _corner_wall_box(b, axis, plane, outward, centre - 0.70, centre + 0.70,
                         near, near + 0.28, 0.0, top)
    for u in (lo + 0.06, hi - 0.06):
        for n in (0.08, deep - 0.08):
            _corner_wall_box(b, axis, plane, outward, u - 0.035, u + 0.035,
                             n - 0.035, n + 0.035, rise, rise + 0.85)
        for z in (rise + 0.40, rise + 0.80):
            _corner_wall_box(b, axis, plane, outward, u - 0.025, u + 0.025,
                             0.08, deep - 0.08, z, z + 0.045)


def _corner_lunettes(b: MeshBuilder, params: FrameTavernParams,
                     w: float, d: float, wall_z: float) -> None:
    """Shallow arched gable feature; glazing/radial bars are reconstruction.

    Gifford's dark arch is clear but its fine lettering/pane interpretation
    is not. Draw the visible arched outline without claiming a legible sign.
    """
    opaque = params.gable_arch_treatment == "opaque_panel"
    # Matte warm charcoal is a reconstructed tonal choice, not an original
    # pigment identification from the monochrome reproduction.
    field_mat = (b.named_mat("gable_panel", (0.11, 0.10, 0.09, 1.0), 0.95)
                 if opaque else M_GLASS)
    half, rise, base = d * 0.20, 0.74, wall_z + 0.55
    rim, samples = 0.09, 16
    for plane, outward in ((-ROOF_OVERHANG, -1), (w + ROOF_OVERHANG, 1)):
        def point(u, z, off=0.025):
            return (plane + outward * off, u, z)
        def face(pts, mat):
            a,c,e=pts[:3]
            normal=(c[1]-a[1])*(e[2]-a[2])-(c[2]-a[2])*(e[1]-a[1])
            if normal*outward<0: pts.reverse()
            b.add_poly(pts,1.0,mat)
        mid = d / 2
        outer = [(mid + half * math.cos(math.pi * i / samples),
                  base + rise * math.sin(math.pi * i / samples))
                 for i in range(samples + 1)]
        inner = [(mid + (half-rim) * math.cos(math.pi * i / samples),
                  base + rim + (rise-2*rim) * math.sin(math.pi * i / samples))
                 for i in range(samples + 1)]
        # Opening field as triangles, front/back facing handled explicitly.
        for i in range(samples):
            pts = [point(mid, base + rim), point(*inner[i]), point(*inner[i+1])]
            face(pts,field_mat)
            pts = [point(*outer[i],off=0.045), point(*outer[i+1],off=0.045),
                   point(*inner[i+1],off=0.045), point(*inner[i],off=0.045)]
            face(pts,M_WALL)
        _corner_wall_box(b, "x", plane, outward, mid-half, mid+half,
                         0.025, 0.070, base-0.06, base+rim)
        # Preserve the old fanlight only by default. The opaque-panel opt-in
        # removes unsupported glazing bars; source lettering remains unresolved.
        for angle in (() if opaque else (math.pi/4, math.pi/2, 3*math.pi/4)):
            u, z = mid + (half-rim) * math.cos(angle), base+rim+(rise-2*rim)*math.sin(angle)
            du, dz = u-mid, z-(base+rim); length = math.hypot(du,dz)
            nx, nz = -dz/length*0.018, du/length*0.018
            pts=[point(mid+nx,base+rim+nz,0.055),point(u+nx,z+nz,0.055),
                 point(u-nx,z-nz,0.055),point(mid-nx,base+rim-nz,0.055)]
            face(pts,M_WALL)



# The six needed stroke-capital shapes are copied from this project's existing
# prairie_draft.GLYPHS (T-2399), adapted to MeshBuilder. No font/source pixels.
_ARCH_NAME_GLYPHS = {'T': ([(0, 6, 4, 6), (2, 6, 2, 0)], 5.6), 'R': ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3), (1.5, 3, 4, 0)], 5.6), 'E': ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (0, 3, 3, 3)], 5.6), 'M': ([(0, 0, 0, 6), (0, 6, 2.5, 3), (2.5, 3, 5, 6), (5, 6, 5, 0)], 6.6), 'O': ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0)], 5.6), 'N': ([(0, 0, 0, 6), (0, 6, 4, 0), (4, 0, 4, 6)], 5.6)}


def _corner_arch_letters(b: MeshBuilder, params: FrameTavernParams,
                         d: float, wall_z: float) -> None:
    """Known house-name reconstruction on the pictured x_min opaque panel only.

    Gifford's native inscription is unresolved. These are invented light paint
    strokes with reconstructed confidence, not an attested glyph transcription.
    """
    if not params.gable_arch_text:
        return
    quads, cursor = [], 0.0
    for char in params.gable_arch_text:
        strokes, advance = _ARCH_NAME_GLYPHS[char]
        for x0, y0, x1, y1 in strokes:
            ax, ay = cursor + x0 + .45, y0 + .45
            bx, by = cursor + x1 + .45, y1 + .45
            length = math.hypot(bx-ax, by-ay)
            dx, dy = (bx-ax)/length, (by-ay)/length
            ax, ay, bx, by = ax-dx*.45, ay-dy*.45, bx+dx*.45, by+dy*.45
            px, py = -dy*.45, dx*.45
            quads.append([(ax-px,ay-py),(bx-px,by-py),(bx+px,by+py),(ax+px,ay+py)])
        cursor += advance
    xs=[p[0] for q in quads for p in q];ys=[p[1] for q in quads for p in q]
    xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys)
    width=d*(2.68/9.14)
    mat=b.named_mat("gable_letter_paint",(.65,.62,.55,1.0),.95)
    for quad in quads:
        # Five millimetres in front of the existing .025m opaque field plane.
        pts=[(-ROOF_OVERHANG-.030,
              d/2+width/2-(x-xmin)/(xmax-xmin)*width,
              wall_z+.65+(y-ymin)/(ymax-ymin)*.32) for x,y in quad]
        # All strokes face x_min; every new vertex stays reconstructed.
        a,c,e=pts[:3]
        nx=(c[1]-a[1])*(e[2]-a[2])-(c[2]-a[2])*(e[1]-a[1])
        if nx>0:pts.reverse()
        b.add_poly(pts,1.0,mat)


def _corner_slope_stacks(b: MeshBuilder, params: FrameTavernParams,
                         w: float, d: float, wall_z: float, mat: int) -> None:
    """Four offset stacks read as occurrences, with reconstructed plan/stature.

    A provisional picture camera bounds these fractional positions; no source
    supplies metres or hidden roof penetrations. Keep old ridge layouts intact.
    """
    stations = ((0.04,0.86,1.75), (0.23,0.40,0.60),
                (0.525,0.23,1.00), (0.82,0.08,1.20))
    t = math.tan(math.radians(params.roof_pitch_deg))
    for fu,fv,rise in stations:
        u,v = w*fu,d*fv
        roof = wall_z + (min(v,d-v)+ROOF_OVERHANG)*t
        b.add_box(u-0.225,v-0.25,roof-0.30,u+0.225,v+0.25,roof+rise,
                  1.0,mat,skip=("bottom",))
        b.add_box(u-0.275,v-0.30,roof+rise,u+0.275,v+0.30,roof+rise+0.075,
                  1.0,mat,skip=("bottom",))


def _corner_roof_staff(b: MeshBuilder, params: FrameTavernParams,
                       w: float, d: float, ridge_z: float) -> None:
    """The pictured roof spar only; cloth belongs to the app's flag layer.

    flags.js currently anchors at a standalone staff's whole-mesh bounds.
    It needs an explicit roof-staff anchor before this hotel may fly its cloth;
    do not turn on form.flag on the hotel and hang it at the wrong point.
    """
    u,v = w*0.37,d/2
    b.add_box(u-0.035,v-0.035,ridge_z-0.15,
              u+0.035,v+0.035,ridge_z+params.flagstaff_height_m,1.0,M_WALL)


def _fenestration_gable_front(b: MeshBuilder, params: FrameTavernParams, w: float,
                              d: float, wall_z: float, ridge_z: float,
                              conf: float) -> None:
    """The gable-front dress, read off plate "11" of the 2026-08-11 reference set
    (data/sources/assets/prefire_views_kevin_2026_08/p6_0.png, T-0083): even
    sash bays along both eaves elevations, the front gable carrying a centred
    door with flanking windows, and a small attic light in each gable peak —
    the one John Gray attests. The default bay count is the archetype's
    footprint arithmetic; a sparse eaves_bays override changes only the pictured
    face named by the record (T-2376). Unnamed faces keep their existing layout.

    Windows are recesses rather than holes, same as _fenestration; the scheme
    draws no shutters (validate refuses the combination rather than guessing).
    """
    story_h = wall_z / max(params.stories, 1)
    win_w, win_h, depth = 0.85, 1.35, 0.06

    # ---- even bays along the two eaves elevations (the x faces) ----------- #
    default_bays = max(3, min(7, round(d / 2.2)))
    for face, x_wall, sgn in (("x_min", 0.0, -1.0), ("x_max", w, 1.0)):
        bays = params.eaves_bays.get(face, default_bays)
        side_conf = max(conf, params.conf("eaves_bays")) if face in params.eaves_bays else conf
        for story in range(params.stories):
            z0 = story * story_h + story_h * 0.30
            for i in range(bays):
                cy = d * (i + 0.5) / bays
                # the attested second entrance, about the middle of the eaves
                # elevation the record names — a door instead of that bay
                if story == 0 and face == params.side_entrance_face and i == bays // 2:
                    _door(b, params, "x", x_wall, int(sgn), cy - 0.6, cy + 0.6, 0.0,
                          2.1, side_conf)
                    continue
                _win(b, params, "x", x_wall, int(sgn), cy - win_w / 2, cy + win_w / 2,
                     z0, z0 + win_h, side_conf)

    # ---- front gable: legacy centre door, optional ground-only layout ----- #
    layout = params.front_ground_layout
    door_cx, ground_sash_centres = params.resolved_front_ground_stations
    ground_conf = conf if layout is None else max(conf, params.conf("front_ground_layout"))
    _door(b, params, "y", d, 1, door_cx - 0.6, door_cx + 0.6, 0.0, 2.1, ground_conf)
    for story in range(params.stories):
        z0 = story * story_h + story_h * 0.30
        centres = params.resolved_front_upper_stations if story else ground_sash_centres
        upper_conf = conf if params.front_upper_layout is None else max(conf,params.conf("front_upper_layout"))
        window_conf = ground_conf if story == 0 else upper_conf
        for cx in centres:
            _win(b, params, "y", d, 1, cx - win_w / 2, cx + win_w / 2, z0, z0 + win_h,
                 window_conf)

    # ---- the rear gable ---------------------------------------------------- #
    # With a rear ell the storey windows would open into the ell's roof space;
    # the plate never shows this face, so the ell keeps the wall and only the
    # attic light above it is drawn.
    if not params.rear_ell:
        for story in range(params.stories):
            z0 = story * story_h + story_h * 0.30
            for cx in (w * 0.22, w * 0.78):
                _win(b, params, "y", 0.0, -1, cx - win_w / 2, cx + win_w / 2, z0,
                     z0 + win_h, conf)

    # ---- an attic light in each gable peak --------------------------------- #
    # John Gray: "There should also be a small attic window in the gable end,
    # for we used the attic, too." The gable triangles sit ROOF_OVERHANG proud
    # of the wall plane, so the lights sit just past them.
    aw, ah = 0.55, 0.65
    z0 = wall_z + 0.45
    for yy2, order in ((d + ROOF_OVERHANG, 1), (-ROOF_OVERHANG, -1)):
        _win(b, params, "y", yy2, order, w / 2 - aw / 2, w / 2 + aw / 2, z0, z0 + ah,
             conf, skin=0.0, rows=(2,))


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
    for z in materials.course_lines(0.0, wall_z, course, params.siding_lay_m,
                                    params.siding_seed):
        b.add_poly([(x1, -p, z), (x0, -p, z),
                    (x0, -p - lip, z - 0.02), (x1, -p - lip, z - 0.02)], c_clad, M_WALL)
        b.add_poly([(x0, 0, z), (x0, -p, z),
                    (x0 - lip, -p, z - 0.02), (x0 - lip, 0, z - 0.02)], c_clad, M_WALL)
        b.add_poly([(x1, -p, z), (x1, 0, z),
                    (x1 + lip, 0, z - 0.02), (x1 + lip, -p, z - 0.02)], c_clad, M_WALL)

    # its own gable, ridge along the deep axis. The span is d, so this returns the
    # main block's own ridge height and the two meet at the apex the plate draws.
    roof_end = 0.0
    if params.cross_wing_shared_ridge_join:
        # add_gable_roof pads the longitudinal end by ROOF_OVERHANG.
        # End its actual crest at the main roof's centre, not 0.25 m beyond it.
        # Walls and the unmeasured outer wing length stay exactly as selected.
        roof_end = d / 2 - ROOF_OVERHANG
        c_roof = params.worst_conf("cross_wing", "roof_type", "roof_pitch_deg",
                                   "cross_wing_shared_ridge_join")
    ridge_z = b.add_gable_roof(x0, -p, x1, roof_end, wall_z, params.roof_pitch_deg,
                               c_roof, M_ROOF, ridge_along_x=False)
    if abs(ridge_z - main_ridge_z) > 0.01:
        raise ValueError(
            f"the cross wing's ridge came out at {ridge_z:.3f} m against the main "
            f"block's {main_ridge_z:.3f} m — the shared apex the plate draws is the "
            f"whole reason this wing is built, and it has stopped being shared")

    # the far gable: two lights at first-floor level and one in the attic above
    cx = (x0 + x1) / 2
    for sgn in (-1.0, 1.0):
        gx = cx + sgn * d / 5.0
        _win(b, params, "y", -p, -1, gx - 0.45, gx + 0.45, 3.05, 4.45, c)
    _win(b, params, "y", -p - ROOF_OVERHANG, -1, cx - 0.40, cx + 0.40, ridge_z - 2.05,
         ridge_z - 1.15, c, skin=0.0, rows=(3,))


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
    for z in materials.course_lines(0.0, eh, course, params.siding_lay_m,
                                    params.siding_seed):
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

    # the wide carriage door, centred in the far gable — or, on a kitchen wing, the
    # back door the cook and the wood came in by (T-1778)
    half = 1.2 if params.rear_ell_door == "carriage" else 0.45
    top = 2.2 if params.rear_ell_door == "carriage" else 2.0
    _door(b, params, "y", -ed, -1, cxe - half, cxe + half, 0.0, top, c,
          kind="carriage" if params.rear_ell_door == "carriage" else "back")

    # one small light on each eaves wall
    cy = -ed / 2
    for x_wall, sgn in ((x0e, -1), (x1e, 1)):
        _win(b, params, "x", x_wall, sgn, cy - 0.35, cy + 0.35, 0.9, 1.9, c)


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
        # the boarding house's chamber rhythm, upstairs only (T-1778); the ground
        # floor keeps its five bays and its centred door
        bays = params.upper_windows if (story > 0 and params.upper_windows) else 5
        for i in range(bays):
            cx = w * (i + 0.5) / bays
            # Ground-floor centre bay is the entrance instead of a window. The
            # entrance is on the FACADE, which is the +y face in Blender and
            # therefore faces north once exported — bearing 0 per the contract.
            if story == 0 and i == bays // 2:
                if params.front_opening_details is not None:
                    _pictured_front_entrance(b, params, cx, d)
                else:
                    _door(b, params, "y", d, 1, cx - 0.6, cx + 0.6, 0.0, 2.1, conf)
                    if params.entrance_frontispiece:
                        _frontispiece(b, params, cx, d)
                continue
            for y, sgn in ((0.0, -1.0), (d, 1.0)):
                # Only the pictured lower facade opts in; rear and upper stock stay exact.
                sash = params.front_lower_sash if story == 0 and sgn > 0 else None
                sash_w = sash["width_m"] if sash else win_w
                sash_h = sash["height_m"] if sash else win_h
                sash_z = sash["sill_m"] if sash else z0
                sash_conf = params.conf("front_lower_sash", "reconstructed") if sash else conf
                _win(b, params, "y", y, int(sgn), cx - sash_w / 2, cx + sash_w / 2, sash_z,
                     sash_z + sash_h, sash_conf)
                if params.shutters:
                    for side in (-1, 1):
                        # hung on the casing's outer edge (T-2278)
                        x0 = cx + side * (sash_w / 2 + openings.CASING_W_M + 0.01)
                        x1 = x0 + side * (sash_w * 0.42)
                        yl = y + sgn * (depth * 0.4)
                        lo, hi = min(x0, x1), max(x0, x1)
                        a_, b_ = (lo, hi) if sgn < 0 else (hi, lo)
                        b.add_poly([(a_, yl, sash_z), (b_, yl, sash_z),
                                    (b_, yl, sash_z + sash_h), (a_, yl, sash_z + sash_h)],
                                   c_shut, M_SHUTTER)
                        if params.shutter_type == "louvred":
                            _louvres(b, params, lo, hi, yl, sgn, sash_z, sash_h)


def _end_windows(b: MeshBuilder, params: FrameTavernParams, w: float,
                 d: float, wall_z: float) -> None:
    """Only the record's sash on the main gables; no openings invented by default."""
    c = params.conf("end_windows", "reconstructed")
    for end, at, z, width, height in params.end_windows:
        out = 1 if end == "+x" else -1
        plane = w if out == 1 else 0.0
        bottom, top = z - height / 2, z + height / 2
        # add_gable_roof closes its triangle at the overhanging rake's plane.
        # A sash placed on the wall plane would disappear behind that triangle.
        attic = bottom >= wall_z
        if attic:
            plane += out * ROOF_OVERHANG
        uc = at * d
        _win(b, params, "x", plane, out, uc - width / 2, uc + width / 2,
             bottom, top, c, skin=0.0 if attic else LIP_M)



def _pictured_front_entrance(b: MeshBuilder, params: FrameTavernParams,
                            cx: float, d: float) -> None:
    """Andreas's broad high case, transom and side lights, front face only.

    This is a closed dark field in front of the existing wall, not a hole or a
    reconstructed hotel interior. Exact sections and light divisions are liberties.
    The default path never calls this or adds its one dark material.
    """
    g = params.front_opening_details
    c = params.conf("front_opening_details", "reconstructed")
    kit = _kit(b, params)
    wall = openings.Wall("y", d, 1, LIP_M)
    dark = b.named_mat("front_entrance_dark_recess", (.018, .017, .015, 1.), .97)
    outer = g["jamb_outer_width_m"] / 2
    inner = outer - .14
    leaf_top, transom_top = g["leaf_head_m"], g["transom_top_m"]
    openings.face(b, wall, LIP_M + .005, cx-inner, cx+inner,
                  .04, transom_top, c, dark)
    # Tall casing legs, with a broader shallow crown above the neighbouring sash.
    for side in (-1, 1):
        lo, hi = sorted((cx + side * inner, cx + side * outer))
        b.add_box(lo, d + .035, .0, hi, d + .15, transom_top,
                  c, kit.casing, skip=("bottom", "front"))
    half = g["case_width_m"] / 2
    crown = g["cornice_top_m"]
    b.add_box(cx-half+.05, d+.035, transom_top,
              cx+half-.05, d+.30, crown-.06, c, kit.casing, skip=("front",))
    b.add_box(cx-half, d+.025, crown-.06,
              cx+half, d+.36, crown, c, kit.casing, skip=("front",))
    # The narrow side lights flank a dark central leaf/aperture. A single
    # reconstructed mullion section separates them; no pane count is attested.
    leaf_half, light_w = g["leaf_width_m"] / 2, g["sidelights_each_width_m"]
    gap = (inner - leaf_half - light_w) / 2
    for side in (-1, 1):
        lo, hi = sorted((cx + side * leaf_half, cx + side * (leaf_half + .05)))
        openings.face(b, wall, LIP_M + .065, lo, hi, .055, leaf_top,
                      c, kit.casing)
    for side in (-1, 1):
        mid = cx + side * (leaf_half + gap + light_w / 2)
        openings.window(b, wall, mid-light_w/2, mid+light_w/2,
                        .45, leaf_top, c, kit, 1, (2, 1),
                        cap=False, casing_w=.045, head_w=.045)
    openings.transom_light(b, wall, cx-inner, cx+inner,
                           leaf_top, transom_top, c, kit)
    b.add_box(cx-outer, d+.02, .0, cx+outer, d+.28, .055,
              c, kit.casing, skip=("bottom", "front"))


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
        _door(b, params, "y", y0, 1, cxw - 0.5, cxw + 0.5, 0.0, 1.85, c_d, kind="cabin",
              skin=0.02)

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


def _enclosed_left_annex(b: MeshBuilder, p: FrameTavernParams, w: float, d: float) -> None:
    """Optional undated enclosed shoulder, low link and left gabled range.

    Pictured occurrence is inferred; every numeric layout/section and hidden face
    is reconstructed. An open shoulder leaves the independent yard bay visible;
    the closed reading never suppresses props or invents an alteration date.
    """
    g=p.enclosed_left_annex
    c=p.conf("enclosed_left_annex", "reconstructed")
    for part in p.left_annex_parts:
        if not part["occupied"]:
            continue
        name=part["id"];v=g[name]
        x0,x1,y0,front=part["x0"],part["x1"],part["back"],part["front"]
        h=v["wall_m"]
        first_vertex=len(b.verts)
        b.add_box(x0,y0,0,x1,front,h,c,M_WALL,skip=("bottom",))
        _annex_courses(b,p,x0,y0,x1,front,h,c)
        if name=="boarding_range":
            rear=v.get("rear_gable")
            if rear is None:
                _annex_gable_roof(b,p,x0,y0,x1,front,h,v["roof_pitch_deg"],c)
            else:
                # Two visible peaks: a low forward roof and the higher rear
                # gable Andreas and Kurz draw behind it. Same occupied envelope.
                join=y0+rear["depth_m"]
                _annex_gable_roof(b,p,x0,join,x1,front,h,v["roof_pitch_deg"],c)
                b.add_box(x0,y0,h,x1,join,rear["wall_m"],c,M_WALL,skip=("bottom",))
                _annex_courses(b,p,x0,y0,x1,join,rear["wall_m"],c,start_z=h)
                _annex_gable_roof(b,p,x0,y0,x1,join,rear["wall_m"],rear["roof_pitch_deg"],c)
        else:
            # Preserve the earlier connector direction unless its reconstructed
            # picture reading explicitly opts into falling away from the main block.
            z0,z1=((v["roof_high_m"],v["roof_low_m"]) if name=="shoulder"
                   else (v["roof_low_m"],v["roof_high_m"]))
            if name=="connector" and v.get("falls_away_from_main",False):
                z0,z1=z1,z0
            _annex_shed_roof(b,x0,y0,x1,front,h,z0,z1,c)
            if g.get("shed_infill_clapboard",False):
                _annex_infill_courses(b,p,x0,y0,x1,front,h,z0,z1,c)
        if name != "connector":
            f,z,ww,hh=v["front_window"];cx=x0+f*v["span_m"]
            _win(b,p,"y",front,+1,cx-ww/2,cx+ww/2,z,z+hh,c)
            f,z,ww,hh=v["front_gable_light"];cx=x0+f*v["span_m"]
            if name=="shoulder":
                # A small closed dormer proxy over this lower roof. Its unseen
                # depth and 250mm side cheeks remain reconstructed.
                a0,a1=cx-ww/2-.25,cx+ww/2+.25
                yf=front+ROOF_OVERHANG+.02;yb=yf-.9;head=z+hh+.15
                b.add_box(a0,yb,v["roof_low_m"],a1,yf,head,c,M_WALL,skip=("bottom",))
                pitch=math.degrees(math.atan((v["front_gable_peak_m"]-head)/((a1-a0+.1)/2)))
                _annex_gable_roof(b,p,a0,yb,a1,yf,head,pitch,c,overhang=.05)
                _win(b,p,"y",yf,+1,cx-ww/2,cx+ww/2,z,z+hh,c,skin=0.)
            else:
                _win(b,p,"y",front+ROOF_OVERHANG,+1,cx-ww/2,cx+ww/2,z,z+hh,c,skin=0.)
                f,ww,hh=v["front_door"];cx=x0+f*v["span_m"]
                _door(b,p,"y",front,+1,cx-ww/2,cx+ww/2,0.,hh,c,kind="back")
        if part["rotated"]:
            # A separate pictured gabled range need not share the main block's
            # heading. Turn the actual envelope, courses and openings together
            # about its connector-side rear corner, retaining the attachment.
            cs,sn=part["cos"],part["sin"]
            for i in range(first_vertex,len(b.verts)):
                px,py,pz=b.verts[i];dx,dy=px-x0,py-y0
                b.verts[i]=(x0+dx*cs-dy*sn,y0+dx*sn+dy*cs,pz)


def _annex_courses(b,p,x0,y0,x1,y1,wall_z,c,*,start_z=0.):
    """The existing frame stock and material, translated onto bounded annex walls."""
    lip=.018
    for z in materials.course_lines(start_z,wall_z,p.siding_exposure_m,p.siding_lay_m,p.siding_seed):
        for y,out in ((y0,-1),(y1,+1)):
            pts=[(x0,y,z),(x1,y,z),(x1,y+out*lip,z-.02),(x0,y+out*lip,z-.02)]
            b.add_poly(list(reversed(pts)) if out<0 else pts,c,M_WALL)
        for x,out in ((x0,-1),(x1,+1)):
            pts=[(x,y0,z),(x,y1,z),(x+out*lip,y1,z-.02),(x+out*lip,y0,z-.02)]
            b.add_poly(list(reversed(pts)) if out>0 else pts,c,M_WALL)


def _annex_infill_courses(b,p,x0,y0,x1,y1,wall_z,z0,z1,c):
    """Continue opted-in clapboard over the shed's trapezoid, clipped to its roof."""
    slope=(z1-z0)/(x1-x0);lip=.018
    for z in materials.course_lines(wall_z,max(z0,z1),p.siding_exposure_m,p.siding_lay_m,p.siding_seed):
        a,bx=x0,x1
        if abs(slope)>1e-12:
            cut=x0+(z-z0)/slope
            if slope>0:a=max(x0,cut)
            else:bx=min(x1,cut)
        if bx-a>1e-8:
            for y,out in ((y0,-1),(y1,+1)):
                pts=[(a,y,z),(bx,y,z),(bx,y+out*lip,z-.02),(a,y+out*lip,z-.02)]
                b.add_poly(list(reversed(pts)) if out<0 else pts,c,M_WALL)
        for x,out,top in ((x0,-1,z0),(x1,+1,z1)):
            if z<=top:
                pts=[(x,y0,z),(x,y1,z),(x+out*lip,y1,z-.02),(x+out*lip,y0,z-.02)]
                b.add_poly(list(reversed(pts)) if out>0 else pts,c,M_WALL)


def _annex_shed_roof(b,x0,y0,x1,y1,wall_z,z0,z1,c):
    """Closed shallow roof and upper wall infill, fixed +X slope topology."""
    slope=(z1-z0)/(x1-x0);o=ROOF_OVERHANG
    b.add_poly([(x0-o,y0-o,z0-o*slope),(x1+o,y0-o,z1+o*slope),
                (x1+o,y1+o,z1+o*slope),(x0-o,y1+o,z0-o*slope)],c,M_ROOF)
    b.add_poly([(x0,y0,wall_z),(x1,y0,wall_z),(x1,y0,z1),(x0,y0,z0)],c,M_WALL)
    b.add_poly([(x1,y1,wall_z),(x0,y1,wall_z),(x0,y1,z0),(x1,y1,z1)],c,M_WALL)
    b.add_poly([(x0,y1,wall_z),(x0,y0,wall_z),(x0,y0,z0),(x0,y1,z0)],c,M_WALL)
    b.add_poly([(x1,y0,wall_z),(x1,y1,wall_z),(x1,y1,z1),(x1,y0,z1)],c,M_WALL)


def _annex_gable_roof(b,p,x0,y0,x1,y1,eave,pitch,c,overhang=ROOF_OVERHANG):
    """Native roof envelope; end triangles use the existing framed wall material."""
    ridge=b.add_gable_roof(x0,y0,x1,y1,eave,pitch,c,M_ROOF,overhang=overhang,ridge_along_x=False)
    b.mat_index[-2:]=[M_WALL,M_WALL]
    # Same stock course rhythm, clipped to the two triangular wall faces.
    mid=(x0+x1)/2;half=(x1-x0+2*overhang)/2
    for z in materials.course_lines(eave,ridge,p.siding_exposure_m,p.siding_lay_m,p.siding_seed):
        zlow=max(eave,z-.02);a=half*(1-(zlow-eave)/(ridge-eave));q=half*(1-(z-eave)/(ridge-eave))
        for y,out in ((y0-overhang,-1),(y1+overhang,+1)):
            pts=[(mid-a,y,zlow),(mid+a,y,zlow),(mid+q,y+out*.018,z),(mid-q,y+out*.018,z)]
            b.add_poly(list(reversed(pts)) if out>0 else pts,c,M_WALL)
    return ridge
