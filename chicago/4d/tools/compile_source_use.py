#!/usr/bin/env python3
"""T-1248: deterministic public source-use backlinks; never a raw research export."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import re
from collections import defaultdict
from compile_scene import cite, resolve_phase

ROOT = Path(__file__).resolve().parents[1]
USES = ('scene', 'other_scene', 'exclusion', 'research', 'unused')
GRADES = {'attested', 'inferred', 'reconstructed'}
GRADE_ALIASES = {'documented': 'attested', 'conjectural': 'reconstructed',
                 'unknown': 'reconstructed', 'not_1835_resident': 'reconstructed'}
NEWSPAPERS = 'chicago_newspapers_1833_1835'
CITATION_KEYS = {'sources', 'source_ids', 'source_id'}


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'


def public_text(value):
    """Do not let an authored locator smuggle a repository research path out."""
    if isinstance(value, str):
        return value if not re.search(r'(?:data|docs)/research/|chicago/reference/', value, re.I) else None
    if isinstance(value, dict):
        return {k: public_text(v) for k, v in value.items() if public_text(v) is not None}
    if isinstance(value, list):
        return [public_text(v) for v in value if public_text(v) is not None]
    return value


class Compiler:
    def __init__(self, root):
        self.root, self.data = Path(root), Path(root) / 'data'
        self.sources = {}
        for path in sorted((self.data / 'sources').glob('*.json')):
            source = read(path)
            sid = source['id']
            if not re.fullmatch(r'[A-Za-z0-9_-]+', sid) or sid in self.sources:
                raise ValueError(f'invalid or duplicate source id: {sid}')
            self.sources[sid] = source
        self.edges = defaultdict(dict)
        self.coverage = defaultdict(lambda: {'records': 0, 'cited': 0, 'unresolved': 0})
        self.issues, self.claims = {}, {}
        paper = self.data / 'research/newspapers'
        for issue in read(paper / 'corpus.json', {}).get('issues', []):
            self.issues[issue['id']] = issue
        for path in sorted((paper / 'extracted').glob('*.json')):
            doc = read(path)
            for claim in doc.get('claims', []):
                self.claims[f"{doc['issue_id']}#{claim['id']}"] = claim

    def references(self, sid, claim_ids, locator):
        if sid == NEWSPAPERS:
            if not claim_ids:
                raise ValueError('newspaper alias without issue-level claim_ids')
            for cid in sorted(set(claim_ids)):
                issue_id = cid.split('#')[0]
                issue, claim = self.issues.get(issue_id), self.claims.get(cid)
                if not issue or not claim:
                    raise ValueError(f'unresolved newspaper claim: {cid}')
                loc = {'issue_id': issue_id, 'issue_date': issue['date'],
                       'publication': issue['publication'], 'claim_id': cid}
                raw = claim.get('locator', {})
                for key, output in [('issue_page', 'page'), ('column', 'column')]:
                    if raw.get(key) is not None:
                        loc[output] = raw[key]
                yield issue['source_id'], loc
        else:
            matches = [cid for cid in claim_ids if cid in self.claims
                       and (self.issues.get(cid.split('#')[0], {}).get('source_id') == sid
                            or cid.split('#')[0] == sid)]
            if matches:
                for _, loc in self.references(NEWSPAPERS, matches, locator):
                    yield sid, loc
            else:
                yield sid, public_text(locator)

    def record(self, family, kind, entity_id, node, use, path='', grade='inferred', claim_ids=()):
        stats = self.coverage[family]
        stats['records'] += 1
        found = False

        def walk(value, field, confidence, inherited_claims):
            nonlocal found
            if isinstance(value, list):
                for i, child in enumerate(value):
                    key = child.get('id', i) if isinstance(child, dict) else i
                    walk(child, f'{field}[{key}]', confidence, inherited_claims)
            elif isinstance(value, dict):
                declared = next((value[k] for k in ('confidence', 'tier', 'grade')
                                 if isinstance(value.get(k), str)), None)
                if declared is not None:
                    confidence = declared if declared in GRADES else GRADE_ALIASES.get(declared, 'reconstructed')
                ids = value.get('claim_ids', inherited_claims)
                refs = []
                for key in CITATION_KEYS:
                    raw = value.get(key, [])
                    refs.extend(raw if isinstance(raw, list) else [raw])
                if any(s is not None and not isinstance(s, str) for s in refs):
                    raise ValueError(f'{kind}/{entity_id}/{field}: non-string source id')
                for sid in sorted(set(s for s in refs if s is not None)):
                    for resolved, loc in self.references(sid, ids, value.get('locator')):
                        if resolved not in self.sources:
                            stats['unresolved'] += 1
                            raise ValueError(f'{kind}/{entity_id}/{field}: unresolved source {resolved}')
                        found = True
                        edge = dict(source_id=resolved, entity_type=kind, entity_id=entity_id,
                                    claim=field or 'record', confidence=confidence, locator=loc, use=use)
                        self.edges[resolved][packed(edge)] = edge
                for key in sorted(value):
                    if key not in CITATION_KEYS:
                        walk(value[key], f'{field}.{key}' if field else key, confidence, ids)
        walk(node, path, grade, claim_ids)
        stats['cited'] += int(found)

    def collect(self):
        data = self.data
        scene = read(data / 'scenes/1835.json', {'target_date': '1835-07-01'})
        target = dt.date.fromisoformat(scene['target_date'])
        current = read(data / 'sidecars/1835/index.json', {}).get('structures', [])
        current_ids = {r['id'] for r in current}
        for path in sorted((data / 'structures').glob('*.json')):
            row = read(path)
            phase = resolve_phase(row, target)
            self.record('structures', 'structure', row['id'],
                        {k: v for k, v in row.items() if k != 'phases'},
                        'scene' if row['id'] in current_ids else 'research')
            for ph in row.get('phases', []):
                self.record('structure phases', 'structure', row['id'], ph,
                            'scene' if ph is phase and row['id'] in current_ids else 'other_scene',
                            f"phases[{ph['id']}]")
        people = read(data / 'sidecars/1835/people.json', {}).get('people', [])
        people_ids = {r['id'] for r in people}
        homes = {r['household'] for r in people}
        for path in sorted((data / 'residents').rglob('*.json')):
            row = read(path)
            if not isinstance(row, dict) or path.name == 'index.json':
                continue
            if isinstance(row.get('persons'), list) and 'id' in row:
                self.record('households', 'household', row['id'],
                            {k: v for k, v in row.items() if k != 'persons'},
                            'scene' if row['id'] in homes else 'research')
                for person in row['persons']:
                    self.record('people', 'person', person['id'], person,
                                'scene' if person['id'] in people_ids else 'research',
                                grade=person.get('grade') if person.get('grade') in GRADES else 'inferred')
            else:
                self.record('resident decisions', 'decision', path.stem, row, 'research')
        for row in read(data / 'residents/index.json', {}).get('researched_not_resident', []):
            self.record('resident exclusions', 'person', row['id'], row, 'exclusion')
        for path in sorted((data / 'businesses').glob('biz_*.json')):
            row = read(path)
            self.record('businesses', 'business', row['id'], row,
                        'scene' if row.get('present_at_scene_date') is True else 'exclusion')
        epoch = scene.get('terrain_epoch')
        for row in read(data / 'terrain/epochs.json', {}).get('epochs', []):
            self.record('terrain epochs', 'terrain', row['id'], row,
                        'scene' if row['id'] == epoch else 'other_scene')
        for path in sorted((data / 'terrain').rglob('*')):
            if path.suffix not in ('.json', '.geojson') or path.name in ('heightfield.json', 'epochs.json'):
                continue
            row = read(path)
            rel = path.relative_to(data / 'terrain')
            use = ('scene' if len(rel.parts) > 1 and rel.parts[1] == epoch else 'other_scene') if rel.parts[0] == 'epochs' else 'research'
            self.record('terrain', 'terrain', rel.with_suffix('').as_posix(), row, use)
        for family, flag in [('flora', 'plantable_in_scene'), ('fauna', 'in_modelled_extent')]:
            for path in sorted((data / family / 'zones').glob('*.json')):
                row = read(path)
                self.record(family, family, row['id'], row, 'scene' if row.get(flag) else 'research')
        for row in read(data / 'exclusions.json', {}).get('excluded', []):
            self.record('exclusions', 'exclusion', row['id'], row, 'exclusion')
        for row in read(data / 'liberties.json', {}).get('liberties', []):
            self.record('liberties (structured citations)', 'liberty', row['id'], row, 'research', grade='reconstructed')
        # A cited current structure must have a backlink, independently of input traversal.
        reached = {e['entity_id'] for edges in self.edges.values() for e in edges.values()
                   if e['entity_type'] == 'structure' and e['use'] == 'scene'}
        for row in current:
            card_path = data / row.get('sidecar', f"sidecars/1835/{row['id']}.json")
            card = read(card_path)
            if card is None:
                raise ValueError(f'missing compiled structure: {card_path}')
            if card.get('citations') and row['id'] not in reached:
                raise ValueError(f"cited current structure has no edge: {row['id']}")

    def outputs(self):
        outputs, index = {}, []
        for sid, source in sorted(self.sources.items()):
            edges = [self.edges[sid][key] for key in sorted(self.edges[sid])]
            citation = public_text(cite([sid], self.sources)[0])
            uses = sorted({e['use'] for e in edges}, key=USES.index)
            counts = {'entities': len({(e['entity_type'], e['entity_id']) for e in edges}),
                      'claims': len({(e['entity_type'], e['entity_id'], e['claim']) for e in edges})}
            # Full, unabridged citation/link/limits live beside the edges, fetched on demand.
            index.append(dict(source_id=sid, citation=citation['citation'], type=source.get('type'),
                              date=source.get('date'), tier=source.get('tier'), use=uses[0] if uses else 'unused',
                              counts=counts, has_archive_link=bool(source.get('archived_url'))))
            outputs[f'{sid}.json'] = packed({'source': citation, 'uses': uses, 'edges': edges})
        outputs['index.json'] = packed({'schema_version': 1, 'scene': '1835', 'sources': index})
        size = len(outputs['index.json'].encode())
        if size > 120_000:
            raise ValueError(f'source index {size} bytes exceeds 120000-byte budget')
        return outputs

    def report(self, outputs):
        lines = ['# Source-use coverage', '', 'Generated by `tools/compile_source_use.py`; no timestamps.', '',
                 '| Input family | Records read | With citations | Unresolved IDs |',
                 '| --- | ---: | ---: | ---: |']
        for family, s in sorted(self.coverage.items()):
            lines.append(f"| {family} | {s['records']} | {s['cited']} | {s['unresolved']} |")
        lines += ['', f"Registered sources: {len(self.sources)}. Index: {len(outputs['index.json'].encode())} bytes / 120000.", '',
                  'Records are adapter units: a structure and each phase are separate readings; a household and each person are separate readings.',
                  'Claims deduplicate by entity type, entity ID and field path; entities deduplicate independently. Several newspaper issues can support one claim.',
                  'Use precedence is scene, other_scene, exclusion, research, unused; per-source files retain every use and edge.',
                  'Missing attribute confidence inherits the enclosing grade, otherwise inferred. Documented maps to attested; conjectural/unknown maps conservatively to reconstructed. Registration or numeric source tier never upgrades a claim.', '',
                  '## Coverage limits', '',
                  '- Businesses are covered: T-1180 has landed. Newspaper aliases resolve through their claim IDs to registered publications, preserving issue date/page/column where supplied.',
                  '- Liberties are read, but their prose-only bibliographic mentions are not parsed as structured citations. No guessed source IDs.',
                  '- Decisions cover resident decision records only. Free-form dossiers, other research ledgers, and decision prose without structured source IDs are not exhaustively indexed.',
                  '- Terrain covers authored JSON/GeoJSON, not binary heightfields. Ancillary terrain readings are research; current-epoch inputs are scene and other epochs are other_scene.',
                  '- Unmodelled flora/fauna zones are research, not scene use. Out-of-scene structure phases are other_scene; this does not claim they are visible in 1835.',
                  '- Jaunts and loading facts await their owning tickets. No PDF/image bytes or asset derivation is produced.',
                  '- The compact index holds citation text and explicit type/date/tier metadata. Full public citations, links and source limits are lazy per-source data. Internal source fields and raw research paths are not exported.', '']
        return '\n'.join(lines)


def compile_outputs(root):
    compiler = Compiler(root)
    compiler.collect()
    outputs = compiler.outputs()
    return outputs, compiler.report(outputs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='refuse stale committed outputs without writing')
    args = ap.parse_args()
    outputs, report = compile_outputs(ROOT)
    dest = ROOT / 'data/sidecars/1835/sources'
    files = {dest / name: body for name, body in outputs.items()}
    files[ROOT / 'docs/measurements/source_use_coverage.md'] = report
    stale = [str(p.relative_to(ROOT)) for p, body in files.items() if not p.exists() or p.read_text() != body]
    extra = sorted(set(dest.glob('*.json')) - set(files))
    if args.check:
        if stale or extra:
            raise SystemExit('SOURCE USE FAIL — rebuild with python3 tools/compile_source_use.py: ' + ', '.join(stale + [str(p) for p in extra]))
    else:
        for p, body in files.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)
        for p in extra:
            p.unlink()
    print(f'SOURCE USE PASS — {len(outputs)-1} sources; {len(outputs["index.json"].encode())} index bytes; all source IDs resolve')


if __name__ == '__main__':
    main()
