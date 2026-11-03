#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
// Actual authored GLBs and vendored Three selection/batching/picking/disposal.
// Network is replaced with local reads; synthetic flat ground is NOT world proof.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';
const vendor = new URL('../../../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const T = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { createParkedTransport } = await import('../../../renderers/web/js/parked-transport.js');
const record = JSON.parse(fs.readFileSync(new URL('../../../data/transport/parked/placements.json', import.meta.url)));
const obsoleteC02=JSON.parse(fs.readFileSync(new URL('./obsolete-c02-placement.json',import.meta.url)));
let compatibilityRecord=null;
const load = GLTFLoader.prototype.loadAsync, parseAsyncBefore=GLTFLoader.prototype.parseAsync, fetchBefore = globalThis.fetch;
const selfBefore=globalThis.self, bitmapBefore=globalThis.createImageBitmap;
// Unchanged legacy C02 embeds images. Its pixel decoding is outside this geometry
// test; the original image/texture objects still follow normal ownership/disposal.
globalThis.self=globalThis;globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
const requests = [], legacyRequests=[], parseBases=[], managerEvents=[], sourceDisposals = [], sourceMaterials = [], assertions = [];
const manager=T.DefaultLoadingManager, managerBefore={itemStart:manager.itemStart,itemEnd:manager.itemEnd,itemError:manager.itemError};
for(const name of ['itemStart','itemEnd','itemError'])manager[name]=function(url){if(String(url).includes('/parked-brougham/'))managerEvents.push({name,url:String(url)});return managerBefore[name].call(this,url)};
let rejectMid = false, rejectNear=false, holdMid = false, releaseMid, midStarted;
const need = (value, label) => { assert(value, label); assertions.push(label); };
const count = root => { let n=0;root.traverse(m=>{if(m.isMesh)n+=(m.geometry.index?.count??m.geometry.attributes.position.count)/3});return n; };
function observe(asset) {
 const geos=new Set(),mats=new Set();asset.scene.traverse(n=>{if(n.geometry)geos.add(n.geometry);if(n.material)mats.add(n.material)});
 for(const g of geos){const row={count:0};g.addEventListener('dispose',()=>row.count++);sourceDisposals.push(row)}
 for(const m of mats){const row={count:0};m.addEventListener('dispose',()=>row.count++);sourceMaterials.push(row)}
 return asset;
}
GLTFLoader.prototype.parseAsync = async function(bytes,base) {parseBases.push(base);return observe(await parseAsyncBefore.call(this,bytes,base))};
GLTFLoader.prototype.loadAsync = async function(url) {
 legacyRequests.push(String(url));requests.push(String(url));
 const bytes=fs.readFileSync(new URL(url));
 return observe(await new Promise((resolve,reject)=>this.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),new URL('.',url).href,resolve,reject)));
};
globalThis.fetch=async(url,options={})=>{
 const u=new URL(url);
 if(u.protocol!=='file:')return fetchBefore(url,options);
 if(u.pathname.endsWith('/brougham-near-delivery-v1.glb')||u.pathname.endsWith('/brougham-mid-delivery-v1.glb')){
  requests.push(String(url));assert(options.signal===manager.abortController.signal,'Use actual manager cancellation signal');assert(options.credentials==='same-origin','Keep original same-origin credentials');
  if(rejectNear&&u.pathname.endsWith('/brougham-near-delivery-v1.glb'))return new Response('Controlled missing near',{status:404});
  if(rejectMid&&u.pathname.endsWith('/brougham-mid-delivery-v1.glb'))return new Response('Controlled missing mid',{status:503});
  if(holdMid&&u.pathname.endsWith('/brougham-mid-delivery-v1.glb'))await new Promise((resolve,reject)=>{releaseMid=resolve;midStarted();options.signal.addEventListener('abort',()=>reject(options.signal.reason),{once:true})});
  if(options.signal.aborted)throw options.signal.reason;
  return new Response(fs.readFileSync(u),{status:200,headers:{'Content-Type':'model/gltf-binary'}});
 }
 return{ok:true,json:async()=>compatibilityRecord&&u.pathname.endsWith('/transport/parked/placements.json')?structuredClone(compatibilityRecord):JSON.parse(fs.readFileSync(u))};
};
const problems=[],patched=new Set(),hidden={reconstructed:false};
let height=800;
const options={dataBase:new URL('../../../data/',import.meta.url),sceneId:'1904',terrain:{surfaceHeight:()=>0},groundHeight:()=>0,
 confidence:{hidden,patch:m=>patched.add(m)},problems,getDrawingBufferHeight:()=>height};
const camera=new T.PerspectiveCamera(55,1.6,0.1,5000);
const objects=[];
const dispose=async out=>{out.dispose();await Promise.resolve();await Promise.resolve()};
try {
 // Actual installed scene owns one Brougham and no obsolete prototype; preserve
 // all legacy loader assertions in a separate explicit compatibility fixture.
 need(record.scenes['1835'].length===5&&record.scenes['1904'].length===1,'Installed scene keeps five1835wagons and one1904carriage');
 need(!record.scenes['1904'].some(r=>r.id==='prairie_parked_carriage')&&record.models.carriage_c02.file==='transport/parked-carriage/carriage-c02.glb','Obsolete display removed while legacy C02 model remains');
 const installed=await createParkedTransport(options);objects.push(installed);
 need(installed.instances.length===1&&installed.instances[0].row.id==='prairie_parked_studebaker_brougham','Actual installed1904adapter loads only the replacement Brougham');
 need(JSON.stringify(installed.instances[0].row.at_local_enu_m)==='[1397.9,-3240]'&&installed.instances[0].row.bearing_deg===178.99,'Replacement retains existing qualified stand and bearing');
 need(legacyRequests.length===0,'Removed C02 display incurs no legacy asset load in installed1904scene');
 await dispose(installed);need(sourceDisposals.every(r=>r.count===1)&&sourceMaterials.every(r=>r.count===1),'Installed replacement retires every source resource once');
 const midRequestsBeforeCompat=requests.filter(u=>u.endsWith('/brougham-mid-delivery-v1.glb')).length;
 compatibilityRecord=structuredClone(record);compatibilityRecord.scenes['1904'].push(obsoleteC02);
 const out=await createParkedTransport(options);objects.push(out);
 need(problems.length===0,'Actual near, mid and C02 load and batch without runtime problems: '+JSON.stringify(problems));
 const b=out.instances.find(i=>i.row.model==='studebaker_brougham_1893'),legacy=out.instances.find(i=>i.row.model==='carriage_c02');
 need(b?.lod?.isLOD&&b.lod.autoUpdate===false&&b.lod.levels.length===2,'Only opted-in Brougham has controlled standard THREE.LOD');
 need(legacy&&!legacy.lod&&legacy.group.children.every(n=>n.isMesh),'Legacy C02 retains its ordinary merged group');
 need(b.draw_batches===8&&b.lod.levels.every(l=>l.object.children.length===8),'Actual near and mid each merge to eight material batches');
 need(count(b.lod.levels[0].object)===45338&&count(b.lod.levels[1].object)===23062,'Actual merged indexed geometry reads back genuine near/mid triangle counts');
 for(const level of b.lod.levels){
  const glass=level.object.children.filter(mesh=>mesh.material.name==='thin_sheet_cabin_glass_delivery_reconstruction');
  need(glass.length===1,'Each actual runtime LOD retains exactly one cabin-glass material batch');
  const material=glass[0].material;
  need((material.transmission??0)===0&&material.opacity===.14&&material.transparent&&!material.depthWrite&&material.ior===1.5,
    'Actual vendored loader reads the declared alpha optical profile without a transmission pass');
 }
 need(b.lod.levels[1].hysteresis===0.05,'Standard five percent hysteresis retained');
 for(const l of b.lod.levels)l.object.traverse(m=>{if(m.isMesh){need(patched.has(m.material),'Every level uses existing confidence material patch');need(Array.from(m.geometry.attributes._confidence.array).every(v=>v===1),'Every level retains reconstructed confidence values')}});
 const pose=(distance)=>{camera.position.copy(b.group.position).add(new T.Vector3(0,0,distance));camera.lookAt(b.group.position.clone().add(new T.Vector3(0,1,0)));camera.updateMatrixWorld(true);out.update(camera);out.group.updateMatrixWorld(true)};
 const active=(label,expected)=>need(b.active_lod===expected&&b.active_triangles===(expected==='near'?45338:23062)&&b.lod.levels.filter(l=>l.object.visible).length===1,label);
 pose(23.99);active('Near retained below 24m', 'near');
 pose(24.01);active('Actual mid selected beyond24m','mid');
 pose(23.0);active('Hysteresis keeps mid while returning through boundary','mid');
 pose(22.79);active('Near restored before conversation distance','near');
 pose(3);active('Conversation distance keeps exact near model','near');
 pose(25.227878213450246);active('Historical source spawn distance selects genuine mid at800px','mid');
 height=3200;pose(25.227878213450246);active('Large drawing buffer restores near at same stand and camera','near');
 height=800;camera.zoom=2;camera.updateProjectionMatrix();pose(25.23);active('Zoom retains near through standard LOD zoom distance','near');camera.zoom=1;camera.updateProjectionMatrix();
 height=NaN;pose(30);active('Missing render-height evidence safely retains near','near');height=800;
 const saved=record.models.studebaker_brougham_1893;need(saved.delivery_lods.mid.endsWith('/brougham-mid-delivery-v1.glb')&&saved.delivery_lods.runtime_distance_selection_enabled,'Actual placements opt into exact separate mid payload');
 const activeGeometryReadback=[];
 for(const distance of [3,25]){
  pose(distance);camera.position.x=b.group.position.x+distance;camera.position.z=b.group.position.z;camera.position.y=b.group.position.y+1.25;camera.lookAt(b.group.position.clone().add(new T.Vector3(0,1.0,0)));camera.updateMatrixWorld(true);out.update(camera);out.group.updateMatrixWorld(true);
  const inactive=b.lod.levels[1-b.lod.getCurrentLevel()].object,orig=[];
  inactive.traverse(n=>{if(n.isMesh){orig.push([n,n.raycast]);n.raycast=()=>{throw Error('Inactive LOD geometry was raycast')}}});
  try{
   const hit=out.pickAt(new T.Vector2(0,0),camera);need(hit?.id===b.row.id&&hit.record===b.card,`Actual active ${b.active_lod} mesh remains pickable with unchanged card: ${hit?.id??'none'}`);
   const ray=new T.Raycaster();ray.setFromCamera(new T.Vector2(0,0),camera);
   assert.throws(()=>ray.intersectObjects([b.group],true),/Inactive LOD geometry/);assertions.push('Negative control: default recursive LOD raycast visits hidden geometry');
   hidden.reconstructed=true;need(out.pickAt(new T.Vector2(0,0),camera)===null,'Existing reconstructed-confidence hiding suppresses picks');hidden.reconstructed=false;
  }finally{for(const[n,fn]of orig)n.raycast=fn}
  activeGeometryReadback.push({level:b.active_lod,triangles:b.active_triangles,batches:b.draw_batches});
 }
 pose(99.9);need(b.group.visible,'Full retains existing100m reach');pose(100);need(!b.group.visible,'Full hides at original100m boundary');
 await out.setTier('balanced');pose(64.9);need(b.group.visible,'Balanced retains original65m reach');pose(65);need(!b.group.visible,'Balanced hides at original65m boundary');
 const loadedCount=requests.length;await out.setTier('light');pose(3);need(out.instances.every(i=>!i.group.visible),'Light hides every authored vehicle');
 await out.setTier('full');pose(3);active('Full restores original near after Light','near');need(requests.length===loadedCount,'Tier changes reuse existing caches without another GLB load');
 const batchDisposals=[];out.group.traverse(n=>{if(n.geometry){const row={count:0};n.geometry.addEventListener('dispose',()=>row.count++);batchDisposals.push(row)}});
 await dispose(out);need(batchDisposals.every(r=>r.count===1),'Each near/mid/C02 merged buffer is disposed once');need(sourceDisposals.every(r=>r.count===1)&&sourceMaterials.every(r=>r.count===1),'Each cached source geometry and material is disposed once');
 need(!out.group.children.length&&!out.instances.length,'Disposal clears all active level ownership');
 const beforeLight=requests.length;const light=await createParkedTransport({...options,detail:'light'});objects.push(light);need(requests.length===beforeLight&&!light.instances.length,'Light boot does not fetch either Brougham level');await dispose(light);
 rejectMid=true;const failed=[];const fallback=await createParkedTransport({...options,problems:failed});objects.push(fallback);
 const retained=fallback.instances.find(i=>i.row.model==='studebaker_brougham_1893');need(retained&&!retained.lod&&count(retained.group)===45338&&failed.some(s=>s.includes('near retained')),'Actual failed mid fetch retains original near and reports failure');await dispose(fallback);rejectMid=false;
 need(requests.filter(u=>u.endsWith('/brougham-mid-delivery-v1.glb')).length===midRequestsBeforeCompat+2,'Each created transport caches its one mid request; failure control is distinct');
 // A Light boot returns its API before loading. Dispose during its actual pending
 // mid load, then let the real GLTF parse finish; no late model may be attached.
 const waiting=await createParkedTransport({...options,detail:'light',problems:[]});objects.push(waiting);
 const started=new Promise(resolve=>{midStarted=resolve});holdMid=true;
 const pending=waiting.setTier('full');await started;waiting.dispose();releaseMid();await pending;holdMid=false;
 await Promise.resolve();await Promise.resolve();
 need(!waiting.group.children.length&&!waiting.instances.length,'Disposal during pending mid load never attaches a late model');
 need(sourceDisposals.every(r=>r.count===1)&&sourceMaterials.every(r=>r.count===1),'Pending and failed-mid paths retire every cached source resource once');

 // HTTP failure is propagated through the original per-model fallback. No
 // malformed success is cached or parsed; legacy C02 still uses loadAsync.
 rejectNear=true;const missingProblems=[];const missing=await createParkedTransport({...options,problems:missingProblems});objects.push(missing);
 need(!missing.instances.some(i=>i.row.model==='studebaker_brougham_1893')&&missing.instances.some(i=>i.row.model==='carriage_c02')&&missingProblems.some(s=>s.includes('Brougham HTTP 404')),'Actual HTTP404 near failure is reported and leaves legacy C02');await dispose(missing);rejectNear=false;
 const aborted=await createParkedTransport({...options,detail:'light',problems:[]});objects.push(aborted);const abortStarted=new Promise(resolve=>{midStarted=resolve});holdMid=true;
 const abortLoad=aborted.setTier('full');await abortStarted;manager.abort();await abortLoad;holdMid=false;
 const abortRetained=aborted.instances.find(i=>i.row.model==='studebaker_brougham_1893');need(abortRetained&&!abortRetained.lod,'Actual manager abort rejects pending mid and retains existing near fallback');await dispose(aborted);
 need(legacyRequests.every(u=>!u.includes('brougham-'))&&legacyRequests.some(u=>u.endsWith('/carriage-c02.glb')),'Legacy C02 retains loadAsync and both Brougham levels use direct body read');
 need(parseBases.length>1&&parseBases.every(u=>u.endsWith('/transport/parked-brougham/')),'Actual parseAsync resolves relative resources from original asset directory');
 const starts=managerEvents.filter(e=>e.name==='itemStart'),ends=managerEvents.filter(e=>e.name==='itemEnd'),errors=managerEvents.filter(e=>e.name==='itemError');
 need(starts.length===ends.length&&starts.length===requests.filter(u=>u.includes('/parked-brougham/')).length,'Every success, HTTP failure and manager abort balances source manager start/end');
 need(errors.length===3,'Manager error accounting preserves controlled mid503, near404 and aborted-mid errors');
 need(sourceDisposals.every(r=>r.count===1)&&sourceMaterials.every(r=>r.count===1),'HTTP-failure/manager-abort paths retain exact cached source disposal');
 // T-3300: loadWithin defers each vehicle's fetch until the eye is within its
 // tier's reach plus that margin; nearer than that it loads once and is drawn.
 {
  const at=new T.Vector3(1397.9,0,3240),place=d=>{camera.position.copy(at).add(new T.Vector3(0,1.6,d));camera.lookAt(at);camera.updateMatrixWorld(true)};
  const saved=compatibilityRecord;compatibilityRecord=null;
  const before=requests.length;const deferred=await createParkedTransport({...options,loadWithin:60,problems:[]});objects.push(deferred);
  need(requests.length===before&&!deferred.instances.length&&deferred.records.length===1,'loadWithin: creation fetches no vehicle');
  place(161);deferred.update(camera);await Promise.resolve();
  need(requests.length===before&&!deferred.requested.size,'loadWithin: beyond reach plus margin fetches nothing');
  await deferred.setTier('balanced');place(126);deferred.update(camera);
  need(requests.length===before&&!deferred.requested.size,'loadWithin: Balanced measures from its own 65 m reach');
  await deferred.setTier('full');place(159);deferred.update(camera);
  need(deferred.requested.size===1&&deferred.pending===1,'loadWithin: inside reach plus margin requests the vehicle, pending until placed');
  for(let i=0;i<400&&!deferred.instances.length;i++)await new Promise(r=>setTimeout(r,5));
  for(let i=0;i<400&&deferred.pending;i++)await new Promise(r=>setTimeout(r,5));
  need(deferred.instances.length===1&&!deferred.pending&&!deferred.instances[0].group.visible,'loadWithin: the loaded vehicle stays hidden until within reach');
  const loaded=requests.length;place(50);deferred.update(camera);
  need(deferred.instances[0].group.visible&&requests.length===loaded,'loadWithin: within reach it is drawn, with no second fetch');
  await dispose(deferred);compatibilityRecord=saved;
 }
 console.log(JSON.stringify({pass:true,scope:'Actual vendored Three/GLTF optical near-mid batching, active-only picking, source-cache ownership, tier/reach/zoom/resize and disposal; synthetic flat ground is not world proof',activeGeometryReadback,parseBases,managerEvents,assertionCount:assertions.length,assertions,opticalDeliveryProfileVerified:true,geometryCountsPreserved:true,photographicAcceptance:false,actualWorldBudgetAcceptance:false},null,2));
} finally {
 for(const out of objects)if(out.instances.length)await dispose(out);
 GLTFLoader.prototype.loadAsync=load;GLTFLoader.prototype.parseAsync=parseAsyncBefore;for(const name of Object.keys(managerBefore))manager[name]=managerBefore[name];globalThis.fetch=fetchBefore;globalThis.self=selfBefore;globalThis.createImageBitmap=bitmapBefore;
}
