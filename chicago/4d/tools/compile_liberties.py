#!/usr/bin/env python3
"""Compile docs/LIBERTIES.md into data/liberties.json for the walkthrough.

    python3 tools/compile_liberties.py            write data/liberties.json
    python3 tools/compile_liberties.py --check    re-derive and diff, write nothing

The project's standard is that *a visitor should be able to tell you which parts
we made up*. The per-attribute confidence model does that for attributes, and the
provenance popup shows it. It cannot show the liberties that live ABOVE any single
attribute — scope, omission, simplification, a navigation rule — because those
belong to no attribute and to no structure. Those are written in LIBERTIES.md,
which until now shipped nowhere a visitor could read it.

So the markdown stays the source of truth and stays append-only, and this derives
the machine-readable copy the renderer loads. Same discipline as data/datum.json:
the derived artefact is committed so the site needs no build step, and `check.sh`
re-derives it on every commit, so an edit to the prose that never reaches the JSON
is a gate failure rather than a silent divergence.

One field is read as data rather than as prose: `**Covers:**` lists the inventions
an entry admits to, as `structure_id[.phase_id].aspect` tokens, and `validate.py`
matches those claims against the records in both directions. The aspect may be a
drawn one (`footprint`, `position`) or any attribute of the building's form
(`form.roof_type`) — anything a record states without evidence.

The ground admits to its inventions in a namespace of its own,
`terrain.<epoch>.<claim>`, because the terrain is not a structure and squeezing
it into the structures' grammar would misname it in the one file whose whole job
is calling things what they are. Epoch is part of the token rather than dropped:
`docs/EPOCHS.md` versions terrain per epoch, so a later year gets its own
shoreline and its own inventions, and an admission about the 1834 bank must not
silently discharge whatever an 1830 one makes up.

Deliberately NOT a markdown renderer. It reads the one shape this document has —
`### L<n> — <title>` followed by `**Label:** text` fields — and carries the field
text through verbatim, markdown and all, for the renderer to display. Anything it
cannot parse it reports rather than dropping.

WHICH SECTION AN ENTRY IS IN TAKES TWO STATEMENTS THAT AGREE (T-0054). `resolved`
is not a label like the others: `validate.py` exempts that section from the check
that a claimed invention is still an invention, which is what lets an append-only
document survive its own data being corrected. So it is the one section a mistake
in cannot be caught by anything downstream — the exemption's whole job is to stop
asking.

It was reached by accident 23 times. `## Resolved` was the LAST section of the
document, and this project's rule is that a liberty is APPENDED, so an entry
written at the end of the file landed inside the exemption and compiled
`section: "resolved"` while the fence it was written for stood in the town. The
markdown and the compiled JSON agreed exactly — this file read the fault the same
way both times — which is the same blind spot T-0207 found with conflict markers:
a consistency check cannot see a fault that both sides reproduce faithfully.

The document was reshaped so that appending lands in the per-subject register, and
that is the fix. This is the guard: an entry's own text says whether it was
settled, in the `**Resolved:**` line the section's preamble has always asked for,
and its position says the same thing independently. The exemption is granted only
where the two agree. Either half alone is reported, and the compiled section is
the one that is still checked — a misfiled entry is a standing liberty until
somebody writes down what settled it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "LIBERTIES.md"
OUT = ROOT / "data" / "liberties.json"

# "### L4a — Sauganash Hotel: the log wing is inferred from two derivative images"
#
# The trailing letter is part of the id and not decoration: `L31` and `L31a` are
# two entries, nine such sub-entries stand in the document today, and a numbering
# check that folds them onto their parent cries wolf nine times on an unmodified
# file — which is worse than no check, because a gate that is always red gets
# switched off (T-0186).
HEADING = re.compile(r"^###\s+(L\d+[a-z]?)\s*[—-]\s*(.+?)\s*$", re.M)

# A line that MEANT to be an entry heading, matched loosely so the strict grammar
# above can be told apart from a near miss.
#
# The strict shape is not a filter, it is a CLIFF. A heading it rejects is not
# reported and not dropped — the body underneath it folds into the previous
# entry's fields, and the liberty leaves the register without a word. Measured
# 2026-08-27 (T-0186) by appending `### L198 – title` with an EN dash, which the
# `[—-]` class does not carry: 197 liberties compiled, `--check` exited 0, the
# whole of check.sh stayed green, and L198 was simply not there while its
# Decision and Recorded hung off the end of L197.
#
# That is the same silence this ticket was filed for, one step earlier than the
# duplicate number. A ledger whose whole job is to say which parts we made up
# cannot lose an entry quietly: an invention with no admission is the one fault
# that outranks everything else here.
NEAR_HEADING = re.compile(r"^\s{0,3}#{2,6}\s*L\s*\d+")
SECTION = re.compile(r"^##\s+(.+?)\s*$", re.M)
# "**How to resolve:**" — a bolded label ending in a colon. The colon is what
# keeps ordinary emphasis ("**no** gallery", "**[DISPUTED]**") out of the match.
FIELD = re.compile(r"\*\*([A-Z][^*:]{0,60}):\*\*")
DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# "**Covers:** `sauganash_hotel.log_1829.footprint`, `wolf_point_tavern.footprint`"
# — the structured half of an admission. Shape is checked here; whether the token
# resolves to a real phase carrying a real invention is validate.py's business,
# so a renamed record fails the gate as a semantic error rather than by making the
# derived file uncompilable.
#
# Two shapes of aspect, and the difference is deliberate. The record's fixed
# blocks — `footprint`, `position`, `documented_range`, `ground_contact`, and the
# structure-level `function` and `occupants` — are a closed list, because their
# names are part of the schema. Everything under `form` is open, because that is where a building's
# character is written and the vocabulary grows with the archetypes; a form claim
# therefore carries its `form.` prefix, which is also what keeps the last segment
# from having to be guessed at.
COVER_ASPECTS = ("footprint", "position", "documented_range", "function", "occupants",
                 "ground_contact")
FORM_ASPECT = r"form(?:\.[a-z0-9_]+)+"
COVER_TOKEN = re.compile(
    r"^([a-z0-9_]+\*?|\*)(?:\.([a-z0-9_]+?|\*))?\.("
    + "|".join(COVER_ASPECTS) + r"|" + FORM_ASPECT + r"|form\.\*)$")

# A CLASS token: `recon_*.*.form.*`.
#
# Added because grading the invented buildings honestly turned ~2,900 values into
# admitted inventions overnight, and the alternative was 2,900 hand-written
# tokens. That is not a stricter document, it is an unreadable one — and this
# register exists to be read. A visitor's question is "which parts of this did
# you make up", and "every dimension of every building the reconstruction
# programme raised, because none of them is recorded anywhere" answers it better
# than two thousand lines they will never scroll through.
#
# The wildcard is deliberately narrow. It may stand for a structure id, a phase
# id, or the attribute after `form.` — never for the aspect vocabulary itself,
# so no entry can write `*.*.*` and silently discharge the whole gate. An
# admission still has to say WHAT KIND of thing it is admitting to inventing.
WILDCARD = "*"

# "**Covers:** `terrain.e1834_harbor_cut.bank`" — the ground's own namespace.
#
# The terrain invents as freely as a record does — a bank profile nobody drew, a
# channel section whose note says it carries no evidence at all — and until this
# existed the coverage gate read `data/structures/` and could not see any of it,
# so those admissions were owed by a person rather than demanded by a check.
#
# `terrain` is a reserved first segment rather than a structure id, and the claim
# is the id `compile_scene.ground_claims` gives the block — one segment for a
# whole block (`bank`, `micro_relief`) and two for a member of a list of them
# (`swales.west_prairie_swale_a`). The epoch sits between the two because
# `docs/EPOCHS.md` versions the ground: a second scene gets a second terrain with
# its own inventions, and one admission must not discharge both.
TERRAIN_NS = "terrain"
TERRAIN_TOKEN = re.compile(r"^terrain\.([a-z0-9_]+)\.(.+)$")

# "**Scope:** `register_1835.businesses[survival_liberty_required]` — 126 businesses"
# — the second field read as data rather than as prose, and the answer to a
# liberty that is owed by a POPULATION rather than by a record.
#
# `Covers:` names invented values one at a time, which is the right shape while
# the admission is about a building. It cannot state the assumption the
# newspaper register mints: a business documented before 1835 is taken to be
# still standing on the scene date unless something contradicts it (owner ruling
# 3, 2026-08-28). Not one of those businesses has a structure record yet — the
# seeding that raises them is still ahead — so there is no token to write, and
# writing one near-identical entry per business the day there is would bury the
# register under its own bookkeeping, which is the fault the class wildcard above
# was added to avoid.
#
# So one entry states the assumption once and DELEGATES its membership to a
# derived file, naming the file, the predicate, and how many it reaches. The
# count is the load-bearing half. A scope that has drifted from its register is
# worse than no scope at all, because it reads as a measured claim and is not
# one — the T-0207 shape again, one step further out: here the two sides are the
# prose and the data, and only re-deriving the number can tell them apart. So it
# is re-derived on every compile and a disagreement is a gate failure.
SCOPE_TOKEN = re.compile(r"^`([a-z0-9_]+\.[a-z0-9_]+\[[a-z0-9_]+\])`"
                         r"\s*[\u2014-]\s*(\d+)\b(.*)$")

REGISTER_1835 = ROOT / "data" / "research" / "newspapers" / "register_1835.json"


def _register_survival_liberty_count() -> int:
    """Businesses standing at the scene date on an assumption, not on a source.

    `present_at_scene_date` as well as the flag, because the register only
    carries the flag forward for a business nothing contradicts — asserting both
    here keeps this count from quietly widening if that ever separates.
    """
    doc = json.loads(REGISTER_1835.read_text())
    return sum(1 for b in doc.get("businesses", [])
               if b.get("present_at_scene_date") and b.get("survival_liberty_required"))


def _register_backdating_liberty_count() -> int:
    """Businesses standing at the scene date documented only after it.

    The forward twin of `_register_survival_liberty_count`, and counted the same
    way and for the same reason: `present_at_scene_date` is asserted here as well
    as the flag, so this number cannot quietly widen if `compile_register.py` ever
    carries the flag on a business its own evidence excludes.
    """
    doc = json.loads(REGISTER_1835.read_text())
    return sum(1 for b in doc.get("businesses", [])
               if b.get("present_at_scene_date") and b.get("backdating_liberty_required"))


RESIDENTS_HOUSEHOLDS = ROOT / "data" / "residents" / "households"


def _letter_list_person_count() -> int:
    """People the town holds on a post-office letter list and nothing else.

    Counted off the household RECORDS rather than off `index.json`'s `counts`
    block, which is a denormalised copy another tool writes: a scope that reads a
    number somebody else derived is agreeing with a second opinion, not measuring.
    T-0379's ruling made this most of the town's people, so the liberty that admits
    the change of scale has to be able to restate its own share.
    """
    n = 0
    for path in sorted(RESIDENTS_HOUSEHOLDS.glob("*.json")):
        doc = json.loads(path.read_text())
        n += sum(1 for p in doc.get("persons") or [] if p.get("letter_list_only"))
    return n


def _civic_mint_person_count() -> int:
    """People the town holds because its own civic, church, press, book and census
    records name them, minted by tools/mint_civic_residents.py (T-0514).

    Counted off the household RECORDS for the reason the letter-list scope above
    gives at length: reading `index.json`'s denormalised `counts` block would be
    agreeing with a second opinion rather than measuring.
    """
    n = 0
    for path in sorted(RESIDENTS_HOUSEHOLDS.glob("*.json")):
        doc = json.loads(path.read_text())
        n += sum(1 for p in doc.get("persons") or [] if p.get("civic_mint"))
    return n


def _back_projected_position_count() -> int:
    """Businesses standing on a face read back out of a later directory (T-0633).

    Counted off the household RECORDS, for the same reason the letter-list scope
    is: `address_back_projection.json` carries its own `counts` block, and a
    scope that reads a number the pass wrote about itself is agreeing rather than
    measuring. The record is what a reader opens, so the record is what is
    counted.
    """
    n = 0
    for path in sorted(RESIDENTS_HOUSEHOLDS.glob("*.json")):
        doc = json.loads(path.read_text())
        for person in (doc.get("directories") or {}).get("people") or []:
            bp = person.get("back_projection") or {}
            if bp.get("outcome") == "placed":
                n += 1
    return n


def _back_projected_residence_count() -> int:
    """Homes standing on a face read back out of a later directory (T-0669).

    The residence half of the pass above, counted the same way and off the same
    records, and kept a separate enumeration because it is a separate policy: a
    home is carried back on a weaker argument than a shop is, and a scope that
    added the two together would let one liberty's count move on the other's work.
    """
    n = 0
    for path in sorted(RESIDENTS_HOUSEHOLDS.glob("*.json")):
        doc = json.loads(path.read_text())
        for person in (doc.get("directories") or {}).get("people") or []:
            if (person.get("residence_back_projection") or {}).get("outcome") == "placed":
                n += 1
    return n


STRUCTURES_DIR = ROOT / "data" / "structures"


def _land_owner_count() -> int:
    """Roofs standing on a tract the register names, put there by a constructed grid.

    Counted off the structure RECORDS rather than off `ground.json`'s own `counts`
    block, for the reason the two scopes above are: a scope that reads the number
    the pass wrote about itself is agreeing with a second opinion, not measuring.
    """
    return sum(1 for path in sorted(STRUCTURES_DIR.glob("*.json"))
               if "land_owner" in json.loads(path.read_text()))


# enumeration -> (how many it reaches now, where that number is derived from).
#
# A scope may only name an enumeration written down HERE. The alternative — an
# entry free to spell its own predicate — is a check marking its own homework:
# whatever the prose selected would be exactly what the prose counted, for ever.
SCOPE_SOURCES = {
    "register_1835.businesses[survival_liberty_required]": (
        _register_survival_liberty_count,
        "data/research/newspapers/register_1835.json, itself re-derived by "
        "tools/compile_register.py --check"),
    "register_1835.businesses[backdating_liberty_required]": (
        _register_backdating_liberty_count,
        "data/research/newspapers/register_1835.json, itself re-derived by "
        "tools/compile_register.py --check"),
    "residents.persons[letter_list_only]": (
        _letter_list_person_count,
        "data/residents/households/*.json, themselves re-derived by "
        "tools/mint_letter_list_residents.py --check"),
    "residents.persons[civic_mint]": (
        _civic_mint_person_count,
        "data/residents/households/*.json, themselves re-derived by "
        "tools/mint_civic_residents.py --check"),
    "address_back_projection.positions[placed]": (
        _back_projected_position_count,
        "data/residents/households/*.json, themselves re-derived by "
        "tools/back_project_addresses.py --check"),
    "residence_back_projection.positions[placed]": (
        _back_projected_residence_count,
        "data/residents/households/*.json, themselves re-derived by "
        "tools/back_project_residences.py --check"),
    "structures.land_owner[constructed_section_grid]": (
        _land_owner_count,
        "data/structures/*.json, themselves re-derived by "
        "tools/resolve_land_tracts.py --check"),
}

SECTION_KEY = {
    "standing liberties": "standing",
    "per-subject liberties": "per_subject",
    "resolved": "resolved",
}

# The order the Evidence panel reads in, which is not the order the document is
# written in. The markdown is a ledger and grows by appending; the panel is read
# by a visitor, and what we are still making up belongs above what we no longer
# are. Emitting in this order also means the file can be reshaped — as it was to
# get Resolved out of the append path — without the panel's order moving.
SECTION_ORDER = ("standing", "per_subject", "resolved", "other")

# The section that cannot be entered by accident, and the field that has to say so.
RESOLVED = "resolved"
SETTLED_FIELD = "resolved"

# Where a misfiled entry lands instead. It is the section that is still CHECKED:
# an entry nobody has said is settled keeps its obligations, and the register it
# keeps them in is the per-subject one, which is 167 of the 170 unsettled entries.
UNSETTLED_DEFAULT = "per_subject"


def _clean(text: str) -> str:
    """Collapse the markdown's hard-wrapped lines into one paragraph."""
    return re.sub(r"\s*\n\s*", " ", text).strip().rstrip()


def claim_sort_key(c: dict) -> tuple:
    """A total order over both domains, so the derived file is deterministic."""
    if c.get("domain") == TERRAIN_NS:
        return (TERRAIN_NS, c["epoch"], "", c["claim"])
    return ("structure", c["structure"], c["phase"] or "", c["aspect"])


def claim_token(c: dict) -> str:
    """A claim back in the text the document wrote it as.

    One function, so an error message quoting a token and the markdown that has
    to be edited to satisfy it cannot come to disagree about the grammar.
    """
    if c.get("domain") == TERRAIN_NS:
        return f"{TERRAIN_NS}.{c['epoch']}.{c['claim']}"
    return ".".join(t for t in (c["structure"], c["phase"], c["aspect"]) if t)


def parse_covers(text: str, lid: str, problems: list[str]) -> list[dict]:
    """`Covers:` tokens -> the claims this entry makes, in one of two domains.

    For a structure the token is `structure_id[.phase_id].aspect`. The aspect is
    the trailing segment (or `form.` plus one, for the open half of the
    vocabulary), so a two-segment token and a three-segment one are told apart
    without guessing: `walker_meeting_house.position` covers whichever phases drew
    a position from nothing, `walker_meeting_house.log_1831.position` covers
    exactly one, and `sauganash_hotel.log_1829.form.roof_type` names the one
    attribute in the one phase.

    For the ground it is `terrain.<epoch>.<claim>`, and the domain is carried on
    the claim rather than guessed at from its shape by whoever reads it later.
    Two vocabularies meeting in one field is exactly where a reader starts
    inferring which one they are looking at, and this project has already paid
    once for a name read as being about the wrong thing.
    """
    claims: list[dict] = []
    for raw in re.split(r"[,;]", text):
        token = raw.strip().strip(".").strip("`").strip()
        if not token:
            continue
        if token.split(".")[0] == TERRAIN_NS:
            m = TERRAIN_TOKEN.match(token)
            if not m:
                problems.append(f"{lid}: Covers entry '{token}' is not "
                                f"terrain.<epoch>.<claim>, which is the shape an "
                                f"admission about the ground takes")
                continue
            claims.append({"domain": TERRAIN_NS, "epoch": m.group(1), "claim": m.group(2)})
            continue
        m = COVER_TOKEN.match(token)
        if not m:
            problems.append(f"{lid}: Covers entry '{token}' is not "
                            f"structure_id[.phase_id].<{'|'.join(COVER_ASPECTS)}"
                            f"|form.attribute> or terrain.<epoch>.<claim>")
            continue
        claims.append({"domain": "structure", "structure": m.group(1),
                       "phase": m.group(2), "aspect": m.group(3)})
    if not claims:
        problems.append(f"{lid}: a Covers field that claims nothing — drop the field "
                        f"or name what it discharges")
    return sorted(claims, key=claim_sort_key)


def parse_scope(text: str, lid: str, problems: list[str], sources: dict) -> dict | None:
    """`Scope:` -> the population an entry covers, and the count it claims to reach.

    Two independent statements of one fact, which is the same discipline the
    section check runs on. The markdown declares a number a reader can see; the
    derived file it names is counted here. Neither is believed alone — a
    hand-typed count is a claim about data that moves under it, and a count taken
    silently from the data would agree with itself for ever and tell a reader
    nothing at all.

    Returns the declared reading, not the derived one, on purpose: this file is a
    faithful copy of the markdown, so a drift has to surface as a problem the
    gate reports rather than as a number the next compile quietly absorbs.
    """
    m = SCOPE_TOKEN.match(text.strip())
    if not m:
        problems.append(
            f"{lid}: Scope must read '`<enumeration>` \u2014 <n> <noun>', naming an "
            f"enumeration something derives and how many of it the liberty reaches; "
            f"got {text[:60]!r}")
        return None
    enumeration, declared = m.group(1), int(m.group(2))
    source = sources.get(enumeration)
    if source is None:
        problems.append(
            f"{lid}: Scope names the enumeration '{enumeration}', which nothing "
            f"derives \u2014 a population selected by the same sentence that counts it "
            f"is unchecked. Add it to compile_liberties.SCOPE_SOURCES. Known: "
            f"{', '.join(sorted(sources)) or '(none)'}")
        return None
    count, derived_from = source
    actual = count()
    if actual != declared:
        problems.append(
            f"{lid}: Scope claims {declared} for '{enumeration}' and it reaches "
            f"{actual} today \u2014 the population moved under the liberty. Restate the "
            f"count, and the prose that reasons from it, against {derived_from}")
    return {"enumeration": enumeration, "count": declared}


def settled_section(lid: str, positional: str, states_settled: bool,
                    problems: list[str]) -> str:
    """The section an entry is in, from its position AND its own words.

    They are two independent statements of one fact, and `resolved` is granted
    only where they agree, because `resolved` is the section `validate.py`
    exempts from the over-claim check. A section that switches a check off is
    the one section a mistake in has nothing downstream to catch it.

    Neither half is silently believed:

      * Under `## Resolved`, saying nothing about what settled it — the T-0054
        fault, and the reason the document was reshaped. It compiles as a
        standing liberty, keeps its obligations, and is named here.
      * Carrying a `**Resolved:**` line somewhere else — the mirror image, and
        the likelier one now that appending lands in the per-subject register.
        It compiles where it sits, because a line of prose may not switch off a
        check on its own; the entry is moved, or it is not resolved.
    """
    if positional == RESOLVED and not states_settled:
        problems.append(
            f"{lid}: sits under '## Resolved' but no '**Resolved:**' line says what "
            f"settled it — an entry appended at the end of the file used to land "
            f"here and be exempted from the check that its claim is still an "
            f"invention (T-0054). Compiled as '{UNSETTLED_DEFAULT}'. Move it into the "
            f"per-subject register, or write down what settled it")
        return UNSETTLED_DEFAULT
    if positional != RESOLVED and states_settled:
        problems.append(
            f"{lid}: carries a '**Resolved:**' line but sits under the "
            f"'{positional}' section — say what settled it AND move the entry into "
            f"'## Resolved'. Compiled as '{positional}': one line of prose does not "
            f"exempt an entry from the check that its claim is still an invention")
    return positional


def unparsed_headings(markdown: str) -> list[tuple[int, str]]:
    """Lines that look like an entry heading and are not one, with line numbers.

    The one thing this document cannot survive is losing an entry silently, and
    a heading the grammar rejects does exactly that — see NEAR_HEADING. So the
    near miss is caught here rather than downstream, where there is nothing left
    to catch: the compiled JSON, the liberties gate and the Evidence panel all
    agree perfectly about a register the entry was never in.

    Line numbers, because the whole point is that the reader cannot see it. A
    bare "a heading did not parse" in an 8,800-line file is a search, and an en
    dash and an em dash are the same three pixels apart.
    """
    parsed = {markdown.count("\n", 0, m.start()) for m in HEADING.finditer(markdown)}
    return [(i + 1, line) for i, line in enumerate(markdown.splitlines())
            if NEAR_HEADING.match(line) and i not in parsed]


def duplicate_ids(entries: list[dict]) -> list[str]:
    """Numbers taken twice, reported with both titles.

    Two branches that each append `### L177` merge CLEAN when their appends land
    in different parts of the file, and git says nothing because neither touched
    the other's lines (T-0186, 2026-08-24: it happened twice in one afternoon).
    A conflict is safe because it stops you; a clean merge of two appends to a
    numbered ledger is not, and this is what stands in for the conflict.

    Both titles, because the number alone does not tell you which of the two
    entries is the newcomer to renumber — and the renumber has to carry its
    references, since liberty numbers are cited from records, tickets, STATUS.md
    and the research docs.
    """
    seen: dict[str, str] = {}
    problems: list[str] = []
    for e in entries:
        first = seen.get(e["id"])
        if first is not None:
            problems.append(
                f"{e['id']}: taken twice — '{first}' and '{e['title']}'. Two "
                f"appends to a numbered ledger merged clean; renumber the newer "
                f"entry and carry its citations. A lettered sub-entry ({e['id']}a) "
                f"is a different id and is not this")
        else:
            seen[e["id"]] = e["title"]
    return problems


def parse(markdown: str, known: dict[str, str],
          sources: dict | None = None) -> tuple[list[dict], list[str]]:
    problems: list[str] = []
    sources = SCOPE_SOURCES if sources is None else sources
    for lineno, line in unparsed_headings(markdown):
        problems.append(
            f"line {lineno}: '{line.strip()[:70]}' looks like an entry heading and "
            f"does not parse as one, so its body folds into the entry above it and "
            f"the liberty leaves the register. The shape is "
            f"'### L<n>[a] — Title', with an em dash or a plain hyphen")

    # Which "## " section each character offset falls under.
    sections = [(m.start(), m.group(1).strip().lower()) for m in SECTION.finditer(markdown)]

    def section_at(pos: int) -> str:
        name = ""
        for start, title in sections:
            if start < pos:
                name = title
            else:
                break
        if name not in SECTION_KEY:
            problems.append(f"entry at offset {pos} sits under an unknown section '{name}'")
        return SECTION_KEY.get(name, "other")

    entries: list[dict] = []
    heads = list(HEADING.finditer(markdown))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(markdown)
        body = markdown[m.end():end]
        # Stop at the next "## " section rule so a trailing section's prose does
        # not get swallowed into the last entry of the previous one.
        nxt = SECTION.search(body)
        if nxt:
            body = body[:nxt.start()]
        body = body.strip().strip("-").strip()

        fields = []
        marks = list(FIELD.finditer(body))
        if not marks:
            problems.append(f"{m.group(1)}: no '**Label:**' fields found")
        preamble = _clean(body[:marks[0].start()]) if marks else _clean(body)
        if preamble:
            problems.append(f"{m.group(1)}: text before the first field is dropped: "
                            f"{preamble[:60]}…")
        for j, f in enumerate(marks):
            stop = marks[j + 1].start() if j + 1 < len(marks) else len(body)
            text = _clean(body[f.end():stop])
            if not text:
                problems.append(f"{m.group(1)}: field '{f.group(1)}' is empty")
            fields.append({"label": f.group(1).strip(), "text": text})

        by_label = {f["label"].split(" (")[0].lower(): f["text"] for f in fields}
        recorded = DATE.search(by_label.get("recorded", ""))
        revised = DATE.search(by_label.get("revised", ""))

        # A liberty names its subject either as a record id in backticks or, in
        # a title, by the building's name. Both are matched, so the entry can be
        # tied back to the structure it constrains.
        blob = m.group(2) + " " + body
        subjects = sorted(sid for sid, name in known.items()
                          if sid in blob or (name and name in blob))

        covers = (parse_covers(by_label["covers"], m.group(1), problems)
                  if "covers" in by_label else [])
        scope = (parse_scope(by_label["scope"], m.group(1), problems, sources)
                 if "scope" in by_label else None)

        entries.append({
            "id": m.group(1),
            "title": m.group(2).strip(),
            "section": settled_section(m.group(1), section_at(m.start()),
                                       SETTLED_FIELD in by_label, problems),
            "subjects": subjects,
            "covers": covers,
            # Present only where an entry declares one, so the 200-odd liberties
            # owed by a record rather than by a population carry no empty field.
            **({"scope": scope} if scope else {}),
            "recorded": recorded.group(1) if recorded else None,
            "revised": revised.group(1) if revised else None,
            "fields": fields,
        })

    if not entries:
        problems.append("no '### L<n> — title' entries found at all")
    problems.extend(duplicate_ids(entries))
    for e in entries:
        if e["recorded"] is None:
            problems.append(f"{e['id']}: no Recorded date")

    # Grouped for the reader, stable within each group, so the panel's order is
    # a decision here rather than a side effect of where a section sits in a
    # 7,800-line markdown file. Nothing else in the derived file is reordered.
    entries.sort(key=lambda e: SECTION_ORDER.index(e["section"])
                 if e["section"] in SECTION_ORDER else len(SECTION_ORDER))

    return entries, problems


def build() -> tuple[dict, list[str]]:
    known = {}
    for p in sorted((ROOT / "data" / "structures").glob("*.json")):
        known[p.stem] = json.loads(p.read_text()).get("name", "")
    markdown = SOURCE.read_text()
    entries, problems = parse(markdown, known)
    doc = {
        "_doc": "GENERATED from docs/LIBERTIES.md by tools/compile_liberties.py. "
                "Do not hand-edit: tools/check.sh re-derives this file and fails on drift. "
                "Edit the markdown, which is append-only, and re-run the tool.",
        "source": "docs/LIBERTIES.md",
        "standard": "A visitor should be able to tell you which parts we made up.",
        "note": "The confidence model covers attributes. These are the decisions that live "
                "above any single attribute: scope, omission, simplification, and the choices "
                "a visitor would otherwise have to reverse-engineer.",
        "count": len(entries),
        "liberties": entries,
    }
    return doc, problems


SPECIMEN = """# Liberties taken

## Standing liberties

### L1 — A whole-scene decision
**Decision:** something the scene does everywhere.
**Recorded:** 2026-08-09.

---

## Resolved

Kept verbatim, with a **Resolved:** line saying what settled them.

### L2 — Settled, and it says so
**Decision:** something we invented.
**Recorded:** 2026-08-10.
**Resolved:** 2026-08-11, the evidence arrived.

### L3 — Appended at the end of the file, which used to be here
**Decision:** something we are still inventing.
**Recorded:** 2026-08-12.

---

## Per-subject liberties

### L4 — One building
**Decision:** something about one building.
**Recorded:** 2026-08-13.

### L5 — Says it was settled, and was never moved
**Decision:** something we invented.
**Recorded:** 2026-08-14.
**Resolved:** 2026-08-15, the evidence arrived.
"""


# The numbering faults, in miniature. Separate from SPECIMEN because that one is
# about which SECTION an entry is in and this one is about its NUMBER, and a
# specimen carrying both faults at once cannot show either cleanly.
#
# It holds the shape the committed document actually has — a parent with lettered
# sub-entries under it — beside the collision those sub-entries are forever being
# mistaken for. Both readings have to be asserted together or the check drifts
# into one of its two failure modes: silent on a real duplicate, or red nine
# times on a file nobody touched.
NUMBERING_SPECIMEN = """# Liberties taken

## Per-subject liberties

### L31 — A parent entry
**Decision:** something we invented.
**Recorded:** 2026-08-09.

### L31a — A lettered sub-entry, which is a different entry and not a duplicate
**Decision:** something narrower.
**Recorded:** 2026-08-10.

### L31b — A second sub-entry of the same parent
**Decision:** something else narrower.
**Recorded:** 2026-08-11.

### L32 — One branch's entry
**Decision:** something one branch invented.
**Recorded:** 2026-08-12.

### L32 — The other branch's entry, carried in by a merge that raised no conflict
**Decision:** something the other branch invented.
**Recorded:** 2026-08-13.
"""

# A heading that misses the grammar by one character. The en dash is the real
# instance — it is three pixels from the em dash the shape requires, and it is
# what a paste from anywhere else in the world brings with it.
SHAPE_SPECIMEN = """# Liberties taken

## Per-subject liberties

### L40 — An entry that parses
**Decision:** something we invented.
**Recorded:** 2026-08-09.

### L41 \u2013 An en dash, which the heading shape does not accept
**Decision:** something we invented and admit to.
**Recorded:** 2026-08-10.
"""


# The scope field's four readings, which a specimen is the only way to hold: the
# committed document cannot carry a drifted count or an invented enumeration,
# because the gate refuses to compile one.
#
# `specimen.things[flagged]` is resolved by a stub that returns 3, so L60 agrees,
# L61 has drifted by one, L62 names a predicate nothing derives, and L63 writes
# the field as the sentence a person would reach for first.
SCOPE_SPECIMEN = """# Liberties taken

## Per-subject liberties

### L60 — A population, counted, and the count agrees
**Decision:** something assumed about a whole class of things.
**Scope:** `specimen.things[flagged]` — 3 things carrying the flag.
**Recorded:** 2026-08-09.

### L61 — The same population, and the count has drifted under it
**Decision:** something assumed about a whole class of things.
**Scope:** `specimen.things[flagged]` — 2 things carrying the flag.
**Recorded:** 2026-08-10.

### L62 — A scope naming a predicate nothing derives
**Decision:** something assumed about a whole class of things.
**Scope:** `specimen.things[invented_right_here]` — 3 things carrying the flag.
**Recorded:** 2026-08-11.

### L63 — A scope written as the sentence a person reaches for first
**Decision:** something assumed about a whole class of things.
**Scope:** all the things in the register that carry the flag.
**Recorded:** 2026-08-12.
"""

SCOPE_STUB = {"specimen.things[flagged]": (lambda: 3, "the specimen")}


def self_test() -> bool:
    """Every assertion fires when broken.

    The specimen is the document in miniature, faults and all: an entry that is
    settled and says so, one that landed under Resolved by being appended (the
    T-0054 fault), and one that says it was settled without being moved (the
    mirror image). A synthetic document is the only way to hold both faults,
    because the committed one is repaired — and the repaired document is
    asserted too, at the end, so this cannot pass on the specimen alone.
    """
    ok = True

    def check(label, got, want=True):
        nonlocal ok
        if got != want:
            ok = False
        print(f"  {'ok  ' if got == want else 'FAIL'}  {label}")

    entries, problems = parse(SPECIMEN, {})
    at = {e["id"]: e["section"] for e in entries}
    blamed = {lid for lid in at for p in problems if p.startswith(lid + ":")}

    check("a standing entry compiles standing", at.get("L1") == "standing")
    check("a resolved entry that says what settled it compiles resolved",
          at.get("L2") == "resolved")
    check("…and is not blamed for anything", "L2" not in blamed)
    check("an entry under Resolved saying nothing is NOT compiled resolved",
          at.get("L3") == UNSETTLED_DEFAULT)
    check("…and the gate names it", "L3" in blamed)
    check("a per-subject entry compiles per_subject", at.get("L4") == "per_subject")
    check("…and is not blamed for anything", "L4" not in blamed)
    check("a Resolved line outside the section does NOT exempt the entry",
          at.get("L5") == "per_subject")
    check("…and the gate names that too", "L5" in blamed)
    check("the reader's order is standing, then per-subject, then resolved — "
          "and inside a group, the order the document was written in",
          [e["id"] for e in entries] == ["L1", "L3", "L4", "L5", "L2"])

    # The NUMBER of an entry, which is the other half. Same discipline as the
    # section assertions above: the fault in a specimen, then the live document
    # beside it, because a check can only be trusted once it has been seen to
    # fire and seen to stay quiet.
    num, num_problems = parse(NUMBERING_SPECIMEN, {})
    dupes = [p for p in num_problems if "taken twice" in p]
    check("a number taken by two entries is reported",
          len(dupes) == 1 and dupes[0].startswith("L32:"))
    check("…and the report names BOTH titles, so the newcomer can be told apart",
          bool(dupes) and "One branch's entry" in dupes[0]
          and "the other branch's entry" in dupes[0].lower())
    check("a lettered sub-entry is NOT a duplicate of its parent",
          [e["id"] for e in num] == ["L31", "L31a", "L31b", "L32", "L32"])
    check("…and nothing is reported for the sub-entries",
          not [p for p in num_problems if p.startswith(("L31:", "L31a:", "L31b:"))])

    # The heading that misses the grammar and takes its entry with it.
    shape, shape_problems = parse(SHAPE_SPECIMEN, {})
    near = [p for p in shape_problems if "looks like an entry heading" in p]
    want_line = SHAPE_SPECIMEN.splitlines().index(
        [l for l in SHAPE_SPECIMEN.splitlines() if "en dash" in l][0]) + 1
    check(f"a heading the grammar rejects is reported rather than swallowed "
          f"(line {want_line})",
          len(near) == 1 and f"line {want_line}:" in near[0])
    check("…and the entry it would have swallowed is named by line, not left "
          "to be searched for", bool(near) and "L41" in near[0])
    check("…and it is the ONLY entry parsed, which is why the silence mattered",
          [e["id"] for e in shape] == ["L40"])

    # The scope field, whose whole value is the count, and whose whole risk is
    # that the count stops being true without anything looking different.
    sco, sco_problems = parse(SCOPE_SPECIMEN, {}, SCOPE_STUB)
    scoped = {e["id"]: e.get("scope") for e in sco}
    sco_blamed = {lid: [p for p in sco_problems if p.startswith(lid + ":")]
                  for lid in scoped}

    check("a scope whose count agrees with its enumeration compiles",
          scoped.get("L60") == {"enumeration": "specimen.things[flagged]", "count": 3})
    check("…and is not blamed for anything", not sco_blamed.get("L60"))
    check("a count that has drifted from its enumeration is reported",
          len(sco_blamed.get("L61") or []) == 1)
    check("…and the report names BOTH numbers, so it can be repaired without "
          "re-deriving the population by hand",
          bool(sco_blamed.get("L61")) and "claims 2" in sco_blamed["L61"][0]
          and "reaches 3" in sco_blamed["L61"][0])
    check("…and the drifted entry still compiles the DECLARED count, so the next "
          "compile cannot absorb the drift into the derived file",
          (scoped.get("L61") or {}).get("count") == 2)
    check("an enumeration nothing derives is reported rather than believed",
          len(sco_blamed.get("L62") or []) == 1 and not scoped.get("L62"))
    check("…and the report lists the enumerations that do exist",
          bool(sco_blamed.get("L62"))
          and "specimen.things[flagged]" in sco_blamed["L62"][0])
    check("a Scope field written as prose is reported, not parsed into a count",
          len(sco_blamed.get("L63") or []) == 1 and not scoped.get("L63"))

    # And the document that ships. The fault this exists for is exactly a
    # section nobody meant to be in, so the specimen proving the assertion
    # fires is worth nothing without the live reading beside it.
    live, live_problems = parse(SOURCE.read_text(), {})
    settled = [e["id"] for e in live if e["section"] == RESOLVED]
    misfiled = [p for p in live_problems if "## Resolved" in p or "**Resolved:**" in p]
    check(f"the committed document misfiles nothing ({len(settled)} settled, "
          f"{len(live) - len(settled)} still standing)", not misfiled)

    # The nine sub-entries are the reason the lettered-id assertion above is not
    # academic: a check that folded them onto their parents would report nine
    # duplicates on an unmodified file, and the gate would be switched off within
    # the day rather than fixed.
    subs = [e["id"] for e in live if re.fullmatch(r"L\d+[a-z]", e["id"])]
    check(f"the committed document carries no duplicate number, across "
          f"{len(live)} entries including {len(subs)} lettered sub-entries "
          f"({', '.join(subs)})", not duplicate_ids(live))
    check(f"…and every one of its {len(live)} headings parses",
          not unparsed_headings(SOURCE.read_text()))

    # The live scopes, resolved against the real register rather than the stub.
    # The specimen proves the assertion fires; this proves the document it fires
    # on is clean today, which is the half a synthetic document cannot show.
    live_scopes = [(e["id"], e["scope"]["count"]) for e in live if e.get("scope")]
    scope_problems = [p for p in live_problems if ": Scope " in p]
    declared = ", ".join(f"{lid} reaches {n}" for lid, n in live_scopes)
    check(f"every scope in the committed document resolves and its count agrees "
          f"({declared or 'none declared'})",
          bool(live_scopes) and not scope_problems)
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare against the committed file")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the section assertions fire when broken")
    args = ap.parse_args()

    if args.self_test:
        print("\n\033[1m== …and its own assertions still fire when broken\033[0m")
        good = self_test()
        print("\nSELF-TEST " + ("PASS" if good else "FAIL"))
        return 0 if good else 1

    doc, problems = build()
    for p in problems:
        print(f"   {p}")

    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"   data/liberties.json is missing — run tools/compile_liberties.py")
            return 1
        if OUT.read_text() != text:
            print("   data/liberties.json does not match docs/LIBERTIES.md — "
                  "re-run tools/compile_liberties.py and commit the result")
            return 1
        # The summary line has to agree with the exit code. It used to print
        # "OK: … matches its markdown" and then exit 1 on the problems listed
        # directly above it, which reads as green in a 600-line gate log — the
        # one place a duplicate number was ever going to be noticed (T-0186).
        # Matching is not passing: the derived file agreeing with a faulty
        # register is the exact shape of fault this project has now paid for
        # three times (T-0054, T-0207, and this one).
        if problems:
            print(f"   data/liberties.json matches its markdown, and the markdown "
                  f"has {len(problems)} problem(s) listed above — a faithful copy "
                  f"of a faulty register is still a fail")
            return 1
        print(f"OK: {doc['count']} liberties, data/liberties.json matches its markdown")
        return 0

    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['count']} liberties"
          + (f" — {len(problems)} problem(s) above" if problems else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
