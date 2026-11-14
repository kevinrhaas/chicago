#!/usr/bin/env python3
"""T-3590: a jaunt's reading level, and the school grade band it is tagged with.

Every jaunt carries `grade_band`, the US school grades its words are written for, in the bands
the Common Core literacy standards and most state standards group texts by: K-2, 3-5, 6-8,
9-10, 11-12. The band is measured, not guessed: the Flesch-Kincaid grade level over every word
the visitor reads (the opening, each stop's text and narrative, each walk's story, each
choice and its consequence, each ending), mapped to the band that holds it. No one formula is
trusted alone: the grade is the mean of the five standard US grade-level formulas (Flesch-Kincaid,
Coleman-Liau, the Automated Readability Index, Gunning Fog and SMOG), the consensus a
readability library reports, here computed with no dependency. A text measured past grade 12 is
11-12, the top band. The owner, 2026-11-13: "tag that jaunt with an education
level of 3rd-x grade ... and tag the other jaunts as whatever level they are ... in the future
we will add more versions of the same jaunts targeted at different grade levels".

A jaunt's tag may sit one band off its measure (a formula is a rough reader), never two; a
jaunt written for children (K-2 or 3-5) must measure inside its own band.

    python3 tools/jaunt_reading_level.py            # every jaunt: measured grade, band, tag
    python3 tools/jaunt_reading_level.py --check    # fail on a tag too far from its measure
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANDS = ('K-2', '3-5', '6-8', '9-10', '11-12')
TOP = {'K-2': 2, '3-5': 5, '6-8': 8, '9-10': 10, '11-12': 99}
CHILDREN = {'K-2', '3-5'}
NOT_JAUNTS = {'schema.json', 'daybook.json'}

WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*|\d[\d,.]*")
SENTENCE_END = re.compile(r"[.!?]+[\"'’”)]*(?=\s|$)|\n\s*\n")
# A full stop that ends a title or an initial ends no sentence.
ABBREVIATION = re.compile(r"\b(?:Mr|Mrs|Dr|St|Co|Ave|Jr|Sr|Capt|Lt|Gen|Col|Rev|No|Mt|Ft|[A-Z])\.")
HEADING = re.compile(r"^[A-Z0-9 :,'’&.-]{6,}\.\s*")


def syllables(word):
    """A count good enough for a readability formula: vowel groups, less a silent final e."""
    w = word.lower().replace('’', "'")
    if w[0].isdigit():
        return max(1, len(re.sub(r'\D', '', w)))   # a number is read aloud: one per digit, roughly
    w = re.sub(r"'s$|'", '', w)
    if len(w) <= 3:
        return 1
    w = re.sub(r'(?:[^laeiouy]es|[^laeiouy]ed|[^laeiouy]e)$', '', w)
    w = re.sub(r'^y', '', w)
    return max(1, len(re.findall(r'[aeiouy]+', w)))


def texts(doc):
    """Every passage the visitor reads in a jaunt."""
    out = [doc.get('opening', {}).get('text', '')]
    for stop in doc.get('stops', []):
        out += [stop.get('text', ''), stop.get('narrative', '')]
        for c in stop.get('choices', []):
            out += [c.get('label', ''), c.get('consequence', '')]
    out += [leg.get('story', '') for leg in doc.get('legs', [])]
    out += [e.get('text', '') for e in doc.get('endings', [])]
    return [t for t in out if t and t.strip()]


def measure(doc):
    """A jaunt's reading grade (one decimal): the mean of five grade-level formulas, with each and the counts."""
    words = sentences = syl = poly = chars = 0
    for t in texts(doc):
        # A heading in capitals ("JAUNT: THE GLESSNER HOUSEHOLD.") is a title, not prose.
        t = ABBREVIATION.sub(lambda m: m.group(0)[:-1], HEADING.sub('', t.strip()))
        ws = WORD.findall(t)
        if not ws:
            continue
        counts = [syllables(w) for w in ws]
        words += len(ws)
        syl += sum(counts)
        poly += sum(1 for c in counts if c >= 3)
        chars += sum(len(re.sub(r'\W', '', w)) for w in ws)
        sentences += max(1, len(SENTENCE_END.findall(t)))
    if not words:
        return {'grade': 0.0, 'words': 0, 'sentences': 0, 'formulas': {}}
    wps, letters, per100 = words / sentences, chars / words, 100 / words
    formulas = {
        'flesch_kincaid': 0.39 * wps + 11.8 * syl / words - 15.59,
        'coleman_liau': 0.0588 * letters * 100 - 0.296 * sentences * per100 - 15.8,
        'ari': 4.71 * letters + 0.5 * wps - 21.43,
        'gunning_fog': 0.4 * (wps + 100 * poly / words),
        'smog': 1.043 * (poly * 30 / sentences) ** 0.5 + 3.1291,
    }
    grade = sum(formulas.values()) / len(formulas)
    return {'grade': round(grade, 1), 'words': words, 'sentences': sentences,
            'formulas': {k: round(v, 1) for k, v in formulas.items()}}


def band_of(grade):
    for band in BANDS:
        if grade < TOP[band] + 1:   # grade 5.9 still reads as fifth grade
            return band
    return BANDS[-1]


def problem(doc):
    """Why a jaunt's grade_band does not fit its words, or None."""
    tag = doc.get('grade_band')
    if tag not in BANDS:
        return f'grade_band {tag!r} is not one of {", ".join(BANDS)}'
    m = measure(doc)
    got = band_of(m['grade'])
    if tag in CHILDREN and got != tag:
        return f'written for grades {tag} but reads at grade {m["grade"]} ({got})'
    if abs(BANDS.index(got) - BANDS.index(tag)) > 1:
        return f'tagged grades {tag} but reads at grade {m["grade"]} ({got})'
    return None


def jaunts():
    for path in sorted((ROOT / 'data/jaunts').glob('*.json')):
        if path.name in NOT_JAUNTS:
            continue
        yield path, json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='fail when a tag is too far from its measure')
    args = ap.parse_args()
    bad = []
    for path, doc in jaunts():
        m, why = measure(doc), problem(doc)
        print(f"{doc.get('scene', '?'):>5}  {m['grade']:>5}  {band_of(m['grade']):>5}  tag {doc.get('grade_band', '-'):>5}  {path.stem}"
              + (f'  <- {why}' if why else ''))
        if why:
            bad.append(f'{path.stem}: {why}')
    if args.check and bad:
        sys.exit('READING LEVEL FAIL\n' + '\n'.join(bad))
    if args.check:
        print('READING LEVEL PASS')


if __name__ == '__main__':
    main()
