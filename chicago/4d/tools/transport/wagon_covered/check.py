# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded identity, kind, provenance and unchanged-ground checks for T-2980."""
import hashlib
import json
import struct

COVERED_MODELS = {'covered_w01_western_blue', 'covered_w01_wolfpoint_oak'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_covered(record, originals, root):
    source = json.loads((root/'assets/authored/transport/wagon_covered/SOURCE.json').read_text())
    recipe = json.loads((root/'data/transport/parked/covered-w01.json').read_text())
    yard_source = (root/'renderers/web/js/yard.js').read_text()
    for contract in source['original_yard_seed_contracts'].values():
        start = yard_source.index(contract['start'])
        if 'end' in contract:
            end = yard_source.index(contract['end'], start)+len(contract['end'])
        else:
            end = yard_source.index('{', start)+1
            depth = 1
            while depth:
                if yard_source[end] == '{': depth += 1
                elif yard_source[end] == '}': depth -= 1
                end += 1
        assert hashlib.sha256(yard_source[start:end].encode()).hexdigest() == contract['sha256'], 'Original seeded finish contract changed; re-audit its legacy colors'
    # This checker owns the covered subset. Keep every existing required family,
    # allow only the separately validated named Brougham addition, reject all others.
    required_models = {'wagon_w01', 'carriage_c02'} | COVERED_MODELS
    assert required_models <= set(record['models']) <= required_models | {'studebaker_brougham_1893'}, 'Unknown or missing model family'
    variants = {v['asset_id']: v for v in recipe['variants']}
    products = {v['model']: v for v in source['variants']}
    assert set(variants) == set(products) == COVERED_MODELS, 'Only two reviewed covered variants'
    proof = source['actual_terrain_qualification']
    assert proof['epoch'] == 'e1834_harbor_cut'
    assert len(proof['data_sha256']) == 2, 'Need actual terrain meta and binary pins'
    for path, expected in proof['data_sha256'].items():
        relative = path.removeprefix('chicago/4d/')
        assert relative.startswith('data/terrain/epochs/e1834_harbor_cut/heightfield.')
        assert digest(root/relative) == expected, 'Terrain changed; requalify exact existing stands'
    stands = {s['id']: s for s in proof['stands']}
    seen = set()
    for year, rows in record['scenes'].items():
        for row in rows:
            if row['model'] not in COVERED_MODELS:
                continue
            model = row['model']
            assert year == '1835' and model not in seen, 'Wrong era or duplicate covered variant'
            seen.add(model)
            variant, product = variants[model], products[model]
            old = originals[row['replaces']]
            assert old['kind'] == variant['kind'] == 'covered' and old.get('tilt') is True, 'Covered kind required'
            assert row['replaces'] == variant['id'] == product['legacy_id'], 'Original individual identity required'
            assert row['at_local_enu_m'] == old['at_local_enu_m'] and row['bearing_deg'] == old['bearing_deg']
            assert row['belongs_to'] == old.get('belongs_to'), 'No invented owner'
            for key in ['at_local_enu_m', 'bearing_deg', 'belongs_to', 'in_enclosure', 'under_shed']:
                assert variant.get(key) == old.get(key), 'Original covered context changed: '+key
            assert row['source_ids'] == [], 'No source attests this individual invented wagon'
            assert row['liberty'] == 'L-covered-wagons-2980'
            assert old.get('yoke', False) == variant['yoke'] == product['contains_laid_by_yoke'], 'Preserve laid-by yoke'
            coat = variant['coat']
            seed = '|'.join(['wagon', old['id'], *[format(v, '.15g') for v in old['at_local_enu_m']]])
            hashed = 2166136261
            for char in seed:
                hashed = ((hashed ^ ord(char)) * 16777619) & 0xffffffff
            assert coat['seedText'] == product['source_seed_text'] == seed
            assert coat['seedUint32'] == hashed, 'Do not reseed by replacement asset or rounded coordinates'
            for key in ['ageScalar', 'canvasScalar', 'scheme']:
                assert coat[key] == product[key], 'Original finish/age changed'
            stand = stands[old['id']]
            assert stand['at_local_enu_m'] == old['at_local_enu_m'] and stand['bearing_deg'] == old['bearing_deg']
            contacts = stand['contacts']
            assert len(contacts) == 4 and all(c['inside'] for c in contacts)
            heights = [c['height'] for c in contacts]
            assert all(isinstance(y, (int, float)) and abs(y) < float('inf') for y in heights)
            assert max(heights)-min(heights) == stand['wheel_plane_span_m'] <= .03, 'Unchanged 30mm ground guard'
            spec = record['models'][model]
            assert spec['file'] == f'transport/covered-wagon/{model}/covered-w01.glb'
            assert spec['type'] == 'Covered wagon' and not spec.get('support_file')
            assert spec['wheel_contacts_m'] == [[-.605, -1.175], [-.605, 1.175], [.605, -1.175], [.605, 1.175]]
            glb = root/'renderers/web'/spec['file']
            side = glb.with_suffix('.json')
            assert digest(glb) == product['glb_sha256'] and digest(side) == product['sidecar_sha256'], 'Reviewed source product changed'
            metadata = json.loads(side.read_text())
            assert metadata['legacy_record_id'] == old['id'] and metadata['seeded_coat'] == coat
            raw = glb.read_bytes()
            length = struct.unpack_from('<I', raw, 12)[0]
            exported = json.loads(raw[20:20+length])
            info = exported['extras']['covered_derivative']
            assert info['legacy_record_id'] == old['id'] and info['yoke'] == old.get('yoke', False)
            sockets = set(metadata['unsupportedInheritedSockets'])
            assert sockets == set(info['unsupported_inherited_sockets']) and len(sockets) == 10
            assert all(n.get('extras', {}).get('covered_empty_interface_supported') is False
                       for n in exported['nodes'] if n['name'] in sockets), 'No occupied/hitch/collision interfaces'
    assert seen == COVERED_MODELS, 'Both reviewed individuals must be explicit and unique'
    return len(seen)
