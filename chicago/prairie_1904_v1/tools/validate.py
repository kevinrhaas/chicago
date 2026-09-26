#!/usr/bin/env python3
"""Validate identities, citations, local files and bounded evidence distinctions."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1]
j=json.loads((P/'data/library.json').read_text()); errors=[]
def require(ok,msg):
 if not ok:errors.append(msg)
for key in ['buildings','sources','maps']:
 ids=[x['id'] for x in j[key]];require(len(ids)==len(set(ids)),f'duplicate {key} ids')
sources={s['id'] for s in j['sources']}
for s in j['sources']:
 if s.get('local_path'):require((P/s['local_path']).is_file(),f'missing local source {s["id"]}')
for b in j['buildings']:
 require(bool(b.get('source_ids')),f'uncited building {b["id"]}')
 for sid in b['source_ids']:require(sid in sources,f'unknown source {sid}')
 require(not b.get('coordinates'),f'coordinates not validated: {b["id"]}')
for m in j['maps']:require((P/m['local_path']).is_file(),f'missing map {m["id"]}')
for f in j['glessner']['sections']:
 for sid in f['source_ids']:require(sid in sources,f'unknown Glessner source {sid}')
for r in j['map_inventory']['records']:
 require(r['observation_year']==1911,'map silently backdated')
 require(r.get('dimensions_ft') is None,'unvalidated map dimensions')
for r in j['occupancy_candidates']:require('verification' in r,'directory verification missing')
for m in json.loads((P/'research/acquired-files.json').read_text()):
 if m['retention']=='repository':
  p=P/m['path'];require(p.exists(),f'missing archived file {p}')
  if p.exists():require(hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256'],f'hash mismatch {p}')
for r in j.get('measurements',[]):require(r.get('source_id') in sources,'unresolved measurement source')
require(j['meta']['target_year']==1904,'wrong target')
print(f'{len(j["buildings"])} buildings; {len(sources)} sources; {len(j["map_inventory"]["records"])} frontage readings; {len(j["occupancy_candidates"])} directory candidates')
if errors:raise SystemExit('\n'.join(errors))
print('PASS: identities, evidence dates, source links and acquired-file hashes')
