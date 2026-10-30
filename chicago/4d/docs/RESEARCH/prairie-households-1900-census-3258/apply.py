import json, re, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from spec import SPEC, OTHER_FAMILY

ROOT = Path(__file__).resolve().parents[3]
HH = ROOT / 'data/residents_1904/households'
SRC = 'census_1900_chicago_t623_roll245'
TSV = Path(sys.argv[1])

MONTHS = {'jan': 'January', 'feb': 'February', 'mar': 'March', 'mch': 'March', 'apr': 'April', 'april': 'April', 'may': 'May',
          'june': 'June', 'jun': 'June', 'july': 'July', 'jul': 'July', 'aug': 'August', 'sep': 'September', 'sept': 'September',
          'oct': 'October', 'nov': 'November', 'dec': 'December'}
STAFF_REL = {'Servant', 'Butler', 'Companion', 'Helper'}
STABLE = ('coachman', 'groom', 'horseman', 'stableman', 'footman', 'helper')

rows = []
for line in TSV.read_text().splitlines():
    if line.startswith('#') or not line.strip():
        continue
    f = line.split('\t') + [''] * 14
    leaf, ed, sheet, ln, house, name, rel, sex, birth, age, mar, bp, occ, note = f[:14]
    rows.append(dict(leaf=leaf, ed=ed, sheet=sheet, line=ln, house=house, name=name, rel=rel, sex=sex, birth=birth,
                     age=age, marital=mar, bp=bp, occ=occ, note=note))

def base(h):
    m = re.match(r'(?:Rear\s+)?(\d+)', h)
    return m.group(1) if m else ''

def is_rear(h):
    return h.startswith('Rear') or '(dw.2)' in h or h.endswith(' R') or ' R?' in h

def clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'\[.*?\]|\?|\(.*?\)', '', s)).strip(' ,')

def display(name):
    if ',' in name:
        sur, given = name.split(',', 1)
    else:
        sur, given = name, ''
    sur, given = clean(sur), clean(given)
    given = re.sub(r'\b(Mr|Mrs|Miss)\.?$', '', given).strip()
    jr = ''
    m = re.search(r'\s*\bJr\.?$', given)
    if m:
        given, jr = given[:m.start()].strip(), ' Jr.'
    given = re.sub(r'\b([A-Z])\b(?!\.)', r'\1.', given)
    return f'{given} {sur}{jr}'.strip()

def doubtful(r):
    return '?' in r['name']

def locator(r):
    return f"ED {r['ed']}, sheet {r['sheet']}, line {r['line']}, leaf n{r['leaf']}"

def birth_text(r):
    b = r['birth'].replace('?', '').strip()
    if not b or b.lower() in ('unknown',):
        return None, None
    parts = b.split()
    yr = parts[-1] if parts and parts[-1].isdigit() else None
    mo = MONTHS.get(parts[0].lower().rstrip('.')) if len(parts) > 1 else None
    return (f'{mo} {yr}' if mo else yr), yr

def slug(s):
    s = re.sub(r"[^a-z0-9]+", '_', s.lower()).strip('_')
    return s

def describe(r):
    bits = []
    bt, _ = birth_text(r)
    if bt:
        bits.append(f"born {bt}{' (the figures are hard to read)' if '?' in r['birth'] or '?' in r['age'] else ''}")
    if r['bp'] and r['bp'] not in ('?', '(blank)') and 'ditto' not in r['bp'] and not r['bp'].startswith('('):
        bits.append(f"in {r['bp'].replace('?', '')}{' (as read)' if '?' in r['bp'] else ''}")
    m = re.search(r'imm (\d{4})', r['note'])
    if m:
        bits.append(f'came to the United States in {m.group(1)}')
    if r['marital'] in ('Wd',):
        bits.append('widowed')
    elif r['marital'] == 'M':
        bits.append('married')
    elif r['marital'] == 'S':
        try:
            young = int(re.sub(r'\D', '', r['age']) or 99) < 16
        except ValueError:
            young = False
        if not young:
            bits.append('single')
    return ', '.join(bits)

def occ_value(r):
    o = r['occ'].replace('?', '').strip()
    if not o or o.startswith('(') or o.lower() == 'servant':
        return None
    o = o.replace('Nurse (children\'s)', 'Nurse (children)')
    return o[0].lower() + o[1:]


WORDS = {2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}
OLD_SENT = ("A house of this kind kept live-in staff, and the 1900 and 1910 censuses name them; neither was read for "
            "this card, so no staff are listed.")
GLESSNER_OLD = "The 1900 and 1910 censuses would name the rest and were not read for this card."

def set_census_sentence(card, msg, staff_n=0):
    nih = card['not_in_this_household']
    note = nih['note']
    if OLD_SENT in note:
        note = note.replace(OLD_SENT, msg)
    elif GLESSNER_OLD in note:
        note = note.replace("Of the household staff only the cook is here.",
                            f"Of the household staff the cook is here, with {WORDS.get(staff_n, staff_n)} more the 1900 census lists.")
        note = note.replace(GLESSNER_OLD, msg)
    else:
        raise SystemExit(f"{card['id']}: no census sentence to replace")
    nih['note'] = note
    if SRC not in nih['sources']:
        nih['sources'].append(SRC)

cards = {}
for p in HH.glob('hh_*.json'):
    cards[p.stem] = (p, json.loads(p.read_text()))

by_house = collections.defaultdict(list)
for r in rows:
    by_house[base(r['house'])].append(r)

touched, added, enriched = set(), collections.Counter(), collections.Counter()
used_ids = {pp['id'] for _, d in cards.values() for pp in d['persons']}

def new_id(stem, r):
    fam = stem.replace('hh_', '')
    nm = display(r['name'])
    pid = f"pa1904_{fam}_c1900_{slug(nm)}"
    i = 2
    while pid in used_ids:
        pid = f"pa1904_{fam}_c1900_{slug(nm)}_{i}"; i += 1
    used_ids.add(pid)
    return pid

def seen(r):
    return {'date': '1900-06-01', 'source': SRC, 'locator': locator(r), 'as_enumerated': r['name'].replace('?', '').strip(),
            'relation_as_enumerated': r['rel']}

def key_for(r, mapping):
    for k in (f"{r['name']}|{r['rel']}", r['name']):
        if k in mapping:
            return k
    return None

report = []
for house, rs in sorted(by_house.items()):
    if house not in SPEC:
        continue
    stem, enrich, skip, add = SPEC[house]
    path, card = cards[stem]
    persons = card['persons']
    by_id = {pp['id']: pp for pp in persons}
    rear_family = collections.defaultdict(list)
    # group rear dwellings: the head of each rear family collects the rest
    cur = None
    for r in rs:
        if is_rear(r['house']):
            if r['rel'] == 'Head':
                cur = r
            elif cur is not None:
                rear_family[id(cur)].append(r)
        else:
            cur = None
    new = []
    for r in rs:
        k_enrich = key_for(r, enrich)
        k_add = next((a for a in add if a in (r['name'], f"{r['name']}|{r['rel']}")), None)
        k_skip = key_for(r, skip)
        rear = is_rear(r['house'])
        if k_enrich:
            pp = by_id[enrich[k_enrich]]
            if SRC not in pp['sources']:
                pp['sources'].append(SRC)
            pp['census_1900'] = seen(r)
            d = describe(r)
            occ = occ_value(r)
            txt = (f"The 1900 census lists {display(r['name'])} here as {r['rel'].lower()}"
                   f"{', ' + d if d else ''}{', ' + occ if occ else ''} ({locator(r)}).")
            if r['birth'] in ('', '(blank)') or 'blank' in r['birth']:
                txt = f"The 1900 census lists {display(r['name'])} here with the other columns left blank ({locator(r)})."
            elif r['birth'].lower() == 'unknown':
                txt = f"The 1900 census lists {display(r['name'])} here as head, with the personal columns written 'Unknown' ({locator(r)})."
            pp['note'] = (pp.get('note', '') + ' ' + txt).strip()
            enriched[stem] += 1
            continue
        if k_skip:
            report.append((house, r['name'], 'skip', skip[k_skip]))
            continue
        staff = False
        if rear:
            if r['rel'] == 'Head' or r['rel'] in ('Servant', 'Boarder', 'Roomer', 'Helper'):
                staff = any(s in r['occ'].lower() for s in STABLE)
            if not staff:
                if r['rel'] != 'Head':
                    continue  # a coachman's wife or child, named in his note
                report.append((house, r['name'], 'skip', 'rear dwelling, no stable trade'))
                continue
        elif r['rel'] in STAFF_REL or r['rel'] == 'Servant':
            staff = True
        if not staff and not k_add:
            report.append((house, r['name'], 'UNHANDLED', r['rel']))
            continue
        pid = new_id(stem, r)
        d = describe(r)
        occ = occ_value(r)
        person = {'id': pid, 'name': display(r['name']) or r['name'], 'relationship': 'servant' if staff else (
            {'Son': 'son', 'Daughter': 'daughter'}.get(r['rel'], 'household_member')),
                  'grade': 'inferred', 'sources': [SRC]}
        bt, yr = birth_text(r)
        if bt and yr:
            person['born'] = {'value': yr, 'confidence': 'inferred' if ('?' in r['birth'] or '?' in r['age']) else 'attested',
                              'sources': [SRC], 'note': f"The census gives {bt}, age {r['age'].replace('?', '')} on 1 June 1900."}
        if occ:
            person['occupation'] = {'value': occ, 'confidence': 'attested', 'sources': [SRC],
                                    'note': f"Written as \"{r['occ'].replace('?', '')}\" in the occupation column on 1 June 1900{' (the column runs a line out of step here, so the trade is uncertain)' if 'step' in r['note'] else ''}."}
        person['census_1900'] = seen(r)
        where = 'in the rear building behind the house' if rear else 'in the house'
        if '(dw.2)' in r['house']:
            where = 'in the dwelling the enumerator visited next, which has no number of its own and follows 1729'
        role = {'Head': 'the head of his own household there', 'Servant': 'a servant', 'Butler': 'a servant',
                'Helper': 'a helper', 'Boarder': 'a boarder', 'Roomer': 'a roomer', 'Companion': 'a companion',
                'Son': 'a son of the head', 'Daughter': 'a daughter of the head'}.get(r['rel'], r['rel'].lower())
        if occ and occ.lower() not in role:
            role += f" ({occ})"
        if staff:
            lead = f"Enumerated on 1 June 1900 {where}, as {role}" + (f"; {d}." if d else '.')
            fam = rear_family.get(id(r)) if rear and r['rel'] == 'Head' else None
            if fam:
                names = [f"{display(x['name'])} ({x['rel'].lower()})" for x in fam if not any(s in x['occ'].lower() for s in STABLE)]
                if names:
                    lead += f" Living with him: {', '.join(names)}."
            lead += (" Servants changed places often, so this records who worked here in 1900; no source read says "
                     "whether this person was still here on 1 July 1904.")
        else:
            lead = (f"Enumerated on 1 June 1900 {where}, as {role}" + (f"; {d}." if d else '.') +
                    " The 1904 Blue Book names no children, so a child at home in 1900 is placed here in 1904 by inference.")
        if doubtful(r):
            lead += " Part of the name is hard to read on the sheet; this is the best reading."
        if 'Black' in r['note']:
            lead += " The census records the color column as B."
        if stem == 'hh_glessner_john_j' and r['name'] == 'Ryan, Kate':
            lead += (" The family was at their New Hampshire farm on the census day, and the museum's account has Mattie "
                     "Williamson as their cook in these years, so Kate Ryan may have cooked for the house while they were away.")
        person['note'] = lead
        new.append(person)
        added[stem] += 1
    if new or enriched[stem]:
        persons.extend(new)
        touched.add(stem)
    # the who-is-left-out note
    staff_n = sum(1 for p in new if p['relationship'] == 'servant')
    kid_n = len(new) - staff_n
    eds = sorted({f"ED {r['ed']}" for r in rs})
    msg = f"The 1900 census ({' and '.join(eds)}, T623 roll 245) was read for this card. "
    if staff_n or kid_n:
        bits = []
        if staff_n:
            bits.append('one live-in servant' if staff_n == 1 else f"{WORDS.get(staff_n, staff_n)} live-in staff")
        if kid_n:
            bits.append('one child' if kid_n == 1 else f"{WORDS.get(kid_n, kid_n)} children")
        msg += (f"The {' and '.join(bits)} it lists at the house on 1 June 1900 {'is' if staff_n + kid_n == 1 else 'are'} on the card, "
                "graded inferred because the count was taken four years before the scene."
                + (" A coachman's wife and children in the rear building are named in his note rather than carded."
                   if any('Living with him' in p.get('note', '') for p in new) else ''))
    else:
        msg += "It lists no live-in staff at the house on 1 June 1900."
    left = [f"{display(n)} ({why})" for (h, n, kind, why) in report if h == house and kind == 'skip']
    if left:
        msg += " Left off: " + '; '.join(left) + '.'
    msg += " The 1910 census was not read."
    set_census_sentence(card, msg, staff_n)
    # daughters the Blue Book prints only as '& dr.'
    named = [r for r in rs if key_for(r, skip) and 'note on' in skip[key_for(r, skip)] or (key_for(r, skip) and "that line's note" in skip[key_for(r, skip)])]
    if named:
        target = next((pp for pp in persons if pp['relationship'] == 'daughter' and pp.get('grade') == 'attested'), None)
        if target is not None:
            names = [f"{display(r['name'])} ({describe(r)}; {locator(r)})" for r in named]
            target['note'] = (target.get('note', '') + ' The 1900 census lists the unmarried '
                              + ('daughter at home as ' if len(names) == 1 else 'daughters at home as ') + '; '.join(names)
                              + ('. She is very likely the one the book means, but the book does not say.' if len(names) == 1
                                 else '. Which of them the 1904 line stands for, the book does not say.')).strip()
            if SRC not in target['sources']:
                target['sources'].append(SRC)
    touched.add(stem)


# cards the census did not reach, or found another family at
NOT_FOUND = ("The 1900 census was read for the Prairie Avenue sheets of ED 36 and ED 40 (T623 roll 245), and this "
             "household was not found at this number on 1 June 1900, so no staff are listed. The 1910 census was not read.")
for stem, (path, card) in cards.items():
    if stem in touched:
        continue
    m = re.search(r'at (\d+) Prairie', card['name'])
    h = m.group(1) if m else ''
    other = OTHER_FAMILY.get(h)
    if stem == 'hh_lee_blewett':
        other = ("In 1900 the Lees were not yet here: the census finds Blewett and Frances Lee at 1623 Prairie Avenue "
                 "(ED 36, sheet 1A, lines 14-19) with their son John, then a year old, and three servants: Margaret Kelly, "
                 "waitress, Anna Sawtelle, nurse, and Julia Nolan, cook. Those servants kept a different house four years "
                 "earlier and are not carried to 1700.")
        set_census_sentence(card, other + " The 1910 census was not read.")
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + '\n')
        touched.add(stem)
        continue
    msg = (other + " The census says nothing about this household's staff. The 1910 census was not read.") if other else NOT_FOUND
    set_census_sentence(card, msg)
    path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + '\n')
    touched.add(stem)

for stem in sorted(touched):
    path, card = cards[stem]
    path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + '\n')

print('touched', len(touched), 'added', sum(added.values()), 'enriched', sum(enriched.values()))
for x in report:
    if x[2] == 'UNHANDLED':
        print('UNHANDLED', x)
