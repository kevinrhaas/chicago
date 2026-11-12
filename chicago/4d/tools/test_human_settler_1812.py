"""A settler's plain working dress about 1810 on the shared male rig: sourced, layered, skinned; no BPy.

Coarse shirt, blue neckerchief, brown waistcoat, loose linen trousers, shoes and a black round hat
(tools/human_settler_1812.py, recipe data/humans/recipes/settler_1812.json). A role, never a person.
"""
import copy
import json
from pathlib import Path
import sys
import unittest

from test_human_linen_seat import LinenSeat
from test_human_clothing_capture_v2 import CaptureControls

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_settler_1812 as St

ROOT = Path(__file__).resolve().parent.parent


class Settler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads((ROOT/St.RECIPE).read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = St.prepare_settler_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_and_light(self):
        self.assertEqual(set(self.mesh), {'shirt_full_sleeves', 'neckerchief_blue', 'waistcoat_brown', 'loose_trousers',
                                          'headwear_round_hat'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        # Lighter than the 1812 private's dress (15,028 triangles at lod0 before the body).
        self.assertLess(sum(len(m['triangles']) for m in self.bundle['meshes']), 15028)
        self.assertNotIn('braces', ' '.join(self.mesh))

    def test_anonymous_role(self):
        from human_teamster_blend import resolve_person_reference
        v = self.variant
        self.assertEqual((v['id'], v['person_reference_id'], v['person_reference_grade']), ('settler_1812', St.PERSON, 'reconstructed'))
        self.assertFalse(resolve_person_reference(v)['named'])
        people = {p['id'] for p in json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']}
        self.assertNotIn(St.PERSON, people)
        named = copy.deepcopy(v); named['person_reference_id'] = 'burns_thomas'
        with self.assertRaises(ValueError):
            resolve_person_reference(named)

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['settler_components']['garments']
        self.assertEqual({g['material'] for g in garments}, set(St.MATERIALS))
        for g in garments:
            p = g['provenance']
            self.assertEqual(p['grade'], 'reconstructed', g['id'])   # no source describes a Chicago settler's clothes
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), set(self.recipe['sources']), g['id'])
            for sid in p['source_ids']:
                rec = json.loads((ROOT/'data/sources'/f'{sid}.json').read_text())
                self.assertIn(rec['rights_status'], ('public_domain', 'no_known_restrictions'), sid)

    def test_layers_and_hat(self):
        vest, shirt = self.mesh['waistcoat_brown'], self.mesh['shirt_full_sleeves']
        spine = self.bones['spine_02']['head_m'][1]
        zv, _ = G._surface_sample(vest, .08, spine+.05)
        zs, _ = G._surface_sample(shirt, .08, spine+.05)
        self.assertGreater(zv, zs)
        hat = self.mesh['headwear_round_hat']
        self.assertTrue(all(w == {'head': 1.} for w in hat['weights']))
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in hat['positions_m']), top+.01)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['settler_components']['tailoring']['shirt'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['settler_components'].update(body_sha256='0'*64), 'body source'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__round_hat_black_1810=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1835-07-01'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    St.prepare_settler_assembly(ROOT, recipe, self.variant, self.body)


if __name__ == '__main__':
    unittest.main(verbosity=1)
