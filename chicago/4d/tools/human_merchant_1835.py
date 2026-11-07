# SPDX-License-Identifier: GPL-3.0-or-later
"""An 1835 merchant's day dress on the shared portable male rig (T-3449).

First worn by Philip F. W. Peck (attested), merchant at South Water and LaSalle in the
Chicago of 1835. The pieces, read from the period pictures in the recipe
(data/humans/recipes/merchant_1835.json):

  shirt          white linen, made only where it shows: the front inside the waistcoat's
                 opening and a little of the cuffs (the Met's coat and trousers of about
                 1833; Durand's portrait of the New York merchant Luman Reed, 1835)
  collar points  the shirt collar's two points standing up at the cheeks above the stock
                 (Reed, 1835)
  stock          a black silk stock wound high round the neck, under the jaw (Reed, 1835;
                 the Met's 1833 ensemble wears one)
  waistcoat      buff, single-breasted, cut straight at the waist with a rolled collar
                 (the Met's ensemble of about 1833)
  tailcoat       dark blue wool, double-breasted and cut away square at the waist, broad
                 lapels, a collar standing high behind the neck, tails to the back of the
                 knee, gilt buttons (the Met's coat of about 1833; men on Broadway, 1836)
  trousers       pale stone, full and straight to the instep (the Met's ensemble)
  top hat        black, its crown flaring a little to a flat top and its brim curled at
                 the sides (Hornor's Broadway, 1836), rigid on the head bone and a mesh of
                 its own, so a renderer can lift it for a greeting

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with its T-3449 supplement. The source anatomy is never changed:
every piece is a shell offset from the body's own triangles (its UVs and skin weights
carried) or a loft round the body's own cross-sections, skinned to the body's own bones.
Reuses the 1904 gentleman's helpers (tools/human_gentleman_1904.py).

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_merchant_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_workwear_fit import _slab_points, garment_shell
from human_period_wardrobe import finish_edges
import human_gentleman_1904 as G
from human_maid_1904 import _two_sided

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'merchant_1835_v1'
RECIPE = 'data/humans/recipes/merchant_1835.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=dict(ease=.006, waist_below_spine02=.115, top_below_neck=.036, cuff_beyond_coat=.012),
    stock=dict(ease=.008, bottom_below_neck=.042, back_bottom_below_neck=.004, back_above_neck=.062, jaw_clearance=.004, segments=40, rows=7),
    collar_points=dict(inner_deg=20., outer_deg=52., rise=.040, tip_out=.012, standoff=.006),
    waistcoat=dict(ease=.016, armpit_extra=.008, hem_below_spine02=.098, top_below_neck=.020,
                   v_bottom_above_spine02=.245, v_half_width_top=.046, roll_width=.020, roll_notch=.85, front_only_x=.15),
    coat=dict(ease=.022, armpit_extra=.022, sleeve_short_of_wrist=.024, collar_above_neck=.042, waist_below_spine02=.010,
              roll_above_spine02=.120, v_half_width_top=.088, lapel_width=.060, lapel_notch=.78, lapel_top_above_neck=-.028),
    tails=dict(hem_y=.530, ease=.020, edge_top_deg=74., edge_hem_deg=124., vent_deg=3., segments=24, rows=14),
    buttons=dict(radius=.0085, rows=3, spacing=.045, x=.066, below_roll=.018, standoff=.0025, sides=10),
    trousers=dict(ease=.011, waist_height_fraction=.585, cuff_radius_ratio=.92, added_section_ease=.012,
                  thigh_transition_fraction=.65, hem_front_y=.062, hem_back_y=.030),
    top_hat=dict(seat_below_top=.084, ease=.007, crown_height=.160, crown_flare=1.08, brim_side=.038, brim_fore=.052,
                 brim_curl=.022, thickness=.004),
)

MATERIALS = {
    'garment_upper__shirt_linen_1835': {'base_color_linear': [.80, .80, .78, 1], 'roughness': .78},
    'garment_outer__tailcoat_blue_1835': {'base_color_linear': [.016, .021, .052, 1], 'roughness': .84},
    'garment_outer__waistcoat_buff_1835': {'base_color_linear': [.50, .38, .20, 1], 'roughness': .8},
    'garment_lower__trousers_stone_1835': {'base_color_linear': [.52, .49, .42, 1], 'roughness': .88},
    'accessory__silk_stock_black': {'base_color_linear': [.012, .012, .014, 1], 'roughness': .42},
    'accessory__gilt_buttons': {'base_color_linear': [.45, .32, .11, 1], 'roughness': .35},
    'headwear__top_hat_black': {'base_color_linear': [.014, .013, .013, 1], 'roughness': .55},
    'footwear__black_boots_1835': {'base_color_linear': [.012, .011, .011, 1], 'roughness': .38},
}
SHOE_MATERIAL = 'footwear__black_boots_1835'
WEAVE_MATERIAL = 'garment_upper__shirt_linen_1835'


def shirt(body, bones):
    """The white shirt, made only where it can be seen: its front inside the waistcoat's
    opening up to the foot of the stock, and a cuff beyond each coat sleeve."""
    t = TAILORING['shirt']; c = TAILORING['coat']; v = TAILORING['waistcoat']
    neck = bones['neck_01']['head_m'][1]; spine = bones['spine_02']['head_m'][1]
    lo = spine-t['waist_below_spine02']; hi = neck-t['top_below_neck']
    wrist = abs(bones['hand_l']['head_m'][0])
    cuff = wrist-.012
    coat_end = wrist-c['sleeve_short_of_wrist']
    fields = [lambda p: p['p'][1]-lo, lambda p: hi-p['p'][1], lambda p: cuff-p['p'][0], lambda p: cuff+p['p'][0]]
    front_y = spine+v['v_bottom_above_spine02']-.035
    cuff_x = coat_end-t['cuff_beyond_coat']
    def pieces(poly):
        front = G._clip(G._clip(G._clip(G._clip(poly, lambda p: p['p'][1]-front_y), lambda p: p['p'][2]),
                                lambda p: .095-p['p'][0]), lambda p: .095+p['p'][0])
        left = G._clip(poly, lambda p: p['p'][0]-cuff_x)
        right = G._clip(poly, lambda p: -p['p'][0]-cuff_x)
        return [front, left, right]
    out = G._poly_shell(body, bones, 'shirt_front_and_cuffs', 'garment_upper__shirt_linen_1835', fields, t['ease'],
                        [(lo, hi)], neck, pieces)
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='white linen shirt, front and cuffs', front_bottom_y_m=front_y, top_y_m=hi,
                          cuff_x_m=[cuff_x, cuff], ease_m=t['ease'], source_body_mutated=False)
    return out


def _neck_frame(body, bones):
    """Neck-skinned body points (head and jaw under 30 per cent) and the neck's centre."""
    m = body['meshes'][0]
    neck = bones['neck_01']['head_m'][1]
    pts = [p for p, w in zip(m['positions_m'], m['weights'])
           if neck-.06 <= p[1] <= neck+.08 and abs(p[0]) < .11 and w.get('head', 0.)+w.get('jaw', 0.) < .3]
    base = [p for p in pts if neck-.025 <= p[1] <= neck+.015]
    cz = (min(p[2] for p in base)+max(p[2] for p in base))/2
    jaw = [p for p, w in zip(m['positions_m'], m['weights'])
           if neck-.03 <= p[1] <= neck+.12 and abs(p[0]) < .12 and w.get('head', 0.)+w.get('jaw', 0.) >= .3]
    return pts, jaw, (0., cz)


def stock(body, bones, lod=0):
    """A black silk stock wound round the neck: a band whose every ring encloses the neck's
    own section at its height, from below the collar bones' line up to just under the jaw
    in front and high behind, its top following the jaw line round. Skinned to the neck."""
    t = TAILORING['stock']
    neck = bones['neck_01']['head_m'][1]
    pts, jaw, (cx, cz) = _neck_frame(body, bones)
    n = t['segments']
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    bottom = neck-t['bottom_below_neck']
    def radius(k, y):
        dx, dz = dirs[k]
        slab = [p for p in pts if abs(p[1]-y) <= .007] or [p for p in pts if abs(p[1]-y) <= .02]
        need(bool(slab), 'no neck section for the stock')
        return max((p[0]-cx)*dx+(p[2]-cz)*dz for p in slab)+t['ease']
    tops = []
    for k, (dx, dz) in enumerate(dirs):
        top = neck+t['back_above_neck']
        # The jaw line: the lowest head- or jaw-skinned point standing out over this ring.
        for p in jaw:
            ang = math.atan2(p[0]-cx, p[2]-cz)
            d = abs((ang-math.atan2(dx, dz)+math.pi) % (2*math.pi)-math.pi)
            if d > math.radians(14) or p[1] < bottom+.01:
                continue
            if (p[0]-cx)*dx+(p[2]-cz)*dz >= radius(k, min(p[1], neck+.07))-.012:
                top = min(top, p[1]-t['jaw_clearance'])
        tops.append(max(top, bottom+.022))
    # The foot of the stock rises behind, where the coat's collar stands close over it.
    bottoms = [bottom+(t['bottom_below_neck']-t['back_bottom_below_neck'])*(1-dz)/2 for dx, dz in dirs]
    # Smooth the top line round the ring.
    tops = [min(tops[k], (tops[k-1]+2*tops[k]+tops[(k+1) % n])/4) for k in range(n)]
    out = empty('black_silk_stock', 'accessory__silk_stock_black')
    rows = t['rows']
    for r in range(rows):
        f = r/(rows-1)
        for k, (dx, dz) in enumerate(dirs):
            y = bottoms[k]+(tops[k]-bottoms[k])*f
            rr = radius(k, y)
            out['positions_m'].append([cx+rr*dx, y, cz+rr*dz]); out['uvs'].append([k/n, f])
            out['weights'].append({'neck_01': 1.} if f > .3 else {'neck_01': .6+f, 'spine_03': .4-f})
    for r in range(rows-1):
        for k in range(n):
            a = r*n+k; b = r*n+(k+1) % n; c = a+n; d = b+n
            out['triangles'] += [[a, b, d], [a, d, c]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='black silk stock', bottom_y_m=bottom, top_front_y_m=tops[0],
                          top_back_y_m=tops[n//2], ease_m=t['ease'], skinning='neck_01 (spine_03 at the foot)')
    return out, (dirs, tops, (cx, cz))


def collar_points(body, bones, stock_mesh, frame):
    """The shirt collar's two points standing up out of the stock at the cheeks, as the
    1835 portrait shows: a small triangle each side, its foot on the stock's top edge, its
    tip a few centimetres up and out along the jaw. Two skins 0.6 mm apart (thin cloth)."""
    t = TAILORING['collar_points']
    dirs, tops, (cx, cz) = frame
    n = len(dirs)
    body_mesh = body['meshes'][0]
    out = empty('shirt_collar_points', 'garment_upper__shirt_linen_1835')
    def top_at(deg):
        k = (deg/360.*n) % n; k0 = int(k) % n; k1 = (k0+1) % n; f = k-int(k)
        return tops[k0]*(1-f)+tops[k1]*f
    for sign in (1, -1):
        base = len(out['positions_m'])
        A = (t['inner_deg'], 0.); B = (t['outer_deg'], 0.)
        rows, cols = 6, 4
        for r in range(rows):
            v = r/(rows-1)
            for c in range(cols):
                u = c/(cols-1)
                deg = A[0]+(B[0]-A[0])*u
                deg = deg+(B[0]+6-deg)*v          # the tip leans out toward the jaw's corner
                y0 = top_at(deg)-.004
                y = y0+v*t['rise']*(1-.55*(1-u))
                x = sign*math.sin(math.radians(deg))*.062
                try:
                    zb, wb = G._surface_sample(body_mesh, x, y)
                except ValueError:
                    zb = cz+.06
                try:
                    zs, _ = G._surface_sample(stock_mesh, x, y0+.001)
                except ValueError:
                    zs = zb
                z = max(zb+t['standoff'], zs+.0015 if v < .4 else zb+t['standoff'])+t['tip_out']*v
                out['positions_m'].append([x, y, z]); out['uvs'].append([u, v])
                out['weights'].append({'neck_01': 1.} if v < 1e-9 else ({'head': 1.} if v > .999 else {'neck_01': 1-v, 'head': v}))
        for r in range(rows-1):
            for c in range(cols-1):
                a = base+r*cols+c; b = a+1; d = a+cols; e = d+1
                faces = ([a, b, e], [a, e, d]) if sign > 0 else ([a, e, b], [a, d, e])
                out['triangles'] += [list(f) for f in faces]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = _two_sided(out)
    out['receipt'] = dict(garment='shirt collar points', rise_m=t['rise'], double_sided=True)
    return out


def waistcoat(body, bones):
    t = TAILORING['waistcoat']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['hem_below_spine02']; hi = neck-t['top_below_neck']
    vb = spine+t['v_bottom_above_spine02']
    # Only the front is made: the back lies wholly under the coat, where a whole waistcoat
    # only pokes through it as the arms come down.
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: .35-G._arm_mass(v),
              lambda v: t['front_only_x']-v['p'][0], lambda v: t['front_only_x']+v['p'][0], lambda v: v['p'][2]-.01]
    out = G._poly_shell(body, bones, 'waistcoat_buff', 'garment_outer__waistcoat_buff_1835', fields, t['ease'],
                        [(lo, hi)], neck, G._v_pieces(vb, t['v_half_width_top'], hi), smooth=(12, t['ease']))
    G._armpit_ease(out, body, bones, t['armpit_extra'])
    out['receipt'] = dict(garment='buff single-breasted waistcoat front, straight at the waist', hem_y_m=lo, top_y_m=hi, v_bottom_y_m=vb)
    return out, (lo, vb, hi)


def coat_body(body, bones):
    """The tailcoat above its waist seam: closed torso to the roll of the lapels, long
    sleeves, a collar standing high behind the neck."""
    t = TAILORING['coat']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['waist_below_spine02']; hi = neck+t['collar_above_neck']
    cuff = abs(bones['hand_l']['head_m'][0])-t['sleeve_short_of_wrist']
    vb = spine+t['roll_above_spine02']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: cuff-v['p'][0], lambda v: cuff+v['p'][0]]
    out = G._poly_shell(body, bones, 'tailcoat_body', 'garment_outer__tailcoat_blue_1835', fields, t['ease'],
                        [(lo, hi)], neck, G._v_pieces(vb, t['v_half_width_top'], hi), smooth=(60, .019))
    loose = G._armpit_ease(out, body, bones, t['armpit_extra'])
    out['receipt'] = dict(garment='tailcoat body and sleeves', armpit_points_eased=loose, waist_seam_y_m=lo, collar_y_m=hi,
                          roll_point_y_m=vb, sleeve_end_x_m=cuff)
    return out, (lo, vb, hi)


def rolled_edges(base, roll, name, material, width, notch, half_top, top_gap=.004, standoff=.003, stop=None):
    """Two rolled lapels (or a waistcoat's rolled collar) laid on a garment's front along its
    V's edges, from the roll point to the top, widening to a notch: a strip proud of the
    garment and skinned as the garment beneath it (the 1904 gentleman's lapel, re-cut)."""
    lo, vb, hi = roll
    out = empty(name, material)
    rows, cols = 16, 5
    slope = half_top/(hi-vb)
    end = min(hi-top_gap, stop if stop is not None else hi)
    for sign in (1, -1):
        start = len(out['positions_m'])
        for r in range(rows):
            s = r/(rows-1)
            y = vb+s*(end-vb)
            edge = slope*(y-vb)
            for step in range(40):
                try:
                    G._surface_sample(base, sign*(edge+.002), y); break
                except ValueError:
                    edge += .002
            ramp = min(1., s/notch)
            w = max(width*(ramp*(2-ramp))*(1. if s <= notch else .55), .006)
            for c in range(cols):
                u = c/(cols-1)
                x = sign*min(.13, edge+.002+u*w)
                while True:
                    try:
                        z, wt = G._surface_sample(base, x, y); break
                    except ValueError:
                        need(abs(x) > edge, 'rolled edge has no garment beneath it')
                        x -= sign*.002
                out['positions_m'].append([x, y, z+standoff*(1-.4*u)])
                out['uvs'].append([.5+sign*.25*u, s]); out['weights'].append(wt)
        for r in range(rows-1):
            for c in range(cols-1):
                a = start+r*cols+c; b = a+1; d = a+cols; e = d+1
                faces = ([a, b, e], [a, e, d]) if sign > 0 else ([a, e, b], [a, d, e])
                for f in faces:
                    out['triangles'].append(list(f)); out['corner_uvs'].append([out['uvs'][i] for i in f])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment=name.replace('_', ' '), roll_point_y_m=vb, width_m=width, notch_fraction=notch)
    return out


def tails(body, bones, coat, waist, t=None, name='tailcoat_tails', material='garment_outer__tailcoat_blue_1835',
          garment='tailcoat tails to the back of the knee'):
    """The tailcoat's tails: two panels lofted round convex supports that enclose the body's
    own sections (and hang: below the seat no ring is narrower than the one above it), cut
    away from the front at the waist, their front edges sloping back to the hem at the back
    of the knee, a short vent between them. Each tail goes with its own thigh and calf.
    `t`, `name` and `material` let another coat (the 1812 soldier's, T-3451) cut its own."""
    t = t or TAILORING['tails']
    rows, cols, ease = t['rows'], t['segments'], t['ease']
    hem = t['hem_y']; top = waist+.006
    levels = [top+(hem-top)*i/(rows-1) for i in range(rows)]
    tris = [[m['positions_m'][i] for i in f] for m in body['meshes'] for f in m['triangles']
            if min(m['positions_m'][i][1] for i in f) <= top+.02 and max(m['positions_m'][i][1] for i in f) >= hem-.02]
    N = 144
    ring = [2*math.pi*k/N for k in range(N)]
    supports = []
    for i, y in enumerate(levels):
        pts = _slab_points(tris, levels[min(rows-1, i+1)]-.004, levels[max(0, i-1)]+.004)
        need(len(pts) >= 3, 'empty tail band')
        supports.append([max(math.sin(a)*p[0]+math.cos(a)*p[2] for p in pts)+ease for a in ring])
    widest = max(range(rows), key=lambda i: sum(supports[i]))
    for i in range(widest+1, rows):
        supports[i] = [max(a, .995*b) for a, b in zip(supports[i], supports[i-1])]
    for i in range(rows):
        s = supports[i]
        supports[i] = [max(s[k], (s[k-1]+2*s[k]+s[(k+1) % N])/4) for k in range(N)]
    coat_sec = []
    for face in coat['triangles']:
        tri = [coat['positions_m'][i] for i in face]
        if min(p[1] for p in tri) <= top+.008 <= max(p[1] for p in tri):
            coat_sec.extend(_slab_points([tri], top+.008, top+.008))
    def support(i, a):
        k = (a % (2*math.pi))/(2*math.pi)*N; k0 = int(k) % N; f = k-int(k)
        return supports[i][k0]*(1-f)+supports[i][(k0+1) % N]*f
    knee = bones['calf_l']['head_m'][1]
    out = empty(name, material)
    vent = math.radians(t['vent_deg'])/2
    for side in (1, -1):
        base = len(out['positions_m'])
        for i, y in enumerate(levels):
            f = i/(rows-1)
            edge = math.radians(t['edge_top_deg']+(t['edge_hem_deg']-t['edge_top_deg'])*f**.8)
            for c in range(cols):
                u = c/(cols-1)
                a = edge+(math.pi-vent-edge)*u
                a = a if side > 0 else 2*math.pi-a
                r = support(i, a)+.006*f**1.4
                if i == 0 and coat_sec:
                    r = min(r, max(math.sin(a)*p[0]+math.cos(a)*p[2] for p in coat_sec)-.0015)
                p = [math.sin(a)*r, y, math.cos(a)*r]
                tt = min(1., max(0., (waist-y)/(.45*(waist-knee)))); tt = tt*(2-tt)
                share = tt*.45
                calf = min(1., max(0., (knee+.02-y)/.3))
                s = 'l' if side > 0 else 'r'
                w = {'pelvis': 1-share}
                if share*(1-calf) > 1e-6:
                    w[f'thigh_{s}'] = share*(1-calf)
                if share*calf > 1e-6:
                    w[f'calf_{s}'] = share*calf
                out['positions_m'].append(p); out['uvs'].append([u, f]); out['weights'].append(G._skin4(w, 1.))
        for i in range(rows-1):
            for c in range(cols-1):
                a = base+i*cols+c; b = a+1; d = a+cols; e = d+1
                faces = ([a, e, b], [a, d, e]) if side > 0 else ([a, b, e], [a, e, d])
                for fc in faces:
                    out['triangles'].append(list(fc)); out['corner_uvs'].append([out['uvs'][j] for j in fc])
    # Standing clearance: every body point behind the tails lies inside them.
    worst = math.inf
    for i in range(rows-1):
        for p in _slab_points(tris, levels[i+1], levels[i]):
            a = math.atan2(p[0], p[2]) % (2*math.pi)
            if not math.radians(t['edge_hem_deg']) <= a <= 2*math.pi-math.radians(t['edge_hem_deg']):
                continue
            rr = support(i, a)
            worst = min(worst, rr-math.hypot(p[0], p[2]))
    need(worst > .004, f'tails meet the standing body ({worst:.4f} m)')
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment=garment, hem_y_m=hem, top_y_m=top, ease_m=ease,
                          minimum_standing_body_clearance_m=worst, front_edge_deg=[t['edge_top_deg'], t['edge_hem_deg']],
                          skinning='pelvis at the seam; each tail with its own thigh/calf')
    return out


def buttons(coat, roll):
    """Two rows of gilt buttons down the coat's closed front below the roll point, small
    discs laid on the cloth and skinned as the coat beneath them."""
    t = TAILORING['buttons']
    lo, vb, hi = roll
    out = empty('tailcoat_buttons', 'accessory__gilt_buttons')
    n = t['sides']; placed = 0
    for row in range(t['rows']):
        y = vb-t['below_roll']-row*t['spacing']
        if y < lo+.012:
            continue
        for sign in (1, -1):
            x0 = sign*t['x']
            z0, w = G._surface_sample(coat, x0, y)
            c = len(out['positions_m']); placed += 1
            out['positions_m'].append([x0, y, z0+t['standoff']+.0015]); out['uvs'].append([.5, .5]); out['weights'].append(w)
            for k in range(n):
                a = 2*math.pi*k/n
                x, yy = x0+t['radius']*math.cos(a), y+t['radius']*math.sin(a)
                try:
                    z, _ = G._surface_sample(coat, x, yy)
                except ValueError:
                    z = z0
                out['positions_m'].append([x, yy, z+t['standoff']]); out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)])
                out['weights'].append(w)
            for k in range(n):
                out['triangles'].append([c, c+1+k, c+1+(k+1) % n])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='gilt coat buttons', count=placed, radius_m=t['radius'])
    return out


def trousers(body, bones, height):
    t = TAILORING['trousers']
    recipe = dict(waist_height_fraction=t['waist_height_fraction'], shirt_hem_fraction=.565,
                  workwear_tailoring_v5=dict(waistcoat_closed_front_torso_fraction=.4,
                                             trouser_cuff_radius_ratio=t['cuff_radius_ratio'],
                                             trouser_added_section_ease_m=t['added_section_ease'],
                                             trouser_thigh_transition_fraction=t['thigh_transition_fraction']))
    out = garment_shell(body['meshes'][0], 'trousers', t['ease'], recipe, bones, height)
    out = G._lengthen_hems(out, bones, t)
    out = finish_edges(out, .0015)
    out['name'] = 'full_trousers'; out['material'] = 'garment_lower__trousers_stone_1835'
    for k in ('source_basis', 'source_triangle_indices'):
        out.pop(k, None)
    return out


def top_hat(body, bones, lod=0):
    """A black top hat seated round the skull's own section: a tall crown flaring a little
    to a flat top, a narrow brim curled up at the sides. Rigid on the head bone, a separate
    mesh, so it can be lifted off and set back."""
    t = TAILORING['top_hat']
    P = body['meshes'][0]['positions_m']; W = body['meshes'][0]['weights']
    head_pts = [p for p, w in zip(P, W) if w.get('head', 0.) > .9]
    top = max(p[1] for p in head_pts)
    seat = top-t['seat_below_top']
    band = [p for p in head_pts if seat-.012 <= p[1] <= seat+.03]
    cx = (min(p[0] for p in band)+max(p[0] for p in band))/2
    cz = (min(p[2] for p in band)+max(p[2] for p in band))/2
    n = (40, 28, 20, 12)[lod]
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    seat_r = [max((p[0]-cx)*dx+(p[2]-cz)*dz for p in band)+t['ease'] for dx, dz in dirs]
    seat_r = [(seat_r[(k-1) % n]+2*seat_r[k]+seat_r[(k+1) % n])/4+.002 for k in range(n)]
    H = t['crown_height']; fl = t['crown_flare']
    out = empty('headwear_top_hat', 'headwear__top_hat_black')
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
    edge = ring([r+b+.004 for r, b in zip(seat_r, brim)], lambda k: seat+curl[k]+th*.6)
    over_out = ring([r+b for r, b in zip(seat_r, brim)], lambda k: seat+th+curl[k])
    # Crown: nearly straight sides waisted a little above the band, flaring to the top edge.
    profile = [(0., 1.), (.08, .995), (.35, .985), (.7, 1.0+(fl-1.)*.45), (.97, fl), (1., fl*.985)]
    crown = [ring([r*f for r in seat_r], (lambda yy: (lambda k: yy))(seat+th+H*h)) for h, f in profile]
    rings = [inner, under_out, edge, over_out]+crown
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    apex = len(out['positions_m'])
    out['positions_m'].append([cx, seat+th+H, cz]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([crown[-1][k], apex, crown[-1][(k+1) % n]])
    lining_y = top+.004
    lining = ring([r*.55 for r in seat_r], lambda k: lining_y)
    for k in range(n):
        a, b, c, d = inner[k], inner[(k+1) % n], lining[(k+1) % n], lining[k]
        out['triangles'] += [[a, b, c], [a, c, d]]
    lc = len(out['positions_m']); out['positions_m'].append([cx, lining_y+.004, cz]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([lining[k], lining[(k+1) % n], lc])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='black top hat', seat_y_m=seat, crown_height_m=H, crown_flare=fl, brim_side_m=t['brim_side'],
                          brim_fore_m=t['brim_fore'], head_bone='head', separate_mesh=True,
                          lift='rigid on the head bone; a renderer may detach it to the right hand socket for a greeting')
    return out


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    shirt_mesh = shirt(body, bones)
    stock_mesh, frame = stock(body, bones)
    vest, vroll = waistcoat(body, bones)
    t = TAILORING['waistcoat']
    vest_roll = rolled_edges(vest, vroll, 'waistcoat_rolled_collar', 'garment_outer__waistcoat_buff_1835',
                             t['roll_width'], t['roll_notch'], t['v_half_width_top'], top_gap=.002, standoff=.0025)
    coat, roll = coat_body(body, bones)
    c = TAILORING['coat']
    parts = [shirt_mesh, collar_points(body, bones, stock_mesh, frame), stock_mesh, finish_edges(vest, .0015), vest_roll,
             finish_edges(coat, .0018),
             rolled_edges(coat, roll, 'tailcoat_lapels', 'garment_outer__tailcoat_blue_1835', c['lapel_width'],
                          c['lapel_notch'], c['v_half_width_top'], stop=bones['neck_01']['head_m'][1]+c['lapel_top_above_neck']),
             tails(body, bones, coat, roll[0]), buttons(coat, roll), trousers(body, bones, height), top_hat(body, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_merchant_1835_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; no picture is of Peck or of Chicago',
                             'No cloth simulation: shells and tails follow the body bones (each tail goes with its own leg)',
                             'Hat rigid on the head bone; lifting it is a renderer action, not a clip'])


def prepare_merchant_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3449; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('merchant_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_merchant_1835.py',
         'unsupported merchant component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'merchant assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1835-07-01' and recipe.get('grade') == 'reconstructed',
         'merchant scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed merchant body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'merchant components require the declared liberty')
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
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    data = construct(json.loads(raw))
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]},
                     indent=1, default=str))
