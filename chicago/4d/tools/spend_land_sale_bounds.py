#!/usr/bin/env python3
"""The 313 upheld land-sale purchases, written onto the cards they name AS BOUNDS (T-1332).

    python3 tools/spend_land_sale_bounds.py             write the ledger and the bounds
    python3 tools/spend_land_sale_bounds.py --check      everything re-derives; nothing drifted
    python3 tools/spend_land_sale_bounds.py --report     person by person, what each tract bounds
    python3 tools/spend_land_sale_bounds.py --self-test  the rules below, held over what it derives

WHY THIS EXISTS. T-1296 wrote the ruling on all 1,572 land-sale purchaser units, and 313 of
them it could not close: the tract was entered on or before 1 July 1835 and the crosswalk's
T-0700 / T-0850 adjudication UPHELD the join between the purchaser and a person this town
holds a card for. A ruling on those rows would have been a ruling on evidence that belongs
on a card, so the register handed them on — `disposition: unresolved`, `ticket: T-1332` —
and said of itself that a hand-off is not a spend. This is the spend.

It is the same hop T-1326 made for the town's own rolls, into the same block, and
deliberately so. `persons[].dated_bounds[]` is where a dated appearance lives; inventing a
second shape for the same fact is the duplication this ticket was told to avoid in as many
words. The block therefore has two owners now, and `tools/dated_bounds_block.py` is the
rule that keeps them from wiping each other.

WHAT A ROW SAYS — AND THE FOUR RULES THAT KEEP IT FROM SAYING MORE.

  1. A PURCHASE IS A TRANSACTION AND NOT A RESIDENCE. This is the standing rule the whole
     domain was read under, and here it is a field rather than a sentence: `here_by` is
     `null` on all 313 rows. `here_by` means "this person was in CHICAGO no later than
     this day" — that is what T-1326 writes into it off a poll list, where a man presented
     himself and voted — and NOTHING in this register says that. Its only column that
     speaks to residence at all reads COOK, ILLINOIS, another county, or UNKNOWN: a county,
     a state, or nothing, and never a town. So a land-sale row is a DATED APPEARANCE in a
     register, `bound_kind: "appearance"`, and the date it carries is in `reaches`.

  2. WHERE THE REGISTER ITSELF STATES COOK, THE ROW SAYS SO AND STILL NOT MORE. Eighteen of
     the 313 read COOK in the Residence column, which is the document stating that a man of
     this name lived in Cook County on the day of the entry — the crosswalk's own
     `what_it_evidences` puts it exactly that way, "not evidence that he lived in the town".
     Those rows carry `bound_kind: "residence_in_cook"`. They do NOT get a `here_by`,
     because Chicago is in Cook County and Cook County is not Chicago, and a field whose one
     meaning is "in the town by" cannot be lent a second meaning for eighteen rows without
     becoming the thing that drifts. Five rows read ILLINOIS and are appearances: Cook is in
     Illinois, so a row reading ILLINOIS states a state and excludes nothing.

  3. EVERY ROW IS `inferred`, AND NOT ONE OF THEM IS `attested`. The REGISTER is
     documented — the Illinois State Archives' index to the federal land offices' own sale
     registers, and the date and the tract are the register's. The IDENTITY is not: all 313
     rows rest on the crosswalk's name adjudication, and its ground is carried on every row
     in `identity_discriminator` (`forename_agrees`, `initial_agrees`). No source states
     that the purchaser is the person on the card. A bound whose subject is inferred is an
     inferred bound however documented the page under it is, so `date_confidence` is
     `documented` and `confidence` is `inferred`, and `--self-test` asserts that uniformity
     rather than leaving it to the data.

  4. ONLY WHAT THE CROSSWALK AND THE RULING REGISTER ALREADY DECLARED. This pass
     re-adjudicates nothing and it does not even pick its own rows: it IMPORTS
     `tools/spend_land_sales_rulings.py` and writes exactly the rows that module's
     `classify()` puts under `the_purchase_bounds_a_held_residents_presence`. One
     classifier, two consumers — so the set this pass writes and the set the register hands
     over cannot come apart, and a re-adjudication moves both at once. `--self-test`
     asserts the count against the register on disk.

NO GRADE MOVES, NO IDENTITY REOPENS, NO PERSON IS MINTED, AND NO OTHER KEY IS TOUCHED.
`--self-test` diffs a record through the applier and asserts the changed key set is
`{"dated_bounds"}` alone. The ladder is applied by T-0515 against every source at once;
this pass hands it evidence, never a verdict.

AND THE RULING REGISTER NO LONGER RULES THESE 313. It cannot: `ruling_coverage_faults` in
`tools/research_spend_ledger.py` fails a ruling on a unit something else already closed,
"because a ruling on a unit something else already closed reads as work done and is not".
Once these bounds are on the cards the ledger closes all 313 as `asserted` off the card, so
`spend_land_sales_rulings.py` stops emitting the rule — which is the contract that file
states about itself, that the ticket closing turns it red.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import dated_bounds_block  # noqa: E402  — the block this pass shares with T-1326

ROOT = TOOLS.parent
LAND = ROOT / "data" / "research" / "land_sales"
LEDGER = LAND / "purchase_bounds_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1
TICKET = "T-1332"
GENERATOR = "tools/spend_land_sale_bounds.py"
BLOCK = dated_bounds_block.BLOCK
SCENE_DATE = "1835-07-01"

# The Illinois State Archives' database — the one id written onto a card, the same one the
# record files and the crosswalk already declare.
SOURCE_ID = "isa_public_domain_land_tract_sales"
REGISTER_TITLE = ("Illinois Public Domain Land Tract Sales Database — the federal land "
                  "offices' sale registers, indexed by the Illinois State Archives")

# The rule in the derived ruling register whose units this pass spends.
RULE = "the_purchase_bounds_a_held_residents_presence"

CONFIDENCE = "inferred"
DATE_CONFIDENCE = "documented"

# The Residence column, where it states the county the town is in. Not ILLINOIS: Cook is in
# Illinois, so a row reading ILLINOIS states a state and excludes nothing — the same
# distinction `spend_land_sales_rulings.py` draws for the same reason.
COOK = "COOK"

TRANSACTION = (
    "A purchase is a TRANSACTION and not a RESIDENCE, so `here_by` is null: nothing in this "
    "register says this person was at Chicago on or before any day. Its only column that "
    "speaks to residence reads a county, a state, or UNKNOWN, and never a town.")


def _rulings_module():
    """The classifier, imported rather than copied — see rule 4 above."""
    spec = importlib.util.spec_from_file_location(
        "spend_land_sales_rulings", TOOLS / "spend_land_sales_rulings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RULINGS = _rulings_module()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- the rows the ruling register hands over -------------------------------------------

def upheld_rows() -> list:
    """(record file, row, the crosswalk match that upheld it) for each of the 313, in order.

    The order is the register's own — file by file, row by row — because a ledger that
    re-sorted its input would stop being a re-derivation of it.
    """
    index = RULINGS.crosswalk_index(RULINGS.read_json(RULINGS.CROSSWALK))
    out = []
    for path in RULINGS.record_files():
        for row in RULINGS.read_json(path).get("records") or []:
            disposal = index.get(row["id"])
            rule, _ = RULINGS.classify(row, disposal)
            if rule != RULE:
                continue
            out.append((path, row, disposal[1]))
    return out


def bound_row(row: dict, match: dict) -> dict:
    """One register entry, as the bound it is — built from the row's own fields and no others."""
    sale = row.get("sale") or {}
    date = str(sale["date_purchased"])
    residence = str(sale.get("residence_as_read") or "").strip().upper()
    in_cook = residence == COOK
    locator = row.get("locator") or {}
    name = row.get("normalized") or row.get("as_read") or row["id"]

    if in_cook:
        says = (
            "THE REGISTER STATES COOK, AND COOK COUNTY IS NOT THE TOWN. The Residence "
            "column reads COOK, so the document itself says a man of this name lived in "
            "Cook County on %s. The crosswalk says what that is worth in its own words — "
            "it is “not evidence that he lived in the town”. %s" % (date, TRANSACTION))
    else:
        says = (
            "A DATED APPEARANCE IN A LAND REGISTER, AND NOTHING FURTHER. The Residence "
            "column reads %s, which places this purchaser nowhere: %s. %s"
            % (residence or "nothing",
               "a state, and Cook is in it" if residence == "ILLINOIS"
               else "the register did not record where the purchaser lived",
               TRANSACTION))

    return {
        # `bound_kind` and `identity_discriminator` are spelled long for the reason T-1326
        # spells them long: `tools/measure_layer_reads.py` matches a field's name against
        # the expressions the renderers evaluate, and a bare `bounds` or `identity` here
        # would collide with names the walkthrough reads for other things entirely.
        "bound_kind": "residence_in_cook" if in_cook else "appearance",
        "list": locator.get("list"),
        "list_title": REGISTER_TITLE,
        "record_id": row["id"],
        "as_read": row.get("as_read"),
        "locator": RULINGS.where(row),
        "describes_date": sale.get("date_as_read") or date,
        "date_confidence": DATE_CONFIDENCE,
        "precision": "day",
        "reaches": date,
        # Null on all 313. See rule 1: this register never puts a body in the town.
        "here_by": None,
        "covers_scene_date": date == SCENE_DATE,
        "confidence": CONFIDENCE,
        "sources": [SOURCE_ID],
        "identity_discriminator": match.get("match"),
        "identity_rule": match.get("rule"),
        "note": (
            "%s THE IDENTITY IS INFERRED AND THE REGISTER IS NOT. The date, the tract and "
            "the purchase number are the register's own, indexed by the Illinois State "
            "Archives from the land offices' sale volumes. What no source states is that "
            "the purchaser is the person on this card: "
            "data/research/land_sales/resident_crosswalk.json joins %s to this card on a "
            "name, upheld under %s, on the ground “%s”. A bound whose subject is "
            "inferred is an inferred bound. No grade moves here and the identity is neither "
            "reopened nor hardened."
            % (says, (row.get("as_read") or name),
               (match.get("ruling") or {}).get("ticket") or "the crosswalk's adjudication",
               match.get("match") or "stated in the crosswalk")),
    }


def people() -> list:
    """One row per PERSON the crosswalk upheld, carrying that person's bounds in order."""
    order: list = []
    seen: dict = {}
    for _, row, match in upheld_rows():
        key = (match["household_id"], match["resident_id"])
        if key not in seen:
            seen[key] = {
                "household_id": match["household_id"],
                "person_id": match["resident_id"],
                "bounds": [],
            }
            order.append(seen[key])
        seen[key]["bounds"].append(bound_row(row, match))
    return order


# --- the ledger -----------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = people()
    kinds: dict = {}
    per_list: dict = {}
    for row in rows:
        for b in row["bounds"]:
            kinds[b["bound_kind"]] = kinds.get(b["bound_kind"], 0) + 1
            per_list[b["list"]] = per_list.get(b["list"], 0) + 1
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by " + GENERATOR + ". The ledger of T-1332: every land-sale purchase "
            "entered on or before 1 July 1835 whose purchaser the T-0700 / T-0850 "
            "adjudication upheld against a card this town holds, written onto that person as "
            "a structured bound the research-spend ledger can see. It records WRITES and not "
            "adjudications — the adjudication is resident_crosswalk.json and the rows are "
            "chosen by spend_land_sales_rulings.py's own classifier — and this file carries "
            "no 'crosswalk' in its name so that measure_research_spend.py cannot read a "
            "write as a second ruling. NOTHING HERE IS A RESIDENCE: a purchase is a "
            "transaction, `here_by` is null on all of them, and the eighteen rows whose "
            "Residence column states COOK bound Cook County and not the town."),
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "source_id": SOURCE_ID,
        "reads": "data/research/land_sales/resident_crosswalk.json, records/*.json",
        "writes": "data/residents/households/*.json — persons[].%s[]" % BLOCK,
        "counts": {
            "bounds_written": sum(len(r["bounds"]) for r in rows),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "identities_changed": 0,
            "persons_minted": 0,
            "per_kind": kinds,
            "per_register_list": {k: per_list[k] for k in sorted(per_list, key=str)},
        },
        "refusals": [
            {
                "rule": "L1",
                "why": ("no row carries a `here_by`. A purchase is a transaction and not a "
                        "residence, and the register's Residence column names a county, a "
                        "state or nothing — never a town — so nothing here puts a body in "
                        "Chicago by any date"),
                "rulings": sum(len(r["bounds"]) for r in rows),
            },
            {
                "rule": "L2",
                "why": ("no row reaches `attested`. Every identity here is the crosswalk's "
                        "name adjudication, and none of them is an identification a source "
                        "makes, so the bound is inferred however documented the register is"),
                "rulings": sum(len(r["bounds"]) for r in rows),
            },
            {
                "rule": "L3",
                "why": ("the eighteen COOK rows are not promoted to a town presence. Chicago "
                        "is in Cook County and Cook County is not Chicago; they carry "
                        "`bound_kind: residence_in_cook` and no `here_by`"),
                "rulings": kinds.get("residence_in_cook", 0),
            },
        ],
        "people": rows,
    }


# --- writing the cards ----------------------------------------------------------------

def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs: this pass's group of one key, rewritten whole.

    Scoped by `tools/dated_bounds_block.py` so that T-1326's roll bounds — the block's
    other owner — are carried through untouched and land in a stable slot either way.
    """
    return dated_bounds_block.write(person, SOURCE_ID, row["bounds"])


def apply(quiet: bool = False) -> int:
    touched = 0
    for row in people():
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, hh)
    if not quiet:
        print("land-sale bounds: written onto %d resident record(s)" % touched)
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
            bad.append("%s is upheld against %d land-sale entr%s and its %s does not "
                       "re-derive — run %s"
                       % (row["person_id"], len(row["bounds"]),
                          "y" if len(row["bounds"]) == 1 else "ies", BLOCK, GENERATOR))
    return bad


def strays(rows: list) -> list:
    """And nobody the crosswalk did NOT uphold may carry a bound off this register."""
    wanted = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        for person in hh.get("persons") or []:
            if not dated_bounds_block.mine(person, SOURCE_ID):
                continue
            if (hh.get("id"), person.get("id")) not in wanted:
                bad.append("%s carries a bound off the land register and the crosswalk "
                           "upholds no purchase against it" % person.get("id"))
    return bad


def register_drift() -> list:
    """The ruling register must have STOPPED ruling these units — see the module docstring."""
    path = LAND / "spend_rulings.json"
    if not path.exists():
        return ["%s is missing" % path.relative_to(ROOT)]
    doc = load(path)
    still = [r for r in doc.get("rulings") or [] if r.get("rule") == RULE]
    if still:
        return ["%s still rules %d unit(s) under %s, which this pass has spent onto the "
                "cards — a ruling on a unit something else closed reads as work done and "
                "is not (research_spend_ledger.ruling_coverage_faults)"
                % (path.relative_to(ROOT), len(still), RULE)]
    return []


def ledger_drift() -> list:
    return ([] if LEDGER.exists() and load(LEDGER) == ledger_doc()
            else ["%s does not re-derive — run %s" % (LEDGER.relative_to(ROOT), GENERATOR)])


def check(quiet: bool = False) -> int:
    rows = people()
    bad = ledger_drift() + register_drift() + gaps(rows) + strays(rows)
    if bad:
        for line in bad[:40]:
            print("  FAIL: %s" % line)
        if len(bad) > 40:
            print("  ... and %d more" % (len(bad) - 40))
        return 1
    if not quiet:
        total = sum(len(r["bounds"]) for r in rows)
        print("land-sale bounds: %d bound(s) on %d card(s), all written, no strays, "
              "none doubled, none still ruled" % (total, len(rows)))
    return 0


def report() -> int:
    for row in people():
        print("%s (%s)" % (row["person_id"], row["household_id"]))
        for b in row["bounds"]:
            print("   %-18s %-10s %s  %s  %s"
                  % (b["bound_kind"], b["reaches"], b["confidence"], b["record_id"],
                     b["as_read"]))
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

    rows = people()
    bounds = [b for r in rows for b in r["bounds"]]

    # Rule 4: the set this pass writes IS the set the ruling register handed over. The
    # register records it under `spent` and rules none of them — see the module docstring.
    register = load(LAND / "spend_rulings.json")
    handed = ((register.get("spent") or {}).get(RULE) or {}).get("units")
    ok("this pass writes one bound per unit the register handed to %s" % TICKET,
       len(bounds) == 313 and handed == 313)
    ok("…and the register itself rules none of them",
       not any(r.get("rule") == RULE for r in register.get("rulings") or []))

    # Rule 1, the standing rule of the whole domain, held as a field.
    ok("not one row claims a Chicago presence", all(b["here_by"] is None for b in bounds))
    ok("every row is an appearance or a Cook residence, and nothing stronger",
       {b["bound_kind"] for b in bounds} <= {"appearance", "residence_in_cook"})
    ok("no row covers the scene date", not any(b["covers_scene_date"] for b in bounds))
    ok("every date the register prints falls on or before the scene date",
       all(b["reaches"] <= SCENE_DATE for b in bounds))

    # Rule 2: COOK is stated by the document; ILLINOIS is a state and excludes nothing.
    cook = [b for b in bounds if b["bound_kind"] == "residence_in_cook"]
    ok("the rows the register states COOK for are the ones marked a Cook residence",
       cook and all("Residence column reads COOK" in b["note"] for b in cook))
    ok("…and a Cook residence still puts no body in the town",
       all(b["here_by"] is None for b in cook))

    # Rule 3: the register is documented, the identity is not.
    ok("every bound is inferred and none is attested",
       bounds and {b["confidence"] for b in bounds} == {CONFIDENCE})
    ok("every bound calls the register's own date documented",
       {b["date_confidence"] for b in bounds} == {DATE_CONFIDENCE})
    ok("every bound carries the ground the crosswalk upheld it on",
       all(b["identity_discriminator"] and b["identity_rule"] for b in bounds))
    ok("every bound names the register and only it",
       all(b["sources"] == [SOURCE_ID] for b in bounds))

    # The ledger reads the CARD, and it reads it by the record id.
    ok("every bound names the register row it was built from",
       all(b["record_id"] and b["record_id"].startswith("ls") for b in bounds))
    ok("no record is written twice",
       len({b["record_id"] for b in bounds}) == len(bounds))

    # Rule: one key and no others. A pass that touched a grade, an identity or a note while
    # writing evidence would be marking its own work.
    before = {"id": "doe_john", "grade": "projected", "sources": ["x"], "note": "n",
              "sex": "male"}
    after = json.loads(json.dumps(before))
    apply_to_person(after, rows[0])
    ok("the applier changes exactly one key",
       {k for k in set(before) | set(after) if before.get(k) != after.get(k)} == {BLOCK})
    ok("the applier is idempotent", apply_to_person(after, rows[0]) is False)
    ok("the block lands in its slot and not at the end of the record",
       list(after) == ["id", "grade", "sources", BLOCK, "note", "sex"])
    roll = {"record_id": "poll_1835_001", "sources": ["chicago_voter_lists_1833_1835_irad"]}
    shared = {"id": "doe_john", "sources": ["x"], BLOCK: [roll]}
    apply_to_person(shared, rows[0])
    ok("a write carries T-1326's roll bounds through untouched",
       shared[BLOCK] == [roll] + rows[0]["bounds"])

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
