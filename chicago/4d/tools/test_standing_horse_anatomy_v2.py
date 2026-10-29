"""Meaningful current-source boundary, topology and differential-normal tests.

No browser or standing-motion acceptance is inferred from these source tests.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
SOURCE = APP / 'assets/authored/transport/horse_standing'
sys.path.insert(0, str(SOURCE))
import generate_anatomy_v2 as anatomy


class AnatomySourceV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = (SOURCE / anatomy.base.PARENT_FILE).read_bytes()
        cls.recipe = json.loads((SOURCE / 'anatomy-v2-recipe.json').read_text())
        cls.sidecar = json.loads((APP / 'tools/fixtures/horse-anatomy-parent-sidecar-v1.json').read_text())
        cls.candidate, cls.receipt = anatomy.derive(cls.parent, cls.recipe, cls.sidecar, APP / 'data/sources')
        cls.old, cls.oldbin = anatomy.base.read_glb(cls.parent)
        cls.new, cls.newbin = anatomy.base.read_glb(cls.candidate)

    def test_gated_field_analytical_jacobian(self):
        controls = self.recipe['controls']
        for point in [(0.112, 1.510, 1.342), (0.112, 1.521, 1.342), (0.125, 1.54, 1.33), (0, 1, 0)]:
            _, matrix = anatomy.gated_field(point, controls)
            for axis in range(3):
                lo, hi = list(point), list(point)
                lo[axis] -= 1e-7
                hi[axis] += 1e-7
                a, _ = anatomy.gated_field(lo, controls)
                b, _ = anatomy.gated_field(hi, controls)
                for k in range(3):
                    self.assertAlmostEqual((b[k] - a[k]) / 2e-7, matrix[k][axis], delta=4e-8)

    def test_actual_parent_rig_images_and_eye_streams_are_protected(self):
        self.assertEqual(self.newbin[:len(self.oldbin)], self.oldbin)
        for key in ['nodes', 'skins', 'animations', 'images', 'textures', 'materials', 'samplers']:
            self.assertEqual(self.old.get(key), self.new.get(key))
        for mesh in [0, 2]:
            self.assertEqual(self.old['meshes'][mesh], self.new['meshes'][mesh])
        self.assertLessEqual(len(self.candidate), 4 * 1024 * 1024)
        self.assertNotEqual(self.parent, self.candidate)

    def test_all_faces_have_owned_children_and_real_ground_anchors(self):
        proof = self.receipt['hoof_refinement']
        mapping = proof['source_face_to_children']
        self.assertEqual(len(mapping), 7390)
        children = [face for group in mapping for face in group]
        self.assertEqual(sorted(children), list(range(proof['new_triangles'])))
        self.assertGreater(proof['new_vertices'], proof['original_vertices'])
        self.assertGreater(self.receipt['serialized_minimum_parent_child_face_normal_dot'], 0)
        oldpos = anatomy.read_attribute(self.old, self.oldbin, 203)
        index = self.new['meshes'][1]['primitives'][0]['attributes']['POSITION']
        newpos = anatomy.read_attribute(self.new, self.newbin, index)
        for vertex in proof['ground_support_anchor_vertex_ids']:
            self.assertEqual(oldpos[vertex], newpos[vertex])
        self.assertTrue(proof['moved_ground_witness_vertex_ids'])
        self.assertFalse(proof['ground_witness_geometry_unchanged'])
        self.assertFalse(proof['fresh_loaded_deformation_contact_acceptance'])

    def test_original_skin_rows_retained_and_added_rows_have_four_influences(self):
        attrs = self.new['meshes'][1]['primitives'][0]['attributes']
        for semantic, oldindex in [('JOINTS_0', 205), ('WEIGHTS_0', 206)]:
            old = anatomy.read_attribute(self.old, self.oldbin, oldindex)
            new = anatomy.read_attribute(self.new, self.newbin, attrs[semantic])
            self.assertEqual(new[:len(old)], old)
        joints = anatomy.read_attribute(self.new, self.newbin, attrs['JOINTS_0'])
        weights = anatomy.read_attribute(self.new, self.newbin, attrs['WEIGHTS_0'])
        for js, ws in zip(joints, weights):
            self.assertEqual(len(js), 4)
            self.assertTrue(all(w >= 0 and math.isfinite(w) for w in ws))
            self.assertAlmostEqual(sum(ws), 1, delta=2e-7)
            self.assertTrue(all(0 <= j < 26 for j, w in zip(js, ws) if w))

    def test_selected_runtime_is_exact_canonical_recipe_output(self):
        spec = json.loads((APP / 'data/transport/parked/horse-sevket-sidecar.json').read_text())
        selected = (APP / 'renderers/web' / spec['runtime_asset']['file']).read_bytes()
        # The925 derivation remains an immutable supported source mode. The
        # explicit new socket mode has separate, stronger head ownership proof.
        self.assertEqual((SOURCE / 'horse-sevket-anatomy-v2.glb').read_bytes(), self.candidate)
        mode = spec['runtime_asset'].get('source_qualification_mode', 'anatomy_r3')
        if mode == 'upper_orbital_transition_v1':
            from test_standing_horse_upper_orbital import check_source_selection
            check_source_selection()
        elif mode == 'canonical_socket_interface_v1':
            from test_standing_horse_upper_lid import check_source_selection
            check_source_selection()
        else:
            self.assertEqual(mode, 'anatomy_r3')
            self.assertEqual(selected, self.candidate)
        self.assertEqual(anatomy.base.digest(selected), spec['runtime_asset']['sha256'])
        self.assertEqual(len(selected), spec['runtime_asset']['bytes'])
        self.assertEqual(spec['contact_mesh']['vertices'], self.receipt['hoof_refinement']['new_vertices'])

    def test_undeclared_source_and_parent_drift_rejected(self):
        invalid = copy.deepcopy(self.recipe)
        invalid['controls'][0]['source_ids'] = ['unresolved_anatomical_assertion']
        with self.assertRaisesRegex(ValueError, 'cleared source'):
            anatomy.derive(self.parent, invalid, self.sidecar, APP / 'data/sources')
        invalid_parent = bytearray(self.parent)
        invalid_parent[-20] ^= 1
        with self.assertRaisesRegex(ValueError, 'parent drift'):
            anatomy.derive(bytes(invalid_parent), self.recipe, self.sidecar, APP / 'data/sources')

    def test_static_crossing_interior_interval_and_boundary_controls(self):
        spec = importlib.util.spec_from_file_location('anatomy_crossings', APP / 'tools/transport/check_horse_anatomy_crossings.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        # Includes the independent counterexample where strict edge hits alone
        # missed a segment whose endpoints landed on both triangles' boundaries.
        checker.self_test()


if __name__ == '__main__':
    unittest.main()
