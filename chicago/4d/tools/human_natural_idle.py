#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Append an authored portable standing clip to exact, qualified parent GLBs.

This changes animation only. It is a separately generated derivative, not another
canonical Blender run. The original clips and every original BIN byte survive.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess

APP = Path(__file__).resolve().parents[1]
RECIPE = APP / 'data/humans/animations/natural-standing-v1.json'
CLIP = 'idle_natural_v1'
TARGETS = ('spine_02', 'neck_01', 'head')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parent_bytes(row, recipe):
    """Canonical parents remain recoverable after installing an animation child."""
    require(re.fullmatch(r'assets/humans/(?:web/)?bardwell_otis_1835\.lod[0-3]\.glb', row['file']) is not None,
            'explicit existing resident parent path required')
    local = APP/row['file']
    if local.exists():
        raw = local.read_bytes()
        if sha(raw) == row['sha256']:
            return raw
    revision = recipe['parent_revision']
    require(re.fullmatch(r'[0-9a-f]{40}', revision) is not None, 'exact parent Git revision required')
    # Read a pinned, existing Git blob. Never fetch, check out, rewrite or prune.
    raw = subprocess.check_output(['git', '-C', str(APP), 'show', revision+':chicago/4d/'+row['file']])
    require(sha(raw) == row['sha256'], 'pinned canonical Git parent SHA mismatch')
    return raw


def parse(raw):
    require(len(raw) >= 28 and struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'complete GLB2 required')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a and size % 4 == 0 and 20 + size + 8 <= len(raw), 'JSON chunk required')
    doc = json.loads(raw[20:20 + size])
    length, kind = struct.unpack_from('<II', raw, 20 + size)
    binary = raw[28 + size:]
    require(kind == 0x004e4942 and length == len(binary) and length % 4 == 0, 'single complete BIN required')
    require(doc['buffers'][0].get('uri') is None and doc['buffers'][0]['byteLength'] <= len(binary), 'embedded buffer0 required')
    return doc, binary


def encode(doc, binary):
    payload = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode()
    payload += b' ' * (-len(payload) % 4)
    binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<III', 0x46546c67, 2, 28 + len(payload) + len(binary))
            + struct.pack('<II', len(payload), 0x4e4f534a) + payload
            + struct.pack('<II', len(binary), 0x004e4942) + binary)


def quat_mul(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X + x*W + y*Z - z*Y, w*Y - x*Z + y*W + z*X,
            w*Z + x*Y - y*X + z*W, w*W - x*X - y*Y - z*Z)


def inverse(q):
    n = sum(v*v for v in q)
    require(n > .999 and n < 1.001, 'unit rigid quaternion required')
    return (-q[0]/n, -q[1]/n, -q[2]/n, q[3]/n)


def axis_quat(axis, degrees):
    s = math.sin(math.radians(degrees) / 2)
    return tuple(v*s for v in axis) + (math.cos(math.radians(degrees)/2),)


def float_rows(doc, binary, index, kind):
    accessor = doc['accessors'][index]
    require(accessor['componentType'] == 5126 and accessor['type'] == kind
            and not accessor.get('sparse') and not accessor.get('normalized'), 'uncompressed FLOAT source channel required')
    view = doc['bufferViews'][accessor['bufferView']]
    require(view['buffer'] == 0 and not view.get('extensions'), 'uncompressed source channel required')
    width = {'SCALAR': 1, 'VEC4': 4}[kind]
    stride = view.get('byteStride', width*4)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    require(offset + (accessor['count']-1)*stride + width*4 <= len(binary), 'channel outside BIN')
    rows = [struct.unpack_from('<' + 'f'*width, binary, offset + i*stride) for i in range(accessor['count'])]
    require(all(math.isfinite(v) for row in rows for v in row), 'nonfinite animation')
    return rows


def source_pose(doc, binary):
    idle = [a for a in doc['animations'] if a.get('name') == 'idle']
    require(len(idle) == 1, 'one exact parent idle required')
    rotations = {i: tuple(n.get('rotation', [0, 0, 0, 1])) for i, n in enumerate(doc['nodes'])}
    channels = {}
    for channel in idle[0]['channels']:
        target = channel['target']
        if target['path'] != 'rotation':
            continue
        sampler = idle[0]['samplers'][channel['sampler']]
        rotations[target['node']] = float_rows(doc, binary, sampler['output'], 'VEC4')[0]
        channels[doc['nodes'][target['node']].get('name')] = channel
    require(all(n in channels for n in TARGETS), 'required original upper-body channels missing')
    parents = {child: i for i, node in enumerate(doc['nodes']) for child in node.get('children', [])}
    worlds = {}

    def world(i):
        if i not in worlds:
            worlds[i] = quat_mul(world(parents[i]), rotations[i]) if i in parents else rotations[i]
        return worlds[i]

    bases = {}
    for name in TARGETS:
        i = channels[name]['target']['node']
        bases[name] = {'local': rotations[i], 'parent_world': world(parents[i]) if i in parents else (0, 0, 0, 1)}
    return bases


def authored_angles(name, phase, recipe):
    """World-axis angles: plain standing, no gesture, translation or foot motion."""
    bounds = recipe['motion_degrees']
    if name == 'spine_02':
        return ((1, 0, 0), bounds['breath_pitch'] * math.sin(2*phase)),
    if name == 'neck_01':
        return ((0, 1, 0), bounds['neck_look_yaw'] * math.sin(phase)),
    if name == 'head':
        return (((0, 1, 0), bounds['head_look_yaw'] * math.sin(phase)),
                ((1, 0, 0), bounds['head_nod_pitch'] * math.sin(2*phase)))
    raise ValueError('Natural standing must not add arm, elbow or lower-body curves')


def authored_rows(name, bases, recipe):
    base = bases[name]
    parent = base['parent_world']
    rows = []
    for key in range(recipe['samples']):
        phase = 2*math.pi*key/(recipe['samples']-1)
        delta = (0, 0, 0, 1)
        for axis, angle in authored_angles(name, phase, recipe):
            delta = quat_mul(delta, axis_quat(axis, angle))
        local_delta = quat_mul(quat_mul(inverse(parent), delta), parent)
        q = quat_mul(local_delta, base['local'])
        length = math.sqrt(sum(v*v for v in q))
        rows.append(tuple(v/length for v in q))
    rows[-1] = rows[0]  # Exact stored loop endpoint, independent of sine roundoff.
    return rows


def append_clip(raw, expected_sha, bases, recipe):
    require(sha(raw) == expected_sha, 'parent SHA mismatch')
    parent, binary = parse(raw)
    doc = copy.deepcopy(parent)
    require(not any(a.get('name') == CLIP for a in doc['animations']), 'derivative already installed')
    idle = [a for a in doc['animations'] if a.get('name') == 'idle']
    require(len(idle) == 1, 'one parent idle required')
    clip = copy.deepcopy(idle[0])
    clip['name'] = CLIP
    clip['extras'] = {'loop': True, 'cycle_duration_s': recipe['duration_s'], 'in_place': True,
                      'motion_basis': recipe['basis'], 'derivation': 'portable CPU animation derivative; original canonical clips preserved'}
    clip['extras'].update(liberty=recipe['liberty'], recipe='data/humans/animations/natural-standing-v1.json',
                         canonical_rig_pose_parent_sha256=recipe['parents'][0]['sha256'])
    blob = bytearray(binary)

    def accessor(rows, kind):
        blob.extend(b'\0' * (-len(blob) % 4))
        start = len(blob)
        for row in rows:
            blob.extend(struct.pack('<' + 'f'*len(row), *row))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(blob)-start})
        idx = len(doc['accessors'])
        item = {'bufferView': view, 'componentType': 5126, 'count': len(rows), 'type': kind}
        if kind == 'SCALAR':
            item.update(min=[rows[0][0]], max=[rows[-1][0]])
        doc['accessors'].append(item)
        return idx

    time = accessor([(recipe['duration_s'] * i/(recipe['samples']-1),) for i in range(recipe['samples'])], 'SCALAR')
    replaced = []
    for channel in clip['channels']:
        target = channel['target']
        name = doc['nodes'][target['node']].get('name')
        if target['path'] != 'rotation' or name not in TARGETS:
            continue
        rows = authored_rows(name, bases, recipe)
        sampler = clip['samplers'][channel['sampler']]
        sampler.update(input=time, output=accessor(rows, 'VEC4'), interpolation='LINEAR')
        replaced.append(name)
    require(sorted(replaced) == sorted(TARGETS), 'missing/duplicate qualified upper-body targets')
    doc['animations'].append(clip)
    doc['buffers'][0]['byteLength'] = len(blob)
    output = encode(doc, bytes(blob))
    check, result_binary = parse(output)
    for key in parent:
        if key not in ('animations', 'accessors', 'bufferViews', 'buffers'):
            require(check[key] == parent[key], 'protected JSON changed: ' + key)
    require(check['animations'][:-1] == parent['animations'], 'original clips changed')
    require(check['accessors'][:len(parent['accessors'])] == parent['accessors'], 'original accessors changed')
    require(check['bufferViews'][:len(parent['bufferViews'])] == parent['bufferViews'], 'original views changed')
    require(check['buffers'][1:] == parent['buffers'][1:] and result_binary[:len(binary)] == binary, 'original BIN/fallback buffers changed')
    return output, {'parent_sha256': expected_sha, 'sha256': sha(output), 'bytes': len(output),
                    'original_bin_bytes': len(binary), 'original_bin_sha256': sha(binary),
                    'original_bin_prefix_exact': True, 'old_clips_exact': True,
                    'meshes_skins_images_nodes_materials_exact': True,
                    'new_clip': CLIP, 'changed_rotation_targets': replaced,
                    'lower_body_channels_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path, help='separate derivative directory; never overwrites canonical parent')
    mode.add_argument('--check', action='store_true', help='reproduce all eight active derivatives from their immutable parents')
    args = parser.parse_args()
    recipe = json.loads(RECIPE.read_text())
    require(recipe['clip'] == CLIP and recipe['samples'] == 65 and recipe['duration_s'] == 8, 'reviewed recipe domain changed')
    require(args.check or not args.output.exists(), 'fresh output directory required')
    master = recipe['parents'][0]
    require('/web/' not in master['file'], 'first parent must be uncompressed master')
    raw = parent_bytes(master, recipe)
    require(sha(raw) == master['sha256'], 'base master SHA mismatch')
    bases = source_pose(*parse(raw))
    results = []
    for row in recipe['parents']:
        output, proof = append_clip(parent_bytes(row, recipe), row['sha256'], bases, recipe)
        if args.check:
            require((APP/row['file']).read_bytes() == output, 'active derivative does not reproduce: '+row['file'])
        else:
            destination = args.output/row['file']
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(output)
        results.append(dict(file=row['file'], **proof))
    if args.check:
        print(json.dumps({'reproduced_active_derivatives': len(results), 'passed': True,
                          'scope': 'Exact animation derivative regeneration; not native, garment or photographic qualification'}))
        return
    receipt = {'schema': 'human_natural_idle_derivation_v1', 'recipe_sha256': sha(RECIPE.read_bytes()),
               'generator_sha256': sha(Path(__file__).read_bytes()), 'files': results,
               'scope': 'Generated animation-only derivative. Actual loader, contact, garment and scene qualification pending; no canonical CI transfer.',
               'actual_native_qualified': False, 'photographic_accepted': False}
    (args.output/'DERIVATION.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'generated': len(results), 'receipt': str(args.output/'DERIVATION.json'), 'native_qualified': False}))


if __name__ == '__main__':
    main()
