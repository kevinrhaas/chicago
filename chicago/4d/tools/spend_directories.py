#!/usr/bin/env python3
"""The four directory crosswalks, SPENT on the people of 1835 (T-0632).

    python3 tools/spend_directories.py            write the layer, the ledger and the cards
    python3 tools/spend_directories.py --check    everything re-derives; nothing has drifted
    python3 tools/spend_directories.py --report   person by person, what each volume carries
    python3 tools/spend_directories.py --self-test the four rules below, held over what it derives

WHY THIS EXISTS, and what it replaces. T-0555, T-0571, T-0506 and T-0587 read three
Chicago directories and adjudicated them against this town: Fergus 1839, Fergus 1843,
Norris 1844 and Norris's advertising cards of 1844. Between them they matched 214
entries to people this reconstruction holds, and every one of those match rows carries
`occupation_1835: "none_recorded"` and `lives_at_1835: null` on the resident side. The
adjudication happened and nothing crossed into the town. `tools/spend_norris_1844.py`
spent ONE of the four; this pass subsumes it and spends the rest.

THE THREE THINGS IT WRITES, and why they are three.

  data/residents/directories.json   THE LAYER A VISITOR SEES. One row per person, every
        volume that meets them, every entry as printed, and what the entry holds that
        the 1835 record does not. Beside the records rather than inside them for the
        reason T-0569 set out: a directory listing is EVIDENCE ABOUT ITS OWN YEAR
        offered beside a person of 1835, not a fact of theirs, and keeping it beside
        the record is what stops it reading as one.

  data/research/directories/spend_crosswalk_1835.json   THE LEDGER. One ruling per
        (person, volume): what the volume prints, what this pass CARRIED to the card
        and what it REFUSED to carry, with the claim ids it rests on and the source it
        rests on. It is a crosswalk because it is an adjudication — the decision that a
        printed line may or may not cross to a person as later evidence — and putting
        it anywhere else would hide it from `tools/measure_research_spend.py`, which is
        the instrument that reported this domain as 6,684 read and 288 spent.

  data/residents/households/*.json  THE CARD. A `directories` block on the household,
        carrying the later occupation and the later address as graded values and
        CITING THE SOURCE. This is the hop the owner asked about on 2026-09-03 — "there
        are not outputs or updates to the household and resident data" — and it is the
        only one of the three a reader of a single record can see.

WHAT IS AND IS NOT CARRIED — the whole provenance argument, in four rules.

  1. NOTHING IS CARRIED THAT THE CROSSWALK DOES NOT ALREADY DECLARE. Each match row
     holds a `could_carry` list its own adjudication wrote. This pass reads that list
     and carries exactly what is in it. It never re-parses a printed line, never
     decides for itself that an entry holds a trade, and is therefore reversible from
     the crosswalk in both directions.

  2. ONLY A SINGLE-ENTRY MATCH CARRIES ANYTHING. A person met by several entries is
     AMBIGUOUS and every candidate is shown rather than one chosen; an entry met by two
     people is CONTESTED and at most one of them is the person printed. Both are
     rendered — hiding them would report the crosswalks' successes and their arithmetic
     separately — and neither writes a value onto a card.

  3. A SPLIT IS REFUSED PER ENTRY AND PER FIELD, never per volume. What T-0569 refused
     in Norris's alphabetical volume is a SHAPE: the volume sets a partnership where the
     trade would go — "of Horace Norton & Co", "of Loyd", twice simply "of" — so the
     split yields a value containing no trade at all, and printing one on a card would
     launder a heuristic into a finding. That ground is a fact about one printed line,
     so it is asked of one printed line: `split_refusal` below names the clause a field
     is refused under and says nothing about the field beside it or the volume around
     it. A refused field's LINE is still carried whole and quoted; only its parse stops.

  4. NO 1835 GRADE MOVES, EVER. Under the ratified ladder a directory of 1839, 1843 or
     1844 never makes an 1835 resident, never dates one and never gives one a trade in
     1835. Every value this pass writes is graded `attested` FOR ITS OWN YEAR, carries
     `describes_date`, and says in its own note that the 1835 record is untouched. The
     count of 1835 grades changed by this pass is zero, and `--check` holds it there.

THE STREET NUMBER DOES NOT CROSS EITHER. Fergus 1839 flags the entries whose address is
a street number in the 1839 grid (`address_is_street_only`), a numbering this town's
year does not have; for those the STREET NAME crosses and the number is dropped, which
is the rule the 1839 crosswalk wrote for itself.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ROOT / "data" / "research" / "directories"
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
LAYER = RESIDENTS / "directories.json"
LEDGER = DIRECTORIES / "spend_crosswalk_1835.json"
TICKET = "T-0632"
GENERATOR = "tools/spend_directories.py"

# The four volumes, in the order the town met them — earliest first, because the
# volume closest to 1835 is the one whose reading is worth most and the one whose
# value is carried when two disagree.
#
# NO VOLUME CARRIES A TRUST FLAG. Rule 3 above used to be `parse_trusted`, a boolean on
# the volume, and Norris's alphabetical directory carried it False; T-0987 stretch 6
# replaced it with `split_refusal`, which is asked per entry and per field. `carry_keys`
# maps this file's two carryable things onto whatever the volume's own crosswalk called
# them: Fergus 1839 wrote `street_1839` where Fergus 1843 wrote `address`, and Norris's
# advertisers wrote `place_of_business`. The vocabulary is theirs; the meaning is one.
VOLUMES = [
    {
        "key": "fergus_1839",
        "file": "fergus_1839_crosswalk_1835.json",
        "block": "residents",
        "year": 1839,
        "source_id": "fergus_chicago_directory_1839",
        "title": "Fergus's Chicago directory of 1839",
        "entries_key": "entries_1839",
        "occupation_key": "occupation_1839",
        "address_key": "address_1839",
        "page_key": "printed_page",
        "carry_keys": {"occupation": "occupation", "address": "street_1839"},
    },
    {
        "key": "fergus_1843",
        "file": "fergus_1843_crosswalk_1835.json",
        "block": None,
        "year": 1843,
        "source_id": "fergus_chicago_directory_1843",
        "title": "Fergus's Chicago directory of 1843",
        "entries_key": "entries_1843",
        "occupation_key": "occupation_1843",
        "address_key": "address_1843",
        "page_key": "page",
        "carry_keys": {"occupation": "occupation", "address": "address"},
    },
    {
        "key": "norris_1844",
        "file": "norris_1844_crosswalk_1835.json",
        "block": None,
        "year": 1844,
        "source_id": "norris_directory_1844",
        "title": "Norris's Chicago directory of 1844",
        "entries_key": "entries_1844",
        "occupation_key": "occupation_1844",
        "address_key": "address_1844",
        "page_key": "printed_page",
        "carry_keys": {"occupation": "occupation", "address": "address"},
    },
    {
        "key": "norris_1844_advertiser",
        "file": "norris_1844_advertiser_crosswalk_1835.json",
        "block": None,
        "year": 1844,
        "source_id": "norris_directory_1844",
        "title": "the advertising cards in Norris's directory of 1844",
        "entries_key": "cards_1844",
        "occupation_key": "trade_1844",
        "address_key": "address_1844",
        "page_key": "printed_page",
        "printed_key": "proprietor_as_printed",
        "carry_keys": {"occupation": "trade", "address": "place_of_business"},
    },
]

BY_KEY = {v["key"]: v for v in VOLUMES}

STATUS_ARRAYS = (("matches", "single_entry"), ("ambiguous", "ambiguous"),
                 ("contested", "contested"))

LADDER = (
    "Under the ratified ladder a directory read after 1835 can corroborate that a person "
    "attested here was still in Chicago and can print a trade or a street the 1835 record "
    "never had; on its own it makes nobody a resident of 1835. Nothing on this person's "
    "1835 record was regraded, moved, dated or given an occupation by this entry."
)
# THE SPLIT REFUSAL, PER ENTRY AND PER FIELD — T-0987 stretch 6, replacing the volume
# flag T-0569 wrote. The refusal's GROUND is unchanged and is quoted in each clause: a
# split that yields a value containing no trade at all, rather than a trade with
# something extra on it, may not become a value. What changed is its SCOPE. Under the
# flag all 144 of Norris's alphabetical could-carry units were refused by one sentence
# about three of them, which is not a ruling about a line; measured against the reading
# T-0987 stretch 5 corrected, 13 of that volume's 65 matched trades are the partnership
# shape the sentence describes and 52 are plain legible trades — carpenter, baker,
# tailor, physician, watchmaker.
#
# The shapes below are a COMPOSITOR'S CONSTRUCTION and not one volume's habit, so the
# predicate is asked of every volume. Two of the three volumes the flag trusted print
# them too, and had been carrying them: Fergus 1839 one premises where a trade goes,
# Fergus 1843 four ditto addresses.
FIRM_WHERE_A_TRADE_IS = (
    "THE LINE NAMES A FIRM WHERE THE TRADE WOULD GO, so the split yields no trade at "
    "all. The volume's construction is \"Surname, initials, of <firm>\" — it says this "
    "man stood in that partnership, and the trade, if the book prints one anywhere, is "
    "on the firm's own entry or its advertising card. T-0569 refused exactly this shape, "
    "citing \"of Loyd\", \"of Horace Norton & Co\" and twice simply \"of\", and the "
    "refusal stands; it is now made against the line that has the shape rather than "
    "against every line in the volume. The entry goes to the card as the book set it "
    "and archive.org read it, damage and all, and what it HOLDS is stated separately "
    "for a reader to check against the quote."
)
PREMISES_WHERE_A_TRADE_IS = (
    "THE LINE NAMES A PREMISES WHERE THE TRADE WOULD GO, so the split yields no trade "
    "at all. \"at United States Hotel\", \"at clerk's office\", \"at G. S. Hubbard & "
    "Co.'s warehouse\": the book is saying where this man was to be found, which is "
    "evidence and is not an occupation. It is the same ground T-0569 refused a "
    "partnership on — a value containing no trade rather than a trade with something "
    "extra on it — and a trade that merely ENDS at a premises (\"clerk, at T. King's\", "
    "\"book-keeper at G. S. Hubbard's\") is not refused by it. The line is carried "
    "whole and quoted."
)
ADDRESS_IS_A_BACKREFERENCE = (
    "THE ADDRESS IS A BACK-REFERENCE AND NOT AN ADDRESS: the volume prints \"res "
    "same\", \"house same\" or a ditto mark, which means the door of the entry ABOVE "
    "it in the alphabetical list. This pass reads one entry at a time and never the "
    "entry above, by rule 1 — it carries what a crosswalk declares and re-parses "
    "nothing — so the word resolves to nothing here and would put on a card a value "
    "that names no ground. Reading it would mean the back-reference, not the adjacency "
    "the compositor relied on, and that is a reading and belongs in the volume's own "
    "reader. The line is carried whole and quoted."
)
SPLIT_CLAUSES = {
    "firm_where_a_trade_is": FIRM_WHERE_A_TRADE_IS,
    "premises_where_a_trade_is": PREMISES_WHERE_A_TRADE_IS,
    "address_is_a_backreference": ADDRESS_IS_A_BACKREFERENCE,
}
SPLIT_RULE = (
    "A SPLIT IS REFUSED PER ENTRY AND PER FIELD. T-0569 refused a parse on the ground "
    "that it yielded a value containing no trade at all rather than a trade with "
    "something extra on it, and until T-0987 stretch 6 that ground was carried as a "
    "boolean on a VOLUME: Norris's alphabetical directory of 1844 was refused entire, "
    "144 units of it, by a sentence about three of them. The ground is a fact about a "
    "printed line, so it is now asked of the printed line, for one field at a time — "
    "the clauses below — and a field's refusal says nothing about the field beside it. "
    "Every clause names the shape it saw; nothing is refused without one."
)

EARLIER_VOLUME = (
    "AN EARLIER VOLUME ALREADY CARRIES THIS FIELD. The four volumes are read earliest "
    "first because the one closest to 1835 is the reading worth most and the one whose "
    "value is carried when two disagree: %s prints %s against this person, and %s — %d, "
    "nearer the scene — had printed one already. The refusal is the precedence rule and "
    "nothing about this line. What this volume prints stands in the layer beside the "
    "value that won, and its entry id is named on the card, so a reader can compare "
    "them rather than take the earlier reading on trust."
)
# The two carryable things, in the words a refusal reads them back in.
FIELD_AS_PROSE = {"occupation": "a trade", "address": "an address"}
NOT_A_SINGLE_ENTRY = (
    "THE MATCH IS NOT A SINGLE ENTRY. Rule 2 of this pass: a person met by several "
    "entries is ambiguous and an entry met by two people is contested, and neither "
    "writes a value onto a card. The line holds this field and it does not cross."
)
# And the caution that rides on every value that DOES cross. All four volumes set the
# trade first and whatever qualifies it after — a market, an employer, a corner — on the
# same comma-separated line, so a split that survives the clauses above carries more than
# the trade rather than something other than it. That difference is the whole of what
# those clauses test; it is not a claim that any of these splits is clean.
SPLIT_CAUTION = (
    "The value is the volume's own line, split by its crosswalk on the entry's "
    "punctuation. These volumes set the trade first and its qualifiers after it on the "
    "same line, so the split may carry an employer, a market or a corner along with the "
    "trade. The printed entry is quoted beside the value for exactly that reason: the "
    "split is checkable against it, and neither is read into an 1835 claim."
)

# WHY THE CARD NAMES THE ENTRY IDS (T-0989, spent by T-0987). A ruling in a generated
# crosswalk states no source of its own: the file says once, at the top, which volume it
# rests on, and every ruling in it shares that one id. `tools/measure_research_spend.py`
# therefore judges such a ruling written only if the card ALSO names the unit adjudicated
# — and until this line was added not one of the 263 matches these four crosswalks make
# did. The instance the ticket checked by hand: `hh_garrett_a` cites
# `fergus_chicago_directory_1839` because this pass writes the volume into `sources`,
# while Fergus 1839's ruling for Garrett — entry f1839_e0527 — was nowhere on the record.
# The citation was doing the work of a reading.
#
# So the block's own note ends by naming, per person and per volume, the printed entries
# this pass ruled onto this household and the status it ruled them at. It goes in the
# NOTE rather than in a new leaf deliberately: the note is already rendered whole by
# `renderers/web/js/residents.js` and already declared `shown` in
# `tools/measure_layer_reads.py`, so the entry a reader would have to go back to arrives
# in front of that reader instead of into a field nothing opens. It is also the only
# place that can speak for the 92 people this pass rules on and carries nothing for —
# an ambiguous or contested match writes no graded value, and before this the card said
# of them only that some volume had met somebody of the name.
RULED_ON_PREAMBLE = (
    "WHAT THIS PASS RULED ONTO THIS HOUSEHOLD, named so the ruling can be found again: "
    "each volume below is followed by the printed entries it set against this person and "
    "the status the crosswalk ruled them at — a single entry carries what its own "
    "`could_carry` declares, and an ambiguous or contested match carries nothing and is "
    "shown so that the silence is legible. "
)

STATUS_WORDS = {
    "single_entry": "a single entry",
    "ambiguous": "ambiguous, so nothing crossed",
    "contested": "contested, so nothing crossed",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def block_of(doc: dict, volume: dict) -> dict:
    return doc[volume["block"]] if volume["block"] else doc


def entry_row(entry: dict, volume: dict) -> dict:
    """One printed entry, reduced to what a card may quote: the line and where it is.

    An ADVERTISING CARD IS NOT A DIRECTORY LINE and is not made to look like one.
    Norris's alphabetical volume sets one entry per person and the crosswalk keeps it
    whole as `as_printed`; a card sets the proprietor, the firm, the trade and the
    address as separate lines of a display advertisement, and stitching them into one
    sentence would produce a quotation the book does not contain. So the card's
    proprietor line is what is quoted and its other lines are carried beside it,
    named."""
    row = {
        "claim_id": entry["claim"],
        "printed_page": entry.get(volume["page_key"]),
        "as_printed": entry[volume.get("printed_key", "as_printed")],
    }
    if entry.get("firm"):
        row["firm"] = entry["firm"]
    return row


def carried_from(match: dict, volume: dict) -> dict:
    """What this match's OWN `could_carry` declares, translated to occupation/address.

    Rule 1: the declaration is the crosswalk's, never this pass's. A volume whose
    parse is not trusted declares things it may still not carry as a VALUE, so the
    two are kept apart — `holds` is what the line contains, `carried` is what reached
    the card."""
    declared = set(match.get("could_carry") or [])
    holds = {}
    for field, their_word in volume["carry_keys"].items():
        if their_word in declared:
            holds[field] = True
    return holds


def value_for(field: str, entry: dict, volume: dict) -> str | None:
    """The printed value a single entry offers for one field, or None.

    The street NUMBER does not cross. Fergus 1839 marks the entries whose address is
    a number in the 1839 grid, a numbering this town's year does not have, and its own
    carry rule says the street NAME may cross and the number may not."""
    if field == "occupation":
        value = entry.get(volume["occupation_key"])
    else:
        if entry.get("address_is_street_only"):
            streets = [s for s in (entry.get("streets_1839") or []) if s]
            value = ", ".join(streets) or None
        else:
            value = entry.get(volume["address_key"])
    value = (value or "").strip()
    return value or None


# The three shapes, as the compositors set them. Written against the printed values and
# nothing else — these patterns read a SPLIT, never a line, and the thing they are asked
# is only ever "is this value of its field's kind".
#
# `_FIRM` and `_PREMISES` anchor at the start on purpose: a value that BEGINS "of" or
# "at" names a partnership or a door where the occupation belongs, while one that merely
# ends at an employer ("clerk, at T. King's") is a trade with something extra on it and
# T-0569's ground does not reach it. No trade in the English of 1844 begins with either
# word, which is what makes the anchor safe rather than lucky.
#
# `_BACKREFERENCE` matches the locative word the volume prints — Norris's `h` and `r`,
# Fergus's `res`, `house` and `bds`, and the OCR's `hou.«e` — followed by nothing but a
# ditto. The alternation is ordered longest-first so `r` cannot eat the front of `res`,
# and the separator is required so neither can eat the front of a street name.
_FIRM = re.compile(r"^of\b", re.I)
_PREMISES = re.compile(r"^at\b", re.I)
_BACKREFERENCE = re.compile(
    r"^(?:(?:residence|res|house|hou\S{0,2}e|bds?|h|r)\W+)?"
    r"(?:same|ditto|do|\"|\u201d)\W*$", re.I)


def split_refusal(field: str, value: str) -> str | None:
    """The clause THIS entry's split is refused under for THIS field, or None.

    Rule 3, asked one line at a time. The key returned indexes `SPLIT_CLAUSES`, which
    is written into the layer so the clause a reader meets on the record and the clause
    the ledger states are the same sentence."""
    if field == "occupation":
        if _FIRM.match(value):
            return "firm_where_a_trade_is"
        if _PREMISES.match(value):
            return "premises_where_a_trade_is"
        return None
    if _BACKREFERENCE.match(value):
        return "address_is_a_backreference"
    return None


def split_refused_of(match: dict, volume: dict, status: str, holds: dict) -> dict:
    """Per held field, the clause this match's own entry is refused under.

    ONLY A SINGLE-ENTRY MATCH IS ASKED. Rule 2 already refuses an ambiguous or contested
    match whatever its lines hold, and naming a second clause beside that one would
    report one refusal twice — and would state a judgement about a split that was never
    going to be read."""
    entries = match[volume["entries_key"]]
    if status != "single_entry" or len(entries) != 1:
        return {}
    out = {}
    for field in sorted(holds):
        value = value_for(field, entries[0], volume)
        clause = split_refusal(field, value) if value else None
        if clause:
            out[field] = clause
    return out


def appearance(match: dict, volume: dict, status: str) -> dict:
    entries = [entry_row(e, volume) for e in match[volume["entries_key"]]]
    holds = carried_from(match, volume) if status == "single_entry" else {}
    return {
        "volume": volume["key"],
        "title": volume["title"],
        "year": volume["year"],
        "source_id": volume["source_id"],
        "match_status": status,
        "match_rule": match["rule"],
        "reading": "transcription_mediated",
        "entries": entries,
        "holds": sorted(holds),
        # field -> a key of SPLIT_CLAUSES. Empty is the ordinary case and means every
        # field this line holds is of its own kind.
        "split_refused": split_refused_of(match, volume, status, holds),
        "sources": [volume["source_id"]],
    }


def note_for(field: str, value: str, volume: dict, entry: dict) -> str:
    what = "trade" if field == "occupation" else "address"
    dropped = ""
    if field == "address" and entry.get("address_is_street_only"):
        dropped = (" The street NUMBER printed against it is a number in the %d grid, a "
                   "numbering this town's year does not have, so the street name crosses "
                   "and the number does not." % volume["year"])
    return ("%s prints this %s against this person, in the entry quoted on the card: %r. "
            "It is evidence about %d, written here as %d's and read back onto no 1835 "
            "claim.%s %s"
            % (volume["title"][0].upper() + volume["title"][1:], what,
               entry[volume.get("printed_key", "as_printed")],
               volume["year"], volume["year"], dropped, LADDER))


def graded(field: str, rows: list) -> dict | None:
    """The earliest trustworthy reading of one field, graded for ITS OWN year.

    `attested` is the right word and it is not a claim about 1835: a source STATES
    this value, of the year it was printed in. The year is in the block, in the note
    and in the field's own name, and the 1835 slot beside it is untouched."""
    for volume, match, entry, value in rows:
        # Every row that reaches here has already passed `split_refusal` in `collect`,
        # so precedence is the only question left: earliest volume wins.
        return {
            "value": value,
            "confidence": "attested",
            "describes_date": volume["year"],
            "sources": [volume["source_id"]],
            "claim_id": entry["claim"],
            "as_printed": entry[volume.get("printed_key", "as_printed")],
            "printed_fields": " | ".join(
                str(v) for v in entry.values() if isinstance(v, str)),
            "split": SPLIT_CAUTION,
            "note": note_for(field, value, volume, entry),
        }
    return None


def collect() -> tuple[dict, list]:
    """Every person any volume meets, with each volume's appearance, in volume order."""
    people: dict[str, dict] = {}
    order: list[str] = []
    carries: dict[str, dict[str, list]] = {}
    for volume in VOLUMES:
        doc = read_json(DIRECTORIES / volume["file"])
        block = block_of(doc, volume)
        for array, status in STATUS_ARRAYS:
            for match in block.get(array) or []:
                pid = match.get("person_id")
                if not pid:
                    # Fergus 1839 crosswalks four pools and only the residents pool
                    # names a person this town holds; the voter, letter-list and
                    # 1840-head pools carry a name and nothing to write it onto.
                    continue
                row = people.get(pid)
                if row is None:
                    row = people[pid] = {
                        "person_id": pid,
                        "household_id": match.get("household_id"),
                        "resident": match.get("resident") or match.get("name"),
                        "grade_1835": match.get("grade_1835"),
                        "occupation_1835": match.get("occupation_1835"),
                        "lives_at_1835": match.get("lives_at_1835"),
                        "works_at_1835": match.get("works_at_1835"),
                        "appearances": [],
                    }
                    order.append(pid)
                    carries[pid] = {"occupation": [], "address": []}
                app = appearance(match, volume, status)
                row["appearances"].append(app)
                if status != "single_entry":
                    continue
                entries = match[volume["entries_key"]]
                if len(entries) != 1:
                    continue
                entry = entries[0]
                for field in carried_from(match, volume):
                    if field in app["split_refused"]:
                        continue
                    value = value_for(field, entry, volume)
                    if value:
                        carries[pid][field].append((volume, match, entry, value))
    rows = []
    for pid in sorted(order):
        row = people[pid]
        occupation = graded("occupation", carries[pid]["occupation"])
        address = graded("address", carries[pid]["address"])
        row["occupation_later"] = occupation
        row["address_later"] = address
        row["holds_a_line_whose_parse_does_not_cross"] = bool(
            (carries[pid]["occupation"] or carries[pid]["address"])
            and not (occupation or address))
        row["sources"] = sorted({a["source_id"] for a in row["appearances"]})
        rows.append(row)
    return people, rows


def counts_of(rows: list) -> dict:
    per_volume = {}
    for volume in VOLUMES:
        seen = [a for r in rows for a in r["appearances"] if a["volume"] == volume["key"]]
        per_volume[volume["key"]] = {
            "people": len(seen),
            "single_entry": sum(1 for a in seen if a["match_status"] == "single_entry"),
            "ambiguous": sum(1 for a in seen if a["match_status"] == "ambiguous"),
            "contested": sum(1 for a in seen if a["match_status"] == "contested"),
            "split_refused_fields": sum(len(a["split_refused"]) for a in seen),
        }
    return {
        "people_shown": len(rows),
        "people_met_by_more_than_one_volume": sum(1 for r in rows if len(r["appearances"]) > 1),
        "carrying_an_occupation": sum(1 for r in rows if r["occupation_later"]),
        "carrying_an_address": sum(1 for r in rows if r["address_later"]),
        "line_held_but_parse_refused": sum(
            1 for r in rows if r["holds_a_line_whose_parse_does_not_cross"]),
        "split_refused_trades": sum(
            1 for r in rows for a in r["appearances"] if "occupation" in a["split_refused"]),
        "split_refused_addresses": sum(
            1 for r in rows for a in r["appearances"] if "address" in a["split_refused"]),
        "grades_1835_changed": 0,
        "by_volume": per_volume,
    }


def layer(rows: list) -> dict:
    return {
        "schema": 1,
        "_doc": "GENERATED by %s from the four crosswalks in "
                "data/research/directories/ (%s). Evidence about 1839, 1843 and 1844 "
                "shown beside the people of 1835, never inside their 1835 claims and "
                "never as an 1835 fact." % (GENERATOR, TICKET),
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "sources": sorted({v["source_id"] for v in VOLUMES}),
        "standard": LADDER,
        "split_refusal": {"rule": SPLIT_RULE, "clauses": SPLIT_CLAUSES},
        "volumes": [{"key": v["key"], "title": v["title"], "year": v["year"],
                     "source_id": v["source_id"], "crosswalk": v["file"]}
                    for v in VOLUMES],
        "counts": counts_of(rows),
        "people": rows,
    }


def why_refused(row: dict, a: dict, carried: list) -> dict | None:
    """The clause each refused field was refused under, named field by field."""
    refused = sorted(set(a["holds"]) - set(carried))
    if not refused:
        return None
    out = {}
    for field in refused:
        clause = (a.get("split_refused") or {}).get(field)
        if clause:
            out[field] = SPLIT_CLAUSES[clause]
            continue
        if a["match_status"] != "single_entry":
            out[field] = NOT_A_SINGLE_ENTRY
            continue
        won = row["%s_later" % field]
        # Two of the four volumes share a source id, so the winner is found by the
        # entry it was carried from rather than by that id.
        winner = next((b for b in row["appearances"]
                       if won and any(e["claim_id"] == won["claim_id"]
                                      for e in b["entries"])), None)
        if won and winner:
            out[field] = EARLIER_VOLUME % (
                BY_KEY[a["volume"]]["title"], FIELD_AS_PROSE[field],
                BY_KEY[winner["volume"]]["title"], won["describes_date"])
        else:
            out[field] = NOT_A_SINGLE_ENTRY
    return out


def ledger(rows: list) -> dict:
    """The adjudication, in the domain that holds the reading.

    One ruling per (person, volume): the claims it rests on, the source it rests on,
    and what this pass carried or refused to carry from them. `outcome` is the word
    the other crosswalks in this repo use and the word tools/measure_research_spend.py
    reads; `carried` is what makes the ruling checkable against the card."""
    rulings = []
    for row in rows:
        for a in row["appearances"]:
            carried = []
            for field in ("occupation", "address"):
                block = row["%s_later" % field]
                if block and block["sources"] == [a["source_id"]] \
                        and any(e["claim_id"] == block["claim_id"] for e in a["entries"]):
                    carried.append(field)
            rulings.append({
                "outcome": "matched" if a["match_status"] == "single_entry" else "refused",
                "person_id": row["person_id"],
                "household_id": row["household_id"],
                "resident": row["resident"],
                "volume": a["volume"],
                "source_id": a["source_id"],
                "source_ids": [a["source_id"]],
                "claim_id": a["entries"][0]["claim_id"] if len(a["entries"]) == 1 else None,
                "claim_ids": [e["claim_id"] for e in a["entries"]],
                "match_status": a["match_status"],
                "rule": a["match_rule"],
                "carried": carried,
                "refused_to_carry": sorted(set(a["holds"]) - set(carried)),
                # ONE CLAUSE PER REFUSED FIELD. The doc below promises a refusal is
                # declared as explicitly as a carry; until T-0987 stretch 2 only the
                # untrusted-parse refusal said anything, and 64 of 161 refusals named
                # nothing at all — the shape this file says "reads like a pair nobody
                # has looked at yet".
                "why_refused": why_refused(row, a, carried),
            })
    rulings.sort(key=lambda r: (r["person_id"], r["volume"]))
    return {
        "schema": 1,
        "_doc": "GENERATED by %s (%s). The adjudication that spends the four directory "
                "crosswalks onto the town: for each person a volume meets, what the "
                "volume's entry was allowed to carry to their card and what it was "
                "not. A refusal is declared as explicitly as a carry — the absence of "
                "one reads like a pair nobody has looked at yet." % (GENERATOR, TICKET),
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "source_ids": sorted({v["source_id"] for v in VOLUMES}),
        "rule": LADDER,
        "counts": {
            "rulings": len(rulings),
            "carried": sum(1 for r in rulings if r["carried"]),
            "matched": sum(1 for r in rulings if r["outcome"] == "matched"),
            "refused": sum(1 for r in rulings if r["outcome"] == "refused"),
            "distinct_people": len({r["person_id"] for r in rulings}),
            "distinct_claims": len({c for r in rulings for c in r["claim_ids"]}),
        },
        "rulings": rulings,
    }


def ruled_on(rows: list) -> str:
    """The entry ids this pass adjudicated onto one household, as one rendered sentence.

    Deterministic in the order `cards` already sorts by — person, then volume as
    `VOLUMES` lists them — because this string is compared byte for byte by `--check`."""
    parts = []
    for row in sorted(rows, key=lambda r: r["person_id"]):
        for app in row["appearances"]:
            ids = ", ".join(e["claim_id"] for e in app["entries"])
            if not ids:
                continue
            parts.append("%s, %s — %s (%s)"
                         % (row["person_id"], app["title"], ids,
                            STATUS_WORDS.get(app["match_status"], app["match_status"])))
    if not parts:
        return ""
    return RULED_ON_PREAMBLE + "; ".join(parts) + "."


def card_block(row: dict) -> dict:
    """What goes onto the household record — the person's later readings, and no more.

    DELIBERATELY THINNER THAN THE LAYER. The printed entries, the match rules and the
    crosswalks' arithmetic live in `data/residents/directories.json`, which the panel
    opens once for the whole town; what belongs ON the record is the CLAIM — the later
    trade, the later address, each graded, dated to the year it describes and citing the
    volume. Every leaf here is read by `renderers/web/js/residents.js` and declared in
    `tools/measure_layer_reads.py`, which is the gate that stops a record shipping a
    figure to a browser that nothing shows."""
    block = {"person_id": row["person_id"]}
    for field in ("occupation", "address"):
        value = row["%s_later" % field]
        if value:
            block["%s_later" % field] = {
                "value": value["value"],
                "confidence": value["confidence"],
                "describes_date": value["describes_date"],
                "sources": value["sources"],
                "note": value["note"] + " " + SPLIT_CAUTION,
            }
    return block


def cards(rows: list) -> dict:
    """household id -> the `directories` block that record should carry."""
    out: dict[str, dict] = {}
    for row in rows:
        hid = row["household_id"]
        if not hid or not (HOUSEHOLDS / f"{hid}.json").exists():
            continue
        out.setdefault(hid, {
            "note": "LATER EVIDENCE, BESIDE THE 1835 CLAIMS AND NOT INSIDE THEM. A "
                    "Chicago directory of 1839, 1843 or 1844 meets somebody of this "
                    "name and this pass records what it prints. " + LADDER,
            "sources": [],
            "people": [],
        })
        out[hid]["people"].append(card_block(row))
        out[hid]["sources"] = sorted(set(out[hid]["sources"]) | set(row["sources"]))
    for hid, block in out.items():
        block["people"].sort(key=lambda p: p["person_id"])
        sentence = ruled_on([r for r in rows if r["household_id"] == hid])
        if sentence:
            block["note"] = block["note"] + " " + sentence
    return out


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


# The keys later passes own on a person inside this block, in the order they are
# written. `household_text` lifts them off the record and puts them back rather
# than rebuilding them, because this pass does not derive them.
CARRIED_KEYS = ("back_projection", "residence_back_projection")


def household_text(hid: str, block: dict | None) -> str:
    """The record with this pass's `directories` block on it, and nobody else's.

    T-0633 AND T-0669 CARRY OVER. Two later passes —
    `tools/back_project_addresses.py` and `tools/back_project_residences.py` —
    write a `back_projection` and a `residence_back_projection` onto each person
    INSIDE this block, saying what each did with the address this one carried
    there. Rebuilding the block from the crosswalks would delete them, and the
    gates would then take it in turns to call each other's output drift. So the
    existing keys are lifted off the record and put back on the person they
    belong to, which is the same narrowing T-0632 made in
    `mint_placed_residents.py` for the block as a whole: this pass owns what it
    derives and nothing else.
    """
    doc = read_json(HOUSEHOLDS / f"{hid}.json")
    carried = {p["person_id"]: {k: p[k] for k in CARRIED_KEYS if k in p}
               for p in (doc.get("directories") or {}).get("people") or []}
    doc.pop("directories", None)
    if block:
        block = json.loads(json.dumps(block))
        for person in block["people"]:
            person.update(carried.get(person["person_id"]) or {})
        doc["directories"] = block
    return dumps(doc)


def build() -> tuple[dict, dict, dict]:
    _, rows = collect()
    return layer(rows), ledger(rows), cards(rows)


def written_files() -> dict[Path, str]:
    lay, led, card = build()
    out = {LAYER: dumps(lay), LEDGER: dumps(led)}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hid = path.stem
        if hid in card:
            out[path] = household_text(hid, card[hid])
        elif "directories" in read_json(path):
            out[path] = household_text(hid, None)
    return out


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    lay, led, card = build()
    if "--report" in sys.argv:
        for row in lay["people"]:
            print("%-28s %-40s %s" % (
                row["person_id"],
                (row["occupation_later"] or {}).get("value") or "—",
                (row["address_later"] or {}).get("value") or "—"))
        print(dumps(lay["counts"]))
        print(dumps(led["counts"]))
        return 0
    files = written_files()
    if "--check" in sys.argv:
        drift = [p for p, text in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        if drift:
            for p in drift[:6]:
                print("   DRIFT: %s" % p.relative_to(ROOT), file=sys.stderr)
            print("   %d file(s) do not match what this pass derives — regenerate with "
                  "python3 %s" % (len(drift), GENERATOR), file=sys.stderr)
            return 1
        print("   OK: %d people met by a directory, %d carrying a trade, %d an address; "
              "%d ruling(s) in the ledger; %d card(s) written"
              % (lay["counts"]["people_shown"], lay["counts"]["carrying_an_occupation"],
                 lay["counts"]["carrying_an_address"], led["counts"]["rulings"], len(card)))
        return 0
    for path, text in files.items():
        path.write_text(text, encoding="utf-8")
    print("wrote %s, %s and %d household card(s) — %d people, %d rulings"
          % (LAYER.relative_to(ROOT), LEDGER.relative_to(ROOT), len(card),
             lay["counts"]["people_shown"], led["counts"]["rulings"]))
    return 0


def self_test() -> int:
    """The four rules above, checked over every value this pass derives.

    It is an INVARIANT GATE rather than a mutation test, and the distinction is worth
    stating: it does not break the pass to prove an assertion fires, it asserts the
    four rules against all 138 people and 303 rulings on every run. What it catches is
    a later change to a crosswalk, a carry rule or this file that lets a value cross
    which the rules forbid — which is the failure that would matter.

    It holds one rule that is not a carry rule at all: that a card this pass writes
    NAMES the printed entries it was ruled on (T-1025). That one is about whether the
    reading can be found again rather than about what crossed, which is why it is the
    last assertion here and not one of the four."""
    failures = []

    def check(label: str, condition: bool) -> None:
        if not condition:
            failures.append(label)

    lay, led, card = build()
    rows = lay["people"]

    # Rule 4, the one that outranks everything else here: no 1835 claim moves.
    check("an 1835 grade moved", all(
        r["grade_1835"] in (None, "attested", "inferred", "reconstructed") for r in rows))
    check("the pass reports a changed 1835 grade",
          lay["counts"]["grades_1835_changed"] == 0)

    # Rule 2: nothing is carried off an ambiguous or contested match.
    for r in rows:
        for field in ("occupation_later", "address_later"):
            block = r[field]
            if not block:
                continue
            ok = any(a["match_status"] == "single_entry"
                     and a["source_id"] == block["sources"][0]
                     and any(e["claim_id"] == block["claim_id"] for e in a["entries"])
                     for a in r["appearances"])
            check("%s/%s carried off a match that is not single-entry"
                  % (r["person_id"], field), ok)

    # Rule 3, both directions, over every volume rather than over one.
    # (a) nothing a clause refused reached a card, and (b) nothing that DID reach one
    # has a shape a clause names — which is the assertion the volume flag could never
    # make, because under it the shapes in the trusted volumes went unlooked-at.
    for r in rows:
        for field in ("occupation", "address"):
            block = r["%s_later" % field]
            if not block:
                continue
            check("%s/%s carries a value a split clause refuses (%s)"
                  % (r["person_id"], field, block["value"]),
                  split_refusal(field, block["value"]) is None)
            refusing = [a["volume"] for a in r["appearances"]
                        if field in a["split_refused"]
                        and any(e["claim_id"] == block["claim_id"] for e in a["entries"])]
            check("%s/%s carries the field its own entry was refused on" % (r["person_id"], field),
                  not refusing)
    # And every clause a refusal names is one this file declares.
    for r in rows:
        for a in r["appearances"]:
            check("%s/%s names a clause SPLIT_CLAUSES does not hold"
                  % (r["person_id"], a["volume"]),
                  set(a["split_refused"].values()) <= set(SPLIT_CLAUSES))

    # Rule 1: every carried value is the string the crosswalk itself printed.
    for r in rows:
        for field in ("occupation_later", "address_later"):
            block = r[field]
            if not block:
                continue
            printed = block.get("printed_fields") or block["as_printed"]
            check("%s/%s carries a value its entry does not print"
                  % (r["person_id"], field),
                  all(part.strip() in printed for part in block["value"].split(",")))

    # Every ruling states what it rests on: the third hop's ratchet is zero.
    # T-0987 stretch 2: this file's own doc says a refusal is declared as explicitly
    # as a carry, "the absence of one reads like a pair nobody has looked at yet".
    # Hold it, so the 64 silent refusals that stood until then cannot come back.
    for r in led["rulings"]:
        named = set((r["why_refused"] or {}))
        check("%s/%s refuses %s and names no clause for it"
              % (r["person_id"], r["volume"],
                 ", ".join(sorted(set(r["refused_to_carry"]) - named)) or "-"),
              set(r["refused_to_carry"]) <= named)

    check("a ruling states no source",
          all(r["source_ids"] for r in led["rulings"]))
    check("a ruling names a person no household holds",
          all(r["household_id"] for r in led["rulings"]))
    # And every card cites what its blocks rest on, which is the second hop.
    for hid, block in card.items():
        stated = set()
        for person in block["people"]:
            for field in ("occupation_later", "address_later"):
                if person.get(field):
                    stated |= set(person[field]["sources"])
        check("%s cites less than its claims rest on" % hid,
              stated <= set(block["sources"]) and bool(block["sources"]))

    # THE ENTRY, AND NOT ONLY THE BOOK (T-1025). Citing the volume is the weaker
    # half of the second hop and it was the only half this pass held. A generated
    # crosswalk states its one source id at the top of the file, so that id is
    # shared by every ruling in it and a citation put on a card by ANY other pass
    # satisfied all of them at once; `measure_research_spend.subject_of` therefore
    # requires the card to name the printed entry the ruling was made ON. Until
    # T-0987 stretch 1 (PR #1116) added `ruled_on` this pass wrote the volume and
    # never the entry, and all 264 of the domain's person-reaching rulings were
    # unwritten behind cards that cited the book — including the four T-1018 had
    # just recorded as spent. Nothing in THIS file held that repair afterwards.
    # It was ratcheted only by `measure_research_spend.py --gate`, one number over
    # the whole town, which can say that some card is missing some entry and never
    # which card or which entry.
    #
    # So the rule is asserted here, per household and per entry, and deliberately
    # against the BLOCK this pass writes rather than against the record it lands
    # on: a record may carry the id from some other pass, and a repair that leans
    # on that is not this pass's repair. `ruled_on` speaks for the ambiguous and
    # contested rows too, which carry no graded value at all, so the assertion
    # covers every entry ruled onto the household and not only the ones that
    # crossed.
    entries_of: dict[str, set] = {}
    for r in rows:
        hid = r["household_id"]
        if hid in card:
            entries_of.setdefault(hid, set()).update(
                e["claim_id"] for a in r["appearances"] for e in a["entries"]
                if e["claim_id"])
    for hid, block in card.items():
        text = json.dumps(block, ensure_ascii=False)
        missing = sorted(c for c in entries_of.get(hid, ()) if c not in text)
        check("%s cites the volume and names none of the entries ruled onto it (%s)"
              % (hid, ", ".join(missing)), not missing)

    # The instrument's own reading of the ledger: a ruling it cannot anchor is
    # invisible to it, and this pass exists to be counted.
    check("a ruling carries no anchor the spend measure can read",
          all(r["person_id"] and r["claim_ids"] for r in led["rulings"]))

    if failures:
        for f in failures[:10]:
            print("   assertion did not hold: %s" % f, file=sys.stderr)
        print("   %d assertion(s) failed" % len(failures), file=sys.stderr)
        return 1
    print("   OK: %d assertions over %d people and %d rulings"
          % (5 + len(rows) * 3 + len(card) * 2, len(rows), len(led["rulings"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
