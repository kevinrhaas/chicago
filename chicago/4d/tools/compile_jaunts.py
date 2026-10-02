#!/usr/bin/env python3
"""Compile declarative jaunts; exhaustively validate reachable finite story states."""
import argparse
import json
import operator
import re
from pathlib import Path
from jsonschema import Draft202012Validator
from compile_scene import cite

ROOT = Path(__file__).resolve().parents[1]
# Not jaunts: the content schema, and the visitor's daybook (T-1258), which every scene's
# catalog ships beside its jaunts so the Jaunts menu can rank keepsakes from data alone.
NOT_JAUNTS = {'schema.json', 'daybook.json'}
DAYBOOK_STYLES = {'receipt', 'chit', 'note', 'clipping', 'card'}
OPS = dict(zip(('<', '<=', '==', '>=', '>', '!='),
               (operator.lt, operator.le, operator.eq, operator.ge, operator.gt, operator.ne)))

def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default

def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def unique(rows, label):
    result = {r['id']: r for r in rows}
    require(len(result) == len(rows), f'duplicate {label} id')
    return result

class Compiler:
    def __init__(self, root=ROOT, scene_id="1835"):
        self.root, self.data = Path(root), Path(root) / 'data'
        self.schema = Draft202012Validator(read(self.data / 'jaunts/schema.json'))
        self.scene_id = str(scene_id)
        scene = read(self.data / f'scenes/{self.scene_id}.json')
        self.date = scene['target_date']
        index = read(self.data / f'sidecars/{self.scene_id}/index.json')
        self.refs = {'structure': {r['id']: read(self.data / r['sidecar']) for r in index['structures']},
                     'anchor': unique(scene['anchors'], 'anchor'),
                     'intersection': unique(index['intersections'], 'intersection'),
                     'person': unique(read(self.data / f'sidecars/{self.scene_id}/people.json', {}).get('people', []), 'person'),
                     'business': unique(read(self.data / 'businesses/index.json', {}).get('businesses', []) if self.scene_id == '1835' else [], 'business'),
                     'source': {p.stem: read(p) for p in (self.data / 'sources').glob('*.json')}}
        self.excluded = set(index.get('excluded_by_date', [])) | {
            r['id'] for r in (read(self.data / 'exclusions.json', {}).get('excluded', []) if self.scene_id == '1835' else [])}
        self.liberties = set(re.findall(r'^### (L[\w-]+) [—-]',
            (self.root / 'docs/LIBERTIES.md').read_text(errors='replace'), re.M))
        html = (self.root / 'renderers/web/index.html').read_text()
        self.refs['topic'] = {key: {} for key in re.findall(r'data-topic="([a-z-]+)"', html)}

    def resolve(self, ref, destination=False):
        kind, key = ref['kind'], ref['id']
        require(kind in self.refs, f'unsupported card kind {kind}; no topic registry yet')
        if kind == 'structure':
            require(key not in self.excluded, f'excluded date destination {key}')
        row = self.refs[kind].get(key)
        require(row is not None, f'dangling {kind} id {key}')
        if not destination:
            return None
        reasons = [f'{key} requires review'] if row.get('review_required') else []
        if kind == 'structure':
            period = row.get('documented_range', {})
            require((not period.get('from') or period['from'] <= self.date) and
                    (not period.get('to') or self.date <= period['to']), f'excluded date structure {key}')
        if kind == 'person':
            def val(v): return v.get('value') if isinstance(v, dict) else v
            places = [val(row.get(k)) for k in ('lives_at', 'works_at')]
            require(any(p in self.refs['structure'] for p in places), f'unlocated person {key}')
            for p in places:
                if p in self.refs['structure']:
                    inherited = self.resolve({'kind': 'structure', 'id': p}, True)
                    if inherited: reasons.append(inherited)
                    break
        if kind == 'business':
            where = row.get('where', {})
            require(row.get('present_at_scene_date') is True and
                    (not where.get('from') or where['from'] <= self.date) and
                    (not where.get('to') or self.date <= where['to']), f'excluded date business {key}')
            require(where.get('kind') == 'premises', f'unlocated business {key}; use a supported anchor')
            inherited = self.resolve({'kind': 'structure', 'id': where.get('structure_id')}, True)
            if inherited: reasons.append(inherited)
        return '; '.join(reasons) or None

    def validate(self, doc):
        errors = sorted(self.schema.iter_errors(doc), key=lambda e: str(e.path))
        require(not errors, 'schema: ' + (errors[0].message if errors else ''))
        require(doc['scene'] == self.scene_id, 'jaunt belongs to another scene')
        require(doc['default_mode'] in doc['allowed_modes'], 'default mode not allowed')
        stops, ends = unique(doc['stops'], 'stop'), unique(doc['endings'], 'ending')
        require(not (set(stops) & set(ends) or {'Previous', '$end'} & (set(stops) | set(ends))), 'duplicate/reserved node id')
        claims = unique(doc['evidence'], 'evidence')
        variables, inventory = doc.get('variables', {}), doc.get('inventory', {'items': [], 'initial': [], 'capacity': 0})
        for name, v in variables.items():
            require(v['min'] <= v['initial'] <= v['max'], f'unbounded variable {name}')
            require('money' not in name.lower() or v['unit'] == 'cents', 'money must use integer cents')
        require(set(inventory['initial']) <= set(inventory['items']) and len(inventory['initial']) <= inventory['capacity'], 'invalid initial inventory')
        for liberty in doc['liberties']:
            require(liberty.startswith('L') and liberty in self.liberties, f'unknown liberty {liberty}')
        for claim in claims.values():
            for sid in claim['sources']:
                self.resolve({'kind': 'source', 'id': sid})
            grade = claim['confidence']
            if grade == 'attested':
                require(claim['sources'] and claim.get('locator', '').strip(), 'attested claim needs source and locator')
            if grade == 'inferred':
                require(claim['sources'] and claim.get('reasoning', '').strip(), 'inferred claim needs sources and reasoning')
            if grade == 'reconstructed':
                require(claim.get('liberty') in doc['liberties'], 'reconstructed claim needs declared liberty')
        def condition(c):
            if 'var' in c:
                require(c['var'] in variables, f'undeclared variable {c["var"]}')
            elif 'has' in c:
                require(c['has'] in inventory['items'], f'undeclared item {c["has"]}')
            else:
                for key in ('all', 'any', 'not'):
                    for sub in ([c[key]] if key == 'not' else c[key]) if key in c else []:
                        condition(sub)
        def matches(c, state, items):
            if c is None: return True
            if 'all' in c: return all(matches(x, state, items) for x in c['all'])
            if 'any' in c: return any(matches(x, state, items) for x in c['any'])
            if 'not' in c: return not matches(c['not'], state, items)
            if 'has' in c: return c['has'] in items
            return OPS[c['op']](state[c['var']], c['value'])
        reasons = [doc['review_reason']] if doc['review_required'] and doc.get('review_reason') else []
        require(not doc['review_required'] or reasons, 'review_required needs reason')
        graph = {}
        for i, stop in enumerate(doc['stops']):
            require(25 <= len((stop['text'] + ' ' + stop.get('narrative', '')).split()) <= 60, f'{stop["id"]}: text needs 25–60 words')
            require(set(stop['evidence']) <= set(claims), 'dangling evidence id')
            reason = self.resolve(stop['destination'], True)
            if reason: reasons.append(reason)
            for link in stop.get('links', []): self.resolve(link)
            choices = stop.get('choices', [])
            unique(choices, 'choice')
            transitions = list(choices) + ([{'next': stop['next']}] if 'next' in stop else [])
            graph[stop['id']] = []
            for choice in transitions:
                if 'when' in choice: condition(choice['when'])
                nxt = choice.get('next', stop.get('next'))
                require(nxt in stops or nxt in ends or nxt in ('Previous', '$end'), 'dangling next edge')
                if nxt == 'Previous':
                    require(i > 0 and not choice.get('effects'), 'Previous needs a prior stop and no effects')
                    continue  # Explicit history navigation never makes a dead end viable.
                graph[stop['id']].append((nxt, choice))
                for eff in choice.get('effects', []):
                    if 'var' in eff:
                        require(eff['var'] in variables, 'undeclared effect variable')
                        v = variables[eff['var']]
                        require(eff['op'] != 'set' or v['min'] <= eff['value'] <= v['max'], 'unbounded set effect')
                        require(eff['op'] != 'inc' or abs(eff['value']) <= v['max'] - v['min'], 'unbounded increment effect')
                    else:
                        require(eff['item'] in inventory['items'], 'undeclared effect item')
        leg_edges = set()
        for i, leg in enumerate(doc.get('legs', [])):
            frm = leg.get('from', doc['stops'][i]['id'] if i < len(doc['stops']) else None)
            to = leg.get('to', doc['stops'][i + 1]['id'] if i + 1 < len(doc['stops']) else None)
            require(frm in stops and to in stops, 'leg needs valid stops')
            require(to in [edge[0] for edge in graph[frm]], 'leg must follow a stop transition')
            require((frm, to) not in leg_edges, 'duplicate leg')
            leg_edges.add((frm, to))
            require(leg.get('note') or leg.get('story'), 'empty leg')
            require(set(leg['evidence']) <= set(claims), 'dangling leg evidence')
            require(set(leg.get('story_evidence', [])) <= set(claims), 'dangling story evidence')
        require(sum(bool(e.get('default')) for e in ends.values()) <= 1, 'multiple default endings')
        for end in ends.values():
            if 'when' in end: condition(end['when'])
            require(not (end.get('default') and 'when' in end), 'default ending cannot be conditional')
        # Structural cycles are refused even behind conditions which happen to be false.
        def acyclic(node, active, done):
            if node not in stops or node in done: return
            require(node not in active, 'cycle; only explicit Previous is permitted')
            for nxt, _ in graph[node]: acyclic(nxt, active | {node}, done)
            done.add(node)
        done = set()
        for node in stops: acyclic(node, set(), done)
        visited, reached, terminal = set(), set(), set()
        def walk(node, state, items):
            key = (node, tuple(sorted(state.items())), tuple(sorted(items)))
            if key in visited: return
            visited.add(key)
            require(len(visited) <= 100000, 'state space exceeds 100000; simplify branches')
            if node == '$end':
                viable = [e for e in ends.values() if not e.get('default') and matches(e.get('when'), state, items)]
                if not viable: viable = [e for e in ends.values() if e.get('default')]
                require(viable, 'no viable ending for reachable state')
                terminal.add(viable[0]['id'])  # authored order is ending priority
                return
            if node in ends:
                require(matches(ends[node].get('when'), state, items), 'no viable ending for reachable state')
                terminal.add(node)
                return
            reached.add(node)
            viable = [(n, c) for n, c in graph[node] if matches(c.get('when'), state, items)]
            require(viable, f'{node}: no viable choice/default/skip for reachable state')
            for nxt, choice in viable:
                new, bag = state.copy(), set(items)
                for eff in choice.get('effects', []):
                    if 'var' in eff:
                        var = eff['var']
                        new[var] = eff['value'] if eff['op'] == 'set' else new[var] + eff['value']
                        require(variables[var]['min'] <= new[var] <= variables[var]['max'], f'unbounded effect on {var}')
                    elif eff['op'] == 'add': bag.add(eff['item'])
                    else: bag.discard(eff['item'])
                    require(len(bag) <= inventory['capacity'], 'inventory capacity exceeded')
                walk(nxt, new, bag)
        walk(doc['stops'][0]['id'], {k: v['initial'] for k, v in variables.items()}, set(inventory['initial']))
        require(reached == set(stops), 'unreachable stop')
        require(terminal == set(ends), 'unreachable ending')
        return sorted(set(reasons))

    def compile(self, source=None):
        source = Path(source) if source else self.data / 'jaunts'
        catalog, files, errors, ids = [], {}, [], set()
        for path in sorted(source.glob('*.json')):
            if path.name in NOT_JAUNTS: continue
            try:
                doc = read(path)
                if doc.get('scene') != self.scene_id: continue
                reasons = self.validate(doc)
                require(doc['id'] not in ids, 'duplicate jaunt id')
                require(path.stem == doc['id'], 'filename must match jaunt id')
                ids.add(doc['id'])
                row = {k: doc[k] for k in ('id', 'title', 'premise', 'category', 'content_version', 'default_mode', 'allowed_modes')}
                row.update(stop_count=len(doc['stops']), primary_family=doc['keepsake']['family'], secondary_family=doc.get('secondary_family'),
                           timing={'opening_read_s': doc['opening']['read_s'], 'stops': [{'read_s': s['read_s'], 'action_s': s.get('action_s', 0)} for s in doc['stops']], 'endings_read_s': [e['read_s'] for e in doc['endings']]},
                           destinations=[s['destination'] for s in doc['stops']], availability='unavailable' if reasons else 'available', reason='; '.join(reasons) or None)
                catalog.append(row)
                citations = cite({sid for claim in doc['evidence'] for sid in claim['sources']}, self.refs['source'])
                files[doc['id'] + '.json'] = packed({**doc, 'citations': citations})
            except (ValueError, KeyError, TypeError) as error:
                errors.append(f'{path.name}: {error}')
        files['catalog.json'] = packed({'schema_version': 1, 'scene': self.scene_id, 'jaunts': catalog})
        files['daybook.json'] = packed(self.daybook())
        return files, errors

    def daybook(self):
        """T-1258: families must be exactly the keepsake families a jaunt may name, and the
        ranks a strictly rising ladder from 0, so changing a threshold re-ranks with no code."""
        doc = read(self.data / 'jaunts/daybook.json')
        require(doc and doc.get('schema_version') == 1 and isinstance(doc.get('content_version'), int), 'daybook: bad versions')
        allowed = self.schema.schema['properties']['keepsake']['properties']['family']['enum']
        families = doc.get('families') or []
        require([f.get('name') for f in families] == allowed, f'daybook: families must be {allowed}')
        unique(families, 'daybook family')
        for f in families:
            require(re.fullmatch(r'[a-z][a-z_]*', f['id']) and f.get('description') and f.get('icon'), f'daybook: family {f["id"]} incomplete')
            t = f.get('template') or {}
            require(t.get('form') and t.get('lead') and t.get('style') in DAYBOOK_STYLES, f'daybook: family {f["id"]} template incomplete')
        ranks = doc.get('ranks') or []
        unique(ranks, 'daybook rank')
        levels = [r.get('threshold') for r in ranks]
        require(len(ranks) >= 2 and all(isinstance(v, int) for v in levels) and levels[0] == 0
                and all(a < b for a, b in zip(levels, levels[1:])), 'daybook: rank thresholds must rise strictly from 0')
        require(all(r.get('title') for r in ranks) and doc.get('disclaimer'), 'daybook: ranks need titles and the book its disclaimer')
        return doc

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--source', type=Path, help='alternate content directory, e.g. isolated fixtures')
    ap.add_argument('--output', type=Path, help='alternate output directory')
    ap.add_argument('--scene', help='compile one scene; defaults to all published scenes')
    args = ap.parse_args()
    scenes = sorted(p.stem for p in (ROOT / 'data/scenes').glob('*.json') if (ROOT / f'data/sidecars/{p.stem}/index.json').exists())
    if args.scene: require(args.scene in scenes, 'unknown scene')
    # Preserve the isolated fixture CLI: a custom output is a single catalog.
    selected = [args.scene or '1835'] if args.scene or args.output else scenes
    source = args.source or ROOT / 'data/jaunts'
    for path in source.glob('*.json'):
        if path.name not in NOT_JAUNTS: require(read(path).get('scene') in scenes, f'{path.name}: unknown or missing scene')
    for scene_id in selected:
        compile_scene_jaunts(args, scene_id)

def compile_scene_jaunts(args, scene_id):
    files, errors = Compiler(scene_id=scene_id).compile(args.source)
    dest = args.output or ROOT / f'data/sidecars/{scene_id}/jaunts'
    stale = [name for name, body in files.items() if not (dest / name).exists() or (dest / name).read_text() != body]
    extra = set(p.name for p in dest.glob('*.json')) - set(files)
    if args.check:
        require(not stale and not extra, 'stale jaunts; run python3 tools/compile_jaunts.py')
    else:
        dest.mkdir(parents=True, exist_ok=True)
        for name, body in files.items(): (dest / name).write_text(body)
        for name in extra: (dest / name).unlink()
    for error in errors: print('JAUNT REFUSED — ' + error)
    require(not errors, f'{len(errors)} malformed jaunt(s); valid catalog entries preserved')
    print(f'JAUNTS PASS — {len(files)-2} jaunts; {len(files["catalog.json"].encode())} catalog bytes')

if __name__ == '__main__':
    main()
