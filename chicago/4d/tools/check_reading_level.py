#!/usr/bin/env python3
"""Hold every sentence a visitor is told to an 8th-grade reading level (T-2669).

    python3 tools/check_reading_level.py --check       score every summary, fact, caption and bubble
    python3 tools/check_reading_level.py --print       ...and print each string's score
    python3 tools/check_reading_level.py --self-test   plant each fault and require the gate to refuse it

Design doc "Field Navigator Mk II", section 03 "Voice rules": "Target an 8th-grade reading
level. CI checks it (Flesch-Kincaid <= 9). Keep sentences to 20 words or fewer." The doc is
written for students aged 14 to 16, mostly on phones. This is that check.

WHAT IT READS. Every string a visitor reads, from each source of authored copy that exists:

  - summary   data/summaries/<id>.json: the record's `summary` (T-2635);
  - fact      every other visitor-facing string in a summary record (key facts, residents,
              Look-for lines, notable facts, story entries) -- the strings T-2635's own lint
              walks, from tools/compile_summaries.py `visitor_strings`, so the two gates
              read the same strings and cannot drift apart;
  - caption   data/timestream/<scene>.json: each caption's `text` (T-2611);
  - guide     data/guide/*.json: a glossary `meaning`, an FAQ `q` and `a`, a card's `title`
              and `body` (T-2662, T-2667), a {figure} scored as the numeral it becomes;
  - bubble    data/tour/*.json: every string under a key named `bubble` (the Field Check
              tour, T-2663, which has not landed; until it does this source reads nothing,
              and the self-test proves the reader with a planted file). Section 11 also
              caps a bubble at 14 words, and that is held here too.

A source with no files is not an error: it is copy nobody has written yet. The count of
strings read from each is printed, so an empty source reads as empty, not as passed.

WHAT IT REFUSES.

  1. A sentence over 20 words (section 03), in any string. Words and sentence ends are
     T-2635's: a word is a whitespace token holding a letter or digit, and a full stop
     after an initial or a common abbreviation ("H. H. Richardson", "S. Prairie Ave.")
     does not end a sentence. `split_sentences` below splits on exactly the boundaries
     compile_summaries.sentences() counts, and the self-test holds the two to one answer.
  2. A Flesch-Kincaid grade over 9, for every string of at least MIN_FK_WORDS (12) words:
         grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
     The formula is a passage measure and is unstable on short strings: a single word
     "Reconstructed" scores 32, and on the 30 committed time-stream captions (T-2611) the
     ones of 8 to 11 words read from 1.7 to 10.7 on little more than whether a word like
     "Chicago" or "president" is in them -- "Lincoln is nominated for president where the
     Sauganash Hotel stood." reads 10.7 -- while every caption of 12 words or more reads
     5.8 or lower (measured 2026-10-17; the three decks pool at 4.8 to 5.6). So a string
     shorter than 12 words is not scored ALONE. It is not let off:
     every source file's strings are also pooled (all words over all sentences, as a page
     of them reads) and the pool is held to the same 9, so a file of short, hard lines is
     still caught, and every sentence of every string is still held to 20 words.
  3. A bubble over 14 words (section 11).

HOW SYLLABLES ARE COUNTED (no dictionary, no dependency). A word is lower-cased and cut
to its letters. Then:
  - each run of vowels (a e i o u, and y after a consonant) is one syllable;
  - a final silent "e" takes one away ("house", "stone"), except "-le" after a consonant
    ("table") and words of one vowel group ("the", "be");
  - a final "-es" or "-ed" takes one away unless the stem ends in a sound that keeps it
    ("-ces", "-ges", "-ses", "-zes", "-xes", "-shes", "-ches"; "-ted", "-ded");
  - a few vowel pairs said as two add one: "ia" or "io" not after c, g, s or t and not
    before n ("piano", "radio", but not "nation", "special" or "Christian"), "ua", "uo",
    and a final "-eum" ("museum");
  - every word has at least one.
A numeral ("1966", "$35,000", "18th") counts one word of one syllable: years and prices
are read at a glance, and spelling them out would score a date as hard prose. The
heuristic reads within about one syllable of a dictionary on ordinary English; the
self-test pins it on words with known counts, so a change to it shows up as a change.

Writes nothing; prints only.
"""

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compile_summaries as cs  # noqa: E402  T-2635's words, sentence ends and visitor strings

ROOT = Path(__file__).resolve().parent.parent

MAX_GRADE = 9.0           # section 03
MAX_SENTENCE_WORDS = 20   # section 03
MAX_BUBBLE_WORDS = 14     # section 11
MIN_FK_WORDS = 12         # below this a string is scored only in its file's pool

VOWELS = set("aeiouy")


# ------------------------------------------------------------------ the arithmetic

def split_sentences(text):
    """The sentences of `text`, on exactly the boundaries cs.sentences() counts."""
    toks = text.split()
    out, cur = [], []
    for i, tok in enumerate(toks):
        cur.append(tok)
        bare = tok.rstrip("\"'”’)]")
        if not bare or bare[-1] not in ".!?":
            continue
        last = i == len(toks) - 1
        if not last and not re.match(r"[\"'“‘(\[]?[A-Z0-9]", toks[i + 1]):
            continue
        if bare.endswith(".") and not bare.endswith(".."):
            stem = bare.rstrip(".").lstrip("\"'“‘([").lower()
            if (len(stem) == 1 and stem.isalpha()) or stem in cs.ABBREVIATIONS:
                if not last:
                    continue
        out.append(" ".join(cur))
        cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def syllables(token):
    """Syllables in one word, by the rules in the header."""
    if re.search(r"\d", token):
        return 1
    w = re.sub(r"[^a-z]", "", token.lower())
    if not w:
        return 0
    groups = 0
    prev_vowel = False
    for i, ch in enumerate(w):
        vowel = ch in "aeiou" or (ch == "y" and i > 0 and w[i - 1] not in "aeiou")
        if vowel and not prev_vowel:
            groups += 1
        prev_vowel = vowel
    n = groups
    if n > 1:
        if w.endswith("e") and not w.endswith(("le", "ee", "ye")):
            n -= 1
        elif w.endswith("le") and len(w) > 2 and w[-3] in "aeiouy":
            n -= 1
        elif w.endswith("es") and not re.search(r"(?:[cgsxz]|sh|ch)es$", w):
            n -= 1
        elif w.endswith("ed") and not re.search(r"[td]ed$", w):
            n -= 1
    n += len(re.findall(r"(?<![aeioucgst])i[ao](?!n)|ua|uo", w)) + (1 if w.endswith("eum") else 0)
    return max(1, n)


def score(text):
    """{words, sentences, syllables, grade, longest} for a string."""
    ws = cs.words(text)
    sents = split_sentences(text)
    n_s = max(1, len(sents))
    syl = sum(syllables(w) for w in ws)
    n_w = len(ws)
    grade = 0.39 * (n_w / n_s) + 11.8 * (syl / n_w) - 15.59 if n_w else 0.0
    longest = max((len(cs.words(s)) for s in sents), default=0)
    return {"words": n_w, "sentences": n_s, "syllables": syl, "grade": grade, "longest": longest}


def pooled(scores):
    w = sum(s["words"] for s in scores)
    n = sum(s["sentences"] for s in scores)
    syl = sum(s["syllables"] for s in scores)
    return 0.39 * (w / n) + 11.8 * (syl / w) - 15.59 if w and n else 0.0


# ------------------------------------------------------------------ the sources

def summary_strings(root):
    for p in sorted((Path(root) / "data" / "summaries").glob("*.json")):
        rec = cs.load_json(p)
        for where, text in cs.visitor_strings(rec, ""):
            yield p, ("summary" if where == "summary" else "fact"), where, text


def caption_strings(root):
    for p in sorted((Path(root) / "data" / "timestream").glob("*.json")):
        deck = cs.load_json(p)
        for i, c in enumerate(deck.get("captions") or []):
            if isinstance(c, dict) and isinstance(c.get("text"), str):
                yield p, "caption", f"captions[{i}].text", c["text"]


def bubble_strings(root):
    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                at = f"{where}.{k}" if where else k
                if k == "bubble" and isinstance(v, str):
                    yield at, v
                else:
                    yield from walk(v, at)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{where}[{i}]")
    for p in sorted((Path(root) / "data" / "tour").glob("*.json")):
        for where, text in walk(cs.load_json(p), ""):
            yield p, "bubble", where, text


GUIDE_KEYS = {"meaning", "q", "a", "title", "body"}
_FIGURE = re.compile(r"\{[a-z_]+\}")


def guide_strings(root):
    """data/guide/*.json (T-2662's glossary and FAQ, T-2667's About this destination): every
    string under a key a visitor reads -- a glossary `meaning`, an FAQ `q` and `a`, a card's
    `title` and `body`. A card's {figure} is computed by tools/compile_about_destination.py,
    and a numeral is one word of one syllable here whatever its value, so a figure is scored
    as the numeral "7" and the copy reads the same as it will with its real number."""
    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                at = f"{where}.{k}" if where else k
                if k in GUIDE_KEYS and isinstance(v, str):
                    yield at, _FIGURE.sub("7", v)
                elif not k.startswith("_") and k not in ("note", "rests_on", "researcher"):
                    yield from walk(v, at)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{where}[{i}]")
    for p in sorted((Path(root) / "data" / "guide").glob("*.json")):
        for where, text in walk(cs.load_json(p), ""):
            yield p, "guide", where, text


SOURCES = (("summaries", summary_strings), ("time-stream captions", caption_strings),
           ("tour bubbles", bubble_strings), ("guide", guide_strings))


# ------------------------------------------------------------------ the gate

def audit(root=ROOT):
    """(faults, rows, counts) for every string under `root`."""
    faults, rows, counts = [], [], {}
    for label, reader in SOURCES:
        counts[label] = 0
        by_file = {}
        for path, kind, where, text in reader(root):
            counts[label] += 1
            rel = Path(path).relative_to(root)
            s = score(text)
            by_file.setdefault(rel, []).append(s)
            rows.append((rel, kind, where, s, text))
            at = f"{rel} {where} ({kind})"
            for sent in split_sentences(text):
                n = len(cs.words(sent))
                if n > MAX_SENTENCE_WORDS:
                    faults.append(f"{at}: a sentence of {n} words (at most {MAX_SENTENCE_WORDS}): \"{sent}\"")
            if s["words"] >= MIN_FK_WORDS and s["grade"] > MAX_GRADE:
                faults.append(f"{at}: Flesch-Kincaid grade {s['grade']:.1f} (at most {MAX_GRADE:g}): \"{text}\"")
            if kind == "bubble" and s["words"] > MAX_BUBBLE_WORDS:
                faults.append(f"{at}: a bubble of {s['words']} words (at most {MAX_BUBBLE_WORDS}): \"{text}\"")
        for rel, scores in by_file.items():
            g = pooled(scores)
            if g > MAX_GRADE:
                faults.append(f"{rel}: its strings pooled read at Flesch-Kincaid grade {g:.1f} (at most {MAX_GRADE:g})")
    return faults, rows, counts


def report(root=ROOT, show=False):
    faults, rows, counts = audit(root)
    if show:
        for rel, kind, where, s, text in rows:
            print(f"  {s['grade']:5.1f}  {s['words']:3d}w {s['longest']:3d}max  {kind:8} {rel} {where}: {text}")
    for f in faults:
        print(f"  FAIL {f}")
    read = ", ".join(f"{n} strings from {label}" for label, n in counts.items())
    if faults:
        print(f"reading level: {len(faults)} fault(s) in {read}")
        return 1
    worst = max((r[3]["grade"] for r in rows if r[3]["words"] >= MIN_FK_WORDS), default=None)
    print(f"reading level OK — {read}; every sentence at most {MAX_SENTENCE_WORDS} words, "
          f"every string of {MIN_FK_WORDS}+ words and every file at Flesch-Kincaid grade {MAX_GRADE:g} or lower"
          + (f" (hardest {worst:.1f})" if worst is not None else ""))
    return 0


# ------------------------------------------------------------------ the self-test

KNOWN_SYLLABLES = {
    "house": 1, "the": 1, "stone": 1, "granite": 2, "table": 2, "fortress": 2,
    "courtyard": 2, "architect": 3, "landmark": 2, "national": 3, "historic": 3,
    "reconstructed": 4, "inferred": 2, "attested": 3, "Chicago": 3, "Glessner": 2,
    "named": 1, "buildings": 2, "boxes": 2, "changes": 2, "wanted": 2, "loaded": 2,
    "every": 3, "museum": 3, "people": 2, "nation": 2, "special": 2, "radio": 3, "1966": 1, "$35,000": 1,
}

GRADE_12 = ("The architectural significance of the residence derives principally from its "
            "uncompromising horizontality and its deliberate repudiation of Victorian ornamentation.")


def self_test():
    ok = True

    def expect(label, cond):
        nonlocal ok
        ok &= bool(cond)
        print(f"self-test: {label} {'ok' if cond else 'FAIL'}")

    off = {w: (syllables(w), n) for w, n in KNOWN_SYLLABLES.items() if syllables(w) != n}
    expect(f"syllables read the {len(KNOWN_SYLLABLES)} pinned words as pinned" + (f" (off: {off})" if off else ""), not off)
    for text in ["Built in 1887. H. H. Richardson drew it. It stands at 1800 S. Prairie Ave. today.",
                 "One. Two two! Three three three? And a fourth with no stop",
                 "A single sentence with no full stop"]:
        expect(f"split_sentences agrees with T-2635's count on {text[:24]!r}",
               len(split_sentences(text)) == cs.sentences(text))
    g = score(GRADE_12)["grade"]
    expect(f"the planted sentence scores grade 12 or more (reads {g:.1f})", g >= 12)
    plain = "A granite fortress on the street, a sunny courtyard inside."
    expect(f"the design doc's own after-line passes (reads {score(plain)['grade']:.1f})", score(plain)["grade"] <= MAX_GRADE)

    real_faults, _, _ = audit(ROOT)
    expect("the committed copy passes", not real_faults)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "data" / "timestream").mkdir(parents=True)
        (root / "data" / "summaries").mkdir(parents=True)
        (root / "data" / "tour").mkdir(parents=True)
        (root / "data" / "guide").mkdir(parents=True)

        def write(rel, doc):
            (root / rel).write_text(json.dumps(doc), encoding="utf-8")

        def faults_with(files):
            for p in list((root / "data").rglob("*.json")):
                p.unlink()
            for rel, doc in files.items():
                write(rel, doc)
            return audit(root)[0]

        base_deck = {"scene": "1904", "captions": [{"year": 1976, "text": "The house is named a landmark."}]}
        base_summary = {"id": "x", "summary": "A granite fortress on the street. A sunny courtyard inside.",
                        "key": [{"label": "Built", "value": "1887", "grade": "attested"}],
                        "notable": [{"text": "The front door faces the side street.", "grade": "attested"}]}
        base_tour = {"steps": [{"bubble": "Walk. Left thumb, or W A S D. Head for the corner."}]}
        clean = faults_with({"data/timestream/1904.json": base_deck, "data/summaries/x.json": base_summary,
                             "data/tour/field_check.json": base_tour})
        expect("a clean planted tree passes", not clean)

        def planted(label, mutate, needle):
            deck, summ, tour = copy.deepcopy(base_deck), copy.deepcopy(base_summary), copy.deepcopy(base_tour)
            mutate(deck, summ, tour)
            fs = faults_with({"data/timestream/1904.json": deck, "data/summaries/x.json": summ,
                              "data/tour/field_check.json": tour})
            expect(f"{label} is refused", any(needle in f for f in fs))

        planted("a grade-12 caption",
                lambda d, s, t: d["captions"].append({"year": 1966, "text": GRADE_12}), "Flesch-Kincaid grade")
        planted("a grade-12 summary",
                lambda d, s, t: s.__setitem__("summary", GRADE_12), "(summary): Flesch-Kincaid")
        planted("a grade-12 fact",
                lambda d, s, t: s["notable"].append({"text": GRADE_12, "grade": "inferred"}), "(fact): Flesch-Kincaid")
        planted("a grade-12 bubble",
                lambda d, s, t: t["steps"].append({"bubble": GRADE_12}), "(bubble): Flesch-Kincaid")
        long_plain = " ".join(["The", "cat", "sat", "on", "the", "mat", "and", "then", "the", "dog"] * 2) + " ran."
        planted("a sentence of 21 plain words",
                lambda d, s, t: d["captions"].append({"year": 1950, "text": long_plain}), "a sentence of 21 words")
        planted("a 15-word bubble",
                lambda d, s, t: t["steps"].append({"bubble": "Tap the red door to see who lived in this house in the year 1904."}),
                "a bubble of 15 words")
        fs = faults_with({"data/timestream/1904.json": base_deck, "data/summaries/x.json": base_summary,
                          "data/tour/field_check.json": base_tour,
                          "data/guide/about.json": {"cards": [{"id": "x", "title": "Sources", "scenes": {
                              "1835": {"body": GRADE_12 + " {figure}"}}}]}})
        expect("a grade-12 card in the Guide is refused", any("(guide): Flesch-Kincaid" in f for f in fs))
        planted("a file of short hard lines (each under the per-string floor)",
                lambda d, s, t: d["captions"].extend({"year": 1900 + i, "text": "Unprecedented architectural repudiation."}
                                                     for i in range(4)),
                "pooled read at Flesch-Kincaid")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true")
    g.add_argument("--print", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return 0 if self_test() else 1
    if a.check or a.print:
        return report(show=a.print)
    ap.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
