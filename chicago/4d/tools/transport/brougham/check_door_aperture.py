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
    moved_rows, cut_rows = [], []
    expected_moved, expected_cut, expected_protected = set(), set(), set()
    expected_protected_rows, expected_changed_rows, protected_world_rows = [], [], []
    for source_index, part in enumerate(source_parts):
        positions, normal_bytes, source_node, source_binding = geometry(part, True, source_world)
        right = part['frame'] == 'vehicle_body' and positions[:, 0].max() < 0
        required_move = right and (part['name'] in move_names or
            (part['name'] == 'small_door_hardware' and positions[:, 2].mean() > 0))
        required_cut = right and part['name'] == 'deep_curved_lower_body'
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
        elif required_cut:
            expected_cut.add(source_index)
            expected_changed_rows.append((source_index, part))
            assert target['frame'] == part['frame'] and not under_door(target_node), 'Cut wall must remain fixed'
            cut_rows.append((part, positions.reshape((-1, 3, 3)), actual.reshape((-1, 3, 3))))
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

    cut_accounting = []
    for part, original_triangles, fixed_triangles in cut_rows:
        hole = recipe['aperture_root_yz_m']
        smaller = {key: value + (recipe['backing_relief_m'] if key.endswith('_min') else -recipe['backing_relief_m'])
                   for key, value in hole.items()}
        def inside_area(tris, area):
            return sum(clipped_area(t, [(-1000, 1000), (area['y_min'], area['y_max']),
                                            (area['z_min'], area['z_max'])]) for t in tris)
        area = lambda tris: float(np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1).sum() / 2)
        source_area = area(original_triangles)
        opening_area = inside_area(original_triangles, hole)
        expected_backing_area = inside_area(original_triangles, smaller)
        fixed_area = area(fixed_triangles)
        backing_parts = [p for p in output_parts if p['name'] == 'door_original_curved_backing']
        assert len(backing_parts) == 1, 'Actual moving cut-shell backing missing/duplicated'
        backing, = backing_parts
        backing_positions, _, backing_node, _ = geometry(backing, False, target_world)
        assert backing['frame'] == 'vehicle_door_right' and under_door(backing_node), 'Cut-shell backing is not moving'
        backing_triangles = backing_positions.reshape((-1, 3, 3)); backing_area = area(backing_triangles)
        assert abs(fixed_area - (source_area - opening_area)) <= CUT_SURFACE_AREA_TOLERANCE_M2, 'Fixed cut-shell surface accounting changed'
        assert abs(backing_area - expected_backing_area) <= CUT_SURFACE_AREA_TOLERANCE_M2, 'Moving cut-shell backing/relief accounting changed'
        cut_accounting.append({'name': part['name'], 'source_surface_area_m2': source_area,
            'fixed_retained_surface_area_m2': fixed_area, 'removed_aperture_surface_area_m2': opening_area,
            'moving_backing_surface_area_m2': backing_area,
            'declared_running_relief_surface_area_m2': opening_area - expected_backing_area,
            'relief_m': recipe['backing_relief_m'], 'not_claimed_unchanged': True})
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
            'door_aperture.py', 'check_door_aperture.py', 'door-aperture.json', 'check_near.py', 'check_mid.py']},
        'settings': {'max_interval_depth': args.max_depth, 'tolerance_m': args.tolerance,
                     'sample_count': 15, 'fixed_surface_exemptions': []},
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
    sampled, failures = [], []
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
            candidates = np.flatnonzero(np.all(fhi >= posed.min(axis=0) - args.tolerance, axis=1)
                                        & np.all(flo <= posed.max(axis=0) + args.tolerance, axis=1))
            broadphase_pairs += len(candidates)
            for k in candidates:
                if separation(posed, fixed[k]) <= args.tolerance:
                    hits += 1
                    if len(failures) < 12:
                        failures.append({'angle_deg': math.degrees(angle), 'fixed_mesh': np.asarray(labels)[~moving][k]})
            moving_completed += 1
            if time.monotonic() - last_update >= 1:
                save_progress(current_sample={'angle_deg': float(math.degrees(angle)),
                    'moving_triangles_completed': moving_completed, 'moving_triangles_total': len(mobile),
                    'broadphase_pairs': broadphase_pairs, 'triangle_contacts': hits,
                    'elapsed_s': time.monotonic() - angle_started}, failure_examples=failures)
                last_update = time.monotonic()
        sampled.append({'angle_deg': math.degrees(angle), 'triangle_contacts': hits,
                        'broadphase_pairs': broadphase_pairs, 'seconds': time.monotonic() - angle_started})
        save_progress(sampled_angles_completed=sampled, current_sample=None, failure_examples=failures)
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
    cli.add_argument('--tolerance', type=float, default=1e-8)
    args = cli.parse_args()
    if args.report.exists() or not 0 < args.tolerance <= 1e-8 or not 1 <= args.max_depth <= 16:
        raise ValueError('Fresh report and strict bounded interval settings required')
    raise SystemExit(0 if check(args) else 1)
