# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure scope and real exporter wiring controls; no BPy simulation/execution."""
import ast
import copy
from pathlib import Path
import unittest
from human_cloth_microtexture import JOSEPH, MATERIALS, woven_tangent_required

ROOT = Path(__file__).resolve().parents[1]


def normal_binding(source):
    return {'material': source+'__woven_near', 'normal_mapped': True,
            'marker': {'version': 1, 'source_material': source, 'profile': MATERIALS[source],
                       'runtime_weave': 'portable_maps_replace_common_fabric'}}


class TangentExportControls(unittest.TestCase):
    def test_each_actual_cloth_profile_needs_real_tangents_only_on_joseph_near(self):
        for material in MATERIALS:
            binding = normal_binding(material)
            for asset in (JOSEPH, 'bardwell_otis_1835', 'flynn_martin_1835', 'fixture_adult'):
                for lod in range(4):
                    self.assertEqual(woven_tangent_required(asset, lod, [binding]),
                                     asset == JOSEPH and lod < 2, (asset, lod, material))
        self.assertFalse(woven_tangent_required(JOSEPH, 0, []))

    def test_missing_normal_binding_or_wrong_marker_never_changes_default_export(self):
        source = next(iter(MATERIALS))
        binding = normal_binding(source)
        for key, value in [('normal_mapped', False), ('normal_mapped', None),
                           ('material', 'skin'), ('marker', None)]:
            changed = copy.deepcopy(binding); changed[key] = value
            self.assertFalse(woven_tangent_required(JOSEPH, 0, [changed]), key)
        for key, value in [('version', True), ('version', 2), ('source_material', 'skin'),
                           ('profile', 'unknown'), ('runtime_weave', 'unmarked')]:
            changed = copy.deepcopy(binding); changed['marker'][key] = value
            self.assertFalse(woven_tangent_required(JOSEPH, 0, [changed]), key)
        self.assertFalse(woven_tangent_required(JOSEPH, True, [binding]))

    def test_only_selected_bindings_control_flag(self):
        ordinary = {'material': 'garment_upper__shirt_linen', 'normal_mapped': True}
        self.assertFalse(woven_tangent_required(JOSEPH, 0, [ordinary]))
        self.assertTrue(woven_tangent_required(JOSEPH, 0, [ordinary, normal_binding(next(iter(MATERIALS)))]))
        # A marked near material elsewhere in the master cannot affect a far export.
        self.assertFalse(woven_tangent_required(JOSEPH, 3, [normal_binding(next(iter(MATERIALS)))]))

    def test_real_export_call_uses_selected_policy_without_changing_contract_settings(self):
        tree = ast.parse((ROOT/'tools/human_export.py').read_text())
        exports = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and ast.unparse(n.func) == 'bpy.ops.export_scene.gltf']
        self.assertEqual(len(exports), 1)
        options = {k.arg: k.value for k in exports[0].keywords if k.arg}
        decision = options['export_tangents']
        self.assertIsInstance(decision, ast.Call)
        self.assertEqual(ast.unparse(decision.func), 'selected_woven_tangents')
        self.assertEqual([ast.unparse(a) for a in decision.args], ['asset_id', 'lod', 'meshes'])
        for key, expected in [('use_selection', True), ('export_texcoords', True),
                              ('export_normals', True), ('export_apply', False),
                              ('export_skins', True), ('export_extras', True)]:
            self.assertEqual(ast.literal_eval(options[key]), expected, key)

    def test_actual_root_and_parented_worker_paths_share_that_exporter(self):
        shell = (ROOT/'tools/human_export.sh').read_text()
        workflow = (ROOT.parents[1]/'.github/workflows/chicago-4d-humans.yml').read_text()
        control = (ROOT/'tools/human_hierarchy_control.py').read_text()
        self.assertIn('--python tools/human_export.py -- "$SCRATCH/lods"', shell)
        self.assertIn('--python tools/human_export.py -- "$control/raw"', workflow)
        self.assertIn('mesh.data is not data', control)  # existing actual source-data preservation guard
        self.assertNotIn('export_scene.gltf', control)


if __name__ == '__main__':
    unittest.main()
