# SPDX-License-Identifier: GPL-3.0-or-later
"""A company officer of the First Infantry, August 1812, on the shared portable male rig.

An anonymous officer of the garrison of the first Fort Dearborn (Captain Nathan Heald's
company of the First Regiment of Infantry; Quaife 1913 prints its officers and muster-roll).
The asset is a ROLE: Captain Heald, Lieutenant Linai Helm, Ensign George Ronan and Surgeon's
mate Isaac Van Voorhis each wear one of its three variants with their own face, height and
colouring (the variation kit and human-looks.js). The pieces, read from the 1814 printing of
the army's laws and regulations (the artillery and staff rules, by analogy), the change of
1813 read backwards, Krimmel's Philadelphia soldiery and the Heald sword (recipe
data/humans/recipes/officer_1812.json; docs/RESEARCH/people-1812-3461/dress.json and
people-1812-3463/day.json):

  coat         dark blue superfine, single-breasted and buttoned, the private's body cut
               with long skirts behind to the bend of the knee and white turnbacks on
               their front edges; a scarlet standing collar to the ear, open at the throat
               where the stock shows, with a silver lace loop each side; scarlet cuffs;
               ten silver buttons
  epaulette    one silver bullion epaulette, the strap on the shoulder and the fringe
               falling over the upper arm: a captain's on the right shoulder, a
               lieutenant's on the left (the 1814 light artillery text); none for the
               surgeon's mate, a staff appointment
  waistcoat    white, showing below the coat's front at the waist
  pantaloons   white linen, close, into the boots
  stock        black leather, the private's
  boots        black, to just below the knee (the coachman's top-boot shaft, plain)
  belt, sword  a white leather waist belt over the coat; a sword in a black scabbard with
               brass mounts at the left hip, rigid on the pelvis. The captain's is curved
               with a stirrup hilt (Heald's sword, which his family kept, in Kirkland
               1893); the lieutenant's and the surgeon's mate's straight
  chapeau      a black felt chapeau bras worn fore-and-aft, a half-moon standing over the
               head; a black cockade on its left side under a silver loop and button, and a
               white feather rising eight inches (the 1814 artillery text). The surgeon's
               mate's feather is black and his collar black velvet (the 1814 rule for
               surgeons and mates)

No sash: it was worn "only on a tour of duty" and this is the everyday figure. No
crossbelts or cartridge box. Generated geometry is CC0-1.0. Cuts, eases, lengths and
colours are reconstructed; liberty L-human-modular-dress-1789 (supplement proposed in
docs/RESEARCH/people-1812-dress/officers-traders.md). The source anatomy is never changed.
Reuses the 1812 private's, the 1835 merchant's and the 1904 coachman's helpers by import.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_officer_assembly() (the recipe's `role_1812`) and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_period_wardrobe import finish_edges
import human_gentleman_1904 as G
import human_merchant_1835 as M
import human_coachman_1904 as C
import human_soldier_1812 as S

BODY_SHA256 = 'e7b088b88ea18bb309ca990ef6c0cafea9420ac152d42d1351c1a9795daa9269'
ASSEMBLY = 'officer_1812_v1'
RECIPE = 'data/humans/recipes/officer_1812.json'
LIBERTY = 'L-human-modular-dress-1789'
PERSONS = {'captain': 'anonymous_captain_first_infantry_1812',
           'lieutenant': 'anonymous_lieutenant_first_infantry_1812',
           'surgeons_mate': 'anonymous_surgeons_mate_first_infantry_1812'}

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    coat=dict(ease=.020, armpit_extra=.020, sleeve_short_of_wrist=.022, top_below_neck=.008, waist_below_spine02=.022,
              cuff_depth=.070, smoothing=60, smoothing_min_ease=.018),
    collar=dict(ease=.018, bottom_below_neck=.034, back_above_neck=.072, below_stock_top=.004, front_gap_deg=20.,
                segments=40, rows=6),
    lace=dict(from_gap_deg=3., length_deg=30., height=.012, centre_above_neck=-.010, offset=.0022),
    tails=dict(hem_y=.515, ease=.022, edge_top_deg=72., edge_hem_deg=130., vent_deg=3., segments=20, rows=13),
    turnbacks=dict(top_deg=6., hem_deg=17., offset=.0022),
    buttons=dict(radius=.0078, count=10, below_collar=.030, above_waist=.020, standoff=.0025, sides=10),
    epaulette=dict(inner_x=.080, outer_x=.200, strap_half=.018, pad_half=.040, pad_from_x=.145, pad_to_x=.185,
                   above_arm=.022, offset=.0045, fringe_to_x=.240, fringe_deg=100., fringe_offset=.0080),
    waistcoat=dict(waist_height_fraction=.585, band_ease=.014, band_below_waist=.030, band_above_coat_seam=.016),
    pantaloons=dict(ease=.013, waist_height_fraction=.585, bottom_y=.400, thigh_fullness=.010, smoothing=60),
    boots=dict(bottom_y=.080, top_y=.460, ease_bottom=.006, ease_top=.016, segments=28, rows=9),
    belt=dict(width=.034, above_seam=.003, offset=.0045, segments=48),
    sword=dict(length=.80, width=.032, thickness=.014, off_side=.026, z=-.010, below_belt=.010, tilt_deg=24.,
               curve_deg=14., segments=12, hilt=.120, guard=.080, bow_out=.045),
    chapeau=dict(seat_below_top=.066, ease=.012, length=.40, height=.165, point_lift=.030, point_width=.006,
                 slices=22, wall_rows=7, wall_power=1.5, cockade_radius=.054, cockade_z=.050, cockade_t=.42,
                 loop_width=.016, plume_height=.200, plume_radius=.022, plume_lean=.035),
)

# Each variant's rank: which shoulder carries the epaulette, the sword's curve, the
# collar's and the feather's material, and whether the collar is laced.
RANKS = {
    'captain': dict(epaulette='right', curved=True, collar='garment_upper__facings_scarlet_1812',
                    plume='headwear__plume_white_1812', lace=True),
    'lieutenant': dict(epaulette='left', curved=False, collar='garment_upper__facings_scarlet_1812',
                       plume='headwear__plume_white_1812', lace=True),
    'surgeons_mate': dict(epaulette=None, curved=False, collar='garment_upper__collar_black_velvet_1812',
                          plume='headwear__plume_black_1812', lace=False),
}

MATERIALS = {
    'garment_upper__coat_blue_officer_1812': {'base_color_linear': [.016, .021, .060, 1], 'roughness': .82},
    'garment_upper__facings_scarlet_1812': {'base_color_linear': [.42, .026, .020, 1], 'roughness': .80},
    'garment_upper__collar_black_velvet_1812': {'base_color_linear': [.008, .008, .009, 1], 'roughness': .95},
    'garment_upper__white_1812': {'base_color_linear': [.72, .71, .66, 1], 'roughness': .84},
    'garment_lower__pantaloons_white_1812': {'base_color_linear': [.70, .68, .62, 1], 'roughness': .86},
    'accessory__black_leather_1812': {'base_color_linear': [.010, .010, .011, 1], 'roughness': .45},
    'accessory__silver_1812': {'base_color_linear': [.40, .40, .39, 1], 'roughness': .30},
    'accessory__brass_1812': {'base_color_linear': [.46, .33, .11, 1], 'roughness': .35},
    'footwear__black_boots_officer_1812': {'base_color_linear': [.011, .010, .010, 1], 'roughness': .34},
    'headwear__chapeau_black_1812': {'base_color_linear': [.013, .012, .012, 1], 'roughness': .7},
    'headwear__plume_white_1812': {'base_color_linear': [.80, .79, .75, 1], 'roughness': .9},
    'headwear__plume_black_1812': {'base_color_linear': [.012, .012, .012, 1], 'roughness': .9},
}
SHOE_MATERIAL = 'footwear__black_boots_officer_1812'
WEAVE_MATERIAL = 'garment_lower__pantaloons_white_1812'


def _finish(mesh, thickness):
    """finish_edges where the strip's own boundary allows it; a sliver cut by an angular
    field can leave a degenerate boundary UV, and then the strip stands as cut."""
    try:
        return finish_edges(mesh, thickness)
    except ValueError:
        return mesh


def _merge(name, material, meshes):
    out = empty(name, material)
    for m in meshes:
        base = len(out['positions_m'])
        for k in ('positions_m', 'uvs', 'weights', 'corner_uvs'):
            out[k] += copy.deepcopy(m[k])
        out['triangles'] += [[i+base for i in f] for f in m['triangles']]
    return out


def _face_normal(P, f):
    a, b, c = (P[i] for i in f)
    u = [b[k]-a[k] for k in range(3)]; v = [c[k]-a[k] for k in range(3)]
    n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    d = math.hypot(*n)
    return [x/d for x in n] if d > 1e-15 else None


def on_faces(base, fields, name, material, offset, keep_face):
    """The private's strip on a garment (S._on_garment), cut only from the faces `keep_face`
    accepts (so a garment's own edge returns are left out): it lies on the garment and is
    skinned as the garment beneath it."""
    P = base['positions_m']
    kept = dict(base)
    pairs = [(f, cuv) for f, cuv in zip(base['triangles'], base['corner_uvs'])
             if (n := _face_normal(P, f)) is not None and keep_face([sum(P[i][a] for i in f)/3 for a in range(3)], n)]
    kept['triangles'] = [f for f, _ in pairs]; kept['corner_uvs'] = [c for _, c in pairs]
    return S._on_garment(kept, fields, name, material, offset)


def _orient(mesh, outward, start=0):
    """Wind every triangle from `start` on so its normal points along outward(centroid)."""
    P = mesh['positions_m']
    swap_uv = len(mesh.get('corner_uvs') or []) == len(mesh['triangles'])
    for i, f in enumerate(mesh['triangles']):
        if i < start:
            continue
        n = _face_normal(P, f)
        if n is None:
            continue
        c = [sum(P[j][a] for j in f)/3 for a in range(3)]
        o = outward(c)
        if n[0]*o[0]+n[1]*o[1]+n[2]*o[2] < 0:
            mesh['triangles'][i] = [f[0], f[2], f[1]]
            if swap_uv:
                cu = mesh['corner_uvs'][i]; mesh['corner_uvs'][i] = [cu[0], cu[2], cu[1]]
    return mesh


def coat(body, bones):
    """The private's coat body and cuffs (S.coat), cut to the officer's measures."""
    with C._lent(S, coat=TAILORING['coat']):
        blue, red, waist = S.coat(body, bones)
    blue['material'] = 'garment_upper__coat_blue_officer_1812'
    red['material'] = 'garment_upper__facings_scarlet_1812'; red['name'] = 'coat_cuffs_scarlet'
    blue['receipt']['garment'] = 'officer\'s blue coat body and sleeves, buttoned'
    red['receipt']['garment'] = 'scarlet cuffs'
    return blue, red, waist


def stock_and_collar(body, bones, collar_material):
    """The black leather stock (the private's, the merchant's loft) and outside it a standing
    collar to the ear, open at the throat where the stock shows, its top under the stock's."""
    t = TAILORING['collar']
    stock, (dirs, tops, centre) = M.stock(body, bones)
    stock['name'] = 'black_leather_stock'; stock['material'] = 'accessory__black_leather_1812'
    stock['receipt']['garment'] = 'black leather stock'
    neck = bones['neck_01']['head_m'][1]
    n = len(dirs)
    bottoms = [neck-t['bottom_below_neck']]*n
    collar_tops = [min(tops[k]-t['below_stock_top'], neck+t['back_above_neck']) for k in range(n)]
    collar = S._neck_loft(body, bones, 'coat_collar', collar_material, t['ease'], bottoms, collar_tops,
                          t['front_gap_deg'], n, t['rows'])
    collar['receipt'] = dict(garment='standing collar to the ear', top_back_y_m=collar_tops[n//2], bottom_y_m=bottoms[0],
                             front_gap_deg=t['front_gap_deg'], ease_m=t['ease'])
    return stock, collar, centre


def collar_lace(collar, bones, centre):
    """A silver lace loop each side of the collar's front opening, laid on the collar."""
    t = TAILORING['lace']; g = TAILORING['collar']['front_gap_deg']
    cx, cz = centre
    y0 = bones['neck_01']['head_m'][1]+t['centre_above_neck']
    def ang(p):
        return abs(math.degrees(math.atan2(p[0]-cx, p[2]-cz)))
    lo, hi = g+t['from_gap_deg'], g+t['from_gap_deg']+t['length_deg']
    fields = [lambda v: ang(v['p'])-lo, lambda v: hi-ang(v['p']), lambda v: v['p'][1]-(y0-t['height']/2),
              lambda v: y0+t['height']/2-v['p'][1]]
    def outward(c, n):
        return n[0]*(c[0]-cx)+n[2]*(c[2]-cz) > .5*math.hypot(c[0]-cx, c[2]-cz)
    out = on_faces(collar, fields, 'collar_lace_silver', 'accessory__silver_1812', t['offset'], outward)
    out = _finish(out, .0010)
    out['receipt'] = dict(garment='silver lace loops on the collar', each_side_deg=[lo, hi], centre_y_m=y0, height_m=t['height'])
    return out


def tails_and_turnbacks(body, bones, blue, waist):
    """Long skirts behind to the bend of the knee (the merchant's tail loft) and white
    turnbacks: a band of each skirt's front edge, widening to the hem, laid on the skirt."""
    t = TAILORING['tails']; tb = TAILORING['turnbacks']
    tails = M.tails(body, bones, blue, waist, t=t, name='coat_skirts', material='garment_upper__coat_blue_officer_1812',
                    garment='coat skirts behind to the bend of the knee')
    top = tails['receipt']['top_y_m']; hem = t['hem_y']
    def edge(y):
        f = min(1., max(0., (top-y)/(top-hem)))
        return math.radians(t['edge_top_deg']+(t['edge_hem_deg']-t['edge_top_deg'])*f**.8), f
    def field(v):
        p = v['p']; a = math.atan2(abs(p[0]), p[2])
        e, f = edge(p[1])
        return e+math.radians(tb['top_deg']+(tb['hem_deg']-tb['top_deg'])*f)-a
    def outward(c, n):
        r = math.hypot(c[0], c[2]) or 1.
        return (n[0]*c[0]+n[2]*c[2])/r > .3
    white = on_faces(tails, [field, lambda v: top-.01-v['p'][1]], 'coat_turnbacks_white', 'garment_upper__white_1812',
                     tb['offset'], outward)
    white = _finish(white, .0012)
    white['receipt'] = dict(garment='white turnbacks on the skirts\' front edges', width_deg=[tb['top_deg'], tb['hem_deg']])
    return tails, white


def buttons(blue, bones, waist):
    with C._lent(S, buttons=TAILORING['buttons']):
        out = S.buttons(blue, bones, waist)
    out['material'] = 'accessory__silver_1812'
    out['receipt']['garment'] = 'silver coat buttons'
    return out


def epaulette(blue, bones, side):
    """One silver epaulette on `side`: a strap from the collar to the shoulder point widening
    to a crescent pad, and the bullion fringe over the top of the upper arm, all cut from
    the coat's own surface and skinned as the coat (the fringe goes with the arm)."""
    t = TAILORING['epaulette']
    s = 1. if side == 'left' else -1.
    arm = bones['upperarm_l']['head_m']; ay, az = arm[1], arm[2]
    def half(x):
        f = min(1., max(0., (x-t['pad_from_x'])/(t['pad_to_x']-t['pad_from_x'])))
        return t['strap_half']+(t['pad_half']-t['strap_half'])*f*f*(3-2*f)
    strap = [lambda v: s*v['p'][0]-t['inner_x'], lambda v: t['outer_x']-s*v['p'][0],
             lambda v: half(s*v['p'][0])-abs(v['p'][2]-az), lambda v: v['p'][1]-(ay+t['above_arm'])]
    pad = S._on_garment(blue, strap, 'epaulette_strap', 'accessory__silver_1812', t['offset'])
    cos = math.cos(math.radians(t['fringe_deg']))
    fringe_fields = [lambda v: s*v['p'][0]-(t['outer_x']-.012), lambda v: t['fringe_to_x']-s*v['p'][0],
                     lambda v: (v['p'][1]-ay)-cos*math.hypot(v['p'][1]-ay, v['p'][2]-az)]
    fringe = S._on_garment(blue, fringe_fields, 'epaulette_fringe', 'accessory__silver_1812', t['fringe_offset'])
    out = _merge(f'epaulette_{side}', 'accessory__silver_1812', [_finish(pad, .0015), _finish(fringe, .0020)])
    out['receipt'] = dict(garment=f'silver epaulette, {side} shoulder', strap_x_m=[t['inner_x'], t['outer_x']],
                          fringe_x_m=[t['outer_x']-.012, t['fringe_to_x']], fringe_deg=t['fringe_deg'])
    return out


def waistcoat(body, bones, height, waist):
    """The white waistcoat where it shows: the private's waist band of the body's own
    surface, under the coat's seam and over the pantaloons' top."""
    t = TAILORING['waistcoat']
    with C._lent(S, overalls=dict(S.TAILORING['overalls'], **t)):
        out = S.overalls_waistband(body, bones, height, waist)
    out['name'] = 'white_waistcoat'; out['material'] = 'garment_upper__white_1812'
    out['receipt']['garment'] = 'white waistcoat, below the coat front'
    return out


def pantaloons(body, bones, height):
    with C._lent(C, breeches=TAILORING['pantaloons']):
        out = C.breeches(body, bones, height)
    out['name'] = 'white_pantaloons'; out['material'] = 'garment_lower__pantaloons_white_1812'
    out['receipt']['garment'] = 'white linen pantaloons, close, into the boots'
    return out


def boots(body, bones):
    with C._lent(C, boots=TAILORING['boots']):
        out = C.top_boots(body, bones)
    out['name'] = 'boot_shafts'; out['material'] = SHOE_MATERIAL
    out['receipt']['garment'] = 'black boots to just below the knee'
    return out


def belt(blue, waist):
    """A white leather waist belt over the coat just above its waist seam: a band lofted
    round the coat's own section (bridging the hollow of the back as a belt does), every
    ring enclosing the coat at its height, skinned as the nearest coat point."""
    t = TAILORING['belt']
    lo = waist+t['above_seam']; hi = lo+t['width']
    P, W = blue['positions_m'], blue['weights']
    near = [i for i, p in enumerate(P) if lo-.012 <= p[1] <= hi+.012 and abs(p[0]) < .3]
    cz = (min(P[i][2] for i in near)+max(P[i][2] for i in near))/2
    n = t['segments']; rows = 3
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    out = empty('waist_belt_white', 'garment_upper__white_1812')
    for r in range(rows):
        y = lo+(hi-lo)*r/(rows-1)
        slab = [i for i in near if abs(P[i][1]-y) <= .012]
        for k, (dx, dz) in enumerate(dirs):
            rr = max(P[i][0]*dx+(P[i][2]-cz)*dz for i in slab)+t['offset']
            q = [rr*dx, y, cz+rr*dz]
            j = min(slab, key=lambda i: (P[i][0]-q[0])**2+(P[i][2]-q[2])**2+(P[i][1]-y)**2)
            out['positions_m'].append(q); out['uvs'].append([k/n, r/(rows-1)]); out['weights'].append(G._skin4(dict(W[j]), 1.))
    for r in range(rows-1):
        for k in range(n):
            a = r*n+k; b = r*n+(k+1) % n; c = a+n; d = b+n
            out['triangles'] += [[a, b, d], [a, d, c]]
    _orient(out, lambda c: [c[0], 0., c[2]-cz])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='white leather waist belt over the coat', y_m=[lo, hi], segments=n)
    return out, lo


def _sweep(out, path, half_w, half_t, weights, closed=True):
    """A rectangular section (half_w along the path's normal in y-z, half_t along x) swept
    along `path` (a list of points in the plane x = const); ends capped."""
    ids = []
    for i, p in enumerate(path):
        a = path[max(0, i-1)]; b = path[min(len(path)-1, i+1)]
        ty, tz = b[1]-a[1], b[2]-a[2]; d = math.hypot(ty, tz) or 1.
        ny, nz = -tz/d, ty/d
        ring = []
        for sx, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            ring.append(len(out['positions_m']))
            out['positions_m'].append([p[0]+sx*half_t, p[1]+sw*half_w*ny, p[2]+sw*half_w*nz])
            out['uvs'].append([(sx+1)/2, i/(len(path)-1)]); out['weights'].append(dict(weights))
        ids.append(ring)
    for r0, r1 in zip(ids, ids[1:]):
        for k in range(4):
            a, b, c, d = r0[k], r0[(k+1) % 4], r1[(k+1) % 4], r1[k]
            out['triangles'] += [[a, b, c], [a, c, d]]
    if closed:
        out['triangles'] += [[ids[0][0], ids[0][2], ids[0][1]], [ids[0][0], ids[0][3], ids[0][2]],
                             [ids[-1][0], ids[-1][1], ids[-1][2]], [ids[-1][0], ids[-1][2], ids[-1][3]]]


def sword(body, bones, belt_y, curved):
    """A sword at the left hip, rigid on the pelvis: a black scabbard hanging back from the
    belt (curved for a sabre), brass locket and chape, and a brass hilt above the mouth with
    a black grip, a cross-guard and (a stirrup hilt) a knuckle bow."""
    t = TAILORING['sword']
    P = body['meshes'][0]['positions_m']
    top = belt_y-t['below_belt']
    side = max(p[0] for p in P if abs(p[1]-(top-.06)) < .05 and abs(p[2]-t['z']) < .08 and p[0] > 0)
    x = side+TAILORING['tails']['ease']+t['off_side']+t['thickness']/2
    tilt = math.radians(t['tilt_deg']); bend = math.radians(t['curve_deg'] if curved else 0.)
    n = t['segments']; step = t['length']/n
    path = [[x, top, t['z']]]
    for i in range(n):
        a = tilt+bend*(i+.5)/n
        y, z = path[-1][1], path[-1][2]
        path.append([x, y-step*math.cos(a), z-step*math.sin(a)])
    W = {'pelvis': 1.}
    leather = empty('sword_scabbard', 'accessory__black_leather_1812')
    _sweep(leather, path, t['width']/2, t['thickness']/2, W)
    brass = empty('sword_mounts_brass', 'accessory__brass_1812')
    _sweep(brass, path[:2], t['width']/2+.002, t['thickness']/2+.002, W)
    _sweep(brass, path[-2:], t['width']/2+.002, t['thickness']/2+.002, W)
    # The hilt: up and forward along the scabbard's first direction.
    ux, uy, uz = 0., math.cos(tilt), math.sin(tilt)
    def along(d, fwd=0.):
        return [x, top+uy*d-uz*fwd, t['z']+uz*d+uy*fwd]
    guard = [along(.004, -t['guard']/2), along(.004, t['guard']/2)]
    _sweep(brass, [[x, g[1], g[2]] for g in guard], .006, .009, W)
    pommel = along(t['hilt']+.012)
    _sweep(leather, [along(.012), along(t['hilt'])], .013, .011, W)
    _sweep(brass, [along(t['hilt']), pommel], .015, .012, W)
    if curved:
        # The stirrup: a bar from the guard's front out and up round the grip to the pommel.
        bow = [along(.004+(t['hilt']+.004)*k/8, t['guard']/2*(1-k/8)+t['bow_out']*math.sin(math.pi*k/8)*.6) for k in range(9)]
        _sweep(brass, bow, .0035, .004, W)
    out = []
    for m in (leather, brass):
        m['corner_uvs'] = [[m['uvs'][i] for i in f] for f in m['triangles']]
        out.append(m)
    leather['receipt'] = dict(garment=('curved sabre' if curved else 'straight sword')+' in a black scabbard at the left hip',
                              length_m=t['length'], tilt_deg=t['tilt_deg'], curve_deg=t['curve_deg'] if curved else 0.,
                              mouth_m=[x, top, t['z']], skinning='pelvis, rigid')
    brass['receipt'] = dict(garment='brass sword mounts and hilt', stirrup_hilt=curved)
    return out


def chapeau(body, bones, plume_material):
    """A black felt chapeau bras worn fore-and-aft: a half-moon standing over the head, its
    two flaps meeting in a ridge, their bottoms round the skull's own section at the seat and
    pinched together to points before and behind; every wall point clears the head. A black
    cockade on the left flap under a silver loop and button, and a feather rising from the
    ridge above it. All rigid on the head bone; the feather a mesh of its own."""
    t = TAILORING['chapeau']
    m = body['meshes'][0]
    head = [p for p, w in zip(m['positions_m'], m['weights']) if w.get('head', 0.) > .9]
    top = max(p[1] for p in head); seat = top-t['seat_below_top']
    band = [p for p in head if seat-.012 <= p[1] <= seat+.03]
    cx = (min(p[0] for p in band)+max(p[0] for p in band))/2
    cz = (min(p[2] for p in band)+max(p[2] for p in band))/2
    above = [p for p in head if p[1] >= seat-.01]
    half = t['length']/2
    def head_half(z, y):
        pts = [abs(p[0]-cx) for p in above if abs(p[2]-z) < .014 and abs(p[1]-y) < .014]
        return max(pts)+t['ease'] if pts else 0.
    zs = [cz+half*(-.985+1.97*i/(t['slices']-1)) for i in range(t['slices'])]
    front = max(p[2] for p in band); back = min(p[2] for p in band)
    def bottom_half(z):
        h = head_half(z, seat+.006)
        if h:
            return h
        d = (z-front) if z > front else (back-z)
        span = (cz+half-front) if z > front else (back-(cz-half))
        f = min(1., d/span); w0 = head_half(front if z > front else back, seat+.006) or .08
        return t['point_width']+(w0-t['point_width'])*(1-f)**1.6
    def y_bottom(z):
        d = max(0., z-front, back-z)
        span = (cz+half-front) if z > front else (back-(cz-half))
        return seat+t['point_lift']*(min(1., d/span) if d else 0.)**2
    def y_top(z):
        u = (z-cz)/half; yb = y_bottom(z)
        return yb+(seat+t['height']-yb)*max(0., 1-u*u)**.55
    R = t['wall_rows']
    def wall(z, f, sign):
        yb, yt = y_bottom(z), y_top(z)
        y = yb+(yt-yb)*f
        w = bottom_half(z)*max(0., 1-f**t['wall_power'])**.8
        w = max(w, head_half(z, y)) if f < .999 else 0.
        return [cx+sign*w, y, z]
    out = empty('headwear_chapeau', 'headwear__chapeau_black_1812')
    H = {'head': 1.}
    rings = []
    for i, z in enumerate(zs):
        ring = []
        for j in range(2*R+1):
            f, sign = (j/R, 1.) if j <= R else ((2*R-j)/R, -1.)
            ring.append(len(out['positions_m'])); out['positions_m'].append(wall(z, f, sign))
            out['uvs'].append([j/(2*R), i/(len(zs)-1)]); out['weights'].append(dict(H))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(2*R+1):
            a, b, c, d = r0[j], r0[(j+1) % (2*R+1)], r1[(j+1) % (2*R+1)], r1[j]
            out['triangles'] += [[a, b, c], [a, c, d]]
    for ring, z in ((rings[0], cz-half), (rings[-1], cz+half)):
        tip = len(out['positions_m']); out['positions_m'].append([cx, y_bottom(z)+.004, z])
        out['uvs'].append([.5, 0. if z < cz else 1.]); out['weights'].append(dict(H))
        for j in range(2*R+1):
            out['triangles'].append([ring[j], ring[(j+1) % (2*R+1)], tip])
    def outward(c):
        z = min(max(c[2], cz-half*.98), cz+half*.98)
        mid = (y_bottom(z)+y_top(z))/2
        return [c[0]-cx, (c[1]-mid)*.3, (c[2]-cz)*.4]
    out = _orient(out, outward)
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    # Clearance: no head point above the seat lies outside the walls.
    worst = math.inf
    for p in above:
        if p[1] < seat+.004 or not (zs[0] <= p[2] <= zs[-1]):
            continue
        i = min(range(len(zs)), key=lambda k: abs(zs[k]-p[2]))
        yb, yt = y_bottom(zs[i]), y_top(zs[i])
        f = min(1., max(0., (p[1]-yb)/(yt-yb)))
        worst = min(worst, wall(zs[i], f, 1.)[0]-cx-abs(p[0]-cx), yt-p[1])
    need(worst > .004, f'the chapeau meets the head ({worst:.4f} m)')
    # Cockade, loop and button on the left flap.
    zc = cz+t['cockade_z']
    def frame(f):
        p = wall(zc, f, 1.); q = wall(zc, min(1., f+.04), 1.)
        ty = [q[0]-p[0], q[1]-p[1], 0.]; d = math.hypot(*ty); ty = [a/d for a in ty]
        nrm = [ty[1], -ty[0], 0.]
        return p, ty, nrm
    def disc(mesh, f, r, stand, sides=20):
        p, ty, nrm = frame(f)
        c0 = len(mesh['positions_m']); t0 = len(mesh['triangles'])
        mesh['positions_m'].append([p[a]+nrm[a]*(stand+.001) for a in range(3)]); mesh['uvs'].append([.5, .5]); mesh['weights'].append(dict(H))
        for k in range(sides):
            a = 2*math.pi*k/sides
            mesh['positions_m'].append([p[0]+nrm[0]*stand+ty[0]*r*math.sin(a), p[1]+nrm[1]*stand+ty[1]*r*math.sin(a),
                                        p[2]+r*math.cos(a)])
            mesh['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)]); mesh['weights'].append(dict(H))
        for k in range(sides):
            mesh['triangles'].append([c0, c0+1+k, c0+1+(k+1) % sides])
        _orient(mesh, lambda c: nrm, t0)
    disc(out, t['cockade_t'], t['cockade_radius'], .004)
    silver = empty('chapeau_loop_silver', 'accessory__silver_1812')
    steps = 8; ids = []
    for k in range(steps+1):
        f = t['cockade_t']+(1-t['cockade_t'])*k/steps*.97
        p, ty, nrm = frame(f)
        for dz in (-t['loop_width']/2, t['loop_width']/2):
            ids.append(len(silver['positions_m']))
            silver['positions_m'].append([p[0]+nrm[0]*.0065, p[1]+nrm[1]*.0065, p[2]+dz]); silver['uvs'].append([dz > 0, k/steps])
            silver['weights'].append(dict(H))
    for k in range(steps):
        a, b, c, d = ids[2*k], ids[2*k+1], ids[2*k+3], ids[2*k+2]
        silver['triangles'] += [[a, b, c], [a, c, d]]
    _orient(silver, lambda c: [1., 0., 0.])
    disc(silver, t['cockade_t'], .010, .0085, 12)
    silver['corner_uvs'] = [[silver['uvs'][i] for i in f] for f in silver['triangles']]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='black felt chapeau bras worn fore-and-aft, black cockade on the left', seat_y_m=seat,
                          length_m=t['length'], height_m=t['height'], minimum_head_clearance_m=worst, head_bone='head',
                          separate_mesh=True, lift='rigid on the head bone')
    silver['receipt'] = dict(garment='silver loop and button over the cockade')
    # The feather: rising from the ridge above the cockade, leaning a little back.
    plume = empty('headwear_plume', plume_material)
    ridge = wall(zc, 1., 1.)
    bx, by, bz = ridge[0]+.006, ridge[1]-.03, ridge[2]
    levels, sides = 8, 8; rings = []
    for i in range(levels):
        f = i/(levels-1)
        rad = t['plume_radius']*math.sin(math.pi*min(.98, .15+.85*f))**.8*(1-.55*f)
        ring = []
        for j in range(sides):
            a = 2*math.pi*j/sides
            ring.append(len(plume['positions_m']))
            plume['positions_m'].append([bx+rad*math.cos(a), by+t['plume_height']*f, bz-t['plume_lean']*f*f+rad*math.sin(a)])
            plume['uvs'].append([j/sides, f]); plume['weights'].append(dict(H))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(sides):
            a, b, c, d = r0[j], r0[(j+1) % sides], r1[(j+1) % sides], r1[j]
            plume['triangles'] += [[a, c, b], [a, d, c]]
    tip = len(plume['positions_m']); plume['positions_m'].append([bx, by+t['plume_height']+.012, bz-t['plume_lean']-.004])
    plume['uvs'].append([.5, 1.]); plume['weights'].append(dict(H))
    foot = tip+1; plume['positions_m'].append([bx, by-.004, bz]); plume['uvs'].append([.5, 0.]); plume['weights'].append(dict(H))
    for j in range(sides):
        plume['triangles'].append([rings[-1][j], rings[-1][(j+1) % sides], tip])
        plume['triangles'].append([rings[0][(j+1) % sides], rings[0][j], foot])
    _orient(plume, lambda c: [c[0]-bx, 0., c[2]-bz+.0001])
    plume['corner_uvs'] = [[plume['uvs'][i] for i in f] for f in plume['triangles']]
    plume['receipt'] = dict(garment='feather rising eight inches', height_m=t['plume_height'], head_bone='head')
    return out, silver, plume


def construct(body, rank='captain'):
    need(rank in RANKS, f'unknown officer rank {rank!r}')
    r = RANKS[rank]
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    blue, red, waist = coat(body, bones)
    stock, collar, centre = stock_and_collar(body, bones, r['collar'])
    skirts, turnbacks = tails_and_turnbacks(body, bones, blue, waist)
    band, belt_y = belt(blue, waist)
    hat, loop, plume = chapeau(body, bones, r['plume'])
    parts = [stock, collar]
    if r['lace']:
        parts.append(collar_lace(collar, bones, centre))
    parts += [finish_edges(blue, .0018), finish_edges(red, .0018), skirts, turnbacks, buttons(blue, bones, waist)]
    if r['epaulette']:
        parts.append(epaulette(blue, bones, r['epaulette']))
    parts += [band, *sword(body, bones, belt_y, r['curved']), waistcoat(body, bones, height, waist),
              pantaloons(body, bones, height), boots(body, bones), hat, loop, plume]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    used = {m['material'] for m in parts} | {SHOE_MATERIAL}
    return dict(format='chicago4d_officer_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts, rank=rank,
                materials={k: copy.deepcopy(v) for k, v in MATERIALS.items() if k in used},
                shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL, tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths and colours are reconstructed; no picture is of the Fort Dearborn officers',
                             'No cloth simulation: shells and skirts follow the body bones (each skirt goes with its own leg)',
                             'No sash (worn only on a tour of duty), no lace on the breast, no eagle on the cockade',
                             'Chapeau, loop and feather rigid on the head bone; the sword rigid on the pelvis'])


def prepare_officer_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer (the recipe's role_1812); never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('officer_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_officer_1812.py',
         'unsupported officer component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'officer assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1812-08-14' and recipe.get('grade') == 'reconstructed',
         'officer scene/appearance grade changed')
    rank = variant.get('officer_rank')
    need(rank in RANKS and variant.get('person_reference_id') == PERSONS[rank], 'officer variant names an unknown rank')
    need(spec.get('tailoring') == json.loads(json.dumps(TAILORING)), 'recipe tailoring differs from the generator')
    need(spec.get('ranks') == RANKS, 'recipe ranks differ from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed officer body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'officer components require the declared liberty')
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
    bundle = construct(body, rank)
    bundle['liberty'] = LIBERTY
    worn = {m['material'] for m in bundle['meshes']}
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']
                          if rank in g.get('ranks', RANKS) and (g['material'] in worn or g['material'] == SHOE_MATERIAL)]
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
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True)
    p.add_argument('--rank', default='captain', choices=sorted(RANKS))
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    data = construct(json.loads(raw), a.rank)
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]},
                     indent=1, default=str))
