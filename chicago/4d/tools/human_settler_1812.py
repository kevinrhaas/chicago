# SPDX-License-Identifier: GPL-3.0-or-later
"""A settler's plain working dress about 1810, on the shared portable male rig.

An anonymous American farmer or labourer of the Chicago of 1812: Thomas Burns, John
Cooper, Charles Lee and his grown son, Liberty White and the American men of the militia
company Heald raised in the spring (armed from the garrison store, in their own clothes);
and Black Jim, the Kinzie household's servant, in a working man's dress with nothing
that implies a status the record does not give. The asset is a ROLE, never a person: each
man wears it with his own face, height, build and colouring (the variation kit and
human-looks.js). No source describes any Chicago settler's clothes in 1812; the pieces are
rural and working American dress of 1811-15 (recipe data/humans/recipes/settler_1812.json;
docs/RESEARCH/people-1812-3466/day.json, `settler_1812` and `black_servant_1812`):

  shirt        coarse unbleached linen or tow, full sleeves gathered at the wrist, open at
               the throat (the labourer's shirt, after the Pixler father and Krimmel's
               country inn and sawyers)
  neckerchief  a blue cotton kerchief knotted round the neck
  waistcoat    brown wool, buttoned to the chest, opening in a V above (Krimmel's
               sawyers wear waistcoats over shirt-sleeves)
  trousers     loose natural linen, full and straight to the instep
  round hat    black felt, a low round crown and a soft brim dipping a little fore and aft
               (Krimmel's sawyers' "black round hats"; the labourer's hat, re-measured),
               rigid on the head bone and a mesh of its own
  shoes        dark leather shoes, the shared closed shoe

No braces (the labourer's), no coat: a light figure for August work. Generated geometry is
CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 (supplement proposed in docs/RESEARCH/people-1812-dress/
officers-traders.md). The source anatomy is never changed. Reuses the 1835 labourer's garment
builders by import, lending them this outfit's measures for the call.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_settler_assembly() (the recipe's `role_1812`) and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest
from human_linen_seat import linen_seat_ease
import human_labourer_1835 as L
import human_coachman_1904 as C

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'settler_1812_v1'
RECIPE = 'data/humans/recipes/settler_1812.json'
LIBERTY = 'L-human-modular-dress-1789'
PERSON = 'anonymous_settler_1812'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    shirt=dict(ease=.008, waist_below_spine02=.14, collar_above_neck=.014, throat_v_below_neck=.10, throat_v_half_width=.034,
               cuff_short_of_wrist=.014, sleeve_fullness=.018, smoothing=90, sleeve_gather=.06, armpit_extra=.004),
    neckerchief=dict(ease=.014, bottom_below_neck=.030, back_bottom_below_neck=.004, height=.034, segments=36, rows=4),
    waistcoat=dict(ease=.021, armpit_extra=.008, hem_below_spine02=.095, top_below_neck=.020,
                   opening_half_width_hem=.006, opening_half_width_top=.050),
    trousers=dict(ease=.016, waist_height_fraction=.585, cuff_radius_ratio=.95, added_section_ease=.016,
                  thigh_transition_fraction=.65, hem_front_y=.066, hem_back_y=.034,
                  seat_ease=dict(id='settler_linen_seat_ease_v1', extra_rear_ease_m=.012,
                                 half_width_m=.14, full_half_width_m=.095,
                                 lower_below_pelvis_m=.16, lower_full_below_pelvis_m=.105,
                                 upper_below_waist_m=.008, upper_full_below_waist_m=.05,
                                 rear_transition_m=.035, section_rows=17)),
    round_hat=dict(seat_below_top=.074, ease=.008, crown_height=.100, brim=.074, droop=.022, side_lift=.004, thickness=.005),
)

MATERIALS = {
    'garment_upper__shirt_tow_linen_1810': {'base_color_linear': [.60, .56, .46, 1], 'roughness': .88},
    'garment_outer__waistcoat_brown_1810': {'base_color_linear': [.085, .052, .030, 1], 'roughness': .88},
    'garment_lower__trousers_linen_1810': {'base_color_linear': [.46, .41, .31, 1], 'roughness': .9},
    'accessory__neckerchief_blue_1810': {'base_color_linear': [.040, .070, .17, 1], 'roughness': .8},
    'headwear__round_hat_black_1810': {'base_color_linear': [.016, .015, .014, 1], 'roughness': .7},
    'footwear__shoes_dark_1810': {'base_color_linear': [.028, .019, .012, 1], 'roughness': .55},
}
SHOE_MATERIAL = 'footwear__shoes_dark_1810'
WEAVE_MATERIAL = 'garment_upper__shirt_tow_linen_1810'


def _renamed(mesh, name, material, garment):
    mesh['name'] = name; mesh['material'] = material
    mesh['receipt'] = dict(mesh.get('receipt', {}), garment=garment)
    return mesh


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    t = TAILORING
    with C._lent(L, shirt=t['shirt'], neckerchief=t['neckerchief'], waistcoat=t['waistcoat'], trousers=t['trousers']):
        shirt = _renamed(L.shirt(body, bones), 'shirt_full_sleeves', 'garment_upper__shirt_tow_linen_1810',
                         'coarse unbleached linen shirt, full sleeves, open throat')
        kerchief = _renamed(L.neckerchief(body, bones), 'neckerchief_blue', 'accessory__neckerchief_blue_1810',
                            'blue cotton neckerchief')
        vest = _renamed(L.waistcoat(body, bones), 'waistcoat_brown', 'garment_outer__waistcoat_brown_1810',
                        'brown waistcoat, buttoned to the chest')
        legs = _renamed(L.trousers(body, bones, height), 'loose_trousers', 'garment_lower__trousers_linen_1810',
                        'loose natural linen trousers to the instep')
        legs = linen_seat_ease(legs, bones, height, t['trousers']['waist_height_fraction'],
                               t['trousers']['seat_ease'])
    with C._lent(L, slouch_hat=t['round_hat']):
        hat = _renamed(L.slouch_hat(body, bones, lod=1), 'headwear_round_hat', 'headwear__round_hat_black_1810',
                       'black felt round hat, a low round crown and a soft brim')
    parts = [shirt, kerchief, vest, legs, hat]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_settler_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; no source describes a Chicago settler\'s clothes in 1812',
                             'No cloth simulation: shells follow the body bones',
                             'No coat, braces, musket or militia belts: the militia\'s arms are an instance\'s carried thing, not this dress',
                             'Hat rigid on the head bone'])


def prepare_settler_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer (the recipe's role_1812); never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('settler_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_settler_1812.py',
         'unsupported settler component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'settler assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1812-08-14' and recipe.get('grade') == 'reconstructed',
         'settler scene/appearance grade changed')
    need(variant.get('person_reference_id') == PERSON, 'settler variant names another reference')
    need(spec.get('tailoring') == json.loads(json.dumps(TAILORING)), 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed settler body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'settler components require the declared liberty')
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
