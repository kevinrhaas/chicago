#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure MASTER garment retention copied from the frozen qualified prototype.

Copy selected canonical LOD0 shirt/trouser accessor streams into the matching
LOD3 master, preserving the complete LOD3 BIN prefix and every protected JSON
record. This is a retention experiment, not a garment fit or production export.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, re, struct, subprocess

ALLOWED = {'garment_upper__shirt_linen', 'garment_lower__highwaist_pantaloons'}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
SIZES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TRANSFORMS = ('translation', 'rotation', 'scale', 'matrix')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def save(path, value): Path(path).write_text(json.dumps(value, indent=2)+'\n')

def reference(ref):
    assert set(ref) == {'path', 'sha256'}
    raw = Path(ref['path']).read_bytes(); assert sha(raw) == ref['sha256']
    return json.loads(raw)

def parse(path, expected):
    raw = Path(path).read_bytes(); assert sha(raw) == expected
    magic, version, total, length, kind = struct.unpack_from('<5I', raw)
    assert (magic, version, total, kind) == (0x46546c67, 2, len(raw), 0x4e4f534a)
    doc = json.loads(raw[20:20+length]); n, kind = struct.unpack_from('<2I', raw, 20+length)
    assert kind == 0x004e4942 and len(raw) == 28+length+n
    binary = raw[28+length:]
    assert len(doc['buffers']) == 1 and 'uri' not in doc['buffers'][0]
    assert doc['buffers'][0]['byteLength'] <= len(binary)
    assert not doc.get('extensionsUsed') and not doc.get('extensionsRequired'), 'Master-only prototype; do not rewrite compressed/quantized web data.'
    return raw, doc, binary

def stream(doc, binary, accessor):
    a = doc['accessors'][accessor]
    assert 'sparse' not in a and 'extensions' not in a
    view = doc['bufferViews'][a['bufferView']]
    assert view['buffer'] == 0 and 'extensions' not in view
    width = WIDTHS[a['type']] * SIZES[a['componentType']]
    stride = view.get('byteStride', width)
    assert stride >= width
    offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    assert a.get('byteOffset', 0) + (a['count']-1)*stride + width <= view['byteLength']
    result = b''.join(binary[offset+i*stride:offset+i*stride+width] for i in range(a['count']))
    assert len(result) == a['count']*width
    return result

def parents(doc):
    result = {}
    for i, node in enumerate(doc['nodes']):
        for child in node.get('children', []):
            assert child not in result, 'No ambiguous multi-parent node graph.'
            result[child] = i
    return result

def transform_chain(doc, index):
    ancestry = parents(doc); chain = []; seen = set()
    while True:
        assert index not in seen; seen.add(index)
        chain.append({k: doc['nodes'][index][k] for k in TRANSFORMS if k in doc['nodes'][index]})
        if index not in ancestry: break
        index = ancestry[index]
    return chain

def palette_signature(doc, binary):
    assert len(doc['skins']) == 1
    skin = doc['skins'][0]; nodes = doc['nodes']; ancestry = parents(doc)
    names = [nodes[i]['name'] for i in skin['joints']]
    assert len(names) == len(set(names))
    records = []
    for i in skin['joints']:
        parent = ancestry.get(i)
        records.append(dict(name=nodes[i]['name'], parent_name=nodes[parent].get('name') if parent is not None else None,
            local={k: nodes[i][k] for k in TRANSFORMS if k in nodes[i]}, world_rest_chain=transform_chain(doc, i)))
    a = doc['accessors'][skin['inverseBindMatrices']]
    assert a['type'] == 'MAT4' and a['componentType'] == 5126 and a['count'] == len(names)
    return dict(joint_names_in_palette_order=names, joint_rest_records=records,
                inverse_bind_stream_SHA256=sha(stream(doc, binary, skin['inverseBindMatrices'])))

def selected(doc, material):
    matches = []
    for mi, mesh in enumerate(doc['meshes']):
        for pi, primitive in enumerate(mesh['primitives']):
            if doc['materials'][primitive['material']]['name'] == material:
                matches.append((mi, pi, primitive))
    assert len(matches) == 1, (material, len(matches))
    mi, pi, primitive = matches[0]
    assert len(doc['meshes'][mi]['primitives']) == 1
    assert primitive.get('mode', 4) == 4 and 'targets' not in primitive and 'extensions' not in primitive
    assert {'POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0'} <= set(primitive['attributes'])
    nodes = [i for i, node in enumerate(doc['nodes']) if node.get('mesh') == mi]
    assert len(nodes) == 1 and doc['nodes'][nodes[0]]['skin'] == 0
    return mi, pi, primitive, nodes[0]

def material_signature(doc, binary, index):
    """Resolve texture/image indices without decoding or re-encoding pixels."""
    def texture_signature(i):
        t = copy.deepcopy(doc['textures'][i]); image = doc['images'][t.pop('source')]
        assert 'uri' not in image and 'bufferView' in image
        v = doc['bufferViews'][image['bufferView']]
        assert v['buffer'] == 0 and 'extensions' not in v
        off = v.get('byteOffset', 0); payload = binary[off:off+v['byteLength']]
        t['image'] = dict(descriptor={k:x for k,x in image.items() if k != 'bufferView'}, encoded_payload_SHA256=sha(payload))
        if 'sampler' in t: t['sampler'] = doc['samplers'][t['sampler']]
        return t
    def walk(value):
        if isinstance(value, list): return [walk(x) for x in value]
        if not isinstance(value, dict): return value
        result = {}
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and 'index' in child:
                result[key] = {**{k:walk(v) for k,v in child.items() if k != 'index'}, 'resolved_texture': texture_signature(child['index'])}
            else: result[key] = walk(child)
        return result
    return walk(doc['materials'][index])

def seated_animation_signature(doc, binary):
    clips = [a for a in doc['animations'] if a['name'] == 'sit_drive_look_v2']; assert len(clips) == 1
    rows = []
    for c in clips[0]['channels']:
        target = c['target']; sampler = clips[0]['samplers'][c['sampler']]
        rows.append((doc['nodes'][target['node']]['name'], target['path'], sampler.get('interpolation', 'LINEAR'),
                     sha(stream(doc, binary, sampler['input'])), sha(stream(doc, binary, sampler['output']))))
    assert len(rows) == len(set((r[0], r[1]) for r in rows))
    return sorted(rows)

def encode(doc, binary):
    blob = bytes(binary); blob += b'\0' * (-len(blob) % 4)
    text = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode(); text += b' ' * (-len(text) % 4)
    return struct.pack('<5I', 0x46546c67, 2, 28+len(text)+len(blob), len(text), 0x4e4f534a) + text + struct.pack('<2I', len(blob), 0x004e4942) + blob

def candidate(row, materials):
    fine_raw, fine, fine_bin = parse(row['lod0_master'], row['lod0_master_SHA256'])
    parent_raw, parent, parent_bin = parse(row['lod3_master'], row['lod3_master_SHA256'])
    assert palette_signature(fine, fine_bin) == palette_signature(parent, parent_bin), 'Strict joint order/rest/IBM compatibility is required.'
    assert seated_animation_signature(fine, fine_bin) == seated_animation_signature(parent, parent_bin), 'Fine-reference and target seated curves must actually agree.'
    doc = copy.deepcopy(parent); binary = bytearray(parent_bin); copied = {}; changed = []; stream_proofs = []
    def append_accessor(index, target):
        if index in copied:
            assert copied[index][1] == target
            return copied[index][0]
        payload = stream(fine, fine_bin, index)
        binary.extend(b'\0' * (-len(binary) % 4)); offset = len(binary); binary.extend(payload)
        vi = len(doc['bufferViews']); doc['bufferViews'].append(dict(buffer=0, byteOffset=offset, byteLength=len(payload), target=target))
        a = copy.deepcopy(fine['accessors'][index]); a['bufferView'] = vi; a.pop('byteOffset', None)
        ai = len(doc['accessors']); doc['accessors'].append(a); copied[index] = (ai, target)
        assert stream(doc, binary, ai) == payload
        stream_proofs.append(dict(source_accessor=index, candidate_accessor=ai, component_bytes_SHA256=sha(payload), bytes=len(payload)))
        return ai
    for material in materials:
        smi, spi, src, snode = selected(fine, material)
        tmi, tpi, dst, tnode = selected(parent, material)
        assert transform_chain(fine, snode) == transform_chain(parent, tnode), 'Selected mesh rest/bind transform differs.'
        # Keep the LOD3 material, its textures/images and every material parameter.
        assert material_signature(fine, fine_bin, src['material']) == material_signature(parent, parent_bin, dst['material']), 'Exact resolved material/sampler/encoded image compatibility required.'
        replacement = copy.deepcopy(src); replacement['material'] = dst['material']
        replacement['attributes'] = {name: append_accessor(index, 34962) for name, index in src['attributes'].items()}
        replacement['indices'] = append_accessor(src['indices'], 34963)
        doc['meshes'][tmi]['primitives'][tpi] = replacement
        changed.append(dict(material=material, source_mesh=fine['meshes'][smi]['name'], destination_mesh=parent['meshes'][tmi]['name'],
            mesh_index=tmi, primitive_index=tpi, triangles_before=parent['accessors'][dst['indices']]['count']//3,
            triangles_after=fine['accessors'][src['indices']]['count']//3))
    doc['buffers'][0]['byteLength'] = len(binary)
    assert bytes(binary[:len(parent_bin)]) == parent_bin
    for key in parent:
        if key not in ['meshes', 'accessors', 'bufferViews', 'buffers']: assert doc[key] == parent[key], key
    assert doc['accessors'][:len(parent['accessors'])] == parent['accessors']
    assert doc['bufferViews'][:len(parent['bufferViews'])] == parent['bufferViews']
    altered = {row['mesh_index'] for row in changed}
    for i, mesh in enumerate(parent['meshes']):
        if i not in altered: assert doc['meshes'][i] == mesh, 'Protected body/eye/hair/waistcoat/shoe mesh changed.'
        else:
            assert {k:v for k,v in doc['meshes'][i].items() if k != 'primitives'} == {k:v for k,v in mesh.items() if k != 'primitives'}
    total = lambda d: sum(d['accessors'][p['indices']]['count']//3 for m in d['meshes'] for p in m['primitives'])
    result = encode(doc, binary)
    return result, dict(asset=row['asset'], source_LOD0_SHA256=sha(fine_raw), parent_LOD3_SHA256=sha(parent_raw),
        candidate_SHA256=sha(result), parent_bytes=len(parent_raw), candidate_bytes=len(result),
        triangles_before=total(parent), triangles_after=total(doc), copied_garments=changed,
        copied_accessor_streams=stream_proofs, original_LOD3_BIN_prefix_exact=True,
        non_garment_meshes_nodes_skins_clips_materials_images_identity_exact=True,
        joint_palette_rest_IBMs_and_mesh_bind_compatibility_exact=True,
        source_and_target_seated_pose_curves_exact=True,
        garment_native_pose_or_fit_or_contact_or_world_budget_acceptance=False,
        production_web_derivative_generated=False)
