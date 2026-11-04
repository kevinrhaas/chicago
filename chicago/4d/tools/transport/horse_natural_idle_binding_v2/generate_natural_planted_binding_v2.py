#!/usr/bin/env python3
"""Portable anatomical binding authoring; export alone is no motion acceptance."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

PARENT_SHA = '8ea7748ffba6c5fe17cde91042c6d8b26ed9a0ab77de69cadd4f4fb12e9c09fa'
REFERENCE_SHA = '925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48'
NOTICE = 'chicago4d_natural_planted_binding_v2'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read_glb(raw):
    magic, version, size, count, tag = struct.unpack_from('<5I', raw)
    need((magic, version, size, tag) == (0x46546c67, 2, len(raw), 0x4e4f534a), 'complete GLB2')
    end = 20 + count
    n, tag = struct.unpack_from('<2I', raw, end)
    need(tag == 0x004e4942 and end + 8 + n == len(raw), 'one complete embedded BIN')
    return json.loads(raw[20:end]), raw[end + 8:]

def write_glb(doc, binary):
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    return (struct.pack('<5I', 0x46546c67, 2, 28 + len(encoded) + len(binary), len(encoded), 0x4e4f534a)
            + encoded + struct.pack('<2I', len(binary), 0x004e4942) + binary)

def stream(doc, binary, mesh, semantic):
    p = doc['meshes'][mesh]['primitives'][0]
    a = doc['accessors'][p['indices'] if semantic == 'indices' else p['attributes'][semantic]]
    v = doc['bufferViews'][a['bufferView']]
    need(not a.get('sparse') and not a.get('normalized'), 'explicit source streams')
    q = {'VEC3': 3, 'VEC4': 4, 'SCALAR': 1}[a['type']]
    f = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
    size = struct.calcsize(f) * q
    stride = v.get('byteStride', size)
    start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    need(stride >= size and start + (a['count'] - 1) * stride + size <= len(binary), 'bounded source stream')
    return {'rows': [list(struct.unpack_from('<' + f * q, binary, start + i * stride)) for i in range(a['count'])],
            'start': start, 'stride': stride, 'size': size, 'format': '<' + f * q}

def smooth(a, b, x):
    need(a < b, 'ordered anatomical transition')
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)

def axis_parameter(point, origin, tip):
    axis = [tip[k] - origin[k] for k in range(3)]
    return sum((point[k] - origin[k]) * axis[k] for k in range(3)) / sum(v * v for v in axis)

def target(point, region, field):
    if region == 'head_neck':
        s = axis_parameter(point, field['neck'], field['head'])
        if s <= field['neck_middle_s']:
            neck = smooth(field['body_boundary_s'], field['neck_middle_s'], s)
            return {1: 1 - neck, 2: neck}, smooth(field['body_boundary_s'], field['full_support_s'], s)
        head = smooth(field['neck_middle_s'], field['skull_core_s'], s)
        return {2: 1 - head, 3: head}, 1.0
    t = axis_parameter(point, field['tail_base'], field['tail_tip'])
    root = smooth(field['tail_root_start_s'], field['tail_root_end_s'], t)
    tip = smooth(field['tail_tip_start_s'], field['tail_tip_end_s'], t)
    return {1: 1 - root, 4: root * (1 - tip), 5: root * tip}, 1.0

def new_tuple(point, joints, weights, region, mesh, field):
    allowed = {1, 2, 3} if region == 'head_neck' else {1, 4, 5}
    desired, support = target(point, region, field)
    if region == 'tail' and mesh == 1:
        # C1 BODY-only support at each reviewed dock-mask boundary. This never
        # affects the skull, jaw, muzzle, eyes or cervical support.
        x, y, z = point
        support *= (smooth(0.0, field['tail_dock_x_width_m'], .22 - abs(x))
                    * smooth(0.0, field['tail_dock_y_width_m'], y - 1.08)
                    * smooth(0.0, field['tail_dock_z_width_m'], -.78 - z))
    if support == 0:
        return joints[:], weights[:]
    mass = sum(w for j, w in zip(joints, weights) if j in allowed)
    dense = {}
    for j, w in zip(joints, weights):
        if j in allowed:
            dense[j] = dense.get(j, 0.0) + (1 - support) * w
    for j, fraction in desired.items():
        dense[j] = dense.get(j, 0.0) + support * mass * fraction
    # Positive influences outside the authored palette keep their original slot
    # and exact float bits, even if arbitrarily small. No top-four truncation.
    out_j, out_w = [0] * 4, [0.0] * 4
    protected = {k for k, (j, w) in enumerate(zip(joints, weights)) if j not in allowed and w > 0}
    for k in protected:
        out_j[k], out_w[k] = joints[k], weights[k]
    values = [(j, w) for j, w in sorted(dense.items()) if w > 0]
    slots = [k for k in range(4) if k not in protected]
    need(len(values) <= len(slots), 'anatomical palette does not fit four slots; no influence may be dropped')
    for k, (j, w) in zip(slots, values):
        out_j[k], out_w[k] = j, struct.unpack('<f', struct.pack('<f', w))[0]
    return out_j, out_w

def binding(parent_raw, recipe_raw):
    need(sha(parent_raw) == PARENT_SHA, 'exact failed-motion source; never overwrite or retarget its verdict')
    recipe = json.loads(recipe_raw)
    need(recipe['schema'] == 'natural_planted_binding_v2_recipe' and recipe['source_parent_sha256'] == PARENT_SHA,
         'explicit versioned binding recipe')
    doc, binary = read_glb(parent_raw)
    masks = recipe['allowed_row_masks']
    field = recipe['field']
    need(field == {'neck': [0, 1.3, .55], 'head': [0, 1.48, 1.03], 'body_boundary_s': .21,
                   'neck_middle_s': .48, 'full_support_s': .40, 'skull_core_s': .9,
                   'tail_base': [0, 1.28, -.85], 'tail_tip': [0, .6, -1.1],
                   'tail_root_start_s': -.12, 'tail_root_end_s': .15,
                   'tail_tip_start_s': .18, 'tail_tip_end_s': 1.0,
                   'tail_dock_x_width_m': .12, 'tail_dock_y_width_m': .12, 'tail_dock_z_width_m': .15},
         'reviewed fixed anatomical field; no pose-fitted parameters')
    overlay, reports = {}, []
    for mesh, label in [(0, 'HAIR'), (1, 'BODY')]:
        p, j, w = [stream(doc, binary, mesh, s) for s in ('POSITION', 'JOINTS_0', 'WEIGHTS_0')]
        head = set(masks[label + '_head_neck'])
        tail = set(masks['HAIR_original_tail_component' if mesh == 0 else 'BODY_tail_dock'])
        need(not head.intersection(tail), 'disjoint authored regions')
        expected_head = {i for i, (_, y, z) in enumerate(p['rows']) if y > 1.04 and z > .28}
        need(head == expected_head, 'fixed reviewed anatomical head domain regenerated from source geometry')
        if mesh == 1:
            need(tail == {i for i, (x, y, z) in enumerate(p['rows']) if abs(x) < .22 and z < -.78 and y > 1.08},
                 'fixed reviewed BODY dock domain regenerated from source geometry')
        need(len(head) == (2306 if mesh == 0 else 2913) and len(tail) == (969 if mesh == 0 else 78),
             'reviewed mask cardinalities')
        classes, changed, max_gradient = {}, [], {'l1_per_m': 0.0}
        tuples = {}
        for i in sorted(head | tail):
            region = 'head_neck' if i in head else 'tail'
            out_j, out_w = new_tuple(p['rows'][i], j['rows'][i], w['rows'][i], region, mesh, field)
            need(all(math.isfinite(v) and v >= 0 for v in out_w) and abs(sum(out_w) - sum(w['rows'][i])) < 2e-7,
                 'finite nonnegative preserved skin mass')
            need(all(v == 0 or 0 <= k < 26 for k, v in zip(out_j, out_w)), 'positive influences in genuine 26-joint palette')
            key = tuple(round(v / 1e-6) for v in p['rows'][i])
            semantic = [sum(v for k, v in zip(out_j, out_w) if k == bone) for bone in range(26)]
            need(key not in classes or classes[key] == semantic, 'welded canonical semantic class consistency')
            classes[key] = semantic
            tuples[i] = semantic
            if out_j != j['rows'][i] or out_w != w['rows'][i]:
                changed.append({'row': i, 'joints': out_j, 'weights': out_w})
            if region == 'head_neck' and axis_parameter(p['rows'][i], field['neck'], field['head']) >= .9:
                need(semantic[3] >= .9 and all(semantic[k] == 0 for k in range(26) if k != 3),
                     'entire skull/jaw/muzzle core is rigid HEAD3 without height taper')
        # Static source-neighbor gradient is disclosed, never a motion verdict.
        indices = stream(doc, binary, mesh, 'indices')['rows']
        for start in range(0, len(indices), 3):
            ids = [v[0] for v in indices[start:start + 3]]
            for a, b in [(ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])]:
                if a not in tuples and b not in tuples:
                    continue
                da = tuples.get(a, [sum(v for k, v in zip(j['rows'][a], w['rows'][a]) if k == bone) for bone in range(26)])
                db = tuples.get(b, [sum(v for k, v in zip(j['rows'][b], w['rows'][b]) if k == bone) for bone in range(26)])
                length = math.dist(p['rows'][a], p['rows'][b])
                gradient = sum(abs(x - y) for x, y in zip(da, db)) / length if length > 1e-9 else 0
                if gradient > max_gradient['l1_per_m']:
                    max_gradient = {'l1_per_m': gradient, 'edge': [a, b], 'length_m': length}
        overlay[str(mesh)] = changed
        reports.append({'mesh': mesh, 'reviewed_rows': len(head | tail), 'actual_changed_rows': len(changed),
                        'canonical_weld_classes': len(classes), 'maximum_source_neighbor_weight_gradient': max_gradient})
    return overlay, reports

def apply_overlay(raw, overlay, recipe_raw, source_sha, role):
    need(sha(raw) == source_sha, 'exact declared export parent')
    doc, binary = read_glb(raw)
    result = bytearray(binary)
    for mesh, rows in overlay.items():
        streams = {s: stream(doc, binary, int(mesh), s) for s in ('JOINTS_0', 'WEIGHTS_0')}
        for row in rows:
            for semantic, key in [('JOINTS_0', 'joints'), ('WEIGHTS_0', 'weights')]:
                a = streams[semantic]
                struct.pack_into(a['format'], result, a['start'] + row['row'] * a['stride'], *row[key])
    child = copy.deepcopy(doc)
    child.setdefault('asset', {}).setdefault('extras', {})[NOTICE] = {
        'source_parent_sha256': source_sha, 'recipe_sha256': sha(recipe_raw),
        'binding_version': 2, 'role': role, 'qualification': 'UNRUN', 'old_certificate_transferred': False}
    out = write_glb(child, bytes(result))
    need(len(out) <= 4 * 1024 * 1024, 'unchanged four-MiB master cap')
    return out

def derive(parent_raw, reference_raw, recipe_raw):
    need(sha(reference_raw) == REFERENCE_SHA, 'immutable original925 reference source')
    overlay, reports = binding(parent_raw, recipe_raw)
    candidate = apply_overlay(parent_raw, overlay, recipe_raw, PARENT_SHA, 'natural-idle-candidate')
    reference = apply_overlay(reference_raw, overlay, recipe_raw, REFERENCE_SHA, 'paired-original925-geometry-reference')
    return candidate, reference, overlay, reports

def inspect(parent_raw, reference_raw, candidate_raw, paired_raw, recipe_raw):
    expected, paired, overlay, reports = derive(parent_raw, reference_raw, recipe_raw)
    need(candidate_raw == expected and paired_raw == paired, 'exact deterministic paired exports; no unlisted byte or metadata change')
    return {'status': 'STATIC_BINDING_SOURCE_EXPORT_ONLY_PASS_NOT_POSED_OR_VISUAL_ACCEPTANCE',
            'parent_sha256': PARENT_SHA, 'candidate_sha256': sha(candidate_raw), 'candidate_bytes': len(candidate_raw),
            'original925_sha256': REFERENCE_SHA, 'paired925_sha256': sha(paired_raw), 'paired925_bytes': len(paired_raw),
            'recipe_sha256': sha(recipe_raw), 'mesh_reports': reports,
            'old13_native_pose_parity': 'UNRUN', 'new17_physical129': 'UNRUN', 'paired925_socket129': 'UNRUN',
            'runtime_adoption': False, 'old_certificate_transferred': False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'reference', 'recipe', 'candidate_out', 'paired_out', 'report_out', 'overlay_out'):
        parser.add_argument('--' + name.replace('_', '-'), required=True, type=Path)
    args = parser.parse_args()
    for path in (args.candidate_out, args.paired_out, args.report_out, args.overlay_out):
        need(not path.exists(), 'fresh explicit output required')
    source, original, recipe = args.parent.read_bytes(), args.reference.read_bytes(), args.recipe.read_bytes()
    candidate, paired, overlay, _ = derive(source, original, recipe)
    report = inspect(source, original, candidate, paired, recipe)
    args.candidate_out.write_bytes(candidate)
    args.paired_out.write_bytes(paired)
    args.report_out.write_text(json.dumps(report, indent=2) + '\n')
    args.overlay_out.write_text(json.dumps(overlay, separators=(',', ':')) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
