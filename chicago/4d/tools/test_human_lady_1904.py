"""A 1904 lady's day dress on the shared female rig (T-3447): sourced, layered, skinned; no BPy.

Frances M. Glessner's white shirtwaist with its standing collar and jabot, black fitted
jacket with revers and basque, gored black skirt to the ground, and a wide hat with plumes
(tools/human_lady_1904.py, recipe data/humans/recipes/lady_1904.json).
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_lady_1904 as L

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/L.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Lady(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = L.prepare_lady_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'lady_shirtwaist_collar', 'lace_jabot', 'lady_jacket_body',
                                          'lady_jacket_revers', 'lady_jacket_basque', 'gored_skirt',
                                          'headwear_lady_hat', 'lady_hat_plumes'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__lady_shoes_black')

    def test_she_is_frances_glessner_in_her_own_household_record(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly']), ('glessner_frances_m', 'lady_1904_v1'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        self.assertIn('glessner_frances_m', {p['id'] for p in hh['persons']})
        # No figure in the town draws her yet: the dress is built, not placed.
        self.assertFalse(list((ROOT/'data/humans/instances').rglob('*glessner_frances_m*')))

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['lady_components']['garments']
        self.assertEqual(len(garments), 7)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                self.assertTrue((ROOT/'data/sources'/f'{sid}.json').is_file(), sid)
        # Nothing here is attested: no picture of her in this dress has been read.
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})

    def test_shirtwaist_lies_under_the_jacket_and_only_where_it_shows(self):
        shirt, jacket = self.mesh['lady_shirtwaist_collar'], self.mesh['lady_jacket_body']
        spine = self.bones['spine_02']['head_m'][1]
        vb = spine+L.TAILORING['jacket']['roll_above_spine02']
        both = 0
        for x in (.02, .03, -.03):
            for y in (vb+.005, vb+.03, vb+.06):
                zs, zj = front_z(shirt, x, y), front_z(jacket, x, y)
                if zs is not None and zj is not None:
                    self.assertLess(zs+.003, zj, (x, y)); both += 1
        self.assertGreaterEqual(both, 3)
        # Nothing of it below the V or under the arms, where it would poke through the jacket.
        self.assertGreater(min(p[1] for p in shirt['positions_m']), vb-.02)
        self.assertLess(max(abs(p[0]) for p in shirt['positions_m']), .2)
        # The jabot stands on the shirtwaist front.
        for p in self.mesh['lace_jabot']['positions_m'][::5]:
            z = front_z(shirt, p[0], p[1])
            if z is not None:
                self.assertGreater(p[2], z-.002)

    def test_skirt_reaches_the_ground_clear_of_the_body_and_parts_over_the_legs(self):
        r = self.mesh['gored_skirt']['receipt']
        self.assertGreater(r['minimum_standing_body_clearance_m'], .004)
        self.assertLess(r['hem_y_m'], .05)
        self.assertGreater(self.mesh['lady_jacket_basque']['receipt']['minimum_skirt_clearance_m'], .005)
        # leg_follow (T-3423): over the front, below the hips, each point goes more with the
        # leg on its own side, and wholly with it once it is a hip's width out.
        skirt = self.mesh['gored_skirt']
        half = abs(self.bones['thigh_l']['head_m'][0])
        wide = 0
        for p, w in zip(skirt['positions_m'], skirt['weights']):
            if p[2] > .05 and abs(p[0]) > .02 and p[1] < r['top_y_m']-.25:
                side = 'l' if p[0] > 0 else 'r'
                other = 'r' if side == 'l' else 'l'
                own = w.get(f'thigh_{side}', 0)+w.get(f'calf_{side}', 0)
                rest = w.get(f'thigh_{other}', 0)+w.get(f'calf_{other}', 0)
                self.assertGreater(own, rest)
                if abs(p[0]) > 1.1*half:
                    self.assertGreater(own, .3); self.assertEqual(rest, 0); wide += 1
        self.assertGreater(wide, 50)

    def test_hat_and_plumes_are_rigid_on_the_head_above_the_eyes(self):
        hat, plumes = self.mesh['headwear_lady_hat'], self.mesh['lady_hat_plumes']
        self.assertTrue(hat['material'].startswith('headwear__') and 'band' not in hat['material'])
        self.assertFalse(plumes['material'].startswith('headwear__'))   # only the hat cuts the hair
        eyes = self.bones['eye_l']['head_m'][1]
        for m in (hat, plumes):
            self.assertTrue(all(w == {'head': 1.} for w in m['weights']), m['name'])
            self.assertGreater(min(p[1] for p in m['positions_m']), eyes, m['name'])
        self.assertGreater(hat['receipt']['seat_ring_hair_clearance_m'], .003)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['lady_components']['tailoring']['skirt'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['lady_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['lady_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__lady_hat_black=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    L.prepare_lady_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_pinned_woman_s_own(self):
        mattie = json.loads((ROOT/'data/humans/recipes/adult_dress_1904.json').read_text())
        skin = self.recipe['skin_texture']
        self.assertEqual(skin, mattie['skin_texture'])
        self.assertEqual(hashlib.sha256((ROOT/skin['path']).read_bytes()).hexdigest(), skin['sha256'])
        self.assertEqual(self.recipe['hair_component'], mattie['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
