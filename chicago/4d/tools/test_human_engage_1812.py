"""An 1812 engage of the Chicago trading households on the shared male rig: sourced, layered, skinned; no BPy.

An anonymous French Canadian or Metis engage: a blue calico shirt (the 1835 labourer's cut),
a red worsted sash knotted at the left hip, deer-skin trousers, smoked moccasins and a red
knitted cap (tools/human_engage_1812.py, recipe data/humans/recipes/engage_1812.json).
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_labourer_1835 as L
import human_engage_1812 as E

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/E.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Engage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = E.prepare_engage_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'shirt_calico', 'deerskin_trousers', 'sash_worsted', 'sash_ends', 'headwear_tuque'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], E.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__moccasins_smoked_1812')
        self.assertEqual(self.recipe['role_1812'], {'module': 'human_engage_1812', 'prepare': 'prepare_engage_assembly',
                                                    'assembly': E.ASSEMBLY})

    def test_he_is_anonymous_a_role_and_held_for_review_with_his_reasons(self):
        v = self.variant
        self.assertEqual((v['id'], v['person_reference_id'], v['person_reference_scene'], v['person_reference_grade']),
                         ('engage_1812', E.PERSON, '1812', 'reconstructed'))
        self.assertFalse(v['reference_summary']['named'])
        from human_teamster_blend import resolve_person_reference
        r = resolve_person_reference(v)
        self.assertTrue(r['review_required'])
        self.assertFalse(r['touches_removal'])
        self.assertGreater(len(v['review_reason']), 80); self.assertGreater(len(v['touches_removal_reason']), 40)
        people = json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']
        self.assertNotIn(E.PERSON, {p['id'] for p in people})
        named = copy.deepcopy(v); named['person_reference_id'] = 'ouilmette_antoine'
        with self.assertRaises(ValueError):
            resolve_person_reference(named)

    def test_every_garment_carries_provenance_and_none_is_attested(self):
        garments = self.recipe['engage_components']['garments']
        self.assertEqual({g['material'] for g in garments}, set(E.MATERIALS))
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
        self.assertIn('kinzie_waubun_1856', sources)

    def test_shirt_and_trousers_are_the_labourers_cut(self):
        self.assertEqual(E.TAILORING['shirt'], L.TAILORING['shirt'])
        self.assertEqual(E.TAILORING['trousers'], L.TAILORING['trousers'])
        self.assertEqual(self.recipe['engage_components']['tailoring']['shirt'], json.loads(json.dumps(L.TAILORING['shirt'])))

    def test_the_sash_lies_over_shirt_and_trousers(self):
        sash, shirt, legs = self.mesh['sash_worsted'], self.mesh['shirt_calico'], self.mesh['deerskin_trousers']
        t = E.TAILORING['sash']
        n = 0
        for x in (-.06, 0., .06):
            for y in (t['bottom_y']+.01, (t['bottom_y']+t['top_y'])/2, t['top_y']-.01):
                zs = front_z(sash, x, y)
                for under in (shirt, legs):
                    zu = front_z(under, x, y)
                    if zs is not None and zu is not None:
                        self.assertGreater(zs, zu+.002, (x, y)); n += 1
        self.assertGreaterEqual(n, 6)
        # The ends hang at the left hip and go with the left thigh, never the right.
        ends = self.mesh['sash_ends']
        self.assertTrue(all(p[0] > .05 for p in ends['positions_m']))
        self.assertLess(min(p[1] for p in ends['positions_m']), t['bottom_y']-.15)
        self.assertFalse(any(w.get('thigh_r', 0)+w.get('calf_r', 0) > .01 for w in ends['weights']))

    def test_the_cap_is_rigid_on_the_head_and_its_top_falls_back(self):
        cap = self.mesh['headwear_tuque']
        self.assertTrue(all(w == {'head': 1.} for w in cap['weights']))
        head = [p for p, w in zip(self.body['meshes'][0]['positions_m'], self.body['meshes'][0]['weights']) if w.get('head', 0) > .9]
        top = max(p[1] for p in head)
        self.assertGreater(max(p[1] for p in cap['positions_m']), top+.04)
        self.assertLess(min(p[2] for p in cap['positions_m'] if p[1] > top), min(p[2] for p in head)+.04)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['engage_components']['tailoring']['sash'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['engage_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['engage_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__tuque_red_1812=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1835-07-01'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    E.prepare_engage_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_period_studies_own(self):
        soldier = json.loads((ROOT/'data/humans/recipes/soldier_1812.json').read_text())
        for k in ('skin_texture', 'hair_component', 'eye_components', 'lod_ratios'):
            self.assertEqual(self.recipe[k], soldier[k], k)


if __name__ == '__main__':
    unittest.main(verbosity=1)
