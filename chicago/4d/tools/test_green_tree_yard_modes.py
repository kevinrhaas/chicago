#!/usr/bin/env python3
"""The same canonical shoulder flag must control the competing yard reading."""
import copy
import json
from pathlib import Path
import generate_yard_goods as yard

root = Path(__file__).resolve().parents[1]
source = json.loads((root / 'data/sidecars/1835/green_tree_tavern.json').read_text())
assert source['attributes']['enclosed_left_annex']['value']['shoulder_enclosed'] is True
polygon = source['footprint']['polygon']
place = source['placement']
closed = yard._green_tree_wagon_shed(source, place, polygon, [])
assert closed[0] == [] and closed[1] == []
assert len(closed[2]) == 1 and closed[2][0]['structure_id'] == 'green_tree_tavern'
assert 'canonical enclosed shoulder' in closed[2][0]['why']
for state in (False, None):
    opened = copy.deepcopy(source)
    value = opened['attributes']['enclosed_left_annex']['value']
    if state is None:
        del value['shoulder_enclosed']
    else:
        value['shoulder_enclosed'] = state
    sheds, wagons, refused = yard._green_tree_wagon_shed(opened, place, polygon, [])
    assert len(sheds) == 1 and len(wagons) == 1 and refused == []
    shed, wagon = sheds[0], wagons[0]
    assert shed['id'] == 'green_tree_tavern_wagon_shed'
    assert wagon['under_shed'] == shed['id'] and wagon['tilt'] is True
    assert wagon['at_local_enu_m'] == shed['at_local_enu_m']
    assert shed['confidence'] == wagon['confidence'] == 'reconstructed'
    assert shed['length_m'] >= 3.05 and shed['depth_m'] >= 3.2
    assert shed['head_m'] > shed['eave_m'] >= 0.95 + 0.55 + 1.10
    # A genuinely obstructed bay must still be declined in the open mode.
    e, n = shed['at_local_enu_m']
    blocked = yard._green_tree_wagon_shed(opened, place, polygon, [
        ('blocking-neighbour', [(e-10, n-10), (e+10, n-10), (e+10, n+10), (e-10, n+10)])])
    assert blocked[0] == [] and blocked[1] == [] and len(blocked[2]) == 1
print('Green Tree yard: canonical enclosed, false/absent open, and obstructed-open controls pass')
