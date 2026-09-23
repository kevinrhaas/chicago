#!/usr/bin/env python3
"""The 1830 schedule and St Mary's register, written onto the cards they name (T-1337).

    python3 tools/spend_appearance_bounds.py             write the ledger and the bounds
    python3 tools/spend_appearance_bounds.py --check      everything re-derives; nothing drifted
    python3 tools/spend_appearance_bounds.py --report     person by person, what each row bounds
    python3 tools/spend_appearance_bounds.py --self-test  the rules below, held over what it derives

WHY THIS EXISTS. T-1326 wrote the town's own poll and tax rolls onto the 236 cards they
name, as `persons[].dated_bounds[]`, because a paragraph in `persons[].note` is not a field
and `tools/research_spend_ledger.py` counts a reading as SPENT only where a structured,
source-bearing, `attested`/`inferred` node NAMES the unit. Its sibling T-1329 held three
further corpora on the same footing and in a worse state: the 1830 Peoria & Putnam
schedule, St Mary's baptismal register, St Cyr's marriage pages and the town's press, 238
units, of which only ten sat on a card in any form at all. This pass is the register and
the schedule half of that — T-1337 — and unlike T-1326 it is NOT a legibility pass: an
identification has to already stand before a bound can be written, and where none does the
answer here is a written refusal in the ruling registers and no card is touched.

WHAT IT WRITES, AND THE TWENTY-SEVEN ROWS IT IS LIMITED TO. Two adjudications already made
elsewhere, read and never re-made:

  * `data/research/census_1830/resident_crosswalk.json` — `matched[]`, 14 rows, where the
    1830 reading and a town person agree on surname AND given name. That file REFUSES a
    surname-only agreement in writing (63 of them) and holds one surname-variant row as a
    declared candidate; neither reaches a card, here or anywhere.
  * `data/research/church/st_marys_baptisms_crosswalk.json` — the 13 register appearances
    whose ruling is `merged`, resolved to a person through that file's own `merges[]`,
    whose `into` name is looked up in the residents layer and must resolve to exactly one.

NOT ONE ROW COMES FROM ST CYR'S PAGES. That crosswalk proposes one merge and makes none:
its 13 units in this corpus are 10 declared candidates, one entry printed with a blank
where the forename stands, and two prose readings that bound the register rather than
populate it. A candidate is a rival still standing, and writing a bound off one would print
an undecided identity as a decided one. They are refused in
`tools/spend_remainder_rulings.py`, by name, with what would reopen them.

THE FOUR RULES THAT KEEP A ROW FROM SAYING MORE THAN IT CAN.

  1. THE 1830 LINE BOUNDS PRESENCE IN A DISTRICT AND NOT AT CHICAGO. The division is
     headed 'Peoria & Putnam Counties & Territory attached' and the schedule never writes
     the word Chicago; the Fox River and Du Page settlements are inside it. So an 1830 row
     carries `bound_kind: "district_presence"` and `here_by: null` — the same shape T-1117
     gave a tax row, for the same reason: the reading does not put a body in the town. The
     record's own note says it first ("Presence in that district in the summer of 1830; not
     a Chicago residence, and never an 1835 one") and this pass does not improve on it.

  2. A REGISTER APPEARANCE DOES BOUND A PRESENCE AT CHICAGO, on the day the entry is
     dated: the sponsor stood at the font, and every one of these records carries
     `at_chicago: true` and `cells.place` of Chicago, Cook County, Illinois.

  3. NO ROW IS `attested` AND NO ROW COVERS THE SCENE DATE. The pages are documented — the
     federal schedule off the scan, the register off the eleven deposited page images — and
     the IDENTITIES are not: each rests on a name agreement a crosswalk declared, and no
     source states that the man on the page is the person on the card. A bound whose
     subject is inferred is an inferred bound. Under the ladder ratified 2026-09-03 an
     EARLIER source corroborates and dates and never promotes, and a LATER one does not
     promote either, so `covers_scene_date` is `false` on all 27 rows.

  4. A REGISTER ROW CITES ITS MERGE RULE AND DOES NOT TRANSCRIBE IT, which is the one
     place this pass departs from T-1326 and it was measured rather than chosen. The voter
     crosswalk's rules are machine-written and uniform — "forenames agree initial for
     initial" — so carrying one verbatim onto a card carries a name agreement and nothing
     else. St Mary's merges are hand-written essays that corroborate the identification
     from OTHER evidence, and three of the nine name a relative: "his wife is Monique
     Nadeau in the register and the resident record documents his marriage". Copied onto
     the card, those sentences enter the residents corpus as stated kinship, and
     `tools/survey_stated_kin.py` read them exactly that way — three unruled kin
     statements appeared in the gate, about Chandler's daughter and Juneau's father, off a
     pass that is supposed to write a date. A citation carries the provenance without
     importing the claims: the row names the crosswalk, the register spelling and the
     resident name it was merged into, and the rule stays in the file that authored it.

  5. AND THE LADDER CUTS BOTH WAYS, WHICH THIS CORPUS IS THE FIRST TO NEED. Three of the
     thirteen register appearances are dated after 1 July 1835 (20 August, 25 September and
     9 November 1835). A later day cannot bound a presence AT the scene, so those rows
     carry `side_of_scene_date: "later"` and `here_by: null`, and say so. Only an earlier
     appearance gets an `here_by`.

NO GRADE MOVES, NO IDENTITY REOPENS, NO PERSON IS MINTED, AND NO OTHER KEY IS TOUCHED.
`--self-test` diffs a record through the applier and asserts the changed key set is
`{"appearance_bounds"}` alone. The block is its own key and not T-1326's: that pass's
`--check` re-derives `dated_bounds` byte for byte against the voter crosswalk, so a second
corpus written into the same list would fail a green gate belonging to a closed ticket.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
CENSUS_CROSSWALK = RESEARCH / "census_1830" / "resident_crosswalk.json"
CENSUS_RECORDS = RESEARCH / "census_1830" / "records" / "schedule_chicago_1830.json"
CHURCH_CROSSWALK = RESEARCH / "church" / "st_marys_baptisms_crosswalk.json"
CHURCH_RECORDS = RESEARCH / "church" / "records" / "st_marys_baptisms_1833_1835.json"
LEDGER = RESEARCH / "appearance_bounds_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1
TICKET = "T-1337"
GENERATOR = "tools/spend_appearance_bounds.py"
BLOCK = "appearance_bounds"
SCENE_DATE = "1835-07-01"
CONFIDENCE = "inferred"

CENSUS_SOURCE = "census_1830_peoria_county_chicago_precinct"
CHURCH_SOURCE = "st_marys_baptismal_register_1833_1835"
SOURCE_IDS = (CENSUS_SOURCE, CHURCH_SOURCE)

CENSUS_DIVISION = "Peoria & Putnam Counties & Territory attached"

# The register roles this pass may bound a presence from, and the reason the list is short.
# A sponsor, a godparent or a witness STOOD THERE: the entry records an adult attending a
# sacrament on a day, which is an appearance and nothing more. The KIN roles of the same
# entry — father, mother, spouse, subject, child, decedent — are a TIE between two people
# and they are T-1320's units, ruled in tools/spend_remainder_rulings.py under
# `the_register_entry_names_kin`. Eight of the crosswalk's 22 `merged` rulings carry a kin
# role, and a bound written off one would close another ticket's unit with work that ticket
# has not done. `tools/spend_remainder_rulings.ATTENDANCE_ROLES` is the same set, and it is
# what decides which units reach this pass at all.
ATTENDANCE_ROLES = ("sponsor", "godfather", "godmother", "witness")

LADDER = (
    "Under the evidence ladder ratified 2026-09-03 a source EARLIER than the scene date "
    "corroborates and dates and never promotes, and a source LATER than it does not "
    "promote either.")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- the dates a reading can mean -----------------------------------------------------

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
    raise ValueError("a reading whose date this pass cannot read: %r" % stated)


def side_of_scene(reaches: str) -> str:
    return "earlier" if reaches <= SCENE_DATE else "later"


# --- who the residents layer holds ----------------------------------------------------

def residents_by_name() -> dict:
    """Exact person name -> [(household_id, person_id)]. Ambiguity is never resolved here."""
    found: dict = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        household = load(path)
        for person in household.get("persons") or []:
            name = str(person.get("name") or "").strip()
            if name:
                found.setdefault(name, []).append((household["id"], person.get("id")))
    return found


def one_resident(name: str, by_name: dict) -> tuple[str, str]:
    """The single person of that name, or a refusal. A pass that guessed would be minting."""
    hits = by_name.get(name) or []
    if len(hits) != 1:
        raise ValueError(
            "the residents layer holds %d people named %r and this pass makes no "
            "identification of its own" % (len(hits), name))
    return hits[0]


# --- the 1830 schedule ----------------------------------------------------------------

def census_rows(by_name: dict) -> list:
    crosswalk = load(CENSUS_CROSSWALK)
    doc = load(CENSUS_RECORDS)
    records = {row["id"]: row for row in doc["records"]}
    precision, reaches = reach_of(doc["describes_date"])
    rows = []
    for entry in crosswalk["matched"]:
        record = records[entry["record_id"]]
        locator = record.get("locator") or {}
        household, person_id = one_resident(entry["town_name"], by_name)
        if household != entry["household"]:
            raise ValueError("%s: the crosswalk names household %s and the town person "
                             "%r stands in %s" % (entry["record_id"], entry["household"],
                                                  entry["town_name"], household))
        rows.append({
            "household_id": household,
            "person_id": person_id,
            "bound": {
                "bound_kind": "district_presence",
                "corpus": "census_1830",
                "source_title": ("Fifth census of the United States, 1830 — the division "
                                 "headed '%s'" % CENSUS_DIVISION),
                "record_id": entry["record_id"],
                "as_read": entry["as_read"],
                "role": "head_of_family",
                "locator": "leaf %s entry %s, %s line %s" % (
                    locator.get("image"), locator.get("entry"),
                    locator.get("text_file"), locator.get("line")),
                "describes_date": doc["describes_date"],
                "date_confidence": record.get("confidence"),
                "precision": precision,
                "reaches": reaches,
                "here_by": None,
                "side_of_scene_date": side_of_scene(reaches),
                "covers_scene_date": False,
                "confidence": CONFIDENCE,
                "sources": [CENSUS_SOURCE],
                "identity_rule": entry.get("rule"),
                "note": (
                    "A BOUND ON PRESENCE IN A DISTRICT, AND NOT AT CHICAGO. The division "
                    "is headed '%s' and the schedule never writes the word Chicago — the "
                    "Fox River and Du Page settlements are inside it — so this row bounds "
                    "presence in that district in the summer of 1830 and puts no body in "
                    "the town, which is why `here_by` is null. The record's own note says "
                    "it first: 'Presence in that district in the summer of 1830; not a "
                    "Chicago residence, and never an 1835 one'. %s THE IDENTITY IS "
                    "INFERRED AND THE PAGE IS NOT: the leaf is read scan_verified off the "
                    "federal schedule, and what no source states is that the head of "
                    "family on it is the person on this card. "
                    "data/research/census_1830/resident_crosswalk.json joins them on a "
                    "name agreement and says in terms that it grades nothing on its own. "
                    "No grade moves here and the identity is neither reopened nor "
                    "hardened." % (CENSUS_DIVISION, LADDER)),
            },
        })
    return rows


# --- St Mary's baptismal register -----------------------------------------------------

def church_identities() -> dict:
    """The register name -> the residents-layer name, off the crosswalk's own merges."""
    return {merge["from"]: merge for merge in load(CHURCH_CROSSWALK)["merges"]}


def church_rows(by_name: dict) -> list:
    crosswalk = load(CHURCH_CROSSWALK)
    records = {row["id"]: row for row in load(CHURCH_RECORDS)["records"]}
    merges = church_identities()
    rows = []
    for ruling in crosswalk["rulings"]:
        if ruling.get("outcome") != "merged":
            continue
        record_id = ruling.get("record_id")
        record = records.get(record_id)
        if record is None:
            # A `merged` ruling on a town-finding CLAIM names no register entry and has no
            # date of its own to bound with; the register entry it came from is ruled here
            # in its own right. Nothing to write.
            continue
        merge = merges.get(ruling["name"])
        if merge is None:
            raise ValueError("%s: ruled `merged` and the crosswalk's merges[] does not "
                             "carry %r" % (record_id, ruling["name"]))
        household, person_id = one_resident(merge["into"], by_name)
        cells = record.get("cells") or {}
        if str(cells.get("role") or "") not in ATTENDANCE_ROLES:
            # A KIN role, and a tie rather than an appearance — T-1320's unit. See the
            # comment on ATTENDANCE_ROLES for why this pass may not touch it.
            continue
        if record.get("at_chicago") is not True:
            # The reading says in terms that this entry is not at Chicago, and
            # `research_spend_ledger.natural_disposition` closes it `outside_chicago`
            # before any register is consulted. An appearance somewhere else bounds
            # nothing here.
            continue
        precision, reaches = reach_of(record["describes_date"])
        side = side_of_scene(reaches)
        locator = record.get("locator") or {}
        if side == "earlier":
            says = (
                "A BOUND ON PRESENCE AT CHICAGO, AND NOTHING FURTHER. The entry is dated "
                "%s at %s and this person stood at the font as %s, so the register places "
                "a body in the town no later than %s. %s" % (
                    record["describes_date"], cells.get("place"), cells.get("role"),
                    reaches, LADDER))
        else:
            says = (
                "AN APPEARANCE LATER THAN THE SCENE DATE, WHICH BOUNDS NOTHING AT IT. The "
                "entry is dated %s at %s — after 1 July 1835 — and this person stood at "
                "the font as %s. %s So this row dates and corroborates an appearance and "
                "`here_by` is null: it cannot put a body in the town on the scene date, "
                "and back-projecting it would be the promotion the ladder forbids." % (
                    record["describes_date"], cells.get("place"), cells.get("role"),
                    LADDER))
        rows.append({
            "household_id": household,
            "person_id": person_id,
            "bound": {
                "bound_kind": "presence",
                "corpus": "st_marys_baptisms",
                "source_title": ("St Mary's baptismal register, Chicago, 1833-1835, read "
                                 "off the deposited page images"),
                "record_id": record_id,
                "as_read": record.get("as_read"),
                "role": cells.get("role"),
                "locator": "image %s, page %s, entry %s of the %s series" % (
                    locator.get("image"), locator.get("page"), locator.get("entry"),
                    locator.get("year_series")),
                "describes_date": record["describes_date"],
                "date_confidence": cells.get("date_confidence"),
                "precision": precision,
                "reaches": reaches,
                "here_by": reaches if side == "earlier" else None,
                "side_of_scene_date": side,
                "covers_scene_date": False,
                "confidence": CONFIDENCE,
                "sources": [CHURCH_SOURCE],
                "identity_rule": (
                    "data/research/church/st_marys_baptisms_crosswalk.json merges the "
                    "register's %r into the residents layer's %r under a written rule "
                    "naming both spellings verbatim; the rule is read there and is not "
                    "copied here." % (ruling["name"], merge["into"])),
                "identity_rule_source": (
                    "data/research/church/st_marys_baptisms_crosswalk.json — merges[] "
                    "into %r" % merge["into"]),
                "note": (
                    "%s THE IDENTITY IS INFERRED AND THE PAGE IS NOT. The entry is read "
                    "scan_verified off the page image at `documented` confidence. What no "
                    "source states is that the sponsor the register names is the person on "
                    "this card: data/research/church/st_marys_baptisms_crosswalk.json "
                    "merges the register's %r into the residents layer's %r under a written "
                    "rule, and a bound whose subject is inferred is an inferred bound. No "
                    "grade moves here and the identity is neither reopened nor hardened."
                    % (says, ruling["name"], merge["into"])),
            },
        })
    return rows


# --- one row per person ---------------------------------------------------------------

def people() -> list:
    """One row per PERSON, carrying that person's bounds in corpus order then record order.

    The order is the crosswalks' own and then the record id, so the list is a
    re-derivation of its input rather than a re-sort of it.
    """
    by_name = residents_by_name()
    order: list = []
    seen: dict = {}
    for row in census_rows(by_name) + church_rows(by_name):
        key = (row["household_id"], row["person_id"])
        if key not in seen:
            seen[key] = {"household_id": row["household_id"],
                         "person_id": row["person_id"],
                         "bounds": []}
            order.append(seen[key])
        seen[key]["bounds"].append(row["bound"])
    return order


# --- the ledger -----------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = people()
    bounds = [b for row in rows for b in row["bounds"]]
    per_corpus: dict = {}
    per_kind: dict = {}
    per_side: dict = {}
    for b in bounds:
        per_corpus[b["corpus"]] = per_corpus.get(b["corpus"], 0) + 1
        per_kind[b["bound_kind"]] = per_kind.get(b["bound_kind"], 0) + 1
        per_side[b["side_of_scene_date"]] = per_side.get(b["side_of_scene_date"], 0) + 1
    census = load(CENSUS_CROSSWALK)
    church = load(CHURCH_CROSSWALK)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by " + GENERATOR + ". The ledger of " + TICKET + ": every 1830 "
            "schedule line and St Mary's register appearance whose identification ALREADY "
            "STANDS in a committed crosswalk, written onto that person as a structured "
            "bound the research-spend ledger can see. It records WRITES and not "
            "adjudications — the adjudications are resident_crosswalk.json and "
            "st_marys_baptisms_crosswalk.json, and this file carries no 'crosswalk' in its "
            "name so that measure_research_spend.py cannot read a write as a second "
            "ruling. Nothing here is an 1835 residence: an 1830 line bounds presence in "
            "the Peoria & Putnam division and not at Chicago at all, and a register "
            "appearance bounds a presence on its own day, three of them later than the "
            "scene date. Where no identification stands the answer is a written refusal in "
            "tools/spend_remainder_rulings.py and tools/spend_name_on_a_roll_rulings.py, "
            "and no card is touched."),
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "source_ids": list(SOURCE_IDS),
        "reads": [
            "data/research/census_1830/resident_crosswalk.json — matched[]",
            "data/research/church/st_marys_baptisms_crosswalk.json — rulings[] `merged`",
        ],
        "writes": "data/residents/households/*.json — persons[].%s[]" % BLOCK,
        "counts": {
            "bounds_written": len(bounds),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "identities_changed": 0,
            "persons_minted": 0,
            "per_corpus": per_corpus,
            "per_kind": per_kind,
            "per_side_of_scene_date": per_side,
            "census_1830_surname_variant_candidates": len(
                census["surname_variant_candidates"]),
            "census_1830_surname_only_refused": census["counts"]["surname_only_refused"],
            "census_1830_no_surname_in_town": census["counts"]["no_surname_in_town"],
            "st_marys_rulings": len(church["rulings"]),
            "st_marys_merged_rulings": sum(
                1 for r in church["rulings"] if r.get("outcome") == "merged"),
        },
        "refusals": [
            {
                "rule": "A1",
                "why": ("an 1830 row carries `here_by: null`. The division is Peoria & "
                        "Putnam and everything hung off them, the schedule never writes "
                        "the word Chicago, and a district is not the town"),
                "rows": per_corpus.get("census_1830", 0),
            },
            {
                "rule": "A2",
                "why": ("no row reaches `attested`. Every identification written here is a "
                        "name agreement a crosswalk declared and none of them is an "
                        "identification a source makes, so the bound is inferred however "
                        "documented the page under it is"),
                "rows": len(bounds),
            },
            {
                "rule": "A3",
                "why": ("no row covers the scene date. An earlier source corroborates and "
                        "dates and never promotes, and a later one does not promote either"),
                "rows": len(bounds),
            },
            {
                "rule": "A4",
                "why": ("a register appearance dated after 1 July 1835 carries `here_by: "
                        "null` as well: it dates an appearance and cannot bound a presence "
                        "at a day that had already passed"),
                "rows": per_side.get("later", 0),
            },
            {
                "rule": "A5",
                "why": ("a merged ruling on a KIN role is not written. Eight of the "
                        "crosswalk's merges name the father, mother, spouse or subject of "
                        "an entry, which is a tie between two cards and is T-1320's unit "
                        "under `the_register_entry_names_kin`; one more names a sponsor at "
                        "an entry the reading places outside Chicago, which the reading "
                        "closes itself"),
                "rows": sum(1 for r in church["rulings"] if r.get("outcome") == "merged")
                        - per_corpus.get("st_marys_baptisms", 0),
            },
            {
                "rule": "A6",
                "why": ("nothing is written off St Cyr's pages, off a declared candidate, "
                        "or off a surname-only agreement. A candidate is a rival still "
                        "standing and a bound written off one would print an undecided "
                        "identity as a decided one; those units are refused by name in the "
                        "ruling registers instead"),
                "rows": 0,
            },
        ],
        "people": rows,
    }


# --- writing the cards ----------------------------------------------------------------

def _insert_after(row: dict, key: str, value, after: str) -> None:
    """One field, in a stable slot — the convention T-1326 measured into existence.

    A NEW KEY APPENDED AT THE END IS NOT A STABLE SLOT: `spend_person_sex_age.py --check`
    and `reconstruct_sex_age.py` both re-derive a whole card and compare it byte for byte,
    popping `sex`, `sex_basis`, `age_band` and `birth_year` and re-appending them, so a
    block written after those keys lands before them on the next re-derivation and the card
    reads as drift.
    """
    rebuilt = {}
    for old_key, old_value in row.items():
        rebuilt[old_key] = old_value
        if old_key == after:
            rebuilt[key] = value
    if key not in rebuilt:
        rebuilt[key] = value
    row.clear()
    row.update(rebuilt)


def slot_after(person: dict) -> str:
    """After T-1326's block where the card carries one, otherwise after `sources`.

    Two evidence blocks in one card need a deterministic ORDER, not just a slot, or the
    two passes fight over which comes first and both `--check`s report drift by turns.
    """
    return "dated_bounds" if "dated_bounds" in person else "sources"


def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs: one key, rewritten whole.

    The block is DERIVED and therefore replaced rather than appended to, which is how it
    holds the once-each rule `tools/spend_write_once.py` had to give the prose-writing
    passes a module for: a JSON key exists once by construction, and `--check` compares the
    whole list against what this pass re-derives.
    """
    if person.get(BLOCK) == row["bounds"]:
        return False
    if BLOCK in person:
        person[BLOCK] = row["bounds"]
    else:
        _insert_after(person, BLOCK, row["bounds"], slot_after(person))
    return True


def apply(quiet: bool = False) -> int:
    touched = 0
    for row in people():
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        household = load(path)
        for person in household.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, household)
    if not quiet:
        print("appearance bounds: written onto %d resident record(s)" % touched)
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
        if person.get(BLOCK) != row["bounds"]:
            bad.append("%s is named by %d appearance(s) and its %s does not re-derive — "
                       "run %s" % (row["person_id"], len(row["bounds"]), BLOCK, GENERATOR))
    return bad


def strays(rows: list) -> list:
    """And nobody the crosswalks did NOT identify may carry a bound off these corpora."""
    wanted = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        household = load(path)
        for person in household.get("persons") or []:
            block = person.get(BLOCK) or []
            cited = {s for b in block if isinstance(b, dict)
                     for s in (b.get("sources") or [])}
            if not cited & set(SOURCE_IDS):
                continue
            if (household.get("id"), person.get("id")) not in wanted:
                bad.append("%s carries an appearance bound off the 1830 schedule or St "
                           "Mary's register and no committed crosswalk identifies it"
                           % person.get("id"))
    return bad


def ledger_drift() -> list:
    return ([] if LEDGER.exists() and load(LEDGER) == ledger_doc()
            else ["%s does not re-derive — run %s"
                  % (LEDGER.relative_to(ROOT), GENERATOR)])


def check(quiet: bool = False) -> int:
    rows = people()
    bad = ledger_drift() + gaps(rows) + strays(rows)
    if bad:
        for line in bad[:40]:
            print("  FAIL: %s" % line)
        if len(bad) > 40:
            print("  ... and %d more" % (len(bad) - 40))
        return 1
    if not quiet:
        total = sum(len(r["bounds"]) for r in rows)
        print("appearance bounds: %d bound(s) on %d card(s), all written, no strays, "
              "none doubled" % (total, len(rows)))
    return 0


def report() -> int:
    for row in people():
        print("%s (%s)" % (row["person_id"], row["household_id"]))
        for b in row["bounds"]:
            print("   %-18s %-18s %-11s %-8s here_by=%-11s %s"
                  % (b["corpus"], b["bound_kind"], b["describes_date"],
                     b["side_of_scene_date"], b["here_by"], b["as_read"]))
    return 0


# --- the rules, held over what they derive --------------------------------------------

def self_test() -> int:
    failures = []
    ran = []

    def ok(label, cond):
        ran.append(label)
        print("  %s %s" % ("ok:  " if cond else "FAIL:", label))
        if not cond:
            failures.append(label)

    ok("a day-precision reading reaches its own day",
       reach_of("1834-08-11") == ("day", "1834-08-11"))
    ok("a bare year reaches 31 December", reach_of("1830") == ("year", "1830-12-31"))
    ok("a month reaches its last day", reach_of("1833-08") == ("month", "1833-08-31"))
    try:
        reach_of("summer")
        ok("an unreadable date is refused rather than guessed", False)
    except ValueError:
        ok("an unreadable date is refused rather than guessed", True)
    ok("the scene date itself reads as earlier", side_of_scene(SCENE_DATE) == "earlier")
    ok("the day after the scene date reads as later",
       side_of_scene("1835-07-02") == "later")

    # Rule: this pass makes no identification of its own. A name the residents layer
    # holds twice, or not at all, is a refusal and never a choice.
    for label, index in (("a name no resident carries", {}),
                         ("a name two residents carry",
                          {"J. Doe": [("hh_a", "a"), ("hh_b", "b")]})):
        try:
            one_resident("J. Doe", index)
            ok("%s is refused rather than chosen between" % label, False)
        except ValueError:
            ok("%s is refused rather than chosen between" % label, True)

    rows = people()
    bounds = [b for r in rows for b in r["bounds"]]
    ok("every derived bound is inferred and none is attested",
       bool(bounds) and {b["confidence"] for b in bounds} == {CONFIDENCE})
    ok("no derived bound covers the scene date",
       not any(b["covers_scene_date"] for b in bounds))
    ok("every 1830 row bounds a district and puts no body in the town",
       all(b["bound_kind"] == "district_presence" and b["here_by"] is None
           for b in bounds if b["corpus"] == "census_1830"))
    ok("every register row bounds a presence at Chicago",
       all(b["bound_kind"] == "presence"
           for b in bounds if b["corpus"] == "st_marys_baptisms"))
    ok("an appearance later than the scene date bounds nothing at it",
       all(b["here_by"] is None for b in bounds if b["side_of_scene_date"] == "later")
       and any(b["side_of_scene_date"] == "later" for b in bounds))
    ok("an earlier register appearance reaches its own day and no further",
       all(b["here_by"] == b["reaches"] <= SCENE_DATE for b in bounds
           if b["corpus"] == "st_marys_baptisms" and b["side_of_scene_date"] == "earlier"))
    ok("every bound names one of this pass's two archival sources and only it",
       all(len(b["sources"]) == 1 and b["sources"][0] in SOURCE_IDS for b in bounds))
    ok("every bound states the identity rule it rests on",
       all(len(str(b["identity_rule"] or "")) > 40 for b in bounds))
    ok("a register row cites its merge rule and does not transcribe the crosswalk's prose",
       all("crosswalk.json merges the register's" in b["identity_rule"]
           for b in bounds if b["corpus"] == "st_marys_baptisms"))
    ok("nothing is written off St Cyr's pages",
       not any("st_cyr" in str(b["record_id"]) for b in bounds))
    ok("every register row is an attendance role and no kin tie is taken from T-1320",
       all(b["role"] in ATTENDANCE_ROLES for b in bounds
           if b["corpus"] == "st_marys_baptisms"))
    ok("and the register rows are exactly the merged attendance entries at Chicago",
       len([b for b in bounds if b["corpus"] == "st_marys_baptisms"]) == 13)

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
    withroll = {"id": "doe_john", "sources": ["x"], "dated_bounds": [], "note": "n"}
    apply_to_person(withroll, rows[0])
    ok("and it lands after T-1326's block where a card carries one",
       list(withroll) == ["id", "sources", "dated_bounds", BLOCK, "note"])

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
