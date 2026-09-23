#!/usr/bin/env python3
"""One registry and one gate for every committed research domain.

    tools/research_domains.py --build       write/normalise each domain's scaffold
    tools/research_domains.py --check       the gate
    tools/research_domains.py --self-test   the gate's assertions still fire when broken

WHAT THIS IS FOR. The project has exactly one research pipeline that works — the
newspapers' — and its shape is the reason it works: a register that says where a
passage IS, hand-authored claims that say what was read out of it, a CLOSED kind
vocabulary, a required reading grade, verbatim quotes the gate rebuilds out of the
committed text, a coverage declaration, and an identity layer that declares its
refusals as carefully as its merges.

Six more domains are about to be read in parallel — the civic lists, the 1830
census, the 1840 census, a church register, books and directories — by ten runs
that cannot see each other. If each invents its own file shape, the consolidation
(T-0513) spends its whole run re-reading ten dialects, and the refusals nobody
wrote down have to be made again. So the shape is fixed HERE, before the sweep
starts, and this file is the gate that holds it.

TWO SHAPES, AND THE DIFFERENCE IS THE SOURCE AND NOT THE DOMAIN.

  records — for a LIST. A voter roll, a census line, a baptism entry, a directory
            entry: one printed row, read as it stands (`as_read`) and again as this
            project spells it (`normalized`). A row is not a claim about the town;
            it is a claim about what the page says.

  claims  — for PROSE. A book paragraph that says something about 1835 Chicago.
            Same shape as the newspaper claims, because it is the same act: a
            `kind`, a verbatim `quote`, a `normalized` reading, the `entities` it
            names, and `town_finding` for whether it bears on the reconstruction at
            all — the reminiscence that is only about the author is worth recording
            and is not worth placing.

A domain may hold both. `books` and `directories` are the two the verbatim-quote
gate binds, because they are the two whose text this repo commits.

`data/research/` IS RESEARCH, NOT PAYLOAD, and this subtree inherits that: nothing
here is published, `tools/publish.sh` does not copy it, and
`tools/newspaper_corpus.py --check` already asserts the whole of `data/research/`
stays out of `site/chicago/4d/`.

NOTHING IN HERE AUTHORS A READING. --build writes empty scaffolds and a manifest;
the claims and the records are hand-authored, one ticket at a time, by the runs
this file exists to make consistent.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # chicago/4d
RESEARCH = ROOT / "data" / "research"
SOURCES = ROOT / "data" / "sources"
MANIFEST = RESEARCH / "domains.json"

SCHEMA_VERSION = 2

DECLARED_UNITS = [{
    "glob": "**/*.json",
    "containers": "$declared",
    "id": "row.id || file-relative JSON pointer",
    "name_fields": ["normalized", "as_read", "quote"],
}]

# The six domains, in the order the owner named them, with what each is FOR. The
# order is the manifest's order and the READMEs' order; it is not alphabetical on
# purpose, because "civic first, books last" is the reading order too.
DOMAINS = {
    "civic": {
        "title": "Civic lists",
        "holds": "records",
        "what": "The town's own lists of its own people — the poll books and voter "
                "rolls of 1833-1835, and the officers, jurors and subscribers printed "
                "beside them.",
        "ledger_units": DECLARED_UNITS,
    },
    "census_1830": {
        "title": "The 1830 federal census",
        "holds": "records",
        "what": "Chicago was enumerated in Peoria County in 1830. The named schedule "
                "is the object; the county aggregates this project already holds are "
                "not it.",
        "ledger_units": DECLARED_UNITS,
    },
    "census_1840": {
        "title": "The 1840 federal census",
        "holds": "records",
        "what": "Seventy-five page images and a head-of-household index. 1840 is "
                "LATER EVIDENCE and never an 1835 household fact on its own.",
        "ledger_units": DECLARED_UNITS,
    },
    "church": {
        "title": "Church registers",
        "holds": "records",
        "what": "Baptisms, marriages and burials — St Mary's 1833-1835 first, because "
                "eleven images of its register are already deposited and unread.",
        "ledger_units": DECLARED_UNITS,
    },
    "books": {
        "title": "Books and reminiscences",
        "holds": "claims",
        "what": "Prose: Fergus' Historical Series, Hubbard's autobiography, H. H. "
                "Porter's Short Autobiography, and the memoirs printed beside them.",
        "ledger_units": DECLARED_UNITS,
    },
    "directories": {
        "title": "Directories",
        "holds": "claims",
        "what": "The 1839 Chicago directory and its successors — entry by entry, "
                "structured, and crosswalked rather than quoted at second hand.",
        "ledger_units": DECLARED_UNITS,
    },
    # The seventh, added by T-0562 when the owner put the Newberry Library's
    # genealogical index on the Internet Archive. It is not one of his six original
    # domains and it is not a source of facts at all: it is a FINDING AID, and it
    # earns a domain here because it is list-shaped, it is large, and the one thing
    # it must never do — put a surname behind a person — is a thing only a gate can
    # stop. `tools/read_newberry_index.py --check` is that gate; this entry is what
    # makes the records, the coverage and the crosswalk answer to this one too.
    # The eighth, added by T-0557 when the owner asked for the Illinois State Archives'
    # land tract sales. It is not one of his six original domains and it is not a list of
    # PEOPLE: it is a list of TRANSACTIONS, and the difference is the whole discipline
    # here. A purchase says a man bought ground; only the register's `Residence` column
    # says where he lived, and it says COOK, not Chicago. So a row is a record about a
    # sale, and the crosswalk beside it is the only place a sale is allowed to reach a
    # person. `tools/read_land_sales.py --check` is that gate.
    "land_sales": {
        "title": "Federal land tract sales",
        "holds": "records",
        "what": "The Illinois State Archives' Public Domain Land Tract Sales database, "
                "read for the townships around Chicago through 1836. A sale is a "
                "transaction, never a residence; the register's own Residence column is "
                "the only thing here that speaks to where a purchaser lived.",
        "ledger_units": DECLARED_UNITS,
    },
    # The ninth, registered by T-0678 — and the last domain in this directory that was
    # not. It has been read since T-0574 and T-0577 and adjudicated since, and the
    # registry never held it, so `tools/measure_research_spend.py` printed it as "not
    # registered in domains.json (not measured)" and measured NEITHER hop for 767 read
    # units and 109 rulings that name a person this town holds a card for. A domain
    # nothing measures is a domain that can drift for as long as nobody looks.
    #
    # IT IS SHAPED BY ITS OWN TOOLS AND NOT BY THIS ONE, which is why registering it
    # took two accommodations rather than a rewrite of two generated files: its reading
    # lives in domain-owned files at the top of the directory (people.json,
    # death_notices.json) rather than under records/, and its crosswalk is a ROSTER
    # crosswalk — a printed name against a town person — rather than a pairwise identity
    # crosswalk. Both shapes are gated already, by `tools/old_settlers.py --check` and
    # `tools/read_fergus_obits.py --check`, and both run in check.sh. See
    # `coverage_reached_by_a_domain_file` and `check_crosswalk` below for what each
    # accommodation does and, more importantly, what it still refuses to let past.
    "old_settlers": {
        "title": "The Calumet Club's old settlers",
        "holds": "records",
        "what": "The rolls of the Calumet Club's receptions to the old settlers of "
                "Chicago (1879-1882) and the obituary list printed in Fergus's 1843 "
                "directory. Every one of them is LATER EVIDENCE about a person, and the "
                "obituary list's own header admits it also names citizens who arrived "
                "after 1843 — so a name here is never an 1835 residence.",
        "ledger_units": DECLARED_UNITS,
    },
    "newberry_index": {
        "title": "The Newberry genealogical index",
        "holds": "records",
        "what": "A four-volume photostat of the Newberry Library's genealogical card "
                "index (G. K. Hall, 1960), read for the cards whose citation names "
                "Chicago, Cook County or Illinois. A card says where a genealogy IS; "
                "it never places a person, and nothing here may grade one.",
        "ledger_units": DECLARED_UNITS,
    },
    # These three domains predate this scaffold and retain their domain-owned
    # validators. T-1143 nevertheless registers the actual reading files and the
    # stable row identifiers that enter the closed spend ledger.
    "genealogytrails": {
        "title": "Genealogy Trails transcriptions",
        "holds": "claims",
        "what": "Hand-read transcriptions of Chicago church and civic records; a later "
                "primary-source reading may supersede a claim but never erase it.",
        "managed": False,
        "legacy_measure": False,
        "ledger_units": [{
            "glob": "claims/*.json", "containers": ["claims"],
            "id": "row.id", "name_fields": ["normalized", "quote"],
        }],
    },
    "newspapers": {
        "title": "Chicago newspapers",
        "holds": "claims",
        "what": "Claims read from the committed Chicago Democrat and Chicago American "
                "corpus; gazetteers and registers are generated from these units.",
        "managed": False,
        "legacy_measure": False,
        "ledger_units": [{
            "glob": "extracted/*.json", "containers": ["claims"],
            "id": "row.id", "name_fields": ["normalized", "quote"],
        }],
    },
    "residents": {
        "title": "Resident research passes",
        "holds": "research_passes",
        "what": "Named resident cohorts and focused audits whose positive and negative "
                "findings must survive regeneration of the public resident cards.",
        "managed": False,
        "legacy_measure": False,
        "ledger_units": [
            {"glob": "pass_*_cohort.json", "containers": ["people"],
             "id": "row.person_id"},
            {"glob": "pilot_75_cohort.json", "containers": ["people"],
             "id": "row.person_id"},
            {"glob": "scene_window_trade_audit.json", "containers": ["rows"],
             "id": "row.person_id || file-relative JSON pointer"},
            {"glob": "letter_list_reading_suspicions.json", "containers": ["rows"],
             "id": "row.person_id || file-relative JSON pointer"},
        ],
    },
}

# The claim vocabulary is closed. An open one becomes a synonym list within a week
# and then nothing can be compiled from it — the same reason `compile_gazetteer.py`
# closes the newspapers'. These are the newspapers' nine, plus four the new domains
# need and the papers never did: `landscape` for what a reminiscence says the ground
# looked like, `appearance` for what a building or a person looked like, `household`
# for a census line's composition, and `civic` for an office, a poll or an ordinance.
#
# AND ONE THAT NAMES NO SUBJECT AT ALL (T-1023). `turned_line` is a printed line that
# is part of the record ABOVE it and not a record — the tail of an entry too long for
# the measure, which this scan un-indented so the reader took it for an entry of its
# own and filed `. -house Clark street (See card)` as a man's surname. Its claim exists
# for one reason: claim ids are allocated by position, they are cited by id from the
# identity layer and from the second-hand comparison, and folding the line away would
# renumber every entry after it. So the id keeps its place, the line is read with the
# entry above, and the claim says what it is. A pass that reads people must skip it,
# and the vocabulary is where it learns to. There is exactly one in the corpus and the
# reading tool's --self-test holds it to the text.
KINDS = ("person", "business", "building", "street", "infrastructure",
         "event", "shipping", "price", "notice",
         "landscape", "appearance", "household", "civic",
         "turned_line")

# Ruling 2, unchanged from the papers. `transcription_mediated` is a reading made
# through somebody else's transcription; `scan_verified` is a reading made off the
# page image itself and OUTRANKS it. There is no third value, and the field is
# required — a reading whose grade is unstated is the one that gets cited as though
# it were the stronger one.
READINGS = ("transcription_mediated", "scan_verified")

# What a record row may claim about itself. Deliberately the confidence vocabulary
# the rest of the project uses, so a row can be promoted into a resident record
# without a translation step.
CONFIDENCES = ("documented", "inferred", "conjectural")

RECORD_FIELDS = ("id", "as_read", "normalized", "locator", "reading", "confidence", "notes")
CLAIM_FIELDS = ("id", "kind", "reading", "quote", "normalized", "locator",
                "describes_date", "entities", "town_finding", "notes")

# A coverage declaration says WHAT WAS READ, in the units the source is delivered
# in. An undeclared item is not read yet, which is not a fault and must never be
# reported as one; a DECLARED item nothing reaches is a hole, and that is the whole
# point of the file.
COVERAGE_UNITS = ("list", "image", "page")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def surname_only(name: str) -> bool:
    """True when a name carries nothing but a surname.

    The 1835 lists are full of families and a bare surname separates none of them,
    so a merge on one is always a refusal — the same rule `identity.json` states
    for two read initials that disagree, one step further down.
    """
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    parts = [p for p in parts if p.lower() not in ("mr", "mr.", "mrs", "mrs.", "miss", "dr", "dr.")]
    return len(parts) < 2


def source_ids(sources: Path) -> set:
    ids = set()
    if not sources.exists():
        return ids
    for path in sorted(sources.glob("*.json")):
        try:
            doc = load(path)
        except Exception:
            continue
        if isinstance(doc, dict) and doc.get("id"):
            ids.add(str(doc["id"]))
    return ids


def coverage_key(unit: str, item) -> str:
    return "%s:%s" % (unit, item)


# --------------------------------------------------------------------------- #
# THE images[] COVERAGE SHAPE, AND WHY THE GATE READS IT RATHER THAN REWRITING IT
#
# T-0536, and the ticket asked for the decision in writing, so here it is.
#
# `census_1840` declared its deposit before T-0492 fixed `declarations[]`, and it
# declared it RICHER: one object per page image, carrying the FamilySearch id, the
# sheet side, the printed page number, the line count, a `read_state` and a
# `page_file`. So the shared gate read zero declarations out of the domain that has
# been read the most, and either the tool learned that shape or the file was
# migrated to this one.
#
# THE GATE LEARNS `images[]`. Three reasons, in the order they bind:
#
#   1. The file is being appended to right now. T-0496 and the sheet-reading tickets
#      split out of T-0494 and T-0495 all extend this one document, on branches that
#      cannot see each other. Rewriting it underneath them loses readings in a merge,
#      and a lost reading is a sheet read twice.
#   2. `declarations[{unit, items[], ticket}]` has nowhere to put `read_state`,
#      `page_file` or `lines_with_an_entry` — and those three ARE the evidence that a
#      hole is a hole. The ticket forbids dropping a field to fit the shape.
#   3. `declarations[]` is a PROJECTION of `images[]`, not a rival to it: unit
#      `image`, items the FamilySearch ids, ticket the group's. A projection can be
#      derived, so nothing needs hand-migrating at all.
#
# THE DISTINCTION THAT MAKES THE HOLE ASSERTION MEAN SOMETHING is `read_state`. An
# image whose state is `inventoried_only` is declared as INVENTORIED — the sheet has
# been looked at and described and nothing has been read off it — and it is NOT
# asserted to be reached. Every other state declares the image READ, and a read image
# must name a committed `page_file` and be reached by a `pages/*.json`. Run together,
# the two states would make "declared" mean "seen", and a hole could never fire.
INVENTORIED_ONLY = "inventoried_only"


def coverage_images(cov: dict) -> list:
    """Every image object in an `images[]` coverage document, with its ticket.

    Schema 1 carried `images[]` at the top level. Schema 2 groups them, because the
    deposit is read in image groups by one ticket each; a group's `declared_by` is
    prose that opens with that ticket's id, and that is the ticket the declaration is
    attributed to. Both shapes are read here, and a domain with neither yields
    nothing — which is the correct answer for the six domains that use
    `declarations[]`.
    """
    out = []
    for image in cov.get("images") or []:
        out.append((image, str(cov.get("ticket") or "?")))
    for group in cov.get("groups") or []:
        found = re.search(r"T-\d{4}", str(group.get("declared_by") or ""))
        ticket = found.group(0) if found else "?"
        for image in group.get("images") or []:
            out.append((image, ticket))
    return out


def resolve_page_file(domain_dir: Path, name: str, page_file: str) -> Path:
    """Where a declared `page_file` actually is.

    The committed file states the path from `chicago/4d/`, which is what a person
    reading coverage.json wants; the gate holds a domain directory, which is what the
    self-test's synthetic tree gives it. Strip the one prefix that means "this
    domain" and the two agree.
    """
    prefix = "data/research/%s/" % name
    rel = page_file[len(prefix):] if page_file.startswith(prefix) else page_file
    return domain_dir / rel


def locator_reached(locator: dict) -> list:
    """The coverage keys a locator reaches. One locator may reach exactly one item."""
    if not isinstance(locator, dict):
        return []
    keys = []
    for unit in COVERAGE_UNITS:
        if locator.get(unit) is not None:
            keys.append(coverage_key(unit, locator[unit]))
    return keys


def rebuild_quote(domain_dir: Path, locator: dict):
    """Reassemble a claim's quote out of the domain's committed text.

    Returns (text, error). The rules are the newspapers': `lines` is an inclusive
    [first, last] pair of 1-based line numbers into `text_file`, and `spans` — for
    the case where a segmenter wove two columns into one line — names the exact
    substring taken from each. Never smoothed: the smoothed reading has a field of
    its own to live in, and it is `normalized`.
    """
    rel = locator.get("text_file")
    if not rel:
        return None, "names no text_file"
    path = domain_dir / "text" / rel
    if not path.exists():
        return None, "names text_file %r, which is not committed" % rel
    lines = path.read_text(encoding="utf-8").splitlines()
    spans = locator.get("spans")
    if spans:
        out = []
        for span in spans:
            n = int(span.get("line", 0))
            if n < 1 or n > len(lines):
                return None, "span names line %d, which %s does not have" % (n, rel)
            out.append(lines[n - 1][int(span["from"]):int(span["to"])])
        return "\n".join(out), None
    pair = locator.get("lines")
    if not pair or len(pair) != 2:
        return None, "names neither spans nor a [first, last] lines pair"
    first, last = int(pair[0]), int(pair[1])
    if first < 1 or last < first or last > len(lines):
        return None, "names lines %d-%d, which %s does not have" % (first, last, rel)
    return "\n".join(lines[first - 1:last]), None


def is_roster_crosswalk(doc) -> bool:
    """True for a crosswalk that rules a PRINTED NAME against the town, not spelling
    against spelling.

    Two shapes are in this directory and only one of them was ever checked here. The
    pairwise shape is `identity.json`'s: two spellings, `into` and `from`, and a rule
    naming both. The ROSTER shape rules one printed name against the whole residents
    layer — `as_read` on one side, the town's own `resident_name` on the other — and its
    refusals have no second spelling at all, because what was refused is the layer.
    old_settlers/crosswalk.json is the second kind, generated and gated by
    `tools/old_settlers.py`, and holding it to the first kind's fields reported all 45 of
    its merges as naming fewer than two spellings (T-0678).

    THE SHAPE IS DECIDED BY THE FILE AND NOT BY A ROW, deliberately: a file declares its
    rules once, in a `rules` block, and every row cites one by name. A row cannot pick the
    laxer reading by leaving a field out — a pairwise file has no `rules` block, so its
    merges are still held to `into`/`from`/verbatim, and a roster file with a malformed
    row fails as a roster row rather than falling through to nothing.
    """
    return isinstance(doc, dict) and isinstance(doc.get("rules"), dict) and bool(doc["rules"])


def check_roster_crosswalk(doc, label: str, bad: list) -> None:
    """The roster shape, held to the same four things the pairwise shape is.

    A merge names both spellings; the rule is written down (here ONCE, in the file's own
    `rules` block, and cited by name — which is stronger than repeating it per row, not
    weaker, because one edit changes every row that rests on it); a surname-only merge is
    always a refusal; and a merge carries evidence. A refusal is declared as explicitly as
    a merge, and names the rule and the reason — the second spelling is not demanded of it
    because there is none: the thing refused is every bearer in the layer, and the row says
    which candidates it looked at.
    """
    rules = doc.get("rules") or {}
    for i, merge in enumerate(doc.get("merges") or []):
        where = "%s merge %d" % (label, i)
        printed, town = str(merge.get("as_read") or ""), str(merge.get("resident_name") or "")
        if not printed or not town:
            bad.append("%s: a merge names fewer than two spellings" % where)
            continue
        rule = str(merge.get("rule") or "")
        if not rule.strip():
            bad.append("%s: a merge with no rule — %r into %r" % (where, printed, town))
            continue
        if rule not in rules:
            bad.append("%s: the merge cites rule %r, which the file's rules block does not "
                       "declare — %r into %r" % (where, rule, printed, town))
        if surname_only(printed) or surname_only(town):
            bad.append("%s: a surname-only merge is always a refusal — %r into %r"
                       % (where, printed, town))
        if not str(merge.get("evidence") or "").strip():
            bad.append("%s: a merge with no evidence — %r into %r" % (where, printed, town))
        if not merge.get("person_id"):
            bad.append("%s: a merge naming no person in the town — %r into %r"
                       % (where, printed, town))
    for i, refusal in enumerate(doc.get("refusals") or []):
        where = "%s refusal %d" % (label, i)
        printed = str(refusal.get("as_read") or "")
        if not printed:
            bad.append("%s: a refusal naming no printed spelling" % where)
            continue
        rule = str(refusal.get("rule") or "")
        if rule not in rules:
            bad.append("%s: the refusal cites rule %r, which the file's rules block does "
                       "not declare — %r" % (where, rule, printed))
        if not str(refusal.get("why") or "").strip():
            bad.append("%s: a refusal with no reason — %r" % (where, printed))


def check_crosswalk(doc, label: str, bad: list) -> None:
    """`crosswalk.json` is `identity.json`'s shape, and it is held to its rules.

    A merge needs a written rule; the rule must name BOTH spellings verbatim, so it
    reads back without the code; a surname-only merge is refused however good the
    rule is; and a refusal is declared as explicitly as a merge, naming both
    spellings, because the ABSENCE of a merge reads exactly like a pair nobody has
    looked at yet and the next sweep does the work again.
    """
    if is_roster_crosswalk(doc):
        return check_roster_crosswalk(doc, label, bad)
    for i, merge in enumerate(doc.get("merges") or []):
        where = "%s merge %d" % (label, i)
        into, frm = str(merge.get("into") or ""), str(merge.get("from") or "")
        if not into or not frm:
            bad.append("%s: a merge names fewer than two spellings" % where)
            continue
        rule = str(merge.get("rule") or "")
        if not rule.strip():
            bad.append("%s: a merge with no rule — %r into %r" % (where, frm, into))
            continue
        if into not in rule or frm not in rule:
            bad.append("%s: the merge rule does not name both spellings verbatim — "
                       "%r into %r" % (where, frm, into))
        if surname_only(into) or surname_only(frm):
            bad.append("%s: a surname-only merge is always a refusal — %r into %r"
                       % (where, frm, into))
        if not (merge.get("evidence") or []):
            bad.append("%s: a merge with no evidence[] — %r into %r" % (where, frm, into))
    for i, refusal in enumerate(doc.get("refusals") or []):
        where = "%s refusal %d" % (label, i)
        a, b = str(refusal.get("a") or ""), str(refusal.get("b") or "")
        if not a or not b:
            bad.append("%s: a refusal naming only one spelling — %r against %r" % (where, a, b))
            continue
        rule = str(refusal.get("rule") or "")
        if not rule.strip():
            bad.append("%s: a refusal with no rule — %r against %r" % (where, a, b))
            continue
        if a not in rule or b not in rule:
            bad.append("%s: the refusal rule does not name both spellings verbatim — "
                       "%r against %r" % (where, a, b))
        if not (refusal.get("evidence") or []):
            bad.append("%s: a refusal with no evidence[] — %r against %r" % (where, a, b))


def coverage_reached_by_a_domain_file(domain_dir: Path, bad: list):
    """(coverage key, file name) for every list a domain-owned file says it read.

    The units it counts are the ones `measure_research_spend.py` counts: an entry of a
    `records` or `claims` array carrying a name. A file with none of those names nothing.
    """
    for path in sorted(domain_dir.glob("*.json")):
        if "crosswalk" in path.name or path.name in ("coverage.json", "domains.json"):
            continue
        try:
            doc = load(path)
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        named = 0
        sources = set()
        if isinstance(doc.get("source_id"), str):
            sources.add(doc["source_id"])
        declared = doc.get("units_in")
        containers = ("records", "claims")
        if isinstance(declared, str) and declared.strip():
            if not isinstance(doc.get(declared.strip()), list):
                bad.append("%s/%s: declares units_in %r and holds no such array"
                           % (domain_dir.name, path.name, declared))
            containers += (declared.strip(),)
        for key in containers:
            for unit in doc.get(key) or []:
                if not isinstance(unit, dict):
                    continue
                if any(unit.get(n) for n in ("normalized", "as_read", "quote")):
                    named += 1
                for field in ("source", "source_id"):
                    if isinstance(unit.get(field), str):
                        sources.add(unit[field])
        if not named:
            continue
        for sid in sorted(sources):
            yield coverage_key("list", sid), path.name


def check_domain(name: str, spec: dict, research: Path, known_sources: set, bad: list) -> dict:
    domain_dir = research / name
    counts = {"records": 0, "claims": 0, "declared": 0, "inventoried": 0}
    if not domain_dir.exists():
        bad.append("%s: the domain has no directory — run --build" % name)
        return counts
    if not (domain_dir / "README.md").exists():
        bad.append("%s: no README.md — every domain says in prose what is hand-authored "
                   "here and what is generated" % name)

    coverage_path = domain_dir / "coverage.json"
    declared = {}
    if not coverage_path.exists():
        bad.append("%s: no coverage.json — a reading pass declares the range it read" % name)
    else:
        cov = load(coverage_path)
        for i, dec in enumerate(cov.get("declarations") or []):
            unit = dec.get("unit")
            if unit not in COVERAGE_UNITS:
                bad.append("%s coverage %d: unit %r is outside %s"
                           % (name, i, unit, list(COVERAGE_UNITS)))
                continue
            if not dec.get("ticket"):
                bad.append("%s coverage %d: a declaration with no ticket" % (name, i))
            for item in dec.get("items") or []:
                declared[coverage_key(unit, item)] = dec.get("ticket") or "?"

        # …and the same declaration in the other shape. See the block above
        # coverage_images() for why this file is read rather than rewritten.
        for image, ticket in coverage_images(cov):
            fid = image.get("familysearch_id")
            if not fid:
                bad.append("%s coverage: an image with no familysearch_id — the id is "
                           "how a declaration names what it declares" % name)
                continue
            state = image.get("read_state")
            if not state:
                bad.append("%s coverage %s: an image with no read_state, so nothing "
                           "can tell an inventoried sheet from a read one"
                           % (name, fid))
                continue
            page_file = image.get("page_file")
            if state == INVENTORIED_ONLY:
                counts["inventoried"] += 1
                if page_file:
                    bad.append("%s coverage %s: read_state is %r and it names the page "
                               "file %s — an inventoried sheet has nothing read off it"
                               % (name, fid, INVENTORIED_ONLY, page_file))
                continue
            declared[coverage_key("image", fid)] = ticket
            if not page_file:
                bad.append("%s coverage %s: read_state %r declares the image read and "
                           "it names no page_file" % (name, fid, state))
            elif not resolve_page_file(domain_dir, name, page_file).exists():
                bad.append("%s coverage %s: page_file %s is declared and is not "
                           "committed" % (name, fid, page_file))
    counts["declared"] = len(declared)

    reached = set()

    # A page file reaches the image it names, and that is the third thing that can
    # reach a coverage item — `records/` and `claims/` are the other two. It is what
    # turns a declared-read image with no reading behind it into a hole instead of a
    # silence.
    for path in sorted((domain_dir / "pages").glob("*.json")) if (domain_dir / "pages").exists() else []:
        doc = load(path)
        fid = doc.get("familysearch_id")
        if not fid:
            # A PAGE READ OFF A LEAF THE DEPOSIT DOES NOT HOLD (T-0912). census_1840's
            # coverage is the 74-image FamilySearch deposit, and printed page 232's
            # continuation is not in it — that absence is a finding of its own
            # (continuation_search_page_232.json exhausted all 74 looking for it). The
            # leaf was read off the Internet Archive's scan of NARA M704 roll 57
            # instead. Such a page names no familysearch_id because it has none, and
            # inventing one would be a false coverage claim. What it must still do is
            # name WHAT IT READ: a `source_record` that is a real record in
            # data/sources/. It reaches no coverage item, and that is correct — it
            # declares nothing about the deposit.
            sid = doc.get("source_record")
            if not sid:
                bad.append("%s/pages/%s: names neither a familysearch_id nor a "
                           "source_record, so nothing says what it read"
                           % (name, path.name))
            elif known_sources and sid not in known_sources:
                bad.append("%s/pages/%s: names source_record %r, which is not a "
                           "source record" % (name, path.name, sid))
            continue
        reached.add(coverage_key("image", fid))

    # A DOMAIN-OWNED FILE REACHES A COVERAGE ITEM TOO (T-0678). `records/` and `claims/`
    # are this registry's own shape, and two domains do not use it: old_settlers reads
    # into `people.json` and `death_notices.json` at the top of its directory, under the
    # gates of `tools/old_settlers.py` and `tools/read_fergus_obits.py`. Reading only the
    # two subdirectories reported both of its declared lists as coverage HOLES — a
    # declaration nothing reaches — when in fact 1,084 units reach them, so registering
    # the domain would have meant either a false red or moving two generated files out
    # from under the tools that own them.
    #
    # WHAT THIS IS NOT: it is not "declared, therefore read". A file reaches an item only
    # by NAMING it — as its own `source_id`, or on a unit's `source`/`source_id` — and
    # only if it carries at least one named unit. A declaration with nothing behind it is
    # still a hole, which is the whole point of the file.
    for key, name_ in coverage_reached_by_a_domain_file(domain_dir, bad):
        reached.add(key)

    for path in sorted((domain_dir / "records").glob("*.json")) if (domain_dir / "records").exists() else []:
        doc = load(path)
        label = "%s/records/%s" % (name, path.name)
        sid = doc.get("source_id")
        if not sid:
            bad.append("%s: names no source_id" % label)
        elif known_sources and sid not in known_sources:
            bad.append("%s: cites source id %r, which names no source record" % (label, sid))
        seen = set()
        for row in doc.get("records") or []:
            counts["records"] += 1
            rid = row.get("id")
            where = "%s %s" % (label, rid or "<no id>")
            for field in RECORD_FIELDS:
                if field not in row:
                    bad.append("%s: a record with no %s" % (where, field))
            if rid in seen:
                bad.append("%s: duplicate record id" % where)
            seen.add(rid)
            if row.get("reading") not in READINGS:
                bad.append("%s: reading %r is outside %s"
                           % (where, row.get("reading"), list(READINGS)))
            if row.get("confidence") not in CONFIDENCES:
                bad.append("%s: confidence %r is outside %s"
                           % (where, row.get("confidence"), list(CONFIDENCES)))
            reached.update(locator_reached(row.get("locator") or {}))
            # THE VERBATIM GATE REACHES A ROW TOO, WHEN THE ROW ASKS FOR IT (T-0961).
            # `as_read` is a CELL — a name lifted out of one column of a printed table —
            # so it cannot be rebuilt out of a line of text and is not held to it. But a
            # row transcribed out of a text this repository COMMITS can carry the whole
            # printed line beside its cells, and then the same check the claims get is
            # available for the asking: `verbatim` is rebuilt at the row's own locator and
            # must match byte for byte. It is opt-in ON PURPOSE and not required, because
            # the domains whose rows come off a SCAN — a census sheet, a parish register —
            # have no committed text to rebuild from and never will; requiring the field
            # would either fail them or teach them to fake it. A row that offers the field
            # is asking to be checked, and this is the check.
            if "verbatim" in row:
                rebuilt, err = rebuild_quote(domain_dir, row.get("locator") or {})
                if err:
                    bad.append("%s: carries a verbatim and its locator %s" % (where, err))
                elif rebuilt != row["verbatim"]:
                    bad.append("%s: the verbatim is not what the committed text says at "
                               "that locator" % where)

    for path in sorted((domain_dir / "claims").glob("*.json")) if (domain_dir / "claims").exists() else []:
        doc = load(path)
        label = "%s/claims/%s" % (name, path.name)
        sid = doc.get("source_id")
        if not sid:
            bad.append("%s: names no source_id" % label)
        elif known_sources and sid not in known_sources:
            bad.append("%s: cites source id %r, which names no source record" % (label, sid))
        seen = set()
        for claim in doc.get("claims") or []:
            counts["claims"] += 1
            cid = claim.get("id")
            where = "%s %s" % (label, cid or "<no id>")
            for field in CLAIM_FIELDS:
                if field not in claim:
                    bad.append("%s: a claim with no %s" % (where, field))
            if cid in seen:
                bad.append("%s: duplicate claim id" % where)
            seen.add(cid)
            if claim.get("kind") not in KINDS:
                bad.append("%s: kind %r is outside the closed vocabulary %s"
                           % (where, claim.get("kind"), list(KINDS)))
            if claim.get("reading") not in READINGS:
                bad.append("%s: reading %r is outside %s"
                           % (where, claim.get("reading"), list(READINGS)))
            if not isinstance(claim.get("town_finding"), bool):
                bad.append("%s: town_finding is not a boolean" % where)
            locator = claim.get("locator") or {}
            reached.update(locator_reached(locator))
            # The verbatim gate, and it binds the two domains whose text this repo
            # commits. A tidied quote is invisible to every other check here.
            if spec["holds"] == "claims":
                rebuilt, err = rebuild_quote(domain_dir, locator)
                if err:
                    bad.append("%s: %s" % (where, err))
                elif rebuilt != claim.get("quote"):
                    bad.append("%s: the quote is not what the committed text says at "
                               "that locator" % where)

    for key, ticket in sorted(declared.items()):
        if key not in reached:
            bad.append("%s: coverage hole — %s is declared read by %s and nothing in "
                       "the domain reaches it" % (name, key, ticket))
    return counts


def build(research: Path = RESEARCH, sources: Path = SOURCES, quiet: bool = False) -> int:
    """Write the scaffold. Idempotent, and it never overwrites a hand-authored file."""
    for name, spec in DOMAINS.items():
        d = research / name
        d.mkdir(parents=True, exist_ok=True)
        if not spec.get("managed", True):
            continue
        (d / "records").mkdir(parents=True, exist_ok=True)
        (d / "claims").mkdir(parents=True, exist_ok=True)
        (d / "text").mkdir(parents=True, exist_ok=True)
        for sub in ("records", "claims", "text"):
            keep = d / sub / ".gitkeep"
            if not keep.exists():
                keep.write_text("", encoding="utf-8")
        cov = d / "coverage.json"
        if not cov.exists():
            dump(cov, {
                "schema": SCHEMA_VERSION,
                "domain": name,
                "generated_by": "hand — a reading pass declares the range it read, and "
                                "the gate checks it",
                "note": "An UNDECLARED item is not read yet and is not a fault. A "
                        "DECLARED item nothing reaches is a hole, and that is what "
                        "this file is for.",
                "declarations": [],
            })
        cross = d / "crosswalk.json"
        if not cross.exists():
            dump(cross, {
                "schema": SCHEMA_VERSION,
                "domain": name,
                "note": "The ONLY place two differently-spelled names in this domain may "
                        "become one person, in data/research/newspapers/identity.json's "
                        "shape and under its rules: a merge needs a rule, the rule names "
                        "BOTH spellings verbatim, and a surname-only merge is always a "
                        "refusal. A refusal is declared as explicitly as a merge — the "
                        "absence of one reads like a pair nobody has looked at yet.",
                "passes": [],
                "merges": [],
                "refusals": [],
            })
    manifest = {
        "schema": SCHEMA_VERSION,
        "_doc": "GENERATED by tools/research_domains.py --build. Every committed "
                "research domain, its reading-unit patterns and stable unit-id rule. "
                "Hand-edit and the gate says so.",
        "generated_by": "tools/research_domains.py --build",
        "kinds": list(KINDS),
        "readings": list(READINGS),
        "confidences": list(CONFIDENCES),
        "coverage_units": list(COVERAGE_UNITS),
        "record_fields": list(RECORD_FIELDS),
        "claim_fields": list(CLAIM_FIELDS),
        "domains": [
            {"id": name, "title": spec["title"], "holds": spec["holds"], "what": spec["what"],
             "path": "data/research/%s/" % name,
             "legacy_measure": spec.get("legacy_measure", True),
             "ledger_units": spec["ledger_units"]}
            for name, spec in DOMAINS.items()
        ],
    }
    dump(research / "domains.json", manifest)
    if not quiet:
        print("research domains: %d scaffolded, manifest written" % len(DOMAINS))
    return 0


def check(research: Path = RESEARCH, sources: Path = SOURCES, quiet: bool = False) -> list:
    bad = []
    known = source_ids(sources)
    totals = {"records": 0, "claims": 0, "declared": 0, "inventoried": 0}
    for name, spec in DOMAINS.items():
        if not spec.get("managed", True):
            if not (research / name).is_dir():
                bad.append("%s: the registered research domain has no directory" % name)
            continue
        counts = check_domain(name, spec, research, known, bad)
        for k in totals:
            totals[k] += counts[k]
        cross = research / name / "crosswalk.json"
        if not cross.exists():
            bad.append("%s: no crosswalk.json — the identity layer is declared before "
                       "it is needed, not after" % name)
        else:
            check_crosswalk(load(cross), "%s/crosswalk.json" % name, bad)

    manifest_path = research / "domains.json"
    if not manifest_path.exists():
        bad.append("data/research/domains.json is missing — run --build")
    else:
        want = json.loads(json.dumps({
            "schema": SCHEMA_VERSION,
            "kinds": list(KINDS), "readings": list(READINGS),
            "confidences": list(CONFIDENCES), "coverage_units": list(COVERAGE_UNITS),
            "record_fields": list(RECORD_FIELDS), "claim_fields": list(CLAIM_FIELDS),
            "domains": [{"id": n, "title": s["title"], "holds": s["holds"],
                         "what": s["what"], "path": "data/research/%s/" % n,
                         "legacy_measure": s.get("legacy_measure", True),
                         "ledger_units": s["ledger_units"]}
                        for n, s in DOMAINS.items()],
        }))
        got = load(manifest_path)
        if {k: got.get(k) for k in want} != want:
            bad.append("data/research/domains.json is stale or hand-edited; "
                       "regenerate it with --build")

    if not quiet:
        for b in bad:
            print("  FAIL  " + b)
        print("  %d domain(s); %d record(s), %d claim(s), %d declared coverage "
              "item(s), %d inventoried and not asserted read"
              % (len(DOMAINS), totals["records"], totals["claims"],
                 totals["declared"], totals["inventoried"]))
    return bad


# --------------------------------------------------------------------------- #
# The self-test. Every assertion above is broken on a synthetic tree and must be
# reported; an assertion that has quietly stopped firing is worse than no
# assertion, because the file it guards looks checked.
# --------------------------------------------------------------------------- #

FIXTURE_TEXT = "the town was then a mere hamlet\nand the river ran black with mud\n"

FIXTURE_CLAIM = {
    "id": "c001",
    "kind": "landscape",
    "reading": "transcription_mediated",
    "quote": "the town was then a mere hamlet",
    "normalized": "The town was then a mere hamlet.",
    "locator": {"text_file": "fixture.txt", "lines": [1, 1], "page": 7},
    "describes_date": "1835",
    "entities": [],
    "town_finding": True,
    "notes": "fixture",
}

FIXTURE_RECORD = {
    "id": "r001",
    "as_read": "Jno. Kinzie",
    "normalized": "John Kinzie",
    "locator": {"list": "poll_1835", "line": 12},
    "reading": "scan_verified",
    "confidence": "documented",
    "notes": "fixture",
}


FIXTURE_PAGE = {
    "schema": 1,
    "familysearch_id": "33S7-FIXT-A",
    "image": "chicago/reference/census1840/33S7-FIXT-A.jpg",
    "printed_page": 229,
    "sheet_side": "left",
    "division": "Chicago",
    "reading": "scan_verified",
    "lines": [],
}


def _fixture(tmp: Path) -> Path:
    """A minimal but GREEN tree: one records domain, one claims domain, both covered."""
    research = tmp / "research"
    build(research=research, sources=tmp / "sources", quiet=True)
    # The six READMEs are hand-authored — --build deliberately does not write one,
    # because a stub that says nothing is worse than a missing page the gate names.
    for name in DOMAINS:
        (research / name / "README.md").write_text("fixture\n", encoding="utf-8")
    (tmp / "sources").mkdir(parents=True, exist_ok=True)
    dump(tmp / "sources" / "fixture_source.json", {"id": "fixture_source"})

    civic = research / "civic"
    dump(civic / "records" / "poll_1835.json", {
        "schema": 1, "domain": "civic", "source_id": "fixture_source",
        "records": [copy.deepcopy(FIXTURE_RECORD)],
    })
    dump(civic / "coverage.json", {
        "schema": 1, "domain": "civic", "generated_by": "fixture",
        "declarations": [{"unit": "list", "items": ["poll_1835"], "ticket": "T-9999"}],
    })

    books = research / "books"
    (books / "text").mkdir(parents=True, exist_ok=True)
    (books / "text" / "fixture.txt").write_text(FIXTURE_TEXT, encoding="utf-8")
    dump(books / "claims" / "fixture.json", {
        "schema": 1, "domain": "books", "source_id": "fixture_source",
        "claims": [copy.deepcopy(FIXTURE_CLAIM)],
    })
    dump(books / "coverage.json", {
        "schema": 1, "domain": "books", "generated_by": "fixture",
        "declarations": [{"unit": "page", "items": [7], "ticket": "T-9999"}],
    })

    # The third shape in the tree, because it is a third shape the gate has to hold:
    # one image read and reached by its page file, one inventoried and asserted only
    # to have been looked at. Both states have to be here or the case that tells them
    # apart has nothing to break.
    census = research / "census_1840"
    dump(census / "pages" / "33S7-FIXT-A.json", copy.deepcopy(FIXTURE_PAGE))
    dump(census / "coverage.json", {
        "schema": 2, "domain": "census_1840", "generated_by": "fixture",
        "groups": [{
            "range": "images 1-2 of 2",
            "declared_by": "T-9999. One sheet read to the line, one inventoried only.",
            "images": [
                {"index": 1, "familysearch_id": "33S7-FIXT-A",
                 "file": "chicago/reference/census1840/33S7-FIXT-A.jpg",
                 "sheet_side": "left", "printed_page": 229,
                 "lines_with_an_entry": 2, "what_it_is": "fixture",
                 "read_state": "names_and_cells_transcribed",
                 "page_file": "data/research/census_1840/pages/33S7-FIXT-A.json"},
                {"index": 2, "familysearch_id": "33S7-FIXT-B",
                 "file": "chicago/reference/census1840/33S7-FIXT-B.jpg",
                 "sheet_side": "right", "printed_page": None,
                 "lines_with_an_entry": 0, "what_it_is": "fixture",
                 "read_state": INVENTORIED_ONLY, "page_file": None},
            ],
        }],
    })
    # The fourth shape (T-0678): a domain whose reading lives in a file at the top of its
    # own directory, under a declared `units_in`, and whose crosswalk rules a printed name
    # against the town rather than a spelling against a spelling. Both are in the tree
    # because both are now things this gate has to hold.
    old_settlers = research / "old_settlers"
    dump(old_settlers / "roll.json", {
        "schema": 1, "domain": "old_settlers", "source_id": "fixture_source",
        "units_in": "people",
        "people": [{"id": "os001", "as_read": "Adams, William H.",
                    "normalized": "William H. Adams"}],
    })
    dump(old_settlers / "coverage.json", {
        "schema": 1, "domain": "old_settlers", "generated_by": "fixture",
        "declarations": [{"unit": "list", "items": ["fixture_source"], "ticket": "T-9999"}],
    })
    dump(old_settlers / "crosswalk.json", {
        "schema": 1, "domain": "old_settlers",
        "rules": {"OS1": "surname equal and both sides spell the forename out"},
        "merges": [{"id": "os001", "as_read": "Adams, William H.",
                    "resident_name": "William Hanford Adams", "person_id": "adams_william_h",
                    "rule": "OS1", "evidence": "surname and spelled-out forename agree"}],
        "refusals": [{"id": "os002", "as_read": "Arnold, Isaac N.", "rule": "OS1",
                      "outcome": "refused", "why": "no bearer of the surname in the layer"}],
    })
    return research


def self_test() -> int:
    failures = []
    cases = 0

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        research = _fixture(tmp)
        bad = check(research=research, sources=tmp / "sources", quiet=True)
        if bad:
            print("FAIL: the green fixture is not green: %r" % bad, file=sys.stderr)
            return 1

    def run(mutate, want, label):
        nonlocal cases
        cases += 1
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            research = _fixture(tmp)
            mutate(research, tmp)
            bad = check(research=research, sources=tmp / "sources", quiet=True)
        if not any(want in b for b in bad):
            failures.append("%s: expected a failure mentioning %r, got %r"
                            % (label, want, bad))
        else:
            print("  fires: %s" % label)

    def edit(path: Path, fn):
        doc = load(path)
        fn(doc)
        dump(path, doc)

    # 1. an unknown kind
    run(lambda r, t: edit(r / "books/claims/fixture.json",
                          lambda d: d["claims"][0].update(kind="atmosphere")),
        "outside the closed vocabulary", "a claim kind outside the closed vocabulary")

    # 2. a missing reading — on both shapes, because both require it
    run(lambda r, t: edit(r / "books/claims/fixture.json",
                          lambda d: d["claims"][0].pop("reading")),
        "a claim with no reading", "a claim with no reading grade")
    run(lambda r, t: edit(r / "civic/records/poll_1835.json",
                          lambda d: d["records"][0].pop("reading")),
        "a record with no reading", "a record with no reading grade")
    run(lambda r, t: edit(r / "civic/records/poll_1835.json",
                          lambda d: d["records"][0].update(reading="eyeballed")),
        "is outside", "a reading grade outside the two")

    # 3. a quote that differs by one character
    run(lambda r, t: edit(r / "books/claims/fixture.json",
                          lambda d: d["claims"][0].update(quote="the town was then a mere hamlets")),
        "not what the committed text says", "a quote that differs by one character")
    run(lambda r, t: edit(r / "books/claims/fixture.json",
                          lambda d: d["claims"][0]["locator"].update(text_file="nope.txt")),
        "which is not committed", "a quote citing text this repo does not hold")

    # 3b. THE SAME GATE ON A ROW THAT ASKED FOR IT (T-0961). A record carrying a
    # `verbatim` is held to the committed text exactly as a claim's quote is; a record
    # without one is not, and the third case is what proves the opt-in is really opt-in
    # rather than a check that happens to be off.
    def _row_with_verbatim(research, verbatim=FIXTURE_TEXT.splitlines()[0], **over):
        row = copy.deepcopy(FIXTURE_RECORD)
        row.update({
            "verbatim": verbatim,
            "locator": {"text_file": "fixture.txt", "lines": [1, 1], "page": 7},
        })
        row.update(over)
        dump(research / "books" / "records" / "fixture_rows.json", {
            "schema": 1, "domain": "books", "source_id": "fixture_source",
            "records": [row],
        })

    run(lambda r, t: _row_with_verbatim(r, verbatim="the town was then a mere hamlets"),
        "the verbatim is not what the committed text says",
        "a record verbatim that differs by one character")
    run(lambda r, t: _row_with_verbatim(
            r, locator={"text_file": "nope.txt", "lines": [1, 1], "page": 7}),
        "which is not committed", "a record verbatim citing text this repo does not hold")
    if True:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            research = _fixture(tmp)
            row = copy.deepcopy(FIXTURE_RECORD)
            row["locator"] = {"text_file": "fixture.txt", "lines": [1, 1], "page": 7}
            dump(research / "books" / "records" / "fixture_rows.json", {
                "schema": 1, "domain": "books", "source_id": "fixture_source",
                "records": [row],
            })
            cases += 1
            bad = check(research=research, sources=tmp / "sources", quiet=True)
            if any("verbatim" in b for b in bad):
                failures.append("a record with NO verbatim was held to the text anyway: %r"
                                % bad)
            else:
                print("  fires: a record with no verbatim is not held to the committed text")

    # 4. a coverage hole
    run(lambda r, t: edit(r / "books/coverage.json",
                          lambda d: d["declarations"][0]["items"].append(8)),
        "coverage hole", "a declared page nothing reaches")
    run(lambda r, t: edit(r / "civic/coverage.json",
                          lambda d: d["declarations"][0].update(unit="parish")),
        "is outside", "a coverage unit outside the vocabulary")

    # 4b. the same hole, in the images[] shape — T-0536. An image declared READ that
    # no pages/ file reaches, an inventoried one dressed up as read, and the two
    # pointers a declaration can break.
    def _images(d):
        return d["groups"][0]["images"]

    run(lambda r, t: edit(r / "census_1840/pages/33S7-FIXT-A.json",
                          lambda d: d.update(familysearch_id="33S7-FIXT-Z")),
        "coverage hole", "a census image declared read that no pages/ file reaches")
    run(lambda r, t: edit(r / "census_1840/coverage.json",
                          lambda d: _images(d)[1].update(
                              page_file="data/research/census_1840/pages/33S7-FIXT-A.json")),
        "an inventoried sheet has nothing read off it",
        "an inventoried image that names a page file")
    run(lambda r, t: edit(r / "census_1840/coverage.json",
                          lambda d: _images(d)[0].update(page_file=None)),
        "names no page_file", "an image declared read that names no page file")
    run(lambda r, t: (r / "census_1840/pages/33S7-FIXT-A.json").unlink(),
        "is declared and is not committed",
        "an image whose declared page file is not committed")
    run(lambda r, t: edit(r / "census_1840/coverage.json",
                          lambda d: _images(d)[0].pop("read_state")),
        "no read_state", "an image the gate cannot grade")

    # 4c. an off-deposit page — one read off a leaf the deposit does not hold — still
    # has to say what it read. T-0912.
    run(lambda r, t: edit(r / "census_1840/pages/33S7-FIXT-A.json",
                          lambda d: d.pop("familysearch_id")),
        "names neither a familysearch_id nor a source_record",
        "an off-deposit page that names no source either")
    run(lambda r, t: edit(r / "census_1840/pages/33S7-FIXT-A.json",
                          lambda d: (d.pop("familysearch_id"),
                                     d.update(source_record="no_such_source"))),
        "which is not a source record",
        "an off-deposit page naming a source record that does not exist")

    # 5. a merge with no rule, and a rule that does not read back
    run(lambda r, t: edit(r / "civic/crosswalk.json",
                          lambda d: d["merges"].append(
                              {"into": "John Kinzie", "from": "Jno. Kinzie",
                               "evidence": ["fixture_source"]})),
        "a merge with no rule", "a merge with no rule")
    run(lambda r, t: edit(r / "civic/crosswalk.json",
                          lambda d: d["merges"].append(
                              {"into": "John Kinzie", "from": "Jno. Kinzie",
                               "rule": "the poll book and the roll are one man",
                               "evidence": ["fixture_source"]})),
        "does not name both spellings verbatim", "a merge rule that does not read back")

    # 6. a refusal naming only one spelling
    run(lambda r, t: edit(r / "civic/crosswalk.json",
                          lambda d: d["refusals"].append(
                              {"a": "John Kinzie", "rule": "two families",
                               "evidence": ["fixture_source"]})),
        "a refusal naming only one spelling", "a refusal naming only one spelling")

    # 7. a surname-only merge — refused however good the rule is
    run(lambda r, t: edit(r / "civic/crosswalk.json",
                          lambda d: d["merges"].append(
                              {"into": "Kinzie", "from": "Jno. Kinzie",
                               "rule": "Kinzie and Jno. Kinzie stand at the same entry",
                               "evidence": ["fixture_source"]})),
        "surname-only merge is always a refusal", "a surname-only merge")

    # 8. a claim citing a source id that does not resolve
    run(lambda r, t: edit(r / "books/claims/fixture.json",
                          lambda d: d.update(source_id="no_such_source")),
        "names no source record", "a claim file citing a source id that does not resolve")
    run(lambda r, t: edit(r / "civic/records/poll_1835.json",
                          lambda d: d.update(source_id="no_such_source")),
        "names no source record", "a records file citing a source id that does not resolve")

    # …and the structural half: the scaffold itself, and the manifest.
    run(lambda r, t: (r / "church" / "README.md").unlink(),
        "no README.md", "a domain that has lost its README")
    run(lambda r, t: (r / "church" / "crosswalk.json").unlink(),
        "no crosswalk.json", "a domain with no identity layer")
    run(lambda r, t: (r / "church" / "coverage.json").unlink(),
        "no coverage.json", "a domain that declares no coverage")
    run(lambda r, t: edit(r / "domains.json", lambda d: d["kinds"].append("atmosphere")),
        "stale or hand-edited", "a hand-edited manifest")
    run(lambda r, t: edit(r / "civic/records/poll_1835.json",
                          lambda d: d["records"].append(copy.deepcopy(FIXTURE_RECORD))),
        "duplicate record id", "two rows under one id")
    run(lambda r, t: edit(r / "books/claims/fixture.json",
                          lambda d: d["claims"][0].update(town_finding="yes")),
        "town_finding is not a boolean", "a town_finding that is not a boolean")

    if failures:
        for f in failures:
            print("FAIL: " + f, file=sys.stderr)
        return 1
    # --- T-0678: the two accommodations that let old_settlers be registered ------------
    run(lambda r, t: edit(r / "old_settlers" / "roll.json",
                          lambda d: d.__setitem__("units_in", "peeple")),
        "declares units_in", "a units_in naming an array the file does not hold")
    run(lambda r, t: edit(r / "old_settlers" / "roll.json",
                          lambda d: d.__setitem__("people", [])),
        "coverage hole", "a declared list whose only reading has emptied out")
    run(lambda r, t: edit(r / "old_settlers" / "crosswalk.json",
                          lambda d: d["merges"][0].pop("resident_name")),
        "fewer than two spellings", "a roster merge naming only the printed spelling")
    run(lambda r, t: edit(r / "old_settlers" / "crosswalk.json",
                          lambda d: d["merges"][0].__setitem__("rule", "OS9")),
        "the file's rules block does not declare", "a roster merge citing an undeclared rule")
    run(lambda r, t: edit(r / "old_settlers" / "crosswalk.json",
                          lambda d: d["merges"][0].__setitem__("as_read", "Adams")),
        "surname-only merge", "a roster merge on a bare surname")
    run(lambda r, t: edit(r / "old_settlers" / "crosswalk.json",
                          lambda d: d["merges"][0].pop("evidence")),
        "with no evidence", "a roster merge with nothing behind it")
    run(lambda r, t: edit(r / "old_settlers" / "crosswalk.json",
                          lambda d: d["merges"][0].pop("person_id")),
        "naming no person in the town", "a roster merge that reaches nobody")
    run(lambda r, t: edit(r / "old_settlers" / "crosswalk.json",
                          lambda d: d["refusals"][0].__setitem__("why", "  ")),
        "refusal with no reason", "a roster refusal that does not say why")
    # …and the roster shape does not let the pairwise shape off: civic has no rules block,
    # so its merges are still held to into/from and the verbatim rule.
    run(lambda r, t: edit(r / "civic" / "crosswalk.json",
                          lambda d: d.__setitem__("merges", [{"into": "A. Smith"}])),
        "fewer than two spellings", "a pairwise merge is still a pairwise merge")

    print("SELF-TEST PASS — every research-domain assertion fires when broken "
          "(%d cases)" % cases)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.build:
        return build()
    if args.check:
        bad = check()
        if bad:
            print("RESEARCH DOMAINS FAIL — %d problem(s)" % len(bad))
            return 1
        print("OK: the %d domains hold their shape" % len(DOMAINS))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
