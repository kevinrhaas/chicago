# SPDX-License-Identifier: GPL-3.0-or-later
"""Original modular 1835 garment construction; generated arrays are CC0-1.0.

The dimensions are disclosed reconstructions, not measurements of a resident's
wardrobe. These helpers consume the real garment/body/hair arrays, retain the
shared rig, and never hide or modify the underlying anatomy.
"""
from __future__ import annotations

import collections
import copy
import math


def _normal(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    length = math.hypot(*n)
    return [x/length for x in n] if length > 1e-15 else None


def resolve_wardrobe(recipe, variant):
    """Resolve an explicit reusable assembly without changing identity/body data."""
    library = recipe['modular_wardrobe']
    profile = copy.deepcopy(library['assemblies'][variant['wardrobe_assembly']])
    if library['version'] != 1 or profile['grade'] != 'reconstructed':
        raise ValueError('unsupported wardrobe library/grade')
    if library.get('liberty') != 'L-human-modular-workwear-1789':
        raise ValueError('wardrobe component requires its declared liberty')
    if not 0 < library['edge_thickness_m'] <= .002:
        raise ValueError('garment return must retain the existing source ease')
    pattern = copy.deepcopy(library['connected_waistcoat_pattern'])
    if variant.get('waistcoat_shoulder_pattern'):
        pattern = copy.deepcopy(variant['waistcoat_shoulder_pattern'])
    return {**recipe, 'waistcoat_shoulder_pattern': pattern}, profile


def finish_edges(shell, thickness_m, scale=1.):
    """Add a physical cloth return to actual boundary edges, preserving old faces.

    The outer source geometry and per-corner UVs remain exact. New inner edge
    vertices inherit their own outer vertex's weights; no additional skin
    influence, material or separate overlay hides the garment boundary.
    """
    if not 0 < thickness_m <= .002 or scale <= 0:
        raise ValueError('invalid cloth thickness/scale')
    out = copy.deepcopy(shell)
    positions = shell['positions_m']
    counts = collections.Counter()
    directed = {}
    boundary_uv = {}
    normals = [[0., 0., 0.] for _ in positions]
    for fi, face in enumerate(shell['triangles']):
        n = _normal(*(positions[i] for i in face))
        if n is None:
            raise ValueError('degenerate garment input face')
        for i in face:
            for axis in range(3):
                normals[i][axis] += n[axis]
        uv = shell['corner_uvs'][fi] if 'corner_uvs' in shell else [shell['uvs'][i] for i in face]
        for j, (a, b) in enumerate(zip(face, face[1:] + face[:1])):
            key = tuple(sorted((a, b)))
            counts[key] += 1
            directed[key] = (a, b)
            boundary_uv[key] = [list(uv[k % 3]) for k in (j, j+1, j+2)]
    if any(n > 2 for n in counts.values()):
        raise ValueError('nonmanifold source garment')
    edges = [directed[key] for key, count in counts.items() if count == 1]
    # Reuse the existing cloth texels at this precise source edge. A bounded
    # barycentric step stays inside its adjacent source UV triangle, so the
    # new thickness faces have nonzero UV area without atlas bleed/repacking.
    # This is deliberate material reuse, not a claim to disjoint UV islands.
    strip_uvs = []
    for a, b in edges:
        ua, ub, uc = boundary_uv[tuple(sorted((a, b)))]
        du = [ub[i]-ua[i] for i in (0, 1)]
        uv_length = math.hypot(*du)
        area = abs(du[0]*(uc[1]-ua[1])-du[1]*(uc[0]-ua[0]))
        edge_length_m = math.dist(positions[a], positions[b])*scale
        if uv_length <= 1e-15 or area <= 1e-18 or edge_length_m <= 1e-12:
            raise ValueError('source garment boundary has a degenerate UV triangle')
        desired_height = thickness_m*uv_length/edge_length_m
        fraction = min(.20, desired_height/(area/uv_length))
        ia = [ua[i]+fraction*(uc[i]-ua[i]) for i in (0, 1)]
        ib = [ub[i]+fraction*(uc[i]-ub[i]) for i in (0, 1)]
        strip_uvs.append((ua, ub, ia, ib))
    inner = {}
    for i in sorted({v for edge in edges for v in edge}):
        length = math.hypot(*normals[i])
        if length <= 1e-12:
            raise ValueError('undefined garment edge normal')
        inner[i] = len(out['positions_m'])
        out['positions_m'].append([positions[i][a] - thickness_m/scale*normals[i][a]/length for a in range(3)])
        out['weights'].append(dict(shell['weights'][i]))
        out['uvs'].append(list(shell['uvs'][i]))
        if 'source_basis' in out:
            out['source_basis'].append(dict(shell['source_basis'][i]))
    first_return = len(out['triangles'])
    for (a, b), (ua, ub, ia, ib) in zip(edges, strip_uvs):
        for face, corner_uv in (([b, a, inner[a]], [ub, ua, ia]), ([b, inner[a], inner[b]], [ub, ia, ib])):
            if _normal(*(out['positions_m'][i] for i in face)) is None:
                raise ValueError('degenerate cloth return')
            out['triangles'].append(face)
            if 'corner_uvs' in out:
                out['corner_uvs'].append(corner_uv)
            if 'source_triangle_indices' in out:
                out['source_triangle_indices'].append(-1)
    out['flat_face_indices'] = list(range(first_return, len(out['triangles'])))
    out.setdefault('receipt', {})['physical_edge_return'] = {
        'boundary_edges': len(edges), 'thickness_m': thickness_m,
        'original_vertices_unchanged': True, 'original_faces_unchanged': True,
        'return_uvs': 'bounded adjacent-triangle cloth texel reuse; nonzero area; original source corners unchanged',
        'maximum_return_uv_barycentric_fraction': .20,
        'same_material': True, 'body_mutated': False, 'fit_accepted': False}
    return out


def _front_sample(mesh, x, y):
    """Intersect actual emitted triangles, rather than assuming a torso depth."""
    candidates = []
    for face in mesh['triangles']:
        a, b, c = [mesh['positions_m'][i] for i in face]
        denominator = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator) < 1e-14:
            continue
        u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator
        v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator
        bary = (u, v, 1-u-v)
        if min(bary) < -1e-10:
            continue
        z = math.fsum(w*p[2] for w, p in zip(bary, (a, b, c)))
        weights = collections.defaultdict(float)
        for w, i in zip(bary, face):
            for name, value in mesh['weights'][i].items():
                weights[name] += max(0., w)*value
        items = sorted(weights.items(), key=lambda p: (-p[1], p[0]))
        if math.fsum(w for _, w in items[4:]) > .025:
            raise ValueError('button interpolation exceeds existing skin-weight limit')
        items = items[:4]
        total = math.fsum(w for _, w in items)
        candidates.append((z, {name: w/total for name, w in items}))
    if not candidates:
        raise ValueError('button has no actual garment surface underneath')
    z, weights = max(candidates, key=lambda p: p[0])
    if z <= 0:
        raise ValueError('button surface is not the front of the garment')
    return z, weights


def round_jacket(body_mesh, bones, recipe, height, profile, scale=1.):
    """A separate, open-front source-fitted jacket with connected folded lapels.

    This is an original short work-jacket pattern, not a dated cutting diagram.
    Its underlying shirt/waistcoat/body remain present. New front cut vertices
    interpolate the real source skin; the lapel folds join those actual edges.
    """
    spec = profile.get('jacket')
    if spec is None:
        return None
    from human_workwear_fit import garment_shell, _clip
    if not .02 <= spec['ease_m'] <= .04 or not .52 <= spec['hem_fraction'] <= .58:
        raise ValueError('unsupported reconstructed jacket ease/length')
    source = garment_shell(body_mesh, 'shirt', spec['ease_m'],
                           {**recipe, 'shirt_hem_fraction': spec['hem_fraction']},
                           bones, height, scale)
    waist = recipe['waist_height_fraction']*height/scale
    neck = bones['neck_01']['head_m'][1]
    def opening(y):
        return (.018+.065*max(0., min(1., (y-waist)/(neck-waist))))/scale
    out = {'name': 'round_jacket', 'material': 'garment_outer__round_jacket',
           'positions_m': [], 'triangles': [], 'uvs': [], 'weights': [], 'corner_uvs': []}
    cache = {}
    for fi, face in enumerate(source['triangles']):
        polygon = [{'p': source['positions_m'][i], 'uv': source['corner_uvs'][fi][j],
                    'w': source['weights'][i], 'basis': {i: 1.}, 'n': [0, 0, 1]}
                   for j, i in enumerate(face)]
        back = _clip(polygon, lambda v: -v['p'][2])
        front = _clip(polygon, lambda v: v['p'][2])
        left = _clip(front, lambda v: v['p'][0]-opening(v['p'][1]))
        right = _clip(front, lambda v: -v['p'][0]-opening(v['p'][1]))
        for poly in (back, left, right):
            ids = []
            for v in poly:
                weights = sorted(((b, w) for b, w in v['w'].items() if w > 1e-12), key=lambda x: (-x[1], x[0]))
                if math.fsum(w for _, w in weights[4:]) > .025:
                    raise ValueError('jacket cut exceeds existing discarded-weight limit')
                weights = weights[:4]; total = math.fsum(w for _, w in weights)
                weights = {b: w/total for b, w in weights}
                key = (tuple(v['p']), tuple(sorted(weights.items())))
                if key not in cache:
                    cache[key] = len(out['positions_m'])
                    out['positions_m'].append(list(v['p'])); out['uvs'].append(list(v['uv']))
                    out['weights'].append(weights)
                ids.append(cache[key])
            for j in range(1, len(ids)-1):
                tri = [ids[0], ids[j], ids[j+1]]
                if len(set(tri)) == 3 and _normal(*(out['positions_m'][i] for i in tri)) is not None:
                    out['triangles'].append(tri)
                    out['corner_uvs'].append([poly[k]['uv'] for k in (0, j, j+1)])
    counts = collections.Counter(tuple(sorted((a, b))) for f in out['triangles'] for a, b in zip(f, f[1:]+f[:1]))
    folds = {}
    lapel_edges = []
    for fi, face in enumerate(list(out['triangles'])):
        for edge_index, (a, b) in enumerate(zip(face, face[1:]+face[:1])):
            if counts[tuple(sorted((a, b)))] != 1:
                continue
            points = [out['positions_m'][i] for i in (a, b)]
            if not all(p[2] > 0 and p[1] >= waist+.035/scale and abs(abs(p[0])-opening(p[1])) < 1e-9 for p in points):
                continue
            lapel_edges.append((a, b))
            for i in (a, b):
                if i not in folds:
                    p = out['positions_m'][i]; folds[i] = len(out['positions_m'])
                    out['positions_m'].append([p[0]+math.copysign(spec['lapel_width_m']/scale, p[0]), p[1], p[2]+.008/scale])
                    out['uvs'].append(list(out['uvs'][i])); out['weights'].append(dict(out['weights'][i]))
            ua, ub, uc = [out['corner_uvs'][fi][i % 3] for i in (edge_index, edge_index+1, edge_index+2)]
            du = [ub[i]-ua[i] for i in (0, 1)]
            uv_length = math.hypot(*du)
            area = abs(du[0]*(uc[1]-ua[1])-du[1]*(uc[0]-ua[0]))
            if uv_length <= 1e-15 or area <= 1e-18:
                raise ValueError('jacket lapel requires a nondegenerate adjacent UV face')
            edge_length_m = math.dist(*points)*scale
            fraction = min(.20, spec['lapel_width_m']*uv_length/edge_length_m/(area/uv_length))
            ia = [ua[i]+fraction*(uc[i]-ua[i]) for i in (0, 1)]
            ib = [ub[i]+fraction*(uc[i]-ub[i]) for i in (0, 1)]
            for tri, uv in (([b, a, folds[a]], [ub, ua, ia]), ([b, folds[a], folds[b]], [ub, ia, ib])):
                out['triangles'].append(tri)
                out['corner_uvs'].append(uv)
    if not lapel_edges:
        raise ValueError('jacket has no connected front lapels')
    out['receipt'] = {'construction': 'source-fitted short round jacket with connected folded front edges',
                      'connected_lapel_edges': len(lapel_edges), 'source_body_mutated': False,
                      'source_body_uvs_mutated': False, 'grade': 'reconstructed', 'fit_accepted': False}
    return out


def waistcoat_buttons(garment, bones, recipe, profile, lod, scale=1.):
    """Small closed, skinned buttons seated on the real waistcoat front."""
    count = profile['waistcoat_buttons']
    if not 3 <= count <= 7 or lod not in range(4):
        raise ValueError('invalid button assembly')
    waist = recipe['waist_height_fraction']*profile['body_height_m']/scale
    shoulder = bones['upperarm_l']['head_m'][1]
    closure = waist+recipe['workwear_tailoring_v5']['waistcoat_closed_front_torso_fraction']*(shoulder-waist)
    low, high = waist+.025/scale, closure-.016/scale
    if high <= low:
        raise ValueError('waistcoat closure has no button run')
    result = {'name': 'waistcoat_buttons', 'material': 'accessory__horn_buttons',
              'positions_m': [], 'triangles': [], 'uvs': [], 'weights': [], 'corner_uvs': []}
    radius = profile['button_radius_m']/scale
    if not .002 <= radius*scale <= .006:
        raise ValueError('unsupported reconstructed button radius')
    segments = (12, 10, 8, 6)[lod]
    for button in range(count):
        y = low+(high-low)*button/(count-1)
        x = .010/scale
        z, weights = _front_sample(garment, x, y)
        rings = []
        for depth, r in ((.0002, radius*.8), (.0018, radius), (.003, radius*.72)):
            ring = []
            for i in range(segments):
                theta = 2*math.pi*i/segments
                ring.append(len(result['positions_m']))
                result['positions_m'].append([x+r*math.cos(theta), y+r*math.sin(theta), z+depth/scale])
                result['uvs'].append([.5+.45*math.cos(theta), .5+.45*math.sin(theta)])
                result['weights'].append(dict(weights))
            rings.append(ring)
        for row, (front, back) in enumerate(zip(rings, rings[1:])):
            for i in range(segments):
                j = (i+1) % segments
                result['triangles'].extend(([front[i], front[j], back[j]], [front[i], back[j], back[i]]))
                u0, u1 = i/segments, (i+1)/segments
                v0, v1 = row/2, (row+1)/2
                result['corner_uvs'].extend(([[u0,v0],[u1,v0],[u1,v1]], [[u0,v0],[u1,v1],[u0,v1]]))
        for ring, reverse, depth in ((rings[0], True, .0002), (rings[-1], False, .003)):
            center = len(result['positions_m'])
            result['positions_m'].append([x, y, z+depth/scale])
            result['uvs'].append([.5, .5]); result['weights'].append(dict(weights))
            for i in range(segments):
                face = [center, ring[i], ring[(i+1) % segments]]
                face = face[::-1] if reverse else face
                result['triangles'].append(face)
                result['corner_uvs'].append([result['uvs'][i] for i in face])
    result['receipt'] = {'count': count, 'surface': 'actual waistcoat triangles',
                         'grade': 'reconstructed', 'fit_accepted': False}
    return result


def work_hat(hair, bones, profile, lod, scale=1.):
    """Closed hollow felt-hat construction fitted around the unchanged hair.

    A broad uncreased crown/brim is an original period-category reconstruction,
    not a traced hat, a resident possession, or a recovered historical color.
    """
    spec = profile.get('hat')
    if spec is None:
        return None
    if lod not in range(4) or scale <= 0:
        raise ValueError('invalid hat LOD/scale')
    points = hair['positions_m']
    top = max(p[1] for p in points)
    base = top-spec['seating_depth_m']/scale
    crown = [p for p in points if p[1] >= base]
    if not crown:
        raise ValueError('hat has no actual hair support')
    cx = (min(p[0] for p in crown)+max(p[0] for p in crown))/2
    cz = (min(p[2] for p in crown)+max(p[2] for p in crown))/2
    rx = max(abs(p[0]-cx) for p in crown)+.008/scale
    rz = max(abs(p[2]-cz) for p in crown)+.008/scale
    enlarge = max(1., max(math.hypot((p[0]-cx)/rx, (p[2]-cz)/rz) for p in crown))
    rx *= enlarge; rz *= enlarge
    thickness = .003/scale
    height = max(spec['crown_height_m']/scale, top-base+.015/scale)
    brim = spec['brim_m']/scale
    if not .02 <= brim*scale <= .09 or not .04 <= height*scale <= .18:
        raise ValueError('unsupported reconstructed hat dimensions')
    # Closed cross section: inner opening, brim, crown and two solid top faces.
    section = [(1-thickness/rx, base), (1+brim/rx, base-.006/scale),
               (1+brim/rx, base-.003/scale), (1, base+thickness),
               (1, base+height), (0, base+height),
               (0, base+height-thickness), (1-thickness/rx, base+height-thickness)]
    n = (48, 32, 20, 12)[lod]
    result = {'name': 'work_hat', 'material': 'headwear__felt_hat',
              'positions_m': [], 'triangles': [], 'uvs': [], 'weights': [], 'corner_uvs': []}
    rings = []
    for radius, y in section:
        ring = []
        for i in range(n if radius else 1):
            theta = 2*math.pi*i/n
            ring.append(len(result['positions_m']))
            result['positions_m'].append([cx+rx*radius*math.cos(theta), y, cz+rz*radius*math.sin(theta)])
            result['uvs'].append([i/n, (y-base+.006/scale)/(height+.006/scale)])
            result['weights'].append({'head': 1.})
        rings.append(ring)
    section_lengths = [math.hypot(rx*(b[0]-a[0]), b[1]-a[1]) for a,b in zip(section,section[1:]+section[:1])]
    perimeter = math.fsum(section_lengths)
    for row, (first, second) in enumerate(zip(rings, rings[1:]+rings[:1])):
        if len(first) == len(second) == 1:
            continue
        for i in range(n):
            a, b = first[i % len(first)], first[(i+1) % len(first)]
            c, d = second[(i+1) % len(second)], second[i % len(second)]
            v0 = math.fsum(section_lengths[:row])/perimeter
            v1 = math.fsum(section_lengths[:row+1])/perimeter
            quv = [[i/n,v0],[(i+1)/n,v0],[(i+1)/n,v1],[i/n,v1]]
            if len(first) == 1 or len(second) == 1:
                quv = [[.5+(result['positions_m'][j][0]-cx)/(2*rx), .5+(result['positions_m'][j][2]-cz)/(2*rz)] for j in (a,b,c,d)]
            for face, uv in (([a,b,c],[quv[0],quv[1],quv[2]]), ([a,c,d],[quv[0],quv[2],quv[3]])):
                if len(set(face)) == 3:
                    result['triangles'].append(face)
                    result['corner_uvs'].append(uv)
    volume = math.fsum(sum(result['positions_m'][a][k]*v for k, v in enumerate([
        result['positions_m'][b][1]*result['positions_m'][c][2]-result['positions_m'][b][2]*result['positions_m'][c][1],
        result['positions_m'][b][2]*result['positions_m'][c][0]-result['positions_m'][b][0]*result['positions_m'][c][2],
        result['positions_m'][b][0]*result['positions_m'][c][1]-result['positions_m'][b][1]*result['positions_m'][c][0]]))/6
        for a, b, c in result['triangles'])
    if volume < 0:
        result['triangles'] = [face[::-1] for face in result['triangles']]
        result['corner_uvs'] = [uv[::-1] for uv in result['corner_uvs']]
    result['receipt'] = {'actual_hair_vertices_used': len(crown), 'body_or_hair_mutated': False,
                         'head_bone': 'head', 'grade': 'reconstructed', 'fit_accepted': False}
    return result
