# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in child of the exact V19 near/mid masters; never rewrites its input.

Ports the archived C02 real-aperture/alternating-knuckle mechanism to the
current source body. A fresh export is a STUDY, not a qualified installation.
The original producer, its contracts, parked placements and team stay intact.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np

from check_near import read, values
from check_mid import bind_parts


def digest(data):
    return hashlib.sha256(data).hexdigest()


def split_polygon(vertices, axis, bound, sign):
    """Partition a convex PN polygon without independently sorting its vertices."""
    inside, outside = [], []
    previous = vertices[-1]
    pd = sign * (previous[axis] - bound)
    for current in vertices:
        cd = sign * (current[axis] - bound)
        if (pd >= 0) != (cd >= 0):
            t = pd / (pd - cd)
            hit = previous + t * (current - previous)
            hit[axis] = bound
            inside.append(hit); outside.append(hit.copy())
        (inside if cd >= 0 else outside).append(current.copy())
        previous, pd = current, cd
    return inside, outside


def triangles(polygon):
    for i in range(1, len(polygon) - 1):
        tri = np.array([polygon[0], polygon[i], polygon[i + 1]], dtype=np.float64)
        if np.linalg.norm(np.cross(tri[1, :3] - tri[0, :3], tri[2, :3] - tri[0, :3])) > 1e-12:
            lengths = np.linalg.norm(tri[:, 3:], axis=1)
            if np.any(lengths < 1e-10):
                raise ValueError('Clipping produced an undefined normal')
            tri[:, 3:] /= lengths[:, None]
            yield tri


def partition(tri, aperture):
    """Disjoint outside fragments plus the inside polygon; winding is retained."""
    carry, outside = list(tri), []
    for axis, bound, sign in [(1, aperture['y_min'], 1), (1, aperture['y_max'], -1),
                              (2, aperture['z_min'], 1), (2, aperture['z_max'], -1)]:
        if not carry:
            break
        carry, rejected = split_polygon(carry, axis, bound, sign)
        outside.extend(triangles(rejected))
    return outside, list(triangles(carry))


def profile_planes(profile, offset):
    polygon = np.asarray(profile, dtype=float)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        edge = b - a; normal = np.array([-edge[1], edge[0]])
        normal /= np.linalg.norm(normal)
        yield normal, float(normal @ a - offset)


def partition_profile(tri, profile, offset):
    """Cut at the source-derived convex leaf support polygon in root Y/Z."""
    carry, outside = list(tri), []
    for normal, bound in profile_planes(profile, offset):
        if not carry:
            break
        inside, rejected = [], []; previous = carry[-1]
        pd = float(normal @ previous[1:3] - bound)
        for current in carry:
            cd = float(normal @ current[1:3] - bound)
            if (pd >= 0) != (cd >= 0):
                hit = previous + (pd / (pd - cd)) * (current - previous)
                inside.append(hit); rejected.append(hit.copy())
            (inside if cd >= 0 else rejected).append(current.copy())
            previous, pd = current, cd
        outside.extend(triangles(rejected)); carry = inside
    return outside, list(triangles(carry))


def profile_reveals(fixed, profile, offset):
    """Actual cut-skin joins at every profile plane, not a rectangular proxy."""
    planes = list(profile_planes(profile, offset))
    for normal, bound in planes:
        tangent = np.array([normal[1], -normal[0]])
        segments = []
        for tri in fixed:
            points = [v[:3].copy() for v in tri if abs(normal @ v[1:3] - bound) < 1e-8]
            if len(points) != 2:
                continue
            a, b = points; low, high = 0., 1.
            for other, limit in planes:
                d0, d1 = float(other @ a[1:3] - limit), float(other @ b[1:3] - limit)
                if d0 < -1e-8 and d1 < -1e-8:
                    low, high = 1., 0.; break
                if (d0 >= 0) != (d1 >= 0):
                    crossing = d0 / (d0 - d1)
                    if d0 < 0:
                        low = max(low, crossing)
                    else:
                        high = min(high, crossing)
            if high - low <= 1e-10:
                continue
            aa, bb = a + low * (b - a), a + high * (b - a)
            u, v = float(tangent @ aa[1:3]), float(tangent @ bb[1:3])
            if abs(u - v) < 1e-10:
                continue
            segments.append((u, aa, v, bb) if u < v else (v, bb, u, aa))
        stops = sorted(set(round(t, 10) for lo, a, hi, b in segments for t in [lo, hi]))
        for low, high in zip(stops, stops[1:]):
            if high - low <= 1e-10:
                continue
            middle = (low + high) / 2
            active = [(lo, a, hi, b) for lo, a, hi, b in segments if lo - 1e-9 <= middle <= hi + 1e-9]
            if len(active) < 2:
                continue
            def skins(value):
                xs = [a[0] + (b[0] - a[0]) * (value - lo) / (hi - lo) for lo, a, hi, b in active]
                return min(xs), max(xs)
            x0, x1 = skins(low); x2, x3 = skins(high)
            if max(x1 - x0, x3 - x2) < 1e-9:
                continue
            points = np.zeros((4, 3)); points[:, 0] = [x0, x1, x3, x2]
            points[:, 1:] = [normal * bound + tangent * u for u in [low, low, high, high]]
            n = np.array([0., *normal])
            if np.dot(np.cross(points[1] - points[0], points[2] - points[0]), n) < 0:
                points = points[::-1]
            for ids in [[0, 1, 2], [0, 2, 3]]:
                if np.linalg.norm(np.cross(points[ids[1]] - points[ids[0]], points[ids[2]] - points[ids[0]])) > 1e-12:
                    yield np.concatenate([points[ids], np.tile(n, (3, 1))], axis=1)


def shell_anchor(source_triangles, y, z):
    xs = []
    for tri in source_triangles:
        a, b, c = tri[:, :3]
        matrix = np.column_stack([b[1:] - a[1:], c[1:] - a[1:]])
        if abs(np.linalg.det(matrix)) < 1e-12:
            continue
        uv = np.linalg.solve(matrix, np.array([y, z]) - a[1:])
        if uv.min() >= -1e-8 and uv.sum() <= 1 + 1e-8:
            xs.append(float(a[0] + uv[0] * (b[0] - a[0]) + uv[1] * (c[0] - a[0])))
    if len(xs) < 2 or max(xs) - min(xs) < .001:
        raise ValueError('Fixed hinge anchor is not inside two actual source shell skins')
    return [float((min(xs) + max(xs)) / 2), float(y), float(z)]


def reroute_step(data, plan):
    result = data.copy(); y = result[:, :, 1]
    def smooth(low, high):
        t = np.clip((y - low) / (high - low), 0, 1)
        return t * t * (3 - 2 * t)
    weight = smooth(*plan['ramp_up_root_y_m']) * (1 - smooth(*plan['ramp_down_root_y_m']))
    result[:, :, 0] += plan['inboard_offset_m'] * weight
    for i, tri in enumerate(result):
        if np.array_equal(tri[:, :3], data[i, :, :3]):
            continue
        n = np.cross(tri[1, :3] - tri[0, :3], tri[2, :3] - tri[0, :3])
        length = np.linalg.norm(n)
        if length < 1e-12:
            raise ValueError('Step reroute collapsed a real source face')
        tri[:, 3:] = n / length
    return result


def ring(x, y, z, outer, inner, length, segments):
    """Vertical bored knuckle, true per-triangle normals, no intersecting boxes."""
    vertices = []
    for yy in [y - length / 2, y + length / 2]:
        for radius in [outer, inner]:
            vertices.extend([[x + radius * math.cos(a), yy, z + radius * math.sin(a)]
                             for a in np.linspace(0, 2 * math.pi, segments, endpoint=False)])
    for i in range(segments):
        j = (i + 1) % segments
        for face in [(i, j, 2 * segments + j, 2 * segments + i),
                     (segments + j, segments + i, 3 * segments + i, 3 * segments + j),
                     (j, i, segments + i, segments + j),
                     (2 * segments + i, 2 * segments + j, 3 * segments + j, 3 * segments + i)]:
            face = tuple(reversed(face))
            for indices in [(face[0], face[1], face[2]), (face[0], face[2], face[3])]:
                p = np.asarray([vertices[k] for k in indices], dtype=np.float64)
                n = np.cross(p[1] - p[0], p[2] - p[0]); n /= np.linalg.norm(n)
                yield np.concatenate([p, np.tile(n, (3, 1))], axis=1)


def arm(start, end, width):
    """Original rectangular hinge strap, each face wound away from its centre."""
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    along = end - start; along /= np.linalg.norm(along)
    v = np.cross(along, [0., 1., 0.]); v /= np.linalg.norm(v); v *= width / 2
    w = np.cross(along, v)
    points = np.array([p + a * v + b * w for p in [start, end]
                       for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]])
    centre = points.mean(axis=0)
    for face in [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
                 [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]:
        if np.dot(np.cross(points[face[1]] - points[face[0]], points[face[2]] - points[face[0]]),
                  points[face].mean(axis=0) - centre) < 0:
            face.reverse()
        for ids in [face[:3], [face[0], face[2], face[3]]]:
            p = points[ids]; n = np.cross(p[1] - p[0], p[2] - p[0]); n /= np.linalg.norm(n)
            yield np.concatenate([p, np.tile(n, (3, 1))], axis=1)


def reveals(fixed, aperture):
    """Cap actual inner/outer cut skins; sample their emitted boundary edges.

    This is not a guessed wall thickness. Each jamb strip joins the two actual
    source skin intersections, split at every source edge breakpoint.
    """
    for axis, other, key, inward in [(1, 2, 'y_min', 1), (1, 2, 'y_max', -1),
                                       (2, 1, 'z_min', 1), (2, 1, 'z_max', -1)]:
        bound = aperture[key]; segments = []
        for tri in fixed:
            edge = [v[:3] for v in tri if abs(v[axis] - bound) < 1e-8]
            if len(edge) != 2 or abs(edge[0][other] - edge[1][other]) < 1e-10:
                continue
            a, b = sorted(edge, key=lambda p: p[other])
            # Original exterior edges at this plane do not form a cut reveal.
            other_min = aperture['z_min' if other == 2 else 'y_min']
            other_max = aperture['z_max' if other == 2 else 'y_max']
            if a[other] < other_min - 1e-8 or b[other] > other_max + 1e-8:
                continue
            segments.append((a, b))
        stops = sorted(set(float(p[other]) for edge in segments for p in edge))
        for low, high in zip(stops, stops[1:]):
            middle = (low + high) / 2
            active = [(a, b) for a, b in segments if a[other] <= middle <= b[other]]
            if len(active) < 2:
                continue
            def skins(value):
                xs = [a[0] + (b[0] - a[0]) * (value - a[other]) / (b[other] - a[other])
                      for a, b in active]
                return min(xs), max(xs)
            x0, x1 = skins(low); x2, x3 = skins(high)
            if max(x1 - x0, x3 - x2) < 1e-9:
                continue
            p = np.zeros((4, 3)); p[:, axis] = bound
            p[:, other] = [low, low, high, high]; p[:, 0] = [x0, x1, x3, x2]
            normal = np.zeros(3); normal[axis] = inward
            if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), normal) < 0:
                p = p[::-1]
            for ids in [[0, 1, 2], [0, 2, 3]]:
                yield np.concatenate([p[ids], np.tile(normal, (3, 1))], axis=1)


def build(source, recipe_path, detail, destination):
    if destination.exists():
        raise ValueError('Fresh output directory required')
    recipe = json.loads(recipe_path.read_text())
    if recipe['boarding_enabled'] is not False or recipe['driver_passenger_fit'] is not False:
        raise ValueError('Door study must not enable boarding or occupant fit')
    if not 0 < recipe['hinge_strap_engagement_m'] < recipe['hinge_barrel_radius_m'] - recipe['hinge_bore_radius_m']:
        raise ValueError('Strap engagement must stay inside the outer barrel wall, outside its bore')
    contract_path = Path(__file__).with_name(recipe['base_contracts'][detail])
    contract = json.loads(contract_path.read_text())
    original = source.read_bytes()
    if digest(original) != contract['raw_sha256']:
        raise ValueError('Input is not the exact contracted raw V19 master')
    doc, binary = read(source)
    output = copy.deepcopy(doc)
    nodes = output['nodes']
    names = [n['name'] for n in nodes]
    frames = {n['name']: i for i, n in enumerate(nodes) if names.count(n['name']) == 1}
    # The input has translation-only frames. Reject future unnoticed rig changes.
    if any(any(k in n for k in ['rotation', 'scale', 'matrix']) for n in nodes):
        raise ValueError('Unexpected input frame transform')
    door = recipe['door_node']; pivot = np.asarray(recipe['hinge_root_m'], dtype=np.float64)
    frames[door] = len(nodes)
    nodes.append({'name': door, 'translation': pivot.tolist(), 'children': []})
    nodes[frames['vehicle_body']].setdefault('children', []).append(frames[door])
    source_bindings = bind_parts(doc, binary)
    batches, parts, protected, changed = {}, [], [], []

    def emit(name, frame, material, data, source_part_index=None, derived_source_part_index=None):
        data = np.asarray(data, dtype='<f4').reshape((-1, 3, 6))
        if not len(data):
            return
        # Hubcaps deliberately repeat names in the parent master. A string is
        # permitted only for unique new/body frames; originals use actual IDs.
        frame = frames[frame] if isinstance(frame, str) else frame
        key = (frame, material)
        chunks = batches.setdefault(key, [])
        start = sum(len(c) for c in chunks)
        chunks.append(data)
        parts.append({'name': name, 'frame': nodes[frame]['name'], 'frame_node_index': frame, 'material': material,
                      'triangle_start_in_batch': start, 'triangles': len(data),
                      **({'source_part_index': source_part_index} if source_part_index is not None else {}),
                      **({'derived_source_part_index': derived_source_part_index} if derived_source_part_index is not None else {})})

    moving_names = {'deep_U_closed_door', 'door_edge_lining', 'side_door_glass',
                    'side_window_frame', 'side_glass_division'}
    profile = recipe['aperture_profile_yz_m']
    cached = []
    for binding in source_bindings:
        positions = np.frombuffer(binding['chunks']['POSITION'], dtype='<f4').reshape((-1, 3)).astype(float)
        normals = np.frombuffer(binding['chunks']['NORMAL'], dtype='<f4').reshape((-1, 3)).astype(float)
        cached.append(np.concatenate([positions, normals], axis=1).reshape((-1, 3, 6)))
    right_shells = [i for i, part in enumerate(doc['extras']['parts']) if part['name'] == 'deep_curved_lower_body'
                    and cached[i][:, :, 0].max() < 0]
    assert len(right_shells) == 1
    source_shell = cached[right_shells[0]]
    hinges = []
    for i, part in enumerate(doc['extras']['parts']):
        xyz = cached[i][:, :, :3].reshape((-1, 3))
        if part['name'] == 'small_door_hardware' and xyz[:, 0].max() < 0 and xyz[:, 2].mean() < 0:
            hinges.append({'source_occurrence_id': i, 'centre_root_m': ((xyz.min(axis=0) + xyz.max(axis=0)) / 2).tolist()})
    assert len(hinges) == 2
    hinges.sort(key=lambda h: h['centre_root_m'][1])
    for part_index, part in enumerate(doc['extras']['parts']):
        binding = source_bindings[part_index]
        primitive, = doc['meshes'][binding['mesh_index']]['primitives']
        if set(primitive['attributes']) != {'POSITION', 'NORMAL'} or 'indices' in primitive:
            raise ValueError('Expected the raw original PN triangle master')
        parent = binding['node_path'][-2][0]
        assert nodes[parent]['name'] == part['frame']
        data = cached[part_index]
        p = data[:, :, :3].reshape((-1, 3))
        right = part['frame'] == 'vehicle_body' and float(p[:, 0].max()) < 0
        move = right and (part['name'] in moving_names or
                         part['name'] == 'small_door_hardware')
        if right and part['name'] == 'deep_curved_lower_body':
            outside, backing = [], []
            for tri in data:
                fixed, _ = partition_profile(tri, profile, recipe['fixed_running_relief_m'])
                _, leaf = partition_profile(tri, profile, -recipe['backing_relief_m'])
                outside.extend(fixed); backing.extend(leaf)
            if not backing:
                raise ValueError('No actual body surface removed: overlay-only door refused')
            emit(part['name'], parent, part['material'], outside, part_index)
            emit('door_fixed_aperture_reveal', parent, part['material'],
                 list(profile_reveals(outside, profile, recipe['fixed_running_relief_m'])),
                 derived_source_part_index=part_index)
            backing = np.asarray(backing); backing[:, :, :3] -= pivot
            emit('door_original_curved_backing', door, part['material'], backing, derived_source_part_index=part_index)
            changed.append({**part, 'source_part_index': part_index, 'source_node_path': binding['node_path'],
                            'operation': 'source-leaf-profile aperture; actual backing moves with declared running relief'})
        elif right and part['name'] in recipe['transfer_fixed_interfaces']:
            outside, transferred = [], []
            for tri in data:
                fixed, _ = partition_profile(tri, profile, recipe['fixed_running_relief_m'])
                _, leaf = partition_profile(tri, profile, 0)
                outside.extend(fixed); transferred.extend(leaf)
            if not transferred or not outside:
                raise ValueError('Interface must retain fixed roof/pillar remainder and transfer actual leaf overlap')
            emit(part['name'], parent, part['material'], outside, part_index)
            transferred = np.asarray(transferred); transferred[:, :, :3] -= pivot
            emit('door_transferred_' + part['name'], door, part['material'], transferred,
                 derived_source_part_index=part_index)
            changed.append({**part, 'source_part_index': part_index, 'source_node_path': binding['node_path'],
                            'operation': 'hidden fixed-interface rebate; original inside fragment transfers at same closed-world surface'})
        elif right and part['name'] == 'step_support':
            emit(part['name'], parent, part['material'], reroute_step(data, recipe['step_stem_repair']), part_index)
            changed.append({**part, 'source_part_index': part_index, 'source_node_path': binding['node_path'],
                            'operation': 'right hidden stem middle rerouted inboard; both terminal attachments retained'})
        elif move:
            shifted = data.copy(); shifted[:, :, :3] -= pivot
            emit(part['name'], door, part['material'], shifted, part_index)
            changed.append({**part, 'source_part_index': part_index, 'source_node_path': binding['node_path'],
                            'operation': 'rigid leaf; closed world positions retained'})
        else:
            emit(part['name'], parent, part['material'], data, part_index)
            protected.append({**part, 'source_part_index': part_index, 'source_node_path': binding['node_path'],
                              'expanded_PN_sha256': digest(np.asarray(data, dtype='<f4').tobytes())})
    if not changed or not any(p['name'] == 'side_door_glass' for p in parts if p['frame'] == door):
        raise ValueError('Incomplete door assembly')
    # Port the proven C02 separate pin/alternating knuckle construction, retaining
    # its honest reconstruction status. Current whole-surface checks are REQUIRED.
    for hinge in hinges:
        endpoint = np.asarray(hinge['centre_root_m'])
        y = float(endpoint[1]); fixed_endpoints = []
        for dy in recipe['hinge_fixed_offsets_m']:
            emit('door_fixed_knuckle', 'vehicle_body', 3,
                 list(ring(pivot[0], y + dy, pivot[2], recipe['hinge_barrel_radius_m'],
                           recipe['hinge_bore_radius_m'], recipe['hinge_knuckle_length_m'], recipe['hinge_segments'])))
            anchor = np.asarray(shell_anchor(source_shell, y + dy, recipe['fixed_anchor_z_m']))
            direction = anchor - np.array([pivot[0], y + dy, pivot[2]])
            direction /= np.linalg.norm(direction)
            start = np.array([pivot[0], y + dy, pivot[2]]) + direction * (
                recipe['hinge_barrel_radius_m'] - recipe['hinge_strap_engagement_m'])
            emit('door_fixed_hinge_strap', 'vehicle_body', 3, list(arm(start, anchor, .008)))
            fixed_endpoints.append(anchor.tolist())
        emit('door_pin_tube', 'vehicle_body', 3,
             list(ring(pivot[0], y, pivot[2], recipe['hinge_pin_radius_m'], .001,
                       recipe['hinge_pin_length_m'], recipe['hinge_segments'])))
        emit('door_moving_knuckle', door, 3,
             list(ring(0, y, 0, recipe['hinge_barrel_radius_m'], recipe['hinge_bore_radius_m'],
                       recipe['hinge_knuckle_length_m'], recipe['hinge_segments'])))
        local_end = endpoint - pivot
        direction = np.array([local_end[0], 0., local_end[2]]); direction /= np.linalg.norm(direction)
        local_start = np.array([0., y, 0.]) + direction * (
            recipe['hinge_barrel_radius_m'] - recipe['hinge_strap_engagement_m'])
        emit('door_moving_hinge_strap', door, 3, list(arm(local_start, local_end, .008)))
        hinge['fixed_shell_anchor_endpoints_root_m'] = fixed_endpoints
        hinge['moving_strap_start_local_m'] = local_start.tolist()
        hinge['moving_strap_end_local_m'] = local_end.tolist()
    # Rebuild streams only; preserve original materials, semantic frames and every
    # unrelated part. Orphan old mesh nodes are removed from their parents.
    mesh_nodes = {i for i, n in enumerate(nodes) if 'mesh' in n}
    for n in nodes:
        n['children'] = [i for i in n.get('children', []) if i not in mesh_nodes]
        n.pop('mesh', None)
    blob = bytearray(); output['bufferViews'] = []; output['accessors'] = []; output['meshes'] = []

    def accessor(data):
        data = np.asarray(data, dtype='<f4').reshape((-1, 3)); offset = len(blob); blob.extend(data.tobytes())
        vi = len(output['bufferViews']); ai = len(output['accessors'])
        output['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': data.nbytes, 'target': 34962})
        output['accessors'].append({'bufferView': vi, 'componentType': 5126, 'count': len(data), 'type': 'VEC3',
                                    'min': data.min(axis=0).tolist(), 'max': data.max(axis=0).tolist()})
        return ai

    for (parent, material), chunks in batches.items():
        data = np.concatenate(chunks).reshape((-1, 6)); mi = len(output['meshes'])
        name = f"surface_{nodes[parent]['name']}_{material}"
        output['meshes'].append({'name': name, 'primitives': [{'attributes': {
            'POSITION': accessor(data[:, :3]), 'NORMAL': accessor(data[:, 3:])}, 'material': material}]})
        ni = len(nodes); nodes.append({'name': name, 'mesh': mi})
        nodes[parent].setdefault('children', []).append(ni)
    reachable = set()
    def visit(index):
        if index in reachable:
            raise ValueError('Repeated node in input/output tree')
        reachable.add(index)
        for child in nodes[index].get('children', []):
            visit(child)
    for scene in output['scenes']:
        for index in scene['nodes']:
            visit(index)
    remap = {old: new for new, old in enumerate(sorted(reachable))}
    output['nodes'] = [nodes[index] for index in sorted(reachable)]
    for n in output['nodes']:
        if n.get('children'):
            n['children'] = [remap[c] for c in n['children']]
        else:
            n.pop('children', None)
    for scene in output['scenes']:
        scene['nodes'] = [remap[index] for index in scene['nodes']]
    for part in parts:
        part['frame_node_index'] = remap[part['frame_node_index']]
    output['buffers'] = [{'byteLength': len(blob)}]
    output['extras']['parts'] = parts
    output['extras']['statistics'] = {'triangles': sum(p['triangles'] for p in parts),
                                      'meshes': len(output['meshes']), 'nodes': len(output['nodes'])}
    output['extras']['door_foundation'] = {**recipe, 'input_sha256': digest(original),
        'recipe_sha256': digest(recipe_path.read_bytes()), 'study_only': True}
    # Deliberately preserve original disabled flags. Installation requires fresh
    # actual geometry, near/mid visual and runtime checks, never this recipe alone.
    output['extras']['door_interaction_enabled'] = False
    output['extras']['boarding_enabled'] = False
    payload = json.dumps(output, separators=(',', ':'), allow_nan=False).encode()
    payload += b' ' * (-len(payload) % 4); blob += b'\0' * (-len(blob) % 4)
    raw = (struct.pack('<III', 0x46546c67, 2, 28 + len(payload) + len(blob)) +
           struct.pack('<II', len(payload), 0x4e4f534a) + payload + struct.pack('<II', len(blob), 0x004e4942) + blob)
    destination.mkdir(parents=True)
    (destination / 'brougham-door-study.glb').write_bytes(raw)
    report = {'schema': 'chicago-brougham-door-source-receipt-v1', 'detail': detail,
              'input_sha256': digest(original), 'output_sha256': digest(raw), 'bytes': len(raw),
              'recipe_sha256': digest(recipe_path.read_bytes()), 'producer_sha256': digest(Path(__file__).read_bytes()),
              'actual_hinge_attachments': hinges,
              'protected_parts': protected, 'changed_parts': changed, 'qualification': recipe['qualification'],
              'boarding_enabled': False, 'driver_passenger_fit': False}
    (destination / 'DOOR-SOURCE-RECEIPT.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input', type=Path, required=True)
    cli.add_argument('--recipe', type=Path, default=Path(__file__).with_name('door-aperture.json'))
    cli.add_argument('--detail', choices=['near', 'mid'], required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    result = build(args.input, args.recipe, args.detail, args.output)
    print(json.dumps({k: result[k] for k in ['detail', 'input_sha256', 'output_sha256', 'bytes', 'qualification']}))
