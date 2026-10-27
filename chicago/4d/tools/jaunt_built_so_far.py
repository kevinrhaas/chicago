#!/usr/bin/env python3
"""The 1904 "built so far" walk, written from the building records (T-2747).

The owner, 2026-10-17: "do a jaunt that includes the buildings that you have built out so
far with detail, and when detail is done, you can start adding to it. keep the tour in order
of most detailed to least detailed, but since you are building out multiple areas dont make
the tour jump all over the place, keep it clustered and keep it updated as you continue to
build out buildings".

So this walk is never written by hand. This tool reads the compiled 1904 scene and writes
`data/jaunts/prairie-built-so-far.json`; `--check` (run by check.sh) fails the moment a
building's record or its image-gate verdicts move and the walk was not rewritten, which is
what keeps it current: a refine PR that adds detail turns the gate red until it reruns this.

WHICH BUILDINGS. Every 1904 structure worked past the district draft: a kit or bespoke
record (any archetype but `prairie_draft`), or a draft refined in place from a picture (a
`prairie_draft` record that carries no `draft` attribute, because the draft rules skip it).

HOW DETAILED, on a five-step ladder read off the record alone:
  5  its own model, not a kit (the bespoke archetypes: Glessner)
  4  a kit build with at least one solved picture whose match verdict is `matches`
  3  a kit build with a solved picture, none matching yet
  2  a kit build with no solved picture
  1  a district draft reshaped from a picture
Ties break on matching pictures, then solved pictures, then recorded attributes.

HOW IT STAYS CLUSTERED. Buildings whose footprint centres lie within AREA_LINK_M of each
other (chained) form one area, so the two sides of a block are one area and the 1600 block
and the Eighteenth Street corner are two. Areas run in order of their most detailed
building; inside an area the walk takes the detail levels from the top down, and walks each
level nearest-first from where the last stop left off. So the route crosses between areas
once per area and never doubles back across the district for one building.

HOW LONG IT GROWS. A jaunt holds at most the schema's `stops.maxItems` (50, in
data/jaunts/schema.json). Once more buildings than that are worked, the walk takes the most
detailed of them by the same ranking that orders it, routes only those, and says in its
opening how many less detailed buildings wait outside it; each joins as it gains detail
over the walk's least detailed stop. Measured 2026-10-27: dev's walk reached exactly 50 with
1901 Prairie (#1361), and the next building worked (1712 Prairie, T-3187) made 51, which the
jaunt compiler refused, so every building PR on the avenue stopped there.

    python3 tools/jaunt_built_so_far.py           # rewrite the walk
    python3 tools/jaunt_built_so_far.py --check   # fail if the committed walk is stale
    python3 tools/jaunt_built_so_far.py --list    # print the order and each level
"""
import argparse
import json
import math
import re
import sys
import zlib
from pathlib import Path

import jaunt_names

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'jaunts/prairie-built-so-far.json'
SCENE = '1904'
AREA_LINK_M = 60.0
LIBERTY = 'L-jaunt-prairie-built-so-far'
MAX_STOPS = json.loads((DATA / 'jaunts/schema.json').read_text())['properties']['stops']['maxItems']
BESPOKE = {'masonry_house'}
LEVELS = {
    5: 'its own model, built piece by piece rather than from a kit',
    4: 'a kit build matched to its picture',
    3: 'a kit build checked against its picture, not matching yet',
    2: 'a kit build, no picture solved against it yet',
    1: 'a first rough model, reshaped from a picture',
}
NAMES = jaunt_names.table(SCENE)


def read(path):
    return json.loads(Path(path).read_text())


def worked(record):
    if record['archetype'] != 'prairie_draft':
        return True
    return 'draft' not in record.get('attributes', {})


def level(row):
    if row['archetype'] in BESPOKE:
        return 5
    if row['archetype'] == 'prairie_draft':
        return 1
    if row['matches']:
        return 4
    return 3 if row['views'] else 2


def label(record):
    """'Osborn Keith House, 1808 Prairie': the one name every jaunt gives it (T-2946)."""
    return jaunt_names.name(record, NAMES) or record['name']


def centre(record):
    p, poly = record['placement'], record['footprint']['polygon']
    u = sum(x for x, _ in poly) / len(poly)
    v = sum(y for _, y in poly) / len(poly)
    r = math.radians(p.get('rotation_deg', 0) or 0)
    return (p['local_e'] + u * math.cos(r) - v * math.sin(r), p['local_n'] + u * math.sin(r) + v * math.cos(r))


def rows():
    index = read(DATA / f'sidecars/{SCENE}/index.json')
    out = []
    for entry in index['structures']:
        record = read(DATA / entry['sidecar'])
        if not worked(record):
            continue
        verdicts = [read(p).get('verdict') for p in sorted((DATA / 'reference_views' / record['id']).glob('*.match.json'))]
        e, n = centre(record)
        row = dict(id=record['id'], record=record, archetype=record['archetype'], views=len(verdicts),
                   matches=verdicts.count('matches'), attrs=len(record.get('attributes', {})), e=e, n=n,
                   label=label(record), number=int(jaunt_names.number(record) or 0))
        row['level'] = level(row)
        out.append(row)
    return out


def rank(row):
    return (-row['level'], -row['matches'], -row['views'], -row['attrs'], row['id'])


def areas(items):
    parent = {r['id']: r['id'] for r in items}

    def root(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key
    for a in items:
        for b in items:
            if a['id'] < b['id'] and math.dist((a['e'], a['n']), (b['e'], b['n'])) <= AREA_LINK_M:
                parent[root(a['id'])] = root(b['id'])
    groups = {}
    for r in items:
        groups.setdefault(root(r['id']), []).append(r)
    return sorted(groups.values(), key=lambda g: (min(rank(r) for r in g), -len(g)))


def route(items):
    """Areas by their best building; inside each, levels top down, each walked nearest-first."""
    order, here = [], None
    for number, group in enumerate(areas(items)):
        span = sorted({r['number'] for r in group if r['number']})
        name = f'{span[0]}-{span[-1]} Prairie' if len(span) > 1 else (f'{span[0]} Prairie' if span else 'Prairie Avenue')
        for lvl in sorted({r['level'] for r in group}, reverse=True):
            for nxt in snake([r for r in group if r['level'] == lvl], here):
                nxt['area'], nxt['area_name'] = number, name
                order.append(nxt)
                here = (nxt['e'], nxt['n'])
    return order


def snake(pool, here):
    """One level of one area as a walker takes it: along the side of the street nearest to
    where the last stop left off, from its nearer end to its farther, then back along the
    other side. Even numbers are the west side, odd the east. With no stop behind it (the
    very first), the walk starts at the most detailed building."""
    if not pool:
        return []
    start = min(pool, key=rank) if here is None else min(pool, key=lambda r: (math.dist(here, (r['e'], r['n'])), rank(r)))
    if here is None:
        here = (start['e'], start['n'])
    near = sorted((r for r in pool if r['number'] % 2 == start['number'] % 2), key=lambda r: (r['number'], rank(r)))
    far = sorted((r for r in pool if r['number'] % 2 != start['number'] % 2), key=lambda r: (r['number'], rank(r)))
    if math.dist(here, (near[-1]['e'], near[-1]['n'])) < math.dist(here, (near[0]['e'], near[0]['n'])):
        near.reverse()
    else:
        far.reverse()
    return near + far


def plural(n, word):
    return f'{n} {word}' + ('' if n == 1 else 's')


def stop_text(row, after):
    views = row['views']
    pics = f'; {plural(views, "solved picture")}, {row["matches"]} matching' if views else ''
    head = f'{row["label"]}. DETAIL {row["level"]}/5: {LEVELS[row["level"]]}{pics}. {row["record"]["grade"]["why"]}'
    if after is None:
        tail = 'Last stop of the walk so far; it grows as more buildings are built out.'
    elif after['area'] == row['area']:
        tail = f'Next: {after["label"]}.'
    else:
        tail = f'Next: walk on to the {after["area_name"]} area, starting at {after["label"]}.'
    text = f'{head} {tail}'
    if len(text.split()) < 25:
        text += ' Detail is this project\'s own measure of how far each model is built.'
    return text


def claim(n, row):
    record = row['record']
    period = record['documented_range']
    sources = [s for s in period.get('sources', []) if (DATA / f'sources/{s}.json').exists()]
    base = dict(id=f'stood-{n}', text=f'{row["label"]} stood on 1 July 1904, as its structure record carries it.', sources=sources)
    if period.get('confidence') == 'attested' and sources:
        return dict(base, confidence='attested', locator=read(DATA / f'sources/{sources[0]}.json').get('locator') or 'The whole source.')
    reasoning = (period.get('note') or '').strip() or 'The structure record dates the building across the scene date.'
    return dict(base, confidence='inferred', reasoning=reasoning)


def build():
    worked_rows = rows()
    order = route(sorted(worked_rows, key=rank)[:MAX_STOPS])
    count, area_count = len(order), len({r['area'] for r in order})
    waiting = len(worked_rows) - count
    stops, evidence = [], [dict(id='tour', confidence='reconstructed', sources=[], liberty=LIBERTY,
        text='Which buildings the walk includes, their detail levels, its grouping and order, reading times and keepsake are this project\'s own description of its models, rewritten from the records by tools/jaunt_built_so_far.py; no historical visit is asserted.')]
    for n, row in enumerate(order, 1):
        text = stop_text(row, order[n] if n < count else None)
        stops.append(dict(id=f'stop-{n}', destination=dict(kind='structure', id=row['id']), text=text,
                          read_s=max(10, round(len(text.split()) * 0.42)), evidence=[f'stood-{n}', 'tour'],
                          links=[dict(kind='structure', id=row['id'], label='About this building')],
                          next=f'stop-{n + 1}' if n < count else 'finish'))
        evidence.append(claim(n, row))
    scope = (f'Every Prairie Avenue building modelled past its first rough model: {plural(count, "building")} in '
             f'{plural(area_count, "area")}.') if not waiting else (
        f'The {count} most detailed of the {len(worked_rows)} Prairie Avenue buildings modelled past their first rough model, '
        f'in {plural(area_count, "area")}. A walk holds {MAX_STOPS} stops, so ' + (
            'one less detailed building waits outside it until it gains detail.' if waiting == 1 else
            f'{waiting} less detailed buildings wait outside it until they gain detail.'))
    opening = (f'WALK: BUILT SO FAR. {scope} Most detailed first, one area at a time, so the route does not double back. '
               'It is rewritten from the building records whenever one gains detail.')
    ending = 'End of the walk so far. As more buildings are built out they join it, in their place by detail and area.'
    doc = dict(schema_version=1, content_version=1, category='Build log', featured=True, review_required=False,
               id='prairie-built-so-far', scene=SCENE, title='Every building modelled so far',  # T-2944: the distinctive words first
               premise='Walk every building on Prairie Avenue modelled in detail so far, most detailed first, kept area by area. It grows as buildings are built out.',
               default_mode='walk', allowed_modes=['walk', 'fly', 'instantly'],
               opening=dict(text=opening, read_s=max(10, round(len(opening.split()) * 0.42))), stops=stops,
               endings=[dict(id='finish', text=ending, read_s=10, completion_eligible=True)],
               keepsake=dict(family='Wayfinding', id='prairie-build-log', title='Prairie Avenue build log',
                             text='A note of the buildings modelled in detail when you walked it; a project record, not a historical artifact.'),
               evidence=evidence, liberties=[LIBERTY])
    # A saved walk resumes only on the same content_version, so the version follows the route.
    doc['content_version'] = zlib.crc32(json.dumps(stops, sort_keys=True).encode()) % 900_000_000 + 1
    return doc, order


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()
    doc, order = build()
    body = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
    if args.list:
        for n, r in enumerate(order, 1):
            print(f'{n:2} area {r["area"]} L{r["level"]} {r["matches"]}/{r["views"]} {r["label"]}')
    if args.check:
        if not OUT.exists() or OUT.read_text() != body:
            sys.exit('BUILT-SO-FAR WALK STALE — a 1904 building gained or lost detail; run python3 tools/jaunt_built_so_far.py, '
                     'then python3 tools/compile_jaunts.py')
        print(f'BUILT-SO-FAR WALK PASS — {len(order)} buildings, current with the records')
        return
    OUT.write_text(body)
    print(f'BUILT-SO-FAR WALK — wrote {OUT.relative_to(ROOT)}: {len(order)} buildings')


if __name__ == '__main__':
    main()
