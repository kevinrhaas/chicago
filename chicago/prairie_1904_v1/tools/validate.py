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
# SHEET CENSUSES (T-1841): every frontage the sheet draws is answered by exactly one census entity,
# every named record the sheet touches is listed exactly once, and every id resolves.
images_by_id={r['id'] for r in json.loads((P/'data/images.json').read_text())['images']} if (P/'data/images.json').exists() else set()
buildings_by_id={b['id'] for b in j['buildings']}
for path in j['meta'].get('sheet_censuses',[]):
 c=json.loads((P/path).read_text());sheet=str(c['sheet']);tag=f'census {sheet}'
 ents={e['id']:e for e in c['entities']};require(len(ents)==len(c['entities']),f'{tag}: duplicate entity ids')
 fronts={r['id'] for r in j['map_inventory']['records'] if str(r.get('sheet'))==sheet}
 require(set(c['frontage_assignments'])==fronts,f'{tag}: frontages unassigned {sorted(fronts-set(c["frontage_assignments"]))} or unknown {sorted(set(c["frontage_assignments"])-fronts)}')
 for fid,eid in c['frontage_assignments'].items():require(ents.get(eid,{}).get('frontage_id')==fid,f'{tag}: {fid} assigned to {eid}, which is not on that frontage')
 named=[n['building_id'] for n in c['named_records']];require(len(named)==len(set(named)),f'{tag}: a named record is listed twice')
 for bid in named:require(bid in buildings_by_id,f'{tag}: unknown named record {bid}')
 for cw in j['address_crosswalk']:
  if cw['frontage_id'] in fronts:
   require(cw['match_status']!='candidate_by_printed_number_not_resolved_identity',f'{tag}: crosswalk {cw["frontage_id"]} still unresolved')
   for bid in cw['candidate_building_ids']:require(bid in named,f'{tag}: {bid} on {cw["frontage_id"]} has no named-record entry')
 for e in c['entities']+c['rulings']:
  require(e['tier'] in c['tiers'],f'{tag}: {e["id"]} tier {e["tier"]}')
  for sid in e['source_ids']:require(sid in sources,f'{tag}: {e["id"]} cites unknown source {sid}')
  for iid in e.get('evidence_images',[])+e.get('images',[]):require(iid in images_by_id,f'{tag}: {e["id"]} cites unknown image {iid}')
  if e.get('building_id'):require(e['building_id'] in named,f'{tag}: {e["id"]} owner {e["building_id"]} has no named-record entry')
# THE IMAGE COLLECTION'S BYTES LIVE IN kevinrhaas/chicago-images (owner, 2026-10-02: "you can go as
# large as you need to, 500MB or 2GB"). That repository is its own GitHub Pages site, so its own
# 1 GB publish limit is what binds — not this site's. research/images/STORE.json (written by
# tools/sync_image_store.py) records every file there; at 950 MB the collection needs a second
# store repository, so that is the budget, with a warning at 850.
STORE_BUDGET_MB=950
store=json.loads((P/'research/images/STORE.json').read_text()) if (P/'research/images/STORE.json').exists() else {'bytes':0,'files':{}}
img_mb=store.get('bytes',0)/1048576
require(img_mb<=STORE_BUDGET_MB,f'image store is {img_mb:.1f} MB, over {STORE_BUDGET_MB} MB — add a second store repository (research/images/files/README.md)')
if img_mb>850:print(f'WARN image store at {img_mb:.1f} of {STORE_BUDGET_MB} MB — plan the second store repository')
# The first store (research/images/files/) was emptied on 2026-10-02 once kevinrhaas/chicago-images was
# serving: image files live only there now, so none may land here.
stray=sorted(p.name for p in (P/'research/images/files').glob('*') if p.is_file() and p.name!='README.md') if (P/'research/images/files').exists() else []
require(not stray,f'{len(stray)} file(s) in research/images/files/ (e.g. {stray[:3]}) — image files go to kevinrhaas/chicago-images via tools/fetch_image.py')
IMAGE_BUDGET_MB=STORE_BUDGET_MB
# The image & document index (research/images/README.md): every stream record checked and merged, both outputs current.
import subprocess,sys
r=subprocess.run([sys.executable,str(P/'tools/build_images.py'),'--check'],capture_output=True,text=True)
require(r.returncode==0,'image index: '+(r.stdout+r.stderr).strip())
if (P/'data/images.json').exists():
 im=json.loads((P/'data/images.json').read_text())
 for rec in im['images']:
  for bid in rec['building_ids']:require(bid in {b['id'] for b in j['buildings']},f'image {rec["id"]} cites unknown building {bid}')
  if rec.get('local'):require(rec['rights'] in ('public domain','no known restrictions') or (rec['rights']=='pending — permission requested' and (P/str(rec.get('rights_request') or 'x')).is_file()) or rec['local'].get('display','').startswith('research/public/'),f'image {rec["id"]}: local copy of a {rec["rights"]} item')
print(f'image store {img_mb:.1f} of {STORE_BUDGET_MB} MB ({len(store.get("files",{}))} files, kevinrhaas/chicago-images)');print(f'{len(j["buildings"])} buildings; {len(sources)} sources; {len(j["map_inventory"]["records"])} frontage readings; {len(j["occupancy_candidates"])} directory candidates')
if errors:raise SystemExit('\n'.join(errors))
subprocess.run([sys.executable, str(P/'tools/test_evidence_review.py')], check=True)
print('PASS: identities, evidence dates, source links and acquired-file hashes')
