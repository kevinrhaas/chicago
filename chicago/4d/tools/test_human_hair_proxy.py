"""Cleared hm08 hair proxy fitting (T-3434): Mattie's bun hair, pinned, CC0, fitted, skinned; no BPy."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
from human_hair_proxy import fit

ROOT = Path(__file__).resolve().parent.parent


class HairProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recipe = json.loads((ROOT/'data/humans/recipes/adult_dress_1904.json').read_text())
        cls.config = recipe['hair_component']
        cls.body = json.loads((ROOT/recipe['proof_variants'][0]['body_input']).read_text())

    def test_the_bun_fits_her_head_and_skins_to_it(self):
        self.assertEqual(self.config['fitter'], 'mhclo_proxy')
        mesh, texture, report = fit(self.body, self.config, ROOT)
        self.assertEqual(texture.name, 'hair_bun_brown_dark_tie.png')
        self.assertEqual(len(mesh['triangles']), self.config['topology'][1])
        bones = {b['name']: b for b in self.body['skeleton']}
        eyes = [(a+b)/2 for a, b in zip(bones['eye_l']['head_m'], bones['eye_r']['head_m'])]
        names = set(bones)
        for p, uv, w in zip(mesh['positions_m'], mesh['uvs'], mesh['weights']):
            self.assertTrue(all(math.isfinite(v) for v in p))
            self.assertTrue(all(0 <= v <= 1 for v in uv))
            self.assertTrue(0 < len(w) <= 4 and set(w) <= names)
            self.assertAlmostEqual(math.fsum(w.values()), 1, places=12)
            # On the head: within 13 cm of the eyes' height, no further forward than the eyes,
            # and no more than 24 cm behind them (the bun).
            self.assertLess(abs(p[1]-eyes[1]), .13)
            self.assertLess(p[2]-eyes[2], .01)
            self.assertGreater(p[2]-eyes[2], -.24)
        # The bun stands well behind the back of the skull.
        self.assertLess(min(p[2] for p in mesh['positions_m'])-eyes[2], -.2)
        self.assertEqual(report['source']['license'], 'CC0-1.0')

    def test_pins_and_licence_refuse_substitutes(self):
        for change, message in [(dict(source_manifest_sha256='0'*64), 'manifest hash'),
                                (dict(texture='other.png'), 'manifest member'),
                                (dict(topology=[1, 1]), 'topology'),
                                (dict(roughness=2), 'within 0..1'),
                                (dict(directory='../hair_bun_brown'), 'unsafe')]:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, message):
                    fit(self.body, {**copy.deepcopy(self.config), **change}, ROOT)

    def test_the_red_tie_is_gone_from_the_derivative(self):
        from PIL import Image
        folder = ROOT/self.config['directory']
        src = Image.open(folder/'Hair_bun_brown.png').convert('RGB').resize((256, 256))
        out = Image.open(folder/self.config['texture']).convert('RGB').resize((256, 256))
        red = lambda im: sum(1 for r, g, b in im.getdata() if r > 2*g and r > 80)
        self.assertGreater(red(src), 500)
        self.assertLess(red(out), 20)


if __name__ == '__main__':
    unittest.main()
