#!/usr/bin/env python3
"""THE OCR'S TURKISH ALPHABET, REPAIRED IN THE READING AND REFUSED THEREAFTER (T-0901).

Seven readings in this corpus carry a letter no compositor in 1835 Chicago had in his
case, because they were not set by a compositor at all: they are the signature of an OCR
run whose language model was Turkish, and they are the four letters Turkish has and the
Latin alphabet this project transcribes does not —

    ı  U+0131  LATIN SMALL LETTER DOTLESS I
    İ  U+0130  LATIN CAPITAL LETTER I WITH DOT ABOVE
    Ğ  U+011E  LATIN CAPITAL LETTER G WITH BREVE
    ğ  U+011F  LATIN SMALL LETTER G WITH BREVE

THE RULE IS A READING AND NOT A CONVENIENCE, AND THE CORPUS DEMONSTRATES IT THREE WAYS.
Each of the four maps back to its ASCII base, and where the result can be checked it is a
name the corpus already documents:

  * `JOHN H. KİNZIE.` — the Democrat of 6 August 1834 — becomes `JOHN H. KINZIE.`, the
    name every other impression in the corpus sets, and the best-attested name in it.
  * `JOHN WRIĞHT` — 26 November 1833 — becomes `JOHN WRIGHT`. The transcriber's own note
    on that claim already says so: "'WRIĞHT' carries a spurious breve, which is a
    recognition artefact and not an 1830s orthography."
  * `Benjamın Swena` and `Benjamin Swena` were RULED one entry by T-0299, aligned BY
    POSITION across the three printings of the 1 July 1834 letter list and declared in
    `data/research/newspapers/identity.json` — the strictest identity method this project
    has, and it was spent on a difference of one dot. `tools/compile_gazetteer.py`'s own
    T-0299 self-test asserts that the two parse as one name.

So the substitution is not inferred from resemblance: three of the seven readings become
names the corpus holds independently the moment the Turkish letter goes back to its base.

WHAT IS REPAIRED, AND WHAT IS NOT. The `quote` on a newspaper claim is the transcription
character for character — `compile_gazetteer.py --check` proves it against the deposit,
brackets, artefacts and all — so a quote KEEPS the letter: the artefact is the evidence
that the artefact is there. A claim's `notes` keeps it too, because those notes QUOTE the
artefact to explain a correction ('Rayınand'→'Ra[y]m[o]nd'), and repairing the before-side
of a worked example falsifies it. Every other string in `data/` carries a READING, and a
reading is repaired.

WHAT IT DOES NOT DO. It does not invent a name. `Willınm Bandle` becomes `Willinm Bandle`
and stops there: `Willinm` is what this page's OCR makes of `William` all down the column
(`Sprague, Willinm B.`, `Willinm G.`), but that is an argument about a word and not about a
character, and this pass rules on characters only. The forename stays refused against
Fergus 1843's `Willis` — two full forenames that differ — and it is now refused on a name
a hand could have written, which is the whole of T-0901's complaint.

AND NOTHING ELSE FROM THAT ALPHABET IS GUESSED. `ş`/`Ş` have no unambiguous base — the
cedilla is a letter in Turkish and a diacritic in French, and this corpus prints French
names — so the check REFUSES one rather than mapping it, and the refusal asks for a ruling.

    python3 tools/repair_ocr_turkish_alphabet.py --check      # no reading carries one
    python3 tools/repair_ocr_turkish_alphabet.py --repair     # write the repairs
    python3 tools/repair_ocr_turkish_alphabet.py --self-test  # the assertions still fire
"""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# The four whose base letter is not in doubt.
REPAIRS = {"\u0131": "i", "\u0130": "I", "\u011e": "G", "\u011f": "g"}
# The two the pass refuses to decide, so a new one is a question and not a silent map.
UNRULED = {"\u015e", "\u015f"}

# A reading is repaired; these two keys are not readings.
VERBATIM_KEYS = ("quote", "notes")

# The raw OCR store is a scanned artefact and not a reading of one.
SKIP_DIRS = ("newberry_index/text",)


def _string_at(text: str, i: int) -> int:
    """Index just past the JSON string whose opening quote is at `i`."""
    j = i + 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == '"':
            return j + 1
        j += 1
    return len(text)


def verbatim_spans(text: str) -> list[tuple[int, int]]:
    """The (start, end) of every VERBATIM_KEYS value in a JSON document's raw text.

    Raw text and not a parse, because these files are hand-formatted — three-space
    indents, two-space indents, arrays both ways — and a repair of four characters
    has no business reflowing a file it is not otherwise changing.
    """
    spans = []
    for key in VERBATIM_KEYS:
        needle = '"%s"' % key
        at = text.find(needle)
        while at != -1:
            k = at + len(needle)
            while k < len(text) and text[k] in " \t\r\n":
                k += 1
            if k < len(text) and text[k] == ":":
                k += 1
                while k < len(text) and text[k] in " \t\r\n":
                    k += 1
                if k < len(text) and text[k] == '"':
                    spans.append((k, _string_at(text, k)))
            at = text.find(needle, at + 1)
    return sorted(spans)


def repair_text(text: str) -> tuple[str, int, list[str]]:
    """Return (repaired, count, unruled) over everything outside a verbatim span."""
    spans = verbatim_spans(text)
    out, count, unruled = [], 0, []
    pos = 0
    for start, end in spans:
        chunk, n, u = _repair_chunk(text[pos:start])
        out.append(chunk)
        count += n
        unruled += u
        out.append(text[start:end])
        pos = end
    chunk, n, u = _repair_chunk(text[pos:])
    out.append(chunk)
    return "".join(out), count + n, unruled + u


def _repair_chunk(chunk: str) -> tuple[str, int, list[str]]:
    count = sum(chunk.count(ch) for ch in REPAIRS)
    unruled = sorted({ch for ch in UNRULED if ch in chunk})
    for ch, base in REPAIRS.items():
        chunk = chunk.replace(ch, base)
    return chunk, count, unruled


def files() -> list[pathlib.Path]:
    return sorted(p for p in DATA.rglob("*.json")
                  if not any(d in p.as_posix() for d in SKIP_DIRS))


def run(write: bool) -> int:
    touched, total, refusals = [], 0, []
    for path in files():
        text = path.read_text(encoding="utf-8")
        fixed, n, unruled = repair_text(text)
        for ch in unruled:
            refusals.append("%s: carries %r, which this pass refuses to map — the cedilla "
                            "is a letter in Turkish and a diacritic in French, and this "
                            "corpus prints French names. Rule it before repairing it."
                            % (path.relative_to(ROOT), ch))
        if n:
            total += n
            touched.append((path.relative_to(ROOT), n))
            if write:
                path.write_text(fixed, encoding="utf-8")
    for r in refusals:
        print("REFUSED  " + r)
    if write:
        for rel, n in touched:
            print("repaired %3d  %s" % (n, rel))
        print("%d letters repaired in %d files" % (total, len(touched)))
        return 1 if refusals else 0
    if touched:
        print("FAIL: %d reading(s) in %d file(s) still carry a letter of the OCR's Turkish "
              "alphabet (T-0901). Run --repair." % (total, len(touched)))
        for rel, n in touched:
            print("   %3d  %s" % (n, rel))
    return 1 if (touched or refusals) else 0


def self_test() -> int:
    failures = []

    def case(label, got, want):
        if got != want:
            failures.append("%s: got %r, wanted %r" % (label, got, want))

    # The four map to their base, and the demonstrated three land on documented names.
    case("dotless i", repair_text('{"name": "Benjam\u0131n Swena"}')[0],
         '{"name": "Benjamin Swena"}')
    case("dotted I", repair_text('{"as_printed": "JOHN H. K\u0130NZIE."}')[0],
         '{"as_printed": "JOHN H. KINZIE."}')
    case("breve G", repair_text('{"as_printed": "JOHN WRI\u011eHT"}')[0],
         '{"as_printed": "JOHN WRIGHT"}')
    case("breve g", repair_text('{"name": "a\u011fb"}')[0], '{"name": "agb"}')

    # A quote keeps the artefact — that is what a quote is for.
    q = '{"quote": "Bandle, Will\u0131nm", "as_printed": "Bandle, Will\u0131nm"}'
    case("the quote is verbatim", repair_text(q)[0],
         '{"quote": "Bandle, Will\u0131nm", "as_printed": "Bandle, Willinm"}')
    # …including when it carries an escaped quotation mark before the reading.
    q2 = '{"quote": "he said \\"Will\u0131nm\\" twice", "name": "Will\u0131nm"}'
    case("an escape inside a quote", repair_text(q2)[0],
         '{"quote": "he said \\"Will\u0131nm\\" twice", "name": "Willinm"}')
    # …and so does a claim's notes, which quotes the artefact to explain a correction.
    n = '{"notes": "\'Ray\u0131nand\'\u2192\'Ra[y]m[o]nd\'", "name": "Ray\u0131nand"}'
    case("the notes keep the worked example", repair_text(n)[0],
         '{"notes": "\'Ray\u0131nand\'\u2192\'Ra[y]m[o]nd\'", "name": "Rayinand"}')

    # The pass rules on characters, never on words: no name is invented.
    case("no name is invented", repair_text('{"name": "Will\u0131nm Bandle"}')[0],
         '{"name": "Willinm Bandle"}')

    # The cedilla is refused rather than mapped.
    _, _, unruled = repair_text('{"name": "Ni\u015fan"}')
    case("the cedilla is refused", unruled, ["\u015f"])

    # The counter counts what it repaired, outside the verbatim spans only.
    case("the count skips the quote", repair_text(q)[1], 1)

    for f in failures:
        print("FAIL  " + f)
    print("self-test: %d case(s), %d failure(s)" % (10, len(failures)))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.repair:
        return run(write=True)
    return run(write=False)


if __name__ == "__main__":
    sys.exit(main())
