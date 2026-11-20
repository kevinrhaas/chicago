#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The 1871 story jaunts: T-3692 The Last Sunday (last_sunday.py), and the others that join it.

Writes data/jaunts/<id>.json for each jaunt module in JAUNTS, from the claims in claims.py, and
data/narration/direction/<id>.json, the narrator's performance copy (T-3578 format) from the
module's DIRECTIONS. Edit the modules and run this; never hand-edit the JSON. The grade-band and
18+ tellings are versions (docs/RESEARCH/jaunt-grade-versions-3621/versions.py).

    python3 docs/RESEARCH/jaunt-stories-1871/build.py           # write
    python3 docs/RESEARCH/jaunt-stories-1871/build.py --check   # the jaunts are as built
"""
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import claims as C  # noqa: E402

JAUNTS = ['last_sunday']


def read_s(text):
    return max(8, round(len(text.split()) / 3.8))


def dev_version(path):
    try:
        raw = subprocess.run(['git', 'show', f'origin/dev:chicago/4d/{path.relative_to(ROOT)}'], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        return json.loads(raw)['content_version'] + 1
    except Exception:
        return 1


def claim(cid):
    if cid not in C.CLAIMS:
        raise SystemExit(f'no claim {cid}')
    c = C.CLAIMS[cid]
    order = ['text', 'confidence', 'sources', 'locator', 'reasoning', 'liberty']
    return {'id': cid, **{k: c[k] for k in order if k in c}}


def build(mod):
    j = mod.JAUNT
    used = []

    def use(ids):
        for i in ids:
            if i not in used: used.append(i)
    stops = []
    for k, s in enumerate(j['stops']):
        ev = list(s['evidence'])
        use(ev)
        stop = {'id': s['id'], 'destination': {'kind': 'anchor', 'id': s['anchor']}, 'text': s['text'], 'evidence': ev}
        links = [{'kind': a, 'id': b, 'label': c} for a, b, c in s.get('links', [])]
        if links: stop['links'] = links
        stop['next'] = j['stops'][k + 1]['id'] if k + 1 < len(j['stops']) else j['endings'][0]['id']
        stop['read_s'] = read_s(s['text'])
        if 'hour' in s:   # a stop told over the place, after the night, carries no clock
            stop['hour'] = s['hour']
            stop['date'] = s.get('date', mod.DATE)
            stop['hour_evidence'] = s.get('hour_evidence', ['sunday-walk'] if 'sunday-walk' in ev else ev[:1])
        n = len(s['text'].split())
        assert 25 <= n <= 150, (s['id'], n)
        stops.append(stop)
    legs = []
    for leg in j['legs']:
        use(leg['evidence'])
        out = {}
        if leg.get('story'):
            assert len(leg['story']) <= 180, leg['story']
            out['story'] = leg['story']
        if leg.get('note'): out['note'] = leg['note']
        if leg.get('mode'): out['mode'] = leg['mode']
        out['evidence'] = leg['evidence']
        if leg.get('story'): out['story_evidence'] = leg['evidence']
        legs.append(out)
    use(j.get('extra_evidence', []))
    liberties = sorted({C.CLAIMS[c]['liberty'] for c in used if C.CLAIMS[c].get('liberty')})
    fam, ktitle, ktext = j['keepsake']
    path = ROOT / f'data/jaunts/{j["id"]}.json'
    doc = {
        'schema_version': 1, 'content_version': dev_version(path),
        'category': j['category'], 'menu_group': 'Stories', 'menu_rank': j['menu_rank'],
        'grade_band': j.get('grade_band', '6-8'),
        'review_required': False, 'id': j['id'], 'scene': '1871', 'title': j['title'], 'premise': j['premise'],
        'default_mode': 'walk', 'allowed_modes': ['walk', 'fly', 'instantly'], 'long_form': True,
        'ambience': {'hour': j['hour'], 'season': 'fall'},
        'opening': {'text': j['opening'], 'read_s': read_s(j['opening'])},
        'stops': stops, 'legs': legs,
        'endings': [{'id': e['id'], 'text': e['text'], 'read_s': read_s(e['text']), 'completion_eligible': True,
                     **({'default': True} if i == 0 else {})} for i, e in enumerate(j['endings'])],
        'keepsake': {'family': fam, 'id': f'{j["id"]}-card', 'title': ktitle, 'text': ktext},
        'evidence': [claim(c) for c in used], 'liberties': liberties,
    }
    assert len(doc['premise']) <= 260, (j['id'], len(doc['premise']))
    return path, doc


def words(text):
    """tools/narrate_jaunts.mjs spokenWords: the words alone, tags, case and punctuation aside."""
    return re.findall(r'[^\W_]+', re.sub(r'\[[^\]]*\]', ' ', text).lower())


def straight(t):
    return t.replace('“', '"').replace('”', '"').replace('’', "'")


def opening_script(doc):
    """renderers/web/js/narration.js openingScript: the title, then the welcome without its
    leading "JAUNT: ITS TITLE." line, which the title replaces."""
    paras = [t.strip() for t in re.split(r'\n\s*\n', doc['opening']['text']) if t.strip()]
    if paras: paras[0] = re.sub(r'^JAUNT:\s*[^.!?]*[.!?]\s*', '', paras[0])
    body = '\n\n'.join(p for p in paras if p)
    return f"{doc['title'].strip()}.\n\n{body}" if body else ''


def direction(doc, plan):
    """The performance copy of each narrator script (T-3578 format), its words the voiced
    script's own (narration.js narrationScripts: the opening leads with the title)."""
    texts = {'opening:opening': opening_script(doc), **{f'stop:{s["id"]}': s['text'] for s in doc['stops']},
             **{f'ending:{e["id"]}': e['text'] for e in doc['endings']}}
    scripts, misses = {}, []
    for key, text in texts.items():
        lead, edits = plan.get(key, ('', []))
        out = text
        for old, new in edits:
            old, new = straight(old), straight(new)
            if out.count(old) != 1:
                misses.append(f'{doc["id"]}/{key}: {old!r} found {out.count(old)} times'); continue
            out = out.replace(old, new)
        out = (lead + ' ' + out).strip() if lead else out
        if words(out) != words(text): misses.append(f'{doc["id"]}/{key}: the performed words differ from the panel\'s')
        scripts[key] = out
    if set(plan) - set(texts): misses.append(f'{doc["id"]}: direction for parts it does not have: {sorted(set(plan) - set(texts))}')
    return {'$comment': "T-3578 format, written by docs/RESEARCH/jaunt-stories-1871/build.py from the jaunt's own module: the same words as the panel shows, with audio tags in square brackets and ellipses and [short pause]/[long pause] for pauses. Performance only: a whisper or a sigh is a reading of the story, not evidence of how anyone spoke (L-jaunt-voices-3578). Keyed <part>:<id>.",
            'version': 1, 'jaunt': doc['id'], 'scripts': scripts}, misses


def main(check=False):
    stale, missed = [], []
    for name in JAUNTS:
        mod = importlib.import_module(name)
        path, doc = build(mod)
        body = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
        perf, misses = direction(doc, mod.DIRECTIONS)
        missed += misses
        dpath = ROOT / f'data/narration/direction/{doc["id"]}.json'
        dbody = json.dumps(perf, indent=2, ensure_ascii=False) + '\n'
        if check:
            for pth, b in ((path, body), (dpath, dbody)):
                if not pth.exists() or pth.read_text() != b: stale.append(str(pth.relative_to(ROOT)))
        else:
            path.write_text(body)
            dpath.parent.mkdir(parents=True, exist_ok=True)
            dpath.write_text(dbody)
            n = [len(s['text'].split()) for s in doc['stops']]
            print(f'wrote {path.relative_to(ROOT)}: {len(doc["stops"])} stops ({min(n)}-{max(n)} words), {len(doc["evidence"])} claims')
    if missed:
        raise SystemExit('direction refused:\n  ' + '\n  '.join(missed))
    if stale:
        raise SystemExit('stale: ' + ', '.join(stale) + '; run build.py')


if __name__ == '__main__':
    main('--check' in sys.argv)
