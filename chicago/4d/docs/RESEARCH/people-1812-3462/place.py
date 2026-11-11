# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3462: stand every enlisted man of Heald's company in the 1812 scene as himself.

Each man the T-3461 sweep cards in Heald's company (data/residents_1812/households/) gets a
human instance (data/humans/instances/1812/hi_<person>_1812.json) wearing the company
private's dress (asset private_first_infantry_1812, T-3451), with the face, height and build
the variation kit seeds from his own person id (T-3412). Paul Grummo already stands on the
parade (hi_heald_company_private_1812) and is left as he is.

THE STATIONS ARE OURS (liberty L-1812-garrison-stations-3462). No order book, guard report or
morning report of the post survives for 14 August 1812, so where each man is at three in the
afternoon, and what he is doing, is reconstructed from what any small frontier post of the
period kept: a guard at the main gate under a sergeant, a sentry at the magazine, men about
the barracks doors and on the parade, men at the post's garden, stables, bake house and
armourer's shop, at the wharf and the river bank, and two at the company's cornfield at the
forks. T-3490 (owner: "all of them standing around aimlessly is awkward") gives the men inside
the pickets duties (behaviour.duty, renderers/web/js/human-duties.js): sentries walking their
posts, a fatigue party in rank before its sergeant, knots of men talking that break up and come
back together, an orderly at the commanding officer's door. Paul Grummo's own record is moved
into the rank by hand. Nothing of that day is acted out: no council, no giving out of the goods, no
destruction of the ammunition. Which man stands where follows the roll's order within a rank;
the four married men stand near the quarters T-3461 gives their families. T-3523 dresses and arms each man by his rank and his station (garrison_dress.py: NCO epaulettes,
the musicians' red coats, drums and fife cases, fatigue clothes at chores, muskets carried by
duty) and writes data/humans/variation/dress_1812_garrison.json with the instances.

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-3462/place.py [--check]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import garrison_dress as GD  # noqa: E402  (T-3523: dress by rank and duty)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INST = ROOT / 'data/humans/instances/1812'
COMPANY = ROOT / 'data/residents_1812/households'
ASSET = 'private_first_infantry_1812'
KEEP = 'hi_heald_company_private_1812'      # Paul Grummo, placed by T-3452
DRESS_SOURCES = ['loc_ogden_1888_infantry_artillery_1802_1810', 'met_krimmel_1813_philadelphia_soldiery',
                 'us_1812_rules_and_articles_albany', 'us_1814_military_laws_and_regulations']

# (station id, words, e, n, heading, state, route or None[, duty])
# e/n are the scene's local metres; heading clockwise from grid north. A duty (T-3490) is the
# record's behaviour.duty, played by renderers/web/js/human-duties.js: a `knot` of men talking
# who now and then each walk off to their own place and come back, a sentry's `beat`, a `rank`.


def knot(kid, words, ce, cn, members, turn=0.0):
    """A knot of men standing together facing in: (station id, away (e, n, heading[, via]))."""
    r = 0.75 if len(members) <= 3 else 0.9
    out = []
    for i, (sid, away) in enumerate(members):
        ang = math.radians(turn + i * 360.0 / len(members))
        e, n = ce + r * math.sin(ang), cn + r * math.cos(ang)
        heading = (math.degrees(math.atan2(ce - e, cn - n)) + 360) % 360
        a = {'local_e': away[0], 'local_n': away[1], 'heading_deg': away[2]}
        if len(away) > 3:
            a['via'] = [{'local_e': x, 'local_n': y} for x, y in away[3]]
        out.append((sid, words, round(e, 2), round(n, 2), round(heading, 1) % 360, 'talking', None,
                    {'kind': 'knot', 'id': kid, 'away': a}))
    return out


def beat(sid, words, e, n, heading, to, face=None, pause=None):
    d = {'kind': 'beat', 'to': {'local_e': to[0], 'local_n': to[1]}}
    if face is not None:
        d['face_deg'] = face
    if pause:
        d['pause_s'] = list(pause)
    return (sid, words, e, n, heading, 'standing', None, d)


RANK_E, RANK_N0, RANK_STEP = 1146.3, 218.2, 0.72
GRUMMO_SLOT = 2        # Paul Grummo's own record (T-3452) stands third in the rank


def rank():
    out = [('fatigue_lead', 'facing a fatigue party drawn up in a rank on the parade, telling it off', 1149.1, 220.0, 270,
            'standing', None, {'kind': 'rank', 'id': 'fatigue_party', 'lead': True})]
    for i in range(6):
        if i == GRUMMO_SLOT:
            continue
        out.append((f'fatigue_{i}', 'in the rank of a fatigue party drawn up on the parade', RANK_E,
                    round(RANK_N0 + i * RANK_STEP, 2), 90, 'standing', None, {'kind': 'rank', 'id': 'fatigue_party'}))
    return out


STATIONS = [
    # the main gate: the sergeant and corporal of the guard, two sentries walking their posts
    # along the outer pickets (n < 204), turning at each end to face out
    ('gate_sergeant', 'in command of the guard before the main gate', 1149.6, 200.2, 190, 'standing', None),
    ('gate_corporal', 'corporal of the guard, before the main gate', 1151.0, 200.8, 165, 'standing', None),
    beat('gate_west', 'on sentry before the main gate, walking his post west along the pickets', 1147.4, 202.7, 270,
         (1141.6, 202.7), face=180),
    beat('gate_east', 'on sentry before the main gate, walking his post east along the pickets', 1151.8, 202.7, 90,
         (1157.6, 202.7), face=180),
    beat('magazine', 'on sentry before the magazine, walking his post', 1145.3, 229.9, 90, (1148.9, 229.9), face=180),
    # the parade: a fatigue party in rank, four knots of men talking, an orderly, a man to and fro
    *rank(),
    *knot('sw_porch', 'talking with others before the soldiers\' barracks west of the gate', 1145.4, 214.9, [
        ('sw_knot_a', (1144.0, 212.4, 20)),           # the barracks door
        ('sw_knot_b', (1149.4, 212.5, 180)),          # the gate passage, looking out
        ('sw_knot_c', (1142.9, 212.6, 300)),          # the small house in the south-west corner
    ], turn=20),
    *knot('se_porch', 'talking with others before the soldiers\' barracks east of the gate', 1154.8, 215.1, [
        ('se_knot_a', (1153.3, 212.4, 10)),
        ('se_knot_b', (1156.2, 212.5, 350)),
        ('se_knot_c', (1150.7, 212.6, 190)),
        ('se_knot_d', (1159.2, 213.8, 250)),
    ], turn=35),
    *knot('north_range', 'talking with others before the north range', 1154.6, 227.2, [
        ('nr_knot_a', (1161.2, 230.6, 30)),           # the small house in the north-east corner
        ('nr_knot_b', (1153.4, 230.4, 180)),
        ('nr_knot_c', (1156.4, 230.4, 190)),
        ('nr_knot_d', (1151.0, 229.8, 160)),          # between the magazine and the north range
    ], turn=10),
    *knot('west_parade', 'talking with others on the parade by the magazine', 1146.6, 225.6, [
        ('wp_knot_a', (1143.8, 228.4, 300)),
        ('wp_knot_b', (1144.0, 222.8, 90)),           # under the officers' barracks gallery
        ('wp_knot_c', (1150.2, 226.4, 250)),
    ], turn=50),
    ('orderly', 'the commanding officer\'s orderly, waiting at his door', 1160.5, 222.6, 270, 'standing', None),
    beat('storehouse', 'going to and fro between the barracks east of the gate and the north range', 1157.4, 212.6, 0,
         (1158.2, 230.2), pause=(6, 14)),
    # outside the pickets
    ('blockhouse_se', 'outside the pickets by the south-east blockhouse', 1172.0, 205.4, 100, 'standing', None),
    *knot('river_bank', 'talking with others on the river bank north of the fort', 1149.4, 242.4, [
        ('rb_knot_a', (1145.6, 243.4, 0)),            # looking across to the Kinzie house
        ('rb_knot_b', (1153.4, 243.2, 340)),
        ('rb_knot_c', (1156.6, 241.4, 20)),
        ('rb_knot_d', (1142.4, 242.6, 330)),
    ], turn=0),
    ('wharf_a', 'on the bank at the wharf', 1099.2, 242.6, 330, 'standing', None),
    ('wharf_b', 'on the bank at the wharf', 1101.4, 242.9, 20, 'standing', None),
    ('garden_a', 'at work in the commanding officer\'s garden', 1130.0, 125.0, 0, 'working', None),
    ('garden_b', 'at work in the commanding officer\'s garden', 1133.2, 127.2, 80, 'working', None),
    ('garden_c', 'at work in the commanding officer\'s garden', 1150.0, 120.5, 260, 'working', None),
    ('garden_d', 'at work in the commanding officer\'s garden', 1162.0, 131.0, 200, 'working', None),
    ('bake_house', 'at the bake house door', 1067.4, 185.0, 270, 'standing', None),
    ('stable_north', 'at the stables', 1064.6, 142.0, 270, 'standing', None),
    ('stable_middle', 'at the stables', 1063.8, 122.6, 300, 'standing', None),
    ('armourer', 'at the armourer\'s shop', 1219.6, 87.0, 90, 'standing', None),
    ('merchant_shop', 'by the merchant\'s shop', 1205.6, 150.0, 90, 'standing', None),
    ('sutler_garden', 'at work in the sutler\'s garden', 1216.0, 120.0, 340, 'working', None),
    ('road_walk', 'walking between the fort and the agent\'s house', 1146.0, 198.0, 0, 'walking',
     [(1110.0, 186.0), (1076.0, 176.0), (1110.0, 184.0)]),
    ('road_walk_b', 'walking down to the garden', 1153.0, 197.5, 0, 'walking',
     [(1150.0, 160.0), (1146.0, 144.5), (1151.0, 160.0)]),
    ('river_walk', 'walking the river bank west of the fort', 1112.0, 243.0, 0, 'walking',
     [(1132.0, 243.2), (1134.0, 242.0), (1114.0, 242.4)]),
    ('forks_cornfield_a', 'at work in the company\'s cornfield at the forks', 162.0, -240.0, 20, 'working', None),
    ('forks_cornfield_b', 'at work in the company\'s cornfield at the forks', 171.0, -247.0, 200, 'working', None),
    ('forks_walk', 'walking back from the cornfield at the forks', 158.0, -232.0, 0, 'walking',
     [(190.0, -215.0), (160.0, -230.0)]),
]

# Who is out when (T-3490; owner: "all these soldiers around the fort hanging out 24 7"): the
# guard at the gate and the magazine's sentry keep their posts through the night; everyone else
# is out from reveille at daybreak to tattoo in the evening and in quarters between (human-duties.js).
NIGHT_GUARD = {'gate_sergeant', 'gate_corporal', 'gate_west', 'gate_east', 'magazine'}
DAY_HOURS = (5.5, 21.0)

# Who goes where: the guard's sergeant and corporal, the fatigue party's sergeant, the families'
# men in the knots nearest the quarters T-3461 gives their families; then the roll's order.
FIXED = {'holt_isaac': 'gate_sergeant', 'forth_thomas': 'gate_corporal', 'griffith_william': 'fatigue_lead',
         'corbin_fielding': 'sw_knot_a', 'hays_otho': 'sw_knot_c', 'bowen_joseph': 'sw_knot_b',
         'needs_john': 'se_knot_a', 'mcpherson_hugh': 'se_knot_b', 'burnett_george': 'se_knot_c',
         'simmons_john': 'nr_knot_a', 'crozier_john': 'nr_knot_b', 'hamilton_john': 'nr_knot_c',
         'smith_john_jr': 'nr_knot_d'}


def men():
    hh = [json.loads(p.read_text()) for p in sorted(COMPANY.glob('hh_*_1812.json'))]
    out = []
    for h in hh:
        home = next((a['place_or_structure_id'] for a in h.get('associated_with', []) if a.get('kind') == 'home'), None)
        for p in h['persons']:
            occ = (p.get('occupation') or {}).get('value', '')
            if "heald's company" in occ.lower() and not occ.startswith(('captain', 'second lieutenant', 'ensign', "surgeon")):
                out.append({**p, '_home': home})
    return out


def instance(p, st):
    sid, words, e, n, heading, state, route = st[:7]
    duty = st[7] if len(st) > 7 else None
    rank = p['occupation']['value'].split(',')[0]
    asset, _dress, worn = GD.dress_for(p['id'], rank, sid)
    behaviour = {'state': state}
    if route:
        behaviour['route'] = [{'local_e': a, 'local_n': b} for a, b in route]
    if duty:
        behaviour['duty'] = duty
    # T-3541: the station remains the duty engine's; the day owns meals, rest and
    # visitor requests. These hours are reconstruction, not a surviving guard roster.
    if sid not in NIGHT_GUARD:
        behaviour['hours'] = list(DAY_HOURS)  # legacy readers; a day takes precedence
    home = p['_home']
    behaviour['quarters'] = home
    at = {'local_e': e, 'local_n': n, 'heading_deg': heading}
    def inside(a, b, doing):
        return {'from': a, 'to': b, 'indoors': True, 'where': home, 'doing': doing}
    def out(a, b, activity, doing, **extra):
        return {'from': a, 'to': b, 'indoors': False, 'at': at,
                'activity': activity, 'doing': doing, **extra}
    kind = (duty or {}).get('kind')
    activity = ('walk' if kind == 'beat' or route else 'talk' if kind == 'knot'
                else 'stand' if sid in NIGHT_GUARD else 'work')
    post_fields = {'duty': True}
    if kind == 'beat':
        post_fields['to_point'] = duty['to']
    elif route:
        post_fields['via'] = behaviour['route'][:-1]
        post_fields['to_point'] = behaviour['route'][-1]
    if kind == 'knot':
        post_fields['knot'] = duty['id']
    post = lambda a, b: out(a, b, activity, words, **post_fields)
    if sid in NIGHT_GUARD:
        spans = [post(0, 5.5), inside(5.5, 13, 'sleeping after the night watch'),
                 post(13, 17), inside(17, 18, 'supper in quarters'),
                 out(18, 20, 'work', 'cleaning and mending equipment'),
                 inside(20, 21, 'resting before the night watch'), post(21, 24)]
    else:
        spans = [inside(0, 5.5, 'asleep in quarters'), post(5.5, 12),
                 inside(12, 13, 'meal in quarters'), post(13, 18),
                 inside(18, 19, 'supper in quarters'),
                 out(19, 20, 'work', 'cleaning and mending equipment'),
                 out(20, 21, 'talk', 'a break with a comrade', knot=f'quarters_{home}'),
                 inside(21, 24, 'asleep in quarters')]
    cold = []
    for span in spans:
        if not span['indoors'] and not span.get('duty') and span.get('activity') == 'work':
            cold.extend([{**span, 'to': span['from'] + 0.5},
                         inside(span['from'] + 0.5, span['to'], 'mending equipment indoors in cold weather')])
        elif not span.get('duty') and span.get('activity') == 'talk':
            cold.append(inside(span['from'], span['to'], 'evening rest in quarters in cold weather'))
        elif any(word in words for word in ('garden', 'cornfield')) and span.get('duty'):
            cold.append(inside(span['from'], span['to'], 'tending stored supplies in cold weather'))
        else:
            cold.append(span)
    behaviour['day'] = [{'dates': {'months': [11, 12, 1, 2, 3]}, 'spans': cold}, {'spans': spans}]
    for variant in behaviour['day']:
        variant['note'] = 'Reconstructed daily hours and ordinary activities; liberty L-1812-everyday-routines-3541. The station and existing presence records remain.'
    seed_phase = (sum(map(ord, p['id'])) % 97) / 97
    return {
        'id': f"hi_{p['id']}_1812",
        'contract_version': 1,
        'scene': '1812',
        'person_id': p['id'],
        'appearance': {'asset_id': asset},
        'placement': {'local_e': e, 'local_n': n, 'heading_deg': heading, 'anchor': 'terrain'},
        'animation': {'clip': 'walk' if state == 'walking' else 'idle', 'loop': True, 'phase': round(seed_phase, 3)},
        'behaviour': behaviour,
        'interaction': {'selectable': True, 'radius_m': 3, 'opens': 'resident_card'},
        'lod': {'policy': 'auto'},
        'display': 'shown',
        'review_required': False,
        'provenance': {
            'grade': 'reconstructed',
            'basis': (f"Reconstructed figure of {p['name']}, {rank} of Captain Nathan Heald's company of the First Infantry "
                      f"(on the company's muster-roll to 31 May 1812, Quaife 1913 App. VIII), {words}, on the afternoon of "
                      f"14 August 1812. Where he stands and what he is doing are ours (liberty L-1812-garrison-stations-3462); his daily meals, rest and activity hours are also reconstructed (L-1812-everyday-routines-3541): "
                      f"no guard report or order book of the post survives for that day, and nothing of it is acted out. He wears "
                      + (f"{worn} (T-3523; who wears what, and how his musket is carried, are ours, liberty {GD.LIBERTY})" if worn
                         else "the company private's dress (T-3451)") + ". His face, height and build are seeded from his own name; no "
                      "picture of him is known."),
            'sources': sorted(set(['quaife_1913', 'whistler_1808_fort_dearborn_draught'] + DRESS_SOURCES + (GD.SOURCES if worn else []))),
            'liberty': 'L418',
            'seed': f"{p['id']}:1812:{sid}:20261107",
            'replaceable_by': 'A guard report, order book or morning report of the post for August 1812, which would put him at his own duty.',
        },
    }


def build():
    people = [p for p in men() if p['id'] != 'grummo_paul']
    by_station = {s[0]: s for s in STATIONS}
    used, plan = set(), {}
    for pid, sid in FIXED.items():
        plan[pid] = by_station[sid]
        used.add(sid)
    free = [s for s in STATIONS if s[0] not in used]
    for p in people:
        if p['id'] not in plan:
            plan[p['id']] = free.pop(0)
    missing = [p['id'] for p in people if p['id'] not in plan]
    assert not missing, missing
    return {f"hi_{p['id']}_1812.json": instance(p, plan[p['id']]) for p in people}, plan


def garrison_dress(people, plan):
    """T-3523: data/humans/variation/dress_1812_garrison.json, every man's and officer's dress."""
    entries = {}
    for p in people:
        rank = p['occupation']['value'].split(',')[0]
        sid = 'fatigue_2' if p['id'] == 'grummo_paul' else plan[p['id']][0]   # Grummo stands third in the rank
        entries[p['id']] = GD.dress_for(p['id'], rank, sid)
    for pid in GD.OFFICERS:
        rec, words = GD.officer_dress(pid)
        entries[pid] = ('officer_first_infantry_1812', rec, words)
    return GD.dress_file(entries)


def main(check=False):
    files, plan = build()
    # Grummo keeps his existing attested identity and placement, sharing the day model.
    grummo = json.loads((INST / f'{KEEP}.json').read_text())
    person = next(p for p in men() if p['id'] == 'grummo_paul')
    at = grummo['placement']
    station = ('fatigue_2', 'in the rank of a fatigue party drawn up on the parade', at['local_e'], at['local_n'], at['heading_deg'], 'standing', None, {'kind': 'rank', 'id': 'fatigue_party'})
    grummo['behaviour'] = instance(person, station)['behaviour']
    files[f'{KEEP}.json'] = grummo
    index_path = INST / 'index.json'
    index = json.loads(index_path.read_text())
    others = [i for i in index['instances'] if not (i.startswith('hi_') and f"{i}.json" in files)]
    # Sorted whole, so every script that writes its own instances here (this one, the town's
    # place_town.py) writes the same index.
    index = {'scene': '1812', 'instances': sorted(set(others) | {f[:-5] for f in files})}
    files['index.json'] = index
    dress = garrison_dress(men(), plan)
    stale = []
    for name, rec in files.items():
        text = json.dumps(rec, indent=2, ensure_ascii=False) + '\n'
        path = INST / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    dress_path = ROOT / 'data/humans/variation/dress_1812_garrison.json'
    dress_text = json.dumps(dress, indent=1, ensure_ascii=False) + '\n'
    if check:
        if not dress_path.exists() or dress_path.read_text() != dress_text:
            stale.append(str(dress_path.relative_to(ROOT)))
    else:
        dress_path.write_text(dress_text)
    if stale:
        raise SystemExit('stale 1812 garrison instances (rerun place.py): ' + ', '.join(stale))
    print(f"{len(files) - 1} men of Heald's company placed" + (' — current' if check else ''))


if __name__ == '__main__':
    main(check='--check' in sys.argv)
