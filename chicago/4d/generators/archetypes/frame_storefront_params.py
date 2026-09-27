"""Parameters for the frame_storefront archetype — pure Python, NO bpy import.

Same split, and for the same reason, as frame_tavern_params and log_dwelling_params:
tools/check.sh imports this module on every commit to prove that every scene-included
record still resolves into buildable parameters, and it has to do that in a bare
Python 3.11 with no Blender in the sandbox.

## What this archetype has to cover

The 1835 town was a boom town of **stores**, and until this module existed every
mercantile record in the dataset had to be a log cabin, a frame tavern or a bridge.
The buildings it was written for are the ones the dossiers actually describe — see
docs/research/04-structures-south.md §5, §6 and §12, and §2.4 and §3.10 of
docs/research/03-structures-north.md:

- **P. F. W. Peck's store**, SW corner South Water & LaSalle, 1832-33 — "two-story
  frame", with an "unfinished loft" a visiting minister lodged in. Dry goods,
  hardware and groceries, so goods arrived by wagon and left over a counter. This
  is the type specimen: two storeys, a loft, a shopfront and a way in for freight.
- **Philo Carpenter's store**, South Water between LaSalle and Wells, summer 1833 —
  he "erected a small store". His earlier shop was a 16 x 20 ft log building, so
  "small" here means small. The degenerate case: one room, one shop opening, no ell,
  no loading door, and the archetype has to reduce to it without looking unfinished.
- **Thomas Church's store**, Lake Street — "the first store building on Lake Street,
  a two-story frame structure". Corroborates two-storey frame as the type.
- **Brewster, Hogan & Co.'s store** at Franklin & South Water, and the log store at
  Lake & South Water that this project already models as `log_dwelling` — the only
  attested STORE FOOTPRINT in the dataset is that log one, 20 x 45 ft, which is what
  the plan ranges below are shaped against: a long frontage on a shallow plan.
- **Robert A. Kinzie's storehouse** at Wolf Point, "dealing in groceries and Indian
  goods" — construction unattested, and the reason `shopfront` is a parameter that
  can be turned off rather than something the archetype always builds.

South Water lots were **55 ft wide** (Andreas), which is the frontage this archetype
is proportioned for; a store filled its lot side to side and was shallow.

## What is different about a store, and where each difference comes from

1. **A shopfront** — one composed ground-floor opening much wider than a dwelling's
   door: a door plus display/counter windows behind a continuous sill, framed by
   pilaster boards and capped by a fascia. THE COMPOSITION IS THE ARCHETYPE'S. No
   source reached describes a Chicago shop window in 1835. What is attested is the
   trade, the counter and the street frontage; the rest is type, and it is the
   liberty this archetype is most exposed on.
2. **A goods entrance** on a loading side — a store that advertises "dry goods,
   groceries and hardware" and calls itself a forwarding and commission house takes
   freight off a wagon, and not through the shop door. Unattested per building, so
   it defaults to `conjectural` and dithers unless a record says otherwise.
3. **A rear or side ell** — the working half: storeroom, counting room, kitchen.
   Carved OUT of the footprint, never bolted onto the outside of it, so the building
   stays inside the polygon the record attests (log_dwelling's rule, and the better
   one — frame_tavern's log wing projects past its own footprint).
4. **Balloon framing.** See below; it is the reason this archetype exists in the
   form it does rather than being frame_tavern with a wider door.

## Balloon framing is a first-class parameter, not a label

1833-35 Chicago is where balloon framing was invented, and docs/ROADMAP.md S4 names
it as the first thing a knowledgeable viewer checks. St. Mary's church, built at Lake
& State in October 1833 by Augustine D. Taylor, is the early example the dossier
records (docs/research/04-structures-south.md §6).

`construction` therefore **moves geometry here**, which is the difference between
this archetype and its siblings: in `frame_tavern` the same attribute is declared
CONSUMED, resolves into a parameter, and then changes nothing a visitor can see.
What the two systems show on a finished elevation:

| | balloon_frame | braced_frame |
|---|---|---|
| corner | a thin applied BOARD, ~4 in | a 6 in POST standing in the wall |
| 2nd floor | nothing: studs run sill to plate | a girt line — the frame is storeyed |
| module | 2x4 studs at **16 in centres** | posts at ~8 ft, studs between |
| wall | 4 in stud + 1 in sheathing + siding, which is every reveal's depth |

The stud rhythm cannot be seen through finished siding, so it reaches the mesh two
ways. Always: every opening on the elevation is set out on the 16 in module, which is
what "proportions" means in the ROADMAP line and is visible whether or not anyone can
count studs. And, when a record says the building was unfinished, `framing_exposed`
leaves the loading gable open — studs at their true centres over horizontal board
sheathing, which is the one place the rhythm can literally be counted. That state is
attested in kind rather than invented: Andreas has John Calhoun taking a building at
South Water & Clark for the *Chicago Democrat* in November 1833 "which was unfinished
at the time", and Peck's loft was unfinished in 1833 as well.

## What it deliberately does not cover

A store built of logs is a `log_dwelling` — Hogan's store is recorded that way, and
which side of that line a building falls on is a research judgement that belongs in
the record's `archetype`, not in a parameter. Brick is excluded from 1835 by date on
the south side (the first brick house is 1837), so this archetype refuses it rather
than quietly substituting a wall.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute. See
# docs/GLB-CONTRACT.md. Duplicated from the sibling params modules rather than
# imported so that neither can break the other's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# Gable is the type. Shed is allowed for a one-storey shop and refused above that,
# because a two-storey shed-roofed store in 1835 Chicago would be a claim rather
# than a default. Gambrel is not offered at all: no source describes one on a
# Chicago store at this date, and substituting one silently is how an archetype
# invents a building.
#
# HIP IS OFFERED SINCE T-1659, AND ONLY BECAUSE ONE FAMILY'S OWN ROOF LINE ASKS FOR
# IT. `data/reconstruction/1835_family_archetype_crosswalk.json` authors C4 — the
# wide two-storey store or mixed block — with `roof: "side gable or hip, 6:12-9:12"`.
# Until this ticket the archetype refused a hip outright, which did not keep the
# claim out of the scene: it made HALF of C4's authored roof line unbuildable, so the
# family could only ever be dealt the other half and nothing said that the choice had
# been made by an absence rather than by an argument. That is the same fault
# `tools/roof_form.py` was written to end one level up. A hip is therefore buildable
# HERE, and `validate()` refuses it anywhere C4's own entry does not reach: no other
# family's roof line names one, and no family that does is one storey.
ROOF_TYPES = ("gable", "shed", "hip")

# The eave band this archetype will actually BUILD at a storey count, in metres.
#
# NAMED HERE rather than left as bare numbers inside `validate()` for the reason
# T-0142 named `frame_dwelling`'s and T-0274 named `log_dwelling`'s: a reconstruction
# sampler drawing an eave from a family's authored band has to know which part of that
# band this archetype can carry, and `tools/family_bands.eave_limits` can only ask a
# module that publishes the answer. The numbers are exactly the ones `validate()`
# enforces — 2.2-9 m overall, and a one-storey record capped at 4.2 m because more
# than that is two storeys' worth of wall — and are not re-argued here.
# 1.5 IS HERE SINCE T-1659, and its band is frame_dwelling's own (2.9-4.6 m) rather
# than a second opinion about what a half storey is: a store-residence and a
# story-and-a-half cottage are the same carpentry with a shop in the front room, and
# two archetypes disagreeing about the height of a knee wall would be a finding about
# the town that is an artefact of which module built the roof.
WALL_HEIGHT_M = {1.0: (2.2, 4.2), 1.5: (2.9, 4.6), 2.0: (2.2, 9.0)}

# The standing height a half storey needs behind its knee wall, and the knee wall a
# record that says nothing about one gets. Both are frame_dwelling's, for the reason
# above; `KNEE_WALL_DEFAULT_M` is also what makes the ground storey's plate derivable,
# which is what `shopfront_head_z` needs to stop cutting a shop opening through the
# floor of the room over it (the defect T-1659 measured).
HALF_STOREY_HEADROOM_M = 2.1
KNEE_WALL_DEFAULT_M = 0.95
KNEE_WALL_M = (0.3, 1.8)

# The shop opening's own headroom, which is a SECOND floor under the eave and on a
# store-residence the binding one. `shopfront_head_z` drops the head of the opening
# `SHOP_HEAD_BELOW_FLOOR_M` under the floor above it — a shopfront's fascia and the
# joists behind it have to land somewhere — and `_validate_shopfront` refuses a head
# under `SHOP_HEAD_MIN_Z_M`, which is simply a door. Named because
# `wall_height_band_m` has to publish the eave that follows: a sampler drawing the low
# end of C2's authored 11-13 ft band got an eave this archetype then refused, which
# `tools/measure_band_claims.py` measured at 41 of 400 synthetic C2 deals.
SHOP_HEAD_MIN_Z_M = 2.15
SHOP_HEAD_BELOW_FLOOR_M = 0.34
# The other two things the head has to duck under, named for the same reason: the
# frieze board at the eave (with the fascia over the opening below it), and a plausible
# ceiling over a shop counter.
SHOP_HEAD_BELOW_FRIEZE_M = 0.26
SHOP_HEAD_CEILING_Z_M = 3.05

# The storey counts this archetype will build. 1.5 is the C2 store-residence, whose
# crosswalk entry authors `levels: "1.5"` and asks in writing for "a true
# knee-wall/attic-room silhouette". Until T-1659 `from_phase` resolved the record's
# storeys with `int()`, so eight committed records that STATE 1.5 were built as
# one-storey shops — the half storey lost its light, and `shopfront_head_z` put the
# shop opening's head at 3.05 m in buildings whose ground-storey plate is 2.55-2.99 m,
# i.e. the shopfront was cut through the attic floor.
STORIES = (1.0, 1.5, 2.0)


def wall_height_band_m(stories: float,
                       knee_wall_m: float = KNEE_WALL_DEFAULT_M,
                       shopfront: bool = True) -> tuple[float, float]:
    """The eave band this archetype will build at a storey count.

    Read by `tools/family_bands.eave_limits`. A storey count this archetype refuses
    outright raises here rather than returning a band, so a caller cannot sample its
    way past `validate()`.

    At 1.5 storeys the coarse band is not the binding rule — a half storey is a knee
    wall standing on a full one and `validate()` refuses an eave that leaves under
    2.1 m below the knee wall — so the floor is lifted the same way
    `frame_dwelling_params.wall_height_band_m` lifts its own, plus the one millimetre
    that every dimension in data/ is authored at (3.05 - 0.95 is 2.0999999999999996 in
    binary, and a strict comparison refuses a floor sitting exactly on the limit).
    """
    lo, hi = WALL_HEIGHT_M[float(stories)]
    if float(stories) == 1.5:
        lo = max(lo, round(knee_wall_m + HALF_STOREY_HEADROOM_M, 3) + 0.001)
    if shopfront:
        # The ground storey has to carry a shop opening, and a shop opening is taller
        # than a bedroom's headroom. `shopfront` defaults TRUE because the caller that
        # matters — `tools/family_bands.eave_limits`, asked by every anonymous-roof
        # sampler — is dealing store families, and every one of them gets a shopfront.
        # A record that states it had none (Robert Kinzie's Wolf Point "storehouse") is
        # validated against the archetype's flat floor instead, which is why this is a
        # parameter and not another `max` inside the table.
        lo = max(lo, round(_shop_eave_floor_m(float(stories), knee_wall_m), 3) + 0.001)
    return lo, hi


def _shop_eave_floor_m(stories: float, knee_wall_m: float) -> float:
    """The lowest eave that can still carry a shop opening at this storey count.

    Solved from `shopfront_head_z`'s own three terms rather than restated as a number,
    so the band a sampler is handed and the head the mesh is built at cannot disagree.
    Inverting each term for the eave:

      the floor above  ->  plate >= SHOP_HEAD_MIN_Z_M + SHOP_HEAD_BELOW_FLOOR_M, and
                           the plate is the eave at 1 storey, the eave less the knee
                           wall at 1.5, and half the eave at 2
      the frieze       ->  eave  >= SHOP_HEAD_MIN_Z_M + SHOP_HEAD_BELOW_FRIEZE_M
                                    + SHOP_FASCIA_M
      the ceiling      ->  a CEILING on the head and never a floor under the eave

    The third term is why this is a `max` of two and not of three.
    """
    plate = SHOP_HEAD_MIN_Z_M + SHOP_HEAD_BELOW_FLOOR_M
    if stories == 1.5:
        from_plate = knee_wall_m + plate
    elif stories == 1.0:
        from_plate = plate
    else:
        from_plate = plate * 2.0
    from_frieze = SHOP_HEAD_MIN_Z_M + SHOP_HEAD_BELOW_FRIEZE_M + SHOP_FASCIA_M
    return max(from_plate, from_frieze)

# The two framing systems this archetype builds, and the only two that can be
# meant here. `log` and `brick` are refused with an argument in validate().
CONSTRUCTIONS = ("balloon_frame", "braced_frame")

# The exterior skin. Unlike frame_tavern (see docs/LIBERTIES.md L22, where
# `cladding` is recorded on four records and read by none), the VALUE reaches the
# mesh: clapboard is horizontal lap courses, the other two are vertical.
CLADDINGS = ("clapboard", "vertical_board", "board_and_batten")

ELL_SIDES = ("rear", "end")
DOOR_SIDES = ("left", "centre", "right")
GOODS_DOOR_SIDES = ("end", "rear")

# The form attributes whose VALUE this archetype reads — the ones `from_phase`
# below turns into a parameter, and therefore the only ones a vertex position can
# depend on. The argument for the set is written out in frame_tavern_params; the
# short version is that an attribute outside it cannot move a vertex, so the record
# would be stating something the mesh does not contain, and tools/validate.py holds
# every such attribute to a `geometry:` declaration on the record.
#
# Reading an attribute's CONFIDENCE is deliberately not membership. `fenestration`
# tints the upper-storey windows with the record's confidence while their number
# comes from the frontage and their rhythm from the framing module, and a tint is
# not a building. `gallery` is not here at all, and that is a claim rather than an
# oversight: this archetype builds no awning or porch over the walk, so a record
# that states one has to say `geometry: 'absent'` and admit it.
#
# Adding a parameter without adding its name here is a gate failure rather than a
# silently unbuilt attribute — which is the whole point of the set.
# `finish_key` and `roof_condition` are NOT in this set and must not be, although the
# archetype now reads both (T-0007). This set names FORM attributes — what a phase
# states about the building — and those two live in the record's `reconstruction`
# block, the 665-roof programme's own ledger, one level above the phase. That is why
# no archetype could read them for as long as `from_phase` took only a phase, and it
# is what `docs/RESEARCH/materials.md` §4 finding 4 was pointing at.
CONSUMED = frozenset({
    "stories", "wall_height_m", "knee_wall_m", "roof_type", "roof_pitch_deg",
    "gable_front",
    "construction", "cladding", "paint", "siding_exposure_m", "loft", "chimneys",
    "framing_exposed",
    "shopfront", "shopfront_bays", "shopfront_door_side",
    "goods_door", "goods_door_side", "goods_door_bays", "hoist_door",
    "ell", "ell_side", "ell_width_m", "ell_depth_m", "ell_stories", "ell_height_m",
    "sign",
})

# Where this archetype touches the ground, read by tools/validate.py's ground
# contact check. `perimeter`: the whole footprint outline meets the terrain at
# local z = 0, which is what "y = 0 at the base of the walls" means in
# docs/GLB-CONTRACT.md. It is true of the mesh by construction — the main block,
# the ell and the shopfront's stall riser all start at z = 0, nothing is raised on
# piers, and no part of the building leaves the footprint bounding box. Notably
# there is no step, stoop or plank walk in front of the shop door; a store door
# stood above the mud and this archetype does not model that, which is exactly the
# kind of thing GROUND_CONTACT exists to keep honest.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class FrameStorefrontParams:
    """A frame store: a shopfront on the street, a loading side, an optional ell.

    Dimensions are metres and describe the WHOLE building including any ell,
    because that is what a footprint polygon means. Confidence keys mirror the
    record's attribute confidences and are what the generator paints into
    _CONFIDENCE.
    """

    # massing
    width_m: float
    depth_m: float
    # A FLOAT since T-1659, because 1.5 is a storey count this archetype builds and
    # `int()` is not a way of reading one. See STORIES above for what the truncation
    # cost eight committed C2 records.
    stories: float = 2.0
    wall_height_m: float = 5.4
    # The wall standing above the half storey's floor before the roof takes over —
    # what makes an attic room habitable and what its gable window sits above. Unused
    # at 1 or 2 storeys. frame_dwelling's attribute, same name, same default.
    knee_wall_m: float = KNEE_WALL_DEFAULT_M
    roof_type: str = "gable"
    # 33, against frame_tavern's 38 and log_dwelling's 35. A store's frontage is
    # long and its plan shallow — the one attested store footprint in the dataset
    # is 45 ft by 20 ft — so a tavern's pitch over a store's frontage puts more
    # roof above the eave than there is wall below it, and the building stops
    # reading as a shop and starts reading as a barn.
    roof_pitch_deg: float = 33.0
    # False is "eaves to the street", which is the phrase Andreas uses of a frame
    # building on Lake Street and the normal set-out for a store filling its lot
    # frontage. True turns the gable to the street for a narrow, deep lot. This is
    # the kind of thing a source CAN contain, which is why it is a parameter.
    gable_front: bool = False

    # framing and skin
    construction: str = "balloon_frame"
    cladding: str = "clapboard"
    paint: str = "unpainted"
    # The clapboard's exposed face. 0.14 m (~5.5 in) is the archetype's own stock —
    # the one rhythm every frame building wore until T-0049 — and stays the default
    # for a record that carries no value. Only read when `cladding` is clapboard;
    # the deal that writes record values is tools/deal_siding_stock.py and
    # docs/LIBERTIES.md owns the invention.
    siding_exposure_m: float = 0.14

    # The loading gable left open: studs at their true centres over horizontal
    # board sheathing. Only ever reached when a record describes the building as
    # unfinished — see the module docstring for the two period cases that are.
    framing_exposed: bool = False

    # A loft over the shop. From outside this is one opening in a gable and nothing
    # else, exactly as in log_dwelling: a loft leaves no other external trace, and
    # inventing a dormer or a hoist beam would be adding evidence.
    loft: bool = False

    # How many stacks stand on the block. The COUNT comes from the record; where
    # they stand does not. One is the default because a store was one heated room
    # over a counting room, not a tavern with a hearth in every public room.
    chimneys: int = 1

    # ---- the shopfront: the thing that makes this archetype a storefront -------
    # A composed opening — pilaster boards, a continuous counter sill, a door and
    # `shopfront_bays` display windows, a fascia over the whole. Off gives a plain
    # storehouse elevation, which is what Robert Kinzie's Wolf Point "storehouse"
    # would be until something describes its street face.
    shopfront: bool = True
    shopfront_bays: int = 2
    shopfront_door_side: str = "centre"

    # ---- the goods entrance ---------------------------------------------------
    goods_door: bool = True
    goods_door_side: str = "end"

    # HOW MANY cargo openings stand on that side, set out evenly with equal piers
    # between them and at each corner (T-1663). One is a store, which took its
    # freight in at one door because it took it off one wagon. More than one is a
    # WAREHOUSE — a building worked at several points along its loading side — and
    # it is the thing family F3 in the crosswalk asks for in as many words
    # ("multiple cargo doors"), and the thing F2's "upper freight doors" is the
    # plural of: an upper freight door stands over a cargo opening, so two of them
    # means two loading points, not two doors over one.
    #
    # A COUNT FROM THE RECORD, never derived from the wall — outbuilding's rule
    # since T-1662 and the same reason here: an archetype that decides for itself
    # how many doors a building had is deciding how the building was worked, which
    # is a claim about its use and belongs in a record where it can be graded. The
    # validator refuses a count the elevation cannot carry rather than quietly
    # dropping one.
    goods_door_bays: int = 1

    # An UPPER freight door in the loading gable with a hoist beam projecting over it:
    # the way a two-storey store or warehouse got a barrel to its second floor without
    # carrying it up a stair. The crosswalk authors it for C3 ("optional hoist door")
    # and for F2 ("hoist beam; upper freight doors"), and it is OFF by default because
    # those same entries say why it cannot be defaulted on: C3's assumption note reads
    # "Upper lodging and hoist equipment are selectable variants and cannot be inferred
    # from height alone", and F2's reads "Hoist beam presence varies". So a record gets
    # a hoist because something said so, and an anonymous roof dealt from a family band
    # does not get one at all — which is the state every committed record is in today.
    hoist_door: bool = False

    # ---- the ell --------------------------------------------------------------
    ell: bool = False
    ell_side: str = "rear"
    ell_width_m: float = 5.0
    ell_depth_m: float = 4.0
    ell_stories: int = 1
    ell_height_m: float | None = None

    # A signboard, as a string naming what it carried. The geometry is a plain
    # board on the fascia over the shopfront; NO LETTERING AND NO IMAGE is drawn,
    # for the reason docs/LIBERTIES.md L25 gives about the wolf at Wolf Point. No
    # source reached records the wording, the lettering or the device on any
    # Chicago store sign in 1835 — the firm names survive from newspaper
    # advertisements, which are not sign boards — so painting one would be
    # manufacturing the most-photographed piece of evidence in the scene.
    sign: str | None = None

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
        several attributes. A wall whose height is a guess is a guessed wall,
        even if we know what it was clad in."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def loading_side_run_m(self) -> float:
        """How long the wall the freight goes in on actually is, in metres.

        Asked by the set-out below, and therefore by `validate()` — which is why it
        is here and not in the generator. It reads the SAME two extents the drawing
        code reads (`main_extent` for the block, `ell_extent` for the stretch a rear
        ell takes out of the back wall), so the wall the validator measures and the
        wall the frames are drawn on cannot come apart.
        """
        mx0, my0, mx1, my1 = main_extent(self)
        if self.goods_door_side == "rear":
            u0 = ell_extent(self)[2] if (self.ell and self.ell_side == "rear") else mx0
            return mx1 - u0
        return my1 - my0

    @property
    def goods_door_spans_m(self) -> list:
        """`[(u0, u1), ...]` — the clear opening of every cargo doorway on the
        loading side, in that elevation's own coordinate, left to right.

        ONE set-out, asked for by the frames at the ground, by the upper freight
        doors that stand over them, and by the validator that refuses a count the
        wall cannot carry. Before T-1663 the arithmetic lived inside `_goods_door`
        and centred a single door, and the moment there could be more than one the
        doors below and the doors above would have been set out by two different
        sums.

        The rhythm is even and symmetrical — n openings with their jamb stock and
        n + 1 equal piers, one at each corner and one between every pair. This is
        outbuilding's rule since T-1662, adopted here deliberately rather than
        re-argued: a warehouse's loading side is a frame with bays in it, and an
        even set-out is the only one that does not claim a plan no source in this
        project describes.
        """
        n = int(self.goods_door_bays)
        if not self.goods_door or n < 1:
            return []
        u0, u1 = self._loading_side_extent_m
        if n == 1:
            # ONE BAY IS THE OLD CENTRING, WRITTEN THE OLD WAY. The general formula
            # below is the same QUANTITY at n = 1 but not the same double —
            # (run - w - 2j)/2 + j differs from mid - w/2 in the last bit — and the
            # 43 storefronts in this town that carry a single goods door may not
            # move by a rounding for a change about warehouses. outbuilding made
            # exactly this measurement at T-1662 and eleven of its sheds moved.
            um = (u0 + u1) / 2.0
            return [(um - GOODS_DOOR_W_M / 2.0, um + GOODS_DOOR_W_M / 2.0)]
        framed = GOODS_DOOR_W_M + 2 * GOODS_DOOR_JAMB_M
        pier = ((u1 - u0) - n * framed) / (n + 1)
        out = []
        for i in range(n):
            a = u0 + pier * (i + 1) + framed * i + GOODS_DOOR_JAMB_M
            out.append((a, a + GOODS_DOOR_W_M))
        return out

    @property
    def _loading_side_extent_m(self) -> tuple:
        """The loading wall's two ends, in the coordinate the openings are drawn in."""
        mx0, my0, mx1, my1 = main_extent(self)
        if self.goods_door_side == "rear":
            u0 = ell_extent(self)[2] if (self.ell and self.ell_side == "rear") else mx0
            return u0, mx1
        return my0, my1

    @property
    def goods_door_pier_m(self) -> float:
        """The clear board the even set-out leaves at each gap — between two
        openings and at each corner beside the outermost one. With a single doorway
        this is simply the margin either side of a centred door."""
        n = max(1, int(self.goods_door_bays))
        framed = GOODS_DOOR_W_M + 2 * GOODS_DOOR_JAMB_M
        return round((self.loading_side_run_m - n * framed) / (n + 1), 4)

    @property
    def loading_end_is_gable(self) -> bool:
        """Is the side the freight goes in on a GABLE end?

        The hoist beam projects from a gable — a wall crane under an eave is a different
        arrangement and a second invention — so this is the question `hoist_door` turns
        on, and it is asked HERE because `validate()` has to refuse a record the bake
        cannot honour before the bake runs.

        The gable ends stand across the ridge. The ridge runs along x when the record
        does NOT front its gable (`frame_storefront._ridge_along_x`), which puts the
        gables on the x planes — the footprint's two ENDS, where an `end` goods door
        stands. Front the gable instead and the gables move to the y planes, one of
        which is the REAR: so exactly one of the two goods-door sides has a gable over
        it, and which one it is is the record's `gable_front`.
        """
        if self.roof_type != "gable":
            return False
        ridge_along_x = not self.gable_front
        if self.goods_door_side == "rear":
            return not ridge_along_x
        return ridge_along_x

    @property
    def half_story(self) -> bool:
        """A knee wall standing on a full storey, with rooms in the roof."""
        return float(self.stories) == 1.5

    @property
    def full_stories(self) -> int:
        """How many FULL storeys of wall the elevation has to light. A half storey
        has none of its own — its light comes out of the gable, which is
        frame_dwelling's rule and the reason a C2 store-residence reads as one."""
        return int(float(self.stories))

    @property
    def story_height_m(self) -> float:
        """The GROUND storey's plate above the base of the walls.

        Not `wall_height_m / stories`, which is only the same number when the storeys
        are equal. On a story-and-a-half the upper floor lands where the knee wall
        starts, so the ground storey is the eave less the knee wall — and that is the
        height the shopfront's head and a braced frame's girt both have to duck under.
        Dividing by 1.5 instead put the attic floor 0.4-0.5 m too high on every C2
        record and the shop opening's head above it.
        """
        if self.half_story:
            return self.wall_height_m - self.knee_wall_m
        return self.wall_height_m / max(self.full_stories, 1)

    @property
    def front_width_m(self) -> float:
        """The frontage the shopfront actually has to sit in. An END ell takes a
        slice of the footprint's width, and a shopfront checked against the
        footprint rather than against the block it is built on is checked against
        a wall that is not there."""
        if self.ell and self.ell_side == "end":
            return self.width_m - self.ell_width_m
        return self.width_m

    @property
    def shopfront_head_z(self) -> float:
        """Top of the shop opening, under its fascia.

        Derived rather than fixed, and derived HERE rather than in the generator,
        because `validate` has to know whether the opening clears a door before the
        bake does, and two places computing it separately is how a gate and a mesh
        drift apart. It has to duck under three things: the floor above, the frieze
        board at the eave, and a plausible ceiling.
        """
        avail = self.wall_height_m if float(self.stories) == 1.0 else self.story_height_m
        return min(avail - SHOP_HEAD_BELOW_FLOOR_M, SHOP_HEAD_CEILING_Z_M,
                   self.wall_height_m - SHOP_HEAD_BELOW_FRIEZE_M - SHOP_FASCIA_M)

    @property
    def ell_wall_height_m(self) -> float:
        """The ell's plate height. Defaulted from its storey count on the same
        constants log_dwelling uses for a frame addition, so an ell and a frame
        addition of the same storey count stand at the same height."""
        if self.ell_height_m is not None:
            return self.ell_height_m
        return 2.55 if self.ell_stories == 1 else 4.7

    def validate(self) -> None:
        if not 3.0 <= self.width_m <= 40.0:
            raise ParamError(f"width_m {self.width_m} outside plausible range 3-40 m "
                             f"for a store; South Water lots were 55 ft wide and a "
                             f"store filled its frontage, so anything past a couple "
                             f"of lots is a block and not a building")
        if not 3.0 <= self.depth_m <= 30.0:
            raise ParamError(f"depth_m {self.depth_m} outside plausible range 3-30 m")
        if float(self.stories) not in STORIES:
            raise ParamError(
                f"stories {self.stories} not in {STORIES}. Chicago's first three-storey "
                f"structure is the Saloon Building of 1836 and its first brick house "
                f"is 1837 (docs/research/04-structures-south.md §6, §13) — a "
                f"three-storey store on 1835-07-01 is excluded by date, not merely "
                f"unlikely, so it is refused rather than built")
        if not 2.2 <= self.wall_height_m <= 9.0:
            raise ParamError(f"wall_height_m {self.wall_height_m} outside 2.2-9 m")
        if not 0.10 <= self.siding_exposure_m <= 0.16:
            raise ParamError(f"siding_exposure_m {self.siding_exposure_m} outside "
                             f"0.10-0.16 m (~4-6.3 in): not a period clapboard exposure")
        band_lo, band_hi = wall_height_band_m(float(self.stories), self.knee_wall_m,
                                              shopfront=self.shopfront)
        if not band_lo <= self.wall_height_m <= band_hi:
            raise ParamError(
                f"wall_height_m {self.wall_height_m} is outside {band_lo:.3f}-{band_hi} m, "
                f"the eave this archetype builds at {self.stories} storey(s)"
                + (f" behind a {self.knee_wall_m} m knee wall — a half storey with under "
                   f"{HALF_STOREY_HEADROOM_M} m of standing room behind its knee wall is "
                   f"not a storey" if self.half_story else
                   "; set the storeys or set the height"))
        if self.half_story:
            if not KNEE_WALL_M[0] <= self.knee_wall_m <= KNEE_WALL_M[1]:
                raise ParamError(
                    f"knee_wall_m {self.knee_wall_m} outside "
                    f"{KNEE_WALL_M[0]}-{KNEE_WALL_M[1]} m; under a foot is a plate and "
                    f"not a knee wall, and over six is a second storey being called half "
                    f"of one")
        if self.roof_type not in ROOF_TYPES:
            raise ParamError(
                f"roof_type '{self.roof_type}' not in {ROOF_TYPES}. frame_storefront "
                f"builds gable and shed only; a hip or gambrel on a Chicago store at "
                f"this date would be an invention, so it is refused rather than "
                f"substituted")
        if self.roof_type == "shed" and float(self.stories) != 1.0:
            raise ParamError(f"a shed roof over {self.stories} storeys is a claim, not a "
                             f"default — record the roof as gable or the building as "
                             f"one storey")
        if self.roof_type == "hip" and float(self.stories) != 2.0:
            raise ParamError(
                f"a hip roof over {self.stories} storeys is outside every claim this "
                f"archetype has for one. C4 — the wide two-storey store or mixed block — "
                f"is the ONLY family whose crosswalk roof line names a hip, and its own "
                f"`levels` line is 2; a hip on a one-storey shop or a store-residence "
                f"would be this archetype inventing a form nothing asked it for, which "
                f"is exactly what refusing the hip outright used to prevent")
        if not 15.0 <= self.roof_pitch_deg <= 55.0:
            raise ParamError(f"roof_pitch_deg {self.roof_pitch_deg} outside 15-55 deg")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(
                f"construction '{self.construction}' not in {CONSTRUCTIONS}. A store "
                f"built of logs is a log_dwelling — Hogan's store is recorded that way "
                f"— and brick is excluded from the 1835 south side by date. Which "
                f"system a building was framed in is a research judgement, not a "
                f"default this archetype may pick")
        if self.cladding not in CLADDINGS:
            raise ParamError(f"cladding '{self.cladding}' not in {CLADDINGS}")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")

        # 0 is allowed and is a claim, not an absence: a record saying a store had
        # no stack gets a store with no stack. The ceiling is what the frontage can
        # space without the stacks touching.
        if not isinstance(self.chimneys, int) or isinstance(self.chimneys, bool):
            raise ParamError(f"chimneys {self.chimneys!r} is not a whole number — the "
                             f"record states a count, not whether there was one")
        if not 0 <= self.chimneys <= 3:
            raise ParamError(f"chimneys {self.chimneys} outside 0..3; a store of these "
                             f"proportions cannot carry more, and a record that means "
                             f"it should say where they stood")

        if self.sign is not None and not str(self.sign).strip():
            raise ParamError("sign is present but empty — omit it, or say what it "
                             "carried")
        if self.sign and not self.shopfront:
            raise ParamError("a sign board is carried on the shopfront fascia, and this "
                             "record has no shopfront — either the store had a street "
                             "face or the board hung somewhere this archetype does not "
                             "model")

        if self.shopfront:
            self._validate_shopfront()
        if self.goods_door and self.goods_door_side not in GOODS_DOOR_SIDES:
            raise ParamError(f"goods_door_side '{self.goods_door_side}' not in "
                             f"{GOODS_DOOR_SIDES}")
        self._validate_goods_door_bays()
        if self.hoist_door:
            if float(self.stories) < 2.0:
                raise ParamError(
                    f"a hoist door lifts to an upper FLOOR and this record has "
                    f"{self.stories} storey(s) — a hoist over a one-storey shop or into "
                    f"an attic is not the C3/F2 arrangement, and a beam projecting off a "
                    f"gable with nothing behind it is a prop")
            if not self.goods_door:
                raise ParamError(
                    "a hoist door is the upper half of a LOADING side and this record "
                    "has no goods door — a store that takes no freight at the ground "
                    "does not hoist it to the second floor")
            if self.roof_type != "gable":
                raise ParamError(
                    f"the hoist door hangs in the loading GABLE and this record's roof "
                    f"is '{self.roof_type}', which has none there — record the roof as "
                    f"gable or drop the hoist")
            if not self.loading_end_is_gable:
                raise ParamError(
                    f"the freight goes in on this record's "
                    f"'{self.goods_door_side}' side and, with gable_front "
                    f"{self.gable_front}, that side is an EAVES wall — the beam would "
                    f"have no gable to project from. A crane hung under an eave is a "
                    f"different arrangement and this archetype does not model it; turn "
                    f"the ridge, move the goods door, or drop the hoist")
        if self.ell:
            self._validate_ell()

    def _validate_goods_door_bays(self) -> None:
        """Refuse a cargo-door rhythm the loading side cannot carry (T-1663).

        Refusing is the point. An archetype that thins the piers, drops a bay or
        shrinks the door to make a count fit is deciding how the building was
        worked and then not saying so — the same argument outbuilding's own door
        check makes, and the reason this is a gate and not a clamp.
        """
        bays = self.goods_door_bays
        if isinstance(bays, bool) or int(bays) != bays or bays < 1:
            raise ParamError(
                f"goods_door_bays is {bays!r} and a cargo opening is a whole "
                f"opening. A building that takes no freight says goods_door false; "
                f"one with a single door says 1")
        n = int(bays)
        if n > 1 and not self.goods_door:
            raise ParamError(
                f"goods_door_bays is {n} and this record has no goods door — a "
                f"rhythm of nothing is not a rhythm. Record the door, or record "
                f"one bay")
        if not self.goods_door or n == 1:
            return
        framed = GOODS_DOOR_W_M + 2 * GOODS_DOOR_JAMB_M
        run = self.loading_side_run_m
        need = n * framed
        if need > run:
            raise ParamError(
                f"{n} cargo doors are {GOODS_DOOR_W_M} m clear each and need "
                f"{need:.2f} m of wall with their jambs, but this record's "
                f"'{self.goods_door_side}' elevation is only {run:.2f} m long. "
                f"Widen the footprint, move the freight to the long side, or "
                f"record fewer bays — an archetype that shrinks the door to fit is "
                f"deciding what the building was for")
        # ONLY ASKED OF A RHYTHM. With one doorway the set-out centres it and the
        # wall either side is whatever the elevation has left, which is what every
        # storefront in this town has always had; imposing a corner margin on those
        # would refuse 43 records that were never in question. What is new here is
        # board BETWEEN two openings, and that is the thing a single door cannot
        # have.
        if self.goods_door_pier_m < GOODS_DOOR_PIER_MIN_M:
            raise ParamError(
                f"{n} cargo doors on a {run:.2f} m elevation leave "
                f"{self.goods_door_pier_m:.2f} m of board between them, under the "
                f"{GOODS_DOOR_PIER_MIN_M:.2f} m this archetype will build. A pier "
                f"thinner than the jambs that flank it is two door frames touching, "
                f"not a wall with openings in it: record fewer bays or a longer "
                f"loading side")

    def _validate_shopfront(self) -> None:
        bays = self.shopfront_bays
        if not isinstance(bays, int) or isinstance(bays, bool):
            raise ParamError(f"shopfront_bays {bays!r} is not a whole number")
        if not 1 <= self.shopfront_bays <= 4:
            raise ParamError(f"shopfront_bays {self.shopfront_bays} outside 1..4 — one "
                             f"door and four show windows is already a frontage no "
                             f"store in this town had")
        if self.shopfront_door_side not in DOOR_SIDES:
            raise ParamError(f"shopfront_door_side '{self.shopfront_door_side}' not in "
                             f"{DOOR_SIDES}")
        # The shopfront is sized by its parts and then has to fit inside the
        # frontage with wall left either side. Checked here rather than in the
        # generator so a record that cannot be built says so in the commit gate,
        # seconds after it is written, instead of minutes into a bake.
        if shopfront_width_m(self.shopfront_bays) > self.front_width_m - 2 * PIER_MIN_M:
            raise ParamError(
                f"a {self.shopfront_bays}-bay shopfront needs "
                f"{shopfront_width_m(self.shopfront_bays):.2f} m and the block it sits "
                f"on has {self.front_width_m:.2f} m of frontage, which leaves less than "
                f"{PIER_MIN_M} m of wall at each end — reduce the bays, widen the "
                f"footprint, or make the ell a rear ell")
        if self.shopfront_head_z < SHOP_HEAD_MIN_Z_M:
            raise ParamError(
                f"a {self.wall_height_m} m wall over {self.stories} storey(s) leaves the "
                f"shop opening a head height of {self.shopfront_head_z:.2f} m, which is "
                f"under a door — raise the wall, drop a storey, or record the building "
                f"as having no shopfront")

    def _validate_ell(self) -> None:
        if self.ell_side not in ELL_SIDES:
            raise ParamError(f"ell_side '{self.ell_side}' not in {ELL_SIDES}")
        if self.ell_stories not in (1, 2):
            raise ParamError(f"ell_stories {self.ell_stories} not in 1..2")
        if not 1.8 <= self.ell_wall_height_m <= 7.0:
            raise ParamError(f"ell height {self.ell_wall_height_m} outside 1.8-7 m")
        if self.ell_wall_height_m > self.wall_height_m:
            raise ParamError(f"the ell stands {self.ell_wall_height_m} m against a "
                             f"{self.wall_height_m} m block — an ell is subordinate to "
                             f"the store it hangs off, and one that overtops it is a "
                             f"second building")
        if self.ell_width_m > self.width_m:
            raise ParamError("ell is wider than the footprint it sits in")
        if self.ell_depth_m > self.depth_m:
            raise ParamError("ell is deeper than the footprint it sits in")
        # The ell is carved out of the footprint, so what is left has to still be a
        # store: a shop needs enough depth for a counter and a customer, and enough
        # frontage to put a shopfront on.
        if self.ell_side == "rear":
            if self.depth_m - self.ell_depth_m < 3.0:
                raise ParamError(
                    f"a rear ell {self.ell_depth_m} m deep leaves only "
                    f"{self.depth_m - self.ell_depth_m:.2f} m of shop inside a "
                    f"{self.depth_m} m footprint; deepen the footprint or make the "
                    f"ell an end ell")
            # A lean-to has to get under the main eave, or it is a second roof
            # crashing into the first.
            if self.ell_wall_height_m + _lean_to_rise(self.ell_depth_m) \
                    > self.wall_height_m - 0.30:
                raise ParamError(
                    f"a {self.ell_wall_height_m} m rear ell {self.ell_depth_m} m deep "
                    f"carries its lean-to up to "
                    f"{self.ell_wall_height_m + _lean_to_rise(self.ell_depth_m):.2f} m, "
                    f"which does not tuck under a {self.wall_height_m} m eave. Lower "
                    f"the ell, shorten it, or record it as an end ell with a roof of "
                    f"its own")
        elif self.width_m - self.ell_width_m < 4.0:
            raise ParamError(
                f"an end ell {self.ell_width_m} m wide leaves only "
                f"{self.width_m - self.ell_width_m:.2f} m of frontage inside a "
                f"{self.width_m} m footprint, which is not a store front; widen the "
                f"footprint or record the building as a dwelling")


# ---------------------------------------------------------------------------
# The shopfront's set-out, and the framing module it is set out on.
#
# These live here rather than in the generator because they are what `validate`
# has to know to refuse a shopfront that cannot fit, and the commit gate has no
# Blender. The generator imports them so the two cannot drift.
# ---------------------------------------------------------------------------

# Balloon framing, in the dimensions the system is actually described in. A 2x4
# stud at 16 in on centre, 1 in board sheathing, a clapboard over it: the wall is
# about 5 1/2 inches thick, which is why a balloon-framed store looks thin at every
# opening and a braced-framed one does not.
STUD_SPACING_M = 0.4064          # 16 in on centre
STUD_FACE_M = 0.051              # 2 in of face
STUD_DEPTH_M = 0.102             # 4 in of depth
SHEATHING_M = 0.019              # nominal 1 in board sheathing, dressed
SIDING_M = 0.014                 # the clapboard butt

# A braced frame is a storeyed frame of heavy posts, so its module is the bay and
# not the stud, and it shows a corner post and a girt where a balloon frame shows
# neither.
POST_SPACING_M = 2.44            # 8 ft between principal posts
POST_FACE_M = 0.152              # 6 in of corner post standing in the wall
CORNER_BOARD_M = 0.102           # a 1 x 4 corner board over the siding

# The shopfront's parts, in inches translated once. A 40 in door, 5 ft show
# windows, a counter sill at 29 in, pilaster boards at the ends and mullions
# between: the set-out of a plain country store front, and every one of these
# numbers is the archetype's rather than any record's.
SHOP_DOOR_W_M = 1.016
SHOP_BAY_W_M = 1.524
SHOP_MULLION_M = 0.102
SHOP_PILASTER_M = 0.140
SHOP_SILL_Z_M = 0.737
SHOP_FASCIA_M = 0.280
# How much plain wall has to be left at each end of the frontage. Less than this
# and the shopfront is not a shopfront in a wall, it is a wall around a shopfront.
PIER_MIN_M = 0.60

# The goods opening, and the board around it. These two numbers were written into
# `frame_storefront._goods_door`'s body until T-1663 and are lifted here for the
# reason the block above gives: `validate()` has to know them to refuse a rhythm
# the wall cannot carry, and the commit gate has no Blender. Neither number moved.
GOODS_DOOR_W_M = 1.85            # clear, a double leaf a barrel goes through
GOODS_DOOR_H_M = 2.30            # clear head
GOODS_DOOR_JAMB_M = 0.16         # jamb stock either side, as outbuilding's
# The narrowest CLEAR board this archetype will leave between two goods openings
# on one elevation — outbuilding's rule and outbuilding's floor, for the same
# reason: a pier thinner than the jambs that flank it is two door frames touching,
# not a wall with openings in it. It is NOT `PIER_MIN_M`, which is about how much
# plain wall a SHOPFRONT must leave at the ends of a frontage a passer-by reads,
# and is a different question about a different elevation.
GOODS_DOOR_PIER_MIN_M = 2 * GOODS_DOOR_JAMB_M


def gable_top_m(u: float, u0: float, u1: float, wall_z: float, ridge_z: float,
                overhang: float) -> float:
    """How high the gable's sloping edge stands over the point `u` on that wall.

    Pure arithmetic, and it lives HERE rather than beside the builder for the reason
    the block at the top of this section gives: the commit gate has no Blender, and a
    number the gate cannot reach is a number nothing holds. `frame_storefront` passes
    its own `ROOF_OVERHANG_M` in, so the triangle measured here is the one
    `add_gable_roof` actually fills and the two cannot drift.

    The apex stands over the MIDDLE of the wall, which is the whole point of asking:
    the roof line at a bay near the corner is far lower than the same height taken at
    the ridge, and a hoist beam set out on the wall's midline arithmetic would be
    drawn out through a roof plane (T-1663).
    """
    half_base = (u1 - u0) / 2.0 + overhang
    if half_base <= 1e-6:
        return wall_z
    d = min(abs(u - (u0 + u1) / 2.0), half_base)
    return wall_z + (ridge_z - wall_z) * (1.0 - d / half_base)


def shopfront_width_m(bays: int) -> float:
    """Overall width of a shopfront of `bays` display windows plus its door.

    Snapped UP to the framing module: a shopfront is an opening cut in a framed
    wall, and its trimmer studs stand on stud centres like everything else. This is
    where the 16 in module becomes a proportion a viewer can see without being able
    to count a single stud.
    """
    raw = (2 * SHOP_PILASTER_M + SHOP_DOOR_W_M + bays * SHOP_BAY_W_M
           + (bays + 1) * SHOP_MULLION_M)
    n = int(raw / STUD_SPACING_M) + 1
    return round(n * STUD_SPACING_M, 4)


def _lean_to_rise(depth_m: float) -> float:
    """How far a rear ell's lean-to climbs over its own depth.

    A shallow pitch, because the roof has to arrive under the main block's eave and
    because a lean-to over a storeroom was covered in whatever shed water. Shared
    with the generator so the validator's refusal and the built roof agree.
    """
    return depth_m * 0.2679          # tan 15 degrees


# The most of its own frontage a store front takes when the record does not say.
# Not "as many bays as will fit": glass came in small panes and cost money in 1835,
# the wall between the openings is what the shelves stand against, and a front that
# is nearly all opening is a plate-glass idea from fifty years later.
SHOPFRONT_MAX_FRACTION = 0.45

# ---------------------------------------------------------------------------
# WHAT A "BAY" IS, AND WHOSE WORD IT IS (T-1665).
#
# Two counts wear the same word here and they differ by one, which is how the
# reconstruction specification came to look unsatisfiable on C3.
#
#   `shopfront_bays` — THIS MODULE'S count, and it counts SHOW WINDOWS. The door
#     is not one of them: `shopfront_width_m` adds `SHOP_DOOR_W_M` to `bays *
#     SHOP_BAY_W_M` separately, so a `shopfront_bays=1` front is a door with one
#     5 ft window beside it.
#   a FACADE bay — the SPECIFICATION's count, and it counts openings: a window or
#     the door, each one a vertical division of the elevation.
#
# The spec's usage is not a guess, and it is not the owner's to rule on either. It
# is settled by the spec's own words, in `1835_family_archetype_crosswalk.json`,
# and the witness is a door position beside an odd count:
#
#   D4  "3/5 bays; center or side door"
#   H1  "5 bays; center hall; kitchen ell; small porch"
#
# A centre door needs an odd number of bays to be centred in, and 3 and 5 are odd.
# Read the door OUT of the count and "3 bays, centre door" is a facade of four
# openings with a door that cannot be in the middle of them — so the door-exclusive
# reading contradicts the same sentence that states it, on two families, while the
# door-inclusive reading is the ordinary architectural one and contradicts nothing.
#
# So the crosswalk's bay counts map onto this module by `facade_bays`, and C3's
# "2-3 shop bays" asks for `shopfront_bays` of 1 or 2 — not 2 or 3. See
# docs/FACADE-BAYS.md for the measurement that follows from that, and
# `tools/test_shopfront_bay_count.py`, which re-derives the reading from the
# crosswalk rather than remembering it.
# ---------------------------------------------------------------------------

def facade_bays(shopfront_bays: int) -> int:
    """The specification's bay count for a shopfront of `shopfront_bays` windows.

    One more, because the door is a bay in that counting and is not one in this
    module's. Stated as a function rather than left as a `+ 1` at the call site so
    that the mapping has one home and a reader can find the argument for it above.
    """
    return shopfront_bays + 1


#: `shopfront_bay_verdict` reasons. The first is the rule answering; the second is
#: its floor answering and still inside the ceiling; the third is its floor
#: OVERRULING the ceiling, which is the case nothing used to say out loud.
BAY_WITHIN_FRACTION = "within_fraction"
BAY_FLOOR_WITHIN_FRACTION = "floor_within_fraction"
BAY_FLOOR_OVER_FRACTION = "floor_over_fraction"


def shopfront_bay_verdict(width_m: float) -> tuple[int, str, float]:
    """`default_shopfront_bays`, and WHY it answered that — count, reason, fraction.

    The count is the same value `default_shopfront_bays` returns; nothing about a
    built front depends on this function, and no asset's inputs read it (see
    generators/mesh_inputs.py: the params MODULE's bytes are not hashed, and this is
    a module function rather than a dataclass property, so it moves no mesh).

    It exists because the rule has a FLOOR and the floor can break the rule's own
    ceiling without saying so. Measured over the 45 committed `frame_storefront`
    phases on 2026-09-27: twenty-six reach the floor, and on TWENTY of those the one
    remaining window and the door put 50.0% to 66.7% of the frontage into opening,
    against a stated maximum of 45%. Those twenty are the narrow gable-front stores
    — C1, C2 and C3 — whose front is the 18-22 ft END of the building, where a door
    and one 5 ft window are already more than nine twentieths of the wall.
    `SHOPFRONT_MAX_FRACTION` was argued for a store filling a 55 ft lot frontage
    with its EAVES to the street, and on a narrow front it therefore decides
    nothing: the floor decides, and until this function existed it decided in
    silence. `tools/test_shopfront_bay_count.py` holds the override to fronts that
    genuinely cannot afford the next count up.
    """
    for bays in (3, 2):
        if shopfront_width_m(bays) <= width_m * SHOPFRONT_MAX_FRACTION:
            return bays, BAY_WITHIN_FRACTION, shopfront_width_m(bays) / width_m
    frac = shopfront_width_m(1) / width_m
    reason = (BAY_FLOOR_WITHIN_FRACTION if frac <= SHOPFRONT_MAX_FRACTION
              else BAY_FLOOR_OVER_FRACTION)
    return 1, reason, frac


def default_shopfront_bays(width_m: float) -> int:
    """How many show windows a frontage of this width carries, when the record
    does not say. Derived rather than fixed at one number, because a fixed
    fenestration is exactly the defect docs/LIBERTIES.md L23 records against the
    frame taverns: one five-bay rhythm spread across three buildings of different
    sizes, which reads as a finding about how the town was built and is an artefact
    of one archetype.

    The rule itself is `shopfront_bay_verdict`, which also says which of its two
    branches answered. This wrapper keeps the one-integer call the builder and the
    params resolver make, byte for byte as before.
    """
    return shopfront_bay_verdict(width_m)[0]


def from_phase(phase: dict, record: dict | None = None) -> FrameStorefrontParams:
    """Resolve one structure phase into generator parameters.

    Reads only the attested `value` of each form attribute plus its confidence.
    Footprint dimensions come from the phase footprint polygon's bounding box —
    the polygon is authoritative, the width and depth are derived.
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

    # The contract pins the mesh origin to polygon coordinate (0, 0). Deriving only
    # a bounding-box SIZE and then building from the origin silently translates any
    # polygon not anchored there, so the building would stand somewhere its own
    # footprint does not describe. Refuse instead — the same refusal frame_tavern
    # makes, and for the same reason.
    if abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise ParamError(
            f"footprint polygon starts at ({min(xs)}, {min(ys)}), not the origin. "
            f"docs/GLB-CONTRACT.md pins the mesh origin to polygon coordinate (0, 0); "
            f"building from a bounding box would silently move the structure "
            f"{max(abs(min(xs)), abs(min(ys))):.2f} m from where its footprint puts it. "
            f"Re-anchor the polygon at the origin and put the offset in position.")

    # `dock` is excluded from the sweep because this builder never reads it: a
    # dock statement selects a deck on the RENDERER's wharf layer
    # (tools/generate_river_wharves.py), not a metre of this mesh, and
    # generators/mesh_inputs.py hashes exactly what the builder can see — "only
    # a value the generator reads counts". Sweeping it in marked five South
    # Water stores stale on the day their landings were stated (T-0062) when
    # not one of their vertices could move.
    # `reconstruction` is the 665-roof programme's own block: it is present on every
    # anonymous or household roof it dealt and absent from every named building.
    recon = (record or {}).get("reconstruction") or {}
    confidences = {a: conf(a) for a in form if a != "dock"}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")

    # A FLOAT, and that one character is the whole of T-1659's C2 finding: `int()`
    # read the eight committed records that state `stories: 1.5` as one-storey shops.
    stories = float(val("stories", 2.0))
    sign = val("sign")

    # The default bay count is measured against the frontage the shopfront will
    # actually stand on, which an end ell shortens.
    ell_w = float(val("ell_width_m", round(width * 0.45, 3)))
    front_w = round(width, 3)
    if bool(val("ell", False)) and str(val("ell_side", "rear")) == "end":
        front_w -= ell_w

    p = FrameStorefrontParams(
        width_m=round(width, 3),
        depth_m=round(depth, 3),
        stories=stories,
        wall_height_m=float(val("wall_height_m",
                                {1.0: 3.1, 1.5: 3.6, 2.0: 5.4}.get(stories, 5.4))),
        knee_wall_m=float(val("knee_wall_m", KNEE_WALL_DEFAULT_M)),
        roof_type=str(val("roof_type", "gable")),
        roof_pitch_deg=float(val("roof_pitch_deg", 33.0)),
        gable_front=bool(val("gable_front", False)),
        construction=str(val("construction", "balloon_frame")),
        cladding=str(val("cladding", "clapboard")),
        paint=str(val("paint", "unpainted")),
        siding_exposure_m=float(val("siding_exposure_m", 0.14)),
        framing_exposed=bool(val("framing_exposed", False)),
        loft=bool(val("loft", False)),
        chimneys=int(val("chimneys", 1)),
        shopfront=bool(val("shopfront", True)),
        shopfront_bays=int(val("shopfront_bays", default_shopfront_bays(front_w))),
        shopfront_door_side=str(val("shopfront_door_side", "centre")),
        goods_door=bool(val("goods_door", True)),
        goods_door_side=str(val("goods_door_side", "end")),
        goods_door_bays=int(val("goods_door_bays", 1)),
        hoist_door=bool(val("hoist_door", False)),
        ell=bool(val("ell", False)),
        ell_side=str(val("ell_side", "rear")),
        ell_width_m=ell_w,
        ell_depth_m=float(val("ell_depth_m", round(depth * 0.35, 3))),
        ell_stories=int(val("ell_stories", 1)),
        ell_height_m=(None if val("ell_height_m") is None
                      else float(val("ell_height_m"))),
        sign=(None if sign is None else str(sign)),
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
# THE ELEVATION'S SET-OUT, and the openings that fall out of it (T-0459).
#
# These live here so that something with no Blender can ask WHERE THE OPENINGS
# ARE. The signage layer is the caller that needed it: it was placing painted
# names and wall boards at a height that suited the trade and had no idea what was
# behind them, so twenty boards were hung over doors and windows. They belong in
# the params module for the same reason `shopfront_head_z` does — the commit gate
# has to read them and the commit gate has no Blender.

# THE BUILDER READS THESE (T-0520). It used to compute the same rectangles beside
# them, which made two copies of one set-out and left a written rule — change one,
# change the other — as the only thing holding them together. It does not any more:
# the builder calls these functions, so an opening moved here moves on the mesh a
# visitor sees, and there is nowhere else to move it. What made that a ticket of its
# own is that the asset staleness hash covers each archetype's builder module BYTE
# FOR BYTE, so touching the three builders staled 212 assets and demanded the
# town-wide rebake that landed with the refactor.
# ---------------------------------------------------------------------------

def snap(x: float, origin: float, module: float) -> float:
    """The nearest framing line at or near `x`, measured from `origin`.

    This is where the 16 in module stops being a note in a docstring: every opening
    on the elevation is set out on it, because in a framed wall an opening lands
    between studs or it does not land at all.
    """
    return origin + round((x - origin) / module) * module


def module_m(p: "FrameStorefrontParams") -> float:
    """The framing module the elevation is set out on."""
    return STUD_SPACING_M if p.construction == "balloon_frame" else POST_SPACING_M


def main_extent(p: "FrameStorefrontParams") -> tuple[float, float, float, float]:
    """The store block's rectangle inside the footprint bbox.

    The ell is carved OUT of the footprint rather than bolted onto it, so the whole
    building stays inside the polygon the record attests — log_dwelling's rule, and
    the one that keeps GROUND_CONTACT 'perimeter' true of the mesh.
    """
    w, d = p.width_m, p.depth_m
    if not p.ell:
        return 0.0, 0.0, w, d
    if p.ell_side == "end":
        return 0.0, 0.0, w - p.ell_width_m, d
    return 0.0, p.ell_depth_m, w, d


def ell_extent(p: "FrameStorefrontParams") -> tuple[float, float, float, float]:
    """The ell's rectangle. A rear ell sits against the -x end of the back wall,
    leaving the yard on the loading side; an end ell runs to the +x edge and takes
    the whole depth."""
    w, d = p.width_m, p.depth_m
    if p.ell_side == "end":
        return w - p.ell_width_m, 0.0, w, d
    return 0.0, 0.0, p.ell_width_m, p.ell_depth_m


def shopfront_extent(p: "FrameStorefrontParams", mx0: float,
                     mx1: float) -> tuple[float, float, float]:
    """(x0, x1, head_z) for the shopfront, centred on the frontage and snapped to
    the framing module."""
    sf_w = shopfront_width_m(p.shopfront_bays)
    centre = (mx0 + mx1) / 2.0
    x0 = snap(centre - sf_w / 2.0, mx0, STUD_SPACING_M)
    x0 = min(max(x0, mx0 + 0.30), mx1 - sf_w - 0.30)
    return x0, x0 + sf_w, p.shopfront_head_z


def shopfront_panels(p: "FrameStorefrontParams",
                     shop: tuple[float, float, float]) -> list[tuple]:
    """The shopfront's panels left to right, as `(kind, u0, u1, z0, z1)`.

    `kind` is `shop_door` or `show_window`; the pilasters, mullions and stall riser
    are solid boards and are not listed, because a sign nailed over a mullion covers
    nothing a visitor was meant to see through.
    """
    sx0, sx1, head = shop
    inner0, inner1 = sx0 + SHOP_PILASTER_M, sx1 - SHOP_PILASTER_M
    bays = p.shopfront_bays
    fit = (inner1 - inner0 - SHOP_DOOR_W_M - bays * SHOP_MULLION_M) / bays
    bay_w = min(fit, SHOP_BAY_W_M * 1.15)
    run = SHOP_DOOR_W_M + bays * bay_w + bays * SHOP_MULLION_M
    cur = inner0 + (inner1 - inner0 - run) / 2.0
    door_at = {"left": 0, "right": bays, "centre": (bays + 1) // 2}[p.shopfront_door_side]

    out: list[tuple] = []
    for i in range(bays + 1):
        if i == door_at:
            out.append(("shop_door", cur, cur + SHOP_DOOR_W_M, 0.0, head))
            cur += SHOP_DOOR_W_M
        else:
            out.append(("show_window", cur, cur + bay_w, SHOP_SILL_Z_M, head - 0.13))
            cur += bay_w
        if i < bays:
            cur += SHOP_MULLION_M
    return out


#: THE STOREY WINDOW, on any elevation of this archetype. The front wall's are set
#: out by `front_window_rects` below; the flanks and the back are the builder's own
#: and read these, so there is one window in this archetype and not two (T-0520).
STOREY_WIN_W_M = 0.85
STOREY_WIN_H_M = 1.30
#: The sill's height up its own storey, as a fraction of the storey height.
STOREY_SILL_FRAC = 0.30


def storey_sill_z(p: "FrameStorefrontParams", story: int) -> float:
    """The sill height of storey `story`'s windows, above the base of the walls."""
    story_h = p.story_height_m
    return story * story_h + story_h * STOREY_SILL_FRAC


def front_window_rects(p: "FrameStorefrontParams", x0: float, x1: float,
                       shop: tuple | None) -> list[tuple]:
    """The storey windows on the FRONT wall, as `(u0, u1, z0, z1)`.

    THE BAY COUNT COMES FROM THE FRONTAGE, not from a constant — the argument is at
    `frame_storefront._fenestration`, which draws exactly this list.
    """
    win_w, win_h = STOREY_WIN_W_M, STOREY_WIN_H_M
    front_w = x1 - x0
    bays = max(2, min(7, int(round(front_w / 2.45))))
    module = module_m(p)
    out: list[tuple] = []
    for story in range(p.full_stories):
        z0 = storey_sill_z(p, story)
        if story == 0 and shop is not None:
            continue                       # the ground storey is the shop
        for i in range(bays):
            cx = snap(x0 + front_w * (i + 0.5) / bays, x0, module)
            cx = min(max(cx, x0 + win_w), x1 - win_w)
            out.append((cx - win_w / 2, cx + win_w / 2, z0, z0 + win_h))
    return out


def plain_door_rect(u0: float, u1: float) -> tuple[float, float, float, float]:
    """`(u0, u1, z0, z1)` of the single door a store with no shopfront shows the
    street, centred on the frontage `u0..u1`. Robert Kinzie's Wolf Point
    'storehouse' is the case the builder argues; the rectangle is stated here so the
    builder and the signage layer read one door (T-0520)."""
    cx = (u0 + u1) / 2.0
    return cx - 0.52, cx + 0.52, 0.02, 2.06


def front_openings(p: "FrameStorefrontParams") -> list[dict]:
    """Everything on the front wall a signboard must not be hung over.

    In footprint coordinates: `u` along the front wall from the polygon's own
    origin, `z` above the base of the walls. Openings proper — the shop door, the
    show windows, the storey windows, a plain storehouse door — plus the two pieces
    of applied joinery the archetype puts on the same face, the fascia board and the
    blank signboard nailed to it. Those two are not openings, but a name painted
    across them is as wrong as one painted across the glass, and the caller is
    entitled to know they are there.
    """
    mx0, _my0, mx1, _my1 = main_extent(p)
    shop = shopfront_extent(p, mx0, mx1) if p.shopfront else None
    out: list[dict] = []

    if shop is not None:
        sx0, sx1, head = shop
        for kind, u0, u1, z0, z1 in shopfront_panels(p, shop):
            out.append({"kind": kind, "u0": u0, "u1": u1, "z0": z0, "z1": z1})
        out.append({"kind": "fascia", "u0": sx0 - 0.04, "u1": sx1 + 0.04,
                    "z0": head, "z1": head + SHOP_FASCIA_M})
        if p.sign is not None:
            w = min((sx1 - sx0) * 0.78, 3.2)
            cx = (sx0 + sx1) / 2.0
            out.append({"kind": "archetype_sign", "u0": cx - w / 2, "u1": cx + w / 2,
                        "z0": head + SHOP_FASCIA_M * 0.06,
                        "z1": head + SHOP_FASCIA_M + 0.11})
    else:
        du0, du1, dz0, dz1 = plain_door_rect(mx0, mx1)
        out.append({"kind": "door", "u0": du0, "u1": du1, "z0": dz0, "z1": dz1})

    for u0, u1, z0, z1 in front_window_rects(p, mx0, mx1, shop):
        out.append({"kind": "window", "u0": u0, "u1": u1, "z0": z0, "z1": z1})
    return out
