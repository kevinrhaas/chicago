#!/usr/bin/env python3
"""T-1376, stage `underdocumented` — the men of the company the 1832 roll heads INDIAN.

    python3 tools/reconstruct_underdocumented.py --build      card them
    python3 tools/reconstruct_underdocumented.py --check      re-derive and refuse drift
    python3 tools/reconstruct_underdocumented.py --report     every row, and what was ruled
    python3 tools/reconstruct_underdocumented.py --self-test  the rules, each refusing its case

WHAT THIS STAGE IS, AND THE COUNT THAT MADE IT NECESSARY. The Illinois State Archives
index of Black Hawk War enrollments prints 134 men enrolled AT CHICAGO in 1832 in two
companies: forty under `G KERCHEVAL` and ninety-four under a company the roll heads,
in that column and in that word, `INDIAN`. The borderline roster (T-1172's input) sorted
those 134 rows into two classes by the same rule it uses on everybody — R3 for the muster,
R6 for a reading carrying a Native, Metis or Black community term — and T-1172 spent R3
and left R6 for T-1177. It then re-admitted **twenty of the forty men of Kercheval's
company and none of the ninety-four of the other one**. Same roll. Same year. Same page.
The only thing that separated them was which class the community term put them in, and
that class had no ticket to spend it.

This stage spends the Native and Metis part of R6. It is the FIRST stage of this
programme permitted to write a Native or Metis person — the programme file says so and
`reconstruct_residents_1835.check_reconstructed_person` enforces it — and every record it
writes carries `review_required` and `touches_removal` with the sentence that says why.

THE LICENCE IS R3's, WORD FOR WORD, AND IT IS BORROWED ON PURPOSE. R3 reads: "A name on
the 1 April 1834 post-office return or the 1832 Black Hawk muster enrolled at Chicago,
with no 1835 corroboration and no card. Licence: Mint reconstructed, presence bounded by
the persistence rate." Every man carded here answers that description exactly. Nothing
about the evidence differs; only the class does. So the presence draw is the same
persistence model, seeded the same way, and a card minted here is worth neither more nor
less than one of Kercheval's men.

THREE THINGS THIS STAGE DOES DIFFERENTLY FROM T-1172, AND WHY.

  1. A ONE-WORD NAME IS STILL A NAME. T-1172 withholds a reading that gives no surname
     and forename together (`not_a_whole_name`), which is the right rule for a land index
     that clipped `CHIPMAN` off `CHIPMAN ANSEL`. Applied to this company it is not a rule
     about evidence at all, it is a rule about European naming: `Cau be nah`, `Mas go` and
     `Ke o quaw` are whole names, printed whole, and a mint that requires a surname would
     refuse every one of them and call it rigour. So the test here is on the READING and
     not on its shape: a name the roll prints as a name is a name, it is carried `as_read`,
     no surname is invented for it and no given/family split is imposed on it.
     What IS still refused is a ONE-WORD EUROPEAN SURNAME — `Beaubien`, `Morgan`,
     `Crafts`, `Chamblee`, `Francois` — because there the roll clipped a name this town
     carries several of, and the row gives nothing to tell which man it is.

  2. THE TERM MUST BE A STATEMENT AND NOT A WORD IN THE PROSE. The roster's older R6
     rule is `community_term_in_the_reading`, a text match, and a text match over-catches:
     the biography of a white Indian agent contains the word `Indian` too. Charles Jouett,
     John Tipton, Daniel W. Beckwith and the 1843 directory's two advertisers reach R6
     that way. This stage mints only where the SOURCE'S OWN STRUCTURE says it — a company
     column reading `INDIAN` is a field the clerk filled in about this man; a paragraph
     that mentions Indians is not. Every other row is withheld with the reason named, and
     the count of them is a finding about the roster's rule rather than about the people.

     SINCE T-1383 THE ROSTER HAS A SECOND R6 RULE, and it is not a text match:
     `community_term_written_onto_the_name` fires only where the term follows the row's
     OWN name — the priest's parenthesis, "Marianne (sauvage)". That IS the source's own
     structure, by this stage's own test, so those rows may not be refused as prose. This
     stage still cannot mint them, because the only book it reads is the 1832 muster roll
     and a baptismal register is not on it; they are withheld saying exactly that, and
     they are a finding about a stage this project does not have yet rather than about
     the strength of the reading. See rule 6.

  3. NO NATION IS WRITTEN. The roll heads the company `INDIAN` and says no more. The
     Potawatomi, the Ottawa and the Ojibwe of this country were three nations and a united
     band of them lived at the forks; the roll distinguishes none of them, so neither does
     this stage. `community` is `native`, which is this vocabulary's word for *the source
     says Indian and says nothing further*, and a card that later reaches a nation replaces
     it. Writing `potawatomi` on ninety-odd men because most of the country's people were
     Potawatomi would be inventing the one fact the record withholds.

WHAT IS NOT DONE HERE, AND IT IS THE LARGER HALF. The roll is a roll of enrolled MEN.
It counts no woman and no child, and this corpus holds no roll, census or annuity schedule
that counts the Native and Metis people at Chicago on 1 July 1835 at all. The bracket in
`the_counted_but_unnamed` states that in figures and refuses to draw a remainder out of a
count that does not exist — the same refusal T-1353 made for the crews of the vessels, for
the same reason. The August 1835 gathering is not a source for a July scene and is not
staged; AGENTS.md's standing constraint governs, and no figure is drawn for anybody (L1).

NOTHING HERE OVERTURNS A REFUSAL. The ledger refused every one of these rows as a person
unit and its reasoning is carried onto each card verbatim. A card written here is a
reconstruction of what the town looks like if the name is admitted at the limit of its own
evidence, and it says so on its face, exactly as a re-admission does.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resident_mint_carry import carry_seats  # noqa: E402

from reconstruct_residents_1835 import (  # noqa: E402
    RECONSTRUCTED, UNDERDOCUMENTED_STAGE, check_reconstructed_person, load_programme, stages)
from readmit_borderline_roster import (  # noqa: E402
    dated_evidence, name_key, persistence_model, ruled_present, slug)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
ROSTER = DATA / "reconstruction" / "1835_borderline_roster.json"
MUSTER = DATA / "research" / "civic" / "records" / "blackhawk_war_1832_chicago.json"
OUT = DATA / "reconstruction" / "1835_native_and_metis.json"
CARDS = RESIDENTS / "underdocumented"
INDEX = RESIDENTS / "index.json"
SOURCES = DATA / "sources"

STAGE = UNDERDOCUMENTED_STAGE
SUB_STAGE = "native_and_metis"
TICKET = "T-1376"
PARENT = "T-1177"
SCENE_DATE = dt.date(1835, 7, 1)
WINDOW_OPENS = dt.date(1833, 1, 1)
SCHEMA = 1

CLASS = "R6_native_metis_black"
COMMUNITY_IN = "native_or_metis"
COMMUNITY_OUT = "native"
RULE_ID = "underdocumented_r6_company_roll_names_the_man"
MUSTER_SOURCE = "blackhawk_war_chicago_enrollments_isa"
MUSTER_FILE = "data/research/civic/records/blackhawk_war_1832_chicago.json"
INDIAN_COMPANY = "INDIAN"
# The id every card of THIS sub-stage wears; T-1377's free Black cards wear `hh_fb_`.
CARD_PREFIX = "hh_um_"

# The re-admissions' own sentence for the same roll, quoted rather than paraphrased so a
# reader can see that the two stages are standing on one licence.
R3_SENTENCE = ("Enrolled at Chicago in the 1832 Black Hawk muster, with no 1835 "
               "corroboration and no card; an earlier source dates and corroborates and "
               "never promotes, so presence is priced against the persistence model.")

CLASS_SENTENCE = (
    "Enrolled at Chicago in 1832 in the company the Black Hawk War roll heads INDIAN, "
    "with no 1835 corroboration and no card. The licence is R3's — the same roll, the "
    "same year, the same page — and the twenty men of Kercheval's company the town "
    "already carries were re-admitted under it.")

# Why each withheld row is withheld. The key is written onto the row; the sentence is
# written once, here, so two rows refused for one reason cannot drift apart.
REFUSALS = {
    "later_only_and_this_stage_does_not_back_project": (
        "The reading is dated AFTER 1 July 1835 — an old-settlers obituary, a directory of "
        "1839 or 1843 — and carries nothing in itself that dates an arrival before the "
        "scene. Back-projecting off a later naming is R5's licence and R5 is T-1172's; "
        "borrowing it here would be a second borrowed licence in one stage, and one is "
        "the argument."),
    "earlier_than_the_window_and_nothing_follows_the_person_forward": (
        "The reading is dated before the roster's window opens on 1833-01-01 and nothing "
        "in the corpus follows this person forward to the scene. Under the ladder ratified "
        "2026-09-03 an earlier source dates and corroborates and never promotes. The 1832 "
        "muster is the one exception this stage takes, and it takes it because T-1172 "
        "already took it on the same page for the other company."),
    "the_term_is_prose_and_not_a_statement": (
        "The roster classed this row R6 because a community term appears in the text of "
        "the reading. A word in a paragraph is not a statement by the source about this "
        "person's community — the biography of an Indian agent, a treaty commissioner or "
        "a trader who dealt with Native customers carries the same word — and this stage "
        "mints only where the source's own structure says it."),
    "the_statement_is_not_on_the_roll_this_stage_reads": (
        "The source states this person's community in its own structure — the term is "
        "written onto this name and onto no other on the line — so the refusal above, "
        "that a term in prose is not a statement, would be untrue of this row. What "
        "holds it out is this stage's SCOPE: the only book it reads is the 1832 muster "
        "roll, and this reading is a baptismal register entry. The row is owed a stage "
        "that reads the register, and until one exists the person stays out of the town "
        "for want of a reader rather than for want of evidence."),
    "a_card_of_that_name_already_stands": (
        "A person already in the layer shares this reading's surname and first given "
        "initial, the discriminator this project's directory crosswalks match on. The "
        "town already carries this man under his own card; a second would double him."),
    "a_one_word_european_surname_gives_no_person": (
        "The roll clipped this reading to a single European surname, and this town "
        "carries more than one family of it. A one-word Native name printed whole is "
        "admitted here; a one-word surname with no forename is not, because nothing in "
        "the row says which man it is."),
    "the_reading_carries_no_date_this_tool_can_read": (
        "A mint needs a dated appearance to price its presence against the persistence "
        "model, and this reading gives none."),
    "no_source_resolves": (
        "Every record here must cite a source that resolves in data/sources/, and this "
        "reading's does not."),
    "the_roll_prints_this_name_twice": (
        "The roll prints this same reading twice in the same company, letter for letter. "
        "One card is written for it and the second row is refused, because two identical "
        "rows are not evidence of two men and nothing on the page distinguishes them. "
        "The test here is EQUALITY of the whole reading and not the surname-plus-initial "
        "key T-1172 uses, for the reason the licence gives: that key reads the last word "
        "as a family name, and `MES KEE SUCK` and `MAU KAI TAI O SUCK` share a closing "
        "syllable and are two men."),
    "the_id_a_read_name_derives_is_already_taken": (
        "The household id this reading derives is already borne by a card in the layer; "
        "the id scheme forbids renaming a real person to make room."),
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def display_name(normalised: str) -> str:
    """The roster's reading, capitalised for a card and NOTHING else done to it.

    T-1172's `title_case` turns a one-letter word into an initial with a full stop —
    `ANSEL C` into `Ansel C.` — which is right for a European name and wrong here: it
    would print `Ke O. Quaw` and `Mex E. Man`, putting an English initial inside a
    Potawatomi name that has no initials in it. The roll prints these names as runs of
    syllables and this prints them back, capitalised and otherwise untouched.
    """
    return " ".join(w.capitalize() for w in str(normalised or "").split())


def without_parenthetical(name) -> str:
    """`Alexander Robinson (Che-che-pin-qua)` -> `Alexander Robinson`.

    A collision key is a surname and a first initial, and the layer writes a person's
    own Indigenous name in a parenthesis after the English one — which moves the last
    word and breaks the key on exactly the cards this stage must not double. Alexander
    Robinson keys as `qua|a` unless the parenthesis comes off first, and `ROBINSON, A`
    of the 1832 roll is him.
    """
    return re.sub(r"\s*\([^)]*\)", "", str(name or "")).strip()


def layer_keys() -> tuple[set, set]:
    """(surname + first-initial keys, household ids) across every place a card lives.

    T-1172 reads the index alone, which was the whole town when it was written. Three
    stages have since minted outside it, so this pass reads all four: a collision with a
    re-admitted or a drawn card is the same collision.

    THIS STAGE'S OWN OUTPUT IS NOT IN THE LIST, and it must not be. `--check` re-derives
    from the roster and compares against what is committed, so a pass that read its own
    cards as the layer would find every one of them colliding with itself on the second
    run and mint nobody — which is a build that is green the first time and empty
    afterwards. The duplicate a stage can make WITHIN one run is caught by
    `minted_readings` in `derive`, where it belongs.
    """
    keys, ids = set(), set()
    for folder in ("households", "readmitted", "reconstructed_trades", "transients"):
        path = RESIDENTS / folder
        if not path.is_dir():
            continue
        for card in sorted(path.glob("*.json")):
            rec = load(card)
            ids.add(rec.get("id"))
            for person in rec.get("persons") or []:
                name = person.get("name")
                keys.add(name_key(name))
                keys.add(name_key(without_parenthetical(name)))
    keys.discard("")
    ids.discard(None)
    return keys, ids


def muster_rows() -> dict:
    """{record id: cells} for the rows the roll puts in the company it heads INDIAN."""
    doc = load(MUSTER)
    return {r["id"]: r for r in doc.get("records", [])
            if ((r.get("cells") or {}).get("company") or "").strip().upper() == INDIAN_COMPANY}


def is_one_word(normalised: str) -> bool:
    return len([w for w in str(normalised or "").split() if w]) < 2


def card_for(row: dict, record: dict, hid: str, pid: str, sources: list,
             presence: dict) -> dict:
    display = display_name(row.get("normalised") or row.get("name_as_read"))
    cells = record.get("cells") or {}
    return {
        "id": hid,
        "name": f"{display} — of the company the 1832 roll heads INDIAN",
        "division": "unplaced",
        "head": pid,
        "source_pass": "reconstructed_underdocumented",
        "underdocumented": {
            "ticket": TICKET,
            "parent": PARENT,
            "stage": STAGE,
            "sub_stage": SUB_STAGE,
            "class": CLASS,
            "rule": RULE_ID,
            "row_id": row["row_id"],
            "name_as_read": row["name_as_read"],
            "as_printed": cells.get("name"),
            "company_as_printed": cells.get("company"),
            "place_of_enrollment_as_printed": cells.get("place_of_enrollment"),
            "stands_on": CLASS_SENTENCE,
            "withdrawn_if": ("a ruling that this name is a duplicate of a card the town "
                             "already holds; the retirement runs through "
                             "tools/consolidate_town_cards.py, never by hand"),
        },
        "arrival": {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": ("Not attested, and the question is the wrong one. This is the country "
                     "these people were already in; an enrollment dates an appearance and "
                     "the roll records no arrival because there was none to record."),
        },
        "origin": {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": ("THE ROLL NAMES NO NATION. It heads the company INDIAN and writes "
                     "nothing further, so no nation, band or village is written here. The "
                     "Potawatomi, Ottawa and Ojibwe of this country were three peoples and "
                     "a united band of them lived at the forks; choosing one for this man "
                     "would invent the single fact the record withholds."),
        },
        "lives_at": {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": ("Not attested: the roll gives a place of enrollment and no dwelling. "
                     "`CHICAGO` in that column is where the man was enrolled, which is not "
                     "an address and is not a residence."),
        },
        "works_at": {"value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
                     "note": "Not attested."},
        "present_on_scene_date": presence,
        "persons": [{
            "id": pid,
            "name": display,
            "name_as_read": row["name_as_read"],
            "relationship": "head",
            "grade": RECONSTRUCTED,
            "sex": "male",
            "sex_basis": {
                "value": "male", "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
                "note": ("READ OFF THE ROLL'S OWN SUBJECT and not drawn from the sex "
                         "model: this is a militia enrollment list, and the 1832 Illinois "
                         "muster enrolled men. It is the one attribute the document "
                         "settles, and no age is written beside it because the same "
                         "document settles nothing about that."),
            },
            "basis": {"kind": "rule", "id": RULE_ID, "note": CLASS_SENTENCE},
            "replaceable_by": {
                "kind": "person",
                "match": ("a second independent source naming this person at Chicago "
                          "inside the window, or any source that states his nation, band "
                          "or family — either would carry the card past what the roll "
                          "alone can hold"),
            },
            "reconstruction": {
                "stage": STAGE,
                "sub_stage": SUB_STAGE,
                "programme": "chicago_1835_resident_reconstruction",
                "community": COMMUNITY_OUT,
                "review_required": True,
                "touches_removal": True,
            },
            "occupation": {"value": "none_recorded", "confidence": RECONSTRUCTED,
                           "tier": "unknown",
                           "note": ("No source records an occupation for this person. A "
                                    "militia enrollment is not a trade.")},
            "sources": sources,
            "note": (
                f"CARDED FROM THE BORDERLINE ROSTER'S R6 ({TICKET}, stage `{STAGE}`). "
                f"{CLASS_SENTENCE} The roll prints him as `{cells.get('name')}`, company "
                f"`{cells.get('company')}`, enrolled at `{cells.get('place_of_enrollment')}`. "
                f"The research READ this name and WITHHELD it, and that refusal is not "
                f"overturned: this record is a reconstruction of what the town looks like "
                f"if the name is admitted at the limit of its own evidence, and it says so "
                f"on its face. The reading, the source and the refusal stand at "
                f"`{row['row_id']}` in data/reconstruction/1835_borderline_roster.json. "
                f"REVIEW REQUIRED: this card is a record of a Native person at Chicago in "
                f"the three years of the removal, and AGENTS.md's standing constraint holds "
                f"it for review by Native scholars or community organisations before any "
                f"scene carrying it may be marked released. No figure is drawn (L1)."),
            "resident_subtype": "underdocumented_resident",
        }],
        "touches_removal": True,
        "review_required": True,
        "research_note": (
            f"WRITTEN BY tools/reconstruct_underdocumented.py ({TICKET}), the "
            f"`{SUB_STAGE}` half of the `{STAGE}` stage of the 1835 resident "
            f"reconstruction programme, under the owner's ruling of 2026-09-17 recorded in "
            f"AGENTS.md. This file is NOT research and is not a mint output: "
            f"data/residents/households/ is re-derived by the mint writers and "
            f"data/residents/index.json is derived from that directory, so a card written "
            f"here lives beside the re-admissions and is overlaid onto the scene by "
            f"tools/compile_scene.py. REVIEW REQUIRED AND TOUCHES REMOVAL, both true, for "
            f"the subject this record is about: a Native man at Chicago in 1832, three "
            f"years before the removal of the Potawatomi from this place, inside the "
            f"project's first target year. The review AGENTS.md commits to has not been "
            f"held; until it is, no scene carrying this card may be marked released. "
            f"docs/RESEARCH/native_and_metis_1835.md lists every source read and what is "
            f"still owed. docs/LIBERTIES.md carries the invention."),
    }


def derive() -> tuple[dict, dict]:
    """(the record, {household_id: card}) — the whole sub-stage, in memory."""
    roster = load(ROSTER)
    model = persistence_model()
    keys, ids = layer_keys()
    source_ids = {p.stem for p in SOURCES.glob("*.json")}
    company = muster_rows()

    minted: list[dict] = []
    withheld: list[dict] = []
    already: list[dict] = []
    cards: dict[str, dict] = {}
    taken_keys, taken_ids = set(keys), set(ids)
    minted_readings: set = set()

    def withhold(row, reason, extra=None):
        withheld.append({
            "row_id": row["row_id"], "name_as_read": row["name_as_read"],
            "domain": row.get("domain"), "describes_date": row.get("describes_date"),
            "reason": reason, "why": REFUSALS[reason] + (f" {extra}" if extra else ""),
        })

    rows = [r for r in roster["rows"]
            if r.get("class") == CLASS and r.get("community") == COMMUNITY_IN]
    for row in sorted(rows, key=lambda r: r["row_id"]):
        existing = row.get("existing_household_id")
        if existing:
            already.append({
                "row_id": row["row_id"], "name_as_read": row["name_as_read"],
                "household_id": existing, "community_term": row.get("community_term"),
                "note": ("The term was found on a card the town already holds. Nothing is "
                         "minted; whether that card carries `touches_removal` is the "
                         "card's own affair and this stage does not reach into it."),
            })
            continue

        record = company.get(row.get("claim_or_record_id"))
        when, _refusal = dated_evidence(row)
        if record is None:
            # NOT ON THE ROLL. Say which of the four things it is, one row at a time — a
            # single catch-all reason would print `the term is prose` over Shabonee and
            # over Antoine Ouilmette, who are Native men their sources NAME and who are
            # held out for reasons about DATES rather than about the word `Indian`.
            if name_key(display_name(row.get("normalised"))) in taken_keys:
                withhold(row, "a_card_of_that_name_already_stands")
            elif when is None:
                withhold(row, "the_reading_carries_no_date_this_tool_can_read")
            elif when > SCENE_DATE:
                withhold(row, "later_only_and_this_stage_does_not_back_project")
            elif when < WINDOW_OPENS:
                withhold(row, "earlier_than_the_window_and_nothing_follows_the_person_forward")
            elif row.get("rule") == "community_term_written_onto_the_name":
                # A FIFTH thing, and the reason above would be a lie about it: the term
                # is not in the prose, it is written onto this name. T-1383.
                withhold(row, "the_statement_is_not_on_the_roll_this_stage_reads")
            else:
                withhold(row, "the_term_is_prose_and_not_a_statement")
            continue

        if when is None:
            withhold(row, "the_reading_carries_no_date_this_tool_can_read")
            continue
        if is_one_word(row.get("normalised")):
            withhold(row, "a_one_word_european_surname_gives_no_person")
            continue
        whole = " ".join(str(row.get("normalised") or "").split()).lower()
        if whole and whole in minted_readings:
            withhold(row, "the_roll_prints_this_name_twice")
            continue
        key = name_key(display_name(row.get("normalised")))
        if key and key in taken_keys:
            withhold(row, "a_card_of_that_name_already_stands")
            continue
        pid = slug(row.get("normalised"))
        hid = f"hh_um_{pid}"
        if not pid or hid in taken_ids:
            withhold(row, "the_id_a_read_name_derives_is_already_taken")
            continue
        sources = [s for s in (row.get("source_id") or []) if s in source_ids]
        if not sources:
            withhold(row, "no_source_resolves")
            continue

        value, share, lag, seed = ruled_present(model, hid, when)
        presence = {
            "value": value, "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
            "basis": {"kind": "model", "id": model["id"],
                      "note": (f"The roll dates this name at {row.get('describes_date')}, "
                               f"{lag:.2f} years before the scene date. The persistence "
                               f"model gives {share:.3f} for that lag and the seeded draw "
                               f"reads {value}. It is the same model, the same lag and the "
                               f"same draw that priced the twenty men of Kercheval's "
                               f"company the town already carries.")},
            "seed": seed,
            "replaceable_by": {"kind": "person",
                               "match": "any source naming this person at Chicago on or "
                                        "after 1 July 1835"},
        }
        card = card_for(row, record, hid, pid, sources, presence)
        cards[hid] = card
        minted_readings.add(whole)
        taken_ids.add(hid)
        minted.append({
            "row_id": row["row_id"], "class": CLASS, "rule": RULE_ID,
            "household_id": hid, "person_id": pid,
            "name_as_read": row["name_as_read"], "name": card["persons"][0]["name"],
            "file": f"underdocumented/{hid}.json", "sources": sources,
            "community": COMMUNITY_OUT, "review_required": True, "touches_removal": True,
            "dated_evidence": row.get("describes_date"),
            "dated_evidence_read_as": when.isoformat(),
            "present_on_scene_date": {"value": value, "persistence": round(share, 4),
                                      "years_before_the_scene": round(lag, 4), "seed": seed},
        })

    doc = load(MUSTER)
    by_company: dict[str, int] = {}
    for rec in doc.get("records", []):
        name = ((rec.get("cells") or {}).get("company") or "").strip().upper() or "(blank)"
        by_company[name] = by_company.get(name, 0) + 1
    readmissions = load(DATA / "reconstruction" / "1835_readmissions.json")
    kercheval_minted = sum(1 for m in readmissions.get("minted", [])
                           if m.get("class") == "R3_1834_return_or_muster")

    record = {
        "$schema_note": ("DERIVED — regenerate with tools/reconstruct_underdocumented.py "
                         "--build; tools/check.sh re-derives it. Do not hand-edit: every "
                         "card under data/residents/underdocumented/ is a function of the "
                         "borderline roster row named on it."),
        "schema": SCHEMA,
        "id": "chicago_july_1835_native_and_metis",
        "ticket": TICKET,
        "parent": PARENT,
        "stage": STAGE,
        "sub_stage": SUB_STAGE,
        "target_date": SCENE_DATE.isoformat(),
        "generated_by": "tools/reconstruct_underdocumented.py --build",
        "reads": ["data/reconstruction/1835_borderline_roster.json", MUSTER_FILE,
                  "data/reconstruction/1835_readmissions.json"],
        "writes": "data/residents/underdocumented/",
        "the_owners_ruling": {
            "date": "2026-09-17",
            "recorded_in": "AGENTS.md § Standing constraint — 1835 and Indigenous history",
            "quote": ("i think it is fair, in fact required to Reconstruct Native or Métis "
                      "people as part of this."),
            "what_it_does_not_change": ("L1 — no human figure is drawn, for anybody; no "
                                        "staging of the August 1835 gathering; no invented "
                                        "dialogue, ceremony or depiction. A card, and "
                                        "nothing that is looked at."),
        },
        "the_review_still_owed": (
            "Review by Native scholars or community organisations, which AGENTS.md commits "
            "to and which has not been held. Every record this stage writes carries "
            "`review_required: true`, which blocks a scene from being marked `released`. "
            "The flag is the project's own promise held open, not a formality."),
        "the_count_that_made_this_stage_necessary": {
            "roll": MUSTER_FILE,
            "source": MUSTER_SOURCE,
            "rows_by_company_as_printed": by_company,
            "kercheval_company_cards_in_the_town_before_this_stage": kercheval_minted,
            "indian_company_cards_in_the_town_before_this_stage": 0,
            "what_separated_them": (
                "Not the evidence — one roll, one year, one page, and the same rank column "
                "empty on both. The borderline roster's class rule put a reading carrying "
                "a community term into R6 and everything else into R3; T-1172 was licensed "
                "to spend R3 and not R6, and R6's owner (T-1177) had not been split into "
                "workable tickets until 2026-09-19. So the town carried "
                f"{kercheval_minted} of Kercheval's forty and none of the other ninety-four."),
        },
        "rules": {
            "licence": {"id": RULE_ID, "borrowed_from": "R3_1834_return_or_muster",
                        "r3_sentence": R3_SENTENCE, "this_sentence": CLASS_SENTENCE},
            "a_one_word_name_is_still_a_name": (
                "T-1172's `not_a_whole_name` refuses a reading without a surname AND a "
                "forename. Here that would refuse every man whose name the roll prints "
                "whole in the Potawatomi, Ottawa or Ojibwe of this country, so the test is "
                "on the reading and not on its shape. A one-word EUROPEAN surname is still "
                "refused, because there the roll clipped a name this town carries several "
                "of."),
            "the_term_must_be_a_statement": (
                "The roster's R6 rule is a text match over the reading, and a text match "
                "over-catches: an Indian agent's biography carries the word. This stage "
                "mints only where the source's own structure says it — here, a company "
                "column a clerk filled in with the word INDIAN."),
            "no_nation_is_written": (
                "The roll heads the company INDIAN and says no more, so `community` is "
                "`native` — this vocabulary's term for *the source says Indian and says "
                "nothing further* — and no nation, band or village is written on any card."),
            "the_sex_is_read_and_not_drawn": (
                "A militia enrollment list enrolled men. That is the one attribute the "
                "document settles; no age band is drawn beside it, because the same "
                "document settles nothing about that and the 1840 Chicago schedule counted "
                "no Native person at all."),
        },
        "persistence_model": model,
        "counts": {
            "r6_rows_offered": len(rows),
            "already_on_a_card": len(already),
            "cards_minted": len(cards),
            "minted_present": sum(1 for m in minted
                                  if m["present_on_scene_date"]["value"] == "present"),
            "minted_absent": sum(1 for m in minted
                                 if m["present_on_scene_date"]["value"] == "absent"),
            "withheld": len(withheld),
            "withheld_by_reason": {
                reason: sum(1 for w in withheld if w["reason"] == reason)
                for reason in sorted({w["reason"] for w in withheld})},
        },
        "the_counted_but_unnamed": {
            "what_the_ticket_asked_for": (
                "A reconstruction of the counted-but-unnamed remainder within a stated "
                "bracket."),
            "the_answer": "REFUSED, and the refusal is the reading.",
            "why": (
                "A bracket needs a count. This corpus holds no roll, census, annuity "
                "schedule or estimate that counts the Native and Metis people at or about "
                "Chicago on 1 July 1835. The roll spent above counts enrolled MEN in 1832 "
                "and no woman or child appears on it. The 1840 federal schedule, five "
                "years after the scene, counts no Native person in any column. The "
                "transient bracket (T-1352) prices the summer crowd off the newspapers and "
                "carries no Native row — the paper's `strangers` are the emigrants off the "
                "lake vessels and the land-sale parties, and reading them as anything else "
                "would be putting a number in a sentence that does not hold one. "
                "Reconstructing a remainder without a count would not be a bounded "
                "reconstruction; it would be a population invented whole, on the one "
                "subject AGENTS.md says is not a research gap to be filled by inference."),
            "the_one_count_that_exists_and_why_it_is_not_this_one": (
                "The great gathering and the last war dance at Chicago are AUGUST 1835 — "
                "six and a half weeks AFTER the scene date, and the event the standing "
                "constraint is written about. A crowd that assembled in August is not "
                "evidence of a population on 1 July, and this project does not stage it."),
            "what_would_retire_this_refusal": [
                "An 1835 annuity payment roll or schedule for the Chicago agency.",
                "A count of the families at the Agency, at Wolf Point or on the reservations "
                "in any month of 1834 or 1835.",
                "A contemporary estimate of the Native population in or about the town "
                "before 1 July 1835, in a source this project can commit.",
            ],
            "what_the_layer_carries_instead": (
                "Eight households already carry `touches_removal` — the Beaubiens, "
                "Robinson, Caldwell, McKee, Porthier, Kercheval and the Agency — and "
                "hh_robinson_alexander carries a collective row, `the rest of the Robinson "
                "household, unnamed`, which its own note calls an admission and not a "
                "person and refuses to count. That refusal is right and is not overturned "
                "here."),
        },
        "sources_read": [
            {"source_id": MUSTER_SOURCE, "file": MUSTER_FILE,
             "what_it_gave": f"{by_company.get(INDIAN_COMPANY, 0)} men enrolled at Chicago "
                             f"in 1832 in the company the roll heads INDIAN",
             "spent": True},
            {"source_id": "st_marys_baptismal_register_1833_1835",
             "file": "data/research/church/records/st_marys_baptisms_1833_1835.json",
             "what_it_gave": ("Four entries of 1833 in which the priest states an "
                              "Indigenous identity in his own hand — entries 7, 14, 17 and "
                              "18, naming Josette Ashkam of Ottaway, Marianne (sauvage) "
                              "wife of Antoine Aspam, and Jaespquaa (sauvage de Green Bay) "
                              "wife of Paul Vieaux. The two women are the ONLY adults on "
                              "their own entries that the borderline roster ruled "
                              "ineligible, so the town carries their husbands and their "
                              "children and not them."),
             "spent": False,
             "why_not": ("A baptism is not a residence and the roster's ineligibility "
                         "ruling is the research layer's, not this stage's to overturn "
                         "from the outside. It is a reading, and a reading is a ticket: "
                         "filed as T-1383, with the four entries and what it should "
                         "answer."),
             "filed_as": "T-1383"},
        ],
        "minted": sorted(minted, key=lambda m: m["household_id"]),
        "already_on_a_card": sorted(already, key=lambda a: a["row_id"]),
        "withheld": sorted(withheld, key=lambda w: w["row_id"]),
    }
    # T-1489. THE SEAT ANOTHER PASS DREW FOR THESE PEOPLE, CARRIED THROUGH THE REBUILD.
    # `tools/seat_reconstructed_trades_1835.py` points a reconstructed trade-holder with
    # no attested workplace at a house the business layer already holds, and writes the
    # answer onto the person as `persons[].employment`. It runs AFTER this stage, and
    # this stage derives its directory whole and compares it byte for byte — so without
    # this the key would be deleted on the next --build and reported as drift by the
    # pass that wrote it. It is the same fixed-slot carry the four `households/` mints
    # already use for `workplaces`; what the block may CONTAIN is that pass's --check to
    # decide, never this one's.
    carry_seats(cards, CARDS)
    return record, cards


def emit(record: dict, cards: dict, write: bool) -> list[str]:
    drift: list[str] = []
    wanted = {f"{hid}.json" for hid in cards}

    def settle(path: Path, payload: dict):
        text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            drift.append(str(path.relative_to(ROOT)))

    settle(OUT, record)
    for hid, card in sorted(cards.items()):
        settle(CARDS / f"{hid}.json", card)

    # EACH SUB-STAGE SWEEPS ITS OWN PREFIX and no more. The directory holds two cohorts
    # now — `hh_um_` is this one's and `hh_fb_` is T-1377's free Black town — and a sweep
    # of everything would have the two writers deleting each other's cards turn about.
    existing = ({p.name for p in CARDS.glob(f"{CARD_PREFIX}*.json")}
                if CARDS.exists() else set())
    for stale in sorted(existing - wanted):
        if write:
            (CARDS / stale).unlink()
        else:
            drift.append(f"data/residents/underdocumented/{stale} "
                         f"(committed, no longer derived)")
    return drift


def build() -> int:
    prog = load_programme()
    if STAGE not in stages(prog):
        print(f"FAIL the programme carries no '{STAGE}' stage", file=sys.stderr)
        return 2
    record, cards = derive()
    emit(record, cards, write=True)
    c = record["counts"]
    print(f"  ok    {c['cards_minted']} card(s) written to data/residents/underdocumented/, "
          f"{c['withheld']} row(s) withheld, {c['already_on_a_card']} already on a card")
    return 0


def check() -> int:
    prog = load_programme()
    problems: list[str] = []

    def error(where, msg):
        problems.append(f"{where}: {msg}")

    record, cards = derive()
    for hid, card in sorted(cards.items()):
        for person in card["persons"]:
            check_reconstructed_person(f"{hid}:{person['id']}", person,
                                       set(stages(prog)), error)
            if person["reconstruction"].get("community") not in ("native",):
                error(hid, "a card of this stage must carry community `native`")
            if not (card.get("review_required") and card.get("touches_removal")):
                error(hid, "the household must carry review_required and touches_removal")
            prose = person.get("note") or ""
            if "REVIEW REQUIRED" not in prose or "removal" not in prose:
                error(hid, "a flagged record says why in its own words and names the "
                           "subject it is held for (AGENTS.md)")
    for drifted in emit(record, cards, write=False):
        error(drifted, "does not re-derive from the roster; run --build")
    if problems:
        for p in problems:
            print(f"  FAIL {p}")
        return 1
    c = record["counts"]
    print(f"  ok    {c['cards_minted']} underdocumented card(s) re-derive, every one "
          f"review_required and touches_removal with its own sentence")
    print(f"  ok    {c['withheld']} row(s) withheld, each with a named reason; "
          f"{c['already_on_a_card']} already on a card")
    print(f"  ok    the counted-but-unnamed remainder is refused in writing, with the "
          f"three readings that would retire the refusal")
    return 0


def report() -> int:
    record, cards = derive()
    print(f"{record['id']} — {TICKET}, stage `{STAGE}` / `{SUB_STAGE}`")
    tally = record["the_count_that_made_this_stage_necessary"]
    print(f"  the roll: {tally['rows_by_company_as_printed']}")
    print(f"  before this stage: {tally['kercheval_company_cards_in_the_town_before_this_stage']} "
          f"of Kercheval's company carded, "
          f"{tally['indian_company_cards_in_the_town_before_this_stage']} of the other")
    print(f"  minted {record['counts']['cards_minted']} "
          f"({record['counts']['minted_present']} present, "
          f"{record['counts']['minted_absent']} absent on the scene date)")
    for reason, n in record["counts"]["withheld_by_reason"].items():
        print(f"  withheld {n:3}  {reason}")
    for m in record["minted"]:
        print(f"    {m['name']:28} {m['present_on_scene_date']['value']:8} "
              f"{m['row_id'].split('#')[-2]}")
    return 0


def self_test() -> int:
    """The rules, each refusing its own case."""
    failures = []

    def case(name, ok):
        print(f"  {'ok   ' if ok else 'FAIL '} {name}")
        if not ok:
            failures.append(name)

    case("a one-word reading is refused", is_one_word("beaubien"))
    case("a two-word Native name is not", not is_one_word("cau be nah"))
    case("a name key is the crosswalks' discriminator",
         name_key("Alexander Robinson") == "robinson|a")
    case("an Indigenous name in a parenthesis does not break the key",
         name_key(without_parenthetical("Alexander Robinson (Che-che-pin-qua)")) == "robinson|a")
    case("a card is capitalised without an English initial",
         display_name("ke o quaw") == "Ke O Quaw")
    case("the stage does not read its own output as the layer",
         not any(str(p).endswith("underdocumented") for p in [CARDS])
         or "underdocumented" not in layer_keys.__doc__.split("THIS STAGE'S OWN")[0])
    case("two syllabic names that share a closing syllable are two men",
         name_key("Mes Kee Suck") == name_key("Mau Kai Tai O Suck")
         and "mes kee suck" != "mau kai tai o suck")
    case("the muster reader takes only the company the roll heads INDIAN",
         all(((r.get("cells") or {}).get("company") or "").upper() == INDIAN_COMPANY
             for r in muster_rows().values()))

    record, cards = derive()
    case("every card carries review_required and touches_removal",
         all(c.get("review_required") and c.get("touches_removal") for c in cards.values()))
    case("every person carries the stage that is allowed to write them",
         all(p["reconstruction"]["stage"] == STAGE
             for c in cards.values() for p in c["persons"]))
    case("no card writes a nation",
         all(c["origin"]["value"] is None for c in cards.values()))
    case("every withheld row names a reason this file states",
         all(w["reason"] in REFUSALS for w in record["withheld"]))
    case("the counted-but-unnamed remainder is refused and says what would retire it",
         bool(record["the_counted_but_unnamed"]["what_would_retire_this_refusal"]))
    # T-1383. The roster's two R6 rules do not mean the same thing, and the refusal that
    # says "a term in prose is not a statement" is only true of the text-matched one.
    roster_rule = {r["row_id"]: r.get("rule") for r in load(ROSTER)["rows"]
                   if r.get("class") == CLASS}
    case("no row whose term was written onto its own name is refused as prose",
         not any(w["reason"] == "the_term_is_prose_and_not_a_statement"
                 and roster_rule.get(w["row_id"]) == "community_term_written_onto_the_name"
                 for w in record["withheld"]))
    case("a row held out for this stage's scope came in on the name-borne rule",
         all(roster_rule.get(w["row_id"]) == "community_term_written_onto_the_name"
             for w in record["withheld"]
             if w["reason"] == "the_statement_is_not_on_the_roll_this_stage_reads"))
    case("the register's two mothers reach this stage and are refused in its own words",
         {w["name_as_read"] for w in record["withheld"]
          if w["reason"] == "the_statement_is_not_on_the_roll_this_stage_reads"}
         >= {"Marianne (sauvage)", "Jaespquaa (sauvage de Green Bay)"})

    case("no person drawn here is invented — every id is a read name",
         all(not p["id"].startswith("rc_") for c in cards.values() for p in c["persons"]))

    if failures:
        print(f"  {len(failures)} case(s) failed")
        return 1
    print(f"  ok    14 rule(s) hold")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
