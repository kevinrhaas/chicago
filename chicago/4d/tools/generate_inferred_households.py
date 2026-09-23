#!/usr/bin/env python3
"""Expand the inferred-household programme: people, adoptions, and new buildings.

    python3 tools/generate_inferred_households.py            write
    python3 tools/generate_inferred_households.py --check    re-derive and diff

Phase two of docs/ROADMAP.md K1. Phase one wrote the town's DOCUMENTED and DERIVED
people and deliberately wrote no inferred ones; this expands
`data/reconstruction/1835_inferred_household_programme.json` into

  * `data/residents/households/hh_inf_*.json` — one file per inferred household,
    every person graded `inferred`, none of them named;
  * `data/residents/index.json` — the manifest's household rows and counts, and
    the five documented households whose buildings this parcel finally builds;
  * `data/structures/*.json` — the new records: the seven documented buildings
    phase one found with no record, and the inferred workplaces and dwellings the
    occupation census requires.

The adopted anonymous roofs are NOT written here. They belong to the two
anonymous-infill generators, which read `tools/inferred_occupancy.py` for the
occupancy block so their own byte-for-byte drift check keeps working.

WHAT THIS FILE WILL NOT DO. It will not invent a name: every inferred person
carries a designation and says in its note that it is a hypothesis. It will not
grade an invention `inferred` to make a gate pass: a position nobody recorded is
`conjectural` here exactly as it is on every other record in the dataset, and it
owes docs/LIBERTIES.md a `Covers:` token like any other invention.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
PROGRAMME = DATA / "reconstruction" / "1835_inferred_household_programme.json"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
INVENTORY = DATA / "reconstruction" / "1835_building_inventory.json"
RESERVED = (DATA / "reconstruction" / "1835_phase2_west_wolf_point_approaches.json",
            DATA / "reconstruction" / "1835_phase2_south_core_and_mixed_recipe.json")
SPEC = "owner_chicago_1835_reconstruction_spec_2026"
ANDREAS = "andreas_1884_v1"
SCENE_DATE = "1835-07-01"
PREFIX = "hh_inf_"

sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))
from rebuild_resident_index import rebuild  # noqa: E402  (the manifest's one owner)

from band_notes import split_notes  # noqa: E402
from roof_form import note_refusal, roof_kind  # noqa: E402
from inferred_occupancy import label  # noqa: E402
from measure_adoption_tests import floor_evidence  # noqa: E402
# T-0112. The clapboard stock is dealt at the end of the parcel, because it is the one
# form value that depends on where a building's neighbours stand. The four DOCUMENTED
# frame buildings this parcel regenerates are neighbours here and never subjects — see
# tools/siding_stock.is_invented.
from siding_stock import deal_records as deal_siding  # noqa: E402
# T-0182. Two of this layer's roofs stand on a committed block face, and the face is
# read rather than retyped — the same module `tools/generate_inferred_infill.py` and
# `tools/generate_block_infill.py` already import for their own frontage rows.
from block_faces import face_frame  # noqa: E402
# T-0274. The eave and the pitch are drawn from the family's own authored band
# instead of being retyped as a per-archetype constant, and the sampler is the one
# `tools/family_bands.py` already holds for the other three parcels. The run the
# roof climbs is the ARCHETYPE's, so `tools/ridge_model.py` is asked for it rather
# than it being computed here.
from family_bands import (eave_floor, eave_for_ridge, eave_limits,  # noqa: E402
                          families, pitch_deg, wall_height_m)
from ridge_model import ridge_run_m  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc, indent: int) -> str:
    return json.dumps(doc, indent=indent, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------
# people
# --------------------------------------------------------------------------

def arrival_block() -> dict:
    return {
        "value": SCENE_DATE,
        # Bottom tier: this bounds an invention, it does not report a finding.
        "confidence": "reconstructed",
        "note": ("NOT AN ARRIVAL, A BOUND. Nothing dates a hypothesised household, and a year "
                 "would be a claim nobody made. `not_later_than` the scene date states the only "
                 "thing the inference carries: the town's need is measured on 1 July 1835, so "
                 "the household is posited as being here by then and at no stated time before "
                 "it."),
        "precision": "not_later_than",
    }


def null_block(note: str) -> dict:
    return {"value": None, "confidence": "reconstructed", "note": note}


def link_block(sid, note: str) -> dict:
    if sid is None:
        return null_block(note)
    # An invented person attached to an invented building. The link is a construction
    # of this generator, not a reading of a source about either end of it.
    return {"value": sid, "confidence": "reconstructed", "sources": [SPEC], "note": note}


def person(hh: dict, census: dict, idx: int | None = None, extra: dict | None = None) -> dict:
    occ = (extra or hh)["occupation"]
    trade = label(occ)
    base = hh["id"].removeprefix("hh_")
    if extra is None:
        article = "An" if trade[0] in "aeiou" else "A"
        pid, rel, name = base, "head", f"{article} {trade} (reconstructed resident, unnamed)"
        why = (f"THE {ordinal_word(hh['ordinal']).upper()} OF {hh['of']} {trade.upper()} "
               f"HOUSEHOLDS THIS LAYER RECONSTRUCTS. " + census[occ]["argument"])
    else:
        pid = f"{base}_{extra['relationship'][:1]}{idx}"
        rel = extra["relationship"]
        article = "An" if rel[0] in "aeiou" else "A"
        name = f"{article} {rel} {trade} (reconstructed resident, unnamed)"
        why = (f"A {rel} in the same shop. The trade's own argument: "
               + census[occ]["argument"])
    p = {
        "id": pid,
        "name": name,
        "relationship": rel,
        "grade": "reconstructed",
        "occupation": {
            "value": occ,
            # The occupation is the REASON this person was invented — the town needed
            # this many of this trade — so it is a claim about a ratio, not a finding
            # about a person. Grading it as reasoned-from-evidence-about-this-person
            # asserts a person the record explicitly says does not exist.
            "confidence": "reconstructed",
            "sources": [ANDREAS, SPEC],
            "note": census[occ]["argument"],
        },
        "note": ("HYPOTHESISED, AND NOT A PERSON. No source names this resident and none is "
                 "claimed to: the record asserts that a town of 3,265 people in 398 dwellings "
                 "held at least this many households of this trade, and asserts nothing whatever "
                 "about any individual. THE NAME IS INVENTED TOO, and `name_basis` beside it says "
                 "so and says which pool it came from: this record used to carry a bare "
                 "designation instead, on the reasoning that a surname would make it look like "
                 "the documented layer, but a town of designations does not read as a town and "
                 "the grade, this note and name_basis all say plainly which layer this is. "
                 "No figure is drawn (docs/LIBERTIES.md L1). " + why),
    }
    if occ in ("laundress", "domestic"):
        p["sex"] = "female"
        p["note"] += (" SEX IS STATED HERE AND NOWHERE ELSE IN THIS LAYER: the argument for the "
                      "trade is explicitly an argument about women's work, so recording the "
                      "person as male would contradict the reasoning that produced her.")
    return p


ORDINALS = ("zeroth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
            "eighth", "ninth", "tenth", "eleventh", "twelfth")


def ordinal_word(n: int) -> str:
    return ORDINALS[n] if n < len(ORDINALS) else f"{n}th"


def household_record(hh: dict, census: dict, buildings: dict) -> dict:
    occ = hh["occupation"]
    trade = label(occ)
    persons = [person(hh, census)]
    for i, extra in enumerate(hh.get("extras") or [], start=1):
        persons.append(person(hh, census, i, extra))

    def where(sid: str) -> str:
        if sid is None:
            return ""
        if sid.startswith("recon_"):
            return ("an anonymous reconstructed roof already standing on the plat, adopted rather "
                    "than duplicated: its existence, position and footprint stay conjectural and "
                    "the adoption adds only the occupant argument")
        if sid in buildings:
            return ("a structure record this parcel raises for the purpose, because no roof of "
                    "the right family stood free in this district")
        return "a documented building in this dataset"

    lives = hh.get("lives_at")
    works = hh.get("works_at")
    lives_note = (f"THE HOUSEHOLD IS HOUSED, WHICH IS THE POINT OF THE LAYER. {lives} is "
                  f"{where(lives)}. Which roof of the right family and district a hypothesised "
                  f"household occupies is not evidence about that roof; the household needed a "
                  f"dwelling and the programme assigned it one.") if lives else \
        "No dwelling is claimed for this household."
    if works == lives and works:
        works_note = (f"THE SAME BUILDING. {works} is a shop or house that this layer reads as "
                      f"both workplace and dwelling - the schedule's store-residence and "
                      f"boarding-house families are exactly that, and a frontier tradesman "
                      f"living over his own premises is the type rather than the exception.")
    elif works:
        works_note = (f"{works} is {where(works)}. The workplace is assigned from the "
                      f"reconstruction schedule's workshop and store families for this trade.")
    else:
        works_note = (f"NO SEPARATE WORKPLACE. A {trade} in this town worked in other people's "
                      f"buildings, in the street, or in the dwelling itself, and inventing a "
                      f"shop for the sake of a link would be inventing a building.")

    return {
        "id": hh["id"],
        "name": f"A reconstructed {trade}'s household ({hh['division']} division)",
        "division": hh["division"],
        "head": persons[0]["id"],
        "arrival": arrival_block(),
        "party_size_on_arrival": null_block(
            "Not claimed. The layer infers households, not families: the person entries here are "
            "the ones the trade argument requires and nothing counts wives or children, because "
            "counting them would multiply a hypothesis by an invention."),
        "origin": null_block(
            "Not claimed. Where a hypothesised resident came from is unknowable by construction, "
            "and the documented layer's origins (Vermont, Washington, Ann Arbor) are evidence "
            "about those men and not a distribution to sample from."),
        "reason_for_coming": null_block(
            "Not claimed for the person. The reason the HOUSEHOLD is in the dataset is the trade "
            "argument in research_note, which is a statement about the town and not about a "
            "motive."),
        "lives_at": link_block(lives, lives_note),
        "works_at": link_block(works, works_note),
        "present_on_scene_date": {
            "value": "present",
            "confidence": "reconstructed",
            "note": ("Presence on the scene date IS the hypothesis: this household exists in the "
                     "dataset because the town of 1 July 1835 demonstrably needed households of "
                     "this trade. It is not a finding about anybody's whereabouts."),
        },
        "persons": persons,
        "touches_removal": False,
        "review_required": False,
        "research_note": (
            f"RECONSTRUCTED HOUSEHOLD - {ordinal_word(hh['ordinal'])} of {hh['of']} {trade} households "
            f"in this layer, in the {hh['division']} division. " + census[occ]["argument"] +
            " METHOD: the count comes from the occupation census in "
            "data/reconstruction/1835_inferred_household_programme.json, which calibrates every "
            "trade against three things this project already holds - the 1835 town census "
            "(3,265 people, 398 dwellings), Andreas's roster of the fall of 1833 (about fifty "
            "named people, most with a trade, in a settlement of some 350), and the "
            "reconstruction specification's roof schedule, whose workshop and store family "
            "targets are treated as the ceiling on a trade rather than as its measure. Every "
            "count is stated NET of the documented layer: this dataset infers a tradesman only "
            "where it cannot name one."),
    }


# --------------------------------------------------------------------------
# buildings
# --------------------------------------------------------------------------
FT = 0.3048

REAL_BUILDING_FORM_NOTE = (
    "THE BUILDING IS ATTESTED; THIS ATTRIBUTE IS NOT. A source places this building and "
    "says what it was, but nothing records this particular dimension or detail, so the "
    "value is a typology from the reconstruction spec — what a building of this kind was "
    "ordinarily like. Reconstructed, therefore, and not because the building is in doubt: "
    "it is not. Only this number is. "
)


INVENTED_FORM_NOTE = (
    "INVENTED, NOT DERIVED. A typology value from the reconstruction spec — what a "
    "building of this kind was ordinarily like — not a reading of evidence about this "
    "particular building, because no source speaks to it: the structure exists in the "
    "model because the town demonstrably needed one of these, and nothing more. The "
    "spec is cited because the invention is bounded by it. "
)




# --------------------------------------------------------------------------
# placements that stand on a committed block face (T-0182)
# --------------------------------------------------------------------------
#
# Most of this layer's roofs stand on free ground: a frontage-band assignment, tested
# for clearance and buildable ground, and written into the programme as a centre. Two
# of them do not. `inf_bakery_lake` and `inf_butcher_market` front the north face of
# `blk_lake_clark`, and `recon_1835_south_d3_013` declares a shared party wall with the
# butcher — a claim about one wall, made from the other side.
#
# Written as centres they could not honour it. Both were authored at bearing 0 where
# that face runs at 0.465, so their front walls landed 0.804 m and 0.784 m off the
# committed boundary against the 0.800 m the seven frontage records on the face stand
# at: near the line, parallel to nothing, and by arithmetic nobody re-derived. The
# party wall was 16 mm open and `tools/measure_street_line.py` had to bank it by name.
#
# So a building here MAY declare a face instead of a centre, and then it takes its
# line, its bearing and its outward offset from `data/traces/vectors/thompson_lots.json`
# — the committed plat, through the one `tools/block_faces.py` module both infill
# generators already read. What the programme still authors is where along that face
# the building's west wall stands, which is the same thing a frontage row authors as
# its corner clearance: an interpretive choice about which part of a street a made-up
# building occupies, expressed in the face's own frame rather than as a coordinate
# beside the plat.
#
# STANDING ON A DERIVED BLOCK FACE IS NOT STANDING ON A RECOVERED LOT. The buildings
# are still invented, their positions are still `reconstructed`, and the derivation
# block still says `not_derivable` — nothing here upgrades a confidence. It removes a
# hand-typed coordinate, which is the whole of the claim.

# T-1227 (piece of T-1108): WHERE A BAND ASSIGNMENT MEETS A PLATTED CORRIDOR, THE CORRIDOR WINS — AND IT
# WINS IN THE RECIPE, NOT IN THE FILE THE RECIPE WRITES.
#
# `validate` below refuses an invented placement that stands in the roadway, and it is
# right to: a band assignment has no evidence to encroach with. T-0827 met that refusal
# when it re-fitted Market Street off the plat's own 400 ft module instead of off the
# modern junction on N Wacker Drive, moving the platted corridor 3.0 m west onto
# `inf_cooperage_south_branch`. It settled the ruling correctly — the roadway moved, so
# the building moves — and then wrote the answer into the GENERATED record by hand while
# leaving the centre in the programme where it was. This generator owns that file, so the
# two disagreed from that day: three `--check` modes refused on one line, none of the
# three could be gated, and `data/research/check_gate_baseline.json` carried the refusal
# as a standing exemption.
#
# So the ruling is expressed as a RULE a re-fitted plat re-runs, in the same spirit as the
# block faces above. A building MAY declare `corridor_clearance` beside its centre, and
# the pass then moves it the LEAST distance along that corridor's cross axis that leaves
# its whole footprint the stated margin clear of the platted kerb. The centre in the
# programme keeps its meaning — it is still the band assignment, still the interpretive
# choice about which part of town this made-up building occupies — and the corridor is
# what overrules it, measured rather than typed. A building already clear by the margin
# does not move at all.
#
# THIS UPGRADES NOTHING. The position stays `reconstructed`, the derivation block stays
# `not_derivable`, and standing clear of a derived corridor is not standing on a
# recovered lot. What it removes is a hand-typed coordinate that no longer had anything
# re-deriving it.

CORRIDOR_CLEARANCE_NOTE = (
    " MOVED OUT OF THE PLATTED {street_name} CORRIDOR, BY THE CORRIDOR RATHER THAN BY "
    "HAND (T-1227, settling T-0827's ruling of 2026-09-12). The band assignment above "
    "puts this building's centre at local ENU E {from_e:g} N {from_n:g}, which stands "
    "{depth:.2f} m inside {street_name}'s platted corridor — and the reason is that the "
    "ROADWAY moved, not the building: T-0827 re-fitted {street_name} off the plat's own "
    "400 ft module instead of off the modern junction on N Wacker Drive it had been hung "
    "from, and the corridor came west onto this footprint. An invented placement has "
    "nothing to encroach with, so the corridor wins. The record therefore stands "
    "{shift:.3f} m {direction} of its band assignment, at E {to_e:.3f} N {to_n:.3f} — the "
    "LEAST this building can move and still leave its whole footprint {clear:.2f} m clear "
    "of the platted kerb, measured against the corridor through tools/plat_corridors.py, "
    "which is the same geometry the gate refuses on. The margin is T-0827's own and the "
    "distance is not typed anywhere: re-fit {street_name} again and this building moves "
    "again, instead of silently disagreeing with it."
)

FACE_PLACEMENT_NOTE = (
    "INTERPRETIVE PLACEMENT ON A COMMITTED BLOCK FACE, NOT A RECOVERED LOT (T-0182). "
    "{role} This building does not stand where a centre in the programme put it: it "
    "stands on the {face} face of {block}, whose line and bearing are read from the "
    "block boundary in data/traces/vectors/thompson_lots.json — the same committed "
    "geometry the lot grid and the corridor gate are derived from. Its front wall is "
    "set {setback} m back from that lot line, which is the one line every record on "
    "this face stands on, and its bearing is the face's own rather than the zero a "
    "hand-authored centre carried. What the programme still chooses is where along the "
    "face it stands — {along} m from the face's west end, the position it already "
    "occupied, so this repair moves no building along the street. WHAT IS INVENTED IS "
    "STILL EVERYTHING THAT MATTERS: that a building stood here at all, and that it was "
    "this trade's. The dataset's 20 m working georeference uncertainty applies on top "
    "of an already invented position, and standing on a derived block face is not "
    "standing on a recovered lot."
)

FACE_DERIVATION_REASON = (
    "No source gives this building a lot, and none is claimed. The block face it fronts "
    "IS derived — line, bearing and outward offset out of the committed plat in "
    "data/traces/vectors/thompson_lots.json — but which building stands on it, and where "
    "along it, is a production control of the inferred-household programme."
)


def face_placement(spec: dict, wft: float, dft: float) -> tuple[float, float, float]:
    """(centre east, centre north, bearing) for a building standing on a block face.

    The face's frame comes out of the committed plat; the programme hands in the
    setback and how far along the face the west wall lands. Nothing here authors a
    coordinate, and the arithmetic is the frontage runs' own: walk along the face to
    the west wall, then in from the line by the setback and half the depth.
    """
    grid = load(LOTS)
    block = next((b for b in grid["blocks"] if b["id"] == spec["block"]), None)
    if block is None:
        raise SystemExit(f"{spec['block']} is not a block of the committed plat grid")
    frame = face_frame(block, spec["face"])
    w, d = wft * FT, dft * FT
    along = float(spec["west_wall_along_m"])
    if not 0.0 <= along <= frame["length"] - w:
        raise SystemExit(f"a face placement at {along} m does not fit on the "
                         f"{spec['face']} face of {spec['block']}, which is "
                         f"{frame['length']:.2f} m long")
    setback = float(spec["setback_m"])
    ce = (frame["origin"][0] + frame["along"][0] * (along + w / 2)
          + frame["outward"][0] * (-setback - d / 2))
    cn = (frame["origin"][1] + frame["along"][1] * (along + w / 2)
          + frame["outward"][1] * (-setback - d / 2))
    return ce, cn, frame["bearing"]


def resolve_placements(programme: dict) -> None:
    """Give every face-placed building the centre and bearing its face implies.

    The rest of the generator reads `center_local_enu_m` and `rotation_deg` off a
    building, so a face placement resolves into exactly those two before anything
    else runs — the difference is that for these buildings the programme no longer
    carries them, and a re-derived plat moves them instead of silently disagreeing
    with them.
    """
    for b in programme["buildings"]:
        spec = b.get("frontage")
        if not spec:
            continue
        if "center_local_enu_m" in b or "rotation_deg" in b:
            raise SystemExit(f"{b['id']} declares a block face AND a centre: one of them "
                             f"is a second opinion about the same ground")
        wft, dft = b["footprint_ft"]
        ce, cn, bearing = face_placement(spec, wft, dft)
        b["center_local_enu_m"] = [round(ce, 6), round(cn, 6)]
        b["rotation_deg"] = bearing


def _corridor_rect(ce: float, cn: float, w: float, d: float, bearing: float) -> list:
    """The footprint a RECORD will carry, centred on (ce, cn).

    Deliberately not `rect_polygon`: that one multiplies feet by FT unrounded, while
    `structure_record` rounds the metres to the millimetre it writes into the file, and
    the corridor gate measures the written polygon. Half a millimetre does not matter to
    the answer; measuring a different body from the one being gated does.
    """
    th = math.radians(bearing)
    cos, sin = math.cos(th), math.sin(th)
    return [(ce + u * cos + v * sin, cn - u * sin + v * cos)
            for u, v in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]


def resolve_corridor_clearance(programme: dict) -> None:
    """Push a band-assigned centre clear of a platted corridor — see the note above.

    Mutates `center_local_enu_m` in place and records what it did under
    `_corridor_clearance_applied`, which `structure_record` turns into the record's own
    account of the move. A building already clear by its stated margin is left alone and
    the key says so, so the record never claims a move that did not happen.
    """
    from plat_corridors import sampled  # noqa: PLC0415
    from generate_plat_lots import (  # noqa: PLC0415
        EW_STREETS, NS_STREETS, point_in_polygon, point_to_ring_m,
    )

    lanes = None
    for b in programme["buildings"]:
        spec = b.get("corridor_clearance")
        if not spec:
            continue
        if b.get("frontage"):
            raise SystemExit(f"{b['id']} stands on a block face AND asks to be pushed off a "
                             f"corridor: the face already decides where it stands")
        if lanes is None:
            from plat_corridors import corridors  # noqa: PLC0415
            lanes = corridors()
        street = spec["street"]
        if street not in lanes:
            raise SystemExit(f"{b['id']} names a corridor no committed street draws: {street}")
        axis = 0 if street in NS_STREETS else 1 if street in EW_STREETS else None
        if axis is None:
            raise SystemExit(f"{b['id']} names {street}, which is on neither grid axis, so the "
                             f"corridor has no cross axis to move along")

        clear = float(spec["clear_m"])
        ring = lanes[street]["ring"]
        ce, cn = (float(v) for v in b["center_local_enu_m"])
        wft, dft = b["footprint_ft"]
        w, d = round(wft * FT, 3), round(dft * FT, 3)
        bearing = float(b["rotation_deg"])

        def body(shift: float) -> list:
            c = (ce + shift, cn) if axis == 0 else (ce, cn + shift)
            return _corridor_rect(c[0], c[1], w, d, bearing)

        def signed(shift: float) -> float:
            """How far short of `clear` the shifted footprint falls.

            Positive while any part of it is inside the corridor or inside the margin,
            negative once the whole body stands clear by more than the margin.
            """
            worst = -math.inf
            for point in sampled(body(shift)):
                depth = point_to_ring_m(point, ring)
                inside = point_in_polygon(point, ring)
                worst = max(worst, (depth if inside else -depth) + clear)
            return worst

        if signed(0.0) <= 0.0:
            b["_corridor_clearance_applied"] = None
            continue

        # The least move on the cross axis, in whichever direction is nearer. A corridor
        # is a convex band, so the shortfall falls monotonically once a body is on its way
        # out of one and a bisection per side is exact. The winner is rounded AWAY from
        # the roadway to the millimetre this dataset quotes a position in, which can only
        # leave the building clearer than the rule asks and never nearer.
        reach = 2.0 * (point_to_ring_m((ce, cn), ring) + max(w, d) + clear) + 1.0
        best = None
        for sign in (-1.0, 1.0):
            hi = reach
            if signed(sign * hi) > 0.0:
                continue
            lo = 0.0
            for _ in range(60):
                mid = (lo + hi) / 2.0
                if signed(sign * mid) > 0.0:
                    lo = mid
                else:
                    hi = mid
            candidate = sign * (math.ceil(hi * 1000.0) / 1000.0)
            if best is None or abs(candidate) < abs(best):
                best = candidate
        if best is None:
            raise SystemExit(f"{b['id']} cannot be moved clear of the {street} corridor along "
                             f"its cross axis: the band assignment is in the wrong place")

        depth = max((point_to_ring_m(pt, ring) for pt in sampled(body(0.0))
                     if point_in_polygon(pt, ring)), default=0.0)
        moved = (round(ce + best, 3), cn) if axis == 0 else (ce, round(cn + best, 3))
        b["_corridor_clearance_applied"] = {
            "street_name": lanes[street]["name"],
            "from_e": ce, "from_n": cn,
            "to_e": moved[0], "to_n": moved[1],
            "shift": abs(best),
            "direction": ("west" if best < 0 else "east") if axis == 0
                         else ("south" if best < 0 else "north"),
            "depth": depth,
            "clear": clear,
        }
        b["center_local_enu_m"] = [moved[0], moved[1]]


def footprint_origin(ce: float, cn: float, w: float, d: float, bearing: float):
    th = math.radians(bearing)
    cos, sin = math.cos(th), math.sin(th)
    return (ce - w * .5 * cos - d * .5 * sin, cn + w * .5 * sin - d * .5 * cos)


# The crosswalk's per-family bands, read once through the one module that reads them.
# This parcel pairs family with archetype BY HAND in the programme — H1 reaches
# `log_dwelling` here and nowhere else — so the archetype below stays the programme's
# answer; it is only the eave and the pitch that stop being the archetype's business.
FAMILY_BANDS = families()


def band_spec(family: str) -> dict:
    spec = FAMILY_BANDS.get(family)
    if spec is None or not spec.get("eave_ft"):
        raise SystemExit(f"the crosswalk authors no eave band for family {family}; "
                         f"the inferred-household programme cannot sample it")
    return spec


def storeys_for(archetype: str, family: str) -> float | None:
    """The storey count this parcel deals, hoisted out of the branches below.

    It is hoisted because `family_bands.eave_limits` asks the ARCHETYPE what wall it
    will carry AT A STOREY COUNT, and the count has to be known before the branch that
    writes it is reached. The values are exactly the ones those branches wrote; `None`
    is the outbuilding tail, which authors no storey count at all and which
    `eave_limits` reads as "no storey-dependent limit" — the truth for `outbuilding`.
    """
    if archetype == "log_dwelling":
        return 1
    if archetype == "frame_dwelling":
        return 2 if family in ("D7", "H2", "H3") else 1
    if archetype == "frame_storefront":
        # C3 IS TWO STOREYS AND EVERY OTHER STORE HERE IS ONE. The flat 1 this branch
        # used to write was the retyped constant that made C3's authored 18-22 ft eave
        # band unbuildable: `frame_storefront` refuses more than 4.2 m of wall on a
        # one-storey record, so not one value in that band could stand. The crosswalk
        # authors `levels: 2` for the family and `generate_inferred_infill.storeys_for`
        # already deals it two; this parcel was the one out of step. The single C3 this
        # programme raises is documented and overrides its form to two storeys by hand,
        # which is why nothing standing was wrong and only the sweep could see it.
        return 2 if family == "C3" else 1
    return None


def door_kind(family: str) -> str:
    """WHICH DOOR a family carries, asked for rather than read off the form dict.

    The eave FLOOR depends on it — a wagon door needs a metre more wall than a man
    door — and the floor has to be known before the eave is drawn. The membership is
    the one the outbuilding tail below has always written.
    """
    if family in ("W1", "W2", "W3", "W5", "F1", "A2"):
        return "wagon"
    return "stable" if family == "A1" else "man"


def roof_for(archetype: str, family: str) -> tuple[str, bool | None]:
    """The roof type and gable orientation the branches below actually WRITE.

    Asked separately from `roof_form.roof_kind` and hoisted, because `ridge_model` has
    to be handed the roof the record will carry rather than the one the family's
    crosswalk line offers, and for this parcel those differ. Three of the four
    archetypes here build a gable whatever the family's roof line says — only the
    outbuilding tail takes `roof_kind`'s answer — and the storefront branch writes
    `gable_front: True`, which is what turns the ridge across the plan and so decides
    which of width and depth the roof climbs. Handing `ridge_model` the family's raw
    answer instead put the barber's shop on its DEPTH, made the ridge band look
    reachable from an eave that could not reach it, and shipped a roof 1.6 ft under its
    own band.
    """
    if archetype in ("log_dwelling", "frame_dwelling"):
        return "gable", None
    if archetype == "frame_storefront":
        return "gable", True
    return roof_kind(family)


def pitch_default(archetype: str, family: str) -> float:
    """The generator's own type value, which is what a family authoring no band gets.

    `family_bands.pitch_deg` returns this unchanged for a family whose roof line names
    no rise:run at all, so the sampler invents no claim where the specification makes
    none. The four values are the constants the branches below used to write.
    """
    if archetype == "log_dwelling":
        return 35.0
    if archetype == "frame_dwelling":
        return 38.0
    if archetype == "frame_storefront":
        return 33.0
    return 18.0 if roof_kind(family)[0] == "shed" else 32.0


def inferred_form(archetype: str, family: str, spec_note: str, key: str,
                  width_m: float = 9.0, depth_m: float = 9.0,
                  building_documented: bool = False) -> dict:
    # Every value below is INVENTED, and the grade says so.
    #
    # It used to say "derived", which under this project's own definition means
    # "reasoned from evidence about THIS PARTICULAR THING". There is no particular
    # thing: these attributes describe a building raised because the town must have
    # had a shoemaker, not a building anybody recorded. The typology behind them is
    # real and the spec is cited — an invention bounded by a source is defensible,
    # which is why the citation stays — but a claim about what shops of this kind
    # were ordinarily like is not a reading of a source about this shop.
    #
    # The cost of the old grade was not academic. It made 158 buildings that never
    # existed render SOLID in the confidence view while the Exchange Coffee House —
    # a real tavern with a name, a keeper and a documented function — rendered as a
    # dithered ghost beside them, because its wall height is honestly unknown. The
    # view was telling the visitor the exact opposite of the truth.
    lede = REAL_BUILDING_FORM_NOTE if building_documented else INVENTED_FORM_NOTE

    def a(v):
        return {"value": v, "confidence": "reconstructed", "sources": [SPEC],
                "note": lede + spec_note}

    # THE EAVE AND THE PITCH COME FROM THE FAMILY'S OWN BAND (T-0274), and this is the
    # fourth and last parcel to make the move T-0144 and T-0145 made on the platted
    # blocks, T-0272 on the West approaches and T-0273 on the South infill.
    #
    # This parcel keyed both values on the ARCHETYPE, so one figure per archetype was
    # dealt to every family that reaches it, and the note printed under each one told a
    # visitor it was a type-level choice "within the {family} band" — which for ten of
    # them was not true. `tools/measure_family_deal.py` named all ten: A5 and W4 stood
    # at a man door's 2.05 m under bands starting at 7 and 9 ft, C2 at 3.25 m and
    # 33.0 deg, C3 at the same 3.25 m under an 18-22 ft band, D3 at 2.78 m, D2 fell
    # past the frame branches into the outbuilding tail and took 2.05 m and 18.0 deg
    # with it, A2 at 32.0 deg, and H1 — reached through `log_dwelling`, which this
    # parcel alone pairs it with — at that branch's flat 2.5 m, a metre short of its
    # own band. Every one was a per-family CONSTANT, so it was made on 100 per cent of
    # that family's deals and not on a tail.
    #
    # A constant is also a claim of uniformity no source makes: five D3 dwellings dealt
    # from one figure are not five dwellings. Sampling adds variety, not knowledge —
    # every value still grades at the bottom tier and the note still says the band is a
    # typology and not evidence about this building. What changes is that the band is
    # used as the range it was authored as instead of being collapsed to a point.
    #
    # The archetype bounds the band at BOTH ends and the limits are ASKED of it, never
    # retyped: `eave_floor` for the door a family's wall has to header, `eave_limits`
    # for the storey-height ceiling `frame_dwelling` publishes. The family's own RIDGE
    # band bounds it once more (T-0148), which needs the run the roof climbs, and that
    # is the archetype's too.
    spec = band_spec(family)
    roof, gable_front = roof_for(archetype, family)
    stories = storeys_for(archetype, family)
    run = ridge_run_m(archetype, roof, width_m, depth_m, gable_front)
    arch_lo, arch_hi = eave_limits(archetype, stories)
    floor, ceiling = max(eave_floor(family, door_kind(family)), arch_lo), arch_hi
    default_pitch = pitch_default(archetype, family)
    wall = eave_for_ridge(wall_height_m(family, spec["eave_ft"], key, floor, ceiling),
                          family, spec["eave_ft"], spec.get("roof"),
                          spec.get("ridge_ft"), run, default_pitch, key, floor, ceiling)

    def pitch() -> float:
        # A pitch and a footprint together make the RIDGE, and the crosswalk authors a
        # band for that too, so the sampler is constrained by it.
        return pitch_deg(family, spec.get("roof"), key, default_pitch,
                         eave_m=wall, run_m=run, ridge_ft=spec.get("ridge_ft"))

    if archetype == "log_dwelling":
        return {"stories": a(stories), "wall_height_m": a(wall), "roof_type": a("gable"),
                "roof_pitch_deg": a(pitch()), "construction": a("log"), "loft": a(True),
                "chimneys": a(1)}
    if archetype == "frame_dwelling":
        two = stories == 2
        return {"stories": a(stories), "wall_height_m": a(wall),
                "roof_type": a("gable"), "roof_pitch_deg": a(pitch()),
                "construction": a("braced_frame"),
                "plan": a("centre_passage" if two else ("single_pen" if family == "D3"
                                                        else "hall_parlour")),
                "bays": a(5 if two else 3), "chimneys": a(1), "paint": a("unpainted")}
    if archetype == "frame_storefront":
        # A glazed shopfront needs 3.25 m of bay plus a return at each end. Below about
        # 6 m of frontage the archetype cannot build one and neither could a carpenter:
        # a shop that narrow had a door and a window, which is what the record then says.
        wide = width_m >= 6.0
        narrow_note = (spec_note + " THE SHOPFRONT IS OFF because this frontage cannot carry "
                       "one: the archetype's glazed front needs 3.25 m of bay plus a return at "
                       "each end, and a shop of this width had a door and a window instead.")
        return {"stories": a(stories), "wall_height_m": a(wall), "roof_type": a("gable"),
                "roof_pitch_deg": a(pitch()), "gable_front": a(True),
                "construction": a("braced_frame"), "cladding": a("clapboard"),
                "paint": a("unpainted"), "loft": a(family in ("C2", "C3")), "chimneys": a(1),
                "shopfront": ({"value": False, "confidence": "reconstructed", "sources": [SPEC],
                               "note": lede + narrow_note} if not wide else a(True)),
                "goods_door": a(wide), "goods_door_side": a("end")}
    door = door_kind(family)
    # WHICH ROOF A FAMILY GETS is `tools/roof_form.py`'s answer and no longer this
    # file's (T-0179): the same literal used to sit in five parcels and the five had
    # already drifted over A5. `roof_for` above returns it unchanged for this tail.
    return {"wall_height_m": a(wall), "roof_type": a(roof),
            "roof_pitch_deg": a(pitch()),
            "construction": a("plank" if family.startswith("D") else "light_frame"),
            "door": a(door), "door_side": a("front"),
            "loft": a(family in ("W2", "W5", "A1", "A2")),
            "board_gap_m": a(0.012), "paint": a("unpainted")}


def attested(value, confidence, sources, note) -> dict:
    block = {"value": value, "confidence": confidence}
    if sources:
        block["sources"] = list(sources)
    block["note"] = note
    return block


def structure_record(b: dict, datum: dict, prose: dict, hh_by_building: dict) -> dict:
    bid = b["id"]
    ce, cn = b["center_local_enu_m"]
    wft, dft = b["footprint_ft"]
    w, d = round(wft * FT, 3), round(dft * FT, 3)
    e0, n0 = footprint_origin(ce, cn, w, d, float(b["rotation_deg"]))
    documented = b["kind"] == "documented"
    p = prose.get(bid, {})
    occupants_hh = hh_by_building.get(bid, [])

    if documented:
        exist_conf, exist_src, exist_note = p["existence"]
        pos_conf, pos_src, pos_note = p["position"]
        foot_note = p["footprint"]
        func_conf, func_src, func_note = "attested", [ANDREAS], p["research"]
        name = p["name"]
        function_value = p["function"]
        occ_conf, occ_src, occ_note = p["occupants"]
        research = p["research"]
        form_over = p.get("form") or {}
        phase_id = "documented_1835"
        change = ("The building as this dataset can state it on the scene date. Where the "
                  "sources give a size, a plan or a fabric, the record carries it; where they do "
                  "not, the note says so attribute by attribute.")
    else:
        role = b["role"]
        role_lc = role[0].lower() + role[1:]
        trade = label(b["occupation"])
        name = "Reconstructed " + b["function"].replace("_", " ") + " (" + trade + ")"
        function_value = b["function"]
        exist_conf, exist_src = "reconstructed", None
        exist_note = ("NO EVIDENCE ESTABLISHES THAT THIS PARTICULAR BUILDING EXISTED. It is the "
                      "roof a reconstructed household requires - " + role_lc + " The argument for the "
                      "trade's presence in the town is in the household record and in the "
                      "occupation census at "
                      "data/reconstruction/1835_inferred_household_programme.json; the argument "
                      "for THIS BUILDING is only that the household needs somewhere to be.")
        pos_conf, pos_src = "reconstructed", None
        pos_note = ("INTERPRETIVE PLACEMENT, NOT A RECOVERED LOT. " + role + " The band follows "
                    "ROADMAP K1's placement rule - businesses toward the river and the built "
                    "streets, residences further out - using the same frontage bands the "
                    "reconstruction recipes already work in, which come from the 80 ft platted "
                    "street module in data/traces/street_control.json. The centre was tested "
                    "against every structure footprint in the dataset, against the reserved "
                    "slots of the two uninstantiated phase-2 recipes, against the platted "
                    "street corridors of the K7 block grid so that no invented building "
                    "stands in the roadway, and against the committed heightfield for "
                    "coverage, dry ground and step tolerance; it is free ground and nothing "
                    "more. The dataset's 20 m working georeference uncertainty applies on top "
                    "of an already invented position.")
        foot_note = (f"A {wft:g} x {dft:g} ft rectangle from the {b['family']} family band in the "
                     f"reconstruction specification. NO DIMENSION IS DOCUMENTED for this "
                     f"building, which does not exist in any source; the band is type-level "
                     f"evidence about what buildings of this class measured and is not evidence "
                     f"about this one.")
        func_conf, func_src, func_note = "reconstructed", [ANDREAS, SPEC], role
        occ_conf, occ_src = "reconstructed", [ANDREAS, SPEC]
        occ_note = ("The reconstructed household this building exists for: "
                    + ", ".join(occupants_hh) + " in data/residents/households/. No name is "
                    "claimed and no figure is drawn.")
        research = ("RECONSTRUCTED BUILDING, RAISED FOR A RECONSTRUCTED HOUSEHOLD (docs/ROADMAP.md K1, "
                    "phase two). " + role + " It is NOT one of the anonymous count-units of the "
                    "665-roof programme: those are placed by aggregate mix and carry no occupant, "
                    "while this one exists because the occupation census says the town held a "
                    "household of this trade and no anonymous roof of the right family stood free "
                    "in this district. It consumes one slot of its district's programme target "
                    "rather than adding to it - see the accounting block in "
                    "data/reconstruction/1835_inferred_household_programme.json.")
        # T-0182: a roof standing on a committed block face says so, and says which
        # part of that placement is derived and which part is still a choice.
        if b.get("frontage"):
            spec = b["frontage"]
            pos_note = FACE_PLACEMENT_NOTE.format(
                role=role, face=spec["face"], block=spec["block"],
                setback=f"{float(spec['setback_m']):.2f}",
                along=f"{float(spec['west_wall_along_m']):.3f}")
        # T-1227: and a roof the platted corridor moved says so, says by how much, and
        # says that the corridor is what moved it — in the record the generator owns,
        # because that is the only place a reader of this building will look.
        moved = b.get("_corridor_clearance_applied")
        if moved:
            pos_note += CORRIDOR_CLEARANCE_NOTE.format(**moved)
        form_over = {}
        phase_id = "inferred_1835"
        change = ("Raised by the inferred-household programme. A better-evidenced named building "
                  "substitutes for this roof rather than standing beside it.")

    spec_note = (f"Type-level choice within the {b['family']} band in the reconstruction "
                 f"specification; it is not evidence for this building.")
    # ROADMAP K33: the citation is restricted to the values the family actually authors
    # something for, BEFORE the programme's own overrides land — those carry authored
    # notes of their own and are not this parcel's to rewrite.
    # ...and T-0179's other half lands in the same place: where the family's roof line
    # offers a SHED this town does not build, the record says so and says by how much.
    form = note_refusal(
        split_notes(inferred_form(b["archetype"], b["family"], spec_note, bid, w, d,
                                  building_documented=documented),
                    b["family"], spec_note),
        b["family"], w, d)
    for key, value in (form_over or {}).items():
        form[key] = attested(value, "reconstructed", [ANDREAS] if documented else [SPEC],
                             p.get("form_note") or spec_note)

    phase = {
        "id": phase_id,
        "documented_range": {
            "from": p.get("from", "1835-01-01") if documented else "1835-01-01",
            "to": "1835-12-31",
            "confidence": exist_conf,
            **({"sources": list(exist_src)} if exist_src else {}),
            "note": exist_note,
        },
        "position": {
            "utm_e": round(float(datum["origin_utm_e"]) + e0, 3),
            "utm_n": round(float(datum["origin_utm_n"]) + n0, 3),
            "rotation_deg": float(b["rotation_deg"]),
            "symbolic_location": b.get("symbolic_location") or p.get("symbolic_location")
            or (f"{b['district'].capitalize()} Division, standing on the "
                f"{b['frontage']['face']} frontage of {b['frontage']['block']}, "
                f"{float(b['frontage']['west_wall_along_m']):.1f} m along that face"
                if b.get("frontage") else
                f"{b['district'].capitalize()} Division, local ENU E {ce:g} N {cn:g}"),
            "confidence": pos_conf,
            **({"sources": list(pos_src)} if pos_src else {}),
            "note": pos_note,
            "derivation": {
                "method": "not_derivable",
                "reason": FACE_DERIVATION_REASON if b.get("frontage") else
                          ("No source gives this building a lot. The placement is a frontage-band "
                           "assignment tested for clearance and buildable ground, which is a "
                           "production control and not a derivation from any line in the "
                           "dataset."),
            },
        },
        "footprint": {
            "polygon": [[0, 0], [w, 0], [w, d], [0, d]],
            "confidence": "reconstructed",
            "note": foot_note,
        },
        "form": form,
        "change_note": change,
    }
    if p.get("ground_contact"):
        state, note = p["ground_contact"]
        phase["ground_contact"] = {"state": state, "note": note}

    # K21 — the family band, in a field a gate can read.
    #
    # Every one of these 31 buildings was dealt a crosswalk family by the
    # programme, and every one has always SAID so: the footprint note above reads
    # "a 16 x 22 ft rectangle from the D3 family band", and the form notes cite the
    # same band attribute by attribute. What no record carried was the band as a
    # VALUE. Rule 6 of the programme's method asks whether a roof's family is one
    # this layer already houses a trade in, and for a trade housed only here the
    # question had no answer — not "no", which is a refusal, but nothing, which is
    # an unanswered question wearing a refusal's clothes. T-A5 refused the two
    # sawyer households on exactly that silence.
    #
    # So this writes down a value the programme already committed. It is a
    # transcription, not a claim: `b["family"]` is read from the recipe, the same
    # string the prose has been printing all along, and nothing here decides
    # anything about a building. That is why it owes docs/LIBERTIES.md nothing —
    # a liberty is an invention, and no invention is made by recording what was
    # already committed in two other places.
    #
    # `status` is its own value rather than `inferred_anonymous`, because these
    # roofs are the opposite of anonymous: each exists for a named-nowhere but
    # argued household, carries an occupants block, and consumes a programme slot
    # rather than filling one by aggregate mix. Reusing the anonymous word would
    # have told popup.js to print "anonymous roof" over a building whose whole
    # reason for existing is the household in it.
    household_layer = None if documented else {
        "status": "inferred_household",
        "family": b["family"],
        "district": b["district"],
        "programme_phase": "phase2_inferred_households",
        "source_id": SPEC,
        "occupation": b["occupation"],
    }

    record = {
        "id": bid,
        "name": name,
        "archetype": b["archetype"],
        "phases": [phase],
        "function": attested(function_value, func_conf, func_src, func_note),
        "occupants": attested(
            p["occupants_value"] if documented else "A reconstructed household; no name is claimed",
            occ_conf, occ_src, occ_note),
        **({"reconstruction": household_layer} if household_layer else {}),
        "research_note": research,
        "review_required": False,
    }
    return record


# --------------------------------------------------------------------------
# geometry gates
# --------------------------------------------------------------------------

def world_polygon(pos: dict, poly: list, origin: tuple) -> list:
    th = math.radians(float(pos.get("rotation_deg") or 0))
    cos, sin = math.cos(th), math.sin(th)
    e0 = float(pos["utm_e"]) - origin[0]
    n0 = float(pos["utm_n"]) - origin[1]
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def rect_polygon(ce, cn, wft, dft, bearing) -> list:
    w, d = wft * FT, dft * FT
    th = math.radians(bearing)
    cos, sin = math.cos(th), math.sin(th)
    return [(ce + u * cos + v * sin, cn - u * sin + v * cos)
            for u, v in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]


def overlaps(a: list, b: list, pad: float = 0.0) -> bool:
    """Convex SAT with a separation pad; touching or near-touching counts as a hit."""
    for poly in (a, b):
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            ax, ay = -(q[1] - p[1]), q[0] - p[0]
            length = math.hypot(ax, ay) or 1.0
            ax, ay = ax / length, ay / length
            pa = [x * ax + y * ay for x, y in a]
            pb = [x * ax + y * ay for x, y in b]
            if max(pa) <= min(pb) + pad or max(pb) <= min(pa) + pad:
                return False
    return True


def reserved_slots() -> list[tuple[str, list]]:
    out = []
    west = load(RESERVED[0])
    for slot in west.get("placements", []):
        ce, cn = slot["center_local_enu_m"]
        wft, dft = slot["footprint_ft"]
        out.append((f"west recipe {slot['id']}", rect_polygon(ce, cn, wft, dft,
                                                              slot.get("rotation_deg", 0))))
    south = load(RESERVED[1])
    for cluster in south.get("clusters", []):
        for slot in cluster.get("placements", []):
            sid, e, n, _fam, wft, dft, bearing, _cls = slot
            out.append((f"south phase-2 recipe {sid}", rect_polygon(e, n, wft, dft, bearing)))
    return out


def validate(records: list[dict], households: list[dict], programme: dict, datum: dict) -> None:
    origin = (float(datum["origin_utm_e"]), float(datum["origin_utm_n"]))

    # every form must resolve through an implemented archetype
    for record in records:
        module = importlib.import_module(f"archetypes.{record['archetype']}_params")
        module.from_phase(record["phases"][0])

    # nothing may be stacked on anything: existing records, reserved slots, each other
    mine = [(r["id"], world_polygon(r["phases"][0]["position"],
                                    r["phases"][0]["footprint"]["polygon"], origin))
            for r in records]
    new_ids = {r["id"] for r in records}
    existing = []
    # A DECLARED PARTY WALL IS NOT A COLLISION (T-0077). The three-metre rule below
    # exists to stop two records occupying one yard, and until this scene had a street
    # front that was the only way two footprints ever came to touch. It is not the only
    # way now: the plate of Lake and Dearborn shows buildings shoulder to shoulder on
    # shared party lines, and a run built that way abuts whatever already stands on the
    # face. So the exemption is exactly as wide as the claim that earns it — a record
    # that NAMES this building in its own `reconstruction.frontage.abuts`, which is
    # written into the record, re-derived by the generator that placed it, and gated by
    # `check_frontage` there to be a shared wall rather than a near miss. Anything else,
    # including a building that merely happens to be close, still fails.
    abutted = set()
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load(path)
        if doc.get("id") in new_ids:
            continue
        target = ((doc.get("reconstruction") or {}).get("frontage") or {}).get("abuts")
        if target:
            abutted.add((doc["id"], target))
        for phase in doc.get("phases", []):
            pos = phase.get("position") or {}
            poly = (phase.get("footprint") or {}).get("polygon")
            if pos.get("utm_e") is None or not poly:
                continue
            existing.append((doc["id"], world_polygon(pos, poly, origin)))
    for name, poly in existing + reserved_slots():
        for sid, other in mine:
            if (name, sid) in abutted:
                continue
            if overlaps(poly, other, -3.0):
                raise SystemExit(f"{sid} is within 3 m of {name}")
    for i, (sid, poly) in enumerate(mine):
        for other_sid, other in mine[:i]:
            if overlaps(poly, other, -3.0):
                raise SystemExit(f"{sid} is within 3 m of {other_sid}")

    # and nothing may stand in the platted roadway. The plat is a LEGAL corridor rather
    # than a travelled way - L79 puts the visible tracks at 5.8-10.5 m inside 80 ft - and
    # a real building did sometimes encroach: the Sauganash's first cabin is the standing
    # reminder. But an INVENTED placement has nothing to encroach with. Where a record's
    # position is a frontage-band assignment rather than a finding, standing in the road
    # is a defect in this generator, and the grid is the only thing that can see it.
    from plat_corridors import corridors, intrusion  # noqa: PLC0415
    lanes = corridors()
    for sid, poly in mine:
        street, depth = intrusion(poly, lanes)
        if street:
            raise SystemExit(f"{sid} stands {depth:.1f} m inside the platted "
                             f"{lanes[street]['name']} corridor")

    # buildable ground, on the same committed surface the walker uses
    from heightfield import Heightfield  # noqa: PLC0415
    field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    if field is None:
        raise SystemExit("cannot validate placements: the committed heightfield is missing")
    declared = {r["id"] for r in records if r["phases"][0].get("ground_contact")}
    for sid, poly in mine:
        pts = []
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            steps = max(2, int(math.dist(a, b)))
            pts += [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
                    for k in range(steps)]
        covered = all(field.covers(e, n) for e, n in pts)
        if sid in declared:
            if covered:
                raise SystemExit(f"{sid} declares ground_contact and stands on modelled ground")
            continue
        if not covered:
            raise SystemExit(f"{sid} falls outside the modelled terrain and declares nothing")
        heights = [field.height(e, n) for e, n in pts]
        if min(heights) < -.10:
            raise SystemExit(f"{sid} stands on the water side of the terrain")
        if max(heights) - min(heights) > .30:
            raise SystemExit(f"{sid} spans {max(heights) - min(heights):.2f} m of relief")

    # the census and the households have to agree, in both directions
    census = {c["occupation"]: c for c in programme["occupation_census"]}
    counted: dict[str, int] = {}
    for h in households:
        counted[h["occupation"]] = counted.get(h["occupation"], 0) + 1
    for occ, c in census.items():
        if counted.get(occ, 0) != c["inferred_households"]:
            raise SystemExit(f"census says {c['inferred_households']} {occ} household(s), "
                             f"the recipe deals {counted.get(occ, 0)}")
    for occ in counted:
        if occ not in census:
            raise SystemExit(f"household trade '{occ}' has no entry in the occupation census")

    # one roof, one household living in it; and no household is homeless. A WORKPLACE
    # MAY BE SHARED - a sawpit is worked by two men by definition, and a shop with a
    # journeyman in it is the reason the journeyman is in the record - so only the
    # dwelling link is exclusive.
    homes: dict[str, str] = {}
    for h in households:
        sid = h.get("lives_at")
        if not sid:
            raise SystemExit(f"{h['id']} has no dwelling; the layer exists to house households")
        if sid in homes:
            raise SystemExit(f"{sid} is the dwelling of both {homes[sid]} and {h['id']}")
        homes[sid] = h["id"]

    # K21 — every roof this layer stands a household on must name its family band.
    #
    # This is the gate that keeps rule 6's second test ANSWERABLE. The test asks
    # whether a block roof's family is one this layer already houses that trade in,
    # and it can only be evaluated against the families the layer's own roofs
    # carry. A roof with no family in it does not answer "no" — it answers
    # nothing, and a trade housed only on such roofs falls out of the test
    # entirely. Four of them did (brickmaker, packer, sawyer, wheelwright), and
    # eight more were partly out; T-A5 refused an adoption on that silence and
    # could not tell the refusal apart from an unanswered question.
    #
    # It is deliberately stated over BOTH links, not just the dwelling. A trade's
    # workshop family is as much a claim about the town as its dwelling family,
    # and the works_at side is where the shop families (W*, C*) live.
    crosswalk = {f["id"] for f in load(
        DATA / "reconstruction" / "1835_family_archetype_crosswalk.json")["families"]}
    by_id = {r["id"]: r for r in records}
    for h in households:
        for key in ("lives_at", "works_at"):
            sid = h.get(key)
            if not sid:
                continue
            doc = by_id.get(sid)
            if doc is None:
                path = STRUCTURES / f"{sid}.json"
                if not path.exists():
                    raise SystemExit(f"{h['id']} {key.replace('_', ' ')} {sid}, which no "
                                     f"structure record builds")
                doc = load(path)
            family = (doc.get("reconstruction") or {}).get("family")
            if not family:
                raise SystemExit(
                    f"{h['id']} {key.replace('_', ' ')} {sid}, which names no family band: "
                    f"rule 6's family test cannot be evaluated for a {h['occupation']} and "
                    f"would go silent rather than negative. Give the roof a reconstruction "
                    f"block, or amend rule 6 to name the case explicitly (docs/ROADMAP.md K21)")
            if family not in crosswalk:
                raise SystemExit(f"{sid} names family {family}, which is not in "
                                 f"1835_family_archetype_crosswalk.json")

    # K28 — the two clauses rule 6 gained on 2026-08-16, gated so they are rules
    # rather than the habit nine block parcels supplied them with.
    #
    # An ADOPTION is a household living under a roof this programme did not raise:
    # the roof was already on the plat, put there by a block parcel, and rule 6 is
    # the only thing standing between a drawing and a claim about the town's trade
    # mix. `reconstruction.block_id` is what makes the block readable off the roof.
    raised = {b["id"] for b in programme["buildings"]}
    census = {e["occupation"]: e for e in programme["occupation_census"]}
    adoptions: dict[tuple[str, str], list[str]] = {}
    for h in households:
        sid = h.get("lives_at")
        if not sid or sid in raised:
            continue
        doc = by_id.get(sid) or (load(STRUCTURES / f"{sid}.json")
                                 if (STRUCTURES / f"{sid}.json").exists() else None)
        block = ((doc or {}).get("reconstruction") or {}).get("block_id")
        if not block:
            continue
        adoptions.setdefault((block, h["occupation"]), []).append(h["id"])

        # rule 6 test 1, clause (iii): the trade's OWN committed argument has to
        # call its count a floor. Method rule 3's list of unbounded trades is a
        # statement about where a number came from, not that the number is too
        # low, and reading test 1 off that list would let a block being dealt a D2
        # hand the laundresses a floor they never claimed. The predicate is
        # imported from tools/measure_adoption_tests.py rather than restated, so
        # the gate and the report can never disagree about what a floor is.
        entry = census.get(h["occupation"])
        if entry is None:
            raise SystemExit(f"{h['id']} is a {h['occupation']}, which the occupation "
                             f"census does not carry, so rule 6 test 1 cannot be read")
        if not floor_evidence(entry["argument"]):
            raise SystemExit(
                f"{h['id']} adopts the block roof {sid}, but the {h['occupation']} "
                f"argument never states in its own committed text that its count is a "
                f"floor, so rule 6 test 1 fails (K28 clause iii). If that count really "
                f"is a floor, argue it in the trade's own argument from the town — not "
                f"as a side effect of a block being dealt this roof")

    # rule 6 clause (ii): one adoption per trade per block parcel. Passing all
    # three tests is permission, not an instruction; without the cap the
    # granularity of the plat sets the rate at which this census grows, which is
    # the fitting-the-model-to-the-drawing rule 6 opens by forbidding.
    for (block, trade), ids in sorted(adoptions.items()):
        if len(ids) > 1:
            raise SystemExit(
                f"{block} adopts {len(ids)} {trade} households ({', '.join(sorted(ids))}): "
                f"rule 6 caps a block parcel at ONE adoption per trade (K28 clause ii). "
                f"Passing all three tests is permission and not an instruction")

    # the 665-roof programme is a ceiling, not a budget to overspend
    inventory = load(INVENTORY)
    by_district: dict[str, int] = {}
    for path in sorted(STRUCTURES.glob("recon_*.json")):
        doc = load(path)
        by_district[doc["reconstruction"]["district"]] = \
            by_district.get(doc["reconstruction"]["district"], 0) + 1
    for b in programme["buildings"]:
        by_district[b["district"]] = by_district.get(b["district"], 0) + 1
    for district, count in sorted(by_district.items()):
        target = inventory["districts"][district]["target"]
        if count > target:
            raise SystemExit(f"{district}: {count} inferred roofs against a programme target of "
                             f"{target}")


# --------------------------------------------------------------------------
# expansion
# --------------------------------------------------------------------------

def build_all() -> tuple[dict[Path, str], list[dict], list[dict]]:
    programme = load(PROGRAMME)
    resolve_placements(programme)
    resolve_corridor_clearance(programme)
    datum = load(DATA / "datum.json")
    census = {c["occupation"]: c for c in programme["occupation_census"]}
    buildings = {b["id"]: b for b in programme["buildings"]}
    prose = programme["building_prose"]

    hh_by_building: dict[str, list[str]] = {}
    for h in programme["households"]:
        for key in ("lives_at", "works_at"):
            sid = h.get(key)
            if sid in buildings:
                hh_by_building.setdefault(sid, [])
                if h["id"] not in hh_by_building[sid]:
                    hh_by_building[sid].append(h["id"])
    for link in programme["documented_household_links"]:
        for key in ("lives_at", "works_at"):
            sid = link.get(key)
            if sid in buildings:
                hh_by_building.setdefault(sid, [])
                if link["household"] not in hh_by_building[sid]:
                    hh_by_building[sid].append(link["household"])

    records = [structure_record(b, datum, prose, hh_by_building)
               for b in programme["buildings"]]
    deal_siding(records)
    households = [household_record(h, census, buildings) for h in programme["households"]]
    validate(records, programme["households"], programme, datum)

    files: dict[Path, str] = {}
    for record in records:
        files[STRUCTURES / f"{record['id']}.json"] = dumps(record, 2)
    for h in households:
        files[HOUSEHOLDS / f"{h['id']}.json"] = dumps(h, 1)

    # the documented households whose buildings this parcel finally builds
    documented_updates = []
    for link in programme["documented_household_links"]:
        path = HOUSEHOLDS / f"{link['household']}.json"
        doc = load(path)
        for key in ("lives_at", "works_at"):
            if link.get(key):
                doc[key] = {
                    "value": link[key],
                    "confidence": "attested",
                    "sources": [ANDREAS],
                    "note": link["note"] + " Linked by the inferred-household programme's "
                                           "building parcel (docs/ROADMAP.md K1, phase two); the "
                                           "building record carries the evidence.",
                }
        files[path] = dumps(doc, 1)
        documented_updates.append(doc)

    # the manifest
    index = load(INDEX)
    vocab = index["vocabulary"]
    if "labourer" not in vocab["occupations"]:
        vocab["occupations"] = sorted(set(vocab["occupations"]) | {"labourer"})
    # The vocabulary is a contract (validate.py checks it exactly), so it is
    # stated here rather than carried forward from whatever the file happened to
    # say. The three levels were renamed and this list is the one place that
    # would otherwise still be quoting the old ones.
    vocab["grades"] = ["attested", "inferred", "reconstructed"]

    # THE MANIFEST HAS ONE OWNER (T-0715). This programme used to rebuild its own
    # PREFIX rows and patch the rest in place, which left every row no pass owns
    # carrying whatever the last writer happened to leave. `final` is the layer as
    # this run leaves it: the records it just wrote, over the cards on disk.
    final = {path: json.loads(text) for path, text in files.items()
             if path != INDEX and path.parent == HOUSEHOLDS}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        final.setdefault(path, load(path))
    rebuild(index, final)
    files[INDEX] = dumps(index, 1)
    return files, records, households


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="report drift in the fields this pass still owns")
    parser.add_argument("--write-anyway", action="store_true",
                        help="write, knowing it reverses the owner's T-0489 ruling")
    args = parser.parse_args()
    files, records, households = build_all()

    # WHAT THIS PASS STILL OWNS, AND WHY THE COMPARISON IS NOT BYTE-IDENTITY (T-1228).
    #
    # Until 2026-09-17 this compared its whole output against the tree, after
    # overlaying the naming pass and the newspaper deal, because those two rewrite
    # the same household files and a raw comparison would have reported all eighty
    # as drift. That modelled the pipeline correctly and still could not pass: on
    # 2026-09-02 the owner's T-0489 ruling retired the reconstructed resident
    # population and kept the geometry as anonymous stock, and nothing told this
    # generator. It still derives all 101 households — 96 of which the ruling
    # removed — and still derives an occupant for each of the 31 roofs the ruling
    # emptied. Byte-identity against the tree is therefore a demand that the ruling
    # be reversed, once per commit, which is why this could not be gated.
    #
    # What it IS still the last writer of is the geometry the owner kept: 38
    # structure records, minus the three paths T-0489 withdrew on 31 of them and
    # the paths four later tickets took (T-0415's renamed Wright pair, T-0884's
    # move of the Heacock house onto Monroe, T-0230's function note on the
    # physician's office). That settlement is authored at
    # data/reconstruction/1835_inferred_household_pass_ownership.json, and the
    # withdrawn paths are ASSERTED rather than skipped — a retired household that
    # reappears, or an `occupants` block that stops saying anonymous stock, is red
    # here. tools/inferred_household_ownership.py holds both halves.
    if args.check:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import inferred_household_ownership as ownership  # noqa: PLC0415

        drift = ownership.check_households_pass(files)
        if drift:
            print("INFERRED HOUSEHOLD PROGRAMME DRIFT")
            for item in drift:
                print(f"  - {item}")
            return 1
        owned = ownership.settlement()["passes"][
            "tools/generate_inferred_households.py"]["still_owns"]["data/structures"]
        print(f"   OK: {len(owned['ids'])} structure record(s) re-derive in every field "
              f"this pass still owns, and T-0489's retirement stands on all of them")

    elif not args.write_anyway:
        # Writing is the reversal itself. This run watched it try: regenerating
        # inf_cooperage_south_branch whole re-claimed the withdrawn occupant, put
        # `status` back to `inferred_household` and dropped the resident_assignment
        # block T-0489 wrote. A tool that can undo an owner ruling by being run
        # without an argument is a hazard, so it now says so and stops.
        print("REFUSING TO WRITE. The owner's T-0489 ruling of 2026-09-02 retired the "
              "reconstructed\nresident population this pass derives and kept the geometry "
              "as anonymous stock.\nWriting would put all 96 retired households back and "
              "re-claim the occupants of the\n31 roofs the ruling emptied — see "
              "data/reconstruction/1835_inferred_household_pass_ownership.json.\n"
              "Use --check to re-derive what this pass still owns, or --write-anyway if "
              "reversing\nthat ruling is genuinely what you were asked to do.")
        return 2

    else:
        for path, text in sorted(files.items()):
            path.write_text(text, encoding="utf-8")

    # WHAT THE PROGRAMME ARGUES, which is not what the tree holds: since T-0489
    # the households below are the recipe's reasoning, kept as history, and not a
    # population. The figure is printed as the programme's, not the town's.
    persons = sum(len(h["persons"]) for h in households)
    adopted = len({sid for h in load(PROGRAMME)["households"]
                   for sid in (h.get("lives_at"), h.get("works_at"))
                   if sid and sid.startswith("recon_")})
    print(f"   the programme still argues {len(households)} households "
          f"({persons} persons) behind {len(records)} structure records, "
          f"{adopted} anonymous roofs adopted; T-0489 retired the households "
          f"and kept the roofs")
    # K21: the figure the gate above guarantees, printed rather than assumed. A
    # trade whose dwelling families are known is a trade rule 6's second test can
    # be evaluated for; before this parcel four of them could not be, and the
    # refusal that followed was indistinguishable from an unanswered question.
    programme = load(PROGRAMME)
    dwellings = {r["id"]: r for r in records}
    trades: dict[str, set] = {}
    for h in programme["households"]:
        doc = dwellings.get(h["lives_at"]) or load(STRUCTURES / f"{h['lives_at']}.json")
        trades.setdefault(h["occupation"], set()).add(doc["reconstruction"]["family"])
    print(f"  rule 6 family test: {len(trades)} of "
          f"{len(programme['occupation_census'])} census trades resolve, "
          f"{sum(len(v) for v in trades.values())} trade-family pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
