"""The 1812 children on child bodies of the shared portable rig (T-3465): sourced, layered, skinned; no BPy.

Five anonymous role assets (tools/human_child_1812.py, recipes data/humans/recipes/<role>.json):
a boy of about six to ten in a skeleton suit, a girl in a high-waisted frock and pinafore, a
child of about two to four (either sex) in a white frock, and a Potawatomi boy and girl of the
camp in calico, stroud and moccasins (review_required, touches_removal). Bodies are CC0 MakeHuman
child/baby macro blends (SOURCE-child.json) at CDC 10th-centile heights.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_child_1812 as C

ROOT = Path(__file__).resolve().parent.parent
HM = ROOT/'assets/authored/humans/makehuman_hm08'
PIECES = {
    'child_boy_1812': {'skeleton_jacket', 'shirt_collar', 'skeleton_trousers', 'skeleton_trousers_band', 'suit_buttons'},
    'child_girl_1812': {'frock_bodice', 'frock_skirt', 'pinafore_apron', 'pinafore_bib'},
    'child_toddler_1812': {'frock_bodice', 'frock_skirt'},
    'potawatomi_boy_1812': {'calico_shirt', 'calico_shirt_tail', 'stroud_leggings'},
    'potawatomi_girl_1812': {'calico_blouse', 'calico_blouse_skirt', 'wrapped_skirt', 'wrapped_skirt_selvage', 'stroud_leggings'},
}
HEIGHTS = {'male_8': 1.208, 'female_8': 1.205, 'either_3': .905}


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


class Children(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes, cls.variants, cls.bodies, cls.bundles, cls.mesh = {}, {}, {}, {}, {}
        for role, r in C.ROLES.items():
            recipe = json.loads((ROOT/r['recipe']).read_text())
            variant = recipe['proof_variants'][0]
            body = json.loads((ROOT/variant['body_input']).read_text())
            cls.recipes[role], cls.variants[role], cls.bodies[role] = recipe, variant, body
            cls.bundles[role] = C.prepare_child_assembly(ROOT, recipe, variant, body)
            cls.mesh[role] = {m['name']: m for m in cls.bundles[role]['meshes']}

    def test_child_bodies_are_pinned_cc0_blends_on_the_56_joint_rig(self):
        manifest = json.loads((HM/'SOURCE-child.json').read_text())
        adult = json.loads((HM/'SOURCE.json').read_text())
        rows = {f['path']: f for f in manifest['files']}
        # Every adult row is kept unchanged; the twelve child/baby macro targets are added.
        for f in adult['files']:
            self.assertEqual(rows.get(f['path']), f, f['path'])
        added = {p for p in rows if p not in {f['path'] for f in adult['files']}}
        self.assertEqual(added, {f'makehuman/data/targets/macrodetails/{r}-{s}-{a}.target'
                                 for r in ('caucasian', 'asian', 'african') for s in ('male', 'female') for a in ('child', 'baby')})
        self.assertEqual(manifest['commit'], adult['commit'])
        for p in added:
            raw = (HM/p).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (rows[p]['bytes'], rows[p]['sha256']), p)
            self.assertIn(manifest['commit'], rows[p]['url'])
        for key, (path, sha) in C.BODIES.items():
            raw = (ROOT/path).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sha, path)
            body = json.loads(raw)
            self.assertEqual(body['license'], 'CC0-1.0')
            self.assertEqual(len(body['skeleton']), 56, path)
            self.assertAlmostEqual(max(p[1] for m in body['meshes'] for p in m['positions_m']), HEIGHTS[key], delta=.006)
            blend = body['target_blend']
            self.assertEqual(blend['phenotype']['age_anchors_years'], {'baby': 1, 'child': 10, 'young': 25})

    def test_every_piece_is_there_with_its_material_and_colour(self):
        for role, pieces in PIECES.items():
            with self.subTest(role):
                self.assertEqual(set(self.mesh[role]), pieces)
                recipe = self.recipes[role]
                for m in self.bundles[role]['meshes']:
                    self.assertIn(m['material'], recipe['colors_linear_rgba'], m['name'])
                    self.assertIn(m['material'], C.MATERIALS[role], m['name'])
                slots = {m['material'].split('__')[0] for m in self.bundles[role]['meshes']} | {'skin', 'eyes', 'footwear'}
                self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'footwear'}, slots)
                self.assertEqual(self.bundles[role]['shoe_material'], C.ROLES[role]['shoe'])
                self.assertIn(self.bundles[role]['weave_material'], C.MATERIALS[role])
                self.assertEqual(bool(self.bundles[role].get('skirt')), C.ROLES[role]['skirt'])
        self.assertEqual(self.mesh['child_boy_1812']['suit_buttons']['receipt'], {
            'garment': 'horn buttons: jacket front and trouser band', 'front': 4, 'band': 7})

    def test_each_child_is_anonymous_and_a_role(self):
        from human_teamster_blend import resolve_person_reference
        people = {p['id'] for p in json.loads((ROOT/'data/sidecars/1812/people.json').read_text())['people']}
        for role, v in self.variants.items():
            with self.subTest(role):
                self.assertEqual((v['person_reference_id'], v['person_reference_scene'], v['person_reference_grade']),
                                 (C.ROLES[role]['person'], '1812', 'reconstructed'))
                self.assertTrue(v['person_reference_id'].startswith('anonymous_'))
                self.assertNotIn(v['person_reference_id'], people)
                r = resolve_person_reference(v)
                self.assertFalse(r['named'])
                lo, hi = r['ages_years']
                self.assertTrue(2 <= lo < hi <= 11, r['ages_years'])
                named = copy.deepcopy(v); named['person_reference_id'] = 'kinzie_john_elder'
                with self.assertRaises(ValueError):
                    resolve_person_reference(named)

    def test_every_garment_carries_provenance_from_cleared_sources(self):
        for role, recipe in self.recipes.items():
            with self.subTest(role):
                garments = recipe['child_components']['garments']
                sources = set(recipe['sources'])
                for g in garments:
                    p = g['provenance']
                    self.assertIn(p['grade'], ('inferred', 'reconstructed'), g['id'])
                    self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'] == C.LIBERTY, g['id'])
                    self.assertLessEqual(set(p['source_ids']), sources, g['id'])
                    for sid in p['source_ids']:
                        record = json.loads((ROOT/'data/sources'/f'{sid}.json').read_text())
                        self.assertIn(record['rights_status'], ('public_domain', 'no_known_restrictions'), sid)
                worn = {m['material'] for m in self.bundles[role]['meshes']} | {C.ROLES[role]['shoe']}
                self.assertEqual({g['material'] for g in garments}, worn)
                # Winter's 1837 picture is permission-only: reference in prose, never a garment source.
                self.assertFalse([s for s in sources if 'winter' in s])

    def test_the_potawatomi_children_keep_their_review_and_removal_flags(self):
        for role, r in C.ROLES.items():
            v = self.variants[role]
            with self.subTest(role):
                if r.get('native'):
                    self.assertIs(v['review_required'], True)
                    self.assertIs(v['touches_removal'], True)
                    self.assertGreater(len(v['review_reason']), 80)
                    self.assertGreater(len(v['touches_removal_reason']), 80)
                    self.assertNotEqual(v['review_reason'], v['touches_removal_reason'])
                    self.assertEqual(v['reference_summary']['research'], 'docs/RESEARCH/people-1812-3467/day.json')
                    for m in C.MATERIALS[role]:
                        for word in ('paint', 'feather', 'bonnet', 'war', 'plume', 'silver', 'bead'):
                            self.assertNotIn(word, m)
                    stripped = copy.deepcopy(v); stripped.pop('touches_removal')
                    with self.assertRaisesRegex(ValueError, 'review'):
                        C.prepare_child_assembly(ROOT, self.recipes[role], stripped, self.bodies[role])
                else:
                    self.assertNotIn('review_required', v)

    def test_layers_stand_in_order(self):
        bones = {b['name']: b for b in self.bodies['child_girl_1812']['skeleton']}
        girl = self.mesh['child_girl_1812']
        waist = girl['frock_bodice']['receipt']['waist_y_m']
        n = 0
        for x in (-.04, 0., .04):
            for y in (waist-.05, waist-.12, waist-.2):
                za, zs = front_z(girl['pinafore_apron'], x, y), front_z(girl['frock_skirt'], x, y)
                if za is not None and zs is not None:
                    self.assertGreater(za, zs+.002, (x, y)); n += 1
            for y in (waist+.03, waist+.07):
                zb, zd = front_z(girl['pinafore_bib'], x, y), front_z(girl['frock_bodice'], x, y)
                if zb is not None and zd is not None:
                    self.assertGreater(zb, zd+.002, (x, y)); n += 1
        self.assertGreaterEqual(n, 8)
        boy = self.mesh['child_boy_1812']
        band = boy['skeleton_trousers_band']['receipt']
        y = (band['bottom_y_m']+band['top_y_m'])/2
        self.assertGreater(front_z(boy['skeleton_trousers_band'], 0., y), front_z(boy['skeleton_jacket'], 0., y))
        self.assertGreater(max(p[2] for p in boy['shirt_collar']['positions_m']), 0.)
        # The skirt and tail are lofted clear of the standing body.
        for role, name in (('child_girl_1812', 'frock_skirt'), ('child_toddler_1812', 'frock_skirt'),
                           ('potawatomi_boy_1812', 'calico_shirt_tail'), ('potawatomi_girl_1812', 'calico_blouse_skirt')):
            r = self.mesh[role][name]['receipt']
            self.assertGreaterEqual(r['standing_body_core_clearance_m'], C.TAILORING[role][
                {'frock_skirt': 'skirt', 'calico_shirt_tail': 'tail', 'calico_blouse_skirt': 'peplum'}[name]]['ease']-1e-9)
        # The chest relief (nipples through the cloth) is lowered onto the cloth's local surface.
        for role, name in (('child_boy_1812', 'skeleton_jacket'), ('child_girl_1812', 'frock_bodice'),
                           ('child_toddler_1812', 'frock_bodice'), ('potawatomi_boy_1812', 'calico_shirt'),
                           ('potawatomi_girl_1812', 'calico_blouse')):
            self.assertGreater(self.mesh[role][name]['receipt']['drape']['affected_vertices'], 10, role)

    def test_skirts_are_skinned_to_the_legs_below_the_waist(self):
        for role, name in (('child_girl_1812', 'frock_skirt'), ('child_toddler_1812', 'frock_skirt'),
                           ('potawatomi_girl_1812', 'wrapped_skirt')):
            m = self.mesh[role][name]
            waist = m['receipt']['waist_y_m']
            low = [w for p, w in zip(m['positions_m'], m['weights']) if p[1] < waist-.25]
            self.assertTrue(low, role)
            self.assertTrue(all(any(b.startswith(('thigh', 'calf')) for b in w) for w in low), role)

    def test_the_baked_walk_is_scaled_to_the_child_leg(self):
        for role, r in C.ROLES.items():
            body = self.bodies[role]
            w = C.child_walk(body)
            leg = C._leg({b['name']: b for b in body['skeleton']})
            with self.subTest(role):
                self.assertAlmostEqual(w['scale'], leg/C.ADULT_LEG_M)
                self.assertAlmostEqual(w['speed_m_s'], .6*w['scale'])
                self.assertAlmostEqual(w['stride_m']/leg, .6*1.2/C.ADULT_LEG_M)
                self.assertTrue(.3 < w['scale'] < .7)
        self.assertLess(C.child_walk(self.bodies['child_toddler_1812'])['speed_m_s'],
                        C.child_walk(self.bodies['child_boy_1812'])['speed_m_s'])

    def test_refuses_changed_inputs(self):
        role = 'child_girl_1812'
        cases = [('tailoring', lambda r: r['child_components']['tailoring']['skirt'].update(ease=.05), 'tailoring'),
                 ('body', lambda r: r['child_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['child_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(garment_outer__pinafore_linen_1812=[1, 0, 0, 1]), 'colour'),
                 ('date', lambda r: r.update(scene_date='1813-08-14'), 'scene')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipes[role]); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    C.prepare_child_assembly(ROOT, recipe, self.variants[role], self.bodies[role])
        other = copy.deepcopy(self.variants[role]); other['body_input'] = C.BODIES['male_8'][0]
        with self.assertRaises(ValueError):
            C.prepare_child_assembly(ROOT, self.recipes[role], other, self.bodies['child_boy_1812'])

    def test_each_asset_is_no_heavier_than_the_private(self):
        web = ROOT/'assets/humans/web'
        for role in C.ROLES:
            for lod in range(4):
                mine = web/f'{role}.lod{lod}.glb'
                with self.subTest(role=role, lod=lod):
                    self.assertTrue(mine.is_file(), mine)
                    self.assertLessEqual(mine.stat().st_size, (web/f'private_first_infantry_1812.lod{lod}.glb').stat().st_size)

    def test_skin_and_hair_are_the_period_studies_own(self):
        soldier = json.loads((ROOT/'data/humans/recipes/soldier_1812.json').read_text())
        for role, recipe in self.recipes.items():
            self.assertEqual(recipe['hair_component'], soldier['hair_component'], role)
            self.assertEqual(recipe['lod_ratios'], soldier['lod_ratios'], role)


if __name__ == '__main__':
    unittest.main(verbosity=1)
