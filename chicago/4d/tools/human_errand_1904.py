# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 parlor maid's street dress on an errand, on the shared portable female rig (T-3481).

First worn by Christine Nelson, parlor maid in the Glessner household at 1800 Prairie Avenue
in the 1900 census (born March 1873 in Sweden, came 1892), walking round the block as if back
from market. Out of the house a maid left off her apron and cap and went in the street dress
every working woman of the decade wore. The pieces, read from the period pictures in the recipe
(data/humans/recipes/errand_1904.json):

  shirtwaist   white cotton, pouched over the belt in front, full in the upper sleeve, with
               a tall standing collar and narrow cuffs (the American cotton shirtwaist of about
               1900, the Met; the striking shirtwaist workers, Bain, 1909)
  necktie      a small dark bow at the front of the collar (the Wasson young woman's dark tie,
               1903; the shirtwaist workers)
  belt         a narrow black belt at the waist, over the top of the skirt
  skirt        a dark serge walking skirt of seven gores, close over the hips and flaring a
               little to a hem clear of the ground at the ankle (the shirtwaist workers; the
               women on State Street, 1903)
  boater       a straw sailor hat, flat crown and straight brim, with a black ribbon round the
               crown, set straight on the drawn-up hair (the American straw hat of about 1900,
               the Met; the shirtwaist workers). A separate mesh rigidly on the head bone
               (`headwear__errand_boater_straw`), its ribbon a mesh of its own
  basket       a willow market basket with a cloth over what she bought, carried by its handle
               in the left hand, the arm held a little out from the skirt
               (`accessory__market_basket`, `accessory__basket_cloth`), rigid on the hand bone,
               laid so that it hangs straight when human-actions.js holds the hand as CARRY
               below says (the recipe's `carry`, written into the asset for the renderer)

Generated geometry is CC0-1.0. The shirtwaist is the dress components of T-3423 and T-3434
(tools/human_dress_components.py) re-cut; the gored skirt follows the 1904 lady's (T-3447) cut
narrower and shorter; the rest is drawn here. Amounts and every colour are reconstructed (the
pictures are monochrome or of single garments); liberty L-human-modular-dress-1789 with its
T-3481 supplement. The source anatomy is never changed.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_errand_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty, bodice, blouse, leg_follow
from human_workwear_fit import _slab_points
from human_period_wardrobe import finish_edges
from human_lady_1904 import _section, _ray_radius
from human_maid_1904 import _two_sided

BODY_SHA256 = '3060ee86957ff7c2d70c89e70fe95ff3bc2294a0d7f6a5716b5a2f3f8dd84c72'
ASSEMBLY = 'errand_1904_v1'
RECIPE = 'data/humans/recipes/errand_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirtwaist=dict(ease=.012, collar=.042, waist_below_spine02=.018, pouch=.024, pouch_height=.09, sleeve=.02),
    cuffs=dict(length=.05, lift=.0025),
    tie=dict(below_collar_top=.03, loop=.032, loop_height=.022, tail=.05, standoff=.004),
    belt=dict(height=.028, lift=.004),
    skirt=dict(hem_y=.075, ease=.02, follow_below_top=.06, flare_from_y=.62, hem_rx=.30, hem_rz_front=.27, hem_rz_back=.31,
               gores=7, gore_depth=.009, segments=84, rows=24),
    boater=dict(seat_below_hair_top=.052, ease=.006, crown_height=.072, brim=.068, thickness=.004, band=.028),
    basket=dict(length=.34, width=.21, depth=.12, bottom_scale=.82, handle_rise=.16, handle_radius=.0075,
                cloth_dome=.03, cloth_drape=.035, segments=40),
)

# How the renderer holds the hand the basket hangs from (renderers/web/js/human-actions.js
# `carry`), in the figure's own frame (+x her left, +y up, +z forward), metres from the
# shoulder joint: the wrist a little out from the skirt and the fingers down round the
# handle, palm to the thigh. The basket is laid in the bind pose so that, in this hold, it
# hangs straight.
CARRY = dict(side='l', wrist_from_shoulder=[.205, -.39, .05], elbow_pole=[.7, -.1, -.7],
             fingers=[.10, -1., .06], palm=[-1., 0., 0.], grip_from_wrist=.08, grip_toward_palm=.02, curl=.75)

MATERIALS = {
    'garment_upper__errand_shirtwaist_white': {'base_color_linear': [.80, .79, .75, 1], 'roughness': .74},
    'garment_lower__errand_skirt_navy': {'base_color_linear': [.020, .024, .046, 1], 'roughness': .86},
    'garment_outer__errand_belt_black': {'base_color_linear': [.014, .013, .013, 1], 'roughness': .5},
    'garment_outer__errand_tie_black': {'base_color_linear': [.016, .016, .02, 1], 'roughness': .7},
    'headwear__errand_boater_straw': {'base_color_linear': [.50, .40, .22, 1], 'roughness': .8},
    'headwear__errand_boater_ribbon': {'base_color_linear': [.014, .014, .016, 1], 'roughness': .55},
    'accessory__market_basket': {'base_color_linear': [.28, .19, .095, 1], 'roughness': .85},
    'accessory__basket_cloth': {'base_color_linear': [.66, .65, .60, 1], 'roughness': .85},
    'footwear__errand_shoes_black': {'base_color_linear': [.012, .011, .011, 1], 'roughness': .42},
}
SHOE_MATERIAL = 'footwear__errand_shoes_black'
WEAVE_MATERIAL = 'garment_upper__errand_shirtwaist_white'
WHITE = 'garment_upper__errand_shirtwaist_white'


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


def _outward(out, centre_of):
    """Wind every face of `out` so its normal points away from `centre_of(face centroid)`."""
    P = out['positions_m']
    for i, f in enumerate(out['triangles']):
        a, b, c = (P[j] for j in f)
        cen = [(a[k]+b[k]+c[k])/3 for k in range(3)]
        if _dot(_cross(_sub(b, a), _sub(c, a)), _sub(cen, centre_of(cen))) < 0:
            out['triangles'][i] = [f[0], f[2], f[1]]
    out['corner_uvs'] = [[out['uvs'][j] for j in f] for f in out['triangles']]
    return out


def shirtwaist(body, bones, waist):
    t = TAILORING['shirtwaist']
    out = bodice(body, bones, waist, ease=t['ease'], collar=t['collar'])
    out = blouse(out, bones, waist, pouch=t['pouch'], pouch_height=t['pouch_height'], sleeve=t['sleeve'])
    out['name'] = 'errand_shirtwaist'; out['material'] = WHITE
    return out


def cuffs(upper, bones):
    """Narrow white cuffs: the shirtwaist's own triangles over the last `length` of each
    sleeve, copied a little out from the forearm's axis, skinned as the sleeve is there."""
    t = TAILORING['cuffs']
    P = upper['positions_m']
    out = empty('errand_cuffs', WHITE)
    index = {}
    for f, corner in zip(upper['triangles'], upper['corner_uvs']):
        xs = [abs(P[i][0]) for i in f]
        side = 'l' if P[f[0]][0] > 0 else 'r'
        end = abs(bones[f'hand_{side}']['head_m'][0])
        if min(xs) < end-t['length'] or max(xs) > end+.01:
            continue
        ax = bones[f'lowerarm_{side}']['head_m']
        ids = []
        for i in f:
            if i not in index:
                p = P[i]; dy, dz = p[1]-ax[1], p[2]-ax[2]; r = math.hypot(dy, dz)
                need(r > .005, 'cuff point on the forearm axis')
                index[i] = len(out['positions_m'])
                out['positions_m'].append([p[0], p[1]+t['lift']*dy/r, p[2]+t['lift']*dz/r])
                out['uvs'].append(list(upper['uvs'][i])); out['weights'].append(dict(upper['weights'][i]))
            ids.append(index[i])
        out['triangles'].append(ids); out['corner_uvs'].append([list(c) for c in corner])
    need(bool(out['triangles']), 'no sleeve end for the cuffs')
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='white cuffs', length_m=t['length'], lift_m=t['lift'])
    return out


def necktie(upper, bones):
    """A small black bow at the front of the standing collar: two flattened loops and two
    short tails either side of a knot, stood off the collar's front and skinned as the
    collar there (neck_01), double-sided."""
    t = TAILORING['tie']
    neck = bones['neck_01']['head_m']
    top = neck[1]+TAILORING['shirtwaist']['collar']
    y0 = top-t['below_collar_top']
    P = upper['positions_m']
    front = [p for p in P if abs(p[0]) < .012 and abs(p[1]-y0) < .008]
    need(bool(front), 'no collar front for the tie')
    z0 = max(p[2] for p in front)+t['standoff']
    w0 = {'neck_01': 1.}
    out = empty('errand_necktie', 'garment_outer__errand_tie_black')
    def strip(points, width_at, flat_axis):
        base = len(out['positions_m']); n = len(points)
        for i, (x, y, z) in enumerate(points):
            hw = width_at(i/(n-1))
            for e in (-1, 1):
                q = [x, y, z]; q[flat_axis] += e*hw
                out['positions_m'].append(q); out['uvs'].append([(e+1)/2, i/(n-1)]); out['weights'].append(dict(w0))
        for i in range(n-1):
            a = base+2*i; b = a+1; c = a+3; d = a+2
            out['triangles'] += [[a, b, c], [a, c, d]]
    for side in (1, -1):
        loop = [(side*(.004+t['loop']*math.sin(math.pi*s)*.9), y0+.003*math.sin(2*math.pi*s), z0+.006*math.sin(math.pi*s))
                for s in [i/10 for i in range(11)]]
        strip(loop, lambda s: t['loop_height']/2*(.4+.6*math.sin(math.pi*s)), 1)
        tail = [(side*(.004+.012*s), y0-.004-t['tail']*s, z0+.002) for s in [i/6 for i in range(7)]]
        strip(tail, lambda s: .007+.004*s, 0)
    kb = len(out['positions_m'])
    for i in range(8):
        a = 2*math.pi*i/8
        out['positions_m'].append([.007*math.cos(a), y0+.008*math.sin(a), z0+.009]); out['uvs'].append([.5, .5]); out['weights'].append(dict(w0))
    kc = len(out['positions_m']); out['positions_m'].append([0., y0, z0+.012]); out['uvs'].append([.5, .5]); out['weights'].append(dict(w0))
    for i in range(8):
        out['triangles'].append([kb+i, kb+(i+1) % 8, kc])
    out = _two_sided(out)
    out['receipt'] = dict(garment='black bow at the collar', y_m=y0, z_m=z0, double_sided=True, skinning='neck_01')
    return out


def skirt(body, bones, top, shirt):
    """The gored walking skirt: a loft from just above the shirtwaist's foot to a hem clear of
    the ground, round convex supports enclosing the body's own sections, flaring a little
    below `flare_from_y` toward an elliptical hem, each of its gores full between its seams;
    its top ring stands just outside the shirtwaist there, so the shirtwaist is tucked in.
    Skinned with the leg-following skirt weights of T-3423."""
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
    start = t['flare_from_y']
    ring_r = []
    for i, y in enumerate(levels):
        row = []
        f = min(1., max(0., (start-y)/(start-hem)))
        for k, (nx, nz) in enumerate(dirs):
            base = supports[i][k]
            rz = t['hem_rz_front'] if nz > 0 else t['hem_rz_back']
            ell = 1/math.sqrt((nx/t['hem_rx'])**2+(nz/rz)**2)
            want = base+(max(base, ell)-base)*(f*f*(3-2*f))
            u = (k*t['gores']/segs) % 1.
            want += t['gore_depth']*f**1.3*.5*(1-math.cos(2*math.pi*u))
            row.append(want)
        ring_r.append(row)
    # The top ring stands just outside the shirtwaist (tucked in under it).
    ssec = _section(shirt, top_y)
    for k, (nx, nz) in enumerate(dirs):
        r = _ray_radius(ssec, nx, nz) if ssec else None
        if r:
            ring_r[0][k] = max(ring_r[0][k], r+.003)
    out = empty('walking_skirt', 'garment_lower__errand_skirt_navy')
    # The legs take the cloth only from below the belly, so a stride never pulls the skirt's
    # front in under the belt (T-3481: the body showed through there walking).
    follow = leg_follow(bones, top-t['follow_below_top'])
    for i, y in enumerate(levels):
        for k, (nx, nz) in enumerate(dirs):
            r = ring_r[i][k]
            p = [nx*r, y, nz*r]
            out['positions_m'].append(p); out['uvs'].append([k/segs, i/(rows-1)]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for k in range(segs):
            n = (k+1) % segs
            a = i*segs+k; b = i*segs+n; c = (i+1)*segs+n; d = (i+1)*segs+k
            for face in ([a, c, b], [a, d, c]):   # wound outward
                out['triangles'].append(face)
                out['corner_uvs'].append([[(k+(1 if v in (b, c) else 0))/segs, (v//segs)/(rows-1)] for v in face])
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
    out['receipt'] = dict(garment='gored walking skirt to the ankle', hem_y_m=hem, top_y_m=top_y, ease_m=ease, gores=t['gores'],
                          flare_from_y_m=start, minimum_standing_body_clearance_m=worst,
                          skinning='pelvis at the waist, shared with the thigh and calf of each side below it (leg_follow, T-3423)')
    return out, (levels, dirs, ring_r)


def belt(shirt, skirt_mesh, top):
    """A narrow black belt round the waist over the skirt's top and the shirtwaist above it,
    standing `lift` off whichever lies outermost at each angle; stiff, one radius per angle."""
    t = TAILORING['belt']
    lo = top+.002; hi = lo+t['height']
    segs = 64
    secs = [_section(shirt, y)+_section(skirt_mesh, y) for y in (lo+.002, hi)]
    radius = []
    for k in range(segs):
        a = 2*math.pi*k/segs; dx, dz = math.sin(a), math.cos(a)
        rs = [r for r in (_ray_radius(s, dx, dz) for s in secs) if r]
        need(bool(rs), 'no garment under the belt')
        radius.append(max(rs)+t['lift'])
    radius = [max(radius[k], (radius[k-1]+radius[k]+radius[(k+1) % segs])/3) for k in range(segs)]
    out = empty('errand_belt', 'garment_outer__errand_belt_black')
    for j, y in enumerate((lo, hi)):
        for k in range(segs):
            a = 2*math.pi*k/segs
            out['positions_m'].append([radius[k]*math.sin(a), y, radius[k]*math.cos(a)])
            out['uvs'].append([k/segs, j]); out['weights'].append({'pelvis': .5, 'spine_01': .5})
    for k in range(segs):
        q = (k+1) % segs
        out['triangles'] += [[k, q, segs+q], [k, segs+q, segs+k]]
    out = _outward(out, lambda c: [0., c[1], 0.])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='narrow black belt', from_y_m=lo, to_y_m=hi, lift_m=t['lift'])
    return out


def boater(body, bones, hair, lod=0):
    """A straw sailor hat set straight on the drawn-up hair: a straight-sided crown seated
    round the hair's own section at the seat (and the scalp's, so it never sinks into the
    head), a flat top, a flat stiff brim of even width all round, and a black ribbon round
    the crown. Rigid on the head bone; the crown and brim one mesh, the ribbon another."""
    t = TAILORING['boater']
    Q = hair['positions_m']
    head_y = bones['head']['head_m'][1]
    top = max(p[1] for p in Q)
    seat = top-t['seat_below_hair_top']
    band = [p for p in Q if p[1] >= seat-.01]
    cx = (min(p[0] for p in band)+max(p[0] for p in band))/2
    cz = (min(p[2] for p in band)+max(p[2] for p in band))/2+.012
    scalp = [p for p in body['meshes'][0]['positions_m'] if p[1] > head_y]
    above = [p for p in Q+scalp if p[1] >= seat-.012]
    n = (48, 32, 24, 16)[lod]
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    seat_r = [max(dx*(p[0]-cx)+dz*(p[2]-cz) for p in above)+t['ease'] for dx, dz in dirs]
    seat_r = [(seat_r[k-1]+2*seat_r[k]+seat_r[(k+1) % n])/4+.002 for k in range(n)]
    # An oval crown, as a hat is blocked: the support's own ellipse, no dents.
    rx = max(seat_r[k]*abs(dirs[k][0]) for k in range(n)); rz = max(seat_r[k]*abs(dirs[k][1]) for k in range(n))
    oval = [max(seat_r[k], 1/math.sqrt((dx/rx)**2+(dz/rz)**2)) for k, (dx, dz) in enumerate(dirs)]
    crown_top = max(p[1] for p in above)+.008
    hgt = max(t['crown_height'], crown_top-seat)
    th = t['thickness']
    straw = empty('headwear_errand_boater', 'headwear__errand_boater_straw')
    def ring(mesh, radii, y, v):
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            ids.append(len(mesh['positions_m']))
            mesh['positions_m'].append([cx+radii[k]*dx, y, cz+radii[k]*dz]); mesh['uvs'].append([k/n, v]); mesh['weights'].append({'head': 1.})
        return ids
    def band_faces(mesh, a_ring, b_ring, ref):
        """Faces between two rings, each wound with its normal away from `ref(centroid)`."""
        P = mesh['positions_m']
        for k in range(n):
            q = (k+1) % n
            for f in ([a_ring[k], b_ring[q], a_ring[q]], [a_ring[k], b_ring[k], b_ring[q]]):
                a, b, c = (P[j] for j in f)
                cen = [(a[i]+b[i]+c[i])/3 for i in range(3)]
                if _dot(_cross(_sub(b, a), _sub(c, a)), _sub(cen, ref(cen))) < 0:
                    f = [f[0], f[2], f[1]]
                mesh['triangles'].append(f)
    above = lambda c: [c[0], c[1]+1., c[2]]
    below = lambda c: [c[0], c[1]-1., c[2]]
    axis = lambda c: [cx, c[1], cz]
    brim = t['brim']
    inner_low = ring(straw, [r-th for r in oval], seat, 0.)
    under = ring(straw, [r+brim for r in oval], seat, .2)
    edge = ring(straw, [r+brim+.002 for r in oval], seat+th/2, .25)
    over = ring(straw, [r+brim for r in oval], seat+th, .3)
    base = ring(straw, oval, seat+th, .4)
    wall_top = ring(straw, [r*.985 for r in oval], seat+th+hgt, .9)
    lip = ring(straw, [r*.95 for r in oval], seat+th+hgt+.002, 1.)
    for a_ring, b_ring, ref in ((inner_low, under, above), (under, edge, axis), (edge, over, axis), (over, base, below),
                                (base, wall_top, axis), (wall_top, lip, below)):
        band_faces(straw, a_ring, b_ring, ref)
    apex = len(straw['positions_m'])
    straw['positions_m'].append([cx, seat+th+hgt+.003, cz]); straw['uvs'].append([.5, 1.]); straw['weights'].append({'head': 1.})
    band_faces(straw, lip, [apex]*n, below)
    # The inside, closed just above the hair so it reads solid from below.
    lining = ring(straw, [r*.6 for r in oval], crown_top-.004, .5)
    band_faces(straw, lining, inner_low, lambda c: [cx, c[1]-.2, cz])
    lc = len(straw['positions_m']); straw['positions_m'].append([cx, crown_top, cz]); straw['uvs'].append([.5, .5]); straw['weights'].append({'head': 1.})
    band_faces(straw, lining, [lc]*n, above)
    straw['triangles'] = [f for f in straw['triangles'] if len(set(f)) == 3]
    straw['corner_uvs'] = [[straw['uvs'][j] for j in f] for f in straw['triangles']]
    # The ribbon: a band just proud of the crown wall from its foot up `band`.
    ribbon = empty('headwear_errand_boater_ribbon', 'headwear__errand_boater_ribbon')
    r0 = ring(ribbon, [r+.0015 for r in oval], seat+th+.001, 0.)
    r1 = ring(ribbon, [r*.997+.0015 for r in oval], seat+th+t['band'], 1.)
    band_faces(ribbon, r0, r1, axis)
    ribbon['corner_uvs'] = [[ribbon['uvs'][j] for j in f] for f in ribbon['triangles']]
    clearance = min(math.dist(straw['positions_m'][i], q) for i in inner_low for q in Q)
    straw['receipt'] = dict(garment='straw sailor hat', seat_y_m=seat, crown_height_m=hgt, brim_m=brim, oval_m=[rx, rz],
                            head_bone='head', separate_mesh=True, seat_ring_hair_clearance_m=clearance)
    ribbon['receipt'] = dict(garment='black ribbon round the crown', height_m=t['band'], head_bone='head', separate_mesh=True)
    return straw, ribbon


def carry_frame(bones):
    """The rotation that turns the left hand from its bind pose into the CARRY hold, as
    human-actions.js orientHand() does: the hand's own `along` (wrist to the middle knuckle)
    to `fingers`, its palm normal (across x along on the left hand) to `palm`. Returns
    (wrist in the bind pose, R as rows) with q_hold = R (p_bind - wrist)."""
    s = CARRY['side']
    wrist = bones[f'hand_{s}']['head_m']
    along = _unit(_sub(bones[f'middle_01_{s}']['head_m'], wrist))
    across = _sub(bones[f'pinky_01_{s}']['head_m'], bones[f'index_01_{s}']['head_m'])
    palm = _cross(across, along) if s == 'l' else _cross(along, across)
    palm = _unit([palm[i]-_dot(palm, along)*along[i] for i in range(3)])
    f = _unit(CARRY['fingers'])
    p = _unit([CARRY['palm'][i]-_dot(CARRY['palm'], f)*f[i] for i in range(3)])
    src = [along, palm, _cross(along, palm)]
    dst = [f, p, _cross(f, p)]
    # R = sum_k dst_k src_k^T
    R = [[sum(dst[k][i]*src[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return wrist, R, dict(fingers=f, palm=p)


def basket(bones):
    """A willow market basket hanging from the left hand by its handle, a cloth laid over what
    is in it: an oval tapered body with a rolled rim, a round handle arching front to back
    through the fist, and the cloth domed over the top and falling a little over the rim.
    Drawn in the hold (CARRY), then turned back into the bind pose, rigid on the hand bone."""
    t = TAILORING['basket']
    wrist, R, axes = carry_frame(bones)
    f, p = axes['fingers'], axes['palm']
    grip = [CARRY['grip_from_wrist']*f[i]+CARRY['grip_toward_palm']*p[i] for i in range(3)]   # from the wrist, in the hold
    rim_y = grip[1]-t['handle_rise']
    cx, cz = grip[0], grip[2]
    a0, b0 = t['length']/2, t['width']/2           # along z (front to back), across x
    n = t['segments']
    side = CARRY['side']
    w = {f'hand_{side}': 1.}
    def to_bind(q):
        # p_bind = wrist + R^T q
        return [wrist[i]+sum(R[k][i]*q[k] for k in range(3)) for i in range(3)]
    wick = empty('market_basket', 'accessory__market_basket')
    def ring(mesh, a, b, y, v, z_off=0.):
        ids = []
        for k in range(n):
            ang = 2*math.pi*k/n
            q = [cx+b*math.sin(ang), y, cz+z_off+a*math.cos(ang)]
            ids.append(len(mesh['positions_m'])); mesh['positions_m'].append(q); mesh['uvs'].append([k/n, v]); mesh['weights'].append(dict(w))
        return ids
    def faces(mesh, ra, rb):
        for k in range(n):
            q = (k+1) % n
            mesh['triangles'] += [[ra[k], rb[q], ra[q]], [ra[k], rb[k], rb[q]]]
    bs = t['bottom_scale']; d = t['depth']
    bottom = ring(wick, a0*bs, b0*bs, rim_y-d, 0.)
    mid = ring(wick, a0*(bs+1)/2+.004, b0*(bs+1)/2+.004, rim_y-d/2, .5)
    top = ring(wick, a0, b0, rim_y-.012, .9)
    roll_out = ring(wick, a0+.009, b0+.009, rim_y-.006, .95)
    roll_top = ring(wick, a0+.004, b0+.004, rim_y+.002, 1.)
    for ra, rb in ((bottom, mid), (mid, top), (top, roll_out), (roll_out, roll_top)):
        faces(wick, ra, rb)
    c0 = len(wick['positions_m']); wick['positions_m'].append([cx, rim_y-d, cz]); wick['uvs'].append([.5, .5]); wick['weights'].append(dict(w))
    for k in range(n):
        wick['triangles'].append([bottom[k], bottom[(k+1) % n], c0])
    centre = lambda c: [cx, min(max(c[1], rim_y-d+.02), rim_y-.02), cz]
    wick = _outward(wick, centre)
    # The handle: a round rod arching in the basket's long plane from the rim's front, up
    # through the grip, to its back.
    hr = t['handle_radius']; m = 6; steps = 24
    hb = len(wick['positions_m'])
    for i in range(steps+1):
        s = i/steps; ang = math.pi*s
        # An arch of half-width a0 and height handle_rise, through the grip at its top.
        z = cz+a0*.96*math.cos(ang); y = rim_y+(grip[1]-rim_y)*math.sin(ang)
        tz, ty = -a0*math.sin(ang), (grip[1]-rim_y)*math.cos(ang)   # tangent in (z, y)
        L = math.hypot(tz, ty) or 1.; tz, ty = tz/L, ty/L
        nz, ny = -ty, tz                                              # in-plane normal
        for j in range(m):
            phi = 2*math.pi*j/m
            q = [cx+hr*math.sin(phi), y+hr*math.cos(phi)*ny, z+hr*math.cos(phi)*nz]
            wick['positions_m'].append(q); wick['uvs'].append([j/m, s]); wick['weights'].append(dict(w))
    for i in range(steps):
        ang = math.pi*(i+.5)/steps
        mid = [cx, rim_y+(grip[1]-rim_y)*math.sin(ang), cz+a0*.96*math.cos(ang)]
        for j in range(m):
            a = hb+i*m+j; b = hb+i*m+(j+1) % m; c = a+m; dd = b+m
            for f in ([a, b, dd], [a, dd, c]):
                A, B, C = (wick['positions_m'][k] for k in f)
                cen = [(A[k]+B[k]+C[k])/3 for k in range(3)]
                if _dot(_cross(_sub(B, A), _sub(C, A)), _sub(cen, mid)) < 0:
                    f = [f[0], f[2], f[1]]
                wick['triangles'].append(f)
    wick['corner_uvs'] = [[wick['uvs'][j] for j in f] for f in wick['triangles']]
    # The cloth over the top: domed, falling a little over the rim all round.
    cloth = empty('basket_cloth', 'accessory__basket_cloth')
    rings = []
    for r_i, (sc, dy) in enumerate(((1.06, -t['cloth_drape']), (1.03, -.004), (.85, t['cloth_dome']*.55), (.55, t['cloth_dome']*.9), (.25, t['cloth_dome']))):
        rings.append(ring(cloth, a0*sc+.006*(r_i == 0), b0*sc+.006*(r_i == 0), rim_y+.006+dy, r_i/4))
    for ra, rb in zip(rings, rings[1:]):
        faces(cloth, ra, rb)
    cc = len(cloth['positions_m']); cloth['positions_m'].append([cx, rim_y+.006+t['cloth_dome']+.004, cz]); cloth['uvs'].append([.5, 1.]); cloth['weights'].append(dict(w))
    for k in range(n):
        cloth['triangles'].append([rings[-1][k], rings[-1][(k+1) % n], cc])
    cloth = _outward(cloth, lambda c: [cx, rim_y-.03, cz])
    # Where the handle passes the cloth it stands clear: the cloth is under the arch.
    for mesh in (wick, cloth):
        mesh['positions_m'] = [to_bind(q) for q in mesh['positions_m']]
    held = [cx, rim_y-d, cz]
    wick['receipt'] = dict(garment='willow market basket', length_m=t['length'], width_m=t['width'], depth_m=d,
                           hand_bone=f'hand_{side}', rigid=True, bottom_below_wrist_in_hold_m=-(rim_y-d),
                           hold=CARRY)
    cloth['receipt'] = dict(garment='cloth over the basket', hand_bone=f'hand_{side}', rigid=True)
    return wick, cloth, held


def construct(body, hair):
    before = digest(body)
    bones = _bones(body)
    t = TAILORING
    spine = bones['spine_02']['head_m'][1]
    waist = spine-t['shirtwaist']['waist_below_spine02']
    shirt = shirtwaist(body, bones, waist)
    skirt_mesh, rings = skirt(body, bones, waist, shirt)
    straw, ribbon = boater(body, bones, hair)
    wick, cloth, held = basket(bones)
    parts = [shirt, cuffs(shirt, bones), necktie(shirt, bones), skirt_mesh, belt(shirt, skirt_mesh, waist+.006),
             straw, ribbon, wick, cloth]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_errand_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING), carry=copy.deepcopy(CARRY),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; the pictures are monochrome or of single garments',
                             'No cloth simulation: the skirt shares the leg-following skirt weights (T-3423)',
                             'Hat rigid on the head bone over the fitted bun hair; basket rigid on the left hand, hanging straight only in the renderer\'s carry hold'])


def prepare_errand_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3481; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('errand_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_errand_1904.py',
         'unsupported errand component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'errand assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'errand scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    need(spec.get('carry') == CARRY, 'recipe carry hold differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed errand body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'errand components require the declared liberty')
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
    need(recipe['hair_component'].get('fitter') == 'mhclo_proxy', 'the hat is set over the fitted bun hair')
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
