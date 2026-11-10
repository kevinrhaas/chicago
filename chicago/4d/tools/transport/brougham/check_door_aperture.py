# SPDX-License-Identifier: GPL-3.0-or-later
"""Read actual exported triangles, not constructor bounds or a door-only proxy.

Ports the archived C02 whole-surface SAT test. Adds conservative angular-interval
separation: every moving/fixed triangle pair must have a real separating axis
whose gap exceeds the maximum rigid displacement on that interval. Subdivision
that cannot establish separation is NONPASS, never a sampled-sweep approval.
No occupied fit, solid containment or force/strength claim follows.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import time

import numpy as np

from check_near import read, values, component, world_nodes
from check_mid import bind_parts
from sampled_sat import separation_batch, BATCH_CAP
from sampled_broadphase import FixedYBroadphase

CLOSED_WORLD_POSITION_TOLERANCE_M = 2e-7
CUT_SURFACE_AREA_TOLERANCE_M2 = 2e-6


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def axes(a, b):
    ea = np.roll(a, -1, axis=0) - a; eb = np.roll(b, -1, axis=0) - b
    na = np.cross(ea[0], ea[1]); nb = np.cross(eb[0], eb[1])
    # Coplanar in-plane axes are essential: the original study used these too.
    for axis in [na, nb] + [np.cross(x, y) for x in ea for y in eb] + [
            np.cross(na, x) for x in ea] + [np.cross(nb, x) for x in eb]:
        length = np.linalg.norm(axis)
        if length > 1e-14:
            yield axis / length


def separation(a, b):
    return max(max(float((a @ axis).min() - (b @ axis).max()),
                   float((b @ axis).min() - (a @ axis).max())) for axis in axes(a, b))


def turn(tri, angle):
    c, s = math.cos(angle), math.sin(angle)
    return tri @ np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def sampled_pair_batches(posed, fixed, candidates, tolerance):
    """Only the sampled inner loop; native fixed-index order is unchanged."""
    for start in range(0, len(candidates), BATCH_CAP):
        indices = candidates[start:start + BATCH_CAP]
        gaps, diagnostics = separation_batch(
            np.broadcast_to(posed, (len(indices), 3, 3)), fixed[indices],
            scalar=separation, decision_thresholds=tolerance)
        yield indices, gaps, diagnostics


def interval_clear(moving, fixed, start, end, depth, tolerance):
    middle = (start + end) / 2
    radius = float(np.hypot(moving[:, 0], moving[:, 2]).max())
    displacement = 2 * radius * math.sin(abs(end - start) / 4)
    sample = turn(moving, middle)
    gap = separation(sample, fixed)
    if gap > displacement + tolerance:
        return True, 0
    if gap <= tolerance:
        return False, 1  # Actual intersection/contact at the midpoint.
    if depth <= 0:
        return False, 0  # Unresolved interval is not a PASS.
    left, hits = interval_clear(moving, fixed, start, middle, depth - 1, tolerance)
    if not left:
        return False, hits
    return interval_clear(moving, fixed, middle, end, depth - 1, tolerance)


def decode(doc, binary):
    parents = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
    world = world_nodes(doc)
    by_mesh = {n['mesh']: i for i, n in enumerate(doc['nodes']) if 'mesh' in n}
    triangles, moving, labels = [], [], []
    for mi, mesh in enumerate(doc['meshes']):
        ni = by_mesh[mi]
        p = ni; is_moving = False
        while True:
            if doc['nodes'][p]['name'] == 'vehicle_door_right':
                is_moving = True
            if p not in parents:
                break
            p = parents[p]
        for primitive in mesh['primitives']:
            xyz = np.asarray(values(doc, binary, primitive['attributes']['POSITION']))
            if 'indices' in primitive:
                xyz = xyz[np.array(values(doc, binary, primitive['indices'])).reshape(-1)]
            xyz += np.asarray(world[ni]); xyz = xyz.reshape((-1, 3, 3))
            triangles.extend(xyz); moving.extend([is_moving] * len(xyz)); labels.extend([mesh['name']] * len(xyz))
    return np.asarray(triangles), np.asarray(moving), labels


def clipped_area(triangle, bounds):
    """Independent actual-surface obstruction test in the aperture's core."""
    polygon = list(triangle)
    for axis, (low, high) in enumerate(bounds):
        for bound, sign in [(low, 1), (high, -1)]:
            if not polygon:
                return 0.
            result = []; previous = polygon[-1]; pd = sign * (previous[axis] - bound)
            for current in polygon:
                cd = sign * (current[axis] - bound)
                if (pd >= 0) != (cd >= 0):
                    result.append(previous + pd / (pd - cd) * (current - previous))
                if cd >= 0:
                    result.append(current)
                previous, pd = current, cd
            polygon = result
    return sum(np.linalg.norm(np.cross(polygon[i] - polygon[0], polygon[i + 1] - polygon[0])) / 2
               for i in range(1, len(polygon) - 1))


def clipped_axis_vertices(triangles, limits):
    vertices = []
    for triangle in triangles:
        polygon = list(triangle)
        for axis, low, high in limits:
            for bound, sign in [(low, 1), (high, -1)]:
                if not polygon:
                    break
                output = []; previous = polygon[-1]; pd = sign * (previous[axis] - bound)
                for current in polygon:
                    cd = sign * (current[axis] - bound)
                    if (pd >= 0) != (cd >= 0):
                        output.append(previous + pd / (pd - cd) * (current - previous))
                    if cd >= 0:
                        output.append(current)
                    previous, pd = current, cd
                polygon = output
            if not polygon:
                break
        vertices.extend(polygon)
    return np.asarray(vertices).reshape((-1, 3))


def profile_area(triangles, profile, offset, min_y=None):
    total = 0.
    for triangle in triangles:
        polygon = list(triangle)
        for a, b in zip(profile, np.roll(profile, -1, axis=0)):
            edge = b - a; n = np.array([-edge[1], edge[0]]); n /= np.linalg.norm(n)
            bound = float(n @ a - offset)
            if not polygon:
                break
            result = []; previous = polygon[-1]; pd = float(n @ previous[1:] - bound)
            for current in polygon:
                cd = float(n @ current[1:] - bound)
                if (pd >= 0) != (cd >= 0):
                    result.append(previous + (pd / (pd - cd)) * (current - previous))
                if cd >= 0:
                    result.append(current)
                previous, pd = current, cd
            polygon = result
        if min_y is not None and polygon:
            result = []; previous = polygon[-1]; pd = previous[1] - min_y
            for current in polygon:
                cd = current[1] - min_y
                if (pd >= 0) != (cd >= 0):
                    result.append(previous + pd / (pd - cd) * (current - previous))
                if cd >= 0:
                    result.append(current)
                previous, pd = current, cd
            polygon = result
        total += sum(np.linalg.norm(np.cross(polygon[i] - polygon[0], polygon[i + 1] - polygon[0])) / 2
                     for i in range(1, len(polygon) - 1))
    return float(total)


def original_surface_error(points, normals, original_triangles, original_normals):
    """Each transferred PN vertex must lie on an actual original source facet."""
    a = original_triangles[:, 0]; e0 = original_triangles[:, 1] - a; e1 = original_triangles[:, 2] - a
    d00 = np.einsum('ij,ij->i', e0, e0); d01 = np.einsum('ij,ij->i', e0, e1); d11 = np.einsum('ij,ij->i', e1, e1)
    denominator = d00 * d11 - d01 * d01
    assert np.all(denominator > 0)
    slack = CLOSED_WORLD_POSITION_TOLERANCE_M / np.maximum(np.minimum(np.sqrt(d00), np.sqrt(d11)), 1e-9)
    worst = 0.
    for point, normal in zip(points, normals):
        v = point - a; d20 = np.einsum('ij,ij->i', v, e0); d21 = np.einsum('ij,ij->i', v, e1)
        u = (d11 * d20 - d01 * d21) / denominator; w = (d00 * d21 - d01 * d20) / denominator
        closest = a + u[:, None] * e0 + w[:, None] * e1
        distance = np.linalg.norm(closest - point, axis=1)
        interpolated = ((1 - u - w)[:, None] * original_normals[:, 0]
                        + u[:, None] * original_normals[:, 1] + w[:, None] * original_normals[:, 2])
        interpolated /= np.linalg.norm(interpolated, axis=1)[:, None]
        possible = ((u >= -slack) & (w >= -slack) & (u + w <= 1 + slack)
                    & (np.abs(interpolated - normal).max(axis=1) <= 2e-7))
        assert possible.any(), 'Transferred header/pillar normal is not from an original facet'
        best = float(distance[possible].min())
        assert best <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Transferred header/pillar closed-WORLD surface changed'
        worst = max(worst, best)
    return worst


def verify_structure(args):
    """The same actual-geometry prefix used by structure-only AND full checks.

    Returns decoded geometry for the later sweep, but never runs or qualifies it.
    Receipts identify inputs; original part classification, ancestry and actual
    closed geometry are checked independently of the receipt's changed labels.
    """
    recipe = json.loads(args.recipe.read_text())
    original, source_bin = read(args.input); doc, binary = read(args.candidate)
    receipt = json.loads(args.source_receipt.read_text())
    assert receipt['input_sha256'] == sha(args.input)
    assert receipt['output_sha256'] == sha(args.candidate)
    assert receipt['recipe_sha256'] == sha(args.recipe)
    assert receipt['detail'] in ['near', 'mid']
    contract = json.loads(Path(__file__).with_name(recipe['base_contracts'][receipt['detail']]).read_text())
    assert contract['raw_sha256'] == sha(args.input), 'Not the exact V19 parent master'
    assert doc['materials'] == original['materials'], 'Original finishes changed'
    assert doc['extras']['boarding_enabled'] is False
    assert doc['extras']['door_interaction_enabled'] is False
    assert doc['extras']['door_foundation']['driver_passenger_fit'] is False
    # Compare the actual input and output streams, independently of the emitted
    # source-receipt claims. Every original occurrence is accounted for once.
    source_parts = original['extras']['parts']; output_parts = doc['extras']['parts']
    protected = receipt['protected_parts']; changed = receipt['changed_parts']
    assert len(source_parts) == len(protected) + len(changed)
    # Use the repository's established source-order + complete-range binder.
    # Four real hubcap frames/meshes intentionally share their names. A name is
    # not identity; each actual mesh must be exhausted exactly once.
    source_bindings = bind_parts(original, source_bin)
    target_bindings = bind_parts(doc, binary)
    source_index_for_part = {id(p): i for i, p in enumerate(source_parts)}
    target_index_for_part = {id(p): i for i, p in enumerate(output_parts)}

    def geometry(part, source, world):
        binding = (source_bindings[source_index_for_part[id(part)]] if source else
                   target_bindings[target_index_for_part[id(part)]])
        node_index = binding['node_path'][-1][0]
        assert node_index in world, 'Part mesh is not reachable'
        local = np.frombuffer(binding['chunks']['POSITION'], dtype='<f4').reshape((-1, 3)).astype(float)
        return local + np.asarray(world[node_index]), binding['chunks']['NORMAL'], node_index, binding

    source_world, target_world = world_nodes(original), world_nodes(doc)
    parents = {child: i for i, node in enumerate(doc['nodes']) for child in node.get('children', [])}
    doors = [i for i, node in enumerate(doc['nodes']) if node['name'] == 'vehicle_door_right']
    assert len(doors) == 1, 'Required independent door root missing or ambiguous'
    door, = doors
    assert doc['nodes'][parents[door]]['name'] == 'vehicle_body', 'Door is not hung to the current body'
    assert np.array_equal(np.asarray(target_world[door]), np.asarray(recipe['hinge_root_m'])), 'Hinge rest frame changed'

    def under_door(node_index):
        while True:
            if node_index == door:
                return True
            if node_index not in parents:
                return False
            node_index = parents[node_index]

    move_names = {'deep_U_closed_door', 'door_edge_lining', 'side_door_glass',
                  'side_window_frame', 'side_glass_division'}
    moved_rows, cut_rows, step_rows = [], [], []
    expected_moved, expected_cut, expected_protected = set(), set(), set()
    expected_interfaces, expected_steps = set(), set()
    assert set(recipe['transfer_fixed_interfaces']) == {'closed_upper_side_header', 'rear_window_pillar'}
    expected_protected_rows, expected_changed_rows, protected_world_rows = [], [], []
    for source_index, part in enumerate(source_parts):
        positions, normal_bytes, source_node, source_binding = geometry(part, True, source_world)
        right = part['frame'] == 'vehicle_body' and positions[:, 0].max() < 0
        required_move = right and (part['name'] in move_names or part['name'] == 'small_door_hardware')
        required_cut = right and part['name'] == 'deep_curved_lower_body'
        required_interface = right and part['name'] in recipe['transfer_fixed_interfaces']
        required_step = right and part['name'] == 'step_support'
        targets = [p for p in output_parts if p.get('source_part_index') == source_index]
        assert len(targets) == 1, ('Original part lost/duplicated', source_index, part['name'])
        target, = targets
        actual, actual_normals, target_node, target_binding = geometry(target, False, target_world)
        if required_move:
            expected_moved.add(source_index)
            expected_changed_rows.append((source_index, part))
            assert target['frame'] == 'vehicle_door_right' and under_door(target_node), (
                'Required leaf part is not under vehicle_door_right', part['name'])
            assert all(target[k] == part[k] for k in ['name', 'material', 'triangles']), 'Retained leaf inventory changed'
            assert actual_normals == normal_bytes, ('Retained leaf NORMAL changed', part['name'])
            error = float(np.abs(actual - positions).max())
            assert error <= CLOSED_WORLD_POSITION_TOLERANCE_M, ('Retained leaf closed-WORLD POSITION changed', part['name'], error)
            moved_rows.append({'source_part_index': source_index, 'name': part['name'],
                               'closed_world_position_max_error_m': error, 'normals_exact': True,
                               'actual_required_door_ancestry': True})
        elif required_cut or required_interface:
            (expected_cut if required_cut else expected_interfaces).add(source_index)
            expected_changed_rows.append((source_index, part))
            assert target['frame'] == part['frame'] and not under_door(target_node), 'Cut wall must remain fixed'
            cut_rows.append((part, positions.reshape((-1, 3, 3)), actual.reshape((-1, 3, 3)),
                             required_cut, normal_bytes))
        elif required_step:
            expected_steps.add(source_index); expected_changed_rows.append((source_index, part))
            assert target['frame'] == part['frame'] and not under_door(target_node), 'Fixed step stem moved with leaf'
            plan = recipe['step_stem_repair']; y = positions[:, 1]
            terminal = (y <= plan['ramp_up_root_y_m'][0]) | (y >= plan['ramp_down_root_y_m'][1])
            assert np.array_equal(actual[terminal], positions[terminal]), 'Original step terminal attachment moved'
            assert np.array_equal(actual[:, 1:], positions[:, 1:]), 'Source ring Y/Z coordinates changed'
            assert len(positions) == 444
            # Independent extraction: use the source upper cap then the NEXT
            # corner at the end of each actual side quad, not producer ring starts.
            rings = [np.unique(positions[:6], axis=0)] + [np.array([
                positions[12 + 24 * i + 6 * j + 5] for j in range(4)]) for i in range(18)]
            actual_for_source = {}
            for original_point, actual_point in zip(positions, actual):
                key = tuple(original_point)
                if key in actual_for_source:
                    assert np.array_equal(actual_for_source[key], actual_point), 'Expanded source ring vertex occurrences separated'
                actual_for_source[key] = actual_point
            assert len(actual_for_source) == 76 and len(rings) == 19
            checked_vertices = set(); ring_readings = []; error = 0.; section_error = 0.
            for i, ring in enumerate(rings):
                assert len(ring) == 4 and len(np.unique(ring, axis=0)) == 4
                assert not any(tuple(p) in checked_vertices for p in ring)
                checked_vertices.update(tuple(p) for p in ring)
                emitted = np.asarray([actual_for_source[tuple(p)] for p in ring])
                shifts = emitted - ring
                assert np.ptp(shifts, axis=0).max() <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Source stem ring is not a rigid translation'
                before_dist = np.linalg.norm(ring[:, None] - ring[None, :], axis=2)
                after_dist = np.linalg.norm(emitted[:, None] - emitted[None, :], axis=2)
                distortion = float(np.abs(before_dist - after_dist).max()); section_error = max(section_error, distortion)
                assert distortion <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Source ring section/thickness changed'
                centre_y = float(ring[:, 1].mean())
                def smooth(bounds):
                    t = min(1., max(0., (centre_y - bounds[0]) / (bounds[1] - bounds[0])))
                    return t * t * (3 - 2 * t)
                protected_ring = bool((ring[:, 1] <= plan['ramp_up_root_y_m'][0]).any()
                                      or (ring[:, 1] >= plan['ramp_down_root_y_m'][1]).any())
                base = plan['inboard_offset_m'] * smooth(plan['ramp_up_root_y_m']) * (1 - smooth(plan['ramp_down_root_y_m']))
                weight = smooth(plan['extra_ramp_up_root_y_m']) * (1 - smooth(plan['extra_ramp_down_root_y_m']))
                expected_dx = 0. if protected_ring else base + weight * max(0., plan['lower_target_min_x_m'] - float(ring[:, 0].min()) - base)
                delta = float(np.abs(shifts[:, 0] - expected_dx).max()); error = max(error, delta)
                assert delta <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Whole-ring route differs from bounded source recipe'
                if protected_ring:
                    assert np.array_equal(emitted, ring), 'Whole original terminal ring changed'
                ring_readings.append({'ring': i, 'terminal_ring_exact': protected_ring,
                                      'actual_x_translation_m': float(shifts[:, 0].mean()),
                                      'section_distance_error_m': distortion,
                                      'source_bounds': {'min': ring.min(axis=0).tolist(), 'max': ring.max(axis=0).tolist()},
                                      'actual_bounds': {'min': emitted.min(axis=0).tolist(), 'max': emitted.max(axis=0).tolist()}})
            assert checked_vertices == set(actual_for_source)
            max_shift = max(r['actual_x_translation_m'] for r in ring_readings)
            assert max_shift <= plan['max_ring_translation_m']
            whole_unchanged = terminal.reshape((-1, 3)).all(axis=1)
            a_normals = np.frombuffer(actual_normals, dtype='<f4').reshape((-1, 3, 3))
            b_normals = np.frombuffer(normal_bytes, dtype='<f4').reshape((-1, 3, 3))
            assert np.array_equal(a_normals[whole_unchanged], b_normals[whole_unchanged]), 'Unchanged terminal triangle NORMAL changed'
            step_rows.append({'source_part_index': source_index, 'terminal_vertices_exact': int(terminal.sum()),
                              'unchanged_terminal_triangles_PN_exact': int(whole_unchanged.sum()),
                              'recipe_position_max_error_m': error, 'base_inboard_offset_m': plan['inboard_offset_m'],
                              'whole_source_rings_verified': 19, 'max_actual_translation_m': max_shift,
                              'max_section_distance_error_m': section_error, 'actual_ring_table': ring_readings})
        else:
            expected_protected.add(source_index)
            expected_protected_rows.append((source_index, part))
            assert all(target[k] == part[k] for k in ['name', 'frame', 'material', 'triangles']), 'Protected inventory changed'
            for kind in ['POSITION', 'NORMAL']:
                assert source_binding['chunks'][kind] == target_binding['chunks'][kind], (part['name'], kind)
            assert not under_door(target_node), ('Unrelated original part moved with door', part['name'])
            assert np.array_equal(actual, positions), ('Protected closed-WORLD position changed', part['name'])
            protected_world_rows.append({'source_part_index': source_index, 'name': part['name'],
                'source_node_path': source_binding['node_path'], 'target_node_path': target_binding['node_path'],
                'expanded_local_PN_exact': True, 'closed_WORLD_PN_exact': True})
    assert expected_moved and len(expected_cut) == 1, 'Required original leaf/cut body inventory missing'
    assert len(expected_interfaces) == 2 and len(expected_steps) == 2, 'Narrow right-interface repair inventory changed'
    assert {r['name'] for r in moved_rows}.issuperset(move_names), 'Incomplete original glass/trim/door assembly'
    assert len(expected_protected) == len(protected), 'Protected classification disagrees with actual input'
    # Preserve the original all-occurrences accounting assertion, now with real
    # occurrence identity instead of rejecting or first-matching repeated names.
    used = set()
    for declared, expected in [(protected, expected_protected_rows), (changed, expected_changed_rows)]:
        assert len(declared) == len(expected)
        for claim, (source_index, part) in zip(declared, expected):
            assert all(claim[k] == part[k] for k in ['name', 'frame', 'material', 'triangle_start_in_batch', 'triangles']), 'Receipt occurrence order/identity changed'
            if 'source_part_index' in claim:
                assert claim['source_part_index'] == source_index
            assert source_index not in used
            used.add(source_index)
    assert used == set(range(len(source_parts))), 'Original occurrence accounting incomplete'

    profile = np.asarray(recipe['aperture_profile_yz_m'], dtype=float)
    assert set(recipe['profile_source_names']) == {'deep_U_closed_door', 'door_edge_lining', 'side_door_glass', 'side_window_frame'}
    assert profile.ndim == 2 and profile.shape[1] == 2 and len(profile) >= 3 and np.isfinite(profile).all()
    support = []
    for i, part in enumerate(source_parts):
        if part['name'] not in recipe['profile_source_names'] or part['frame'] != 'vehicle_body':
            continue
        p, _, _, _ = geometry(part, True, source_world)
        if p[:, 0].max() < 0:
            support.extend(p[:, 1:])
    support = np.asarray(support)
    assert len(support)
    for a, b in zip(profile, np.roll(profile, -1, axis=0)):
        edge = b - a; n = np.array([-edge[1], edge[0]]); n /= np.linalg.norm(n)
        assert (support @ n - a @ n).min() >= -CLOSED_WORLD_POSITION_TOLERANCE_M, 'Profile does not enclose actual original leaf support'
        assert (profile @ n - a @ n).min() >= -1e-10, 'Profile is not convex/CCW'
    for vertex in profile:
        assert np.linalg.norm(support - vertex, axis=1).min() <= 1e-8, 'Profile vertex is not an actual source point'
    floor_ids = [i for i, p in enumerate(source_parts) if p['name'] == 'interior_floor']
    assert len(floor_ids) == 1
    floor_id, = floor_ids
    floor_positions, _, _, _ = geometry(source_parts[floor_id], True, source_world)
    assert len(floor_positions) == 36 and len(np.unique(floor_positions, axis=0)) == 8
    floor_min, floor_max = floor_positions.min(axis=0), floor_positions.max(axis=0)
    assert recipe['backing_min_root_y_m'] - floor_max[1] >= .003, 'Backing floor gap changed'
    original_u_lining = np.concatenate([geometry(p, True, source_world)[0] for p in source_parts
        if p['name'] in ['deep_U_closed_door', 'door_edge_lining']
        and geometry(p, True, source_world)[0][:, 0].max() < 0]).reshape((-1, 3, 3))
    for reading in step_rows:
        target = next(p for p in output_parts if p.get('source_part_index') == reading['source_part_index'])
        xyz, _, _, _ = geometry(target, False, target_world)
        low_z, high_z = float(xyz[:, 2].min()), float(xyz[:, 2].max())
        closed_envelopes = []
        # Cover the WHOLE actual overlapping Y domain, including the source
        # U minimum .4899098 below the old rounded .49 observation band.
        domain_low = max(float(original_u_lining[:, :, 1].min()), float(xyz[:, 1].min()))
        domain_high = min(float(original_u_lining[:, :, 1].max()), float(xyz[:, 1].max()))
        y_breaks = sorted({domain_low, domain_high, *[y for y in [.53, .60, .65, .735] if domain_low < y < domain_high]})
        for low_y, high_y in zip(y_breaks, y_breaks[1:]):
            leaf_points = clipped_axis_vertices(original_u_lining, [(1, low_y, high_y), (2, low_z, high_z)])
            stem_points = clipped_axis_vertices(xyz.reshape((-1, 3, 3)), [(1, low_y, high_y)])
            if not len(leaf_points) or not len(stem_points):
                continue
            separator = float(stem_points[:, 0].min() - leaf_points[:, 0].max())
            assert separator >= .006, 'Actual stem triangle envelope still crosses original U/lining'
            closed_envelopes.append({'root_y_band_m': [low_y, high_y],
                                     'actual_triangle_envelope_x_separator_m': separator,
                                     'closed_only_not_swept_proof': True})
        assert closed_envelopes
        reading['actual_closed_triangle_envelope_bands'] = closed_envelopes
    cut_accounting = []
    for part, original_triangles, fixed_triangles, is_wall, original_normals in cut_rows:
        area = lambda tris: float(np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1).sum() / 2)
        source_area = area(original_triangles)
        opening_area = profile_area(original_triangles, profile, recipe['fixed_running_relief_m'])
        full_backing_area = profile_area(original_triangles, profile, -recipe['backing_relief_m'] if is_wall else 0)
        expected_backing_area = profile_area(original_triangles, profile, -recipe['backing_relief_m'] if is_wall else 0,
                                            recipe['backing_min_root_y_m'] if is_wall else None)
        fixed_area = area(fixed_triangles)
        derived_name = 'door_original_curved_backing' if is_wall else 'door_transferred_' + part['name']
        backing_parts = [p for p in output_parts if p['name'] == derived_name]
        assert len(backing_parts) == 1, 'Actual moving cut-shell backing missing/duplicated'
        backing, = backing_parts
        backing_positions, _, backing_node, _ = geometry(backing, False, target_world)
        assert backing['frame'] == 'vehicle_door_right' and under_door(backing_node), 'Cut-shell backing is not moving'
        assert backing['material'] == part['material'], 'Transferred source finish changed'
        backing_triangles = backing_positions.reshape((-1, 3, 3)); backing_area = area(backing_triangles)
        if is_wall:
            assert backing_positions[:, 1].min() >= recipe['backing_min_root_y_m'] - CLOSED_WORLD_POSITION_TOLERANCE_M, 'Added backing remains below the declared actual-floor cut'
        assert abs(fixed_area - (source_area - opening_area)) <= CUT_SURFACE_AREA_TOLERANCE_M2, 'Fixed cut-shell surface accounting changed'
        assert abs(backing_area - expected_backing_area) <= CUT_SURFACE_AREA_TOLERANCE_M2, 'Moving cut-shell backing/relief accounting changed'
        transferred_error = None
        if not is_wall:
            actual_n = np.frombuffer(component(doc, binary, backing, 'NORMAL'), dtype='<f4').reshape((-1, 3))
            source_n = np.frombuffer(original_normals, dtype='<f4').reshape((-1, 3, 3))
            transferred_error = original_surface_error(backing_positions, actual_n, original_triangles, source_n)
        cut_accounting.append({'name': part['name'], 'source_surface_area_m2': source_area,
            'fixed_retained_surface_area_m2': fixed_area, 'removed_aperture_surface_area_m2': opening_area,
            'moving_backing_surface_area_m2': backing_area,
            'declared_running_relief_surface_area_m2': opening_area - full_backing_area,
            'removed_lower_backing_source_surface_area_m2': full_backing_area - expected_backing_area,
            'fixed_running_relief_m': recipe['fixed_running_relief_m'],
            'backing_inset_m': recipe['backing_relief_m'] if is_wall else 0,
            'transferred_original_closed_surface_max_error_m': transferred_error, 'not_claimed_unchanged': True})
    caps = [p for p in output_parts if p['name'] == 'door_backing_floor_edge_cap']
    assert len(caps) == 1
    cap, = caps
    cap_positions, cap_normals, cap_node, _ = geometry(cap, False, target_world)
    assert under_door(cap_node) and cap['frame'] == 'vehicle_door_right' and cap['material'] == 0
    assert cap['engineering_source_part_indices'] == [next(iter(expected_cut)), floor_id]
    cut_y = recipe['backing_min_root_y_m']
    assert np.abs(cap_positions[:, 1] - cut_y).max() <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Backing floor edge cap changed height'
    actual_cap_normals = np.frombuffer(cap_normals, dtype='<f4').reshape((-1, 3))
    assert np.array_equal(actual_cap_normals, np.tile([0., -1., 0.], (len(cap_positions), 1))), 'Backing floor cap must face down'
    backing = next(p for p in output_parts if p['name'] == 'door_original_curved_backing')
    back_positions, _, _, _ = geometry(backing, False, target_world)
    edges = []
    for tri in back_positions.reshape((-1, 3, 3)):
        points = [p for p in tri if abs(p[1] - cut_y) <= CLOSED_WORLD_POSITION_TOLERANCE_M]
        if len(points) == 2 and np.linalg.norm(points[1] - points[0]) > 1e-10:
            edges.append(points)
    assert edges, 'Actual backing cut skins missing'
    for point in cap_positions:
        distances = []
        for a, b in edges:
            d = b - a; t = np.clip(np.dot(point - a, d) / np.dot(d, d), 0, 1)
            distances.append(np.linalg.norm(point - a - t * d))
        assert min(distances) <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Floor cap vertex is not attached to actual cut skins'
    for tri in cap_positions.reshape((-1, 3, 3)):
        assert np.cross(tri[1] - tri[0], tri[2] - tri[0])[1] < -1e-12, 'Backing cap triangle winding/area changed'
    stops = sorted(set(float(p[2]) for edge in edges for p in edge))
    expected_cap_area = 0.
    for low, high in zip(stops, stops[1:]):
        active = [(a, b) for a, b in edges if min(a[2], b[2]) <= (low + high) / 2 <= max(a[2], b[2])
                  and abs(a[2] - b[2]) > 1e-12]
        if len(active) < 2:
            continue
        widths = []
        for z in [low, high]:
            xs = [a[0] + (b[0] - a[0]) * (z - a[2]) / (b[2] - a[2]) for a, b in active]
            widths.append(max(xs) - min(xs))
        expected_cap_area += (high - low) * sum(widths) / 2
    cap_triangles = cap_positions.reshape((-1, 3, 3))
    actual_cap_area = float(np.linalg.norm(np.cross(cap_triangles[:, 1] - cap_triangles[:, 0],
                                                  cap_triangles[:, 2] - cap_triangles[:, 0]), axis=1).sum() / 2)
    assert abs(actual_cap_area - expected_cap_area) <= CUT_SURFACE_AREA_TOLERANCE_M2, 'Actual backing floor cut is not fully capped'
    # Area alone cannot distinguish equal-area duplicated and omitted facets.
    # On each Z partition, every triangle/skin interval endpoint is linear;
    # matching the ordered coverage at two interior Z values proves the full
    # partition's cross-section coverage (within the original position limit).
    all_stops = sorted(set(stops + cap_positions[:, 2].tolist()))
    coverage_sections = 0
    for low, high in zip(all_stops, all_stops[1:]):
        if high - low <= 1e-10:
            continue
        for fraction in [.25, .75]:
            z = low + fraction * (high - low)
            xs = [a[0] + (b[0] - a[0]) * (z - a[2]) / (b[2] - a[2])
                  for a, b in edges if min(a[2], b[2]) < z < max(a[2], b[2]) and abs(a[2] - b[2]) > 1e-12]
            actual_intervals = []
            for tri in cap_triangles:
                intersections = []
                for a, b in zip(tri, np.roll(tri, -1, axis=0)):
                    if min(a[2], b[2]) < z < max(a[2], b[2]):
                        intersections.append(float(a[0] + (b[0] - a[0]) * (z - a[2]) / (b[2] - a[2])))
                if intersections:
                    assert len(intersections) == 2
                    actual_intervals.append((min(intersections), max(intersections)))
            if not xs:
                assert not actual_intervals, 'Backing cap extends beyond actual cut skins'
                continue
            assert len(xs) >= 2 and actual_intervals, 'Backing cap has an actual uncovered section'
            cursor = min(xs)
            for left, right in sorted(actual_intervals):
                assert abs(left - cursor) <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Backing cap has an actual gap/overlap'
                cursor = right
            assert abs(cursor - max(xs)) <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Backing cap misses actual cut-skin width'
            coverage_sections += 1
    assert coverage_sections

    links = [p for p in output_parts if p['name'] == 'fixed_step_floor_carry_link']
    assert len(links) == 2
    link_readings = []
    for source_id in sorted(expected_steps):
        candidates = [p for p in links if p.get('engineering_source_part_indices') == [source_id, floor_id]]
        assert len(candidates) == 1
        link, = candidates
        xyz, _, node, _ = geometry(link, False, target_world)
        assert not under_door(node) and link['frame'] == 'vehicle_body' and link['material'] == 4
        assert len(xyz) == 36 and len(np.unique(xyz, axis=0)) == 8
        source_xyz, _, _, _ = geometry(source_parts[source_id], True, source_world)
        terminal_centre = np.unique(source_xyz[:6], axis=0).mean(axis=0)
        plan = recipe['fixed_step_carry_links']
        intended_end = terminal_centre + [plan['floor_inboard_offset_m'], 0, 0]
        intended_end[1] = floor_min[1] + plan['floor_engagement_m']
        axis = intended_end - terminal_centre; axis /= np.linalg.norm(axis)
        intended_start = terminal_centre - axis * plan['terminal_engagement_m']
        unique = np.unique(xyz, axis=0); projection = unique @ axis
        start_vertices = unique[projection <= projection.min() + CLOSED_WORLD_POSITION_TOLERANCE_M]
        end_vertices = unique[projection >= projection.max() - CLOSED_WORLD_POSITION_TOLERANCE_M]
        assert len(start_vertices) == len(end_vertices) == 4
        assert np.abs(start_vertices.mean(axis=0) - intended_start).max() <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Fixed carry link terminal attachment moved'
        assert np.abs(end_vertices.mean(axis=0) - intended_end).max() <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Fixed carry link floor attachment moved'
        assert np.all(end_vertices > floor_min) and np.all(end_vertices < floor_max), 'Carry link end cap is not embedded in the actual floor'
        for cross_section in [start_vertices, end_vertices]:
            measured = sorted(np.linalg.norm(cross_section[i] - cross_section[j]) for i in range(4) for j in range(i))
            expected = sorted([plan['section_m']] * 4 + [plan['section_m'] * math.sqrt(2)] * 2)
            assert np.abs(np.asarray(measured) - expected).max() <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Fixed carry link section changed'
        margins = []
        for tri in xyz.reshape((-1, 3, 3)):
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0]); n /= np.linalg.norm(n)
            assert (xyz @ n - tri[0] @ n).max() <= CLOSED_WORLD_POSITION_TOLERANCE_M, 'Carry link is not a convex outward box'
            margins.append(float((tri[0] - terminal_centre) @ n))
        assert min(margins) >= plan['terminal_engagement_m'] - CLOSED_WORLD_POSITION_TOLERANCE_M, 'Carry link does not actually engage original terminal cap'
        lo, hi = xyz.min(axis=0), xyz.max(axis=0)
        nearby_original_leaf = clipped_axis_vertices(original_u_lining, [(1, lo[1], hi[1])])
        assert len(nearby_original_leaf)
        separator = float(lo[0] - nearby_original_leaf[:, 0].max())
        assert separator >= .006, 'Fixed link crosses whole original U/lining envelope'
        assert hi[1] < back_positions[:, 1].min() - 1e-8, 'Fixed link intersects added backing height envelope'
        link_readings.append({'step_source_occurrence': source_id, 'floor_source_occurrence': floor_id,
            'actual_bounds': {'min': lo.tolist(), 'max': hi.tolist()},
            'terminal_cap_actual_interior_margin_m': min(margins), 'floor_end_cap_fully_embedded': True,
            'WHOLE_original_U_lining_all_Z_closed_x_separator_m': separator,
            'section_m': plan['section_m'], 'not_strength_or_swept_proof': True})
    triangles, moving, labels = decode(doc, binary)
    hole = recipe['aperture_root_yz_m']; inset = .015
    core = [(-.80, -.30), (hole['y_min'] + inset, hole['y_max'] - inset),
            (hole['z_min'] + inset, hole['z_max'] - inset)]
    fixed_core = triangles[~moving]
    # Same clipping assertion, conservative AABB rejection only avoids clipping
    # unrelated wheels/roof/lights thousands of times during structural controls.
    possible = np.all(fixed_core.max(axis=1) >= np.asarray(core)[:, 0], axis=1) & np.all(
        fixed_core.min(axis=1) <= np.asarray(core)[:, 1], axis=1)
    obstruction = sum(clipped_area(t, core) for t in fixed_core[possible])
    assert obstruction < 1e-10, 'A fixed wall/trim surface still closes the entry aperture'
    pivot = np.asarray(recipe['hinge_root_m']); mobile = triangles[moving] - pivot
    fixed = triangles[~moving] - pivot
    assert len(mobile) and len(fixed), 'Missing actual fixed or hinged geometry'
    summary = {'schema': 'chicago-brougham-door-structure-only-v1', 'result': 'STRUCTURE_ONLY_PASS',
        'input_sha256': sha(args.input), 'candidate_sha256': sha(args.candidate),
        'recipe_sha256': sha(args.recipe), 'source_receipt_sha256': sha(args.source_receipt),
        'checker_sha256': sha(Path(__file__)), 'protected_original_occurrences_exact': len(protected),
        'protected_actual_world_occurrences': protected_world_rows,
        'retained_original_leaf_parts': moved_rows, 'cut_shell_accounting': cut_accounting,
        'hidden_step_stem_repairs': step_rows, 'source_derived_profile_vertices': len(profile),
        'actual_floor_top_m': float(floor_max[1]), 'actual_floor_bottom_m': float(floor_min[1]),
        'actual_backing_min_y_m': float(back_positions[:, 1].min()),
        'actual_floor_edge_cap_triangles': len(cap_positions) // 3,
        'actual_floor_edge_cap_area_m2': actual_cap_area, 'actual_floor_cap_coverage_sections': coverage_sections,
        'fixed_step_carry_links': link_readings,
        'closed_world_position_tolerance_m': CLOSED_WORLD_POSITION_TOLERANCE_M,
        'cut_surface_area_tolerance_m2': CUT_SURFACE_AREA_TOLERANCE_M2,
        'all_actual_triangles': len(triangles), 'moving_triangles': int(moving.sum()),
        'actual_fixed_aperture_core_surface_area_m2': obstruction,
        'sweep_run': False, 'continuous_sweep_qualified': False, 'appearance_qualified': False,
        'boarding_enabled': False, 'qualification_flags_unchanged': doc['extras']['door_foundation']['qualification'] == recipe['qualification'],
        'scope': 'Structural geometry/ancestry and retained closed-world streams only. No swept/visual/runtime/boarding qualification.'}
    assert summary['qualification_flags_unchanged'], 'Study qualification flags changed'
    return summary, (recipe, doc, binary, protected, triangles, moving, labels, mobile, fixed)


def check(args):
    started = time.monotonic()
    progress_path = args.progress or Path(str(args.report) + '.progress.json')
    assert not progress_path.exists(), 'Fresh partial progress path required'
    progress = {'schema': 'chicago-brougham-actual-door-proof-progress-v1',
        'state': 'RUNNING', 'phase': 'STRUCTURE',
        'input_sha256': sha(args.input), 'candidate_sha256': sha(args.candidate),
        'recipe_sha256': sha(args.recipe), 'source_receipt_sha256': sha(args.source_receipt),
        'checker_sha256': sha(Path(__file__)),
        'source_file_sha256': {name: sha(Path(__file__).with_name(name)) for name in [
            'door_aperture.py', 'check_door_aperture.py', 'door-aperture.json', 'check_near.py', 'check_mid.py', 'sampled_sat.py', 'sampled_broadphase.py']},
        'settings': {'max_interval_depth': args.max_depth, 'tolerance_m': args.tolerance,
                     'sample_count': 15, 'fixed_surface_exemptions': [],
                     'sampled_only_diagnostic': args.sampled_only, 'sampled_batch_cap': BATCH_CAP},
        'sampled_angles_completed': [], 'interval_counts': {},
        'sweep_qualification_complete': False, 'final_PASS': False}

    def save_progress(**updates):
        progress.update(updates)
        progress['elapsed_s'] = time.monotonic() - started
        temporary = Path(str(progress_path) + '.tmp')
        temporary.write_text(json.dumps(progress, indent=2, allow_nan=False) + '\n')
        temporary.replace(progress_path)

    save_progress()
    structure, data = verify_structure(args)
    save_progress(phase='STRUCTURE_COMPLETED', structure=structure)
    if args.structure_only:
        args.report.write_text(json.dumps(structure, indent=2, allow_nan=False) + '\n')
        save_progress(state='STRUCTURE_ONLY_COMPLETE', phase='STRUCTURE_ONLY_COMPLETE')
        return True
    recipe, doc, binary, protected, triangles, moving, labels, mobile, fixed = data
    flo, fhi = fixed.min(axis=1), fixed.max(axis=1)
    sampled_broadphase = FixedYBroadphase(flo, fhi)
    sampled, failures = [], []
    sampled_batch_totals = {'batches': 0, 'pairs': 0, 'scalar_fallback_rows': 0,
                            'axis_cutoff_ambiguous_rows': 0, 'decision_ambiguous_rows': 0,
                            'owned_workspace_upper_bound_bytes': 0}
    total_angle = math.radians(recipe['open_angle_deg'])
    save_progress(phase='SAMPLED_SURFACES', sampled_angles_requested_deg=[float(math.degrees(a)) for a in np.linspace(0, total_angle, 15)])
    # The old 15-angle evidence is a method reference only; every row here is
    # recomputed from this exact current GLB. Do not relabel it continuous.
    for angle in np.linspace(0, total_angle, 15):
        angle_started = time.monotonic()
        hits = 0; broadphase_pairs = 0; moving_completed = 0
        last_update = time.monotonic()
        for tri in mobile:
            posed = turn(tri, angle)
            candidates = sampled_broadphase.candidates(posed.min(axis=0), posed.max(axis=0), args.tolerance)
            broadphase_pairs += len(candidates)
            for indices, gaps, diagnostics in sampled_pair_batches(posed, fixed, candidates, args.tolerance):
                sampled_batch_totals['batches'] += 1
                for key in ['pairs', 'scalar_fallback_rows', 'axis_cutoff_ambiguous_rows', 'decision_ambiguous_rows']:
                    sampled_batch_totals[key] += diagnostics[key]
                sampled_batch_totals['owned_workspace_upper_bound_bytes'] = max(
                    sampled_batch_totals['owned_workspace_upper_bound_bytes'], diagnostics['owned_workspace_upper_bound_bytes'])
                contacts = np.flatnonzero(gaps <= args.tolerance)
                hits += len(contacts)
                for local_index in contacts:
                    k = indices[local_index]
                    if len(failures) < 12:
                        failures.append({'angle_deg': math.degrees(angle), 'fixed_mesh': np.asarray(labels)[~moving][k]})
            moving_completed += 1
            if time.monotonic() - last_update >= 1:
                save_progress(current_sample={'angle_deg': float(math.degrees(angle)),
                    'moving_triangles_completed': moving_completed, 'moving_triangles_total': len(mobile),
                    'broadphase_pairs': broadphase_pairs, 'triangle_contacts': hits,
                    'elapsed_s': time.monotonic() - angle_started}, failure_examples=failures,
                    sampled_batch_totals=sampled_batch_totals, sampled_broadphase=sampled_broadphase.reading())
                last_update = time.monotonic()
        sampled.append({'angle_deg': math.degrees(angle), 'triangle_contacts': hits,
                        'broadphase_pairs': broadphase_pairs, 'seconds': time.monotonic() - angle_started})
        save_progress(sampled_angles_completed=sampled, current_sample=None, failure_examples=failures,
                      sampled_batch_totals=sampled_batch_totals, sampled_broadphase=sampled_broadphase.reading())
    if args.sampled_only:
        contacts = any(row['triangle_contacts'] for row in sampled)
        result = {'schema': 'chicago-brougham-sampled-pose-diagnostic-v1',
            'result': 'COMPLETE_WITH_SAMPLED_CONTACTS' if contacts else 'COMPLETE_NO_CONTACTS_AT_REQUESTED_SAMPLES',
            'structure': structure, 'input_sha256': sha(args.input), 'candidate_sha256': sha(args.candidate),
            'recipe_sha256': sha(args.recipe), 'source_receipt_sha256': sha(args.source_receipt),
            'checker_sha256': sha(Path(__file__)), 'sampled_helper_sha256': sha(Path(__file__).with_name('sampled_sat.py')),
            'sampled_broadphase_sha256': sha(Path(__file__).with_name('sampled_broadphase.py')),
            'sampled_broadphase': sampled_broadphase.reading(),
            'all_actual_triangles': len(triangles), 'moving_triangles': int(moving.sum()),
            'sampled': sampled, 'failure_examples': failures, 'sampled_batch_totals': sampled_batch_totals,
            'intersection_tolerance_m': args.tolerance, 'max_interval_depth_UNRUN': args.max_depth,
            'continuous_interval_run': False, 'continuous_surface_separation': False,
            'PASS': False, 'final_PASS': False, 'boarding': False, 'passenger_fit': False,
            'scope': 'Fifteen actual discrete poses only; no interval, continuous, visual, fit or delivery qualification.'}
        args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        save_progress(state='SAMPLED_DIAGNOSTIC_COMPLETE_NONQUALIFYING', phase='COMPLETE',
                      continuous_interval_run=False, final_PASS=False, sweep_qualification_complete=False,
                      final_report_sha256=sha(args.report))
        # Exit0 only means no contacts at these requested discrete samples.
        # The explicit diagnostic report can NEVER be used as a full PASS.
        return not contacts
    unresolved = 0
    interval_started = time.monotonic()
    interval_counts = {'moving_triangles_completed': 0, 'moving_triangles_total': len(mobile),
                       'broadphase_pairs': 0, 'pairs_completed': 0, 'pairs_proven_clear': 0,
                       'unresolved_or_intersecting_pairs': 0}
    if not any(r['triangle_contacts'] for r in sampled):
        save_progress(phase='CONTINUOUS_INTERVAL_SURFACES', interval_counts=interval_counts)
        last_update = time.monotonic()
        # Broad phase encloses the ENTIRE possible swept triangle, not only its
        # rest box. The tighter interval SAT then proves or rejects each pair.
        for tri in mobile:
            radius = float(np.hypot(tri[:, 0], tri[:, 2]).max())
            lo = np.array([-radius, tri[:, 1].min(), -radius])
            hi = np.array([radius, tri[:, 1].max(), radius])
            candidates = np.flatnonzero(np.all(fhi >= lo - args.tolerance, axis=1)
                                        & np.all(flo <= hi + args.tolerance, axis=1))
            interval_counts['broadphase_pairs'] += len(candidates)
            for k in candidates:
                clear, _ = interval_clear(tri, fixed[k], 0, total_angle, args.max_depth, args.tolerance)
                interval_counts['pairs_completed'] += 1
                interval_counts['pairs_proven_clear'] += int(clear)
                if not clear:
                    unresolved += 1
                interval_counts['unresolved_or_intersecting_pairs'] = unresolved
                if time.monotonic() - last_update >= 1:
                    save_progress(interval_counts=interval_counts, interval_seconds=time.monotonic() - interval_started)
                    last_update = time.monotonic()
            interval_counts['moving_triangles_completed'] += 1
        save_progress(interval_counts=interval_counts, interval_seconds=time.monotonic() - interval_started)
    else:
        unresolved = None
        save_progress(phase='CONTINUOUS_NOT_QUALIFIED_SAMPLED_CONTACTS', interval_counts=interval_counts,
                      interval_not_run_reason='Actual sampled surface contacts already reject the door; no sweep approval')
    result = {'schema': 'chicago-brougham-actual-door-surface-proof-v1',
              'structure': structure,
              'input_sha256': sha(args.input), 'candidate_sha256': sha(args.candidate),
              'recipe_sha256': sha(args.recipe), 'source_receipt_sha256': sha(args.source_receipt),
              'checker_sha256': sha(Path(__file__)), 'protected_original_occurrences_exact': len(protected),
              'sampled_helper_sha256': sha(Path(__file__).with_name('sampled_sat.py')),
              'sampled_broadphase_sha256': sha(Path(__file__).with_name('sampled_broadphase.py')),
              'sampled_broadphase': sampled_broadphase.reading(),
              'sampled_batch_totals': sampled_batch_totals,
              'progress_path': str(progress_path), 'interval_counts': interval_counts,
              'all_actual_triangles': len(triangles), 'moving_triangles': int(moving.sum()),
              'sampled': sampled, 'failure_examples': failures, 'unresolved_continuous_pairs': unresolved,
              'continuous_surface_separation': unresolved == 0,
              'intersection_tolerance_m': args.tolerance, 'max_interval_depth': args.max_depth,
              'whole_solid_containment': False, 'passenger_fit': False, 'boarding': False,
              'scope': 'Actual triangle surfaces including touches; all fixed surfaces, no contact whitelist. No enclosed-solid containment, forces or occupant proof.'}
    result['PASS'] = unresolved == 0 and not any(r['triangle_contacts'] for r in sampled)
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    save_progress(state='FULL_PROOF_PASS' if result['PASS'] else 'FULL_PROOF_NONPASS',
                  phase='COMPLETE', sweep_qualification_complete=result['PASS'], final_PASS=result['PASS'],
                  final_report_sha256=sha(args.report))
    return result['PASS']


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ['input', 'candidate', 'source-receipt', 'report']:
        cli.add_argument('--' + name, type=Path, required=True)
    cli.add_argument('--recipe', type=Path, default=Path(__file__).with_name('door-aperture.json'))
    cli.add_argument('--max-depth', type=int, default=12)
    cli.add_argument('--progress', type=Path, default=None, help='Fresh atomic source-bound partial progress JSON')
    cli.add_argument('--structure-only', action='store_true', help='Run the same structural prefix; do not execute or qualify sweep')
    cli.add_argument('--sampled-only', action='store_true', help='DIAGNOSTIC: fifteen poses only; never emits full PASS or runs interval proof')
    cli.add_argument('--tolerance', type=float, default=1e-8)
    args = cli.parse_args()
    if args.report.exists() or (args.structure_only and args.sampled_only) or not 0 < args.tolerance <= 1e-8 or not 1 <= args.max_depth <= 16:
        raise ValueError('Fresh report and strict bounded interval settings required')
    raise SystemExit(0 if check(args) else 1)
