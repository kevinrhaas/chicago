#!/usr/bin/env python3
"""Validate the authored loading library and its exact published evidence links."""
import json
import re
from collections import Counter
from pathlib import Path
import jsonschema
ROOT = Path(__file__).resolve().parents[1]
RANK = {'reconstructed': 0, 'conjectural': 0, 'inferred': 1, 'attested': 2, 'documented': 2}
MINIMUM = {'assess': 30, 'collect': 35, 'prepare': 40, 'resolve': 25, 'land': 28}

def validate(root=ROOT, document=None):
    data = root / 'data'
    doc = document if document is not None else json.loads((data / 'loading/statuses.json').read_text())
    jsonschema.validate(doc, json.loads((data / 'loading/schema.json').read_text()))
    entries = doc['entries']
    assert 160 <= len(entries) <= 250, 'expected 160–250 entries'
    assert len({e['id'] for e in entries}) == len(entries), 'duplicate ID'
    assert len({e['text'] for e in entries}) == len(entries), 'duplicate text'
    assert len(json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()) <= 60000, '60 KB budget'
    sources = {s['source_id']: s for s in json.loads((data / 'sidecars/1835/sources/index.json').read_text())['sources']}
    structure_ids = {s['id'] for s in json.loads((data / 'sidecars/1835/index.json').read_text())['structures']}
    phases, kinds = Counter(e['phase'] for e in entries), Counter(e['kind'] for e in entries)
    assert all(phases[p] >= n for p, n in MINIMUM.items()), f'phase minimums: {phases}'
    assert kinds['fact'] >= 50, 'at least 50 facts'
    assert 1 <= kinds['humor'] <= 2, 'one or two humor entries'
    fact_claims = set()
    for e in entries:
        assert not re.search(r'<[^>]*>|&(?:\w+|#\d+);', e['text']), f"markup: {e['id']}"
        assert '\n' not in e['text'], 'single plain-text card'
        refs = e.get('source_ids', [])
        assert all(s in sources and (data / f'sources/{s}.json').exists() for s in refs), f"source: {e['id']}"
        if e['kind'] == 'source':
            assert refs and all(sources[s]['use'] == 'scene' for s in refs), 'source cards need scene sources'
        if e['kind'] == 'humor':
            assert e['weight'] <= .001 and e['phase'] != 'land' and not refs and 'fact' not in e, 'humor cap'
        entity = e.get('entity')
        card = None
        if entity:
            kind, eid = entity['type'], entity['id']
            if kind == 'structure':
                assert eid in structure_ids, f'unknown structure {eid}'
                card = json.loads((data / f'sidecars/1835/{eid}.json').read_text())
            elif kind == 'flora':
                path = data / f'flora/zones/{eid}.json'
                assert path.exists() and json.loads(path.read_text()).get('plantable_in_scene'), f'unknown scene flora {eid}'
            else:
                raise AssertionError(f'unsupported entity type {kind}')
        if e['kind'] == 'build':
            assert entity, 'build cards require a real entity'
        if e['kind'] == 'fact':
            assert refs and card and e.get('source_label'), 'facts pair observation, source and entity'
            fact = e['fact']; loc = fact['locator']
            assert loc['sidecar'] == entity['id'], 'locator must refer to its own entity'
            attribute = card['attributes'][loc['attribute']]
            assert set(refs) <= set(attribute.get('sources', [])), 'fact cites an unrelated source'
            assert RANK[fact['confidence']] <= RANK[attribute['confidence']], 'fact promotes its evidence'
            claim = (entity['id'], loc['attribute'])
            assert claim not in fact_claims, 'same observation counted twice'
            fact_claims.add(claim)
            for sid in refs:
                edges = json.loads((data / f'sidecars/1835/sources/{sid}.json').read_text())['edges']
                assert any(x['entity_type'] == 'structure' and x['entity_id'] == entity['id']
                           and (x['claim'].endswith('.form.' + loc['attribute']) or x['claim'] == loc['attribute']) and x['use'] == 'scene'
                           for x in edges), f"fact has no source-claim backlink: {e['id']}"
    return phases, kinds

def main():
    phases, kinds = validate()
    doc = json.loads((ROOT / 'data/loading/statuses.json').read_text())
    js = (ROOT / 'renderers/web/js/loading-early.js').read_text()
    early = json.loads(js.split('export const EARLY_ENTRIES = ', 1)[1].strip().removesuffix(';'))
    entries = {e['id']: e for e in doc['entries']}
    assert len(early) == 24 and len({e['id'] for e in early}) == 24, '24 distinct early entries'
    for e in early:
        assert all(entries[e['id']].get(k) == v for k, v in e.items()), 'stale early subset'
        assert e['kind'] != 'humor', 'early subset excludes humor'
    print('LOADING CONTENT PASS —', sum(phases.values()), 'entries;', dict(sorted(phases.items())), dict(sorted(kinds.items())))
if __name__ == '__main__':main()
