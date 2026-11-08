# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3463..T-3467: stand everyone else of 1812 Chicago in the town, each at their own day.

The owner, 2026-11-08: *"What about the rest of the 1812 people John Kinzie, Black Partridge,
etc"*, *"Right everyone! lalime and everyone"*, *"Follow the same rules for deployment of these
people some inside and others active and doing what they would be doing as normal activities
per time of day"*, *"If they are inside I can walk to door and ask for any person inside"* and
*"if we set to winter lalime would exist and we will need him for the murder jaunt"*.

Five readings beside the garrison's give each person their day, hour by hour, for each run of
dates in which it differs (docs/RESEARCH/people-1812-34NN/day.json; NN = 63 officers, 64 women,
65 children, 66 civilian men, 67 Potawatomi and Miami people). Every span there carries its own
grade and basis; this script only turns them into human instance records
(data/humans/instances/1812/hi_town_<person>_1812.json) that renderers/web/js/human-days.js plays:

  presence     the person's own {from, to}
  day          one variant per run of dates ({dates, spans}); a span is indoors in a building
               (its door then offers Ask for them), out at a point doing stand / talk / work /
               walk, or `away` (off the scene: gone out of the gate with the column, at Milwaukee)

What it decides, said here:

  * ACTIVITIES. The readings use a wider word list than the runtime plays. `sit` (no seated
    clip yet) and `knot` are a talk when anyone is beside them, else a stand; `tend`, `paddle`
    and `carry` with no second point are work at the place; `carry` and `ride` with a second
    point are a walk between the two. The reading's own `doing` is kept on the span.
  * TALK. Spans in which people stand within TALK_M of one another at overlapping hours are one
    talk (a shared `knot`); the readings' own knot ids are kept and joined.
  * WORK AND WALK POINTS. A work span with no `spots` gets two, 1.4 m either side of the
    person across their heading; a walk with no `to_point` gets one 7 m ahead. Each is moved,
    or dropped, until it is CLEAR_M clear of every 1812 footprint.
  * INFANTS in arms are not drawn (there is no carried pose); they stay on their cards.
  * A DRESS is the role asset the reading's dress role maps to (DRESS); a role with no asset
    built yet leaves its people on their cards, not drawn, and the script says who.

Liberty L-1812-town-days-3463 (the hours, places and companions are reconstructed).

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-town/place_town.py [--check]
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INST = ROOT / 'data/humans/instances/1812'
DOORS = ROOT / 'data/humans/doors_1812.json'
SIDECARS = ROOT / 'data/sidecars/1812'
READINGS = [ROOT / f'docs/RESEARCH/people-1812-{t}/day.json' for t in (3463, 3464, 3465, 3466, 3467)]
LIBERTY = 'L-1812-town-days-3463'
PREFIX = 'hi_town_'
TALK_M = 4.0
CLEAR_M = 0.6

# The reading's dress role -> the role asset drawn (assets/humans/web/<asset>.lod*.glb). A role
# not here (or whose asset is not built) leaves its people undrawn.
DRESS = {
    'officer_first_infantry_1812': 'officer_first_infantry_1812',
    # Folded to save the published site's bytes (owner, 2026-11-08: the 432 MB budget): the
    # surgeon's mate, the lieutenant and the woman of the country are drawn in the officer's
    # and the working woman's dresses; their own builds stay in assets/ for when room is made.
    'surgeons_mate_1812': 'officer_first_infantry_1812',
    # Wells on the 14th in frontier dress (deerskin, belt, moccasins), nearer the record than a
    # trader's breeches and top boots; no asset draws his own.
    'wells_frontier_agent_1812': 'engage_1812',
    'trader_1812': 'trader_1812',
    'officer_wife_1812': 'lady_1812',
    'trader_wife_matron_1812': 'lady_1812',
    'soldier_wife_laundress_1812': 'woman_working_1812',
    'working_woman_enslaved_1812': 'woman_working_1812',
    'woman_of_the_country_1812': 'woman_working_1812',
    'boy_jacket_trousers_1812': 'child_boy_1812',
    'boy_skeleton_suit_1812': 'child_boy_1812',
    'boy_of_the_country_1812': 'child_boy_1812',
    'girl_frock_pinafore_1812': 'child_girl_1812',
    'girl_of_the_country_1812': 'child_girl_1812',
    'child_frock_toddler_1812': 'child_toddler_1812',
    'engage_1812': 'engage_1812',
    'potawatomi_man_1812': 'potawatomi_man_1812',
    'potawatomi_woman_1812': 'potawatomi_woman_1812',
    'potawatomi_child_1812': 'potawatomi_boy_1812',   # potawatomi_girl_1812 for a girl, below
    'potawatomi_chief_1812': 'potawatomi_man_1812',
    'potawatomi_elder_1812': 'potawatomi_man_1812',
    'potawatomi_elder_woman_1812': 'potawatomi_woman_1812',
    'miami_escort_1812': 'potawatomi_man_1812',   # no source gives the escort a dress of its own (T-3467)
    'settler_1812': 'settler_1812',
    'black_servant_1812': 'settler_1812',
}


GROWN_FROM = 12
GROWN = {'potawatomi_boy_1812': 'potawatomi_man_1812', 'potawatomi_girl_1812': 'potawatomi_woman_1812',
         'child_boy_1812': 'settler_1812', 'child_girl_1812': 'woman_working_1812'}
# A child younger than this wears the toddler's frock on the three-year-old's body.
TODDLER_UNDER = 5


def asset_built(asset: str) -> bool:
    return all((ROOT / f'assets/humans/web/{asset}.lod{k}.glb').is_file() for k in range(4))


# ── the town's footprints, for clearance ─────────────────────────────────────────────
def to_world(u, v, pl):
    th = math.radians(float(pl.get('rotation_deg') or 0.0))
    c, s = math.cos(th), math.sin(th)
    return (float(pl['local_e']) + u * c + v * s, float(pl['local_n']) - u * s + v * c)


def footprints():
    out = []
    for f in sorted(SIDECARS.glob('*.json')):
        sc = json.loads(f.read_text())
        if not isinstance(sc, dict) or 'placement' not in sc:
            continue
        poly = (sc.get('footprint') or {}).get('polygon') or []
        if len(poly) < 3 or sc.get('archetype') in ('field', 'garden', 'parade', 'yard', 'camp') or 'camp' in sc['id']:
            continue
        if any(k in sc['id'] for k in ('parade', 'garden', 'field', 'cornfield', 'covered_way', 'green', 'pickets')):
            continue
        out.append((sc['id'], [to_world(u, v, sc['placement']) for u, v in poly]))
    return out


FOOT = footprints()


def _inside(p, poly):
    x, y = p
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _edge_d(p, poly):
    best = 1e9
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = 0 if L < 1e-12 else max(0, min(1, ((p[0] - x1) * dx + (p[1] - y1) * dy) / L))
        best = min(best, math.hypot(x1 + t * dx - p[0], y1 + t * dy - p[1]))
    return best


def clear(p, margin=CLEAR_M):
    return all(not _inside(p, poly) and _edge_d(p, poly) >= margin for _, poly in FOOT)


def blocked_by(p):
    return [sid for sid, poly in FOOT if _inside(p, poly) or _edge_d(p, poly) < CLEAR_M]


# ── readings ──────────────────────────────────────────────────────────────────────────
def readings():
    people = []
    for path in READINGS:
        if not path.exists():
            continue
        d = json.loads(path.read_text())
        ticket = d['meta']['ticket']
        for p in d['people']:
            people.append((ticket, p))
    return people


def pid_of(p):
    return p['person_id'].split(':', 1)[1] if p['person_id'].startswith('new:') else p['person_id']


WORDS = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
         'twelve': 12, 'fifteen': 15, 'twenty': 20, 'thirty': 30}


def chance_of(freq):
    """'about one day in five' -> 0.2; None when it says nothing countable."""
    if not freq:
        return None
    words = str(freq).lower().replace('-', ' ').split()
    if 'in' in words:
        n = words[words.index('in') + 1:words.index('in') + 2]
        if n and (n[0] in WORDS or n[0].isdigit()):
            return round(1 / (WORDS.get(n[0]) or int(n[0])), 3)
    return None


def variants_of(p):
    """[(dates, label/note, spans, chance)]: a reading's dated `days` in order (a `recurs` run
    as months over a run of years; an `absent` run as a day away), then its lone `day` as the
    day of every other date. `alt_days` (another reading's dates, e.g. Wells's arrival on the
    14th instead of the 13th) are not played."""
    out = []
    for d in p.get('days') or []:
        dates = {k: v for k, v in (('from', d.get('from_date')), ('to', d.get('to_date'))) if v}
        rec = d.get('recurs')
        if rec:
            if rec.get('months'):
                dates['months'] = sorted(int(m) for m in rec['months'])
            ys = str(rec.get('years') or '')
            if ys:
                a, _, b = ys.partition('-')
                dates['years'] = {'from': int(a), 'to': int(b or a)}
        if not dates:
            continue
        spans = d.get('day') or []
        if d.get('absent'):
            spans = [{'from': 0, 'to': 24, 'indoors': True, 'away': True, 'doing': str(d.get('label') or 'away')}]
        out.append((dates, d.get('label') or d.get('note'), spans, chance_of(d.get('frequency'))))
    if p.get('day'):
        out.append(({}, None, p['day'], None))
    return out


def seeded(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def point(at):
    return {'local_e': round(float(at['local_e']), 2), 'local_n': round(float(at['local_n']), 2)}


def work_spots(at, key):
    h = math.radians(float(at.get('heading_deg') or 0))
    across = (math.cos(h), -math.sin(h))   # to the right of the heading
    out = []
    for side in (1, -1):
        for r in (1.4, 1.0, 0.7):
            p = (at['local_e'] + side * r * across[0], at['local_n'] + side * r * across[1])
            if clear(p):
                out.append({'local_e': round(p[0], 2), 'local_n': round(p[1], 2)})
                break
    return out


def walk_end(at, key):
    h0 = float(at.get('heading_deg') or 0)
    for dh in (0, 30, -30, 60, -60, 90, -90, 180):
        h = math.radians(h0 + dh)
        for r in (7.0, 5.0, 3.5):
            p = (at['local_e'] + r * math.sin(h), at['local_n'] + r * math.cos(h))
            if clear(p) and all(clear((at['local_e'] + f * (p[0] - at['local_e']), at['local_n'] + f * (p[1] - at['local_n'])))
                                for f in (0.25, 0.5, 0.75)):
                return {'local_e': round(p[0], 2), 'local_n': round(p[1], 2)}
    return None


def _xy(q):
    return (float(q[0]), float(q[1])) if isinstance(q, (list, tuple)) else (float(q['local_e']), float(q['local_n']))


def bearing(a, b):
    return (math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360) % 360


# Not drawn for the span: no canoe, no lying-down pose, no one carried, nothing afloat.
NOT_DRAWN = ('paddle', 'sleep')
UNDRAWN_HOMES = set()


def span_of(s, key, problems, doors):
    out = {'from': float(s['from']), 'to': float(s['to'])}
    act = s.get('activity')
    unseen = (s.get('offscene') or s.get('away') or s.get('drawn') is False or s.get('carried_by') or s.get('afloat')
              or (not s.get('indoors') and (act in NOT_DRAWN or (not s.get('at') and not s.get('route')))))
    if unseen:
        return {**out, 'indoors': True, 'away': True, 'doing': s.get('doing', '')[:200]}
    if not s.get('indoors') and s.get('route'):
        route = [_xy(q) for q in s['route']]
        if len(route) >= 2:
            pts = [{'local_e': round(e, 2), 'local_n': round(n, 2)} for e, n in route]
            for q in route:
                if not clear(q, 0.25):
                    problems.append(f'{key}: the route point {q} stands in {blocked_by(q)}')
            return {**out, 'indoors': False, 'at': {**pts[0], 'heading_deg': round(bearing(route[0], route[1]), 1)},
                    'activity': 'walk', 'to_point': pts[-1], **({'via': pts[1:-1]} if len(pts) > 2 else {}), 'once': True,
                    'doing': s.get('doing', '')[:200], '_with': list(s.get('with') or []), '_knot': None}
        s = {**s, 'at': {'local_e': route[0][0], 'local_n': route[0][1], 'heading_deg': (s.get('at') or {}).get('heading_deg', 0)}}
    if s.get('indoors'):
        where = s.get('where')
        if where not in doors:
            # In a building the town does not draw (Fettle's cabin, Currey): off the scene.
            UNDRAWN_HOMES.add(where)
            return {**out, 'indoors': True, 'away': True, 'doing': s.get('doing', '')[:200]}
        return {**out, 'indoors': True, 'where': where, 'doing': s.get('doing', '')[:200]}
    at = s.get('at')
    if not at:
        problems.append(f'{key}: an outdoor span with no point')
        return None
    if not clear((at['local_e'], at['local_n']), 0.25):
        problems.append(f"{key}: ({at['local_e']}, {at['local_n']}) stands in {blocked_by((at['local_e'], at['local_n']))}")
    act = s.get('activity') or 'stand'
    span = {**out, 'indoors': False, 'at': {**point(at), 'heading_deg': round(float(at.get('heading_deg') or 0) % 360, 1)},
            'doing': s.get('doing', '')[:200], '_with': list(s.get('with') or []), '_knot': s.get('knot')}
    if act in ('sit', 'knot', 'talk'):
        span['activity'] = 'talk'
    elif act in ('work', 'tend', 'paddle') or (act == 'carry' and not s.get('to_point')):
        span['activity'] = 'work'
        spots = [point(x) for x in (s.get('spots') or []) if clear((x['local_e'], x['local_n']))] or work_spots(at, key)
        if spots:
            span['spots'] = spots
    elif act in ('walk', 'carry', 'ride'):
        end = s.get('to_point')
        end = point(end) if end and clear((end['local_e'], end['local_n'])) else walk_end(at, key)
        if end:
            span['activity'] = 'walk'
            span['to_point'] = end
        else:
            span['activity'] = 'stand'
    else:
        span['activity'] = 'stand'
    return span


def overlaps(a, b):
    def parts(s):
        return [(s['from'], s['to'])] if s['from'] <= s['to'] else [(s['from'], 24), (0, s['to'])]
    return any(x0 < y1 and y0 < x1 for x0, x1 in parts(a) for y0, y1 in parts(b))


def join_talks(records):
    """Every talk-ish span near another person's at an overlapping hour, on a date both hold,
    is one knot; a talk with nobody beside it is a stand."""
    spans = []
    for pid, rec in records.items():
        for vi, v in enumerate(rec['behaviour']['day']):
            for si, s in enumerate(v['spans']):
                if not s['indoors'] and not s.get('away'):
                    spans.append((pid, v.get('dates') or {}, s))
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def dates_meet(a, b):
        return (a.get('from') or '0000') <= (b.get('to') or '9999') and (b.get('from') or '0000') <= (a.get('to') or '9999')

    talky = [(i, x) for i, x in enumerate(spans) if x[2]['activity'] == 'talk' or x[2].get('_knot')]
    by_knot = {}
    for i, (pid, dates, s) in talky:
        if s.get('_knot'):
            by_knot.setdefault(s['_knot'], []).append(i)
    for ids in by_knot.values():
        for i in ids[1:]:
            union(ids[0], i)
    for a in range(len(talky)):
        for b in range(a + 1, len(talky)):
            i, (p1, d1, s1) = talky[a]
            j, (p2, d2, s2) = talky[b]
            if p1 == p2 or not dates_meet(d1, d2) or not overlaps(s1, s2):
                continue
            if math.hypot(s1['at']['local_e'] - s2['at']['local_e'], s1['at']['local_n'] - s2['at']['local_n']) <= TALK_M:
                union(i, j)
    groups = {}
    for i, _ in talky:
        groups.setdefault(find(i), []).append(i)
    for members in groups.values():
        people = {spans[i][0] for i in members}
        knot_ids = sorted({spans[i][2].get('_knot') for i in members if spans[i][2].get('_knot')})
        kid = knot_ids[0] if knot_ids else 'talk_' + hashlib.sha256('|'.join(sorted(f"{spans[i][0]}:{spans[i][2]['from']}" for i in members)).encode()).hexdigest()[:8]
        for i in members:
            s = spans[i][2]
            if len(people) >= 2:
                s['activity'] = 'talk'
                s['knot'] = kid
            elif s['activity'] == 'talk':
                s['activity'] = 'stand'
    for _, _, s in spans:
        s.pop('_with', None); s.pop('_knot', None)
        if s['activity'] == 'talk' and 'knot' not in s:
            s['activity'] = 'stand'


def first_point(variants, doors):
    pref = [v for v in variants if (v.get('dates') or {}).get('from', '') <= '1812-08-14' <= (v.get('dates') or {}).get('to', '9999')] + variants
    for v in pref:
        for s in v['spans']:
            if not s['indoors']:
                return s['at']
    for v in pref:
        for s in v['spans']:
            if s.get('where') in doors:
                st = doors[s['where']]['doors'][0]
                return {**st['step'], 'heading_deg': st['outward_deg']}
    return None


def build():
    doors = {s['structure']: s for s in json.loads(DOORS.read_text())['structures']}
    problems, skipped, records, meta = [], [], {}, {}
    for ticket, p in readings():
        pid = pid_of(p)
        if pid in ('fettle_louis',):
            skipped.append(f'{pid}: no card (cards.py says why)')
            continue
        if p.get('infant_in_arms'):
            skipped.append(f'{pid}: an infant in arms, not drawn')
            continue
        role = p.get('dress_role')
        asset = DRESS.get(role)
        age = (p.get('age_1812') or {}).get('value')
        if asset == 'potawatomi_boy_1812' and str(p.get('sex') or '').startswith('f'):
            asset = 'potawatomi_girl_1812'
        # From twelve a child is drawn on the grown body, in the grown dress of their own
        # people (the 8-year body stretched past about 1.18 reads wrong; T-3465 notes).
        if isinstance(age, (int, float)) and age >= GROWN_FROM and asset in GROWN:
            asset = GROWN[asset]
        if asset in ('child_boy_1812', 'child_girl_1812') and isinstance(age, (int, float)) and age < TODDLER_UNDER:
            asset = 'child_toddler_1812'
        if not asset or not asset_built(asset):
            skipped.append(f'{pid}: no built dress for {role} ({asset})')
            continue
        variants = []
        for vi, (dates, note, spans, chance) in enumerate(variants_of(p)):
            out = [span_of(s, f'{pid} {dates} span {si}', problems, doors) for si, s in enumerate(spans)]
            out = [s for s in out if s]
            if not out:
                continue
            total = sum((s['to'] - s['from']) if s['from'] <= s['to'] else 24 - s['from'] + s['to'] for s in out)
            if abs(total - 24) > 1e-6:
                problems.append(f'{pid} {dates}: spans cover {total} h, not 24')
            v = {'spans': out}
            if dates:
                v = {'dates': dates, **({'chance': chance} if chance else {}), **({'note': str(note)[:200]} if note else {}), 'spans': out}
            variants.append(v)
        if not variants:
            skipped.append(f'{pid}: no day')
            continue
        if all(sp.get('away') for v in variants for sp in v['spans']):
            skipped.append(f'{pid}: off the scene at every hour the readings give (nowhere drawn)')
            continue
        presence = {k: p['presence'][k] for k in ('from', 'to') if (p.get('presence') or {}).get(k)}
        b = {'state': 'standing', 'day': variants}
        if presence:
            b['presence'] = presence
        records[pid] = {'behaviour': b}
        meta[pid] = (ticket, p, asset)
    join_talks(records)
    files = {}
    for pid, rec in records.items():
        ticket, p, asset = meta[pid]
        at = first_point(rec['behaviour']['day'], doors)
        if at is None:
            problems.append(f'{pid}: nowhere to stand')
            continue
        sources = sorted({f['source'] for f in p.get('facts', []) if f.get('source') and (ROOT / f"data/sources/{f['source']}.json").exists()})
        native = ticket == 'T-3467' or bool(p.get('review_required')) or bool((p.get('card') or {}).get('touches_native_history'))
        name = p.get('name') or pid
        basis = (f"Reconstructed figure of {name} in the 1812 town, at each hour of each run of dates where the reading for "
                 f"{ticket} (docs/RESEARCH/people-1812-{ticket[2:]}/day.json) puts them: indoors (asked for at the door) or "
                 f"out at their work, with the people they would be with. The hours, the places and the companions are ours "
                 f"(liberty {LIBERTY}), each span graded with its own basis in the reading; what a source says of them is on "
                 f"their card. They wear the {asset.replace('_', ' ')} role dress, with their own face, height, build and colouring.")
        iid = f'{PREFIX}{pid}' + ('' if pid.endswith('_1812') else '_1812')
        files[f'{iid}.json'] = {
            'id': iid, 'contract_version': 1, 'scene': '1812', 'person_id': pid,
            'appearance': {'asset_id': asset},
            'placement': {'local_e': at['local_e'], 'local_n': at['local_n'], 'heading_deg': at.get('heading_deg', 0), 'anchor': 'terrain'},
            'animation': {'clip': 'idle', 'loop': True, 'phase': round(seeded(pid, 'phase'), 3)},
            'behaviour': rec['behaviour'],
            'interaction': {'selectable': True, 'radius_m': 3, 'opens': 'resident_card'},
            'lod': {'policy': 'auto'}, 'display': 'shown', 'review_required': native,
            'provenance': {'grade': 'reconstructed', 'basis': basis, 'sources': sources or ['quaife_1913'], 'liberty': 'L418',
                           'seed': f'{pid}:1812:days:20261108',
                           'replaceable_by': 'A diary, letter or order book of the post that says where they were and what they did on the day.'},
        }
    return files, problems, skipped


def main(check=False):
    files, problems, skipped = build()
    index_path = INST / 'index.json'
    index = json.loads(index_path.read_text())
    others = [i for i in index['instances'] if not i.startswith(PREFIX)]
    index = {'scene': '1812', 'instances': sorted(set(others) | {f[:-5] for f in files})}   # as place.py sorts it
    stale = []
    want = {**files, 'index.json': index}
    for name, rec in want.items():
        text = json.dumps(rec, indent=2, ensure_ascii=False) + '\n'
        path = INST / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    for old in INST.glob(f'{PREFIX}*.json'):
        if old.name not in files:
            if check:
                stale.append(old.name)
            else:
                old.unlink()
    for s in skipped:
        print(f'  not drawn: {s}')
    for h in sorted(UNDRAWN_HOMES):
        print(f'  indoors in a building not drawn (away for the span): {h}')
    for p in problems:
        print(f'  PROBLEM: {p}', file=sys.stderr)
    if stale:
        raise SystemExit('stale 1812 town instances (rerun place_town.py): ' + ', '.join(stale[:12]))
    print(f'{len(files)} people of the 1812 town placed at their days ({len(skipped)} not drawn)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv))
