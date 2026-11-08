# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 stable helper's working dress on the shared portable male rig (T-3484).

First worn by August Billings (born 1875 in Sweden), the helper who lived in the rear
building behind 1800 Prairie Avenue in 1900. The pieces, read from Frances Benjamin
Johnston's groom at a horse's head (ca. 1902; recipe data/humans/recipes/
stable_helper_1904.json):

  shirt        worn without coat or waistcoat, long sleeves buttoned at the wrist, a
               tall white standing collar closed at the throat (drawn in the shirt's colour); pale with a fine stripe in the
               photograph, drawn as its pale blue-grey (the stripe is not modelled)
  braces       dark straps over the shoulders and down the back
  belt         a leather belt at the trousers' waist, worn with the braces as the groom does
  trousers     dark and straight, long over the boots
  felt hat     a light felt hat with a creased crown and a short brim, rigid on the head
               bone and a mesh of its own
  boots        brown work boots (the foot is the shared fitted shoe)

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed (the
photograph is monochrome); liberty L-human-modular-dress-1789 with its T-3484 supplement.
The source anatomy is never changed: every piece is a shell offset from the body's own
triangles (its UVs and skin weights carried) or a loft round the body's own sections,
skinned to the body's own bones. Reuses the 1835 labourer's and the 1904 gentleman's
helpers, lending them this outfit's measures only for the call (their own builds are
untouched).

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_stable_helper_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_period_wardrobe import finish_edges
from human_workwear_fit import _slab_points, garment_shell
import human_gentleman_1904 as G
import human_labourer_1835 as L
from human_coachman_1904 import _lent

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'stable_helper_1904_v1'
RECIPE = 'data/humans/recipes/stable_helper_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=dict(ease=.007, waist_below_spine02=.14, collar_above_neck=.024, throat_v_below_neck=.040, throat_v_half_width=.010,
               cuff_short_of_wrist=.012, sleeve_fullness=.016, smoothing=90, sleeve_gather=.05, armpit_extra=.004),
    braces=dict(ease=.013, width=.026, x_at_waist=.064, x_at_top=.090, below_trouser_waist=.030, straight_above_below_neck=.035,
                over_shoulder_above_neck=.06),
    belt=dict(ease=.006, below_waist=.008, height=.032, segments=48, rows=3),
    trousers=dict(ease=.012, waist_height_fraction=.585, cuff_radius_ratio=.90, added_section_ease=.012,
                  thigh_transition_fraction=.65, hem_front_y=.066, hem_back_y=.034),
    felt_hat=dict(seat_below_top=.072, ease=.008, crown_height=.110, brim=.048, droop=.010, side_lift=.010,
                  thickness=.005, crease_depth=.030, pinch=.10),
)

MATERIALS = {
    'garment_upper__shirt_striped_1904': {'base_color_linear': [.60, .61, .63, 1], 'roughness': .84},  # the striped shirt reads pale in the photograph
    'accessory__braces_black_1904': {'base_color_linear': [.020, .019, .018, 1], 'roughness': .65},
    'accessory__belt_leather_1904': {'base_color_linear': [.070, .040, .022, 1], 'roughness': .55},
    'garment_lower__trousers_dark_1904': {'base_color_linear': [.038, .036, .034, 1], 'roughness': .92},
    'headwear__felt_hat_light_1904': {'base_color_linear': [.36, .33, .28, 1], 'roughness': .9},
    'footwear__brown_work_boots_1904': {'base_color_linear': [.050, .030, .017, 1], 'roughness': .5},
}
SHOE_MATERIAL = 'footwear__brown_work_boots_1904'
WEAVE_MATERIAL = 'garment_upper__shirt_striped_1904'


def shirt(body, bones):
    """The labourer's full-sleeved shirt cut closer: the collar closed at the throat with
    only a narrow opening under it, sleeves less full, buttoned at the wrist."""
    with _lent(L, shirt=TAILORING['shirt']):
        out = L.shirt(body, bones)
    out['name'] = 'work_shirt'; out['material'] = 'garment_upper__shirt_striped_1904'
    out['receipt'] = dict(out['receipt'], garment='striped work shirt, long sleeves, collar closed')
    return out


def braces(body, bones, trouser_waist):
    with _lent(L, braces=TAILORING['braces']):
        out = L.braces(body, bones, trouser_waist)
    out['name'] = 'braces_black'; out['material'] = 'accessory__braces_black_1904'
    return out


def trousers(body, bones, height):
    with _lent(L, trousers=TAILORING['trousers']):
        out = L.trousers(body, bones, height)
    out['name'] = 'work_trousers'; out['material'] = 'garment_lower__trousers_dark_1904'
    return out


def belt(body, bones, trousers_mesh, trouser_waist):
    """A leather belt round the trousers' waistband: a band lofted round the trousers' own
    section just under their top edge, standing `ease` off it. Skinned to the pelvis and
    the spine as the waistband beneath it."""
    t = TAILORING['belt']
    top = trouser_waist-t['below_waist']; bottom = top-t['height']
    tris = [[trousers_mesh['positions_m'][i] for i in f] for f in trousers_mesh['triangles']]
    n = t['segments']
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    pts = _slab_points(tris, bottom-.006, top+.004)
    need(len(pts) >= 12, 'no trouser section under the belt')
    cx = (min(p[0] for p in pts)+max(p[0] for p in pts))/2; cz = (min(p[2] for p in pts)+max(p[2] for p in pts))/2
    radii = [max((p[0]-cx)*dx+(p[2]-cz)*dz for p in pts)+t['ease'] for dx, dz in dirs]
    radii = [max(radii[k], (radii[k-1]+2*radii[k]+radii[(k+1) % n])/4) for k in range(n)]
    out = empty('leather_belt', 'accessory__belt_leather_1904')
    rows = t['rows']
    for r in range(rows):
        f = r/(rows-1); y = bottom+(top-bottom)*f
        for k, (dx, dz) in enumerate(dirs):
            out['positions_m'].append([cx+radii[k]*dx, y, cz+radii[k]*dz]); out['uvs'].append([k/n, f])
            out['weights'].append({'pelvis': .75, 'spine_01': .25})
    for r in range(rows-1):
        for k in range(n):
            a = r*n+k; b = r*n+(k+1) % n; c = a+n; d = b+n
            out['triangles'] += [[a, b, d], [a, d, c]]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .002)
    out['receipt'] = dict(garment='leather belt', top_y_m=top, bottom_y_m=bottom, ease_m=t['ease'],
                          skinning='pelvis, spine_01')
    return out


def felt_hat(body, bones, lod=0):
    """A light felt hat seated round the skull's own section: a crown creased down the
    middle and pinched at the front, a short brim turned down a little before and behind.
    Rigid on the head bone, a separate mesh."""
    t = TAILORING['felt_hat']
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
    H = t['crown_height']
    out = empty('headwear_felt_hat', 'headwear__felt_hat_light_1904')
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
    under_out = ring([r+B for r in seat_r], lambda k: seat-.002+fall[k])
    edge = ring([r+B+.004 for r in seat_r], lambda k: seat+fall[k]+th*.5-.002)
    over_out = ring([r+B for r in seat_r], lambda k: seat+th+fall[k])
    # The crown: straight sides tapering a little, then a top whose middle is creased down
    # from front to back, and whose front is pinched in at the sides.
    def clear(h, f):
        y = seat+th+H*h
        sl = [p for p in head_pts if abs(p[1]-y) <= .006]
        return [max(r*f*(1-t['pinch']*max(0., dz)*h*h), (max(((p[0]-cx)*dx+(p[2]-cz)*dz for p in sl), default=0.)+.006))
                for r, (dx, dz) in zip(seat_r, dirs)]
    profile = [(0., 1.01), (.3, 1.0), (.6, .96), (.85, .9), (1., .84)]
    crown = [ring(clear(h, f), (lambda yy: (lambda k: yy))(seat+th+H*h)) for h, f in profile]
    # The creased top: a ring part-way in at full height, then a ridge sunk along the
    # front-back line.
    rim = crown[-1]
    top_y = seat+th+H
    inner_top = ring([math.hypot(out['positions_m'][rim[k]][0]-cx, out['positions_m'][rim[k]][2]-cz)*.55 for k in range(n)],
                     lambda k: top_y-t['crease_depth']*(1-abs(dirs[k][0]))*.7+.004)
    rings = [inner, under_out, edge, over_out]+crown+[inner_top]
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    apex = len(out['positions_m'])
    out['positions_m'].append([cx, top_y-t['crease_depth'], cz]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([inner_top[k], apex, inner_top[(k+1) % n]])
    lining_y = top+.004
    need(top_y-t['crease_depth'] > lining_y+.006, 'the hat crease meets the skull')
    lining = ring([r*.55 for r in seat_r], lambda k: lining_y)
    for k in range(n):
        a, b, c, d = inner[k], inner[(k+1) % n], lining[(k+1) % n], lining[k]
        out['triangles'] += [[a, b, c], [a, c, d]]
    lc = len(out['positions_m']); out['positions_m'].append([cx, lining_y+.004, cz]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([lining[k], lining[(k+1) % n], lc])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='light felt hat, creased crown', seat_y_m=seat, crown_height_m=H, brim_m=B,
                          crease_depth_m=t['crease_depth'], head_bone='head', separate_mesh=True, lift='rigid on the head bone')
    return out


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    trouser_waist = TAILORING['trousers']['waist_height_fraction']*height
    legs = trousers(body, bones, height)
    parts = [shirt(body, bones), braces(body, bones, trouser_waist), legs, belt(body, bones, legs, trouser_waist),
             felt_hat(body, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_stable_helper_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; the photograph is monochrome and of Alabama',
                             'The shirt is one colour: its stripe is not modelled',
                             'No cloth simulation: shells follow the body bones',
                             'Braces run straight down the back (an H)',
                             'Hat rigid on the head bone'])


def prepare_stable_helper_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3484; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('stable_helper_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_stable_helper_1904.py',
         'unsupported stable helper component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'stable helper assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'stable helper scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed stable helper body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'stable helper components require the declared liberty')
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
