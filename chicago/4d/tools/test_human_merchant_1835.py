"""An 1835 merchant's day dress on the shared male rig (T-3449): sourced, layered, skinned; no BPy.

Philip F. W. Peck's dark blue tailcoat, buff waistcoat, black stock and collar points, pale
trousers and black top hat (tools/human_merchant_1835.py, recipe data/humans/recipes/merchant_1835.json).
"""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_merchant_1835 as M

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/M.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Merchant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = M.prepare_merchant_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'shirt_front_and_cuffs', 'shirt_collar_points', 'black_silk_stock', 'waistcoat_buff',
                                          'waistcoat_rolled_collar', 'tailcoat_body', 'tailcoat_lapels', 'tailcoat_tails',
                                          'tailcoat_buttons', 'full_trousers', 'headwear_top_hat'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], M.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__black_boots_1835')
        self.assertEqual(self.mesh['tailcoat_buttons']['receipt']['count'], 6)

    def test_he_is_philip_peck_as_recorded_and_not_placed_in_town(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('peck_philip', 'merchant_1835_v1', 'attested'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual((person['grade'], person['occupation']['value'], person['age_band']['value']),
                         ('attested', 'merchant', '30-39'))
        # The engineering body's age sits inside his band, so no ageing is asked of it.
        self.assertTrue(30 <= v['body_parameters']['engineering_age_years'] <= 39)
        from human_teamster_blend import resolve_person_reference
        self.assertEqual(resolve_person_reference(v)['name'], 'Philip F. W. Peck')
        self.assertFalse([p for p in (ROOT/'data/humans/instances').rglob('*.json')
                          if 'peck_philip' in p.read_text() or 'merchant_1835' in p.read_text()])

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['merchant_components']['garments']
        self.assertEqual(len(garments), 8)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                self.assertTrue((ROOT/'data/sources'/f'{sid}.json').is_file(), sid)
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})

    def test_layers_stand_in_order_on_the_chest(self):
        # Waistcoat under coat where both cover; the shirt front under the waistcoat.
        vest, coat, shirt = (self.mesh[k] for k in ('waistcoat_buff', 'tailcoat_body', 'shirt_front_and_cuffs'))
        spine = self.bones['spine_02']['head_m'][1]
        two = three = 0
        for x in (.06, .08, .1, .12, -.08, -.1):
            for y in (spine+.02, spine+.06, spine+.1, spine+.2, spine+.26):
                zv, zc = front_z(vest, x, y), front_z(coat, x, y)
                if zv is not None and zc is not None:
                    self.assertLess(zv+.002, zc, (x, y)); two += 1   # at least 2 mm of cloth between
        for x in (.03, -.03, .05):
            for y in (spine+.24, spine+.28, spine+.31):
                zs, zv = front_z(shirt, x, y), front_z(vest, x, y)
                if zs is not None and zv is not None:
                    self.assertLess(zs+.003, zv, (x, y)); three += 1
        self.assertGreaterEqual(two, 12); self.assertGreaterEqual(three, 2)
        # The waistcoat is made only in front (its back would poke through the coat).
        self.assertGreater(min(p[2] for p in vest['positions_m']), -.02)

    def test_tails_hang_behind_to_the_knee_and_part_over_the_legs(self):
        r = self.mesh['tailcoat_tails']['receipt']
        self.assertGreater(r['minimum_standing_body_clearance_m'], .004)
        knee = self.bones['calf_l']['head_m'][1]
        self.assertLess(abs(r['hem_y_m']-knee), .05)
        tails = self.mesh['tailcoat_tails']
        # Cut away in front: no tail cloth in front of the hips below the waist seam.
        self.assertFalse(any(p[2] > .06 and abs(p[0]) < .1 for p in tails['positions_m']))
        for p, w in zip(tails['positions_m'], tails['weights']):
            if p[1] < r['top_y_m']-.15 and abs(p[0]) > .01:
                side = 'l' if p[0] > 0 else 'r'
                other = 'r' if side == 'l' else 'l'
                self.assertGreater(w.get(f'thigh_{side}', 0)+w.get(f'calf_{side}', 0), .2)
                self.assertEqual(w.get(f'thigh_{other}', 0)+w.get(f'calf_{other}', 0), 0)

    def test_stock_wraps_the_neck_under_the_jaw(self):
        st = self.mesh['black_silk_stock']
        self.assertTrue(all(set(w) <= {'neck_01', 'spine_03'} for w in st['weights']))
        r = st['receipt']
        self.assertGreater(r['top_back_y_m'], r['top_front_y_m']+.03)   # high behind, under the jaw in front
        # The collar points stand above the stock's front edge, on the head and neck, both sides seen.
        cp = self.mesh['shirt_collar_points']
        self.assertTrue(cp['receipt']['double_sided'])
        self.assertGreater(max(p[1] for p in cp['positions_m']), r['top_front_y_m']+.02)
        self.assertTrue(all(set(w) <= {'neck_01', 'head'} for w in cp['weights']))

    def test_top_hat_is_rigid_on_the_head_and_tall(self):
        hat = self.mesh['headwear_top_hat']
        self.assertTrue(hat['material'].startswith('headwear__'))
        self.assertTrue(all(w == {'head': 1.} for w in hat['weights']))
        eyes = self.bones['eye_l']['head_m'][1]
        self.assertGreater(min(p[1] for p in hat['positions_m']), eyes)
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in hat['positions_m']), top+.06)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['merchant_components']['tailoring']['coat'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['merchant_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['merchant_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__top_hat_black=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    M.prepare_merchant_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_1835_studies_own(self):
        worker = json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_text())
        self.assertEqual(self.recipe['skin_texture'], worker['skin_texture'])
        self.assertEqual(self.recipe['hair_component'], worker['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
