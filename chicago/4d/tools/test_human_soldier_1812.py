"""An 1812 private of the First Infantry on the shared male rig (T-3451): sourced, layered, skinned; no BPy.

An anonymous private of Heald's company: blue coat faced red, black leather stock, white
crossbelts with cartridge box and bayonet scabbard, white linen overalls, a tall felt cap with
a feather (tools/human_soldier_1812.py, recipe data/humans/recipes/soldier_1812.json).
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_soldier_1812 as S

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/S.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Soldier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = S.prepare_soldier_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'black_leather_stock', 'coat_collar_red', 'coat_body', 'coat_cuffs_red', 'coat_tails',
                                          'coat_buttons', 'crossbelts', 'cartridge_box_and_scabbard', 'linen_overalls',
                                          'overalls_waistband', 'headwear_felt_cap', 'headwear_plume'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], S.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.mesh['coat_buttons']['receipt']['count'], 8)

    def test_he_is_anonymous_and_not_placed_in_town(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['person_reference_scene'], v['person_reference_grade']),
                         (S.PERSON, '1812', 'reconstructed'))
        self.assertFalse(v['reference_summary']['named'])
        from human_teamster_blend import resolve_person_reference
        r = resolve_person_reference(v)
        self.assertEqual(r['unit'], 'First Regiment of Infantry')
        people = json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']
        self.assertNotIn(S.PERSON, {p['id'] for p in people})
        named = copy.deepcopy(v); named['person_reference_id'] = 'kinzie_john_elder'
        with self.assertRaises(ValueError):
            resolve_person_reference(named)
        self.assertFalse([p for p in (ROOT/'data/humans/instances').rglob('*.json')
                          if 'private_first_infantry' in p.read_text() or 'soldier_1812' in p.read_text()])

    def test_every_garment_carries_provenance_and_the_dating_is_kept(self):
        garments = self.recipe['soldier_components']['garments']
        self.assertEqual(len(garments), 7)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                self.assertTrue((ROOT/'data/sources'/f'{sid}.json').is_file(), sid)
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})
        # What the 1813 change took away is worn; what it brought is not.
        names = {m['material'] for m in self.bundle['meshes']}
        self.assertIn('garment_upper__facings_red_1812', names)
        self.assertIn('headwear__felt_cap_black', names)
        self.assertIn('headwear__plume_white', names)
        self.assertFalse([n for n in names if 'leather_cap' in n or 'pompon' in n])

    def test_layers_stand_in_order(self):
        coat, belts, band, collar, stock = (self.mesh[k] for k in ('coat_body', 'crossbelts', 'overalls_waistband',
                                                                    'coat_collar_red', 'black_leather_stock'))
        spine = self.bones['spine_02']['head_m'][1]
        n = 0
        for x in (-.04, 0., .04, .08, -.08):
            for y in (spine+.08, spine+.16, spine+.24, spine+.3):
                zb, zc = front_z(belts, x, y), front_z(coat, x, y)
                if zb is not None and zc is not None:
                    self.assertGreater(zb, zc+.002, (x, y)); n += 1
        self.assertGreaterEqual(n, 4)
        # The belts go over the shoulders and down the back.
        self.assertLess(min(p[2] for p in belts['positions_m']), -.05)
        # The waistband closes the waist under the coat's seam.
        waist = coat['receipt']['waist_seam_y_m']
        self.assertGreater(band['receipt']['top_y_m'], waist+.01)
        self.assertLess(front_z(band, 0., waist+.005), front_z(coat, 0., waist+.012))
        # The red collar stands outside the stock behind, and leaves its front open.
        neck = self.bones['neck_01']['head_m'][1]
        self.assertIsNone(front_z(collar, 0., neck))
        self.assertIsNotNone(front_z(stock, 0., neck-.01))

    def test_tails_hang_behind_to_mid_thigh_and_part_over_the_legs(self):
        r = self.mesh['coat_tails']['receipt']
        self.assertGreater(r['minimum_standing_body_clearance_m'], .004)
        knee = self.bones['calf_l']['head_m'][1]; hip = self.bones['thigh_l']['head_m'][1]
        self.assertTrue(knee+.1 < r['hem_y_m'] < hip-.1)
        tails = self.mesh['coat_tails']
        self.assertFalse(any(p[2] > .06 and abs(p[0]) < .1 for p in tails['positions_m']))
        for p, w in zip(tails['positions_m'], tails['weights']):
            if p[1] < r['top_y_m']-.15 and abs(p[0]) > .01:
                side = 'l' if p[0] > 0 else 'r'; other = 'r' if side == 'l' else 'l'
                self.assertGreater(w.get(f'thigh_{side}', 0)+w.get(f'calf_{side}', 0), .1)
                self.assertEqual(w.get(f'thigh_{other}', 0)+w.get(f'calf_{other}', 0), 0)

    def test_box_and_scabbard_are_rigid_on_the_pelvis_and_clear_of_the_body(self):
        m = self.mesh['cartridge_box_and_scabbard']
        self.assertTrue(all(w == {'pelvis': 1.} for w in m['weights']))
        P = self.body['meshes'][0]['positions_m']
        bz = m['receipt']['box_centre_m'][2]
        self.assertLess(bz+S.TAILORING['cartridge_box']['depth']/2, min(p[2] for p in P if .9 < p[1] < 1.05)-.02)

    def test_cap_and_feather_are_rigid_on_the_head_and_tall(self):
        cap, plume = self.mesh['headwear_felt_cap'], self.mesh['headwear_plume']
        for m in (cap, plume):
            self.assertTrue(all(w == {'head': 1.} for w in m['weights']))
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in cap['positions_m']), top+.08)
        self.assertGreater(max(p[1] for p in plume['positions_m']), max(p[1] for p in cap['positions_m']))

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['soldier_components']['tailoring']['coat'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['soldier_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['soldier_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__felt_cap_black=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1813-08-14'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    S.prepare_soldier_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_period_studies_own(self):
        worker = json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_text())
        self.assertEqual(self.recipe['skin_texture'], worker['skin_texture'])
        self.assertEqual(self.recipe['hair_component'], worker['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
