#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write the five reconstructed 1904 child clothing recipes; no Blender or export."""
import copy
import argparse
import hashlib
import json
from pathlib import Path
from human_child_1904 import ROOT, ROLES, LIBERTY, materials


def generate():
    outputs = {}
    source_ids = ['hewitt_roosevelt_sons_1904', 'snyder_children_tea_1904']
    for role, (body, age, kind) in ROLES.items():
        original = 'boy' if kind == 'boy' else 'girl' if kind == 'girl' else 'toddler'
        rec = json.loads((ROOT / f'data/humans/recipes/child_{original}_1812.json').read_text())
        rec.pop('role_1812', None)
        rec.update(liberty=LIBERTY, label=f'Reconstructed {role.replace("_", " ")} clothing on an age-{age} body',
                   scene_date='1904-07-01', sources=source_ids,
                   basis='Original 1904 clothing shells on a pinned CC0 child body. Identity, stature, colour and exact fit are not attested.',
                   source_scope='Hewitt: Roosevelt boys, published New-York Tribune 29 May 1904. Snyder: two children at play, Oxford Ohio, August 1904. These are clothing references, not portraits of Prairie Avenue residents.',
                   colors_linear_rgba={**{k: rec['colors_linear_rgba'][k] for k in ('skin', 'eyes')},
                                       **{k: v['base_color_linear'] for k, v in materials(kind).items()}})
        path = 'assets/authored/humans/makehuman_hm08/' + body
        raw = (ROOT / path).read_bytes(); b = json.loads(raw)
        height = max(p[1] for p in b['meshes'][0]['positions_m']) - min(p[1] for p in b['meshes'][0]['positions_m'])
        variant = copy.deepcopy(rec['proof_variants'][0])
        variant.update(id=role, component_assembly=role+'_v1', person_reference_id='anonymous_'+role,
                       person_reference_scene='1904', person_reference_record='data/sources/'+source_ids[0]+'.json',
                       reference_summary={'name': f'a {kind} in reconstructed 1904 everyday clothes', 'named': False,
                                          'dress_role': role, 'presence': 'clothing reference only'},
                       body_input=path, recipe_path=f'data/humans/recipes/{role}.json',
                       body_basis='Pinned CC0 age-specific body; neither a named person nor an attested height or ancestry.')
        variant['body_parameters'] = {'chosen_height_m': round(height, 4), 'engineering_age_years': age,
            'height_basis': 'Reconstructed engineering stature, varied per resident; no individual measurement.',
            'age_basis': 'Child graphical targets for this engineering age; resident age comes from the household record.',
            'shape_basis': 'An equal blend of software shape categories, not a claim about ancestry.'}
        rec['proof_variants'] = [variant]
        rec['child_components'] = {'version': 1, 'generator': 'tools/human_child_1904.py', 'role': role,
            'liberty': LIBERTY, 'body_sha256': hashlib.sha256(raw).hexdigest(),
            'production_eligible': False, 'photo_accepted': False,
            'garments': [{'id': name, 'material': name, 'provenance': {'grade': 'reconstructed',
                'source_ids': source_ids, 'liberty': LIBERTY}} for name in materials(kind)]}
        outputs[variant['recipe_path']] = json.dumps(rec, indent=1)+'\n'
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    for path, text in generate().items():
        if args.check:
            if not (ROOT / path).exists() or (ROOT / path).read_text() != text:
                raise SystemExit('stale child recipe: ' + path)
        else:
            (ROOT / path).write_text(text)
    print('ok five 1904 child clothing recipes; canonical exports and visual acceptance remain required')


if __name__ == '__main__':
    main()
