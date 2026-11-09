"""A prosperous trader about 1810 on the shared male rig: sourced, layered, skinned; no BPy.

Dark green tailcoat cut square at the waist, yellow waistcoat, white neckcloth and collar points,
buff breeches, top boots with tan tops and a black round hat (tools/human_trader_1812.py, recipe
data/humans/recipes/trader_1812.json). A role, never a person: Kinzie and the settled men wear it.
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_trader_1812 as T

ROOT = Path(__file__).resolve().parent.parent


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Trader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads((ROOT/T.RECIPE).read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = T.prepare_trader_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'shirt_front_and_cuffs', 'shirt_collar_points', 'white_neckcloth', 'neckcloth_knot',
                                          'waistcoat_yellow', 'waistcoat_collar', 'tailcoat_body', 'tailcoat_lapels', 'tailcoat_tails',
                                          'tailcoat_buttons', 'buff_breeches', 'top_boot_shafts', 'top_boot_tops_tan', 'headwear_round_hat'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], T.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.mesh['tailcoat_buttons']['receipt']['count'], 6)
        self.assertFalse([m for m in self.bundle['meshes'] if '1835' in m['material']])

    def test_anonymous_role(self):
        from human_teamster_blend import resolve_person_reference
        v = self.variant
        self.assertEqual((v['id'], v['person_reference_id'], v['person_reference_scene'], v['person_reference_grade']),
                         ('trader_1812', T.PERSON, '1812', 'reconstructed'))
        self.assertFalse(resolve_person_reference(v)['named'])
        people = {p['id'] for p in json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']}
        self.assertNotIn(T.PERSON, people)
        named = copy.deepcopy(v); named['person_reference_id'] = 'kinzie_john_elder'
        with self.assertRaises(ValueError):
            resolve_person_reference(named)
        self.assertEqual(self.recipe['role_1812']['module'], 'human_trader_1812')

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['trader_components']['garments']
        sources = set(self.recipe['sources'])
        self.assertEqual({g['material'] for g in garments}, set(T.MATERIALS))
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                rec = json.loads((ROOT/'data/sources'/f'{sid}.json').read_text())
                self.assertIn(rec['rights_status'], ('public_domain', 'no_known_restrictions'), sid)
        self.assertNotIn('met_ci_1833_tailcoat_and_trousers', sources)   # too late for 1812 (dress.json)

    def test_layers_stand_in_order(self):
        coat, vest, shirt, cloth, knot = (self.mesh[k] for k in ('tailcoat_body', 'waistcoat_yellow', 'shirt_front_and_cuffs',
                                                                'white_neckcloth', 'neckcloth_knot'))
        spine = self.bones['spine_02']['head_m'][1]
        # Below the coat's square-cut front the waistcoat shows, and it overlaps the breeches.
        seam = coat['receipt']['waist_seam_y_m']
        self.assertGreater(seam, spine)
        self.assertIsNotNone(front_z(vest, 0., seam-.03))
        self.assertLess(vest['receipt']['hem_y_m'], T.TAILORING['breeches']['waist_height_fraction']*1.75)
        # The shirt shows in the waistcoat's V, behind it.
        y = vest['receipt']['v_bottom_y_m']+.04
        self.assertIsNotNone(front_z(shirt, 0., y))
        self.assertGreater(front_z(vest, .03, y), front_z(shirt, .03, y) or 0.)
        self.assertGreater(front_z(knot, 0., knot['receipt']['centre_y_m']), front_z(cloth, 0., knot['receipt']['centre_y_m']))

    def test_tails_to_the_knee_and_top_boots(self):
        r = self.mesh['tailcoat_tails']['receipt']
        self.assertGreater(r['minimum_standing_body_clearance_m'], .004)
        knee = self.bones['calf_l']['head_m'][1]
        self.assertLess(abs(r['hem_y_m']-knee), .03)
        black, tan = self.mesh['top_boot_shafts'], self.mesh['top_boot_tops_tan']
        self.assertLess(max(p[1] for p in black['positions_m']), min(p[1] for p in tan['positions_m'])+.001)
        self.assertLess(max(p[1] for p in tan['positions_m']), knee)
        self.assertGreater(min(p[1] for p in self.mesh['buff_breeches']['positions_m']), .3)

    def test_round_hat_not_the_1835_top_hat(self):
        hat = self.mesh['headwear_round_hat']
        self.assertTrue(all(w == {'head': 1.} for w in hat['weights']))
        merchant = json.loads((ROOT/'data/humans/recipes/merchant_1835.json').read_text())['merchant_components']['tailoring']['top_hat']
        mine = T.TAILORING['round_hat']
        self.assertLess(mine['crown_height'], merchant['crown_height'])
        self.assertLess(mine['crown_flare'], 1.)   # tapering, where the 1835 hat flares

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['trader_components']['tailoring']['coat'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['trader_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['trader_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__round_hat_black_1810=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1835-07-01'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    T.prepare_trader_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_period_studies_own(self):
        private = json.loads((ROOT/'data/humans/recipes/soldier_1812.json').read_text())
        for k in ('skin_texture', 'hair_component', 'eye_components', 'lod_ratios'):
            self.assertEqual(self.recipe[k], private[k], k)


if __name__ == '__main__':
    unittest.main(verbosity=1)
