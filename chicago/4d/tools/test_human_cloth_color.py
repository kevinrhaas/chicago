# SPDX-License-Identifier: GPL-3.0-or-later
"""Byte-quantized IEC round trips and preserved inherited/data inputs, not BPy."""
import hashlib
import math
import unittest
from human_cloth_microtexture import SIZE, COLOR_INPUT_SPACE, map_pixels, linear_to_srgb


def decode(encoded):
    return encoded/12.92 if encoded <= .04045 else ((encoded+.055)/1.055)**2.4


class ClothColorControls(unittest.TestCase):
    def test_iec_low_dark_and_full_range_quantization_intervals(self):
        self.assertAlmostEqual(linear_to_srgb(.0031308), .040449936, places=10)
        self.assertAlmostEqual(linear_to_srgb(.18), .46135612950044164, places=12)
        for value in [0, .00001, .001, .0031308, .045, .055, .063, .13, .14, .15, .16, .18, 1]:
            encoded=linear_to_srgb(value);q=round(encoded*255)
            self.assertLessEqual(decode(max(0,q-.5)/255)-1e-12, value)
            self.assertGreaterEqual(decode(min(255,q+.5)/255)+1e-12, value)
        for bad in [-.1,1.1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):linear_to_srgb(bad)

    def test_actual_old_wool_factors_survive_mean_byte_roundtrip(self):
        # Verified old8745 sourceLOD0 c8975fec... actual baseColorFactors.
        palettes={'waistcoat':(.14,.15,.14,1), 'trousers':(.18,.16,.13,1), 'jacket':(.045,.055,.063,1)}
        for garment,color in palettes.items():
            pixels=map_pixels('wool','color',color,.9)
            for channel,target in enumerate(color[:3]):
                codes=[round(v*255) for v in pixels[channel::4]]
                lo=sum(decode(max(0,q-.5)/255) for q in codes)/(SIZE*SIZE)
                hi=sum(decode(min(255,q+.5)/255) for q in codes)/(SIZE*SIZE)
                actual=sum(decode(q/255) for q in codes)/(SIZE*SIZE)
                self.assertLessEqual(lo,target,(garment,channel,actual))
                self.assertGreaterEqual(hi,target,(garment,channel,actual))
                self.assertTrue(all(math.isfinite(v) for v in [lo,hi,actual]))

    def test_inherited_linen_and_all_noncolor_pixel_bytes_stay_exact(self):
        # Frozen pure input arrays from the pre-correction source controls. Actual
        # PNG equality remains a native worker check, not a claim of this test.
        expected={('linen','color'):'a6c13c3c9b698639b4e064765120a5ed5f218dafb7b400ebe6998e97d6fb110a',
                  ('linen','normal'):'961327d5fd155448ef3475251a91643e95bf9a0d1c66e939125268bd2d19ddc4',
                  ('linen','orm'):'7cf87b9fee01f347b60f272cd09e85f7d8c4300a5f1c0fb1c713d7eb23fc1ca9',
                  ('wool','normal'):'0cd091799ffa82408a909d6755332cc2bf83970eb79c02a8d9c97fe181065bab',
                  ('wool','orm'):'c44ab18c5393318a87f3ccbe5f6cf59c610d67b59de59f77e3d19efad5d5ed95'}
        for (kind,channel),digest in expected.items():
            self.assertEqual(hashlib.sha256(map_pixels(kind,channel,(.12,.09,.065,1),.9).tobytes()).hexdigest(),digest)
        self.assertEqual(COLOR_INPUT_SPACE,{'linen':'legacy_encoded_srgb','wool':'linear_factor'})


if __name__=='__main__':unittest.main()
