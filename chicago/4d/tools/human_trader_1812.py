# SPDX-License-Identifier: GPL-3.0-or-later
"""A prosperous trader about 1810, on the shared portable male rig.

An anonymous settled civilian man of the Chicago of 1812: the dress a trader of John
Kinzie's standing would wear, and with him Charles Lee, Thomas Burns and the other settled
men; Captain William Wells too on the 14th of August (his own dress of the 15th, "dressed
like an Indian", is not this). The asset is a ROLE, never a person: each man wears it with
his own face, height, build and colouring (the variation kit and human-looks.js). The
pieces, read from the period pictures in the recipe (data/humans/recipes/trader_1812.json;
docs/RESEARCH/people-1812-3461/dress.json, role 'Prosperous trader / merchant about 1810'):

  shirt        white linen where it shows: the front in the waistcoat's opening, the cuffs,
               and the collar's two points standing up at the cheeks above the neckcloth
  neckcloth    white, wound high round the neck and tied in front (Peale's Robinson, 1811)
  waistcoat    yellow, single-breasted, cut straight across at the waist below the coat's
               square-cut front, with a turned collar (Robinson, 1811; the Pixler father)
  tailcoat     dark green wool, double-breasted and cut square across the front at the
               waist, lapels and a collar standing high behind, tails to the knee, gilt
               buttons (Robinson's green coat; Krimmel's green tailcoat of 1811-13; the
               Coutts coat and the Met's coat of about 1815 for the cut)
  breeches     buff, to below the knee and into the boots (Krimmel)
  top boots    black, to just below the knee, with turned-down tops of tan leather
               (Krimmel's 'top boots'; the coachman's boot shaft)
  round hat    black felt, its crown tapering a little to a flat top, a moderate brim
               curled at the sides: the round hat of 1810, lower and narrower-topped than
               the 1835 top hat (Krimmel's tall hat; dress.json 'tall round hat with a
               moderate brim'). Rigid on the head bone and a mesh of its own

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 (supplement proposed in docs/RESEARCH/people-1812-dress/
officers-traders.md). The source anatomy is never changed. Reuses the 1835 merchant's
garment builders and the 1904 coachman's breeches and boot shafts by import, lending them
this outfit's measures only for the call.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_trader_assembly() (the recipe's `role_1812`) and makes the four LODs.
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

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'trader_1812_v1'
RECIPE = 'data/humans/recipes/trader_1812.json'
LIBERTY = 'L-human-modular-dress-1789'
PERSON = 'anonymous_trader_1812'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=dict(ease=.006, waist_below_spine02=.115, top_below_neck=.036, cuff_beyond_coat=.012),
    neckcloth=dict(ease=.012, bottom_below_neck=.040, back_bottom_below_neck=.004, back_above_neck=.040, jaw_clearance=.005,
                   segments=40, rows=7),
    knot=dict(width=.058, height=.032, depth=.018, below_top=.020, standoff=.004),
    collar_points=dict(inner_deg=20., outer_deg=50., rise=.036, tip_out=.012, standoff=.006),
    waistcoat=dict(ease=.016, armpit_extra=.008, hem_below_spine02=.088, top_below_neck=.016,
                   v_bottom_above_spine02=.275, v_half_width_top=.040, roll_width=.018, roll_notch=.85, front_only_x=.16),
    coat=dict(ease=.022, armpit_extra=.022, sleeve_short_of_wrist=.022, collar_above_neck=.048, waist_below_spine02=-.008,
              roll_above_spine02=.150, v_half_width_top=.082, lapel_width=.056, lapel_notch=.78, lapel_top_above_neck=-.024),
    tails=dict(hem_y=.520, ease=.020, edge_top_deg=76., edge_hem_deg=124., vent_deg=3., segments=22, rows=13),
    buttons=dict(radius=.0090, rows=3, spacing=.042, x=.070, below_roll=.016, standoff=.0025, sides=10),
    breeches=dict(ease=.012, waist_height_fraction=.585, bottom_y=.400, thigh_fullness=.014, smoothing=60),
    boots=dict(bottom_y=.080, top_y=.430, ease_bottom=.006, ease_top=.018, segments=28, rows=9),
    boot_tops=dict(rows=2, extra_ease=.004),
    round_hat=dict(seat_below_top=.084, ease=.007, crown_height=.125, crown_flare=.85, brim_side=.050, brim_fore=.060,
                   brim_curl=.020, thickness=.004),
)

MATERIALS = {
    'garment_upper__shirt_linen_1810': {'base_color_linear': [.80, .80, .78, 1], 'roughness': .78},
    'garment_outer__tailcoat_green_1810': {'base_color_linear': [.018, .034, .022, 1], 'roughness': .84},
    'garment_outer__waistcoat_yellow_1810': {'base_color_linear': [.52, .40, .14, 1], 'roughness': .8},
    'garment_lower__breeches_buff_1810': {'base_color_linear': [.50, .40, .25, 1], 'roughness': .86},
    'accessory__gilt_buttons_1810': {'base_color_linear': [.45, .32, .11, 1], 'roughness': .35},
    'footwear__black_top_boots_1810': {'base_color_linear': [.011, .010, .010, 1], 'roughness': .34},
    'footwear__boot_tops_tan_1810': {'base_color_linear': [.30, .18, .08, 1], 'roughness': .55},
    'headwear__round_hat_black_1810': {'base_color_linear': [.014, .013, .013, 1], 'roughness': .6},
}
SHOE_MATERIAL = 'footwear__black_top_boots_1810'
WEAVE_MATERIAL = 'garment_upper__shirt_linen_1810'
SHIRT = 'garment_upper__shirt_linen_1810'


def _renamed(mesh, name, material, garment):
    mesh['name'] = name; mesh['material'] = material
    mesh['receipt'] = dict(mesh.get('receipt', {}), garment=garment)
    return mesh


def _lent_merchant():
    t = TAILORING
    return C._lent(M, shirt=t['shirt'], stock=t['neckcloth'], collar_points=t['collar_points'], waistcoat=t['waistcoat'],
                   coat=t['coat'], tails=t['tails'], buttons=t['buttons'], top_hat=t['round_hat'])


def knot(stock_mesh, bones):
    """The neckcloth's tie in front: a small flattened lump on the cloth below the chin,
    skinned to the neck."""
    t = TAILORING['knot']
    top = stock_mesh['receipt']['top_front_y_m']
    y0 = top-t['below_top']
    z0, _w = G._surface_sample(stock_mesh, 0., y0)
    out = empty('neckcloth_knot', SHIRT)
    rows, cols = 6, 10
    ids = []
    for r in range(rows+1):
        v = r/rows; a = math.pi*v
        ring = []
        for c in range(cols):
            b = 2*math.pi*c/cols
            x = t['width']/2*math.sin(a)*math.cos(b)
            y = y0+t['height']/2*math.cos(a)
            z = z0+t['standoff']+t['depth']/2*(1+math.sin(a)*math.sin(b))*.9
            ring.append(len(out['positions_m'])); out['positions_m'].append([x, y, z])
            out['uvs'].append([c/cols, v]); out['weights'].append({'neck_01': 1.})
        ids.append(ring)
    for r in range(rows):
        for c in range(cols):
            a, b, cc, d = ids[r][c], ids[r][(c+1) % cols], ids[r+1][(c+1) % cols], ids[r+1][c]
            for f in ([a, b, cc], [a, cc, d]):
                if len({tuple(out['positions_m'][i]) for i in f}) == 3:
                    out['triangles'].append(f)
    P = out['positions_m']
    cz = z0+t['standoff']+t['depth']*.45
    for i, f in enumerate(out['triangles']):
        a, b, c = (P[j] for j in f)
        n = [(b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]), (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
             (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])]
        m = [(a[k]+b[k]+c[k])/3 for k in range(3)]
        if n[0]*m[0]+n[1]*(m[1]-y0)+n[2]*(m[2]-cz) < 0:
            out['triangles'][i] = [f[0], f[2], f[1]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='neckcloth tie in front', centre_y_m=y0, width_m=t['width'])
    return out


def boots(body, bones):
    """The coachman's plain boot shafts to below the knee, their top band in tan: the
    turned-down tops of a pair of top boots."""
    t = TAILORING['boot_tops']
    with C._lent(C, boots=TAILORING['boots']):
        shafts = C.top_boots(body, bones)
    b = TAILORING['boots']
    top = b['top_y']
    # Cut on a ring of the shaft, so each band's quads go whole to one side.
    cut = top-(b['top_y']-b['bottom_y'])*t['rows']/(b['rows']-1)
    black = S._split(shafts, lambda c: c[1] < cut, 'top_boot_shafts', SHOE_MATERIAL)
    tan = S._split(shafts, lambda c: c[1] >= cut, 'top_boot_tops_tan', 'footwear__boot_tops_tan_1810')
    # The turned-down top stands a little proud of the shaft below it.
    for side in ('l', 'r'):
        cx = bones[f'calf_{side}']['head_m'][0]; cz = bones[f'calf_{side}']['head_m'][2]
        for p in tan['positions_m']:
            if (p[0] > 0) == (cx > 0):
                d = math.hypot(p[0]-cx, p[2]-cz) or 1.
                f = min(1., max(0., (p[1]-cut)/.012))
                p[0] += t['extra_ease']*f*(p[0]-cx)/d; p[2] += t['extra_ease']*f*(p[2]-cz)/d
    black['receipt'] = dict(shafts['receipt'], garment='black top boots to below the knee')
    tan['receipt'] = dict(garment='turned-down tan boot tops', depth_m=top-cut, top_y_m=top)
    return black, tan


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    t = TAILORING
    with _lent_merchant():
        shirt = _renamed(M.shirt(body, bones), 'shirt_front_and_cuffs', SHIRT, 'white linen shirt, front and cuffs')
        cloth, frame = M.stock(body, bones)
        cloth = _renamed(cloth, 'white_neckcloth', SHIRT, 'white neckcloth wound high')
        points = _renamed(M.collar_points(body, bones, cloth, frame), 'shirt_collar_points', SHIRT, 'shirt collar points')
        vest, vroll = M.waistcoat(body, bones)
        vest = _renamed(finish_edges(vest, .0015), 'waistcoat_yellow', 'garment_outer__waistcoat_yellow_1810',
                        'yellow single-breasted waistcoat, straight at the waist')
        vest_roll = M.rolled_edges(vest, vroll, 'waistcoat_collar', 'garment_outer__waistcoat_yellow_1810',
                                   t['waistcoat']['roll_width'], t['waistcoat']['roll_notch'], t['waistcoat']['v_half_width_top'],
                                   top_gap=.002, standoff=.0025)
        coat, roll = M.coat_body(body, bones)
        coat = _renamed(finish_edges(coat, .0018), 'tailcoat_body', 'garment_outer__tailcoat_green_1810',
                        'dark green tailcoat body and sleeves, cut square at the waist')
        c = t['coat']
        lapels = M.rolled_edges(coat, roll, 'tailcoat_lapels', 'garment_outer__tailcoat_green_1810', c['lapel_width'],
                                c['lapel_notch'], c['v_half_width_top'], stop=bones['neck_01']['head_m'][1]+c['lapel_top_above_neck'])
        tails = M.tails(body, bones, coat, roll[0], name='tailcoat_tails', material='garment_outer__tailcoat_green_1810',
                        garment='tailcoat tails to the knee')
        buttons = _renamed(M.buttons(coat, roll), 'tailcoat_buttons', 'accessory__gilt_buttons_1810', 'gilt coat buttons')
        hat = _renamed(M.top_hat(body, bones, lod=1), 'headwear_round_hat', 'headwear__round_hat_black_1810',
                       'black felt round hat, the crown tapering a little, a moderate brim')
    with C._lent(C, breeches=t['breeches']):
        breeches = _renamed(C.breeches(body, bones, height), 'buff_breeches', 'garment_lower__breeches_buff_1810',
                            'buff breeches to below the knee, into the boots')
    black, tan = boots(body, bones)
    parts = [shirt, points, cloth, knot(cloth, bones), vest, vest_roll, coat, lapels, tails, buttons, breeches, black, tan, hat]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_trader_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; no picture is of Kinzie or of Chicago',
                             'No cloth simulation: shells and tails follow the body bones (each tail goes with its own leg)',
                             'No shirt frill, no watch fob or seals, no knee-band buckles under the boots',
                             'Hat rigid on the head bone; lifting it is a renderer action, not a clip'])


def prepare_trader_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer (the recipe's role_1812); never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('trader_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_trader_1812.py',
         'unsupported trader component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'trader assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1812-08-14' and recipe.get('grade') == 'reconstructed',
         'trader scene/appearance grade changed')
    need(variant.get('person_reference_id') == PERSON, 'trader variant names another reference')
    need(spec.get('tailoring') == json.loads(json.dumps(TAILORING)), 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed trader body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'trader components require the declared liberty')
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
