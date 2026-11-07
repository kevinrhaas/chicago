# SPDX-License-Identifier: GPL-3.0-or-later
"""An 1835 labourer's working dress on the shared portable male rig (T-3450).

First worn by Patrick Mahoney (reconstructed), a labourer of the South Division in the
Chicago of 1835. The pieces, read from the period pictures in the recipe
(data/humans/recipes/labourer_1835.json):

  shirt        unbleached linen or cotton, worn without a coat: full sleeves gathered to a
               cuff at the wrist, open at the throat (Mount's Raffle, 1837; Mount's Cider
               Making, 1840-41; Weir's Wood Sawyer, 1842)
  neckerchief  a red cotton kerchief knotted round the neck over the shirt collar (the
               Raffle; Cider Making)
  braces       two straps from the trousers' waistband up over the shoulders and down the
               back, seen inside the open waistcoat (Cider Making, where a man in his shirt wears them)
  waistcoat    dark green wool, worn open over the shirt, cut straight at the waist (Cider
               Making; the Wood Sawyer wears his open)
  trousers     brown, full and straight to the instep (Cider Making)
  slouch hat   a drab felt hat with a low round crown and a broad soft brim, drooping fore
               and aft (the Raffle), rigid on the head bone and a mesh of its own

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with its T-3450 supplement. The source anatomy is never changed:
every piece is a shell offset from the body's own triangles (its UVs and skin weights
carried) or a loft round the body's own cross-sections, skinned to the body's own bones.
Reuses the 1904 gentleman's and the 1835 merchant's helpers.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_labourer_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_period_wardrobe import finish_edges
from human_workwear_fit import garment_shell
import human_gentleman_1904 as G
import human_merchant_1835 as M

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'labourer_1835_v1'
RECIPE = 'data/humans/recipes/labourer_1835.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=dict(ease=.008, waist_below_spine02=.14, collar_above_neck=.014, throat_v_below_neck=.10, throat_v_half_width=.034,
               cuff_short_of_wrist=.014, sleeve_fullness=.024, smoothing=90, sleeve_gather=.06, armpit_extra=.004),
    neckerchief=dict(ease=.014, bottom_below_neck=.030, back_bottom_below_neck=.004, height=.034, segments=36, rows=4),
    braces=dict(ease=.015, width=.024, x_at_waist=.060, x_at_top=.086, below_trouser_waist=.030, straight_above_below_neck=.035,
                over_shoulder_above_neck=.06),
    waistcoat=dict(ease=.022, armpit_extra=.008, hem_below_spine02=.105, top_below_neck=.020,
                   opening_half_width_hem=.088, opening_half_width_top=.102),
    trousers=dict(ease=.013, waist_height_fraction=.585, cuff_radius_ratio=.92, added_section_ease=.014,
                  thigh_transition_fraction=.65, hem_front_y=.068, hem_back_y=.036),
    slouch_hat=dict(seat_below_top=.072, ease=.008, crown_height=.098, brim=.066, droop=.020, side_lift=.006,
                    thickness=.005),
)

MATERIALS = {
    'garment_upper__shirt_unbleached_1835': {'base_color_linear': [.62, .58, .49, 1], 'roughness': .86},
    'garment_outer__waistcoat_green_1835': {'base_color_linear': [.030, .052, .036, 1], 'roughness': .86},
    'garment_lower__trousers_brown_1835': {'base_color_linear': [.15, .10, .058, 1], 'roughness': .92},
    'accessory__neckerchief_red': {'base_color_linear': [.36, .045, .030, 1], 'roughness': .8},
    'accessory__braces_brown': {'base_color_linear': [.085, .055, .032, 1], 'roughness': .7},
    'headwear__slouch_hat_drab': {'base_color_linear': [.30, .24, .15, 1], 'roughness': .9},
    'footwear__brown_boots_1835': {'base_color_linear': [.040, .025, .015, 1], 'roughness': .55},
}
SHOE_MATERIAL = 'footwear__brown_boots_1835'
WEAVE_MATERIAL = 'garment_upper__shirt_unbleached_1835'


def _arm_share(w):
    return math.fsum(x for b, x in w.items() if b.startswith(('upperarm', 'lowerarm')))


def shirt(body, bones):
    """The whole shirt, worn without a coat: the body's own surface from below the waist
    (tucked into the trousers) to a low collar band, open in a short V at the throat; full
    sleeves standing off the arm and gathered back to the arm at the cuff."""
    t = TAILORING['shirt']
    neck = bones['neck_01']['head_m'][1]; spine = bones['spine_02']['head_m'][1]
    lo = spine-t['waist_below_spine02']; hi = neck+t['collar_above_neck']
    cuff = abs(bones['hand_l']['head_m'][0])-t['cuff_short_of_wrist']
    shoulder = abs(bones['upperarm_l']['head_m'][0])
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: cuff-v['p'][0], lambda v: cuff+v['p'][0]]
    vb = neck-t['throat_v_below_neck']
    args = (body, bones, 'shirt_full_sleeves', 'garment_upper__shirt_unbleached_1835', fields, t['ease'],
            [(lo, hi)], neck, G._v_pieces(vb, t['throat_v_half_width'], hi))
    out = G._poly_shell(*args)
    # The sleeves hang smooth over the arm's muscles: the same shell smoothed, taken only
    # on the arms (the body stays the plain offset, under the waistcoat and braces).
    smooth = G._poly_shell(*args, smooth=(t['smoothing'], t['ease']))
    need(len(smooth['positions_m']) == len(out['positions_m']), 'smoothed shirt lost its topology')
    for i, (p, q, w) in enumerate(zip(out['positions_m'], smooth['positions_m'], out['weights'])):
        k = _arm_share(w)*min(1., max(0., (abs(p[0])-shoulder)/.06))
        if k > 0:
            out['positions_m'][i] = [a+(b-a)*k for a, b in zip(p, q)]
    G._armpit_ease(out, body, bones, t['armpit_extra'])
    # Full sleeves: arm-skinned points stand further off the arm, rising from the shoulder
    # and gathered back to the arm over the last few centimetres before the cuff.
    full = 0
    for i, (p, w) in enumerate(zip(out['positions_m'], out['weights'])):
        arm = _arm_share(w)
        x = abs(p[0])
        rise = min(1., max(0., (x-shoulder-.02)/.08)); gather = min(1., max(0., (cuff-x)/t['sleeve_gather']))
        g = arm*rise*gather
        if g <= 0:
            continue
        n = out['_normals'][i]
        out['positions_m'][i] = [p[a]+t['sleeve_fullness']*g*n[a] for a in range(3)]
        full += 1
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='unbleached shirt, full sleeves, open throat', waist_y_m=lo, collar_top_y_m=hi,
                          throat_v_bottom_y_m=vb, cuff_x_m=cuff, ease_m=t['ease'], sleeve_points_eased=full,
                          sleeve_fullness_m=t['sleeve_fullness'], source_body_mutated=False)
    return out


def neckerchief(body, bones):
    """A cotton kerchief knotted round the neck: a low band lofted round the neck's own
    sections over the shirt's collar band, lower in front than behind. Skinned to the neck."""
    t = TAILORING['neckerchief']
    neck = bones['neck_01']['head_m'][1]
    pts, _jaw, (cx, cz) = M._neck_frame(body, bones)
    n = t['segments']
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    def radius(k, y):
        dx, dz = dirs[k]
        slab = [p for p in pts if abs(p[1]-y) <= .007] or [p for p in pts if abs(p[1]-y) <= .02]
        need(bool(slab), 'no neck section for the neckerchief')
        return max((p[0]-cx)*dx+(p[2]-cz)*dz for p in slab)+t['ease']
    bottoms = [neck-t['bottom_below_neck']+(t['bottom_below_neck']-t['back_bottom_below_neck'])*(1-dz)/2 for dx, dz in dirs]
    out = empty('neckerchief_red', 'accessory__neckerchief_red')
    rows = t['rows']
    for r in range(rows):
        f = r/(rows-1)
        for k, (dx, dz) in enumerate(dirs):
            y = bottoms[k]+t['height']*f
            rr = radius(k, y)+.002*math.sin(math.pi*f)
            out['positions_m'].append([cx+rr*dx, y, cz+rr*dz]); out['uvs'].append([k/n, f])
            out['weights'].append({'neck_01': 1.} if f > .3 else {'neck_01': .6+f, 'spine_03': .4-f})
    for r in range(rows-1):
        for k in range(n):
            a = r*n+k; b = r*n+(k+1) % n; c = a+n; d = b+n
            out['triangles'] += [[a, b, d], [a, d, c]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='red cotton neckerchief', bottom_front_y_m=bottoms[0], top_back_y_m=bottoms[n//2]+t['height'],
                          ease_m=t['ease'], skinning='neck_01 (spine_03 at the foot)')
    return out


def braces(body, bones, trouser_waist):
    """Two straps from the trousers' waistband up the chest, over the shoulders and straight
    down the back to the waistband again, seen in front inside the open waistcoat."""
    t = TAILORING['braces']
    neck = bones['neck_01']['head_m'][1]
    lo = trouser_waist-t['below_trouser_waist']; turn = neck-t['straight_above_below_neck']
    half = t['width']/2
    slope = (t['x_at_top']-t['x_at_waist'])/(turn-lo)
    centre = lambda y: t['x_at_waist']+slope*(min(y, turn)-lo)
    fields = [lambda v: v['p'][1]-lo, lambda v: neck+t['over_shoulder_above_neck']-v['p'][1]]
    def pieces(poly):
        left = G._clip(G._clip(poly, lambda v: v['p'][0]-(centre(v['p'][1])-half)), lambda v: centre(v['p'][1])+half-v['p'][0])
        right = G._clip(G._clip(poly, lambda v: -v['p'][0]-(centre(v['p'][1])-half)), lambda v: centre(v['p'][1])+half+v['p'][0])
        return [left, right]
    out = G._poly_shell(body, bones, 'braces', 'accessory__braces_brown', fields, t['ease'], [], neck, pieces,
                        smooth=(8, t['ease']))
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='braces, front and back straps over the shoulders', bottom_y_m=lo, straight_above_y_m=turn,
                          width_m=t['width'], x_m=[t['x_at_waist'], t['x_at_top']], ease_m=t['ease'])
    return out


def waistcoat(body, bones):
    """The waistcoat, worn open: back and two fronts, the fronts falling apart from hem to
    neck so the shirt and braces show between them; cut straight at the waist."""
    t = TAILORING['waistcoat']
    spine = bones['spine_02']['head_m'][1]; neck = bones['neck_01']['head_m'][1]
    lo = spine-t['hem_below_spine02']; hi = neck-t['top_below_neck']
    slope = (t['opening_half_width_top']-t['opening_half_width_hem'])/(hi-lo)
    gap = lambda y: t['opening_half_width_hem']+slope*(y-lo)
    fields = [lambda v: v['p'][1]-lo, lambda v: hi-v['p'][1], lambda v: .35-G._arm_mass(v),
              lambda v: .235-v['p'][0], lambda v: .235+v['p'][0]]
    def pieces(poly):
        back = G._clip(poly, lambda v: -v['p'][2])
        front = G._clip(poly, lambda v: v['p'][2])
        left = G._clip(front, lambda v: v['p'][0]-gap(v['p'][1]))
        right = G._clip(front, lambda v: -v['p'][0]-gap(v['p'][1]))
        return [back, left, right]
    out = G._poly_shell(body, bones, 'waistcoat_open', 'garment_outer__waistcoat_green_1835', fields, t['ease'],
                        [(lo, hi)], neck, pieces, smooth=(12, t['ease']))
    G._armpit_ease(out, body, bones, t['armpit_extra'])
    out = finish_edges(out, .0016)
    out['receipt'] = dict(garment='green waistcoat worn open', hem_y_m=lo, top_y_m=hi,
                          opening_half_width_m=[t['opening_half_width_hem'], t['opening_half_width_top']])
    return out


def trousers(body, bones, height):
    """Full trousers on the shared workwear shell, lengthened to the instep (the merchant's cut)."""
    t = TAILORING['trousers']
    recipe = dict(waist_height_fraction=t['waist_height_fraction'], shirt_hem_fraction=.565,
                  workwear_tailoring_v5=dict(waistcoat_closed_front_torso_fraction=.4,
                                             trouser_cuff_radius_ratio=t['cuff_radius_ratio'],
                                             trouser_added_section_ease_m=t['added_section_ease'],
                                             trouser_thigh_transition_fraction=t['thigh_transition_fraction']))
    out = garment_shell(body['meshes'][0], 'trousers', t['ease'], recipe, bones, height)
    out = G._lengthen_hems(out, bones, t)
    out = finish_edges(out, .0015)
    out['name'] = 'full_trousers'; out['material'] = 'garment_lower__trousers_brown_1835'
    for k in ('source_basis', 'source_triangle_indices'):
        out.pop(k, None)
    return out


def slouch_hat(body, bones, lod=0):
    """A drab felt slouch hat seated round the skull's own section: a low round crown and a
    broad soft brim that droops fore and aft and lifts a little at the sides. Rigid on the
    head bone, a separate mesh."""
    t = TAILORING['slouch_hat']
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
    # The crown must clear the skull above the seat: each ring at least the head's own
    # section there plus the ease.
    H = t['crown_height']
    out = empty('headwear_slouch_hat', 'headwear__slouch_hat_drab')
    def ring(radii, y_of_k):
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            ids.append(len(out['positions_m']))
            out['positions_m'].append([cx+radii[k]*dx, y_of_k(k), cz+radii[k]*dz])
            out['uvs'].append([k/n, 0.]); out['weights'].append({'head': 1.})
        return ids
    side = [abs(dx) for dx, dz in dirs]
    th = t['thickness']; B = t['brim']
    fall = [-t['droop']*(1-s)**2+t['side_lift']*s*s for s in side]
    inner = ring([r-th for r in seat_r], lambda k: seat+.002)
    mid_under = ring([r+B*.5 for r in seat_r], lambda k: seat-.002+fall[k]*.3)
    under_out = ring([r+B for r in seat_r], lambda k: seat-.002+fall[k])
    edge = ring([r+B+.004 for r in seat_r], lambda k: seat+fall[k]+th*.5-.002)
    over_out = ring([r+B for r in seat_r], lambda k: seat+th+fall[k])
    mid_over = ring([r+B*.5 for r in seat_r], lambda k: seat+th+fall[k]*.3)
    profile = [(0., 1.01), (.25, 1.02), (.55, 1.0), (.8, .92), (.95, .74), (1., .45)]
    def clear(h, f):
        y = seat+th+H*h
        sl = [p for p in head_pts if abs(p[1]-y) <= .006]
        return [max(r*f, (max(((p[0]-cx)*dx+(p[2]-cz)*dz for p in sl), default=0.)+.006)) for r, (dx, dz) in zip(seat_r, dirs)]
    crown = [ring(clear(h, f), (lambda yy: (lambda k: yy))(seat+th+H*h)) for h, f in profile]
    rings = [inner, mid_under, under_out, edge, over_out, mid_over]+crown
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    apex = len(out['positions_m'])
    out['positions_m'].append([cx, seat+th+H+.006, cz]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
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
    out['receipt'] = dict(garment='drab felt slouch hat', seat_y_m=seat, crown_height_m=H, brim_m=B, droop_m=t['droop'],
                          head_bone='head', separate_mesh=True, lift='rigid on the head bone')
    return out


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    trouser_waist = TAILORING['trousers']['waist_height_fraction']*height
    parts = [shirt(body, bones), neckerchief(body, bones), braces(body, bones, trouser_waist), waistcoat(body, bones),
             trousers(body, bones, height), slouch_hat(body, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_labourer_1835_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; no picture is of Mahoney or of Chicago',
                             'No cloth simulation: shells follow the body bones',
                             'Braces run straight down the back (an H), under the waistcoat',
                             'Hat rigid on the head bone'])


def prepare_labourer_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3450; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('labourer_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_labourer_1835.py',
         'unsupported labourer component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'labourer assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1835-07-01' and recipe.get('grade') == 'reconstructed',
         'labourer scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed labourer body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'labourer components require the declared liberty')
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
