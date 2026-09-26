#!/usr/bin/env python3
"""THE GROUND THE PLAT DOES NOT DRAW, AND THE HOUSEHOLDS IT CAN HOLD.

T-1614, piece 2 of 3 of T-1199.

    tools/seat_off_plat_ground_1835.py --build      write the ledger and the deal
    tools/seat_off_plat_ground_1835.py --check      re-derive both, refuse drift
    tools/seat_off_plat_ground_1835.py --report     the ground by kind, the deal by clause
    tools/seat_off_plat_ground_1835.py --self-test  the guards, fired on the real data

## WHAT T-1613 HANDED ON

The plat's own lot ledger enumerated 226 lots and seated 106 of the 1,480 households the
address book leaves standing at a BAND. The other 1,374 were not refused: each carries a
written reason and `handed_to: T-1614`, and this is that file. Three of the bands name
ground the committed plat does not draw by their clause's own terms — the farms and
country seats, the heavy and noxious trades, and `division_ground`, the band for a head
whose trade no dwelling clause reaches — and the rest simply overflowed a plat that had
no free roof left of a family their clause admits.

## SO THIS WRITES TWO FILES, THE SAME PAIR AND THE SAME SHAPE

`data/reconstruction/1835_off_plat_ledger.json` — one row per parcel of committed ground
the plat's lot ledger does not draw. Five kinds, finest line first:

  * the TIER LOTS — 56 on the North Division tier under Kinzie (T-1457) and 80 in the
    School Section tier between Madison and Monroe (T-1466). Both plats draw lot lines
    and both files were written after the Thompson lot grid was closed, so neither lot
    is in the 226.
  * the TIER BLOCKS left whole — 2 School Section blocks whose own file withholds their
    subdivision.
  * the ADDITION BLOCKS — Kinzie's Addition, 27 blocks with a boundary, a numeral and a
    ground reading and NO LOT LINE. Its own grid says why: no lot rule has been read for
    that plat, and carrying the Original Town's four-to-a-face module across the river
    would be a guess dressed as arithmetic. A block is as fine a line as this project
    holds there, and this ledger does not invent a finer one.
  * the SURVEY TRACTS — the 7 placed chips of the 1834 survey colour key: the U.S.
    Military Reservation, the Canal Commissioners' 1830 survey, Wabansia, Kinzie's
    Addition, the School Section, Fractional Section 15 and the Canal Section 9
    remainder. This is the farms-and-country-seats ground, and it is the only ground in
    the file with no street line at all.
  * the CAMP GROUNDS — the 5 candidates of T-1214, carried by NAME and no polygon,
    because that file authors no vertex and this one may not author one for it.

`data/reconstruction/1835_off_plat_seats.json` — the deal. The 1,374 rows T-1613 handed
on, offered this ground in the placement policy's own clause order, and given either a
named parcel or a written reason there is none.

## THE DEAL'S RULES, AND THEY ARE T-1613'S

**Adopt before raising**, and the same three refusals: a documented building is never
re-tenanted, a roof whose record states its occupancy is left alone, and an ancillary
family is not a dwelling.

**A roof's division is the roof's own.** On the plat a lot's district came from the
665-roof programme's schedule row. Off the plat most parcels have no schedule row at
all, so the division test is made against `reconstruction.district` — a field every one
of the 320 reconstruction records carries — and a parcel's district is a REPORTED field,
read off the schedule where there is a row and left null where there is not.

**The `ground:` terms are spent here.** T-1613 scored `class:`, `street:` and `lot:` and
said in as many words that the policy vocabulary's `ground:` terms "are about unplatted
ground and are the successor ticket's". They are scored now, off committed fields only:
`outside_plat` on every parcel in this file by construction, `unplatted` where no lot
line is drawn, and `wet` where the parcel's own ground sample reports metres below the
datum. Two of the vocabulary's five ground terms — `branch` and `river_frontage` — are
NOT scored, because no committed off-plat parcel record answers them; the file says so
rather than guessing, and `unscored_ground_terms` carries it.

## WHY NOTHING IS RAISED HERE, WHICH IS THE FINDING AND NOT AN OMISSION

A slot may be raised only on a block the 665-roof programme's schedule marks `open`,
inside its committed family plan and up to its headroom. Of the 177 parcels in this
ledger, the 27 addition blocks are the only ones the schedule carries a row for at all,
and it marks every one of them `unsubdivided` with zero headroom, waiting on that plat's
own lot rule. The 136 tier lots, the 2 whole tier blocks, the 7 tracts and the 5 camp
grounds have no schedule row of any kind: 150 parcels of committed, surveyed, drawn
ground that the roof programme does not carry. So this pass raises NO slot, and every
row it cannot seat is owed against the programme's own coverage statement — *"the
binding constraint on the 668-roof programme is coverage, not recipes."*

## WHICH WAY IT IS WRONG IF IT IS WRONG

The same way its predecessor was: toward ground holding too FEW of the town's
households. It adopts what already stands and hands the rest on in writing rather than
inventing a crowd onto ground no schedule reaches. The liberty is which parcel each
household takes: docs/LIBERTIES.md L271 carries it.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DATA = ROOT / "data"

GRID = DATA / "traces" / "vectors" / "thompson_lots.json"
NORTH_TIER = DATA / "traces" / "vectors" / "north_division_tier_lots.json"
SCHOOL_TIER = DATA / "traces" / "vectors" / "school_section_tier_lots.json"
TRACTS = DATA / "reconstruction" / "1835_survey_tracts.json"
CAMPS = DATA / "reconstruction" / "1835_camp_grounds.json"
DATUM = DATA / "datum.json"
PROGRAMME = DATA / "reconstruction" / "1835_665_roof_programme.json"
POLICY = DATA / "reconstruction" / "1835_placement_policy.json"
ADDRESS_BOOK = DATA / "reconstruction" / "1835_address_book.json"
PLATTED_SEATS = DATA / "reconstruction" / "1835_platted_seats.json"
STRUCTURES = DATA / "structures"

LEDGER_OUT = DATA / "reconstruction" / "1835_off_plat_ledger.json"
SEATS_OUT = DATA / "reconstruction" / "1835_off_plat_seats.json"

TICKET = "T-1614"
PARENT = "T-1199"
PREDECESSOR = "T-1613"
SUCCESSOR = "T-1615"

FACES = ("north", "south", "east", "west")

# The North Division tier names its two rows of lots `upper` and `lower` rather than by
# compass face, because T-1457 hangs the tier on Kinzie's south kerb and carries its
# south face down by a READ depth. The upper row fronts the block's north line and the
# lower row its south line, which is the tier file's own arrangement in its `seating`
# note. A row the record names neither way is resolved from the lot's own geometry —
# north of its block's centre fronts the north line, south of it the south — and that is
# a derivation from committed vertices, not a reading of anything.
TIER_FACE = {"upper": "north", "lower": "south"}
ANCILLARY_LETTERS = ("A1", "A2", "A3", "A4", "A5")

# The ground terms the placement policy's own vocabulary lists, and which of them a
# committed off-plat parcel record can answer. A term this file cannot read is not
# scored and not asserted — see the module docstring.
GROUND_TERMS_SCORED = ("outside_plat", "unplatted", "wet")
GROUND_TERMS_UNSCORED = {
    "branch": "no committed off-plat parcel record names a branch frontage. The four "
              "documented noxious trades stand on the branches by their own positions, "
              "not by a parcel line, and this ledger authors no parcel for them.",
    "river_frontage": "the landings layer draws the bank and this file draws parcels; "
                      "no committed parcel record here names a river frontage, and "
                      "joining the two is a reading T-1214 owns, not this pass.",
}

# The band whose clause key the address book leaves null, because no dwelling clause of
# the policy reaches that head's trade. It is answered here with the reason, never a seat.
NO_CLAUSE_BAND = "division_ground"


class Fault(Exception):
    """A refusal this pass makes out loud."""


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _tree():
    """The street classes and the documented families, from the modules that own them.

    Imported inside the function for the reason `seat_platted_ground_1835._tree` gives:
    a module-level import would drag the policy module's own import circle into a data
    load.
    """
    sys.path.insert(0, str(TOOLS))
    import plat_occupancy  # noqa: E402
    from measure_frontage_fabric import documented_families, street_traffic  # noqa: E402
    return plat_occupancy, street_traffic(), documented_families()


def load() -> dict:
    occupancy, traffic, documented = _tree()
    datum = load_json(DATUM)
    grid = load_json(GRID)
    programme = load_json(PROGRAMME)
    schedule = {row["id"]: row for row in programme["schedule"]}
    policy = load_json(POLICY)
    clauses = {row["id"]: row for row in policy["clauses"]}

    records = {}
    for path in sorted(STRUCTURES.glob("*.json")):
        record = load_json(path)
        records[record["id"]] = record

    holders = occupancy.lot_holders(grid, datum)
    on_a_platted_lot = {
        structure_id
        for lots in holders.values()
        for standing in lots.values()
        for structure_id in standing
    }

    return {
        "datum": datum, "grid": grid, "programme": programme, "schedule": schedule,
        "policy": policy, "clauses": clauses, "clause_order": [c["id"] for c in policy["clauses"]],
        "records": records, "traffic": traffic, "documented": documented,
        "on_a_platted_lot": on_a_platted_lot,
        "north_tier": load_json(NORTH_TIER), "school_tier": load_json(SCHOOL_TIER),
        "tracts": load_json(TRACTS), "camps": load_json(CAMPS),
        "address_book": load_json(ADDRESS_BOOK), "platted": load_json(PLATTED_SEATS),
        "occupancy": occupancy,
    }


# ------------------------------------------------------------------------- geometry

def centroid(polygon: list) -> tuple[float, float]:
    """The mean vertex of a world polygon — enough to say which parcel a roof is on.

    The plat's own occupancy test is an AREA test (`plat_occupancy.lot_holders` gives a
    footprint to the lot it covers most of, and only if it reaches that lot's buildable
    inset), because a lot is 24 m wide and a party-line run straddles lines. Off the plat
    the parcels are blocks, tiers and whole survey tracts, hundreds of metres across, and
    a centroid answers the same question without an inset this ground has no module for.
    """
    return (sum(point[0] for point in polygon) / len(polygon),
            sum(point[1] for point in polygon) / len(polygon))


def inside(point: tuple[float, float], polygon: list) -> bool:
    """Ray casting, because the survey tracts are not convex.

    `plat_occupancy.overlap_area` clips against a CONVEX polygon and refuses anything
    else; the U.S. Military Reservation chip alone carries 60-odd vertices around the
    river mouth. This is the general test, and it is used for nothing but naming which
    parcel a roof already standing falls inside.
    """
    x, y = point
    hit = False
    count = len(polygon)
    previous = count - 1
    for current in range(count):
        xi, yi = polygon[current][0], polygon[current][1]
        xj, yj = polygon[previous][0], polygon[previous][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        previous = current
    return hit


def polygon_area(polygon: list) -> float:
    total = 0.0
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index][0], polygon[index][1]
        x2, y2 = polygon[(index + 1) % count][0], polygon[(index + 1) % count][1]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


# --------------------------------------------------------------------- the ledger

def family_of(record: dict, documented: dict[str, str]) -> str | None:
    """The family letter a standing record carries — its own, or the reconciliation's."""
    reconstruction = record.get("reconstruction") or {}
    return reconstruction.get("family") or documented.get(record["id"])


def _face_of(lot: dict, block: dict) -> str | None:
    """Which line of its block a tier lot fronts. See TIER_FACE for why it is not read."""
    tier = lot.get("tier")
    if tier in FACES:
        return tier
    if tier in TIER_FACE:
        return TIER_FACE[tier]
    boundary = block.get("boundary_local_enu_m")
    polygon = lot.get("polygon")
    if not boundary or not polygon:
        return None
    return "north" if centroid(polygon)[1] >= centroid(boundary)[1] else "south"


def _street_class(traffic: dict, fronts) -> tuple[str | None, str]:
    """The street a face fronts and that street's traffic class, or an honest absence.

    A tier block's `bounded_by` is not always a street id: T-1457 writes prose there
    where the tier's own south face is a depth carried down from Kinzie rather than a
    platted line. A value the street record does not know is not a street, and the face
    is classed `unplatted` rather than given a class it has not got.
    """
    if not isinstance(fronts, str):
        return None, "unplatted"
    traffic_class = traffic.get(fronts)
    if traffic_class is None:
        return None, "unplatted"
    return fronts, traffic_class


def _ground_tokens(reading: str | None, granularity: str) -> list[str]:
    """The `ground:` terms a parcel answers, read off committed fields and no others."""
    tokens = ["outside_plat"]
    if granularity in ("tract", "ground", "block"):
        tokens.append("unplatted")
    if reading and not reading.startswith("0 sample"):
        tokens.append("wet")
    return sorted(set(tokens))


def _schedule_fields(schedule: dict, block_id: str | None) -> dict:
    row = schedule.get(block_id) if block_id else None
    if row is None:
        return {
            "district": None,
            "district_read_from": None,
            "in_the_roof_schedule": False,
            "schedule_state": None,
            "slot_headroom": 0,
            "may_raise_a_slot": False,
            "why_no_slot": "the 665-roof programme's schedule carries no row for this "
                           "ground, so there is no committed family plan to raise a "
                           "roof inside and no headroom to draw on",
        }
    state = row.get("state")
    headroom = int(row.get("principal_room") or 0)
    return {
        "district": row.get("district"),
        "district_read_from": "the 665-roof programme's schedule row",
        "in_the_roof_schedule": True,
        "schedule_state": state,
        "slot_headroom": headroom,
        "may_raise_a_slot": state == "open" and headroom > 0,
        "why_no_slot": None if (state == "open" and headroom > 0) else
                       (row.get("waiting_on")
                        or f"the roof programme marks this ground `{state}` with "
                           f"{headroom} principal roof(s) of headroom"),
    }


def _parcel(kind: str, granularity: str, parcel_id: str, source: str, data: dict,
            *, block_id=None, lot_index=None, grid=None, plat=None, polygon=None,
            fronts_raw=None, frontage_m=None, depth_m=None, plat_lot_number=None,
            reading=None, confidence=None, note=None, area=None,
            face=None, corner=False) -> dict:
    fronts, street_class = _street_class(data["traffic"], fronts_raw)
    row = {
        "parcel_id": parcel_id,
        "kind": kind,
        "granularity": granularity,
        "source": source,
        "grid": grid,
        "plat": plat,
        "block_id": block_id,
        "lot_index": lot_index,
        "plat_lot_number": plat_lot_number,
        "face": face,
        "corner": bool(corner),
        "fronts": fronts,
        "fronts_as_written": fronts_raw if fronts is None else None,
        "street_class": street_class,
        "frontage_m": frontage_m,
        "depth_m": depth_m,
        "area_m2": round(area if area is not None
                         else (polygon_area(polygon) if polygon else 0.0), 1),
        "ground_reading": reading,
        "ground_tokens": _ground_tokens(reading, granularity),
        "confidence": confidence,
        "note": note,
    }
    row.update(_schedule_fields(data["schedule"], block_id))
    row["_polygon"] = polygon
    return row


def ledger(data: dict) -> list[dict]:
    """Every parcel of committed ground the plat's own lot ledger does not draw.

    The order is the precedence order too, finest line first: a roof standing inside a
    tier lot is reported on that lot and not on the survey tract the tier sits in, and
    the tracts overlap almost everything else in the file by construction — the School
    Section chip contains the whole School Section tier.
    """
    rows: list[dict] = []

    for source, doc, grid_name in (
            ("data/traces/vectors/north_division_tier_lots.json", data["north_tier"],
             "north_division_tier"),
            ("data/traces/vectors/school_section_tier_lots.json", data["school_tier"],
             "school_section_tier")):
        for block in doc["blocks"]:
            lots = block.get("lots") or []
            reading = (block.get("ground") or {}).get("reading")
            faces = [_face_of(lot, block) for lot in lots]
            by_face: dict[str | None, list[int]] = {}
            for index, face in enumerate(faces):
                by_face.setdefault(face, []).append(index)
            corners = {indices[0] for indices in by_face.values()}
            corners |= {indices[-1] for indices in by_face.values()}
            for index, lot in enumerate(lots):
                face = faces[index]
                fronts_raw = block.get("bounded_by", {}).get(face) if face else None
                rows.append(_parcel(
                    "tier_lot", "lot", f"{block['id']}#{index:02d}", source, data,
                    block_id=block["id"], lot_index=index, grid=block.get("grid"),
                    plat=block.get("plat"), polygon=lot.get("polygon"),
                    fronts_raw=fronts_raw, frontage_m=lot.get("frontage_m"),
                    depth_m=lot.get("depth_m"), plat_lot_number=lot.get("lot"),
                    reading=reading, confidence=block.get("confidence"),
                    face=face, corner=index in corners, note=None))
            if not lots:
                withheld = block.get("subdivision_withheld") or {}
                rows.append(_parcel(
                    "tier_block", "block", block["id"], source, data,
                    block_id=block["id"], grid=block.get("grid"), plat=block.get("plat"),
                    polygon=block.get("boundary_local_enu_m"),
                    frontage_m=block.get("frontage_m"), depth_m=block.get("depth_m"),
                    reading=reading, confidence=block.get("confidence"),
                    note=withheld.get("why") if isinstance(withheld, dict) else None,
                    area=block.get("area_m2")))

    for block in data["grid"]["blocks"]:
        if block["grid"] != "kinzies_addition":
            continue
        reading = (block.get("ground") or {}).get("reading")
        rows.append(_parcel(
            "addition_block", "block", block["id"],
            "data/traces/vectors/thompson_lots.json", data,
            block_id=block["id"], grid=block["grid"], plat=block.get("plat"),
            polygon=block.get("boundary_local_enu_m"),
            frontage_m=block.get("frontage_m"), depth_m=block.get("depth_m"),
            reading=reading, confidence=block.get("confidence"),
            note="no lot rule has been read for this plat — the block stands with its "
                 "boundary, its numeral and its ground, and the line it has not got is "
                 "a lot",
            area=block.get("area_m2")))

    for tract in data["tracts"]["tracts"]:
        if not tract.get("placed") or not tract.get("polygon_local_enu_m"):
            continue
        rows.append(_parcel(
            "survey_tract", "tract", tract["id"],
            "data/reconstruction/1835_survey_tracts.json", data,
            polygon=tract["polygon_local_enu_m"],
            confidence="documented" if tract.get("legend_text") else None,
            note=tract.get("legend_reading")))

    for camp in data["camps"]["candidates"]:
        rows.append(_parcel(
            "camp_ground", "ground", camp["id"],
            "data/reconstruction/1835_camp_grounds.json", data,
            confidence=camp.get("confidence"),
            note=f"{camp['name']} — resolved from "
                 f"{', '.join(camp.get('resolves_from') or ['no layer named'])}; this "
                 "file authors no vertex for it and neither may this one"))

    return rows


def stand_on(data: dict, parcels: list[dict]) -> None:
    """Fill each parcel's standing roofs, and each roof's parcel, by centroid.

    Only roofs that stand on NO lot of the committed plat are considered: a roof the
    plat's own ledger already reports is that ledger's, and reporting it twice would let
    one roof be adopted twice across two files.
    """
    footprints = dict(data["occupancy"].footprints(data["datum"]))
    order = [row for row in parcels if row["_polygon"]]
    placed: dict[str, str] = {}
    for row in parcels:
        row["standing"] = []
        row["standing_families"] = {}
    by_id = {row["parcel_id"]: row for row in parcels}

    for structure_id in sorted(footprints):
        if structure_id in data["on_a_platted_lot"]:
            continue
        point = centroid(footprints[structure_id])
        for row in order:
            if inside(point, row["_polygon"]):
                placed[structure_id] = row["parcel_id"]
                break

    for structure_id, parcel_id in sorted(placed.items()):
        row = by_id[parcel_id]
        row["standing"].append(structure_id)
        row["standing_families"][structure_id] = family_of(
            data["records"][structure_id], data["documented"])

    for row in parcels:
        row["standing"].sort()
        row["principal_roofs_standing"] = sum(
            1 for structure_id in row["standing"]
            if (row["standing_families"][structure_id] or "") not in ANCILLARY_LETTERS
            and row["standing_families"][structure_id])
    data["parcel_of"] = placed


# ----------------------------------------------------------------------- the deal

def adoptable(data: dict, parcels: list[dict]) -> tuple[dict[str, dict], list[dict], list[dict]]:
    """Every off-plat roof a household may be seated into, held back, or standing free.

    The third return is the roofs on NO parcel of this ledger — reconstruction roofs the
    project placed on free ground the survey chips do not cover. They are adoptable: the
    clause that takes one seats a household `on_no_committed_parcel`, which is what the
    policy's `setback_class: unplatted` already describes, and the seat says so rather
    than naming a parcel that does not contain it.
    """
    offer: dict[str, dict] = {}
    held_back: list[dict] = []
    unparcelled: list[dict] = []
    by_id = {row["parcel_id"]: row for row in parcels}

    for structure_id, record in sorted(data["records"].items()):
        if structure_id in data["on_a_platted_lot"]:
            continue
        if data["occupancy"].layer_of_record(record) != "reconstruction":
            continue
        letter = family_of(record, data["documented"])
        if letter is None or letter in ANCILLARY_LETTERS:
            continue
        parcel_id = data["parcel_of"].get(structure_id)
        parcel = by_id.get(parcel_id) if parcel_id else None
        occupants = record.get("occupants")
        if occupants:
            held_back.append({
                "structure_id": structure_id,
                "parcel_id": parcel_id,
                "family": letter,
                "why": "its own record already states an occupancy, and a policy deal "
                       "does not overturn a committed claim about the town",
                "occupants": (occupants.get("value") if isinstance(occupants, dict)
                              else str(occupants)),
            })
            continue
        offer[structure_id] = parcel
        if parcel is None:
            unparcelled.append({
                "structure_id": structure_id,
                "family": letter,
                "district": (record.get("reconstruction") or {}).get("district"),
                "why": "this roof stands off the plat and inside no parcel of this "
                       "ledger — the survey chips, the tiers and the addition do not "
                       "reach it",
            })
    held_back.sort(key=lambda row: row["structure_id"])
    unparcelled.sort(key=lambda row: row["structure_id"])
    return offer, held_back, unparcelled


def score(parcel: dict | None, clause: dict) -> int:
    """How well a parcel answers a clause's stated preferences, `ground:` terms included.

    The weighting is T-1613's — the `prefers` list is ordered, so a term is worth its own
    position in it — extended with the ground terms that file left to this one. A roof on
    no parcel scores nothing and is taken only when nothing better is free; the tie-break
    below is the structure id, so that is still deterministic.
    """
    if parcel is None:
        return 0
    prefers = clause.get("prefers") or []
    tokens = set(parcel["ground_tokens"])
    total = 0
    for position, term in enumerate(prefers):
        weight = len(prefers) - position
        if term == f"class:{parcel['street_class']}":
            total += weight
        elif term == f"street:{parcel['fronts']}":
            total += weight
        elif term == "lot:corner":
            if parcel["granularity"] == "lot" and parcel["corner"]:
                total += weight
        elif term == "lot:mid":
            if parcel["granularity"] == "lot" and not parcel["corner"]:
                total += weight
        elif term.startswith("ground:") and term.split(":", 1)[1] in tokens:
            total += weight
    for term in clause.get("avoids") or []:
        if term == f"class:{parcel['street_class']}":
            total -= len(prefers) + 1
        elif term == f"street:{parcel['fronts']}":
            total -= len(prefers) + 1
        elif term == "lot:corner" and parcel["granularity"] == "lot" and parcel["corner"]:
            total -= len(prefers) + 1
        elif term.startswith("ground:") and term.split(":", 1)[1] in tokens:
            total -= len(prefers) + 1
    return total


def in_scope(data: dict) -> list[dict]:
    """Exactly the rows T-1613 handed on, joined back to their address-book rows.

    The scope is read off the predecessor's own output rather than re-derived from the
    band list, because "the rows the plat could not hold" is the predecessor's finding
    and re-deriving it here would be a second rule for one question. The join is asserted:
    a handed-on id that is not a banded address-book row is a fault, not a skip.
    """
    book = {row["id"]: row for row in data["address_book"]["rows"]}
    rows = []
    for owed in data["platted"]["owed"]:
        row = book.get(owed["id"])
        if row is None:
            raise Fault(f"{PREDECESSOR} hands on {owed['id']}, which the address book "
                        "does not hold")
        if (row.get("seat") or {}).get("kind") != "division_band":
            raise Fault(f"{owed['id']} is handed on as banded and the address book has "
                        "it at a different rung")
        rows.append(row)
    rows.sort(key=lambda row: row["id"])
    return rows


def deal(data: dict, parcels: list[dict]) -> dict:
    """Offer the off-plat ground to every handed-on household in the policy's order."""
    offer, held_back, unparcelled = adoptable(data, parcels)
    taken: dict[str, str] = {}
    order = data["clause_order"]
    scheduled = sum(1 for parcel in parcels if parcel["in_the_roof_schedule"])
    no_slot = (
        "and no parcel of this ledger may raise one: the 665-roof programme carries a "
        f"schedule row for {scheduled} of its {len(parcels)} parcels and marks every one "
        "of them `unsubdivided` with no headroom, waiting on that plat's own lot rule")

    # WHY A CLAUSE CAME AWAY EMPTY, and the two answers are different things. Either no
    # roof of a family the clause admits stands off the plat in that division at all, or
    # one did and a clause the policy ranks ABOVE this one took it first. An owed row
    # that cannot tell a visitor which is a row with a reason that explains nothing.
    stock: dict[tuple[str, str], list[str]] = {}
    for structure_id in sorted(offer):
        record = data["records"][structure_id]
        district = (record.get("reconstruction") or {}).get("district")
        letter = family_of(record, data["documented"])
        for clause_id, clause in data["clauses"].items():
            if letter in set(clause["applies_to"]):
                stock.setdefault((district, clause_id), []).append(structure_id)
    occupied: dict[tuple[str, str], int] = {}
    for row in held_back:
        record = data["records"][row["structure_id"]]
        district = (record.get("reconstruction") or {}).get("district")
        for clause_id, clause in data["clauses"].items():
            if row["family"] in set(clause["applies_to"]):
                key = (district, clause_id)
                occupied[key] = occupied.get(key, 0) + 1

    def why_none(district: str, clause_id: str) -> str:
        held = occupied.get((district, clause_id), 0)
        pool = stock.get((district, clause_id)) or []
        if not pool:
            if held:
                said = (f"the {held} off-plat roof(s) of a family this clause admits in "
                        "this division all carry a record that states their own "
                        "occupancy, which a policy deal does not overturn, and no other "
                        "stands there")
            else:
                said = ("no roof of a family this clause admits stands off the plat in "
                        "this division at all")
            return f"{said}, {no_slot}"
        spent = sorted({taken[structure_id] for structure_id in pool
                        if structure_id in taken})
        above = [name for name in spent if name != clause_id]
        if above:
            return (f"every one of the {len(pool)} off-plat roof(s) of a family this "
                    "clause admits in this division is already spent, "
                    f"{len(pool) - sum(1 for s in pool if taken.get(s) == clause_id)} "
                    "of them by "
                    f"{', '.join(above)} — clause(s) the placement policy's own order "
                    f"ranks above {clause_id} — {no_slot}")
        return (f"every one of the {len(pool)} off-plat roof(s) of a family this clause "
                f"admits in this division is already seated under it, {no_slot}")

    seats: list[dict] = []
    owed: list[dict] = []

    def clause_rank(row: dict) -> int:
        clause_id = (row.get("seat") or {}).get("clause")
        return order.index(clause_id) if clause_id in order else len(order)

    for row in sorted(in_scope(data), key=lambda r: (clause_rank(r), r["id"])):
        seat = row["seat"]
        clause_id = seat.get("clause") or seat["id"].split("/")[-1]
        district = seat.get("division")

        if clause_id == NO_CLAUSE_BAND or clause_id not in data["clauses"]:
            owed.append({
                "id": row["id"], "kind": row["kind"], "band": seat["id"],
                "clause": clause_id, "district": district,
                "why": "the band names a division and stops — no clause of the placement "
                       "policy reaches this head's trade, so there is no rule here to "
                       "deal any ground by, on the plat or off it",
                "handed_to": SUCCESSOR,
            })
            continue

        clause = data["clauses"][clause_id]
        admitted = set(clause["applies_to"])
        candidates = [
            (structure_id, parcel) for structure_id, parcel in offer.items()
            if structure_id not in taken
            and (data["records"][structure_id].get("reconstruction") or {}).get("district")
            == district
            and family_of(data["records"][structure_id], data["documented"]) in admitted
        ]
        if candidates:
            structure_id, parcel = max(
                candidates, key=lambda pair: (score(pair[1], clause), pair[0]))
            taken[structure_id] = clause_id
            letter = family_of(data["records"][structure_id], data["documented"])
            seats.append({
                "id": row["id"], "kind": row["kind"], "name": row["name"],
                "clause": clause_id, "district": district, "band": seat["id"],
                "parcel_id": parcel["parcel_id"] if parcel else None,
                "parcel_kind": parcel["kind"] if parcel else "on_no_committed_parcel",
                "granularity": parcel["granularity"] if parcel else "unplatted",
                "block_id": parcel["block_id"] if parcel else None,
                "fronts": parcel["fronts"] if parcel else None,
                "street_class": parcel["street_class"] if parcel else "unplatted",
                "ground_tokens": parcel["ground_tokens"] if parcel else
                                 ["outside_plat", "unplatted"],
                "how": "adopted", "structure_id": structure_id, "family": letter,
                "stands_on": parcel["granularity"] if parcel else "unplatted",
                "setback_class": clause["setback_class"],
                "policy_rule": clause_id,
                "order_book_draw": None,
                "seed": row.get("seed"),
                "why": "a standing anonymous roof of a family this clause admits, off "
                       "the plat and in this household's own division: the roof is "
                       "already raised, so nothing is drawn off the order book",
            })
            continue

        owed.append({
            "id": row["id"], "kind": row["kind"], "band": seat["id"],
            "clause": clause_id, "district": district,
            "why": why_none(district, clause_id),
            "handed_to": SUCCESSOR,
        })

    return {
        "seats": seats, "owed": owed, "held_back": held_back,
        "unparcelled": unparcelled, "adoptable_offered": len(offer),
        "offered_ids": sorted(offer),
        "adoptable_unspent": [
            {"structure_id": structure_id,
             "family": family_of(data["records"][structure_id], data["documented"]),
             "district": (data["records"][structure_id].get("reconstruction")
                          or {}).get("district"),
             "parcel_id": data["parcel_of"].get(structure_id),
             "why": "no clause of the placement policy that any handed-on band names "
                    "admits this roof's family, so no household in scope could be "
                    "seated under it"}
            for structure_id in sorted(set(offer) - set(taken))],
    }


# ------------------------------------------------------------------ the invariants

def assert_the_deal_is_honest(data: dict, parcels: list[dict], dealt: dict) -> None:
    """Every refusal this pass makes about its own output, fired before it is written."""
    by_id = {row["parcel_id"]: row for row in parcels}
    if len(by_id) != len(parcels):
        raise Fault("the off-plat ledger holds two rows with one parcel id")

    plat_adopted = {seat["structure_id"] for seat in data["platted"]["seats"]
                    if seat.get("structure_id")}

    seen: set[str] = set()
    adopted: set[str] = set()
    for seat in dealt["seats"]:
        if seat["id"] in seen:
            raise Fault(f"{seat['id']} is seated twice")
        seen.add(seat["id"])
        if seat["parcel_id"] is not None and seat["parcel_id"] not in by_id:
            raise Fault(f"{seat['id']} is seated on {seat['parcel_id']}, which the "
                        "off-plat ledger does not draw")
        record = data["records"].get(seat["structure_id"])
        if record is None:
            raise Fault(f"{seat['id']} adopts {seat['structure_id']}, which is not a "
                        "committed structure")
        district = (record.get("reconstruction") or {}).get("district")
        if district != seat["district"]:
            raise Fault(f"{seat['id']} is a {seat['district']} household seated in a "
                        f"{district} roof")
        clause = data["clauses"][seat["clause"]]
        if seat["family"] not in clause["applies_to"]:
            raise Fault(f"{seat['id']} is seated in a {seat['family']} roof and its "
                        f"clause {seat['clause']} admits only "
                        f"{', '.join(clause['applies_to'])}")
        if seat["structure_id"] in adopted:
            raise Fault(f"{seat['structure_id']} is adopted twice — two households "
                        "cannot be the sole household of one roof")
        adopted.add(seat["structure_id"])
        # THE ROOF IS NOT SPENT TWICE ACROSS TWO FILES. T-1613 adopted 100 roofs on the
        # plat's own lots; every roof here stands off those lots by construction, and
        # this is the assertion that keeps it true when either file changes.
        if seat["structure_id"] in plat_adopted:
            raise Fault(f"{seat['structure_id']} is adopted here and by {PREDECESSOR} "
                        "too, which would seat two households in one roof")
        if seat["structure_id"] in data["on_a_platted_lot"]:
            raise Fault(f"{seat['structure_id']} stands on a lot of the committed plat "
                        "and is not this pass's to deal")
        if seat["order_book_draw"] is not None:
            parcel = by_id.get(seat["parcel_id"])
            if parcel is None or not parcel["may_raise_a_slot"]:
                raise Fault(f"{seat['id']} draws on the order book for ground the "
                            "665-roof programme does not mark open with headroom")
        if seat["parcel_id"] is not None and \
                seat["structure_id"] not in by_id[seat["parcel_id"]]["standing"]:
            raise Fault(f"{seat['id']} adopts {seat['structure_id']}, which does not "
                        f"stand on {seat['parcel_id']}")

    # NOBODY IS DROPPED. Every row handed on is either seated or owed, once.
    scope = {row["id"] for row in in_scope(data)}
    answered = seen | {row["id"] for row in dealt["owed"]}
    if scope != answered:
        missing = sorted(scope - answered)[:5]
        extra = sorted(answered - scope)[:5]
        raise Fault("the deal does not answer its own scope — "
                    f"{len(scope - answered)} unanswered {missing}, "
                    f"{len(answered - scope)} out of scope {extra}")
    if len(dealt["owed"]) + len(dealt["seats"]) != len(scope):
        raise Fault("a row is both seated and owed")
    for row in dealt["owed"]:
        if not row.get("why"):
            raise Fault(f"{row['id']} is owed with no reason written, and a blank is "
                        "not a stated absence")


# ---------------------------------------------------------------------- the records

def _public(parcel: dict) -> dict:
    return {key: value for key, value in parcel.items() if not key.startswith("_")}


def ledger_document(data: dict, parcels: list[dict]) -> dict:
    scheduled = [row for row in parcels if row["in_the_roof_schedule"]]
    return {
        "$schema_note": "DERIVED — regenerate with tools/seat_off_plat_ground_1835.py "
                        "--build; tools/check.sh re-derives this file",
        "id": "chicago_july_1835_off_plat_ledger",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "predecessor": PREDECESSOR,
        "target_date": data["programme"]["target_date"],
        "generated_by": "tools/seat_off_plat_ground_1835.py --build",
        "not_a_reading": "no page of any source is read here. Every field is a JOIN over "
                         "committed records: the tier files draw the lots, the lot grid "
                         "draws the addition's blocks, the survey chips draw the tracts, "
                         "the camp file names the grounds, the street record classes a "
                         "face where there is one, and the roof programme's schedule "
                         "says whether this ground may be built on at all.",
        "what_a_row_is": "one parcel of committed ground that the plat's own lot ledger "
                         "(1835_lot_ledger.json, T-1613) does not draw. `granularity` is "
                         "how fine a line this project actually holds there — a lot, a "
                         "block, a survey tract, or a named ground with no vertex at all "
                         "— and it is never finer than the record it is read from.",
        "the_precedence": "the rows are in precedence order, finest line first: tier "
                          "lots, tier blocks left whole, addition blocks, survey tracts, "
                          "camp grounds. A roof inside a tier lot is reported on that lot "
                          "and not on the tract the tier sits in, and the tracts overlap "
                          "almost everything else here by construction.",
        "unscored_ground_terms": GROUND_TERMS_UNSCORED,
        "inputs": [
            "data/traces/vectors/north_division_tier_lots.json",
            "data/traces/vectors/school_section_tier_lots.json",
            "data/traces/vectors/thompson_lots.json",
            "data/reconstruction/1835_survey_tracts.json",
            "data/reconstruction/1835_camp_grounds.json",
            "data/reconstruction/1835_665_roof_programme.json",
            "data/streets/1835.json",
            "data/structures/*.json",
            "data/datum.json",
        ],
        "counts": {
            "parcels": len(parcels),
            "by_kind": dict(sorted(Counter(row["kind"] for row in parcels).items())),
            "by_granularity": dict(sorted(
                Counter(row["granularity"] for row in parcels).items())),
            "by_street_class": dict(sorted(
                Counter(row["street_class"] for row in parcels).items())),
            "in_the_roof_schedule": len(scheduled),
            "by_schedule_state": dict(sorted(
                Counter(row["schedule_state"] for row in scheduled).items())),
            "may_raise_a_slot": sum(1 for row in parcels if row["may_raise_a_slot"]),
            "carrying_a_roof": sum(1 for row in parcels if row["standing"]),
            "principal_roofs_standing": sum(row["principal_roofs_standing"]
                                            for row in parcels),
            "ground_m2": round(math.fsum(row["area_m2"] for row in parcels), 1),
        },
        "what_the_roof_programme_does_not_carry": {
            "parcels": len(parcels) - len(scheduled),
            "of": len(parcels),
            "statement":
                f"{len(parcels) - len(scheduled)} of the {len(parcels)} parcels in this "
                "ledger have no row in the 665-roof programme's schedule of any kind — "
                "committed, surveyed, drawn ground the building programme does not carry. "
                f"The {len(scheduled)} it does carry are Kinzie's Addition, and it marks "
                "every one of them `unsubdivided` with no headroom, waiting on that "
                "plat's own lot rule. So no slot may be raised anywhere in this file, "
                "which is why this pass adopts and never raises.",
        },
        "parcels": [_public(row) for row in parcels],
    }


def seats_document(data: dict, parcels: list[dict], dealt: dict) -> dict:
    seats = dealt["seats"]
    owed = dealt["owed"]
    return {
        "$schema_note": "DERIVED — regenerate with tools/seat_off_plat_ground_1835.py "
                        "--build; tools/check.sh re-derives this file",
        "id": "chicago_july_1835_off_plat_seats",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "predecessor": PREDECESSOR,
        "successor": SUCCESSOR,
        "target_date": data["programme"]["target_date"],
        "generated_by": "tools/seat_off_plat_ground_1835.py --build",
        "not_a_reading": "no page of any source is read here. This is an adjudication "
                         "over committed records: which parcel of the ground the plat "
                         "does not draw each handed-on household takes, by the placement "
                         "policy's own clause order. docs/LIBERTIES.md L271 carries the "
                         "invention.",
        "raises_no_roof": "every seat here is an ADOPTION — a household put under a roof "
                          "that already stands, was already gated and was already paid "
                          "for in the 665-roof programme. No slot is requested anywhere "
                          "in this file, because no parcel of the off-plat ledger is "
                          "open ground in that programme's schedule. Nothing is written "
                          "to a structure record and nothing is baked.",
        "mints_nobody": "every row seated here is a household the address book already "
                        "holds and T-1613 already handed on. Nobody is invented and no "
                        "household is moved between divisions: a roof is only ever "
                        "offered to a row of its own division, tested against the "
                        "roof's own committed `reconstruction.district`.",
        "the_order": data["clause_order"],
        "the_order_is_the_policy_file_s": "the clauses are taken in the order the "
                                          "committed placement policy lists them, not in "
                                          "an order this pass chose. Where a clause finds "
                                          "the roof it wanted already spent, the clause "
                                          "ranked above it spent it, and `by_clause` "
                                          "beside `owed_by_clause` is where that shows.",
        "inputs": [
            "data/reconstruction/1835_off_plat_ledger.json (built by this tool)",
            "data/reconstruction/1835_platted_seats.json (the rows handed on)",
            "data/reconstruction/1835_address_book.json",
            "data/reconstruction/1835_placement_policy.json",
            "data/reconstruction/1835_665_roof_programme.json",
        ],
        "counts": {
            "rows_in_scope": len(seats) + len(owed),
            "seated": len(seats),
            "owed": len(owed),
            "by_how": dict(sorted(Counter(seat["how"] for seat in seats).items())),
            "by_clause": dict(sorted(Counter(seat["clause"] for seat in seats).items())),
            "by_district": dict(sorted(Counter(seat["district"] for seat in seats).items())),
            "by_family": dict(sorted(Counter(seat["family"] for seat in seats).items())),
            "by_parcel_kind": dict(sorted(
                Counter(seat["parcel_kind"] for seat in seats).items())),
            "parcels_taken": len({seat["parcel_id"] for seat in seats
                                  if seat["parcel_id"]}),
            "roofs_adopted": sum(1 for seat in seats if seat["how"] == "adopted"),
            "slots_requested": sum(1 for seat in seats if seat["how"] == "slot"),
            "owed_by_clause": dict(sorted(Counter(row["clause"] for row in owed).items())),
            "owed_by_district": dict(sorted(
                Counter(row["district"] for row in owed).items())),
            "roofs_offered_for_adoption": dealt["adoptable_offered"],
            "roofs_held_back": len(dealt["held_back"]),
            "roofs_standing_on_no_committed_parcel": len(dealt["unparcelled"]),
            "roofs_offered_and_unspent": len(dealt["adoptable_unspent"]),
        },
        "what_this_ground_could_not_hold": {
            "rows": len(owed),
            "handed_to": SUCCESSOR,
            "statement":
                f"the ground the plat does not draw seats {len(seats)} of the "
                f"{len(seats) + len(owed)} households {PREDECESSOR} handed on. The rest "
                f"is not refused: it is handed to {SUCCESSOR} with the gate named. The "
                "gate is the one the 665-roof programme states about itself — \"12 of "
                "the 262 remaining roofs stand on ground this project has already "
                "surveyed, platted and modelled… the binding constraint is coverage, "
                "not recipes\" — and off the plat it bites harder still: not one parcel "
                "of this ledger is open ground in that schedule, so a household with no "
                "standing roof free in its own division has nowhere at all to be put.",
        },
        "the_south_division_has_no_off_plat_roof": {
            "free_roofs_off_the_plat": dict(sorted(Counter(
                (data["records"][structure_id].get("reconstruction") or {}).get("district")
                for structure_id in dealt["offered_ids"]).items(), key=lambda kv: str(kv[0]))),
            "rows_owed_by_district": dict(sorted(
                Counter(row["district"] for row in owed).items())),
            "statement":
                "not one free reconstruction roof stands off the plat in the South "
                "Division: every South Division roof this project raised stands on a lot "
                "of the committed plat, and T-1613 dealt what was free of them. So the "
                f"{Counter(row['district'] for row in owed).get('south', 0)} South "
                "Division rows handed on here could not be seated by ANY clause, and "
                "their reason is a shortage of roofs rather than a shortage of clauses. "
                "It is the sharpest reading of the coverage gate in either file.",
        },
        "roofs_held_back": dealt["held_back"],
        "roofs_on_no_committed_parcel": dealt["unparcelled"],
        "roofs_offered_and_unspent": dealt["adoptable_unspent"],
        "seats": seats,
        "owed": owed,
    }


def _dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def derive():
    data = load()
    parcels = ledger(data)
    stand_on(data, parcels)
    dealt = deal(data, parcels)
    assert_the_deal_is_honest(data, parcels, dealt)
    return data, ledger_document(data, parcels), seats_document(data, parcels, dealt), \
        parcels, dealt


# ----------------------------------------------------------------------- commands

def cmd_build() -> int:
    _, ledger_doc, seats_doc, _, _ = derive()
    LEDGER_OUT.write_text(_dump(ledger_doc), encoding="utf-8")
    SEATS_OUT.write_text(_dump(seats_doc), encoding="utf-8")
    counts = seats_doc["counts"]
    parcel_counts = ledger_doc["counts"]
    print(f"OK: the off-plat ledger — {parcel_counts['parcels']} parcels the committed "
          f"plat does not draw, {parcel_counts['carrying_a_roof']} carrying a roof, "
          f"{parcel_counts['may_raise_a_slot']} that may raise a slot; and the off-plat "
          f"deal — {counts['seated']} of {counts['rows_in_scope']} handed-on households "
          f"seated, all by adoption, {counts['owed']} handed to {SUCCESSOR}; no roof "
          "raised, nothing baked")
    return 0


def cmd_check() -> int:
    for path in (LEDGER_OUT, SEATS_OUT):
        if not path.exists():
            raise Fault(f"{path.relative_to(ROOT)} has never been built — run "
                        "tools/seat_off_plat_ground_1835.py --build")
    _, ledger_doc, seats_doc, _, _ = derive()
    for path, doc in ((LEDGER_OUT, ledger_doc), (SEATS_OUT, seats_doc)):
        if path.read_text(encoding="utf-8") != _dump(doc):
            raise Fault(f"{path.relative_to(ROOT)} no longer re-derives — run "
                        "tools/seat_off_plat_ground_1835.py --build")
    print(f"OK: {ledger_doc['counts']['parcels']} off-plat parcels and "
          f"{seats_doc['counts']['seated']} off-plat seats re-derive, and the "
          f"{seats_doc['counts']['owed']} this ground cannot hold are owed in writing")
    return 0


def cmd_report() -> int:
    _, ledger_doc, seats_doc, parcels, dealt = derive()
    print("\n\033[1m== the off-plat ledger\033[0m")
    for key, value in ledger_doc["counts"].items():
        print(f"   {key:<38} {value}")
    print("\n\033[1m== the deal\033[0m")
    for key, value in seats_doc["counts"].items():
        print(f"   {key:<38} {value}")
    print("\n\033[1m== the seats, by parcel\033[0m")
    for parcel_id, count in sorted(Counter(
            seat["parcel_id"] or "(on no committed parcel)"
            for seat in dealt["seats"]).items()):
        print(f"   {parcel_id:<38} {count}")
    print("\n\033[1m== offered and unspent\033[0m")
    for row in dealt["adoptable_unspent"][:10]:
        print(f"   {row['structure_id']:<32} {row['family']}  {row['district']}")
    if len(dealt["adoptable_unspent"]) > 10:
        print(f"   … and {len(dealt['adoptable_unspent']) - 10} more")
    return 0


def _fires(what: str, thunk) -> None:
    try:
        thunk()
    except Fault:
        return
    raise Fault(f"the guard against {what} did not fire")


def cmd_self_test() -> int:
    data, _, _, parcels, dealt = derive()
    print("\n\033[1m== the guards, fired on the real data\033[0m")

    def seated_on_a_parcel_that_is_not_drawn():
        bent = json.loads(json.dumps(dealt))
        bent["seats"][0]["parcel_id"] = "blk_nowhere#99"
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("a seat on a parcel the ledger does not draw",
           seated_on_a_parcel_that_is_not_drawn)
    print("   a seat on a parcel the ledger does not draw         refused")

    def two_households_in_one_roof():
        bent = json.loads(json.dumps(dealt))
        if len(bent["seats"]) < 2:
            raise Fault("fixture needs two seats")
        bent["seats"][1]["structure_id"] = bent["seats"][0]["structure_id"]
        bent["seats"][1]["parcel_id"] = bent["seats"][0]["parcel_id"]
        bent["seats"][1]["district"] = bent["seats"][0]["district"]
        bent["seats"][1]["family"] = bent["seats"][0]["family"]
        bent["seats"][1]["clause"] = bent["seats"][0]["clause"]
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("one roof adopted twice", two_households_in_one_roof)
    print("   one standing roof adopted by two households         refused")

    def a_household_of_another_division():
        bent = json.loads(json.dumps(dealt))
        seat = bent["seats"][0]
        seat["district"] = "south" if seat["district"] != "south" else "north"
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("a household seated across a division line", a_household_of_another_division)
    print("   a household seated in another division              refused")

    def a_roof_the_plat_already_spent():
        bent = json.loads(json.dumps(dealt))
        plat = data["platted"]["seats"][0]
        bent["seats"][0]["structure_id"] = plat["structure_id"]
        bent["seats"][0]["parcel_id"] = None
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("a roof this pass and T-1613 both adopt", a_roof_the_plat_already_spent)
    print("   a roof the plat's own deal already adopted          refused")

    def a_slot_on_ground_no_schedule_opens():
        bent = json.loads(json.dumps(dealt))
        seat = bent["seats"][0]
        seat["order_book_draw"] = {"parcel_id": seat["parcel_id"],
                                   "family": seat["family"],
                                   "district": seat["district"]}
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("a slot raised on ground the roof programme does not open",
           a_slot_on_ground_no_schedule_opens)
    print("   a slot drawn on ground the schedule does not open   refused")

    def a_row_dropped():
        bent = json.loads(json.dumps(dealt))
        bent["seats"].pop()
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("a handed-on row answered by neither a seat nor a reason", a_row_dropped)
    print("   a row in scope left unanswered                      refused")

    def a_blank_reason():
        bent = json.loads(json.dumps(dealt))
        if not bent["owed"]:
            raise Fault("fixture needs an owed row")
        bent["owed"][0]["why"] = ""
        assert_the_deal_is_honest(data, parcels, bent)
    _fires("an owed row with a blank reason", a_blank_reason)
    print("   an owed row with no reason written                  refused")

    print("\nSELF-TEST PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.report:
            return cmd_report()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
