#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent raw-component verifier. Does not import the material generator.

MASTER children only: every expanded triangle corner is checked byte-for-byte.
This is not native loaded-WEB, image/style/fit or memory acceptance.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

MATERIAL = 'garment_outer__livery_coat_green_1904'
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(raw):
    require(len(raw) >= 28 and struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'complete GLB2')
    n, kind = struct.unpack_from('<II', raw, 12)
    require(n % 4 == 0 and kind == 0x4e4f534a, 'JSON chunk')
    doc = json.loads(raw[20:20+n])
    length, kind = struct.unpack_from('<II', raw, 20+n)
    binary = raw[28+n:]
    require(kind == 0x004e4942 and length == len(binary), 'single embedded BIN')
    require(len(doc['buffers']) == 1 and 'uri' not in doc['buffers'][0], 'buffer0 only')
    require(doc['buffers'][0]['byteLength'] <= len(binary), 'buffer bounds')
    return doc, binary


def components(doc, binary, ai):
    a = doc['accessors'][ai]
    v = doc['bufferViews'][a['bufferView']]
    require(not a.get('sparse') and not a.get('extensions') and not v.get('extensions') and v['buffer'] == 0, 'plain component stream')
    width = WIDTH[a['type']]*SIZE[a['componentType']]
    stride = v.get('byteStride', width)
    start = v.get('byteOffset', 0)+a.get('byteOffset', 0)
    end = start+(a['count']-1)*stride+width
    require(a['count'] > 0 and stride >= width and end <= v.get('byteOffset', 0)+v['byteLength'] and end <= len(binary), 'accessor bounds')
    return [binary[start+i*stride:start+i*stride+width] for i in range(a['count'])]


def indices(doc, binary, primitive):
    a = doc['accessors'][primitive['indices']]
    require(a['type'] == 'SCALAR' and a['componentType'] in (5121, 5123, 5125) and not a.get('normalized'), 'unsigned indices')
    return [int.from_bytes(b, 'little') for b in components(doc, binary, primitive['indices'])]


def png(doc, binary, info):
    texture = doc['textures'][info['index']]
    image = doc['images'][texture['source']]
    require(image['mimeType'] == 'image/png' and 'uri' not in image, 'embedded PNG')
    v = doc['bufferViews'][image['bufferView']]
    raw = binary[v['byteOffset']:v['byteOffset']+v['byteLength']]
    require(raw[:8] == b'\x89PNG\r\n\x1a\n' and len(raw) < 128*128*8, 'bounded PNG')
    at, data, ended = 8, b'', False
    while at < len(raw):
        n = struct.unpack_from('>I', raw, at)[0]
        tag, body = raw[at+4:at+8], raw[at+8:at+8+n]
        require(at+12+n <= len(raw) and zlib.crc32(tag+body) == struct.unpack_from('>I', raw, at+8+n)[0], 'PNG CRC')
        if tag == b'IHDR':
            require(struct.unpack('>IIBBBBB', body) == (128, 128, 8, 6, 0, 0, 0), '128px RGBA8 noninterlaced')
        elif tag == b'IDAT':
            data += body
        elif tag == b'IEND':
            require(n == 0 and at+12 == len(raw), 'PNG EOF')
            ended = True
        else:
            raise ValueError('unexpected generated PNG chunk')
        at += n+12
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(data, 128*513+1)
    require(ended and decoder.eof and not decoder.unused_data and len(pixels) == 128*513, 'complete bounded image data')
    require(all(pixels[y*513] == 0 for y in range(128)), 'known lossless scanline representation')
    return [pixels[y*513+1+x*4:y*513+5+x*4] for y in range(128) for x in range(128)], sha(raw)


def verify(parent_raw, child_raw, recipe_raw, lod):
    r = json.loads(recipe_raw)
    expected_parent = next(x for x in r['parents'] if x['lod'] == lod and '/web/' not in x['file'])
    require(lod in (0, 1) and sha(parent_raw) == expected_parent['sha256'], 'pinned exact near MASTER parent')
    parent, old_bin = read(parent_raw)
    child, binary = read(child_raw)
    require(binary[:len(old_bin)] == old_bin, 'entire original BIN/padding must remain byte-exact')
    for key in ('accessors', 'bufferViews', 'images', 'textures', 'samplers'):
        require(child.get(key, [])[:len(parent.get(key, []))] == parent.get(key, []), 'all original '+key+' unchanged')
    require(len(child['materials']) == len(parent['materials']), 'original material slots/names retained')
    expected = copy.deepcopy(parent)
    for key in ('accessors', 'bufferViews', 'images', 'textures', 'samplers', 'extensionsUsed'):
        expected[key] = child[key]
    expected['buffers'][0]['byteLength'] = child['buffers'][0]['byteLength']
    found, material_ids = [], set()
    for mi, mesh in enumerate(parent['meshes']):
        for pi, p in enumerate(mesh['primitives']):
            if parent['materials'][p['material']].get('name') != MATERIAL:
                continue
            q = child['meshes'][mi]['primitives'][pi]
            require(set(q['attributes']) == set(p['attributes']) | {'TANGENT'}, 'only TANGENT semantic added')
            old_idx, new_idx = indices(parent, old_bin, p), indices(child, binary, q)
            require(len(old_idx) == len(new_idx) and len(old_idx) % 3 == 0, 'all triangles/order/corners retained')
            count = parent['accessors'][p['attributes']['POSITION']]['count']
            tangent = components(child, binary, q['attributes']['TANGENT'])
            tangent_a = child['accessors'][q['attributes']['TANGENT']]
            require(tangent_a['type'] == 'VEC4' and tangent_a['componentType'] == 5126 and not tangent_a.get('normalized'), 'FLOAT glTF tangents')
            require(all(all(math.isfinite(v) for v in struct.unpack('<4f', b)) and abs(struct.unpack('<4f', b)[3]) == 1 for b in tangent), 'finite tangent handedness')
            groups, new_to_old = {}, {}
            for old_i, new_i in zip(old_idx, new_idx):
                require(0 <= old_i < count and 0 <= new_i < len(tangent), 'corner domains')
                require(new_to_old.setdefault(new_i, old_i) == old_i, 'never merge different old vertices')
                key = (old_i, tangent[new_i])
                require(groups.setdefault(key, new_i) == new_i, 'no gratuitous duplicate of same old index/tangent group')
            require(set(new_to_old) == set(range(len(tangent))) and len(tangent) == len(groups), 'exactly necessary tangent groups, no orphan rows')
            require(all(new_to_old[i] == i for i in range(count)), 'retain every old vertex in original row order')
            streams = [(p['attributes'], {k: v for k, v in q['attributes'].items() if k != 'TANGENT'})]
            require(len(p.get('targets', [])) == len(q.get('targets', [])), 'all morph targets retained')
            streams.extend(zip(p.get('targets', []), q.get('targets', [])))
            hashes = {}
            for si, (before, after) in enumerate(streams):
                require(before.keys() == after.keys(), 'exact original semantics/morph membership')
                for semantic, ai in before.items():
                    old_rows, new_rows = components(parent, old_bin, ai), components(child, binary, after[semantic])
                    old_a, new_a = parent['accessors'][ai], child['accessors'][after[semantic]]
                    shape = {k: v for k, v in old_a.items() if k not in ('bufferView', 'byteOffset', 'count')}
                    require(shape == {k: v for k, v in new_a.items() if k not in ('bufferView', 'byteOffset', 'count')}, 'component type/normalized/minmax/extras retained')
                    require(len(new_rows) == len(tangent) and all(new_rows[j] == old_rows[new_to_old[j]] for j in range(len(new_rows))), 'every protected attribute and morph row byte-exact')
                    old_corners = b''.join(old_rows[i] for i in old_idx)
                    require(old_corners == b''.join(new_rows[i] for i in new_idx), 'expanded corner bit identity')
                    hashes[str(si)+':'+semantic] = sha(old_corners)
            dst = expected['meshes'][mi]['primitives'][pi]
            dst['attributes'], dst['indices'] = q['attributes'], q['indices']
            if 'targets' in q:
                dst['targets'] = q['targets']
            material_ids.add(p['material'])
            found.append({'mesh': mesh['name'], 'old_vertices': count, 'new_vertices': len(tangent), 'duplicated_vertices': len(tangent)-count, 'corners': len(old_idx), 'protected_corner_sha256': hashes, 'tangent_sha256': sha(b''.join(tangent))})
    require(len(found) == 2 and len(material_ids) == 1, 'only exact current two-part coat')
    material_id = material_ids.pop()
    material = child['materials'][material_id]
    pbr = material['pbrMetallicRoughness']
    require(material['name'] == MATERIAL and pbr['baseColorFactor'] == [1, 1, 1, 1] and pbr['metallicFactor'] == 0 and pbr['roughnessFactor'] == 1, 'portable maps, original exact recolor name')
    marker = material['extras']['chicago4d_cloth_microtexture']
    require(marker['recipe_sha256'] == sha(recipe_raw) and marker['parent_glb_sha256'] == sha(parent_raw) and marker['lod'] == lod and marker['runtime_weave'] == 'portable_maps_with_common_macro', 'material-only derivative provenance')
    require(marker['source_material'] == MATERIAL and marker['historical_texture'] is False and marker['photo_quality_accepted'] is False and marker['license'] == 'CC0-1.0', 'reconstructed pixel provenance')
    infos = [pbr['baseColorTexture'], pbr['metallicRoughnessTexture'], material['normalTexture']]
    for info in infos:
        require(info['texCoord'] == 0 and info['extensions'] == {'KHR_texture_transform': {'scale': [marker['uv_repeat']]*2}}, 'same original UV / explicit repeat per map')
    require(material['normalTexture']['scale'] == 1 and child['extensionsUsed'] == ['KHR_texture_transform'], 'standard tangent normal +Y / transform')
    images = [png(child, binary, info) for info in infos]
    srgb_decode = lambda x: x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4
    means = [sum(srgb_decode(p[c]/255) for p in images[0][0])/16384 for c in range(3)]
    # Each quantized pixel bounds its unrounded IEC-domain target. Compare the
    # palette to aggregate intervals, rather than inventing a dark-color epsilon.
    intervals = [(sum(srgb_decode(max(0, p[c]-.5)/255) for p in images[0][0])/16384, sum(srgb_decode(min(255, p[c]+.5)/255) for p in images[0][0])/16384) for c in range(3)]
    require(all(lo <= target <= hi for target, (lo, hi) in zip(r['linear_color'], intervals)), 'original linear wool palette inside actual 8-bit quantization intervals')
    require(all(p[0] == 255 and p[2] == 0 and p[3] == 255 for p in images[1][0]), 'linear ORM channels / no metallic cloth')
    require(all(p[3] == 255 and p[2] >= 128 for p in images[2][0]), 'opaque +Z tangent normals')
    expected_material = copy.deepcopy(parent['materials'][material_id])
    expected_material['pbrMetallicRoughness'] = {**expected_material['pbrMetallicRoughness'], **{key: pbr[key] for key in ('baseColorFactor', 'metallicFactor', 'roughnessFactor', 'baseColorTexture', 'metallicRoughnessTexture')}}
    expected_material['normalTexture'] = material['normalTexture']
    expected_material['extras'] = {**expected_material.get('extras', {}), 'chicago4d_cloth_microtexture': marker}
    require(expected_material == material, 'only reviewed coat material fields changed')
    expected['materials'][material_id] = material
    require(expected == child, 'all noncoat primitives, nodes, rig, clips, identity, frame and metadata exact')
    return {'status': 'RAW_MASTER_SEMANTICS_PASS_NOT_NATIVE_ACCEPTANCE', 'parent_sha256': sha(parent_raw), 'child_sha256': sha(child_raw), 'rows': found, 'linear_color_means': means, 'linear_palette_intervals': intervals, 'image_sha256': [im[1] for im in images], 'original_BIN_bytes_exact': len(old_bin), 'native_WEB_render_fit_photo_memory': 'UNRUN'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipe', type=Path)
    parser.add_argument('parent', type=Path)
    parser.add_argument('child', type=Path)
    parser.add_argument('--lod', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.parent.read_bytes(), args.child.read_bytes(), args.recipe.read_bytes(), args.lod), indent=2))
