#!/usr/bin/env python3
"""T-1335: the family pass proper — the kin the registers, the papers' family columns and
the completed resident enrichments state, each unit ruled on its own terms.

    python3 tools/spend_family_pass.py              the reading, on stdout
    python3 tools/spend_family_pass.py --check      every authored ruling answers a live unit
    python3 tools/spend_family_pass.py --self-test  the church derivation, broken on purpose

WHY THIS EXISTS. 168 units stood `unresolved` behind a hand-off line that read "T-1170's
field", retargeted to T-1320 and then here, in all four domain rulings files. T-1320 was
scoped to the BOOK corpus and its pass (tools/spend_book_kin.py) never read the other
three. By the time this pass ran, 68 were still open: 46 church, 13 newspapers, 7
residents and 2 books. The rest had been closed by the mints and the appearance bounds.

WHAT A RULING HERE IS. The standing constraint of T-1312 and T-1320 holds and is not
relaxed: NOBODY IS MINTED AND NO HOUSEHOLD GAINS A MEMBER. A tie is written onto two cards
the town already holds, both ends, or it is not written. A relative who is nobody here is
RULED, not minted to give the tie a far end. KIN IS INSIDE THE TOWN (T-0849).

THE THREE DOMAINS ARE THREE KINDS OF STATEMENT, and each is read the way it speaks:

  church       the register's own `cells.role`: the child, father, mother, groom, bride,
               spouse, subject, parent or decedent of one dated entry. DERIVED, below,
               from the entry's other kin rows and from which cards CLAIM each row as
               their own evidence — the back-link rule tools/survey_stated_kin.py set
               (T-0734). A name that folds onto a town person with no card claiming the
               row is an identity nobody has asserted, not a match.
  newspapers   the MARRIED and DIED columns. A paper names its people in prose, with no
               back-link to a card, so each column is read and ruled by hand in
               data/research/family_pass_rulings.json, against the identity the press
               register (data/research/newspapers/register_1835.json) already made.
  residents    a completed pass's `corroborated_enrichment` naming kin no field carries.
  books        the two book units T-1320's own pass left unruled.

WHAT IT FOUND. No unit carries a tie this pass may write. Every pair with both ends on a
card is either a marriage the kin survey already refused because the register dates it
after the scene, a death before the scene, a tie the household already IS (a wife inside
her husband's record), or — once — a tie the household contradicts: Chester Ingersoll's
house holds a MODELLED wife while the Democrat prints his marriage to Betsy Weaver, who
has her own card. Writing that tie would state two wives; seating the printed bride is a
household edit, so the unit is handed to T-2190, which owns it. Ties whose far end is a
card a BUILD writes whole (the register's underdocumented cards, the readmissions) are
handed to T-2191, because a kin row typed onto one is gone on the next build. One
column, the Noble family's MARRIED notice of 3 December 1833, states two parent ties
between held cards and two marriages: T-2229 wrote the ties onto both cards of each,
and T-2230 owns the marriages, because seating a bride is a household edit. A second
finding fell out
of the burials: five people the registers and papers bury before 1 July 1835 are ruled
present on it. That is not kin and not this pass's to fix; it is T-2189.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

TICKET = "T-1335"
SCENE_DATE = "1835-07-01"
RULINGS = ROOT / "data" / "research" / "family_pass_rulings.json"
RESIDENTS = ROOT / "data" / "residents"
KIN_SURVEY_RULINGS = RESIDENTS / "kin_rulings.json"
READMISSIONS = ROOT / "data" / "reconstruction" / "1835_readmissions.json"
SCHEMA = "chicago4d.family_pass_rulings.v1"

KIN_ROLES = {"child", "father", "mother", "groom", "bride", "spouse", "parent",
             "decedent", "subject"}

TIES_ARE_INSIDE_THE_TOWN = (
    " NOBODY IS MINTED AND NO HOUSEHOLD GAINS A MEMBER (T-1312, T-1320): a kin row is the "
    "link between two cards this town holds, and a relative who is nobody here is evidence "
    "for the prose of a card, not a structure (T-0849).")

# verdict -> the rule it closes under in the remainder registers. One vocabulary for all
# four domains, so a church refusal and a newspaper refusal of the same kind read alike.
RULES = {
    "the_family_pass_finds_the_relative_is_nobody_this_town_holds": {
        "disposition": "refused",
        "statement": (
            "The family pass (T-1335) read the tie and one end of it is a person this "
            "town holds while the other is not: a relative named in the source who has no "
            "card here. The source is not doubted; the tie has no far end to land on, and "
            "this pass does not mint one to give it somewhere." + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_family_pass_finds_neither_party_is_held": {
        "disposition": "refused",
        "statement": (
            "The family pass (T-1335) read the tie and NEITHER of the people it joins is "
            "a person this town holds, or the column's damage has taken the names that "
            "would say who they are. A tie between two people the town does not hold is "
            "not a fact about the town." + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_family_pass_finds_an_identity_nobody_has_asserted": {
        "disposition": "refused",
        "statement": (
            "The family pass (T-1335) read the tie and an end of it folds onto a person "
            "the town holds BY NAME ONLY: no card claims this source row as its own "
            "evidence, and no crosswalk has identified the two. Who a printed name is, is "
            "a crosswalk ruling and not a kinship; a surname and a forename are not "
            "permission to marry two cards (T-0734)." + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_family_pass_finds_the_tie_is_the_household_itself": {
        "disposition": "refused",
        "statement": (
            "The family pass (T-1335) read the tie and it is already the STRUCTURE of the "
            "card: the two people are members of one household record and the person's "
            "own `relationship` states it. `kin` is the link that crosses two records "
            "(T-0597); writing it inside one would say the same thing twice. Any other "
            "relative the reading names is ruled in the note." + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_family_pass_finds_the_tie_ended_before_the_scene": {
        "disposition": "refused",
        "statement": (
            "The family pass (T-1335) read the tie and the source is a DEATH dated before "
            "1 July 1835: on the day this dataset reconstructs, one end of it was buried. A "
            "kin row carries no date, so writing it would state in the present tense a "
            "tie the source closes before the scene. Where the town still holds the dead "
            "person as present, that is a presence fault and T-2189's, not a kinship."
            + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_family_pass_finds_the_tie_begins_after_the_scene": {
        "disposition": "later_only",
        "statement": (
            "The family pass (T-1335) read the tie and the source dates it AFTER 1 July "
            "1835, or describes a household of a later year: on the scene date the tie "
            "did not yet stand. `later_only` is an answer, not a deferral."
            + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_kin_survey_already_ruled_the_register_tie": {
        "disposition": "refused",
        "statement": (
            "The register tie this entry states was proposed by the kin survey "
            "(tools/survey_stated_kin.py, T-0734) — both ends are cards that claim the "
            "entry's own rows — and data/residents/kin_rulings.json REFUSED it, with its "
            "reason, which the note quotes. The family pass (T-1335) carries that ruling "
            "onto the unit rather than making it a second time."
            + TIES_ARE_INSIDE_THE_TOWN),
    },
    "the_register_entry_names_no_relative": {
        "disposition": "refused",
        "statement": (
            "The register entry puts this person in a sacrament — a burial, an adult's "
            "baptism, a child's baptism with no parent written — and names NOBODY ELSE in a "
            "kin role on that line. The role is a role in a rite, not a tie: there is no "
            "second person for a kin row to join, so the family pass (T-1335) has nothing "
            "to write." + TIES_ARE_INSIDE_THE_TOWN),
    },
    # `the_family_pass_finds_a_tie_the_household_contradicts` was RETIRED by T-2190, which
    # spent its one unit: the Democrat's marriage of Chester Ingersoll to Betsy Weaver, a
    # tie into a house that held a modelled wife. The printed bride is seated as his wife
    # and the drawn one withdrawn (tools/reconstruct_modelled_families.py PRINTED_WIVES), so
    # the tie is now the card's own structure and the unit is ruled `same_household`.
    "the_family_pass_finds_a_tie_onto_a_card_a_build_writes": {
        "disposition": "unresolved",
        "ticket": "T-2191",
        "statement": (
            "The family pass (T-1335) read a register tie with BOTH ends on a card, and one "
            "card is written whole by a build — the register's own underdocumented cards "
            "(tools/reconstruct_church_register.py, T-1504) or the readmission stage "
            "(T-1172). A kin row typed onto such a card is gone the next time its stage "
            "runs, so the tie is handed to the open ticket that teaches those builds to "
            "carry it: reciprocal, nobody minted, no household gaining a member."),
    },
    # `the_family_pass_finds_a_family_the_column_states_whole` was RETIRED by T-2232, which
    # spent its one unit: the Democrat's notice of the Noble marriages, 3 December 1833. Its
    # parent ties were already written (T-2229), and Charlotte Wesencraft is now seated as
    # Mark Noble jun.'s wife (PRINTED_WIVES), so that marriage is the card's own structure and
    # the unit is ruled `same_household`; Mary Noble's marriage to George Bickerdyke is T-2233.
    "the_family_pass_finds_the_tie_cannot_be_dated_against_the_scene": {
        "disposition": "refused",
        "statement": (
            "The family pass (T-1335) read the tie and the source dates it to the scene's "
            "own YEAR and no closer: 1 July 1835 sits inside the span and the sentence "
            "cannot say which side. A kin row carries no date, so writing it would state "
            "in the present tense a tie that may not yet have stood. Reopened by any "
            "source that dates it to the month." + TIES_ARE_INSIDE_THE_TOWN),
    },
}

# Rules only the hand-authored book register uses; the derived registers never fire them.
BOOK_ONLY = {"the_family_pass_finds_the_tie_cannot_be_dated_against_the_scene"}

VERDICTS = {
    "relative_not_held": "the_family_pass_finds_the_relative_is_nobody_this_town_holds",
    "neither_end_held": "the_family_pass_finds_neither_party_is_held",
    "identity_not_asserted": "the_family_pass_finds_an_identity_nobody_has_asserted",
    "same_household": "the_family_pass_finds_the_tie_is_the_household_itself",
    "ended_before_the_scene": "the_family_pass_finds_the_tie_ended_before_the_scene",
    "after_the_scene": "the_family_pass_finds_the_tie_begins_after_the_scene",
    "ruled_by_the_kin_survey": "the_kin_survey_already_ruled_the_register_tie",
    "names_no_relative": "the_register_entry_names_no_relative",
    "on_a_generated_card": "the_family_pass_finds_a_tie_onto_a_card_a_build_writes",
    "undated": "the_family_pass_finds_the_tie_cannot_be_dated_against_the_scene",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---- who holds a register row ------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def claims() -> dict[str, list[tuple[str, str, str]]]:
    """record id -> the (card, person, name) that claim that register row as THEIR OWN.

    Three card families carry a register row as identity, each in its own shape, and the
    index reads exactly those shapes and no other: a household person's `*_evidence[]`
    and `appearance_bounds[]` (the survey's back-link and T-1337's merged appearance), an
    underdocumented card's `entries_that_name_her[]` (T-1504), and the readmission
    stage's own `minted[].row_id` (T-1172). `named_on_the_same_entries[]` is NOT a claim — it lists the OTHER
    people of an entry — and `merged/` holds superseded records, so neither is read.
    """
    out: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    def add(rid, card, pid, name):
        if isinstance(rid, str) and (card, pid, name) not in out[rid]:
            out[rid].append((card, pid, name))

    for path in sorted((RESIDENTS / "households").glob("*.json")):
        doc = read_json(path)
        for p in doc.get("persons") or []:
            for key, block in p.items():
                if (key.endswith("_evidence") or key == "appearance_bounds") \
                        and isinstance(block, list):
                    for e in block:
                        if isinstance(e, dict):
                            add(e.get("record_id"), path.stem, p.get("id"), p.get("name"))
    for path in sorted((RESIDENTS / "underdocumented").glob("*.json")):
        doc = read_json(path)
        head = next((p for p in doc.get("persons") or [] if p.get("id") == doc.get("head")),
                    (doc.get("persons") or [{}])[0])
        for e in (doc.get("underdocumented") or {}).get("entries_that_name_her") or []:
            add(e.get("record_id"), path.stem, head.get("id"), head.get("name"))
    for row in read_json(READMISSIONS).get("minted") or []:
        rid = str(row.get("row_id") or "").split("#records/")[-1].split("#")[0]
        add(rid or None, row.get("household_id"), row.get("person_id"), row.get("name"))
    return dict(out)


@functools.lru_cache(maxsize=None)
def generated_cards() -> frozenset:
    """Cards a build writes whole (T-1504's register cards, T-1172's readmissions): a kin
    row written onto one by hand is gone on the next build, so this pass never writes there."""
    stems = {p.stem for p in (RESIDENTS / "underdocumented").glob("*.json")}
    stems |= {p.stem for p in (RESIDENTS / "readmitted").glob("*.json")}
    return frozenset(stems)


@functools.lru_cache(maxsize=None)
def town():
    from survey_stated_kin import Town, load_town
    return Town(load_town())


@functools.lru_cache(maxsize=None)
def survey_pairs() -> dict[frozenset, tuple[str, dict]]:
    """Every register pair the kin survey proposed, with its committed ruling if any."""
    from survey_stated_kin import read_church
    rulings = read_json(KIN_SURVEY_RULINGS).get("rulings") or {}
    return {frozenset((st["subject_record"], st["other_record"])): (st["id"], rulings.get(st["id"]))
            for st in read_church() if st.get("subject_record") and st.get("other_record")}


@functools.lru_cache(maxsize=None)
def entries(source_file: str) -> dict[tuple, list[dict]]:
    doc = read_json(ROOT / source_file)
    out: dict[tuple, list[dict]] = defaultdict(list)
    for r in doc.get("records") or []:
        loc = r.get("locator") or {}
        out[(loc.get("year_series"), loc.get("entry"))].append(r)
    return dict(out)


def state(row: dict, held: dict) -> str:
    """held: a card claims the row; unasserted: a town name folds onto it; else nobody."""
    if held.get(row.get("id")):
        return "held"
    if town().resolve(str(row.get("normalized") or row.get("as_read") or "")):
        return "unasserted"
    return "nobody"


def role_of(row: dict) -> str:
    return str((row.get("cells") or {}).get("role") or (row.get("locator") or {}).get("role") or "")


def church_verdict(row: dict, source_file: str, held: dict | None = None,
                   pairs: dict | None = None, line_rows: list | None = None) -> tuple[str, str]:
    """The verdict on one register row in a kin role, derived and never authored."""
    held = claims() if held is None else held
    pairs = survey_pairs() if pairs is None else pairs
    loc = row.get("locator") or {}
    dated = str((row.get("cells") or {}).get("date") or row.get("describes_date") or "")
    if line_rows is None:
        line_rows = entries(source_file).get((loc.get("year_series"), loc.get("entry")), [])
    kin = [r for r in line_rows if r.get("id") != row.get("id") and role_of(r) in KIN_ROLES]
    name = str(row.get("normalized") or row.get("as_read") or row.get("id"))
    if not kin:
        return "names_no_relative", (
            f"{name}, {role_of(row)} of the entry dated {dated}: the line names nobody else "
            f"in a kin role.")
    me = state(row, held)
    them = [(r, state(r, held)) for r in kin]

    def who(r, s):
        n = r.get("normalized") or r.get("as_read") or r.get("id")
        if s == "held":
            return f"{n} ({role_of(r)}, held as {held[r['id']][0][0]})"
        return f"{n} ({role_of(r)}, {'a name the town holds with no card claiming the row' if s == 'unasserted' else 'nobody here'})"

    line = (f"{who(row, me)}; the entry dated {dated} also names "
            + "; ".join(who(r, s) for r, s in them) + ".")
    for r, _ in them:
        hit = pairs.get(frozenset((row.get("id"), r.get("id"))))
        if hit and hit[1]:
            sid, ruling = hit
            if ruling.get("ruling") != "refused":
                raise SystemExit(
                    f"{row.get('id')}: kin_rulings.json rules {sid} {ruling.get('ruling')!r}, "
                    "so the tie is on the cards and the unit should have closed asserted — "
                    "re-derive the ledger rather than ruling it here")
            return "ruled_by_the_kin_survey", (
                f"{line} kin_rulings.json on {sid}: {str(ruling.get('why'))[:300]}")
    if me == "held" and any(s == "held" for _, s in them):
        # A month-precision date in the scene's own month decides neither way, and raises.
        if source_file.endswith("st_cyr_deaths_1834_1837.json") and dated[:7] < SCENE_DATE[:7]:
            return "ended_before_the_scene", (
                f"{line} The burial is dated {dated}, before the scene date.")
        # A marriage after the scene is a tie that did not yet stand. A burial after it is
        # not: the dead person was alive on the day, and that tie is the survey's to rule.
        if source_file.endswith("st_cyr_marriages_1834_1839.json") and (
                dated[:7] > SCENE_DATE[:7] or (len(dated) >= 10 and dated[:10] > SCENE_DATE)):
            return "after_the_scene", f"{line} The entry is dated {dated}, after the scene date."
        cards = {held[r["id"]][0][0] for r, s in them if s == "held"} | {held[row["id"]][0][0]}
        if cards & generated_cards():
            return "on_a_generated_card", (
                f"{line} {', '.join(sorted(cards & generated_cards()))} is written whole by "
                "its stage's build, so the tie is T-2191's to write through it.")
        raise SystemExit(
            f"{row.get('id')}: both ends of a register tie are held and nothing has ruled "
            "it — rule it in data/residents/kin_rulings.json (the survey's file) first")
    if me == "unasserted" or any(s == "unasserted" for _, s in them):
        return "identity_not_asserted", line
    if me == "held" or any(s == "held" for _, s in them):
        return "relative_not_held", line
    return "neither_end_held", line


def church_rule(unit: dict) -> tuple[str, str]:
    verdict, note = church_verdict(unit["record"], unit["source_file"])
    return VERDICTS[verdict], note


# ---- the authored rulings: newspapers, residents, books ----------------------------------

@functools.lru_cache(maxsize=None)
def authored() -> dict[str, dict]:
    return read_json(RULINGS).get("rulings") or {}


CONSUMED: set[str] = set()


def authored_rule(unit: dict, where: str) -> tuple[str, str]:
    uid = unit.get("unit_id") or ""
    ruling = authored().get(uid)
    if ruling is None:
        raise SystemExit(
            f"{uid or where}: a kin unit the family pass (T-1335) has not read — rule it in "
            "data/research/family_pass_rulings.json rather than handing it on by default")
    CONSUMED.add(uid)
    return VERDICTS[ruling["verdict"]], f"{where} THE FAMILY PASS: {ruling['why']}"


def check(quiet: bool = False) -> list[str]:
    faults = []
    doc = read_json(RULINGS)
    if doc.get("schema") != SCHEMA:
        faults.append(f"{RULINGS.name}: schema is {doc.get('schema')!r}, not {SCHEMA!r}")
    for uid, ruling in sorted(authored().items()):
        if ruling.get("verdict") not in VERDICTS:
            faults.append(f"{uid}: verdict {ruling.get('verdict')!r} is not one this pass knows")
        if len(str(ruling.get("why") or "").strip()) < 80:
            faults.append(f"{uid}: a ruling owes its reason, and this one states none")
    # Every authored ruling answers a unit the remainder registers actually route here; an
    # orphan is a ruling on a unit something else closed, which reads as work and is not.
    # The registers import this module by name; run as a script, this is `__main__`, so
    # the set the build fills is read off the imported module and not this one.
    import spend_remainder_rulings as R
    from spend_family_pass import CONSUMED as consumed
    R.build_documents(ROOT)
    # …and the press-bounds pass asks this one about its units BEFORE any card asserts
    # them (spend_press_bounds.corpus_units reads no target), so a kin unit that has since
    # closed `asserted` onto a card is still routed here there, and its ruling is no orphan
    # (T-2190: the Ingersoll-Weaver marriage, now one household).
    import spend_press_bounds as P
    P.rows(ROOT)
    for uid in sorted(set(authored()) - consumed):
        faults.append(f"{uid}: authored, and no unit the registers route to the family pass "
                      "is this one — withdraw the ruling")
    if not quiet:
        for f in faults:
            print(f"  FAIL {f}")
        print(f"family pass: {len(authored())} authored rulings, {len(faults)} fault(s)")
    return faults


def self_test() -> int:
    """The church derivation over fixtures, each case one verdict."""
    failures = []
    src = "data/research/church/records/st_cyr_deaths_1834_1837.json"

    def case(label, rows, me, held, want, pairs=None):
        try:
            got = church_verdict(me, src, held, pairs or {}, rows)[0]
        except SystemExit:
            got = "raised"
        print(f"  {'ok  ' if got == want else 'FAIL'} {label}: {got}")
        if got != want:
            failures.append(label)

    def r(rid, role, date="1834-06", name="Zz Qqqqq"):
        return {"id": rid, "normalized": name, "locator": {"entry": 1},
                "cells": {"role": role, "date": date}}

    dec, par = r("d", "decedent"), r("p", "parent", name="Yy Wwwww")
    case("a lone burial", [dec], dec, {}, "names_no_relative")
    case("neither end on a card", [dec, par], dec, {}, "neither_end_held")
    case("one end on a card", [dec, par], dec, {"d": [("hh_x", "x", "X")]}, "relative_not_held")
    both = {"d": [("hh_x", "x", "X")], "p": [("hh_y", "y", "Y")]}
    case("both on cards, buried before the scene", [dec, par], dec, both,
         "ended_before_the_scene")
    late = r("d", "decedent", date="1835-09-01")
    case("both on cards, alive on the day, nothing has ruled the tie", [late, par], late, both,
         "raised")
    case("the survey refused it", [dec, par], dec, both, "ruled_by_the_kin_survey",
         pairs={frozenset(("d", "p")): ("p__parent_of__d", {"ruling": "refused", "why": "w"})})
    case("the survey landed it", [dec, par], dec, both, "raised",
         pairs={frozenset(("d", "p")): ("p__parent_of__d", {"ruling": "landed", "why": "w"})})
    print(f"self-test | {len(failures)} failure(s)")
    return 1 if failures else 0


def report() -> None:
    import spend_remainder_rulings as R
    docs = R.build_documents(ROOT)
    tally = Counter()
    for domain, doc in docs.items():
        for row in doc["rulings"]:
            if row["rule"] in RULES:
                tally[(domain, row["rule"])] += 1
    for (domain, rule), n in sorted(tally.items()):
        print(f"  {domain:11} {n:3}  {rule}")
    print(f"family pass: {sum(tally.values())} units ruled")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.check:
        return 1 if check(args.quiet) else 0
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
