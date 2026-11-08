# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3491: each man of Heald's company looks like himself — complexion, hair, eyes, stature.

The owner, 2026-11-07, of the T-3462 soldiers: "they all look the same? ... if we dont have a
photo we should use their ethnicity and find an image of someone like that and use that as a
basis ... they might vary a bit in height and build and they all have the same complexion and
hair so change all that up". Until this every drawn man shared one skin, one mid-brown crop
and one eye colour; only the face, height and build were seeded (T-3412).

WHAT IS READ (reading.json beside this script; every number has its source and quote):
  * No man's own enlistment description (the Register of Enlistments, NARA M233, gives each
    recruit's height, complexion, eyes and hair) could be reached: the 1798-1815 volumes are
    transcribed only behind Ancestry / Fold3 / FamilySearch logins. So nobody's colouring is
    attested. Two men have something of their own: Paul Grummo, "a tall, well-built man" (a
    neighbour's memory, Quaife 1913 p. 239), and David Kennison, "about five feet ten inches"
    with "an expansive chest and broad shoulders" (Lossing, measured c. 1848, in old age).
  * The period's own mix of what the registers wrote: 199 men of the 22nd US Infantry, mostly
    Pennsylvania-born, transcribed from M233 (the closer analogue for a pre-war company raised
    in the middle states and the Ohio valley), and 739 army men of the Maine 1812 database.
  * Stature: 68.1 in, the mean of native-born US Army recruits of 1815-20 aged 24-35 (n=2,163;
    Sokoloff 1984 after Sokoloff & Villaflor 1982); the spread, 2.5 in, from the two register
    samples (2.54 in, n=354; 2.44 in, n=171).
  * Each surname's origin, from a surname dictionary (reading.json `surnames`).
  * Eight public-domain colour portraits of young American men of c. 1810-1825 (The Met).

WHAT IS OURS (liberty L-1812-garrison-looks-3491):
  * Each man's complexion, hair colour and eye colour are DRAWN, seeded by his id, from the
    22nd Infantry register mix (the register's words kept: fair, light, dark, ruddy, brown).
    His name's origin leans the draw a little: a Scottish, Ulster or Irish name doubles the
    chance of sandy and triples that of red hair; a Welsh or French name leans dark; a Dutch
    name leans fair. The leaning is our choice, not a measured rate.
  * His stature is drawn from 68.1 in, sd 2.5 in, clipped to 62-75 in; Grummo's is put tall
    (71-74 in) and his build heavier, Kennison's at 70 in.
  * The portrait shown on his card is the one of the eight whose colouring is nearest his:
    a STAND-IN, a period face of like colouring, never his likeness.
  * Every man wears his hair cropped short, and about two in five short side whiskers; chins
    shaved. Our choice for soldiers of the time; no regulation is cited for it here.

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-3491/looks.py [--check]
Then python3 tools/human_variation_kit.py (it carries each looks file into the persons table).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'data/humans/variation/looks'
INST = ROOT / 'data/humans/instances/1812'
LIBERTY = 'L-1812-garrison-looks-3491'
ASSET = 'private_first_infantry_1812'
ENGINEERING_IN = 68.9          # the shared hm08 body stands 1.75 m


def rng(key: str):
    """FNV-1a into mulberry32, as renderers/web/js/human-variation.js seeds."""
    h = 2166136261
    for ch in key:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    a = h or 1

    def r():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return r


def pick(r, weights: dict[str, float]) -> str:
    tot = sum(weights.values())
    x = r() * tot
    for k, w in weights.items():
        x -= w
        if x <= 0:
            return k
    return k


def gauss(r):
    u, v = max(r(), 1e-12), r()
    return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


def family(origin: str) -> str:
    o = origin.lower()
    if 'dutch' in o:
        return 'dutch'
    if 'french origin via' in o:
        return 'french'
    if any(w in o for w in ('scottish', 'ulster', 'irish', 'scots')):
        return 'gaelic'
    if o.startswith('welsh'):
        return 'welsh'
    return 'english'


LEAN = {
    'gaelic': {'hair': {'sandy': 2, 'red': 3, 'fair': 1.3}, 'complexion': {'fair': 1.2, 'ruddy': 1.5}},
    'welsh': {'hair': {'black': 1.3, 'dark': 1.3}, 'complexion': {'dark': 1.2}},
    'french': {'hair': {'black': 1.4, 'dark': 1.3}, 'complexion': {'dark': 1.3}},
    'dutch': {'hair': {'fair': 1.4, 'light': 1.4}, 'complexion': {'fair': 1.2}},
    'english': {},
}
FAMILY_WORDS = {'gaelic': 'a Scottish, Ulster or Irish', 'welsh': 'a Welsh', 'french': 'a French', 'dutch': 'a Dutch'}
# The register's hair words, and the colour the renderer draws for each (human-hair-styles.js).
HAIR_DRAWN = {'black': 'black', 'dark': 'dark_brown', 'brown': 'mid_brown', 'light': 'light_brown',
              'fair': 'fair', 'sandy': 'sandy', 'red': 'red'}
EYES_DRAWN = {'blue': 'blue', 'grey': 'grey', 'hazel': 'hazel', 'brown': 'brown', 'dark': 'dark_brown', 'black': 'dark_brown'}
COMPLEXION_DRAWN = {'fair': 'fair', 'light': 'light', 'dark': 'dark', 'ruddy': 'ruddy', 'brown': 'brown'}
# Colouring of each stand-in portrait, as read (reading.json `portraits`): hair, complexion.
PORTRAIT_COLOURING = {
    'Henry Rice': ('red', 'ruddy'), 'Alexander Anderson': ('black', 'dark'), 'Self-portrait|Joseph Wood': ('brown', 'fair'),
    'Mr. Cook': ('light', 'fair'), 'Self-portrait|Samuel Lovett Waldo': ('dark', 'ruddy'),
    'Portrait of the Artist': ('sandy', 'fair'), 'Henry La Tourette de Groot': ('black', 'fair'),
}
HAIR_NEAR = {'black': 0, 'dark': 1, 'brown': 2, 'light': 3, 'fair': 4, 'sandy': 4.2, 'red': 5}
SKIN_NEAR = {'fair': 0, 'light': 0.5, 'ruddy': 0.8, 'brown': 1.6, 'dark': 2}


def main(check=False):
    reading = json.loads((HERE / 'reading.json').read_text())
    br = reading['base_rates']
    s22 = {k: br[k]['inf22_sample']['counts'] for k in ('complexion', 'eyes', 'hair')}
    hair_w = {'black': s22['hair']['black'], 'dark': s22['hair']['dark'], 'brown': s22['hair']['brown'],
              'light': s22['hair']['light'], 'fair': s22['hair']['fair'], 'sandy': s22['hair']['sandy'], 'red': s22['hair']['red']}
    eyes_w = {'blue': s22['eyes']['blue'], 'grey': s22['eyes']['grey/gray'], 'hazel': s22['eyes']['hazel'],
              'brown': s22['eyes']['brown'], 'dark': s22['eyes']['dark'], 'black': s22['eyes']['black']}
    comp_w = {k: s22['complexion'][k] for k in ('fair', 'light', 'dark', 'ruddy', 'brown')}
    portraits = []
    for p in reading['portraits']:
        key = p['title'] if p['title'] in PORTRAIT_COLOURING else f"{p['title']}|{p['artist'].split(' (')[0]}"
        if key in PORTRAIT_COLOURING:
            portraits.append((PORTRAIT_COLOURING[key], p))
    men = sorted({json.loads(f.read_text())['person_id'] for f in INST.glob('hi_*.json')
                  if json.loads(f.read_text())['appearance']['asset_id'] == ASSET})
    files = {}
    for pid in men:
        r = rng(f'looks:{pid}:1812')
        sur = reading['surnames'].get(pid, {})
        fam = family(sur.get('origin', 'english'))
        lean = LEAN[fam]
        hw = {k: v * lean.get('hair', {}).get(k, 1) for k, v in hair_w.items()}
        cw = {k: v * lean.get('complexion', {}).get(k, 1) for k, v in comp_w.items()}
        hair, comp, eyes = pick(r, hw), pick(r, cw), pick(r, eyes_w)
        inches = min(75, max(62, 68.1 + gauss(r) * 2.5))
        whiskers = r() < 0.4
        stature = {'inches': round(inches, 1), 'grade': 'reconstructed',
                   'basis': 'Drawn from the stature of US Army recruits of 1815-20, 68.1 in on average (Sokoloff 1984), with the 2.5 in spread of the period\'s registers; no measure of him is known.'}
        build = None
        if pid == 'grummo_paul':
            stature = {'inches': round(71 + r() * 3, 1), 'grade': 'inferred',
                       'basis': 'A neighbour remembered him as "a tall, well-built man" (Quaife 1913, p. 239); how tall is our choice, a little over the period\'s tall.'}
            build = {'weight': 0.35, 'muscle': 0.35, 'grade': 'inferred', 'basis': 'Well-built, as the same neighbour remembered him.'}
        elif pid == 'kennison_david':
            stature = {'inches': 70.0, 'grade': 'inferred',
                       'basis': 'Lossing, who met him about 1848, gives him "about five feet ten inches" with "an expansive chest and broad shoulders" — a measure of his old age, taken here for 1812.'}
            build = {'weight': 0.15, 'muscle': 0.3, 'grade': 'inferred', 'basis': 'Broad-shouldered and deep-chested, as Lossing describes him.'}
        near = min(portraits, key=lambda cp: abs(HAIR_NEAR[cp[0][0]] - HAIR_NEAR[hair]) + abs(SKIN_NEAR[cp[0][1]] - SKIN_NEAR[comp]))
        pic = near[1]
        rec = {
            'format': 'chicago4d_human_looks_v1', 'ticket': 'T-3491', 'person_id': pid, 'scene': '1812',
            'generated_by': 'docs/RESEARCH/people-1812-3491/looks.py',
            'heritage': {'origin': sur.get('origin', 'not found'), 'family': fam, 'source_title': sur.get('source_title'),
                         'url': sur.get('url')},
            'complexion': {'value': comp, 'drawn': COMPLEXION_DRAWN[comp], 'grade': 'reconstructed'},
            'hair': {'value': hair, 'drawn': HAIR_DRAWN[hair], 'cut': 'cropped_1812', 'facial': ['side_whiskers_short'] if whiskers else [],
                     'grade': 'reconstructed'},
            'eyes': {'value': eyes, 'drawn': EYES_DRAWN[eyes], 'grade': 'reconstructed'},
            'stature': stature,
            'height_scale': round(stature['inches'] / ENGINEERING_IN, 4),
            'basis': (f"His complexion ({comp}), hair ({hair}) and eyes ({eyes}) are drawn in the register's own words from what the "
                      "Register of Enlistments wrote of 199 men of the 22nd US Infantry, 1812-14"
                      + (f", with the lean we give {FAMILY_WORDS[fam]} name" if fam != 'english' else '')
                      + "; his own entry has not been read. The short crop is our choice for a soldier of the time."),
            'reference': {'title': pic['title'], 'artist': pic['artist'], 'date': pic['date'], 'page_url': pic['page_url'],
                          'image': f"humans/web/portraits/ref_1812_{pic['accession'].replace('.', '_')}.jpg",
                          'licence': 'The Met Open Access, public domain',
                          'why': f"A stand-in: a period face of like colouring ({pic.get('hair_as_seen', '')}; {pic.get('complexion_as_seen', '')}), not his likeness."},
            'grade': 'reconstructed', 'liberty': LIBERTY,
            'replaceable_by': 'His entry in the Register of Enlistments (NARA M233), which gives his height, complexion, eyes and hair.',
        }
        if build:
            rec['build'] = build
        files[f'{pid}.json'] = rec
    stale = []
    for name, rec in files.items():
        text = json.dumps(rec, indent=1, ensure_ascii=False) + '\n'
        p = OUT / name
        if check:
            if not p.exists() or p.read_text() != text:
                stale.append(name)
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
    if stale:
        raise SystemExit('stale 1812 looks (rerun looks.py): ' + ', '.join(stale))
    print(f'{len(files)} men of Heald\'s company: looks ' + ('current' if check else 'written'))
    return files


if __name__ == '__main__':
    main(check='--check' in sys.argv)
