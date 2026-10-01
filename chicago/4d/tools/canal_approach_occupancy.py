#!/usr/bin/env python3
"""T-1766: five trade roofs, five existing heads, no new people or claimed homes.

--build writes five authored firms; --check reproduces them; --self-test mutates
identity, division, trade and duplicate assignments. Geometry consumes occupancy()
and assignments(). A separate trade_roof business form keeps lodging beds honest.
"""
import argparse
import copy
import json
from pathlib import Path
from compile_businesses import derive_proprietor_community, person_communities

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/reconstruction/1835_canal_approach_occupancy.json'
SOURCE = 'owner_chicago_1835_reconstruction_spec_2026'
PREFIX = 'rcb_canal_'


def load():
    return json.loads(INPUT.read_text())


def resolved(doc=None):
    doc = load() if doc is None else doc
    seen = {key: set() for key in ('family', 'structure_id', 'person_id', 'household_id', 'business_id')}
    result = []
    for row in doc['rows']:
        for key, values in seen.items():
            if row[key] in values:
                raise ValueError('duplicate ' + key)
            values.add(row[key])
        hh = json.loads((ROOT / 'data/residents/reconstructed_trades' / (row['household_id'] + '.json')).read_text())
        head = next((p for p in hh['persons'] if p['id'] == row['person_id']), None)
        if head is None or hh['head'] != row['person_id']:
            raise ValueError('keeper is not the existing household head')
        if hh['division'] != 'west':
            raise ValueError('keeper must remain in the west division')
        if head['occupation']['value'] != row['occupation']:
            raise ValueError('the existing occupation cannot be reassigned')
        expected = {'C3':'grocer','C4':'grocer','W1':'blacksmith','W2':'carpenter','W3':'carpenter'}
        if expected.get(row['family']) != row['occupation']:
            raise ValueError('family and existing trade disagree')
        if row['structure_id'] != 'recon_1835_canal_trade_' + row['family'].lower() + '_' + {'C3':'001','C4':'002','W1':'003','W2':'004','W3':'005'}[row['family']]:
            raise ValueError('assignment escaped the five new roofs')
        if not row['business_id'].startswith(PREFIX):
            raise ValueError('firm escaped this generator namespace')
        for path in list((ROOT / 'data/businesses/authored').glob('*.json')) + list((ROOT / 'data/businesses').glob('*.json')):
            other = json.loads(path.read_text())
            if not other.get('id') or other['id'].startswith(PREFIX):
                continue
            if any(p.get('person_id') == row['person_id'] for p in other.get('proprietors', [])):
                raise ValueError('keeper already owns another authored firm: ' + other['id'])
        result.append((row, hh, head))
    if seen['family'] != {'C3','C4','W1','W2','W3'}:
        raise ValueError('exactly the five ticket roofs must be occupied')
    return result


def note(row):
    extra = (' The wagon woodwork specialty is invented within a carpenter\'s woodworking trade; '
             'the person remains a carpenter, not a documented wheelwright or cooper.' if row['family'] == 'W3' else '')
    return ('RECONSTRUCTED WORKPLACE AND FIRM, T-1766. The standing roof adopts an existing west '
            'trade head; no person is minted, no source places this firm here, and no residence '
            'is asserted. The need is bounded by owner_chicago_1835_reconstruction_spec_2026. This is an explicit family-to-head allocation, not a recovered address.' + extra)


def occupancy():
    return {row['structure_id']: {'value': head['name'] + ', ' + row['trade'],
            'confidence': 'reconstructed', 'sources': [SOURCE], 'note': note(row)}
            for row, hh, head in resolved()}


def assignments():
    """No residential allocation: the platted dealer treats this key as a home seat.

    Workplace occupation is carried by occupants() and the firm's primary premises.
    """
    return {}


def records(doc=None):
    out = []
    for row, hh, head in resolved(doc):
        n = note(row)
        rec = {
            'id': row['business_id'], 'register_id': None,
            'name': head['name'] + ', ' + row['trade'], 'provenance': 'reconstructed',
            'type': ['store' if row['family'].startswith('C') else 'other'],
            'trade': row['trade'], 'occupation': row['occupation'], 'goods': [row['trade']],
            'firm_styles': [], 'proprietors': [{'name': head['name'], 'person_id': head['id'],
                'register_person_id': None, 'role': 'proprietor', 'from': None, 'to': None,
                'tier': 'reconstructed', 'basis': n, 'source_id': None, 'claim_ids': []}],
            'partners': [], 'staff': [],
            'locations': [{'kind':'premises','structure_id':row['structure_id'],'street_id':'canal',
                'face':None,'primary':True,'from':None,'to':None,'tier':'reconstructed',
                'basis':n,'limit_reason':'The whole placement is invented within the Canal approach programme.'}],
            'dates': {'opened':None,'closed':None,'precision':'unbounded','tier':'reconstructed',
                'basis':'Reconstructed as trading on 1835-07-01; no opening or closing date is claimed.'},
            'evidence':{},'present_at_scene_date':True,'exclusion':None,'exclusion_note':None,
            'proprietor_community':[], 'customers':[], 'sources':[], 'claim_ids':[],
            'liberties':{'survival_required':False,'backdating_required':False},'review_required':False,
            'replaceable_by':'Evidence naming the real keeper or premises; retirement of this reconstructed roof or keeper.',
            'reconstruction':{'programme':'canal_approach_trade_roofs','group':'canal_approach',
                'ticket':'T-1766','seed':'T-1766:' + row['family'] + ':' + head['id'],
                'trade_roof':{'structure_id':row['structure_id'],'family':row['family'],
                    'keeper_person_id':head['id'],'keeper_household_id':hh['id'],
                    'occupation':row['occupation'],'note':n},
                'basis':{'kind':'rule','id':'1835_canal_approach_occupancy','note':n},
                'withdrawn_if':'The roof or its existing keeper is retired, or evidence replaces this reconstructed firm.'}}
        rec["proprietor_community"] = derive_proprietor_community(rec["proprietors"], [], person_communities())
        out.append(rec)
    return out


def self_test():
    from compile_businesses import trade_roof_faults, semantic_problems
    if assignments(): raise ValueError("workplace allocation became a residential seat")
    for label, mutate in [
        ('duplicate keeper',lambda d:d['rows'][1].update(person_id=d['rows'][0]['person_id'])),
        ('invented trade',lambda d:d['rows'][4].update(occupation='wheelwright')),
        ('wrong head',lambda d:d['rows'][0].update(person_id='rc_missing')),
        ('foreign roof',lambda d:d['rows'][0].update(structure_id='recon_elsewhere')),
        ('missing roof',lambda d:d['rows'].pop()),
    ]:
        d=copy.deepcopy(load());mutate(d)
        try: resolved(d)
        except (ValueError,FileNotFoundError): pass
        else: raise ValueError('self-test accepted ' + label)
    import jsonschema
    schema=json.loads((ROOT/'data/businesses.schema.json').read_text())
    for rec in records():
        jsonschema.validate(rec,schema)
        if semantic_problems([rec]): raise ValueError(semantic_problems([rec]))
        if trade_roof_faults(rec): raise ValueError('valid trade roof refused')
    for label, mutate in [
        ('wrong premises',lambda r:r['locations'][0].update(structure_id='wrong')),
        ('wrong proprietor',lambda r:r['proprietors'][0].update(person_id='wrong')),
        ('false occupation',lambda r:r.update(occupation='wheelwright')),
        ('false beds',lambda r:r['reconstruction']['trade_roof'].update(beds_ordinary=1)),
        ('missing household',lambda r:r['reconstruction']['trade_roof'].update(keeper_household_id='')),
    ]:
        rec=copy.deepcopy(records()[0]);mutate(rec)
        if not trade_roof_faults(rec): raise ValueError('compiler accepted ' + label)
    # The pre-existing lodging form still requires a real positive bed capacity.
    lodging=next(json.loads(p.read_text()) for p in (ROOT/'data/businesses/authored').glob('*.json')
                 if json.loads(p.read_text()).get('reconstruction',{}).get('roof'))
    jsonschema.validate(lodging,schema)
    del lodging['reconstruction']['roof']['beds_ordinary']
    try: jsonschema.validate(lodging,schema)
    except jsonschema.ValidationError: pass
    else: raise ValueError('lodging lost its bed requirement')
    print('Canal occupancy: identity/trade refusal mutations, compiler joins, five schemas and unchanged lodging bed gate pass')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test: self_test();return
    for rec in records():
        path=ROOT/'data/businesses/authored'/(rec['id']+'.json')
        text=json.dumps(rec,indent=2,ensure_ascii=False)+'\n'
        if a.build: path.write_text(text)
        elif a.check:
            roof_path=ROOT/'data/structures'/(rec['reconstruction']['trade_roof']['structure_id']+'.json')
            if not roof_path.exists(): raise ValueError('trade firm requires its standing roof: '+str(roof_path))
            roof=json.loads(roof_path.read_text())
            if roof.get('reconstruction',{}).get('family') != rec['reconstruction']['trade_roof']['family']:
                raise ValueError('standing roof family differs from the occupied trade family')
            if not path.exists() or path.read_text()!=text: raise ValueError('stale '+str(path))
        else: p.error('choose --build, --check or --self-test')
    print('Canal occupancy: five existing keepers, five reconstructed firms; no people or homes created')


if __name__ == '__main__': main()
