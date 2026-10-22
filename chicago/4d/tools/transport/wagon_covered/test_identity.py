# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual bad-kind, identity, yoke and placement refusals for the covered subset."""
from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wagon_covered.check import validate_covered

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT/'data/transport/parked/placements.json').read_text())
originals = {r['id']: r for r in json.loads((ROOT/'data/yard/town_trade_goods.json').read_text())['wagons']}
assert validate_covered(record, originals, ROOT) == 2
cases = []


def refuse(name, mutate):
    candidate, old = deepcopy(record), deepcopy(originals)
    mutate(candidate, old)
    try:
        validate_covered(candidate, old, ROOT)
    except (AssertionError, KeyError):
        cases.append(name)
        return
    raise AssertionError('Did not refuse: '+name)


def covered(candidate):
    return next(r for r in candidate['scenes']['1835'] if r['model'] == 'covered_w01_western_blue')


target = 'town_wagon_western_hotel_wagon_yard_1'
for kind in ['cart', 'farm_box']:
    refuse('original '+kind+' cannot become covered', lambda c, o, k=kind: o[target].update(kind=k))
refuse('original laid-by yoke cannot disappear', lambda c, o: o[target].update(yoke=False))
refuse('existing stand cannot move', lambda c, o: covered(c).update(at_local_enu_m=[-136.04, -291]))
refuse('bearing cannot change', lambda c, o: covered(c).update(bearing_deg=356.3))
refuse('no unreviewed individual substitution', lambda c, o: covered(c).update(replaces='town_wagon_western_hotel_wagon_yard_2'))
refuse('no duplicate covered replacement', lambda c, o: c['scenes']['1835'].append(deepcopy(covered(c))))


def wrong_era(candidate, old):
    row = covered(candidate)
    candidate['scenes']['1835'].remove(row)
    candidate['scenes']['1904'].append(row)


refuse('no covered backdating/era substitution', wrong_era)
print('COVERED IDENTITY PASS — two reviewed originals; '+str(len(cases))+' actual negative refusals')
