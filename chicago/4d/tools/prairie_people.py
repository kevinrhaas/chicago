#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3548: reproducible casting and days for the researched Prairie Avenue roster.

Identity, birth and presence come from the household records. Everything this tool
chooses for an unpictured person is a labelled liberty, never a new census reading.
Run after compile_scene.py --scene 1904; --check compares every generated file.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBERTY = 'L-prairie-people-3548'
CHILD_LIBERTY = 'L-prairie-younger-3550'
LOOKS_LIBERTY = 'L-prairie-likenesses-3547'
MALE_STAFF = {'henry_deneke', 'joseph_daniels', 'b_f_plummer', 'fred_stump',
              'thomas_benson', 'john_dunford', 'james_mason', 'arthur_george_parker',
              'daniel_bain', 'james_halligan', 'valentine_nier', 'john_olson',
              'george_hauser', 'peter_benson', 'paul_rasmussen', 'thomas_nelson',
              'ernest_sibbald', 'charles_lingquist', 'robert_bain', 'james_o_keith',
              'robert_grimmond', 'clarence_clough', 'hugh_fields', 'john_halloran',
              'terry_young', 'alex_dumas_jr', 'alfred_johnson', 'hans_johnson',
              'john_bailey', 'chris_johnson', 'henry_windish', 'samuel_whatter_jr',
              'harry_walker', 'axel_carlson', 'frank_allen', 'christ_jorgensen',
              'edward_carlson', 'peter_wilson', 'frank_manda', 'charles_rolde',
              'wm_taylor', 'john_clarke', 'james_robertson', 'thomas_goodwin',
              'william_wellington', 'charles_nelson', 'august_billings'}
FEMALE_MEMBERS = {'pa1904_gregory_eleanor', 'pa1904_de_teresa_isabel',
                  'pa1904_pullman_mrs_george_m'}
PALETTE = [('navy', [.025, .038, .07]), ('charcoal', [.048, .047, .044]),
           ('brown', [.09, .053, .032]), ('dark green', [.035, .06, .045]),
           ('plum', [.075, .035, .05]), ('slate', [.075, .085, .10])]


def read(rel):
    return json.loads((ROOT / rel).read_text())


def draw(pid, key):
    return int(hashlib.sha256(f'{pid}:{key}'.encode()).hexdigest()[:8], 16) / 2**32


def choose(pid, key, values):
    return values[int(draw(pid, key) * len(values))]


def age_of(p):
    b = str((p.get('born') or {}).get('value', ''))
    return 1904 - int(b[:4]) - (len(b) >= 7 and b[5:7] > '06') if b[:4].isdigit() else None


def casting(p):
    """Presentation of the reusable body, not an attested sex field."""
    if p.get('relationship') in ('wife', 'daughter') or p['name'].startswith(('Mrs.', 'Miss ')) or p['id'] in FEMALE_MEMBERS:
        return 'female'
    if p.get('relationship') == 'servant':
        return 'male' if p['id'].split('_c1900_')[-1] in MALE_STAFF else 'female'
    return 'male'


def role_of(p, sex):
    age = age_of(p)
    if age is not None and age < 18:
        return 'child_toddler_1904' if age < 5 else ('child_' if age < 12 else 'teen_') + ('girl' if sex == 'female' else 'boy') + '_1904'
    job = (p.get('occupation') or {}).get('value', '').lower()
    if p.get('relationship') != 'servant':
        return 'lady' if sex == 'female' else 'gentleman'
    if 'coachman' in job:
        return 'coachman'
    if any(w in job for w in ('groom', 'horseman', 'stable', 'helper')):
        return 'stable_helper'
    if sex == 'male':
        return 'steward'
    if job == 'cook':
        return 'cook'
    if any(w in job for w in ('nurse', 'governess', 'companion')):
        return 'companion'
    return 'maid'


ASSETS = {'gentleman': 'glessner_john_j_1904', 'lady': 'glessner_frances_m_1904',
          'coachman': 'nelson_charles_1904_coachman', 'stable_helper': 'billings_august_1904_stable_helper',
          'steward': 'glessner_john_j_1904', 'maid': 'reynolds_mary_1904_maid',
          'cook': 'ryan_kate_1904_cook', 'companion': 'nelson_christine_1904_errand'}

CHILD_HEIGHT = {'child_boy_1904': 1.208, 'child_girl_1904': 1.205, 'child_toddler_1904': .905, 'teen_boy_1904': 1.65, 'teen_girl_1904': 1.59}
ASSETS.update({k: k for k in CHILD_HEIGHT})

def dress_for(pid, role):
    if role in CHILD_HEIGHT:
        palette = PALETTE + [('cream', [.40, .36, .28]), ('blue', [.13, .20, .28]), ('rose', [.30, .16, .18])]
        name, rgb = choose(pid, 'cloth', palette)
        boy = 'boy' in role
        mats = ['garment_upper__child_jacket_1904', 'garment_lower__child_trousers_1904'] if boy else ['garment_upper__child_frock_1904', 'garment_lower__child_frock_1904']
        return {'asset': role, 'colours': {m: rgb for m in mats}, 'hide': [], 'worn': f'{name} jacket and knee trousers' if boy else f'{name} frock and stockings'}
    name, rgb = choose(pid, 'cloth', PALETTE[:4] if role in ('gentleman', 'steward') else PALETTE)
    material = {'gentleman': 'garment_outer__frock_coat_black', 'steward': 'garment_outer__frock_coat_black',
                'lady': 'garment_outer__lady_jacket_black', 'coachman': 'garment_outer__livery_coat_green_1904',
                'stable_helper': 'garment_lower__trousers_dark_1904',
                'maid': 'garment_upper__maid_dress_black', 'cook': 'garment_upper__cook_print_dress',
                'companion': 'garment_lower__errand_skirt_navy'}[role]
    colours = {material: rgb}
    if role in ('maid', 'cook', 'lady'):
        colours[{'maid': 'garment_lower__maid_skirt_black', 'cook': 'garment_lower__cook_print_skirt',
                 'lady': 'garment_lower__lady_skirt_black'}[role]] = rgb
    return {'asset': ASSETS[role], 'colours': colours,
            'hide': ['market_basket', 'basket_cloth'] if role == 'companion' else [],
            'worn': f'{name} {"day dress" if role == "lady" else "coat and trousers" if role in ("gentleman", "steward") else role.replace("_", " ") + " working clothes"}'}


def looks_for(p, sex, portrait):
    pid = p['id']; age = age_of(p)
    hair = choose(pid, 'hair', ['dark_brown', 'mid_brown', 'light_brown', 'black_brown', 'sandy'])
    if age is not None and age > 58:
        hair = choose(pid, 'grey', ['white_grey', 'grey_brown'])
    cut = ('swept_up_knot_1904' if draw(pid, 'cut') > .5 else 'drawn_back_bun_1904') if sex == 'female' else 'short_side_part_1904'
    facial = []
    stand_in = bool(portrait and portrait.get('stand_in'))
    if portrait:
        cut = portrait['hair_cut']
        facial = list(portrait['facial']) if isinstance(portrait.get('facial'), list) else [portrait['facial']] if portrait.get('facial') else []
        hair = portrait.get('hair_tone', hair)
    elif sex == 'male' and (age is None or age > 25) and draw(pid, 'moustache') > .65:
        facial = ['moustache']
    if not any(f.startswith('brows_') for f in facial):   # a portrait's own brows stand in for the default
        facial += ['brows_fine'] if sex == 'female' else ['brows_full']
    if sex == 'female' and 'lashes_upper' not in facial:
        facial += ['lashes_upper']
    skin = choose(pid, 'skin', ['fair', 'light', 'ruddy', 'olive'])
    eyes = choose(pid, 'eyes', ['blue', 'grey', 'hazel', 'brown'])
    if stand_in:
        skin = portrait.get('complexion', skin); eyes = portrait.get('eyes', eyes)
    inches = round((64 if sex == 'female' else 68) + (draw(pid, 'height') - .5) * 6, 1)
    young = age is not None and age < 18
    if young:
        if not portrait:
            cut = 'girl_plait_1812' if sex == 'female' else 'cropped_1812'
        facial = ['brows_fine', 'lashes_upper'] if sex == 'female' else ['brows_full']
        # Interpolate between the approved engineering bodies, not a historical measurement.
        anchors = [(2, .85), (3, .905), (4, .99), (5, 1.06), (8, 1.205), (11, 1.40), (12, 1.45), (15, 1.59 if sex == 'female' else 1.65), (17, 1.65 if sex == 'female' else 1.74)]
        lo = max((x for x in anchors if x[0] <= age), key=lambda x: x[0])
        hi = min((x for x in anchors if x[0] >= age), key=lambda x: x[0])
        metres = lo[1] if lo[0] == hi[0] else lo[1] + (hi[1] - lo[1]) * (age - lo[0]) / (hi[0] - lo[0])
        inches = round(metres * (1 + (draw(pid, 'height') - .5) * .035) / .0254, 1)
    basis = ('No photograph of this person is known. Face, hair cut, facial hair and dress follow a stand-in portrait the owner chose as the likeness (' + portrait['source'] + '); it is not a picture of them. ' if stand_in else
             'Hair cut and facial hair follow the identified portrait; facial proportions have a separate photograph fit. ' if portrait else
             'No verified individual portrait is available. This is a distinct, seeded reconstruction, not a likeness. ')
    basis += 'Skin, eye and hair colours, stature and build are artistic choices, not demographic facts or measurements. No ancestry is inferred from a surname or photograph. The body and clothes are selected from the recorded household role; exact clothes are a liberty.'
    if young:
        basis += ' Stature is interpolated between approved child and teen engineering bodies, with small individual variation; adult aging and body-build targets are disabled.'
    if age is None:
        basis += 'An adult age is provisional because this record gives no birth year.'
    return {'format': 'chicago4d_human_looks_v1', 'ticket': 'T-3550' if young else 'T-3547', 'person_id': pid, 'scene': '1904',
            'generated_by': 'tools/prairie_people.py', 'heritage': {'origin': 'not found'},
            'complexion': {'value': skin, 'drawn': skin, 'grade': 'reconstructed'},
            'hair': {'value': hair.replace('_', ' '), 'drawn': hair, 'cut': cut, 'facial': facial,
                     'grade': 'inferred' if portrait and not stand_in else 'reconstructed',
                     **({'basis': portrait['hair_tone_basis']} if portrait and portrait.get('hair_tone_basis') else {})},
            'eyes': {'value': eyes, 'drawn': eyes, 'grade': 'reconstructed'},
            'stature': {'inches': inches, 'grade': 'reconstructed', 'basis': 'Artistic body variation; no personal measurement located.'},
            'height_scale': round(inches * .0254 / (CHILD_HEIGHT[role_of(p, sex)] if young else (1.65 if sex == 'female' else 1.75)), 4),
            **({'build': portrait['build']} if stand_in and portrait.get('build') else {}),
            **({'drawn_age': portrait['drawn_age']} if stand_in and portrait.get('drawn_age') else {}),
            'grade': 'reconstructed', 'basis': basis, 'liberty': CHILD_LIBERTY if young else LOOKS_LIBERTY}


# T-3554 (owner, 2026-11-12: "people should not be able to walk through walls or barriers"): a
# day's outdoor place stands STAND_M off every house wall and every barrier a house builds outside
# them (stoop, area walls, railings, bays: tools/prairie_barriers.py), and the walks out to it and
# along the frontage keep a skirt's half-width (prairie_barriers.SKIRT_M) off them the whole way.
STAND_M = 0.55       # human-days.js clearWayOf stands a body 0.5 m off a wall; a hair more here
OUT_M = (0.8, 1.2, 1.6, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0)   # how far out from the answering place
SIDE_M = tuple(x / 2 for x in range(-6, 7))                    # and along the frontage
WALK_M = (3.0, 2.0)                                             # the length of a frontage walk
CORE_M = 0.15        # where no walk keeps a skirt's width (a narrow front gate), the body itself still clears


def outdoor_points(pid, door, rings):
    """Where `pid`'s outdoor spans stand and walk to: (at, end) in local E/N, the seeded
    first choice (0.8 m out, up to 1.5 m along, a 3 m walk along the frontage) where it is clear,
    else the nearest clear one; where no way out from the door keeps a skirt's width (a narrow
    gate in a front railing), the nearest whose way out keeps the body itself clear (CORE_M);
    None when the frontage has none."""
    angle = math.radians(door['outward_deg']); de, dn = math.sin(angle), math.cos(angle)
    base = (door['step']['local_e'], door['step']['local_n'])
    side = (draw(pid, 'side') - .5) * 3
    pt = lambda o, s: (round(base[0] + o * de + s * dn, 2), round(base[1] + o * dn - s * de, 2))
    sides = sorted({round(side, 6), *SIDE_M}, key=lambda s: (abs(s - side), s))
    for r in (None, CORE_M):
        leg = (lambda a, b: rings.clear_leg(a, b)) if r is None else (lambda a, b: rings.clear_leg(a, b, r))
        for o in OUT_M:
            for s in sides:
                at = pt(o, s)
                if not rings.clear_point(at, STAND_M) or not leg(base, at):
                    continue
                for length in WALK_M:
                    for sign in (1, -1):
                        end = (round(at[0] + sign * length * dn, 2), round(at[1] - sign * length * de, 2))
                        if rings.clear_point(end, STAND_M) and rings.clear_leg(at, end):
                            return at, end
    return None


def scene_rings(door_data):
    """Every 1904 building's walls and every Prairie house's barriers, as prairie_barriers.Rings."""
    import prairie_barriers as pb
    rings = []
    for f in sorted((ROOT / 'data/sidecars/1904').glob('*.json')):
        try:
            sc = json.loads(f.read_text())
        except ValueError:
            continue
        poly = (sc.get('footprint') or {}).get('polygon') if isinstance(sc, dict) else None
        pl = sc.get('placement') if isinstance(sc, dict) else None
        if poly and len(poly) >= 3 and pl and pl.get('vertical_anchor') != 'water':
            rings.append([pb.d1812.to_world(float(u), float(v), pl) for u, v in poly])
    for row in door_data['structures'] + door_data.get('barriers', []):
        rings += pb.rings_from_plan(row.get('barrier'), row['placement'])
    return pb.Rings(rings)


def routine(pid, home, door, role, age=None, rings=None):
    # All outdoor points are beyond the answering place, along its frontage, clear of what is built there.
    got = outdoor_points(pid, door, rings) if rings is not None else None
    if got is None and rings is not None:
        raise ValueError(f'{pid}: no clear outdoor place before {door["id"]}')
    if got is None:
        angle = math.radians(door['outward_deg']); de, dn = math.sin(angle), math.cos(angle)
        base = door['step']; side = (draw(pid, 'side') - .5) * 3
        got = ((round(base['local_e'] + .8 * de + side * dn, 2), round(base['local_n'] + .8 * dn - side * de, 2)), None)
        got = (got[0], (round(got[0][0] + 3 * dn, 2), round(got[0][1] - 3 * de, 2)))
    at = {'local_e': got[0][0], 'local_n': got[0][1], 'heading_deg': door['outward_deg']}
    end = {'local_e': got[1][0], 'local_n': got[1][1]}
    if role in CHILD_HEIGHT:
        def inside(a, b, doing):
            return {'from': a, 'to': b, 'indoors': True, 'where': home, 'doing': doing}
        def outside(a, b, doing, activity):
            return {'from': a, 'to': b, 'indoors': False, 'at': at, 'activity': activity, 'doing': doing, **({'to_point': end} if activity == 'walk' else {})}
        days = []
        for months, length in [([11, 12, 1, 2], .5), ([3, 4, 9, 10], 1), (None, 1.5)]:
            little = age < 5
            days.append({**({'dates': {'months': months}} if months else {}), 'spans': [
                inside(0, 7, 'sleeping in household care' if little else 'sleeping'),
                inside(7, 10, 'breakfast and indoor play' if little else 'breakfast and lessons or reading'),
                outside(10, 10 + length, 'a short walk with a household adult' if age < 12 else 'taking the air near home', 'walk'),
                inside(10 + length, 15, 'meal, indoor play and a nap' if little else 'lessons, a meal and indoor occupations'),
                outside(15, 15 + length, 'playing near home with a household adult' if age < 12 else 'a walk along the frontage', 'walk'),
                inside(15 + length, 17, 'indoor play and family time'),
                outside(17, 17 + length / 2, 'a conversation with a household member', 'talk'),
                inside(17 + length / 2, 20 if age < 12 else 21.5, 'supper and family time'),
                inside(20 if age < 12 else 21.5, 24, 'sleeping') ]})
        return days
    work = {'gentleman': 'taking a walk along the house frontage', 'lady': 'taking the air and visiting along the frontage',
            'coachman': 'checking the approach before the next carriage trip',
            'stable_helper': 'checking the carriage approach', 'steward': 'checking for household deliveries',
            'maid': 'sweeping the entrance', 'cook': 'checking kitchen deliveries at the entrance',
            'companion': 'taking a short walk near the house'}[role]
    def indoors(a, b, doing):
        return {'from': a, 'to': b, 'indoors': True, 'where': home, 'doing': doing}
    def outdoors(a, b, doing, activity='work'):
        s = {'from': a, 'to': b, 'indoors': False, 'at': at, 'activity': activity, 'doing': doing}
        if activity == 'walk':
            s['to_point'] = end
        return s
    days = []
    shift = int(draw(pid, 'shift') * 4) / 2
    for months, morning, evening in [([11, 12, 1, 2], .5, .5), ([3, 4, 9, 10], 1, 1), (None, 1.5, 1.5)]:
        a = 8 + shift; b = 15 + shift
        spans = [indoors(0, 6.5, 'sleeping'), indoors(6.5, a, 'breakfast and preparations for the day'),
                 outdoors(a, a + morning, work, 'walk' if role in ('gentleman', 'lady', 'companion') else 'work'),
                 indoors(a + morning, 12.5, 'household duties' if role not in ('gentleman', 'lady') else 'correspondence and personal business'),
                 indoors(12.5, b, 'meal and afternoon duties'), outdoors(b, b + morning, work, 'walk'),
                 indoors(b + morning, 18, 'preparing for the evening'),
                 outdoors(18, 18 + evening, 'a conversation with a household member or neighbour', 'talk'),
                 indoors(18 + evening, 22, 'supper and evening duties'), indoors(22, 24, 'sleeping')]
        days.append({**({'dates': {'months': months}} if months else {}), 'spans': [s for s in spans if s['from'] < s['to']]})
    return days


def generate():
    rows = read('data/sidecars/1904/people.json')['people']
    originals = {read(str(f.relative_to(ROOT)))['person_id'] for f in (ROOT / 'data/humans/instances/1904').glob('hi_*.json')}
    portraits = {x['person_id']: x for x in read('docs/RESEARCH/prairie-portraits-3546/portraits.json')['portraits']}
    # T-3553: a stand-in the owner chose as someone's likeness where no photograph of them is
    # known (data/humans/variation/portraits/<id>.json `stand_in` + `likeness`): its hair, facial
    # hair, colouring and dress, labelled everywhere as not them.
    stand_ins = {}
    for f in sorted((ROOT / 'data/humans/variation/portraits').glob('pa1904_*.json')):
        rec = json.loads(f.read_text())
        if rec.get('stand_in') and rec.get('likeness') and rec['person_id'] not in portraits:
            stand_ins[rec['person_id']] = {**rec['likeness'], 'stand_in': True, 'source': rec['source']}
    catalog, inside, care, dresses, outputs = [], [], [], {}, {}
    records = {}
    for row in rows:
        p = next(p for p in read('data/residents_1904/' + row['file'])['persons'] if p['id'] == row['id'])
        pid = p['id']; age = age_of(p); sex = casting(p); role = role_of(p, sex)
        records[pid] = p
        status = ('alias' if p.get('own_card') else 'collective' if p.get('collective') else
                  'absent' if row['present'] == 'absent' or p.get('lived_here', {}).get('on_scene_date') == 'no' else
                  'existing' if pid in originals else 'household_care' if age is not None and age < 2 else 'ready')
        item = {'person': pid, 'home': row['lives_at'], 'status': status, 'age_1904': age,
                'portrait': 'stand_in' if pid in stand_ins else 'verified' if pid in portraits or p.get('portrait') or (ROOT / f'data/humans/variation/fits/{pid}.json').exists() else 'not_identified'}
        if status == 'alias':
            item['canonical'] = p['own_card']
        elif status not in ('collective', 'existing', 'household_care') and (age is None or age >= 2):
            item.update(asset_id=ASSETS[role], body_presentation=sex, casting_grade='reconstructed', role=role)
            outputs[f'data/humans/variation/looks/{pid}.json'] = looks_for(p, sex, portraits.get(pid) or stand_ins.get(pid))
            dresses[pid] = dress_for(pid, role)
            if pid in stand_ins and stand_ins[pid].get('dress'):
                own = stand_ins[pid]['dress']
                dresses[pid] = {**dresses[pid], 'colours': {**dresses[pid]['colours'], **own['colours']}, 'worn': own['worn'],
                                **({'collar': own['collar']} if own.get('collar') else {})}
        if status == 'ready':
            inside.append({'person': pid, 'name': p['name'], 'home': row['lives_at'], 'door': row['lives_at'] + ':front',
                           'asset_id': ASSETS[role], 'ask_order': 10 if p['relationship'] != 'servant' else 30,
                           'provenance': {'grade': 'reconstructed', 'ticket': 'T-3548', 'sources': p.get('sources', []),
                                          'liberty': LIBERTY, 'basis': 'Identity from the household record; presence remains as graded there. Appearance, daily movements, company and clothes are reconstructed.'}})
        if status == 'household_care':
            care.append({'person': pid, 'name': p['name'], 'home': row['lives_at'], 'door': row['lives_at'] + ':front', 'ask_order': 15, 'age_1904': age, 'care_only': True,
                         'provenance': {'grade': 'reconstructed', 'ticket': 'T-3550', 'sources': p.get('sources', []), 'liberty': CHILD_LIBERTY,
                                        'basis': 'Identity and birth evidence remain on the household record; care, timing and caregivers are reconstructed.'}})
        catalog.append(item)
    # A care assignment is a same-household reconstruction, never a claim of parentage.
    for entry in inside + care:
        age = age_of(records[entry['person']])
        if age is None or age >= 18:
            continue
        adults = [x for x in catalog if x['home'] == entry['home'] and x['status'] in ('ready', 'existing') and (x['age_1904'] is None or x['age_1904'] >= 18)]
        adults.sort(key=lambda x: (0 if any(w in (records[x['person']].get('occupation') or {}).get('value', '').lower() for w in ('nurse', 'governess')) else 1 if records[x['person']].get('relationship') in ('head', 'wife') else 2, x['person']))
        if not adults:
            raise ValueError('No household adult for ' + entry['person'])
        entry['caregivers'] = [x['person'] for x in adults]
        entry['care_basis'] = 'Reconstructed company from adults recorded in this household; not an attested care assignment or parentage.'
        entry['age_1904'] = age
        entry['supervised'] = age < 12
        entry['routine_liberty'] = CHILD_LIBERTY
        if age >= 2:
            entry['role_review'] = 'data/humans/role_reviews/prairie_children_1904.json'
            entry['provenance']['liberty'] = CHILD_LIBERTY
            entry['provenance']['ticket'] = 'T-3550'
    # Derive doors from this full set without a circular dependency on yesterday's generated inside file.
    import derive_doors_scene as doors_tool
    previous = doors_tool.wheres
    doors_tool.wheres = lambda scene: previous(scene) | {x['home'] for x in inside + care} if scene == '1904' else previous(scene)
    door_data, errors = doors_tool.derive('1904')
    doors_tool.wheres = previous
    if errors:
        raise ValueError(errors)
    byhome = {x['structure']: x['doors'] for x in door_data['structures']}
    rings = scene_rings(door_data)
    roles = {x['person']: x.get('role') for x in catalog}
    for entry in inside + care:
        ds = byhome[entry['home']]
        door = next((d for d in ds if d['id'] == entry['door']), ds[0])
        entry['door'] = door['id']
        if entry.get('care_only'):
            entry['day'] = [{'spans': [{'from': a, 'to': b, 'indoors': True, 'where': entry['home'], 'doing': doing} for a, b, doing in [(0, 7, 'sleeping in household care'), (7, 10, 'being fed and cared for'), (10, 12, 'playing quietly in household care'), (12, 15, 'being fed or taking a nap'), (15, 18, 'awake with a household caregiver'), (18, 24, 'receiving evening care or sleeping')]]}]
        else:
            entry['day'] = routine(entry['person'], entry['home'], door, roles[entry['person']], entry.get('age_1904'), rings)
        entry.setdefault('routine_liberty', LIBERTY)
    # Keep the door compiler's canonical byte representation as well as its values.
    outputs['data/humans/doors_1904.json'] = json.dumps(door_data, indent=1) + '\n'
    outputs['data/humans/inside_1904.json'] = {'format': 'chicago4d_inside_only_v1', 'generated_by': 'tools/prairie_people.py',
        'doc': 'Prairie Avenue residents built near the visitor or on a door call; seasonal reconstructed days. Aliases, collective listings and absent former residents do not create duplicate actors. See prairie_1904.json for the complete roster. Infants have household care schedules and can be asked after at the door; they do not walk out independently.', 'people': inside, 'care': care}
    outputs['data/humans/prairie_1904.json'] = {'format': 'chicago4d_prairie_cast_v1', 'ticket': 'T-3548',
        'generated_by': 'tools/prairie_people.py', 'liberty': LIBERTY, 'people': catalog}
    outputs['data/humans/variation/dress_1904_prairie.json'] = {'format': 'chicago4d_human_dress_v1', 'scene': '1904',
        'ticket': 'T-3548', 'generated_by': 'tools/prairie_people.py', 'liberty': LIBERTY, 'persons': dresses}
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--check', action='store_true'); args = ap.parse_args()
    bad = []
    for rel, data in generate().items():
        text = data if isinstance(data, str) else json.dumps(data, indent=1, ensure_ascii=False) + '\n'
        path = ROOT / rel
        if args.check:
            if not path.exists() or path.read_text() != text:
                bad.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
    if bad:
        raise SystemExit('FAIL Prairie people outputs stale: ' + ', '.join(bad))
    print('ok Prairie people outputs ' + ('reproduce' if args.check else 'written'))


if __name__ == '__main__':
    main()
