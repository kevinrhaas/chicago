#!/usr/bin/env python3
"""T-2193, stage `held_head_dwellings` — the family dwellings the town already forms.

    python3 tools/count_held_head_dwellings_1835.py --build      write the ledger, fill the book
    python3 tools/count_held_head_dwellings_1835.py --check      re-derive both, refuse drift
    python3 tools/count_held_head_dwellings_1835.py --report     what was counted, by division
    python3 tools/count_held_head_dwellings_1835.py --self-test  break each rule, require it fires

WHAT THIS IS FOR. Piece 1 of T-2188. The order book still ordered 338 family dwellings
(`households/family_dwelling/<division>`) beside 1,243 present head records it counts as
AWAITING A HOUSEHOLD — a name with no reading about a dwelling (the owner's ruling of
2026-09-21, T-1476). The ticket asked for those houses to be formed around heads the town
already holds rather than around new ones. Most of them already were. Two committed
passes put those very records under a standing dwelling:

  * `dealt` — the platted and off-plat seating (T-1613, T-1614) dealt the household a
    dwelling of its own, which the address book records as its `dealt_roof` and the
    housing seats (T-1971) carry as "lived here";
  * `family` — the housing seats' second rung put a FAMILY (two or more people on the
    card: the head, and the wife and children the modelled-families stage drew) under a
    standing dwelling of its own division, "shared this roof".

Both joins live beside the card, in `data/reconstruction/1835_housing_seats.json`, and the
book counts houses off the card alone (`rebuild_resident_index.dwelling_evidence`). So the
houses stood and the book kept ordering them. This stage counts them.

THE RULE, IN THE ORDER IT IS TAKEN. A record is counted when ALL of these hold:

  1. the book itself counts it as awaiting a household
     (`build_order_book_1835.records_awaiting_a_household`). A record that is already a
     house is never counted again;
  2. the housing seats put it under a standing dwelling (D1-D7, H1, H2) on the `dealt` or
     the `family` rung. A BOARDER is not counted: a man boarding in somebody's house is a
     bed in that household, not a household. Nor is a lodging-house roof (H3, T1-T3);
  3. its division's `family_dwelling` order still has room once every other stage's fill
     is taken off it.

Inside a division, `dealt` comes before `family` (a roof dealt to the household is the
stronger join), then the larger family before the smaller, then a seeded hash of the
household id. The walk stops when the division's order is full. Whoever is past that is
written to `not_counted` with the reason. Nothing is packed and nothing is chosen by hand.

WHAT IT DOES NOT DO. It mints nobody, moves nobody, touches no card, and raises no roof.
The town's population is the same number before and after: a household fill counts HOUSES,
and every person in these houses was already standing. Store residences are not
touched. The seats refuse every store roof, so no held head stands over a shop, and the
56 the book orders are T-2194's ruling. The seats are themselves an invention
(docs/LIBERTIES.md L354) and this count stands on them. Retire a seat and the count
follows on the next build.

THE HOUSEHOLDS OUTSIDE THE INDEX (T-2237). The rule above read only the residents index,
and T-2194 found the index short: the cards the reconstruction writes beside it — the
trade heads T-1347 drew, the readmitted, the underdocumented, the lodgers and the one
institutional household — stand present on the scene date and the book counted not one of
them as a household. So every one of them is read here too, and sorted by what the seats
make of it:

  * `a_household_of_its_own` — seated on the `dealt` or `family` rung under a standing
    dwelling. It is the same kind of household as a held head's, so it joins the same walk,
    AFTER the held heads of its rung (a record the index carries is the stronger one);
  * `a_bed_in_a_dwelling` / `a_bed_in_a_lodging_house` — seated as a boarder, or put in a
    lodging house's bed by the lodgers stage (T-1371). A bed inside a household another
    seat forms, by rule 2; the book already credits the person as a person fill;
  * `filed_by_its_own_stage` — a lodgers or institutional card, which IS a household and
    whose own stage (T-1371, T-1531) already files it in the book;
  * `not_present` — neither the card nor the presence rulings put it in the town.

Measured 2026-10-09: of the 659 people the cards beside the index hold present, 491 are
beds — every one of the 309 trade heads (297 boarding in a dwelling, 12 in a lodging
house's bed), and nearly every readmitted and underdocumented card — and 156 stand in the
lodging and institutional households their own stages file. Four households, all
underdocumented families of three, stand under a dwelling of their own, and the
family_dwelling order was full before any of them was reached. So the book does not
over-order on their account and no row moves. The person overrun the completion audit
reads is a count of people, not of houses, and is not settled here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_order_book_1835 as ob  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BOOK = DATA / "reconstruction" / "1835_reconstruction_order_book.json"
SEATS = DATA / "reconstruction" / "1835_housing_seats.json"
LEDGER = DATA / "reconstruction" / "1835_held_head_dwellings.json"
LODGERS_SEATED = DATA / "reconstruction" / "1835_lodgers_seated.json"
RESIDENTS = DATA / "residents"
# The resident folders beside the index (town_census.BEYOND_THE_INDEX), and the stage that
# already files the two whose cards ARE households (T-2237).
BEYOND_FOLDERS = ("reconstructed_trades", "lodgers", "readmitted", "underdocumented",
                  "institutional")
FILED_BY = {"lodgers": "T-1371", "institutional": "T-1531"}
BEYOND_CLASSES = {
    "a_household_of_its_own": "seated on the dealt or family rung under a standing dwelling; "
                              "counted like a held head's, after them",
    "a_bed_in_a_dwelling": "boarded in a dwelling whose household another seat forms",
    "a_bed_in_a_lodging_house": "put in a lodging house's bed by the seats or the lodgers "
                                "stage (T-1371)",
    "filed_by_its_own_stage": "a lodging or institutional household its own stage files in "
                              "the book",
    "not_present": "neither the card nor the presence rulings put it in the town on 1 July",
    "not_seated": "present, and no seat, lodging bed or stage holds it",
}

TICKET = "T-2193"
PARENT = "T-2188"
BEYOND_TICKET = "T-2237"
STAGE = "held_head_dwellings"
DIVISIONS = ("north", "south", "west")
CELL = "households/family_dwelling/{}"
# The housing seats' own dwelling families, less its lodging ones (house_the_present_1835.py).
DWELLINGS = {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "H1", "H2"}
RUNGS = {
    "dealt": "the seating dealt this household a standing dwelling of its own, and it lived there",
    "family": "the housing seats put this family under a standing dwelling of its division",
}


def dumps(doc) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def seed_of(hid: str) -> str:
    return hashlib.blake2s(f"{hid}|{TICKET}".encode("utf-8"), digest_size=6).hexdigest()


def room_in_the_book(book: dict) -> dict[str, int]:
    """Each division's family_dwelling order, less every fill but this stage's own."""
    others = Counter()
    for fill in book.get("fills") or []:
        if fill.get("ticket") != TICKET:
            others[fill["bucket"]] += int(fill.get("records") or 0)
    family = next(f for f in book["bucket_families"] if f["key"] == "households")
    by_key = {b["key"]: b for b in family["buckets"]}
    return {d: max(0, int(by_key[CELL.format(d)]["to_reconstruct"] or 0)
                   - others[CELL.format(d)]) for d in DIVISIONS}


def a_household_seat(hid: str, seat: dict | None) -> bool:
    """Rule 2: a household of its own under a standing dwelling, never a bed."""
    if not seat or seat.get("rung") not in RUNGS or seat.get("family") not in DWELLINGS:
        return False
    if seat.get("division") not in DIVISIONS:
        raise SystemExit(f"FAIL {hid} is seated in {seat.get('division')!r}, "
                         "which has no family_dwelling order")
    return True


def classify_beyond(card: dict, seat: dict | None, lodged: set[str]) -> str:
    """What the seats make of one card outside the index (T-2237)."""
    if card["folder"] in FILED_BY:
        return "filed_by_its_own_stage"
    if not card["present"]:
        return "not_present"
    if a_household_seat(card["household"], seat):
        return "a_household_of_its_own"
    if seat and seat.get("rung") == "boarder":
        return "a_bed_in_a_dwelling"
    if (seat and seat.get("rung") == "lodger") or card["household"] in lodged:
        return "a_bed_in_a_lodging_house"
    return "not_seated"


def derive(awaiting: list[str], seats: list[dict], room: dict[str, int],
           beyond: list[dict] = (), lodged: set[str] = frozenset()) -> dict:
    """The ledger, from its inputs and nothing else. Pure, so the self-test can
    break any one of them. `beyond` is one row per card outside the index (T-2237)."""
    waiting = set(awaiting)
    by_household: dict[str, dict] = {}
    for seat in seats:
        if seat["household"] in by_household:
            raise SystemExit(f"FAIL {seat['household']} is seated twice in the housing seats")
        by_household[seat["household"]] = seat
    candidates = []
    for hid in awaiting:
        seat = by_household.get(hid)
        if a_household_seat(hid, seat):
            candidates.append((seat, "index"))
    # T-2237: the cards beside the index, every one of them sorted, and the households
    # among them put into the same walk as the held heads.
    sorted_beyond = Counter()
    persons_beyond = Counter()
    by_folder: dict[str, Counter] = {}
    for card in sorted(beyond, key=lambda c: c["household"]):
        hid = card["household"]
        if hid in waiting:
            raise SystemExit(f"FAIL {hid} is both a held head record and a card beyond "
                             "the index")
        kind = classify_beyond(card, by_household.get(hid), lodged)
        sorted_beyond[kind] += 1
        persons_beyond[kind] += int(card["persons"])
        by_folder.setdefault(card["folder"], Counter())[kind] += 1
        if kind == "a_household_of_its_own":
            candidates.append((by_household[hid], card["folder"]))
    rank = list(RUNGS)
    candidates.sort(key=lambda c: (c[0]["division"], rank.index(c[0]["rung"]),
                                   c[1] != "index", -int(c[0]["persons"]),
                                   seed_of(c[0]["household"])))
    counted, past = [], []
    taken = Counter()
    for seat, source in candidates:
        row = {"household": seat["household"], "division": seat["division"],
               "rung": seat["rung"], "place": seat["place"], "family": seat["family"],
               "persons": int(seat["persons"]), "seed": seed_of(seat["household"])}
        if source != "index":
            row["beyond_the_index"] = source
        if taken[seat["division"]] < room.get(seat["division"], 0):
            taken[seat["division"]] += 1
            counted.append(row)
        else:
            past.append({**row, "why": f"the {seat['division']} division's family_dwelling "
                                       "order was full before this household was reached"})
    assert all(r["household"] in waiting or "beyond_the_index" in r for r in counted)
    fills = {CELL.format(d): taken[d] for d in DIVISIONS if taken[d]}
    present_beyond = sum(persons_beyond[k] for k in BEYOND_CLASSES if k != "not_present")
    beds = persons_beyond["a_bed_in_a_dwelling"] + persons_beyond["a_bed_in_a_lodging_house"]
    own = [r for r in counted + past if "beyond_the_index" in r]
    counted_own = sum(1 for r in counted if "beyond_the_index" in r)
    return {
        "id": "1835_held_head_dwellings",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "stage": STAGE,
        "target_date": "1835-07-01",
        "generated_by": "tools/count_held_head_dwellings_1835.py --build",
        "not_a_reading": "A count over two committed joins (the seating's dealt roofs and the "
                         "housing seats' family rung). It reads no source, rules on no person "
                         "and mints nobody; it says which held heads already stand as a "
                         "family dwelling.",
        "inputs": ["data/residents/index.json", "data/reconstruction/1835_presence_rulings.json",
                   "data/reconstruction/1835_housing_seats.json",
                   "data/reconstruction/1835_reconstruction_order_book.json",
                   "data/reconstruction/1835_lodgers_seated.json"]
                  + [f"data/residents/{f}/*.json" for f in BEYOND_FOLDERS],
        "the_rule": [
            "the order book counts the record as awaiting a household",
            "the housing seats put it under a standing dwelling (D1-D7, H1, H2) on the "
            "`dealt` or `family` rung; a boarder or a lodging-house roof is not counted",
            "its division's family_dwelling order has room once every other stage's fill "
            "is taken off it; dealt before family, larger family first, then the seed",
        ],
        "rungs": RUNGS,
        "mints_nobody": True,
        "liberty": "L354 — the housing seats this count stands on",
        "counts": {
            "records_awaiting_a_household": len(awaiting),
            "under_a_standing_dwelling": dict(sorted(Counter(
                s["rung"] for s, source in candidates if source == "index").items())),
            "room_by_division": {d: room.get(d, 0) for d in DIVISIONS},
            "counted_by_division": {d: taken[d] for d in DIVISIONS},
            "counted_by_rung": dict(sorted(Counter(r["rung"] for r in counted).items())),
            "persons_in_the_counted_houses": sum(r["persons"] for r in counted),
            "not_counted": len(past),
        },
        "beyond_the_index": {
            "ticket": BEYOND_TICKET,
            "asks": "The household quota reads the residents index only. Are the cards the "
                    "reconstruction writes beside it households the town holds, and does the "
                    "book over-order on their account?",
            "classes": BEYOND_CLASSES,
            "households_by_class": {k: sorted_beyond[k] for k in BEYOND_CLASSES},
            "persons_by_class": {k: persons_beyond[k] for k in BEYOND_CLASSES},
            "households_by_folder": {f: {k: n for k, n in sorted(c.items())}
                                     for f, c in sorted(by_folder.items())},
            "filed_by": FILED_BY,
            "households_of_their_own": len(own),
            "counted": counted_own,
            "past_a_full_order": len(own) - counted_own,
            "ruling": (f"Of the {present_beyond:,} people the cards beside the index hold "
                       f"present, {beds:,} are beds in a household another seat forms, and "
                       "the book already credits each as a person; a bed is not a house. "
                       f"{persons_beyond['filed_by_its_own_stage']:,} stand in the lodging and "
                       "institutional households their own stages already file. "
                       f"{len(own)} household(s) stand under a dwelling of their own; "
                       f"{counted_own} counted into the family_dwelling order, "
                       f"{len(own) - counted_own} past it. So the index-only quota does not "
                       "over-order on their account: no household row moves for them."),
            "what_this_does_not_do": "It mints, moves and retires nobody, and does not settle "
                                     "the completion audit's person count against the "
                                     "census ceiling: that is a count of people, not houses.",
        },
        "fills": fills,
        "counted": counted,
        "not_counted": past,
    }


def beyond_the_index(ruled: dict) -> list[dict]:
    """One row per card beside the index, read as town_census.beyond_the_index reads it."""
    rows = []
    for folder in BEYOND_FOLDERS:
        for path in sorted((RESIDENTS / folder).glob("*.json")):
            card = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(card, dict) or not card.get("id"):
                continue
            here = card.get("present_on_scene_date")
            here = here.get("value") if isinstance(here, dict) else here
            rows.append({"household": card["id"], "folder": folder,
                         "persons": len(card.get("persons") or []),
                         "present": here == "present" or card["id"] in ruled})
    return rows


def inputs() -> tuple:
    data = ob.load()
    awaiting = ob.records_awaiting_a_household(data["residents"], data["presence_rulings"])
    seats = json.loads(SEATS.read_text(encoding="utf-8"))["seats"]
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    lodged = {s["household"] for s in
              json.loads(LODGERS_SEATED.read_text(encoding="utf-8")).get("seats") or []}
    beyond = beyond_the_index(ob.ruled_present(data["presence_rulings"]))
    return awaiting, seats, room_in_the_book(book), beyond, lodged


def write_fills(ledger: dict) -> None:
    """Carry the fills into the order book and re-derive it. The book's own --build
    refuses an overfilled bucket, so the room is enforced twice."""
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    rows = [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
             "by": "tools/count_held_head_dwellings_1835.py --build"}
            for key, n in sorted(ledger["fills"].items())]
    book["fills"] = ob.splice_fills(book.get("fills", []), {TICKET}, rows)
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def build() -> int:
    ledger = derive(*inputs())
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    write_fills(ledger)
    c = ledger["counts"]
    print(f"  wrote {LEDGER.relative_to(ROOT)}: {sum(c['counted_by_division'].values())} "
          f"family dwelling(s) counted around held heads {c['counted_by_division']}, "
          f"{c['not_counted']} past a full order; nobody minted")
    return 0


def check() -> int:
    ledger = derive(*inputs())
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print(f"  FAIL {LEDGER.relative_to(ROOT)} is not what --build writes")
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours = {f["bucket"]: int(f.get("records") or 0)
            for f in book.get("fills", []) if f.get("ticket") == TICKET}
    if ours != ledger["fills"]:
        print(f"  FAIL the order book's fills for {TICKET} are not this stage's ledger")
        return 1
    short = {d: n for d, n in ledger["counts"]["room_by_division"].items()
             if n > ledger["counts"]["counted_by_division"][d]}
    if short:
        print(f"  note  the family_dwelling order outruns the seated heads in {short}")
    b = ledger["beyond_the_index"]
    if b["households_by_class"]["not_seated"]:
        print(f"  note  {b['households_by_class']['not_seated']} card(s) beyond the index stand "
              "present with no seat, lodging bed or stage holding them")
    print(f"  ok    {sum(ledger['fills'].values())} family dwelling(s) re-derive from the "
          f"seats and the book carries them ({b['counted']} from beyond the index, "
          f"{b['past_a_full_order']} past the order); nobody minted")
    return 0


def report() -> int:
    ledger = derive(*inputs())
    c = ledger["counts"]
    print(f"THE FAMILY DWELLINGS THE TOWN ALREADY FORMS AROUND HELD HEADS ({TICKET})")
    print(f"  {c['records_awaiting_a_household']:,} records await a household; "
          f"{sum(c['under_a_standing_dwelling'].values())} of them stand under a dwelling "
          f"{c['under_a_standing_dwelling']}")
    for d in DIVISIONS:
        print(f"  {d:<6} room {c['room_by_division'][d]:>4}  counted "
              f"{c['counted_by_division'][d]:>4}")
    print(f"  {c['persons_in_the_counted_houses']:,} people in the counted houses, all of "
          f"them already standing; {c['not_counted']} past a full order")
    b = ledger["beyond_the_index"]
    print(f"BEYOND THE INDEX ({BEYOND_TICKET}): households / persons by what the seats make "
          "of them")
    for k in BEYOND_CLASSES:
        print(f"  {k:<26} {b['households_by_class'][k]:>4} {b['persons_by_class'][k]:>5}")
    print(f"  {b['ruling']}")
    return 0


def self_test() -> int:
    failures = []

    def case(name, ok):
        print("   self-test | %-4s %s" % ("ok" if ok else "FAIL", name))
        if not ok:
            failures.append(name)

    def seat(hid, rung="dealt", family="D3", division="south", persons=1):
        return {"household": hid, "rung": rung, "family": family, "division": division,
                "persons": persons, "place": f"roof_{hid}"}

    room = {"north": 0, "south": 2, "west": 0}
    got = derive(["a", "b"], [seat("a", rung="boarder"), seat("b")], room)
    case("a boarder is never counted as a household",
         [r["household"] for r in got["counted"]] == ["b"])
    got = derive(["a"], [seat("a", family="T1")], room)
    case("a lodging-house roof is never counted", not got["counted"])
    got = derive(["b"], [seat("a"), seat("b")], room)
    case("a record the book does not count as awaiting is never counted",
         [r["household"] for r in got["counted"]] == ["b"])
    got = derive(["a", "b", "c"], [seat("a", rung="family", persons=6), seat("b"),
                                   seat("c", rung="family", persons=3)], room)
    case("the dealt roof is taken before the seated family, then the larger family",
         [r["household"] for r in got["counted"]] == ["b", "a"]
         and [r["household"] for r in got["not_counted"]] == ["c"])
    case("the walk stops at the division's room and says why for the rest",
         got["fills"] == {CELL.format("south"): 2}
         and "full" in got["not_counted"][0]["why"])
    case("the count does not depend on the order its inputs are read in",
         dumps(derive(["a", "b", "c"], [seat("c"), seat("b"), seat("a")], room))
         == dumps(derive(["c", "b", "a"], [seat("a"), seat("b"), seat("c")], room)))
    try:
        derive(["a"], [seat("a"), seat("a")], room)
        case("fires: a household seated twice", False)
    except SystemExit:
        case("fires: a household seated twice", True)
    try:
        derive(["a"], [seat("a", division="fort")], room)
        case("fires: a seat in a division with no family_dwelling order", False)
    except SystemExit:
        case("fires: a seat in a division with no family_dwelling order", True)
    book = {"fills": [{"bucket": CELL.format("south"), "ticket": "T-1174", "records": 5},
                      {"bucket": CELL.format("south"), "ticket": TICKET, "records": 9}],
            "bucket_families": [{"key": "households", "buckets": [
                {"key": CELL.format(d), "to_reconstruct": 20} for d in DIVISIONS]}]}
    case("the room is the order less every OTHER stage's fill, never this stage's own",
         room_in_the_book(book) == {"north": 20, "south": 15, "west": 20})
    # T-2237: the cards beside the index.
    def card(hid, folder="underdocumented", persons=1, present=True):
        return {"household": hid, "folder": folder, "persons": persons, "present": present}

    room = {"north": 0, "south": 2, "west": 0}
    got = derive(["a"], [seat("a", rung="family", persons=2), seat("x", rung="family", persons=5)],
                 room, [card("x", persons=5)])
    case("a household beyond the index is counted, after the held heads of its rung",
         [r["household"] for r in got["counted"]] == ["a", "x"]
         and got["counted"][1]["beyond_the_index"] == "underdocumented"
         and got["beyond_the_index"]["counted"] == 1)
    got = derive([], [seat("x", rung="boarder"), seat("y", rung="lodger", family="H3")], room,
                 [card("x", "reconstructed_trades"), card("y", "readmitted"),
                  card("z", "reconstructed_trades")], {"z"})
    case("a boarder, a lodger and a lodging-house bed beyond the index are beds, never houses",
         not got["counted"] and got["beyond_the_index"]["households_by_class"]
         ["a_bed_in_a_dwelling"] == 1 and got["beyond_the_index"]["households_by_class"]
         ["a_bed_in_a_lodging_house"] == 2)
    got = derive([], [seat("l", rung="family"), seat("i")], room,
                 [card("l", "lodgers", 4), card("i", "institutional")])
    case("a lodging or institutional household is its own stage's fill, never counted again",
         not got["counted"]
         and got["beyond_the_index"]["households_by_class"]["filed_by_its_own_stage"] == 2)
    got = derive([], [seat("x", rung="dealt")], room, [card("x", present=False)])
    case("a card the town does not hold on 1 July is never counted",
         not got["counted"] and got["beyond_the_index"]["households_by_class"]["not_present"] == 1)
    got = derive([], [], room, [card("q")])
    case("a present card nothing holds is reported, not hidden",
         got["beyond_the_index"]["households_by_class"]["not_seated"] == 1)
    try:
        derive(["a"], [seat("a")], room, [card("a")])
        case("fires: a household that is both a held head record and beyond the index", False)
    except SystemExit:
        case("fires: a household that is both a held head record and beyond the index", True)
    print("   self-test | %d failure(s)" % len(failures))
    return 1 if failures else 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for flag in ("--build", "--check", "--report", "--self-test"):
        ap.add_argument(flag, action="store_true")
    args = ap.parse_args(argv)
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
