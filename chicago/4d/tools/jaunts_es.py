#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The Spanish telling of every jaunt (gap analysis item 15, "Spanish").

A Spanish jaunt is the same walk in another language: nothing about the walk changes, only the
words the visitor reads. Each jaunt's Spanish lives in a words file, data/jaunts/_es/<id>.txt,
in the format the grade versions use (docs/RESEARCH/jaunt-grade-versions-3621/versions.py):
a line `== <key>` starts a passage and the passage runs to the next such line. The keys are
that tool's (premise, opening, stop <id>, narrative <id>, caption <id>, label <stop> <choice>,
consequence <stop> <choice>, leg <n>, note <n>, ending <id>, keepsake title, keepsake text)
plus `title`, the jaunt's name.

Each key line also carries the English it was translated from, as `@` and the first eight hex
of that passage's SHA-1: `== stop cloth @1a2b3c4d`. The overlay keeps each mark beside its
Spanish, and the app (js/jaunt-language.js) puts a passage over the English only while the
English it shows still has that mark. When the English changes after the Spanish was written (a
fact corrected, a stop re-told, the build log rewritten from the building records), the visitor
reads the corrected English there instead: a stale Spanish passage can never contradict its
English. The overlay is built from the words files alone, so a change to a jaunt's English never
stales it; `--report` lists the passages a translator should revisit.

A translation adds nothing: no fact, no name, no hedge that the English does not have.
Quotations from the sources are given in Spanish; the jaunt panel says, in Spanish, that the
quotations are translated from English.

    python3 tools/jaunts_es.py                  write data/sidecars/<scene>/jaunts/es/
    python3 tools/jaunts_es.py --check          the overlays are as built, every words file parses
    python3 tools/jaunts_es.py --template ID    the English passages of jaunt ID, keyed and marked
    python3 tools/jaunts_es.py --report         per jaunt: passages translated, missing, stale
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'docs/RESEARCH/jaunt-grade-versions-3621'))
import versions  # noqa: E402  (passages() and get(): one list of what a visitor reads)

JAUNTS = ROOT / 'data/jaunts'
WORDS = JAUNTS / '_es'
SIDECARS = ROOT / 'data/sidecars'
NOT_JAUNTS = {'schema.json', 'daybook.json', 'catalog-55.json'}
KEY = re.compile(r'^== (.+?)\s*$', re.M)
MARK = re.compile(r'^(.*?)\s+@([0-9a-f]{8})$')


def mark(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]


def keys(doc):
    yield 'title', True
    yield from versions.passages(doc)


def english(doc, key):
    return doc['title'] if key == 'title' else versions.get(doc, key)


def parse(path):
    """{key: (mark, text)} from a words file."""
    parts = KEY.split(path.read_text(encoding='utf-8'))
    if parts[0].strip():
        raise ValueError(f'{path.name}: text before the first == key')
    out = {}
    for head, body in zip(parts[1::2], parts[2::2]):
        m = MARK.match(' '.join(head.split()))
        if not m:
            raise ValueError(f'{path.name}: "== {head}" carries no @mark of its English')
        key, sig = m[1], m[2]
        if key in out:
            raise ValueError(f'{path.name}: {key} given twice')
        body = body.strip()
        if not body:
            raise ValueError(f'{path.name}: {key} is empty')
        out[key] = (sig, body)
    return out


def jaunts():
    return {p.stem: json.loads(p.read_text()) for p in sorted(JAUNTS.glob('*.json')) if p.name not in NOT_JAUNTS}


def standing(doc, words):
    """(missing, stale) against today's English: passages with no Spanish, and Spanish whose
    English has changed (or whose passage is gone) since it was translated."""
    known = {}
    for key, _ in keys(doc):
        try:
            known[key] = english(doc, key)
        except (KeyError, IndexError, TypeError):
            continue
    stale = [k for k, (sig, _) in words.items() if k not in known or mark(known[k]) != sig]
    missing = [k for k in known if k not in words]
    return missing, stale


def build():
    """{scene: {file name: body}} and the per-jaunt report rows."""
    files, rows = {}, []
    docs = jaunts()
    stray = [p.stem for p in WORDS.glob('*.txt') if p.stem not in docs]
    if stray:
        raise ValueError(f"words files for no jaunt: {', '.join(sorted(stray))}")
    for jid, doc in docs.items():
        path = WORDS / f'{jid}.txt'
        if not path.exists():
            continue
        words = parse(path)
        missing, stale = standing(doc, words)
        rows.append((doc['scene'], jid, len(words) - len(stale), missing, stale))
        passages = {k: [sig, text] for k, (sig, text) in words.items()}
        scene = files.setdefault(doc['scene'], {'catalog': {}})
        scene[f'{jid}.json'] = packed({'id': jid, 'lang': 'es', 'passages': passages})
        scene['catalog'][jid] = {k: passages[k] for k in ('title', 'premise') if k in passages}
    for scene in files.values():
        scene['catalog.json'] = packed({'lang': 'es', 'jaunts': scene.pop('catalog')})
    return files, rows


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'


def template(jid):
    doc = json.loads((JAUNTS / f'{jid}.json').read_text())
    for key, required in keys(doc):
        try:
            text = english(doc, key)
        except (KeyError, IndexError, TypeError):
            continue
        print(f'== {key} @{mark(text)}')
        print(text)
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--template')
    args = ap.parse_args()
    if args.template:
        return template(args.template)
    try:
        files, rows = build()
    except ValueError as e:
        sys.exit(f'JAUNTS ES FAIL — {e}')
    if args.report:
        for scene, jid, n, missing, stale in rows:
            print(f"{scene}  {n:>3} es  {len(missing):>3} missing  {len(stale):>3} stale  {jid}")
        return
    scenes = {p.parent.parent.name for p in SIDECARS.glob('*/jaunts/es')} | set(files)
    bad = []
    for scene in sorted(scenes):
        dest = SIDECARS / scene / 'jaunts' / 'es'
        want = files.get(scene, {})
        have = {p.name for p in dest.glob('*.json')} if dest.exists() else set()
        stale = [n for n, body in want.items() if n not in have or (dest / n).read_text(encoding='utf-8') != body]
        extra = have - set(want)
        if args.check:
            bad += [f'{scene}/{n}' for n in stale + sorted(extra)]
            continue
        dest.mkdir(parents=True, exist_ok=True)
        for n, body in want.items():
            (dest / n).write_text(body, encoding='utf-8')
        for n in extra:
            (dest / n).unlink()
        if not want:
            dest.rmdir()
    if bad:
        sys.exit('JAUNTS ES STALE (run python3 tools/jaunts_es.py): ' + ', '.join(bad))
    done = sum(1 for r in rows if r[2])
    stale = sum(len(r[4]) for r in rows)
    print(f"JAUNTS ES PASS — {done} jaunts in Spanish; {stale} passage(s) whose English changed since translation read in English")


if __name__ == '__main__':
    main()
