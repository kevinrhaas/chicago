#!/usr/bin/env python3
"""Mutation checks stay in memory; never alter the live gate's authored input."""
import copy
import json
import unittest
from check_loading_content import ROOT, validate
from compile_source_use import Compiler
class LoadingEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((ROOT / 'data/loading/statuses.json').read_text())
    def rejected(self, edit):
        doc = copy.deepcopy(self.doc); edit(doc['entries'])
        with self.assertRaises((AssertionError, KeyError)):
            validate(document=doc)
    def test_source_mismatch(self):
        self.rejected(lambda es: es[0].update(source_ids=['wright_1834']))
    def test_unknown_entity(self):
        self.rejected(lambda es: es[0]['entity'].update(id='invented_building'))
    def test_promotion(self):
        self.rejected(lambda es: next(e for e in es if e.get('fact',{}).get('confidence')=='inferred')['fact'].update(confidence='attested'))
    def test_duplicate_observation(self):
        def edit(es):es[1].update(entity=es[0]['entity'],fact=es[0]['fact'],source_ids=es[0]['source_ids'])
        self.rejected(edit)
    def test_backlinks(self):
        c=Compiler(ROOT);c.collect()
        edges=[e for group in c.edges.values() for e in group.values() if e['claim']=='loading_fact']
        facts=[e for e in self.doc['entries'] if e['kind']=='fact']
        self.assertEqual(len(edges),50)
        for fact in facts:
            edge=next(e for e in edges if e['entity_id']==fact['id'])
            self.assertEqual(edge['entity_type'],'decision')
            self.assertEqual(edge['confidence'],fact['fact']['confidence'])
            self.assertEqual(edge['locator'],fact['fact']['locator'])
            self.assertEqual(edge['source_id'],fact['source_ids'][0])
if __name__=='__main__':unittest.main()
