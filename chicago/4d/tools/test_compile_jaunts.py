#!/usr/bin/env python3
"""T-1253: executable refusal cases, reachable-state safety and JSON-only expansion."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import audit_confidence
from compile_jaunts import Compiler, ROOT, packed
from compile_source_use import Compiler as SourceCompiler

class JauntTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = Compiler()
        cls.fixtures = ROOT / 'data/jaunts/_fixtures'

    def setUp(self):
        self.doc = json.loads((self.fixtures / 'fixture-branch.json').read_text())

    def bad(self, text):
        with self.assertRaisesRegex(ValueError, text): self.compiler.validate(self.doc)

    def test_real_pilot_available_and_deterministic(self):
        a, errors = self.compiler.compile()
        self.assertFalse(errors)
        self.assertEqual(a, self.compiler.compile()[0])
        row = next(r for r in json.loads(a['catalog.json'])['jaunts'] if r['id'] == 'new-in-chicago')
        self.assertEqual((row['id'], row['availability'], row['stop_count']), ('new-in-chicago', 'available', 5))
        self.assertEqual(row['destinations'][1]['id'], 'hogan_store')
        content = json.loads(a['new-in-chicago.json'])
        self.assertTrue(all(c['citation'] and 'note' not in c for c in content['citations']))

    def test_fixtures_add_without_code_and_malformed_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            for source in self.fixtures.iterdir():
                name = source.name.removesuffix('.invalid')
                (Path(tmp) / name).write_bytes(source.read_bytes())
            files, errors = self.compiler.compile(tmp)
            self.assertEqual(len(errors), 1)
            self.assertIn('malformed.json', errors[0])
            self.assertEqual(len(json.loads(files['catalog.json'])['jaunts']), 4)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            walk = (self.fixtures / 'fixture-walk.json').read_text()
            (out / 'fixture-walk.json').write_text(walk)
            before, _ = self.compiler.compile(out)
            (out / 'fixture-branch.json').write_text(json.dumps(self.doc))
            after, errors = self.compiler.compile(out)
            self.assertFalse(errors)
            self.assertEqual(before['fixture-walk.json'], after['fixture-walk.json'])
            self.assertEqual(set(after) - set(before), {'fixture-branch.json'})
            self.assertEqual(len(json.loads(after['catalog.json'])['jaunts']), 2)

    def test_27_entry_catalog_budget(self):
        pilot = json.loads((ROOT / 'data/jaunts/new-in-chicago.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(27):
                row = copy.deepcopy(pilot); row['id'] = f'new-in-chicago-{i:02}'
                (Path(tmp) / (row['id'] + '.json')).write_text(json.dumps(row))
            files, errors = self.compiler.compile(Path(tmp))
            self.assertFalse(errors)
            self.assertLessEqual(len(files['catalog.json'].encode()), 30000)

    def test_dangling_id(self):
        self.doc['stops'][0]['destination']['id'] = 'missing'; self.bad('dangling')

    def test_excluded_date(self):
        self.doc['stops'][0]['destination']['id'] = 'cook_county_courthouse_1835'; self.bad('excluded date')

    def test_missing_source(self):
        self.doc['evidence'][0]['sources'] = ['missing']; self.bad('dangling source')

    def test_missing_locator(self):
        self.doc['evidence'][0].pop('locator'); self.bad('locator')

    def test_missing_reasoning_or_liberty(self):
        self.doc['evidence'][-2].pop('reasoning'); self.bad('reasoning')
        self.setUp();self.doc['evidence'][-1].pop('liberty');self.bad('liberty')

    def test_unknown_liberty(self):
        self.doc['liberties'] = ['L-missing-jaunt']; self.bad('unknown liberty')

    def test_duplicate_ids(self):
        self.doc['stops'].append(copy.deepcopy(self.doc['stops'][0])); self.bad('duplicate stop')
        self.setUp();self.doc['evidence'].append(copy.deepcopy(self.doc['evidence'][0]));self.bad('duplicate evidence')

    def test_bounds_checked_across_branch_states(self):
        self.doc['stops'][1]['choices'] = [{'id': 'spend', 'label': 'Spend again', 'consequence': 'Too much.', 'effects': [{'op':'inc','var':'money','value':-90}]}]
        self.bad('unbounded effect')  # second spend exceeds the 75 remaining, not the initial 100

    def test_static_set_and_undeclared_effect(self):
        effect = self.doc['stops'][0]['choices'][0]['effects'][0]
        effect.update(op='set', value=101);self.bad('unbounded set')
        effect.update(var='absent');self.bad('undeclared effect')

    def test_money_integer_and_cents(self):
        self.doc['variables']['money']['unit'] = 'count';self.bad('integer cents')
        self.setUp();self.doc['variables']['money']['initial'] = 1.5;self.bad('schema')

    def test_no_viable_choice(self):
        for choice in self.doc['stops'][0]['choices']:
            choice['when'] = {'var':'money','op':'<','value':0}
        self.bad('no viable choice')

    def test_unreachable_ending(self):
        self.doc['endings'][0]['when'] = {'var':'money','op':'<','value':0};self.bad('unreachable ending')

    def test_cycle_including_false_branch(self):
        self.doc['stops'][1]['next'] = 'arrival';self.bad('cycle')

    def test_explicit_previous_is_navigation_not_completion(self):
        self.doc['stops'][1]['choices'] = [{'id':'back','label':'Previous','consequence':'Return without reapplying effects.','next':'Previous'}]
        self.compiler.validate(self.doc)
        self.doc['stops'][1].pop('next');self.bad('no viable choice')

    def test_inventory_capacity_and_conditions(self):
        self.doc['inventory']['capacity'] = 0;self.bad('capacity')
        self.setUp();self.doc['stops'][0]['choices'][0]['when'] = {'all':[{'any':[{'var':'money','op':'>=','value':25}]},{'not':{'has':'receipt'}}]}
        self.compiler.validate(self.doc)
        self.doc['stops'][0]['choices'][0]['when'] = {'has':'unknown'};self.bad('undeclared item')

    def test_dangling_links_and_next(self):
        self.doc['stops'][0]['links'][0]['id'] = 'missing';self.bad('dangling')
        self.setUp();self.doc['stops'][0]['choices'][0]['next'] = 'missing';self.bad('dangling next')

    def test_plain_text_and_word_count(self):
        self.doc['stops'][0]['text'] = '<script>alert(1)</script>';self.bad('schema')
        self.doc['stops'][0]['text'] = 'Too short.';self.bad('25–60')
        self.setUp();self.doc['onEnter'] = 'run()';self.bad('schema')

    def test_review_unavailable_with_reason(self):
        self.doc.update(review_required=True);self.bad('needs reason')
        self.doc['review_reason'] = 'Awaiting consultation on this narrative.'
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / (self.doc['id'] + '.json')).write_text(json.dumps(self.doc))
            files, errors = self.compiler.compile(tmp)
            self.assertFalse(errors)
            row = json.loads(files['catalog.json'])['jaunts'][0]
            self.assertEqual(row['availability'], 'unavailable')
            self.assertIn('consultation', row['reason'])

    def test_person_business_location_and_date(self):
        c = copy.deepcopy(self.compiler)
        c.refs['person']['fixture-person'] = {'lives_at':'sauganash_hotel'}
        c.refs['business']['fixture-business'] = {'present_at_scene_date':True,'where':{'kind':'premises','structure_id':'hogan_store','from':'1834-01-01'}}
        for kind in ('person','business'):
            self.doc['stops'][0]['destination'] = {'kind':kind,'id':f'fixture-{kind}'}
            c.validate(self.doc)
        c.refs['business']['fixture-business']['where']['from'] = '1835-08-01'
        with self.assertRaisesRegex(ValueError, 'excluded date'):c.validate(self.doc)
        self.doc['stops'][0]['destination'] = {'kind':'person','id':'fixture-person'}
        c.refs['person']['fixture-person']['lives_at'] = None
        with self.assertRaisesRegex(ValueError, 'unlocated'):c.validate(self.doc)

    def test_anchor_intersection_topic_and_review_inheritance(self):
        c = copy.deepcopy(self.compiler)
        for kind in ('anchor', 'intersection'):
            self.doc['stops'][0]['destination'] = {'kind':kind,'id':next(iter(c.refs[kind]))}
            self.doc['stops'][0]['links'] = [{'kind':'topic','id':'sources','label':'Sources'}]
            c.validate(self.doc)
        c.refs['person']['held-person'] = {'lives_at':'sauganash_hotel'}
        c.refs['structure']['sauganash_hotel']['review_required'] = True
        self.doc['stops'][0]['destination'] = {'kind':'person','id':'held-person'}
        self.assertIn('sauganash_hotel requires review', c.validate(self.doc))

    def test_confidence_audit_reads_jaunt_reasoning(self):
        pilot = json.loads((ROOT / 'data/jaunts/new-in-chicago.json').read_text())
        path = ROOT / 'data/sidecars/1835/jaunts/new-in-chicago.json'
        with patch.object(audit_confidence, 'load_sidecars', return_value=[(path,pilot)]):
            self.assertFalse(audit_confidence.audit()[0])
            pilot['evidence'][-2].pop('reasoning')
            self.assertTrue(any('no reasoning' in e for e in audit_confidence.audit()[0]))

    def test_every_sourced_claim_registered(self):
        pilot = json.loads((ROOT / 'data/jaunts/new-in-chicago.json').read_text())
        c = SourceCompiler(ROOT)
        c.record('jaunt claims','jaunt',pilot['id'],pilot['evidence'],'scene','evidence')
        edges = [e for rows in c.edges.values() for e in rows.values()]
        expected = {f'evidence[{e["id"]}]' for e in pilot['evidence'] if e['sources']}
        self.assertEqual({e['claim'] for e in edges}, expected)
        self.assertTrue(all(e['entity_type']=='jaunt' and e['entity_id']==pilot['id'] for e in edges))

if __name__ == '__main__': unittest.main()
