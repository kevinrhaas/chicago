"""outbuilding — the stable, shed, barn, smokehouse, privy, crib and woodshed family.

A frontier town is mostly outbuildings. The 1835 scene currently holds eight buildings,
all of them public houses, stores or a bridge, and behind every one of them the sources
put a stable, a yard, a pen or a shed that nothing here can build — see
`outbuilding_params` for the attested list and its citations, and docs/LIBERTIES.md L10
for the one the project has already had to admit to in writing.

**This is a family, not a shape**, and the module is organised around the three things
that differ between a privy and a livery stable rather than around one building with
options bolted on:

- **the wall** — hewn log courses (`common/logwork`, so a log shed and a log cabin are
  visibly the same trade), sawn boards nailed up vertically with the gaps showing, or
  boards laid horizontally on a light frame;
- **the top line** — every elevation carries a `_top_z` profile, so an eave wall, a
  gable end and the trapezoid side of a shed roof are one piece of code and the roof
  meets the wall exactly instead of approximately;
- **the opening** — a doorway sized by what has to get through it, cut out of the
  boarding rather than pasted onto it, and posts-and-air where a side is open.

**It is deliberately crude, and the crudeness is geometry rather than a texture.** These
are not small houses. Boards are of uneven width, spaced with gaps you can see daylight
through, and do not all reach the ground; the wall behind them is dark, so the gaps read
as gaps; the roof is boards, not shingles; there is no paint by default, no clapboard
rhythm, no glazing anywhere, and at most one small unglazed vent. The failure mode this
is written against is a neat little cottage: the first thing that makes a shed a shed is
that it was built in a day by someone who was not a joiner.

**The irregularity is deterministic.** `_jit` is a tiny integer hash seeded from the
building's own dimensions and the elevation, not a random number generator, because
`generators/mesh_inputs.py` defines freshness on inputs and a mesh that differs between
two runs of the same parameters would make every outbuilding permanently stale.

**Orientation.** The facade — the `front` side — faces NORTH at rotation_deg 0, per
docs/GLB-CONTRACT.md. In Blender that is the +y face, because the exporter's
`export_yup=True` maps Blender +Y to glTF -Z. The door defaults there. Getting this
wrong is a silent error, so it is stated here as well as in the contract.

**A note on face winding.** Every polygon in this module is emitted through `_face` or
`_prism`, which take their points in the elevation's own (u, z) plane and flip the order
for the two elevations whose local frame is left-handed (`front` and `left`). Blender's
exporter writes `doubleSided: true` for a default material, so a reversed face is
invisible today — but the contract says counter-clockwise and outward, and a renderer
that ever enables culling would find holes rather than a bug report.
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
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.outbuilding_params import (  # noqa: E402
    DOOR_JAMB_M, OutbuildingParams, boarding_holes, eave_overhang_m, loft_rect,
    vent_rect,
)

# Materials are indices into the list passed to to_object(), in this order.
M_LOG, M_CHINK, M_BOARD, M_ROOF, M_DARK, M_TIMBER = 0, 1, 2, 3, 4, 5

# Sawn boards left to weather. NOT the taverns' unpainted brown: bare sawn softwood on
# a north-facing wall silvers off within a season or two, and if a shed carried the
# same colour as an unpainted clapboard tavern the two would read as the same building
# at a distance — which is exactly the failure this archetype exists to avoid. That
# argument now lives on the sheet as the `weathered_board` finish (T-0007) and this
# name is kept pointing at it, because the argument is about outbuildings and a reader
# of this module should meet it here. Linear, like every other colour in this project.
WEATHERED_BOARD_RGBA = materials.FINISHES["weathered_board"].rgba
# What you see through a gap between boards, through the vent, and inside an open bay.
# Near-black rather than black: an interior in daylight is dark, not a hole in the world.
# That argument is now the sheet's `DARK` row and it is the TOWN's, not this
# archetype's: T-0126 converged the frame dwellings', the log cabins', the fort's and
# the stockade's openings onto this colour and this roughness rather than the other way
# about, so nothing here changes and 170 slots elsewhere came to meet it.
INTERIOR_RGBA = materials.DARK.rgba
# Heavy squared stock: posts, plates, jambs, headers, battens. A SIXTH material, added
# after looking at a render in which the door frame was `HEWN_RGBA` and came out warmer
# and no darker than the siding around it — so the one crude board building in the row
# was wearing what read as new pine trim, which is the neat-cottage failure arriving by
# the back door. Heavy timber holds moisture, weathers darker than thin sawn stock, and
# a post darkens from the foot up; the value is chosen to separate the two by hue as
# well as by value. log_dwelling already carries six materials, so this is not new
# ground for the draw-call budget.
# On the sheet as `heavy_timber` (T-0007). materials.md finding 3 — `timber` was ONE
# NAME over TWO materials 3.2x apart in linear red, this one and frame_storefront's
# paler fresh-sawn value, of which only this one has ever shipped because no record in
# the dataset turns `framing_exposed` on — is discharged by T-0126: the two rows are
# `HEAVY_TIMBER` and `SAWN_FRAMING`, and the material slot below is renamed to match so
# the name in the shipped GLB says which of the two a reader is looking at.
TIMBER_RGBA = materials.HEAVY_TIMBER.rgba

# --- board work -------------------------------------------------------------------
# Riven and mill-sawn stock at the forks came in whatever widths the log gave. The RANGE
# is what makes a wall read as boards rather than as a striped texture, and the range is
# wide on purpose: a first pass at 0.20-0.34 m came out looking like board-and-batten
# siding somebody had ordered, which is the neat-little-cottage failure this archetype
# exists to avoid. Three things are jittered per board and all three are visible at
# fifty metres — its width, how far it stands proud, and where its foot stops.
BOARD_W_M = (0.18, 0.40)
BOARD_T_M = 0.030           # nominal; each board varies about this
BOARD_T_JITTER = (0.65, 1.55)
BOARD_FOOT_JITTER_M = 0.09  # how far a board's bottom can stop short of the ground
# Roof boards are wider still, and each one's lip and its overshoot past the eave vary.
# Regular boards at a regular lip read as corrugated sheet — which is what the first
# version of this roof looked like, on a building that predates corrugated iron by two
# decades.
ROOF_BOARD_W_M = (0.34, 0.58)
ROOF_BOARD_LIP_M = 0.024
ROOF_BOARD_OVERSHOOT_M = 0.07

# --- framing ----------------------------------------------------------------------
POST_D_M = 0.17             # a squared post in an open bay
POST_SPACING_MAX_M = 3.0    # past this the plate sags; a wagon bay is about this wide
PLATE_D_M = 0.18            # the beam the rafters land on over an open bay
ROOF_THK_M = 0.085
LOG_COURSE_RANGE_M = (0.20, 0.34)

# How far the outermost wall surface stands proud of the core plane, per construction.
# Openings have to clear it: on a boarded wall the doorway is CUT (the boards stop), so
# the dark sits just behind the siding; on a log wall nothing is cut, so the whole
# opening assembly stands in front of the chinking and the notch ends.
LOG_FACE_OFF_M = RELIEF_M * 1.7 + 0.014


def build(params: OutbuildingParams, name: str):
    """Build the outbuilding. Returns a Blender object at the local origin, y-up handled
    by the exporter (Blender is z-up internally)."""
    params.validate()
    p = params
    b = MeshBuilder(name)

    # Massing takes the confidence of the attributes that say what the building WAS,
    # not the precision of its dimensions — the rule frame_tavern.build sets out at
    # length. For an outbuilding the whole of "what it was" is how it was built and
    # whether it was open, because nothing else about one of these was ever written
    # down: `construction` and `open_sides` are the two attributes a witness would have
    # had to mention, so they are what the walls answer to.
    c_mass = p.worst_conf("construction", "open_sides")
    c_roof = p.worst_conf("roof_type", "roof_pitch_deg")
    c_fen = p.conf("fenestration", "reconstructed")

    holes = boarding_holes(p)

    if p.construction == "log":
        _log_walls(b, p, c_mass)
    else:
        _core_walls(b, p, c_mass)
        _boarded_walls(b, p, holes, c_mass)

    if p.open_sides:
        # An open bay is the only case where the inside of this building is visible, and
        # the two things it needs are the reason GROUND_CONTACT can honestly say
        # `perimeter` on a wall-less elevation: posts that land at z = 0, and a floor.
        _open_bays(b, p, c_mass)
        _interior(b, p, c_mass)

    _roof(b, p, c_roof)

    if p.door != "none":
        _doorway(b, p, p.door_side, p.door_size_m, p.conf("door", "reconstructed"))
    if p.loft and p.loft_side:
        _loft_door(b, p, p.conf("loft", "reconstructed"))
    vent = vent_rect(p)
    if vent:
        _vent(b, p, vent, c_fen)

    # ---- the surfaces, off the sheet (T-0007) --------------------------------
    # 114 of the town's records are outbuildings and 76 of them ship a boarded wall,
    # so this is the largest single family the sheet repaints. The substrate is sawn
    # board at 0.94 — the archetype's own value, and the sheet's — and the COLOUR is
    # the finish the 665-roof programme dealt this shed, which until now it dealt
    # into nothing: every unpainted board wall in Chicago was one tone.
    # `WEATHERED_BOARD_RGBA` survives as the sheet's `weathered_board` row and is
    # still what a shed with no dealt finish wears, which is the whole reason it was
    # argued in the first place — a shed carrying a tavern's brown would read as the
    # same building at a distance.
    finish = materials.wall_finish(p.paint, p.finish_key,
                                   default="weathered_board")
    board_rgba, board_rough = materials.resolve(
        materials.SUBSTRATES["sawn_board"], finish)
    mats = [
        simple_material("log", HEWN_RGBA,
                        roughness=materials.SUBSTRATES["hewn_log"].roughness),
        simple_material("chinking", CHINK_RGBA,
                        roughness=materials.SUBSTRATES["chinking"].roughness),
        simple_material("board", board_rgba, roughness=board_rough),
        # 0.93 stays a literal, and materials.md §2.2 is why: the board roof this
        # archetype argues for is separated from a shingle field by 0.03 of
        # roughness and nothing else, and choosing between them would be claiming
        # the covering finding 2 says no record states. The COLOUR takes the
        # weathering condition, which the records do state.
        simple_material("roof", materials.roof_finish(p.roof_condition).rgba,
                        roughness=0.93),
        # ONE DARK (T-0126). The slot is renamed from `interior` and takes the
        # sheet's `DARK` row, which converges this archetype's value with the
        # `dark` the frame dwellings, the log cabins, the fort and the stockade
        # carried at two other roughnesses. THE COLOUR AND THE ROUGHNESS ARE THIS
        # ARCHETYPE'S OWN, unchanged: the sheet took the warm near-black and the
        # 0.60 from here, so all 117 of these slots come out of the bake exactly as
        # they went in and it is the other 170 in the town that moved onto them.
        simple_material("dark", materials.DARK.rgba,
                        roughness=materials.DARK.roughness),
        # TWO TIMBERS, TWO NAMES (T-0126) — materials.md finding 3 discharged. The
        # slot is renamed from `timber`, which was one name over this weathered
        # heavy stock and frame_storefront's pale fresh mill stock, 3.2x apart in
        # linear red. Value and roughness unchanged; only the name in the GLB moves.
        simple_material("heavy_timber", TIMBER_RGBA,
                        roughness=materials.HEAVY_TIMBER.roughness),
    ]
    return b.to_object(mats)


# ------------------------------------------------------------------- determinism

def _jit(seed: int) -> float:
    """A repeatable pseudo-random float in [0, 1) from an integer.

    Integer arithmetic only, so it produces the same building on every machine and in
    every Python build. NOT `random`: `generators/mesh_inputs.py` defines a mesh's
    freshness on its inputs, so a generator whose output moves between two runs of the
    same parameters would leave every outbuilding permanently stale and teach the reader
    that "stale" means nothing.
    """
    x = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    x ^= x >> 13
    x = (x * 1103515245 + 12345) & 0x7FFFFFFF
    x ^= x >> 11
    return (x & 0x7FFFFFFF) / float(0x7FFFFFFF)


_SIDE_SALT = {"front": 11, "back": 23, "left": 37, "right": 53}


def _seed(p: OutbuildingParams, side: str, i: int) -> int:
    """A seed that depends on the building AND the elevation AND the board index, so
    two sheds of different sizes are not the same shed and no two walls of one shed
    carry the same board rhythm."""
    return (int(round(p.width_m * 1000)) * 7
            + int(round(p.depth_m * 1000)) * 13
            + _SIDE_SALT.get(side, 3) * 101
            + i * 6151)


def _lerp_jit(seed: int, lo: float, hi: float) -> float:
    return lo + (hi - lo) * _jit(seed)


# ------------------------------------------------------------ the elevation frame
#
# Each elevation is worked in its own (u, z) plane and mapped to 3D once, at the end.
# `u` runs along x on `front`/`back` and along y on `left`/`right`, always increasing.
# `off` is distance OUTWARD from the wall's core plane.

def _to3(side: str, p: OutbuildingParams, u: float, z: float, off: float):
    if side == "front":
        return (u, p.depth_m + off, z)
    if side == "back":
        return (u, -off, z)
    if side == "left":
        return (-off, u, z)
    return (p.width_m + off, u, z)


# `back` and `right` have a right-handed (u, z, outward) frame, so a polygon wound
# counter-clockwise in (u, z) already faces out. `front` and `left` do not, and their
# point order is reversed. Working this out once here is what keeps every recess, board
# and jamb in this module from being able to face into the building by hand.
_KEEP = {"back", "right"}


def _face(b: MeshBuilder, side: str, p: OutbuildingParams, off: float, pts_uz,
          conf: float, mat: int, inward: bool = False) -> None:
    """One flat polygon on an elevation, wound outward (or inward)."""
    pts = list(pts_uz)
    if (side in _KEEP) == bool(inward):
        pts = pts[::-1]
    b.add_poly([_to3(side, p, u, z, off) for u, z in pts], conf, mat)


def _prism(b: MeshBuilder, side: str, p: OutbuildingParams, pts_uz,
           off_in: float, off_out: float, conf: float, mat: int,
           skip: tuple = ()) -> None:
    """A polygon standing proud of the wall: the outer face plus its returns.

    `pts_uz` is counter-clockwise in (u, z); `skip` names edge indices into THAT list
    whose return quad is omitted (a board's top edge disappears under the roof, and
    two triangles per board across a town is not nothing). The reversal for the
    left-handed elevations remaps the indices with it — an edge is identified by the
    geometry it belongs to, not by where it happened to sit in a list.
    """
    pts = list(pts_uz)
    n = len(pts)
    skip_set = set(skip)
    if side not in _KEEP:
        pts = pts[::-1]
        skip_set = {(n - 2 - i) % n for i in skip_set}
    outer = [_to3(side, p, u, z, off_out) for u, z in pts]
    inner = [_to3(side, p, u, z, off_in) for u, z in pts]
    b.add_poly(outer, conf, mat)
    for i in range(n):
        if i in skip_set:
            continue
        j = (i + 1) % n
        b.add_poly([inner[i], inner[j], outer[j], outer[i]], conf, mat)


# ---------------------------------------------------------------- the top profile

def _top_z(p: OutbuildingParams, side: str, u: float) -> float:
    """The height of the wall top at position `u` along `side`.

    One function for all three shapes a wall top can take here — level under an eave,
    peaked at a gable end, sloping along the side of a shed roof — because the roof
    surface is derived from the SAME numbers. Where these two disagree you get a
    daylight gap along a rake that nobody notices until a render, which is how the
    first version of this went.
    """
    wall_z = float(p.wall_height_m)
    rise = p.roof_rise_m
    if p.roof_type == "gable":
        if p.ridge_along_x:
            if side in ("front", "back"):
                return wall_z
            half = p.depth_m / 2.0
            return wall_z + rise * (1.0 - abs(u - half) / half)
        if side in ("left", "right"):
            return wall_z
        half = p.width_m / 2.0
        return wall_z + rise * (1.0 - abs(u - half) / half)

    # shed: linear from the low eave to the high one
    high = p.shed_high_side
    if p.shed_axis == "y":
        if side == "back":
            return wall_z + (rise if high == "back" else 0.0)
        if side == "front":
            return wall_z + (rise if high == "front" else 0.0)
        f = u / p.depth_m                       # u runs along y on left/right
        return wall_z + rise * ((1.0 - f) if high == "back" else f)
    if side == "left":
        return wall_z + (rise if high == "left" else 0.0)
    if side == "right":
        return wall_z + (rise if high == "right" else 0.0)
    f = u / p.width_m                           # u runs along x on front/back
    return wall_z + rise * ((1.0 - f) if high == "left" else f)


def _top_break(p: OutbuildingParams, side: str) -> float | None:
    """The `u` at which the top profile turns a corner — a gable end's ridge point, and
    nothing else. Returned so every polygon and every board that crosses it carries the
    peak instead of cutting it off."""
    if p.roof_type != "gable":
        return None
    if p.ridge_along_x and side in ("left", "right"):
        return p.depth_m / 2.0
    if not p.ridge_along_x and side in ("front", "back"):
        return p.width_m / 2.0
    return None


def _top_profile(p: OutbuildingParams, side: str) -> list:
    """The wall top as a polyline of (u, z) — two points, or three at a gable end.

    Every top profile in this archetype is piecewise linear with at most one break, so
    questions about it can be answered exactly instead of by sampling. That matters:
    `_horizontal_boards` sampled the profile at 48 points to decide how far a course
    could run, got the comparison backwards on a monotonic slope, and left the whole
    upper triangle of every shed-roofed side unboarded — a hole you can see straight
    through in a render and cannot see at all in the code.
    """
    run = p.side_run_m(side)
    brk = _top_break(p, side)
    us = [0.0] + ([brk] if brk is not None else []) + [run]
    return [(u, _top_z(p, side, u)) for u in us]


def _top_span(p: OutbuildingParams, side: str, z: float):
    """The `u` range over which the wall top is at or above `z`, or None.

    Which is where a horizontal course of boards can run, and it is the whole width of
    the wall under an eave, a shrinking band under a rake, and nothing at all above the
    ridge.
    """
    prof = _top_profile(p, side)
    lo = hi = None
    for i in range(len(prof) - 1):
        (ua, za), (ub, zb) = prof[i], prof[i + 1]
        if za >= z and zb >= z:
            a, c = ua, ub
        elif za < z and zb < z:
            continue
        else:
            cut = ua + (ub - ua) * (z - za) / (zb - za)
            a, c = (ua, cut) if za >= z else (cut, ub)
        lo = a if lo is None else min(lo, a)
        hi = c if hi is None else max(hi, c)
    return None if lo is None or hi - lo < 0.02 else (lo, hi)


def _top_points(p: OutbuildingParams, side: str, u0: float, u1: float) -> list:
    """The top edge of a wall or a board between u0 and u1, right to left, with the
    ridge point inserted if it falls inside."""
    pts = [(u1, _top_z(p, side, u1))]
    brk = _top_break(p, side)
    if brk is not None and u0 < brk < u1:
        pts.append((brk, _top_z(p, side, brk)))
    pts.append((u0, _top_z(p, side, u0)))
    return pts


def _plate_z(p: OutbuildingParams, side: str) -> float:
    """The height of the plate over an open bay: the LOWEST point of that elevation's
    top profile.

    Not `wall_height_m`, and the difference is the whole wagon shed. A shed roof's high
    side has a top profile at `wall_height_m + rise`, so pinning the plate to the wall
    height would hang a beam across the middle of the opening at exactly the height a
    loaded wagon needs — the opening under a tall eave is meant to be the full height of
    that eave. On a gable end the lowest point is the corner, at `wall_height_m`, which
    puts the plate where it belongs and leaves the triangle above it to be boarded.
    """
    run = p.side_run_m(side)
    brk = _top_break(p, side)
    us = [0.0, run] + ([brk] if brk is not None else [])
    return min(_top_z(p, side, u) for u in us)


def _wall_base_z(p: OutbuildingParams, side: str) -> float:
    """Where this elevation's solid wall starts.

    Zero for a closed side. For an OPEN side it starts at the plate: a post-and-plate
    bay is open all the way up to the beam and boarded above it, which is what an open
    gable end on a barn actually looks like and what carries the roof over an opening.
    """
    return _plate_z(p, side) if side in p.open_sides else 0.0


def _wall_poly(p: OutbuildingParams, side: str) -> list | None:
    """The whole elevation as a polygon in (u, z), or None if there is nothing to
    build (an open eave wall, whose top profile is level with the plate)."""
    z0 = _wall_base_z(p, side)
    run = p.side_run_m(side)
    top = _top_points(p, side, 0.0, run)
    if max(z for _, z in top) - z0 < 1e-6:
        return None
    return [(0.0, z0), (run, z0)] + top


# ------------------------------------------------------------------------- walls

def _core_walls(b: MeshBuilder, p: OutbuildingParams, conf: float) -> None:
    """The dark shell the boards are nailed to.

    Not a structural claim and not sheathing — a crude board wall has nothing behind
    it. It is what you see THROUGH the gaps, and it is the reason the gaps read as gaps
    rather than as a change of shade. Modelled at the core plane so the boards standing
    proud of it are the building's real outside face.
    """
    for side in ("front", "back", "left", "right"):
        poly = _wall_poly(p, side)
        if poly:
            _face(b, side, p, 0.0, poly, conf, M_DARK)


def _log_walls(b: MeshBuilder, p: OutbuildingParams, conf: float) -> None:
    """Hewn log courses, chinking and corner notching, from common/logwork.

    The same visual language as the Wolf Point buildings, on purpose: a log stable and
    a log cabin at the forks were put up by the same handful of people with the same
    axes, and they should look it.

    The COURSE scales with the building. A 2.4 m smokehouse built of the 0.34 m wall
    logs a dwelling uses is seven courses tall and reads as a toy; a small pen was
    built of lighter stuff. Above the eave the gable or the wedge is emitted flat, in
    the log material — a log gable is a stack of short logs and modelling that would
    cost more triangles than the silhouette is worth.
    """
    course = _lerp_jit(_seed(p, "back", 0), *LOG_COURSE_RANGE_M)
    course = min(course, max(LOG_COURSE_RANGE_M[0], min(p.width_m, p.depth_m) / 6.0))
    wall_z = float(p.wall_height_m)
    hewn_log_wall(b, 0.0, 0.0, p.width_m, p.depth_m, 0.0, wall_z, conf,
                  M_LOG, M_CHINK, skip=("bottom", "top"), course=course)
    for side in ("front", "back", "left", "right"):
        run = p.side_run_m(side)
        top = _top_points(p, side, 0.0, run)
        if max(z for _, z in top) - wall_z < 1e-6:
            continue
        _face(b, side, p, LOG_FACE_OFF_M * 0.4,
              [(0.0, wall_z), (run, wall_z)] + top, conf, M_LOG)


def _boarded_walls(b: MeshBuilder, p: OutbuildingParams, holes: dict,
                   conf: float) -> None:
    """Sawn boards, uneven, gapped, and not all reaching the ground.

    `plank` stands them on end — the frontier default, because a board on end needs
    only a sill and a plate to nail to and no studs in between. `light_frame` lays them
    horizontally on a stick frame, which is the same material doing the other thing.
    Either way they are BOARDS: no lapped courses, no corner boards, no trim, and the
    gaps are left in rather than closed, because that is what these buildings looked
    like and it is also what a corn crib IS.
    """
    for side in ("front", "back", "left", "right"):
        if _wall_poly(p, side) is None:
            continue
        if p.construction == "plank":
            _vertical_boards(b, p, side, holes.get(side, ()), conf)
        else:
            _horizontal_boards(b, p, side, holes.get(side, ()), conf)


def _free_spans(z0: float, z1: float, blocks) -> list:
    """`[z0, z1]` minus the z-ranges in `blocks`, as a list of surviving spans.

    This is how an opening gets CUT OUT of the boarding instead of pasted on top of it.
    A board that crosses a doorway is not deleted and is not left whole: it survives
    above the header, exactly as the ripped board on a real shed does.
    """
    spans = [(z0, z1)]
    for bz0, bz1 in blocks:
        out = []
        for s0, s1 in spans:
            if bz1 <= s0 or bz0 >= s1:
                out.append((s0, s1))
                continue
            if s0 < bz0:
                out.append((s0, bz0))
            if bz1 < s1:
                out.append((bz1, s1))
        spans = out
    return [(a, c) for a, c in spans if c - a > 0.05]


def _u_cuts(u0: float, u1: float, holes) -> list:
    """Split `[u0, u1]` at every hole edge inside it, so each sub-span is either wholly
    inside a hole or wholly outside one."""
    cuts = {u0, u1}
    for hu0, hu1, _, _ in holes:
        for c in (hu0, hu1):
            if u0 < c < u1:
                cuts.add(c)
    edges = sorted(cuts)
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)
            if edges[i + 1] - edges[i] > 0.02]


def _board_piece(b: MeshBuilder, p: OutbuildingParams, side: str, u0: float, u1: float,
                 z0: float, z1_cap: float | None, conf: float, t: float) -> None:
    """One board (or one surviving piece of one) standing `t` proud of the wall."""
    if z1_cap is None:
        top = _top_points(p, side, u0, u1)
    else:
        top = [(u1, z1_cap), (u0, z1_cap)]
    if min(z for _, z in top) - z0 < 0.05:
        return
    pts = [(u0, z0), (u1, z0)] + top
    # The top edge is under the roof or under a header; its return is never seen.
    skip = tuple(range(2, len(pts) - 1))
    _prism(b, side, p, pts, 0.0, t, conf, M_BOARD, skip=skip)


def _vertical_boards(b: MeshBuilder, p: OutbuildingParams, side: str, holes,
                     conf: float) -> None:
    """Boards on end, walked along the elevation with jittered widths and gaps."""
    run = p.side_run_m(side)
    base = _wall_base_z(p, side)
    u, i = 0.0, 0
    while u < run - 0.01:
        s = _seed(p, side, i)
        w = min(_lerp_jit(s, *BOARD_W_M), run - u)
        gap = p.board_gap_m * _lerp_jit(s + 1, 0.6, 1.6)
        t = BOARD_T_M * _lerp_jit(s + 3, *BOARD_T_JITTER)
        # A board's foot is where the sawyer left it. Only ever UPWARD from the base:
        # the perimeter has to keep meeting the terrain at z = 0, which is what this
        # archetype's GROUND_CONTACT declaration promises, and the dark core behind the
        # ragged feet is what a shed's bottom edge actually looks like.
        foot = base + (0.0 if base > 0.0 else BOARD_FOOT_JITTER_M * _jit(s + 2))
        for a, c in _u_cuts(u, u + w, holes):
            blocks = [(hz0, hz1) for hu0, hu1, hz0, hz1 in holes
                      if hu0 - 1e-6 <= a and c <= hu1 + 1e-6]
            for z0, z1 in _free_spans(foot, _top_z(p, side, (a + c) / 2.0), blocks):
                cap = None if z1 >= _top_z(p, side, (a + c) / 2.0) - 1e-6 else z1
                _board_piece(b, p, side, a, c, z0, cap, conf, t)
        u += w + gap
        i += 1


def _horizontal_boards(b: MeshBuilder, p: OutbuildingParams, side: str, holes,
                       conf: float) -> None:
    """Boards laid flat on a light frame, walked up the elevation.

    Each course is clipped to the wall's top profile, so a course crossing a gable end
    stops at the rake instead of sailing past it into the sky.
    """
    base = _wall_base_z(p, side)
    top_max = max(z for _, z in _top_profile(p, side))
    z, i = base, 0
    while z < top_max - 0.03:
        s = _seed(p, side, i)
        h = _lerp_jit(s, *BOARD_W_M)
        gap = p.board_gap_m * _lerp_jit(s + 1, 0.6, 1.6)
        t = BOARD_T_M * _lerp_jit(s + 3, *BOARD_T_JITTER)
        z1 = min(z + h, top_max)
        # Where the top profile slopes, the course stops under the rake. Solved on the
        # polyline rather than sampled, so the boarding meets the rake exactly and no
        # sliver of the dark core is left showing along it.
        span = _top_span(p, side, z1)
        if span is None:
            z = z1 + gap
            i += 1
            continue
        u_lo, u_hi = span
        for a, c in _u_cuts(u_lo, u_hi, holes):
            blocked = any(hu0 - 1e-6 <= a and c <= hu1 + 1e-6 and hz0 < z1 and z < hz1
                          for hu0, hu1, hz0, hz1 in holes)
            if blocked:
                continue
            _prism(b, side, p, [(a, z), (c, z), (c, z1), (a, z1)],
                   0.0, t, conf, M_BOARD, skip=(2,))
        z = z1 + gap
        i += 1


# -------------------------------------------------------------------- open bays

def _open_bays(b: MeshBuilder, p: OutbuildingParams, conf: float) -> None:
    """Posts and a plate where a side is open.

    The wagon shed and the hay shelter are the reason this archetype is not just a box
    with a door in it. Posts stand at the corners and at no more than
    POST_SPACING_MAX_M between, which is about a wagon bay and about as far as a hand-
    hewn plate will span; the plate itself sits under the eave and is what the boarded
    gable above the opening stands on.

    The posts run to z = 0 and that is not a detail: this archetype declares
    GROUND_CONTACT `perimeter`, and on an elevation with no wall the posts and the
    floor are the whole of what meets the ground.
    """
    for side in p.open_sides:
        run = p.side_run_m(side)
        plate_z = _plate_z(p, side)
        n = max(1, int(math.ceil(run / POST_SPACING_MAX_M)))
        for k in range(n + 1):
            u = run * k / n
            u0 = min(max(u - POST_D_M / 2.0, 0.0), run - POST_D_M)
            _box_on_side(b, p, side, u0, u0 + POST_D_M, 0.0, plate_z - PLATE_D_M,
                         0.0, POST_D_M, conf, M_TIMBER)
        _box_on_side(b, p, side, 0.0, run, plate_z - PLATE_D_M, plate_z,
                     0.0, PLATE_D_M, conf, M_TIMBER)


def _box_on_side(b: MeshBuilder, p: OutbuildingParams, side: str, u0: float, u1: float,
                 z0: float, z1: float, off_in: float, off_out: float,
                 conf: float, mat: int) -> None:
    """An axis-aligned box described in one elevation's own frame."""
    _prism(b, side, p, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)],
           off_in, off_out, conf, mat)


def _interior(b: MeshBuilder, p: OutbuildingParams, conf: float) -> None:
    """The inside faces of the closed walls, and an earth floor.

    Only built when a side is open, because that is the only time anyone can see in.
    Without them an open bay shows the BACK of the far wall's single-sided polygon —
    which renders today only because the exporter writes doubleSided by default, and
    renders lit from the wrong side even then.

    The inside faces are BOARD, not the dark of the core plane: the core stands for what
    shows through a gap from outside, and what you see from inside a wagon shed is the
    backs of the same boards. It also keeps the bay from reading as a black rectangle
    cut in the building, which is what it did when both faces were dark.
    """
    for side in ("front", "back", "left", "right"):
        poly = _wall_poly(p, side)
        if poly:
            _face(b, side, p, 0.0, poly, conf, M_BOARD, inward=True)
    b.add_poly([(0.0, 0.0, 0.0), (p.width_m, 0.0, 0.0),
                (p.width_m, p.depth_m, 0.0), (0.0, p.depth_m, 0.0)], conf, M_DARK)


# --------------------------------------------------------------------------- roof

def _ccw_from_above(pts: list) -> list:
    """Order a planar quad counter-clockwise as seen from above, so its normal points
    up and the slab built from it faces the sky."""
    area = 0.0
    for i, (x, y, _) in enumerate(pts):
        x2, y2, _ = pts[(i + 1) % len(pts)]
        area += x * y2 - x2 * y
    return pts if area > 0 else pts[::-1]


def _slab(b: MeshBuilder, top_pts: list, drop: float, conf: float, mat: int,
          skip: tuple = ()) -> None:
    """A flat plate of thickness `drop`, given its top face. `skip` omits edge returns
    by index, for the edges where two plates meet along a ridge."""
    top = _ccw_from_above(list(top_pts))
    bot = [(x, y, z - drop) for x, y, z in top]
    b.add_poly(top, conf, mat)
    b.add_poly(bot[::-1], conf, mat)
    for i in range(len(top)):
        if i in skip:
            continue
        j = (i + 1) % len(top)
        b.add_poly([bot[i], bot[j], top[j], top[i]], conf, mat)


def _roof(b: MeshBuilder, p: OutbuildingParams, conf: float) -> float:
    """The roof planes, boarded.

    THE OVERHANG CONTINUES THE SLOPE rather than being pinned at the eave height, which
    is the geometrically real thing and is what lets `_top_z` and the roof agree exactly
    at every point of every rake. `MeshBuilder.add_gable_roof` does the other thing —
    it grows the footprint first and raises the ridge to suit — which is fine for a
    building whose gable end is drawn by the roof itself, and wrong here, where the
    gable end is a boarded WALL and any disagreement is a strip of daylight.

    The overhang scales with the building, for the same reason the wall height does: a
    fixed 0.25 m eave is a tenth of a privy's plan on each side and turns it into a
    mushroom.
    """
    # The same number `tools/ridge_model.py` asks the params module for, so a model of
    # where this roof gets to and the roof itself cannot drift apart (T-0274).
    oh = eave_overhang_m(p.width_m, p.depth_m)
    w, d = p.width_m, p.depth_m

    # `along` is the axis the roof slopes down; `z_at` is the roof's top surface at a
    # given coordinate on it, and it is the SAME line the wall tops follow, extended
    # past the building by the overhang. Building the planes out of one function
    # instead of a fistful of signed offsets is what makes that guarantee checkable —
    # an earlier version juggled `copysign` per case and put one overhang on the
    # wrong side of the building.
    if p.roof_type == "shed":
        along = "y" if p.shed_axis == "y" else "x"
        far = d if along == "y" else w
        side_lo, side_hi = (("back", "front") if along == "y" else ("left", "right"))

        def z_at(c: float, _lo=side_lo, _hi=side_hi, _far=far) -> float:
            a = _top_z(p, _lo, 0.0)
            bz = _top_z(p, _hi, 0.0)
            return a + (bz - a) * (c / _far)

        spans = [(-oh, far + oh)]
    else:
        along = "y" if p.ridge_along_x else "x"
        far = d if along == "y" else w
        mid = far / 2.0

        def z_at(c: float, _far=far) -> float:
            half = _far / 2.0
            return float(p.wall_height_m) + p.roof_rise_m * (1.0 - abs(c - half) / half)

        spans = [(-oh, mid), (mid, far + oh)]

    cross = (-oh, (w if along == "y" else d) + oh)
    for k, (c0, c1) in enumerate(spans):
        corners = []
        for c in (c0, c1):
            for x_or_y in cross:
                corners.append((x_or_y, c, z_at(c)) if along == "y"
                               else (c, x_or_y, z_at(c)))
        # corners currently pairs (c0,lo),(c0,hi),(c1,lo),(c1,hi); reorder to a ring
        pts = [corners[0], corners[1], corners[3], corners[2]]
        _roof_plane(b, p, pts, conf, f"{p.roof_type[0]}{k}",
                    ridge_edge=(p.roof_type == "gable"))
    return p.apex_z_m


def _roof_plane(b: MeshBuilder, p: OutbuildingParams, quad: list, conf: float,
                tag: str, ridge_edge: bool = False) -> None:
    """One sloping plane: a plate, then boards laid up and down the slope over it.

    Boards rather than shingles, because a shed roof at the forks was boards weighted or
    nailed down and a shingle field on an outbuilding would be claiming a finish the
    building did not have. They are jittered in width like the walls, and the plate
    behind them shows in the gaps.
    """
    pts = _ccw_from_above(list(quad))
    ridge_skip: tuple = ()
    if ridge_edge:
        # The two planes of a gable meet along one edge; its return quad would be a
        # pair of triangles buried inside the ridge.
        hi = max(z for _, _, z in pts)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            if abs(pts[i][2] - hi) < 1e-6 and abs(pts[j][2] - hi) < 1e-6:
                ridge_skip = (i,)
                break
    _slab(b, pts, ROOF_THK_M, conf, M_ROOF, skip=ridge_skip)

    # Walk across the slope, laying boards down it. `a` and `c` are the two edges that
    # run down-slope; the boards subdivide the span between them.
    lo = sorted(pts, key=lambda q: q[2])[:2]
    hi = sorted(pts, key=lambda q: q[2])[2:]
    lo = sorted(lo, key=lambda q: (q[0], q[1]))
    hi = sorted(hi, key=lambda q: (q[0], q[1]))
    span = math.hypot(lo[1][0] - lo[0][0], lo[1][1] - lo[0][1])
    if span < 1e-6:
        return
    salt = sum(ord(ch) for ch in tag) * 977
    f, i = 0.0, 0
    while f < 1.0 - 1e-4:
        s = _seed(p, "back", i) + salt
        wfrac = min(_lerp_jit(s, *ROOF_BOARD_W_M) / span, 1.0 - f)
        gapf = (0.010 + 0.012 * _jit(s + 1)) / span
        lip = ROOF_BOARD_LIP_M * _lerp_jit(s + 2, 0.6, 1.5)
        f1 = min(f + wfrac, 1.0)

        def at(edge, ff):
            e0, e1 = edge
            return [e0[k] + (e1[k] - e0[k]) * ff for k in range(3)]

        corners = [at((lo[0], lo[1]), f), at((lo[0], lo[1]), f1),
                   at((hi[0], hi[1]), f1), at((hi[0], hi[1]), f)]
        # Each board runs a little further past the eave than its neighbour. A board
        # roof was cut to length with a saw and an opinion, and the ragged line at the
        # eave is the single clearest signal in the silhouette that this is not a
        # finished building — it is also the one thing a regular grid of boards, which
        # is what this looked like first time, could never say.
        ext = ROOF_BOARD_OVERSHOOT_M * _jit(s + 4)
        for k in (0, 1):
            dv = [corners[k][j] - corners[3 - k][j] for j in range(3)]
            mag = math.sqrt(sum(c * c for c in dv)) or 1.0
            corners[k] = [corners[k][j] + dv[j] / mag * ext for j in range(3)]
        board = [(c[0], c[1], c[2] + lip) for c in corners]
        _slab(b, board, lip, conf, M_ROOF)
        f = f1 + gapf
        i += 1


# ---------------------------------------------------------------------- openings

def _offsets(p: OutbuildingParams) -> dict:
    """Where the pieces of an opening sit, relative to the wall's core plane.

    A boarded wall has the doorway CUT out of it, so the dark and the door leaf sit
    just behind the siding. A log wall has nothing cut — logs are not sawn through for
    a door at this level of detail — so the whole assembly stands in front of the
    chinking and the notch ends, which is the arrangement log_dwelling settled on for
    the same reason.
    """
    if p.construction == "log":
        base = LOG_FACE_OFF_M
        return {"frame": base + 0.004, "dark": base + 0.012,
                "leaf": base + 0.026, "batten": base + 0.038}
    return {"frame": BOARD_T_M + 0.006, "dark": 0.006,
            "leaf": 0.020, "batten": 0.031}


def _doorway(b: MeshBuilder, p: OutbuildingParams, side: str, size: tuple,
             conf: float) -> None:
    """A doorway: a dark opening in a sawn frame, with a batten door hung in it.

    The frame is not decoration. An opening drawn as a bare dark rectangle reads as a
    plaque glued to the wall — the same lesson log_dwelling records — and the jambs and
    header are what a wall of any construction actually needs around a hole.

    A `wagon` door is TWO leaves, because a three-metre opening was never closed by one,
    and the pair of them is most of what tells a viewer this is a building a wagon went
    into. Both leaves are shown SHUT: whether a given door stood open on 1 July 1835 is
    not something any source can say, and a swung leaf would be inventing an occupied
    building.
    """
    dw, dh = size
    if dw <= 0.0:
        return
    off = _offsets(p)
    run = p.side_run_m(side)
    um = run / 2.0
    u0, u1 = um - dw / 2.0, um + dw / 2.0
    j = DOOR_JAMB_M

    _face(b, side, p, off["dark"], [(u0, 0.0), (u1, 0.0), (u1, dh), (u0, dh)],
          conf, M_DARK)
    for a, c in ((u0 - j, u0), (u1, u1 + j)):
        _prism(b, side, p, [(a, 0.0), (c, 0.0), (c, dh + j), (a, dh + j)],
               0.0, off["frame"], conf, M_TIMBER)
    _prism(b, side, p, [(u0, dh), (u1, dh), (u1, dh + j), (u0, dh + j)],
           0.0, off["frame"], conf, M_TIMBER)

    leaves = [(u0, u1)] if dw < 1.9 else [(u0, um - 0.012), (um + 0.012, u1)]
    for la, lc in leaves:
        _leaf(b, p, side, la, lc, 0.015, dh - 0.02, off, conf)


def _leaf(b: MeshBuilder, p: OutbuildingParams, side: str, u0: float, u1: float,
          z0: float, z1: float, off: dict, conf: float) -> None:
    """One batten door: vertical boards with gaps, on two cross battens.

    The boards are plain faces rather than prisms — a door leaf is 25 mm of stock and
    the returns would be invisible at any distance this model is looked at from. The
    gaps between them are the point: they show the dark behind, which is what a shed
    door does in daylight.
    """
    span = u1 - u0
    n = max(3, int(round(span / 0.19)))
    for k in range(n):
        a = u0 + span * k / n + 0.008
        c = u0 + span * (k + 1) / n - 0.008
        _face(b, side, p, off["leaf"], [(a, z0), (c, z0), (c, z1), (a, z1)],
              conf, M_BOARD)
    for f in (0.20, 0.78):
        zc = z0 + (z1 - z0) * f
        _face(b, side, p, off["batten"],
              [(u0, zc - 0.055), (u1, zc - 0.055), (u1, zc + 0.055), (u0, zc + 0.055)],
              conf, M_TIMBER)


def _loft_door(b: MeshBuilder, p: OutbuildingParams, conf: float) -> None:
    """The loft's only external trace: the door you pitch hay through.

    Not a dormer, not a floor band, not a second range of windows — a loft leaves
    nothing else on the outside of a building like this, and adding more would be
    adding evidence rather than reading it. It sits high in the gable end, where a
    wagon standing at the end of the building can be forked into.
    """
    side = p.loft_side
    if not side:
        return
    u0, u1, z0, z1 = loft_rect(p)
    off = _offsets(p)
    _face(b, side, p, off["dark"], [(u0, z0), (u1, z0), (u1, z1), (u0, z1)],
          conf, M_DARK)
    j = 0.11
    for a, c in ((u0 - j, u0), (u1, u1 + j)):
        _prism(b, side, p, [(a, z0 - j), (c, z0 - j), (c, z1 + j), (a, z1 + j)],
               0.0, off["frame"], conf, M_TIMBER)
    for a, c in ((z0 - j, z0), (z1, z1 + j)):
        _prism(b, side, p, [(u0, a), (u1, a), (u1, c), (u0, c)],
               0.0, off["frame"], conf, M_TIMBER)
    _leaf(b, p, side, u0 + 0.01, u1 - 0.01, z0 + 0.01, z1 - 0.01, off, conf)


def _vent(b: MeshBuilder, p: OutbuildingParams, vent: tuple, conf: float) -> None:
    side, (u0, u1, z0, z1) = vent
    off = _offsets(p)
    _face(b, side, p, off["dark"], [(u0, z0), (u1, z0), (u1, z1), (u0, z1)],
          conf, M_DARK)
    j = 0.075
    _prism(b, side, p, [(u0 - j, z0 - j), (u1 + j, z0 - j),
                        (u1 + j, z1 + j), (u0 - j, z1 + j)],
           0.0, off["frame"] * 0.8, conf, M_TIMBER)
