# SPDX-License-Identifier: GPL-3.0-or-later
"""Bind C02 triangle labels to active exported articulation; sample actual GLB poses."""
from pathlib import Path
import argparse, collections, contextlib, hashlib, io, json, math, runpy, struct, sys
import tempfile, time
import numpy as np
ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(node):
    if 'matrix' in node:
        require(not any(k in node for k in ('translation', 'rotation', 'scale')), 'Matrix and TRS cannot coexist')
        m = np.asarray(node['matrix'], dtype=float).reshape(4, 4, order='F')
    else:
        x, y, z, w = node.get('rotation', [0, 0, 0, 1])
        require(abs(x*x+y*y+z*z+w*w-1) < 1e-6, 'Invalid node quaternion')
        r = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                      [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                      [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        m = np.eye(4)
        m[:3, :3] = r @ np.diag(node.get('scale', [1, 1, 1]))
        m[:3, 3] = node.get('translation', [0, 0, 0])
    require(np.isfinite(m).all() and np.allclose(m[3], [0, 0, 0, 1], atol=1e-12, rtol=0), 'Invalid affine node frame')
    return m


def world(nodes, parents, index, pose=None):
    m = (pose or {}).get(index, local(nodes[index]))
    while index in parents:
        index = parents[index]
        m = (pose or {}).get(index, local(nodes[index])) @ m
    return m


def active_hierarchy(g):
    parents, active = {}, set()
    pending = [(i, None) for i in g['scenes'][g.get('scene', 0)]['nodes']]
    while pending:
        index, parent = pending.pop()
        require(0 <= index < len(g['nodes']), 'Invalid active node index')
        require(index not in active, 'Active scene has repeated node, multiple parents or cycle')
        active.add(index)
        if parent is not None:
            parents[index] = parent
        pending.extend((i, index) for i in g['nodes'][index].get('children', []))
    return parents, active


def descendant(index, pivot, parents):
    while index != pivot and index in parents:
        index = parents[index]
    return index == pivot


def triangles(binary, accessors, views, primitive):
    require(primitive.get('mode', 4) == 4 and 'indices' not in primitive, 'Expected original unindexed triangle export')
    a = accessors[primitive['attributes']['POSITION']]
    v = views[a['bufferView']]
    require(a['componentType'] == 5126 and a['type'] == 'VEC3' and v.get('byteStride', 12) == 12,
            'Expected tightly packed FLOAT32 VEC3 positions')
    require(a['count'] % 3 == 0, 'Incomplete triangle')
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    xyz = np.asarray(struct.unpack_from('<%sf' % (a['count']*3), binary, offset)).reshape(-1, 3, 3)
    require(np.isfinite(xyz).all(), 'Nonfinite geometry')
    return xyz


def transformed(xyz, matrix):
    return xyz @ matrix[:3, :3].T + matrix[:3, 3]


def key(triangle):
    return tuple(sorted(tuple(round(float(v), 5) for v in p) for p in triangle))


# Original SAT, including coplanar in-plane axes; tolerance unchanged at 1e-8 m.
def intersects(a, b, tol=1e-8):
    ea = np.roll(a, -1, axis=0)-a; eb = np.roll(b, -1, axis=0)-b
    na = np.cross(ea[0], ea[1]); nb = np.cross(eb[0], eb[1])
    axes = [na, nb]+[np.cross(x, y) for x in ea for y in eb]+[np.cross(na, x) for x in ea]+[np.cross(nb, x) for x in eb]
    for axis in axes:
        length = np.linalg.norm(axis)
        if length < 1e-14:
            continue
        axis = axis/length; pa = a@axis; pb = b@axis
        if pa.max() < pb.min()-tol or pb.max() < pa.min()-tol:
            return False
    return True


def predicate_controls():
    a = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
    cases = [(np.array([[.1, .1, 0], [.4, .1, 0], [.1, .4, 0]]), True),
             (np.array([[.8, .8, 0], [1, .8, 0], [.8, 1, 0]]), False),
             (np.array([[0, 0, .001], [1, 0, .001], [0, 1, .001]]), False),
             (np.array([[.2, .2, -1], [.2, .2, 1], [.4, .2, 0]]), True),
             (np.array([[0, 0, 0], [1, 0, 0], [0, -1, 0]]), True)]
    for b, expected in cases:
        require(intersects(a, b) == expected and intersects(b, a) == expected, 'Triangle predicate control failed')


def check(args, receipt, output):
    receipt['stage'] = 'source_generation'
    previous = sys.argv[:]
    try:
        sys.argv = [str(args.generator), '--parameters', str(args.parameters), '--output-dir', str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            e = runpy.run_path(str(args.generator))
    finally:
        sys.argv = previous
    source_nodes = e['oldnodes']
    source_parents = {c: i for i, n in enumerate(source_nodes) for c in n.get('children', [])}
    source_pivots = [i for i, n in enumerate(source_nodes) if n['name'] == 'vehicle_door_left']
    require(len(source_pivots) == 1, 'One source door pivot required')
    source_pivot = source_pivots[0]
    parts = []
    for i, node in enumerate(source_nodes):
        if 'mesh' not in node:
            continue
        for primitive in e['oldmeshes'][node['mesh']]['primitives']:
            xyz = triangles(e['oldbinary'], e['oldaccess'], e['oldviews'], primitive)
            parts.append({'name': node['name'], 'source_node': i,
                          'moving': descendant(i, source_pivot, source_parents),
                          'triangles': transformed(xyz, world(source_nodes, source_parents, i))})
    receipt['stage'] = 'active_export_decode'
    raw = args.asset.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]
    g = json.loads(raw[20:20+size]); binary = raw[28+size:]
    receipt.update(input_sha256=hashlib.sha256(raw).hexdigest(), generator_sha256=hashlib.sha256(args.generator.read_bytes()).hexdigest(),
                   parameters_sha256=hashlib.sha256(args.parameters.read_bytes()).hexdigest())
    require(g['extras']['units'] == 'm' and g['extras']['up_axis'] == '+Y' and g['extras']['forward_axis'] == '+Z', 'Invalid metric frame')
    require(g['extras']['parameters'] == e['params'], 'Asset parameter metadata stale')
    require(g['extras']['boarding_enabled'] is False, 'Boarding must remain disabled')
    require(g['extras']['scene_eligibility'] == e['sidecar']['scene_eligibility'] and '1904' in g['extras']['scene_eligibility'] and 'not 1835' in g['extras']['scene_eligibility'], 'Invalid period eligibility')
    parents, active = active_hierarchy(g)
    pivots = [i for i in active if g['nodes'][i].get('name') == 'vehicle_door_left']
    require(len(pivots) == 1, 'One active exported door pivot required')
    pivot = pivots[0]; pivot_rest = local(g['nodes'][pivot])
    # Viewer sets rotation.y from zero; require the original unscaled, unrotated local hinge basis.
    require(np.allclose(pivot_rest[:3, :3], np.eye(3), atol=1e-12, rtol=0), 'Exported hinge local basis changed')
    require(np.allclose(world(g['nodes'], parents, pivot), world(source_nodes, source_parents, source_pivot), atol=1e-12, rtol=0), 'Exported hinge world frame changed')
    receipt['actual_active_door_node'] = pivot
    records, lookup = [], collections.defaultdict(list)
    for i in sorted(active):
        node = g['nodes'][i]
        if 'mesh' not in node:
            continue
        matrix = world(g['nodes'], parents, i)
        for pi, primitive in enumerate(g['meshes'][node['mesh']]['primitives']):
            for ti, xyz in enumerate(triangles(binary, g['accessors'], g['bufferViews'], primitive)):
                record = {'node': i, 'primitive': pi, 'triangle': ti, 'local': xyz,
                          'world': transformed(xyz, matrix), 'moving': descendant(i, pivot, parents)}
                records.append(record); lookup[key(record['world'])].append(record)
    receipt['active_triangle_count'] = len(records)
    receipt['actual_active_moving_triangle_count'] = sum(r['moving'] for r in records)
    receipt['stage'] = 'closed_geometry_and_actual_ancestry_binding'
    for part in parts:
        bound = []
        for triangle in part['triangles']:
            candidates = lookup[key(triangle)]
            require(bool(candidates), 'Active exported triangle missing for source part '+part['name'])
            record = candidates.pop()
            require(max(min(np.linalg.norm(record['world']-v, axis=1)) for v in triangle) < 1e-6, 'Closed geometry mapping exceeds 1 micrometre')
            require(record['moving'] == part['moving'], 'Actual door ancestry mismatch for source part '+part['name']+' at exported node '+str(record['node']))
            bound.append(record)
        part['records'] = bound
    require(not any(lookup.values()), 'Unmatched active exported triangles')
    require(len(records) == 11512, 'Unexpected final active triangle count')
    moving = [p for p in parts if p['moving']]; fixed = [p for p in parts if not p['moving']]
    require(moving and fixed, 'Missing actual moving/fixed geometry')
    receipt['moving_source_parts'] = [p['name'] for p in moving]
    predicate_controls(); receipt['predicate_controls_both_orders'] = 10
    receipt['stage'] = 'actual_hierarchy_discrete_poses'; rows = receipt['rows'] = []
    for degrees in range(0, 71, 5):
        angle = math.radians(degrees); c, s = math.cos(angle), math.sin(angle)
        posed_pivot = pivot_rest.copy(); posed_pivot[:3, :3] = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
        matrices = {i: world(g['nodes'], parents, i, {pivot: posed_pivot}) for i in active}
        # Both fixed and moving geometry come from actual primitive-local GLB positions and hierarchy.
        ft = np.asarray([transformed(r['local'], matrices[r['node']]) for p in fixed for r in p['records']])
        labels = [(p['name'], r['node'], r['triangle']) for p in fixed for r in p['records']]
        flo, fhi = ft.min(1), ft.max(1); hits = collections.Counter(); examples = []; candidates = 0
        max_travel = 0.
        for part in moving:
            for record in part['records']:
                a = transformed(record['local'], matrices[record['node']])
                max_travel = max(max_travel, float(np.linalg.norm(a-record['world'], axis=1).max()))
                ix = np.flatnonzero(np.all(fhi >= a.min(0)-1e-8, axis=1) & np.all(flo <= a.max(0)+1e-8, axis=1)); candidates += len(ix)
                for k in ix:
                    if intersects(a, ft[k]):
                        name, node, tri = labels[k]; hits[(part['name'], record['node'], name, node)] += 1
                        if len(examples) < 12:
                            examples.append({'moving': [part['name'], record['node'], record['triangle']], 'fixed': [name, node, tri]})
        rows.append({'angle_deg': degrees, 'broadphase_pairs': candidates, 'triangle_intersections_including_contact': sum(hits.values()),
                     'actual_moving_max_vertex_travel_m': max_travel,
                     'part_pairs': [{'moving': a, 'moving_node': b, 'fixed': c, 'fixed_node': d, 'triangle_pairs': count} for (a, b, c, d), count in hits.items()], 'examples': examples})
        print(degrees, sum(hits.values()), flush=True)
    require(rows[-1]['actual_moving_max_vertex_travel_m'] > .5, 'Actual exported door did not travel')
    require(all(r['triangle_intersections_including_contact'] == 0 for r in rows), 'Actual discrete door surface interference')
    receipt.update(passed=True, stage='complete', actual_final_triangles_matched_to_source_labels=len(records))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--parameters', type=Path, default=ROOT/'data/transport/studies/carriage-c02.json')
    cli.add_argument('--generator', type=Path, default=Path(__file__).with_name('generate_carriage_c02.py'))
    cli.add_argument('--asset', type=Path, default=ROOT/'renderers/web/transport/carriage-c02/carriage-c02.glb')
    cli.add_argument('--receipt', type=Path); args = cli.parse_args()
    receipt = {'passed': False, 'status': 'Actual selected-GLB ancestry binding and hierarchy-composed triangle surface SAT',
               'scope': '15 discrete door angles only; all contacts retained, no whitelist; no continuous clearance/solid containment/occupant acceptance',
               'angles_deg': list(range(0, 71, 5)), 'intersection_tolerance_m': 1e-8, 'closed_mapping_tolerance_m': 1e-6, 'all_contacts_preserved': True}
    began = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix='c02-actual-door-check-') as temp:
            check(args, receipt, Path(temp))
    except Exception as error:
        receipt['error'] = str(error)
        raise
    finally:
        receipt['elapsed_s'] = time.time()-began
        if args.receipt:
            args.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print('PASS: 11512 actual active triangles, actual door ancestry/poses, 15 discrete angles, zero contacts; no continuous/inside/occupant acceptance')


if __name__ == '__main__':
    main()
