# SPDX-License-Identifier: GPL-3.0-or-later
"""A Potawatomi man at the Chicago gathering of August 1812 on the shared portable male rig.

An anonymous man of the camp by the fort on 14 August 1812 (Helm counted "500 warriors 179
women & children" at Wells's council; quaife_1913, Appendix VI), in everyday dress: the
cloth, calico and blankets of the goods distributed on the 13th (Wau-Bun) or the 14th
(Heald), made up as the nearest dated eyewitness describes a Potawatomi man (Keating,
1823). No man of the camp is named here, nothing of the 15th (paint, arms) is worn, and
nothing ceremonial is drawn. The Miami of Wells's escort wear the same: no source read
gives them a distinguishable dress. The pieces (data/humans/recipes/potawatomi_man_1812.json):

  shirt        a printed cotton trade shirt worn loose over the breechcloth to mid-thigh
               (Keating's "short checkered shirt over it"; Hubbard's calico shirt, 1818);
               the 1835 labourer's shirt above the waist, a hanging skirt below it
  breechcloth  blue broadcloth, flaps falling before and behind below the shirt's hem
               (Keating twice: "a breech-cloth of blue broadcloth")
  leggings     scarlet stroud (the camp's new broadcloth; Keating's men wore leather), each
               leg separate, a narrow flap standing out along the outer seam with the cloth's
               undyed white selvage at its edge, gartered below the knee (Keating's Wennebea)
  blanket      a white wool trade blanket wrapped round the waist to the knee, open at the
               front and held by a belt ("secured round his waist by a belt"; Lambert: "In
               warm weather, they fasten it round their waist"), its dark stripes near the
               ends falling at the opening
  silver       a band round each upper arm over the sleeve and three small brooches down the
               shirt front (Wau-Bun's annual presents: "silver-works (comprising arm-bands,
               bracelets, brooches; and ear-bobs)")
  head         bare. The hair is the looks layer's, not the asset's: the T-3467 day research
               reads it "long and tied or clubbed behind" (the hair kit's clubbed_behind_1812
               cut); the head wraps of the 1830s pictures are later and a minority, so no
               wrap is built in. The asset carries the shared short04 cap like every figure.
  moccasins    smoked deer-skin, the shared closed foot loft (Keating)

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with the supplement proposed in
docs/RESEARCH/people-1812-dress/engage-native-men.md. The source anatomy is never changed.
Native depiction under AGENTS.md's standing constraint: the recipe's variant keeps
review_required and touches_removal with its own prose.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_potawatomi_man_assembly() through the recipe's `role_1812`.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty, leg_follow
from human_period_wardrobe import finish_edges
from human_workwear_fit import garment_shell, _slab_points
import human_gentleman_1904 as G
import human_labourer_1835 as L
import human_soldier_1812 as S
import human_engage_1812 as E

BODY_SHA256 = 'e7b088b88ea18bb309ca990ef6c0cafea9420ac152d42d1351c1a9795daa9269'
ASSEMBLY = 'potawatomi_man_1812_v1'
RECIPE = 'data/humans/recipes/potawatomi_man_1812.json'
LIBERTY = E.LIBERTY
PERSON = 'anonymous_potawatomi_man_1812'

# Every dimension of the outfit, in metres (angles in degrees); the recipe repeats them for
# review and the builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=copy.deepcopy(L.TAILORING['shirt']),
    shirt_skirt=dict(top_y=1.030, hem_y=.700, ease=.022, segments=64, rows=9, fold=.006, folds=7),
    breechcloth=dict(top_y=.800, hem_front_y=.520, hem_back_y=.545, ease=.016, half_width_deg=34., rows=7, cols=9),
    leggings=dict(ease=.011, waist_height_fraction=.585, cuff_radius_ratio=.95, added_section_ease=.012,
                  thigh_transition_fraction=.65, hem_front_y=.072, hem_back_y=.050, top_y=.780,
                  flap=.032, selvage=.009, flap_back_deg=24., flap_top_y=.760, flap_bottom_y=.090, flap_rows=16),
    brooches=dict(radius=.011, count=3, first_below_neck=.135, step=.045, standoff=.003, sides=12),
    garters=dict(centre_below_knee=.050, height=.026, ease=.004, segments=24, rows=3, roll=.002),
    blanket=dict(top_y=1.040, hem_y=.505, ease_top=.030, ease=.052, segments=72, rows=12, open_top_deg=30., open_hem_deg=42.,
                 fold=.026, folds=13, corner_droop=.035, stripe_from_edge=.050, stripe_width=.045),
    belt=dict(bottom_y=1.002, top_y=1.040, ease=.004, segments=48, rows=3, roll=.002),
    arm_bands=dict(centre_from_shoulder=.115, width=.032, ease=.003, segments=24),
)

MATERIALS = {
    'garment_upper__shirt_check_blue_1812': {'base_color_linear': [.27, .30, .37, 1], 'roughness': .86},
    'garment_lower__leggings_stroud_scarlet_1812': {'base_color_linear': [.26, .045, .035, 1], 'roughness': .9},
    'garment_lower__leggings_selvage_white_1812': {'base_color_linear': [.60, .58, .52, 1], 'roughness': .9},
    'garment_lower__breechcloth_broadcloth_blue_1812': {'base_color_linear': [.022, .032, .085, 1], 'roughness': .9},
    'garment_outer__blanket_wool_white_1812': {'base_color_linear': [.47, .45, .39, 1], 'roughness': .95},
    'garment_outer__blanket_stripe_dark_1812': {'base_color_linear': [.025, .03, .06, 1], 'roughness': .95},
    'accessory__belt_leather_1812': {'base_color_linear': [.06, .035, .02, 1], 'roughness': .6},
    'accessory__garters_woven_dark_1812': {'base_color_linear': [.035, .04, .075, 1], 'roughness': .9},
    'accessory__silver_1812': {'base_color_linear': [.40, .40, .39, 1], 'roughness': .32},
    'footwear__moccasins_smoked_1812': {'base_color_linear': [.15, .095, .052, 1], 'roughness': .88},
}
SHOE_MATERIAL = 'footwear__moccasins_smoked_1812'
WEAVE_MATERIAL = 'garment_upper__shirt_check_blue_1812'


def _tris(*meshes):
    return [[m['positions_m'][i] for i in f] for m in meshes for f in m['triangles']]


def shirt(body, bones):
    out = L.shirt(body, bones)
    out['name'] = 'trade_shirt'; out['material'] = 'garment_upper__shirt_check_blue_1812'
    out['receipt']['garment'] = 'printed cotton trade shirt above the waist (the 1835 labourer\'s cut)'
    return out


def _hanging(body, bones, t, name, material, columns, closed, extra_fold=None):
    """A cloth hanging from y=top to y=hem round the body's own sections (a convex support
    polygon `ease` clear of each slab, never narrowing below the widest), in angular
    `columns` (radians from the front, towards +x), shared between the pelvis and each
    leg below the waist (leg_follow). `t` carries top_y, hem_y (or a function of the
    angle), ease, rows, fold and folds."""
    hem = t['hem_y'] if callable(t['hem_y']) else (lambda a, h=t['hem_y']: h)
    lo = min(hem(a) for a in columns)
    rows = t['rows']
    levels = [t['top_y']+(lo-t['top_y'])*i/(rows-1) for i in range(rows)]
    tris = [tri for tri in _tris(body['meshes'][0]) if min(p[1] for p in tri) <= t['top_y']+.02 and max(p[1] for p in tri) >= lo-.02]
    N = 144
    dirs = [(math.sin(2*math.pi*k/N), math.cos(2*math.pi*k/N)) for k in range(N)]
    sup = E.supports(tris, levels, dirs, t['ease'], hang=True)
    for i in range(rows):  # a little smoothing round the ring: cloth spans the hollows
        s = sup[i]
        sup[i] = [max(s[k], (s[k-1]+2*s[k]+s[(k+1) % N])/4) for k in range(N)]
    def support(i, a):
        k = (a % (2*math.pi))/(2*math.pi)*N; k0 = int(k) % N; f = k-int(k)
        return sup[i][k0]*(1-f)+sup[i][(k0+1) % N]*f
    follow = leg_follow(bones, t['top_y']-.03)
    out = empty(name, material)
    pts = []
    for i in range(rows):
        f = i/(rows-1)
        row = []
        for a in columns:
            # Each column falls to its own hem: the rows are spaced between top and that hem.
            y = t['top_y']+(hem(a)-t['top_y'])*f
            ii = min(rows-1, max(0, round((t['top_y']-y)/(t['top_y']-lo)*(rows-1))))
            r = support(ii, a)
            fold = t.get('fold', 0.)*f**1.3*(1-math.cos(t.get('folds', 0)*a))*.5
            if extra_fold:
                fold += extra_fold(a, f)
            r += fold
            row.append((math.sin(a)*r, y, math.cos(a)*r))
        pts.append(row)
    E.grid(out, pts, closed, lambda p: G._skin4(follow(p), 1.))
    # Standing clearance: every body point under the cloth is inside it.
    worst = math.inf
    for i in range(rows-1):
        for p in _slab_points(tris, levels[i+1], levels[i]):
            a = math.atan2(p[0], p[2])
            rr = support(i+1, a)
            worst = min(worst, rr-math.hypot(p[0], p[2]))
    need(worst > .004, f'{name} meets the standing body ({worst:.4f} m)')
    return out, worst


def shirt_skirt(body, bones):
    """The shirt below the waist, worn loose over the breechcloth: a closed hanging tube
    from under the belt to mid-thigh, a little fuller in soft folds towards the hem."""
    t = TAILORING['shirt_skirt']
    cols = [2*math.pi*k/t['segments'] for k in range(t['segments'])]
    out, worst = _hanging(body, bones, t, 'trade_shirt_skirt', 'garment_upper__shirt_check_blue_1812', cols, True)
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='trade shirt worn loose to mid-thigh', top_y_m=t['top_y'], hem_y_m=t['hem_y'],
                          ease_m=t['ease'], minimum_standing_body_clearance_m=worst,
                          skinning='pelvis at the top, shared with each thigh below (leg_follow)')
    return out


def breechcloth(body, bones):
    """Blue broadcloth flaps before and behind, from under the shirt to above the knee."""
    t = TAILORING['breechcloth']
    h = math.radians(t['half_width_deg'])
    parts = []
    for label, centre, hem in (('front', 0., t['hem_front_y']), ('back', math.pi, t['hem_back_y'])):
        cols = [centre-h+2*h*j/(t['cols']-1) for j in range(t['cols'])]
        tt = dict(t, hem_y=hem, fold=.003, folds=5)
        mesh, worst = _hanging(body, bones, tt, f'breechcloth_{label}', 'garment_lower__breechcloth_broadcloth_blue_1812', cols, False)
        parts.append((mesh, worst))
    out = empty('breechcloth', 'garment_lower__breechcloth_broadcloth_blue_1812')
    for m, _ in parts:
        base = len(out['positions_m'])
        for k in ('positions_m', 'uvs', 'weights', 'corner_uvs'):
            out[k] += m[k]
        out['triangles'] += [[i+base for i in f] for f in m['triangles']]
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='blue broadcloth breechcloth, flaps before and behind', top_y_m=t['top_y'],
                          hem_m=[t['hem_front_y'], t['hem_back_y']], half_width_deg=t['half_width_deg'],
                          minimum_standing_body_clearance_m=min(w for _, w in parts))
    return out


def leggings(body, bones, height):
    """Deer-skin leggings: the shared trouser shell to the instep, cut off above the crotch
    so each leg is its own (the breechcloth and the shirt cover the top), and a narrow
    flap standing out along each outer seam."""
    t = TAILORING['leggings']
    recipe = dict(waist_height_fraction=t['waist_height_fraction'], shirt_hem_fraction=.565,
                  workwear_tailoring_v5=dict(waistcoat_closed_front_torso_fraction=.4,
                                             trouser_cuff_radius_ratio=t['cuff_radius_ratio'],
                                             trouser_added_section_ease_m=t['added_section_ease'],
                                             trouser_thigh_transition_fraction=t['thigh_transition_fraction']))
    shell = garment_shell(body['meshes'][0], 'trousers', t['ease'], recipe, bones, height)
    shell = G._lengthen_hems(shell, bones, t)
    for k in ('source_basis', 'source_triangle_indices'):
        shell.pop(k, None)
    legs = S._split(shell, lambda c: c[1] < t['top_y'], 'stroud_leggings', 'garment_lower__leggings_stroud_scarlet_1812')
    legs = finish_edges(legs, .0015)
    # The flaps: along each leg's outermost line, a strip standing out and a little back,
    # its outer edge the stroud's undyed selvage.
    P = legs['positions_m']; W = legs['weights']
    flap = empty('legging_flaps', 'garment_lower__leggings_stroud_scarlet_1812')
    selvage = empty('legging_selvage', 'garment_lower__leggings_selvage_white_1812')
    back = math.radians(t['flap_back_deg'])
    for side in (1, -1):
        roots = []
        for i in range(t['flap_rows']):
            y = t['flap_top_y']+(t['flap_bottom_y']-t['flap_top_y'])*i/(t['flap_rows']-1)
            sl = [(p, w) for p, w in zip(P, W) if abs(p[1]-y) < .02 and p[0]*side > 0]
            need(bool(sl), 'no legging section for the flap')
            p, w = max(sl, key=lambda q: q[0][0]*side)
            roots.append([p[0]-side*.002, y, p[2]-.004])
        # The outermost legging vertex jumps from row to row; the seam runs smooth.
        for _ in range(3):
            roots = [roots[0]]+[[(a[0]+2*b[0]+c[0])/4, b[1], (a[2]+2*b[2]+c[2])/4]
                                for a, b, c in zip(roots, roots[1:], roots[2:])]+[roots[-1]]
        rows = []
        for root in roots:
            y = root[1]
            at = lambda d, root=root, y=y: (root[0]+side*d*math.cos(back), y, root[2]-d*math.sin(back))
            rows.append([tuple(root), at(t['flap']-t['selvage']), at(t['flap'])])
        own = [(p, w) for p, w in zip(P, W) if p[0]*side > 0]
        weigh = lambda q, own=own: G._skin4(dict(min(own, key=lambda r: math.dist(r[0], q))[1]), 1.)
        E.grid(flap, [r[:2] for r in rows], False, weigh)
        E.grid(selvage, [r[1:] for r in rows], False, weigh)
    flap = finish_edges(flap, .0016); selvage = finish_edges(selvage, .0016)
    flap['receipt'] = dict(garment='legging flaps along the outer seams', width_m=t['flap'], back_deg=t['flap_back_deg'])
    selvage['receipt'] = dict(garment='the undyed selvage at the flaps\' edge', width_m=t['selvage'])
    legs['receipt'] = dict(garment='scarlet stroud leggings, each leg its own, to the instep', top_y_m=t['top_y'],
                           ease_m=t['ease'], hem_y_m=[t['hem_front_y'], t['hem_back_y']])
    return legs, flap, selvage


def garters(body, bones, legs):
    """A woven garter round each leg just below the knee, over the legging."""
    t = TAILORING['garters']
    knee = bones['calf_l']['head_m'][1]
    y0 = knee-t['centre_below_knee']-t['height']/2; y1 = y0+t['height']
    out = empty('garters', 'accessory__garters_woven_dark_1812')
    for side in ('l', 'r'):
        sign = 1 if side == 'l' else -1
        tris = [tri for tri in _tris(legs) if sum(p[0] for p in tri)*sign > 0]
        cx = bones[f'calf_{side}']['head_m'][0]; cz = bones[f'calf_{side}']['head_m'][2]
        levels = [y0+(y1-y0)*i/(t['rows']-1) for i in range(t['rows'])]
        dirs = E.directions(t['segments'])
        sup = E.supports(tris, levels, dirs, t['ease'], centre=(cx, cz))
        top = [max(s[k] for s in sup) for k in range(t['segments'])]
        rows = []
        for i, y in enumerate(levels):
            g = t['roll']*math.sin(math.pi*i/(t['rows']-1))
            rows.append([(x+(x-cx)*g/.05, y, z+(z-cz)*g/.05) for x, z in (E.ring_point(top, dirs, k, (cx, cz)) for k in range(t['segments']))])
        E.grid(out, rows, True, lambda p, s=side: {f'calf_{s}': 1.})
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='woven garters below the knee', y_m=[y0, y1], skinning='calf, rigid')
    return out


def blanket(body, bones):
    """A white wool blanket wrapped round the waist to the knee, open at the front, its
    stripes near the ends falling either side of the opening; split into the white and
    the stripes by column, so the stripes are cloth of their own colour."""
    t = TAILORING['blanket']
    a_top = math.radians(t['open_top_deg']); a_hem = math.radians(t['open_hem_deg'])
    n = t['segments']
    # Columns in a fraction u of the blanket's width from its left edge (at +x of the
    # opening) round the back to its right edge; the stripes are placed by arc length.
    approx_r = .19
    span = approx_r*(2*math.pi-a_top-a_hem)
    s0 = t['stripe_from_edge']/span; s1 = (t['stripe_from_edge']+t['stripe_width'])/span
    us = sorted(set([j/n for j in range(n+1)]+[s0, s1, 1-s1, 1-s0]))
    us = [u for u in us if not any(abs(u-v) < .004 and u != v and v in (s0, s1, 1-s1, 1-s0) for v in (s0, s1, 1-s1, 1-s0))]
    rows = t['rows']
    tt = dict(t)
    # The opening widens from the top to the hem; a column's angle depends on its row,
    # so the cloth is built row by row here rather than through _hanging's fixed columns.
    levels = [t['top_y']+(t['hem_y']-t['top_y'])*i/(rows-1) for i in range(rows)]
    tris = [tri for tri in _tris(body['meshes'][0]) if min(p[1] for p in tri) <= t['top_y']+.02 and max(p[1] for p in tri) >= t['hem_y']-.02]
    N = 144
    dirs = [(math.sin(2*math.pi*k/N), math.cos(2*math.pi*k/N)) for k in range(N)]
    # Gathered close under the belt, falling free and fuller towards the hem.
    ease = [t['ease_top']+(t['ease']-t['ease_top'])*(i/(rows-1))**.6 for i in range(rows)]
    sup = E.supports(tris, levels, dirs, 0., hang=True)
    for i in range(rows):
        s = sup[i]
        sup[i] = [max(s[k], (s[k-1]+2*s[k]+s[(k+1) % N])/4)+ease[i] for k in range(N)]
    for i in range(1, rows):  # and never narrower than the row above (hang)
        sup[i] = [max(a, b) for a, b in zip(sup[i], sup[i-1])]
    def support(i, a):
        k = (a % (2*math.pi))/(2*math.pi)*N; k0 = int(k) % N; f = k-int(k)
        return sup[i][k0]*(1-f)+sup[i][(k0+1) % N]*f
    follow = leg_follow(bones, t['top_y']-.03)
    white = empty('blanket_wrap', 'garment_outer__blanket_wool_white_1812')
    stripes = empty('blanket_stripes', 'garment_outer__blanket_stripe_dark_1812')
    grid_pts = []
    for i, y in enumerate(levels):
        f = i/(rows-1)
        edge = a_top+(a_hem-a_top)*f**.9
        row = []
        for u in us:
            a = edge+(2*math.pi-2*edge)*u
            # Folds deepen towards the hem, uneven from fold to fold as wool hangs.
            ph = a-edge
            r = support(i, a)+t['fold']*f**1.2*(1-math.cos(t['folds']*ph))*.5*(.75+.25*math.sin(2.3*ph+.7))
            # The two ends of the blanket lie a little proud of the wrap (folded hems).
            r += .004*max(0., 1-min(u, 1-u)/.03)
            # The blanket's corners at the opening hang a little below the rest of the hem.
            yy = y-t['corner_droop']*f**2*max(0., 1-min(u, 1-u)/.12)
            row.append((math.sin(a)*r, yy, math.cos(a)*r))
        grid_pts.append(row)
    stripe_cols = {j for j in range(len(us)-1) if (s0-1e-9 <= us[j] < s1-1e-9) or (1-s1-1e-9 <= us[j] < 1-s0-1e-9)}
    def emit(out, cols):
        ids = {}
        for i in range(rows):
            for j in range(len(us)):
                if j in cols or j-1 in cols:
                    p = grid_pts[i][j]
                    ids[i, j] = len(out['positions_m'])
                    out['positions_m'].append(list(p)); out['uvs'].append([us[j], i/(rows-1)])
                    out['weights'].append(G._skin4(follow(p), 1.))
        for i in range(rows-1):
            for j in cols:
                a, b, c, d = ids[i, j], ids[i, j+1], ids[i+1, j], ids[i+1, j+1]
                for fc in ([a, b, d], [a, d, c]):
                    out['triangles'].append(fc); out['corner_uvs'].append([out['uvs'][v] for v in fc])
    emit(white, set(range(len(us)-1))-stripe_cols)
    emit(stripes, stripe_cols)
    worst = math.inf; worst_legs = math.inf
    for i in range(rows-1):
        for p in _slab_points(tris, levels[i+1], levels[i]):
            c = support(i+1, math.atan2(p[0], p[2]))-math.hypot(p[0], p[2])
            worst = min(worst, c)
            if levels[i] < .86:  # over the thighs: room for the stride
                worst_legs = min(worst_legs, c)
    need(worst > .006, f'blanket meets the standing body ({worst:.4f} m)')
    need(worst_legs > .02, f'blanket leaves the thighs no room ({worst_legs:.4f} m)')
    white = finish_edges(white, .002); stripes = finish_edges(stripes, .002)
    white['receipt'] = dict(garment='white wool blanket wrapped round the waist, gathered under the belt, open in front', top_y_m=t['top_y'],
                            hem_y_m=t['hem_y'], opening_deg=[t['open_top_deg'], t['open_hem_deg']], ease_m=[t['ease_top'], t['ease']],
                            minimum_standing_body_clearance_m=worst, minimum_thigh_clearance_m=worst_legs, skinning='pelvis, shared with each thigh below (leg_follow)')
    stripes['receipt'] = dict(garment='the blanket\'s dark stripes near its ends', from_edge_m=t['stripe_from_edge'],
                              width_m=t['stripe_width'])
    return white, stripes


def belt(body, bones, blanket_meshes):
    t = TAILORING['belt']
    weights = E.nearest_weights(body, t['bottom_y'], t['top_y'])
    out, _, _ = E.band(_tris(*blanket_meshes), t['bottom_y'], t['top_y'], t['rows'], t['segments'], t['ease'], t['roll'],
                       'leather_belt', 'accessory__belt_leather_1812', weights)
    out['receipt'].update(garment='leather belt holding the blanket at the waist')
    return out


def arm_bands(bones, shirt_mesh):
    """A silver band round each upper arm, over the shirt sleeve: a short loft round the
    sleeve's own section about the arm's axis. Rigid on the upper arm."""
    t = TAILORING['arm_bands']
    out = empty('silver_arm_bands', 'accessory__silver_1812')
    P = shirt_mesh['positions_m']
    n = t['segments']
    for side in ('l', 'r'):
        sign = 1 if side == 'l' else -1
        a0 = bones[f'upperarm_{side}']['head_m']
        xc = a0[0]+sign*t['centre_from_shoulder']
        cy, cz = a0[1], a0[2]
        sec = [p for p in P if abs(p[0]-xc) <= t['width']/2+.01]
        need(len(sec) > 8, 'no sleeve section for the arm band')
        dirs = [(math.cos(2*math.pi*k/n), math.sin(2*math.pi*k/n)) for k in range(n)]
        radii = [max((p[1]-cy)*dy+(p[2]-cz)*dz for p in sec)+t['ease'] for dy, dz in dirs]
        radii = [(radii[k-1]+2*radii[k]+radii[(k+1) % n])/4+.001 for k in range(n)]
        rows = []
        for j, (dx, r_add) in enumerate(((-.5, -.001), (-.5, .0015), (.5, .0015), (.5, -.001))):
            x = xc+dx*t['width']
            rows.append([(x, cy+(r+r_add)*dy, cz+(r+r_add)*dz) for r, (dy, dz) in zip(radii, dirs)])
        base = len(out['positions_m'])
        E.grid(out, rows, True, lambda p, s=side: {f'upperarm_{s}': 1.})
        if sign < 0:  # mirrored: keep the faces turned outward
            for fi in range(len(out['triangles'])):
                f = out['triangles'][fi]
                if f[0] >= base:
                    out['triangles'][fi] = [f[0], f[2], f[1]]
                    out['corner_uvs'][fi] = [out['uvs'][v] for v in out['triangles'][fi]]
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='silver arm bands over the sleeves', width_m=t['width'],
                          centre_from_shoulder_m=t['centre_from_shoulder'], skinning='upper arm, rigid')
    return out


def brooches(shirt_mesh, bones):
    """Three small silver brooches down the shirt front below the throat's opening, skinned
    as the shirt beneath (the soldier's button discs)."""
    t = TAILORING['brooches']
    neck = bones['neck_01']['head_m'][1]
    out = empty('silver_brooches', 'accessory__silver_1812')
    n = t['sides']
    for i in range(t['count']):
        y = neck-t['first_below_neck']-t['step']*i
        z0, w = G._surface_sample(shirt_mesh, 0., y)
        c = len(out['positions_m'])
        out['positions_m'].append([0., y, z0+t['standoff']+.002]); out['uvs'].append([.5, .5]); out['weights'].append(w)
        for k in range(n):
            a = 2*math.pi*k/n
            x, yy = t['radius']*math.cos(a), y+t['radius']*math.sin(a)
            try:
                z, _ = G._surface_sample(shirt_mesh, x, yy)
            except ValueError:
                z = z0
            out['positions_m'].append([x, yy, z+t['standoff']]); out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)])
            out['weights'].append(w)
        for k in range(n):
            out['triangles'].append([c, c+1+k, c+1+(k+1) % n])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='silver brooches on the shirt front', count=t['count'], radius_m=t['radius'])
    return out


def construct(body):
    need(TAILORING['shirt'] == L.TAILORING['shirt'], 'the trade shirt is the 1835 labourer\'s cut above the waist')
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    top = shirt(body, bones)
    skirt = shirt_skirt(body, bones)
    flaps = breechcloth(body, bones)
    legs, flap, selvage = leggings(body, bones, height)
    white, stripes = blanket(body, bones)
    parts = [top, skirt, flaps, legs, flap, selvage, garters(body, bones, legs), white, stripes,
             belt(body, bones, [white, stripes]), arm_bands(bones, top), brooches(top, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_potawatomi_man_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Everyday dress of 14 August only: no paint, arms, feathers, medal or anything of the 15th',
                             'Cut, ease, lengths and colours are reconstructed; the nearest detailed description is of 1823 (Keating)',
                             'Flat colours: the shirt\'s check, the blanket\'s weave and any quill or ribbon work are not drawn',
                             'No cloth simulation: the blanket, shirt and breechcloth hang from the pelvis and follow each thigh',
                             'Hair is the shared short04 cap; the clubbed cut is grown per person by the hair layer',
                             'The shared closed foot loft stands for the moccasin; no seam, vamp or cuff',
                             'No ear-bobs (too small to read); arm bands rigid on the upper arms'])


def prepare_potawatomi_man_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for the 1812 Potawatomi man; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('potawatomi_man_components', {})
    E.check_inputs(root, recipe, variant, body, spec, 'tools/human_potawatomi_man_1812.py', RECIPE, ASSEMBLY,
                   TAILORING, BODY_SHA256)
    need(variant.get('review_required') is True and variant.get('touches_removal') is True
         and len(variant.get('review_reason', '')) > 80 and len(variant.get('touches_removal_reason', '')) > 80,
         'a Native role keeps review_required and touches_removal with its own prose')
    bundle = construct(body)
    bundle['liberty'] = LIBERTY
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']]
    E.check_bundle(root, recipe, spec, bundle, body)
    return bundle


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    data = construct(json.loads(raw))
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]},
                     indent=1, default=str))
