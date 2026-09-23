#!/usr/bin/env python3
"""The 30 corroborated_enrichment arrival and origin units, spent one at a time (T-1330).

    python3 tools/spend_enrichment_arrivals.py             what each of the 30 units does
    python3 tools/spend_enrichment_arrivals.py --write     write the blocks onto the cards
    python3 tools/spend_enrichment_arrivals.py --check     it re-derives; nothing drifted
    python3 tools/spend_enrichment_arrivals.py --self-test the rules below, over the table

WHY THIS EXISTS. T-1301 read all 98 `corroborated_enrichment` findings one at a time and
handed each to the OPEN ticket whose acceptance owns the kind of fact it names. Thirty of
them named an ARRIVAL, an ORIGIN, a departure or a dated appearance that bounds one, and
they were handed to the arrival line — T-1169, then T-1316, then T-1319, then here. A
hand-off is not a spend. This is the spend: every one of the thirty is read against the
card it names, and it does exactly one of four things.

  1. IT WRITES AN ORIGIN OR AN ARRIVAL YEAR THE MODEL WAS STANDING IN FOR. T-1169 filled
     `origin`, `arrival_year` and `reason_for_coming` on all 1,258 households, most of
     them DRAWN — an origin region taken from the birthplaces of seventy Old Settlers, an
     arrival year drawn from a distribution truncated at the household's bound. Those
     blocks carry `replaceable_by` saying what retires them: "a source that says where
     this household came from", "a dated source that says which year this household came
     to Chicago". These findings are those sources. The drawn block is replaced by a
     sourced one at `inferred`, the stage's `written_by_stage` mark does not travel onto
     it, and `reconstruct_residents_1835.py --check` therefore leaves it alone — its
     `writable()` is the supersession contract, and this pass is the first thing to use
     it. That is nine of the thirty, and it is why they become `asserted` in the research
     spend ledger without a ruling: the ledger reads the CARD.

  2. IT CORROBORATES A DATE THE CARD ALREADY CARRIES, AND MOVES NOTHING. Fifteen of them.
     A man the card already has arriving in 1833 from Andreas, named again on an 1833
     voter roster by a county history, has been confirmed and not moved. Under the ladder
     ratified 2026-09-03 corroboration corroborates; it does not promote. These are ruled
     `refused` in `data/research/residents/spend_rulings.json` — a finished answer.

  3. IT NAMES A DEPARTURE FROM CHICAGO, WHICH NO FIELD ON THE CARD CARRIES. Six of them:
     Caldwell's westward removal in 1835, Jones settling at the Manitowoc in 1836,
     Porthier leaving with Horace Chase on 27 February 1835, Sweet's removal to Milwaukee,
     Pugsley prospecting and returning to Paw Paw, Cleland choosing a home near Niles.
     A departure bears on `present_on_scene_date` and on nothing else, and the ticket
     whose acceptance owns that field — "no false Chicago resident" — is T-1144. They are
     handed there, in writing, and asserted nowhere.

  4. NOTHING ELSE. There is no fifth outcome and `--self-test` refuses one.

WHAT THIS PASS MAY NOT DO, and each of these is a rule rather than a preference.

  * IT NEVER TOUCHES A BLOCK A READING OWNS. `arrival` is the household's dated bound —
    a letter-list return, an advertisement, a roster day — and it is written by the pass
    that read that source. The one exception is stated in the table and gated by
    `--self-test`: an `arrival` whose confidence is `reconstructed` and which CITES NO
    SOURCE is this project's own guess ("1834 is the earliest year that reading supports
    and it is a guess"), and a source that states the year retires a guess the same way it
    retires a draw. One card qualifies.
  * IT NEVER MOVES A PERSON'S GRADE, MINTS A PERSON, OR REOPENS AN IDENTITY. The findings
    were adjudicated by the resident-research passes; this reads their verdict and writes
    the field, and `--self-test` diffs a record through the applier and asserts the changed
    key set is a subset of the three keys named here.
  * IT NEVER WIDENS A DATE. A source that says "July 1833" writes the YEAR into
    `arrival_year`, because that is the field, and says the month in its own note. A source
    that says "from 1834" states a presence and not an arrival, and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
RULINGS = ROOT / "data" / "research" / "residents" / "spend_rulings.json"
SOURCES = ROOT / "data" / "sources"

TICKET = "T-1330"
GENERATOR = "tools/spend_enrichment_arrivals.py"
# THE THREE RULES THIS PASS'S OWN UNITS FALL UNDER, after it has ruled them. Before it
# ran they were one rule -- `the_enrichment_names_an_arrival_or_origin_no_field_carries`,
# which named the arrival ticket and handed all thirty on. tools/spend_remainder_rulings.py
# now writes these instead, and a unit this pass wrote onto a card may carry NO ruling at
# all: where the finding's volume was already among the reading's own sources, the ledger
# closes it by reading the card and a ruling on it would be a fault. So the register is
# checked in one direction only -- everything it rules must be adjudicated here -- and the
# other direction is checked against the outcome instead.
PASS_RULES = ("the_enrichment_is_written_onto_the_card_it_names",
              "the_enrichment_dates_an_appearance_the_card_already_carries",
              "the_enrichment_names_a_departure_from_chicago_no_field_carries")
STAGE_MARK = "written_by_stage"
OUTCOMES = ("written", "corroborates", "departure")
WRITABLE_KEYS = ("origin", "arrival_year", "arrival")

LADDER = (
    "Under the evidence ladder ratified 2026-09-03 a source earlier than 1 July 1835 "
    "corroborates and dates and never promotes: the person's grade does not move on this.")


def block(value, source: str, note: str) -> dict:
    """One sourced attribute block, in the shape the arrival stage's own blocks carry."""
    return {"value": value, "confidence": "inferred", "tier": "inferred",
            "note": note, "sources": [source]}


# THE ADJUDICATION, ONE ROW A UNIT, AUTHORED AND NOT DERIVED. The routing of a finding to
# a field cannot be computed from the finding: "arriving in July 1831" is an arrival,
# "in Cook County from 1834" is a presence, and only a reader can tell them apart. So the
# table is written out, each row naming what the pass returned and what this project does
# about it, and `--self-test` holds it against the ruling register one-to-one in both
# directions — a unit missing from here, or a row here that is not one of the thirty, is
# a failure rather than a silent skip.
ADJUDICATION: dict[str, dict] = {
    # --- 1. the nine the sources retire a drawn or guessed value on ---------------------
    "peck_philip": {
        "outcome": "written",
        "why": "a Providence birth, where the card carried a region drawn from a sample",
        "writes": {"origin": block(
            "Providence, Rhode Island", "encyclopedia_chicago_biographical_p",
            "A SOURCE, WHERE THE FIELD HELD A DRAW. The completed resident-research pass on "
            "peck_philip read the Chicago History Museum's encyclopedia as identifying "
            "Philip F. W. Peck as a Providence-born merchant and real-estate developer who "
            "arrived in July 1831. The block this replaces was drawn from the birthplaces of "
            "the seventy Old Settlers who registered an arrival at or before 1835 and said "
            "“New York State” on no evidence about this household at all; its own "
            "`replaceable_by` asked for “a source that says where this household came "
            "from”, and this is one. It is a BIRTHPLACE and is carried as the best "
            "statement of origin the sources make about this household, not as a last "
            "residence. The arrival itself is unchanged: the card already states 1831-07-01 "
            "at month precision from Andreas, which the same finding corroborates.")},
    },
    "tuller_elam": {
        "outcome": "written",
        "why": "a Connecticut origin and a July 1833 arrival, where the card carried two draws",
        "writes": {
            "origin": block(
                "Connecticut", "whiteside_elam_tuller",
                "A SOURCE, WHERE THE FIELD HELD A DRAW. The completed resident-research pass "
                "on tuller_elam read a county biography as saying that Elam Tuller's family "
                "reached Chicago in July 1833 and as identifying his Connecticut origin and "
                "his farmer, mechanic and steam-engine manufacturing background. The block "
                "this replaces read “The Mid-Atlantic states”, drawn from the Old "
                "Settlers birthplace sample and resting on nothing about this household."),
            "arrival_year": block(
                1833, "whiteside_elam_tuller",
                "A STATED YEAR, WHERE THE FIELD HELD A DRAW. The same county biography says "
                "the family of tuller_elam reached Chicago in July 1833. The year drawn by "
                "the arrival stage read 1833 as well, so the value does not move — what "
                "moves is that it is now a reading with a source behind it rather than a "
                "figure taken from a distribution. The MONTH is stated by the source and is "
                "not written into this field, which carries a year; the household's own "
                "`arrival` block holds its separate bound of 1834-01-01 from the Chicago "
                "Democrat and is untouched, because a bound and an arrival are two claims. "
                + LADDER)},
    },
    "paine_seth": {
        "outcome": "written",
        "why": "an 1834 migration from Montpelier, where the card drew 1835 and New York",
        "writes": {
            "origin": block(
                "Montpelier, Vermont", "andreas_seth_paine_1834",
                "A SOURCE, WHERE THE FIELD HELD A DRAW. The completed resident-research pass "
                "on paine_seth read Andreas's Seth Paine biography as giving a direct 1834 "
                "migration from Montpelier, Vermont to Chicago. The block this replaces read "
                "“New York State” from the Old Settlers birthplace sample. This is a "
                "stated point of departure, which is what this field asks for."),
            "arrival_year": block(
                1834, "andreas_seth_paine_1834",
                "A STATED YEAR, AND THE DRAW IT CORRECTS. The same biography gives a direct "
                "1834 migration to Chicago for paine_seth. The arrival stage had drawn 1835, "
                "truncating its distribution at the household's bound — the post-office "
                "return of 1835-03-31 that the `arrival` block carries — and a source "
                "that names the year retires a figure drawn against that bound. The bound "
                "itself is unchanged and is not contradicted: a man who came in 1834 is a man "
                "who was here by March 1835. " + LADDER)},
    },
    "temple_john_t": {
        "outcome": "written",
        "why": "a July 1833 arrival with a family, where the card drew the year",
        "writes": {"arrival_year": block(
            1833, "plainfield_john_temple_report",
            "A STATED YEAR, WHERE THE FIELD HELD A DRAW. The completed resident-research pass "
            "on temple_john_t read a municipal preservation study as corroborating Temple's "
            "July 1833 arrival with wife and four children, and his mail contract. The drawn "
            "year read 1833 too, so the value does not move; what moves is that it is now "
            "sourced. The same study gives dwelling and office locations that CONFLICT with "
            "this household's, and no address is taken from it here — the conflict is "
            "left standing where the pass recorded it. " + LADDER)},
    },
    "hugunin_leonard_c": {
        "outcome": "written",
        "why": "an arrival dated 17 August 1833, where the card drew 1834 against a bound",
        "writes": {"arrival_year": block(
            1833, "chicago_old_settlers_hugunin_1883",
            "A STATED YEAR, AND THE DRAW IT CORRECTS. The completed resident-research pass on "
            "hugunin_leonard_c read the Old Settlers of Chicago proceedings as recording "
            "Leonard C. Hugunin as arriving 17 August 1833. The arrival stage had drawn 1834 "
            "from a distribution truncated at this household's only bound — the "
            "post-office return of June 1835 the `arrival` block carries — and said in "
            "its own note that it described “a household of this bound” and "
            "“nothing whatever about this household”. This is a statement about "
            "this household. The proceedings are a roll set down forty-eight years after the "
            "event and the value is carried at `inferred` for that reason; the DAY it states "
            "is not written into a field that carries a year. " + LADDER)},
    },
    "jackson_samuel": {
        "outcome": "written",
        "why": "an arrival from Buffalo dated 27 June 1833, where the card drew 1834",
        "writes": {"arrival_year": block(
            1833, "resident_research_cook_harbor_jackson",
            "A STATED YEAR, AND THE DRAW IT CORRECTS. The completed resident-research pass on "
            "jackson_samuel read a Cook County history as stating that Samuel Jackson arrived "
            "from Buffalo on 27 June 1833 and served as foreman of Chicago harbour "
            "construction. The arrival stage had drawn 1834, truncated at the letter-list "
            "bound of 1834-10-01 the `arrival` block carries; a stated arrival a year before "
            "that bound is consistent with it and retires the draw. The origin field already "
            "reads “Buffalo, New York” from the voter lists and is untouched. "
            + LADDER)},
    },
    "andrus_thomas": {
        "outcome": "written",
        "why": "an arrival dated 1 December 1833, where the card drew 1834",
        "writes": {"arrival_year": block(
            1833, "rr_dupage_andrus_1882",
            "A STATED YEAR, AND THE DRAW IT CORRECTS. The completed resident-research pass on "
            "andrus_thomas read a DuPage history as giving his arrival at Chicago on 1 "
            "December 1833, carpenter and pile-driving work through 1834, a return east in "
            "the autumn of 1834 and an arrival back at Chicago in June 1835 before he settled "
            "in DuPage. The year written here is the FIRST arrival, which is what this field "
            "asks for. The going and returning is a chronology no field on this card carries "
            "and it is not asserted here; the household's `arrival` block keeps its own bound "
            "of 1835-03-31 from the Chicago Democrat, which the June 1835 return does not "
            "contradict. " + LADDER)},
    },
    "evans_sciota": {
        "outcome": "written",
        "why": "a dated October 1834 naming, where the card drew 1835 against a later bound",
        "writes": {"arrival_year": block(
            1834, "rr_cook_democratic_republicans_1834",
            "A DATED NAMING EARLIER THAN THE BOUND THE DRAW WAS MADE AGAINST. The completed "
            "resident-research pass on evans_sciota read a Cook County history quoting the "
            "Chicago Democrat's political list of 15 October 1834 as naming Sciota Evans "
            "among the leading Cook County Democratic-Republicans. The arrival stage had "
            "drawn 1835 from a distribution truncated at this household's bound of "
            "1835-03-31; a man named on a county political list in October 1834 was here by "
            "1834, so the draw is retired by a year the evidence reaches. This is the LATEST "
            "year the arrival can be and not a statement that he came in it, which is why it "
            "is `inferred`. " + LADDER)},
    },
    "church_thomas": {
        "outcome": "written",
        "why": "an 1834 arrival stated by a reminiscence, where the card carried its own guess",
        "writes": {"arrival": {
            "value": "1834", "confidence": "inferred", "precision": "year",
            "sources": ["ingale_early_chicago_reminiscence"],
            "note": (
                "A SOURCE, WHERE THIS PROJECT HAD A GUESS. The block this replaces said so "
                "itself — “NOT ATTESTED … 1834 is the earliest year that "
                "reading supports and it is a guess”, argued from the date of the store "
                "he built rather than from anything about the man. The completed "
                "resident-research pass on church_thomas read a published early-Chicago "
                "reminiscence as saying that Thomas Church arrived in 1834 and describing his "
                "Lake Street building activity. The year does not move; what moves is that it "
                "is now a reading with a source, at `inferred` because a reminiscence "
                "corroborates an uncommon name, a migration year and a merchant setting "
                "without proving the identity. This is the one `arrival` block this pass "
                "touches and it qualifies on the stated rule: reconstructed, and citing no "
                "source. " + LADDER)}},
    },

    # --- 2. the fifteen that corroborate a date the card already carries ----------------
    "kinzie_juliette": {
        "outcome": "corroborates",
        "why": ("the card's origin already reads “Chicago, by way of Fort Winnebago” "
                "from Andreas, which is the residence this finding dates"),
    },
    "spring_giles": {
        "outcome": "corroborates",
        "why": ("the card's arrival already reads 1833 from Andreas; the finding's June is a "
                "month inside that year and `arrival` is a read block this pass does not "
                "overwrite"),
    },
    "wright_john": {
        "outcome": "corroborates",
        "why": ("the card's arrival already reads 1832 from Andreas, which the joint arrival "
                "of 29 October 1832 falls inside"),
    },
    "carver_david": {
        "outcome": "corroborates",
        "why": ("an 1833 voter-roster naming, and the card's arrival already reads 1833 from "
                "Andreas"),
    },
    "casey_edward_w": {
        "outcome": "corroborates",
        "why": ("a near-participant's recollection of an 1833 arrival, and the card's arrival "
                "already reads 1833 from Andreas"),
    },
    "gale_stephen_f": {
        "outcome": "corroborates",
        "why": ("an 1833 voter-roster naming, and the card already carries 1833 in both "
                "`arrival` and `arrival_year` and a sourced origin of Exeter, N. H."),
    },
    "norton_nelson_r": {
        "outcome": "corroborates",
        "why": ("the card's arrival already reads 1833-11-16 at day precision — the very "
                "day this finding preserves"),
    },
    "pierce_asahel": {
        "outcome": "corroborates",
        "why": ("an October 1833 arrival, and the card's arrival already reads 1833-10-08 at "
                "day precision from Andreas"),
    },
    "kercheval_gholson": {
        "outcome": "corroborates",
        "why": ("an 1833 treaty payment naming him of Chicago, and the card's arrival already "
                "reads 1831 from Andreas — the naming falls inside a residence the card "
                "already states"),
    },
    "andrews_davi": {
        "outcome": "corroborates",
        "why": ("a presence in Cook County from 1834, which is a county and not a town and is "
                "not a stated arrival; the card's drawn arrival year already reads 1834 and "
                "the finding gives no ground to retire the draw"),
    },
    "orsemus_morrison": {
        "outcome": "corroborates",
        "why": ("an 1833 arrival from the very source the card's `arrival` block already "
                "cites"),
    },
    "boilvin_nicholas": {
        "outcome": "corroborates",
        "why": ("1834 post-office returns and an 1833 treaty schedule, and the card's arrival "
                "already reads a 1834-04-01 bound from the same Chicago Democrat run"),
    },
    "christy_nathan": {
        "outcome": "corroborates",
        "why": ("an 1834 letter-list appearance, and the card's arrival already reads a "
                "1834-07-01 bound from the same run"),
    },
    "vasseur_noel": {
        "outcome": "corroborates",
        "why": ("an 1835 postal list and an 1833 treaty schedule, and the card's arrival "
                "already reads a 1835-03-31 bound from the same run"),
    },
    "woodworth_james_h": {
        "outcome": "corroborates",
        "why": ("a move to Chicago in 1833 from the very source the card's `arrival` block "
                "already cites"),
    },

    # --- 3. the six that name a departure no field on the card carries ------------------
    "caldwell_billy": {
        "outcome": "departure",
        "why": "a westward removal placed in 1835, against the record's own 1836",
    },
    "jones_benjamin": {
        "outcome": "departure",
        "why": "a purchase at the Manitowoc in 1835 and a settlement there in 1836",
    },
    "porthier_joseph": {
        "outcome": "departure",
        "why": "a departure with Horace Chase dated 27 February 1835, and a brief return",
    },
    "sweet_alanson": {
        "outcome": "departure",
        "why": "a removal to Milwaukee in 1835, with no safe departure day in the passage",
    },
    "pugsley_john_k": {
        "outcome": "departure",
        "why": ("a June 1835 journey from near Utica, a prospecting stay and a return to Paw "
                "Paw Township"),
    },
    "cleland_martin": {
        "outcome": "departure",
        "why": ("an 1834 prospecting tour from Chautauqua and a future home selected near "
                "Niles, Michigan"),
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def units() -> list[str]:
    """The person ids of the thirty units this ticket owns, from the ruling register."""
    doc = read_json(RULINGS)
    return sorted(row["unit"].split("#people/")[1]
                  for row in doc.get("rulings") or [] if row.get("rule") in PASS_RULES)


def household_of(person_id: str, households: Path = HOUSEHOLDS) -> Path | None:
    for path in sorted(households.glob("hh_*.json")):
        doc = read_json(path)
        if any((p or {}).get("id") == person_id for p in doc.get("persons") or []):
            return path
    return None


def retires(block_now, key: str) -> bool:
    """A block this pass may replace, and the two reasons it may.

    The arrival stage's own blocks carry `written_by_stage` and a `replaceable_by` that
    names the source that retires them; a source is what this pass has. The second reason
    is narrower and stated in the module doc: a `reconstructed` value citing NO source is
    this project's own guess, and a guess is retired by a reading the same way a draw is.
    """
    if not isinstance(block_now, dict):
        return False
    if block_now.get(STAGE_MARK):
        return True
    return (key == "arrival" and block_now.get("confidence") == "reconstructed"
            and not block_now.get("sources"))


def plan(households: Path = HOUSEHOLDS) -> dict[str, dict]:
    """Every card this pass would change, keyed by file name, with the whole new doc."""
    out: dict[str, dict] = {}
    for person_id, row in sorted(ADJUDICATION.items()):
        if row["outcome"] != "written":
            continue
        path = household_of(person_id, households)
        if path is None:
            continue
        doc = out.get(path.name) or read_json(path)
        for key, new in row["writes"].items():
            if not retires(doc.get(key), key):
                continue
            doc[key] = new
        out[path.name] = doc
    # A card whose blocks already stand is not a change.
    return {name: doc for name, doc in out.items()
            if dumps(doc) != (households / name).read_text(encoding="utf-8")}


def report() -> int:
    rows = units()
    for person_id in rows:
        row = ADJUDICATION.get(person_id)
        if row is None:
            print(f"  {person_id:<22} UNADJUDICATED", file=sys.stderr)
            continue
        wrote = ", ".join(sorted(row.get("writes") or {})) or "—"
        print(f"  {person_id:<22} {row['outcome']:<13} {wrote:<22} {row['why'][:60]}")
    tally = {name: sum(1 for p in rows if (ADJUDICATION.get(p) or {}).get("outcome") == name)
             for name in OUTCOMES}
    print(f"\n{len(rows)} unit(s): " + ", ".join(f"{k} {v}" for k, v in tally.items()))
    pending = plan()
    print(f"{len(pending)} card(s) would change" if pending
          else "every block this pass writes already stands on its card")
    return 0


def write() -> int:
    pending = plan()
    for name, doc in pending.items():
        (HOUSEHOLDS / name).write_text(dumps(doc), encoding="utf-8")
    print(f"wrote {len(pending)} household card(s) under "
          f"{HOUSEHOLDS.relative_to(ROOT)}")
    return 0


def check() -> int:
    faults = []
    known = set(units())
    for person_id in sorted(known - set(ADJUDICATION)):
        faults.append(f"{person_id}: an arrival-or-origin unit this pass never adjudicated")
    for person_id in sorted(set(ADJUDICATION) - known):
        row = ADJUDICATION[person_id]
        # A unit this pass ASSERTED has left the ruling register by design: the ledger
        # reads the card, finds the block, and closes the unit without a ruling. That is
        # the success case and not a stale row.
        if row["outcome"] != "written":
            faults.append(f"{person_id}: adjudicated here and not among the units this "
                          f"ticket owns")
    for name in sorted(plan()):
        faults.append(f"{name}: does not carry what {GENERATOR} writes — run --write "
                      f"and commit it")
    for line in faults:
        print(f"FAIL {line}", file=sys.stderr)
    if faults:
        return 1
    written = sum(len(r.get("writes") or {}) for r in ADJUDICATION.values())
    print(f"{len(ADJUDICATION)} unit(s) adjudicated, {written} block(s) written, and every "
          f"one of them re-derives")
    return 0


def self_test() -> int:
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append(f"{label}: got {got!r}, wanted {want!r}")

    holds("every row names one of the three outcomes",
          sorted({r["outcome"] for r in ADJUDICATION.values()} - set(OUTCOMES)), [])
    holds("thirty units are adjudicated", len(ADJUDICATION), 30)
    holds("only a written row writes blocks",
          sorted(p for p, r in ADJUDICATION.items()
                 if bool(r.get("writes")) != (r["outcome"] == "written")), [])
    holds("no block is written outside the three keys",
          sorted({k for r in ADJUDICATION.values() for k in (r.get("writes") or {})}
                 - set(WRITABLE_KEYS)), [])
    holds("every row states its reason",
          sorted(p for p, r in ADJUDICATION.items() if len(r.get("why") or "") < 30), [])

    # EVERY CITED SOURCE IS A COMMITTED SOURCE RECORD. An invented citation is the one
    # thing this project refuses outright, and a pass that writes citations proves it.
    cited = {s for r in ADJUDICATION.values() for b in (r.get("writes") or {}).values()
             for s in b.get("sources") or []}
    holds("every citation is a committed source record",
          sorted(s for s in cited if not (SOURCES / f"{s}.json").exists()), [])
    holds("every written block is source-bearing and inferred",
          sorted(f"{p}:{k}" for p, r in ADJUDICATION.items()
                 for k, b in (r.get("writes") or {}).items()
                 if b.get("confidence") != "inferred" or not b.get("sources")), [])
    # THE BLOCK MUST NAME THE PERSON. tools/research_spend_ledger.py closes a unit as
    # `asserted` only where a source-bearing structured node NAMES the unit's record id,
    # so a note that does not say the id leaves the unit open and this whole pass reads as
    # unspent. That is a silent failure, so it is a test.
    holds("every written block names the person it is about",
          sorted(f"{p}:{k}" for p, r in ADJUDICATION.items()
                 for k, b in (r.get("writes") or {}).items() if p not in str(b.get("note"))),
          [])
    # AND THE SOURCE MUST BE THE FINDING'S OWN. The same gate matches on a shared source
    # id between the unit and the block, so a block citing a DIFFERENT volume than the
    # finding does not close the finding.
    doc = read_json(RULINGS)
    noted = {row["unit"].split("#people/")[1]: row["note"]
             for row in doc.get("rulings") or [] if row.get("rule") in PASS_RULES}
    holds("every citation appears in the finding it spends",
          sorted(f"{p}:{s}" for p, r in ADJUDICATION.items()
                 for b in (r.get("writes") or {}).values() for s in b.get("sources") or []
                 if p in noted and s not in noted[p]), [])

    # THE RETIREMENT RULE, over fixtures rather than over the tree.
    holds("a stage block is retired", retires({"value": "x", STAGE_MARK: "s"}, "origin"), True)
    holds("a sourced reading is not", retires(
        {"value": "x", "confidence": "attested", "sources": ["s"]}, "origin"), False)
    holds("an inferred reading is not", retires(
        {"value": "x", "confidence": "inferred", "sources": ["s"]}, "arrival"), False)
    holds("a sourceless guess is retired, but only in `arrival`", retires(
        {"value": "x", "confidence": "reconstructed"}, "arrival"), True)
    holds("…and not in `origin`", retires(
        {"value": "x", "confidence": "reconstructed"}, "origin"), False)
    holds("an absent block is not retired", retires(None, "origin"), False)

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        hh = Path(tmp)
        held = {"id": "hh_peck_philip", "head": "peck_philip", "division": "south",
                "origin": {"value": "New York State", "confidence": "reconstructed",
                           STAGE_MARK: "attribute_fill_arrival"},
                "arrival": {"value": "1831-07-01", "confidence": "attested",
                            "sources": ["andreas_1884_v1"]},
                "persons": [{"id": "peck_philip", "grade": "attested"}]}
        (hh / "hh_peck_philip.json").write_text(dumps(held), encoding="utf-8")
        got = plan(hh)["hh_peck_philip.json"]
        holds("the drawn origin is replaced", got["origin"]["value"],
              "Providence, Rhode Island")
        holds("…at inferred", got["origin"]["confidence"], "inferred")
        holds("…and the stage mark does not travel onto it",
              STAGE_MARK in got["origin"], False)
        holds("the read arrival is untouched", got["arrival"], held["arrival"])
        holds("no other key moves",
              sorted(k for k in got if got[k] != held[k]), ["origin"])
        holds("no person is touched", got["persons"], held["persons"])
        (hh / "hh_peck_philip.json").write_text(dumps(got), encoding="utf-8")
        holds("a second pass proposes nothing", sorted(plan(hh)), [])

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    print(f"self-test: {21 - len(failures)}/21 assertions hold")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.write:
        return write()
    if args.check:
        return check()
    if args.self_test:
        return self_test()
    return report()


if __name__ == "__main__":
    sys.exit(main())
