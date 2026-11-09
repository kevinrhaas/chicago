"""A company officer of the First Infantry, August 1812, on the shared male rig: sourced, layered, skinned; no BPy.

Three variants on one geometry (tools/human_officer_1812.py, recipe data/humans/recipes/officer_1812.json):
a captain (epaulette right, a curved stirrup-hilted sword), a lieutenant (epaulette left, a
straight sword) and a surgeon's mate (no epaulette, black velvet collar, black plume).
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_officer_1812 as O

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/O.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Officer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variants = {v['officer_rank']: v for v in cls.recipe['proof_variants']}
        cls.body = json.loads((ROOT/cls.variants['captain']['body_input']).read_text())
        cls.bundles = {rank: O.prepare_officer_assembly(ROOT, cls.recipe, v, cls.body) for rank, v in cls.variants.items()}
        cls.mesh = {m['name']: m for m in cls.bundles['captain']['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_three_ranks_one_geometry(self):
        self.assertEqual(set(self.variants), {'captain', 'lieutenant', 'surgeons_mate'})
        self.assertEqual({v['id'] for v in self.recipe['proof_variants']},
                         {'officer_first_infantry_1812', 'officer_first_infantry_1812_lieutenant', 'surgeons_mate_first_infantry_1812'})
        names = {r: {m['name'] for m in b['meshes']} for r, b in self.bundles.items()}
        self.assertIn('epaulette_right', names['captain']); self.assertNotIn('epaulette_left', names['captain'])
        self.assertIn('epaulette_left', names['lieutenant']); self.assertNotIn('epaulette_right', names['lieutenant'])
        self.assertFalse([n for n in names['surgeons_mate'] if n.startswith('epaulette')])
        self.assertNotIn('collar_lace_silver', names['surgeons_mate'])
        # Every other piece is the same geometry in all three.
        common = names['captain'] & names['lieutenant'] & names['surgeons_mate']
        for name in common - {'sword_mounts_brass'}:
            shapes = {len(next(m for m in b['meshes'] if m['name'] == name)['triangles']) for b in self.bundles.values()}
            self.assertEqual(len(shapes), 1, name)
        mats = {r: {m['name']: m['material'] for m in b['meshes']} for r, b in self.bundles.items()}
        self.assertEqual(mats['surgeons_mate']['coat_collar'], 'garment_upper__collar_black_velvet_1812')
        self.assertEqual(mats['surgeons_mate']['headwear_plume'], 'headwear__plume_black_1812')
        self.assertEqual(mats['captain']['coat_collar'], 'garment_upper__facings_scarlet_1812')
        self.assertEqual(mats['captain']['headwear_plume'], 'headwear__plume_white_1812')

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'black_leather_stock', 'coat_collar', 'collar_lace_silver', 'coat_body', 'coat_cuffs_scarlet',
                                          'coat_skirts', 'coat_turnbacks_white', 'coat_buttons', 'epaulette_right', 'waist_belt_white',
                                          'sword_scabbard', 'sword_mounts_brass', 'white_waistcoat', 'white_pantaloons', 'boot_shafts',
                                          'headwear_chapeau', 'chapeau_loop_silver', 'headwear_plume'})
        for b in self.bundles.values():
            for m in b['meshes']:
                self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
                self.assertIn(m['material'], O.MATERIALS, m['name'])
            slots = {m['material'].split('__')[0] for m in b['meshes']} | {'skin', 'eyes'}
            self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.mesh['coat_buttons']['receipt']['count'], 10)
        # One draw no heavier than the private's ten dress materials.
        self.assertLessEqual(len({m['material'] for m in self.bundles['captain']['meshes']}), 10)

    def test_no_sash_no_crossbelts(self):
        for b in self.bundles.values():
            names = ' '.join(m['name']+' '+m['material'] for m in b['meshes'])
            for word in ('sash', 'crossbelt', 'cartridge'):
                self.assertNotIn(word, names)

    def test_anonymous_roles_placed_by_rank(self):
        from human_teamster_blend import resolve_person_reference
        people = {p['id'] for p in json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']}
        for rank, v in self.variants.items():
            self.assertEqual((v['person_reference_id'], v['person_reference_scene'], v['person_reference_grade']),
                             (O.PERSONS[rank], '1812', 'reconstructed'))
            self.assertFalse(v['reference_summary']['named'])
            self.assertNotIn(v['person_reference_id'], people)
            self.assertEqual(resolve_person_reference(v)['unit'], 'First Regiment of Infantry')
        named = copy.deepcopy(self.variants['captain']); named['person_reference_id'] = 'heald_nathan'
        with self.assertRaises(ValueError):
            resolve_person_reference(named)
        self.assertEqual(self.recipe['role_1812'], {'module': 'human_officer_1812', 'prepare': 'prepare_officer_assembly',
                                                    'assembly': O.ASSEMBLY})

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['officer_components']['garments']
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                rec = json.loads((ROOT/'data/sources'/f'{sid}.json').read_text())
                self.assertIn(rec['rights_status'], ('public_domain', 'no_known_restrictions'), sid)
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})
        self.assertNotIn('inde_peale_1808_zebulon_pike', sources)   # check_required: cited in text only
        for b in self.bundles.values():
            worn = {m['material'] for m in b['meshes']}
            self.assertLessEqual(worn, {g['material'] for g in b['garments']})

    def test_epaulette_on_the_shoulder_and_over_the_arm(self):
        for rank, side in (('captain', -1), ('lieutenant', 1)):
            m = next(m for m in self.bundles[rank]['meshes'] if m['name'].startswith('epaulette'))
            self.assertTrue(all(side*p[0] > .07 for p in m['positions_m']), rank)
            self.assertGreater(max(p[1] for p in m['positions_m']), self.bones['upperarm_l']['head_m'][1]+.03)
            arm = sum(sum(v for k, v in w.items() if k.startswith('upperarm')) for w in m['weights'])/len(m['weights'])
            self.assertGreater(arm, .2, rank)

    def test_layers_stand_in_order(self):
        coat, belt, vest, collar, stock = (self.mesh[k] for k in ('coat_body', 'waist_belt_white', 'white_waistcoat', 'coat_collar',
                                                                  'black_leather_stock'))
        waist = coat['receipt']['waist_seam_y_m']
        y = belt['receipt']['y_m'][0]+.015
        for x in (-.06, 0., .06):
            self.assertGreater(front_z(belt, x, y), front_z(coat, x, y)+.002, x)
        self.assertGreater(vest['receipt']['top_y_m'], waist+.01)
        self.assertLess(front_z(vest, 0., waist+.005), front_z(coat, 0., waist+.012))
        neck = self.bones['neck_01']['head_m'][1]
        self.assertIsNone(front_z(collar, 0., neck))
        self.assertIsNotNone(front_z(stock, 0., neck-.01))
        # The collar stands higher behind than the private's.
        self.assertGreater(collar['receipt']['top_back_y_m'], neck+.05)

    def test_skirts_to_the_bend_of_the_knee_with_turnbacks_on_them(self):
        r = self.mesh['coat_skirts']['receipt']
        self.assertGreater(r['minimum_standing_body_clearance_m'], .004)
        knee = self.bones['calf_l']['head_m'][1]
        self.assertLess(abs(r['hem_y_m']-knee), .03)
        tails, white = self.mesh['coat_skirts'], self.mesh['coat_turnbacks_white']
        import math
        def radius(p):
            return math.hypot(p[0], p[2])
        for p in white['positions_m'][::7]:
            near = min(tails['positions_m'], key=lambda q: (q[0]-p[0])**2+(q[1]-p[1])**2+(q[2]-p[2])**2)
            self.assertGreaterEqual(radius(p), radius(near)-.003)
        self.assertGreater(min(p[1] for p in self.mesh['boot_shafts']['positions_m']), .07)
        self.assertLess(max(p[1] for p in self.mesh['boot_shafts']['positions_m']), knee)

    def test_sword_rigid_at_the_left_hip_curved_for_the_captain(self):
        for rank, b in self.bundles.items():
            m = {x['name']: x for x in b['meshes']}
            for name in ('sword_scabbard', 'sword_mounts_brass'):
                self.assertTrue(all(w == {'pelvis': 1.} for w in m[name]['weights']))
                self.assertTrue(all(p[0] > .15 for p in m[name]['positions_m']), (rank, name))
            r = m['sword_scabbard']['receipt']
            self.assertEqual(r['curve_deg'] > 0, rank == 'captain')
            self.assertEqual(m['sword_mounts_brass']['receipt']['stirrup_hilt'], rank == 'captain')

    def test_chapeau_fore_and_aft_rigid_and_clear_of_the_head(self):
        hat, loop, plume = self.mesh['headwear_chapeau'], self.mesh['chapeau_loop_silver'], self.mesh['headwear_plume']
        for m in (hat, loop, plume):
            self.assertTrue(all(w == {'head': 1.} for w in m['weights']))
        self.assertGreater(hat['receipt']['minimum_head_clearance_m'], .004)
        P = hat['positions_m']
        span_z = max(p[2] for p in P)-min(p[2] for p in P); span_x = max(p[0] for p in P)-min(p[0] for p in P)
        self.assertGreater(span_z, 2*span_x)   # worn fore-and-aft
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(max(p[1] for p in P), top+.06)
        self.assertGreater(max(p[1] for p in plume['positions_m']), max(p[1] for p in P)+.1)
        self.assertTrue(all(p[0] > 0 for p in loop['positions_m']))   # cockade on the left

    def test_refuses_changed_inputs(self):
        v = self.variants['captain']
        cases = [('tailoring', lambda r: r['officer_components']['tailoring']['coat'].update(ease=.05), 'tailoring'),
                 ('ranks', lambda r: r['officer_components']['ranks']['captain'].update(epaulette='left'), 'ranks'),
                 ('body', lambda r: r['officer_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['officer_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__chapeau_black_1812=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1813-08-14'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    O.prepare_officer_assembly(ROOT, recipe, v, self.body)
        wrong = copy.deepcopy(v); wrong['officer_rank'] = 'colonel'
        with self.assertRaisesRegex(ValueError, 'rank'):
            O.prepare_officer_assembly(ROOT, self.recipe, wrong, self.body)

    def test_skin_and_hair_are_the_period_studies_own(self):
        private = json.loads((ROOT/'data/humans/recipes/soldier_1812.json').read_text())
        for k in ('skin_texture', 'hair_component', 'eye_components', 'lod_ratios'):
            self.assertEqual(self.recipe[k], private[k], k)


if __name__ == '__main__':
    unittest.main(verbosity=1)
