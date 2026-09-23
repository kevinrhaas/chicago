#!/usr/bin/env python3
"""One-shot: documented/derived/inferred -> attested/inferred/reconstructed.

Kept in the tree because it is the only safe way to run this rename and the
reasons are not obvious.

TWO HAZARDS, both of which have already bitten this project once:

1. **The mapping collides head-on.** derived -> inferred and inferred ->
   reconstructed. A sequential search-and-replace does derived -> inferred and
   then immediately rewrites those same values to reconstructed, silently
   demoting every middle-tier claim in the dataset by one level. Every value
   must therefore move through a sentinel, or be mapped in a single pass. This
   does the latter.

2. **`inferred` is TWO different vocabularies in this repo.** It is a confidence
   level, and it is also the value of `kind` on a programme building — the
   recipe's own documented|inferred axis for "did the sources describe this
   building". A blanket text pass rewrites both, which turns every invented
   building into a documented one and tells the visitor that a cooperage nobody
   recorded is attested. So this NEVER touches text: it parses the JSON and
   rewrites only the values of keys named `confidence` or `grade`, leaving
   `kind`, prose notes and everything else exactly as they were.

Notes are prose and are left alone deliberately. A note that says "derived from
the lot line" is still true and still English; rewriting prose mechanically is
how you get sentences nobody wrote.
"""
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP = {"documented": "attested", "derived": "inferred", "inferred": "reconstructed"}

# ONLY the key/value pair, never a bare word. `"confidence": "inferred"` moves;
# `"kind": "inferred"` and the word "inferred" inside a note do not. Rewriting
# the pair rather than reserialising the document also means not one byte of
# formatting changes in 700 committed files, so the diff is the rename and
# nothing else.
#
# `[a-z_]*_confidence` matters as much as the bare key: `geometry_confidence`,
# `surface_confidence`, `wear_confidence`, `width_confidence`, `carried_confidence`
# and `bed_confidence` all hold the same vocabulary, and a first pass that missed
# them left ~2,400 values behind in the old words.
PAIR = re.compile(
    r'("(?:[a-z_]*_)?(?:confidence|grade)"\s*:\s*")(documented|derived|inferred)(")')

# The schema's own list of legal values.
ENUM = re.compile(r'"enum"\s*:\s*\[\s*"documented"\s*,\s*"derived"\s*,\s*"inferred"\s*\]')

# `building_prose` in the reconstruction programme stores a level POSITIONALLY:
# ["documented", ["andreas_1884_v1"], "…note…"]. No key names it, so no key-based
# pass can see it, and it drives the grade of every documented building the
# household programme writes.
POSITIONAL = ("building_prose", ("existence", "position", "occupants"))


def main():
    stats = Counter()
    changed = 0

    # REFUSE TO RUN TWICE. Every value moves one step, and two of the steps
    # collide: derived -> inferred and inferred -> reconstructed. Applied twice,
    # everything that was `derived` — the middle tier, "reasoned from evidence
    # about this thing" — lands on `reconstructed`, the bottom one, and the whole
    # dataset quietly claims to be invented. That is not hypothetical: it happened
    # here, and it took a diff on one structure record to notice.
    for p in sorted((ROOT / "data").rglob("*.json")):
        if re.search(r'"(?:[a-z_]*_)?(?:confidence|grade)"\s*:\s*"(?:attested|reconstructed)"',
                     p.read_text()):
            print(f"   REFUSED: {p.relative_to(ROOT)} already carries the NEW vocabulary.")
            print("   This rename is not idempotent — running it twice demotes every "
                  "middle-tier value to the bottom tier. Reset the tree first.")
            return 2

    targets = []
    for sub in ("data",):
        d = ROOT / sub
        for ext in ("*.json", "*.geojson"):
            targets += sorted(d.rglob(ext))

    for p in targets:
        text = p.read_text()
        new = text

        def sub(m):
            stats[f"{m.group(2)} -> {MAP[m.group(2)]}"] += 1
            return m.group(1) + MAP[m.group(2)] + m.group(3)

        new = PAIR.sub(sub, new)
        if ENUM.search(new):
            new = ENUM.sub('"enum": ["attested", "inferred", "reconstructed"]', new)
            stats["schema enum"] += 1

        if new != text:
            before, after = json.loads(text), json.loads(new)
            if strip_grades(before) != strip_grades(after):
                print(f"   REFUSED (changed more than grades): {p.relative_to(ROOT)}")
                return 1
            p.write_text(new)
            changed += 1

    # The positional levels, handled structurally because no regex can see them.
    for p in sorted((ROOT / "data").rglob("*.json")):
        doc = json.loads(p.read_text())
        key, fields = POSITIONAL
        block = doc.get(key) if isinstance(doc, dict) else None
        if not isinstance(block, dict):
            continue
        moved = 0
        for _bid, entry in block.items():
            for f in fields:
                v = entry.get(f) if isinstance(entry, dict) else None
                if isinstance(v, list) and v and isinstance(v[0], str) and v[0] in MAP:
                    stats[f"{v[0]} -> {MAP[v[0]]} (positional)"] += 1
                    v[0] = MAP[v[0]]
                    moved += 1
        if moved:
            p.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
            changed += 1

    print(f"   {changed} file(s) rewritten")
    for k, v in sorted(stats.items()):
        print(f"   {v:6d}  {k}")
    return 0


GRADED_KEY = re.compile(r"^(?:[a-z_]*_)?(?:confidence|grade)$")


def strip_grades(node):
    """The document with every graded value blanked — must be identical before
    and after, or the regex reached something it had no business in.

    The key test has to match PAIR exactly. When it was narrower (bare
    `confidence` and `grade` only) this check fired on `lake_stage_confidence`
    and refused a rename that was entirely correct.
    """
    if isinstance(node, dict):
        return {k: (None if GRADED_KEY.match(k) else strip_grades(v))
                for k, v in node.items()}
    if isinstance(node, list):
        return [strip_grades(v) for v in node]
    return node


if __name__ == "__main__":
    sys.exit(main())
