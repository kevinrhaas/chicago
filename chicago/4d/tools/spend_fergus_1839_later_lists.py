#!/usr/bin/env python3
"""Fergus 1839's two LATER lists, spent on the people they name (T-0635, consolidation pass 2).

    python3 tools/spend_fergus_1839_later_lists.py             write the ledger and the cards
    python3 tools/spend_fergus_1839_later_lists.py --check     everything re-derives; nothing drifted
    python3 tools/spend_fergus_1839_later_lists.py --report    person by person, which list meets them
    python3 tools/spend_fergus_1839_later_lists.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. T-0634 was consolidation pass 1 and spent the town's own rolls of
1833-1835. This is pass 2, and its window opens where pass 1 closed. Two crosswalks landed
in that window whose rulings name a person in this town and had never reached that person's
card:

    fergus_1839_election_crosswalk_1835.json   T-0664   86 residents matched
    fergus_1839_register_crosswalk_1835.json   T-0665   15 residents matched

Both were read out of the same volume — Fergus' Chicago Directory for 1839 — and both are
LATER evidence read backwards. The election is the poll of Chicago's first city election,
2 May 1837, printed pages 40-46. The register is the city register of 1839 and the printed
tables of mayors and sheriffs, printed pages 38-39. Neither is an 1835 fact and neither may
ever become one; what each is, is a SECOND INDEPENDENT BOOK meeting a name this project
holds, which is the thing the ratified ladder asks for and the thing 92.8% of this town's
records did not have.

WHY THE MEASURE SAID ZERO. `tools/measure_research_spend.py`'s second hop reported
directories at 0 unwritten while these 101 rulings sat unspent, and the reason is a defect
in the instrument rather than a fact about the domain: both files put their rulings one
level down, under `residents.matches`, and the hop only walked lists that were direct
values of the document. It could not see them. T-0635 repairs that descent in the same PR;
this tool is what the repaired number is then paid down with.

WHAT IS AND IS NOT WRITTEN, in four rules — pass 1's rules, unchanged, because the defect
they guard against is the same one.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED. This pass re-adjudicates nothing. It reads
     the `residents.matches` rows and writes those. `contested`, `ambiguous` and the
     surname-only refusals are rivals still standing and write nothing; the voter,
     letter-list and 1840-head pools name a row in another reading rather than a card in
     this town, and this pass does not touch them.

  2. TWO FIELDS AND NO OTHERS. A person gains the source id in `sources` and a paragraph in
     `note`. Nothing else is touched — not a grade, not an arrival, not a claim block, not
     a placement, and above all not `present_on_scene_date`. `--self-test` holds that by
     diffing a record through the applier and asserting the changed key set.

  3. NO GRADE MOVES, and here the crosswalks themselves forbid it. Each carries a
     `carry_rule` saying in its own words that a later appearance is corroboration of
     CONTINUED RESIDENCE and not of July 1835, and that the person's grade does not move on
     it alone. That sentence is quoted onto every card this pass writes, so the limit
     travels with the evidence. T-0515 applies the ladder against every source at once.

  4. ONE PARAGRAPH PER PERSON, NOT PER ENTRY. A man who voted in 1837 and held an office in
     1839 is named in one paragraph naming both, with the claim id each was read into, so
     nothing is lost by the fold.

THE LEDGER IS NOT A CROSSWALK, deliberately, and for the reason pass 1 gave:
`data/research/directories/fergus_1839_later_spend_1835.json` carries no "crosswalk" in its
name so that `measure_research_spend.py` does not read a record of WRITES as a second
adjudication and report the pass grading its own homework.
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
DIRECTORIES = ROOT / "data" / "research" / "directories"
ELECTION = DIRECTORIES / "fergus_1839_election_crosswalk_1835.json"
REGISTER = DIRECTORIES / "fergus_1839_register_crosswalk_1835.json"
LEDGER = DIRECTORIES / "fergus_1839_later_spend_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1

# The volume, and the only id written onto a card. Both crosswalks state it at the top of
# the file and both state the same one: they are two readings of one book.
SOURCE_ID = "fergus_chicago_directory_1839"

# The sentence that says a paragraph is this pass's, so re-running it is idempotent and
# `--check` can find its own work without guessing.
MARKER = "FERGUS 1839'S LATER LISTS — 1837 AND 1839 EVIDENCE, NEVER AN 1835 FACT."

# A WORDING THIS PASS HAS REPLACED — the second half of the once-each rule (T-0846). An
# applier here is add-only (`if MARKER not in note`), so rewriting the paragraph makes a
# re-run APPEND a second one saying the same thing in different words rather than overwrite
# the first, and neither `gaps` nor `strays` can see it. T-0677 measured exactly that on
# `spend_land_sales.py`: thirty-one cards doubled, `tools/check.sh` green. Any MARKER this
# pass retires belongs in this tuple from the commit that retires it, and `--check` then
# refuses a card still carrying it. Empty means this pass has never changed its wording.
SUPERSEDED_MARKERS: tuple = ()

LADDER_LIMIT = (
    "This pass WRITES THE EVIDENCE AND MOVES NO GRADE. Under the ratified ladder (T-0513) a "
    "second independent source is what lifts a projected resident, and a poll twenty-two "
    "months after the scene date — or a register four years after it — is a second source "
    "about CONTINUED RESIDENCE rather than about July 1835. T-0515 applies the ladder "
    "against every source at once; this pass hands it the evidence and not the verdict."
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- what the two files say ------------------------------------------------------------

def election_entry(e: dict) -> dict:
    """One 1837 poll line, reduced to what a card is told about it."""
    return {
        "claim_id": e["claim"],
        "list": "city_election_1837",
        "as_printed": e.get("as_printed"),
        "printed_page": e.get("printed_page"),
        "describes_date": "1837-05-02",
        "ward": e.get("ward_1837"),
        "voted_for": e.get("voted_for"),
        "office": e.get("office"),
    }


def register_entry(e: dict) -> dict:
    """One city-register or table row, reduced the same way."""
    return {
        "claim_id": e["claim"],
        "list": "city_register_1839",
        "as_printed": e.get("as_printed"),
        "printed_page": e.get("printed_page"),
        "describes_date": str(e["year"]) if e.get("year") else None,
        "ward": e.get("ward_1839"),
        "office": e.get("office") or e.get("role"),
        "body": e.get("body"),
    }


def matches() -> list:
    """One row per PERSON, folding both files' entries together.

    Order is the election crosswalk's own and then the register's, because a ledger that
    re-sorted its input would stop being a re-derivation of it. A person named by both
    keeps the position their first appearance gave them.
    """
    order: list = []
    seen: dict = {}

    def slot(row: dict) -> dict:
        key = (row["household_id"], row["person_id"])
        if key not in seen:
            seen[key] = {
                "household_id": row["household_id"],
                "person_id": row["person_id"],
                "name": row.get("name"),
                "source_id": SOURCE_ID,
                "grade_1835": row.get("grade_1835"),
                "entries": [],
                "rules": [],
            }
            order.append(seen[key])
        cell = seen[key]
        if row.get("rule") and row["rule"] not in cell["rules"]:
            cell["rules"].append(row["rule"])
        return cell

    for row in load(ELECTION)["residents"]["matches"]:
        cell = slot(row)
        for e in row.get("entries_1837") or []:
            cell["entries"].append(election_entry(e))

    for row in load(REGISTER)["residents"]["matches"]:
        cell = slot(row)
        for e in row.get("entries_1839") or []:
            cell["entries"].append(register_entry(e))

    return order


def carry_rules() -> dict:
    """Each crosswalk's OWN limit, quoted rather than paraphrased."""
    return {
        "city_election_1837": load(ELECTION)["carry_rule"],
        "city_register_1839": load(REGISTER)["carry_rule"],
    }


# --- what a card is told ---------------------------------------------------------------

def _cite(e: dict) -> str:
    where = "printed page %s" % e["printed_page"] if e.get("printed_page") else "unpaged"
    if e["list"] == "city_election_1837":
        ward = ", ward %s" % e["ward"] if e.get("ward") else ""
        voted = ", voting for %s" % e["voted_for"] if e.get("voted_for") else ""
        return ("the poll of Chicago's first city election, 2 May 1837 — “%s” (%s, %s%s%s)"
                % (e["as_printed"], e["claim_id"], where, ward, voted))
    office = (e.get("office") or "an office").replace("_", " ")
    year = ", %s" % e["describes_date"] if e.get("describes_date") else ""
    return ("the city register of 1839 — “%s” as %s%s (%s, %s)"
            % (e["as_printed"], office, year, e["claim_id"], where))


def paragraph(row: dict) -> str:
    """What one person's card is told, and the whole of it."""
    cites = "; ".join(_cite(e) for e in row["entries"])
    lists = [e["list"] for e in row["entries"]]
    limits = carry_rules()
    limit = " ".join(limits[k] for k in ("city_election_1837", "city_register_1839")
                     if k in lists)
    rule = row["rules"][0] if row["rules"] else "stated in the crosswalk"
    n = len(row["entries"])
    return (
        "%s Fergus' Chicago Directory for 1839 names this person %d time%s in its two later "
        "lists: %s. %s Identity by the crosswalk's own rule: %s "
        "(data/research/directories/fergus_1839_election_crosswalk_1835.json and "
        "fergus_1839_register_crosswalk_1835.json). %s"
        % (MARKER, n, "" if n == 1 else "s", cites, limit, rule, LADDER_LIMIT))


# --- the ledger ------------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = matches()
    per_list: dict = {}
    for row in rows:
        for e in row["entries"]:
            per_list[e["list"]] = per_list.get(e["list"], 0) + 1
    election = load(ELECTION)
    register = load(REGISTER)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by tools/spend_fergus_1839_later_lists.py. The ledger of T-0635's "
            "consolidation pass 2: which of the two Fergus 1839 later-list crosswalks' "
            "resident matches were written onto the card they name, and what each card was "
            "told. It is a record of WRITES, not of adjudications — the adjudications are "
            "the two crosswalks — and it deliberately carries no 'crosswalk' in its name so "
            "that measure_research_spend.py does not count a write as a second ruling."),
        "generated_by": "tools/spend_fergus_1839_later_lists.py",
        "ticket": "T-0635",
        "pass": "consolidation pass 2",
        "source_id": SOURCE_ID,
        "reads": [
            "data/research/directories/fergus_1839_election_crosswalk_1835.json",
            "data/research/directories/fergus_1839_register_crosswalk_1835.json",
        ],
        "writes": "data/residents/households/*.json — persons[].sources and persons[].note",
        "carry_rules": carry_rules(),
        "counts": {
            "matched_rulings": (len(election["residents"]["matches"])
                                + len(register["residents"]["matches"])),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "entries_carried": sum(len(r["entries"]) for r in rows),
            "per_list": per_list,
            "named_by_both_lists": sum(
                1 for r in rows if len({e["list"] for e in r["entries"]}) > 1),
        },
        "not_written": [
            {
                "rule": "F1",
                "why": ("a `contested` or `ambiguous` row is a rival still standing: the "
                        "crosswalk did not choose between the bearers of the name, and a "
                        "card that cited the volume anyway would print an undecided "
                        "identity as a decided one"),
                "rulings": (election["counts"]["residents_ambiguous"]
                            + election["counts"]["residents_contested"]
                            + register["counts"]["residents_ambiguous"]
                            + register["counts"]["residents_contested"]),
            },
            {
                "rule": "F2",
                "why": ("a surname-only agreement is a refusal in both crosswalks and in "
                        "the newspapers' ratified rules, and refusals are not spent"),
                "rulings": (election["counts"]["residents_surname_only_refused"]
                            + register["counts"]["residents_surname_only_refused"]),
            },
            {
                "rule": "F3",
                "why": ("the voter, letter-list and 1840-head pools match a row in ANOTHER "
                        "reading rather than a person this town holds a card for. They are "
                        "corroboration between readings and there is no card to write them "
                        "onto; T-0515 is the pass that rules on the letter list"),
                "rulings": (election["counts"]["voters_matched_one_entry"]
                            + election["counts"]["letter_list_matched_one_entry"]
                            + election["counts"]["heads_1840_matched_one_entry"]
                            + register["counts"]["voters_matched_one_entry"]
                            + register["counts"]["letter_list_matched_one_entry"]
                            + register["counts"]["heads_1840_matched_one_entry"]),
            },
            {
                "rule": "F4",
                "why": ("no grade moves here. The ratified ladder reads every source at "
                        "once and T-0515 applies it; a pass that wrote the evidence and "
                        "graded off it in the same breath would be marking its own work"),
                "rulings": 0,
            },
        ],
        "people": [
            {
                "household_id": r["household_id"],
                "person_id": r["person_id"],
                "name": r["name"],
                "source_id": r["source_id"],
                "grade_1835": r["grade_1835"],
                "rules": r["rules"],
                "entries": r["entries"],
                "written": paragraph(r),
            }
            for r in rows
        ],
    }


# --- the write -------------------------------------------------------------------------

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


def retract_from_person(person: dict) -> bool:
    """A RULING WITHDRAWN MUST BE UNWRITTEN (T-0987 stretch 8).

    The applier above is add-only, and `strays()` below has always REFUSED a card
    that carries this pass's paragraph with no ruling behind it — but nothing could
    ever clear one, so the gate could only report the state and never leave it. It
    was reached the first time when T-0987 stretch 8 stopped the crosswalks reading
    a RANK as a forename: `Morgan Shapley` of the 1837 poll had been reaching
    `Major L Shapley` on the M of Major, and when the M went, the ruling went with
    it and the paragraph on his card stayed.

    This undoes exactly what `apply_to_person` does and nothing else — the
    paragraph, which runs from the marker to the end of the ladder limit, and the
    source id, which no longer has a sentence behind it. Every other pass that
    writes this volume is add-only too and puts its own citation back on the next
    rebuild, so removing it here cannot lose one that is still earned."""
    changed = False
    note = person.get("note") or ""
    i = note.find(MARKER)
    if i >= 0:
        j = note.find(LADDER_LIMIT, i)
        j = (j + len(LADDER_LIMIT)) if j >= 0 else len(note)
        person["note"] = (note[:i] + " " + note[j:]).replace("  ", " ").strip()
        changed = True
    if changed and SOURCE_ID not in (person.get("note") or "") \
            and SOURCE_ID in (person.get("sources") or []):
        person["sources"] = [s for s in person["sources"] if s != SOURCE_ID]
    return changed


def apply(quiet: bool = False) -> int:
    touched = 0
    rows = matches()
    for row in rows:
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        if not path.exists():
            continue
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, hh)
    ruled = {(r["household_id"], r["person_id"]) for r in rows}
    withdrawn = 0
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        dirty = False
        for person in hh.get("persons") or []:
            if MARKER not in (person.get("note") or ""):
                continue
            if (hh.get("id"), person.get("id")) in ruled:
                continue
            if retract_from_person(person):
                withdrawn += 1
                dirty = True
        if dirty:
            dump(path, hh)
    if not quiet:
        print("fergus 1839 later lists: written onto %d resident record(s)%s"
              % (touched, ", withdrawn from %d" % withdrawn if withdrawn else ""))
    return touched


def build(quiet: bool = False) -> int:
    dump(LEDGER, ledger_doc())
    apply(quiet=quiet)
    if not quiet:
        print("wrote %s" % LEDGER.relative_to(ROOT))
    return 0


# --- the gate --------------------------------------------------------------------------

def _person(row: dict):
    path = HOUSEHOLDS / ("%s.json" % row["household_id"])
    if not path.exists():
        return None
    for person in load(path).get("persons") or []:
        if person.get("id") == row["person_id"]:
            return person
    return None


def gaps(rows: list) -> list:
    """Every ruling has to be ON the record it names, or the ruling is only a file."""
    bad = []
    for row in rows:
        person = _person(row)
        if person is None:
            bad.append("%s/%s — the record the ruling names does not exist"
                       % (row["household_id"], row["person_id"]))
            continue
        if SOURCE_ID not in (person.get("sources") or []):
            bad.append("%s/%s — matched by the crosswalk and the card does not cite %s"
                       % (row["household_id"], row["person_id"], SOURCE_ID))
        if MARKER not in (person.get("note") or ""):
            bad.append("%s/%s — matched by the crosswalk and the card carries no paragraph"
                       % (row["household_id"], row["person_id"]))
    return bad


def strays(rows: list) -> list:
    """…and a card may not carry this pass's paragraph without a ruling behind it."""
    ruled = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        for person in hh.get("persons") or []:
            if MARKER not in (person.get("note") or ""):
                continue
            if (hh.get("id"), person.get("id")) not in ruled:
                bad.append("%s/%s — carries this pass's paragraph and no crosswalk match "
                           "names them" % (hh.get("id"), person.get("id")))
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
    rows = matches()
    if not LEDGER.exists():
        print("   the ledger is missing: %s" % LEDGER.relative_to(ROOT))
        return 1
    if load(LEDGER) != ledger_doc():
        print("   %s no longer re-derives from the two crosswalks — re-run the tool"
              % LEDGER.relative_to(ROOT))
        return 1
    bad = gaps(rows) + strays(rows) + doubles()
    if bad:
        for line in bad[:20]:
            print("   %s" % line)
        if len(bad) > 20:
            print("   …and %d more" % (len(bad) - 20))
        return 1
    if not quiet:
        print("fergus 1839 later lists: %d ruling(s) on %d card(s), no strays, none "
              "written twice"
              % (sum(len(r["entries"]) for r in rows), len(rows)))
    return 0


def report() -> int:
    rows = matches()
    print("%-34s %-28s %s" % ("household", "person", "entries"))
    print("-" * 78)
    for r in rows:
        lists = ",".join(sorted({e["list"] for e in r["entries"]}))
        print("%-34s %-28s %d  %s" % (r["household_id"], r["person_id"],
                                      len(r["entries"]), lists))
    print("-" * 78)
    print("%d people, %d entries" % (len(rows), sum(len(r["entries"]) for r in rows)))
    return 0


def self_test() -> int:
    fails = []

    def want(label, cond):
        if not cond:
            fails.append(label)

    rows = matches()
    want("the two crosswalks must name at least one person", bool(rows))
    want("every row must name a household and a person",
         all(r["household_id"] and r["person_id"] for r in rows))
    want("every entry must name the claim it was read into",
         all(e["claim_id"] for r in rows for e in r["entries"]))
    want("every paragraph must carry the marker and the source id",
         all(MARKER in paragraph(r) for r in rows))

    # Rule 2, held over a synthetic record: two keys move and no others.
    before = {"id": "x", "name": "X", "grade": "projected_resident",
              "sources": ["some_source"], "note": "Existing sentence.",
              "occupation": {"value": "cooper", "confidence": "inferred"}}
    after = json.loads(json.dumps(before))
    apply_to_person(after, rows[0])
    moved = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    want("the applier moved keys other than sources and note: %s" % sorted(moved),
         moved == {"sources", "note"})
    want("the grade must not move", after["grade"] == before["grade"])
    want("the earlier note must survive", before["note"] in after["note"])
    want("the citation must be added, not replaced", "some_source" in after["sources"])

    # …and it must be idempotent: a second application changes nothing.
    twice = json.loads(json.dumps(after))
    apply_to_person(twice, rows[0])
    want("a second application must change nothing", twice == after)

    # The gate must FIRE when its two failures are staged.
    stripped = json.loads(json.dumps(after))
    stripped["sources"] = ["some_source"]
    want("gaps must fire on a card that stopped citing the source",
         any("does not cite" in g for g in _gaps_over(rows[0], stripped)))
    silent = json.loads(json.dumps(after))
    silent["note"] = "Existing sentence."
    want("gaps must fire on a card that carries no paragraph",
         any("no paragraph" in g for g in _gaps_over(rows[0], silent)))

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

    # THE WITHDRAWAL (T-0987 stretch 8). A card whose ruling has gone must be put back to
    # the state it was in before this pass ever wrote on it — the sentence that stood
    # before survives, the paragraph goes, the citation goes with it, and running the
    # retraction twice takes nothing further. Held over the card the applier just wrote.
    undone = json.loads(json.dumps(after))
    want("the withdrawal must strip this pass's paragraph",
         retract_from_person(undone) and MARKER not in (undone.get("note") or ""))
    want("…and leave the sentence that stood before it",
         undone["note"] == "Existing sentence.")
    want("…and drop the citation it put there",
         SOURCE_ID not in (undone.get("sources") or []))
    want("…and do nothing at all on a second pass", not retract_from_person(undone))
    kept = json.loads(json.dumps(after))
    kept["note"] = kept["note"] + " Another pass cites %s too." % SOURCE_ID
    retract_from_person(kept)
    want("…and keep a citation another pass's sentence still earns",
         SOURCE_ID in (kept.get("sources") or []))

    for line in fails:
        print("   %s" % line)
    print("fergus 1839 later lists self-test: %s" % ("FAILED" if fails else "ok"))
    return 1 if fails else 0


def _gaps_over(row: dict, person: dict) -> list:
    """gaps() for one already-loaded person — what the self-test needs and the gate reuses."""
    out = []
    if SOURCE_ID not in (person.get("sources") or []):
        out.append("%s/%s — does not cite %s" % (row["household_id"], row["person_id"],
                                                 SOURCE_ID))
    if MARKER not in (person.get("note") or ""):
        out.append("%s/%s — no paragraph" % (row["household_id"], row["person_id"]))
    return out


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
