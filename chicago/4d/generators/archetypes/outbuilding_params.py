"""Parameters for the outbuilding archetype — pure Python, NO bpy import.

Same split, and for the same reason, as frame_tavern_params: tools/check.sh imports
this module on every commit to prove that every scene-included record still resolves
into buildable parameters, and it has to do that in a bare Python 3.11 with no Blender
in the sandbox.

## What this archetype is for

A frontier town is mostly outbuildings. The eight buildings currently in the 1835
scene are all public houses, stores and a bridge, and behind every one of them the
sources put things this dataset has no archetype for: "the large stable and the yard
into which the trains were driven" behind the Western Hotel (chicagology_prefire278,
docs/research/03-structures-north.md §2.6); the Cook County tavern schedule of 13 April
1831 — "Keeping horse one night 50" — which is a stable stated as a price
(NOTE: this file previously quoted a "13 cents to stable a horse" tariff. That
sentence does not exist in any source this project holds; it was the MAN's 12 1/2
cent lodging rate carried across to the horse. Corrected 2026-08-11.)
(drloih_wolf_point, §2.1); du Sable's "numerous outbuildings" and the Kinzie group's
"dairy, bakehouse, stables, and lodging rooms for the French engages"
(kinzie_waubun_1856, §3.3 — that group is gone by 1835, but it is what the type looked
like here); Beaubien converting "an earlier cabin to a barn" beside the fort
(andreas_1884_v1, docs/research/04-structures-south.md §4); Clybourn's log
slaughterhouse and its stockyard on the north branch (§3.6); and a town code of
November 1833 that forbids pigs to wander the streets (chicagology_prefire278), which
documents pigs and therefore pens.

None of those is dimensioned. Not one source describes the *fabric* of any outbuilding
at the forks — no material, no roof, no size. So this module's defaults are conventions
and are labelled as such throughout, and a record that states nothing gets `conjectural`
for everything by the normal rule (an attribute absent from `form` has no confidence
entry, and `conf()` falls back to conjectural), which is the honest rendering.

## It is a FAMILY, and the family is what the parameters are shaped around

A privy is 1.2 m square and a livery stable is twenty metres long. One set of
proportions cannot serve both — a fixed 2.5 m wall makes the privy a tower and the
stable a crawlspace; a fixed 0.25 m eave overhang is a tenth of the privy's plan on
each side and reads as a mushroom; a fixed 35 degree shed pitch puts 4.9 m of rise on
a 7 m deep wagon shed and builds a ski jump. So the dimensional defaults are FUNCTIONS
of the footprint (`default_wall_height_m`, `default_roof_type`, `default_roof_pitch_deg`),
and the validator checks the *consequences* — the shed roof's absolute rise against the
wall it stands on, the door's width against the wall it is cut into — rather than only
the angles and the lengths in isolation. A range check that passes at both ends and
lies in the middle is the failure this module is written against.

Three axes carry the family:

- **construction** — `log`, `plank` (sawn boards nailed on vertically, gaps and all)
  or `light_frame` (boards laid horizontally on a stick frame). Not
  `balloon_frame`/`braced_frame`: what is behind the boards of a shed is invisible at
  this LOD and no source states it for any outbuilding here, so the vocabulary says
  only what a viewer can see. `log` is refused an open side — a notched log pen is
  held up by its corners, and a wall you remove is a corner you remove.
- **roof_type** — `shed` is first class, not a fallback. A single-slope roof is at
  least as common as a gable on this class of building, and the archetype derives which
  way it falls from the open sides rather than taking a parameter for it (see
  `shed_high_side`): a wagon shed is open on its TALL side, because that is the side a
  loaded wagon can drive through.
- **open_sides** — the wagon shed and the hay shelter are posts and a roof. Any subset
  of the four elevations, including all four.

## What it deliberately does not cover

**The yard.** docs/LIBERTIES.md L10 admits that the Western Hotel's stable *and* its
wagon yard are attested and unbuilt, and this archetype can discharge only the first
half. A yard is an enclosure — a fence line, two gateways and the ground between them —
and building it out of an outbuilding would mean calling a fence a building. L10 should
be revised to narrow its claim, not resolved, until something models enclosures.

**A raised floor.** A corn crib standing clear of the ground on blocks is real and is
not built: `GROUND_CONTACT` below is `perimeter`, which is the claim that the whole
footprint outline meets the terrain at the base of the walls, and a crib on blocks
does not. A crib is buildable here as what a crib mainly is — a slatted box with wide
air gaps between its boards, which is what `board_gap_m` is for — sitting on its sill
at grade. The blocks are the liberty and a record that wants them needs an archetype
that can say so.

**Interiors.** No stalls, no mangers, no seat. Openings are surfaces, not holes, exactly
as in log_dwelling.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md. Duplicated from the sibling params modules rather than
# imported so that no one of them can break another's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# What a viewer can see of how the thing was put together, and nothing more. The
# framing method behind sawn boards is invisible at this LOD and unattested for every
# outbuilding in the dossiers, so `balloon_frame` and `braced_frame` are deliberately
# absent — a record using one of those is describing a house.
CONSTRUCTIONS = ("log", "plank", "light_frame")

# Two forms, and `shed` is not the poor relation. A hip or gambrel on a stable at the
# forks in 1835 would be a claim, so it is refused loudly rather than substituted —
# the same rule log_dwelling applies.
ROOF_TYPES = ("gable", "shed")

# The four elevations, named on the PLAN with north up: `front` is the facade (+y in
# Blender, the bearing `rotation_deg` names, north at 0), `back` is opposite it, and
# `left`/`right` are west and east of it on that plan. Stated this way because "left"
# read as a person standing outside looking at the building is the opposite hand, and
# a silently mirrored building looks right from every angle except the map.
SIDES = ("front", "back", "left", "right")

# What has to get through the doorway. This is the parameter the archetype exists to
# get right: a stable whose door is a person's door is a shed with a horse painted on
# it. Widths are the clear opening.
DOOR_KINDS = ("none", "man", "stable", "wagon")
DOOR_SIZE_M = {
    "man": (0.86, 1.88),      # one person, a barrow, an armful of wood
    "stable": (1.35, 2.30),   # a horse led through in hand, single leaf
    "wagon": (2.90, 3.00),    # a loaded wagon and its team, double leaf
}
# Jamb and header stock either side of the clear opening. The door has to fit the WALL,
# not merely be under some maximum, so this is part of the check.
DOOR_JAMB_M = 0.16

# Finishes. Outbuildings here are unpainted by default and mostly stayed that way;
# whitewash is included because a dairy or a smokehouse sometimes got it and because
# refusing a value a record might legitimately hold is worse than carrying it.
PAINTS = ("unpainted", "whitewash", "white", "red")

# Below this, corner notching eats the wall: `common/logwork` protrudes a notched end
# 0.24 m past each corner, so a 1.8 m log pen has notches meeting near the middle of
# every elevation. Real small outbuildings — privies, smokehouses — were boarded or
# were built of much lighter stuff than a house's wall logs, and this archetype models
# hewn house logs. So it refuses rather than draws a caricature.
LOG_MIN_DIM_M = 2.2

# Nothing at the forks in 1835 was this tall. A three-storey building did not exist in
# the town; an outbuilding reaching nine metres to its ridge is an arithmetic accident
# in a record, not a barn.
MAX_HEIGHT_M = 9.0

# A shed roof whose rise exceeds this multiple of its own wall is not a shed roof, it
# is a ramp. The number is the point at which the low wall stops being the building
# and the roof starts being it. A record that trips this wants `gable`.
SHED_RISE_RATIO_MAX = 1.5

# The form attributes whose VALUE this archetype reads — the ones `from_phase` turns
# into a parameter, and therefore the only ones a vertex position can depend on. See
# frame_tavern_params for the full argument; tools/validate.py holds every attribute
# OUTSIDE this set to a `geometry:` declaration on the record, so adding a parameter
# here without adding its name is a gate failure rather than a silently unbuilt
# attribute.
#
# Two names are absent on purpose and the absences are load-bearing:
#
# `stories` — every other building archetype reads it and this one refuses to. An
# outbuilding is one storey; what a barn or a stable has over it is a LOFT, whose only
# external trace is the door you pitch hay through, and that is what `loft` builds. A
# record stating `stories` on an outbuilding will be held to a `geometry:` declaration,
# which is the right outcome: two storeys of wall on a secondary building is a claim,
# and the honest way to state it is `wall_height_m`.
#
# `fenestration` — read for its CONFIDENCE only, never for its value, exactly as in
# frame_tavern. The single small unglazed vent this archetype cuts is a fixed default;
# a tint is not a building, and calling that "consumed" would excuse the omission this
# set exists to surface.
# `finish_key` and `roof_condition` are NOT in this set and must not be, although the
# archetype now reads both (T-0007). This set names FORM attributes — what a phase
# states about the building — and those two live in the record's `reconstruction`
# block, the 665-roof programme's own ledger, one level above the phase. That is why
# no archetype could read them for as long as `from_phase` took only a phase, and it
# is what `docs/RESEARCH/materials.md` §4 finding 4 was pointing at.
CONSUMED = frozenset({
    "construction", "roof_type", "roof_pitch_deg", "wall_height_m",
    "door", "door_side", "door_width_m", "door_height_m",
    "open_sides", "loft", "board_gap_m", "paint",
})

# Where this archetype touches the ground, read by tools/validate.py's ground contact
# check. `perimeter`: the whole footprint outline meets the terrain at local z = 0,
# which is what "y = 0 at the base of the walls" means in docs/GLB-CONTRACT.md.
#
# It holds for the open-sided variants too, and that is not automatic — a wagon shed
# has no wall on one side, so the claim rests on the posts landing at z = 0 and on an
# earth floor being built across the opening. Both are in `outbuilding.py`, and the
# claim would be false without them.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


# ---------------------------------------------------------------- size-aware defaults
#
# Module-level functions rather than methods, because `from_phase` needs them BEFORE
# the object exists — the whole point is that the default depends on the footprint —
# and because a record author reading this file should be able to see the convention
# without instantiating anything. They are conventions, not findings; every one of
# them lands on an attribute whose confidence will be conjectural unless the record
# says otherwise.

def default_wall_height_m(width_m: float, depth_m: float) -> float:
    """Eave height for a building of this footprint.

    Grows with both dimensions, and faster with the SHORT one, because what sets the
    wall of a small outbuilding is headroom (a privy needs a person standing) while
    what sets the wall of a big one is span — a wider building carries a longer tie and
    wants more wall under the same roof. Clamped at both ends: 1.9 m is the least a
    person uses standing, 4.5 m is a two-storey stable and past it a record should say
    the number itself.

    Worked: 1.2 x 1.2 privy -> 1.97 m; 2.4 m smokehouse -> 2.19 m; 4 x 3 woodshed ->
    2.35 m; 13 x 7 stable -> 3.38 m; 20 x 9 livery -> 3.91 m.
    """
    lo, hi = min(width_m, depth_m), max(width_m, depth_m)
    return round(min(4.5, max(1.9, 1.75 + 0.14 * lo + 0.045 * hi)), 3)


def default_roof_type(depth_m: float) -> str:
    """`shed` on a shallow building, `gable` on a deep one.

    A single slope is the cheapest roof there is and it is what most of these buildings
    carried — but it only works over a short run, because the rise is the run times the
    pitch and a shallow pitch will not shed water off riven shakes. Five metres is
    where a shed roof at a workable 18 degrees stops being a roof and starts being a
    wedge: over 5 m it rises 1.6 m, which is most of a wall again.

    The default flips on the DEPTH, not the area: a 20 x 3 m range of stalls is a shed
    roof all day, and a 6 x 6 m barn is not.
    """
    return "shed" if depth_m <= 5.0 else "gable"


def default_roof_pitch_deg(roof_type: str) -> float:
    """32 degrees for a gable, 18 for a shed.

    Both are lower than the 35-38 the house archetypes use, and deliberately: pitch on
    a dwelling is set by wanting a loft under it, and nobody framed a secondary building
    steeper than the covering required. 18 degrees is about the shallowest a riven shake
    roof sheds at, which is why a shed roof is what a shallow building gets.
    """
    return 32.0 if roof_type == "gable" else 18.0


def eave_overhang_m(width_m: float, depth_m: float) -> float:
    """How far this archetype's roof planes stand out past the walls, in metres.

    NAMED HERE rather than left as an expression inside `outbuilding._roof` (T-0274),
    for the reason `shed_axis_for` above is a module-level function: it is not only the
    mesh's business. A SHED's plane continues its slope out over the overhang instead
    of being pinned at the eave — the roof builder says so in as many words — so the
    highest point of a shed roof is not the high wall top, it is the high wall top plus
    this distance times the pitch. Any tool modelling where a shed roof gets to has to
    ask the same number the mesh will, and `generators/archetypes/outbuilding.py`
    cannot be imported outside Blender, which is why the number lives in the params
    module beside the door table `tools/family_bands.eave_floor` already asks for.

    The scaling is the roof builder's own and is not re-argued here: a fixed 0.25 m
    eave is a tenth of a privy's plan on each side and turns it into a mushroom, so the
    overhang grows with the smaller plan dimension between a 0.10 m floor and a 0.35 m
    ceiling.
    """
    return min(0.35, max(0.10, 0.12 + 0.03 * min(width_m, depth_m)))


def shed_axis_for(open_sides) -> str:
    """Which way a shed roof falls: 'y' front-to-back, 'x' side-to-side.

    DERIVED FROM THE OPEN SIDES, not taken as a parameter, and this is the rule that
    makes a wagon shed a wagon shed. The opening has to be under the TALL eave: a
    loaded hay wagon that clears a 2.4 m wall does not clear the 2.4 m wall at the
    other end of the slope. So one open side sets the axis across itself; two OPPOSITE
    open sides are a drive-through and the roof has to fall along the other axis or one
    of the two openings is the low one.

    It is a module-level function and not only a property because the run a shed climbs
    IS this choice — 'y' climbs the depth and 'x' the width — so a tool asking whether a
    family's ridge band can carry a shed has to ask the same question the mesh will
    (T-0179). `tools/ridge_model.py` calls this rather than retyping it; retyping it is
    how a model of an archetype drifts from the archetype.
    """
    op = set(open_sides)
    fb, lr = op & {"front", "back"}, op & {"left", "right"}
    if len(fb) == 1 and not lr:
        return "y"
    if len(lr) == 1 and not fb:
        return "x"
    if len(fb) == 2 and len(lr) <= 1:
        return "x"
    if len(lr) == 2 and len(fb) <= 1:
        return "y"
    return "y"


@dataclass
class OutbuildingParams:
    """A stable, shed, barn, smokehouse, privy, crib or woodshed.

    Dimensions are metres and describe the whole building. x runs along `width_m`,
    y along `depth_m`, and the facade — the `front` side — is +y, which the exporter
    turns into the bearing `rotation_deg` names. z = 0 is the base of the walls.
    """

    # massing
    width_m: float
    depth_m: float
    wall_height_m: float | None = None      # None -> default_wall_height_m
    roof_type: str | None = None            # None -> default_roof_type
    roof_pitch_deg: float | None = None     # None -> default_roof_pitch_deg
    construction: str = "plank"

    # The elevations that are posts and open air. Empty for a closed building.
    # Normalised to a sorted tuple in `from_phase` so that two records listing the
    # same sides in different orders hash to the same mesh inputs.
    open_sides: tuple = ()

    # The doorway. `door` names what has to get through it; the two explicit
    # dimensions override the class when a record has a measurement, which no record
    # in this dataset does yet.
    door: str = "man"
    door_side: str = "front"
    door_width_m: float | None = None
    door_height_m: float | None = None

    # A hay or storage loft. As in log_dwelling, the loft leaves exactly one external
    # trace and the archetype builds that and nothing else: the door you pitch through,
    # high in a gable end or under the tall eave of a shed roof. No dormer, no floor
    # line, no second range of openings — those would be evidence we do not have.
    loft: bool = False

    # The gap between siding boards, and the single parameter that turns a shed into a
    # corn crib. Sawn boards shrink and were nailed up green, so a small gap is the
    # crude default rather than a defect; a crib is the same wall with the boards
    # spaced on purpose so the corn dries. Ignored by `log` construction, where the
    # gap between courses is chinked.
    board_gap_m: float = 0.012

    paint: str = "unpainted"

    # The finish the 665-roof programme dealt this building, and how weathered its
    # roof is. NOT form attributes — they live in the record's `reconstruction`
    # block, which is why `from_phase` takes the record — and until T-0007 they were
    # read by `generators/inferred_placeholder.py` alone, so a weathered roof and a
    # fresh one were the same pixel on every archetype building in the town
    # (docs/RESEARCH/materials.md §4 finding 4). None on every named or documented
    # building, which carries no reconstruction block and therefore keeps exactly the
    # colours it had. `common/materials.py` is what turns either into a surface.
    finish_key: str | None = None
    roof_condition: str | None = None

    # per-attribute confidence, keyed by the attribute name in the record
    confidence: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Defaults are resolved HERE rather than in `from_phase`, so that a golden
        # case written by hand in generators/preview.py gets the same size-aware
        # behaviour a record does. A default that only applies on one of the two
        # paths is a difference between the reference image and the town.
        if self.roof_type is None:
            self.roof_type = default_roof_type(self.depth_m)
        if self.roof_pitch_deg is None:
            self.roof_pitch_deg = default_roof_pitch_deg(self.roof_type)
        if self.wall_height_m is None:
            self.wall_height_m = default_wall_height_m(self.width_m, self.depth_m)
        self.open_sides = tuple(sorted(set(self.open_sides)))

    # ------------------------------------------------------------------ confidence

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the contract's rule for geometry driven by several
        attributes."""
        return max((self.conf(a) for a in attrs), default=1.0)

    # -------------------------------------------------------------- derived geometry
    #
    # Every one of these is hashed by generators/mesh_inputs.py along with the fields,
    # because a derived constant is as load-bearing as a stated one. They must stay
    # cheap, total, and JSON-serialisable.

    @property
    def ridge_along_x(self) -> bool:
        """A gable ridge runs down the long axis. Same rule as the other archetypes,
        so a stable and a cabin of the same plan point their gables the same way."""
        return self.width_m >= self.depth_m

    @property
    def shed_axis(self) -> str:
        """Which way a shed roof falls: 'y' front-to-back, 'x' side-to-side.

        DERIVED FROM THE OPEN SIDES, not taken as a parameter — see `shed_axis_for`,
        which is this rule and is a module-level function so that a tool asking "how
        high would a shed on this plan stand?" can read the rule instead of retyping
        it (T-0179).
        """
        return shed_axis_for(self.open_sides)

    @property
    def shed_high_side(self) -> str:
        """The side a shed roof stands tallest on.

        An open side takes it, per `shed_axis`. With nothing open the tall wall goes
        at the BACK and the water runs off in front of the door — log_dwelling's
        convention, restated here rather than imported so the two cannot drift, and a
        convention rather than an attested fact in both places.
        """
        op = set(self.open_sides)
        if self.shed_axis == "y":
            if "front" in op and "back" not in op:
                return "front"
            return "back"
        if "left" in op and "right" not in op:
            return "left"
        return "right"

    @property
    def roof_run_m(self) -> float:
        """The horizontal run one roof plane covers, before overhang. A gable's plane
        covers half the span across the ridge; a shed's covers the whole thing."""
        if self.roof_type == "shed":
            return self.depth_m if self.shed_axis == "y" else self.width_m
        return (self.depth_m if self.ridge_along_x else self.width_m) / 2.0

    @property
    def roof_rise_m(self) -> float:
        return round(self.roof_run_m * math.tan(math.radians(self.roof_pitch_deg)), 4)

    @property
    def apex_z_m(self) -> float:
        """Top of the roof surface — the ridge, or the high eave of a shed."""
        return round(float(self.wall_height_m) + self.roof_rise_m, 4)

    @property
    def door_size_m(self) -> tuple:
        """(clear width, clear height) of the doorway, in metres."""
        if self.door == "none":
            return (0.0, 0.0)
        dw, dh = DOOR_SIZE_M.get(self.door, DOOR_SIZE_M["man"])
        return (round(float(self.door_width_m if self.door_width_m is not None else dw), 4),
                round(float(self.door_height_m if self.door_height_m is not None else dh), 4))

    @property
    def loft_side(self) -> str | None:
        """Which elevation carries the loft door, or None when there is no loft.

        A gable roof puts it in a gable END, which is where you pitch hay from a wagon
        standing at the end of the building. A shed roof has no gable, so it goes under
        the TALL eave, which is the only wall with height to spare. Either way the wall
        has to be closed and must not already carry the main door — two openings in one
        small elevation is a facade, and these buildings do not have facades.
        """
        if not self.loft:
            return None
        if self.roof_type == "shed":
            candidates = [self.shed_high_side]
        elif self.ridge_along_x:
            candidates = ["right", "left"]
        else:
            candidates = ["front", "back"]
        taken = self.door_side if self.door != "none" else None
        for side in candidates:
            if side not in self.open_sides and side != taken:
                return side
        return None

    @property
    def loft_door_size_m(self) -> tuple:
        """(width, height) of the hay door, shrunk to what its wall can hold.

        A gable narrows as it rises, so the door's own width is set by the wall it is
        cut into rather than by a constant: at 74 per cent of the way up a gable there
        is only a quarter of the half-span left, and a 0.95 m door on a 4 m gable end
        would run out through the rake. Returns (0, 0) when there is no loft; `validate`
        refuses anything under 0.55 m rather than build a hatch and call it a hay door.
        """
        side = self.loft_side
        if side is None:
            return (0.0, 0.0)
        rise = self.roof_rise_m
        if self.roof_type == "shed":
            half_avail = self.side_run_m(side) / 2.0 - 0.35
            height = min(1.05, (float(self.wall_height_m) + rise) * 0.35)
        else:
            # The gable's half-span at the DOOR HEAD, which is its narrowest point.
            half_span = self.roof_run_m
            half_avail = half_span * (1.0 - 0.74) - 0.10
            height = min(1.05, max(0.55, rise * 0.62))
        return (round(max(0.0, min(0.95, 2.0 * half_avail)), 4), round(height, 4))

    def side_run_m(self, side: str) -> float:
        """How long the wall on this side is, along the ground."""
        return self.width_m if side in ("front", "back") else self.depth_m

    # ------------------------------------------------------------------- validation

    def validate(self) -> None:
        # 0.9 m is a privy that a person can shut the door of; 30 m is longer than any
        # building attested in the town in 1835, so an outbuilding past it is an
        # arithmetic accident and not a barn.
        for name, v in (("width_m", self.width_m), ("depth_m", self.depth_m)):
            if not 0.9 <= v <= 30.0:
                raise ParamError(
                    f"{name} {v} outside 0.9-30 m. This archetype spans a privy to a "
                    f"livery stable and refuses both ends of that on purpose: under "
                    f"0.9 m nothing fits through the door, over 30 m the record is "
                    f"describing a building the town did not have")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(
                f"construction '{self.construction}' not in {CONSTRUCTIONS}. A framing "
                f"method behind the boards is not visible at this level of detail and "
                f"is unattested for every outbuilding in the dossiers, so this "
                f"archetype's vocabulary names only what a viewer can see")
        if self.roof_type not in ROOF_TYPES:
            raise ParamError(
                f"roof_type '{self.roof_type}' not in {ROOF_TYPES}. outbuilding builds "
                f"gable and shed only; a hip or gambrel on a stable at the forks in "
                f"1835 would be an invention, so it is refused rather than substituted")
        if self.paint not in PAINTS:
            raise ParamError(f"paint '{self.paint}' not in {PAINTS}")

        wall_z = float(self.wall_height_m)
        if not 1.7 <= wall_z <= 6.5:
            raise ParamError(f"wall_height_m {wall_z} outside 1.7-6.5 m")
        if not 6.0 <= float(self.roof_pitch_deg) <= 55.0:
            raise ParamError(f"roof_pitch_deg {self.roof_pitch_deg} outside 6-55 deg")

        # The check that actually keeps the wide end of the family honest. An angle
        # inside its range still builds a ski jump once the run is long enough, and
        # nothing about "18 degrees" says so — the RISE is what a person sees.
        if self.roof_type == "shed" and self.roof_rise_m > SHED_RISE_RATIO_MAX * wall_z:
            raise ParamError(
                f"a shed roof at {self.roof_pitch_deg} deg over a {self.roof_run_m} m "
                f"run rises {self.roof_rise_m:.2f} m on a {wall_z:.2f} m wall. Past "
                f"{SHED_RISE_RATIO_MAX} x the wall the roof is the building and the "
                f"wall is a skirt; use roof_type 'gable', or a shallower pitch")
        if self.apex_z_m > MAX_HEIGHT_M:
            raise ParamError(
                f"the roof reaches {self.apex_z_m} m, past the {MAX_HEIGHT_M} m ceiling "
                f"this archetype sets. No building in 1835 Chicago exceeded three "
                f"storeys and none of them was a shed")

        self._validate_openness()
        self._validate_door()
        if not 0.0 <= self.board_gap_m <= 0.15:
            raise ParamError(
                f"board_gap_m {self.board_gap_m} outside 0-0.15 m. Past 150 mm the "
                f"boards are further apart than they are wide and the wall is a fence")
        if self.loft and self.loft_side is None:
            raise ParamError(
                "loft is set but every elevation that could carry the loft door is "
                "either open or already carries the main door. Close one, move the "
                "door, or drop the loft — an archetype that quietly puts the hay door "
                "somewhere else is inventing the building's working arrangement")
        if self.loft and self.loft_door_size_m[0] < 0.55:
            raise ParamError(
                f"the loft door would be {self.loft_door_size_m[0]:.2f} m wide once it "
                f"is fitted inside the '{self.loft_side}' elevation's top. Nothing is "
                f"forked through a 0.55 m hole: this building is too small or too flat "
                f"in the roof to have had a hay loft, and a hatch drawn where a hay "
                f"door should be is a claim about how the building was worked")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")

    def _validate_openness(self) -> None:
        for s in self.open_sides:
            if s not in SIDES:
                raise ParamError(f"open_sides names '{s}', which is not one of {SIDES}")
        if self.open_sides and self.construction == "log":
            raise ParamError(
                "log construction cannot have an open side. A notched log pen is held "
                "up by its corners: take a wall away and the two corners it carried go "
                "with it. An open-sided log shelter is a post structure with log "
                "infill, which is a different building — record it as 'plank' or "
                "'light_frame', or close the side")
        if self.construction == "log" and min(self.width_m, self.depth_m) < LOG_MIN_DIM_M:
            raise ParamError(
                f"a {self.width_m} x {self.depth_m} m log building has a shorter side "
                f"than {LOG_MIN_DIM_M} m, and this archetype's corner notches protrude "
                f"0.24 m past every corner — they would meet near the middle of that "
                f"wall. Small outbuildings here are boarded; record it as 'plank'")

    def _validate_door(self) -> None:
        if self.door not in DOOR_KINDS:
            raise ParamError(
                f"door '{self.door}' not in {DOOR_KINDS}. It names what has to get "
                f"through the opening, not whether there was one — a boolean cannot "
                f"say that a stable door is a horse wide")
        if self.door == "none":
            return
        if self.door_side not in SIDES:
            raise ParamError(f"door_side '{self.door_side}' not in {SIDES}")
        if self.door_side in self.open_sides:
            raise ParamError(
                f"the door is on the '{self.door_side}' side and that side is open. An "
                f"opening in an opening is nothing; put the door on a closed elevation "
                f"or set door 'none'")
        dw, dh = self.door_size_m
        run = self.side_run_m(self.door_side)
        if dw + 2 * DOOR_JAMB_M > run:
            raise ParamError(
                f"a '{self.door}' door is {dw} m clear and needs {dw + 2 * DOOR_JAMB_M:.2f} m "
                f"of wall with its jambs, but the '{self.door_side}' elevation is only "
                f"{run} m long. Widen the footprint, move the door to the long side, or "
                f"record a smaller door — an archetype that shrinks the door to fit is "
                f"deciding what the building was for")
        if dh > float(self.wall_height_m) - 0.08:
            raise ParamError(
                f"a '{self.door}' door is {dh} m clear and the wall is "
                f"{self.wall_height_m} m, leaving no header. A wagon door needs its "
                f"wall: state wall_height_m, or record a smaller door")


def from_phase(phase: dict, record: dict | None = None) -> OutbuildingParams:
    """Resolve one structure phase into generator parameters.

    Reads only the attested `value` of each form attribute plus its confidence.
    Footprint dimensions come from the phase footprint polygon's bounding box — the
    polygon is authoritative, width and depth are derived.
    """
    form = phase.get("form", {})

    def val(attr, default=None):
        a = form.get(attr)
        return default if a is None else a.get("value", default)

    def conf(attr, default="reconstructed"):
        a = form.get(attr)
        return default if a is None else a.get("confidence", default)

    poly = phase.get("footprint", {}).get("polygon") or []
    if len(poly) < 3:
        raise ParamError("footprint polygon needs at least 3 points")
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    width, depth = max(xs) - min(xs), max(ys) - min(ys)

    # The contract pins the mesh origin to polygon coordinate (0, 0). Deriving only a
    # bounding-box SIZE and then building from the origin silently translates any
    # polygon not anchored there — see frame_tavern_params, where this refusal was
    # written after the same class of silent 6 m displacement.
    if abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise ParamError(
            f"footprint polygon starts at ({min(xs)}, {min(ys)}), not the origin. "
            f"docs/GLB-CONTRACT.md pins the mesh origin to polygon coordinate (0, 0); "
            f"building from a bounding box would silently move the structure "
            f"{max(abs(min(xs)), abs(min(ys))):.2f} m from where its footprint puts it. "
            f"Re-anchor the polygon at the origin and put the offset in position.")

    # `reconstruction` is the 665-roof programme's own block: it is present on every
    # anonymous or household roof it dealt and absent from every named building.
    recon = (record or {}).get("reconstruction") or {}
    confidences = {a: conf(a) for a in form}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")

    open_sides = val("open_sides", ())
    if isinstance(open_sides, str):
        raise ParamError(
            f"open_sides is the string '{open_sides}'; it is a LIST of elevations, "
            f"because a hay shelter is open on more than one")

    door = val("door", "man")
    if isinstance(door, bool):
        raise ParamError(
            "door is a boolean. It names what has to get through the opening — one of "
            f"{DOOR_KINDS} — because 'there was a door' does not say whether a horse "
            f"could use it, and that is the whole difference between a stable and a shed")

    p = OutbuildingParams(
        width_m=round(width, 3),
        depth_m=round(depth, 3),
        wall_height_m=(None if val("wall_height_m") is None
                       else float(val("wall_height_m"))),
        roof_type=(None if val("roof_type") is None else str(val("roof_type"))),
        roof_pitch_deg=(None if val("roof_pitch_deg") is None
                        else float(val("roof_pitch_deg"))),
        construction=str(val("construction", "plank")),
        open_sides=tuple(str(s) for s in (open_sides or ())),
        door=str(door),
        door_side=str(val("door_side", "front")),
        door_width_m=(None if val("door_width_m") is None
                      else float(val("door_width_m"))),
        door_height_m=(None if val("door_height_m") is None
                       else float(val("door_height_m"))),
        loft=bool(val("loft", False)),
        board_gap_m=float(val("board_gap_m", 0.012)),
        paint=str(val("paint", "unpainted")),
        # The programme's own finish deal, read off the record rather than the
        # phase. `wall_finish` in `common/materials.py` states the order these are
        # applied in and why a stated coating outranks them.
        finish_key=recon.get("finish_key"),
        roof_condition=recon.get("roof_condition"),
        confidence=confidences,
    )
    p.validate()
    return p


# ---------------------------------------------------------------------------
# THE OPENINGS, and where they fall on each elevation (T-0459).
#
# These live here so that something with no Blender can ask WHERE THE OPENINGS
# ARE. The signage layer is the caller that needed it: eight of this archetype's
# sheds carry a painted name, and the generator that placed them knew the wall's
# height and its frontage and nothing at all about the doorway in the middle of it.

# THE BUILDER READS THESE (T-0520). It used to compute the same rectangles beside
# them, which made two copies of one set-out and left a written rule — change one,
# change the other — as the only thing holding them together. It does not any more:
# the builder calls these functions, so an opening moved here moves on the mesh a
# visitor sees, and there is nowhere else to move it. What made that a ticket of its
# own is that the asset staleness hash covers each archetype's builder module BYTE
# FOR BYTE, so touching the three builders staled 212 assets and demanded the
# town-wide rebake that landed with the refactor.
# ---------------------------------------------------------------------------

def loft_rect(p: "OutbuildingParams") -> tuple:
    """(u0, u1, z0, z1) of the hay door on `p.loft_side`."""
    side = p.loft_side
    run = p.side_run_m(side)
    dw, dh = p.loft_door_size_m
    if p.roof_type == "shed":
        z1 = float(p.wall_height_m) + p.roof_rise_m - 0.22
    else:
        z1 = float(p.wall_height_m) + p.roof_rise_m * 0.74
    return (run / 2.0 - dw / 2.0, run / 2.0 + dw / 2.0, z1 - dh, z1)


def vent_rect(p: "OutbuildingParams"):
    """The one small unglazed opening this archetype gives a closed outbuilding, as
    `(side, (u0, u1, z0, z1))`, or None.

    A FIXED DEFAULT, not a record's value: `fenestration` is read for its confidence
    and never for its value, exactly as in frame_tavern, because a tint is not a
    building. A stable with no opening but its door is a crate, and a smokehouse needs
    to breathe — but the size, the shape and the position of this hole are the
    archetype's, and docs/LIBERTIES.md owns them the moment a record uses this
    archetype.

    Skipped on anything under 2.4 m: a privy's ventilation is the gaps between its own
    boards, and cutting a window in one would be inventing a fitting.
    """
    if min(p.width_m, p.depth_m) < 2.4 or p.open_sides:
        return None
    order = ["back", "left", "right", "front"]
    for side in order:
        if side == p.door_side and p.door != "none":
            continue
        if side == p.loft_side:
            continue
        run = p.side_run_m(side)
        if run < 1.4:
            continue
        z1 = min(float(p.wall_height_m) - 0.30, 2.35)
        if z1 < 1.2:
            continue
        return (side, (run * 0.62 - 0.19, run * 0.62 + 0.19, z1 - 0.32, z1))
    return None


def openings(p: "OutbuildingParams") -> dict:
    """side -> [(kind, u0, u1, z0, z1), ...] — every hole in the building.

    Independent of construction, unlike `boarding_holes`: a log shed's doorway is
    drawn as an assembly standing in FRONT of the logs rather than as a hole cut
    through them, but it is still a doorway, and a name painted across it is still
    a name painted across a doorway.
    """
    out: dict = {}
    if p.open_sides:
        # An open bay runs the whole elevation and up to the plate under the eave —
        # `_plate_z` in the mesh module, the LOWEST point of that elevation's top
        # profile, which on a shed's high side is the wall height plus the whole
        # rise. The bound here is that maximum rather than the exact plate, and
        # deliberately generous: the only solid face an open side has is the beam
        # itself, 0.18 m of it, which is a member and not a wall, and a caller
        # asking "may something be fixed here" must not be told yes because a
        # hand's breadth of timber crosses the top of a wagon bay.
        for side in p.open_sides:
            out.setdefault(side, []).append(
                ("open_bay", 0.0, p.side_run_m(side), 0.0,
                 float(p.wall_height_m) + p.roof_rise_m))
    if p.door != "none":
        dw, dh = p.door_size_m
        um = p.side_run_m(p.door_side) / 2.0
        out.setdefault(p.door_side, []).append(
            ("door", um - dw / 2.0, um + dw / 2.0, 0.0, dh))
    if p.loft and p.loft_side:
        u0, u1, z0, z1 = loft_rect(p)
        out.setdefault(p.loft_side, []).append(("loft_door", u0, u1, z0, z1))
    v = vent_rect(p)
    if v:
        side, (u0, u1, z0, z1) = v
        out.setdefault(side, []).append(("vent", u0, u1, z0, z1))
    return out


def boarding_holes(p: "OutbuildingParams") -> dict:
    """side -> [(u0, u1, z0, z1), ...] to be cut out of the boarding.

    Only meaningful for boarded construction; the log path ignores it, because a hole in
    a log wall is not a hole in this model. The open bays are not listed either — an
    open side has no boarding to cut.
    """
    if p.construction == "log":
        return {}
    return {side: [(u0, u1, z0, z1) for kind, u0, u1, z0, z1 in rects
                   if kind != "open_bay"]
            for side, rects in openings(p).items()}


def front_openings(p: "OutbuildingParams") -> list[dict]:
    """Everything on the front wall a signboard must not be hung over, in footprint
    coordinates: `u` along the front from the polygon's origin, `z` above the base of
    the walls. The archetype's `front` side IS the footprint's max-v edge (see `_to3`
    in the mesh module), so no transform is needed."""
    return [{"kind": kind, "u0": u0, "u1": u1, "z0": z0, "z1": z1}
            for kind, u0, u1, z0, z1 in openings(p).get("front", [])]
