#!/usr/bin/env python3
"""Generate the bounded, anonymous 60-roof North Division parcel.

The authored recipe fixes an aggregate mix and review layout, not sixty recovered
buildings.  Consequently every generated instance says, in machine-readable and
visitor-facing fields, that its presence, position and footprint are conjectural.

This generator intentionally uses only archetypes already implemented in the
repository.  H1 temporarily resolves through ``frame_dwelling`` while the larger
H2-H3 and I2 forms use generic rectangular ``frame_tavern`` massing; none of those
mappings claims that a boarding house was a tavern or a hall was an inn.
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
RECIPE_PATH = DATA / "reconstruction" / "1835_north_division_initial_parcel.json"
SOURCE_ID = "owner_chicago_1835_reconstruction_spec_2026"
PHASE_ID = "inferred_1835"
PROGRAMME_PHASE = "phase2_north_division_initial"
PREFIX = "recon_1835_north_"

sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

# Phase two of the inferred-residents programme adopts some of these anonymous roofs
# as the dwellings and shops of inferred households (docs/ROADMAP.md K1). The link is
# data, not a hand edit: this generator still re-derives every record byte for byte,
# and the occupancy block arrives from the household programme's ledger.
from band_notes import split_notes  # noqa: E402
# The one sampling rule, shared with the block parcel. This generator used to retype
# one width, one depth and one eave per family into Python, so its sixty roofs were
# twenty-four buildings stamped sixty times and seventeen of them stood outside the
# eave band their own note cited (ROADMAP T-V1). The band is now used as the range it
# was authored as.
from family_bands import (dimensions_m, eave_floor, eave_for_ridge,  # noqa: E402
                          families, pitch_deg, storeys, wall_height_m)
from ridge_model import ridge_run_m  # noqa: E402
from roof_form import note_refusal, roof_kind  # noqa: E402
from inferred_occupancy import occupancy  # noqa: E402
# T-0112. The clapboard stock is dealt HERE, at the end of the parcel, because it is
# the one form value that depends on where a building's neighbours stand — and the
# recipe is the only thing that knows the parcel whole. See tools/siding_stock.py.
from siding_stock import deal_records as deal_siding  # noqa: E402

OCCUPANCY = occupancy()
FAMILIES = families()


def spec_for(family: str) -> dict:
    spec = FAMILIES.get(family)
    if spec is None or not spec.get("band_ft"):
        raise SystemExit(f"the crosswalk authors no footprint band for family {family}; "
                         f"the North recipe cannot sample it")
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


FUNCTIONS = {
    "D1": "older log dwelling", "D2": "rough plank dwelling or shanty",
    "D3": "one-room frame cottage", "D4": "two-room frame cottage",
    "D5": "deep-plan frame cottage", "D6": "one-and-a-half-story frame cottage",
    "D7": "small two-story frame house", "H1": "small boarding house",
    "H2": "medium boarding house", "H3": "large boarding house",
    "C1": "small shop or office", "C2": "store-residence",
    "T1": "small inn or tavern", "W1": "blacksmith shop",
    "W2": "carpenter or joiner shop", "W5": "large workshop",
    "F1": "freight or storage shed", "I2": "schoolhouse or meeting hall",
    "A1": "stable", "A2": "barn or carriage shed", "A3": "privy",
    "A4": "woodshed or storage shed", "A5": "small utility building",
}


def finish_for(seq: int) -> tuple[str, str]:
    # A deterministic sequence weighted toward unpainted material.  ``finish_key``
    # is the inventory vocabulary; the second value is the current archetypes'.
    keys = ("fresh_timber", "weathered_timber", "fresh_timber", "whitewash",
            "weathered_timber", "red_oxide", "ochre", "mixed_patch")
    key = keys[(seq * 5) % len(keys)]
    paint = {"whitewash": "whitewash", "red_oxide": "red"}.get(key, "unpainted")
    return key, paint


def band_note(family: str) -> str:
    """The sentence that defends every invented form value, and it is a source claim.

    Kept in one place because K33 restricts where it may be attached, and a claim that
    is authored in one file and audited in another drifts. See tools/band_notes.py.
    """
    return (f"Type-level choice within the {family} band in the supplied reconstruction "
            "specification; it is not evidence for this anonymous North Division instance.")


def door_kind(family: str) -> str:
    """Which door the family's building carries — asked before the eave is sampled.

    The eave floor depends on it: a wagon door needs a metre more wall than a man
    door, and asking for the floor without naming the door is how a band gets sampled
    below what the archetype can build.
    """
    if family in ("W1", "W2", "W5", "F1", "A2"):
        return "wagon"
    return "stable" if family == "A1" else "man"


def form_for(family: str, spec: dict, key: str, seq: int, paint: str,
             archetype: str, width: float, depth: float) -> dict:
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
        split_notes(_form_body(family, spec, key, seq, paint, archetype, width, depth),
                    family, band_note(family)),
        family, width, depth)


# WHICH ROOF A FAMILY GETS is `tools/roof_form.py`'s answer and no longer this file's
# (T-0179). It was decided here and in four other parcels, as the same literal written
# five times, and the five had already drifted: three named A5 among the shed families
# and two did not, which is why one A5 stands on a gable beside three A5 sheds. The rule
# now has one home, and `tools/measure_ridge_reach.py` tests it against the ridge band
# every family authors, so a family cannot be dealt a form its own bands cannot carry.


def _pitch_default(family: str) -> float:
    """The generator's own type value, which is what a family authoring no band gets."""
    if family == "D1":
        return 35.0
    if family.startswith("D") and family != "D2" or family == "H1":
        return 42.0 if family in ("D6", "H1") else 38.0
    if family.startswith("C"):
        return 33.0
    if family.startswith("T") or family.startswith("I") or family in ("H2", "H3"):
        return 38.0
    return 18.0 if roof_kind(family)[0] == "shed" else 32.0


def _form_body(family: str, spec: dict, key: str, seq: int, paint: str,
               archetype: str, width: float, depth: float) -> dict:
    why = band_note(family)
    frame = "balloon_frame" if seq % 2 else "braced_frame"
    # The eave is drawn from the family's authored band, on the same stable key as the
    # footprint, instead of the single retyped figure that used to stand for the whole
    # family — which is what put seventeen of these sixty roofs outside the band their
    # own note cites. Sampling adds variety, not knowledge: every value still grades at
    # the bottom tier, and the note still says the band is a typology and not evidence
    # about this building.
    #
    # ...and it is then HELD inside the part of that band the family's ridge band can
    # actually be reached from (T-0148). Drawing the eave free and asking the pitch
    # alone to land the ridge is what left three A1 stables and an A4 shed here outside
    # a ridge band that is reachable at an eave their own family also authors — the
    # sampler was constraining one of its two free claims and making the other carry
    # the choice.
    roof_type, gable_front = roof_kind(family)
    run = ridge_run_m(archetype, roof_type, width, depth, gable_front)
    floor = eave_floor(family, door_kind(family))
    wall = eave_for_ridge(wall_height_m(family, spec["eave_ft"], key, floor),
                          family, spec["eave_ft"], spec.get("roof"),
                          spec.get("ridge_ft"), run, _pitch_default(family), key, floor)

    # THE PITCH, T-0145. The eave moved onto its band in the pass before this one and
    # the pitch was deliberately left behind, because a pitch is not a dimension that
    # stands on its own: it and the footprint together make the RIDGE, and the crosswalk
    # authors a band for that too. So the sampler is asked for a pitch inside the
    # family's `N:12-M:12` band that also lands the ridge inside the family's `ridge_ft`
    # — which needs the run the roof climbs, and that is the archetype's, not the
    # family's, so `ridge_model` is asked for it. A family whose roof line names no
    # pitch keeps the type default it always had, and `band_notes` already makes its
    # note say that is what it is.
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
        stories = 1.5 if family in ("D6", "H1") else (
            2 if family in ("D7", "H2", "H3") else 1)
        plan = "centre_passage" if family in ("D7", "H2", "H3") else (
            "single_pen" if family == "D3" else "hall_parlour")
        return {
            "stories": inferred(stories, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why), "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred(frame, why), "plan": inferred(plan, why),
            "bays": inferred(5 if family in ("D7", "H2", "H3") else 3, why),
            "chimneys": inferred(2 if family.startswith("H") else 1, why),
            "paint": inferred(paint, why),
        }

    if family.startswith("C"):
        return {
            "stories": inferred(1, why), "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why),
            "roof_pitch_deg": inferred(pitch(), why),
            "gable_front": inferred(True, why), "construction": inferred(frame, why),
            "cladding": inferred("clapboard", why), "paint": inferred(paint, why),
            "loft": inferred(family == "C2", why), "chimneys": inferred(1, why),
            "shopfront": inferred(True, why), "goods_door": inferred(True, why),
            "goods_door_side": inferred("end", why),
        }

    if family.startswith("T") or family.startswith("I") or family in ("H2", "H3"):
        # The I2 school/meeting-hall is a flagged generic block until a dedicated
        # institutional archetype exists; the function and research note stay I2.
        return {
            "stories": inferred(1 if family == "I2" else 2, why),
            "wall_height_m": inferred(wall, why),
            "roof_type": inferred("gable", why), "roof_pitch_deg": inferred(pitch(), why),
            "construction": inferred("braced_frame", why), "paint": inferred(paint, why),
            "gallery": inferred(False, why), "chimneys": inferred(1 if family == "I2" else 2, why),
        }

    door = door_kind(family)
    construction = "light_frame" if family in ("W2", "A1", "A2") else "plank"
    return {
        "wall_height_m": inferred(wall, why), "roof_type": inferred(roof_type, why),
        "roof_pitch_deg": inferred(pitch(), why),
        "construction": inferred(construction, why), "door": inferred(door, why),
        "door_side": inferred("front", why),
        # THE LOFT IS THE FAMILY'S TO AUTHOR, not this file's (T-0145). A retyped
        # tuple gave W5 a loft its `levels` never mentions — "1", flat — which is the
        # same retyping fault as the eave, one field over, and the band-claims gate
        # named it on `recon_1835_north_w5_040`. `family_bands.storeys` already reads
        # a loft out of the levels string for every other parcel; it reads it here now.
        "loft": inferred(storeys(spec["levels"], key)[1], why),
        "board_gap_m": inferred(.012, why), "paint": inferred(paint, why),
    }


def footprint_origin(center_e: float, center_n: float, width: float, depth: float,
                     bearing: float) -> tuple[float, float]:
    """Convert the recipe's centre anchor to the GLB contract's (0, 0) corner."""
    theta = math.radians(bearing)
    cos, sin = math.cos(theta), math.sin(theta)
    return (center_e - width * .5 * cos - depth * .5 * sin,
            center_n + width * .5 * sin - depth * .5 * cos)


# Slot 41's authored centre crosses the steep east-fringe ridge: its perimeter
# spans 1.43 m of relief, four times the walker's step tolerance.  The anonymous
# placement has a 25 m review radius, so move its centre 7.1 m to nearby dry,
# coherent ground rather than emit another visible ground layer or bury the walls.
TERRAIN_ADJUSTMENTS = {41: (-5.0, 5.0)}


def make_record(row: list, datum: dict) -> dict:
    seq, suffix, center_e, center_n, family, inventory_class, width_ft, depth_ft, bearing, cluster, yard_group = row
    sid = f"{PREFIX}{suffix}"
    spec = spec_for(family)
    de, dn = TERRAIN_ADJUSTMENTS.get(seq, (0.0, 0.0))
    center_e, center_n = float(center_e) + de, float(center_n) + dn
    # The recipe's `width_ft`/`depth_ft` columns hold ONE rectangle per family — a
    # production-layout figure, not a per-building one — so the parcel stood as
    # twenty-four massings dealt sixty times. The rectangle is now drawn inside the
    # family's authored footprint band on a stable per-record key, by the same rule the
    # block parcel uses. The recipe columns stay as the layout control they always
    # were: `placement_constraints` measures its spacing against them.
    width, depth = dimensions_m(family, spec["band_ft"], sid)
    local_e, local_n = footprint_origin(center_e, center_n, width, depth, float(bearing))
    finish_key, paint = finish_for(seq)
    function = FUNCTIONS[family]
    adjusted = (f" Slot {seq} is shifted {math.hypot(de, dn):.1f} m within the recipe's "
                "25 m control radius so its entire perimeter meets one terrain surface."
                if de or dn else "")
    position_note = ("Interpretive placement within the reviewed North Division cluster. "
                     "The recipe coordinate is a production-layout control, not a recovered lot."
                     + adjusted)
    symbolic = (f"Anonymous reconstructed roof in North Division cluster {cluster}; "
                "between the north bank and Michigan Street")
    reconstruction = {
        "status": "inferred_anonymous", "family": family, "district": "north",
        "inventory_class": inventory_class, "programme_phase": PROGRAMME_PHASE,
        "source_id": SOURCE_ID, "sequence": int(seq), "finish_key": finish_key,
        "roof_condition": ("fresh", "darkened", "patched", "weathered")[seq % 4],
        "age_state": ("new", "recent", "established", "older_frontier")[seq % 4],
    }
    if yard_group:
        reconstruction["yard_group"] = yard_group
    mapping_note = (" H-family boarding-house massing currently uses a generic frame "
                    "dwelling/block archetype." if family.startswith("H") else
                    " I2 currently uses a generic rectangular frame block because no "
                    "institutional generator is implemented." if family == "I2" else "")
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
                "rotation_deg": float(bearing), "symbolic_location": symbolic,
                "confidence": "reconstructed", "note": position_note,
                "derivation": {"method": "not_derivable", "reason": "No parcel-by-parcel July 1835 North Division roof register survives in the supplied evidence."}
            },
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"A {width:.2f} × {depth:.2f} m rectangle sampled deterministically inside the {family} family's authored footprint band in the reconstruction specification; no individual dimensions are documented."
            },
            "form": form_for(family, spec, sid, int(seq), paint,
                             archetype_for(family), width, depth),
            "change_note": "Reconstructed anonymous July 1835 North Division infill; a better-evidenced named roof substitutes for a compatible count-unit rather than increasing the 665-roof total."
        }],
        "function": inferred(function, f"Assigned from the {family} family to satisfy the aggregate North Division mix; no occupant or individual use is known."),
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


def validate(records: list[dict], inventory: dict, recipe: dict, datum: dict) -> None:
    expected = recipe["inventory"]
    classes = Counter(r["reconstruction"]["inventory_class"] for r in records)
    families = Counter(r["reconstruction"]["family"] for r in records)
    if len(records) != expected["roof_total"]:
        raise SystemExit(f"North recipe generated {len(records)} roofs, expected {expected['roof_total']}")
    if classes != Counter({"principal_functional": expected["principal_functional"],
                           "ancillary": expected["ancillary"]}):
        raise SystemExit(f"North inventory-class mix drifted: {dict(classes)}")
    if families != Counter(expected["family_totals"]):
        raise SystemExit(f"North family mix drifted: {dict(families)}")
    for family, count in families.items():
        if count > inventory["family_targets"][family]:
            raise SystemExit(f"North {family} count {count} exceeds programme target")

    # Every form must resolve through a currently implemented archetype.
    for record in records:
        module = importlib.import_module(f"archetypes.{record['archetype']}_params")
        module.from_phase(record["phases"][0])

    polygons = [(r["id"], world_polygon(r, datum)) for r in records]
    for i, (sid, poly) in enumerate(polygons):
        for other_sid, other in polygons[:i]:
            if polygons_overlap(poly, other):
                raise SystemExit(f"North recipe collision: {sid} overlaps {other_sid}")

    # No anonymous roof may stand in a platted street (ROADMAP K7 phase two), asked
    # through the module the grid report and the other two generators read, on the
    # FOOTPRINT rather than the centre. It binds nothing today and is wired anyway: the
    # K7 grid covers 19 South and West Division blocks and no North Division block,
    # because the North's street control is what ROADMAP S9 still records as owed. The
    # day that control arrives, this parcel is already inside the rule rather than
    # waiting to be found in the road by a report.
    from plat_corridors import corridors, intrusion  # noqa: PLC0415
    lanes = corridors()
    for sid, poly in polygons:
        street, depth = intrusion(poly, lanes)
        if street:
            raise SystemExit(f"{sid} reaches {depth:.1f} m inside the platted "
                             f"{lanes[street]['name']} corridor")

    # Use the same committed surface the walker uses: every perimeter must be on
    # covered, dry ground and stay within its 0.35 m step-height contract.
    from heightfield import Heightfield  # noqa: PLC0415
    field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    if field is None:
        raise SystemExit("North recipe cannot validate: committed heightfield is missing")
    for sid, poly in polygons:
        heights = [field.height(e, n) for e, n in poly]
        if not all(field.covers(e, n) for e, n in poly):
            raise SystemExit(f"{sid} falls outside modelled terrain")
        if min(heights) < -.10:
            raise SystemExit(f"{sid} intersects the authoritative water side of the terrain")
        if max(heights) - min(heights) > .35:
            raise SystemExit(f"{sid} spans {max(heights) - min(heights):.2f} m of relief; its walls would not share the walker surface")


def records_from_inputs() -> list[dict]:
    inventory, recipe, datum = load(INVENTORY_PATH), load(RECIPE_PATH), load(DATA / "datum.json")
    records = [make_record(row, datum) for row in recipe["placements"]]
    deal_siding(records)
    validate(records, inventory, recipe, datum)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report missing, changed, or extra North outputs")
    args = parser.parse_args()
    records = records_from_inputs()
    expected = {f"{r['id']}.json" for r in records}
    drift = []
    for record in records:
        path = STRUCTURES / f"{record['id']}.json"
        # T-0609. `land_owner` is the ONE block on these records this recipe does not
        # own: it says which federal or canal tract the roof's position falls in, it is
        # derived from the land-sale register by tools/resolve_land_tracts.py, and that
        # tool's own --check re-derives every one of them on the same gate. So it is
        # carried through a regeneration rather than wiped by it — the same arrangement
        # the block recipe has with `lot_address`, and for the same reason: a generated
        # file may hold a claim a second derivation owns, as long as exactly one gate
        # owns it and nothing hand-edits it.
        if path.exists():
            committed = json.loads(path.read_text(encoding="utf-8"))
            if "land_owner" in committed:
                rebuilt = {}
                for key, value in record.items():
                    rebuilt[key] = value
                    if key == "occupants":
                        rebuilt["land_owner"] = committed["land_owner"]
                if "land_owner" not in rebuilt:
                    rebuilt["land_owner"] = committed["land_owner"]
                record = rebuilt
        text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists():
                drift.append(f"{path.relative_to(ROOT)} is missing")
            elif path.read_text(encoding="utf-8") != text:
                drift.append(f"{path.relative_to(ROOT)} has drifted from the North recipe")
        else:
            path.write_text(text, encoding="utf-8")
    extras = sorted(p.name for p in STRUCTURES.glob(f"{PREFIX}*.json") if p.name not in expected)
    drift.extend(f"data/structures/{name} is outside the bounded 60-roof parcel" for name in extras)
    if drift:
        print("NORTH INFILL DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    mode = "verified" if args.check else "generated"
    print(f"{mode} {len(records)} inferred anonymous North Division records (45 principal, 15 ancillary)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
