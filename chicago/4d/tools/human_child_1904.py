# SPDX-License-Identifier: GPL-3.0-or-later
"""Original 1904 children's clothes on pinned child and teenage bodies (T-3548).

The 1904 Hewitt photograph guides boys' knee trousers, stockings and jackets;
Snyder's Oxford children guide a girl's sleeved, waisted frock. Neither picture
identifies a Prairie Avenue child. All cuts, colours and unseen details are
reconstructed. Anatomy is left unchanged; canonical Blender export is separate.
"""
import copy
import hashlib
import json
from pathlib import Path

import human_child_1812 as C
import human_gentleman_1904 as G
import human_soldier_1812 as S
from human_dress_components import digest, empty, need
from human_period_wardrobe import finish_edges

ROOT = Path(__file__).resolve().parents[1]
LIBERTY = 'L-prairie-people-3548'
ROLES = {
    'child_boy_1904': ('prepared_child_male_8.json', 8, 'boy'),
    'child_girl_1904': ('prepared_child_female_8.json', 8, 'girl'),
    'child_toddler_1904': ('prepared_child_3.json', 3, 'toddler'),
    'teen_boy_1904': ('prepared_teen_male_15.json', 15, 'boy'),
    'teen_girl_1904': ('prepared_teen_female_15.json', 15, 'girl'),
}
CLOTH = 'garment_upper__child_jacket_1904'
PANTS = 'garment_lower__child_trousers_1904'
UPPER = 'garment_upper__child_frock_1904'
LOWER = 'garment_lower__child_frock_1904'
SOCKS = 'garment_lower__child_stockings_1904'
COLLAR = 'accessory__child_collar_1904'
BUTTONS = 'accessory__child_buttons_1904'
SHOES = 'footwear__child_shoes_1904'


def materials(kind):
    keys = [CLOTH, PANTS, COLLAR, BUTTONS] if kind == 'boy' else [UPPER, LOWER, COLLAR]
    colours = {CLOTH: [.065, .08, .10, 1], PANTS: [.065, .08, .10, 1],
               UPPER: [.40, .36, .28, 1], LOWER: [.40, .36, .28, 1],
               SOCKS: [.025, .022, .02, 1], COLLAR: [.75, .73, .68, 1],
               BUTTONS: [.055, .045, .035, 1], SHOES: [.022, .019, .016, 1]}
    return {k: {'base_color_linear': colours[k], 'roughness': .82 if k != SHOES else .5}
            for k in keys + [SOCKS, SHOES]}


def shell(body, bones, name, material, low, high, ease, sleeves=None):
    fields = [lambda v: v['p'][1] - low, lambda v: high - v['p'][1]]
    if sleeves is not None:
        fields += [lambda v: sleeves - abs(v['p'][0])]
    else:
        fields += [lambda v: .35 - G._arm_mass(v)]
    out = G._poly_shell(body, bones, name, material, fields, ease, [(low, high)],
                        bones['neck_01']['head_m'][1], None, smooth=(60, ease))
    out.pop('_normals', None)
    return finish_edges(out, .0015)


def collar(upper, bones, width, depth):
    # Cut from the outer cloth, excluding its thin turned edges. Those returns
    # share vertex UVs and must not become a second garment's cutting surface.
    if upper.get('flat_face_indices'):
        outer = copy.deepcopy(upper)
        skip = set(outer.pop('flat_face_indices'))
        outer['triangles'] = [f for i, f in enumerate(outer['triangles']) if i not in skip]
        if 'corner_uvs' in outer:
            outer['corner_uvs'] = [f for i, f in enumerate(outer['corner_uvs']) if i not in skip]
        upper = outer
    neck = bones['neck_01']['head_m']
    fields = [lambda v: v['p'][1] - (neck[1] - depth),
              lambda v: width - abs(v['p'][0]),
              lambda v: max(abs(v['p'][0]) - .007, -v['p'][2] + neck[2])]
    return finish_edges(S._on_garment(upper, fields, 'child_collar', COLLAR, .003), .0012)


def construct(body, role):
    need(role in ROLES, 'unknown 1904 child role')
    _, age, kind = ROLES[role]; before = digest(body); bones = C._bones(body)
    neck = bones['neck_01']['head_m'][1]; waist = bones['spine_01']['head_m'][1]
    knee = bones['calf_l']['head_m'][1]; ankle = bones['foot_l']['head_m'][1]
    wrist = abs(bones['hand_l']['head_m'][0]) - .012
    parts = []
    if kind == 'boy':
        upper = shell(body, bones, 'child_jacket', CLOTH, waist - .025, neck - .008, .018, wrist)
        shorts = shell(body, bones, 'child_trousers', PANTS, ankle + .012 if age >= 14 else knee + .018,
                       waist + .018, .023)
        buttons = empty('child_jacket_buttons', BUTTONS)
        t = dict(radius=.004, standoff=.002, sides=10)
        for i in range(4):
            C._button_at(buttons, upper, 0, neck - .055 - i * (neck - .09 - waist) / 3, t)
        buttons['corner_uvs'] = [[buttons['uvs'][i] for i in f] for f in buttons['triangles']]
        parts += [upper, shorts, buttons, collar(upper, bones, .12 if age >= 14 else .10, .04)]
        hem = knee + .025
    else:
        # The original frock helpers accept explicit measurements; no 1812 recipe or
        # material is used. Long sleeves, a higher neckline, lower waist and shorter
        # skirt give the 1904 silhouette visible in the reference photograph.
        t = copy.deepcopy(C.TAILORING['child_girl_1812']['bodice'])
        ua = abs(bones['upperarm_l']['head_m'][0]); la = abs(bones['lowerarm_l']['head_m'][0])
        t.update(sleeve_of_upperarm=(wrist - ua) / (la - ua), puff=.008,
                 neck_drop_front=.016, neck_drop_back=.010, neck_drop_side=.012,
                 waist_from_spine03_to_shoulder=-.45)
        upper, seam = C.frock_bodice(body, bones, t, UPPER)
        hem = ankle + .08 if age >= 14 else max(ankle + .07, knee - .075)
        t = copy.deepcopy(C.TAILORING['child_girl_1812']['skirt'])
        scale = C._height(body) / 1.27
        t.update(hem_y=hem, hem_rx=.215*scale, hem_rz_front=.185*scale,
                 hem_rz_back=.195*scale, gathers=18, gather=.007)
        skirt = C.frock_skirt(body, bones, seam, upper, t, LOWER, 'child_frock_skirt')
        parts += [upper, skirt, collar(upper, bones, .10*scale, .035)]
    parts.append(shell(body, bones, 'child_stockings', SOCKS, ankle + .01, hem + .025, .004))
    for p in parts:
        p.pop('_normals', None)
    need(before == digest(body), '1904 clothes mutated the pinned anatomy')
    return {'format': 'chicago4d_child_1904_source_v1', 'license': 'CC0-1.0', 'units': 'm',
            'grade': 'reconstructed', 'assembly': role + '_v1', 'source_body_unchanged': True,
            'body_semantic_sha256': before, 'meshes': parts, 'materials': materials(kind),
            'shoe_material': SHOES, 'weave_material': CLOTH if kind == 'boy' else UPPER,
            'skirt': kind != 'boy', 'liberty': LIBERTY,
            'limitations': ['The references show other American children, not these residents.',
                            'Cuts, colour, fit and unseen details are reconstructed; no cloth simulation.',
                            'The teenage outfits and toddler frock extrapolate the reference silhouettes.']}


def validate_palette(recipe, kind):
    # The exporter textures the body's neutral skin material before adding clothes.
    # Keeping only garment colours leaves that real mesh without its material.
    palette = recipe.get('colors_linear_rgba', {})
    need(palette.get('skin') == [1, 1, 1, 1], 'textured child skin needs its neutral material')
    for name, material in materials(kind).items():
        need(palette.get(name) == material['base_color_linear'], 'cloth palette changed: ' + name)


def prepare_child_assembly(root, recipe, variant, body):
    role = variant['id']; need(role in ROLES, 'unknown 1904 child asset')
    filename, age, kind = ROLES[role]
    validate_palette(recipe, kind)
    need(recipe.get('grade') == 'reconstructed' and recipe.get('scene_date') == '1904-07-01', 'wrong scene or grade')
    need(variant.get('component_assembly') == role + '_v1' and
         variant.get('recipe_path') == f'data/humans/recipes/{role}.json', 'recipe/assembly binding changed')
    need(variant.get('person_reference_id') == 'anonymous_' + role and
         variant.get('person_reference_grade') == 'reconstructed', 'a clothing asset must not invent a resident')
    path = Path(root) / 'assets/authored/humans/makehuman_hm08' / filename
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == recipe['child_components']['body_sha256'], 'child body pin changed')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'wrong child anatomy or rights')
    need(body['target_blend']['phenotype']['chosen_age_years'] == age, 'wrong engineering age')
    for source in recipe['sources']:
        s = json.loads((Path(root) / 'data/sources' / (source + '.json')).read_text())
        need(s.get('rights_status') in ('public_domain', 'no_known_restrictions'), 'uncleared clothing reference')
    bundle = construct(body, role)
    bundle['walk'] = C.apply_child_walk(body) or C.child_walk(body)
    bundle['garments'] = recipe['child_components']['garments']
    return bundle


def resolve_reference(variant, root=ROOT):
    role = variant['id']; need(role in ROLES, 'unknown anonymous 1904 child role')
    need(variant.get('component_assembly') == role + '_v1' and
         variant.get('recipe_path') == f'data/humans/recipes/{role}.json', 'unbound child recipe')
    need(variant.get('person_reference_id') == 'anonymous_' + role and
         variant.get('person_reference_grade') == 'reconstructed', 'a role must not identify a person')
    record = Path(root) / variant['person_reference_record']
    need(record.parent == Path(root) / 'data/sources' and record.is_file(), 'role has no source record')
    summary = variant['reference_summary']; need(summary.get('named') is False, 'role must stay anonymous')
    people = json.loads((Path(root) / 'data/sidecars/1904/people.json').read_text())['people']
    need(all(p['id'] != variant['person_reference_id'] for p in people), 'anonymous role collides with a person')
    return {**summary, 'review_required': True, 'touches_removal': False}
