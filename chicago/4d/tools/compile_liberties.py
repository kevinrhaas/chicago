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
#
# A SLUGGED ID IS AN ID (T-1399). `L-rc-sex-rate` and `L-rc-age-conditioning` were
# written on 2026-09-17 and 2026-09-18 under the names the reconstruction
# programme had promised them by, and `L\d+` did not match either one. Both fell
# off exactly the cliff the paragraph below describes: 259 liberties compiled,
# `--check` exited 0, and the two admissions covering 587 drawn sexes and 1,212
# drawn age bands hung off the end of L241 as three `How to resolve` fields on a
# liberty about the 1880s scene. They are cited by that name from two tools, the
# sex-age model and five household cards, so the grammar is widened to the name
# they already carry rather than the citations rewritten to suit the grammar.
HEADING = re.compile(r"^###\s+(L\d+[a-z]?|L-[a-z0-9]+(?:-[a-z0-9]+)*)\s*[—-]\s*(.+?)\s*$",
                     re.M)

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
NEAR_HEADING = re.compile(r"^\s{0,3}#{2,6}\s*L\s*[-\d]")
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


BUSINESSES_AUTHORED = ROOT / "data" / "businesses" / "authored"


def _reconstructed_business_count() -> int:
    """Houses of trade nobody named, written to fill a count the census leaves short.

    Counted off the records themselves rather than off the business index, because the
    index is derived from them and a liberty that counted a derivation would be checking
    the compiler rather than the invention. `provenance` as well as the block, for the
    reason the register counts above assert two fields: a reconstruction that ever lost
    its `reconstruction` block would be a record with no writer, and this count must not
    quietly narrow when that happens — tools/compile_businesses.py refuses it instead.
    """
    if not BUSINESSES_AUTHORED.is_dir():
        return 0
    n = 0
    for path in sorted(BUSINESSES_AUTHORED.glob("*.json")):
        doc = json.loads(path.read_text())
        if doc.get("provenance") == "reconstructed" and doc.get("reconstruction"):
            n += 1
    return n


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


def _modelled_family_person_count() -> int:
    """People the household model drew for a head the sources leave standing alone.

    Counted off the household RECORDS and off the stage key each of them carries, for the
    same reason the letter-list count is: a scope that read a number another tool derived
    would be agreeing with a second opinion rather than measuring. T-1171's stage is the
    first thing in this project to write a person, so the liberty that admits it has to be
    able to restate its own size.
    """
    n = 0
    for path in sorted(RESIDENTS_HOUSEHOLDS.glob("*.json")):
        doc = json.loads(path.read_text())
        n += sum(1 for p in doc.get("persons") or []
                 if ((p.get("reconstruction") or {}) if isinstance(p.get("reconstruction"), dict)
                     else {}).get("stage") == "modelled_families")
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
RECON_DIR = ROOT / "data" / "reconstruction"


def _land_owner_count() -> int:
    """Roofs standing on a tract the register names, put there by a constructed grid.

    Counted off the structure RECORDS rather than off `ground.json`'s own `counts`
    block, for the reason the two scopes above are: a scope that reads the number
    the pass wrote about itself is agreeing with a second opinion, not measuring.
    """
    return sum(1 for path in sorted(STRUCTURES_DIR.glob("*.json"))
               if "land_owner" in json.loads(path.read_text()))


def _attr(value):
    """A form attribute's value, whether it is bare or wrapped in a tier block."""
    return value.get("value") if isinstance(value, dict) else value


def _phase_forms():
    """Every phase form in the structure layer, read once."""
    for path in sorted(STRUCTURES_DIR.glob("*.json")):
        doc = json.loads(path.read_text())
        for record in (doc if isinstance(doc, list) else [doc]):
            if not isinstance(record, dict) or "id" not in record:
                continue
            for phase in (record.get("phases") or []):
                yield record, (phase.get("form") or {})


def _brick_fabric_count() -> int:
    """Structures the layer says are brick, which L264's course dimension reaches.

    Counted off the records rather than off materials.md's prose, for the reason
    every scope here is: the memo says "two records are attested brick" and the
    layer carries three — `fort_dearborn_magazine` is the one the sentence forgot.
    A liberty that restated the memo's number would be agreeing with a second
    opinion instead of measuring the population it reaches.
    """
    return len({record["id"] for record, form in _phase_forms()
                if _attr(form.get("construction")) == "brick"})


def _log_and_fort_roof_count() -> int:
    """Phases on a log dwelling or a fort structure — the roofs L266 shingles by an
    argument rather than by materials.md §2.2's grading.

    Counted off the records' own `archetype` rather than restated from the selector,
    for the reason every scope here is counted: `roof_substrate()` deals by archetype,
    so a record refamilied into or out of `log_dwelling` moves in and out of this
    liberty's reach, and the entry should say how many it reaches today rather than
    how many it reached when it was written.
    """
    return sum(1 for record, _ in _phase_forms()
               if record.get("archetype") in ("log_dwelling", "fort_structure"))


def _roof_covering_count() -> int:
    """Phases stating a roof type, which is the population L263's exposure reaches.

    R-W2a finding 2 counted the roof TYPES and found no covering behind any of
    them. This counts the same population, because the exposure L263 commits is
    drawn on every one of them the moment the substrate carries a tile.
    """
    return sum(1 for _, form in _phase_forms() if _attr(form.get("roof_type")))


RESIDENTS_DIR = ROOT / "data" / "residents"
PROGRAMME = ROOT / "data" / "reconstruction" / \
    "1835_resident_reconstruction_programme.json"


def programme_stages() -> list[dict]:
    """The reconstruction programme's stages, in the order it runs them.

    Read rather than restated, for the reason validate.py reads the same file for
    the same list: adding a stage is a data change, and a stage this module had to
    be taught about by hand would be a stage that could be forgotten. A missing or
    unreadable programme yields no stages, which makes every stage assertion below
    vacuous and the enumeration family empty — an entry claiming a stage scope then
    fails on the enumeration nothing derives, which is the right answer.
    """
    try:
        return list(json.loads(PROGRAMME.read_text()).get("stages") or [])
    except (OSError, ValueError, TypeError):
        return []


def _stage_person_count(stage: str) -> int:
    """People a reconstruction stage minted, counted off the cards it wrote.

    Over the WHOLE of `data/residents/`, not `households/` alone: five stages write
    into a directory of their own — `readmitted/`, `reconstructed_trades/`,
    `lodgers/`, `transients/`, `underdocumented/` — and a counter anchored on the
    household directory reads every one of them as zero. The three hand-written
    stage counters this replaced (T-1171's, T-1174's and T-1176's) were anchored
    there and were right only because their three stages happen to write into it.

    Counted off the records and off the stage key each person carries, never off a
    stage's own ledger: a scope that read the number the pass wrote about itself
    would be agreeing with a second opinion rather than measuring its own size.
    """
    n = 0
    for path in sorted(RESIDENTS_DIR.rglob("*.json")):
        try:
            doc = json.loads(path.read_text())
        except ValueError:
            continue
        if not isinstance(doc, dict):
            continue
        for person in doc.get("persons") or []:
            # `persons` is a list of records in the resident layer and a list of
            # NAMES in a handful of research files that share the key; a card is
            # the only thing that can carry a stage, so anything else is skipped
            # rather than crashed on.
            if not isinstance(person, dict):
                continue
            block = person.get("reconstruction")
            if isinstance(block, dict) and block.get("stage") == stage:
                n += 1
    return n


def stage_enumeration(key: str) -> str:
    return f"residents.persons[{key}]"


def _stage_scope_sources() -> dict:
    """One enumeration per person-minting stage, derived from the programme.

    The rows below this are hand-written because each counts a different predicate
    over a different file. These all count the same predicate over the same layer,
    so writing eleven of them out would be eleven chances to write the twelfth one
    wrong — and a stage added to the programme with no enumeration would take its
    liberty's `Scope:` with it into the "nothing derives that" branch, which reads
    as the entry's fault rather than the register's.
    """
    rows = {}
    for stage in programme_stages():
        key = stage.get("key")
        if not key or stage.get("mints") != "persons":
            continue
        built_by = stage.get("built_by")
        rows[stage_enumeration(key)] = (
            (lambda k=key: _stage_person_count(k)),
            f"data/residents/**/*.json, themselves re-derived by {built_by} --check"
            if built_by else
            "data/residents/**/*.json, themselves re-derived by the stage's own "
            "writer under tools/check.sh")
    return rows


# enumeration -> (how many it reaches now, where that number is derived from).
#
# A scope may only name an enumeration written down HERE. The alternative — an
# entry free to spell its own predicate — is a check marking its own homework:
# whatever the prose selected would be exactly what the prose counted, for ever.
def _redealt_roof_count() -> int:
    """Anonymous roofs whose family an adjudication moved and an executor carried out.

    Counted off the RECIPE's own `redealt` record rather than off the adjudication
    ledger, and that is the whole point of counting it here: the ledger is derived
    over the town as it stands, so a verdict carried out vanishes from it the moment
    it works. The recipe is where the execution is permanent.
    """
    recipe = json.loads(
        (RECON_DIR / "1835_phase2_west_wolf_point_approaches.json").read_text())
    return len(recipe.get("redealt", {}).get("roofs", []))


SCOPE_SOURCES = {
    "register_1835.businesses[survival_liberty_required]": (
        _register_survival_liberty_count,
        "data/research/newspapers/register_1835.json, itself re-derived by "
        "tools/compile_register.py --check"),
    "register_1835.businesses[backdating_liberty_required]": (
        _register_backdating_liberty_count,
        "data/research/newspapers/register_1835.json, itself re-derived by "
        "tools/compile_register.py --check"),
    "businesses.records[reconstructed]": (
        _reconstructed_business_count,
        "data/businesses/authored/*.json, themselves re-derived by "
        "tools/reconstruct_businesses_1835.py --check"),
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
    "structures.records[brick_fabric]": (
        _brick_fabric_count,
        "data/structures/*.json, the layer's own construction attribute"),
    "structures.phases[roof_type_stated]": (
        _roof_covering_count,
        "data/structures/*.json, the layer's own roof_type attribute"),
    "structures.phases[log_or_fort_archetype]": (
        _log_and_fort_roof_count,
        "data/structures/*.json, the layer's own archetype attribute"),
    "phase2_west_wolf_point_approaches.placements[redealt]": (
        _redealt_roof_count,
        "data/reconstruction/1835_phase2_west_wolf_point_approaches.json, itself "
        "re-derived by tools/execute_roof_redeal.py --check"),
    **_stage_scope_sources(),
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


MINTS = ("persons", "attribute_blocks", "nothing")
DOSSIER = ROOT / "docs" / "RESEARCH" / "1835_resident_reconstruction.md"
STAGE_TABLE_HEADING = "## The stages at close"
STAGE_ROW = re.compile(r"^\|\s*`([a-z_]+)`\s*\|(.+)\|\s*$", re.M)


def _stage_household_count(stage: str) -> int:
    """Cards holding at least one person a stage minted.

    Not an enumeration: no liberty declares a `Scope:` in households, because the
    person is what a stage invents and the card is where it put them. It is here
    because the dossier's closing table prints both, and a number in a document
    nothing re-derives is a number that drifts.
    """
    n = 0
    for path in sorted(RESIDENTS_DIR.rglob("*.json")):
        try:
            doc = json.loads(path.read_text())
        except ValueError:
            continue
        if not isinstance(doc, dict):
            continue
        if any(isinstance(person, dict)
               and isinstance(person.get("reconstruction"), dict)
               and person["reconstruction"].get("stage") == stage
               for person in doc.get("persons") or []):
            n += 1
    return n


def check_stage_liberties(entries: list[dict], stages: list[dict] | None = None,
                          counts=None) -> list[str]:
    """Every reconstruction stage is admitted to by an entry, and the count agrees.

    The programme (T-1167) is the only authority under which a person graded
    `reconstructed` may be written, and each of its stages invents people. Until
    T-1399 which entry admitted which stage was a matter of prose: the programme
    carried a promise list naming six liberties `L-rc-persons`, `L-rc-families`,
    `L-rc-readmission` and so on, four of which were never the id of anything —
    the entries that kept those promises are L244, L242, L246, L250 and L255 —
    and nothing noticed, because nothing read the list. A promise nothing checks
    is a promise that ages.

    So the binding is declared, in `stages[].liberties`, and held here in BOTH
    directions. Forward: a stage that mints people names at least one entry, that
    entry exists, and one of its entries carries the `Scope:` that counts the
    stage. Backward: an entry may not claim a stage the programme has not declared
    it on, which is what stops the register from acquiring a second opinion about
    how many people a stage wrote. And `mints` is checked against the layer itself,
    so a stage that starts writing people — or stops — is red rather than silently
    exempt from both halves.
    """
    stages = programme_stages() if stages is None else stages
    counts = _stage_person_count if counts is None else counts
    problems: list[str] = []
    if not stages:
        return [f"the reconstruction programme declares no stages, so no liberty "
                f"can be held to one — expected them in "
                f"{PROGRAMME.relative_to(ROOT) if PROGRAMME.is_absolute() else PROGRAMME}"]

    by_id = {e["id"]: e for e in entries}
    declared_on: dict[str, str] = {}

    for stage in stages:
        key = stage.get("key") or "<unnamed>"
        mints = stage.get("mints")
        libs = stage.get("liberties")
        if mints not in MINTS:
            problems.append(f"stage {key}: `mints` is {mints!r}, not one of "
                            f"{', '.join(MINTS)} — it says what this stage writes "
                            f"that a liberty has to account for")
            continue
        if not isinstance(libs, list):
            problems.append(f"stage {key}: no `liberties` list. A stage names the "
                            f"entries in docs/LIBERTIES.md that admit its inventions, "
                            f"or declares `mints: nothing` and says why")
            continue
        for lid in libs:
            if lid not in by_id:
                problems.append(f"stage {key}: names liberty {lid}, which is not an "
                                f"entry in docs/LIBERTIES.md")

        minted = counts(key)
        if mints == "persons" and minted == 0:
            problems.append(f"stage {key}: declares `mints: persons` and no card in "
                            f"data/residents/ carries its stage key — either the "
                            f"stage has not run or the key has been renamed under it")
        if mints != "persons" and minted:
            problems.append(f"stage {key}: declares `mints: {mints}` and {minted} "
                            f"person(s) in data/residents/ carry its stage key. A "
                            f"stage that has started writing people owes a counted "
                            f"scope like the ones that always did")
        if mints != "persons" and not (stage.get("owes_no_person_scope") or "").strip():
            problems.append(f"stage {key}: mints no person and does not say why in "
                            f"`owes_no_person_scope` — the exemption is the one "
                            f"thing here nothing else can check")

        enumeration = stage_enumeration(key)
        declared_on[enumeration] = key
        claimants = [lid for lid in libs
                     if (by_id.get(lid, {}).get("scope") or {}).get("enumeration") == enumeration]
        if mints == "persons":
            if not libs:
                problems.append(f"stage {key}: minted {minted} people and names no "
                                f"liberty. Every invented person is admitted to by "
                                f"an entry or by nothing at all")
            elif not claimants:
                named = ", ".join(libs)
                problems.append(f"stage {key}: minted {minted} people and none of "
                                f"{named} carries '**Scope:** `{enumeration}`'. The "
                                f"entry says so in prose and the register cannot "
                                f"count prose")
        elif claimants:
            problems.append(f"stage {key}: mints {mints} and {', '.join(claimants)} "
                            f"claims a person scope for it")

    for e in entries:
        enumeration = (e.get("scope") or {}).get("enumeration")
        if not enumeration or not enumeration.startswith("residents.persons["):
            continue
        key = declared_on.get(enumeration)
        if key is None:
            continue          # not a stage enumeration — letter_list_only, civic_mint
        stage = next(s for s in stages if s.get("key") == key)
        if e["id"] not in (stage.get("liberties") or []):
            problems.append(
                f"{e['id']}: claims `{enumeration}`, and stage {key} does not name "
                f"it. The programme decides which entries admit a stage; an entry "
                f"that appointed itself would be a second opinion about how many "
                f"people the stage wrote")
    return problems


def check_stage_table(stages: list[dict] | None = None, text: str | None = None,
                      counts=None, households=None) -> list[str]:
    """The dossier's closing table prints the numbers this module derives.

    The tables are the half of T-1399 a person reads, and a table nothing
    re-derives is a table that is right on the day it is typed. They are checked
    HERE rather than in a module of their own because the numbers are the ones
    this module already derives for the scopes: a second derivation would be a
    second answer, and the day they disagreed there would be no way to tell which
    of them had drifted.
    """
    stages = programme_stages() if stages is None else stages
    counts = _stage_person_count if counts is None else counts
    households = _stage_household_count if households is None else households
    if text is None:
        try:
            text = DOSSIER.read_text()
        except OSError:
            return [f"the dossier {DOSSIER.name} is missing, so the closing table "
                    f"nothing else prints is missing with it"]
    problems: list[str] = []
    if STAGE_TABLE_HEADING not in text:
        return [f"the dossier has no '{STAGE_TABLE_HEADING}' section — the closing "
                f"table is where the programme states what each stage wrote"]
    body = text[text.index(STAGE_TABLE_HEADING) + len(STAGE_TABLE_HEADING):]
    # The stage table only. The tier tables below it are in subsections of their
    # own and have a backticked first cell too, so a search over the whole section
    # reads `attested` as a stage of the programme.
    sub = body.find("\n### ")
    if sub != -1:
        body = body[:sub]
    rows = {m.group(1): [c.strip() for c in m.group(2).split("|")]
            for m in STAGE_ROW.finditer(body)}

    for stage in stages:
        key = stage.get("key")
        row = rows.pop(key, None)
        if row is None:
            problems.append(f"the closing table has no row for stage {key}")
            continue
        if len(row) < 4:
            problems.append(f"the closing table's {key} row has {len(row) + 1} "
                            f"columns, not 5: stage, mints, persons, households, liberty")
            continue
        minted, seated = counts(key), households(key)
        want_p = f"{minted:,}" if stage.get("mints") == "persons" else "—"
        want_h = f"{seated:,}" if stage.get("mints") == "persons" else "—"
        if row[1] != want_p or row[2] != want_h:
            problems.append(
                f"the closing table says stage {key} wrote {row[1]} people in "
                f"{row[2]} cards; the layer holds {want_p} in {want_h}")
        cited = set(re.findall(r"L(?:\d+[a-z]?|-[a-z0-9-]+)", row[3]))
        named = set(stage.get("liberties") or [])
        if cited != named:
            problems.append(
                f"the closing table credits stage {key} to "
                f"{', '.join(sorted(cited)) or 'nothing'}; the programme names "
                f"{', '.join(sorted(named)) or 'nothing'}")
    for key in rows:
        problems.append(f"the closing table has a row for '{key}', which is not a "
                        f"stage of the reconstruction programme")
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
    problems.extend(check_stage_liberties(entries))
    problems.extend(check_stage_table())
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

    # --- the stage binding (T-1399) -----------------------------------------
    #
    # A synthetic programme and a synthetic register, for the reason the
    # specimen document exists: the committed pair is repaired, and an assertion
    # proved only on a repaired subject is an assertion proved on nothing. The
    # live pair is asserted below, which is the half a synthetic one cannot show.
    def stage(key, mints="persons", libs=(), why=None):
        row = {"key": key, "mints": mints, "liberties": list(libs)}
        if why:
            row["owes_no_person_scope"] = why
        return row

    def entry(lid, key=None):
        e = {"id": lid, "title": lid}
        if key:
            e["scope"] = {"enumeration": stage_enumeration(key), "count": 1}
        return e

    def blame(stages, entries, counts):
        return check_stage_liberties(entries, stages, lambda k: counts.get(k, 0))

    good = blame([stage("alpha", libs=["L90"])], [entry("L90", "alpha")], {"alpha": 1})
    check("a stage whose named entry carries its scope is clean", not good)

    check("a stage that mints people and names no liberty is refused",
          any("names no liberty" in m
              for m in blame([stage("alpha")], [], {"alpha": 1})))
    check("a stage naming an entry that does not exist is refused",
          any("not an entry" in m
              for m in blame([stage("alpha", libs=["L90"])], [], {"alpha": 1})))
    check("a stage whose entry admits it in prose and carries no Scope is refused",
          any("cannot count prose" in m
              for m in blame([stage("alpha", libs=["L90"])], [entry("L90")],
                             {"alpha": 1})))
    check("an entry claiming a stage the programme did not name it on is refused",
          any("does not name it" in m
              for m in blame([stage("alpha", libs=["L90"])],
                             [entry("L90", "alpha"), entry("L91", "alpha")],
                             {"alpha": 1})))
    check("a stage that says it mints nothing and has written people is refused",
          any("has started writing people" in m
              for m in blame([stage("alpha", "nothing", why="it reports")], [],
                             {"alpha": 1})))
    check("a stage that says it mints people and has written none is refused",
          any("has not run" in m
              for m in blame([stage("alpha", libs=["L90"])], [entry("L90", "alpha")],
                             {})))
    check("a stage exempt from a count and silent about why is refused",
          any("owes_no_person_scope" in m
              for m in blame([stage("alpha", "nothing")], [], {})))
    check("an unknown `mints` word is refused rather than read as an exemption",
          any("not one of" in m
              for m in blame([stage("alpha", "some")], [], {"alpha": 1})))
    check("a programme with no stages refuses every binding at once",
          len(blame([], [], {})) == 1)

    # The dossier's tables, the same way.
    TABLE = ("## The stages at close\n\n"
             "| stage | mints | persons | cards | liberty |\n"
             "| --- | --- | ---: | ---: | --- |\n"
             "| `alpha` | persons | 1,200 | 40 | **L90** |\n"
             "| `omega` | nothing | — | — | — |\n"
             "\n### The layer by tier\n\n| `attested` | 1 |\n")
    stages_t = [stage("alpha", libs=["L90"]), stage("omega", "nothing", why="reports")]
    counts_t = {"alpha": 1200}
    homes_t = {"alpha": 40}

    def blame_table(text, counts=counts_t, homes=homes_t, stages=stages_t):
        return check_stage_table(stages, text, lambda k: counts.get(k, 0),
                                 lambda k: homes.get(k, 0))

    check("a closing table that agrees with the layer is clean",
          not blame_table(TABLE))
    check("…and the tier tables under it are not read as stages",
          not any("attested" in m for m in blame_table(TABLE)))
    check("a table row whose count has drifted from the layer is refused",
          any("the layer holds" in m
              for m in blame_table(TABLE.replace("1,200", "1,100"))))
    check("a thousands separator is required, so 1200 does not pass as 1,200",
          any("the layer holds" in m
              for m in blame_table(TABLE.replace("1,200", "1200"))))
    check("a table crediting a stage to the wrong entry is refused",
          any("the programme names" in m
              for m in blame_table(TABLE.replace("**L90**", "**L91**"))))
    check("a stage missing from the table is refused",
          any("no row for stage omega" in m
              for m in blame_table(TABLE.replace("| `omega` | nothing | — | — | — |",
                                                 ""))))
    check("a table row naming no stage of the programme is refused",
          any("not a stage" in m
              for m in blame_table(TABLE.replace("`omega`", "`psi`"))))
    check("a dossier with no closing section at all is refused",
          len(blame_table("# a dossier that stops early\n")) == 1)

    # And the live pair.
    live_stages = programme_stages()
    minting = [s["key"] for s in live_stages if s.get("mints") == "persons"]
    live_entries, _ = parse(SOURCE.read_text(), {})
    bound = check_stage_liberties(live_entries)
    check(f"the committed programme's {len(live_stages)} stages are each admitted "
          f"to by an entry, and the {len(minting)} that mint people are counted "
          f"({', '.join(minting)})", not bound)
    check("…and the dossier's closing tables print the same numbers",
          not check_stage_table())

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
