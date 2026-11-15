#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The ten 1904 story jaunts (the owner, 2026-11-15: "add 10 new dramatic story telling jaunts in
1904 based on these stories ... dramatic compelling factual ... make each stop want to lead you
to the next ... a strong story arch and conclusion and ... well developed cinematic characters").

Writes data/jaunts/<id>.json for each jaunt in stories.py, from the claims in claims.py (new ones,
and others' borrowed whole by id), with each stop staged by its people
(renderers/web/js/jaunt-stage.js). Marks are local ENU metres: a structure's are measured out
from its front toward the stand the app frames it from (stands.json, written by stands.mjs
beside this file, the router check_jaunt_views.mjs uses), an anchor's from its own stand.

    python3 docs/RESEARCH/jaunt-stories-1904/build.py           # write
    python3 docs/RESEARCH/jaunt-stories-1904/build.py --check   # the jaunts are as built
"""
import glob
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import claims as C  # noqa: E402
import stories  # noqa: E402
import directions as D  # noqa: E402

LIBERTY = C.LIBERTY
STANDS = json.loads((HERE / 'stands.json').read_text())
SCENE = json.loads((ROOT / 'data/scenes/1904.json').read_text())


def _anchors(o):
    if isinstance(o, dict):
        if isinstance(o.get('anchors'), list): return o['anchors']
        for v in o.values():
            r = _anchors(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = _anchors(v)
            if r: return r
    return None


ANCHORS = {a['id']: a for a in _anchors(SCENE)}
INSIDE = {e['person']: e for e in json.loads((ROOT / 'data/humans/inside_1904.json').read_text())['people']}
DRAWN = {json.loads(Path(f).read_text())['person_id'] for f in glob.glob(str(ROOT / 'data/humans/instances/1904/hi_*.json'))}
PEOPLE = {p['id']: p for p in json.loads((ROOT / 'data/sidecars/1904/people.json').read_text())['people']}


def castable(pid):
    return pid in PEOPLE and (pid in DRAWN or bool(INSIDE.get(pid, {}).get('asset_id')))


# ── marks ───────────────────────────────────────────────────────────────────────────────────
def P(e, n):
    return [round(e, 2), round(n, 2)]


def hd(a, b):
    return round((math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360) % 360, 1)


def at(sid, a, b=0.0):
    """`a` m out from the structure's front toward its stand, `b` m across (right, seen from the stand)."""
    s, f = STANDS[sid]['stand'], STANDS[sid]['front']
    de, dn = s[0] - f[0], s[1] - f[1]
    L = math.hypot(de, dn)
    ue, un = de / L, dn / L
    ve, vn = -un, ue          # the stand looking at the front has this on its right
    return P(f[0] + a * ue + b * ve, f[1] + a * un + b * vn)


def anchor(aid):
    a = ANCHORS[aid]
    return (a['local_e'], a['local_n'])


def _member(m, at_, face=None, heading=None, pose=None, hidden=None, beats=None):
    m['at'] = at_
    if face is not None and not isinstance(face, str):
        heading = hd(at_, face)
    if heading is not None:
        m['heading'] = round(heading % 360, 1)
    if pose: m['pose'] = pose
    if hidden: m['hidden'] = True
    if beats:
        m['beats'] = beats
    return m, face


def cast(pid, at_, **kw):
    if not castable(pid):
        raise SystemExit(f'{pid} has no figure in 1904')
    m, face = _member({'person': pid}, at_, **kw)
    if isinstance(face, str):
        m.setdefault('beats', []).insert(0, {'t': 0, 'face': face})
    return m


def figure(recipe):
    """The figure a 1904 recipe builds, by asset id: the recipe's own name (the children), its
    asset_id, or its first proof variant (lady_1904 builds glessner_frances_m_1904, worn by
    every lady of the town; an unnamed figure keyed by its own id gets its own face)."""
    r = json.loads((ROOT / f'data/humans/recipes/{recipe}.json').read_text())
    for a in (recipe, r.get('asset_id'), (r.get('proof_variants') or [{}])[0].get('id')):
        if a and (ROOT / f'assets/humans/{a}.lod0.glb').exists(): return a
    raise SystemExit(f'{recipe}: builds no figure')


def extra(slug, dress, name, at_, **kw):
    m, face = _member({'extra': slug, 'dress': figure(dress), 'name': name}, at_, **kw)
    if isinstance(face, str):
        m.setdefault('beats', []).insert(0, {'t': 0, 'face': face})
    return m


def beat(t, walk=None, pace=None, face=None, heading=None, pose=None, talk=None, greet=None, hide=None, show=None):
    b = {'t': t}
    if walk: b['walk'] = walk
    if pace: b['pace'] = pace
    if face is not None: b['face'] = face
    if heading is not None: b['heading'] = round(heading % 360, 1)
    if pose: b['pose'] = pose
    if talk is not None: b['talk'] = talk
    if greet: b['greet'] = True
    if hide: b['hide'] = True
    if show: b['show'] = True
    return b


# ── claims ──────────────────────────────────────────────────────────────────────────────────
def borrowed(cid):
    doc = json.loads((ROOT / f'data/jaunts/{C.BORROW[cid]}.json').read_text())
    return next(e for e in doc['evidence'] if e['id'] == cid)


def claim(cid):
    if cid in C.CLAIMS: return {'id': cid, **C.CLAIMS[cid]}
    if cid in C.BORROW: return borrowed(cid)
    raise SystemExit(f'no claim {cid}')


def read_s(text):
    return max(8, round(len(text.split()) / 3.8))


def dev_version(path):
    try:
        raw = subprocess.run(['git', 'show', f'origin/dev:chicago/4d/{path.relative_to(ROOT)}'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return json.loads(raw)['content_version'] + 1
    except Exception:
        return 1


def build(j):
    staging = C.staging(j['title'])
    used = []
    def use(ids):
        for i in ids:
            if i not in used: used.append(i)
    stops = []
    for k, s in enumerate(j['stops']):
        kind, did = s['dest']
        ev = list(s['evidence']) + (['day'] if k == 0 else []) + ['stage']
        use(ev)
        stop = {'id': s['id'], 'destination': {'kind': kind, 'id': did}, 'text': s['text'], 'evidence': ev}
        links = [{'kind': a, 'id': b, 'label': c} for a, b, c in s.get('links', [])]
        if links: stop['links'] = links
        stop['next'] = j['stops'][k + 1]['id'] if k + 1 < len(j['stops']) else j['endings'][0]['id']
        stop['read_s'] = read_s(s['text'])
        cast_ = s['cast']()
        stage = {'caption': s['caption'], 'liberty': LIBERTY, 'cast': cast_}
        if s.get('teams'): stage['teams'] = s['teams']()
        stop['stage'] = stage
        stops.append(stop)
    legs = []
    for leg in j['legs']:
        use(leg['evidence'] + leg['story_evidence'])
        assert len(leg['story']) <= 180, leg['story']
        legs.append({'story': leg['story'], 'evidence': leg['evidence'], 'story_evidence': leg['story_evidence']})
    use(j.get('extra_evidence', []))
    evidence = []
    for cid in used:
        evidence.append(staging[cid] | {'id': cid} if cid in staging else claim(cid))
    evidence = [{'id': e['id'], **{k: v for k, v in e.items() if k != 'id'}} for e in evidence]
    fam, ktitle, ktext = j['keepsake']
    path = ROOT / f'data/jaunts/{j["id"]}.json'
    doc = {
        'schema_version': 1, 'content_version': dev_version(path),
        'category': 'True stories', 'menu_group': 'Stories', 'grade_band': j.get('grade_band', '6-8'),
        'review_required': False, 'id': j['id'], 'scene': '1904', 'title': j['title'], 'premise': j['premise'],
        'default_mode': 'walk', 'allowed_modes': ['walk', 'fly', 'instantly'], 'long_form': True,
        'ambience': {'hour': j['hour'], 'season': 'fall'},
        'opening': {'text': j['opening'], 'read_s': read_s(j['opening'])},
        'stops': stops, 'legs': legs,
        'endings': [{'id': e['id'], 'text': e['text'], 'read_s': read_s(e['text']), 'completion_eligible': True} for e in j['endings']],
        'keepsake': {'family': fam, 'id': f'{j["id"]}-card', 'title': ktitle, 'text': ktext},
        'evidence': evidence, 'liberties': [LIBERTY],
    }
    assert len(doc['premise']) <= 260, (j['id'], len(doc['premise']))
    return path, doc


def words(text):
    """tools/narrate_jaunts.mjs spokenWords: the words alone, tags, case and punctuation aside."""
    import re
    return re.findall(r'[^\W_]+', re.sub(r'\[[^\]]*\]', ' ', text).lower())


def straight(t):
    return t.replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'")


def direction(doc):
    """The performance copy of each narrator script (T-3578 format), its words the panel's own."""
    texts = {'opening:opening': doc['opening']['text'], **{f'stop:{s["id"]}': s['text'] for s in doc['stops']},
             **{f'ending:{e["id"]}': e['text'] for e in doc['endings']}}
    plan, scripts, misses = D.DIRECTIONS[doc['id']], {}, []
    for key, text in texts.items():
        lead, edits = plan.get(key, ('', []))
        out = text
        for old, new in edits:
            old, new = straight(old), straight(new)
            if out.count(old) != 1: misses.append(f'{doc["id"]}/{key}: {old!r} found {out.count(old)} times'); continue
            out = out.replace(old, new)
        out = (lead + ' ' + out).strip() if lead else out
        if words(out) != words(text): misses.append(f'{doc["id"]}/{key}: the performed words differ from the panel\'s')
        scripts[key] = out
    if set(plan) - set(texts): misses.append(f'{doc["id"]}: direction for parts it does not have: {sorted(set(plan) - set(texts))}')
    return {'$comment': "T-3578 format, written by docs/RESEARCH/jaunt-stories-1904/build.py from directions.py: the same words as the panel shows, with ElevenLabs v3 audio tags in square brackets and ellipses and [short pause]/[long pause] for pauses. Performance only: a whisper or a sigh is a reading of the story, not evidence of how anyone spoke (L-jaunt-voices-3578). Keyed <part>:<id>.",
            'version': 1, 'jaunt': doc['id'], 'scripts': scripts}, misses


def main(check=False):
    stale, missed = [], []
    sys.modules['build_h'] = sys.modules[__name__]
    for j in stories.jaunts(sys.modules[__name__]):
        path, doc = build(j)
        body = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
        perf, misses = direction(doc)
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
            words = [len(s['text'].split()) for s in doc['stops']]
            print(f'wrote {path.relative_to(ROOT)}: {len(doc["stops"])} stops ({min(words)}-{max(words)} words), '
                  f'{sum(len(s["stage"]["cast"]) for s in doc["stops"])} castmates, {len(doc["evidence"])} claims')
    if missed:
        raise SystemExit('direction refused:\n  ' + '\n  '.join(missed))
    if stale:
        raise SystemExit('stale: ' + ', '.join(stale) + '; run build.py')


if __name__ == '__main__':
    main('--check' in sys.argv)
