#!/usr/bin/env python3
"""Build and validate the closed, unit-level research-spend ledger (T-1143)."""
from __future__ import annotations

import copy
import gzip
import json
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "research" / "domains.json"
LEDGER = ROOT / "data" / "research" / "research_spend_ledger.json.gz"
REPORT = ROOT / "docs" / "RESEARCH" / "research-spend-ledger-2026-09-15.md"
RULINGS = ROOT / "data" / "research" / "spend_rulings.json"
AS_OF = "2026-09-15"

DISPOSITIONS = (
    "asserted", "later_only", "outside_chicago", "aggregate_only", "refused", "unresolved",
)
OPEN_TICKET_STATES = {"open", "claimed", "review", "in-progress", "split_live"}
STRUCTURED_CONFIDENCE = {"attested", "inferred", "documented"}
NAME_FIELDS = ("normalized", "as_read", "quote")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_ledger(path: Path = LEDGER):
    try:
        return json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def write_ledger(path: Path, doc) -> None:
    """Write deterministic compressed JSON; the Markdown report is the review surface."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))


def pointer_part(value) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def resolve_pointer(doc, pointer: str):
    if pointer == "":
        return doc
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise KeyError(pointer)
    node = doc
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            node = node[int(key)]
        elif isinstance(node, dict):
            node = node[key]
        else:
            raise KeyError(pointer)
    return node


def ticket_states(root: Path = ROOT) -> dict[str, str]:
    """Ticket id -> state, with one derived state: `split_live` (T-1237).

    A `split` parent is a terminal state in the ticket tool — the children take its
    place in the queue and carry its work — so read flatly it looks exactly like a
    ticket that FINISHED. That difference is load-bearing here, because the only thing
    this state is asked is whether an unresolved research unit is still deferred to live
    work. When T-1147 was split into five pieces, 748 units across the book, directory
    and letter-list claims were suddenly reading as deferred to a closed ticket, and the
    gate said so; none of them had changed, and the work they wait on had not stopped.

    So a `split` parent reports `split_live` while at least one of its children is
    itself open, and plain `split` once every child has closed. The invariant is
    unchanged and is the strict one: a unit may only defer to work that is still going
    to happen. What changes is that re-filing work no longer reads as finishing it.
    """
    states, parents = {}, {}
    for path in sorted((root / "tickets").glob("T-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        tid = re.search(r"(?m)^id:\s*(T-\d+)\s*$", text)
        state = re.search(r"(?m)^state:\s*([^\s#]+)", text)
        parent = re.search(r"(?m)^parent:\s*(T-\d+)\s*$", text)
        if tid and state:
            states[tid.group(1)] = state.group(1)
            if parent:
                parents[tid.group(1)] = parent.group(1)
    # AND LIVENESS CLIMBS A CHAIN, NOT ONE STEP (T-1421). A split piece may itself be
    # split — T-1188 was cut into T-1410 and T-1411, and T-1411 into T-1421 and T-1422 —
    # and read one level deep the grandparent went back to plain `split` the moment its
    # last direct child stopped being `open`, so twelve units that had not moved read as
    # deferred to finished work and the sign-off went NO-GO on C3. The work had not
    # stopped; it had been cut finer. So the pass runs to a fixed point and a `split_live`
    # parent is itself live for ITS parent. The invariant is untouched and still strict:
    # a unit may only defer to work that is still going to happen, and a chain every one
    # of whose leaves has closed still reports plain `split`.
    alive = {"open", "claimed", "review", "in-progress", "split_live"}
    while True:
        promoted = False
        for child, parent in parents.items():
            if states.get(child) in alive and states.get(parent) == "split":
                states[parent] = "split_live"
                promoted = True
        if not promoted:
            return states


def declared_containers(doc: dict) -> list[str]:
    out = ["records", "claims"]
    if isinstance(doc.get("units_in"), str) and doc["units_in"].strip():
        out.append(doc["units_in"].strip())
    return out


def raw_identifier(row: dict, source_pointer: str) -> str:
    for key in ("id", "person_id", "record_id", "claim_id", "familysearch_id"):
        if row.get(key) is not None:
            return str(row[key])
    return source_pointer


# A LEDGER KEY HAS TO BE UNIQUE ACROSS THE CORPUS, AND A CLAIM ID IS NOT (T-1338).
# `target_index` is one dictionary over every reading unit in the project, and until this
# ticket its key was the row's own `source_record_id`. For a person id or a land-sale
# certificate that is a name the whole corpus agrees on. For a newspaper claim it is
# `c004` -- a POSITION in the extraction of ONE issue, which 55 issue files each print --
# so a resident card naming `c004` was read as naming every one of them. It was not a
# hazard waiting to happen: 145 units were closed `asserted` on it the day this ticket
# was taken, off three cards that had each cited exactly one claim. `hh_taylor_c`'s
# arrival cites `chicago_democrat_1835_08_19#c007` and closed 74; `hh_dole_george_w`'s
# reason_for_coming cites `chicago_democrat_1834_04_01#c013` and `chicago_democrat_
# 1835_07_01#c015` and closed 71 between them, one of which was not even a newspaper.
# A ledger that overstates its own spend is wrong in the direction it must never be wrong
# in, and the 128 press units this ticket's parent left cannot be spent one at a time
# until a bound can name ONE claim.
#
# The key is therefore the source file's stem and the row's id, joined by `#` -- the form
# the cards' own prose had been writing all along. Which containers need it is DECLARED in
# domains.json rather than guessed, because the two cases are genuinely different and no
# shape tells them apart: `residents` people ids repeat across the pass cohorts and mean
# the same man each time, and `newspapers` claim ids repeat and mean nothing outside their
# own file. `record_id_scope_faults` below refuses an undeclared repeat, so the next corpus
# that reuses an id has to say which kind it is instead of quietly joining the first case.
def record_key(source_file: str, raw_id: str, file_local: bool) -> str:
    """The unit's key in the target index: file-qualified where the id is file-local."""
    if not file_local:
        return raw_id
    return f"{Path(source_file).stem}#{raw_id}"


def extract_units(root: Path, registry: dict) -> tuple[list[dict], list[str]]:
    """Return every registered reading unit and every registry fault.

    A file pattern owns rows only through its declared containers. The stable id is
    the row's explicit id where one exists and otherwise its file-relative JSON
    pointer — the rule recorded beside the pattern in domains.json.
    """
    research = root / "data" / "research"
    entries = registry.get("domains") or []
    faults = []
    units = []
    known = {Path(entry.get("path", "")).name for entry in entries}
    present = {p.name for p in research.iterdir() if p.is_dir()}
    for name in sorted(present - known):
        faults.append(f"unregistered research domain: data/research/{name}/")
    for name in sorted(known - present):
        faults.append(f"registered research domain has no directory: data/research/{name}/")

    seen_sources = set()
    for entry in entries:
        domain = entry.get("id")
        domain_dir = root / entry.get("path", "")
        patterns = entry.get("ledger_units")
        if not domain or not isinstance(patterns, list) or not patterns:
            faults.append(f"{domain or '<unnamed>'}: no ledger unit patterns")
            continue
        for pattern in patterns:
            glob = pattern.get("glob")
            containers = pattern.get("containers")
            if not isinstance(glob, str) or not glob:
                faults.append(f"{domain}: ledger pattern has no glob")
                continue
            paths = sorted(p for p in domain_dir.glob(glob) if p.is_file())
            if not paths:
                faults.append(f"{domain}: ledger pattern {glob!r} matches no file")
            for path in paths:
                doc = read_json(path)
                rel = path.relative_to(root).as_posix()
                if not isinstance(doc, dict):
                    faults.append(f"{rel}: registered research file is not a JSON object")
                    continue
                if containers == "$declared" and (
                        "crosswalk" in path.name or doc.get("not_a_reading")):
                    continue
                file_local = pattern.get("file_local_containers")
                if file_local is None:
                    file_local = []
                if not isinstance(file_local, list) or not all(
                        isinstance(c, str) for c in file_local):
                    faults.append(
                        f"{domain} {glob}: file_local_containers must be a list of container names")
                    file_local = []
                use = declared_containers(doc) if containers == "$declared" else containers
                if not isinstance(use, list) or not all(isinstance(c, str) for c in use):
                    faults.append(f"{domain} {glob}: containers must be a list or $declared")
                    continue
                for container in use:
                    rows = doc.get(container)
                    if rows is None:
                        continue
                    if not isinstance(rows, list):
                        faults.append(f"{rel}#/{container}: registered unit container is not a list")
                        continue
                    for index, row in enumerate(rows):
                        pointer = f"/{pointer_part(container)}/{index}"
                        if not isinstance(row, dict):
                            faults.append(f"{rel}#{pointer}: research row is not an object")
                            continue
                        name_fields = pattern.get("name_fields")
                        if isinstance(name_fields, list) and not any(row.get(k) for k in name_fields):
                            continue
                        raw_id = raw_identifier(row, pointer)
                        key = f"{domain}:{rel}#{container}/{pointer_part(raw_id)}"
                        source_key = (rel, pointer)
                        if source_key in seen_sources:
                            faults.append(f"{rel}#{pointer}: row matched more than one ledger pattern")
                            continue
                        seen_sources.add(source_key)
                        source_ids = []
                        for candidate in (doc.get("source_id"), doc.get("source_record"),
                                          row.get("source_id")):
                            if isinstance(candidate, str) and candidate:
                                source_ids.append(candidate)
                        for value in (doc.get("source_ids"), row.get("sources")):
                            if isinstance(value, list):
                                source_ids.extend(v for v in value if isinstance(v, str) and v)
                        units.append({
                            "unit_id": key,
                            "domain": domain,
                            "source_file": rel,
                            "source_pointer": pointer,
                            "source_record_id": raw_id,
                            "record_key": record_key(rel, raw_id, container in file_local),
                            "file_local_id": container in file_local,
                            "source_ids": sorted(set(source_ids)),
                            "record": row,
                        })
    units.sort(key=lambda u: u["unit_id"])
    return units, faults


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from strings(value)


# T-1144 acceptance 9 writes `present_on_scene_date.last_dated_appearance`: the date the
# corpus last saw a person, DERIVED from evidence the card already holds. Its own note
# says what it is -- "THE FIELD IS THE EVIDENCE UNDER THE VERDICT, not a new claim".
#
# It must not be read as one here. The leg carries the person's own id in `person`, and
# names ids in its prose, so the block ABOVE it -- `present_on_scene_date`, which does
# carry a confidence and sources -- starts matching unit ids it never named before. 190
# readings flipped to `asserted` against `/present_on_scene_date` the day the leg landed,
# among them an enrichment naming a July 1833 arrival and a Connecticut origin. Neither
# an arrival nor an origin is anywhere in that block: what changed was that a derived
# restatement of the evidence mentioned the man by id.
#
# A reading is spent when a field carries WHAT IT SAYS, not when a summary of the same
# evidence repeats the subject's name. The leg contributes no name tokens.
TOKEN_BLIND_KEYS = {"last_dated_appearance"}


def naming_strings(node):
    """`strings`, minus the subtrees that restate evidence rather than assert a fact."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in TOKEN_BLIND_KEYS:
                continue
            yield from naming_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from naming_strings(value)


def cited_sources(node) -> set[str]:
    found = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "sources" and isinstance(value, list):
                found.update(v for v in value if isinstance(v, str))
            else:
                found.update(cited_sources(value))
    elif isinstance(node, list):
        for value in node:
            found.update(cited_sources(value))
    return found


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

# `#` JOINS THE TWO HALVES OF A FILE-QUALIFIED KEY AND IS NOT A WORD CHARACTER, so the
# token pattern has to reach across it or a card naming `chicago_democrat_1835_08_19#c007`
# would be read as naming the file and the bare claim and never the pair. Both readings are
# kept: the joined token is offered whole AND split, so nothing a global id used to match
# stops matching. What changed is on the other side -- a file-local raw id is no longer a
# key at all, so the bare `c007` half now finds nothing to join.
UNIT_TOKEN = re.compile(r"[A-Za-z0-9_.:#-]+")


# T-1508. THE BUSINESS LAYER IS A TARGET SURFACE, and until this it was not. The ledger
# indexed the residents layer alone, so a reading whose whole content is an enterprise --
# a firm style, a partner, a trade kept at a named house -- had nowhere to land even after
# T-1310 BUILT the layer out of those very readings. 485 units stood `unresolved` behind a
# routing ticket while the record compiled from them cited them by claim id.
#
# It is indexed on a STRICTER rule than the residents walk below uses, and deliberately.
# There the match is a token found anywhere in a confident block's prose, which is why
# TOKEN_BLIND_KEYS had to be invented when a derived restatement started matching ids it
# never asserted. A business block does not need the loose reading: it carries the claims
# it was compiled from in its own `claim_ids` list, so the claim is either named there or
# it is not reached. Nothing is inferred from prose.
#
# The two layers state the same thing in two vocabularies -- a resident block says
# `confidence` and cites `sources`, a business block says `tier` and cites `source_id` --
# and `field_confidence` and `field_sources` are where that translation lives, so a reader
# downstream sees one kind of assertion.
BUSINESS_LAYER = ("data", "businesses")
BUSINESS_INDEX_FILES = {"index.json"}


def field_confidence(field) -> str | None:
    """What a structured block claims for itself, under either layer's word for it."""
    if not isinstance(field, dict):
        return None
    for key in ("confidence", "tier"):
        value = field.get(key)
        if isinstance(value, str):
            return value
    return None


def field_sources(field) -> set[str]:
    """`cited_sources`, plus the single `source_id` a business block names instead."""
    found = cited_sources(field)
    if isinstance(field, dict):
        value = field.get("source_id")
        if isinstance(value, str) and value:
            found.add(value)
    return found


def business_target_index(root: Path, keys: set[str]) -> dict[str, list[dict]]:
    """Index the business layer's tiered, source-bearing blocks by the claims they name."""
    found = defaultdict(list)
    base = root.joinpath(*BUSINESS_LAYER)
    if not base.is_dir():
        return found

    def walk(node, parts, root_id, rel):
        if isinstance(node, dict):
            claims = node.get("claim_ids")
            if isinstance(claims, list) and field_confidence(node) in STRUCTURED_CONFIDENCE:
                sources_here = field_sources(node)
                if sources_here:
                    for claim in claims:
                        if isinstance(claim, str) and claim in keys:
                            found[claim].append({
                                "kind": "business_record",
                                "id": root_id,
                                "file": rel,
                                "field_path": "".join("/" + pointer_part(p) for p in parts),
                                "sources": sorted(sources_here),
                            })
            for key, value in node.items():
                walk(value, parts + [key], root_id, rel)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, parts + [index], root_id, rel)

    for path in sorted(base.rglob("*.json")):
        if path.name in BUSINESS_INDEX_FILES:
            continue
        doc = read_json(path)
        if not isinstance(doc, dict) or not doc.get("id"):
            continue
        walk(doc, [], str(doc["id"]), path.relative_to(root).as_posix())
    return found


def target_index(root: Path, keys: set[str]) -> dict[str, list[dict]]:
    """Index source-bearing structured assertions by the unit keys they name.

    The residents layer first, then the business layer, so a reading a resident card
    already carries keeps the target it had and a reading only the business layer carries
    reaches the block that carries it (T-1508).
    """
    found = defaultdict(list)

    def walk(node, parts, root_id, rel):
        if isinstance(node, dict):
            confidence = node.get("confidence")
            sources_here = cited_sources(node) if confidence in STRUCTURED_CONFIDENCE else set()
            if sources_here:
                tokens = set()
                for value in naming_strings(node):
                    if value in keys:
                        tokens.add(value)
                    for token in UNIT_TOKEN.findall(value):
                        if token in keys:
                            tokens.add(token)
                        tokens.update(part for part in token.split("#") if part in keys)
                for key in tokens:
                    found[key].append({
                        "kind": "resident_record",
                        "id": root_id,
                        "file": rel,
                        "field_path": "".join("/" + pointer_part(p) for p in parts),
                        "sources": sorted(sources_here),
                    })
            for key, value in node.items():
                walk(value, parts + [key], root_id, rel)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, parts + [index], root_id, rel)

    for path in town_records((root / "data" / "residents")):
        doc = read_json(path)
        if not isinstance(doc, dict) or not doc.get("id"):
            continue
        walk(doc, [], str(doc["id"]), path.relative_to(root).as_posix())
    for key, rows in business_target_index(root, keys).items():
        found[key].extend(rows)
    return found


def year_in(row: dict) -> int | None:
    for key in ("describes_date", "event_date", "date", "year"):
        value = row.get(key)
        if isinstance(value, (str, int)):
            match = re.search(r"\b(17\d\d|18\d\d|19\d\d)\b", str(value))
            if match:
                return int(match.group(1))
    return None


def resident_finding(root: Path, unit: dict) -> dict | None:
    name = Path(unit["source_file"]).name
    match = re.match(r"pass_(\d\d)_.*_cohort\.json$", name)
    if not match:
        return None
    path = root / "data" / "research" / "residents" / f"pass_{match.group(1)}_findings.json"
    doc = read_json(path)
    if not isinstance(doc, dict):
        return None
    person = unit["source_record_id"]
    overrides = doc.get("overrides") or {}
    finding = copy.deepcopy(overrides.get(person) or {}) if isinstance(overrides, dict) else {}
    completed = doc.get("completed_person_ids")
    # Passes 2-4 predate the completed array but their whole fixed cohort was reviewed;
    # an absent override is the file's declared default no-find.
    finding["completed"] = (person in completed) if isinstance(completed, list) else True
    finding["default_summary"] = doc.get("default_summary") or "The completed pass recorded no new defensible fact."
    return finding


# T-1232 SPLIT T-1146 AND THIS FILE HELD ITS NAME IN FOUR PLACES. The ledger refuses an
# unresolved unit whose owner is not an OPEN ticket, which is the rule that makes "owned"
# mean something — so the moment the parent went to `split` the gate went red on 61 units
# it had been perfectly happy with the hour before. That is the rule working. The owner of
# an unasserted PERSON unit is now T-1234, which is the piece of the parent that still has
# this corpus to spend: T-1232 read the 94 matched resident-research blocks and T-1234 has
# the book claims, the Newberry index units and the letter-list name suspicions.
# T-1236 WAS SPLIT, AND AN OWNER MUST BE AN OPEN TICKET. The epic owned 3,384 unasserted
# units by default, and the owner's bound capped it at three children BY WEIGHT rather than
# nine by corpus. The moment the parent went to `split` every one of those units named a
# ticket in a state this gate refuses — the same rule that went red on 61 units when T-1146
# was split, working exactly as intended. The default owner is therefore routed by domain to
# the piece that actually has that corpus to spend.
EPIC_PIECES = {
    "land_sales": ("T-1296", "The land-sale ruling piece owns this unasserted unit."),
    # THE CIVIC POINTER WAS AIMED AT DONE WORK, and nothing noticed because nothing reached
    # it: T-1297 closed, and zero units cited it on the day T-1342 was taken. The one that
    # can reach it now is a civic CLAIM and not a name on a roll at all — Andreas on how the
    # town got its water by cart from the foot of Randolph Street — and it was being read as
    # an assertion about George W. Dole's reason for coming, because its id is `c013` and so
    # is the Democrat claim that card cites. It was owned with the press claims by T-1343,
    # which was the ticket that could reach it.
    # AND T-1343 HAS SPENT ITS CORPUS, so the pointer moves again rather than going quiet
    # with the ticket. It cannot simply fall to the default below: `spend_remainder_rulings`
    # rules four domains and refuses civic by name, and dropping this entry hands it 24
    # civic claims it will not rule. What the one unit that reaches it actually says is that
    # the town bought its water from a CART TRADE — "private enterprise reaped a comfortable
    # little financial harvest in the operation of water carts", five to ten cents the
    # barrel, according to competition — which is an in-window trade this project holds no
    # business record for, and raising one for exactly that is T-1182's acceptance in its
    # own words. It is the same routing `PLACE_AND_ENTERPRISE` gives an enterprise claim one
    # comment below, reached from the civic corpus instead of the press.
    "civic": ("T-1468", "The business layer's convergence owns this unasserted civic claim: "
                        "a trade the town ran that no business record carries."
                        " T-1182 WAS SPLIT on 2026-09-19 into T-1401..T-1405 and all five are DONE, so the pointer moves again rather than going quiet with the ticket. T-1190 since 2026-09-20 (owner's call): the business layer's convergence is what is left to reconcile a trade or a premises against the layer once the audit is spent."
                        " AND T-1190 IS SPENT SINCE 2026-09-20, its three pieces T-1440, T-1441 and T-1442 all closed; the pointer moves once more, to T-1468, which owns the reconciliation itself rather than the convergence that has now finished."),
    "census_1830": ("T-1297", "The name-on-a-roll piece owns this unasserted unit."),
    "directories": ("T-1297", "The name-on-a-roll piece owns this unasserted unit."),
}

# T-1241 ENDED T-1147, AND THE SAME ROUTING RULE APPLIES A THIRD TIME. The place and
# enterprise completion pass was split into five pieces; T-1237, T-1238 and T-1239 ran and
# T-1240 was withdrawn, so the pass has spent what it could spend. What it left behind is
# 748 newspaper, book, directory, civic and church units that describe a business, a
# building, a street or a piece of infrastructure and reach no structured target — not
# because nobody has looked at them, but because THE LAYER THAT WOULD RECEIVE THEM IS NOT
# BUILT YET. There is no authored business record to carry an enterprise claim (T-1180) and
# no seat on the ground to carry a place claim (T-1198).
#
# Leaving them pointed at T-1147 made the last open child of that parent load-bearing: close
# T-1241 and the parent falls out of `split_live`, and 748 units that had not changed would
# suddenly be deferred to finished work. T-1241's own file records that, and records the
# cost of the alternative — "those 748 units repointed at whatever absorbs it". This is that
# repointing, and it is the routing EPIC_PIECES already does one comment above: the owner of
# an unasserted unit is the piece that still has THAT corpus to spend. Here the corpus
# divides by what the unit describes rather than by which domain read it, because an
# enterprise claim and a place claim are absorbed by different bands.
PLACE_AND_ENTERPRISE = {
    # WAS T-1180 UNTIL T-1311 CLOSED ON 2026-09-18.
    # That ticket split into T-1310 (the business record layer) and T-1311 (the structure-function vocabulary), and with the second of the two done the parent is spent work a unit cannot defer to (T-1237).
    # T-1310 BUILT the layer -- 196 firms with a tier on every field -- so what is left for these notices is not building it but reconciling them against it, which is T-1182's field: audit every attested and inferred business against the research, its proprietors, partners, dates and premises.
    #
    "business": ("T-1468", "The business layer's convergence owns this unasserted "
                           "enterprise claim."
                           " T-1182 WAS SPLIT on 2026-09-19 into T-1401..T-1405 and all five are DONE, so the pointer moves again rather than going quiet with the ticket. T-1190 since 2026-09-20 (owner's call): the business layer's convergence is what is left to reconcile a trade or a premises against the layer once the audit is spent."
                        " AND T-1190 IS SPENT SINCE 2026-09-20, its three pieces T-1440, T-1441 and T-1442 all closed; the pointer moves once more, to T-1468, which owns the reconciliation itself rather than the convergence that has now finished."),
    # T-1509, 2026-09-21: T-1468's last live child closed and BOTH ROUTES ABOVE ARE NOW
    # UNREACHED. The `business` half was spent into the newspapers and books registers by
    # tools/spend_remainder_rulings.py; the one civic reading left is ruled in the
    # hand-authored register, because what took it was the YARD layer (a water cart),
    # which this ledger does not index as a target surface. A unit arriving here tomorrow
    # would name a ticket that is `split` and not live, and the gate would say so on the
    # unit rather than on the pointer — so the next reading that lands here is a ticket
    # of its own, not a rename.
    "building": ("T-1198", "The seating pass owns this unasserted place claim."),
    "street": ("T-1198", "The seating pass owns this unasserted place claim."),
    "infrastructure": ("T-1198", "The seating pass owns this unasserted place claim."),
}


def natural_disposition(root: Path, unit: dict, targets: dict[str, list[dict]]) -> dict:
    row = unit["record"]
    domain = unit["domain"]
    source = f"{unit['source_file']}#{unit['source_pointer']}"

    if domain == "residents":
        name = Path(unit["source_file"]).name
        if name == "scene_window_trade_audit.json":
            # T-1229 emptied this file: the six standing rows became dated pre-scene
            # roles and the audit's population is zero, so nothing classifies here today.
            # The pointer moves off T-1145 because that ticket was SPLIT and a split
            # parent is not an open state — a row arriving tomorrow would have cited a
            # ticket this gate cannot resolve, and said so in a message about a dead
            # pointer rather than about the trade. T-1254 is the open successor that
            # owns what is left of the role migration.
            return {"disposition": "unresolved", "ticket": "T-1254",
                    "reason": "The dated plural-role migration owns this temporal role ruling."}
        if name == "letter_list_reading_suspicions.json":
            return {"disposition": "unresolved", "ticket": "T-1298",
                    "reason": "The remainder piece of the epic owns this surviving name suspicion."}
        finding = resident_finding(root, unit)
        if finding:
            outcome = str(finding.get("outcome") or "no_corroboration")
            if outcome.startswith("no_") or outcome in {"refused", "not_found"}:
                return {"disposition": "refused", "rule": outcome,
                        "evidence": finding.get("summary") or finding["default_summary"]}
            if not finding.get("completed"):
                return {"disposition": "unresolved", "ticket": "T-1298",
                        "reason": "The resident research pass has not completed this reserved person."}
        # The pilot is a reservation without a committed findings file; positive
        # pass findings that have no exact structured target also remain owned here.
        candidates = targets.get(unit["record_key"], [])
        for target in candidates:
            if not unit["source_ids"] or set(unit["source_ids"]) & set(target["sources"]):
                target = {k: v for k, v in target.items() if k != "sources"}
                return {"disposition": "asserted", "target": target}
        return {"disposition": "unresolved", "ticket": "T-1298",
                "reason": "No exact source-bearing structured resident field is named yet."}

    if domain == "newberry_index":
        return {"disposition": "refused", "rule": "finding_aid_only",
                "evidence": "A Newberry index card locates a genealogy; it does not attest an 1835 person fact."}
    if domain in {"census_1840", "old_settlers"}:
        return {"disposition": "later_only",
                "reason": "This domain is later evidence and cannot by itself assert an 1835 fact."}
    if row.get("superseded_by"):
        return {"disposition": "refused", "rule": "superseded_reading",
                "evidence": str(row["superseded_by"])}
    if row.get("kind") == "turned_line":
        return {"disposition": "refused", "rule": "continuation_not_subject",
                "evidence": "The printed continuation belongs to the preceding entry and names no new subject."}
    if row.get("outside_chicago") is True or row.get("at_chicago") is False:
        return {"disposition": "outside_chicago", "reason": f"The source row explicitly marks the finding outside Chicago ({source})."}
    year = year_in(row)
    if year is not None and year > 1835:
        return {"disposition": "later_only",
                "reason": f"The unit describes {year}, later than the 1835 scene date."}
    if row.get("town_finding") is False:
        return {"disposition": "aggregate_only",
                "reason": "The committed reading explicitly says it is not a town finding."}

    for target in targets.get(unit["record_key"], []):
        if not unit["source_ids"] or set(unit["source_ids"]) & set(target["sources"]):
            target = {k: v for k, v in target.items() if k != "sources"}
            return {"disposition": "asserted", "target": target}

    kind = row.get("kind")
    if kind in PLACE_AND_ENTERPRISE:
        owner, reason = PLACE_AND_ENTERPRISE[kind]
        return {"disposition": "unresolved", "ticket": owner, "reason": reason}
    owner, reason = EPIC_PIECES.get(
        domain, ("T-1298", "The remainder piece of the epic owns this unasserted unit."))
    return {"disposition": "unresolved", "ticket": owner, "reason": reason}


# T-1234 GAVE THE LEDGER A PLACE TO WRITE A RULING DOWN. Every disposition above is derived
# from what a reading already says about itself — its date, its `superseded_by`, its
# domain. A unit whose reading says nothing self-classifying had exactly one outcome
# available, `unresolved`, and the only way to close it was to write code that guessed. So
# 3,471 person units sat owned by a ticket whose title covered 87 of them.
# data/research/spend_rulings.json is the written alternative: a named rule with a stated
# reason, and a note on every single unit it closes. It is consulted ONLY where the
# derivation ends in `unresolved`, so a ruling can never overturn an assertion, a
# later_only or a refusal the reading itself carries — the readings stay in charge.
RULING_DISPOSITIONS = {"refused", "later_only", "outside_chicago", "aggregate_only", "unresolved",
                       "asserted"}

# AN UNRESOLVED UNIT NAMES A TICKET *OR* THE EVIDENCE IT IS WAITING FOR (T-1423).
# The ledger's ownership invariant — only an open ticket may own an unresolved unit — was
# built for a unit that is waiting on WORK, and it is right about that. It was also the
# only shape available, so units waiting on EVIDENCE had to borrow it, and the borrowing
# has a five-rename history written into tools/spend_name_on_a_roll_rulings.py: the roster
# hand-off ran T-1159 -> T-1172 -> T-1179 -> T-1394 -> T-1423 and the arrival hand-off ran
# T-1169 -> T-1318 -> T-1329, each rename forced by this same gate going red the moment the
# named ticket closed. Nothing was learned by any of them. Worse, one of them fired inside
# `rederive.mjs --run`, which the PR lap runs on every pass: "the lap stopped pushing and
# three PRs sat dirty with no gate able to run on them".
#
# The 266 units of the five rules below ask a question no ticket can answer — whether a name
# the research READ and the town WITHHELD, since re-admitted at the reconstructed tier, was
# in the town on 1 July 1835. Only a document can answer that, and none is in hand. This
# file already says what such a pointer is worth: "'wait for somebody to decide' is not a
# disposition, it is a deferral wearing one." So an unresolved ruling may instead state
# `awaiting_evidence` — the document that would reopen the unit — and name NO ticket. The
# unit stays `unresolved`, because it is; what goes away is the false claim that somebody
# is working on it. Exactly one of the two, never both, and a wait that states no evidence
# is the deferral this rule exists to refuse.
AWAITING_MIN = 40


def unresolved_owner_faults(where: str, row: dict) -> list[str]:
    """One owner, and a wait has to say what it is waiting for."""
    ticket = str(row.get("ticket") or "").strip()
    awaiting = str(row.get("awaiting_evidence") or "").strip()
    if ticket and awaiting:
        return [f"{where}: names a ticket AND the evidence it awaits — a unit has one owner"]
    if ticket:
        return []
    if not awaiting:
        return [f"{where}: hands the unit on and names neither a ticket nor the evidence it awaits"]
    if len(awaiting) < AWAITING_MIN:
        return [f"{where}: awaits evidence it does not state — a bare wait is a deferral wearing a disposition"]
    return []

# A RULING MAY SAY `asserted`, AND IT IS THE ONLY DISPOSITION THAT MUST PROVE ITSELF (T-1330).
# The derivation above closes a unit as `asserted` on one test: a source-bearing structured
# field on a resident card NAMES the unit's record id AND cites a source the unit itself
# lists. That test cannot see the spend this project most wants to make -- a finding that
# brings a NEW volume and writes what it says onto the card -- because the new volume is by
# definition not among the sources the reading already carried. Nine of T-1330's thirty
# enrichments are exactly that: Peck's Providence birth out of the Chicago History Museum's
# encyclopedia, Hugunin's 17 August 1833 arrival out of the Old Settlers proceedings, each
# replacing a value the arrival stage had DRAWN from a distribution. Left to the derivation
# they read `unresolved` for ever, and the register's only way to close them would be to call
# a written assertion `refused`, which would understate the spend in the one direction a
# ledger must never be wrong in.
#
# So a ruling may assert, and a ruling that asserts must NAME THE FIELD: `wrote` on the
# ruling row, a LIST of `{"file": <path under data/residents/>, "field": <key>}` because a
# finding can fill two of them at once. The checks below are
# the whole of the licence -- the file exists, the field is there, it is `attested`,
# `inferred` or `documented`, it cites at least one source, and it names the unit's own
# record id. A row that cannot show all five is a fault and not an assertion, which keeps
# `asserted` something a register has to earn rather than something it can declare.
# THE RULING'S PROOF NAMES THE SAME KEY THE DERIVATION DOES (T-1338). `record_id` here is
# the unit's `record_key`, so a ruling that asserts a file-local unit has to show the
# FILE-QUALIFIED id on the card. A bare `c004` proved nothing about which issue was read.
def asserted_ruling_faults(root: Path, unit_id: str, record_id: str, row: dict) -> list[str]:
    wrote = row.get("wrote")
    where = f"a ruling asserts {unit_id} and"
    if not isinstance(wrote, list) or not wrote:
        return [f"{where} names no field it was written into"]
    faults = []
    for named in wrote:
        if not isinstance(named, dict) or not named.get("file") or not named.get("field"):
            faults.append(f"{where} one of the fields it names is not a file and a key")
            continue
        path = root / str(named["file"])
        if not path.exists():
            faults.append(f"{where} names {named['file']}, which is not a file")
            continue
        doc = read_json(path)
        block = doc.get(str(named["field"])) if isinstance(doc, dict) else None
        at = f"{named['file']}#{named['field']}"
        if not isinstance(block, dict):
            faults.append(f"{where} names {at}, which carries no block")
            continue
        if field_confidence(block) not in STRUCTURED_CONFIDENCE:
            faults.append(f"{where} {at} is not attested, inferred or documented")
        if not field_sources(block):
            faults.append(f"{where} {at} cites no source")
        if record_id not in json.dumps(block, ensure_ascii=False):
            faults.append(f"{where} {at} does not say {record_id}")
    return faults



# AN UNDECLARED REPEAT IS THE DEFECT, NOT THE REPEAT (T-1338). Two corpora reuse a row id
# across their own files and they mean opposite things by it: a `residents` pass cohort
# names the same man in four passes, and a `newspapers` issue numbers its claims from
# `c001` with no reference to any other issue. Nothing in the id tells them apart -- both
# are short strings printed more than once -- so the file that registers the corpus has to
# say which it is. The absence of a declaration used to read exactly like the global case
# and was silently taken as one, which is how 145 assertions were made off a claim number.
# A corpus whose ids repeat and which says nothing is therefore a fault here, in the shape
# the rest of this project already uses for a judgement nobody has recorded.
def record_id_scope_faults(units: list[dict], registry: dict) -> list[str]:
    """Refuse a container whose ids repeat across files and which declares neither scope."""
    files_by_raw = defaultdict(set)
    for unit in units:
        files_by_raw[unit["source_record_id"]].add(unit["source_file"])
    repeated = {raw for raw, files in files_by_raw.items() if len(files) > 1}
    seen = defaultdict(set)
    for unit in units:
        if unit["source_record_id"] in repeated:
            container = unit["unit_id"].split("#", 1)[1].rsplit("/", 1)[0]
            seen[(unit["domain"], container)].add(unit["source_record_id"])
    declared = {}
    for entry in registry.get("domains") or []:
        domain = entry.get("id")
        for pattern in entry.get("ledger_units") or []:
            for key, scope in (("file_local_containers", "file_local"),
                               ("global_containers", "global")):
                for container in pattern.get(key) or []:
                    declared[(domain, container)] = scope
    faults = []
    for (domain, container), ids in sorted(seen.items()):
        if (domain, container) not in declared:
            faults.append(
                f"data/research/domains.json does not say whether {domain} {container} record "
                f"ids are file-local or global, and {len(ids)} of them are printed in more "
                f"than one file: declare file_local_containers or global_containers")
    for (domain, container), scope in sorted(declared.items()):
        if scope == "global" and (domain, container) not in seen:
            faults.append(
                f"data/research/domains.json declares {domain} {container} record ids global "
                f"because they repeat, and no id of theirs repeats any more")
    return faults


def ruling_registers(root: Path) -> list[Path]:
    """The hand-authored register first, then every derived one, in a stable order.

    T-1234 wrote one file and typed all 87 of its notes. T-1296 is 1,572 rows of a single
    land register, where typing the notes would make a WORSE register — they would drift,
    and nobody could prove a note matched the row it claims to rule. So a derived register
    (generated by a named tool, re-derived by its own `--check`) sits beside the corpus it
    rules, as `data/research/<domain>/spend_rulings.json`, and is read here on exactly the
    same terms: the same statement floor, the same note floor, the same coverage faults.
    The distinction is provenance, not authority. It lives INSIDE the domain rather than in
    a directory of its own because every directory under data/research/ is a reading
    corpus and extract_units refuses one that is not — a rule worth keeping.
    """
    return [root / RULINGS.relative_to(ROOT)] + sorted(
        (root / "data" / "research").glob("*/spend_rulings.json"))


def read_rulings(root: Path = ROOT) -> tuple[dict, list[str]]:
    """Load every ruling register, and every fault in them."""
    registers = ruling_registers(root)
    empty = {"rules": {}, "by_unit": {}}
    if not registers[0].exists():
        return empty, [f"{RULINGS.relative_to(ROOT)} is missing"]
    rules: dict = {}
    stated_in: dict[str, str] = {}
    by_unit: dict = {}
    ruled_in: dict[str, str] = {}
    faults: list[str] = []
    for path in registers:
        label = path.relative_to(root).as_posix()
        doc = read_json(path)
        if not isinstance(doc, dict):
            faults.append(f"{label} is unreadable")
            continue
        file_rules = doc.get("rules")
        if not isinstance(file_rules, dict) or not file_rules:
            faults.append(f"{label}: rules is missing or empty")
            continue
        for name, rule in sorted(file_rules.items()):
            where = f"{label} rule {name}"
            if not isinstance(rule, dict):
                faults.append(f"{where}: is not an object")
                continue
            if name in rules and rules[name] != rule:
                faults.append(
                    f"{where}: {stated_in[name]} states a DIFFERENT rule under this name — "
                    "one name must mean one thing across the registers")
                continue
            if rule.get("disposition") not in RULING_DISPOSITIONS:
                faults.append(f"{where}: disposition {rule.get('disposition')!r} is not one a ruling may reach")
            if len(str(rule.get("statement") or "").strip()) < 40:
                faults.append(f"{where}: states no rule — a ruling with no statement is a silent reclassification")
            if rule.get("disposition") == "unresolved":
                faults.extend(unresolved_owner_faults(where, rule))
            rules[name] = rule
            stated_in.setdefault(name, label)
        rows = doc.get("rulings")
        if not isinstance(rows, list):
            faults.append(f"{label}: rulings is not a list")
            continue
        for index, row in enumerate(rows):
            where = f"{label} ruling {index}"
            if not isinstance(row, dict):
                faults.append(f"{where}: is not an object")
                continue
            unit_id = row.get("unit")
            if not isinstance(unit_id, str) or not unit_id:
                faults.append(f"{where}: names no unit")
                continue
            where = f"{label} ruling on {unit_id}"
            if unit_id in by_unit:
                faults.append(f"{where}: two rulings on one unit (also in {ruled_in[unit_id]})")
                continue
            if row.get("rule") not in file_rules:
                faults.append(f"{where}: names rule {row.get('rule')!r}, which this file does not state")
                continue
            if len(str(row.get("note") or "").strip()) < 20:
                faults.append(f"{where}: carries no note — the rule alone never says why THIS unit fell under it")
                continue
            by_unit[unit_id] = row
            ruled_in[unit_id] = label
    if not rules:
        return empty, faults
    return {"rules": rules, "by_unit": by_unit}, faults


def ruling_coverage_faults(rulings: dict, known: set[str], fired: set[str]) -> list[str]:
    """A ruling must name a real unit and must be the thing that closed it.

    A ruling on a unit something else already closed reads as work done and is not, so it
    fails rather than sitting in the file looking spent.
    """
    faults = []
    ruled = set(rulings.get("by_unit") or {})
    for unit_id in sorted(ruled - known):
        faults.append(f"a ruling register rules on {unit_id}, which is not a registered reading unit")
    for unit_id in sorted((ruled & known) - fired):
        faults.append(f"a ruling register rules on {unit_id}, which was already closed without it")
    return faults


def classify(root: Path, unit: dict, targets: dict[str, list[dict]],
             rulings: dict, fired: set[str]) -> dict:
    """The reading's own disposition, and the written ruling where it leaves one open."""
    out = natural_disposition(root, unit, targets)
    if out.get("disposition") != "unresolved":
        return out
    ruling = rulings["by_unit"].get(unit["unit_id"])
    if not ruling:
        return out
    fired.add(unit["unit_id"])
    rule = rulings["rules"][ruling["rule"]]
    said = f"{rule['statement']} THIS UNIT: {ruling['note']}"
    row = {"disposition": rule["disposition"], "ruling": ruling["rule"]}
    if rule["disposition"] == "asserted":
        # The document's `target` is ONE field, in the shape `natural_disposition` builds,
        # so every reader downstream sees an assertion of the kind it already knows. The
        # whole list stays beside it: a finding that filled two fields says both, and
        # `asserted_ruling_faults` re-reads every one.
        wrote = [w for w in (ruling.get("wrote") or []) if isinstance(w, dict)]
        if wrote:
            first = wrote[0]
            row["target"] = {"kind": "resident_record",
                             "id": Path(str(first.get("file"))).stem,
                             "file": first.get("file"),
                             "field_path": "/" + pointer_part(str(first.get("field")))}
            row["wrote"] = wrote
        row["reason"] = said
    elif rule["disposition"] == "refused":
        row["rule"] = ruling["rule"]
        row["evidence"] = said
    elif rule["disposition"] == "unresolved":
        if str(rule.get("ticket") or "").strip():
            row["ticket"] = rule["ticket"]
        else:
            row["awaiting_evidence"] = rule["awaiting_evidence"]
        row["reason"] = said
    else:
        row["reason"] = said
    return row


def build_document(root: Path = ROOT) -> tuple[dict, list[str]]:
    registry = read_json(root / "data" / "research" / "domains.json")
    if not isinstance(registry, dict):
        return {}, ["data/research/domains.json is missing or unreadable"]
    units, faults = extract_units(root, registry)
    faults.extend(record_id_scope_faults(units, registry))
    targets = target_index(root, {unit["record_key"] for unit in units})
    rulings, ruling_faults = read_rulings(root)
    faults.extend(ruling_faults)
    known = {unit["unit_id"] for unit in units}
    fired = set()
    rows = []
    for unit in units:
        row = {k: unit[k] for k in (
            "unit_id", "domain", "source_file", "source_pointer", "source_record_id")}
        # Carried only where it differs from the raw id, so the document itself says which
        # readings are keyed file-locally and a reader can see the population at a glance.
        if unit["record_key"] != unit["source_record_id"]:
            row["record_key"] = unit["record_key"]
        row.update(classify(root, unit, targets, rulings, fired))
        if row.get("disposition") == "asserted" and row.get("ruling"):
            faults.extend(asserted_ruling_faults(
                root, unit["unit_id"], unit["record_key"],
                rulings["by_unit"][unit["unit_id"]]))
        rows.append(row)
    faults.extend(ruling_coverage_faults(rulings, known, fired))
    by_domain = defaultdict(Counter)
    for row in rows:
        by_domain[row["domain"]][row["disposition"]] += 1
    totals = Counter(row["disposition"] for row in rows)
    doc = {
        "schema": 1,
        "as_of": AS_OF,
        "generated_by": "tools/measure_research_spend.py --ledger-build",
        "dispositions": list(DISPOSITIONS),
        "unit_count": len(rows),
        "totals": {name: totals[name] for name in DISPOSITIONS},
        "domains": {
            domain: {name: counts[name] for name in DISPOSITIONS}
            for domain, counts in sorted(by_domain.items())
        },
        "units": rows,
    }
    return doc, faults


def validate_document(doc: dict, root: Path = ROOT,
                      states: dict[str, str] | None = None) -> list[str]:
    faults = []
    states = ticket_states(root) if states is None else states
    rows = doc.get("units") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return ["ledger has no units array"]
    seen = set()
    json_cache = {}

    def cached(relative):
        key = str(relative or "")
        if key not in json_cache:
            json_cache[key] = read_json(root / key)
        return json_cache[key]

    for index, row in enumerate(rows):
        where = f"ledger unit {index}"
        if not isinstance(row, dict):
            faults.append(f"{where}: is not an object")
            continue
        uid = row.get("unit_id")
        where = str(uid or where)
        if not uid:
            faults.append(f"{where}: has no stable unit_id")
        elif uid in seen:
            faults.append(f"{where}: duplicate unit_id")
        seen.add(uid)
        disposition = row.get("disposition")
        if disposition not in DISPOSITIONS:
            faults.append(f"{where}: unclassified disposition {disposition!r}")
            continue
        source_doc = cached(row.get("source_file"))
        if not isinstance(source_doc, dict):
            faults.append(f"{where}: source file is missing or unreadable: {row.get('source_file')}")
        else:
            try:
                resolve_pointer(source_doc, row.get("source_pointer"))
            except (KeyError, IndexError, TypeError, ValueError):
                faults.append(f"{where}: source pointer is dead: {row.get('source_pointer')}")
        if disposition == "asserted":
            target = row.get("target")
            if not isinstance(target, dict):
                faults.append(f"{where}: asserted row names no target")
                continue
            target_doc = cached(target.get("file"))
            if not isinstance(target_doc, dict) or target_doc.get("id") != target.get("id"):
                faults.append(f"{where}: asserted target is dead or its id does not agree")
                continue
            try:
                field = resolve_pointer(target_doc, target.get("field_path"))
            except (KeyError, IndexError, TypeError, ValueError):
                faults.append(f"{where}: asserted field_path is dead")
                continue
            if field_confidence(field) not in STRUCTURED_CONFIDENCE:
                faults.append(f"{where}: asserted fact exists only in prose or lacks attested/inferred confidence")
            if not field_sources(field):
                faults.append(f"{where}: asserted structured field names no source")
        elif disposition == "unresolved":
            owner_faults = unresolved_owner_faults(where, row)
            if owner_faults:
                faults.extend(owner_faults)
            elif not str(row.get("awaiting_evidence") or "").strip():
                ticket = row.get("ticket")
                if states.get(ticket) not in OPEN_TICKET_STATES:
                    faults.append(f"{where}: unresolved ticket {ticket!r} is missing or not open")
            if not str(row.get("reason") or "").strip():
                faults.append(f"{where}: unresolved row gives no reason")
        elif disposition == "refused":
            if not str(row.get("rule") or "").strip() or not str(row.get("evidence") or "").strip():
                faults.append(f"{where}: refusal must name both rule and evidence")
        elif not str(row.get("reason") or "").strip():
            faults.append(f"{where}: {disposition} row gives no reason")
    counts = Counter(row.get("disposition") for row in rows if isinstance(row, dict))
    if doc.get("unit_count") != len(rows):
        faults.append("ledger unit_count does not equal its rows")
    if doc.get("totals") != {name: counts[name] for name in DISPOSITIONS}:
        faults.append("ledger disposition totals do not equal its rows")
    return faults


def report_text(doc: dict, legacy_rows: list[dict]) -> str:
    before_read = sum(row["read"] for row in legacy_rows)
    before_spent = sum(row["spent"] for row in legacy_rows)
    before_unspent = sum(row["unspent"] for row in legacy_rows)
    reached = sum(row["reached"] for row in legacy_rows)
    wrote = sum(row["wrote"] for row in legacy_rows)
    unwritten = sum(row["unwritten"] for row in legacy_rows)
    unsourced = sum(row["unsourced"] for row in legacy_rows)
    out = [
        "# Closed research-spend ledger — 2026-09-15", "",
        "Generated by `tools/measure_research_spend.py --ledger-build`. The compressed JSON "
        "ledger is the machine-readable authority; this report is its review surface.", "",
        "## Before and after", "",
        "| Measure | Before T-1143 | Closed ledger |", "| --- | ---: | ---: |",
        f"| Research units in the legacy read/spent measure | {before_read:,} | {before_read:,} |",
        f"| Legacy spend rulings | {before_spent:,} | {before_spent:,} |",
        f"| Legacy units without a spend ruling | {before_unspent:,} | dispositioned below |",
        f"| All registered reading units | not closed | {doc['unit_count']:,} |",
        f"| Unclassified registered units | not measured | 0 |", "",
        "The historical read/spent comparison remains unchanged so new accounting cannot "
        "launder its backlog. The closed ledger adds the durable outcome for every registered "
        "unit, including newspapers, Genealogy Trails, and resident research passes.", "",
        "## Dispositions by domain", "",
        "| Domain | Asserted | Later only | Outside Chicago | Aggregate only | Refused | Unresolved | Total |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for domain, counts in doc["domains"].items():
        total = sum(counts.values())
        out.append(f"| {domain} | {counts['asserted']:,} | {counts['later_only']:,} | "
                   f"{counts['outside_chicago']:,} | {counts['aggregate_only']:,} | "
                   f"{counts['refused']:,} | {counts['unresolved']:,} | {total:,} |")
    totals = doc["totals"]
    out.append(f"| **Total** | **{totals['asserted']:,}** | **{totals['later_only']:,}** | "
               f"**{totals['outside_chicago']:,}** | **{totals['aggregate_only']:,}** | "
               f"**{totals['refused']:,}** | **{totals['unresolved']:,}** | "
               f"**{doc['unit_count']:,}** |")
    out += ["", "## Second-hop preservation", "",
            f"The pre-ledger resident-card measure is preserved: **{reached:,}** rulings reach "
            f"a town person, **{wrote:,}** are on a card, **{unwritten:,}** are unwritten, "
            f"and **{unsourced:,}** state no source.", "", "## Unresolved ownership", "",
            "An unresolved unit is waiting on WORK or on EVIDENCE, and it says which. Only "
            "tickets whose current state is open may own the first kind. The second names "
            "no ticket at all — no ticket can produce a document that is not in hand — and "
            "states instead what would reopen it (T-1423).", "",
            "| Ticket | Units |", "| --- | ---: |"]
    rows_unresolved = [row for row in doc["units"] if row["disposition"] == "unresolved"]
    owned = Counter(row["ticket"] for row in rows_unresolved if row.get("ticket"))
    for ticket, count in sorted(owned.items()):
        out.append(f"| {ticket} | {count:,} |")
    awaiting = Counter(row["awaiting_evidence"] for row in rows_unresolved
                       if row.get("awaiting_evidence"))
    out += ["", f"**{sum(awaiting.values()):,}** unit(s) wait on evidence rather than on a "
            "ticket, under " + f"{len(awaiting):,} stated reopening condition(s):", "",
            "| Units | Reopened by |", "| ---: | --- |"]
    for clause, count in sorted(awaiting.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"| {count:,} | {clause} |")
    out += ["", "Nonzero `later_only`, `outside_chicago`, `aggregate_only`, and `refused` "
            "counts are closed decisions, not missing work. The gate fails only when a unit "
            "is unclassified, an asserted target dies, an unresolved unit owned by a ticket "
            "has that ticket close or disappear, a unit waits on evidence it does not state, "
            "a unit claims both owners, or an assertion survives only as prose.", ""]
    return "\n".join(out)


def build(legacy_rows: list[dict], root: Path = ROOT) -> list[str]:
    doc, faults = build_document(root)
    faults.extend(validate_document(doc, root))
    if faults:
        return faults
    write_ledger(root / LEDGER.relative_to(ROOT), doc)
    report = root / REPORT.relative_to(ROOT)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(report_text(doc, legacy_rows), encoding="utf-8")
    return []


def check(legacy_rows: list[dict], root: Path = ROOT) -> list[str]:
    expected, faults = build_document(root)
    ledger = read_ledger(root / LEDGER.relative_to(ROOT))
    if not isinstance(ledger, dict):
        return faults + ["closed research-spend ledger is missing or unreadable"]
    faults.extend(validate_document(ledger, root))
    if ledger != expected:
        faults.append("closed research-spend ledger is stale — run --ledger-build")
    report = root / REPORT.relative_to(ROOT)
    if not report.exists() or report.read_text(encoding="utf-8") != report_text(expected, legacy_rows):
        faults.append("research-spend report is stale — run --ledger-build")
    return faults


AWAITING = {"good": "A document naming this person at Chicago on or about 1 July 1835."}


def self_test() -> int:
    """Mutate one green row in memory and prove each closure assertion fires."""
    failures = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "data/research/civic/records/fixture.json"
        target = root / "data/residents/hh_fixture.json"
        write_json(source, {"records": [{"id": "r1", "normalized": "One"}]})
        write_json(target, {"id": "hh_fixture", "facts": [{
            "value": "One", "confidence": "attested", "sources": ["fixture_source"]}]})
        base = {"unit_id": "civic:r1", "domain": "civic",
                "source_file": "data/research/civic/records/fixture.json",
                "source_pointer": "/records/0", "source_record_id": "r1",
                "disposition": "asserted", "target": {"kind": "resident_record",
                    "id": "hh_fixture", "file": "data/residents/hh_fixture.json",
                    "field_path": "/facts/0"}}

        def run(label, mutate, want, states=None):
            row = copy.deepcopy(base)
            mutate(row)
            doc = {"units": [row], "unit_count": 1,
                   "totals": {name: int(row.get("disposition") == name) for name in DISPOSITIONS}}
            got = validate_document(doc, root, states or {})
            if not any(want in fault for fault in got):
                failures.append(f"{label}: expected {want!r}, got {got!r}")
            else:
                print(f"  fires: {label}")

        run("an unclassified unit", lambda r: r.pop("disposition"), "unclassified")
        run("a dead asserted target", lambda r: r["target"].update(file="data/residents/nope.json"),
            "target is dead")
        run("an assertion left only in prose", lambda r: r["target"].update(field_path="/id"),
            "only in prose")
        run("an unresolved unit owned by a closed ticket",
            lambda r: (r.update(disposition="unresolved", ticket="T-1", reason="fixture"),
                       r.pop("target")), "missing or not open", {"T-1": "closed"})
        # T-1237. A SPLIT PARENT WHOSE CHILDREN HAVE ALL CLOSED IS CLOSED WORK, and a
        # unit deferred to it is stranded exactly as it would be behind a done ticket.
        run("an unresolved unit owned by a spent split parent",
            lambda r: (r.update(disposition="unresolved", ticket="T-1", reason="fixture"),
                       r.pop("target")), "missing or not open", {"T-1": "split"})
        # T-1423. The other kind of unresolved unit — waiting on a document, not on work.
        # It has to say what document, and it may not also claim a ticket is on it.
        run("an unresolved unit waiting on nothing it names",
            lambda r: (r.update(disposition="unresolved", reason="fixture"),
                       r.pop("target")), "names neither a ticket nor the evidence")
        run("an unresolved unit whose wait states no evidence",
            lambda r: (r.update(disposition="unresolved", reason="fixture",
                                awaiting_evidence="something, one day"),
                       r.pop("target")), "awaits evidence it does not state")
        run("an unresolved unit claiming both owners",
            lambda r: (r.update(disposition="unresolved", reason="fixture", ticket="T-1",
                                awaiting_evidence=AWAITING["good"]),
                       r.pop("target")), "a unit has one owner", {"T-1": "open"})
        # …and the honest shape passes, which is the half a mutation test cannot show.
        clean = copy.deepcopy(base)
        clean.update(disposition="unresolved", reason="fixture",
                     awaiting_evidence=AWAITING["good"])
        clean.pop("target")
        if validate_document({"units": [clean], "unit_count": 1,
                              "totals": {name: int(name == "unresolved")
                                         for name in DISPOSITIONS}}, root, {}):
            failures.append("a unit waiting on stated evidence should be green")
        else:
            print("  passes: a unit waiting on stated evidence, owned by no ticket")
        good = {"unit": "u1", "rule": "r", "note": "The row says so in its own last word."}
        rule = {"disposition": "refused",
                "statement": "A stated rule, long enough to be a sentence a reader can weigh."}

        def register(label, mutate, want):
            doc = {"rules": {"r": copy.deepcopy(rule)}, "rulings": [copy.deepcopy(good)]}
            mutate(doc)
            write_json(root / "data/research/spend_rulings.json", doc)
            got = read_rulings(root)[1]
            if not any(want in fault for fault in got):
                failures.append(f"{label}: expected {want!r}, got {got!r}")
            else:
                print(f"  fires: {label}")

        register("a rule that states nothing",
                 lambda d: d["rules"]["r"].update(statement="too short"), "states no rule")
        register("a ruling with no note",
                 lambda d: d["rulings"][0].update(note="x"), "carries no note")
        register("a ruling naming an unstated rule",
                 lambda d: d["rulings"][0].update(rule="nope"), "which this file does not state")
        register("a hand-off that names neither a ticket nor an evidence clause",
                 lambda d: d["rules"]["r"].update(disposition="unresolved"),
                 "names neither a ticket nor the evidence")
        register("a hand-off that waits on evidence it does not state",
                 lambda d: d["rules"]["r"].update(disposition="unresolved",
                                                  awaiting_evidence="later"),
                 "awaits evidence it does not state")
        register("a hand-off that claims a ticket and an evidence clause at once",
                 lambda d: d["rules"]["r"].update(disposition="unresolved", ticket="T-1",
                                                  awaiting_evidence=AWAITING["good"]),
                 "a unit has one owner")
        register("two rulings on one unit",
                 lambda d: d["rulings"].append(copy.deepcopy(good)), "two rulings on one unit")
        for label, args, want in (
                ("a ruling on a unit that does not exist", (set(), set()), "not a registered reading unit"),
                ("a ruling something else had already closed", ({"u1"}, set()), "already closed without it")):
            got = ruling_coverage_faults({"by_unit": {"u1": good}}, *args)
            if not any(want in fault for fault in got):
                failures.append(f"{label}: expected {want!r}, got {got!r}")
            else:
                print(f"  fires: {label}")

        # T-1421: LIVENESS CLIMBS THE WHOLE CHAIN. A split piece that is itself split
        # used to drop its grandparent back to plain `split`, and twelve unmoved units
        # read as deferred to finished work. Both directions are asserted here: a live
        # leaf lifts every split above it, and a chain whose leaves have all closed
        # still reports plain `split`.
        chain = root / "tickets"
        def ticket(tid, state, parent=None):
            body = f"---\nid: {tid}\nstate: {state}\n"
            body += f"parent: {parent}\n" if parent else "parent: null\n"
            chain.mkdir(parents=True, exist_ok=True)
            (chain / f"{tid}-fixture.md").write_text(body + "---\n", encoding="utf-8")
        ticket("T-9001", "split")
        ticket("T-9002", "split", "T-9001")
        ticket("T-9003", "open", "T-9002")
        states = ticket_states(root)
        if states.get("T-9001") != "split_live" or states.get("T-9002") != "split_live":
            failures.append("a live leaf did not lift the splits above it: %r" % states)
        else:
            print("  holds: a live leaf lifts every split above it")
        ticket("T-9003", "done", "T-9002")
        states = ticket_states(root)
        if states.get("T-9001") != "split" or states.get("T-9002") != "split":
            failures.append("a spent chain still reported itself live: %r" % states)
        else:
            print("  fires: a chain whose leaves have all closed reports plain split")
        for stale in chain.glob("T-90*-fixture.md"):
            stale.unlink()

        # T-1144 acceptance 9's presence leg restates evidence and names its own subject.
        # A block is a target when it carries WHAT THE READING SAYS; repeating the man's
        # id inside a derived summary is not that, and both halves are asserted here.
        write_json(root / "data/residents/hh_leg.json", {
            "id": "hh_leg",
            "present_on_scene_date": {
                "value": "uncertain", "confidence": "inferred",
                "sources": ["fixture_source"],
                "last_dated_appearance": {
                    "leg": "sighting", "person": "elam_tuller",
                    "note": "Read for elam_tuller, and nothing here moves the verdict."}},
            "origin": {"value": "Connecticut", "confidence": "attested",
                       "sources": ["fixture_source"], "from": "elam_tuller"}})
        index = target_index(root, {"elam_tuller"})
        paths = {t["field_path"] for t in index.get("elam_tuller", [])
                 if t["id"] == "hh_leg"}
        if "/present_on_scene_date" in paths:
            failures.append("the presence leg named its own subject into the target index")
        else:
            print("  fires: the presence leg names nobody into the target index")
        if "/origin" not in paths:
            failures.append("a field that does carry the reading stopped being a target")
        else:
            print("  holds: a field that carries the reading is still a target")

        # T-1508: THE BUSINESS LAYER AS A TARGET SURFACE, and the boundary it is read on.
        # The residents walk above matches a token found anywhere in a confident block,
        # which is the reading TOKEN_BLIND_KEYS had to be invented to narrow. A business
        # block is read on its own `claim_ids` list and on nothing else, so the three
        # cases that matter are: the claim is in the list and the block is tiered and
        # sourced (a target); the claim is in the block's prose only (not a target); the
        # claim is in the RECORD's top-level list, which carries no tier (not a target,
        # and the population T-1509 owns).
        write_json(root / "data/businesses/biz_fixture.json", {
            "id": "biz_fixture", "name": "Fixture & Co.",
            "claim_ids": ["gazette_1835_06_08#c101"],
            "proprietors": [{"name": "A. Fixture", "tier": "attested",
                             "source_id": "fixture_press",
                             "claim_ids": ["gazette_1835_06_08#c100"]}],
            "partners": [{"name": "B. Fixture", "tier": "attested",
                          "source_id": "fixture_press", "claim_ids": [],
                          "basis": "Printed over gazette_1835_06_08#c102."}]})
        biz = business_target_index(
            root, {"gazette_1835_06_08#c100", "gazette_1835_06_08#c101",
                   "gazette_1835_06_08#c102"})
        reached = {key: {t["field_path"] for t in rows} for key, rows in biz.items()}
        if reached.get("gazette_1835_06_08#c100") != {"/proprietors/0"}:
            failures.append(
                f"a tiered, sourced business block did not carry its own claim: {reached!r}")
        else:
            print("  holds: a business block naming the claim in its claim_ids is a target")
        if "gazette_1835_06_08#c101" in reached:
            failures.append("an untiered record-level claim_ids list stood as a target")
        else:
            print("  fires: a record's untiered claim_ids closes nothing (T-1509's population)")
        if "gazette_1835_06_08#c102" in reached:
            failures.append("a claim named only in a business block's prose stood as a target")
        else:
            print("  fires: a claim in a business block's prose alone is no target")
        block = {"tier": "inferred", "source_id": "fixture_press"}
        if field_confidence(block) != "inferred" or field_sources(block) != {"fixture_press"}:
            failures.append("the business vocabulary did not read as confidence and sources")
        else:
            print("  holds: `tier` and `source_id` read as confidence and a cited source")
        (root / "data/businesses/biz_fixture.json").unlink()

        # T-1342: THE FILE-LOCAL KEY, over the exact shape that made 142 false assertions —
        # two issue files each carrying a claim `c007`, and one card citing one of them.
        registry = {"domains": [{"id": "press", "path": "data/research/press/", "ledger_units": [
            {"glob": "extracted/*.json", "containers": ["claims"],
             "file_local_containers": ["claims"]}]}]}
        for issue in ("gazette_1835_06_08", "gazette_1835_08_19"):
            write_json(root / f"data/research/press/extracted/{issue}.json",
                       {"claims": [{"id": "c007", "normalized": "Mrs C. Taylor"}]})
        write_json(root / "data/residents/hh_press.json", {"id": "hh_press", "arrival": {
            "value": "1835-08-10", "confidence": "inferred", "sources": ["press_source"],
            "note": "The notice is over the copy date (gazette_1835_08_19#c007)."}})
        units, unit_faults = extract_units(root, registry)
        keys = {unit["record_key"] for unit in units}
        index = target_index(root, keys)
        hit = {unit["unit_id"] for unit in units
               if natural_disposition(root, unit, index).get("disposition") == "asserted"}
        pattern_faults = [f for f in unit_faults if "press" in f and "unregistered" not in f]
        if pattern_faults:
            failures.append(f"the file-local fixture did not extract: {pattern_faults!r}")
        elif len(hit) != 1 or "gazette_1835_08_19" not in next(iter(hit)):
            failures.append(
                f"a card citing one claim closed {len(hit)} unit(s), not the one it named: {hit!r}")
        else:
            print("  holds: a card naming one file-qualified claim closes that claim alone")
        bare = copy.deepcopy(read_json(root / "data/residents/hh_press.json"))
        bare["arrival"]["note"] = "The notice is over the copy date (c007)."
        write_json(root / "data/residents/hh_press.json", bare)
        index = target_index(root, keys)
        if any(natural_disposition(root, unit, index).get("disposition") == "asserted"
               for unit in units):
            failures.append("a bare file-local id still closed a unit")
        else:
            print("  fires: a bare claim number names no file-local unit at all")
        undeclared = copy.deepcopy(registry)
        undeclared["domains"][0]["ledger_units"][0].pop("file_local_containers")
        got = record_id_scope_faults(extract_units(root, undeclared)[0], undeclared)
        if not any("does not say whether" in fault for fault in got):
            failures.append(f"an undeclared repeated record id did not fire: {got!r}")
        else:
            print("  fires: a repeated record id whose scope the registry does not declare")
        declared_global = copy.deepcopy(registry)
        declared_global["domains"][0]["ledger_units"][0] = {
            "glob": "extracted/*.json", "containers": ["claims"], "global_containers": ["notes"]}
        got = record_id_scope_faults(extract_units(root, declared_global)[0], declared_global)
        if not any("repeats any more" in fault for fault in got):
            failures.append(f"a dead global declaration did not fire: {got!r}")
        else:
            print("  fires: a global declaration for a container whose ids no longer repeat")

        duplicate = {"units": [base, copy.deepcopy(base)], "unit_count": 2,
                     "totals": {name: (2 if name == "asserted" else 0) for name in DISPOSITIONS}}
        got = validate_document(duplicate, root, {})
        if not any("duplicate unit_id" in fault for fault in got):
            failures.append("duplicate unit id did not fire")
        else:
            print("  fires: a duplicate stable unit id")
    for failure in failures:
        print("   SILENT: " + failure)
    print("LEDGER SELF-TEST %s — 23 case(s)" % ("FAIL" if failures else "PASS"))
    return 1 if failures else 0
