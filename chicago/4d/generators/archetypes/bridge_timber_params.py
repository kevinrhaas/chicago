"""Parameters for the bridge_timber archetype — pure Python, NO bpy import.

Same split, same reason, as frame_tavern_params: tools/check.sh imports this on every
commit and must not need Blender.

## What is actually documented

Two of the three 1835 crossings were log structures of the same crude specification
(docs/research/03-structures-north.md §5):

- **North Branch bridge**, built winter 1831-32 to replace Clybourn's ferry: log
  construction, **about 10 ft wide, clearing the water by about 6 ft**. A variant
  account credits Samuel Miller in 1832 near the south-east corner of Kinzie and Canal,
  "formed of stringers and only fitted for foot passengers", and says the structure was
  "useless for teams" even in the summer of 1833. But on 18 Aug 1835 the war-dance
  procession — some 800 people — "crossed the North Branch bridge", so by then it was
  more than a footway. A rebuild or widening between 1833 and 1835 is likely and
  **unattested**; the dossier lists it as an open gap.

  **Correction, 2026-08-10, made while writing the first record against this module.**
  Of those two numbers only the WIDTH survives the check. Ten feet is Charles Cleaver's,
  recalled in the *Chicago Tribune* of 29 Oct 1893 — "The abutments were built of heavy
  logs in the shallow water near the banks. These bridges were ten feet wide" — and it
  has a source record now (`chicagology_prefire252`). The six-foot clearance has none:
  the dossier tags it `[DOC]` and nothing reached states it. `DOC_CLEARANCE_M` below
  keeps the figure, because it is plausible and it is the dossier's, but the constant's
  name overstates it and `data/structures/north_branch_bridge.json` records the value as
  `inferred`. Cleaver's sentence also earns the abutments their own `documented` tag,
  which is more than the dossier's summary carried.

  **The correction is itself corrected, later the same day, and the constant's name was
  right after all.** Andreas prints at the foot of pp. 631-632 a statement signed by
  J. D. Caton, John Bates, Charles Cleaver and John Noble, agreed at a meeting of old
  settlers in the fall of 1883 (source `old_settlers_bridges_1883`): the branch bridges
  "were about six feet above the water, so that teams passed under them on the ice
  freely". The clearance is documented, and its reason is better than the number — the
  gap under the deck is the winter road. The dossier's `[DOC]` tag was correct and the
  demotion was the right thing to have done in the meantime. The same paragraph is the
  only description anybody wrote of how these crossings were put together, and three
  more of this module's parameters answer to it; see the next section.

## The middle of a bridge is a count and a form, not a spacing

The same 1883 statement says the bridges were "built on abutments and two 'bents'", that
"the bents were of four heavy logs, resting on the bottom, in deeper water", that
stringers ran "from the abutments to the bents, and between the bents", and that on
those stringers "puncheons or split logs were laid for a floor".

This archetype originally took a `pier_spacing_m` and divided the span by it, which over
the North Branch bridge's 71.83 m put **fifteen** supports in the river against the
letter's **two**. The repair is not a different number in the same parameter — it is a
different parameter. A spacing is a builder's convenience and no source will ever state
one; what a witness remembers is *how many* stood in the water and *what they were*. So
`pier_count` is the input, `PIER_SPACING_FALLBACK_M` is what a bridge whose middle nobody
described falls back to, and `pier_kind` gains `bent` beside `crib` and `pile`.

`deck_kind` exists for the same reason. The floor was the archetype's silently until the
letter named it, and an attribute stated on a record has to be one the generator reads —
otherwise the record owes `docs/LIBERTIES.md` an admission for a feature that is in fact
built (see `tools/validate.py`'s geometry declarations).
- **South Branch raft bridge**, winter 1832-33, between Lake and Randolph: the dossiers
  call it a floating log raft, and **that reading did not survive the source that
  describes how these crossings were built.** The paragraph above is why: the 1883
  old-settlers statement is about BOTH branch bridges — "both bridges were built on
  abutments and two 'bents'", "these bridges were about ten feet wide", "these were
  BOTH wagon bridges, and were about six feet above the water, so that teams passed
  under them on the ice freely" — and a floating raft has no abutments, no bents, no
  six feet of air beneath it and no way for a team to pass under it. So the South
  Branch crossing is this archetype after all, and
  `data/structures/south_branch_raft_bridge.json` records the disagreement instead of
  deleting it: the raft is the word every retelling uses, including the account of the
  crossing in use six weeks after the scene date, and the fixed bridge is what four men
  who drove teams over it set down over their signatures.

  **This section said the opposite until 2026-08-11**, and the superseded text is kept
  because its caution was right and only its conclusion was wrong: "Floating is a
  genuinely different structure, and this archetype does NOT model it — a raft has no
  piers and no clearance in the sense used here. It needs its own archetype, and a
  record that points a floating bridge at this one will get a fixed-pier bridge and a
  false impression of solidity." That danger is real, and it is exactly why the record
  carries the conflict on its face rather than in a footnote. What changed is which
  reading the best evidence supports, not the standard for pointing a structure at an
  archetype. If a source ever puts a floating raft on the South Branch in 1835 against
  the settlers' signatures, the answer is a `raft_timber` archetype, not a parameter
  on this one.

The 1834 Dearborn Street drawbridge is a different animal again — Andreas has it about
three hundred feet long, with a sixty-foot draw hoisted between two "gallows" frames —
and **the moving half of it is out of scope here.** This archetype builds the fixed
timber crossing and nothing else, so a drawbridge record has to declare the draw, its
frames and its overall length as things the mesh does not contain (the `geometry:`
declarations `tools/validate.py` enforces) and owe docs/LIBERTIES.md an entry for each.
That is the honest arrangement available today. Building a hoisted leaf and two frames
whose height, section and mechanism no source gives would bolt four inventions onto the
two dimensions anybody actually recorded — and one of those inventions would be the
silhouette a visitor remembers.

## The dimensional confidences run the other way round from a building

frame_tavern established that massing takes the confidence of the attributes saying
what a building WAS, not of its dimensions, because an unknown size and an unknown form
are different kinds of not-knowing. A bridge inverts the premise. "About ten feet wide,
clearing the water by about six feet, of logs" is the *entire* documented description —
the dimensions ARE the character. So `width_m` and `clearance_m` belong in the set that
drives deck and stringer confidence, while `span_m` (nobody recorded the river's width
at the crossing) does not. The rule is unchanged; what changes is which attributes say
what the thing was — and `deck_kind` joined that set on 2026-08-10, when a source turned
out to state the floor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# `bent` is the settlers' own word for what stood in the deeper water: four heavy
# logs resting on the bottom under a cap. `crib` is a sunk and filled log box and
# `pile` is a driven bent; neither is what the 1883 statement describes.
PIER_KINDS = ("crib", "bent", "pile")

# What the floor was made of. `puncheon` is the 1883 statement's "puncheons or split
# logs"; `plank` is sawn stock, which no source puts on either branch bridge in this
# decade and which a later phase of the same archetype could carry.
DECK_KINDS = ("puncheon", "plank")

# WHAT HOISTED THE DRAW. `None` is the state this archetype built from 2026-08-11 to
# 2026-08-21: gallows frames standing over a closed opening with nothing hung from
# them, because the two TEXTS this project holds (Andreas, and the chicagology page
# that transcribes him) name no tackle at all. `chain_hoist` hangs a chain from each
# frame's head down to the deck, and it is not a re-reading of those texts — they are
# still silent. It is the PLATES: the two engravings recorded in
# `data/sources/assets/owner_brief_2026_08_18/README.md` (images 2 and 3) draw chains
# falling from the frames to the leaves, and a tier-5 pictorial view may drive form as
# `inferred`. A record turning this on owes docs/LIBERTIES.md the arrangement, because
# the plate shows THAT there were chains and not how many, how heavy, or how rigged.
DRAW_GEAR = (None, "chain_hoist")

# The documented specification, in metres, for both log bridges at the forks.
DOC_WIDTH_M = 3.05        # "These bridges were ten feet wide" — Cleaver, documented
DOC_CLEARANCE_M = 1.83    # "about six feet above the water" — old settlers, DOCUMENTED

# What a bridge falls back to when nobody described its middle: the supports are
# spread evenly at this spacing and the count comes out of the span. Not a record's
# attribute, and deliberately not one — see the module docstring. A record resolved
# through this fallback is inventing every support it gets, and owes
# docs/LIBERTIES.md an entry saying so.
PIER_SPACING_FALLBACK_M = 4.5

# Where a structure of this archetype is anchored vertically, read by
# tools/compile_scene.py and written into the sidecar for the renderer.
# docs/GLB-CONTRACT.md pins the rule: a building sits at the base of its walls on the
# terrain, and a structure over water sits on the design water surface, because a
# bridge's one measured dimension is a clearance above the water and its piers run to a
# bed this project does not model. `bridge_timber` is the first archetype to declare it;
# anything that does not declare one is placed against the terrain as before.
VERTICAL_ANCHOR = "water"

# Where this archetype touches the ground, read by tools/validate.py's ground
# contact check. A building meets the terrain all the way round its outline at
# the base of its walls; a crossing does not meet it anywhere in between, and
# where it DOES meet it is the deck, not the base — the piers run down to a bed
# this project does not model. So `ends`: the two end edges of the footprint,
# at `deck_height_m` above the anchor.
#
# Declaring it is what lets the gate ask whether a bridge lands on anything.
# It is a separate question from VERTICAL_ANCHOR, which says where the structure
# is placed; this says where a person could step off it.
GROUND_CONTACT = "ends"


def ground_contact_z(params: "BridgeTimberParams") -> float:
    """Local z at which a bridge could meet the ground: the deck.

    A module-level function rather than a `@property` on the parameter class, and
    the reason is the staleness gate: `generators/mesh_inputs.py` hashes every
    property the class derives, because a derived constant is as load-bearing as
    a field. This one is not — it is read by `tools/validate.py` and by nothing
    that turns parameters into vertices — so making it a property would have
    re-staled the bridge for a number no builder looks at, which is precisely
    the false positive that module was rewritten to end.

    Separate from `deck_height_m` because the two answer different questions and
    only happen to agree today: the deck is where the traffic is, and a bridge
    whose approach ramps were modelled would meet the ground lower down without
    its deck moving at all.
    """
    return float(params.deck_height_m or 0.0)

# The form attributes whose VALUE this archetype reads. See frame_tavern_params
# for the argument. `pier_spacing_m` was here until 2026-08-10 and is gone rather
# than kept as an alias: a record still stating it would now be an attribute the
# generator does not read, which is exactly what the omission gate is for.
CONSUMED = frozenset({
    "width_m", "clearance_m", "pier_count", "pier_kind", "deck_kind",
    "stringer_count", "stringer_d_m", "plank_t_m", "abutments", "construction",
    "railing", "deck_height_m",
    # The draw, added 2026-08-11. All three reach vertices: the opening clears the
    # supports out of itself and stations the frames, the count sets how many frames
    # there are, and the height is the silhouette.
    "draw_span_m", "gallows_frames", "gallows_height_m",
    # The engravings' half, added 2026-08-21 for T-0132. Each reaches vertices: the
    # bracing changes the frame from a bare portal into the plates' A, the gear hangs
    # the chains, and the leaf count divides the closed deck across the opening.
    "gallows_braced", "draw_lifting_gear", "draw_leaves",
})


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class BridgeTimberParams:
    """A fixed log bridge on timber piers.

    **Local origin.** x runs along the span, y across the width, and **z = 0 is the
    design water surface**, not the ground. docs/GLB-CONTRACT.md pins a structure's
    local origin to "y = 0 at the base of the walls", which a bridge does not have —
    and the one dimension the sources actually give is a clearance above the *water*,
    so anchoring anywhere else would mean carrying the documented number as a derived
    one. The sidecar therefore has to place a bridge against the water surface rather
    than the terrain. Flagged in the module docstring of bridge_timber.py too.

    **Bearing.** The long elevation is the facade, so at `rotation_deg` 0 the deck runs
    east-west and the upstream side faces north — the same rule as a building, which is
    what keeps one convention in the renderer instead of two. A bridge over the
    north-flowing north branch is therefore near 0 or 180.
    """

    span_m: float
    width_m: float = DOC_WIDTH_M
    clearance_m: float = DOC_CLEARANCE_M

    # How many intermediate supports stand between the abutments. None means
    # nobody described the middle of this bridge, and the count is derived from
    # PIER_SPACING_FALLBACK_M instead — the archetype's colonnade, which is an
    # invention and owes an entry in docs/LIBERTIES.md.
    pier_count: int | None = None
    pier_kind: str = "crib"
    deck_kind: str = "puncheon"
    stringer_count: int = 4
    stringer_d_m: float = 0.30
    plank_t_m: float = 0.09
    abutments: bool = True
    construction: str = "log"

    # OFF by default and argued in bridge_timber.py's docstring: no source attests a
    # railing on either log bridge, and the one description we have ("formed of
    # stringers", "useless for teams") describes something cruder than a railed
    # structure. Exposed so a record with evidence can turn it on; when it is on, the
    # railing is built at whatever confidence the record gives it and nothing else
    # inherits from it.
    railing: bool = False

    # THE MOVING PART, added 2026-08-11 for the Dearborn Street drawbridge.
    #
    # `draw_span_m` is the clear opening left for craft, centred on the span. None
    # means a fixed bridge, which is what both branch crossings were. What it changes
    # in the mesh is two things and neither of them is a leaf: the intermediate
    # supports are cleared out of the opening — a navigable draw with a pier standing
    # in it is not a draw — and the gallows frames are stationed at its ends.
    #
    # THE DRAW IS BUILT CLOSED, AND THAT IS THE CHOICE THAT AVOIDS AN INVENTION.
    # Andreas gives "gallows pattern", two frames "one at either end", a draw that was
    # "hoisted", and the occasion the frames "held the draw suspended in mid-air". That
    # establishes it lifted rather than swung, and it does NOT say whether the opening
    # was closed by one leaf, by two, or by a section lifted bodily between the frames —
    # all three fit every word of it. A raised leaf would have to pick one; a closed
    # deck under two frames fits all three, so the deck runs continuously across the
    # opening and the record carries the ambiguity instead of the mesh.
    draw_span_m: float | None = None

    # How many gallows frames stand over the draw. Two is the documented arrangement
    # for the Dearborn bridge, one at either end of the opening.
    gallows_frames: int = 0

    # How tall a gallows frame stands above the deck. NO SOURCE GIVES IT, for the one
    # structure in this dataset that had them, and the default below is this module's
    # own. A record must state it `conjectural`, and the geometry it drives is the
    # silhouette of the whole crossing — see bridge_timber._gallows.
    gallows_height_m: float = 6.4

    # THE ENGRAVINGS' HALF, added 2026-08-21. Three parameters off one body of
    # evidence, and it is a different KIND of evidence from everything above:
    # `gallows_frames` and `draw_span_m` come from a text, and these come from two
    # retrospective engravings. See DRAW_GEAR for what that buys and what it does not.
    #
    # `gallows_braced` puts raking timber into the frame — knee braces under the head
    # and a shore down to the bearing line, leaning away from the opening. The plates
    # draw the frames as an A rather than as two bare posts; the members' sections,
    # angles and count are this module's own and are a liberty.
    gallows_braced: bool = False

    # What hoisted the draw. See DRAW_GEAR. `chain_hoist` hangs one chain each side of
    # the deck from each frame's head down to the deck, taut and vertical.
    draw_lifting_gear: str | None = None

    # How many leaves the opening was closed by. ZERO IS NOT "NONE" — it is this
    # archetype's original and still-defensible reading, a deck that runs unbroken
    # across the opening and takes no view. Two divides the closed deck: a bearing
    # timber at each end of the opening and the two leaves' butts meeting at its
    # centre. The deck boards themselves are unchanged and stay walkable; what is
    # added is the timber at the joints, which is what makes a draw legible as a draw
    # while it is down. A record setting this above zero is choosing one of the three
    # readings form.draw_lifting_gear enumerates, and owes docs/LIBERTIES.md the choice.
    draw_leaves: int = 0

    # Derived in __post_init__ from clearance + structure depth unless a record
    # overrides it. Kept derived because clearance is the documented number and deck
    # height is not; storing both as independent inputs would let them disagree.
    deck_height_m: float | None = None

    confidence: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.deck_height_m is None:
            self.deck_height_m = round(
                self.clearance_m + self.stringer_d_m + self.plank_t_m, 4)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def bays(self) -> int:
        """How many spans between supports. At least one — a short bridge is a single
        stringer run from abutment to abutment with no pier in the water at all.

        A stated `pier_count` gives it directly; otherwise the span is divided by the
        fallback spacing, which is a guess dressed as arithmetic and is treated as one.
        """
        if self.pier_count is not None:
            return self.pier_count + 1
        return max(1, round(self.span_m / PIER_SPACING_FALLBACK_M))

    @property
    def pier_x(self) -> list[float]:
        """Centre-lines of the interior supports, evenly spaced along the span.

        EVEN SPACING IS THE ARCHETYPE'S, always. Even where the count is attested it
        is only a count: the 1883 statement puts two bents "in deeper water" between
        log abutments "in the shallow water near the banks" and says nothing about
        where along the span they stood. Thirds are what a builder would do and not
        what anybody recorded, so a record whose count is documented still owes
        docs/LIBERTIES.md an admission for the positions.

        ANYTHING THAT WOULD STAND INSIDE THE DRAW IS DROPPED, and that is not a
        cosmetic filter: a sixty-foot opening for the passage of craft with a pier
        standing in the middle of it is not an opening. The evenly spaced stations are
        computed first and then cleared out of the gap, so the count a record states is
        the count of supports it would have had WITHOUT a draw. A record with a draw
        therefore builds fewer supports than its `pier_count` says, and that is the
        arithmetic being honest rather than the record being wrong: nobody wrote down
        either number, and inventing a redistribution of the survivors would be a third
        guess on top of two.
        """
        n = self.bays
        xs = [self.span_m * i / n for i in range(1, n)]
        if not self.draw_span_m:
            return xs
        lo = self.span_m / 2.0 - self.draw_span_m / 2.0
        hi = self.span_m / 2.0 + self.draw_span_m / 2.0
        return [x for x in xs if not lo < x < hi]

    @property
    def gallows_x(self) -> list[float]:
        """Where the gallows frames stand: at the ends of the draw opening.

        "The frames, one at either end, stood like instruments of death to frighten
        the timid stranger at night" — Andreas. "Either end" is either end of the
        DRAW, not of the bridge: the same paragraph pairs the frames with the draw
        being hoisted and held suspended between them. A single frame, if a record
        ever states one, stands over the middle of the opening.
        """
        if not self.gallows_frames or not self.draw_span_m:
            return []
        mid = self.span_m / 2.0
        if self.gallows_frames == 1:
            return [mid]
        return [mid - self.draw_span_m / 2.0, mid + self.draw_span_m / 2.0]

    def validate(self) -> None:
        if not 3.0 <= self.span_m <= 90.0:
            raise ParamError(f"span_m {self.span_m} outside 3-90 m")
        # Before the width range check, so a transposed footprint gets told what is
        # actually wrong with it rather than "your bridge is 17 metres wide".
        if self.span_m <= self.width_m:
            raise ParamError(
                f"span_m {self.span_m} is not longer than width_m {self.width_m}. "
                f"The footprint polygon's u axis is the SPAN and its v axis is the "
                f"deck width; a polygon the other way round means the record's "
                f"footprint is rotated 90 degrees")
        if not 1.0 <= self.width_m <= 12.0:
            raise ParamError(f"width_m {self.width_m} outside 1-12 m")
        if not 0.3 <= self.clearance_m <= 6.0:
            raise ParamError(f"clearance_m {self.clearance_m} outside 0.3-6 m")
        if self.pier_kind not in PIER_KINDS:
            raise ParamError(f"pier_kind '{self.pier_kind}' not in {PIER_KINDS}")
        if self.deck_kind not in DECK_KINDS:
            raise ParamError(f"deck_kind '{self.deck_kind}' not in {DECK_KINDS}")
        if self.pier_count is not None and not 0 <= self.pier_count <= 24:
            raise ParamError(f"pier_count {self.pier_count} outside 0-24. Zero is a "
                             f"legitimate value — a short crossing lands abutment to "
                             f"abutment with nothing in the water — and anything past "
                             f"a couple of dozen is a spacing being smuggled in as a "
                             f"count")
        if not 2 <= self.stringer_count <= 12:
            raise ParamError(f"stringer_count {self.stringer_count} outside 2-12")
        if not 0.12 <= self.stringer_d_m <= 0.6:
            raise ParamError(f"stringer_d_m {self.stringer_d_m} outside 0.12-0.6 m")
        if not 0.03 <= self.plank_t_m <= 0.30:
            raise ParamError(f"plank_t_m {self.plank_t_m} outside 0.03-0.3 m")
        if self.construction not in ("log", "timber_crib"):
            raise ParamError(
                f"construction '{self.construction}' is not log or timber_crib — a "
                f"framed or iron bridge is not this archetype and not this decade")
        if self.deck_height_m is None or self.deck_height_m <= self.clearance_m:
            raise ParamError("deck_height_m must sit above the clearance line; leave "
                             "it unset and it is derived from clearance + structure")
        if self.draw_span_m is not None:
            if not 3.0 <= self.draw_span_m < self.span_m:
                raise ParamError(
                    f"draw_span_m {self.draw_span_m} must be at least 3 m and shorter "
                    f"than the span it opens ({self.span_m}); a draw as wide as the "
                    f"bridge is not a draw, it is a ferry")
        if self.draw_lifting_gear not in DRAW_GEAR:
            raise ParamError(
                f"draw_lifting_gear '{self.draw_lifting_gear}' is not in {DRAW_GEAR}; "
                f"a mechanism this archetype cannot build is a claim the mesh cannot "
                f"keep")
        if self.draw_lifting_gear and not self.draw_span_m:
            raise ParamError("draw_lifting_gear without draw_span_m: tackle and no "
                             "opening to hoist")
        if self.draw_leaves not in (0, 1, 2):
            raise ParamError(
                f"draw_leaves {self.draw_leaves} outside 0-2. Three leaves is not a "
                f"reading anybody has ever put on this bridge")
        if self.draw_leaves and not self.draw_span_m:
            raise ParamError("draw_leaves without draw_span_m: a leaf is what closes "
                             "an opening, so leaves with no opening is a record that "
                             "lost half its evidence")
        if self.gallows_braced and not self.gallows_frames:
            raise ParamError("gallows_braced without gallows_frames: nothing to brace")
        if not 0 <= self.gallows_frames <= 2:
            raise ParamError(f"gallows_frames {self.gallows_frames} outside 0-2. The "
                             f"one bridge in this dataset that had them had two, one "
                             f"at either end of the draw")
        if self.gallows_frames and not self.draw_span_m:
            raise ParamError("gallows_frames without draw_span_m: a gallows frame is "
                             "the thing that hoists a draw, so a bridge with frames "
                             "and no opening is a record that lost half its evidence")
        if not 2.0 <= self.gallows_height_m <= 14.0:
            raise ParamError(f"gallows_height_m {self.gallows_height_m} outside 2-14 m "
                             f"above the deck")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")


def from_phase(phase: dict, record: dict | None = None) -> BridgeTimberParams:
    """Resolve one structure phase into generator parameters.

    The footprint polygon is the DECK outline: its u extent is the span and its v
    extent is the width. validate() rejects the transposed case rather than guessing,
    because a bridge silently rotated 90 degrees lands in the river beside its
    crossing and looks plausible from every angle except above.
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
    span, width = max(xs) - min(xs), max(ys) - min(ys)

    confidences = {a: conf(a) for a in form}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")
    # The deck's width comes off the polygon, so a record that documents "about ten
    # feet" in prose but leaves the footprint conjectural should say so on the
    # width_m attribute. Where it does not, the footprint's confidence stands in.
    confidences.setdefault("width_m", confidences["footprint"])

    p = BridgeTimberParams(
        span_m=round(span, 3),
        width_m=round(float(val("width_m", width)), 3),
        clearance_m=float(val("clearance_m", DOC_CLEARANCE_M)),
        pier_count=(None if val("pier_count") is None else int(val("pier_count"))),
        pier_kind=str(val("pier_kind", "crib")),
        deck_kind=str(val("deck_kind", "puncheon")),
        stringer_count=int(val("stringer_count", 4)),
        stringer_d_m=float(val("stringer_d_m", 0.30)),
        plank_t_m=float(val("plank_t_m", 0.09)),
        abutments=bool(val("abutments", True)),
        construction=str(val("construction", "log")),
        railing=bool(val("railing", False)),
        deck_height_m=(None if val("deck_height_m") is None
                       else float(val("deck_height_m"))),
        draw_span_m=(None if val("draw_span_m") is None
                     else float(val("draw_span_m"))),
        gallows_frames=int(val("gallows_frames", 0)),
        gallows_height_m=float(val("gallows_height_m", 6.4)),
        # `val` returns the old boolean `false` for a record that predates the gear,
        # and falsy collapses to None — so a record written before 2026-08-21 resolves
        # to exactly the bridge it resolved to then.
        gallows_braced=bool(val("gallows_braced", False)),
        draw_lifting_gear=(str(val("draw_lifting_gear"))
                           if val("draw_lifting_gear") else None),
        draw_leaves=int(val("draw_leaves", 0) or 0),
        confidence=confidences,
    )
    p.validate()
    return p
