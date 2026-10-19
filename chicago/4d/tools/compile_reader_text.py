#!/usr/bin/env python3
"""The reader's overlay for the records a page reads as authored (T-2825).

    python3 tools/compile_reader_text.py            write data/reader/*.json
    python3 tools/compile_reader_text.py --check    re-derive and compare, write nothing
    python3 tools/compile_reader_text.py --stats    what each family holds, and how much

THE OWNER, 2026-10-18: "You should rewrite the records so you are not referring to internal
ticket numbers or internal record ids in researcher or educator mode." The research records
the Sources hub compiles (liberties, ground, open questions, the reconstruction plan) are
rewritten at their compile step by tools/readable_text.py. These are the ones no compiler
stands between: the page fetches them as they are authored or compiled for the scene.

  flora        the plant communities (js/plants.js): data/flora/, and each scene's
               flora_sources.json and flora_clamp.json
  fauna        the wildlife communities (js/fauna.js): data/fauna/ and fauna_sources.json
  residents_index  the household browser's manifest, read as the section mounts
  residents    a person's card and a household's (js/people.js, js/residents.js), read when
               one opens: every household record and the joins the card reads (the research
               pilot, the facts withheld, the seating, the employment coverage, the
               directories, the 1835 address book and agencies, residents_sources.json)
  businesses   the Shops & work card (js/businesses.js): every firm's record, the index and
               the address book's seats
  structures_<scene>  a building's card (js/popup.js): every structure sidecar of the scene,
               its versions, and the agencies it can name

A record's prose is said for a reader by the one rule every research surface shares
(readable_text.rewrite: a ticket dropped or said as "earlier work", an id as the name the
data gives it, a file path as what the file is). The authored text stays as it is, because
it is the builders' working record and two dozen tools read it. What is written here is the
EDIT that turns each string a reader would be refused into the string they get, keyed by the
original's CRC-32 and UTF-8 length, so the page (js/reader-text.js) can apply it to the
record it fetched and the gate (tools/check_visitor_ui.py, the `records` surface) lints the
very same result through readable_text.reader_copy.

Each family file is
    {"_doc": ..., "family": "...", "count": N, "edits": {"<key>": [[start, delete, insert], …]},
     "work_refs": {"<key>": ["T-1460", …]}, "names": {"<id>": "<its name>", …}}
`work_refs` keeps the tickets a string named, beside the sentence and never in it: the one
shape Researcher mode may link from. `names` says the few record ids a card prints bare (see
NAMED_KEYS) by the name the data gives each.

A string the rewrite cannot clear is reported and fails the build: the overlay never
claims a clean sentence it does not have. `--check` re-derives every rewrite (the slow half
is the word diff, and an entry that still reproduces its rewrite is kept, not re-diffed).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import readable_text as rt  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "reader"
SCENES = ("1812", "1835", "1904")


def _sidecar_files(scene: str, names: tuple[str, ...]) -> list[Path]:
    return [p for n in names for p in [DATA / "sidecars" / scene / n] if p.is_file()]


def _structures(scene: str) -> list[Path]:
    """A scene's structure sidecars and their versions: a record with a phase and attributes."""
    out = []
    base = DATA / "sidecars" / scene
    for path in sorted(base.glob("*.json")) + sorted((base / "versions").rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(doc, dict) and "attributes" in doc and "phase" in doc:
            out.append(path)
    return out


def families() -> dict[str, list[Path]]:
    res = DATA / "residents"
    book = DATA / "reconstruction" / "1835_address_book.json"
    agencies = DATA / "reconstruction" / "1835_agencies.json"
    fam = {
        "flora": [DATA / "flora" / "index.json", *sorted((DATA / "flora" / "zones").glob("*.json"))]
                 + [p for s in SCENES for p in _sidecar_files(s, ("flora_sources.json", "flora_clamp.json"))],
        "fauna": [DATA / "fauna" / "index.json", *sorted((DATA / "fauna" / "zones").glob("*.json"))]
                 + [p for s in SCENES for p in _sidecar_files(s, ("fauna_sources.json",))],
        # The manifest is read when the section mounts; everything else when a card opens,
        # so the two are two files and the household one never rides the first visit.
        "residents_index": [res / "index.json"],
        "residents": [*sorted((res / "households").glob("*.json"))]
                     + [res / n for n in ("research_pilot.json", "person_facts_withheld.json",
                                          "reconstructed_seating.json", "employment_coverage.json",
                                          "directories.json")]
                     + [book, agencies]
                     + [p for s in SCENES for p in _sidecar_files(s, ("residents_sources.json",))],
        "businesses": [DATA / "businesses" / "index.json", *sorted((DATA / "businesses").glob("biz_*.json")),
                       *sorted((DATA / "businesses" / "authored").glob("biz_*.json")), book],
    }
    for scene in SCENES:
        fam[f"structures_{scene}"] = _structures(scene) + [agencies]
    return {k: [p for p in v if p.is_file()] for k, v in fam.items()}


DOC = ("The reader's overlay for {what} (T-2825): the edits that say each of its research "
       "strings without a ticket number, a record id or a file path, keyed by the original "
       "string's CRC-32 and UTF-8 length. Applied by js/reader-text.js as the page renders and "
       "by tools/readable_text.py reader_copy() in the gate. Derived by "
       "tools/compile_reader_text.py; never hand-written.")
WHAT = {
    "flora": "the plant communities",
    "fauna": "the wildlife communities",
    "residents_index": "the household browser's manifest",
    "residents": "the household records and a person's card",
    "businesses": "the Shops & work card",
}


# The few record ids a card prints bare, by the key that holds them: the household a person
# was dealt in, and the notice or book a firm was read from. js/reader-text.js `nameOf`
# says each by the name written here.
NAMED_KEYS = {
    "residents": ("from_household",),
    "businesses": ("claim_ids",),
}


def claim_sources() -> dict[str, str]:
    """A claim read out of a book (`bk_fer_052`) is that book: its register names the source."""
    out = {}
    for path in sorted((DATA / "research").glob("*/claims/*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not isinstance(doc, dict) or not doc.get("source_id"):
            continue
        for c in doc.get("claims") or []:
            if isinstance(c, dict) and c.get("id"):
                out[c["id"]] = doc["source_id"]
    return out


def tokens_of(paths: list[Path], keys: tuple[str, ...]) -> list[str]:
    seen, out = set(), []

    def walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, key)
        elif key in keys and isinstance(node, str) and node and not rt.is_prose(node) and node not in seen:
            seen.add(node)
            out.append(node)
    for path in paths:
        walk(json.loads(path.read_text(encoding="utf-8")))
    return out


def strings_of(paths: list[Path]) -> list[str]:
    seen, out = set(), []
    for path in paths:
        for s in rt.prose_strings(json.loads(path.read_text(encoding="utf-8"))):
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


def liberty_titles() -> dict[str, str]:
    """A liberty named in a record is named by its title, as the register shows it."""
    path = DATA / "liberties.json"
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {e["id"]: e["title"] for e in doc.get("liberties") or [] if e.get("id") and e.get("title")}


def build_family(name: str, paths: list[Path], names: rt.Names, old: dict | None,
                 libs: dict | None = None):
    edits, refs, unclear = {}, {}, []
    prior = (old or {}).get("edits") or {}
    for s in strings_of(paths):
        if not rt.problems(s):
            continue
        new, tickets = rt.rewrite(s, names, liberties=libs)
        left = rt.problems(new)
        if left:
            unclear.append(f"{name}: {left[0]} — in {new[:120]!r}")
        key = rt.reader_key(s)
        if key in edits:
            if rt.apply_edits(s, edits[key]) != new:
                unclear.append(f"{name}: two strings share the key {key}")
            continue
        e = prior.get(key)
        if e is None or rt.apply_edits(s, e) != new:
            e = rt.edits_between(s, new)
        if rt.apply_edits(s, e) != new:
            unclear.append(f"{name}: the edits for {key} do not reproduce the rewrite")
        edits[key] = e
        if tickets:
            refs[key] = tickets
    named = {}
    claims = claim_sources() if NAMED_KEYS.get(name) else {}
    for tok in tokens_of(paths, NAMED_KEYS.get(name, ())):
        said, _ = rt.rewrite(tok, names, liberties=libs)
        if tok in claims and names.get(claims[tok]):
            said = names.get(claims[tok])
        if said != tok:
            named[tok] = said
            left = rt.problems(said)
            if left:
                unclear.append(f"{name}: the name for {tok!r} still carries {left[0]}")
    what = WHAT.get(name) or f"a building's card in the {name.split('_')[-1]} scene"
    doc = {"_doc": DOC.format(what=what), "family": name, "count": len(edits),
           "edits": dict(sorted(edits.items())), "work_refs": dict(sorted(refs.items()))}
    if named:
        doc["names"] = dict(sorted(named.items()))
    return doc, unclear


def text_of(doc) -> str:
    # Compact, like people.json: a directory the browser looks up, not a file a person reads.
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="re-derive and compare, write nothing")
    ap.add_argument("--stats", action="store_true", help="print each family's size")
    a = ap.parse_args(argv)
    names = rt.Names(ROOT)
    libs = liberty_titles()
    bad, stale = [], []
    fams = families()
    for name, paths in fams.items():
        out = OUT / f"{name}.json"
        old = None
        if out.is_file():
            try:
                old = json.loads(out.read_text(encoding="utf-8"))
            except ValueError:
                old = None
        doc, unclear = build_family(name, paths, names, old, libs)
        bad += unclear
        text = text_of(doc)
        if a.stats:
            print(f"   {name}: {len(paths)} files, {doc['count']} strings rewritten, "
                  f"{len(text.encode()) // 1024} KiB")
        if a.check:
            if not out.is_file() or out.read_text(encoding="utf-8") != text:
                stale.append(f"data/reader/{name}.json")
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            if not out.is_file() or out.read_text(encoding="utf-8") != text:
                out.write_text(text, encoding="utf-8")
    known = {f"{n}.json" for n in fams}
    extra = sorted(p.name for p in OUT.glob("*.json") if p.name not in known) if OUT.is_dir() else []
    for e in extra:
        if a.check:
            stale.append(f"data/reader/{e} is not a family this compiler writes")
        else:
            (OUT / e).unlink()
    for b in bad:
        print(f"   FAIL {b}")
    for s in stale:
        print(f"   FAIL {s} is not what the records compile to — run tools/compile_reader_text.py")
    if bad or stale:
        return 1
    print(f"OK: the reader's overlay covers {len(fams)} families, every string a reader opens "
          f"is said without a ticket, a record id or a file path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
