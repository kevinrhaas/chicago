"""An 1835 labourer's working dress on the shared male rig (T-3450): sourced, layered, skinned; no BPy.

Patrick Mahoney's unbleached shirt with full sleeves, red neckerchief, braces, open green
waistcoat, brown trousers and drab slouch hat (tools/human_labourer_1835.py, recipe
data/humans/recipes/labourer_1835.json).
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_labourer_1835 as L

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/L.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Labourer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = L.prepare_labourer_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'shirt_full_sleeves', 'neckerchief_red', 'braces', 'waistcoat_open', 'full_trousers',
                                          'headwear_slouch_hat'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], L.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__brown_boots_1835')

    def test_he_is_patrick_mahoney_as_recorded_and_placed_once_in_town(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('rc_mahoney_patrick', 'labourer_1835_v1', 'reconstructed'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual((person['grade'], person['occupation']['value'], person['age_band']['value']),
                         ('reconstructed', 'labourer', '30-39'))
        self.assertTrue(30 <= v['body_parameters']['engineering_age_years'] <= 39)
        from human_teamster_blend import resolve_person_reference
        self.assertEqual(resolve_person_reference(v)['name'], 'Patrick Mahoney')
        # He stands in the 1835 town once, in this dress, on the South Water bank (T-3452).
        found = [p for p in (ROOT/'data/humans/instances').rglob('hi_*.json')
                 if 'mahoney_patrick' in p.read_text() or 'labourer_1835' in p.read_text()]
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in found], ['data/humans/instances/1835/hi_rc_mahoney_patrick_1835.json'])
        inst = json.loads(found[0].read_text())
        self.assertEqual((inst['scene'], inst['person_id'], inst['appearance']['asset_id'], inst['display']),
                         ('1835', 'rc_mahoney_patrick', v['id'], 'shown'))
        self.assertIn(inst['id'], json.loads((ROOT/'data/humans/instances/1835/index.json').read_text())['instances'])

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['labourer_components']['garments']
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

    def test_braces_lie_on_the_shirt_and_show_in_the_open_waistcoat(self):
        shirt, braces, vest = (self.mesh[k] for k in ('shirt_full_sleeves', 'braces', 'waistcoat_open'))
        spine = self.bones['spine_02']['head_m'][1]
        t = L.TAILORING['braces']
        shown = 0
        for y in (spine-.05, spine+.05, spine+.15, spine+.25):
            r = braces['receipt']
            f = min(1., (y-r['bottom_y_m'])/(r['straight_above_y_m']-r['bottom_y_m']))
            x = t['x_at_waist']+(t['x_at_top']-t['x_at_waist'])*f
            for side in (1, -1):
                zb, zs = front_z(braces, side*x, y), front_z(shirt, side*x, y)
                self.assertIsNotNone(zb, (x, y))
                if zs is not None:
                    self.assertGreater(zb, zs+.004, (x, y))
                if front_z(vest, side*x, y) is None or front_z(vest, side*x, y) < zb:
                    shown += 1
        self.assertGreaterEqual(shown, 6)
        # The waistcoat stands over the shirt wherever both are; its fronts fall open.
        n = 0
        for x in (.12, .14, -.12, -.14):
            for y in (spine, spine+.1, spine+.2):
                zv, zs = front_z(vest, x, y), front_z(shirt, x, y)
                if zv is not None and zs is not None:
                    self.assertGreater(zv, zs+.004, (x, y)); n += 1
        self.assertGreaterEqual(n, 8)
        self.assertIsNone(front_z(vest, 0., spine+.1))
        # The braces go over the shoulders and down the back.
        self.assertLess(min(p[2] for p in braces['positions_m']), -.05)

    def test_sleeves_are_full_and_the_shirt_tucks_in(self):
        r = self.mesh['shirt_full_sleeves']['receipt']
        self.assertGreater(r['sleeve_points_eased'], 200)
        trousers_waist = L.TAILORING['trousers']['waist_height_fraction']*max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertLess(r['waist_y_m'], trousers_waist-.04)

    def test_neckerchief_wraps_the_neck_over_the_shirt_collar(self):
        k = self.mesh['neckerchief_red']
        self.assertTrue(all(set(w) <= {'neck_01', 'spine_03'} for w in k['weights']))
        shirt = self.mesh['shirt_full_sleeves']
        neck = self.bones['neck_01']['head_m'][1]
        for x in (.03, -.03, .045):
            zk, zs = front_z(k, x, neck), front_z(shirt, x, neck)
            self.assertIsNotNone(zk)
            if zs is not None:
                self.assertGreater(zk, zs, x)

    def test_slouch_hat_is_rigid_on_the_head_and_broad(self):
        hat = self.mesh['headwear_slouch_hat']
        self.assertTrue(all(w == {'head': 1.} for w in hat['weights']))
        eyes = self.bones['eye_l']['head_m'][1]
        self.assertGreater(min(p[1] for p in hat['positions_m']), eyes-.02)
        xs = [p[0] for p in hat['positions_m']]
        self.assertGreater(max(xs)-min(xs), .30)
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in hat['positions_m']), top+.02)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['labourer_components']['tailoring']['waistcoat'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['labourer_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['labourer_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__slouch_hat_drab=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    L.prepare_labourer_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_1835_studies_own(self):
        worker = json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_text())
        self.assertEqual(self.recipe['skin_texture'], worker['skin_texture'])
        self.assertEqual(self.recipe['hair_component'], worker['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
