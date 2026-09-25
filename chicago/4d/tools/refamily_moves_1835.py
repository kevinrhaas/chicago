#!/usr/bin/env python3
"""Spend the re-family moves the rule yields, where the cards already say so (T-1563).

    python3 tools/refamily_moves_1835.py --build      carry the spent moves into the book
    python3 tools/refamily_moves_1835.py --check      re-derive the ledger and refuse drift
    python3 tools/refamily_moves_1835.py --report     what is spent and what is still owed
    python3 tools/refamily_moves_1835.py --self-test

THREE TICKETS AND ONE LEDGER. The owner's ruling of 2026-09-24 (T-1556, answering T-1530)
turned the 523 reconstructed people the re-cut holds from something RETIRED into something
MOVED. T-1557 built the accounting — a move recorded on both ends, so a bucket's draw is
never un-written — and moved nobody. T-1558 modelled WHICH heads may move, published the
cost ladder at `data/reconstruction/1835_refamily_rule.json`, and found that the rule
yields 73 moves rather than the 265 the aggregate suggested. This tool spends them.

THE CARD IS THE AUTHORITY AND THIS FILE IS THE ACCOUNTANT. A move is two statements: the
household card says which cell its head is counted in, and the order book's ledger says
the same thing in the book's own arithmetic. Only one of them can be the original, and it
is the card — the card is where a reader meets the person, and C1 is a rung ABOUT the
card ("the cell is written on an invented card that took it from the bucket"). So the
mints carry the move onto the card inside their own derivation, where the seeds, the
names and the ids are already fixed and `--check` re-derives every byte; and this tool
writes a row into the book ONLY where the card it names already carries the same move,
field for field.

That ordering buys the one guarantee that matters here: **the book cannot claim a move
the layer has not made.** A row typed into the ledger by hand names a card; the card does
not agree; `--build` drops it and `--check` goes red. And the converse is checked too — a
`refamilied` block standing on a card that the rule does not yield a move for is a fault,
so the two cannot drift apart in either direction.

WHAT IS SPENT AND WHAT IS STILL OWED. The rule's 73 moves belong to two mints: 19 to
`reconstruct_trade_households.py` (T-1563) and 54 to `reconstruct_women_children.py`
(T-1564). This tool is indifferent to which — it spends what the layer says, counts what
the rule still owes, and the book's `who_makes_the_moves` reads `settled` only when the
two numbers meet. Nothing here decides who moves; that was T-1558's and is read, not
re-derived.

IT MINTS NOBODY, RETIRES NOBODY, AND MOVES NO GEOMETRY. Every head it counts is a head
the town already holds, standing on a card that already exists, at `lives_at: null`. What
falls is what the town is still OWED.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_order_book_1835 as ob  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
RULE = ROOT / "data" / "reconstruction" / "1835_refamily_rule.json"
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"

TICKET = "T-1563"
PARENT = "T-1559"
#: The block a mint writes onto a moved card, and the three fields of it that must agree
#: with the rule's row before a move may be counted. They are the whole of the move: who
#: he was dealt as, who he is counted as, and the rung that let him cross.
CARD_BLOCK = "refamilied"
MUST_AGREE = (("drawn_in_bucket", "from_bucket"),
              ("counted_in_bucket", "to_bucket"),
              ("rule", "rule"))


class Fault(Exception):
    """A statement this tool may not write."""


def rule_doc() -> dict:
    if not RULE.exists():
        raise Fault("the re-family rule is missing — run tools/model_refamily_rule.py --build")
    return json.loads(RULE.read_text(encoding="utf-8"))


def yielded() -> list:
    """The moves T-1558's rule yields, in its own order. Read, never re-derived."""
    rows = rule_doc().get("the_moves_the_rule_yields") or []
    if not rows:
        raise Fault("the re-family rule yields no moves at all")
    return rows


def household_cards() -> dict:
    """Every household card in the residents layer, by id, with its path.

    The layer keeps reconstructions outside `households/` on purpose — a trade head lives
    in `reconstructed_trades/`, a readmitted household in `readmitted/` — so the index is
    built by walking the directories rather than by assuming one.
    """
    found = {}
    for path in sorted(RESIDENTS.glob("*/*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(doc, dict):
            continue
        hid = doc.get("id")
        if not hid or not doc.get("head") or "persons" not in doc:
            continue
        if hid in found:
            raise Fault(f"two household cards answer to {hid}")
        found[hid] = (path, doc)
    return found


def spent(rows: list, cards: dict) -> tuple[list, list]:
    """(the moves the cards carry, the moves still owed) — in the rule's own order."""
    made, owing = [], []
    for row in rows:
        hid = row.get("household")
        entry = cards.get(hid)
        block = (entry[1].get(CARD_BLOCK) or {}) if entry else {}
        if not block:
            owing.append(row)
            continue
        for on_card, in_rule in MUST_AGREE:
            if block.get(on_card) != row.get(in_rule):
                raise Fault(
                    f"{hid} says it was re-familied {on_card}={block.get(on_card)!r} and "
                    f"the rule says {in_rule}={row.get(in_rule)!r}")
        person = row.get("person")
        if person not in {p.get("id") for p in entry[1].get("persons") or []}:
            raise Fault(f"the rule re-families {person}, who is not on {hid}")
        if entry[1].get("division") != str(row["to_bucket"]).split("/")[3]:
            raise Fault(
                f"{hid} is counted in {row['to_bucket']} and its card states the "
                f"{entry[1].get('division')} division")
        made.append({
            "person": person,
            "household": hid,
            "from_bucket": row["from_bucket"],
            "to_bucket": row["to_bucket"],
            "rule": row["rule"],
            "changes": list(row.get("changes") or []),
            "ticket": row.get("ticket") or PARENT,
            "adoptions_carried": list(row.get("adoptions_carried") or []),
            "carried_by": {
                "ticket": block.get("ticket"),
                "stage": entry[1].get("source_pass"),
                "card": str(entry[0].relative_to(RESIDENTS)),
            },
        })
    return made, owing


def stray_blocks(rows: list, cards: dict) -> list:
    """Cards claiming a re-family the rule does not yield. A move may not be hand-written."""
    allowed = {row.get("household") for row in rows}
    return sorted(hid for hid, (_path, doc) in cards.items()
                  if doc.get(CARD_BLOCK) and hid not in allowed)


def derive() -> tuple[list, list, list]:
    rows = yielded()
    cards = household_cards()
    stray = stray_blocks(rows, cards)
    if stray:
        raise Fault("a card carries a re-family the rule does not yield: "
                    + ", ".join(stray[:6]))
    made, owing = spent(rows, cards)
    return made, owing, rows


def write(made: list) -> None:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    book.setdefault("re_family_ledger", {})["moves"] = made
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def still_owed(owing: list, cards: dict | None = None) -> dict:
    """Who owes the rest, read off the buckets the unspent rows leave."""
    by_stage: dict = {}
    for row in owing:
        stage = ("trade_households" if str(row["from_bucket"]).endswith("/family/trade")
                 else "women_and_children")
        by_stage[stage] = by_stage.get(stage, 0) + 1
    return dict(sorted(by_stage.items()))


def cmd_build() -> int:
    made, owing, rows = derive()
    write(made)
    print("OK: %d of the %d moves the rule yields are spent; %d still owed %s"
          % (len(made), len(rows), len(owing), still_owed(owing) or "— none"))
    return 0


def cmd_check() -> int:
    made, owing, rows = derive()
    if not BOOK.exists():
        print("FAIL: the order book is missing — run build_order_book_1835.py --build",
              file=sys.stderr)
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    committed = (book.get("re_family_ledger") or {}).get("moves") or []
    if committed != made:
        print("FAIL: the book's re-family ledger is not what the cards carry — "
              "run tools/refamily_moves_1835.py --build", file=sys.stderr)
        return 1
    print("OK: the book's re-family ledger carries %d move(s), each on a card that says "
          "the same thing; %d of the rule's %d still owed %s"
          % (len(made), len(owing), len(rows), still_owed(owing) or "— none"))
    return 0


def cmd_report() -> int:
    made, owing, rows = derive()
    print("THE RE-FAMILY, AS THE LAYER STANDS")
    print("  the rule yields   %3d move(s)" % len(rows))
    print("  spent             %3d" % len(made))
    print("  still owed        %3d  %s" % (len(owing), still_owed(owing) or ""))
    by_ticket: dict = {}
    for m in made:
        key = (m["carried_by"].get("ticket"), m["carried_by"].get("stage"))
        by_ticket[key] = by_ticket.get(key, 0) + 1
    for (ticket, stage), n in sorted(by_ticket.items(), key=lambda kv: str(kv[0])):
        print("  carried by %-8s %-34s %3d" % (ticket, stage, n))
    return 0


def cmd_self_test() -> int:
    fired = 0

    def fires(why, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            print("   fires: %s" % why)
            return
        raise AssertionError("did not fire: %s" % why)

    rows = yielded()
    cards = household_cards()
    made, owing = spent(rows, cards)
    assert made or owing, "the rule yields moves and none of them is either spent or owed"
    assert len(made) + len(owing) == len(rows), (len(made), len(owing), len(rows))

    # THE ROWS COME OUT IN THE RULE'S ORDER, so the ledger a reader compares against the
    # rule reads down the same list. Order is derived, never sorted into a new one.
    order = [row["person"] for row in rows if row["household"] in
             {m["household"] for m in made}]
    assert [m["person"] for m in made] == order, "the ledger re-orders the rule"

    # A MOVE THE CARD DOES NOT CARRY IS NOT SPENT — the whole point of the ordering.
    stripped = {hid: (path, {k: v for k, v in doc.items() if k != CARD_BLOCK})
                for hid, (path, doc) in cards.items()}
    assert spent(rows, stripped)[0] == [], "a card with no block still spent its move"
    assert len(spent(rows, stripped)[1]) == len(rows)

    # AND A CARD THAT DISAGREES WITH THE RULE IS A FAULT RATHER THAN A DROPPED ROW. A
    # silently dropped row is how a ledger and a layer drift apart while both look green.
    first = next(m for m in made)
    for on_card, _in_rule in MUST_AGREE:
        bent = {hid: (path, json.loads(json.dumps(doc)))
                for hid, (path, doc) in cards.items()}
        bent[first["household"]][1][CARD_BLOCK][on_card] = "persons/nobody/at/all"
        fires("a card whose %s disagrees with the rule" % on_card,
              lambda b=bent: spent(rows, b))

    # A CARD CLAIMING A MOVE THE RULE DOES NOT YIELD IS A FAULT. This is the hand-written
    # re-family, and it must not survive a --check.
    invented = {hid: (path, json.loads(json.dumps(doc)))
                for hid, (path, doc) in cards.items()}
    free = next(hid for hid, (_p, doc) in invented.items() if not doc.get(CARD_BLOCK))
    invented[free][1][CARD_BLOCK] = {"rule": "C1"}
    assert stray_blocks(rows, invented) == [free], stray_blocks(rows, invented)

    # AND THE DIVISION ON THE CARD IS THE DESTINATION BUCKET'S. C1 rewrites exactly that
    # statement, so a card that kept the old one is a move only half made.
    moved = {hid: (path, json.loads(json.dumps(doc)))
             for hid, (path, doc) in cards.items()}
    moved[first["household"]][1]["division"] = "nowhere"
    fires("a moved card that still states the division it was dealt in",
          lambda: spent(rows, moved))

    # THE PERSON THE ROW NAMES STANDS ON THE CARD THE ROW NAMES.
    orphan = {hid: (path, json.loads(json.dumps(doc)))
              for hid, (path, doc) in cards.items()}
    orphan[first["household"]][1]["persons"] = []
    fires("a row naming somebody who is not on the household it names",
          lambda: spent(rows, orphan))

    print("OK: %d fixture(s) fired; %d move(s) spent, %d owed" % (fired, len(made), len(owing)))
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
        print("FAIL: %s" % exc, file=sys.stderr)
        return 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
