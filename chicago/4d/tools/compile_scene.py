#!/usr/bin/env python3
"""Compile per-scene provenance sidecars from the dataset.

    python3 tools/compile_scene.py --scene 1835
    python3 tools/compile_scene.py --all
    python3 tools/compile_scene.py --all --check     # re-derive, change nothing

The renderer reads these, never the raw dataset. That is deliberate: the sidecar
is a flattened, resolved view of one structure at one date, with its citations
already joined in — so the walkthrough and the archival record cannot drift apart,
and the renderer never has to reimplement the phase-resolution rule.

"Cannot drift apart" was a statement about the design and not a check on it until
`--check` existed: the derived files are committed so the site needs no build step,
and a record edited without a recompile shipped a walkthrough quoting the previous
dataset. `tools/check.sh` re-derives them on every commit for the same reason it
re-derives the liberties — drift is a gate failure, not a discovery.

Pure Python, no Blender. See docs/GLB-CONTRACT.md § "The sidecar".
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))
from review_constraint import record_reason  # noqa: E402
from tiers import tier_ladder, tier_label  # noqa: E402


CHECK = False
DRIFT: list[str] = []

# Which write-up a reconstructed building's card points at, by the programme that
# raised it. A record with no reconstruction block is a researched building and
# keeps its own per-record dossier path.
RESEARCH_DOSSIER = {
    "inferred_anonymous": "docs/RESEARCH/inferred_infill_1835.md",
    "inferred_household": "docs/RESEARCH/residents_1835_inferred.md",
}

# T-0516. The dossier follows the programme that RAISED the roof, and after the
# retirement of 2026-09-02 that is no longer the same question as the status. The
# owner retired the reconstructed resident population and ruled its 31 roofs kept
# as anonymous stock, so they now read `inferred_anonymous` — but they were never
# dealt by an anonymous parcel, and sending them to the infill programme's write-up
# would put a visitor in front of a document about a deal that never dealt them.
# The phase is the durable answer, so the phase is what this keys on.
PROGRAMME_DOSSIER = {
    "phase2_inferred_households": "docs/RESEARCH/residents_1835_inferred.md",
}


def research_doc(structure: dict) -> str:
    """The dossier that covers this record, or `""` where none has been written.

    The path used to be asserted by convention — `docs/RESEARCH/<id>.md` for
    anything with no reconstruction block — and the convention is right about 302
    of 332 records and wrong about 30, which are documented buildings whose
    write-up nobody has done yet. The card rendered the guess as a link either
    way, so a third of the town's most interesting buildings offered a link that
    breaks (ROADMAP K26). Resolving it here rather than in the renderer is what
    lets a static card be honest about it: the compiler can see the repository
    and a browser on the deployed site cannot see even the file it is asking for.

    Emitting `""` rather than dropping the key keeps the sidecar one shape
    everywhere, which is the same rule `residents` follows.
    """
    block = structure.get("reconstruction") or {}
    path = PROGRAMME_DOSSIER.get(
        block.get("programme_phase"),
        RESEARCH_DOSSIER.get(block.get("status"),
                             f"docs/RESEARCH/{structure['id']}.md"))
    return path if (ROOT / path).exists() else ""


def load(p: Path):
    return json.loads(p.read_text())


def emit(path: Path, doc, *, compact: bool = False) -> None:
    """Write a derived file — or, under `--check`, prove the committed one is
    exactly what this compiler would write.

    `compact` drops the indentation. Every sidecar is read by a machine, but a
    building's sidecar is also read by a person with a diff in front of them, and
    the indentation is for that reader. `people.json` has 1,400 rows and no
    reader of that kind — it is a directory the browser filters — and indented it
    is 1.6 MB against 0.7 MB compact, so it is the one file written this way."""
    text = (json.dumps(doc, separators=(",", ":"), ensure_ascii=False) if compact
            else json.dumps(doc, indent=2, ensure_ascii=False)) + "\n"
    if not CHECK:
        path.write_text(text)
        return
    rel = path.relative_to(ROOT)
    if not path.exists():
        DRIFT.append(f"{rel} is missing")
    elif path.read_text() != text:
        DRIFT.append(f"{rel} is not what the dataset compiles to")


def vertical_anchor(archetype: str) -> str:
    """What this archetype's `y = 0` sits on — `terrain` or `water`.

    docs/GLB-CONTRACT.md pins the convention and says it is "declared per archetype";
    this reads that declaration off the parameter module rather than keeping a second
    list here, for the same reason `terrain_inputs_sha` has one definition: two copies
    agree until the day one of them matters. An archetype that declares nothing is
    placed against the terrain, which is what every building wants.

    Import failures are deliberately NOT fatal. A missing parameter module is already
    an error the staleness gate raises with a better message, and a sidecar compile is
    not the place to discover it.
    """
    gen = str(ROOT / "generators")
    if gen not in sys.path:
        sys.path.insert(0, gen)
    try:
        mod = __import__(f"archetypes.{archetype}_params", fromlist=["VERTICAL_ANCHOR"])
    except Exception:  # noqa: BLE001
        return "terrain"
    return getattr(mod, "VERTICAL_ANCHOR", "terrain")


def walk_surface_m(structure: dict, phase: dict):
    """The height, above this structure's own `y = 0`, of a surface a visitor may
    STAND on — or `None` for the 330 structures that have no such surface.

    Only bridges have one, and for a bridge it is the deck. The number is the
    generator's own `deck_height_m`, read off the resolved parameter object rather
    than recomputed here or measured off the GLB, for the same reason
    `vertical_anchor` above reads its declaration off the parameter module: the
    deck a visitor stands on and the deck the mesh draws have to be ONE number, and
    two definitions agree until the day one of them matters. `mesh_inputs` already
    imports these modules without Blender, so this costs the compile nothing.

    Why the renderer cannot just measure it. The deck IS a distinct primitive in the
    GLB, named by its material, so its top face is findable — but the material names
    are not part of docs/GLB-CONTRACT.md, and a renderer keyed on one would be
    reading a generator convention nobody promised to keep. The drawbridge also
    carries gallows frames five metres above its deck, so the structure's bounding
    box is not the answer either.

    Silent on failure for the same reason `vertical_anchor` is: a parameter module
    that will not import is the staleness gate's error to raise, with a better
    message than a sidecar compile could give.
    """
    arch = structure.get("archetype")
    if not arch:
        return None
    gen = str(ROOT / "generators")
    if gen not in sys.path:
        sys.path.insert(0, gen)
    try:
        mod = __import__(f"archetypes.{arch}_params", fromlist=["from_phase"])
        value = getattr(mod.from_phase(phase), "deck_height_m", None)
    except Exception:  # noqa: BLE001
        return None
    return round(float(value), 4) if value is not None else None


def resolve_phase(structure: dict, target: dt.date):
    """Exactly one phase must cover the date — the same rule the validator and
    the generator apply. Duplicated deliberately in three places is worse than
    duplicated in two, so if this grows further it moves to a shared module."""
    hits = []
    for ph in structure.get("phases", []):
        r = ph.get("documented_range", {})
        try:
            frm, to = dt.date.fromisoformat(r["from"]), dt.date.fromisoformat(r["to"])
        except (KeyError, ValueError):
            continue
        if frm <= target <= to:
            hits.append(ph)
    if len(hits) > 1:
        raise SystemExit(f"{structure['id']}: {len(hits)} phases cover {target}")
    return hits[0] if hits else None


#: Which fields of a source record a visitor is shown, and which stay in the
#: repository — declared, because the alternative is what happened for the life
#: of this project. `data/source.schema.json` grew four fields whose own
#: descriptions say they are written for a reader ("so an agent reaching for it
#: sees the limit before the citation"), and `cite()` never carried one of them,
#: so nothing anywhere read them. That fault is a third kind, after the two
#: STATUS § 28-30 found: not a field read and never emitted, and not a field
#: emitted and never read, but a field that never entered the interface at all.
#: Neither direction of `check_sidecar_contract` can see it, because a shape
#: unioned over what is emitted cannot report what was never offered.
#:
#: The set that CAN be enumerated is the schema, so the partition is over the
#: schema's own properties and `check_source_surface` fails on a property in
#: neither half. Adding a field to a source record now costs one line saying
#: whether a visitor sees it — which is the whole mechanism, and the reason this
#: lives beside `cite()` rather than in a document.
SOURCE_FIELD_SURFACE: dict[str, str] = {
    # --- shown on the citation line -----------------------------------------
    "citation": "visitor: the citation itself",
    "url": "visitor: where to read it",
    "archived_url": "visitor: whether it can be re-read at all",
    "tier": "visitor: the rung, with tier_label supplying the words",
    "transcribes": "visitor: WHY the rung is what it is when the URL is a modern page",
    "carries_no_document": "visitor: the reading that established the page reprints nothing",
    "what_it_supplies": "visitor: what this source can legitimately be used for",
    "what_it_does_not_supply": "visitor: what it is assumed to give and does not",
    # --- kept in the repository ---------------------------------------------
    "id": "internal: the join key; the citation text is what a person reads",
    "type": "internal: machinery, and the tier label says the same thing in words",
    "author": "internal: already inside the citation string",
    "date": "internal: already inside the citation string",
    "describes_date": "internal: the phase's documented_range is the visitor's form of this",
    "repository": "internal: already inside the citation string",
    "locator": "internal: already inside the citation string",
    "rights_status": "internal: governs asset derivation, not the reading of a claim",
    "rights_note": "internal: same",
    "rights_checked": "internal: same",
    "asset_use": "internal: same",
    "verified": "internal: a workflow flag; an unverified source may not be cited anyway",
    "access_notes": "internal: fetch problems, addressed to whoever fetches next",
    "note": "internal: the working note; its reader-facing halves are the four fields above",
}

#: The keys `cite()` may take from a source record, derived from the partition
#: rather than typed twice. `tier_label` is computed here and is not a schema
#: property, so it is named on its own.
VISITOR_SOURCE_FIELDS: tuple[str, ...] = tuple(
    k for k, why in SOURCE_FIELD_SURFACE.items() if why.startswith("visitor")
)


def cite(source_ids, sources: dict) -> list[dict]:
    """Join source ids to the citation the visitor reads. One shape, one place:
    the popup and the exclusions list quote the same record the same way.

    `tier_label` travels with the number because the number on its own says
    nothing. The card has printed "tier 4" since it was written, next to a
    citation, at a visitor who has no table to look it up in — and the whole
    argument of this panel is that a person can judge the evidence for
    themselves. The words come out of `data/source.schema.json` through
    `tools/tiers.py`, the same ladder `check_evidence_ladder` enforces, so the
    rung a value is held to and the rung a visitor is shown cannot come apart.

    And the rung's REASON travels with it, which it did not. A rung is a
    judgement about a document, and on ten of these records the document is not
    the page: `chicagology_lastwardance` is rung 2 because it reprints the
    *Chicago Tribune* of 14 August 1910 printing John Dean Caton's own
    recollection, and a visitor following that citation arrived at a modern
    blog stamped "tier 2 · near-primary recollection" with nothing on the card
    saying why. That is the ladder made to look like an over-grade by the one
    field that would have explained it. `transcribes` and its opposite number
    `carries_no_document` are the reading that fixed the rung, and they are on
    the line now.

    So are the source's own stated limits. `hathaway_1834` says in its record
    that it does NOT supply building footprints — a claim that reached this
    project's brief before anyone opened the scan, and the correction stayed in
    the repository. A source shown without its limits is the one thing this
    panel is not for.

    The four new fields are omitted when a record does not carry them, rather
    than emitted empty: a source with no stated limit should render nothing on
    the card, not an empty heading, and thirteen of twenty-nine records carry
    them. The four that every citation has kept their unconditional shape, so a
    renderer reading `c.tier` still reads a key that is always there.
    """
    ladder = tier_ladder()
    always = ("citation", "url", "archived_url", "tier")
    out = []
    for s in sorted(source_ids):
        if s not in sources:
            continue
        rec = sources[s]
        c: dict = {"source_id": s}
        for key in always:
            c[key] = rec.get(key, "") if key != "tier" else rec.get("tier")
        c["tier_label"] = tier_label(rec.get("tier"), ladder)
        for key in VISITOR_SOURCE_FIELDS:
            if key not in always and rec.get(key):
                c[key] = rec[key]
        out.append(c)
    return out


def compile_exclusions(scene_id: str, scene: dict, target: dt.date,
                       sources: dict, exclusions: dict, outdir: Path,
                       in_scene: dict | None = None) -> int:
    """The structures researched and deliberately LEFT OUT of this scene.

    `data/exclusions.json` is the authored research record and has lived only in
    the repository, where a visitor cannot read it. A town of eight buildings
    looks the same whether a structure is missing because nobody looked, because
    the evidence dates it after the scene, or because it had already come down —
    and those are three completely different statements about the research. This
    derives the second and third kinds, with their citations joined, so the
    walkthrough can say which it is.

    Filtered by the scene's own year rather than shipped wholesale: an entry
    whose `earliest_scene` this scene has reached is not an exclusion here, and
    the validator reports that contradiction rather than this compiler hiding it.
    """
    in_scene = in_scene or {}
    year = target.year
    entries = []
    for ex in exclusions.get("excluded", []):
        earliest = str(ex.get("earliest_scene") or "")
        if earliest.isdigit() and int(earliest) <= year:
            continue
        entries.append({
            "id": ex.get("id"),
            "name": ex.get("name", ex.get("id")),
            "reason": ex.get("reason", ""),
            "detail": ex.get("detail", ""),
            "earliest_scene": ex.get("earliest_scene"),
            "citations": cite(ex.get("sources", []) or [], sources),
        })

    uncertain = compile_watch_list(scene_id, sources, exclusions, in_scene)

    emit(outdir / "exclusions.json", {
        "scene": scene_id,
        "target_date": scene["target_date"],
        # What the list covers, stated in the derived file so the renderer quotes
        # it rather than composing its own claim about the dataset's completeness.
        "standard": "Structures this project researched and deliberately left out of "
                    "this scene, with the evidence that dates them. It is not a list of "
                    "everything missing: most of the town is simply not built yet.",
        "excluded": entries,
        # T-0305: this sentence counted, and it had gone wrong the way the
        # paraphrase it replaced went wrong. "One of them is standing in front of
        # you" was true of four entries and stopped being true at the second
        # standing one — the New York House, on 2026-08-29 — a day before a fifth
        # entry was added and nobody read it. It counts nothing now: each entry
        # carries its own `standing` flag and the chip beside it says which.
        "uncertain_standard": "Structures whose status on this date is genuinely OPEN — "
                              "neither built with confidence nor ruled out. They are the "
                              "third category, and each one says whether it is standing in "
                              "front of you or was never found on the ground.",
        "uncertain": uncertain,
    })
    return len(entries)


def compile_watch_list(scene_id: str, sources: dict, exclusions: dict,
                       in_scene: dict) -> list[dict]:
    """The open questions, which are neither a building nor an exclusion.

    A visitor can be told what stands and, since the exclusions shipped, what was
    researched and left out. Between those sits a third statement the walkthrough
    could not make: researched, and still open. Three of the five are empty
    ground for the same reason a gap is empty — nobody could establish whether
    the building was there — and two are standing in the scene, each with an
    `inferred` claim carrying the doubt: the New York House's side of Wells, and
    (T-0305) the corner S. B. Cobb's saddlery stands on. Putting the standing
    ones under "what is not here" would be false about them, which is why they
    get their own section rather than a footnote on somebody else's.

    `standing` is derived from the scene rather than read off the entry: whether
    a structure resolves into 1 July 1835 is a fact about the dataset and the
    date, and an entry that asserted it would be one more thing to drift.
    """
    out = []
    for item in exclusions.get("watch_list", []):
        wid = item.get("id")
        phase = in_scene.get(wid)
        entry = {
            "id": wid,
            "name": item.get("name", wid),
            "question": item.get("question", ""),
            "consequence": item.get("consequence", ""),
            "standing": phase is not None,
            "no_source_record": item.get("no_source_record", ""),
            "dossier": item.get("dossier", {}),
            "citations": cite(item.get("sources", []) or [], sources),
        }
        # For the one that IS standing, name the claim on its own record that
        # carries the doubt and repeat that claim's grade — so the section and
        # the provenance card cannot describe the same uncertainty differently.
        ref = (item.get("carried_by") or "").strip()
        if phase is not None and ref.count(".") == 1:
            _, field = ref.split(".")
            claim = phase.get(field) or {}
            entry["carried_by"] = ref
            entry["carried_confidence"] = claim.get("confidence", "")
        out.append(entry)
    return out


# Keys that are the claim's machinery rather than part of what it states: the
# grade itself, the evidence behind it, the reasoning, the names already shown in
# the heading, and the `mesh` map, which is a statement ABOUT the figures
# rather than one of them (it is attached to the rows below instead). Everything
# else in a block is a figure the spec authored and a visitor is entitled to read.
#
# `zone` is in the heading exactly as `id` and `label` are — a surface-material
# block is titled by it — so it is machinery here for the same reason.
GROUND_META_KEYS = {"confidence", "bed_confidence", "sources", "note", "label",
                    "id", "zone", "mesh"}

# The blocks of `terrain_spec.json`, in the order a visitor should meet them:
# what the water is, what it does under the surface, how the land leaves it, what
# each division stands at, and what was laid on top. Order is authored because
# reading order is a piece of writing; membership is not — anything inside these
# blocks that grades itself is surfaced, so a zone added to the spec appears here
# the day it is added.
GROUND_GROUPS = [
    ("water", "the water surface"),
    ("reaches", "the channel beds"),
    ("channel_profile", "the channel cross-section"),
    ("bank", "the bank"),
    ("divisions", "the three divisions"),
    ("marsh_strips", "the marshy shore"),
    ("swales", "the prairie swales"),
    ("watercourses", "the watercourses"),
    ("approaches", "the bridge approaches"),
    ("micro_relief", "the surface texture"),
    ("surface_materials", "what the ground is made of"),
]


def ground_fields(block: dict) -> list[dict]:
    """The figures a spec block states, as the block states them.

    No prose is composed here. A division says `near_ft: 2.4` and the card says
    `near_ft 2.4`, because the moment this function starts writing "rising gently
    from the bank" it is making a claim the record does not.

    Nested structure is skipped rather than flattened: a swale's `line` is a
    polyline of eleven numbers that tells a reader nothing, and the alignment it
    describes is exactly the thing that entry admits is invented.

    A field the terrain generator does not read carries its `mesh:` declaration
    here, on the row, for the reason the provenance card puts the
    same mark beside a building's attribute: a figure a visitor is shown with a
    confidence chip over it, and no vertex behind it, reads as something they are
    looking at. The declaration is authored on the block, in a map keyed by field
    name, and travels to the row so the panel cannot show one without the other.
    """
    declared = block.get("mesh") or {}
    out = []
    for key, value in block.items():
        if key in GROUND_META_KEYS or key.endswith("_note"):
            continue
        if isinstance(value, (dict, type(None))):
            continue
        if isinstance(value, list):
            if len(value) > 4 or any(isinstance(v, (list, dict)) for v in value):
                continue
        field = {"key": key, "value": value}
        if isinstance(declared, dict) and declared.get(key):
            field["mesh"] = declared[key]
        out.append(field)
    return out


def ground_claim(group: str, path: str, block: dict, sources: dict) -> dict | None:
    """One graded statement the ground makes about itself, joined to its evidence.

    A block earns a card by carrying a confidence, which is the same rule the
    provenance popup applies to a building's attributes: a value with a grade on
    it is a claim, and a claim a visitor cannot read is one this project has not
    really made. `channel_profile` grades itself under `bed_confidence`, so the
    key travels with the claim rather than being normalised away — the spec is a
    generator input whose bytes are hashed into the terrain's staleness, and
    tidying its vocabulary would re-stale the ground for a rename.
    """
    key = "confidence" if "confidence" in block else (
        "bed_confidence" if "bed_confidence" in block else None)
    if key is None:
        return None
    notes = [str(block[k]) for k in block if k == "note" or k.endswith("_note")]
    return {
        "id": path,
        "group": group,
        "label": (block.get("label") or block.get("id") or block.get("zone")
                  or path.split(".")[-1]),
        "confidence": block[key],
        "confidence_key": key,
        "fields": ground_fields(block),
        "sources": block.get("sources", []) or [],
        "citations": cite(block.get("sources", []) or [], sources),
        "notes": notes,
    }


def ground_claims(spec: dict, sources: dict) -> list[dict]:
    """Every graded statement in one epoch's terrain spec, in reading order.

    One enumeration, two callers — this compiler, which puts the claims on the
    Evidence panel, and `tools/validate.py`, which holds them to the citation
    rule. A gate walking its own copy of the spec would check a set of claims
    that could quietly stop being the set a visitor reads, which is the drift
    this project keeps closing in other places.
    """
    claims = []
    for group, group_label in GROUND_GROUPS:
        block = spec.get(group)
        if isinstance(block, dict):
            claim = ground_claim(group_label, group, block, sources)
            if claim:
                claims.append(claim)
        elif isinstance(block, list):
            for i, item in enumerate(block):
                if not isinstance(item, dict):
                    continue
                key = item.get("id") or item.get("zone") or i
                claim = ground_claim(group_label, f"{group}.{key}", item, sources)
                if claim:
                    claims.append(claim)
    return claims


def compile_residents_sources(scene_id: str, sources: dict, outdir: Path) -> int:
    """The citations the residents layer stands on, joined once for the panel.

    ROADMAP K52, and the argument is `compile_fauna_sources`'s exactly. What a
    household record carries is a list of `source_id`s and a bare id on a card is
    not a citation, so the join is done here, where every other join in this
    project is done, and `renderers/web/js/citations.js` renders it.

    THE DIFFERENCE FROM FAUNA IS THE SHAPE OF THE READ. The browser fetches the
    manifest and then one household record per row a visitor opens, so this file
    must cover every household — not only the ones a building sidecar reaches.
    It carries no resident figure of its own: the people are read from
    `data/residents/`, and a census of which figures reach a visitor must not
    have two answers to the same question.
    """
    cited: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "sources" and isinstance(value, list):
                    cited.update(str(v) for v in value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    index_path = DATA / "residents" / "index.json"
    if not index_path.exists():
        return 0
    index = load(index_path)
    walk(index)
    for entry in index.get("households", []):
        household_path = DATA / "residents" / entry.get("file", "")
        if household_path.exists():
            walk(load(household_path))
    # T-0442 keeps candidate identities beside, not inside, authoritative
    # household records. They still need the same citation join when a visitor
    # opens a researched person's card.
    research_path = DATA / "residents" / "research_pilot.json"
    if research_path.exists():
        walk(load(research_path))
    # T-0569 keeps Norris's 1844 directory beside the household records for the
    # same reason, and its rows cite the volume. A citation join that stopped at
    # the records would leave 67 cards quoting a bare source id.
    directory_path = DATA / "residents" / "directory_1844.json"
    if directory_path.exists():
        walk(load(directory_path))

    citations = cite(sorted(cited), sources)
    emit(outdir / "residents_sources.json", {
        "scene": scene_id,
        "standard": "Every source the household records cite, joined once so the people "
                    "section of the Evidence panel quotes a source exactly the way the "
                    "building card and the exclusions list do.",
        "citations": {c["source_id"]: c for c in citations},
    })
    return len(citations)


#: Honorifics and suffixes a name may END in, which are not the surname. "John
#: Bates Jr." is a Bates; "Reynolds John Hon." is a Reynolds. The letter-list
#: transcriptions carry these in the order the paper printed them, which is not
#: always forename-first.
_NOT_A_SURNAME = {
    "jr", "sr", "sen", "jun", "miss", "mrs", "mr", "hon", "esq", "rev", "dr",
    "col", "capt", "maj", "gen", "win", "wm", "jas", "jno", "chas", "thos",
    "unnamed",
}
#: Words a placeholder entry ends in: "Mark Beaubien's family, unnamed", "The four
#: Temple children". Sorting those under F and C would scatter a household's
#: admissions away from the household; the id's leading token names it.
_PLACEHOLDER_WORDS = {"family", "household", "children", "wife", "rest", "member"}
#: A particle that travels with the surname: "St Cyr", "Van Horne", "De Vries".
_PARTICLES = {"st", "st.", "van", "von", "de", "du", "le", "la", "mc", "mac", "o'"}


def surname_of(name: str, person_id: str) -> str:
    """The word a directory sorts this person under, lower-cased and diacritics
    folded — derived from the name, never typed.

    Last word after stripping a parenthetical ("Billy Caldwell (Sauganash)"), a
    trailing comma clause ("Mark Beaubien's family, unnamed" keeps its first
    clause) and trailing honorifics; a particle before it is kept ("St Cyr"). A
    placeholder entry — "the rest of the Robinson household" — falls back to the
    record id's leading token, which the mint writes as the surname.
    """
    import re
    import unicodedata

    def fold(s: str) -> str:
        s = unicodedata.normalize("NFD", s)
        return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()

    s = re.sub(r"\([^)]*\)", "", str(name or ""))
    s = s.split(",")[0].strip()
    tokens = [t for t in s.split() if t]
    while tokens and fold(tokens[-1]).rstrip(".") in _NOT_A_SURNAME:
        tokens.pop()
    last = fold(tokens[-1]).strip(".") if tokens else ""
    id_token = fold(str(person_id or "").split("_")[0])
    if not last or last in _PLACEHOLDER_WORDS or not re.search(r"[a-z]", last):
        return id_token or last
    if len(tokens) >= 2 and fold(tokens[-2]) in _PARTICLES:
        return f"{fold(tokens[-2]).rstrip('.')} {last}"
    return last


def arrival_year(value) -> int | None:
    """`1826`, `1835-07-01` → the year; anything else → None. The household's
    `arrival.value` is a string in two shapes (a bare year, an ISO date), and the
    directory's year pills need one integer per row."""
    m = __import__("re").match(r"^\s*(\d{4})", str(value or ""))
    return int(m.group(1)) if m else None


#: The person-level evidence arrays, in the order `residents.js` shows them, plus
#: the biographical block. The row carries only WHICH kinds a person has: the
#: appearances themselves stay on the household record, which the card fetches.
PERSON_EVIDENCE_KINDS = (
    ("press_evidence", "press"),
    ("civic_evidence", "civic"),
    ("book_evidence", "book"),
    ("church_evidence", "church"),
    ("census_evidence", "census"),
    ("biographical_evidence", "biographical"),
)

#: How a person came to be in this town, as ONE word a row can be marked by. The
#: flags are not exclusive — 85 civic-mint people also carry the projected
#: subtype — so this is a precedence, weakest evidence first, and the filter in
#: `people.js` reads the underlying flags rather than this word.
HOW_KNOWN = ("documented", "letter_list", "civic_mint", "projected")


def how_known(person: dict) -> str:
    if person.get("letter_list_only"):
        return "letter_list"
    if person.get("civic_mint"):
        return "civic_mint"
    if person.get("resident_subtype") == "projected_resident":
        return "projected"
    return "documented"


#: How many role labels a LIST row carries. A person's roles live on the record
#: and the card reads them from there; the row needs enough to label and to
#: search, which for this corpus's widest career (five roles) is all of them,
#: and a cap keeps a future reading from silently fattening 1,282 rows.
ROLE_LABELS_ON_ROW = 5


def role_year(role: dict) -> int | None:
    """The year a role's bound starts in — `1833-11` → 1833 — or its end where it
    has no start, or None where the evidence dates it to nothing. The list prints
    ONE year beside a role word because a row is one line; the card prints the
    whole bound at its own precision."""
    for key in ("from", "to"):
        m = __import__("re").match(r"^\s*(\d{4})", str(role.get(key) or ""))
        if m:
            return int(m.group(1))
    return None


def role_word(role: dict) -> str | None:
    """The controlled word where the source's wording has been adjudicated into
    the vocabulary, the wording AS PRINTED where it has not (T-1254 is where the
    rest are ruled on). One of the two is always present on a role."""
    return role.get("role") or role.get("as_printed") or None


def role_row_view(person: dict) -> dict:
    """The roles of one person, in the shape a LIST needs: labels to print, words
    to search, and the two counts a filter tests.

    `persons[].roles[]` is the canonical dated record of a trade, a profession or
    an office (index.json `_roles_doc`), and 262 people carry 267 of them — 127
    reaching 1 July 1835 and 140 not. The singular `occupation` view only ever
    showed the first kind, so a man printed as a brickmaker in 1839 read on the
    directory row as a person with no trade at all. The row carries the label and
    the search words; the dated timeline, its precision, how it was dated, its
    note and its sources stay on the record, which the card fetches.

    Sorted by the year the bound opens, undated last, so a row's labels and the
    card's timeline read in the same order.
    """
    roles = [r for r in (person.get("roles") or []) if isinstance(r, dict)]
    if not roles:
        return {}
    ordered = sorted(roles, key=lambda r: (role_year(r) is None, role_year(r) or 0,
                                           str(role_word(r) or "")))
    labels = []
    words_seen: list[str] = []
    for role in ordered:
        word = role_word(role)
        if len(labels) < ROLE_LABELS_ON_ROW:
            labels.append({
                "word": word,
                "kind": role.get("kind"),
                "year": role_year(role),
                "at_scene_date": bool(role.get("covers_scene_date")),
            })
        for token in (role.get("role"), role.get("as_printed")):
            if token and str(token) not in words_seen:
                words_seen.append(str(token))
    return {
        "roles": len(roles),
        "roles_at_scene_date": sum(1 for r in roles if r.get("covers_scene_date")),
        "role_labels": labels,
        "role_words": words_seen,
    }


def compile_people(scene_id: str, outdir: Path) -> int:
    """One row per PERSON, flattened from the 1,380 household records, so the
    drawer's People section and its Go-to list can search a town of 1,404 without
    a fetch each.

    `data/residents/index.json` is a manifest of HOUSEHOLDS: it summarises a
    record for the household browser and says nothing about the people in it
    beyond a grade tally. A directory is the other axis — a visitor looks for a
    surname, a trade, a division, a year — and every one of those figures lives
    on the person or on the household record around them, which the browser
    only fetches when a row is opened. Fetching 1,380 files to build a search
    index in the browser is not a design; compiling the flat view here, beside
    every other join this project does, is.

    THE ROW IS A POINTER, NOT A COPY OF THE RECORD. It carries what a list needs
    to sort, filter and label — name, surname, household, grade, trade, division,
    the arrival bound and its precision, the flags that say how the person is
    known, which building they lived or worked at — and the household `file`, so
    the card fetches the record itself and renders it with the same code the
    household browser uses. The notes, the appearances and the citations stay on
    the record: a figure quoted twice is a figure that drifts, and the census in
    `tools/measure_layer_reads.py` reads the record's own text.

    AND THE ROW SAYS WHAT THE SINGULAR FIELD CANNOT (T-1255). `occupation` is a
    generated view of the roles that cover 1 July 1835, so a person whose only
    dated role is a trade printed in 1839 carries no trade on the row at all —
    262 people hold 267 roles and 140 of those roles are outside the scene
    window. `role_row_view` above puts the labels, the search words and the two
    counts a filter tests on the row, marked by whether each role reaches the
    scene date; the dated timeline itself stays on the record.

    `occupation` is `null` where the record says `none_recorded` (1,270 of them).
    That is the same fact — the ABSENCE of a record, which the occupation note
    on the card explains — in the shape a filter can test, and the row keeps the
    attribute's confidence beside it so the absence is still graded.

    Sorted by surname then name, with the surname derived (`surname_of`) rather
    than typed. Emitted through `emit()` so `--check` holds it to the dataset
    like every sidecar.
    """
    import unicodedata

    index_path = DATA / "residents" / "index.json"
    if not index_path.exists():
        return 0
    index = load(index_path)
    vocab = index.get("vocabulary", {}) or {}
    manifest_counts = index.get("counts", {}) or {}

    def fold(s) -> str:
        s = unicodedata.normalize("NFD", str(s or ""))
        return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()

    def value_of(block):
        return block.get("value") if isinstance(block, dict) else block

    rows: list[dict] = []
    households = 0
    for entry in index.get("households", []):
        rel = entry.get("file", "")
        path = DATA / "residents" / rel
        if not path.exists():
            continue
        hh = load(path)
        households += 1
        arrival = hh.get("arrival") or {}
        lives = hh.get("lives_at") or {}
        works = hh.get("works_at") or {}
        for person in hh.get("persons", []) or []:
            occ = person.get("occupation") or {}
            occ_value = occ.get("value")
            returns = sorted(str(d) for d in (person.get("letter_list_returns") or []))
            age = person.get("age_on_scene_date") or {}
            born = person.get("birth_year") or {}
            rows.append({
                "id": person.get("id"),
                "name": person.get("name"),
                "household": hh.get("id"),
                "household_name": hh.get("name"),
                "file": rel,
                "relationship": person.get("relationship"),
                "grade": person.get("grade"),
                "occupation": None if occ_value in (None, "", "none_recorded") else occ_value,
                "letter_list_only": bool(person.get("letter_list_only")),
                "civic_mint": bool(person.get("civic_mint")),
                "resident_subtype": person.get("resident_subtype"),
                "how_known": how_known(person),
                "division": hh.get("division"),
                "arrival_year": arrival_year(arrival.get("value")),
                "arrival_precision": arrival.get("precision"),
                "present": (hh.get("present_on_scene_date") or {}).get("value"),
                "lives_at": lives.get("value"),
                "works_at": works.get("value"),
                **role_row_view(person),
            })

    rows.sort(key=lambda r: (surname_of(r["name"], r["id"]), fold(r["name"]), str(r["id"])))

    def tally(key):
        counts: dict = {}
        for r in rows:
            v = r.get(key)
            if v is None:
                continue
            counts[v] = counts.get(v, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: str(kv[0])))

    occupations = tally("occupation")
    by_grade = {g: sum(1 for r in rows if r["grade"] == g)
                for g in (vocab.get("grades") or ["attested", "inferred", "reconstructed"])}
    divisions = {d: sum(1 for r in rows if r["division"] == d)
                 for d in (vocab.get("divisions") or sorted(tally("division")))}
    presence = {p: sum(1 for r in rows if r["present"] == p)
                for p in (vocab.get("presence") or sorted(tally("present")))}
    known = {
        "documented": sum(1 for r in rows if not r["letter_list_only"] and not r["civic_mint"]
                          and r["resident_subtype"] != "projected_resident"),
        "letter_list": sum(1 for r in rows if r["letter_list_only"]),
        "civic_mint": sum(1 for r in rows if r["civic_mint"]),
        "projected": sum(1 for r in rows if r["resident_subtype"] == "projected_resident"),
    }
    with_address = sum(1 for r in rows if r["lives_at"] or r["works_at"])

    emit(outdir / "people.json", {
        "scene": scene_id,
        "standard": "One row per person in data/residents/, flattened from the household "
                    "records so the People section and the Go-to list can search the town "
                    "without a fetch each; the row points at its household file, and the "
                    "record itself is what a card renders.",
        "counts": {
            "people": len(rows),
            "households": households,
            "manifest_persons": manifest_counts.get("persons"),
            "letter_list_only": known["letter_list"],
            "civic_mint": known["civic_mint"],
            "projected_residents": known["projected"],
            "documented": known["documented"],
            "by_grade": by_grade,
            "by_division": divisions,
            "by_presence": presence,
            "by_arrival_year": {str(k): v for k, v in sorted(tally("arrival_year").items())},
            "with_address": with_address,
            "with_lives_at": sum(1 for r in rows if r["lives_at"]),
            "with_works_at": sum(1 for r in rows if r["works_at"]),
            "with_occupation": sum(1 for r in rows if r["occupation"]),
            "with_roles": sum(1 for r in rows if r.get("roles")),
            "roles": sum(r.get("roles", 0) for r in rows),
            "with_a_role_at_scene_date": sum(1 for r in rows if r.get("roles_at_scene_date")),
            "with_every_role_off_scene_date": sum(
                1 for r in rows if r.get("roles") and not r.get("roles_at_scene_date")),
        },
        "vocabulary": {
            "occupations": [{"value": k, "count": v} for k, v in occupations.items()],
            "divisions": list(vocab.get("divisions") or divisions.keys()),
            "grades": list(vocab.get("grades") or by_grade.keys()),
            "presence": list(vocab.get("presence") or presence.keys()),
            "relationships": list(vocab.get("relationships") or sorted(tally("relationship"))),
            "arrival_precision": list(vocab.get("arrival_precision") or sorted(tally("arrival_precision"))),
            "how_known": list(HOW_KNOWN),
            "role_kinds": list(vocab.get("role_kinds") or []),
            "evidence_kinds": [label for _, label in PERSON_EVIDENCE_KINDS],
        },
        "people": rows,
    }, compact=True)
    return len(rows)


def compile_fauna_sources(scene_id: str, sources: dict, outdir: Path) -> int:
    """The citations the fauna layer stands on, joined once for the walkthrough.

    ROADMAP K51. `data/fauna/` is authored research and the renderer now reads it
    straight — the zone records and the manifest are fetched by the browser as
    they are committed, which is what makes the read map in
    `tools/measure_layer_reads.py` scannable at all. What a zone record carries
    is a list of `source_id`s, and a bare id on a card is not a citation: this
    project's own argument is that a visitor should be able to judge the
    evidence, and `renderers/web/js/citations.js`'s single citation renderer
    wants the joined record — the rung, the words for the rung, what the page
    reprints and the source's own stated limits.

    So the join is done here, where every other join in this project is done, and
    nowhere else. The fauna layer cites seven sources today; the file is keyed by
    id because a species reaches it by id, and it carries no fauna figure of its
    own — the animals are read from `data/fauna/`, not from here, and the census
    that counts which figures reach a visitor must not have two answers.
    """
    cited: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "sources" and isinstance(value, list):
                    cited.update(str(v) for v in value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    index_path = DATA / "fauna" / "index.json"
    if not index_path.exists():
        return 0
    index = load(index_path)
    walk(index)
    for entry in index.get("zones", []):
        zone_path = DATA / "fauna" / entry.get("file", "")
        if zone_path.exists():
            walk(load(zone_path))

    citations = cite(sorted(cited), sources)
    emit(outdir / "fauna_sources.json", {
        "scene": scene_id,
        "standard": "Every source the animal records cite, joined once so the wildlife "
                    "section of the Evidence panel quotes a source exactly the way the "
                    "building card and the exclusions list do.",
        "citations": {c["source_id"]: c for c in citations},
    })
    return len(citations)


def compile_flora_sources(scene_id: str, sources: dict, outdir: Path) -> int:
    """The citations the plant records stand on, joined once for the panel.

    T-0281, and the argument is `compile_fauna_sources`'s exactly. `data/flora/`
    is authored research and the browser fetches it as committed — the manifest
    and each zone record — which is what keeps the read map in
    `tools/measure_layer_reads.py` scannable. What a zone and each of its species
    carry is a list of `source_id`s, and a bare id on a card is not a citation.

    The plant records are the THIRD layer to need this join and the second to
    need it twice over: a species cites its own sources and the community it
    stands in cites others for its extent, so the file is keyed by id and both
    reads come out of the one fetch. It carries no plant figure of its own — the
    densities are read from `data/flora/`, and the census that counts which
    figures reach a visitor must not have two answers to one question.
    """
    cited: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "sources" and isinstance(value, list):
                    cited.update(str(v) for v in value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    index_path = DATA / "flora" / "index.json"
    if not index_path.exists():
        return 0
    index = load(index_path)
    walk(index)
    for entry in index.get("zones", []):
        zone_path = DATA / "flora" / entry.get("file", "")
        if zone_path.exists():
            walk(load(zone_path))

    citations = cite(sorted(cited), sources)
    emit(outdir / "flora_sources.json", {
        "scene": scene_id,
        "standard": "Every source the plant records cite, joined once so the plants "
                    "section of the Evidence panel quotes a source exactly the way the "
                    "building card and the wildlife list do.",
        "citations": {c["source_id"]: c for c in citations},
    })
    return len(citations)


def compile_flora_clamp(scene_id: str, outdir: Path) -> int:
    """The declared cost of the forb lattice's ceiling, carried to the browser.

    T-0281's second half, and the reason it is a COMPILE rather than a copy in
    `tools/publish.sh`. `tools/forb_clamp_baseline.json` is the declaration
    T-0019 made and `node tools/measure_sward_draw.mjs --gate` holds: every
    (community, stratum, side) the ceiling binds, with the density its records
    ask for and the share of it the lattice can carry. It lives under `tools/`
    because it is a gate's baseline, and `tools/` is not published — so a card
    wanting those figures had two dishonest options and one honest one.

    The dishonest ones are typing the table into the renderer, which is what
    docs/LIBERTIES.md L186 already does and which goes stale the first time a
    flora record moves, and copying the file into `data/` by hand, which is the
    same staleness with an extra file to forget. The honest one is this: derive
    it where every other derived file in this project is derived, so
    `tools/compile_scene.py --check` — which `tools/check.sh` runs — fails the
    moment the committed sidecar stops matching the declaration behind it. The
    figures a visitor reads and the figures the gate holds cannot drift apart
    without the build going red.

    Nothing is recomputed here and nothing may be: this reads the declaration and
    carries it. A second calculation of the same share would be a second answer
    to the question `measure_sward_draw.mjs` already owns.
    """
    declared = ROOT / "tools" / "forb_clamp_baseline.json"
    if not declared.exists():
        return 0
    doc = load(declared)
    emit(outdir / "flora_clamp.json", {
        "scene": scene_id,
        "standard": "The forb lattice's ceiling as tools/forb_clamp_baseline.json declares "
                    "it, carried unchanged so the plants section can state the share of "
                    "each record the scene is able to draw rather than typing a table. "
                    "Nothing here is recalculated: tools/measure_sward_draw.mjs --gate "
                    "owns these numbers and tools/compile_scene.py --check holds this copy "
                    "to them.",
        "declared_by": "tools/forb_clamp_baseline.json",
        "measured": doc.get("measured"),
        "stand": doc.get("stand"),
        "cell_m": doc.get("cell"),
        "per_cell": doc.get("perCell"),
        "slot_area_m2": doc.get("slotAreaM2"),
        "ceiling_per_m2": doc.get("ceilingPerM2"),
        "clamped": doc.get("clamped", []),
        "fits": doc.get("fits", []),
    })
    return len(doc.get("clamped", []))


def southern_edge_text() -> str:
    """Where the modelled ground stops on the south, and what the plat has beyond it.

    Composed from `tools/measure_southern_ground.py` rather than written here, for the
    same reason the relief row reads `heightfield.json`: a sentence about the extent of
    the ground that is typed into prose is a sentence that survives the ground moving.
    """
    from measure_southern_ground import measure  # noqa: PLC0415

    m = measure()
    field, corridor = m["field"], m["washington_corridor"]
    census, tier = m["south_of_plat"], m["tier"]
    south_of_field = field["south_edge_n_m"] - tier["madison_at"]["state"]
    return (
        f"The modelled box ends {abs(field['south_edge_n_m']):.0f} m south of the forks, "
        f"and that line falls inside Washington Street's own 80 ft corridor: "
        f"{corridor['area_m2'] / 1e4:.2f} ha of the street's south half, over "
        f"{corridor['length_m']:.0f} m of its length, lies off the field. Madison Street "
        f"— the 1830 town plat's south boundary, fixed here from the section corner at "
        f"State and Madison — is {south_of_field:.1f} m further south again, so the plat's "
        f"last tier of blocks, {tier['area_ha']:.2f} ha on {tier['lots']} lots between "
        f"Market and State, is not modelled ground at all. Of the "
        f"{census['land_ha']:.2f} ha of land the field does hold south of Washington's "
        f"corridor, none is in the South Division: it is the far bank of the South "
        f"Branch. Past every edge of the box the ground is a plain skirt carrying the "
        f"edge heights outward, which claims nothing about 1835. Measured from the "
        f"committed heightfield and the committed street lines, not asserted."
    )


def compile_ground(scene_id: str, scene: dict, sources: dict, outdir: Path) -> int:
    """What the ground claims, for the visitor standing on it.

    Every building in this scene can tell you what it asserts, how sure of it we
    are, which sources say so and where the record is weakest. The surface all of
    them stand on could tell you none of that. `terrain_spec.json` is as fully
    graded as any structure record — a documented water plane, three inferred
    division levels arguing from period narrative feet, a conjectural bank face
    and a channel cross-section that says on its own face that it carries no
    evidence at all — and none of it reached any surface a visitor could read.
    The ground even dithers under the confidence view, which shows that a grade
    exists while saying nothing about what it grades.

    Derived, never authored: the spec is a generator input, hashed into the
    terrain's staleness, and this compiler only ever reads it. The measured
    figures come off `heightfield.json`, which the generator wrote — so the
    relief a visitor is told about is the relief the mesh actually has, not a
    number copied into prose and left to rot.
    """
    epoch = scene.get("terrain_epoch", "")
    ep_dir = DATA / "terrain" / "epochs" / epoch
    spec_path = ep_dir / "terrain_spec.json"
    if not spec_path.exists():
        emit(outdir / "terrain.json", {
            "scene": scene_id, "epoch": epoch, "claims": [], "not_modelled": [],
            "standard": f"No terrain spec is committed for epoch '{epoch}', so the "
                        f"ground in this scene makes no recorded claims.",
        })
        return 0

    spec = load(spec_path)
    datum = load(DATA / "datum.json")
    hf = load(ep_dir / "heightfield.json") if (ep_dir / "heightfield.json").exists() else {}

    claims = ground_claims(spec, sources)

    vert = datum.get("vertical", {})
    # The one claim the ground makes that is not in its own spec. Z = 0 is the
    # 1835 water surface by definition, and what that surface stood at above the
    # sea is a working assumption the whole vertical datum hangs off — recorded
    # in datum.json, graded conjectural there, and read by nobody.
    if vert.get("lake_stage_confidence"):
        claims.append({
            "id": "datum.lake_stage",
            "group": "the vertical datum",
            "label": "How high the 1835 water surface stood",
            "confidence": vert["lake_stage_confidence"],
            "confidence_key": "lake_stage_confidence",
            "fields": [{"key": "export_offset_ft_asl", "value": vert.get("export_offset_ft_asl")}],
            "sources": [],
            "citations": [],
            "notes": [t for t in (vert.get("lake_stage_note"), vert.get("internal")) if t],
        })

    relief = (hf.get("relief_ft") or {})
    grid = spec.get("grid", {})
    context = [
        {"label": "Zero", "text": spec.get("vertical", {}).get("datum", "")},
        {"label": "Vertical exaggeration",
         "text": spec.get("vertical", {}).get("exaggeration_note", "")},
        {"label": "The modelled box", "text": grid.get("note", "")},
    ]
    if relief:
        # Measured off the committed heightfield rather than asserted: the whole
        # argument for refusing the dossier's 4-8x exaggeration is that the site
        # really is this flat, and a visitor should get that figure from the mesh
        # they are standing on.
        context.append({
            "label": "Measured relief",
            "text": f"Land in the modelled box runs {relief.get('land_min')} to "
                    f"{relief.get('land_max')} ft above the water surface, and the "
                    f"channel floor reaches {relief.get('channel_min')} ft below it. "
                    f"Measured from the committed heightfield, not asserted.",
        })

    # T-0026. The box's own note above tells a reader how many samples it holds and
    # what it cost to publish; it does not tell them WHERE IT ENDS, and the south edge
    # is the one a visitor meets. Walk to the south side of Washington Street and the
    # town's modelled ground is already behind you — the box's edge falls inside that
    # street's own platted corridor, and the plat has a whole further tier of blocks
    # below it that this reconstruction does not contain. Same discipline as the relief
    # row: every figure is measured off the committed heightfield and the committed
    # street lines by `tools/measure_southern_ground.py`, so the card cannot drift from
    # the ground the day the terrain is extended.
    if epoch == "e1834_harbor_cut":
        context.append({"label": "Where the ground stops on the south",
                        "text": southern_edge_text()})

    emit(outdir / "terrain.json", {
        "scene": scene_id,
        "target_date": scene["target_date"],
        "epoch": epoch,
        "scope": spec.get("scope", ""),
        # The spec's own caveat, verbatim, for the same reason the exclusions list
        # quotes its own standard: the section's honesty claim belongs to the
        # dataset, not to whichever renderer happens to be displaying it.
        "standard": spec.get("critical_caveat", ""),
        "context": [c for c in context if c["text"]],
        "claims": claims,
        # Researched, sited, and outside this box — the terrain's own version of
        # "what is not here", which the same spec has recorded since it was written.
        "not_modelled": [
            {"dossier_zone": z.get("dossier_zone"), "why": z.get("why", "")}
            for z in spec.get("not_modelled_in_this_box", [])
        ],
    })
    return len(claims)


def compile_intersections(datum: dict) -> list[dict]:
    """Every verified street-control junction, flattened for navigation.

    The renderer reads sidecars, never the raw research dataset.  Street
    intersections therefore belong in the scene index beside the structures:
    one derived list, re-derived by ``--check``, rather than a second set of
    coordinates typed into the interface.  The names come from the same street
    dictionary the placement checks use, and local ENU is derived from the
    committed datum exactly as structure placement is below.
    """
    doc = load(DATA / "traces" / "street_control.json")
    streets = doc.get("streets", {})
    out = []
    for iid, control in sorted((doc.get("control") or {}).items()):
        street_ids = control.get("streets", []) or []
        names = [streets.get(s, {}).get("name", s.replace("_", " ").title())
                 for s in street_ids]
        modern = [streets.get(s, {}).get("modern", "") for s in street_ids]
        out.append({
            "id": iid,
            "label": " & ".join(names),
            "streets": street_ids,
            "search_terms": [x for x in [*names, *modern] if x],
            "local_e": round(control["utm_e"] - datum["origin_utm_e"], 3),
            "local_n": round(control["utm_n"] - datum["origin_utm_n"], 3),
        })
    return out


# T-0111.  How far a drawn track may run past the end of its own platted line.
# The measured need is one bridge abutment: Dearborn's causeway deck ends 2.70 m
# north of where the platted line stops, and a track that cannot reach it stops
# on bare crest.  Four metres carries that and nothing like a block, so an
# overrun that would amount to an unplatted street fails here rather than
# arriving quietly in the picture.
DRAWN_TRACK_OVERHANG_MAX_M = 4.0


def _plat_offsets(plat: list[tuple[float, float]],
                  point: tuple[float, float]) -> tuple[float, float]:
    """(lateral offset from the platted line, overhang past its ends), metres.

    The terminal segments are read as LINES rather than as segments, so a point
    beyond the end reports the offset it actually has from the street's own
    bearing plus the distance it runs past the end — two separate numbers,
    because they are two separate ways of ceasing to be that street.  Interior
    segments are clamped as usual.
    """
    e, n = point
    lateral = float("inf")
    overhang = 0.0
    last = len(plat) - 2
    for i in range(len(plat) - 1):
        (ae, an), (be, bn) = plat[i], plat[i + 1]
        de, dn = be - ae, bn - an
        length = math.hypot(de, dn) or 1e-9
        ux, uy = de / length, dn / length
        t = (e - ae) * ux + (n - an) * uy
        lo = -math.inf if i == 0 else 0.0
        hi = math.inf if i == last else length
        held = min(max(t, lo), hi)
        lateral = min(lateral, math.hypot(e - (ae + ux * held), n - (an + uy * held)))
        if i == 0:
            overhang = max(overhang, -t)
        if i == last:
            overhang = max(overhang, t - length)
    return lateral, max(overhang, 0.0)


def compile_streets(scene_id: str, target_date: str,
                    sources: dict) -> tuple[str, list[dict]]:
    """The dated street surface and name layer consumed by the renderer.

    Street research is authored under ``data/streets`` and flattened into the
    same scene index that already carries structures and verified junctions.
    That keeps raw research out of the browser, joins citations once, and makes
    ``compile_scene --check`` the drift gate for the visible roads too.

    The rendered strip is deliberately NOT the whole platted corridor: an
    80-foot legal right-of-way and the wagon-worn earth inside it are different
    claims.  Both widths travel so the readout can identify the street across
    the corridor while flora is cleared only from the narrower travelled part.

    T-0111 SPLIT THE LINE THE SAME WAY THE WIDTHS WERE ALREADY SPLIT, and the
    reason is a measurement rather than a preference.  ``path_local_enu_m`` is
    the PLATTED line, and it is read by ``generate_plat_lots.py`` — which
    re-derives every block face by offsetting the whole polyline — and by
    ``plat_corridors``, which the corridor-intrusion gate scores against.  So a
    three-metre bend appended to it to carry Dearborn's worn track onto its
    causeway moved platted lot lines the length of the street (PLAT GRID DRIFT)
    and pushed the drawbridge itself into a corridor it had not been in
    (30 laps against a committed 29, the deck newly lapping by 0.66 m).  Both
    were measured on the appended path before this field existed.

    ``drawn_track_local_enu_m`` is the optional second line: the wagon-worn
    wheel line the renderer paints, which the plat, corridor and lot
    derivations never read.  It is bounded here rather than trusted — every
    point stays inside the street's own platted corridor and may run past the
    platted line's ends by at most ``DRAWN_TRACK_OVERHANG_MAX_M`` — so the
    field can reach a bridge abutment and cannot quietly become a second plat.
    """
    path = DATA / "streets" / f"{scene_id}.json"
    if not path.exists():
        return "No dated street layer is committed for this scene.", []
    doc = load(path)
    if doc.get("scene") != scene_id:
        raise SystemExit(f"{path.relative_to(ROOT)}: scene must be {scene_id!r}")
    if doc.get("target_date") != target_date:
        raise SystemExit(f"{path.relative_to(ROOT)}: target_date must be {target_date!r}")

    common_sources = doc.get("sources", []) or []
    default_corridor = doc.get("corridor_width_m", 24.384)
    out = []
    seen: set[str] = set()
    for raw in doc.get("streets", []) or []:
        sid = raw.get("id", "")
        if not sid or sid in seen:
            raise SystemExit(f"{path.relative_to(ROOT)}: missing or duplicate street id {sid!r}")
        seen.add(sid)
        points = raw.get("path_local_enu_m")
        if (not isinstance(points, list) or len(points) < 2
                or any(not isinstance(p, list) or len(p) != 2
                       or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in p)
                       for p in points)):
            raise SystemExit(f"{path.relative_to(ROOT)}: {sid} needs two or more finite [e,n] points")
        corridor = raw.get("corridor_width_m", default_corridor)
        track = raw.get("track_width_m")
        # A PLATTED BUT UNOPENED STREET HAS NO TRACK, and until T-0797 this layer had no
        # way to say so: every record was required to draw a worn strip inside its
        # corridor. Wright rules twelve east-west lines across the School Section that
        # nobody had yet driven — the owner read the sheet on 2026-09-05 as "no alleys and
        # no street names but still a grid" — so `opened: false` and a zero track are a
        # legal pair, and they must travel together. A zero track with no such declaration
        # is still the old error, because it would silently erase a street that existed.
        opened = raw.get("opened", True)
        if not isinstance(corridor, (int, float)) or not isinstance(track, (int, float)):
            raise SystemExit(f"{path.relative_to(ROOT)}: {sid} track width must be inside its corridor")
        if opened is False:
            if track != 0:
                raise SystemExit(f"{path.relative_to(ROOT)}: {sid} is declared unopened and "
                                 "still draws a track — an unopened street has no worn strip")
        elif not 0 < track < corridor:
            raise SystemExit(f"{path.relative_to(ROOT)}: {sid} track width must be inside its corridor")
        drawn = raw.get("drawn_track_local_enu_m")
        if drawn is not None:
            if (not isinstance(drawn, list) or len(drawn) < 2
                    or any(not isinstance(p, list) or len(p) != 2
                           or any(not isinstance(v, (int, float)) or not math.isfinite(v)
                                  for v in p)
                           for p in drawn)):
                raise SystemExit(f"{path.relative_to(ROOT)}: {sid}.drawn_track_local_enu_m "
                                 "needs two or more finite [e,n] points")
            if not str(raw.get("drawn_track_note", "")).strip():
                raise SystemExit(f"{path.relative_to(ROOT)}: {sid} draws a track off its "
                                 "platted line and says nothing about why — "
                                 "drawn_track_note must state what bounds the invention")
            plat = [(float(e), float(n)) for e, n in points]
            for pe, pn in drawn:
                lateral, overhang = _plat_offsets(plat, (float(pe), float(pn)))
                if lateral > corridor / 2.0:
                    raise SystemExit(
                        f"{path.relative_to(ROOT)}: {sid} draws its track {lateral:.2f} m "
                        f"off the platted line at [{pe}, {pn}] — outside its own "
                        f"{corridor:.3f} m corridor, which makes it a different street")
                if overhang > DRAWN_TRACK_OVERHANG_MAX_M:
                    raise SystemExit(
                        f"{path.relative_to(ROOT)}: {sid} draws its track {overhang:.2f} m "
                        f"past the end of the platted line at [{pe}, {pn}] — the limit is "
                        f"{DRAWN_TRACK_OVERHANG_MAX_M:.1f} m, enough to meet a bridge "
                        "abutment and not enough to be an unplatted street")
        for key in ("geometry_confidence", "surface_confidence", "wear_confidence"):
            if raw.get(key, "reconstructed") not in ("attested", "inferred", "reconstructed"):
                raise SystemExit(f"{path.relative_to(ROOT)}: {sid}.{key} is not a confidence grade")
        street_sources = sorted(set([*common_sources, *(raw.get("sources", []) or [])]))
        missing = [s for s in street_sources if s not in sources]
        if missing:
            raise SystemExit(f"{path.relative_to(ROOT)}: {sid} cites missing source(s): {', '.join(missing)}")
        out.append({
            "id": sid,
            "name_1835": raw["name_1835"],
            "name_2026": raw["name_2026"],
            "name_changed": bool(raw.get("name_changed", False)),
            "path_local_enu_m": points,
            # Only where one is authored, so every street without a drawn track
            # compiles to exactly the entry it always did.
            **({"drawn_track_local_enu_m": drawn,
                "drawn_track_note": raw["drawn_track_note"]} if drawn is not None else {}),
            "corridor_width_m": corridor,
            "track_width_m": track,
            # Only on the records that declare it, so every street compiled before
            # T-0797 compiles to exactly the entry it always did.
            **({"opened": False,
                "status_1835": raw.get("status_1835", "platted, unopened, unworn"),
                "alleys": bool(raw.get("alleys", False))} if opened is False else {}),
            "surface": raw["surface"],
            "traffic": raw["traffic"],
            "geometry_confidence": raw.get("geometry_confidence", "reconstructed"),
            "surface_confidence": raw.get("surface_confidence", "reconstructed"),
            "wear_confidence": raw.get("wear_confidence", "reconstructed"),
            "note": raw.get("note", ""),
            "citations": cite(street_sources, sources),
        })
    return doc.get("surface_standard", ""), out


def compile_residents() -> dict[str, list[dict]]:
    """structure_id -> the households the residents layer attaches to it.

    THE REASON THIS EXISTS. `data/residents/` is a dataset layer with no geometry
    (docs/LIBERTIES.md L1: v1 draws no human figures), so nothing in the renderer
    had any way to reach it and ninety-six researched Chicagoans were invisible on
    the site — the exact complaint the owner made about work that had "landed".
    A building is the only place a visitor meets a resident, so the household
    travels in the building's own sidecar and the card shows who lived or worked
    there, with each person's accuracy grade shown as plainly as an attribute's
    confidence.

    `basis` is the sentence the inferred-household programme owes the reader: a
    building raised BECAUSE of a hypothesised household has to say so in the same
    breath as it names them, or the card reads as evidence of a person.
    """
    index_path = DATA / "residents" / "index.json"
    if not index_path.exists():
        return {}
    index = load(index_path)
    programme_path = DATA / "reconstruction" / "1835_inferred_household_programme.json"
    raised = {}
    if programme_path.exists():
        raised = {b["id"]: b for b in load(programme_path).get("buildings", [])}

    out: dict[str, list[dict]] = {}
    for entry in index.get("households", []):
        hh = load(DATA / "residents" / entry["file"])
        links = {}
        for key in ("lives_at", "works_at"):
            block = hh.get(key) or {}
            if block.get("value"):
                links.setdefault(block["value"], []).append((key, block))
        for sid, pairs in links.items():
            kinds = [k for k, _ in pairs]
            relation = ("lived and worked here" if len(kinds) == 2
                        else "lived here" if kinds[0] == "lives_at" else "worked here")
            grades = sorted({p.get("grade") for p in hh.get("persons", [])})
            building = raised.get(sid)
            if building and building.get("kind") == "inferred":
                basis = ("THIS BUILDING IS IN THE MODEL BECAUSE OF THIS HOUSEHOLD. Neither is "
                         "documented: the household is inferred from the town's demonstrable "
                         "needs and the roof was raised to house it. Its existence, position "
                         "and size are all inventions, and the chips above say so.")
            elif building:
                basis = ("The building is documented and the household is the one the sources "
                         "attach to it; this parcel built the record they had been waiting for.")
            elif sid.startswith("recon_") and "reconstructed" in grades:
                basis = ("An anonymous roof of the reconstruction programme, ADOPTED by this "
                         "household rather than raised for it. The roof's own existence and "
                         "position stay conjectural; what the adoption adds is an argued "
                         "occupant instead of an anonymous count-unit.")
            else:
                basis = ""
            out.setdefault(sid, []).append({
                "household": hh["id"],
                "name": hh["name"],
                "division": hh.get("division", ""),
                "relation": relation,
                "why": pairs[0][1].get("note", ""),
                "sources": sorted({s for _, b in pairs for s in (b.get("sources") or [])}),
                "basis": basis,
                "persons": [{
                    "name": person.get("name", ""),
                    "relationship": person.get("relationship", ""),
                    "grade": person.get("grade", "reconstructed"),
                    "occupation": (person.get("occupation") or {}).get("value", ""),
                    "note": person.get("note", ""),
                } for person in hh.get("persons", [])],
                "research_note": hh.get("research_note", ""),
            })
    for households in out.values():
        households.sort(key=lambda h: h["household"])
    return out


def compile_scene(scene_id: str, sources: dict, exclusions: dict) -> int:
    scene = load(DATA / "scenes" / f"{scene_id}.json")
    target = dt.date.fromisoformat(scene["target_date"])
    datum = load(DATA / "datum.json")
    outdir = DATA / "sidecars" / scene_id
    outdir.mkdir(parents=True, exist_ok=True)

    written, skipped = 0, []
    index = []
    residents = compile_residents()
    # id -> the phase that resolves into this scene, for the watch list below
    resolved: dict[str, dict] = {}

    for path in sorted((DATA / "structures").glob("*.json")):
        st = load(path)
        phase = resolve_phase(st, target)
        if phase is None:
            skipped.append(st["id"])
            continue

        # gather every source cited anywhere in this phase, so the popup can show
        # the evidence without the renderer walking the dataset
        cited: set[str] = set()

        def collect(node):
            if isinstance(node, dict):
                for s in node.get("sources", []) or []:
                    cited.add(s)
                for v in node.values():
                    collect(v)
            elif isinstance(node, list):
                for v in node:
                    collect(v)

        collect(phase)
        for key in ("function", "occupants", "lot_address", "land_owner"):
            collect(st.get(key, {}))
        if st.get("reconstruction", {}).get("source_id"):
            cited.add(st["reconstruction"]["source_id"])
        for household in residents.get(st["id"], []):
            cited.update(household["sources"])

        # `geometry` travels with the attribute because it qualifies the chip next
        # to it: a documented value the mesh does not contain is a true statement
        # about the evidence and a false one about the view, and the popup has to
        # be able to say which it is showing.
        attributes = {}
        for attr, a in (phase.get("form") or {}).items():
            attributes[attr] = {k: v for k, v in a.items() if k in
                                ("value", "confidence", "sources", "note", "geometry")}
        for key in ("function", "occupants"):
            if key in st:
                attributes[key] = {k: v for k, v in st[key].items() if k in
                                   ("value", "confidence", "sources", "note", "geometry")}
        # T-0423. A LOT-AND-BLOCK ADDRESS IS AN ATTRIBUTE OF THE BUILDING, and it travels
        # as one so that the card renders it with the same chip, sources and reasoning as
        # everything else it says. The row's `value` is the title the address gives the
        # house — `display-name.js` reads it from here rather than from a second copy —
        # and its grade is the bottom tier, because the words are read and the lot lines
        # they land on are not. The record's own `lot_address` block keeps the block and
        # lot numbers; the card wants the sentence, not the arithmetic.
        if "lot_address" in st:
            attributes["lot_address"] = {
                "value": st["lot_address"]["title"],
                "confidence": st["lot_address"]["confidence"],
                "sources": st["lot_address"]["sources"],
                "note": st["lot_address"]["note"],
            }

        # T-0609. WHO ENTERED THE GROUND UNDER THE ROOF is an attribute of the building
        # for the same reason the address is: it is a claim with a source, a grade and a
        # reason, and the card already renders those. The register is a register of
        # TRANSACTIONS, so the row's own words are what travel — the block's `note`
        # carries what it does not claim, which is the part a visitor most needs.
        if "land_owner" in st:
            attributes["land_owner"] = {
                "value": st["land_owner"]["value"],
                "confidence": st["land_owner"]["confidence"],
                "sources": st["land_owner"]["sources"],
                "note": st["land_owner"]["note"],
            }

        # THE PHASE'S CLAIM ABOUT ITSELF. Every `form` attribute has carried its
        # note to the card since the card was written; the two phase-level blocks
        # a visitor is most likely to ask about — was it here, and how do you know
        # where — carried only a confidence chip, and `documented_range` did not
        # reach the sidecar at all. The popup has read `documented_range` since it
        # was written and this compiler never wrote it, so the line has never once
        # rendered: the question the whole scene rests on was answered nowhere in
        # the walkthrough while being argued at length in the record.
        #
        # Note the shape is the SAME as an attribute's — value/confidence/sources/
        # note — because the card renders these rows with the attribute renderer.
        # Two renderers describing the same kind of claim differently is the drift
        # this project keeps closing.
        rng = phase.get("documented_range", {})
        pos = phase.get("position", {})
        provisional = pos.get("utm_e") is None
        if provisional:
            local_e = local_n = 0.0
        else:
            local_e = round(pos["utm_e"] - datum["origin_utm_e"], 3)
            local_n = round(pos["utm_n"] - datum["origin_utm_n"], 3)

        sidecar = {
            "id": st["id"],
            "phase": phase["id"],
            "name": st["name"],
            "aka": st.get("aka", []),
            "archetype": st["archetype"],
            # A phase whose geometry moved to another layer has no GLB, and the
            # sidecar says so in the field the loader reads rather than by
            # naming a file that is not there. `drawn_by` travels with it so the
            # renderer can say WHAT draws it instead — a null asset alone would
            # be indistinguishable from a bake that failed to land. The estray
            # pen is the first: a pound is a fence, and the roof it wore until
            # 2026-08-18 existed only because `outbuilding` cannot build a
            # roofless structure (docs/LIBERTIES.md L60, T-0051).
            "asset": None if phase.get("drawn_by")
                     else f"gltf/{st['id']}__{phase['id']}.glb",
            "scene": scene_id,
            "target_date": scene["target_date"],
            # Was it here at all? The scene date falls inside this span by
            # construction — resolve_phase would not have returned the phase
            # otherwise — so what the card has to show is not the fact but the
            # STRENGTH of it, and the reasoning behind the end of the range, which
            # for a building nobody followed past 1834 is the weakest claim on it.
            "documented_range": {
                "from": rng.get("from", ""),
                "to": rng.get("to", ""),
                "confidence": rng.get("confidence", "reconstructed"),
                "sources": rng.get("sources", []),
                "note": rng.get("note", ""),
            },
            # What this phase IS, in the record's own words. Written for a reader
            # and read by nobody: it is where a record says that a building holding
            # the post office for three years is not the post office on the scene
            # date, which no chip can express.
            "change_note": phase.get("change_note", ""),
            "placement": {
                "local_e": local_e,
                "local_n": local_n,
                "rotation_deg": pos.get("rotation_deg", 0.0),
                "position_confidence": pos.get("confidence", "reconstructed"),
                "position_sources": pos.get("sources", []),
                "position_note": pos.get("note", ""),
                "symbolic_location": pos.get("symbolic_location", ""),
                "uncertainty_m": 20,
                "placement_provisional": provisional,
                # `terrain` for a building, `water` for a bridge. The renderer must
                # not sample the heightfield for the second kind: mid-channel the
                # ground surface is the river bed, and a bridge placed on it sinks.
                "vertical_anchor": vertical_anchor(st["archetype"]),
                # T-0001. How high above that anchor a visitor may STAND — a
                # bridge deck, and nothing else in this dataset has one. `null`
                # for a building, whose walkable surface is the ground the walker
                # is already standing on.
                "walk_surface_m": walk_surface_m(st, phase),
            },
            # Carry the footprint's own confidence, not just its geometry — a bare
            # polygon loses precisely the thing the confidence view exists to show.
            #
            # And carry its ARGUMENT, which this compiler dropped on the floor from
            # the day it was written. The footprint note is the longest and most
            # load-bearing uncertainty statement on most of these records — six of
            # the eight say PLACEHOLDER in their first line — and it reached no
            # visitor, while a roof pitch carried its chip, its sources and its
            # reasoning. Worse, the tint stopped carrying it deliberately: when an
            # unknown SIZE was found dithering whole buildings into ghost massing,
            # the massing rule was narrowed to the attributes that say what a
            # building WAS, on the stated understanding that dimensional
            # uncertainty is carried in the sidecar "where the popup shows it".
            # The sidecar carried it. The popup was never given it. Same shape as
            # `documented_range` and `research_note` before it.
            "footprint": {
                "polygon": phase.get("footprint", {}).get("polygon", []),
                "confidence": phase.get("footprint", {}).get("confidence", "reconstructed"),
                "sources": phase.get("footprint", {}).get("sources", []),
                "note": phase.get("footprint", {}).get("note", ""),
            },
            "attributes": attributes,
            # Who was here. Empty on most buildings and never absent, so the card
            # reads one shape everywhere and the sidecar contract can see the field.
            "residents": residents.get(st["id"], []),
            "citations": cite(cited, sources),
            "research_note": st.get("research_note", ""),
            # A reconstruction block used to mean one dossier, because there was
            # only one kind of it. Since K21 the inferred-household layer's 31
            # buildings carry one too, and the layer they belong to is written up
            # in its own dossier — sending them to the anonymous-infill programme's
            # write-up would put a visitor in front of a document about aggregate
            # count-units when the building they clicked exists for a particular
            # argued household. Keyed on the status rather than on the block's mere
            # presence, so a third status cannot inherit the wrong dossier by
            # default; anything with no block keeps its per-record path — and
            # the path is resolved against the repository, so a card never
            # offers a dossier nobody wrote (see research_doc() above).
            "research_doc": research_doc(st),
            "review_required": st.get("review_required", False),
        }
        # Written ONLY on the phases that have it, unlike `residents`, which is
        # written empty everywhere so the card reads one shape. The difference is
        # that this one is a rare exception rather than a per-record field: 330
        # sidecars carrying `drawn_by: null` would be 330 files of diff saying
        # nothing, in a mirror that is published byte-for-byte.
        # AGENTS.md's standing constraint is the one rule this project puts above the
        # work, and until T-0268 it reached a browser once, as a console line about the
        # scene. The boolean above lets the card SAY a building is held; this says what
        # it is held for, in the record's own words rather than a paraphrase — the same
        # sentence `measure_review_constraint.py` assertion 6 judges, read by the module
        # they share, and re-derived against these bytes by assertion 7. Written only on
        # the records that carry the flag, like `drawn_by` below: nine files rather than
        # 330 saying nothing in a mirror that is published byte-for-byte.
        if sidecar["review_required"]:
            reason = record_reason(st)
            if reason:
                sidecar["review_reason"] = reason
        if phase.get("drawn_by"):
            sidecar["drawn_by"] = phase["drawn_by"]["layer"]
        if st.get("reconstruction"):
            sidecar["reconstruction"] = st["reconstruction"]
        emit(outdir / f"{st['id']}.json", sidecar)
        resolved[st["id"]] = phase
        index.append({"id": st["id"], "name": st["name"],
                      "sidecar": f"sidecars/{scene_id}/{st['id']}.json",
                      "asset": sidecar["asset"]})
        written += 1

    street_standard, streets = compile_streets(scene_id, scene["target_date"], sources)
    emit(outdir / "index.json", {
        "scene": scene_id,
        "target_date": scene["target_date"],
        "intersections": compile_intersections(datum),
        "street_standard": street_standard,
        "streets": streets,
        "structures": index,
        "excluded_by_date": skipped,
    })

    left_out = compile_exclusions(scene_id, scene, target, sources, exclusions, outdir,
                                  in_scene=resolved)
    ground = compile_ground(scene_id, scene, sources, outdir)
    fauna_cites = compile_fauna_sources(scene_id, sources, outdir)
    flora_cites = compile_flora_sources(scene_id, sources, outdir)
    flora_clamped = compile_flora_clamp(scene_id, outdir)
    resident_cites = compile_residents_sources(scene_id, sources, outdir)
    people = compile_people(scene_id, outdir)

    # A SIDECAR WHOSE STRUCTURE HAS GONE IS NOT INERT, which is why this sweeps
    # rather than leaves them. The compiler only ever wrote sidecars, so a record
    # deleted between two compiles left its sidecar behind — and the derived layers
    # read `data/sidecars/`, not `data/structures/`, so the town went on fencing and
    # planting the yard of a house that no longer existed while every gate stayed
    # green: the layer re-derived exactly, from an input nobody had noticed was a
    # ghost. Found 2026-08-22 in T-0105's own merge, which left three of them.
    keep = {entry["id"] for entry in index} | set(skipped) | {
        "index", "exclusions", "terrain", "fauna_sources", "flora_sources",
        "flora_clamp", "residents_sources", "people"}
    for stale in sorted(outdir.glob("*.json")):
        if stale.stem in keep:
            continue
        if CHECK:
            DRIFT.append(f"{stale.relative_to(ROOT)} is a sidecar for a structure the "
                         f"dataset no longer carries")
        else:
            stale.unlink()

    print(f"scene {scene_id}: {written} sidecar(s), {left_out} researched exclusion(s), "
          f"{ground} ground claim(s), {fauna_cites} fauna source(s), "
          f"{flora_cites} flora source(s), {flora_clamped} clamped plant layer(s), "
          f"{resident_cites} resident source(s), {people} people in the directory"
          + (f", {len(skipped)} excluded by date ({', '.join(skipped)})" if skipped else ""))
    return written


def main() -> int:
    global CHECK
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="re-derive and fail on drift; write nothing")
    args = ap.parse_args()
    CHECK = args.check

    sources = {}
    for p in sorted((DATA / "sources").glob("*.json")):
        s = load(p)
        sources[s["id"]] = s
    exclusions = load(DATA / "exclusions.json")

    scenes = ([p.stem for p in sorted((DATA / "scenes").glob("*.json"))]
              if args.all or not args.scene else [args.scene])
    total = sum(compile_scene(s, sources, exclusions) for s in scenes)
    if CHECK:
        for d in DRIFT:
            print(f"   DRIFT: {d}")
        if DRIFT:
            print(f"{len(DRIFT)} derived file(s) disagree with the dataset — "
                  f"run: python3 tools/compile_scene.py --all")
            return 1
        print("OK: every committed sidecar is what the dataset compiles to")
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
