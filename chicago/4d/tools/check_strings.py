#!/usr/bin/env python3
"""Gate the Navigator string table, js/strings/ (T-2624).

    python3 tools/check_strings.py --check       gate every section and the page's markup
    python3 tools/check_strings.py --self-test   plant each fault and require it refused by name

Design doc "Field Navigator Mk II" section 03, "Audience, voice and terms". The arrival,
the HUD and the Navigator read their visible strings from one table of sections, one file
per app under renderers/web/js/strings/ (later apps add a file of their own), and each
Navigator app's manifest (js/apps/<id>.js) carries its own name and screen code. A visitor
reads those strings exactly as written, so this refuses, in every section:

  - a locked term in another spelling: a grade word in lower case or any case but its own
    ("attested", "ATTESTED" inside a sentence; a string wholly in capitals is machine lore,
    a screen code such as "SCR 07 · CONFIDENCE VIEW", and may carry it in capitals),
    "Confidence View" or any other casing of Confidence view, and Sources, Liberties or
    Jaunts in a casing that is neither theirs nor plain prose lower case;
  - a retired term (documented, conjectural, Evidence, Citations) and an old name section 03
    renamed (Coordinate, Travel, Controls, Firms, Modeled phase, Present status, Not
    recorded …), each named with the word that replaced it;
  - an id, snake_case word, file path, link or ticket number (compile_summaries.lint_string,
    imported, so this gate and the summary and Guide gates agree), and a sentence over 20
    words — except that a string only Researcher mode shows, a key with a `researcher`
    segment (T-2668; tools/check_visitor_ui.py has the contract), may run a sentence past
    20 words. It keeps every other rule: the owner, 2026-10-18 (T-2657), "rewrite the records
    so you are not referring to internal ticket numbers or internal record ids in researcher
    or educator mode", so it still refuses an id, a file path and a ticket number;
  - in renderers/web/index.html, a [data-str] / [data-str-title] / [data-str-label] naming a
    key the table does not hold, or whose first-paint words differ from the table's (the
    page would change under the visitor as the module arrives);
  - and drift from the Guide (T-2662): when tools/check_guide.py and data/guide/glossary.json
    are in the tree, the locked and retired lists must equal its LOCKED and RETIRED, and each
    term's plain line must equal the glossary's.

The table is JavaScript and the lint is Python, so the sections are read by running node
over them (every file in js/strings/, imported and listed by its own `entries()`).
"""

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from compile_summaries import lint_string, words  # noqa: E402

WEB = ROOT / "renderers" / "web"
STRINGS = WEB / "js" / "strings"
INDEX = WEB / "index.html"
MAX_SENTENCE_WORDS = 20

DUMP = r"""
import { readdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const dir = process.argv[1];
const mod = await import(pathToFileURL(path.join(dir, 'index.js')));
for (const f of readdirSync(dir).filter(f => f.endsWith('.js')).sort()) await import(pathToFileURL(path.join(dir, f)));
const terms = await import(pathToFileURL(path.join(dir, 'terms.js')));
// Each Navigator app's manifest (js/apps/<id>.js) carries its own name and screen code:
// that app's section of the table, linted with the rest.
const apps = [];
const appDir = path.join(dir, '..', 'apps');
for (const f of readdirSync(appDir).filter(f => f.endsWith('.js') && f !== 'index.js' && !f.endsWith('-view.js')).sort()) {
  const app = (await import(pathToFileURL(path.join(appDir, f)))).default;
  if (app?.id) for (const k of ['label', 'code']) if (typeof app[k] === 'string') apps.push([`app.${app.id}.${k}`, app[k]]);
}
console.log(JSON.stringify({ entries: mod.entries(), apps, locked: terms.LOCKED_TERMS,
  retired: terms.RETIRED_TERMS, renamed: terms.RENAMED_TERMS }));
"""


def read_table(strings=STRINGS):
    out = subprocess.run(["node", "--input-type=module", "-e", DUMP, str(strings)],
                         capture_output=True, text=True, timeout=120)
    if out.returncode:
        raise SystemExit(f"STRINGS FAIL — the table did not load:\n{out.stderr.strip()}")
    return json.loads(out.stdout)


def term_errors(where, text, locked, retired, renamed, researcher=False):
    """`researcher`: a string only Researcher mode shows (T-2668) may run a sentence past the
    visitor's 20 words (a full essay), and keeps every other rule: no id, path or ticket
    number reaches a researcher either (owner, 2026-10-18, T-2657)."""
    errs = []
    bare = re.sub(r"\{\w+\}", "x", text)
    # Machine lore stays in mono caps (section 03): a string set wholly in capitals, a
    # screen code such as "SCR 07 · CONFIDENCE VIEW", may carry a locked term in capitals.
    lore = bare == bare.upper()
    for term, _ in locked:
        for m in re.finditer(rf"(?<![\w-]){re.escape(term)}(?![\w-])", bare, re.IGNORECASE):
            got = m.group(0)
            if got == term or (lore and got == term.upper()):
                continue
            prose = got == term.lower() and " " not in term and term not in ("Attested", "Inferred", "Reconstructed")
            if not prose:
                errs.append(f"{where}: `{got}` is the locked term `{term}` spelled another way")
    for term in retired:
        flags = re.IGNORECASE if term.islower() else 0
        m = re.search(rf"\b{re.escape(term)}\b", bare, flags)
        if m:
            errs.append(f"{where}: `{m.group(0)}` is retired (section 03: Sources, Attested, Reconstructed)")
    for old, new in renamed:
        if re.search(rf"(?<![\w-]){re.escape(old)}(?![\w-])", bare):
            errs.append(f"{where}: `{old}` was renamed `{new}` (section 03)")
    for found in lint_string(bare):
        errs.append(f"{where}: {found} in a string a {'researcher' if researcher else 'visitor'} reads")
    if researcher:
        return errs
    for s in re.split(r"(?<=[.!?])\s+", bare):
        if len(words(s)) > MAX_SENTENCE_WORDS:
            errs.append(f"{where}: a sentence of {len(words(s))} words, over {MAX_SENTENCE_WORDS}")
    return errs


MARK = re.compile(r"<(?P<tag>[a-z][a-z0-9-]*)(?P<attrs>[^>]*\bdata-str(?:-title|-label)?=\"[^\"]+\"[^>]*)>", re.IGNORECASE)
ATTR = re.compile(r"([a-zA-Z-]+)=\"([^\"]*)\"")


def markup_errors(page, table):
    errs = []
    for m in MARK.finditer(page):
        attrs = dict(ATTR.findall(m.group("attrs")))
        for data, target in (("data-str", None), ("data-str-title", "title"), ("data-str-label", "aria-label")):
            key = attrs.get(data)
            if not key:
                continue
            if key not in table:
                errs.append(f"index.html: {data}=\"{key}\" names no string in the table")
                continue
            if target:
                got = html.unescape(attrs.get(target, ""))
            else:
                close = page.find(f"</{m.group('tag')}>", m.end())
                got = html.unescape(re.sub(r"<[^>]+>", "", page[m.end():close])).strip()
            if got != table[key]:
                errs.append(f"index.html: {key} paints {got!r} first and the table says {table[key]!r}")
    return errs


PAGES = [WEB / "index.html", WEB / "portal" / "index.html", WEB / "portal" / "pending.html"]
VISIBLE_ATTR = re.compile(r"\b(?:title|aria-label|placeholder|alt)=\"([^\"]*)\"")


def visible_text(page):
    """The words a visitor can read on a static page: text between tags and the title,
    aria-label, placeholder and alt attributes; scripts, styles and comments removed."""
    body = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>", " ", page, flags=re.S | re.I)
    out = [html.unescape(v) for v in VISIBLE_ATTR.findall(body)]
    out += [html.unescape(t).strip() for t in re.findall(r">([^<>]+)<", body)]
    return [t for t in out if t.strip()]


def page_errors(pages, retired, renamed):
    """Section 03's retired and renamed words, swept over the shipped static pages too,
    so a rename is applied where the visitor reads it and not only in the table."""
    errs = []
    for path in pages:
        if not path.is_file():
            continue
        for text in visible_text(path.read_text(encoding="utf-8")):
            for term in retired:
                if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE if term.islower() else 0):
                    errs.append(f"{path.name}: `{term}` is retired, in {text[:60]!r}")
            for old, new in renamed:
                if re.search(rf"(?<![\w-]){re.escape(old)}(?![\w-])", text):
                    errs.append(f"{path.name}: `{old}` was renamed `{new}`, in {text[:60]!r}")
    return errs


def guide_errors(locked, retired, root=ROOT):
    errs = []
    guide = Path(root) / "tools" / "check_guide.py"
    if guide.is_file():
        src = guide.read_text(encoding="utf-8")
        for name, ours in (("LOCKED", [t for t, _ in locked]), ("RETIRED", list(retired))):
            m = re.search(rf"^{name}\s*=\s*(\[[^\]]*\])", src, re.MULTILINE)
            if m and json.loads(m.group(1).replace("'", '"')) != ours:
                errs.append(f"terms: the table's {name.lower()} list differs from tools/check_guide.py {name}")
    gloss = Path(root) / "data" / "guide" / "glossary.json"
    if gloss.is_file():
        theirs = {t.get("term"): t.get("meaning") for t in json.loads(gloss.read_text(encoding="utf-8")).get("terms", [])}
        for term, meaning in locked:
            if term in theirs and theirs[term] != meaning:
                errs.append(f"terms: `{term}` means {meaning!r} here and {theirs[term]!r} in the Guide glossary")
    return errs


def gate(dump, page, root=ROOT, pages=None):
    locked, retired, renamed = dump["locked"], dump["retired"], dump["renamed"]
    table = dict(dump["entries"])
    errs = []
    if [t for t, _ in locked] != ["Attested", "Inferred", "Reconstructed", "Confidence view", "Liberties", "Sources", "Jaunts"]:
        errs.append("terms: the locked terms are not section 03's seven, in its order")
    for key, value in dump["entries"] + dump.get("apps", []):
        errs += term_errors(key, value, locked, retired, renamed, researcher="researcher" in key.split("."))
    errs += markup_errors(page, table)
    errs += guide_errors(locked, retired, root)
    if pages is None:
        errs += page_errors(PAGES, retired, renamed)
    else:
        errs += page_errors(pages, retired, renamed)
    return errs


def self_test():
    failures = []

    def expect(cond, what):
        print(f"   {'ok  ' if cond else 'FAIL'} {what}")
        if not cond:
            failures.append(what)

    base = read_table()
    page = INDEX.read_text(encoding="utf-8")
    clean = gate(base, page)
    expect(not clean, f"the committed table and page pass ({clean[:2]})")

    def plant(label, needle, value=None, markup=None):
        dump = json.loads(json.dumps(base))
        if value is not None:
            dump["entries"].append(["planted.string", value])
        errs = gate(dump, markup if markup is not None else page)
        expect(any(needle in e for e in errs), f"{label} is refused ({needle!r})")

    plant("a grade word in lower case", "spelled another way", "This roof is attested.")
    plant("a grade word in capitals inside a sentence", "spelled another way", "This roof is ATTESTED.")
    dump2 = json.loads(json.dumps(base)); dump2["apps"] = dump2.get("apps", []) + [["app.planted.label", "Confidence View"]]
    expect(any("spelled another way" in e for e in gate(dump2, page)), "an app manifest's misspelt label is refused")
    expect(not term_errors("ok", "SCR 07 · CONFIDENCE VIEW", base["locked"], base["retired"], base["renamed"]),
           "a screen code in mono caps passes")
    plant("Confidence View", "spelled another way", "Open the Confidence View.")
    plant("SOURCES in the table", "spelled another way", "Open SOURCES")
    plant("documented", "is retired", "A documented house.")
    plant("Evidence", "is retired", "Open Evidence")
    plant("Citations", "is retired", "Citations")
    plant("Coordinate", "was renamed `Destination`", "Pick a Coordinate")
    plant("Travel", "was renamed `Move`", "Travel")
    plant("Not recorded", "was renamed `Unknown`", "Not recorded.")
    plant("a snake_case id", "snake_case", "Inspect glessner_house")
    plant("a file path", "file path", "See data/scenes/1835.json")
    plant("a ticket number", "ticket number", "Fixed under T-2624")
    plant("a long sentence", "a sentence of 21 words", " ".join(["word"] * 21) + ".")
    dump3 = json.loads(json.dumps(base)); dump3["entries"].append(["researcher.planted", "See data/scenes/1835.json, attested."])
    errs3 = gate(dump3, page)
    expect(any("file path" in e for e in errs3) and any("spelled another way" in e for e in errs3),
           "a Researcher-mode string refuses a path (T-2657) and keeps the locked terms")
    for label, value, needle in [("a ticket number", "Fixed under T-2624.", "ticket number"),
                                 ("a snake_case id", "Inspect glessner_house.", "snake_case")]:
        d = json.loads(json.dumps(base)); d["entries"].append(["guide.researcher.planted", value])
        expect(any(needle in e for e in gate(d, page)), f"{label} in a Researcher-mode string is refused (owner, 2026-10-18)")
    d = json.loads(json.dumps(base)); d["entries"].append(["researcher.planted", " ".join(["word"] * 30) + "."])
    expect(not any("a sentence of" in e for e in gate(d, page)), "a Researcher-mode string may run past 20 words (a full essay)")
    plant("markup naming no string", "names no string", markup='<b data-str="hud.no-such">x</b>')
    first = next((k for k, v in base["entries"]), None)
    plant("markup whose first paint differs", "paints", markup=f'<b data-str="{first}">Something else</b>')
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "index.html"
        fake.write_text('<p>Pick a Coordinate</p><button title="Evidence">x</button><!-- Travel --><p>Fine</p>', encoding="utf-8")
        errs = page_errors([fake], base["retired"], base["renamed"])
        expect(any("`Coordinate` was renamed" in e for e in errs), "a renamed word left on a shipped page is refused")
        expect(any("`Evidence` is retired" in e for e in errs), "a retired word in a title attribute is refused")
        expect(not any("Travel" in e for e in errs), "a word inside a comment is not read as visible")
    expect(not term_errors("ok", "Reconstructed from the sources under Sources.", base["locked"], base["retired"], base["renamed"]),
           "plain prose 'the sources' beside the locked Sources passes")
    expect(not term_errors("ok", "Take a Jaunt to {place}.", base["locked"], base["retired"], base["renamed"]),
           "a placeholder and the singular Jaunt pass")
    print(f"   {len(failures)} planted fault(s) got through" if failures else "   every planted fault refused")
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    dump = read_table()
    errs = gate(dump, INDEX.read_text(encoding="utf-8"))
    ns = sorted({k.split(".")[0] for k, _ in dump["entries"]})
    print(f"  {len(dump['entries'])} strings in {len(ns)} sections ({', '.join(ns)}), "
          f"and {len(dump.get('apps', []))} from the Navigator apps' manifests")
    for e in errs:
        print(f"FAIL {e}")
    if errs:
        print(f"STRINGS FAIL — {len(errs)} problem(s)")
        return 1
    print("STRINGS PASS — locked terms exact, no retired or renamed word, no ids, the page paints the table")
    return 0


if __name__ == "__main__":
    sys.exit(main())
