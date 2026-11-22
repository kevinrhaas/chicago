# SPDX-License-Identifier: GPL-3.0-or-later
"""Check era eligibility and exact replacement ownership for parked vehicles (T-2979)."""
import json
import math
from wagon_covered.check import COVERED_MODELS, validate_covered
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# T-3558: the photographic farm-box wagon the 1835 moving teams draw, parked at original
# farm-box stands; every other 1835 farm-box or covered yard vehicle is retired.
FARM_BOX = 'farm_box_w01'
# T-3686, the owner's ruling of 2026-11-21 ("Yes, a labelled stand-in"): the five hacks the
# Sherman House stereograph (LOC 1s12371) shows on Clark Street are drawn with the 1893
# catalogue Brougham, labelled as a stand-in. Only these five rows, at that stand, may do so.
HACK_STAND = tuple(f'hack_stand_clark_court_house_{i}' for i in range(1, 6))
HACK_SOURCES = ['loc_stereo_1s12371_sherman_house', 'studebaker_1893_illustrated_souvenir']


def validate(record):
    assert set(record['scenes']) == {'1835', '1871', '1904'}, 'Only the explicitly authored eras may draw these models'
    original = json.loads((ROOT/'data/yard/town_trade_goods.json').read_text())
    originals = {w['id']: w for w in original['wagons']}
    ids, replaced = set(), set()
    for year, rows in record['scenes'].items():
        for row in rows:
            assert row['id'] not in ids, 'Duplicate vehicle instance'
            ids.add(row['id'])
            assert len(row['at_local_enu_m']) == 2 and all(math.isfinite(x) for x in row['at_local_enu_m'])
            assert math.isfinite(row['bearing_deg'])
            stand_in = year == '1871' and row['id'] in HACK_STAND
            assert row['liberty'] == ('L-1871-streetscape' if stand_in else 'L-brougham-parked-2794' if row['model'] == 'studebaker_brougham_1893' else 'L-covered-wagons-2980' if row['model'] in COVERED_MODELS
                                      else 'L-1835-parked-farm-box' if row['model'] == FARM_BOX else 'L-parked-vehicles-2979')
            assert row['note'] and row['location']
            for source in row['source_ids']:
                assert (ROOT/f'data/sources/{source}.json').is_file(), ('Missing source', source)
            if row['model'] in ('wagon_w01', FARM_BOX) or row['model'] in COVERED_MODELS:
                assert year == '1835' and row['replaces'] not in replaced, 'Wrong era or duplicate replacement'
                replaced.add(row['replaces'])
                old = originals[row['replaces']]
                kind = 'covered' if row['model'] in COVERED_MODELS else 'farm_box'
                assert old['kind'] == kind, 'Do not change the original vehicle kind'
                assert row['at_local_enu_m'] == old['at_local_enu_m'], 'Replacement must keep its existing stand'
                assert row['bearing_deg'] == old['bearing_deg'], 'Replacement must keep its existing bearing'
                assert row['belongs_to'] == old.get('belongs_to'), 'Do not invent a vehicle owner'
            elif row['model'] == 'studebaker_brougham_1893' and stand_in:
                assert row.get('belongs_to') is None and not row.get('replaces'), 'A hack at the stand has no owner claim'
                assert row['source_ids'] == HACK_SOURCES, 'The stand is the stereograph\'s; the form is the catalogue\'s'
                assert 'stand-in' in row['note'] and 'reconstructed' in row['note'], 'The stand-in says so on its card'
                e, n = row['at_local_enu_m']
                assert 570 < e < 578 and -315 < n < -270, 'Clark Street, along the Court House Square, south of Randolph'
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
        assert spec['file'] == 'transport/parked-brougham/brougham-near-delivery-v1.glb'
        assert spec['wheel_contacts_m'] == [[-.67,-1.15],[.67,-1.15],[-.67,1.15],[.67,1.15]]
        assert spec['static_support_contacts_m'] == [[-.0325,0,3.725],[.0325,0,3.725],[-.0325,0,3.825],[.0325,0,3.825]]
        ref = spec['design_reference']
        assert ref['confidence'] == 'attested' and ref['sources'] == ['studebaker_1893_illustrated_souvenir']
        assert spec['delivery_lods'] == {'near':'transport/parked-brougham/brougham-near-delivery-v1.glb','mid':'transport/parked-brougham/brougham-mid-delivery-v1.glb','runtime_distance_selection_enabled':True}
        assert (ROOT/'renderers/web'/spec['delivery_lods']['mid']).is_file(), 'Missing genuine Brougham mid'
        assert sum(r['model'] == 'studebaker_brougham_1893' for r in record['scenes']['1904']) == 1
        # The obsolete display is intentionally removed; its model and assets remain.
        generic = [r for r in record['scenes']['1904'] if r['id'] == 'prairie_parked_carriage']
        assert len(generic) == 0, 'Obsolete 1904 C02 prototype display must remain removed'
        assert record['models']['carriage_c02']['file'] == 'transport/parked-carriage/carriage-c02.glb', 'Keep legacy model and asset available'
        assert len(record['scenes']['1835']) == 8 and len(record['scenes']['1904']) == 1, 'Eight photographic wagons and one replacement carriage'
        assert not any(r['model'] == 'carriage_c02' for rows in record['scenes'].values() for r in rows), 'No prototype display reintroduced in another era'
        assert not record['models']['carriage_c02'].get('design_reference'), 'Catalogue must not retrospectively brand generic C02'
    validate_covered(record, originals, ROOT)
    # T-3558: no 1835 row stays on the procedural W01 model; the farm-box model is the master.
    if FARM_BOX in record['models']:
        spec = record['models'][FARM_BOX]
        assert spec['file'] == 'transport/farm-box-master/farm-box-near.glb' and spec['file_light'] == 'transport/farm-box-master/farm-box-mid.glb'
        assert not spec.get('paint') and not spec.get('support_file'), 'The parked farm box is the photographed master, unpainted'
        assert not any(r['model'] == 'wagon_w01' for r in record['scenes']['1835']), 'Procedural W01 stands are now the farm-box master'
    retired = record.get('retired_yard_wagons', {})
    assert set(retired) <= {'_doc', '1835'}, 'Only the 1835 yard retires vehicles'
    gone = retired.get('1835', [])
    assert len(gone) == len(set(gone)), 'Duplicate retired vehicle'
    for wid in gone:
        assert wid in originals, ('Retired vehicle is not a yard record', wid)
        assert originals[wid]['kind'] in ('farm_box', 'covered'), 'Carts are not retired'
        assert wid not in replaced, 'A replaced vehicle cannot also be retired'
    # Every 1835 farm-box and covered yard vehicle is either photographic or retired.
    wagons = {w['id'] for w in original['wagons'] if w['kind'] in ('farm_box', 'covered')}
    if gone:
        assert wagons == replaced | set(gone), ('Unaccounted yard wagons', sorted(wagons - replaced - set(gone)))
    return len(ids)


if __name__ == '__main__':
    record = json.loads((ROOT/'data/transport/parked/placements.json').read_text())
    count=validate(record)
    import copy
    obsolete=json.loads((ROOT/'tools/transport/brougham/obsolete-c02-placement.json').read_text())
    broken=copy.deepcopy(record);broken['scenes']['1904'].append(obsolete)
    try:validate(broken)
    except AssertionError:pass
    else:raise AssertionError('Obsolete prototype reintroduction negative control failed')
    print(f'PARKED PLACEMENTS PASS — {count} instances; eight photographic 1835 wagons at original stands, the rest retired; one carriage at its unchanged qualified stand; prototype reintroduction refused')
