#!/usr/bin/env python3
"""Generate one platted block of anonymous infill from the 665-roof schedule.

ROADMAP T-A2 onward. The three parcels before this one — phase-one South, the West
approaches, the North Division cluster — each authored their own coordinates: a row
northing and a list of eastings, or a centre per slot. That was the only thing
available before the plat module existed. It does not survive the module: the block
and lot grid (`tools/generate_plat_lots.py`, ROADMAP K7) knows where the lots are, and
a recipe that retypes coordinates beside it is a second opinion about the same ground.
The K7 slice found seven buildings standing in the road for exactly that reason.

So this generator authors NO coordinates. The recipe says which family stands on which
lot and whether it fronts the street or the alley; every metre comes from the committed
lot polygon. That is also what makes the parcel shape repeat (T-A3…T-An): the next block
is a recipe entry, not a new geometry argument.

**Family geometry comes from the crosswalk, not from this file.**
`data/reconstruction/1835_family_archetype_crosswalk.json` already carries, per family,
the footprint band, the storey count, the eave height and the placeholder archetype it
resolves through. The earlier generators retyped some of that into Python and could only
build the families somebody had retyped — which is why `family_bands_ft` in the building
inventory has no H1 or H2 band at all, while the schedule apportions H1 and H2 to this
very block. Read where the numbers are authored and every family the programme can name
becomes buildable. The crosswalk agrees with `family_bands_ft` on all 21 families both
of them carry; it also covers the 14 they do not.

Every record this writes is an invention: an anonymous count-unit toward a documented
aggregate. Presence, position, footprint and every form value grade at the bottom tier
with a reasoning note, and no lot is numbered — this project has never read Thompson's
numbering off a sheet, and standing on a generated lot is not standing on a recovered one.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
RECIPE_PATH = DATA / "reconstruction" / "1835_platted_block_parcels.json"
INVENTORY_PATH = DATA / "reconstruction" / "1835_building_inventory.json"
LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
SOURCE_ID = "owner_chicago_1835_reconstruction_spec_2026"
PHASE_ID = "inferred_1835"
PREFIX = "recon_1835_blk_"

sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

# T-E2's refused ground is resolved from the committed traces rather than stored, so the
# generator asks the same command the gate does instead of keeping its own copy.
from band_notes import split_notes  # noqa: E402
from placement_policy_1835 import constant  # noqa: E402
from measure_no_build_ground import inside as point_in_ring  # noqa: E402
from measure_no_build_ground import region_ring as no_build_ring  # noqa: E402
# T-0112. The clapboard stock is dealt at the end of the parcel — over all fourteen
# blocks at once, because a roof on one block's alley face stands within 60 m of the
# next block's — since it is the one form value that depends on where a building's
# neighbours stand. See tools/siding_stock.py.
from siding_stock import deal_records as deal_siding  # noqa: E402
# T-1311. A band the FUNCTIONS table below has no row for takes its term from the same
# folding rule the migration used, so a new band cannot reopen the free string.
from normalise_structure_function import canonical as canonical_function  # noqa: E402


def no_build_rings() -> dict[str, list[tuple[float, float]]]:
    """Every region the refusal file authors, resolved the way that region's entry says.

    Named by the FILE rather than listed here, so a region added there is refused here on
    the same commit. Until T-0891 this function held its own copy of the two rings, and
    the gate and the generator could have come to disagree about what ground exists
    without either of them saying so.
    """
    refused = json.loads(
        (DATA / "reconstruction" / "1835_no_build_ground.json").read_text(encoding="utf-8"))
    return {region["id"]: no_build_ring(region) for region in refused["regions"]}

# An adopted roof's `occupants` block is authored ONCE, in the household programme's
# ledger, and handed to whichever generator owns the roof — the arrangement the three
# earlier anonymous parcels already use. Writing the adoption here as well would put it
# in two places and let them disagree, and hand-editing a generated record would fail
# the drift check that makes these parcels trustworthy in the first place.
from inferred_occupancy import occupancy  # noqa: E402

# Which lot is already taken is the SAME question the schedule asks before it deals this
# parcel its roofs, so it is asked in one place and imported by both (ROADMAP T-A7).
from plat_occupancy import LOT_MARGIN_M, exclusive_lots, footprints  # noqa: E402
from plat_occupancy import lot_holders, shared_business_fronts  # noqa: E402
import lot_addresses  # noqa: E402

# The face of a committed block — the line a party-line street row stands on, the way
# its fronts look, and where along it a wall lands. Authored once, in the module the
# first frontage run (T-0077) and this one both import, because a face retyped beside
# the committed boundary would be a second opinion about the same ground.
from block_faces import extent as face_extent, face_frame  # noqa: E402
from block_faces import project as face_project  # noqa: E402

# How many party-line units a lot of the committed grid holds (T-0079). Authored in
# tools/reconcile_665.py because that is where the schedule counts with it; imported
# here rather than retyped, so the ceiling the schedule deals against and the ceiling
# the generator enforces cannot become two numbers.
from reconcile_665 import ROW_UNITS_PER_LOT  # noqa: E402

# The family band, and the one rule that turns it into an instance's dimensions. It
# used to live in this file; the North Division parcel needed the same arithmetic and
# had a retyped constant instead, so the rule moved to one module both import
# (ROADMAP T-V1).
from family_bands import (dimensions_m, eave_floor, eave_for_ridge,  # noqa: E402
                          eave_limits, families, pitch_deg, stable_fraction,
                          storeys, wall_height_m)
from ridge_model import ridge_run_m  # noqa: E402
from roof_form import note_refusal, roof_kind  # noqa: E402

OCCUPANCY = occupancy()

# The same separation the household parcel enforces. A generated building that lands
# three metres from another one is not a dense town, it is two records occupying one
# yard, and nothing downstream can tell them apart.
MIN_SEPARATION_M = 3.0
# LOT_MARGIN_M — how far a footprint must stand clear of its own lot line — is authored
# in `tools/plat_occupancy.py` and imported above, because the occupancy rule reads the
# same number from the other side: the buildable part of a lot is the lot inset by it.
# The walker's step tolerance, from the household parcel's placement gate.
MAX_RELIEF_M = 0.30


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


INVENTED_NOTE = (
    "INVENTED, NOT DERIVED. This value comes from a typology in the reconstruction "
    "spec — what a building of this kind was ordinarily like — and NOT from evidence "
    "about this particular building, because there is no particular building: the "
    "structure itself is an invention filling a demonstrable need of the town. The "
    "spec is cited because the invention is bounded by it, which is what makes it "
    "defensible rather than arbitrary; the GRADE is the bottom tier because nothing "
    "here is a reading of a source about this thing. "
)


# T-0189, and the same fault the `symbolic_location` clause below carried: this note was
# written for T-0078's run on South Water Street, where every literal in it was true, and
# it has been printed verbatim on every frontage run since. The card shows it beside the
# location line, so a house on Washington Street 400 m from the water was told it stood on
# "the town's river business front" and looked at "the river beyond it, as every documented
# store on this face does" — on a face whose entire documented 1835 frontage is the estray
# pen (tools/measure_street_frontage.py randolph washington: Washington 1 record, 0 inferred
# households). Two claims about the town were removed and nothing else changed. What stays
# is the treatment's real provenance: the 1834 view IS where a row of party walls comes
# from, and a row placed on any other face is borrowing it, which the note now says.
# T-0208, and it is the same class of fault again in the same template: prose written for
# one face printed verbatim on another. The sentence used to say "its east wall is fixed by
# {anchor}" unconditionally, which was true while every run in the town anchored on the EAST
# end of its face and packed west — the anchored wall and the east wall were the same wall.
# T-0079 opened the west end for a corner lot that builds to the corner, and `place_frontage`
# below sets `east = along_min + clear_m + width` on such a run: the wall standing `clear_m`
# off the side lot line is the WEST one, and the east wall is derived from it by the
# building's own width. Nine of the twenty-seven records carrying this note are
# west-anchored, and each told a reader to put its east wall against the west side line.
# Which wall the anchor fixes is now read off the anchor rather than assumed.
FRONTAGE_NOTE = (
    "PARTY-LINE FRONTAGE, DERIVED FROM THE COMMITTED PLAT (T-0078). This building does "
    "not stand centred on a lot at a typology setback: it stands ON the {face} face of "
    "{block}, the block's {street} Street frontage, whose line and bearing are read from "
    "the block boundary in data/traces/vectors/thompson_lots.json — the same committed "
    "geometry the lot grid and the corridor gate are derived from. Its front wall is "
    "{setback} m back from that lot line, {line_why}, and its {anchored_wall} wall is "
    "fixed by {anchor}. The bearing is the face's own, so the front looks square at {street} "
    "Street. The run carries no "
    "lateral offset, because a shared party wall is one wall and cannot wander. WHAT IS "
    "INVENTED IS STILL EVERYTHING THAT MATTERS: that a building stood here at all, which "
    "building it was, and that these particular units stood shoulder to shoulder. What the "
    "1834 South Water Street view supports is the TREATMENT — a continuous working row of "
    "party walls rather than detached cottages set back on grass. The treatment is what "
    "this placement takes from it, and a run standing on any other face of the town is "
    "borrowing it from that one street: the view draws a row, it does not place this row. "
    "Standing on a derived block face is not standing "
    "on a recovered lot, and the side lot lines this row crosses were always conjectural."
)


# Where the run's line came from, in the record's own note. A frontage that opens a
# face takes the closest line the plat module's margin allows; a frontage that joins a
# face already built takes the line those buildings stand on, because a street wall is
# one wall (T-0104). Neither is a measurement of 1835 and the note says so either way.
LINE_WHY_MARGIN = ("which is the closest line the plat module's own margin allows and is "
                   "not a measurement of this frontage")
LINE_WHY_ADOPTED = ("which is NOT a measurement of this frontage either: it is the line "
                    "the buildings already standing on this face were built to, adopted "
                    "so that the face carries one street wall rather than two (T-0104). "
                    "The plat module's lot margin still fixes the side lines this run "
                    "stands clear of; what it does not fix is a street line that other "
                    "records had already set")


def invented(value, reason: str) -> dict:
    return {"value": value, "confidence": "reconstructed", "sources": [SOURCE_ID],
            "note": INVENTED_NOTE + reason}


# --------------------------------------------------------------------------
# the family table, read from the crosswalk
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# the families this generator refuses to mass, and why each one
# --------------------------------------------------------------------------
#
# A family with no form rule is ordinarily a gap: somebody adds the rule and the
# next recipe uses it. The families below are NOT that, and the generic message
# ("add one before a recipe uses it") is the wrong instruction for them, because
# each carries a precondition the crosswalk already wrote down and adding a form
# rule would step straight over it. They are refused by name, with the
# precondition quoted, so a parcel that meets one of these slots has to defer it
# and say so rather than reach for a shape.
#
# There are two kinds of precondition here, and they refuse for different reasons.
#
# THE INSTITUTIONAL FAMILIES (I1, I2, I3) are refused because of what an anonymous
# one would CLAIM. An anonymous DWELLING is the ordinary case in a town of 3,000
# whose householders were never enumerated roof by roof. An anonymous PUBLIC
# building is a different claim — that an institution stood here and left no
# record at all — and 1835 Chicago's public buildings are few enough to be
# nameable.
#
# F3 is refused for the opposite reason: not the claim but the GROUND. An unnamed
# river warehouse is an ordinary count-unit and nobody doubts there were some; what
# this generator cannot supply is the water its own crosswalk entry makes a
# precondition of the form. A refusal of that kind is not permanent and is not
# about anonymity — it names the parcel that should carry the slot instead.
REFUSED_FAMILIES = {
    "I1": (
        "worship or meeting buildings. The crosswalk schedules four of them and says "
        "the schedule 'explicitly calls for four custom assets' which the placeholder "
        "'must not genericize'. Each is a named congregation with its own dossier, so "
        "an anonymous one is not a count-unit toward them — it is a fifth."
    ),
    "I2": (
        "schools and community-use structures. The crosswalk gives the family two "
        "roofs and says each 'needs named-record reconciliation'. (One anonymous I2 "
        "stands in the North Division from an earlier parcel, written before this rule "
        "and before this generator existed; it is recorded in docs/LIBERTIES.md rather "
        "than quietly removed, and it is not a precedent this generator extends.)"
    ),
    "I3": (
        "civic or public-service structures. THE REFUSAL IS NOW THE RESEARCH RATHER "
        "THAN THE ARCHETYPE (ROADMAP T-I3, docs/RESEARCH/civic_public_buildings_1835.md): "
        "the town's public buildings on 1835-07-01 are enumerable and every one of them "
        "is already a committed named record — the log jail, the council house and the "
        "lighthouse. The court-house went up in the fall of 1835 and the engine house was "
        "contracted on 30 December 1835; the estray pen is roofless; and every other "
        "public function in the town, the post office and the United States Land Office "
        "and the county's own offices among them, was carried on inside a private "
        "building. There is no unnamed civic roof for a slot to be spent on. (The "
        "archetype argument stands and was the original ground: the family resolves "
        "through the fort_structure placeholder, whose whole vocabulary of building kinds "
        "is garrison words — quarters, barracks, blockhouse, magazine, store, guard, "
        "sutler, artillery — so massing one would also stand a garrison building in the "
        "middle of the platted town.) The crosswalk stated the precondition itself: the "
        "six-roof aggregate 'spans unlike functions; they must reconcile to named public "
        "records before selecting construction'. Three of those six slots are now known "
        "to be a count of nothing, and correcting the target is T-I3(b)."
    ),
    "F3": (
        "large river warehouses, and this refusal is about SITE ACCESS rather than about "
        "an anonymous claim \u2014 an unnamed warehouse is an ordinary count-unit, and the "
        "three the crosswalk schedules are real roofs somebody has to place. What this "
        "generator cannot give one is the river. It authors no coordinates: every metre "
        "comes from a committed LOT polygon on the platted grid, and a lot is a rectangle "
        "inside a block bounded by four platted STREETS. F3's own crosswalk entry makes "
        "water access a precondition of the form \u2014 the variant is 'multiple cargo doors; "
        "landing apron; sparse glazing', and the assumption note reads 'Landing apron and "
        "cargo-door arrangement must follow site access and cannot extend into water or "
        "duplicate a counted pier'. The landing and wharf ground of the main stem lies "
        "OUTSIDE this grid, beyond South Water and Market, and is placed by "
        "tools/generate_river_wharves.py against the committed bank rather than against a "
        "lot. So an F3 massed here is a river warehouse the river does not reach: its "
        "cargo-door rhythm opens onto a platted roadway, and its landing apron would have "
        "to cross a public street onto ground this parcel does not hold. Measured on the "
        "committed heightfield, the block this refusal was first met on \u2014 "
        "blk_lake_franklin, bounded by Lake, Randolph, Franklin and Wells \u2014 stands 134 m "
        "from the nearest water. That the schedule keeps dealing F3 onto platted blocks "
        "is a fault in the DEAL and not in the block: T-0275."
    ),
}


FUNCTIONS = {
    "D1": "older_log_dwelling", "D2": "rough_plank_dwelling_or_shanty",
    "D3": "one_room_frame_cottage", "D4": "two_room_frame_cottage",
    "D5": "deep_plan_frame_cottage", "D6": "one_and_a_half_story_frame_cottage",
    "D7": "small_two_story_frame_house",
    "H1": "larger_one_and_a_half_story_house", "H2": "merchant_or_professional_house",
    "C1": "small_shop_or_office", "C2": "store_residence",
    "C3": "narrow_two_story_store",
    "W1": "blacksmith_shop", "W2": "carpenter_or_joiner_shop",
    "W3": "cooper_wagon_or_wheelwright_shop", "W4": "small_artisan_shop",
    "F1": "freight_or_storage_shed", "F2": "narrow_two_story_warehouse",
    "A1": "stable", "A2": "barn_or_carriage_shed", "A3": "privy",
    "A4": "woodshed_or_storage_shed", "A5": "small_utility_building",
}

# The prose the record's human-facing `name` has always used. Split from FUNCTIONS
# by T-1311, which closed the `function` vocabulary: the value is now a term from
# `data/structures.schema.json`, and a term is not a phrase to put in front of a
# visitor. Both tables are keyed by the same band, and this one keeps the names
# these records already carry - migrating a vocabulary is not licence to rename
# 120 buildings.
LABELS = {
    "D1": "older log dwelling",
    "D2": "rough plank dwelling or shanty",
    "D3": "one-room frame cottage",
    "D4": "two-room frame cottage",
    "D5": "deep-plan frame cottage",
    "D6": "one-and-a-half-story frame cottage",
    "D7": "small two-story frame house",
    "H1": "larger one-and-a-half-story house",
    "H2": "merchant or professional house",
    "C1": "small shop or office",
    "C2": "store-residence",
    "C3": "narrow two-story store",
    "W1": "blacksmith shop",
    "W2": "carpenter or joiner shop",
    "W3": "cooper, wagon, or wheelwright shop",
    "W4": "small artisan shop",
    "F1": "freight or storage shed",
    "F2": "narrow two-story warehouse",
    "A1": "stable",
    "A2": "barn or carriage shed",
    "A3": "privy",
    "A4": "woodshed or storage shed",
    "A5": "small utility building",
}


def finish_for(key: str) -> tuple[str, str]:
    bucket = stable_fraction(key, 9)
    if bucket < .34:
        return "fresh_timber", "unpainted"
    if bucket < .58:
        return "weathered_timber", "unpainted"
    if bucket < .75:
        return "whitewash", "whitewash"
    if bucket < .84:
        return "ochre", "unpainted"
    if bucket < .92:
        return "red_oxide", "red"
    return "mixed_patch", "unpainted"


def door_kind(family: str) -> str:
    """What has to get through the opening, which is a claim about the building's use."""
    if family in ("W1", "W3", "F1", "A2"):
        return "wagon"
    if family in ("W2", "A1"):
        return "stable"
    return "man"


def band_note(family: str) -> str:
    """The sentence that defends every invented form value, and it is a source claim.

    Kept in one place because K33 restricts where it may be attached, and a claim that
    is authored in one file and audited in another drifts. See tools/band_notes.py.
    """
    return (f"Type-level choice within the {family} band in the supplied reconstruction "
            "specification; it is not evidence for this anonymous instance.")


def form_for(family: str, spec: dict, key: str, width: float, depth: float,
             paint: str) -> dict:
    """Form values, with the storey count, eave height and pitch read off the crosswalk.

    `_form_body` authors every value exactly as it always has, with the citation
    attached to all of them; `split_notes` (ROADMAP K33) then strips that citation from
    the values whose family authors nothing for it to point at, and says instead what
    the value actually is — the reconstruction generator's type default. `note_refusal`
    (T-0179) then adds, on the families whose roof line offers a SHED this town does not
    build, the measured reason it does not — because a refusal that lives only in a
    Python tuple is a refusal no visitor can read.
    """
    return note_refusal(
        split_notes(_form_body(family, spec, key, width, depth, paint), family,
                    band_note(family)),
        family, width, depth)


# WHICH ROOF A FAMILY GETS is `tools/roof_form.py`'s answer and no longer this file's
# (T-0179). It was decided here and in four other parcels, as the same literal written
# five times, and the five had already drifted: three named A5 among the shed families
# and two — this one and `generate_inferred_infill.py` — did not. No A5 stands on these
# blocks, so adopting the shared rule moves nothing here; it moves what the schedule
# WOULD deal, which is the whole point of a rule with one home.


def _pitch_default(family: str, levels: float) -> float:
    """The generator's own type value, which is what a family authoring no band gets."""
    if family == "D1":
        return 38.0
    if family.startswith(("C", "F")) and family != "F1":
        return 34.0
    if family.startswith(("D", "H")) and family != "D2":
        return 44.0 if levels == 1.5 else 38.0
    return 18.0 if roof_kind(family)[0] == "shed" else 32.0


def _form_body(family: str, spec: dict, key: str, width: float, depth: float,
               paint: str) -> dict:
    why = band_note(family)
    # The key is what lets a family whose crosswalk `levels` is a BAND — W2 is 1-1.5 —
    # be sampled rather than refused. Without it this generator died on the day the
    # schedule dealt it one, which nothing in the repo said until the family sweep
    # dealt every family it is allowed to (T-0142).
    levels, loft = storeys(spec["levels"], key)
    construction = "balloon_frame" if stable_fraction(key, 6) < .52 else "braced_frame"
    # The door is chosen before the eave because the eave floor depends on it: a wagon
    # door needs a metre more wall than a man door, and asking for the floor without
    # naming the door is how a band gets sampled below what the archetype can build.
    door = door_kind(family)
    # ...and the ARCHETYPE bounds the band at BOTH ends (T-0142). H2's authored eave
    # runs to 21 ft and `frame_dwelling` will not carry a two-storey wall over 6.2 m,
    # so a uniform sample dealt this block a merchant house the generator refused to
    # build; D6's runs down to 10 ft and the same archetype will not carry a half
    # storey under 3.05 m. Both limits are asked of the archetype, never retyped here.
    arch_lo, arch_hi = eave_limits(spec.get("archetype"), levels)
    floor, ceiling = max(eave_floor(family, door), arch_lo), arch_hi
    # ...and the family's own RIDGE band bounds it once more (T-0148). The pitch below
    # is already constrained by that band; the eave was not, so a low draw could leave
    # no pitch inside the family's band able to reach it, and the gate then reported a
    # ridge outside a band that is reachable at an eave the family also authors. Two
    # A1 stables on these blocks stood outside their ridge band for exactly that. The
    # eave is held to the nearest value in its OWN band that the ridge band can be met
    # from; a draw that already meets it is returned untouched.
    roof_type, gable_front = roof_kind(family)
    run = ridge_run_m(spec.get("archetype"), roof_type, width, depth, gable_front)
    wall = eave_for_ridge(wall_height_m(family, spec["eave_ft"], key, floor, ceiling),
                          family, spec["eave_ft"], spec.get("roof"),
                          spec.get("ridge_ft"), run, _pitch_default(family, levels),
                          key, floor, ceiling)

    # THE PITCH, T-0142, and it is T-0145's repair arriving in the parcel that needed it
    # next. This generator dealt a retyped constant — 44 deg to every 1.5-storey D or H
    # family, 38 to the rest — and a constant is a claim of uniformity no source makes.
    # Worse, three of the families it deals are refused by their OWN crosswalk entry at
    # that constant: H1 cites 8:12-11:12 and was dealt 44.0, H2 and H3 cite 6:12-9:12 and
    # were dealt 38.0. So the pitch comes from the family's band, constrained by the
    # ridge band the same entry authors, which needs the run the roof climbs — and that
    # is the archetype's, so `ridge_model` is asked for it. A family whose roof line
    # names no pitch keeps the type default it always had.
    def pitch() -> float:
        return pitch_deg(family, spec.get("roof"), key,
                         _pitch_default(family, levels), eave_m=wall, run_m=run,
                         ridge_ft=spec.get("ridge_ft"))

    if family == "D1":
        return {
            "stories": invented(1, why), "wall_height_m": invented(wall, why),
            "roof_type": invented("gable", why),
            "roof_pitch_deg": invented(pitch(), why),
            "construction": invented("log", why), "loft": invented(True, why),
            "chimneys": invented(1, why),
        }

    if family.startswith(("D", "H")) and family != "D2":
        big = family in ("D7", "H2")
        plan = "centre_passage" if big else ("single_pen" if family == "D3" else "hall_parlour")
        result = {
            "stories": invented(levels, why), "wall_height_m": invented(wall, why),
            "roof_type": invented("gable", why),
            "roof_pitch_deg": invented(pitch(), why),
            "construction": invented(construction, why), "plan": invented(plan, why),
            "bays": invented(5 if big else (3 if width >= 5.4 else 2), why),
            "chimneys": invented(2 if big else 1, why),
            "paint": invented(paint, why),
        }
        # Slot 10, not slot 7: `family_bands.pitch_deg` draws on 7, and two decisions
        # sharing a slot would make a house's porch a function of its roof pitch.
        if stable_fraction(key, 10) < .58:
            result["porch"] = invented("stoop", why)
        return result

    if family.startswith(("C", "F")) and family != "F1":
        return {
            "stories": invented(levels, why), "wall_height_m": invented(wall, why),
            "roof_type": invented("gable", why),
            "roof_pitch_deg": invented(pitch(), why),
            "gable_front": invented(family.startswith("C"), why),
            "construction": invented(construction, why),
            "cladding": invented("clapboard" if family != "F2" else "vertical_board", why),
            # T-0430. A LOFT IS AUTHORED IN THE BAND OR IT IS NOT AUTHORED AT ALL.
            # This line used to read `family == "C2"`, so every store-residence this
            # generator built carried a loft on top of the 1.5 levels its own crosswalk
            # entry authors — and `tools/measure_band_claims.py` prices a loft at the
            # half level it is worth everywhere else in this dataset, so the record
            # claimed 2 levels while citing a band of 1.5. That is how
            # `recon_1835_blk_randolph_clark_c2_01:levels` got into the K25(a) ratchet
            # on 2026-08-15, and the second C2 this generator was asked for would have
            # put a second offender in a file whose own note says it may only ever grow
            # to record a REPAIR. The crosswalk's convention is explicit: a family that
            # wants one writes `1 + loft` in `levels`, which `family_bands.storeys()`
            # reads and this generator has always honoured through `loft` above. C2
            # writes `1.5` and offers "attic rooms" in its VARIANTS column, beside
            # "rear lean-to" and "signboard" — optional features this generator does
            # not switch on for every instance either. So the loft follows the band and
            # nothing else, which takes one offender back out of the ratchet.
            "paint": invented(paint, why), "loft": invented(loft, why),
            "chimneys": invented(1 if not family.startswith("F") else 0, why),
            "shopfront": invented(not family.startswith("F"), why),
            "goods_door": invented(True, why), "goods_door_side": invented("end", why),
        }

    if not family.startswith(("A", "W")) and family != "D2" and family != "F1":
        raise SystemExit(f"{family} has no form rule in this generator; add one before "
                         f"a recipe uses it")

    material = "plank"
    if family == "A1":
        material = "log"
    elif family in ("A2", "W2"):
        material = "light_frame"
    return {
        "wall_height_m": invented(wall, why), "roof_type": invented(roof_type, why),
        "roof_pitch_deg": invented(pitch(), why),
        "construction": invented(material, why), "door": invented(door, why),
        "door_side": invented("front", why), "loft": invented(loft, why),
        "board_gap_m": invented(.012, why), "paint": invented(paint, why),
    }


# --------------------------------------------------------------------------
# geometry, entirely from the committed lot polygons
# --------------------------------------------------------------------------

def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def lot_frame(lot: dict, alley: list[tuple[float, float]]) -> dict:
    """The lot's street edge, its alley edge and the axes a building stands on.

    Which edge fronts the street is asked of the geometry rather than of the vertex
    order, because the lot polygons do not wind consistently: on the first block the
    north tier listed its street edge first and the south tier listed its alley edge
    first.

    **The rear edge is the one nearest the alley STRIP, not the alley's centroid,
    and the second block is what proved the difference matters.** A block's alley
    centroid sits at the block's own centre, so for an END lot the side lot line
    running back toward that centre is very nearly as close to it as the lot's alley
    edge is: on `blk_randolph_dearborn` the two came out 38.93 m and 38.95 m apart —
    two centimetres over a thirty-nine metre lever — and two of that block's four end
    lots picked the side lot line. A building framed off a side line stands broadside
    to its own street and hangs over the neighbouring lot; the margin gate caught it
    at 1.44 m against a 1.5 m bound, which is a millimetre-scale complaint about a
    ninety-degree error. Measuring to the strip separates the same two edges by
    0.2 m and 26.3 m. `blk_randolph_wells` cleared the centroid tie by 1.3 m in 37 —
    a 3 % margin — so nothing it committed moves, but it was never more than the
    block's proportions away from the same failure.
    """
    poly = [tuple(p) for p in lot["polygon"]]
    edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
    rear = min(edges, key=lambda e: distance_to_edges(_mid(*e), alley))
    rm = _mid(*rear)
    front = max(edges, key=lambda e: math.dist(_mid(*e), rm))
    fm = _mid(*front)
    # Front and rear are the two block-face-parallel edges of the same lot, so they
    # are the same length to within the plat's own skew. A side lot line is twice
    # that on these blocks, which makes this a cheap structural check on the choice
    # above rather than a tolerance anybody has to tune.
    front_len, rear_len = math.dist(*front), math.dist(*rear)
    if abs(front_len - rear_len) > .20 * max(front_len, rear_len):
        raise SystemExit(f"lot frame is not square to the block: a {front_len:.1f} m "
                         f"frontage against a {rear_len:.1f} m rear edge — one of them "
                         f"is a side lot line")
    span = math.dist(fm, rm)
    if span <= 0:
        raise SystemExit("degenerate lot polygon")
    inward = ((rm[0] - fm[0]) / span, (rm[1] - fm[1]) / span)
    return {
        "front_mid": fm, "rear_mid": rm, "depth_m": span,
        "front_len_m": math.dist(*front), "rear_len_m": math.dist(*rear),
        "inward": inward, "polygon": poly,
    }


def place(edge_mid: tuple[float, float], inward: tuple[float, float],
          setback: float, lateral: float, width: float,
          depth: float) -> tuple[float, float, float]:
    """(local_e, local_n, bearing) for a building standing off one lot edge.

    `inward` points from the edge into the lot, so the facade faces out of it — the
    street for a frontage building, the alley for a yard one. The returned coordinate
    is the footprint's (0, 0) corner, which is what the GLB contract anchors on.

    T-0103: the bearing is therefore taken from the OUTWARD normal, `-inward`.
    `rotation_deg` is pinned by `docs/GLB-CONTRACT.md` as the facade bearing —
    the way the front looks, 0 = north — and this function read it off `inward`
    for twelve blocks, so every roof it stood turned its face into the middle of
    its own block. `tools/block_faces.py` has always taken the same angle off the
    face's outward normal, which is why the frontage rows on the same faces are
    right and these were not.
    """
    bearing = math.degrees(math.atan2(-inward[0], -inward[1])) % 360.0
    # The lateral axis along the edge: `inward` turned 90 degrees clockwise. It is
    # the ground direction a slot's `lateral_m` slides the building in, and it is
    # deliberately NOT re-derived from the corrected bearing — a lot's slot offsets
    # describe where the building stands, so turning the roof around must not also
    # move it to the other end of its lot.
    axis = (inward[1], -inward[0])
    cx = edge_mid[0] + inward[0] * (setback + depth / 2.0) + axis[0] * lateral
    cy = edge_mid[1] + inward[1] * (setback + depth / 2.0) + axis[1] * lateral
    theta = math.radians(bearing)
    cos, sin = math.cos(theta), math.sin(theta)
    return (cx - width * .5 * cos - depth * .5 * sin,
            cy + width * .5 * sin - depth * .5 * cos,
            round(bearing, 2))


def world_polygon(record: dict, datum: dict) -> list[tuple[float, float]]:
    phase = record["phases"][0]
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def point_in_polygon(pt: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    e, n = pt
    inside = False
    for i in range(len(poly)):
        e1, n1 = poly[i]
        e2, n2 = poly[(i + 1) % len(poly)]
        if (n1 > n) != (n2 > n):
            x = e1 + (n - n1) * (e2 - e1) / (n2 - n1)
            if x > e:
                inside = not inside
    return inside


def distance_to_edges(pt: tuple[float, float], poly: list[tuple[float, float]]) -> float:
    best = float("inf")
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        vx, vy = b[0] - a[0], b[1] - a[1]
        span = vx * vx + vy * vy
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((pt[0] - a[0]) * vx + (pt[1] - a[1]) * vy) / span))
        best = min(best, math.dist(pt, (a[0] + t * vx, a[1] + t * vy)))
    return best


def polygon_gap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    """Nearest approach between two convex-ish footprints; 0 if they overlap."""
    for pt in a:
        if point_in_polygon(pt, b):
            return 0.0
    for pt in b:
        if point_in_polygon(pt, a):
            return 0.0
    return min(min(distance_to_edges(pt, b) for pt in a),
               min(distance_to_edges(pt, a) for pt in b))


# --------------------------------------------------------------------------
# records
# --------------------------------------------------------------------------

def make_record(block: dict, slot: dict, lot_index: int | None, frame: dict | None,
                spec: dict, family: str, datum: dict, seq: int,
                face: dict | None = None) -> dict:
    sid = f"{PREFIX}{block['block_id'].removeprefix('blk_')}_{family.lower()}_{seq:02d}"
    if spec["band_ft"] is None:
        raise SystemExit(f"{family} has no numeric footprint band in the crosswalk")
    width, depth = dimensions_m(family, spec["band_ft"], sid)

    on_frontage = slot["stands_on"] == "frontage"
    fronts_alley = slot["stands_on"] == "alley"
    if on_frontage:
        # The coordinate is resolved in a second pass, by `place_frontage`, because a
        # run is a CHAIN: the unit at the end of the face is fixed by the block's own
        # corner and every unit west of it by the wall of the one before, so no unit's
        # position is known until its anchor's is. Everything else about the record —
        # its dimensions, its form, what it discloses — is known here.
        setback = float(block["frontage"]["setback_m"])
        lateral = 0.0
        local_e, local_n, bearing = 0.0, 0.0, round(face["bearing"], 2)
    else:
        edge_mid = frame["rear_mid"] if fronts_alley else frame["front_mid"]
        inward = ((-frame["inward"][0], -frame["inward"][1]) if fronts_alley
                  else frame["inward"])
        setback = float(slot["setback_m"])
        lateral = float(slot.get("lateral_m") or 0.0)
        local_e, local_n, bearing = place(edge_mid, inward, setback, lateral, width, depth)

    finish_key, paint = finish_for(sid)
    fallback = (spec["label"] or family).lower()
    function = FUNCTIONS.get(family) or canonical_function(fallback)
    label = LABELS.get(family) or fallback
    ancillary = slot["inventory_class"] == "ancillary"
    bounded = block["bounded_by"]
    faces = bounded["south"] if fronts_alley else slot["fronts"]
    # The division is the block's own, not this generator's. Both blocks before
    # `blk_randolph_clinton` were South Division, so a literal "South Division" here
    # read correctly on every record that existed and would have written the wrong
    # division into the visitor-facing location line of the first West one.
    where = (f"Anonymous reconstructed roof in the {block['district'].title()} Division "
             f"block bounded by "
             f"{bounded['north'].replace('_', ' ').title()}, "
             f"{bounded['east'].replace('_', ' ').title()}, "
             f"{bounded['south'].replace('_', ' ').title()} and "
             f"{bounded['west'].replace('_', ' ').title()}")
    if on_frontage:
        # T-0189. This clause read "one unit of the party-line RIVER row" until
        # 2026-08-27, which was written for T-0078's South Water run and was true of it.
        # It is the first line a visitor reads on the card, and by the time it was
        # caught it stood on 23 records across four faces — three houses on Washington
        # Street 400 m from the water among them, told they were part of a river row on
        # a street the sentence does not name. The row belongs to the face it stands on,
        # which is the face this same sentence has always named; `tools/block_faces.py`
        # calls it "a party-line STREET row" in its own docstring and that is the
        # vocabulary. Nothing moved: the phrase describes the placement, it does not
        # decide it.
        where += (f"; standing ON the {faces.replace('_', ' ').title()} Street frontage "
                  "itself, one unit of the party-line row along it")
    else:
        where += (f"; a yard building off the block alley behind the {slot['fronts'].title()} "
                  "Street frontage" if fronts_alley
                  else f"; standing back from the {faces.title()} Street frontage")

    anchor = slot.get("anchor") or {}
    # WHICH WALL THE ANCHOR ACTUALLY FIXES (T-0208). `place_frontage` solves for the
    # east wall in every case, but on a west-anchored run it solves for it FROM the
    # west wall — `corner: "west"` measures the margin off `along_min` and
    # `abut_east_of` reads a neighbour's east extent — so the wall the anchor fixes is
    # the west one and the east wall follows by the building's own width. The two are
    # the same wall on an east-anchored run, which is why the sentence read true for
    # twelve blocks before T-0079 opened the west end.
    anchored_wall = ("west" if anchor.get("corner") == "west" or anchor.get("abut_east_of")
                     else "east")
    described = (
        f"the {anchor.get('corner')} end of the run's own frontage, "
        f"{float(anchor.get('clear_m', LOT_MARGIN_M)):.1f} m clear of the side lot line at "
        f"that end" if "corner" in anchor
        else f"the west wall of {anchor['abut_west_of']}, which it shares a party line with"
        if anchor.get("abut_west_of")
        else f"the east wall of {anchor['abut_east_of']}, which it shares a party line with"
        if anchor.get("abut_east_of")
        else f"{float(anchor.get('clear_m', 0)):.1f} m west of {anchor.get('clear_west_of')}, "
        f"which stands proud of the platted line and so cannot share a wall with the row")
    position_note = FRONTAGE_NOTE.format(
        face=block["frontage"]["face"], block=block["block_id"],
        setback=f"{setback:.2f}", anchor=described, anchored_wall=anchored_wall,
        line_why=(LINE_WHY_ADOPTED if block["frontage"].get("adopts_face_line")
                  else LINE_WHY_MARGIN),
        street=slot["fronts"].replace("_", " ").title()) if on_frontage else (
        "Interpretive placement on a GENERATED lot, not a recovered parcel. The lot "
        "geometry is the K7 plat module's — this project has never read Thompson's "
        "numbering off a sheet, and the side lot lines and the alley are conjectural "
        f"even where the block face is not. The building stands {setback:.1f} m back "
        f"from its {'alley' if fronts_alley else 'street'} edge, which is a typology "
        "for the period and not a measurement of this lot. The whole footprint — not "
        "its centre — is tested against the platted street corridors, against its own "
        "lot lines and against every other footprint in the dataset, so no invented "
        "building of this parcel stands in the roadway; clearing the roadway is not "
        "the same as standing on a recovered lot.")

    reconstruction = {
        "status": "inferred_anonymous", "family": family, "district": block["district"],
        "inventory_class": slot["inventory_class"],
        "programme_phase": block["programme_phase"], "source_id": SOURCE_ID,
        "block_id": block["block_id"], "lot_index": lot_index,
        "stands_on": slot["stands_on"], "fronts": slot["fronts"],
        "sequence": seq, "finish_key": finish_key,
        "roof_condition": ("fresh", "darkened", "patched", "weathered")[seq % 4],
        "age_state": ("new", "recent", "established", "older_frontier")[seq % 4],
    }
    if on_frontage:
        # A unit of a row holds no lot: it stands across the run's frontage, and which
        # of the run's conjectural side lines fall under it is not a claim this parcel
        # makes. The lots the run was DEALT are named on the block's frontage entry,
        # where the ledger can count them, rather than shared out one per unit here.
        del reconstruction["lot_index"]
        reconstruction["frontage"] = {
            "block": block["block_id"], "face": block["frontage"]["face"],
            "setback_m": setback,
            "abuts": anchor.get("abut_west_of") or anchor.get("abut_east_of"),
            "why": block["frontage"]["why"],
        }
    mapping = (" H-family house massing currently resolves through the frame dwelling "
               "archetype; no larger house generator is implemented."
               if family.startswith("H") else "")
    return {
        "id": sid,
        "name": f"Reconstructed {family} {label} #{seq:02d}",
        "archetype": spec["archetype"],
        "phases": [{
            "id": PHASE_ID,
            "documented_range": {
                "from": "1835-01-01", "to": "1835-12-31", "confidence": "reconstructed",
                "note": "Anonymous count-unit toward the July 1835 665-roof programme. No evidence establishes that this particular building existed, and no source names an occupant of this lot."
            },
            "position": {
                "utm_e": round(float(datum["origin_utm_e"]) + local_e, 3),
                "utm_n": round(float(datum["origin_utm_n"]) + local_n, 3),
                "rotation_deg": bearing, "symbolic_location": where,
                "confidence": "reconstructed", "note": position_note,
                "derivation": {"method": "not_derivable", "reason": "No parcel-by-parcel July 1835 roof register survives in the supplied evidence, and no lot in this block is numbered."}
            },
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"A {width:.2f} × {depth:.2f} m rectangle sampled deterministically inside the {family} family's authored footprint band; no individual dimensions are documented."
            },
            "form": form_for(family, spec, sid, width, depth, paint),
            "change_note": "Reconstructed anonymous July 1835 block infill; a better-evidenced named roof substitutes for a compatible count-unit rather than increasing the 665-roof total."
        }],
        "function": invented(function, f"Assigned from the {family} family to satisfy the block's scheduled mix; no occupant or individual use is known."),
        **({"occupants": OCCUPANCY[sid]} if sid in OCCUPANCY else {}),
        "reconstruction": reconstruction,
        **({"_frontage": anchor} if on_frontage else {}),
        "research_note": ("RECONSTRUCTED / GENERATED, NOT AN ATTESTED NAMED BUILDING. The "
                          "block, its scheduled roof count and its family mix follow the "
                          "665-roof programme; exact presence, lot, position, footprint, "
                          "finish and instance-level form are interpretive." + mapping),
        "review_required": False,
    }


def build_block(block: dict, table: dict[str, dict], lots_by_id: dict[str, dict],
                datum: dict, sibling_lots: frozenset[int] = frozenset()) -> list[dict]:
    grid = lots_by_id.get(block["block_id"])
    if grid is None:
        raise SystemExit(f"{block['block_id']} is not a block of the committed plat grid")
    streets = street_traffic()
    alley = [tuple(p) for p in grid["alley_local_enu_m"]]
    frames = [lot_frame(lot, alley) for lot in grid["lots"]]

    frontage = block.get("frontage")
    face = face_frame(grid, frontage["face"]) if frontage else None
    strip = frontage_strip(block, grid, face) if frontage else None

    # T-0105. A BLOCK MAY BE DEALT TWICE, and the second deal is a second entry.
    # Until the core density standard raised the ceiling (T-0079) a block was dealt
    # once, built once and finished, so a recipe entry could number its records from
    # one and never meet another entry's. The standard retired that: a block built to
    # the old ceiling now stands BELOW the new one, and the roofs it is dealt next
    # arrive years of commits after the ones already standing on it. Rewriting the
    # first entry to cover both deals would restate a schedule that was true in
    # August under numbers that were not, so the second deal is its own entry against
    # its own headroom — and `seq_start` is the one thing that has to move with it,
    # because the record id carries the sequence and two entries numbering from one
    # would collide on the first slot that shared a family. Everything else already
    # works across entries: occupancy, separation and the roadway are all measured
    # against the committed dataset rather than against this entry's own slots.
    records = []
    for seq, slot in enumerate(block["slots"], start=int(block.get("seq_start", 1))):
        on_frontage = slot["stands_on"] == "frontage"
        if on_frontage and frontage is None:
            raise SystemExit(f"{block['block_id']}: a slot stands on the frontage, but "
                             f"the block names no frontage for the run to stand on")
        lot_index = None if on_frontage else int(slot["lot"])
        if lot_index is not None and not 0 <= lot_index < len(frames):
            raise SystemExit(f"{block['block_id']} has no lot {lot_index}")
        family = slot["family"]
        if family in REFUSED_FAMILIES:
            raise SystemExit(
                f"{block['block_id']}: this generator refuses to mass {family} — "
                f"{REFUSED_FAMILIES[family]} Defer the slot in the recipe's `deferred` "
                f"list with the reason, or reconcile it to a named record first.")
        spec = table.get(family)
        if spec is None:
            raise SystemExit(f"family {family} is not in the crosswalk")
        if not on_frontage:
            check_non_dwelling_slot(block, slot, family, streets)
        records.append(make_record(
            block, slot, lot_index, None if on_frontage else frames[lot_index], spec,
            family, datum, seq, face))
    if frontage:
        place_frontage(block, face, strip, records, datum)
    check_block(block, grid, frames, records, datum, face, strip, sibling_lots)
    return records


# --------------------------------------------------------------------------
# where a NON-DWELLING stands (T-0024, ROADMAP K32)
# --------------------------------------------------------------------------
#
# The face rule ranks DWELLINGS: the best take the better street, the meanest take the
# back one. T-A15 was dealt the first store any block parcel had had to place, found the
# rule said nothing about it, and EXTENDED the ranking to cover it — commerce above the
# better dwelling — putting the C2 on Randolph and sending a D6 to the back street. That
# extension was an invention about 1835 commerce made by an agent and was opened as K32
# for the next block dealt a commercial family to follow or refute.
#
# SETTLED HERE ON READING 2 OF THE THREE THE ROADMAP OFFERED: the face rule ranks
# dwellings only, and a non-dwelling is placed by its own FUNCTION. What makes this more
# than a preference is that the function is READ OFF THE DOCUMENTED RECORD of the family's
# own letter rather than reasoned about — `tools/measure_face_rule.py` takes the reading
# and `tools/check.sh` runs it. As committed today, on the 48 documented buildings the
# reconciliation credits a non-dwelling family:
#
#   C  stores        15 records — 10 principal, 5 ordinary, 0 light
#   F  warehouses     9 records —  9 principal, 0 ordinary, 0 light
#   W  workshops      7 records —  2 principal, 5 ordinary, 0 light
#   T  lodging        8 records —  3 principal, 4 ordinary, 1 light
#   I  institutions   9 records —  1 principal, 4 ordinary, 4 light, and refused to a
#                     block parcel BY NAME above, so no frontage rule ever reaches them
#
# NOT ONE documented STORE, WAREHOUSE OR WORKSHOP stands on a LIGHT street — a zero across
# 31 buildings, on the three letters a block parcel may actually be dealt. T's one is the
# Steamboat Hotel, which stands 287 m from the State Street centreline and does not front
# it; State is simply the nearest committed line in a division with almost no street
# control. The two rules that follow are the whole of the clause:
#
#   1. A non-dwelling takes the block's BETTER face, by the traffic class the committed
#      street hierarchy authors in data/streets/1835.json. It may never take a light one:
#      the record has no instance of it, and an invented one would be the first.
#   2. A COMMERCIAL roof stands ON the street line rather than back at a dwelling's
#      typology setback. Thirteen of the fourteen documented stores do (the fourteenth is
#      out at Wolf Point, off the platted grid), and a store's claim on frontage is
#      functional — T-A15's own words, "the only one of the six roofs whose purpose
#      requires that a stranger can find it". The line is the closest one the plat
#      module's own margin allows, LOT_MARGIN_M, which is the same line the party-line
#      runs already stand on across this town.
#
# What this REFUSES is reading 1, the ranking T-A15 extended. On `blk_randolph_clark` the
# two readings agree — the store takes Randolph either way — so nothing that stands moves
# on account of the ranking, and that agreement is why the question could be settled at
# all rather than being settled on the block where it first bites.
#
# BOTH LETTER SETS COME FROM THE PLACEMENT POLICY SINCE T-1195. They were typed here, and
# under other names in measure_face_rule and measure_frontage_fabric, and three copies of
# one reading is how a reading drifts. `data/reconstruction/1835_placement_policy.json`
# holds them with the clause each one serves; its assertion 5 reads these two lines.
NON_DWELLING_LETTERS = "".join(constant("non_dwelling_letters"))

# The letters the documented record puts a zero on for light streets, re-derivable with
# `tools/measure_face_rule.py`: stores 0 of 15, warehouses 0 of 9, workshops 0 of 7. The
# same three the policy calls the trade letters.
LIGHT_STREET_ZERO = "".join(constant("trade_letters"))

# The traffic classes data/streets/1835.json authors, worst to best.
TRAFFIC_RANK = {"light": 0, "ordinary": 1, "principal": 2}


def street_traffic() -> dict[str, str]:
    return {s["id"]: s.get("traffic")
            for s in load(DATA / "streets" / "1835.json")["streets"]}


def check_non_dwelling_slot(block: dict, slot: dict, family: str,
                            streets: dict[str, str]) -> None:
    """The two clauses above, on a slot standing on a lot. See NON_DWELLING_LETTERS."""
    if family[0] not in NON_DWELLING_LETTERS or slot["inventory_class"] == "ancillary":
        return
    fronts = slot["fronts"]
    klass = streets.get(fronts)
    if klass is None:
        raise SystemExit(f"{block['block_id']}: slot {family} fronts {fronts!r}, which "
                         f"the committed street hierarchy does not grade")
    # The hard refusal is on the three letters the record puts a ZERO on, not on all five:
    # a rule wider than its own evidence is the thing this clause exists to stop.
    if klass == "light" and family[0] in LIGHT_STREET_ZERO:
        raise SystemExit(
            f"{block['block_id']}: a {family} roof may not front {fronts!r}, a light "
            f"street. Not one of the 31 documented stores, warehouses and workshops in "
            f"this town stands on one, so this would be the first — see the clause above "
            f"and tools/measure_face_rule.py")
    best = max((TRAFFIC_RANK.get(streets.get(s), -1), s)
               for s in block["bounded_by"].values())
    if TRAFFIC_RANK.get(klass, -1) < best[0]:
        raise SystemExit(
            f"{block['block_id']}: a {family} roof fronts {fronts!r} ({klass}) while the "
            f"block is bounded by {best[1]!r} ({streets.get(best[1])}). A non-dwelling "
            f"takes the block's better face (T-0024)")
    if family[0] == "C" and float(slot["setback_m"]) > LOT_MARGIN_M + 0.005:
        raise SystemExit(
            f"{block['block_id']}: a {family} roof is authored {slot['setback_m']} m back "
            f"from its lot line. A commercial roof stands ON the street line, at the "
            f"{LOT_MARGIN_M} m the plat module's margin allows (T-0024)")


# --------------------------------------------------------------------------
# the gates, run before a single file is written
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# the party-line frontage (T-0078)
# --------------------------------------------------------------------------
#
# The placements above are one principal roof per lot, centred on its own lot at a
# typology setback with a lateral nudge. That is a DISTRIBUTION of roofs across a
# block, and it is the right shape for a residential back street. It is the wrong
# shape for the town's business front: the owner's reference for South Water Street
# in 1834 shows the south bank as a CONTINUOUS working row — one-storey log and frame
# buildings shoulder to shoulder facing the river, the street between them and the
# grassy bank — and this row rendered as detached cottages seven metres back from the
# frontage, each looking away from the river at the block's interior.
#
# So a slot may say instead that it stands ON the block face, and it then takes three
# things from the committed plat rather than from the recipe: the line it fronts, the
# bearing of that line, and where along it its east wall lands. Nothing here authors a
# coordinate. A run is anchored either on the east end of its own frontage or on the
# wall of a building already standing on the face, and it packs west from there.
#
# What the run gives up is the one-roof-per-lot geometry, and the trade is stated
# rather than assumed: the side lot lines inside a run are conjectural — every record
# this generator writes has always said so — while the block face is not. A row is a
# claim about the FACE. The lots it was dealt are named on the block's `frontage`
# entry so the ledger can still count them, and the strip's OUTER lines keep the same
# margin every other roof here keeps.


def frontage_strip(block: dict, grid: dict, face: dict) -> dict:
    """The ground one run may stand on: its own lots of one block face, as one strip.

    Measured, not authored. The lots are projected onto the face; the strip runs from
    the west line of the westmost to the east line of the eastmost, and every lot in
    between has to adjoin its neighbour — a run is one stretch of frontage, and lots
    with somebody else's roof between them are two runs and have to say so.
    """
    frontage = block["frontage"]
    lots = frontage["lots"]
    if not lots:
        raise SystemExit(f"{block['block_id']}: a frontage run stands on no lots")
    spans = []
    for index in lots:
        if not 0 <= index < len(grid["lots"]):
            raise SystemExit(f"{block['block_id']} has no lot {index} for its frontage run")
        corners = [face_project(face, tuple(p)) for p in grid["lots"][index]["polygon"]]
        along = (min(c[0] for c in corners), max(c[0] for c in corners))
        offs = (min(c[1] for c in corners), max(c[1] for c in corners))
        if offs[1] < -0.5:
            raise SystemExit(f"{block['block_id']}: lot {index} does not reach the "
                             f"{frontage['face']} face, so no run of that face can be "
                             f"dealt its roof")
        spans.append((along, offs, index))
    spans.sort()
    for (a, _, i), (b, _, j) in zip(spans, spans[1:]):
        if b[0] > a[1] + 0.5:
            raise SystemExit(f"{block['block_id']}: lots {i} and {j} do not adjoin on "
                             f"the {frontage['face']} face — a run is one continuous "
                             f"stretch of frontage, not a list of lots")
    return {"along_min": spans[0][0][0], "along_max": spans[-1][0][1],
            "off_min": min(s[1][0] for s in spans), "off_max": max(s[1][1] for s in spans),
            "lots": [s[2] for s in spans]}


def place_frontage(block: dict, face: dict, strip: dict, records: list[dict],
                   datum: dict) -> None:
    """Stand every slot that declared the frontage on it, in run order.

    Anchors resolve in passes because a run is a chain: the unit at the east end is
    fixed by the end of the run's own frontage, and each unit west of it by the wall
    of the one before. An anchor may also name a building this parcel did not write,
    which is how a run butts onto a store that is already standing on the face.
    """
    pending = {r["id"]: r for r in records if r.get("_frontage")}
    if not pending:
        return
    mine = {r["id"] for r in records}
    committed = dict(footprints(datum, exclude=mine))
    setback = float(block["frontage"]["setback_m"])
    resolved: dict[str, list[tuple[float, float]]] = {}

    while pending:
        progressed = False
        for sid, record in list(pending.items()):
            anchor = record["_frontage"]
            phase = record["phases"][0]
            polygon = phase["footprint"]["polygon"]
            width = max(p[0] for p in polygon) - min(p[0] for p in polygon)
            depth = max(p[1] for p in polygon) - min(p[1] for p in polygon)
            if "corner" in anchor:
                # T-0079 opened the WEST end. A run anchored east packs back toward the
                # block corner and stops wherever the roofs it was dealt run out, so the
                # corner lot's corner is the one piece of frontage a row can never reach —
                # and a corner built to the corner is exactly what the street plates show.
                # A west-anchored run starts against the corner margin instead and chains
                # east with `abut_east_of`, which is the same party line read the other way.
                if anchor["corner"] not in ("east", "west"):
                    raise SystemExit(f"{sid}: a run anchors on the east or the west end "
                                     f"of its face, not {anchor['corner']!r}")
                if anchor["corner"] == "east":
                    east = strip["along_max"] - float(anchor.get("clear_m", LOT_MARGIN_M))
                else:
                    east = strip["along_min"] + float(anchor.get("clear_m", LOT_MARGIN_M)) + width
            else:
                # `abut_west_of` shares a party line with the named building and stands west
                # of it; `abut_east_of` is the same wall from the other side, for a run that
                # chains away from the west corner. `clear_west_of` stands a stated distance
                # west instead, which is how a run breaks around a documented store that
                # stands PROUD of the platted line. Several of the South Water stores do:
                # they were placed from typed coordinates before the plat module existed and
                # their walls sit in the corridor, so a row on the platted line cannot share
                # a wall with them and the three-metre separation rule — not this recipe —
                # is what fixes the size of the break.
                target = (anchor.get("abut_west_of") or anchor.get("abut_east_of")
                          or anchor.get("clear_west_of"))
                if target is None:
                    raise SystemExit(f"{sid}: a frontage slot anchors on an end of the "
                                     f"run, abuts a named building or stands clear west "
                                     f"of one")
                neighbour = resolved.get(target) or committed.get(target)
                if neighbour is None:
                    if target in mine:
                        continue  # its own anchor has not been placed yet
                    raise SystemExit(f"{sid}: nothing in the dataset is called {target}")
                span = face_extent(face, neighbour)
                east = span[1] + width if anchor.get("abut_east_of") else span[0]
                if "clear_west_of" in anchor:
                    east -= float(anchor["clear_m"])
            # The footprint's (0, 0) corner, which is what the GLB contract anchors on:
            # walk back from the east wall along the face, then in from the face line by
            # the setback and the building's own depth.
            #
            # WHICH WAY "BACK" IS DEPENDS ON THE FACE, and it did not have to until this
            # run (T-0143). `rotation_deg` is the facade bearing, so the footprint's own
            # +u axis is the outward normal turned a quarter turn — and that runs WITH
            # the face's `along` on a north or west face and AGAINST it on a south or
            # east one. Twelve blocks of frontage runs stand on north faces, where the
            # two agree, so placing the corner at `east - width` was right on every row
            # this generator had ever built. The first run on a south face put each unit
            # a whole width west of the party wall it declared, which `check_frontage`
            # refused: the assertion is a measurement of the geometry, which is why it
            # could catch a defect in the placement that wrote it.
            position = phase["position"]
            theta = math.radians(float(position["rotation_deg"]))
            cos, sin = math.cos(theta), math.sin(theta)
            u_along = cos * face["along"][0] - sin * face["along"][1]
            if abs(u_along) < .99:
                raise SystemExit(f"{sid}: the facade bearing is {position['rotation_deg']} "
                                 f"deg, which does not lie along the face it fronts")
            along_0 = east - width if u_along > 0 else east
            base = (face["origin"][0] + face["along"][0] * along_0
                    + face["outward"][0] * (-setback - depth),
                    face["origin"][1] + face["along"][1] * along_0
                    + face["outward"][1] * (-setback - depth))
            local_e, local_n = round(base[0], 3), round(base[1], 3)
            position["utm_e"] = round(float(datum["origin_utm_e"]) + local_e, 3)
            position["utm_n"] = round(float(datum["origin_utm_n"]) + local_n, 3)
            resolved[sid] = [(local_e + u * cos + v * sin, local_n - u * sin + v * cos)
                             for u, v in polygon]
            del pending[sid]
            progressed = True
        if not progressed:
            raise SystemExit("a frontage run anchors on itself: " + ", ".join(sorted(pending)))

    for record in records:
        record.pop("_frontage", None)


def adopted_line(block: dict, face: dict, adopts: list[str], records: list[dict],
                 datum: dict) -> float:
    """The line a face's committed frontage already stands on, measured (T-0104).

    Nothing here is authored: the caller names records this parcel did not write, and
    the answer is their front walls projected onto the face this run stands on. Naming
    them rather than sweeping the face is deliberate — the sweep is what
    `tools/measure_street_line.py` does over the whole town, and a generator that
    silently adopted whatever happened to be near its face could be moved by a
    building nobody meant to put on the line.
    """
    mine = {r["id"] for r in records}
    committed = dict(footprints(datum, exclude=mine))
    walls = {}
    for name in adopts:
        polygon = committed.get(name)
        if polygon is None:
            raise SystemExit(f"{block['block_id']}: the run adopts the line of {name}, "
                             f"which is not a committed building this parcel can see")
        walls[name] = -max(face_project(face, p)[1] for p in polygon)
    if not walls:
        raise SystemExit(f"{block['block_id']}: `adopts_face_line` names no records, so "
                         f"there is no line to adopt")
    if max(walls.values()) - min(walls.values()) > 0.005:
        raise SystemExit(f"{block['block_id']}: the records the run adopts do not stand "
                         f"on one line — " + ", ".join(f"{k} at {v:.3f} m"
                                                       for k, v in sorted(walls.items())))
    return round(math.fsum(walls.values()) / len(walls), 3)


def check_frontage(block: dict, face: dict, strip: dict, records: list[dict],
                   datum: dict) -> None:
    """A row is a row: on one line, in order, and touching.

    Three assertions, because each of the three is a way the row stops being one and
    none of them is visible in a diff of coordinates. The front walls sit on one line
    to the millimetre or the street wall steps; a run's units are in the order its
    anchors deal them or "west of" means nothing; and a party line is a shared wall, so
    a gap inside a run is a defect while the gap between a run and a documented store
    further along the face is the frontage the parcel was not dealt.
    """
    row = [r for r in records if r["reconstruction"].get("frontage")]
    if not row:
        return
    frontage = block["frontage"]
    setback = {r["reconstruction"]["frontage"]["setback_m"] for r in row}
    if len(setback) != 1:
        raise SystemExit(f"{block['block_id']}: the {frontage['face']} frontage is set "
                         f"back by {sorted(setback)} m — a street wall is one line")
    stated = float(next(iter(setback)))
    adopts = frontage.get("adopts_face_line")
    if adopts:
        # T-0104. A FACE THAT IS ALREADY BUILT HAS A STREET LINE, and it outranks the
        # margin: a street wall is one wall, and a run that stands 0.70 m behind the
        # buildings it joins puts a jog in it. So a recipe may name the committed
        # records whose line it adopts, and then the setback is not authored at all —
        # it is MEASURED off them here, and a recipe that states any other number
        # fails. The exemption is as narrow as L141's party-wall one: it reaches the
        # STREET line only, it needs records to point at, and the side lines below
        # keep the full margin.
        line = adopted_line(block, face, adopts, records, datum)
        if abs(line - stated) > 0.005:
            raise SystemExit(f"{block['block_id']}: the run states a {stated} m setback "
                             f"and adopts the line of {', '.join(sorted(adopts))}, whose "
                             f"front walls stand {line:.3f} m off the "
                             f"{frontage['face']} face")
    elif stated < LOT_MARGIN_M - 1e-6:
        raise SystemExit(f"{block['block_id']}: a run set back {stated} m stands inside "
                         f"the {LOT_MARGIN_M} m margin the plat module keeps off a lot "
                         f"line. The row crosses the side lines between its own units, "
                         f"which are conjectural; it does not cross the street line. A "
                         f"face that is already built may state `adopts_face_line` and "
                         f"take the line of the records named there instead")
    spans = {}
    for record in row:
        world = world_polygon(record, datum)
        offs = [face_project(face, p)[1] for p in world]
        if abs(max(offs) + stated) > 0.005:
            raise SystemExit(f"{record['id']} fronts {max(offs):.3f} m off the "
                             f"{frontage['face']} face of {block['block_id']}, not its "
                             f"stated setback")
        spans[record["id"]] = face_extent(face, world)
    for record in row:
        target = record["reconstruction"]["frontage"].get("abuts")
        if not target or target not in spans:
            continue
        # A shared wall is one wall from either side: the record is west of its neighbour
        # or east of it, and the party line is the smaller of the two readings. Taking the
        # minimum rather than branching on the recipe's key means the assertion is a
        # measurement of the geometry and cannot be satisfied by relabelling the anchor.
        gap = min(abs(spans[target][0] - spans[record["id"]][1]),
                  abs(spans[record["id"]][0] - spans[target][1]))
        if gap > 0.005:
            raise SystemExit(f"{record['id']} stands {gap:.3f} m from the party line it "
                             f"shares with {target}")
    # the run inside its own frontage, clear of the lines it did not earn
    for record in row:
        for point in world_polygon(record, datum):
            along, off = face_project(face, point)
            # 5 mm, the tolerance the setback line above uses and for the same reason:
            # a placement is rounded to the millimetre before it is written.
            if not (strip["along_min"] + LOT_MARGIN_M - .005 <= along
                    <= strip["along_max"] - LOT_MARGIN_M + .005):
                raise SystemExit(f"{record['id']} reaches past the end of its own "
                                 f"frontage on {block['block_id']}, inside the "
                                 f"{LOT_MARGIN_M} m margin of a side line the run does "
                                 f"not stand across")
            # The street-side bound is the run's OWN line rather than the lot margin:
            # where the run adopts a built face (T-0104) that line is the margin's
            # replacement, and where it does not the two are the same number.
            if not (strip["off_min"] + LOT_MARGIN_M - .005 <= off <= -stated + .005):
                raise SystemExit(f"{record['id']} stands {off:.2f} m off the "
                                 f"{frontage['face']} face, outside the run's own ground")


def check_block(block: dict, grid: dict, frames: list[dict], records: list[dict],
                datum: dict, face: dict | None = None,
                strip: dict | None = None,
                sibling_lots: frozenset[int] = frozenset()) -> None:
    from plat_corridors import corridors, intrusion  # noqa: PLC0415
    from heightfield import Heightfield  # noqa: PLC0415

    mine = [(r["id"], world_polygon(r, datum)) for r in records]

    # the schedule the recipe claims against
    counts = Counter(r["reconstruction"]["family"] for r in records)
    if dict(counts) != block["families"]:
        raise SystemExit(f"{block['block_id']}: the slots deal {dict(counts)}, the "
                         f"claimed schedule mix is {block['families']}")
    principal = sum(1 for r in records
                    if r["reconstruction"]["inventory_class"] == "principal_functional")
    claimed = block["drawn_from_schedule"]
    if (principal, len(records) - principal) != (claimed["principal"], claimed["ancillary"]):
        raise SystemExit(f"{block['block_id']}: {principal} principal / "
                         f"{len(records) - principal} ancillary against a claim of "
                         f"{claimed['principal']} / {claimed['ancillary']}")
    if len(records) > claimed["headroom"]:
        raise SystemExit(f"{block['block_id']}: {len(records)} roofs exceed the block's "
                         f"{claimed['headroom']} of headroom")

    dealt_p = claimed.get("dealt_principal", claimed["principal"])
    dealt_a = claimed.get("dealt_ancillary", claimed["ancillary"])
    # T-0834. THE SCHEDULE'S SIZING IS CONDITIONAL, AND THE CONDITION IS GATED HERE.
    # `reconcile_665.block_rooms` sizes a block's principal room in party-line units —
    # ROW_UNITS_PER_LOT of them per free lot — and this generator places by whole LOTS:
    # an ordinary principal roof stands ON a free lot and one lot never carries two, so
    # the party-line density is reachable only along a frontage run the recipe NAMES.
    # A parcel that gives its run k of its free lots can stand
    #
    #     (free_lots - k - 1) + ROW_UNITS_PER_LOT * k
    #
    # principal roofs, and `principal_room` is that at k = free_lots - 1. Between those
    # two numbers sat a gap nothing measured: the programme said roofs were dealt, the
    # ground said they were not placed, and the difference went into the district
    # balance unremarked — `blk_south_water_clark`'s second deal (T-0431) is where it
    # was found, and `blk_south_water_franklin`'s (T-0430) is where the same two shapes
    # agreed by accident. The schedule now states the condition per unit as
    # `row_lots_required`; this refuses a parcel that does not meet it, so a deal too
    # big for its ground fails at the parcel that would have quietly shed it.
    #
    # The four phase-3 recipes written before ROADMAP T-A6 carry no `free_lots` — the
    # schedule did not size in lots yet — so there is nothing to hold them to and they
    # are passed. That is a gap in the OLD recipes, not a relaxation of the rule.
    free_lots = claimed.get("free_lots")
    if free_lots is not None:
        ceiling = max(0, free_lots - 1)
        row_lots = len((block.get("frontage") or {}).get("lots") or ())
        if row_lots > ceiling:
            raise SystemExit(f"{block['block_id']}: the frontage run is dealt {row_lots} "
                             f"of the block's {free_lots} free lot(s), which leaves it no "
                             f"open lot. A run's lots are free lots like any other and "
                             f"the block keeps one open (T-0834)")
        can_stand = ceiling + row_lots * (ROW_UNITS_PER_LOT - 1)
        if dealt_p > can_stand:
            raise SystemExit(f"{block['block_id']}: the schedule dealt {dealt_p} "
                             f"principal roof(s) and this parcel has ground for "
                             f"{can_stand} — {ceiling} on its free lots, less the one it "
                             f"keeps open, plus {row_lots * (ROW_UNITS_PER_LOT - 1)} the "
                             f"frontage run's {row_lots} lot(s) add at "
                             f"{ROW_UNITS_PER_LOT} units to the lot. Name the run more "
                             f"lots or take a smaller deal; a roof with nowhere to stand "
                             f"is not deferrable, because no family is refused (T-0834)")

    # A parcel may build FEWER roofs than the schedule dealt it, but only by naming
    # each missing slot and the refusal it rests on. Without this, "the block carries
    # nine roofs" and "the schedule dealt it ten" are two numbers in two files and
    # nothing makes them meet — which is how a slot gets dropped for being awkward
    # rather than for being wrong, and the ledger reads as though it were never dealt.
    deferred = block.get("deferred") or []
    shortfall = (dealt_p - claimed["principal"]) + (dealt_a - claimed["ancillary"])
    if shortfall < 0:
        raise SystemExit(f"{block['block_id']}: the parcel claims to build more roofs "
                         f"than the schedule dealt it")
    if shortfall != len(deferred):
        raise SystemExit(f"{block['block_id']}: the schedule dealt {dealt_p + dealt_a} "
                         f"roofs and the parcel builds {len(records)}, but "
                         f"{len(deferred)} slot(s) are deferred — every roof dealt and "
                         f"not built must be named in `deferred` with its reason")
    for entry in deferred:
        family = entry.get("family")
        if family not in REFUSED_FAMILIES:
            raise SystemExit(f"{block['block_id']}: {family} is deferred, but this "
                             f"generator does not refuse {family} by name. A slot may "
                             f"only be deferred for a refusal the code states; "
                             f"anything else is a roof quietly dropped")
        if family in block["families"]:
            raise SystemExit(f"{block['block_id']}: {family} is both built and deferred")
        if len((entry.get("why") or "").split()) < 40:
            raise SystemExit(f"{block['block_id']}: the deferral of {family} does not "
                             f"state its reasoning. A refusal this project cannot read "
                             f"back is indistinguishable from an omission")

    # one principal roof per lot, and no lot carries two. A frontage run holds no lot
    # per unit — it stands across its own stretch of the face — so it counts against the
    # lots the recipe named for it, and the count is gated: a run may not carry more
    # roofs than the lots it was dealt, which is the same ceiling stated the same way.
    # T-0103. EVERY ROOF LOOKS AT THE THING IT FRONTS, and the block's own faces are
    # asked rather than the lot's. `place()` derived the facade bearing from the lot
    # frame for twelve blocks and derived it backwards, so 78 roofs stood with their
    # doors and windows turned into the middle of their own block — and nothing here
    # noticed, because every gate this generator carries measures WHERE a building
    # stands and none of them measured which way it looks. This one does, off
    # `block_faces.py`'s outward normal, which is a different derivation from the lot
    # polygon that `place()` reads: a 180-degree error cannot be right in both.
    # The tolerance is the plat's own skew — a lot's front edge is not exactly
    # parallel to its block face, and the committed grid runs up to 2.6 degrees out
    # on the West Division blocks — so five degrees is loose enough for the ground
    # and nowhere near loose enough to admit a flip.
    for record in records:
        recon = record["reconstruction"]
        street = recon["fronts"]
        compass = [k for k, v in grid["bounded_by"].items() if v == street]
        if len(compass) != 1:
            raise SystemExit(f"{record['id']} fronts {street!r}, which is not exactly "
                             f"one face of {block['block_id']}")
        want = face_frame(grid, compass[0])["bearing"]
        if recon["stands_on"] == "alley":
            want = (want + 180.0) % 360.0   # a yard building looks at the alley behind it
        got = float(record["phases"][0]["position"]["rotation_deg"])
        off = abs((got - want + 180.0) % 360.0 - 180.0)
        if off > 5.0:
            raise SystemExit(f"{record['id']} stands on the {street} face and looks "
                             f"{got:.2f}deg, {off:.1f}deg off the {want:.2f}deg its "
                             f"face looks. rotation_deg is the FACADE bearing "
                             f"(docs/GLB-CONTRACT.md), so this roof fronts the wrong "
                             f"way")

    frontage = block.get("frontage")
    row = [r for r in records if r["reconstruction"].get("frontage")]
    if frontage and not row:
        raise SystemExit(f"{block['block_id']}: the block names a frontage run and no "
                         f"slot stands on it")
    if row and not frontage:
        raise SystemExit(f"{block['block_id']}: a roof stands on a frontage the block "
                         f"does not name")
    used = [r["reconstruction"]["lot_index"] for r in records
            if r["reconstruction"]["inventory_class"] == "principal_functional"
            and "lot_index" in r["reconstruction"]]
    if frontage:
        # T-0079, the core density standard. This gate used to read `!=`: a run carried
        # exactly one roof per lot it was dealt, which made a row exactly as dense as the
        # lot grid and left "a row is denser than the lot grid" a sentence with no
        # arithmetic behind it. The ceiling is now the one the schedule counts in —
        # `ROW_UNITS_PER_LOT` units per lot of frontage, measured at the smallest lot on
        # the committed grid — and the run's OWN strip, which `check_frontage` already
        # holds it inside with the plat's margin at each end, is what makes it physical.
        # Two ceilings, and the tighter one binds; neither of them is the conjectural
        # side lot line, which is the whole point.
        if len(row) > ROW_UNITS_PER_LOT * len(frontage["lots"]):
            raise SystemExit(f"{block['block_id']}: the run carries {len(row)} roofs on "
                             f"{len(frontage['lots'])} lot(s) of frontage, past the "
                             f"{ROW_UNITS_PER_LOT} units a lot of this grid holds at the "
                             f"row's own measured spacing. A row is denser than the lot "
                             f"grid, not unbounded by it")
        if any(r["reconstruction"]["inventory_class"] != "principal_functional"
               for r in row):
            raise SystemExit(f"{block['block_id']}: a yard building cannot stand in the "
                             f"street row — an ancillary roof serves the lot behind it")
        used += list(frontage["lots"])
    if len(set(used)) != len(used):
        raise SystemExit(f"{block['block_id']}: two principal roofs on one lot")

    # every other placed footprint in the dataset, in this block's local frame — read
    # by the same module that answers the occupancy question below, so the separation
    # gate and the occupancy gate cannot end up looking at two different towns
    mine_ids = {sid for sid, _ in mine}
    others = footprints(datum, exclude=mine_ids)

    # --- the lots this block ALREADY carries -------------------------------
    #
    # The check above asks whether this parcel put two roofs on one lot. It has
    # never been able to ask the question that matters on an occupied block —
    # whether the lot was free in the first place — because it reads only the
    # records this parcel builds, and the two blocks before this one were empty.
    # `blk_randolph_clinton` is the first block off the schedule that was not:
    # three roofs from the pre-plat West parcel stand on three of its eight lots,
    # placed from typed coordinates before the plat module existed, so nothing in
    # the dataset says which lot they are on. A free lot and a lot with somebody
    # else's house on it looked identical here, and the three-metre separation
    # gate does not close the difference: two principal roofs can stand twelve
    # metres apart on one twenty-five-metre lot and pass every test in this file.
    #
    # A lot is occupied by the footprint standing on it, so occupancy is DERIVED
    # from the committed records rather than authored in the recipe — a recipe
    # that had to be told which lots were taken would be a second opinion about
    # the same ground, which is the defect the plat module exists to retire.
    #
    # T-A7: it is derived by the footprint's OVERLAP with the lot, in the module the
    # schedule itself calls, because the centroid it used to read is a proxy that
    # fails on exactly the records this gate exists for. A building placed from typed
    # coordinates before the plat module existed can stand a metre proud of its own
    # frontage: its centroid is then in the roadway and its walls are on the lot. Three
    # documented buildings on this grid do it, and the block this parcel shape met them
    # on read every one of its lots as free.
    #
    # THE OWNER'S 2026-08-27 CLAUSE, and it is asked here as `exclusive_lots` rather
    # than as `occupied_lots`: a lot of this block's own declared business front is not
    # exhausted by a RESEARCHED building standing AT THE STREET on it. He ruled it after
    # the South Water plat reconciliation (T-0199) seated five documented stores on lots
    # the schedule had already dealt this street's frontage runs — nothing overlapped,
    # the worst overlap in the town was zero, and what refused them was this rule and
    # not the ground. `tools/plat_occupancy.py`'s docstring carries the ruling, the fork
    # as it was put to him and all three tests the clause has to pass; everything
    # physical below — the lot margin, the corridor, the three-metre separation — is
    # untouched by it and still refuses what it always refused.
    # T-0432. THE OTHER DEAL'S ROOFS ARE NOT A STRANGER'S. `mine_ids` is this ENTRY's
    # records, and on a block dealt once that is every anonymous roof on it — so this
    # question has always been asked of ground the parcel itself had not touched. A
    # second deal breaks the coincidence: read with only its own records excluded, the
    # first deal's run reads the second deal's cottages as somebody else's houses, and
    # the business-front clause switches off underneath the lot they share the moment a
    # third claimant stands on it. The whole parcel is excluded instead, which restores
    # the question the clause was ruled on — was this lot free of everything THIS
    # PROGRAMME did not build — and leaves every physical gate reading the full town.
    # What it does not relax is density: the ceiling counted across deals, above, is
    # what now refuses a lot the programme has already filled.
    parcel = {sid for sid, _ in footprints(datum)
              if sid.startswith(f"{PREFIX}{block['block_id'][len('blk_'):]}_")}
    occupied = exclusive_lots({"blocks": [grid]}, datum,
                              exclude=mine_ids | parcel).get(block["block_id"], {})
    # The lots the owner's clause is HOLDING OPEN on this block — a documented store at
    # the street on a declared business-front lot, which `occupied` therefore does not
    # report. T-1053: while every declared front lot was also ground the run was dealt,
    # such a lot always landed in `built on by this parcel` and the class audit below
    # never had to name it. A front that reaches past the run's own ground does, and a
    # lot that is neither built on, occupied nor open would otherwise fail that audit
    # for carrying a store the clause itself says does not exhaust it.
    front_held = shared_business_fronts({"blocks": [grid]}, datum,
                                        exclude=mine_ids | parcel).get(block["block_id"], {})
    for index in (frontage["lots"] if frontage else []):
        holder = occupied.get(index)
        if holder is not None:
            raise SystemExit(f"{block['block_id']}: lot {index} already carries {holder}, "
                             f"so the frontage run cannot be dealt its roof. The "
                             f"schedule's headroom is the block's, not the lot's")
    for record in records:
        recon = record["reconstruction"]
        if "lot_index" not in recon:
            continue
        index, holder = recon["lot_index"], occupied.get(recon["lot_index"])
        if holder is None:
            continue
        if recon["inventory_class"] == "principal_functional":
            raise SystemExit(f"{block['block_id']}: lot {index} already carries "
                             f"{holder}, so a principal roof cannot stand on it. The "
                             f"schedule's headroom is the block's, not the lot's")
        raise SystemExit(f"{block['block_id']}: the yard building on lot {index} "
                         f"stands behind {holder}, which this parcel did not build. A "
                         f"yard building is a claim about the household on its own lot")
    for record in records:
        recon = record["reconstruction"]
        if (recon["inventory_class"] != "principal_functional"
                and recon.get("lot_index") not in set(used)):
            raise SystemExit(f"{block['block_id']}: the yard building on lot "
                             f"{recon['lot_index']} stands behind no roof — an ancillary "
                             f"building serves the lot it is in the yard of")

    # Every lot is built on, already taken, or open, and the recipe says which.
    # Without this the three classes are counted in three places and nothing makes
    # them meet: a lot could be called open in the recipe while a house stood on it,
    # which is a false statement about the town in the file that documents the town.
    open_entries = block.get("open_lots")
    if open_entries is None:
        single = block.get("open_lot")
        open_entries = [single] if single else []
    named_open = [int(entry["lot"]) for entry in open_entries]
    if len(set(named_open)) != len(named_open):
        raise SystemExit(f"{block['block_id']}: a lot is named open twice")
    for entry in open_entries:
        if len((entry.get("why") or "").split()) < 12:
            raise SystemExit(f"{block['block_id']}: lot {entry['lot']} is left open "
                             f"without saying why. Which lot is arbitrary, and an "
                             f"arbitrary choice nobody wrote down is indistinguishable "
                             f"from a slot that went missing")
    # A lot another DEAL on this same block builds on is its own class, and it has to
    # be, in both directions. Before that deal's records exist on disk it is occupied by
    # nothing and would read as a lot nobody accounted for; after they exist it is
    # occupied by a roof this recipe wrote, and calling it "already carrying a roof"
    # would say a stranger built it. The lots are read from the recipe rather than from
    # the ground, which is what makes the answer the same on both sides of a generate.
    # A lot the owner's business-front clause admits is NOT its own class: it is built
    # on by this parcel — the run stands over it — and it also carries a documented
    # store at the street. `occupied` is `exclusive_lots` above, so the clause has
    # already taken it out of "already carrying a roof".
    #
    # T-0432. THE TWO DEALS MAY MEET ON ONE LOT, and until this block nothing had asked
    # them to. The four sets above were held pairwise disjoint, which made "built on by
    # another deal" a PROHIBITION as well as an account: a lot the first deal's run
    # stood over could never be dealt again. That was true of every block so far only
    # because no second deal had come back to one — `blk_south_water_clark`'s two deals
    # took lots 4 and 2, and never met. It is not true here. The first deal on this
    # block declared a run over lots 0, 2 and 4 in August, under the ceiling of one
    # principal roof per lot; T-0079 retired that ceiling, and this block's whole
    # remaining headroom stands on lot 2 — its one free business front, the other free
    # lot being the corner the schedule's own sizing reserves. Refusing it would have
    # been the OLD ceiling enforcing itself through an accounting rule, a run at a time,
    # after the standard that retired it had already been written down.
    #
    # So the overlap is admitted and BOUNDED, and the bound is the density standard's
    # own, counted across deals rather than inside one: `ROW_UNITS_PER_LOT` roofs may
    # stand on a lot, and the roofs already standing on it are read off the committed
    # ground by the same module the rest of this gate asks. Nothing else relaxes — the
    # lot margin, the corridor, the three-metre separation and the run's own strip all
    # still refuse what they always refused, and on this lot the metres bind first: the
    # frontage clear of Frederick Thomas's shop takes two roofs and the ceiling takes
    # two, which is two reasons agreeing rather than one rule doing the work.
    shared_with_sibling = set(used) & set(sibling_lots)
    if shared_with_sibling:
        standing = lot_holders({"blocks": [grid]}, datum, exclude=mine_ids)
        standing = standing.get(block["block_id"], {})
        placed = {sid: poly for sid, poly in mine}
        for index in sorted(shared_with_sibling):
            # ROW UNITS, not roofs. A yard building is not in the street row and was
            # never what `ROW_UNITS_PER_LOT` counted — the ceiling is a statement about
            # how tightly a frontage packs, and a privy behind the row does not pack it.
            # A building this programme did not write carries no inventory class and is
            # counted: Frederick Thomas's shop stands in this row whoever built it.
            already = sum(1 for sid in standing.get(index, ())
                          if not is_ancillary_record(sid))
            # Where a row unit STANDS, not which lots its run was dealt. A run is one
            # stretch of frontage across several lots and its units fall where the
            # chain of party walls puts them — the first deal on this block declared
            # lots 0, 2 and 4 and stood all three of its units on lot 4 — so counting a
            # run's whole length against every lot it was dealt would refuse a lot that
            # carries none of it.
            lot = frames[index]["polygon"]
            adding = sum(
                1 for r in records
                if r["reconstruction"]["inventory_class"] == "principal_functional"
                and any(point_in_polygon(pt, lot) for pt in placed[r["id"]]))
            if already + adding > ROW_UNITS_PER_LOT:
                raise SystemExit(
                    f"{block['block_id']}: lot {index} already carries {already} roof(s) "
                    f"and this deal adds {adding}, past the {ROW_UNITS_PER_LOT} units a "
                    f"lot of this grid holds at the row's own measured spacing. A second "
                    f"deal on a lot is denser than the first, not unbounded by it")
    classes = {"built on by this parcel": set(used),
               "built on by another deal on this block": set(sibling_lots) - set(used),
               "already carrying a roof": set(occupied) - set(sibling_lots),
               "carrying a documented store on this block's business front":
                   set(front_held) - set(used) - set(sibling_lots) - set(occupied),
               "named open in the recipe": set(named_open)}
    for name, indices in classes.items():
        for other_name, other_indices in classes.items():
            if name < other_name and indices & other_indices:
                raise SystemExit(f"{block['block_id']}: lot(s) "
                                 f"{sorted(indices & other_indices)} are both {name} "
                                 f"and {other_name}")
    accounted = set().union(*classes.values())
    if accounted != set(range(len(frames))):
        missing = sorted(set(range(len(frames))) - accounted)
        raise SystemExit(f"{block['block_id']}: lot(s) {missing} are neither built on, "
                         f"already occupied, nor named open. Every lot of a block this "
                         f"parcel claims has to be accounted for")

    # a row stands on its face; everything else stands on its lot
    if frontage:
        check_frontage(block, face, strip, records, datum)

    # every footprint inside its own lot, clear of the conjectural side lines
    for record, (sid, poly) in zip(records, mine):
        if "lot_index" not in record["reconstruction"]:
            continue
        lot = frames[record["reconstruction"]["lot_index"]]["polygon"]
        for pt in poly:
            if not point_in_polygon(pt, lot):
                raise SystemExit(f"{sid} reaches outside lot "
                                 f"{record['reconstruction']['lot_index']}")
            gap = distance_to_edges(pt, lot)
            # 5 mm, the tolerance the party-line frontage gate above already uses and for
            # a related reason (T-0024). `gap` is the distance from a CORNER of the
            # footprint to the nearest point of the lot RING, while the setback the recipe
            # authors is measured along the face normal. On a lot whose side lines are not
            # exactly square to its face the two differ by a few millimetres of geometry,
            # so a roof authored to stand exactly ON the margin reads 1.4957 m and fails a
            # strict comparison. This is the derivation noise the file already tolerates
            # twice, not a relaxation of the margin: 1.5 m is still the floor and a roof
            # a centimetre inside it still fails.
            if gap < LOT_MARGIN_M - 0.005:
                raise SystemExit(f"{sid} stands {gap:.2f} m from its own lot line, "
                                 f"inside the {LOT_MARGIN_M} m margin")

    # nothing in the platted roadway. The lots are offset from the corridors, so this
    # cannot fail while the lot test passes — which is the point of running it anyway:
    # if the two ever disagree, the disagreement is the finding.
    lanes = corridors()
    for sid, poly in mine:
        street, depth = intrusion(poly, lanes)
        if street:
            raise SystemExit(f"{sid} reaches {depth:.1f} m inside the platted "
                             f"{lanes[street]['name']} corridor")

    # nothing within three metres of anything else in the dataset — EXCEPT a declared
    # party wall, which is not a collision (T-0077, and the same exemption the household
    # generator carries). The rule exists to stop two records occupying one yard; a row
    # on a shared line is the other thing two footprints can do, and the exemption is
    # exactly as wide as the claim that earns it — a record naming its neighbour in
    # `reconstruction.frontage.abuts`, which `check_frontage` above has already gated to
    # be a shared wall to the millimetre rather than a near miss. A building that merely
    # happens to be close still fails.
    abutted = set()
    for record in records:
        target = (record["reconstruction"].get("frontage") or {}).get("abuts")
        if target:
            abutted.add((record["id"], target))
            abutted.add((target, record["id"]))

    for sid, poly in mine:
        for other_id, other in others + [(s, p) for s, p in mine if s != sid]:
            if (sid, other_id) in abutted:
                continue
            gap = polygon_gap(poly, other)
            if gap < MIN_SEPARATION_M:
                raise SystemExit(f"{sid} stands {gap:.2f} m from {other_id}")

    # ground that was ever open to a private builder. The five tests around this one
    # ask where a roof stands relative to other roofs, to lot lines, to the roadway and
    # to the shape of the land. None of them asks whether the ground was for sale, and
    # T-A16 found that hole inside the plat before T-E2 found the larger one outside it:
    # the United States Reservation and the sand bar are a quarter of the modelled land
    # in this scene and nothing refused a dwelling on either.
    refused = load(DATA / "reconstruction" / "1835_no_build_ground.json")
    rings = no_build_rings()
    for region in refused["regions"]:
        polygon = rings[region["id"]]
        permitted = {p["structure_id"]
                     for p in region["what_may_stand_here"]["permitted"]}
        for sid, poly in mine:
            if sid in permitted:
                continue
            if any(point_in_ring(p, polygon) for p in poly):
                raise SystemExit(
                    f"{sid} stands on {region['name']}, which took no anonymous roof "
                    f"in 1835. The refusal is authored in 1835_no_build_ground.json and "
                    f"graded `{region['confidence']}`; read it before writing a recipe "
                    "here, and withdraw the refusal with its evidence rather than "
                    "working around it.")

    # buildable ground, on the surface the walker uses
    field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    if field is None:
        raise SystemExit("cannot validate placements: the committed heightfield is missing")
    for sid, poly in mine:
        pts = []
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            steps = max(2, int(math.dist(a, b)))
            pts += [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
                    for k in range(steps)]
        if not all(field.covers(e, n) for e, n in pts):
            raise SystemExit(f"{sid} falls outside the modelled terrain")
        heights = [field.height(e, n) for e, n in pts]
        if min(heights) < -.10:
            raise SystemExit(f"{sid} stands on the water side of the terrain")
        if max(heights) - min(heights) > MAX_RELIEF_M:
            raise SystemExit(f"{sid} spans {max(heights) - min(heights):.2f} m of relief")

    # the programme is a ceiling, not a budget to overspend
    inventory = load(INVENTORY_PATH)
    standing = Counter()
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load(path)
        recon = doc.get("reconstruction") or {}
        if recon.get("status") == "inferred_anonymous" and doc["id"] not in {s for s, _ in mine}:
            standing[recon["family"]] += 1
    for family, count in counts.items():
        target = inventory["family_targets"].get(family)
        if target is None:
            raise SystemExit(f"family {family} has no target in the building inventory")
        if standing[family] + count > target:
            raise SystemExit(f"{family}: {standing[family] + count} anonymous roofs "
                             f"against a programme target of {target}")

    # and every record resolves through the archetype it names
    for record in records:
        module = importlib.import_module(f"archetypes.{record['archetype']}_params")
        module.from_phase(record["phases"][0])


# --------------------------------------------------------------------------

def claimed_lots(block: dict) -> set[int]:
    """Every lot of the grid a recipe entry stands a roof on, run or not."""
    lots = {int(slot["lot"]) for slot in block["slots"] if "lot" in slot}
    return lots | {int(index) for index in (block.get("frontage") or {}).get("lots", [])}


def is_ancillary_record(structure_id: str) -> bool:
    """Whether a COMMITTED record is a yard building, read off the record itself.

    Only this generator's own records carry an inventory class; a documented building
    has none and is not ancillary — it is a roof in the row like any other.
    """
    path = STRUCTURES / f"{structure_id}.json"
    if not path.exists():
        return False
    recon = load(path).get("reconstruction") or {}
    return recon.get("inventory_class") == "ancillary"


def siblings(blocks: list[dict], block: dict) -> frozenset[int]:
    """The lots the OTHER deals on this block build on (T-0105)."""
    return frozenset().union(*[claimed_lots(other) for other in blocks
                               if other is not block
                               and other["block_id"] == block["block_id"]] or [set()])


def records_from_inputs() -> list[dict]:
    recipe = load(RECIPE_PATH)
    table = families()
    lots_by_id = {b["id"]: b for b in load(LOTS_PATH)["blocks"]}
    datum = load(DATA / "datum.json")
    records: list[dict] = []
    for block in recipe["blocks"]:
        # Ground the town held in common is refused BY NAME and before anything is
        # built, because the failure it would otherwise produce is the wrong one:
        # a reserved block reaches here with no lots, so a recipe on it would die
        # with "lot 3 is not in the grid" and read as a stale lot number rather
        # than as a claim about 1835 (ROADMAP T-A16).
        hold = (lots_by_id.get(block["block_id"]) or {}).get("reserved")
        if hold:
            raise SystemExit(
                f"{block['block_id']} is reserved ground — {hold['name']} — and takes no "
                f"anonymous roof. The reservation is authored in {hold['authored_in']} "
                f"and graded `{hold['confidence']}`; read it before writing a recipe "
                "entry here, and withdraw the reservation with its evidence rather than "
                "working around it."
            )
        records += build_block(block, table, lots_by_id, datum,
                               siblings(recipe["blocks"], block))
    ids = [r["id"] for r in records]
    if len(set(ids)) != len(ids):
        raise SystemExit("two block slots produced the same record id")
    deal_siding(records)

    # T-0423. The corpus prints ONE lot-and-block address — 'LOT No. 7, in block No. 16,
    # one lot east of Haddock's Tavern, on Lake street' — and the roof standing on that
    # lot is one of this parcel's own count-units. The address is spent here rather than
    # by editing the record, for exactly the reason the occupancy ledger is: hand-editing
    # a generated file would fail the drift check that makes these parcels trustworthy.
    # The seating is handed the records THIS RUN BUILT, not the committed ones, so an
    # address resolves against the town the recipe describes rather than against the file
    # the generator is about to overwrite. It writes ONE address block and nothing else —
    # not the record's `function`, which the dooryard, fence and signboard generators read
    # to decide what stands in a yard — and `tools/lot_addresses.py --check` re-reads the
    # phase afterwards and fails if a documented address has quietly promoted a roof.
    lot_addresses.apply(records, [(r["id"], world_polygon(r, datum))
                                  for r in records])

    # The adoption gate, in both directions. A household may name a roof this generator
    # owns, but only a PRINCIPAL one: an A-family roof is a stable, a privy or a woodshed
    # standing behind somebody's lot, and housing a household in one would be inventing an
    # occupant for a shed. The other direction — a roof the ledger names and no recipe
    # builds — would leave an adoption pointing at nothing, which is how a household
    # quietly loses its dwelling when a recipe is edited.
    by_id = {r["id"]: r for r in records}
    for sid in sorted(sid for sid in OCCUPANCY if sid.startswith(PREFIX)):
        record = by_id.get(sid)
        if record is None:
            raise SystemExit(f"the inferred-household programme adopts {sid}, which no "
                             f"block recipe builds")
        recon = record["reconstruction"]
        if recon["inventory_class"] != "principal_functional":
            raise SystemExit(f"{sid} is an ancillary {recon['family']} roof and cannot be "
                             f"adopted: a yard building serves the lot it stands behind, "
                             f"and an adoption is a claim about who lived or worked in a "
                             f"building")
    return records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the committed records still re-derive from the recipe")
    args = ap.parse_args()

    records = records_from_inputs()
    expected = {f"{r['id']}.json" for r in records}
    drift = []
    for rec in records:
        path = STRUCTURES / f"{rec['id']}.json"
        text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists():
                drift.append(f"{path.relative_to(ROOT)} is missing")
            elif path.read_text(encoding="utf-8") != text:
                drift.append(f"{path.relative_to(ROOT)} has drifted from the block recipe")
        else:
            path.write_text(text, encoding="utf-8")
    for path in sorted(STRUCTURES.glob(f"{PREFIX}*.json")):
        if path.name not in expected:
            drift.append(f"{path.relative_to(ROOT)} is not in any block recipe")
    if drift:
        print("PLATTED BLOCK INFILL DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    parcels = load(RECIPE_PATH)["blocks"]
    mode = "verified" if args.check else "generated"
    print(f"{mode} {len(records)} anonymous roofs across {len(parcels)} platted block(s)")
    # T-0834, and it is the line the ticket was opened for. A parcel's deal either fits
    # on its free lots one roof to a lot, or it does not and the frontage run is the
    # only ground the rest of it has. Those two cases read identically in the ledger —
    # same block, same shape of recipe, same `frontage` key — and the difference is
    # whether the run was headroom or necessity. It is printed rather than left to be
    # worked out from the schedule, because working it out is what nobody did.
    conditional, unsized = [], 0
    for block in parcels:
        claimed = block["drawn_from_schedule"]
        free = claimed.get("free_lots")
        if free is None:
            unsized += 1
            continue
        short = claimed.get("dealt_principal", claimed["principal"]) - max(0, free - 1)
        if short > 0:
            need = -(-short // (ROW_UNITS_PER_LOT - 1))
            got = len((block.get("frontage") or {}).get("lots") or ())
            conditional.append(f"{block['block_id']} needs {need} of its {got}")
    print(f"  lot ceiling (T-0834): {len(conditional)} of {len(parcels) - unsized} sized "
          f"parcel(s) are dealt past their free lots and stand the rest in a frontage "
          f"run — {', '.join(conditional) if conditional else 'none'}"
          + (f"; {unsized} pre-T-A6 parcel(s) carry no free-lot count" if unsized else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
