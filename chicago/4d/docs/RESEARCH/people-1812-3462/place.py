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
forks. Nothing of that day is acted out: no council, no giving out of the goods, no
destruction of the ammunition. Which man stands where follows the roll's order within a rank;
the four married men stand near the quarters T-3461 gives their families. Sergeants', corporals'
and musicians' distinctions (epaulettes, sashes, the musicians' coats) are not drawn: every man
wears the private's dress, and his card's rank says what he was.

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-3462/place.py [--check]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INST = ROOT / 'data/humans/instances/1812'
COMPANY = ROOT / 'data/residents_1812/households'
ASSET = 'private_first_infantry_1812'
KEEP = 'hi_heald_company_private_1812'      # Paul Grummo, placed by T-3452
DRESS_SOURCES = ['loc_ogden_1888_infantry_artillery_1802_1810', 'met_krimmel_1813_philadelphia_soldiery',
                 'us_1812_rules_and_articles_albany', 'us_1814_military_laws_and_regulations']

# (station id, words, e, n, heading, state, route or None)
# e/n are the scene's local metres; heading clockwise from grid north.
STATIONS = [
    # the main gate, under a sergeant (outside the outer pickets, n < 204)
    ('gate_sergeant', 'in command of the guard before the main gate', 1149.6, 200.2, 190, 'standing', None),
    ('gate_west', 'on guard at the main gate, west of the passage', 1147.4, 202.7, 180, 'standing', None),
    ('gate_east', 'on guard at the main gate, east of the passage', 1151.8, 202.7, 180, 'standing', None),
    ('magazine', 'on sentry before the magazine', 1147.1, 229.4, 180, 'standing', None),
    # the parade
    ('parade_drum', 'on the parade near the flagstaff', 1150.3, 223.6, 110, 'standing', None),
    ('parade_fife', 'on the parade near the flagstaff', 1149.6, 224.9, 140, 'standing', None),
    ('parade_drum2', 'at the north range door', 1154.6, 229.9, 190, 'standing', None),
    ('parade_fife2', 'at the north range door', 1156.0, 229.7, 160, 'standing', None),
    ('sw_door_a', 'at the door of the soldiers\' barracks west of the gate', 1145.0, 212.3, 10, 'standing', None),
    ('sw_door_b', 'at the door of the soldiers\' barracks west of the gate', 1146.3, 212.7, 330, 'standing', None),
    ('se_door_a', 'at the door of the soldiers\' barracks east of the gate', 1153.4, 212.4, 20, 'standing', None),
    ('se_door_b', 'at the door of the soldiers\' barracks east of the gate', 1154.8, 212.6, 300, 'standing', None),
    ('se_door_c', 'at the door of the soldiers\' barracks east of the gate', 1156.3, 212.3, 340, 'standing', None),
    ('east_a', 'on the parade before the commanding officer\'s quarters', 1158.6, 216.0, 270, 'standing', None),
    ('east_b', 'on the parade before the commanding officer\'s quarters', 1159.2, 217.4, 245, 'standing', None),
    ('east_c', 'on the parade before the commanding officer\'s quarters', 1157.9, 217.8, 120, 'standing', None),
    ('west_a', 'on the parade before the officers\' barracks', 1143.4, 221.8, 90, 'standing', None),
    ('west_b', 'on the parade before the officers\' barracks', 1143.7, 223.3, 105, 'standing', None),
    ('parade_c', 'on the parade', 1150.0, 216.6, 40, 'standing', None),
    ('parade_d', 'on the parade', 1155.2, 224.6, 300, 'standing', None),
    ('parade_e', 'on the parade', 1146.6, 226.6, 140, 'standing', None),
    ('parade_f', 'on the parade', 1157.6, 226.2, 220, 'standing', None),
    ('parade_g', 'on the parade', 1154.0, 217.3, 350, 'standing', None),
    ('parade_walk_a', 'crossing the parade between the barracks and the north range', 1153.0, 214.0, 0, 'walking',
     [(1155.4, 228.6), (1157.0, 227.8), (1154.8, 214.6)]),
    ('parade_walk_b', 'walking the parade', 1145.4, 215.0, 0, 'walking',
     [(1145.4, 227.4), (1148.4, 228.2), (1148.4, 215.0)]),
    # the families' quarters (T-3461 puts them there; reconstructed)
    ('holt_quarters', 'before the small house in the south-west corner', 1142.9, 212.4, 300, 'standing', None),
    ('simmons_quarters', 'before the small house in the north-east corner', 1160.4, 230.2, 120, 'standing', None),
    ('corbin_quarters', 'at the door of the soldiers\' barracks west of the gate', 1143.6, 212.6, 30, 'standing', None),
    ('needs_quarters', 'at the door of the soldiers\' barracks east of the gate', 1151.8, 212.8, 350, 'standing', None),
    # outside the pickets
    ('blockhouse_se', 'outside the pickets by the south-east blockhouse', 1172.0, 205.4, 100, 'standing', None),
    ('river_bank_a', 'on the river bank north of the fort, looking across to the Kinzie house', 1146.0, 242.0, 0, 'standing', None),
    ('river_bank_b', 'on the river bank north of the fort', 1152.4, 242.4, 345, 'standing', None),
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
    ('river_walk', 'walking the river bank', 1138.0, 243.0, 0, 'walking',
     [(1158.0, 243.5), (1162.0, 241.5), (1140.0, 241.0)]),
    ('forks_cornfield_a', 'at work in the company\'s cornfield at the forks', 162.0, -240.0, 20, 'working', None),
    ('forks_cornfield_b', 'at work in the company\'s cornfield at the forks', 171.0, -247.0, 200, 'working', None),
    ('forks_walk', 'walking back from the cornfield at the forks', 158.0, -232.0, 0, 'walking',
     [(190.0, -215.0), (160.0, -230.0)]),
]

# Who goes where: by rank, then the roll's order; families' men by their quarters.
FIXED = {'holt_isaac': 'gate_sergeant', 'simmons_john': 'simmons_quarters', 'corbin_fielding': 'corbin_quarters',
         'needs_john': 'needs_quarters', 'hays_otho': 'holt_quarters', 'crozier_john': 'magazine',
         'griffith_william': 'east_a', 'forth_thomas': 'gate_west', 'bowen_joseph': 'gate_east',
         'burnett_george': 'parade_fife', 'smith_john_jr': 'parade_fife2', 'mcpherson_hugh': 'parade_drum',
         'hamilton_john': 'parade_drum2'}


def men():
    hh = [json.loads(p.read_text()) for p in sorted(COMPANY.glob('hh_*_1812.json'))]
    out = []
    for h in hh:
        for p in h['persons']:
            occ = (p.get('occupation') or {}).get('value', '')
            if "heald's company" in occ.lower() and not occ.startswith(('captain', 'second lieutenant', 'ensign', "surgeon")):
                out.append(p)
    return out


def instance(p, st):
    sid, words, e, n, heading, state, route = st
    rank = p['occupation']['value'].split(',')[0]
    behaviour = {'state': state}
    if route:
        behaviour['route'] = [{'local_e': a, 'local_n': b} for a, b in route]
    seed_phase = (sum(map(ord, p['id'])) % 97) / 97
    return {
        'id': f"hi_{p['id']}_1812",
        'contract_version': 1,
        'scene': '1812',
        'person_id': p['id'],
        'appearance': {'asset_id': ASSET},
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
                      f"14 August 1812. Where he stands and what he is doing are ours (liberty L-1812-garrison-stations-3462): "
                      f"no guard report or order book of the post survives for that day, and nothing of it is acted out. He wears "
                      f"the company private's dress (T-3451)" + ('' if rank == 'private' else
                      f"; the marks of a {rank} are not drawn") + ". His face, height and build are seeded from his own name; no "
                      "picture of him is known."),
            'sources': sorted(set(['quaife_1913', 'whistler_1808_fort_dearborn_draught'] + DRESS_SOURCES)),
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
    return {f"hi_{p['id']}_1812.json": instance(p, plan[p['id']]) for p in people}


def main(check=False):
    files = build()
    index_path = INST / 'index.json'
    index = json.loads(index_path.read_text())
    others = [i for i in index['instances'] if not (i.startswith('hi_') and f"{i}.json" in files)]
    index = {'scene': '1812', 'instances': others + sorted(f[:-5] for f in files)}
    files['index.json'] = index
    stale = []
    for name, rec in files.items():
        text = json.dumps(rec, indent=2, ensure_ascii=False) + '\n'
        path = INST / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    if stale:
        raise SystemExit('stale 1812 garrison instances (rerun place.py): ' + ', '.join(stale))
    print(f"{len(files) - 1} men of Heald's company placed" + (' — current' if check else ''))


if __name__ == '__main__':
    main(check='--check' in sys.argv)
