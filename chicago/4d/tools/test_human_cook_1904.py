"""A 1904 cook's working dress on the shared female rig (T-3479): sourced, layered, skinned; no BPy.

Kate Ryan's dark print work dress with its sleeves rolled up, a broad checked apron wrapping
round the skirt with a pinned bib, its waistband and ties, and a cloth bound over her hair
(tools/human_cook_1904.py, recipe data/humans/recipes/cook_1904.json). Her own cut, not the
maid's recoloured, and she stands at the foot of the service stair in the court.
"""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_cook_1904 as K
import human_maid_1904 as M

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/K.RECIPE
INSTANCE = 'data/humans/instances/1904/hi_pa1904_glessner_john_j_c1900_kate_ryan_1904.json'


def normals_cancel(mesh):
    seen = {}
    for f in mesh['triangles']:
        key = frozenset(f)
        if key in seen and seen[key] != tuple(f):
            return True
        seen.setdefault(key, tuple(f))
    return False


class Cook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = K.prepare_cook_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'cook_bodice', 'rolled_sleeves', 'cook_neckband', 'cook_skirt', 'cook_apron_skirt',
                                          'cook_apron_bib', 'apron_waistband', 'apron_ties', 'headwear_cook_head_cloth'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], K.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__cook_shoes_black')
        col = self.recipe['colors_linear_rgba']
        self.assertLess(max(col['garment_upper__cook_print_dress'][:3]), .07)   # a dark print
        self.assertTrue(.2 < min(col['garment_outer__cook_apron_check'][:3]) < .6)   # a mid check, not the maid's white

    def test_her_own_cut_not_the_maid_s_recoloured(self):
        maid = M.prepare_maid_assembly(ROOT, json.loads((ROOT/M.RECIPE).read_text()),
                                       json.loads((ROOT/M.RECIPE).read_text())['proof_variants'][0], self.body)
        self.assertFalse(set(self.mesh) & {m['name'] for m in maid['meshes']})
        self.assertFalse(set(K.MATERIALS) & set(M.MATERIALS))
        # The sleeves stop on the forearm, rolled; the wrists are bare.
        for s, sx in (('l', 1), ('r', -1)):
            elbow, wrist = abs(self.bones[f'lowerarm_{s}']['head_m'][0]), abs(self.bones[f'hand_{s}']['head_m'][0])
            reach = max(sx*p[0] for p in self.mesh['cook_bodice']['positions_m'] + self.mesh['rolled_sleeves']['positions_m'])
            self.assertLess(reach, elbow+.11)
            self.assertLess(reach, wrist-.1)
        # The apron wraps round the hips past the sides (the maid's covers only the front).
        apron = self.mesh['cook_apron_skirt']['positions_m']
        self.assertLess(min(p[2] for p in apron), -.02)
        # The bib is pinned on across the chest: no straps over the shoulders or down the back.
        bib = self.mesh['cook_apron_bib']['positions_m']
        self.assertLess(max(p[1] for p in bib), self.bones['neck_01']['head_m'][1]-.1)
        self.assertGreater(min(p[2] for p in bib), .05)

    def test_the_cook_was_fitted_to_kate_ryan_who_is_not_drawn_in_1904(self):
        # T-3590 (owner, 2026-11-13, relaying Bill Tyre of Glessner House): Kate Ryan was the
        # temporary summer cook while Mattie was in New Hampshire with the family, and the
        # Glessners kept one cook at a time. The cook asset keeps her as its fitted reference
        # (the 1900 census record); her card says she was not living here in 1904, and no 1904
        # instance draws her. The asset is worn by other houses' cooks (prairie_1904.json).
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('pa1904_glessner_john_j_c1900_kate_ryan', 'cook_1904_v1', 'inferred'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual(person['occupation']['value'], 'cook')
        self.assertEqual(person['lived_here']['on_scene_date'], 'no')
        self.assertFalse((ROOT/INSTANCE).exists())
        self.assertNotIn('hi_pa1904_glessner_john_j_c1900_kate_ryan_1904', json.loads((ROOT/'data/humans/instances/1904/index.json').read_text())['instances'])
        cast = json.loads((ROOT/'data/humans/prairie_1904.json').read_text())['people']
        self.assertTrue(any(c.get('asset_id') == v['id'] for c in cast), 'other cooks still wear the asset')

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['cook_components']['garments']
        self.assertEqual(len(garments), 7)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                self.assertTrue((ROOT/'data/sources'/f'{sid}.json').exists(), sid)

    def test_apron_lies_over_the_skirt_and_stops_short_of_the_hem(self):
        skirt, apron = self.mesh['cook_skirt'], self.mesh['cook_apron_skirt']
        segs, rows = K.TAILORING['skirt']['segments'], K.TAILORING['skirt']['rows']
        for p in apron['positions_m'][::9]:
            q = min(skirt['positions_m'][:segs*rows], key=lambda s: math.dist(s, p))
            self.assertGreater(math.hypot(p[0], p[2]), math.hypot(q[0], q[2]))
        self.assertGreater(min(p[1] for p in apron['positions_m']), min(p[1] for p in skirt['positions_m'])+.05)

    def test_head_cloth_is_rigid_on_the_head_over_the_hair(self):
        cloth = self.mesh['headwear_cook_head_cloth']
        self.assertTrue(all(w == {'head': 1.} for w in cloth['weights']))
        eyes = self.bones['eye_l']['head_m'][1]
        self.assertGreater(min(p[1] for p in cloth['positions_m']), eyes-.06)
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in cloth['positions_m']), top)

    def test_ties_shade_from_both_sides(self):
        self.assertTrue(self.mesh['apron_ties']['receipt']['double_sided'])
        self.assertFalse(normals_cancel(self.mesh['apron_ties']))

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['cook_components']['tailoring']['skirt'].update(ease=.03), 'tailoring'),
                 ('body', lambda r: r['cook_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['cook_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__cook_head_cloth=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    K.prepare_cook_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_pinned_woman_s_own(self):
        mattie = json.loads((ROOT/'data/humans/recipes/adult_dress_1904.json').read_text())
        self.assertEqual(self.recipe['skin_texture'], mattie['skin_texture'])
        self.assertEqual(self.recipe['hair_component'], mattie['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
