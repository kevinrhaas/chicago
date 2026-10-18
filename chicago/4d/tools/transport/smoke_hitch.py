# SPDX-License-Identifier: GPL-3.0-or-later
import json,pathlib,math,gzip,hashlib
from playwright.sync_api import sync_playwright
P=pathlib.Path(__file__).resolve().parents[2]/'docs/RESEARCH/period-transport-2026-10-18/hitch'
report={'scope':'exported GLBs coupled in browser; geometric study, not force or full collision certification','browser':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for w,h in [(1280,800),(390,780)]:
  page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8774/renderers/web/transport/hitch/');page.wait_for_function('window.hitchFixture?.ready===true');page.wait_for_timeout(400);states=[]
  for steer in [0,8,-8]:
   page.evaluate('(d)=>window.hitchFixture.setSteer(d)',steer)
   for d in [0,.25,.5,1,2,3,5]:
    page.evaluate('(d)=>window.hitchFixture.setDistance(d)',d);s=page.evaluate('window.hitchFixture.state');s['clearance']=page.evaluate('window.hitchFixture.clearance()');assert s['head_bind_error_m']<1e-7;assert max(e['actual_tube_endpoint_error_m'] for e in s['straps'])<1e-5;assert all(v==[1,1,1] for v in s['scales'].values());assert all(math.isfinite(x) for c in s['contacts'] for x in c['position']);states.append(s)
  page.evaluate('window.hitchFixture.setSteer(0);window.hitchFixture.setDistance(0)');page.wait_for_timeout(200);page.screenshot(path=str(P/f'preview-{w}-rest.png'))
  page.evaluate('window.hitchFixture.setSteer(8);window.hitchFixture.setDistance(1)');page.wait_for_timeout(200);page.screenshot(path=str(P/f'preview-{w}-turn.png'));assert not errors,errors
  report['browser'].append({'viewport':[w,h],'page_errors':errors,'sample_count':len(states),'maximum_strap_geometry_endpoint_error_m':max(e['actual_tube_endpoint_error_m'] for s in states for e in s['straps']),'maximum_head_binding_error_m':max(s['head_bind_error_m'] for s in states),'min_contact_y_m':min(c['position'][1] for s in states for c in s['contacts']),'max_contact_y_m':max(c['position'][1] for s in states for c in s['contacts']),'min_shaft_torso_lateral_envelope_clearance_m':min(s['clearance']['shaft_torso_lateral_envelope_clearance_m'] for s in states),'min_horse_body_longitudinal_gap_m':min(s['clearance']['horse_body_longitudinal_gap_m'] for s in states),'max_shaft_attachment_endpoint_gap_m':max(s['shaft_attachment_endpoint_gap_m'] for s in states),'samples':states});page.close()
 b.close()
payload=gzip.compress(json.dumps([case.pop('samples') for case in report['browser']],separators=(',',':')).encode(),mtime=0)
(P/'samples.json.gz').write_bytes(payload)
report['raw_samples']={'file':'samples.json.gz','sha256':hashlib.sha256(payload).hexdigest(),'format':'gzip JSON array: one 21-state sample list per viewport'}
(P/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items() if k!='samples'} for x in report['browser']],indent=2))
