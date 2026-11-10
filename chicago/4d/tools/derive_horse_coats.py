# SPDX-License-Identifier: GPL-3.0-or-later
"""Derive an engine-neutral coat contract from immutable licensed source arrays.

No mesh/image bytes or joints are changed. Runtime palettes are reconstruction;
source model/maps retain CC BY 4.0. Run explicitly, not as a browser fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

APP = Path(__file__).resolve().parent.parent


def derive(recipe, root):
    assert recipe['schema'] == 'chicago4d_horse_coats_recipe_v1', 'authored recipe required'
    sources = []
    for spec in recipe['sources']:
        raw = (root/spec['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == spec['sha256'], 'immutable horse source differs'
        magic, version, length = struct.unpack_from('<III', raw)
        assert magic == 0x46546c67 and version == 2 and length == len(raw)
        size, kind = struct.unpack_from('<II', raw, 12)
        assert kind == 0x4e4f534a
        g = json.loads(raw[20:20+size]); binary = memoryview(raw)[28+size:]
        def view_hash(index):
            v = g['bufferViews'][index]; start = v.get('byteOffset', 0)
            return hashlib.sha256(binary[start:start+v['byteLength']]).hexdigest()
        def accessor_hash(index):
            a = g['accessors'][index]
            return {'accessor': a, 'buffer_view_sha256': view_hash(a['bufferView'])}
        bodies = [p for m in g['meshes'] for p in m['primitives']
                  if g['materials'][p['material']]['name'] == recipe['body_material']]
        assert len(bodies) == 1
        body = bodies[0]; position = g['accessors'][body['attributes']['POSITION']]
        assert position['count'] == recipe['body_vertices']
        joints = [g['nodes'][i]['name'] for i in g['skins'][0]['joints']]
        assert len(joints) == 26 and len(set(joints)) == 26
        sources.append({**spec, 'body_vertices': position['count'],
                        'body_bounds_m': [position['min'], position['max']],
                        'body_attributes': {k: accessor_hash(v) for k, v in body['attributes'].items()},
                        'body_indices': accessor_hash(body['indices']), 'joint_names': joints,
                        'inverse_bind_matrices': accessor_hash(g['skins'][0]['inverseBindMatrices']),
                        'animation_names': [a['name'] for a in g.get('animations', [])],
                        'image_payload_sha256': [view_hash(i['bufferView']) for i in g['images']],
                        'material_names': [m['name'] for m in g['materials']]})
    reference = root/recipe['foot_reference']
    sidecar = json.loads(reference.read_text())
    feet = {name: patch['minimum_vertex_canonical_m'] for name, patch in sidecar['contacts'].items()}
    assert set(feet) == {'fore_l', 'fore_r', 'hind_l', 'hind_r'}
    return {**recipe, 'schema': 'chicago4d_horse_coats_v1', 'source_contract': sources,
            'foot_reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
            'foot_centres_m': feet,
            'source_protection': 'Original geometry/UV/skin/IBMs/joints/clips/maps unchanged; shader colour only. Derived anchors do not replace complete-hoof classifiers.',
            'native_all_path_visual_qualification': 'UNRUN'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, default=APP)
    p.add_argument('--recipe', type=Path, default=APP/'data/transport/horse-coats.recipe.json')
    p.add_argument('--output', type=Path, default=APP/'data/transport/horse-coats.json')
    p.add_argument('--check', action='store_true', help='compare the entire canonical derivation without writing')
    args = p.parse_args()
    raw_recipe = args.recipe.read_bytes()
    output = derive(json.loads(raw_recipe), args.source_root)
    output['recipe_sha256'] = hashlib.sha256(raw_recipe).hexdigest()
    canonical = json.dumps(output, indent=2)+'\n'
    if args.check:
        if not args.output.is_file() or args.output.read_text() != canonical:
            raise SystemExit('HORSE COATS FAIL: canonical output is stale; run python3 tools/derive_horse_coats.py')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical)
    print(json.dumps({'sources': len(output['source_contract']), 'body_vertices': output['body_vertices'],
                      'source_only': True, 'native_qualification': 'UNRUN'}))
