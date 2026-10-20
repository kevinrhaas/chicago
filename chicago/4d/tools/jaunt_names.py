#!/usr/bin/env python3
"""What a jaunt calls a building (T-2946), one way everywhere a jaunt names one.

The owner, 2026-10-20, on the famous-names walk: "I find the text fairly inconsistent on the
names labels, etc of the buildings". A stop was headed "1905 Prairie Avenue — Field Sr. Second
Empire", a road note named "John J. Glessner House", and the built-so-far walk said "1808
Prairie, the Keith house": three styles from three places (the record's production name, the
card title, this walk's own rule). So the names come from here, in one style:

    Marshall Field House, 1905 Prairie       a house whose family data/jaunts/_names/place-names.json names
    Marshall Field coach house, 1905 Prairie its coach house (or alley/rear building, conservatory)
    1726 Prairie                             a house with no family named
    Coach house, 1736 Prairie                its coach house

The number is the house's own (the id carries it; Glessner's is its aka), so a coach house is
named for the house it stands behind even where its record spans two lots. compile_jaunts.py
writes `places` into each compiled jaunt from `names()`; jaunt_built_so_far.py heads its stops
with `name()`.

    python3 tools/jaunt_names.py --list 1904   # print every name a scene's jaunts use
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / 'data/jaunts/_names/place-names.json'
PARTS = (('_coach_house', 'coach house'), ('_alley_building', 'alley building'),
         ('_rear_building', 'rear building'), ('_conservatory', 'conservatory'), ('_front', None))


def table(scene):
    return json.loads(TABLE.read_text()).get(str(scene), {})


def number(record):
    """The house number: from the id ('…_1905_prairie…'), else the record's own address."""
    found = re.findall(r'_(\d{4})_prairie', record['id'])
    if found:
        return found[-1]
    for text in list(record.get('aka') or []) + [record.get('name', '')]:
        m = re.match(r'\s*(\d{4})\s+(?:S\.\s+)?Prairie\b', text)
        if m:
            return m.group(1)
    return None


def split(record_id):
    """('marshall_field_house_1905_prairie', 'coach house') for its coach house."""
    for suffix, word in PARTS:
        if record_id.endswith(suffix):
            return record_id[: -len(suffix)], word
    return record_id, None


def name(record, names):
    """The jaunt's name for one structure record, or None where the scene has no rule."""
    base, part = split(record['id'])
    family = names.get(base) or names.get(record['id'])
    where = number(record)
    if part:
        lead = f'{family[: -len(" House")]} {part}' if family and family.endswith(' House') else part.capitalize()
    else:
        lead = family
    if lead and 'Prairie' in lead:
        return lead
    if not where:
        return lead
    return f'{lead}, {where} Prairie' if lead else f'{where} Prairie'


def names(scene, records):
    """Every structure of a scene that has a jaunt name, id → name; {} for a scene with no table."""
    rule = table(scene)
    if not rule:
        return {}
    ids = {r['id'] for r in records}
    bases = {split(i)[0] for i in ids}
    stray = sorted(k for k in rule if k not in ids and k not in bases)
    if stray:
        raise ValueError(f'place-names.json: {", ".join(stray)} not a {scene} structure')
    out = {}
    for record in records:
        called = name(record, rule)
        if called:
            out[record['id']] = called
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', metavar='SCENE', required=True)
    args = ap.parse_args()
    index = json.loads((ROOT / f'data/sidecars/{args.list}/index.json').read_text())
    records = [json.loads((ROOT / 'data' / e['sidecar']).read_text()) for e in index['structures']]
    for key, value in sorted(names(args.list, records).items()):
        print(f'{key:52} {value}')


if __name__ == '__main__':
    main()
