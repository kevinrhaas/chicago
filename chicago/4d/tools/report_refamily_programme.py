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
ticket as "the honest alternative". The ruling asked for the held people to be
re-familied rather than retired. The rule the ruling got yields a bounded number of
moves and then stops. So when the programme has been spent in full, the great majority
of the surplus is STILL HELD — and there is no piece of work left that could move it,
because T-1558 measured the ceilings and the axes are disjoint. That number existed in
no file: the order book states the surplus BEFORE the programme, the rule states the
moves the programme makes, and nothing subtracted one from the other and said what the
town is left holding.

WHAT IT FINDS, and every figure in this paragraph is DERIVED rather than written here —
the rule has been re-modelled twice since this report was first built and a number typed
into a docstring goes stale in a way the report itself cannot. Held at the ruling less
the moves the rule yields is what the buckets are left holding; a handful of buckets
clear completely and the rest go on naming two figures apiece. The remedy reaches a
minority of what it was asked to remedy. That is not an argument against the ruling —
the alternative the owner refused was deleting the invented people, and this project
does not un-write somebody to make arithmetic close — but it is the thing a reader of
the order book is owed, and docs/LIBERTIES.md L268 carries it as a liberty rather than
leaving it to be reverse-engineered out of two JSON files.

AND SINCE 2026-09-25 IT CARRIES THE OWNER'S ANSWER ABOUT THE RESIDUE (T-1597). The
report could say how many were left holding; nothing said what they ARE. The owner was
asked, and ruled that they remain held, recorded as held, with the programme settled at
the rule's fixpoint rather than at nought. `the_residue_and_the_ruling_on_it` below reads
that decision off the order book's own programme step — count, buckets, the refusal that
holds each of them, and what would reopen it — so the two documents cannot disagree.

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


def converges_to(ledger: dict, converge: dict, outstanding: int) -> dict:
    """Where the town lands now and where it lands when the programme is spent.

    THE PROJECTION THIS STOPPED COPYING (T-1597). The rule publishes
    `converges_to_if_the_rule_is_spent` as its own figure less every move it yields, and
    that is the T-1563 double count one file over: once the moves are SPENT, the standing
    and owed figures the subtraction starts from are already post-move, so subtracting the
    same 129 again predicts a town 129 people smaller than the one that exists. Shipped
    beside a programme the owner settled AT ITS FIXPOINT, it said the town would still
    fall by 129 when nothing whatever would move it.

    So this computes both ends from the two numbers that are read — the layer's standing
    persons and what the book still owes — and keeps the rule's projection in the document
    under its own name, marked, rather than deleting a figure another tool published.
    `model_refamily_rule.py` owns the projection and is where the fix belongs; this report
    refuses to restate it.
    """
    standing = converge["persons_standing_in_the_layer"]
    owed_now = ledger["what_it_would_converge_to"]["still_owed_now"]
    if converge["converges_to_now"] != standing + owed_now:
        raise Fault(f"the rule has the town converging to {converge['converges_to_now']:,} now "
                    f"and the book has {standing:,} standing plus {owed_now:,} owed")
    owed_spent = owed_now - outstanding
    lands = standing + owed_spent
    point, (low, high) = converge["the_model_point"], converge["the_model_range"]
    if not low <= lands <= high:
        raise Fault(f"the town would converge to {lands:,}, outside the model's {low:,}-{high:,}")
    above = lands - point
    doc = {
        "still_owed_now": owed_now,
        "still_owed_when_the_programme_is_spent": owed_spent,
        "persons_standing_in_the_layer": standing,
        "converges_to_now": converge["converges_to_now"],
        "converges_to_when_the_programme_is_spent": lands,
        "the_model_point": point,
        "the_model_range": [low, high],
        "reading": (f"{lands:,} is inside the model's {low:,}-{high:,} and {abs(above):,} "
                    f"{'above' if above >= 0 else 'below'} its {point:,} point, against "
                    f"{abs(converge['converges_to_now'] - point):,} above it today."),
    }
    if converge.get("converges_to_if_the_rule_is_spent") != lands:
        doc["and_the_rules_own_projection_is_not_used"] = {
            "the_rule_says": converge.get("converges_to_if_the_rule_is_spent"),
            "this_report_says": lands,
            "why": "the rule subtracts every move it yields from a standing-and-owed pair "
                   "that is ALREADY post-move, so once the moves are spent it counts them "
                   "twice — the T-1563 double count, one file over. Both ends here are "
                   "computed from the layer's standing persons and what the book still "
                   "owes; `model_refamily_rule.py` owns the projection and the fix.",
        }
    return doc


def residue_of(book: dict, still_held: int) -> dict:
    """The residue and the owner's ruling on it (T-1597), read off the book's own step.

    Nothing here is restated: the order book's `re_family_ledger.the_programme` is where
    the finish line lives and where `build_order_book_1835.py`'s own gate holds it to the
    rule's remainder. This report's job is to put it in front of a reader of the
    PROGRAMME, who would otherwise learn how many people are left holding and nothing
    about what they are.

    THE ONE THING THIS FILE CAN CHECK THAT THE BOOK CANNOT. The book counts what is held
    TODAY; this report counts what is held once every move the rule yields has been made.
    Those are the same number only at the fixpoint — which is exactly when the book calls
    the programme settled. So a settled programme whose count differs from this report's
    end state is one of the two documents having moved without the other, and that is a
    refusal rather than a note.
    """
    step = (book.get("re_family_ledger") or {}).get("the_programme")
    if not isinstance(step, dict):
        raise Fault("the order book's re-family ledger states no programme step, so nothing "
                    "says where the programme finishes or what the residue is (T-1597)")
    missing = [f for f in ("settled", "people_still_held", "buckets_they_are_held_in",
                           "and_what_holds_each_of_them", "the_finish_line",
                           "the_ruling_that_set_it", "what_becomes_of_them",
                           "what_would_reopen_it") if step.get(f) is None]
    if missing:
        raise Fault("the book's programme step states no " + ", no ".join(missing))
    if step["settled"] and step["people_still_held"] != still_held:
        raise Fault(f"the book settles the programme over {step['people_still_held']} people "
                    f"still held and this report's end state holds {still_held}")
    return {
        "people_still_held": step["people_still_held"],
        "buckets_they_are_held_in": step["buckets_they_are_held_in"],
        "and_what_holds_each_of_them": step["and_what_holds_each_of_them"],
        "the_programme_is_settled": bool(step["settled"]),
        "the_finish_line": step["the_finish_line"],
        "the_ruling_that_set_it": step["the_ruling_that_set_it"],
        "what_becomes_of_them": step["what_becomes_of_them"],
        "what_would_reopen_it": step["what_would_reopen_it"],
        "read_from": "data/reconstruction/1835_reconstruction_order_book.json "
                     "§ re_family_ledger.the_programme",
    }


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
    ceil = rule["the_ceilings"]
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
            # THE CEILINGS ARE READ, NOT RESTATED. This sentence carried 233/123/73 from the
            # first derivation of the rule and went stale twice while the rule was re-modelled
            # under it — a hard-coded number in a report about a moving ledger (T-1597).
            "and_nothing_can_move_them": (
                f"T-1558 measured the ceilings, each loosening one more axis than the one "
                f"above it: {ceil['if_only_the_division_changed']} if only the division "
                f"changed, {ceil['if_the_household_kind_changed_too']} if the household kind "
                f"changed too, {ceil['if_the_trade_could_change_as_well']} if the trade could "
                f"change as well, and {ceil['under_this_rule']} under the rule as written. The "
                f"remainder is not waiting on a run; it is waiting on an order book that wants "
                f"women and children somewhere else."),
        },
        "what_the_town_converges_to": converges_to(ledger, converge, len(pending)),
        "the_residue_and_the_ruling_on_it": residue_of(book, still_held),
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
    res = doc["the_residue_and_the_ruling_on_it"]
    is_settled = "settled" if res["the_programme_is_settled"] else "not settled"
    out += ["",
            "## Where the programme finishes, and what the residue is",
            "",
            f"The programme is **{is_settled}**, and its finish line is "
            f"{res['the_finish_line']}",
            "",
            f"> {res['the_ruling_that_set_it']}",
            "",
            f"**{_fmt(res['people_still_held'])} people remain held**, in "
            f"{res['buckets_they_are_held_in']} refused bucket(s). What becomes of them is "
            f"{res['what_becomes_of_them']}",
            "",
            "| the refusal that holds them | people |",
            "|---|---:|"]
    out += [f"| `{r['refusal']}` | {_fmt(r['people'])} |"
            for r in res["and_what_holds_each_of_them"]]
    out += ["",
            f"**What would reopen it:** {res['what_would_reopen_it']}",
            "",
            f"Read from `{res['read_from']}`.",
            "",
            "## What the town converges to",
            "",
            f"- standing in the layer: {_fmt(conv['persons_standing_in_the_layer'])}",
            f"- still owed now: {_fmt(conv['still_owed_now'])}",
            f"- still owed when the programme is spent: "
            f"{_fmt(conv['still_owed_when_the_programme_is_spent'])}",
            f"- converges to now: {_fmt(conv['converges_to_now'])}",
            f"- converges to when the programme is spent: "
            f"{_fmt(conv['converges_to_when_the_programme_is_spent'])}",
            f"- {conv['reading']}"]
    if conv.get("and_the_rules_own_projection_is_not_used"):
        not_used = conv["and_the_rules_own_projection_is_not_used"]
        out += ["",
                f"The rule's own projection of {_fmt(not_used['the_rule_says'])} is NOT used "
                f"here, and {not_used['why']}"]
    out += ["",
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
    # The fixtures bend a move still OUTSTANDING: a move already spent is not re-read
    # here, so bending a spent one would prove nothing. Since T-1564 the programme is
    # SETTLED — every move the rule yields is spent — so there is no outstanding move to
    # bend and one is made by taking the last spent move back out of the book's ledger.
    # That is the same fixture it always was, and it goes on holding when the rule yields
    # a fresh round that nobody has spent yet.
    book = json.loads(json.dumps(book))
    made = {m["person"] for m in book["re_family_ledger"]["moves"]}
    if len(made) >= len(rule["the_moves_the_rule_yields"]):
        put_back = book["re_family_ledger"]["moves"].pop()
        made.discard(put_back["person"])
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
    # BENT ON THE BUCKET THE OUTSTANDING MOVE ACTUALLY LEAVES, which since T-1564 is not
    # `recut_refusals[0]`: a spent move is not re-read, so emptying any other bucket's
    # surplus is a change nothing looks at.
    overdrawn = json.loads(json.dumps(book))
    leaves = rule["the_moves_the_rule_yields"][first]["from_bucket"]
    for refusal in overdrawn["recut_refusals"]:
        if refusal["bucket"] == leaves:
            refusal["surplus_still_held"] = 0
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
    # AND BOTH ENDS OF THE CONVERGENCE ARE THE SAME TWO READ NUMBERS (T-1597), never the
    # rule's own projection: standing plus owed, at each end.
    conv = doc["what_the_town_converges_to"]
    assert conv["converges_to_now"] == \
        conv["persons_standing_in_the_layer"] + conv["still_owed_now"], conv
    assert conv["converges_to_when_the_programme_is_spent"] == \
        conv["persons_standing_in_the_layer"] + conv["still_owed_when_the_programme_is_spent"], conv
    bent = json.loads(json.dumps(rule["what_the_town_converges_to"]))
    bent["converges_to_now"] += 7
    fires("a rule whose town does not converge to its own standing plus owed",
          lambda: converges_to(_load(BOOK)["re_family_ledger"], bent, 0))
    outside = json.loads(json.dumps(rule["what_the_town_converges_to"]))
    outside["the_model_range"] = [0, 1]
    fires("a town converging outside the model's own range",
          lambda: converges_to(_load(BOOK)["re_family_ledger"], outside, 0))

    # 5. THE RESIDUE AND THE RULING ON IT ARE THE BOOK'S OWN (T-1597), never restated here:
    # the two documents settle over one set of people or one of them has moved alone.
    res = doc["the_residue_and_the_ruling_on_it"]
    step = _load(BOOK)["re_family_ledger"]["the_programme"]
    assert res["people_still_held"] == step["people_still_held"], res
    assert res["the_ruling_that_set_it"] == step["the_ruling_that_set_it"], res
    assert not res["the_programme_is_settled"] or \
        res["people_still_held"] == four["people_still_held_when_it_is_spent"], res
    assert sum(r["people"] for r in res["and_what_holds_each_of_them"]) \
        == res["people_still_held"], res
    left_holding = four["people_still_held_when_it_is_spent"]
    drifted = json.loads(json.dumps(_load(BOOK)))
    drifted["re_family_ledger"]["the_programme"]["people_still_held"] += 1
    fires("a settled programme whose residue is not the one this report ends on",
          lambda: residue_of(drifted, left_holding))
    no_step = json.loads(json.dumps(_load(BOOK)))
    del no_step["re_family_ledger"]["the_programme"]
    fires("an order book that says nothing about where the programme finishes",
          lambda: residue_of(no_step, left_holding))
    silent = json.loads(json.dumps(_load(BOOK)))
    del silent["re_family_ledger"]["the_programme"]["what_becomes_of_them"]
    fires("a programme step that does not say what becomes of the people it holds",
          lambda: residue_of(silent, left_holding))

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
