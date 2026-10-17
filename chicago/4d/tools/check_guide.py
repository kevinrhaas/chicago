#!/usr/bin/env python3
"""Gate the Guide's glossary and FAQ: data/guide/glossary.json and data/guide/faq.json (T-2662).

    python3 tools/check_guide.py --check       gate both files; write nothing
    python3 tools/check_guide.py --self-test   plant each fault and require it refused by name

Design doc "Field Navigator Mk II" section 03 (locked terms, voice) and NAV-804. A visitor
reads these strings exactly as written, so this refuses:

  - a glossary that is not exactly the seven locked terms, spelled exactly, in section 03's
    order (Attested, Inferred, Reconstructed, Confidence view, Liberties, Sources, Jaunts);
  - a meaning over 15 words; an FAQ answer over 60 words; any sentence over 20 words;
  - a reading grade over 9 (Flesch-Kincaid, section 03's own measure; a vowel-group
    syllable count, so it is an estimate, and T-2669 owns the project-wide gate);
  - an FAQ missing "Is this real?" or "What does Reconstructed mean?";
  - a grade word in lower case ("reconstructed"), which is the locked term not used exactly,
    and a retired term (documented, conjectural, Evidence, Citations, section 03);
  - any id, snake_case word, file path, link or ticket number (compile_summaries.lint_string,
    imported, so this gate and the summary gate agree);
  - and a `rests_on` path that does not exist: every claim the Guide makes about the project
    names the files that make it true.
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from compile_summaries import lint_string, sentences, words  # noqa: E402

GUIDE = ROOT / "data" / "guide"
LOCKED = ["Attested", "Inferred", "Reconstructed", "Confidence view", "Liberties", "Sources", "Jaunts"]
REQUIRED_QUESTIONS = ["Is this real?", "What does Reconstructed mean?"]
RETIRED = ["documented", "conjectural", "Evidence", "Citations"]
LIMITS = {"meaning": 15, "answer": 60, "sentence": 20, "grade": 9.0}


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def split_sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])", text.strip()) if s]


def fk_grade(text):
    ws = words(text)
    if not ws:
        return 0.0
    n_sent = max(1, sentences(text))
    syl = sum(syllables(w) for w in ws)
    return 0.39 * (len(ws) / n_sent) + 11.8 * (syl / len(ws)) - 15.59


def voice(where, text):
    errs = []
    for s in split_sentences(text):
        if len(words(s)) > LIMITS["sentence"]:
            errs.append(f"{where}: a sentence of {len(words(s))} words, over the limit of {LIMITS['sentence']}")
    g = fk_grade(text)
    if g > LIMITS["grade"]:
        errs.append(f"{where}: reading grade {g:.1f}, over the limit of {LIMITS['grade']:.0f}")
    for term in ("attested", "inferred", "reconstructed"):
        if re.search(rf"\b{term}\b", text):
            errs.append(f"{where}: `{term}` in lower case; the locked term is `{term.capitalize()}`")
    for term in RETIRED:
        if re.search(rf"\b{term}\b", text, re.IGNORECASE if term.islower() else 0):
            errs.append(f"{where}: the retired term `{term}`")
    errs += [f"{where}: {w} in a string a visitor reads" for w in lint_string(text)]
    return errs


def rests_on(where, paths, root):
    if not paths:
        return [f"{where}: no `rests_on` — say which files make this true"]
    return [f"{where}: rests on `{p}`, which does not exist" for p in paths if not (root / p).exists()]


def gate(glossary, faq, root=ROOT):
    errs = []
    terms = glossary.get("terms") or []
    names = [t.get("term") for t in terms]
    if names != LOCKED:
        errs.append(f"glossary: terms are {names}, and must be exactly {LOCKED}, in that order")
    for t in terms:
        where = f"glossary `{t.get('term')}`"
        m = t.get("meaning") or ""
        if not m.strip():
            errs.append(f"{where}: no meaning")
        if len(words(m)) > LIMITS["meaning"]:
            errs.append(f"{where}: {len(words(m))} words, over the limit of {LIMITS['meaning']}")
        errs += voice(where, m)
        errs += rests_on(where, t.get("rests_on"), root)
    qs = faq.get("questions") or []
    asked = [q.get("q") for q in qs]
    for need in REQUIRED_QUESTIONS:
        if need not in asked:
            errs.append(f"faq: the question {need!r} is missing")
    for q in qs:
        where = f"faq {q.get('q')!r}"
        a = q.get("a") or ""
        if len(words(a)) > LIMITS["answer"]:
            errs.append(f"{where}: {len(words(a))} words, over the limit of {LIMITS['answer']}")
        errs += voice(where, q.get("q") or "") + voice(where, a)
        errs += rests_on(where, q.get("rests_on"), root)
    return errs


def load():
    return (json.loads((GUIDE / "glossary.json").read_text(encoding="utf-8")),
            json.loads((GUIDE / "faq.json").read_text(encoding="utf-8")))


def check():
    g, f = load()
    errs = gate(g, f)
    for e in errs:
        print(f"FAIL: {e}")
    if errs:
        print(f"FAIL: {len(errs)} problem(s) in the Guide's glossary and FAQ")
        return 1
    worst = max([fk_grade(t["meaning"]) for t in g["terms"]] + [fk_grade(q["a"]) for q in f["questions"]])
    print(f"OK: {len(g['terms'])} locked terms and {len(f['questions'])} answers, every one within "
          f"its lengths, reading grade at most {worst:.1f}, and every claim resting on files that exist")
    return 0


def self_test():
    g, f = load()
    fails = 0

    def expect(label, mutate, needle):
        nonlocal fails
        g2, f2 = copy.deepcopy(g), copy.deepcopy(f)
        mutate(g2, f2)
        errs = gate(g2, f2)
        hit = any(needle in e for e in errs) if needle else not errs
        print(f"  {'ok  ' if hit else 'FAIL'} {label}" + ("" if hit else f": {errs[:3]}"))
        fails += 0 if hit else 1

    expect("the committed glossary and FAQ pass", lambda g, f: None, None)
    expect("a locked term missing", lambda g, f: g["terms"].pop(), "must be exactly")
    expect("a locked term misspelled", lambda g, f: g["terms"][3].update(term="Confidence View"), "must be exactly")
    expect("a sixteen-word meaning", lambda g, f: g["terms"][0].update(meaning=" ".join(["word"] * 16)), "over the limit of 15")
    expect("a sixty-one-word answer", lambda g, f: f["questions"][0].update(a=("Yes it is. " * 21).strip()), "over the limit of 60")
    expect("a twenty-one-word sentence", lambda g, f: f["questions"][0].update(a=" ".join(["word"] * 21) + "."), "over the limit of 20")
    expect("a hard sentence", lambda g, f: g["terms"][1].update(meaning="Interpretively extrapolated probabilistic determinations."), "reading grade")
    expect("a grade word in lower case", lambda g, f: f["questions"][1].update(a="It is reconstructed."), "in lower case")
    expect("a retired term", lambda g, f: g["terms"][5].update(meaning="See the Evidence for each fact."), "retired term")
    expect("a snake_case id", lambda g, f: g["terms"][6].update(meaning="Open across_wolf_point to start."), "snake_case")
    expect("a ticket number", lambda g, f: f["questions"][0].update(a="Fixed in T-2662."), "ticket number")
    expect("a required question missing", lambda g, f: f["questions"].pop(), "is missing")
    expect("a claim resting on a file that does not exist",
           lambda g, f: g["terms"][4].update(rests_on=["docs/NO_SUCH_FILE.md"]), "does not exist")
    expect("a claim resting on nothing", lambda g, f: f["questions"][0].update(rests_on=[]), "no `rests_on`")
    print(f"check_guide self-test: {'FAIL' if fails else 'OK'} ({fails} assertion(s) did not fire as required)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--check", action="store_true")
    m.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    return self_test() if a.self_test else check()


if __name__ == "__main__":
    sys.exit(main())
