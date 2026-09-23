#!/usr/bin/env python3
"""Generate the anonymous West Division parcel west of Wolf Point.

The authored recipe (`data/reconstruction/1835_phase2_west_wolf_point_approaches.json`)
fixes an aggregate mix and a review layout, not fifty-five recovered buildings. Every
generated instance therefore says, in machine-readable and visitor-facing fields, that
its presence, position and footprint are conjectural.

**THE WHOLE PARCEL IS EMITTED SINCE T-1444, AND THAT TOO IS THE RECIPE'S OWN
INSTRUCTION.** Its `terrain_and_hydrology_gate` used to block any placement whose
centre lay west of local E -300 m until the modelled surfaces reached the extended box,
because a roof west of the ground would stand on nothing and the ground-contact gate
would have no surface to check it against. T-1416 built that ground: the committed
heightfield now spans E -705..1700 m, and the collision surface, the water mask and the
vegetation sampler are all readings of that same field, so the condition the block was
written against is met and the block is retired rather than waived. The 35 held slots
instantiate on their recipe ids and their recipe families, exactly as the hold promised.

**Five of those thirty-five stay held, on a different question entirely.** They stand
inside the drift band of the corporate boundary's extrapolated west leg, so it would be
the extrapolation rather than the 1833 ordinance deciding whether each stood inside the
town limits or outside them. The reconstruction leaves that side unstated by not
building the roof; see `BOUNDARY_HOLDS`. They keep their ids, their families and their
dealt sequence numbers, exactly as the terrain hold kept them.

The hold's one lasting mark is the dealing order. `seq` deals finish, roof condition,
age state and form, and the twenty roofs built under the hold were dealt 1..20 in
recipe order. Releasing the rest does not redeal them: `dealing_order()` keeps those
twenty first and appends the thirty-five behind them, so nothing already committed,
reviewed and baked moves because its neighbours arrived.

Like its two siblings (`generate_inferred_infill.py`, `generate_north_infill.py`) this
re-derives every record byte for byte under `--check`, which is what makes 20 generated
buildings auditable rather than 20 hand-placed ones.
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
INVENTORY_PATH = DATA / "reconstruction" / "1835_building_inventory.json"
RECIPE_PATH = DATA / "reconstruction" / "1835_phase2_west_wolf_point_approaches.json"
SOURCE_ID = "owner_chicago_1835_reconstruction_spec_2026"
PHASE_ID = "inferred_1835"
PROGRAMME_PHASE = "phase2_west_wolf_point_approaches"
PREFIX = "recon_1835_west_"

# The recipe's own instantiation block, retired by T-1444. It held every placement
# whose centre lay west of this line; `dealing_order()` still reads it, because the
# twenty roofs dealt east of it keep the sequence numbers they were built on. It is a
# record of what was held, not a gate — `validate()` asks the committed heightfield
# whether each footprint has ground under it, which is the question the block stood in
# for while no ground existed.
WEST_TERRAIN_LIMIT_E = -300.0

# The committed box the release stands on, from
# data/terrain/epochs/e1834_harbor_cut/heightfield.json. Stated here so a shrunk field
# fails loudly instead of silently un-grounding thirty-five roofs.
REQUIRED_WEST_BOX_E = -705.0

sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

# Phase two of the inferred-residents programme may adopt an anonymous roof as the
# dwelling or workplace of an inferred household (ROADMAP K1). The link is data, not a
# hand edit, so this generator still re-derives every record byte for byte.
from band_notes import split_notes  # noqa: E402
# The one sampling rule, shared with the platted blocks and the North parcel. This
# generator used to retype one eave and one pitch per family into Python, and eleven of
# those constants sat outside the band the note under them cited (T-0172, T-0272). The
# band is now used as the range it was authored as.
from family_bands import admits_loft  # noqa: E402
from family_bands import (eave_floor, eave_for_ridge,  # noqa: E402
                          eave_limits, eaves_front_refusal_ratio,
                          eaves_front_width_m, families, pitch_deg,
                          wall_height_m)
from ridge_model import ridge_run_m  # noqa: E402
from roof_form import note_refusal, roof_kind  # noqa: E402
from inferred_occupancy import occupancy  # noqa: E402
# T-0112. The clapboard stock is dealt at the end of the parcel, because it is the one
# form value that depends on where a building's neighbours stand — and the recipe is
# the only thing that knows the parcel whole. See tools/siding_stock.py.
from siding_stock import deal_records as deal_siding  # noqa: E402

OCCUPANCY = occupancy()
FAMILIES = families()


def spec_for(family: str) -> dict:
    """The crosswalk's entry for a family, which is where its bands are authored."""
    spec = FAMILIES.get(family)
    if spec is None or not spec.get("eave_ft"):
        raise SystemExit(f"the crosswalk authors no eave band for family {family}; "
                         f"the West recipe cannot sample it")
    return spec


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


def inferred(value, reason: str):
    # The grade is the BOTTOM tier, not the middle one. This helper is called
    # `inferred` and wrote "derived", which is the whole bug: every roof it raises
    # is an invention, and grading those as reasoned-from-evidence made buildings
    # that never existed render solid while the documented Exchange Coffee House
    # rendered as a dithered ghost beside them.
    return {"value": value, "confidence": "reconstructed", "sources": [SOURCE_ID],
            "note": INVENTED_NOTE + reason}


def archetype_for(family: str) -> str:
    if family == "D1":
        return "log_dwelling"
    if family.startswith("D") and family != "D2" or family == "H1":
        return "frame_dwelling"
    if family.startswith("C"):
        return "frame_storefront"
    if family.startswith("T") or family.startswith("I") or family in ("H2", "H3"):
        return "frame_tavern"
    return "outbuilding"


# The West families, worded from the crosswalk's own labels so a visitor reading the
# card and a maintainer reading the ledger see the same trade.
FUNCTIONS = {
    "D1": "older_log_dwelling", "D2": "rough_plank_dwelling_or_shanty",
    "D3": "one_room_frame_cottage", "D4": "two_room_frame_cottage",
    "D5": "deep_plan_frame_cottage", "D6": "one_and_a_half_story_frame_cottage",
    "D7": "small_two_story_frame_house", "H1": "small_boarding_house",
    "H2": "medium_boarding_house", "C1": "small_shop_or_office",
    "C2": "store_residence", "W1": "blacksmith_shop",
    "W2": "carpenter_or_joiner_shop",
    "W3": "cooper_wagon_or_wheelwright_shop", "W4": "small_artisan_shop",
    "W5": "large_workshop", "F1": "freight_or_storage_shed",
    "A1": "stable", "A2": "barn_or_carriage_shed", "A3": "privy",
    "A4": "woodshed_or_storage_shed", "A5": "small_utility_building",
}

# The prose the record's human-facing `name` has always used. Split from FUNCTIONS
# by T-1311, which closed the `function` vocabulary: the value is now a term from
# `data/structures.schema.json`, and a term is not a phrase to put in front of a
# visitor. Both tables are keyed by the same band, and this one keeps the names
# these records already carry - migrating a vocabulary is not licence to rename
# 48 buildings.
LABELS = {
    "D1": "older log dwelling",
    "D2": "rough plank dwelling or shanty",
    "D3": "one-room frame cottage",
    "D4": "two-room frame cottage",
    "D5": "deep-plan frame cottage",
    "D6": "one-and-a-half-story frame cottage",
    "D7": "small two-story frame house",
    "H1": "small boarding house",
    "H2": "medium boarding house",
    "C1": "small shop or office",
    "C2": "store-residence",
    "W1": "blacksmith shop",
    "W2": "carpenter or joiner shop",
    "W3": "cooper, wagon or wheelwright shop",
    "W4": "small artisan shop",
    "W5": "large workshop",
    "F1": "freight or storage shed",
    "A1": "stable",
    "A2": "barn or carriage shed",
    "A3": "privy",
    "A4": "woodshed or storage shed",
    "A5": "small utility building",
}


def finish_for(seq: int) -> tuple[str, str]:
    # Deterministic and weighted toward unpainted material, as in the two sibling
    # parcels. The west side is the poorer, newer half of the town and the recipe says
    # so, so the paint that does appear stays sparse.
    keys = ("weathered_timber", "fresh_timber", "weathered_timber", "mixed_patch",
            "fresh_timber", "whitewash", "weathered_timber", "ochre")
    key = keys[(seq * 3) % len(keys)]
    paint = {"whitewash": "whitewash", "red_oxide": "red"}.get(key, "unpainted")
    return key, paint


def band_note(family: str) -> str:
    """The sentence that defends every invented form value, and it is a source claim.

    Kept in one place because K33 restricts where it may be attached, and a claim that
    is authored in one file and audited in another drifts. See tools/band_notes.py.
    """
    return (f"Type-level choice within the {family} band in the supplied reconstruction "
            "specification; it is not evidence for this anonymous West Division instance.")


def form_for(family: str, seq: int, paint: str, width: float, depth: float) -> dict:
    """The family's form values, with the band citation restricted to what it can cite.

    `_form_body` authors every value exactly as it always has, with the citation
    attached to all of them; `split_notes` (ROADMAP K33) then strips that citation from
    the values whose family authors nothing for it to point at, and says instead what
    the value actually is — the reconstruction generator's type default. `note_refusal`
    (T-0179) then adds, on the families whose roof line offers a SHED this town does not
    build, the measured reason it does not — because a refusal that lives only in a
    Python tuple is a refusal no visitor can read.
    """
    return note_refusal(
        split_notes(_form_body(family, seq, paint, width, depth), family,
                    band_note(family)),
        family, width, depth)


def door_kind(family: str) -> str:
    """WHICH DOOR a family carries. Asked for rather than read off the form dict,
    because the eave FLOOR depends on it — a wagon door needs a metre more wall than a
    man door — and the floor has to be known before the eave is drawn."""
    if family in ("W1", "W2", "W3", "W5", "F1", "A2"):
        return "wagon"
    return "stable" if family == "A1" else "man"


def _storeys(family: str):
    """The storey count this parcel authors, which is what bounds the eave.

    `None` for the families that fall to the outbuilding tail, which author no storey
    count at all — and `eave_limits` reads that as "no storey-dependent limit", which is
    the truth for `outbuilding`. The values are the ones this file has always written;
    they are named here because `eave_limits` has to be asked the question before the
    branch that answers it is reached.
    """
    if family == "D1" or family.startswith("C"):
        return 1
    if family.startswith("D") and family != "D2" or family == "H1":
        return 1.5 if family in ("D6", "H1") else (2 if family in ("D7", "H2") else 1)
    if family == "H2":
        return 2
    return None


def _pitch_default(family: str) -> float:
    """The generator's own type value, which is what a family authoring no band gets."""
    if family == "D1":
        return 35.0
    if family.startswith("D") and family != "D2" or family == "H1":
        return 42.0 if family in ("D6", "H1") else 38.0
    if family.startswith("C"):
        return 33.0
    if family == "H2":
        return 38.0
    return 18.0 if roof_kind(family)[0] == "shed" else 32.0


def _form_body(family: str, seq: int, paint: str, width: float, depth: float) -> dict:
    why = band_note(family)
    frame = "balloon_frame" if seq % 2 else "braced_frame"
    spec = spec_for(family)
    # The stable key every sampled value in this parcel is drawn on. It is the SEQUENCE
    # number because that is what identifies a West slot: the recipe hands this file a
    # layout row and the structure id is derived from it further down, so the sequence
    # is the one identifier `tools/measure_family_deal.py` can also deal a synthetic
    # instance under.
    key = f"{PREFIX}form_{seq:04d}"

    # THE EAVE AND THE PITCH COME FROM THE FAMILY'S OWN BAND (T-0272). They were
    # per-family CONSTANTS, and the note printed under each one told a visitor it was a
    # type-level choice "within the {family} band" — which for eleven of them was not
    # true: A5 and W4 stood at a man door's 2.05 m under bands starting at 7 and 9 ft,
    # C2 at 3.25 m and 33.0 deg, D3 at 2.78, D7 at 5.05, H2 at 5.2 m and 38.0 deg, A2 at
    # 32.0 deg, and D2 fell past the D branch to the outbuilding tail and took the
    # tail's 2.05 m and 18.0 deg with it. A constant is also a claim of uniformity no
    # source makes: twenty roofs dealt from one figure per family are not twenty roofs.
    #
    # This is the repair T-0144 and T-0145 made on the platted blocks, which T-0172's
    # sweep then measured here. Two of the eleven — H2's pair — stood on a branch no
    # West slot has ever been dealt, so nothing in the repo said the card was bad until
    # a sweep dealt the family anyway.
    #
    # The archetype bounds the band at BOTH ends and the limits are ASKED of it, never
    # retyped; the ridge band the same crosswalk entry authors bounds it once more,
    # which needs the run the roof climbs, and that is the archetype's too.
    roof_type, gable_front = roof_kind(family)
    stories = _storeys(family)
    archetype = archetype_for(family)
    run = ridge_run_m(archetype, roof_type, width, depth, gable_front)
    arch_lo, arch_hi = eave_limits(archetype, stories)
    floor, ceiling = max(eave_floor(family, door_kind(family)), arch_lo), arch_hi
    wall = eave_for_ridge(wall_height_m(family, spec["eave_ft"], key, floor, ceiling),
                          family, spec["eave_ft"], spec.get("roof"),
                          spec.get("ridge_ft"), run, _pitch_default(family), key,
                          floor, ceiling)

    def pitch() -> float:
        return pitch_deg(family, spec.get("roof"), key, _pitch_default(family),
                         eave_m=wall, run_m=run, ridge_ft=spec.get("ridge_ft"))

    if family == "D1":
        return {
            "stories": inferred(1, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why), "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred("log", why), "loft": inferred(True, why),
            "chimneys": inferred(1, why),
        }

    if family.startswith("D") and family != "D2" or family == "H1":
        plan = "centre_passage" if family in ("D7", "H2") else (
            "single_pen" if family == "D3" else "hall_parlour")
        return {
            "stories": inferred(stories, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why), "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred(frame, why), "plan": inferred(plan, why),
            "bays": inferred(5 if family in ("D7", "H2") else 3, why),
            "chimneys": inferred(2 if family.startswith("H") else 1, why),
            "paint": inferred(paint, why),
        }

    if family.startswith("C"):
        return {
            "stories": inferred(1, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why), "roof_pitch_deg": inferred(pitch(), why),
            "gable_front": inferred(True, why), "construction": inferred(frame, why),
            "cladding": inferred("clapboard", why), "paint": inferred(paint, why),
            "loft": inferred(family == "C2", why), "chimneys": inferred(1, why),
            "shopfront": inferred(True, why), "goods_door": inferred(True, why),
            "goods_door_side": inferred("end", why),
        }

    if family in ("H2",):
        return {
            "stories": inferred(2, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why), "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred("braced_frame", why), "paint": inferred(paint, why),
            "gallery": inferred(False, why), "chimneys": inferred(2, why),
        }

    door = door_kind(family)
    # WHICH ROOF A FAMILY GETS is `tools/roof_form.py`'s answer and no longer this
    # file's (T-0179): the same literal used to sit in five parcels and the five had
    # already drifted over A5.
    construction = "light_frame" if family in ("W2", "W4", "A1", "A2") else "plank"
    return {
        "wall_height_m": inferred(wall, why), "roof_type": inferred(roof_type, why),
        "roof_pitch_deg": inferred(pitch(), why),
        "construction": inferred(construction, why), "door": inferred(door, why),
        "door_side": inferred("front", why),
        # ASKED OF THE CROSSWALK, not of a literal (T-0179's lesson, one line below the
        # comment that draws it): the hand-kept set gave a loft to W3 and W5, both
        # authored `levels '1'`, and west_rec_036 reached the band gate on it.
        "loft": inferred(admits_loft(family), why),
        "board_gap_m": inferred(.012, why), "paint": inferred(paint, why),
    }


def footprint_origin(center_e: float, center_n: float, width: float, depth: float,
                     bearing: float) -> tuple[float, float]:
    """Convert the recipe's centre anchor to the GLB contract's (0, 0) corner."""
    theta = math.radians(bearing)
    cos, sin = math.cos(theta), math.sin(theta)
    return (center_e - width * .5 * cos - depth * .5 * sin,
            center_n + width * .5 * sin - depth * .5 * cos)


CLUSTER_PLACE = {
    "w1_canal_lake_mixed": "west of Canal and Lake, behind the Wolf Point sequence",
    "w2_canal_randolph_teamster": "the Canal and Randolph teamster approach",
}

# Eight of the twenty buildable slots stand inside a platted street corridor, by
# 2.2 to 11.7 m. That is not a defect in the recipe so much as its date: it was
# authored before ROADMAP K7 generated the Thompson block and lot geometry, so
# nothing could check its layout against a street until now. A building in the
# middle of Clinton Street is the one thing everyone can see is wrong, and K7's own
# phase-two note already records seven EXISTING records standing in the road.
#
# Each slot is therefore set back to the nearest position that clears the corridor
# and still passes every other gate — collision with this parcel and with every
# committed record, terrain covered, dry, and inside the 0.35 m step contract. The
# largest move is 12.5 m, inside the ±20 m working uncertainty the recipe states for
# its own coordinates, so no slot leaves the block it was allocated to. Values are
# frozen constants rather than a search run at generation time: a placement that
# moves when an unrelated gate changes is not reproducible.
#
# T-1444 keyed this by PLACEMENT ID rather than by dealing sequence. The eight values
# below are unchanged and still land on the same eight roofs; the key changed because
# releasing the held slots moves nothing but adds thirty-five sequence numbers, and a
# setback that follows its building is worth more than one that follows its position in
# a list. Five more slots joined the table when the hold lifted: four of the five sit in
# corridors that only reached them once T-1443 carried Lake and Randolph west off their
# E -320 clip, which is the ordinary consequence of a street arriving after a layout.
STREET_ADJUSTMENTS = {
    "west_rec_003": (4.50, 0.00),    # Clinton Street, 4.3 m in
    "west_rec_007": (-1.25, -2.17),  # Lake Street, 2.2 m in
    "west_rec_009": (-6.40, 1.13),   # Clinton Street, 6.3 m in
    "west_rec_012": (10.00, 0.00),   # Clinton Street, 9.5 m in
    "west_rec_016": (12.00, 0.00),   # Clinton Street, 11.7 m in
    "west_rec_022": (-9.36, 1.65),   # Clinton Street, 9.1 m in
    "west_rec_023": (1.39, 7.88),    # Randolph Street, 7.8 m in
    "west_rec_024": (8.03, 9.58),    # Randolph Street, 9.5 m in
    # Released by T-1444, set back on the same rule and by the same search: the nearest
    # quarter-metre step that clears the corridor and still passes collision, terrain
    # cover, the dry-ground test and the 0.35 m step contract. Largest move 5.5 m.
    "west_rec_025": (0.96, 5.42),    # Randolph Street, 5.4 m in
    "west_rec_029": (-1.04, -3.86),  # Lake Street, 3.8 m in
    "west_rec_031": (-1.42, -5.31),  # Lake Street, 5.3 m in
    "west_rec_035": (-0.74, -1.59),  # Randolph Street, 1.5 m in
    "west_rec_036": (-0.48, -0.57),  # Randolph Street, 0.6 m in
}

# THE EAVES-FRONT HOLD — T-1497, and it replaces a quarter-circle turn.
#
# This parcel is the one that takes its rectangle STRAIGHT FROM THE RECIPE instead of
# sampling it through `tools/family_bands.py`, so the rule the platted blocks and the
# North parcel already carry — hold a D- or H-family rectangle to a proportion the
# eaves-front frame dwelling can actually build — never reached it. What stood in its
# place was `FACING_CORRECTIONS`, a frozen set of one: west_rec_033, whose recipe slot
# is 20 x 32 ft, a ratio of 1.6 past the 1.5 `frame_dwelling_params` refuses. The
# generator swapped width for depth and turned the bearing a quarter circle to get an
# eaves-front house through at all, and the result stood as 32.00 x 20.00 ft — OUT of
# the 18x28-24x34 ft band its own note cites, which is the row
# `tools/band_claims_baseline.json` has been carrying with `waiting_on: T-1497`.
#
# The swap existed because the crosswalk asked D5 for a FRONT GABLE the archetype would
# not build. `docs/RESEARCH/d5_gable_front_cottage_1835.md` withdrew that: no source in
# this corpus records a gable-front dwelling at Chicago before 1836, and the narrow lot
# that produces the form on a cottage was not a condition of a town whose committed lots
# read a median 80.9 ft of frontage. With the front gable gone the swap has nothing to be
# a workaround for.
#
# So the rectangle is held rather than turned: the recipe's DEPTH is kept exactly, and
# the FRONT is widened inside the family's own band until the range is one the archetype
# builds. west_rec_033 re-derives at 21.92 x 32.00 ft — both figures inside D5's band,
# no swap, no rotation. Nothing is recorded standing a different way round from the way
# the recipe laid it out.
#
# IT FIRES ONLY WHERE THE ARCHETYPE REFUSES. Nineteen other west slots sit between
# family_bands' 1.46 proportion and the archetype's 1.5 refusal; their archetype builds
# them, so they keep the recipe's rectangle and are not re-derived for a proportion
# nothing is complaining about. Re-sampling the whole parcel through `dimensions_m` is a
# different and larger change; T-1497 records it as a finding rather than doing it here.
def eaves_front_hold(family: str, width_ft: float, depth_ft: float) -> float:
    """The front this recipe rectangle must carry, in feet. Unchanged where it fits."""
    spec = families().get(family) or {}
    refusal = eaves_front_refusal_ratio(spec.get("archetype"))
    if refusal is None or depth_ft <= width_ft * refusal:
        return width_ft
    band = spec.get("band_ft")
    if not band:
        return width_ft
    hi_w_ft = float(band[2])
    held_m = eaves_front_width_m(family, width_ft * .3048, depth_ft * .3048,
                                 hi_w_ft * .3048)
    return held_m / .3048

# FIVE SLOTS STAY HELD, AND NOT FOR TERRAIN. The corporate boundary of 7 November 1833
# resolves its west leg on Jefferson Street, whose committed centreline ends far south
# of this parcel: `tools/measure_corporation_limits.py` carries it 1 188.8 m past that
# end to reach Ohio, and an extension that long is uncertain by 22 m of drift. Five of
# the released slots stand inside that band — 6.9 to 22.6 m from the line — so it is the
# EXTRAPOLATION, not the ordinance, that would decide whether each of them stood inside
# the town of Chicago or outside it. The gate says the remedy in as many words: trace the
# street, or leave the structure's side unstated. Tracing Jefferson north to Ohio is not
# this ticket's work, so the side is left unstated in the only way a reconstruction can
# leave it unstated — the roof is not built. They keep their ids, their families and
# their dealt sequence numbers exactly as the terrain hold kept them, so the day the
# centreline is carried they instantiate unchanged. Measured 2026-09-20; T-1490 owns it.
# The slots and their measurements are RECORDED IN THE RECIPE, under
# `terrain_and_hydrology_gate.boundary_hold`, and read from there rather than retyped:
# `tools/reconcile_665.py` has to count the same hold, and two copies of a hold are how
# a schedule and a generator come to disagree about what the parcel still owes.
BOUNDARY_HOLDS = frozenset(
    load(RECIPE_PATH)["terrain_and_hydrology_gate"]["boundary_hold"]["slots"])
HELD_IDS = {f"{PREFIX}{rid.split('_')[-1]}" for rid in BOUNDARY_HOLDS}

# The reading T-1444 took of the recipe's fourth terrain rule, frozen so the corridor
# cannot quietly gain a roof while T-1460 is open. Measured as footprint-corner distance
# to the swale centreline against its own half_width_m; see validate() for what it means
# and why nothing is moved to satisfy it. Closest in is recon_1835_west_002 at 3.2 m of
# a 30 m half-width; the eighth, recon_1835_west_013, arrives with the release at 14.3 m.
SWALE_CORRIDOR_OCCUPANTS = {
    (f"{PREFIX}{n}", "west_prairie_swale_a")
    for n in ("001", "002", "003", "005", "009", "011", "012", "013")
}


def make_record(row: dict, seq: int, datum: dict) -> dict:
    sid = f"{PREFIX}{row['id'].split('_')[-1]}"
    de, dn = STREET_ADJUSTMENTS.get(row["id"], (0.0, 0.0))
    center_e = float(row["center_local_enu_m"][0]) + de
    center_n = float(row["center_local_enu_m"][1]) + dn
    width_ft, depth_ft = (float(v) for v in row["footprint_ft"])
    bearing = float(row["rotation_deg"])
    family = row["family"]
    recipe_width_ft = width_ft
    width_ft = eaves_front_hold(family, width_ft, depth_ft)
    held = width_ft != recipe_width_ft
    width, depth = round(width_ft * .3048, 3), round(depth_ft * .3048, 3)
    local_e, local_n = footprint_origin(center_e, center_n, width, depth, bearing)
    finish_key, paint = finish_for(seq)
    function = FUNCTIONS[family]
    label = LABELS[family]
    where = CLUSTER_PLACE.get(row["cluster"], "the West Division approaches")
    setback = (f" Set back {math.hypot(de, dn):.1f} m from the recipe coordinate, which "
               "placed it inside a platted street corridor; the move is well inside the "
               "±20 m uncertainty the recipe states for its own layout controls."
               if de or dn else "")
    if held:
        setback += (f" The recipe's {recipe_width_ft:.0f} ft front is widened to "
                    f"{width_ft:.2f} ft here, its {depth_ft:.0f} ft depth kept exactly. "
                    "An 1835 dwelling is eaves-front — ridge parallel to the facade — and "
                    "the recipe's rectangle is deeper than that roof will carry on that "
                    "front, so the front is held to the proportion the archetype builds. "
                    "Both figures stay inside the family's authored band; the building is "
                    "not turned, and nothing is recorded standing a different way round "
                    "from the way the recipe laid it out. See "
                    "docs/RESEARCH/d5_gable_front_cottage_1835.md.")
    reconstruction = {
        "status": "inferred_anonymous", "family": family, "district": "west",
        "inventory_class": row["inventory_class"], "programme_phase": PROGRAMME_PHASE,
        "source_id": SOURCE_ID, "sequence": seq, "finish_key": finish_key,
        "roof_condition": ("weathered", "fresh", "patched", "darkened")[seq % 4],
        "age_state": ("recent", "new", "older_frontier", "established")[seq % 4],
    }
    mapping_note = (" H2 boarding-house massing currently uses a generic rectangular "
                    "frame block because no boarding-house generator is implemented."
                    if family == "H2" else "")
    return {
        "id": sid, "name": f"Reconstructed {family} {label} #{seq:03d}",
        "archetype": archetype_for(family),
        "phases": [{
            "id": PHASE_ID,
            "documented_range": {
                "from": "1835-01-01", "to": "1835-12-31", "confidence": "reconstructed",
                "note": "Anonymous count-unit toward the July 1835 programme. No evidence establishes that this particular building existed."
            },
            "position": {
                "utm_e": round(float(datum["origin_utm_e"]) + local_e, 3),
                "utm_n": round(float(datum["origin_utm_n"]) + local_n, 3),
                "rotation_deg": bearing,
                "symbolic_location": f"Anonymous reconstructed roof on {where}",
                "confidence": "reconstructed",
                "note": ("Interpretive placement within the reviewed West Division cluster "
                         f"{row['cluster']}. The recipe coordinate is a production-layout "
                         "control, not a recovered lot." + setback),
                "derivation": {"method": "not_derivable", "reason": "No parcel-by-parcel July 1835 West Division roof register survives in the supplied evidence."}
            },
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": (f"A {width_ft:.2f} × {depth_ft:g} ft rectangle assigned by the reconstruction recipe within the {family} family band; no individual dimensions are documented."
                         if held else
                         f"A {width_ft:g} × {depth_ft:g} ft rectangle assigned by the reconstruction recipe within the {family} family band; no individual dimensions are documented.")
            },
            "form": form_for(family, seq, paint, width, depth),
            "change_note": "Reconstructed anonymous July 1835 West Division infill; a better-evidenced named roof substitutes for a compatible count-unit rather than increasing the 665-roof total."
        }],
        "function": inferred(function, f"Assigned from the {family} family to satisfy the aggregate West Division mix; no occupant or individual use is known."),
        **({"occupants": OCCUPANCY[sid]} if sid in OCCUPANCY else {}),
        "reconstruction": reconstruction,
        "research_note": ("RECONSTRUCTED / GENERATED, NOT AN ATTESTED NAMED BUILDING. "
                          "Aggregate mix follows the supplied specification; exact presence, "
                          "position, footprint, finish and instance-level form are interpretive."
                          + mapping_note),
        "review_required": False,
    }


def world_polygon(record: dict, datum: dict) -> list[tuple[float, float]]:
    phase = record["phases"][0]
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg", 0)))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def point_segment_distance(e: float, n: float, a: tuple[float, float],
                           b: tuple[float, float]) -> float:
    """Local-ENU distance from a point to a segment, for the swale corridors."""
    de, dn = b[0] - a[0], b[1] - a[1]
    span = de * de + dn * dn
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((e - a[0]) * de + (n - a[1]) * dn) / span))
    return math.hypot(e - (a[0] + t * de), n - (a[1] + t * dn))


def polygons_overlap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    """Strict convex-polygon SAT; touching edges are permitted."""
    for poly in (a, b):
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            axis = (-(q[1] - p[1]), q[0] - p[0])
            pa = [x * axis[0] + y * axis[1] for x, y in a]
            pb = [x * axis[0] + y * axis[1] for x, y in b]
            if max(pa) <= min(pb) + .05 or max(pb) <= min(pa) + .05:
                return False
    return True


def other_world_polygons(datum: dict, mine: set[str]) -> list[tuple[str, list]]:
    """Every OTHER committed structure's footprint, so this parcel cannot be placed
    into a building that already exists. The two sibling generators only check within
    their own parcel; the West approaches run past Wolf Point, where the oldest and
    best-attested records in the project stand."""
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        record = load(path)
        if record["id"] in mine:
            continue
        for phase in record.get("phases", []):
            pos = phase.get("position") or {}
            poly = (phase.get("footprint") or {}).get("polygon") or []
            if pos.get("utm_e") is None or len(poly) < 3:
                continue
            out.append((record["id"], world_polygon({"phases": [phase]}, datum)))
            break
    return out


def validate(records: list[dict], rows: list[dict],
             inventory: dict, recipe: dict, datum: dict) -> None:
    totals = recipe["roof_totals"]
    if len(records) != totals["all"]:
        raise SystemExit(f"West recipe accounts for {len(records)} roofs, "
                         f"expected {totals['all']}")

    # Releasing the held half is not licence to quietly change what the parcel is: the
    # whole parcel must still be the recipe's mix, as both halves together had to be.
    all_families = Counter(r["reconstruction"]["family"] for r in records)
    if all_families != Counter(recipe["family_totals"]):
        raise SystemExit(f"West family mix drifted: {dict(all_families)}")
    for family, count in all_families.items():
        if count > inventory["family_targets"][family]:
            raise SystemExit(f"West {family} count {count} exceeds programme target")

    # Every placement instantiates, on its own recipe id. The hold promised the 35 held
    # slots would arrive unchanged in id and family, and this is where that is kept.
    placement_ids = {row["id"] for row in recipe["placements"]}
    if not BOUNDARY_HOLDS <= placement_ids:
        raise SystemExit("BOUNDARY_HOLDS names a slot this recipe does not place: "
                         + ", ".join(sorted(BOUNDARY_HOLDS - placement_ids)))
    expected_ids = {f"{PREFIX}{row['id'].split('_')[-1]}" for row in recipe["placements"]}
    if {r["id"] for r in records} != expected_ids:
        raise SystemExit("the West parcel no longer instantiates one record per "
                         "recipe placement, on the placement's own id")

    # The twenty roofs dealt under the hold keep their sequence numbers. A released slot
    # that took one would redeal a committed roof's finish, roof condition and age state.
    first, _ = split_placements(recipe)
    for seq, row in enumerate(first, start=1):
        sid = f"{PREFIX}{row['id'].split('_')[-1]}"
        record = next(r for r in records if r["id"] == sid)
        if record["reconstruction"]["sequence"] != seq:
            raise SystemExit(f"{sid} was dealt {seq} under the hold and is now "
                             f"{record['reconstruction']['sequence']}; the release "
                             "may not redeal the roofs already built")

    for record in records:
        module = importlib.import_module(f"archetypes.{record['archetype']}_params")
        module.from_phase(record["phases"][0])

    mine = {r["id"] for r in records}
    polygons = [(r["id"], world_polygon(r, datum)) for r in records]
    for i, (sid, poly) in enumerate(polygons):
        for other_sid, other in polygons[:i]:
            if polygons_overlap(poly, other):
                raise SystemExit(f"West recipe collision: {sid} overlaps {other_sid}")
    for sid, poly in polygons:
        for other_sid, other in other_world_polygons(datum, mine):
            if polygons_overlap(poly, other):
                raise SystemExit(f"West recipe collision: {sid} overlaps existing {other_sid}")

    from plat_corridors import corridors, intrusion  # noqa: PLC0415
    lanes = corridors()
    for sid, poly in polygons:
        street, depth = intrusion(poly, lanes)
        if street:
            raise SystemExit(f"{sid} reaches {depth:.1f} m inside the platted "
                             f"{lanes[street]['name']} corridor")

    from heightfield import Heightfield  # noqa: PLC0415
    field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    if field is None:
        raise SystemExit("West recipe cannot validate: committed heightfield is missing")

    # The released half stands on the ground T-1416 built, so the release reads the box
    # rather than trusting the note that says it arrived. This is the retired
    # instantiation block's condition, asked of the committed field every run.
    spec = load(DATA / "terrain" / "epochs" / "e1834_harbor_cut" / "terrain_spec.json")
    if float(spec["grid"]["e_min_m"]) > REQUIRED_WEST_BOX_E:
        raise SystemExit(
            f"the committed terrain box starts at E {spec['grid']['e_min_m']:g} m and "
            f"the West parcel was released onto ground reaching E {REQUIRED_WEST_BOX_E:g} m. "
            "Re-extend the field or re-impose the recipe's instantiation block; do not "
            "leave thirty-five roofs standing off the edge of it.")

    # The recipe's fourth terrain rule deferred a reading to "after the west terrain
    # extension", which is now: no roof in the two conjectural west-prairie swales, and
    # move the roof rather than flatten the swale. T-1444 took the reading and it does
    # not say what the rule assumed. SEVEN OF THE TWENTY ROOFS BUILT UNDER THE HOLD
    # ALREADY STAND INSIDE west_prairie_swale_a's 30 m corridor, seated there in 2026-08
    # while the rule was still deferred, and an eighth arrives with the release. The
    # swale is the conjectural half of that pair: its alignment is invented (no source;
    # T-0795 walked the whole Wright sheet and it draws no watercourse on this prairie),
    # and since T-1416 carried the field out to E -705 its line no longer even reaches
    # the edge of the ground — it begins abruptly at E -320, in open modelled prairie,
    # where the old west wall used to be. Moving eight reviewed roofs to fit an invented
    # line that starts nowhere is not what the rule was protecting, so the alignment
    # goes to the owner (T-1460) and the occupancy is frozen here instead: the corridor
    # may not quietly acquire a ninth roof while that question is open.
    swales = [sw for sw in spec.get("swales", []) if sw["id"].startswith("west_prairie_")]
    inside = set()
    for sid, poly in polygons:
        for swale in swales:
            line = [(float(e), float(n)) for e, n in swale["line"]]
            half = float(swale["half_width_m"])
            if any(point_segment_distance(e, n, a, b) <= half
                   for e, n in poly for a, b in zip(line, line[1:])):
                inside.add((sid, swale["id"]))
    if inside != SWALE_CORRIDOR_OCCUPANTS:
        arrived = sorted(f"{sid} in {swale}" for sid, swale in inside - SWALE_CORRIDOR_OCCUPANTS)
        left = sorted(f"{sid} in {swale}" for sid, swale in SWALE_CORRIDOR_OCCUPANTS - inside)
        raise SystemExit(
            "the conjectural west-prairie swale corridors no longer hold the roofs "
            "T-1444 measured into them"
            + (f"; arrived: {', '.join(arrived)}" if arrived else "")
            + (f"; left: {', '.join(left)}" if left else "")
            + ". See T-1460: the alignment, not the roofs, is what the recipe's fourth "
              "terrain rule asked to be reviewed.")

    for sid, poly in polygons:
        heights = [field.height(e, n) for e, n in poly]
        if not all(field.covers(e, n) for e, n in poly):
            raise SystemExit(f"{sid} falls outside modelled terrain")
        if min(heights) < -.10:
            raise SystemExit(f"{sid} intersects the authoritative water side of the terrain")
        if max(heights) - min(heights) > .35:
            raise SystemExit(f"{sid} spans {max(heights) - min(heights):.2f} m of relief; "
                             "its walls would not share the walker surface")


def split_placements(recipe: dict) -> tuple[list[dict], list[dict]]:
    """The two halves the retired instantiation block cut the parcel into.

    Both halves build now. The split survives because it is what `dealing_order()`
    keeps: the first half carries the sequence numbers its roofs were dealt, baked and
    reviewed on, and a released slot may not take one of them.
    """
    first, released = [], []
    for row in recipe["placements"]:
        (first if float(row["center_local_enu_m"][0]) >= WEST_TERRAIN_LIMIT_E
         else released).append(row)
    return first, released


def dealing_order(recipe: dict) -> list[dict]:
    """Every placement, in the order `seq` is dealt over.

    Recipe order within each half, the half built under the hold first. Sorting the
    parcel by easting or by id instead would renumber the twenty committed roofs and
    redeal their finish, roof condition and age state for no reason but the arrival of
    their neighbours.
    """
    first, released = split_placements(recipe)
    return first + released


def records_from_inputs() -> list[dict]:
    inventory, recipe, datum = load(INVENTORY_PATH), load(RECIPE_PATH), load(DATA / "datum.json")
    rows = dealing_order(recipe)
    records = [make_record(row, i + 1, datum) for i, row in enumerate(rows)]
    deal_siding(records)
    validate(records, rows, inventory, recipe, datum)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="report missing, changed, or extra West outputs")
    args = parser.parse_args()
    recipe = load(RECIPE_PATH)
    first, released = split_placements(recipe)
    records = records_from_inputs()
    # Every slot is derived, dealt and validated; the five the corporate boundary cannot
    # decide are then withheld from the tree. Deriving them and dropping them — rather
    # than never dealing them — is what keeps the other fifty byte-identical: `seq`, and
    # with it every roof's finish, condition and age state, is dealt over the whole
    # parcel exactly as the terrain hold dealt it.
    records = [r for r in records if r["id"] not in HELD_IDS]
    expected = {f"{r['id']}.json" for r in records}
    drift = []
    for record in records:
        path = STRUCTURES / f"{record['id']}.json"
        text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists():
                drift.append(f"{path.relative_to(ROOT)} is missing")
            elif path.read_text(encoding="utf-8") != text:
                drift.append(f"{path.relative_to(ROOT)} has drifted from the West recipe")
        else:
            path.write_text(text, encoding="utf-8")
    extras = sorted(p.name for p in STRUCTURES.glob(f"{PREFIX}*.json") if p.name not in expected)
    drift.extend(f"data/structures/{name} is outside the West parcel" for name in extras)
    if drift:
        print("WEST INFILL DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    principal = sum(1 for r in records
                    if r["reconstruction"]["inventory_class"] == "principal_functional")
    mode = "verified" if args.check else "generated"
    print(f"{mode} {len(records)} inferred anonymous West Division records "
          f"({principal} principal, {len(records) - principal} ancillary); "
          f"{len(first)} dealt under the retired terrain hold and "
          f"{len(released) - len(BOUNDARY_HOLDS)} released onto the ground west of "
          f"E {WEST_TERRAIN_LIMIT_E:g} m; {len(BOUNDARY_HOLDS)} held on the corporate "
          f"boundary's extrapolated west leg (T-1444, T-1490)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
