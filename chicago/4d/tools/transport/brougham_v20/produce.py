# SPDX-License-Identifier: GPL-3.0-or-later
"""V20 plate-matched Brougham: the V19 specimen with its driving box rebuilt to plate 0095.

T-3558 (owner, 2026-11-12/17). Read beside Studebaker's 1893 colour plate (leaf 0095,
source `studebaker_1893_illustrated_souvenir`), the V19 Brougham's two visible misses were
its coachman's seat, which stood on four bare posts with a loose footboard below, where the
plate draws a closed black box with a curved upright dash and a swept iron under it, and a
rear mudguard over each back wheel, which the plate does not have.

This stage DERIVES V20 from the V19 physical masters; it never edits the V19 producer, whose
own checks stay as they are. Everything else of V19 is carried over byte for byte: the
body, door, glass, roof, lamps, wheels, springs, pole, contacts, anchors, the driver's
cushion, backboard, rails and footboard (the seated coachman's fit rests on those), and the
passengers' seats. Only the six named V19 parts in REMOVED leave, and the parts in ADDED
join the black-timber and iron batches of the body.

Usage (fresh output directory; writes near/mid/far raw + indexed GLBs and a receipt):

    python3 tools/transport/brougham_v20/produce.py --output /tmp/v20

The far detail runs the unchanged V19 producer with far-lods.json, then the same derivation.
No Blender, image, texture or download is used.
"""
from pathlib import Path
import argparse, hashlib, json, math, struct, subprocess, sys, tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
V19 = HERE.parent / 'brougham'
ROOT = HERE.parents[2]
ASSET = ROOT / 'renderers/web/transport/parked-brougham'
sys.path.insert(0, str(V19))
from check_near import read  # noqa: E402
from check_mid import bind_parts  # noqa: E402
from index_streams import write_indexed  # noqa: E402

REMOVED = {'perch_support', 'footboard_support', 'thin_rear_mudguard'}
ADDED = ['box_side_panel', 'box_seat_riser', 'box_dash', 'box_dash_rail', 'box_dash_stay', 'box_sweep_iron']
# Body-frame geometry in V19 is authored, then lifted by its declared vertical affine.
AFFINE = (1.13, 0.03)
SAMPLES = {'near': {'outline': 28, 'curve': 18, 'tube': 8, 'dash_x': 14},
           'mid': {'outline': 16, 'curve': 10, 'tube': 6, 'dash_x': 8},
           'far': {'outline': 8, 'curve': 6, 'tube': 4, 'dash_x': 4}}
sha = lambda b: hashlib.sha256(b).hexdigest()


def lift(points):
    """V19 pre-affine body coordinates (its parameters' numbers) to delivered metres."""
    p = np.array(points, dtype=np.float64)
    p[..., 1] = p[..., 1] * AFFINE[0] + AFFINE[1]
    return p


def bezier(p0, c, p1, n):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(c) + t ** 2 * np.array(p1)


def catmull(points, n):
    q = np.array(points, dtype=float)
    q = np.vstack([2 * q[0] - q[1], q, 2 * q[-1] - q[-2]])
    out = []
    for i in range(1, len(q) - 2):
        for t in np.linspace(0, 1, n, endpoint=False):
            a, b, c, d = q[i - 1], q[i], q[i + 1], q[i + 2]
            out.append(.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    out.append(q[-2])
    return np.array(out)


class Mesh:
    """Triangle soup with explicit per-corner normals (V19's own P/N layout)."""

    def __init__(self):
        self.p, self.n = [], []

    def tri(self, a, b, c, normal=None):
        a, b, c = map(np.asarray, (a, b, c))
        nn = np.cross(b - a, c - a)
        length = np.linalg.norm(nn)
        if length < 1e-12:
            raise ValueError('Degenerate V20 triangle')
        nn = nn / length
        self.p.extend([a, b, c]); self.n.extend([nn, nn, nn])

    def quad(self, a, b, c, d):
        self.tri(a, b, c); self.tri(a, c, d)

    def arrays(self):
        return np.array(self.p, dtype='<f4'), np.array(self.n, dtype='<f4')


def plate(outline_zy, x0, x1):
    """A flat board: polygon in (z, y) extruded across x0..x1, faces outward."""
    m = Mesh(); q = np.array(outline_zy); n = len(q)
    c = q.mean(axis=0)
    lo, hi = min(x0, x1), max(x0, x1)
    area = np.sum(q[:, 0] * np.roll(q[:, 1], -1) - q[:, 1] * np.roll(q[:, 0], -1))
    if area < 0:
        q = q[::-1]
    P = lambda x, zy: np.array([x, zy[1], zy[0]])
    for i in range(n):
        a, b = q[i], q[(i + 1) % n]
        # In (z, y) counter-clockwise, the +x face is seen with (y, z) orientation reversed.
        m.tri(P(hi, c), P(hi, b), P(hi, a))
        m.tri(P(lo, c), P(lo, a), P(lo, b))
        m.quad(P(lo, a), P(hi, a), P(hi, b), P(lo, b))
    return m


def outward(m, centre):
    """Flip any face whose normal points at the solid's centre (thin convex parts)."""
    return orient(m, lambda mid, normal: mid - centre)


def orient(m, want):
    """Flip any flat face whose normal disagrees with want(mid, normal)."""
    p, n = m.p, m.n
    for i in range(0, len(p), 3):
        mid = (p[i] + p[i + 1] + p[i + 2]) / 3
        if np.dot(n[i], want(mid, n[i])) < 0:
            p[i + 1], p[i + 2] = p[i + 2], p[i + 1]
            for k in range(3):
                n[i + k] = -n[i + k]
    return m


def tube(path, radius, sides):
    m = Mesh(); path = np.array(path, dtype=float)
    tangents = np.gradient(path, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]
    ref = np.eye(3)[int(np.argmin(np.max(np.abs(tangents), axis=0)))]
    rings, normals = [], []
    for c, u in zip(path, tangents):
        a = np.cross(u, ref); a /= np.linalg.norm(a); b = np.cross(u, a)
        ring = [(math.cos(t) * a + math.sin(t) * b) for t in np.arange(sides) * math.tau / sides]
        normals.append(ring); rings.append([c + radius * r for r in ring])
    for i in range(len(path) - 1):
        for j in range(sides):
            k = (j + 1) % sides
            quad = [(i, j), (i + 1, j), (i + 1, k), (i, k)]
            for tri in ([quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]):
                pts = [rings[a][b] for a, b in tri]
                if np.dot(np.cross(pts[1] - pts[0], pts[2] - pts[0]), normals[tri[0][0]][tri[0][1]]) < 0:
                    tri = [tri[0], tri[2], tri[1]]
                m.p.extend(rings[a][b] for a, b in tri); m.n.extend(normals[a][b] for a, b in tri)
    for end, sign in [(0, -1), (len(path) - 1, 1)]:
        c = path[end]; u = tangents[end] * sign
        for j in range(sides):
            a, b = rings[end][j], rings[end][(j + 1) % sides]
            tri = [c, a, b] if np.dot(np.cross(a - c, b - c), u) > 0 else [c, b, a]
            m.p.extend(tri); m.n.extend([u, u, u])
    return m


def box_parts(detail):
    """The rebuilt driving box, in delivered vehicle-root metres (body frame = root)."""
    s = SAMPLES[detail]; parts = []
    # Pre-affine V19 numbers: perch base underside 1.365, cushion z .565-.955,
    # footboard top .9375 at z 1.08-1.44, body front about z .46-.50 at y .70-1.0.
    top_rear, top_front = (0.40, 1.365), (0.955, 1.365)
    foot_rear = (1.08, 0.955)
    bottom_rear = (0.47, 0.975)
    front_edge = bezier(top_front, (1.05, 1.24), foot_rear, s['outline'] // 2)
    bottom_edge = bezier(foot_rear, (0.78, 0.925), bottom_rear, s['outline'] // 2)
    outline = [top_rear] + [tuple(p) for p in front_edge] + [tuple(p) for p in bottom_edge[1:]]
    outline_m = [(z, y * AFFINE[0] + AFFINE[1]) for z, y in outline]
    for side in (1, -1):
        m = plate(outline_m, side * 0.5225, side * 0.5475)
        centre = np.array([side * 0.535, np.mean([y for _, y in outline_m]), np.mean([z for z, _ in outline_m])])
        parts.append(('box_side_panel', 1, outward(m, centre)))
    # The box's front under the cushion, behind the coachman's calves: a ruled board
    # between the two side panels' front edges.
    m = Mesh(); edge = lift([[0, y, z] for z, y in front_edge])
    for i in range(len(edge) - 1):
        a, b = edge[i], edge[i + 1]
        for x0, x1 in [(-0.5225, 0.5225)]:
            A, B, C, D = [np.array([x, p[1], p[2]]) for x, p in [(x0, a), (x1, a), (x1, b), (x0, b)]]
            m.quad(A, D, C, B)
    # One board face toward the coachman's feet; its back is inside the closed box.
    parts.append(('box_seat_riser', 1, orient(m, lambda mid, n: np.array([0, 0.3, 1.0]))))
    # The dash: an upright board at the footboard's front, raked forward, wrapping a
    # little round the coachman's feet in plan; plate 0095 draws it black and plain.
    xs = np.linspace(-0.49, 0.49, s['dash_x'] + 1)
    ys = np.linspace(0.935, 1.27, max(3, s['curve'] // 3))
    def dash(x, y, t=0.0):
        rake = 0.06 * (y - 0.935) / (1.27 - 0.935)
        wrap = -0.05 * (x / 0.49) ** 2
        return lift([x, y, 1.425 + rake + wrap + t])
    m = Mesh()
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            for t in (0.012, -0.012):
                A, B, C, D = dash(xs[i], ys[j], t), dash(xs[i + 1], ys[j], t), dash(xs[i + 1], ys[j + 1], t), dash(xs[i], ys[j + 1], t)
                face = Mesh(); face.quad(A, D, C, B)
                face = orient(face, lambda mid, n, t=t: np.array([0, 0, t]))
                m.p.extend(face.p); m.n.extend(face.n)
    for x, sgn in [(xs[0], -1), (xs[-1], 1)]:
        for j in range(len(ys) - 1):
            A, B, C, D = dash(x, ys[j], -0.012), dash(x, ys[j], 0.012), dash(x, ys[j + 1], 0.012), dash(x, ys[j + 1], -0.012)
            face = Mesh(); face.quad(A, B, C, D)
            face = orient(face, lambda mid, n, sgn=sgn: np.array([sgn, 0, 0])); m.p.extend(face.p); m.n.extend(face.n)
    for y, sgn in [(ys[0], -1), (ys[-1], 1)]:
        for i in range(len(xs) - 1):
            A, B, C, D = dash(xs[i], y, -0.012), dash(xs[i + 1], y, -0.012), dash(xs[i + 1], y, 0.012), dash(xs[i], y, 0.012)
            face = Mesh(); face.quad(A, B, C, D)
            face = orient(face, lambda mid, n, sgn=sgn: np.array([0, sgn, 0])); m.p.extend(face.p); m.n.extend(face.n)
    parts.append(('box_dash', 1, m))
    rail = [dash(x, 1.285) for x in np.linspace(-0.49, 0.49, s['dash_x'] + 1)]
    parts.append(('box_dash_rail', 4, tube(rail, 0.011, s['tube'])))
    for side in (1, -1):
        stay = catmull(lift([[side * 0.47, 0.94, 1.30], [side * 0.48, 1.06, 1.40], [side * 0.48, 1.18, 1.448]]), max(2, s['curve'] // 4))
        parts.append(('box_dash_stay', 4, tube(stay, 0.009, s['tube'])))
    # The swept iron the plate draws under the box, from the footboard's front back
    # and down into the body's lower front; inside the front wheels' locked sweep.
    for side in (1, -1):
        path = catmull(lift([[side * 0.40, 0.905, 1.36], [side * 0.40, 0.87, 1.12],
                             [side * 0.40, 0.80, 0.86], [side * 0.40, 0.73, 0.62],
                             [side * 0.40, 0.70, 0.50]]), max(2, s['curve'] // 4))
        parts.append(('box_sweep_iron', 4, tube(path, 0.017, s['tube'])))
    return parts


def derive(source_glb, detail, out_glb, simplified=None):
    j, b = read(Path(source_glb))
    rows = bind_parts(j, b)
    names = {p['name'] for p in j['extras']['parts']}
    assert REMOVED <= names, 'V19 parts to remove are present'
    mesh_parent = {}
    for i, n in enumerate(j['nodes']):
        for c in n.get('children', []):
            if 'mesh' in j['nodes'][c]:
                mesh_parent[j['nodes'][c]['mesh']] = i
    # Batch order and contents, V19 order kept; removed parts drop out.
    batches = {mi: {'P': [], 'N': [], 'parts': []} for mi in range(len(j['meshes']))}
    for row in rows:
        name, frame, mat, tris = row['identity']
        if name in REMOVED:
            continue
        chunks = row['chunks']
        if simplified and name in simplified:
            P, N = simplified[name][row['part_index']]
            chunks = {'POSITION': P.tobytes(), 'NORMAL': N.tobytes()}
            tris = len(P) // 9
        batch = batches[row['mesh_index']]
        start = len(batch['P']) // 36 if False else sum(len(c) for c in batch['P']) // 36
        batch['P'].append(chunks['POSITION']); batch['N'].append(chunks['NORMAL'])
        batch['parts'].append({**j['extras']['parts'][row['part_index']], 'triangle_start_in_batch': start, 'triangles': tris})
    body = next(i for i, n in enumerate(j['nodes']) if n['name'] == 'vehicle_body')
    target = {mat: next(mi for mi, m in enumerate(j['meshes']) if m['name'] == f'surface_vehicle_body_{mat}') for mat in (1, 4)}
    for name, mat, m in box_parts(detail):
        P, N = m.arrays()
        if not (np.isfinite(P).all() and np.isfinite(N).all()):
            raise ValueError('Non-finite V20 geometry ' + name)
        batch = batches[target[mat]]
        start = sum(len(c) for c in batch['P']) // 36
        batch['P'].append(P.tobytes()); batch['N'].append(N.tobytes())
        batch['parts'].append({'name': name, 'frame': 'vehicle_body', 'material': mat, 'triangle_start_in_batch': start, 'triangles': len(P) // 3})
    # Rebuild: keep node order; drop a mesh (and its node) only if it emptied.
    keep = [mi for mi in range(len(j['meshes'])) if batches[mi]['P']]
    remap = {old: new for new, old in enumerate(keep)}
    nodes = []
    old_to_new_node = {}
    for i, n in enumerate(j['nodes']):
        if 'mesh' in n and n['mesh'] not in remap:
            continue
        old_to_new_node[i] = len(nodes)
        nodes.append(dict(n))
    for n in nodes:
        if 'children' in n:
            kids = [old_to_new_node[c] for c in n['children'] if c in old_to_new_node]
            if kids:
                n['children'] = kids
            else:
                n.pop('children')
        if 'mesh' in n:
            n['mesh'] = remap[n['mesh']]
    binary = bytearray(); views = []; access = []; meshes = []; parts = []
    def append(data, count):
        arr = np.frombuffer(data, dtype='<f4').reshape(-1, 3)
        off = len(binary); binary.extend(data); vi = len(views)
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data), 'target': 34962})
        ai = len(access)
        access.append({'bufferView': vi, 'componentType': 5126, 'count': count, 'type': 'VEC3', 'min': arr.min(axis=0).tolist(), 'max': arr.max(axis=0).tolist()})
        return ai
    # V19's extras.parts list follows batch creation order; keep it by sorting on the
    # V19 part order, with added parts after their batch's last V19 part.
    for mi in keep:
        batch = batches[mi]
        P = b''.join(batch['P']); N = b''.join(batch['N']); count = len(P) // 12
        mesh = dict(j['meshes'][mi]); prim = dict(mesh['primitives'][0])
        prim['attributes'] = {'POSITION': append(P, count), 'NORMAL': append(N, count)}
        mesh['primitives'] = [prim]; meshes.append(mesh)
    order = {id(p): k for k, p in enumerate(j['extras']['parts'])}
    for mi in keep:
        parts.extend(batches[mi]['parts'])
    extras = json.loads(json.dumps(j['extras']))
    # Part list in V19's own order of first appearance per batch (bind_parts reads
    # parts sequentially per mesh name, so each batch's rows must stay contiguous
    # and ordered by start; V19 interleaves batches, which bind_parts allows).
    v19_rank = {}
    for k, p in enumerate(j['extras']['parts']):
        v19_rank.setdefault((p['frame'], p['material']), k)
    extras['parts'] = parts
    tris = sum(p['triangles'] for p in parts)
    extras['statistics'] = {'triangles': tris, 'meshes': len(meshes), 'nodes': len(nodes)}
    extras['status'] = ('V20 plate-matched Studebaker 1893 Brougham: the V19 specimen with its driving box rebuilt '
                        'to plate 0095 (closed black box, upright dash, swept box irons) and no rear mudguards; '
                        'static empty reconstruction, the driven rows carry it in town')
    extras['plate_match_v20'] = {
        'ticket': 'T-3558', 'detail': detail, 'derived_from_v19_raw_sha256': sha(Path(source_glb).read_bytes()),
        'removed_v19_parts': sorted(REMOVED), 'added_parts': ADDED,
        'reference': {'source_id': 'studebaker_1893_illustrated_souvenir', 'scan_leaf': '0095'},
        'grade': 'reconstructed',
        'basis': ('Plate 0095 draws the coachman on a closed black box above a curved upright dash, a swept iron '
                  'under the box into the body, and no mudguard over the rear wheels. Board thickness, the dash '
                  'height and rake, the iron section and every hidden joint are reconstructed; the seat, '
                  'footboard and every V19 anchor stand exactly where the seated coachman was fitted.'),
        'far_body_simplified': bool(simplified)}
    doc = dict(j); doc['nodes'] = nodes; doc['meshes'] = meshes; doc['bufferViews'] = views
    doc['accessors'] = access; doc['buffers'] = [{'byteLength': len(binary)}]; doc['extras'] = extras
    doc['scenes'] = [{'nodes': [old_to_new_node[i] for i in j['scenes'][0]['nodes']]}]
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * ((-len(enc)) % 4)
    binary += b'\0' * ((-len(binary)) % 4)
    out = struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary
    Path(out_glb).write_bytes(out)
    return {'detail': detail, 'triangles': tris, 'meshes': len(meshes), 'nodes': len(nodes), 'bytes': len(out), 'sha256': sha(out)}


SIMPLIFY = {'cabin_front_lower': 0.2, 'deep_curved_lower_body': 0.25}


def simplify_far(source_glb, tools_root):
    """meshoptimizer (pinned 1.2.0) on the two dense body shells; original P/N kept per corner."""
    j, b = read(Path(source_glb))
    out = {}
    for name, ratio in SIMPLIFY.items():
        rows = [r for r in bind_parts(j, b) if r['identity'][0] == name]
        payload = {'parts': {name: [{'P': np.frombuffer(r['chunks']['POSITION'], '<f4').tolist(),
                                     'N': np.frombuffer(r['chunks']['NORMAL'], '<f4').tolist()} for r in rows]},
                   'ratio': ratio, 'error': 0.02}
        res = subprocess.run(['node', str(HERE / 'simplify_far.mjs'), '--tools-root', str(tools_root)],
                             input=json.dumps(payload).encode(), capture_output=True, check=True)
        got = json.loads(res.stdout)[name]
        unit = lambda n: (np.array(n).reshape(-1, 3) / np.linalg.norm(np.array(n).reshape(-1, 3), axis=1)[:, None]).astype('<f4').reshape(-1)
        out[name] = {r['part_index']: (np.array(g['P'], dtype='<f4'), unit(g['N'])) for r, g in zip(rows, got)}
    return out


def far_source(workdir):
    out = Path(workdir) / 'v19-far'
    subprocess.run([sys.executable, str(V19 / 'generate.py'), '--output', str(out), '--detail', 'far',
                    '--lod-recipe', str(HERE / 'far-lods.json'), '--rear-quarter-recipe', str(V19 / 'rear-quarter.json')],
                   check=True, capture_output=True)
    return out / 'brougham.glb'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--tools-root', type=Path, required=True, help='node_modules holding meshoptimizer 1.2.0')
    a = ap.parse_args()
    if a.output.exists():
        raise ValueError('Fresh output required')
    a.output.mkdir(parents=True)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        sources = {'near': ASSET / 'brougham-source.glb', 'mid': ASSET / 'brougham-mid-source.glb', 'far': far_source(tmp)}
        for detail, src in sources.items():
            raw = a.output / f'brougham-v20-{detail}-source.glb'
            row = derive(src, detail, raw, simplify_far(src, a.tools_root) if detail == 'far' else None)
            row.update(write_indexed(raw, a.output / f'brougham-v20-{detail}.glb'))
            row['v19_source_sha256'] = sha(Path(src).read_bytes())
            rows.append(row)
    (a.output / 'RECEIPT.json').write_text(json.dumps({'variant': 'V20_plate_match', 'rows': rows}, indent=2) + '\n')
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
