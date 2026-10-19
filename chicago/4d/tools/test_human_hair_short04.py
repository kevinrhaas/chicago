"""Actual source fitting, provenance and texture-registration contracts; no BPy."""
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
from PIL import Image
from human_hair_short04 import fit

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / 'assets/authored/humans/hair_short04'


class HairSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / 'data/humans/recipes/worker_1835.json').read_text())['hair_component']
        cls.bodies = {age: json.loads((ROOT / f'assets/authored/humans/makehuman_hm08/prepared_adult_{age}.json').read_text()) for age in [25, 35]}

    def test_actual_bodies_have_finite_normalized_existing_skin_bindings(self):
        for age, body in self.bodies.items():
            with self.subTest(age=age):
                mesh, texture, report = fit(body, self.config, ROOT)
                self.assertEqual((len(mesh['positions_m']), len(mesh['triangles'])), (991, 1050))
                self.assertEqual(texture.name, self.config['texture'])
                names = {bone['name'] for bone in body['skeleton']}
                for point, uv, weights in zip(mesh['positions_m'], mesh['uvs'], mesh['weights']):
                    self.assertTrue(all(math.isfinite(v) for v in point))
                    self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1 for v in uv))
                    self.assertTrue(0 < len(weights) <= 4 and set(weights) <= names)
                    self.assertTrue(all(math.isfinite(v) and v > 0 for v in weights.values()))
                    self.assertAlmostEqual(math.fsum(weights.values()), 1, places=12)
                self.assertLessEqual(report['max_clamped_negative_weight_mass'], .00002)
                self.assertEqual(report['max_pruned_weight_mass'], 0)

    def test_repeatable_fit_leaves_body_and_original_assets_unchanged(self):
        body = self.bodies[25]
        before = copy.deepcopy(body)
        files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FOLDER.iterdir()}
        first = fit(body, self.config, ROOT)
        self.assertEqual(first, fit(body, self.config, ROOT))
        self.assertEqual(body, before)
        self.assertEqual(files, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FOLDER.iterdir()})

    def test_decoded_padding_preserves_every_source_pixel_and_periodic_rows(self):
        with Image.open(FOLDER / 'short04_diffuse.png') as source, Image.open(FOLDER / self.config['texture']) as padded:
            self.assertEqual(source.size, (2048, 2048))
            self.assertEqual(padded.size, (2048, 2057))
            original = source.convert('RGBA').tobytes()
            derivative = padded.convert('RGBA').tobytes()
        row = 2048 * 4
        self.assertEqual(derivative[8 * row:2056 * row], original)
        self.assertEqual(derivative[:8 * row], original[-8 * row:])
        self.assertEqual(derivative[2056 * row:], original[:row])

    def test_unverified_texture_and_material_settings_refuse(self):
        for texture in ['../other.png', '/tmp/other.png', 'missing.png', 'short04_diffuse.png']:
            with self.subTest(texture=texture), self.assertRaisesRegex(ValueError, 'selected hair texture'):
                fit(self.bodies[25], {**self.config, 'texture': texture}, ROOT)
        for key in ['roughness', 'alpha_cutoff']:
            for value in [True, None, '0.4', float('nan'), float('inf'), -.1, 1.1]:
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, 'material setting'):
                    fit(self.bodies[25], {**self.config, key: value}, ROOT)
        with self.assertRaisesRegex(ValueError, 'unsafe hair component directory'):
            fit(self.bodies[25], {**self.config, 'directory': '../outside'}, ROOT)

    def test_missing_actual_proxy_reference_refuses(self):
        lines = (FOLDER / 'short04.mhclo').read_text().splitlines()
        start = next(i for i, line in enumerate(lines) if line.split() and line.split()[0] == 'verts')
        row = next(fields for line in lines[start + 1:]
                   if len(fields := line.split()) == 9 and fields[0].isdigit())
        required = int(row[0])
        body = copy.deepcopy(self.bodies[25])
        replacement = max(i for mesh in body['meshes'] for i in mesh['source_vertex_indices']) + 1
        for mesh in body['meshes']:
            mesh['source_vertex_indices'] = [replacement if i == required else i for i in mesh['source_vertex_indices']]
        with self.assertRaisesRegex(ValueError, 'missing body source vertices'):
            fit(body, self.config, ROOT)

    def test_changed_manifest_or_source_bytes_refuse(self):
        with self.assertRaisesRegex(ValueError, 'manifest hash mismatch'):
            fit(self.bodies[25], {**self.config, 'source_manifest_sha256': '0' * 64}, ROOT)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / self.config['directory']
            target.parent.mkdir(parents=True)
            shutil.copytree(FOLDER, target)
            with (target / 'short04.obj').open('ab') as stream:
                stream.write(b'\n# explicit provenance regression mutation\n')
            with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
                fit(self.bodies[25], self.config, directory)


if __name__ == '__main__':
    unittest.main()
