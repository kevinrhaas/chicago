#!/usr/bin/env python3
"""Compile declarative jaunts; exhaustively validate reachable finite story states."""
import argparse
import datetime as dt
import functools
import json
import math
import operator
import re
from pathlib import Path
from jsonschema import Draft202012Validator
from compile_scene import cite
import jaunt_names
import jaunt_place_facts

ROOT = Path(__file__).resolve().parents[1]
# Not jaunts: the content schema, and the visitor's daybook (T-1258), which every scene's
# catalog ships beside its jaunts so the Jaunts menu can rank keepsakes from data alone.
NOT_JAUNTS = {'schema.json', 'daybook.json'}
DAYBOOK_STYLES = {'receipt', 'chit', 'note', 'clipping', 'card'}
OPS = dict(zip(('<', '<=', '==', '>=', '>', '!='),
               (operator.lt, operator.le, operator.eq, operator.ge, operator.gt, operator.ne)))

# T-3459: a dated stop's season by its month, as jaunts.js seasonOfDate gives it.
MONTH_SEASON = ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'fall', 'fall', 'fall', 'winter']

def season_of_date(date):
    m = re.fullmatch(r'\d{4}-(\d{2})-\d{2}', date or '')
    return MONTH_SEASON[int(m.group(1)) - 1] if m and 1 <= int(m.group(1)) <= 12 else None

def opening_light(doc):
    """T-3459: the hour and season a jaunt's first scene is shown in (jaunts.js openingLight)."""
    first, amb = (doc.get('stops') or [{}])[0], doc.get('ambience') or {}
    hour, season = first.get('hour') or amb.get('hour'), season_of_date(first.get('date')) or amb.get('season')
    return {k: v for k, v in (('hour', hour), ('season', season)) if v} or None

def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default

def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'

def require(ok, message):
    if not ok:
        raise ValueError(message)

@functools.cache
def time_names():
    """T-3328: the setting's named times, read from the one list the app uses (T-3331)."""
    js = (ROOT / 'renderers/web/js/time-of-day.js').read_text()
    block = js.split('export const TIME_NAMES = [', 1)[1].split('];', 1)[0]
    return frozenset(re.findall(r"id: '([a-z-]+)'", block))

@functools.cache
def time_at():
    """T-3406: each named time's `at` ('09:00', 'rise', 'set', 'civil-dusk', 'scene')."""
    js = (ROOT / 'renderers/web/js/time-of-day.js').read_text()
    block = js.split('export const TIME_NAMES = [', 1)[1].split('];', 1)[0]
    return dict(re.findall(r"id: '([a-z-]+)', label: '[^']*', at: '([^']+)'", block))

# T-3406: THE STORY'S CLOCK. The owner, 2026-11-06: start each stop "with have like 6 months
# later, or a few hours later, or 4 hours later, to give people a sense of what they just
# left and how much time has past". A stop's `since` is that lead. It is checked against
# the date and hour the two stops already show, so a stop whose date or hour moves without
# its lead fails here instead of telling the visitor the wrong gap.
CHICAGO_LAT = 41.8867  # world.js's sun station
NUMBER_WORDS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen '
    'fifteen sixteen seventeen eighteen nineteen twenty'.split())}
NUMBER_WORDS.update(a=1, an=1, thirty=30, forty=40, fifty=50, sixty=60, seventy=70, eighty=80, ninety=90)
UNIT_MIN = {'minute': 1, 'hour': 60, 'day': 1440, 'week': 10080, 'month': 43830, 'year': 525960}

def sun_crossing(day, elevation, rising):
    """Local mean solar minutes at which the sun's centre crosses `elevation` degrees on
    `day`, from the low-precision almanac series (declination and equation of time). It
    lands within a few minutes of world.js's solarPosition, which is all a lead rounded
    to the nearest hour or minute-ten needs; the app itself never reads this."""
    g = 2 * math.pi / 365 * (day.timetuple().tm_yday - 1)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eot = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    phi = math.radians(CHICAGO_LAT)
    cos_h = (math.sin(math.radians(elevation)) - math.sin(phi) * math.sin(decl)) / (math.cos(phi) * math.cos(decl))
    half = math.degrees(math.acos(max(-1, min(1, cos_h)))) * 4
    return 720 - eot + (-half if rising else half)

def stop_moment(stop):
    """The clock a stop shows, as a datetime: its date plus its hour, a named time solved
    and snapped the way time-of-day.js resolveTime snaps it (daybreak up, sunset down,
    dusk to the nearest ten minutes)."""
    require(stop.get('date') and stop.get('hour'), f'{stop["id"]}: a since needs this stop and the one before it to carry a date and an hour')
    day, hour = dt.date.fromisoformat(stop['date']), stop['hour']
    at = time_at().get(hour, hour)
    require(at != 'scene', f'{stop["id"]}: a since cannot count from or to "daytime", which is the scene\'s own hour; give the stop a clock time')
    if re.fullmatch(r'\d\d:\d\d', at):
        minutes = int(at[:2]) * 60 + int(at[3:])
    else:
        event = sun_crossing(day, 1.0 if at in ('rise', 'set') else -6.0, at == 'rise')
        minutes = (math.ceil(event / 10) if at == 'rise' else math.floor(event / 10) if at == 'set' else round(event / 10)) * 10
    return dt.datetime.combine(day, dt.time()) + dt.timedelta(minutes=minutes)

def since_fits(phrase, before, after):
    """Whether a lead such as 'Four hours later' says the gap between two stop clocks.
    The vocabulary is small on purpose: a count of minutes, hours, days, weeks, months or
    years 'later' (within half a unit, or 15% of a long count), 'Within the hour',
    'A few hours later', 'The next day', 'The next morning', 'That evening', 'That night'.
    T-3459: a story that opens on its ending (a cold open) goes back with a count of
    days, weeks, months or years 'earlier', checked the same way against the gap back."""
    gap = (after - before).total_seconds() / 60
    days = (after.date() - before.date()).days
    said = phrase.strip().rstrip('.').lower()
    back = re.fullmatch(r'([a-z]+|\d+) (day|week|month|year)(s?) earlier', said)
    if back:
        count = int(back[1]) if back[1].isdigit() else NUMBER_WORDS.get(back[1])
        if gap >= 0 or count is None or (count == 1) == bool(back[3]): return False
        return abs(-gap / UNIT_MIN[back[2]] - count) <= max(0.5, 0.15 * count)
    if gap <= 0: return False
    fixed = {'within the hour': gap <= 60, 'a few hours later': 90 <= gap <= 390,
             'the next day': days == 1, 'the next morning': days == 1 and after.hour < 12,
             'that evening': days == 0 and after.hour >= 17, 'that night': days == 0 and after.hour >= 19}
    if said in fixed: return fixed[said]
    m = re.fullmatch(r'([a-z]+|\d+) (minute|hour|day|week|month|year)(s?) later', said)
    if not m: return False
    count = int(m[1]) if m[1].isdigit() else NUMBER_WORDS.get(m[1])
    if count is None or (count == 1) == bool(m[3]): return False
    return abs(gap / UNIT_MIN[m[2]] - count) <= max(0.5, 0.15 * count)

def check_since(doc):
    """T-3406: in a jaunt that tells its clock, every stop after the first says how long
    since the one before, and says it truly; the first has nothing to count from."""
    stops = doc['stops']
    if not any('since' in s for s in stops): return
    require('since' not in stops[0], f'{stops[0]["id"]}: the first stop has no stop before it to count a since from')
    for before, stop in zip(stops, stops[1:]):
        require('since' in stop, f'{stop["id"]}: this jaunt tells its clock, so every stop after the first needs a since')
        require(before.get('next') == stop['id'], f'{stop["id"]}: a since counts from the stop before, which must lead straight here')
        a, b = stop_moment(before), stop_moment(stop)
        require(since_fits(stop['since'], a, b),
                f'{stop["id"]}: since {stop["since"]!r} does not say the {(b - a).total_seconds() / 3600:.1f} hours from {before["id"]} ({a:%Y-%m-%d %H:%M}) to here ({b:%Y-%m-%d %H:%M})')

def leg_mode(doc, i):
    """T-3355: the catalog row's stop i carries the mode of the authored leg that reaches it, if any."""
    if not i: return {}
    frm, to = doc['stops'][i - 1]['id'], doc['stops'][i]['id']
    for j, leg in enumerate(doc.get('legs', [])):
        if leg.get('mode') and leg.get('from', doc['stops'][j]['id'] if j < len(doc['stops']) else None) == frm \
                and leg.get('to', doc['stops'][j + 1]['id'] if j + 1 < len(doc['stops']) else None) == to:
            return {'leg_mode': leg['mode']}
    return {}

# T-3525: how far from a stop's stand its host may stand: near enough to meet, clear of the visitor.
HOST_REACH_M = 12

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
        check_since(doc)
        reasons = [doc['review_reason']] if doc['review_required'] and doc.get('review_reason') else []
        require(not doc['review_required'] or reasons, 'review_required needs reason')
        graph = {}
        for i, stop in enumerate(doc['stops']):
            # T-3355: a long-form story jaunt tells each stop in full, up to 150 words.
            most = 150 if doc.get('long_form') else 60
            require(25 <= len((stop['text'] + ' ' + stop.get('narrative', '')).split()) <= most, f'{stop["id"]}: text needs 25–{most} words')
            require(set(stop['evidence']) <= set(claims), 'dangling evidence id')
            # T-3328: a stop's hour rests on its own claims, and names only a time the setting knows.
            if 'hour' in stop or 'date' in stop or 'hour_evidence' in stop:
                require('hour' in stop and stop.get('hour_evidence'), f'{stop["id"]}: an hour needs hour_evidence, and a date or hour_evidence needs an hour')
                require(set(stop['hour_evidence']) <= set(stop['evidence']), f'{stop["id"]}: hour_evidence must be among the stop\'s own evidence')
                require(stop['hour'] in time_names() or re.fullmatch(r'([01][0-9]|2[0-3]):[0-5][0-9]', stop['hour']),
                        f'{stop["id"]}: hour {stop["hour"]!r} is neither HH:MM nor a named time in time-of-day.js')
                if 'date' in stop:
                    try: dt.date.fromisoformat(stop['date'])
                    except ValueError: require(False, f'{stop["id"]}: date {stop["date"]!r} is not a day')
            reason = self.resolve(stop['destination'], True)
            if reason: reasons.append(reason)
            for link in stop.get('links', []): self.resolve(link)
            # T-3495: the people a stop calls for are people of this scene.
            for pid in stop.get('people', []): self.resolve({'kind': 'person', 'id': pid})
            # T-3525: a stop's hosts are people of this scene, each once, standing where the
            # visitor at the stop can meet them: within HOST_REACH_M of an anchor's stand.
            hosts = stop.get('hosts', [])
            unique([{'id': h['person']} for h in hosts], f'{stop["id"]} host')
            for h in hosts:
                self.resolve({'kind': 'person', 'id': h['person']})
                d = stop['destination']
                if d['kind'] == 'anchor':
                    a = self.refs['anchor'][d['id']]
                    far = math.hypot(h['local_e'] - a['local_e'], h['local_n'] - a['local_n'])
                    require(0.8 <= far <= HOST_REACH_M, f'{stop["id"]}: host {h["person"]} stands {far:.1f} m from the stand; '
                            f'a host stands 0.8-{HOST_REACH_M:g} m from it')
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
            # T-3355: a leg's own mode (a long ride Instantly) is one the jaunt allows.
            require('mode' not in leg or leg['mode'] in doc['allowed_modes'], 'leg mode not allowed')
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
        # T-2946: one name per building for a stop's heading and its road notes, in every jaunt.
        places = jaunt_names.names(self.scene_id, list(self.refs['structure'].values()))
        # T-3379: a sourced fact for each building a road note passes, cited like any claim.
        facts = jaunt_place_facts.facts(self.scene_id, list(self.refs['structure'].values()))
        errors_facts = jaunt_place_facts.check(self.scene_id, list(self.refs['structure'].values()), self.refs['source'])
        for path in sorted(source.glob('*.json')):
            if path.name in NOT_JAUNTS or path.name == 'catalog-55.json': continue  # Harness catalog, not a story.
            try:
                doc = read(path)
                if doc.get('scene') != self.scene_id: continue
                reasons = self.validate(doc)
                require(doc['id'] not in ids, 'duplicate jaunt id')
                require(path.stem == doc['id'], 'filename must match jaunt id')
                ids.add(doc['id'])
                row = {k: doc[k] for k in ('id', 'title', 'premise', 'category', 'content_version', 'default_mode', 'allowed_modes')}
                # T-3377: the light it is walked in; T-3459: the light it opens in (jaunts.js
                # openingLight), so a story jaunt of dated stops says its first scene's season.
                light = opening_light(doc)
                if light: row['ambience'] = light
                row.update(featured=doc.get('featured', False), stop_count=len(doc['stops']), primary_family=doc['keepsake']['family'], secondary_family=doc.get('secondary_family'),
                           timing={'opening_read_s': doc['opening']['read_s'], 'stops': [{'read_s': s['read_s'], 'action_s': s.get('action_s', 0), **leg_mode(doc, i)} for i, s in enumerate(doc['stops'])], 'endings_read_s': [e['read_s'] for e in doc['endings']]},
                           destinations=[s['destination'] for s in doc['stops']], availability='unavailable' if reasons else 'available', reason='; '.join(reasons) or None)
                catalog.append(row)
                citations = cite({sid for claim in doc['evidence'] for sid in claim['sources']}, self.refs['source'])
                files[doc['id'] + '.json'] = packed({**doc, 'citations': citations, **({'places': places} if places else {}),
                                                     **({'place_facts': facts} if facts else {})})
            except (ValueError, KeyError, TypeError) as error:
                errors.append(f'{path.name}: {error}')
        errors.extend(errors_facts)
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
