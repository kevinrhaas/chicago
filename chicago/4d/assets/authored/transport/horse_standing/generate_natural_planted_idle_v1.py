#!/usr/bin/env python3
"""Prepare a new portable glTF idle, retaining the exact qualified parent.

This is an unexecuted source proposal. A successful export is not physical,
socket, browser, photographic, gait or rider acceptance.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

EXPECTED_PARENT = 'bd443df87b92d19266284cb9b52d30e791215cddf099876c774e9cfb5f5a79b6'
PARENT_CLIP = 'sevket_reconstructed_planted_posture_v1'
NEW_CLIP = 'sevket_reconstructed_natural_planted_idle_v1'
NAMES = {2: 'horse_neck', 3: 'horse_head', 4: 'horse_tail_base', 5: 'horse_tail_tip'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_glb(raw):
    need(len(raw) >= 28, 'complete GLB required')
    magic, version, length, count, tag = struct.unpack_from('<5I', raw)
    need(magic == 0x46546c67 and version == 2 and length == len(raw) and tag == 0x4e4f534a,
         'complete glTF2 JSON-first binary required')
    offset = 20 + count
    binary_length, binary_tag = struct.unpack_from('<2I', raw, offset)
    need(binary_tag == 0x004e4942 and offset + 8 + binary_length == len(raw),
         'exact embedded BIN chunk required')
    return json.loads(raw[20:offset]), raw[offset + 8:]


def write_glb(doc, binary):
    need(len(binary) % 4 == 0, 'BIN alignment')
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    size = 12 + 8 + len(encoded) + 8 + len(binary)
    return (struct.pack('<3I', 0x46546c67, 2, size)
            + struct.pack('<2I', len(encoded), 0x4e4f534a) + encoded
            + struct.pack('<2I', len(binary), 0x004e4942) + binary)


def scalar_curve(time, knots):
    """C1 authored waypoint interpolation; endpoint quaternions are exact rest."""
    need(knots[0] == [0, 0] and knots[-1] == [12, 0], 'neutral closed waypoints')
    if time <= 0 or time >= 12:
        return 0.0
    for (start, a), (end, b) in zip(knots, knots[1:]):
        if start <= time <= end:
            fraction = (time - start) / (end - start)
            fraction = fraction * fraction * (3 - 2 * fraction)
            return a + (b - a) * fraction
    raise ValueError('curve did not cover requested time')


def local_quaternion(node, time, recipe):
    """Engine-neutral local bone rotation, exported as real glTF keys."""
    if time == 0 or time == 12:
        return [0.0, 0.0, 0.0, 1.0]
    limits = recipe['max_local_rotation_degrees']
    if node in (2, 3):
        name = 'neck' if node == 2 else 'head'
        yaw = math.radians(limits[name + '_yaw'] * scalar_curve(time, recipe['look_shape_knots'])) / 2
        pitch = math.radians(limits[name + '_pitch'] * scalar_curve(time, recipe['nod_shape_knots'])) / 2
        # Hamilton product qYawY * qPitchX, glTF component order x,y,z,w.
        return [math.cos(yaw) * math.sin(pitch), math.sin(yaw) * math.cos(pitch),
                -math.sin(yaw) * math.sin(pitch), math.cos(yaw) * math.cos(pitch)]
    name = 'tail_base' if node == 4 else 'tail_tip'
    angle = math.radians(limits[name + '_roll']
                         * scalar_curve(time, recipe[name + '_shape_knots'])) / 2
    return [0.0, 0.0, math.sin(angle), math.cos(angle)]


def read_times(doc, binary, index):
    accessor = doc['accessors'][index]
    view = doc['bufferViews'][accessor['bufferView']]
    need(accessor['componentType'] == 5126 and accessor['type'] == 'SCALAR'
         and accessor['count'] == 65 and not view.get('byteStride'), '65 packed FLOAT times')
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    times = list(struct.unpack_from('<65f', binary, offset))
    need(times == [12 * i / 64 for i in range(65)], 'exact original65 time grid')
    return times


def derive(parent_raw, recipe_raw):
    recipe = json.loads(recipe_raw)
    need(sha(parent_raw) == EXPECTED_PARENT == recipe['source_parent_sha256'], 'exact qualified bd443 parent')
    need(len(parent_raw) == recipe['parent_bytes'] == 4159196, 'exact parent byte count')
    need(recipe['duration_s'] == 12 and recipe['key_count'] == 65
         and recipe['parent_clip'] == PARENT_CLIP and recipe['candidate_clip'] == NEW_CLIP,
         'explicit distinct portable clip contract')
    parent, parent_binary = read_glb(parent_raw)
    need(len(parent['buffers']) == 1 and not parent['buffers'][0].get('uri'), 'embedded source only')
    need(len(parent['animations']) == 1 and parent['animations'][0]['name'] == PARENT_CLIP,
         'one genuine existing planted clip')
    old_clip = parent['animations'][0]
    need(len(old_clip['channels']) == len(old_clip['samplers']) == 13, 'old13 tracks retained')
    for node, name in NAMES.items():
        need(parent['nodes'][node]['name'] == name and not parent['nodes'][node].get('rotation'),
             'exact identity-rest target joint ' + name)
    need(all(channel['target']['node'] not in NAMES for channel in old_clip['channels']),
         'new joints are genuinely unanimated in parent')
    input_id = old_clip['samplers'][0]['input']
    times = read_times(parent, parent_binary, input_id)
    need(all(sampler['input'] == input_id for sampler in old_clip['samplers']), 'one genuine shared time accessor')
    child = copy.deepcopy(parent)
    binary = bytearray(parent_binary)
    clip = copy.deepcopy(old_clip)
    clip['name'] = NEW_CLIP
    clip['extras'] = {'source_parent_sha256': EXPECTED_PARENT, 'recipe_sha256': sha(recipe_raw),
                      'authorship': 'Project-authored reconstructed head look and tail flick.',
                      'walking_enabled': False, 'independent_ears': False,
                      'qualification': 'UNRUN; no previous13track certificate transferred'}
    for node in NAMES:
        quaternions = [local_quaternion(node, time, recipe) for time in times]
        raw = struct.pack('<260f', *(value for quaternion in quaternions for value in quaternion))
        offset = len(binary)
        binary.extend(raw)
        view = len(child['bufferViews'])
        child['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(raw)})
        output = len(child['accessors'])
        child['accessors'].append({'bufferView': view, 'componentType': 5126, 'count': 65, 'type': 'VEC4'})
        sampler = len(clip['samplers'])
        clip['samplers'].append({'input': input_id, 'output': output, 'interpolation': 'LINEAR'})
        clip['channels'].append({'sampler': sampler, 'target': {'node': node, 'path': 'rotation'}})
    child['animations'].append(clip)
    child['buffers'][0]['byteLength'] = len(binary)
    child.setdefault('asset', {}).setdefault('extras', {})['chicago4d_natural_planted_idle_v1'] = {
        'source_parent_sha256': EXPECTED_PARENT, 'recipe_sha256': sha(recipe_raw),
        'new_clip': NEW_CLIP, 'source_geometry_rig_weights_and_parent_animation_unchanged': True,
        'old_certificate_transferred': False, 'new_native_physical_and_socket_qualification': 'UNRUN'}
    candidate = write_glb(child, bytes(binary))
    need(len(candidate) <= 4 * 1024 * 1024, 'unchanged4MiB standing master cap')
    inspect(parent_raw, candidate, recipe_raw)
    return candidate


def inspect(parent_raw, candidate_raw, recipe_raw):
    recipe = json.loads(recipe_raw)
    parent, old_binary = read_glb(parent_raw)
    child, binary = read_glb(candidate_raw)
    need(sha(parent_raw) == EXPECTED_PARENT, 'parent identity')
    need(binary[:len(old_binary)] == old_binary and len(binary) == len(old_binary) + 4160,
         'all original BIN bytes preserved and only4new65quaternion streams appended')
    for key in ('nodes', 'meshes', 'skins', 'materials', 'images', 'textures', 'samplers',
                'scenes', 'scene', 'extensionsUsed', 'extensionsRequired'):
        need(child.get(key) == parent.get(key), 'protected source document field ' + key)
    need(child['accessors'][:len(parent['accessors'])] == parent['accessors'], 'every original accessor exact')
    need(child['bufferViews'][:len(parent['bufferViews'])] == parent['bufferViews'], 'every original bufferView exact')
    need(child['animations'][:1] == parent['animations'] and len(child['animations']) == 2,
         'genuine parent clip retained byte-semantically, exactlyone added clip')
    old = parent['animations'][0]
    new = child['animations'][1]
    need(new['name'] == NEW_CLIP and new['channels'][:13] == old['channels']
         and new['samplers'][:13] == old['samplers'], 'exact inherited13track playback in new clip')
    need(len(new['channels']) == len(new['samplers']) == 17, 'explicit new17channel clip')
    need([channel['target'] for channel in new['channels'][13:]]
         == [{'node': node, 'path': 'rotation'} for node in NAMES], 'only declared head/neck/tail rotations')
    need(child['asset']['extras']['chicago4d_natural_planted_idle_v1']['recipe_sha256'] == sha(recipe_raw),
         'exact recipe binding')
    need(len(child['accessors']) == len(parent['accessors']) + 4
         and len(child['bufferViews']) == len(parent['bufferViews']) + 4,
         'exactlyfour appended output accessors/views')
    input_id = old['samplers'][0]['input']
    times = read_times(parent, old_binary, input_id)
    for added, node in enumerate(NAMES):
        output_id = len(parent['accessors']) + added
        view_id = len(parent['bufferViews']) + added
        offset = len(old_binary) + added * 1040
        need(new['samplers'][13 + added] == {'input': input_id, 'output': output_id, 'interpolation': 'LINEAR'},
             'new selected sampler requires exact original time input, declared output and LINEAR interpolation')
        need(child['accessors'][output_id] == {'bufferView': view_id, 'componentType': 5126, 'count': 65, 'type': 'VEC4'},
             'exact new packed65 FLOAT quaternion accessor')
        need(child['bufferViews'][view_id] == {'buffer': 0, 'byteOffset': offset, 'byteLength': 1040},
             'exact in-bounds new quaternion output view')
        actual = binary[offset:offset + 1040]
        expected = struct.pack('<260f', *(value for time in times for value in local_quaternion(node, time, recipe)))
        need(actual == expected, 'new quaternion stream differs from declared recipe at joint ' + str(node))
        values = struct.unpack('<260f', actual)
        need(all(math.isfinite(value) for value in values), 'all quaternion components finite')
        for index in range(65):
            q = values[4 * index:4 * index + 4]
            need(abs(sum(value * value for value in q) - 1) <= 1e-6, 'normalized exported FLOAT quaternion')
        need(values[:4] == values[-4:] == (0.0, 0.0, 0.0, 1.0), 'exact new neutral closed quaternion loop')
    restored = copy.deepcopy(child)
    restored['accessors'] = restored['accessors'][:len(parent['accessors'])]
    restored['bufferViews'] = restored['bufferViews'][:len(parent['bufferViews'])]
    restored['animations'] = restored['animations'][:1]
    restored['buffers'][0]['byteLength'] = parent['buffers'][0]['byteLength']
    del restored['asset']['extras']['chicago4d_natural_planted_idle_v1']
    need(restored == parent, 'all unlisted parent metadata and document fields exact')
    need(len(candidate_raw) <= 4 * 1024 * 1024, 'unchanged4MiB standing master cap')
    return {'status': 'PORTABLE_SOURCE_STRUCTURE_ONLY_PASS_NOT_PHYSICAL_OR_VISUAL_ACCEPTANCE',
            'parent_sha256': sha(parent_raw), 'candidate_sha256': sha(candidate_raw),
            'candidate_bytes': len(candidate_raw), 'recipe_sha256': sha(recipe_raw),
            'parent_bin_prefix_bytes_exact': len(old_binary), 'new_animation_output_bytes': 4160,
            'old_clips_retained': True, 'new_channels': list(NAMES.values()),
            'new_qualification': 'UNRUN', 'walk_trot': False, 'photographic_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    need(not args.out.exists(), 'fresh explicit output required')
    parent_raw, recipe_raw = args.parent.read_bytes(), args.recipe.read_bytes()
    candidate = derive(parent_raw, recipe_raw)
    args.out.write_bytes(candidate)
    print(json.dumps(inspect(parent_raw, candidate, recipe_raw), indent=2))


if __name__ == '__main__':
    main()
