# SPDX-License-Identifier: GPL-3.0-or-later
"""An 1812 private of the First Infantry on the shared portable male rig (T-3451).

An anonymous private of Captain Nathan Heald's company of the First Regiment of Infantry,
the garrison of the first Fort Dearborn in the summer of 1812 (Quaife 1913, Appendix VIII,
prints the company's muster-roll). No soldier of the company is named here and no picture
of any of them is known. The pieces, read from the period law and regulations and from the
pictures in the recipe (data/humans/recipes/soldier_1812.json):

  coat         dark blue wool with a red standing collar and red cuffs, single-breasted and
               closed, cut away at the waist to short tails behind. The red facings and the
               felt cap are read backwards from the change of April 1813, which made the
               coat "uniformly blue; no red collars or cuffs" and put leather caps in place
               of felt: what the change removed was worn before it.
  stock        a black leather stock round the neck (the 1802 act's "stock and clasp")
  crossbelts   two white belts over the shoulders crossing on the chest, a black cartridge
               box behind the right hip and a bayonet scabbard at the left (Krimmel's
               Philadelphia soldiery, 1811-13; Ogden's plate of 1802-1810)
  overalls     white linen, full length (the 1802 act issues two pair of linen overalls a
               year; this is August)
  cap          a tall black felt cylinder with a short leather peak and a white feather at
               the front, rigid on the head bone and a mesh of its own
  shoes        black shoes and half gaiters, the shared closed boot (the 1802 act)

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with its T-3451 supplement. The source anatomy is never changed.
Reuses the 1904 gentleman's and the 1835 merchant's helpers.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_soldier_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_period_wardrobe import finish_edges
from human_workwear_fit import _clip, garment_shell
import human_gentleman_1904 as G
import human_merchant_1835 as M

BODY_SHA256 = 'e7b088b88ea18bb309ca990ef6c0cafea9420ac152d42d1351c1a9795daa9269'
ASSEMBLY = 'soldier_1812_v1'
RECIPE = 'data/humans/recipes/soldier_1812.json'
LIBERTY = 'L-human-modular-dress-1789'
PERSON = 'anonymous_private_heald_company_1812'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    coat=dict(ease=.020, armpit_extra=.020, sleeve_short_of_wrist=.022, top_below_neck=.008, waist_below_spine02=.024,
              cuff_depth=.065, smoothing=60, smoothing_min_ease=.018),
    collar=dict(ease=.018, bottom_below_neck=.034, back_above_neck=.050, below_stock_top=.010, front_gap_deg=26.,
                segments=40, rows=5),
    tails=dict(hem_y=.700, ease=.020, edge_top_deg=96., edge_hem_deg=138., vent_deg=3., segments=20, rows=10),
    buttons=dict(radius=.0075, count=8, below_collar=.030, above_waist=.022, standoff=.0025, sides=10),
    crossbelts=dict(width=.052, shoulder_x=.092, hip_x=.150, top_below_neck=.020, offsets=(.0028, .0042)),
    cartridge_box=dict(width=.17, height=.11, depth=.055, x=-.105, below_waist=.045, off_back=.012),
    scabbard=dict(width=.034, thickness=.012, length=.34, below_waist=.012, off_side=.020, back_z=-.045, tilt_deg=14.),
    overalls=dict(ease=.012, waist_height_fraction=.585, band_ease=.013, band_below_waist=.03, band_above_coat_seam=.016, cuff_radius_ratio=.92, added_section_ease=.012,
                  thigh_transition_fraction=.65, hem_front_y=.064, hem_back_y=.032),
    cap=dict(seat_below_top=.078, ease=.007, height=.175, flare=1.03, peak=.050, peak_droop=.016, plume_height=.13,
             plume_radius=.019, plume_deg=-24., thickness=.004),
)

MATERIALS = {
    'garment_upper__coat_blue_1812': {'base_color_linear': [.014, .019, .055, 1], 'roughness': .86},
    'garment_upper__facings_red_1812': {'base_color_linear': [.34, .022, .018, 1], 'roughness': .84},
    'garment_lower__overalls_linen_1812': {'base_color_linear': [.70, .68, .62, 1], 'roughness': .86},
    'accessory__leather_stock_black': {'base_color_linear': [.010, .010, .011, 1], 'roughness': .45},
    'accessory__crossbelts_white': {'base_color_linear': [.74, .72, .66, 1], 'roughness': .7},
    'accessory__cartridge_box_black': {'base_color_linear': [.012, .011, .010, 1], 'roughness': .42},
    'accessory__white_metal_buttons': {'base_color_linear': [.52, .52, .50, 1], 'roughness': .35},
    'headwear__felt_cap_black': {'base_color_linear': [.013, .012, .012, 1], 'roughness': .7},
    'headwear__plume_white': {'base_color_linear': [.80, .79, .75, 1], 'roughness': .9},
    'footwear__shoes_gaiters_black_1812': {'base_color_linear': [.012, .011, .011, 1], 'roughness': .45},
}
SHOE_MATERIAL = 'footwear__shoes_gaiters_black_1812'
WEAVE_MATERIAL = 'garment_lower__overalls_linen_1812'


def _split(mesh, keep, name, material):
    """The triangles of `mesh` whose centroid `keep` accepts, as a mesh of their own."""
    out = empty(name, material); ids = {}
    for face, cuv in zip(mesh['triangles'], mesh['corner_uvs']):
        c = [sum(mesh['positions_m'][i][a] for i in face)/3 for a in range(3)]
        if not keep(c):
            continue
        new = []
        for i in face:
            if i not in ids:
                ids[i] = len(out['positions_m'])
                out['positions_m'].append(list(mesh['positions_m'][i])); out['uvs'].append(list(mesh['uvs'][i]))
                out['weights'].append(dict(mesh['weights'][i]))
            new.append(ids[i])
        out['triangles'].append(new); out['corner_uvs'].append([list(u) for u in cuv])
    if '_normals' in mesh:
        back = {v: k for k, v in ids.items()}
        out['_normals'] = [mesh['_normals'][back[j]] for j in range(len(out['positions_m']))]
    return out


def coat(body, bones):
    """The coat above its waist seam, closed in front, long sleeves, its top a little under the
    neck joint; then cut in two: the blue body and sleeves, and the red cuffs at the wrists."""
    t = TAILORING['coat']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['waist_below_spine02']; hi = neck-t['top_below_neck']
    wrist = abs(bones['hand_l']['head_m'][0])-t['sleeve_short_of_wrist']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: wrist-v['p'][0], lambda v: wrist+v['p'][0]]
    whole = G._poly_shell(body, bones, 'coat_body', 'garment_upper__coat_blue_1812', fields, t['ease'],
                          [(lo, hi)], neck, None, smooth=(t['smoothing'], t['smoothing_min_ease']))
    loose = G._armpit_ease(whole, body, bones, t['armpit_extra'])
    cuff = wrist-t['cuff_depth']
    blue = _split(whole, lambda c: abs(c[0]) < cuff, 'coat_body', 'garment_upper__coat_blue_1812')
    red = _split(whole, lambda c: abs(c[0]) >= cuff, 'coat_cuffs_red', 'garment_upper__facings_red_1812')
    blue['receipt'] = dict(garment='blue coat body and sleeves, closed', armpit_points_eased=loose, waist_seam_y_m=lo,
                           top_y_m=hi, sleeve_end_x_m=wrist)
    red['receipt'] = dict(garment='red cuffs', from_x_m=cuff, to_x_m=wrist)
    return blue, red, lo


def _neck_loft(body, bones, name, material, ease, bottoms, tops, gap_deg, n, rows):
    """A band lofted round the neck's own sections between per-direction bottoms and tops,
    `ease` out, leaving out `gap_deg` either side of the front. Skinned to the neck."""
    pts, _jaw, (cx, cz) = M._neck_frame(body, bones)
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    def radius(k, y):
        dx, dz = dirs[k]
        slab = [p for p in pts if abs(p[1]-y) <= .007] or [p for p in pts if abs(p[1]-y) <= .02]
        need(bool(slab), f'no neck section for the {name}')
        return max((p[0]-cx)*dx+(p[2]-cz)*dz for p in slab)+ease
    keep = [k for k in range(n) if abs(((360.*k/n)+180.) % 360.-180.) >= gap_deg]
    out = empty(name, material)
    index = {}
    for r in range(rows):
        f = r/(rows-1)
        for k in keep:
            dx, dz = dirs[k]
            y = bottoms[k]+(tops[k]-bottoms[k])*f
            rr = radius(k, y)
            index[r, k] = len(out['positions_m'])
            out['positions_m'].append([cx+rr*dx, y, cz+rr*dz]); out['uvs'].append([k/n, f])
            out['weights'].append({'neck_01': 1.} if f > .3 else {'neck_01': .6+f, 'spine_03': .4-f})
    for r in range(rows-1):
        for k in keep:
            k2 = (k+1) % n
            if (r, k2) not in index:
                continue
            a, b, c, d = index[r, k], index[r, k2], index[r+1, k], index[r+1, k2]
            out['triangles'] += [[a, b, d], [a, d, c]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    return finish_edges(out, .0016)


def stock_and_collar(body, bones):
    """The black leather stock (the merchant's stock loft) and, outside it, the coat's red
    standing collar, open at the front where the stock shows, its top under the stock's."""
    t = TAILORING['collar']
    stock, (dirs, tops, _c) = M.stock(body, bones)
    stock['name'] = 'black_leather_stock'; stock['material'] = 'accessory__leather_stock_black'
    stock['receipt']['garment'] = 'black leather stock'
    neck = bones['neck_01']['head_m'][1]
    n = len(dirs)
    bottoms = [neck-t['bottom_below_neck']]*n
    collar_tops = [min(tops[k]-t['below_stock_top'], neck+t['back_above_neck']) for k in range(n)]
    collar = _neck_loft(body, bones, 'coat_collar_red', 'garment_upper__facings_red_1812', t['ease'], bottoms,
                        collar_tops, t['front_gap_deg'], n, t['rows'])
    collar['receipt'] = dict(garment='red standing collar', top_back_y_m=collar_tops[n//2], bottom_y_m=bottoms[0],
                             front_gap_deg=t['front_gap_deg'], ease_m=t['ease'])
    return stock, collar


def buttons(coat_mesh, bones, waist):
    """One row of white metal buttons down the closed front, skinned as the coat beneath."""
    t = TAILORING['buttons']
    neck = bones['neck_01']['head_m'][1]
    top = neck-t['below_collar']; bottom = waist+t['above_waist']
    out = empty('coat_buttons', 'accessory__white_metal_buttons')
    n = t['sides']
    for i in range(t['count']):
        y = top-(top-bottom)*i/(t['count']-1)
        z0, w = G._surface_sample(coat_mesh, 0., y)
        c = len(out['positions_m'])
        out['positions_m'].append([0., y, z0+t['standoff']+.0015]); out['uvs'].append([.5, .5]); out['weights'].append(w)
        for k in range(n):
            a = 2*math.pi*k/n
            x, yy = t['radius']*math.cos(a), y+t['radius']*math.sin(a)
            try:
                z, _ = G._surface_sample(coat_mesh, x, yy)
            except ValueError:
                z = z0
            out['positions_m'].append([x, yy, z+t['standoff']]); out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)])
            out['weights'].append(w)
        for k in range(n):
            out['triangles'].append([c, c+1+k, c+1+(k+1) % n])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='white metal coat buttons', count=t['count'], radius_m=t['radius'])
    return out


def _vertex_normals(mesh):
    acc = [[0., 0., 0.] for _ in mesh['positions_m']]
    P = mesh['positions_m']
    for f in mesh['triangles']:
        a, b, c = (P[i] for i in f)
        u = [b[k]-a[k] for k in range(3)]; v = [c[k]-a[k] for k in range(3)]
        n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        for i in f:
            for k in range(3):
                acc[i][k] += n[k]
    out = []
    for n in acc:
        length = math.hypot(*n)
        out.append([x/length for x in n] if length > 1e-15 else [0., 0., 1.])
    return out


def _on_garment(base, fields, name, material, offset):
    """A strip cut from a garment's own surface by `fields` and stood `offset` off it along
    the garment's normals: it lies on the garment wherever the garment goes, front, shoulder
    and back, and is skinned as the garment beneath it."""
    normals = _vertex_normals(base)
    out = empty(name, material); cache = {}
    P = base['positions_m']
    for face in base['triangles']:
        poly = [dict(p=P[i], uv=base['uvs'][i], w=base['weights'][i], n=normals[i], basis={i: 1.}) for i in face]
        for field in fields:
            poly = _clip(poly, field)
            if not poly:
                break
        if len(poly) < 3:
            continue
        ids = []
        for v in poly:
            length = math.hypot(*v['n']) or 1.
            p = [v['p'][a]+offset*v['n'][a]/length for a in range(3)]
            weights = G._skin4(dict(v['w']), 1.)
            key = (tuple(round(x, 12) for x in p), tuple(sorted(weights.items())))
            if key not in cache:
                cache[key] = len(out['positions_m'])
                out['positions_m'].append(p); out['uvs'].append(list(v['uv'])); out['weights'].append(weights)
            ids.append(cache[key])
        for i in range(1, len(ids)-1):
            tri = [ids[0], ids[i], ids[i+1]]
            if len(set(tri)) == 3:
                out['triangles'].append(tri); out['corner_uvs'].append([out['uvs'][k] for k in tri])
    need(bool(out['triangles']), f'empty strip {name}')
    return out


def crossbelts(coat_mesh, bones, waist):
    """Two white belts, each over one shoulder and down across the chest and the back to the
    other hip, crossing on the breast: strips of the coat's own surface, stood off it."""
    t = TAILORING['crossbelts']
    neck = bones['neck_01']['head_m'][1]
    top = neck-t['top_below_neck']
    half = t['width']/2
    out = []
    for sign, offset, label in ((-1, t['offsets'][0], 'bayonet'), (1, t['offsets'][1], 'cartridge')):
        # The belt from the shoulder at x = sign*shoulder_x to the hip at x = -sign*hip_x.
        x0, x1 = sign*t['shoulder_x'], -sign*t['hip_x']
        centre = lambda y, x0=x0, x1=x1: x0+(x1-x0)*(top-y)/(top-waist)
        fields = [lambda v, c=centre: v['p'][0]-(c(v['p'][1])-half), lambda v, c=centre: c(v['p'][1])+half-v['p'][0],
                  lambda v: v['p'][1]-waist]
        out.append(_on_garment(coat_mesh, fields, f'crossbelt_{label}', 'accessory__crossbelts_white', offset))
    merged = empty('crossbelts', 'accessory__crossbelts_white')
    for m in out:
        base = len(merged['positions_m'])
        for k in ('positions_m', 'uvs', 'weights', 'corner_uvs'):
            merged[k] += m[k]
        merged['triangles'] += [[i+base for i in f] for f in m['triangles']]
    merged = finish_edges(merged, .0018)
    merged['receipt'] = dict(garment='white crossbelts', width_m=t['width'], shoulder_x_m=t['shoulder_x'], hip_x_m=t['hip_x'],
                             top_y_m=top, offsets_m=list(t['offsets']))
    return merged


def _box(out, centre, size, rot_x_deg, weights):
    """An axis-aligned box (rotated about x), closed, with its own UVs."""
    cx, cy, cz = centre; sx, sy, sz = (s/2 for s in size)
    a = math.radians(rot_x_deg); ca, sa = math.cos(a), math.sin(a)
    corners = []
    for dx in (-sx, sx):
        for dy in (-sy, sy):
            for dz in (-sz, sz):
                y, z = dy*ca-dz*sa, dy*sa+dz*ca
                corners.append([cx+dx, cy+y, cz+z])
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for q in quads:
        base = len(out['positions_m'])
        for j, i in enumerate(q):
            out['positions_m'].append(list(corners[i])); out['uvs'].append([(0., 1., 1., 0.)[j], (0., 0., 1., 1.)[j]])
            out['weights'].append(dict(weights))
        for f in ([base, base+1, base+2], [base, base+2, base+3]):
            out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][i] for i in f])


def cartridge_box_and_scabbard(body, bones, waist):
    """A black cartridge box behind the right hip at the cartridge belt's end and a bayonet
    scabbard at the left hip at the other's, rigid on the pelvis, clear of the tails."""
    P = body['meshes'][0]['positions_m']
    tb = TAILORING['cartridge_box']; ts = TAILORING['scabbard']
    out = empty('cartridge_box_and_scabbard', 'accessory__cartridge_box_black')
    by = waist-tb['below_waist']-tb['height']/2
    back = min(p[2] for p in P if abs(p[1]-by) < .06 and abs(p[0]-tb['x']) < tb['width']/2 and p[2] < 0)
    tails_ease = TAILORING['tails']['ease']
    bz = back-tails_ease-tb['off_back']-tb['depth']/2
    _box(out, (tb['x'], by, bz), (tb['width'], tb['height'], tb['depth']), 0., {'pelvis': 1.})
    sy = waist-ts['below_waist']-ts['length']/2
    side = max(p[0] for p in P if abs(p[1]-(waist-.08)) < .05 and abs(p[2]-ts['back_z']) < .08 and p[0] > 0)
    sx = side+tails_ease+ts['off_side']+ts['thickness']/2
    _box(out, (sx, sy, ts['back_z']), (ts['thickness'], ts['length'], ts['width']), ts['tilt_deg'], {'pelvis': 1.})
    out['receipt'] = dict(garment='cartridge box and bayonet scabbard', box_centre_m=[tb['x'], by, bz],
                          scabbard_centre_m=[sx, sy, ts['back_z']], skinning='pelvis, rigid')
    return out


def overalls(body, bones, height):
    """White linen overalls on the shared workwear shell, to the instep (the merchant's cut)."""
    t = TAILORING['overalls']
    recipe = dict(waist_height_fraction=t['waist_height_fraction'], shirt_hem_fraction=.565,
                  workwear_tailoring_v5=dict(waistcoat_closed_front_torso_fraction=.4,
                                             trouser_cuff_radius_ratio=t['cuff_radius_ratio'],
                                             trouser_added_section_ease_m=t['added_section_ease'],
                                             trouser_thigh_transition_fraction=t['thigh_transition_fraction']))
    out = garment_shell(body['meshes'][0], 'trousers', t['ease'], recipe, bones, height)
    out = G._lengthen_hems(out, bones, t)
    out = finish_edges(out, .0015)
    out['name'] = 'linen_overalls'; out['material'] = 'garment_lower__overalls_linen_1812'
    for k in ('source_basis', 'source_triangle_indices'):
        out.pop(k, None)
    return out


def overalls_waistband(body, bones, height, coat_seam):
    """The overalls rise high to the waist, under the short-fronted coat: the shared trouser
    shell stops where the legs' skin ends, so a band of the body's own surface, offset just
    beyond it, carries them up under the coat's waist seam."""
    t = TAILORING['overalls']
    neck = bones['neck_01']['head_m'][1]
    lo = t['waist_height_fraction']*height-t['band_below_waist']; hi = coat_seam+t['band_above_coat_seam']
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: .35-G._arm_mass(v),
              lambda v: .235-v['p'][0], lambda v: .235+v['p'][0]]
    out = G._poly_shell(body, bones, 'overalls_waistband', 'garment_lower__overalls_linen_1812', fields, t['band_ease'],
                        [(lo, hi)], neck, None)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='overalls, waist band', bottom_y_m=lo, top_y_m=hi, ease_m=t['band_ease'])
    return out


def cap(body, bones, lod=0):
    """A tall black felt cap: a cylinder seated round the skull's own section, flat-topped,
    with a short leather peak drooping over the brow, and a white feather standing at the
    front left (a separate mesh). Both rigid on the head bone."""
    t = TAILORING['cap']
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
    # A cylinder: the seat's section rounded towards its mean radius.
    mean = sum(seat_r)/n
    seat_r = [max(r, .5*r+.5*mean)+.002 for r in seat_r]
    out = empty('headwear_felt_cap', 'headwear__felt_cap_black')
    def ring(radii, y_of_k):
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            ids.append(len(out['positions_m']))
            out['positions_m'].append([cx+radii[k]*dx, y_of_k(k), cz+radii[k]*dz])
            out['uvs'].append([k/n, 0.]); out['weights'].append({'head': 1.})
        return ids
    th = t['thickness']; H = t['height']
    inner = ring([r-th for r in seat_r], lambda k: seat+.002)
    rim = ring(seat_r, lambda k: seat)
    rows = [ring([r*(1+(t['flare']-1)*h) for r in seat_r], (lambda yy: (lambda k: yy))(seat+H*h)) for h in (.25, .5, .75, 1.)]
    rings = [inner, rim]+rows
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    apex = len(out['positions_m'])
    out['positions_m'].append([cx, seat+H, cz]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([rows[-1][k], apex, rows[-1][(k+1) % n]])
    lining_y = top+.004
    lining = ring([r*.55 for r in seat_r], lambda k: lining_y)
    for k in range(n):
        a, b, c, d = inner[k], inner[(k+1) % n], lining[(k+1) % n], lining[k]
        out['triangles'] += [[a, b, c], [a, c, d]]
    lc = len(out['positions_m']); out['positions_m'].append([cx, lining_y+.004, cz]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([lining[k], lining[(k+1) % n], lc])
    # The peak: a half-moon over the front half of the rim, drooping to its edge.
    front = [k for k, (dx, dz) in enumerate(dirs) if dz > .05]
    front.sort(key=lambda k: math.atan2(dirs[k][0], dirs[k][1]))
    def reach(k):
        return t['peak']*max(0., dirs[k][1])**.7
    upper = []; lower = []; edge = []
    for k in front:
        dx, dz = dirs[k]; r = seat_r[k]
        for lst, rr, yy in ((upper, r, seat+.002), (edge, r+reach(k), seat-t['peak_droop']*max(0., dz)), (lower, r, seat-.002)):
            lst.append(len(out['positions_m']))
            out['positions_m'].append([cx+rr*dx, yy, cz+rr*dz]); out['uvs'].append([k/n, .5]); out['weights'].append({'head': 1.})
    for i in range(len(front)-1):
        a, b, c, d = upper[i], upper[i+1], edge[i+1], edge[i]
        out['triangles'] += [[a, c, b], [a, d, c]]
        a, b, c, d = lower[i], lower[i+1], edge[i+1], edge[i]
        out['triangles'] += [[a, b, c], [a, c, d]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='black felt cap with a leather peak', seat_y_m=seat, height_m=H, peak_m=t['peak'],
                          head_bone='head', separate_mesh=True, lift='rigid on the head bone')
    # The feather: a slim tapering spindle standing up the front left of the cap.
    plume = empty('headwear_plume', 'headwear__plume_white')
    a = math.radians(t['plume_deg']); k0 = min(range(n), key=lambda k: abs(math.atan2(dirs[k][0], dirs[k][1])-a))
    dx, dz = math.sin(a), math.cos(a)
    bx, bz = cx+(seat_r[k0]*t['flare']+.004)*dx, cz+(seat_r[k0]*t['flare']+.004)*dz
    y0 = seat+H-.05; m = 8; levels = 7
    ids = []
    for i in range(levels):
        f = i/(levels-1)
        rad = t['plume_radius']*math.sin(math.pi*min(.98, .15+.85*f))**.8*(1-.6*f)
        lean = .015*f*f
        ring_ids = []
        for j in range(m):
            th2 = 2*math.pi*j/m
            ring_ids.append(len(plume['positions_m']))
            plume['positions_m'].append([bx+lean*dx+rad*math.cos(th2), y0+t['plume_height']*f, bz+lean*dz+rad*math.sin(th2)])
            plume['uvs'].append([j/m, f]); plume['weights'].append({'head': 1.})
        ids.append(ring_ids)
    for i in range(levels-1):
        for j in range(m):
            a1, b1, c1, d1 = ids[i][j], ids[i][(j+1) % m], ids[i+1][(j+1) % m], ids[i+1][j]
            plume['triangles'] += [[a1, c1, b1], [a1, d1, c1]]
    tip = len(plume['positions_m']); plume['positions_m'].append([bx+.015*dx, y0+t['plume_height']+.012, bz+.015*dz])
    plume['uvs'].append([.5, 1.]); plume['weights'].append({'head': 1.})
    for j in range(m):
        plume['triangles'].append([ids[-1][j], ids[-1][(j+1) % m], tip])
    base = len(plume['positions_m']); plume['positions_m'].append([bx, y0-.004, bz]); plume['uvs'].append([.5, 0.]); plume['weights'].append({'head': 1.})
    for j in range(m):
        plume['triangles'].append([ids[0][(j+1) % m], ids[0][j], base])
    plume['corner_uvs'] = [[plume['uvs'][i] for i in f] for f in plume['triangles']]
    plume['receipt'] = dict(garment='white feather', height_m=t['plume_height'], head_bone='head')
    return out, plume


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    blue, red, waist = coat(body, bones)
    stock, collar = stock_and_collar(body, bones)
    tails = M.tails(body, bones, blue, waist, t=TAILORING['tails'], name='coat_tails', material='garment_upper__coat_blue_1812',
                    garment='coat tails, cut away in front, to mid-thigh')
    hat, plume = cap(body, bones)
    parts = [stock, collar, finish_edges(blue, .0018), finish_edges(red, .0018), tails, buttons(blue, bones, waist),
             crossbelts(blue, bones, waist), cartridge_box_and_scabbard(body, bones, waist), overalls(body, bones, height),
             overalls_waistband(body, bones, height, waist),
             hat, plume]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_soldier_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths and colours are reconstructed; no picture is of the Fort Dearborn garrison',
                             'No cloth simulation: shells and tails follow the body bones (each tail goes with its own leg)',
                             'No musket, no lace on the coat front, no cap plate or cockade, no breast plate on the belts',
                             'Cap and feather rigid on the head bone'])


def prepare_soldier_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3451; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('soldier_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_soldier_1812.py',
         'unsupported soldier component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'soldier assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1812-08-14' and recipe.get('grade') == 'reconstructed',
         'soldier scene/appearance grade changed')
    need(spec.get('tailoring') == json.loads(json.dumps(TAILORING)), 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed soldier body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'soldier components require the declared liberty')
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
