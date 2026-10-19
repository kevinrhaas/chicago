# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure current breastcollar route against loaded neutral torso skin; no model edits."""
import json,pathlib
from playwright.sync_api import sync_playwright
P=pathlib.Path(__file__).parent
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1280,'height':800});page.goto('http://127.0.0.1:8774/renderers/web/transport/horse/');page.wait_for_function('window.fixture?.ready');page.evaluate('fixture.pause();fixture.setClip("idle");fixture.setPhase(0)')
 data=page.evaluate("""async()=>{
 const T=await import('../../vendor/three-0.185.1/three.module.js');const {GLTFLoader}=await import('../../vendor/three-0.185.1/addons/loaders/GLTFLoader.js');
 const manifest=await(await fetch('manifest.json')).json(),params=await(await fetch('../../../../data/transport/studies/harness.json')).json();const range=manifest.vertex_ranges.find(r=>r.original_node==='continuous_body_neck');const harness=await new GLTFLoader().loadAsync('../harness/light_breastcollar_harness_reconstructed_01.glb');harness.scene.updateMatrixWorld(true);const collar=harness.scene.getObjectByName('breastcollar');const garment=[];for(let i=0;i<collar.geometry.attributes.position.count;i++)garment.push(new T.Vector3().fromBufferAttribute(collar.geometry.attributes.position,i).applyMatrix4(collar.matrixWorld));
 const m=fixture.horse.getObjectByName('skinned_equine_coat'),g=m.geometry;
 function triangles(){m.skeleton.update();fixture.horse.updateMatrixWorld(true);const ts=[];for(let i=0;i<g.index.count;i+=3){const ids=[0,1,2].map(j=>g.index.getX(i+j));if(ids.every(id=>id>=range.vertex_start&&id<range.vertex_start+range.vertex_count))ts.push({ids,tri:new T.Triangle(...ids.map(id=>m.getVertexPosition(id,new T.Vector3()).applyMatrix4(m.matrixWorld)))});}return ts;}
 function nearest(pt,ts){let best={distance_m:Infinity};for(const {ids,tri} of ts){const q=tri.closestPointToPoint(pt,new T.Vector3()),distance=pt.distanceTo(q);if(distance<best.distance_m){const n=tri.getNormal(new T.Vector3()),signed=pt.clone().sub(q).dot(n);best={distance_m:distance,point_m:q.toArray(),normal:n.toArray(),signed_triangle_plane_distance_m:signed,signed_nearest_distance_m:Math.sign(signed)*distance,suggested_outer_route_10mm_m:q.clone().addScaledVector(n,.010).toArray(),triangle_vertex_ids:ids};}}return best;}
 fixture.setClip('idle');fixture.setPhase(0);let ts=triangles();const samples=params.breastcollar_route_m.map(x=>({route_m:x,...nearest(new T.Vector3(...x),ts)}));const phases=[];
 for(const clip of ['idle','walk'])for(let i=0;i<(clip==='idle'?1:21);i++){
  const phase=clip==='idle'?0:i/20;fixture.setClip(clip);fixture.setPhase(phase);const ts=triangles();let low={signed_nearest_distance_m:Infinity},high={signed_nearest_distance_m:-Infinity},penetrating=0;
  for(let j=0;j<garment.length;j++){const v=garment[j],n=nearest(v,ts);if(n.signed_nearest_distance_m<low.signed_nearest_distance_m)low={vertex_index:j,vertex_m:v.toArray(),...n};if(n.signed_nearest_distance_m>high.signed_nearest_distance_m)high={vertex_index:j,vertex_m:v.toArray(),...n};if(n.signed_nearest_distance_m<-.001)penetrating++;}
  phases.push({clip,phase,vertex_samples:garment.length,vertices_with_signed_distance_below_minus_1mm:penetrating,min:low,max:high});
 }
 return{asset:manifest.asset_id,torso_range:range,samples,width_aware:{method:'all actual breastcollar mesh vertices against actual skinned continuous torso triangles; sign from nearest face normal, not a watertight inside test; no edge/face intersection or limb test',phases,min_signed_distance_m:Math.min(...phases.map(p=>p.min.signed_nearest_distance_m)),max_signed_distance_m:Math.max(...phases.map(p=>p.max.signed_nearest_distance_m))}};
}""");b.close()
assert data['width_aware']['min_signed_distance_m']>=0, 'Breastcollar vertex nearest-torso-face sign criterion failed; not a full collision certificate'
(P/'torso-clearance.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'route_samples':data['samples'],'width_aware_summary':{k:v for k,v in data['width_aware'].items() if k!='phases'}},indent=2))
