"""Independent mathematical and protected-stream checks for the anatomy source path.

These do not qualify native rendering or deformation of a changed horse. The
full exported standing field/contact proof remains a separate release gate.
"""

import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/authored/transport/horse_standing"
SPEC = importlib.util.spec_from_file_location("horse_anatomy", SOURCE / "generate_anatomy_v1.py")
ANATOMY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANATOMY)


class AnatomySource(unittest.TestCase):
    def test_analytical_jacobian_agrees_with_finite_differences(self):
        control = {"centre_m": [0.1, 1.5, 1.3], "radii_m": [0.1, 0.08, 0.2], "delta_m": [0.002, 0.005, -0.003]}
        for point in [(0.1, 1.5, 1.3), (0.12, 1.52, 1.28), (0.4, 1.7, 1.3)]:
            _, jacobian = ANATOMY.field(point, [control])
            for axis in range(3):
                before, after = list(point), list(point)
                before[axis] -= 1e-7
                after[axis] += 1e-7
                a, _ = ANATOMY.field(before, [control])
                b, _ = ANATOMY.field(after, [control])
                for component in range(3):
                    self.assertAlmostEqual((b[component] - a[component]) / 2e-7,
                                           jacobian[component][axis], delta=2e-8)

    def test_normal_is_perpendicular_to_transformed_tangents(self):
        matrix = [[1.0, 0.3, 0.2], [0.1, 1.2, 0.0], [0.0, 0.2, 0.9]]
        normal, determinant = ANATOMY.normal_transform((0.0, 0.0, 1.0), matrix)
        self.assertGreater(determinant, 0)
        for axis in (0, 1):
            tangent = [matrix[i][axis] for i in range(3)]
            self.assertAlmostEqual(sum(a * b for a, b in zip(normal, tangent)), 0, delta=1e-12)
        with self.assertRaisesRegex(ValueError, "reverses"):
            ANATOMY.normal_transform((0, 1, 0), [[-1, 0, 0], [0, 1, 0], [0, 0, 1]])

    def test_actual_parent_boundary_and_meaningful_rejections(self):
        parent = (SOURCE / ANATOMY.PARENT_FILE).read_bytes()
        recipe = json.loads((SOURCE / "anatomy-v1-recipe.json").read_text())
        candidate, receipt = ANATOMY.derive(parent, recipe)
        source_doc, source_bin = ANATOMY.read_glb(parent)
        changed_doc, changed_bin = ANATOMY.read_glb(candidate)
        self.assertNotEqual(parent, candidate)
        self.assertGreater(sum(len(x["changed_vertex_ids"]) for x in receipt["meshes"]), 0)
        # Rebuild the allowed byte mask independently from the selected accessor
        # layouts, not the generator's own declared changed-byte ranges.
        allowed = set()
        for index in [199, 200, 203, 204]:
            acc = source_doc["accessors"][index]
            view = source_doc["bufferViews"][acc["bufferView"]]
            start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
            for i in range(acc["count"]):
                allowed.update(range(start + i * view.get("byteStride", 12), start + i * view.get("byteStride", 12) + 12))
        self.assertEqual(len(source_bin), len(changed_bin))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(source_bin, changed_bin))))
        # Eye POSITION207/NORMAL208/UV10 and images/weights/binds/clip are outside
        # that mask. Verify their actual complete bytes separately as well.
        for index in [10, 201, 202, 205, 206, 207, 208, 209, 210]:
            acc = source_doc["accessors"][index]
            view = source_doc["bufferViews"][acc["bufferView"]]
            start, length = view.get("byteOffset", 0), view["byteLength"]
            self.assertEqual(source_bin[start:start + length], changed_bin[start:start + length])
        for mesh, index in [(0, 199), (1, 203)]:
            before = ANATOMY.float_stream(source_doc, source_bin, index)[3]
            after = ANATOMY.float_stream(changed_doc, changed_bin, index)[3]
            self.assertTrue(all(a == b for a, b in zip(before, after) if a[1] <= 0.2))
        for invalid in [dict(recipe, controls=[]), dict(recipe, parent_sha256="0" * 64)]:
            with self.assertRaises(ValueError):
                ANATOMY.derive(parent, invalid)
        bad = bytearray(parent)
        bad[-10] ^= 1
        with self.assertRaisesRegex(ValueError, "source drift"):
            ANATOMY.derive(bytes(bad), recipe)
        invalid = copy.deepcopy(recipe)
        invalid["controls"][0]["centre_m"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "Invalid"):
            ANATOMY.derive(parent, invalid)
        invalid = copy.deepcopy(recipe)
        invalid["controls"][0]["centre_m"] = [0.15, 0.05, 0.33]
        invalid["controls"][0]["radii_m"] = [0.3, 0.3, 0.3]
        with self.assertRaisesRegex(ValueError, "protected actual foot"):
            ANATOMY.derive(parent, invalid)


if __name__ == "__main__":
    unittest.main()
