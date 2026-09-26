#!/usr/bin/env python3
"""THE PLAT'S OWN LOT LEDGER, AND THE HOUSEHOLDS THE PLATTED GROUND CAN HOLD.

T-1613, piece 1 of 3 of T-1199.

    tools/seat_platted_ground_1835.py --build      write the ledger and the deal
    tools/seat_platted_ground_1835.py --check      re-derive both, refuse drift
    tools/seat_platted_ground_1835.py --report     the ledger by block, the deal by clause
    tools/seat_platted_ground_1835.py --self-test  the guards, fired on the real data

## WHAT WAS MISSING

T-1198 built `data/reconstruction/1835_address_book.json` and got 1,691 households and
businesses as far as a BAND — "west/merchant_and_professional_dwellings" — which names a
division and a clause of the placement policy and claims no lot, no roof and no
coordinate. 1,480 of those rows stand at exactly that rung and nowhere else. T-1199 is
where a band becomes a lot, and it could not start, because the thing a seating pass has
to deal from did not exist: an enumeration of the lots.

The lots themselves have been committed since T-0221 and T-1194 —
`data/traces/vectors/thompson_lots.json` draws 226 of them across 72 blocks of five
grids — and everything a seating pass needs to ask about one was READABLE and nowhere
written down. Which street the lot fronts is `bounded_by[lot.tier]`, one dictionary
lookup away. That street's traffic class is another. Whether the lot is a corner is the
lot's position on its own face. Whether anything stands on it is
`plat_occupancy.lot_holders`, which measures it. How many principal roofs the lot may
carry is the placement policy's `multi_building_lot` rule, selected by the street class.
Six committed facts, joined nowhere, so every pass that wanted them either re-derived
them or guessed.

## SO THIS WRITES TWO FILES AND THE SECOND IS AN ADJUDICATION OVER THE FIRST

`data/reconstruction/1835_lot_ledger.json` — one row per lot of the committed plat, 226
of them, each carrying its block, its grid, its district, its plat lot number and that
number's confidence, the face it takes, the street that face fronts and that street's
traffic class, its frontage and depth, the block's ground reading, the multi-building
rule the policy puts on a lot of that class, what stands on it today and whether that
bars another roof. It is a JOIN and not a claim: every field is read off a committed
record, and a lot the grid does not draw is not in it.

`data/reconstruction/1835_platted_seats.json` — the deal. Every household the address
book leaves at a band, offered the plat in the placement policy's own order, and given
either a named lot or a written reason there is none.

## THE DEAL'S RULES, AND THEY ARE THE TICKET'S

**Adopt before raising.** A standing anonymous roof of the right family is a roof this
project has already built, already gated and already paid for in the order book. A
household that fits one takes it, and the order book is not touched: nothing is raised,
so nothing is drawn down. Only where no standing roof fits does the pass ask for a
SLOT — a request the 5C build tickets fulfil — and a slot draws its family from the open
block's own committed plan.

**Which roofs may be adopted.** The reconstruction layer's, unoccupied, of a dwelling or
trade family the clause admits. Three refusals are deliberate:

  * a DOCUMENTED building is never re-tenanted by a policy deal. 34 of the roofs on
    these lots are the research layer's, and a rule that put an invented household under
    Pruyne & Kimball's drugstore would be the reconstruction reading back as a fact.
  * a roof whose record already STATES its occupancy is left alone, including the
    sixteen that say `Anonymous stock; no occupant is claimed`. That sentence is a
    committed claim about the town (T-0516 filed it), and overturning it silently is the
    one thing a seating pass must not do. They are counted and named in the deal as held
    back, with that reason, for T-1615 to put in front of the owner.
  * an ANCILLARY family — A1 through A5, the barns, stables, privies and woodsheds — is
    not a dwelling. 48 of the 151 unoccupied roofs are ancillary and no household is
    seated in one; the policy's own clause for them is `ancillary_behind_its_own_roof`
    and it seats outbuildings, not people.

**Where a slot may be raised.** Only on a block the 665-roof programme's schedule marks
`open`, only inside that block's committed `families` plan, only up to its `headroom`,
and only onto a lot that is under its own multi-building rule. **And never onto the one
lot the schedule's own sizing keeps open** (T-1623): `lot_ceiling_principal` is
`free_lots - 1` for exactly that reason, so a free lot takes a slot only while the
block's occupied free lots are still under that ceiling, and a free lot carrying a
STANDING roof takes none at all — extending that run is a claim about the face left
between documented stores, which this pass does not measure. A lot this pass has itself
dealt a slot to does take another, up to the lot's own ceiling: that run is the one the
successor recipe names. Four roofs were refused by this on 2026-09-26 —
blk_south_water_dearborn's and blk_south_water_wells's last two each, after T-1622 built
blk_south_water_franklin's — and the owner ruled that they are refused in writing and the
households owed, rather than left standing unfulfillable. The schedule marks two
blocks open and holds 6 roofs of headroom against the remainder — its own coverage
statement says the great majority of those remaining "have nowhere to go until street
control, terrain and hydrology reach them" — and this pass does not argue with it. It spends what
the schedule offers and says what it could not spend.

**Everything else is OWED, in writing.** Three of the address book's bands name ground
the plat does not hold — `farms_and_country_seats`, `heavy_and_noxious_trades` and
`division_ground`, which is the band for a head whose trade no dwelling clause reaches —
and a row in one of them is not refused here, it is HANDED ON to T-1614 with that
reason. A row in a plat band that finds no roof and no slot is owed too, for the same
file. No row is dropped and no row is blank.

## WHICH WAY IT IS WRONG IF IT IS WRONG

Toward a plat that holds too FEW of the town's households. The deal seats what the
committed ground can carry and hands on the rest, so its error is a shortfall handed to
the next piece rather than a crowd invented onto lots the evidence does not reach. The
liberty is which lot each household takes: docs/LIBERTIES.md L270 carries it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DATA = ROOT / "data"

GRID = DATA / "traces" / "vectors" / "thompson_lots.json"
DATUM = DATA / "datum.json"
PROGRAMME = DATA / "reconstruction" / "1835_665_roof_programme.json"
POLICY = DATA / "reconstruction" / "1835_placement_policy.json"
ADDRESS_BOOK = DATA / "reconstruction" / "1835_address_book.json"
STRUCTURES = DATA / "structures"

LEDGER_OUT = DATA / "reconstruction" / "1835_lot_ledger.json"
SEATS_OUT = DATA / "reconstruction" / "1835_platted_seats.json"

TICKET = "T-1613"
PARENT = "T-1199"
SUCCESSOR = "T-1614"

FACES = ("north", "south", "east", "west")

# The placement policy's own order, as T-1199 states it: the commercial front first, then
# the better houses, then the tradesmen, then the labourers, then the lodging houses. The
# clauses the plat cannot hold are not in it — they are handed on by name, below.
DEAL_ORDER = (
    "commercial_front",
    "professional_row",
    "mechanics_streets",
    "merchant_and_professional_dwellings",
    "tradesman_dwellings",
    "labourer_dwellings",
    "lodging_near_the_landings",
)

# The bands whose ground is not inside the plat. Each carries the reason it is handed on
# rather than refused, in the words of the policy clause that puts it off the plat.
OFF_PLAT_BANDS = {
    "farms_and_country_seats":
        "the clause seats this household outside the plat by its own terms "
        "(`ground:outside_plat`); the committed lot grid is not its ground",
    "heavy_and_noxious_trades":
        "the clause seats this trade on the branches and the unplatted river frontage "
        "(`ground:branch`), which no lot of the committed grid draws",
    "division_ground":
        "the band names a division and stops — no dwelling clause of the policy reaches "
        "this head's trade, so there is no clause to deal a lot by",
}

# A family letter this pass will never seat a household into, and why.
ANCILLARY_LETTERS = ("A1", "A2", "A3", "A4", "A5")

CLASS_RANK = {"principal": 3, "ordinary": 2, "light": 1, "none": 0}


class Fault(Exception):
    """A refusal this pass makes out loud."""


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _tree():
    """The street classes and the documented families, from the modules that own them.

    Imported inside the function for the reason `placement_policy_1835._tree` gives:
    `measure_frontage_fabric` imports the policy module for its constants, and a
    module-level import here would drag that circle into a data load.
    """
    sys.path.insert(0, str(TOOLS))
    import plat_occupancy  # noqa: E402
    from measure_frontage_fabric import documented_families, street_traffic  # noqa: E402
    return plat_occupancy, street_traffic(), documented_families()


def load() -> dict:
    occupancy, traffic, documented = _tree()
    grid = load_json(GRID)
    datum = load_json(DATUM)
    programme = load_json(PROGRAMME)
    schedule = {row["id"]: row for row in programme["schedule"]}
    policy = load_json(POLICY)
    clauses = {row["id"]: row for row in policy["clauses"]}

    records = {}
    for path in sorted(STRUCTURES.glob("*.json")):
        record = load_json(path)
        records[record["id"]] = record

    holders = occupancy.lot_holders(grid, datum)
    exclusive = occupancy.exclusive_lots(grid, datum)

    return {
        "grid": grid, "datum": datum, "programme": programme, "schedule": schedule,
        "policy": policy, "clauses": clauses, "records": records,
        "holders": holders, "exclusive": exclusive,
        "traffic": traffic, "documented": documented,
        "address_book": load_json(ADDRESS_BOOK),
        "occupancy": occupancy,
    }


# --------------------------------------------------------------------- the ledger

def family_of(record: dict, documented: dict[str, str]) -> str | None:
    """The family letter a standing record carries.

    Its own `reconstruction.family` where this project raised it, and the committed
    reconciliation's `likely_family` where a source did. A record neither names — a
    bridge, a pier, the palisade — has no family and takes no part in a dwelling deal.
    """
    reconstruction = record.get("reconstruction") or {}
    return reconstruction.get("family") or documented.get(record["id"])


def corner_lots(block: dict) -> set[int]:
    """The lot indices at the ends of their own face, which is what `lot:corner` means.

    A face's first and last lot each turn a corner of the block; the lots between them
    do not. A face carrying one lot is that face's corner and its middle at once, and it
    is counted a corner — the term the clauses prefer is about the frontage a corner
    buys, and a lot holding a whole face holds both of its street lines.
    """
    by_face: dict[str, list[int]] = {}
    for index, lot in enumerate(block["lots"]):
        by_face.setdefault(lot["tier"], []).append(index)
    corners: set[int] = set()
    for face, indices in by_face.items():
        if face not in FACES:
            continue
        corners.add(indices[0])
        corners.add(indices[-1])
    return corners


def ledger(data: dict) -> list[dict]:
    """One row per lot of the committed plat, every field read off a committed record."""
    rows: list[dict] = []
    for block in data["grid"]["blocks"]:
        block_id = block["id"]
        scheduled = data["schedule"].get(block_id)
        if scheduled is None:
            raise Fault(f"{block_id} is drawn in the lot grid and absent from the "
                        "665-roof programme's schedule — one of the two is wrong")
        corners = corner_lots(block)
        held = data["holders"].get(block_id, {})
        barred = data["exclusive"].get(block_id, {})
        ground = block.get("ground") or {}
        reading = str(ground.get("reading") or "")
        for index, lot in enumerate(block["lots"]):
            face = lot["tier"]
            fronts = block.get("bounded_by", {}).get(face) if face in FACES else None
            if fronts is None:
                street_class = "unplatted" if face in FACES else "whole_block"
            else:
                street_class = data["traffic"].get(fronts) or "none"

            standing = sorted(held.get(index, []))
            families = {}
            principal = 0
            for structure_id in standing:
                letter = family_of(data["records"][structure_id], data["documented"])
                families[structure_id] = letter
                if letter is not None and letter not in ANCILLARY_LETTERS:
                    principal += 1

            party_line = street_class == "principal"
            rule = data["policy"]["multi_building_lot"][
                "principal_street_lot" if party_line else "back_street_lot"]
            maximum = int(rule["principal_roofs_max"])

            reserved = scheduled.get("reserved")
            if reserved:
                state = "reserved"
            elif principal >= maximum:
                state = "at_capacity"
            elif principal:
                state = "room"
            else:
                state = "free"

            rows.append({
                "lot_id": f"{block_id}#{index:02d}",
                "block_id": block_id,
                "lot_index": index,
                "grid": block["grid"],
                "plat": block["plat"],
                "district": scheduled["district"],
                "block_state": scheduled.get("state"),
                "plat_lot_number": lot.get("plat_lot_number"),
                "plat_lot_confidence": lot.get("plat_lot_confidence"),
                "face": face if face in FACES else "whole_block",
                "fronts": fronts,
                "street_class": street_class,
                "corner": index in corners,
                "frontage_m": lot.get("frontage_m"),
                "depth_m": lot.get("depth_m"),
                "ground_reading": reading or None,
                "dry": reading.startswith("dry") if reading else None,
                "multi_building_rule": rule["rule"],
                "principal_roofs_max": maximum,
                "standing": standing,
                "standing_families": families,
                "principal_roofs_standing": principal,
                "bars_another_roof": index in barred,
                "shared_business_front": bool(standing) and index not in barred,
                "over_its_rule": principal > maximum,
                "reserved_for": (reserved or {}).get("reserved_for"),
                "state": state,
            })
    rows.sort(key=lambda row: row["lot_id"])
    return rows


# ----------------------------------------------------------------------- the deal

def in_scope(data: dict) -> list[dict]:
    """The address book's rows that stand at a band and nowhere further.

    `seat.kind == "division_band"` is the whole test: a row the book got as far as a
    street face or a structure is already placed, and re-placing it here would be a
    second rule for one question.
    """
    rows = [row for row in data["address_book"]["rows"]
            if (row.get("seat") or {}).get("kind") == "division_band"]
    rows.sort(key=lambda row: row["id"])
    return rows


def adoptable(data: dict, lots: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    """Every standing roof a household may be seated into, and the ones held back.

    The three refusals in the module docstring, applied: the reconstruction layer only,
    unoccupied only, no ancillary family. The return is keyed on structure id and
    carries the ledger row the roof stands on, because the deal scores LOTS.
    """
    offer: dict[str, dict] = {}
    held_back: list[dict] = []
    for lot in lots:
        for structure_id in lot["standing"]:
            record = data["records"][structure_id]
            letter = lot["standing_families"][structure_id]
            layer = data["occupancy"].layer_of_record(record)
            if layer != "reconstruction":
                continue
            if letter is None or letter in ANCILLARY_LETTERS:
                continue
            occupants = record.get("occupants")
            if occupants:
                held_back.append({
                    "structure_id": structure_id,
                    "lot_id": lot["lot_id"],
                    "family": letter,
                    "why": "its own record already states an occupancy, and a policy "
                           "deal does not overturn a committed claim about the town",
                    "occupants": (occupants.get("value") if isinstance(occupants, dict)
                                  else str(occupants)),
                })
                continue
            offer[structure_id] = lot
    held_back.sort(key=lambda row: row["structure_id"])
    return offer, held_back


def score(lot: dict, clause: dict) -> int:
    """How well a lot answers a clause's stated preferences, and nothing more.

    The clause's `prefers` list is ordered, so the terms are weighted by their own
    position in it — `class:principal` first in `commercial_front` outranks
    `lot:corner` last. `avoids` subtracts. Only the terms a LOT can answer are read:
    `ground:` terms are about unplatted ground and are the successor ticket's, and
    `division:` is already satisfied, because a lot is never offered to a row of
    another division.
    """
    prefers = clause.get("prefers") or []
    total = 0
    for position, term in enumerate(prefers):
        weight = len(prefers) - position
        if term == f"class:{lot['street_class']}":
            total += weight
        elif term == f"street:{lot['fronts']}":
            total += weight
        elif term == "lot:corner" and lot["corner"]:
            total += weight
        elif term == "lot:mid" and not lot["corner"]:
            total += weight
    for term in clause.get("avoids") or []:
        if term == f"class:{lot['street_class']}":
            total -= len(prefers) + 1
    return total


def slot_plan(data: dict) -> dict[str, dict]:
    """What each open block still offers: its family plan and its headroom.

    Read off the 665-roof programme's schedule, which is the committed quota. A block the
    schedule does not mark `open` offers nothing, whatever its lots look like — that is
    the coverage gate, and this pass does not argue with it.
    """
    plan = {}
    for block_id, row in sorted(data["schedule"].items()):
        if row.get("state") != "open":
            continue
        families = {letter: count for letter, count in (row.get("families") or {}).items()
                    if letter not in ANCILLARY_LETTERS}
        # T-1623. `principal_room` is PARTY-LINE UNITS and this pass deals whole LOTS,
        # so the block's own lot-granularity ceiling comes along with it. The schedule
        # states it as `lot_ceiling_principal` and reconcile_665 derives it as
        # `free_lots - 1` — "less the one it keeps open". A block that reaches this pass
        # with neither is a block whose sizing cannot be read, and a gate may not count
        # a skip as a pass.
        ceiling = row.get("lot_ceiling_principal")
        if ceiling is None:
            free_lots = row.get("free_lots")
            if free_lots is None:
                raise Fault(
                    f"{block_id} is marked open and offers "
                    f"{sum(families.values())} principal roof(s) with neither "
                    "`lot_ceiling_principal` nor `free_lots` in its schedule row, so "
                    "the lot the sizing keeps open cannot be named (T-1623)")
            ceiling = max(0, int(free_lots) - 1)
        plan[block_id] = {
            "district": row["district"],
            "families": families,
            "headroom": int(row.get("principal_room") or 0),
            "lot_ceiling": int(ceiling),
            "dealt": 0,
        }
    return plan


def deal(data: dict, lots: list[dict]) -> dict:
    """Offer the plat to every banded household in the policy's order.

    Adoption first, a slot second, and a written reason third. Deterministic throughout:
    the rows are taken in clause order then by their own id, and a tie between two lots
    is broken on the lot id.
    """
    by_id = {lot["lot_id"]: lot for lot in lots}
    offer, held_back = adoptable(data, lots)
    taken: set[str] = set()
    plan = slot_plan(data)
    slots_on_lot: dict[str, int] = {}
    # T-1623. The block(s) whose last open lot this pass declined to spend, the lot it
    # held open, and the family letters that refusal actually cost — so both the written
    # refusal and the plan left unclaimed can say which of the two things happened. A
    # letter no clause admits is left unclaimed for the OTHER reason, and saying the
    # reserve cost it would be a false statement about the deal.
    held_open: dict[str, str] = {}
    reserve_cost: dict[str, set[str]] = {}

    rows = in_scope(data)
    seats: list[dict] = []
    owed: list[dict] = []

    def clause_rank(row: dict) -> int:
        clause_id = (row.get("seat") or {}).get("clause")
        return DEAL_ORDER.index(clause_id) if clause_id in DEAL_ORDER else len(DEAL_ORDER)

    for row in sorted(rows, key=lambda r: (clause_rank(r), r["id"])):
        seat = row["seat"]
        # A band's own id is `<division>/<clause>` and `division_ground` is the one band
        # whose clause key the book leaves null, because no dwelling clause reaches that
        # head's trade. The band still NAMES it, so the reason is read off the band
        # rather than invented here.
        clause_id = seat.get("clause") or seat["id"].split("/")[-1]
        district = seat.get("division")

        if clause_id in OFF_PLAT_BANDS:
            owed.append({"id": row["id"], "kind": row["kind"], "band": seat["id"],
                         "clause": clause_id, "district": district,
                         "why": OFF_PLAT_BANDS[clause_id], "handed_to": SUCCESSOR})
            continue
        clause = data["clauses"].get(clause_id)
        if clause is None:
            owed.append({"id": row["id"], "kind": row["kind"], "band": seat["id"],
                         "clause": clause_id, "district": district,
                         "why": "the band names no clause of the placement policy, so "
                                "there is no rule here to deal a lot by",
                         "handed_to": SUCCESSOR})
            continue

        admitted = set(clause["applies_to"])

        candidates = [
            (structure_id, lot) for structure_id, lot in offer.items()
            if structure_id not in taken
            and lot["district"] == district
            and lot["standing_families"][structure_id] in admitted
        ]
        if candidates:
            structure_id, lot = max(
                candidates, key=lambda pair: (score(pair[1], clause), pair[1]["lot_id"]))
            taken.add(structure_id)
            seats.append({
                "id": row["id"], "kind": row["kind"], "name": row["name"],
                "clause": clause_id, "district": district, "band": seat["id"],
                "lot_id": lot["lot_id"], "block_id": lot["block_id"],
                "lot_index": lot["lot_index"], "fronts": lot["fronts"],
                "street_class": lot["street_class"], "corner": lot["corner"],
                "how": "adopted", "structure_id": structure_id,
                "family": lot["standing_families"][structure_id],
                "stands_on": "street" if clause["setback_class"] == "street_line" else "lot",
                "setback_class": clause["setback_class"],
                "multi_building_rule": lot["multi_building_rule"],
                "policy_rule": clause_id,
                "order_book_draw": None,
                "seed": row.get("seed"),
                "why": "a standing anonymous roof of a family this clause admits, on a "
                       "lot of this household's own division: the roof is already "
                       "raised, so nothing is drawn off the order book",
            })
            continue

        raised = None
        reserved_open: list[str] = []
        for block_id, block in sorted(plan.items()):
            if block["district"] != district or block["dealt"] >= block["headroom"]:
                continue
            letters = sorted(letter for letter, count in block["families"].items()
                             if count > 0 and letter in admitted)
            if not letters:
                continue
            # WHICH LOTS OF AN OPEN BLOCK MAY TAKE A SLOT. `exclusive_lots` is the
            # committed map "a schedule or a generator asks before it deals a lot a
            # roof", so a lot that bars another roof is out. And the block's ground
            # reading is not read here: it is a BLOCK-level sample, the coverage
            # decision at lot granularity is the schedule's own `state`, and using both
            # would refuse ground the 665-roof programme has already accepted
            # (blk_south_water_dearborn, 2 samples below datum over a whole block, one
            # free lot).
            free = [lot for lot in lots
                    if lot["block_id"] == block_id and not lot["bars_another_roof"]]
            # T-1623 — THE ONE LOT THE SCHEDULE'S OWN SIZING KEEPS OPEN, and the run a
            # slot may not name. `principal_room` is party-line units; the schedule's
            # lot-granularity ceiling is `lot_ceiling_principal = free_lots - 1`, and
            # reconcile_665 says why in its own words: "less the one it keeps open",
            # precisely so a block is never dealt out of its open lot. Party-line
            # density above one roof per free lot is reachable only along a frontage run
            # a RECIPE NAMES, and this pass names none — so:
            #   * an unoccupied free lot may take a slot only while the block's occupied
            #     free lots are still UNDER its ceiling; the last one stays open.
            #   * a free lot already carrying a STANDING roof takes no slot. Extending
            #     that run is a claim about face this pass has not measured, and on
            #     2026-09-26 the two blocks where it would have fired had 2.84 m, 2.28 m
            #     and 4.46 m of face left between documented stores — not a roof between
            #     them.
            #   * a lot THIS PASS has already dealt a slot to does take another, up to
            #     the lot's own multi-building ceiling: that run is the one the successor
            #     recipe names, and it is how blk_south_water_franklin's two roofs were
            #     asked for together on one lot while its other lot stayed open — the
            #     request T-1622 then built.
            # The owner ruled on 2026-09-26 that the four roofs this refuses — the last
            # two blk_south_water_dearborn plans and the last two blk_south_water_wells
            # plans — are REFUSED IN WRITING and the households owed, rather than left
            # standing unfulfillable or answered by moving a block's `open` declaration
            # onto a lot that carries two documented stores.
            occupied = {lot["lot_id"] for lot in free
                        if lot["principal_roofs_standing"] > 0
                        or slots_on_lot.get(lot["lot_id"], 0) > 0}
            room = []
            for lot in free:
                if (lot["principal_roofs_standing"]
                        + slots_on_lot.get(lot["lot_id"], 0)) >= lot["principal_roofs_max"]:
                    continue
                if slots_on_lot.get(lot["lot_id"], 0) > 0:
                    room.append(lot)                     # this pass's own run
                elif lot["principal_roofs_standing"] > 0:
                    continue                             # a run only a recipe may name
                elif len(occupied) < block["lot_ceiling"]:
                    room.append(lot)                     # a free lot under the ceiling
            if not room:
                if len(occupied) >= block["lot_ceiling"]:
                    still_open = sorted(lot["lot_id"] for lot in free
                                        if lot["lot_id"] not in occupied)
                    if still_open:
                        held_open[block_id] = still_open[0]
                        reserve_cost.setdefault(block_id, set()).update(letters)
                        reserved_open.append(f"{block_id} ({still_open[0]})")
                continue
            lot = max(room, key=lambda l: (score(l, clause), l["lot_id"]))
            raised = (block_id, block, letters[0], lot)
            break

        if raised is not None:
            block_id, block, letter, lot = raised
            block["families"][letter] -= 1
            block["dealt"] += 1
            slots_on_lot[lot["lot_id"]] = slots_on_lot.get(lot["lot_id"], 0) + 1
            seats.append({
                "id": row["id"], "kind": row["kind"], "name": row["name"],
                "clause": clause_id, "district": district, "band": seat["id"],
                "lot_id": lot["lot_id"], "block_id": lot["block_id"],
                "lot_index": lot["lot_index"], "fronts": lot["fronts"],
                "street_class": lot["street_class"], "corner": lot["corner"],
                "how": "slot", "structure_id": None, "family": letter,
                "stands_on": "street" if clause["setback_class"] == "street_line" else "lot",
                "setback_class": clause["setback_class"],
                "multi_building_rule": lot["multi_building_rule"],
                "policy_rule": clause_id,
                "order_book_draw": {"block_id": block_id, "family": letter,
                                    "district": district},
                "seed": row.get("seed"),
                "why": "no standing roof of an admitted family was free in this "
                       "division, and this block's own committed plan still holds a "
                       f"{letter} roof of headroom: the slot is a request T-1200 "
                       "through T-1214 fulfil",
            })
            continue

        if reserved_open:
            # THE PLAN HAD HEADROOM AND THE GROUND DID NOT. Saying "no open block's plan
            # has headroom" here would be a false statement about the schedule, so the
            # refusal names the blocks whose last open lot it declined to spend.
            why = ("no standing roof of an admitted family was free in this division, "
                   "and every open block that still plans one has a single lot left, "
                   "which is the lot the schedule's own sizing keeps open "
                   "(`lot_ceiling_principal` = free lots less one): "
                   + ", ".join(reserved_open)
                   + ". The owner ruled on 2026-09-26 (T-1623) that a block is not "
                     "dealt out of its open lot, so the request is refused here rather "
                     "than left standing unfulfillable")
        else:
            why = ("the plat holds no free roof of a family this clause admits in this "
                   "division, and no open block's plan has headroom for one")
        owed.append({
            "id": row["id"], "kind": row["kind"], "band": seat["id"],
            "clause": clause_id, "district": district,
            "why": why,
            "handed_to": SUCCESSOR,
        })

    unclaimed = [
        {"block_id": block_id, "family": letter, "roofs": count,
         "district": block["district"],
         # T-1623. Two different reasons, and reading the second as the first is what
         # made the four refused roofs look like a plan nobody wanted.
         "why": ("a banded row of this division IS admitted by a clause that takes this "
                 f"family, and the only lot left on the block is {held_open[block_id]}, "
                 "the one the schedule's own sizing keeps open: the roof is refused "
                 "here (T-1623) and the household is owed"
                 if letter in reserve_cost.get(block_id, ()) else
                 "the plan offers this family and no banded row of this division is "
                 "admitted by a clause that takes it")}
        for block_id, block in plan.items()
        for letter, count in block["families"].items() if count > 0
    ]
    unclaimed.sort(key=lambda row: (row["block_id"], row["family"]))

    return {
        "seats": seats, "owed": owed, "held_back": held_back,
        "unclaimed_plan": unclaimed,
        "adoptable_offered": len(offer), "by_id": by_id,
    }


# ------------------------------------------------------------------ the invariants

def assert_the_deal_is_honest(data: dict, lots: list[dict], dealt: dict) -> None:
    """Every refusal this pass makes about its own output, fired before it is written.

    These are the assertions, not warnings: a pass that could write a seat onto a lot
    that does not exist, or two households into one roof, is a pass whose output cannot
    be read. Each one names the rule it is holding.
    """
    by_id = {lot["lot_id"]: lot for lot in lots}
    if len(by_id) != len(lots):
        raise Fault("the lot ledger holds two rows with one lot id")

    seen: set[str] = set()
    adopted: set[str] = set()
    slots: dict[str, int] = {}
    for seat in dealt["seats"]:
        if seat["id"] in seen:
            raise Fault(f"{seat['id']} is seated twice")
        seen.add(seat["id"])
        lot = by_id.get(seat["lot_id"])
        if lot is None:
            raise Fault(f"{seat['id']} is seated on {seat['lot_id']}, which the lot "
                        "ledger does not draw")
        if lot["district"] != seat["district"]:
            raise Fault(f"{seat['id']} is a {seat['district']} household seated on a "
                        f"{lot['district']} lot")
        clause = data["clauses"][seat["clause"]]
        if seat["family"] not in clause["applies_to"]:
            raise Fault(f"{seat['id']} is seated in a {seat['family']} roof and its "
                        f"clause {seat['clause']} admits only "
                        f"{', '.join(clause['applies_to'])}")
        if seat["how"] == "adopted":
            if seat["structure_id"] in adopted:
                raise Fault(f"{seat['structure_id']} is adopted twice — two households "
                            "cannot be the sole household of one roof")
            adopted.add(seat["structure_id"])
            if seat["structure_id"] not in lot["standing"]:
                raise Fault(f"{seat['id']} adopts {seat['structure_id']}, which does not "
                            f"stand on {seat['lot_id']}")
            if seat["order_book_draw"] is not None:
                raise Fault(f"{seat['id']} adopts a standing roof and draws on the order "
                            "book, which would spend a roof twice")
        else:
            if lot["bars_another_roof"]:
                raise Fault(f"{seat['id']} asks for a slot on {seat['lot_id']}, which the "
                            "committed exclusive-lot map says bars another roof")
            if lot["block_state"] != "open":
                raise Fault(f"{seat['id']} asks for a slot in {lot['block_id']}, which "
                            f"the roof programme marks {lot['block_state']}")
            slots[seat["lot_id"]] = slots.get(seat["lot_id"], 0) + 1
            if lot["principal_roofs_standing"] + slots[seat["lot_id"]] > \
                    lot["principal_roofs_max"]:
                raise Fault(
                    f"{seat['lot_id']} would carry "
                    f"{lot['principal_roofs_standing'] + slots[seat['lot_id']]} principal "
                    f"roofs and its {lot['multi_building_rule']} rule allows "
                    f"{lot['principal_roofs_max']}")

    # T-1623 — NO BLOCK IS DEALT OUT OF ITS OPEN LOT. The schedule sizes a block's
    # room at `lot_ceiling_principal` free lots, "less the one it keeps open", and a
    # slot is dealt at lot granularity. So after the deal, the free lots of a block
    # this pass drew on may carry a roof on no more than that many of them — which is
    # the same statement as "one free lot is still carrying nothing". A pass that could
    # spend the reserve is a pass that moves a block's `open` declaration onto a lot
    # carrying documented stores, and the owner refused that on 2026-09-26.
    free_by_block: dict[str, list[dict]] = {}
    for lot in lots:
        if not lot["bars_another_roof"]:
            free_by_block.setdefault(lot["block_id"], []).append(lot)
    for block_id in sorted({seat["block_id"] for seat in dealt["seats"]
                            if seat["how"] == "slot"}):
        row = data["schedule"].get(block_id) or {}
        ceiling = row.get("lot_ceiling_principal")
        if ceiling is None:
            free_lots = row.get("free_lots")
            if free_lots is None:
                raise Fault(f"{block_id} takes a slot and its schedule row states "
                            "neither `lot_ceiling_principal` nor `free_lots`, so the "
                            "lot its sizing keeps open cannot be named (T-1623)")
            ceiling = max(0, int(free_lots) - 1)
        occupied = sorted(
            lot["lot_id"] for lot in free_by_block.get(block_id, ())
            if lot["principal_roofs_standing"] > 0 or slots.get(lot["lot_id"], 0) > 0)
        if len(occupied) > int(ceiling):
            raise Fault(f"{block_id} would carry a roof on {len(occupied)} of its free "
                        f"lots ({', '.join(occupied)}) and the schedule sizes it at "
                        f"{ceiling} — the block keeps one lot open (T-1623)")

    # THE ORDER BOOK IS NOT EXCEEDED. Every slot draws on one open block's committed
    # family plan, and the draws per block may not pass that block's own headroom.
    drawn: dict[str, int] = {}
    per_family: dict[tuple[str, str], int] = {}
    for seat in dealt["seats"]:
        draw = seat["order_book_draw"]
        if draw is None:
            continue
        drawn[draw["block_id"]] = drawn.get(draw["block_id"], 0) + 1
        key = (draw["block_id"], draw["family"])
        per_family[key] = per_family.get(key, 0) + 1
    for block_id, count in drawn.items():
        offered = int(data["schedule"][block_id].get("principal_room") or 0)
        if count > offered:
            raise Fault(f"{block_id} is drawn {count} times and its schedule offers "
                        f"{offered} principal roof(s) of headroom")
    for (block_id, family), count in per_family.items():
        plan = int((data["schedule"][block_id].get("families") or {}).get(family, 0))
        if count > plan:
            raise Fault(f"{block_id} is drawn for {count} {family} roof(s) and its "
                        f"committed plan holds {plan}")

    # NOBODY IS DROPPED. Every row in scope is either seated or owed, once.
    scope = {row["id"] for row in in_scope(data)}
    answered = seen | {row["id"] for row in dealt["owed"]}
    if scope != answered:
        missing = sorted(scope - answered)[:5]
        extra = sorted(answered - scope)[:5]
        raise Fault("the deal does not answer its own scope — "
                    f"{len(scope - answered)} unanswered {missing}, "
                    f"{len(answered - scope)} out of scope {extra}")
    if len(dealt["owed"]) + len(seats_of(dealt)) != len(scope):
        raise Fault("a row is both seated and owed")
    for row in dealt["owed"]:
        if not row.get("why"):
            raise Fault(f"{row['id']} is owed with no reason written, and a blank is "
                        "not a stated absence")


def seats_of(dealt: dict) -> list[dict]:
    return dealt["seats"]


# ---------------------------------------------------------------------- the records

def ledger_document(data: dict, lots: list[dict]) -> dict:
    from collections import Counter
    return {
        "$schema_note": "DERIVED — regenerate with tools/seat_platted_ground_1835.py "
                        "--build; tools/check.sh re-derives this file",
        "id": "chicago_july_1835_lot_ledger",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "target_date": data["programme"]["target_date"],
        "generated_by": "tools/seat_platted_ground_1835.py --build",
        "not_a_reading": "no page of any source is read here. Every field is a JOIN over "
                         "committed records: the lot grid draws the lot, the street "
                         "record classes its frontage, plat_occupancy measures what "
                         "stands on it, and the placement policy names the "
                         "multi-building rule its street class carries.",
        "what_a_row_is": "one lot of the committed plat. `state` is what the lot can take "
                         "NOW — `free` nothing standing, `room` a principal roof standing "
                         "under the lot's own ceiling, `at_capacity` at or over it, "
                         "`reserved` a block that is not building ground.",
        "inputs": [
            "data/traces/vectors/thompson_lots.json",
            "data/reconstruction/1835_665_roof_programme.json",
            "data/reconstruction/1835_placement_policy.json",
            "data/streets/1835.json",
            "data/structures/*.json",
            "data/datum.json",
        ],
        "counts": {
            "lots": len(lots),
            "blocks": len({lot["block_id"] for lot in lots}),
            "by_grid": dict(sorted(Counter(lot["grid"] for lot in lots).items())),
            "by_district": dict(sorted(Counter(lot["district"] for lot in lots).items())),
            "by_street_class": dict(sorted(
                Counter(lot["street_class"] for lot in lots).items())),
            "by_state": dict(sorted(Counter(lot["state"] for lot in lots).items())),
            "by_multi_building_rule": dict(sorted(
                Counter(lot["multi_building_rule"] for lot in lots).items())),
            "corner_lots": sum(1 for lot in lots if lot["corner"]),
            "lots_with_a_roof": sum(1 for lot in lots if lot["standing"]),
            "lots_barring_another_roof": sum(1 for lot in lots if lot["bars_another_roof"]),
            "shared_business_fronts": sum(1 for lot in lots if lot["shared_business_front"]),
            "principal_roofs_standing": sum(lot["principal_roofs_standing"] for lot in lots),
            "lots_over_their_own_rule": sum(1 for lot in lots if lot["over_its_rule"]),
        },
        "the_density_standard": {
            "rule": data["policy"]["multi_building_lot"],
            "multi_building_lot_rate_on_the_principal_streets": _rate(lots),
        },
        "lots": lots,
    }


def _rate(lots: list[dict]) -> dict:
    """The density standard, measured: how many principal-street lots actually carry a run.

    T-1199's acceptance asks for this number against the standard, and it is a reading of
    the committed town rather than a target. A lot of a principal street may carry three
    party-line units; this says how many do.
    """
    principal = [lot for lot in lots if lot["street_class"] == "principal"]
    runs = [lot for lot in principal if lot["principal_roofs_standing"] > 1]
    return {
        "principal_street_lots": len(principal),
        "carrying_more_than_one_principal_roof": len(runs),
        "rate": round(len(runs) / len(principal), 4) if principal else None,
        "standard": "three party-line units per lot where the rule fires — the "
                    "schedule's capacity is a ceiling and not a target "
                    "(1835_platted_block_parcels.json, `placement_rule.open_lots`)",
    }


def seats_document(data: dict, lots: list[dict], dealt: dict) -> dict:
    from collections import Counter
    seats = dealt["seats"]
    owed = dealt["owed"]
    return {
        "$schema_note": "DERIVED — regenerate with tools/seat_platted_ground_1835.py "
                        "--build; tools/check.sh re-derives this file",
        "id": "chicago_july_1835_platted_seats",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "successor": SUCCESSOR,
        "target_date": data["programme"]["target_date"],
        "generated_by": "tools/seat_platted_ground_1835.py --build",
        "not_a_reading": "no page of any source is read here. This is an adjudication "
                         "over committed records: which lot of the committed plat each "
                         "banded household takes, by the placement policy's own clause "
                         "order. docs/LIBERTIES.md L270 carries the invention.",
        "raises_no_roof": "an adoption seats a household into a roof that already "
                          "stands, and a slot is a REQUEST the 5C build tickets fulfil. "
                          "No geometry is written, no structure record is touched, and "
                          "no mesh is baked by this pass.",
        "mints_nobody": "every row seated here is a household the address book already "
                        "holds. Nobody is invented and no household is moved between "
                        "divisions: a lot is only ever offered to a row of its own.",
        "the_order": list(DEAL_ORDER),
        "off_the_plat": OFF_PLAT_BANDS,
        "inputs": [
            "data/reconstruction/1835_lot_ledger.json (built by this tool)",
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
            "lots_taken": len({seat["lot_id"] for seat in seats}),
            "roofs_adopted": sum(1 for seat in seats if seat["how"] == "adopted"),
            "slots_requested": sum(1 for seat in seats if seat["how"] == "slot"),
            "owed_by_band_clause": dict(sorted(
                Counter(row["clause"] for row in owed).items())),
            "roofs_offered_for_adoption": dealt["adoptable_offered"],
            "roofs_held_back": len(dealt["held_back"]),
        },
        "what_the_plat_could_not_hold": {
            "rows": len(owed),
            "handed_to": SUCCESSOR,
            "statement":
                f"the committed plat seats {len(seats)} of the {len(seats) + len(owed)} "
                "households the address book leaves at a band. The rest is not refused: "
                f"it is handed to {SUCCESSOR}, which owns the ground the plat does not "
                "draw — the farms and country seats, the additions' small lots, the "
                "fringes and the branches. The binding constraint is the one the "
                "665-roof programme already states: coverage, not recipes.",
        },
        "roofs_held_back": dealt["held_back"],
        "plan_left_unclaimed": dealt["unclaimed_plan"],
        "seats": seats,
        "owed": owed,
    }


def _dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def derive() -> tuple[dict, dict, dict, list[dict], dict]:
    data = load()
    lots = ledger(data)
    dealt = deal(data, lots)
    assert_the_deal_is_honest(data, lots, dealt)
    return data, ledger_document(data, lots), seats_document(data, lots, dealt), lots, dealt


# ----------------------------------------------------------------------- commands

def cmd_build() -> int:
    _, ledger_doc, seats_doc, _, _ = derive()
    LEDGER_OUT.write_text(_dump(ledger_doc), encoding="utf-8")
    SEATS_OUT.write_text(_dump(seats_doc), encoding="utf-8")
    counts = seats_doc["counts"]
    lot_counts = ledger_doc["counts"]
    print(f"OK: the 1835 lot ledger — {lot_counts['lots']} lots over "
          f"{lot_counts['blocks']} blocks, {lot_counts['by_state'].get('free', 0)} free, "
          f"{lot_counts['lots_with_a_roof']} carrying a roof; and the platted deal — "
          f"{counts['seated']} of {counts['rows_in_scope']} banded households seated "
          f"({counts['roofs_adopted']} adopted, {counts['slots_requested']} slots), "
          f"{counts['owed']} handed to {SUCCESSOR}; no roof raised, nothing baked")
    return 0


def cmd_check() -> int:
    for path in (LEDGER_OUT, SEATS_OUT):
        if not path.exists():
            raise Fault(f"{path.relative_to(ROOT)} has never been built — run "
                        "tools/seat_platted_ground_1835.py --build")
    _, ledger_doc, seats_doc, _, _ = derive()
    for path, doc in ((LEDGER_OUT, ledger_doc), (SEATS_OUT, seats_doc)):
        if path.read_text(encoding="utf-8") != _dump(doc):
            raise Fault(f"{path.relative_to(ROOT)} no longer re-derives — run "
                        "tools/seat_platted_ground_1835.py --build")
    print(f"OK: {ledger_doc['counts']['lots']} committed lots and "
          f"{seats_doc['counts']['seated']} platted seats re-derive, and the "
          f"{seats_doc['counts']['owed']} the plat cannot hold are owed in writing")
    return 0


def cmd_report() -> int:
    _, ledger_doc, seats_doc, lots, dealt = derive()
    print("\n\033[1m== the lot ledger\033[0m")
    for key, value in ledger_doc["counts"].items():
        print(f"   {key:<34} {value}")
    print(f"   {'density on the principal streets':<34} "
          f"{ledger_doc['the_density_standard']['multi_building_lot_rate_on_the_principal_streets']['carrying_more_than_one_principal_roof']}"
          f" of {ledger_doc['the_density_standard']['multi_building_lot_rate_on_the_principal_streets']['principal_street_lots']}")
    print("\n\033[1m== the deal\033[0m")
    for key, value in seats_doc["counts"].items():
        print(f"   {key:<34} {value}")
    print("\n\033[1m== the seats, by block\033[0m")
    from collections import Counter
    for block_id, count in sorted(Counter(s["block_id"] for s in dealt["seats"]).items()):
        print(f"   {block_id:<34} {count}")
    print("\n\033[1m== held back\033[0m")
    for row in dealt["held_back"][:8]:
        print(f"   {row['structure_id']:<40} {row['family']}  {row['occupants'][:44]}")
    if len(dealt["held_back"]) > 8:
        print(f"   … and {len(dealt['held_back']) - 8} more")
    return 0


def _fires(what: str, thunk, expect: str | None = None) -> None:
    """Fire a guard on a bent copy of the real deal, and refuse a pass for the wrong reason.

    `expect` is a phrase the refusal has to say. A fixture that trips SOME other
    assertion looks green and proves nothing, so a guard worth a self-test names itself.
    """
    try:
        thunk()
    except Fault as fault:
        if expect is not None and expect not in str(fault):
            raise Fault(f"the guard against {what} fired on the wrong rule: {fault}")
        return
    raise Fault(f"the guard against {what} did not fire")


def cmd_self_test() -> int:
    data, _, _, lots, dealt = derive()
    print("\n\033[1m== the guards, fired on the real data\033[0m")

    def seated_on_a_lot_that_is_not_drawn():
        bent = json.loads(json.dumps(dealt))
        bent["seats"][0]["lot_id"] = "blk_nowhere#99"
        assert_the_deal_is_honest(data, lots, bent)
    _fires("a seat on a lot the ledger does not draw", seated_on_a_lot_that_is_not_drawn)
    print("   a seat on a lot the ledger does not draw            refused")

    def two_households_in_one_roof():
        bent = json.loads(json.dumps(dealt))
        adopted = [s for s in bent["seats"] if s["how"] == "adopted"]
        if len(adopted) < 2:
            raise Fault("fixture needs two adoptions")
        adopted[1]["structure_id"] = adopted[0]["structure_id"]
        adopted[1]["lot_id"] = adopted[0]["lot_id"]
        assert_the_deal_is_honest(data, lots, bent)
    _fires("one roof adopted twice", two_households_in_one_roof)
    print("   one standing roof adopted by two households         refused")

    def a_household_of_another_division():
        bent = json.loads(json.dumps(dealt))
        seat = bent["seats"][0]
        seat["district"] = "north" if seat["district"] != "north" else "south"
        assert_the_deal_is_honest(data, lots, bent)
    _fires("a household seated across a division line", a_household_of_another_division)
    print("   a household seated in another division              refused")

    def a_block_dealt_out_of_its_open_lot():
        # The fixture is built from the LEDGER rather than from a slot the deal happens
        # to hold, because the deal holds none the moment the recipes catch up — which is
        # exactly when a guard against spending the reserve stops being testable and
        # starts being load-bearing. So: an open block whose free lots are already at the
        # schedule's ceiling, and one synthetic slot on the lot it keeps open.
        target = None
        for block_id in sorted({lot["block_id"] for lot in lots
                                if lot["block_state"] == "open"}):
            free = [lot for lot in lots if lot["block_id"] == block_id
                    and not lot["bars_another_roof"]]
            row = data["schedule"].get(block_id) or {}
            ceiling = row.get("lot_ceiling_principal")
            if ceiling is None:
                continue
            occupied = [lot for lot in free if lot["principal_roofs_standing"] > 0]
            vacant = [lot for lot in free if lot["principal_roofs_standing"] == 0]
            if len(occupied) >= int(ceiling) and vacant:
                target = min(vacant, key=lambda l: l["lot_id"])
                break
        if target is None:
            raise Fault("fixture needs an open block already at its lot ceiling")
        template = next((s for s in dealt["seats"]
                         if s["district"] == target["district"]), None)
        if template is None:
            raise Fault(f"fixture needs a seat of the {target['district']} division")
        bent = json.loads(json.dumps(dealt))
        slot = json.loads(json.dumps(template))
        slot.update({
            "id": f"{template['id']}__fixture", "how": "slot", "structure_id": None,
            "lot_id": target["lot_id"], "block_id": target["block_id"],
            "lot_index": target["lot_index"], "fronts": target["fronts"],
            "street_class": target["street_class"], "corner": target["corner"],
            "multi_building_rule": target["multi_building_rule"],
            "order_book_draw": {"block_id": target["block_id"],
                                "family": template["family"],
                                "district": target["district"]},
        })
        bent["seats"].append(slot)
        assert_the_deal_is_honest(data, lots, bent)
    _fires("a block dealt out of its open lot", a_block_dealt_out_of_its_open_lot,
           expect="the block keeps one lot open")
    print("   a slot on the last open lot of an open block         refused")

    def an_adoption_that_also_spends_the_order_book():
        bent = json.loads(json.dumps(dealt))
        for seat in bent["seats"]:
            if seat["how"] == "adopted":
                seat["order_book_draw"] = {"block_id": seat["block_id"],
                                           "family": seat["family"],
                                           "district": seat["district"]}
                break
        assert_the_deal_is_honest(data, lots, bent)
    _fires("a standing roof spending the order book",
           an_adoption_that_also_spends_the_order_book)
    print("   an adopted roof drawn off the order book too        refused")

    def a_row_dropped():
        bent = json.loads(json.dumps(dealt))
        bent["seats"].pop()
        assert_the_deal_is_honest(data, lots, bent)
    _fires("a banded row answered by neither a seat nor a reason", a_row_dropped)
    print("   a row in scope left unanswered                      refused")

    def a_blank_reason():
        bent = json.loads(json.dumps(dealt))
        if not bent["owed"]:
            raise Fault("fixture needs an owed row")
        bent["owed"][0]["why"] = ""
        assert_the_deal_is_honest(data, lots, bent)
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
