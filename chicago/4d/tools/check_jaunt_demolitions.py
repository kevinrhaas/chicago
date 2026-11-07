#!/usr/bin/env python3
"""Every 1904 jaunt stop at a house later torn down says so (2026-11-07).

The owner, 2026-11-07: "The jaunts particularly for 1904 when you have hit a building,
somewhere in the stop if was torn down mention that and if appropriate the context for
that, but don't distract heavily from the tour on that, but include that torn down fact
in there".

data/jaunts/_names/demolished.json holds, for each Prairie Avenue house whose loss date a
read source gives, the year and the claim. This gate reads every 1904 jaunt in data/jaunts
and fails a stop whose destination is one of those houses unless its text gives the year
and its evidence cites a claim resting on that house's source. The build-log walk is
written with the line by tools/jaunt_built_so_far.py, so it passes the same test.

    python3 tools/check_jaunt_demolitions.py
    python3 tools/check_jaunt_demolitions.py --self-test   # the gate must fire when broken
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAUNTS = ROOT / 'data/jaunts'
TABLE = JAUNTS / '_names/demolished.json'


def problems(docs, table):
    out = []
    for name, doc in docs:
        if doc.get('scene') != '1904':
            continue
        claims = {c['id']: c for c in doc.get('evidence', [])}
        for stop in doc.get('stops', []):
            row = table.get(stop.get('destination', {}).get('id'))
            if not row:
                continue
            where = f'{name} {stop["id"]} ({row["address"]})'
            if row['year'] not in stop['text']:
                out.append(f'{where}: the stop does not say the house was torn down in {row["year"]}')
            if not any(row['source'] in claims.get(e, {}).get('sources', []) for e in stop.get('evidence', [])):
                out.append(f'{where}: no claim on {row["source"]} backs the teardown')
    return out


def load():
    table = json.loads(TABLE.read_text())['houses']
    for key, row in table.items():
        if not (ROOT / f'data/sources/{row["source"]}.json').exists():
            sys.exit(f'JAUNT DEMOLITIONS FAIL — {key}: unknown source {row["source"]}')
    docs = []
    for path in sorted(JAUNTS.glob('*.json')):
        if path.name == 'schema.json':
            continue
        docs.append((path.name, json.loads(path.read_text())))
    return docs, table


def self_test(docs, table):
    hit = next(((n, d, s) for n, d in docs if d.get('scene') == '1904'
                for s in d['stops'] if s['destination'].get('id') in table), None)
    if hit is None:
        sys.exit('JAUNT DEMOLITIONS SELF-TEST FAIL — no 1904 stop reaches a torn-down house')
    name, doc, stop = hit
    year = table[stop['destination']['id']]['year']
    broken = copy.deepcopy(doc)
    s = next(x for x in broken['stops'] if x['id'] == stop['id'])
    s['text'] = s['text'].replace(year, 'one day')
    s['evidence'] = [e for e in s['evidence'] if table[stop['destination']['id']]['source']
                     not in {c['id']: c for c in broken['evidence']}.get(e, {}).get('sources', [])]
    found = problems([(name, broken)], table)
    if len(found) != 2:
        sys.exit(f'JAUNT DEMOLITIONS SELF-TEST FAIL — a stop stripped of its teardown gave {found}')
    print(f'JAUNT DEMOLITIONS SELF-TEST PASS — {name} {stop["id"]} without {year} and its claim fails twice')


def main():
    docs, table = load()
    if '--self-test' in sys.argv:
        return self_test(docs, table)
    found = problems(docs, table)
    if found:
        sys.exit('JAUNT DEMOLITIONS FAIL —\n  ' + '\n  '.join(found))
    count = sum(1 for _, d in docs if d.get('scene') == '1904' for s in d['stops'] if s['destination'].get('id') in table)
    print(f'JAUNT DEMOLITIONS PASS — {count} 1904 stops at torn-down houses each give the year, with a claim')


if __name__ == '__main__':
    main()
