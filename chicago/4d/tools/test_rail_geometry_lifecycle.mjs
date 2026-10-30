import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
if(process.argv.slice(2).some(v=>v!=='--self-test'))throw Error('Only --self-test is supported');
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url)).replace(/\/$/,''),base=await fs.readFile(`${root}/renderers/web/js/railway.js`,'utf8'),proposed=base;
const THREE=await import(pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href);
const {compactStreams}=await import(pathToFileURL(`${root}/renderers/web/js/compact-streams.js`).href);
const {compactNormals}=compactStreams(THREE);
const producer=s=>s.slice(s.indexOf('function railProfile('),s.indexOf('/* -------------------------------------------------------------------------- */\n/* the layer'));
// Geometry fixture below pins the output; lifecycle functions are the actual producer.
const producerWith=pack=>Function('THREE','compactNormals','GROUND','STEEL','RUST','HEAD_SIDE','wx','wz',producer(base)+';return {railProfile,laySection,railMesh};')(THREE,pack,{bed:{lift:.024}},new THREE.Color(0xa3a4a6),new THREE.Color(0x4f3527),new THREE.Color(0x6b5546),e=>e,n=>-n);
const funcs=producerWith(compactNormals),legacy=producerWith(src=>new THREE.Float32BufferAttribute(src,3));
const tieHelpers=base.slice(base.indexOf('const TIE_MATRIX_LANES ='),base.indexOf('function railMesh('));
const tieFunctions=Function('THREE',tieHelpers+';return {packTieCache,installTieCache};')(THREE);
const trackCode=base.slice(base.indexOf('function trackPath('),base.indexOf('/* -------------------------------------------------------------------------- */\n/* draped ribbons'));
const trackPath=Function(trackCode+';return trackPath;')();
const spec={gauge_m:1.435,rail:{base_m:.125,base_depth_m:.018,web_m:.013,head_width_m:.065,height_m:.145,head_depth_m:.034},ties:{exposed_m:.025}};
const paths=[trackPath([[0,0],[1,-90],[-4,-220]],{surfaceHeight:(e,n)=>Math.sin(n/70)*.3}),trackPath([[3,0],[4,-100],[2,-230]],{surfaceHeight:(e,n)=>Math.cos(n/60)*.2})];
const profNear=funcs.railProfile(spec.rail,true),profFar=funcs.railProfile(spec.rail,false),mat=new THREE.MeshStandardMaterial();
const headers=proposed.slice(proposed.indexOf('  const nearRails = (z) => {'),proposed.indexOf('  /* ---- level and reach ---- */'));
// T-3247: the far ground's per-piece update sits just before `out.update` and goes with it.
const update=proposed.slice(proposed.indexOf('  /** T-3247: a piece shown or hidden'),proposed.indexOf('  /* ---- what a pick answers ---- */'));
const dispose=proposed.slice(proposed.indexOf('  out.dispose = () => {'),proposed.indexOf('  group.userData.census = out.census;'));
const reach={full:{near:130,ties:650,tufts:240,rocks:110},balanced:{near:100,ties:480,tufts:170,rocks:85},light:{near:60,ties:220,tufts:100,rocks:50}};
const releaseSource=await fs.readFile(`${root}/renderers/web/js/upload-release.js`,'utf8');
const release=await import('data:text/javascript;base64,'+Buffer.from(releaseSource.replace("import * as THREE from 'three';",`import * as THREE from '${pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href}';`).replace("import { isSharedImage, retireSharedImage } from './shared-images.js';",'const isSharedImage=()=>false,retireSharedImage=()=>{};')).toString('base64'));
function make(){const group=new THREE.Group();group.name='railway';let marks=0;const zone={index:0,nHi:0,nLo:-110,centre:new THREE.Vector3(0,0,55),level:.5,sections:[[0,0,70],[1,10,100]]};const zones=[zone];const out=Function('installTieCache','THREE','group','paths','profNear','profFar','spec','railMat','onGeometry','laySection','railMesh','zones','REACH',`const out={census:{nearZones:0}},ZONE_M=110;let level='light';const capPile=null,pileSpots=[],groundPairs=[],geometries=[],materials=[],maps=new Map();${headers}${update}${dispose}return {...out,zone:zones[0],farRails,dropFarRails,nearRails,dropNearRails,setLevel:(v)=>{level=v;}};`)(tieFunctions.installTieCache,THREE,group,paths,profNear,profFar,spec,mat,g=>{marks++;release.releaseAfterUpload(g);},funcs.laySection,funcs.railMesh,zones,reach);return{...out,group,get marks(){return marks;}};}
const hashMesh=m=>createHash('sha256').update(Buffer.concat([...Object.entries(m.geometry.attributes).map(([k,a])=>Buffer.concat([Buffer.from(k),Buffer.from(a.array.buffer,a.array.byteOffset,a.array.byteLength)])),Buffer.from(m.geometry.index.array.buffer,m.geometry.index.array.byteOffset,m.geometry.index.array.byteLength)])).digest('hex');
function eager(implementation=funcs){const b={pos:[],nrm:[],col:[],idx:[]};for(const[i,s0,s1]of [[0,0,70],[1,10,100]])funcs.laySection(paths[i],s0,s1,profFar,spec,b);return implementation.railMesh('railway-rails-far-z0',b,.5,mat,false);}
const expected=eager(),expectedHash=hashMesh(expected),legacyExpected=eager(legacy);
// The immutable float-layout golden still protects every original producer stream.
assert.equal(hashMesh(legacyExpected),'87c4ce9d4ed5fa06e903dcef68b2b162c35aeca4fa783499b207450c61f3edfb');let checks=1;
assert.deepEqual(Object.keys(expected.geometry.attributes),Object.keys(legacyExpected.geometry.attributes));checks++;
for(const[name,a]of Object.entries(expected.geometry.attributes))if(name!=='normal'){
 const b=legacyExpected.geometry.getAttribute(name);assert.equal(a.itemSize,b.itemSize);assert.equal(a.normalized,b.normalized);assert.deepEqual(a.array,b.array);checks+=3;
}
assert.deepEqual(expected.geometry.index.array,legacyExpected.geometry.index.array);checks++;
for(const key of ['name','material','castShadow','receiveShadow']){assert.equal(expected[key],legacyExpected[key]);checks++;}
function normalPrecision(original,packed){
 assert.ok(packed.array instanceof Int8Array);assert.equal(packed.itemSize,4);assert.equal(packed.normalized,true);assert.equal(packed.count,original.count);
 let maxComponentError=0,maxAngleDeg=0;
 for(let i=0;i<original.count;i++){
  assert.equal(packed.array[i*4+3],0);const a=[original.getX(i),original.getY(i),original.getZ(i)],b=[packed.getX(i),packed.getY(i),packed.getZ(i)];
  for(let j=0;j<3;j++)maxComponentError=Math.max(maxComponentError,Math.abs(a[j]-b[j]));
  const al=Math.hypot(...a),bl=Math.hypot(...b);if(al>0&&bl>0)maxAngleDeg=Math.max(maxAngleDeg,Math.acos(Math.max(-1,Math.min(1,a.reduce((v,x,j)=>v+x*b[j],0)/al/bl)))*180/Math.PI);
 }
 assert.ok(maxComponentError<=1/254+1e-6);assert.ok(maxAngleDeg<1);return{maxComponentError,maxAngleDeg};
}
const oldNormal=legacyExpected.geometry.getAttribute('normal'),packedNormal=expected.geometry.getAttribute('normal'),precision=normalPrecision(oldNormal,packedNormal);checks++;
assert.throws(()=>normalPrecision(oldNormal,compactNormals(Array(oldNormal.count*3).fill(1))));checks++;
assert.notEqual(expectedHash,hashMesh(legacyExpected));checks++;
assert.equal(expectedHash,'d846925237edd1a8a22d7549b09eac324d90d886213235077ea9be06c1214a99');checks++;
console.log(JSON.stringify({legacyFloatGeometrySHA256:hashMesh(legacyExpected),packedGeometrySHA256:expectedHash,normalBytesSaved:oldNormal.array.byteLength-packedNormal.array.byteLength,...precision,allOtherStreamsAndMetadataExact:true,wrongNormalControlRejected:true}));
const eye=n=>({position:new THREE.Vector3(0,1,-n)});
{
 const f=make();assert.equal(f.group.children.length,0);assert.equal(f.marks,0);checks+=2;
 f.update(eye(-300));assert.ok(f.zone.railsFar.visible);assert.equal(hashMesh(f.zone.railsFar),expectedHash);assert.equal(f.zone.railsFar.material,mat);assert.equal(f.marks,1);checks+=4;
 const first=f.zone.railsFar;let disposed=0;first.geometry.addEventListener('dispose',()=>disposed++);
 f.update(eye(-310));assert.equal(f.zone.railsFar,first);assert.equal(f.marks,1);checks+=2;
 f.update(eye(-340));assert.equal(f.zone.railsFar,first);assert.equal(first.visible,false);assert.equal(disposed,0);checks+=3;
 f.update(eye(-450));assert.equal(f.zone.railsFar,null);assert.equal(first.parent,null);assert.equal(disposed,1);assert.equal(f.group.children.length,0);checks+=4;
 f.update(eye(-300));assert.notEqual(f.zone.railsFar,first);assert.equal(hashMesh(f.zone.railsFar),expectedHash);assert.equal(f.marks,2);checks+=3;
 const second=f.zone.railsFar;for(const a of [...Object.values(second.geometry.attributes),second.geometry.index]){assert.ok(a.userData.uploadReleased);a.onUploadCallback.call(a);assert.ok(a.array===null||a.array.length===0);checks+=2;}
 assert.doesNotThrow(()=>f.update(eye(-310)));checks++;
 f.update(eye(-450));f.update(eye(-300));assert.equal(hashMesh(f.zone.railsFar),expectedHash);checks++;
 f.dispose();assert.equal(f.zone.railsFar,null);assert.equal(f.zone.railsNear,undefined);assert.equal(f.group.children.length,0);checks+=3;
}
{
 const f=make();f.update(eye(-50));assert.ok(f.zone.railsNear.visible);assert.equal(f.zone.railsFar,undefined);assert.equal(f.marks,1);checks+=3;
 for(const level of ['full','balanced','light'])for(const n of [-50,-170,-209.999,-210,-329.999,-330,-340,-700,-300,-50]){f.setLevel(level);f.update(eye(n));const d=n<-110?-110-n:n>0?n:0,near=d<reach[level].near,far=!near&&d<reach[level].ties;assert.equal(!!f.zone.railsNear?.visible,near);assert.equal(!!f.zone.railsFar?.visible,far);checks+=2;}
 f.dispose();assert.equal(f.group.children.length,0);assert.equal(f.zone.railsNear,null);assert.equal(f.zone.railsFar,null);checks+=3;
}
assert.ok(!proposed.includes('z0.railFar'));assert.ok(!proposed.includes('geometries.push(z.railsFar.geometry)'));checks+=2;
const main=await fs.readFile(`${root}/renderers/web/js/main.js`,'utf8');assert.ok(main.includes('onGeometry: coarse ? (group) => releaseAfterUpload(group) : undefined'));checks++;
console.log(JSON.stringify({geometrySHA256:expectedHash,fixtureFarBytes:[...Object.values(expected.geometry.attributes),expected.geometry.index].reduce((s,a)=>s+a.array.byteLength,0),goldenFixtureGeometryByteExact:true,nearFarVisibilityAcrossTiers:true,dropRebuildGeometryByteExact:true,markedBeforeDraw:true,noDisposedReferenceInGroup:true}));

// T-3262: final Float32 tie payloads are cached until their existing reach.
// The oracle is the exact former eager producer block, not a new approximation.
const eagerTieSource = "    if (z.ties.length) {\n      const near = new THREE.InstancedMesh(tieGeoNear, tieMat, z.ties.length);\n      const far = new THREE.InstancedMesh(tieGeoFar, tieMat, z.ties.length);\n      z.ties.forEach((t, k) => {\n        q.setFromAxisAngle(up, t.yaw + Math.PI / 2);\n        m4.compose(v3.set(wx(t.e), t.y, wz(t.n)), q, s3.set(t.length, tieDepth, ties.width_m));\n        near.setMatrixAt(k, m4);\n        c.setRGB(t.tone, t.tone * (0.97 + 0.05 * t.warm), t.tone * (0.92 + 0.06 * t.warm));\n        near.setColorAt(k, c);\n      });\n      far.instanceMatrix = near.instanceMatrix;\n      far.instanceColor = near.instanceColor;\n      near.computeBoundingSphere(); far.boundingSphere = near.boundingSphere;\n      near.name = `railway-ties-z${zi}`; far.name = `railway-ties-far-z${zi}`;\n      near.castShadow = false; far.castShadow = false; near.receiveShadow = true; far.receiveShadow = true;\n      group.add(near, far);\n      z.tiesNear = near; z.tiesFar = far;\n      out.census.ties += z.ties.length;\n    }\n";
const lazyTieSource = base.slice(base.indexOf('    if (z.ties.length) {'), base.indexOf('    z.ties = null;', base.indexOf('    if (z.ties.length) {')));
const nearTieGeo = new THREE.BoxGeometry(1,1,1), farTieGeo = new THREE.PlaneGeometry(1,1);
farTieGeo.rotateX(-Math.PI/2);
const tieMat = new THREE.MeshStandardMaterial();
const tieRecords = [
 {e:2.1,n:-50,y:1.3,yaw:-Math.PI/2+.03,length:2.44,tone:.89,warm:.12},
 {e:-0,n:-90,y:-0,yaw:-Math.PI/2-.06,length:2.51,tone:1.12,warm:.98},
 {e:7,n:-70,y:.04,yaw:.91,length:2.36,tone:.78,warm:.45},
];
function tiePair(source, records=tieRecords) {
 const z={ties:records},group=new THREE.Group(),out={census:{ties:0}};
 const marker=new THREE.Object3D();
 Function('THREE','packTieCache','z','group','out','zi','tieGeoNear','tieGeoFar','tieMat','tieDepth','ties','wx','wz',
  `const m4=new THREE.Matrix4(),q=new THREE.Quaternion(),up=new THREE.Vector3(0,1,0),v3=new THREE.Vector3(),s3=new THREE.Vector3(),c=new THREE.Color();${source}`)(
  THREE,tieFunctions.packTieCache,z,group,out,0,nearTieGeo,farTieGeo,tieMat,.12,{width_m:.229},e=>e,n=>-n);
 const after=new THREE.Object3D();
 assert.equal(after.id-marker.id,3,'Only original near/far Object3D ids are reserved');checks++;
 return {z,group,out};
}
const byteView=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength);
function sameTiePair(eager,lazy) {
 for(const key of ['tiesNear','tiesFar']) {
  const a=eager.z[key],b=lazy.z[key];
  assert.equal(b.count,a.count);assert.equal(b.name,a.name);assert.equal(b.material,a.material);assert.equal(b.geometry,a.geometry);
  assert.equal(b.castShadow,a.castShadow);assert.equal(b.receiveShadow,a.receiveShadow);
  assert.deepEqual(byteView(b.instanceMatrix.array),byteView(a.instanceMatrix.array));
  assert.deepEqual(byteView(b.instanceColor.array),byteView(a.instanceColor.array));
  assert.deepEqual(b.boundingSphere.center.toArray(),a.boundingSphere.center.toArray());assert.equal(b.boundingSphere.radius,a.boundingSphere.radius);checks+=10;
  if(a.boundingBox===null){assert.equal(b.boundingBox,null);checks++;}
  else{assert.deepEqual(b.boundingBox.min.toArray(),a.boundingBox.min.toArray());assert.deepEqual(b.boundingBox.max.toArray(),a.boundingBox.max.toArray());checks+=2;}
 }
 assert.equal(lazy.z.tiesFar.instanceMatrix,lazy.z.tiesNear.instanceMatrix);
 assert.equal(lazy.z.tiesFar.instanceColor,lazy.z.tiesNear.instanceColor);
 assert.equal(lazy.z.tiesFar.boundingSphere,lazy.z.tiesNear.boundingSphere);checks+=3;
}
{
 const eager=tiePair(eagerTieSource),lazy=tiePair(lazyTieSource);
 assert.equal(eager.out.census.ties,lazy.out.census.ties);assert.deepEqual(lazy.group.children.map(o=>o.name),eager.group.children.map(o=>o.name));
 assert.equal(lazy.z.tiesNear.count,0);assert.equal(lazy.z.tiesFar.count,0);assert.equal(lazy.z.tiesNear.instanceMatrix.array.byteLength,0);assert.equal(lazy.z.tiesNear.instanceColor.array.byteLength,0);
 assert.equal(lazy.z.tiesNear.boundingSphere,null);assert.equal(lazy.z.tieCache.stride,11);assert.equal(lazy.z.tieCache.values.byteLength,tieRecords.length*44);checks+=9;
 // An external bounds visitor can cache the inactive shells' empty boxes.
 for(const key of ['tiesNear','tiesFar']) {lazy.z[key].computeBoundingBox();assert.equal(lazy.z[key].boundingBox.isEmpty(),true);eager.z[key].computeBoundingBox();checks++;}
 tieFunctions.installTieCache(lazy.z.tiesNear,lazy.z.tiesFar,lazy.z.tieCache);lazy.z.tieCache=null;sameTiePair(eager,lazy);
 // Full records are copied exactly for a future tilt, negative zero, or mixed layout.
 const final=new Float32Array(tieRecords.length*19);
 for(let i=0;i<tieRecords.length;i++){final.set(eager.z.tiesNear.instanceMatrix.array.subarray(i*16,i*16+16),i*19);final.set(eager.z.tiesNear.instanceColor.array.subarray(i*3,i*3+3),i*19+16);}
 for(const value of [.125,-0]) {
  const bad=final.slice();bad[19+1]=value;const cache=tieFunctions.packTieCache(bad);assert.equal(cache.stride,19);assert.equal(cache.values,bad);assert.equal(cache.values.byteLength,tieRecords.length*76);
  const pair=tiePair(lazyTieSource);tieFunctions.installTieCache(pair.z.tiesNear,pair.z.tiesFar,cache);
  for(let i=0;i<tieRecords.length;i++){assert.deepEqual(byteView(pair.z.tiesNear.instanceMatrix.array.subarray(i*16,i*16+16)),byteView(bad.subarray(i*19,i*19+16)));assert.deepEqual(byteView(pair.z.tiesNear.instanceColor.array.subarray(i*3,i*3+3)),byteView(bad.subarray(i*19+16,i*19+19)));checks+=2;}
  assert.equal(Object.is(pair.z.tiesNear.instanceMatrix.array[16+1],value),true);checks+=4;
 }
 assert.throws(()=>tieFunctions.packTieCache(new Float32Array(20)));checks++;
}
{
 const expected=tiePair(eagerTieSource),lazy=tiePair(lazyTieSource),f=make();
 f.group.add(...lazy.group.children.slice());Object.assign(f.zone,{tiesNear:lazy.z.tiesNear,tiesFar:lazy.z.tiesFar,tieCache:lazy.z.tieCache});
 f.update(eye(-700));assert.equal(f.zone.tiesNear.count,0);assert.ok(f.zone.tieCache);assert.equal(f.zone.tiesNear.visible,false);assert.equal(f.zone.tiesFar.visible,false);checks+=4;
 f.update(eye(-300));assert.equal(f.zone.tieCache,null);sameTiePair(expected,{z:f.zone});assert.equal(f.zone.tiesFar.visible,true);checks+=2;
 const matrix=f.zone.tiesNear.instanceMatrix,color=f.zone.tiesNear.instanceColor;
 for(const level of ['full','balanced','light'])for(const n of [-50,-169.999,-170,-209.999,-210,-329.999,-330,-589.999,-590,-759.999,-760,-900,-300,-50]) {
  f.setLevel(level);f.update(eye(n));const d=n<-110?-110-n:n>0?n:0;
  assert.equal(f.zone.tiesNear.visible,d<reach[level].near);assert.equal(f.zone.tiesFar.visible,!(d<reach[level].near)&&d<reach[level].ties);assert.equal(f.zone.tiesNear.instanceMatrix,matrix);assert.equal(f.zone.tiesNear.instanceColor,color);assert.equal(f.zone.tieCache,null);checks+=5;
 }
 let disposed=0;for(const m of [f.zone.tiesNear,f.zone.tiesFar])m.addEventListener('dispose',()=>disposed++);
 f.dispose();assert.equal(disposed,2);assert.equal(f.zone.tieCache,null);checks+=2;
}
{
 const lazy=tiePair(lazyTieSource),f=make();f.group.add(...lazy.group.children.slice());Object.assign(f.zone,{tiesNear:lazy.z.tiesNear,tiesFar:lazy.z.tiesFar,tieCache:lazy.z.tieCache});
 let disposed=0;for(const m of [f.zone.tiesNear,f.zone.tiesFar])m.addEventListener('dispose',()=>disposed++);
 f.dispose();assert.equal(disposed,2);assert.equal(f.zone.tieCache,null);assert.equal(f.zone.tiesNear.count,0);checks+=3;
}
console.log(JSON.stringify({tieCacheCanonicalBytesPerTie:44,tieCacheFallbackBytesPerTie:76,finalMatrixAndColorBytesExact:true,originalObject3DIdSlotsAndNamesMaterialChildOrderPreserved:true,unreachedCountZeroShells:true,actualTierReachInstallationOnce:true,cacheDroppedOnFirstReachAndDisposal:true,mixedTiltAndNegativeZeroFallbackExact:true,CPUAllocationOnlyNoGpuSavingClaim:true,browserUploadPixelsAndOfficialMeterStillRequired:true}));

console.log(`PASS ${checks} bounded actual-producer geometry/lifecycle/upload-mark/visibility checks. Browser memory, pixels, complete walk and timing still required.`);
