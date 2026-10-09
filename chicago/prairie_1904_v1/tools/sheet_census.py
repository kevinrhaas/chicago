#!/usr/bin/env python3
"""Hold the Sanborn sheet censuses (data/sheet_census/sheet-*.json) to their contract (T-1840).

    python3 tools/sheet_census.py --check       # every census against the library, grid and images
    python3 tools/sheet_census.py --self-test   # break a copy each way and prove each refusal fires

A sheet census is the 1904 reading of one 1911 sheet. Its contract is the ticket's acceptance:
every frontage row the library holds for that sheet, and every named record standing on that
sheet's ground, is assigned EXACTLY ONCE (to a frontage, to vacant ground, or to the excluded
list), and every traced Prairie parcel on the sheet is owned by a row. A 1911 use lettered on a
rear building (GARAGE, AUTO …) carries a 1904 note, because the study's ruling 11 says a 1911
label proves nothing about 1904. The printed number a row reads must be the number the library's
frontage record and the traced parcel carry, so a misread cannot survive in one place only.
"""
from pathlib import Path
import copy, hashlib, json, re, sys

P = Path(__file__).resolve().parents[1]
GRID = P.parents[0] / '4d/data/street_grid/1904.json'
HOUSE = re.compile(r'^(\d{4})(?:\s*[–-]\s*(\d{4}))?\s+S\.\s+Prairie', re.I)
KINDS = {'front', 'attached', 'detached_service', 'non_building_use'}
DECISIONS = {'present_as_mapped', 'backcast_1886', 'alias', 'phase_unresolved'}
TIERS = {'attested', 'inferred', 'reconstructed', 'unresolved'}
LABELLED_1911 = re.compile(r'\b(GARAGE|AUTO|MFG)\b')
# The hundreds of Prairie Avenue each sheet covers.
SHEET_RANGE = {'20': (1600, 1799), '28': (1800, 1999)}


def load():
    lib = json.loads((P / 'data/library.json').read_text())
    grid = json.loads(GRID.read_text())
    images = json.loads((P / 'data/images.json').read_text())
    sheets = {p.stem.split('-', 1)[1]: json.loads(p.read_text())
              for p in sorted((P / 'data/sheet_census').glob('sheet-*.json'))}
    return lib, grid, images, sheets


def number_range(text):
    m = re.match(r'^(\d{4})(?:\s*[–-]\s*(\d{4}))?$', str(text).strip())
    return (int(m.group(1)), int(m.group(2) or m.group(1))) if m else None


def placements(sheets):
    """building id -> (parcel ids, ticket): where each census puts the records it assigns."""
    out = {}
    for c in sheets.values():
        rows = {f['frontage_id']: f for f in c['frontages']}
        for f in c['frontages']:
            for b in f['named_record_ids']: out[b] = (f.get('placed_on') or f['parcel_ids'], c['ticket'])
        for v in c.get('vacant_ground', []):
            for b in v['named_record_ids']: out[b] = (v.get('placed_on') or v['parcel_ids'], c['ticket'])
        for x in c.get('excluded_records', []):
            if x['ground'] in rows: out[x['building_id']] = (rows[x['ground']]['parcel_ids'], c['ticket'])
    return out


def check_sheet(sheet, c, lib, grid, images):
    errors = []
    say = errors.append
    buildings = {b['id']: b for b in lib['buildings']}
    sources = {s['id'] for s in lib['sources']}
    inventory = {r['id']: r for r in lib['map_inventory']['records'] if str(r.get('sheet')) == sheet}
    parcels = {p['id']: p for p in grid['parcels']}
    image_ids = {r['id'] for r in images['images']}
    lo, hi = SHEET_RANGE[sheet]

    for key in ('source', 'comparison'):
        s = c.get(key)
        if not s: continue
        if s['source_id'] not in sources: say(f'{key} source {s["source_id"]} is not in the library')
        f = P / s['file']
        if not f.is_file(): say(f'{key} file {s["file"]} is missing')
        elif hashlib.sha256(f.read_bytes()).hexdigest() != s['sha256']: say(f'{key} file {s["file"]} is not the sheet this census read (sha256)')

    # Every frontage row exactly once, and its printed number agrees with the library and the trace.
    seen = {}
    for f in c['frontages']:
        fid = f['frontage_id']
        seen[fid] = seen.get(fid, 0) + 1
        if fid not in inventory: say(f'{fid} is not a sheet {sheet} frontage record in the library'); continue
        rec = inventory[fid]
        if str(rec['address']) != f['printed_number_1911']:
            say(f'{fid}: the census reads {f["printed_number_1911"]} but the library frontage record says {rec["address"]}')
        if rec.get('side') != f['side']: say(f'{fid}: side {f["side"]} disagrees with the library ({rec.get("side")})')
        want = number_range(f['printed_number_1911'])
        for pid in f['parcel_ids']:
            if pid not in parcels: say(f'{fid}: parcel {pid} is not in the traced grid'); continue
            nums = [number_range(a) for a in parcels[pid]['addresses_1911']]
            if nums and want and not any(n and n[0] <= want[1] and want[0] <= n[1] for n in nums) \
                    and f['decision_1904'] != 'backcast_1886':
                say(f'{fid}: parcel {pid} reads {parcels[pid]["addresses_1911"]}, not {f["printed_number_1911"]}')
        if not set(f.get('placed_on', [])) <= set(f['parcel_ids']): say(f'{fid}: placed_on must be among its own parcels')
        if f['decision_1904'] not in DECISIONS: say(f'{fid}: unknown decision {f["decision_1904"]}')
        if f['decision_1904'] == 'alias':
            if f.get('alias_of') not in {g['frontage_id'] for g in c['frontages']} or f.get('alias_of') == fid:
                say(f'{fid}: an alias must name another row of this census')
        elif not f['polygons'] and f['decision_1904'] != 'backcast_1886':
            say(f'{fid}: a row that stands for a building enumerates no polygon')
        if not (f.get('why') or '').strip(): say(f'{fid}: no reason given for its 1904 decision')
        for k, v in f['tiers'].items():
            if v not in TIERS: say(f'{fid}: tier {k}={v} is not one of {sorted(TIERS)}')
        for img in f.get('image_ids', []):
            if img not in image_ids: say(f'{fid}: image {img} is not in data/images.json')
    for fid, n in seen.items():
        if n > 1: say(f'{fid} is assigned {n} times')
    for fid in sorted(set(inventory) - set(seen)): say(f'{fid} (sheet {sheet}) is in no census row')

    # Allocations (T-1841): service ground on this sheet given to a named record that another
    # census places. They hand out polygons, never a placement, so the record is not 'held' here.
    for a in c.get('allocations', []):
        if a['building_id'] not in buildings: say(f'allocation {a["id"]}: {a["building_id"]} is not a named record in the library')
        if not (a.get('why') or '').strip(): say(f'allocation {a["id"]}: no reason given')
        for p in a['polygons']:
            if p.get('tier') not in TIERS: say(f'{p["id"]}: tier {p.get("tier")} is not one of {sorted(TIERS)}')
        for img in a.get('image_ids', []):
            if img not in image_ids: say(f'allocation {a["id"]}: image {img} is not in data/images.json')
    # Polygons: unique ids, known kinds, and a 1911 label never stands for 1904 unremarked.
    pids = [p['id'] for f in c['frontages'] for p in f['polygons']] + [p['id'] for a in c.get('allocations', []) for p in a['polygons']]
    for d in sorted({i for i in pids if pids.count(i) > 1}): say(f'polygon id {d} is used twice')
    for f in c['frontages']:
        for p in f['polygons']:
            if p['kind'] not in KINDS: say(f'{p["id"]}: unknown kind {p["kind"]}')
            if LABELLED_1911.search(p['reading_1911']) and not p.get('note_1904'):
                say(f'{p["id"]}: a 1911 use is lettered on it and no 1904 note says what it was then (study ruling 11)')

    # Every named record on the sheet's ground exactly once.
    held = []
    for f in c['frontages']: held += f['named_record_ids']
    for v in c.get('vacant_ground', []):
        held += v['named_record_ids']
        for pid in v['parcel_ids'] + v.get('placed_on', []):
            if pid not in parcels: say(f'{v["id"]}: parcel {pid} is not in the traced grid')
        if not set(v.get('placed_on', [])) <= set(v['parcel_ids']): say(f'{v["id"]}: placed_on must be among its own parcels')
    rows = {f['frontage_id'] for f in c['frontages']}
    for x in c.get('excluded_records', []):
        held.append(x['building_id'])
        if x['ground'] not in rows: say(f'excluded {x["building_id"]}: ground {x["ground"]} is not a row of this census')
        b = buildings.get(x['building_id'])
        if b and not (b.get('excluded_1904') or re.match(r'(demolished|replaced|excluded|absent)', str(b.get('status_1904')))):
            say(f'excluded {x["building_id"]}: the library does not record it as gone by 1904 ({b.get("status_1904")})')
    for b in held:
        if b not in buildings: say(f'{b} is not a named record in the library')
    for b in sorted({b for b in held if held.count(b) > 1}): say(f'{b} is assigned {held.count(b)} times')
    for b in lib['buildings']:
        m = HOUSE.match(b.get('address') or '')
        if m and lo <= int(m.group(1)) <= hi and b['id'] not in held:
            say(f'{b["id"]} ({b["address"]}) stands on sheet {sheet} ground and is in no census row')

    # Every traced Prairie parcel on the sheet is owned by a row.
    owned = {pid for f in c['frontages'] for pid in f['parcel_ids']} | \
            {pid for v in c.get('vacant_ground', []) for pid in v['parcel_ids']}
    for pid, p in parcels.items():
        if not pid.startswith('prairie_'): continue
        n = re.match(r'prairie_(\d{4})', pid)
        if n and lo <= int(n.group(1)) <= hi and pid not in owned:
            say(f'traced parcel {pid} on sheet {sheet} is owned by no census row')
    return errors


def check(lib, grid, images, sheets):
    errors = []
    for sheet, c in sheets.items():
        if sheet not in SHEET_RANGE: errors.append(f'sheet-{sheet}.json: no Prairie range is known for sheet {sheet}'); continue
        errors += [f'sheet {sheet}: {e}' for e in check_sheet(sheet, c, lib, grid, images)]
    return errors


def self_test(lib, grid, images, sheets):
    base = sheets['20']
    def broken(fn):
        c = copy.deepcopy(base); l = copy.deepcopy(lib); fn(c, l); return check_sheet('20', c, l, grid, images)
    cases = {
        'a frontage row dropped': (lambda c, l: c['frontages'].pop(0), 'is in no census row'),
        'a frontage row twice': (lambda c, l: c['frontages'].append(copy.deepcopy(c['frontages'][0])), 'assigned 2 times'),
        'a named record twice': (lambda c, l: c['frontages'][0]['named_record_ids'].append('pa-1612-1'), 'assigned 2 times'),
        'a named record dropped': (lambda c, l: c['vacant_ground'][0]['named_record_ids'].clear(), 'pa-1635-48'),
        'a misread number kept in the library': (lambda c, l: next(r for r in l['map_inventory']['records'] if r['id'] == 'frontage-20-023').update(address='1603'), 'library frontage record says 1603'),
        'a number the trace does not carry': (lambda c, l: c['frontages'][0]['parcel_ids'].__setitem__(0, 'prairie_1604'), 'reads'),
        'a 1911 garage with no 1904 note': (lambda c, l: next(p for f in c['frontages'] for p in f['polygons'] if 'GARAGE' in p['reading_1911']).pop('note_1904'), 'ruling 11'),
        'an unknown tier': (lambda c, l: c['frontages'][0]['tiers'].update(presence_1904='documented'), 'tier presence_1904'),
        'a parcel no row owns': (lambda c, l: c['vacant_ground'][0]['parcel_ids'].remove('prairie_1625_1637_a'), 'owned by no census row'),
        'an alias pointing at itself': (lambda c, l: next(f for f in c['frontages'] if f['decision_1904'] == 'alias').update(alias_of='frontage-20-014'), 'alias must name'),
    }
    failed = []
    for name, (fn, expect) in cases.items():
        errs = broken(fn)
        hit = any(expect in e for e in errs)
        print(f'{"refused" if hit else "NOT REFUSED"}: {name}' + ('' if hit else f' — got {errs[:2]}'))
        if not hit: failed.append(name)
    # Sheet 28 carries the one allocation (T-1841).
    if '28' in sheets:
        c = copy.deepcopy(sheets['28']); c['allocations'][0]['building_id'] = 'pa-no-such-record'
        hit = any('is not a named record' in e for e in check_sheet('28', c, lib, grid, images))
        print(f'{"refused" if hit else "NOT REFUSED"}: an allocation to an unknown record')
        if not hit: failed.append('an allocation to an unknown record')
        c = copy.deepcopy(sheets['28']); c['allocations'][0]['polygons'][0]['id'] = c['frontages'][0]['polygons'][0]['id']
        hit = any('used twice' in e for e in check_sheet('28', c, lib, grid, images))
        print(f'{"refused" if hit else "NOT REFUSED"}: an allocated polygon reusing a frontage polygon id')
        if not hit: failed.append('an allocated polygon reusing a frontage polygon id')
    if failed: sys.exit(f'{len(failed)} refusal(s) did not fire: {", ".join(failed)}')
    print(f'sheet census self-test: all {len(cases)} refusals fire')


if __name__ == '__main__':
    if {'-h', '--help'} & set(sys.argv): print(__doc__); sys.exit()
    lib, grid, images, sheets = load()
    if '--self-test' in sys.argv: self_test(lib, grid, images, sheets); sys.exit()
    errors = check(lib, grid, images, sheets)
    if errors: sys.exit('\n'.join(errors) + f'\n{len(errors)} sheet census problem(s)')
    for s, c in sheets.items():
        print(f'sheet {s}: {len(c["frontages"])} frontage rows, '
              f'{sum(len(f["polygons"]) for f in c["frontages"])} polygons, '
              f'{sum(len(f["named_record_ids"]) for f in c["frontages"]) + sum(len(v["named_record_ids"]) for v in c.get("vacant_ground", [])) + len(c.get("excluded_records", []))} named records, each once')
