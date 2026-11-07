# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 lady's day dress on the shared portable female rig (T-3447).

First worn by Frances M. Glessner (1848-1932), wife of John J. Glessner, 56 in 1904. The
pieces, read from the period pictures in the recipe (data/humans/recipes/lady_1904.json):

  shirtwaist     white, with a tall boned standing collar close up the neck; only what the
                 jacket leaves showing is made (the collar and the front in the jacket's V),
                 with a lace jabot falling from the collar (Mrs. Fairbanks and the matrons
                 beside her, Johnston, 1905; the 1902 suit's lace bodice, the Met)
  jacket         black wool, fitted, long sleeves, closed below the bust with narrow revers
                 above, and a basque below the waist to the upper thigh (the 1902 suit's coat,
                 the Met; Mrs. Fairbanks's coat, 1905)
  skirt          black wool, gored (seven gores), close over the hips and flaring from the
                 knee to a hem just clear of the ground (the 1902 suit's skirt; the women on
                 Fifth Avenue, Easter 1904)
  hat            black, with a wide brim tilted a little forward and a crown trimmed with
                 plumes (the matrons, 1905; Easter 1904), perched over the drawn-up hair. A
                 separate mesh rigidly on the head bone (material `headwear__lady_hat_black`),
                 its trim a mesh of its own (`accessory__lady_hat_plumes`).

Generated geometry is CC0-1.0. Cuts, eases, lengths and every colour but the suit's black are
reconstructed; liberty L-human-modular-dress-1789 with its T-3447 supplement. The source anatomy
is never changed: every piece is either a shell offset from the body's own triangles (its UVs
and skin weights carried) or a loft round the body's own cross-sections, skinned to the body's
own bones.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_lady_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty, leg_follow
from human_workwear_fit import _clip, _slab_points
from human_period_wardrobe import finish_edges
import human_gentleman_1904 as G

BODY_SHA256 = '3060ee86957ff7c2d70c89e70fe95ff3bc2294a0d7f6a5716b5a2f3f8dd84c72'
ASSEMBLY = 'lady_1904_v1'
RECIPE = 'data/humans/recipes/lady_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirtwaist=dict(ease=.007, collar=.046, front_margin=.032),
    jabot=dict(top_below_collar=.012, length=.13, width_top=.034, width_bottom=.05, pleats=7, depth=.006, standoff=.003),
    jacket=dict(ease=.021, smooth_iterations=40, armpit_extra=.016, waist_below_spine02=.018,
                collar_above_neck=.010, sleeve_short_of_wrist=.022, roll_above_spine02=.150,
                v_half_width_top=.046, revers_width=.036, revers_notch=.78),
    basque=dict(length=.17, ease=.009, flare=.022, front_gap_deg=1.0, segments=84, rows=8),
    skirt=dict(hem_y=.030, ease=.010, flare_from_y=.70, hem_rx=.36, hem_rz_front=.30, hem_rz_back=.36,
               gores=7, gore_depth=.011, segments=84, rows=24),
    hat=dict(seat_below_hair_top=.045, tilt_deg=9., ease=.006, crown_height=.085, crown_taper=.80,
             brim_front=.075, brim_side=.070, brim_back=.050, brim_droop=.012, thickness=.004),
    plumes=dict(count=4, width=.06, rise=.04, sweep_deg=80.),
)

MATERIALS = {
    'garment_upper__lady_shirtwaist_white': {'base_color_linear': [.78, .77, .73, 1], 'roughness': .72},
    'garment_outer__lady_jacket_black': {'base_color_linear': [.016, .016, .019, 1], 'roughness': .82},
    'garment_lower__lady_skirt_black': {'base_color_linear': [.018, .018, .021, 1], 'roughness': .86},
    'headwear__lady_hat_black': {'base_color_linear': [.014, .013, .014, 1], 'roughness': .7},
    'accessory__lady_hat_plumes': {'base_color_linear': [.20, .19, .20, 1], 'roughness': .9},
    'footwear__lady_shoes_black': {'base_color_linear': [.012, .011, .011, 1], 'roughness': .4},
}
SHOE_MATERIAL = 'footwear__lady_shoes_black'
WEAVE_MATERIAL = 'garment_upper__lady_shirtwaist_white'


def _bones(body):
    return {b['name']: b for b in body['skeleton']}


def _keep(mesh, test, name=None, material=None):
    """A copy of `mesh` holding only the triangles whose corners pass `test` (a function of
    the three corner positions); unreferenced vertices are dropped."""
    P = mesh['positions_m']
    out = empty(name or mesh['name'], material or mesh['material'])
    index = {}
    for f, corner in zip(mesh['triangles'], mesh['corner_uvs']):
        if not test([P[i] for i in f]):
            continue
        ids = []
        for i in f:
            if i not in index:
                index[i] = len(out['positions_m'])
                out['positions_m'].append(list(P[i])); out['uvs'].append(list(mesh['uvs'][i]))
                out['weights'].append(dict(mesh['weights'][i]))
            ids.append(index[i])
        out['triangles'].append(ids); out['corner_uvs'].append([list(c) for c in corner])
    need(bool(out['triangles']), f'nothing kept of {out["name"]}')
    return out


def shirtwaist(body, bones, waist):
    """The white shirtwaist with its tall standing collar: a shell off the body's own surface
    from the jacket's V to a collar close up the neck, lightly smoothed across the hollow of
    the chest. Only what the jacket leaves showing is made: the collar all round and the
    front inside the V, with a margin tucked under the jacket's edges. A whole shirtwaist
    under a closed jacket only pokes through it as the arms come down."""
    t = TAILORING['shirtwaist']
    neck = bones['neck_01']['head_m'][1]
    spine = bones['spine_02']['head_m'][1]
    centre = bones['spine_02']['head_m'][2]
    j = TAILORING['jacket']
    vb = spine+j['roll_above_spine02']
    lo = vb-.012; hi = neck+t['collar']
    slope = j['v_half_width_top']/(neck+j['collar_above_neck']-vb)
    collar_y = neck-.02
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: .2-abs(v['p'][0])]
    def pieces(poly):
        collar = _clip(poly, lambda v: v['p'][1]-collar_y)
        front = _clip(_clip(_clip(poly, lambda v: collar_y-v['p'][1]), lambda v: v['p'][2]-centre),
                      lambda v: slope*max(0., v['p'][1]-vb)+t['front_margin']-abs(v['p'][0]))
        return [collar, front]
    out = G._poly_shell(body, bones, 'lady_shirtwaist_collar', 'garment_upper__lady_shirtwaist_white', fields, t['ease'],
                        [(lo, hi)], neck, pieces, smooth=(10, t['ease']))
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='white shirtwaist, tall standing collar; collar and front only',
                          collar_top_y_m=hi, front_from_y_m=lo, ease_m=t['ease'], source_body_mutated=False)
    return out


def jabot(shirt, bones):
    """A lace jabot: a pleated frill falling from the foot of the collar down the shirtwaist
    front, widening as it falls, standing a few millimetres off it."""
    t = TAILORING['jabot']
    neck = bones['neck_01']['head_m'][1]
    top = neck+TAILORING['shirtwaist']['collar']-t['top_below_collar']-.02
    bottom = top-t['length']
    out = empty('lace_jabot', 'garment_upper__lady_shirtwaist_white')
    rows, cols = 12, 2*t['pleats']+1
    for r in range(rows):
        s = r/(rows-1); y = top+(bottom-top)*s
        half = (t['width_top']+(t['width_bottom']-t['width_top'])*s**.8)/2
        for c in range(cols):
            u = c/(cols-1); x = -half+2*half*u
            z, w = G._surface_sample(shirt, x, y)
            pleat = t['depth']*(.35+.65*s)*(1 if c % 2 else 0)
            z += t['standoff']+pleat+.004*(1-(2*u-1)**2)*s
            out['positions_m'].append([x, y, z]); out['uvs'].append([u, s]); out['weights'].append(w)
    for r in range(rows-1):
        for c in range(cols-1):
            a = r*cols+c; b = a+1; d = a+cols; e = d+1
            for f in ([a, e, b], [a, d, e]):
                out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][i] for i in f])
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='lace jabot', top_y_m=top, bottom_y_m=bottom, pleats=t['pleats'])
    return out


def jacket_body(body, bones):
    """The jacket above its waist seam: a shell off the body, smoothed so it spans the bust
    and the hollow beneath it the way a boned, lined jacket does, eased under the arms, open
    in a V from below the bust to a low standing collar."""
    t = TAILORING['jacket']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['waist_below_spine02']; hi = neck+t['collar_above_neck']
    cuff = abs(bones['hand_l']['head_m'][0])-t['sleeve_short_of_wrist']
    vb = spine+t['roll_above_spine02']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: cuff-v['p'][0], lambda v: cuff+v['p'][0]]
    out = G._poly_shell(body, bones, 'lady_jacket_body', 'garment_outer__lady_jacket_black', fields, t['ease'],
                        [(lo, hi)], neck, G._v_pieces(vb, t['v_half_width_top'], hi), smooth=(t['smooth_iterations'], t['ease']-.002))
    loose = G._armpit_ease(out, body, bones, t['armpit_extra'])
    out['receipt'] = dict(garment='fitted jacket body and sleeves', armpit_points_eased=loose, waist_seam_y_m=lo,
                          collar_y_m=hi, v_bottom_y_m=vb, sleeve_end_x_m=cuff)
    return out, (lo, vb, hi)


def revers(jacket, roll):
    """Narrow revers turned back along the jacket's V, from the bottom of the V to the
    collar, widening to a notch near the top: a strip 3 mm proud of the jacket, skinned as
    the jacket beneath it."""
    t = TAILORING['jacket']
    lo, vb, hi = roll
    out = empty('lady_jacket_revers', 'garment_outer__lady_jacket_black')
    rows, cols = 14, 5
    slope = t['v_half_width_top']/(hi-vb)
    for sign in (1, -1):
        base = len(out['positions_m'])
        for r in range(rows):
            s = r/(rows-1)
            y = vb+s*(hi-vb-.006)
            edge = slope*(y-vb)
            for _ in range(40):
                try:
                    G._surface_sample(jacket, sign*(edge+.002), y); break
                except ValueError:
                    edge += .002
            ramp = min(1., s/t['revers_notch'])
            width = max(.006, t['revers_width']*(ramp*(2-ramp))*(1. if s <= t['revers_notch'] else .5))
            for c in range(cols):
                u = c/(cols-1)
                x = sign*(edge+.002+u*width)
                while True:
                    try:
                        z, w = G._surface_sample(jacket, x, y); break
                    except ValueError:
                        need(abs(x) > edge, 'revers have no jacket beneath them')
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
    out['receipt'] = dict(garment='narrow revers', v_bottom_y_m=vb, width_m=t['revers_width'])
    return out


def _section(mesh, y):
    """The (x, z) segments where `mesh` crosses the plane at height y."""
    segs = []
    for face in mesh['triangles']:
        tri = [mesh['positions_m'][i] for i in face]
        if min(p[1] for p in tri) <= y <= max(p[1] for p in tri):
            pts = list(dict.fromkeys(tuple(p) for p in _slab_points([tri], y, y)))
            if len(pts) == 2:
                segs.append(pts)
    return segs


def _ray_radius(segs, dx, dz):
    """The farthest crossing, from the vertical axis outward along (dx, dz), of `segs`."""
    best = None
    for a, b in segs:
        ux, uz = b[0]-a[0], b[2]-a[2]
        den = ux*dz-uz*dx
        if abs(den) < 1e-14:
            continue
        t = -(a[0]*dz-a[2]*dx)/den
        if -1e-9 <= t <= 1+1e-9:
            r = (a[0]+t*ux)*dx+(a[2]+t*uz)*dz
            if r > 0 and (best is None or r > best):
                best = r
    return best


def skirt(body, bones, top, jacket):
    """The gored skirt: a loft from the waist seam to a hem just clear of the ground, round
    convex supports that enclose the body's own sections (below the widest, no ring is
    narrower than the one above it), flaring below `flare_from_y` toward an elliptical hem,
    each of its seven gores full between its seams. Skinned with the leg-following skirt
    weights of T-3423, so a striding leg carries the cloth over it."""
    t = TAILORING['skirt']
    segs, rows, ease, hem = t['segments'], t['rows'], t['ease'], t['hem_y']
    top_y = top+.006
    levels = [top_y+(hem-top_y)*i/(rows-1) for i in range(rows)]
    tris = [[m['positions_m'][i] for i in f] for m in body['meshes'] for f in m['triangles']
            if min(m['positions_m'][i][1] for i in f) <= top_y+.02 and max(m['positions_m'][i][1] for i in f) >= hem-.02]
    dirs = [(math.sin(2*math.pi*k/segs), math.cos(2*math.pi*k/segs)) for k in range(segs)]
    supports = []
    for i in range(rows):
        pts = _slab_points(tris, levels[min(rows-1, i+1)]-.004, levels[max(0, i-1)]+.004)
        need(len(pts) >= 3, 'empty skirt band')
        supports.append([max(nx*p[0]+nz*p[2] for p in pts)+ease for nx, nz in dirs])
    widest = max(range(rows), key=lambda i: sum(supports[i]))
    for i in range(widest+1, rows):
        supports[i] = [max(a, .998*b) for a, b in zip(supports[i], supports[i-1])]
    for i in range(rows):
        s = supports[i]
        supports[i] = [max(s[k], (s[k-1]+2*s[k]+s[(k+1) % segs])/4) for k in range(segs)]
    # The flare: toward the hem the ring opens to an ellipse, fuller behind (the sweep of
    # the decade's skirts), the two blended smoothly so no crease marks where it begins.
    start = t['flare_from_y']
    def flare(y, nx, nz):
        f = min(1., max(0., (start-y)/(start-hem)))
        rz = t['hem_rz_front'] if nz > 0 else t['hem_rz_back']
        ell = 1/math.sqrt((nx/t['hem_rx'])**2+(nz/rz)**2)
        return f, ell
    ring_r = []
    for i, y in enumerate(levels):
        row = []
        for k, (nx, nz) in enumerate(dirs):
            base = supports[i][k]
            f, ell = flare(y, nx, nz)
            want = base+(max(base, ell)-base)*(f*f*(3-2*f))
            # Gores: each panel full between its seams, the fullness growing to the hem.
            u = (k*t['gores']/segs) % 1.
            want += t['gore_depth']*f**1.3*.5*(1-math.cos(2*math.pi*u))
            row.append(want)
        ring_r.append(row)
    # The top ring tucks just inside the jacket's own section at its seam.
    jsec = _section(jacket, top_y+.008)
    if jsec:
        for k, (nx, nz) in enumerate(dirs):
            r = _ray_radius(jsec, nx, nz)
            if r:
                ring_r[0][k] = min(ring_r[0][k], r-.002)
    out = empty('gored_skirt', 'garment_lower__lady_skirt_black')
    follow = leg_follow(bones, top)
    for i, y in enumerate(levels):
        for k, (nx, nz) in enumerate(dirs):
            r = ring_r[i][k]
            p = [nx*r, y, nz*r]
            out['positions_m'].append(p); out['uvs'].append([k/segs, i/(rows-1)]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for k in range(segs):
            n = (k+1) % segs
            a = i*segs+k; b = i*segs+n; c = (i+1)*segs+n; d = (i+1)*segs+k
            for face in ([a, b, c], [a, c, d]):
                out['triangles'].append(face)
                out['corner_uvs'].append([[(k+(1 if v in (b, c) else 0))/segs, (v//segs)/(rows-1)] for v in face])
    # Standing clearance: every body point of a band lies inside its ring.
    worst = math.inf
    step = 2*math.pi/segs
    for i in range(rows-1):
        for p in _slab_points(tris, levels[i+1], levels[i]):
            th = math.atan2(p[0], p[2]) % (2*math.pi)
            k = int(th/step) % segs
            q = (p[1]-levels[i])/(levels[i+1]-levels[i])
            rr = min((1-q)*ring_r[i][j]+q*ring_r[i+1][j] for j in (k, (k+1) % segs))
            worst = min(worst, rr-math.hypot(p[0], p[2]))
    need(worst > .004, f'skirt meets the standing body ({worst:.4f} m)')
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='gored skirt to the ground', hem_y_m=hem, top_y_m=top_y, ease_m=ease, gores=t['gores'],
                          flare_from_y_m=start, minimum_standing_body_clearance_m=worst,
                          skinning='pelvis at the waist, shared with the thigh and calf of each side below it (leg_follow, T-3423)')
    return out, (levels, dirs, ring_r)


def basque(bones, top, jacket, skirt_rings):
    """The jacket's basque below its waist seam, to the upper thigh: a loft just outside the
    skirt's own rings, opening a little toward its hem, skinned as the skirt is so the two
    move together; open at the front where the jacket's fronts meet."""
    t = TAILORING['basque']
    levels, dirs_s, rings = skirt_rings
    segs, rows = t['segments'], t['rows']
    need(segs == len(dirs_s), 'basque and skirt share their directions')
    top_y = top+.006; hem = top-t['length']
    lv = [top_y+(hem-top_y)*i/(rows-1) for i in range(rows)]
    gap = math.radians(t['front_gap_deg'])
    angles = [gap+(2*math.pi-2*gap)*k/(segs-1) for k in range(segs)]
    def skirt_r(y, a):
        # The skirt's ring radius at height y and angle a, interpolated in both.
        j = min(len(levels)-2, max(0, next((n for n in range(len(levels)-1) if levels[n+1] <= y), len(levels)-2)))
        q = min(1., max(0., (levels[j]-y)/(levels[j]-levels[j+1])))
        s = a/(2*math.pi)*segs; k = int(s) % segs; f = s-int(s)
        r0 = rings[j][k]*(1-f)+rings[j][(k+1) % segs]*f
        r1 = rings[j+1][k]*(1-f)+rings[j+1][(k+1) % segs]*f
        return r0*(1-q)+r1*q
    jsec = _section(jacket, top_y+.008)
    out = empty('lady_jacket_basque', 'garment_outer__lady_jacket_black')
    follow = leg_follow(bones, top)
    for i, y in enumerate(lv):
        f = i/(rows-1)
        for k, a in enumerate(angles):
            nx, nz = math.sin(a), math.cos(a)
            r = skirt_r(y, a)+t['ease']+t['flare']*f**1.5
            if i == 0 and jsec:
                jr = _ray_radius(jsec, nx, nz)
                if jr:
                    r = min(r, jr-.0015)
            p = [nx*r, y, nz*r]
            out['positions_m'].append(p); out['uvs'].append([k/(segs-1), f]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for k in range(segs-1):
            a = i*segs+k; b = a+1; c = a+segs+1; d = a+segs
            for face in ([a, b, c], [a, c, d]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][j] for j in face])
    margin = min(math.hypot(p[0], p[2])-skirt_r(p[1], math.atan2(p[0], p[2]) % (2*math.pi))
                 for p in out['positions_m'][segs:])
    need(margin > .005, f'basque meets the skirt ({margin:.4f} m)')
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='jacket basque to the upper thigh', top_y_m=top_y, hem_y_m=hem,
                          minimum_skirt_clearance_m=margin, front_gap_deg=t['front_gap_deg'])
    return out


def _hat_frame(bones, hair, t):
    """The hat's seat: a centre over the hair, a height, and a forward tilt. Returns a pair of
    functions taking a point to and from the hat's own frame (y up its crown)."""
    Q = hair['positions_m']
    top = max(p[1] for p in Q)
    seat = top-t['seat_below_hair_top']
    band = [p for p in Q if p[1] >= seat-.01]
    cx = (min(p[0] for p in band)+max(p[0] for p in band))/2
    cz = (min(p[2] for p in band)+max(p[2] for p in band))/2+.01
    a = math.radians(t['tilt_deg'])          # front down: a turn about +x
    ca, sa = math.cos(a), math.sin(a)
    def to_hat(p):
        x, y, z = p[0]-cx, p[1]-seat, p[2]-cz
        return [x, ca*y+sa*z, -sa*y+ca*z]
    def from_hat(q):
        x, y, z = q
        return [x+cx, ca*y-sa*z+seat, sa*y+ca*z+cz]
    return to_hat, from_hat, dict(centre_m=[cx, seat, cz], hair_top_y_m=top)


def hat(body, bones, hair, lod=0):
    """A black hat perched over the drawn-up hair: a low crown seated round the hair's own
    section in the hat's tilted frame, a wide brim drooping a little at its edge, wider in
    front and at the sides than behind. The seat clears the scalp as well as the hair, since
    the tilt brings the front of the brim down to the brow. Rigid on the head bone, a
    separate mesh."""
    t = TAILORING['hat']
    to_hat, from_hat, seat = _hat_frame(bones, hair, t)
    H = [to_hat(p) for p in hair['positions_m']]
    head_y = bones['head']['head_m'][1]
    scalp = [to_hat(p) for p in body['meshes'][0]['positions_m'] if p[1] > head_y]
    above = [p for p in H+scalp if p[1] >= -.012]
    n = (48, 32, 24, 16)[lod]
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    seat_r = [max(dx*p[0]+dz*p[2] for p in above)+t['ease'] for dx, dz in dirs]
    seat_r = [(seat_r[k-1]+2*seat_r[k]+seat_r[(k+1) % n])/4+.002 for k in range(n)]
    crown_top = max(p[1] for p in above)+.012
    hgt = max(t['crown_height'], crown_top)
    out = empty('headwear_lady_hat', 'headwear__lady_hat_black')
    def ring(radii, ys):
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            ids.append(len(out['positions_m']))
            out['positions_m'].append(from_hat([radii[k]*dx, ys[k], radii[k]*dz]))
            out['uvs'].append([k/n, 0.]); out['weights'].append({'head': 1.})
        return ids
    brim = [t['brim_side']*abs(dx)+(t['brim_front'] if dz > 0 else t['brim_back'])*abs(dz) for dx, dz in dirs]
    th = t['thickness']; droop = t['brim_droop']
    inner = ring([r-th for r in seat_r], [.0]*n)
    mid_u = ring([r+.55*b for r, b in zip(seat_r, brim)], [-.003-.3*droop]*n)
    under = ring([r+b for r, b in zip(seat_r, brim)], [-.003-droop]*n)
    edge = ring([r+b+.003 for r, b in zip(seat_r, brim)], [-droop+th*.3]*n)
    over = ring([r+b for r, b in zip(seat_r, brim)], [th-droop]*n)
    mid_o = ring([r+.55*b for r, b in zip(seat_r, brim)], [th-.3*droop]*n)
    base = ring(seat_r, [th]*n)
    profile = [(.25, 1.02), (.55, 1.04), (.8, 1.0), (.93, .93), (1., t['crown_taper'])]
    crown = [ring([r*f for r in seat_r], [th+hgt*h]*n) for h, f in profile]
    rings = [inner, mid_u, under, edge, over, mid_o, base]+crown
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    apex = len(out['positions_m'])
    out['positions_m'].append(from_hat([0., th+hgt+.004, 0.])); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([crown[-1][k], apex, crown[-1][(k+1) % n]])
    # Close the inside just above the hair, so the hat reads solid from below.
    lining = ring([r*.6 for r in seat_r], [crown_top-.004]*n)
    for k in range(n):
        a, b, c, d = inner[k], inner[(k+1) % n], lining[(k+1) % n], lining[k]
        out['triangles'] += [[a, b, c], [a, c, d]]
    lc = len(out['positions_m']); out['positions_m'].append(from_hat([0., crown_top, 0.])); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([lining[k], lining[(k+1) % n], lc])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    clearance = min(math.dist(p, q) for p in [out['positions_m'][i] for i in inner] for q in hair['positions_m'])
    out['receipt'] = dict(garment='wide-brimmed hat', seat=seat, tilt_deg=t['tilt_deg'], crown_height_m=hgt,
                          brim_m=dict(front=t['brim_front'], side=t['brim_side'], back=t['brim_back']),
                          head_bone='head', separate_mesh=True, seat_ring_hair_clearance_m=clearance)
    return out, (to_hat, from_hat, seat_r, dirs, hgt)


def plumes(frame, lod=0):
    """The hat's trim: curled plumes laid round the crown from the front left over to the
    back, each a lens-shaped strip arching up and out from the crown and falling over the
    brim, rigid on the head bone."""
    t = TAILORING['plumes']
    to_hat, from_hat, seat_r, dirs, hgt = frame
    n = len(dirs)
    th = TAILORING['hat']['thickness']
    def crown_r(a):
        s = (a/(2*math.pi)) % 1*n; k = int(s) % n; f = s-int(s)
        return seat_r[k]*(1-f)+seat_r[(k+1) % n]*f
    out = empty('lady_hat_plumes', 'accessory__lady_hat_plumes')
    rows, cols = (16, 7) if lod < 2 else (8, 3)
    half_th = .0015                          # each plume is two skins this far either side
    for j in range(t['count']):
        a0 = math.radians(25+40*j)          # from the front left, round the left side
        for side in (1, -1):                # the outer skin, then the inner one wound the other way
            base = len(out['positions_m'])
            for r in range(rows):
                s = r/(rows-1)
                a = a0+math.radians(t['sweep_deg'])*s   # sweeping back round the crown
                arch = math.sin(math.pi*s)
                radius = crown_r(a)*(1.0-.05*arch)+.012+.035*s
                y = th+hgt*(.45+.12*j/t['count'])+t['rise']*arch-.035*s*s
                half = t['width']/2*math.sin(math.pi*min(1., .12+.88*s))**.6*(1-.25*j/t['count'])
                dx, dz = math.sin(a), math.cos(a)
                for c in range(cols):
                    u = c/(cols-1)
                    off = (2*u-1)*half
                    curl = .02*(1-(2*u-1)**2)+side*half_th*(1-(2*u-1)**2)
                    q = [(radius+curl)*dx, y+off*.8, (radius+curl)*dz]
                    out['positions_m'].append(from_hat(q)); out['uvs'].append([u, s]); out['weights'].append({'head': 1.})
            for r in range(rows-1):
                for c in range(cols-1):
                    a = base+r*cols+c; b = a+1; d = a+cols; e = d+1
                    out['triangles'] += [[a, e, b], [a, d, e]] if side > 0 else [[a, b, e], [a, e, d]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='plume trim', count=t['count'], double_sided=True, skins_apart_m=2*half_th, head_bone='head')
    return out


def construct(body, hair):
    before = digest(body)
    bones = _bones(body)
    spine = bones['spine_02']['head_m'][1]
    waist = spine-TAILORING['jacket']['waist_below_spine02']
    shirt = shirtwaist(body, bones, waist)
    jacket, roll = jacket_body(body, bones)
    skirt_mesh, rings = skirt(body, bones, waist, jacket)
    hat_mesh, frame = hat(body, bones, hair)
    parts = [shirt, jabot(shirt, bones), finish_edges(jacket, .0018), revers(jacket, roll),
             basque(bones, waist, jacket, rings), skirt_mesh, hat_mesh, plumes(frame)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_lady_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours other than the black are reconstructed',
                             'No cloth simulation: shells follow the body; skirt and basque share the leg-following skirt weights',
                             'Hat and plumes rigid on the head bone, seated over the fitted bun hair'])


def prepare_lady_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3447; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('lady_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_lady_1904.py',
         'unsupported lady component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'lady assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'lady scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed lady body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'lady components require the declared liberty')
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
    need(recipe['hair_component'].get('fitter') == 'mhclo_proxy', 'the hat is seated over the fitted bun hair')
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
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]}, indent=1))
