# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual opt-in source-consumer and identity controls; never a Blender claim."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import unittest

from human_dress_components import prepare_dress_assembly, BODY_SHA256
from human_teamster_blend import validate_input, resolve_person_reference
from human_base_prepare import prepare

ROOT = Path(__file__).resolve().parent.parent


def canonical_recipe_paths(source, recipe, dress):
    """Conservative literal-key contract for actual canonical build() branches.

    This reads real builder source, not a copied mini-builder or fake BPy API.
    Known dress/wardrobe branches and their short-circuit expressions are selected;
    unknown branches are both inspected. Nested function bodies are not executed
    merely by defining them. Dynamic/indirect access and BPy/export correctness
    remain outside this bounded source-interface check.
    """
    paths = set()
    unknown = object()
    flags = {'dress': dress, 'wardrobe': 'modular_wardrobe' in recipe}

    def truth(node):
        if isinstance(node, ast.Name):
            return flags.get(node.id, unknown)
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            value = truth(node.operand)
            return unknown if value is unknown else not value
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.left, ast.Constant) and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == 'recipe':
            if isinstance(node.ops[0], ast.In):
                return node.left.value in recipe
            if isinstance(node.ops[0], ast.NotIn):
                return node.left.value not in recipe
        if isinstance(node, ast.BoolOp):
            values = [truth(value) for value in node.values]
            if isinstance(node.op, ast.And):
                return False if any(v is False for v in values) else True if all(v is True for v in values) else unknown
            return True if any(v is True for v in values) else False if all(v is False for v in values) else unknown
        return unknown

    class Reads(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            return  # Definitions are not calls; excludes the male-only shell helper.

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_Lambda = visit_FunctionDef

        def visit_If(self, node):
            self.visit(node.test)
            value = truth(node.test)
            for child in (node.body if value is True else node.orelse if value is False else node.body+node.orelse):
                self.visit(child)

        def visit_IfExp(self, node):
            self.visit(node.test)
            value = truth(node.test)
            for child in ([node.body] if value is True else [node.orelse] if value is False else [node.body, node.orelse]):
                self.visit(child)

        def visit_BoolOp(self, node):
            for child in node.values:
                self.visit(child)
                value = truth(child)
                if (isinstance(node.op, ast.And) and value is False) or (isinstance(node.op, ast.Or) and value is True):
                    break

        def visit_Subscript(self, node):
            path = []
            value = node
            while isinstance(value, ast.Subscript) and isinstance(value.slice, ast.Constant) and isinstance(value.slice.value, str):
                path.append(value.slice.value); value = value.value
            if isinstance(value, ast.Name) and value.id == 'recipe':
                paths.add(tuple(reversed(path)))
            self.generic_visit(node)

    build = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'build')
    reads = Reads()
    for statement in build.body:
        reads.visit(statement)
    return paths


def absent_recipe_paths(source, recipe, dress):
    missing = []
    for path in sorted(canonical_recipe_paths(source, recipe, dress)):
        value = recipe
        try:
            for key in path:
                value = value[key]
        except (KeyError, TypeError):
            missing.append(path)
    return missing


class DressComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads((ROOT/'data/humans/recipes/adult_dress_1835.json').read_text())
        cls.variant = cls.recipe['proof_variants'][0]
        cls.bodypath = ROOT/cls.variant['body_input']
        cls.raw = cls.bodypath.read_bytes(); cls.body = json.loads(cls.raw)

    def test_actual_canonical_source_consumer_preserves_body(self):
        before = copy.deepcopy(self.body)
        bundle = prepare_dress_assembly(ROOT, self.recipe, self.variant, self.body)
        self.assertEqual(before, self.body)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), BODY_SHA256)
        self.assertEqual(bundle['skeleton'], self.body['skeleton'])
        self.assertEqual([p['name'] for p in bundle['meshes']],
                         ['plain_closed_bodice', 'gathered_ankle_skirt', 'separate_plain_apron', 'closed_low_shoes'])
        self.assertGreater(bundle['meshes'][1]['receipt']['standing_body_core_clearance_m']-.0015, .015)
        for mesh in bundle['meshes']:
            for face in mesh['triangles']:
                self.assertEqual(len(set(face)), 3)
        self.assertFalse(bundle['meshes'][1]['receipt']['walking_or_seated_accepted'])

    def test_unqualified_pose_or_source_changes_are_refused(self):
        for key, bad, message in [('production_eligible', True, 'promotion'),
                                  ('walking_seated_or_photo_accepted', True, 'promotion'),
                                  ('body_sha256', '0'*64, 'body source')]:
            recipe = copy.deepcopy(self.recipe); recipe['dress_components'][key] = bad
            with self.assertRaisesRegex(ValueError, message):
                prepare_dress_assembly(ROOT, recipe, self.variant, self.body)
        variant = copy.deepcopy(self.variant); variant['person_reference_id'] = 'invented_new_person'
        with self.assertRaisesRegex(ValueError, 'existing reconstructed Mary Flynn'):
            prepare_dress_assembly(ROOT, self.recipe, variant, self.body)
        body = copy.deepcopy(self.body); body['meshes'][0]['positions_m'][0][0] += .001
        with self.assertRaisesRegex(ValueError, 'anatomy'):
            prepare_dress_assembly(ROOT, self.recipe, self.variant, body)

    def test_real_person_and_contract_source_bounds(self):
        contract = json.loads((ROOT/'data/humans/contract.json').read_text())
        bones = validate_input(self.body, contract)
        self.assertEqual(len(bones), 56)
        person = resolve_person_reference(self.variant, ROOT)
        self.assertEqual((person['name'], person['age_band'], person['presence']), ('Mary Flynn', '20-29', 'present'))
        # Original male resident recipes retain their unchanged identity path.
        male = json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_text())
        for variant in male['proof_variants']:
            self.assertEqual(resolve_person_reference(variant, ROOT)['name'], variant['reference_summary']['name'])
        wrong = copy.deepcopy(self.variant); wrong['person_reference_grade'] = 'attested'
        with self.assertRaisesRegex(ValueError, 'grade differs'):
            resolve_person_reference(wrong, ROOT)
        wrong = copy.deepcopy(self.variant); wrong['person_reference_record'] = 'data/residents/households/hh_rc_unknown.json'
        with self.assertRaisesRegex(ValueError, 'explicit existing Mary Flynn'):
            resolve_person_reference(wrong, ROOT)

    def test_explicit_female_manifest_and_unsafe_selection(self):
        source = ROOT/'assets/authored/humans/makehuman_hm08'
        # The original SOURCE.json remains complete and byte-identical; the
        # female preparation explicitly opts into its separate complete manifest.
        manifest = json.loads((source/'SOURCE.json').read_text())
        self.assertFalse(any('female' in row['path'] for row in manifest['files']))
        female = prepare(source, 1.65, source/'adult_female_25.recipe.json', 'SOURCE-female.json')
        encoded = (json.dumps(female, separators=(',', ':'))+'\n').encode()
        self.assertEqual(encoded, self.raw)
        for unsafe in ['../SOURCE.json', '/tmp/SOURCE.json', '', 'SOURCE.txt']:
            with self.assertRaisesRegex(ValueError, 'local JSON filename'):
                prepare(source, 1.65, source/'adult_female_25.recipe.json', unsafe)

    def test_actual_canonical_recipe_paths_and_original_defect(self):
        source = (ROOT/'tools/human_teamster_blend.py').read_text()
        male = json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_text())
        self.assertEqual(absent_recipe_paths(source, self.recipe, True), [])
        self.assertEqual(absent_recipe_paths(source, male, False), [])
        # Put the actual obsolete pre-LOD reads back into the real builder source.
        # The dress recipe must catch both, while the original male recipe still
        # satisfies them. This is not an assertion that those names are banned.
        marker = "    shoulder_y = bones['upperarm_l']['head_m'][1]"
        self.assertEqual(source.count(marker), 1)
        broken = source.replace(marker, "    waist = recipe['waist_height_fraction']*height/scale\n    hem = recipe['shirt_hem_fraction']*height/scale\n"+marker)
        self.assertEqual(set(absent_recipe_paths(broken, self.recipe, True)),
                         {('waist_height_fraction',), ('shirt_hem_fraction',)})
        self.assertEqual(absent_recipe_paths(broken, male, False), [])
        missing = copy.deepcopy(self.recipe); missing.pop('lod_ratios')
        self.assertIn(('lod_ratios',), absent_recipe_paths(source, missing, True))


if __name__ == '__main__':
    unittest.main()
