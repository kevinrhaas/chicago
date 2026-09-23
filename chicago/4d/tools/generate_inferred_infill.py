#!/usr/bin/env python3
"""Generate the explicitly conjectural phase-one anonymous building parcel.

The authored inputs are the 665-roof ledger and the compact parcel recipe under
``data/reconstruction``.  The outputs are ordinary one-file-per-structure records,
so the existing schema, confidence, liberty, scene and terrain gates apply to them.

This tool deliberately does not make the parcel authoritative.  Every individual
presence, footprint and position is conjectural; only the aggregate family bands
and district programme are inferred from the owner-supplied specification.
"""

from __future__ import annotations

import argparse
import hashlib
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
PARCEL_PATH = DATA / "reconstruction" / "1835_phase1_south_mixed_blocks.json"
SOURCE_ID = "owner_chicago_1835_reconstruction_spec_2026"
PHASE_ID = "inferred_1835"
PREFIX = "recon_1835_south_"
# This parcel's own name, as `roof_form.AWAITING_BAKE` keys it. It is passed rather than
# inferred so a hold is looked up under a string this file states about itself. The table
# is empty today (T-0212); the name is what makes it possible to fill again.
PARCEL = "generate_inferred_infill.py"

sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

# Phase two of the inferred-residents programme adopts some of these anonymous roofs
# as the dwellings and shops of inferred households (docs/ROADMAP.md K1). The link is
# data, not a hand edit: this generator still re-derives every record byte for byte,
# and the occupancy block arrives from the household programme's ledger.
from band_notes import split_notes  # noqa: E402
from roof_form import note_refusal, roof_kind  # noqa: E402
# THE ONE SAMPLING RULE (T-0273). The eave and the pitch used to be retyped here, one
# constant per family, and ten of them sat outside the very band their own note cites.
# They are asked of the family's authored band now, exactly as the block parcel asks
# (T-0144, T-0145) and the north parcel after it — same module, so a value and the gate
# that tests it cannot be reading two different bands.
from family_bands import (eave_floor, eave_for_ridge, eave_limits,  # noqa: E402
                          families, pitch_deg, wall_height_m)
from ridge_model import ridge_run_m  # noqa: E402
from inferred_occupancy import occupancy  # noqa: E402
# Every committed footprint in this scene's local frame, so a frontage run can butt
# onto a building this parcel did not write — read from the module the occupancy and
# separation gates read, so a run and a gate cannot be looking at two towns.
from plat_occupancy import footprints  # noqa: E402
# The face of a committed block — the line a party-line row stands on — is one
# rule in one module, imported by both generators that build a row (T-0078).
from block_faces import extent, face_frame as block_face, project  # noqa: E402
# T-0112. The clapboard stock is dealt at the end of the parcel, AFTER the frontage
# runs move their buildings: it is the one form value that depends on where a
# building's neighbours stand. See tools/siding_stock.py.
from siding_stock import deal_records as deal_siding  # noqa: E402

OCCUPANCY = occupancy()
# The crosswalk's per-family bands, read once. `family_bands` is the only reader of that
# file, so this parcel and every gate that measures it see the same eave, roof and ridge
# columns.
FAMILY_BANDS = families()


def load(path: Path):
    return json.loads(path.read_text())


def stable_fraction(key: str, slot: int) -> float:
    raw = hashlib.sha256(f"{key}:{slot}".encode()).digest()
    return int.from_bytes(raw[:4], "big") / 0xFFFFFFFF


INVENTED_NOTE = (
    "INVENTED, NOT DERIVED. A typology value from the reconstruction spec, not a reading "
    "of evidence about this particular building — there is no particular building. The "
    "spec is cited because the invention is bounded by it. "
)


def inferred(value, reason: str):
    # Named `inferred`, and it used to write "derived". That one-word mismatch is why
    # buildings that never existed rendered solid in the confidence view.
    return {
        "value": value,
        "confidence": "reconstructed",
        "sources": [SOURCE_ID],
        "note": INVENTED_NOTE + reason,
    }


def finish_for(key: str) -> tuple[str, str]:
    # Weighted toward unpainted material, matching the specification's 55% target.
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


def dimensions(family: str, seq: int, bands: dict[str, list[float]]) -> tuple[float, float]:
    lo_w, lo_d, hi_w, hi_d = bands[family]
    key = f"{family}:{seq}"
    width_ft = lo_w + (hi_w - lo_w) * (.18 + .70 * stable_fraction(key, 1))
    depth_ft = lo_d + (hi_d - lo_d) * (.15 + .72 * stable_fraction(key, 2))
    width, depth = width_ft * .3048, depth_ft * .3048
    # The current frame dwelling generator is eaves-front. D5/D6 can reach a
    # gable-front proportion at the edge of their bands, so keep this first parcel
    # inside the implemented family while the eventual D5/D6 archetypes are built.
    if family.startswith("D") and family not in ("D1", "D2") and depth > width * 1.46:
        width = min(hi_w * .3048, depth / 1.46)
    return round(width, 3), round(depth, 3)


def archetype_for(family: str) -> str:
    if family == "D1":
        return "log_dwelling"
    if family == "D2" or family.startswith(("W", "A")) or family == "F1":
        return "outbuilding"
    if family.startswith("D"):
        return "frame_dwelling"
    return "frame_storefront"


def function_for(family: str) -> str:
    return {
        "D1": "older log dwelling", "D2": "rough plank dwelling or shanty",
        "D3": "one-room frame cottage", "D4": "two-room frame cottage",
        "D5": "deep-plan frame cottage", "D6": "one-and-a-half-story frame cottage",
        "D7": "small two-story frame house", "C1": "small shop or office",
        "C2": "store-residence", "C3": "narrow two-story store",
        "W1": "blacksmith shop", "W2": "carpenter or joiner shop",
        "W3": "cooper, wagon, or wheelwright shop", "W4": "small artisan shop",
        "F1": "freight or storage shed", "F2": "narrow two-story warehouse",
        "A1": "stable", "A2": "barn or carriage shed", "A3": "privy",
        "A4": "woodshed or storage shed", "A5": "small utility building",
    }[family]


def band_note(family: str) -> str:
    """The sentence that defends every invented form value, and it is a source claim.

    Kept in one place because K33 restricts where it may be attached, and a claim that
    is authored in one file and audited in another drifts. See tools/band_notes.py.
    """
    return (f"Type-level choice within the {family} band in the 2026 reconstruction "
            "specification; it is not evidence for this anonymous instance.")


def form_for(family: str, seq: int, finish: str, width: float, depth: float) -> dict:
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
        split_notes(_form_body(family, seq, finish, width, depth), family,
                    band_note(family)),
        family, width, depth)


def door_kind(family: str) -> str:
    """Which door an outbuilding family carries, and it is asked BEFORE the eave.

    The eave floor depends on it — a wagon door needs a metre more wall than a man
    door — so the choice that used to sit halfway down the outbuilding tail is hoisted
    to where `eave_floor` can be asked about it.
    """
    if family in ("W1", "W3", "F1", "A2"):
        return "wagon"
    if family in ("W2", "A1"):
        return "stable"
    return "man"


def storeys_for(family: str) -> float:
    """The storey count this parcel deals a family — unchanged, and hoisted.

    It is hoisted because `family_bands.eave_limits` asks the ARCHETYPE what wall it
    will carry AT A STOREY COUNT, and the count was authored twice inside the branches
    below. The values are exactly the ones those branches wrote.
    """
    if family == "D1":
        return 1
    if family.startswith("D") and family != "D2":
        return 1.5 if family == "D6" else (2 if family == "D7" else 1)
    if family.startswith(("C", "F")) and family != "F1":
        return 2 if family in ("C3", "F2") else 1
    return 1


def _pitch_default(family: str) -> float:
    """The generator's own type value, which is what a family authoring no band gets.

    Six of the families this parcel deals write a roof line with no rise:run in it —
    "gable or shed" — and `family_bands.pitch_deg` returns this unchanged for them, so
    the sampler invents no claim where the specification makes none.
    """
    if family == "D1":
        return 38.0
    if family.startswith("D") and family != "D2":
        return 44.0 if family == "D6" else 38.0
    if family.startswith(("C", "F")) and family != "F1":
        return 34.0
    return 18.0 if roof_kind(family, PARCEL)[0] == "shed" else 32.0


def _form_body(family: str, seq: int, finish: str, width: float, depth: float) -> dict:
    why = band_note(family)
    key = f"{family}:{seq}"
    spec = FAMILY_BANDS[family]
    construction = "balloon_frame" if stable_fraction(key, 6) < .52 else "braced_frame"

    # THE EAVE AND THE PITCH, T-0273, and it is the repair T-0144 and T-0145 already
    # made on the block parcel arriving in the parcel that needed it next. This file
    # dealt one retyped constant per family — 2.75 m to the whole outbuilding tail,
    # 3.25 m to every one-storey shop, 34 deg to every C and F roof — and a constant is
    # a claim of uniformity no source makes. Worse, ten of them sat OUTSIDE the very
    # band the note attached to them cites: A4's 2.75 m against an authored 6-8 ft,
    # C3's 5.35 m against 18-22 ft, D2 falling past the D branch into the tail
    # altogether. So the value is drawn from the family's own authored band instead,
    # on the same stable key the footprint is drawn on.
    #
    # Sampling adds variety, not knowledge. Every value still grades at the bottom
    # tier and the note still says the band is a typology and not evidence about this
    # building; what changes is that the band is used as the range it was authored as
    # instead of being collapsed to a point.
    #
    # WHICH ROOF A FAMILY GETS is `tools/roof_form.py`'s answer and no longer this
    # file's (T-0179). This parcel was the one held back from part of that rule — it had
    # retyped the shed set without A5 and one A5 roof stood on the difference, which
    # could not move without a bake. T-0212 baked it, so the hold is gone and this call
    # now returns the same shed every other parcel deals an A5. The parcel name is still
    # passed because the mechanism it reads stays: see `roof_form.AWAITING_BAKE`.
    roof, gable_front = roof_kind(family, PARCEL)
    stories = storeys_for(family)
    archetype = archetype_for(family)
    run = ridge_run_m(archetype, roof, width, depth, gable_front)
    # The band is bounded at BOTH ends by what the archetype will actually build, and
    # both limits are ASKED OF IT rather than retyped: `eave_floor` for the door a
    # family's wall has to header, `eave_limits` for the storey-height ceiling
    # `frame_dwelling` publishes. This parcel's tail is exactly why that matters — it
    # deals 2.75 m for a man door where the west parcel deals 2.05 m for the same door,
    # two copies of one constant that had already drifted apart.
    arch_lo, arch_hi = eave_limits(archetype, stories)
    floor, ceiling = max(eave_floor(family, door_kind(family)), arch_lo), arch_hi
    # ...and the family's own RIDGE band bounds it once more (T-0148): a low draw can
    # leave no pitch inside the family's band able to reach the ridge the same entry
    # authors, and the eave is held at the nearest value in its OWN band that can. A
    # draw that already reaches it is returned untouched, to the bit.
    wall = eave_for_ridge(wall_height_m(family, spec["eave_ft"], key, floor, ceiling),
                          family, spec["eave_ft"], spec.get("roof"),
                          spec.get("ridge_ft"), run, _pitch_default(family),
                          key, floor, ceiling)

    def pitch() -> float:
        # A pitch and a footprint together make the RIDGE, and the crosswalk authors a
        # band for that too, so the sampler is constrained by it — which needs the run
        # the roof climbs, and that is the archetype's, not the family's.
        return pitch_deg(family, spec.get("roof"), key, _pitch_default(family),
                         eave_m=wall, run_m=run, ridge_ft=spec.get("ridge_ft"))

    if family == "D1":
        return {
            "stories": inferred(stories, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why),
            "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred("log", why), "loft": inferred(True, why),
            "chimneys": inferred(1, why),
        }

    if family.startswith("D") and family != "D2":
        bays = 5 if family == "D7" else (3 if width >= 5.4 else 2)
        plan = "centre_passage" if family == "D7" else ("single_pen" if family == "D3" else "hall_parlour")
        result = {
            "stories": inferred(stories, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why),
            "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred(construction, why), "plan": inferred(plan, why),
            "bays": inferred(bays, why), "chimneys": inferred(1, why),
            "paint": inferred(finish, why),
        }
        # Slot 10, not slot 7: `family_bands.pitch_deg` draws on 7, and two decisions
        # sharing a slot would make a house's porch a function of its roof pitch. The
        # block parcel moved this same draw for this same reason.
        if stable_fraction(key, 10) < .58:
            result["porch"] = inferred("stoop", why)
        return result

    if family.startswith(("C", "F")) and family != "F1":
        return {
            "stories": inferred(stories, why),
            "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why),
            "roof_pitch_deg": inferred(pitch(), why),
            "gable_front": inferred(family in ("C1", "C2", "C3"), why),
            "construction": inferred(construction, why),
            "cladding": inferred("clapboard" if family != "F2" else "vertical_board", why),
            "paint": inferred(finish, why), "loft": inferred(family == "C2", why),
            "chimneys": inferred(1 if not family.startswith("F") else 0, why),
            "shopfront": inferred(not family.startswith("F"), why),
            "goods_door": inferred(True, why), "goods_door_side": inferred("end", why),
        }

    door = door_kind(family)
    material = "plank"
    if family == "A1" and min(width, depth) >= 2.2:
        material = "log"
    elif family in ("A2", "W2"):
        material = "light_frame"
    return {
        "wall_height_m": inferred(wall, why), "roof_type": inferred(roof, why),
        "roof_pitch_deg": inferred(pitch(), why),
        "construction": inferred(material, why), "door": inferred(door, why),
        "door_side": inferred("front", why),
        "loft": inferred(family in ("W2", "A1", "A2"), why),
        "board_gap_m": inferred(.012, why), "paint": inferred(finish, why),
    }


def block_name(e: float) -> str:
    if e < 330: return "Franklin and Wells"
    if e < 450: return "Wells and LaSalle"
    if e < 575: return "LaSalle and Clark"
    if e < 700: return "Clark and Dearborn"
    return "Dearborn and State"


def make_record(seq: int, family: str, e: float, n: float, row: dict,
                inventory: dict, datum: dict, frontage: dict | None = None) -> dict:
    sid = f"{PREFIX}{family.lower()}_{seq:03d}"
    width, depth = dimensions(family, seq, inventory["family_bands_ft"])
    jitter_e = (stable_fraction(sid, 3) - .5) * 1.2
    jitter_n = (stable_fraction(sid, 4) - .5) * 1.5
    rotation = round((stable_fraction(sid, 5) - .5) * 2.8, 2)
    local_e, local_n = round(e + jitter_e, 3), round(n + jitter_n, 3)
    finish_key, finish = finish_for(sid)
    ancillary = family.startswith("A")
    yard_group = row.get("yard_group")
    reconstruction = {
        "status": "inferred_anonymous", "family": family, "district": "south",
        "inventory_class": "ancillary" if ancillary else "principal_functional",
        "programme_phase": "phase1_south_mixed_blocks", "source_id": SOURCE_ID,
        "sequence": seq, "finish_key": finish_key,
        "roof_condition": ("fresh", "darkened", "patched", "weathered")[seq % 4],
        "age_state": ("new", "recent", "established", "older_frontier")[seq % 4],
    }
    if yard_group:
        reconstruction["yard_group"] = yard_group
    if frontage is not None:
        # Recorded on the record rather than only in the recipe, because the frontage
        # is the answer to "why does this building stand here" and a reader of the
        # record cannot open the recipe. `place_on_frontage` reads the private key
        # below and drops it; what survives into the file is this block.
        reconstruction["frontage"] = {
            "block": frontage["row"]["block"], "face": frontage["row"]["face"],
            "setback_m": frontage["row"]["setback_m"],
            "abuts": frontage["placement"].get("abut_west_of"),
            "why": frontage["row"]["why"],
        }

    blocks = block_name(local_e)
    location = f"Anonymous reconstructed roof in the South Division block between {blocks}, south of Lake Street"
    function = function_for(family)
    return {
        "id": sid,
        "name": f"Reconstructed {family} {function} #{seq:03d}",
        "archetype": archetype_for(family),
        "phases": [{
            "id": PHASE_ID,
            "documented_range": {
                "from": "1835-01-01", "to": "1835-12-31", "confidence": "reconstructed",
                "note": "This is an anonymous count-unit created to begin the July 1835 aggregate roof target. No evidence establishes that this particular building existed."
            },
            "position": {
                "utm_e": round(datum["origin_utm_e"] + local_e, 3),
                "utm_n": round(datum["origin_utm_n"] + local_n, 3),
                "rotation_deg": rotation, "symbolic_location": location,
                "confidence": "reconstructed",
                "note": "Interpretive lot placement inside a measured street grid. It preserves mixed-block spacing and open lots but is not a recovered parcel position. The whole footprint - not its centre - is tested against the platted street corridors of the K7 block grid, so no invented building of this parcel stands in the roadway; clearing the roadway is not the same as standing on a recovered lot.",
                "derivation": {"method": "not_derivable", "reason": "No parcel-by-parcel July 1835 roof register survives in the supplied evidence."}
            },
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"A {width:.2f} × {depth:.2f} m rectangle sampled deterministically inside the {family} family band; no individual dimensions are documented."
            },
            "form": form_for(family, seq, finish, width, depth),
            "change_note": "Reconstructed anonymous July 1835 infill. It may later be replaced by a named, better-evidenced roof through an explicit inventory substitution."
        }],
        "function": inferred(function, f"Assigned from the {family} production family to satisfy the aggregate South Division mix; no occupant or individual use is known."),
        **({"occupants": OCCUPANCY[sid]} if sid in OCCUPANCY else {}),
        "reconstruction": reconstruction,
        "research_note": "RECONSTRUCTED / GENERATED, NOT AN ATTESTED NAMED BUILDING. Family and aggregate district role follow the owner-supplied 2026 specification; exact presence, location, footprint, finish and instance-level form are interpretive.",
        "review_required": False
    }


def world_polygon(record: dict, datum: dict) -> list[tuple[float, float]]:
    """A record's footprint in local ENU metres, rotated as it is placed."""
    phase = record["phases"][0]
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def check_corridors(records: list[dict], datum: dict) -> None:
    """No anonymous roof of this parcel may stand in a platted street.

    ROADMAP K7 phase two. The grid report found four of these eight ancillary buildings
    inside a corridor and the generator had never asked - it tested nothing at all about
    where it put a roof. The question is asked through `tools/plat_corridors.py`, the same
    module `generate_plat_lots.py --report` and the household generator read, so the report
    that finds a problem and the gate that must satisfy it cannot answer differently.

    The test is on the FOOTPRINT, not the centre. A centre is one point and a building is a
    rectangle up to 11 m across, so a building can front a street with its centre clear of
    the corridor and half its depth inside it - which is exactly what the household parcel
    turned out to have been doing. The plat is the LEGAL corridor rather than the travelled
    way (L79 puts the visible tracks at 5.8-10.5 m inside 80 ft), and a real building did
    sometimes encroach; the Sauganash's first cabin is the standing reminder. But an
    ANONYMOUS COUNT-UNIT has nothing to encroach with. Its position is a band assignment,
    so standing in the road is a defect in this generator and nothing else can see it.
    """
    from plat_corridors import corridors, intrusion  # noqa: PLC0415
    lanes = corridors()
    for record in records:
        street, depth = intrusion(world_polygon(record, datum), lanes)
        if street:
            raise SystemExit(f"{record['id']} reaches {depth:.1f} m inside the platted "
                             f"{lanes[street]['name']} corridor")


# --------------------------------------------------------------------------
# the party-line frontage (T-0077)
# --------------------------------------------------------------------------
#
# The rows above are the parcel as it was first written: a shared northing and a
# list of eastings, each nudged by its own jitter. That is a DISTRIBUTION of roofs
# across a block, and it is the right shape for the interior of one. It is the
# wrong shape for a street front. The owner's screenshot of the Lake and Dearborn
# corner is the whole of the argument — the Tremont House standing alone on grass
# with four cottages seventeen to twenty-four metres behind the frontage — against
# a plate of that same corner showing buildings shoulder to shoulder on shared
# party lines, signboards across the fronts and plank walks below.
#
# So a placement may say instead that it stands ON a block face, and then it takes
# three things from the committed plat rather than from this file: the line it
# fronts, the bearing of that line, and where along it the building's east wall
# lands. Nothing here authors a coordinate — the face comes out of
# `data/traces/vectors/thompson_lots.json`, the same block boundary the lot grid
# and the corridor gate are derived from, and a run is anchored either on the
# block's own corner or on the wall of a building already standing on that face.
# A hand-typed northing beside the plat module is a second opinion about the same
# ground; that is the lesson `tools/generate_block_infill.py` was written on.
#
# The jitter goes with it, and deliberately. A party wall does not wander: two
# buildings that share one are the same wall, so a metre of scatter and a degree
# of yaw are exactly what makes a row read as detached cottages standing near each
# other. On a frontage placement the bearing IS the face's bearing and the offsets
# are zero.

LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"

FRONTAGE_NOTE = (
    "PARTY-LINE FRONTAGE, DERIVED FROM THE COMMITTED PLAT (T-0077). This building "
    "does not stand where a northing in the recipe put it: it stands on the {face} "
    "face of {block}, whose line and bearing are read from the block boundary in "
    "data/traces/vectors/thompson_lots.json — the same committed geometry the lot "
    "grid and the corridor gate are derived from. Its front wall is set {setback} m "
    "back from that lot line, the alignment the two frontage buildings already "
    "standing on this face use, and its east wall is fixed by {anchor}. The bearing "
    "is the face's own, and this placement carries none of the jitter the parcel's "
    "interior rows carry, because a shared party wall is one wall and cannot wander. "
    "WHAT IS INVENTED IS STILL EVERYTHING THAT MATTERS: that a building stood here "
    "at all, which building it was, and that these particular units stood shoulder "
    "to shoulder. What the plate supports is the TREATMENT — a continuous storefront "
    "row on the town's principal street rather than detached cottages set back on "
    "grass — and the treatment is what this placement takes from it. Standing on a "
    "derived block face is not standing on a recovered lot."
)


def face_frame(block_id: str, face: str) -> dict:
    """This block's face, out of the committed plat grid.

    The arithmetic moved to `tools/block_faces.py` for T-0078, which needed the same
    answer inside the platted-block generator; a second copy of it beside this one
    would be a second opinion about the same ground. Nothing about the frames this
    returns changes — the module is the same rule, imported instead of retyped.
    """
    grid = load(LOTS_PATH)
    block = next((b for b in grid["blocks"] if b["id"] == block_id), None)
    if block is None:
        raise SystemExit(f"{block_id} is not a block of the committed plat grid")
    return block_face(block, face)


def _project(frame: dict, point: tuple[float, float]) -> tuple[float, float]:
    return project(frame, point)


def _extent(frame: dict, polygon: list[tuple[float, float]]) -> tuple[float, float]:
    return extent(frame, polygon)


def place_on_frontage(records: list[dict], parcel: dict, datum: dict) -> None:
    """Move every placement that declared a block face onto that face.

    Anchors resolve in passes because a run is a chain: the corner unit is fixed by
    the block's own corner, and each unit west of it by the wall of the one before.
    An anchor may also name a building this parcel did not write, which is how a run
    butts onto a frontage that is already standing.
    """
    pending = {r["id"]: r for r in records if r.get("_frontage")}
    if not pending:
        return
    mine = {r["id"] for r in records}
    committed = dict(footprints(datum, exclude=mine))
    frames: dict[tuple[str, str], dict] = {}
    resolved: dict[str, list[tuple[float, float]]] = {}

    while pending:
        progressed = False
        for sid, record in list(pending.items()):
            spec = record["_frontage"]
            row = spec["row"]
            key = (row["block"], row["face"])
            frame = frames.setdefault(key, face_frame(*key))
            anchor = spec["placement"]
            if "corner" in anchor:
                if anchor["corner"] != "east":
                    raise SystemExit(f"{sid}: only the east corner anchors a run today")
                east = frame["length"] - float(anchor.get("clear_m", 0.0))
                described = (f"the block's own east corner, {anchor.get('clear_m', 0.0):.1f} m "
                             f"clear of the platted corridor")
            else:
                target = anchor.get("abut_west_of")
                if target is None:
                    raise SystemExit(f"{sid}: a frontage placement anchors on a corner "
                                     f"or abuts a named building")
                polygon = resolved.get(target) or committed.get(target)
                if polygon is None:
                    if target in mine:
                        continue  # its own anchor has not been placed yet
                    raise SystemExit(f"{sid}: nothing in the dataset is called {target}")
                east = _extent(frame, polygon)[0]
                described = f"the west wall of {target}, which it shares a party line with"

            phase = record["phases"][0]
            polygon = phase["footprint"]["polygon"]
            width = max(p[0] for p in polygon) - min(p[0] for p in polygon)
            depth = max(p[1] for p in polygon) - min(p[1] for p in polygon)
            setback = float(row["setback_m"])
            # The footprint's (0, 0) corner, which is what the GLB contract anchors
            # on: walk back from the east wall along the face, then in from the face
            # line by the setback and the building's own depth.
            base = (frame["origin"][0] + frame["along"][0] * (east - width)
                    + frame["outward"][0] * (-setback - depth),
                    frame["origin"][1] + frame["along"][1] * (east - width)
                    + frame["outward"][1] * (-setback - depth))
            local_e, local_n = round(base[0], 3), round(base[1], 3)
            position = phase["position"]
            position["utm_e"] = round(datum["origin_utm_e"] + local_e, 3)
            position["utm_n"] = round(datum["origin_utm_n"] + local_n, 3)
            position["rotation_deg"] = frame["bearing"]
            position["symbolic_location"] = (
                f"Anonymous reconstructed roof standing on the {row['face']} frontage of "
                f"the South Division block between {block_name(local_e)}, in the "
                f"party-line row at Lake and Dearborn")
            position["note"] = FRONTAGE_NOTE.format(
                face=row["face"], block=row["block"], setback=f"{setback:.2f}",
                anchor=described)
            theta = math.radians(frame["bearing"])
            cos, sin = math.cos(theta), math.sin(theta)
            resolved[sid] = [(local_e + u * cos + v * sin, local_n - u * sin + v * cos)
                             for u, v in polygon]
            del pending[sid]
            progressed = True
        if not progressed:
            raise SystemExit("a frontage run anchors on itself: "
                             + ", ".join(sorted(pending)))

    for record in records:
        record.pop("_frontage", None)


def check_frontage(records: list[dict], parcel: dict, datum: dict) -> None:
    """A row is a row: on the line, in order, and touching.

    Three assertions, because each of the three is a way the row stops being one and
    none of them is visible in a diff of coordinates. The front walls sit on one line
    to the millimetre or the street wall steps; a run's units are in the order the
    recipe deals them or "west of" means nothing; and a party line is a shared wall,
    so a gap inside a run is a defect while a gap BETWEEN runs is the gangway the
    recipe asked for and says why.
    """
    placed = [r for r in records if r["reconstruction"].get("frontage")]
    if not placed:
        return
    by_face: dict[tuple[str, str], list[dict]] = {}
    for record in placed:
        f = record["reconstruction"]["frontage"]
        by_face.setdefault((f["block"], f["face"]), []).append(record)
    for key, group in by_face.items():
        frame = face_frame(*key)
        setback = {r["reconstruction"]["frontage"]["setback_m"] for r in group}
        if len(setback) != 1:
            raise SystemExit(f"{key[0]}: the {key[1]} frontage is set back by "
                             f"{sorted(setback)} m — a street wall is one line")
        for record in group:
            offs = [_project(frame, p)[1]
                    for p in world_polygon(record, datum)]
            if abs(max(offs) + float(next(iter(setback)))) > 0.005:
                raise SystemExit(f"{record['id']} fronts {max(offs):.3f} m off the "
                                 f"{key[1]} face of {key[0]}, not its stated setback")
        chained = {r["id"]: r["reconstruction"]["frontage"].get("abuts")
                   for r in group}
        spans = {r["id"]: _extent(frame, world_polygon(record=r, datum=datum))
                 for r in group}
        for sid, target in chained.items():
            if not target or target not in spans:
                continue
            gap = spans[target][0] - spans[sid][1]
            if abs(gap) > 0.005:
                raise SystemExit(f"{sid} stands {gap:.3f} m from the party line it "
                                 f"shares with {target}")


def validate_programme(inventory: dict, parcel: dict, records: list[dict]) -> None:
    if sum(inventory["family_targets"].values()) != inventory["targets"]["roof_total"]:
        raise SystemExit("family targets do not sum to the authored roof target")
    matrix_total = sum(v["total"] for v in inventory["district_group_matrix"].values())
    if matrix_total != inventory["targets"]["roof_total"]:
        raise SystemExit("district/group matrix does not sum to the authored roof target")
    for district, row in inventory["districts"].items():
        total = sum(v[district] for v in inventory["district_group_matrix"].values())
        if total != row["target"]:
            raise SystemExit(f"{district} matrix column is {total}, expected {row['target']}")
    principal = sum(1 for r in records if r["reconstruction"]["inventory_class"] == "principal_functional")
    ancillary = len(records) - principal
    if (len(records), principal, ancillary) != (48, parcel["principal_functional"], parcel["ancillary"]):
        raise SystemExit(f"phase-one parcel counts are {(len(records), principal, ancillary)}, expected (48, 40, 8)")
    counts = Counter(r["reconstruction"]["family"] for r in records)
    for family, count in counts.items():
        if count > inventory["family_targets"][family]:
            raise SystemExit(f"phase-one {family} count {count} exceeds programme target")

    # Prove each record resolves through the current archetype before it is written.
    for rec in records:
        module = importlib.import_module(f"archetypes.{rec['archetype']}_params")
        module.from_phase(rec["phases"][0])


def records_from_inputs() -> list[dict]:
    inventory, parcel, datum = load(INVENTORY_PATH), load(PARCEL_PATH), load(DATA / "datum.json")
    records = []
    for row in parcel["rows"]:
        frontage_row = row.get("frontage")
        for placement in row["placements"]:
            e, family = placement[0], placement[1]
            # A third element says this placement stands on a block face instead of on
            # the row's northing. It is deliberately a per-placement opt-in: the row's
            # own eastings still fix the SEQUENCE, so moving four buildings onto a
            # frontage renames nothing and re-deals no dimensions — every id, band and
            # baked mesh in the parcel is the one it was.
            spec = placement[2] if len(placement) > 2 else None
            if spec is not None and frontage_row is None:
                raise SystemExit(f"{row['id']}: a placement stands on a block face but "
                                 f"the row declares no `frontage`")
            frontage = {"row": frontage_row, "placement": spec} if spec else None
            record = make_record(len(records) + 1, family, float(e),
                                 float(row["local_n"]), row, inventory, datum, frontage)
            if frontage is not None:
                record["_frontage"] = frontage
            records.append(record)
    place_on_frontage(records, parcel, datum)
    deal_siding(records)
    validate_programme(inventory, parcel, records)
    check_frontage(records, parcel, datum)
    check_corridors(records, datum)
    return records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    records = records_from_inputs()
    drift = []
    for rec in records:
        path = STRUCTURES / f"{rec['id']}.json"
        text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists():
                drift.append(f"{path.relative_to(ROOT)} is missing")
            elif path.read_text() != text:
                drift.append(f"{path.relative_to(ROOT)} has drifted from the parcel recipe")
        else:
            path.write_text(text)
    if drift:
        print("INFERRED INFILL DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    mode = "verified" if args.check else "generated"
    print(f"{mode} {len(records)} inferred anonymous South Division records (40 principal, 8 ancillary)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
