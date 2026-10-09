#!/usr/bin/env python3
"""HOUSE THE PRESENT: every household present on 1 July 1835 under a roof that stands.

T-1971, piece 1 of 2 of T-1965 (itself piece 2 of 7 of T-1215, the closeout of the whole
reconstruction). The owner's stop condition is *"every person in Chicago has a place to
live"*, and on the day this was written the town's own join said otherwise: of the
households the residents layer holds PRESENT on the scene date, 1,003 reached no roof, no
vessel and no camp — neither through their own `lives_at` nor through a sidecar seating
them. Meanwhile 223 dwellings of the reconstruction's own programme stood with nobody in
them at all. The people and the roofs were both committed; the join between them was not.

    tools/house_the_present_1835.py              write data/reconstruction/1835_housing_seats.json
    tools/house_the_present_1835.py --check      re-derive it and refuse drift, a seat on a roof
                                                 the scene does not stand, a household seated
                                                 twice, a present household left unhoused, a
                                                 ruled-in one neither seated nor counted apart,
                                                 a line stopped while the census had room, or a
                                                 town above the census's people per dwelling
    tools/house_the_present_1835.py --report     the deal by rung, division and roof family
    tools/house_the_present_1835.py --self-test  break each guard in memory and prove it fires

## WHAT THIS WRITES, AND WHAT IT DOES NOT

One ledger, one seat per household. `tools/compile_scene.py` (`overlay_housing`) puts each
seat on the building card of the roof it names, beside the people `compile_residents` and
`overlay_lodgers` already put there, which is how the lodgers' seats already travel. **No
card is touched**: every folder of `data/residents/` is re-derived whole by its own stage
and two of those stages refuse a roof outright, so a `lives_at` written here would be
overwritten on the next rebuild — the seat lives beside the card, as T-1406's do. No roof
is raised and no record is edited; nobody is minted, and nobody is moved out of the
division their own card or the address book puts them in.

## THE DEAL, IN THE ORDER IT IS TAKEN

  1. **Dealt.** A household the platted or off-plat seating (T-1613, T-1614) already put
     under a standing roof — the address book's `dealt_roof` — takes that roof. That deal
     was argued once and is not re-argued here; this pass only joins it.
  2. **Families** (two or more people on the card), largest first, take a dwelling of the
     family their placement-policy clause admits (`applies_to`), in their own division. A
     household the address book never banded (the reconstructed trades, the readmitted
     and the underdocumented, who stand beside `households/`) takes any dwelling of its
     division — the band it would need is one nobody dealt, and this pass does not invent
     one. Where no roof of the clause stands in the division, the division's dwellings.
  3. **Single people** take a free ordinary-night bed in a lodging house of their division
     first (the lodging model's own count, never its crowded one), and board in the
     division's dwellings when the beds are gone.

Between the first rung and the second, since T-2236, **keepers** take a store (below).

**A workplace is not a bed** (T-2249). A household the building cards list on a roof only
because its card WORKS there ("worked here") is not under a roof by that row. Until T-2249
it was counted as already housed, so 31 households the town holds present (22 on their
own cards, 9 ruled in), among them the Harmon brothers, John Calhoun, George W. Dole
and Archibald Clybourne, slept under no roof in the scene and the audit counted them as
housed. They now take the rungs like every other household.

Among the roofs a household may take, it takes the one that leaves the fewest people per
square metre of floor (footprint × storeys), ties broken by a seeded hash. That is the whole
of the placement: **the room is where the people go.** A household whose division is
`unplaced` is offered the whole town and lands where the room is.

## WHICH ROOFS, AND THE REFUSALS

A standing roof of the reconstruction layer whose family is a dwelling (D1–D7, H1–H3,
T1–T3). Refused, on T-1613's own rules:

  * every DOCUMENTED building — a policy deal that put an invented boarder under a
    researched house would read back as a fact about that house;
  * a roof whose sidecar already STATES its occupants ("Anonymous stock; no occupant is
    claimed", a named practice, a named shop) — a deal does not overturn a committed claim;
  * stores, workshops, warehouses, outbuildings and civic works (C, W, F, A, I, M).

## THE CEILING

The census of November 1835 counted 3,265 people in 398 dwellings — 8.204 a roof
(`data/reconstruction/1835_town_model.json`). `--check` refuses a deal whose present,
housed people per inhabited roof exceeds that, so the town this draws is never more crowded
than the town the enumerator walked four months later. The most crowded roof is printed
beside it, not hidden in the mean.

## THE RULED IN, AND THE LINE THE CEILING DRAWS (T-1972)

Piece 2 of T-1965. The cards of 885 more unhoused households still read `uncertain`, but
T-1386's presence rulings (`data/reconstruction/1835_presence_rulings.json`) put them in
the town by the project's standing rule: an attested or inferred resident is present
unless evidence says otherwise. So they are owed a roof too, and they are seated AFTER the
present-on-the-card cohort, by the same three rungs, so not one of T-1971's seats moves.

They cannot all be seated. The scene stands 294 dwellings against the roof programme's 377,
and the whole cohort under the roofs that stand would be ~10 people a dwelling against the
census's 8.204. The ceiling is not weakened to let them in. Instead the cohort queues, by
the ruling's strength (a reading on the day, a span, a bracket, then the carried, the
nearest last reading first), and takes roofs until the next household would push the town
over the census. The line stops there: everyone behind it is written to `counted_apart` as
`waiting_on_a_roof`, with their place in the queue. Those roofs are the remaining dwelling
builds' (T-1755, T-1759, T-1829, T-1957), and each one they raise lengthens the line on the
next build with no edit here.

The households the town holds OUT of the day — a card ruled `absent` (a death, the
persistence draw T-1172 made for the underdocumented and readmitted), or one of the
rulings' two evidenced absences — are written to `counted_apart` as
`absent_on_the_scene_date`, with the first sentence of their own evidence. They are owed
no roof in July 1835, and saying so is how the audit's unhoused count reaches zero without
pretending they were housed.

## THE KEEPERS, OVER THEIR OWN STORES (T-2236)

The order book (T-2194's ruling) orders one household for each civil store roof the town
stands, the keeper's, and 38 of those roofs stood with no household in them while the
keepers of the town's own stores boarded in other people's dwellings. A store residence is
not a new store. The State census of December 1835 printed 44 stores and the town already
holds 65 (T-1996), so a store kept by somebody the town did not already hold as a keeper
would be one store too many. Only the keepers of a HOUSE OF TRADE THE TOWN ALREADY HOLDS
(`data/businesses/index.json`, present on the scene date, the person its proprietor or a
partner) are offered a store roof. Taken right after `dealt`, own roof first:

  * a keeper whose house of trade stands on a store roof (C1-C4) nobody sleeps in takes
    THAT roof: the register's own premises, or the roof the street-face adoption gave the
    firm (`street_face_adoptions.json`, T-0354, L212). The roof is already the firm's; this
    only puts its keeper's household over it;
  * a keeper whose house of trade stands on NO roof, and whose trade the premises rulings
    put on a street of stores ("a counter open to the street", "a shop front on a street of
    stores", less the trades a workshop family's own label names,
    `seat_trade_roofs_1835.MATCH`), takes an empty store roof of their own division: generated (never a
    documented building), with no household, no worker and no house of trade on it, whose
    sidecar states no occupant beyond T-0516's anonymous stock. Where the roof's own record
    names the trade it was raised for (a bakery, a grocery), only a keeper of that trade.

The division takes keepers only while the book still orders a store household there: its
standing store roofs less the store households the index already knows. Everyone else goes
on to the rungs below. Nobody is minted, no house of trade is raised or moved, and no card is
touched: what is invented is which store roof the keeper's house stands in, which is L354's
liberty, the same as every other seat here.

The invention is docs/LIBERTIES.md **L354**.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
YEAR = "1835"
OUT = DATA / "reconstruction" / "1835_housing_seats.json"
TICKET = "T-1971"
RULED_TICKET = "T-1972"
KEEPER_TICKET = "T-2236"
ELSEWHERE_TICKET = "T-2244"
LIBERTY = "L354"
RULINGS = DATA / "reconstruction" / "1835_presence_rulings.json"

# The presence rulings' legs, strongest first (tools/rule_presence_1835.py). The ruled-in
# cohort takes its roofs in this order, so where the census's ceiling stops the line it is
# the households the town is least sure of that wait.
LEG_ORDER = ("on_the_day", "spans", "bracketed", "carried")

sys.path.insert(0, str(ROOT / "tools"))
from compile_scene import compile_residents  # noqa: E402
from seat_trade_roofs_1835 import MATCH as TRADE_ROOF_MATCH  # noqa: E402

# The residents layer's folders of people OF the town; `transients` kept no residence by
# construction (T-1353) and `merged` cards were folded into another.
RESIDENT_FOLDERS = ("households", "reconstructed_trades", "lodgers", "underdocumented",
                    "readmitted", "institutional")
DIVISIONS = ("north", "south", "west")

DWELLING_FAMILIES = {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "H1", "H2", "H3", "T1", "T2", "T3"}
LODGING_FAMILIES = {"H3", "T1", "T2", "T3"}
# T-2236. The civil store families (the crosswalk's C1-C4: small shop, store-residence,
# narrow and wide two-storey store) and the two lines of the premises rulings that put a
# trade on a street of stores. T-0516's words for a roof that is anonymous stock.
STORE_FAMILIES = {"C1", "C2", "C3", "C4"}
STREET_OF_STORES = ("a counter open to the street", "a shop front on a street of stores")
ANONYMOUS_STOCK = "Anonymous stock; no occupant is claimed"
WORKSHOP_TRADES = {o for family, rule in TRADE_ROOF_MATCH.items() if family.startswith("W")
                   for o in rule.get("occupations", ())}
ORDER_BOOK = DATA / "reconstruction" / "1835_reconstruction_order_book.json"
STREET_FACES = DATA / "research" / "newspapers" / "street_face_adoptions.json"
KEEPER_ROLES = {"proprietor", "partner"}
# A documented building counts as a DWELLING for the census's ratio by its own function.
# It is never offered to the deal (a researched house is not re-tenanted by a policy), but
# the enumerator counted it, so the ceiling does too.
DOCUMENTED_DWELLINGS = {
    "agency_house_residence", "boarding_house", "commanding_officers_quarters", "dwelling",
    "dwelling_and_store", "dwelling_and_trading_house", "dwelling_farmstead",
    "dwelling_former_school_use_unattested", "dwelling_to_let", "enlisted_mens_barracks",
    "hotel", "log_cabin_former_store_and_school_use_unattested",
    "log_house_former_school_use_unattested", "office_and_lodging", "officers_quarters",
    "residence", "store_and_dwelling", "store_residence", "tavern_inn",
}

# The census of November 1835 (town model, `people_per_dwelling_november_1835`).
CENSUS_PEOPLE_PER_DWELLING = 8.204

# The relation compile_scene writes for a household whose card only WORKS at the roof.
WORKED_HERE = "worked here"
RELATION = {
    "dealt": "lived here",
    "family": "shared this roof",
    "boarder": "boarded here",
    "lodger": "lodged here",
    "keeper": "kept the store and lived here",
}
# T-2244. Where a keeper the scene places on another roof is, in the words the store's card
# gives it. A keeper the town places at work on another roof is not listed on the store.
ELSEWHERE = {
    "lived here": "in a house of their own",
    "shared this roof": "in a house they shared",
    "boarded here": "boarding in another household",
    "lodged here": "lodging in a boarding house",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_of(field):
    return field.get("value") if isinstance(field, dict) else field


def floor_area(polygon, stories) -> float:
    pts = polygon or []
    twice = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return round(abs(twice) / 2 * max(1.0, float(stories or 1)), 2)


def seed(*parts) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def read_inputs() -> dict:
    index = load(DATA / "sidecars" / YEAR / "index.json")
    roofs, standing = {}, set()
    for row in index["structures"]:
        standing.add(row["id"])
        record_path = DATA / "structures" / f"{row['id']}.json"
        record = load(record_path) if record_path.exists() else {}
        recon = record.get("reconstruction") or {}
        sidecar = load(DATA / row["sidecar"])
        attributes = sidecar.get("attributes") or {}
        roofs[row["id"]] = {
            "family": recon.get("family"),
            "district": recon.get("district"),
            "trade": recon.get("occupation"),
            "documented": not recon,
            "occupants": value_of(attributes.get("occupants")),
            "area": floor_area((sidecar.get("footprint") or {}).get("polygon"),
                               value_of(attributes.get("stories"))),
            "beds": (recon.get("capacity") or {}).get("beds_ordinary"),
            "function": value_of(record.get("function")),
            "assigned_to": (record.get("resident_assignment") or {}).get("household_id"),
        }

    cards = {}
    for folder in RESIDENT_FOLDERS:
        for path in sorted((DATA / "residents" / folder).glob("*.json")):
            card = load(path)
            if isinstance(card, dict) and card.get("id"):
                cards[card["id"]] = {"file": f"{folder}/{path.name}", "card": card}

    book = {r["id"]: r for r in load(DATA / "reconstruction" / "1835_address_book.json")["rows"]}
    policy = load(DATA / "reconstruction" / "1835_placement_policy.json")
    clauses = {c["id"]: set(c.get("applies_to") or []) for c in policy["clauses"]}
    boats = load(DATA / "boats" / "index.json").get("boats") or []

    # Who is ALREADY under a roof, read the way the building card is built — without
    # this pass's own overlay, so the ledger never reads itself. T-2249: a row that only
    # WORKED there is not a bed. Until then it counted, and 31 households the town holds
    # present (a merchant at his store, a clerk at the agency) slept under no roof at all.
    seated, at_work = set(), set()
    for rows in compile_residents(housing=False).values():
        for h in rows:
            (at_work if h.get("relation") == WORKED_HERE else seated).add(h["household"])

    # T-1386's rulings: the `uncertain` households the town's own rule puts in the
    # population, and the two absences it found evidence for. They stand BESIDE the cards
    # (which keep their `uncertain`), so this pass reads them where they are.
    rulings = load(RULINGS)
    ruled = {r["household_id"]: r["leg"] for r in rulings["rulings"]
             if value_of(r.get("present_on_scene_date")) == "present"}
    evidenced_absent = {r["household_id"]: r.get("note", "")
                        for r in rulings.get("evidenced_absences") or []}

    # T-2236: the keepers (proprietors and partners) of the houses of trade the town holds
    # present on the scene date, by household, with the roof each house stands on: the
    # register's own premises, else the roof the street-face adoption (T-0354, L212) gave
    # the firm. And every roof a house of trade stands on, nobody else's store to move into.
    premises = {r["occupation"]: r for r in
                load(DATA / "businesses" / "rulings" / "premises_rulings.json")["rulings"]}
    adopted = {a["business_id"]: a["structure_id"] for a in
               load(STREET_FACES).get("adoptions") or []}
    household_of = {p["id"]: hid for hid, e in cards.items()
                    for p in e["card"].get("persons") or [] if p.get("id")}
    keepers, business_at = {}, set()
    for b in load(DATA / "businesses" / "index.json")["businesses"]:
        at = (b.get("where") or {}).get("structure_id") or adopted.get(b.get("register_id")) \
            or adopted.get(b["id"])
        business_at.add(at)
        if b.get("present_at_scene_date") is not True:
            continue
        trade = b.get("occupation")
        for person in b.get("people") or []:
            hid = household_of.get(person.get("person_id"))
            if person.get("role") in KEEPER_ROLES and hid:
                keepers.setdefault(hid, []).append({
                    "business": b["id"], "name": b.get("name", ""), "trade": trade,
                    "person": person.get("person_id"),
                    "at": at if at in standing else None,
                    "street_of_stores": trade not in WORKSHOP_TRADES and str(
                        (premises.get(trade) or {}).get("basis", "")).startswith(STREET_OF_STORES)})

    # The store households the book still orders, by division (T-2194's ruling): one a
    # standing store roof, less the store households the index already knows. Neither
    # figure reads a fill, so this deal never reads its own count back.
    order = load(ORDER_BOOK)
    known = {b["key"]: int(b.get("known") or 0) for f in order["bucket_families"]
             if f["key"] == "households" for b in f["buckets"]}
    store_room = {d: max(0, int(r["store_roofs_standing"])
                         - known.get(f"households/store_residence/{d}", 0))
                  for d, r in (order.get("store_residence_ruling") or {})
                  .get("by_division", {}).items()}

    return {"roofs": roofs, "standing": standing, "cards": cards, "book": book,
            "clauses": clauses, "vessels": {b["id"] for b in boats if b.get("id")},
            "seated": seated, "at_work_only": at_work - seated, "ruled": ruled, "evidenced_absent": evidenced_absent,
            "keepers": keepers, "business_at": business_at, "store_room": store_room}


def lag_days(card: dict) -> int:
    """How long before the scene date the corpus last reads this household (T-1144)."""
    presence = card.get("present_on_scene_date")
    last = presence.get("last_dated_appearance") if isinstance(presence, dict) else None
    days = (last or {}).get("days_before_scene_date") if isinstance(last, dict) else None
    return days if isinstance(days, int) and days >= 0 else 10 ** 6


def first_sentence(text: str) -> str:
    text = " ".join((text or "").split())
    cut = text.find(". ")
    return text if cut < 0 else text[:cut + 1]


def division_of(card: dict, row: dict | None) -> str | None:
    if row and (row.get("seat") or {}).get("division") in DIVISIONS:
        return row["seat"]["division"]
    for key in ("division", "division_reconstructed"):
        value = value_of(card.get(key))
        if value in DIVISIONS:
            return value
    return None


def deal(inputs: dict) -> dict:
    roofs, cards, book = inputs["roofs"], inputs["cards"], inputs["book"]
    standing, vessels, seated = inputs["standing"], inputs["vessels"], inputs["seated"]

    pool = {sid: r for sid, r in roofs.items()
            if r["family"] in DWELLING_FAMILIES and not r["documented"]
            and r["occupants"] in (None, "") and r["area"] > 0}

    # People already sleeping under each roof, from every overlay but this one. A row
    # that only WORKED there is somebody else's bed and is not counted.
    people = Counter()
    rows_now = compile_residents(housing=False)
    for sid, rows in rows_now.items():
        people[sid] += sum(len(h.get("persons") or []) for h in rows
                           if h.get("relation") != WORKED_HERE)

    # T-2236: the store roofs a keeper may take. A keeper's own (the register stands their
    # house of trade on it) wants only that nobody sleeps there; any other wants nobody on
    # it at all — no household, no worker, no house of trade — and no stated occupant.
    own_store_ok = {sid for sid, r in roofs.items() if r["family"] in STORE_FAMILIES
                    and not r["documented"] and people[sid] == 0}
    store_pool = {sid: r for sid, r in roofs.items() if sid in own_store_ok and r["area"] > 0
                  and not rows_now.get(sid) and sid not in inputs["business_at"]
                  and r["occupants"] in (None, "", ANONYMOUS_STOCK)}
    keepers, store_room = inputs["keepers"], inputs["store_room"]
    stores_taken, kept = set(), Counter()
    lodging_beds = {sid: max(0, (r["beds"] or 0) - people[sid]) for sid, r in pool.items()
                    if r["family"] in LODGING_FAMILIES and r["beds"]}

    owed, already = [], 0
    ruled_owed, ruled_already, absent = [], 0, []
    for hid, entry in sorted(cards.items()):
        card = entry["card"]
        on_card = value_of(card.get("present_on_scene_date"))
        where = value_of(card.get("lives_at"))
        housed = bool((where and (where in standing or where in vessels)) or hid in seated)
        if on_card == "present":
            if housed:
                already += 1
            else:
                owed.append(hid)
        elif hid in inputs["ruled"]:
            if housed:
                ruled_already += 1
            else:
                ruled_owed.append(hid)
        elif not housed and (on_card == "absent" or hid in inputs["evidenced_absent"]):
            presence = card.get("present_on_scene_date") or {}
            basis = presence.get("basis") if isinstance(presence.get("basis"), dict) else {}
            absent.append({
                "household": hid, "file": entry["file"],
                "persons": len(card.get("persons") or []),
                "why": "absent_on_the_scene_date",
                "on_the_card": on_card,
                "confidence": presence.get("confidence") if on_card == "absent" else "attested",
                "basis": basis.get("id") or ("evidenced_absence" if on_card != "absent"
                                             else "the_card's_own_reading"),
                "evidence": first_sentence(inputs["evidenced_absent"].get(hid)
                                           or basis.get("note") or presence.get("note") or ""),
            })

    seats, refused = [], []

    def place(hid, sid, rung, words, presence="on_the_card"):
        entry = cards[hid]
        n = len(entry["card"].get("persons") or [])
        people[sid] += n
        seats.append({"household": hid, "file": entry["file"], "place": sid,
                      "rung": rung, "relation": RELATION[rung], "persons": n,
                      "division": roofs[sid]["district"], "family": roofs[sid]["family"],
                      "presence": presence, "words": words})

    def best(hid, candidates):
        return min(candidates, key=lambda sid: (
            round((people[sid] + len(cards[hid]["card"].get("persons") or [])) / pool[sid]["area"], 6),
            seed(hid, sid, TICKET)))

    def size(hid):
        return len(cards[hid]["card"].get("persons") or [])

    def in_division(hid, families_ok):
        division = division_of(cards[hid]["card"], book.get(hid))
        return division, [sid for sid, r in pool.items()
                          if (division is None or r["district"] == division)
                          and r["family"] in families_ok]

    homes = DWELLING_FAMILIES - LODGING_FAMILIES

    def dealt_roof(hid):
        dealt = (book.get(hid) or {}).get("dealt_roof") or {}
        sid = dealt.get("structure_id") if isinstance(dealt, dict) else None
        return (sid, dealt) if sid in pool or (sid in roofs and roofs[sid]["assigned_to"] == hid) \
            else (None, dealt)

    def own_store(hid):
        return next((k for k in keepers.get(hid, ()) if k["at"] in own_store_ok
                     and k["at"] not in stores_taken), None)

    def seat_keepers(cohort, presence):
        """1b. keepers (T-2236) — the keeper of a house of trade the town holds, over a store:
        their own roof first, then an empty one of their division, while the book orders a
        store household there. Returns everyone it did not seat."""
        others = []
        for hid in sorted(cohort, key=lambda h: (own_store(h) is None, seed(h, KEEPER_TICKET))):
            own = own_store(hid)
            division = roofs[own["at"]]["district"] if own else \
                division_of(cards[hid]["card"], book.get(hid))
            if hid not in keepers or division not in DIVISIONS or \
                    kept[division] >= store_room.get(division, 0):
                others.append(hid)
                continue
            if own:
                sid = own["at"]
                how = (f"keeping {own['name']}, over the store roof the business register "
                       "or the street-face adoption stands that house of trade on")
            else:
                if any(k["at"] for k in keepers[hid]):
                    others.append(hid)      # their house of trade stands, and not on a store
                    continue
                trades = {k["trade"] for k in keepers[hid] if k["street_of_stores"]}
                fits = [s for s, r in store_pool.items() if trades and s not in stores_taken
                        and r["district"] == division and (not r["trade"] or r["trade"] in trades)]
                if not fits:
                    others.append(hid)
                    continue
                sid = min(fits, key=lambda s: seed(hid, s, KEEPER_TICKET))
                k = next(k for k in keepers[hid] if k["trade"] in trades and (
                    not roofs[sid]["trade"] or k["trade"] == roofs[sid]["trade"]))
                how = (f"keeping {k['name']}, a house of trade the town holds and stands on no "
                       f"roof, over an empty store roof of the {division} division")
            stores_taken.add(sid)
            kept[division] += 1
            place(hid, sid, "keeper", how, presence)
        return others

    def seat_cohort(cohort, presence):
        # 1. dealt — the platted and off-plat seating already chose the roof.
        rest = []
        for hid in cohort:
            sid, dealt = dealt_roof(hid)
            if sid:
                place(hid, sid, "dealt", f"the roof {dealt.get('dealt_by') or 'the seating'} dealt "
                                         "this household, joined here and not re-argued", presence)
            else:
                rest.append(hid)
        rest = seat_keepers(rest, presence)

        families = sorted((h for h in rest if size(h) >= 2), key=lambda h: (-size(h), seed(h, TICKET)))
        singles = sorted((h for h in rest if size(h) < 2), key=lambda h: seed(h, TICKET))

        # 2. families, by their clause's own families, else the division's dwellings.
        for hid in families:
            row = book.get(hid)
            clause = ((row or {}).get("seat") or {}).get("clause")
            admitted = inputs["clauses"].get(clause, set()) & homes
            division, roofs_ok = in_division(hid, admitted) if admitted else (None, [])
            how = f"a {'/'.join(sorted(admitted))} dwelling, as the {clause} clause admits"
            if not roofs_ok:
                division, roofs_ok = in_division(hid, homes)
                how = "a dwelling of its division" if division else "the town's least crowded dwelling"
            if not roofs_ok:
                refused.append({"household": hid, "why": "no dwelling of its division stands"})
                continue
            place(hid, best(hid, roofs_ok), "family", how, presence)

        # 3. single people: a free ordinary bed in their division, then boarding.
        for hid in singles:
            division = division_of(cards[hid]["card"], book.get(hid))
            beds = [sid for sid, free in lodging_beds.items()
                    if free > 0 and (division is None or pool[sid]["district"] == division)]
            if beds:
                sid = min(beds, key=lambda s: (-lodging_beds[s], seed(hid, s, TICKET)))
                lodging_beds[sid] -= 1
                place(hid, sid, "lodger", "a free ordinary-night bed of the lodging model", presence)
                continue
            division, roofs_ok = in_division(hid, homes)
            if not roofs_ok:
                refused.append({"household": hid, "why": "no dwelling of its division stands"})
                continue
            place(hid, best(hid, roofs_ok),
                  "boarder", "boarding in the division's least crowded dwelling" if division
                  else "boarding in the town's least crowded dwelling", presence)

    def standing_dwellings():
        inhabited = {sid for sid, n in people.items() if n > 0}
        return {sid for sid, r in roofs.items()
                if (r["family"] in DWELLING_FAMILIES and not r["documented"])
                or (r["documented"] and r["function"] in DOCUMENTED_DWELLINGS)} | inhabited

    # THE PRESENT ON THEIR CARDS (T-1971): every one is owed a roof and every one gets one.
    seat_cohort(owed, "on_the_card")

    # THE RULED IN (T-1972): the households T-1386's rule puts in the town that their cards
    # still leave `uncertain`. They queue by the strength of the ruling — a reading on the
    # day, a span, a bracket, then the carried, nearest last reading first — and take roofs
    # while the town stays within the census's people per dwelling. The line stops at the
    # first household the ceiling cannot take; everyone behind it waits for the roofs the
    # programme orders and the scene does not yet stand, and is counted apart saying so.
    # A ruled-in KEEPER takes their store before the line is drawn: the store is a dwelling
    # the enumerator would have counted, so a keeper brings their own roof with them and
    # never takes one a stronger ruling waits for (T-2236).
    undealt = [h for h in ruled_owed if not dealt_roof(h)[0]]
    ruled_keepers = set(undealt) - set(seat_keepers(undealt, "ruled_in"))
    ruled_owed = [h for h in ruled_owed if h not in ruled_keepers]
    leg_rank = {leg: i for i, leg in enumerate(LEG_ORDER)}
    ruled_owed.sort(key=lambda h: (leg_rank.get(inputs["ruled"][h], len(LEG_ORDER)),
                                   lag_days(cards[h]["card"]), seed(h, RULED_TICKET)))
    room = math.floor(CENSUS_PEOPLE_PER_DWELLING * len(standing_dwellings()) + 1e-9) \
        - sum(n for n in people.values() if n > 0)
    admitted, waiting = [], []
    for hid in ruled_owed:
        if waiting or size(hid) > room:
            waiting.append(hid)
            continue
        room -= size(hid)
        admitted.append(hid)
    seat_cohort(admitted, "ruled_in")
    # T-2244. A store roof nobody sleeps in, standing a house of trade whose keeper the
    # town already places on another roof — sleeping there by their own card, the dealt
    # roof or a lodging bed, or at work there by their own card — is a store with nobody
    # living over it: the keeper's household is not moved, and the book's order for a
    # household over that store is discharged. A keeper who slept elsewhere and works
    # nowhere else is listed on the store's own card; one whose card puts their work on
    # another roof is not, because the card has already said where they kept the trade.
    placed_at = {}
    for sid, rows in sorted(rows_now.items()):
        for h in rows:
            placed_at.setdefault(h.get("household"), []).append((sid, h.get("relation")))
    for s in seats:
        placed_at.setdefault(s["household"], []).append((s["place"], s["relation"]))
    kept_elsewhere = []
    for sid in sorted(sid for sid in own_store_ok if people[sid] == 0 and not rows_now.get(sid)
                      and sid not in stores_taken):
        mine = sorted((hid, k) for hid, ks in keepers.items() for k in ks if k["at"] == sid)
        away = [(hid, k, [(at, rel) for at, rel in placed_at.get(hid, ()) if at != sid])
                for hid, k in mine]
        away = [(hid, k, where) for hid, k, where in away if where]
        if not away:
            continue
        hid, k, where = away[0]
        works = [at for at, rel in where if rel in ("worked here", "lived and worked here")]
        sleeps = [(at, rel) for at, rel in where if rel in ELSEWHERE]
        listed = bool(sleeps) and not works and bool(k["person"])
        kept_elsewhere.append({
            "structure_id": sid, "division": roofs[sid]["district"],
            "business": k["business"], "name": k["name"], "household": hid,
            "file": cards[hid]["file"], "person_id": k["person"],
            "keeper_placed_at": (works or [at for at, _ in sleeps] or [where[0][0]])[0],
            "keeper_placed_as": "at work" if works else (sleeps[0][1] if sleeps else where[0][1]),
            "listed_on_the_store_card": listed,
            "relation": "worked here",
            "words": (f"kept {k['name']}'s business here and slept elsewhere in the town, "
                      f"{ELSEWHERE[sleeps[0][1]]}; nobody lived over this store") if listed else
                     (f"the keeper of {k['name']} is placed on another roof, so nobody lived "
                      "over this store"),
        })
    elsewhere_by = Counter(r["division"] for r in kept_elsewhere)

    counted_apart = sorted(absent + [{
        "household": hid, "file": cards[hid]["file"], "persons": size(hid),
        "why": "waiting_on_a_roof", "leg": inputs["ruled"][hid],
        "queue_position": len(admitted) + i + 1,
    } for i, hid in enumerate(waiting)], key=lambda r: r["household"])

    seats.sort(key=lambda s: s["household"])
    inhabited = {sid for sid, n in people.items() if n > 0}
    present_housed = sum(people[sid] for sid in inhabited)
    dwellings = standing_dwellings()
    by_presence = Counter(s["presence"] for s in seats)
    crowd = sorted(((people[sid], sid) for sid in pool), reverse=True)
    density = sorted(((round(people[sid] / pool[sid]["area"], 4), sid) for sid in pool),
                     reverse=True)
    return {
        "$schema_note": "DERIVED — regenerate with tools/house_the_present_1835.py; "
                        "tools/check.sh re-derives it. Do not hand-edit.",
        "id": "chicago_july_1835_housing_seats",
        "ticket": TICKET,
        "tickets": [TICKET, RULED_TICKET, KEEPER_TICKET],
        "parent_ticket": "T-1965",
        "target_date": "1835-07-01",
        "generated_by": "tools/house_the_present_1835.py",
        "liberty": LIBERTY,
        "not_a_reading": "no page of any source is read here. Every seat is an adjudication over "
                         "committed records — which standing dwelling a present household with no "
                         "roof shares — and the roof over each of them is the invention. The "
                         "household is the residents layer's and is not touched.",
        "raises_no_roof": "every seat is a household put under a roof that already stands. No "
                          "record is written, no slot is requested and nothing is baked.",
        "inputs": [
            "data/residents/{" + ",".join(RESIDENT_FOLDERS) + "}/*.json",
            "data/businesses/index.json", "data/businesses/rulings/premises_rulings.json",
            "data/reconstruction/1835_reconstruction_order_book.json (store_residence_ruling, "
            "known)",
            "data/reconstruction/1835_presence_rulings.json",
            "data/reconstruction/1835_address_book.json",
            "data/reconstruction/1835_placement_policy.json",
            "data/reconstruction/1835_lodgers_seated.json (through compile_scene)",
            "data/sidecars/1835/index.json", "data/sidecars/1835/*.json",
            "data/structures/*.json", "data/boats/index.json",
        ],
        "counts": {
            "present_households_already_housed": already,
            "present_households_owed_a_roof": len(owed),
            "ruled_in_households_already_housed": ruled_already,
            "ruled_in_households_owed_a_roof": len(ruled_owed),
            "of_them_only_at_work_on_a_roof": sum(h in inputs["at_work_only"]
                                                  for h in owed + ruled_owed),
            "seated": len(seats),
            "seated_by_presence": dict(sorted(by_presence.items())),
            "refused": len(refused),
            "persons_seated": sum(s["persons"] for s in seats),
            "counted_apart": dict(sorted(Counter(r["why"] for r in counted_apart).items())),
            "persons_counted_apart": dict(sorted(Counter(
                r["why"] for r in counted_apart for _ in range(r["persons"])).items())),
            "by_rung": dict(sorted(Counter(s["rung"] for s in seats).items())),
            "by_division": dict(sorted(Counter(s["division"] for s in seats).items())),
            "by_family": dict(sorted(Counter(s["family"] for s in seats).items())),
            "roofs_in_the_pool": len(pool),
            "roofs_the_deal_used": len({s["place"] for s in seats}),
            "of_them_assigned_to_their_own_household": len(
                {s["place"] for s in seats if s["place"] not in pool}),
        },
        "the_ceiling": {
            "census_people_per_dwelling": CENSUS_PEOPLE_PER_DWELLING,
            "source": "data/reconstruction/1835_town_model.json people_per_dwelling_november_1835 "
                      "(3,265 people in 398 dwellings)",
            "the_ratio_is": "people under a roof / standing dwellings — the enumerator's own "
                            "division, every dwelling counted whether this layer links "
                            "anybody to it or not",
            "standing_dwellings": len(dwellings),
            "people_under_a_roof": present_housed,
            "people_per_dwelling": round(present_housed / len(dwellings), 3) if dwellings else 0,
            "inhabited_roofs": len(inhabited),
            "people_per_inhabited_roof": round(present_housed / len(inhabited), 3) if inhabited else 0,
            "why_the_two_differ": "documented dwellings no card links and roofs whose record "
                                  "already states its occupants stand in the first count and "
                                  "are refused by this deal; who sleeps in them is T-1966's "
                                  "and T-1615's to settle, not a policy deal's",
            "most_crowded_roof": {"structure_id": crowd[0][1], "people": crowd[0][0],
                                  "floor_m2": pool[crowd[0][1]]["area"]} if crowd else None,
            "densest_roof": {"structure_id": density[0][1], "people_per_m2": density[0][0]}
            if density else None,
        },
        "the_keepers": {
            "ticket": KEEPER_TICKET,
            "who": "the proprietor's household of a house of trade the town holds present on "
                   "the scene date (data/businesses/index.json) whose trade the premises rulings "
                   "put on a street of stores, less the trades a workshop family's label names",
            "where": "the store roof the register stands that house on, else an empty "
                     "generated store roof (C1-C4) of the keeper's division that no household, "
                     "worker or house of trade is on and whose sidecar states no occupant "
                     "beyond anonymous stock; a roof raised for one trade takes only its keeper",
            "not_a_new_store": "every keeper's house of trade is already in the register, so "
                               "the town's store count (T-1996: 65 held against 44 printed) "
                               "does not move",
            "room_by_division": dict(sorted(store_room.items())),
            "kept_by_division": {d: kept[d] for d in sorted(store_room)},
            "keepers_held": len(keepers),
            "store_roofs_offered": len(store_pool),
            "kept_from_elsewhere": {
                "ticket": ELSEWHERE_TICKET,
                "rule": "a generated store roof nobody sleeps or works in, standing a house of "
                        "trade whose keeper (proprietor or partner) the town already places "
                        "on another roof, is a store with nobody living over it: the keeper is "
                        "not moved, and the book's order for a household over it is "
                        "discharged (build_order_book_1835.py, store_residence_ruling)",
                "on_the_card": "a keeper who slept elsewhere and whose card puts their work "
                               "nowhere else is listed on the store's card as having worked "
                               "there; the rest of the household is not",
                "by_division": {d: elsewhere_by[d] for d in sorted(store_room)},
                "stores": kept_elsewhere,
            },
        },
        "the_ruled_in": {
            "ticket": RULED_TICKET,
            "who": "households whose cards still read `uncertain` and whom T-1386's rule puts in "
                   "the town (data/reconstruction/1835_presence_rulings.json): an attested or "
                   "inferred resident is present unless evidence says otherwise",
            "order": "the ruling's leg, strongest first (" + ", ".join(LEG_ORDER) + "), then the "
                     "nearest last dated reading, then a seeded hash",
            "the_line_stops": "at the first household the census's people per dwelling cannot "
                              "take; nobody behind it is seated, so a weaker ruling never takes "
                              "a roof a stronger one waits for",
            "admitted": len(admitted),
            "kept_a_store_before_the_line": len(ruled_keepers),
            "waiting": len(waiting),
            "admitted_by_leg": dict(sorted(Counter(inputs["ruled"][h] for h in admitted).items())),
            "waiting_by_leg": dict(sorted(Counter(inputs["ruled"][h] for h in waiting).items())),
        },
        "counted_apart_reasons": {
            "absent_on_the_scene_date": "the card, or the presence rulings' evidenced absences, "
                                        "put this household out of the town on 1 July 1835 (a "
                                        "death, a dated departure, or the persistence draw "
                                        "T-1172 ruled on): it is owed no roof in this scene",
            "waiting_on_a_roof": "ruled present, and owed a roof the scene does not stand yet. "
                                 "The roof programme orders 377 dwelling roofs on the scene date "
                                 "(1835_roof_programme_rederivation.json) and the scene stands "
                                 "fewer; seating these under the roofs that do stand would put "
                                 "the town above the census's 8.204 people per dwelling. The "
                                 "roofs are the remaining dwelling builds (T-1755, T-1759, "
                                 "T-1829, T-1957); every roof they raise lengthens this deal's "
                                 "line on the next build, with no edit here",
        },
        "seats": seats,
        "refused": refused,
        "counted_apart": counted_apart,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def problems(doc: dict, inputs: dict) -> list[str]:
    out = []
    pool_ok = {sid for sid, r in inputs["roofs"].items() if r["family"] in DWELLING_FAMILIES
               and not r["documented"] and r["occupants"] in (None, "")}
    seen = Counter(s["household"] for s in doc["seats"])
    for hid, n in seen.items():
        if n > 1:
            out.append(f"{hid} is seated {n} times")
        if hid in inputs["seated"]:
            out.append(f"{hid} is seated here and also housed by another overlay")
        if hid not in inputs["cards"]:
            out.append(f"{hid} is seated and no card holds it")
    for s in doc["seats"]:
        if s["place"] not in inputs["standing"]:
            out.append(f"{s['household']} is seated at {s['place']}, which the scene does not stand")
        elif s["rung"] == "keeper":
            roof = inputs["roofs"][s["place"]]
            own = {k["at"] for k in inputs["keepers"].get(s["household"], ())}
            if roof["family"] not in STORE_FAMILIES or roof["documented"]:
                out.append(f"{s['household']} keeps {s['place']}, which is not a generated "
                           "store roof")
            elif s["household"] not in inputs["keepers"]:
                out.append(f"{s['household']} keeps {s['place']} and holds no house of trade")
            elif s["place"] not in own and (
                    any(k["at"] for k in inputs["keepers"][s["household"]])
                    or not any(k["street_of_stores"] for k in inputs["keepers"][s["household"]])):
                out.append(f"{s['household']} keeps {s['place']}, though their house of trade "
                           "stands elsewhere or is not kept on a street of stores")
            elif s["place"] not in own and (s["place"] in inputs["business_at"]
                                            or roof["occupants"] not in (None, "", ANONYMOUS_STOCK)):
                out.append(f"{s['household']} keeps {s['place']}, which somebody else's "
                           "house of trade or stated occupant already holds")
        elif s["place"] not in pool_ok and \
                inputs["roofs"][s["place"]]["assigned_to"] != s["household"]:
            out.append(f"{s['household']} is seated at {s['place']}, which this deal refuses")
    if doc["refused"]:
        out.append(f"{len(doc['refused'])} present household(s) left without a roof")
    keeper_seats = [s for s in doc["seats"] if s["rung"] == "keeper"]
    stores = Counter(s["place"] for s in keeper_seats)
    for sid, n in stores.items():
        if n > 1:
            out.append(f"{sid} is kept by {n} households, and a store residence is one")
    for d, n in Counter(s["division"] for s in keeper_seats).items():
        if n > inputs["store_room"].get(d, 0):
            out.append(f"{n} keepers seated in the {d} division, where the book orders "
                       f"{inputs['store_room'].get(d, 0)} store households")
    seat_places = {s["place"] for s in doc["seats"]}
    for r in doc["the_keepers"]["kept_from_elsewhere"]["stores"]:
        roof = inputs["roofs"].get(r["structure_id"]) or {}
        if r["structure_id"] in seat_places:
            out.append(f"{r['structure_id']} is ruled a store nobody lived over, and the deal "
                       "seats a household in it")
        if roof.get("family") not in STORE_FAMILIES or roof.get("documented", True):
            out.append(f"{r['structure_id']} is ruled kept from elsewhere and is not a "
                       "generated store roof")
        if r["keeper_placed_at"] == r["structure_id"] or not any(
                k["at"] == r["structure_id"] for k in inputs["keepers"].get(r["household"], ())):
            out.append(f"{r['structure_id']} is ruled kept from elsewhere, and {r['household']} "
                       "is not a keeper of its house of trade placed on another roof")
    apart = Counter(r["household"] for r in doc["counted_apart"])
    for hid, n in apart.items():
        if n > 1 or hid in seen:
            out.append(f"{hid} is counted apart and also seated, or counted apart twice")
    for r in doc["counted_apart"]:
        if r["why"] == "waiting_on_a_roof" and r["household"] not in inputs["ruled"]:
            out.append(f"{r['household']} waits on a roof and no presence ruling puts it in the town")
    owed = set(inputs["ruled"]) - inputs["seated"] - set(seen) - set(apart)
    for hid in sorted(owed):
        card = (inputs["cards"].get(hid) or {}).get("card") or {}
        where = value_of(card.get("lives_at"))
        if not (where and (where in inputs["standing"] or where in inputs["vessels"])):
            out.append(f"{hid} is ruled present and neither seated nor counted apart")
    # T-2249. A household present on its own card is under a roof by its own lives_at, by
    # another overlay's bed, or by a seat here. A workplace row is none of those.
    refused = {r["household"] for r in doc["refused"]}
    for hid, entry in sorted(inputs["cards"].items()):
        card = entry["card"]
        where = value_of(card.get("lives_at"))
        if value_of(card.get("present_on_scene_date")) != "present" or hid in seen \
                or hid in inputs["seated"] or hid in refused or hid in apart \
                or (where and (where in inputs["standing"] or where in inputs["vessels"])):
            continue
        out.append(f"{hid} is present and sleeps under no roof"
                   + (" — it only works at one" if hid in inputs["at_work_only"] else ""))
    ceiling = doc["the_ceiling"]
    if ceiling["people_per_dwelling"] > CENSUS_PEOPLE_PER_DWELLING:
        out.append(f"{ceiling['people_per_dwelling']} people per standing dwelling is above "
                   f"the census's {CENSUS_PEOPLE_PER_DWELLING}")
    # A household left waiting while the census still had room for it is a line stopped
    # early: the next one in the queue must be the one that did not fit.
    waiting = sorted((r for r in doc["counted_apart"] if r["why"] == "waiting_on_a_roof"),
                     key=lambda r: r["queue_position"])
    if waiting:
        room = math.floor(CENSUS_PEOPLE_PER_DWELLING * ceiling["standing_dwellings"] + 1e-9) \
            - ceiling["people_under_a_roof"]
        if waiting[0]["persons"] <= room:
            out.append(f"{waiting[0]['household']} waits on a roof though the census's ceiling "
                       f"still has room for {room}")
    return out


def report(doc: dict) -> str:
    c, t = doc["counts"], doc["the_ceiling"]
    return "\n".join([
        f"house the present (T-1971, T-1972): {c['seated']} households seated "
        f"{c['seated_by_presence']}, {c['refused']} refused; owed {c['present_households_owed_a_roof']} "
        f"on the card + {c['ruled_in_households_owed_a_roof']} ruled in",
        f"  counted apart {c['counted_apart']} households, {c['persons_counted_apart']} persons",
        f"  by rung      {c['by_rung']}",
        f"  keepers      {doc['the_keepers']['kept_by_division']} over a store, of "
        f"{doc['the_keepers']['room_by_division']} the book orders (T-2236)",
        f"  elsewhere    {doc['the_keepers']['kept_from_elsewhere']['by_division']} stores whose "
        f"keeper is placed on another roof (T-2244)",
        f"  by division  {c['by_division']}",
        f"  by family    {c['by_family']}",
        f"  roofs        {c['roofs_the_deal_used']} used: {c['roofs_in_the_pool']} in the pool, "
        f"{c['of_them_assigned_to_their_own_household']} assigned to their own household",
        f"  ceiling      {t['people_per_dwelling']} people per standing dwelling "
        f"({t['people_under_a_roof']} under {t['standing_dwellings']}) against the census's "
        f"{t['census_people_per_dwelling']}; {t['people_per_inhabited_roof']} per inhabited "
        f"roof ({t['inhabited_roofs']}); most crowded {t['most_crowded_roof']}",
    ])


def self_test(inputs: dict) -> int:
    failures = []
    base = deal(inputs)
    if problems(base, inputs):
        failures.append("the committed deal is not clean to begin with")

    def expect(label, mutate):
        doc = copy.deepcopy(base)
        mutate(doc)
        if not problems(doc, inputs):
            failures.append(label)

    expect("a seat on a roof the scene does not stand",
           lambda d: d["seats"][0].update(place="no_such_structure"))
    expect("a household seated twice", lambda d: d["seats"].append(dict(d["seats"][0])))
    expect("a seat on a documented building", lambda d: d["seats"][0].update(
        place=next(s for s, r in sorted(inputs["roofs"].items()) if r["documented"])))
    expect("a present household left unhoused",
           lambda d: d["refused"].append({"household": "hh_x", "why": "test"}))
    expect("two keepers over one store", lambda d: d["seats"].append(
        {**next(s for s in d["seats"] if s["rung"] == "keeper"), "household": "hh_x"}))
    expect("a keeper over a documented building", lambda d: next(
        s for s in d["seats"] if s["rung"] == "keeper").update(
        place=next(s for s, r in sorted(inputs["roofs"].items()) if r["documented"])))
    expect("a store kept from elsewhere with a household seated in it", lambda d: d[
        "the_keepers"]["kept_from_elsewhere"]["stores"].append(
        {**d["the_keepers"]["kept_from_elsewhere"]["stores"][0],
         "structure_id": d["seats"][0]["place"]}))
    expect("a store kept from elsewhere by its own keeper's bed", lambda d: d[
        "the_keepers"]["kept_from_elsewhere"]["stores"][0].update(
        keeper_placed_at=d["the_keepers"]["kept_from_elsewhere"]["stores"][0]["structure_id"]))
    expect("a town above the census's crowding",
           lambda d: d["the_ceiling"].update(people_per_dwelling=9.0))

    def drop_a_waiter(d):
        row = next(r for r in d["counted_apart"] if r["why"] == "waiting_on_a_roof")
        d["counted_apart"].remove(row)

    def stop_early(d):
        d["the_ceiling"]["people_under_a_roof"] -= 50

    expect("a ruled-in household neither seated nor counted apart", drop_a_waiter)
    expect("a household counted apart and seated", lambda d: d["counted_apart"].append(
        {"household": d["seats"][0]["household"], "why": "absent_on_the_scene_date", "persons": 1}))
    expect("a line stopped while the census still had room", stop_early)

    def housed_at_work(d):
        # T-2249's defect put back: a present household whose only row is its workplace,
        # taken out of the deal as though that row were a bed.
        hid = next(s["household"] for s in d["seats"] if s["household"] in inputs["at_work_only"]
                   and s["presence"] == "on_the_card")
        d["seats"] = [s for s in d["seats"] if s["household"] != hid]

    expect("a present household housed by its workplace alone", housed_at_work)
    if failures:
        print("SELF-TEST FAILED — the guard did not fire on: " + "; ".join(failures))
        return 1
    print("self-test: all thirteen guards fire")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    inputs = read_inputs()
    if args.self_test:
        return self_test(inputs)
    doc = deal(inputs)
    if args.report:
        print(report(doc))
        return 0
    if args.check:
        errors = problems(doc, inputs)
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != render(doc):
            errors.append(f"{OUT.relative_to(ROOT)} is stale — run tools/house_the_present_1835.py")
        print(report(doc))
        if errors:
            print("HOUSING DEAL FAILED\n  - " + "\n  - ".join(errors))
            return 1
        return 0
    errors = problems(doc, inputs)
    OUT.write_text(render(doc), encoding="utf-8")
    print(report(doc))
    print(f"wrote {OUT.relative_to(ROOT)}")
    if errors:
        print("but it is not clean:\n  - " + "\n  - ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
