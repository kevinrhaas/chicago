// SPDX-License-Identifier: GPL-3.0-or-later
// Metadata and synthetic native-Three CPU controls. No actual asset/native-fit claim.
import assert from 'node:assert/strict';
import test from 'node:test';
import {ASSET,LINEN_PATCH,LIMITS,POSES,OBSERVER_FILES,parentFiles,validateRequest,
  validateRuntimeInventory,validateBeforeObservation,captureViews,validatePose,checkBudget,signedRearGap,nativeSeatObserver,inspectorReady} from './human_settler_seat_review.mjs';
const sha='a'.repeat(64),source='b'.repeat(40),definition='c'.repeat(40);
function fixture(){
  const parents=parentFiles().map(file=>({file,sha256:sha,bytes:100}));
  const request={schema:'t1789_settler_seat_observer_request_v1',status:'BOUND_FOR_NATIVE_OBSERVATION',asset_id:ASSET,
    role:'before',release:false,native_fit_accepted:false,source_commit:source,receipt_sha256:sha,
    observer_base_commit:source,runtime_base_commit:source,runtime_inventory_sha256:sha,
    observer_files:OBSERVER_FILES.map(file=>({file,sha256:sha})),receipt_kind:'fixture_baseline',parents};
  return {request,receipt:{files:parents.map(row=>({...row,verdicts:[{ok:true}]}))}};
}
test('bound baseline and closed actual-capture metadata remain distinct',()=>{
  const {request,receipt}=fixture();assert.equal(validateRequest(request,receipt).size,8);
  request.role='after';request.receipt_kind='canonical_capture';request.source_patch_sha256=LINEN_PATCH;request.definition_commit=definition;
  const capture={schema:'t1789_canonical_parent_capture_v2',status:'CANONICAL_PARENT_CAPTURE_ONLY',phase:'CLOSED',
    source_sha:source,definition_sha:definition,release:false,install:false,material_applied:false,native_fit_accepted:false,
    parent_hashes:request.parents.map(row=>({...row,file:ASSET+'/parents/'+row.file}))};
  assert.equal(validateRequest(request,capture).size,8);
  for(const key of ['release','install','material_applied','native_fit_accepted']){
    const bad=structuredClone(capture);bad[key]=true;assert.throws(()=>validateRequest(request,bad));
  }
  capture.phase='PRODUCERS';assert.throws(()=>validateRequest(request,capture));
});
test('unknown, stale, extra, duplicate and failed input bindings cannot run',()=>{
  for(const change of [r=>r.source_commit=null,r=>r.status='NOT_ADMITTED',r=>r.parents.pop(),
    r=>r.parents.push({...r.parents[0]}),r=>r.parents[0].sha256=null,r=>r.parents[0].file='../other',
    r=>r.observer_files.pop()]){const {request,receipt}=fixture();change(request);assert.throws(()=>validateRequest(request,receipt));}
  const {request,receipt}=fixture();receipt.files[0].sha256='d'.repeat(64);assert.throws(()=>validateRequest(request,receipt));
});
test('runtime projection resources use their own lineage and the exact four WEBs',()=>{
  const {request}=fixture(),inventory={schema:'t1789_native_runtime_inventory_v1',runtime_base_commit:source,
    files:request.parents.filter(r=>r.file.includes('/web/')).map(r=>({...r,file:r.file.replace('assets/humans/','data/humans/')}))};
  assert.equal(validateRuntimeInventory(request,inventory).size,4);
  for(const mutate of [x=>x.runtime_base_commit=definition,x=>x.files[0].sha256='d'.repeat(64),
    x=>x.files.push({...x.files[0]}),x=>x.files.push({file:'../escape',sha256:sha,bytes:1})]){
    const bad=structuredClone(inventory);mutate(bad);assert.throws(()=>validateRuntimeInventory(request,bad));
  }
});
test('finite real clip schedule and budgets refuse invented poses or extra work',()=>{
  assert.equal(POSES.filter(p=>p.clip==='walk').length,8);for(const pose of POSES)validatePose(pose);
  for(const pose of [{clip:'walk',phase:1},{clip:'walk',phase:NaN},{clip:'sit_drive',phase:0},{clip:'turn',phase:0}])assert.throws(()=>validatePose(pose));
  assert.equal(checkBudget({triangles:4096,matrices:256}).maximum_triangle_tests,LIMITS.rayTrianglePairs);
  for(const args of [{triangles:4097},{triangles:1,rays:64},{triangles:1,matrices:257}])assert.throws(()=>checkBudget(args));
});
test('paired before cameras require complete matching poses, dimensions and observer source',()=>{
  const {request}=fixture();request.role='after';
  const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
  const before={schema:'t1789_settler_native_seat_observation_v1',status:'NATIVE_OBSERVATION_NONPASS',
    request:{...request,role:'before'},native_fit_accepted:false,
    runs:[['desktop',1280,800],['mobile',390,780]].map(([viewport_name,width,height])=>({
      file:'assets/humans/web/settler_1812.lod0.glb',viewport_name,viewport:{width,height},complete:true,
      poses:POSES.map(pose=>({pose})),screenshots:POSES.flatMap(pose=>captureViews(pose).map(camera=>({
        ...camera,actual_pose:pose,camera_world:identity,camera_projection:identity})))}))};
  assert.equal(before.runs[0].screenshots.length,13);assert.equal(validateBeforeObservation(request,before,[0]),before);
  for(const mutate of [r=>r.runs[0].screenshots.pop(),r=>r.runs[0].viewport.width=390,
    r=>r.runs[0].poses[0]=r.runs[0].poses[1],r=>r.runs[0].screenshots[0].camera_world[0]=NaN,
    r=>r.request.observer_files=[]]){
    const bad=structuredClone(before);mutate(bad);assert.throws(()=>validateBeforeObservation(request,bad,[0]));
  }
});
test('signed posterior gaps distinguish outer cloth, breakthrough and missing cover',()=>{
  assert.equal(signedRearGap([{distance:.06}],[{distance:.04}]).posterior_ray_gap_m,.06-.04);
  assert.equal(signedRearGap([{distance:.04}],[{distance:.06}]).sampled_breakthrough,true);
  assert.equal(signedRearGap([{distance:.04}],[]).body_without_garment,true);
  assert.equal(signedRearGap([],[]).posterior_ray_gap_m,null);
  assert.throws(()=>signedRearGap([{distance:Infinity}],[]));
});

const T=await import(process.env.C4D_SEAT_TEST_THREE_MODULE??new URL('../renderers/web/vendor/three-0.185.1/three.module.js',import.meta.url));
function syntheticNative(garmentZ=-.04,wrongRole=false,bodyOutsideSeat=false){
  const root=new T.Group(),pelvis=new T.Bone();pelvis.name='pelvis';pelvis.position.y=.95;root.add(pelvis);
  const skeleton=new T.Skeleton([pelvis]);root.updateMatrixWorld(true);skeleton.calculateInverses();
  function plane(z,name){
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute([-.2,0,z,.2,0,z,.2,1.75,z,-.2,1.75,z],3));
    geometry.setIndex([0,1,2,0,2,3]);geometry.setAttribute('skinIndex',new T.Uint16BufferAttribute(new Uint16Array(16),4));
    geometry.setAttribute('skinWeight',new T.Float32BufferAttribute([1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],4));
    const material=new T.MeshBasicMaterial();material.name=name;const mesh=new T.SkinnedMesh(geometry,material);mesh.name=name;
    root.add(mesh);root.updateMatrixWorld(true);mesh.bind(skeleton,new T.Matrix4());return mesh;
  }
  const skin=[plane(-.02,'skin'),plane(garmentZ,wrongRole?'garment_upper__other':'garment_lower__trousers_linen_1810')];
  if(bodyOutsideSeat){const p=skin[0].geometry.attributes.position;for(let i=0;i<p.count;i++)p.setY(i,1.5+p.getY(i)*.1);p.needsUpdate=true;}
  const update=()=>{root.updateMatrixWorld(true);skeleton.update();};
  const state=()=>({root,skin,frame:{min:[-.2,0,-.04],max:[.2,1.75,0]},header:{scenes:[{extras:{chicago4d_human:{asset_id:ASSET}}}]},
    rest(){pelvis.rotation.set(0,0,0);update();},update,
    setClip(name,phase){pelvis.rotation.x=name==='walk'&&phase===.25?.1:0;update();}});
  update();return {observer:nativeSeatObserver(T,state),dispose(){for(const m of skin){m.geometry.dispose();m.material.dispose();}}};
}
test('actual native Three CPU skin/raycast controls keep DoubleSide posterior gap under rigid pose',async()=>{
  const fixture=syntheticNative();try{
    await fixture.observer.prepare();const standing=await fixture.observer.measure({clip:'idle',phase:0});
    const walking=await fixture.observer.measure({clip:'walk',phase:.25});
    for(const row of [standing,walking]){
      assert.equal(row.body_hit_count,63);assert.equal(row.sampled_negative_gap_count,0);
      assert.ok(Math.abs(row.minimum_sampled_posterior_ray_gap_m-.02)<1e-7);
      assert.equal(row.native_fit_accepted,false);assert.match(row.matrix.float64_le_sha256,/^[a-f0-9]{64}$/);
    }
  }finally{fixture.dispose();}
});
test('native Three synthetic breakthrough is reported, never promoted to garment fit',async()=>{
  const fixture=syntheticNative(0);try{await fixture.observer.prepare();const row=await fixture.observer.measure({clip:'idle',phase:0});
    assert.equal(row.sampled_negative_gap_count,63);assert.ok(row.minimum_sampled_posterior_ray_gap_m<-.019);assert.equal(row.native_fit_accepted,false);
  }finally{fixture.dispose();}
});
test('wrong actual native material role is refused',async()=>{
  const fixture=syntheticNative(-.04,true);try{await assert.rejects(()=>fixture.observer.prepare(),/material role absent/);}finally{fixture.dispose();}
});
test('coarse triangles crossing the seat do not turn the close-up into a whole-body frame',async()=>{
  const fixture=syntheticNative();try{
    await fixture.observer.prepare();const points=fixture.observer.points(),ys=[];
    for(let i=1;i<points.length;i+=3)ys.push(points[i]);
    assert.ok(ys.length>0);assert.ok(Math.max(...ys)-Math.min(...ys)<.30);
  }finally{fixture.dispose();}
});

test('omitted posterior skin is unavailable diagnostic evidence, never model failure or fit approval',async()=>{
  const fixture=syntheticNative(-.04,false,true);try{
    const prepared=await fixture.observer.prepare();assert.equal(prepared.selected_triangles.body,0);
    const row=await fixture.observer.measure({clip:'idle',phase:0});
    assert.equal(row.diagnostic_execution_complete,true);assert.equal(row.paired_body_surface_available,false);
    assert.equal(row.diagnostic_status,'UNAVAILABLE_NO_POSTERIOR_BODY_HITS');
    assert.equal(row.body_hit_count,0);assert.equal(row.minimum_sampled_posterior_ray_gap_m,null);
    assert.equal(row.sampled_negative_gap_count,0);assert.equal(row.native_fit_accepted,false);
    assert.ok(fixture.observer.points().length>0);
  }finally{fixture.dispose();}
});

test('opt-in readiness waits for delayed helper attachment while legacy readiness stays unchanged',async()=>{
  const api={ready:true};assert.equal(inspectorReady({seatMode:false,api}),true);
  assert.equal(inspectorReady({seatMode:true,api}),false);
  await Promise.resolve();api.prepareSeatReview=()=>{};
  assert.equal(inspectorReady({seatMode:true,api}),false);
  await Promise.resolve();api.measureSeatReview=()=>{};
  assert.equal(inspectorReady({seatMode:true,api}),false);
  await Promise.resolve();api.seatView=true;
  assert.equal(inspectorReady({seatMode:true,api}),false);
  api.seatView=()=>{};assert.equal(inspectorReady({seatMode:true,api}),true);
  api.ready=false;assert.equal(inspectorReady({seatMode:true,api}),false);
  assert.equal(inspectorReady({seatMode:false,api}),false);
});
