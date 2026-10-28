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
from exclusion_scope import ruled_for

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tools/derived_manifest.json'
STEP = ['python3', 'tools/compile_source_use.py']
USES = ('scene', 'other_scene', 'exclusion', 'research', 'unused')
# The raw index.json ceiling (bytes). 120 000 from T-1248; 128 000 from T-1728; 136 000 from
# T-2334; 144 000 from T-2473; 152 000 from T-2498; 160 000 from T-2747;
# 168 000 from T-2792/T-2799; 176 000 from T-3055/T-3056; 184 000 from T-3013; 192 000 from
# T-2385 (dev's new Prairie sources and the Tremont's Gale record together read 184 255);
# 200 000 from T-3188 — see outputs().
INDEX_BUDGET = 208_000
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
        # T-2079: the sources each OTHER scene's own records cite, by scene id. Every edge
        # keeps its 1835 `use`; an edge a record of another scene draws also says which.
        self.scene_sources = defaultdict(set)
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

    def record(self, family, kind, entity_id, node, use, path='', grade='inferred', claim_ids=(), elsewhere=()):
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
                        if elsewhere:
                            edge['scenes'] = sorted(elsewhere)
                            for other in elsewhere:
                                self.scene_sources[other].add(resolved)
                        self.edges[resolved][packed(edge)] = edge
                for key in sorted(value):
                    if key not in CITATION_KEYS:
                        walk(value[key], f'{field}.{key}' if field else key, confidence, ids)
        walk(node, path, grade, claim_ids)
        stats['cited'] += int(found)

    def other_scenes(self):
        """T-2079: every published scene but 1835, with what its renderer draws.

        A scene is published when compile_scene has written its sidecar index — the same
        test compile_jaunts uses. Its `layers` list is the renderer's contract (T-1739,
        T-1740): a layer it does not list is never drawn or offered there, so nothing that
        layer reads is that scene's use."""
        scenes = {}
        for path in sorted((self.data / 'scenes').glob('*.json')):
            index = read(self.data / f'sidecars/{path.stem}/index.json')
            if path.stem == '1835' or index is None:
                continue
            scene = read(path)
            layers = set(scene.get('layers', []))
            # Residents, firms and animals are authored for 1835 alone; a scene that starts
            # listing one needs its own reading of it here first, rather than a Sources list
            # that silently leaves those citations out. The excluded-buildings record is read
            # per scene since T-2489: an entry is a ruling for the scenes its `scenes` names.
            unread = sorted(layers & {'residents', 'businesses', 'fauna'})
            if unread:
                raise ValueError(f"scene {path.stem} lists {', '.join(unread)}: the per-scene source index cannot read them yet")
            scenes[path.stem] = dict(target=dt.date.fromisoformat(scene['target_date']), layers=layers,
                                     epoch=scene.get('terrain_epoch'),
                                     current={r['id'] for r in index.get('structures', [])})
        return scenes

    def collect(self):
        data = self.data
        scene = read(data / 'scenes/1835.json', {'target_date': '1835-07-01'})
        target = dt.date.fromisoformat(scene['target_date'])
        current = read(data / 'sidecars/1835/index.json', {}).get('structures', [])
        current_ids = {r['id'] for r in current}
        others = self.others = self.other_scenes()
        for path in sorted((data / 'structures').glob('*.json')):
            row = read(path)
            phase = resolve_phase(row, target)
            standing = {s: resolve_phase(row, o['target']) for s, o in others.items() if row['id'] in o['current']}
            self.record('structures', 'structure', row['id'],
                        {k: v for k, v in row.items() if k != 'phases'},
                        'scene' if row['id'] in current_ids else 'research', elsewhere=tuple(standing))
            for ph in row.get('phases', []):
                self.record('structure phases', 'structure', row['id'], ph,
                            'scene' if ph is phase and row['id'] in current_ids else 'other_scene',
                            f"phases[{ph['id']}]", elsewhere=tuple(s for s, p in standing.items() if p is ph))
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
                        'scene' if row['id'] == epoch else 'other_scene',
                        elsewhere=tuple(s for s, o in others.items() if o['epoch'] == row['id']))
        for path in sorted((data / 'terrain').rglob('*')):
            if path.suffix not in ('.json', '.geojson') or path.name in ('heightfield.json', 'epochs.json'):
                continue
            row = read(path)
            rel = path.relative_to(data / 'terrain')
            use = ('scene' if len(rel.parts) > 1 and rel.parts[1] == epoch else 'other_scene') if rel.parts[0] == 'epochs' else 'research'
            drawn = tuple(s for s, o in others.items()
                          if rel.parts[0] == 'epochs' and len(rel.parts) > 1 and rel.parts[1] == o['epoch'])
            self.record('terrain', 'terrain', rel.with_suffix('').as_posix(), row, use, elsewhere=drawn)
        # A flora zone stands in another scene the way flora.js's floraInScene decides: the
        # scene lists the layer, and the zone's index entry names no scenes or names it.
        scoped = {z['id']: z.get('scenes') for z in read(data / 'flora/index.json', {}).get('zones', [])}
        for family, flag in [('flora', 'plantable_in_scene'), ('fauna', 'in_modelled_extent')]:
            for path in sorted((data / family / 'zones').glob('*.json')):
                row = read(path)
                drawn = tuple(s for s, o in others.items() if family == 'flora' and family in o['layers']
                              and row.get(flag) and (scoped.get(row['id']) is None or s in map(str, scoped[row['id']])))
                self.record(family, family, row['id'], row, 'scene' if row.get(flag) else 'research', elsewhere=drawn)
        # The 1904 street grid and its paving (T-0474, T-1728) are another scene's own records;
        # from 1835 they are other-scene use, and the scene that lists the layer draws them.
        for s, o in others.items():
            if 'street_grid' not in o['layers']:
                continue
            for family, kind, folder in [('street grid', 'street_grid', 'street_grid'),
                                         ('street surfaces', 'street_surface', 'street_surfaces')]:
                row = read(data / folder / f'{s}.json')
                if row is not None:
                    self.record(family, kind, f'{folder}/{s}', row, 'other_scene', elsewhere=(s,))
        # The 1904 lakefront railway (T-2478), the same way.
        for s, o in others.items():
            if 'railway' not in o['layers']:
                continue
            row = read(data / 'railway' / f'{s}.json')
            if row is not None:
                self.record('railway', 'railway', f'railway/{s}', row, 'other_scene', elsewhere=(s,))
        # T-2489: a ruling is the 1835 town's exclusion when it is ruled for 1835, and
        # another scene's when that scene lists the layer and the ruling names it.
        for row in read(data / 'exclusions.json', {}).get('excluded', []):
            listed = tuple(s for s, o in others.items() if 'exclusions' in o['layers'] and ruled_for(row, s))
            self.record('exclusions', 'exclusion', row['id'], row,
                        'exclusion' if ruled_for(row, '1835') else 'other_scene', elsewhere=listed)
        for row in read(data / 'liberties.json', {}).get('liberties', []):
            self.record('liberties (structured citations)', 'liberty', row['id'], row, 'research', grade='reconstructed')
        for row in read(data / 'loading/statuses.json', {}).get('entries', []):
            if row['kind'] == 'fact':
                self.record('loading facts', 'decision', row['id'],
                            dict(source_ids=row['source_ids'], locator=row['fact']['locator'],
                                 confidence=row['fact']['confidence']), 'scene', 'loading_fact')
        # Compile in memory: check.sh pools validators, so never race on generated files.
        if (data / 'jaunts/schema.json').exists():
            from compile_jaunts import Compiler as JauntsCompiler
            jaunts = JauntsCompiler(self.root)
            outputs, errors = jaunts.compile()
            if errors:
                raise ValueError('; '.join(errors))
            for row in json.loads(outputs['catalog.json'])['jaunts']:
                content = json.loads(outputs[row['id'] + '.json'])
                self.record('jaunt claims', 'jaunt', row['id'], content['evidence'],
                            'scene' if row['availability'] == 'available' else 'research', 'evidence')
            for s in others:
                outputs, errors = JauntsCompiler(self.root, s).compile()
                if errors:
                    raise ValueError('; '.join(errors))
                for row in json.loads(outputs['catalog.json'])['jaunts']:
                    content = json.loads(outputs[row['id'] + '.json'])
                    available = row['availability'] == 'available'
                    self.record('jaunt claims', 'jaunt', row['id'], content['evidence'],
                                'other_scene' if available else 'research', 'evidence',
                                elsewhere=(s,) if available else ())
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

    # ---- T-2825: the source's detail view said for a reader -------------------------------
    # The owner, 2026-10-18: no internal ticket number or record id in anything a person
    # opens, in any mode. Sources › a source printed each use by its record id in words
    # ("recon 1835 west 002"), its claim path and its raw locator (a JSON object, a ticket, a
    # file path). The ids and locators stay as they are, for the links and the issue groups;
    # beside them each file now carries the thing's NAME (`names`, by entity id) and each
    # located edge a `locator_text`, both through the rule every research surface shares
    # (tools/readable_text.py), and the source's own prose is said the same way.
    def _reader(self):
        if getattr(self, '_names', None) is None:
            import readable_text
            self._rt = readable_text
            self._names = readable_text.Names(self.root)
            libs = read(self.data / 'liberties.json', {}) or {}
            self._extra = {l['id']: l.get('title') for l in libs.get('liberties', []) if l.get('title')}
            for path in sorted((self.data / 'jaunts').glob('*.json')):
                doc = read(path, {}) or {}
                if isinstance(doc, dict) and doc.get('id') and doc.get('title'):
                    self._extra[doc['id']] = doc['title']
        return self._rt, self._names

    def say(self, text):
        rt, names = self._reader()
        return rt.rewrite(text, names)[0] if isinstance(text, str) else text

    def entity_name(self, kind, eid):
        rt, names = self._reader()
        hit = self._extra.get(eid) or names.get(eid)
        if hit:
            return hit
        if kind == 'terrain':
            return rt.words(str(eid).split('.')[-1])
        return rt.words(str(eid))

    def locator_text(self, loc):
        if isinstance(loc, str):
            return self.say(loc)
        if not isinstance(loc, dict):
            return None
        if loc.get('publication') or loc.get('issue_date'):
            parts = [str(loc.get('publication') or ''), str(loc.get('issue_date') or '')]
            if loc.get('page') is not None:
                parts.append(f"p. {loc['page']}")
            if loc.get('column') is not None:
                parts.append(f"col. {loc['column']}")
            return self.say(', '.join(p for p in parts if p))
        rt, names = self._reader()
        bits = []
        for key, value in loc.items():
            if key in ('issue_id', 'claim_id') or value in (None, '', [], {}):
                continue
            if isinstance(value, str):
                bits.append(self._extra.get(value) or names.get(value) or self.say(rt.words(value) if ' ' not in value else value))
            elif isinstance(value, (int, float)):
                bits.append(f"{rt.words(key)} {value}")
        return ' · '.join(b for b in bits if b) or None

    def reader_detail(self, citation, uses, edges):
        source = json.loads(json.dumps(citation))
        for key in ('citation', 'what_it_supplies', 'what_it_does_not_supply'):
            value = source.get(key)
            if isinstance(value, list):
                source[key] = [self.say(v) for v in value]
            elif isinstance(value, str):
                source[key] = self.say(value)
        out, named = [], {}
        for edge in edges:
            e = dict(edge)
            text = self.locator_text(edge.get('locator'))
            if text:
                e['locator_text'] = text
            out.append(e)
            named.setdefault(edge['entity_id'], self.entity_name(edge['entity_type'], edge['entity_id']))
        return {'source': source, 'uses': uses, 'edges': out, 'names': dict(sorted(named.items()))}

    def outputs(self):
        outputs, index = {}, []
        for sid, source in sorted(self.sources.items()):
            edges = [self.edges[sid][key] for key in sorted(self.edges[sid])]
            citation = public_text(cite([sid], self.sources)[0])
            uses = sorted({e['use'] for e in edges}, key=USES.index)
            counts = {'entities': len({(e['entity_type'], e['entity_id']) for e in edges}),
                      'claims': len({(e['entity_type'], e['entity_id'], e['claim']) for e in edges})}
            # A claim supported by several locators counts once, at its strongest grade.
            order = ('attested', 'inferred', 'reconstructed')
            claims, entities = {}, {}
            for edge in edges:
                rank = order.index(edge['confidence'])
                entity = (edge['entity_type'], edge['entity_id'])
                claim = (*entity, edge['claim'])
                claims[claim] = min(rank, claims.get(claim, 2))
                entities[entity] = min(rank, entities.get(entity, 2))
            # Compact, documented order keeps the first-open index inside INDEX_BUDGET.
            counts['grades'] = [[sum(v == i for v in group.values()) for i in range(3)]
                                for group in (claims, entities)]
            # Full, unabridged citation/link/limits live beside the edges, fetched on demand.
            index.append(dict(source_id=sid, citation=self.say(citation['citation']), type=source.get('type'),
                              date=source.get('date'), tier=source.get('tier'), use=uses[0] if uses else 'unused',
                              counts=counts, has_archive_link=bool(source.get('archived_url'))))
            outputs[f'{sid}.json'] = packed(self.reader_detail(citation, uses, edges))
        outputs['index.json'] = packed({'schema_version': 1, 'scene': '1835', 'sources': index})
        size = len(outputs['index.json'].encode())
        # THE BUDGET WAS 120 000 BYTES (T-1248) AND IS 128 000 SINCE 2026-09-29 (T-1728). A
        # conscious re-budget, not a weakened assertion: the index grows about 375 bytes per
        # registered source, and the 1904 scene's two owner-asked parcels (T-1732's Glessner
        # records, T-1728's street-paving records) landed the same night and took it to 121 936
        # bytes with every citation kept whole. What a visitor actually pays is the gzipped first
        # open, which is ~28 KB and is still held at T-1276's 120 KB by measure_sources.mjs; the
        # raw figure moves 8 KB, room for about twenty more sources before this is asked again.
        # 136 000 SINCE 2026-10-11 (T-2334), asked again without a single new source: the Prairie
        # district drafts (T-2329, T-2330, T-2334) grew the use counts of the sheets they cite, and
        # the 16th-18th west side's drafts put the index at 128 001 bytes. The gzipped first open
        # is still held at 120 KB by measure_sources.mjs; this is the raw file only.
        # 144 000 SINCE 2026-10-13 (T-2473): the owner's streetscape (T-2473's two Prairie Avenue
        # views) and the day's other 1904 parcels (T-2476's Inter Ocean notice, T-2477's context
        # city, T-2478's railway) took it to 136 530 bytes with every citation kept whole. Same
        # bargain as before: about twenty sources of room, the gzipped first open still held at
        # 120 KB by measure_sources.mjs.
        # 152 000 SINCE 2026-10-15 (T-2498): the 1812 Kinzie house's pictures (T-2497's two and
        # T-2498's six: the Cram plate, the Teich postcard, the Eastman and Gemmell 1820 views and
        # Sarony's lithograph in Currey and Kirkland), each a source record the image gate and the
        # card's Images tab need, took it to 144 165 bytes with every citation kept whole. Same
        # bargain: about twenty sources of room, the gzipped first open still held at 120 KB by
        # measure_sources.mjs; this is the raw file only.
        # 160 000 SINCE 2026-10-17 (T-2747): the owner's 1904 walking jaunts cite the district's
        # five interpretive markers and the house museum's history of the street, six source
        # records the walks' claims need, which took it to 152 941 bytes with every citation kept
        # whole. Same bargain: about twenty sources of room, the gzipped first open still held at
        # 120 KB by measure_sources.mjs.
        # 168 000 SINCE 2026-10-22 (T-2792/T-2799): the owner-requested vehicle and
        # horse reference/specification records take the complete 404-source index from
        # 159 155 to 161 435 raw bytes. Full citations remain intact. The candidate's
        # gzip is about 39 KB; the unchanged 120 KB first-open compressed allowance
        # still includes sources.js and sources.css. This measured 8 KB raw increase
        # follows the previous approximately twenty-source increments, with no change
        # to scene-detail tiers, rendering allowances or the compressed-wire ceiling.
        # 176 000 SINCE 2026-10-23 (T-3055/T-3056): the early frame buildings' picture
        # records (Gale's 1902 Trowbridge pages for the jail, Green Tree and Sauganash, and
        # Gifford's first Tremont) merged onto dev's own additions took the index to
        # 168 716 raw bytes with every citation kept whole. Same bargain: about twenty
        # sources of room, the gzipped first open still held at 120 KB by measure_sources.mjs.
        # 184 000 SINCE 2026-10-25 (T-3013): twelve dated records (four Blue Books, the 1902
        # Lakeside directory and seven Tribune advertisements) that rule what stood on five
        # Indiana Avenue lots on 1 July 1904, merged onto dev's T-3055/T-3056 additions, took
        # the index to 177 692 raw bytes with every citation whole. Same bargain as before:
        # about twenty sources of room, and the 120 KB compressed first-open allowance,
        # measured by measure_sources.mjs, unchanged.
        # 192 000 SINCE 2026-10-26 (T-3167): 1824 Prairie's Pomeroy photograph merged onto
        # dev's T-3162 (1823's engraving and album plate) took the index to 184 545 raw
        # bytes with every citation whole. Same bargain: about twenty sources of room; the
        # index gzips to 43.8 KB (gzip -9), far inside the 120 KB compressed first-open allowance.
        # T-3110 (HABS photograph 2 of 1801 Prairie) landed in the same room, alongside T-3167.
        # T-3171 (the Doane photograph's record, 1827 Prairie) landed in the same room too.
        # 200 000 SINCE 2026-10-27 (T-3188): 1708 Prairie's two photographs (the Glessner House
        # Museum's Christmas print and Chicagology's photograph of 1700-1706, at whose edge it
        # stands) took the index to 192 534 raw bytes with every citation whole. Same bargain:
        # about twenty sources of room, the gzipped first open measured by measure_sources.mjs.
        # 208 000 SINCE 2026-10-28 (T-3161): J. W. Taylor's photograph no. 1445 of 1729 Prairie
        # (the owner ruled it public domain on 2026-10-27) took the index to 200 142 raw bytes
        # with every citation whole, its own citation already cut short. Same bargain again.
        if size > INDEX_BUDGET:
            raise ValueError(f'source index {size} bytes exceeds {INDEX_BUDGET}-byte budget')
        return outputs

    def scene_outputs(self, outputs):
        """T-2079: one use map per other scene, so its Sources topic lists what ITS records cite.

        The catalog stays one file: the rows, their counts (a count covers every recorded use
        of a source, as the panel says) and the per-source files under sidecars/1835/sources/
        are the same in every scene. What differs is which sources a scene uses, so each other
        scene gets `sidecars/<scene>/sources/uses.json`, mapping EVERY registered source to its
        use read from that scene's side — `scene` for one this scene's own records cite;
        `other_scene` for one another scene draws (1835 included); otherwise the source's own
        exclusion/research/unused reading, which no scene changes. A copy of the whole index
        per scene was tried first and stood at 127 866 of INDEX_BUDGET's 128 000 bytes; the
        map is about a tenth of that, and Sources fetches it only when the topic opens."""
        rows = json.loads(outputs['index.json'])['sources']
        drawn = set().union(*self.scene_sources.values()) if self.scene_sources else set()
        result = {}
        for scene in sorted(getattr(self, 'others', {})):
            uses = {}
            for row in rows:
                sid = row['source_id']
                if sid in self.scene_sources[scene]:
                    uses[sid] = 'scene'
                elif row['use'] in ('scene', 'other_scene') or sid in drawn:
                    uses[sid] = 'other_scene'
                else:
                    uses[sid] = row['use']
            result[scene] = packed({'schema_version': 1, 'scene': scene, 'catalog': '1835', 'uses': uses})
        return result

    def report(self, outputs):
        lines = ['# Source-use coverage', '', 'Generated by `tools/compile_source_use.py`; no timestamps.', '',
                 '| Input family | Records read | With citations | Unresolved IDs |',
                 '| --- | ---: | ---: | ---: |']
        for family, s in sorted(self.coverage.items()):
            lines.append(f"| {family} | {s['records']} | {s['cited']} | {s['unresolved']} |")
        lines += ['', f"Registered sources: {len(self.sources)}. Index: {len(outputs['index.json'].encode())} bytes / {INDEX_BUDGET}.", '']
        for scene, body in sorted(self.scene_outputs(outputs).items()):
            used = sum(u == 'scene' for u in json.loads(body)['uses'].values())
            lines.append(f"Scene {scene}: {used} sources cited by its own records; use map {len(body.encode())} bytes "
                         f"(`sidecars/{scene}/sources/uses.json`).")
        lines += ['',
                  'Records are adapter units: a structure and each phase are separate readings; a household and each person are separate readings.',
                  'Claims deduplicate by entity type, entity ID and field path; entities deduplicate independently. Several newspaper issues can support one claim.',
                  'Use precedence is scene, other_scene, exclusion, research, unused; per-source files retain every use and edge.',
                  'Missing attribute confidence inherits the enclosing grade, otherwise inferred. Documented maps to attested; conjectural/unknown maps conservatively to reconstructed. Registration or numeric source tier never upgrades a claim.', '',
                  '## Coverage limits', '',
                  '- Businesses are covered: T-1180 has landed. Newspaper aliases resolve through their claim IDs to registered publications, preserving issue date/page/column where supplied.',
                  '- Liberties are read, but their prose-only bibliographic mentions are not parsed as structured citations. No guessed source IDs.',
                  '- Decisions cover resident decision records and explicitly cited loading facts. Free-form dossiers, other research ledgers, and decision prose without structured source IDs are not exhaustively indexed.',
                  '- Terrain covers authored JSON/GeoJSON, not binary heightfields. Ancillary terrain readings are research; current-epoch inputs are scene and other epochs are other_scene.',
                  '- Unmodelled flora/fauna zones are research, not scene use. Out-of-scene structure phases are other_scene; this does not claim they are visible in 1835.',
                  '- Jaunt evidence claims are validated and registered as typed jaunt backlinks (T-1253); source-free reconstructed narrative has no fabricated source edge. Unavailable jaunts are research use. Loading facts carry decision/loading_fact backlinks. No PDF/image bytes or asset derivation is produced.',
                  '- The compact index holds citation text and explicit type/date/tier metadata. Full public citations, links and source limits are lazy per-source data. Internal source fields and raw research paths are not exported.',
                  '- Other scenes (T-2079) get their own use map over the one catalog: a source is `scene` there when a record that scene draws cites it — a structure standing on its date, its terrain epoch, flora zones its layer scope admits, its street grid and paving, its available jaunts. Edges keep their 1835 `use` and add `scenes` naming the other scenes that draw them. A scene that lists residents, businesses or fauna is refused until this compiler reads those for it; exclusions are read per scene, from the `scenes` each entry names (T-2489); plantings and loading facts are not read for other scenes.', '']
        return '\n'.join(lines)


def owned_resolves(manifest, owned):
    """T-3131: this step's `resolves` in tools/derived_manifest.json, set to exactly what it writes.

    The list is what lets rederive.mjs --resolve clear a merge conflict in a file by rebuilding
    it, and it enumerates rather than pattern-matches on purpose. Written by hand at T-1248 and
    once more at T-2747, it had fallen to 303 of the 436 files this compiler writes, because
    every new source record adds a per-source file and nothing added the line: a conflict in
    any of the other 134 was refused, and a lap that took one side by hand dropped that
    branch's source-use edges without a word. So the compiler that decides the set now writes
    the list, and --check refuses the moment the two disagree. Returns (missing, extra)."""
    steps = [s for s in manifest['steps'] if s.get('command') == STEP]
    if len(steps) != 1:
        raise SystemExit(f'SOURCE USE FAIL — tools/derived_manifest.json has {len(steps)} steps running '
                         f'{" ".join(STEP)}; expected exactly one')
    step, want = steps[0], sorted(owned)
    missing = sorted(set(want) - set(step['resolves']))
    extra = sorted(set(step['resolves']) - set(want))
    step['resolves'] = want
    return missing, extra


def compile_outputs(root):
    compiler = Compiler(root)
    compiler.collect()
    outputs = compiler.outputs()
    return outputs, compiler.report(outputs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='refuse stale committed outputs without writing')
    args = ap.parse_args()
    compiler = Compiler(ROOT)
    compiler.collect()
    outputs = compiler.outputs()
    report = compiler.report(outputs)
    dest = ROOT / 'data/sidecars/1835/sources'
    files = {dest / name: body for name, body in outputs.items()}
    for scene, body in compiler.scene_outputs(outputs).items():
        files[ROOT / f'data/sidecars/{scene}/sources/uses.json'] = body
    files[ROOT / 'docs/measurements/source_use_coverage.md'] = report
    stale = [str(p.relative_to(ROOT)) for p, body in files.items() if not p.exists() or p.read_text() != body]
    extra = sorted(set(dest.glob('*.json')) - set(files))
    manifest = json.loads(MANIFEST.read_text())
    unlisted, unowned = owned_resolves(manifest, {'chicago/4d/' + str(p.relative_to(ROOT)) for p in files})
    if args.check:
        if stale or extra:
            raise SystemExit('SOURCE USE FAIL — rebuild with python3 tools/compile_source_use.py: ' + ', '.join(stale + [str(p) for p in extra]))
        if unlisted or unowned:
            raise SystemExit(f'SOURCE USE FAIL — tools/derived_manifest.json lists {len(unowned)} file(s) this compiler '
                             f'does not write and omits {len(unlisted)} it does, so rederive.mjs --resolve would refuse '
                             f'a conflict in them; rebuild with python3 tools/compile_source_use.py: '
                             + ', '.join((unlisted + unowned)[:5])
                             + (f' and {len(unlisted + unowned) - 5} more' if len(unlisted + unowned) > 5 else ''))
    else:
        for p, body in files.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)
        for p in extra:
            p.unlink()
        if unlisted or unowned:
            MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f'SOURCE USE PASS — {len(outputs)-1} sources; {len(outputs["index.json"].encode())} index bytes; all source IDs resolve')


if __name__ == '__main__':
    main()
