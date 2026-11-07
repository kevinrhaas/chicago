"""A 1904 gentleman's day dress on the shared male rig (T-3441): sourced, layered, skinned; no BPy.

John J. Glessner's frock coat, high waistcoat, standing collar and tie, grey trousers and
black derby (tools/human_gentleman_1904.py, recipe data/humans/recipes/gentleman_1904.json).
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/G.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Gentleman(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = G.prepare_gentleman_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'shirt_standing_collar', 'waistcoat_high_cut', 'frock_coat_body',
                                          'frock_coat_lapels', 'frock_coat_skirts', 'straight_trousers',
                                          'four_in_hand_tie', 'headwear_derby'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
        # The contract's required slots, and the eye materials the spectacles fit to, survive.
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__black_boots')

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['gentleman_components']['garments']
        self.assertEqual(len(garments), 7)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                self.assertTrue((ROOT/'data/sources'/f'{sid}.json').is_file(), sid)

    def test_layers_stand_in_order_on_the_chest(self):
        # Shirt under waistcoat under coat, at points of the chest all three cover; the
        # shirt is made only where it can be seen (collar, front, cuffs).
        shirt, vest, coat = (self.mesh[k] for k in ('shirt_standing_collar', 'waistcoat_high_cut', 'frock_coat_body'))
        spine = self.bones['spine_02']['head_m'][1]
        vb = spine+G.TAILORING['waistcoat']['v_bottom_above_spine02']
        three = two = 0
        for x in (.06, .08, .1, .12, -.08):
            for y in (spine+.02, spine+.08, spine+.14, vb, vb+.05, vb+.1):
                zs, zv, zc = front_z(shirt, x, y), front_z(vest, x, y), front_z(coat, x, y)
                if zv is None or zc is None:
                    continue
                self.assertLess(zv+.003, zc, (x, y)); two += 1
                if zs is not None:
                    self.assertLess(zs+.003, zv, (x, y)); three += 1
        self.assertGreaterEqual(two, 12); self.assertGreaterEqual(three, 4)
        # No shirt under the armpits (where it would poke through the coat as the arms come down).
        arm_y = self.bones['upperarm_l']['head_m'][1]
        self.assertFalse(any(.12 < abs(p[0]) < .3 and arm_y-.15 < p[1] < arm_y-.02 for p in shirt['positions_m']))

    def test_skirts_clear_the_standing_body_and_part_over_the_legs(self):
        r = self.mesh['frock_coat_skirts']['receipt']
        self.assertGreater(r['minimum_standing_body_clearance_m'], .004)
        knee = self.bones['calf_l']['head_m'][1]
        self.assertLess(abs(r['hem_y_m']-knee), .06)   # to the knee
        skirt = self.mesh['frock_coat_skirts']
        for p, w in zip(skirt['positions_m'], skirt['weights']):
            if p[2] > .05 and abs(p[0]) > .02 and p[1] < r['top_y_m']-.15:
                side = 'l' if p[0] > 0 else 'r'
                other = 'r' if side == 'l' else 'l'
                self.assertGreater(w.get(f'thigh_{side}', 0)+w.get(f'calf_{side}', 0), .3)
                self.assertEqual(w.get(f'thigh_{other}', 0)+w.get(f'calf_{other}', 0), 0)

    def test_derby_is_rigid_on_the_head_and_liftable(self):
        hat = self.mesh['headwear_derby']
        self.assertTrue(hat['material'].startswith('headwear__') and 'band' not in hat['material'])
        self.assertTrue(all(w == {'head': 1.} for w in hat['weights']))
        eyes = self.bones['eye_l']['head_m'][1]
        self.assertGreater(min(p[1] for p in hat['positions_m']), eyes)

    def test_tie_lies_on_the_shirt_front(self):
        tie, shirt = self.mesh['four_in_hand_tie'], self.mesh['shirt_standing_collar']
        for p in tie['positions_m'][::7]:
            z = front_z(shirt, p[0], p[1])
            if z is not None:
                self.assertGreater(p[2], z-.002)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['gentleman_components']['tailoring']['coat'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['gentleman_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['gentleman_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__derby_felt=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    G.prepare_gentleman_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_is_the_pinned_bald_crown_atlas(self):
        skin = self.recipe['skin_texture']
        data = (ROOT/skin['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), skin['sha256'])
        source = json.loads((ROOT/skin['source_manifest_path']).read_text())
        self.assertEqual(source['derivative']['sha256'], skin['sha256'])
        self.assertEqual(skin['license'], 'CC0-1.0')
        from PIL import Image
        im = Image.open(ROOT/skin['path']).convert('L')
        self.assertEqual(im.size, (2048, 2048))
        # The crown (outer arc of the head island) is now as light as the forehead.
        crown = im.crop((1300, 500, 1450, 700)).resize((1, 1)).getpixel((0, 0))
        face = im.crop((1800, 900, 1900, 1100)).resize((1, 1)).getpixel((0, 0))
        self.assertLess(abs(crown-face), 30)


if __name__ == '__main__':
    unittest.main(verbosity=1)
