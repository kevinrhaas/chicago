#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Roster identity, portrait and seasonal routine contract for Prairie Avenue."""
import json
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    people = read('data/sidecars/1904/people.json')['people']
    cast = read('data/humans/prairie_1904.json')['people']
    roster = read('data/humans/inside_1904.json')
    inside, care = roster['people'], roster['care']
    ids = {p['id'] for p in people}
    assert len(cast) == len(ids) and {p['person'] for p in cast} == ids
    assert len({p['person'] for p in inside}) == len(inside)
    active = {p['person'] for p in cast if p['status'] == 'ready'}
    assert active == {p['person'] for p in inside}
    for p in cast:
        if p['status'] in ('alias', 'collective', 'absent', 'household_care'):
            assert p['person'] not in active
        if p['status'] == 'alias':
            assert p['canonical'] in ids and p['canonical'] != p['person']
    doors = {d['id']: (s['structure'], d) for s in read('data/humans/doors_1904.json')['structures'] for d in s['doors']}
    for p in inside:
        assert p['door'] in doors and doors[p['door']][0] == p['home']
        assert (ROOT / ('assets/humans/web/' + p['asset_id'] + '.lod0.glb')).exists(), p['asset_id']
        for day in p['day']:
            spans = day['spans']
            assert spans[0]['from'] == 0 and spans[-1]['to'] == 24
            assert all(a['to'] == b['from'] for a, b in zip(spans, spans[1:]))
            assert all(s['from'] < s['to'] for s in spans)
            assert any(not s['indoors'] for s in spans)
            assert any(s.get('activity') == 'talk' for s in spans)
        assert len(p['day']) == 3 and 'dates' not in p['day'][-1]
        winter = sum(s['to'] - s['from'] for s in p['day'][0]['spans'] if not s['indoors'])
        summer = sum(s['to'] - s['from'] for s in p['day'][-1]['spans'] if not s['indoors'])
        assert winter < summer
    young = [p for p in inside if p.get('age_1904', 18) < 18]
    assert len(young) == 35 and len(care) == 5
    assert not any(p['status'] == 'child_mesh_pending' for p in cast)
    byid = {p['person']: p for p in cast}
    admission = read('data/humans/role_reviews/prairie_children_1904.json')
    assert admission['approval'] == 'Approve these five prototypes'
    roles = {r['asset_id'] for r in admission['roles']}
    axes = read('data/humans/variation/axes.json')['assets']
    for p in young + care:
        age = p['age_1904']
        assert p['caregivers'] and len(set(p['caregivers'])) == len(p['caregivers'])
        for aid in p['caregivers']:
            adult = byid[aid]
            assert adult['home'] == p['home'] and adult['status'] in ('ready', 'existing')
            assert adult['age_1904'] is None or adult['age_1904'] >= 18
        assert p['supervised'] == (age < 12)
        if p.get('care_only'):
            assert age < 2 and 'asset_id' not in p
            assert all(s['indoors'] and s['where'] == p['home'] for day in p['day'] for s in day['spans'])
            assert p['day'][0]['spans'][0]['from'] == 0 and p['day'][0]['spans'][-1]['to'] == 24
        else:
            assert p['asset_id'] in roles and axes[p['asset_id']]['age_drive'] is False
            assert ('toddler' in p['asset_id']) == (age < 5)
            assert p['asset_id'].startswith('teen_') == (age >= 12)
            assert 'office' not in json.dumps(p['day']) and 'business' not in json.dumps(p['day'])
            looks = read('data/humans/variation/looks/' + p['person'] + '.json')
            assert 'moustache' not in looks['hair']['facial']
            assert axes[p['asset_id']]['height_clip'][0] <= looks['height_scale'] <= axes[p['asset_id']]['height_clip'][1]
            assert p['role_review'] == 'data/humans/role_reviews/prairie_children_1904.json'
    for p in read('docs/RESEARCH/prairie-portraits-3546/portraits.json')['portraits']:
        assert p['person_id'] in ids
        portrait = read('data/humans/variation/portraits/' + p['person_id'] + '.json')
        actor = next((a for a in inside if a['person'] == p['person_id']), None)
        if actor:
            assert actor['asset_id'] == portrait['card']['body'], f"Portrait/body mismatch: {p['person_id']}"
        for k in ('portrait', 'model'):
            assert (ROOT / portrait['card'][k]).is_file()
    coverage = read('docs/RESEARCH/prairie-portraits-3546/search-coverage.json')
    # Every listed record is audited; a search failure must remain a failure.
    rows = coverage.get('people', coverage.get('results', []))
    assert len(rows) == len(ids), 'search coverage must include every card'
    # Regression for the canonical build's missing skin material, before Blender
    # starts: every child clothing palette must still bind the textured body.
    from human_child_1904 import ROLES, validate_palette
    for role, (_, _, kind) in ROLES.items():
        recipe = read(f'data/humans/recipes/{role}.json')
        validate_palette(recipe, kind)
        broken = copy.deepcopy(recipe)
        del broken['colors_linear_rgba']['skin']
        try:
            validate_palette(broken, kind)
        except ValueError:
            pass
        else:
            raise AssertionError(f'{role}: missing skin material was accepted')
    print(f'ok Prairie Avenue: {len(ids)} cards, {len(inside)} distinct lazy residents, complete seasonal days and canonical doors')


if __name__ == '__main__':
    main()
