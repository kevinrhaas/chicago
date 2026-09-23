"""frame_dwelling — a frame HOUSE: one to two storeys, a rear ell, a stoop.

The archetype the dataset has been missing. Until it existed every frame record had
to be a `frame_tavern` — a two-storey public house with a five-bay front — or a log
cabin, which is why the town so far is three taverns, three log buildings, a store and
a bridge, and not one dwelling. Chicago in July 1835 held about 3,265 people who had
arrived, most of them, within two years (`docs/research/03-structures-north.md` §0), and
almost all of them lived in something this file builds.

**What the evidence gives, and what it does not.** No source reached by this project
describes an ordinary Chicago dwelling of 1835 in elevation. What the dossiers do give
is a set of hard numbers about frame building here in exactly these years, and every
default in `frame_dwelling_params` is built from them rather than from a generic
American frame house:

- **7 1/2 ft ceilings** — the Green Tree's, which its own source calls "rather low for
  a hotel ceiling" (`chicagology_prefire127`, John Gray and Edwin O. Gale). A house was
  not built taller than the hotel, so the storey heights here start there.
- **12 x 12 ft rooms and 6 x 8 in window panes** — the same page, Gale on a guest
  chamber "about 12x12, with two windows 6x8". That pane size is why the windows here
  are small and nearly square-headed rather than tall Federal sash.
- **"a small attic window in the gable end, for we used the attic, too"** — Gray again,
  and the reason the half storey in this archetype is lit from the gables and not from
  dormers. P. F. W. Peck's store on South Water, whose "unfinished loft" Rev. Jeremiah
  Porter lodged in in 1833 (`andreas_1884_v1`, scan p. 627), is the same half storey in
  the same use.
- **"a low one-story addition to the right, the same as on the left"** — Gray on the
  Green Tree, the dataset's one direct attestation of the low subordinate wing this
  archetype builds as the ell.
- **25 x 35 ft, balloon-framed, 1833** — St Mary's church, Augustine D. Taylor
  (`andreas_1884_v1` scan pp. 281, 601): the size of a substantial frame building here
  and the first balloon frame anyone names.
- **Plain.** The First Presbyterian church of 1834 is "plain frame", $600, pine-board
  benches and bare puncheon floors (`andreas_1884_v1` scan p. 623). The first Greek
  Revival house in Chicago is the Clarke House of **1836**, which `data/exclusions.json`
  keeps out of this scene by date. Nothing here builds an entablature, a corner
  pilaster or a portico, and the default front is deliberately irregular.

**Orientation.** The facade faces NORTH at rotation_deg 0, per the pinned convention in
docs/GLB-CONTRACT.md. In Blender that is the +y face, because the exporter's
`export_yup=True` maps Blender +Y to glTF -Z, which the contract defines as north. The
door, the porch and the front windows are all on +y and the ell runs back toward -y.
Getting this wrong is a silent error — the house looks fine and faces the wrong way.

**The ridge runs parallel to the facade, always.** The eaves-front house is the 1835
form; the gable-front house turned end-on to the street is the Greek Revival habit of
the 1840s. `frame_dwelling_params` refuses a range deeper than one and a half times its
frontage rather than build one.

**Balloon framing moves vertices here.** `construction` picks the stud module (16 in
against 24), the module places every opening, a braced frame gets the girt band its
upper floor puts in the siding and a balloon frame does not, and the corner boards
follow. The studs themselves are behind the sheathing on a finished house and are not
modelled, but the one place the frame reaches the surface is: clapboard butt joints
fall on stud lines, staggered course to course, which is what an eye that knows how a
wall is built actually reads off it.

**A note on face winding.** Every quad here is wound so its normal points out of the
building. Blender's exporter writes `doubleSided: true` for a default material, so a
reversed face is invisible today — but the contract says counter-clockwise and outward,
and a renderer that ever enables culling would find holes rather than a bug report.
`_panel` exists so no recessed opening can get this wrong by hand.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from common.mesh import (  # noqa: E402
    SHUTTER_RGBA, MeshBuilder, simple_material,
)
from archetypes.frame_dwelling_params import (  # noqa: E402
    HALL_FRACTION, FrameDwellingParams,
)

# Materials are indices into the list passed to to_object(), in this order.
M_WALL, M_ROOF, M_TRIM, M_DARK, M_SHUTTER = 0, 1, 2, 3, 4
# Appended only where the record counts a stack (T-0008) — appended rather than
# inserted, and conditionally, for the reason `log_dwelling` gives at its own
# mats list: a material slot nothing references still reaches the glTF, so adding
# one unconditionally would rewrite every chimneyless master in the archetype for
# a colour none of them uses.
M_CHIMNEY = 5

# The exposed face of a course is `params.siding_exposure_m` — a record's own mill
# stock since T-0049, defaulting to 0.14 m (~5.5 in), which was this constant.
CLAPBOARD_LIP_M = 0.018     # how far a course stands proud of the one above it
EAVE_M = 0.25               # eave overhang, matching the other archetypes
TRIM_RELIEF_M = 0.032       # boarded trim standing off the siding

# A window opening sized from the one attested pane in this dataset: the Green Tree's
# 6 x 8 in lights (chicagology_prefire127). Four panes across and three high per sash,
# with stiles and rails, comes to roughly this — small, and nearly as wide as it is
# tall by comparison with the tall sash of a later decade.
WIN_W_M, WIN_H_M = 0.78, 1.25
# The gable-end window of a half storey. "A small attic window in the gable end."
GABLE_WIN_W_M, GABLE_WIN_H_M = 0.62, 0.70
DOOR_W_M, DOOR_H_M = 0.92, 2.02
# The threshold stands on the sill rather than on the ground. Small, and load-bearing
# for the GROUND_CONTACT claim: the boarded surround around an opening reaches 75 mm
# past it on every side, so a door drawn from z = 0.02 puts trim below the base of the
# walls and the archetype stops being flat on its own footprint.
DOOR_SILL_M = 0.10

# Longest clapboard a mill of this period shipped, roughly; it is what sets how many
# butt joints a wall of a given length carries. Lumber came from St Joseph, Michigan, by
# scow (docs/research/02-flora.md), so these were sawn boards, not riven ones.
CLAPBOARD_RUN_M = 4.4


def build(params: FrameDwellingParams, name: str):
    """Build the house. Returns a Blender object at the local origin, y-up handled by
    the exporter (Blender is z-up internally)."""
    params.resolve()
    b = MeshBuilder(name)

    w, d = params.width_m, params.depth_m
    y0 = d - params.main_depth_m          # the front range's rear wall
    wall_z = params.wall_height_m

    # Massing confidence describes the building's CHARACTER, not the precision of its
    # dimensions. The reasoning is set out at length in frame_tavern.build and is not
    # repeated here; the short form is that an unknown size and an unknown form are
    # different kinds of not-knowing, and dithering a well-attested building into ghost
    # massing because nobody wrote down its width misrepresents the evidence in the
    # direction of false modesty. Dimensional uncertainty is carried honestly elsewhere
    # — the footprint keeps its own confidence in the sidecar and the placement carries
    # uncertainty_m, and both surface in the popup.
    c_mass = params.worst_conf("stories", "construction", "cladding")
    c_roof = params.worst_conf("roof_type", "roof_pitch_deg")
    c_clad = params.worst_conf("cladding", "paint")
    # The trim IS the construction argument — corner boards, the girt band, the module
    # the openings sit on — so it carries the confidence of the attribute that decides
    # it rather than the massing's.
    c_trim = params.conf("construction", "reconstructed")
    # The arrangement of the front comes from `plan` and `bays`; where a record states
    # neither, the archetype's own default plan is doing the talking and the geometry
    # says so.
    c_fen = max(params.conf("fenestration", "reconstructed"),
                params.conf("plan", "reconstructed"), params.conf("bays", "reconstructed"))

    # main range — omit the bottom, it is never seen and costs two triangles per
    # building across the whole town
    b.add_box(0, y0, 0, w, d, wall_z, c_mass, M_WALL, skip=("bottom",))
    # the siding starts above the water table and stops under the frieze, because
    # that is where the boards stop on a building and because a course hidden behind
    # a trim board is triangles nobody sees
    _clapboard(b, params, 0, y0, w, d, 0.20, wall_z - 0.20, c_clad, long_axis="x")
    _wall_trim(b, params, 0, y0, w, d, wall_z, c_trim)

    ridge_z = _roof(b, params, 0, y0, w, d, wall_z, c_roof)

    openings = _facade_openings(params)
    _facade(b, params, openings, w, d, y0, wall_z, c_fen)
    _gable_ends(b, params, w, y0, d, wall_z, ridge_z, c_fen, c_mass)
    _rear_windows(b, params, openings, w, y0, wall_z, c_fen)

    ell_ridge_z = _ell(b, params, w, y0, c_clad, c_trim, c_fen) if params.ell \
        else None

    _chimneys(b, params, w, y0, d, wall_z, ridge_z, ell_ridge_z,
              params.conf("chimneys", "reconstructed"),
              M_CHIMNEY if params.chimneys > 0 else M_ROOF)

    if params.porch:
        _porch(b, params, openings, d, wall_z, params.conf("porch", "reconstructed"))

    # ---- the surfaces, off the sheet (T-0007) --------------------------------
    # `common/materials.py` IS docs/RESEARCH/materials.md. The wall is a clapboard
    # substrate — this archetype builds no other, and `_clapboard` above is what
    # makes that true — so its ROUGHNESS is the sheet's 0.86 for bare stock, and a
    # coating overrides it with its own (limewash 0.90, lead paint 0.60). Its COLOUR
    # is the finish: a paint the record states, else the finish the 665-roof
    # programme dealt it, else the archetypes' committed unpainted tone. Before this
    # parcel every house in the town wore that last one whatever its record said.
    finish = materials.wall_finish(params.paint, params.finish_key)
    wall_rgba, wall_rough = materials.resolve(
        materials.wall_substrate(cladding="clapboard"), finish)
    # A weathering CONDITION and not a covering: nothing in this repository states
    # what any of these roofs was made of, and this parcel does not pretend one.
    roof_rgba = materials.roof_finish(params.roof_condition).rgba
    mats = [
        simple_material("wall", wall_rgba, roughness=wall_rough),
        # 0.9 is the archetype's own committed roof value and stays a literal: the
        # sheet's §2.2 has one roughness for a shingle field and another for a board
        # roof, and choosing between them would be claiming the covering finding 2
        # says nobody stated.
        simple_material("roof", roof_rgba, roughness=0.9),
        simple_material("trim", materials.trim_rgba(finish), roughness=0.85),
        # ONE DARK (T-0126). materials.md §2.3's convergence: this archetype's 112
        # opening panels wore 0.070/0.080/0.090 at roughness 0.35, the outbuilding's
        # 117 wore 0.072/0.068/0.060 at 0.60, and the fort, the stockade and the log
        # cabins wore the first colour at 0.40 — three readings of one idea, and the
        # roughness spread is the half a visitor sees, because a window here glinted
        # and the identical opening on the shed next door did not. The sheet's `DARK`
        # row is now the single answer. Its 0.60 is a bounded midpoint and the note
        # on the row is the argument; what matters HERE is that these particular
        # panels are the glazed end of the family — every one of them is sized off
        # the Green Tree's attested 6x8 lights (WIN_W_M above) — which is what keeps
        # the row off the bare-fabric roughnesses and holds some specular in it.
        simple_material("dark", materials.DARK.rgba,
                        roughness=materials.DARK.roughness),
        simple_material("shutter",
                        SHUTTER_RGBA.get(params.shutters or "", SHUTTER_RGBA["green"])),
    ]
    # THE STACK IS NOT THE ROOF (T-0008). Until this parcel every stack this
    # archetype built took `M_ROOF`, so a chimney was painted whatever weathering
    # condition its roof was dealt — R-W2a finding 1, and 71 of the town's 157 stacks
    # are this archetype's.
    # A stack that rises inside the wall and breaks the roof at the ridge is masonry
    # by necessity, and the masonry this town had was brick: `common/materials.py`
    # § the chimney stack, and docs/RESEARCH/chimneys.md.
    if params.chimneys > 0:
        stack = materials.chimney_finish("interior")
        mats.append(simple_material("chimney", stack.rgba, roughness=stack.roughness))
    return b.to_object(mats)


# ------------------------------------------------------------------ primitives

def _panel(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
           z0: float, z1: float, outward: int, conf: float, mat: int) -> None:
    """One flat rectangle on an axis-aligned plane, wound to face `outward`.

    `axis` names the plane's normal axis ('x' or 'y'); `u0`/`u1` run along the other
    horizontal axis. Every applied surface in this module goes through here so none of
    them can end up facing into the building.
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
             relief: float = TRIM_RELIEF_M) -> None:
    """A door or window: a dark opening inside a boarded surround.

    Surfaces, not holes. At this level of detail a real opening would show the inside
    of the far wall, and interiors are out of scope.

    The surround is not decoration. A frame wall's openings are trimmed with boards
    wider than the siding is thick, and without them the dark rectangle has to sit
    proud of the wall to be visible at all, which reads as a plaque glued on. Both
    surfaces are flat, so the dark panel sits very slightly IN FRONT of the surround
    rather than recessed into it — it is entirely inside the surround's outline and
    would otherwise be hidden by it.
    """
    off = relief + 0.010
    m = 0.075
    _panel(b, axis, plane + outward * off, u0 - m, u1 + m, z0 - m, z1 + m,
           outward, conf, M_TRIM)
    _panel(b, axis, plane + outward * (off + 0.006), u0, u1, z0, z1,
           outward, conf, M_DARK)


def _sash(sill: float, head_limit: float) -> float:
    """How tall a window can be between this sill and the plate above it.

    Not a nicety. The window is sized from an attested pane, the wall height is the
    record's, and the two do not have to agree: a low one-storey house at the bottom of
    the range this archetype accepts has less wall between its sill and its frieze board
    than a full sash needs. Left unchecked the head pushes through the plate and out of
    the top of the building — visible, wrong, and only in the combinations no golden case
    happens to use. So the opening shortens instead, which is what a builder did.
    """
    return min(WIN_H_M, head_limit - sill)


def _band(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
          z0: float, z1: float, conf: float, mat: int,
          relief: float = TRIM_RELIEF_M, skip: tuple = ()) -> None:
    """A horizontal board running round the elevations of a block.

    `skip` names faces the way `MeshBuilder.add_box` does — `front` is the -y face,
    `back` the +y one — so a wing abutting a wall can leave out the elevation that is
    not there.
    """
    if "front" not in skip:
        _panel(b, "y", y0 - relief, x0, x1, z0, z1, -1, conf, mat)
    if "back" not in skip:
        _panel(b, "y", y1 + relief, x0, x1, z0, z1, 1, conf, mat)
    if "left" not in skip:
        _panel(b, "x", x0 - relief, y0, y1, z0, z1, -1, conf, mat)
    if "right" not in skip:
        _panel(b, "x", x1 + relief, y0, y1, z0, z1, 1, conf, mat)


# ------------------------------------------------------------- walls and trim

def _clapboard(b: MeshBuilder, p: FrameDwellingParams, x0: float, y0: float,
               x1: float, y1: float, z_lo: float, z_hi: float, conf: float,
               long_axis: str, skip: tuple = ()) -> None:
    """Horizontal lap courses on all four elevations, with butt joints on stud lines.

    The lap is the same treatment `frame_tavern` and `log_dwelling`'s frame addition
    use, so a dwelling, a tavern and a frame wing read as the same material at fifty
    metres. What is new here is the joint.

    **Why the joints matter.** A clapboard is a board, not a ribbon: it runs a few
    metres and then another one starts, and the join has to land on a stud because
    that is the only thing there to nail it to. So the vertical seams in a real wall
    fall on the frame's module and stagger from course to course, and that pattern is
    the one thing about the framing that reaches the outside of a finished house. It
    is also, at walking distance, most of what stops a clapboard wall reading as a
    printed texture. `construction` sets the module, so a balloon frame's seams fall on
    16 in centres and a braced frame's on 24 in ones.

    The stagger is deterministic — a fixed step through the stud lines rather than a
    random draw — because a generator that produced a different wall on every run would
    make `assets/manifest.json`'s input hashes meaningless.
    """
    stud = p.stud_spacing_m
    course = p.siding_exposure_m
    n = int((z_hi - z_lo) / course)
    lip = CLAPBOARD_LIP_M
    faces_y = [(y, ny, sgn, nm) for y, ny, sgn, nm in
               ((y0, y0 - lip, -1.0, "front"), (y1, y1 + lip, 1.0, "back"))
               if nm not in skip]
    faces_x = [(x, nx, sgn, nm) for x, nx, sgn, nm in
               ((x0, x0 - lip, -1.0, "left"), (x1, x1 + lip, 1.0, "right"))
               if nm not in skip]
    for i in range(1, n):
        z = z_lo + i * course
        if z > z_hi - 0.02:
            break
        for y, ny, _sgn, _nm in faces_y:
            b.add_poly([(x0, y, z), (x1, y, z), (x1, ny, z - 0.02), (x0, ny, z - 0.02)],
                       conf, M_WALL)
        for x, nx, _sgn, _nm in faces_x:
            b.add_poly([(x, y0, z), (x, y1, z), (nx, y1, z - 0.02), (nx, y0, z - 0.02)],
                       conf, M_WALL)
        # butt joints, on the two elevations facing along the building's length
        if long_axis == "x":
            for jx in _joint_positions(x0, x1, stud, i):
                for y, _ny, sgn, _nm in faces_y:
                    _panel(b, "y", y + sgn * (lip + 0.006), jx - 0.015, jx + 0.015,
                           z - course, z, int(sgn), conf, M_WALL)
        else:
            for jy in _joint_positions(y0, y1, stud, i):
                for x, _nx, sgn, _nm in faces_x:
                    _panel(b, "x", x + sgn * (lip + 0.006), jy - 0.015, jy + 0.015,
                           z - course, z, int(sgn), conf, M_WALL)


def _joint_positions(u0: float, u1: float, stud: float, course: int) -> list:
    """Where this course's boards butt, as stud lines along a wall.

    One joint per full board run, stepped along by three studs per course so no two
    adjacent courses join over the same stud — which is how a wall is actually laid up,
    and why the pattern reads as boards rather than as a grid.
    """
    length = u1 - u0
    n_studs = max(1, int(length / stud))
    n_joints = int(length / CLAPBOARD_RUN_M)
    if n_joints < 1 or n_studs < 3:
        return []
    out = []
    for j in range(n_joints):
        k = (course * 3 + j * max(2, n_studs // (n_joints + 1))) % n_studs
        u = u0 + (k + 1) * stud
        if u0 + 0.4 < u < u1 - 0.4:
            out.append(u)
    return out


def _wall_trim(b: MeshBuilder, p: FrameDwellingParams, x0: float, y0: float,
               x1: float, y1: float, wall_z: float, conf: float) -> None:
    """Corner boards, water table, frieze, and the girt band a braced frame shows.

    This is where `construction` stops being a word in the sidecar. A balloon frame's
    studs run in one piece from sill to plate, so its wall has no horizontal break in
    it anywhere; a braced frame carries a girt at the upper floor and the siding shows
    the line. That is the most legible exterior difference between the two systems and
    it costs four quads. The corner board follows the same logic from the other end: a
    braced frame has a heavy corner post to box and a balloon frame has only studs, so
    the board is wider on the older system.

    None of it is attested for any building; it is what a sheathed frame wall needs to
    keep water out of its corners and its sill, and a record's `cladding` attribute
    declares `geometry: simplified` over the whole of it.
    """
    board = 0.19 if p.construction == "braced_frame" else 0.13
    # water table at the sill and frieze under the plate
    _band(b, x0, y0, x1, y1, 0.0, 0.20, conf, M_TRIM)
    _band(b, x0, y0, x1, y1, wall_z - 0.20, wall_z, conf, M_TRIM)
    if p.construction == "braced_frame" and p.stories > 1.0:
        floor_z = (wall_z - p.knee_wall_m) if p.half_story else wall_z / 2.0
        _band(b, x0, y0, x1, y1, floor_z - 0.06, floor_z + 0.06, conf, M_TRIM)
    # corner boards: one on each face of each corner, so a corner reads as boxed
    for x, sx in ((x0, -1.0), (x1, 1.0)):
        for y, sy in ((y0, -1.0), (y1, 1.0)):
            bx0, bx1 = sorted((x, x - sx * board))
            by0, by1 = sorted((y, y - sy * board))
            _panel(b, "y", y + sy * TRIM_RELIEF_M, bx0, bx1, 0.20,
                   wall_z - 0.20, int(sy), conf, M_TRIM)
            _panel(b, "x", x + sx * TRIM_RELIEF_M, by0, by1, 0.20,
                   wall_z - 0.20, int(sx), conf, M_TRIM)


# ------------------------------------------------------------------------ roof

def _roof(b: MeshBuilder, p: FrameDwellingParams, x0: float, y0: float,
          x1: float, y1: float, eave_z: float, conf: float) -> float:
    """The main roof. Returns the height of its highest point.

    Ridge parallel to the facade, always — see the module docstring. The gable ends are
    passed inset by the overhang so that after `add_gable_roof` grows the rectangle
    uniformly they land FLUSH with the walls below, while the eaves still project over
    the front and back. A gable end has a rake board, not an eave; letting the standard
    overhang run round all four sides steps the gable a quarter of a metre out from the
    wall under it, which on a house is plainly visible.
    """
    if p.roof_type == "shed":
        return _shed_roof(b, x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf)
    return b.add_gable_roof(x0 + EAVE_M, y0, x1 - EAVE_M, y1, eave_z,
                            p.roof_pitch_deg, conf, M_ROOF, overhang=EAVE_M,
                            ridge_along_x=True)


def _shed_roof(b: MeshBuilder, x0, y0, x1, y1, eave_z, pitch_deg, conf,
               thickness: float = 0.10) -> float:
    """A single plane falling from the back wall to the facade.

    Falling toward the facade rather than away from it is the frontier default: the
    tall wall is the one the chimney and the back rooms go against, and rain runs off in
    front of the door where the ground is trodden hard. It is a convention, not an
    attested fact, and it is only reached when a record explicitly says shed.
    """
    x0, y0, x1, y1 = x0 - EAVE_M, y0 - EAVE_M, x1 + EAVE_M, y1 + EAVE_M
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


# ------------------------------------------------------------------- the front

def _facade_openings(p: FrameDwellingParams) -> list:
    """Where the openings go across the front, as `(centre_x, kind)`.

    **This is the archetype's answer to docs/LIBERTIES.md L23** — one window
    arrangement on every frame building. The front is not a fixed five bays: the count
    comes from the frontage (or from the record) and the ARRANGEMENT comes from the
    plan behind the wall, which is what actually decides where a door is.

    - `hall_parlour`, the default and the commonest vernacular plan, divides the front
      at the partition between the larger heated hall and the smaller parlour. The door
      opens into the hall, near the middle of it, so it is well off the centre of the
      building and the two rooms' windows are spaced differently from one another —
      with a wider gap over the partition. That gap is the plan showing through the
      wall, and it is what makes the front read as a house rather than as a facade.
    - `centre_passage` is the symmetrical alternative, and it has to be asked for.
    - `single_pen` is one room: a door and a window or two beside it.

    Every centre is then snapped to a stud-bay centre, so an opening's jambs land
    against studs. That is a real constraint on where a window can go in a framed wall,
    and it is what makes the stud module something the facade obeys rather than
    something the sidecar mentions.
    """
    w, n = p.width_m, p.bays
    if p.plan == "centre_passage":
        centres = [w * (i + 0.5) / n for i in range(n)]
        door = n // 2
        out = [(x, "door" if i == door else "window") for i, x in enumerate(centres)]
        return [(_snap(x, p, w), k) for x, k in out]

    hf = 0.5 if p.plan == "single_pen" else HALL_FRACTION
    xp = w * hf
    if p.plan == "single_pen":
        n_hall = 1
    else:
        n_hall = 1 + min(max(int(round((n - 1) * hf)), 1), n - 2)
    n_parlour = n - n_hall

    out = []
    door_i = n_hall // 2
    for i in range(n_hall):
        out.append((xp * (i + 0.5) / n_hall, "door" if i == door_i else "window"))
    for j in range(n_parlour):
        out.append((xp + (w - xp) * (j + 0.5) / n_parlour, "window"))
    return [(_snap(x, p, w), k) for x, k in out]


def _snap(x: float, p: FrameDwellingParams, w: float) -> float:
    """Nearest stud-bay centre, kept clear of the corner boards."""
    stud = p.stud_spacing_m
    k = math.floor(x / stud)
    u = (k + 0.5) * stud
    return min(max(u, 0.72), w - 0.72)


def _facade(b: MeshBuilder, p: FrameDwellingParams, openings: list, w: float,
            d: float, y0: float, wall_z: float, conf: float) -> None:
    """The front elevation: door, windows, and shutters where a record attests them.

    A half storey has NO front windows and that is the whole point of it — its chambers
    are lit from the gable ends, which is what "a small attic window in the gable end"
    describes. Dormers are a later and richer habit; adding one to make the half storey
    more visible would be manufacturing evidence.
    """
    story_h = wall_z / 2.0 if p.stories >= 2.0 else wall_z
    sill = min(0.95, story_h * 0.36)
    c_shut = p.conf("shutters", "reconstructed")
    # everything on this wall stops under the frieze board
    top_head = wall_z - 0.28
    h = _sash(sill, story_h - 0.14 if p.stories >= 2.0 else top_head)
    door_h = min(DOOR_H_M, top_head - DOOR_SILL_M)

    for cx, kind in openings:
        if kind == "door":
            if door_h > 1.6:
                _opening(b, "y", d, cx - DOOR_W_M / 2, cx + DOOR_W_M / 2, DOOR_SILL_M,
                         DOOR_SILL_M + door_h, 1, conf)
            continue
        if h < 0.5:
            continue
        _opening(b, "y", d, cx - WIN_W_M / 2, cx + WIN_W_M / 2, sill, sill + h, 1, conf)
        if p.shutters:
            _shutters(b, d, cx, sill, sill + h, 1, c_shut)

    if p.stories >= 2.0:
        z = story_h + sill
        hu = _sash(z, top_head)
        for cx, _kind in openings:
            if hu < 0.5:
                continue
            _opening(b, "y", d, cx - WIN_W_M / 2, cx + WIN_W_M / 2, z, z + hu, 1, conf)
            if p.shutters:
                _shutters(b, d, cx, z, z + hu, 1, c_shut)


def _shutters(b: MeshBuilder, plane: float, cx: float, z0: float, z1: float,
              outward: int, conf: float) -> None:
    """Board shutters hung either side of a window, in the open position.

    Only ever built when a record states them. The Sauganash's bright-blue shutters are
    documented and were worth remarking on precisely because they were unusual; a house
    that says nothing about shutters gets none rather than a plainer pair.
    """
    for side in (-1, 1):
        x0 = cx + side * (WIN_W_M / 2 + 0.08)
        x1 = x0 + side * (WIN_W_M * 0.46)
        lo, hi = min(x0, x1), max(x0, x1)
        _panel(b, "y", plane + outward * (TRIM_RELIEF_M + 0.004), lo, hi, z0, z1,
               outward, conf, M_SHUTTER)


def _rear_windows(b: MeshBuilder, p: FrameDwellingParams, openings: list, w: float,
                  y0: float, wall_z: float, conf: float) -> None:
    """One or two windows on the back of the front range, where the ell is not.

    The back of a house was the working side and was worse lit than the front; two
    openings at most, and none at all where the wing covers the wall.
    """
    if p.ell:
        ex0, ex1 = _ell_extent(p, w)
    else:
        ex0 = ex1 = -1.0
    sill = min(0.95, (wall_z / 2.0 if p.stories >= 2.0 else wall_z) * 0.36)
    h = _sash(sill, (wall_z / 2.0 - 0.14) if p.stories >= 2.0 else wall_z - 0.28)
    if h < 0.5:
        return
    placed = 0
    for cx, kind in openings:
        if kind == "door" or placed >= 2:
            continue
        if ex0 - 0.5 < cx < ex1 + 0.5:
            continue
        _opening(b, "y", y0, cx - WIN_W_M / 2, cx + WIN_W_M / 2, sill,
                 sill + h, -1, conf)
        placed += 1


def _gable_ends(b: MeshBuilder, p: FrameDwellingParams, w: float, y0: float,
                d: float, wall_z: float, ridge_z: float, c_fen: float,
                c_mass: float) -> None:
    """The gable-end windows — the half storey's only light, and its only outside sign.

    "A small attic window in the gable end, for we used the attic, too" (John Gray on
    the Green Tree, `chicagology_prefire127`). One per end, above the plate, centred in
    the gable and small. It carries the MASSING's confidence rather than the
    fenestration's, because what it says is that there was a half storey here — which
    is the `stories` claim — not that a window was arranged just so.

    A ground-floor window goes in whichever gable end has no stack against it. The end
    walls of a small house carried very little glass; the fireplaces were there.
    """
    if p.roof_type != "gable":
        return
    rise = ridge_z - wall_z
    yc = (y0 + d) / 2.0
    half_depth = (d - y0) / 2.0 + EAVE_M

    for x, out in ((0.0, -1), (w, 1)):
        top = wall_z + 0.16 + GABLE_WIN_H_M
        shrink = 1.0 - (top - wall_z) / max(rise, 1e-6)
        if shrink * half_depth > GABLE_WIN_W_M / 2 + 0.35 and p.stories >= 1.5:
            # the gable face is the roof's end triangle, which sits flush with the
            # wall because _roof insets it by the overhang
            _opening(b, "x", x, yc - GABLE_WIN_W_M / 2, yc + GABLE_WIN_W_M / 2,
                     wall_z + 0.16, top, out, c_mass)

    stack_x = _stack_positions(p, w)
    sill = min(0.95, (wall_z / 2.0 if p.stories >= 2.0 else wall_z) * 0.36)
    h = _sash(sill, (wall_z / 2.0 - 0.14) if p.stories >= 2.0 else wall_z - 0.28)
    if h < 0.5:
        return
    for x, out in ((0.0, -1), (w, 1)):
        if any(abs(sx - x) < 1.0 for sx in stack_x):
            continue
        _opening(b, "x", x, yc - WIN_W_M / 2, yc + WIN_W_M / 2, sill,
                 sill + h, out, c_fen)


# -------------------------------------------------------------------- the ell

def _ell_extent(p: FrameDwellingParams, w: float) -> tuple:
    """The wing's x range inside the footprint. It hugs whichever side the record's
    own footprint polygon puts it on."""
    if p.ell_side == "east":
        return w - p.ell_width_m, w
    return 0.0, p.ell_width_m


def _ell(b: MeshBuilder, p: FrameDwellingParams, w: float, y0: float,
         c_clad: float, c_trim: float, c_fen: float) -> float:
    """The rear kitchen wing. Returns its ridge height.

    Its arms come out of the footprint polygon, not out of invented parameters — see
    `frame_dwelling_params.read_plan`. Its confidence is its own: that there WAS a wing
    is what `ell` states, and the L that gives its size is the footprint's claim,
    carried in the sidecar where the popup shows it.

    "A low one-story addition to the right, the same as on the left" is the dataset's
    one direct description of a subordinate frame wing at Chicago (John Gray on the
    Green Tree, `chicagology_prefire127`), and low is the operative word: the wing's
    eave and ridge both sit under the house's, which is what stops it reading as a
    second house pushed up against the first.

    The wing's own gable runs BACK from the house rather than parallel to it, so its
    ridge dies into the main rear wall. That is how a rear wing is built and it is also
    what keeps the two roofs from fighting: the ell's roof is inset by the eave
    overhang at the junction, so no plane is driven into the wall behind it.
    """
    c = p.conf("ell", "reconstructed")
    ex0, ex1 = _ell_extent(p, w)
    ez = p.ell_height_m

    # the face against the main range is skipped: the wall behind it is already there,
    # and two coincident surfaces are a z-fighting stripe down the most visible corner
    # of the building
    b.add_box(ex0, 0.0, 0.0, ex1, y0, ez, c, M_WALL, skip=("bottom", "back"))
    _clapboard(b, p, ex0, 0.0, ex1, y0, 0.18, ez - 0.18, c_clad, long_axis="y",
               skip=("back",))
    _band(b, ex0, 0.0, ex1, y0, 0.0, 0.18, c_trim, M_TRIM, skip=("back",))
    _band(b, ex0, 0.0, ex1, y0, ez - 0.18, ez, c_trim, M_TRIM, skip=("back",))

    ridge_z = b.add_gable_roof(ex0, EAVE_M, ex1, y0 - EAVE_M, ez, p.roof_pitch_deg,
                               c, M_ROOF, overhang=EAVE_M, ridge_along_x=False)

    # a door and a window on the wing: the kitchen's own way out to the yard
    xc = (ex0 + ex1) / 2.0
    door_h = min(DOOR_H_M, ez - 0.26 - DOOR_SILL_M)
    if door_h > 1.6:
        _opening(b, "y", 0.0, xc - DOOR_W_M / 2, xc + DOOR_W_M / 2, DOOR_SILL_M,
                 DOOR_SILL_M + door_h, -1, c_fen)
    side_x, out = (ex0, -1) if p.ell_side == "east" else (ex1, 1)
    yc = y0 / 2.0
    sill = 0.85
    h = _sash(sill, ez - 0.26)
    if h > 0.5:
        _opening(b, "x", side_x, yc - WIN_W_M / 2, yc + WIN_W_M / 2, sill,
                 sill + h, out, c_fen)
    return ridge_z


# ------------------------------------------------------------ stacks and porch

def _stack_positions(p: FrameDwellingParams, w: float) -> list:
    """Where the stacks stand, as x on the main ridge. May be shorter than the count —
    a stack on the ell has no x on this ridge."""
    if p.chimneys <= 0:
        return []
    out = [0.75]
    if p.chimneys >= 3 or (p.chimneys == 2 and not p.ell):
        out.append(w - 0.75)
    return out


def _chimneys(b: MeshBuilder, p: FrameDwellingParams, w: float, y0: float, d: float,
              wall_z: float, ridge_z: float, ell_ridge_z: float | None,
              conf: float, mat: int) -> None:
    """As many stacks as the record counts, placed by the archetype.

    The count is the record's; everything else about a stack here is invented, so the
    arrangement needs an argument rather than a preference:

    - The first stands at a GABLE END, rising inside the wall and breaking the roof at
      the ridge. That is the eastern habit these settlers brought with them, and it is
      the difference between a framed house and the log cabins next door, whose stacks
      `log_dwelling` builds OUTSIDE the gable so they can be pulled down when they
      catch fire.
    - The second goes on the ELL when there is one, because a kitchen wing exists to
      hold the kitchen fire; with no wing it goes to the other gable.
    - The third, only reachable with a wing, takes the other gable.

    docs/LIBERTIES.md L26 owns all of it — every chimney in this project stands where
    its archetype puts it.
    """
    if p.chimneys <= 0:
        return
    yc = (y0 + d) / 2.0
    for cx in _stack_positions(p, w):
        _stack(b, cx, yc, wall_z, ridge_z, conf, mat)
    if p.ell and p.chimneys >= 2 and ell_ridge_z is not None:
        ex0, ex1 = _ell_extent(p, w)
        # near the wing's own outer gable, and kept inside it however short it is
        cy = min(0.95, max(0.55, p.ell_depth_m * 0.3))
        _stack(b, (ex0 + ex1) / 2.0, cy, p.ell_height_m, ell_ridge_z, conf, mat)


def _stack(b: MeshBuilder, cx: float, cy: float, base_z: float, ridge_z: float,
           conf: float, mat: int) -> None:
    """One stack, from inside the roof to a corbelled head above the ridge."""
    half = 0.42
    b.add_box(cx - half, cy - half, base_z - 0.4, cx + half, cy + half,
              ridge_z + 0.62, conf, mat, skip=("bottom",))
    b.add_box(cx - half - 0.07, cy - half - 0.07, ridge_z + 0.62,
              cx + half + 0.07, cy + half + 0.07, ridge_z + 0.78, conf, mat,
              skip=("bottom",))


def _porch(b: MeshBuilder, p: FrameDwellingParams, openings: list, d: float,
           wall_z: float, conf: float) -> None:
    """A stoop, or a small roofed porch over the door. NOT a gallery.

    The distinction is the reason this parameter exists. `frame_tavern` builds a
    full-width two-tier gallery because that is what the retrospective images of the
    Sauganash argue about; a gallery is public-house furniture, a place for travellers
    to sit. A house has a stoop: a plank landing and two steps, so the door does not
    open onto mud. Chicago's streets were unpaved and in July 1836 there was still "a
    pond of water on Lake Street, corner of La Salle, inhabited by frogs"
    (`andreas_1884_v1`, scan p. 403), which is the ground this step is above.

    The stoop projects beyond the recorded footprint, because that is what a stoop
    does. It is the one part of this archetype that stands outside the polygon, and the
    first record that carries a porch owes docs/LIBERTIES.md an entry saying so.
    """
    door = next((cx for cx, k in openings if k == "door"), p.width_m / 2.0)
    step = 0.19
    wide, deep = 1.55, 0.62

    # landing, then one step down to the ground
    b.add_box(door - wide / 2, d, 0.0, door + wide / 2, d + deep, step * 2,
              conf, M_TRIM, skip=("bottom", "back"))
    b.add_box(door - wide / 2 + 0.09, d + deep, 0.0, door + wide / 2 - 0.09,
              d + deep + 0.30, step, conf, M_TRIM, skip=("bottom", "back"))
    if p.porch != "roofed":
        return

    # a small shed roof on two posts, over the door only
    pw, pd = 2.30, 1.35
    head = min(wall_z - 0.32, 2.62)
    x0, x1 = door - pw / 2, door + pw / 2
    yf = d + pd
    for x in (x0 + 0.09, x1 - 0.09):
        b.add_box(x - 0.055, yf - 0.14, 0.0, x + 0.055, yf - 0.02, head - 0.12,
                  conf, M_TRIM, skip=("bottom",))
    drop = 0.22
    for dz in (0.0, -0.07):
        b.add_poly([(x0, yf, head - drop + dz), (x1, yf, head - drop + dz),
                    (x1, d, head + dz), (x0, d, head + dz)], conf, M_ROOF)
    b.add_poly([(x0, yf, head - drop - 0.07), (x1, yf, head - drop - 0.07),
                (x1, yf, head - drop), (x0, yf, head - drop)], conf, M_ROOF)
    for x, sgn in ((x0, -1), (x1, 1)):
        pts = [(yf, head - drop - 0.07), (yf, head - drop), (d, head), (d, head - 0.07)]
        if sgn > 0:
            pts.reverse()
        b.add_poly([(x, y, z) for y, z in pts], conf, M_ROOF)
