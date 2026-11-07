"""A 1904 house maid's dress on the shared female rig (T-3448): sourced, layered, skinned; no BPy.

Mary Reynolds's black work dress with white collar and cuffs, a white bib apron with frilled
straps tied in a bow behind, and a small white frilled cap (tools/human_maid_1904.py, recipe
data/humans/recipes/maid_1904.json).
"""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import human_gentleman_1904 as G
import human_maid_1904 as M

ROOT = Path(__file__).resolve().parent.parent
RECIPE = ROOT/M.RECIPE


def front_z(mesh, x, y):
    try:
        return G._surface_sample(mesh, x, y)[0]
    except ValueError:
        return None


def normals_cancel(mesh):
    """Faces whose reverse uses the very same vertices: their normals cancel and they shade as shards."""
    seen = {}
    for f in mesh['triangles']:
        key = frozenset(f)
        if key in seen and seen[key] != tuple(f):
            return True
        seen.setdefault(key, tuple(f))
    return False


class Maid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECIPE.read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.body = json.loads((ROOT/cls.variant['body_input']).read_text())
        cls.bundle = M.prepare_maid_assembly(ROOT, cls.recipe, cls.variant, cls.body)
        cls.mesh = {m['name']: m for m in cls.bundle['meshes']}
        cls.bones = {b['name']: b for b in cls.body['skeleton']}

    def test_every_piece_is_there_with_its_material_and_colour(self):
        self.assertEqual(set(self.mesh), {'maid_bodice', 'maid_skirt', 'maid_apron_skirt', 'apron_bib', 'apron_straps',
                                          'white_collar', 'white_cuffs', 'apron_strap_frills', 'apron_bow',
                                          'headwear_maid_cap'})
        for m in self.bundle['meshes']:
            self.assertIn(m['material'], self.recipe['colors_linear_rgba'], m['name'])
            self.assertIn(m['material'], M.MATERIALS, m['name'])
        slots = {m['material'].split('__')[0] for m in self.bundle['meshes']} | {'skin', 'eyes', 'footwear'}
        self.assertLessEqual({'skin', 'eyes', 'garment_upper', 'garment_lower', 'footwear'}, slots)
        self.assertEqual(self.bundle['shoe_material'], 'footwear__maid_shoes_black')
        # The dress is black and the apron, collar, cuffs and cap white.
        col = self.recipe['colors_linear_rgba']
        self.assertLess(max(col['garment_upper__maid_dress_black'][:3]), .05)
        self.assertGreater(min(col['garment_outer__maid_apron_white'][:3]), .6)

    def test_she_is_mary_reynolds_in_her_own_household_record(self):
        v = self.variant
        self.assertEqual((v['person_reference_id'], v['component_assembly'], v['person_reference_grade']),
                         ('pa1904_glessner_john_j_c1900_mary_reynolds', 'maid_1904_v1', 'inferred'))
        hh = json.loads((ROOT/v['person_reference_record']).read_text())
        person = next(p for p in hh['persons'] if p['id'] == v['person_reference_id'])
        self.assertEqual(person['occupation']['value'], 'house maid')
        # She stands in the 1904 town once, in this dress, at the service arch (T-3452).
        found = list((ROOT/'data/humans/instances').rglob('hi_*mary_reynolds*.json'))
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in found],
                         ['data/humans/instances/1904/hi_pa1904_glessner_john_j_c1900_mary_reynolds_1904.json'])
        inst = json.loads(found[0].read_text())
        self.assertEqual((inst['scene'], inst['person_id'], inst['appearance']['asset_id'], inst['display']),
                         ('1904', v['person_reference_id'], v['id'], 'shown'))
        self.assertIn(inst['id'], json.loads((ROOT/'data/humans/instances/1904/index.json').read_text())['instances'])

    def test_every_garment_carries_provenance(self):
        garments = self.recipe['maid_components']['garments']
        self.assertEqual(len(garments), 8)
        sources = set(self.recipe['sources'])
        for g in garments:
            p = g['provenance']
            self.assertIn(p['grade'], ('attested', 'inferred', 'reconstructed'), g['id'])
            self.assertTrue(p['source_ids'] and p['source_scope'] and p['liberty'], g['id'])
            self.assertLessEqual(set(p['source_ids']), sources, g['id'])
            self.assertIn(g['material'], M.MATERIALS, g['id'])
        self.assertNotIn('attested', {g['provenance']['grade'] for g in garments})

    def test_apron_lies_over_the_dress(self):
        bodice, bib = self.mesh['maid_bodice'], self.mesh['apron_bib']
        spine = self.bones['spine_02']['head_m'][1]
        n = 0
        for x in (0., .04, -.04, .07):
            for y in (spine+.02, spine+.08, spine+.14):
                zb, za = front_z(bodice, x, y), front_z(bib, x, y)
                if zb is not None and za is not None:
                    self.assertLess(zb+.002, za, (x, y)); n += 1
        self.assertGreaterEqual(n, 6)
        # The apron skirt stands off the dress skirt, row by row, and stops short of the hem.
        skirt, apron = self.mesh['maid_skirt'], self.mesh['maid_apron_skirt']
        segs = M.TAILORING['skirt']['segments']
        for p in apron['positions_m'][::11]:
            q = min(skirt['positions_m'][:segs*M.TAILORING['skirt']['rows']], key=lambda s: math.dist(s, p))
            self.assertGreater(math.hypot(p[0], p[2]), math.hypot(q[0], q[2]))
        self.assertGreater(min(p[1] for p in apron['positions_m']), min(p[1] for p in skirt['positions_m'])+.05)

    def test_skirt_and_apron_part_over_the_legs(self):
        half = abs(self.bones['thigh_l']['head_m'][0])
        waist = self.bones['spine_02']['head_m'][1]
        for name in ('maid_skirt', 'maid_apron_skirt'):
            m, wide = self.mesh[name], 0
            for p, w in zip(m['positions_m'], m['weights']):
                if p[2] > .05 and abs(p[0]) > 1.1*half+.01 and p[1] < waist-.35:   # the apron sits 8 mm out on the skirt's weights
                    side = 'l' if p[0] > 0 else 'r'
                    other = 'r' if side == 'l' else 'l'
                    self.assertGreater(w.get(f'thigh_{side}', 0)+w.get(f'calf_{side}', 0), .3, name)
                    self.assertEqual(w.get(f'thigh_{other}', 0)+w.get(f'calf_{other}', 0), 0, name)
                    wide += 1
            self.assertGreater(wide, 20, name)

    def test_cap_is_rigid_on_the_head_and_sits_on_the_hair(self):
        cap = self.mesh['headwear_maid_cap']
        self.assertTrue(cap['material'].startswith('headwear__'))
        self.assertTrue(all(w == {'head': 1.} for w in cap['weights']))
        eyes = self.bones['eye_l']['head_m'][1]
        self.assertGreater(min(p[1] for p in cap['positions_m']), eyes+.06)
        # On the crown, not floating: its lowest point within 2 cm of the top of the head.
        top = max(p[1] for p in self.body['meshes'][0]['positions_m'])
        self.assertLess(min(p[1] for p in cap['positions_m']), top+.02)

    def test_thin_pieces_shade_from_both_sides(self):
        for name in ('apron_strap_frills', 'apron_bow', 'headwear_maid_cap'):
            m = self.mesh[name]
            self.assertTrue(m['receipt']['double_sided'], name)
            self.assertFalse(normals_cancel(m), name)

    def test_refuses_changed_inputs(self):
        cases = [('tailoring', lambda r: r['maid_components']['tailoring']['skirt'].update(ease=.02), 'tailoring'),
                 ('body', lambda r: r['maid_components'].update(body_sha256='0'*64), 'body source'),
                 ('provenance', lambda r: r['maid_components']['garments'][0].update(provenance={'grade': 'attested'}), 'provenance'),
                 ('colour', lambda r: r['colors_linear_rgba'].update(headwear__maid_cap_white=[1, 0, 0, 1]), 'colour')]
        for name, change, message in cases:
            with self.subTest(name):
                recipe = copy.deepcopy(self.recipe); change(recipe)
                with self.assertRaisesRegex(ValueError, message):
                    M.prepare_maid_assembly(ROOT, recipe, self.variant, self.body)

    def test_skin_and_hair_are_the_pinned_woman_s_own(self):
        mattie = json.loads((ROOT/'data/humans/recipes/adult_dress_1904.json').read_text())
        self.assertEqual(self.recipe['skin_texture'], mattie['skin_texture'])
        self.assertEqual(self.recipe['hair_component'], mattie['hair_component'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
