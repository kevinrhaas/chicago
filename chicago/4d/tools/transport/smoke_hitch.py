# SPDX-License-Identifier: GPL-3.0-or-later
import json,pathlib,math,gzip,hashlib,struct
from playwright.sync_api import sync_playwright
P=pathlib.Path(__file__).resolve().parents[2]/'docs/RESEARCH/period-transport-2026-10-18/hitch'
report={'scope':'exported GLBs coupled in browser; geometric study, not force or full collision certification','browser':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for w,h in [(1280,800),(390,780)]:
  page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8774/renderers/web/transport/hitch/');page.wait_for_function('window.hitchFixture?.ready===true');page.wait_for_timeout(400);states=[]
  for steer in [0,8,-8,12,-12]:
   page.evaluate('(d)=>window.hitchFixture.setSteer(d)',steer)
   for d in [0,.25,.5,1,2,3,5]:
    page.evaluate('(d)=>window.hitchFixture.setDistance(d)',d);s=page.evaluate('window.hitchFixture.state');s['clearance']=page.evaluate('window.hitchFixture.clearance()');assert s['head_bind_error_m']<1e-7;assert s['shaft_attachment_endpoint_gap_m']<1e-5;assert min(f['radial_clearance_m'] for f in s['shaft_tug_fit'])>0;assert max(e['actual_tube_endpoint_error_m'] for e in s['straps'])<1e-5;assert all(v==[1,1,1] for v in s['scales'].values());assert all(math.isfinite(x) for c in s['contacts'] for x in c['position']);states.append(s)
  # Independent finite difference of actual loaded wheel-center trajectories.
  # Compare observed center travel with roll-angle delta times exported radius.
  geometry_checks=[]
  if w==1280:
   vehicle_parameters=json.loads((pathlib.Path(__file__).resolve().parents[2]/'renderers/web/transport/carriage/carriage-c01.json').read_text())['parameters']
   for angle in [0,8,-8,12,-12]:
    page.evaluate('(a)=>window.hitchFixture.setSteer(a)',angle);samples=[]
    for distance in [1,1.01]:
     page.evaluate('(s)=>window.hitchFixture.setDistance(s)',distance)
     samples.append(page.evaluate("""()=>{const f=window.hitchFixture;f.scene.updateMatrixWorld(true);return ['rear_left','rear_right','front_left','front_right'].map(name=>{const o=f.scene.getObjectByName('vehicle_wheel_'+name);return {name,center:Array.from(o.matrixWorld.elements).slice(12,15),angle:o.rotation.x};});}"""))
    for first,last in zip(*samples):
     observed=math.dist(first['center'],last['center']);assert observed>.005;end=first['name'].split('_')[0];rolled=abs(last['angle']-first['angle'])*vehicle_parameters['wheel_radius_'+end+'_m'];error=abs(observed-rolled);assert error<1e-8,(angle,first['name'],observed,rolled,error);geometry_checks.append({'steer_deg':angle,'wheel':first['name'],'world_center_chord_m':observed,'rolled_surface_m':rolled,'error_m':error})
   report['wheel_path_finite_difference']={'method':'actual loaded world wheel centers at rear-axle distances1m and1.01m; compare chord to roll-angle increment times exported radius','max_error_m':max(x['error_m'] for x in geometry_checks),'samples':geometry_checks}
  page.evaluate('window.hitchFixture.setSteer(0);window.hitchFixture.setDistance(0)');page.wait_for_timeout(200);page.screenshot(path=str(P/f'preview-{w}-rest.png'))
  page.evaluate('window.hitchFixture.setSteer(8);window.hitchFixture.setDistance(1)');page.wait_for_timeout(200);page.screenshot(path=str(P/f'preview-{w}-turn.png'));assert not errors,errors
  report['browser'].append({'viewport':[w,h],'page_errors':errors,'sample_count':len(states),'maximum_strap_geometry_endpoint_error_m':max(e['actual_tube_endpoint_error_m'] for s in states for e in s['straps']),'maximum_head_binding_error_m':max(s['head_bind_error_m'] for s in states),'min_contact_y_m':min(c['position'][1] for s in states for c in s['contacts']),'max_contact_y_m':max(c['position'][1] for s in states for c in s['contacts']),'min_shaft_torso_lateral_envelope_clearance_m':min(s['clearance']['shaft_torso_lateral_envelope_clearance_m'] for s in states),'min_horse_body_longitudinal_gap_m':min(s['clearance']['horse_body_longitudinal_gap_m'] for s in states),'min_shaft_tug_radial_clearance_m':min(f['radial_clearance_m'] for s in states for f in s['shaft_tug_fit']),'max_shaft_attachment_endpoint_gap_m':max(s['shaft_attachment_endpoint_gap_m'] for s in states),'samples':states});page.close()
 # Metadata-only perturbation: intercepted responses leave tracked assets untouched.
 # This proves consumption, not physical validity of an inconsistent alternative model.
 app=pathlib.Path(__file__).resolve().parents[2]/'renderers/web/transport'
 raw=(app/'carriage/carriage-c01.glb').read_bytes();jn=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jn]);alternate=doc['extras']['parameters']
 for key in ['wheelbase_m','track_m','wheel_radius_front_m','wheel_radius_rear_m']:alternate[key]*=1.1
 encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*(-len(encoded)%4);tail=raw[20+jn:];body=struct.pack('<III',0x46546c67,2,20+len(encoded)+len(tail))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+tail
 hm=json.loads((app/'horse/manifest.json').read_text());hm['locomotion']['walk']['stride_m']*=1.1
 page=b.new_page(viewport={'width':1280,'height':800});page.route('**/carriage-c01.glb',lambda r:r.fulfill(body=body,content_type='model/gltf-binary'));page.route('**/horse/manifest.json',lambda r:r.fulfill(json=hm));page.goto('http://127.0.0.1:8774/renderers/web/transport/hitch/');page.wait_for_function('window.hitchFixture?.ready===true');page.evaluate('window.hitchFixture.setSteer(8);window.hitchFixture.setDistance(1)');state=page.evaluate('window.hitchFixture.state');k=math.tan(math.radians(8))/alternate['wheelbase_m'];expected=[]
 for end in ['rear','front']:
  for sign in [1,-1]:
   x=sign*alternate['track_m']/2;factor=1-k*x if end=='rear' else 1/math.cos(math.radians(8))-k*x;expected.append(factor/alternate['wheel_radius_'+end+'_m'])
 assert max(abs(a-b) for a,b in zip(state['wheel_angles'],expected))<1e-9
 expected_phase=(state['horse_path_m']/hm['locomotion']['walk']['stride_m'])%1;assert abs(state['phase']-expected_phase)<1e-9
 report['metadata_sensitivity']={'method':'Playwright response overrides only; original geometry unchanged; not a valid alternative physical asset','factor':1.1,'fields':list(alternate_key for alternate_key in ['wheelbase_m','track_m','wheel_radius_front_m','wheel_radius_rear_m'])+['locomotion.walk.stride_m'],'actual_wheel_angles_rad':state['wheel_angles'],'expected_wheel_angles_rad':expected,'actual_phase':state['phase'],'expected_phase':expected_phase,'passed':True};page.close()
 b.close()
payload=gzip.compress(json.dumps([case.pop('samples') for case in report['browser']],separators=(',',':')).encode(),mtime=0)
(P/'samples.json.gz').write_bytes(payload)
report['raw_samples']={'file':'samples.json.gz','sha256':hashlib.sha256(payload).hexdigest(),'format':'gzip JSON array: one 35-state sample list per viewport'}
(P/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items() if k!='samples'} for x in report['browser']],indent=2))
