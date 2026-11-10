# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure refusal/framing controls using the real recipe; no BPy or mocked renders."""
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest

from human_library_stills import ROOT, SIZE, VIEWS, framing, validate_identity, validate_paths, verify_outputs


class AssemblyStillControls(unittest.TestCase):
    def setUp(self):
        self.recipe = json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_text())

    def metadata(self, variant):
        return {'asset_id': variant['id'], 'skeleton': 'c4d_humanoid_v1', 'grade': 'reconstructed',
                'recipe': 'data/humans/recipes/worker_1835.json',
                **{key: variant[key] for key in ('person_reference_id', 'person_reference_scene', 'person_reference_grade')}}

    def test_actual_three_recipe_identities(self):
        self.assertEqual(len(self.recipe['proof_variants']), 3)
        for variant in self.recipe['proof_variants']:
            receipt = validate_identity(self.metadata(variant), variant['id'])
            self.assertEqual(receipt['person_reference_id'], variant['person_reference_id'])
            self.assertEqual(len(receipt['recipe_sha256']), 64)

    def test_wrong_asset_or_person_or_grade_refused(self):
        variant = self.recipe['proof_variants'][0]
        metadata = self.metadata(variant)
        changes = ({'asset_id': 'invented'}, {'person_reference_id': 'invented'},
                   {'person_reference_scene': '1904'}, {'person_reference_grade': 'attested'},
                   {'grade': 'attested'}, {'skeleton': 'invented'},
                   {'recipe': 'data/humans/recipes/../../../../AGENTS.md'})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_identity({**metadata, **change}, variant['id'])

    def test_missing_variant_in_actual_recipe_refused(self):
        metadata = self.metadata(self.recipe['proof_variants'][0])
        metadata['asset_id'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'actual recipe variant'):
            validate_identity(metadata, 'invented')

    def test_every_view_fits_same_portrait_frame_with_margin(self):
        # Wide off-origin assembly exercises the horizontal rather than height limit.
        points = list(itertools.product((2.1, 3.5), (-4.0, -3.5), (.08, 1.88)))
        result = framing(points)
        target, scale = result['target_m'], result['ortho_scale_m']
        self.assertEqual(target, [2.8, -3.75, .98])
        for _, angle in VIEWS:
            radians = math.radians(angle)
            for x, y, z in points:
                screen_x = (x-target[0])*math.cos(radians)+(y-target[1])*math.sin(radians)
                self.assertLess(abs(screen_x), scale*SIZE[0]/SIZE[1]/2)
                self.assertLess(abs(z-target[2]), scale/2)

    def test_invalid_geometry_bounds_refused(self):
        bad = ([], [(0, 0, 0)], [(0, 0, 0), (1, 1, float('nan'))],
               [(0, 0, 0), (1, float('inf'), 1.8)], [(0, 0, 0), (1, 1, 180)],
               [(0, 0, 0), (0, 1, 1.8)], [(0, 0), (1, 1)])
        for points in bad:
            with self.subTest(points=points), self.assertRaises(ValueError):
                framing(points)

    def test_missing_master_and_existing_outputs_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            master = directory/'canonical.blend'
            with self.assertRaisesRegex(ValueError, 'existing .blend'):
                validate_paths(master, directory/'renders')
            # Only path validation reads this sentinel; no Blender loading is simulated.
            master.write_bytes(b'source sentinel')
            self.assertEqual(validate_paths(master, directory/'renders')[0], master)
            with self.assertRaisesRegex(ValueError, 'separate'):
                validate_paths(master, master)
            (directory/'front.png').write_bytes(b'stale output')
            with self.assertRaisesRegex(ValueError, 'existing still outputs'):
                validate_paths(master, directory)
            with self.assertRaisesRegex(ValueError, 'missing rendered output'):
                verify_outputs(directory/'renders')
            with self.assertRaisesRegex(ValueError, 'invalid PNG'):
                verify_outputs(directory)


if __name__ == '__main__':
    unittest.main()
