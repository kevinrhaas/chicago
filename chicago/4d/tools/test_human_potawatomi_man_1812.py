"""A Potawatomi man of the 1812 Chicago gathering on the shared male rig: sourced, layered, skinned; no BPy.

An anonymous man in the everyday dress of 14 August 1812 after Keating's Metea (1823) and the
goods given out on the 13th: a checked trade shirt loose to mid-thigh, a blue broadcloth
breechcloth, scarlet stroud leggings with selvage flaps and garters, a white blanket belted
round the waist, silver arm bands and brooches, moccasins, bare head
(tools/human_potawatomi_man_1812.py, recipe data/humans/recipes/potawatomi_man_1812.json).
Held for review under the AGENTS.md standing constraint.
"""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_labourer_1835 as L
import human_potawatomi_man_1812 as P

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/P.RECIPE


def radial(mesh, y, a, band=.03, width=.12):
    """How far `mesh` reaches from the body axis near height y in the direction a (radians from the front)."""
    best = None
    for p in mesh['positions_m']:
        if abs(p[1]-y) < band:
            d = math.atan2(p[0], p[2])-a
            if abs(math.atan2(math.sin(d), math.cos(d))) < width:
                r = math.hypot(p[0], p[2])
                best = r if best is None else max(best, r)
    return best


class PotawatomiMan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = P.prepare_potawatomi_man_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'trade_shirt', 'trade_shirt_skirt', 'breechcloth', 'stroud_leggings', 'legging_flaps',
                                          'legging_selvage', 'garters', 'blanket_wrap', 'blanket_stripes', 'leather_belt',
                                          'silver_arm_bands', 'silver_brooches'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], P.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertNotIn('headwear', slots)  # bare head: the hair is the looks layer's
        self.assertEqual(self.recipe['role_1812'], {'module': 'human_potawatomi_man_1812',
                                                    'prepare': 'prepare_potawatomi_man_assembly', 'assembly': P.ASSEMBLY})

    def test_nothing_of_the_fifteenth_or_of_the_plains(self):
        words = json.dumps([m['name'] for m in self.bundle['meshes']]+list(P.MATERIALS)).lower()
        for w in ('paint', 'feather', 'bonnet', 'fringe', 'war', 'gun', 'knife', 'tomahawk', 'medal', 'gorget', 'headdress'):
            self.assertNotIn(w, words)

    def test_he_is_anonymous_and_held_for_review_with_his_own_reasons(self):
        v = self.variant
        self.assertEqual((v['id'], v['person_reference_id'], v['person_reference_scene'], v['person_reference_grade']),
                         ('potawatomi_man_1812', P.PERSON, '1812', 'reconstructed'))
        self.assertFalse(v['reference_summary']['named'])
        from human_teamster_blend import resolve_person_reference
        r = resolve_person_reference(v)
        self.assertTrue(r['review_required']); self.assertTrue(r['touches_removal'])
        self.assertGreater(len(v['review_reason']), 80); self.assertGreater(len(v['touches_removal_reason']), 80)
        people = json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']
        self.assertNotIn(P.PERSON, {p['id'] for p in people})
        named = copy.deepcopy(v); named['person_reference_id'] = 'black_partridge'
        with self.assertRaises(ValueError):
            resolve_person_reference(named)

    def test_every_garment_carries_provenance_and_none_is_attested(self):
        garments = self.recipe['potawatomi_man_components']['garments']
        self.assertEqual({g['material'] for g in garments} | {'garment_lower__leggings_selvage_white_1812',
                                                             'garment_outer__blanket_stripe_dark_1812'}, set(P.MATERIALS))
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
        self.assertLessEqual({'keating_1824_narrative_v1', 'kinzie_waubun_1856'}, sources)

    def test_the_shirt_is_the_labourers_cut_and_hangs_over_the_breechcloth(self):
        self.assertEqual(P.TAILORING['shirt'], L.TAILORING['shirt'])
        skirt, cloth = self.mesh['trade_shirt_skirt'], self.mesh['breechcloth']
        for y in (.78, .74):
            self.assertGreater(radial(skirt, y, 0.), radial(cloth, y, 0.)+.003, y)
        self.assertLess(min(p[1] for p in skirt['positions_m']), .71)

    def test_the_blanket_lies_over_shirt_and_breechcloth_under_its_belt_and_clears_the_stride(self):
        blanket, skirt = self.mesh['blanket_wrap'], self.mesh['trade_shirt_skirt']
        for y in (1.0, .9, .75):
            for a in (math.pi/2, math.pi, -math.pi/2):
                self.assertGreater(radial(blanket, y, a), radial(skirt, y, a)+.003, (y, a))
        self.assertGreater(self.mesh['blanket_wrap']['receipt']['minimum_thigh_clearance_m'], .02)
        belt = self.mesh['leather_belt']
        for a in (math.pi/2, math.pi):
            self.assertGreater(radial(belt, 1.02, a), radial(blanket, 1.02, a), a)
        # Open in front, the stripes either side of the opening.
        self.assertIsNone(radial(blanket, .9, 0., width=.15))
        xs = [p[0] for p in self.mesh['blanket_stripes']['positions_m']]
        self.assertTrue(min(xs) < -.05 and max(xs) > .05)

    def test_leggings_each_its_own_to_the_instep_and_gartered_below_the_knee(self):
        legs = self.mesh['stroud_leggings']
        self.assertLess(max(p[1] for p in legs['positions_m']), P.TAILORING['leggings']['top_y']+.025)  # cut by face centre
        self.assertLess(min(p[1] for p in legs['positions_m']), .08)
        knee = self.bones['calf_l']['head_m'][1]
        g = self.mesh['garters']
        self.assertTrue(all(knee-.09 < p[1] < knee-.02 for p in g['positions_m']))
        self.assertTrue(all(set(w) <= {'calf_l', 'calf_r'} for w in g['weights']))
        # The flaps run smooth down the outer seam (no jumps between rows).
        f = self.mesh['legging_flaps']['positions_m']; t = P.TAILORING['leggings']
        ys = [t['flap_top_y']+(t['flap_bottom_y']-t['flap_top_y'])*i/(t['flap_rows']-1) for i in range(t['flap_rows'])]
        for side in (1, -1):
            xs = [min(abs(p[0]) for p in f if p[0]*side > 0 and abs(p[1]-y) < .01) for y in ys]
            for a, b, c in zip(xs, xs[1:], xs[2:]):  # no zigzag: the seam bends gently from row to row
                self.assertLess(abs(a-2*b+c), .012)

    def test_silver_is_rigid_on_the_arms_and_lies_on_the_shirt(self):
        bands = self.mesh['silver_arm_bands']
        self.assertTrue(all(len(w) == 1 and next(iter(w)) in ('upperarm_l', 'upperarm_r') for w in bands['weights']))
        shirt = self.mesh['trade_shirt']
        for p in self.mesh['silver_brooches']['positions_m']:
            z, _ = G._surface_sample(shirt, p[0], p[1])
            self.assertGreater(p[2], z)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['potawatomi_man_components']['tailoring']['blanket'].update(ease=.08), 'tailoring'),
                 ('body', lambda r: r['potawatomi_man_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['potawatomi_man_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(accessory__silver_1812=[1, 1, 1, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1812-08-15'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    P.prepare_potawatomi_man_assembly(ROOT, recipe, self.variant, self.body)
        for flag in ('review_required', 'touches_removal'):
            with self.subTest(flag):
                variant = copy.deepcopy(self.variant); variant[flag] = False
                with self.assertRaisesRegex(ValueError, 'review_required and touches_removal'):
                    P.prepare_potawatomi_man_assembly(ROOT, self.recipe, variant, self.body)
        with self.subTest('prose'):
            variant = copy.deepcopy(self.variant); variant['touches_removal_reason'] = 'see above'
            with self.assertRaisesRegex(ValueError, 'own prose'):
                P.prepare_potawatomi_man_assembly(ROOT, self.recipe, variant, self.body)

    def test_skin_and_hair_are_the_period_studies_own(self):
        soldier = json.loads((ROOT/'data/humans/recipes/soldier_1812.json').read_text())
        for k in ('skin_texture', 'hair_component', 'eye_components', 'lod_ratios'):
            self.assertEqual(self.recipe[k], soldier[k], k)


if __name__ == '__main__':
    unittest.main(verbosity=1)
