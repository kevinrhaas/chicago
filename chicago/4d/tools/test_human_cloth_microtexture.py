# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure periodic-surface, metric-calibration and bounded-image-cost controls."""
import hashlib
import json
import math
import re
from pathlib import Path
import unittest
import zlib
from human_cloth_microtexture import SIZE, TILE_M, calibration, map_pixels, memory_cost, relief, requested_near, JOSEPH, MATERIALS


class TextileControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = {(kind, channel): map_pixels(kind, channel, (.12, .09, .065, 1), .9)
                    for kind in ('linen', 'wool') for channel in ('color', 'orm', 'normal')}

    def test_only_joseph_can_explicitly_enable_the_existing_workflow_study(self):
        recipe=json.loads((Path(__file__).resolve().parents[1]/'data/humans/recipes/worker_1835.json').read_text())
        self.assertEqual({v['id'] for v in recipe['proof_variants']}, {JOSEPH, 'bardwell_otis_1835', 'flynn_martin_1835'})
        self.assertTrue(all(not requested_near(v) for v in recipe['proof_variants']))
        for name in (JOSEPH, 'bardwell_otis_1835', 'flynn_martin_1835'):
            self.assertFalse(requested_near({'id': name}))
        self.assertTrue(requested_near({'id': JOSEPH}, True))
        self.assertTrue(requested_near({'id': JOSEPH, 'authoring_studies': {'woven_cloth_near_v1': True}}))
        for name in ('bardwell_otis_1835', 'flynn_martin_1835', 'unknown'):
            with self.assertRaisesRegex(ValueError, 'Joseph-only'):
                requested_near({'id': name}, True)
            with self.assertRaisesRegex(ValueError, 'Joseph-only'):
                requested_near({'id': name, 'authoring_studies': {'woven_cloth_near_v1': True}})
        with self.assertRaises(ValueError):
            requested_near({'id': JOSEPH, 'authoring_studies': {'woven_cloth_near_v1': 'true'}})

    def test_near_material_variants_keep_actual_portable_contract_slots(self):
        contract=json.loads((Path(__file__).resolve().parents[1]/'data/humans/contract.json').read_text())
        slots=contract['materials']
        pattern=re.compile(slots['name_pattern'])
        known=set(slots['required']) | set(slots['optional'])
        for original in MATERIALS:
            near=original+'__woven_near'
            self.assertEqual(pattern.fullmatch(original).group('slot'), pattern.fullmatch(near).group('slot'))
            self.assertIn(pattern.fullmatch(near).group('slot'), known)

    def test_periodic_height_and_derivative_and_distinct_cloths(self):
        for kind in ('linen', 'wool'):
            for u, v in ((0., .123), (.329, .751), (.998, .004)):
                self.assertAlmostEqual(relief(kind, u, v), relief(kind, u+1, v), places=15)
                self.assertAlmostEqual(relief(kind, u, v), relief(kind, u, v+1), places=15)
                e = 1e-6
                left = (relief(kind, u+e, v)-relief(kind, u-e, v))/(2*e)
                right = (relief(kind, u+1+e, v)-relief(kind, u+1-e, v))/(2*e)
                self.assertAlmostEqual(left, right, places=10)
        self.assertNotEqual(self.maps['linen', 'normal'], self.maps['wool', 'normal'])

    def test_actual_pixels_finite_deterministic_and_normals_unit_length(self):
        for (kind, channel), pixels in self.maps.items():
            self.assertEqual(len(pixels), SIZE*SIZE*4)
            self.assertTrue(all(math.isfinite(x) and 0 <= x <= 1 for x in pixels))
            self.assertEqual(set(pixels[3::4]), {1.})
            self.assertGreater(max(pixels[1::4])-min(pixels[1::4]), .001)
            if channel == 'normal':
                for i in range(0, len(pixels), 4):
                    self.assertAlmostEqual(sum((2*pixels[i+j]-1)**2 for j in range(3)), 1., places=6)
                    self.assertGreater(pixels[i+2], .5)
            if channel == 'orm':
                self.assertEqual(set(pixels[0::4]), {1.})
                self.assertEqual(set(pixels[2::4]), {0.})
                self.assertAlmostEqual(sum(pixels[1::4])/(SIZE*SIZE), .9, places=6)
        self.assertEqual(self.maps['linen', 'color'], map_pixels('linen', 'color', (.12, .09, .065, 1), .9))

    def test_color_is_encoded_once_without_material_factor(self):
        for kind in ('linen', 'wool'):
            pixels = self.maps[kind, 'color']
            for channel, color in enumerate((.12, .09, .065)):
                self.assertAlmostEqual(sum(pixels[channel::4])/(SIZE*SIZE), color, places=7)

    def test_measured_uv_repeat_scales_with_source_and_keeps_metric_period(self):
        positions = [(0, 0, 0), (2, 0, 0), (0, 2, 0)]
        uv = [(0, 0), (1, 0), (0, 1)]
        metric = calibration([(positions, uv)])
        self.assertAlmostEqual(metric['surface_area_m2'], 2)
        self.assertAlmostEqual(metric['uv_area'], .5)
        self.assertAlmostEqual(metric['uv_repeat'], 62.5)
        self.assertAlmostEqual(2/metric['uv_repeat'], TILE_M)
        larger = calibration([([[2*x for x in p] for p in positions], uv)])
        self.assertAlmostEqual(larger['uv_repeat'], 2*metric['uv_repeat'])
        with self.assertRaisesRegex(ValueError, 'no actual'):
            calibration([])
        for wrong in [([(0, 0, 0)]*3, uv), (positions, [(0, 0)]*3), (positions, [(0, 0), (1, 0), (0, float('nan'))])]:
            with self.assertRaises(ValueError):
                calibration([wrong])

    def test_two_near_lods_stay_bounded_and_far_adds_zero_images(self):
        four, three = memory_cost(4), memory_cost(3)
        self.assertEqual(four['image_count'], 10)
        self.assertEqual(three['image_count'], 8)
        self.assertEqual(four['rgba8_base_bytes'], 655360)
        self.assertEqual(four['rgba8_mip_bytes_per_near_lod'], 873800)
        self.assertLess(four['net_mip_bytes_both_near_lods'], 1024**2)
        self.assertEqual(four['far_lod_increment_bytes'], 0)
        for args in [('velvet', 'color'), ('linen', 'height')]:
            with self.assertRaises(ValueError):
                map_pixels(*args)
        with self.assertRaises(ValueError):
            map_pixels('linen', 'color', size=2560)


if __name__ == '__main__':
    result = unittest.main(exit=False)
    if result.result.wasSuccessful():
        records = {}
        for key, pixels in TextileControls.maps.items():
            raw8 = bytes(round(max(0., min(1., v))*255) for v in pixels)
            records['/'.join(key)] = {'float_pixel_sha256': hashlib.sha256(pixels.tobytes()).hexdigest(),
                                      'rgba8_bytes': len(raw8), 'rgba8_zlib_bytes': len(zlib.compress(raw8)),
                                      'scope': 'pure generated pixels; not Blender PNG/export verification'}
        print(json.dumps({'maps': records, 'three_material_budget': memory_cost(3), 'four_material_budget': memory_cost(4)}, sort_keys=True))
    raise SystemExit(0 if result.result.wasSuccessful() else 1)
