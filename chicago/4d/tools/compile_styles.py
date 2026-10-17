#!/usr/bin/env python3
"""Gate the style library: data/styles/<id>.json, one module per architectural style (T-2642).

    python3 tools/compile_styles.py --check       gate every module; write nothing
    python3 tools/compile_styles.py --self-test   plant each fault and require it refused by name

Design doc "Field Navigator Mk II", section 12 "Style library": shared modules (Greek
Revival, Italianate, Second Empire, Queen Anne, Chicago School; Richardsonian Romanesque is
T-2641's), each with four "how to spot it" cues and a reference plate, which the Inspect app's
Design tab shows exactly as written. Shaped by data/style.schema.json. This holds them to:

  - a grade on every fact (the description, each cue, the plate's claim that its building is
    of this style), from the data's own ladder; sources on every attested fact, each resolving
    in data/sources/; a note on every inferred or reconstructed one;
  - the lengths: a cue at most 4 words and its explainer at most 15, the description at most
    20 words in one sentence, the comparison at most 8 words, a caption at most 15;
  - no id, snake_case word, file path, link or ticket number in anything a visitor reads —
    the summary records' own lint (compile_summaries.lint_string), imported, so the two
    gates cannot disagree about what a visitor may see;
  - AGENTS.md hard rule 6 for the plate: its own source record's rights allow display
    (public_domain, no_known_restrictions or cleared); its file is committed under
    assets/plates/styles/ with an entry in assets/LICENSES.md and the sha256 it records; and
    a plate building, where one is named, stands in the plate's scene;
  - a module with no plate says why in `plate_gap`, so a missing plate is a stated gap, not
    a silent one;
  - and every summary record's `style` names a module that exists (or is null).

It compiles nothing yet: nothing reads the library until the Design tab (T-2641) lands, and
that ticket decides what the app fetches.
"""

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from compile_summaries import GRADES, lint_string, load_world, sentences, words  # noqa: E402

DATA = ROOT / "data"
SCHEMA = DATA / "style.schema.json"
STYLES = DATA / "styles"
SUMMARIES = DATA / "summaries"
ASSETS = ROOT / "assets"

LIMITS = {"cue": 4, "explain": 15, "summary": 20, "compare": 8, "caption": 15}
DISPLAYABLE = {"public_domain", "no_known_restrictions", "cleared"}
DATA_KEYS = {"id", "grade", "sources", "file", "sha256", "source", "building", "scene",
             "display_crop", "period"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def visitor_strings(node, where=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k not in DATA_KEYS:
                yield from visitor_strings(v, f"{where}.{k}" if where else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from visitor_strings(v, f"{where}[{i}]")
    elif isinstance(node, str):
        yield where, node


def facts(rec):
    if isinstance(rec.get("about"), dict):
        yield "about", rec["about"]
    for i, c in enumerate(rec.get("cues") or []):
        if isinstance(c, dict):
            yield f"cues[{i}]", c
    plate = rec.get("plate")
    if isinstance(plate, dict) and isinstance(plate.get("shows_style"), dict):
        yield "plate.shows_style", plate["shows_style"]


def world_for(root=ROOT):
    w = load_world(root)
    rights = {}
    for p in sorted((Path(root) / "data" / "sources").glob("*.json")):
        try:
            rights[p.stem] = load_json(p).get("rights_status")
        except (OSError, ValueError):
            continue
    w["rights"] = rights
    lic = Path(root) / "assets" / "LICENSES.md"
    w["licenses"] = lic.read_text(encoding="utf-8") if lic.is_file() else ""
    w["assets"] = Path(root) / "assets"
    return w


def schema_errors(rec, schema):
    try:
        import jsonschema
    except ImportError:
        return []
    v = jsonschema.Draft202012Validator(schema)
    out = []
    for e in sorted(v.iter_errors(rec), key=lambda e: list(e.absolute_path)):
        if e.validator == "required" and "'grade'" in e.message:
            continue
        where = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path)
        out.append(f"shape{where or ' (top level)'}: {e.message}")
    return out


def gate(stem, rec, world, schema):
    errs = list(schema_errors(rec, schema))
    if not isinstance(rec, dict):
        return errs or ["the module is not a JSON object"]
    if rec.get("id") != stem:
        errs.append(f"id `{rec.get('id')}` is not the file's name `{stem}`")

    for where, f in facts(rec):
        grade = f.get("grade")
        if grade is None:
            errs.append(f"{where}: a fact with no grade")
            continue
        if grade not in GRADES:
            errs.append(f"{where}: grade `{grade}` is not one of {', '.join(GRADES)}")
            continue
        srcs = f.get("sources") or []
        if grade == "attested" and not srcs:
            errs.append(f"{where}: an Attested fact with no source")
        if grade in ("inferred", "reconstructed") and not (f.get("note") or "").strip():
            errs.append(f"{where}: an {grade.capitalize()} fact with no note saying what it rests on")
        for s in srcs:
            if s not in world["sources"]:
                errs.append(f"{where}: source `{s}` does not resolve in data/sources/")

    def limit(where, text, n, one_sentence=False):
        if not isinstance(text, str):
            return
        if len(words(text)) > n:
            errs.append(f"{where}: {len(words(text))} words, over the limit of {n}")
        if one_sentence and sentences(text) > 1:
            errs.append(f"{where}: {sentences(text)} sentences, over the limit of 1")

    about = rec.get("about") or {}
    limit("about.summary", about.get("summary"), LIMITS["summary"], one_sentence=True)
    limit("about.compare", about.get("compare"), LIMITS["compare"])
    period = about.get("period") or {}
    if isinstance(period.get("from"), int) and isinstance(period.get("to"), int) \
            and period["from"] > period["to"]:
        errs.append("about.period: `from` is after `to`")
    cues = rec.get("cues") or []
    if len(cues) != 4:
        errs.append(f"cues: {len(cues)} cue(s), and a module has exactly four")
    for i, c in enumerate(cues):
        if isinstance(c, dict):
            limit(f"cues[{i}].cue", c.get("cue"), LIMITS["cue"])
            limit(f"cues[{i}].explain", c.get("explain"), LIMITS["explain"])

    plate = rec.get("plate")
    if plate is None:
        if not (rec.get("plate_gap") or "").strip():
            errs.append("plate: no plate and no `plate_gap` saying why")
    elif isinstance(plate, dict):
        if rec.get("plate_gap"):
            errs.append("plate_gap: set on a module that has a plate")
        limit("plate.caption", plate.get("caption"), LIMITS["caption"])
        src = plate.get("source")
        if src not in world["sources"]:
            errs.append(f"plate.source: `{src}` does not resolve in data/sources/")
        elif world["rights"].get(src) not in DISPLAYABLE:
            errs.append(f"plate.source: `{src}` is `{world['rights'].get(src)}`, and a plate is "
                        f"shown, so its rights must be one of {', '.join(sorted(DISPLAYABLE))} "
                        f"(hard rule 6)")
        rel = plate.get("file") or ""
        path = world["assets"] / rel
        if not rel.startswith("plates/styles/"):
            errs.append(f"plate.file: `{rel}` is not under assets/plates/styles/")
        elif not path.is_file():
            errs.append(f"plate.file: assets/{rel} is not committed")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != plate.get("sha256"):
                errs.append(f"plate.sha256: assets/{rel} hashes to {digest}, not the recorded "
                            f"{plate.get('sha256')}")
            if rel not in world["licenses"]:
                errs.append(f"plate.file: assets/{rel} has no entry in assets/LICENSES.md "
                            f"(hard rule 6)")
        building, scene = plate.get("building"), plate.get("scene")
        if building is not None:
            if scene not in world["scenes"]:
                errs.append(f"plate.scene: `{scene}` is not a scene, and a plate building needs one")
            elif building not in world["standing"].get(scene, set()):
                errs.append(f"plate.building: `{building}` does not stand in the {scene} scene")

    for where, text in visitor_strings(rec):
        for what in lint_string(text):
            errs.append(f"{where}: {what} in a string a visitor reads")
    return errs


def summary_style_refusals(modules, summaries=SUMMARIES):
    out = []
    for p in sorted(Path(summaries).glob("*.json")) if Path(summaries).is_dir() else []:
        try:
            style = load_json(p).get("style")
        except ValueError:
            continue
        if style is not None and style not in modules:
            out.append(f"{p.name}: style `{style}` has no module in data/styles/")
    return out


def read_modules(styles=STYLES):
    out, bad = {}, []
    for p in sorted(Path(styles).glob("*.json")) if Path(styles).is_dir() else []:
        try:
            out[p.stem] = load_json(p)
        except ValueError as e:
            bad.append(f"{p.name}: not valid JSON ({e})")
    return out, bad


def run(styles=STYLES, summaries=SUMMARIES, world=None, quiet=False):
    world = world or world_for()
    schema = load_json(SCHEMA)
    modules, refusals = read_modules(styles)
    for stem, rec in modules.items():
        refusals += [f"{stem}.json: {e}" for e in gate(stem, rec, world, schema)]
    refusals += summary_style_refusals(modules, summaries)
    if refusals:
        for r in refusals:
            print(f"FAIL: {r}")
        print(f"FAIL: {len(refusals)} refusal(s) in {len(modules)} style module(s)")
        return 1
    if not quiet:
        gaps = [s for s, r in modules.items() if r.get("plate") is None]
        n = sum(1 for r in modules.values() for _ in facts(r))
        print(f"OK: {len(modules)} style module(s), {n} graded fact(s), "
              f"{len(modules) - len(gaps)} plate(s) cleared"
              + (f"; no plate yet for {', '.join(gaps)} (stated in plate_gap)" if gaps else ""))
    return 0


def self_test():
    schema = load_json(SCHEMA)
    world = world_for()
    base, _ = read_modules()
    good = copy.deepcopy(base["chicago_school"])
    fails = 0

    def expect(label, rec, needle, stem="chicago_school"):
        nonlocal fails
        errs = gate(stem, rec, world, schema)
        hit = any(needle in e for e in errs) if needle else not errs
        print(f"  {'ok  ' if hit else 'FAIL'} {label}" + ("" if hit else f": {errs[:3]}"))
        fails += 0 if hit else 1

    expect("the committed module passes", good, None)

    def planted(label, mutate, needle):
        rec = copy.deepcopy(good)
        mutate(rec)
        expect(label, rec, needle)

    planted("a cue with no grade", lambda r: r["cues"][0].pop("grade"), "a fact with no grade")
    planted("an Attested cue with no source", lambda r: r["cues"][1].pop("sources"), "an Attested fact with no source")
    planted("an Inferred plate claim with no note",
            lambda r: r["plate"]["shows_style"].update(grade="inferred"), "with no note")
    planted("an invented source", lambda r: r["cues"][2].update(sources=["no_such_source"]), "does not resolve")
    planted("a five-word cue", lambda r: r["cues"][0].update(cue="one two three four five"), "over the limit of 4")
    planted("a sixteen-word explainer", lambda r: r["cues"][0].update(explain=" ".join(["word"] * 16)), "over the limit of 15")
    planted("three cues", lambda r: r["cues"].pop(), "exactly four")
    planted("a snake_case id in a cue", lambda r: r["cues"][0].update(cue="See steel_frame now"), "snake_case")
    planted("a ticket number in a caption", lambda r: r["plate"].update(caption="Fixed under T-2642."), "ticket number")
    planted("a plate whose source is check_required",
            lambda r: r["plate"].update(source="phmc_pa_architectural_field_guide"), "hard rule 6")
    planted("a plate file that is not committed",
            lambda r: r["plate"].update(file="plates/styles/no_such_plate.jpg"), "is not committed")
    planted("a plate whose bytes changed", lambda r: r["plate"].update(sha256="0" * 64), "hashes to")
    planted("a plate building not in its scene",
            lambda r: r["plate"].update(building="no_such_house", scene="1904"), "does not stand in the 1904 scene")
    planted("no plate and no stated gap", lambda r: r.update(plate=None), "no `plate_gap`")

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "x.json").write_text(json.dumps({"style": "no_such_style"}))
        got = summary_style_refusals(base, tmp)
        hit = bool(got) and "no module" in got[0]
        print(f"  {'ok  ' if hit else 'FAIL'} a summary record naming a style with no module")
        fails += 0 if hit else 1

    # A plate file committed without its licence row: build the world with LICENSES.md emptied.
    w2 = dict(world, licenses="")
    errs = gate("chicago_school", copy.deepcopy(good), w2, schema)
    hit = any("no entry in assets/LICENSES.md" in e for e in errs)
    print(f"  {'ok  ' if hit else 'FAIL'} a plate with no row in assets/LICENSES.md")
    fails += 0 if hit else 1

    print(f"compile_styles self-test: {'FAIL' if fails else 'OK'} "
          f"({fails} assertion(s) did not fire as required)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    return self_test() if a.self_test else run()


if __name__ == "__main__":
    sys.exit(main())
