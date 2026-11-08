# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3463..T-3467: each person of the 1812 town drawn in their own colouring and stature.

The owner, 2026-11-07, of the garrison (T-3491): "they all have the same complexion and hair so
change all that up". The town's day readings (docs/RESEARCH/people-1812-34NN/day.json) give
each person a `looks` block: complexion, hair, eyes, height and build, in words, each graded
with its basis (a portrait or a description where one exists, else heritage and the period).
This script turns those words into the drawn tokens human-looks.js and human-hair-styles.js
know, and writes data/humans/variation/looks/<person>.json for every person place_town.py
draws (tools/human_variation_kit.py then carries them into the persons table).

What it decides, said here (liberty L-1812-town-days-3463):

  * COLOUR WORDS to drawn tokens (COMPLEXION, HAIR, EYES below): the reading's first word
    leads; a range ("fair to ruddy", "olive to light brown") draws its first; "weathered" or
    "sunburnt" on a fair skin draws ruddy; "not recorded" draws the commonest of the
    person's group (light; brown eyes).
  * CUT: a man whose hair the reading says is long, tied or in a queue, and every Potawatomi
    and Miami man ("hair long and tied or clubbed behind", Keating 1824), wears it drawn back
    to the nape; other men a short crop; Potawatomi women theirs parted in the middle and
    tied low behind; other women and girls parted and knotted behind. Faces clean-shaven
    unless the reading says otherwise; women and girls get fine brows and lashes.
  * STATURE: the reading's height in inches over the standing height of the body the person's
    dress is built on (BODY_M), as the variation kit scales it.

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-town/looks.py [--check]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'data/humans/variation/looks'
INST = ROOT / 'data/humans/instances/1812'
READINGS = [ROOT / f'docs/RESEARCH/people-1812-{t}/day.json' for t in (3463, 3464, 3465, 3466, 3467)]
LIBERTY = 'L-1812-town-days-3463'
PREFIX = 'hi_town_'
IN_M = 0.0254

# The standing height of each 1812 role's body (the prepared body's report), metres.
BODY_M = {'adult_male': 1.75, 'adult_female': 1.65, 'child_8': 1.205, 'child_3': 0.905}


def body_of(asset: str) -> str:
    """Which prepared body a role asset is built on, read from the recipe that names it."""
    for r in sorted((ROOT / 'data/humans/recipes').glob('*_1812.json')):
        text = r.read_text()
        if f'"{asset}"' not in text:
            continue
        bodies = set(re.findall(r'prepared_[a-z_0-9]*\.json', text))
        if any('child_3' in b for b in bodies):
            return 'child_3'
        if any('child' in b for b in bodies):
            return 'child_8'
        if any('female' in b for b in bodies):
            return 'adult_female'
        if bodies:
            return 'adult_male'
    raise SystemExit(f'{asset}: no 1812 recipe names it, so its body is unknown')


COMPLEXION = [  # (pattern, drawn), first match wins
    (r'^black\b|african', 'deep_brown'), (r'^dark brown', 'deep_brown'), (r'^brown to dark', 'copper'),
    (r'^brown, a warm', 'copper'), (r'^brown', 'copper'), (r'^light brown', 'tan'), (r'^light olive|^olive', 'olive'),
    (r'^fair,? (?:to )?ruddy|^fair, weathered|^fair, sunburnt|^weathered', 'ruddy'), (r'^fair', 'fair'),
    (r'^light', 'light'), (r'^ruddy', 'ruddy'), (r'^dark', 'dark'),
]
HAIR = [(r'grey|gray', 'grey_brown'), (r'^black|dark brown to black', 'black'), (r'^dark brown|^dark\b', 'dark_brown'),
        (r'^sandy', 'sandy'), (r'^light brown', 'light_brown'), (r'^fair', 'fair'), (r'^red', 'red'), (r'^brown|curly|little|fine', 'mid_brown')]
EYES = [(r'^dark brown|^dark\b|^black', 'dark_brown'), (r'^brown', 'brown'), (r'^hazel', 'hazel'), (r'^grey|blue-grey|grey-blue', 'grey'),
        (r'^blue|blue taken|^light', 'blue')]


def pick(table, words, default):
    w = str(words or '').strip().lower()
    for rx, tok in table:
        if re.search(rx, w):
            return tok
    return default


def main(check=False):
    index = json.loads((INST / 'index.json').read_text())
    drawn = {}
    for iid in index['instances']:
        if iid.startswith(PREFIX):
            r = json.loads((INST / f'{iid}.json').read_text())
            drawn[r['person_id']] = r['appearance']['asset_id']
    want, problems = {}, []
    for path in READINGS:
        d = json.loads(path.read_text())
        native = d['meta']['ticket'] == 'T-3467'
        for p in d['people']:
            pid = p['person_id'].split(':', 1)[-1]
            if pid not in drawn:
                continue
            L = p.get('looks') or {}
            asset = drawn[pid]
            female = (p.get('sex') or '').startswith('f')
            age = (p.get('age_1812') or {}).get('value')
            child = isinstance(age, (int, float)) and age < 15
            comp = pick(COMPLEXION, L.get('complexion'), 'copper' if native else 'light')
            hair = pick(HAIR, L.get('hair'), 'black' if native else 'mid_brown')
            if isinstance(age, (int, float)) and age >= 60 and hair != 'grey_brown':
                hair = 'grey_brown'
            eyes = pick(EYES, L.get('eyes'), 'dark_brown' if native else 'brown')
            long_hair = bool(re.search(r'long|tied|queue|club', str(L.get('hair') or ''), re.I))
            if female:
                cut = 'centre_part_clubbed_1812' if native else 'centre_part_knot_1835'
                facial = ['brows_fine', 'lashes_upper']
            elif native or long_hair:
                cut, facial = 'clubbed_behind_1812', []
            else:
                cut, facial = 'cropped_1812', []
            if re.search(r'side.?whisker', str(L.get('facial_hair') or ''), re.I):
                facial.append('side_whiskers_short')
            body = body_of(asset)
            h_in = L.get('height_in')
            scale = round(float(h_in) * IN_M / BODY_M[body], 4) if isinstance(h_in, (int, float)) else None
            if scale is not None and not (0.8 <= scale <= 1.25):
                problems.append(f'{pid}: {h_in} in on the {body} body is a scale of {scale}')
            grade = L.get('grade') if L.get('grade') in ('attested', 'inferred', 'reconstructed') else 'reconstructed'
            rec = {
                'format': 'chicago4d_human_looks_v1', 'ticket': d['meta']['ticket'], 'person_id': pid, 'scene': '1812',
                'generated_by': 'docs/RESEARCH/people-1812-town/looks.py',
                'heritage': {'origin': 'Potawatomi' if native and 'miami' not in pid else 'Miami' if 'miami' in pid else
                             'not recorded (see the basis)', 'family': 'reading'},
                'complexion': {'value': str(L.get('complexion') or 'not recorded'), 'drawn': comp, 'grade': grade},
                'hair': {'value': str(L.get('hair') or 'not recorded'), 'drawn': hair, 'cut': cut, 'facial': facial, 'grade': grade},
                'eyes': {'value': str(L.get('eyes') or 'not recorded'), 'drawn': eyes, 'grade': grade},
                'stature': {'inches': h_in, 'grade': grade, 'basis': str(L.get('basis') or '')[:600]},
                **({'height_scale': scale} if scale is not None else {}),
                'basis': (f"Drawn in the words of the day reading for {d['meta']['ticket']} "
                          f"(docs/RESEARCH/people-1812-{d['meta']['ticket'][2:]}/day.json): {str(L.get('basis') or '').strip()} "
                          f"The drawn colours, cut and scale are a reconstructed rendering of those words (liberty {LIBERTY})."),
                'grade': grade, 'liberty': LIBERTY,
                'replaceable_by': 'A portrait or a description of them written in their lifetime.',
            }
            if L.get('build'):
                rec['build_words'] = str(L['build'])
            want[f'{pid}.json'] = rec
    stale = []
    for name, rec in want.items():
        text = json.dumps(rec, indent=1, ensure_ascii=False) + '\n'
        path = OUT / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    for old in OUT.glob('*.json'):
        try:
            gen = json.loads(old.read_text()).get('generated_by')
        except ValueError:
            continue
        if gen == 'docs/RESEARCH/people-1812-town/looks.py' and old.name not in want:
            if check:
                stale.append(old.name)
            else:
                old.unlink()
    for p in problems:
        print('  PROBLEM:', p, file=sys.stderr)
    if stale:
        raise SystemExit('stale 1812 town looks (rerun looks.py): ' + ', '.join(stale[:12]))
    print(f'{len(want)} looks of the 1812 town' + (' — current' if check else ' written'))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv))
