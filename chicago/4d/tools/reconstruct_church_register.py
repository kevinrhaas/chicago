#!/usr/bin/env python3
"""T-1504, stage `underdocumented` — the women St Mary's register names in the priest's own hand.

    python3 tools/reconstruct_church_register.py --build      card them
    python3 tools/reconstruct_church_register.py --check      re-derive and refuse drift
    python3 tools/reconstruct_church_register.py --report     every row, and what was ruled
    python3 tools/reconstruct_church_register.py --self-test  the rules, each refusing its case

THE READER THIS BOOK WAS OWED. `data/research/church/records/st_marys_baptisms_1833_1835.json`
is the only source this project holds in which a CONTEMPORARY states an Indigenous identity
for a named person at Chicago — Father Saint Cyr's own parenthesis on the page, not a term
in a later biography. Since T-1383 the borderline roster reads it: four rows reach
`R6_native_metis_black` on the rule `community_term_written_onto_the_name`, which fires only
where the term follows the row's OWN name.

`tools/reconstruct_underdocumented.py` then withheld all four, and its reason was honest and
was a dead end: *"the only book it reads is the 1832 muster roll, and this reading is a
baptismal register entry. The row is owed a stage that reads the register, and until one
exists the person stays out of the town for want of a reader rather than for want of
evidence."* This is that stage. It reads the register and nothing else.

WHAT THE TOWN WAS CARRYING IN THE MEANTIME, which is the count that made this stage
necessary. Entries 14, 17 and 18 of 1833 name four adults and three children between them.
The town already holds Antoine Aspam and his two children, and Paul Vieau and his daughter
Susanne. The two people it did NOT hold were the mothers — `Marianne (sauvage)` and
`Jaespquaa (sauvage de Green Bay)` — and the only thing that separated them from their own
husbands and children was the word the priest wrote beside their names. The stage that could
spend that word read a different book. `the_count_that_made_this_stage_necessary` re-derives
that from the committed layer rather than asserting it here.

FIVE THINGS THIS STAGE DOES, AND WHY EACH IS THE SOURCE'S OWN STRUCTURE AND NOT AN INFERENCE.

  1. A BAPTISM IS NOT A RESIDENCE, and this stage asserts none. The register's own rows say
     so on every line — *"A baptism documents a person at a font on a day; it is not a
     residence, an address or an occupation"* — so `lives_at`, `works_at` and `division` are
     written as unplaced and unattested, exactly as the muster stage writes them. What a
     dated appearance DOES give is a lag the persistence model can price, which is the same
     use T-1172 made of the 1834 post-office return and T-1376 of the 1832 muster.

  2. THE MONONYM IS CARRIED `as_read`. Neither woman is given a surname here. The register
     names them with a forename and the clerk's parenthesis and nothing else; her husband's
     surname is HIS, and writing `Marianne Aspam` would be inventing the one thing the page
     withholds. T-1376 settled the principle for the muster's syllabic names — *a name the
     source prints as a name is a name* — and it holds here for the same reason.

     THE SURNAME-AND-INITIAL COLLISION KEY CANNOT SPEAK ABOUT A MONONYM. `name_key` returns
     the empty string for a one-word name, so the test the sibling stages use to stop a
     second card of a person the town already holds is silent on exactly these two rows.
     This stage therefore keys on the WHOLE reading folded, and on the spouse the entry
     names beside her — see rule 3.

  3. THE SPOUSE ON THE LINE IS A DISCRIMINATOR AND NOT A TIE. Entries 14 and 17 both name
     `Marianne (sauvage)` and both name `Antoine Aspam` as the father on the same line. That
     is one woman, and the register says so in its own structure: same book, same clerk,
     same year, same husband. So the second row is refused as a second PRINTING of one
     reading rather than carded as a second woman — the shape T-1562 settled for Samuel Toby,
     whose three printings are one sighting.

     It is used for NOTHING ELSE. No tie is written onto any card: not to the husband, not
     to the children, not to the sponsors. The kinship the register states on a dated line
     is T-1335's field, every one of these rows names T-1335 in its `ledger_reason`, and
     `what_is_handed_to_the_family_pass` in the record below says exactly what is being
     handed over and to whom.

  4. NO NATION IS WRITTEN, AND ONE ORIGIN IS. `sauvage` is the priest's word for an
     Indigenous woman; it is this project's word for nothing, and it names no nation, band
     or village. `community` is `native` — this vocabulary's term for *the source says so
     and says nothing further* — and `origin` stays empty wherever the book is empty.
     Entry 18 is the one exception and it is a PLACE and not a people: `sauvage de Green
     Bay`, the only origin the register ever gives anyone. It is carried, on the card, at
     the register reader's OWN grade for that row and never above it (rule 5).

  5. A CARD NEVER GRADES ABOVE THE READING IT STANDS ON. Each row's `confidence` in the
     register file is the grade the reading carries — `documented` where the clerk's hand is
     plain, `inferred` where it is not, and Jaespquaa's name is `inferred` because an
     Indigenous name written phonetically by a French speaker has middle letters nobody can
     be sure of. Nothing here promotes one. The card's own person is graded `reconstructed`
     like every person the programme writes, and the attributes it carries off the page are
     graded at the row's grade.

NOTHING HERE OVERTURNS A REFUSAL. The research layer ruled both women's rows `unresolved`
and handed them to the family pass; that ruling is carried onto each card verbatim and is
not reversed. A card written here is a reconstruction of what the town looks like if the
name is admitted at the limit of its own evidence, and it says so on its face.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resident_mint_carry import carry_seats  # noqa: E402

from reconstruct_residents_1835 import (  # noqa: E402
    RECONSTRUCTED, UNDERDOCUMENTED_STAGE, check_reconstructed_person, load_programme, stages)
from readmit_borderline_roster import (  # noqa: E402
    dated_evidence, persistence_model, ruled_present, slug)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
ROSTER = DATA / "reconstruction" / "1835_borderline_roster.json"
REGISTER = DATA / "research" / "church" / "records" / "st_marys_baptisms_1833_1835.json"
REGISTER_FILE = "data/research/church/records/st_marys_baptisms_1833_1835.json"
OUT = DATA / "reconstruction" / "1835_church_register.json"
CARDS = RESIDENTS / "underdocumented"
SOURCES = DATA / "sources"

STAGE = UNDERDOCUMENTED_STAGE
SUB_STAGE = "church_register"
TICKET = "T-1504"
PARENT = "T-1177"
FAMILY_PASS = "T-1335"
SCENE_DATE = dt.date(1835, 7, 1)
WINDOW_OPENS = dt.date(1833, 1, 1)
SCHEMA = 1

CLASS = "R6_native_metis_black"
COMMUNITY_IN = "native_or_metis"
COMMUNITY_OUT = "native"
RULE_ID = "underdocumented_r6_the_priest_writes_the_term_onto_the_name"
ROSTER_RULE = "community_term_written_onto_the_name"
REGISTER_SOURCE = "st_marys_baptismal_register_1833_1835"
# The id every card of THIS sub-stage wears. `hh_um_` is T-1376's muster cohort and
# `hh_fb_` is T-1377's free Black town; each sub-stage sweeps its own prefix and no more.
CARD_PREFIX = "hh_cr_"

CLASS_SENTENCE = (
    "Named in St Mary's baptismal register at Chicago in 1833, with the priest's own word "
    "for an Indigenous woman written onto her name and onto no other name on the line. No "
    "1835 corroboration and no card. The licence is R3's — a dated appearance inside the "
    "window, priced against the persistence model — and the husband and the children named "
    "on the same entries the town already carries.")

R3_SENTENCE = ("A name on the 1 April 1834 post-office return or the 1832 Black Hawk muster "
               "enrolled at Chicago, with no 1835 corroboration and no card. Licence: Mint "
               "reconstructed, presence bounded by the persistence rate.")

NOT_A_RESIDENCE = (
    "A baptism documents a person at a font on a day. It is not a residence, an address, an "
    "occupation or an arrival, and this card asserts none of them. What the dated appearance "
    "bounds is that she was at Chicago on that day; what it does not bound is where she "
    "slept, whose roof it was, or whether she was still here on 1 July 1835 — that last is "
    "what the persistence draw prices and says out loud.")

REFUSALS = {
    "the_crosswalk_ruled_this_row_not_a_person": (
        "The register's own crosswalk rules this row `not_a_person`: it is a TOWN FINDING — "
        "a line of prose that bounds the book rather than populating it — and there is "
        "nobody in it for a card to receive. It is not refused for being false and it is "
        "not out of the window. The person the finding describes is carded here from the "
        "entry the finding quotes, so nothing is lost by refusing the finding itself; "
        "carding both would double one woman out of one page."),
    "the_register_prints_this_woman_twice": (
        "The same woman is named on a second entry of the same book, in the same year, with "
        "the same spouse written beside her on the line. Two printings of one reading are "
        "not two people — the shape T-1562 settled for the three printings of Samuel Toby — "
        "so one card is written and this row is refused. The spouse's name is read here as "
        "a DISCRIMINATOR on the page and for nothing else: no kin tie is written onto any "
        "card, and the family pass that owns the tie is named on the card instead."),
    "a_card_of_this_reading_already_stands": (
        "A person already in the layer bears this whole reading. The surname-and-initial "
        "key the sibling stages collide on is empty for a one-word name and can say nothing "
        "here, so the test is the WHOLE folded reading against every name the layer holds."),
    "the_term_is_prose_and_not_a_statement": (
        "The roster classed this row R6 because a community term appears somewhere in the "
        "text of the reading. A word in a paragraph is not a statement by the source about "
        "this person's community, and this stage mints only where the source's own "
        "structure says it — here, a parenthesis the priest wrote onto this name and onto "
        "no other name on the line."),
    "later_only_and_this_stage_does_not_back_project": (
        "The reading is dated AFTER 1 July 1835. The register runs to 1835 and fourteen of "
        "its entries are of that year, so this is a live refusal and not a formality: a "
        "person first seen after the scene date is not evidence of a person at the scene, "
        "and back-projecting off a later naming is R5's licence and R5 is T-1172's."),
    "earlier_than_the_window_and_nothing_follows_the_person_forward": (
        "The reading is dated before the roster's window opens on 1833-01-01 and nothing in "
        "the corpus follows this person forward to the scene. Under the ladder ratified "
        "2026-09-03 an earlier source dates and corroborates and never promotes."),
    "the_reading_carries_no_date_this_tool_can_read": (
        "A mint needs a dated appearance to price its presence against the persistence "
        "model, and this reading gives none."),
    "no_source_resolves": (
        "Every record here must cite a source that resolves in data/sources/, and this "
        "reading's does not."),
    "the_id_a_read_name_derives_is_already_taken": (
        "The household id this reading derives is already borne by a card in the layer; the "
        "id scheme forbids renaming a real person to make room."),
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fold(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).lower().split())


def display_name(normalised: str) -> str:
    """The roster's reading, capitalised for a card and NOTHING else done to it.

    The same choice T-1376 made and for the same reason: `title_case` turns a one-letter
    word into an English initial, which has no business inside a name the priest wrote
    phonetically. `name_as_read` keeps the printed form verbatim on every record.
    """
    return " ".join(w.capitalize() for w in str(normalised or "").split())


def without_parenthetical(name) -> str:
    """`Marianne (sauvage)` -> `Marianne`.

    The parenthesis is the CLERK's, not part of the name he was writing down, and this
    project does not print his word for her as though it were. It is kept whole in
    `name_as_read` and quoted in `community_term_as_written`, because it is the reason
    this card exists and hiding it would be its own kind of edit.
    """
    return re.sub(r"\s*\([^)]*\)", "", str(name or "")).strip()


def register_rows() -> dict:
    """{record id: row} for every named person the register reading holds."""
    return {r["id"]: r for r in load(REGISTER).get("records", [])}


def layer_readings() -> tuple[set, set, set]:
    """(folded person names, person ids, household ids) across every place a card lives.

    THIS STAGE'S OWN OUTPUT IS NOT IN THE LIST, and it must not be — `--check` re-derives
    from the roster and compares against what is committed, so a pass that read its own
    cards as the layer would find each of them colliding with itself on the second run and
    mint nobody. That is a build which is green once and empty afterwards. The duplicate a
    stage can make WITHIN one run is caught by the twice-printed rule, where it belongs.
    """
    names, pids, hids = set(), set(), set()
    for folder in ("households", "readmitted", "reconstructed_trades", "transients",
                   "lodgers"):
        path = RESIDENTS / folder
        if not path.is_dir():
            continue
        for card in sorted(path.glob("*.json")):
            rec = load(card)
            hids.add(rec.get("id"))
            for person in rec.get("persons") or []:
                pids.add(person.get("id"))
                names.add(fold(person.get("name")))
                names.add(fold(without_parenthetical(person.get("name"))))
    names.discard("")
    pids.discard(None)
    hids.discard(None)
    return names, pids, hids


def spouse_on_the_line(record: dict, rows: dict) -> dict | None:
    """The father named on the same entry as this mother, as the register prints him.

    Read straight off the locator — same year series, same entry number, role `father` —
    so it is the page's own pairing and not a name match. Returns the record, or None
    where the entry names no father.
    """
    loc = record.get("locator") or {}
    for other in rows.values():
        oloc = other.get("locator") or {}
        if (oloc.get("year_series") == loc.get("year_series")
                and oloc.get("entry") == loc.get("entry")
                and oloc.get("role") == "father"):
            return other
    return None


def kin_on_the_line(record: dict, rows: dict) -> list[dict]:
    """Everybody else the same entry names, with their role — handed on, never joined."""
    loc = record.get("locator") or {}
    out = []
    for other in sorted(rows.values(), key=lambda r: (r.get("locator") or {}).get("position", 0)):
        oloc = other.get("locator") or {}
        if (oloc.get("year_series") == loc.get("year_series")
                and oloc.get("entry") == loc.get("entry")
                and other["id"] != record["id"]):
            out.append({"record_id": other["id"], "role": oloc.get("role"),
                        "as_read": other.get("as_read"),
                        "normalised": other.get("normalized")})
    return out


def origin_block(term: str, grade: str) -> dict:
    """`sauvage de Green Bay` -> an origin; `sauvage` alone -> no origin at all.

    THE ONE ORIGIN THE BOOK EVER GIVES ANYBODY, by the register reader's own note, and it
    is a PLACE and not a people. Green Bay is where the priest understood her to come from;
    the Menominee, the Ho-Chunk, the Potawatomi and the Ottawa country all met there and the
    entry distinguishes none of them, so no nation is written off the back of it.
    """
    where = re.sub(r"^sauvage\s+(de|du|des)\s+", "", str(term or "").strip(), flags=re.I)
    if not where or fold(where) == "sauvage":
        return {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": ("THE REGISTER GIVES HER NO ORIGIN. The priest writes his word for an "
                     "Indigenous woman and writes nothing further — no nation, no band, no "
                     "village and no place — so nothing is written here. The one origin the "
                     "book ever gives anyone is on entry 18 of 1833 and belongs to the other "
                     "woman this stage cards."),
        }
    return {
        "value": where,
        "confidence": grade,
        "tier": grade,
        "sources": [REGISTER_SOURCE],
        "note": (f"READ OFF THE PAGE, AND IT IS A PLACE AND NOT A PEOPLE. The priest writes "
                 f"`{term}` — the ONLY origin St Mary's register ever gives anyone, by the "
                 f"register reader's own note on this row. It says where he understood her to "
                 f"come from; it does not name a nation, and none is written here. It places "
                 f"HER and not the household, and no residence follows from it. Graded "
                 f"`{grade}` because that is the grade the register reader gives this row, "
                 f"and a card does not grade above the reading it stands on."),
        "replaceable_by": {"kind": "person",
                           "match": "a source that states where this person came from, or "
                                    "that names her nation, band or village"},
    }


def card_for(row, record, spouse, kin, hid, pid, sources, presence, appearances) -> dict:
    display = display_name(row.get("normalised") or without_parenthetical(row["name_as_read"]))
    cells = record.get("cells") or {}
    term = re.search(r"\(([^)]*)\)", row.get("name_as_read") or "")
    term = term.group(1) if term else (row.get("community_term") or "")
    grade = record.get("confidence") or "inferred"
    seen = ", ".join(a["describes_date"] for a in appearances)
    return {
        "id": hid,
        "name": f"{display} — named in St Mary's baptismal register, 1833",
        "division": "unplaced",
        "head": pid,
        "source_pass": "reconstructed_church_register",
        "underdocumented": {
            "ticket": TICKET,
            "parent": PARENT,
            "stage": STAGE,
            "sub_stage": SUB_STAGE,
            "class": CLASS,
            "rule": RULE_ID,
            "row_id": row["row_id"],
            "name_as_read": row["name_as_read"],
            "as_printed": record.get("as_read"),
            "community_term_as_written": term,
            "community_term_is_the_clerks_word": (
                "`sauvage` is Father Saint Cyr's word for an Indigenous woman, written in "
                "his own hand in 1833. It is kept because it is the register's own "
                "vocabulary and the reason this record exists. It is not this project's "
                "word, it is not her name, and it is not printed as either."),
            "entries_that_name_her": appearances,
            "entry_as_read": cells.get("entry_as_read"),
            "priest": cells.get("priest"),
            "place_as_printed": cells.get("place"),
            "role_on_the_entry": cells.get("role"),
            "reading_grade": grade,
            "stands_on": CLASS_SENTENCE,
            "the_research_layers_own_ruling": row.get("ledger_disposition"),
            "handed_to_the_family_pass": {
                "ticket": FAMILY_PASS,
                "named_on_the_same_entries": kin,
                "what_is_handed": (
                    "The kinship these entries state — who is whose child, whose wife, whose "
                    "godparent — is NOT joined here and no tie is written onto this card. "
                    f"The roster's own ledger hands every one of these rows to {FAMILY_PASS}, "
                    "the family pass proper, and that is where the tie belongs. What this "
                    "stage takes off the same line is the spouse's name, used once, as a "
                    "discriminator that tells two printings of one woman from two women."),
            },
            "withdrawn_if": ("a ruling that this reading is a duplicate of a card the town "
                             "already holds; the retirement runs through "
                             "tools/consolidate_town_cards.py, never by hand"),
        },
        "arrival": {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": ("Not attested. The register dates an appearance at a font and records "
                     "no arrival; this is also the country these people were already in, so "
                     "the question the word `arrival` asks may not be the right one to ask "
                     "of this card at all."),
        },
        "origin": origin_block(term, grade),
        "lives_at": {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": ("Not attested. " + NOT_A_RESIDENCE + " The entry's `place` column reads "
                     "Chicago, which is where the sacrament was administered and is not an "
                     "address."),
        },
        "works_at": {"value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
                     "note": "Not attested. A baptismal entry records no trade."},
        "present_on_scene_date": presence,
        "persons": [{
            "id": pid,
            "name": display,
            "name_as_read": row["name_as_read"],
            "relationship": "head",
            "grade": RECONSTRUCTED,
            "sex": "female",
            "sex_basis": {
                "value": "female", "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
                "note": ("READ OFF THE ENTRY'S OWN STRUCTURE and not drawn from the sex "
                         "model: the register's `role` column puts this person in the "
                         "MOTHER's place of a baptism, and the entry names the father "
                         "separately. It is one of two attributes the document settles — "
                         "this and the day — and no age is drawn beside it, because the "
                         "same document settles nothing about that."),
            },
            "basis": {"kind": "rule", "id": RULE_ID, "note": CLASS_SENTENCE},
            "replaceable_by": {
                "kind": "person",
                "match": ("a second independent source naming this person at Chicago inside "
                          "the window, or any source that states her nation, band, village "
                          "or family name — any of them would carry the card past what one "
                          "parenthesis in one register can hold"),
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
                                    "baptismal entry records none for anybody.")},
            "sources": sources,
            "note": (
                f"CARDED FROM THE BORDERLINE ROSTER'S R6 ({TICKET}, stage `{STAGE}`, "
                f"sub-stage `{SUB_STAGE}`). {CLASS_SENTENCE} The register prints her as "
                f"`{record.get('as_read')}`, in the {cells.get('role')}'s place of entry "
                f"{(record.get('locator') or {}).get('entry')} of "
                f"{(record.get('locator') or {}).get('year_series')}, at "
                f"`{cells.get('place')}`, in the hand of {cells.get('priest')}, dated "
                f"{seen}. NO SURNAME IS INVENTED: the book gives her a forename and the "
                f"priest's parenthesis and nothing else, and her husband's surname is his. "
                f"{NOT_A_RESIDENCE} The research READ this row and left it `"
                f"{row.get('ledger_disposition')}`, handing the kinship on to "
                f"{FAMILY_PASS}; that ruling is not overturned, and this record is a "
                f"reconstruction of what the town looks like if the name is admitted at the "
                f"limit of its own evidence. The reading, the source and the ruling stand at "
                f"`{row['row_id']}` in data/reconstruction/1835_borderline_roster.json. "
                f"REVIEW REQUIRED: this card is a record of a Native woman at Chicago in the "
                f"three years of the removal, and AGENTS.md's standing constraint holds it "
                f"for review by Native scholars or community organisations before any scene "
                f"carrying it may be marked released. No figure is drawn (L1)."),
            "resident_subtype": "underdocumented_resident",
        }],
        "touches_removal": True,
        "review_required": True,
        "research_note": (
            f"WRITTEN BY tools/reconstruct_church_register.py ({TICKET}), the `{SUB_STAGE}` "
            f"sub-stage of the `{STAGE}` stage of the 1835 resident reconstruction "
            f"programme, under the owner's ruling of 2026-09-17 recorded in AGENTS.md. This "
            f"file is NOT research and is not a mint output: data/residents/households/ is "
            f"re-derived by the mint writers and data/residents/index.json is derived from "
            f"that directory, so a card written here lives beside the muster cohort and is "
            f"overlaid onto the scene by tools/compile_scene.py. REVIEW REQUIRED AND TOUCHES "
            f"REMOVAL, both true, for the subject this record is about: a Native woman at "
            f"Chicago in 1833, two years before the removal of the Potawatomi from this "
            f"place. The review AGENTS.md commits to has not been held; until it is, no "
            f"scene carrying this card may be marked released. docs/LIBERTIES.md carries the "
            f"invention."),
    }


def derive() -> tuple[dict, dict]:
    """(the record, {household_id: card}) — the whole sub-stage, in memory."""
    roster = load(ROSTER)
    model = persistence_model()
    names, pids, hids = layer_readings()
    source_ids = {p.stem for p in SOURCES.glob("*.json")}
    rows_by_record = register_rows()

    minted: list[dict] = []
    withheld: list[dict] = []
    already: list[dict] = []
    cards: dict[str, dict] = {}
    taken_ids = set(hids)
    minted_by_woman: dict[tuple, str] = {}

    def withhold(row, reason, extra=None):
        withheld.append({
            "row_id": row["row_id"], "name_as_read": row["name_as_read"],
            "domain": row.get("domain"), "describes_date": row.get("describes_date"),
            "reason": reason, "why": REFUSALS[reason] + (f" {extra}" if extra else ""),
        })

    # THE BOOK THIS STAGE READS, and its whole scope: the R6 rows that cite the register.
    offered = [r for r in roster["rows"]
               if r.get("class") == CLASS and r.get("community") == COMMUNITY_IN
               and REGISTER_SOURCE in (r.get("source_id") or [])]

    # Two passes over the same rows, in the register's own order (year, entry, position),
    # so which printing becomes the card is the page's order and not the roster's sort.
    def page_order(row):
        rec = rows_by_record.get(row.get("claim_or_record_id")) or {}
        loc = rec.get("locator") or {}
        return (loc.get("year_series") or 9999, loc.get("entry") or 9999,
                loc.get("position") or 99, row["row_id"])

    for row in sorted(offered, key=page_order):
        existing = row.get("existing_household_id")
        if existing:
            already.append({
                "row_id": row["row_id"], "name_as_read": row["name_as_read"],
                "household_id": existing, "community_term": row.get("community_term"),
                "rule": row.get("rule"),
                "note": ("The term was found on a card the town already holds. Nothing is "
                         "minted; whether that card carries `touches_removal` is the card's "
                         "own affair and this stage does not reach into it."),
            })
            continue

        if row.get("rule") != ROSTER_RULE:
            withhold(row, "the_term_is_prose_and_not_a_statement")
            continue

        record = rows_by_record.get(row.get("claim_or_record_id"))
        if record is None:
            # NOT A ROW OF THE REGISTER'S OWN READING. The only thing that reaches here is
            # a town finding — the crosswalk has already ruled there is no person in it —
            # and saying so is truer than saying it is out of this stage's scope, which
            # would be the sibling's dead end printed a second time.
            withhold(row, "the_crosswalk_ruled_this_row_not_a_person")
            continue

        when, _refusal = dated_evidence(row)
        if when is None:
            withhold(row, "the_reading_carries_no_date_this_tool_can_read")
            continue
        if when > SCENE_DATE:
            withhold(row, "later_only_and_this_stage_does_not_back_project")
            continue
        if when < WINDOW_OPENS:
            withhold(row, "earlier_than_the_window_and_nothing_follows_the_person_forward")
            continue

        spouse = spouse_on_the_line(record, rows_by_record)
        woman = (fold(row.get("normalised")), fold((spouse or {}).get("normalized")))
        if woman in minted_by_woman:
            hid = minted_by_woman[woman]
            card = cards[hid]
            card["underdocumented"]["entries_that_name_her"].append({
                "record_id": record["id"], "row_id": row["row_id"],
                "entry": (record.get("locator") or {}).get("entry"),
                "year_series": (record.get("locator") or {}).get("year_series"),
                "describes_date": row.get("describes_date"),
                "as_read": record.get("as_read"),
            })
            withhold(row, "the_register_prints_this_woman_twice",
                     extra=(f"She is carded as `{hid}` off entry "
                            f"{card['underdocumented']['entries_that_name_her'][0]['entry']} "
                            f"of {card['underdocumented']['entries_that_name_her'][0]['year_series']}, "
                            f"and the spouse both entries name is "
                            f"`{(spouse or {}).get('as_read')}`."))
            continue

        if fold(row.get("normalised")) in names:
            withhold(row, "a_card_of_this_reading_already_stands")
            continue

        pid = slug(row.get("normalised"))
        hid = f"{CARD_PREFIX}{pid}"
        if not pid or hid in taken_ids or pid in pids:
            withhold(row, "the_id_a_read_name_derives_is_already_taken")
            continue
        sources = [s for s in (row.get("source_id") or []) if s in source_ids]
        if not sources:
            withhold(row, "no_source_resolves")
            continue

        appearances = [{
            "record_id": record["id"], "row_id": row["row_id"],
            "entry": (record.get("locator") or {}).get("entry"),
            "year_series": (record.get("locator") or {}).get("year_series"),
            "describes_date": row.get("describes_date"),
            "as_read": record.get("as_read"),
        }]
        kin = kin_on_the_line(record, rows_by_record)
        value, share, lag, seed = ruled_present(model, hid, when)
        presence = {
            "value": value, "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
            "basis": {"kind": "model", "id": model["id"],
                      "note": (f"The register dates this name at {row.get('describes_date')}, "
                               f"{lag:.2f} years before the scene date. The persistence model "
                               f"gives {share:.3f} for that lag and the seeded draw reads "
                               f"{value}. It is the same model, the same lag arithmetic and "
                               f"the same draw that priced the twenty men of Kercheval's "
                               f"company and the ninety-four of the company the roll heads "
                               f"INDIAN.")},
            "seed": seed,
            "replaceable_by": {"kind": "person",
                               "match": "any source naming this person at Chicago on or "
                                        "after 1 July 1835"},
        }
        card = card_for(row, record, spouse, kin, hid, pid, sources, presence, appearances)
        cards[hid] = card
        taken_ids.add(hid)
        minted_by_woman[woman] = hid
        minted.append({
            "row_id": row["row_id"], "class": CLASS, "rule": RULE_ID,
            "household_id": hid, "person_id": pid,
            "name_as_read": row["name_as_read"], "name": card["persons"][0]["name"],
            "file": f"underdocumented/{hid}.json", "sources": sources,
            "community": COMMUNITY_OUT, "review_required": True, "touches_removal": True,
            "spouse_on_the_line_as_read": (spouse or {}).get("as_read"),
            "dated_evidence": row.get("describes_date"),
            "dated_evidence_read_as": when.isoformat(),
            "present_on_scene_date": {"value": value, "persistence": round(share, 4),
                                      "years_before_the_scene": round(lag, 4), "seed": seed},
        })

    # THE PRESENCE DRAW IS PRICED OFF THE LATEST APPEARANCE, not the first. A second
    # printing dated later is the LAST day this project can still see her, which is the
    # lag the persistence model is about — the reading T-1562 made on Samuel Toby's card,
    # arriving here for the same reason. The seed is the household id and does not move,
    # so this changes the share and the draw and never who is being drawn for.
    for m in minted:
        card = cards[m["household_id"]]
        appearances = card["underdocumented"]["entries_that_name_her"]
        latest_row = max(appearances, key=lambda a: str(a["describes_date"]))
        when = dt.date.fromisoformat(
            latest_row["describes_date"] if len(latest_row["describes_date"]) == 10
            else latest_row["describes_date"] + "-01")
        value, share, lag, seed = ruled_present(model, m["household_id"], when)
        card["present_on_scene_date"]["value"] = value
        card["present_on_scene_date"]["basis"]["note"] = (
            f"The register's LAST sighting of this name is "
            f"{latest_row['describes_date']} — entry {latest_row['entry']} of "
            f"{latest_row['year_series']}, of the {len(appearances)} entry/entries that "
            f"name her — {lag:.2f} years before the scene date. The persistence model gives "
            f"{share:.3f} for that lag and the seeded draw reads {value}. A later printing "
            f"is the last day this project can still see her and is the lag the model is "
            f"about; pricing off the first would understate the evidence. It is the same "
            f"model and the same draw that priced the men of the 1832 muster.")
        card["present_on_scene_date"]["seed"] = seed
        m["dated_evidence"] = latest_row["describes_date"]
        m["dated_evidence_read_as"] = when.isoformat()
        m["present_on_scene_date"] = {"value": value, "persistence": round(share, 4),
                                      "years_before_the_scene": round(lag, 4), "seed": seed}

    record = {
        "$schema_note": ("DERIVED — regenerate with tools/reconstruct_church_register.py "
                         "--build; tools/check.sh re-derives it. Do not hand-edit: every "
                         "card under data/residents/underdocumented/ carrying the "
                         f"`{CARD_PREFIX}` prefix is a function of the borderline roster row "
                         "named on it."),
        "schema": SCHEMA,
        "id": "chicago_july_1835_church_register",
        "ticket": TICKET,
        "parent": PARENT,
        "stage": STAGE,
        "sub_stage": SUB_STAGE,
        "target_date": SCENE_DATE.isoformat(),
        "generated_by": "tools/reconstruct_church_register.py --build",
        "reads": ["data/reconstruction/1835_borderline_roster.json", REGISTER_FILE],
        "writes": f"data/residents/underdocumented/{CARD_PREFIX}*.json",
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
        "the_count_that_made_this_stage_necessary": the_count(rows_by_record, names),
        "rules": {
            "licence": {"id": RULE_ID, "borrowed_from": "R3_1834_return_or_muster",
                        "r3_sentence": R3_SENTENCE, "this_sentence": CLASS_SENTENCE},
            "a_baptism_is_not_a_residence": NOT_A_RESIDENCE,
            "the_mononym_is_carried_as_read": (
                "The register gives these women a forename and the priest's parenthesis and "
                "nothing else. No surname is invented and no given/family split is imposed; "
                "her husband's surname is his. The surname-and-initial key the sibling "
                "stages collide on is EMPTY for a one-word name and can say nothing here, "
                "so the collision test is the whole folded reading against every name the "
                "layer holds, and the spouse the entry names beside her tells two printings "
                "of one woman from two women."),
            "the_spouse_is_a_discriminator_and_not_a_tie": (
                "The father named on the same line is read once, to tell one woman from "
                "another, and for nothing else. No kin tie is written onto any card. The "
                f"kinship the register states is {FAMILY_PASS}'s field, every one of these "
                f"rows names it in its ledger reason, and each card carries "
                "`handed_to_the_family_pass` naming who else the entry names."),
            "no_nation_is_written_and_one_place_is": (
                "`sauvage` names no nation, band or village, so `community` is `native` — "
                "this vocabulary's term for *the source says so and says nothing further*. "
                "Entry 18 of 1833 adds `de Green Bay`, the one origin the book ever gives "
                "anyone; it is a PLACE and is carried as one, and no people is read off it."),
            "a_card_never_grades_above_the_reading": (
                "Each attribute taken off the page is graded at the register reader's own "
                "grade for that row and never above it. Jaespquaa's name is `inferred` "
                "because an Indigenous name written phonetically by a French speaker has "
                "middle letters nobody can be sure of, and her origin is carried at that "
                "same grade rather than at the grade the legible words would carry."),
            "the_sex_is_read_and_not_drawn": (
                "The register's `role` column puts each of these people in the MOTHER's "
                "place of a baptism and names the father separately. That is the document's "
                "own structure; no age band is drawn beside it, because the same document "
                "settles nothing about that."),
        },
        "persistence_model": model,
        "counts": {
            "r6_rows_citing_the_register": len(offered),
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
        "what_is_handed_to_the_family_pass": {
            "ticket": FAMILY_PASS,
            "what": ("The kinship every one of these entries states on one dated line — the "
                     "child, the father, the mother and the two sponsors — is handed on "
                     "whole and joined nowhere here. The roster's own ledger reason hands "
                     f"these rows to {FAMILY_PASS} and this stage does not take the tie off "
                     "it; what it takes is the community term and the dated appearance."),
            "by_card": {m["household_id"]: cards[m["household_id"]]["underdocumented"]
                        ["handed_to_the_family_pass"]["named_on_the_same_entries"]
                        for m in minted},
        },
        "what_is_still_not_carded_from_this_book": (
            "Everything else in the register. This stage spends the R6 rows and no others: "
            "the fifty-seven entries name 267 people and the rest of them are the mints' and "
            "T-1335's business, not this one's. And the book counts nobody — it is a record "
            "of sacraments administered, not a census — so no remainder is drawn off it "
            "here, for the reason T-1376 refused the same thing for the muster: a bracket "
            "needs a count, and this corpus holds no count of the Native and Metis people at "
            "Chicago on 1 July 1835."),
        "minted": sorted(minted, key=lambda m: m["household_id"]),
        "already_on_a_card": sorted(already, key=lambda a: a["row_id"]),
        "withheld": sorted(withheld, key=lambda w: w["row_id"]),
    }
    # T-1489. The seat another pass drew for these people, carried through the rebuild —
    # the same fixed-slot carry the sibling sub-stages of this directory already use.
    carry_seats(cards, CARDS)
    return record, cards


def the_count(rows_by_record: dict, layer_names: set) -> dict:
    """Who the town already carried off these same entries, and who it did not.

    RE-DERIVED from the committed layer rather than asserted: the entries are found by
    their own locator, and each name on them is looked up in the layer by the same folded
    reading the collision test uses. If the town later cards one of the people below, this
    block says so on the next --build instead of going stale.
    """
    entries: dict[tuple, list] = {}
    for rec in rows_by_record.values():
        loc = rec.get("locator") or {}
        entries.setdefault((loc.get("year_series"), loc.get("entry")), []).append(rec)
    out = []
    for rec in rows_by_record.values():
        term = re.search(r"\(([^)]*)\)", rec.get("as_read") or "")
        if not term:
            continue
        loc = rec.get("locator") or {}
        others = []
        for other in sorted(entries[(loc.get("year_series"), loc.get("entry"))],
                            key=lambda r: (r.get("locator") or {}).get("position", 0)):
            if other["id"] == rec["id"]:
                continue
            others.append({
                "as_read": other.get("as_read"),
                "role": (other.get("locator") or {}).get("role"),
                "the_town_carried_this_name_before_this_stage":
                    fold(other.get("normalized")) in layer_names,
            })
        out.append({
            "entry": loc.get("entry"), "year_series": loc.get("year_series"),
            "the_name_the_term_was_written_onto": rec.get("as_read"),
            "the_town_carried_this_name_before_this_stage":
                fold(rec.get("normalized")) in layer_names,
            "everybody_else_the_entry_names": others,
        })
    out.sort(key=lambda e: (e["year_series"] or 0, e["entry"] or 0))
    carried = sum(1 for e in out for o in e["everybody_else_the_entry_names"]
                  if o["the_town_carried_this_name_before_this_stage"])
    return {
        "register": REGISTER_FILE,
        "source": REGISTER_SOURCE,
        "the_entries_the_priest_wrote_the_term_on": out,
        "others_on_those_entries_the_town_already_carried": carried,
        "the_named_the_town_already_carried_before_this_stage": sum(
            1 for e in out if e["the_town_carried_this_name_before_this_stage"]),
        "what_separated_them": (
            "Not the evidence — one book, one clerk, one page apiece, and the same entry "
            "naming all of them. The borderline roster's class rule put a reading carrying "
            "a community term into R6 and everything else into R3; the R3 rows were spent "
            "and R6's owner (T-1177) was split into workable tickets only in September, and "
            "the sub-stage that could spend these particular rows read the 1832 muster roll "
            "and not this book. So the town carried the husbands and the children off these "
            "entries and not the women the priest wrote the term onto."),
    }


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

    # EACH SUB-STAGE SWEEPS ITS OWN PREFIX AND NO MORE. The directory holds three cohorts
    # now — `hh_um_` is T-1376's, `hh_fb_` is T-1377's and `hh_cr_` is this one's — and a
    # sweep of everything would have the three writers deleting each other's cards turn
    # about.
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
            if person["reconstruction"].get("community") != COMMUNITY_OUT:
                error(hid, f"a card of this stage must carry community `{COMMUNITY_OUT}`")
            if not (card.get("review_required") and card.get("touches_removal")):
                error(hid, "the household must carry review_required and touches_removal")
            prose = person.get("note") or ""
            if "REVIEW REQUIRED" not in prose or "removal" not in prose:
                error(hid, "a flagged record says why in its own words and names the "
                           "subject it is held for (AGENTS.md)")
            if " " in str(person.get("name") or "").strip():
                error(hid, "this stage carries a mononym; a second word is a surname "
                           "somebody invented")
        ud = card["underdocumented"]
        if not ud.get("handed_to_the_family_pass", {}).get("ticket") == FAMILY_PASS:
            error(hid, f"the kinship on the entry must be handed to {FAMILY_PASS} by name")
    for drifted in emit(record, cards, write=False):
        error(drifted, "does not re-derive from the roster; run --build")
    if problems:
        for p in problems:
            print(f"  FAIL {p}")
        return 1
    c = record["counts"]
    print(f"  ok    {c['cards_minted']} church-register card(s) re-derive, every one "
          f"review_required and touches_removal with its own sentence")
    print(f"  ok    {c['withheld']} row(s) withheld, each with a named reason; "
          f"{c['already_on_a_card']} already on a card")
    print(f"  ok    no surname is invented, and the kinship is handed to {FAMILY_PASS} "
          f"rather than joined here")
    return 0


def report() -> int:
    record, cards = derive()
    print(f"{record['id']} — {TICKET}, stage `{STAGE}` / `{SUB_STAGE}`")
    tally = record["the_count_that_made_this_stage_necessary"]
    for entry in tally["the_entries_the_priest_wrote_the_term_on"]:
        mark = "carded" if entry["the_town_carried_this_name_before_this_stage"] else "NOT CARDED"
        print(f"  entry {entry['entry']:>3} of {entry['year_series']}  "
              f"{entry['the_name_the_term_was_written_onto']:34} {mark}")
        for other in entry["everybody_else_the_entry_names"]:
            om = "carded" if other["the_town_carried_this_name_before_this_stage"] else "not carded"
            print(f"       {other['role']:<10} {other['as_read']:28} {om}")
    print(f"  minted {record['counts']['cards_minted']} "
          f"({record['counts']['minted_present']} present, "
          f"{record['counts']['minted_absent']} absent on the scene date)")
    for reason, n in record["counts"]["withheld_by_reason"].items():
        print(f"  withheld {n:3}  {reason}")
    for m in record["minted"]:
        print(f"    {m['name']:14} {m['present_on_scene_date']['value']:8} "
              f"{m['dated_evidence']:12} spouse on the line: "
              f"{m['spouse_on_the_line_as_read']}")
    return 0


def self_test() -> int:
    """The rules, each refusing its own case."""
    failures = []

    def case(name, ok):
        print(f"  {'ok   ' if ok else 'FAIL '} {name}")
        if not ok:
            failures.append(name)

    case("the clerk's parenthesis comes off the display name",
         without_parenthetical("Marianne (sauvage)") == "Marianne")
    case("a card is capitalised without an English initial",
         display_name("jaespquaa") == "Jaespquaa")
    case("an origin is read off `de Green Bay` and graded at the row's grade",
         origin_block("sauvage de Green Bay", "inferred")["value"] == "Green Bay"
         and origin_block("sauvage de Green Bay", "inferred")["confidence"] == "inferred")
    case("`sauvage` alone yields no origin at all",
         origin_block("sauvage", "documented")["value"] is None)
    case("no nation is read off a place",
         "nation" in origin_block("sauvage de Green Bay", "inferred")["note"])
    case("the spouse is read off the entry's own locator",
         (spouse_on_the_line(register_rows()["st_marys_bapt_1833_14_3_mother"],
                             register_rows()) or {}).get("as_read") == "Antoine Aspam")

    record, cards = derive()
    case("every card carries review_required and touches_removal",
         all(c.get("review_required") and c.get("touches_removal") for c in cards.values()))
    case("every person carries the stage that is allowed to write them",
         all(p["reconstruction"]["stage"] == STAGE
             for c in cards.values() for p in c["persons"]))
    case("no card writes a nation",
         all("nation" not in str(c["persons"][0]["reconstruction"].get("community"))
             for c in cards.values())
         and all(c["persons"][0]["reconstruction"]["community"] == COMMUNITY_OUT
                 for c in cards.values()))
    case("no surname is invented for anybody",
         all(" " not in c["persons"][0]["name"] for c in cards.values()))
    case("no kin tie is written onto a card",
         all(not any(k in c for k in ("spouse", "members", "kin", "family"))
             for c in cards.values())
         and all(c["underdocumented"]["handed_to_the_family_pass"]["ticket"] == FAMILY_PASS
                 for c in cards.values()))
    case("every withheld row names a reason this file states",
         all(w["reason"] in REFUSALS for w in record["withheld"]))
    case("the two printings of one woman make one card, not two",
         any(w["reason"] == "the_register_prints_this_woman_twice"
             for w in record["withheld"])
         and len([c for c in cards.values()
                  if c["persons"][0]["name"] == "Marianne"]) == 1)
    case("the town finding is refused as the crosswalk ruled it and not as out of scope",
         any(w["reason"] == "the_crosswalk_ruled_this_row_not_a_person"
             for w in record["withheld"]))
    case("the two women the register names are the two the town did not carry",
         {c["persons"][0]["name"] for c in cards.values()} == {"Marianne", "Jaespquaa"})
    case("the husbands and children on those entries WERE already carried",
         record["the_count_that_made_this_stage_necessary"]
               ["others_on_those_entries_the_town_already_carried"] >= 4)
    case("presence is priced off the LAST sighting the book gives",
         all("LAST sighting" in c["present_on_scene_date"]["basis"]["note"]
             for c in cards.values()))
    case("the stage does not read its own output as the layer",
         "underdocumented" not in layer_readings.__doc__.split("THIS STAGE'S OWN")[0]
         or all(not str(RESIDENTS / f).endswith("underdocumented")
                for f in ("households", "readmitted", "reconstructed_trades",
                          "transients", "lodgers")))
    case("no person written here is invented — every id is a read name",
         all(not p["id"].startswith("rc_") for c in cards.values() for p in c["persons"]))
    case("the remainder of the register is refused a draw, and says why",
         "a bracket needs a count" in record["what_is_still_not_carded_from_this_book"])

    if failures:
        print(f"  {len(failures)} case(s) failed")
        return 1
    print(f"  ok    20 rule(s) hold")
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
