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
# Both pre-existing and new separately validated families must retain the same covered subset.
without_brougham = deepcopy(record)
without_brougham['models'].pop('studebaker_brougham_1893', None)
for rows in without_brougham['scenes'].values():
    rows[:] = [row for row in rows if row['model'] != 'studebaker_brougham_1893']
assert validate_covered(without_brougham, originals, ROOT) == 2
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
refuse('unknown family cannot use optional Brougham allowance', lambda c, o: c['models'].__setitem__('unreviewed_family', deepcopy(c['models']['carriage_c02'])))
refuse('required generic family cannot disappear', lambda c, o: c['models'].pop('carriage_c02'))


def wrong_era(candidate, old):
    row = covered(candidate)
    candidate['scenes']['1835'].remove(row)
    candidate['scenes']['1904'].append(row)


refuse('no covered backdating/era substitution', wrong_era)


def check_original_chart_contract(root):
    """Cheap actual authored-reader refusals; no numerical authoring or generator."""
    import shutil
    import struct
    import tempfile
    from wagon_parked.authored_charts import OriginalCharts, read_original_charts
    directory = root/'assets/authored/transport/wagon_parked/charts'
    charts = read_original_charts(directory)
    assert len(charts.attributes) == 23 and len(charts.mapping) == 158
    payload = (directory/'original-w01-charts.bin').read_bytes()
    mapping = (directory/'original-w01-charts.mapping.json').read_bytes()
    rejected = []

    def refusal(label, operation):
        try:
            operation()
        except (ValueError, FileNotFoundError):
            rejected.append(label)
            return
        raise AssertionError('Original charts accepted '+label)

    with tempfile.TemporaryDirectory(prefix='original-w01-chart-controls-') as temp:
        copied = Path(temp)
        for filename in ['original-w01-charts.json', 'original-w01-charts.mapping.json']:
            shutil.copyfile(directory/filename, copied/filename)
        refusal('missing payload', lambda: read_original_charts(copied))
        corrupted = bytearray(payload)
        # Changing only a zero's sign must also fail the exact authored-byte pin.
        zero = next(k for k in range(0, len(payload), 4)
                    if struct.unpack_from('<f', payload, k)[0] == 0)
        corrupted[zero+3] ^= 0x80
        (copied/'original-w01-charts.bin').write_bytes(corrupted)
        refusal('changed signed-zero payload', lambda: read_original_charts(copied))

    def malformed(label, mutate):
        candidate = deepcopy(charts.contract)
        mutate(candidate)
        refusal(label, lambda: OriginalCharts(candidate, payload, mapping))

    malformed('duplicate batch', lambda c: c['batches'].__setitem__(1, deepcopy(c['batches'][0])))
    malformed('missing batch', lambda c: c['batches'].pop())
    malformed('batch count mismatch', lambda c: c['batches'][0].update(vertex_count=c['batches'][0]['vertex_count']+3))
    for key in ['hardware_glb_sha256', 'authored_parts_sha256', 'material_recipe_sha256']:
        malformed(key+' mismatch', lambda c, k=key: c['source_inputs'].__setitem__(k, '0'*64))
    malformed('changed owner name', lambda c: c['batches'][0]['parts'][0].update(name='different original part'))
    malformed('changed owner frame', lambda c: c['batches'][0]['parts'][0].update(frame='vehicle_other_frame'))
    malformed('changed owner material', lambda c: c['batches'][0]['parts'][0].update(material=4))
    malformed('changed frozen accessor bound', lambda c: c['batches'][0]['attributes']['TEXCOORD_0']['min'].__setitem__(0, 1000.0))
    assert len(rejected) == 12
    print('ORIGINAL CHART CONTRACT PASS — 23 original batches; '+str(len(rejected))+' actual reader negative refusals')

check_original_chart_contract(ROOT)
print('COVERED IDENTITY PASS — two reviewed originals; '+str(len(cases))+' actual negative refusals')
