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
DOOR_KINDS = ("none", "man", "stable", "wagon", "cargo")
DOOR_SIZE_M = {
    "man": (0.86, 1.88),      # one person, a barrow, an armful of wood
    "stable": (1.35, 2.30),   # a horse led through in hand, single leaf
    "wagon": (2.90, 3.00),    # a loaded wagon and its team, double leaf
    "cargo": (2.20, 2.35),    # goods handed in off a wagon bed or a boat
}

# WHY `cargo` EXISTS, AND WHY IT IS NOT A NARROW WAGON DOOR (T-1662).
#
# Family F1 in data/reconstruction/1835_family_archetype_crosswalk.json is the
# freight or storage shed, it is drawn by this archetype, and its required variant
# is `freight_shed_low` — *"wide doors; low openings; dockside skids"*. Until this
# entry the only wide door here was `wagon`, and a wagon door is the wrong shape for
# the family in a way that is measurable rather than aesthetic:
#
#   * IT IS NOT LOW. The clear head is 3.00 m and this archetype's validator wants
#     more wall than that above the floor, so `tools/family_bands.eave_floor` — which
#     asks THIS TABLE rather than retyping it — returns 3.08 m for any F1 roof. F1's
#     own authored eave band is 10-13 ft, 3.048 to 3.962 m. The door therefore put
#     the family's eave FLOOR 32 mm above the bottom of the band the same file
#     authors, and no F1 shed in this town can be built at the low end of its own
#     band. `cargo` returns the band: 2.35 + 0.08 = 2.43 m, under all of it.
#   * IT IS ONE DOOR. The family says door*s*, and F1's evidence note asks for
#     "long-building framing, cargo openings" — plural. A single 2.9 m opening in
#     the middle of an eleven-metre shed is a barn; freight came off a wagon bed or
#     a boat at more than one point along the loading side, which is what
#     `door_bays` below sets out.
#
# THE TWO NUMBERS, AND WHAT EACH ONE RESTS ON. Both are liberties (docs/LIBERTIES.md
# L278) and neither is a reading of any source — no surviving record describes a
# Chicago freight-shed door in 1835.
#
#   HEIGHT 2.35 m is DERIVED, and the derivation is reproducible here: it is the
#   largest 0.05 m step whose head plus this module's own header stock leaves at
#   least half a metre of boarded wall under F1's LOWEST authored eave. 2.35 + 0.16
#   = 2.51 m of frame, and 3.048 - 2.51 = 0.538 m of board above it. The next step
#   up, 2.40 m, leaves 0.488 m and is refused. That is what "low" is made to mean:
#   an opening the family's own eave band can carry all the way down.
#
#   WIDTH 2.20 m is INVENTED and bounded. It is wider than `stable` (1.35 m, a horse
#   in hand) because the family says wide, and narrower than `wagon` (2.90 m, a team)
#   because no team goes through it — the load is handed in off the bed. The bound
#   that fixes it is the rhythm: two of these with their jambs occupy 5.04 m, which
#   is 72 % of the median front F1's own footprint band allows (18-28 ft, median
#   7.01 m), leaving 0.66 m of pier at each corner and between them. A wagon door
#   cannot do that on any front in the band, which is the whole reason the family
#   needed an opening of its own.

# Jamb and header stock either side of the clear opening. The door has to fit the WALL,
# not merely be under some maximum, so this is part of the check.
DOOR_JAMB_M = 0.16

# The narrowest CLEAR board this archetype will leave between two openings on one
# elevation. A pier thinner than the jamb stock that flanks it is not a pier — it is
# two door frames touching — so the floor is those two jambs, and below it the wall
# stops reading as a wall with doors in it and starts reading as one ragged hole.
DOOR_PIER_MIN_M = 2 * DOOR_JAMB_M

# --- the forge stack ---------------------------------------------------------------
#
# WHY AN OUTBUILDING MAY COUNT A CHIMNEY (T-1680). Family W1 in
# data/reconstruction/1835_family_archetype_crosswalk.json is the blacksmith shop, it is
# drawn by this archetype, and its required variant is `blacksmith_forge` — *"wide work
# door; forge chimney; soot; detached"*. Until this entry there was no way to say it:
# every other building archetype in the project reads `chimneys` and this one did not,
# so the town's four smithies came out of the bake as sheds with a doorway and no
# flue. `pierce_blacksmith_shop` says so on its own record, in a `geometry: absent`
# note that has stood since the record was written — *"the mesh shows a shed with a
# doorway and NO SMOKE, which is the one feature of a smithy anybody in the street
# would have noticed"*.
#
# IT IS THE TOWN'S OWN ATTRIBUTE, NOT A NEW ONE, and that is the whole reason it is
# spelt `chimneys` rather than `forge_chimney`. Three instruments read a stack off a
# record — `tools/measure_stack_ordinance.py` (the 18-inch by-law of 1835, a GATE),
# `tools/measure_stack_fabric.py` (a stack painted its own roof, a GATE) and
# `tools/measure_stack_projection.py` (Andreas's four feet, a report) — and all three
# find one by asking `form.chimneys` for a whole number. A private spelling here would
# have drawn the only stacks in Chicago that no gate could see.
#
# DEFAULT ZERO, WHICH IS THE OPPOSITE OF EVERY OTHER ARCHETYPE'S DEFAULT. A house has a
# fire in it; a privy, a corn crib, a hay shelter and a wagon shed do not, and 133 of
# this archetype's assets are standing today with no stack and no record asking for
# one. So the count is what a record STATES, and an absent `chimneys` means no stack
# rather than one.
#
# ONE, AND NEVER TWO. A second flue on a secondary building is a claim about how the
# building was worked — two fires, or a fire and a stove — and nothing in the dossiers
# says that of any shop at the forks. A record that wants two is describing a house.
MAX_CHIMNEYS = 1

# The smallest plan this archetype will stand a stack on. A forge is a hearth, an
# anvil and room to bring a horse in beside them; 3 m each way is the least that holds
# any of it, and under it the record is putting a chimney on a privy. The number is a
# convention and not a reading, like every other bound in this module.
CHIMNEY_MIN_PLAN_M = 3.0

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
    "door", "door_side", "door_width_m", "door_height_m", "door_bays",
    "open_sides", "loft", "board_gap_m", "paint", "chimneys",
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

    # How many of that doorway stand on `door_side`, set out evenly with equal piers
    # between them and at each corner. One is a shed; more than one is a building
    # worked at several points along its loading side, which is what family F1's
    # "wide doors" and "cargo openings" ask for and what nothing here could say
    # before T-1662. A COUNT FROM THE RECORD, never derived from the wall: an
    # archetype that decides for itself how many doors a building had is deciding
    # how it was worked. The validator refuses a count the elevation cannot carry
    # rather than quietly dropping one, for the same reason it refuses a door the
    # wall cannot header.
    door_bays: int = 1

    # A hay or storage loft. As in log_dwelling, the loft leaves exactly one external
    # trace and the archetype builds that and nothing else: the door you pitch through,
    # high in a gable end or under the tall eave of a shed roof. No dormer, no floor
    # line, no second range of openings — those would be evidence we do not have.
    loft: bool = False

    # The forge stack, and the only fire this archetype builds. See MAX_CHIMNEYS above
    # for why it is spelt with the town's own name and why it defaults to none: a
    # smithy has a flue and a corn crib does not, and 133 of this archetype's assets
    # are the second kind. The stack is BRICK and INTERIOR — it stands against the end
    # wall inside the shop and breaks the roof — which is `docs/RESEARCH/chimneys.md`
    # §2's disposition rather than §3's, and deliberately: §3's cat-and-clay is argued
    # for a stack built OUTSIDE a gable so it can be pulled away when it fires, and a
    # forge fire is a hearth kept hot all day under a board roof. Blodgett's yard had
    # been making brick on the North Side since the spring of 1833 (andreas_1884_v1,
    # `brickyard_north_side`), so the masonry a forge needs is in the town and needs no
    # import. Where the stack stands is `outbuilding._stack_wall`; that it stands
    # anywhere at all is an invention and owes docs/LIBERTIES.md an entry.
    chimneys: int = 0

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
    def door_spans_m(self) -> list:
        """`[(u0, u1), ...]` — the clear opening of every doorway on `door_side`,
        left to right in that elevation's own `u`.

        ONE set-out, asked for by the builder that draws the frames, by `openings()`
        which tells a signboard where it may not hang, and by the validator that
        refuses a count the wall cannot carry. It used to be three lines of
        arithmetic inside `openings()` and `_doorway`, each centring one door on the
        wall, and the moment there could be more than one door that arrangement
        would have had the frames in one place and the holes in the boarding in
        another.

        The rhythm is even and symmetrical: n openings, each with its jamb stock,
        and n + 1 equal piers — one at each corner and one between every pair. A
        freight shed's loading side is a frame with bays in it, not a wall with
        doors punched wherever they fit, and an even set-out is the only one that
        does not claim a plan this project has no evidence for.
        """
        dw, _dh = self.door_size_m
        if dw <= 0.0 or self.door_bays < 1:
            return []
        n = int(self.door_bays)
        run = self.side_run_m(self.door_side)
        if n == 1:
            # ONE BAY IS THE OLD CENTRING, WRITTEN THE OLD WAY, AND THAT IS NOT
            # fussiness. The general formula below is the same quantity for n = 1
            # but not the same DOUBLE: (run - dw - 2j)/2 + j differs from
            # run/2 - dw/2 in the last bit, which is nothing on a wall and enough
            # to move a two-decimal rounding. Measured when it was written the
            # other way: two of the town's business signboards jumped to the far
            # side of their building, because `tools/generate_business_signboards.py`
            # picks a clear span off these rectangles and the tie between the span
            # left of the door and the span right of it broke the other way. 133 of
            # the town's 134 outbuildings carry a single door and none of them may
            # move for a change about freight sheds.
            um = run / 2.0
            return [(um - dw / 2.0, um + dw / 2.0)]
        framed = dw + 2 * DOOR_JAMB_M
        pier = (run - n * framed) / (n + 1)
        # NOT ROUNDED, and that is deliberate. With one bay this arithmetic reduces
        # to the centred door the archetype has always drawn, and rounding it to
        # four places moved eleven of the town's single-door outbuildings by a
        # fraction of a tenth of a millimetre — enough to change every one of their
        # GLBs and nothing a visitor could ever see. A set-out that churns the bake
        # for no visible reason is a set-out nobody will trust the next time it does.
        out = []
        for i in range(n):
            a = pier * (i + 1) + framed * i + DOOR_JAMB_M
            out.append((a, a + dw))
        return out

    @property
    def door_pier_m(self) -> float:
        """The clear board the even set-out leaves at each gap — between two
        openings, and at each corner beside the outermost one. With a single
        doorway this is just the margin either side of a centred door, which is
        why the validator only holds it to a floor when there is a rhythm."""
        dw, _dh = self.door_size_m
        n = max(1, int(self.door_bays))
        run = self.side_run_m(self.door_side)
        return round((run - n * (dw + 2 * DOOR_JAMB_M)) / (n + 1), 4)

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
        self._validate_chimney()
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

    def _validate_chimney(self) -> None:
        """The forge stack's own refusals. T-1680.

        Each one is a claim the record would be making that this archetype cannot
        stand behind, and each is refused rather than quietly dropped — a stack the
        builder declines to draw on a record that counts one is a building the
        ordinance gate then reads as an offender, which is the wrong failure.
        """
        if isinstance(self.chimneys, bool) or not isinstance(self.chimneys, int):
            raise ParamError(
                f"chimneys {self.chimneys!r} is not a whole number. It is a COUNT, the "
                f"same count every other archetype in this project reads, because the "
                f"three instruments that measure a stack find one by asking for one")
        if not 0 <= self.chimneys <= MAX_CHIMNEYS:
            raise ParamError(
                f"chimneys {self.chimneys} outside 0..{MAX_CHIMNEYS} on an outbuilding. "
                f"A second flue on a secondary building is a claim about how it was "
                f"worked — two fires, or a fire and a stove — and nothing in the "
                f"dossiers says that of any shop at the forks")
        if self.chimneys <= 0:
            return
        if min(self.width_m, self.depth_m) < CHIMNEY_MIN_PLAN_M:
            raise ParamError(
                f"chimneys {self.chimneys} on a {self.width_m} x {self.depth_m} m plan. "
                f"Under {CHIMNEY_MIN_PLAN_M} m each way there is no room for a hearth, "
                f"an anvil and the working space beside them: this is a chimney on a "
                f"privy, and the record is describing a different building")
        wall = self.stack_wall
        if wall in self.open_sides:
            raise ParamError(
                f"chimneys {self.chimneys}, but every elevation this stack could stand "
                f"against is open ('{wall}'). A flue is built against a wall; close one, "
                f"or the building is a forge under a roof on posts, which is a "
                f"different thing and is not drawn here")

    @property
    def stack_wall(self) -> str:
        """The elevation the forge stack stands against, inside the building.

        THE END WALL, and the end is chosen by the ROOF rather than by preference: on a
        gable the two ends are the gables, so a stack there rises under the ridge and
        breaks the roof at its highest point, which is `docs/RESEARCH/chimneys.md` §2's
        interior disposition and the shortest flue that clears the building. On a shed
        the ends are the two walls the slope does not fall along, and the same rule
        picks one.

        Of the two, the one that does NOT carry the main door wins — a forge stands
        where the doorway is not, or the hearth is in the traffic — and with the door
        elsewhere the low end of the axis takes it, which is `log_dwelling._chimneys`'
        habit restated so two archetypes put a stack on the same end of the same plan.
        """
        if self.roof_type == "gable":
            ends = ("left", "right") if self.ridge_along_x else ("back", "front")
        else:
            ends = ("back", "front") if self.shed_axis == "x" else ("left", "right")
        free = [s for s in ends if s != self.door_side and s not in self.open_sides]
        if free:
            return free[0]
        open_free = [s for s in ends if s not in self.open_sides]
        return open_free[0] if open_free else ends[0]

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
        if int(self.door_bays) != self.door_bays or self.door_bays < 1:
            raise ParamError(
                f"door_bays is {self.door_bays!r} and a doorway is a whole doorway. A "
                f"building with no door says door 'none'; one with a door says 1")
        dw, dh = self.door_size_m
        n = int(self.door_bays)
        run = self.side_run_m(self.door_side)
        need = n * (dw + 2 * DOOR_JAMB_M)
        if need > run:
            raise ParamError(
                f"{n} '{self.door}' door(s) are {dw} m clear each and need {need:.2f} m "
                f"of wall with their jambs, but the '{self.door_side}' elevation is only "
                f"{run} m long. Widen the footprint, move the door to the long side, "
                f"record fewer bays, or record a smaller door — an archetype that "
                f"shrinks the door to fit is deciding what the building was for")
        # ONLY ASKED OF A RHYTHM, and deliberately. With one doorway the set-out
        # centres it and the wall either side is whatever the elevation has left —
        # which on a 1.67 m privy is 0.25 m and has always been the right answer.
        # Imposing a corner margin on those would refuse 130 outbuildings that were
        # never in question. What is new here is board BETWEEN two openings, and
        # that is the thing a single door cannot have.
        if n > 1 and self.door_pier_m < DOOR_PIER_MIN_M:
            raise ParamError(
                f"{n} '{self.door}' doors on a {run} m elevation leave "
                f"{self.door_pier_m:.2f} m of board between them, under the "
                f"{DOOR_PIER_MIN_M:.2f} m this archetype will build. A pier thinner "
                f"than the jambs that flank it is two door frames touching, not a "
                f"wall with openings in it: record fewer bays or a longer side")
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
        door_bays=int(val("door_bays", 1)),
        door_width_m=(None if val("door_width_m") is None
                      else float(val("door_width_m"))),
        door_height_m=(None if val("door_height_m") is None
                       else float(val("door_height_m"))),
        loft=bool(val("loft", False)),
        chimneys=int(val("chimneys", 0)),
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
        _dw, dh = p.door_size_m
        for u0, u1 in p.door_spans_m:
            out.setdefault(p.door_side, []).append(("door", u0, u1, 0.0, dh))
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
