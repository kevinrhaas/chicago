#!/usr/bin/env python3
"""A fact for each building a jaunt's road notes pass (T-3379).

The owner, 2026-11-05: "on the jaunts when passing places include interesting and relevant
facts", and, of a road note that read only "Passing Dexter House, 1721 Prairie, on your
left", that it should carry those facts rather than a bare name. A "Passing …" line is
measured off this model's map at run time (jaunt-context.js); the fact that follows it is
not, and cites its sources like any other sentence of a jaunt.

One fact per structure, from the first of:

  1. data/jaunts/_names/place-facts.json, written for the houses with a story worth telling;
  2. the Inspect summary in data/summaries/<id>.json (its own `summary`, with its sources);
  3. for 1904, a sentence composed from the residents layer: who the Blue Book lists in the
     house in 1904, with the 1900 census's occupation where it reads cleanly, and who the
     earlier editions list there before them; and the year the record's marker gives.

Nothing here adds a claim the data does not already hold. compile_jaunts.py writes the
result into every compiled jaunt of the scene as `place_facts`.

    python3 tools/jaunt_place_facts.py --list 1904
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / 'data/jaunts/_names/place-facts.json'
STATUS = {'married', 'widowed', 'single', 'divorced', 'unknown', ''}


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


ABBREV = re.compile(r'(?:\b[A-Z]|\bJr|\bSr|\bMr|\bMrs|\bDr|\bSt|\bCo)\.$')


def sentence(text, limit=2):
    """The first `limit` sentences; an initial ('Philip D.') or 'Jr.' does not end one."""
    words, out, count = text.strip().split(' '), [], 0
    for i, w in enumerate(words):
        out.append(w)
        if re.search(r'[.!?]$', w) and not ABBREV.search(w) and (i + 1 == len(words) or words[i + 1][:1].isupper()):
            count += 1
            if count == limit:
                break
    return ' '.join(out)


def occupation(note):
    """'… married, lawyer (ED 40 …' -> 'lawyer'; None where the census line does not read."""
    m = re.search(r',\s*([^,()]+?)\s*(?:\([^)]*\))?\s*\(ED\b', note or '')
    word = (m.group(1).strip() if m else '').lower()
    word = re.sub(r'\bmfr\.?$', 'manufacturer', re.sub(r'^com\. ', 'commission ', word))
    if word in STATUS or not re.fullmatch(r"[a-z][a-z .'-]{2,40}", word) or re.search(r'\b(born|in|came)\b', word):
        return None
    # A trade a person is ('lawyer', 'dry goods merchant'), not a line of business ('wholesale').
    return word if re.search(r'(er|or|ist|man|ant|ian|clerk)$', word) else None


def article(word):
    return ('an ' if word[0] in 'aeiou' else 'a ') + word


def households(scene):
    homes = {}
    for path in sorted((ROOT / f'data/residents_{scene}/households').glob('*.json')):
        doc = read(path) or {}
        if (doc.get('present_on_scene_date') or {}).get('value') != 'present':
            continue
        head = next((p for p in doc.get('persons', []) if p.get('id') == doc.get('head')), None)
        for link in doc.get('associated_with', []):
            if link.get('kind') == 'home' and head:
                homes.setdefault(link['place_or_structure_id'], (doc, head))
    return homes


def composed(scene, structure, homes, former):
    sid, bits, sources = structure['id'], [], []
    if sid in homes:
        doc, head = homes[sid]
        job = occupation(head.get('note'))
        bits.append(f"In 1904 the Blue Book lists {head['name']} here" + (f", {article(job)} by the 1900 census." if job else '.'))
        sources += ['chicago_blue_book_1904'] + (['census_1900_chicago_t623_roll245'] if job else [])
    earlier = [f for f in (former.get(sid) or {}).get('former', [])
               if f.get('grade') == 'attested' and f.get('years') and sid in homes and f.get('role') == 'lived here'
               and max(f.get('editions') or [9999]) < 1904
               and f.get('name') and not f['name'].endswith(homes[sid][0]['name'].split(' household')[0].replace('The ', ''))]
    if earlier:
        f = earlier[0]
        bits.append(f"Before them, {f['name'].replace('The ', 'the ')} lived here ({f['years']}).")
        sources += f.get('sources', [])[:2]
    built = (structure.get('attributes') or {}).get('built') or {}
    if built.get('confidence') == 'attested' and isinstance(built.get('value'), int):
        bits.insert(0, f"Built in {built['value']}.")
        sources += built.get('sources', [])
    if not bits:
        return None
    return {'text': ' '.join(bits), 'confidence': 'attested', 'sources': list(dict.fromkeys(sources))}


def facts(scene, structures):
    scene = str(scene)
    authored = (read(TABLE) or {}).get(scene, {})
    homes = households(scene) if scene == '1904' else {}
    former = ((read(ROOT / 'data/residents_1904/former_residents.json') or {}).get('houses', {})
              if scene == '1904' else {})
    out = {}
    for s in structures:
        sid = s['id']
        if sid in authored:
            a = authored[sid]
            out[sid] = {'text': a['text'], 'confidence': a.get('confidence', 'attested'), 'sources': a['sources']}
            continue
        summary = read(ROOT / f'data/summaries/{sid}.json')
        if summary and summary.get('scene') == scene and summary.get('summary'):
            srcs = []
            for part in [summary.get('built') or {}, summary.get('status') or {}] + summary.get('key', []) + summary.get('notable', []):
                srcs += part.get('sources', [])
            if srcs:
                text = summary['summary'] if len(summary['summary'].split()) <= 45 else sentence(summary['summary'])
                out[sid] = {'text': text, 'confidence': 'attested',
                            'sources': list(dict.fromkeys(srcs))}
                continue
        fact = composed(scene, s, homes, former) if scene == '1904' else None
        if fact:
            out[sid] = fact
    return out


def check(scene, structures, known_sources):
    """Problems with the table and the facts: unknown ids or sources, over-long text."""
    problems = []
    ids = {s['id'] for s in structures}
    for sid, a in (read(TABLE) or {}).get(str(scene), {}).items():
        if sid.startswith('_'):
            continue
        if sid not in ids:
            problems.append(f'place-facts {scene}: {sid} is not a structure of the scene')
    for sid, f in facts(scene, structures).items():
        words = len(f['text'].split())
        if not 4 <= words <= 45:
            problems.append(f'place-facts {scene}: {sid} fact is {words} words (4-45)')
        if not f['sources']:
            problems.append(f'place-facts {scene}: {sid} fact cites nothing')
        for src in f['sources']:
            if src not in known_sources:
                problems.append(f'place-facts {scene}: {sid} cites unknown source {src}')
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', metavar='SCENE')
    args = ap.parse_args()
    if args.list:
        index = read(ROOT / f'data/sidecars/{args.list}/index.json')
        structures = [read(ROOT / 'data' / r['sidecar']) for r in index['structures']]
        for sid, f in sorted(facts(args.list, structures).items()):
            print(f'{sid}: {f["text"]}  [{", ".join(f["sources"])}]')


if __name__ == '__main__':
    main()
