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
from common import openings  # noqa: E402
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.log_dwelling_params import (  # noqa: E402
    LIGHT_HALF_W_M, LIGHT_HALF_H_M,
    ADDITION_WIN_HALF_M, DOOR_HALF_M, WIN_AT_FRAC, WIN_HALF_M, LogDwellingParams,
    addition_extent, addition_front_rects, core_extent, core_front_rects,
    lean_to_extent, compound_front_rects, resolved_core_ridge_axis,
)

#: This archetype's roof COVERING, off the sheet's dealing rule (T-1487).
#: `materials.roof_substrate` holds the argument for why it is this one and
#: which half of it is graded by materials.md §2.2 and which half is L266.
_ROOF = materials.roof_substrate("log_dwelling")
# T-2386: same reconstructed local stock as frame_tavern; no shared finish retune.
ROOF_DEEP_BROWN_RGBA = tuple(c * 0.25 for c in materials.roof_finish("darkened").rgba[:3]) + (1.0,)


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
    roof_conf_keys = ("roof_type", "roof_pitch_deg")
    if params.roof_ridge_axis is not None:
        roof_conf_keys += ("roof_ridge_axis",)
    c_roof = params.worst_conf(*roof_conf_keys)

    if params.compound_joint == "elbow":
        _elbow(b, params)
    elif params.compound_parts:
        _compound(b, params)
    else:
        # Where the log core sits inside the footprint once the addition is carved out.
        cx0, cy0, cx1, cy1 = core_extent(params)
        wall_z = params.wall_height_m

        hewn_log_wall(b, cx0, cy0, cx1, cy1, 0.0, wall_z, c_mass, M_LOG, M_CHINK,
                      skip=("bottom", "top"))

        if params.front_door_state == "recess":
            _cut_front_door_recess(b, params, cy1)

        ridge_z = _roof(b, params, cx0, cy0, cx1, cy1, wall_z, c_roof)

        if params.loft:
            _loft_opening(b, params, cx0, cy0, cx1, cy1, wall_z, ridge_z,
                          params.conf("loft"))

        _core_openings(b, params, cx0, cy0, cx1, cy1, wall_z,
                       params.conf("fenestration", "reconstructed"))
        if params.end_openings:
            _end_openings(b, params, cx0, cy0, cx1, cy1, wall_z)

        addition_ridge_z = _frame_addition(b, params) if params.frame_addition else None

        if params.lean_to:
            _lean_to(b, params, params.conf("lean_to", "reconstructed"),
                     params.worst_conf("roof_type", "lean_to"))

        if params.piazza:
            _piazza(b, params, cx0, cy0, cx1, cy1, wall_z, params.conf("piazza", "reconstructed"))

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

    # The optional tone carries its own uncertainty on every roof face.
    # Absent/legacy selectors leave every previous confidence value untouched.
    if params.roof_colour == "deep_brown":
        c_colour = params.worst_conf("roof_colour")
        for face, material in zip(b.faces, b.mat_index):
            if material == M_ROOF:
                for vertex in face:
                    b.conf[vertex] = max(b.conf[vertex], c_colour)

    # ---- the surfaces, off the sheet (T-0007) --------------------------------
    # The log core is the town's log fabric and does not vary: a cabin's walls ARE
    # its finish. What varies is the FRAME ADDITION, which is a clapboarded wall like
    # any other and now wears the finish the record deals it, and the roof, which
    # takes the weathering condition 218 records state — a condition, never a
    # covering (materials.md finding 2). See `common/materials.py`.
    frame_finish = materials.wall_finish(params.frame_paint, params.finish_key)
    frame_rgba, frame_rough = materials.resolve(
        materials.wall_substrate(cladding="clapboard"), frame_finish)
    # A STATED COATING ON THE LOGS (T-2511) coats the chinking with them: whitewash
    # goes on the whole wall, and a white log over dark daub would be two finishes.
    # The daub keeps its own roughness under the coat, which also keeps the two slots
    # apart — two identical materials are folded into one by the web derivative.
    log_rgba, log_rough = HEWN_RGBA, materials.SUBSTRATES["hewn_log"].roughness
    chink_rgba, chink_rough = CHINK_RGBA, materials.SUBSTRATES["chinking"].roughness
    if params.log_finish is not None:
        coat = materials.FINISHES[params.log_finish]
        log_rgba = chink_rgba = coat.rgba
        log_rough = coat.roughness
    mats = [
        simple_material("log", log_rgba, roughness=log_rough),
        simple_material("chinking", chink_rgba, roughness=chink_rough),
        # A shingle field on a LOG cabin, and that is the half of the dealing rule
        # §2.2 does not grade — it grades shingle for a FRAMED building. L266 is the
        # liberty: the two coverings this project can argue split on what a roof is
        # FOR, and a cabin is a dwelling and not a shed. `materials.roof_substrate`
        # holds the argument; the 0.9 is unchanged.
        simple_material(materials.roof_material_name(_ROOF),
                        (ROOF_DEEP_BROWN_RGBA if params.roof_colour == "deep_brown"
                         else materials.roof_finish(params.roof_condition).rgba),
                        roughness=_ROOF.roughness),
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
    return resolved_core_ridge_axis(p)


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



def _cut_front_door_recess(b: MeshBuilder, p: LogDwellingParams, wall_y: float) -> None:
    """Existing +Y Hogan skin cutter; same rectangles, order and zero skin-back."""
    _cut_door_recesses(b,"y",wall_y,core_front_rects(p))


def _cut_door_recesses(b,axis,plane,rects,skin_back_m=0.):
    """Subtract stated external doors from one outward +X/+Y wall skin only.

    Reuses the established half-plane partitions; default +Y calls retain all
    old faces/material/confidence. Compound skin-back includes its inset dark
    joint backing so the same blind300mm recess has actual cut reveals.
    """
    def clip(poly, axis, bound, above):
        result = []
        for a, q in zip(poly, poly[1:] + poly[:1]):
            ai = a[axis] >= bound if above else a[axis] <= bound
            qi = q[axis] >= bound if above else q[axis] <= bound
            if ai:
                result.append(a)
            if ai != qi:
                t = (bound - a[axis]) / (q[axis] - a[axis])
                result.append(tuple(a[k] + t * (q[k] - a[k]) for k in range(3)))
        # Boundary vertices may coincide after successive cuts.
        clean = []
        for v in result:
            if not clean or sum((v[k]-clean[-1][k])**2 for k in range(3)) > 1e-20:
                clean.append(v)
        if len(clean) > 1 and sum((clean[0][k]-clean[-1][k])**2 for k in range(3)) < 1e-20:
            clean.pop()
        return clean
    def area(poly):
        n = [0., 0., 0.]
        for a,q in zip(poly, poly[1:] + poly[:1]):
            for k in range(3):
                i,j = (k+1)%3,(k+2)%3
                n[k] += (a[i]-q[i])*(a[j]+q[j])
        return sum(v*v for v in n)
    normal_axis,along_axis = (1,0) if axis == "y" else (0,1)
    doors = [r for r in rects if r[0] == "door"]
    for _, u0, u1, z0, z1 in doors:
        old = [(tuple(b.verts[i] for i in f), tuple(b.conf[i] for i in f), mat)
               for f,mat in zip(b.faces,b.mat_index)]
        b.verts, b.faces, b.conf, b.mat_index = [], [], [], []
        for points,confidence,mat in old:
            poly = list(points)
            if (all(v[normal_axis] >= plane-skin_back_m-1e-9 for v in poly)
                    and min(v[along_axis] for v in poly) < u1 and max(v[along_axis] for v in poly) > u0
                    and min(v[2] for v in poly) < z1 and max(v[2] for v in poly) > z0):
                for axis,bound,above in [(along_axis,u0,True),(along_axis,u1,False),(2,z0,True),(2,z1,False)]:
                    outside = clip(poly,axis,bound,not above)
                    if len(outside) >= 3 and area(outside) > 1e-18:
                        b.add_poly(outside,max(confidence),mat)
                    poly = clip(poly,axis,bound,above)
                    if not poly:
                        break
            else:
                ids = b.add_poly(points,confidence[0],mat)
                for idx,c in zip(ids,confidence):
                    b.conf[idx] = c

def _kit(b: MeshBuilder) -> openings.Mats:
    """The openings kit's materials (T-2278): the sawn surround's own colour for casing
    and sash, the town's glass (Glessner's dark pane), a weathered board leaf with iron
    strap hinges, and the shared dark for a board joint's shadow."""
    rgba, rough = openings.WEATHERED_BOARD
    door = b.named_mat("door", rgba, rough)
    return openings.Mats(
        casing=door, sash=M_FRAME, dark=M_DARK,
        glass=b.named_mat("glass", *openings.glass_material_spec()),
        door=door,
        panel=b.named_mat("door_panel", openings.shade(rgba, 0.70), rough),
        iron=b.named_mat("iron", *openings.STRAP_IRON))


def _opening(b: MeshBuilder, axis: str, plane: float, u0: float, u1: float,
             z0: float, z1: float, outward: int, conf: float, kind: str = "window",
             relief: float = RELIEF_M, frame_wall: bool = False,
             shutters: bool = True, door_state: str = "closed") -> None:
    """A door or window in a log wall (or the frame addition's), built by the shared
    openings kit (T-2278).

    Before this both were a dark panel inside a sawn surround — four triangles, and a
    plaque. Now the surround is a sawn casing standing off the chinking with its
    returns, so it reads as the jamb and head that a cut log wall has to have; the
    window is a small sash glazed in the attested 6 x 8 in lights — three by three in
    a log opening — set back in it over the town's dark glass, with a board shutter
    hung open beside some of them; the door is a CLOSED board-and-batten leaf on iron
    strap hinges. Glass was on sale by the box in Chicago in 1833-35 (see
    `common/openings.py`), so a cabin in this town could be glazed, and is.

    The frame addition's own openings are a frame wall's: a capped casing, a
    six-over-six sash, a panelled door.
    """
    k = _kit(b)
    w = openings.Wall(axis, plane, outward, relief)
    if kind == "door":
        if door_state == "recess":
            # The wall was actually cut back here, including proud chink strips.
            # A 0.30 m blind recess bounds the representation: no interior or
            # unseen leaf/hinge is inferred from Cameron's dark occupied doorway.
            back = -0.30 - w.skin
            openings.surround(b, w, u0, u1, z0, z1, conf, k, sill=False,
                              cap=False, casing_w=0.11, proud=0.045, back=back)
            openings.face(b, w, -0.30, u0, u1, z0, z1, conf, M_DARK)
            openings.threshold(b, w, u0, u1, z0, conf, k.casing, 0.11, 0.045)
            return
        if frame_wall:
            openings.panelled_door(b, w, u0, u1, z0, z1, conf, k)
        else:
            openings.batten_door(b, w, u0, u1, z0, z1, conf, k, seed=b.name,
                                 casing_w=0.11, proud=0.045)
        return
    if frame_wall:
        openings.window(b, w, u0, u1, z0, z1, conf, k, 3, (2, 2))
        return
    openings.window(b, w, u0, u1, z0, z1, conf, k, 3, (3,), cap=False,
                    casing_w=0.10, head_w=0.12, proud=0.045)
    # A pair of board shutters, swung open, on about half the windows in the town — a
    # cabin's winter and night closure. Which half is the window's identity. A pair of
    # half-width leaves rather than one full leaf, because the facade's set-out leaves
    # about a third of a metre between a window's casing and the door's or a corner's
    # notching, and a full leaf would lie across one of them.
    seed = f"{b.name}|{axis}|{plane:.2f}|{u0:.2f}|{z0:.2f}"
    if shutters and openings.deal("shutter|" + seed, 2) == 0:
        half = (u1 - u0) / 2.0
        for edge, side in ((u0 - 0.11, -1), (u1 + 0.11, 1)):
            openings.open_shutter(b, w, edge, half, z0 - 0.02, z1 + 0.02, conf,
                                  k.door, side)


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
    if p.hip_end is not None:
        return _hip_end_roof(b, x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf, M_ROOF,
                             at_min=p.hip_end == "min", inset=p.hip_inset_m)
    if p.end_gable_courses == "+x":
        # Same two slopes and hidden -X cap as the generic roof. Only the
        # pictured +X triangular finish changes; no ridge/footprint alteration.
        ax0, ay0, ax1, ay1 = x0-.25, y0-.25, x1+.25, y1+.25
        ym = (ay0+ay1)/2
        ridge_z = eave_z + (ay1-ay0)/2*math.tan(math.radians(p.roof_pitch_deg))
        b.add_poly([(ax0,ay0,eave_z),(ax1,ay0,eave_z),
                    (ax1,ym,ridge_z),(ax0,ym,ridge_z)],conf,M_ROOF)
        b.add_poly([(ax1,ay1,eave_z),(ax0,ay1,eave_z),
                    (ax0,ym,ridge_z),(ax1,ym,ridge_z)],conf,M_ROOF)
        b.add_poly([(ax0,ay0,eave_z),(ax0,ym,ridge_z),(ax0,ay1,eave_z)],conf,M_ROOF)
        _horizontal_end_courses(b, ax1, ay0, ay1, eave_z, ridge_z,
                                p.conf("end_gable_courses", "inferred"))
        return ridge_z
    if p.front_gable_cladding == "log_courses":
        # Use precisely the existing generic roof's two slopes and back cap.
        # Replace its front cap with the pictured category of horizontal courses.
        # Every course interval, joint and relief is reconstructed, not measured.
        ax0, ay0, ax1, ay1 = x0-.25, y0-.25, x1+.25, y1+.25
        xm = (ax0+ax1)/2
        ridge_z = eave_z + (ax1-ax0)/2*math.tan(math.radians(p.roof_pitch_deg))
        b.add_poly([(ax0,ay0,eave_z),(xm,ay0,ridge_z),
                    (xm,ay1,ridge_z),(ax0,ay1,eave_z)],conf,M_ROOF)
        b.add_poly([(xm,ay0,ridge_z),(ax1,ay0,eave_z),
                    (ax1,ay1,eave_z),(xm,ay1,ridge_z)],conf,M_ROOF)
        b.add_poly([(ax0,ay0,eave_z),(ax1,ay0,eave_z),(xm,ay0,ridge_z)],conf,M_ROOF)
        _log_course_gable(b,"y",ay1,ax0,ax1,eave_z,ridge_z,+1)
        return ridge_z
    return b.add_gable_roof(x0, y0, x1, y1, eave_z, p.roof_pitch_deg, conf, M_ROOF,
                            ridge_along_x=(resolved_core_ridge_axis(p) == "x"))


def _hip_end_roof(b: MeshBuilder, x0, y0, x1, y1, eave_z, pitch_deg, conf, mat,
                  at_min: bool, inset: float | None = None,
                  overhang: float = 0.25) -> float:
    """`add_gable_roof` along x with one end hipped (T-2485).

    The ridge stops `inset` short of that end's eave line and the end's roof falls from
    there to the eave, the way Eastman's 1820 view draws the lodging house's far end.
    None is half the span, a hip at the slopes' own pitch; the inset is measured from
    the wall, and the overhang is added to it. The other end keeps its gable. The
    ridge runs along x only: params refuse `hip_end` anywhere else.
    """
    x0, y0, x1, y1 = x0 - overhang, y0 - overhang, x1 + overhang, y1 + overhang
    rise = ((y1 - y0) / 2.0) * math.tan(math.radians(pitch_deg))
    ridge_z = eave_z + rise
    ym = (y0 + y1) / 2.0
    inset = (y1 - y0) / 2.0 if inset is None else inset + overhang
    ra = x0 + inset if at_min else x0
    rb = x1 if at_min else x1 - inset
    b.add_poly([(x0, y0, eave_z), (x1, y0, eave_z),
                (rb, ym, ridge_z), (ra, ym, ridge_z)], conf, mat)
    b.add_poly([(x1, y1, eave_z), (x0, y1, eave_z),
                (ra, ym, ridge_z), (rb, ym, ridge_z)], conf, mat)
    if at_min:
        b.add_poly([(x0, y0, eave_z), (ra, ym, ridge_z), (x0, y1, eave_z)], conf, mat)
        b.add_poly([(x1, y1, eave_z), (x1, ym, ridge_z), (x1, y0, eave_z)], conf, mat)
    else:
        b.add_poly([(x0, y0, eave_z), (x0, ym, ridge_z), (x0, y1, eave_z)], conf, mat)
        b.add_poly([(x1, y1, eave_z), (rb, ym, ridge_z), (x1, y0, eave_z)], conf, mat)
    return ridge_z


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
    takes the +x or +y end to match, which is why both read
    `resolved_core_ridge_axis` rather than independently inspecting the footprint.
    """
    if p.roof_type != "gable":
        return
    zc = wall_z + (ridge_z - wall_z) * 0.42
    hw, hh, out = 0.34, 0.30, 0.07
    # A closed board hatch in a sawn frame (T-2278): a loft was reached for hay,
    # seed and bedding, not lit, and an open black square read as a hole in the roof.
    k = _kit(b)
    if resolved_core_ridge_axis(p) == "x":
        yc = (y0 + y1) / 2.0
        w, uc = openings.Wall("x", x1, 1, out - 0.02), yc
    else:
        xc = (x0 + x1) / 2.0
        w, uc = openings.Wall("y", y1, 1, out - 0.02), xc
    openings.surround(b, w, uc - hw, uc + hw, zc - hh, zc + hh, conf, k, sill=False,
                      cap=False, casing_w=0.07, head_w=0.08, proud=0.03)
    openings.board_shutter(b, w, uc - hw, uc + hw, zc - hh, zc + hh, conf, k)


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
    if p.front_set_out is not None:
        # A STATED SET-OUT (T-2511): the record's openings in its own order, one
        # storey, and the back window hung on the band its first window takes.
        shut = (x1 - x0) >= 5.2 if p.front_shutters is None else p.front_shutters
        for kind, u0, u1, z0, z1 in rects:
            _opening(b, "y", y1, u0, u1, z0, z1, 1,
                     p.conf("front_door_state", "reconstructed") if kind == "door" and p.front_door_state == "recess" else conf,
                     kind=kind, shutters=shut, door_state=p.front_door_state)
        wins = [r for r in rects if r[0] == "window"]
        z0, z1 = (wins[0][3], wins[0][4]) if wins else (0.82, 1.54)
        if gable_front:
            _opening(b, "x", x0, ym - _WIN_HALF, ym + _WIN_HALF, z0, z1, -1, conf)
        else:
            _opening(b, "y", y0, xm - _WIN_HALF, xm + _WIN_HALF, z0, z1, -1, conf)
        return
    i = 0
    if not front_taken:
        kind, u0, u1, z0, z1 = rects[i]
        i += 1
        _opening(b, "y", y1, u0, u1, z0, z1, 1, conf, kind=kind)

    for story in range(p.stories):
        per = 2 * p.front_windows_per_side
        band = rects[i:i + (per + 1 if front_taken and story == 0 else per)]
        i += len(band)
        for kind, u0, u1, z0, z1 in band:
            _opening(b, "y", y1, u0, u1, z0, z1, 1, conf, kind=kind,
                     shutters=((x1 - x0) >= 5.2 if p.front_shutters is None
                               else p.front_shutters))
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


# --------------------------------------------------------------------- piazza

PIAZZA_DECK_M = 0.12        # plank floor on sleepers: one low step, under the door's sill
PIAZZA_PITCH_DEG = 12.0     # a porch roof is flatter than the house's own
PIAZZA_UNDER_EAVE_M = 0.30  # it hangs below the main eave, as the pictures draw it
PIAZZA_POST_M = 0.13        # square posts, a hewn or sawn four inches
PIAZZA_RAIL_Z = 0.82        # the rail's top over the deck


def _piazza(b: MeshBuilder, p: LogDwellingParams, x0, y0, x1, y1,
            wall_z: float, conf: float) -> None:
    """A full-front piazza: a plank deck, a row of posts and a shed roof (T-2497).

    It runs the whole log front, which is what "a piazza extending along its front"
    says, and its roof is a separate, flatter plane hung under the main eave rather
    than the main slope carried down — every picture of the Kinzie house draws that
    break. The posts divide the front into equal bays; a rail, when the record asks
    for one, runs between them except in the bay the door opens into. Every number
    here is this module's own (see the dataclass), so the record that turns it on
    carries a liberty for all of them.
    """
    d = p.piazza_depth_m
    yf = y1 + d
    pitch = PIAZZA_PITCH_DEG if p.piazza_pitch_deg is None else p.piazza_pitch_deg
    tp = math.tan(math.radians(pitch))
    swept = p.piazza_roof == "swept"
    if swept:
        plate_z = p.piazza_plate_m
        head = plate_z + d * tp
    else:
        head = wall_z - PIAZZA_UNDER_EAVE_M
        plate_z = head - d * tp
    xm = (x0 + x1) / 2.0

    # the deck, its face against the wall left off (add_box's y0 face)
    b.add_box(x0, y1, 0.0, x1, yf, PIAZZA_DECK_M, conf, M_FRAME, skip=("bottom", "front"))

    # posts, the end ones just in from the corners
    n = p.piazza_posts
    half = PIAZZA_POST_M / 2.0
    py = yf - 0.10
    xs = [x0 + 0.12 + i * (x1 - x0 - 0.24) / (n - 1) for i in range(n)]
    for x in xs:
        b.add_box(x - half, py - half, PIAZZA_DECK_M, x + half, py + half, plate_z - 0.14,
                  conf, M_FRAME, skip=("bottom",))
    # the plate the rafters sit on, post to post
    b.add_box(x0, py - half, plate_z - 0.14, x1, py + half, plate_z, conf, M_FRAME)

    if p.piazza_rail:
        door_bay = next((i for i in range(n - 1) if xs[i] <= xm <= xs[i + 1]), None)
        for i in range(n - 1):
            if i == door_bay:
                continue
            a, c = xs[i] + half, xs[i + 1] - half
            top = PIAZZA_DECK_M + PIAZZA_RAIL_Z
            b.add_box(a, py - 0.035, top - 0.06, c, py + 0.035, top, conf, M_FRAME)
            b.add_box(a, py - 0.03, PIAZZA_DECK_M + 0.08, c, py + 0.03,
                      PIAZZA_DECK_M + 0.13, conf, M_FRAME)
            k = max(1, int((c - a) / 0.16))
            for j in range(1, k):
                u = a + j * (c - a) / k
                b.add_box(u - 0.02, py - 0.02, PIAZZA_DECK_M + 0.13, u + 0.02, py + 0.02,
                          top - 0.06, conf, M_FRAME, skip=("bottom", "top"))

    # the shed roof, overhanging the plate and the gable ends as the main roof does
    rx0, rx1, ry = x0 - 0.25, x1 + 0.25, yf + 0.25
    rz = plate_z - 0.25 * tp
    t = 0.07
    if swept:
        _swept_piazza_roof(b, p, rx0, rx1, y1, yf, ry, rz, plate_z, tp, t, wall_z, conf)
        return
    b.add_poly([(rx0, ry, rz), (rx1, ry, rz), (rx1, y1, head), (rx0, y1, head)], conf, M_ROOF)
    b.add_poly([(rx0, y1, head - t), (rx1, y1, head - t), (rx1, ry, rz - t),
                (rx0, ry, rz - t)], conf, M_ROOF)
    b.add_poly([(rx0, ry, rz - t), (rx1, ry, rz - t), (rx1, ry, rz), (rx0, ry, rz)],
               conf, M_ROOF)
    for x, sgn in ((rx0, -1), (rx1, 1)):
        pts = [(ry, rz - t), (ry, rz), (y1, head), (y1, head - t)]
        if sgn > 0:
            pts.reverse()
        b.add_poly([(x, y, z) for y, z in pts], conf, M_ROOF)


def _end_poly(b: MeshBuilder, x: float, outward: int, pts_yz, conf: float,
              mat: int) -> None:
    """A flat polygon in the y-z plane at `x`, wound to face +x or -x."""
    area = sum(ya * zb - yb * za for (ya, za), (yb, zb)
               in zip(pts_yz, pts_yz[1:] + pts_yz[:1]))
    if (area > 0) != (outward > 0):      # counter-clockwise in (y, z) faces +x
        pts_yz = list(reversed(pts_yz))
    b.add_poly([(x, y, z) for y, z in pts_yz], conf, mat)


def _swept_piazza_roof(b: MeshBuilder, p: LogDwellingParams, rx0, rx1, y1, yf, ry, rz,
                       plate_z, tp, t, wall_z, conf) -> None:
    """The main roof carried down over the piazza at a break (T-2516).

    A flatter plane rises from the plate at the piazza's pitch until it meets the main
    roof's front slope, which it does above the front wall rather than under the eave:
    from afar the two read as one plane run down to the posts, and close to as a break,
    which is what the Kinzie house's pictures draw between them. The main roof is left
    whole beneath it; the part the piazza roof covers cannot be seen, and a board along
    the wall line closes the space between the piazza's ceiling and the main eave, so
    that eave does not show as a ledge under the piazza.
    """
    tm = math.tan(math.radians(p.roof_pitch_deg))
    ye = y1 + 0.25                          # the main roof's front eave edge, at wall_z
    yb = (wall_z + ye * tm - plate_z - yf * tp) / (tm - tp)
    zb = plate_z + (yf - yb) * tp
    if yb >= ye:
        raise ValueError(f"a swept piazza roof from a {plate_z} m plate meets the main "
                         f"roof beyond its eave; lower the pitch or raise the plate")
    yw = ye + 0.01                          # the wall-line board, just proud of the eave
    zw = plate_z + (yf - yw) * tp

    b.add_poly([(rx0, ry, rz), (rx1, ry, rz), (rx1, yb, zb), (rx0, yb, zb)], conf, M_ROOF)
    b.add_poly([(rx0, yw, zw - t), (rx1, yw, zw - t), (rx1, ry, rz - t),
                (rx0, ry, rz - t)], conf, M_ROOF)
    b.add_poly([(rx0, ry, rz - t), (rx1, ry, rz - t), (rx1, ry, rz), (rx0, ry, rz)],
               conf, M_ROOF)
    _panel(b, "y", yw, rx0, rx1, wall_z - 0.18, zw - t, 1, conf, M_FRAME)
    for x, sgn in ((rx0, -1), (rx1, 1)):
        _end_poly(b, x, sgn, [(ry, rz - t), (ry, rz), (yw, zw), (yw, zw - t)], conf, M_ROOF)
        _end_poly(b, x, sgn, [(yw, zw - t), (yw, zw), (yb, zb), (ye, wall_z)], conf, M_ROOF)


# ---------------------------------------------------------------- gable ends

LIGHT_HALF_W = LIGHT_HALF_W_M   # a small sash in a gable end, about two feet wide
LIGHT_HALF_H = LIGHT_HALF_H_M
GABLE_FACE_OUT = 0.25 + 0.04    # add_gable_roof's overhang, where it closes the gable, and
#                                 0.04 m off that board face, so the sash, which the kit
#                                 sets back into a log wall's relief, stands in front of it


def _end_openings(b: MeshBuilder, p: LogDwellingParams, x0, y0, x1, y1,
                  wall_z: float) -> None:
    """Doors, windows and small lights in the gable ends (T-2516).

    The archetype's rule is that a log gable end is not pierced (`_core_openings`),
    and it still is everywhere a record does not say otherwise: these are built only
    where a record states them, because a picture draws them. A door takes the front
    door's size and a window the front windows' size and band, so the end matches the
    front it turns the corner from. A light above the eave is in the GABLE, which
    `add_gable_roof` closes with a board triangle flush with its rake, 0.25 m outboard
    of the log end, so it is set on that face; a light below the eave is in the log
    wall like any window.
    """
    plane = {"+x": (x1, 1), "-x": (x0, -1)}
    rects = core_front_rects(p)
    win = next(r for r in rects if r[0] == "window")
    whalf, wz0, wz1 = (win[2] - win[1]) / 2.0, win[3], win[4]
    c = p.conf("end_openings", "reconstructed")
    for end, kind, at, z in p.end_openings:
        x, out = plane[end]
        yc = y0 + at * (y1 - y0)
        if kind in ("light", "hatch"):
            if z - LIGHT_HALF_H >= wall_z:
                x += out * GABLE_FACE_OUT
            if kind == "hatch":
                # A boarded proxy for the painting's framed rectangle, not a
                # claim that glass is absent or that its closure is documented.
                w = openings.Wall("x", x, out, RELIEF_M)
                k = _kit(b)
                openings.surround(b, w, yc - LIGHT_HALF_W, yc + LIGHT_HALF_W,
                                  z - LIGHT_HALF_H, z + LIGHT_HALF_H, c, k,
                                  sill=False, cap=False, casing_w=0.07, head_w=0.08, proud=0.03)
                openings.board_shutter(b, w, yc - LIGHT_HALF_W, yc + LIGHT_HALF_W,
                                      z - LIGHT_HALF_H, z + LIGHT_HALF_H, c, k)
            else:
                _opening(b, "x", x, yc - LIGHT_HALF_W, yc + LIGHT_HALF_W, z - LIGHT_HALF_H,
                         z + LIGHT_HALF_H, out, c, shutters=False)
        elif kind == "door":
            _opening(b, "x", x, yc - _DOOR_HALF, yc + _DOOR_HALF, 0.02, 1.95, out, c,
                     kind="door")
        else:
            z0, z1 = (wz0, wz1) if z is None else (z - (wz1 - wz0) / 2.0, z + (wz1 - wz0) / 2.0)
            _opening(b, "x", x, yc - whalf, yc + whalf, z0, z1, out, c, shutters=False)


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

    mixed_cladding = p.frame_addition_cladding == "log_lower_vertical_upper"
    if mixed_cladding:
        c_finish = p.conf("frame_addition_cladding", "reconstructed")
        split = az / 2.0
        hewn_log_wall(b, ax0, ay0, ax1, ay1, 0.0, split, c_finish, M_LOG, M_CHINK,
                      skip=("bottom", "top"))
        b.add_box(ax0, ay0, split, ax1, ay1, az, c_finish, M_FRAME,
                  skip=("bottom", "top"))
        _vertical_addition_edges(b, ax0, ay0, ax1, ay1, split, az, 1.0)
    else:
        b.add_box(ax0, ay0, 0.0, ax1, ay1, az, c, M_FRAME, skip=("bottom", "top"))
        _clapboard(b, ax0, ay0, ax1, ay1, az, c_clad)
    # An end addition abuts the log core, so its roof gets no overhang on that side —
    # `add_gable_roof` grows uniformly, and 0.25 m of eave driven into the core's roof
    # plane is a z-fighting stripe right down the most visible surface of the building.
    rx0 = ax0 + 0.26 if p.frame_addition_side == "end" else ax0
    roof_conf = c if p.frame_addition_roof_pitch_deg is None else max(c, p.conf("frame_addition_roof_pitch_deg"))
    add_ridge_z = b.add_gable_roof(rx0, ay0, ax1, ay1, az, p.resolved_addition_roof_pitch_deg, roof_conf, M_ROOF,
                                   ridge_along_x=True)
    if mixed_cladding:
        _vertical_addition_gables(b, rx0, ay0, ax1, ay1, az, add_ridge_z, c_finish)

    rel = 0.026                    # clapboard lip, not log relief
    # THE ADDITION'S FACADE IS THE PARAMS MODULE'S SET-OUT (T-0520), door and
    # windows both, in the order they are drawn in — and it is the same list the
    # signage layer reads when a front addition is the wall a visitor faces.
    front_rects = addition_front_rects(p)
    for kind, u0, u1, z0, z1 in front_rects:
        _opening(b, "y", ay1, u0, u1, z0, z1, 1, c_fen, kind=kind, relief=rel,
                 frame_wall=True)
    # The gable end that is not buried in the log core gets one window per storey.
    # An END addition's front wall carries exactly two windows a storey and no door
    # (the core keeps that), so the storey's band is the pair at 2*story — read from
    # the facade rather than recomputed, which is the whole point of T-0520.
    if p.frame_addition_side == "end":
        yc = (ay0 + ay1) / 2.0
        for story in range(p.frame_addition_stories):
            if p.frame_addition_front_set_out is None:
                z0, z1 = front_rects[2 * story][3:]
            else:
                lo, hi = story*p.addition_height_m/p.frame_addition_stories, (story+1)*p.addition_height_m/p.frame_addition_stories
                rect = next(r for r in front_rects if r[0] == "window" and lo <= r[3] < r[4] <= hi)
                z0, z1 = rect[3:]
            _opening(b, "x", ax1, yc - ADDITION_WIN_HALF_M, yc + ADDITION_WIN_HALF_M,
                     z0, z1, 1, c_fen, relief=rel, frame_wall=True)
    return add_ridge_z


def _vertical_addition_edges(b: MeshBuilder, x0: float, y0: float, x1: float,
                             y1: float, bottom: float, top: float, conf: float) -> None:
    """Reconstructed dark joint proxy, not measured gaps or applied battens.

    The first same-material 12 mm edges vanished in the actual neutral review.
    Reuse the log slot for 24 mm contrast strips with 4 mm relief, explicitly
    a readable joint depiction, not a claim about historic gap/section sizes.
    """
    spacing, half_edge, proud = 0.24, 0.012, 0.004
    for axis, lo, hi in (("x", x0, x1), ("y", y0, y1)):
        n = max(1, round((hi - lo) / spacing))
        for k in range(1, n):
            at = lo + (hi - lo) * k / n
            if axis == "x":
                for plane, out in ((y0, -1), (y1, 1)):
                    ya, yb = sorted((plane, plane + out * proud))
                    b.add_box(at - half_edge, ya, bottom, at + half_edge, yb, top,
                              conf, M_LOG, skip=("bottom", "top"))
            else:
                for plane, out in ((x0, -1), (x1, 1)):
                    xa, xb = sorted((plane, plane + out * proud))
                    b.add_box(xa, at - half_edge, bottom, xb, at + half_edge, top,
                              conf, M_LOG, skip=("bottom", "top"))


def _vertical_addition_gables(b: MeshBuilder, x0: float, y0: float, x1: float,
                             y1: float, eave: float, ridge: float, conf: float) -> None:
    """Board faces on the roof builder's closed gable planes, not hidden behind them."""
    oh, proud, half_edge = 0.25, 0.004, 0.012
    lo, hi = y0 - oh, y1 + oh
    mid = (lo + hi) / 2.0
    n = max(1, round((hi - lo) / 0.24))
    for plane, out in ((x0 - oh, -1), (x1 + oh, 1)):
        face = plane + out * proud
        pts = [(face, lo, eave), (face, mid, ridge), (face, hi, eave)]
        b.add_poly(pts if out < 0 else list(reversed(pts)), conf, M_FRAME)
        for k in range(1, n):
            at = lo + (hi - lo) * k / n
            run = min(at - half_edge - lo, hi - at - half_edge)
            top = eave + (ridge - eave) * run / ((hi - lo) / 2.0) - 0.02
            if top <= eave:
                continue
            xa, xb = sorted((face, face + out * 0.004))
            b.add_box(xa, at - half_edge, eave, xb, at + half_edge, top,
                      1.0, M_LOG, skip=("bottom", "top"))


#: The lean-to's plank battens (T-2511): the vertical strokes the Currey plate draws
#: on its gable, at about a board's width apart, standing just proud of the wall.
LEAN_TO_BATTEN_M = 0.30
LEAN_TO_BATTEN_W = 0.06


def _lean_to(b: MeshBuilder, p: LogDwellingParams, conf: float, c_roof: float) -> None:
    """A low plank shed against the stack's gable, gable to the street (T-2511).

    Its walls are the frame slot — boards are what `frame_paint` dresses — and its
    gable roof runs its ridge across the house's, so the end a visitor sees from the
    street is a gable, as the plate draws it. A board door is hung in that gable.
    """
    lx0, ly0, lx1, ly1 = lean_to_extent(p)
    wz = p.lean_to_wall_m
    # The face against the gable is not built: it would lie in the log wall.
    inner = "left" if p.chimney_end == "max" else "right"
    b.add_box(lx0, ly0, 0.0, lx1, ly1, wz, conf, M_FRAME, skip=("bottom", "top", inner))
    pitch = p.roof_pitch_deg if p.lean_to_pitch_deg is None else p.lean_to_pitch_deg
    b.add_gable_roof(lx0, ly0, lx1, ly1, wz, pitch, c_roof, M_ROOF, ridge_along_x=False)
    # The front gable's boards, eave to grade and up into the triangle.
    xm = (lx0 + lx1) / 2.0
    half = (lx1 - lx0) / 2.0
    n = int((lx1 - lx0) / LEAN_TO_BATTEN_M)
    for k in range(1, n):
        x = lx0 + k * (lx1 - lx0) / n
        top = wz + (half - abs(x - xm)) * math.tan(math.radians(pitch)) - 0.04
        b.add_box(x - LEAN_TO_BATTEN_W / 2, ly1, 0.0, x + LEAN_TO_BATTEN_W / 2,
                  ly1 + 0.02, top, conf, M_FRAME, skip=("bottom",))
    _opening(b, "y", ly1 + 0.02, xm - 0.42, xm + 0.42, 0.02, min(1.8, wz - 0.1), 1,
             conf, kind="door", relief=0.026, frame_wall=False)


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
      gable by default, mirroring the core's. A stated frame_addition_ridge_stack
      instead puts its short flue through the addition's own ridge. That roof is built ridge-along-x
      (`_frame_addition`), so its gable ends are always its +/-x faces.
    - With no addition, a second stack goes against the core's other gable, which is
      the other end of the one element there is. No record in the dataset asks for
      this case yet.

    docs/LIBERTIES.md L26 owns all of it.
    """
    if p.chimneys <= 0:
        return
    if p.chimney_ridge_at is not None:
        for f in p.chimney_ridge_at:
            _ridge_stack(b, p, cx0, cy0, cx1, cy1, ridge_z, f, conf, mat)
        return
    axis = _gable_axis(p, cx0, cy0, cx1, cy1)
    # `chimney_end` (T-2511) turns the first stack to the other gable where a record's
    # picture puts it there; "min" is the end it has always stood on.
    first_min = p.chimney_end == "min"
    _stack(b, cx0, cy0, cx1, cy1, ridge_z, conf, mat, at_min=first_min, gable_axis=axis,
           cross=p.chimney_cross_m, head_z=p.chimney_head_m)
    if p.chimneys < 2:
        return
    if p.frame_addition and add_ridge_z is not None:
        ax0, ay0, ax1, ay1 = addition_extent(p)
        if p.frame_addition_ridge_stack is None:
            _stack(b, ax0, ay0, ax1, ay1, add_ridge_z, conf, mat, at_min=False,
                   gable_axis="x")
        else:
            # The addition always runs its ridge along x, independently of the
            # log core's axis. Only its existing second stack changes disposition.
            f, width, head = p.frame_addition_ridge_stack
            half = width / 2.0
            rx0 = ax0 + 0.26 if p.frame_addition_side == "end" else ax0
            x = rx0 + f * (ax1 - rx0)
            y = (ay0 + ay1) / 2.0
            foot = add_ridge_z - half * math.tan(math.radians(p.resolved_addition_roof_pitch_deg)) - 0.25
            b.add_box(x - half, y - half, foot, x + half, y + half,
                      add_ridge_z + head,
                      p.worst_conf("chimneys", "frame_addition_ridge_stack"), mat,
                      skip=("bottom",))
    else:
        _stack(b, cx0, cy0, cx1, cy1, ridge_z, conf, mat, at_min=not first_min,
               gable_axis=axis,
               cross=_facade_stack_cross(cx1 - cx0) if axis == "y" else 0.0)


def _ridge_stack(b: MeshBuilder, p: LogDwellingParams, x0, y0, x1, y1, ridge_z: float,
                 f: float, conf: float, mat: int) -> None:
    """One stack rising through the ridge at fraction `f` of it (T-2497).

    Straddling the ridge, its foot below the roof's lowest point where it meets the
    shaft, so no gap shows on either slope, and its head the archetype's usual height
    over the ridge. Placed where a record says a picture puts it, never by default.
    """
    half = _STACK_HALF if p.ridge_stack_w_m is None else p.ridge_stack_w_m / 2.0
    if resolved_core_ridge_axis(p) == "x":
        c = x0 + f * (x1 - x0)
        ym = (y0 + y1) / 2.0
        bx = (c - half, ym - half, c + half, ym + half)
    else:
        c = y0 + f * (y1 - y0)
        xm = (x0 + x1) / 2.0
        bx = (xm - half, c - half, xm + half, c + half)
    run = half * math.tan(math.radians(p.roof_pitch_deg))
    head = 0.95 if p.ridge_stack_head_m is None else p.ridge_stack_head_m
    shaft_top = ridge_z + head - (p.ridge_stack_cap_m[1] if p.ridge_stack_cap_m is not None else 0.)
    b.add_box(bx[0], bx[1], ridge_z - run - 0.25, bx[2], bx[3], shaft_top, conf, mat,
              skip=("bottom", "top") if p.ridge_stack_cap_m is not None else ("bottom",))

    if p.ridge_stack_cap_m is not None:
        projection, thickness = p.ridge_stack_cap_m
        # Cap replaces the top band of the shaft: the stated overall head
        # height stays fixed. All unseen section dimensions are reconstructed.
        b.add_box(bx[0]-projection, bx[1]-projection, ridge_z+head-thickness,
                  bx[2]+projection, bx[3]+projection, ridge_z+head,
                  p.conf("ridge_stack_cap_m", "reconstructed"), mat)


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
           at_min: bool, gable_axis: str = "x", cross: float = 0.0,
           head_z: float | None = None) -> None:
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

    # `head_z` (T-2511) is a stated head over grade; None is 0.72 m over the ridge.
    top = ridge_z + 0.72 if head_z is None else head_z
    sg0, sg1 = span(0.08, 0.72)
    box(sg0, sg1, cc - half, cc + half, 0.0, top - 0.17)
    # a slight corbel at the head, so it reads as a chimney rather than a post
    hg0, hg1 = span(0.12, 0.82)
    box(hg0, hg1, cc - half - 0.08, cc + half + 0.08, top - 0.17, top)


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


def _compound(b: MeshBuilder, p: LogDwellingParams) -> None:
    """First compound log massing; joints and all set-out are reconstructed.

    Roof rectangles may extend over adjoining rooms: their intersecting surfaces
    conceal the internal gable caps. No valley flashing or interior is claimed.
    All emitted faces use reconstructed confidence because the subdivision,
    roof intersections and openings have no measured elevation.
    """
    roofs = []
    for r, roof, axis, opening in p.compound_parts:
        x0,y0,x1,y1 = r
        hewn_log_wall(b,x0,y0,x1,y1,0.0,p.wall_height_m,1.0,M_LOG,M_CHINK,
                      skip=("bottom","top"))
        ridge = b.add_gable_roof(*roof,p.wall_height_m,p.roof_pitch_deg,1.0,M_ROOF,
                                  ridge_along_x=axis == "x")
        roofs.append(ridge)
    for plane,kind,u0,u1,z0,z1 in compound_front_rects(p):
        _opening(b,"y",plane,u0,u1,z0,z1,+1,1.0,kind=kind)
    # Retain the recorded count, but choose the outermost rooms for the two
    # stacks. Their axis, position, section and head remain reconstructed.
    if p.chimneys:
        indices=[min(range(len(p.compound_parts)),key=lambda i:p.compound_parts[i][0][0])]
        if p.chimneys == 2:
            indices.append(max(range(len(p.compound_parts)),key=lambda i:p.compound_parts[i][0][2]))
        for n,i in enumerate(indices):
            r,roof,axis,_=p.compound_parts[i]
            _stack(b,*r,roofs[i],1.0,M_CHIMNEY_AFTER_SIGN,gable_axis=axis,at_min=n == 0,
                   head_z=p.chimney_head_m)


def _clip_plan(poly, a, c, bound, keep_less=True):
    """Clip a convex XY roof cell by a*x+c*y<=bound (or its opposite)."""
    out=[]
    for u,v in zip(poly,poly[1:]+poly[:1]):
        du=a*u[0]+c*u[1]-bound;dv=a*v[0]+c*v[1]-bound
        iu=du<=1e-10 if keep_less else du>=-1e-10
        iv=dv<=1e-10 if keep_less else dv>=-1e-10
        if iu:out.append(u)
        if iu!=iv:
            t=du/(du-dv);out.append((u[0]+t*(v[0]-u[0]),u[1]+t*(v[1]-u[1])))
    clean=[]
    for pt in out:
        if not clean or abs(pt[0]-clean[-1][0])+abs(pt[1]-clean[-1][1])>1e-9:clean.append(pt)
    if len(clean)>1 and abs(clean[0][0]-clean[-1][0])+abs(clean[0][1]-clean[-1][1])<1e-9:clean.pop()
    return clean


def _elbow_roof(b,p):
    """Upper envelope at a true L corner; no buried intersecting roof planes.

    First trial uses flush roof edges at the declared walls. Equal spans keep
    both ridges equal. Eave/valley/flashing details remain reconstructed.
    """
    cw=core_extent(p)[2];D=p.depth_m;W=p.width_m;h=p.wall_height_m;t=math.tan(math.radians(p.roof_pitch_deg))
    o=p.compound_roof_overhang_m
    def emit(poly,z):
        if len(poly)>=3:
            pts=[(x,y,z(x,y)) for x,y in poly]
            b.add_poly(pts,1.,M_ROOF)
            if o>0:b.add_poly([(x,y,z-.05) for x,y,z in reversed(pts)],1.,M_ROOF)
    def rect(x0,y0,x1,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    emit(rect(-o,-o,cw/2,D+o),lambda x,y:h+x*t)
    emit(rect(cw/2,cw+o,cw+o,D+o),lambda x,y:h+(cw-x)*t)
    # Core right slope survives above each cross-roof half.
    emit(_clip_plan(rect(cw/2,-o,cw+o,cw/2),1,1,cw),lambda x,y:h+(cw-x)*t)
    emit(_clip_plan(rect(cw/2,cw/2,cw+o,cw+o),1,-1,0),lambda x,y:h+(cw-x)*t)
    # Cross roof starts at core ridge and ends at its outward +X gable.
    emit(_clip_plan(rect(cw/2,-o,cw+o,cw/2),1,1,cw,False),lambda x,y:h+y*t)
    emit(rect(cw+o,-o,W+o,cw/2),lambda x,y:h+y*t)
    emit(_clip_plan(rect(cw/2,cw/2,cw+o,cw+o),1,-1,0,False),lambda x,y:h+(cw-y)*t)
    emit(rect(cw+o,cw/2,W+o,cw+o),lambda x,y:h+(cw-y)*t)
    z=h+cw/2*t
    # +Y and +X pictured ends plus unseen rear core cap; CCW outward.
    if p.compound_log_profile == "rounded_relief":
        _rounded_compound_gable(b,"y",D,0,cw,h,z,+1)
        _rounded_compound_gable(b,"y",0,0,cw,h,z,-1)
        _rounded_compound_gable(b,"x",W,0,cw,h,z,+1)
    elif p.compound_wall_cladding == "log_courses":
        _log_course_gable(b,"y",D,0,cw,h,z,+1)
        _log_course_gable(b,"y",0,0,cw,h,z,-1)
        _log_course_gable(b,"x",W,0,cw,h,z,+1)
    else:
        b.add_poly([(cw,D,h),(0,D,h),(cw/2,D,z)],1.,M_ROOF)
        b.add_poly([(0,0,h),(cw,0,h),(cw/2,0,z)],1.,M_ROOF)
        b.add_poly([(W,0,h),(W,cw,h),(W,cw/2,z)],1.,M_ROOF)
    if o>0:
        # Reconstructed50mm edge, not a source-measured board or thickness.
        outline=[(-o,-o),(cw/2,-o),(cw+o,-o),(W+o,-o),(W+o,cw/2),(W+o,cw+o),(cw+o,cw+o),(cw+o,D+o),(cw/2,D+o),(-o,D+o)]
        def top(x,y):
            za=h+min(x,cw-x)*t if x<=cw+o+1e-9 else -math.inf
            zb=h+min(y,cw-y)*t if x>=cw/2-1e-9 and y<=cw+o+1e-9 else -math.inf
            return max(za,zb)
        for (x,y),(xx,yy) in zip(outline,outline[1:]+outline[:1]):
            za,zb=top(x,y),top(xx,yy)
            b.add_poly([(x,y,za),(x,y,za-.05),(xx,yy,zb-.05),(xx,yy,zb)],1.,M_ROOF)
    return z


def _elbow(b,p):
    """Bounded source-backed L massing; exact plan and all set-out reconstructed."""
    for i,(r,roof,axis,openings_) in enumerate(p.compound_parts):
        log_face=i==0 or p.compound_wall_cladding == "log_courses"
        if p.compound_log_profile == "rounded_relief":
            _rounded_compound_wall(b,r,p.wall_height_m)
        elif log_face:hewn_log_wall(b,*r,0.,p.wall_height_m,1.,M_LOG,M_CHINK,skip=("bottom","top"))
        else:
            b.add_box(r[0],r[1],0.,r[2],r[3],p.wall_height_m,1.,M_FRAME,skip=("bottom","top"))
            _clapboard(b,*r,p.wall_height_m,1.)
        if p.compound_door_state == "recess":
            for face in {v[0] for v in openings_ if v[1]=="door"}:
                axis_="x" if face=="+x" else "y";plane=r[2] if axis_=="x" else r[3]
                _cut_door_recesses(b,axis_,plane,[(k,u0,u1,z0,z1) for f,k,u0,u1,z0,z1 in openings_ if f==face],skin_back_m=.30)
        for face,kind,u0,u1,z0,z1 in openings_:
            axis_="x" if face=="+x" else "y";plane=r[2] if axis_=="x" else r[3]
            _opening(b,axis_,plane,u0,u1,z0,z1,1,1.,kind=kind,frame_wall=not log_face,relief=RELIEF_M if log_face else .026,
                     door_state="recess" if p.compound_door_state=="recess" and kind=="door" else "closed")
    ridge=_elbow_roof(b,p)
    _ridge_stack(b,p,*core_extent(p),ridge,p.chimney_ridge_at[0],1.,M_CHIMNEY_AFTER_PAINT if p.sign and p.sign_device else M_CHIMNEY_AFTER_SIGN)
    if p.roof_pipe is not None:
        at,diameter,head=p.roof_pipe;x=core_extent(p)[2]/2;y=at*p.depth_m;r=diameter/2
        low=ridge-r*math.tan(math.radians(p.roof_pitch_deg))-.1;top=ridge+head
        ring=[(x+r*math.cos(k*math.tau/8),y+r*math.sin(k*math.tau/8)) for k in range(8)]
        for (xa,ya),(xb,yb) in zip(ring,ring[1:]+ring[:1]):b.add_poly([(xa,ya,low),(xb,yb,low),(xb,yb,top),(xa,ya,top)],1.,M_DARK)
        b.add_poly([(xa,ya,top) for xa,ya in ring],1.,M_DARK)
    if p.sign:
        # Existing kit retained; its source position/height/lean still differs.
        if p.sign_pole_set_out is not None:_posed_sign_pole(b,p)
        elif p.sign_mount == "sapling_pole":_sign_pole(b,p,ridge,p.worst_conf("sign","sign_mount"),p.conf("sign"),p.conf("sign_device"))
        else:_sign(b,p,p.conf("sign"))


def _horizontal_end_courses(b, x, y0, y1, z0, z1, conf):
    """Pictured horizontal end courses, without asserting log versus board fabric.

    The 200mm rhythm, 8mm shadow joints and 12mm relief are reconstructed first
    fits. The +X surface remains behind the existing framed hatch at x+40mm.
    """
    mid=(y0+y1)/2;half=(y1-y0)/2;rise=z1-z0
    b.add_poly([(x,y0,z0),(x,y1,z0),(x,mid,z1)],conf,M_FRAME)
    course=.20;gap=.008;proud=.012
    for i in range(math.floor(z0/course),math.ceil(z1/course)):
        low=max(z0,i*course);high=min(z1,(i+1)*course-gap)
        if high <= low:
            continue
        lh=half*(1-(low-z0)/rise);hh=half*(1-(high-z0)/rise)
        b.add_poly([(x+proud,mid-lh,low),(x+proud,mid+lh,low),
                    (x+proud,mid+hh,high),(x+proud,mid-hh,high)],1.,M_FRAME)
        # Bottom return gives each horizontal joint geometric relief.
        b.add_poly([(x,mid-lh,low),(x,mid+lh,low),
                    (x+proud,mid+lh,low),(x+proud,mid-lh,low)],1.,M_FRAME)


def _log_course_gable(b,axis,plane,u0,u1,z0,z1,outward):
    """Triangle and horizontal course relief; every chosen dimension reconstructed.

    The inferred source category is log coursing, not literal measured wood/chink,
    exact colour, log section or joinery. Continue the existing340mm rhythm into
    the triangular face without changing the shared logwork default elsewhere.
    """
    mid=(u0+u1)/2;half=(u1-u0)/2;rise=z1-z0
    def xyz(u,z,proud=0):return (u,plane+outward*proud,z) if axis=="y" else (plane+outward*proud,u,z)
    def emit(pts,mat):
        # +Y front has decreasingU, +X front increasingU when seen from outside.
        reverse=(axis=="y") == (outward>0)
        b.add_poly(list(reversed(pts)) if reverse else pts,1.,mat)
    emit([xyz(u0,z0),xyz(u1,z0),xyz(mid,z1)],M_LOG)
    za=math.ceil(z0/.34)*.34
    while za<z1-.04:
        low=max(z0,za-.0275);high=min(z1,za+.0275)
        lohalf=half*(1-(low-z0)/rise);hihalf=half*(1-(high-z0)/rise)
        pts=[xyz(mid-lohalf,low,RELIEF_M),xyz(mid+lohalf,low,RELIEF_M),xyz(mid+hihalf,high,RELIEF_M),xyz(mid-hihalf,high,RELIEF_M)]
        emit(pts,M_CHINK)
        # Tiny bottom return makes a geometric relief rather than a painted line.
        emit([xyz(mid-lohalf,low),xyz(mid+lohalf,low),xyz(mid+lohalf,low,RELIEF_M),xyz(mid-lohalf,low,RELIEF_M)],M_CHINK)
        za+=.34


def _posed_sign_pole(b,p):
    """Source-bounded pose; all set-out, sections and device remain reconstructed."""
    (bx,by),(tx,ty,top),arm,(bw,bh),drop=p.sign_pole_set_out
    def add(a,z):return tuple(x+y for x,y in zip(a,z))
    def scale(a,s):return tuple(x*s for x in a)
    def dot(a,z):return sum(x*y for x,y in zip(a,z))
    def cross(a,z):return (a[1]*z[2]-a[2]*z[1],a[2]*z[0]-a[0]*z[2],a[0]*z[1]-a[1]*z[0])
    def unit(a):return scale(a,1/math.sqrt(dot(a,a)))
    def polept(z):return (bx+(tx-bx)*z/top,by+(ty-by)*z/top,z)
    def member(a,z,r,sides=8,mat=M_LOG):
        v=unit(tuple(y-x for x,y in zip(a,z)));q=unit(cross(v,(0,0,1) if abs(v[2])<.95 else (0,1,0)));w=cross(v,q)
        ring=[add(scale(q,r*math.cos(k*math.tau/sides)),scale(w,r*math.sin(k*math.tau/sides))) for k in range(sides)]
        for i in range(sides):j=(i+1)%sides;b.add_poly([add(a,ring[i]),add(a,ring[j]),add(z,ring[j]),add(z,ring[i])],1.,mat)
        b.add_poly([add(a,q) for q in reversed(ring)],1.,mat);b.add_poly([add(z,q) for q in ring],1.,mat)
    member(polept(-POLE_SET_M),polept(top*.56),POLE_BUTT_R)
    member(polept(top*.56),polept(top),POLE_HEAD_R)
    origin=polept(top-.4);e=unit(arm);up=unit(add((0,0,1),scale(e,-e[2])));normal=cross(e,up)
    member(add(origin,scale(e,-.35)),add(origin,arm),POLE_ARM_R,6)
    member(polept(top-1.6),add(origin,scale(arm,.45)),.035,6)
    centre=add(add(origin,scale(arm,.65)),scale(up,-drop))
    bt=SIGN_BOARD[2]
    def pt(u,v,n=0):return add(add(add(centre,scale(e,u)),scale(up,v)),scale(normal,n))
    # Slender reconstructed iron hangers; no literal hinge pattern is claimed.
    for u in (-bw*.34,bw*.34):member(pt(u,0),pt(u,drop+.035),.018,6,M_DARK)
    front=[pt(-bw/2,-bh,bt/2),pt(bw/2,-bh,bt/2),pt(bw/2,0,bt/2),pt(-bw/2,0,bt/2)]
    back=[pt(-bw/2,-bh,-bt/2),pt(bw/2,-bh,-bt/2),pt(bw/2,0,-bt/2),pt(-bw/2,0,-bt/2)]
    b.add_poly(front,1.,M_SIGN);b.add_poly(list(reversed(back)),1.,M_SIGN)
    for i in range(4):j=(i+1)%4;b.add_poly([back[i],back[j],front[j],front[i]],1.,M_SIGN)
    if p.sign_device == "wolf":
        dw=bw*DEVICE_FRACTION[0];dh=min(bh*DEVICE_FRACTION[1],dw/_WOLF_ASPECT);dw=dh*_WOLF_ASPECT
        uv=[(-dw/2+u*dw,-bh+(bh-dh)/2+v*dh) for u,v in _WOLF_UV]
        for side in (-1,1):
            pts=[pt(u,v,side*(bt/2+DEVICE_PROUD_M)) for u,v in uv]
            b.add_poly(pts if side>0 else list(reversed(pts)),1.,M_PAINT)


def _rounded_log_face(b,axis,plane,u0,u1,z0,z1,outward,gable=None):
    """Small rounded relief and thin inset joints, not literal measured log fabric.

    Chosen300mm rhythm,20mm dark gap and38..48mm curved relief replace the pale
    strip proxy only on opt-in compounds. Six angular panels per log give normals
    for shading under the same light/palette; stable seeded relief avoids a perfect
    repeated board face. No historic colour/woodgrain or exact section is claimed.
    """
    course=.30;gap=.020
    def xyz(u,z,proud=0):return (u,plane+outward*proud,z) if axis=="y" else (plane+outward*proud,u,z)
    def widths(z):
        if gable is None:return u0,u1
        mid=(u0+u1)/2;half=(u1-u0)/2*(1-(z-z0)/(z1-z0));return mid-half,mid+half
    def emit(pts):
        clean=[]
        for v in pts:
            if not clean or sum((v[k]-clean[-1][k])**2 for k in range(3))>1e-20:clean.append(v)
        if len(clean)>1 and sum((clean[0][k]-clean[-1][k])**2 for k in range(3))<1e-20:clean.pop()
        if len(clean)<3:return
        reverse=(axis=="y") == (outward>0)
        b.add_poly(list(reversed(clean)) if reverse else clean,1.,M_LOG)
    for i in range(math.floor(z0/course),math.ceil(z1/course)):
        low=max(z0,i*course+gap/2);high=min(z1,(i+1)*course-gap/2)
        if high<=low:continue
        mid=(i+.5)*course;radius=(course-gap)/2
        # Identity uses the official asset key via b.name; all choices reconstructed.
        relief=.038+.010*openings.deal(f"{b.name}|rounded|{axis}|{plane:.3f}|{i}",101)/100
        theta0=math.asin(max(-1.,min(1.,(low-mid)/radius)));theta1=math.asin(max(-1.,min(1.,(high-mid)/radius)))
        for k in range(6):
            a=theta0+(theta1-theta0)*k/6;c=theta0+(theta1-theta0)*(k+1)/6
            za,zb=mid+radius*math.sin(a),mid+radius*math.sin(c);pa,pb=relief*math.cos(a),relief*math.cos(c)
            ua,va=widths(za);ub,vb=widths(zb)
            emit([xyz(ua,za,pa),xyz(va,za,pa),xyz(vb,zb,pb),xyz(ub,zb,pb)])


def _rounded_compound_wall(b,r,height):
    x0,y0,x1,y1=r
    # Dark backing is15mm behind the physical face, visible only in thin joints.
    # It is a shadow/recess proxy using the existing palette, not black painted clay.
    b.add_box(x0+.015,y0+.015,0.,x1-.015,y1-.015,height,1.,M_DARK,skip=("bottom","top"))
    for axis,plane,u0,u1,outward in [("y",y1,x0,x1,1),("y",y0,x0,x1,-1),("x",x1,y0,y1,1),("x",x0,y0,y1,-1)]:
        _rounded_log_face(b,axis,plane,u0,u1,0.,height,outward)


def _rounded_compound_gable(b,axis,plane,u0,u1,z0,z1,outward):
    mid=(u0+u1)/2;back=plane-outward*.015
    pts=[(u0,back,z0),(u1,back,z0),(mid,back,z1)] if axis=="y" else [(back,u0,z0),(back,u1,z0),(back,mid,z1)]
    reverse=(axis=="y") == (outward>0)
    b.add_poly(list(reversed(pts)) if reverse else pts,1.,M_DARK)
    _rounded_log_face(b,axis,plane,u0,u1,z0,z1,outward,gable=True)
