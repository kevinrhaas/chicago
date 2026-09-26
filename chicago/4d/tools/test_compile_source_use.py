#!/usr/bin/env python3
"""Fixture tests for source-use semantics, publication boundaries and determinism."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import audit_confidence
from compile_source_use import Compiler, compile_outputs, NEWSPAPERS


class SourceUseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for sid, tier in [('map', 1), ('memory', 3), ('unused', 4), ('paper', 1)]:
            self.put(f'data/sources/{sid}.json', dict(
                id=sid, citation=f'{sid} citation', type='map', date='1834', tier=tier,
                url=f'https://example.org/{sid}', archived_url='', author='INTERNAL AUTHOR',
                rights_status='check_required', verified=True,
                what_it_supplies=['geometry'], note='INTERNAL NOTE'))
        self.put('data/scenes/1835.json', {'target_date': '1835-07-01', 'terrain_epoch': 'e1834'})
        self.put('data/sidecars/1835/index.json', {'structures': []})

    def put(self, path, value):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value))

    def rows(self, c):
        return {r['source_id']: r for r in json.loads(c.outputs()['index.json'])['sources']}

    def test_exact_typed_edges_mixed_confidence_and_counts(self):
        c = Compiler(self.root)
        c.record('structures', 'structure', 'house', {
            'position': {'sources': ['map', 'memory'], 'confidence': 'attested', 'locator': 'p. 4'},
            'roof': {'sources': ['map'], 'confidence': 'reconstructed'}}, 'scene')
        edges = json.loads(c.outputs()['map.json'])['edges']
        self.assertEqual(edges, [
            dict(source_id='map', entity_type='structure', entity_id='house', claim='position', confidence='attested', locator='p. 4', use='scene'),
            dict(source_id='map', entity_type='structure', entity_id='house', claim='roof', confidence='reconstructed', locator=None, use='scene')])
        self.assertEqual(self.rows(c)['map']['counts'], {'entities': 1, 'claims': 2})
        self.assertEqual(self.rows(c)['memory']['counts'], {'entities': 1, 'claims': 1})
        self.assertEqual(self.rows(c)['unused']['use'], 'unused')
        self.assertEqual(json.loads(c.outputs()['unused.json'])['edges'], [])

    def test_dangling_source_refused(self):
        with self.assertRaisesRegex(ValueError, 'unresolved source missing'):
            Compiler(self.root).record('flora', 'flora', 'zone', {'sources': ['missing']}, 'scene')

    def paper(self):
        self.put('data/research/newspapers/corpus.json', {'issues': [
            {'id': 'paper_1835_07_01', 'source_id': 'paper', 'publication': 'Daily Paper', 'date': '1835-07-01'},
            {'id': 'paper_1835_07_02', 'source_id': 'paper', 'publication': 'Daily Paper', 'date': '1835-07-02'}]})
        for day in ['01', '02']:
            self.put(f'data/research/newspapers/extracted/issue{day}.json', {
                'issue_id': f'paper_1835_07_{day}', 'claims': [
                    {'id': 'c1', 'locator': {'issue_page': 3, 'column': 2, 'artifact_role': 'INTERNAL',
                                           'text_path': 'data/research/private.txt'}}]})

    def test_newspaper_alias_and_registered_citation_join(self):
        self.paper()
        c = Compiler(self.root)
        for sid in [NEWSPAPERS, 'paper']:
            c.record('businesses', 'business', 'shop', {'source_id': sid, 'tier': 'attested',
                     'claim_ids': ['paper_1835_07_02#c1', 'paper_1835_07_01#c1']}, 'scene')
        edges = json.loads(c.outputs()['paper.json'])['edges']
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0]['locator'], dict(issue_id='paper_1835_07_01',
            issue_date='1835-07-01', publication='Daily Paper', claim_id='paper_1835_07_01#c1', page=3, column=2))
        self.assertEqual(self.rows(c)['paper']['counts'], {'entities': 1, 'claims': 1})
        self.assertEqual(json.loads(c.outputs()['paper.json'])['source']['citation'], 'paper citation')

    def test_alias_needs_resolvable_claim(self):
        for ids in [[], ['missing#c1']]:
            with self.assertRaises(ValueError):
                Compiler(self.root).record('businesses', 'business', 'shop',
                    {'source_id': NEWSPAPERS, 'claim_ids': ids}, 'scene')

    def test_public_partition_and_no_research_paths(self):
        c = Compiler(self.root)
        c.record('decisions', 'decision', 'd1', {'sources': ['map'],
            'locator': 'data/research/private.pdf', 'note': 'data/research/private.pdf'}, 'research')
        blob = ''.join(c.outputs().values())
        for forbidden in ['INTERNAL', 'rights_status', 'verified', 'data/research/', 'check_required']:
            self.assertNotIn(forbidden, blob)
        self.assertEqual(json.loads(c.outputs()['map.json'])['source']['what_it_supplies'], ['geometry'])
        self.assertEqual(json.loads(c.outputs()['map.json'])['edges'][0]['locator'], None)

    def test_unknown_and_conjectural_do_not_gain_confidence(self):
        c = Compiler(self.root)
        for grade, expected in [('unknown', 'reconstructed'), ('conjectural', 'reconstructed'), ('documented', 'attested')]:
            c.record('terrain', 'terrain', grade, {'sources': ['map'], 'confidence': grade}, 'research')
            edge = next(e for e in json.loads(c.outputs()['map.json'])['edges'] if e['entity_id'] == grade)
            self.assertEqual(edge['confidence'], expected)

    def test_use_precedence_retains_all_edges_and_type_distinct_entities(self):
        c = Compiler(self.root)
        for kind, use in [('structure', 'other_scene'), ('person', 'scene'), ('decision', 'research')]:
            c.record(kind, kind, 'same_id', {'sources': ['map']}, use)
        self.assertEqual(self.rows(c)['map']['use'], 'scene')
        self.assertEqual(self.rows(c)['map']['counts']['entities'], 3)
        self.assertEqual(json.loads(c.outputs()['map.json'])['uses'], ['scene', 'other_scene', 'research'])

    def test_adapters_and_deterministic_output(self):
        self.put('data/structures/house.json', {'id': 'house', 'phases': [
            {'id': 'now', 'documented_range': {'from': '1830-01-01', 'to': '1840-01-01'},
             'roof': {'sources': ['map'], 'confidence': 'inferred'}},
            {'id': 'later', 'documented_range': {'from': '1841-01-01', 'to': '1880-01-01'},
             'roof': {'sources': ['memory'], 'confidence': 'attested'}}]})
        self.put('data/sidecars/1835/index.json', {'structures': [{'id': 'house', 'sidecar': 'sidecars/1835/house.json'}]})
        self.put('data/sidecars/1835/house.json', {'citations': [{'source_id': 'map'}]})
        self.put('data/sidecars/1835/people.json', {'people': [{'id': 'p1', 'household': 'h1'}]})
        self.put('data/residents/households/h1.json', {'id': 'h1', 'sources': ['map'], 'persons': [
            {'id': 'p1', 'grade': 'reconstructed', 'age': {'sources': ['memory']}}]})
        self.put('data/businesses/biz_shop.json', {'id': 'shop', 'present_at_scene_date': False, 'sources': ['map']})
        self.put('data/flora/zones/zone.json', {'id': 'zone', 'plantable_in_scene': False, 'sources': ['map']})
        self.put('data/exclusions.json', {'excluded': [{'id': 'omitted', 'sources': ['memory']}]})
        self.put('data/terrain/epochs.json', {'epochs': [{'id': 'e1834', 'sources': ['map']}, {'id': 'e1812', 'sources': ['memory']}]})
        self.put('data/fauna/zones/birds.json', {'id': 'birds', 'in_modelled_extent': True, 'sources': ['memory']})
        self.put('data/liberties.json', {'liberties': [{'id': 'L1', 'sources': ['map']}]})
        a, report = compile_outputs(self.root)
        b, report2 = compile_outputs(self.root)
        self.assertEqual(a, b)
        self.assertEqual(report, report2)
        edges = [e for name, body in a.items() if name != 'index.json' for e in json.loads(body)['edges']]
        self.assertIn(('person', 'p1', 'scene', 'reconstructed'),
                      [(e['entity_type'], e['entity_id'], e['use'], e['confidence']) for e in edges])
        self.assertIn('other_scene', {e['use'] for e in edges})
        self.assertEqual(next(e['use'] for e in edges if e['entity_id'] == 'shop'), 'exclusion')
        self.assertEqual(next(e['use'] for e in edges if e['entity_id'] == 'zone'), 'research')
        self.assertEqual(next(e['use'] for e in edges if e['entity_id'] == 'e1834'), 'scene')
        self.assertEqual(next(e['use'] for e in edges if e['entity_id'] == 'e1812'), 'other_scene')
        self.assertEqual(next(e['use'] for e in edges if e['entity_id'] == 'birds'), 'scene')
        self.assertEqual(next(e['confidence'] for e in edges if e['entity_id'] == 'L1'), 'reconstructed')

    def test_confidence_audit_validates_backlinks_and_still_rejects_authored_errors(self):
        self.put('data/exclusions.json', {'excluded': [{'id': 'x', 'sources': ['map'], 'confidence': 'attested'}]})
        outputs, _ = compile_outputs(self.root)
        for name, body in outputs.items():
            self.put('data/sidecars/1835/sources/' + name, json.loads(body))
        with patch.object(audit_confidence, 'ROOT', self.root):
            self.assertEqual(audit_confidence.audit()[0], [])
            forged = json.loads(outputs['map.json'])
            forged['edges'][0]['confidence'] = 'inferred'
            self.put('data/sidecars/1835/sources/map.json', forged)
            self.assertTrue(any('differs from its authored claim' in e for e in audit_confidence.audit()[0]))
            self.put('data/sidecars/1835/ordinary.json', {'id': 'ordinary', 'confidence': 'attested'})
            self.assertTrue(any('attested with no source' in e for e in audit_confidence.audit()[0]))

    def test_compiled_cited_structure_requires_backlink(self):
        self.put('data/sidecars/1835/index.json', {'structures': [{'id': 'absent', 'sidecar': 'sidecars/1835/absent.json'}]})
        self.put('data/sidecars/1835/absent.json', {'citations': [{'source_id': 'map'}]})
        with self.assertRaisesRegex(ValueError, 'cited current structure has no edge'):
            compile_outputs(self.root)


if __name__ == '__main__':
    unittest.main()
