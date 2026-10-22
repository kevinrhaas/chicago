# SPDX-License-Identifier: GPL-3.0-or-later
"""Check era eligibility and exact replacement ownership for parked vehicles (T-2979)."""
import json
import math
from wagon_covered.check import COVERED_MODELS, validate_covered
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate(record):
    assert set(record['scenes']) == {'1835', '1904'}, 'Only the explicitly authored eras may draw these models'
    original = json.loads((ROOT/'data/yard/town_trade_goods.json').read_text())
    originals = {w['id']: w for w in original['wagons']}
    ids, replaced = set(), set()
    for year, rows in record['scenes'].items():
        for row in rows:
            assert row['id'] not in ids, 'Duplicate vehicle instance'
            ids.add(row['id'])
            assert len(row['at_local_enu_m']) == 2 and all(math.isfinite(x) for x in row['at_local_enu_m'])
            assert math.isfinite(row['bearing_deg'])
            assert row['liberty'] == ('L-brougham-parked-2794' if row['model'] == 'studebaker_brougham_1893' else 'L-covered-wagons-2980' if row['model'] in COVERED_MODELS else 'L-parked-vehicles-2979')
            assert row['note'] and row['location']
            for source in row['source_ids']:
                assert (ROOT/f'data/sources/{source}.json').is_file(), ('Missing source', source)
            if row['model'] == 'wagon_w01' or row['model'] in COVERED_MODELS:
                assert year == '1835' and row['replaces'] not in replaced, 'Wrong era or duplicate replacement'
                replaced.add(row['replaces'])
                old = originals[row['replaces']]
                kind = 'covered' if row['model'] in COVERED_MODELS else 'farm_box'
                assert old['kind'] == kind, 'Do not change the original vehicle kind'
                assert row['at_local_enu_m'] == old['at_local_enu_m'], 'Replacement must keep its existing stand'
                assert row['bearing_deg'] == old['bearing_deg'], 'Replacement must keep its existing bearing'
                assert row['belongs_to'] == old.get('belongs_to'), 'Do not invent a vehicle owner'
            elif row['model'] == 'studebaker_brougham_1893':
                assert year == '1904' and row['id'] == 'prairie_parked_studebaker_brougham', 'Catalogue type never backdated or aliased'
                assert row.get('belongs_to') is None and not row.get('replaces'), 'No owner claim or existing C02 rebranding'
                assert row['at_local_enu_m'] == [1397.9, -3240.0] and row['bearing_deg'] == 178.99, 'Explicit separately qualified reconstructed stand'
                assert row['source_ids'] == ['studebaker_1893_illustrated_souvenir']
            else:
                assert row['model'] == 'carriage_c02' and year == '1904', 'Never backdate the enclosed carriage'
                assert not row.get('replaces') and row.get('belongs_to') is None
    for model in record['models'].values():
        path = model['file']
        assert path.startswith('transport/') and '..' not in Path(path).parts
        assert (ROOT/'renderers/web'/path).is_file(), ('Missing model', path)
        assert len(model['wheel_contacts_m']) == 4
        assert all(len(p) == 2 and all(math.isfinite(x) for x in p) for p in model['wheel_contacts_m'])
    if 'studebaker_brougham_1893' in record['models']:
        spec = record['models']['studebaker_brougham_1893']
        assert spec['file'] == 'transport/parked-brougham/brougham-near.glb'
        assert spec['wheel_contacts_m'] == [[-.67,-1.15],[.67,-1.15],[-.67,1.15],[.67,1.15]]
        assert spec['static_support_contacts_m'] == [[-.0325,0,3.725],[.0325,0,3.725],[-.0325,0,3.825],[.0325,0,3.825]]
        ref = spec['design_reference']
        assert ref['confidence'] == 'attested' and ref['sources'] == ['studebaker_1893_illustrated_souvenir']
        assert spec['delivery_lods'] == {'near':'transport/parked-brougham/brougham-near.glb','runtime_distance_selection_enabled':False}
        assert sum(r['model'] == 'studebaker_brougham_1893' for r in record['scenes']['1904']) == 1
        # The pre-existing unidentified reconstruction remains separate at its exact stand.
        generic = [r for r in record['scenes']['1904'] if r['id'] == 'prairie_parked_carriage']
        assert len(generic) == 1 and generic[0]['model'] == 'carriage_c02'
        assert generic[0]['at_local_enu_m'] == [1397.6,-3228.2] and generic[0]['bearing_deg'] == 178.99
        assert not record['models']['carriage_c02'].get('design_reference'), 'Catalogue must not retrospectively brand generic C02'
    validate_covered(record, originals, ROOT)
    return len(ids)


if __name__ == '__main__':
    record = json.loads((ROOT/'data/transport/parked/placements.json').read_text())
    print(f'PARKED PLACEMENTS PASS — {validate(record)} instances; exact prior wagon stands; explicit scene eligibility')
