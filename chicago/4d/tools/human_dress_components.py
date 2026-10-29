# SPDX-License-Identifier: GPL-3.0-or-later
"""Original adult dress components on the existing portable source skeleton.

Generated geometry is CC0-1.0. This is disclosed reconstructed authoring, not
a dated pattern, named likeness, canonical export or accepted photographic asset.
The unchanged source anatomy remains present. Skirt skinning is intentionally a
pelvis-bound standing construction: walking/seated cloth deformation is UNQUALIFIED.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import json
import math
from pathlib import Path

from human_source_normals import source_shared_normals
from human_workwear_fit import _clip, _slab_points, fitted_shoes
from human_period_wardrobe import finish_edges

BODY_SHA256 = '3060ee86957ff7c2d70c89e70fe95ff3bc2294a0d7f6a5716b5a2f3f8dd84c72'


def need(test, message):
    if not test:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def empty(name, material):
    return dict(name=name, material=material, positions_m=[], triangles=[], uvs=[],
                corner_uvs=[], weights=[])


def skin(mapping):
    items = sorted(((k, v) for k, v in mapping.items() if v > 1e-12), key=lambda p: (-p[1], p[0]))
    need(math.fsum(v for _, v in items[4:]) <= .025, 'garment cut discards more than 2.5 percent skin mass')
    items = items[:4]
    total = math.fsum(v for _, v in items)
    need(total > 0, 'empty garment weights')
    return {k: v/total for k, v in items}


def cloth_torso(mesh, bones, waist):
    """Bridge anatomy with a smooth opaque cloth volume, retaining source body.

    The fitted source topology supplies sleeve articulation and UVs, but its
    breast/nipple relief is inappropriate as the outside of a woven bodice.
    Measured elliptical support sections bridge that relief on the new garment
    only. C1 shape-preserving interpolation avoids a sequence of hard ring bands.
    The arm-influence/shoulder transition is continuous and sleeves stay source-fit.
    """
    ps = mesh['positions_m']; weights = mesh['weights']
    shoulder = bones['upperarm_l']['head_m'][1]
    hi = shoulder+.005; rows = 33; step = (hi-waist)/(rows-1)
    arm = [math.fsum(v for b, v in w.items() if b.startswith(('clavicle', 'upperarm', 'lowerarm'))) for w in weights]
    samples = [p for p, a in zip(ps, arm) if a < .10 and abs(p[0]) < .235 and waist <= p[1] <= hi]
    need(bool(samples), 'no source torso for cloth envelope')
    profiles = []
    for i in range(rows):
        y = waist+i*step
        points = [p for p in samples if abs(p[1]-y) <= 1.6*step]
        need(len(points) >= 3, 'empty torso cloth support band')
        center = (max(p[2] for p in points)+min(p[2] for p in points))/2
        rx = max(abs(p[0]) for p in points)+.008
        rz = (max(p[2] for p in points)-min(p[2] for p in points))/2+.008
        bound = max(1., max(math.hypot(p[0]/rx, (p[2]-center)/rz) for p in points))
        profiles.append([rx*bound, rz*bound, center])
    def draped(values):
        # Upper concave hull: a woven envelope spans the under-bust hollow,
        # rather than following the body's anatomical crease. These are
        # reconstructed garment supports, not altered body or measured stays.
        hull = []
        for i, value in enumerate(values):
            while len(hull) >= 2:
                a, b = hull[-2:]
                if (values[b]-values[a])/(b-a) >= (value-values[b])/(i-b):
                    break
                hull.pop()
            hull.append(i)
        result = list(values)
        for a, b in zip(hull, hull[1:]):
            for i in range(a, b+1):
                t = (i-a)/(b-a); result[i] = (1-t)*values[a]+t*values[b]
        return result
    fronts = draped([center+rz for rx, rz, center in profiles])
    backs = [-x for x in draped([-center+rz for rx, rz, center in profiles])]
    widths = draped([rx for rx, rz, center in profiles])
    profiles = [[widths[i], (fronts[i]-backs[i])/2, (fronts[i]+backs[i])/2] for i in range(rows)]
    slopes = []
    for axis in range(3):
        ds = [(profiles[i+1][axis]-profiles[i][axis])/step for i in range(rows-1)]
        slopes.append([ds[0]]+[0. if ds[i-1]*ds[i] <= 0 else 2*ds[i-1]*ds[i]/(ds[i-1]+ds[i]) for i in range(1, rows-1)]+[ds[-1]])
    def profile(y):
        t = max(0., min(rows-1., (y-waist)/step)); i = min(rows-2, int(t)); u = t-i
        return [(2*u**3-3*u*u+1)*profiles[i][a]+(u**3-2*u*u+u)*step*slopes[a][i]
                +(-2*u**3+3*u*u)*profiles[i+1][a]+(u**3-u*u)*step*slopes[a][i+1] for a in range(3)]
    padding = 1.
    for p, mass in zip(ps, arm):
        if mass < .10 and waist <= p[1] <= hi:
            rx, rz, center = profile(p[1]); padding = max(padding, math.hypot(p[0]/rx, (p[2]-center)/rz))
    padding *= 1.01
    changed = 0; maximum = 0.
    for i, (p, mass) in enumerate(zip(ps, arm)):
        if not waist <= p[1] <= hi or mass >= .30:
            continue
        gain = min(1., max(0., (hi-p[1])/.055))*min(1., max(0., (.30-mass)/.20))*min(1., max(0., (p[1]-waist)/.060))
        # C1 ease at both ends of the garment-only transition.
        gain = gain*gain*(3-2*gain)
        if gain <= 0:
            continue
        rx, rz, center = profile(p[1]); rx *= padding; rz *= padding
        norm = math.hypot(p[0]/rx, (p[2]-center)/rz)
        need(norm > .01, 'torso source point on polar axis')
        radial = max(1., 1/norm)
        q = [p[0]*(1+gain*(radial-1)), p[1], center+(p[2]-center)*(1+gain*(radial-1))]
        maximum = max(maximum, math.dist(p, q)); changed += q != p; ps[i] = q
    mesh['receipt'] = dict(construction='Smooth C1 draped cloth envelope spanning under-bust relief, tapering to zero at waist seam',
                           source_body_mutated=False, affected_garment_vertices=changed,
                           maximum_garment_radial_expansion_m=maximum, ellipse_support_padding=padding,
                           skin_weights_and_source_UVs_unchanged=True, photographic_or_all_pose_fit_accepted=False)
    return mesh


def bodice(body, bones, waist, ease=.010):
    """Closed long-sleeve source-fitted bodice with linear neck/waist/cuff cuts."""
    out = empty('plain_closed_bodice', 'garment_upper__plain_dress')
    source = body['meshes'][0]
    positions = source['positions_m']
    normals = source_shared_normals(positions, source['triangles'], source['source_vertex_indices'])
    neck = bones['neck_01']['head_m'][1]
    cuff = abs(bones['hand_l']['head_m'][0])-.012
    cache = {}
    for face in source['triangles']:
        poly = [dict(p=positions[i], uv=source['uvs'][i], w=source['weights'][i], n=normals[i],
                     basis={source['source_vertex_indices'][i]: 1.}) for i in face]
        for field in (lambda v: v['p'][1]-waist, lambda v: neck-v['p'][1],
                      lambda v: cuff-v['p'][0], lambda v: cuff+v['p'][0]):
            poly = _clip(poly, field)
        ids = []
        for v in poly:
            normal_length = math.hypot(*v['n'])
            need(normal_length > 1e-12, 'undefined source garment normal')
            n = [x/normal_length for x in v['n']]
            # Ease Y continuously to zero at cut planes; never clamp interior
            # triangles into coplanar folded fans or move/hide the body.
            y_gain = min(1., max(0., min(v['p'][1]-waist, neck-v['p'][1]))/(2*ease))
            x_gain = min(1., max(0., cuff-abs(v['p'][0]))/(2*ease))
            p = [v['p'][a]+ease*n[a]*({0: x_gain, 1: y_gain}.get(a, 1.)) for a in range(3)]
            mapping = dict(v['w'])
            if abs(v['p'][1]-neck) < 1e-12:
                transfer = math.fsum(mapping.pop(k, 0.) for k in ('head', 'jaw'))
                mapping['neck_01'] = mapping.get('neck_01', 0.)+transfer
            weights = skin(mapping)
            key = (tuple(p), tuple(sorted(weights.items())))
            if key not in cache:
                cache[key] = len(out['positions_m'])
                out['positions_m'].append(p); out['uvs'].append(list(v['uv'])); out['weights'].append(weights)
            ids.append(cache[key])
        for i in range(1, len(ids)-1):
            face = [ids[0], ids[i], ids[i+1]]
            if len(set(face)) < 3:
                continue
            a, b, c = [out['positions_m'][k] for k in face]
            u, v = [[q[j]-a[j] for j in range(3)] for q in (b, c)]
            area = math.hypot(u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            if area <= 1e-18:
                continue
            out['triangles'].append(face)
            out['corner_uvs'].append([poly[k]['uv'] for k in (0, i, i+1)])
    out = finish_edges(cloth_torso(out, bones, waist), .0015)
    out['receipt'].update(source_body_mutated=False, nominal_normal_ease_m=ease,
                          source_body_uvs_reused=True, neckline_y_m=neck, waist_y_m=waist,
                          construction='Long sleeves and closed torso; reconstructed cut, no historical personal outfit')
    return out


def skirt(body, bones, waist, upper_garment=None, segments=96, rows=18, ease=.015, hem=.055):
    """Standing skirt with gathered radial folds around a proven convex core.

    Each core ring encloses the COMPLETE source triangle slabs above and below
    it. Corresponding polygon edges share fixed normals, so each linear loft
    panel bounds its complete source slab. Fold vertices move radially outward;
    all emitted triangles remain outside their own original panel's halfspace.
    This proves standing-body clearance, not cloth mechanics or walking fit.
    """
    need(segments >= 48 and segments % 12 == 0 and rows >= 4 and .01 <= ease <= .03,
         'unsupported skirt discretization/ease')
    levels = [waist+(hem-waist)*i/(rows-1) for i in range(rows)]
    triangles = [[mesh['positions_m'][i] for i in face] for mesh in body['meshes'] for face in mesh['triangles']
                 if min(mesh['positions_m'][i][1] for i in face) <= waist and max(mesh['positions_m'][i][1] for i in face) >= hem]
    normals = [(math.sin(2*math.pi*(k+.5)/segments), math.cos(2*math.pi*(k+.5)/segments)) for k in range(segments)]
    supports = []
    for i, y in enumerate(levels):
        points = _slab_points(triangles, levels[min(rows-1, i+1)], levels[max(0, i-1)])
        need(bool(points), 'empty body skirt band')
        t = i/(rows-1)
        rx, rz = .155+.19*t**.78, .130+.15*t**.78
        supports.append([max(math.hypot(rx*nx, rz*nz), max(nx*p[0]+nz*p[2] for p in points)+ease)
                         for nx, nz in normals])
    out = empty('gathered_ankle_skirt', 'garment_lower__plain_dress')
    core = []
    for i, y in enumerate(levels):
        ring = []
        for k in range(segments):
            nx0, nz0 = normals[(k-1)%segments]; nx1, nz1 = normals[k]
            a, b = supports[i][(k-1)%segments], supports[i][k]
            det = nx0*nz1-nx1*nz0
            x, z = (a*nz1-b*nz0)/det, (nx0*b-nx1*a)/det
            need(x*math.sin(2*math.pi*k/segments)+z*math.cos(2*math.pi*k/segments) > 0,
                 'invalid polar support polygon')
            ring.append((x, y, z))
            # Twelve restrained broad gathers, amplified below the waist.
            gather = (.003+.011*(i/(rows-1))**.6)*(1-math.cos(12*2*math.pi*k/segments))*.5
            r = math.hypot(x, z); factor = 1+gather/r
            out['positions_m'].append([factor*x, y, factor*z]); out['uvs'].append([k/segments, i/(rows-1)])
            out['weights'].append({'pelvis': 1.})
        core.append(ring)
    minimum_panel_margin = math.inf
    for i in range(rows-1):
        for k, (nx, nz) in enumerate(normals):
            n = (k+1)%segments
            faces = [[i*segments+k, (i+1)*segments+n, i*segments+n],
                     [i*segments+k, (i+1)*segments+k, (i+1)*segments+n]]
            for f in faces:
                out['triangles'].append(f)
                uv = [[((v % segments)/segments if v % segments else (1. if k == segments-1 else 0.)), (v//segments)/(rows-1)] for v in f]
                out['corner_uvs'].append(uv)
                for v in f:
                    p = out['positions_m'][v]; t = (p[1]-levels[i])/(levels[i+1]-levels[i])
                    bound = (1-t)*supports[i][k]+t*supports[i+1][k]
                    minimum_panel_margin = min(minimum_panel_margin, nx*p[0]+nz*p[2]-bound)
    need(minimum_panel_margin >= -1e-10, 'fold triangle enters guaranteed body-clearance core')
    minimum_body_clearance = math.inf
    tested = 0
    for i in range(rows-1):
        for p in _slab_points(triangles, levels[i+1], levels[i]):
            t = (p[1]-levels[i])/(levels[i+1]-levels[i])
            for k, (nx, nz) in enumerate(normals):
                bound = (1-t)*supports[i][k]+t*supports[i+1][k]
                minimum_body_clearance = min(minimum_body_clearance, bound-nx*p[0]-nz*p[2])
                tested += 1
    need(minimum_body_clearance >= ease-1e-10, 'standing skirt core intersects source anatomy')
    # Close the top annulus against the ACTUAL emitted bodice, rather than
    # leaving an open gap between a broad skirt and narrower fitted torso.
    # The small1.5mm underlap is a garment-layer construction, not hidden skin.
    need(upper_garment is not None, 'skirt requires an actual upper garment for its waist closure')
    join_y = waist+.014
    sections = []
    for face in upper_garment['triangles']:
        triangle = [upper_garment['positions_m'][i] for i in face]
        if min(p[1] for p in triangle) <= join_y <= max(p[1] for p in triangle):
            points = _slab_points([triangle], join_y, join_y)
            unique = list(dict.fromkeys(tuple(p) for p in points))
            if len(unique) == 2:
                sections.append(unique)
    inner = []
    for k in range(segments):
        dx, dz = math.sin(2*math.pi*k/segments), math.cos(2*math.pi*k/segments)
        radii = []
        for a, b in sections:
            ux, uz = b[0]-a[0], b[2]-a[2]
            denominator = ux*dz-uz*dx
            if abs(denominator) < 1e-14:
                continue
            t = -(a[0]*dz-a[2]*dx)/denominator
            if -1e-10 <= t <= 1+1e-10:
                radius = (a[0]+t*ux)*dx+(a[2]+t*uz)*dz
                if radius > 0:
                    radii.append(radius)
        need(bool(radii), 'waist closure has no actual garment cross-section')
        radius = max(radii)-.0015
        need(radius > .02, 'waist closure underlap exceeds garment radius')
        inner.append(len(out['positions_m']))
        out['positions_m'].append([radius*dx, join_y, radius*dz])
        out['uvs'].append([k/segments, .025]); out['weights'].append({'pelvis': 1.})
    for k in range(segments):
        n = (k+1)%segments
        for face, uv in (([k, n, inner[n]], [[k/segments, 0], [(k+1)/segments, 0], [(k+1)/segments, .025]]),
                         ([k, inner[n], inner[k]], [[k/segments, 0], [(k+1)/segments, .025], [k/segments, .025]])):
            out['triangles'].append(face); out['corner_uvs'].append(uv)
    out['receipt'] = dict(standing_body_core_clearance_m=minimum_body_clearance,
                          body_panel_samples=tested, minimum_fold_panel_margin_m=minimum_panel_margin,
                          hem_y_m=hem, waist_y_m=waist, skirt_all_around_folds=12,
                          waist_closure=dict(actual_bodice_cross_section_y_m=join_y, radial_underlap_m=.0015,
                                             construction='Closed top annulus tucked1.5mm into actual bodice; no anatomy removed'),
                          source_body_mutated=False, walking_or_seated_accepted=False,
                          skinning='All skirt vertices belong to pelvis; standing authoring only')
    return finish_edges(out, .0015), core


def apron(dress, core, rows=18, segments=96):
    """Optional separate broad front apron, following the existing skirt surface."""
    out = empty('separate_plain_apron', 'garment_outer__plain_apron')
    columns = list(range(-segments//8, segments//8+1))
    for row in range(rows-3):
        for col in columns:
            k = col % segments; base = dress['positions_m'][row*segments+k]
            r = math.hypot(base[0], base[2]); offset = .005
            out['positions_m'].append([base[0]*(1+offset/r), base[1]+.001, base[2]*(1+offset/r)])
            out['uvs'].append([(col-columns[0])/(columns[-1]-columns[0]), row/(rows-4)])
            out['weights'].append({'pelvis': 1.})
    width = len(columns)
    for row in range(rows-4):
        for k in range(width-1):
            a = row*width+k; b = a+1; c = a+width+1; d = a+width
            for face in ([a, c, b], [a, d, c]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][i] for i in face])
    return finish_edges(out, .0015)


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    # Original engineering choice near the actual source waist. This is not a
    # measurement of an1835 garment or a statement about a named resident.
    waist = bones['spine_02']['head_m'][1]
    bodice_mesh = bodice(body, bones, waist-.018)
    skirt_mesh, core = skirt(body, bones, waist, bodice_mesh)
    parts = [bodice_mesh, skirt_mesh, apron(skirt_mesh, core)]
    shoes = fitted_shoes(body, bones, 0, clearance_m=.004)
    shoes['name'] = 'closed_low_shoes'; shoes['material'] = 'footwear__plain_low_shoes'
    parts.append(shoes)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_original_female_dress_source_v1', license='CC0-1.0',
                units='m', up_axis='+Y', forward_axis='+Z', grade='reconstructed',
                body_sha256=BODY_SHA256, body_semantic_sha256=before,
                source_body_unchanged=True, skeleton=copy.deepcopy(body['skeleton']), meshes=parts,
                materials={'garment_upper__plain_dress': {'base_color_linear': [.095, .12, .15, 1], 'roughness': .9},
                           'garment_lower__plain_dress': {'base_color_linear': [.095, .12, .15, 1], 'roughness': .9},
                           'garment_outer__plain_apron': {'base_color_linear': [.46, .42, .34, 1], 'roughness': .92},
                           'footwear__plain_low_shoes': {'base_color_linear': [.045, .031, .022, 1], 'roughness': .6}},
                limitations=['Unrendered original source construction, no dated cutting pattern or historical garment image used',
                             'Colours, proportions, folds, cloth thickness and outfit combination are conjectural',
                             'No resident model assignment, skin or hair choice; underlying female body is preserved',
                             'Skirt/apron are pelvis-bound standing source; walking/seated cloth is unqualified',
                             'No canonical Blender master/export, LOD, photo, clipping-all-pose or world-placement acceptance'])


def _finish_merge(target, addition):
    """Reuse an existing material/object; preserve its original arrays exactly."""
    need(target['material'] == addition['material'], 'finishing cannot substitute material slots')
    offset = len(target['positions_m']); face_offset = len(target['triangles'])
    if 'corner_uvs' not in target:
        target['corner_uvs'] = [[list(target['uvs'][i]) for i in face] for face in target['triangles']]
    for key in ('positions_m', 'uvs', 'weights'):
        target[key].extend(copy.deepcopy(addition[key]))
    target['triangles'].extend([[i+offset for i in face] for face in addition['triangles']])
    target['corner_uvs'].extend(copy.deepcopy(addition.get('corner_uvs',
                               [[addition['uvs'][i] for i in face] for face in addition['triangles']])))
    target.setdefault('flat_face_indices', []).extend(face_offset+i for i in addition.get('flat_face_indices', []))
    target.setdefault('receipt', {}).setdefault('optional_finishing_parts', []).append({
        'name': addition['name'], 'first_vertex': offset, 'added_vertices': len(addition['positions_m']),
        'first_triangle': face_offset, 'added_triangles': len(addition['triangles']),
        'construction': copy.deepcopy(addition.get('receipt', {}))})


def _finish_cuffs(bodice_mesh, bones):
    """Small linen bands follow actual outer sleeve faces and their own skin."""
    ps = bodice_mesh['positions_m']; fs = bodice_mesh['triangles']
    skip = set(bodice_mesh.get('flat_face_indices', []))
    outer = [face for fi, face in enumerate(fs) if fi not in skip]
    used = sorted({i for face in outer for i in face}); remap = {i: j for j, i in enumerate(used)}
    compact_normals = source_shared_normals([ps[i] for i in used],
                        [[remap[i] for i in face] for face in outer], used)
    ns = dict(zip(used, compact_normals))
    wrist = abs(bones['hand_l']['head_m'][0])-.012
    result = empty('source_fitted_linen_cuffs', 'garment_outer__plain_apron')
    for side in (-1, 1):
        shell = empty('left_cuff' if side > 0 else 'right_cuff', result['material']); cache = {}
        for face in outer:
            if max(side*ps[i][0] for i in face) < wrist-.029 or min(side*ps[i][0] for i in face) > wrist-.002:
                continue
            poly = [{'p': list(ps[i]), 'uv': list(bodice_mesh['uvs'][i]), 'n': ns[i],
                     'w': bodice_mesh['weights'][i], 'basis': {i: 1.}} for i in face]
            poly = _clip(poly, lambda v: side*v['p'][0]-(wrist-.029))
            poly = _clip(poly, lambda v: (wrist-.002)-side*v['p'][0])
            ids = []
            for v in poly:
                key = tuple((i, round(w, 13)) for i, w in sorted(v['basis'].items()))
                if key not in cache:
                    cache[key] = len(shell['positions_m']); length = math.hypot(*v['n'])
                    need(length > 1e-12, 'undefined source sleeve normal')
                    shell['positions_m'].append([v['p'][a]+.0025*v['n'][a]/length for a in range(3)])
                    shell['uvs'].append(list(v['uv'])); shell['weights'].append(skin(v['w']))
                ids.append(cache[key])
            for j in range(1, len(ids)-1):
                f = [ids[0], ids[j], ids[j+1]]
                if len(set(f)) == 3:
                    shell['triangles'].append(f); shell['corner_uvs'].append([list(shell['uvs'][i]) for i in f])
        need(bool(shell['triangles']), 'empty optional cuff')
        _finish_merge(result, finish_edges(shell, .001))
    result['receipt']['scope'] = '27mm linen cuff overlays; original sleeve remains exact; source standing only'
    return result


def _finish_segments(mesh, y):
    """Actual outer triangle/plane intersections, excluding physical edge returns."""
    lines = []; skip = set(mesh.get('flat_face_indices', [])); ps = mesh['positions_m']
    for fi, face in enumerate(mesh['triangles']):
        if fi in skip: continue
        points = []
        for a, b in zip(face, face[1:]+face[:1]):
            p, q = ps[a], ps[b]
            if p[1] == y: points.append((p[0], p[2]))
            if (p[1]-y)*(q[1]-y) < 0:
                t = (y-p[1])/(q[1]-p[1]); points.append((p[0]+t*(q[0]-p[0]), p[2]+t*(q[2]-p[2])))
        points = list(dict.fromkeys(points))
        if len(points) == 2 and math.dist(*points) > 1e-12: lines.append(points)
    return lines


def _finish_radius(lines, angle):
    sx, sz = math.sin(angle), math.cos(angle); hits = []
    for (x, z), (xx, zz) in lines:
        dx, dz = xx-x, zz-z; den = sx*dz-sz*dx
        if abs(den) < 1e-14: continue
        r = (x*dz-z*dx)/den; t = (sz*x-sx*z)/den
        if r > 0 and -1e-10 <= t <= 1+1e-10: hits.append(r)
    need(bool(hits), 'optional waist/tie has no actual garment support')
    return max(hits)


def _finish_waist(parts, bones):
    waist = bones['spine_02']['head_m'][1]; segments = 96
    out = empty('linen_waistband_and_back_ties', 'garment_outer__plain_apron')
    # Sampling every layer prevents the belt from cutting through an apron fold.
    for row, y in enumerate((waist-.010, waist+.015)):
        lines = [line for mesh in parts[:3] for line in _finish_segments(mesh, y)]
        for k in range(segments):
            a = 2*math.pi*k/segments; r = _finish_radius(lines, a)+.0035
            out['positions_m'].append([r*math.sin(a), y, r*math.cos(a)])
            out['uvs'].append([k/segments, float(row)]); out['weights'].append({'pelvis': 1.})
    for k in range(segments):
        n = (k+1)%segments; a,b,c,d = k,n,segments+n,segments+k
        for f, uv in (([a,b,c],[[k/segments,0],[(k+1)/segments,0],[(k+1)/segments,1]]),
                      ([a,c,d],[[k/segments,0],[(k+1)/segments,1],[k/segments,1]])):
            out['triangles'].append(f); out['corner_uvs'].append(uv)
    out = finish_edges(out, .001)
    for side in (-1,1):
        tie = empty('back_tie_left' if side < 0 else 'back_tie_right', out['material'])
        for row in range(9):
            t = row/8; y = waist+.006-.15*t; lines = _finish_segments(parts[1], y)
            for col in range(2):
                a = math.pi+side*(.025+.15*t)+(col-.5)*.115
                r = _finish_radius(lines, a)+.006+.002*math.sin(math.pi*t)
                tie['positions_m'].append([r*math.sin(a), y, r*math.cos(a)])
                tie['uvs'].append([float(col), t]); tie['weights'].append({'pelvis': 1.})
        for row in range(8):
            a,b,c,d = 2*row,2*row+1,2*row+3,2*row+2
            for f in ([a,c,b],[a,d,c]):
                tie['triangles'].append(f); tie['corner_uvs'].append([tie['uvs'][i] for i in f])
        _finish_merge(out, finish_edges(tie, .001))
    out['receipt']['scope'] = '25mm actual-garment fitted waistband and two simple back ties; conjectural cut/width'
    return out


def _finish_closure(bodice_mesh, bones):
    from human_period_wardrobe import _front_sample
    out = empty('self_cloth_front_closure', bodice_mesh['material'])
    low = bones['spine_02']['head_m'][1]+.025
    high = bones['neck_01']['head_m'][1]-.040
    for row in range(17):
        y = low+(high-low)*row/16
        for col in range(3):
            x = (col-1)*.007; z,w = _front_sample(bodice_mesh,x,y)
            out['positions_m'].append([x,y,z+.0025]);out['uvs'].append([col/2,row/16]);out['weights'].append(w)
    for row in range(16):
        for col in range(2):
            a=row*3+col;b=a+1;c=a+4;d=a+3
            for f in ([a,b,c],[a,c,d]):
                out['triangles'].append(f);out['corner_uvs'].append([out['uvs'][i] for i in f])
    out=finish_edges(out,.001)
    # Closed low-profile self-cloth buttons, not metallic circles or new slots.
    buttons=empty('six_covered_buttons',out['material']);segments=12
    for button in range(6):
        x=.001;y=low+.018+(high-low-.036)*button/5;z,w=_front_sample(bodice_mesh,x,y);start=len(buttons['positions_m'])
        for row,(depth,radius) in enumerate(((.0035,.003),(.005,.0035),(.006,.0028))):
            for k in range(segments):
                a=2*math.pi*k/segments
                buttons['positions_m'].append([x+radius*math.cos(a),y+radius*math.sin(a),z+depth])
                buttons['uvs'].append([k/segments,row/2]);buttons['weights'].append(dict(w))
        for row in range(2):
            for k in range(segments):
                n=(k+1)%segments;a=start+row*segments+k;b=start+row*segments+n;c=b+segments;d=a+segments
                for f,uv in (([a,b,c],[[k/segments,row/2],[(k+1)/segments,row/2],[(k+1)/segments,(row+1)/2]]),
                             ([a,c,d],[[k/segments,row/2],[(k+1)/segments,(row+1)/2],[k/segments,(row+1)/2]])):
                    buttons['triangles'].append(f);buttons['corner_uvs'].append(uv)
        for row in (0,2):
            center=len(buttons['positions_m']);depth=(.0035,.005,.006)[row]
            buttons['positions_m'].append([x,y,z+depth]);buttons['uvs'].append([.5,.5]);buttons['weights'].append(dict(w))
            for k in range(segments):
                n=(k+1)%segments;f=[center,start+row*segments+k,start+row*segments+n]
                if row==0:f.reverse()
                uv=[[.5,.5] if i==center else [.5+.45*math.cos(2*math.pi*((i-start)%segments)/segments),.5+.45*math.sin(2*math.pi*((i-start)%segments)/segments)] for i in f]
                buttons['triangles'].append(f);buttons['corner_uvs'].append(uv)
    _finish_merge(out,buttons)
    out['receipt']['scope']='14mm front placket and six 7mm self-covered buttons sampled from actual bodice; reconstructed fastening only'
    return out


def _finish_bonnet(hair, body):
    """Original pale bonnet family silhouette, fitted around unchanged actual hair.

    Cleared Wild1835 supplies only tiny head-covering/full-skirt analogues. This
    crown/brim is a new conjectural construction, never traced/measured evidence.
    """
    head_y=next(b['head_m'][1] for b in body['skeleton'] if b['name']=='head')
    fitting_points=list(hair['positions_m'])
    for mesh in body['meshes']:
        for p,w in zip(mesh['positions_m'],mesh['weights']):
            if sum(w.get(b,0.) for b in ('head','jaw'))>.75 and p[1]>=head_y-.060 and (p[2]<.035 or p[1]>head_y+.050 or abs(p[0])>.055):
                fitting_points.append(p)
    points=fitting_points;center=[(min(p[a] for p in points)+max(p[a] for p in points))/2 for a in range(3)]
    radii=[(max(p[a] for p in points)-min(p[a] for p in points))/2+.012 for a in range(3)]
    support=max(math.sqrt(sum(((p[a]-center[a])/radii[a])**2 for a in range(3))) for p in points)
    radii=[r*max(1.,support)*1.025 for r in radii]
    out=empty('plain_linen_bonnet','headwear__linen_bonnet');segments=64;rows=14;theta0=1.25
    def vertex(p,uv):
        i=len(out['positions_m']);out['positions_m'].append(p);out['uvs'].append(uv);out['weights'].append({'head':1.});return i
    def face(f,uv=None,front=False):
        a,b,c=[out['positions_m'][i] for i in f];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        direction=[0,0,1] if front else [sum(out['positions_m'][i][j]-center[j] for i in f) for j in range(3)]
        uv=copy.deepcopy(uv or [out['uvs'][i] for i in f])
        if sum(a*b for a,b in zip(normal,direction))<0:f=list(reversed(f));uv.reverse()
        out['triangles'].append(f);out['corner_uvs'].append(uv)
    for row in range(rows):
        theta=theta0+(math.pi-.11-theta0)*row/(rows-1)
        for k in range(segments):
            phi=2*math.pi*k/segments
            vertex([center[0]+radii[0]*math.sin(theta)*math.sin(phi),center[1]+radii[1]*math.sin(theta)*math.cos(phi),center[2]+radii[2]*math.cos(theta)],[k/segments,row/rows])
    for row in range(rows-1):
        for k in range(segments):
            n=(k+1)%segments;a=row*segments+k;b=row*segments+n;c=b+segments;d=a+segments
            face([a,b,c],[[k/segments,row/rows],[(k+1)/segments,row/rows],[(k+1)/segments,(row+1)/rows]])
            face([a,c,d],[[k/segments,row/rows],[(k+1)/segments,(row+1)/rows],[k/segments,(row+1)/rows]])
    pole=vertex([center[0],center[1],center[2]-radii[2]],[.5,1])
    for k in range(segments):
        face([(rows-1)*segments+k,(rows-1)*segments+(k+1)%segments,pole],[[k/segments,(rows-1)/rows],[(k+1)/segments,(rows-1)/rows],[(k+.5)/segments,1]])
    # Open front brim covers upper/side hair while leaving the face/chin open.
    start=len(out['positions_m']);columns=49
    for row in range(4):
        t=row/3
        for col in range(columns):
            phi=-2.13+4.26*col/(columns-1)
            x=center[0]+radii[0]*math.sin(theta0)*math.sin(phi)*(1+.13*t)
            y=center[1]+radii[1]*math.sin(theta0)*math.cos(phi)*(1+.04*t)
            z=center[2]+radii[2]*math.cos(theta0)+t*(.045+.010*max(0.,math.cos(phi)))
            vertex([x,y,z],[col/(columns-1),t])
    for row in range(3):
        for col in range(columns-1):
            a=start+row*columns+col;b=a+1;c=b+columns;d=a+columns
            face([a,b,c],front=True);face([a,c,d],front=True)
    out=finish_edges(out,.001)
    out['receipt']['construction']='Hair-bounded original bonnet crown and open upper/side brim, no traced source pattern; head-bound standing prototype'
    out['receipt']['hair_envelope']={'center_m':center,'radii_m':radii,'maximum_hair_ellipsoid_norm':max(math.sqrt(sum(((p[a]-center[a])/radii[a])**2 for a in range(3))) for p in hair['positions_m']),'hair_vertices_unchanged':True}
    return out


def apply_dress_finishing(bundle, body, hair):
    """Explicit v1 option; absent option preserves the original construction."""
    need(bundle['body_semantic_sha256']==digest(body),'finishing body/source mismatch')
    before_body=digest(body);before_hair=digest(hair);before_bundle=copy.deepcopy(bundle)
    out=copy.deepcopy(bundle);bones={b['name']:b for b in body['skeleton']}
    cuffs=_finish_cuffs(out['meshes'][0],bones)
    waist=_finish_waist(out['meshes'],bones)
    closure=_finish_closure(out['meshes'][0],bones)
    _finish_merge(out['meshes'][2],cuffs);_finish_merge(out['meshes'][2],waist);_finish_merge(out['meshes'][0],closure)
    bonnet=_finish_bonnet(hair,body);out['meshes'].append(bonnet)
    out['materials'][bonnet['material']]={'base_color_linear':[.72,.68,.58,1],'roughness':.92}
    for old,new in zip(before_bundle['meshes'],out['meshes']):
        for key in ('positions_m','triangles','uvs','weights'):
            need(new[key][:len(old[key])]==old[key], 'finishing changed original garment '+key)
        if 'corner_uvs' in old:need(new['corner_uvs'][:len(old['triangles'])]==old['corner_uvs'],'finishing changed original corner UVs')
    need(digest(body)==before_body and digest(hair)==before_hair,'finishing changed original body/hair')
    out['optional_finishing']={'version':1,'source':'wild_1835_third_vine','grade':'reconstructed',
        'scope':'Conjectural bonnet family silhouette, linen cuffs/waistband/back ties, self-cloth closure; actual source body/rig/hair retained',
        'new_material_slots':1,'source_body_unchanged':True,'source_hair_unchanged':True,
        'standing_source_only':True,'production_eligible':False,'walking_seated_or_photo_accepted':False}
    out['limitations'].append('Optional finishing is an unrendered reconstructed standing-source proposal; no dated bonnet/cut/colour or personal possession is asserted')
    return out


def prepare_dress_assembly(root, recipe, variant, body):
    """The opt-in canonical builder's actual source consumer; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('dress_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_dress_components.py',
         'unsupported dress component generator')
    need(recipe.get('scene_date') == '1835-07-01' and recipe.get('grade') == 'reconstructed',
         'dress study scene/appearance grade changed')
    need(spec.get('standing_source_only') is True and spec.get('production_eligible') is False
         and spec.get('walking_seated_or_photo_accepted') is False, 'unqualified dress production or pose promotion')
    need(variant.get('component_assembly') == 'adult_dress_v1'
         and variant.get('person_reference_id') == 'rc_flynn_mary'
         and variant.get('person_reference_grade') == 'reconstructed'
         and variant.get('recipe_path') == 'data/humans/recipes/adult_dress_1835.json'
         and variant.get('person_reference_record') == 'data/residents/households/hh_rc_flynn_mary.json',
         'dress study must retain the existing reconstructed Mary Flynn reference')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe dress body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'dress body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed dress body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed dress anatomy or source rights')
    liberty = 'L-human-modular-dress-1789'
    need(spec.get('liberty') == liberty and ('### '+liberty+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'dress components require the actual declared liberty')
    source_id = 'wild_1835_third_vine'
    need(recipe.get('sources') == [source_id], 'unexpected dress reference substitution')
    record = json.loads((root/'data/sources'/f'{source_id}.json').read_text())
    need(record.get('id') == source_id and record.get('rights_status') == 'public_domain'
         and record.get('asset_use') == 'cross_check', 'dress reference is not the cleared bounded cross-check')
    finishing = spec.get('finishing_version')
    need(finishing is None or (type(finishing) is int and finishing == 1), 'unsupported dress finishing version')
    bundle = construct(body)
    if finishing == 1:
        from human_hair_short04 import fit
        hair, _, _ = fit(body, recipe['hair_component'], root)
        bundle = apply_dress_finishing(bundle, body, hair)
    for material, spec in bundle['materials'].items():
        need(recipe['colors_linear_rgba'].get(material) == spec['base_color_linear'], 'dress material recipe/source disagree')
    names = {b['name'] for b in body['skeleton']}
    for mesh in bundle['meshes']:
        count = len(mesh['positions_m'])
        need(count > 0 and count == len(mesh['weights']) == len(mesh['uvs']), 'incomplete canonical dress arrays')
        for mapping in mesh['weights']:
            need(1 <= len(mapping) <= 4 and not(set(mapping)-names)
                 and all(math.isfinite(w) and w >= 0 for w in mapping.values())
                 and abs(math.fsum(mapping.values())-1.) < 1e-10, 'invalid canonical dress skin')
        for face in mesh['triangles']:
            need(len(face) == len(set(face)) == 3 and all(type(i) is int and 0 <= i < count for i in face),
                 'invalid canonical dress triangle')
    return bundle


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed female body source')
    need(not a.output.exists(), 'fresh output required; retain earlier authoring candidates')
    data = construct(json.loads(raw)); a.output.write_text(json.dumps(data, separators=(',', ':'))+'\n')
    print(json.dumps({'output': str(a.output), 'sha256': hashlib.sha256(a.output.read_bytes()).hexdigest(),
                      'meshes': [{'name': m['name'], 'vertices': len(m['positions_m']), 'triangles': len(m['triangles'])} for m in data['meshes']],
                      'source_body_unchanged': data['source_body_unchanged'], 'acceptance': 'SOURCE_ONLY_UNRENDERED'}))
