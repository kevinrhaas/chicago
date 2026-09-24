#!/usr/bin/env python3
"""The town's press, written onto the cards the register already joins it to (T-1343).

    python3 tools/spend_press_bounds.py             write the ledger and the bounds
    python3 tools/spend_press_bounds.py --check     everything re-derives; nothing drifted
    python3 tools/spend_press_bounds.py --report    person by person, what each claim bounds
    python3 tools/spend_press_bounds.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. T-1329 held four corpora of dated appearances and T-1337 spent two of
them — the 1830 Peoria & Putnam schedule and St Mary's register — as
`persons[].appearance_bounds[]`. The press could not follow, and not for want of an
identification: a newspaper claim's ledger id was its bare `c004`, which 55 held issues
each print, so a bound naming one would have closed 937 other units of this corpus as
`asserted`. T-1342 repaired that — a press claim's ledger key is now the issue file's stem
and the claim id joined by `#` — and this pass is the spend it unblocked.

THE IDENTIFICATION IS NOT MADE HERE. `data/research/newspapers/register_1835.json` is the
committed newspapers-to-residents crosswalk and has been since T-0648: one row per person
the press names, carrying `action` and `action_target`, where `enrich` means THIS PRINTED
NAME IS A PERSON THE RESIDENTS LAYER ALREADY HOLDS and names the card by its person id
rather than by its display string. `tools/compile_register.py --build` derives it from
`gazetteer.json` and the committed town, and `tools/check.sh` refuses a committed copy a
rebuild would not produce. This pass reads that adjudication and never re-makes it: where
the register says `new_resident` or `replace_invented` no card is touched and the unit is
REFUSED BY NAME in `tools/spend_remainder_rulings.py`, with what would reopen it.

WHAT IT WRITES. One row per (person, claim) pair, into `persons[].dated_bounds[]` through
`tools/dated_bounds_block.py` — the block T-1326 introduced and T-1332 gave a second owner,
rather than a third shape for a dated appearance. The two publications are two owners of
that block, one per source id, so the rows of the Democrat and of the American each replace
their own group and nobody else's.

THE FOUR RULES THAT KEEP A ROW FROM SAYING MORE THAN IT CAN.

  1. A NAME IN PRINT IS NOT A BODY IN THE TOWN, so every row carries `here_by: null`. This
     is the standing ruling of `a_dated_appearance_bounds_a_presence` held in a field
     instead of in prose: the paper was printed at Chicago and the claim is dated, and
     neither of those says the person stood in the town that day. A notice can be signed
     three hundred miles off and reprinted here — `chicago_american_1835_06_27#c001` is
     exactly that, a State Bank list out of the Sangamon Journal whose square and court
     house are Springfield's. The row bounds an APPEARANCE IN THE TOWN'S PRINT on a dated
     day, which is what the reading says, and the arrival pass works from the earliest of
     them.

  2. NO ROW IS `attested`. The page is documented — the issue is deposited, dated and
     numbered in `corpus.json` — and the IDENTITY is a name agreement the register
     declared. A bound whose subject is inferred is an inferred bound, exactly as T-1337
     ruled for the schedule and the register.

  3. NO ROW COVERS THE SCENE DATE. Under the evidence ladder ratified 2026-09-03 a source
     EARLIER than the scene date corroborates and dates and never promotes, and a LATER one
     does not promote either.

  4. A ROW CITES ITS CROSSWALK RULE AND DOES NOT TRANSCRIBE IT, which is T-1337's rule 4
     and was measured again here. The register's `action_note` names the resident CARD BY
     ID — "data/residents/ already holds this person as mather_thomas" — and a residents
     cohort unit's ledger key is that same bare id. Transcribed onto a card, eleven of
     those notes closed eleven resident-research units as `asserted` off a press bound that
     says nothing about them, which is the defect `TOKEN_BLIND_KEYS` was written for in the
     other direction. So a row names the register, the gazetteer person and the action, and
     the reason stays in the file that authored it.

NO GRADE MOVES, NO IDENTITY REOPENS, NO PERSON IS MINTED, AND NO OTHER KEY IS TOUCHED.
`--self-test` diffs a record through the applier and asserts the changed key set is
`{"dated_bounds"}` alone.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dated_bounds_block as B  # noqa: E402
import research_spend_ledger as L  # noqa: E402
import spend_remainder_rulings as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
REGISTRY = RESEARCH / "domains.json"
REGISTER = RESEARCH / "newspapers" / "register_1835.json"
GAZETTEER = RESEARCH / "newspapers" / "gazetteer.json"
CORPUS = RESEARCH / "newspapers" / "corpus.json"
HAND_AUTHORED = RESEARCH / "spend_rulings.json"
LEDGER = RESEARCH / "press_bounds_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1
TICKET = "T-1343"
GENERATOR = "tools/spend_press_bounds.py"
SCENE_DATE = "1835-07-01"
CONFIDENCE = "inferred"
BOUND_KIND = "print_appearance"

# `tools/spend_remainder_rulings.py` OWNS THE TEST for what a dated press appearance is,
# and this pass asks it rather than repeating it. Two tools splitting one corpus between
# them can only stay agreed if one of them decides where the line falls.
REMAINDER_TICKET = R.TICKET

# The register actions, and what each one leaves this pass able to do. A new action is a
# SystemExit and not a guess.
ACTIONS = {
    "enrich": "spend",
    "new_resident": "refuse",
    "replace_invented": "refuse",
}

LADDER = (
    "Under the evidence ladder ratified 2026-09-03 a source EARLIER than the scene date "
    "corroborates and dates and never promotes, and a source LATER than it does not "
    "promote either.")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- the corpus -----------------------------------------------------------------------

def corpus_units(root: Path = ROOT) -> list[dict]:
    """The press units of T-1343, derived from the readings and NOT from the ledger.

    `natural_disposition` is asked with an EMPTY target index on purpose. Its assertion
    test is "a source-bearing structured field on a card names this unit", which is exactly
    what this pass goes on to write — so asking it against the live cards would make the
    corpus shrink to nothing the moment the pass had run, and `--check` would re-derive a
    different question from the one it answered. With no targets offered, no unit can close
    as `asserted` and the derivation is fixed by the readings alone, before and after.
    """
    units, faults = L.extract_units(root, load(REGISTRY))
    if faults:
        raise SystemExit("the reading registry is faulted: " + "; ".join(faults[:5]))
    already = {row["unit"] for row in load(HAND_AUTHORED).get("rulings") or []}
    docs: dict = {}
    out = []
    for unit in units:
        if unit["domain"] != "newspapers" or unit["unit_id"] in already:
            continue
        natural = L.natural_disposition(root, unit, {})
        if natural.get("disposition") != "unresolved":
            continue
        if natural.get("ticket") != REMAINDER_TICKET:
            continue
        doc = docs.setdefault(unit["source_file"], load(root / unit["source_file"]))
        if R.is_dated_press_appearance(unit, R.issue_date(doc)):
            out.append(unit)
    return out


# --- who the press names, and which card the register joins it to ---------------------

def residents_by_person_id() -> dict:
    """Resident person id -> (household id, name). The id is the register's own join key."""
    found: dict = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        household = load(path)
        for person in household.get("persons") or []:
            found.setdefault(str(person.get("id")), []).append(
                (household["id"], str(person.get("name") or "")))
    return found


def register_rows() -> dict:
    """Gazetteer person id -> its register row, every action checked against ACTIONS."""
    rows = {}
    for row in load(REGISTER)["persons"]:
        action = row.get("action")
        if action not in ACTIONS:
            raise SystemExit(
                "%s carries register action %r, which this pass has no rule for. Rule it "
                "in ACTIONS rather than mapping it onto the nearest one." % (row["id"], action))
        rows[row["id"]] = row
    return rows


def gazetteer_rows() -> dict:
    return {row["id"]: row for row in load(GAZETTEER)["persons"]}


def publications() -> dict:
    """Issue id -> (publication title, source id, issue date), off the committed corpus."""
    doc = load(CORPUS)
    titles = {key: value["title"] for key, value in doc["publications"].items()}
    return {issue["id"]: (titles[issue["publication"]], issue["source_id"], issue["date"])
            for issue in doc["issues"]}


def printed_as(gazetteer_row: dict, record_key: str) -> str:
    """How this claim printed this person's name — the gazetteer's own variant row."""
    for variant in gazetteer_row.get("variants") or []:
        if variant.get("claim") == record_key:
            return str(variant.get("as_printed") or "")
    return str(gazetteer_row.get("name") or "")


def role_in(record: dict, as_printed: str, normalized: str) -> str | None:
    """The claim's own `entities[].role` for this person, or None where it states none."""
    for entity in record.get("entities") or []:
        if not isinstance(entity, dict):
            continue
        if entity.get("as_printed") == as_printed or entity.get("normalized") == normalized:
            role = str(entity.get("role") or "").strip()
            return role or None
    return None


def locator_of(record: dict) -> str:
    locator = record.get("locator") or {}
    page, column = locator.get("issue_page"), locator.get("column")
    if page is None and column is None:
        return "claim %s, no page or column in the reading's locator" % record.get("id")
    return "page %s column %s" % (page, column)


# --- the rows ---------------------------------------------------------------------------

def rows(root: Path = ROOT) -> tuple[list, list]:
    """(bounds written, identifications refused) — every corpus unit, positive and negative.

    A unit reaches BOTH lists where it names two people and the register enriches one of
    them: the refusal is about the identification, not about the unit.
    """
    register, gazetteer, issues = register_rows(), gazetteer_rows(), publications()
    residents = residents_by_person_id()
    mentions: dict = {}
    for person_id, row in gazetteer.items():
        for claim in row.get("mentions") or []:
            mentions.setdefault(claim, []).append(person_id)
    docs: dict = {}
    written, refused = [], []
    for unit in corpus_units(root):
        key = unit["record_key"]
        record = unit["record"]
        docs.setdefault(unit["source_file"], None)
        issue_id = key.split("#", 1)[0]
        title, source_id, printed = issues[issue_id]
        for person_id in sorted(mentions.get(key) or []):
            gaz = gazetteer[person_id]
            reg = register[person_id]
            as_printed = printed_as(gaz, key)
            normalized = str(gaz.get("name") or "")
            if ACTIONS[reg["action"]] == "refuse":
                refused.append({"unit": unit["unit_id"], "record_key": key,
                                "gazetteer_person": person_id, "as_printed": as_printed,
                                "register_action": reg["action"],
                                "register_note": reg.get("action_note")})
                continue
            target = str(reg.get("action_target") or "")
            held = residents.get(target) or []
            if len(held) != 1:
                raise SystemExit(
                    "%s: the register enriches %r onto resident person %r and the layer "
                    "holds %d of them. This pass makes no identification of its own."
                    % (key, person_id, target, len(held)))
            household, card_name = held[0]
            role = role_in(record, as_printed, normalized)
            side = "earlier" if printed <= SCENE_DATE else "later"
            written.append({
                "household_id": household,
                "person_id": target,
                "source_id": source_id,
                "bound": {
                    "bound_kind": BOUND_KIND,
                    "corpus": "chicago_press_1833_1835",
                    "publication": title,
                    "record_id": key,
                    "claim_kind": record.get("kind"),
                    "as_printed": as_printed,
                    "role": role,
                    "locator": "%s %s" % (issue_id, locator_of(record)),
                    "describes_date": printed,
                    "date_confidence": "documented",
                    "precision": "day",
                    "reaches": printed,
                    "here_by": None,
                    "side_of_scene_date": side,
                    "covers_scene_date": False,
                    "confidence": CONFIDENCE,
                    "sources": [source_id],
                    "identity_rule": (
                        "data/research/newspapers/register_1835.json — persons[] %s, "
                        "action `enrich` onto this card. The register states its own "
                        "reason there and this row cites it rather than transcribing it."
                        % person_id),
                    "note": (
                        "AN APPEARANCE IN THE TOWN'S PRINT, AND NOTHING FURTHER. %s of %s "
                        "names %r in the claim read as %s, so the reading dates an "
                        "appearance of this person in the town's press and `here_by` is "
                        "null: a name in print is not a body in the town, and a notice can "
                        "be signed elsewhere and reprinted here. %s THE IDENTITY IS "
                        "INFERRED AND THE PAGE IS NOT: the issue is deposited, dated and "
                        "numbered in data/research/newspapers/corpus.json, and what no "
                        "source states is that the name the paper prints is the person on "
                        "this card — the register joins them under its own written note. "
                        "No grade moves here and the identity is neither reopened nor "
                        "hardened."
                        % (title, printed, " ".join(as_printed.split()), key, LADDER)),
                },
            })
    return written, refused


def people(root: Path = ROOT) -> list:
    """One row per person, carrying that person's bounds in issue order then claim order."""
    written, _ = rows(root)
    order: list = []
    seen: dict = {}
    for row in sorted(written, key=lambda r: (r["person_id"], r["bound"]["describes_date"],
                                              r["bound"]["record_id"])):
        key = row["person_id"]
        if key not in seen:
            seen[key] = {"household_id": row["household_id"], "person_id": key, "bounds": []}
            order.append(seen[key])
        seen[key]["bounds"].append(row["bound"])
    return sorted(order, key=lambda r: (r["household_id"], r["person_id"]))


# --- the ledger -------------------------------------------------------------------------

def ledger_doc(root: Path = ROOT) -> dict:
    written, refused = rows(root)
    units = corpus_units(root)
    spent = {row["bound"]["record_id"] for row in written}
    per_side: dict = {}
    per_kind: dict = {}
    per_source: dict = {}
    for row in written:
        bound = row["bound"]
        per_side[bound["side_of_scene_date"]] = per_side.get(bound["side_of_scene_date"], 0) + 1
        per_kind[bound["claim_kind"]] = per_kind.get(bound["claim_kind"], 0) + 1
        per_source[bound["sources"][0]] = per_source.get(bound["sources"][0], 0) + 1
    per_action: dict = {}
    for row in refused:
        per_action[row["register_action"]] = per_action.get(row["register_action"], 0) + 1
    by_person = people(root)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by " + GENERATOR + ". The ledger of " + TICKET + ": every press "
            "claim of the Democrat and the American whose person the committed register "
            "ALREADY joins to a card, written onto that person as a structured bound the "
            "research-spend ledger can see. It records WRITES and not adjudications — the "
            "adjudication is register_1835.json's `action`/`action_target`, derived from "
            "the gazetteer by tools/compile_register.py — and this file carries no "
            "'crosswalk' in its name so that measure_research_spend.py cannot read a write "
            "as a second ruling. Nothing here is a residence or a presence: a name in the "
            "town's print is an appearance on a dated day and `here_by` is null on every "
            "row. Where the register says the printed name is a person this layer does NOT "
            "hold, or one that replaces an invented card, the answer is a written refusal "
            "in tools/spend_remainder_rulings.py and no card is touched."),
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "source_ids": sorted(per_source),
        "reads": [
            "data/research/newspapers/register_1835.json — persons[] `enrich`",
            "data/research/newspapers/gazetteer.json — persons[].mentions[] and variants[]",
            "data/research/newspapers/corpus.json — the issue date, title and source id",
        ],
        "writes": "data/residents/households/*.json — persons[].%s[]" % B.BLOCK,
        "counts": {
            "corpus_units": len(units),
            "units_spent": len(spent),
            "units_with_no_identification": len(units) - len(spent),
            "bounds_written": len(written),
            "people_written": len(by_person),
            "households_touched": len({r["household_id"] for r in by_person}),
            "identifications_refused": len(refused),
            "grades_changed": 0,
            "identities_changed": 0,
            "persons_minted": 0,
            "per_side_of_scene_date": per_side,
            "per_claim_kind": per_kind,
            "per_source": per_source,
            "refused_per_register_action": per_action,
        },
        "refusals": [
            {
                "rule": "P1",
                "why": ("every row carries `here_by: null`. The paper was printed at "
                        "Chicago and the claim is dated, and neither of those says the "
                        "person stood in the town that day"),
                "rows": len(written),
            },
            {
                "rule": "P2",
                "why": ("no row reaches `attested`. The issue is documented and the "
                        "identity is a name agreement the register declared, so the bound "
                        "is inferred however documented the page under it is"),
                "rows": len(written),
            },
            {
                "rule": "P3",
                "why": ("no row covers the scene date. An earlier source corroborates and "
                        "dates and never promotes, and a later one does not promote either"),
                "rows": len(written),
            },
            {
                "rule": "P4",
                "why": ("no card is touched where the register's action is not `enrich`. "
                        "A `new_resident` row says the printed name is a person this layer "
                        "does not hold and a `replace_invented` row names a card the "
                        "register has marked for substitution; both are refused by name in "
                        "tools/spend_remainder_rulings.py, with what would reopen them"),
                "rows": len(refused),
            },
        ],
        "people": by_person,
    }


# --- writing the cards --------------------------------------------------------------------

def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs: its own groups of one shared block."""
    changed = False
    for source_id in PRESS_SOURCES:
        # ONLY this pass's OWN groups. `dated_bounds_block.merge` replaces the group it is
        # given, so writing an empty list for a source this pass does not own would delete
        # the voter or land register's rows off the card — measured, by the self-test
        # below, before this loop was cut down from every owner to these two.
        mine = [bound for bound in row["bounds"] if bound["sources"] == [source_id]]
        if not mine and not B.mine(person, source_id):
            continue
        if B.write(person, source_id, mine):
            changed = True
    return changed


def retract(wanted: set, quiet: bool = False) -> int:
    """And take the bound OFF a card the register has stopped enriching (T-1440).

    `apply` visits the cards the register names and no others, so a card that LEAVES
    that set was never visited again and kept the bound it had been given. `strays`
    has always caught it — "carries a press bound and the committed register enriches
    no press person onto it" — and there was no build step the message could send you
    to: the generator could write a bound and not retract one, so the gate named a
    fault the tool it names could not repair.

    It happens whenever a printed name is re-matched. T-1440 moved fifty-four of them,
    and `hogan_john` and `wright_j` — two cards that had been holding another man's
    notices — were left carrying press appearances the register no longer puts on them.

    Only this pass's own groups are cleared, for the reason `apply_to_person` states:
    the block is shared, and writing an empty list for a source this pass does not own
    would delete the voter and land registers' rows off the card.
    """
    dropped = 0
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        household = load(path)
        changed = False
        for person in household.get("persons") or []:
            if person.get("id") in wanted:
                continue
            for source_id in PRESS_SOURCES:
                if B.mine(person, source_id) and B.write(person, source_id, []):
                    changed = True
            # AND THE EMPTIED BLOCK GOES WITH THEM. `dated_bounds: []` is a key no
            # renderer reads and `measure_layer_reads.py --gate` refuses one, rightly:
            # a figure shipped to a browser that nothing builds is dead weight. A card
            # that has given back every bound it held is a card that never had one.
            if B.BLOCK in person and not person[B.BLOCK]:
                del person[B.BLOCK]
                changed = True
        if changed:
            dropped += 1
            dump(path, household)
    if not quiet and dropped:
        print("press bounds: retracted from %d resident record(s) the register no "
              "longer enriches" % dropped)
    return dropped


def apply(quiet: bool = False) -> int:
    touched = 0
    rows = people()
    for row in rows:
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        household = load(path)
        for person in household.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, household)
    retract({row["person_id"] for row in rows}, quiet=quiet)
    if not quiet:
        print("press bounds: written onto %d resident record(s)" % touched)
    return touched


def build(quiet: bool = False) -> int:
    dump(LEDGER, ledger_doc())
    apply(quiet=quiet)
    if not quiet:
        print("wrote %s" % LEDGER.relative_to(ROOT))
    return 0


# --- the gate ------------------------------------------------------------------------------

def gaps(by_person: list) -> list:
    """Every bound has to be ON the record it names, and byte-for-byte what derives."""
    bad = []
    for row in by_person:
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
        for source_id in PRESS_SOURCES:
            want = [b for b in row["bounds"] if b["sources"] == [source_id]]
            if B.mine(person, source_id) != want:
                bad.append("%s is named by %d press claim(s) of %s and its %s does not "
                           "re-derive — run %s"
                           % (row["person_id"], len(want), source_id, B.BLOCK, GENERATOR))
    return bad


def strays(by_person: list) -> list:
    """And nobody the register did NOT enrich may carry a press bound."""
    wanted = {row["person_id"] for row in by_person}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        household = load(path)
        for person in household.get("persons") or []:
            carries = any(B.mine(person, source_id) for source_id in PRESS_SOURCES)
            if carries and person.get("id") not in wanted:
                bad.append("%s carries a press bound and the committed register enriches "
                           "no press person onto it" % person.get("id"))
    return bad


def ledger_drift() -> list:
    return ([] if LEDGER.exists() and load(LEDGER) == ledger_doc()
            else ["%s does not re-derive — run %s"
                  % (LEDGER.relative_to(ROOT), GENERATOR)])


PRESS_SOURCES = ("chicago_democrat_1833_1835", "chicago_american_1835")


def check(quiet: bool = False) -> int:
    by_person = people()
    faults = gaps(by_person) + strays(by_person) + ledger_drift()
    for source_id in PRESS_SOURCES:
        if source_id not in dict(B.OWNERS):
            faults.append(
                "tools/dated_bounds_block.py does not name %s as an owned source, so a "
                "press row reads as unclaimed and both passes drift" % source_id)
    if faults:
        for fault in faults:
            print("FAIL: %s" % fault)
        return 1
    if not quiet:
        print("OK: %d press bound(s) on %d resident record(s), and nothing else carries one"
              % (sum(len(r["bounds"]) for r in by_person), len(by_person)))
    return 0


def report() -> int:
    for row in people():
        print("%s (%s)" % (row["person_id"], row["household_id"]))
        for bound in row["bounds"]:
            print("   %s  %-9s %-28s %s" % (bound["describes_date"], bound["claim_kind"],
                                            bound["as_printed"], bound["record_id"]))
    return 0


def self_test() -> int:
    ran, failures = [], []

    def ok(label, cond):
        ran.append(label)
        if not cond:
            failures.append(label)
        print("  %s %s" % ("ok:  " if cond else "FAIL:", label))

    by_person = people()
    bounds = [b for row in by_person for b in row["bounds"]]
    written, refused = rows()
    units = corpus_units()

    ok("the corpus is the press units of the remainder register's own test and no others",
       bool(units) and all(u["domain"] == "newspapers" for u in units)
       and all(R.is_dated_press_appearance(u, u["record_key"].split("#")[0][-10:].replace("_", "-"))
               for u in units))
    ok("the corpus does not move once the bounds are on the cards",
       {u["record_key"] for u in units} == {u["record_key"] for u in corpus_units()})
    ok("every derived bound is inferred and none is attested",
       bool(bounds) and {b["confidence"] for b in bounds} == {CONFIDENCE})
    ok("no row puts a body in the town", all(b["here_by"] is None for b in bounds))
    ok("no derived bound covers the scene date",
       not any(b["covers_scene_date"] for b in bounds))
    ok("every bound reaches its own issue day and no further",
       all(b["reaches"] == b["describes_date"] and b["precision"] == "day" for b in bounds))
    ok("a bound later than the scene date says so",
       all((b["side_of_scene_date"] == "later") == (b["describes_date"] > SCENE_DATE)
           for b in bounds))
    ok("every bound names one committed publication and only it",
       all(len(b["sources"]) == 1 and b["sources"][0] in PRESS_SOURCES for b in bounds))
    ok("every bound states the identity rule it rests on",
       all(len(str(b["identity_rule"] or "")) > 60 for b in bounds))
    ok("a bound cites the register and does not transcribe the claim",
       all("register_1835.json" in b["identity_rule"] and
           str(b["identity_rule"]).count("action `enrich`") == 1 for b in bounds))
    ok("every bound names its unit by the file-qualified key T-1342 made nameable",
       all("#" in b["record_id"] and b["record_id"].split("#")[0] for b in bounds))
    # The test is the LEDGER'S OWN tokenisation and not a substring search: a gazetteer id
    # such as `person_boardman_harry` contains a card id and names nothing, because
    # `research_spend_ledger.UNIT_TOKEN` reads it as one token. What must not appear is the
    # bare id, which is what a residents cohort unit's key is.
    cards = {row["person_id"] for row in by_person}
    printed_ids = {token for b in bounds
                   for value in L.naming_strings(b)
                   for token in L.UNIT_TOKEN.findall(value)}
    ok("and no bound prints a resident card id, which would assert another corpus's units",
       not (printed_ids & cards))
    ok("nothing is written off a register action other than `enrich`",
       all(ACTIONS[row["register_action"]] == "refuse" for row in refused)
       and bool(refused))
    ok("a register action this pass has no rule for is refused rather than guessed",
       ACTIONS.keys() == {"enrich", "new_resident", "replace_invented"})
    ok("the ledger counts what it wrote", ledger_doc()["counts"]["bounds_written"] == len(written))

    # Rule: one key and no others. A pass that touched a grade, an identity or a note
    # while writing evidence would be marking its own work.
    row = next(r for r in by_person if r["bounds"])
    before = {"id": row["person_id"], "grade": "attested", "sources": ["x"], "note": "n",
              "sex": "male"}
    after = json.loads(json.dumps(before))
    apply_to_person(after, row)
    ok("the applier changes exactly one key",
       {k for k in set(before) | set(after) if before.get(k) != after.get(k)} == {B.BLOCK})
    ok("the applier is idempotent", apply_to_person(after, row) is False)
    ok("the block lands in its slot and not at the end of the record",
       list(after) == ["id", "grade", "sources", B.BLOCK, "note", "sex"])
    other = {"id": row["person_id"], "sources": ["x"],
             "dated_bounds": [{"bound_kind": "presence",
                               "sources": ["chicago_voter_lists_1833_1835_irad"]}]}
    apply_to_person(other, row)
    ok("and another owner's rows in the same block are carried through untouched",
       other["dated_bounds"][0]["sources"] == ["chicago_voter_lists_1833_1835_irad"]
       and len(other["dated_bounds"]) == 1 + len(row["bounds"]))

    # T-1440: the retraction, held to the same rule as the write. A card the register
    # has stopped enriching loses this pass's groups and keeps everybody else's — which
    # is the case `strays` names and, until now, nothing could repair.
    stray = {"id": "x", "sources": ["x"],
             "dated_bounds": [{"bound_kind": "presence",
                               "sources": ["chicago_voter_lists_1833_1835_irad"]}]}
    apply_to_person(stray, row)
    dropped = [B.write(stray, source_id, []) for source_id in PRESS_SOURCES]
    ok("retracting clears this pass's groups off a card the register dropped",
       any(dropped) and not any(B.mine(stray, s) for s in PRESS_SOURCES))
    ok("and it leaves the other owners' rows standing",
       stray["dated_bounds"] == [{"bound_kind": "presence",
                                  "sources": ["chicago_voter_lists_1833_1835_irad"]}])
    ok("and retracting twice is a no-op",
       not any(B.write(stray, source_id, []) for source_id in PRESS_SOURCES))

    print("  %d check(s), %d failure(s)" % (len(ran), len(failures)))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true", dest="self_test")
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
