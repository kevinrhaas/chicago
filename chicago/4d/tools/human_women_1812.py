# SPDX-License-Identifier: GPL-3.0-or-later
"""The women of the 1812 town on the shared portable female rig (T-3464 dress).

Three ROLES, each an anonymous reconstructed figure that a person of the 1812 town wears
with her own face, height, build and colouring (human-looks.js); no asset is a person.

  lady_1812              an officer's or trader's wife about 1810-12 (Rebekah Heald, Margaret
                         Helm, Eleanor Kinzie wear it): a high-waisted day gown of a small
                         blue print, the bodice short to just under the bust, long close
                         sleeves, a narrow gathered skirt falling straight to the ankle with
                         its fullness behind; a white muslin kerchief (fichu) round the neck
                         and crossed into the waist in front; a white cotton day cap with a
                         frill round the face; flat black shoes. Wau-Bun puts a muslin gown,
                         bonnets and shawls at the fort in August 1812; Krimmel's women of
                         1811-13, the Met's 1810-20 linen day dress and cap, the Pixler mother.
  woman_working_1812     a soldier's wife or laundress, a settler's wife, the Healds' servant
                         Cicely (Mrs Corbin, Holt, Needs, Simmons, Burns, Lee): a short gown
                         (a loose jacket-bodice with elbow sleeves and a skirt to the hip)
                         over a petticoat to the ankle, a broad apron tied at the waist, a
                         kerchief at the neck, a plain linen cap; shoes.
  woman_country_1812     (a variant of woman_working_1812's recipe) a French or Metis woman of
                         the country (Archange Ouilmette, Mrs Bisson, Josette LaFramboise):
                         Wau-Bun's "short gown and petticoat, with a blue cotton handkerchief
                         wrapped around her head" (Chicago, 16 August 1812), the short gown a
                         red print, the petticoat dark stroud, moccasins.
  potawatomi_woman_1812  a Potawatomi woman of the camp in August 1812 (Helm counted 179
                         women and children on the 12th): a wrapped dark-blue broadcloth
                         (strouding) skirt to mid-calf, its undyed selvage at the hem, a
                         calico shirt worn over it,
                         cloth leggings, moccasins, a trade blanket round the shoulders, three
                         small silver brooches at the shirt's neck; bare-headed (the looks
                         layer draws her hair). The goods distributed on the 13th or 14th were
                         "blankets, broadcloths, calicoes, paints" (Wau-Bun; Heald); the presents
                         of those years strouding, calicoes and silver-works including brooches
                         (Wau-Bun ch. I). No paint (that is the 15th), nothing ceremonial.

Generated geometry is CC0-1.0. The bodices are the dress components of T-3423
(tools/human_dress_components.py); the skirts are lofts after the 1904 lady's (round convex
supports enclosing the body's own sections), the short gown's skirt after her basque, the
head covers after the 1904 cook's head cloth; the kerchief, blanket and leggings are shells
off the body's own surface. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with its T-3464 supplement. The source anatomy is never changed.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls the
prepare_* function a recipe names in `role_1812` and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty, bodice, blouse, leg_follow
from human_workwear_fit import _clip, _slab_points
from human_period_wardrobe import finish_edges
from human_lady_1904 import _section, _ray_radius
from human_maid_1904 import _two_sided
from human_cook_1904 import cut
import human_gentleman_1904 as G

BODY_SHA256 = '3060ee86957ff7c2d70c89e70fe95ff3bc2294a0d7f6a5716b5a2f3f8dd84c72'
LIBERTY = 'L-human-modular-dress-1789'
SCENE_DATE = '1812-08-14'

# Every dimension, in metres; each recipe repeats its role's for review and the builder
# refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = {
    'lady_1812': dict(
        bodice=dict(high_waist_above_spine03=.044, ease=.011, neck_below_neck01=.012, sleeve_head=.008),
        skirt=dict(hem_y=.062, ease=.016, flare_from_y=.62, hem_rx=.25, hem_rz_front=.215, hem_rz_back=.30,
                   back_fullness=.04, folds=18, fold_depth=.013, front_folds=.3, segments=72, rows=20),
        band=dict(below=.010, above=.012, lift=.0035),
        kerchief=dict(ease=.016, above_neck01=.004, front_point_above_waist=.012, front_slope=.75,
                      back_point_below_neck01=.20, back_slope=.85, half_width=.20, arm=.45, gap=.007, smooth=6, folds=7, fold_depth=.008, cross=.0035),
        cap=dict(front_above_eyes=.085, nape_below_hair=.006, side_drop=1.25, ease=.008, puff=.018,
                 gathers=18, gather_depth=.007, rows=12, sectors=48, frill=.016, frill_waves=13, frill_arc_deg=100.),
    ),
    'woman_working_1812': dict(
        bodice=dict(waist_below_spine02=.018, ease=.017, neck_below_neck01=.012, sleeve_past_elbow=.06, pouch=.008,
                    sleeve_fullness=.012),
        skirt=dict(hem_y=.085, ease=.016, flare_from_y=.66, hem_rx=.27, hem_rz_front=.23, hem_rz_back=.28,
                   back_fullness=.012, folds=16, fold_depth=.009, front_folds=.6, segments=72, rows=18),
        peplum=dict(length=.165, ease=.009, flare=.03, front_gap_deg=7., rows=7),
        apron=dict(half_angle_deg=78., hem_above_skirt_hem=.10, offset=.006, rows=16, columns=37),
        band=dict(below=.010, above=.014, lift=.004),
        kerchief=dict(ease=.02, above_neck01=.003, front_point_above_waist=.15, front_slope=.8,
                      back_point_below_neck01=.17, back_slope=.75, half_width=.19, arm=.4, gap=.007, smooth=8, folds=7, fold_depth=.007, cross=.003),
        cap=dict(front_above_eyes=.08, nape_below_hair=.006, side_drop=1.2, ease=.008, puff=.014,
                 gathers=16, gather_depth=.006, rows=12, sectors=48, frill=.01, frill_waves=11, frill_arc_deg=95.),
        handkerchief=dict(front_above_eyes=.05, nape_below_hair=.012, side_drop=1.3, ease=.007, puff=.006,
                          gathers=9, gather_depth=.003, rows=12, sectors=40, knot=.028),
    ),
    'potawatomi_woman_1812': dict(
        shirt=dict(waist_below_spine02=.018, ease=.016, neck_below_neck01=.0, pouch=.010, sleeve_fullness=.014),
        skirt=dict(hem_y=.33, ease=.017, flare_from_y=.5, hem_rx=.0, hem_rz_front=.0, hem_rz_back=.0,
                   back_fullness=.0, folds=7, fold_depth=.004, front_folds=.7, segments=72, rows=12,
                   wrap_deg=-35., wrap_step=.0045, wrap_overlap_deg=70.),
        peplum=dict(length=.15, ease=.008, flare=.022, front_gap_deg=1., rows=6),
        selvage=dict(height=.032, lift=.0016, rows=2),
        leggings=dict(bottom_y=.11, above_skirt_hem=.07, ease=.011),
        blanket=dict(ease=.034, hem_below_spine02=.09, top_below_neck01=.012, front_gap=.065, sleeve_to_x=.33,
                     smooth=40, smooth_floor=.012, gap=.006),
        brooches=dict(count=3, radius=.0085, first_below_neck01=.045, spacing=.034, standoff=.002, sides=10),
    ),
}

MATERIALS = {
    'lady_1812': {
        'garment_upper__gown_blue_print_1812': {'base_color_linear': [.060, .075, .115, 1], 'roughness': .88},
        'garment_lower__gown_blue_print_1812': {'base_color_linear': [.060, .075, .115, 1], 'roughness': .9},
        'accessory__muslin_kerchief_white_1812': {'base_color_linear': [.60, .59, .55, 1], 'roughness': .85},
        'headwear__cotton_cap_white_1812': {'base_color_linear': [.62, .61, .57, 1], 'roughness': .84},
        'footwear__flat_shoes_black_1812': {'base_color_linear': [.014, .013, .012, 1], 'roughness': .5},
    },
    'woman_working_1812': {
        'garment_upper__short_gown_madder_print_1812': {'base_color_linear': [.15, .075, .055, 1], 'roughness': .9},
        'garment_lower__petticoat_blue_homespun_1812': {'base_color_linear': [.065, .075, .095, 1], 'roughness': .92},
        'garment_outer__apron_natural_linen_1812': {'base_color_linear': [.40, .36, .29, 1], 'roughness': .9},
        'accessory__neck_kerchief_white_1812': {'base_color_linear': [.55, .53, .48, 1], 'roughness': .88},
        'headwear__linen_cap_white_1812': {'base_color_linear': [.58, .56, .51, 1], 'roughness': .86},
        'footwear__shoes_black_1812': {'base_color_linear': [.025, .018, .013, 1], 'roughness': .55},
        'garment_upper__short_gown_red_calico_1812': {'base_color_linear': [.20, .07, .055, 1], 'roughness': .9},
        'garment_lower__petticoat_dark_stroud_1812': {'base_color_linear': [.025, .030, .055, 1], 'roughness': .92},
        'headwear__blue_cotton_handkerchief_1812': {'base_color_linear': [.05, .08, .16, 1], 'roughness': .88},
        'footwear__moccasins_smoked_1812': {'base_color_linear': [.17, .11, .065, 1], 'roughness': .8},
    },
    'potawatomi_woman_1812': {
        'garment_upper__calico_shirt_1812': {'base_color_linear': [.30, .12, .10, 1], 'roughness': .88},
        'garment_lower__strouding_skirt_blue_1812': {'base_color_linear': [.022, .028, .060, 1], 'roughness': .92},
        'garment_lower__strouding_selvage_white_1812': {'base_color_linear': [.40, .38, .32, 1], 'roughness': .92},
        'garment_lower__cloth_leggings_red_1812': {'base_color_linear': [.17, .035, .03, 1], 'roughness': .92},
        'garment_outer__trade_blanket_white_1812': {'base_color_linear': [.52, .49, .42, 1], 'roughness': .95},
        'accessory__silver_brooches_1812': {'base_color_linear': [.62, .62, .60, 1], 'roughness': .3},
        'footwear__moccasins_smoked_1812': {'base_color_linear': [.17, .11, .065, 1], 'roughness': .8},
    },
}

# Each variant's own materials (the working recipe dresses two of them).
LOOKS = {
    'lady_1812': dict(upper='garment_upper__gown_blue_print_1812', lower='garment_lower__gown_blue_print_1812',
                      kerchief='accessory__muslin_kerchief_white_1812', head='headwear__cotton_cap_white_1812',
                      shoes='footwear__flat_shoes_black_1812', headwear='cap'),
    'woman_working_1812': dict(upper='garment_upper__short_gown_madder_print_1812', lower='garment_lower__petticoat_blue_homespun_1812',
                               apron='garment_outer__apron_natural_linen_1812', kerchief='accessory__neck_kerchief_white_1812',
                               head='headwear__linen_cap_white_1812', shoes='footwear__shoes_black_1812', headwear='cap'),
    'woman_country_1812': dict(upper='garment_upper__short_gown_red_calico_1812', lower='garment_lower__petticoat_dark_stroud_1812',
                               apron='garment_outer__apron_natural_linen_1812', kerchief='accessory__neck_kerchief_white_1812',
                               head='headwear__blue_cotton_handkerchief_1812', shoes='footwear__moccasins_smoked_1812',
                               headwear='handkerchief'),
    'potawatomi_woman_1812': dict(upper='garment_upper__calico_shirt_1812', lower='garment_lower__strouding_skirt_blue_1812',
                                  selvage='garment_lower__strouding_selvage_white_1812',
                                  leggings='garment_lower__cloth_leggings_red_1812', blanket='garment_outer__trade_blanket_white_1812',
                                  brooches='accessory__silver_brooches_1812', shoes='footwear__moccasins_smoked_1812'),
}
ROLE_OF = {'lady_1812': 'lady_1812', 'woman_working_1812': 'woman_working_1812', 'woman_country_1812': 'woman_working_1812',
           'potawatomi_woman_1812': 'potawatomi_woman_1812'}
RECIPES = {role: f'data/humans/recipes/{role}.json' for role in TAILORING}
ASSEMBLIES = {role: f'{role}_v1' for role in TAILORING}


def _bones(body):
    return {b['name']: b for b in body['skeleton']}


def _smoothstep(x):
    x = min(1., max(0., x))
    return x*x*(3-2*x)


class Surface:
    """The outermost point of a mesh along z, in front (side=1) or behind (side=-1), under
    (x, y): the gentleman's _surface_sample with its triangles binned, so a garment can be
    laid over another at thousands of points."""
    def __init__(self, mesh, cell=.02):
        self.P = mesh['positions_m']; self.W = mesh['weights']; self.cell = cell; self.bins = {}
        for f in mesh['triangles']:
            xs = [self.P[i][0] for i in f]; ys = [self.P[i][1] for i in f]
            for bx in range(math.floor(min(xs)/cell), math.floor(max(xs)/cell)+1):
                for by in range(math.floor(min(ys)/cell), math.floor(max(ys)/cell)+1):
                    self.bins.setdefault((bx, by), []).append(f)

    def z(self, x, y, side=1):
        best = None
        for face in self.bins.get((math.floor(x/self.cell), math.floor(y/self.cell)), ()):
            a, b, c = (self.P[i] for i in face)
            den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den) < 1e-14:
                continue
            u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
            v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
            bary = (u, v, 1-u-v)
            if min(bary) < -1e-9:
                continue
            z = math.fsum(w*p[2] for w, p in zip(bary, (a, b, c)))
            if best is None or side*z > side*best[0]:
                best = (z, face, bary)
        if best is None:
            return None
        weights = {}
        for w, i in zip(best[2], best[1]):
            for k, val in self.W[i].items():
                weights[k] = weights.get(k, 0.)+max(0., w)*val
        items = sorted(weights.items(), key=lambda p: (-p[1], p[0]))[:4]
        total = math.fsum(w for _, w in items)
        return best[0], {k: w/total for k, w in items}


def _follow(bones, waist, top):
    """Skirt skinning: the leg-following weights of T-3423 below the natural waist, and above
    it (a gown hung from under the bust) shared between the pelvis and the spine."""
    legs = leg_follow(bones, waist)
    def weights(p):
        if p[1] <= waist:
            return legs(p)
        s = _smoothstep((p[1]-waist)/max(.01, top-waist))
        return {'pelvis': 1-.6*s, 'spine_02': .6*s} if s > 1e-6 else {'pelvis': 1.}
    return weights


def loft_skirt(body, bones, top, waist, upper, t, name, material, extra=()):
    """A skirt from `top` to its hem: rings round convex supports enclosing the body's own
    sections (and the `extra` points, garments worn beneath it), the cloth hanging straight
    from the top ring to the widest one (no pinch at the natural waist under a gown hung from
    under the bust), no ring below the widest narrower than the one above, opening below
    `flare_from_y` toward an elliptical hem, standing out behind by `back_fullness`, with
    gathers, fewer in front (`front_folds`). A wrapped skirt (`wrap_deg`) steps out by
    `wrap_step` where its outer edge lies over the under layer. After the 1904 lady's skirt.
    Returns the mesh and the rings (levels, dirs, radii)."""
    segs, rows, ease, hem = t['segments'], t['rows'], t['ease'], t['hem_y']
    top_y = top+.006
    levels = [top_y+(hem-top_y)*i/(rows-1) for i in range(rows)]
    tris = [[m['positions_m'][i] for i in f] for m in body['meshes'] for f in m['triangles']
            if min(m['positions_m'][i][1] for i in f) <= top_y+.02 and max(m['positions_m'][i][1] for i in f) >= hem-.02]
    dirs = [(math.sin(2*math.pi*k/segs), math.cos(2*math.pi*k/segs)) for k in range(segs)]
    supports = []
    for i in range(rows):
        lo, hi = levels[min(rows-1, i+1)]-.004, levels[max(0, i-1)]+.004
        pts = _slab_points(tris, lo, hi)+[p for p in extra if lo <= p[1] <= hi]
        need(len(pts) >= 3, 'empty skirt band')
        supports.append([max(nx*p[0]+nz*p[2] for p in pts)+ease for nx, nz in dirs])
    widest = max(range(rows), key=lambda i: sum(supports[i]))
    for i in range(1, widest):
        f = i/widest
        supports[i] = [max(s, (1-f)*a+f*b) for s, a, b in zip(supports[i], supports[0], supports[widest])]
    for i in range(widest+1, rows):
        supports[i] = [max(a, .998*b) for a, b in zip(supports[i], supports[i-1])]
    for i in range(rows):
        s = supports[i]
        supports[i] = [max(s[k], (s[k-1]+2*s[k]+s[(k+1) % segs])/4) for k in range(segs)]
    start = t['flare_from_y']
    ring_r = []
    for i, y in enumerate(levels):
        q = i/(rows-1)
        row = []
        for k, (nx, nz) in enumerate(dirs):
            want = supports[i][k]
            if t['hem_rx'] > 0:
                f = _smoothstep((start-y)/(start-hem))
                rz = t['hem_rz_front'] if nz > 0 else t['hem_rz_back']
                ell = 1/math.sqrt((nx/t['hem_rx'])**2+(nz/rz)**2)
                want += (max(want, ell)-want)*f
            back = max(0., -nz)
            want += t['back_fullness']*back**1.3*_smoothstep((top_y-y)/.22)
            share = t['front_folds']+(1-t['front_folds'])*back
            want += t['fold_depth']*share*(.3+.7*q**.6)*.5*(1-math.cos(t['folds']*2*math.pi*k/segs))
            if t.get('wrap_deg') is not None:
                a = (math.degrees(math.atan2(nx, nz))-t['wrap_deg']) % 360.
                if a < t['wrap_overlap_deg']:
                    want += t['wrap_step']*(1-_smoothstep((a-.6*t['wrap_overlap_deg'])/(.4*t['wrap_overlap_deg'])))
            row.append(want)
        ring_r.append(row)
    sec = _section(upper, top_y+.008)
    if sec:
        for k, (nx, nz) in enumerate(dirs):
            r = _ray_radius(sec, nx, nz)
            if r:
                ring_r[0][k] = min(ring_r[0][k], r-.002)
    out = empty(name, material)
    follow = _follow(bones, waist, top_y)
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
    worst = math.inf
    step = 2*math.pi/segs
    for i in range(1, rows-1):
        pts = _slab_points(tris, levels[i+1], levels[i])+[p for p in extra if levels[i+1] <= p[1] <= levels[i]]
        for p in pts:
            th = math.atan2(p[0], p[2]) % (2*math.pi)
            k = int(th/step) % segs
            q = (p[1]-levels[i])/(levels[i+1]-levels[i])
            rr = min((1-q)*ring_r[i][j]+q*ring_r[i+1][j] for j in (k, (k+1) % segs))
            worst = min(worst, rr-math.hypot(p[0], p[2]))
    need(worst > .004, f'{name} meets the standing body ({worst:.4f} m)')
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment=name.replace('_', ' '), hem_y_m=hem, top_y_m=top_y, ease_m=ease,
                          minimum_standing_body_clearance_m=worst, widest_ring=widest,
                          skinning='pelvis at the waist, shared with the thigh and calf of each side below it (leg_follow, T-3423); pelvis and spine above the natural waist')
    return out, (levels, dirs, ring_r)


def _ring_radius(rings, y, a):
    """A loft's radius at height y and angle a, interpolated in both."""
    levels, dirs, R = rings
    segs = len(dirs)
    j = min(len(levels)-2, max(0, next((n for n in range(len(levels)-1) if levels[n+1] <= y), len(levels)-2)))
    q = min(1., max(0., (levels[j]-y)/(levels[j]-levels[j+1])))
    s = (a/(2*math.pi)) % 1*segs; k = int(s) % segs; f = s-int(s)
    r0 = R[j][k]*(1-f)+R[j][(k+1) % segs]*f
    r1 = R[j+1][k]*(1-f)+R[j+1][(k+1) % segs]*f
    return r0*(1-q)+r1*q


def selvage(bones, waist, skirt_rings, t, name, material):
    """The undyed selvage (list) of a strouding skirt worn at its hem: a narrow loft just
    outside the skirt's own rings from the hem up `height`, skinned as the skirt is (the same
    leg-following weights at the same points) so the two move together."""
    levels, dirs, _ = skirt_rings
    segs, rows = len(dirs), t['rows']
    hem = levels[-1]; top_y = waist+.006
    lv = [hem-.001+(t['height']+.001)*i/(rows-1) for i in range(rows)]
    follow = _follow(bones, waist, top_y)
    out = empty(name, material)
    for i, y in enumerate(lv):
        for k in range(segs):
            a = 2*math.pi*k/segs
            r = _ring_radius(skirt_rings, max(y, hem), a)+t['lift']
            p = [math.sin(a)*r, y, math.cos(a)*r]
            out['positions_m'].append(p); out['uvs'].append([k/segs, i/(rows-1)]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for k in range(segs):
            n = (k+1) % segs
            a = i*segs+k; b = i*segs+n; c = (i+1)*segs+n; d = (i+1)*segs+k
            for face in ([a, b, c], [a, c, d]):
                out['triangles'].append(face)
                out['corner_uvs'].append([[(k+(1 if v in (b, c) else 0))/segs, (v//segs)/(rows-1)] for v in face])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='strouding selvage at the hem', from_y_m=lv[0], to_y_m=lv[-1], lift_m=t['lift'])
    return out


def peplum(bones, waist, upper, skirt_rings, t, name, material):
    """The skirt of a short gown or shirt below its waist seam, to the hip: a loft just outside
    the skirt's own rings, opening a little toward its hem, skinned as the skirt is so the two
    move together; a little open at the front where its fronts meet. After the lady's basque."""
    levels, dirs, _ = skirt_rings
    segs, rows = len(dirs), t['rows']
    top_y = waist+.006; hem = waist-t['length']
    lv = [top_y+(hem-top_y)*i/(rows-1) for i in range(rows)]
    gap = math.radians(t['front_gap_deg'])
    angles = [gap+(2*math.pi-2*gap)*k/(segs-1) for k in range(segs)]
    sec = _section(upper, top_y+.008)
    out = empty(name, material)
    follow = _follow(bones, waist, top_y)
    for i, y in enumerate(lv):
        f = i/(rows-1)
        for k, a in enumerate(angles):
            nx, nz = math.sin(a), math.cos(a)
            r = _ring_radius(skirt_rings, y, a)+t['ease']+t['flare']*f**1.5
            if i == 0 and sec:
                jr = _ray_radius(sec, nx, nz)
                if jr:
                    r = min(r, jr-.0015)
            p = [nx*r, y, nz*r]
            out['positions_m'].append(p); out['uvs'].append([k/(segs-1), f]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for k in range(segs-1):
            a = i*segs+k; b = a+1; c = a+segs+1; d = a+segs
            for face in ([a, b, c], [a, c, d]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][j] for j in face])
    margin = min(math.hypot(p[0], p[2])-_ring_radius(skirt_rings, p[1], math.atan2(p[0], p[2]) % (2*math.pi))
                 for p in out['positions_m'][segs:])
    need(margin > .004, f'{name} meets the skirt ({margin:.4f} m)')
    out = finish_edges(out, .0016)
    out['receipt'] = dict(garment=name.replace('_', ' '), top_y_m=top_y, hem_y_m=hem, minimum_skirt_clearance_m=margin,
                          front_gap_deg=t['front_gap_deg'])
    return out, (lv, angles, t)


def apron(bones, waist, skirt_rings, pep, t, skirt_hem, material):
    """A broad apron tied at the waist: a panel round the front and sides, over the short
    gown's skirt and the petticoat, hanging straight from wherever it lies farthest out (it
    never steps back in under the short gown's hem), to a little above the petticoat's hem."""
    lv, angles, pt = pep
    top_y = waist+.004; hem = skirt_hem+t['hem_above_skirt_hem']
    rows, cols = t['rows'], t['columns']
    half = math.radians(t['half_angle_deg'])
    pep_top, pep_hem = lv[0], lv[-1]
    def pep_r(y, a):
        if not pep_hem <= y <= pep_top:
            return 0.
        f = (pep_top-y)/(pep_top-pep_hem)
        return _ring_radius(skirt_rings, y, a)+pt['ease']+pt['flare']*f**1.5
    out = empty('apron', material)
    follow = _follow(bones, waist, top_y)
    radius = [0.]*cols
    for i in range(rows):
        s = i/(rows-1); y = top_y+(hem-top_y)*s
        for c in range(cols):
            u = c/(cols-1); a = (-half+2*half*u) % (2*math.pi)
            r = max(_ring_radius(skirt_rings, y, a), pep_r(y, a))+t['offset']
            radius[c] = r = max(r, radius[c])
            p = [math.sin(a)*r, y, math.cos(a)*r]
            out['positions_m'].append(p); out['uvs'].append([u, s]); out['weights'].append(follow(p))
    for i in range(rows-1):
        for c in range(cols-1):
            a = i*cols+c; b = a+1; d = a+cols; e = d+1
            for face in ([a, b, e], [a, e, d]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][j] for j in face])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='broad apron', top_y_m=top_y, hem_y_m=hem, half_angle_deg=t['half_angle_deg'], offset_m=t['offset'])
    return out


def band(meshes, waist, t, name, material, weights):
    """A narrow band round the waist (an apron's string, a gown's waist band): one radius per
    angle for its whole height, the farthest of the garments beneath it there plus `lift`."""
    segs = 64
    lo, hi = waist-t['below'], waist+t['above']
    secs = [s for m in meshes for y in (lo, hi) for s in _section(m, y)]
    radius = []
    for k in range(segs):
        a = 2*math.pi*k/segs
        r = _ray_radius(secs, math.sin(a), math.cos(a))
        need(r is not None, f'no garment under the {name}')
        radius.append(r+t['lift'])
    radius = [max(radius[k], (radius[k-1]+radius[k]+radius[(k+1) % segs])/3) for k in range(segs)]
    out = empty(name, material)
    for j, y in enumerate((lo, hi)):
        for k in range(segs):
            a = 2*math.pi*k/segs
            out['positions_m'].append([radius[k]*math.sin(a), y, radius[k]*math.cos(a)])
            out['uvs'].append([k/segs, j]); out['weights'].append(dict(weights))
    for k in range(segs):
        q = (k+1) % segs
        out['triangles'] += [[k, q, segs+q], [k, segs+q, segs+k]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment=name.replace('_', ' '), from_y_m=lo, to_y_m=hi, lift_m=t['lift'])
    return out


def kerchief(body, bones, t, under, material, front_point_y):
    """A kerchief folded corner to corner and laid round the neck: a shell off the body's own
    surface from the foot of the neck down over the shoulders, its ends crossing to a point in
    front at `front_point_y`, its folded corner a point down the back; smoothed as cloth lies
    over the collar bones, and laid over the garment beneath it wherever that lies farther out."""
    neck = bones['neck_01']['head_m'][1]; cz = bones['spine_03']['head_m'][2]
    hi = neck+t['above_neck01']
    back_point = neck-t['back_point_below_neck01']
    fields = [lambda v: hi-v['p'][1], lambda v: t['arm']-G._arm_mass(v), lambda v: t['half_width']-abs(v['p'][0])]
    def pieces(poly):
        front = _clip(_clip(poly, lambda v: v['p'][2]-cz), lambda v: v['p'][1]-(front_point_y+t['front_slope']*abs(v['p'][0])))
        back = _clip(_clip(poly, lambda v: cz-v['p'][2]), lambda v: v['p'][1]-(back_point+t['back_slope']*abs(v['p'][0])))
        return [front, back]
    out = G._poly_shell(body, bones, 'neck_kerchief', material, fields, t['ease'], [(-1., hi)], neck, pieces,
                        smooth=(t['smooth'], t['ease']-.004))
    front, back = Surface(under), None
    moved = 0
    for i, p in enumerate(out['positions_m']):
        side = 1 if p[2] > cz else -1
        hit = front.z(p[0], p[1], side)
        if hit and side*(p[2]-hit[0]) < t['gap']:
            out['positions_m'][i] = [p[0], p[1], hit[0]+side*t['gap']]; moved += 1
    # Folds: the cloth gathers toward its two points, in front where the ends cross and behind
    # at the folded corner, so it is drawn in shallow ridges fanning out from each point.
    for i, p in enumerate(out['positions_m']):
        side = 1 if p[2] > cz else -1
        apex = front_point_y if side > 0 else back_point
        th = math.atan2(p[0], max(.02, p[1]-apex))
        fade = _smoothstep((p[1]-apex)/.05)*_smoothstep((hi-.012-p[1])/.04)
        bump = t['fold_depth']*.5*(1-math.cos(t['folds']*th))*fade
        if side > 0 and p[0] < .03*(p[1]-front_point_y)/(hi-front_point_y):
            # The left end crosses over the right: it lies one layer out, so its edge shows
            # from the throat down to the point.
            bump += t['cross']
        nrm = out['_normals'][i]
        out['positions_m'][i] = [p[a]+bump*nrm[a] for a in range(3)]
    out.pop('_normals', None)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='kerchief round the neck, crossed in front', folds=t['folds'], top_y_m=hi, front_point_y_m=front_point_y,
                          back_point_y_m=back_point, ease_m=t['ease'], laid_over_points=moved)
    return out


def head_cover(body, bones, hair, t, name, material, lod=0):
    """A cloth cap or a handkerchief over the hair: the hair's (and scalp's) own outline at
    every direction from a centre inside the head plus `ease`, smoothed as cloth bridges the
    strands, fuller toward the back of the crown by `puff`, its edge high over the brow
    (`front_above_eyes`), falling round the temples to under the hair at the nape. A cap has a
    fluted frill round the face (`frill`), a handkerchief its ends knotted at the nape (`knot`).
    After the 1904 cook's head cloth. Rigid on the head bone, a separate mesh."""
    Q = hair['positions_m']
    eye_y = bones['eye_l']['head_m'][1]
    head = bones['head']['head_m']
    c = [0., eye_y+.035, head[2]-.012]
    nape = min(p[1] for p in Q if p[2] < c[2]-.04)
    front_y = eye_y+t['front_above_eyes']
    back_y = nape-t['nape_below_hair']
    scalp = [p for p in body['meshes'][0]['positions_m'] if p[1] > eye_y+.02]
    pts = Q+scalp
    n = t['sectors'] if lod == 0 else max(16, t['sectors']*2//3)
    rows = t['rows']
    def edge_y(az):
        f = .5*(1-math.cos(az))
        return front_y+(back_y-front_y)*f**t['side_drop']
    def direction(az, el):
        return [math.cos(el)*math.sin(az), math.sin(el), math.cos(el)*math.cos(az)]
    rel = [[p[i]-c[i] for i in range(3)] for p in pts]
    lens = [math.sqrt(sum(x*x for x in v)) or 1. for v in rel]
    grid = []
    for r in range(rows):
        row = []
        for k in range(n):
            az = 2*math.pi*k/n
            ye = edge_y(az)
            near = [(p[0]*math.sin(az)+(p[2]-c[2])*math.cos(az)) for p in pts if abs(p[1]-ye) < .02]
            horiz = max(.06, max(near) if near else .06)
            el0 = math.atan2(ye-c[1], horiz)
            el = el0+(math.pi/2-el0)*(r/(rows-1))
            if r == rows-1:
                el = math.pi/2-1e-3
            row.append(direction(az, el))
        grid.append(row)
    radius = []
    for row in grid:
        rr = []
        for d in row:
            best = 0.
            for v, l in zip(rel, lens):
                dot = v[0]*d[0]+v[1]*d[1]+v[2]*d[2]
                if dot > .965*l and dot > best:
                    best = dot
            rr.append(best)
        radius.append(rr)
    for _ in range(6):
        nxt = []
        for r in range(rows):
            row = []
            for k in range(n):
                nb = [radius[r][(k-1) % n], radius[r][(k+1) % n]]+([radius[r-1][k]] if r else [])+([radius[r+1][k]] if r < rows-1 else [])
                row.append(max(radius[r][k], sum(nb)/len(nb)))
            nxt.append(row)
        radius = nxt
    out = empty(name, material)
    for r in range(rows):
        for k in range(n):
            d = grid[r][k]
            # Fuller toward the back of the crown (a soft cap gathered into its band).
            back = max(0., -d[2])*max(0., d[1]+.3)
            az = 2*math.pi*k/n
            # Soft gathers running up from the band, fading out over the crown.
            g = t['gather_depth']*.5*(1-math.cos(t['gathers']*az))*_smoothstep((r-1)/2)*(1-_smoothstep((r-rows*.6)/(rows*.3)))
            rr = radius[r][k]+t['ease']+t['puff']*back*_smoothstep(r/3)+g
            out['positions_m'].append([c[i]+rr*d[i] for i in range(3)])
            out['uvs'].append([k/n, r/(rows-1)]); out['weights'].append({'head': 1.})
    for r in range(rows-1):
        for k in range(n):
            q = (k+1) % n
            a, b, cc, d = r*n+k, r*n+q, (r+1)*n+q, (r+1)*n+k
            out['triangles'] += [[a, b, cc], [a, cc, d]]
    apex = len(out['positions_m'])
    out['positions_m'].append([c[0], c[1]+max(radius[-1])+t['ease']+t['puff']*.3, c[2]]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([(rows-1)*n+k, (rows-1)*n+(k+1) % n, apex])
    P = out['positions_m']
    def outward(f):
        a0, b0, c0 = (P[j] for j in f)
        u = [b0[i]-a0[i] for i in range(3)]; v = [c0[i]-a0[i] for i in range(3)]
        nrm = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        cen = [(a0[i]+b0[i]+c0[i])/3-c[i] for i in range(3)]
        return sum(nrm[i]*cen[i] for i in range(3)) >= 0
    out['triangles'] = [f if outward(f) else [f[0], f[2], f[1]] for f in out['triangles']]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    receipt = dict(garment=name.replace('_', ' '), centre_m=c, front_edge_y_m=front_y, back_edge_y_m=back_y, ease_m=t['ease'],
                   puff_m=t['puff'], head_bone='head', separate_mesh=True)
    if t.get('frill'):
        # The frill: a fluted strip out and down from the edge round the face, double-sided.
        arc = math.radians(t['frill_arc_deg'])
        ks = [k for k in range(n) if abs(((2*math.pi*k/n)+math.pi) % (2*math.pi)-math.pi) <= arc]
        ks.sort(key=lambda k: ((2*math.pi*k/n)+math.pi) % (2*math.pi))
        fr = empty(name+'_frill', material)
        for j, k in enumerate(ks):
            az = 2*math.pi*k/n
            e = P[k]
            d = [e[i]-c[i] for i in range(3)]; l = math.sqrt(sum(x*x for x in d)); d = [x/l for x in d]
            s = abs(((az+math.pi) % (2*math.pi))-math.pi)/arc
            width = t['frill']*(1-.55*_smoothstep((s-.6)/.4))
            flute = .5*(1+math.cos(t['frill_waves']*az*2))
            # It stands out round the face, out from the head, forward and a little down.
            fwd = [.6*d[0], .6*d[1]-.4, .6*d[2]+.5]; fl = math.sqrt(sum(x*x for x in fwd)); fwd = [x/fl for x in fwd]
            o = [e[i]+d[i]*.002 for i in range(3)]
            reach = width*(.8+.2*flute)
            w = [e[i]+fwd[i]*reach for i in range(3)]
            for p, v in ((o, 0.), (w, 1.)):
                fr['positions_m'].append(p); fr['uvs'].append([j/(len(ks)-1), v]); fr['weights'].append({'head': 1.})
        for j in range(len(ks)-1):
            a, b, cc, d = 2*j, 2*j+2, 2*j+3, 2*j+1
            fr['triangles'] += [[a, cc, b], [a, d, cc]]
        fr['corner_uvs'] = [[fr['uvs'][i] for i in f] for f in fr['triangles']]
        fr = _two_sided(fr)
        base = len(out['positions_m'])
        for key in ('positions_m', 'uvs', 'weights'):
            out[key] += fr[key]
        out['triangles'] += [[i+base for i in f] for f in fr['triangles']]
        out['corner_uvs'] += fr['corner_uvs']
        receipt.update(frill_m=t['frill'], frill_arc_deg=t['frill_arc_deg'], frill_double_sided=True)
    if t.get('knot'):
        # Its ends knotted at the nape, behind, just above the edge.
        kn = t['knot']
        back_dir = direction(math.pi, math.atan2(back_y+.03-c[1], .1))
        kr = max(v[0]*back_dir[0]+v[1]*back_dir[1]+v[2]*back_dir[2] for v in rel)+t['ease']+.006
        centre = [c[i]+kr*back_dir[i] for i in range(3)]
        kb = len(out['positions_m'])
        for i in range(10):
            a = 2*math.pi*i/10
            out['positions_m'].append([centre[0]+kn*.7*math.cos(a), centre[1]+kn*.45*math.sin(a), centre[2]])
            out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
        kc = len(out['positions_m'])
        out['positions_m'].append([centre[0], centre[1], centre[2]-.012]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
        for i in range(10):
            f = [kb+i, kb+(i+1) % 10, kc]
            out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][j] for j in f])
        receipt.update(knot_m=kn, knot='at the nape')
    out['receipt'] = receipt
    return out


def leggings(body, bones, t, skirt_hem, material):
    """Cloth leggings from the moccasin tops to under the skirt: a shell off the lower legs'
    own surface, skinned as the legs are."""
    lo, hi = t['bottom_y'], skirt_hem+t['above_skirt_hem']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1]]
    out = G._poly_shell(body, bones, 'cloth_leggings', material, fields, t['ease'], [], bones['neck_01']['head_m'][1])
    out.pop('_normals', None)
    out = finish_edges(out, .0016)
    out['receipt'] = dict(garment='cloth leggings', from_y_m=lo, to_y_m=hi, ease_m=t['ease'])
    return out


def lay_over(mesh, unders, gap, reach=.08, cell=.03, cycles=4, relax=12):
    """Move each point of `mesh` out along its own normal until it lies `gap` outside the
    triangles of the garments `unders` it would meet within `reach` (a ray each way from the
    point), so a shell cut off the body sits over fuller garments beneath it; then relax the
    shell (Laplacian, `relax` steps; its cut edges along themselves) so heavy cloth spans
    the step it was pushed over instead of moulding to it, and push again, `cycles` times. Returns the points the
    last push still had to move."""
    P, N = mesh['positions_m'], mesh['_normals']
    bins = {}
    for f in (f for u in unders for f in ([[u['positions_m'][i] for i in t] for t in u['triangles']])):
        a, b, c = f
        lo = [int(math.floor(min(a[k], b[k], c[k])/cell)) for k in range(3)]
        hi = [int(math.floor(max(a[k], b[k], c[k])/cell)) for k in range(3)]
        for x in range(lo[0], hi[0]+1):
            for y in range(lo[1], hi[1]+1):
                for z in range(lo[2], hi[2]+1):
                    bins.setdefault((x, y, z), []).append((a, b, c))
    def sub(u, v): return [u[0]-v[0], u[1]-v[1], u[2]-v[2]]
    def dot(u, v): return u[0]*v[0]+u[1]*v[1]+u[2]*v[2]
    def cross(u, v): return [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    def push():
        moved = 0
        for i, p in enumerate(P):
            n = N[i]; o = [p[k]-reach*n[k] for k in range(3)]
            seen, cand = set(), []
            for j in range(9):
                q = [o[k]+n[k]*2*reach*j/8 for k in range(3)]
                key = tuple(int(math.floor(q[k]/cell)) for k in range(3))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            kk = (key[0]+dx, key[1]+dy, key[2]+dz)
                            if kk not in seen:
                                seen.add(kk); cand += bins.get(kk, [])
            best = None
            for a, b, c in cand:
                e1, e2 = sub(b, a), sub(c, a)
                h = cross(n, e2); det = dot(e1, h)
                if abs(det) < 1e-12:
                    continue
                s = sub(o, a); u = dot(s, h)/det
                if u < 0 or u > 1:
                    continue
                qv = cross(s, e1); v = dot(n, qv)/det
                if v < 0 or u+v > 1:
                    continue
                tt = dot(e2, qv)/det
                if 0 <= tt <= 2*reach and (best is None or tt > best):
                    best = tt
            if best is not None and best-reach+gap > 0:
                d = best-reach+gap
                P[i] = [p[k]+d*n[k] for k in range(3)]; moved += 1
        return moved
    nbr = [set() for _ in P]
    edges = {}
    for f in mesh['triangles']:
        for a, b in zip(f, f[1:]+f[:1]):
            nbr[a].add(b); nbr[b].add(a)
            key = (min(a, b), max(a, b)); edges[key] = edges.get(key, 0)+1
    boundary = {i for (a, b), c in edges.items() if c == 1 for i in (a, b)}
    along = {i: set() for i in boundary}
    for (a, b), c in edges.items():
        if c == 1:
            along[a].add(b); along[b].add(a)
    moved = push()
    for _ in range(cycles):
        for _ in range(relax):
            cur = [list(p) for p in P]
            for i in range(len(P)):
                # An edge relaxes along itself only, so the cut line smooths without shrinking.
                ring = (along[i] if len(along[i]) == 2 else ()) if i in boundary else nbr[i]
                if not ring:
                    continue
                avg = [math.fsum(cur[j][k] for j in ring)/len(ring) for k in range(3)]
                P[i] = [cur[i][k]+.5*(avg[k]-cur[i][k]) for k in range(3)]
        moved = push()
    return moved

def blanket(body, bones, t, material, under):
    """A trade blanket round the shoulders: a thick shell off the body's own surface from the
    foot of the neck over the shoulders and upper arms and down the back and sides to the
    hip, open down the front where its edges are held, smoothed as heavy wool bridges the
    hollows; skinned as the body beneath, so it comes down with the arms."""
    neck = bones['neck_01']['head_m'][1]; spine = bones['spine_02']['head_m'][1]; cz = bones['spine_03']['head_m'][2]
    lo, hi = spine-t['hem_below_spine02'], neck-t['top_below_neck01']
    reach = t['sleeve_to_x']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: reach-abs(v['p'][0])]
    def pieces(poly):
        back = _clip(poly, lambda v: cz-v['p'][2])
        front = _clip(poly, lambda v: v['p'][2]-cz)
        left = _clip(front, lambda v: v['p'][0]-t['front_gap'])
        right = _clip(front, lambda v: -v['p'][0]-t['front_gap'])
        return [back, left, right]
    out = G._poly_shell(body, bones, 'trade_blanket', material, fields, t['ease'], [(lo, 9.)], neck, pieces,
                        smooth=(t['smooth'], t['smooth_floor']))
    loose = G._armpit_ease(out, body, bones, .012)
    laid = lay_over(out, under, t['gap'])
    out.pop('_normals', None)
    out = finish_edges(out, .002)
    out['receipt'] = dict(garment='trade blanket round the shoulders', hem_y_m=lo, top_y_m=hi, front_gap_m=t['front_gap'],
                          to_x_m=reach, ease_m=t['ease'], armpit_points_eased=loose, laid_over_points=laid)
    return out


def brooches(shirt, bones, t, material):
    """Small round silver brooches down the shirt's opening, each a shallow disc on the shirt's
    own surface, skinned as the shirt beneath."""
    neck = bones['neck_01']['head_m'][1]
    surf = Surface(shirt)
    out = empty('silver_brooches', material)
    n = t['sides']
    for j in range(t['count']):
        y = neck-t['first_below_neck01']-j*t['spacing']
        hit = surf.z(0., y)
        need(hit is not None, 'no shirt under a brooch')
        z0, w = hit
        c = len(out['positions_m'])
        out['positions_m'].append([0., y, z0+t['standoff']+.0018]); out['uvs'].append([.5, .5]); out['weights'].append(w)
        for k in range(n):
            a = 2*math.pi*k/n
            x, yy = t['radius']*math.cos(a), y+t['radius']*math.sin(a)
            h = surf.z(x, yy)
            out['positions_m'].append([x, yy, (h[0] if h else z0)+t['standoff']]); out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)])
            out['weights'].append(w)
        for k in range(n):
            out['triangles'].append([c, c+1+k, c+1+(k+1) % n])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='silver brooches', count=t['count'], radius_m=t['radius'])
    return out


def _bodice(body, bones, waist, ease, neck_below, name, material, sleeve_end=None, pouch=0., sleeve=0., high=None):
    """The T-3423 bodice and its T-3434 fullness, its sleeves cut back to `sleeve_end`; a gown's
    bodice is built to the natural waist (where the cloth's bridging of the bust is measured)
    and then cut short at `high`, just under the bust."""
    full = bodice(body, bones, waist, ease=ease, collar=-neck_below)
    full = blouse(full, bones, waist, pouch=pouch, sleeve=sleeve)
    out = full
    if sleeve_end or high:
        out = cut(full, lambda p: min(sleeve_end-abs(p[0]) if sleeve_end else 1., p[1]-high if high else 1.), name)
        out = finish_edges(out, .0015)
    out['name'] = name; out['material'] = material
    return out


def construct(body, hair, variant_id):
    """The dress bundle of one variant (lady_1812, woman_working_1812, woman_country_1812 or
    potawatomi_woman_1812)."""
    role = ROLE_OF[variant_id]; T = TAILORING[role]; look = LOOKS[variant_id]
    before = digest(body)
    bones = _bones(body)
    spine2 = bones['spine_02']['head_m'][1]; spine3 = bones['spine_03']['head_m'][1]
    neck = bones['neck_01']['head_m'][1]
    extra = {}
    if role == 'lady_1812':
        b = T['bodice']
        high = spine3+b['high_waist_above_spine03']; waist = spine2-.018
        upper = _bodice(body, bones, waist, b['ease'], b['neck_below_neck01'], 'gown_bodice', look['upper'], sleeve=b['sleeve_head'],
                        high=high)
        skirt_mesh, _rings = loft_skirt(body, bones, high, waist, upper, T['skirt'], 'gown_skirt', look['lower'])
        waistband = band([upper, skirt_mesh], high, T['band'], 'gown_waist_band', look['upper'], {'spine_02': .6, 'pelvis': .4})
        kt = T['kerchief']
        neckerchief = kerchief(body, bones, kt, upper, look['kerchief'], high+kt['front_point_above_waist'])
        cap = head_cover(body, bones, hair, T['cap'], 'headwear_day_cap', look['head'])
        parts = [upper, skirt_mesh, waistband, neckerchief, cap]
    elif role == 'woman_working_1812':
        b = T['bodice']
        waist = spine2-b['waist_below_spine02']
        end = abs(bones['lowerarm_l']['head_m'][0])+b['sleeve_past_elbow']
        upper = _bodice(body, bones, waist, b['ease'], b['neck_below_neck01'], 'short_gown_body', look['upper'], end,
                        pouch=b['pouch'], sleeve=b['sleeve_fullness'])
        skirt_mesh, rings = loft_skirt(body, bones, waist, waist, upper, T['skirt'], 'petticoat', look['lower'])
        pep_mesh, pep = peplum(bones, waist, upper, rings, T['peplum'], 'short_gown_skirt', look['upper'])
        apron_mesh = apron(bones, waist, rings, pep, T['apron'], T['skirt']['hem_y'], look['apron'])
        string = band([upper, pep_mesh, apron_mesh], waist, T['band'], 'apron_band', look['apron'], {'pelvis': .55, 'spine_01': .45})
        kt = T['kerchief']
        neckerchief = kerchief(body, bones, kt, upper, look['kerchief'], waist+kt['front_point_above_waist'])
        if look['headwear'] == 'cap':
            head = head_cover(body, bones, hair, T['cap'], 'headwear_linen_cap', look['head'])
        else:
            head = head_cover(body, bones, hair, T['handkerchief'], 'headwear_head_handkerchief', look['head'])
        parts = [upper, pep_mesh, skirt_mesh, apron_mesh, string, neckerchief, head]
    else:
        s = T['shirt']
        waist = spine2-s['waist_below_spine02']
        upper = _bodice(body, bones, waist, s['ease'], s['neck_below_neck01'], 'calico_shirt_body', look['upper'],
                        pouch=s['pouch'], sleeve=s['sleeve_fullness'])
        legs = leggings(body, bones, T['leggings'], T['skirt']['hem_y'], look['leggings'])
        skirt_mesh, rings = loft_skirt(body, bones, waist, waist, upper, T['skirt'], 'strouding_skirt', look['lower'],
                                       extra=legs['positions_m'])
        pep_mesh, _pep = peplum(bones, waist, upper, rings, T['peplum'], 'calico_shirt_skirt', look['upper'])
        list_band = selvage(bones, waist, rings, T['selvage'], 'strouding_selvage', look['selvage'])
        wrap = blanket(body, bones, T['blanket'], look['blanket'], [upper, pep_mesh])
        silver = brooches(upper, bones, T['brooches'], look['brooches'])
        parts = [upper, pep_mesh, skirt_mesh, list_band, legs, wrap, silver]
    for m in parts:
        m.pop('_normals', None)
        for k in ('source_basis', 'source_triangle_indices'):
            m.pop(k, None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    used = {m['material'] for m in parts} | {look['shoes']}
    materials = {k: copy.deepcopy(v) for k, v in MATERIALS[role].items() if k in used}
    return dict(format='chicago4d_women_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y', forward_axis='+Z',
                grade='reconstructed', assembly=ASSEMBLIES[role], body_sha256=BODY_SHA256, body_semantic_sha256=before,
                source_body_unchanged=True, meshes=parts, materials=materials, shoe_material=look['shoes'],
                weave_material=look['shoes'], tailoring=copy.deepcopy(T), skirt=True, **extra,
                limitations=['Cuts, eases, lengths, folds and colours are reconstructed; prints and checks are drawn as their mean colour',
                             'No cloth simulation: skirts, the short gown\'s skirt and the apron share the leg-following skirt weights (T-3423)',
                             'Head covers rigid on the head bone over the shared short04 hair cap'])


def _prepare(role, root, recipe, variant, body):
    root = Path(root).resolve()
    spec = recipe.get('role_1812', {})
    comp = recipe.get('women_components', {})
    need(spec.get('module') == 'human_women_1812' and spec.get('assembly') == ASSEMBLIES[role], 'unsupported 1812 women generator')
    need(comp.get('version') == 1 and comp.get('generator') == 'tools/human_women_1812.py' and comp.get('role') == role,
         'unsupported women component generator')
    need(variant.get('recipe_path') == RECIPES[role] and variant.get('component_assembly') == ASSEMBLIES[role]
         and ROLE_OF.get(variant.get('id')) == role, 'the women assembly is bound to its own recipe')
    need(recipe.get('scene_date') == SCENE_DATE and recipe.get('grade') == 'reconstructed', 'women scene/appearance grade changed')
    need(comp.get('tailoring') == json.loads(json.dumps(TAILORING[role])), 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == comp.get('body_sha256'), 'unreviewed women body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(comp.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'women components require the declared liberty')
    if role == 'potawatomi_woman_1812':
        need(variant.get('review_required') is True and variant.get('touches_removal') is True
             and len(variant.get('review_reason', '')) > 80 and len(variant.get('touches_removal_reason', '')) > 80,
             'a Potawatomi figure keeps review_required and touches_removal with their own prose')
    for garment in comp['garments']:
        prov = garment.get('provenance', {})
        need(prov.get('grade') in ('attested', 'inferred', 'reconstructed') and (prov.get('source_ids') or prov.get('liberty')),
             f"garment {garment.get('id')} has no provenance")
        for sid in prov.get('source_ids', []):
            record = json.loads((root/'data/sources'/f'{sid}.json').read_text())
            need(record.get('id') == sid and record.get('rights_status') in ('public_domain', 'no_known_restrictions'),
                 f'{sid}: not a cleared reference')
    for sid in recipe['sources']:
        need((root/'data/sources'/f'{sid}.json').is_file(), f'{sid}: no source record')
    need(not recipe['hair_component'].get('fitter'), 'the head covers are laid over the shared short04 hair cap')
    from human_hair_short04 import fit
    hair = fit(body, recipe['hair_component'], root)[0]
    bundle = construct(body, hair, variant['id'])
    bundle['liberty'] = LIBERTY
    look = set(LOOKS[variant['id']].values())
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in comp['garments']
                          if g['material'] in look]
    need({m['material'] for m in bundle['meshes']} <= {g['material'] for g in bundle['garments']},
         'a garment of the outfit has no provenance entry')
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


def prepare_lady(root, recipe, variant, body):
    """The canonical builder's source consumer for lady_1812; never a world switch."""
    return _prepare('lady_1812', root, recipe, variant, body)


def prepare_working(root, recipe, variant, body):
    """The canonical builder's source consumer for woman_working_1812 and its woman-of-the-
    country variant; never a world switch."""
    return _prepare('woman_working_1812', root, recipe, variant, body)


def prepare_potawatomi(root, recipe, variant, body):
    """The canonical builder's source consumer for potawatomi_woman_1812; never a world switch."""
    return _prepare('potawatomi_woman_1812', root, recipe, variant, body)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True); p.add_argument('--recipe', type=Path, required=True)
    p.add_argument('--variant', required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    from human_hair_short04 import fit
    body = json.loads(raw)
    hair = fit(body, json.loads(a.recipe.read_text())['hair_component'], Path(__file__).resolve().parent.parent)[0]
    data = construct(body, hair, a.variant)
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]},
                     indent=1, default=str))
