# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 cook's working dress on the shared portable female rig (T-3479).

First worn by Kate Ryan, cook in the Glessner household at 1800 Prairie Avenue in the 1900
census (born April 1850 in Ireland, so 54 in 1904). The pieces, read from the period pictures
in the recipe (data/humans/recipes/cook_1904.json):

  dress        a dark print cotton work dress: a plain bodice, full in front, with a narrow
               band at the neck and long sleeves pushed up to the forearm and rolled there,
               over a full gathered skirt to the floor (the older cook at the kitchen table,
               Wasson, 1903; the Irish cook "Bridget" in her figured print, Underwood, 1901)
  apron        a broad checked apron: a skirt wrapping round past the hips nearly to the hem,
               a square bib pinned on the bodice front without straps, a waistband, and its
               ties knotted behind (the checked bib apron of the 1903 cook; the 1901 cook's
               checked apron round her skirt)
  head cloth   a dark cloth bound over the drawn-up hair, covering the crown and the knot
               (the 1903 cook). A separate mesh rigidly on the head bone
               (material `headwear__cook_head_cloth`).

Generated geometry is CC0-1.0. The bodice, skirt and bib are the dress components of T-3423
(tools/human_dress_components.py), re-cut and re-coloured here; the rolled sleeves, the
waistband, the ties and the head cloth are drawn here. Amounts and every colour are
reconstructed (the pictures are monochrome); liberty L-human-modular-dress-1789 with its T-3479
supplement. The source anatomy is never changed: the forearms the rolled sleeves leave bare
are the body's own.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_cook_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import (need, digest, empty, bodice, blouse, skirt as gathered_skirt, bib, collar_band)
from human_period_wardrobe import finish_edges
from human_workwear_fit import _clip
from human_maid_1904 import _two_sided

BODY_SHA256 = '3060ee86957ff7c2d70c89e70fe95ff3bc2294a0d7f6a5716b5a2f3f8dd84c72'
ASSEMBLY = 'cook_1904_v1'
RECIPE = 'data/humans/recipes/cook_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    bodice=dict(ease=.018, collar=.012, waist_below_spine02=.02, pouch=.016, sleeve=.012),
    neckband=dict(below=.010, lift=.0022),
    sleeves=dict(end_past_elbow=.085, roll_width=.05, roll_lift=.0075, sectors=24, rows=9),
    skirt=dict(hem_y=.042, ease=.02, segments=96, rows=18),
    apron=dict(columns_each_side=27, last_row_from_hem=2, offset=.009),
    bib=dict(top=.26, half_width=[.11, .098], offset=.007),
    waistband=dict(below_waist=.012, above_waist=.022, lift=.010),
    ties=dict(knot=.028, tail_length=.30, tail_width=.05, standoff=.01),
    head_cloth=dict(ease=.006, front_above_brow=.052, nape_below_bun=.012, rows=14, sectors=48, knot=.03),
)

MATERIALS = {
    'garment_upper__cook_print_dress': {'base_color_linear': [.028, .032, .056, 1], 'roughness': .9},
    'garment_lower__cook_print_skirt': {'base_color_linear': [.028, .032, .056, 1], 'roughness': .9},
    'garment_outer__cook_apron_check': {'base_color_linear': [.30, .315, .34, 1], 'roughness': .88},
    'headwear__cook_head_cloth': {'base_color_linear': [.17, .06, .045, 1], 'roughness': .9},
    'footwear__cook_shoes_black': {'base_color_linear': [.014, .013, .012, 1], 'roughness': .5},
}
SHOE_MATERIAL = 'footwear__cook_shoes_black'
WEAVE_MATERIAL = 'garment_upper__cook_print_dress'
APRON = 'garment_outer__cook_apron_check'


def _bones(body):
    return {b['name']: b for b in body['skeleton']}


def _sub(a, b):
    return [a[i]-b[i] for i in range(3)]


def _unit(v):
    m = math.sqrt(sum(x*x for x in v)) or 1.
    return [x/m for x in v]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _dot(a, b):
    return sum(a[i]*b[i] for i in range(3))


def cut(mesh, field, name=None):
    """`mesh` clipped to where `field` (a function of a position) is >= 0: every triangle
    clipped exactly, its UVs and skin carried, so the new edge is a clean line."""
    P = mesh['positions_m']
    out = empty(name or mesh['name'], mesh['material'])
    index = {}
    for face, corner in zip(mesh['triangles'], mesh['corner_uvs']):
        poly = [dict(p=P[i], uv=list(c), w=mesh['weights'][i], n=[0., 0., 0.], basis={i: 1.}) for i, c in zip(face, corner)]
        poly = _clip(poly, lambda v: field(v['p']))
        if len(poly) < 3:
            continue
        ids = []
        for v in poly:
            w = {k: x for k, x in v['w'].items() if x > 1e-9}
            total = math.fsum(w.values())
            w = {k: x/total for k, x in w.items()}
            key = (tuple(round(x, 9) for x in v['p']), tuple(sorted((k, round(x, 9)) for k, x in w.items())))
            if key not in index:
                index[key] = len(out['positions_m'])
                out['positions_m'].append(list(v['p'])); out['uvs'].append(list(v['uv'])); out['weights'].append(w)
            ids.append((index[key], v['uv']))
        for k in range(1, len(ids)-1):
            f = [ids[0], ids[k], ids[k+1]]
            if len({i for i, _ in f}) < 3:
                continue
            a, b, c = (out['positions_m'][i] for i, _ in f)
            if math.sqrt(sum(x*x for x in _cross(_sub(b, a), _sub(c, a)))) <= 1e-12:
                continue
            out['triangles'].append([i for i, _ in f]); out['corner_uvs'].append([list(uv) for _, uv in f])
    need(bool(out['triangles']), f'nothing kept of {out["name"]}')
    out['receipt'] = dict(mesh['receipt']) if 'receipt' in mesh else {}
    return out


def _nearest_weights(mesh, p):
    best = min(range(len(mesh['positions_m'])), key=lambda i: sum((mesh['positions_m'][i][k]-p[k])**2 for k in range(3)))
    return dict(mesh['weights'][best])


def sleeve_rolls(full, bones, end_x):
    """The sleeves pushed up the forearm and rolled: a thick band round each forearm from
    `roll_width` above the sleeve's cut end to just past it, swelling out from the full
    sleeve's own section, closed against the arm at the hand side so no gap shows into it.
    Skinned as the sleeve was there."""
    t = TAILORING['sleeves']
    out = empty('rolled_sleeves', 'garment_upper__cook_print_dress')
    P = full['positions_m']
    n, rows = t['sectors'], t['rows']
    for side, sign in (('l', 1), ('r', -1)):
        a = bones[f'lowerarm_{side}']['head_m']; b = bones[f'hand_{side}']['head_m']
        axis = _unit(_sub(b, a))
        e1 = _unit(_cross(axis, [0., 0., 1.])); e2 = _cross(axis, e1)
        def frame(p):
            d = _sub(p, a); u = _dot(d, axis)
            return u, _dot(d, e1), _dot(d, e2)
        u_end = (end_x-abs(a[0]))/abs(axis[0])
        u0, u1 = u_end-t['roll_width'], u_end+.006
        pts = [frame(p) for p in P if p[0]*sign > 0 and u0-.03 <= frame(p)[0] <= u1+.03]
        need(len(pts) > 50, 'no sleeve under the roll')
        radius = []
        for k in range(n):
            ang = 2*math.pi*k/n; ca, sa = math.cos(ang), math.sin(ang)
            near = [math.hypot(v, w) for u, v, w in pts if (v*ca+w*sa) > .7*math.hypot(v, w)]
            need(bool(near), 'empty sleeve sector')
            radius.append(max(near))
        radius = [(radius[k-1]+2*radius[k]+radius[(k+1) % n])/4 for k in range(n)]
        base = len(out['positions_m'])
        for r in range(rows):
            s = r/(rows-1)
            u = u0+(u1-u0)*s
            swell = t['roll_lift']*(.25+.75*math.sin(math.pi*min(1., s*1.15))**.7)
            for k in range(n):
                ang = 2*math.pi*k/n
                rr = radius[k]+swell
                p = [a[i]+u*axis[i]+rr*(math.cos(ang)*e1[i]+math.sin(ang)*e2[i]) for i in range(3)]
                out['positions_m'].append(p); out['uvs'].append([k/n, s]); out['weights'].append(_nearest_weights(full, p))
        # The hand-side lip: the roll's under face turned in to the forearm.
        lip = len(out['positions_m'])
        skin_r = [radius[k]-TAILORING['bodice']['ease']+.002 for k in range(n)]
        for k in range(n):
            ang = 2*math.pi*k/n
            p = [a[i]+u1*axis[i]+skin_r[k]*(math.cos(ang)*e1[i]+math.sin(ang)*e2[i]) for i in range(3)]
            out['positions_m'].append(p); out['uvs'].append([k/n, 1.]); out['weights'].append(_nearest_weights(full, p))
        rings = [[base+r*n+k for k in range(n)] for r in range(rows)]+[[lip+k for k in range(n)]]
        for ra, rb in zip(rings, rings[1:]):
            for k in range(n):
                q = (k+1) % n
                faces = ([ra[k], rb[q], ra[q]], [ra[k], rb[k], rb[q]]) if sign > 0 else ([ra[k], ra[q], rb[q]], [ra[k], rb[q], rb[k]])
                out['triangles'] += faces
    # Wind every face outward from its own forearm axis.
    P2 = out['positions_m']
    for i, f in enumerate(out['triangles']):
        a0, b0, c0 = (P2[j] for j in f)
        side = 'l' if a0[0] > 0 else 'r'
        ax0 = bones[f'lowerarm_{side}']['head_m']; ax = _unit(_sub(bones[f'hand_{side}']['head_m'], ax0))
        cen = [(a0[k]+b0[k]+c0[k])/3 for k in range(3)]
        d = _sub(cen, ax0); radial = _sub(d, [ax[k]*_dot(d, ax) for k in range(3)])
        if _dot(_cross(_sub(b0, a0), _sub(c0, a0)), radial) < 0:
            out['triangles'][i] = [f[0], f[2], f[1]]
    out['corner_uvs'] = [[out['uvs'][j] for j in f] for f in out['triangles']]
    out['receipt'] = dict(garment='rolled sleeves', sleeve_end_x_m=end_x, roll_width_m=t['roll_width'], lift_m=t['roll_lift'])
    return out


def apron_skirt(dress, rows, segments):
    """The apron's skirt: a broad panel following the dress skirt's own surface round the
    front and on round the hips well toward the back (`columns_each_side` of the skirt's
    `segments`), from the waist to `last_row_from_hem` rows above the hem."""
    t = TAILORING['apron']
    out = empty('cook_apron_skirt', APRON)
    columns = list(range(-t['columns_each_side'], t['columns_each_side']+1))
    last = rows-t['last_row_from_hem']
    for row in range(last):
        for col in columns:
            k = col % segments; base = dress['positions_m'][row*segments+k]
            r = math.hypot(base[0], base[2]); off = t['offset']
            out['positions_m'].append([base[0]*(1+off/r), base[1]+.001, base[2]*(1+off/r)])
            out['uvs'].append([(col-columns[0])/(columns[-1]-columns[0]), row/(last-1)])
            out['weights'].append(dict(dress['weights'][row*segments+k]))
    width = len(columns)
    for row in range(last-1):
        for k in range(width-1):
            a = row*width+k; b = a+1; c = a+width+1; d = a+width
            for face in ([a, c, b], [a, d, c]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][i] for i in face])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='checked apron skirt', columns=width, of_segments=segments, rows=last)
    return out


def waistband(upper, lower, bones, waist):
    """The apron's waistband: a band round the waist from just under the skirt's top to a
    little above the bodice's waist, standing `lift` off whichever of the two lies outermost
    at each angle, so it covers the apron's top edge and the foot of the bib."""
    t = TAILORING['waistband']
    from human_lady_1904 import _section, _ray_radius
    segs = 64
    lo, hi = waist-t['below_waist'], waist+t['above_waist']
    out = empty('apron_waistband', APRON)
    rings = []
    levels = [lo, hi]
    sections = {y: _section(upper, y)+_section(lower, y) for y in levels}
    for y in levels:
        ring = []
        for k in range(segs):
            a = 2*math.pi*k/segs; dx, dz = math.sin(a), math.cos(a)
            r = _ray_radius(sections[y], dx, dz)
            need(r is not None, 'no garment under the waistband')
            ring.append(r)
        rings.append(ring)
    # A band is stiff: one radius per angle for its whole height, the largest beneath it.
    radius = [max(r[k] for r in rings)+t['lift'] for k in range(segs)]
    radius = [max(radius[k], (radius[k-1]+radius[k]+radius[(k+1) % segs])/3) for k in range(segs)]
    from human_dress_components import leg_follow
    for j, y in enumerate((lo, hi)):
        for k in range(segs):
            a = 2*math.pi*k/segs
            p = [radius[k]*math.sin(a), y, radius[k]*math.cos(a)]
            out['positions_m'].append(p); out['uvs'].append([k/segs, j]); out['weights'].append({'pelvis': .55, 'spine_01': .45})
    for k in range(segs):
        q = (k+1) % segs
        for f in ([k, q, segs+q], [k, segs+q, segs+k]):
            out['triangles'].append(f)
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='apron waistband', from_y_m=lo, to_y_m=hi, lift_m=t['lift'])
    return out, radius


def ties(band_radius, waist, lower, segments):
    """The apron's ties knotted at the back of the waist: a small knot and two tails falling
    over the skirt behind, double-sided, skinned as the skirt's back there."""
    t = TAILORING['ties']
    n = len(band_radius)
    rb = band_radius[n//2]                      # the band straight behind (-z)
    P = lower['positions_m']; W = lower['weights']
    back = segments//2
    w0 = dict(W[back])
    out = empty('apron_ties', APRON)
    z0 = -rb-t['standoff']
    y0 = waist+.004
    # The knot: a flattened lozenge.
    base = len(out['positions_m'])
    ring = 10
    for i in range(ring):
        a = 2*math.pi*i/ring
        out['positions_m'].append([t['knot']*.6*math.cos(a), y0+t['knot']*.45*math.sin(a), z0-.006])
        out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)]); out['weights'].append(dict(w0))
    c = len(out['positions_m']); out['positions_m'].append([0., y0, z0-.014]); out['uvs'].append([.5, .5]); out['weights'].append(dict(w0))
    for i in range(ring):
        out['triangles'].append([base+i, c, base+(i+1) % ring])
    for side in (1, -1):
        tail = []
        for i in range(10):
            s = i/9; y = y0-.012-t['tail_length']*s
            row = min(range(len(P)//segments), key=lambda r: abs(P[r*segments+back][1]-y))
            zb = P[row*segments+back][2]-.007
            tail.append((side*(.014+.03*s), y, min(z0, zb)))
        b0 = len(out['positions_m'])
        for i, (x, y, z) in enumerate(tail):
            hw = t['tail_width']/2*(.55+.45*i/9)
            for e in (-1, 1):
                out['positions_m'].append([x+e*hw, y, z]); out['uvs'].append([(e+1)/2, i/9]); out['weights'].append(dict(w0))
        for i in range(9):
            a = b0+2*i; b = a+1; c2 = a+3; d = a+2
            out['triangles'] += [[a, b, c2], [a, c2, d]]
    out = _two_sided(out)
    out['receipt'] = dict(garment='apron ties knotted behind', y_m=y0, double_sided=True, skinning='skirt back at the waist')
    return out


def head_cloth(body, bones, hair, lod=0):
    """A cloth bound over the drawn-up hair: a shell round the hair and the knot behind, the
    hair's own outline at every direction from a centre inside the head plus `ease` (so it
    encloses every strand), smoothed as cloth pulled over hair is, cut at the front along the
    hairline above the brow and behind just under the knot, with a small knot of its ends at
    the nape. Rigid on the head bone, a separate mesh."""
    t = TAILORING['head_cloth']
    Q = hair['positions_m']
    eye_y = bones['eye_l']['head_m'][1]
    head = bones['head']['head_m']
    c = [0., eye_y+.035, head[2]-.012]          # inside the skull, behind the eyes
    bun_low = min(p[1] for p in Q if p[2] < c[2]-.06)
    front_y = eye_y+t['front_above_brow']
    back_y = bun_low-t['nape_below_bun']
    scalp = [p for p in body['meshes'][0]['positions_m'] if p[1] > eye_y+.02]
    pts = Q+scalp
    n, rows = t['sectors'], t['rows']
    # The lower edge: high at the brow, falling round the temples to the nape behind the knot.
    def edge_y(az):
        f = .5*(1-math.cos(az))                  # 0 at the front (+z), 1 behind
        return front_y+(back_y-front_y)*(f**1.3)
    def direction(az, el):
        return [math.cos(el)*math.sin(az), math.sin(el), math.cos(el)*math.cos(az)]
    out = empty('headwear_cook_head_cloth', 'headwear__cook_head_cloth')
    grid = []
    for r in range(rows):
        row = []
        for k in range(n):
            az = 2*math.pi*k/n
            # The elevation of the edge at this azimuth, seen from the centre.
            y_edge = edge_y(az)
            horiz = max(.06, max((p[0]*math.sin(az)+(p[2]-c[2])*math.cos(az)) for p in pts if abs(p[1]-y_edge) < .02))
            el0 = math.atan2(y_edge-c[1], horiz)
            el = el0+(math.pi/2-el0)*(r/(rows-1))**1.0
            if r == rows-1:
                el = math.pi/2-1e-3
            d = direction(az, el)
            row.append(d)
        grid.append(row)
    # The support distance in each direction: the farthest point within a cone of it.
    rel = [_sub(p, c) for p in pts]
    lens = [math.sqrt(_dot(v, v)) or 1. for v in rel]
    radius = []
    for row in grid:
        rr = []
        for d in row:
            best = 0.
            for v, l in zip(rel, lens):
                if _dot(v, d) > .965*l:
                    best = max(best, _dot(v, d))
            rr.append(best)
        radius.append(rr)
    # Fill any empty direction from its neighbours, then smooth: cloth bridges the strands.
    for _ in range(6):
        nxt = []
        for r in range(rows):
            row = []
            for k in range(n):
                nb = [radius[r][(k-1) % n], radius[r][(k+1) % n]]+([radius[r-1][k]] if r else [])+([radius[r+1][k]] if r < rows-1 else [])
                row.append(max(radius[r][k], sum(nb)/len(nb)))
            nxt.append(row)
        radius = nxt
    for r in range(rows):
        for k in range(n):
            out['positions_m'].append([c[i]+(radius[r][k]+t['ease'])*grid[r][k][i] for i in range(3)])
            out['uvs'].append([k/n, r/(rows-1)]); out['weights'].append({'head': 1.})
    for r in range(rows-1):
        for k in range(n):
            q = (k+1) % n
            a, b, cc, d = r*n+k, r*n+q, (r+1)*n+q, (r+1)*n+k
            out['triangles'] += [[a, b, cc], [a, cc, d]]
    # Close the crown.
    apex = len(out['positions_m'])
    top = max(radius[-1])+t['ease']
    out['positions_m'].append([c[0], c[1]+top, c[2]]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([(rows-1)*n+k, (rows-1)*n+(k+1) % n, apex])
    # Wind outward from the centre.
    P = out['positions_m']
    for i, f in enumerate(out['triangles']):
        a0, b0, c0 = (P[j] for j in f)
        cen = [(a0[k]+b0[k]+c0[k])/3 for k in range(3)]
        if _dot(_cross(_sub(b0, a0), _sub(c0, a0)), _sub(cen, c)) < 0:
            out['triangles'][i] = [f[0], f[2], f[1]]
    # The knot of its ends at the nape, behind, just above the edge.
    kn = t['knot']
    kb = len(out['positions_m'])
    back_dir = direction(math.pi, math.atan2(back_y+.03-c[1], .1))
    kr = max(_dot(v, back_dir) for v in rel)+t['ease']+.006
    centre = [c[i]+kr*back_dir[i] for i in range(3)]
    for i in range(10):
        a = 2*math.pi*i/10
        out['positions_m'].append([centre[0]+kn*.7*math.cos(a), centre[1]+kn*.45*math.sin(a), centre[2]])
        out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    kc = len(out['positions_m']); out['positions_m'].append([centre[0], centre[1], centre[2]-.012]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for i in range(10):
        out['triangles'].append([kb+i, kb+(i+1) % 10, kc])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    clearance = min(math.dist(p, q) for p in out['positions_m'][:rows*n:7] for q in Q[::3])
    out['receipt'] = dict(garment='cloth bound over the hair', centre_m=c, front_edge_y_m=front_y, back_edge_y_m=back_y,
                          ease_m=t['ease'], head_bone='head', separate_mesh=True, hair_clearance_sampled_m=clearance)
    return out


def construct(body, hair):
    before = digest(body)
    bones = _bones(body)
    t = TAILORING
    spine = bones['spine_02']['head_m'][1]
    waist = spine-t['bodice']['waist_below_spine02']
    full = bodice(body, bones, waist, ease=t['bodice']['ease'], collar=t['bodice']['collar'])
    full = blouse(full, bones, waist, pouch=t['bodice']['pouch'], sleeve=t['bodice']['sleeve'])
    end_x = abs(bones['lowerarm_l']['head_m'][0])+t['sleeves']['end_past_elbow']
    upper = cut(full, lambda p: end_x-abs(p[0]), 'cook_bodice')
    upper['material'] = 'garment_upper__cook_print_dress'
    s = t['skirt']
    lower, core = gathered_skirt(body, bones, spine, upper, segments=s['segments'], rows=s['rows'], ease=s['ease'], hem=s['hem_y'])
    lower['name'] = 'cook_skirt'; lower['material'] = 'garment_lower__cook_print_skirt'
    neck = collar_band(upper, bones, below=t['neckband']['below'], lift=t['neckband']['lift'])
    neck['name'] = 'cook_neckband'; neck['material'] = 'garment_upper__cook_print_dress'
    apron = apron_skirt(lower, s['rows'], s['segments'])
    b = t['bib']
    front = bib(upper, bones, waist, top=b['top'], half_width=tuple(b['half_width']), offset=b['offset'])
    front['name'] = 'cook_apron_bib'; front['material'] = APRON
    band, band_r = waistband(upper, lower, bones, waist)
    parts = [upper, sleeve_rolls(full, bones, end_x), neck, lower, apron, front, band,
             ties(band_r, waist, lower, s['segments']), head_cloth(body, bones, hair)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_cook_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; the pictures are monochrome, and the print and the check are drawn as their mean colour',
                             'No cloth simulation: skirt and apron share the leg-following skirt weights (T-3423)',
                             'Head cloth rigid on the head bone, laid over the fitted bun hair'])


def prepare_cook_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3479; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('cook_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_cook_1904.py',
         'unsupported cook component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'cook assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'cook scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed cook body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'cook components require the declared liberty')
    for garment in spec['garments']:
        prov = garment.get('provenance', {})
        need(prov.get('grade') in ('attested', 'inferred', 'reconstructed') and (prov.get('source_ids') or prov.get('liberty')),
             f"garment {garment.get('id')} has no provenance")
        for sid in prov.get('source_ids', []):
            record = json.loads((root/'data/sources'/f'{sid}.json').read_text())
            need(record.get('id') == sid and record.get('rights_status') in ('public_domain', 'no_known_restrictions'),
                 f'{sid}: not a cleared reference')
    for sid in recipe['sources']:
        need((root/'data/sources'/f'{sid}.json').is_file(), f'{sid}: no source record')
    need(recipe['hair_component'].get('fitter') == 'mhclo_proxy', 'the head cloth is laid over the fitted bun hair')
    from human_hair_proxy import fit
    hair = fit(body, recipe['hair_component'], root)[0]
    bundle = construct(body, hair)
    bundle['liberty'] = LIBERTY
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']]
    for material, m in bundle['materials'].items():
        need(recipe['colors_linear_rgba'].get(material) == m['base_color_linear'], f'{material}: recipe/source colour differs')
    names = {b['name'] for b in body['skeleton']}
    for mesh in bundle['meshes']:
        count = len(mesh['positions_m'])
        need(mesh['material'] in bundle['materials'], f"{mesh['name']}: material outside the outfit")
        need(count > 0 and count == len(mesh['weights']) == len(mesh['uvs']), 'incomplete garment arrays')
        need(len(mesh['corner_uvs']) == len(mesh['triangles']), 'garment corner UVs missing')
        for mapping in mesh['weights']:
            need(1 <= len(mapping) <= 4 and not (set(mapping)-names)
                 and all(math.isfinite(w) and w >= 0 for w in mapping.values())
                 and abs(math.fsum(mapping.values())-1.) < 1e-9, 'invalid garment skin')
        for face in mesh['triangles']:
            need(len(face) == len(set(face)) == 3 and all(type(i) is int and 0 <= i < count for i in face),
                 'invalid garment triangle')
    return bundle


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True); p.add_argument('--recipe', type=Path, required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    from human_hair_proxy import fit
    body = json.loads(raw)
    hair = fit(body, json.loads(a.recipe.read_text())['hair_component'], Path(__file__).resolve().parent.parent)[0]
    data = construct(body, hair)
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]}, indent=1, default=str))
