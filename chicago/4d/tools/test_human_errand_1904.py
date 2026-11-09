"""A 1904 parlor maid's street dress on the shared female rig (T-3481): sourced, layered, skinned; no BPy.

Christine Nelson out on an errand: a white shirtwaist with a tall collar, cuffs and a black bow,
a belt, a navy walking skirt of seven gores clear of the ground, a straw sailor hat with a
black ribbon, and a market basket carried in her left hand (tools/human_errand_1904.py, recipe
data/humans/recipes/errand_1904.json). She walks a loop round the Glessner block's sidewalks.
"""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import check_structure_clearance as C
import human_errand_1904 as E
import human_maid_1904 as M

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/E.RECIPE
INSTANCE = 'data/humans/instances/1904/hi_pa1904_glessner_john_j_c1900_christine_nelson_1904.json'
BLOCK_WALKS = ('e18th__indiana_prairie_18_20', 'prairie__indiana_prairie_18_20',
               'e20th__indiana_prairie_18_20', 'indiana__indiana_prairie_18_20')


class Errand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = E.prepare_errand_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'errand_shirtwaist', 'errand_cuffs', 'errand_necktie', 'walking_skirt', 'errand_belt',
                                          'headwear_errand_boater', 'headwear_errand_boater_ribbon', 'market_basket', 'basket_cloth'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], E.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        col = self.recipe['colors_linear_rgba']
        self.assertGreater(min(col['garment_upper__errand_shirtwaist_white'][:3]), .6)
        self.assertLess(max(col['garment_lower__errand_skirt_navy'][:3]), .06)
        self.assertFalse(set(E.MATERIALS) & set(M.MATERIALS))

    def test_a_walking_skirt_clear_of_the_ground_and_a_tall_collar(self):
        # The house maid's and the cook's skirts come to about 4 cm off the ground; hers to the ankle.
        self.assertGreater(min(p[1] for p in self.mesh['walking_skirt']['positions_m']), .065)
        neck = self.bones['neck_01']['head_m'][1]
        self.assertGreater(max(p[1] for p in self.mesh['errand_shirtwaist']['positions_m']), neck+.03)
        # Long sleeves to the cuffs at the wrist.
        wrist = abs(self.bones['hand_l']['head_m'][0])
        self.assertGreater(max(p[0] for p in self.mesh['errand_cuffs']['positions_m']), wrist-.03)

    def test_rigid_pieces_ride_their_bones(self):
        for name, bone in (('headwear_errand_boater', 'head'), ('headwear_errand_boater_ribbon', 'head'),
                           ('errand_necktie', 'neck_01'), ('market_basket', 'hand_l'), ('basket_cloth', 'hand_l')):
            self.assertTrue(all(w == {bone: 1.} for w in self.mesh[name]['weights']), name)
        # The hat sits on the drawn-up hair, above the eyes and level.
        eyes = self.bones['eye_l']['head_m'][1]
        hat = self.mesh['headwear_errand_boater']['positions_m']
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertGreater(min(p[1] for p in hat), eyes+.04)
        self.assertLess(min(p[1] for p in hat), top)
        self.assertLess(max(p[1] for p in hat)-min(p[1] for p in hat), .1)

    def test_the_basket_hangs_clear_of_the_skirt_in_the_hold(self):
        self.assertEqual(self.bundle['carry'], E.CARRY)
        self.assertEqual(self.recipe['errand_components']['carry'], E.CARRY)
        wrist, R, _ = E.carry_frame(self.bones)
        sh = self.bones['upperarm_l']['head_m']
        target = [sh[i]+E.CARRY['wrist_from_shoulder'][i] for i in range(3)]
        held = [[target[i]+sum(R[i][k]*(p[k]-wrist[k]) for k in range(3)) for i in range(3)]
                for p in self.mesh['market_basket']['positions_m'] + self.mesh['basket_cloth']['positions_m']]
        skirt = self.mesh['walking_skirt']['positions_m']
        for p in held[::3]:
            near = [q[0] for q in skirt if abs(q[1]-p[1]) < .03 and abs(q[2]-p[2]) < .05 and q[0] > 0]
            if near:
                self.assertGreater(p[0], max(near)+.01, p)
        self.assertGreater(min(p[1] for p in held), .3)
        # The handle passes through the closed hand: a basket point within 2.5 cm of the grip.
        axes = E.carry_frame(self.bones)[2]
        f, pa = axes['fingers'], axes['palm']
        grip = [target[i]+E.CARRY['grip_from_wrist']*f[i]+E.CARRY['grip_toward_palm']*pa[i] for i in range(3)]
        self.assertLess(min(math.dist(p, grip) for p in held), .025)

    def test_she_is_christine_nelson_walking_the_block(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('pa1904_glessner_john_j_c1900_christine_nelson', 'errand_1904_v1', 'inferred'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual(person['occupation']['value'], 'parlor maid')
        found = list((ROOT/'data/humans/instances').rglob('hi_*christine_nelson*.json'))
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in found], [INSTANCE])
        inst = json.loads(found[0].read_text())
        self.assertEqual((inst['scene'], inst['person_id'], inst['appearance']['asset_id'], inst['display'], inst['behaviour']['state'], inst['animation']['clip']),
                         ('1904', v['person_reference_id'], v['id'], 'shown', 'walking', 'walk'))
        self.assertIn(inst['id'], json.loads((ROOT/'data/humans/instances/1904/index.json').read_text())['instances'])

    def test_her_loop_keeps_to_the_block_s_sidewalks_and_clear_of_everything(self):
        inst = json.loads((ROOT/INSTANCE).read_text())
        p0 = inst['placement']
        pts = [(p0['local_e'], p0['local_n'])] + [(q['local_e'], q['local_n']) for q in inst['behaviour']['route']]
        loop = pts + [pts[0]]
        grid = {f['id']: f for f in json.loads((ROOT/'data/street_grid/1904.json').read_text())['faces']}
        bands = [grid[f]['bands']['walk'][0] for f in BLOCK_WALKS]
        shapes = [poly for b in C.buildings('1904') for poly in b['shapes']]
        shapes = [poly for poly in shapes if min(q[0] for q in poly) < 1400 and max(q[0] for q in poly) > 1270
                  and min(q[1] for q in poly) < -3210 and max(q[1] for q in poly) > -3470]
        fixed = [(t['e'], t['n']) for t in json.loads((ROOT/'data/street_trees/1904.json').read_text())['trees']]
        fixed += [(t['e'], t['n']) for t in json.loads((ROOT/'data/street_furniture/1904.json').read_text())['items']]
        others = []
        for f in (ROOT/'data/humans/instances/1904').glob('hi_*.json'):
            h = json.loads(f.read_text())
            if h['id'] != inst['id'] and h['behaviour']['state'] != 'walking':
                others.append((h['placement']['local_e'], h['placement']['local_n']))
        length = 0.
        for a, b in zip(loop, loop[1:]):
            d = math.dist(a, b); length += d
            for k in range(int(d/.25)+1):
                t = k*.25/d if d else 0
                p = (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
                self.assertTrue(any(C.inside(p, band) for band in bands), p)
                self.assertFalse(any(C.inside(p, s) for s in shapes), p)
                self.assertGreater(min(C.edge_distance(p, s) for s in shapes), .9, p)
                self.assertGreater(min(math.dist(p, q) for q in fixed), 1.2, p)
                if others:
                    self.assertGreater(min(math.dist(p, q) for q in others), .75, p)
        self.assertTrue(650 < length < 800, length)

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['errand_components']['garments']
        self.assertEqual(len(garments), 9)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_scope'] and p['liberty'], g['id'])
            # Only the reconstructed basket has no source; every other piece names one.
            self.assertTrue(p['source_ids'] or (g['id'] == 'market_basket' and p['grade'] == 'reconstructed'), g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            for sid in p['source_ids']:
                self.assertTrue((ROOT/'data/sources'/f'{sid}.json').exists(), sid)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['errand_components']['tailoring']['skirt'].update(ease=.03), 'tailoring'),
                 ('body', lambda r: r['errand_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['errand_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(accessory__market_basket=[1, 0, 0, 1]), 'colour'),
                 ('carry', lambda r: r['errand_components']['carry'].update(side='r'), 'carry')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    E.prepare_errand_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_pinned_woman_s_own(self):
        mattie = json.loads((ROOT/'data/humans/recipes/adult_dress_1904.json').read_text())
        self.assertEqual(self.recipe['skin_texture'], mattie['skin_texture'])
        self.assertEqual(self.recipe['hair_component'], mattie['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
