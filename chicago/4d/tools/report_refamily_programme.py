#!/usr/bin/env python3
"""T-1560 — the re-familying programme's own report: the counts, the rule, and the ruling.

    python3 tools/report_refamily_programme.py --build      derive the report
    python3 tools/report_refamily_programme.py --check      re-derive and refuse drift
    python3 tools/report_refamily_programme.py --self-test  each clause refusing its own case

WHAT THIS IS. Piece 4 of 4 of T-1556, the owner's ruling of 2026-09-24 on T-1530. The
other three pieces each own one act: T-1557 built the WORD for a move and moved nobody,
T-1558 modelled WHO may move and moved nobody, T-1559 SPENDS the moves. This piece owns
the accounting of the programme as a whole, and it moves nobody either — it writes one
derived JSON and one derived report, and not one card.

WHY THE PROGRAMME NEEDS A REPORT OF ITS OWN, and it is the reason T-1558 named this
ticket as "the honest alternative". The ruling asked for the 523 held people to be
re-familied rather than retired. The rule the ruling got yields **73** moves. So when
the programme has been spent in full, the great majority of the surplus is STILL HELD —
and there is no piece of work left that could move it, because T-1558 measured the
ceilings and the axes are disjoint. That number exists in no file today: the order book
states the surplus BEFORE the programme, the rule states the moves the programme makes,
and nothing subtracts one from the other and says what the town is left holding.

WHAT IT FINDS. 523 - 73 = **450 people still held, in 43 of the 48 refused buckets**.
Five buckets clear completely and forty-three go on naming two figures apiece. The
remedy reaches 14% of what it was asked to remedy. That is not an argument against the
ruling — the alternative the owner refused was deleting 523 invented people, and this
project does not un-write somebody to make arithmetic close — but it is the thing a
reader of the order book is owed, and docs/LIBERTIES.md L268 carries it as a liberty
rather than leaving it to be reverse-engineered out of two JSON files.

HOW IT STAYS TRUE WHILE T-1559 SPENDS. The report never hard-codes a stage of the
programme. `moves made` is read from the order book's own re-family ledger, `moves the
rule yields` from the rule, and the outstanding moves are the difference BY PERSON — so
as T-1563 and T-1564 land, the "spent" column rises, the "outstanding" column falls, and
the end state the report predicts does not move at all. The gate below asserts exactly
that: the two ends must agree for every bucket, on every build.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
RULE = ROOT / "data" / "reconstruction" / "1835_refamily_rule.json"
OUT = ROOT / "data" / "reconstruction" / "1835_refamily_programme.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_refamily_programme.md"

TICKET = "T-1560"
PARENT = "T-1556"
# The four pieces, and the one sentence each is answerable for. The states are read
# from the ledger rather than written here: `settled` moves as the pieces land.
PIECES = (
    ("T-1557", "the ledger and the order book's accounting of a move, with zero moves made"),
    ("T-1558", "the rule that chooses WHICH held heads move, modelled against the adoption layers"),
    ("T-1559", "the moves themselves, in bucket-family stages"),
    ("T-1560", "this report: the counts, the rule, and the owner's ruling behind them"),
)


class Fault(Exception):
    """A refusal this report makes by name."""


def _load(path: Path) -> dict:
    if not path.exists():
        raise Fault(f"{path.relative_to(ROOT)} is missing — the programme cannot be reported on")
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ the arithmetic --
#
# One subtraction, done per bucket rather than in aggregate, because the aggregate is
# exactly what T-1556 § 3 got wrong: 523 held and 427 open looks like 265 moves until
# somebody asks which cells they are in.


def outstanding_moves(book: dict, rule: dict) -> list[dict]:
    """The moves the rule yields that the ledger has not yet spent, by person.

    A move is identified by the PERSON, not by its position in either list: the rule
    publishes its 73 in its own order and the ledger appends as stages land.
    """
    yielded = {m["person"]: m for m in rule["the_moves_the_rule_yields"]}
    if len(yielded) != len(rule["the_moves_the_rule_yields"]):
        raise Fault("the rule yields two moves for one person")
    spent = [m["person"] for m in book["re_family_ledger"]["moves"]]
    if len(set(spent)) != len(spent):
        raise Fault("the ledger has moved one person twice")
    for person in spent:
        if person not in yielded:
            raise Fault(f"the ledger has moved {person}, whom the rule never yielded — a "
                        f"move must stand on a rung T-1558 published")
    return [yielded[p] for p in yielded if p not in set(spent)]


def end_state(book: dict, rule: dict) -> dict:
    """What every refused bucket holds once the programme has been spent in full."""
    refusals = {b["bucket"]: b for b in book["recut_refusals"]}
    out = Counter(m["from_bucket"] for m in outstanding_moves(book, rule))
    into = Counter(m["to_bucket"] for m in outstanding_moves(book, rule))
    for bucket in out:
        if bucket not in refusals:
            raise Fault(f"an outstanding move leaves {bucket}, which the book does not refuse "
                        f"— only a bucket holding surplus has anybody to move")
    for bucket in into:
        if bucket in refusals:
            raise Fault(f"an outstanding move lands in {bucket}, which is itself refused — a "
                        f"move must reach an OPEN order or it moves the surplus sideways")
    rows = []
    for bucket, row in refusals.items():
        leaving = out.get(bucket, 0)
        holding = row["surplus_still_held"]
        if leaving > holding:
            raise Fault(f"{bucket} would send out {leaving} of the {holding} it still holds")
        rows.append({"bucket": bucket,
                     "owning_ticket": row["owning_ticket"],
                     "held_at": row["held_at"],
                     "the_re_cut_would_have_ordered": row["the_re_cut_would_have_ordered"],
                     "surplus_still_held": holding,
                     "refamilied_out_already": row["refamilied_out"],
                     "outstanding_moves": leaving,
                     "surplus_when_the_programme_is_spent": holding - leaving})
    rows.sort(key=lambda r: (-r["surplus_when_the_programme_is_spent"], r["bucket"]))
    return {"buckets": rows}


def by_family(rows: list[dict]) -> list[dict]:
    """The remainder rolled up on (sex, age band) — the axes the ruling cannot reach.

    This is the shape of the finding rather than a convenience: the surplus that cannot
    move is women and children, and a 43-row table says that less plainly than 8 do.
    """
    tally: Counter = Counter()
    for row in rows:
        if row["surplus_when_the_programme_is_spent"] <= 0:
            continue
        _, sex, band, *_ = row["bucket"].split("/")
        tally[(sex, band)] += row["surplus_when_the_programme_is_spent"]
    return [{"sex": sex, "age_band": band, "people_still_held": n}
            for (sex, band), n in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))]


def derive() -> dict:
    book, rule = _load(BOOK), _load(RULE)
    ledger = book["re_family_ledger"]
    held = ledger["the_held_surplus"]
    rows = end_state(book, rule)["buckets"]
    pending = outstanding_moves(book, rule)
    made = ledger["counts"]["moves"]
    yields = rule["counts"]["moves_the_rule_yields"]
    if made + len(pending) != yields:
        raise Fault(f"{made} moves made and {len(pending)} outstanding is not the {yields} "
                    f"the rule yields")
    still_held = sum(r["surplus_when_the_programme_is_spent"] for r in rows)
    # THE BOOK'S `people_held` IS WHAT IS HELD NOW, not what was held when the owner ruled
    # (T-1563): every move T-1559 spends takes its head out of a refused bucket's
    # `already_drawn`, so the book's figure falls by one per move made. Subtracting every
    # move the rule yields from it counts the spent moves twice. The figure at the ruling
    # is today's plus what has already moved; today's less what is still outstanding is
    # the same end state reached the other way, and both have to agree.
    ruled = held["people_held"] + made
    if ruled - yields != still_held or held["people_held"] - len(pending) != still_held:
        raise Fault(f"{ruled} held at the ruling less {yields} moved is not the {still_held} "
                    f"the buckets are left holding ({held['people_held']} held today, "
                    f"{len(pending)} moves outstanding)")
    converge = rule["what_the_town_converges_to"]
    settled = {"T-1557": True, "T-1558": bool(ledger["who_chooses_who_moves"]["settled"]),
               "T-1559": bool(ledger["who_makes_the_moves"]["settled"]),
               "T-1560": False}
    return {
        "$schema_note": "No schema. DERIVED — regenerate with "
                        "tools/report_refamily_programme.py --build. Do not hand-edit.",
        "id": "chicago_1835_refamily_programme",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "target_date": "1835-07-01",
        "generated_by": "tools/report_refamily_programme.py --build",
        "read_by": ["data/reconstruction/1835_reconstruction_order_book.json",
                    "data/reconstruction/1835_refamily_rule.json"],
        "not_a_reading": "This report adjudicates no source and reads nothing new. It "
                         "subtracts one derived file from another and states the result.",
        "moves_nobody": True,
        "writes_no_card": True,
        "the_ruling": ledger["ruling"],
        "what_a_move_is": ledger["what_a_move_is"],
        "what_a_move_is_not": ledger["what_a_move_is_not"],
        "the_pieces": [{"ticket": t, "owns": owns, "settled": settled[t]} for t, owns in PIECES],
        "the_programme_in_four_numbers": {
            "held_when_the_ruling_was_made": ruled,
            "moves_T_1556_named": rule["the_ceilings"]["the_number_T_1556_named"],
            "moves_the_rule_yields": yields,
            "people_still_held_when_it_is_spent": still_held,
            "the_remedy_reaches": round(yields / ruled, 4),
        },
        "where_the_programme_stands": {
            "moves_made": made,
            "moves_outstanding": len(pending),
            # The ticket each outstanding move NAMES, which is the programme's own
            # ticket and not the stage that will spend it: T-1558 wrote T-1556 onto
            # every move it yielded, and T-1559's pieces deal them out by bucket family.
            "outstanding_by_the_ticket_the_move_names": [
                {"ticket": t, "moves": n}
                for t, n in sorted(Counter(m["ticket"] for m in pending).items())],
            "surplus_still_held_today": held["people_still_held"],
        },
        "what_it_is_left_holding": {
            "people": still_held,
            "buckets": sum(1 for r in rows if r["surplus_when_the_programme_is_spent"] > 0),
            "buckets_cleared": sum(1 for r in rows
                                   if r["surplus_when_the_programme_is_spent"] == 0),
            "of_refused_buckets": len(rows),
            "by_family": by_family(rows),
            "and_nothing_can_move_them": "T-1558 measured the ceilings: with a person's sex "
                                         "and age band fixed the bound is 233, with the trade "
                                         "fixed too it is 123, and with movability applied and "
                                         "a house kept whole it is 73. The remainder is not "
                                         "waiting on a run; it is waiting on an order book that "
                                         "wants women and children somewhere else.",
        },
        "what_the_town_converges_to": {
            "still_owed_now": ledger["what_it_would_converge_to"]["still_owed_now"],
            "still_owed_when_the_programme_is_spent":
                ledger["what_it_would_converge_to"]["still_owed_now"] - len(pending),
            "persons_standing_in_the_layer": converge["persons_standing_in_the_layer"],
            "converges_to_now": converge["converges_to_now"],
            "converges_to_when_the_programme_is_spent": converge["converges_to_if_the_rule_is_spent"],
            "the_model_point": converge["the_model_point"],
            "the_model_range": converge["the_model_range"],
            "reading": converge["reading"],
        },
        "what_the_book_goes_on_saying": "Each of the buckets below keeps its `held_at` and "
                                        "its `the_re_cut_would_have_ordered` side by side, "
                                        "which is T-1459's ruling of 2026-09-20 and is the "
                                        "state the 2026-09-24 ruling IMPROVED on rather than "
                                        "abolished. docs/LIBERTIES.md L268 is the admission.",
        "what_would_move_the_remainder": rule["what_would_raise_the_ceiling"],
        "the_end_state": rows,
    }


# ---------------------------------------------------------------------- the report --


def _fmt(n: int) -> str:
    return f"{n:,}"


def report_text(doc: dict) -> str:
    four = doc["the_programme_in_four_numbers"]
    left = doc["what_it_is_left_holding"]
    stands = doc["where_the_programme_stands"]
    conv = doc["what_the_town_converges_to"]
    out = [f"# The re-familying programme, reported — what the ruling asked and what it reaches ({TICKET})",
           "",
           "DERIVED — regenerate with `python3 tools/report_refamily_programme.py --build`.",
           f"Piece 4 of 4 of {PARENT}. **This report moves nobody and writes no card.**",
           "",
           "## The ruling",
           "",
           f"> {doc['the_ruling']}",
           "",
           f"**A move is** {doc['what_a_move_is']}",
           "",
           f"**A move is not** {doc['what_a_move_is_not']}",
           "",
           "## The programme in four numbers",
           "",
           "| | |",
           "|---|---:|",
           f"| held when the ruling was made | {_fmt(four['held_when_the_ruling_was_made'])} |",
           f"| moves {PARENT} § 3 named | {_fmt(four['moves_T_1556_named'])} |",
           f"| moves the rule yields | **{_fmt(four['moves_the_rule_yields'])}** |",
           f"| people still held when it is spent | **{_fmt(four['people_still_held_when_it_is_spent'])}** |",
           "",
           f"The remedy reaches {four['the_remedy_reaches'] * 100:.0f}% of what it was asked to "
           f"remedy. The other {100 - four['the_remedy_reaches'] * 100:.0f}% is not owed to a "
           "ticket and is not waiting on a run.",
           "",
           "## The four pieces"]
    out += ["", "| piece | owns | settled |", "|---|---|---|"]
    out += [f"| `{p['ticket']}` | {p['owns']} | {'yes' if p['settled'] else 'not yet'} |"
            for p in doc["the_pieces"]]
    out += ["",
            "## Where it stands",
            "",
            f"{_fmt(stands['moves_made'])} move(s) made, {_fmt(stands['moves_outstanding'])} "
            f"outstanding, {_fmt(stands['surplus_still_held_today'])} people held today."]
    if stands["outstanding_by_the_ticket_the_move_names"]:
        out += ["", "| the ticket each outstanding move names | moves |", "|---|---:|"]
        out += [f"| `{s['ticket']}` | {_fmt(s['moves'])} |"
                for s in stands["outstanding_by_the_ticket_the_move_names"]]
    out += ["",
            "## What it is left holding",
            "",
            f"{_fmt(left['people'])} people stand in {left['buckets']} of the "
            f"{left['of_refused_buckets']} refused buckets once every move the rule yields has "
            f"been made. {left['buckets_cleared']} bucket(s) clear completely.",
            "",
            left["and_nothing_can_move_them"],
            "",
            "| sex | age band | still held |",
            "|---|---|---:|"]
    out += [f"| {r['sex']} | `{r['age_band']}` | {_fmt(r['people_still_held'])} |"
            for r in left["by_family"]]
    out += ["",
            "## What the town converges to",
            "",
            f"- standing in the layer: {_fmt(conv['persons_standing_in_the_layer'])}",
            f"- still owed now: {_fmt(conv['still_owed_now'])}",
            f"- still owed when the programme is spent: "
            f"{_fmt(conv['still_owed_when_the_programme_is_spent'])}",
            f"- converges to now: {_fmt(conv['converges_to_now'])}",
            f"- converges to when the programme is spent: "
            f"{_fmt(conv['converges_to_when_the_programme_is_spent'])}",
            f"- {conv['reading']}",
            "",
            "## What would move the remainder",
            ""]
    out += [f"- **{lever['id']}** ({lever['who_owns_it']}) — {lever['says']}"
            for lever in doc["what_would_move_the_remainder"]]
    out += ["",
            "## Every refused bucket, and what it is left holding",
            "",
            doc["what_the_book_goes_on_saying"],
            "",
            "| bucket | ticket | held at | the re-cut would have ordered | surplus today | "
            "moves outstanding | left holding |",
            "|---|---|---:|---:|---:|---:|---:|"]
    out += [f"| `{r['bucket']}` | {r['owning_ticket']} | {r['held_at']} | "
            f"{r['the_re_cut_would_have_ordered']} | {r['surplus_still_held']} | "
            f"{r['outstanding_moves']} | {r['surplus_when_the_programme_is_spent']} |"
            for r in doc["the_end_state"]]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------------ commands --


def cmd_build() -> int:
    doc = derive()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    four, left = doc["the_programme_in_four_numbers"], doc["what_it_is_left_holding"]
    print(f"OK: the re-familying programme — {four['held_when_the_ruling_was_made']:,} held, "
          f"{four['moves_the_rule_yields']:,} moves yielded against the "
          f"{four['moves_T_1556_named']:,} {PARENT} named, "
          f"{four['people_still_held_when_it_is_spent']:,} still held in {left['buckets']} of "
          f"{left['of_refused_buckets']} buckets when it is spent")
    return 0


def cmd_check() -> int:
    faults = []
    if not OUT.exists():
        print("FAIL: the re-familying programme report is missing — run --build", file=sys.stderr)
        return 1
    expected = derive()
    if json.loads(OUT.read_text(encoding="utf-8")) != expected:
        faults.append("the re-familying programme report is stale — run --build")
    if not REPORT.exists():
        faults.append("the re-familying programme's markdown is missing — run --build")
    elif REPORT.read_text(encoding="utf-8") != report_text(expected):
        faults.append("the re-familying programme's markdown is stale — run --build")
    if faults:
        for fault in faults:
            print(f"FAIL: {fault}", file=sys.stderr)
        return 1
    four = expected["the_programme_in_four_numbers"]
    left = expected["what_it_is_left_holding"]
    print(f"OK: the re-familying programme re-derives — {four['moves_the_rule_yields']:,} moves "
          f"against {four['held_when_the_ruling_was_made']:,} held, "
          f"{four['people_still_held_when_it_is_spent']:,} left in {left['buckets']} buckets")
    return 0


def cmd_self_test() -> int:
    book, rule = _load(BOOK), _load(RULE)
    fired = 0

    def fires(why, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            print(f"   self-test | FAIL as intended: {why}")
            return
        raise AssertionError(f"the report did NOT refuse {why}")

    # 1. THE TWO ENDS MUST AGREE. The whole report is one subtraction, so the assertion
    # it stands on is that the rule's moves and the book's ledger are the same 73 moves
    # seen from either end. A ledger that has spent a move the rule never yielded is the
    # failure this catches, and it is exactly what a hand-edited spend would look like.
    derive()
    invented = json.loads(json.dumps(book))
    invented["re_family_ledger"]["moves"] = [{"person": "rc_nobody_at_all"}]
    fires("a ledger move the rule never yielded",
          lambda: outstanding_moves(invented, rule))
    twice = json.loads(json.dumps(book))
    twice["re_family_ledger"]["moves"] = [dict(rule["the_moves_the_rule_yields"][0]),
                                          dict(rule["the_moves_the_rule_yields"][0])]
    fires("one person moved twice", lambda: outstanding_moves(twice, rule))

    # 2. A MOVE MUST LEAVE A HELD BUCKET AND REACH AN OPEN ORDER. Moving the surplus
    # from one refused bucket into another would satisfy every count in this file and
    # remedy nothing whatever, so both directions are refused by name.
    # The fixtures bend the first move still OUTSTANDING: a move already spent is not
    # re-read here (T-1563 spends the first ones), so bending it would prove nothing.
    made = {m["person"] for m in book["re_family_ledger"]["moves"]}
    first = next(i for i, m in enumerate(rule["the_moves_the_rule_yields"])
                 if m["person"] not in made)
    sideways = json.loads(json.dumps(rule))
    sideways["the_moves_the_rule_yields"][first]["to_bucket"] = book["recut_refusals"][0]["bucket"]
    fires("a move landing in a bucket that is itself refused",
          lambda: end_state(book, sideways))
    nowhere = json.loads(json.dumps(rule))
    nowhere["the_moves_the_rule_yields"][first]["from_bucket"] = "persons/male/20_29/south/family/none"
    fires("a move leaving a bucket the book does not refuse",
          lambda: end_state(book, nowhere))

    # 3. A BUCKET CANNOT SEND OUT MORE THAN IT HOLDS. The per-bucket subtraction is the
    # point of this report — the aggregate is what T-1556 § 3 read, and it is how 265
    # moves came to be named for a ladder that yields 73.
    overdrawn = json.loads(json.dumps(book))
    overdrawn["recut_refusals"][0]["surplus_still_held"] = 0
    fires("a bucket sending out more people than it still holds",
          lambda: end_state(overdrawn, rule))

    # 4. THE ARITHMETIC CLOSES IN BOTH DIRECTIONS, and nothing here is a restatement of
    # what the inputs already say: held less moved must equal what the buckets are left
    # holding, bucket by bucket and in total.
    doc = derive()
    four = doc["the_programme_in_four_numbers"]
    assert (four["held_when_the_ruling_was_made"] - four["moves_the_rule_yields"]
            == four["people_still_held_when_it_is_spent"]), "the subtraction does not close"
    assert sum(r["people_still_held"] for r in doc["what_it_is_left_holding"]["by_family"]) \
        == four["people_still_held_when_it_is_spent"], "the family rollup loses people"
    assert four["moves_the_rule_yields"] < four["moves_T_1556_named"], \
        "the rule now yields what T-1556 named — this report's finding has gone away"
    stands = doc["where_the_programme_stands"]
    assert doc["what_the_town_converges_to"]["still_owed_when_the_programme_is_spent"] == \
        doc["what_the_town_converges_to"]["still_owed_now"] - stands["moves_outstanding"], \
        "what is still owed does not fall by what is still to move"
    # A SPENT MOVE IS COUNTED ONCE (T-1563): what was held at the ruling is today's
    # surplus plus what has already moved, and the moves made and outstanding add up
    # to what the rule yields.
    assert four["held_when_the_ruling_was_made"] == \
        stands["surplus_still_held_today"] + stands["moves_made"], "a spent move is lost"
    assert stands["moves_made"] + stands["moves_outstanding"] == four["moves_the_rule_yields"]

    print(f"OK: {fired} refusal(s) fired as intended, and the arithmetic closes both ways")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
