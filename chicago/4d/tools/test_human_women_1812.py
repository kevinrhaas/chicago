"""The women of 1812 on the shared female rig (T-3464): sourced, layered, skinned; no BPy.

Four anonymous reconstructed roles from one generator (tools/human_women_1812.py):
lady_1812 (an officer's or trader's wife: a high-waisted gown of a small blue print, a muslin
kerchief, a day cap), woman_working_1812 (a soldier's wife or laundress: short gown,
petticoat, apron, neck kerchief, linen cap) and its variant woman_country_1812 (a French woman
of the country in Wau-Bun's short gown and petticoat with a blue cotton handkerchief round her
head, moccasins), and potawatomi_woman_1812 (a woman of the camp in the trade cloth of the
13th: a wrapped strouding skirt, a calico shirt, cloth leggings, a blanket, small silver
brooches; flagged review_required and touches_removal).
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_women_1812 as W

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ('lady_1812', 'woman_working_1812', 'woman_country_1812', 'potawatomi_woman_1812')
PIECES = {
    'lady_1812': {'gown_bodice', 'gown_skirt', 'gown_waist_band', 'neck_kerchief', 'headwear_day_cap'},
    'woman_working_1812': {'short_gown_body', 'short_gown_skirt', 'petticoat', 'apron', 'apron_band', 'neck_kerchief',
                           'headwear_linen_cap'},
    'woman_country_1812': {'short_gown_body', 'short_gown_skirt', 'petticoat', 'apron', 'apron_band', 'neck_kerchief',
                           'headwear_head_handkerchief'},
    'potawatomi_woman_1812': {'calico_shirt_body', 'calico_shirt_skirt', 'strouding_skirt', 'strouding_selvage',
                              'cloth_leggings', 'trade_blanket', 'silver_brooches'},
}


def load(variant_id):
    role = W.ROLE_OF[variant_id]
    recipe = json.loads((ROOT/W.RECIPES[role]).read_text())
    variant = next(v for v in recipe['proof_variants'] if v['id'] == variant_id)
    return role, recipe, variant


def z_at(mesh, x, y, side=1):
    hit = W.Surface(mesh).z(x, y, side)
    return hit[0] if hit else None


class Women(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = None
        cls.built = {}
        for vid in VARIANTS:
            role, recipe, variant = load(vid)
            if cls.body is None:
                cls.body = json.loads((ROOT/variant['body_input']).read_text())
            bundle = W._prepare(role, ROOT, recipe, variant, cls.body)
            cls.built[vid] = (recipe, variant, bundle, {m['name']: m for m in bundle['meshes']})
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        for vid, (recipe, variant, bundle, mesh) in self.built.items():
            with self.subTest(vid):
                self.assertEqual(set(mesh), PIECES[vid])
                self.assertTrue(bundle['skirt'])
                self.assertEqual(bundle['assembly'], W.ASSEMBLIES[W.ROLE_OF[vid]])
                self.assertEqual(bundle['shoe_material'], W.LOOKS[vid]['shoes'])
                for m in bundle['meshes']:
                    self.assertIn(m['material'], recipe['colors_linear_rgba'], m['name'])
                    self.assertEqual(m['material'].count('__'), 1, m['name'])
                slots = {m['material'].split('__')[0] for m in bundle['meshes']} | {'skin', 'eyes', 'footwear'}
                self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
                # Flat colours only, never white silk: every cloth is dulled below a pure white.
                for name, mat in bundle['materials'].items():
                    self.assertLess(max(mat['base_color_linear'][:3]), .7, name)
        self.assertEqual(self.built['potawatomi_woman_1812'][3]['silver_brooches']['receipt']['count'], 3)

    def test_each_is_anonymous_a_role_and_no_person(self):
        from human_teamster_blend import resolve_person_reference
        people = {p['id'] for p in json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']}
        ids = set()
        for vid, (recipe, variant, bundle, mesh) in self.built.items():
            with self.subTest(vid):
                self.assertEqual(variant['person_reference_id'], f'anonymous_{vid}')
                self.assertEqual((variant['person_reference_scene'], variant['person_reference_grade']), ('1812', 'reconstructed'))
                self.assertFalse(variant['reference_summary']['named'])
                self.assertNotIn(variant['person_reference_id'], people)
                self.assertTrue((ROOT/variant['person_reference_record']).is_file())
                resolve_person_reference(variant)
                named = copy.deepcopy(variant); named['person_reference_id'] = 'kinzie_john_elder'
                with self.assertRaises(ValueError):
                    resolve_person_reference(named)
                ids.add(variant['person_reference_id'])
        self.assertEqual(len(ids), len(VARIANTS))

    def test_every_garment_carries_provenance(self):
        for role in W.TAILORING:
            recipe = json.loads((ROOT/W.RECIPES[role]).read_text())
            with self.subTest(role):
                comp = recipe['women_components']
                self.assertEqual(comp['liberty'], W.LIBERTY)
                for g in comp['garments']:
                    p = g['provenance']
                    self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
                    self.assertTrue(p['source_scope'] and p['liberty'], g['id'])
                    self.assertLessEqual(set(p['source_ids']), set(recipe['sources']), g['id'])
                    for sid in p['source_ids']:
                        rec = json.loads((ROOT/'data/sources'/f'{sid}.json').read_text())
                        self.assertIn(rec['rights_status'], ('public_domain', 'no_known_restrictions'), sid)
                # Nothing of these women's dress is attested by a witness of 1812 at Chicago.
                self.assertNotIn('attested', {g['provenance']['grade'] for g in comp['garments']})
        for vid, (recipe, variant, bundle, mesh) in self.built.items():
            self.assertEqual({m['material'] for m in bundle['meshes']} | {bundle['shoe_material']},
                             {g['material'] for g in bundle['garments']}, vid)

    def test_the_potawatomi_woman_is_flagged_and_plain(self):
        recipe, variant, bundle, mesh = self.built['potawatomi_woman_1812']
        self.assertIs(variant['review_required'], True)
        self.assertIs(variant['touches_removal'], True)
        self.assertGreater(len(variant['review_reason']), 80)
        self.assertGreater(len(variant['touches_removal_reason']), 80)
        self.assertNotEqual(variant['review_reason'], variant['touches_removal_reason'])
        names = ' '.join(list(bundle['materials'])+list(mesh))
        for word in ('paint', 'feather', 'bonnet', 'headwear', 'fringe', 'bead'):
            self.assertNotIn(word, names)
        self.assertNotIn('bun', bundle, 'bare-headed: the looks layer draws her hair')
        for vid in ('lady_1812', 'woman_working_1812', 'woman_country_1812'):
            self.assertFalse(self.built[vid][1].get('review_required'))

    def test_skirts_clear_the_body_and_layers_stand_in_order(self):
        spine2 = self.bones['spine_02']['head_m'][1]
        for vid, skirt in (('lady_1812', 'gown_skirt'), ('woman_working_1812', 'petticoat'),
                           ('woman_country_1812', 'petticoat'), ('potawatomi_woman_1812', 'strouding_skirt')):
            self.assertGreater(self.built[vid][3][skirt]['receipt']['minimum_standing_body_clearance_m'], .004, vid)
        # The lady's skirt hangs from under the bust; the working skirts from the natural waist.
        self.assertGreater(self.built['lady_1812'][3]['gown_skirt']['receipt']['top_y_m'], spine2+.1)
        self.assertLess(self.built['woman_working_1812'][3]['petticoat']['receipt']['top_y_m'], spine2)
        # The kerchief lies over the bodice in front, at the breastbone.
        for vid, upper in (('lady_1812', 'gown_bodice'), ('woman_working_1812', 'short_gown_body')):
            mesh = self.built[vid][3]
            y = mesh['neck_kerchief']['receipt']['top_y_m']-.08
            zk, zb = z_at(mesh['neck_kerchief'], 0., y), z_at(mesh[upper], 0., y)
            self.assertIsNotNone(zk, vid); self.assertIsNotNone(zb, vid)
            self.assertGreater(zk, zb+.004, vid)
        # The apron lies over the short gown's skirt, which lies over the petticoat.
        mesh = self.built['woman_working_1812'][3]
        y = spine2-.1
        za, zp, zs = (z_at(mesh[k], 0.03, y) for k in ('apron', 'short_gown_skirt', 'petticoat'))
        self.assertGreater(za, zp); self.assertGreater(zp, zs)
        self.assertGreater(mesh['short_gown_skirt']['receipt']['minimum_skirt_clearance_m'], .004)
        # The blanket lies over the calico shirt behind; the selvage outside the skirt at its hem.
        mesh = self.built['potawatomi_woman_1812'][3]
        y = spine2+.15
        self.assertLess(z_at(mesh['trade_blanket'], 0., y, -1), z_at(mesh['calico_shirt_body'], 0., y, -1)-.004)
        hem = mesh['strouding_skirt']['receipt']['hem_y_m']
        y = hem+.015
        self.assertGreater(z_at(mesh['strouding_selvage'], .05, y), z_at(mesh['strouding_skirt'], .05, y))
        legs = mesh['cloth_leggings']['receipt']
        self.assertLess(legs['from_y_m'], hem); self.assertGreater(legs['to_y_m'], hem)

    def test_skirts_follow_the_legs_and_head_covers_ride_the_head(self):
        knee = self.bones['calf_l']['head_m'][1]
        for vid, skirt in (('lady_1812', 'gown_skirt'), ('woman_working_1812', 'petticoat'),
                           ('potawatomi_woman_1812', 'strouding_skirt')):
            m = self.built[vid][3][skirt]
            for p, w in zip(m['positions_m'], m['weights']):
                if p[1] < knee and abs(p[0]) > .03:
                    side = 'l' if p[0] > 0 else 'r'
                    self.assertGreater(w.get(f'thigh_{side}', 0)+w.get(f'calf_{side}', 0), .1, vid)
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        for vid, cover in (('lady_1812', 'headwear_day_cap'), ('woman_working_1812', 'headwear_linen_cap'),
                           ('woman_country_1812', 'headwear_head_handkerchief')):
            m = self.built[vid][3][cover]
            self.assertTrue(all(w == {'head': 1.} for w in m['weights']), vid)
            self.assertGreater(max(p[1] for p in m['positions_m']), top, vid)

    def test_refuses_changed_inputs(self):
        role, recipe0, variant = load('woman_country_1812')
        cases = [('tailoring', lambda r: r['women_components']['tailoring']['skirt'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['women_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['women_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__blue_cotton_handkerchief_1812=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1813-08-14'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(recipe0); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    W._prepare(role, ROOT, recipe, variant, self.body)
        role, recipe0, variant = load('potawatomi_woman_1812')
        for key in ('review_required', 'touches_removal', 'review_reason', 'touches_removal_reason'):
            with self.subTest(key):
                v = copy.deepcopy(variant); v.pop(key)
                with self.assertRaisesRegex(ValueError, 'review_required and touches_removal'):
                    W._prepare(role, ROOT, recipe0, v, self.body)

    def test_skin_and_hair_are_the_shared_studies_own(self):
        soldier = json.loads((ROOT/'data/humans/recipes/soldier_1812.json').read_text())
        cook = json.loads((ROOT/'data/humans/recipes/cook_1904.json').read_text())
        for role in W.TAILORING:
            recipe = json.loads((ROOT/W.RECIPES[role]).read_text())
            hair = {k: v for k, v in recipe['hair_component'].items() if k != 'appearance_basis'}
            self.assertEqual(hair, {k: v for k, v in soldier['hair_component'].items() if k != 'appearance_basis'}, role)
            self.assertEqual((recipe['skin_texture']['path'], recipe['skin_texture']['sha256']),
                             (cook['skin_texture']['path'], cook['skin_texture']['sha256']), role)
            self.assertEqual(recipe['lod_ratios'], soldier['lod_ratios'], role)


if __name__ == '__main__':
    unittest.main(verbosity=1)
