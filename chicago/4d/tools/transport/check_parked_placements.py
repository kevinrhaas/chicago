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
            assert row['liberty'] == ('L-covered-wagons-2980' if row['model'] in COVERED_MODELS else 'L-parked-vehicles-2979')
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
            else:
                assert row['model'] == 'carriage_c02' and year == '1904', 'Never backdate the enclosed carriage'
                assert not row.get('replaces') and row.get('belongs_to') is None
    for model in record['models'].values():
        path = model['file']
        assert path.startswith('transport/') and '..' not in Path(path).parts
        assert (ROOT/'renderers/web'/path).is_file(), ('Missing model', path)
        assert len(model['wheel_contacts_m']) == 4
        assert all(len(p) == 2 and all(math.isfinite(x) for x in p) for p in model['wheel_contacts_m'])
    validate_covered(record, originals, ROOT)
    return len(ids)


if __name__ == '__main__':
    record = json.loads((ROOT/'data/transport/parked/placements.json').read_text())
    print(f'PARKED PLACEMENTS PASS — {validate(record)} instances; exact prior wagon stands; explicit scene eligibility')
