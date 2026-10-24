#!/usr/bin/env python3
"""Runtime flag consumption cannot be hidden as an unbuilt master attribute."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from flag_form_contract import (  # noqa: E402
    FLAG_FORM_FIELDS, FLAG_READER, compiled_form_attributes, flag_form_fields,
)
import validate  # noqa: E402


class FlagFormContract(unittest.TestCase):
    def test_actual_renderer_declares_and_reads_only_three_flag_fields(self):
        self.assertEqual(flag_form_fields(ROOT), FLAG_FORM_FIELDS)

    def test_new_runtime_fields_compile_without_false_unbuilt_labels(self):
        form = {k: {'value': True, 'confidence': 'reconstructed', 'note': 'Working choice',
                    'sources': [], 'internal': 'not a card field'} for k in FLAG_FORM_FIELDS}
        expected = {k: {a: v for a, v in claim.items() if a != 'internal'} for k, claim in form.items()}
        self.assertEqual(compiled_form_attributes(form, ROOT), expected)
        self.assertTrue(all('geometry' not in a for a in expected.values()))
        structures = {'roof': {'id': 'roof', 'archetype': 'frame_tavern',
                              'phases': [{'id': 'p', 'form': form}]}}
        with patch.object(validate, 'ROOT', ROOT):
            self.assertEqual(validate.unbuilt_values(structures, {'frame_tavern': frozenset()}), [])
            report = validate.Report()
            validate.check_geometry_declarations(structures, {'frame_tavern': frozenset()}, report)
            self.assertFalse(report.errors, report.errors)
            bad = copy.deepcopy(structures)
            bad['roof']['phases'][0]['form']['unknown_roof_feature'] = {'value': True, 'confidence': 'reconstructed'}
            report = validate.Report()
            validate.check_geometry_declarations(bad, {'frame_tavern': frozenset()}, report)
            self.assertTrue(any('unknown_roof_feature' in e for e in report.errors))

    def test_compiler_attributes_are_visible_to_existing_sidecar_read_gate(self):
        form = {key: {"value": True, "confidence": "reconstructed", "note": "working"}
                for key in FLAG_FORM_FIELDS}
        attributes = compiled_form_attributes(form, ROOT)
        shape = {"phase": None, "target_date": None,
                 "attributes": {key: {k: None for k in a} for key, a in attributes.items()}}
        reads = {field for _, field in validate.sidecar_field_reads((ROOT / FLAG_READER).read_text(), shape)}
        self.assertTrue({"attributes."+key for key in FLAG_FORM_FIELDS} <= reads)
        self.assertTrue({"phase", "target_date"} <= reads)

    def test_legacy_fort_sidecar_attribute_content_unchanged(self):
        for name in ('fort_dearborn_flagstaff', 'first_fort_dearborn_flagstaff'):
            record = json.loads((ROOT / 'data/structures' / f'{name}.json').read_text())
            for phase in record['phases']:
                form = phase.get('form', {})
                old = {key: {k: v for k, v in a.items() if k in
                       ('value', 'confidence', 'sources', 'note', 'geometry')} for key, a in form.items()}
                self.assertEqual(compiled_form_attributes(form, ROOT), old)

    def test_runtime_fields_cannot_claim_absent_or_simplified(self):
        for state in ('absent', 'simplified'):
            with self.subTest(state=state), self.assertRaises(ValueError):
                compiled_form_attributes({'flag_anchor': {'value': {}, 'geometry': state}}, ROOT)

    def test_missing_or_dishonest_renderer_is_a_compiler_and_validator_error(self):
        actual = (ROOT / FLAG_READER).read_text()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            file = root / FLAG_READER
            file.parent.mkdir(parents=True)
            for text in ('', actual.replace('at.flag_anchor', 'at.unused_anchor'),
                         actual.replace('"flag_anchor"]', '"flag_anchor", "imaginary_feature"]')):
                file.write_text(text)
                with self.subTest(source=text[:20]):
                    with self.assertRaises(ValueError):
                        compiled_form_attributes({'flag_anchor': {'value': {}}}, root)
                    with patch.object(validate, 'ROOT', root):
                        report = validate.Report()
                        validate.check_geometry_declarations({'roof': {'archetype': 'frame_tavern',
                            'phases': [{'id': 'p', 'form': {'flag_anchor': {'value': {}}}}]}},
                            {'frame_tavern': frozenset()}, report)
                        self.assertTrue(report.errors)


if __name__ == '__main__':
    unittest.main()
