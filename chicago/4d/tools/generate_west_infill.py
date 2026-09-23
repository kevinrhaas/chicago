#!/usr/bin/env python3
"""Generate the anonymous West Division parcel west of Wolf Point.

The authored recipe (`data/reconstruction/1835_phase2_west_wolf_point_approaches.json`)
fixes an aggregate mix and a review layout, not fifty-five recovered buildings. Every
generated instance therefore says, in machine-readable and visitor-facing fields, that
its presence, position and footprint are conjectural.

**Only part of the parcel is emitted, and that is the recipe's own instruction.** Its
`terrain_and_hydrology_gate` blocks any placement whose centre lies west of local
E -300 m until the heightfield, collision surface, vegetation sampler, minimap and
water mask all share the extended box out to E -700 m. The committed terrain still
stops at E -320 m, so 35 of the 55 placements are held and 20 are built. That is not a
compromise to be tidied away later: a roof west of the modelled ground would stand on
nothing, sample no terrain, and the ground-contact gate would have no surface to check
it against. The held slots keep their ids and their family allocation so the day the
ground arrives they instantiate unchanged.

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

# The recipe's own instantiation block. Placements at or west of this line wait for
# the extended terrain box; see the module docstring.
WEST_TERRAIN_LIMIT_E = -300.0

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
from family_bands import (eave_floor, eave_for_ridge, eave_limits,  # noqa: E402
                          families, pitch_deg, wall_height_m)
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
    "D1": "older log dwelling", "D2": "rough plank dwelling or shanty",
    "D3": "one-room frame cottage", "D4": "two-room frame cottage",
    "D5": "deep-plan frame cottage", "D6": "one-and-a-half-story frame cottage",
    "D7": "small two-story frame house", "H1": "small boarding house",
    "H2": "medium boarding house", "C1": "small shop or office",
    "C2": "store-residence", "W1": "blacksmith shop",
    "W2": "carpenter or joiner shop",
    "W3": "cooper, wagon or wheelwright shop", "W4": "small artisan shop",
    "W5": "large workshop", "F1": "freight or storage shed",
    "A1": "stable", "A2": "barn or carriage shed", "A3": "privy",
    "A4": "woodshed or storage shed", "A5": "small utility building",
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
        "loft": inferred(family in ("W2", "W3", "W5", "A1", "A2"), why),
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
STREET_ADJUSTMENTS = {
    3: (4.50, 0.00),    # Clinton Street, 4.3 m in
    6: (-1.25, -2.17),  # Lake Street, 2.2 m in
    8: (-6.40, 1.13),   # Clinton Street, 6.3 m in
    11: (10.00, 0.00),  # Clinton Street, 9.5 m in
    14: (12.00, 0.00),  # Clinton Street, 11.7 m in
    18: (-9.36, 1.65),  # Clinton Street, 9.1 m in
    19: (1.39, 7.88),   # Randolph Street, 7.8 m in
    20: (8.03, 9.58),   # Randolph Street, 9.5 m in
}


def make_record(row: dict, seq: int, datum: dict) -> dict:
    sid = f"{PREFIX}{row['id'].split('_')[-1]}"
    de, dn = STREET_ADJUSTMENTS.get(seq, (0.0, 0.0))
    center_e = float(row["center_local_enu_m"][0]) + de
    center_n = float(row["center_local_enu_m"][1]) + dn
    width_ft, depth_ft = (float(v) for v in row["footprint_ft"])
    bearing = float(row["rotation_deg"])
    width, depth = round(width_ft * .3048, 3), round(depth_ft * .3048, 3)
    local_e, local_n = footprint_origin(center_e, center_n, width, depth, bearing)
    family = row["family"]
    finish_key, paint = finish_for(seq)
    function = FUNCTIONS[family]
    where = CLUSTER_PLACE.get(row["cluster"], "the West Division approaches")
    setback = (f" Set back {math.hypot(de, dn):.1f} m from the recipe coordinate, which "
               "placed it inside a platted street corridor; the move is well inside the "
               "±20 m uncertainty the recipe states for its own layout controls."
               if de or dn else "")
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
        "id": sid, "name": f"Reconstructed {family} {function} #{seq:03d}",
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
                "note": f"A {width_ft:g} × {depth_ft:g} ft rectangle assigned by the reconstruction recipe within the {family} family band; no individual dimensions are documented."
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


def validate(records: list[dict], built_rows: list[dict], held: list[dict],
             inventory: dict, recipe: dict, datum: dict) -> None:
    totals = recipe["roof_totals"]
    if len(records) + len(held) != totals["all"]:
        raise SystemExit(f"West recipe accounts for {len(records) + len(held)} roofs, "
                         f"expected {totals['all']}")

    # The built and held halves together must still be the recipe's mix: holding slots
    # back for terrain is not licence to quietly change what the parcel is.
    all_families = Counter(r["reconstruction"]["family"] for r in records)
    all_families.update(p["family"] for p in held)
    if all_families != Counter(recipe["family_totals"]):
        raise SystemExit(f"West family mix drifted: {dict(all_families)}")
    for family, count in all_families.items():
        if count > inventory["family_targets"][family]:
            raise SystemExit(f"West {family} count {count} exceeds programme target")

    # Nothing emitted may sit in the blocked box, and nothing held may sit outside it.
    # The rule is written about placement CENTRES, so it is asked of centres — a
    # footprint corner is a couple of metres further out and answering with one would
    # hold back a slot the recipe permits. That the whole FOOTPRINT is on modelled
    # ground is a separate and stricter question, and `field.covers()` below asks it.
    for row, record in zip(built_rows, records):
        de, dn = STREET_ADJUSTMENTS.get(record["reconstruction"]["sequence"], (0.0, 0.0))
        if float(row["center_local_enu_m"][0]) + de < WEST_TERRAIN_LIMIT_E:
            raise SystemExit(f"{record['id']} sits west of E {WEST_TERRAIN_LIMIT_E:g} m, "
                             "which the recipe's terrain gate blocks")
    for row in held:
        if float(row["center_local_enu_m"][0]) >= WEST_TERRAIN_LIMIT_E:
            raise SystemExit(f"{row['id']} is inside the modelled box and should be built")

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
    build, held = [], []
    for row in recipe["placements"]:
        (build if float(row["center_local_enu_m"][0]) >= WEST_TERRAIN_LIMIT_E
         else held).append(row)
    return build, held


def records_from_inputs() -> list[dict]:
    inventory, recipe, datum = load(INVENTORY_PATH), load(RECIPE_PATH), load(DATA / "datum.json")
    build, held = split_placements(recipe)
    records = [make_record(row, i + 1, datum) for i, row in enumerate(build)]
    deal_siding(records)
    validate(records, build, held, inventory, recipe, datum)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="report missing, changed, or extra West outputs")
    args = parser.parse_args()
    recipe = load(RECIPE_PATH)
    _, held = split_placements(recipe)
    records = records_from_inputs()
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
          f"{len(held)} held for terrain west of E {WEST_TERRAIN_LIMIT_E:g} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
