#!/usr/bin/env python3
"""Unadopted eye NORMAL-only study. Standard-library, deterministic, no installer."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

PARENT_SHA = 'e49b6f1c9f7b70f1fcdf19fa7f6dddf54048b32256b4d8030d6238d6dfe79d49'
PARENT_BYTES = 4159196
NORMAL_ACCESSOR = 208

def need(ok, message):
    if not ok:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def decode(raw):
    need(len(raw) >= 28 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'GLB header')
    count, kind = struct.unpack_from('<II', raw, 12)
    need(kind == 0x4e4f534a, 'JSON chunk')
    size, kind = struct.unpack_from('<II', raw, 20 + count)
    need(kind == 0x004e4942 and len(raw) == 28 + count + size, 'single embedded BIN chunk')
    return json.loads(raw[20:20 + count]), raw[28 + count:]

def encode(doc, binary):
    text = json.dumps(doc, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    text += b' ' * (-len(text) % 4)
    return struct.pack('<4sII', b'glTF', 2, 28 + len(text) + len(binary)) + struct.pack('<II', len(text), 0x4e4f534a) + text + struct.pack('<II', len(binary), 0x004e4942) + binary

def layout(doc, index):
    a = doc['accessors'][index]
    need(not a.get('sparse') and not a.get('normalized'), 'dense unnormalized accessor required')
    v = doc['bufferViews'][a['bufferView']]
    need(v.get('buffer', 0) == 0, 'embedded buffer only')
    components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    widths = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    width = widths[a['componentType']] * components
    stride = v.get('byteStride', width)
    start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    need(stride >= width and a.get('byteOffset', 0) + (a['count'] - 1) * stride + width <= v['byteLength'], 'accessor bounds/stride')
    return a, start, stride, width

def vectors(doc, binary, index):
    a, start, stride, width = layout(doc, index)
    need(a['componentType'] == 5126 and a['type'] == 'VEC3' and width == 12, 'float VEC3 required')
    return [struct.unpack_from('<3f', binary, start + i * stride) for i in range(a['count'])]

def unit(v):
    length = math.sqrt(math.fsum(x * x for x in v))
    need(length > 1e-15 and math.isfinite(length), 'nonzero finite direction')
    return tuple(x / length for x in v)

def sphere_fit(points):
    """Centered algebraic least squares, deterministic 4x4 pivoted elimination."""
    points = sorted(set(points))
    mean = tuple(math.fsum(p[k] for p in points) / len(points) for k in range(3))
    rows = [(tuple(2 * (p[k] - mean[k]) for k in range(3)) + (1.,), math.fsum((p[k] - mean[k]) ** 2 for k in range(3))) for p in points]
    m = [[math.fsum(a[i] * a[j] for a, _ in rows) for j in range(4)] + [math.fsum(a[i] * b for a, b in rows)] for i in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]
        need(abs(m[col][col]) > 1e-15, 'sphere fit singular')
        scale = m[col][col]
        m[col] = [v / scale for v in m[col]]
        for row in range(4):
            if row == col:
                continue
            scale = m[row][col]
            m[row] = [a - scale * b for a, b in zip(m[row], m[col])]
    center = tuple(mean[k] + m[k][4] for k in range(3))
    radii = [math.dist(p, center) for p in points]
    return {'center_m': list(center), 'unique_positions': len(points), 'radius_min_m': min(radii), 'radius_max_m': max(radii), 'radius_mean_m': math.fsum(radii) / len(radii)}

def source_layout(doc, binary):
    need(len(doc['meshes']) == 3 and len(doc['meshes'][2]['primitives']) == 1, 'exact three-mesh source layout')
    primitive = doc['meshes'][2]['primitives'][0]
    need(primitive['attributes']['NORMAL'] == NORMAL_ACCESSOR and primitive['attributes']['POSITION'] == 207 and 'TANGENT' not in primitive['attributes'], 'exact eye-only target')
    refs = [(mi, pi, name) for mi, m in enumerate(doc['meshes']) for pi, p in enumerate(m['primitives']) for name, ai in p.get('attributes', {}).items() if ai == NORMAL_ACCESSOR]
    need(refs == [(2, 0, 'NORMAL')], 'shared NORMAL accessor refused')
    a, start, stride, width = layout(doc, NORMAL_ACCESSOR)
    need(a['count'] == 3968 and width == 12, 'exact eye row count')
    allowed = set()
    for row in range(a['count']):
        allowed.update(range(start + row * stride, start + row * stride + width))
    # Check other accessors and opaque payload views, including animation/bind data.
    for index in range(len(doc['accessors'])):
        if index == NORMAL_ACCESSOR:
            continue
        other, at, step, size = layout(doc, index)
        for row in range(other['count']):
            need(not any(i in allowed for i in range(at + row * step, at + row * step + size)), 'NORMAL aliases another accessor')
    for index, view in enumerate(doc['bufferViews']):
        if index == a['bufferView']:
            continue
        at = view.get('byteOffset', 0)
        need(not any(i in allowed for i in range(at, at + view['byteLength'])), 'NORMAL overlaps another bufferView')
    need(max(allowed) < len(binary), 'NORMAL outside BIN')
    return allowed, start, stride

def derive(parent, recipe):
    need(len(parent) == PARENT_BYTES and digest(parent) == PARENT_SHA, 'exact e49 parent required')
    need(recipe['state'] == 'UNADOPTED_UNQUALIFIED_SOURCE_STUDY' and recipe['parent_sha256'] == PARENT_SHA and recipe['normal_accessor'] == NORMAL_ACCESSOR, 'recipe scope')
    doc, binary = decode(parent)
    allowed, start, stride = source_layout(doc, binary)
    pos = vectors(doc, binary, 207)
    groups = {'negative_x': [p for p in pos if p[0] < 0], 'positive_x': [p for p in pos if p[0] > 0]}
    need(sum(map(len, groups.values())) == len(pos), 'unambiguous two-eye side partition')
    for side, points in groups.items():
        fit = sphere_fit(points)
        expected = recipe['eyes'][side]
        need(len(set(points)) == 482 and fit['unique_positions'] == expected['unique_positions'], 'source sphere vertex set')
        need(math.dist(fit['center_m'], expected['center_m']) <= 1e-12, 'recipe center differs from actual fit')
        need(fit['radius_max_m'] - fit['radius_min_m'] <= 4e-6 and .0348 < fit['radius_mean_m'] < .0349, 'actual near-sphere limits')
    edited = bytearray(binary)
    new = []
    for row, p in enumerate(pos):
        center = recipe['eyes']['negative_x' if p[0] < 0 else 'positive_x']['center_m']
        normal = unit(tuple(p[k] - center[k] for k in range(3)))
        raw = struct.pack('<3f', *normal)
        edited[start + row * stride:start + row * stride + 12] = raw
        new.append(struct.unpack('<3f', raw))
    child_doc = copy.deepcopy(doc)
    for key, func in [('min', min), ('max', max)]:
        if key in child_doc['accessors'][NORMAL_ACCESSOR]:
            child_doc['accessors'][NORMAL_ACCESSOR][key] = [func(p[k] for p in new) for k in range(3)]
    return encode(child_doc, bytes(edited))

def inspect(parent, child, recipe):
    """Independent protected-byte/schema and radial/unit invariants, no render claim."""
    pd, pb = decode(parent)
    cd, cb = decode(child)
    allowed, start, stride = source_layout(pd, pb)
    need(len(pb) == len(cb), 'BIN length preserved')
    changed = [i for i, (a, b) in enumerate(zip(pb, cb)) if a != b]
    need(changed and all(i in allowed for i in changed), 'only eye NORMAL bytes may change')
    clean = copy.deepcopy(cd)
    for key in ['min', 'max']:
        if key in pd['accessors'][NORMAL_ACCESSOR]:
            clean['accessors'][NORMAL_ACCESSOR][key] = pd['accessors'][NORMAL_ACCESSOR][key]
    need(clean == pd, 'JSON only truthful eye NORMAL extrema may change')
    pos = vectors(cd, cb, 207)
    old, new = vectors(pd, pb, NORMAL_ACCESSOR), vectors(cd, cb, NORMAL_ACCESSOR)
    lengths = [math.sqrt(math.fsum(x*x for x in normal)) for normal in new]
    radial = []
    for p, normal in zip(pos, new):
        center = recipe['eyes']['negative_x' if p[0] < 0 else 'positive_x']['center_m']
        direction = unit(tuple(p[k] - center[k] for k in range(3)))
        radial.append(math.fsum(a*b for a,b in zip(normal,direction)))
    need(max(abs(length-1) for length in lengths) < 1e-7 and min(radial) > .9999999, 'unit outward analytic eye normals')
    for key, func in [('min', min), ('max', max)]:
        if key in cd['accessors'][NORMAL_ACCESSOR]:
            need(cd['accessors'][NORMAL_ACCESSOR][key] == [func(p[k] for p in new) for k in range(3)], 'truthful NORMAL extrema')
    angles = [math.degrees(math.acos(max(-1., min(1., math.fsum(a*b for a,b in zip(o,n)))))) for o,n in zip(old,new)]
    ranges=[]
    for i in changed:
        if ranges and i == ranges[-1][1]:
            ranges[-1][1] += 1
        else:
            ranges.append([i, i+1])
    protected = bytes(v for i,v in enumerate(pb) if i not in allowed)
    protected_child = bytes(v for i,v in enumerate(cb) if i not in allowed)
    need(protected == protected_child, 'every protected BIN byte exact')
    return {'state':'PASS_SOURCE_INVARIANTS_ONLY_UNADOPTED_UNQUALIFIED','parent_sha256':digest(parent),'candidate_sha256':digest(child),'parent_bytes':len(parent),'candidate_bytes':len(child),'normal_accessor':NORMAL_ACCESSOR,'normal_rows':len(new),'rows_changed':sum(a!=b for a,b in zip(old,new)),'allowed_BIN_normal_ranges':[[start+i*stride,start+i*stride+12]for i in range(len(new))],'actual_changed_BIN_ranges':ranges,'actual_changed_BIN_bytes':len(changed),'protected_BIN_bytes':len(protected),'protected_BIN_sha256':digest(protected),'normal_length_min':min(lengths),'normal_length_max':max(lengths),'outward_radial_dot_min':min(radial),'max_old_new_normal_degrees':max(angles),'json_changes_only':['accessors[208].min','accessors[208].max'],'preserved':'All positions/indices/UV/weights/joints/binds/nodes/skins/animations/images/materials and other mesh normals; every BIN byte outside eye NORMAL storage exact','NOT_QUALIFIED':['native capture','current published gate','physical129 rerun','posed129 rerun','photo match','BODY ring thinning','cheek retopology','hair improvement']}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--recipe',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--proof',type=Path,required=True)
    args=parser.parse_args()
    need(not args.out.exists() and not args.proof.exists(), 'fresh candidate and proof paths required')
    parent=args.parent.read_bytes();recipe=json.loads(args.recipe.read_text())
    child=derive(parent,recipe);proof=inspect(parent,child,recipe)
    args.out.write_bytes(child);args.proof.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:proof[k]for k in ['state','candidate_sha256','candidate_bytes','rows_changed','actual_changed_BIN_bytes','max_old_new_normal_degrees']}))
