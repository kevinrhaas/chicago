#!/usr/bin/env python3
"""Build T-1766's four reconstructed Canal Street trade roofs.

The recipe fixes a bounded street-front arrangement, not four recovered addresses.
It was built as five; the W3 wagon shop was withdrawn when T-1783's carpenter's shop
took one of the West workshop slots first, leaving the live budget at W1 and W2.
Family dimensions, form and siding use the same production helpers as the existing
block parcels. No standing roof is moved, refamilied or copied. New meshes must be
baked by the ordinary structure pipeline.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import math
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'generators')]
from family_bands import families, dimensions_m
from generate_block_infill import form_for, finish_for, invented, no_build_rings, FUNCTIONS
from generate_west_infill import footprint_origin, omitted_street_corridors
from generate_plat_lots import street_lines
from plat_corridors import corridors, intrusion
from plat_occupancy import world_polygon, footprints, overlap_area
from heightfield import Heightfield
from inferred_occupancy import occupancy
from canal_approach_occupancy import occupancy as trade_occupancy
from normalise_structure_function import canonical
from siding_stock import deal_records

CORRIDOR_LINE = 'drawn'
CORRIDOR_LINE_WHY = 'Place new roofs beside the existing Canal frontage and block grid, without recutting either.'
RECIPE = DATA / 'reconstruction/1835_canal_approach_trade.json'
PREFIX = 'recon_1835_canal_trade_'
SOURCE = 'owner_chicago_1835_reconstruction_spec_2026'
EXPECTED = Counter({'C3': 1, 'C4': 1, 'W1': 1, 'W2': 1})


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def seat(row, width, depth, street):
    """Front midpoint outside the drawn corridor edge; rear points away from Canal."""
    north = float(row['front_station_n_m'])
    if row['side'] != 'east' or not -95 <= north <= -15 or float(row['setback_m']) != 1.0:
        raise ValueError('this recipe owns the east Canal frontage between Lake and Randolph, at 1 m setback')
    points = street['points']
    segments = [(a, b) for a, b in zip(points, points[1:]) if a[1] <= north <= b[1]]
    if len(segments) != 1:
        raise ValueError('station must lie strictly within one Canal segment')
    a, b = segments[0]
    de, dn = b[0] - a[0], b[1] - a[1]
    length = math.hypot(de, dn)
    side = {'west': 1, 'east': -1}[row['side']]
    outward = (-dn / length * side, de / length * side)
    east = a[0] + de * (north - a[1]) / dn
    offset = street['half_width_m'] + float(row['setback_m']) + depth / 2
    centre = (east + outward[0] * offset, north + outward[1] * offset)
    # Both archetypes put their facade on max-v (+Y), so face back toward Canal.
    bearing = (math.degrees(math.atan2(*outward)) + 180) % 360
    return (*footprint_origin(*centre, width, depth, bearing), bearing)


def make_record(row, seq, table, datum, street, people):
    family = row['family']
    seed = row['geometry_seed']
    sid = row['structure_id']
    expected_seed = PREFIX + family.lower()
    expected_id = expected_seed + '_' + {'C3': '001', 'C4': '002', 'W1': '003', 'W2': '004'}[family]
    if seed != expected_seed or sid != expected_id:
        raise ValueError('Canal public identity or preserved geometry seed changed')
    spec = table[family]
    width, depth = dimensions_m(family, spec['band_ft'], seed)
    east, north, bearing = seat(row, width, depth, street)
    finish, paint = finish_for(seed)
    return {
        'id': sid, 'name': f"Reconstructed Canal Street {spec['label'].lower()}",
        'archetype': spec['archetype'],
        'phases': [{
            'id': 'inferred_1835',
            'documented_range': {'from': '1835-01-01', 'to': '1835-12-31',
                'confidence': 'reconstructed',
                'note': 'An invented count-unit for July 1835, not evidence that this particular building existed.'},
            'position': {
                'utm_e': round(datum['origin_utm_e'] + east, 3),
                'utm_n': round(datum['origin_utm_n'] + north, 3),
                'rotation_deg': round(bearing, 6),
                'symbolic_location': 'Reconstructed east frontage of Canal Street between Lake and Randolph',
                'confidence': 'reconstructed',
                'note': 'The street exists in the cadastral evidence; this roof does not. Its front is set one metre outside the drawn east corridor edge. The layout follows the West memo and current trade placement policy, with open gaps and rear work ground; the station is invented and claims no recovered lot or address.',
                'derivation': {'method': 'not_derivable', 'reason': 'The cadastral sheets map streets and lots, not these anonymous buildings.'}},
            'footprint': {'polygon': [[0, 0], [width, 0], [width, depth], [0, depth]],
                'confidence': 'reconstructed',
                'note': f'Deterministically sampled {width:.3f} by {depth:.3f} metre rectangle inside the {family} typology band; neither dimension is attested for this invented roof.'},
            'form': form_for(family, spec, seed, width, depth, paint),
            'change_note': 'T-1766 adds this reconstructed trade roof without moving an existing building.'}],
        'function': invented(FUNCTIONS.get(family) or canonical(spec['label']),
            f'The {family} type fills the remaining West trade programme. No historical proprietor or exact activity is recovered from its footprint.'),
        'reconstruction': {'status': 'inferred_anonymous', 'family': family,
            'district': 'west', 'inventory_class': 'principal_functional',
            'programme_phase': 'canal_approach_trade_1835', 'source_id': SOURCE,
            'sequence': seq, 'finish_key': finish,
            'roof_condition': ('fresh', 'darkened', 'patched', 'weathered')[seq % 4],
            'age_state': ('new', 'recent', 'established', 'older_frontier')[seq % 4]},
        **({'occupants': people[sid]} if sid in people else {}),
        'research_note': 'RECONSTRUCTED, NOT A RECOVERED ADDRESS. The West memo bounds mixed trade on the Canal approach; the live programme leaves room for two stores and two workshops. C3 and C4 use remaining store-family capacity because C1 and C2 are already full. Exact existence, location, dimensions, finish and form remain inventions. Any reconstructed occupants are separately graded by their own records.',
        'review_required': False,
    }


def point_segment_distance(e, n, a, b):
    """Distance used by footprint separation and facade setback, independent of swales.

    T-1460 retired the swale reader and its helper in generate_west_infill;
    this small geometric primitive still serves the Canal frontage validation.
    """
    de, dn = b[0] - a[0], b[1] - a[1]
    span = de * de + dn * dn
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((e - a[0]) * de + (n - a[1]) * dn) / span))
    return math.hypot(e - (a[0] + t * de), n - (a[1] + t * dn))


def separation(a, b):
    if overlap_area(b, a) > .001:
        return 0.0
    return min(point_segment_distance(*p, q, r)
               for x, y in ((a, b), (b, a)) for p in x
               for q, r in zip(y, y[1:] + y[:1]))


def validate(records, recipe, datum):
    if Counter(r['reconstruction']['family'] for r in records) != EXPECTED:
        raise ValueError('the parcel must contain exactly C3, C4, W1 and W2')
    if len({r['id'] for r in records}) != 4:
        raise ValueError('four distinct structure ids required')
    lanes = {**corridors(), **omitted_street_corridors()}
    refused = no_build_rings()
    field = Heightfield.load(DATA / 'terrain/epochs/e1834_harbor_cut')
    if field is None:
        raise ValueError('committed terrain is required')
    water = []
    epoch = DATA / 'terrain/epochs/e1834_harbor_cut'
    for filename in ('river.geojson', 'branches.geojson', 'shoreline.geojson'):
        for feature in load(epoch / filename)['features']:
            if feature['properties'].get('kind') == 'water' and feature['geometry']['type'] == 'Polygon':
                water.append([(e-datum['origin_utm_e'], n-datum['origin_utm_n'])
                              for e, n in feature['geometry']['coordinates'][0]])
    swales = [s for s in load(epoch / 'terrain_spec.json').get('swales', [])
              if s['id'].startswith('west_prairie_')]
    others = footprints(datum, {r['id'] for r in records})
    own = [(r['id'], world_polygon(r['phases'][0], datum)) for r in records]
    report = []
    for i, (record, (sid, poly)) in enumerate(zip(records, own)):
        phase = record['phases'][0]
        importlib.import_module('archetypes.' + record['archetype'] + '_params').from_phase(phase)
        street, depth = intrusion(poly, lanes)
        if street:
            raise ValueError(f'{sid} intrudes into {street}: {depth:.3f} m')
        for name, ring in refused.items():
            if overlap_area(ring, poly) > .001:
                raise ValueError(f'{sid} intersects refused ground {name}')
        bank_gap = min(separation(poly, ring) for ring in water)
        if bank_gap < 8:
            raise ValueError(f'{sid} is only {bank_gap:.2f} m from traced water')
        for swale in swales:
            line = [tuple(p) for p in swale['line']]
            gap = min(point_segment_distance(*p, a, b) for p in poly
                      for a, b in zip(line, line[1:]))
            if gap <= float(swale['half_width_m']):
                raise ValueError(f'{sid} intersects {swale["id"]}')
        heights = [field.height(*point) for point in poly]
        if not all(field.covers(*point) for point in poly) or min(heights) < 0:
            raise ValueError(f'{sid} lacks dry modelled ground at every corner')
        if max(heights) - min(heights) > .35:
            raise ValueError(f'{sid} spans more than 0.35 m of relief')
        nearest = min((separation(poly, other), name) for name, other in others + own[:i])
        if nearest[0] < 3:
            raise ValueError(f'{sid} has only {nearest[0]:.3f} m clearance from {nearest[1]}')
        # The front's nearest edge must remain on Canal, independently of its recipe station.
        canal_gap = min(point_segment_distance(*p, q, r) for p in poly
                        for q, r in zip(lanes['canal']['ring'], lanes['canal']['ring'][1:] + lanes['canal']['ring'][:1]))
        # GLB-CONTRACT: the actual facade is max-v, polygon vertices 2 and 3.
        # Testing the whole ring alone cannot detect a house turned back to front.
        front_gap = min(point_segment_distance(*p, q, r) for p in poly[2:4]
                        for q, r in zip(lanes['canal']['ring'], lanes['canal']['ring'][1:] + lanes['canal']['ring'][:1]))
        back_gap = min(point_segment_distance(*p, q, r) for p in poly[:2]
                       for q, r in zip(lanes['canal']['ring'], lanes['canal']['ring'][1:] + lanes['canal']['ring'][:1]))
        if not .99 <= front_gap <= 1.01 or back_gap <= front_gap + 3:
            raise ValueError(f'{sid} facade faces away from Canal: front {front_gap:.3f}, back {back_gap:.3f} m')
        if not .99 <= canal_gap <= 1.01:
            raise ValueError(f'{sid} lost its 1 m Canal frontage setback ({canal_gap:.3f})')
        report.append(f'{sid}: nearest {nearest[0]:.2f} m ({nearest[1]}), ground {min(heights):.2f} m, relief {max(heights)-min(heights):.2f} m, Canal setback {canal_gap:.3f} m, traced bank {bank_gap:.2f} m')
    return report


def records_from_inputs():
    recipe, datum = load(RECIPE), load(DATA / 'datum.json')
    street = street_lines(load(DATA / 'streets/1835.json'))['canal']
    table, people = families(), occupancy()
    people.update(trade_occupancy())
    records = [make_record(row, i, table, datum, street, people)
               for i, row in enumerate(recipe['placements'], 1)]
    # Public ids carry pool/family/ordinal for the town's adoption contract.
    # The pre-bake rename preserves the original geometry seeds, including siding.
    public_ids = [record['id'] for record in records]
    try:
        for record in records:
            record['id'] = record['id'].rsplit('_', 1)[0]
        deal_records(records)
    finally:
        for record, public_id in zip(records, public_ids):
            record['id'] = public_id
    return records, validate(records, recipe, datum)


def self_test():
    records, _ = records_from_inputs()
    recipe, datum = load(RECIPE), load(DATA / 'datum.json')
    cases = []
    wrong_count = copy.deepcopy(records[:-1])
    cases.append(('missing roof', wrong_count))
    duplicate = copy.deepcopy(records)
    duplicate[1]['id'] = duplicate[0]['id']
    cases.append(('duplicate identity', duplicate))
    roadway = copy.deepcopy(records)
    roadway[0]['phases'][0]['position']['utm_e'] -= 10
    cases.append(('roof moved into Canal', roadway))
    collision = copy.deepcopy(records)
    collision[1]['phases'][0]['position'] = copy.deepcopy(collision[0]['phases'][0]['position'])
    cases.append(('colliding roofs', collision))
    backwards = copy.deepcopy(records)
    phase = backwards[0]['phases'][0]
    poly = world_polygon(phase, datum)
    centre = [sum(p[i] for p in poly) / 4 for i in (0, 1)]
    width, depth = phase['footprint']['polygon'][2]
    bearing = (phase['position']['rotation_deg'] + 180) % 360
    east, north = footprint_origin(*centre, width, depth, bearing)
    phase['position'].update(utm_e=datum['origin_utm_e']+east,
                             utm_n=datum['origin_utm_n']+north,
                             rotation_deg=bearing)
    cases.append(('facade facing the rear yard', backwards))
    off_ground = copy.deepcopy(records)
    off_ground[0]['phases'][0]['position']['utm_e'] -= 2000
    cases.append(('roof off modelled ground', off_ground))
    for label, mutated in cases:
        try:
            validate(mutated, recipe, datum)
        except (ValueError, SystemExit):
            print('PASS self-test: refuses ' + label)
        else:
            raise ValueError('self-test failed to refuse ' + label)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    records, report = records_from_inputs()
    drift = []
    expected = set()
    for record in records:
        path = DATA / 'structures' / (record['id'] + '.json')
        expected.add(path)
        content = json.dumps(record, indent=2, ensure_ascii=False) + '\n'
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding='utf-8')
    drift.extend(str(p.relative_to(ROOT)) for p in (DATA/'structures').glob(PREFIX+'*.json') if p not in expected)
    print('\n'.join(report))
    if drift:
        print('FAIL: Canal trade outputs drift: ' + ', '.join(drift))
        return 1
    print('PASS: four Canal trade roofs' + (' rederive exactly' if args.check else ' generated'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
