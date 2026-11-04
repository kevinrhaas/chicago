#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Append a bounded seated head/neck clip; preserve the exact qualified parent."""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import struct
import subprocess

import human_natural_idle as common

APP = Path(__file__).resolve().parents[1]
RECIPE = APP / 'data/humans/animations/seated-driver-look-v2.json'
CLIP = 'sit_drive_look_v2'
TARGETS = ('neck_01', 'head')
require, sha, parse = common.require, common.sha, common.parse


def read_recipe():
    recipe = json.loads(RECIPE.read_text())
    validate_recipe(recipe)
    return recipe


def validate_recipe(recipe):
    require(recipe['clip'] == CLIP and recipe['source_clip'] == 'sit_drive'
            and recipe['samples'] == 65 and recipe['duration_s'] == 8
            and recipe['targets'] == list(TARGETS), 'reviewed seated clip/timing/targets required')
    require(recipe['motion_degrees'] == dict(neck_look_yaw=3, head_look_yaw=4, head_nod_pitch=1.5),
            'reviewed bounded seated angles required')
    require(len(recipe['parents']) == 8 and len({p['file'] for p in recipe['parents']}) == 8,
            'exactly eight explicit active LOD parents required')
    for row in recipe['parents']:
        require(re.fullmatch(r'assets/humans/(?:web/)?(?:bardwell_otis_1835|anonymous_working_driver_1904)\.lod[03]\.glb', row['file']) is not None,
                'explicit existing seated resident and active LOD path required')
        require(re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None, 'exact parent SHA required')


def parent_bytes(row, recipe):
    local = APP / row['file']
    if local.exists():
        raw = local.read_bytes()
        if sha(raw) == row['sha256']:
            return raw
    require(re.fullmatch('[0-9a-f]{40}', recipe['parent_revision']) is not None, 'exact parent revision required')
    raw = subprocess.check_output(['git', '-C', str(APP), 'show', recipe['parent_revision'] + ':chicago/4d/' + row['file']])
    require(sha(raw) == row['sha256'], 'pinned seated parent SHA mismatch')
    return raw


def seated_pose(raw):
    """Read the actual static sit_drive pose, never standing idle/rest transforms."""
    doc, binary = parse(raw)
    clips = [a for a in doc['animations'] if a.get('name') == 'sit_drive']
    require(len(clips) == 1, 'one actual seated parent clip required')
    rotations = {i: tuple(n.get('rotation', [0, 0, 0, 1])) for i, n in enumerate(doc['nodes'])}
    targets = {}
    for channel in clips[0]['channels']:
        target = channel['target']
        if target['path'] != 'rotation':
            continue
        sampler = clips[0]['samplers'][channel['sampler']]
        rows = common.float_rows(doc, binary, sampler['output'], 'VEC4')
        require(all(row == rows[0] for row in rows), 'original seated rotation must be static')
        rotations[target['node']] = rows[0]
        targets[doc['nodes'][target['node']].get('name')] = target['node']
    require(all(name in targets for name in TARGETS), 'seated head/neck rotation channel missing')
    parents = {child: i for i, node in enumerate(doc['nodes']) for child in node.get('children', [])}
    worlds = {}
    def world(i):
        if i not in worlds:
            worlds[i] = common.quat_mul(world(parents[i]), rotations[i]) if i in parents else rotations[i]
        return worlds[i]
    return {name: dict(local=rotations[i], parent_world=world(parents[i]) if i in parents else (0, 0, 0, 1))
            for name, i in targets.items() if name in TARGETS}


def append_clip(raw, expected_sha, bases, recipe):
    validate_recipe(recipe)
    require(sha(raw) == expected_sha, 'seated parent SHA mismatch')
    parent, binary = parse(raw)
    doc = copy.deepcopy(parent)
    require(not any(a.get('name') == CLIP for a in doc['animations']), 'seated derivative already installed')
    clips = [a for a in doc['animations'] if a.get('name') == 'sit_drive']
    require(len(clips) == 1, 'one exact seated parent required')
    clip = copy.deepcopy(clips[0])
    clip['name'] = CLIP
    clip['extras'] = dict(loop=True, cycle_duration_s=recipe['duration_s'], in_place=True,
                          motion_basis=recipe['basis'], liberty=recipe['liberty'],
                          recipe='data/humans/animations/seated-driver-look-v2.json',
                          derivation='Original seated rotation curves only; exact parent clips and BIN prefix preserved')
    blob = bytearray(binary)
    def accessor(rows, kind):
        blob.extend(b'\0' * (-len(blob) % 4))
        start = len(blob)
        for row in rows:
            blob.extend(struct.pack('<' + 'f'*len(row), *row))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0, byteOffset=start, byteLength=len(blob)-start))
        idx = len(doc['accessors'])
        item = dict(bufferView=view, componentType=5126, count=len(rows), type=kind)
        if kind == 'SCALAR':
            item.update(min=[rows[0][0]], max=[rows[-1][0]])
        doc['accessors'].append(item)
        return idx
    times = accessor([(recipe['duration_s']*i/(recipe['samples']-1),) for i in range(recipe['samples'])], 'SCALAR')
    changed = []
    for channel in clip['channels']:
        target = channel['target']
        name = doc['nodes'][target['node']].get('name')
        if target['path'] != 'rotation' or name not in TARGETS:
            continue
        rows = common.authored_rows(name, bases, recipe)
        clip['samplers'][channel['sampler']].update(input=times, output=accessor(rows, 'VEC4'), interpolation='LINEAR')
        changed.append(name)
    require(sorted(changed) == sorted(TARGETS), 'exactly two seated rotation targets required')
    doc['animations'].append(clip)
    doc['buffers'][0]['byteLength'] = len(blob)
    output = common.encode(doc, bytes(blob))
    check, output_bin = parse(output)
    for key in parent:
        if key not in ('animations', 'accessors', 'bufferViews', 'buffers'):
            require(check[key] == parent[key], 'protected seated JSON changed: '+key)
    require(check['animations'][:-1] == parent['animations'], 'original seated/standing/walk clips changed')
    require(check['accessors'][:len(parent['accessors'])] == parent['accessors'], 'original accessors changed')
    require(check['bufferViews'][:len(parent['bufferViews'])] == parent['bufferViews'], 'original views changed')
    require(output_bin[:len(binary)] == binary and check['buffers'][1:] == parent['buffers'][1:], 'original BIN/fallback changed')
    return output, dict(parent_sha256=expected_sha, sha256=sha(output), bytes=len(output),
                        original_bin_sha256=sha(binary), original_bin_bytes=len(binary),
                        original_bin_prefix_exact=True, old_clips_exact=True,
                        meshes_skins_images_nodes_materials_exact=True, new_clip=CLIP,
                        changed_rotation_targets=changed, non_head_neck_channels_unchanged=True)


def derive(row, recipe, raw=None):
    by_file = {p['file']: p for p in recipe['parents']}
    require(row['pose_parent_file'] in by_file and '/web/' not in row['pose_parent_file'], 'explicit master pose parent required')
    master = by_file[row['pose_parent_file']]
    require(master['asset_id'] == row['asset_id'] and master['lod'] == row['lod'], 'same resident and LOD pose parent required')
    bases = seated_pose(parent_bytes(master, recipe))
    return append_clip(parent_bytes(row, recipe) if raw is None else raw, row['sha256'], bases, recipe)


def chained_active_derivative(file, original):
    """Verify exact subsequent seated and selected garment terminal stages."""
    recipe = read_recipe()
    rows = [row for row in recipe['parents'] if row['file'] == file]
    require(len(rows) == 1 and sha(original) == rows[0]['sha256'], 'exact standing-to-seated parent chain required')
    seated_output = derive(rows[0], recipe, original)[0]
    from human_garment_retention import apply as garment_terminal
    return garment_terminal(file, seated_output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    recipe = read_recipe()
    require(args.check or not args.output.exists(), 'fresh seated output directory required')
    rows = []
    for row in recipe['parents']:
        output, proof = derive(row, recipe)
        if args.check:
            from human_garment_retention import apply as garment_terminal
            output = garment_terminal(row['file'], output)
            require((APP/row['file']).read_bytes() == output, 'active seated derivative does not reproduce: '+row['file'])
        else:
            destination = args.output/row['file']
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(output)
        rows.append(dict(file=row['file'], **proof))
    receipt = dict(schema='seated_driver_look_derivation_v2', recipe_sha256=sha(RECIPE.read_bytes()),
                   generator_sha256=sha(Path(__file__).read_bytes()), files=rows,
                   native_qualified=False, photographic_accepted=False,
                   scope='Exact animation-only regeneration; native skinning/contact and scene appearance are separate')
    if not args.check:
        (args.output/'DERIVATION.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(generated=len(rows), checked=args.check, native_qualified=False)))


if __name__ == '__main__':
    main()
