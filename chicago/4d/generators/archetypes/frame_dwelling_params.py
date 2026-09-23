"""Parameters for the frame_dwelling archetype — pure Python, NO bpy import.

Same split, and for the same reason, as frame_tavern_params and log_dwelling_params:
tools/check.sh imports this module on every commit to prove that every scene-included
record still resolves into buildable parameters, and it has to do that in a bare
Python 3.11 with no Blender in the sandbox.

## What this archetype is for, and how it differs from frame_tavern

A HOUSE, not a public house. `frame_tavern` was written for the Sauganash and carries
its evidence: a two-storey block with a regular five-bay front, a gallery question, and
a bar-room's worth of frontage. Almost nothing a family lived in at Chicago in 1835
looked like that, and until this archetype existed every frame record had to be one of
those or a log cabin — which is why the dataset holds three taverns, three log
buildings, a store and a bridge, and no dwellings at all.

The distinguishing parameters, and where each comes from:

- **`stories` takes 1, 1.5 or 2, and defaults to 1.5.** The story-and-a-half — a full
  storey with chambers in the roof lit from the gable ends over a low knee wall — is
  the characteristic form of these years and the reason `knee_wall_m` exists. The
  dataset's own attestation for the half storey is the Green Tree, where John Gray
  remembered "a small attic window in the gable end, for we used the attic, too"
  (`chicagology_prefire127`), and P. F. W. Peck's store on South Water, whose
  "unfinished loft" Rev. Jeremiah Porter lodged in (`andreas_1884_v1`, scan p. 627).
  Both are the half storey in use; neither is a dormer, and this archetype does not
  build one — see the note on `stories` below.
- **`wall_height_m` is short.** Chicago's one attested ceiling height is the Green
  Tree's seven and a half feet, which the page's own editor calls "rather low for a
  hotel ceiling" (`chicagology_prefire127`). A house was not taller than a hotel, so
  the defaults here are built up from 2.29 m of ceiling plus floor structure rather
  than from a modern storey.
- **`ell` is a plan fact and comes out of the FOOTPRINT**, not out of an invented
  width and depth. `from_phase` reads the wing off an L-shaped footprint polygon and
  refuses a record whose `ell` and whose polygon disagree. The reasoning is the lesson
  docs/ROADMAP.md draws from the North Branch bridge: ask for the kind of number a
  source could contain. No source will ever state a rear wing's width in metres; what
  a source states is exactly what chicagology states about the Western Hotel — "The
  front was about forty feet and the wing sixty feet. It was in an L." That is a
  polygon, and this archetype takes it as one.
- **`porch` is a stoop or a small roofed porch over the door — never the tavern's
  full-front gallery.** A gallery is a public-house feature and `frame_tavern` owns
  it; a record needing one is a tavern record.
- **`plan` and `bays` decide the facade, and they are the point.** See below.

## Balloon framing is a parameter here, not a label

1833-35 Chicago is where balloon framing was invented (St Mary's church, Augustine D.
Taylor, 1833 — `andreas_1884_v1` scan pp. 281, 601), and docs/ROADMAP.md S4 names stud
spacing, sheathing and proportion as the first thing a knowledgeable viewer checks. In
`frame_tavern` and in every structure record so far, `construction` is a value nothing
reads: its own note says the distinction "changes stud rhythm behind the sheathing and
is not visible at this level of detail". Here it moves vertices, three ways:

1. **The module.** `stud_spacing_m` is 16 in for a balloon frame and 24 in for a
   braced one, and every opening's centre lands on a stud-bay centre so its jambs sit
   against studs. The rhythm of the wall is the rhythm of the frame even where the
   studs themselves are behind the sheathing.
2. **The girt.** A braced frame carries a girt at the upper floor and the siding
   shows it; a balloon frame's studs run in one piece from sill to plate and there is
   no line there at all. That is the single most legible exterior difference between
   the two systems, and the generator builds it or omits it accordingly.
3. **The corner.** A braced frame has a heavy corner post to box; a balloon frame has
   a light corner board. The trim width follows the construction.

What is NOT modelled is the studs themselves, because on a finished clapboarded house
they are behind the sheathing and a viewer cannot see them either. The generator does
model the one place the frame reaches the surface: clapboard butt joints fall on stud
lines, staggered course to course, which is what a knowledgeable eye actually reads off
a wall.

## The fenestration problem this archetype exists partly to fix

docs/LIBERTIES.md **L23** records that `fenestration` is stated on all three frame
taverns and read by none of them, so three buildings of different sizes wear one
five-bay front. Its stated resolution is "a bay-count parameter derived from frontage,
and records that state a rhythm rather than a glazing type". That is `bays` and `plan`:

- `bays` is the number of openings across the front, DERIVED from the frontage on a
  period bay module when a record does not state it, and read when it does.
- `plan` names the room arrangement behind the wall, which is what actually decides
  where the door goes. `hall_parlour` — the default, and the commonest vernacular plan
  — puts the door in the middle of the larger room, so the front is asymmetric and the
  openings are unevenly spaced with a wider gap at the partition. `centre_passage` is
  the symmetrical alternative and has to be asked for by name.

The default therefore produces a plainer and less regular front than the taverns', on
purpose. A whole-scene critic reading the existing frame buildings as 1850s Greek
Revival — two-storey clapboard, entablature, corner pilasters, twelve evenly spaced
6-over-6 windows — was reading a real problem: the earliest Greek Revival house in
Chicago is the Clarke House of **1836**, which `data/exclusions.json` already excludes
from this scene by date. A dwelling of 1835 is a year earlier and much plainer than
that, and nothing in this module builds an entablature, a pilaster or a regular front
unless a record asks for one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md. Duplicated from the sibling params modules rather than
# imported so that no params module can break another's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# Gable and shed only. A hip, gambrel or mansard roof on a Chicago house in 1835 would
# be a claim rather than a default, so the archetype refuses it loudly instead of
# quietly substituting a gable — the same rule, for the same reason, as log_dwelling.
ROOF_TYPES = ("gable", "shed")

# Frame only. A log house is a `log_dwelling` and a brick one did not exist here yet:
# the first brick dwelling in Chicago is P. F. W. Peck's of 1837 (andreas_1884_v1;
# data/exclusions.json), two years after this scene.
CONSTRUCTIONS = ("balloon_frame", "braced_frame")

# Room arrangement, which is what decides where the front door is. Not a style.
PLANS = ("single_pen", "hall_parlour", "centre_passage")

# A stoop is a plank landing and two or three steps at the door. A roofed porch is the
# same thing with a small shed roof on two posts, over the door only. Neither is the
# full-width two-tier gallery `frame_tavern` builds, and that distinction is the point:
# the gallery is a public-house feature.
PORCHES = ("stoop", "roofed")

ELL_SIDES = ("west", "east")

# 1, 1.5 or 2, and nothing else. Three storeys is not a dwelling question in 1835
# Chicago: the town's first three-storey building is the Saloon Building of 1836
# (data/exclusions.json), and the only earlier claim is the Tremont House, a hotel
# whose height the sources themselves dispute.
STORIES = (1.0, 1.5, 2.0)

# The eave band each storey count may stand in, in metres. Built up from the one
# attested ceiling in this dataset: the Green Tree's seven and a half feet, 2.29 m,
# which its own source calls low for a hotel. Floor structure and a plate add roughly a
# third of a metre per storey, so a storey is about 2.6 m and the one-storey floor of
# 2.35 m is already under the lowest room anybody in this town wrote down sleeping in —
# and is the shortest wall that can still take the door this archetype hangs in it.
#
# NAMED HERE rather than written inline in `validate()` (T-0142) because the
# reconstruction sampler has to draw an eave this archetype can actually carry, and it
# could not ask. `tools/family_bands.eave_ceiling` reads this table the same way
# `eave_floor` already reads `outbuilding_params.DOOR_SIZE_M` — asking the archetype is
# the rule; retyping its limit into tools/ is the fault `family_bands` exists to end.
WALL_HEIGHT_M = {1.0: (2.35, 3.4), 1.5: (2.9, 4.6), 2.0: (4.0, 6.2)}

# The standing height a half storey needs under its ridge and behind its knee wall, and
# the knee wall a record that says nothing about one gets. Both were written as bare
# numbers inside validate(); they are named because `wall_height_band_m` reads them.
HALF_STOREY_HEADROOM_M = 2.1
KNEE_WALL_DEFAULT_M = 0.95
KNEE_WALL_M = (0.3, 1.8)


def wall_height_band_m(stories: float,
                       knee_wall_m: float = KNEE_WALL_DEFAULT_M) -> tuple[float, float]:
    """The eave band this archetype will actually BUILD at a storey count (T-0142).

    `WALL_HEIGHT_M` is the coarse claim about storey heights; at 1.5 storeys it is not
    the binding one. A half storey is a knee wall on top of a full storey, and
    `validate()` refuses an eave that leaves under 2.1 m below the knee wall — so with
    the default knee wall the real floor is 3.05 m, not 2.9. The two rules live in the
    same validator and disagreed in silence: `tools/measure_family_deal.py` deals D6 at
    the very bottom of its authored 10-12 ft band and the archetype refused three
    houses in four hundred.

    A record that carries its own knee wall gets its own floor; nothing here changes
    what validate() accepts. This is the question a GENERATOR has to ask before it
    samples — which part of a family's authored band this archetype can carry — and it
    is answered here rather than retyped in tools/, for the same reason
    `outbuilding_params.DOOR_SIZE_M` is asked for and not copied.
    """
    lo, hi = WALL_HEIGHT_M[float(stories)]
    if float(stories) == 1.5:
        # Plus one millimetre, which is the resolution every dimension in data/ is
        # authored at. A floor sitting exactly ON the limit does not survive the
        # subtraction validate() makes of it: 3.05 - 0.95 is 2.0999999999999996 in
        # binary and the strict comparison refuses it.
        lo = max(lo, round(knee_wall_m + HALF_STOREY_HEADROOM_M, 3) + 0.001)
    return lo, hi

# The frame module, in metres, by construction. 16 in is balloon framing's spacing;
# 24 in is the wider spacing a braced frame uses between its heavy posts. These are the
# numbers that make `construction` move a vertex rather than sit in the sidecar as an
# unbuilt claim — see the module docstring.
STUD_SPACING_M = {"balloon_frame": 0.4064, "braced_frame": 0.6096}

# Nominal spacing between openings across a front, used only to DERIVE a bay count from
# a frontage when the record does not state one. About nine feet, which is what a
# room-and-a-window costs on a vernacular front of this period.
BAY_MODULE_M = 2.75

# Where the partition between the two rooms of a hall-and-parlour house falls, as a
# fraction of the frontage. The hall is the larger, heated, working room and the
# parlour the smaller; two thirds and one third is the type. This one number is what
# makes the default front asymmetric, so it is stated here rather than buried.
HALL_FRACTION = 0.62

# The form attributes whose VALUE this archetype reads. Membership is earned: an
# attribute is in this set only because `from_phase` below turns it into a parameter
# that the generator then builds something out of. Reading an attribute's CONFIDENCE is
# deliberately NOT membership — `fenestration` tints its geometry with the record's
# confidence while `plan` and `bays` decide the shape, and a tint is not a building.
#
# tools/validate.py holds every attribute outside this set to a `geometry:` declaration
# on the record, so adding a parameter here without adding its name is a gate failure
# rather than a silently unbuilt attribute.
# `finish_key` and `roof_condition` are NOT in this set and must not be, although the
# archetype now reads both (T-0007). This set names FORM attributes — what a phase
# states about the building — and those two live in the record's `reconstruction`
# block, the 665-roof programme's own ledger, one level above the phase. That is why
# no archetype could read them for as long as `from_phase` took only a phase, and it
# is what `docs/RESEARCH/materials.md` §4 finding 4 was pointing at.
CONSUMED = frozenset({
    "stories", "wall_height_m", "knee_wall_m", "roof_type", "roof_pitch_deg",
    "construction", "plan", "bays", "porch", "ell", "ell_wall_height_m",
    "chimneys", "paint", "shutters", "siding_exposure_m",
})
# NOT in the set, and each absence is a decision rather than an oversight:
#   `cladding`      — this archetype always builds clapboard over sheathing, so a
#                     record stating it declares `geometry: simplified`, exactly as
#                     the three frame taverns already do;
#   `fenestration`  — its CONFIDENCE tints the openings, but `plan` and `bays` are
#                     what decide where they go. A glazing type is not a rhythm, which
#                     is the finding docs/LIBERTIES.md L23 records;
#   the ell's arms  — `ell_width_m` and `ell_depth_m` are not form attributes at all
#                     here. They come from the footprint polygon, so there is nothing
#                     for a record to state and nothing to leave unbuilt.

# Where this archetype touches the ground, read by tools/validate.py's ground contact
# check. `perimeter`: the whole footprint outline meets the terrain at local z = 0,
# which is what "y = 0 at the base of the walls" means in docs/GLB-CONTRACT.md.
#
# This archetype can make that claim LITERALLY true of the mesh, which is why the ell
# comes out of the footprint polygon rather than out of two invented dimensions. The
# front range and the wing between them tile the L exactly, so every wall stands on the
# polygon the record attests and every edge of that polygon has a wall on it. The one
# thing that reaches past the polygon is the stoop or porch, which projects from the
# facade and rests on the ground outside it; see docs/LIBERTIES.md when the first
# record with a porch lands.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class FrameDwellingParams:
    """A frame house: one to two storeys, optionally with a rear ell and a porch.

    Dimensions are metres and describe the WHOLE building including the ell, because
    that is what a footprint polygon means. Confidence keys mirror the record's
    attribute confidences and are what the generator paints into _CONFIDENCE.
    """

    # massing. width_m and depth_m are the footprint's bounding box; with an ell the
    # plan is an L inside that box and `main_depth_m` is the front range's own depth.
    width_m: float
    depth_m: float
    # 1.5 is the default because the story-and-a-half is the form of these years, and a
    # default is a claim about the commonest case. A record that knows better says so.
    stories: float = 1.5
    # Eave height: the top of the plate above the base of the walls. For 1.5 storeys
    # this is a full storey PLUS the knee wall, not a full storey plus a whole one.
    wall_height_m: float = 3.6
    # The wall standing above the upper floor before the roof takes over — about three
    # feet. It is what makes a half storey habitable and what a gable-end window sits
    # above; with `stories` 1 or 2 it is unused.
    knee_wall_m: float = KNEE_WALL_DEFAULT_M
    roof_type: str = "gable"
    # Steeper than frame_tavern's 38, because the chambers are in the roof and a
    # shallow pitch puts the ridge too low to stand under. validate() checks the
    # headroom that follows rather than trusting the number.
    roof_pitch_deg: float = 40.0
    construction: str = "balloon_frame"

    # the facade. See the module docstring on L23: `plan` decides where the door is and
    # `bays` how many openings there are; between them they are the archetype's answer
    # to one window arrangement on every frame building.
    plan: str = "hall_parlour"
    # 0 means "derive it from the frontage" — the state a record that says nothing
    # about the elevation leaves this in. from_phase resolves it before construction,
    # so a built parameter object always carries a real count.
    bays: int = 0

    # appearance
    paint: str = "unpainted"
    shutters: str | None = None
    porch: str | None = None

    # The clapboard's exposed face. 0.14 m (~5.5 in) is the archetype's own stock —
    # the one rhythm every frame building wore until T-0049 — and stays the default
    # for a record that carries no value. A record that does carry `siding_exposure_m`
    # is stating which mill stock its walls were hung with; the deal that wrote those
    # values is tools/deal_siding_stock.py and docs/LIBERTIES.md owns the invention.
    siding_exposure_m: float = 0.14

    # How many stacks the house carries. The COUNT is the record's; where they stand is
    # the archetype's — first at one gable, second at the other or on the ell — and
    # docs/LIBERTIES.md L26 owns that arrangement for every archetype here.
    chimneys: int = 1

    # The rear wing. `ell` says whether one is built; its size and side come from the
    # footprint polygon and are filled in by from_phase, or stated directly by a golden
    # case. ell_depth_m is measured from the REAR edge of the footprint forward.
    ell: bool = False
    ell_width_m: float = 0.0
    ell_depth_m: float = 0.0
    ell_side: str = "west"
    # A kitchen wing is lower than the house it serves — that subordination is most of
    # what makes it read as an ell rather than as a second house. None means "derive".
    ell_wall_height_m: float | None = None

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

    # ---------------------------------------------------------------- derived

    @property
    def stud_spacing_m(self) -> float:
        """The frame module. See the module docstring — this is what makes
        `construction` a thing the generator builds rather than a thing the sidecar
        reports."""
        return STUD_SPACING_M.get(self.construction, STUD_SPACING_M["balloon_frame"])

    @property
    def half_story(self) -> bool:
        return abs(self.stories - 1.5) < 1e-9

    @property
    def main_depth_m(self) -> float:
        """Depth of the front range — the whole footprint unless an ell eats into it."""
        return self.depth_m - self.ell_depth_m if self.ell else self.depth_m

    @property
    def ell_height_m(self) -> float:
        """Eave height of the wing. One storey, and lower than the house."""
        if self.ell_wall_height_m is not None:
            return self.ell_wall_height_m
        return min(2.7, max(2.3, self.wall_height_m - 0.9))

    @property
    def ridge_height_m(self) -> float:
        """Top of the main roof above the base of the walls, AT THE WALL PLANE.

        The ridge runs PARALLEL TO THE FACADE — see the generator — so the span that
        sets the rise is the front range's depth, never its frontage. The eave
        overhang the generator adds raises the built ridge a little above this; the
        number here is the one the proportion checks below compare like with like.
        """
        if self.roof_type == "shed":
            return self.wall_height_m + self.main_depth_m * math.tan(
                math.radians(self.roof_pitch_deg))
        return self.wall_height_m + (self.main_depth_m / 2.0) * math.tan(
            math.radians(self.roof_pitch_deg))

    @property
    def ell_ridge_height_m(self) -> float:
        """Top of the wing's roof. 0 when there is no wing.

        The wing's ridge runs BACK from the house, at right angles to the main ridge,
        which is what a rear wing does — a wing whose ridge ran parallel would just be
        a deeper house. So its rise is set by the wing's width.
        """
        if not self.ell:
            return 0.0
        return self.ell_height_m + (self.ell_width_m / 2.0) * math.tan(
            math.radians(self.roof_pitch_deg))

    @property
    def head_room_m(self) -> float:
        """Standing height at the ridge in the half storey, measured from the upper
        floor. The number validate() refuses a building on."""
        if not self.half_story:
            return 0.0
        return self.knee_wall_m + (self.main_depth_m / 2.0) * math.tan(
            math.radians(self.roof_pitch_deg))

    # ---------------------------------------------------------------- confidence

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the contract's rule for geometry driven by several
        attributes. A wall whose height is a guess is a guessed wall, even if we know
        what it was painted."""
        return max((self.conf(a) for a in attrs), default=1.0)

    # ---------------------------------------------------------------- validation

    def validate(self) -> None:
        self._validate_massing()
        self._validate_roof()
        self._validate_facade()
        if self.ell:
            self._validate_ell()
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")

    def _validate_massing(self) -> None:
        # The range is a dwelling's. The largest frame houses attested in this town are
        # about forty feet on the front (the First Presbyterian church is 40 x 25 ft and
        # the Western Hotel 40 ft, both bigger than any house named in the dossiers), and
        # the smallest single pen anyone wintered in is about twelve.
        if not 3.5 <= self.width_m <= 20.0:
            raise ParamError(f"width_m {self.width_m} outside 3.5-20 m for a dwelling; "
                             f"a wider frame building in 1835 Chicago is a hotel, a "
                             f"church or a warehouse, not a house")
        if not 3.0 <= self.depth_m <= 18.0:
            raise ParamError(f"depth_m {self.depth_m} outside 3-18 m for a dwelling")
        if self.stories not in STORIES:
            raise ParamError(
                f"stories {self.stories} not in {STORIES}. A half storey is written 1.5 "
                f"and is a real state, not a rounding; three storeys is not a dwelling "
                f"question in 1835, when the town's first three-storey building (the "
                f"Saloon Building, 1836) had not been begun")
        # The bound is the period stock set: a 4 in exposure is the narrowest siding
        # the deal's sources describe and 6 in the widest. Outside it the value is not
        # a clapboard course at all and the record is wrong, not unusual.
        if not 0.10 <= self.siding_exposure_m <= 0.16:
            raise ParamError(f"siding_exposure_m {self.siding_exposure_m} outside "
                             f"0.10-0.16 m (~4-6.3 in): not a period clapboard exposure")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(
                f"construction '{self.construction}' not in {CONSTRUCTIONS}. A log house "
                f"is a log_dwelling and a brick one did not exist here yet — the first "
                f"brick dwelling in Chicago is 1837 — so this is refused rather than "
                f"quietly built as frame")
        lo, hi = WALL_HEIGHT_M[self.stories]
        if not lo <= self.wall_height_m <= hi:
            raise ParamError(
                f"wall_height_m {self.wall_height_m} outside {lo}-{hi} m for "
                f"{self.stories} storeys. The one attested ceiling height in this "
                f"dataset is the Green Tree's 7 1/2 ft; a house was not built taller "
                f"than the hotel. Set the storey count or the height, not neither")
        if self.half_story:
            if not KNEE_WALL_M[0] <= self.knee_wall_m <= KNEE_WALL_M[1]:
                raise ParamError(f"knee_wall_m {self.knee_wall_m} outside 0.3-1.8 m; "
                                 f"below a foot it is not a knee wall and above six feet "
                                 f"it is a second storey")
            if self.wall_height_m - self.knee_wall_m < HALF_STOREY_HEADROOM_M:
                raise ParamError(
                    f"a {self.knee_wall_m} m knee wall under a {self.wall_height_m} m "
                    f"eave leaves {self.wall_height_m - self.knee_wall_m:.2f} m for the "
                    f"storey below it, which nobody could stand up in")

    def _validate_roof(self) -> None:
        if self.roof_type not in ROOF_TYPES:
            raise ParamError(
                f"roof_type '{self.roof_type}' not in {ROOF_TYPES}. frame_dwelling "
                f"builds gable and shed only; a hip or gambrel roof on a Chicago house "
                f"of 1835 would be an invention, so it is refused rather than "
                f"substituted")
        if not 25.0 <= self.roof_pitch_deg <= 55.0:
            raise ParamError(f"roof_pitch_deg {self.roof_pitch_deg} outside 25-55 deg")
        if self.half_story:
            if self.roof_type != "gable":
                raise ParamError(
                    f"stories 1.5 with a '{self.roof_type}' roof describes nothing: the "
                    f"half storey IS the roof, and its chambers are lit from the gable "
                    f"ends. Either the roof is a gable or the storey count is 1")
            # A half storey nobody can stand up in is an attic, and an attic is not a
            # storey. This is the proportion check the pitch exists to pass, done on the
            # consequence rather than on the number.
            if self.head_room_m < HALF_STOREY_HEADROOM_M:
                raise ParamError(
                    f"a {self.knee_wall_m} m knee wall and a {self.roof_pitch_deg} deg "
                    f"pitch over a {self.main_depth_m:.2f} m range give "
                    f"{self.head_room_m:.2f} m at the ridge — that is a crawl loft, not "
                    f"a half storey. Raise the pitch, raise the knee wall, or record "
                    f"the building as one storey with a loft")
        if self.roof_type == "shed":
            # A shed roof over a deep range piles an implausible amount of roof over a
            # small house: at 40 degrees a 7 m range would carry a 5.9 m rise. Where a
            # shed roof is right at all it is on something small and shallow-pitched —
            # a shanty or a lean-to — so the archetype says so rather than building the
            # cliff a gable's numbers produce when they are handed to a single plane.
            if self.roof_pitch_deg > 30.0:
                raise ParamError(
                    f"a shed roof at {self.roof_pitch_deg} deg is a cliff, not a roof; "
                    f"shed pitches here run to about 30")
            if self.main_depth_m > 6.0:
                raise ParamError(
                    f"a shed roof over a {self.main_depth_m:.2f} m range rises "
                    f"{self.ridge_height_m - self.wall_height_m:.2f} m from eave to "
                    f"head. A building this deep was gabled; record it as one")
        # The eaves-front house is the 1835 form; the gable-front house, turned end-on to
        # the street, is the Greek Revival habit that arrives with the Clarke House in
        # 1836 and dominates the 1840s. The ridge here always runs parallel to the
        # facade, so a range deeper than it is wide would build an implausibly tall roof
        # on an implausibly narrow front rather than the gable-front house someone
        # probably meant.
        if self.main_depth_m > self.width_m * 1.5:
            raise ParamError(
                f"the front range is {self.main_depth_m:.2f} m deep on a "
                f"{self.width_m:.2f} m front. This archetype builds an EAVES-FRONT "
                f"house, ridge parallel to the facade, which is the 1835 form; the "
                f"gable-front house is a Greek Revival habit that arrives here in 1836. "
                f"Rotate the footprint or record the building as something else")

    def _validate_facade(self) -> None:
        if self.plan not in PLANS:
            raise ParamError(f"plan '{self.plan}' not in {PLANS}")
        if self.porch is not None and self.porch not in PORCHES:
            raise ParamError(
                f"porch '{self.porch}' not in {PORCHES}. A full-width two-tier gallery "
                f"is a public-house feature and frame_tavern builds it; a record that "
                f"needs one is a tavern record")
        if self.paint not in ("unpainted", "white", "whitewash", "red"):
            raise ParamError(f"paint '{self.paint}' is not a finish this archetype has "
                             f"a colour for")
        if not isinstance(self.bays, int) or isinstance(self.bays, bool):
            raise ParamError(f"bays {self.bays!r} is not a whole number of openings")
        # 0 is the unresolved state and from_phase never leaves it there; a golden case
        # constructing the dataclass directly may, and gets the same derivation.
        if self.bays and not 2 <= self.bays <= 7:
            raise ParamError(
                f"bays {self.bays} outside 2..7. Below two there is a door and no light; "
                f"above seven the frontage would have to exceed the 20 m this archetype "
                f"accepts at all")
        n = self.bays or self.derived_bays()
        if self.plan == "centre_passage" and n % 2 == 0:
            raise ParamError(
                f"a centre-passage front is an ODD number of bays — a centred door with "
                f"the same number of windows either side — and this record gives {n}. "
                f"Either the count is wrong or the plan is hall_parlour, which is what "
                f"an even front usually means")
        if self.plan == "single_pen":
            if self.width_m > 8.0:
                raise ParamError(
                    f"a single-pen house is ONE ROOM and {self.width_m} m of frontage is "
                    f"two. Record the plan as hall_parlour, or the footprint as smaller")
            if n > 3:
                raise ParamError(f"{n} bays across a single-pen front; one room did not "
                                 f"carry a door and three windows")
        if not isinstance(self.chimneys, int) or isinstance(self.chimneys, bool):
            raise ParamError(f"chimneys {self.chimneys!r} is not a whole number — the "
                             f"record states a count, not whether there was one")
        # The ceiling is the number this archetype can place with an argument behind it:
        # one stack at each gable of the front range, and one on the ell if there is an
        # ell. A fourth would have to stand somewhere invented for no stated reason.
        cap = 3 if self.ell else 2
        if not 0 <= self.chimneys <= cap:
            raise ParamError(
                f"chimneys {self.chimneys} outside 0..{cap} for this house; the "
                f"archetype places one at each gable"
                + (" and one on the ell" if self.ell else "")
                + ", and has nowhere argued to put another")

    def _validate_ell(self) -> None:
        if self.ell_side not in ELL_SIDES:
            raise ParamError(f"ell_side '{self.ell_side}' not in {ELL_SIDES}")
        if self.ell_width_m <= 0 or self.ell_depth_m <= 0:
            raise ParamError("ell is true but the wing has no size — with a record, the "
                             "wing comes from an L-shaped footprint polygon; with a "
                             "golden case, state ell_width_m and ell_depth_m")
        # An ell as wide as the house is not an L, it is a deeper house, and it belongs
        # in the footprint as one. This is the check that keeps `ell` meaning something.
        if self.ell_width_m > self.width_m - 1.2:
            raise ParamError(
                f"an ell {self.ell_width_m} m wide on a {self.width_m} m front leaves "
                f"{self.width_m - self.ell_width_m:.2f} m of open ground beside it, "
                f"which is not an L. A wing the full width of the house is a deeper "
                f"house; record it as one")
        # Shallower than this is not a wing but a porch or a shed, and the archetype
        # has a parameter for the first and no business inventing the second.
        if self.ell_depth_m < 2.0:
            raise ParamError(
                f"an ell {self.ell_depth_m} m deep is a porch or a lean-to, not a "
                f"kitchen wing; record it as a porch or deepen the footprint")
        if self.main_depth_m < 3.5:
            raise ParamError(
                f"an ell {self.ell_depth_m} m deep leaves {self.main_depth_m:.2f} m of "
                f"front range inside a {self.depth_m} m footprint, which is not a room "
                f"deep. Deepen the footprint or shorten the wing")
        if not 2.1 <= self.ell_height_m <= 3.4:
            raise ParamError(f"ell wall height {self.ell_height_m:.2f} m outside "
                             f"2.1-3.4 m; a kitchen wing is a single low storey")
        # Subordination is most of what makes a wing read as a wing.
        if self.ell_ridge_height_m > self.ridge_height_m - 0.3:
            raise ParamError(
                f"the ell's ridge stands at {self.ell_ridge_height_m:.2f} m against the "
                f"house's {self.ridge_height_m:.2f} m — a wing that tall reads as a "
                f"second house, not as a kitchen behind one")

    # ---------------------------------------------------------------- derivation

    def derived_bays(self) -> int:
        """How many openings a front of this width carries when nobody said.

        Frontage over a period bay module, clamped. This is L23's "bay-count parameter
        derived from frontage": the Sauganash's five bays stop being every building's
        five bays, and a small house gets a small front.
        """
        return max(2, min(7, int(round(self.width_m / BAY_MODULE_M))))

    def resolve(self) -> None:
        """Fill in anything left at its derive-me sentinel, then validate."""
        if not self.bays:
            self.bays = self.derived_bays()
        self.validate()


# --------------------------------------------------------------------------
# footprint reading
# --------------------------------------------------------------------------

def _rectilinear(poly: list) -> None:
    """Every edge runs along an axis, or this is not a plan this archetype can read."""
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
            raise ParamError(
                f"footprint edge ({ax}, {ay})-({bx}, {by}) is not axis-aligned. "
                f"frame_dwelling builds a rectangle or a rectilinear L, because those "
                f"are the plans the sources describe; a canted or curved wall is a claim "
                f"this archetype cannot honour and will not approximate")


def read_plan(poly: list) -> dict:
    """Turn a footprint polygon into a plan: bbox, and the wing if there is one.

    Returns `{width_m, depth_m, ell, ell_width_m, ell_depth_m, ell_side}`.

    Two shapes are accepted, and they are the two the evidence produces:

    - **four points, a rectangle** — a single-range house, no wing;
    - **six points, a rectilinear L** — a front range across the whole frontage with a
      wing running back from one end. The notch is at a REAR corner; the wing is what
      is left beside it.

    The wing's arms are therefore read off the record's own footprint rather than
    invented as parameters. It is also what lets GROUND_CONTACT say `perimeter` and
    mean it: the front range and the wing tile the L exactly, so every edge of the
    polygon carries a wall standing on the ground at z = 0.
    """
    if len(poly) not in (4, 6):
        raise ParamError(
            f"footprint has {len(poly)} vertices; frame_dwelling reads a rectangle (4) "
            f"or a rectilinear L (6). A more complicated plan is a real finding and "
            f"deserves its own archetype rather than a bounding box that discards it")
    pts = [(float(p[0]), float(p[1])) for p in poly]
    _rectilinear(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w, d = max(xs) - min(xs), max(ys) - min(ys)

    # The contract pins the mesh origin to polygon coordinate (0, 0). Building from a
    # bounding box SIZE alone silently translates any polygon not anchored there, so the
    # house would stand somewhere its own footprint does not describe. Refuse instead —
    # the same refusal, for the same reason, as frame_tavern_params.from_phase.
    if abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise ParamError(
            f"footprint polygon starts at ({min(xs)}, {min(ys)}), not the origin. "
            f"docs/GLB-CONTRACT.md pins the mesh origin to polygon coordinate (0, 0); "
            f"building from a bounding box would silently move the structure "
            f"{max(abs(min(xs)), abs(min(ys))):.2f} m from where its footprint puts it. "
            f"Re-anchor the polygon at the origin and put the offset in position.")

    if len(pts) == 4:
        return {"width_m": w, "depth_m": d, "ell": False,
                "ell_width_m": 0.0, "ell_depth_m": 0.0, "ell_side": "west"}

    def near(a: float, b: float) -> bool:
        return abs(a - b) < 1e-6

    # The reflex corner is the only vertex strictly inside both bbox spans; the missing
    # bbox corner is the one no vertex sits on. Between them they are the notch.
    reflex = [p for p in pts if 1e-6 < p[0] < w - 1e-6 and 1e-6 < p[1] < d - 1e-6]
    corners = [(0.0, 0.0), (w, 0.0), (w, d), (0.0, d)]
    missing = [c for c in corners
               if not any(near(c[0], p[0]) and near(c[1], p[1]) for p in pts)]
    if len(reflex) != 1 or len(missing) != 1:
        raise ParamError(
            f"a six-point footprint has to be an L — one reflex corner and one corner "
            f"of the bounding box missing — and this one has {len(reflex)} and "
            f"{len(missing)}. A T, a Z or a U is a different building")
    (rx, ry), (mx, my) = reflex[0], missing[0]

    if not near(my, 0.0):
        raise ParamError(
            "the notch in this footprint is at the FACADE end, so the wing would run "
            "forward from the front wall. frame_dwelling builds a rear ell — a kitchen "
            "behind the house — because that is the wing the sources describe. Rotate "
            "the footprint and the position's rotation_deg together, or use another "
            "archetype")

    ell_depth = ry
    if near(mx, w):
        ell_width, side = rx, "west"
    elif near(mx, 0.0):
        ell_width, side = w - rx, "east"
    else:
        raise ParamError(f"the missing bbox corner ({mx}, {my}) is not a corner")
    return {"width_m": w, "depth_m": d, "ell": True,
            "ell_width_m": ell_width, "ell_depth_m": ell_depth, "ell_side": side}


def from_phase(phase: dict, record: dict | None = None) -> FrameDwellingParams:
    """Resolve one structure phase into generator parameters.

    Reads only the attested `value` of each form attribute plus its confidence. The
    footprint polygon is authoritative for the whole plan — the bounding box AND the
    wing — rather than for a width and a depth alone.
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
    plan_from_footprint = read_plan(poly)

    # The record and its own footprint have to agree about the wing. Defaulting `ell`
    # to what the polygon shows means a record that simply draws an L gets one; stating
    # the opposite of the drawing is a contradiction and is raised rather than resolved,
    # because either the polygon or the attribute is wrong and an archetype cannot know
    # which.
    ell = bool(val("ell", plan_from_footprint["ell"]))
    if ell and not plan_from_footprint["ell"]:
        raise ParamError(
            "the record says this house had an ell and its footprint is a plain "
            "rectangle. The wing is a plan fact: draw it in the footprint polygon as an "
            "L and the archetype will read its arms off the drawing, which is the only "
            "place a source's 'a forty foot front and a sixty foot wing, in an L' can "
            "honestly land")
    if plan_from_footprint["ell"] and not ell:
        raise ParamError(
            "the footprint is an L and the record says there was no ell. One of the two "
            "is wrong — an archetype cannot decide which, and building the rectangle "
            "would silently overwrite an attested plan")

    # `reconstruction` is the 665-roof programme's own block: it is present on every
    # anonymous or household roof it dealt and absent from every named building.
    recon = (record or {}).get("reconstruction") or {}
    confidences = {a: conf(a) for a in form}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")

    stories = float(val("stories", 1.5))
    # Storey heights built up from the Green Tree's attested 7 1/2 ft ceiling plus floor
    # structure, with the knee wall added for a story-and-a-half.
    default_wall = {1.0: 2.75, 1.5: 3.6, 2.0: 4.9}.get(stories, 3.6)
    shutters = val("shutters")
    porch = val("porch")

    p = FrameDwellingParams(
        width_m=round(plan_from_footprint["width_m"], 3),
        depth_m=round(plan_from_footprint["depth_m"], 3),
        stories=stories,
        wall_height_m=float(val("wall_height_m", default_wall)),
        knee_wall_m=float(val("knee_wall_m", 0.95)),
        roof_type=str(val("roof_type", "gable")),
        roof_pitch_deg=float(val("roof_pitch_deg", 40.0)),
        construction=str(val("construction", "balloon_frame")),
        plan=str(val("plan", "hall_parlour")),
        bays=int(val("bays", 0)),
        paint=str(val("paint", "unpainted")),
        siding_exposure_m=float(val("siding_exposure_m", 0.14)),
        shutters=(None if shutters in (None, False, "") else str(shutters)),
        porch=(None if porch in (None, False, "") else str(porch)),
        chimneys=int(val("chimneys", 1)),
        ell=ell,
        ell_width_m=round(plan_from_footprint["ell_width_m"], 3),
        ell_depth_m=round(plan_from_footprint["ell_depth_m"], 3),
        ell_side=plan_from_footprint["ell_side"],
        ell_wall_height_m=(None if val("ell_wall_height_m") is None
                           else float(val("ell_wall_height_m"))),
        # The programme's own finish deal, read off the record rather than the
        # phase. `wall_finish` in `common/materials.py` states the order these are
        # applied in and why a stated coating outranks them.
        finish_key=recon.get("finish_key"),
        roof_condition=recon.get("roof_condition"),
        confidence=confidences,
    )
    p.resolve()
    return p
