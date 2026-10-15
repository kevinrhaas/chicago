"""Parameters for the log_dwelling archetype — pure Python, NO bpy import.

Same split, and for the same reason, as frame_tavern_params: tools/check.sh imports
this module on every commit to prove that every scene-included record still resolves
into buildable parameters, and it has to do that in a bare Python 3.11 with no
Blender in the sandbox.

## What this archetype has to cover

Hewn log was the commonest construction at the forks in 1835, and the three buildings
this archetype was written for differ in exactly the ways the parameters expose:

- **Wolf Point Tavern** — "partly log and partly frame" (chicagology/prefire273,
  describing Wentworth's house), so a log core with a frame extension. It was *low*;
  the retrospective images that show it tall are not evidence. Its one genuinely
  distinctive documented feature is the **painted sign of a wolf hung outside** by
  about 1833, which is what `sign` is for.
- **Samuel Miller's house** — "log cabin with a two-storey frame addition fronting the
  river" (DRLOIH), corroborated by the 1833 view showing "a two-story building and
  adjoining log cabin" on the north bank. So: `frame_addition` on the `front` side,
  two storeys, over a single-storey log core.
- **Rev. Jesse Walker's meeting house** — Wau-Bun: "a small square log building,
  originally designed for a school-house". No additions, no sign, square in plan. The
  plain case, and the one that proves the archetype degrades to nothing-but-a-cabin.

See docs/research/03-structures-north.md §2.1, §2.2 and §3.1 for the evidence and its
disagreements.

## What it deliberately does not cover

The `frame_addition` is a *massing* addition — a clapboarded block sharing the log
core's footprint bbox. It is not a general-purpose second archetype: a building that is
mostly frame with a log wing is a `frame_tavern` (the Sauganash), and one that is
mostly log with a frame piece is a `log_dwelling`. Which side of that line a record
falls on is a research judgement and belongs in the record's `archetype`, not in a
parameter.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md. Duplicated from frame_tavern_params rather than imported
# so that neither params module can break the other's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# Only the two roof forms this archetype actually builds. A log dwelling with a
# gambrel roof in 1835 Chicago would be a claim, not a default, so the archetype
# refuses it loudly rather than quietly substituting a gable.
LOG_ROOF_TYPES = ("gable", "shed")

# The eave band this archetype will actually BUILD at a storey count, in metres.
#
# NAMED HERE rather than left as bare numbers inside `validate()` (T-0274, following
# the shape T-0142 gave `frame_dwelling`) because a reconstruction sampler has to draw
# an eave this archetype can carry, and until now it could not ask: `family_bands`
# read the absence of this table as "no storey-dependent limit", which was true of
# `outbuilding` and false here. The cost was measurable — the inferred-household
# programme pairs H1 with this archetype, H1's authored eave band is 11-13 ft, and a
# uniform draw across it put 227 walls in four hundred above the one-storey limit and
# the build refused every one.
#
# The numbers are exactly the ones `validate()` enforces and are not re-argued here:
# 1.8-7 m overall, and a one-storey record capped at 3.6 m because more than that is
# two storeys' worth of wall. Asking the archetype is the rule; retyping its limit
# into tools/ is the fault `tools/family_bands.py` exists to end.
WALL_HEIGHT_M = {1.0: (1.8, 3.6), 2.0: (1.8, 7.0)}


def wall_height_band_m(stories: float) -> tuple[float, float]:
    """The eave band this archetype will build at a storey count.

    Read by `tools/family_bands.eave_limits`. A storey count this archetype refuses
    outright raises here rather than returning a band, so a caller cannot sample its
    way past `validate()`.
    """
    return WALL_HEIGHT_M[float(stories)]


#: THE FACADE'S OWN NUMBERS. They were the builder's module constants (T-0435) and
#: came here with T-0520, when the builder stopped setting out the facade itself and
#: started reading `core_front_rects`. Both modules read these: the builder still
#: needs `_WIN_AT` and `_DOOR_HALF` to keep a second chimney stack out of the band
#: the facade leaves clear, and two copies of those figures is exactly how the stack
#: and the door drift back into each other. Half-widths in metres; `WIN_AT_FRAC` is
#: the flanking windows' offset as a fraction of the wall's full span.
DOOR_HALF_M = 0.52
WIN_HALF_M = 0.31
WIN_AT_FRAC = 0.28
#: The frame addition's own half-width: a sawn-frame wall takes a larger light than a
#: log one, and the gable end the builder pierces takes the same window as the facade.
ADDITION_WIN_HALF_M = 0.36

# How a signboard is displayed. `bracket` is an arm off the wall; `sapling_pole` is
# a slender trunk set in the ground with a cross-arm at its head, which is what the
# Wolf Point sources describe and what its engraving draws. See `sign_mount`.
SIGN_MOUNTS = ("bracket", "sapling_pole")

# What may be painted on a board. Deliberately an enumeration rather than free text:
# the value drives an outline this module owns, so a record naming a device the
# archetype cannot draw has to be refused rather than silently given a blank board.
SIGN_DEVICES = (None, "wolf")

ADDITION_SIDES = ("front", "end")

# The form attributes whose VALUE this archetype reads. See the same set in
# frame_tavern_params for the argument; the short version is that an attribute
# outside it cannot move a vertex, so the record states something the mesh does
# not contain and `tools/validate.py` makes the record say which.
#
# Note the two spellings this set made visible rather than tolerant. The Wolf
# Point record wrote `frame_extension` and `signage`; the parameters are
# `frame_addition` and `sign`. Neither name is wrong on its own and neither
# resolver ever complained, which is exactly why a documented frame half and a
# documented painted sign went unbuilt without anything saying so. The record was
# renamed to this vocabulary on 2026-08-10 and re-baked in the same slice; the set
# is what found it, and it is what will find the next one.
#
# `chimney` was a third one of those, caught the same way and fixed on 2026-08-10.
# Every record in the dataset states `chimneys`, a COUNT; this module read a
# boolean called `chimney` that no record has ever contained, so `from_phase` took
# its default and every log building got exactly one stack whatever the record
# said. Samuel Miller's house says two. The parameter is now `chimneys` and it is
# the count.
# `finish_key` and `roof_condition` are NOT in this set and must not be, although the
# archetype now reads both (T-0007). This set names FORM attributes — what a phase
# states about the building — and those two live in the record's `reconstruction`
# block, the 665-roof programme's own ledger, one level above the phase. That is why
# no archetype could read them for as long as `from_phase` took only a phase, and it
# is what `docs/RESEARCH/materials.md` §4 finding 4 was pointing at.
CONSUMED = frozenset({
    "stories", "wall_height_m", "roof_type", "roof_pitch_deg", "construction",
    "loft", "chimneys", "sign", "sign_mount", "sign_device", "frame_paint",
    "frame_addition", "frame_addition_side", "frame_addition_width_m",
    "frame_addition_depth_m", "frame_addition_stories", "frame_addition_height_m",
    "piazza", "piazza_depth_m", "piazza_posts", "piazza_rail", "chimney_ridge_at",
    "front_windows_per_side", "window_w_m", "window_h_m", "front_shutters",
    "front_set_out", "door_w_m", "door_h_m", "chimney_end", "chimney_cross_m", "chimney_head_m", "lean_to",
    "lean_to_length_m", "lean_to_width_m", "lean_to_wall_m", "lean_to_pitch_deg", "log_finish",
    "roof_condition",
})

#: The coatings a log wall can be stated to wear (T-2511). Whitewash is the one a
#: picture here has asked for; a record that wants another argues it in here first.
LOG_FINISHES = (None, "whitewash")
CHIMNEY_ENDS = ("min", "max")
#: Half a gable stack's shaft across its gable — the builder's `_STACK_HALF` — so a
#: lean-to can be held clear of the stack it stands beside.
STACK_HALF_M = 0.48

# See frame_tavern_params for the argument. `perimeter`: the footprint outline
# meets the terrain at local z = 0, the base of the walls.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class LogDwellingParams:
    """A hewn-log building, optionally with a frame addition, a loft and a sign.

    Dimensions are metres and describe the WHOLE building including any frame
    addition, because that is what a footprint polygon means. The addition is
    carved out of the footprint bbox, never bolted onto the outside of it — a
    building that overflows its own recorded footprint is a lie the renderer
    cannot detect.
    """

    # massing
    width_m: float
    depth_m: float
    stories: int = 1
    wall_height_m: float = 2.5
    roof_type: str = "gable"
    # 35, not the frame_tavern's 38 and emphatically not the 42 this started at: a
    # cabin is shallow in plan and low in the wall, so a steep pitch puts more roof
    # above the eave than there is wall below it and the building stops reading as
    # low. Wolf Point Tavern is described as low and that has to survive the roof.
    roof_pitch_deg: float = 35.0
    construction: str = "log"

    # a sleeping or storage loft under the roof. From outside this is a gable-end
    # opening and nothing else, which is honest: a loft leaves no other external
    # trace, and inventing a dormer would be adding evidence.
    loft: bool = False

    # How many stacks the building carries. Log dwellings here were heated, so the
    # default is one, and the record supplies the number. Where each one stands is
    # the archetype's: the first goes against the log core's gable end, and a second
    # goes on the frame addition if there is one — which is the reasoning Miller's
    # record gives for counting two, "a stack in each element" — or against the
    # opposite gable if there is not. Nothing about a stack's position, size or
    # material is attested for any of these buildings; docs/LIBERTIES.md owns that.
    chimneys: int = 1

    # the frame addition. `front` puts it against the facade (Miller's house, the
    # two-storey block "fronting the river"); `end` extends the building sideways
    # (Wolf Point Tavern, "partly log and partly frame").
    frame_addition: bool = False
    frame_addition_side: str = "front"
    frame_addition_width_m: float = 6.0
    frame_addition_depth_m: float = 4.0
    frame_addition_stories: int = 2
    frame_addition_height_m: float | None = None
    frame_paint: str = "unpainted"

    # THE PIAZZA (T-2497): a full-front porch on posts under its own shed roof, the
    # word the Kinzie house's one near-contemporary description uses ("a long, low
    # building, with a piazza extending along its front" — Wau-Bun ch. XVII). It
    # stands OUTSIDE the footprint, as frame_dwelling's stoop does, because a piazza
    # is not a room and the polygon is the walls. Off by default, so no other log
    # building gains one; a record that turns it on owes docs/LIBERTIES.md its depth,
    # its posts and its rail, which no source here measures.
    piazza: bool = False
    piazza_depth_m: float = 2.1
    piazza_posts: int = 6
    piazza_rail: bool = False
    # INTERIOR STACKS ON THE RIDGE (T-2497), as fractions of the ridge from the core's
    # -x end, one per chimney. None keeps the archetype's gable-end placement (L26),
    # which is every other record; a record sets it only where a picture puts a stack
    # through the roof rather than against a gable.
    chimney_ridge_at: tuple | None = None
    # THE FRONT'S WINDOWS (T-2497). One small light each side of the door is the log
    # type and stays the default; a long house a picture draws with more and larger
    # sash states how many stand each side of the door and their size.
    front_windows_per_side: int = 1
    window_w_m: float | None = None
    window_h_m: float | None = None
    # None keeps the archetype's rule (shutters on a front 5.2 m or wider); a record
    # whose picture draws the sash bare says False (T-2497).
    front_shutters: bool | None = None
    # THE FRONT'S SET-OUT, STATED (T-2511). None keeps the archetype's rule above —
    # one door at the middle, `front_windows_per_side` windows each side — which is
    # every record but the ones a picture draws otherwise. A record that states it
    # gives every opening on the front in order, each `[kind, at_m]`: "door" or
    # "window", centred `at_m` along the front from the core's -x corner. Doors take
    # `door_w_m` x `door_h_m` (None: the archetype's 1.04 x 1.93 m) and windows
    # `window_w_m` x `window_h_m`, their heads level with the doors' — the line a
    # long front with several doors is drawn on. One storey and no front addition
    # only: a set-out for an upper storey or an addition's facade is not stated here.
    front_set_out: tuple | None = None
    door_w_m: float | None = None
    door_h_m: float | None = None
    # WHICH GABLE THE STACK STANDS AGAINST (T-2511). "min" is the low end of the
    # ridge's axis, where `_chimneys` has always put the first stack (L26); "max" is
    # the other gable, for a record whose picture draws it there. The facade of a
    # gable-fronted cabin is the "max" end, and a stack is refused there.
    chimney_end: str = "min"
    # How far the gable stack slides along its gable from the centre, toward the
    # front (+) or the back (-), in metres (T-2511). 0 keeps it centred, as every
    # stack has stood; the builder never lets it past the wall's corner.
    chimney_cross_m: float = 0.0
    # The gable stack's head over grade, in metres (T-2511). None keeps the
    # archetype's 0.72 m over the ridge; a stack slid toward the eave clears the roof
    # beside it at much less, and a record whose picture draws it lower says so.
    chimney_head_m: float | None = None
    # A LEAN-TO AGAINST THE STACK'S GABLE (T-2511): a low plank shed built onto the
    # gable the stack stands on, tucked in behind the stack, under its own gable roof
    # whose ridge runs across the house's, so its gable faces the street as the
    # Currey plate draws Lee's Place's. `lean_to_length_m` runs out along the ridge's
    # axis and `lean_to_width_m` across it, back from the stack's back face (from the
    # back wall where there is no stack), and it may not pass the back wall;
    # `lean_to_wall_m` is its eave. It stands outside the
    # footprint, as the stack beside it does: the polygon is the log house's walls.
    # Its planks wear `frame_paint`. Off by default.
    lean_to: bool = False
    lean_to_length_m: float = 2.4
    lean_to_width_m: float = 3.0
    lean_to_wall_m: float = 2.0
    # None roofs it at the house's own pitch.
    lean_to_pitch_deg: float | None = None
    # WHAT THE LOGS WEAR (T-2511). None is the town's bare hewn log and chinking;
    # "whitewash" coats both, for a record whose picture draws the walls pale and
    # smooth. A coating is a claim about the building and owes its confidence.
    log_finish: str | None = None

    # A hanging signboard, as a string naming what was painted on it. The value
    # exists so the sidecar can say what the board carried; whether the mesh draws
    # the device is `sign_device`'s question and not this one's.
    sign: str | None = None

    # HOW THE BOARD WAS DISPLAYED, added 2026-08-21 for T-0072. `bracket` is what
    # this archetype built from the start — a board on an arm off the wall beside
    # the door, an arrangement nothing attests and which was chosen because it is
    # what a tavern sign usually is. `sapling_pole` is what the Wolf Point sources
    # actually describe: "the wolf sign was hung on a sapling" (chicagology's Wolf's
    # Point note, chicagology_prefire273), which is a slender trunk set in the ground
    # and not a wall bracket, and which the 2026-08-18 owner brief's engraving of the
    # tavern draws as a mast-tall pole with a cross-arm and the board flying from it.
    # A record has to choose; the default stays `bracket` so no other building moves.
    sign_mount: str = "bracket"

    # WHETHER THE DEVICE IS PAINTED ON THE BOARD, and it is a separate attribute
    # from `sign` for the reason gallows_braced is separate from gallows_frames: the
    # subject is one claim and the drawing is another, and they are evidenced
    # differently. `None` leaves the board blank, which is what every board in this
    # dataset was until T-0072 and what docs/LIBERTIES.md L25 argued for. `wolf`
    # paints a flat canine silhouette, and a record turning it on is claiming only
    # THAT a wolf was painted there — the outline is the archetype's own and owes
    # docs/LIBERTIES.md an entry.
    sign_device: str | None = None

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

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the contract's rule for geometry driven by
        several attributes."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def addition_height_m(self) -> float:
        if self.frame_addition_height_m is not None:
            return self.frame_addition_height_m
        return 2.55 if self.frame_addition_stories == 1 else 4.7

    def validate(self) -> None:
        if not 2.0 <= self.width_m <= 40.0:
            raise ParamError(f"width_m {self.width_m} outside plausible range 2-40 m "
                             f"for a log building")
        if not 2.0 <= self.depth_m <= 40.0:
            raise ParamError(f"depth_m {self.depth_m} outside plausible range 2-40 m "
                             f"for a log building")
        if self.stories not in (1, 2):
            raise ParamError(f"stories {self.stories} not in 1..2 — a log core of "
                             f"three storeys is not a thing at the forks in 1835")
        if not 1.8 <= self.wall_height_m <= 7.0:
            raise ParamError(f"wall_height_m {self.wall_height_m} outside 1.8-7 m")
        if self.stories == 1 and self.wall_height_m > 3.6:
            raise ParamError(f"wall_height_m {self.wall_height_m} is two storeys' worth "
                             f"of wall on a one-storey record; set stories or the height")
        if self.roof_type not in LOG_ROOF_TYPES:
            raise ParamError(
                f"roof_type '{self.roof_type}' not in {LOG_ROOF_TYPES}. log_dwelling "
                f"builds gable and shed only; a hip or gambrel roof on a log building "
                f"here would be an invention, so it is refused rather than substituted")
        if not 15.0 <= self.roof_pitch_deg <= 55.0:
            raise ParamError(f"roof_pitch_deg {self.roof_pitch_deg} outside 15-55 deg")
        if self.construction != "log":
            raise ParamError(
                f"construction '{self.construction}' is not log — a mostly-frame "
                f"building belongs to the frame_tavern archetype, and which side of "
                f"that line a building falls on is a research judgement, not a default")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")
        if self.sign is not None and not str(self.sign).strip():
            raise ParamError("sign is present but empty — omit it or say what it showed")
        if self.sign_mount not in SIGN_MOUNTS:
            raise ParamError(
                f"sign_mount '{self.sign_mount}' not in {SIGN_MOUNTS} — how a board "
                f"was displayed is evidence, so an unknown mounting is refused "
                f"rather than defaulted to the commonest one")
        if self.sign_device not in SIGN_DEVICES:
            raise ParamError(
                f"sign_device '{self.sign_device}' not in {SIGN_DEVICES} — this "
                f"archetype draws only the devices whose outline it owns")
        if self.sign_device is not None and self.sign is None:
            raise ParamError(
                "sign_device is set with no sign — a device is painted ON a board, "
                "so the board has to be stated first")
        if not isinstance(self.chimneys, int) or isinstance(self.chimneys, bool):
            raise ParamError(f"chimneys {self.chimneys!r} is not a whole number — the "
                             f"record states a count, not whether there was one")
        # Two is the ceiling because two is the number this archetype can place with
        # an argument behind it: one on the log core, one on the frame addition. A
        # third stack would have to go somewhere invented for no stated reason, and
        # a log pen at the forks carrying three is a claim a record should make
        # explicitly rather than have an archetype guess at.
        if not 0 <= self.chimneys <= 2:
            raise ParamError(f"chimneys {self.chimneys} outside 0..2 for a log dwelling; "
                             f"this archetype places one at the core's gable and one on "
                             f"the frame addition, and has nowhere argued to put a third")
        if self.chimneys > 1 and not self.frame_addition and self.width_m < 4.0:
            raise ParamError(f"two stacks on a {self.width_m} m log pen with no frame "
                             f"addition would stand within a metre of each other")
        if self.frame_addition:
            self._validate_addition()
        if self.chimney_end not in CHIMNEY_ENDS:
            raise ParamError(f"chimney_end {self.chimney_end!r} not in {CHIMNEY_ENDS}")
        if self.chimney_end == "max":
            cx0, cy0, cx1, cy1 = core_extent(self)
            if self.frame_addition:
                raise ParamError("chimney_end 'max' with a frame addition: the addition "
                                 "already owns the stack at that end")
            if self.roof_type != "shed" and (cx1 - cx0) < (cy1 - cy0):
                raise ParamError("chimney_end 'max' on a gable-fronted cabin is its "
                                 "facade, and a stack is not what that elevation carries")
        if self.chimney_head_m is not None:
            if self.chimney_ridge_at is not None or self.chimneys == 0:
                raise ParamError("chimney_head_m is a gable stack's head; this record has "
                                 "none, or its stacks are on the ridge")
            if not self.wall_height_m + 0.9 <= self.chimney_head_m <= 12.0:
                raise ParamError(f"chimney_head_m {self.chimney_head_m} must clear the "
                                 f"{self.wall_height_m} m eave by 0.9 m")
        if self.log_finish not in LOG_FINISHES:
            raise ParamError(f"log_finish {self.log_finish!r} not in {LOG_FINISHES}")
        if self.front_set_out is not None:
            self._validate_set_out()
        if self.lean_to:
            if self.chimney_ridge_at is not None or self.frame_addition:
                raise ParamError("lean_to stands beyond a gable stack, and this record's "
                                 "stack is on the ridge or its end is an addition")
            if self.roof_type != "gable":
                raise ParamError("lean_to needs a gable roof to stand against a gable")
            if not 0.8 <= self.lean_to_length_m <= 6.0:
                raise ParamError(f"lean_to_length_m {self.lean_to_length_m} outside 0.8..6.0")
            if not 1.0 <= self.lean_to_width_m <= self.depth_m:
                raise ParamError(f"lean_to_width_m {self.lean_to_width_m} outside "
                                 f"1.0..{self.depth_m} (the gable it stands against)")
            if self.lean_to_pitch_deg is not None and not 15 <= self.lean_to_pitch_deg <= 55:
                raise ParamError(f"lean_to_pitch_deg {self.lean_to_pitch_deg} outside 15..55")
            if self.chimneys > 0:
                room = max(self.depth_m / 2.0 - STACK_HALF_M, 0.0)
                cross = max(-room, min(room, self.chimney_cross_m))
                stack_back = self.depth_m / 2.0 + cross - STACK_HALF_M
                if self.lean_to_width_m > stack_back + 1e-6:
                    raise ParamError(f"lean_to_width_m {self.lean_to_width_m} runs past "
                                     f"the back wall from behind the stack, whose back "
                                     f"is {stack_back:.2f} m from it: slide the stack "
                                     f"(chimney_cross_m) or narrow the lean-to")
            if not 1.5 <= self.lean_to_wall_m <= self.wall_height_m:
                raise ParamError(f"lean_to_wall_m {self.lean_to_wall_m} outside "
                                 f"1.5..{self.wall_height_m}: a lean-to is lower than the house")
        if self.chimney_ridge_at is not None:
            if len(self.chimney_ridge_at) != self.chimneys:
                raise ParamError(f"chimney_ridge_at names {len(self.chimney_ridge_at)} stacks "
                                 f"for a record that counts {self.chimneys}")
            if any(not 0.05 <= f <= 0.95 for f in self.chimney_ridge_at):
                raise ParamError(f"chimney_ridge_at {self.chimney_ridge_at}: each stack "
                                 f"stands between 0.05 and 0.95 of the ridge")
            if self.roof_type != "gable":
                raise ParamError("chimney_ridge_at needs a gable roof to have a ridge")
        if not 1 <= self.front_windows_per_side <= 3:
            raise ParamError(f"front_windows_per_side {self.front_windows_per_side} outside 1..3")
        if self.window_w_m is not None and not 0.4 <= self.window_w_m <= 1.2:
            raise ParamError(f"window_w_m {self.window_w_m} outside 0.4-1.2 m")
        if self.window_h_m is not None and not 0.5 <= self.window_h_m <= 1.8:
            raise ParamError(f"window_h_m {self.window_h_m} outside 0.5-1.8 m")
        if self.piazza:
            if self.frame_addition and self.frame_addition_side == "front":
                raise ParamError("a piazza and a front addition both claim the facade")
            if not 1.2 <= self.piazza_depth_m <= 3.5:
                raise ParamError(f"piazza_depth_m {self.piazza_depth_m} outside 1.2-3.5 m: "
                                 f"shallower is a stoop, deeper a room")
            if not 2 <= self.piazza_posts <= 12:
                raise ParamError(f"piazza_posts {self.piazza_posts} outside 2..12")
            if self.wall_height_m < 2.6:
                raise ParamError(f"a piazza roof hung under a {self.wall_height_m} m eave "
                                 f"leaves no headroom at its posts; it needs 2.6 m of wall")

    def _validate_set_out(self) -> None:
        if self.stories != 1 or self.frame_addition:
            raise ParamError("front_set_out states a one-storey log front; this record "
                             "has an upper storey or a frame addition")
        x0, _y0, x1, _y1 = core_extent(self)
        rects = core_front_rects(self)
        if not any(k == "door" for k, *_ in rects):
            raise ParamError("front_set_out has no door, and a cabin has to have one")
        last = x0
        for kind, u0, u1, z0, z1 in rects:
            if kind not in ("door", "window"):
                raise ParamError(f"front_set_out kind {kind!r} is not door or window")
            if u0 < last + 0.15 or u1 > x1 - 0.15:
                raise ParamError(f"front_set_out {kind} at {u0:.2f}..{u1:.2f} m overlaps "
                                 f"its neighbour or the corner: give them in order, apart")
            if z0 < 0.0 or z1 > self.wall_height_m - 0.15:
                raise ParamError(f"front_set_out {kind} head {z1:.2f} m reaches the eave")
            last = u1

    def _validate_addition(self) -> None:
        if self.frame_addition_side not in ADDITION_SIDES:
            raise ParamError(f"frame_addition_side '{self.frame_addition_side}' "
                             f"not in {ADDITION_SIDES}")
        if self.frame_addition_stories not in (1, 2):
            raise ParamError(f"frame_addition_stories {self.frame_addition_stories} "
                             f"not in 1..2")
        if not 1.8 <= self.addition_height_m <= 7.0:
            raise ParamError(f"frame addition height {self.addition_height_m} "
                             f"outside 1.8-7 m")
        if self.frame_addition_width_m > self.width_m:
            raise ParamError("frame addition is wider than the footprint it sits in")
        if self.frame_addition_depth_m > self.depth_m:
            raise ParamError("frame addition is deeper than the footprint it sits in")
        # The addition is carved out of the footprint, so what is left has to still be
        # a building. 2 m is about the smallest single-pen log room anyone lived in.
        if self.frame_addition_side == "end":
            if self.width_m - self.frame_addition_width_m < 2.0:
                raise ParamError(
                    f"an end addition {self.frame_addition_width_m} m wide leaves only "
                    f"{self.width_m - self.frame_addition_width_m:.2f} m of log core "
                    f"inside a {self.width_m} m footprint; widen the footprint or "
                    f"record the building as frame")
        elif self.depth_m - self.frame_addition_depth_m < 2.0:
            raise ParamError(
                f"a front addition {self.frame_addition_depth_m} m deep leaves only "
                f"{self.depth_m - self.frame_addition_depth_m:.2f} m of log core "
                f"inside a {self.depth_m} m footprint; deepen the footprint or "
                f"record the building as frame")


def from_phase(phase: dict, record: dict | None = None) -> LogDwellingParams:
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

    # `dock` is excluded from the sweep because this builder never reads it, the same
    # exclusion `frame_storefront_params` makes and for the same reason: a dock
    # statement selects a deck on the RENDERER's wharf layer
    # (tools/generate_river_wharves.py), not a metre of this mesh, and
    # generators/mesh_inputs.py hashes exactly what the builder can see — "only a
    # value the generator reads counts". Without it, stating the landing at Robert
    # Kinzie's store (T-0107) would have marked that GLB stale on the day the
    # statement was authored, on a runner with no Blender, when not one of its
    # vertices could move. The storefront archetype learned this on the five South
    # Water stores (T-0062); this is the log archetype carrying the same lesson.
    # `reconstruction` is the 665-roof programme's own block: it is present on every
    # anonymous or household roof it dealt and absent from every named building.
    recon = (record or {}).get("reconstruction") or {}
    confidences = {a: conf(a) for a in form if a != "dock"}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")

    stories = int(val("stories", 1))
    sign = val("sign")

    p = LogDwellingParams(
        width_m=round(width, 3),
        depth_m=round(depth, 3),
        stories=stories,
        wall_height_m=float(val("wall_height_m", 2.5 if stories == 1 else 4.6)),
        roof_type=str(val("roof_type", "gable")),
        roof_pitch_deg=float(val("roof_pitch_deg", 35.0)),
        construction=str(val("construction", "log")),
        loft=bool(val("loft", False)),
        chimneys=int(val("chimneys", 1)),
        frame_addition=bool(val("frame_addition", False)),
        frame_addition_side=str(val("frame_addition_side", "front")),
        frame_addition_width_m=float(val("frame_addition_width_m",
                                         round(width * 0.5, 3))),
        frame_addition_depth_m=float(val("frame_addition_depth_m",
                                         round(depth * 0.5, 3))),
        frame_addition_stories=int(val("frame_addition_stories", 2)),
        frame_addition_height_m=(None if val("frame_addition_height_m") is None
                                 else float(val("frame_addition_height_m"))),
        frame_paint=str(val("frame_paint", "unpainted")),
        piazza=bool(val("piazza", False)),
        piazza_depth_m=float(val("piazza_depth_m", 2.1)),
        piazza_posts=int(val("piazza_posts", 6)),
        piazza_rail=bool(val("piazza_rail", False)),
        front_windows_per_side=int(val("front_windows_per_side", 1)),
        window_w_m=(None if val("window_w_m") is None else float(val("window_w_m"))),
        window_h_m=(None if val("window_h_m") is None else float(val("window_h_m"))),
        front_shutters=(None if val("front_shutters") is None else bool(val("front_shutters"))),
        front_set_out=(None if val("front_set_out") is None
                       else tuple((str(k), float(a)) for k, a in val("front_set_out"))),
        door_w_m=(None if val("door_w_m") is None else float(val("door_w_m"))),
        door_h_m=(None if val("door_h_m") is None else float(val("door_h_m"))),
        chimney_end=str(val("chimney_end", "min")),
        chimney_cross_m=float(val("chimney_cross_m", 0.0)),
        chimney_head_m=(None if val("chimney_head_m") is None
                        else float(val("chimney_head_m"))),
        lean_to=bool(val("lean_to", False)),
        lean_to_length_m=float(val("lean_to_length_m", 2.4)),
        lean_to_width_m=float(val("lean_to_width_m", 3.0)),
        lean_to_wall_m=float(val("lean_to_wall_m", 2.0)),
        lean_to_pitch_deg=(None if val("lean_to_pitch_deg") is None
                           else float(val("lean_to_pitch_deg"))),
        log_finish=(None if val("log_finish") is None else str(val("log_finish"))),
        chimney_ridge_at=(None if val("chimney_ridge_at") is None
                          else tuple(float(f) for f in val("chimney_ridge_at"))),
        sign=(None if sign is None else str(sign)),
        sign_mount=str(val("sign_mount", "bracket")),
        sign_device=(None if val("sign_device") is None
                     else str(val("sign_device"))),
        # The programme's own finish deal, read off the record rather than the
        # phase. `wall_finish` in `common/materials.py` states the order these are
        # applied in and why a stated coating outranks them.
        finish_key=recon.get("finish_key"),
        # A record that states its roof's condition (T-2511: a picture draws it dark)
        # outranks the programme's deal, which no named building carries anyway.
        roof_condition=val("roof_condition", recon.get("roof_condition")),
        confidence=confidences,
    )
    p.validate()
    return p


# ---------------------------------------------------------------------------
# THE ELEVATION'S SET-OUT, and the openings that fall out of it (T-0459).
#
# These live here so that something with no Blender can ask WHERE THE OPENINGS
# ARE. The signage layer is the caller that needed it: it hung painted names and
# wall boards at a height chosen for the trade, over whatever happened to be behind
# them.

# THE BUILDER READS THESE (T-0520). It used to compute the same rectangles beside
# them, which made two copies of one set-out and left a written rule — change one,
# change the other — as the only thing holding them together. It does not any more:
# the builder calls these functions, so an opening moved here moves on the mesh a
# visitor sees, and there is nowhere else to move it. What made that a ticket of its
# own is that the asset staleness hash covers each archetype's builder module BYTE
# FOR BYTE, so touching the three builders staled 212 assets and demanded the
# town-wide rebake that landed with the refactor.
# ---------------------------------------------------------------------------

def core_extent(p: "LogDwellingParams") -> tuple[float, float, float, float]:
    """The log core's rectangle inside the footprint bbox.

    The addition is carved OUT of the footprint rather than bolted onto it, so the
    whole building stays inside the polygon the record actually attests. See the
    dataclass docstring above.
    """
    w, d = p.width_m, p.depth_m
    if not p.frame_addition:
        return 0.0, 0.0, w, d
    if p.frame_addition_side == "end":
        return 0.0, 0.0, w - p.frame_addition_width_m, d
    return 0.0, 0.0, w, d - p.frame_addition_depth_m


def addition_extent(p: "LogDwellingParams") -> tuple[float, float, float, float]:
    """The frame addition's rectangle. `front` is centred on the facade; `end` runs
    to the +x edge and aligns its front wall with the core's."""
    w, d = p.width_m, p.depth_m
    fw, fd = p.frame_addition_width_m, p.frame_addition_depth_m
    if p.frame_addition_side == "end":
        return w - fw, max(d - fd, 0.0), w, d
    x0 = (w - fw) / 2.0
    return x0, d - fd, x0 + fw, d


def core_front_rects(p: "LogDwellingParams") -> list[tuple]:
    """The log core's front-wall openings as `(kind, u0, u1, z0, z1)`.

    Openings in a log wall were few and small because every one of them cuts the
    courses and has to be framed — one door and one or two small windows is the type.
    When a front addition exists it takes the front door, so the core gets a window
    where its door would have been.
    """
    x0, _y0, x1, _y1 = core_extent(p)
    if p.front_set_out is not None:
        return _stated_front_rects(p, x0)
    front_taken = p.frame_addition and p.frame_addition_side == "front"
    story_h = p.wall_height_m / max(p.stories, 1)
    xm = (x0 + x1) / 2.0
    span = x1 - x0
    out: list[tuple] = []
    if not front_taken:
        out.append(("door", xm - DOOR_HALF_M, xm + DOOR_HALF_M, 0.02, 1.95))
    whalf = WIN_HALF_M if p.window_w_m is None else p.window_w_m / 2.0
    wh = 0.72 if p.window_h_m is None else p.window_h_m
    n = p.front_windows_per_side
    if n == 1:
        us = (xm - span * WIN_AT_FRAC, xm + span * WIN_AT_FRAC)
    else:
        # T-2497: n sash each side, evenly in the wall between the door and the corner
        step = (span / 2.0 - DOOR_HALF_M) / n
        offs = [DOOR_HALF_M + (k + 0.5) * step for k in range(n)]
        us = tuple(xm - o for o in reversed(offs)) + tuple(xm + o for o in offs)
    for story in range(p.stories):
        z0 = story * story_h + story_h * 0.34
        if p.window_h_m is not None:
            z0 = story * story_h + max(0.6, min(story_h * 0.34, story_h - wh - 0.45))
        for u in us:
            out.append(("window", u - whalf, u + whalf, z0, z0 + wh))
        if front_taken and story == 0:
            out.append(("window", xm - WIN_HALF_M, xm + WIN_HALF_M, z0, z0 + 0.72))
    return out


def _stated_front_rects(p: "LogDwellingParams", x0: float) -> list[tuple]:
    """A front a record sets out opening by opening (T-2511), in its own order.

    The doors stand on the sill the archetype's door does; every window hangs from
    the doors' head, so a long front reads on one line as the picture draws it.
    """
    dhalf = DOOR_HALF_M if p.door_w_m is None else p.door_w_m / 2.0
    head = 1.95 if p.door_h_m is None else 0.02 + p.door_h_m
    whalf = WIN_HALF_M if p.window_w_m is None else p.window_w_m / 2.0
    wh = 0.72 if p.window_h_m is None else p.window_h_m
    out: list[tuple] = []
    for kind, at in p.front_set_out:
        u = x0 + at
        if kind == "door":
            out.append(("door", u - dhalf, u + dhalf, 0.02, head))
        else:
            out.append((kind, u - whalf, u + whalf, head - wh, head))
    return out


def lean_to_extent(p: "LogDwellingParams") -> tuple[float, float, float, float] | None:
    """The lean-to's rectangle (T-2511), against the gable at `chimney_end`, from the
    back wall forward — or None where the record builds none."""
    if not p.lean_to:
        return None
    cx0, cy0, cx1, cy1 = core_extent(p)
    y0, y1 = cy0, cy0 + p.lean_to_width_m
    if p.chimneys > 0:
        room = max((cy1 - cy0) / 2.0 - STACK_HALF_M, 0.0)
        cross = max(-room, min(room, p.chimney_cross_m))
        y1 = (cy0 + cy1) / 2.0 + cross - STACK_HALF_M
        y0 = y1 - p.lean_to_width_m
    if p.chimney_end == "max":
        return cx1, y0, cx1 + p.lean_to_length_m, y1
    return cx0 - p.lean_to_length_m, y0, cx0, y1


def addition_front_rects(p: "LogDwellingParams") -> list[tuple]:
    """The frame addition's front-wall openings as `(kind, u0, u1, z0, z1)`.

    Only the elevation that faces the town: an END addition's front wall is in the
    same plane as the core's and carries this same range of windows.
    """
    if not p.frame_addition:
        return []
    ax0, _ay0, ax1, _ay1 = addition_extent(p)
    az = p.addition_height_m
    xm = (ax0 + ax1) / 2.0
    story_h = az / max(p.frame_addition_stories, 1)
    front = p.frame_addition_side == "front"
    out: list[tuple] = []
    if front:
        out.append(("door", xm - 0.55, xm + 0.55, 0.02, 2.05))
    for story in range(p.frame_addition_stories):
        z0 = story * story_h + story_h * 0.32
        for fx in (0.22, 0.78):
            u = ax0 + (ax1 - ax0) * fx
            if story == 0 and front and abs(u - xm) < 0.9:
                continue
            out.append(("window", u - ADDITION_WIN_HALF_M, u + ADDITION_WIN_HALF_M,
                        z0, z0 + 1.05))
    return out


def front_wall(p: "LogDwellingParams") -> dict:
    """The wall standing on the footprint's max-v edge, and what is on it.

    A FRONT addition is a block set into the middle of that edge, so the wall a
    visitor faces is only as wide as the addition and the log core stands a pace
    behind it. Anything mounted on the front has to know that: `u0`/`u1` are the
    extent of real wall on the plane, not the footprint's own width.
    """
    if p.frame_addition and p.frame_addition_side == "front":
        ax0, _ay0, ax1, _ay1 = addition_extent(p)
        rects = addition_front_rects(p)
        u0, u1, top = ax0, ax1, p.addition_height_m
    else:
        cx0, _cy0, cx1, _cy1 = core_extent(p)
        rects = list(core_front_rects(p))
        u0, u1, top = cx0, cx1, p.wall_height_m
        if p.frame_addition and p.frame_addition_side == "end":
            rects += addition_front_rects(p)
            u1 = p.width_m
    openings = [{"kind": k, "u0": a, "u1": c, "z0": z0, "z1": z1}
                for k, a, c, z0, z1 in rects]
    if p.sign is not None and p.sign_mount == "bracket":
        # The archetype's own hanging board, on its bracket beside the front door.
        # Not an opening, but a name painted across it is as wrong as one painted
        # across the glass, and the caller is entitled to know it is there.
        bx0, bx1 = (u0, u1)
        x = min((bx0 + bx1) / 2.0 + 1.7, bx1 - 0.6)
        z = min(top - 0.30, 2.55)
        openings.append({"kind": "archetype_sign", "u0": x - 0.44, "u1": x + 0.44,
                         "z0": z - 0.70, "z1": z})
    return {"u0": u0, "u1": u1, "wall_height_m": top, "openings": openings}


def front_openings(p: "LogDwellingParams") -> list[dict]:
    """Everything on the front wall a signboard must not be hung over."""
    return front_wall(p)["openings"]
