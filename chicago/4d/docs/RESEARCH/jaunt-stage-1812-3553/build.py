#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: the 1812 story jaunts played by their people (renderers/web/js/jaunt-stage.js).

The owner, 2026-11-14: place the right people at the right scenes so the visitor watches the
events unfold (the attack at Lee's place and the flight, the people at the murder site, the
Lalime-Kinzie quarrel, the column coming down the shore and passing, the warriors gathered,
lying or kneeling before the attack); for students, "Build-up and aftermath": the lead-up is
watched, then the fallen lie still, and no blow, shot or blood is staged.

Writes each stop's `stage` into data/jaunts/battle-of-fort-dearborn.json and
killing-of-jean-lalime.json (content_version + 1 from origin/dev's) and declares the liberty
L-1812-staged-jaunts-3553 on both. Every mark is local ENU metres, read off the app's own views
from above (tools/qa_jaunt_stage_t3553.mjs QA_SURVEY) and the structures' sidecars.

    python3 docs/RESEARCH/jaunt-stage-1812-3553/build.py           # write
    python3 docs/RESEARCH/jaunt-stage-1812-3553/build.py --check   # the jaunts are as built
"""
import glob
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIBERTY = 'L-1812-staged-jaunts-3553'


def rel(p):
    return str(p.relative_to(ROOT))


def dev_version(path):
    """content_version on origin/dev, so a rebuild is always dev's + 1."""
    try:
        raw = subprocess.run(['git', 'show', f'origin/dev:chicago/4d/{rel(path)}'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return json.loads(raw)['content_version']
    except Exception:
        return json.loads(path.read_text())['content_version']


# ── who can be cast ─────────────────────────────────────────────────────────────────────────
INSIDE = {e['person']: e for e in json.loads((ROOT / 'data/humans/inside_1812.json').read_text())['people']}
DRAWN = {json.loads(Path(f).read_text())['person_id'] for f in glob.glob(str(ROOT / 'data/humans/instances/1812/hi_*.json'))}
PEOPLE = {p['id']: p for p in json.loads((ROOT / 'data/sidecars/1812/people.json').read_text())['people']}


def castable(pid):
    return pid in PEOPLE and (pid in DRAWN or (pid in INSIDE and INSIDE[pid].get('asset_id')))


def gathering(sex='male', lo=18, hi=50):
    """The gathering's people of one sex and age, carded and with a figure; for men, those whose
    card already gives 15 August as 'Likely among the warriors' (L-1812-native-cards-3507)."""
    out = []
    for f in sorted(glob.glob(str(ROOT / 'data/residents_1812/households/hh_gathering_*_1812.json'))):
        for p in json.loads(Path(f).read_text())['persons']:
            age = p.get('age_band', {}).get('low', 0)
            if p.get('sex') != sex or not (lo <= age <= hi) or not castable(p['id']):
                continue
            if sex == 'male' and 'Likely' not in str(p.get('on_15_august', {}).get('value', '')):
                continue
            out.append(p['id'])
    return out


MEN = gathering('male')
WOMEN = gathering('female', 16, 60)
_used = set()


def take(pool, n, stride=7, offset=0):
    """n people from a pool, spread across its camps (every `stride`th), none twice in a jaunt."""
    got, i = [], offset
    while len(got) < n and i < offset + len(pool) * stride:
        pid = pool[(i * stride) % len(pool)] if stride > 1 else pool[i % len(pool)]
        i += 1
        if pid not in _used:
            _used.add(pid); got.append(pid)
    return got


# ── marks ───────────────────────────────────────────────────────────────────────────────────
def P(e, n):
    return [round(e, 2), round(n, 2)]


def bearing(a, b):
    return round((math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360) % 360, 1)


def ring(centre, r, k, start=0.0, span=360.0):
    return [P(centre[0] + r * math.sin(math.radians(start + span * i / max(1, k - (0 if span >= 360 else 1)))),
              centre[1] + r * math.cos(math.radians(start + span * i / max(1, k - (0 if span >= 360 else 1))))) for i in range(k)]


def member(who, at, heading=None, pose=None, beats=None, tier=None, face=None, **extra):
    m = {}
    if who.startswith('extra:'):
        m['extra'] = who[6:]
    else:
        m['person'] = who
    m.update(extra)
    m['at'] = at
    if face is not None:
        heading = bearing(at, face)
    if heading is not None:
        m['heading'] = round(heading % 360, 1)
    if pose and pose != 'stand':
        m['pose'] = pose
    if tier:
        m['tier'] = tier
    if beats:
        m['beats'] = beats
    return m


def walk_line(start, end, t, pace=None, heading=None, hide=False):
    b = {'t': t, 'walk': [end] if not isinstance(end[0], list) else end}
    if pace: b['pace'] = pace
    if heading is not None: b['heading'] = round(heading % 360, 1)
    if hide: b['hide'] = True
    return b


def offset_path(path, de, dn):
    return [P(p[0] + de, p[1] + dn) for p in path]


# Scenes are filled in below (see SCENES), then written.
sys.path.insert(0, str(Path(__file__).parent))
from scenes import battle, lalime  # noqa: E402  (scenes.py beside this file)


def write(check=False):
    stale = []
    for name, scenes in (('battle-of-fort-dearborn', battle), ('killing-of-jean-lalime', lalime)):
        path = ROOT / f'data/jaunts/{name}.json'
        doc = json.loads(path.read_text())
        built = scenes(sys.modules[__name__])
        for stop in doc['stops']:
            stop.pop('stage', None)
            if stop['id'] in built:
                stage = built[stop['id']]
                for c in stage['cast']:
                    who = c.get('person')
                    if who and not castable(who):
                        raise SystemExit(f'{name}/{stop["id"]}: {who} has no figure in 1812')
                stop['stage'] = {'caption': stage['caption'], 'liberty': LIBERTY, 'cast': stage['cast']}
                if stage.get('teams'):
                    stop['stage']['teams'] = stage['teams']
        if LIBERTY not in doc['liberties']:
            doc['liberties'].append(LIBERTY)
        doc['content_version'] = dev_version(path) + 1
        body = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
        if check:
            if path.read_text() != body: stale.append(rel(path))
        else:
            path.write_text(body)
            print(f'wrote {rel(path)}: {sum(len(s["cast"]) for s in built.values())} castmates on {len(built)} stops')
    if stale:
        raise SystemExit('stale: ' + ', '.join(stale) + '; run build.py')


if __name__ == '__main__':
    write('--check' in sys.argv)
