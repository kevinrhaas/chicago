#!/usr/bin/env python3
"""Compile the building summary records into what the Inspect app reads (T-2635).

    python3 tools/compile_summaries.py --build       gate, then write data/inspect/<scene>.json
    python3 tools/compile_summaries.py --check       gate and compile in memory; write nothing
    python3 tools/compile_summaries.py --self-test   plant each fault and require the gate to refuse it

Design doc "Field Navigator Mk II", section 12 "Building summary record": a notable
structure gets an AUTHORED front page, data/summaries/<id>.json, shaped by
data/summary.schema.json. The Inspect app's front page (T-2638) answers what a visitor
actually asks — what is it, who lived here, what should I look at, what is remarkable —
and every line of it carries a grade dot. That page shows these strings exactly as they
are written, so the gate sits here, between the author and the visitor:

  - a grade on every fact (status, built, each key fact, resident, Look-for line,
    notable fact and story entry), from the data's own ladder: attested, inferred,
    reconstructed;
  - sources on every attested fact, each resolving in data/sources/ — never invented;
    a note on every inferred or reconstructed fact (AGENTS.md hard rule 2, and the
    reconstructed tier's "record what bounded the invention"); a liberty, where named,
    resolving in data/liberties.json;
  - each person resolving in the scene's people directory,
    data/sidecars/<scene>/people.json, which is where the compiled form takes the name;
  - the structure standing in the record's scene (data/sidecars/<scene>/<id>.json);
  - the length limits: summary at most 60 words and 3 sentences, a role at most 12 words,
    a Look-for line at most 8 words, a notable fact at most 25 words;
  - no id, snake_case word, file path, link or ticket number inside any string a visitor
    reads. Reading level is a separate gate (T-2669).

THE COMPILED FORM. One file per scene, data/inspect/<scene>.json, written for every
scene in data/scenes/ whether or not any record names it, so the Inspect app's one fetch
never 404s and a structure missing from `summaries` takes the templated fallback (T-2636).
Each record is carried as authored, plus what the app should not have to work out:
residents carry their directory name; notable facts are ranked for the front page by
impact (surprising x3, about a person x2, visible from the street x2, Attested x1.5,
multiplied, ties kept in authored order) and carry the score; story entries are in date
order; `grades` counts the record's facts by grade for the confidence meter; and the
file's `sources` resolves every cited id to its citation, type, date, tier and links, so the
Sources tab can show a human title, what kind of source it is, and the full citation without
a fetch per source; `source_dates` carries the recorded date of every source the scene's
structures cite, so the tab says "from the time" only of a source dated by the scene's year
(T-2644).

THE DESIGN TAB (T-2641; design doc section 08 "Design", section 12 "Style library" and
"Attribute table -> Design hotspots"). A record may carry `onThisHouse`, the numbered
hotspots: each is a graded fact like any other (grade, sources on Attested, a note on the
other two, a liberty that resolves), its feature at most 8 words and its line at most 16,
and where it names one of the structure's sidecar `attribute`s its grade must be that
attribute's own confidence, so the Design tab and the sidecar cannot grade one feature two
ways. They are gated with the record's facts and NOT counted in `grades`: they restate what
the record and the sidecar already grade, and the front page's meter is the record's own.
A record's `style` must name a module in data/styles/<id>.json (data/style.schema.json):
the style card's name, a two-line description, up to four "how to spot it" cues of at most
8 words, an optional credited plate and up to three Compare styles lines of at most 12
words, every one of them graded and sourced the same way, and the plate's own picture
record public domain or free of known restrictions (AGENTS.md hard rule 6). A cue the
sources do not support is left out, never written from general knowledge. Every module is
carried into every scene's file under `styles`, with its cited sources added to `sources`,
so a building of any year can link to one (T-2642). A Compare styles line may name another
module by its `style`; the Design tab then opens that module's lines and cues in place, so
the gate refuses a line pointing at its own module or calling the module it names by any
name but that module's own.

GENERATED, NOT COMMITTED. data/inspect/ is ignored by git and written by publish.sh just
before the mirror, the way data/pictures/ is: the compiled form reads source records and
the people directory, which other tickets change, and a committed copy would go stale on
dev the moment one of them merged. A record that fails the gate stops --build, so a
publish never ships a front page the gate refused.
"""

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMA = DATA / "summary.schema.json"
SUMMARIES = DATA / "summaries"
STYLES = DATA / "styles"
STYLE_SCHEMA = DATA / "style.schema.json"
OUT = DATA / "inspect"

GRADES = ("attested", "inferred", "reconstructed")

# Design doc section 12. Words are counted as whitespace-separated tokens holding a letter
# or a digit, so a "·" or a dash between words is not a word.
LIMITS = {
    "summary": {"words": 60, "sentences": 3},
    "residents.role": {"words": 12},
    "lookFor.text": {"words": 8},
    "notable.text": {"words": 25},
    # T-2641: the Design tab.
    "onThisHouse.text": {"words": 8},
    "onThisHouse.detail": {"words": 16},
    "style.description": {"words": 30, "sentences": 2},
    "style.cue": {"words": 8},
    "style.compare": {"words": 12},
}

# Impact for the front page, design doc section 12 "Impact score".
IMPACT = {"surprising": 3.0, "person": 2.0, "visible_from_street": 2.0, "attested": 1.5}

# The lists whose every item is a fact, and the single facts.
FACT_LISTS = ("key", "residents", "lookFor", "notable", "story", "onThisHouse")
# Gated as facts, never counted in the front page's Confidence meter (T-2641): the Design
# tab's hotspots restate facts the record and the sidecar already grade.
UNCOUNTED = ("onThisHouse",)
FACT_SINGLES = ("status", "built")

# Keys whose string values are data, never shown to a visitor. Every other string in a
# record is visitor-facing and is linted.
DATA_KEYS = {"id", "scene", "grade", "sources", "person", "feature", "style", "about",
             "era", "date", "liberty",
             # T-2641: a hotspot's sidecar attribute; a style plate's picture, structure and record.
             "attribute", "picture", "structure", "record"}

SNAKE = re.compile(r"[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+")
PATH = re.compile(
    r"(?:(?<![\w])(?:\.{1,2}/|/)?(?:data|tools|docs|assets|renderers|generators|site|"
    r"tickets|research|chicago|walk|js|css)/\S*)"
    r"|(?:\b[\w.-]+\.(?:json|jsonl|js|mjs|cjs|ts|py|sh|md|html?|css|glb|gltf|bin|png|"
    r"jpe?g|webp|gif|svg|csv|tsv|txt|pdf|tiff?|xml|ya?ml)\b)",
    re.IGNORECASE)
LINK = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
TICKET = re.compile(r"\b(?:T|NAV|PR)-?#?\d{2,5}\b")

# A period after one of these does not end a sentence: "H. H. Richardson",
# "1800 S. Prairie Ave. at 18th St." is one sentence, not four.
ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "st", "ave", "blvd", "jr", "sr", "co", "gen",
                 "col", "rev", "capt", "lt", "mt", "ft", "no", "vs", "inc", "bros",
                 "messrs", "prof", "hon", "gov", "sen", "rep", "maj", "sgt", "ct", "pl"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dumps(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def words(text):
    return [t for t in text.split() if re.search(r"[A-Za-z0-9]", t)]


def sentences(text):
    """How many sentences: a token ending in . ! or ? (quotes and brackets after it allowed)
    ends one when it is the last token or the next starts a sentence, unless it is an
    initial or a common abbreviation."""
    toks = text.split()
    n = 0
    for i, tok in enumerate(toks):
        bare = tok.rstrip("\"'”’)]")
        if not bare or bare[-1] not in ".!?":
            continue
        last = i == len(toks) - 1
        if not last and not re.match(r"[\"'“‘(\[]?[A-Z0-9]", toks[i + 1]):
            continue
        if bare.endswith(".") and not bare.endswith(".."):
            stem = bare.rstrip(".").lstrip("\"'“‘([").lower()
            if (len(stem) == 1 and stem.isalpha()) or stem in ABBREVIATIONS:
                if not last:
                    continue
        n += 1
    if toks and n == 0:
        n = 1
    elif toks:
        tail = toks[-1].rstrip("\"'”’)]")
        if tail and tail[-1] not in ".!?":
            n += 1  # trailing words with no full stop are a sentence too
    return n


def lint_string(text):
    """What in this visitor-facing string a visitor must never see."""
    found = []
    for m in LINK.finditer(text):
        found.append(f"a link `{m.group(0)}`")
    scrubbed = LINK.sub(" ", text)
    for m in PATH.finditer(scrubbed):
        found.append(f"a file path `{m.group(0)}`")
    for m in SNAKE.finditer(scrubbed):
        found.append(f"an id or snake_case word `{m.group(0)}`")
    for m in TICKET.finditer(scrubbed):
        found.append(f"a ticket number `{m.group(0)}`")
    return found


def visitor_strings(node, where):
    """(location, text) for every visitor-facing string in a record."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in DATA_KEYS:
                continue
            yield from visitor_strings(v, f"{where}.{k}" if where else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from visitor_strings(v, f"{where}[{i}]")
    elif isinstance(node, str):
        yield where, node


def facts(rec):
    """(location, fact) for every graded fact in a record."""
    for k in FACT_SINGLES:
        if isinstance(rec.get(k), dict):
            yield k, rec[k]
    for k in FACT_LISTS:
        for i, f in enumerate(rec.get(k) or []):
            if isinstance(f, dict):
                yield f"{k}[{i}]", f


# ------------------------------------------------------------------- the world

def load_world(root=ROOT):
    """What a record's ids resolve against, read from the tree."""
    data = Path(root) / "data"
    sources = {}
    for p in sorted((data / "sources").glob("*.json")):
        try:
            s = load_json(p)
        except (OSError, ValueError):
            continue
        # The tier is carried so the Sources tab can say "from the time" or "written later"
        # (T-2644); it never prints the rung. The links let the folded citation open its source.
        sources[p.stem] = {k: s[k] for k in ("citation", "type", "date", "tier", "url", "archived_url")
                           if k in s}
    scenes = sorted(p.stem for p in (data / "scenes").glob("*.json"))
    standing = {}
    people = {}
    cited_in = {}
    for scene in scenes:
        sdir = data / "sidecars" / scene
        standing[scene] = {p.stem for p in sdir.glob("*.json")} if sdir.is_dir() else set()
        directory = sdir / "people.json"
        people[scene] = {}
        if directory.is_file():
            for row in load_json(directory).get("people", []):
                people[scene][row["id"]] = {"name": row.get("name"), "grade": row.get("grade")}
        standing[scene].discard("people")
        # Every source a structure of this scene cites (T-2644): the Sources tab needs each
        # one's date to say "from the time" only where the source is dated by the scene year.
        cited_in[scene] = set()
        for stem in standing[scene]:
            try:
                side = load_json(sdir / f"{stem}.json")
            except (OSError, ValueError):
                continue
            for c in side.get("citations", []) if isinstance(side, dict) else []:
                if isinstance(c, dict) and c.get("source_id"):
                    cited_in[scene].add(c["source_id"])
    liberties = set()
    lib = data / "liberties.json"
    if lib.is_file():
        liberties = {e["id"] for e in load_json(lib).get("liberties", []) if "id" in e}
    return {"sources": sources, "scenes": scenes, "standing": standing,
            "people": people, "liberties": liberties, "cited_in": cited_in}


def load_schema():
    return load_json(SCHEMA)


def schema_errors(rec, schema):
    try:
        import jsonschema
    except ImportError:
        return ["note: jsonschema is not installed, so the record's shape was NOT "
                "validated (the semantic checks below still ran)"], True
    v = jsonschema.Draft202012Validator(schema)
    out = []
    for e in sorted(v.iter_errors(rec), key=lambda e: list(e.absolute_path)):
        # A missing grade is reported once, in the semantic check's plain words.
        if e.validator == "required" and "'grade'" in e.message:
            continue
        where = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path)
        out.append(f"shape{where or ' (top level)'}: {e.message}")
    return out, False


def attributes_of(world, scene, rid):
    """{attribute: confidence} for one structure's sidecar (T-2641), read on first need."""
    cache = world.setdefault("attributes", {}).setdefault(scene, {})
    if rid not in cache:
        root = Path(world.get("root", ROOT))
        try:
            side = load_json(root / "data" / "sidecars" / scene / f"{rid}.json")
        except (OSError, ValueError):
            side = {}
        cache[rid] = {k: (v or {}).get("confidence") for k, v in (side.get("attributes") or {}).items()
                      if isinstance(v, dict)}
    return cache[rid]


def read_styles(styles=STYLES):
    """{stem: module} for every style-library module, and the files that would not parse."""
    out, bad = {}, []
    if Path(styles).is_dir():
        for p in sorted(Path(styles).glob("*.json")):
            try:
                out[p.stem] = load_json(p)
            except ValueError as e:
                bad.append(f"styles/{p.name}: not valid JSON ({e})")
    return out, bad


def rights_of(world, record):
    """A source record's rights_status, read on first need (T-2641's plate check)."""
    cache = world.setdefault("rights", {})
    if record not in cache:
        try:
            cache[record] = load_json(Path(world.get("root", ROOT)) / "data" / "sources" / f"{record}.json").get("rights_status")
        except (OSError, ValueError):
            cache[record] = None
    return cache[record]


# ------------------------------------------------------------------- the gate

def fact_errors(where, f, world):
    """Every refusal for one graded fact, in plain words."""
    errs = []
    grade = f.get("grade")
    if grade is None:
        return [f"{where}: a fact with no grade"]
    if grade not in GRADES:
        return [f"{where}: grade `{grade}` is not one of {', '.join(GRADES)}"]
    srcs = f.get("sources") or []
    if grade == "attested" and not srcs:
        errs.append(f"{where}: an Attested fact with no source")
    if grade in ("inferred", "reconstructed") and not (f.get("note") or "").strip():
        errs.append(f"{where}: an {grade.capitalize()} fact with no note saying what it rests on")
    for s in srcs:
        if s not in world["sources"]:
            errs.append(f"{where}: source `{s}` does not resolve in data/sources/")
    lib = f.get("liberty")
    if lib is not None and lib not in world["liberties"]:
        errs.append(f"{where}: liberty `{lib}` does not resolve in data/liberties.json")
    return errs


SHOWN_RIGHTS = ("public_domain", "no_known_restrictions")


def style_facts(mod):
    """(location, fact) for every graded fact in a style module."""
    if isinstance(mod.get("description"), dict):
        yield "description", mod["description"]
    for i, c in enumerate(mod.get("cues") or []):
        if isinstance(c, dict):
            yield f"cues[{i}]", c
    if isinstance(mod.get("plate"), dict):
        yield "plate", mod["plate"]
    for i, c in enumerate(mod.get("compare") or []):
        if isinstance(c, dict):
            yield f"compare[{i}]", c


def gate_style(stem, mod, world, schema):
    """Every refusal for one style-library module (T-2641). Empty means it may ship."""
    errs = []
    shape, _ = schema_errors(mod, schema)
    errs += [s for s in shape if not s.startswith("note:")]
    if not isinstance(mod, dict):
        return errs or ["the module is not a JSON object"]
    if mod.get("id") != stem:
        errs.append(f"id `{mod.get('id')}` is not the file's name `{stem}`")
    for where, f in style_facts(mod):
        errs += fact_errors(where, f, world)

    def limit(where, text, rule):
        if not isinstance(text, str):
            return
        nw = len(words(text))
        if "words" in rule and nw > rule["words"]:
            errs.append(f"{where}: {nw} words, over the limit of {rule['words']}")
        if "sentences" in rule and sentences(text) > rule["sentences"]:
            errs.append(f"{where}: {sentences(text)} sentences, over the limit of {rule['sentences']}")

    limit("description.text", (mod.get("description") or {}).get("text"), LIMITS["style.description"])
    for i, c in enumerate(mod.get("cues") or []):
        if isinstance(c, dict):
            limit(f"cues[{i}].text", c.get("text"), LIMITS["style.cue"])
    for i, c in enumerate(mod.get("compare") or []):
        if isinstance(c, dict):
            limit(f"compare[{i}].text", c.get("text"), LIMITS["style.compare"])
            # T-2642: a Compare line may point at another module, which the Design tab then
            # opens in place. It may not point at its own module, and where the module it
            # names exists, the line must call that style by the module's own name.
            other = c.get("style")
            if other is not None and other == mod.get("id"):
                errs.append(f"compare[{i}]: points at its own module `{other}`")
            elif isinstance(other, str) and isinstance(world.get("styles", {}).get(other), dict):
                theirs = world["styles"][other].get("name")
                if theirs != c.get("name"):
                    errs.append(f"compare[{i}]: calls `{other}` \"{c.get('name')}\", but that module "
                                f"names itself \"{theirs}\"")
    plate = mod.get("plate")
    if isinstance(plate, dict):
        scene, sid, record = plate.get("scene"), plate.get("structure"), plate.get("record")
        if scene not in world["scenes"]:
            errs.append(f"plate: scene `{scene}` is not a scene in data/scenes/")
        elif sid not in world["standing"].get(scene, set()):
            errs.append(f"plate: structure `{sid}` does not stand in the {scene} scene")
        if record not in world["sources"]:
            errs.append(f"plate: record `{record}` does not resolve in data/sources/")
        elif rights_of(world, record) not in SHOWN_RIGHTS:
            errs.append(f"plate: record `{record}` has rights_status `{rights_of(world, record)}`; "
                        f"a plate is shown only from a record that is {' or '.join(SHOWN_RIGHTS)}")
    for where, text in visitor_strings(mod, ""):
        for what in lint_string(text):
            errs.append(f"{where}: {what} in a string a visitor reads")
    return errs


def style_cited(mod):
    return {s for _, f in style_facts(mod) for s in (f.get("sources") or [])}


def attach_styles(docs, styles, world):
    """Carry every module into every scene's file, with its cited sources resolved."""
    ids = sorted(set().union(*[style_cited(m) for m in styles.values()])) if styles else []
    for doc in docs.values():
        doc["styles"] = {stem: copy.deepcopy(m) for stem, m in sorted(styles.items())}
        for s in ids:
            doc["sources"].setdefault(s, world["sources"][s])
    return docs


def gate(stem, rec, world, schema):
    """Every refusal for one record, in plain words. Empty means it may ship."""
    errs = []
    shape, _ = schema_errors(rec, schema)
    errs += [s for s in shape if not s.startswith("note:")]
    if not isinstance(rec, dict):
        return errs or ["the record is not a JSON object"]

    rid, scene = rec.get("id"), rec.get("scene")
    if rid != stem:
        errs.append(f"id `{rid}` is not the file's name `{stem}`")
    if scene not in world["scenes"]:
        errs.append(f"scene `{scene}` is not a scene in data/scenes/")
    elif rid not in world["standing"].get(scene, set()):
        errs.append(f"structure `{rid}` does not stand in the {scene} scene "
                    f"(no data/sidecars/{scene}/{rid}.json)")

    for where, f in facts(rec):
        errs += fact_errors(where, f, world)
    # T-3037: a build date the sources give as a phrase is placed at its earliest year.
    built = rec.get("built") if isinstance(rec.get("built"), dict) else {}
    if isinstance(built.get("phrase"), str):
        years = [int(y) for y in re.findall(r"\d{4}", built["phrase"])]
        if years and built.get("year") != min(years):
            errs.append(f"built: year {built.get('year')} is not the earliest year of its phrase "
                        f"'{built['phrase']}' ({min(years)})")

    # T-2641: a hotspot that names a sidecar attribute takes that attribute's own grade.
    if scene in world["scenes"] and rid in world["standing"].get(scene, set()):
        attrs = attributes_of(world, scene, rid)
        for i, h in enumerate(rec.get("onThisHouse") or []):
            name = h.get("attribute") if isinstance(h, dict) else None
            if name is None:
                continue
            if name not in attrs:
                errs.append(f"onThisHouse[{i}]: attribute `{name}` is not one of the structure's "
                            f"sidecar attributes (data/sidecars/{scene}/{rid}.json)")
            elif h.get("grade") in GRADES and attrs[name] != h.get("grade"):
                errs.append(f"onThisHouse[{i}]: graded {h.get('grade')}, but the sidecar grades "
                            f"attribute `{name}` {attrs[name]}")
    style = rec.get("style")
    if isinstance(style, str) and style not in world.get("styles", {}):
        errs.append(f"style `{style}` has no module in data/styles/")

    directory = world["people"].get(scene, {})
    for i, r in enumerate(rec.get("residents") or []):
        pid = r.get("person") if isinstance(r, dict) else None
        if pid is not None and pid not in directory:
            why = ("" if directory else f"; the {scene} scene has no people directory yet")
            errs.append(f"residents[{i}]: person `{pid}` does not resolve in "
                        f"data/sidecars/{scene}/people.json{why}")
    for i, s in enumerate(rec.get("story") or []):
        era = s.get("era") if isinstance(s, dict) else None
        if era is not None and era not in world["scenes"]:
            errs.append(f"story[{i}]: era `{era}` is not a scene")

    def limit(where, text, rule):
        if not isinstance(text, str):
            return
        nw = len(words(text))
        if "words" in rule and nw > rule["words"]:
            errs.append(f"{where}: {nw} words, over the limit of {rule['words']}")
        if "sentences" in rule:
            ns = sentences(text)
            if ns > rule["sentences"]:
                errs.append(f"{where}: {ns} sentences, over the limit of {rule['sentences']}")

    limit("summary", rec.get("summary"), LIMITS["summary"])
    for key, field in (("residents", "role"), ("lookFor", "text"), ("notable", "text"),
                       ("onThisHouse", "text"), ("onThisHouse", "detail")):
        for i, item in enumerate(rec.get(key) or []):
            if isinstance(item, dict):
                limit(f"{key}[{i}].{field}", item.get(field), LIMITS[f"{key}.{field}"])

    for where, text in visitor_strings(rec, ""):
        for what in lint_string(text):
            errs.append(f"{where}: {what} in a string a visitor reads")
    return errs


# ------------------------------------------------------------------- the compiler

def impact(n):
    score = 1.0
    if n.get("surprising"):
        score *= IMPACT["surprising"]
    if n.get("about") == "person":
        score *= IMPACT["person"]
    if n.get("visible_from_street"):
        score *= IMPACT["visible_from_street"]
    if n.get("grade") == "attested":
        score *= IMPACT["attested"]
    return score


def compile_record(rec, world):
    out = copy.deepcopy(rec)
    directory = world["people"].get(rec["scene"], {})
    for r in out["residents"]:
        r["name"] = directory[r["person"]]["name"]
    ranked = []
    for i, n in enumerate(out["notable"]):
        n.setdefault("surprising", False)
        n.setdefault("visible_from_street", False)
        n["impact"] = impact(n)
        ranked.append((-n["impact"], i, n))
    out["notable"] = [n for _, _, n in sorted(ranked, key=lambda t: (t[0], t[1]))]
    out["story"] = [s for _, s in sorted(enumerate(out["story"]), key=lambda t: (t[1]["date"], t[0]))]
    counts = {g: 0 for g in GRADES}
    for where, f in facts(out):
        if where.split("[")[0] in UNCOUNTED:
            continue
        counts[f["grade"]] += 1
    counts["facts"] = sum(counts[g] for g in GRADES)
    out["grades"] = counts
    return out


def cited(rec):
    return {s for _, f in facts(rec) for s in (f.get("sources") or [])}


def compile_all(records, world):
    """records: {stem: record}, all already through the gate. -> {scene: document}."""
    docs = {}
    for scene in world["scenes"]:
        mine = {stem: r for stem, r in sorted(records.items()) if r["scene"] == scene}
        ids = sorted(set().union(*[cited(r) for r in mine.values()])) if mine else []
        docs[scene] = {
            "scene": scene,
            "standard": ("The Inspect app's building summaries for this scene, compiled from "
                         "the authored records by tools/compile_summaries.py. A structure "
                         "not listed here takes the templated fallback."),
            "count": len(mine),
            "summaries": {stem: compile_record(r, world) for stem, r in mine.items()},
            "sources": {s: world["sources"][s] for s in ids},
            # The recorded date of every source this scene's structures or summaries cite, as
            # the source record writes it (T-2644). Undated sources are absent, never guessed.
            "source_dates": {s: world["sources"][s]["date"]
                             for s in sorted(set(ids) | world.get("cited_in", {}).get(scene, set()))
                             if "date" in world["sources"].get(s, {})},
        }
    return docs


def read_records(summaries=SUMMARIES):
    out, bad = {}, []
    if not Path(summaries).is_dir():
        return out, bad
    for p in sorted(Path(summaries).glob("*.json")):
        try:
            out[p.stem] = load_json(p)
        except ValueError as e:
            bad.append(f"{p.name}: not valid JSON ({e})")
    return out, bad


def run(write, summaries=SUMMARIES, out_dir=OUT, root=ROOT, quiet=False, world=None, styles_dir=None):
    world = world or load_world(root)
    world.setdefault("root", Path(root))
    schema = load_schema()
    styles, refusals = read_styles(styles_dir if styles_dir is not None else Path(root) / "data" / "styles")
    world.setdefault("styles", styles)
    style_schema = load_json(STYLE_SCHEMA)
    for stem, mod in world["styles"].items():
        for e in gate_style(stem, mod, world, style_schema):
            refusals.append(f"styles/{stem}.json: {e}")
    records, more = read_records(summaries)
    refusals += more
    _, no_validator = schema_errors({}, schema)
    for stem, rec in records.items():
        for e in gate(stem, rec, world, schema):
            refusals.append(f"{stem}.json: {e}")
    if refusals:
        for r in refusals:
            print(f"FAIL: {r}")
        print(f"FAIL: {len(refusals)} refusal(s) in {len(records)} summary record(s); "
              "nothing was compiled")
        return 1
    docs = attach_styles(compile_all(records, world), world["styles"], world)
    if write:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        for old in Path(out_dir).glob("*.json"):
            if old.stem not in docs:
                old.unlink()
        for scene, doc in docs.items():
            (Path(out_dir) / f"{scene}.json").write_text(dumps(doc), encoding="utf-8")
    if not quiet:
        nfacts = sum(r["grades"]["facts"] for d in docs.values() for r in d["summaries"].values())
        if no_validator:
            print("note: jsonschema is not installed; record shapes were not validated")
        print(f"OK: {len(records)} summary record(s), {nfacts} graded fact(s), "
              f"{len(world['styles'])} style module(s), "
              f"{len(docs)} scene file(s) {'written' if write else 'compiled in memory'}")
    return 0


# ------------------------------------------------------------------- self-test

def fixture_world():
    """A tiny world for the gate to resolve against. These ids are a test fixture, not
    citations: they never leave this function and nothing ships from them."""
    return {
        "sources": {"fixture_source": {"citation": "A fixture source record, used only by this self-test.",
                                       "type": "book", "date": "1900"}},
        "scenes": ["1835", "1904"],
        "standing": {"1835": set(), "1904": {"fixture_house"}},
        "people": {"1835": {}, "1904": {"fixture_person": {"name": "A. Fixture", "grade": "attested"}}},
        "liberties": {"L1"},
        # T-2641: the fixture house's sidecar attributes, its style module, and the fixture
        # source's rights, so the gate reads none of them from the real tree.
        "attributes": {"1904": {"fixture_house": {"walls": "attested", "window_heights": "reconstructed"}}},
        "styles": {"fixture_style": fixture_style()},
        "rights": {"fixture_source": "public_domain"},
    }


def fixture_style():
    """The smallest style module that passes. A fixture: its words are about the gate."""
    src = ["fixture_source"]
    return {
        "id": "fixture_style", "name": "Fixture Revival",
        "description": {"text": "A style that exists only in this test. It has two lines.",
                        "grade": "inferred", "sources": src, "note": "Worked out from the fixture."},
        "cues": [{"text": "Fixture stone on the street", "grade": "attested", "sources": src}],
        "plate": {"picture": "fixture-picture", "structure": "fixture_house", "scene": "1904",
                  "record": "fixture_source", "caption": "The fixture house", "grade": "attested",
                  "sources": src},
        "compare": [{"name": "Other Fixture", "style": "other_fixture", "text": "A line about another style.",
                     "grade": "attested", "sources": src}],
    }


def minimal_record():
    """The smallest record that passes. A fixture: its words are about the gate, not about
    any building, and it is never written under data/summaries/."""
    src = ["fixture_source"]
    return {
        "id": "fixture_house", "scene": "1904",
        "name": "The Fixture House",
        "address": "1800 S. Fixture Ave. · at 18th St.",
        "status": {"text": "Still standing", "today": "A test fixture", "grade": "attested", "sources": src},
        "built": {"year": 1887, "grade": "inferred", "note": "Worked out from the fixture's own dates."},
        "use": "Home",
        "summary": ("This record exists only to prove the gate reads a valid file. "
                    "Mr. H. H. Fixture never lived at 1800 S. Fixture Ave. at all. "
                    "Nothing in it ships to a visitor."),
        "key": [{"label": "Architect", "value": "H. H. Fixture", "grade": "attested", "sources": src}],
        "residents": [{"person": "fixture_person", "role": "A person who exists only in this test",
                       "grade": "attested", "sources": src}],
        "lookFor": [{"text": "The front door", "feature": "front_door",
                     "camera": {"yaw": -82, "pitch": 6}, "grade": "reconstructed",
                     "note": "Placed where a door would be.", "liberty": "L1"}],
        "notable": [
            {"text": "A plain fact about the building.", "about": "structure",
             "grade": "reconstructed", "note": "A fixture."},
            {"text": "A surprising fact about a person, seen from the street.", "about": "person",
             "surprising": True, "visible_from_street": True, "grade": "attested", "sources": src},
            {"text": "A surprising fact about the building.", "about": "structure",
             "surprising": True, "grade": "inferred", "note": "A fixture."},
        ],
        "style": "fixture_style",
        "onThisHouse": [
            {"text": "Stone walls", "detail": "Stone on the street.", "attribute": "walls",
             "camera": {"yaw": 90, "pitch": 4}, "grade": "attested", "sources": src},
            {"text": "Window heights", "detail": "Ours.", "attribute": "window_heights",
             "grade": "reconstructed", "note": "Bounded by the fixture.", "liberty": "L1"},
        ],
        "story": [{"date": "1887-05", "text": "Finished.", "era": "1904", "grade": "attested", "sources": src},
                  {"date": "1885", "text": "Designed.", "era": "1904", "grade": "attested", "sources": src}],
    }


def self_test():
    fails = []
    world = fixture_world()
    schema = load_schema()

    def expect(cond, what):
        if not cond:
            fails.append(what)

    real = load_world()
    expect(len(real["sources"]) > 0 and "no_such_source_planted" not in real["sources"],
           "the real tree's data/sources/ loads, and the planted id below is not in it")

    ok = minimal_record()
    errs = gate("fixture_house", ok, world, schema)
    expect(errs == [], f"the minimal valid record passes the gate (it was refused: {errs})")
    expect(sentences(ok["summary"]) == 3, "initials and street abbreviations do not end a sentence "
           f"(counted {sentences(ok['summary'])} in the fixture summary)")

    # Compile it to the published form, through the real writer, into a scratch tree.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "in").mkdir()
        (tmp / "in" / "fixture_house.json").write_text(dumps(ok), encoding="utf-8")
        rc = run(write=True, summaries=tmp / "in", out_dir=tmp / "out", world=world)
        expect(rc == 0, "--build compiles the minimal record")
        written = sorted(p.name for p in (tmp / "out").glob("*.json"))
        expect(written == ["1835.json", "1904.json"], f"a file per scene, even an empty one (got {written})")
        pub = load_json(tmp / "out" / "1904.json")
        empty = load_json(tmp / "out" / "1835.json")
        expect(empty["count"] == 0 and empty["summaries"] == {}, "a scene with no records ships an empty file")
        rec = pub["summaries"].get("fixture_house", {})
        expect(pub["count"] == 1 and rec.get("name") == "The Fixture House",
               "the minimal record compiles into its scene's file")
        expect(rec.get("residents", [{}])[0].get("name") == "A. Fixture",
               "a resident carries the name from the people directory")
        order = [n["text"] for n in rec.get("notable", [])]
        expect(order[:1] == ["A surprising fact about a person, seen from the street."]
               and order[-1] == "A plain fact about the building.",
               f"notable facts are ranked by impact (got {order})")
        expect(rec.get("notable", [{}])[0].get("impact") == 3 * 2 * 2 * 1.5,
               "the top fact scores surprising x3, person x2, street x2, Attested x1.5 = 18")
        expect([s["date"] for s in rec.get("story", [])] == ["1885", "1887-05"], "the story is in date order")
        expect(rec.get("grades") == {"attested": 6, "inferred": 2, "reconstructed": 2, "facts": 10},
               f"the facts are counted by grade, the Design tab's hotspots not among them (got {rec.get('grades')})")
        expect(len(rec.get("onThisHouse", [])) == 2, "the hotspots are carried into the compiled record")
        expect(pub.get("styles", {}).get("fixture_style", {}).get("name") == "Fixture Revival"
               and empty.get("styles", {}).get("fixture_style") is not None,
               "every style module is carried into every scene's file, an empty scene's too")
        expect(set(pub["sources"]) == {"fixture_source"} and "citation" in pub["sources"]["fixture_source"],
               "every cited source resolves to its citation in the file")

    # And through the same entry point check.sh and publish.sh call: a refused record on
    # disk fails the run and writes nothing, so a publish cannot ship it.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "in").mkdir()
        bad = minimal_record()
        del bad["key"][0]["grade"]
        (tmp / "in" / "fixture_house.json").write_text(dumps(bad), encoding="utf-8")
        print("-- planted on disk: a refused record handed to --build")
        rc = run(write=True, summaries=tmp / "in", out_dir=tmp / "out", world=world)
        expect(rc == 1 and not (tmp / "out").exists(),
               "--build refuses a bad record on disk and writes no scene file")

    # Each planted fault must be refused, by name. The transcript below is meant to look bad.
    def plant(label, needle, mutate, stem="fixture_house"):
        rec = minimal_record()
        mutate(rec)
        got = gate(stem, rec, world, schema)
        print(f"-- planted: {label}")
        for e in got:
            print(f"   FAIL: {e}")
        if not any(needle in e for e in got):
            fails.append(f"the gate did not refuse {label} (wanted `{needle}`, got {got})")

    def drop_grade(r): del r["key"][0]["grade"]
    def unsourced(r): r["notable"][1]["sources"] = []
    def long_summary(r): r["summary"] = " ".join(["word"] * 61) + "."
    def many_sentences(r): r["summary"] = "One. Two. Three. Four."
    def snake(r): r["summary"] = "The prairie_1800 lot held a house."
    def bad_source(r): r["status"]["sources"] = ["no_such_source_planted"]
    def long_role(r): r["residents"][0]["role"] = " ".join(["word"] * 13)
    def long_lookfor(r): r["lookFor"][0]["text"] = " ".join(["word"] * 9)
    def long_notable(r): r["notable"][0]["text"] = " ".join(["word"] * 26)
    def path(r): r["key"][0]["value"] = "See data/street_grid/1904.json"
    def ticket(r): r["notable"][0]["text"] = "Fixed under T-2635."
    def link(r): r["status"]["today"] = "https://example.test/house"
    def bad_person(r): r["residents"][0]["person"] = "no_such_person"
    def no_note(r): del r["built"]["note"]
    def bad_grade(r): r["key"][0]["grade"] = "documented"
    def bad_liberty(r): r["lookFor"][0]["liberty"] = "L-no-such-liberty"
    def not_standing(r): r["scene"] = "1835"
    def bad_era(r): r["story"][0]["era"] = "1700"
    def stray_field(r): r["key"][0]["why"] = "an unknown field"
    def story_ungraded(r): del r["story"][1]["grade"]
    def phrase_year(r): r["built"]["phrase"] = "1864 or 1875"; r["built"]["year"] = 1875

    plant("a fact with no grade", "a fact with no grade", drop_grade)
    plant("an ungraded story entry", "story[1]: a fact with no grade", story_ungraded)
    plant("an unsourced Attested fact", "an Attested fact with no source", unsourced)
    plant("an over-length summary", "61 words, over the limit of 60", long_summary)
    plant("a four-sentence summary", "4 sentences, over the limit of 3", many_sentences)
    plant("a snake_case id in a string", "an id or snake_case word `prairie_1800`", snake)
    plant("an unresolved source id", "source `no_such_source_planted` does not resolve", bad_source)
    plant("an over-length role", "13 words, over the limit of 12", long_role)
    plant("an over-length Look-for line", "9 words, over the limit of 8", long_lookfor)
    plant("an over-length notable fact", "26 words, over the limit of 25", long_notable)
    plant("a file path in a string", "a file path", path)
    plant("a ticket number in a string", "a ticket number `T-2635`", ticket)
    plant("a link in a string", "a link", link)
    plant("an unresolved person id", "person `no_such_person` does not resolve", bad_person)
    plant("an Inferred fact with no note", "an Inferred fact with no note", no_note)
    plant("a built phrase not placed at its earliest year", "is not the earliest year of its phrase", phrase_year)
    plant("a grade outside the ladder", "grade `documented` is not one of", bad_grade)
    plant("an unresolved liberty", "liberty `L-no-such-liberty` does not resolve", bad_liberty)
    plant("a structure that does not stand in its scene", "does not stand in the 1835 scene", not_standing)
    plant("a story era that is not a scene", "era `1700` is not a scene", bad_era)
    plant("a file whose name is not its id", "is not the file's name", lambda r: None, stem="other_house")
    if "jsonschema" in sys.modules or _have_jsonschema():
        plant("a field the schema does not know", "Additional properties are not allowed", stray_field)

    # T-2641: the Design tab's hotspots, and a record's link to its style module.
    def hot_regraded(r): r["onThisHouse"][0]["grade"] = "inferred"; r["onThisHouse"][0]["note"] = "x"
    def hot_attr(r): r["onThisHouse"][0]["attribute"] = "no_such_attribute"
    def hot_long(r): r["onThisHouse"][0]["text"] = " ".join(["word"] * 9)
    def hot_detail(r): r["onThisHouse"][0]["detail"] = " ".join(["word"] * 17)
    def hot_ungraded(r): del r["onThisHouse"][1]["grade"]
    def hot_unsourced(r): r["onThisHouse"][0]["sources"] = []
    def hot_snake(r): r["onThisHouse"][0]["detail"] = "Read from window_heights."
    def no_style(r): r["style"] = "no_such_style"
    plant("a hotspot graded apart from its sidecar attribute", "but the sidecar grades attribute `walls` attested", hot_regraded)
    plant("a hotspot naming an attribute the sidecar lacks", "attribute `no_such_attribute` is not one of", hot_attr)
    plant("an over-length hotspot", "onThisHouse[0].text: 9 words, over the limit of 8", hot_long)
    plant("an over-length hotspot line", "onThisHouse[0].detail: 17 words, over the limit of 16", hot_detail)
    plant("an ungraded hotspot", "onThisHouse[1]: a fact with no grade", hot_ungraded)
    plant("an unsourced Attested hotspot", "onThisHouse[0]: an Attested fact with no source", hot_unsourced)
    plant("a snake_case word in a hotspot", "an id or snake_case word `window_heights`", hot_snake)
    plant("a style with no module", "style `no_such_style` has no module", no_style)

    style_schema = load_json(STYLE_SCHEMA)
    good = gate_style("fixture_style", fixture_style(), world, style_schema)
    expect(good == [], f"the minimal style module passes the gate (it was refused: {good})")

    def plant_style(label, needle, mutate, stem="fixture_style"):
        mod = fixture_style()
        mutate(mod)
        got = gate_style(stem, mod, world, style_schema)
        print(f"-- planted in a style module: {label}")
        for e in got:
            print(f"   FAIL: {e}")
        if not any(needle in e for e in got):
            fails.append(f"the style gate did not refuse {label} (wanted `{needle}`, got {got})")

    def cue_long(m): m["cues"][0]["text"] = " ".join(["word"] * 9)
    def cue_unsourced(m): m["cues"][0]["sources"] = []
    def cue_no_note(m): m["cues"][0] = {"text": "A guess", "grade": "inferred"}
    def cue_bad_source(m): m["cues"][0]["sources"] = ["no_such_source_planted"]
    def desc_long(m): m["description"]["text"] = "One. Two. Three."
    def compare_long(m): m["compare"][0]["text"] = " ".join(["word"] * 13)
    def plate_rights(m): world["rights"]["fixture_source"] = "check_required"
    def plate_scene(m): m["plate"]["structure"] = "no_such_house"
    def style_snake(m): m["name"] = "fixture_style"
    def five_cues(m): m["cues"] = m["cues"] * 5
    plant_style("an over-length cue", "cues[0].text: 9 words, over the limit of 8", cue_long)
    plant_style("an unsourced Attested cue", "cues[0]: an Attested fact with no source", cue_unsourced)
    plant_style("an Inferred cue with no note", "cues[0]: an Inferred fact with no note", cue_no_note)
    plant_style("a cue citing a source that does not exist", "source `no_such_source_planted` does not resolve", cue_bad_source)
    plant_style("a three-sentence description", "3 sentences, over the limit of 2", desc_long)
    plant_style("an over-length Compare line", "compare[0].text: 13 words, over the limit of 12", compare_long)
    plant_style("a plate whose structure does not stand", "structure `no_such_house` does not stand", plate_scene)
    plant_style("a snake_case id in a module's name", "an id or snake_case word `fixture_style`", style_snake)
    plant_style("a file whose name is not its id", "is not the file's name", lambda m: None, stem="other_style")
    if _have_jsonschema():
        plant_style("five cues", "is too long", five_cues)
    plant_style("a plate from a record whose rights are not cleared", "has rights_status `check_required`", plate_rights)
    world["rights"]["fixture_source"] = "public_domain"
    # T-2642: Compare lines that point between modules.
    def compare_self(m): m["compare"][0]["style"] = "fixture_style"
    plant_style("a Compare line pointing at its own module", "points at its own module", compare_self)
    world["styles"]["other_fixture"] = {"id": "other_fixture", "name": "Another Fixture"}
    plant_style("a Compare line that misnames the module it points at", "but that module names itself", lambda m: None)
    del world["styles"]["other_fixture"]

    for f in fails:
        print(f"FAIL: {f}")
    if fails:
        return 1
    print("OK: the minimal record compiles to its scene's file, and every planted fault was refused by name")
    return 0


def _have_jsonschema():
    try:
        import jsonschema  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return run(write=a.build)


if __name__ == "__main__":
    sys.exit(main())
