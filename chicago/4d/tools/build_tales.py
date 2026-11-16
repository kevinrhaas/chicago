#!/usr/bin/env python3
"""build_tales.py — the "Tell me a story" library, one file per scene (T-3553).

The owner, 2026-11-16 (thread "Add 'Tell me a story' to every character"): *"For all
characters in all years, add to interactions a tell me a story action, pick a random story
from a personal and if no personal one exisists, pull a story from the story library. The
story library should have hundreds of unique stories so you can interact with lots of people
and not hear the same story twice, it should be relevant to them as a person and their role
and life and maybe even give you some guidance to meet or connect with another person to find
them ... make sure you have enough stories so you can interact say with lots of soldiers and
not hear the same story"*.

Reads the hand-written tales in docs/RESEARCH/tales-3553/<scene>/*.txt and writes
data/tales/<scene>.json, which renderers/web/js/tales.js fetches the first time a visitor
asks someone for a story:

  tales     the library: [{id, roles, sex?, age?, from?, to?, title, text[], meet?}]
  personal  {person id: [tale]}: a named person's own tales, told first
  tellers   {person id: "role,role/sex[/c]"}: every figure the town can draw (the scene's
            instances and the residents its days call out of their doors), with the roles
            whose tales suit them, their sex (from the figure they are drawn as, else their
            record) and /c for a child
  roles     {role: count of tales}, for the gate

A tale is a reconstruction told in the teller's voice, not a source; the liberty is
L-tales-3553 in docs/LIBERTIES.md. Nothing in a tale may postdate its scene's date.

  python3 tools/build_tales.py            write data/tales/*.json
  python3 tools/build_tales.py --check    exit 1 if a written file differs from a rebuild
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'docs/RESEARCH/tales-3553'
OUT = ROOT / 'data/tales'
SCENES = ('1812', '1835', '1904')
FIELDS = {'roles', 'for', 'sex', 'age', 'title', 'meet', 'from', 'to'}

# The figure a person is drawn as says what the visitor sees: a woman's figure tells a
# woman's tale. Asset ids from data/humans/inside_<scene>.json.
FEMALE_ASSET = re.compile(r'woman|girl|flynn_mary|frances|christine|reynolds_mary|ryan_kate|mattie')
CHILD_ASSET = re.compile(r'(^|_)(boy|girl|toddler|child|teen)(_|$)')


def parse(path: Path) -> list[dict]:
    """A file of tales: `## id`, then `key: value` lines, a blank line, then paragraphs."""
    out, cur, body = [], None, []
    def close():
        if cur is None:
            return
        paras = [re.sub(r'\s+', ' ', p).strip() for p in '\n'.join(body).split('\n\n')]
        cur['text'] = [p for p in paras if p]
        out.append(cur)
    lines = path.read_text(encoding='utf-8').splitlines()
    head = False
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            close()
            cur, body, head = {'id': line[3:].strip(), '_at': f'{path.name}:{i}'}, [], True
            continue
        if cur is None:
            continue  # the file's own comment lines
        if head:
            m = re.match(r'^([a-z]+):\s*(.*)$', line)
            if m and m.group(1) in FIELDS:
                cur[m.group(1)] = m.group(2).strip()
                continue
            if line.strip():
                raise SystemExit(f'{path.name}:{i}: {cur["id"]}: unknown field line {line!r}')
            head = False
            continue
        body.append(line)
    close()
    return out


def age_of(person: dict, year: int) -> float | None:
    band = person.get('age_band')
    if isinstance(band, dict) and band.get('low') is not None:
        high = band.get('high')
        return (band['low'] + (band['low'] if high is None else high)) / 2
    born = person.get('born')
    born = born.get('value') if isinstance(born, dict) else born
    m = re.match(r'(\d{4})', str(born or ''))
    return year - int(m.group(1)) if m else None


def sex_of(person: dict) -> str | None:
    s = person.get('sex')
    s = s.get('value') if isinstance(s, dict) else s
    return {'male': 'm', 'female': 'f'}.get(s)


def households(scene: str) -> dict:
    root = ROOT / ('data/residents/households' if scene == '1835' else f'data/residents_{scene}/households')
    persons = {}
    for f in sorted(root.glob('*.json')):
        doc = json.loads(f.read_text(encoding='utf-8'))
        for p in doc.get('persons', []):
            persons[p['id']] = p
    return persons


def drawable(scene: str) -> dict:
    """Everyone the town can draw: {person id: asset id or None}."""
    out = {}
    for f in sorted((ROOT / f'data/humans/instances/{scene}').glob('hi_*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        if d.get('person_id'):
            out[d['person_id']] = (d.get('appearance') or {}).get('asset_id')
    inside = json.loads((ROOT / f'data/humans/inside_{scene}.json').read_text(encoding='utf-8'))
    for x in inside.get('people', []):
        out.setdefault(x['person'], x.get('asset_id'))
    return out, {x['person']: x for x in inside.get('people', [])}


# ---- who tells which tales ----------------------------------------------------------- #

def roles_1812(row, person, sex, age, child):
    occ = (row.get('occupation') or '').lower()
    rel = row.get('relationship') or ''
    hh = row.get('household') or ''
    if re.search(r'captain|lieutenant|ensign|surgeon', occ):
        return ['officer', 'soldier']
    if rel == 'soldier' or "heald's company" in occ:
        return ['soldier']
    if rel == 'militiaman' or 'militia' in occ:
        return ['militia', 'settler_man']
    if rel in ('enslaved', 'servant'):
        return ['child', 'household_servant'] if child else ['household_servant']
    if 'miami' in hh:
        return ['miami']
    if rel in ('employee', 'clerk'):
        return ['engage', 'settler_man']
    native = row.get('division') == 'camp' or (row.get('grade') == 'attested' and not row.get('occupation')
                                                and hh.replace('hh_', '').replace('_1812', '') in NATIVE_1812)
    if native:
        if child:
            return ['potawatomi_child']
        if age is not None and age >= 55:
            return ['potawatomi_elder', 'potawatomi_woman' if sex == 'f' else 'potawatomi_man']
        return ['potawatomi_woman'] if sex == 'f' else ['potawatomi_man']
    if child:
        return ['child']
    if sex == 'f':
        return ['woman', 'settler_woman']
    return ['settler_man']


NATIVE_1812 = {'black_partridge', 'blackbird', 'keepotah', 'naunongee', 'nuscotnemeg', 'peesotum', 'shabbona',
               'topenebe', 'waubansee', 'waubeeneemah', 'winnemeg', 'main_poc_runner', 'caldwell_billy', 'robinson_alexander'}

TRADE_1835 = {'carpenter', 'builder', 'mason', 'brickmaker', 'blacksmith', 'tailor', 'shoemaker', 'cooper', 'sawyer',
              'cabinetmaker', 'painter', 'wheelwright', 'joiner', 'saddler', 'harness_maker', 'tinsmith', 'gunsmith',
              'plasterer', 'chairmaker', 'watchmaker', 'silversmith', 'bricklayer', 'stonecutter', 'millwright', 'hatter'}
MERCHANT_1835 = {'merchant', 'grocer', 'hardware_merchant', 'dry_goods_merchant', 'forwarding_and_commission',
                 'lumber_merchant', 'clothier', 'druggist', 'auctioneer', 'trader', 'baker', 'butcher', 'packer',
                 'commission_merchant', 'jeweller', 'bookseller', 'confectioner', 'storekeeper'}
LEARNED_1835 = {'attorney', 'land_agent', 'justice_of_the_peace', 'county_clerk', 'surveyor', 'postmaster', 'editor',
                'printer', 'insurance_agent', 'physician', 'banker', 'clergyman', 'minister', 'interpreter', 'army_officer'}


def roles_1835(row, person, sex, age, child, routine):
    occ = row.get('occupation') or ''
    com = row.get('community') or ''
    if com == 'native':
        if child:
            return ['potawatomi_child']
        return ['potawatomi_woman'] if sex == 'f' else ['potawatomi_man']
    if child:
        return ['child']
    if occ == 'army_officer':
        return ['officer', 'gentleman']
    if occ == 'soldier':
        return ['soldier']
    if com == 'metis' or occ == 'interpreter':
        return ['metis', 'canadien']
    out = []
    if com == 'free_black':
        out.append('black_resident')
    if occ in ('domestic',):
        out.append('domestic')
    elif occ == 'laundress':
        out += ['laundress', 'domestic']
    elif occ in ('dressmaker', 'milliner', 'seamstress'):
        out.append('needlewoman')
    elif occ == 'boarding_house_keeper':
        out.append('boarding_keeper')
    elif occ in ('hotel_keeper', 'tavern_keeper', 'refectory_keeper'):
        out.append('innkeeper')
    elif occ == 'clerk':
        out.append('clerk')
    elif occ in MERCHANT_1835:
        out.append('merchant')
    elif occ in LEARNED_1835:
        out.append('professional')
    elif occ in TRADE_1835:
        out.append('mechanic')
    elif occ in ('labourer', 'teamster', 'boatman', 'farmer'):
        out.append('labourer')
    elif occ == 'schoolteacher':
        out.append('teacher')
    elif occ:
        out.append('mechanic' if sex != 'f' else 'townswoman')
    if com == 'irish':
        out.append('irish')
    if com == 'french_canadian':
        out.append('canadien')
    if not out or out == ['irish'] or out == ['canadien'] or out == ['black_resident']:
        out += {'gentleman': ['gentleman'], 'lady': ['lady', 'townswoman'], 'woman': ['townswoman'],
                'woman_trade': ['needlewoman', 'townswoman'], 'laundress': ['laundress'], 'domestic': ['domestic'],
                'keeper': ['innkeeper', 'boarding_keeper'] if sex == 'f' else ['innkeeper'],
                'tradesman': ['mechanic'], 'lad': ['youth', 'townsman'], 'girl': ['youth', 'townswoman'],
                'soldier': ['soldier']}.get(routine, ['townswoman'] if sex == 'f' else ['townsman', 'labourer'])
    if sex == 'f':
        out = [r for r in out if r not in ('labourer', 'townsman', 'mechanic', 'gentleman')] or ['townswoman']
    else:
        out = [r for r in out if r not in ('townswoman', 'lady', 'needlewoman', 'domestic', 'laundress', 'boarding_keeper')] or ['townsman']
    return list(dict.fromkeys(out))


def roles_1904(row, person, sex, age, child):
    occ = (row.get('occupation') or '').lower()
    rel = row.get('relationship') or ''
    if child:
        return ['child']
    if re.search(r'nurse|governess|companion', occ):
        return ['nurse']
    if re.search(r'cook', occ):
        return ['cook', 'maid'] if 'waitress' in occ else ['cook']
    if re.search(r'coachman|groom|horse|stable', occ):
        return ['coachman']
    if 'laundress' in occ:
        return ['laundress', 'maid']
    if 'housekeeper' in occ:
        return ['housekeeper', 'maid']
    if re.search(r'maid|waitress', occ):
        return ['maid']
    if re.search(r'butler|footman|valet|steward|helper', occ):
        return ['manservant']
    if rel == 'servant':
        return ['maid'] if sex == 'f' else ['manservant']
    if rel in ('son', 'daughter'):
        return ['young_lady'] if sex == 'f' else ['young_man']
    return ['lady'] if sex == 'f' else ['gentleman']


def tellers(scene: str) -> dict:
    year = int(scene)
    rows = {p['id']: p for p in json.loads((ROOT / f'data/sidecars/{scene}/people.json').read_text(encoding='utf-8'))['people']}
    persons = households(scene)
    figures, inside = drawable(scene)
    out = {}
    for pid in sorted(figures):
        row, person, asset = rows.get(pid, {}), persons.get(pid, {}), figures[pid] or ''
        neutral = bool(asset) and not FEMALE_ASSET.search(asset) and re.search(r'(^|_)(child|toddler)(_|$)', asset)
        sex = ('f' if FEMALE_ASSET.search(asset) else 'm') if asset and not neutral else sex_of(person)
        if sex is None:
            name, rel = row.get('name', ''), row.get('relationship', '')
            sex = 'f' if re.match(r'(Mrs\.|Miss)', name) or rel in ('wife', 'daughter') else 'm'
        age = age_of(person, year)
        child = bool(asset and CHILD_ASSET.search(asset) and 'teen' not in asset) if asset else (
            age is not None and age < 14 or row.get('relationship') in ('child', 'children') and (age is None or age < 14))
        if scene == '1812':
            roles = roles_1812(row, person, sex, age, child)
        elif scene == '1835':
            roles = roles_1835(row, person, sex, age, child, inside.get(pid, {}).get('routine'))
        else:
            roles = roles_1904(row, person, sex, age, child)
        if age is not None and age < 4:
            roles, child = ['toddler'], True  # a little one tells a little story
        out[pid] = f"{','.join(roles)}/{sex}{'/c' if child else ''}"
    return out, rows


# A teller whose roles hold fewer than POOL_MIN tales also draws on a wider role of their
# town, so that a man in a small trade still has many stories to tell (m, f).
POOL_MIN = 12
# A figure the builder did not know tells the town's common stories.
FALLBACK = {'1812': {'m': 'settler_man', 'f': 'woman'}, '1835': {'m': 'townsman', 'f': 'townswoman'},
            '1904': {'m': 'gentleman', 'f': 'lady'}}
WIDER = {
    'household_servant': ('settler_man', 'woman'), 'teacher': ('townsman', 'townswoman'),
    'innkeeper': ('townsman', 'townswoman'), 'boarding_keeper': ('townsman', 'townswoman'),
    'needlewoman': ('townsman', 'townswoman'), 'domestic': ('labourer', 'townswoman'),
    'laundress': ('labourer', 'townswoman'), 'officer': ('gentleman', 'lady'),
    'nurse': ('manservant', 'maid'), 'cook': ('manservant', 'maid'), 'coachman': ('manservant', 'maid'),
    'housekeeper': ('manservant', 'maid'), 'professional': ('townsman', 'townswoman'),
    'clerk': ('townsman', 'townswoman'),
}


def widen(tell: dict, tales: list) -> dict:
    def pool(roles, sex):
        return sum(1 for t in tales if set(t['roles']) & roles and t.get('sex', sex) == sex)
    out = {}
    for pid, key in tell.items():
        roles, sex, *rest = key.split('/')
        have = roles.split(',')
        if pool(set(have), sex) < POOL_MIN:
            for r in list(have):
                extra = WIDER.get(r, (None, None))[0 if sex == 'm' else 1]
                if extra and extra not in have and any(extra in t['roles'] for t in tales):
                    have.append(extra)
        out[pid] = '/'.join([','.join(have), sex, *rest])
    return out


def build(scene: str) -> dict:
    src = SRC / scene
    tales, personal, problems = [], {}, []
    for f in sorted(src.glob('*.txt')):
        for t in parse(f):
            at = t.pop('_at')
            if not t.get('title') or not t.get('text'):
                problems.append(f'{at}: {t["id"]} needs a title and a story')
            # A teller who speaks of "my wife" is a man, of "my husband" a woman, unless the tale says.
            if not t.get('sex'):
                body = ' '.join(t['text'])
                if re.search(r'\bmy (late )?wife\b', body, re.I) and not re.search(r'\bmy (late )?husband\b', body, re.I):
                    t['sex'] = 'm'
                elif re.search(r'\bmy (late )?husband\b', body, re.I) and not re.search(r'\bmy (late )?wife\b', body, re.I):
                    t['sex'] = 'f'
            tale = {'id': t['id'], 'title': t['title'], 'text': t['text']}
            for k in ('sex', 'age', 'from', 'to'):
                if t.get(k):
                    tale[k] = t[k]
            if t.get('meet'):
                tale['meet'] = t['meet']
            if t.get('for'):
                personal.setdefault(t['for'], []).append(tale)
            else:
                tale['roles'] = [r.strip() for r in t.get('roles', '').split(',') if r.strip()]
                if not tale['roles']:
                    problems.append(f'{at}: {t["id"]} names no roles')
                tales.append({'id': tale['id'], 'roles': tale.pop('roles'), **tale})
    tell, rows = tellers(scene)
    tell = widen(tell, tales)
    for t in [*tales, *(x for v in personal.values() for x in v)]:
        if t.get('meet'):
            r = rows.get(t['meet'])
            if not r:
                problems.append(f'{t["id"]}: meet {t["meet"]} is no one in the {scene} directory')
            else:
                t['meet'] = {'person': t['meet'], 'name': r['name']}
    for pid in personal:
        if pid not in rows:
            problems.append(f'personal tales for {pid}, who is no one in the {scene} directory')
    if problems:
        raise SystemExit('build_tales: ' + '\n  '.join(problems))
    roles = {}
    for t in tales:
        for r in t['roles']:
            roles[r] = roles.get(r, 0) + 1
    return {
        '_doc': ('The "Tell me a story" library for this scene (T-3553): tales told in the voice of the person asked, '
                 'their own first (personal), else from the library by their roles (tellers). Written by '
                 'tools/build_tales.py from docs/RESEARCH/tales-3553; a reconstruction, liberty L-tales-3553.'),
        'scene': scene,
        'liberty': 'L-tales-3553',
        'roles': dict(sorted(roles.items())),
        'tales': tales,
        'personal': dict(sorted(personal.items())),
        'tellers': tell,
        'fallback': FALLBACK[scene],
    }


def main(argv):
    check = '--check' in argv
    bad = 0
    OUT.mkdir(parents=True, exist_ok=True)
    for scene in SCENES:
        if not (SRC / scene).is_dir():
            continue
        doc = build(scene)
        text = json.dumps(doc, ensure_ascii=False, separators=(',', ':')) + '\n'
        path = OUT / f'{scene}.json'
        if check:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                print(f'build_tales: {path.relative_to(ROOT)} differs from a rebuild; run python3 tools/build_tales.py')
                bad = 1
            continue
        path.write_text(text, encoding='utf-8')
        n_personal = sum(len(v) for v in doc['personal'].values())
        print(f'{scene}: {len(doc["tales"])} library tales, {n_personal} personal for {len(doc["personal"])} people, '
              f'{len(doc["tellers"])} tellers, {len(text) / 1024:.0f} KiB')
    return bad


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
