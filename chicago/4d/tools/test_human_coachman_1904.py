"""A 1904 coachman's standing livery on the shared male rig (T-3483): sourced, layered, skinned; no BPy.

Charles Nelson's double-breasted livery coat, white-metal buttons, white stock and gloves,
white breeches, black top boots and silk hat (tools/human_coachman_1904.py, recipe
data/humans/recipes/coachman_livery_1904.json).
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
import human_coachman_1904 as C

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/C.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


def ring_radius(mesh, y, cx, cz, tol=.012):
    pts = [p for p in mesh['positions_m'] if abs(p[1]-y) <= tol]
    return min(math.hypot(p[0]-cx, p[2]-cz) for p in pts) if pts else None


class Coachman(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = C.prepare_coachman_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'white_stock', 'livery_coat_body', 'livery_coat_skirt', 'livery_buttons', 'white_gloves',
                                          'white_breeches', 'top_boot_shafts', 'headwear_top_hat'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], C.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__black_top_boots')

    def test_it_is_not_hans_johnsons_livery(self):
        hans = json.loads((ROOT/'data/humans/wardrobes/anonymous_working_driver_1904.json').read_text())
        self.assertFalse(set(hans['materials']) & set(C.MATERIALS))
        self.assertNotIn('cape', ' '.join(self.mesh))
        coat = C.MATERIALS['garment_outer__livery_coat_green_1904']['base_color_linear']
        box = hans['materials']['garment_outer__box_coat_wool']['color']
        self.assertGreater(coat[1], coat[2]); self.assertLess(box[1], box[2])  # green, where Hans's is blue

    def test_he_is_charles_nelson_as_recorded_and_placed_once_in_town(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('pa1904_glessner_john_j_c1900_charles_nelson', 'coachman_livery_1904_v1', 'inferred'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual((person['grade'], person['occupation']['value'], person['born']['value']), ('inferred', 'coachman', '1848'))
        from human_teamster_blend import resolve_person_reference
        self.assertEqual(resolve_person_reference(v)['name'], 'Charles Nelson')
        found = [p for p in (ROOT/'data/humans/instances').rglob('hi_*.json') if v['id'] in p.read_text()]
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in found],
                         ['data/humans/instances/1904/hi_pa1904_glessner_john_j_c1900_charles_nelson_1904.json'])
        inst = json.loads(found[0].read_text())
        self.assertEqual((inst['scene'], inst['person_id'], inst['appearance']['asset_id'], inst['display'], inst['interaction']['opens']),
                         ('1904', v['person_reference_id'], v['id'], 'shown', 'resident_card'))
        self.assertIn(inst['id'], json.loads((ROOT/'data/humans/instances/1904/index.json').read_text())['instances'])

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['coachman_components']['garments']
        self.assertEqual(len(garments), 7)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            self.assertIn('seely_1902_coachman_livery_plates', p['source_ids'], g['id'])
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})

    def test_the_coat_closes_to_the_throat_and_the_buttons_lie_on_it(self):
        coat, buttons = self.mesh['livery_coat_body'], self.mesh['livery_buttons']
        spine = self.bones['spine_02']['head_m'][1]
        for y in (spine+.05, spine+.15, spine+.25):
            self.assertIsNotNone(front_z(coat, 0., y), y)  # closed: no opening down the front
        self.assertEqual(buttons['receipt']['count'], 12)
        for p in buttons['positions_m']:
            z = front_z(coat, p[0], p[1])
            if z is not None:
                self.assertGreater(p[2], z, p)

    def boot_section(self, side, y):
        """The boot shaft's cross-section at its row nearest y, as a polygon in (x, z)."""
        shaft = self.mesh['top_boot_shafts']['positions_m']
        y = min({p[1] for p in shaft}, key=lambda r: abs(r-y))
        row = [p for p in shaft if (p[0] > 0) == (side == 'l') and abs(p[1]-y) < 1e-3]
        cx = sum(p[0] for p in row)/len(row); cz = sum(p[2] for p in row)/len(row)
        row.sort(key=lambda p: math.atan2(p[2]-cz, p[0]-cx))
        return y, [(p[0], p[2]) for p in row]

    def assert_inside(self, points, polygon, label):
        for x, _, z in points:
            inside = False
            for (x1, z1), (x2, z2) in zip(polygon, polygon[-1:]+polygon[:-1]):
                if (z1 > z) != (z2 > z) and x < (x2-x1)*(z-z1)/(z2-z1)+x1:
                    inside = not inside
            self.assertTrue(inside, (label, x, z))

    def test_breeches_show_between_the_coat_hem_and_the_boots(self):
        hem = C.TAILORING['skirt']['hem_y']; boot_top = C.TAILORING['boots']['top_y']
        self.assertGreater(hem-boot_top, .05)
        b = self.mesh['white_breeches']['positions_m']
        self.assertLess(min(p[1] for p in b), boot_top)  # their foot is tucked inside the boot
        self.assertGreater(max(p[1] for p in b), hem+.3)
        for side in ('l', 'r'):
            y, mouth = self.boot_section(side, boot_top)
            leg = [p for p in b if (p[0] > 0) == (side == 'l') and abs(p[1]-y) < .006]
            self.assertTrue(leg, side)
            self.assert_inside(leg, mouth, f'breeches in the {side} boot mouth')

    def test_boots_enclose_the_calf(self):
        P = self.body['meshes'][0]['positions_m']
        rows = sorted({p[1] for p in self.mesh['top_boot_shafts']['positions_m']})
        for side in ('l', 'r'):
            checked = 0
            for y in [r for r in rows if r > .10]:  # below, the fitted shoe takes the ankle
                _, section = self.boot_section(side, y)
                calf = [p for p in P if (p[0] > .02 if side == 'l' else p[0] < -.02) and abs(p[1]-y) < .006]
                self.assert_inside(calf, section, f'{side} calf at {y:.3f}')
                checked += bool(calf)
            self.assertGreaterEqual(checked, 4, side)

    def test_gloves_and_hat_are_where_they_belong(self):
        g = self.mesh['white_gloves']
        wrist = abs(self.bones['hand_l']['head_m'][0])
        self.assertGreater(min(abs(p[0]) for p in g['positions_m']), wrist-.035)
        hat = self.mesh['headwear_top_hat']
        self.assertTrue(all(w == {'head': 1.} for w in hat['weights']))
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in hat['positions_m']), top+.06)  # a tall silk hat, not a bowler

    def test_lent_measures_go_back(self):
        before = (copy.deepcopy(G.TAILORING), copy.deepcopy(M.TAILORING))
        C.construct(self.body)
        self.assertEqual((G.TAILORING, M.TAILORING), before)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['coachman_components']['tailoring']['coat'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['coachman_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['coachman_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__silk_top_hat_1904=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    C.prepare_coachman_assembly(ROOT, recipe, self.variant, self.body)


if __name__ == '__main__':
    unittest.main(verbosity=1)
