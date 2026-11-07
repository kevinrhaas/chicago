"""A 1904 stable helper's working dress on the shared male rig (T-3484): sourced, layered, skinned; no BPy.

August Billings's striped work shirt closed at the collar, black braces, leather belt, dark
trousers, brown work boots and light creased felt hat (tools/human_stable_helper_1904.py,
recipe data/humans/recipes/stable_helper_1904.json), after a groom photographed ca. 1902.
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_labourer_1835 as L
import human_merchant_1835 as M
import human_stable_helper_1904 as H

ROOT = Path(__file__).resolve().parent.parent


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class StableHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads((ROOT/H.RECIPE).read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = H.prepare_stable_helper_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'work_shirt', 'braces_black', 'work_trousers', 'leather_belt', 'headwear_felt_hat'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__brown_work_boots_1904')

    def test_dressed_as_the_photographed_groom_not_as_the_coachman(self):
        spec = self.recipe['stable_helper_components']
        ids = {g['id'] for g in spec['garments']}
        self.assertFalse(ids & {'waistcoat', 'cap', 'apron', 'livery_coat'})  # the groom wears none
        self.assertIn('loc_johnston_1902_tuskegee_horse_and_groom', self.recipe['sources'])
        import human_coachman_1904 as C
        self.assertFalse(set(H.MATERIALS) & set(C.MATERIALS))

    def test_he_is_august_billings_as_recorded_and_placed_once_in_town(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('pa1904_glessner_john_j_c1900_august_billings', 'stable_helper_1904_v1', 'inferred'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual((person['grade'], person['occupation']['value'], person['born']['value']), ('inferred', 'helper', '1875'))
        from human_teamster_blend import resolve_person_reference
        self.assertEqual(resolve_person_reference(v)['name'], 'August Billings')
        found = [p for p in (ROOT/'data/humans/instances').rglob('hi_*.json') if v['id'] in p.read_text()]
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in found],
                         ['data/humans/instances/1904/hi_pa1904_glessner_john_j_c1900_august_billings_1904.json'])
        inst = json.loads(found[0].read_text())
        self.assertEqual((inst['scene'], inst['person_id'], inst['appearance']['asset_id'], inst['display'], inst['interaction']['opens']),
                         ('1904', v['person_reference_id'], v['id'], 'shown', 'resident_card'))
        self.assertIn(inst['id'], json.loads((ROOT/'data/humans/instances/1904/index.json').read_text())['instances'])

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['stable_helper_components']['garments']
        self.assertEqual(len(garments), 6)
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), set(self.recipe['sources']), g['id'])
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})

    def test_layers_braces_over_shirt_and_belt_round_trousers(self):
        shirt, braces = self.mesh['work_shirt'], self.mesh['braces_black']
        over = 0
        for p in braces['positions_m'][::7]:
            if p[2] > 0:
                z = front_z(shirt, p[0], p[1])
                if z is not None:
                    self.assertGreater(p[2], z-.002, p); over += 1
        self.assertGreater(over, 10)
        belt = self.mesh['leather_belt']; legs = self.mesh['work_trousers']
        for p in belt['positions_m'][::5]:
            if p[2] > .04:
                z = front_z(legs, p[0], p[1])
                if z is not None:
                    self.assertGreater(p[2], z, p)
        self.assertTrue(all(w == {'pelvis': .75, 'spine_01': .25} for w in belt['weights']))

    def test_the_collar_is_closed_and_the_hat_is_on_the_head(self):
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        neck = self.bones['neck_01']['head_m'][1]
        self.assertIsNotNone(front_z(self.mesh['work_shirt'], 0., neck-.05))  # buttoned well up the throat
        hat = self.mesh['headwear_felt_hat']
        self.assertTrue(all(set(w) == {'head'} for w in hat['weights']))
        self.assertGreater(max(p[1] for p in hat['positions_m']), top+.02)
        self.assertLess(max(p[1] for p in hat['positions_m']), top+.10)  # a low crown, not a silk hat

    def test_lent_measures_go_back(self):
        before = (copy.deepcopy(G.TAILORING), copy.deepcopy(L.TAILORING), copy.deepcopy(M.TAILORING))
        H.construct(self.body)
        self.assertEqual((G.TAILORING, L.TAILORING, M.TAILORING), before)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['stable_helper_components']['tailoring']['shirt'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['stable_helper_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['stable_helper_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__felt_hat_light_1904=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    H.prepare_stable_helper_assembly(ROOT, recipe, self.variant, self.body)


if __name__ == '__main__':
    unittest.main(verbosity=1)
