#!/usr/bin/env python3
"""The town's own rolls of 1833-1835, SPENT on the people they name (T-0634, pass 1).

    python3 tools/spend_civic_voter_lists.py             write the ledger and the cards
    python3 tools/spend_civic_voter_lists.py --check     everything re-derives; nothing drifted
    python3 tools/spend_civic_voter_lists.py --report    person by person, which rolls meet them
    python3 tools/spend_civic_voter_lists.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. `tools/measure_research_spend.py` asks two questions of this project's
research. The first is whether what was READ was ever RULED ON. The second — the one the
owner actually asked on 2026-09-03, "there are not outputs or updates to the household and
resident data" — is whether a ruling that names a person in this town ever reached that
PERSON'S CARD. Measured on dev the morning of 2026-09-04, the civic domain answered:

    civic   99 reached, 99 judgeable, 0 on a card, 99 unwritten

Ninety-nine adjudicated matches between the four early Chicago lists and the residents
layer, and not one of the ninety-nine had put a source on the record it named. The
adjudication happened in `data/research/civic/voter_crosswalk.json` and stopped there.
This pass is the hop, and it is the whole of what T-0634 asks for: write what is already
ruled onto the card it names, and measure the difference.

THE FOUR LISTS, and what each is. They are the town's own paper, not a recollection of it:
the poll list of the first election of the Board of Trustees of the Town of Chicago,
10 August 1833; the tax list of the Town of Chicago, 1833; the poll list of the 1834
election, filed 11 August 1834; and the 1835 poll list. This project has never seen the
IRAD originals — the reading is twice mediated, Schulz's transcription and Genealogy
Trails' republication of it — and every record here says so.

WHAT IS AND IS NOT WRITTEN, in four rules.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED. This pass re-adjudicates nothing. It reads
     `outcome: "matched"` rows and writes those; a `candidate` row is a rival still
     standing and writes nothing, and an `unmatched` row names nobody. The pass is
     therefore reversible from the crosswalk in both directions, and re-running it after
     a re-adjudication moves exactly the rows the re-adjudication moved.

  2. TWO FIELDS AND NO OTHERS. A person gains the source id in `sources` and a paragraph
     in `note`. Nothing else on the record is touched — not a grade, not an arrival, not
     a claim block, not a placement. `--self-test` holds that by diffing a record through
     the applier and asserting the changed key set.

  3. NO GRADE MOVES, and this is the rule the ratified ladder forces. Under it (T-0513)
     "attested = 1835 poll + any second independent source ... inferred = 1835 poll alone,
     or 1833/1834 lists with another source". A pass that both wrote the evidence and
     re-read the ladder off it would be grading itself; the ladder is applied by T-0515,
     against every source at once, and this pass hands it the evidence rather than the
     verdict. The count of grades this pass changes is zero and `--check` holds it there.

  4. ONE PARAGRAPH PER PERSON, NOT PER ENTRY. Fifty-five people carry the ninety-nine
     matches between them — Philo Carpenter stands on three of the four rolls — and a
     card that said the same thing three times would be harder to read, not better
     evidenced. Every list that names the person is named in the one paragraph, with the
     line as printed and the record id it was read into, so nothing is lost by the fold.

THE LEDGER IS NOT A CROSSWALK, deliberately. `data/research/civic/voter_spend_1835.json`
records what this pass did, and it is named so that `measure_research_spend.py` does NOT
read it as an adjudication: that instrument counts any file with "crosswalk" in its name,
and a ledger of writes counted as rulings would report fifty-five new rulings reaching a
person and fifty-five of them written — the pass grading its own homework and inflating
both columns of the very measurement it exists to move. The adjudication is
`voter_crosswalk.json` and remains the only one.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(Path(__file__).resolve().parent))

# THE ONCE-EACH RULE lives in one place (T-0846). `gaps` asks whether this pass's
# paragraph is PRESENT and `strays` whether an unruled card carries one; neither can
# see a card that carries it TWICE, which is what an add-only applier produces when the
# wording changes between runs. T-0677 measured that on this series and closed it in one
# tool; three copies later the copies had already drifted apart, so the rule is shared.
import spend_write_once  # noqa: E402
CIVIC = ROOT / "data" / "research" / "civic"
CROSSWALK = CIVIC / "voter_crosswalk.json"
RECORDS = CIVIC / "records" / "voter_lists_1833_1835.json"
LEDGER = CIVIC / "voter_spend_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1

# The archival source, and the only id written onto a card. The republication
# (`chicago_genealogist_1993_voter_lists`) is the link in the chain and is named in the
# source record itself; it is `verified: false` and `rights_status: check_required`, so it
# is not multiplied across fifty-five resident records by this pass.
SOURCE_ID = "chicago_voter_lists_1833_1835_irad"

# The sentence that says a paragraph is this pass's, so re-running it is idempotent and
# `--check` can find its own work without guessing.
MARKER = "THE TOWN'S OWN ROLLS, 1833-1835 — CORROBORATION, NOT A GRADE."

# A WORDING THIS PASS HAS REPLACED — the second half of the once-each rule (T-0846). An
# applier here is add-only (`if MARKER not in note`), so rewriting the paragraph makes a
# re-run APPEND a second one saying the same thing in different words rather than overwrite
# the first, and neither `gaps` nor `strays` can see it. T-0677 measured exactly that on
# `spend_land_sales.py`: thirty-one cards doubled, `tools/check.sh` green. Any MARKER this
# pass retires belongs in this tuple from the commit that retires it, and `--check` then
# refuses a card still carrying it. Empty means this pass has never changed its wording.
SUPERSEDED_MARKERS: tuple = ()

LADDER_LIMIT = (
    "Under the ratified ladder (T-0513) the 1835 poll with a second independent source is "
    "attested, the 1835 poll alone or a 1833/1834 list with another source is inferred, and "
    "a single appearance with nothing else is a projected resident. This pass WRITES THE "
    "EVIDENCE AND MOVES NO GRADE — T-0515 applies the ladder against every source at once."
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- what the crosswalk already ruled -------------------------------------------------

def lists_index() -> dict:
    """id -> the list's own title and date, as its records file states them."""
    return {row["id"]: row for row in load(RECORDS)["lists"]}


def records_index() -> dict:
    return {row["id"]: row for row in load(RECORDS)["records"]}


def matches() -> list:
    """One row per PERSON the crosswalk matched, folding that person's entries together.

    Order is the crosswalk's own — a ledger that re-sorted its input would stop being a
    re-derivation of it — and inside a person the entries keep the order they were read in.
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
                "source_id": SOURCE_ID,
                "entries": [],
            }
            order.append(seen[key])
        rec = recs.get(entry["record_id"], {})
        locator = rec.get("locator") or {}
        seen[key]["entries"].append({
            "record_id": entry["record_id"],
            "list": entry["list"],
            "list_title": lists.get(entry["list"], {}).get("title"),
            "list_date": lists.get(entry["list"], {}).get("date"),
            "as_read": entry["as_read"],
            "line": locator.get("line"),
            "rule": entry.get("rule"),
            "discriminator": entry.get("discriminator"),
        })
    return order


def paragraph(row: dict) -> str:
    """What one person's card is told, and the whole of it."""
    cites = "; ".join(
        "%s — “%s” (%s, line %s)"
        % (e["list_title"], e["as_read"], e["record_id"], e["line"])
        for e in row["entries"])
    rule = row["entries"][0]["rule"] or "stated in the crosswalk"
    return (
        "%s The early Chicago voter and tax lists held by the Illinois Regional Archives "
        "Depository name this person %d time%s: %s. These are the town's own contemporary "
        "paper rather than a recollection of it, and each appearance says that a man of "
        "that name stood on that roll in that year — no more. The reading is twice "
        "mediated (Schulz's transcription, then Genealogy Trails' republication) and this "
        "project has not seen the IRAD originals. %s Identity by the crosswalk's own rule: "
        "%s (data/research/civic/voter_crosswalk.json)."
        % (MARKER, len(row["entries"]), "" if len(row["entries"]) == 1 else "s",
           cites, LADDER_LIMIT, rule))


# --- the ledger -----------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = matches()
    per_list: dict = {}
    for row in rows:
        for e in row["entries"]:
            per_list[e["list"]] = per_list.get(e["list"], 0) + 1
    doc = load(CROSSWALK)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by tools/spend_civic_voter_lists.py. The ledger of T-0634's first "
            "consolidation pass: which of voter_crosswalk.json's matched rulings were "
            "written onto the card they name, and what each card was told. It is a record "
            "of WRITES, not of adjudications — the adjudication is voter_crosswalk.json "
            "and this file deliberately carries no 'crosswalk' in its name so that "
            "measure_research_spend.py does not count a write as a second ruling."),
        "generated_by": "tools/spend_civic_voter_lists.py",
        "ticket": "T-0634",
        "source_id": SOURCE_ID,
        "reads": "data/research/civic/voter_crosswalk.json",
        "writes": "data/residents/households/*.json — persons[].sources and persons[].note",
        "counts": {
            "matched_rulings": sum(len(r["entries"]) for r in rows),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "per_list": per_list,
            "crosswalk_entries": len(doc["entries"]),
            "candidate_not_written": doc["counts"]["candidate"],
            "unmatched": doc["counts"]["unmatched"],
        },
        "refusals": [
            {
                "rule": "V1",
                "why": ("a `candidate` row is a rival still standing: the crosswalk did not "
                        "choose between the bearers of the name, and a card that cited the "
                        "roll anyway would print an undecided identity as a decided one"),
                "rulings": doc["counts"]["candidate"],
            },
            {
                "rule": "V2",
                "why": ("no grade moves here. The ratified ladder reads every source at "
                        "once and T-0515 applies it; a pass that wrote the evidence and "
                        "graded off it in the same breath would be marking its own work"),
                "rulings": 0,
            },
        ],
        "people": rows,
    }


# --- writing the cards ----------------------------------------------------------------

def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs. Two keys, and rule 2 is held here."""
    changed = False
    if SOURCE_ID not in (person.get("sources") or []):
        person["sources"] = (person.get("sources") or []) + [SOURCE_ID]
        changed = True
    note = (person.get("note") or "").strip()
    if MARKER not in note:
        person["note"] = (note + " " + paragraph(row)).strip()
        changed = True
    return changed


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
        print("civic voter lists: written onto %d resident record(s)" % touched)
    return touched


def build(quiet: bool = False) -> int:
    dump(LEDGER, ledger_doc())
    apply(quiet=quiet)
    if not quiet:
        print("wrote %s" % LEDGER.relative_to(ROOT))
    return 0


# --- the gate -------------------------------------------------------------------------

def gaps(rows: list) -> list:
    """Every ruling has to be ON the record it names, or the ruling is only a file."""
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
        if SOURCE_ID not in (person.get("sources") or []):
            bad.append("%s is matched to the 1833-1835 rolls and its record does not cite "
                       "'%s' — run tools/spend_civic_voter_lists.py"
                       % (row["person_id"], SOURCE_ID))
        if MARKER not in (person.get("note") or ""):
            bad.append("%s is matched to the 1833-1835 rolls and its record does not say "
                       "what they are worth — run tools/spend_civic_voter_lists.py"
                       % row["person_id"])
    return bad


def strays(rows: list) -> list:
    """And nobody the crosswalk did NOT match may carry this pass's paragraph."""
    wanted = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        for person in hh.get("persons") or []:
            if MARKER not in (person.get("note") or ""):
                continue
            if (hh.get("id"), person.get("id")) not in wanted:
                bad.append("%s carries this pass's paragraph and the crosswalk matches no "
                           "roll entry to it" % person.get("id"))
    return bad


def doubles() -> list:
    """…and a card says this pass's source ONCE, however many passes have written it.

    The third direction, and the one `gaps` and `strays` are both blind to: `gaps` asks
    whether the paragraph is PRESENT and `strays` whether an unruled card carries one, so a
    card carrying it TWICE answers both correctly. T-0677 measured that hole on
    `spend_land_sales.py` — thirty-one cards each doubled by re-running a superseded version
    of the tool, and `tools/check.sh` green over all of it. T-0846 gives this pass the same
    rule, out of `tools/spend_write_once.py` so that six passes hold one implementation.
    """
    return spend_write_once.doubles(MARKER, SUPERSEDED_MARKERS, HOUSEHOLDS)


def check(quiet: bool = False) -> int:
    faults = []
    rows = matches()
    if LEDGER.exists():
        if load(LEDGER) != ledger_doc():
            faults.append("%s no longer re-derives from voter_crosswalk.json — run "
                          "tools/spend_civic_voter_lists.py" % LEDGER.name)
    else:
        faults.append("%s is missing — run tools/spend_civic_voter_lists.py" % LEDGER.name)
    faults += gaps(rows)
    faults += strays(rows)
    faults += doubles()
    if faults:
        print("civic voter-list spend: %d fault(s)" % len(faults))
        for f in faults[:40]:
            print("   " + f)
        return 1
    if not quiet:
        print("civic voter-list spend: %d ruling(s) on %d card(s), all written, no strays, "
              "none written twice"
              % (sum(len(r["entries"]) for r in rows), len(rows)))
    return 0


def report() -> int:
    rows = matches()
    print("%-34s %-26s %s" % ("household", "person", "rolls"))
    print("-" * 96)
    for row in rows:
        print("%-34s %-26s %s" % (row["household_id"], row["person_id"],
                                  ", ".join(e["record_id"] for e in row["entries"])))
    print("-" * 96)
    print("%d ruling(s), %d person(s), %d household(s)"
          % (sum(len(r["entries"]) for r in rows), len(rows),
             len({r["household_id"] for r in rows})))
    return 0


# --- the gate's own assertions --------------------------------------------------------

def self_test() -> int:
    rows = matches()
    failures = []

    ran = []

    def want(label, cond):
        ran.append(label)
        if not cond:
            failures.append(label)

    want("a matched crosswalk row must reach a person", bool(rows))

    # 1. The applier writes TWO keys and no others — rule 2, held rather than asserted.
    row = rows[0]
    before = {"id": row["person_id"], "grade": "attested", "sex": "male",
              "sources": ["some_source"], "note": "Existing sentence.",
              "occupation": {"value": "none_recorded"}}
    after = json.loads(json.dumps(before))
    apply_to_person(after, row)
    moved = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    want("the applier moved keys other than sources and note: %s" % sorted(moved),
         moved == {"sources", "note"})
    want("the grade must be untouched", after["grade"] == before["grade"])
    want("the earlier note must survive", before["note"] in after["note"])
    want("the citation must be added, not replaced", "some_source" in after["sources"])

    # 2. And it is idempotent: a second application changes nothing.
    twice = json.loads(json.dumps(after))
    want("applying twice must change nothing", apply_to_person(twice, row) is False)

    # 3. A record that lost the citation is reported.
    stripped = json.loads(json.dumps(after))
    stripped["sources"] = ["some_source"]
    want("a missing citation must be reported",
         any(SOURCE_ID in f for f in _gaps_over(row, stripped)))

    # 4. A record that lost the paragraph is reported.
    silent = json.loads(json.dumps(after))
    silent["note"] = "Existing sentence."
    want("a missing paragraph must be reported",
         any("what they are worth" in f for f in _gaps_over(row, silent)))

    # 5. A ruling naming a household this town no longer holds is reported.
    ghost = dict(row, household_id="hh_no_such_household")
    want("a vanished household must be reported", bool(gaps([ghost])))

    # 6. The paragraph names every roll the person stands on, and its own source.
    text = paragraph(row)
    want("the paragraph must name every entry",
         all(e["record_id"] in text for e in row["entries"]))
    want("the paragraph must refuse to move a grade", "MOVES NO GRADE" in text)

    # 7. And the mint that rebuilds some of these records carries the same two constants.
    # `tools/mint_placed_residents.py` derives a person's sources and note from the
    # newspaper register, so it re-attaches this pass's citation rather than deleting it;
    # it names the id and the marker itself rather than importing them, and a drift
    # between the two copies would silently start deleting citations again.
    mint = (ROOT / "tools" / "mint_placed_residents.py").read_text(encoding="utf-8")
    want("the placed mint must carry this pass's source id",
         'CIVIC_ROLLS_SOURCE = "%s"' % SOURCE_ID in mint)
    want("the placed mint must carry this pass's marker",
         'CIVIC_ROLLS_MARKER = "%s"' % MARKER in mint)

    # THE ONCE-EACH RULE, both directions (T-0846). `gaps` and `strays` are both blind to a
    # card that carries this pass's paragraph twice — the one answers "present", the other
    # "ruled" — and an add-only applier produces exactly that when the wording changes
    # between runs. The card the applier actually writes must stay silent; the same card
    # with the paragraph appended again, and the same card carrying a superseded wording
    # beside it, must both fault.
    want("the once-each rule must stay silent on the card the applier writes",
         spend_write_once.doubles_over("hh_x", after, MARKER, SUPERSEDED_MARKERS) == [])
    doubled = json.loads(json.dumps(after))
    doubled["note"] = doubled["note"] + " " + doubled["note"]
    want("the once-each rule must fire on a card carrying this pass's paragraph twice",
         any("2 times" in d for d in spend_write_once.doubles_over(
             "hh_x", doubled, MARKER, SUPERSEDED_MARKERS)))
    rival = json.loads(json.dumps(after))
    rival["note"] = rival["note"] + " A SUPERSEDED WORDING OF THE SAME PASS. …"
    want("the once-each rule must fire on a superseded paragraph left standing",
         any("superseded" in d for d in spend_write_once.doubles_over(
             "hh_x", rival, MARKER, ("A SUPERSEDED WORDING OF THE SAME PASS.",))))
    want("this pass must declare its superseded wordings as a tuple",
         isinstance(SUPERSEDED_MARKERS, tuple))

    if failures:
        print("spend_civic_voter_lists self-test: %d assertion(s) did not fire" % len(failures))
        for f in failures:
            print("   " + f)
        return 1
    print("spend_civic_voter_lists self-test: %d assertion(s) hold" % len(ran))
    return 0


def _gaps_over(row: dict, person: dict) -> list:
    """gaps() against ONE person held in memory, so the self-test never writes a file."""
    bad = []
    if SOURCE_ID not in (person.get("sources") or []):
        bad.append("%s ... does not cite '%s'" % (row["person_id"], SOURCE_ID))
    if MARKER not in (person.get("note") or ""):
        bad.append("%s ... does not say what they are worth" % row["person_id"])
    return bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check(quiet=args.quiet)
    if args.report:
        return report()
    return build(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
