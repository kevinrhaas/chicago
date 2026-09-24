#!/usr/bin/env python3
"""The town's own rolls, written onto the cards they name AS BOUNDS (T-1326).

    python3 tools/spend_civic_roll_bounds.py             write the ledger and the bounds
    python3 tools/spend_civic_roll_bounds.py --check     everything re-derives; nothing drifted
    python3 tools/spend_civic_roll_bounds.py --report    person by person, what each roll bounds
    python3 tools/spend_civic_roll_bounds.py --self-test the rules below, held over what it derives

WHY THIS EXISTS, AND WHY IT IS NOT THE PASS THAT CAME BEFORE IT. T-0634's
`tools/spend_civic_voter_lists.py` put the 1833-1835 poll and tax lists ONTO the 236 cards
they name, as a paragraph of prose in `persons[].note` and a source id in
`persons[].sources`. That was the right hop for its ticket and it is untouched here. But a
paragraph is not a field: `tools/research_spend_ledger.py` counts a reading as SPENT only
where a structured, source-bearing, `attested`/`inferred` node NAMES the unit, and a
person node carries `grade` rather than `confidence`. So all 292 matched roll entries went
on reading `unresolved` in the research-spend ledger, deferred to an arrival ticket, while
the evidence itself had been on the cards since 2026-09-04. The hole is the one
`spend_write_once.py` already names in its own table: two of the eight passes that touch a
resident card write a BLOCK and the other six write prose, and only the blocks are legible
to anything downstream.

This pass writes the block. One row per roll ENTRY, on the person the crosswalk matched,
under `persons[].dated_bounds[]` — and a bound is all it is.

WHAT A ROW SAYS, AND THE FOUR RULES THAT KEEP IT FROM SAYING MORE.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED. Like the pass before it, this one
     re-adjudicates nothing: it reads `outcome: "matched"` rows of
     `data/research/civic/voter_crosswalk.json` and writes those. A `candidate` row is a
     rival still standing and writes nothing; an `unmatched` row names nobody. Re-running
     after a re-adjudication moves exactly the rows the re-adjudication moved.

  2. EVERY ROW IS `inferred`, AND NOT ONE OF THEM IS `attested`. The ROLL is documented —
     it is the town's own contemporary paper, held by the Illinois Regional Archives
     Depository. The IDENTITY is not: all 292 matched rows rest on a name agreement, and
     the crosswalk's own discriminator says so for every one of them ("forenames agree
     initial for initial"). No source states that the man on the roll is the man on the
     card. A bound whose subject is inferred is an inferred bound, however documented the
     page is, and the confidence carried here is therefore uniform. `--self-test` asserts
     that uniformity rather than leaving it to the data, because the one thing this pass
     could do to flatter the town is promote a name agreement to an identification.

  3. A ROLL BOUNDS, AND NEVER REACHES THE SCENE DATE. Under the ladder ratified
     2026-09-03 a source EARLIER than 1 July 1835 corroborates and dates and never
     promotes. `covers_scene_date` is therefore `false` on every row, including the 1835
     poll: that list's own record gives its date as `1835` at `inferred` confidence, so
     the latest day it can mean is 1835-12-31 and nothing in it says which side of 1 July
     the poll fell. `reaches` is the last day the reading can mean and `here_by` is the
     bound it puts on the person — for a year-precision list they are the same day, which
     is exactly how weak that kind of bound is.

  4. THE TAX LIST BOUNDS PROPERTY AND NOT PRESENCE (T-1117). The Tax List of the Town of
     Chicago, 1833 names the owners of ground inside the town, resident or not — entry 110
     is Alexander Wolcott, dead since 25 October 1830 — so a tax row's `bound_kind` is
     `property`, its `here_by` is `null`, and `tools/assert_tax_roll_ruling.py` is the gate
     that keeps that ruling from being quietly undone. A pass that wrote 90 tax rows as
     presence bounds would overturn a standing ruling in a field nobody reads.

NO GRADE MOVES, NO IDENTITY REOPENS, NO PERSON IS MINTED, AND NO OTHER KEY IS TOUCHED.
`--self-test` diffs a record through the applier and asserts the changed key set is
`{"dated_bounds"}` alone. The ladder is applied by T-0515 against every source at once;
this pass hands it evidence, never a verdict.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dated_bounds_block  # noqa: E402  — the block this pass shares with T-1332

ROOT = Path(__file__).resolve().parents[1]
CIVIC = ROOT / "data" / "research" / "civic"
CROSSWALK = CIVIC / "voter_crosswalk.json"
RECORDS = CIVIC / "records" / "voter_lists_1833_1835.json"
LEDGER = CIVIC / "roll_bounds_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1
TICKET = "T-1326"
GENERATOR = "tools/spend_civic_roll_bounds.py"
BLOCK = dated_bounds_block.BLOCK
SCENE_DATE = "1835-07-01"

# The archival source, and the only id written onto a card — the same one T-0634 chose,
# for the same reason: the republication is `verified: false` and is named inside the
# source record rather than multiplied across 236 resident records.
SOURCE_ID = "chicago_voter_lists_1833_1835_irad"

# The lists whose rows bound PROPERTY rather than a body in the town (T-1117).
PROPERTY_LISTS = ("tax_1833",)

CONFIDENCE = "inferred"

LADDER = (
    "Under the evidence ladder ratified 2026-09-03 a source EARLIER than the scene date "
    "corroborates and dates and never promotes: a man on a roll of 1833, 1834 or 1835 is "
    "not thereby at Chicago on 1 July 1835.")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- the dates a list can mean --------------------------------------------------------

def reach_of(stated: str) -> tuple[str, str]:
    """(precision, the last day this stated date can mean). The only date rule here."""
    stated = str(stated or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stated):
        return "day", stated
    if re.fullmatch(r"\d{4}-\d{2}", stated):
        month = int(stated[5:7])
        last = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month - 1]
        return "month", "%s-%02d" % (stated, last)
    if re.fullmatch(r"\d{4}", stated):
        return "year", "%s-12-31" % stated
    raise ValueError("a list whose date this pass cannot read: %r" % stated)


# --- what the crosswalk already ruled -------------------------------------------------

def lists_index() -> dict:
    return {row["id"]: row for row in load(RECORDS)["lists"]}


def records_index() -> dict:
    return {row["id"]: row for row in load(RECORDS)["records"]}


def bound_row(entry: dict, record: dict, meta: dict) -> dict:
    """One roll entry, as the bound it is. Built from the row's own fields and no others."""
    precision, reaches = reach_of(meta.get("date"))
    is_property = entry["list"] in PROPERTY_LISTS
    locator = record.get("locator") or {}
    where = "%s line %s" % (locator.get("text_file"), locator.get("line"))
    if is_property:
        says = (
            "PROPERTY, NOT PRESENCE (T-1117). %s names the owners of ground inside the "
            "town, resident or not — its entry 110 is Alexander Wolcott, who had been "
            "dead since 25 October 1830 — so this row bounds what this person was "
            "assessed for and says nothing about where the person was. "
            "tools/assert_tax_roll_ruling.py holds that ruling on the two readings it "
            "rests on." % meta.get("title"))
    else:
        says = (
            "A BOUND ON PRESENCE, AND NOTHING FURTHER. %s records a man who presented "
            "himself and voted, so the entry places a body in Chicago no later than %s. "
            "%s" % (meta.get("title"), reaches, LADDER))
    return {
        # `bound_kind` and `identity_discriminator` are spelled long deliberately.
        # `tools/measure_layer_reads.py` matches a figure's name against the expressions
        # the renderers actually evaluate, and `.bounds` and `.identity` are both read in
        # the walkthrough for things that have nothing to do with a roll — a bare `bounds`
        # here would be "banked as reaching nothing and the renderer accesses it", which
        # is the gate telling the truth about a name collision it cannot see past.
        "bound_kind": "property" if is_property else "presence",
        "list": entry["list"],
        "list_title": meta.get("title"),
        "record_id": entry["record_id"],
        "as_read": entry["as_read"],
        "locator": where,
        "describes_date": meta.get("date"),
        "date_confidence": meta.get("date_confidence"),
        "precision": precision,
        "reaches": reaches,
        "here_by": None if is_property else reaches,
        "covers_scene_date": False,
        "confidence": CONFIDENCE,
        "sources": [SOURCE_ID],
        "identity_discriminator": entry.get("discriminator"),
        "identity_rule": entry.get("rule"),
        "note": (
            "%s THE IDENTITY IS INFERRED AND THE PAGE IS NOT. The reading of the roll is "
            "documented — the town's own paper, held by the Illinois Regional Archives "
            "Depository, twice mediated by Schulz's transcription and Genealogy Trails' "
            "republication, which this project has not gone behind. What no source states "
            "is that the man on the roll is the person on this card: "
            "data/research/civic/voter_crosswalk.json joins them on a name, by its rule "
            "“%s”, and %s. A bound whose subject is inferred is an inferred bound. No "
            "grade moves here and the identity is neither reopened nor hardened."
            % (says, entry.get("rule") or "stated in the crosswalk",
               entry.get("discriminator") or "the discriminator is stated there")),
    }


def matches() -> list:
    """One row per PERSON the crosswalk matched, carrying that person's bounds in order.

    Order is the crosswalk's own — a ledger that re-sorted its input would stop being a
    re-derivation of it.
    """
    doc = load(CROSSWALK)
    lists = lists_index()
    recs = records_index()
    order: list = []
    seen: dict = {}
    for entry in doc["entries"]:
        if entry.get("outcome") != "matched":
            continue
        key = (entry["household_id"], entry["matched_resident"])
        if key not in seen:
            seen[key] = {
                "household_id": entry["household_id"],
                "person_id": entry["matched_resident"],
                "bounds": [],
            }
            order.append(seen[key])
        meta = lists.get(entry["list"]) or {}
        seen[key]["bounds"].append(
            bound_row(entry, recs.get(entry["record_id"], {}), meta))
    return order


# --- the ledger -----------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = matches()
    per_list: dict = {}
    kinds: dict = {}
    for row in rows:
        for b in row["bounds"]:
            per_list[b["list"]] = per_list.get(b["list"], 0) + 1
            kinds[b["bound_kind"]] = kinds.get(b["bound_kind"], 0) + 1
    doc = load(CROSSWALK)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by " + GENERATOR + ". The ledger of T-1326: every matched entry of "
            "the 1833-1835 poll and tax lists, written onto the person the crosswalk "
            "named as a structured bound the research-spend ledger can see. It records "
            "WRITES and not adjudications — the adjudication is voter_crosswalk.json, and "
            "this file carries no 'crosswalk' in its name so that "
            "measure_research_spend.py cannot read a write as a second ruling. Nothing "
            "here is an 1835 residence: a poll row bounds a presence at its own date and "
            "a tax row bounds property and not presence at all."),
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "source_id": SOURCE_ID,
        "reads": "data/research/civic/voter_crosswalk.json",
        "writes": "data/residents/households/*.json — persons[].%s[]" % BLOCK,
        "counts": {
            "bounds_written": sum(len(r["bounds"]) for r in rows),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "identities_changed": 0,
            "per_list": per_list,
            "per_kind": kinds,
            "crosswalk_entries": len(doc["entries"]),
            "candidate_not_written": doc["counts"]["candidate"],
            "unmatched": doc["counts"]["unmatched"],
        },
        "refusals": [
            {
                "rule": "B1",
                "why": ("a `candidate` row is a rival still standing: the crosswalk did "
                        "not choose between the bearers of the name, and a bound written "
                        "off it would print an undecided identity as a decided one"),
                "rulings": doc["counts"]["candidate"],
            },
            {
                "rule": "B2",
                "why": ("no row reaches `attested`. Every matched identity in this "
                        "crosswalk is a name agreement and none of them is an "
                        "identification a source makes, so the bound is inferred however "
                        "documented the page under it is"),
                "rulings": sum(len(r["bounds"]) for r in rows),
            },
            {
                "rule": "B3",
                "why": ("no row covers the scene date. An earlier source corroborates and "
                        "dates and never promotes, and the 1835 poll's own date is "
                        "`inferred` as a bare year, so it cannot be put on either side of "
                        "1 July 1835"),
                "rulings": sum(len(r["bounds"]) for r in rows),
            },
        ],
        "people": rows,
    }


# --- writing the cards ----------------------------------------------------------------

def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs: this pass's group of one key, rewritten whole.

    The block is DERIVED and therefore replaced rather than appended to — which is how it
    holds the once-each rule that `tools/spend_write_once.py` had to give the six
    prose-writing passes a module for. A JSON key exists once by construction and
    `--check` compares this pass's rows against what it re-derives, so a doubled or a
    superseded row cannot survive a run.

    SINCE T-1332 THE BLOCK HAS A SECOND OWNER — the land register's dated appearances —
    so "rewritten whole" is scoped to the rows citing THIS pass's source.
    `tools/dated_bounds_block.py` holds that scoping and the stable group order, so that
    both passes' byte-for-byte checks are true at once and in either run order.
    """
    return dated_bounds_block.write(person, SOURCE_ID, row["bounds"])


def apply(quiet: bool = False) -> int:
    touched = 0
    for row in matches():
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, hh)
    if not quiet:
        print("civic roll bounds: written onto %d resident record(s)" % touched)
    return touched


def build(quiet: bool = False) -> int:
    dump(LEDGER, ledger_doc())
    apply(quiet=quiet)
    if not quiet:
        print("wrote %s" % LEDGER.relative_to(ROOT))
    return 0


# --- the gate -------------------------------------------------------------------------

def gaps(rows: list) -> list:
    """Every bound has to be ON the record it names, and byte-for-byte what derives."""
    bad = []
    for row in rows:
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        if not path.exists():
            bad.append("%s: household %s no longer exists"
                       % (row["person_id"], row["household_id"]))
            continue
        person = next((p for p in load(path).get("persons") or []
                       if p.get("id") == row["person_id"]), None)
        if person is None:
            bad.append("%s: person is no longer in %s"
                       % (row["person_id"], row["household_id"]))
            continue
        if dated_bounds_block.mine(person, SOURCE_ID) != row["bounds"]:
            bad.append("%s is matched to %d roll entr%s and its %s does not re-derive — "
                       "run %s" % (row["person_id"], len(row["bounds"]),
                                   "y" if len(row["bounds"]) == 1 else "ies", BLOCK,
                                   GENERATOR))
    return bad


def strays(rows: list) -> list:
    """And nobody the crosswalk did NOT match may carry a bound off these rolls."""
    wanted = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        for person in hh.get("persons") or []:
            block = person.get(BLOCK) or []
            if not any(b.get("sources") == [SOURCE_ID] for b in block
                       if isinstance(b, dict)):
                continue
            if (hh.get("id"), person.get("id")) not in wanted:
                bad.append("%s carries a bound off the town's rolls and the crosswalk "
                           "matches no entry to it" % person.get("id"))
    return bad


def ledger_drift() -> list:
    return ([] if LEDGER.exists() and load(LEDGER) == ledger_doc()
            else ["%s does not re-derive — run %s" % (LEDGER.relative_to(ROOT), GENERATOR)])


def check(quiet: bool = False) -> int:
    rows = matches()
    bad = ledger_drift() + gaps(rows) + strays(rows)
    if bad:
        for line in bad[:40]:
            print("  FAIL: %s" % line)
        if len(bad) > 40:
            print("  ... and %d more" % (len(bad) - 40))
        return 1
    if not quiet:
        total = sum(len(r["bounds"]) for r in rows)
        print("civic roll bounds: %d bound(s) on %d card(s), all written, no strays, "
              "none doubled" % (total, len(rows)))
    return 0


def report() -> int:
    for row in matches():
        print("%s (%s)" % (row["person_id"], row["household_id"]))
        for b in row["bounds"]:
            print("   %-10s %-9s %s  %s  %s"
                  % (b["list"], b["bound_kind"], b["reaches"], b["confidence"], b["as_read"]))
    return 0


# --- the rules, held over what they derive ---------------------------------------------

def self_test() -> int:
    failures = []
    ran = []

    def ok(label, cond):
        ran.append(label)
        print("  %s %s" % ("ok:  " if cond else "FAIL:", label))
        if not cond:
            failures.append(label)

    ok("a day-precision list reaches its own day", reach_of("1834-08-11") == ("day", "1834-08-11"))
    ok("a bare year reaches 31 December", reach_of("1835") == ("year", "1835-12-31"))
    ok("a month reaches its last day", reach_of("1835-02") == ("month", "1835-02-28"))
    try:
        reach_of("summer")
        ok("an unreadable list date is refused rather than guessed", False)
    except ValueError:
        ok("an unreadable list date is refused rather than guessed", True)

    entry = {"record_id": "tax_1833_001", "list": "tax_1833", "as_read": "Doe, J.",
             "discriminator": "forenames agree initial for initial",
             "rule": "one bearer considered"}
    record = {"locator": {"text_file": "voter_lists_1833_1835.txt", "line": 3}}
    tax = bound_row(entry, record, {"title": "Tax list of the Town of Chicago, 1833",
                                    "date": "1833", "date_confidence": "documented"})
    ok("a tax row bounds property and not presence", tax["bound_kind"] == "property")
    ok("a tax row puts no body in the town", tax["here_by"] is None)

    poll = bound_row(dict(entry, record_id="poll_1835_001", list="poll_1835"), record,
                     {"title": "Poll list of 1835", "date": "1835",
                      "date_confidence": "inferred"})
    ok("a poll row bounds a presence", poll["bound_kind"] == "presence")
    ok("a year-precision poll bounds only the year's end", poll["here_by"] == "1835-12-31")
    ok("no row reaches the scene date", poll["covers_scene_date"] is False)

    rows = matches()
    all_bounds = [b for r in rows for b in r["bounds"]]
    ok("every derived bound is inferred and none is attested",
       all_bounds and {b["confidence"] for b in all_bounds} == {CONFIDENCE})
    ok("no derived bound covers the scene date",
       not any(b["covers_scene_date"] for b in all_bounds))
    ok("every tax bound refuses to place a body",
       all(b["here_by"] is None for b in all_bounds if b["list"] in PROPERTY_LISTS))
    ok("every presence bound reaches before the scene date is over",
       all(b["here_by"] <= "1835-12-31" for b in all_bounds if b["here_by"]))
    ok("every bound names the archival source and only it",
       all(b["sources"] == [SOURCE_ID] for b in all_bounds))
    ok("every bound names a record the roll actually holds",
       {b["record_id"] for b in all_bounds} <= set(records_index()))

    # Rule: one key and no others. A pass that touched a grade, an identity or a note
    # while writing evidence would be marking its own work.
    before = {"id": "doe_john", "grade": "projected", "sources": ["x"], "note": "n",
              "sex": "male"}
    after = json.loads(json.dumps(before))
    apply_to_person(after, rows[0])
    ok("the applier changes exactly one key",
       {k for k in set(before) | set(after) if before.get(k) != after.get(k)} == {BLOCK})
    ok("the applier is idempotent", apply_to_person(after, rows[0]) is False)
    ok("the block lands in its slot and not at the end of the record",
       list(after) == ["id", "grade", "sources", BLOCK, "note", "sex"])

    # T-1332 put a second owner on this block. A rewrite here must not touch its rows.
    land = {"record_id": "ls0959", "sources": ["isa_public_domain_land_tract_sales"]}
    shared = {"id": "doe_john", "sources": ["x"], BLOCK: [land]}
    apply_to_person(shared, rows[0])
    ok("a rewrite carries the land register's group through untouched",
       shared[BLOCK] == rows[0]["bounds"] + [land])

    print("  %d check(s), %d failure(s)" % (len(ran), len(failures)))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    if args.check:
        return check(quiet=args.quiet)
    return build(quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
