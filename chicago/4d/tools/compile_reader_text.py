#!/usr/bin/env python3
"""The reader's overlay for the records a page reads as authored (T-2825).

    python3 tools/compile_reader_text.py            write data/reader/*.json (publish.sh runs this)
    python3 tools/compile_reader_text.py --out DIR  write them to DIR instead (the JS test does)
    python3 tools/compile_reader_text.py --check    derive them in memory, write nothing
    python3 tools/compile_reader_text.py --stats    what each family holds, and how much
    python3 tools/compile_reader_text.py --list     each family's files, as JSON (the JS test reads it)

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
               directories, the 1835 address book and agencies, residents_sources.json, and
               the directory rows of people.json a card prints)
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
claims a clean sentence it does not have.

DERIVED AT PUBLISH, NEVER COMMITTED (data/reader/ is ignored), like the Inspect summaries:
the overlay follows the records as they stand, so a change to one household note never has
to re-commit a megabyte of edits beside it. The gate reads the same records through the same
rewrite (check_visitor_ui.py), and test_reader_text.mjs compiles the overlay to a scratch
folder and holds the page's JavaScript to it. An overlay already on disk is a cache: an entry
that still reproduces its string's rewrite is kept rather than diffed again.
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
                     + [p for s in SCENES for p in _sidecar_files(s, ("residents_sources.json", "people.json"))],
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
    "residents": ("from_household", "wife", "sources"),
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


class Reader:
    """The one rewrite, with what it names things by, said once per distinct string. The
    compiler writes its edits; the gate (check_visitor_ui.py) reads the records through it."""

    def __init__(self, root: Path = ROOT):
        self.names = rt.Names(root)
        self.libs = liberty_titles()
        self.claims = claim_sources()
        self.memo: dict[str, tuple[str, list[str]]] = {}

    def say(self, text: str) -> tuple[str, list[str]]:
        """(the string as a reader gets it, the tickets it named) — unchanged when clean."""
        hit = self.memo.get(text)
        if hit is None:
            hit = rt.rewrite(text, self.names, liberties=self.libs) if rt.problems(text) else (text, [])
            self.memo[text] = hit
        return hit

    def copy(self, doc):
        """`doc` as the page renders it once its overlay is applied (js/reader-text.js)."""
        if isinstance(doc, dict):
            return {k: self.copy(v) for k, v in doc.items()}
        if isinstance(doc, list):
            return [self.copy(v) for v in doc]
        return self.say(doc)[0] if rt.is_prose(doc) else doc

    def names_for(self, family: str, paths: list[Path]) -> dict[str, str]:
        """The bare ids of a family a card prints (NAMED_KEYS), each by the name it is said by."""
        out = {}
        for tok in tokens_of(paths, NAMED_KEYS.get(family, ())):
            said, _ = rt.rewrite(tok, self.names, liberties=self.libs)
            if tok in self.claims and self.names.get(self.claims[tok]):
                said = self.names.get(self.claims[tok])
            if said != tok:
                out[tok] = said
        return out


def build_family(name: str, paths: list[Path], reader: Reader, old: dict | None):
    edits, refs, unclear = {}, {}, []
    prior = (old or {}).get("edits") or {}
    for s in strings_of(paths):
        if not rt.problems(s):
            continue
        new, tickets = reader.say(s)
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
    named = reader.names_for(name, paths)
    for tok, said in named.items():
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
    ap.add_argument("--check", action="store_true", help="derive in memory, write nothing")
    ap.add_argument("--out", type=Path, default=None, help="write the overlay here, not data/reader/")
    ap.add_argument("--stats", action="store_true", help="print each family's size")
    ap.add_argument("--list", action="store_true", help="print each family's files as JSON")
    ap.add_argument("--family", action="append", default=None,
                    help="only this family (repeatable); the overlay of the others is left as it is")
    a = ap.parse_args(argv)
    if a.list:
        print(json.dumps({k: [str(p.relative_to(ROOT)) for p in v] for k, v in families().items()}))
        return 0
    reader = Reader(ROOT)
    bad = []
    fams = families()
    if a.family:
        unknown = [f for f in a.family if f not in fams]
        if unknown:
            print(f"   FAIL no such family: {', '.join(unknown)} (there are {', '.join(fams)})")
            return 1
        fams = {k: v for k, v in fams.items() if k in a.family}
    outdir = a.out or OUT
    for name, paths in fams.items():
        out = outdir / f"{name}.json"
        old = None
        if out.is_file():
            try:
                old = json.loads(out.read_text(encoding="utf-8"))
            except ValueError:
                old = None
        doc, unclear = build_family(name, paths, reader, old)
        bad += unclear
        text = text_of(doc)
        if a.stats:
            print(f"   {name}: {len(paths)} files, {doc['count']} strings rewritten, "
                  f"{len(text.encode()) // 1024} KiB")
        if not a.check:
            outdir.mkdir(parents=True, exist_ok=True)
            if not out.is_file() or out.read_text(encoding="utf-8") != text:
                out.write_text(text, encoding="utf-8")
    if not a.check and not a.family and outdir.is_dir():
        known = {f"{n}.json" for n in fams}
        for p in outdir.glob("*.json"):
            if p.name not in known:
                p.unlink()
    for b in bad:
        print(f"   FAIL {b}")
    if bad:
        return 1
    print(f"OK: the reader's overlay covers {len(fams)} families, every string a reader opens "
          f"is said without a ticket, a record id or a file path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
