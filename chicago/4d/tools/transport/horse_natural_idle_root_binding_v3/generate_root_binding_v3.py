#!/usr/bin/env python3
"""Root-aware reconstructed mane binding, separate from failed v2 qualification."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

PARENT_SHA = '0ced8a09e27da047ad404c902e9d032e43654393027199db8dfd9c315be17929'
REFERENCE_SHA = 'a3eca1a164e2adf13d7d5f6699ff43de66d48dde0e3220f4aae90591dcaf4cb3'
GUIDE_IDS = [1524, 3256, 3243, 3204, 3070, 3078, 3083, 3090]
NOTICE = 'chicago4d_natural_planted_binding_v3'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read_glb(raw):
    magic, version, size, count, tag = struct.unpack_from('<5I', raw)
    need((magic, version, size, tag) == (0x46546c67, 2, len(raw), 0x4e4f534a), 'complete embedded GLB2')
    end = 20 + count
    length, tag = struct.unpack_from('<2I', raw, end)
    need(tag == 0x004e4942 and end + 8 + length == len(raw), 'complete embedded BIN')
    return json.loads(raw[20:end]), raw[end + 8:]

def write_glb(doc, binary):
    text = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode()
    text += b' ' * (-len(text) % 4)
    return (struct.pack('<5I', 0x46546c67, 2, 28 + len(text) + len(binary), len(text), 0x4e4f534a)
            + text + struct.pack('<2I', len(binary), 0x004e4942) + binary)

def stream(doc, binary, mesh, name):
    primitive = doc['meshes'][mesh]['primitives'][0]
    accessor = doc['accessors'][primitive['indices'] if name == 'indices' else primitive['attributes'][name]]
    view = doc['bufferViews'][accessor['bufferView']]
    need(not accessor.get('sparse') and not accessor.get('normalized'), 'explicit unnormalized dense source')
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    fmt = {5126: 'f', 5125: 'I', 5123: 'H'}[accessor['componentType']]
    size = struct.calcsize(fmt) * width
    stride = view.get('byteStride', size)
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    need(start + (accessor['count'] - 1) * stride + size <= len(binary), 'source stream bounded')
    return {'rows': [list(struct.unpack_from('<' + fmt * width, binary, start + i * stride))
                     for i in range(accessor['count'])], 'start': start, 'stride': stride,
            'size': size, 'format': '<' + fmt * width}

def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

def root_height(z, guide):
    if z <= guide[0][2]:
        return guide[0][1]
    if z >= guide[-1][2]:
        return guide[-1][1]
    for a, b in zip(guide, guide[1:]):
        if a[2] <= z <= b[2]:
            return a[1] + smooth(a[2], b[2], z) * (b[1] - a[1])
    raise ValueError('root profile coverage')

def axis_parameter(p):
    return ((p[1] - 1.3) * .18 + (p[2] - .55) * .48) / (.18 ** 2 + .48 ** 2)

def partition(s):
    # Exact same anatomically declared adjacent-control partition as v2. Only
    # the HAIR attachment coordinate changes, never the motion or a tolerance.
    if s <= .48:
        neck = smooth(.21, .48, s)
        return {1: 1 - neck, 2: neck}
    head = smooth(.48, .9, s)
    return {2: 1 - head, 3: head}

def source_domain(parent_raw, recipe_raw):
    need(sha(parent_raw) == PARENT_SHA, 'exact immutable failed-v2 candidate')
    recipe = json.loads(recipe_raw)
    need(recipe['schema'] == 'natural_planted_root_binding_v3_recipe'
         and recipe['source_parent_sha256'] == PARENT_SHA
         and recipe['paired_parent_sha256'] == REFERENCE_SHA, 'explicit new paired v3 recipe')
    need(recipe['field'] == 'C1_crestY_by_longitudinal_z_adjacent_control_partition_no_tipY', 'fixed root field definition')
    doc, binary = read_glb(parent_raw)
    positions = stream(doc, binary, 0, 'POSITION')['rows']
    guide_rows = recipe['source_root_guide']
    need([row['source_vertex'] for row in guide_rows] == GUIDE_IDS, 'reviewed eight actual source crest row IDs')
    guide = []
    for row in guide_rows:
        p = positions[row['source_vertex']]
        need(row['point_m'] == p and abs(p[0]) < .055, 'root guide point exact source geometry')
        guide.append(p)
    need(all(b[2] > a[2] for a, b in zip(guide, guide[1:])), 'monotonic longitudinal root guide')
    domain = set(recipe['head_rows'])
    need(len(domain) == len(recipe['head_rows']) == 2306
         and domain == {i for i, (x, y, z) in enumerate(positions) if y > 1.04 and z > .28},
         'entire existing reviewed2306 HAIR head/mane component, no widened rows')
    classes = {}
    for i, p in enumerate(positions):
        key = tuple(round(x / 1e-6) for x in p)
        classes.setdefault(key, []).append(i)
    need(all(not (set(rows) & domain) or set(rows) <= domain for rows in classes.values()), 'no mixed HAIR head/protected tail class')
    protected_classes = {tuple(round(x / 1e-6) for x in p)
                         for mesh in [1, 2] for p in stream(doc, binary, mesh, 'POSITION')['rows']}
    need(not protected_classes.intersection({key for key, rows in classes.items() if set(rows) & domain}),
         'no HAIR root class crosses protected BODY/EYE')
    core = [i for i in domain if axis_parameter(positions[i]) >= .9]
    need(len(core) == 1184 and all(axis_parameter([positions[i][0], root_height(positions[i][2], guide), positions[i][2]]) >= .9
                                 for i in core), 'every original skull core remains rigid HEAD3 independent of tip height')
    return doc, binary, positions, guide, domain, classes

def binding(parent_raw, recipe_raw):
    doc, binary, positions, guide, domain, classes = source_domain(parent_raw, recipe_raw)
    joints, weights = [stream(doc, binary, 0, name)['rows'] for name in ['JOINTS_0', 'WEIGHTS_0']]
    overlay, semantic = [], {}
    for rows in classes.values():
        if rows[0] not in domain:
            continue
        representative = min(rows)
        point = positions[representative]
        parameter = axis_parameter([point[0], root_height(point[2], guide), point[2]])
        desired = partition(parameter)
        need(all(weight == 0 or joint in {1, 2, 3} for row in rows for joint, weight in zip(joints[row], weights[row])),
             'source HAIR has no positive off-palette component to discard')
        mass = sum(weights[representative])
        values = [(joint, struct.unpack('<f', struct.pack('<f', mass * value))[0])
                  for joint, value in sorted(desired.items()) if value > 0]
        out_j, out_w = [0] * 4, [0.0] * 4
        for slot, (joint, value) in enumerate(values):
            out_j[slot], out_w[slot] = joint, value
        for row in rows:
            need(abs(sum(out_w) - sum(weights[row])) < 2e-7 and all(math.isfinite(x) and x >= 0 for x in out_w),
                 'finite nonnegative source-class mass preserved, no four-slot truncation')
            semantic[row] = [sum(w for j, w in zip(out_j, out_w) if j == bone) for bone in range(26)]
            if axis_parameter(positions[row]) >= .9:
                need(semantic[row][3] >= .9 and all(value == 0 for bone, value in enumerate(semantic[row]) if bone != 3),
                     'actual generated original skull-core tuple remains rigid HEAD3')
            if out_j != joints[row] or out_w != weights[row]:
                overlay.append({'row': row, 'joints': out_j[:], 'weights': out_w[:]})
    overlay.sort(key=lambda row: row['row'])
    indices = stream(doc, binary, 0, 'indices')['rows']
    maximum = {'l1_per_m': 0.0}
    for start in range(0, len(indices), 3):
        ids = [x[0] for x in indices[start:start + 3]]
        for a, b in [(ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])]:
            if a not in domain or b not in domain:
                continue
            length = math.dist(positions[a], positions[b])
            delta = sum(abs(x - y) for x, y in zip(semantic[a], semantic[b]))
            if length > 1e-9 and delta / length > maximum['l1_per_m']:
                maximum = {'l1_per_m': delta / length, 'edge': [a, b], 'length_m': length}
    return {'0': overlay}, {'head_rows': len(domain), 'changed_rows': len(overlay),
                            'canonical_head_weld_classes': sum(bool(set(rows) & domain) for rows in classes.values()),
                            'all1184_original_core_rigid_HEAD3': True, 'maximum_source_neighbor_weight_gradient': maximum}

def apply_overlay(raw, overlay, recipe_raw, expected_sha, role):
    need(sha(raw) == expected_sha, 'immutable declared v2 export parent')
    doc, binary = read_glb(raw)
    result = bytearray(binary)
    for name, key in [('JOINTS_0', 'joints'), ('WEIGHTS_0', 'weights')]:
        a = stream(doc, binary, 0, name)
        for row in overlay['0']:
            struct.pack_into(a['format'], result, a['start'] + row['row'] * a['stride'], *row[key])
    child = copy.deepcopy(doc)
    child.setdefault('asset', {}).setdefault('extras', {})[NOTICE] = {
        'source_parent_sha256': expected_sha, 'recipe_sha256': sha(recipe_raw), 'binding_version': 3,
        'role': role, 'qualification': 'UNRUN', 'old_certificate_transferred': False}
    out = write_glb(child, result)
    need(len(out) <= 4194304, 'unchanged four-MiB master cap')
    return out

def derive(parent, reference, recipe):
    need(sha(parent) == PARENT_SHA and sha(reference) == REFERENCE_SHA, 'exact v2 pair retained as immutable failed source')
    overlay, report = binding(parent, recipe)
    return (apply_overlay(parent, overlay, recipe, PARENT_SHA, 'natural-idle-rootbound-candidate'),
            apply_overlay(reference, overlay, recipe, REFERENCE_SHA, 'paired925-geometry-rootbound-reference'), overlay, report)

def audit(parent, reference, candidate, paired, recipe, overlay):
    changed_counts = []
    domain = set(json.loads(recipe)['head_rows'])
    for source, child, expected_sha, role in [(parent, candidate, PARENT_SHA, 'natural-idle-rootbound-candidate'),
                                             (reference, paired, REFERENCE_SHA, 'paired925-geometry-rootbound-reference')]:
        need(sha(source) == expected_sha, 'exact source parent identity')
        pd, pb = read_glb(source)
        cd, cb = read_glb(child)
        clean = copy.deepcopy(cd)
        notice = clean['asset']['extras'].pop(NOTICE)
        need(notice == {'source_parent_sha256': expected_sha, 'recipe_sha256': sha(recipe), 'binding_version': 3,
                        'role': role, 'qualification': 'UNRUN', 'old_certificate_transferred': False}, 'exact truthful v3 notice')
        need(clean == pd and len(pb) == len(cb), 'all unlisted metadata and exact BIN length retained')
        allowed = set()
        for name, key in [('JOINTS_0', 'joints'), ('WEIGHTS_0', 'weights')]:
            a = stream(pd, pb, 0, name)
            c = stream(cd, cb, 0, name)
            expected = {row['row']: row[key] for row in overlay['0']}
            need(len(expected) == len(overlay['0']) and set(expected) <= domain, 'unique rows inside reviewed2306 mane domain')
            for i, row in enumerate(a['rows']):
                need(c['rows'][i] == expected.get(i, row), 'every HAIR tuple is exact overlay or protected original tail')
            for i in expected:
                start = a['start'] + i * a['stride']
                allowed.update(range(start, start + a['size']))
        count = 0
        for offset, (a, b) in enumerate(zip(pb, cb)):
            if a != b:
                need(offset in allowed, 'every unlisted BIN byte including BODY/EYE/tail/UV/geometry/clip/images stays exactV2')
                count += 1
        changed_counts.append(count)
    cd, cb = read_glb(candidate)
    rd, rb = read_glb(paired)
    for mesh in range(3):
        for name in ['JOINTS_0', 'WEIGHTS_0']:
            need(stream(cd, cb, mesh, name)['rows'] == stream(rd, rb, mesh, name)['rows'], 'entire candidate/paired925 skin streams identical')
    return {'status': 'ROOT_BINDING_V3_STATIC_BYTE_DOMAIN_ONLY_PASS', 'candidate_sha256': sha(candidate),
            'paired925_sha256': sha(paired), 'recipe_sha256': sha(recipe), 'changed_BIN_bytes': changed_counts,
            'BODY_EYE_tail_outside_geometry_rig_images_UV_clips_exactV2': True,
            'old13_native129': 'UNRUN', 'new17_native129': 'UNRUN', 'paired925_socket129': 'UNRUN', 'runtime_adoption': False}

def inspect(parent, reference, candidate, paired, recipe):
    expected, expected_pair, overlay, field = derive(parent, reference, recipe)
    need(candidate == expected and paired == expected_pair, 'exact reproducible new root-aware exports')
    result = audit(parent, reference, candidate, paired, recipe, overlay)
    result['field_static'] = field
    return result

def controls(parent, reference, candidate, paired, recipe, overlay):
    doc, binary = read_glb(candidate)
    checks = []
    def refuse(name, bad_candidate=candidate, bad_pair=paired):
        try:
            audit(parent, reference, bad_candidate, bad_pair, recipe, overlay)
        except (ValueError, KeyError, IndexError):
            checks.append(name)
            return
        raise AssertionError('source corruption accepted: ' + name)
    for name, mesh, semantic, row in [('BODY_skin', 1, 'WEIGHTS_0', 1300), ('EYE_skin', 2, 'WEIGHTS_0', 0),
                                       ('HAIR_rest_POSITION', 0, 'POSITION', 2857), ('HAIR_rest_NORMAL', 0, 'NORMAL', 2857)]:
        a = stream(doc, binary, mesh, semantic)
        bad = bytearray(binary)
        bad[a['start'] + row * a['stride']] ^= 1
        refuse(name, write_glb(doc, bad))
    outside = next(i for i in range(len(stream(doc, binary, 0, 'POSITION')['rows'])) if i not in set(json.loads(recipe)['head_rows']))
    a = stream(doc, binary, 0, 'WEIGHTS_0')
    bad = bytearray(binary)
    bad[a['start'] + outside * a['stride']] ^= 1
    refuse('original969_tail_skin', write_glb(doc, bad))
    pd, pb = read_glb(paired)
    bad = bytearray(pb)
    a = stream(pd, pb, 0, 'WEIGHTS_0')
    bad[a['start'] + 2857 * a['stride']] ^= 1
    refuse('paired925_tuple_mismatch', bad_pair=write_glb(pd, bad))
    for name, mutate in [('old_clip_changed', lambda d: d['animations'][0].update(name='bad')),
                         ('new17_clip_changed', lambda d: d['animations'][1].update(name='bad')),
                         ('rig_changed', lambda d: d['nodes'][2].update(translation=[0, 0, 0])),
                         ('false_certificate_transfer', lambda d: d['asset']['extras'][NOTICE].update(old_certificate_transferred=True))]:
        bad = copy.deepcopy(doc)
        mutate(bad)
        refuse(name, write_glb(bad, binary))
    bad = json.loads(recipe)
    bad['source_root_guide'][0]['point_m'][1] += .001
    try:
        source_domain(parent, json.dumps(bad).encode())
    except ValueError:
        checks.append('rootguide_source_coordinate_changed')
    else:
        raise AssertionError('invented root guide point accepted')
    need(len(checks) == 11, 'all eleven independent actual source corruptions exercised')
    return checks

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['parent', 'reference', 'recipe', 'candidate_out', 'paired_out', 'report_out', 'overlay_out']:
        parser.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    args = parser.parse_args()
    for path in [args.candidate_out, args.paired_out, args.report_out, args.overlay_out]:
        need(not path.exists(), 'fresh explicit output required')
    parent, reference, recipe = args.parent.read_bytes(), args.reference.read_bytes(), args.recipe.read_bytes()
    candidate, paired, overlay, _ = derive(parent, reference, recipe)
    report = inspect(parent, reference, candidate, paired, recipe)
    report['source_corruption_controls'] = controls(parent, reference, candidate, paired, recipe, overlay)
    args.candidate_out.write_bytes(candidate)
    args.paired_out.write_bytes(paired)
    args.report_out.write_text(json.dumps(report, indent=2) + '\n')
    args.overlay_out.write_text(json.dumps(overlay, separators=(',', ':')) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
