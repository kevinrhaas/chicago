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


def bodice(body, bones, waist, ease=.010, collar=0.):
    """Closed long-sleeve source-fitted bodice with linear neck/waist/cuff cuts.

    `collar` raises the neck cut up the neck by that many metres (a 1904 shirtwaist's
    standing collar, T-3423); what lies above the neck bone's head follows the neck."""
    out = empty('plain_closed_bodice', 'garment_upper__plain_dress')
    source = body['meshes'][0]
    positions = source['positions_m']
    normals = source_shared_normals(positions, source['triangles'], source['source_vertex_indices'])
    neck_base = bones['neck_01']['head_m'][1]
    neck = neck_base+collar
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
            if v['p'][1] >= neck_base-1e-12:
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
                          collar_m=collar,
                          construction='Long sleeves and closed torso; reconstructed cut, no historical personal outfit')
    return out


def leg_follow(bones, waist):
    """T-3423: skirt skinning that lets the cloth go with the legs (walking, sitting).

    A pelvis-only skirt is a rigid bell: a stepping or seated thigh passes straight
    through it. Below the waist each skirt point is shared between the pelvis and the
    leg on its side (thigh above the knee, calf below it), more over the front than the
    back, so a forward thigh carries the front of the skirt over it and the hem below
    the knee hangs from the calf. Points between the legs split evenly between them.
    An original engineering blend, not a measured cloth simulation.
    """
    knee = bones['calf_l']['head_m'][1]; half = abs(bones['thigh_l']['head_m'][0])
    def weights(p):
        t = min(1., max(0., (waist-p[1])/(.4*(waist-knee))))
        t = t*(2-t)
        r = math.hypot(p[0], p[2]) or 1.
        front = p[2]/r
        a = t*(.5+.5*max(0., front))
        u = min(1., max(0., (knee+.06-p[1])/.2))
        left = min(1., max(0., .5+p[0]/(2.2*half)))
        w = {'pelvis': 1-a}
        for side, share in (('l', left), ('r', 1-left)):
            for bone, part in ((f'thigh_{side}', 1-u), (f'calf_{side}', u)):
                if a*share*part > 1e-6: w[bone] = w.get(bone, 0.)+a*share*part
        w = dict(sorted(w.items(), key=lambda kv: -kv[1])[:4])
        total = math.fsum(w.values())
        return {k: v/total for k, v in w.items()}
    return weights


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
    follow = leg_follow(bones, waist)
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
            out['weights'].append(follow([factor*x, y, factor*z]))
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
                          skinning='Pelvis at the waist, shared with the thigh and calf of each side below it (leg_follow, T-3423)')
    return finish_edges(out, .0015), core


def apron(dress, core, rows=18, segments=96):
    """Optional separate broad front apron, following the existing skirt surface."""
    out = empty('separate_plain_apron', 'garment_outer__plain_apron')
    columns = list(range(-segments//8, segments//8+1))
    for row in range(rows-3):
        for col in columns:
            k = col % segments; base = dress['positions_m'][row*segments+k]
            r = math.hypot(base[0], base[2]); offset = .008
            out['positions_m'].append([base[0]*(1+offset/r), base[1]+.001, base[2]*(1+offset/r)])
            out['uvs'].append([(col-columns[0])/(columns[-1]-columns[0]), row/(rows-4)])
            out['weights'].append(dict(dress['weights'][row*segments+k]))
    width = len(columns)
    for row in range(rows-4):
        for k in range(width-1):
            a = row*width+k; b = a+1; c = a+width+1; d = a+width
            for face in ([a, c, b], [a, d, c]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][i] for i in face])
    return finish_edges(out, .0015)


def collar_band(upper, bones, below=.010, lift=.0018):
    """T-3423: a 1904 shirtwaist's white standing collar: the bodice's own triangles above
    `below` over the neck bone's head, copied a little out from the neck's axis, skinned as
    the bodice is there. A reconstructed construction, not a measured collar."""
    out = empty('standing_collar', 'garment_outer__plain_apron')
    P = upper['positions_m']; base = bones['neck_01']['head_m']
    keep = [f for f in upper['triangles'] if min(P[i][1] for i in f) >= base[1]+below]
    need(bool(keep), 'no bodice above the collar line')
    index = {}
    for f, corner in zip(upper['triangles'], upper['corner_uvs']):
        if f not in keep:
            continue
        ids = []
        for i in f:
            if i not in index:
                p = P[i]; dx, dz = p[0]-base[0], p[2]-base[2]; r = math.hypot(dx, dz)
                need(r > .01, 'collar point on the neck axis')
                index[i] = len(out['positions_m'])
                out['positions_m'].append([p[0]+lift*dx/r, p[1], p[2]+lift*dz/r])
                out['uvs'].append(list(upper['uvs'][i])); out['weights'].append(dict(upper['weights'][i]))
            ids.append(index[i])
        out['triangles'].append(ids); out['corner_uvs'].append([list(c) for c in corner])
    out = finish_edges(out, .0012)
    out['receipt'] = dict(collar_from_y_m=base[1]+below, lift_m=lift, triangles=len(keep), basis='reconstructed')
    return out


def bib(upper, bones, waist, top=.215, half_width=(.118, .098), rows=15, cols=15, offset=.007):
    """T-3423: the bib of a 1904 apron, laid over the actual bodice front.

    A grid from just under the skirt's waist to `top` above the bodice's waist, narrowing from the bottom
    half-width to the top one, each point dropped onto the front-most bodice triangle
    along the body's depth axis and stood `offset` off it. Each point takes the skin of
    the bodice point under it, so the bib bends with the torso. Shape and size are
    reconstructed from the 1903 Wasson stereographs' bib aprons, not measured."""
    out = empty('apron_bib', 'garment_outer__plain_apron')
    P = upper['positions_m']; W = upper['weights']
    tris = [f for f in upper['triangles']
            if max(P[i][1] for i in f) >= waist-.02 and min(P[i][1] for i in f) <= waist+top+.01
            and min(P[i][2] for i in f) > bones['spine_02']['head_m'][2]]
    def drop(x, y):
        best = None
        for f in tris:
            a, b, c = (P[i] for i in f)
            d = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(d) < 1e-14:
                continue
            l0 = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/d
            l1 = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/d
            l2 = 1-l0-l1
            if min(l0, l1, l2) < -1e-9:
                continue
            z = l0*a[2]+l1*b[2]+l2*c[2]
            if best is None or z > best[0]:
                best = (z, f, (l0, l1, l2))
        need(best is not None, 'apron bib point finds no bodice front')
        z, f, ls = best
        mix = collections.Counter()
        for i, l in zip(f, ls):
            for bone, w in W[i].items():
                mix[bone] += max(0., l)*w
        return z, skin(dict(mix))
    bottom = waist+.012   # just under the skirt's waist, so the apron's skirt overlaps it
    for r in range(rows):
        t = r/(rows-1); y = bottom+(waist+top-bottom)*t
        hw = half_width[0]+(half_width[1]-half_width[0])*t
        for k in range(cols):
            u = k/(cols-1); x = -hw+2*hw*u
            z, w = drop(x, y)
            out['positions_m'].append([x, y, z+offset]); out['uvs'].append([u, t]); out['weights'].append(w)
    for r in range(rows-1):
        for k in range(cols-1):
            a = r*cols+k; b = a+1; c = a+cols+1; d = a+cols
            for face in ([a, b, c], [a, c, d]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][i] for i in face])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(bib_bottom_y_m=bottom, bib_top_y_m=waist+top, half_width_m=list(half_width),
                          offset_m=offset, skinning='bodice point beneath', basis='reconstructed')
    return out


def hair_bun(hair, bones, rings=10, segments=20, up=.05, half_axes=(.044, .040, .030)):
    """T-3423: a gathered bun at the back of the head, over the fitted short04 cap.

    Women of 1835 and 1904 wore their hair up; the cleared short04 cap alone reads as a
    man's crop. The bun is an original ellipsoid (4.4 x 4.0 x 3.0 cm half-axes) seated
    on the back of the cap a little above the ears and skinned to the head. It wears the
    same cleared hair atlas through a 2 % window centred on the texture coordinate of the
    cap vertex it sits on (opaque throughout in the padded atlas), mirrored six times round
    and four times over so strand detail stays at the cap's scale. Size and placement are reconstructed, not measured.
    """
    P, U = hair['positions_m'], hair['uvs']
    head = bones['head']['head_m']
    y0 = head[1]+up
    band = [p for p in P if abs(p[1]-y0) < .015 and abs(p[0]) < .03]
    need(bool(band), 'no back-of-head hair at the bun height')
    back = min(p[2] for p in band)
    rx, ry, rz = half_axes
    c = [0., y0, back-.45*rz]
    out = empty('gathered_bun', 'hair__makehuman_short04')
    seat = min((j for j, p in enumerate(P) if abs(p[1]-y0) < .015 and abs(p[0]) < .03), key=lambda j: P[j][2])
    u0, v0 = U[seat]
    window = .02
    tri = lambda x: 1-abs(2*(x % 1)-1)  # mirrored repeats: strand detail without leaving the window
    def vertex(th, ph):
        ridge = 1+.06*math.cos(5*ph+3*th)  # gentle twist ridges, not a smooth egg
        x = c[0]+rx*ridge*math.sin(th)*math.cos(ph)
        y = c[1]+ry*math.cos(th)
        z = c[2]-rz*ridge*math.sin(th)*math.sin(ph)
        out['positions_m'].append([x, y, z]); out['uvs'].append([u0+window*(tri(6*ph/(2*math.pi))-.5), v0+window*(tri(4*th/math.pi)-.5)])
        out['weights'].append({'head': 1.})
        return len(out['positions_m'])-1
    top = vertex(0., 0.)
    grid = [[vertex(math.pi*i/rings, 2*math.pi*k/segments) for k in range(segments)] for i in range(1, rings)]
    bottom = vertex(math.pi, 0.)
    faces = []
    for k in range(segments):
        n = (k+1) % segments
        faces.append([top, grid[0][n], grid[0][k]])
        faces.append([bottom, grid[-1][k], grid[-1][n]])
    for i in range(rings-2):
        for k in range(segments):
            n = (k+1) % segments
            faces += [[grid[i][k], grid[i][n], grid[i+1][n]], [grid[i][k], grid[i+1][n], grid[i+1][k]]]
    for f in faces:
        out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][v] for v in f])
    out['receipt'] = dict(centre_m=c, half_axes_m=[rx, ry, rz], back_of_cap_z_m=back, uv_window=[u0, v0, window], weights='head', basis='reconstructed')
    return out


# The two outfits (T-3423). 1835: a plain dark dress and a tan apron. 1904: a working
# woman's pale shirtwaist with a standing collar, a dark skirt and a white bib apron, as
# the 1903 Wasson stereographs show cooks and maids; colours are reconstructed (the
# photographs are monochrome). The bun sits higher in 1904, where hair was drawn up.
OUTFITS = {
    '1835': dict(collar=0., ease=.010, bib=False, bun=dict(up=.05, half_axes=(.044, .040, .030)),
                 materials={'garment_upper__plain_dress': {'base_color_linear': [.095, .12, .15, 1], 'roughness': .9},
                            'garment_lower__plain_dress': {'base_color_linear': [.095, .12, .15, 1], 'roughness': .9},
                            'garment_outer__plain_apron': {'base_color_linear': [.46, .42, .34, 1], 'roughness': .92},
                            'footwear__plain_low_shoes': {'base_color_linear': [.045, .031, .022, 1], 'roughness': .6}}),
    '1904': dict(collar=.032, ease=.016, bib=True, bun=dict(up=.10, half_axes=(.040, .030, .032)),
                 materials={'garment_upper__plain_dress': {'base_color_linear': [.56, .59, .64, 1], 'roughness': .85},
                            'garment_lower__plain_dress': {'base_color_linear': [.028, .030, .036, 1], 'roughness': .9},
                            'garment_outer__plain_apron': {'base_color_linear': [.72, .71, .67, 1], 'roughness': .88},
                            'footwear__plain_low_shoes': {'base_color_linear': [.02, .018, .016, 1], 'roughness': .5}}),
}


def construct(body, outfit='1835'):
    need(outfit in OUTFITS, f'unknown dress outfit {outfit!r}')
    look = OUTFITS[outfit]
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    # Original engineering choice near the actual source waist. This is not a
    # measurement of an1835 garment or a statement about a named resident.
    waist = bones['spine_02']['head_m'][1]
    bodice_mesh = bodice(body, bones, waist-.018, ease=look['ease'], collar=look['collar'])
    skirt_mesh, core = skirt(body, bones, waist, bodice_mesh)
    parts = [bodice_mesh, skirt_mesh, apron(skirt_mesh, core)]
    if look['bib']:
        parts.append(bib(bodice_mesh, bones, waist-.018))
    if look['collar']:
        parts.append(collar_band(bodice_mesh, bones))
    shoes = fitted_shoes(body, bones, 0, clearance_m=.004)
    shoes['name'] = 'closed_low_shoes'; shoes['material'] = 'footwear__plain_low_shoes'
    parts.append(shoes)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_original_female_dress_source_v1', license='CC0-1.0',
                units='m', up_axis='+Y', forward_axis='+Z', grade='reconstructed',
                body_sha256=BODY_SHA256, body_semantic_sha256=before,
                source_body_unchanged=True, skeleton=copy.deepcopy(body['skeleton']), meshes=parts,
                outfit=outfit, bun=dict(look['bun']),
                materials=copy.deepcopy(look['materials']),
                limitations=['Unrendered original source construction, no dated cutting pattern or historical garment image used',
                             'Colours, proportions, folds, cloth thickness and outfit combination are conjectural',
                             'No resident model assignment, skin or hair choice; underlying female body is preserved',
                             'Skirt/apron share pelvis and leg weights (T-3423); no cloth simulation, walking/seated fit judged by eye',
                             'No canonical Blender master/export, LOD, photo, clipping-all-pose or world-placement acceptance'])


# The dress studies the builder may make, each bound to its recipe, scene, person and
# reference pictures (T-3423 added the 1904 one).
DRESS_STUDIES = {
    'data/humans/recipes/adult_dress_1835.json': dict(
        outfit='1835', scene_date='1835-07-01', person='rc_flynn_mary', grade='reconstructed',
        record='data/residents/households/hh_rc_flynn_mary.json', sources=['wild_1835_third_vine'],
        rights=('public_domain',)),
    'data/humans/recipes/adult_dress_1904.json': dict(
        outfit='1904', scene_date='1904-07-01', person='glessner_williamson_martha_l', grade='attested',
        record='data/residents_1904/households/hh_glessner_john_j.json',
        sources=['loc_wasson_1903_charming_rogue_new_cook_stereograph', 'loc_wasson_1903_new_french_cook_mr_mrs_stereograph',
                 'loc_wasson_1903_new_french_cook_stereograph'],
        rights=('public_domain', 'no_known_restrictions')),
}


def prepare_dress_assembly(root, recipe, variant, body):
    """The opt-in canonical builder's actual source consumer; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('dress_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_dress_components.py',
         'unsupported dress component generator')
    study = DRESS_STUDIES.get(variant.get('recipe_path'))
    need(study is not None, 'dress study recipe is not one of the bound studies')
    need(spec.get('outfit', '1835') == study['outfit'], 'dress study outfit differs from its recipe binding')
    need(recipe.get('scene_date') == study['scene_date'] and recipe.get('grade') == 'reconstructed',
         'dress study scene/appearance grade changed')
    need(spec.get('standing_source_only') is True and spec.get('production_eligible') is False
         and spec.get('walking_seated_or_photo_accepted') is False, 'unqualified dress production or pose promotion')
    need(variant.get('component_assembly') == 'adult_dress_v1'
         and variant.get('person_reference_id') == study['person']
         and variant.get('person_reference_grade') == study['grade']
         and variant.get('person_reference_record') == study['record'],
         'dress study must retain its bound person reference')
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
    need(recipe.get('sources') == study['sources'], 'unexpected dress reference substitution')
    for source_id in study['sources']:
        record = json.loads((root/'data/sources'/f'{source_id}.json').read_text())
        need(record.get('id') == source_id and record.get('rights_status') in study['rights']
             and record.get('asset_use') == 'cross_check', 'dress reference is not a cleared bounded cross-check')
    bundle = construct(body, study['outfit'])
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
