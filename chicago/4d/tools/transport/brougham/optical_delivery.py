# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent optical-only identity and deterministic regeneration contract."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = ROOT / 'renderers/web/transport/parked-brougham'
GENERATOR = Path(__file__).with_name('generate_optical_delivery.mjs')
SOURCE_SHA = {
    'near': '3d2f3a802f4b32dba6a3e61f2c188dddce4db05cecfcbba81e1e8d369d5dfe89',
    'mid': 'd5cdd34e981d29db41634ac780c22526742f6a20527b5866d2349c727a67400d',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'GLB envelope'
    length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4e4f534a, 'JSON chunk'
    document = json.loads(raw[20:20 + length])
    size, kind = struct.unpack_from('<II', raw, 20 + length)
    assert kind == 0x004e4942 and 28 + length + size == len(raw), 'One final BIN chunk'
    return document, raw[20 + length:], sha(raw)


def compare(original, source_bin, delivery, delivery_bin, source_sha, producer_sha):
    assert source_bin == delivery_bin, 'Every BIN/index/position/normal byte must remain exact'
    expected = copy.deepcopy(original)
    glass = expected['materials'][7]
    assert glass['extensions']['KHR_materials_transmission']['transmissionFactor'] == .98
    del glass['extensions']['KHR_materials_transmission']
    glass['name'] = 'thin_sheet_cabin_glass_delivery_reconstruction'
    glass['alphaMode'] = 'BLEND'
    glass['pbrMetallicRoughness']['baseColorFactor'][3] = .14
    for key in ['extensionsUsed', 'extensionsRequired']:
        if key in expected:
            expected[key] = [value for value in expected[key] if value != 'KHR_materials_transmission']
    assert delivery['extras']['status'] == expected['extras']['status'] + '; separate thin-sheet optical delivery approximation; all physical geometry retained; acceptance pending'
    actual = copy.deepcopy(delivery)
    actual['extras']['status'] = expected['extras']['status']
    derivation = actual['extras'].pop('runtime_derivation')
    assert derivation['source_indexed_sha256'] == source_sha, 'Exact indexed source attribution'
    assert derivation['producer_sha256'] == producer_sha, 'Exact canonical producer attribution'
    assert derivation['geometry_and_all_binary_bytes_unchanged'] is True
    assert derivation['materials0_through6_unchanged'] is True
    assert derivation['photographic_accepted'] is False and derivation['world_budget_accepted'] is False
    profile = derivation['glass_delivery_profile']
    assert profile['alphaMode'] == 'BLEND' and profile['opacity'] == .14
    assert profile['transmission'] == 0 and profile['ior'] == 1.5
    assert actual == expected, 'No geometry/layout/scene/material0-6 or other JSON change is permitted'


def controls(source, source_bin, delivery, delivery_bin, source_sha, producer_sha):
    changes = [
        ('BIN corruption', None),
        ('protected lamp material', lambda doc: doc['materials'][3].update(name='wrong')),
        ('body node transform', lambda doc: doc['nodes'][0].update(translation=[.001, 0, 0])),
        ('wrong alpha opacity', lambda doc: doc['materials'][7]['pbrMetallicRoughness']['baseColorFactor'].__setitem__(3, .15)),
        ('wrong geometry count', lambda doc: doc['accessors'][0].update(count=1)),
        ('wrong triangle statistic', lambda doc: doc['extras']['statistics'].update(triangles=1)),
        ('wrong source attribution', lambda doc: doc['extras']['runtime_derivation'].update(source_indexed_sha256='0' * 64)),
        ('wrong producer attribution', lambda doc: doc['extras']['runtime_derivation'].update(producer_sha256='0' * 64)),
        ('transmission restored', lambda doc: doc['materials'][7]['extensions'].update(KHR_materials_transmission={'transmissionFactor': .01})),
    ]
    results = []
    for name, mutate in changes:
        document, binary = copy.deepcopy(delivery), delivery_bin
        if mutate:
            mutate(document)
        else:
            binary = delivery_bin[:12] + bytes([delivery_bin[12] ^ 1]) + delivery_bin[13:]
        try:
            compare(source, source_bin, document, binary, source_sha, producer_sha)
        except AssertionError as error:
            results.append({'control': name, 'rejected': str(error)})
        else:
            raise AssertionError('Corruption escaped: ' + name)
    return results


def verify(directory=DIRECTORY):
    producer_sha = sha(GENERATOR.read_bytes())
    results = []
    for detail, expected in SOURCE_SHA.items():
        source, source_bin, source_sha = read(directory / f'brougham-{detail}.glb')
        assert source_sha == expected, 'Original physical indexed master changed'
        delivery, binary, delivery_sha = read(directory / f'brougham-{detail}-delivery-v1.glb')
        compare(source, source_bin, delivery, binary, source_sha, producer_sha)
        results.append({'detail': detail, 'source_sha256': source_sha, 'delivery_sha256': delivery_sha,
                        'triangles': source['extras']['statistics']['triangles'],
                        'entire_BIN_and_geometry_layout_scene_and_materials0_6_exact': True,
                        'negative_controls': controls(source, source_bin, delivery, binary, source_sha, producer_sha)})
    # The actual canonical command must reproduce the two committed bytes and its
    # original receipt. Its fresh temporary output is never a repository write.
    with tempfile.TemporaryDirectory(prefix='brougham-optical-check-') as temp:
        output = Path(temp) / 'fresh'
        subprocess.run(['node', str(GENERATOR), '--source-dir', str(directory), '--output', str(output)],
                       cwd=ROOT, check=True, capture_output=True, text=True)
        for detail in SOURCE_SHA:
            name = f'brougham-{detail}-delivery-v1.glb'
            assert (output / name).read_bytes() == (directory / name).read_bytes(), 'Canonical optical output drifted: ' + detail
        assert (output / 'CANDIDATE.json').read_bytes() == (directory / 'OPTICAL-DELIVERY-RECEIPT.json').read_bytes(), 'Canonical optical receipt drifted'
    return {'pass': True, 'scope': 'Strict serialized identity and canonical regeneration only; no renderer or world acceptance',
            'producer_sha256': producer_sha, 'rows': results, 'canonical_regeneration_byte_exact': True}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
