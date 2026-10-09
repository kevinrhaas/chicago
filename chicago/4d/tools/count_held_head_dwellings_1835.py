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

TICKET = "T-2193"
PARENT = "T-2188"
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


def derive(awaiting: list[str], seats: list[dict], room: dict[str, int]) -> dict:
    """The ledger, from the three inputs and nothing else. Pure, so the self-test can
    break any one of them."""
    waiting = set(awaiting)
    by_household: dict[str, dict] = {}
    for seat in seats:
        if seat["household"] in by_household:
            raise SystemExit(f"FAIL {seat['household']} is seated twice in the housing seats")
        by_household[seat["household"]] = seat
    candidates = []
    for hid in awaiting:
        seat = by_household.get(hid)
        if not seat or seat.get("rung") not in RUNGS or seat.get("family") not in DWELLINGS:
            continue
        if seat.get("division") not in DIVISIONS:
            raise SystemExit(f"FAIL {hid} is seated in {seat.get('division')!r}, "
                             "which has no family_dwelling order")
        candidates.append(seat)
    rank = list(RUNGS)
    candidates.sort(key=lambda s: (s["division"], rank.index(s["rung"]),
                                   -int(s["persons"]), seed_of(s["household"])))
    counted, past = [], []
    taken = Counter()
    for seat in candidates:
        row = {"household": seat["household"], "division": seat["division"],
               "rung": seat["rung"], "place": seat["place"], "family": seat["family"],
               "persons": int(seat["persons"]), "seed": seed_of(seat["household"])}
        if taken[seat["division"]] < room.get(seat["division"], 0):
            taken[seat["division"]] += 1
            counted.append(row)
        else:
            past.append({**row, "why": f"the {seat['division']} division's family_dwelling "
                                       "order was full before this household was reached"})
    assert all(r["household"] in waiting for r in counted)
    fills = {CELL.format(d): taken[d] for d in DIVISIONS if taken[d]}
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
                   "data/reconstruction/1835_reconstruction_order_book.json"],
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
                s["rung"] for s in candidates).items())),
            "room_by_division": {d: room.get(d, 0) for d in DIVISIONS},
            "counted_by_division": {d: taken[d] for d in DIVISIONS},
            "counted_by_rung": dict(sorted(Counter(r["rung"] for r in counted).items())),
            "persons_in_the_counted_houses": sum(r["persons"] for r in counted),
            "not_counted": len(past),
        },
        "fills": fills,
        "counted": counted,
        "not_counted": past,
    }


def inputs() -> tuple[list[str], list[dict], dict]:
    data = ob.load()
    awaiting = ob.records_awaiting_a_household(data["residents"], data["presence_rulings"])
    seats = json.loads(SEATS.read_text(encoding="utf-8"))["seats"]
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    return awaiting, seats, room_in_the_book(book)


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
    print(f"  ok    {sum(ledger['fills'].values())} family dwelling(s) re-derive from the "
          "seats and the book carries them; nobody minted")
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
