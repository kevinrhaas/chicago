#!/usr/bin/env python3
"""The written ruling on all 718 name-on-a-roll units (T-1297).

    python3 tools/spend_name_on_a_roll_rulings.py            write the three registers
    python3 tools/spend_name_on_a_roll_rulings.py --check    they re-derive; nothing drifted
    python3 tools/spend_name_on_a_roll_rulings.py --self-test the rules below, held over what
                                                             they derive

WHY THIS EXISTS. T-1234 gave the research-spend ledger a place to write a ruling down:
`data/research/spend_rulings.json`, consulted only where a reading's own dispositions run
out, a named rule with a stated reason and a note on every single unit it closes. T-1296
then showed that such a register may be DERIVED where the corpus is too large to type —
1,572 land-sale rows, sitting beside the register they rule, re-derived by their own
`--check`. This is the same instrument over the third body the epic left open: 718 units
that are all one question, a NAME ON A ROLL, in three domains.

    civic        496  the 1833-1835 poll and tax lists, the 1832 Black Hawk War
                      enrollments at Chicago, and seventeen town findings
    census_1830  204  the 1830 heads of family of the Peoria & Putnam division, and
                      four findings about the schedule
    directories   18  the retrospective town findings of Norris 1844 and Fergus 1839

and every ruling is derived from the files that already carry the judgement:

    data/research/civic/records/*.json              the rolls as read
    data/research/civic/voter_crosswalk.json        the poll and tax identities
    data/research/civic/blackhawk_war_crosswalk.json the 1832 enrollments set beside them
    data/research/census_1830/records/*.json        the schedule as read
    data/research/census_1830/resident_crosswalk.json the 1830 identities, positive and
                                                    negative alike
    the claim rows themselves, for the town findings

NOTHING HERE RE-ADJUDICATES AN IDENTITY, MOVES A GRADE, MINTS A PERSON OR WRITES TO
data/residents/. Every note is built out of the row's own fields — its list, its date, its
company, its crosswalk outcome — so a reader can put the note beside the row and see that
it says what the row says.

THE STANDING RULE THIS BODY WAS READ UNDER, and the one every ruling below obeys: A NAME
ON A ROLL IS NOT A RESIDENCE ON THE SCENE DATE. The rolls are dated 1830, 1832, 1833,
1834 and 1835; under the ladder ratified 2026-09-03 an EARLIER source corroborates and
dates and never promotes, because a man at Chicago in 1830 or 1832 is not thereby at
Chicago on 1 July 1835, and a LATER source does not promote either. What a roll can do is
BOUND the presence of a person the town already holds, and that bound is the arrival
pass's to draw, not this file's.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICKET = "T-1297"
GENERATOR = "tools/spend_name_on_a_roll_rulings.py"

VOTER_RECORDS = ROOT / "data/research/civic/records/voter_lists_1833_1835.json"
VOTER_CROSSWALK = ROOT / "data/research/civic/voter_crosswalk.json"
BLACKHAWK_RECORDS = ROOT / "data/research/civic/records/blackhawk_war_1832_chicago.json"
BLACKHAWK_CROSSWALK = ROOT / "data/research/civic/blackhawk_war_crosswalk.json"
CENSUS_RECORDS = ROOT / "data/research/census_1830/records/schedule_chicago_1830.json"
CENSUS_CROSSWALK = ROOT / "data/research/census_1830/resident_crosswalk.json"

# The arrival pass takes every bound a roll can put on a person the town holds; the
# borderline roster takes every name a roll carries that the town does not hold. Both are
# open tickets with exactly that field, and a hand-off is not a spend: when either closes,
# these registers go red and the units come back for a real answer. That is the point.
ARRIVAL = "T-1169"
ROSTER = "T-1159"

LADDER = (
    "Under the evidence ladder ratified 2026-09-03 a source EARLIER than the scene date "
    "corroborates and dates and never promotes — a man at Chicago in 1830 or 1832 is not "
    "thereby at Chicago on 1 July 1835 — and a source LATER than it does not promote "
    "either. ")

CIVIC_RULES = {
    "the_poll_book_bounds_a_held_residents_presence": {
        "disposition": "unresolved",
        "ticket": ARRIVAL,
        "statement": (
            "A poll list records a man who presented himself and voted at a town election, "
            "so the entry does place a body in Chicago on the day the list was taken. The "
            "voter crosswalk matches this entry to a person the town already holds, on "
            "surname and on forenames agreeing initial for initial. " + LADDER +
            "What the entry therefore gives is a BOUND on that person's presence — he was "
            "here by this date — and drawing an arrival from a bound is the arrival pass's "
            "work, with the other dated appearances of the same man in front of it. The "
            "unit is handed on unasserted; no card is edited, no confidence moves, and the "
            "identity the crosswalk made is neither re-opened nor strengthened here."),
    },
    "the_1833_tax_roll_bounds_property_and_not_presence": {
        "disposition": "unresolved",
        "ticket": ARRIVAL,
        "statement": (
            "The entry stands on the 1833 TAX list, and this domain's own reading has "
            "already ruled what that list is: 'THE 1833 TAX LIST OF THE TOWN OF CHICAGO IS "
            "A PROPERTY ROLL AND NOT A CHECK ON RESIDENCE' (claims/town_findings_voter_"
            "lists.json v005), settled out of the list's own membership. A man may be "
            "taxed on a town lot he does not live on, so the roll bounds his PROPERTY in "
            "the town and not his body in it. The crosswalk matches the entry to a person "
            "the town holds; the unit is handed to the arrival pass with that limit stated, "
            "so the bound is weighed for what it is rather than read as a residence."),
    },
    "a_roll_agreeing_on_surname_alone_is_never_a_merge": {
        "disposition": "refused",
        "statement": (
            "The crosswalk declares this entry a CANDIDATE and not a match: the town holds "
            "one or more bearers of the surname, and nothing printed in the entry separates "
            "them — an initial that fits two men, or no forename at all. This project's "
            "standing rule is that a surname-only join is always a refusal, and a candidate "
            "is not promoted to a merge by being written down a second time. The row is "
            "refused as a person unit; the crosswalk's candidate stands where it is, for "
            "whatever evidence reaches it next."),
    },
    "the_roll_names_a_person_the_town_does_not_hold": {
        "disposition": "unresolved",
        "ticket": ROSTER,
        "statement": (
            "The entry is a named person on a roll of the Town of Chicago, and the "
            "crosswalk finds no one in the town's households it can be joined to: either no "
            "resident carries the surname, or one does and no forename reading agrees. That "
            "is a name the research READ and the town WITHHELD, which is the borderline "
            "roster's case exactly — it is the file that carries every such name with its "
            "source, its reason and its re-admission class, so that reconstruction names "
            "real people before it invents any. Nothing is minted here and no presence is "
            "asserted; the name is handed on with the roll and date that carry it."),
    },
    "the_1832_enrollment_may_bound_a_rolled_mans_arrival": {
        "disposition": "unresolved",
        "ticket": ARRIVAL,
        "statement": (
            "The Black Hawk War index enrolls this man AT CHICAGO in 1832, and the "
            "crosswalk finds one reading on the 1833-1835 poll and tax lists that agrees "
            "with him initial for initial. The crosswalk is explicit that this is "
            "corroboration and not an identity: the same NAME stands on both, and whether "
            "it is the same MAN it does not say. " + LADDER + "So the enrollment cannot "
            "assert a residence; what it can do, IF the identity holds, is push that man's "
            "presence at Chicago back to 1832, three years before the scene. That is a "
            "candidate bound and the arrival pass owns it, with the identity still open."),
    },
    "an_ambiguous_enrollment_agreement_is_never_a_merge": {
        "disposition": "refused",
        "statement": (
            "The crosswalk calls this enrollment AMBIGUOUS: more than one distinct reading "
            "on the rolls agrees with the index row, or more than one index row agrees with "
            "the same entry, and nothing printed in either separates them. A contested "
            "agreement is a candidate and never a merge, and writing it into a second file "
            "does not settle it. The row is refused as a person unit rather than joined to "
            "a name on the strength of an ambiguity."),
    },
    "the_enrollment_index_prints_no_surname": {
        "disposition": "unresolved",
        "ticket": ROSTER,
        "statement": (
            "The index prints this enrollment WITHOUT a surname comma — the French and "
            "Potawatomi forms, eighty-three of the hundred and thirty-four rows — and the "
            "poll and tax lists are indexed by surname, so there is nothing to compare and "
            "no match is attempted. The name is carried and counted rather than dropped, "
            "which is what the reading was built to do. It is a name the research read at "
            "Chicago in 1832 and the town does not hold, so it goes to the borderline "
            "roster with its form stated as the reason no crosswalk could reach it. NOTHING "
            "IS INFERRED ABOUT WHO THIS PERSON WAS, and nothing about the 1835 town follows "
            "from the row; the name is preserved exactly as the index prints it."),
    },
    "the_enrollment_names_a_man_the_rolls_do_not_carry": {
        "disposition": "unresolved",
        "ticket": ROSTER,
        "statement": (
            "The index enrolls this man at Chicago in 1832 under a surname the 1833-1835 "
            "poll and tax lists either do not carry at all, or carry under forenames that "
            "do not agree with his. " + LADDER + "The crosswalk's target is those rolls and "
            "not the residents layer, so this file may not say the town has no such person "
            "— it says only that the rolls do not reach him. That is a name read and "
            "withheld, and the borderline roster is where such a name is kept with its "
            "source and its re-admission class."),
    },
    "the_1884_history_is_later_evidence_about_the_town": {
        "disposition": "later_only",
        "statement": (
            "The finding is read out of Andreas's History of Chicago, volume I, published "
            "in 1884 — forty-nine years after the scene date. " + LADDER + "So the claim "
            "may corroborate a town fact and may date one, and may not by itself assert an "
            "1835 fact, mint a person or place a structure. The reading stands as committed "
            "chronology and the town's own contemporary sources outrank it wherever both "
            "speak."),
    },
    "the_democrats_date_falls_after_the_scene_date": {
        "disposition": "later_only",
        "statement": (
            "The Chicago Democrat is the town's own contemporary paper, but THIS claim's "
            "content is dated after 1 July 1835, so under the ladder it may corroborate and "
            "date and may not assert an 1835 fact as the scene stands. It is written here "
            "rather than caught by rule because the ledger's year test reads the first year "
            "printed in describes_date: an election held on 10 July 1835 reads as the year "
            "1835 and is not later than it."),
    },
    "the_towns_charter_is_not_a_person_or_a_place": {
        "disposition": "refused",
        "statement": (
            "The claim states the town's CONSTITUTION — the act of the legislature "
            "enlarging the corporation's powers, and the section of the new charter fixing "
            "how and when its Board is elected. It is dated before the scene date and it is "
            "true of the town on 1 July 1835, and it is still neither a person, a household "
            "nor a structure: there is no card it could be spent into and no roof it could "
            "raise. The reading stands as the town's committed constitutional record, and "
            "the person ledger's answer is that there is no person here — a finished answer "
            "rather than a deferral."),
    },
    "the_finding_describes_the_roll_and_not_the_town": {
        "disposition": "refused",
        "statement": (
            "The claim is a finding ABOUT THE LIST — what the published roll does and does "
            "not print, which election it is and is not the poll book of, and which "
            "discrepancy the search failed to resolve. It is a statement about the "
            "evidence, deliberately committed so that a limit of the source cannot be "
            "forgotten and re-crossed. It names no person to mint and no place to build, so "
            "the person ledger refuses it as a person unit while the finding itself stands "
            "exactly where the reading put it."),
    },
}

CENSUS_RULES = {
    "the_1830_line_bounds_a_held_residents_presence": {
        "disposition": "unresolved",
        "ticket": ARRIVAL,
        "statement": (
            "The 1830 schedule enters this head of family in the enumerator's division "
            "headed 'Peoria & Putnam Counties & Territory attached', and the resident "
            "crosswalk finds a person in the town whose surname AND given name both agree. "
            "The crosswalk carries that agreement as EARLIER EVIDENCE and says in terms "
            "that it grades nothing on its own. " + LADDER + "What the line gives is a "
            "bound — this person was in the district in the summer of 1830, five years "
            "before the scene — and the arrival pass draws arrivals from bounds. The unit "
            "is handed on unasserted and the identity is neither re-opened nor hardened."),
    },
    "the_1830_surname_variant_is_a_candidate_and_not_a_merge": {
        "disposition": "unresolved",
        "ticket": ARRIVAL,
        "statement": (
            "The given names agree and the surnames differ only by a silent terminal e or a "
            "doubled consonant, and the crosswalk is explicit that this is a CANDIDATE and "
            "never a merge. This file does not make the identification either. What it does "
            "is carry the row forward with the identity still open, because IF the "
            "identification is made the 1830 line becomes a bound on that person's presence "
            "and the arrival pass is where a bound is weighed. Nothing is upgraded, and the "
            "candidate remains a candidate."),
    },
    "the_1830_line_names_the_garrison_and_not_a_person": {
        "disposition": "refused",
        "statement": (
            "The line enters the United States garrison of Fort Dearborn as a single "
            "household under its commanding officer. It is not a person and may never reach "
            "one: the schedule names no soldier, and the officer is named as commanding "
            "rather than enumerated as a head of family. Ruled here so that the one row on "
            "these leaves which can never be crosswalked is not left looking unexamined."),
    },
    "the_1830_surname_stands_in_no_town_household": {
        "disposition": "refused",
        "statement": (
            "No person in the town's households carries this surname at all. The crosswalk "
            "states the three readings that remain open — the man had gone by 1835, or he "
            "lived in the part of the division that was never Chicago (the Fox River and "
            "Du Page settlements are inside it, and the schedule never writes the word "
            "Chicago), or he is somebody the reconstruction has not found — and it settles "
            "none of them. " + LADDER + "On all three readings the 1830 line asserts no "
            "1835 fact, mints nobody and edits no card, and the answer to what this unit "
            "spends into the town is NOTHING. That is a complete answer here rather than a "
            "deferral, and the row stays in the reading for any later evidence to reach."),
    },
    "the_1830_surname_only_match_was_refused_in_the_crosswalk": {
        "disposition": "refused",
        "statement": (
            "The crosswalk has already refused this row by name: the 1830 reading shares "
            "only a surname with the town person or persons it was set beside, and a "
            "surname match is a clue and not an identity. The refusal was written down so "
            "that the next sweep would not make the same match again, and the ledger now "
            "carries it instead of reading the row as work nobody has looked at."),
    },
    "the_1830_town_finding_is_earlier_evidence": {
        "disposition": "refused",
        "statement": (
            "The claim is a town finding read off the 1830 schedule — who was enumerated as "
            "one household, and which households stood at the forks in that year. " + LADDER
            + "The finding is committed chronology of the place five years before the "
            "scene, and the town it describes is the town of 1830; it asserts nothing about "
            "1 July 1835 and mints nobody into it."),
    },
    "the_1830_schedule_describes_its_own_making": {
        "disposition": "refused",
        "statement": (
            "The claim is a finding about the MANUSCRIPT rather than about the town: a "
            "heavy rule the enumerator drew under one line and the wider spacing after it, "
            "and the fact that in 1830 Chicago had no county of its own and the schedule "
            "never writes the word Chicago. These are readings of how the document was "
            "made and what it covers, kept so the source's shape cannot be forgotten. They "
            "name no person and raise no structure, so the person ledger refuses them while "
            "the findings stand where the reading put them."),
    },
}

DIRECTORY_RULES = {
    "the_1844_sketch_is_later_evidence_about_an_earlier_year": {
        "disposition": "later_only",
        "statement": (
            "The claim is read out of the historical sketch prefixed to Norris's Chicago "
            "directory of 1844 — a retrospective, written nine years after the scene date, "
            "about a year at or before it. " + LADDER + "So the statement may corroborate "
            "and may date, and may not assert an 1835 fact on its own: its population "
            "figures are a later man's estimate, its chronology a later man's summary. It "
            "is written here rather than caught by the ledger's year rule because that rule "
            "reads the year the claim DESCRIBES, and this claim describes 1835 or earlier "
            "while standing in a book of 1844."),
    },
    "the_1839_register_is_later_evidence_about_an_earlier_year": {
        "disposition": "later_only",
        "statement": (
            "The claim is read out of Fergus's Chicago directory and city register of 1839, "
            "four years after the scene date, and states a fact about an earlier year — the "
            "organisation of the county, or the town's population in a past year as the "
            "register's own retrospective column gives it. " + LADDER + "So it may "
            "corroborate and may date, and may not assert an 1835 fact by itself. The "
            "ledger's year rule does not catch it because the year DESCRIBED is 1835 or "
            "earlier even though the book is later."),
    },
}

# The seventeen civic and four 1830 town findings are prose claims, not rows of a roll, so
# the rule each falls under is stated here by id rather than derived from a crosswalk
# column. The NOTE is still built from the row itself — its kind, its describes_date and
# its own normalized sentence — so a reader can hold the note against the claim and check
# it. Every id below is a unit the ledger leaves unresolved and owned by this ticket.
CIVIC_CLAIM_RULES = {
    "town_findings_andreas_v1.json": dict.fromkeys(
        ("c001", "c003", "c005", "c006", "c007", "c009", "c011", "c012"),
        "the_1884_history_is_later_evidence_about_the_town"),
    "town_election_1835_democrat.json": {
        "d001": "the_towns_charter_is_not_a_person_or_a_place",
        "d002": "the_democrats_date_falls_after_the_scene_date",
        "d003": "the_democrats_date_falls_after_the_scene_date",
        "d004": "the_democrats_date_falls_after_the_scene_date",
        "d005": "the_towns_charter_is_not_a_person_or_a_place",
    },
    "town_findings_voter_lists.json": dict.fromkeys(
        ("v001", "v003", "v004", "v005"),
        "the_finding_describes_the_roll_and_not_the_town"),
}

CENSUS_CLAIM_RULES = {
    "schedule_town_findings.json": {
        "census1830_town_001": "the_1830_town_finding_is_earlier_evidence",
        "census1830_town_002": "the_1830_town_finding_is_earlier_evidence",
        "census1830_town_003": "the_1830_schedule_describes_its_own_making",
        "census1830_town_004": "the_1830_schedule_describes_its_own_making",
    },
}

DIRECTORY_CLAIM_RULES = {
    "norris_1844_town_findings.json": dict.fromkeys(
        ("n1844_tf_008", "n1844_tf_011", "n1844_tf_012", "n1844_tf_013", "n1844_tf_014",
         "n1844_tf_015", "n1844_tf_018", "n1844_tf_022", "n1844_tf_026", "n1844_tf_028",
         "n1844_tf_029", "n1844_tf_033", "n1844_tf_034", "n1844_tf_036", "n1844_tf_054",
         "n1844_tf_057"),
        "the_1844_sketch_is_later_evidence_about_an_earlier_year"),
    "fergus_1839_city_register.json": {
        "f1839_r0054": "the_1839_register_is_later_evidence_about_an_earlier_year"},
    "fergus_1839_population.json": {
        "f1839_pop01": "the_1839_register_is_later_evidence_about_an_earlier_year"},
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def unit_id(domain: str, path: Path, container: str, row_id: str) -> str:
    return f"{domain}:{path.relative_to(ROOT).as_posix()}#{container}/{row_id}"


def sentence(value) -> str:
    """One readable line out of a claim's `normalized`, which may be prose or an object."""
    if isinstance(value, str):
        text = value
    elif isinstance(value, dict):
        text = str(value.get("value") or value.get("as_printed") or json.dumps(
            value, ensure_ascii=False, sort_keys=True))
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= 240 else text[:237].rstrip() + "..."


def claim_note(lead: str, row: dict) -> str:
    dated = str(row.get("describes_date") or "no date")
    kind = str(row.get("kind") or "finding")
    return (f"{lead} Claim {row['id']}, a {kind} finding dated {dated}: "
            f"\"{sentence(row.get('normalized'))}\"")


def claim_rulings(domain: str, directory: str, mapping: dict) -> list[dict]:
    out = []
    for filename, by_id in sorted(mapping.items()):
        path = ROOT / "data" / "research" / directory / "claims" / filename
        doc = read_json(path)
        leads = {
            "town_findings_andreas_v1.json": "Andreas 1884, volume I.",
            "town_election_1835_democrat.json": "The Chicago Democrat, read for T-0542.",
            "town_findings_voter_lists.json": "A finding about the published lists themselves.",
            "schedule_town_findings.json": "The 1830 schedule of the Peoria & Putnam division.",
            "norris_1844_town_findings.json": "Norris's directory of 1844, historical sketch.",
            "fergus_1839_city_register.json": "Fergus's directory and city register of 1839.",
            "fergus_1839_population.json": "Fergus's directory of 1839, population column.",
        }
        for row in doc.get("claims") or []:
            rule = by_id.get(row.get("id"))
            if rule:
                out.append({"unit": unit_id(domain, path, "claims", row["id"]),
                            "rule": rule,
                            "note": claim_note(leads[filename], row)})
    return out


def voter_rule(row: dict, entry: dict, lists: dict) -> tuple[str, str]:
    outcome = entry["outcome"]
    meta = lists.get(entry["list"], {})
    title = meta.get("title") or entry["list"]
    when = meta.get("date") or "an undated list"
    seen = f"{row.get('as_read')!r} read as {row.get('normalized')!r}"
    where = f"{title}, entry {row['locator'].get('entry')} ({when})"
    if outcome == "matched":
        held = (f"The crosswalk joins it to {entry['matched_resident']} in household "
                f"{entry['household_id']}: {entry.get('discriminator') or entry.get('rule')}")
        if entry["list"] == "tax_1833":
            return "the_1833_tax_roll_bounds_property_and_not_presence", (
                f"{where} enters {seen}. {held}. The roll is the town's property list of "
                f"1833, so what it bounds is this man's taxable standing in Chicago and "
                f"not his body in it.")
        return "the_poll_book_bounds_a_held_residents_presence", (
            f"{where} enters {seen}, a man who voted at a town election on that day. "
            f"{held}. The date bounds that person's presence and is handed on unasserted.")
    if outcome == "candidate":
        rivals = ", ".join(str(r) for r in (entry.get("rivals") or [])) or "no single bearer"
        return "a_roll_agreeing_on_surname_alone_is_never_a_merge", (
            f"{where} enters {seen}. The crosswalk calls it a candidate and not a match "
            f"(candidate {entry.get('candidate')}; rivals: {rivals}): {entry.get('rule')}")
    return "the_roll_names_a_person_the_town_does_not_hold", (
        f"{where} enters {seen}, and the town's households hold no one the crosswalk can "
        f"join it to: {entry.get('rule')}")


def blackhawk_rule(row: dict, entry: dict) -> tuple[str, str]:
    outcome = entry["outcome"]
    seen = f"{row.get('as_read')!r} read as {row.get('normalized')!r}"
    company = entry.get("company") or "no company"
    rank = entry.get("rank") or "no rank"
    where = (f"Black Hawk War enrollments at Chicago, 1832, row "
             f"{row['locator'].get('entry')} of 134 — company {company}, rank {rank}")
    if outcome == "corroborated":
        agrees = ", ".join(f"{v['record_id']} {v['as_read']!r}" for v in entry.get("voter_entries") or [])
        return "the_1832_enrollment_may_bound_a_rolled_mans_arrival", (
            f"{where} — enrolls {seen}. One reading on the 1833-1835 rolls agrees initial "
            f"for initial ({agrees}): {entry.get('rule')}")
    if outcome == "ambiguous":
        agrees = ", ".join(f"{v['record_id']} {v['as_read']!r}" for v in entry.get("voter_entries") or [])
        return "an_ambiguous_enrollment_agreement_is_never_a_merge", (
            f"{where} — enrolls {seen}. The agreement is contested ({agrees}): "
            f"{entry.get('rule')}")
    if outcome == "no_surname":
        return "the_enrollment_index_prints_no_surname", (
            f"{where} — enrolls {seen}, printed without a surname comma, so the "
            f"surname-indexed rolls cannot be searched for it: {entry.get('rule')}")
    return "the_enrollment_names_a_man_the_rolls_do_not_carry", (
        f"{where} — enrolls {seen}, and the 1833-1835 rolls do not reach him: "
        f"{entry.get('rule')}")


def census_rule(row: dict, outcome: str, entry: dict) -> tuple[str, str]:
    seen = f"{row.get('as_read')!r} read as {row.get('normalized')!r}"
    where = (f"The 1830 schedule, leaf {row['locator'].get('image')} entry "
             f"{row['locator'].get('entry')}, in the division headed 'Peoria & Putnam "
             f"Counties & Territory attached'")
    if outcome == "earlier_evidence":
        return "the_1830_line_bounds_a_held_residents_presence", (
            f"{where}, enters {seen}. {entry.get('rule')} The household is "
            f"{entry.get('household')}.")
    if outcome == "surname_variant_candidate":
        return "the_1830_surname_variant_is_a_candidate_and_not_a_merge", (
            f"{where}, enters {seen}. {entry.get('rule')} The household weighed was "
            f"{entry.get('household')}.")
    if outcome == "not_a_person":
        return "the_1830_line_names_the_garrison_and_not_a_person", (
            f"{where}, enters {seen}. {entry.get('rule')}")
    if outcome == "refused_surname_only":
        return "the_1830_surname_only_match_was_refused_in_the_crosswalk", (
            f"{where}, enters {seen}. {entry.get('rule')}")
    return "the_1830_surname_stands_in_no_town_household", (
        f"{where}, enters {seen}. {entry.get('note')}")


def civic_rulings() -> list[dict]:
    rulings = []
    voters = read_json(VOTER_RECORDS)
    lists = {item["id"]: item for item in voters.get("lists") or []}
    by_record = {e["record_id"]: e for e in read_json(VOTER_CROSSWALK)["entries"]}
    for row in voters["records"]:
        rule, note = voter_rule(row, by_record[row["id"]], lists)
        rulings.append({"unit": unit_id("civic", VOTER_RECORDS, "records", row["id"]),
                        "rule": rule, "note": note})
    enrollments = read_json(BLACKHAWK_RECORDS)
    by_enrollment = {e["record_id"]: e for e in read_json(BLACKHAWK_CROSSWALK)["entries"]}
    for row in enrollments["records"]:
        rule, note = blackhawk_rule(row, by_enrollment[row["id"]])
        rulings.append({"unit": unit_id("civic", BLACKHAWK_RECORDS, "records", row["id"]),
                        "rule": rule, "note": note})
    rulings.extend(claim_rulings("civic", "civic", CIVIC_CLAIM_RULES))
    return rulings


def census_rulings() -> list[dict]:
    crosswalk = read_json(CENSUS_CROSSWALK)
    outcome_of = {}
    for bucket in ("matched", "surname_variant_candidates", "not_a_person",
                   "no_surname_in_town", "refusals"):
        for entry in crosswalk.get(bucket) or []:
            outcome_of[entry["record_id"]] = (entry["outcome"], entry)
    rulings = []
    for row in read_json(CENSUS_RECORDS)["records"]:
        outcome, entry = outcome_of[row["id"]]
        rule, note = census_rule(row, outcome, entry)
        rulings.append({"unit": unit_id("census_1830", CENSUS_RECORDS, "records", row["id"]),
                        "rule": rule, "note": note})
    rulings.extend(claim_rulings("census_1830", "census_1830", CENSUS_CLAIM_RULES))
    return rulings


def directory_rulings() -> list[dict]:
    return claim_rulings("directories", "directories", DIRECTORY_CLAIM_RULES)


REGISTERS = {
    "civic": (CIVIC_RULES, civic_rulings,
              "the 1833-1835 poll and tax lists, the 1832 Black Hawk War enrollments at "
              "Chicago read against them, and the seventeen town findings of Andreas, the "
              "Chicago Democrat and the lists themselves"),
    "census_1830": (CENSUS_RULES, census_rulings,
                    "the 200 heads of family of the 1830 Peoria & Putnam division read "
                    "against the town's households, and the four findings about the "
                    "schedule itself"),
    "directories": (DIRECTORY_RULES, directory_rulings,
                    "the retrospective town findings of Norris's 1844 sketch and Fergus's "
                    "1839 register that describe a year at or before the scene date"),
}


def build_document(domain: str) -> dict:
    rules, builder, what = REGISTERS[domain]
    rulings = builder()
    tally = Counter(r["rule"] for r in rulings)
    return {
        "schema": "research-spend-rulings-v1",
        "_doc": (
            f"DERIVED, {TICKET}, by {GENERATOR} from the records, claims and crosswalks "
            f"beside it — run --check to re-derive it. The written ruling on {what}: every "
            "unit of this domain the research-spend ledger leaves unresolved. "
            "tools/research_spend_ledger.py reads this file beside the hand-authored "
            "data/research/spend_rulings.json, at the point where it would otherwise leave "
            "a unit open, so a ruling here can only close a unit nothing else has closed "
            "and can never overturn an assertion, a later_only or a refusal the readings "
            "themselves carry. NOTHING HERE EDITS A RESIDENT, MINTS A PERSON, MOVES A "
            "CONFIDENCE OR REOPENS AN IDENTITY A CROSSWALK RULED. A hand-off is not a "
            "spend: it names the open ticket whose field owns the finding, and that ticket "
            "closing turns this file red, which is the point."),
        "ticket": TICKET,
        "generated_by": GENERATOR,
        "counts": {rule: tally[rule] for rule in sorted(tally)},
        "rules": rules,
        "rulings": rulings,
    }


def out_path(domain: str) -> Path:
    return ROOT / "data" / "research" / domain / "spend_rulings.json"


def write(domain: str, doc: dict) -> None:
    out_path(domain).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> int:
    """Hold each rule over a row built to fall under it, and prove every rule fires."""
    failures = []

    def held(label, got, want):
        rule, note = got
        if rule != want:
            failures.append(f"{label}: fell under {rule!r}, wanted {want!r}")
        elif len(note.strip()) < 20:
            failures.append(f"{label}: note is too short to say why this row fell under it")
        else:
            print(f"  rules: {label} -> {want}")

    row = {"id": "x", "as_read": "Doe, J.", "normalized": "J. Doe", "locator": {"entry": 1}}
    lists = {"poll_1834": {"title": "Poll list of 1834", "date": "1834-08-11"},
             "tax_1833": {"title": "Tax list of 1833", "date": "1833"}}

    def voter(outcome, list_id="poll_1834", **kw):
        entry = {"outcome": outcome, "list": list_id, "matched_resident": "doe_john",
                 "household_id": "hh_doe_john", "discriminator": "initials agree",
                 "rule": "one bearer considered", "candidate": None, "rivals": []}
        entry.update(kw)
        return voter_rule(row, entry, lists)

    held("a poll entry matched to a resident", voter("matched"),
         "the_poll_book_bounds_a_held_residents_presence")
    held("a tax entry matched to a resident", voter("matched", "tax_1833"),
         "the_1833_tax_roll_bounds_property_and_not_presence")
    held("a candidate on the rolls", voter("candidate"),
         "a_roll_agreeing_on_surname_alone_is_never_a_merge")
    held("a roll name the town does not hold", voter("unmatched"),
         "the_roll_names_a_person_the_town_does_not_hold")
    # A TAX entry that is NOT matched follows its outcome, not the roll: the property-roll
    # limit only bites where there is a held person for it to bite on.
    held("an unmatched tax entry", voter("unmatched", "tax_1833"),
         "the_roll_names_a_person_the_town_does_not_hold")

    def enrollment(outcome, **kw):
        entry = {"outcome": outcome, "company": "G KERCHEVAL", "rank": "PVT",
                 "voter_entries": [{"record_id": "poll_1835_008", "as_read": "Bond, H."}],
                 "rule": "stated"}
        entry.update(kw)
        return blackhawk_rule(row, entry)

    held("a corroborated 1832 enrollment", enrollment("corroborated"),
         "the_1832_enrollment_may_bound_a_rolled_mans_arrival")
    held("an ambiguous 1832 enrollment", enrollment("ambiguous"),
         "an_ambiguous_enrollment_agreement_is_never_a_merge")
    held("an enrollment printed without a surname", enrollment("no_surname", company="INDIAN",
                                                               rank=None, voter_entries=[]),
         "the_enrollment_index_prints_no_surname")
    held("an enrollment the rolls do not carry", enrollment("unmatched", voter_entries=[]),
         "the_enrollment_names_a_man_the_rolls_do_not_carry")

    crow = {"id": "x", "as_read": "John Doe", "normalized": "JOHN DOE",
            "locator": {"image": "n576", "entry": 1}}
    for outcome, want in (
            ("earlier_evidence", "the_1830_line_bounds_a_held_residents_presence"),
            ("surname_variant_candidate", "the_1830_surname_variant_is_a_candidate_and_not_a_merge"),
            ("not_a_person", "the_1830_line_names_the_garrison_and_not_a_person"),
            ("refused_surname_only", "the_1830_surname_only_match_was_refused_in_the_crosswalk"),
            ("no_surname_in_town", "the_1830_surname_stands_in_no_town_household")):
        held(f"an 1830 line, {outcome}",
             census_rule(crow, outcome, {"rule": "stated by the crosswalk",
                                         "note": "stated by the crosswalk",
                                         "household": "hh_doe_john"}), want)

    for domain, (rules, _, _) in REGISTERS.items():
        for name, rule in sorted(rules.items()):
            if len(str(rule.get("statement") or "").strip()) < 40:
                failures.append(f"{domain} rule {name}: states no rule")
            if rule["disposition"] == "unresolved" and not rule.get("ticket"):
                failures.append(f"{domain} rule {name}: hands the unit on and names no ticket")

    total = 0
    for domain in REGISTERS:
        doc = build_document(domain)
        total += len(doc["rulings"])
        if len(doc["rulings"]) != len({r["unit"] for r in doc["rulings"]}):
            failures.append(f"{domain}: two rulings on one unit")
        unfired = sorted(set(doc["rules"]) - set(doc["counts"]))
        if unfired:
            failures.append(f"{domain}: rules that never fire over the committed corpus: "
                            + ", ".join(unfired))
        for ruling in doc["rulings"]:
            if ruling["rule"] not in doc["rules"]:
                failures.append(f"{domain}: ruling on {ruling['unit']} names an unstated rule")

    for line in failures:
        print(f"FAIL {line}")
    print(f"NAME-ON-A-ROLL RULING SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), "
          f"{sum(len(r) for r, _, _ in REGISTERS.values())} rule(s), {total} unit(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-derive and prove nothing drifted")
    parser.add_argument("--self-test", action="store_true", help="hold the rules over the rows")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        for domain in REGISTERS:
            doc = build_document(domain)
            path = out_path(domain)
            if not path.exists():
                print(f"FAIL {path.relative_to(ROOT)} is missing — run {GENERATOR}")
                return 1
            if read_json(path) != doc:
                print(f"FAIL {path.relative_to(ROOT)} is stale — run {GENERATOR}")
                return 1
            if not args.quiet:
                print(f"OK {domain} rulings re-derive: {len(doc['rulings'])} units, "
                      + ", ".join(f"{k} {v}" for k, v in doc["counts"].items()))
        return 0
    for domain in REGISTERS:
        doc = build_document(domain)
        write(domain, doc)
        print(f"wrote {out_path(domain).relative_to(ROOT)}: {len(doc['rulings'])} rulings")
        for rule, n in doc["counts"].items():
            print(f"  {n:5d}  {rule}  ({doc['rules'][rule]['disposition']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
