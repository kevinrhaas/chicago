# SPDX-License-Identifier: GPL-3.0-or-later
"""Reconstructed seat ease for the 1812 settler's loose linen trousers.

The original shell follows the anatomical cleft. A posterior convex section
bridges that hollow rather than making the body or every garment larger. Only
positions change; topology, UVs and skin weights remain those of the canonical
trouser builder. This source construction is not a posed-clearance certificate.
"""
from __future__ import annotations

import copy
import math


def _smooth(value):
    value = max(0., min(1., value))
    return value*value*(3.-2.*value)


def _rear_hull(mesh, y):
    """Upper hull in (x, -z) of actual triangle/section intersections."""
    points = set()
    ps = mesh['positions_m']
    for face in mesh['triangles']:
        tri = [ps[i] for i in face]
        if y < min(p[1] for p in tri) or y > max(p[1] for p in tri):
            continue
        for a, b in zip(tri, tri[1:]+tri[:1]):
            if abs(a[1]-y) <= 1e-12:
                points.add((a[0], -a[2]))
            if (a[1] < y < b[1]) or (b[1] < y < a[1]):
                t = (y-a[1])/(b[1]-a[1])
                points.add((a[0]+t*(b[0]-a[0]), -(a[2]+t*(b[2]-a[2]))))
    top = {}
    for x, rear in points:
        top[x] = max(top.get(x, -math.inf), rear)
    hull = []
    for p in sorted(top.items()):
        while len(hull) >= 2:
            a, b = hull[-2:]
            cross = (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
            if cross < -1e-14:
                break
            hull.pop()
        hull.append(p)
    if len(hull) < 2:
        raise ValueError('trouser seat section has no horizontal span')
    return hull


def _rear_at(hull, x):
    if not hull[0][0]-1e-12 <= x <= hull[-1][0]+1e-12:
        raise ValueError('seat point outside actual section support')
    for a, b in zip(hull, hull[1:]):
        if x <= b[0]+1e-12:
            t = max(0., min(1., (x-a[0])/(b[0]-a[0])))
            return a[1]+t*(b[1]-a[1])
    return hull[-1][1]


def linen_seat_ease(mesh, bones, height, waist_fraction, spec):
    """Apply the recipe's bounded posterior ease without changing other dress.

    Every support is sampled from the original trousers, not from progressively
    moved vertices. Smooth fades preserve the waistband, lower legs, front and
    outside hips. The new cut and its dimensions are reconstructed choices.
    """
    expected = {'id', 'extra_rear_ease_m', 'half_width_m', 'full_half_width_m',
                'lower_below_pelvis_m', 'lower_full_below_pelvis_m',
                'upper_below_waist_m', 'upper_full_below_waist_m',
                'rear_transition_m', 'section_rows'}
    if set(spec) != expected or spec['id'] != 'settler_linen_seat_ease_v1':
        raise ValueError('unsupported linen seat pattern')
    dims = [v for k, v in spec.items() if k not in ('id', 'section_rows')]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in dims):
        raise ValueError('invalid linen seat dimensions')
    count = spec['section_rows']
    if type(count) is not int or not 3 <= count <= 65:
        raise ValueError('invalid linen seat section count')
    if not (0 < spec['full_half_width_m'] < spec['half_width_m'] < .25
            and spec['extra_rear_ease_m'] < .04):
        raise ValueError('invalid linen seat ease/width')
    pelvis = bones['pelvis']['head_m']
    waist = height*waist_fraction
    lo = pelvis[1]-spec['lower_below_pelvis_m']
    full_lo = pelvis[1]-spec['lower_full_below_pelvis_m']
    full_hi = waist-spec['upper_full_below_waist_m']
    hi = waist-spec['upper_below_waist_m']
    if not 0 < lo < full_lo < full_hi < hi < waist:
        raise ValueError('linen seat landmarks do not form a supported interval')
    levels = [lo+(hi-lo)*i/(count-1) for i in range(count)]
    hulls = [_rear_hull(mesh, y) for y in levels]
    out = copy.deepcopy(mesh)
    moved = 0
    maximum = 0.
    for p in out['positions_m']:
        x, y, z = p
        side = 1.-_smooth((abs(x)-spec['full_half_width_m']) /
                          (spec['half_width_m']-spec['full_half_width_m']))
        vertical = _smooth((y-lo)/(full_lo-lo))*_smooth((hi-y)/(hi-full_hi))
        rear = _smooth((pelvis[2]-z)/spec['rear_transition_m'])
        gain = side*vertical*rear
        if gain <= 0:
            continue
        index = min(count-2, max(0, int((y-lo)/(hi-lo)*(count-1))))
        t = (y-levels[index])/(levels[index+1]-levels[index])
        support = ((1.-t)*_rear_at(hulls[index], x)
                   + t*_rear_at(hulls[index+1], x))
        delta = gain*max(0., support+spec['extra_rear_ease_m']+z)
        if delta > 0:
            p[2] -= delta
            moved += 1
            maximum = max(maximum, delta)
    out.pop('_normals', None)
    out.setdefault('receipt', {})['linen_seat_ease'] = {
        'pattern': copy.deepcopy(spec), 'section_y_m': levels,
        'changed_vertices': moved, 'maximum_posterior_shift_m': maximum,
        'source_body_changed': False, 'topology_uvs_skin_weights_changed': False,
        'native_lod_and_posed_clearance_accepted': False,
        'scope': 'Reconstructed source cut; canonical bake, all LODs and movement/visual review remain pending',
    }
    return out
