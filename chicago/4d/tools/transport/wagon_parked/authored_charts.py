# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the original W01 authored charts; never calculate replacement charts."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct

DIRECTORY = Path(__file__).resolve().parents[3] / 'assets/authored/transport/wagon_parked/charts'
MANIFEST = 'original-w01-charts.json'
MANIFEST_SHA256 = 'e925adf8450a2db85f1183a789ea9aabdd3f83f407bf5763d160b24a14410a0b'
INPUTS = {
    'hardware_glb_sha256': '04820fc15b16c6f1b9b12487c2d6ceb3500d03c94094d84c73554f2b2d1f5709',
    'authored_parts_sha256': '2fb3709d233e896280c50342618c28f9e340029e52c67b328100e05a125e2c27',
    'material_recipe_sha256': '45b3d15ddf15bf28a38dbc6d2c788354d83eafecc8914278db6e17d9bcf4a0bf',
}
REFERENCE_SHA256 = '0138ad2565f3e8b08029ef788c5196c65c80c79643313e944c726b993ff31ee4'
MATERIALS = ['paint', 'timber', 'plank_a', 'plank_b', 'iron', 'end_grain']


def need(ok, message):
    if not ok:
        raise ValueError('Original W01 charts: ' + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON field ' + key)
        result[key] = value
    return result


def _json(raw):
    def nonfinite(value):
        raise ValueError('Original W01 charts: nonfinite JSON ' + value)
    return json.loads(raw, object_pairs_hook=_object, parse_constant=nonfinite)


def _keys(value, expected, label):
    need(isinstance(value, dict) and set(value) == set(expected), label + ' fields')


def _positive_int(value):
    return type(value) is int and value > 0


def _digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_input_hashes(values):
    """The same strict source contract is used by the loader and finite controls."""
    need(values == INPUTS, 'hardware, ownership or material recipe hash mismatch')


def _validate_bundle(contract, payload, mapping_raw):
    _keys(contract, ['schema', 'source_inputs', 'reference', 'payload', 'mapping', 'batches'], 'manifest')
    need(contract['schema'] == 'original_w01_authored_charts_v1', 'schema')
    validate_input_hashes(contract['source_inputs'])
    need(contract['reference']['material_glb_sha256'] == REFERENCE_SHA256, 'reviewed material reference')
    for field, data, filename in [('payload', payload, 'original-w01-charts.bin'),
                                  ('mapping', mapping_raw, 'original-w01-charts.mapping.json')]:
        item = contract[field]
        _keys(item, ['file', 'bytes', 'sha256'], field)
        need(item['file'] == filename and type(item['bytes']) is int and item['bytes'] == len(data)
             and item['sha256'] == sha(data), field + ' bytes/hash')
    batches = contract['batches']
    need(isinstance(batches, list) and len(batches) == 23, 'exact 23 ordered batches required')
    names, attributes, expected_mapping, cursor = set(), {}, [], 0
    for batch in batches:
        _keys(batch, ['name', 'material', 'vertex_count', 'geometry_sha256', 'parts', 'attributes'], 'batch')
        name, material, count = batch['name'], batch['material'], batch['vertex_count']
        need(isinstance(name, str) and name and name not in names, 'duplicate/invalid batch identity')
        names.add(name)
        need(type(material) is int and 0 <= material < len(MATERIALS) and _positive_int(count), 'batch material/count')
        need(count % 3 == 0, 'triangle vertex count')
        _keys(batch['geometry_sha256'], ['POSITION', 'NORMAL'], 'geometry hashes')
        need(all(_digest(v) for v in batch['geometry_sha256'].values()), 'geometry digest')
        owners = batch['parts']
        need(isinstance(owners, list) and owners, 'ordered source ownership required')
        total = 0
        for owner in owners:
            _keys(owner, ['name', 'frame', 'material', 'vertices'], 'source owner')
            need(isinstance(owner['name'], str) and owner['name'] and isinstance(owner['frame'], str)
                 and owner['frame'] + '_' + MATERIALS[material] == name
                 and type(owner['material']) is int and owner['material'] == material
                 and _positive_int(owner['vertices']) and owner['vertices'] % 3 == 0, 'source owner identity/count')
            total += owner['vertices']
            expected_mapping.append((name, owner['name'], owner['vertices'] // 3))
        need(total == count, 'source ownership vertex count')
        _keys(batch['attributes'], ['TEXCOORD_0', 'TANGENT'], 'chart attributes')
        attributes[name] = {}
        for semantic, kind, width in [('TEXCOORD_0', 'VEC2', 2), ('TANGENT', 'VEC4', 4)]:
            item = batch['attributes'][semantic]
            _keys(item, ['byte_offset', 'byte_length', 'sha256', 'componentType', 'count', 'type', 'min', 'max'], semantic)
            need(type(item['byte_offset']) is int and item['byte_offset'] == cursor
                 and type(item['byte_length']) is int and item['byte_length'] == count * width * 4,
                 semantic + ' ordered payload range')
            need(type(item['componentType']) is int and item['componentType'] == 5126
                 and type(item['count']) is int and item['count'] == count and item['type'] == kind,
                 semantic + ' accessor shape')
            data = payload[cursor:cursor + item['byte_length']]
            need(len(data) == item['byte_length'] and sha(data) == item['sha256'], semantic + ' payload hash')
            values = struct.unpack('<' + 'f' * (count * width), data)
            need(all(math.isfinite(v) for v in values), semantic + ' finite payload')
            for limit, operation in [('min', min), ('max', max)]:
                bounds = item[limit]
                need(isinstance(bounds, list) and len(bounds) == width, semantic + ' frozen bounds shape')
                for axis, bound in enumerate(bounds):
                    need(type(bound) in (int, float) and math.isfinite(bound)
                         and operation(values[axis::width]) == bound, semantic + ' frozen bounds/data mismatch')
            metadata = {k: deepcopy(item[k]) for k in ['componentType', 'count', 'type', 'min', 'max']}
            attributes[name][semantic] = (data, metadata)
            cursor += len(data)
    need(cursor == len(payload) == 871488, 'complete original chart payload')
    mapping = _json(mapping_raw)
    _keys(mapping, ['schema', 'scope', 'reference_material_glb_sha256', 'source_mapping'], 'mapping')
    need(mapping['schema'] == 'original_w01_chart_mapping_v1'
         and mapping['reference_material_glb_sha256'] == REFERENCE_SHA256, 'original mapping reference')
    rows = mapping['source_mapping']
    need(isinstance(rows, list) and len(rows) == len(expected_mapping) == 158, 'complete original mapping')
    for row, expected in zip(rows, expected_mapping):
        _keys(row, ['part', 'batch', 'triangles', 'flat_constant_neutral_chart_triangles',
                    'physical_chart_anisotropy', 'grain', 'tile_m'], 'mapping row')
        need((row['batch'], row['part'], row['triangles']) == expected, 'mapping ownership/order')
        need(type(row['triangles']) is int and type(row['flat_constant_neutral_chart_triangles']) is int
             and 0 <= row['flat_constant_neutral_chart_triangles'] <= row['triangles'], 'mapping triangle counts')
        need(type(row['physical_chart_anisotropy']) in (int, float)
             and math.isfinite(row['physical_chart_anisotropy']) and row['physical_chart_anisotropy'] > 0,
             'finite original author-time chart metric')
    return attributes, rows


class OriginalCharts:
    def __init__(self, contract, payload, mapping_raw):
        self.attributes, self.mapping = _validate_bundle(contract, payload, mapping_raw)
        self.contract = contract
        self.receipt = {
            'mode': 'validated original authored Float32 charts',
            'manifest_sha256': MANIFEST_SHA256,
            'payload_sha256': contract['payload']['sha256'],
            'mapping_sha256': contract['mapping']['sha256'],
            'reference_material_glb_sha256': REFERENCE_SHA256,
            'mapping_metrics': 'Pinned original author-time values describing these exact charts; not newly recomputed production measurements',
        }

    def attribute(self, batch, semantic):
        data, metadata = self.attributes[batch][semantic]
        return data, deepcopy(metadata)


def read_original_charts(directory=DIRECTORY):
    directory = Path(directory)
    manifest_raw = (directory / MANIFEST).read_bytes()
    need(sha(manifest_raw) == MANIFEST_SHA256, 'manifest hash')
    contract = _json(manifest_raw)
    # Fixed filenames; manifest data never chooses a filesystem path.
    payload = (directory / 'original-w01-charts.bin').read_bytes()
    mapping = (directory / 'original-w01-charts.mapping.json').read_bytes()
    return OriginalCharts(contract, payload, mapping)


def _hardware(raw):
    need(len(raw) >= 28 and struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'hardware GLB header')
    length, kind = struct.unpack_from('<II', raw, 12)
    need(kind == 0x4e4f534a and 28 + length <= len(raw), 'hardware JSON chunk')
    binary_length, kind = struct.unpack_from('<II', raw, 20 + length)
    need(kind == 0x004e4942 and 28 + length + binary_length == len(raw), 'hardware BIN chunk')
    return _json(raw[20:20 + length]), raw[28 + length:]


def _geometry(gltf, binary, index):
    accessor = gltf['accessors'][index]
    view = gltf['bufferViews'][accessor['bufferView']]
    need(accessor['componentType'] == 5126 and accessor['type'] == 'VEC3'
         and 'sparse' not in accessor and 'byteStride' not in view and view['buffer'] == 0,
         'original contiguous Float32 geometry')
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    count = accessor['count'] * 3 * 4
    need(offset >= 0 and offset + count <= len(binary), 'geometry buffer range')
    return binary[offset:offset + count]


def load_original_charts(hardware_raw, parts_raw, recipe_raw, directory=DIRECTORY):
    validate_input_hashes({'hardware_glb_sha256': sha(hardware_raw),
                          'authored_parts_sha256': sha(parts_raw), 'material_recipe_sha256': sha(recipe_raw)})
    charts = read_original_charts(directory)
    gltf, binary = _hardware(hardware_raw)
    parts = _json(parts_raw)
    need(isinstance(parts, list) and len(parts) == 158, 'exact original ownership list')
    need([b['name'] for b in charts.contract['batches']] == [m['name'] for m in gltf['meshes']], 'batch order')
    for batch, mesh in zip(charts.contract['batches'], gltf['meshes']):
        need(len(mesh['primitives']) == 1, 'single original batch primitive')
        primitive = mesh['primitives'][0]
        need(primitive['material'] == batch['material'] and 'indices' not in primitive, 'batch primitive identity')
        owned = [p for p in parts if p['frame'] + '_' + gltf['materials'][p['material']]['name'] == mesh['name']]
        need([{'name': p['name'], 'frame': p['frame'], 'material': p['material'], 'vertices': len(p['positions'])}
              for p in owned] == batch['parts'], 'ordered original ownership')
        for semantic, source_key in [('POSITION', 'positions'), ('NORMAL', 'normals')]:
            data = _geometry(gltf, binary, primitive['attributes'][semantic])
            need(len(data) == batch['vertex_count'] * 12 and sha(data) == batch['geometry_sha256'][semantic],
                 semantic + ' exact protected geometry')
            values = [v for part in owned for vector in part[source_key] for v in vector]
            need(struct.pack('<' + 'f' * len(values), *values) == data, semantic + ' source-part actual mapping')
    return charts
