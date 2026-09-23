#!/usr/bin/env python3
"""The written ruling on the 1,094 remaining unasserted units (T-1298).

    python3 tools/spend_remainder_rulings.py             write the five ruling registers
    python3 tools/spend_remainder_rulings.py --check     they re-derive; nothing drifted
    python3 tools/spend_remainder_rulings.py --self-test the rules below, held over the
                                                         corpus they derive

WHY THIS EXISTS. T-1234 gave the research-spend ledger a place to write a ruling down:
`data/research/spend_rulings.json`, consulted only where a reading's own dispositions run
out, a named rule with a stated reason and a note on every single unit it closes. That
file is HAND-AUTHORED and holds 87 rulings; T-1296 wrote the first DERIVED register, for
1,572 land-sale rows, because typing 1,572 notes by hand would make a worse register --
the notes drift and nobody can prove a note matched the row it claims to rule.

T-1298 is the remainder of T-1236, and it is five corpora at once:

    residents        382  the reserved people of the pilot and passes 02-15 whose pass
                          finding names no exact structured resident field
    newspapers       378  the person, notice, event, shipping and price units of the
                          thirteen held issues that no card names
    church           272  the register entries outside the later-only and outside-Chicago
                          rulings already carried by the readings themselves
    books             61  the non-person readings -- ground, harbour, weather, price,
                          shipping, institution and household
    genealogytrails    1  one landscape reading

Each gets its own derived register beside its corpus, on the terms
`research_spend_ledger.ruling_registers` sets: the same statement floor, the same note
floor, the same coverage faults. Every note is built out of the unit's OWN committed
fields -- its file's preamble, its pass finding's summary, its issue date, its register
role, its `normalized` line -- so a reader can put the note beside the row and see that
it says what the row says.

WHAT THIS DOES NOT DO. Nothing here edits a resident, mints a person, moves a confidence,
invents a citation or re-adjudicates an identity. A hand-off is not a spend: it names the
OPEN ticket whose field genuinely owns the finding, and that ticket closing turns this
file red, which is the point. In particular this file does NOT decide the letter-list
question: T-0660 -> T-0691 is blocked on the owner and its outcome is not invented here.
A letter-list name is handed to T-1159, whose field is the roster of names the research
READ AND WITHHELD, with `letter-list-only` as a declared re-admission class -- recording
that a name was read and withheld is not ruling on whether its bearer lived here.

THE CORPUS IS DERIVED FROM THE CORPUS, not from the committed ledger: this tool asks
`research_spend_ledger.natural_disposition` -- the derivation that reads no ruling
register at all -- which units end unresolved and owned by T-1298, and rules exactly
those. So writing the registers cannot change what the registers are asked to cover, and
`--check` re-derives the same answer from the same readings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_spend_ledger as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TICKET = "T-1298"
SCENE_DATE = "1835-07-01"
HAND_AUTHORED = ROOT / "data" / "research" / "spend_rulings.json"
DOMAINS = ("residents", "newspapers", "church", "books", "genealogytrails")

# The register roles that carry KIN -- the entry's own `cells.role`. A child, a parent, a
# groom, a bride or a decedent named beside a spouse is a family the source names, which
# is T-1170's field verbatim. A sponsor or a witness is NOT kin: standing at the font or
# signing the page names a person on a dated Chicago day and nothing about a household.
KIN_ROLES = {"child", "father", "mother", "groom", "bride", "spouse", "parent",
             "decedent", "subject"}
ATTENDANCE_ROLES = {"sponsor", "godfather", "godmother", "witness"}

# The column headings a Chicago paper prints over its family news.
FAMILY_COLUMN = re.compile(r"^\W{0,4}(MARRIED|Married|DIED|Died)\b")

RULES = {
    # ---- residents ---------------------------------------------------------------
    "the_manifest_is_a_reservation_and_not_a_reading": {
        "disposition": "refused",
        "statement": (
            "The unit is a row of a research COHORT MANIFEST, and the manifest says so "
            "itself in its own preamble: it is a sampling frame that reserves a person "
            "for a pass and an identity lock that fixes which person was reserved. It "
            "carries the person_id, the starting grade and the letter-list returns the "
            "residents layer ALREADY holds, and it states no new fact about anybody. The "
            "pilot committed no findings ledger, so no reading is attached to this row to "
            "spend. What is refused here is the claim that the ROW carries an 1835 fact; "
            "nothing is refused about the person, whose card is untouched and whose "
            "evidence is exactly what it was."),
    },
    "the_pass_named_a_candidate_and_did_not_assert_it": {
        "disposition": "refused",
        "statement": (
            "The completed pass reviewed this reserved person and returned a CANDIDATE "
            "IDENTITY it explicitly did not assert -- the finding's own candidate rows "
            "carry `asserted: false` and name the conflict that stopped them. The "
            "research already refused the join; the ledger now carries that refusal "
            "instead of leaving the row open. Closing it by eye would be manufacturing "
            "the identity the pass declined to make, and this ruling does not touch the "
            "candidate, the card, or the grade either of them carries."),
    },
    "corroboration_confirms_and_moves_nothing": {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated`: an independent source agrees "
            "with what the card already says, and the finding's own words are that the "
            "person was confirmed, NOT MOVED. Under the evidence ladder ratified "
            "2026-09-03 corroboration corroborates; it does not promote and it names no "
            "new structured field, so there is nothing here to write. The agreement is a "
            "closed decision and the sources stand in the finding where the pass put "
            "them."),
    },
    "the_enrichment_names_an_attribute_no_field_carries": {
        "disposition": "unresolved",
        "ticket": "T-1160",
        "statement": (
            "The completed pass returned `corroborated_enrichment`: a real, sourced fact "
            "about a person this town holds -- a trade, an address, an origin, a kinship, "
            "a date -- that extends the card and that no exact source-bearing structured "
            "field on that card carries today. It is not refused, because it is true "
            "research; it is not written here, because writing one attribute at a time, "
            "out of one pass and without the other sources beside it, is how a layer "
            "acquires facts it cannot defend. T-1160 is the pass that profiles every "
            "attested and inferred person attribute by attribute and tier by tier, and "
            "this is one of the attributes it must read."),
    },
    # ---- the ladder --------------------------------------------------------------
    "the_issue_is_printed_after_the_scene_date": {
        "disposition": "later_only",
        "statement": (
            "The issue this unit was read from was PRINTED after 1 July 1835, so under "
            "T-0513's ladder it may corroborate, enrich and date, and it may not assert "
            "an 1835 fact. The unit itself carries no `describes_date`, which is why the "
            "ledger's year test never reached it: the date that bounds it is the issue's "
            "own masthead date, and that is what is applied here."),
    },
    "the_roll_is_beyond_the_reading_window": {
        "disposition": "later_only",
        "statement": (
            "The entry's own `beyond_ticket_window` field is true: it is a row of a "
            "congregation roll that begins after the scene date -- the Second "
            "Presbyterian Church of Chicago was formed in 1842, seven years on -- and the "
            "row prints no date within the window at all. Under the ladder it may "
            "corroborate and date a person the town already holds, and it may never "
            "assert that person into 1835."),
    },
    "the_reading_is_earlier_than_the_scene_and_does_not_reach_it": {
        "disposition": "refused",
        "statement": (
            "The reading's own `describes_date` is earlier than 1835 and its content does "
            "not reach the scene date: an event, a notice, an appearance, a civic act or "
            "a household described in 1812, 1818, 1821, 1827, 1830 or 1833 is a fact "
            "about that year. Under the ladder ratified 2026-09-03 a source LATER than "
            "the scene date corroborates and never promotes, and an EARLIER source does "
            "not promote either -- a man, a society or a house at Chicago in 1827 is not "
            "thereby at Chicago in 1835. The reading stands as committed chronology; no "
            "card is edited, nothing is minted, and the ground, harbour and structure "
            "layers keep it exactly as they have it."),
    },
    # ---- readings about the town rather than about a record ----------------------
    "a_ground_reading_describes_the_site_not_a_record": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a LANDSCAPE reading: it describes the site -- its timber, its "
            "prairie, its streams, its shore, the naming of a river -- and names no "
            "person, household, business or structure record for the person ledger to "
            "write. That is the answer, not a deferral: a ground reading is committed "
            "chronology for the terrain and shore work, which cites it where it bears, "
            "and the spend ledger's honest disposition for it is that it is good in "
            "AGGREGATE and attaches to no record. This ruling neither cites it for the "
            "ground tickets nor invents a terrain fact from it."),
    },
    "the_market_and_the_port_in_aggregate": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a PRICE or a SHIPPING reading -- a marine journal's arrivals and "
            "clearances, a wholesale list by the cask, a freight or a rate. This is the "
            "question T-1298 was asked to answer: what a reading of the harbour or the "
            "price of flour does for the 1835 scene when no person unit owns it. It sizes "
            "the town's trade -- what came in, in what bottoms, and what it cost -- and "
            "it names no person, household, business or structure record, so the person "
            "ledger has nothing to write from it. It is true, it is spent in aggregate, "
            "and it is closed: the scene reads it as texture and the vessels and stocks "
            "it counts are not thereby minted as records."),
    },
    "a_town_reading_with_no_record_to_write": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is an in-window reading ABOUT THE TOWN rather than about a person: "
            "a society, a public event, a civic act, a weather or an institution note, "
            "dated 1835 or undated, naming no record this layer holds. It is not refused "
            "-- it is true and it is in the window -- and it is not handed on, because "
            "there is no structured record for it to land on. It is spent in aggregate as "
            "scene chronology, which is a finished answer."),
    },
    "the_column_names_nobody": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a notice or an editorial paragraph whose own `entities` array is "
            "EMPTY -- the reading looked for the people in it and recorded that it names "
            "none. A paragraph that names nobody cannot assert a person fact and cannot "
            "be handed to a person pass. Its content is the town's public print in "
            "aggregate -- what the paper carried, and when -- and that is what it is "
            "spent as."),
    },
    # ---- hand-offs ---------------------------------------------------------------
    "the_letter_list_name_belongs_to_the_borderline_roster": {
        "disposition": "unresolved",
        "ticket": "T-1159",
        "statement": (
            "The unit's own `letter_list_only` field is true: the name's whole evidence is "
            "that a letter waited for it at the Chicago post office. Whether a letter-list "
            "name is a resident is the question of T-0660 -> T-0691, which is BLOCKED on "
            "the owner, and NOTHING HERE INVENTS ITS OUTCOME. What is ruled is the only "
            "thing that can be ruled without it: the name was read and it is withheld from "
            "1835, and T-1159's field is exactly that roster -- every name the research "
            "read and withheld, with its source, its reason and its re-admission class, of "
            "which `letter-list-only` is one the ticket names. Handing the name to the "
            "roster records the withholding; it does not decide the residency."),
    },
    "the_notice_names_a_firm": {
        "disposition": "unresolved",
        "ticket": "T-1147",
        "statement": (
            "The unit carries a `business` block: the reading pulled a firm name, and "
            "where it could a trade, a proprietor and a street placement, out of the "
            "advertisement or notice. That is enterprise evidence, and the ledger already "
            "routes every business, building, street and infrastructure unit to the place "
            "and enterprise completion pass. A firm is not minted here, a placement is not "
            "written here, and a contradiction between two notices is not resolved here."),
    },
    "the_family_column_names_kin": {
        "disposition": "unresolved",
        "ticket": "T-1170",
        "statement": (
            "The unit is the paper's own MARRIED or DIED column, printed under that "
            "heading: it names a bride and a groom, or a decedent and the survivor they "
            "are named by, and the magistrate or minister who officiated. A marriage names "
            "a spouse and creates nobody; T-1170 gives the attested and inferred heads the "
            "families the sources name, from exactly these ruled kin ties. No household "
            "member is minted here and no kin tie is written here."),
    },
    "the_register_entry_names_kin": {
        "disposition": "unresolved",
        "ticket": "T-1170",
        "statement": (
            "The entry's own `cells.role` puts this person in the KIN of a dated "
            "sacrament at Chicago -- the child, the father, the mother, the groom, the "
            "bride, the spouse or the decedent of a baptism, a marriage or a death. "
            "T-1170's field is the spouses, children, kin and dependants the baptism and "
            "marriage registers name. The tie is handed on whole; nobody is minted, no "
            "household is edited, and the entry's `confidence` is untouched."),
    },
    "a_dated_appearance_bounds_a_presence": {
        "disposition": "unresolved",
        "ticket": "T-1169",
        "statement": (
            "The unit puts a named person at Chicago on a dated day and states nothing "
            "else about them -- standing sponsor or witness at a register entry, or named "
            "in a dated notice of the town's print. A dated appearance BOUNDS a presence "
            "and is never itself a presence, and the earliest dated appearance is the "
            "bound T-1169 works from. This ruling hands the date on and writes nothing: it "
            "does not decide that a named party is a resident, that a name is a person "
            "rather than a firm, or that it is the individual a card of that name already "
            "holds."),
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clip(value, limit: int = 220) -> str:
    """One line of a committed field, whitespace-flattened, cut on a word."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + " …"


def issue_date(doc: dict) -> str | None:
    """The masthead date of a held issue, off its own `issue_id`."""
    match = re.search(r"(\d{4})_(\d{2})_(\d{2})$", str(doc.get("issue_id") or ""))
    return "-".join(match.groups()) if match else None


def entity_names(row: dict) -> list[str]:
    names = []
    for entity in row.get("entities") or []:
        if isinstance(entity, dict):
            names.append(str(entity.get("normalized") or entity.get("as_printed") or ""))
        else:
            names.append(str(entity))
    return [name for name in names if name]


def rule_residents(unit: dict, finding: dict | None, preamble: str) -> tuple[str, str]:
    if not finding:
        return ("the_manifest_is_a_reservation_and_not_a_reading",
                f"{unit['source_record_id']} is a row of the pilot manifest, whose own preamble "
                f"reads: “{clip(preamble, 160)}” No findings ledger was ever committed for the "
                f"pilot, so this reservation has no reading attached to it to spend.")
    outcome = str(finding.get("outcome") or "")
    summary = clip(finding.get("summary") or finding.get("default_summary"))
    sources = ", ".join(str(s) for s in (finding.get("sources") or [])) or "none named"
    if outcome == "candidate_identity":
        candidates = finding.get("candidates") or []
        assessed = "; ".join(
            f"{clip(c.get('name'), 60)} ({clip(c.get('assessment'), 24)}, asserted="
            f"{bool(c.get('asserted'))})" for c in candidates if isinstance(c, dict))
        return ("the_pass_named_a_candidate_and_did_not_assert_it",
                f"The pass on {unit['source_record_id']} returned: “{summary}” "
                f"Candidate(s) as recorded: {assessed or 'none carried on the finding'}.")
    if outcome == "corroborated":
        return ("corroboration_confirms_and_moves_nothing",
                f"The pass on {unit['source_record_id']} returned: “{summary}” "
                f"Corroborating sources as recorded: {clip(sources, 200)}.")
    return ("the_enrichment_names_an_attribute_no_field_carries",
            f"The pass on {unit['source_record_id']} returned: “{summary}” "
            f"Sources as recorded: {clip(sources, 180)}.")


def rule_newspapers(unit: dict, printed: str | None) -> tuple[str, str]:
    row = unit["record"]
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    kind = row.get("kind")
    line = clip(row.get("normalized"), 180)
    if printed and printed > SCENE_DATE:
        return ("the_issue_is_printed_after_the_scene_date",
                f"{where}: the issue is dated {printed}, after the scene date. The {kind} "
                f"reads: “{line}”")
    if row.get("letter_list_only"):
        return ("the_letter_list_name_belongs_to_the_borderline_roster",
                f"{where}: a post-office letter list printed {printed}. Names as read: "
                f"{clip(', '.join(entity_names(row)) or line, 200)}")
    business = row.get("business") or {}
    if business:
        return ("the_notice_names_a_firm",
                f"{where}: the notice of {printed} carries the firm "
                f"“{clip(business.get('name'), 80) or 'unnamed in the block'}” "
                f"(trade as read: {clip(business.get('trade'), 60) or 'none'}; street as read: "
                f"{clip(business.get('street'), 60) or 'none'}).")
    if kind == "person":
        if FAMILY_COLUMN.match(str(row.get("normalized") or "")):
            return ("the_family_column_names_kin",
                    f"{where}: the family column of {printed} reads: “{line}”")
        return ("a_dated_appearance_bounds_a_presence",
                f"{where}: a person notice of {printed} naming "
                f"{clip(', '.join(entity_names(row)) or 'no entity row', 120)}. It reads: “{line}”")
    if kind in {"price", "shipping"}:
        return ("the_market_and_the_port_in_aggregate",
                f"{where}: a {kind} reading of {printed}. It reads: “{line}”")
    names = entity_names(row)
    if names:
        return ("a_dated_appearance_bounds_a_presence",
                f"{where}: a {kind} of {printed} naming {clip(', '.join(names), 150)}. "
                f"It reads: “{line}”")
    return ("the_column_names_nobody",
            f"{where}: a {kind} of {printed} whose entities array is empty. It reads: “{line}”")


def rule_church(unit: dict) -> tuple[str, str]:
    row = unit["record"]
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    dated = row.get("describes_date")
    if row.get("beyond_ticket_window") is True:
        return ("the_roll_is_beyond_the_reading_window",
                f"{where}: {clip(row.get('normalized'), 80)}, read from the roll of the Second "
                f"Presbyterian Church. The entry as printed: "
                f"“{clip((row.get('cells') or {}).get('entry_as_printed') or row.get('as_read'), 140)}”")
    role = str((row.get("cells") or {}).get("role") or "")
    if role in KIN_ROLES:
        return ("the_register_entry_names_kin",
                f"{where}: {clip(row.get('normalized'), 80)} is the {role} of a register entry "
                f"dated {dated} at Chicago. {clip(row.get('notes'), 160)}")
    if role in ATTENDANCE_ROLES:
        return ("a_dated_appearance_bounds_a_presence",
                f"{where}: {clip(row.get('normalized'), 80)} stands as {role} at a register entry "
                f"dated {dated} at Chicago. {clip(row.get('notes'), 160)}")
    if row.get("kind") == "person":
        return ("a_dated_appearance_bounds_a_presence",
                f"{where}: a person reading of the register prose, dated {dated}. "
                f"It reads: “{clip(row.get('normalized'), 180)}”")
    return ("a_town_reading_with_no_record_to_write",
            f"{where}: a {row.get('kind')} reading of the register, dated {dated}. "
            f"It reads: “{clip(row.get('normalized'), 180)}”")


def rule_books(unit: dict) -> tuple[str, str]:
    row = unit["record"]
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    kind = row.get("kind")
    dated = row.get("describes_date")
    line = clip(row.get("normalized"), 200)
    if kind == "landscape":
        return ("a_ground_reading_describes_the_site_not_a_record",
                f"{where}: a landscape reading dated {dated}. It reads: “{line}”")
    if kind in {"price", "shipping"}:
        return ("the_market_and_the_port_in_aggregate",
                f"{where}: a {kind} reading dated {dated}. It reads: “{line}”")
    year = L.year_in(row)
    if year is not None and year < 1835:
        return ("the_reading_is_earlier_than_the_scene_and_does_not_reach_it",
                f"{where}: a {kind} reading whose own describes_date is “{clip(dated, 60)}”, "
                f"earlier than the scene date. It reads: “{line}”")
    return ("a_town_reading_with_no_record_to_write",
            f"{where}: a {kind} reading dated {clip(dated, 60) or 'undated'}, in the window and "
            f"naming no record this layer holds. It reads: “{line}”")


def mine(root: Path = ROOT) -> list[dict]:
    """Every unit the derivation leaves unresolved and owned by T-1298.

    `natural_disposition` reads no ruling register, so this corpus is fixed by the
    readings and the residents layer alone -- writing the registers cannot change what
    they are asked to cover. The hand-authored register's own units are excluded: they
    were ruled by T-1234 and a second ruling on one unit is a fault, correctly.
    """
    registry = read_json(root / "data" / "research" / "domains.json")
    units, faults = L.extract_units(root, registry)
    if faults:
        raise SystemExit("the reading registry is faulted: " + "; ".join(faults[:5]))
    targets = L.target_index(root, {unit["source_record_id"] for unit in units})
    already = {row["unit"] for row in read_json(HAND_AUTHORED).get("rulings") or []}
    out = []
    for unit in units:
        if unit["unit_id"] in already:
            continue
        natural = L.natural_disposition(root, unit, targets)
        if natural.get("disposition") == "unresolved" and natural.get("ticket") == TICKET:
            out.append(unit)
    return out


def classify(root: Path, unit: dict, cache: dict) -> tuple[str, str]:
    domain = unit["domain"]
    if domain == "residents":
        preamble = cache.setdefault(
            unit["source_file"], read_json(root / unit["source_file"])).get("_doc") or ""
        return rule_residents(unit, L.resident_finding(root, unit), preamble)
    if domain == "newspapers":
        doc = cache.setdefault(unit["source_file"], read_json(root / unit["source_file"]))
        return rule_newspapers(unit, issue_date(doc))
    if domain == "church":
        return rule_church(unit)
    return rule_books(unit)


def build_documents(root: Path = ROOT) -> dict[str, dict]:
    cache: dict = {}
    per_domain: dict[str, list[dict]] = {domain: [] for domain in DOMAINS}
    for unit in mine(root):
        if unit["domain"] not in per_domain:
            raise SystemExit(f"{unit['unit_id']}: T-1298 owns a domain this tool does not rule")
        rule, note = classify(root, unit, cache)
        per_domain[unit["domain"]].append({"unit": unit["unit_id"], "rule": rule, "note": note})
    documents = {}
    for domain, rulings in per_domain.items():
        rulings.sort(key=lambda row: row["unit"])
        tally = Counter(row["rule"] for row in rulings)
        documents[domain] = {
            "schema": "research-spend-rulings-v1",
            "_doc": (
                f"DERIVED, T-1298, by tools/spend_remainder_rulings.py from the {domain} "
                "corpus beside it and the residents layer it names -- run --check to "
                "re-derive it. The written ruling on the remainder of T-1236: every unit "
                "the ledger's own derivation leaves unresolved and owns to T-1298. "
                "tools/research_spend_ledger.py reads this file beside the hand-authored "
                "spend_rulings.json, at the point where it would otherwise leave a unit "
                "open, so a ruling here can only close a unit nothing else has closed and "
                "can never overturn an assertion, a later_only or a refusal the readings "
                "themselves carry. NOTHING HERE EDITS A RESIDENT, MINTS A PERSON, MOVES A "
                "CONFIDENCE OR INVENTS A CITATION, and nothing here decides the blocked "
                "letter-list question of T-0660 -> T-0691. A hand-off is not a spend: it "
                "names the open ticket whose field owns the finding, and that ticket "
                "closing turns this file red, which is the point."),
            "ticket": TICKET,
            "generated_by": "tools/spend_remainder_rulings.py",
            "counts": {rule: tally[rule] for rule in sorted(tally)},
            "rules": {name: RULES[name] for name in sorted(tally)},
            "rulings": rulings,
        }
    return documents


def out_path(domain: str, root: Path = ROOT) -> Path:
    return root / "data" / "research" / domain / "spend_rulings.json"


def write(documents: dict[str, dict]) -> None:
    for domain, doc in documents.items():
        path = out_path(domain)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> int:
    failures = []
    for name, rule in sorted(RULES.items()):
        if len(str(rule.get("statement") or "").strip()) < 40:
            failures.append(f"rule {name}: states no rule")
        if rule["disposition"] not in L.RULING_DISPOSITIONS:
            failures.append(f"rule {name}: {rule['disposition']!r} is not a disposition a ruling may reach")
        if rule["disposition"] == "unresolved" and not rule.get("ticket"):
            failures.append(f"rule {name}: hands the unit on and names no ticket")

    # A hand-off may only name a ticket that is still live work, which is the invariant
    # that makes "owned" mean something. The ledger tests this too; testing it here says
    # WHICH rule broke rather than which 90 units did.
    states = L.ticket_states(ROOT)
    for name, rule in sorted(RULES.items()):
        if rule["disposition"] != "unresolved":
            continue
        if states.get(rule["ticket"]) not in L.OPEN_TICKET_STATES:
            failures.append(f"rule {name}: hands on to {rule['ticket']}, which is "
                            f"{states.get(rule['ticket'])!r} and not live work")

    # The rules held over the corpus they derive.
    def held(label, unit, want, **kw):
        got = classify(ROOT, unit, {}) if not kw else kw["fn"](unit)
        if got[0] != want:
            failures.append(f"{label}: ruled {got[0]!r}, wanted {want!r}")

    paper = {"source_file": "x/chicago_democrat_1835_01_21.json",
             "record": {"id": "c001", "kind": "notice", "normalized": "A notice.", "entities": []}}
    held("an issue after the scene date", paper,
         "the_issue_is_printed_after_the_scene_date",
         fn=lambda u: rule_newspapers(u, "1835-08-05"))
    held("a letter list", {**paper, "record": {**paper["record"], "letter_list_only": True}},
         "the_letter_list_name_belongs_to_the_borderline_roster",
         fn=lambda u: rule_newspapers(u, "1835-06-10"))
    held("a letter list printed later still reads by the ladder",
         {**paper, "record": {**paper["record"], "letter_list_only": True}},
         "the_issue_is_printed_after_the_scene_date",
         fn=lambda u: rule_newspapers(u, "1835-08-05"))
    held("a notice carrying a firm",
         {**paper, "record": {**paper["record"], "business": {"name": "Goss & Cobb"}}},
         "the_notice_names_a_firm", fn=lambda u: rule_newspapers(u, "1835-06-10"))
    held("the married column",
         {**paper, "record": {**paper["record"], "kind": "person",
                              "normalized": "MARRIED, In this town, on the 12th inst."}},
         "the_family_column_names_kin", fn=lambda u: rule_newspapers(u, "1834-01-07"))
    held("a person notice that is not the family column",
         {**paper, "record": {**paper["record"], "kind": "person",
                              "normalized": "Be it ordained by the Board of Trustees"}},
         "a_dated_appearance_bounds_a_presence", fn=lambda u: rule_newspapers(u, "1834-01-07"))
    held("the marine journal", {**paper, "record": {**paper["record"], "kind": "shipping"}},
         "the_market_and_the_port_in_aggregate", fn=lambda u: rule_newspapers(u, "1835-06-20"))
    held("a notice naming nobody", paper, "the_column_names_nobody",
         fn=lambda u: rule_newspapers(u, "1835-06-10"))
    held("a notice naming somebody",
         {**paper, "record": {**paper["record"], "entities": [{"normalized": "George W. Snow"}]}},
         "a_dated_appearance_bounds_a_presence", fn=lambda u: rule_newspapers(u, "1834-01-07"))

    church = {"source_file": "x/st_marys_baptisms_1833_1835.json",
              "record": {"id": "e1", "normalized": "George Beaubien", "describes_date": "1833-05-22",
                         "cells": {"role": "child"}, "notes": "Child of entry 1."}}
    held("a register child", church, "the_register_entry_names_kin", fn=rule_church)
    held("a register sponsor",
         {**church, "record": {**church["record"], "cells": {"role": "godmother"}}},
         "a_dated_appearance_bounds_a_presence", fn=rule_church)
    held("the roll beyond the window",
         {**church, "record": {**church["record"], "beyond_ticket_window": True,
                               "cells": {"role": "member"}}},
         "the_roll_is_beyond_the_reading_window", fn=rule_church)
    held("register prose about the town",
         {**church, "record": {"id": "p1", "kind": "civic", "normalized": "A civic note.",
                               "describes_date": "1834"}},
         "a_town_reading_with_no_record_to_write", fn=rule_church)

    book = {"source_file": "x/hubbard_autobiography_1911.json",
            "record": {"id": "b1", "kind": "landscape", "normalized": "The prairie.",
                       "describes_date": "1818"}}
    held("a ground reading, whatever its year", book,
         "a_ground_reading_describes_the_site_not_a_record", fn=rule_books)
    held("a price reading", {**book, "record": {**book["record"], "kind": "price"}},
         "the_market_and_the_port_in_aggregate", fn=rule_books)
    held("an earlier event", {**book, "record": {**book["record"], "kind": "event"}},
         "the_reading_is_earlier_than_the_scene_and_does_not_reach_it", fn=rule_books)
    held("an in-window civic reading",
         {**book, "record": {**book["record"], "kind": "civic", "describes_date": "1835-03"}},
         "a_town_reading_with_no_record_to_write", fn=rule_books)

    manifest = {"source_record_id": "carpenter_philo"}
    held("the pilot reservation", manifest, "the_manifest_is_a_reservation_and_not_a_reading",
         fn=lambda u: rule_residents(u, None, "a sampling manifest, not new evidence"))
    held("a declined candidate", manifest, "the_pass_named_a_candidate_and_did_not_assert_it",
         fn=lambda u: rule_residents(u, {"outcome": "candidate_identity", "summary": "s" * 50,
                                         "candidates": [{"name": "X", "assessment": "strong",
                                                         "asserted": False}]}, ""))
    held("a corroboration", manifest, "corroboration_confirms_and_moves_nothing",
         fn=lambda u: rule_residents(u, {"outcome": "corroborated", "summary": "s" * 50}, ""))
    held("an enrichment", manifest, "the_enrichment_names_an_attribute_no_field_carries",
         fn=lambda u: rule_residents(u, {"outcome": "corroborated_enrichment",
                                         "summary": "s" * 50}, ""))

    documents = build_documents()
    total = 0
    seen: set[str] = set()
    for domain, doc in documents.items():
        for row in doc["rulings"]:
            total += 1
            if row["unit"] in seen:
                failures.append(f"two rulings on one unit: {row['unit']}")
            seen.add(row["unit"])
            if len(row["note"].strip()) < 20:
                failures.append(f"{row['unit']}: carries no note")
            if not row["unit"].startswith(domain + ":"):
                failures.append(f"{row['unit']}: ruled in the {domain} register")
    unfired = sorted(set(RULES) - {rule for doc in documents.values() for rule in doc["counts"]})
    if unfired:
        failures.append("rules that never fire over the committed corpora: " + ", ".join(unfired))

    for line in failures:
        print(f"FAIL {line}")
    print(f"REMAINDER RULING SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), {len(RULES)} rule(s), {total} unit(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-derive and prove nothing drifted")
    parser.add_argument("--self-test", action="store_true", help="hold the rules over the rows")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    documents = build_documents()
    if args.check:
        for domain, doc in documents.items():
            path = out_path(domain)
            if not path.exists():
                print(f"FAIL {path.relative_to(ROOT)} is missing — run tools/spend_remainder_rulings.py")
                return 1
            if read_json(path) != doc:
                print(f"FAIL {path.relative_to(ROOT)} is stale — run tools/spend_remainder_rulings.py")
                return 1
        if not args.quiet:
            total = sum(len(doc["rulings"]) for doc in documents.values())
            print(f"OK remainder rulings re-derive: {total} units across "
                  + ", ".join(f"{d} {len(doc['rulings'])}" for d, doc in documents.items()))
        return 0
    write(documents)
    for domain, doc in documents.items():
        print(f"wrote {out_path(domain).relative_to(ROOT)}: {len(doc['rulings'])} rulings")
        for rule, n in doc["counts"].items():
            print(f"  {n:5d}  {rule}  ({RULES[rule]['disposition']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
