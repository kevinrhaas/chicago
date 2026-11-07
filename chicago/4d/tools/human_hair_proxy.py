# SPDX-License-Identifier: GPL-3.0-or-later
"""Fit any cleared hm08 MakeClothes hair proxy (.mhclo + .obj) to a resident's body (T-3434).

The same arithmetic as human_hair_short04 (barycentric rows on the fitted body plus scaled
offsets, skin weights interpolated and pruned to four), for a hair component named by its
recipe instead of the one short04 cap: the 1904 cook's bun, drawn back from the face.
Every file is checked against the component's SOURCE.json and that manifest against the
recipe's pin; the source must be CC0 in its manifest. No MakeHuman program code is used.
"""
import hashlib, json, math, pathlib


def _safe(name, what):
    p = pathlib.PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or p.as_posix() != name:
        raise ValueError(f'unsafe {what}: {name}')
    return p


def fit(body, config, root):
    folder = pathlib.Path(root)/_safe(config['directory'], 'hair component directory')
    for key in ['roughness', 'alpha_cutoff']:
        value = config[key]
        if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('hair material setting must be finite within 0..1: '+key)
    manifest = (folder/'SOURCE.json').read_bytes()
    if hashlib.sha256(manifest).hexdigest() != config['source_manifest_sha256']:
        raise ValueError('hair source manifest hash mismatch')
    source = json.loads(manifest)
    if source['license'] != 'CC0-1.0':
        raise ValueError('hair source must be CC0')
    members = {row['path']: row for row in source['files']}
    for row in source['files']:
        if hashlib.sha256((folder/_safe(row['path'], 'hair source path')).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('hair source hash mismatch: '+row['path'])
    for key in ['mhclo', 'obj', 'texture']:
        if config[key] not in members:
            raise ValueError(f'hair {key} must be a verified manifest member')
    rows, scales, uv, faces, reading = [], {}, [], [], False
    for line in (folder/config['mhclo']).read_text().splitlines():
        f = line.split()
        if not f or f[0].startswith('#'):
            continue
        if f[0] == 'basemesh' and f[1] != 'hm08':
            raise ValueError('hair basemesh mismatch')
        if f[0] == 'obj_file' and f[1] != config['obj']:
            raise ValueError('hair proxy names another OBJ')
        if f[0] in ['x_scale', 'y_scale', 'z_scale']:
            scales[f[0][0]] = (int(f[1]), int(f[2]), float(f[3]))
        elif f[0] == 'verts':
            reading = True
        elif reading and len(f) == 9:
            rows.append(([int(x) for x in f[:3]], [float(x) for x in f[3:6]], [float(x) for x in f[6:9]]))
        elif reading:
            raise ValueError('unsupported hair proxy row')
    if sorted(scales) != ['x', 'y', 'z']:
        raise ValueError('hair proxy lacks its scale references')
    count = 0
    for line in (folder/config['obj']).read_text().splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == 'v':
            count += 1
        elif f[0] == 'vt':
            uv.append([float(x) for x in f[1:3]])
        elif f[0] == 'f':
            corners = [tuple(int(x)-1 for x in s.split('/')[:2]) for s in f[1:]]
            for j in range(1, len(corners)-1):
                faces.append([corners[0], corners[j], corners[j+1]])
    if count != len(rows) or [len(rows), len(faces)] != config['topology']:
        raise ValueError(f'unexpected source hair topology {len(rows)} rows/{count} vertices, {len(faces)} triangles')
    points, skin = {}, {}
    for m in body['meshes']:
        for i, p, w in zip(m['source_vertex_indices'], m['positions_m'], m['weights']):
            if i in points and (math.dist(points[i], p) > 1e-10 or skin[i] != w):
                raise ValueError('body source seam disagreement')
            points[i] = p; skin[i] = w
    required = {i for ids, bary, offset in rows for i in ids} | {i for a, b, d in scales.values() for i in [a, b]}
    if required-set(points):
        raise ValueError('hair references missing body source vertices')
    factor = [abs(points[scales[a][0]][k]-points[scales[a][1]][k])/scales[a][2] for k, a in enumerate('xyz')]
    coords, weights, max_pruned = [], [], 0
    for ids, bary, offset in rows:
        total = math.fsum(bary)
        if abs(total-1) > 2e-5:
            raise ValueError('invalid geometric barycentric sum')
        bary = [v/total for v in bary]
        coords.append([math.fsum(w*points[i][k] for w, i in zip(bary, ids))+offset[k]*factor[k] for k in range(3)])
        accum = {}
        for w, i in zip(bary, ids):
            for joint, value in skin[i].items():
                accum[joint] = accum.get(joint, 0)+w*value
        ordered = sorted(((n, w) for n, w in accum.items() if w > 0), key=lambda x: (-x[1], x[0]))
        max_pruned = max(max_pruned, math.fsum(w for n, w in ordered[4:]))
        keep = ordered[:4]; s = math.fsum(w for n, w in keep)
        if s <= 0:
            raise ValueError('unweighted hair vertex')
        weights.append({n: w/s for n, w in keep})
    split, p, u, w, t = {}, [], [], [], []
    for face in faces:
        tri = []
        for vi, ti in face:
            if (vi, ti) not in split:
                split[vi, ti] = len(p); p.append(coords[vi]); u.append(list(uv[ti])); w.append(weights[vi])
            tri.append(split[vi, ti])
        t.append(tri)
    if not all(0 <= v <= 1 for pair in u for v in pair):
        raise ValueError('hair UV outside human contract')
    report = {'source': {k: source[k] for k in ['asset', 'license', 'archive_url']}, 'missing_references': 0,
              'triangles_each_lod': len(t), 'vertices_each_lod': len(p), 'max_pruned_weight_mass': max_pruned,
              'limitations': 'Cleared CC0 proxy fitted unchanged; period appearance reconstructed, not a likeness. All LODs preserve source topology.'}
    return {'positions_m': p, 'triangles': t, 'uvs': u, 'weights': w}, folder/config['texture'], report
