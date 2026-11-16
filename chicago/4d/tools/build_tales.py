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
  asks      "Ask a question" (the owner, 2026-11-16: "add ask a question to everyone and give 5
            different options for everyone ... allow one or two follow on questions"):
            [{id, roles, sex?, q, a[], more: [{q, a[]}], meet?}], from docs/RESEARCH/asks-3553
  personal_asks  {person id: [ask]}: what only that person is asked, offered first
  ask_wider {role: {m: [role], f: [role]}}: kindred roles whose questions also suit a person
            whose own roles hold few
  ask_roles {role: count of asks}
  tempers   {code: {name, lines[]}} from docs/RESEARCH/asks-3553/tempers.txt: how a temperament
            comes to an answer ("{He} looks you over before {he} answers.")
  persona   {person id: "temper|topic.topic.topic|who"}: every figure's temperament and what
            they talk about, weighted by their record (the owner, 2026-11-16: "Give everyone a
            unique personality as well their words and perspectives are driven from their
            history"), and a line of who they are from that record; named people's are written
            by hand in asks-3553/<scene>/personas.txt
  Every tale and question carries `k`, its topics (TOPICS below), so a person's temperament and
  history steer which questions they offer and which stories they tell.

A tale is a reconstruction told in the teller's voice, not a source; the liberty is
L-tales-3553 in docs/LIBERTIES.md. Nothing in a tale may postdate its scene's date.

  python3 tools/build_tales.py            write data/tales/*.json
  python3 tools/build_tales.py --check    exit 1 if a written file differs from a rebuild
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'docs/RESEARCH/tales-3553'
ASKS = ROOT / 'docs/RESEARCH/asks-3553'
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


ASK_FIELDS = {'roles', 'for', 'sex', 'meet', 'q'}

# What a tale or a question is about, read from its words: (code, pattern). An item carries the
# (at most three) codes its text matches most.
TOPICS = [
    ('trade', r'\b(lots?|land|dollars?|cents|price|prices|sell|sold|buy|bought|money|rich|store|goods|trade|trader|business|pay|paid|credit|debt|bank|furs?)\b'),
    ('kin', r'\b(child|children|baby|babies|wife|husband|son|daughter|mother|father|brother|sister|family|married|marry|boy|girl)\b'),
    ('home', r'\b(home|miss|missed|letters?|left behind|Ireland|Cork|Kentucky|Vermont|Connecticut|garden|grave|old country)\b'),
    ('faith', r'\b(church|Mass|God|pray|prayers?|priest|minister|Bible|hymns?|sacred|spirits?|blessing|Sunday)\b'),
    ('war', r'\b(soldiers?|fight|fought|war|battle|musket|guns?|army|captain|warriors?|march|garrison|officers?|sentry|powder)\b'),
    ('wild', r'\b(lake|river|prairie|wolf|wolves|fish|fishing|hunt|hunting|deer|ducks|geese|birds?|horses?|corn|marsh|canoe|woods|trees)\b'),
    ('work', r'\b(work|worked|working|trade|wages|hammer|forge|cook|cooking|wash|washing|scrub|build|built|carry|carried|job|shift|tools?)\b'),
    ('fun', r'\b(dance|dancing|danced|fiddle|songs?|sing|singing|game|games|play|played|laugh|laughed|joke|music|party|ball|fun)\b'),
    ('talk', r'\b(news|newspapers?|politics|President|says?|said|told|gossip|talk|talking|everybody|opinion|vote|election)\b'),
    ('past', r'\b(remember|years ago|used to|before the|long ago|old days|when I was|in those days|once)\b'),
    ('dread', r'\b(afraid|fear|frightened|danger|sick|sickness|fever|died|dead|killed|fire|cholera|grave|worst|scared)\b'),
]
TOPIC_RE = [(c, re.compile(p, re.I)) for c, p in TOPICS]


def topics_of(text: str) -> list[str]:
    counts = [(len(r.findall(text)), i, c) for i, (c, r) in enumerate(TOPIC_RE)]
    counts = sorted((x for x in counts if x[0]), key=lambda x: (-x[0], x[1]))
    return [c for _, _, c in counts[:3]]


def parse_tempers(path: Path) -> dict:
    out, cur = {}, None
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('## '):
            cur = out.setdefault(line[3:].strip(), {'lines': []})
        elif cur is None or not line.strip():
            continue
        elif m := re.match(r'^(name|topics):\s*(.*)$', line):
            cur[m.group(1)] = m.group(2).strip()
        else:
            cur['lines'].append(line.strip())
    for code, t in out.items():
        if not t.get('name') or len(t['lines']) < 3:
            raise SystemExit(f'build_tales: temper {code} needs a name and three lines')
        t['topics'] = [x.strip() for x in t.get('topics', '').split(',') if x.strip()]
        bad = [x for x in t['topics'] if x not in dict(TOPICS)]
        if bad:
            raise SystemExit(f'build_tales: temper {code}: unknown topics {bad}')
    return out


def parse_personas(path: Path) -> dict:
    out, cur = {}, None
    if not path.exists():
        return out
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            cur = out.setdefault(line[3:].strip(), {})
        elif cur is not None and (m := re.match(r'^(temper|topics|who):\s*(.*)$', line)):
            cur[m.group(1)] = m.group(2).strip()
    return out


# A figure's temperament leans the way their life leans: {role: [temper, ...]}, picked from by a
# hash of their id, so it is the same on every visit and two neighbours seldom share one.
TEMPER_BY_ROLE = {
    'soldier': ['wary', 'wry', 'gloomy', 'earnest', 'fiery', 'cheerful', 'proud'],
    'officer': ['proud', 'earnest', 'wary', 'shrewd'],
    'militia': ['earnest', 'wary', 'gloomy', 'proud'],
    'settler_man': ['earnest', 'wary', 'wry', 'gloomy', 'proud'],
    'settler_woman': ['earnest', 'wary', 'devout', 'talkative', 'gloomy'],
    'woman': ['earnest', 'wary', 'devout', 'talkative', 'cheerful'],
    'engage': ['cheerful', 'wry', 'dreamy', 'talkative'],
    'household_servant': ['wary', 'shy', 'earnest', 'wry'],
    'miami': ['wary', 'proud', 'earnest', 'gloomy'],
    'potawatomi_man': ['wary', 'proud', 'fiery', 'earnest', 'shrewd', 'wry', 'gloomy', 'dreamy'],
    'potawatomi_woman': ['wary', 'earnest', 'shy', 'proud', 'talkative', 'gloomy', 'devout'],
    'potawatomi_elder': ['gloomy', 'proud', 'earnest', 'devout', 'wry'],
    'potawatomi_child': ['shy', 'cheerful', 'dreamy', 'talkative'],
    'child': ['cheerful', 'shy', 'talkative', 'dreamy', 'fiery'],
    'toddler': ['cheerful', 'shy', 'dreamy'],
    'townsman': ['shrewd', 'cheerful', 'wry', 'talkative', 'proud', 'earnest', 'fiery'],
    'labourer': ['wry', 'cheerful', 'gloomy', 'earnest', 'fiery', 'talkative'],
    'townswoman': ['cheerful', 'earnest', 'talkative', 'wry', 'devout', 'shy', 'proud'],
    'irish': ['wry', 'cheerful', 'devout', 'talkative', 'fiery'],
    'canadien': ['cheerful', 'dreamy', 'talkative', 'proud', 'wry'],
    'metis': ['wary', 'shrewd', 'proud', 'gloomy'],
    'black_resident': ['wary', 'proud', 'earnest', 'wry', 'devout'],
    'mechanic': ['proud', 'earnest', 'wry', 'cheerful', 'shrewd'],
    'merchant': ['shrewd', 'proud', 'talkative', 'cheerful'],
    'professional': ['shrewd', 'proud', 'earnest', 'wry', 'talkative'],
    'clerk': ['shrewd', 'cheerful', 'shy', 'earnest'],
    'innkeeper': ['cheerful', 'talkative', 'shrewd'],
    'boarding_keeper': ['shrewd', 'talkative', 'wry', 'earnest'],
    'domestic': ['wry', 'shy', 'earnest', 'cheerful', 'devout'],
    'laundress': ['wry', 'earnest', 'gloomy', 'cheerful'],
    'needlewoman': ['shrewd', 'talkative', 'earnest', 'proud'],
    'teacher': ['earnest', 'cheerful', 'proud'],
    'youth': ['cheerful', 'dreamy', 'fiery', 'shy', 'talkative'],
    'lady': ['proud', 'earnest', 'talkative', 'shy', 'devout', 'wry'],
    'gentleman': ['shrewd', 'proud', 'earnest', 'wry', 'talkative', 'gloomy'],
    'young_man': ['cheerful', 'fiery', 'dreamy', 'wry', 'proud'],
    'young_lady': ['cheerful', 'dreamy', 'fiery', 'shy', 'wry', 'talkative'],
    'maid': ['shy', 'wry', 'cheerful', 'talkative', 'devout', 'earnest'],
    'cook': ['proud', 'wry', 'talkative', 'fiery', 'earnest'],
    'coachman': ['proud', 'wry', 'earnest', 'gloomy', 'talkative'],
    'laundress_1904': ['wry', 'earnest', 'gloomy'],
    'manservant': ['proud', 'wry', 'earnest', 'shy'],
    'nurse': ['earnest', 'cheerful', 'devout', 'talkative'],
    'housekeeper': ['proud', 'shrewd', 'earnest'],
}
# What a life's work gives a person to talk about, before their temperament adds its own.
TOPICS_BY_ROLE = {
    'soldier': ['war', 'dread'], 'officer': ['war', 'work'], 'militia': ['kin', 'war'],
    'settler_man': ['work', 'kin'], 'settler_woman': ['kin', 'home'], 'woman': ['kin', 'home'],
    'engage': ['wild', 'work'], 'household_servant': ['work', 'kin'], 'miami': ['war', 'past'],
    'potawatomi_man': ['wild', 'war'], 'potawatomi_woman': ['kin', 'wild'], 'potawatomi_elder': ['past', 'faith'],
    'potawatomi_child': ['wild', 'fun'], 'child': ['fun', 'kin'], 'toddler': ['fun', 'kin'],
    'townsman': ['trade', 'talk'], 'labourer': ['work', 'home'], 'townswoman': ['kin', 'home'],
    'irish': ['home', 'faith'], 'canadien': ['past', 'fun'], 'metis': ['past', 'kin'],
    'black_resident': ['work', 'home'], 'mechanic': ['work', 'trade'], 'merchant': ['trade', 'talk'],
    'professional': ['talk', 'trade'], 'clerk': ['trade', 'work'], 'innkeeper': ['fun', 'talk'],
    'boarding_keeper': ['work', 'talk'], 'domestic': ['work', 'kin'], 'laundress': ['work', 'kin'],
    'needlewoman': ['work', 'talk'], 'teacher': ['kin', 'work'], 'youth': ['fun', 'trade'],
    'lady': ['kin', 'talk'], 'gentleman': ['trade', 'talk'], 'young_man': ['fun', 'talk'],
    'young_lady': ['fun', 'kin'], 'maid': ['work', 'home'], 'cook': ['work', 'talk'],
    'coachman': ['wild', 'work'], 'manservant': ['work', 'talk'], 'nurse': ['kin', 'work'],
    'housekeeper': ['work', 'talk'],
}
ORIGIN_1835 = {'yankee': 'A Yankee from New England', 'new_york': 'From New York', 'irish': 'From Ireland',
               'british': 'From Britain', 'french_canadian': 'Of the old French families', 'native': 'Potawatomi',
               'southern': 'From the South', 'metis': 'Of French and Potawatomi family'}


def seeded(pid: str, salt: str) -> int:
    return int(hashlib.md5(f'{pid}:{salt}'.encode()).hexdigest()[:8], 16)


def who_line(scene: str, pid: str, row: dict, person: dict, roles: list, sex: str, age, child: bool) -> str:
    """One line of who this person is, from their record alone."""
    bits = []
    occ = row.get('occupation') or ''
    occ = occ.get('value') if isinstance(occ, dict) else occ
    if scene == '1812':
        facts = {f.get('label'): f.get('value') for f in person.get('card_facts') or [] if isinstance(f, dict)}
        if facts.get('People'):
            band = facts.get('Band')
            band = re.sub(r'^The ', 'the ', band or '')
            bits.append(f"{facts['People']}{', of ' + band if band else ''}")
            if facts.get('Gens'):
                bits.append(f"of the {facts['Gens'].split(' (')[0]} clan")
        elif occ:
            bits.append(occ[0].upper() + occ[1:])
        elif row.get('household_name') and not row['household_name'].startswith('The people of'):
            bits.append(row['household_name'].replace('The ', 'Of the ', 1) if row['household_name'].startswith('The ') else row['household_name'])
    elif scene == '1835':
        origin = next((f.get('value') for f in person.get('profile_facts') or [] if f.get('field') == 'origin'), None)
        com = row.get('community') or ''
        if com == 'free_black':
            bits.append('A free woman of colour' if sex == 'f' else 'A free man of colour')
        elif origin:
            bits.append(f'From {origin}')
        elif ORIGIN_1835.get(com):
            bits.append(ORIGIN_1835[com])
        if occ and occ not in ('none_recorded',):
            bits.append(occ.replace('_', ' '))
        y = row.get('arrival_year')
        if y and not child:
            bits.append('come this year' if y >= 1835 else f'in Chicago since {y}')
        m = re.match(r'The (.+?) household\b', row.get('household_name') or '')
        rel = row.get('relationship') or ''
        if m and not m.group(1).startswith('Reconstructed'):
            name = m.group(1)
            bits.append({'head': f'head of the {name} household', 'wife': f'wife in the {name} household',
                         'son': f'a son of the {name} household', 'daughter': f'a daughter of the {name} household'}
                        .get(rel, f'of the {name} household'))
        elif rel in ('lodger', 'boarder') or 'lodgers' in (row.get('household_name') or ''):
            bits.append('a boarder')
    else:
        note = person.get('note') or ''
        m = re.search(r'born [A-Z][a-z]+ \d{4}[^,.;]*, in ([^,(.;]+?)\s*[,(.;]', note)
        if m:
            bits.append(f'Born in {m.group(1).strip()}')
        hm = re.match(r'The (.+?) household at (.+)$', row.get('household_name') or '')
        house = f'the {hm.group(1)} house at {hm.group(2)}' if hm else ''
        rel = row.get('relationship') or ''
        if occ and rel == 'servant':
            bits.append(f'{occ} in {house}' if house else occ)
        elif occ:
            bits.append(occ)
        if house and rel != 'servant':
            bits.append({'head': f'master of {house}', 'wife': f'mistress of {house}', 'son': f'a son of {house}',
                         'daughter': f'a daughter of {house}'}.get(rel, f'of {house}'))
    if age is not None and child and age >= 1:
        bits.append(f'about {int(round(age))}')
    line = ', '.join(b for b in bits if b)
    return (line[0].upper() + line[1:] + '.') if line else ''


def persona_of(scene, pid, roles, sex, child, age, row, person, tempers, hand):
    if pid in hand:
        h = hand[pid]
        t = h.get('temper') if h.get('temper') in tempers else None
        tops = [x.strip() for x in h.get('topics', '').split(',') if x.strip() in dict(TOPICS)]
        if t and tops:
            return f"{t}|{'.'.join(tops[:3])}|{h.get('who', '')}"
    pool = []
    for r in roles:
        pool += TEMPER_BY_ROLE.get(r, [])
    if (row.get('community') or '') == 'irish':
        pool += TEMPER_BY_ROLE['irish']
    pool = [t for t in pool if t in tempers] or list(tempers)
    temper = pool[seeded(pid, 'temper') % len(pool)]
    other = [t for t in dict.fromkeys(pool + list(tempers)) if t != temper]
    temper = f"{temper}+{other[seeded(pid, 'second') % len(other)]}"
    tops = []
    for r in roles:
        tops += [x for x in TOPICS_BY_ROLE.get(r, []) if x not in tops]
    if scene == '1835' and (row.get('arrival_year') or 0) >= 1835 and 'home' not in tops:
        tops.insert(0, 'home')      # a newcomer talks of where they came from
    if age is not None and age >= 55 and 'past' not in tops:
        tops.insert(0, 'past')      # the old talk of the old days
    lean = [x for x in tempers[temper.split('+')[0]]['topics'] if x not in tops]
    pick = tops[:2]
    if lean:
        pick.append(lean[seeded(pid, 'lean') % len(lean)])
    elif len(tops) > 2:
        pick.append(tops[2])
    return f"{temper}|{'.'.join(pick[:3])}|{who_line(scene, pid, row, person, roles, sex, age, child)}"



def parse_asks(path: Path) -> list[dict]:
    """A file of questions: `## id`, `key: value` lines (q: the question), a blank line, the
    answer's paragraphs, then one or two follow-ups, each a `?? question` line and its answer."""
    out, cur, parts = [], None, []
    def paras(lines):
        return [p for p in (re.sub(r'\s+', ' ', x).strip() for x in '\n'.join(lines).split('\n\n')) if p]
    def close():
        if cur is None:
            return
        cur['a'] = paras(parts[0][1])
        cur['more'] = [{'q': q, 'a': paras(body)} for q, body in parts[1:]]
        out.append(cur)
    head = False
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('## '):
            close()
            cur, parts, head = {'id': line[3:].strip(), '_at': f'{path.name}:{i}'}, [(None, [])], True
            continue
        if cur is None:
            continue
        if head:
            m = re.match(r'^([a-z]+):\s*(.*)$', line)
            if m and m.group(1) in ASK_FIELDS:
                cur[m.group(1)] = m.group(2).strip()
                continue
            if line.strip():
                raise SystemExit(f'{path.name}:{i}: {cur["id"]}: unknown field line {line!r}')
            head = False
            continue
        if line.startswith('?? '):
            parts.append((line[3:].strip(), []))
            continue
        parts[-1][1].append(line)
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
    out, facts = {}, {}
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
        facts[pid] = (roles, sex, child, age, row, person)
    return out, rows, facts


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


# Where a person's own roles hold few questions, the questions of these roles also suit them
# (m, f): kin in life and voice, never another people's.
ASK_WIDER = {
    'settler_man': (['militia', 'engage'], []), 'woman': ([], ['household_servant']),
    'settler_woman': ([], ['household_servant']), 'officer': (['soldier', 'professional'], []),
    'gentleman': (['professional', 'merchant', 'townsman'], ['townswoman']),
    'irish': (['labourer', 'townsman'], ['domestic', 'townswoman']),
    'boarding_keeper': (['townsman'], ['townswoman']), 'needlewoman': ([], ['townswoman', 'lady']),
    'clerk': (['townsman', 'youth'], ['townswoman']), 'innkeeper': (['townsman'], ['townswoman', 'boarding_keeper']),
    'teacher': (['townsman'], ['townswoman']), 'merchant': (['townsman'], ['townswoman']),
    'laundress': (['labourer'], ['domestic', 'townswoman']), 'domestic': ([], ['townswoman']),
    'black_resident': (['labourer', 'townsman'], ['domestic', 'townswoman']),
    'potawatomi_woman': ([], ['potawatomi_elder']), 'young_man': (['gentleman'], []),
    'young_lady': ([], ['lady']), 'manservant': (['coachman'], ['maid']), 'nurse': ([], ['maid']),
    'housekeeper': ([], ['maid', 'cook']), 'cook': ([], ['maid']), 'coachman': (['manservant'], []),
    'metis': (['canadien'], ['canadien']), 'canadien': (['townsman'], ['townswoman']),
    'youth': (['townsman'], ['townswoman']), 'engage': (['settler_man'], []), 'militia': (['settler_man'], []),
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
    asks, personal_asks, seen = [], {}, set()
    for f in [x for x in sorted((ASKS / scene).glob('*.txt')) if x.name != 'personas.txt'] if (ASKS / scene).is_dir() else []:
        for t in parse_asks(f):
            at = t.pop('_at')
            if t['id'] in seen:
                problems.append(f'{at}: {t["id"]} is asked twice')
            seen.add(t['id'])
            if not t.get('q') or not t['a']:
                problems.append(f'{at}: {t["id"]} needs a question (q:) and an answer')
            if not 1 <= len(t['more']) <= 2 or any(not m['q'] or not m['a'] for m in t['more']):
                problems.append(f'{at}: {t["id"]} needs one or two follow-ups, each a ?? question and its answer')
            if not t.get('sex'):
                body = ' '.join([*t['a'], *(' '.join(m['a']) for m in t['more'])])
                wife = re.search(r'\bmy (late )?wife\b', body, re.I)
                husband = re.search(r'\bmy (late )?husband\b', body, re.I)
                if wife and not husband:
                    t['sex'] = 'm'
                elif husband and not wife:
                    t['sex'] = 'f'
            ask = {'id': t['id'], 'q': t.get('q', ''), 'a': t['a'], 'more': t['more']}
            for k in ('sex', 'meet'):
                if t.get(k):
                    ask[k] = t[k]
            if t.get('for'):
                personal_asks.setdefault(t['for'], []).append(ask)
            else:
                roles = [r.strip() for r in t.get('roles', '').split(',') if r.strip()]
                if not roles:
                    problems.append(f'{at}: {t["id"]} names no roles')
                asks.append({'id': ask['id'], 'roles': roles, **ask})
    tell, rows, facts = tellers(scene)
    tell = widen(tell, tales)
    tempers = parse_tempers(ASKS / 'tempers.txt')
    hand = parse_personas(ASKS / scene / 'personas.txt')
    for pid in hand:
        if pid not in rows:
            problems.append(f'personas.txt: {pid} is no one in the {scene} directory')
        h = hand[pid]
        if h.get('temper') not in tempers or not h.get('who'):
            problems.append(f'personas.txt: {pid} needs a known temper and a who line')
    persona = {pid: persona_of(scene, pid, *facts[pid][:2], facts[pid][2], facts[pid][3], *facts[pid][4:], tempers, hand)
               for pid in tell}
    for t in [*tales, *(x for v in personal.values() for x in v)]:
        t['k'] = topics_of(' '.join([t['title'], *t['text']]))
    for t in [*asks, *(x for v in personal_asks.values() for x in v)]:
        t['k'] = topics_of(' '.join([t['q'], *t['a'], *(m['q'] + ' ' + ' '.join(m['a']) for m in t['more'])]))
    for t in [*tales, *(x for v in personal.values() for x in v), *asks,
              *(x for v in personal_asks.values() for x in v)]:
        if t.get('meet'):
            r = rows.get(t['meet'])
            if not r:
                problems.append(f'{t["id"]}: meet {t["meet"]} is no one in the {scene} directory')
            else:
                t['meet'] = {'person': t['meet'], 'name': r['name']}
    for pid in [*personal, *personal_asks]:
        if pid not in rows:
            problems.append(f'personal tales or questions for {pid}, who is no one in the {scene} directory')
    if problems:
        raise SystemExit('build_tales: ' + '\n  '.join(problems))
    roles, ask_roles = {}, {}
    for t in tales:
        for r in t['roles']:
            roles[r] = roles.get(r, 0) + 1
    for t in asks:
        for r in t['roles']:
            ask_roles[r] = ask_roles.get(r, 0) + 1
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
        'ask_roles': dict(sorted(ask_roles.items())),
        'asks': asks,
        'personal_asks': dict(sorted(personal_asks.items())),
        'ask_wider': {r: {'m': m, 'f': f} for r, (m, f) in sorted(ASK_WIDER.items())
                      if any(r in a['roles'] for a in asks) or any(x in a['roles'] for x in m + f for a in asks)},
        'tempers': {k: {'name': v['name'], 'lines': v['lines']} for k, v in sorted(tempers.items())},
        'persona': persona,
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
              f'{len(doc["tellers"])} tellers; {len(doc["asks"])} questions, '
              f'{sum(len(v) for v in doc["personal_asks"].values())} personal for {len(doc["personal_asks"])} people; '
              f'{len(text) / 1024:.0f} KiB')
    return bad


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
