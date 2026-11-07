# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 gentleman's day dress on the shared portable male rig (T-3441).

First worn by John J. Glessner (1843-1936), vice president of International Harvester
in 1904. The pieces, read from the period pictures in the recipe
(data/humans/recipes/gentleman_1904.json):

  shirt          white linen, long sleeves, a tall standing collar (the 1897 plate of
                 Glessner himself shows one reaching nearly to the jaw)
  tie            a dark four-in-hand knotted at the collar (the same plate)
  waistcoat      dark, single-breasted and cut high, its V opening well up the chest
                 (the plate; Elihu Root beside Taft, 1904)
  frock coat     dark wool, buttoned to the chest, rolled lapels, skirts to the knee
                 (Root and Taft, 1904; the frock-coated man on State Street, 1903)
  trousers       mid-grey, straight and hanging (Taft, 1904), worn over black boots
  derby          a black felt bowler: nearly every man on State Street in 1903 wears one,
                 the frock-coated man among them. A separate mesh rigidly on the head
                 bone (material `headwear__derby_felt`), so a renderer can lift it off
                 the head for a greeting and set it back.

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed
(the pictures are monochrome); liberty L-human-modular-dress-1789 with its T-3441
supplement. The source anatomy is never changed: every piece is either a shell offset
from the body's own triangles (its UVs and skin weights carried) or a loft round the
body's own cross-sections, skinned to the body's own bones.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_gentleman_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_source_normals import source_shared_normals
from human_workwear_fit import _clip, _slab_points, garment_shell
from human_period_wardrobe import finish_edges

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'gentleman_1904_v1'
RECIPE = 'data/humans/recipes/gentleman_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=dict(ease=.006, collar=.040, collar_front_dip=.024, collar_dip_depth=.060, waist_below_spine02=.115),
    waistcoat=dict(ease=.013, armpit_extra=.008, hem_below_spine02=.115, top_below_neck=.022,
                   v_bottom_above_spine02=.215, v_half_width_top=.050),
    coat=dict(ease=.024, armpit_extra=.022, sleeve_short_of_wrist=.030, collar_above_neck=.016, waist_below_spine02=.020,
              roll_above_spine02=.130, v_half_width_top=.060, lapel_width=.052, lapel_notch=.80),
    skirt=dict(hem_y=.490, ease=.022, front_gap_deg=.5, segments=72, rows=14),
    trousers=dict(ease=.009, waist_height_fraction=.585, cuff_radius_ratio=.88,
                  added_section_ease=.010, thigh_transition_fraction=.65, hem_front_y=.072, hem_back_y=.038),
    tie=dict(knot_width=.026, blade_width=.050, standoff=.0035),
    derby=dict(seat_below_top=.090, ease=.007, crown_height=.118, brim_side=.040, brim_fore=.048,
               brim_curl=.018, thickness=.004),
)

MATERIALS = {
    'garment_upper__shirt_linen_1904': {'base_color_linear': [.80, .80, .78, 1], 'roughness': .78},
    'garment_outer__frock_coat_black': {'base_color_linear': [.018, .018, .021, 1], 'roughness': .86},
    'garment_lower__trousers_grey_1904': {'base_color_linear': [.085, .084, .082, 1], 'roughness': .9},
    'accessory__silk_tie_black': {'base_color_linear': [.012, .012, .014, 1], 'roughness': .45},
    'headwear__derby_felt': {'base_color_linear': [.014, .013, .013, 1], 'roughness': .7},
    'footwear__black_boots': {'base_color_linear': [.012, .011, .011, 1], 'roughness': .38},
}
SHOE_MATERIAL = 'footwear__black_boots'
WEAVE_MATERIAL = 'garment_upper__shirt_linen_1904'


def _skin4(mapping, limit=.08):
    """Four strongest influences, renormalised; a cut vertex interpolated across a
    joint may carry five or six, and up to `limit` of its mass is let go."""
    items = sorted(((k, v) for k, v in mapping.items() if v > 1e-12), key=lambda p: (-p[1], p[0]))
    need(math.fsum(v for _, v in items[4:]) <= limit, 'garment cut discards too much skin mass')
    items = items[:4]; total = math.fsum(v for _, v in items)
    return {k: v/total for k, v in items}


def _smooth(out, anchors, iterations, min_ease):
    """Tailoring, not skin: Laplacian smoothing of a shell's interior so the cloth spans
    the anatomy's hollows (between the pectorals, over the ribs) the way a pressed wool
    coat does, then every point is pushed back out along its body normal to at least
    `min_ease` off the body. Boundary vertices (cut edges) stay where they were."""
    P = out['positions_m']; n = len(P)
    nbr = [set() for _ in range(n)]
    edges = {}
    for f in out['triangles']:
        for a, b in zip(f, f[1:]+f[:1]):
            nbr[a].add(b); nbr[b].add(a)
            key = (min(a, b), max(a, b)); edges[key] = edges.get(key, 0)+1
    boundary = {i for (a, b), c in edges.items() if c == 1 for i in (a, b)}
    def relax(points):
        cur = [list(p) for p in points]
        for _ in range(iterations):
            nxt = [list(p) for p in cur]
            for i in range(n):
                if i in boundary or not nbr[i]:
                    continue
                avg = [math.fsum(cur[j][a] for j in nbr[i])/len(nbr[i]) for a in range(3)]
                nxt[i] = [cur[i][a]+.5*(avg[a]-cur[i][a]) for a in range(3)]
            cur = nxt
        return cur
    # The body beneath, relaxed the same way: the clamp holds the cloth off the body's
    # broad form, not off every small relief (a nipple would otherwise print through).
    body = relax([a[0] for a in anchors])
    raw = anchors
    anchors = [(b, a[1]) for b, a in zip(body, anchors)]
    cur = [list(p) for p in P]
    for _ in range(iterations):
        nxt = [list(p) for p in cur]
        for i in range(n):
            if i in boundary or not nbr[i]:
                continue
            avg = [math.fsum(cur[j][a] for j in nbr[i])/len(nbr[i]) for a in range(3)]
            nxt[i] = [cur[i][a]+.5*(avg[a]-cur[i][a]) for a in range(3)]
        cur = nxt
    moved = 0.
    for i, (body_p, nrm) in enumerate(anchors):
        if i in boundary:
            continue
        d = math.fsum((cur[i][a]-body_p[a])*nrm[a] for a in range(3))
        if d < min_ease:
            cur[i] = [cur[i][a]+(min_ease-d)*nrm[a] for a in range(3)]
        # ...and never more than 2 mm nearer the actual body than that.
        d = math.fsum((cur[i][a]-raw[i][0][a])*nrm[a] for a in range(3))
        if d < min_ease-.002:
            cur[i] = [cur[i][a]+(min_ease-.002-d)*nrm[a] for a in range(3)]
        moved = max(moved, math.dist(cur[i], P[i]))
    out['positions_m'] = cur
    return moved


def _poly_shell(body, bones, name, material, fields, ease, ease_planes, neck_base, pieces=None, smooth=None):
    """Body triangles clipped by linear `fields` (each a function of a corner dict,
    kept where >= 0), offset `ease` along the body's shared normals, eased to zero
    normal travel in Y within 2*ease of the y-planes in `ease_planes`. `pieces` splits
    a polygon into several clipped pieces (a V opening). Weights and UVs carried."""
    out = empty(name, material)
    source = body['meshes'][0]
    P = source['positions_m']
    normals = source_shared_normals(P, source['triangles'], source['source_vertex_indices'])
    cache = {}; anchors = []
    for face in source['triangles']:
        poly = [dict(p=P[i], uv=source['uvs'][i], w=source['weights'][i], n=normals[i],
                     basis={source['source_vertex_indices'][i]: 1.}) for i in face]
        for field in fields:
            poly = _clip(poly, field)
            if not poly:
                break
        if not poly:
            continue
        for part in (pieces(poly) if pieces else [poly]):
            if len(part) < 3:
                continue
            ids = []
            for v in part:
                length = math.hypot(*v['n']); need(length > 1e-12, 'undefined garment normal')
                n = [x/length for x in v['n']]
                gain = 1.
                for lo, hi in ease_planes:
                    gain = min(gain, max(0., min(v['p'][1]-lo, hi-v['p'][1]))/(2*ease))
                p = [v['p'][a]+ease*n[a]*(gain if a == 1 else 1.) for a in range(3)]
                mapping = dict(v['w'])
                if v['p'][1] >= neck_base-1e-12:
                    moved = math.fsum(mapping.pop(k, 0.) for k in ('head', 'jaw'))
                    mapping['neck_01'] = mapping.get('neck_01', 0.)+moved
                weights = _skin4(mapping)
                key = (tuple(round(x, 12) for x in p), tuple(sorted(weights.items())))
                if key not in cache:
                    cache[key] = len(out['positions_m'])
                    out['positions_m'].append(p); out['uvs'].append(list(v['uv'])); out['weights'].append(weights)
                    anchors.append((v['p'], n))
                ids.append(cache[key])
            for i in range(1, len(ids)-1):
                tri = [ids[0], ids[i], ids[i+1]]
                if len(set(tri)) < 3:
                    continue
                a, b, c = [out['positions_m'][k] for k in tri]
                u = [b[j]-a[j] for j in range(3)]; w = [c[j]-a[j] for j in range(3)]
                if math.hypot(u[1]*w[2]-u[2]*w[1], u[2]*w[0]-u[0]*w[2], u[0]*w[1]-u[1]*w[0]) <= 1e-16:
                    continue
                out['triangles'].append(tri); out['corner_uvs'].append([part[k]['uv'] for k in (0, i, i+1)])
    need(bool(out['triangles']), f'empty garment {name}')
    if smooth:
        out['smoothing_max_move_m'] = _smooth(out, anchors, *smooth)
    out['_normals'] = [n for _, n in anchors]
    return out


def _armpit_ease(out, body, bones, extra):
    """Room under the arm: where the arm meets the body the skin folds and swells as the
    arm comes down from the rest pose, and a shell skinned like the body meets it there.
    Smoothing has slid the shell along the body, so near the arm each point first takes the
    skin weights of the body points nearest it now (inverse-distance over three), then a
    tailored coat is cut loose under the arm: points of mixed arm and torso skin below the
    shoulder stand `extra` further out, fading to nothing at pure torso and pure arm."""
    shoulder = bones['upperarm_l']['head_m'][1]
    source = body['meshes'][0]
    near_arm = [(p, w) for p, w in zip(source['positions_m'], source['weights'])
                if p[1] < shoulder+.08 and p[1] > shoulder-.3 and abs(p[0]) > .06]
    def arm_share(w):
        return math.fsum(x for b, x in w.items() if b.startswith(('clavicle', 'upperarm')))
    moved = 0
    for i, (p, w) in enumerate(zip(out['positions_m'], out['weights'])):
        if not shoulder-.3 < p[1] < shoulder+.08 or abs(p[0]) <= .06 or not .01 < arm_share(w) < .99:
            continue
        best = sorted(near_arm, key=lambda q: math.dist(q[0], p))[:3]
        mapping = {}
        for q, qw in best:
            k = 1./max(math.dist(q, p), 1e-4)
            for b, x in qw.items():
                mapping[b] = mapping.get(b, 0.)+k*x
        total = math.fsum(mapping.values())
        out['weights'][i] = w = _skin4({b: x/total for b, x in mapping.items()}, 1.)
    for i, (p, w) in enumerate(zip(out['positions_m'], out['weights'])):
        arm = arm_share(w)
        if p[1] > shoulder+.03 or not .05 < arm < .95:
            continue
        g = math.sin(math.pi*(arm-.05)/.9)*min(1., (shoulder+.03-p[1])/.04)
        n = out['_normals'][i]
        out['positions_m'][i] = [p[a]+extra*g*n[a] for a in range(3)]
        moved += 1
    return moved


def _v_pieces(y_bottom, half_top, y_top):
    """Split a polygon into back, front-left and front-right, cutting a V opening whose
    half-width grows linearly from 0 at y_bottom to half_top at y_top."""
    slope = half_top/(y_top-y_bottom)
    def pieces(poly):
        back = _clip(poly, lambda v: -v['p'][2])
        front = _clip(poly, lambda v: v['p'][2])
        left = _clip(_clip(front, lambda v: v['p'][0]), lambda v: v['p'][0]-slope*(v['p'][1]-y_bottom))
        right = _clip(_clip(front, lambda v: -v['p'][0]), lambda v: -v['p'][0]-slope*(v['p'][1]-y_bottom))
        return [back, left, right]
    return pieces


def _arm_mass(v):
    return math.fsum(x for b, x in v['w'].items() if b.startswith(('clavicle', 'upperarm', 'lowerarm', 'hand')))


def shirt(body, bones):
    """The white shirt: the body's own surface from the waist to a tall standing collar,
    sleeves to the wrist. A plain normal offset (no bridging envelope: on a man the
    chest needs none, and an envelope pushed the shirt out through the waistcoat)."""
    t = TAILORING['shirt']
    neck = bones['neck_01']['head_m'][1]
    lo = bones['spine_02']['head_m'][1]-t['waist_below_spine02']; hi = neck+t['collar']
    cuff = abs(bones['hand_l']['head_m'][0])-.012
    # T-3456 (owner, 2026-11-07: "his collar looks like it wraps around his chin"): the
    # collar's top falls toward the throat, `collar_front_dip` lower at the front than at
    # the back, so a level cut through the body no longer takes in the underside of the jaw.
    neck_z = bones['neck_01']['head_m'][2]
    def top(v):
        return hi-t['collar_front_dip']*min(1., max(0., (v['p'][2]-neck_z)/t['collar_dip_depth']))-v['p'][1]
    fields = [lambda v: v['p'][1]-lo, top, lambda v: cuff-v['p'][0], lambda v: cuff+v['p'][0]]
    # Only what can be seen is made: the collar all round, the front between the
    # waistcoat's and the coat's openings, and the cuffs beyond the coat sleeves. A whole
    # shirt under a closed coat only pokes through it at the armpits when the arms come down.
    collar_y = neck-.012
    front_y = bones['spine_02']['head_m'][1]+TAILORING['waistcoat']['v_bottom_above_spine02']-.035
    cuff_x = cuff-.045
    def pieces(poly):
        collar = _clip(_clip(poly, lambda v: v['p'][1]-collar_y), lambda v: .2-abs(v['p'][0]))
        front = _clip(_clip(_clip(_clip(_clip(poly, lambda v: collar_y-v['p'][1]), lambda v: v['p'][1]-front_y),
                                    lambda v: v['p'][2]), lambda v: .09-v['p'][0]), lambda v: .09+v['p'][0])
        left = _clip(poly, lambda v: v['p'][0]-cuff_x)
        right = _clip(poly, lambda v: -v['p'][0]-cuff_x)
        return [collar, front, left, right]
    out = _poly_shell(body, bones, 'shirt_standing_collar', 'garment_upper__shirt_linen_1904', fields, t['ease'],
                      [(lo, hi)], neck, pieces)
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='white linen shirt, long sleeves, standing collar', waist_y_m=lo, collar_top_y_m=hi,
                          cuff_x_m=cuff, ease_m=t['ease'], source_body_mutated=False)
    return out


def waistcoat(body, bones):
    t = TAILORING['waistcoat']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['hem_below_spine02']; hi = neck-t['top_below_neck']
    vb = spine+t['v_bottom_above_spine02']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: .35-_arm_mass(v),
              lambda v: .235-v['p'][0], lambda v: .235+v['p'][0]]
    out = _poly_shell(body, bones, 'waistcoat_high_cut', 'garment_outer__frock_coat_black', fields, t['ease'],
                      [(lo, hi)], bones['neck_01']['head_m'][1], _v_pieces(vb, t['v_half_width_top'], hi), smooth=(12, .0125))
    _armpit_ease(out, body, bones, t['armpit_extra'])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='dark single-breasted waistcoat cut high', hem_y_m=lo, top_y_m=hi, v_bottom_y_m=vb)
    return out


def coat_body(body, bones):
    """The frock coat above its waist seam: closed torso to the roll of the lapels,
    sleeves to just short of the shirt cuff, a low standing coat collar at the back."""
    t = TAILORING['coat']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['waist_below_spine02']; hi = neck+t['collar_above_neck']
    cuff = abs(bones['hand_l']['head_m'][0])-t['sleeve_short_of_wrist']
    vb = spine+t['roll_above_spine02']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: cuff-v['p'][0], lambda v: cuff+v['p'][0]]
    out = _poly_shell(body, bones, 'frock_coat_body', 'garment_outer__frock_coat_black', fields, t['ease'],
                      [(lo, hi)], neck, _v_pieces(vb, t['v_half_width_top'], hi), smooth=(60, .019))
    loose = _armpit_ease(out, body, bones, t['armpit_extra'])
    out['receipt'] = dict(garment='frock coat body and sleeves', armpit_points_eased=loose, waist_seam_y_m=lo, collar_y_m=hi,
                          roll_point_y_m=vb, sleeve_end_x_m=cuff)
    return out, (lo, vb, hi)


def _surface_sample(mesh, x, y, side=1):
    """The outermost (front, z max) point of `mesh` under (x, y), with its skin."""
    best = None
    P = mesh['positions_m']
    for face in mesh['triangles']:
        a, b, c = [P[i] for i in face]
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-14:
            continue
        u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        bary = (u, v, 1-u-v)
        if min(bary) < -1e-9:
            continue
        z = math.fsum(w*p[2] for w, p in zip(bary, (a, b, c)))
        if z > 0 and (best is None or z > best[0]):
            weights = {}
            for w, i in zip(bary, face):
                for k, val in mesh['weights'][i].items():
                    weights[k] = weights.get(k, 0.)+max(0., w)*val
            best = (z, weights)
    need(best is not None, f'no garment surface under ({x:.3f}, {y:.3f})')
    items = sorted(best[1].items(), key=lambda p: (-p[1], p[0]))[:4]
    total = math.fsum(w for _, w in items)
    return best[0], {k: w/total for k, w in items}


def lapels(coat, roll):
    """Two rolled lapels laid on the coat front along the V's edges, from the roll point
    to the collar, widening to a notch near the top: a shaped strip 3 mm proud of the
    coat, skinned as the coat beneath it."""
    t = TAILORING['coat']
    lo, vb, hi = roll
    out = empty('frock_coat_lapels', 'garment_outer__frock_coat_black')
    rows, cols = 16, 5
    slope = t['v_half_width_top']/(hi-vb)
    for sign in (1, -1):
        base = len(out['positions_m'])
        for r in range(rows):
            s = r/(rows-1)
            y = vb+s*(hi-vb-.004)
            edge = slope*(y-vb)
            # cloth_torso eased the V edge outward: start at the coat's actual edge.
            for step in range(40):
                try:
                    _surface_sample(coat, sign*(edge+.002), y); break
                except ValueError:
                    edge += .002
            ramp = min(1., s/t['lapel_notch'])
            width = t['lapel_width']*(ramp*(2-ramp))*(1. if s <= t['lapel_notch'] else .55)
            width = max(width, .006)
            for c in range(cols):
                u = c/(cols-1)
                x = sign*min(.112, edge+.002+u*width)
                while True:
                    try:
                        z, w = _surface_sample(coat, x, y); break
                    except ValueError:
                        need(abs(x) > edge, 'lapel has no coat beneath it')
                        x -= sign*.002
                out['positions_m'].append([x, y, z+.003*(1-.4*u)])
                out['uvs'].append([.5+sign*.25*u, s]); out['weights'].append(w)
        for r in range(rows-1):
            for c in range(cols-1):
                a = base+r*cols+c; b = a+1; d = a+cols; e = d+1
                faces = ([a, b, e], [a, e, d]) if sign > 0 else ([a, e, b], [a, d, e])
                for f in faces:
                    out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][i] for i in f])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='rolled lapels', roll_point_y_m=vb, width_m=t['lapel_width'], notch_fraction=t['lapel_notch'])
    return out


def _coat_follow(bones, waist):
    """Skirt skin: pelvis at the waist seam, shared with the thigh (and below the knee
    the calf) of its own side below it, more at the front than the back; the two front
    panels each go wholly with their own leg, so they part over a striding thigh."""
    knee = bones['calf_l']['head_m'][1]; half = abs(bones['thigh_l']['head_m'][0])
    def weights(p):
        t = min(1., max(0., (waist-p[1])/(.45*(waist-knee)))); t = t*(2-t)
        r = math.hypot(p[0], p[2]) or 1.
        front = p[2]/r
        a = t*(.45+.5*max(0., front))
        u = min(1., max(0., (knee+.02-p[1])/.3))
        left = 1. if (p[2] > 0 and p[0] > 0) else 0. if p[2] > 0 else min(1., max(0., .5+p[0]/(2*half)))
        w = {'pelvis': 1-a}
        for side, share in (('l', left), ('r', 1-left)):
            for bone, part in ((f'thigh_{side}', 1-u), (f'calf_{side}', u)):
                if a*share*part > 1e-6:
                    w[bone] = w.get(bone, 0.)+a*share*part
        return _skin4(w, 1.)
    return weights


def coat_skirt(body, bones, coat, waist):
    """The frock coat's skirts: a loft from the waist seam to the knee, round convex
    supports that enclose the body's own sections (and hang: below the seat no ring
    is narrower than the one above it), open at the front where the two fronts meet."""
    t = TAILORING['skirt']
    segs, rows, ease = t['segments'], t['rows'], t['ease']
    hem = t['hem_y']; top = waist+.006
    levels = [top+(hem-top)*i/(rows-1) for i in range(rows)]
    tris = [[m['positions_m'][i] for i in f] for m in body['meshes'] for f in m['triangles']
            if min(m['positions_m'][i][1] for i in f) <= top+.02 and max(m['positions_m'][i][1] for i in f) >= hem-.02]
    gap = math.radians(t['front_gap_deg'])
    angles = [gap+(2*math.pi-2*gap)*k/(segs-1) for k in range(segs)]
    dirs = [(math.sin(a), math.cos(a)) for a in angles]
    # Closed polar support of each band (both neighbouring slabs), then hang.
    supports = []
    for i, y in enumerate(levels):
        pts = _slab_points(tris, levels[min(rows-1, i+1)]-.004, levels[max(0, i-1)]+.004)
        need(len(pts) >= 3, 'empty coat skirt band')
        supports.append([max(nx*p[0]+nz*p[2] for p in pts)+ease for nx, nz in dirs])
    widest = max(range(rows), key=lambda i: sum(supports[i]))
    for i in range(widest+1, rows):
        supports[i] = [max(a, .995*b) for a, b in zip(supports[i], supports[i-1])]
    # Smooth round the ring (the support of a polygon of directions is jagged).
    for i in range(rows):
        s = supports[i]
        supports[i] = [max(s[k], (s[max(0, k-1)]+2*s[k]+s[min(segs-1, k+1)])/4) for k in range(segs)]
    # The top ring tucks just inside the coat body's own section at the seam.
    coat_sec = []
    for face in coat['triangles']:
        tri = [coat['positions_m'][i] for i in face]
        if min(p[1] for p in tri) <= top+.008 <= max(p[1] for p in tri):
            coat_sec.extend(_slab_points([tri], top+.008, top+.008))
    out = empty('frock_coat_skirts', 'garment_outer__frock_coat_black')
    follow = _coat_follow(bones, waist)
    flare = .006
    for i, y in enumerate(levels):
        f = i/(rows-1)
        for k, (nx, nz) in enumerate(dirs):
            # More room over the front, where a striding knee pushes the skirt.
            r = supports[i][k]+(flare+.014*max(0., nz))*f**1.4
            if i == 0 and coat_sec:
                r = min(r, max(nx*p[0]+nz*p[2] for p in coat_sec)-.0015)
            p = [nx*r, y, nz*r]
            out['positions_m'].append(p); out['uvs'].append([k/(segs-1), f]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for k in range(segs-1):
            a = i*segs+k; b = a+1; c = a+segs+1; d = a+segs
            for face in ([a, b, c], [a, c, d]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][j] for j in face])
    # Standing clearance: every body point of the band lies inside its ring.
    worst = math.inf
    for i in range(rows-1):
        for p in _slab_points(tris, levels[i+1], levels[i]):
            th = math.atan2(p[0], p[2]) % (2*math.pi)
            if th < gap or th > 2*math.pi-gap:
                continue
            k = min(segs-2, max(0, int((th-gap)/((2*math.pi-2*gap)/(segs-1)))))
            q = (p[1]-levels[i])/(levels[i+1]-levels[i])
            ring = [out['positions_m'][j*segs+k] for j in (i, i+1)]
            rr = (1-q)*math.hypot(ring[0][0], ring[0][2])+q*math.hypot(ring[1][0], ring[1][2])
            worst = min(worst, rr-math.hypot(p[0], p[2]))
    need(worst > .004, f'coat skirt meets the standing body ({worst:.4f} m)')
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='frock coat skirts to the knee', hem_y_m=hem, top_y_m=top, ease_m=ease,
                          minimum_standing_body_clearance_m=worst, front_gap_deg=t['front_gap_deg'],
                          skinning='pelvis at the seam; each front panel with its own thigh/calf; back shared')
    return out


def _lengthen_hems(shell, bones, t):
    """The workwear shell ends a little above the ankle; a 1904 trouser reaches the shoe.
    Each leg's open hem cycle is carried straight down (no taper, 3 per cent fuller) to a
    hem that slopes from the instep in front to just above the heel behind, skinned as
    the hem it hangs from."""
    import collections
    P = shell['positions_m']
    edges = collections.Counter(tuple(sorted(e)) for f in shell['triangles'] for e in zip(f, f[1:]+f[:1]))
    adj = collections.defaultdict(list)
    for (a, b), c in edges.items():
        if c == 1:
            adj[a].append(b); adj[b].append(a)
    seen = set(); cycles = []
    for start in sorted(adj):
        if start in seen:
            continue
        cyc = [start]; seen.add(start); prev, cur = None, start
        while True:
            nxt = [v for v in adj[cur] if v != prev]
            if not nxt or nxt[0] == start:
                break
            prev, cur = cur, nxt[0]
            if cur in seen:
                break
            cyc.append(cur); seen.add(cur)
        cycles.append(cyc)
    knee = bones['calf_l']['head_m'][1]
    hems = [c for c in cycles if max(P[i][1] for i in c) < knee]
    need(len(hems) == 2, 'trousers need two leg hems to lengthen')
    out = copy.deepcopy(shell)
    front_y, back_y = t['hem_front_y'], t['hem_back_y']
    for cyc in hems:
        cx = math.fsum(P[i][0] for i in cyc)/len(cyc); cz = math.fsum(P[i][2] for i in cyc)/len(cyc)
        zmin = min(P[i][2] for i in cyc); zmax = max(P[i][2] for i in cyc)
        # Keep the cycle's own winding: the new band continues the shell outward-facing.
        a0, b0 = cyc[0], cyc[1]
        face = next(f for f in shell['triangles'] if a0 in f and b0 in f)
        k = face.index(a0)
        forward = face[(k+1) % 3] == b0
        rings = [cyc]
        for step, frac in ((1, .5), (2, 1.)):
            ring = []
            for i in cyc:
                p = P[i]; w = (p[2]-zmin)/max(1e-9, zmax-zmin)
                y_end = back_y+(front_y-back_y)*w
                y = p[1]+(y_end-p[1])*frac
                scale = 1+.03*frac
                q = [cx+(p[0]-cx)*scale, y, cz+(p[2]-cz)*scale]
                ring.append(len(out['positions_m']))
                out['positions_m'].append(q); out['uvs'].append(list(shell['uvs'][i])); out['weights'].append(dict(shell['weights'][i]))
                if 'source_basis' in out:
                    out['source_basis'].append(dict(shell['source_basis'][i]))
            rings.append(ring)
        n = len(cyc)
        for ri, (r0, r1) in enumerate(zip(rings, rings[1:])):
            for j in range(n):
                a, b, c, d = r0[j], r0[(j+1) % n], r1[(j+1) % n], r1[j]
                # A small band of its own in UV (a flat cloth colour; no atlas detail lost).
                uv = {a: [j/n, .90+.04*ri], b: [(j+1)/n, .90+.04*ri], c: [(j+1)/n, .94+.04*ri], d: [j/n, .94+.04*ri]}
                for f in ([a, d, c], [a, c, b]) if forward else ([a, b, c], [a, c, d]):
                    out['triangles'].append(f)
                    out['corner_uvs'].append([uv[v] for v in f])
                    if 'source_triangle_indices' in out:
                        out['source_triangle_indices'].append(-1)
    return out


def trousers(body, bones, height):
    t = TAILORING['trousers']
    recipe = dict(waist_height_fraction=t['waist_height_fraction'], shirt_hem_fraction=.565,
                  workwear_tailoring_v5=dict(waistcoat_closed_front_torso_fraction=.4,
                                             trouser_cuff_radius_ratio=t['cuff_radius_ratio'],
                                             trouser_added_section_ease_m=t['added_section_ease'],
                                             trouser_thigh_transition_fraction=t['thigh_transition_fraction']))
    bones = {b['name']: b for b in body['skeleton']}
    out = garment_shell(body['meshes'][0], 'trousers', t['ease'], recipe, bones, height)
    out = _lengthen_hems(out, bones, t)
    out = finish_edges(out, .0015)
    out['name'] = 'straight_trousers'; out['material'] = 'garment_lower__trousers_grey_1904'
    for k in ('source_basis', 'source_triangle_indices'):
        out.pop(k, None)
    return out


def tie(shirt_mesh, bones, waist_v_bottom):
    """A dark four-in-hand: a knot at the foot of the collar's front and the blade
    down the shirt front to below the waistcoat's opening, 3.5 mm proud of the shirt."""
    t = TAILORING['tie']
    neck = bones['neck_01']['head_m'][1]
    out = empty('four_in_hand_tie', 'accessory__silk_tie_black')
    top = neck+.006; knot_bottom = neck-.030; bottom = waist_v_bottom-.03
    rows = 14; cols = 5
    for r in range(rows):
        s = r/(rows-1)
        y = top+(bottom-top)*s
        knot = y >= knot_bottom
        half = (t['knot_width']*(1-.25*(top-y)/(top-knot_bottom)) if knot else
                t['knot_width']*.55+(t['blade_width']-t['knot_width']*.55)*((knot_bottom-y)/(knot_bottom-bottom))**.8)/2
        bulge = .006*(1-((y-(knot_bottom+top)/2)/((top-knot_bottom)/2))**2) if knot else 0.
        for c in range(cols):
            u = c/(cols-1)
            x = -half+2*half*u
            z, w = _surface_sample(shirt_mesh, x, y)
            z += t['standoff']+bulge*(1-(2*u-1)**2)+.0015*(1-(2*u-1)**2)
            out['positions_m'].append([x, y, z]); out['uvs'].append([u, s]); out['weights'].append(w)
    for r in range(rows-1):
        for c in range(cols-1):
            a = r*cols+c; b = a+1; d = a+cols; e = d+1
            for f in ([a, e, b], [a, d, e]):
                out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][i] for i in f])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='four-in-hand tie', knot_y_m=[knot_bottom, top], blade_bottom_y_m=bottom)
    return out


def derby(body, bones, lod=0):
    """A black felt derby seated round the skull's own section: a domed crown, a narrow
    brim curled up at the sides. Rigid on the head bone, a separate mesh, so it can be
    lifted off and set back."""
    t = TAILORING['derby']
    P = body['meshes'][0]['positions_m']; W = body['meshes'][0]['weights']
    head_pts = [p for p, w in zip(P, W) if w.get('head', 0.) > .9]
    top = max(p[1] for p in head_pts)
    seat = top-t['seat_below_top']
    band = [p for p in head_pts if seat-.012 <= p[1] <= seat+.03]
    cx = (min(p[0] for p in band)+max(p[0] for p in band))/2
    cz = (min(p[2] for p in band)+max(p[2] for p in band))/2
    n = (40, 28, 20, 12)[lod]
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    # Seat ring: the skull's support in each direction, plus ease.
    seat_r = [max((p[0]-cx)*dx+(p[2]-cz)*dz for p in band)+t['ease'] for dx, dz in dirs]
    seat_r = [(seat_r[(k-1) % n]+2*seat_r[k]+seat_r[(k+1) % n])/4+.002 for k in range(n)]
    H = t['crown_height']
    # Crown profile: (height fraction, radius factor): straight-ish sides, rounded top.
    profile = [(0., 1.), (.12, 1.015), (.45, 1.03), (.68, 1.0), (.82, .9), (.92, .72), (.98, .42)]
    out = empty('headwear_derby', 'headwear__derby_felt')
    rings = []
    def ring(radii, y_of_k):
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            ids.append(len(out['positions_m']))
            out['positions_m'].append([cx+radii[k]*dx, y_of_k(k), cz+radii[k]*dz])
            out['uvs'].append([k/n, 0.]); out['weights'].append({'head': 1.})
        return ids
    side = [abs(dx) for dx, dz in dirs]
    brim = [t['brim_side']*s+t['brim_fore']*(1-s) for s in side]
    curl = [t['brim_curl']*s*s for s in side]
    th = t['thickness']
    inner = ring([r-th for r in seat_r], lambda k: seat+.002)
    under_out = ring([r+b for r, b in zip(seat_r, brim)], lambda k: seat-.003+curl[k])
    edge = ring([r+b+.003 for r, b in zip(seat_r, brim)], lambda k: seat+curl[k]+th*.3)
    over_out = ring([r+b for r, b in zip(seat_r, brim)], lambda k: seat+th+curl[k])
    crown = [ring([r*f for r in seat_r], (lambda yy: (lambda k: yy))(seat+th+H*h)) for h, f in profile]
    rings = [inner, under_out, edge, over_out]+crown
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            for f in ([a, c, b], [a, d, c]):
                out['triangles'].append(f)
    apex = len(out['positions_m'])
    out['positions_m'].append([cx, seat+th+H, cz]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([crown[-1][k], apex, crown[-1][(k+1) % n]])
    # Close the inside: a felt lining disk just above the skull's top keeps the hat solid.
    lining_y = top+.004
    lining = ring([r*.55 for r in seat_r], lambda k: lining_y)
    for k in range(n):
        a, b, c, d = inner[k], inner[(k+1) % n], lining[(k+1) % n], lining[k]
        for f in ([a, b, c], [a, c, d]):
            out['triangles'].append(f)
    lc = len(out['positions_m']); out['positions_m'].append([cx, lining_y+.004, cz]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([lining[k], lining[(k+1) % n], lc])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='black felt derby', seat_y_m=seat, crown_height_m=H, brim_side_m=t['brim_side'],
                          brim_fore_m=t['brim_fore'], head_bone='head', separate_mesh=True,
                          lift='rigid on the head bone; a renderer may detach it to the right hand socket for a greeting')
    return out


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    shirt_mesh = shirt(body, bones)
    vest = waistcoat(body, bones)
    coat, roll = coat_body(body, bones)
    parts = [shirt_mesh, vest, finish_edges(coat, .0018), lapels(coat, roll), coat_skirt(body, bones, coat, roll[0]),
             trousers(body, bones, height), tie(shirt_mesh, bones, vest['receipt']['v_bottom_y_m']), derby(body, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_gentleman_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; the pictures are monochrome',
                             'No cloth simulation: shells and skirts follow the body bones (skirt fronts each go with their own leg)',
                             'Hat rigid on the head bone; lifting it is a renderer action, not a clip'])


def prepare_gentleman_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3441; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('gentleman_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_gentleman_1904.py',
         'unsupported gentleman component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'gentleman assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'gentleman scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed gentleman body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'gentleman components require the declared liberty')
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
    bundle = construct(body)
    bundle['liberty'] = LIBERTY
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']]
    for material, m in bundle['materials'].items():
        need(recipe['colors_linear_rgba'].get(material) == m['base_color_linear'], f'{material}: recipe/source colour differs')
    names = {b['name'] for b in body['skeleton']}
    for mesh in bundle['meshes']:
        count = len(mesh['positions_m'])
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
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    data = construct(json.loads(raw))
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles'])} for m in data['meshes']]}, indent=1))
