#!/usr/bin/env python3
"""Merge the image & document streams into data/images.json and draw data/site-plan.json.

    python3 tools/build_images.py            # build both
    python3 tools/build_images.py --check    # build in memory, fail if the files differ

images.json   every record from research/images/stream-*.json, de-duplicated (same id,
              or same catalog page + image), checked against the record schema in
              research/images/README.md, and indexed by building.
site-plan.json  the 1904 street grid's blocks, carriageways, alleys and the 92 Prairie
              Avenue parcels (traced from the Sanborn 1911 sheets by the 4D project's
              tools/trace_prairie_1904_grid.py), with each parcel's library building ids
              matched by printed house number. It is a locator for the viewer, not a
              claim about any building's 1904 footprint.
"""
from pathlib import Path
import json, re, sys
from evidence_review import validate_reviews
from sheet_census import placements as census_placements

P = Path(__file__).resolve().parents[1]
GRID = P.parents[0] / '4d/data/street_grid/1904.json'
KINDS = {'photograph', 'stereograph', 'postcard', 'engraving', 'lithograph', 'publication plate',
         'architectural drawing', 'measured drawing', 'fire insurance map', 'atlas plate',
         "bird's-eye view", 'aerial', 'document', 'permit record', 'newspaper item'}
PERIODS = {'in-period', 'near-period', 'later'}
COPYABLE = {'public domain', 'no known restrictions'}
PENDING = 'pending — permission requested'
RIGHTS = COPYABLE | {PENDING, 'copyright — link only', 'unknown — link only'}


def load_library():
    return json.loads((P / 'data/library.json').read_text())


def norm_rights(r):
    r = (r or '').strip().lower().replace(' - ', ' — ').replace('--', '—')
    if r.startswith('public domain'): return 'public domain'
    if r.startswith('no known'): return 'no known restrictions'
    # Owner, 2026-10-02: published while the holder's permission is pending (research/images/README.md rule 2).
    if r.startswith('pending'): return 'pending — permission requested'
    if r.startswith('copyright') or r.startswith('in copyright') or r.startswith('rights reserved'): return 'copyright — link only'
    return 'unknown — link only'


def period_of(rec):
    hi, lo = rec.get('date_latest'), rec.get('date_earliest')
    y = hi if isinstance(hi, int) else lo if isinstance(lo, int) else None
    if y is None: return rec.get('period') if rec.get('period') in PERIODS else 'later'
    return 'in-period' if y <= 1911 else 'near-period' if y <= 1930 else 'later'


def store_index():
    # The image store (kevinrhaas/chicago-images) as of its last sync — tools/sync_image_store.py.
    f = P / 'research/images/STORE.json'
    return json.loads(f.read_text()) if f.exists() else {'files': {}, 'prefix': 'research/images/files/'}


def merge(lib):
    store = store_index()
    bids = {b['id'] for b in lib['buildings']}
    errors, seen, keys, out = [], set(), {}, []
    streams = sorted((P / 'research/images').glob('stream-*.json'))
    for f in streams:
        try: recs = json.loads(f.read_text())
        except Exception as e: errors.append(f'{f.name}: not valid JSON ({e})'); continue
        if not isinstance(recs, list): errors.append(f'{f.name}: not a JSON array'); continue
        for r in recs:
            rid = r.get('id')
            where = f'{f.name}:{rid}'
            if not rid or not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,100}', rid): errors.append(f'{where}: bad id'); continue
            if not r.get('title'): errors.append(f'{where}: no title')
            if not (r.get('catalog_url') or r.get('image_url') or r.get('local')): errors.append(f'{where}: no catalog_url, image_url or local file — where does it live?')
            # Two streams finding the SAME item: same catalogue page, same image, same local copy and
            # same kind. A stream never collapses its own records — several plates, crops or pages
            # of one catalogue record are separate items, and the stream that made them knows.
            kind0 = (r.get('kind') or '').strip().lower()
            key = '|'.join([(r.get('catalog_url') or '').rstrip('/'), r.get('image_url') or '',
                            str((r.get('local') or {}).get('display') or ''), kind0])
            if rid in seen: errors.append(f'{where}: duplicate id'); continue
            first = keys.get(key)
            if first is not None and first['stream'] != f.stem.replace('stream-', '') and key.strip('|' + kind0):
                first['building_ids'] = sorted(set(first['building_ids']) | set(r.get('building_ids') or []))
                first.setdefault('also_found_by', []).append(f.stem.replace('stream-', ''))
                continue
            seen.add(rid)
            kind = (r.get('kind') or 'document').strip().lower()
            if kind not in KINDS: kind = 'document' if 'doc' in kind or 'report' in kind else 'photograph' if 'photo' in kind else kind
            rights = norm_rights(r.get('rights'))
            b = [x for x in (r.get('building_ids') or []) if x]
            unknown = [x for x in b if x not in bids]
            if unknown: errors.append(f'{where}: unknown building ids {unknown}')
            local = r.get('local') or None
            if local:
                if rights == PENDING:
                    req = r.get('rights_request') or ''
                    if not (req.startswith('research/images/rights-requests/') and (P / req).is_file()):
                        errors.append(f'{where}: a pending-rights copy must name its request file in rights_request')
                elif rights not in COPYABLE and not str(local.get('display', '')).startswith('research/public/'):
                    errors.append(f'{where}: a local copy of a {rights} item')
                for k in ('display', 'thumb'):
                    v = local.get(k)
                    if v and not (P / v).is_file() and not (v.startswith(store['prefix']) and v[len(store['prefix']):] in store['files']):
                        errors.append(f'{where}: missing local {k} {v} (neither in the package nor in the image store — run tools/sync_image_store.py)')
            rec = dict(r, kind=kind, rights=rights, building_ids=b, stream=f.stem.replace('stream-', ''),
                       period=period_of(r), streetscape=bool(r.get('streetscape')) or not b, local=local)
            keys.setdefault(key, rec)
            out.append(rec)
    errors.extend(validate_reviews(out))
    return out, errors, [f.name for f in streams]


HOUSE = re.compile(r'^(\d{4})(?:\s*[–-]\s*(\d{4}))?\s+S\.\s+Prairie', re.I)


def census():
    return {p.stem.split('-', 1)[1]: json.loads(p.read_text()) for p in sorted((P / 'data/sheet_census').glob('sheet-*.json'))}


def site_plan(lib):
    g = json.loads(GRID.read_text())
    r1 = lambda pts: [[round(x, 1), round(y, 1)] for x, y in pts]
    numbers = {}
    for p in g['parcels']:
        for a in p['addresses_1911']:
            m = re.match(r'\d{4}', a)
            if m: numbers.setdefault(int(m.group()), []).append(p['id'])
    by_parcel, placed, unplaced = {}, {}, []
    for b in lib['buildings']:
        m = HOUSE.match(b.get('address') or '')
        if not m: unplaced.append(b['id']); continue
        lo = int(m.group(1)); hi = int(m.group(2) or lo)
        hits = sorted({pid for n in range(lo, hi + 1, 1) for pid in numbers.get(n, [])})
        if not hits:
            # The nearest printed number on the same face of the block (same parity, same hundred).
            near = [n for n in numbers if n % 2 == lo % 2 and n // 100 == lo // 100 and n <= lo]
            if near: hits = numbers[max(near)]
        if not hits: unplaced.append(b['id']); continue
        placed[b['id']] = {'parcels': hits, 'by': 'printed number' if numbers.get(lo) else 'nearest lower printed number on the same face'}
    # A sheet census (data/sheet_census/) has read the sheet and assigned each record on its ground
    # once, so where one speaks it replaces the number match: the match put Forsyth's 1635 on
    # 1625's lot and reached across the alley to Indiana Avenue lots that share a number.
    for bid, (hits, ticket) in census_placements(census()).items():
        if bid in placed or bid in unplaced:
            placed[bid] = {'parcels': sorted(hits), 'by': f'sheet census ({ticket})'}
            if bid in unplaced: unplaced.remove(bid)
    for bid, at in placed.items():
        for pid in at['parcels']: by_parcel.setdefault(pid, []).append(bid)
    labels = {
        'prairie': 'Prairie Avenue', 'indiana': 'Indiana Avenue', 'calumet': 'Calumet Avenue',
        'e16th': 'E. 16th St.', 'e18th': 'E. 18th St.', 'e20th': 'E. 20th St. (Cullerton)',
        'e21st': 'E. 21st St.', 'e22nd': 'E. 22nd St.'}
    return {
        '_doc': 'GENERATED by tools/build_images.py from ../4d/data/street_grid/1904.json (traced from the '
                'Sanborn 1911 sheets 20, 28, 35). Local ENU metres: x east, y north. A locator for the '
                'viewer: a parcel is a 1911 map lot, not a verified 1904 footprint, and a building is '
                'placed by its sheet census where one has read its ground, else by its printed house number.',
        'frame': g.get('frame'),
        'streets': {k: {'label': labels.get(k, k), 'name_1904': v.get('name_1904')} for k, v in g['streets'].items()},
        'blocks': [{'id': b['id'], 'where': b.get('where'), 'outline': r1(b['outline_local_m'])} for b in g['blocks']],
        'carriageways': [{'id': c['id'], 'street': c.get('street'), 'polygon': r1(c['polygon_local_m'])} for c in g['carriageways']],
        'alleys': [{'id': a['id'], 'polygon': r1(a['polygon_local_m'])} for a in g['alleys']],
        'parcels': [{'id': p['id'], 'addresses': p['addresses_1911'], 'side': p.get('side'),
                     'polygon': r1(p['polygon_local_m']), 'frontage_ft': p.get('frontage_ft'),
                     'building_ids': by_parcel.get(p['id'], [])} for p in g['parcels']],
        'placed': placed, 'unplaced': unplaced,
    }


def build():
    lib = load_library()
    images, errors, streams = merge(lib)
    order = {b['id']: i for i, b in enumerate(lib['buildings'])}
    images.sort(key=lambda r: (min([order.get(b, 999) for b in r['building_ids']] or [999]),
                               r.get('date_earliest') or r.get('date_latest') or 9999, r['id']))
    plan = site_plan(lib)
    # Every record is placed on the traced lots it shows: through its buildings, and through
    # any Prairie Avenue address it names — so a picture of a house the library has no
    # building record for (1730, 2120 …) still lands on its lot.
    numbers = {}
    for pc in plan['parcels']:
        for a in pc['addresses']:
            m = re.match(r'\d{4}', a)
            if m: numbers.setdefault(int(m.group()), []).append(pc['id'])
    by_building, by_parcel = {}, {}
    for r in images:
        lots = {pid for b in r['building_ids'] for pid in plan['placed'].get(b, {}).get('parcels', [])}
        for a in r.get('addresses') or []:
            m = HOUSE.match(str(a).strip())
            if not m: continue
            lo = int(m.group(1)); hi = int(m.group(2) or lo)
            lots |= {pid for n in range(lo, hi + 1) for pid in numbers.get(n, [])}
        r['parcel_ids'] = sorted(lots)
        for b in r['building_ids']: by_building.setdefault(b, []).append(r['id'])
        for pid in r['parcel_ids']: by_parcel.setdefault(pid, []).append(r['id'])
    counts = {'images': len(images), 'local': sum(1 for r in images if r.get('local')),
              'in_period': sum(1 for r in images if r['period'] == 'in-period'),
              'buildings_with_images': len(by_building), 'buildings': len(lib['buildings']),
              'lots_with_images': len(by_parcel), 'lots': len(plan['parcels'])}
    doc = {'_doc': 'GENERATED by tools/build_images.py from research/images/stream-*.json — edit the streams, '
                   'not this file. Schema: research/images/README.md.',
           'image_store': {k: v for k, v in store_index().items() if k in ('base_url', 'prefix', 'repository')} or None,
           'streams': streams, 'counts': counts, 'by_building': by_building, 'by_parcel': by_parcel,
           'images': images}
    return doc, plan, errors


def dump(o): return json.dumps(o, ensure_ascii=False, indent=1) + '\n'


if __name__ == '__main__':
    if {'-h', '--help'} & set(sys.argv): print(__doc__); sys.exit()
    doc, plan, errors = build()
    if errors:
        print('\n'.join(errors)); sys.exit(f'{len(errors)} problem(s) in the image streams')
    targets = {P / 'data/images.json': dump(doc), P / 'data/site-plan.json': dump(plan)}
    if '--check' in sys.argv:
        stale = [str(p.relative_to(P)) for p, t in targets.items() if not p.exists() or p.read_text() != t]
        if stale: sys.exit('stale (re-run tools/build_images.py): ' + ', '.join(stale))
        print('images.json and site-plan.json are current'); sys.exit()
    for p, t in targets.items(): p.write_text(t)
    c = doc['counts']
    print(f"{c['images']} records ({c['local']} with local copies, {c['in_period']} in-period) across "
          f"{c['buildings_with_images']} of {c['buildings']} buildings and {c['lots_with_images']} of {c['lots']} lots; {len(plan['placed'])} buildings placed on "
          f"the site plan, unplaced: {', '.join(plan['unplaced']) or 'none'}")
