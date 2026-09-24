#!/usr/bin/env python3
"""What the research domains have READ, against what the town has SPENT.

WHY THIS EXISTS. On 2026-09-03 the owner reported, of the 1840 census reading
tickets: "i see lots of research being done and some apparent findings from
parsing but there are not outputs or updates to the household and resident data
it seems, should i be concerned?"

He was right, and nothing in the repo could have told him so. Every reading
ticket DOES leave an output — T-0584 wrote 2,354 lines of page records, a
coverage entry and a changelog line — so no gate was red and no run was idle.
The hole was one layer down: `data/research/census_1840/` held 562 named heads
read off the sheets and `census_1840/crosswalk.json` held `passes: []`,
`merges: []`, `refusals: []`. Nothing had crossed into the town. Four of 828
household records carried an 1840 link.

`coverage.json` already answers "which images have been looked at, and what has
NOT been read from them" — deliberately, so a hole fails rather than passes
quietly. This is the same instrument one step later: which names have been READ,
and how many of them anybody has RULED ON. A domain may read far ahead of its
spending — the ratified ladder REQUIRES it, since 1839/1840 alone is never an
1835 resident and the bridge is a separate adjudicated step — but the gap may
not silently WIDEN. That is what this gate holds.

THE MEASURE, and what each half deliberately does not count.

  read    a unit captured off a source and carrying a name or a quote: an entry
          of a `records` array (domains that hold records) or of a `claims`
          array (domains that hold claims). Continuation-sheet lines that carry
          cells and no name are not names and do not count.

          A FILE MAY DECLARE ITSELF NOT A READING, with a top-level
          `not_a_reading` sentence saying what it is instead, and then its units
          are not charged to the domain (T-0602). Newberry's
          `precision_sample.json` re-adjudicates 160 cards this domain has
          already read, to measure how good the reading is; census_1840's
          `second_readings/` re-reads two sheets independently so that a
          disagreement survives. Both were charged as fresh reading, so
          MEASURING THE READING READ THE METER UP and sampling harder made the
          domain look further behind. Every declaration is printed by `report`,
          with the units it withheld, because a file that could exempt itself in
          silence would be a hole straight through this gate.

  spent   a crosswalk entry ANCHORED to something real — a read record
          (`record_id`, `entry_id`, `claim_id`) or a person in the town
          (`person_id`, `resident`, `matched_resident`). Deduped by that anchor,
          because civic adjudicates its 479 voters in `voter_crosswalk.json`
          AND rules on name pairs in `crosswalk.json`, and summing the two array
          lengths reported civic as 571 spent against 492 read — a domain more
          than finished. An instrument that reports -79 unspent is worse than no
          instrument.

          A REFUSAL COUNTS AS SPENT. census_1840/crosswalk.json says why: "A
          refusal is declared as explicitly as a merge — the absence of one
          reads like a pair nobody has looked at yet." Ruling that a name is
          NOT a town person is the adjudication; it is not a failure to do one.

          A RULING MAY ANCHOR THROUGH ITS EVIDENCE. `evidence` and `support`
          rows that are plain strings naming a unit THIS DOMAIN HAS READ are
          anchors like any other id (T-0602): newberry's crosswalk refuses five
          headings and cites fourteen card ids between them, and counting that
          as zero said the most carefully reasoned paragraph in the domain had
          adjudicated nothing. A string that resolves to no read unit anchors
          nothing — the resolution is against the domain's own ids, so no ruling
          can talk its way into a spend.

  id pairs a merge/refusal ruling on two spellings (`a` / `b`) with no anchor.
          Reported, never counted as spend: it is a ruling about the sources'
          own vocabulary, not about whether the town gained anything. WHAT COULD
          NOT BE COUNTED IS NOW SAID OUT LOUD, per file and with the reason —
          civic writes 90 refusals whose evidence names its sources and its
          locators in prose ("poll_1835 line 293") rather than record ids, and
          the honest report of that is a printed line, not a silent zero. The
          fix for one is to write the id; guessing which record a prose locator
          meant is the kind of invention this project forbids.

  unspent read - spent. NOT a defect count. census_1830, church and books read
          nothing yet and are honestly 0/0; a domain reading ahead of a bridge
          ticket is the method working.

THE GATE is a ratchet, not a target. `unspent` may not exceed the figure in
research_spend_baseline.json. Read more and you must rule on more, or say in the
PR why the baseline moves. Raising a baseline is a decision somebody makes on
purpose; drifting past it is what happened for three weeks.

THE RATCHET HAS TWO DIRECTIONS, and only one of them costs anything. Raising a
ceiling says the project chose to read further ahead of its adjudication, so it
takes one domain and a written reason. Lowering is what SPENDING a domain earns,
can only make this gate stricter, and is therefore free. Without the second
direction the first is a slow leak: a domain spent to nothing would keep the
ceiling its worst day earned and could drift back up to it in silence.

THE THIRD HOP, and the only ratchet here whose ceiling is zero by default (T-0598).
A ruling is only spendable if something can CARRY it to a card, and
`persons[].sources` is a list of SOURCE IDS: a ruling that names a person and never
says what it rests on can be spent by nobody but a human rereading the whole
crosswalk. 103 of 109 rulings were in that state the evening this was written —
civic's voter_crosswalk matched 99 voters to residents and the string
`chicago_voter_lists_1833_1835_irad` appeared nowhere in the file adjudicating
against it. Every generated crosswalk now states its source, at the top of the file
where the whole file rests on one and per entry where a ruling rests on something
specific, and `no source stated` is held at 0. Reading further ahead of your
adjudication is a legitimate choice; ruling on a person and not saying why is not,
so no domain gets an allowance unless somebody writes one deliberately. THE FIX FOR
AN UNSOURCED RULING IS TO STATE THE SOURCE OR TO WITHDRAW THE RULING — never to
invent a plausible-looking citation, which would take this gate green on a lie.

    tools/measure_research_spend.py              the table
    tools/measure_research_spend.py --gate       the ratchet, and what slack it sees
    tools/measure_research_spend.py --raise newberry_index --why "T-0578 read vol 2"
    tools/measure_research_spend.py --raise <domain> --hop write|source --why "..."
    tools/measure_research_spend.py --tighten    reclaim slack after spending
    tools/measure_research_spend.py --tighten <domain> --hop write --why "..."
    tools/measure_research_spend.py --rebaseline first write only
    tools/measure_research_spend.py --self-test
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
REGISTRY = RESEARCH / "domains.json"
BASELINE = Path(__file__).resolve().parent / "research_spend_baseline.json"

# WHICH ARRAY HOLDS THE RULINGS IS NOT A LIST WE MAINTAIN — it was, for one day,
# and the list was wrong within hours. The first version whitelisted
# passes/merges/refusals/matches/contested/ambiguous/probable/entries, and then
# the two tickets this very gate provoked filed their work under names it had
# never heard of: T-0505 wrote 498 rulings as `heads` in resident_crosswalk.json
# and T-0590 wrote 319 as `lead_rulings` in lead_crosswalk.json. The measure read
# both as zero and would have reported the town had spent nothing while it had in
# fact spent 817 — an instrument that demands work and then cannot see it.
#
# So EVERY array in a crosswalk file is scanned, and the ENTRY decides, not its
# heading: it is a ruling if it anchors to something real or states an `outcome`.
# Structural arrays (a `ladder`, an `inputs` block, the `pages` of a page-level
# agreement test) carry neither and are ignored without being counted anywhere.
OUTCOME_KEY = "outcome"

# What a ruling may anchor to. Order matters only for which name the dedup key
# takes; any one of them makes the entry a spend. Plural forms are here because
# one ruling may reach several cards or several people at once.
# `household_id` and `resident_id` are here since T-0602: the SECOND hop has read
# them as naming a person in the town since the day it was written (PERSON_KEYS),
# and the spend half never did — so land_sales' resident_crosswalk matched 17
# purchasers to households by name and this measure called every one of them
# nothing. A key that identifies a town person on one hop identifies one on both.
ANCHOR_KEYS = ("record_id", "entry_id", "claim_id", "lead_id",
               "person_id", "resident", "matched_resident", "household_id",
               "resident_id", "record_ids", "person_ids")

# A unit is READ if it carries one of these. `quote` is here for the claims
# domains, whose unit is a sentence the source prints rather than a name.
NAME_KEYS = ("normalized", "as_read", "quote")

# HOW A FILE SAYS IT IS NOT A READING (T-0602). One top-level sentence, in the
# file itself rather than in a registry a long way off, because the reason a
# precision sample is not fresh reading is a fact about that file and belongs
# where somebody opening it will see it. The VALUE is the reason and it may not
# be empty: `not_a_reading: true` would let a file exempt itself without saying
# why, which is the shape of every silent hole this gate exists to close.
NOT_A_READING_KEY = "not_a_reading"

# WHERE A FILE'S NAMED UNITS LIVE, when they do not live in `records` or `claims`
# (T-0678). old_settlers/people.json holds 327 roll entries under `people`, and this
# instrument read every one of them as nothing — a domain that had read three rolls
# measured as though it had read one. The declaration is in the file, beside
# `not_a_reading` and for the same reason: which array is the reading is a fact about
# that file. It cannot inflate a domain, because the units still have to carry a name,
# and it cannot be used to hide one — withholding is `not_a_reading`'s job and that one
# has to give a reason.
UNITS_IN_KEY = "units_in"


def unit_containers(doc: dict) -> tuple:
    declared = doc.get(UNITS_IN_KEY)
    if isinstance(declared, str) and declared.strip():
        return ("records", "claims", declared.strip())
    return ("records", "claims")

# Where a ruling may name a unit it adjudicated, as a plain string. These are the
# two blocks the crosswalks already use for "what this rests on"; a string in one
# of them that IS an id this domain has read is an anchor (T-0602), and a string
# that resolves to nothing is left alone.
EVIDENCE_KEYS = ("evidence", "support")


def is_crosswalk(path: Path) -> bool:
    return "crosswalk" in path.name


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# THE SECOND HOP. Everything above measures research READ against research RULED
# ON. That is two thirds of the owner's original question and not the third he
# actually asked — "there are not outputs or updates to the household and
# resident data". A ruling lives in data/research/; a VISITOR sees data/residents/.
#
# Measured the evening of 2026-09-03, on the ten 1840 heads T-0505 matched or
# graded candidate: ten name a real resident record, ten records exist, and NOT
# ONE carries a single source its own ruling rests on. Philo Carpenter's card
# cites `andreas_1884_v1` and nothing else while the ruling for him rests on
# Fergus 1843 and Norris 1844 and the crosswalks hold four more. The evidence and
# the slot have never been introduced.
#
# So: of the rulings that reach a person in the town, how many reach that
# person's CARD? A ruling counts as written when the record it names cites at
# least one source the ruling itself rests on. That is deliberately generous —
# it asks whether the card learned ANYTHING from the ruling, not whether it
# learned everything — because a strict test would read 0 forever and tell
# nobody anything new.
RESIDENTS = DATA_DIR = ROOT / "data" / "residents"
PERSON_KEYS = ("household_id", "person_id", "person_ids", "resident", "matched_resident")
WRITTEN_OUTCOMES = ("matched", "candidate")


# T-1172. `data/residents/readmitted/` is the RECONSTRUCTION, not the research: the
# borderline roster's names offered back at the reconstructed tier by
# tools/readmit_borderline_roster.py. The research instruments below measure what the
# sources say and what has been spent of them, and a reconstruction is neither. Reading it
# here would let an invention raise the research meter, join a crosswalk, or stand as a
# rival card in an identity ruling — which is the exact boundary that stage is built on.
READMITTED_DIR = "readmitted"


def town_records(root):
    """Every committed resident record EXCEPT the reconstruction's own."""
    return [p for p in sorted(root.rglob("*.json")) if p.parent.name != READMITTED_DIR]

def resident_records() -> dict:
    """Every resident record by its own id — households and the people files alike."""
    out = {}
    for path in town_records(RESIDENTS):
        doc = read_json(path)
        if isinstance(doc, dict) and doc.get("id"):
            out[doc["id"]] = doc
    return out


def cited_sources(doc) -> set:
    """Every source id a record cites, at any depth. `sources` is the field the
    residents layer has always used; nothing else counts as a citation."""
    found = set()
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "sources" and isinstance(value, list):
                    found.update(v for v in value if isinstance(v, str))
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(doc)
    return found


# Where a source id may be stated. `evidence` is here because the identity
# crosswalks (civic/crosswalk.json and its shape-mates) have always written their
# basis per refusal, as `evidence: [{source_id, locator}]`, and reading only
# `discriminators` reported those files as stating nothing.
SOURCE_BEARING_KEYS = ("discriminators", "same_name_support", "evidence", "support")


def stated_sources(node) -> set:
    """The source ids stated ON one object — `source_id` and `source_ids` alike.

    Both spellings are in use in this repo and both mean the same thing: what this
    was adjudicated FROM. A ruling may rest on several sources at once (a gazetteer
    person read out of four issues of the American), so the plural is not a
    convenience, it is the honest shape for that case.
    """
    out = set()
    if not isinstance(node, dict):
        return out
    if isinstance(node.get("source_id"), str):
        out.add(node["source_id"])
    value = node.get("source_ids")
    if isinstance(value, list):
        out.update(v for v in value if isinstance(v, str))
    return out


def rests_on(ruling: dict) -> set:
    """The source ids a ruling rests on — what its card would have to learn."""
    out = stated_sources(ruling)
    for key in SOURCE_BEARING_KEYS:
        for row in ruling.get(key) or []:
            out |= stated_sources(row)
    return out


def doc_rests_on(doc: dict) -> set:
    """What the FILE says its rulings rest on — the narrow form T-0598 asks for.

    A crosswalk generated out of one source states it once at the top rather than
    on each of 345 entries, and that statement is as real as a per-entry one: it
    names what the whole file adjudicated FROM. The per-entry form is still the
    better one wherever a ruling rests on something specific, and it WINS: a
    ruling that names its own sources is not diluted by the file's.

    IT MAKES A RULING JUDGEABLE. IT DOES NOT MAKE ONE WRITTEN — see `subject_of`.
    """
    return stated_sources(doc)


def all_strings(node) -> list:
    """Every string anywhere under a node, in no particular order."""
    out = []
    if isinstance(node, dict):
        for value in node.values():
            out.extend(all_strings(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(all_strings(item))
    elif isinstance(node, str):
        out.append(node)
    return out


def subject_of(ruling: dict, ids: set) -> set:
    """What this ruling adjudicated, as strings the CARD would have to name (T-0989).

    THE FAULT THIS EXISTS TO CLOSE. `doc_rests_on` lets a generated crosswalk state
    its basis once at the top, and 811 of the 1,359 person-reaching rulings in this
    repo state nothing else — 60% of the second hop. For every one of those the
    written test collapsed to *does this card cite this source id anywhere, for any
    reason at all?*, and a card citing it from a DIFFERENT pass satisfied every
    ruling in the file at once. That is not a hypothetical: hh_garrett_a cites
    `fergus_chicago_directory_1839` because a later resident-research pass wrote a
    generic `directories` block on it, and on the strength of that citation this
    measure called Fergus 1839's ruling for Garrett — entry f1839_e0527, "Garrett,
    Augustus, auctioneer, real estate, bds. Sauganash Hotel", printed page 15 —
    WRITTEN. Nothing of that entry is on the card.

    So a file-level statement makes a ruling judgeable and no more. To count written
    the card must name what the ruling was about:

      * a READ UNIT the ruling names — `f1839_e0527`, `ls0001`, `poll_1833_001` —
        resolved against what this domain has actually read, exactly as T-0602
        resolves an evidence string, so a string naming a file, a source id or
        another domain's card resolves to nothing and buys nothing; and
      * the SHEET a sheet-and-line ruling sits on. The 1840 heads carry no unit id
        — the census names none — and `familysearch_id` is where a reader goes back
        to the line. It is what `spend_census_1840_heads.py` writes onto the card,
        and it is as real an anchor here as it is in `anchor_of`.
    """
    subjects = {s for s in all_strings(ruling) if s in ids}
    sheet = ruling.get("familysearch_id")
    if isinstance(sheet, str) and ruling.get("line") is not None:
        subjects.add(sheet)
    return subjects


def names_subject(record: dict, subjects: set) -> bool:
    """Does this card name one of the units the ruling adjudicated, anywhere in it?

    Deliberately the whole record and not `note` alone: the 1840 heads reach a card
    as `census_evidence[].record_id`, the directories reach one as prose, and both
    are the card having learned the ruling. What is ruled out is the citation on its
    own, which is what a card carries whether or not anybody read the ruling."""
    return any(subject in text for text in all_strings(record) for subject in subjects)


def people_named(ruling: dict) -> list:
    out = []
    for key in PERSON_KEYS:
        value = ruling.get(key)
        if isinstance(value, list):
            out.extend(str(v) for v in value if v)
        elif value:
            out.append(str(value))
    return out


# HOW A RULING SAYS IT IS A MATCH (T-0635). `outcome: "matched"` is one way and the way
# this instrument was built around; the other, used by every crosswalk generated as pools,
# is the NAME OF THE LIST THE RULING IS FILED IN. A row under `matches` or `merges` in a
# file whose own counts call it a match is a match, and reading it as nothing because it
# spells its verdict in the container rather than in a field is the instrument mistaking
# its own vocabulary for the project's. `refusals`, `ambiguous`, `contested`, `probable`
# and `passes` are NOT here and must never be: a rival still standing is not a ruling to
# spend, which is the same line tools/spend_civic_voter_lists.py draws at its rule 1.
#
# `matched` IS here since T-0962, and the singular cost the town a whole domain. The list
# was written from the containers dev happened to hold, so the second hop read `matches`
# and never `matched` — and church/second_presbyterian_crosswalk.json files its 82
# adjudicated roll members under `matched`, every one naming a household this town holds a
# card for. The hop did not report them unwritten; it did not report church AT ALL, and a
# domain missing from the table reads as a domain with nothing to answer for. Which
# grammatical number a generator reached for is not a fact about the research, so the
# instrument may not make it one.
MATCH_CONTAINERS = ("matches", "merges", "matched")

# WHERE A RULING MAY LIVE IN A CROSSWALK (T-0635, consolidation pass 2). The second hop
# used to read only lists that were DIRECT values of the document, and two of this
# project's crosswalks do not put them there: fergus_1839_election_crosswalk_1835.json and
# fergus_1839_register_crosswalk_1835.json group their rulings by the POOL each was matched
# against — `residents.matches`, `voters.matches`, `letter_list.matches` — one level down.
# So 101 rulings that name a person this town holds a card for were invisible, and the hop
# reported the directories domain at 0 unwritten while not one of the 101 had reached a
# card. A clean bill of health that is an artefact of the instrument is the exact failure
# the docstring below calls a smear, so the walk descends. It descends through DICTS only:
# a list inside a list is a matrix or a quote block, never a ruling table, and following it
# would start counting rows of transcription as adjudications. ONE level of grouping is all
# that is followed: a pool is a pool, and a table three dicts deep is a structure this
# instrument has no business reading as a list of rulings.
RULING_DEPTH = 1


def ruling_lists(doc, depth: int = RULING_DEPTH):
    """(container key, rulings) for every ruling list, at the top level or under a pool."""
    if depth < 0 or not isinstance(doc, dict):
        return
    for key, value in doc.items():
        if isinstance(value, list):
            yield key, value
        elif isinstance(value, dict):
            yield from ruling_lists(value, depth - 1)


def count_written(domain_dir: Path, records: dict) -> tuple:
    """(reached, judgeable, wrote, on the file's word) for rulings that name a person.

    JUDGEABLE IS NOT A TECHNICALITY, it is the difference between a measurement and
    a smear. A ruling that never says what it rests on cannot be checked against a
    card, and reporting it as "unwritten" would be the same failure as the
    whitelist bug: a number that looks like a finding and is really an artefact of
    the instrument. Such a ruling is counted UNSOURCED and printed, because it is
    its own defect — a crosswalk that cannot say what it rests on cannot be spent.

    T-0598 is that defect, held rather than merely printed. When this was written
    civic's voter_crosswalk matched 99 voters to residents and stated no source
    anywhere in the file; 103 of 109 rulings across the town were unsourced. The
    fix was to say it once at the top of each generated crosswalk, which is what
    `doc_rests_on` reads, and `--gate` now ratchets the remainder at 0 so it
    cannot regrow. A file-level statement is a FALLBACK, never an override: a
    ruling naming its own sources is judged against those.

    AND A FALLBACK IS NOT THE SAME TEST (T-0989). Where the ruling names its own
    sources, a card citing one of them has demonstrably learned something from that
    ruling. Where it does not, the file's one source id is shared by every ruling in
    the file, so a single citation put there by any other pass would pass all of
    them at once — which is how census_1840 read 27 of 27 written with 15 cards
    carrying no mention of the census. For those the card must ALSO name what the
    ruling was about (`subject_of`). The fourth return value is how many of the
    written came through that softer door, because a measurement with two tests in
    it should say which one it used.

    A fallback ruling that names no subject at all is counted UNWRITTEN, not
    unsourced: the file did say what it rests on, so the hop knows what to look for
    and the answer is no. Making it unsourced instead would push it into the T-0598
    ratchet, where the remedy is to state a source that is already stated."""
    ids = units_read(domain_dir)
    reached = judgeable = wrote = on_file_word = 0
    for path in sorted(domain_dir.rglob("*.json")):
        if not is_crosswalk(path):
            continue
        doc = read_json(path)
        if not isinstance(doc, dict):
            continue
        from_file = doc_rests_on(doc)
        for key, rulings in ruling_lists(doc):
            declared = key in MATCH_CONTAINERS
            for ruling in rulings:
                if not isinstance(ruling, dict):
                    continue
                # A RULING'S OWN VERDICT OUTRANKS THE LIST IT IS FILED IN (T-0962). The
                # container is how a ruling that states no `outcome` spells its verdict,
                # and that is the whole of its authority: where the entry DOES state one,
                # that is the adjudication and the heading is filing. Widening
                # MATCH_CONTAINERS without this would have counted census_1830's sixteen
                # `matched` rows — every one an explicit `earlier_evidence`, which is not
                # a match — as matches, and bought the coverage with a false reading.
                outcome = ruling.get(OUTCOME_KEY)
                if outcome is None:
                    if not declared:
                        continue
                elif outcome not in WRITTEN_OUTCOMES:
                    continue
                named = [p for p in people_named(ruling) if p in records]
                if not named:
                    continue
                reached += 1
                own = rests_on(ruling)
                wants = own or from_file
                if not wants:
                    continue
                judgeable += 1
                if not any(wants & cited_sources(records[p]) for p in named):
                    continue
                if own:
                    wrote += 1
                    continue
                subjects = subject_of(ruling, ids)
                if subjects and any(names_subject(records[p], subjects) for p in named):
                    wrote += 1
                    on_file_word += 1
    return reached, judgeable, wrote, on_file_word


def anchor_of(ruling: dict) -> str | None:
    """What this ruling is about, as a dedup key — or None if it names nothing.

    A 1840 head is identified by its position on the sheet (`familysearch_id` +
    `line`) rather than by any id, because the census names no ids; that pair is
    as real an anchor as a record_id and is treated as one."""
    for key in ANCHOR_KEYS:
        value = ruling.get(key)
        if isinstance(value, list) and value:
            return f"{key}={','.join(str(v) for v in sorted(value))}"
        if value and not isinstance(value, list):
            return f"{key}={value}"
    if ruling.get("familysearch_id") and ruling.get("line") is not None:
        return f"sheet={ruling['familysearch_id']}:{ruling['line']}"
    return None


def named_units(doc: dict) -> int:
    """The named units a file holds, whether or not they are a fresh reading."""
    total = 0
    for key in unit_containers(doc):
        units = doc.get(key)
        if not isinstance(units, list):
            continue
        total += sum(1 for u in units if isinstance(u, dict)
                     and any(u.get(n) for n in NAME_KEYS))
    return total


def count_read(domain_dir: Path) -> tuple:
    """(named units read, the files that declared themselves not a reading).

    A RE-READING IS NOT A READING (T-0602). Everything here walks a domain's own
    output, and some of that output is the domain looking at itself: a precision
    sample re-adjudicates cards already counted, a second reading re-reads a sheet
    already counted. Charging those as fresh names made the instrument punish the
    two habits that keep it honest — sampling your own precision, and reading a
    sheet twice — so a file may say `not_a_reading: "<what it is instead>"` and be
    withheld. The declarations are returned, not swallowed: `report` prints every
    one with the units it withheld, so an exemption is a thing somebody can see and
    argue with rather than a number that quietly went missing."""
    total = 0
    declared = []
    for path in sorted(domain_dir.rglob("*.json")):
        if is_crosswalk(path):
            continue
        doc = read_json(path)
        if not isinstance(doc, dict):
            continue
        units = named_units(doc)
        why = doc.get(NOT_A_READING_KEY)
        if isinstance(why, str) and why.strip():
            if units:
                declared.append((path.name, units, why.strip()))
            continue
        total += units
    return total, declared


def units_read(domain_dir: Path) -> set:
    """Every id this domain has filed a named unit under.

    What an evidence string is resolved AGAINST, and the reason resolution cannot
    inflate a domain: a ruling anchors through its evidence only by naming a unit
    the domain can produce. A string naming a file path, a source id or a card in
    some other domain resolves to nothing and buys nothing."""
    ids = set()
    for path in sorted(domain_dir.rglob("*.json")):
        if is_crosswalk(path):
            continue
        doc = read_json(path)
        if not isinstance(doc, dict):
            continue
        for key in unit_containers(doc):
            for unit in doc.get(key) or []:
                if isinstance(unit, dict) and isinstance(unit.get("id"), str):
                    ids.add(unit["id"])
    return ids


def evidence_anchors(ruling: dict, ids: set) -> list:
    """The read units a ruling names in its evidence, as anchors (T-0602).

    Deliberately the SAME anchor shape a `record_id` produces, so a card ruled on
    once by id and once through an evidence list is one spend and not two."""
    named = []
    for key in EVIDENCE_KEYS:
        for row in ruling.get(key) or []:
            if isinstance(row, str) and row in ids:
                named.append(f"record_id={row}")
    return named


def count_spent(domain_dir: Path) -> tuple[int, int, list]:
    """(anchored rulings, deduped), (unanchored name-pair rulings) and what could
    not be counted at all — [(file, array, count, why)].

    THE THIRD VALUE IS THE POINT OF T-0602. A written adjudication that this
    measure cannot turn into a spend used to leave no trace but a number in the
    `id pairs` column, and a domain could hold five carefully reasoned refusals
    and read as having ruled on nothing. It is now reported per file, with the
    reason, so the next person either writes the id that would fix it or knows why
    it cannot be written."""
    ids = units_read(domain_dir)
    anchors: set[str] = set()
    pairs = 0
    uncounted: dict = {}

    def note(path, key, why):
        row = uncounted.setdefault((path.name, key, why), 0)
        uncounted[(path.name, key, why)] = row + 1

    for path in sorted(domain_dir.rglob("*.json")):
        if not is_crosswalk(path):
            continue
        doc = read_json(path)
        if not isinstance(doc, dict):
            continue
        for key, rulings in doc.items():
            if not isinstance(rulings, list):
                continue
            for index, ruling in enumerate(rulings):
                if not isinstance(ruling, dict):
                    continue
                anchor = anchor_of(ruling)
                if anchor:
                    anchors.add(anchor)
                    continue
                through_evidence = evidence_anchors(ruling, ids)
                if through_evidence:
                    anchors.update(through_evidence)
                    continue
                if ruling.get(OUTCOME_KEY):
                    # A stated outcome with nothing to anchor it is still a ruling
                    # somebody made; it dedups by where it sits.
                    anchors.add(f"{path.name}:{key}:{index}")
                    continue
                if ruling.get("a") and ruling.get("b"):
                    pairs += 1
                    note(path, key, "a spelling pair whose evidence names no unit "
                                    "this domain has read — write the record id")
                elif ruling.get("rule"):
                    note(path, key, "a written ruling naming no unit and no outcome")
                elif ruling.get("what") and (ruling.get("pass") or ruling.get("ticket")):
                    note(path, key, "a pass note: it records that a sweep happened "
                                    "and names no unit, so it is not a spend")
    return len(anchors), pairs, [(f, k, n, w) for (f, k, w), n in sorted(uncounted.items())]


def measure() -> list[dict]:
    registry = read_json(REGISTRY)
    if not isinstance(registry, dict) or not registry.get("domains"):
        raise SystemExit(f"unreadable domain registry: {REGISTRY}")
    records = resident_records()
    rows = []
    for entry in registry["domains"]:
        # T-1143 preserves this instrument's historical 21,419-unit baseline.
        # Newly registered domains enter the closed ledger below, not this older
        # read-versus-ruling comparison.
        if entry.get("legacy_measure") is False:
            continue
        domain_dir = ROOT / entry["path"]
        if not domain_dir.is_dir():
            raise SystemExit(f"registered domain has no directory: {entry['path']}")
        read, declared = count_read(domain_dir)
        spent, pairs, uncounted = count_spent(domain_dir)
        reached, judgeable, wrote, on_file_word = count_written(domain_dir, records)
        rows.append({"domain": entry["id"], "holds": entry["holds"],
                     "read": read, "spent": spent,
                     "not_a_reading": declared, "uncounted": uncounted,
                     "unspent": read - spent, "id_pairs": pairs,
                     "reached": reached, "judgeable": judgeable, "wrote": wrote,
                     "on_file_word": on_file_word,
                     "unwritten": judgeable - wrote,
                     "unjudgeable": reached - judgeable,
                     "unsourced": reached - judgeable})
    return rows


def unregistered() -> list[str]:
    """Domain directories on disk that the registry does not name.

    T-1143 made this a failure. Newspapers, Genealogy Trails and the resident
    research passes are now registered alongside the original nine domains, so
    any directory left over is research that no ledger pattern can disposition.
    """
    registry = read_json(REGISTRY) or {}
    known = {Path(d["path"]).name for d in registry.get("domains", [])}
    return sorted(p.name for p in RESEARCH.iterdir()
                  if p.is_dir() and p.name not in known)


def report() -> str:
    rows = measure()
    out = ["domain            holds      read    spent  unspent  id pairs",
           "-" * 58]
    for r in rows:
        out.append(f"{r['domain']:<17}{r['holds']:<9}{r['read']:>7}"
                   f"{r['spent']:>9}{r['unspent']:>9}{r['id_pairs']:>10}")
    out.append("-" * 58)
    out.append(f"{'TOTAL':<26}{sum(r['read'] for r in rows):>7}"
               f"{sum(r['spent'] for r in rows):>9}"
               f"{sum(r['unspent'] for r in rows):>9}"
               f"{sum(r['id_pairs'] for r in rows):>10}")
    # The second hop, printed only for domains that have rulings reaching a person.
    hop = [r for r in rows if r["reached"]]
    out.append("")
    out.append("ruled onto a town person, and whether their CARD learned it:")
    if hop:
        out.append("domain            reached  judgeable  on a card  unwritten  no source stated"
                   "  on the file's word")
        out.append("-" * 96)
        for r in hop:
            out.append(f"{r['domain']:<17}{r['reached']:>7}{r['judgeable']:>11}"
                       f"{r['wrote']:>11}{r['unwritten']:>11}{r['unjudgeable']:>18}"
                       f"{r['on_file_word']:>20}")
        out.append("-" * 96)
        out.append(f"{'TOTAL':<17}{sum(r['reached'] for r in hop):>7}"
                   f"{sum(r['judgeable'] for r in hop):>11}"
                   f"{sum(r['wrote'] for r in hop):>11}"
                   f"{sum(r['unwritten'] for r in hop):>11}"
                   f"{sum(r['unjudgeable'] for r in hop):>18}"
                   f"{sum(r['on_file_word'] for r in hop):>20}")
        # WHAT THE LAST COLUMN MEANS, said rather than left to be worked out. A
        # ruling counted there stated no source of its own: the file's one source id
        # is all it rests on, and it counts written because the card names the unit
        # it adjudicated as well as citing that source. It is the weaker of the two
        # tests this measure runs and it is printed so nobody has to read the code to
        # find out how much of a green figure came through it (T-0989).
        out.append("  the last column is the weaker test: no source of the ruling's own, so the")
        out.append("  card had to NAME the unit adjudicated and not merely cite the file's source")
    else:
        out.append("  no ruling in any domain yet names a person in the residents layer")
    # WHAT THE MEASURE WITHHELD, AND WHAT IT COULD NOT COUNT (T-0602). Both blocks
    # exist so that neither correction is a number that quietly moved: an exemption
    # a file claimed is printed with the units it withheld, and a written ruling
    # this tool cannot spend is printed with the reason it cannot.
    withheld = [(r["domain"], d) for r in rows for d in r["not_a_reading"]]
    if withheld:
        out.append("")
        out.append("declared not a reading, and so not charged to the domain:")
        for domain, (name, units, why) in withheld:
            out.append(f"  {domain} {name} — {units} unit(s): {why}")
    uncounted = [(r["domain"], u) for r in rows for u in r["uncounted"]]
    if uncounted:
        out.append("")
        out.append("written and NOT counted as spend, and why — never a silent zero:")
        for domain, (name, key, count, why) in uncounted:
            out.append(f"  {domain} {name}:{key} — {count} ruling(s): {why}")
    extra = unregistered()
    if extra:
        out.append("")
        out.append("UNREGISTERED research domain(s): " + ", ".join(extra))
    # The closed ledger is a second, unit-level accounting surface. Keep it in the
    # ordinary report so a reader sees the historical measure and dispositions in
    # one command, while the dated Markdown report remains the review artifact.
    try:
        from research_spend_ledger import read_ledger, LEDGER, DISPOSITIONS
        ledger = read_ledger(LEDGER)
    except (ImportError, OSError):
        ledger = None
    if isinstance(ledger, dict):
        out.append("")
        out.append("closed ledger dispositions:")
        for domain, counts in ledger.get("domains", {}).items():
            summary = ", ".join(f"{name} {counts.get(name, 0)}" for name in DISPOSITIONS)
            out.append(f"  {domain}: {summary}")
        out.append(f"  TOTAL: {ledger.get('unit_count', 0)}; unclassified 0")
    return "\n".join(out)


def gate(quiet: bool = False) -> int:
    baseline = read_json(BASELINE)
    if not isinstance(baseline, dict):
        print(f"   no baseline at {BASELINE.name} — run --rebaseline")
        return 1
    ceilings = baseline.get("unspent_ceiling", {})
    rows = measure()
    faults = []
    for domain in unregistered():
        faults.append(f"{domain}: research directory is not registered in domains.json")
    for r in rows:
        if r["domain"] not in ceilings:
            faults.append(f"{r['domain']}: no ceiling recorded — a new domain must "
                          f"enter the baseline deliberately (unspent {r['unspent']})")
            continue
        ceiling = ceilings[r["domain"]]
        if r["unspent"] > ceiling:
            faults.append(f"{r['domain']}: {r['unspent']} unspent, ceiling {ceiling} "
                          f"(+{r['unspent'] - ceiling}) — {r['read']} read, {r['spent']} ruled on")
    for domain in ceilings:
        if not any(r["domain"] == domain for r in rows):
            faults.append(f"{domain}: in the baseline and not in domains.json")
    # THE SECOND HOP, held the same way. A ruling that reaches a person and never
    # reaches their card is the fault the owner reported in the first place, and
    # it is the one thing nothing measured until now.
    written = baseline.get("unwritten_ceiling", {})
    for r in rows:
        if not r["reached"]:
            continue
        if not r["judgeable"]:
            continue
        ceiling = written.get(r["domain"])
        if ceiling is None:
            faults.append(f"{r['domain']}: {r['unwritten']} ruling(s) reach a town person "
                          f"and no unwritten ceiling is recorded")
        elif r["unwritten"] > ceiling:
            faults.append(f"{r['domain']}: {r['unwritten']} ruled onto a person whose card "
                          f"has not learned it, ceiling {ceiling} "
                          f"(+{r['unwritten'] - ceiling}) — {r['reached']} reached, {r['wrote']} written")
    # THE THIRD HOP, and the one T-0598 turned from a printed number into a gate.
    # A ruling that reaches a town person and states no source rests on nothing a
    # tool can follow, so it can never be spent onto a card by anything but a
    # person rereading the crosswalk. The ratchet holds it at what the backfill
    # left, which is 0: it may be paid down, never grown.
    # ZERO IS THE DEFAULT HERE, and it is the only ratchet in this file that has one.
    # The other two ceilings must be recorded deliberately because reading ahead of
    # adjudication is a legitimate choice somebody makes; there is no legitimate
    # choice to rule on a person and not say what the ruling rests on, so a domain
    # gets no allowance unless somebody writes one on purpose and says why.
    unsourced = baseline.get("unsourced_ceiling", {})
    for r in rows:
        if not r["reached"]:
            continue
        ceiling = unsourced.get(r["domain"], 0)
        if r["unsourced"] > ceiling:
            faults.append(f"{r['domain']}: {r['unsourced']} ruling(s) reach a town person "
                          f"and state no source, ceiling {ceiling} "
                          f"(+{r['unsourced'] - ceiling}) — a crosswalk that cannot say "
                          f"what it rests on cannot be spent. State the source at the top "
                          f"of the file, or per entry where the ruling rests on something "
                          f"specific; do NOT invent one for a ruling whose basis is "
                          f"genuinely unrecorded — withdraw that ruling instead")
    if faults:
        print("   research read faster than the town spent it:")
        for f in faults:
            print(f"     {f}")
        print("   Rule on the names, or raise that one domain's ceiling with")
        print("     tools/measure_research_spend.py --raise <domain> --why \"...\"")
        return 1
    # SLACK IS REPORTED, ALWAYS. A ceiling only ever moved up, and this gate would
    # have stayed silent about it: a domain spent all the way down keeps the ceiling
    # its worst day earned, and may drift back up to it unnoticed. That is a ratchet
    # with one tooth. `--tighten` reclaims it and needs no justification, because
    # lowering a ceiling can only make this gate stricter.
    slack = [(r["domain"], ceilings[r["domain"]] - r["unspent"]) for r in rows
             if r["domain"] in ceilings and ceilings[r["domain"]] > r["unspent"]]
    slack += [(f"{r['domain']} (unwritten)", written[r["domain"]] - r["unwritten"])
              for r in rows if r["domain"] in written and written[r["domain"]] > r["unwritten"]]
    slack += [(f"{r['domain']} (unsourced)", unsourced[r["domain"]] - r["unsourced"])
              for r in rows if r["domain"] in unsourced and unsourced[r["domain"]] > r["unsourced"]]
    if slack and not quiet:
        for domain, by in slack:
            print(f"   reclaimable: {domain} sits {by} under its ceiling")
        print("   tools/measure_research_spend.py --tighten takes it back")
    if not quiet:
        print(report())
    return 0


def write_baseline(doc: dict) -> None:
    BASELINE.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")


def rebaseline() -> int:
    """FIRST WRITE ONLY. It used to rewrite every domain from current state, which
    is how a run raising one ceiling would have silently absorbed the drift of all
    the others — no reason recorded anywhere, which is the exact fault this file
    exists to catch. Raising is now per-domain and costs a sentence (`--raise`);
    lowering is free (`--tighten`)."""
    if BASELINE.exists():
        print(f"   {BASELINE.name} already exists — refusing to rewrite every ceiling at once.")
        print("   Raise ONE domain, with a reason:  --raise <domain> --why \"...\"")
        print("   Reclaim slack after spending:     --tighten")
        return 1
    rows = measure()
    write_baseline({
        "schema": 1,
        "_doc": ("The unspent ceiling per research domain — read minus ruled-on. RAISING A "
                 "NUMBER HERE IS A DECISION and is written by --raise, which requires a "
                 "reason and touches one domain. Lowering is free and is what spending a "
                 "domain does: --tighten reclaims the slack. --rebaseline writes this file "
                 "once and then refuses, so no run can launder every ceiling in one go."),
        "generated_by": "tools/measure_research_spend.py --rebaseline",
        "unspent_ceiling": {r["domain"]: r["unspent"] for r in rows},
        "unwritten_ceiling": {r["domain"]: r["unwritten"] for r in rows if r["judgeable"]},
        "unsourced_ceiling": {r["domain"]: r["unsourced"] for r in rows if r["reached"]},
        "witness": {r["domain"]: {"read": r["read"], "spent": r["spent"]} for r in rows},
        "raised": [],
    })
    print(f"wrote {BASELINE.name}")
    print(report())
    return 0


def raise_ceiling(domain: str, why: str, hop: str = "read") -> int:
    """Raise ONE domain's ceiling on ONE hop, and record who said why.

    hop 'read'   — the read-vs-ruled ceiling (`unspent_ceiling`)
    hop 'write'  — the ruled-vs-on-a-card ceiling (`unwritten_ceiling`)
    hop 'source' — the reaches-a-person-and-says-nothing ceiling (`unsourced_ceiling`)

    Raising the SOURCE hop should be all but impossible to justify, and the message
    below says so: the fix for an unsourced ruling is to state the source or to
    withdraw the ruling, never to make room for it."""
    baseline = read_json(BASELINE)
    if not isinstance(baseline, dict):
        print(f"   no baseline at {BASELINE.name} — run --rebaseline")
        return 1
    rows = {r["domain"]: r for r in measure()}
    if domain not in rows:
        print(f"   {domain} is not a domain in domains.json — nothing to raise")
        return 1
    if not why.strip():
        print("   --why is required: a raise says the project chose to read further "
              "ahead of its adjudication, and somebody has to say why")
        return 1
    if hop not in ("read", "write", "source"):
        print("   --hop must be 'read' (read vs ruled), 'write' (ruled vs on a card) "
              "or 'source' (reaches a person and states nothing)")
        return 1
    row = rows[domain]
    field = {"read": "unspent_ceiling", "write": "unwritten_ceiling",
             "source": "unsourced_ceiling"}[hop]
    figure = {"read": row["unspent"], "write": row["unwritten"],
              "source": row["unsourced"]}[hop]
    ceilings = baseline.setdefault(field, {})
    was = ceilings.get(domain)
    if was is not None and figure <= was:
        print(f"   {domain} is at {figure} against a {hop} ceiling of {was} — "
              "nothing to raise. Use --tighten to reclaim the slack.")
        return 1
    ceilings[domain] = figure
    baseline.setdefault("witness", {})[domain] = {"read": row["read"], "spent": row["spent"]}
    baseline.setdefault("raised", []).append({
        "domain": domain, "hop": hop, "from": was, "to": figure,
        "date": date.today().isoformat(), "why": why.strip()})
    write_baseline(baseline)
    print(f"raised {domain} ({hop}): {was} -> {figure}")
    print(f"  why: {why.strip()}")
    return 0


def tighten(domain: str | None = None, hop: str = "read", why: str = "") -> int:
    """Lower every ceiling that sits above what the domain now reads. Always safe:
    it can only make the gate stricter, so it needs no reason and asks for none.

    NAMING A DOMAIN NARROWS IT TO ONE CEILING, and T-0992 is why. A pass that spends one
    domain reclaims that domain's slack, and a bare `--tighten` reclaims everybody's at the
    same time — pinning six other domains to the exact figure they happened to read that
    morning, so the next run to read ahead of its own adjudication goes red on a ceiling no
    ticket touched. The ratified ladder REQUIRES reading ahead, so that slack is not waste.
    A scoped tightening takes back only what the unit earned, and because it is a deliberate
    move rather than a sweep it records itself in `lowered[]` and asks for the reason.
    """
    baseline = read_json(BASELINE)
    if not isinstance(baseline, dict):
        print(f"   no baseline at {BASELINE.name} — run --rebaseline")
        return 1
    if domain and not why.strip():
        print("   a scoped tightening records itself, so it needs --why")
        return 1
    ceilings = baseline.setdefault("unspent_ceiling", {})
    written = baseline.setdefault("unwritten_ceiling", {})
    unsourced = baseline.setdefault("unsourced_ceiling", {})
    rows = [r for r in measure() if domain is None or r["domain"] == domain]
    if domain and not rows:
        print(f"   {domain} is not a registered domain")
        return 1
    wants = {"read", "write", "source"} if domain is None else {hop}
    moved = []
    for row in rows:
        was = ceilings.get(row["domain"])
        if "read" in wants and was is not None and row["unspent"] < was:
            ceilings[row["domain"]] = row["unspent"]
            baseline.setdefault("witness", {})[row["domain"]] = {
                "read": row["read"], "spent": row["spent"]}
            moved.append((row["domain"], "read", was, row["unspent"]))
        was_w = written.get(row["domain"])
        if "write" in wants and was_w is not None and row["unwritten"] < was_w:
            written[row["domain"]] = row["unwritten"]
            moved.append((row["domain"], "write", was_w, row["unwritten"]))
        was_s = unsourced.get(row["domain"])
        if "source" in wants and was_s is not None and row["unsourced"] < was_s:
            unsourced[row["domain"]] = row["unsourced"]
            moved.append((row["domain"], "source", was_s, row["unsourced"]))
    if not moved:
        print("every ceiling already sits at what its domain reads — nothing to reclaim")
        return 0
    if domain:
        # A sweep is bookkeeping and says so by leaving no entry; a scoped move is a
        # decision about one domain, and `lowered[]` is where this file keeps those.
        for name, which, was, now in moved:
            baseline.setdefault("lowered", []).append(
                {"domain": name, "hop": which, "from": was, "to": now,
                 "date": date.today().isoformat(), "why": why.strip()})
    write_baseline(baseline)
    for name, which, was, now in moved:
        label = name if which == "read" else f"{name} ({which})"
        print(f"tightened {label}: {was} -> {now} (reclaimed {was - now})")
    return 0


def self_test() -> int:
    """Every assertion this gate makes, proved to fire when the fault is present."""
    failures = []

    ran = []

    def fires(label: str, condition: bool) -> None:
        # COUNTED, not tallied by hand: the case count used to be a literal 46 and
        # T-0598 added six cases without moving it, which is a self-test that
        # cannot say how much it tested.
        ran.append(label)
        if not condition:
            failures.append(label)

    # --- the read counter
    fires("a record with a normalized name is read",
          sum(1 for u in [{"normalized": "W. H. Adams"}]
              if any(u.get(n) for n in NAME_KEYS)) == 1)
    fires("a continuation line with cells and no name is NOT read",
          sum(1 for u in [{"line": 4, "cells": {"1": 2}}]
              if any(u.get(n) for n in NAME_KEYS)) == 0)
    fires("an as_read-only record is still read",
          sum(1 for u in [{"as_read": "Wm S. Lans[?]me"}]
              if any(u.get(n) for n in NAME_KEYS)) == 1)
    fires("a claims unit counts by its quote",
          sum(1 for u in [{"quote": "the town then had four stores"}]
              if any(u.get(n) for n in NAME_KEYS)) == 1)

    # --- the spend counter, on a scratch tree
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "voter_crosswalk.json").write_text(json.dumps({"entries": [
            {"record_id": "poll_1833_001", "outcome": "matched"},
            {"record_id": "poll_1833_002", "outcome": "refused"}]}))
        spent, pairs, _ = count_spent(d)
        fires("two anchored rulings are two spends", spent == 2)
        fires("…and neither is an id pair", pairs == 0)

        # the civic double-count this tool was written to avoid
        (d / "crosswalk.json").write_text(json.dumps({"refusals": [
            {"a": "Medard Beaubien", "b": "Col. Jean Baptiste Beaubien"}]}))
        spent, pairs, _ = count_spent(d)
        fires("an unanchored name-pair ruling is NOT a spend", spent == 2)
        fires("…it is reported as an id pair", pairs == 1)

        # one record ruled on twice in two files is one spend
        (d / "second_crosswalk.json").write_text(json.dumps({"matches": [
            {"record_id": "poll_1833_001", "person_id": "adams_william_h"}]}))
        spent, *_ = count_spent(d)
        fires("one record ruled on in two files is one spend", spent == 2)

        # a refusal that names a person is spent
        (d / "third_crosswalk.json").write_text(json.dumps({"refusals": [
            {"person_id": "beaubien_jean_baptiste", "rule": "surname only"}]}))
        spent, *_ = count_spent(d)
        fires("an anchored refusal IS a spend", spent == 3)

        # `pages` is not an adjudication array
        (d / "crosswalk_670.json").write_text(json.dumps({
            "pages": [{"printed_page": 229}, {"printed_page": 231}]}))
        spent, pairs, _ = count_spent(d)
        # `pages` is not in ADJUDICATION_KEYS, so the file adds nothing at all —
        # the one id pair still standing is the Beaubien refusal above.
        fires("a page-level agreement test rules on nobody",
              spent == 3 and pairs == 1)

        # a non-crosswalk file is never a spend, however it is shaped
        (d / "records.json").write_text(json.dumps({"entries": [
            {"record_id": "x"}]}))
        spent, *_ = count_spent(d)
        fires("only a crosswalk file carries rulings", spent == 3)

        # the read counter over the same tree
        (d / "page.json").write_text(json.dumps({"records": [
            {"as_read": "A"}, {"line": 2}, {"normalized": "B"}]}))
        fires("read counts names and skips the blank line", count_read(d)[0] == 2)
        fires("…and never reads a crosswalk as a source",
              count_read(d)[0] == 2)

    # --- T-0602, FAULT ONE: a re-reading counted as a reading. Newberry was
    # charged 160 units for MEASURING ITSELF and census_1840 61 for reading two
    # sheets twice on purpose, so sampling harder read the meter up.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "page.json").write_text(json.dumps({"records": [
            {"normalized": "A"}, {"normalized": "B"}]}))
        sample = {"records": [{"normalized": "A"}, {"normalized": "B"}]}
        (d / "precision_sample.json").write_text(json.dumps(sample))
        fires("a re-reading with no declaration is charged as fresh reading",
              count_read(d)[0] == 4)

        (d / "precision_sample.json").write_text(json.dumps(
            dict(sample, not_a_reading="a measurement of the reading")))
        read, declared = count_read(d)
        fires("a file declaring itself not a reading is withheld", read == 2)
        fires("…and the declaration is REPORTED, with the units and the reason",
              declared == [("precision_sample.json", 2, "a measurement of the reading")])

        (d / "precision_sample.json").write_text(json.dumps(dict(sample, not_a_reading=True)))
        fires("…while `not_a_reading: true` says nothing and exempts nothing",
              count_read(d)[0] == 4)
        (d / "precision_sample.json").write_text(json.dumps(dict(sample, not_a_reading="  ")))
        fires("…nor does a blank reason", count_read(d)[0] == 4)

    # --- T-0678: a reading filed under the domain's own word for it. old_settlers holds
    # 327 roll entries under `people`, and this instrument counted them as nothing until
    # the file said which array was the reading.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        roll = {"records": [{"id": "r1", "normalized": "A"}],
                "people": [{"id": "os1", "normalized": "B"}, {"id": "os2", "as_read": "C"}]}
        (d / "roll.json").write_text(json.dumps(roll))
        fires("an undeclared array is read as nothing", count_read(d)[0] == 1)
        (d / "roll.json").write_text(json.dumps(dict(roll, units_in="people")))
        fires("a declared array is counted beside records and claims",
              count_read(d)[0] == 3)
        fires("…and its ids can anchor a ruling like any other read unit",
              {"r1", "os1", "os2"} <= units_read(d))
        (d / "roll.json").write_text(json.dumps(dict(roll, units_in="  ")))
        fires("a blank units_in declares nothing", count_read(d)[0] == 1)
        (d / "roll.json").write_text(json.dumps(dict(roll, units_in="people",
                                                     not_a_reading="a re-reading")))
        fires("…and a declared array is still withheld when the file says it is not a "
              "reading", count_read(d)[0] == 0)

    # --- T-0602, FAULT TWO: a written refusal counted as nothing. The five
    # newberry refusals cite card ids in `evidence` as plain strings, and the
    # measure read the most carefully reasoned paragraph in the domain as zero.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "records.json").write_text(json.dumps({"records": [
            {"id": "nbi_v01_0452", "normalized": "Beeubion"},
            {"id": "nbi_v01_0453", "normalized": "Beeubion"}]}))
        refusal = {"a": "Beeubion", "b": "Jean Baptiste Beaubien", "rule": "a surname is not a man",
                   "evidence": ["nbi_v01_0452", "nbi_v01_0453"]}
        (d / "crosswalk.json").write_text(json.dumps({"refusals": [refusal]}))
        spent, pairs, uncounted = count_spent(d)
        fires("a refusal anchors through the read units its evidence names", spent == 2)
        fires("…so it is no longer reported as a bare id pair", pairs == 0)
        fires("…and nothing is left uncounted", uncounted == [])

        # the same refusal ruled on again by id is the SAME spend, not a second one
        (d / "second_crosswalk.json").write_text(json.dumps({"refusals": [
            {"record_id": "nbi_v01_0452", "outcome": "refused"}]}))
        fires("a card ruled on by id and through evidence is one spend",
              count_spent(d)[0] == 2)

        # resolution is against the domain's own ids, so it cannot be talked into
        (d / "crosswalk.json").write_text(json.dumps({"refusals": [dict(
            refusal, evidence=["data/residents/households/", "no_such_id"])]}))
        spent, pairs, uncounted = count_spent(d)
        fires("evidence naming no read unit anchors nothing", spent == 1)
        fires("…it is an id pair, as it always was", pairs == 1)
        fires("…and it is SAID OUT LOUD, per file, with the reason",
              len(uncounted) == 1 and uncounted[0][:3] == ("crosswalk.json", "refusals", 1)
              and "write the record id" in uncounted[0][3])

        # a manifest row is not a ruling and is not reported as one
        (d / "third_crosswalk.json").write_text(json.dumps({"inputs": [
            {"what": "1840 left sheets read in this repo", "path": "pages/", "n": 17}]}))
        fires("a structural inputs row is not a ruling anybody failed to count",
              len(count_spent(d)[2]) == 1)
        (d / "third_crosswalk.json").write_text(json.dumps({"passes": [
            {"pass": "T-0570", "what": "volume 1 against the residents"}]}))
        fires("…while a pass note IS reported, as a sweep that names no unit",
              len(count_spent(d)[2]) == 2)

        # the key the second hop always read and the spend half never did
        (d / "crosswalk.json").write_text(json.dumps({"matches": [
            {"household_id": "hh_pearsons_hiram", "rule": "the forename agrees in full"}]}))
        fires("a ruling naming a town household by household_id is a spend",
              count_spent(d)[0] == 2)

    # --- the second hop
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        cards = {"hh_a": {"id": "hh_a", "persons": [{"sources": ["fergus_1843"]}]},
                 "hh_b": {"id": "hh_b", "persons": [{"sources": ["andreas_1884_v1"]}]}}
        (d / "x_crosswalk.json").write_text(json.dumps({"heads": [
            {"outcome": "matched", "household_id": "hh_a",
             "discriminators": [{"source_id": "fergus_1843"}]},
            {"outcome": "matched", "household_id": "hh_b",
             "discriminators": [{"source_id": "fergus_1843"}]},
            {"outcome": "matched", "household_id": "hh_b"},
            {"outcome": "matched", "household_id": "hh_nobody",
             "discriminators": [{"source_id": "fergus_1843"}]},
            {"outcome": "refused", "household_id": "hh_a",
             "discriminators": [{"source_id": "fergus_1843"}]}]}))
        reached, judgeable, wrote, _ = count_written(d, cards)
        fires("a ruling naming a person in the town is reached", reached == 3)
        fires("…a refusal is not, however well sourced", reached == 3)
        fires("…nor is one naming a person the town does not have", reached == 3)
        fires("a ruling stating no source is unjudgeable, not unwritten",
              judgeable == 2)
        fires("a card citing the ruling's own source has learned it", wrote == 1)
        fires("…and a card citing something else has not", judgeable - wrote == 1)

    # --- T-0635, consolidation pass 2. The two ways a crosswalk can hide a ruling from
    # this hop, both found on dev with the hop reporting a clean 0 unwritten: a ruling
    # grouped one level down under the POOL it was matched against, and a ruling that
    # spells its verdict in the name of the list it is filed in rather than in `outcome`.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        cards = {"hh_a": {"id": "hh_a", "persons": [
                     {"sources": ["fergus_1839"],
                      "note": "Fergus 1839 prints this person at entry f1839_e1."}]},
                 "hh_b": {"id": "hh_b", "persons": [{"sources": ["andreas_1884_v1"]}]}}
        # The reading the pool was matched against, so a ruling can name a unit and
        # the card can be asked whether it names it back (T-0989).
        (d / "entries.json").write_text(json.dumps({"records": [
            {"id": "f1839_e1", "normalized": "A. Name"},
            {"id": "f1839_e2", "normalized": "B. Name"}]}))
        (d / "pooled_crosswalk.json").write_text(json.dumps({
            "source_id": "fergus_1839",
            "residents": {
                "matches": [{"household_id": "hh_a", "entry": "f1839_e1"},
                            {"household_id": "hh_b", "entry": "f1839_e2"}],
                "refusals": [{"household_id": "hh_a", "entry": "f1839_e1"}],
                "ambiguous": [{"household_id": "hh_b", "entry": "f1839_e2"}],
                "contested": [{"household_id": "hh_a", "entry": "f1839_e1"}],
            },
            "voters": {"matches": [{"name": "a name in another reading"}]},
        }))
        reached, judgeable, wrote, on_file_word = count_written(d, cards)
        fires("a ruling grouped under a pool is reached, not invisible", reached == 2)
        fires("…a refusal in the same pool is still not a ruling to spend", reached == 2)
        fires("…nor is an ambiguous or contested rival still standing", reached == 2)
        fires("…nor a match naming no person this town holds", reached == 2)
        fires("the file's own source makes a pooled ruling judgeable", judgeable == 2)
        fires("…and only the card citing it AND naming the entry has learned it",
              wrote == 1)
        fires("…and that one is reported as resting on the file's word",
              on_file_word == 1)
        fires("a list nested deeper than a pool is still not followed as a matrix",
              [k for k, _ in ruling_lists({"a": {"b": {"c": {"d": [1]}}}})] == [])

        fires("same_name_support counts as what a ruling rests on",
              rests_on({"same_name_support": [{"source_id": "s1"}]}) == {"s1"})
        fires("a bare source_id counts too", rests_on({"source_id": "s2"}) == {"s2"})
        fires("a ruling resting on nothing states nothing", rests_on({}) == set())

    # --- T-0962. The same fault as T-0635's second half, one grammatical number over:
    # a container the list had not heard of hides its rulings, and a domain with nothing
    # visible is a domain that never appears in the report at all. Found on dev with the
    # hop showing 1,282 of 1,282 written and church absent from the table while
    # second_presbyterian_crosswalk.json's 82 `matched` roll members named 82 cards, none
    # of which cited the roll. The second assertion is the price of the first: widening
    # the list may not let a container OVERRULE a ruling that stated its own verdict.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        cards = {"hh_a": {"id": "hh_a", "persons": [
                     {"sources": ["second_presb"],
                      "note": "The roll carries this person at member sp_1."}]},
                 "hh_b": {"id": "hh_b", "persons": [{"sources": ["andreas_1884_v1"]}]}}
        (d / "roll.json").write_text(json.dumps({"records": [
            {"id": "sp_1", "normalized": "A. Name"},
            {"id": "sp_2", "normalized": "B. Name"}]}))
        (d / "roll_crosswalk.json").write_text(json.dumps({
            "source_id": "second_presb",
            "matched": [{"household_id": "hh_a", "member": "sp_1"},
                        {"household_id": "hh_b", "member": "sp_2"}],
            "refused": [{"household_id": "hh_a", "member": "sp_1"}],
        }))
        reached, judgeable, wrote, _ = count_written(d, cards)
        fires("a ruling filed under `matched` is reached, not invisible", reached == 2)
        fires("…and `refused` beside it is still not a ruling to spend", reached == 2)
        fires("…and only the card citing the roll has learned it", wrote == 1)

        (d / "roll_crosswalk.json").write_text(json.dumps({
            "source_id": "census_1830",
            "matched": [{"household_id": "hh_a", "outcome": "earlier_evidence",
                         "member": "sp_1"},
                        {"household_id": "hh_b", "outcome": "matched",
                         "member": "sp_2"}],
        }))
        fires("a ruling stating its own verdict is judged on that, not on its heading",
              count_written(d, cards)[0] == 1)

    # --- T-0598: THE THIRD HOP. A crosswalk that states no source at all is a
    # FAULT, not merely a blind spot in the instrument, and a file-level statement
    # is how a generated crosswalk answers for all of its rulings at once.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        cards = {"hh_a": {"id": "hh_a", "persons": [
                     {"sources": ["voter_lists_irad"],
                      "note": "Polled at poll_1833_001."}]},
                 "hh_b": {"id": "hh_b", "persons": [{"sources": ["andreas_1884_v1"]}]}}
        (d / "polls.json").write_text(json.dumps({"records": [
            {"id": "poll_1833_001", "normalized": "A. Name"},
            {"id": "poll_1833_002", "normalized": "B. Name"}]}))
        bare = {"entries": [{"outcome": "matched", "matched_resident": "hh_a",
                             "record_id": "poll_1833_001"},
                            {"outcome": "matched", "matched_resident": "hh_b",
                             "record_id": "poll_1833_002"}]}
        (d / "voter_crosswalk.json").write_text(json.dumps(bare))
        reached, judgeable, wrote, _ = count_written(d, cards)
        fires("a crosswalk stating no source anywhere is a FAULT, not a measurement",
              (reached, judgeable, reached - judgeable) == (2, 0, 2))

        (d / "voter_crosswalk.json").write_text(json.dumps(
            dict(bare, source_id="voter_lists_irad")))
        reached, judgeable, wrote, _ = count_written(d, cards)
        fires("…and one source_id at the top of the file answers for every ruling in it",
              (reached, judgeable, reached - judgeable) == (2, 2, 0))
        fires("…which then judges each card on its own merits", wrote == 1)

        (d / "voter_crosswalk.json").write_text(json.dumps(
            dict(bare, source_ids=["voter_lists_irad", "tax_1833"])))
        _, judgeable, _, _ = count_written(d, cards)
        fires("a file may rest on several sources, stated as source_ids", judgeable == 2)

        (d / "voter_crosswalk.json").write_text(json.dumps({
            "source_id": "voter_lists_irad",
            "entries": [{"outcome": "matched", "matched_resident": "hh_b",
                         "discriminators": [{"source_id": "andreas_1884_v1"}]}]}))
        _, _, wrote, on_file_word = count_written(d, cards)
        fires("a ruling naming its own source is judged on that, not the file's",
              wrote == 1)
        fires("…and it does not rest on the file's word", on_file_word == 0)

        fires("evidence rows state a source like any other basis",
              rests_on({"evidence": [{"source_id": "s3", "locator": "poll_1833 line 26"}]})
              == {"s3"})
        fires("source_ids is read wherever source_id is",
              rests_on({"source_ids": ["s4", "s5"]}) == {"s4", "s5"})
        fires("a file stating nothing rests on nothing", doc_rests_on({"entries": []}) == set())
        fires("sources are found at any depth in a record",
              cited_sources({"a": {"b": [{"sources": ["deep"]}]}}) == {"deep"})
        fires("a plural person_ids ruling names every person it reaches",
              people_named({"person_ids": ["p1", "p2"]}) == ["p1", "p2"])


    # --- T-0989. THE FALLBACK IS NOT THE SAME TEST AS A STATED SOURCE, and every
    # assertion here fails on the code as it stood. A file-level source id is shared
    # by every ruling in its file, so under the old rule ONE citation — put on the
    # card by any pass, for any reason — counted all of them written at once. That is
    # how census_1840 read 27 of 27 written while 15 of the 27 cards carried no
    # mention of the census, and it covered 811 of the 1,359 person-reaching rulings
    # in this repo. The fixture below is hh_garrett_a's case in miniature: the card
    # cites the directory because a later pass wrote a generic block on it, and
    # nothing of the entry the ruling adjudicated is anywhere on it.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "entries.json").write_text(json.dumps({"records": [
            {"id": "f1839_e0527", "normalized": "Garrett, Augustus"}]}))
        crosswalk = {"source_id": "fergus_chicago_directory_1839",
                     "matches": [{"household_id": "hh_g",
                                  "entries_1839": [{"claim": "f1839_e0527"}]}]}
        (d / "x_crosswalk.json").write_text(json.dumps(crosswalk))

        cited_only = {"hh_g": {"id": "hh_g", "directories": {
            "note": "LATER EVIDENCE, BESIDE THE 1835 CLAIMS AND NOT INSIDE THEM.",
            "sources": ["fergus_chicago_directory_1839"]}}}
        reached, judgeable, wrote, _ = count_written(d, cited_only)
        fires("a card citing the file's source for an unrelated reason has NOT "
              "learned the ruling", (reached, judgeable, wrote) == (1, 1, 0))

        told = {"hh_g": {"id": "hh_g", "directories": {
            "note": "Fergus 1839 prints this person at f1839_e0527, printed page 15.",
            "sources": ["fergus_chicago_directory_1839"]}}}
        _, _, wrote, on_file_word = count_written(d, told)
        fires("…and a card naming the entry the ruling adjudicated HAS", wrote == 1)
        fires("…counted, and reported, as resting on the file's word",
              on_file_word == 1)

        # The citation is still necessary. Naming the unit without citing the source
        # would mean the card knows the entry and not where it came from.
        unsourced_card = {"hh_g": {"id": "hh_g", "note": "see f1839_e0527"}}
        fires("naming the unit without citing the source is not a spend",
              count_written(d, unsourced_card)[2] == 0)

        # A string that resolves to no unit this domain has read buys nothing —
        # the rule T-0602 set for the spend half, held on both hops now.
        fires("a subject is only a unit the domain has actually read",
              subject_of({"entries_1839": [{"claim": "not_a_unit"}]},
                         units_read(d)) == set())
        fires("…and a unit it has read is the ruling's subject",
              subject_of(crosswalk["matches"][0], units_read(d)) == {"f1839_e0527"})

        # A sheet-and-line ruling names no unit id and is not therefore anonymous:
        # the sheet is where the reader goes back to the line, and it is what
        # spend_census_1840_heads.py writes onto the card.
        fires("a sheet-and-line ruling is subject to its sheet",
              subject_of({"familysearch_id": "33S7-9YYJ-99F", "line": 3}, set())
              == {"33S7-9YYJ-99F"})
        fires("…and a sheet id with no line is not an anchor",
              subject_of({"familysearch_id": "33S7-9YYJ-99F"}, set()) == set())

        # A fallback ruling that names no subject at all reads UNWRITTEN, not
        # unsourced: the file did say what it rests on, so the hop knows what to look
        # for and the answer is no. Calling it unsourced would push it into T-0598's
        # ratchet, whose remedy is to state a source that is already stated.
        (d / "x_crosswalk.json").write_text(json.dumps({
            "source_id": "fergus_chicago_directory_1839",
            "matches": [{"household_id": "hh_g"}]}))
        reached, judgeable, wrote, _ = count_written(d, cited_only)
        fires("a fallback ruling naming no unit is unwritten, not unsourced",
              (reached, judgeable, wrote) == (1, 1, 0))

    # --- the ratchet
    def over(unspent: int, ceiling: int) -> bool:
        return unspent > ceiling
    fires("the gate fires when the gap widens", over(563, 562))
    fires("the gate is silent when the gap holds", not over(562, 562))
    fires("the gate is silent when a domain is spent down", not over(0, 562))

    # --- raising and tightening, against a real baseline file
    global BASELINE
    kept = BASELINE
    # These cases drive the real writers, which report to stdout by design. A
    # self-test that narrates every one of them buries its own verdict.
    import contextlib, io
    hush = contextlib.redirect_stdout(io.StringIO())
    try:
        with tempfile.TemporaryDirectory() as tmp, hush:
            BASELINE = Path(tmp) / "baseline.json"
            rows = measure()
            live = {r["domain"]: r["unspent"] for r in rows}
            some = rows[0]["domain"]

            fires("--rebaseline writes the file when there is none",
                  rebaseline() == 0 and BASELINE.exists())
            fires("…and REFUSES a second time, so no run launders every ceiling at once",
                  rebaseline() == 1)

            doc = json.loads(BASELINE.read_text())
            fires("the first write records every domain",
                  doc["unspent_ceiling"] == live)

            fires("a raise with no reason is refused",
                  raise_ceiling(some, "   ") == 1)
            fires("a raise on an unknown domain is refused",
                  raise_ceiling("no_such_domain", "because") == 1)
            fires("a raise with nothing to raise is refused, and points at --tighten",
                  raise_ceiling(some, "because") == 1)

            # drop one ceiling below the live figure so a raise is genuinely owed
            doc["unspent_ceiling"][some] = live[some] - 1
            BASELINE.write_text(json.dumps(doc))
            fires("the gate fires on that one domain", gate(quiet=True) == 1)
            fires("a reasoned raise is taken", raise_ceiling(some, "T-9999 read it") == 0)
            after = json.loads(BASELINE.read_text())
            fires("…the ceiling moves to what the domain now reads",
                  after["unspent_ceiling"][some] == live[some])
            fires("…the reason is written down, with what it moved from and to",
                  after["raised"][-1]["why"] == "T-9999 read it"
                  and after["raised"][-1]["to"] == live[some])
            fires("…and only that domain moved", all(
                  after["unspent_ceiling"][d] == live[d] for d in live if d != some))
            fires("the gate is green again", gate(quiet=True) == 0)

            # slack: a ceiling above the live figure is reclaimable
            after["unspent_ceiling"][some] = live[some] + 50
            BASELINE.write_text(json.dumps(after))
            fires("slack does not fire the gate", gate(quiet=True) == 0)
            fires("--tighten reclaims it", tighten() == 0)
            fires("…down to what the domain reads",
                  json.loads(BASELINE.read_text())["unspent_ceiling"][some] == live[some])
            fires("…and a second --tighten has nothing left to take", tighten() == 0)
            fires("…and never RAISES a ceiling that is already tight",
                  json.loads(BASELINE.read_text())["unspent_ceiling"] == live)

            # T-0992: the SCOPED tightening. A bare --tighten pins every domain to the
            # figure it happened to read that morning, and reading ahead of an
            # adjudication is what the ratified ladder requires — so a pass that spends
            # ONE domain must be able to reclaim only its own slack.
            slacked = json.loads(BASELINE.read_text())
            others = [d for d in live if d != some]
            slacked["unspent_ceiling"] = {d: live[d] + 50 for d in live}
            BASELINE.write_text(json.dumps(slacked))
            fires("a scoped tightening with no reason is refused",
                  tighten(some, "read", "") == 1
                  and json.loads(BASELINE.read_text())["unspent_ceiling"][some]
                  == live[some] + 50)
            fires("a scoped tightening reclaims the domain it names",
                  tighten(some, "read", "T-0992 self-test") == 0
                  and json.loads(BASELINE.read_text())["unspent_ceiling"][some] == live[some])
            fires("…and leaves every other domain's slack alone",
                  all(json.loads(BASELINE.read_text())["unspent_ceiling"][d] == live[d] + 50
                      for d in others))
            fires("…and records itself in lowered[], with the reason it was given",
                  json.loads(BASELINE.read_text())["lowered"][-1]
                  == {"domain": some, "hop": "read", "from": live[some] + 50,
                      "to": live[some], "date": date.today().isoformat(),
                      "why": "T-0992 self-test"})
            fires("a domain nobody registered is refused rather than silently ignored",
                  tighten("no_such_domain", "read", "why") == 1)
            scoped = json.loads(BASELINE.read_text())
            scoped["unspent_ceiling"] = dict(live)
            scoped["unwritten_ceiling"] = {d: 5 for d in scoped.get("unwritten_ceiling", {})}
            BASELINE.write_text(json.dumps(scoped))
            hopped = next((d for d in scoped["unwritten_ceiling"]), None)
            if hopped:
                fires("--hop write tightens the write ceiling and not the read one",
                      tighten(hopped, "write", "T-0992 self-test") == 0
                      and json.loads(BASELINE.read_text())["unwritten_ceiling"][hopped] == 0
                      and json.loads(BASELINE.read_text())["unspent_ceiling"] == live)
            # …and hand the cases below the fully-tight baseline they were written against.
            BASELINE.write_text(json.dumps(after))
            fires("the scoped cases leave a baseline a bare --tighten still closes",
                  tighten() == 0
                  and json.loads(BASELINE.read_text())["unspent_ceiling"] == live)

            # T-0598: the unsourced ratchet, which defaults to zero and so needs no
            # entry in the baseline to bite. Proved against the live tree, which
            # states a source for every ruling that reaches a town person.
            tight = json.loads(BASELINE.read_text())
            tight.pop("unsourced_ceiling", None)
            BASELINE.write_text(json.dumps(tight))
            fires("an unsourced ceiling nobody wrote defaults to zero, and is green "
                  "because the backfill landed", gate(quiet=True) == 0)
            reaching = next((r["domain"] for r in measure() if r["reached"]), None)
            fires("some domain rules onto a town person at all", reaching is not None)
            if reaching:
                tight["unsourced_ceiling"] = {reaching: -1}
                BASELINE.write_text(json.dumps(tight))
                fires("…and a domain over its unsourced ceiling fires the gate",
                      gate(quiet=True) == 1)
                tight["unsourced_ceiling"] = {reaching: 5}
                BASELINE.write_text(json.dumps(tight))
                fires("…while an allowance somebody wrote on purpose is honoured",
                      gate(quiet=True) == 0)
                fires("--tighten reclaims that allowance too, unasked",
                      tighten() == 0 and
                      json.loads(BASELINE.read_text())["unsourced_ceiling"][reaching] == 0)
    finally:
        BASELINE = kept

    for line in failures:
        print(f"   SILENT: {line}")
    print("SELF-TEST %s — %d case(s)" % ("FAIL" if failures else "PASS", len(ran)))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--rebaseline", action="store_true")
    parser.add_argument("--raise", dest="raise_domain", metavar="DOMAIN",
                        help="raise ONE domain's ceiling to what it now reads; needs --why")
    parser.add_argument("--why", default="", help="the reason a raise is being taken")
    parser.add_argument("--hop", default="read", choices=("read", "write", "source"),
                        help="which ceiling to raise: read (read vs ruled), write "
                             "(ruled vs on a card) or source (reaches a person, states nothing)")
    parser.add_argument("--tighten", nargs="?", const="*", metavar="DOMAIN",
                        help="lower every ceiling to what its domain now reads (always safe); "
                             "name ONE domain to reclaim only that domain's slack on --hop, "
                             "which records itself in lowered[] and needs --why")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--ledger-build", action="store_true",
                        help="write the closed unit ledger and dated research report")
    parser.add_argument("--ledger-self-test", action="store_true",
                        help="mutate the closed-ledger contract in memory")
    parser.add_argument("--check", action="store_true",
                        help="run the historical ratchet and closed-ledger gate")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.ledger_self_test:
        from research_spend_ledger import self_test as ledger_self_test
        return ledger_self_test()
    if args.ledger_build:
        from research_spend_ledger import build as build_ledger
        faults = build_ledger(measure())
        for fault in faults:
            print("   FAIL: " + fault)
        if not faults and not args.quiet:
            print("OK: closed research-spend ledger and report written")
        return 1 if faults else 0
    if args.check:
        from research_spend_ledger import check as check_ledger
        old = gate(quiet=True)
        faults = check_ledger(measure())
        for fault in faults:
            print("   FAIL: " + fault)
        if not old and not faults and not args.quiet:
            print("OK: historical research ratchet and closed ledger")
        return 1 if old or faults else 0
    if args.raise_domain:
        return raise_ceiling(args.raise_domain, args.why, args.hop)
    if args.tighten:
        one = None if args.tighten == "*" else args.tighten
        return tighten(one, args.hop, args.why)
    if args.rebaseline:
        return rebaseline()
    if args.gate:
        return gate(quiet=args.quiet)
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
