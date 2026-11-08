# SPDX-License-Identifier: GPL-3.0-or-later
"""The children of Chicago, 1812, on child bodies of the shared portable rig (T-3465).

Three anonymous roles, each one reconstructed figure that any child of its age and sex in the
1812 town may wear (the variation kit and human-looks.js give each their own face, height and
colouring; the asset names no one). Read from the pictures in the recipes and from the
children's research (docs/RESEARCH/people-1812-3465/day.json `dress`, and
docs/RESEARCH/people-1812-3461/dress.json "Children 2-12 and infants"):

  child_boy_1812      a boy of about six to ten in a skeleton suit: a short dark blue jacket,
                      long sleeves, closed and buttoned down the front, its hem hidden under
                      long trousers of the same cloth that rise high to the ribs and button
                      onto it in a row round the front; a wide white shirt collar (frilled
                      in the pictures, drawn plain) lying out over the jacket's shoulders; bare head; black shoes (the
                      Rutter boy, Joshua Johnson about 1805; the Pixler boys about 1815)
  child_girl_1812     a girl of about six to ten in a high-waisted frock to just above the
                      ankle, short puffed sleeves, a wide round neck, in a faded rose printed
                      cotton (Emma Van Name's pink spotted frock; the Rutter girl's frock),
                      with a white linen pinafore over it: a bib on the breast and a broad
                      apron round the front and sides to below the knee (the pinafore is
                      reconstructed, as the research says); bare head; dark shoes
  child_toddler_1812  an unbreeched child of either sex of about two and a half to four and a
                      half in a white cotton frock, high waist, short puffed sleeves, to the
                      ankle (the Beecher frock, worn by a boy about 1813; the Rutter girl);
                      bare head; red shoes (both Johnson portraits paint them)

The boy and the girl stand on 8-year bodies (prepared_child_male_8 / prepared_child_female_8)
and the toddler on a 3-year one of either sex (prepared_child_3), all MakeHuman hm08 child and
baby graphical targets (assets/authored/humans/makehuman_hm08/SOURCE-child.json).

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with its T-3465 supplement (docs/RESEARCH/people-1812-dress/children.md).
The source anatomy is never changed. Reuses the gentleman's, merchant's, labourer's and the
dress components' helpers.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_child_assembly() through each recipe's `role_1812` and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

from human_dress_components import need, digest, empty, leg_follow, bib as apron_bib
from human_period_wardrobe import finish_edges
from human_workwear_fit import _slab_points, garment_shell
import human_gentleman_1904 as G
import human_soldier_1812 as S

LIBERTY = 'L-human-modular-dress-1789'
MODULE = 'human_child_1812'
PREPARE = 'prepare_child_assembly'
GENERATOR = 'tools/human_child_1812.py'
BODIES = {
    'male_8': ('assets/authored/humans/makehuman_hm08/prepared_child_male_8.json',
               '573c17c5e93c7f3c9c22c43cd3aa97a652acf00577dcf51f1c6de9dc39026b90'),
    'female_8': ('assets/authored/humans/makehuman_hm08/prepared_child_female_8.json',
                 '24933040bbb254cbb5c1e81e16ddc797fd82952c12b489ce42f5354ffd666972'),
    'either_3': ('assets/authored/humans/makehuman_hm08/prepared_child_3.json',
                 'f040beceec388b0c63ffb6834bc616be3adc23aa2ba9913a9474cb09d82ac142'),
}
# The 25-year engineering body's leg (hip to ankle, metres) at which the builder's baked walk
# was drawn (0.6 m/s, 1.2 s cycle); see child_walk().
ADULT_LEG_M = 0.8603

# Every dimension of each outfit, in metres; the recipes repeat them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
FROCK_SLEEVE = dict(ease=.013, smoothing=90, smoothing_min_ease=.013, armpit_extra=.008, sleeve_of_upperarm=.42,
                    puff=.016, neck_drop_front=.040, neck_drop_back=.014, neck_drop_side=.022)
TAILORING = {
    'child_boy_1812': dict(
        jacket=dict(ease=.015, armpit_extra=.012, sleeve_short_of_wrist=.012, top_below_neck=.006,
                    hem_above_spine01=.012, smoothing=90, smoothing_min_ease=.015),
        collar=dict(depth_front=.060, depth_back=.070, depth_side=.050, half_width=.118, front_gap=.016,
                    frill_waves=0, frill_depth=0., offset=.0035),
        trousers=dict(ease=.010, cuff_radius_ratio=.95, added_section_ease=.010, thigh_transition_fraction=.45,
                      hem_front_y=.044, hem_back_y=.024, band_ease=.018, band_below_waist=.02,
                      band_above_spine02=.030),
        buttons=dict(radius=.0055, standoff=.0022, sides=10, front_count=4, front_top_below_neck=.050,
                     band_count=7, band_half_span=.075, band_below_top=.011),
    ),
    'child_girl_1812': dict(
        bodice=dict(FROCK_SLEEVE, waist_from_spine03_to_shoulder=.30),
        skirt=dict(hem_y=.075, ease=.012, hem_rx=.215, hem_rz_front=.185, hem_rz_back=.195, flare_power=1.15,
                   gathers=16, gather=.010, segments=72, rows=18),
        pinafore=dict(columns_each_side=15, rows_short_of_hem=4, offset=.006, bib_top=.115,
                      bib_half_width=[.074, .062], bib_offset=.005),
    ),
    'child_toddler_1812': dict(
        bodice=dict(FROCK_SLEEVE, ease=.012, smoothing_min_ease=.012, armpit_extra=.006, puff=.013,
                    neck_drop_front=.030, neck_drop_back=.010, neck_drop_side=.016,
                    waist_from_spine03_to_shoulder=.25),
        skirt=dict(hem_y=.050, ease=.011, hem_rx=.175, hem_rz_front=.155, hem_rz_back=.160, flare_power=1.1,
                   gathers=14, gather=.008, segments=72, rows=16),
    ),
    'potawatomi_boy_1812': dict(
        shirt=dict(ease=.013, smoothing=90, smoothing_min_ease=.013, armpit_extra=.012, sleeve_short_of_wrist=.018,
                   top_below_neck=.004),
        tail=dict(hem_from_knee_to_hip=.40, ease=.014, hem_rx=.155, hem_rz_front=.140, hem_rz_back=.085, flare_power=1.3,
                  gathers=10, gather=.006, segments=72, rows=10),
        leggings=dict(ease=.006, bottom_above_ankle=.050, top_above_knee=.10, leg_share=.6),
    ),
    'potawatomi_girl_1812': dict(
        blouse=dict(ease=.013, smoothing=90, smoothing_min_ease=.013, armpit_extra=.010, sleeve_past_elbow=.012,
                    top_below_neck=.006),
        peplum=dict(hem_below_hip=.02, ease=.026, hem_rx=.150, hem_rz_front=.150, hem_rz_back=.085, flare_power=1.0,
                    gathers=12, gather=.006, segments=72, rows=6),
        skirt=dict(hem_from_ankle_to_knee=.45, ease=.012, hem_rx=.150, hem_rz_front=.135, hem_rz_back=.105, flare_power=2.0,
                   gathers=8, gather=.004, segments=72, rows=16, selvage=.022),
        leggings=dict(ease=.006, bottom_above_ankle=.050, top_above_knee=-.03, leg_share=.6),
    ),
}

MATERIALS = {
    'child_boy_1812': {
        'garment_upper__skeleton_jacket_blue_1812': {'base_color_linear': [.030, .040, .095, 1], 'roughness': .86},
        'garment_lower__skeleton_trousers_blue_1812': {'base_color_linear': [.030, .040, .095, 1], 'roughness': .86},
        'accessory__shirt_collar_white_1812': {'base_color_linear': [.72, .71, .66, 1], 'roughness': .84},
        'accessory__horn_buttons_1812': {'base_color_linear': [.10, .085, .065, 1], 'roughness': .45},
        'footwear__child_shoes_black_1812': {'base_color_linear': [.014, .013, .012, 1], 'roughness': .5},
    },
    'child_girl_1812': {
        'garment_upper__frock_bodice_rose_1812': {'base_color_linear': [.40, .22, .20, 1], 'roughness': .88},
        'garment_lower__frock_skirt_rose_1812': {'base_color_linear': [.40, .22, .20, 1], 'roughness': .9},
        'garment_outer__pinafore_linen_1812': {'base_color_linear': [.70, .69, .63, 1], 'roughness': .86},
        'footwear__child_shoes_brown_1812': {'base_color_linear': [.040, .026, .016, 1], 'roughness': .5},
    },
    'child_toddler_1812': {
        'garment_upper__toddler_frock_white_1812': {'base_color_linear': [.66, .65, .61, 1], 'roughness': .86},
        'garment_lower__toddler_frock_white_1812': {'base_color_linear': [.66, .65, .61, 1], 'roughness': .88},
        'footwear__toddler_shoes_red_1812': {'base_color_linear': [.30, .045, .035, 1], 'roughness': .55},
    },
    'potawatomi_boy_1812': {
        'garment_upper__calico_shirt_madder_1812': {'base_color_linear': [.30, .085, .060, 1], 'roughness': .88},
        'garment_lower__stroud_leggings_blue_1812': {'base_color_linear': [.030, .045, .110, 1], 'roughness': .9},
        'footwear__moccasins_smoked_1812': {'base_color_linear': [.17, .11, .065, 1], 'roughness': .8},
    },
    'potawatomi_girl_1812': {
        'garment_upper__calico_blouse_rose_1812': {'base_color_linear': [.36, .11, .14, 1], 'roughness': .88},
        'garment_lower__stroud_skirt_blue_1812': {'base_color_linear': [.022, .030, .080, 1], 'roughness': .9},
        'garment_lower__stroud_selvage_white_1812': {'base_color_linear': [.58, .57, .52, 1], 'roughness': .9},
        'garment_lower__stroud_leggings_red_1812': {'base_color_linear': [.28, .032, .030, 1], 'roughness': .9},
        'footwear__moccasins_smoked_1812': {'base_color_linear': [.17, .11, .065, 1], 'roughness': .8},
    },
}

# `weave` names the material the builder lays its one-texel cloth weave on. The builder writes
# that material's LINEAR colour into an sRGB image (tools/human_teamster_blend.py, the woven
# texture), so the cloth it lands on draws far darker than its recipe colour (a rose bodice
# went maroon, a blue jacket black). Each child puts it on the shoes, where dark leather barely
# changes (the Potawatomi boy's moccasins do draw darker than smoked deerskin); the Potawatomi
# girl puts it on the stroud's white selvage, which draws a light grey. The fix belongs in the
# builder (notes file, rows for shared files).
ROLES = {
    'child_boy_1812': dict(body='male_8', assembly='child_boy_1812_v1', recipe='data/humans/recipes/child_boy_1812.json',
                           person='anonymous_child_boy_1812', shoe='footwear__child_shoes_black_1812',
                           weave='footwear__child_shoes_black_1812', skirt=False),
    'child_girl_1812': dict(body='female_8', assembly='child_girl_1812_v1', recipe='data/humans/recipes/child_girl_1812.json',
                            person='anonymous_child_girl_1812', shoe='footwear__child_shoes_brown_1812',
                            weave='footwear__child_shoes_brown_1812', skirt=True),
    'child_toddler_1812': dict(body='either_3', assembly='child_toddler_1812_v1',
                               recipe='data/humans/recipes/child_toddler_1812.json',
                               person='anonymous_child_toddler_1812', shoe='footwear__toddler_shoes_red_1812',
                               weave='footwear__toddler_shoes_red_1812', skirt=True),
    # The Potawatomi children of the camp (T-3467's research, docs/RESEARCH/people-1812-3467/day.json
    # `dress.potawatomi_child_1812`); review_required and touches_removal with their own prose.
    'potawatomi_boy_1812': dict(body='male_8', assembly='potawatomi_boy_1812_v1',
                                recipe='data/humans/recipes/potawatomi_boy_1812.json',
                                person='anonymous_potawatomi_boy_1812', shoe='footwear__moccasins_smoked_1812',
                                weave='footwear__moccasins_smoked_1812', skirt=False, native=True),
    'potawatomi_girl_1812': dict(body='female_8', assembly='potawatomi_girl_1812_v1',
                                 recipe='data/humans/recipes/potawatomi_girl_1812.json',
                                 person='anonymous_potawatomi_girl_1812', shoe='footwear__moccasins_smoked_1812',
                                 weave='garment_lower__stroud_selvage_white_1812', skirt=True, native=True),
}


def _bones(body):
    return {b['name']: b for b in body['skeleton']}


def _height(body):
    return max(p[1] for m in body['meshes'] for p in m['positions_m'])


def _leg(bones):
    h, k, a = (bones[n]['head_m'] for n in ('thigh_l', 'calf_l', 'foot_l'))
    return math.dist(h, k)+math.dist(k, a)


def _arm_share(w):
    return math.fsum(x for b, x in w.items() if b.startswith(('upperarm', 'lowerarm')))


def _merge(name, material, meshes):
    out = empty(name, material)
    for m in meshes:
        base = len(out['positions_m'])
        for k in ('positions_m', 'uvs', 'weights', 'corner_uvs'):
            out[k] += m[k]
        out['triangles'] += [[i+base for i in f] for f in m['triangles']]
    return out


def _drape(mesh, bones, lo, ease, sigma=.015):
    """Smooth the chest under the cloth: a child's nipples, areolae and navel showed through
    every shell at 3 m (the shell is cut from the body's own dense topology there, so its
    small relief and the noise of the dense rings shade like the anatomy). Each front-facing
    garment point between `lo` and just under the shoulder, off the arm, takes the depth (z
    only; x, y, skinning and UVs kept) of a moving least-squares quadratic through the front
    of the garment round it: Gaussian weights of `sigma`, each sample weighted by its own
    surface area, so the many tiny triangles of a nipple count for what they cover and the
    fit reproduces the chest's own curvature without shrinking it. The change fades to nothing
    over 2 cm at the zone's edges and is clamped to the ease less 4 mm inward, so the cloth
    stays outside the skin. (The shared cloth envelope, cloth_torso, was tried first: it
    inflates every section to its circumscribed ellipse and ballooned a child's chest and back
    into a barrel; a Laplacian diffusion sank the dense nipple patches into dishes.)"""
    ps = mesh['positions_m']; normals = mesh['_normals']
    shoulder = bones['upperarm_l']['head_m'][1]; hi = shoulder-.02
    cz = bones['spine_02']['head_m'][2]
    reach = 3*sigma
    def front(i, margin):
        p, n = ps[i], normals[i]
        return (lo-.02-margin <= p[1] <= hi+.02+margin and abs(p[0]) < .14 and n[2] > .2 and p[2] > cz
                and _arm_share(mesh['weights'][i]) < .25)
    zone = [i for i in range(len(ps)) if front(i, 0.)]
    area = [0.]*len(ps)
    for f in mesh['triangles']:
        a, b, c = (ps[k] for k in f)
        u = [b[m]-a[m] for m in range(3)]; v = [c[m]-a[m] for m in range(3)]
        A = .5*math.hypot(u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        for k in f:
            area[k] += A/3
    samples = [(list(ps[i]), area[i]) for i in range(len(ps)) if front(i, reach) and area[i] > 0]
    def solve(a, b):
        n = len(b)
        for c in range(n):
            r = max(range(c, n), key=lambda k: abs(a[k][c]))
            if abs(a[r][c]) < 1e-18:
                return None
            a[c], a[r] = a[r], a[c]; b[c], b[r] = b[r], b[c]
            for k in range(c+1, n):
                f = a[k][c]/a[c][c]
                for m in range(c, n):
                    a[k][m] -= f*a[c][m]
                b[k] -= f*b[c]
        x = [0.]*n
        for c in range(n-1, -1, -1):
            x[c] = (b[c]-math.fsum(a[c][m]*x[m] for m in range(c+1, n)))/a[c][c]
        return x
    cap = max(0., ease-.004)
    new = {}
    for i in zone:
        p = ps[i]
        ata = [[0.]*6 for _ in range(6)]; atb = [0.]*6; count = 0
        for q, wa in samples:
            dx, dy = q[0]-p[0], q[1]-p[1]
            d2 = dx*dx+dy*dy
            if d2 > reach*reach:
                continue
            w = wa*math.exp(-d2/(2*sigma*sigma)); count += 1
            row = (1., dx, dy, dx*dx, dx*dy, dy*dy)
            for a in range(6):
                wr = w*row[a]; atb[a] += wr*q[2]
                for b in range(a, 6):
                    ata[a][b] += wr*row[b]
        if count < 12:
            continue
        for a in range(6):
            for b in range(a):
                ata[a][b] = ata[b][a]
        c = solve(ata, atb)
        if c is not None:
            new[i] = c[0]
    moved = 0; deepest = 0.; highest = 0.
    for i, zi in new.items():
        p = ps[i]
        fade = max(0., min(1., (p[1]-(lo-.02))/.02, ((hi+.02)-p[1])/.02, (.14-abs(p[0]))/.02))
        d = max(-cap, zi-p[2])*fade
        if abs(d) > 1e-6:
            ps[i] = [p[0], p[1], p[2]+d]; moved += 1
            deepest = max(deepest, -d); highest = max(highest, d)
    return dict(lower_y_m=lo, upper_y_m=hi, sigma_m=sigma, affected_vertices=moved,
                maximum_inward_m=deepest, maximum_outward_m=highest, inward_cap_m=cap)


def _button_at(out, mesh, x, y, t):
    """One flat round button on `mesh`'s front at (x, y), skinned as the cloth under it."""
    z0, w = G._surface_sample(mesh, x, y)
    c = len(out['positions_m'])
    out['positions_m'].append([x, y, z0+t['standoff']+.0012]); out['uvs'].append([.5, .5]); out['weights'].append(w)
    n = t['sides']
    for k in range(n):
        a = 2*math.pi*k/n
        xx, yy = x+t['radius']*math.cos(a), y+t['radius']*math.sin(a)
        try:
            z, _ = G._surface_sample(mesh, xx, yy)
        except ValueError:
            z = z0
        out['positions_m'].append([xx, yy, z+t['standoff']]); out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)])
        out['weights'].append(w)
    for k in range(n):
        out['triangles'].append([c, c+1+k, c+1+(k+1) % n])


# ---------------------------------------------------------------------------------------
# The boy: a skeleton suit.

def boy_jacket(body, bones):
    """The short jacket, closed, long sleeves to the wrist, from a little above the natural
    waist (hidden under the trousers) to just under the neck."""
    t = TAILORING['child_boy_1812']['jacket']
    neck = bones['neck_01']['head_m'][1]
    lo = bones['spine_01']['head_m'][1]+t['hem_above_spine01']; hi = neck-t['top_below_neck']
    wrist = abs(bones['hand_l']['head_m'][0])-t['sleeve_short_of_wrist']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: wrist-v['p'][0], lambda v: wrist+v['p'][0]]
    out = G._poly_shell(body, bones, 'skeleton_jacket', 'garment_upper__skeleton_jacket_blue_1812', fields, t['ease'],
                        [(lo, hi)], neck, None, smooth=(t['smoothing'], t['smoothing_min_ease']))
    eased = G._armpit_ease(out, body, bones, t['armpit_extra'])
    band_top = bones['spine_02']['head_m'][1]+TAILORING['child_boy_1812']['trousers']['band_above_spine02']
    drape = _drape(out, bones, band_top, t['ease'])
    out['receipt'] = dict(garment='skeleton suit jacket, closed, long sleeves', hem_y_m=lo, top_y_m=hi, sleeve_end_x_m=wrist,
                          armpit_points_eased=eased, ease_m=t['ease'], drape=drape)
    return out


def boy_collar(jacket, bones):
    """The shirt's wide collar turned out over the jacket: a band of the jacket's own surface
    round the neck, deepest behind, open a little at the throat, stood off the jacket and
    skinned as it is. The pictures' frill can scallop the outer edge (frill_waves/frill_depth);
    at the scale drawn it read as a jagged edge, so it is drawn plain (both zero)."""
    t = TAILORING['child_boy_1812']['collar']
    neck = bones['neck_01']['head_m']
    def depth(v):
        dx, dz = v['p'][0]-neck[0], v['p'][2]-neck[2]
        a = math.atan2(dx, dz)                       # 0 front, +-pi back
        f = .5+.5*math.cos(a)                        # 1 front, 0 back
        side = abs(math.sin(a))
        base = t['depth_back']+(t['depth_front']-t['depth_back'])*f
        base = base*(1-side)+t['depth_side']*side
        return base-t['frill_depth']*.5*(1-math.cos(t['frill_waves']*a))
    fields = [lambda v: v['p'][1]-(neck[1]-depth(v)), lambda v: t['half_width']-abs(v['p'][0]),
              lambda v: max(abs(v['p'][0])-t['front_gap'], -v['p'][2]+neck[2])]
    out = S._on_garment(jacket, fields, 'shirt_collar', 'accessory__shirt_collar_white_1812', t['offset'])
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='wide shirt collar over the jacket, drawn plain', depth_front_m=t['depth_front'],
                          depth_back_m=t['depth_back'], half_width_m=t['half_width'], frill_waves=t['frill_waves'])
    return out


def boy_trousers(body, bones, height):
    """Long trousers on the shared workwear shell, lengthened to the instep, with a high band
    of the body's own surface carrying them up over the jacket's hem to the ribs."""
    t = TAILORING['child_boy_1812']['trousers']
    waist_fraction = bones['spine_01']['head_m'][1]/height
    recipe = dict(waist_height_fraction=waist_fraction, shirt_hem_fraction=waist_fraction-.02,
                  workwear_tailoring_v5=dict(waistcoat_closed_front_torso_fraction=.4,
                                             trouser_cuff_radius_ratio=t['cuff_radius_ratio'],
                                             trouser_added_section_ease_m=t['added_section_ease'],
                                             trouser_thigh_transition_fraction=t['thigh_transition_fraction']))
    legs = garment_shell(body['meshes'][0], 'trousers', t['ease'], recipe, bones, height)
    legs = G._lengthen_hems(legs, bones, t)
    legs = finish_edges(legs, .0015)
    legs['name'] = 'skeleton_trousers'; legs['material'] = 'garment_lower__skeleton_trousers_blue_1812'
    for k in ('source_basis', 'source_triangle_indices'):
        legs.pop(k, None)
    lo = waist_fraction*height-t['band_below_waist']; hi = bones['spine_02']['head_m'][1]+t['band_above_spine02']
    neck = bones['neck_01']['head_m'][1]
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: .35-G._arm_mass(v)]
    band = G._poly_shell(body, bones, 'skeleton_trousers_band', 'garment_lower__skeleton_trousers_blue_1812', fields,
                         t['band_ease'], [(lo, hi)], neck, None)
    band.pop('_normals', None)
    band = finish_edges(band, .0015)
    band['receipt'] = dict(garment='trousers rising high over the jacket hem', bottom_y_m=lo, top_y_m=hi, ease_m=t['band_ease'])
    return legs, band, hi


def boy_buttons(jacket, band, bones, band_top):
    """The jacket's buttons down the front above the trousers, and the row round the front
    of the trousers' top that buttons them onto the jacket."""
    t = TAILORING['child_boy_1812']['buttons']
    out = empty('suit_buttons', 'accessory__horn_buttons_1812')
    neck = bones['neck_01']['head_m'][1]
    top = neck-t['front_top_below_neck']; bottom = band_top+.02
    for i in range(t['front_count']):
        _button_at(out, jacket, 0., top-(top-bottom)*i/(t['front_count']-1), t)
    y = band_top-t['band_below_top']
    for i in range(t['band_count']):
        _button_at(out, band, -t['band_half_span']+2*t['band_half_span']*i/(t['band_count']-1), y, t)
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='horn buttons: jacket front and trouser band', front=t['front_count'], band=t['band_count'])
    return out


def construct_boy(body):
    bones = _bones(body); height = _height(body)
    jacket = boy_jacket(body, bones)
    collar = boy_collar(jacket, bones)
    legs, band, band_top = boy_trousers(body, bones, height)
    buttons = boy_buttons(jacket, band, bones, band_top)
    jacket.pop('_normals', None)
    return [finish_edges(jacket, .0015), collar, legs, band, buttons], [
        'Cut, ease, lengths and colours are reconstructed; the pictures are of Baltimore and rural Pennsylvania children',
        'No cloth simulation: the shells follow the body bones',
        'The shirt shows only as its collar; no white stockings show under the long trousers',
        'Bare head: the Rutter boy is painted bareheaded; a round hat out of doors is not made']


# ---------------------------------------------------------------------------------------
# The frock (girl and toddler).

def frock_bodice(body, bones, t, material):
    """A high-waisted bodice: the body's own surface from the high waist under the chest to a
    wide round neck, short sleeves puffed out from the shoulder seam and gathered back into
    a band on the upper arm."""
    neck = bones['neck_01']['head_m']; s3 = bones['spine_03']['head_m'][1]; sh = bones['upperarm_l']['head_m'][1]
    waist = s3+t['waist_from_spine03_to_shoulder']*(sh-s3)
    ua = abs(bones['upperarm_l']['head_m'][0]); la = abs(bones['lowerarm_l']['head_m'][0])
    end = ua+t['sleeve_of_upperarm']*(la-ua)
    def neckline(v):
        dx, dz = v['p'][0]-neck[0], v['p'][2]-neck[2]
        a = math.atan2(dx, dz); f = .5+.5*math.cos(a); side = abs(math.sin(a))
        drop = t['neck_drop_back']+(t['neck_drop_front']-t['neck_drop_back'])*f
        return neck[1]-(drop*(1-side)+t['neck_drop_side']*side)
    fields = [lambda v: v['p'][1]-waist, lambda v: neckline(v)-v['p'][1], lambda v: end-v['p'][0], lambda v: end+v['p'][0]]
    out = G._poly_shell(body, bones, 'frock_bodice', material, fields, t['ease'], [(waist, neck[1])], neck[1], None,
                        smooth=(t['smoothing'], t['smoothing_min_ease']))
    G._armpit_ease(out, body, bones, t['armpit_extra'])
    puffed = 0
    for i, (p, w) in enumerate(zip(out['positions_m'], out['weights'])):
        arm = _arm_share(w); x = abs(p[0])
        if arm <= .05 or x <= ua-.01:
            continue
        u = min(1., max(0., (x-(ua-.01))/(end-(ua-.01))))
        g = t['puff']*math.sin(math.pi*min(1., u*1.08))**.7*min(1., arm/.5)
        if u > .9:
            g *= max(0., (1-u)/.1)
        n = out['_normals'][i]
        out['positions_m'][i] = [p[a]+g*n[a] for a in range(3)]
        puffed += 1
    drape = _drape(out, bones, waist, t['ease'])
    out.pop('_normals', None)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='high-waisted frock bodice, short puffed sleeves, round neck', waist_y_m=waist,
                          sleeve_end_x_m=end, puffed_points=puffed, neck_drop_front_m=t['neck_drop_front'], drape=drape)
    return out, waist


def frock_skirt(body, bones, waist, upper, t, material, name):
    """The frock's skirt from the high waist to the hem: rings lofted round the body's own
    sections (each ring's support polygon holds the complete body slabs above and below it,
    `ease` out), widening A-line to an elliptical hem, with broad soft gathers; its top closed
    against the bodice. Above the natural waist it rides the spine, below it the pelvis and
    each leg (leg_follow, T-3423)."""
    segments, rows = t['segments'], t['rows']
    need(segments >= 48 and segments % 12 == 0 and rows >= 6, 'unsupported skirt discretization')
    hem = t['hem_y']
    levels = [waist+(hem-waist)*i/(rows-1) for i in range(rows)]
    natural = bones['spine_01']['head_m'][1]
    follow = leg_follow(bones, natural)
    cz = bones['spine_01']['head_m'][2]
    tris = [[m['positions_m'][i] for i in f] for m in body['meshes'] for f in m['triangles']
            if min(m['positions_m'][i][1] for i in f) <= waist+.01 and max(m['positions_m'][i][1] for i in f) >= hem]
    normals = [(math.sin(2*math.pi*(k+.5)/segments), math.cos(2*math.pi*(k+.5)/segments)) for k in range(segments)]
    body_support = []
    for i, y in enumerate(levels):
        pts = _slab_points(tris, levels[min(rows-1, i+1)], levels[max(0, i-1)])
        need(bool(pts), 'empty body skirt band')
        body_support.append([max(nx*p[0]+nz*p[2] for p in pts)+t['ease'] for nx, nz in normals])
    def hem_support(nx, nz):
        rz = t['hem_rz_front'] if nz > 0 else t['hem_rz_back']
        return nz*cz+math.hypot(t['hem_rx']*nx, rz*nz)
    supports = []
    for i in range(rows):
        f = (i/(rows-1))**t['flare_power']
        supports.append([max(body_support[i][k], (1-f)*body_support[0][k]+f*hem_support(*normals[k]))
                         for k in range(segments)])
    out = empty(name, material)
    for i, y in enumerate(levels):
        for k in range(segments):
            nx0, nz0 = normals[(k-1) % segments]; nx1, nz1 = normals[k]
            a, b = supports[i][(k-1) % segments], supports[i][k]
            det = nx0*nz1-nx1*nz0
            x, z = (a*nz1-b*nz0)/det, (nx0*b-nx1*a)/det
            need(x*math.sin(2*math.pi*k/segments)+(z-cz)*math.cos(2*math.pi*k/segments) > 0, 'invalid polar support polygon')
            u = i/(rows-1)
            gather = t['gather']*(.25+.75*u**.6)*.5*(1-math.cos(t['gathers']*2*math.pi*k/segments))
            r = math.hypot(x, z-cz); fac = 1+gather/r
            p = [x*fac, y, cz+(z-cz)*fac]
            out['positions_m'].append(p); out['uvs'].append([k/segments, u])
            if y >= natural:
                s = min(1., (y-natural)/max(1e-6, waist-natural))
                out['weights'].append({'spine_01': s, 'pelvis': 1-s} if s < 1 else {'spine_01': 1.})
            else:
                out['weights'].append(follow(p))
    margin = math.inf
    for i in range(rows-1):
        for k, (nx, nz) in enumerate(normals):
            n = (k+1) % segments
            for f in ([i*segments+k, (i+1)*segments+n, i*segments+n], [i*segments+k, (i+1)*segments+k, (i+1)*segments+n]):
                out['triangles'].append(f)
                out['corner_uvs'].append([[((v % segments)/segments if v % segments else (1. if k == segments-1 else 0.)),
                                           (v//segments)/(rows-1)] for v in f])
                for v in f:
                    p = out['positions_m'][v]; s = (p[1]-levels[i])/(levels[i+1]-levels[i])
                    margin = min(margin, nx*p[0]+nz*p[2]-((1-s)*supports[i][k]+s*supports[i+1][k]))
    need(margin >= -1e-10, 'fold triangle enters the body-clearance core')
    clearance = math.inf
    for i in range(rows-1):
        for p in _slab_points(tris, levels[i+1], levels[i]):
            s = (p[1]-levels[i])/(levels[i+1]-levels[i])
            for k, (nx, nz) in enumerate(normals):
                clearance = min(clearance, (1-s)*supports[i][k]+s*supports[i+1][k]-nx*p[0]-nz*p[2])
    need(clearance >= t['ease']-1e-10, 'standing skirt core intersects source anatomy')
    # Close the top against the actual bodice (the dress components' construction).
    join_y = waist+.012
    sections = []
    for face in upper['triangles']:
        tri = [upper['positions_m'][i] for i in face]
        if min(p[1] for p in tri) <= join_y <= max(p[1] for p in tri):
            unique = list(dict.fromkeys(tuple(p) for p in _slab_points([tri], join_y, join_y)))
            if len(unique) == 2:
                sections.append(unique)
    inner = []; found = []
    for k in range(segments):
        dx, dz = math.sin(2*math.pi*k/segments), math.cos(2*math.pi*k/segments)
        radii = []
        for a, b in sections:
            ux, uz = b[0]-a[0], b[2]-a[2]; ax, az = a[0], a[2]-cz
            den = ux*dz-uz*dx
            if abs(den) < 1e-14:
                continue
            s = -(ax*dz-az*dx)/den
            if -1e-10 <= s <= 1+1e-10:
                r = (ax+s*ux)*dx+(az+s*uz)*dz
                if r > 0:
                    radii.append(r)
        found.append(max(radii) if radii else None)
    # A ray may slip between sections where a sliver triangle cut to one point (the smoothed
    # bodice has many): it takes the smaller of its nearest found neighbours either way round.
    # Most rays must find the bodice; a run longer than four is refused.
    need(sum(f is not None for f in found) >= .75*segments, 'waist closure has no bodice cross-section')
    filled = list(found)
    for k in range(segments):
        if found[k] is None:
            near = []
            for step in (1, -1):
                for d in range(1, 5):
                    if found[(k+step*d) % segments] is not None:
                        near.append(found[(k+step*d) % segments]); break
            need(len(near) == 2, 'waist closure has no bodice cross-section')
            filled[k] = min(near)
    found = filled
    for k in range(segments):
        dx, dz = math.sin(2*math.pi*k/segments), math.cos(2*math.pi*k/segments)
        r = found[k]-.0015
        need(r > .02, 'waist closure underlap exceeds bodice radius')
        inner.append(len(out['positions_m']))
        out['positions_m'].append([r*dx, join_y, cz+r*dz]); out['uvs'].append([k/segments, .02])
        out['weights'].append({'spine_01': 1.})
    for k in range(segments):
        n = (k+1) % segments
        for face, uv in (([k, n, inner[n]], [[k/segments, 0], [(k+1)/segments, 0], [(k+1)/segments, .02]]),
                         ([k, inner[n], inner[k]], [[k/segments, 0], [(k+1)/segments, .02], [k/segments, .02]])):
            out['triangles'].append(face); out['corner_uvs'].append(uv)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='frock skirt, high waist to hem', waist_y_m=waist, hem_y_m=hem,
                          standing_body_core_clearance_m=clearance, minimum_fold_panel_margin_m=margin,
                          hem_radii_m=[t['hem_rx'], t['hem_rz_front'], t['hem_rz_back']], gathers=t['gathers'],
                          skinning='spine above the natural waist, pelvis and each leg below it (leg_follow)')
    return out


def pinafore_skirt(skirt, t, rows, segments):
    """The pinafore's apron: a broad panel on the frock skirt's own surface round the front and
    sides, from the waist to `rows_short_of_hem` rows above the hem, stood off it."""
    out = empty('pinafore_apron', 'garment_outer__pinafore_linen_1812')
    cols = list(range(-t['columns_each_side'], t['columns_each_side']+1))
    last = rows-t['rows_short_of_hem']
    P = skirt['positions_m']
    cz = math.fsum(P[k][2] for k in range(segments))/segments
    for row in range(last):
        for col in cols:
            k = col % segments; base = P[row*segments+k]
            r = math.hypot(base[0], base[2]-cz)
            out['positions_m'].append([base[0]*(1+t['offset']/r), base[1]+.001, cz+(base[2]-cz)*(1+t['offset']/r)])
            out['uvs'].append([(col-cols[0])/(cols[-1]-cols[0]), row/(last-1)])
            out['weights'].append(dict(skirt['weights'][row*segments+k]))
    width = len(cols)
    for row in range(last-1):
        for k in range(width-1):
            a = row*width+k; b = a+1; c = a+width+1; d = a+width
            for f in ([a, c, b], [a, d, c]):
                out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][i] for i in f])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='pinafore apron', columns=width, of_segments=segments, rows=last)
    return out


def construct_frock(body, role):
    bones = _bones(body); T = TAILORING[role]
    upper_mat, lower_mat = [m for m in MATERIALS[role] if m.startswith(('garment_upper', 'garment_lower'))]
    bodice, waist = frock_bodice(body, bones, T['bodice'], upper_mat)
    skirt = frock_skirt(body, bones, waist, bodice, T['skirt'], lower_mat, 'frock_skirt')
    parts = [bodice, skirt]
    limits = ['Cut, ease, lengths and colours are reconstructed; the pictures are of eastern children in their best',
              'No cloth simulation: the skirt rides the spine above the natural waist and the pelvis and legs below',
              'Bare head: no cap or bonnet is made']
    if 'pinafore' in T:
        p = T['pinafore']; s = T['skirt']
        apron = pinafore_skirt(skirt, p, s['rows'], s['segments'])
        bib = apron_bib(bodice, bones, waist, top=p['bib_top'], half_width=tuple(p['bib_half_width']), offset=p['bib_offset'])
        bib['name'] = 'pinafore_bib'; bib['material'] = 'garment_outer__pinafore_linen_1812'
        parts += [apron, bib]
        limits.append('The pinafore is reconstructed: a bib pinned on the breast over a broad apron; no straps or ties are made')
    return parts, limits


# ---------------------------------------------------------------------------------------
# The Potawatomi children of the camp: trade cloth (calico, stroud), leggings, moccasins.

def _upper_shell(body, bones, t, name, material, lo, sleeve_end):
    """A garment of the body's own surface from `lo` to just under the neck, sleeves to
    `sleeve_end`, smoothed off the anatomy and eased under the arm (the jacket's method)."""
    neck = bones['neck_01']['head_m'][1]; hi = neck-t['top_below_neck']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: sleeve_end-v['p'][0], lambda v: sleeve_end+v['p'][0]]
    out = G._poly_shell(body, bones, name, material, fields, t['ease'], [(lo, hi)], neck, None,
                        smooth=(t['smoothing'], t['smoothing_min_ease']))
    G._armpit_ease(out, body, bones, t['armpit_extra'])
    drape = _drape(out, bones, lo, t['ease'])
    out.pop('_normals', None)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(bottom_y_m=lo, top_y_m=hi, sleeve_end_x_m=sleeve_end, ease_m=t['ease'], drape=drape)
    return out


def leggings(body, bones, t, material):
    """A legging on each leg: the leg's own surface from a little above the ankle (inside the
    moccasin's top) to `top_above_knee` over the knee, stood `ease` off it, skinned as the leg."""
    knee = bones['calf_l']['head_m'][1]; ankle = bones['foot_l']['head_m'][1]
    lo = ankle+t['bottom_above_ankle']; hi = knee+t['top_above_knee']
    def leg(v):
        return math.fsum(x for b, x in v['w'].items() if b.startswith(('thigh', 'calf', 'foot')))
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: leg(v)-t['leg_share']]
    out = G._poly_shell(body, bones, 'stroud_leggings', material, fields, t['ease'], [(lo, hi)],
                        bones['neck_01']['head_m'][1], None)
    out.pop('_normals', None)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='stroud leggings', bottom_y_m=lo, top_y_m=hi, ease_m=t['ease'])
    return out


def construct_potawatomi_boy(body):
    bones = _bones(body); T = TAILORING['potawatomi_boy_1812']
    natural = bones['spine_01']['head_m'][1]
    wrist = abs(bones['hand_l']['head_m'][0])-T['shirt']['sleeve_short_of_wrist']
    shirt = _upper_shell(body, bones, T['shirt'], 'calico_shirt', 'garment_upper__calico_shirt_madder_1812', natural, wrist)
    shirt['receipt']['garment'] = 'calico shirt, long sleeves, worn outside'
    tt = dict(T['tail']); knee = bones['calf_l']['head_m'][1]; hip = bones['thigh_l']['head_m'][1]
    tt['hem_y'] = knee+tt['hem_from_knee_to_hip']*(hip-knee)
    tail = frock_skirt(body, bones, natural, shirt, tt, 'garment_upper__calico_shirt_madder_1812', 'calico_shirt_tail')
    tail['receipt']['garment'] = 'the shirt hanging loose to mid-thigh'
    legs = leggings(body, bones, T['leggings'], 'garment_lower__stroud_leggings_blue_1812')
    return [shirt, tail, legs], [
        'Reconstructed from the research\'s reading of trade goods and of Winter\'s 1837 picture (reference only, not cleared, nothing taken from it)',
        'The breechcloth is under the long shirt and is not made; the leggings stop above the knee',
        'Bare head, hair plain (the short cut every figure shares); no ornament, paint or feather',
        'No cloth simulation: the shirt\'s tail rides the spine above the natural waist and the legs below']


def construct_potawatomi_girl(body):
    bones = _bones(body); T = TAILORING['potawatomi_girl_1812']
    natural = bones['spine_01']['head_m'][1]
    elbow = abs(bones['lowerarm_l']['head_m'][0])+T['blouse']['sleeve_past_elbow']
    blouse = _upper_shell(body, bones, T['blouse'], 'calico_blouse', 'garment_upper__calico_blouse_rose_1812', natural, elbow)
    blouse['receipt']['garment'] = 'calico over-blouse, sleeves to the elbow'
    knee = bones['calf_l']['head_m'][1]; ankle = bones['foot_l']['head_m'][1]; hip = bones['thigh_l']['head_m'][1]
    st = dict(T['skirt']); st['hem_y'] = ankle+st['hem_from_ankle_to_knee']*(knee-ankle)
    skirt = frock_skirt(body, bones, natural, blouse, st, 'garment_lower__stroud_skirt_blue_1812', 'wrapped_skirt')
    selvage_top = st['hem_y']+st['selvage']
    blue = S._split(skirt, lambda c: c[1] >= selvage_top, 'wrapped_skirt', 'garment_lower__stroud_skirt_blue_1812')
    white = S._split(skirt, lambda c: c[1] < selvage_top, 'wrapped_skirt_selvage', 'garment_lower__stroud_selvage_white_1812')
    blue['receipt'] = dict(skirt['receipt'], garment='wrapped stroud skirt to mid-calf')
    white['receipt'] = dict(garment='the stroud\'s white selvage at the hem', height_m=st['selvage'])
    pt = dict(T['peplum']); pt['hem_y'] = hip-pt['hem_below_hip']
    peplum = frock_skirt(body, bones, natural, blouse, pt, 'garment_upper__calico_blouse_rose_1812', 'calico_blouse_skirt')
    # The blouse hangs over the skirt: every peplum ring stands outside the skirt's ring at its height.
    rows = pt['rows']; seg = pt['segments']; srows = st['rows']; sseg = st['segments']
    P, Q = peplum['positions_m'], skirt['positions_m']
    cz = bones['spine_01']['head_m'][2]
    for i in range(1, rows):
        y = P[i*seg][1]
        j = min(range(srows), key=lambda r: abs(Q[r*sseg][1]-y))
        for k in range(seg):
            a, b = P[i*seg+k], Q[j*sseg+k]
            need(math.hypot(a[0], a[2]-cz) > math.hypot(b[0], b[2]-cz)+.003, 'the blouse sinks into the skirt')
    peplum['receipt']['garment'] = 'the blouse hanging over the skirt to the hips'
    legs = leggings(body, bones, T['leggings'], 'garment_lower__stroud_leggings_red_1812')
    return [blouse, peplum, blue, white, legs], [
        'Reconstructed from the research\'s reading of trade goods and of Winter\'s 1837 picture (reference only, not cleared, nothing taken from it)',
        'No kerchief, brooches, beads or ear-bobs are made; no ribbonwork (pictured from about 1840)',
        'Hair plain (the short cut every figure shares), not the long parted hair the research describes for women',
        'No cloth simulation: the skirt rides the spine above the natural waist and the pelvis and legs below']


# ---------------------------------------------------------------------------------------

def child_walk(body):
    """The builder's baked walk (tools/human_grounded_gait.py) is drawn at 0.6 m/s on a 1.2 s
    cycle with a 4 cm pelvis drop and a 6.5 cm swing lift for an adult's 0.86 m leg; a child's
    leg cannot reach those steps (the solver refuses them). For a child body the same cycle
    is scaled by the leg: speed, drop and lift times leg/0.86, so the stride keeps the adult
    clip's proportion to the leg. Returns the scaled values; apply_child_walk() sets them for
    the build. The runtime gait (renderers/web/js/human-gait.js) replaces this clip's legs on
    the walk anyway; this is the clip the asset carries."""
    import human_grounded_gait as GG
    k = _leg(_bones(body))/ADULT_LEG_M
    need(.3 < k < 1., 'child walk scale outside the child range')
    base = getattr(GG, '_adult_walk', (GG.SPEED_M_S, GG.PELVIS_DROP_M, GG.SWING_LIFT_M))
    need(base == (.6, .04, .065), 'the baked walk changed; review the child scaling')
    return dict(scale=k, speed_m_s=base[0]*k, pelvis_drop_m=base[1]*k, swing_lift_m=base[2]*k,
                stride_m=base[0]*k*GG.CYCLE_DURATION_S, cycle_duration_s=GG.CYCLE_DURATION_S)


def apply_child_walk(body):
    """Set the scaled walk for THIS build process only: the gait module's constants (read at
    call time by pose_at_phase/foot_trajectory) and the builder's own copy of the ground speed
    (which it writes into the walk clip's extras), when the running __main__ is the canonical
    builder. A stopgap until the builder takes a walk scale from the recipe
    (docs/RESEARCH/people-1812-dress/children.md, "rows for shared files")."""
    import human_grounded_gait as GG
    main = sys.modules.get('__main__')
    if not str(getattr(main, '__file__', '')).endswith('human_teamster_blend.py'):
        return None
    if getattr(GG, '_child_scaled', False):
        return GG._child_scaled
    w = child_walk(body)
    GG._adult_walk = (GG.SPEED_M_S, GG.PELVIS_DROP_M, GG.SWING_LIFT_M)
    GG.SPEED_M_S = w['speed_m_s']; GG.PELVIS_DROP_M = w['pelvis_drop_m']; GG.SWING_LIFT_M = w['swing_lift_m']
    main.SPEED_M_S = w['speed_m_s']
    GG._child_scaled = w
    return w


def construct(body, role):
    need(role in ROLES, f'unknown child role {role}')
    before = digest(body)
    if role == 'child_boy_1812':
        parts, limits = construct_boy(body)
    elif role == 'potawatomi_boy_1812':
        parts, limits = construct_potawatomi_boy(body)
    elif role == 'potawatomi_girl_1812':
        parts, limits = construct_potawatomi_girl(body)
    else:
        parts, limits = construct_frock(body, role)
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    r = ROLES[role]
    return dict(format='chicago4d_child_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y', forward_axis='+Z',
                grade='reconstructed', assembly=r['assembly'], body_sha256=BODIES[r['body']][1],
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS[role]), shoe_material=r['shoe'], weave_material=r['weave'],
                tailoring=copy.deepcopy(TAILORING[role]), limitations=limits)


def role_of(recipe):
    spec = recipe.get('child_components', {})
    role = spec.get('role')
    need(role in ROLES, 'unknown child role')
    return role, spec


def prepare_child_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3465 (through `role_1812`); never a world switch."""
    root = Path(root).resolve()
    role, spec = role_of(recipe)
    r = ROLES[role]
    need(spec.get('version') == 1 and spec.get('generator') == GENERATOR, 'unsupported child component generator')
    need(recipe.get('role_1812') == {'module': MODULE, 'prepare': PREPARE, 'assembly': r['assembly']},
         'child role recipe names another generator')
    need(variant.get('recipe_path') == r['recipe'] and variant.get('component_assembly') == r['assembly']
         and variant.get('id') == role, 'child assembly is bound to its own recipe')
    need(variant.get('person_reference_id') == r['person'] and variant.get('person_reference_grade') == 'reconstructed'
         and variant.get('reference_summary', {}).get('named') is False, 'a child role is anonymous and reconstructed')
    need(recipe.get('scene_date') == '1812-08-14' and recipe.get('grade') == 'reconstructed',
         'child scene/appearance grade changed')
    if r.get('native'):
        # AGENTS.md standing constraint: the flags stay, each with its own words.
        need(variant.get('review_required') is True and variant.get('touches_removal') is True
             and len(variant.get('review_reason', '')) > 80 and len(variant.get('touches_removal_reason', '')) > 80,
             'a Potawatomi child keeps review_required and touches_removal with their own prose')
    need(spec.get('tailoring') == json.loads(json.dumps(TAILORING[role])), 'recipe tailoring differs from the generator')
    if 'leggings' in TAILORING[role]:
        # The moccasin (the builder's shared shoe, open at 145 mm) stands outside the legging's
        # foot, so its top reads as a clean cuff instead of the legging breaking through it.
        need(recipe.get('workwear_coverage', {}).get('shoe_clearance_m', 0) > TAILORING[role]['leggings']['ease']+.002,
             'the moccasin must stand outside the legging')
    path, sha = BODIES[r['body']]
    need(variant['body_input'] == path, 'child role on another body')
    source = (root/path).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == sha == spec.get('body_sha256'), 'unreviewed child body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'child components require the declared liberty')
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
    bundle = construct(body, role)
    bundle['liberty'] = LIBERTY
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']]
    if r['skirt']:
        bundle['skirt'] = True
    walk = apply_child_walk(body)
    bundle['walk'] = walk or child_walk(body)
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
    p = argparse.ArgumentParser(); p.add_argument('--role', choices=sorted(ROLES), required=True)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    a = p.parse_args()
    raw = (a.root/BODIES[ROLES[a.role]['body']][0]).read_bytes()
    data = construct(json.loads(raw), a.role)
    print(json.dumps({'body_sha256': hashlib.sha256(raw).hexdigest(),
                      'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]},
                     indent=1, default=str))
