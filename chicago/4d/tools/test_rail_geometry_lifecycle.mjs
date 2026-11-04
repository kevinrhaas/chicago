import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
const args=process.argv.slice(2),phases=args.filter(v=>v.startsWith('--phase='));
if(args.some(v=>!['--self-test','--phase=legacy','--phase=cache-words'].includes(v))||phases.length>1)throw Error('Only --self-test and one native CPU phase are supported');
// The default still runs EVERY control. Two explicit partitions let a short CPU
// qualification keep the existing 269k producer controls and the new word codec.
const phase=phases[0]?.slice('--phase='.length);
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
const tieFunctions=Function('THREE',tieHelpers+';return {packTieCache,installTieCache,packTuftCache,installTuftCache,packRailCacheWords,unpackRailCacheWords};')(THREE);
const rngCode=base.slice(base.indexOf('function rng('),base.indexOf('\n/* ---',base.indexOf('function rng(')));
const rockHelpers=Function('THREE',rngCode+tieHelpers+';return {rng,packRockValues,packRockCache,replayRockMatrices,installRockCache};')(THREE);
const trackCode=base.slice(base.indexOf('function trackPath('),base.indexOf('/* -------------------------------------------------------------------------- */\n/* draped ribbons'));
const trackPath=Function(trackCode+';return trackPath;')();
const spec={gauge_m:1.435,rail:{base_m:.125,base_depth_m:.018,web_m:.013,head_width_m:.065,height_m:.145,head_depth_m:.034},ties:{exposed_m:.025}};
const paths=[trackPath([[0,0],[1,-90],[-4,-220]],{surfaceHeight:(e,n)=>Math.sin(n/70)*.3}),trackPath([[3,0],[4,-100],[2,-230]],{surfaceHeight:(e,n)=>Math.cos(n/60)*.2})];
const profNear=funcs.railProfile(spec.rail,true),profFar=funcs.railProfile(spec.rail,false),mat=new THREE.MeshStandardMaterial();
const headers=proposed.slice(proposed.indexOf('  const nearRails = (z) => {'),proposed.indexOf('  /* ---- level and reach ---- */'));
// T-3247: the far ground's per-piece update sits just before `out.update` and goes with it.
const update=proposed.slice(proposed.indexOf('  /** T-3247: a piece shown or hidden'),proposed.indexOf('  /* ---- what a pick answers ---- */'));
const dispose=proposed.slice(proposed.indexOf('  out.dispose = () => {'),proposed.indexOf('  group.userData.census = out.census;'));
const detailSource=proposed.slice(proposed.indexOf('  const applyDetail = () => {'),proposed.indexOf('  /** T-3247: a piece shown or hidden'));
const reach={full:{near:130,ties:650,tufts:240,rocks:110},balanced:{near:100,ties:480,tufts:170,rocks:85},light:{near:60,ties:220,tufts:100,rocks:50}};
const releaseSource=await fs.readFile(`${root}/renderers/web/js/upload-release.js`,'utf8');
const release=await import('data:text/javascript;base64,'+Buffer.from(releaseSource.replace("import * as THREE from 'three';",`import * as THREE from '${pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href}';`).replace("from './shared-images.js'",`from '${pathToFileURL(`${root}/renderers/web/js/shared-images.js`).href}'`).replace("from './batch-bounds.js'",`from 'data:text/javascript;base64,${Buffer.from((await fs.readFile(`${root}/renderers/web/js/batch-bounds.js`,'utf8')).replace("from 'three'",`from '${pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href}'`)).toString('base64')}'`)).toString('base64'));
function make(dens={full:4,balanced:2,light:1}){const group=new THREE.Group();group.name='railway';let marks=0;const zone={index:0,nHi:0,nLo:-110,centre:new THREE.Vector3(0,0,55),level:.5,sections:[[0,0,70],[1,10,100]]};const zones=[zone];const out=Function('rockShare','installRockCache','dens','installTuftCache','installTieCache','THREE','group','paths','profNear','profFar','spec','railMat','onGeometry','laySection','railMesh','zones','REACH',`const out={census:{nearZones:0}},ZONE_M=110;let level='light';const capPile=null,pileSpots=[],groundPairs=[],geometries=[],materials=[],maps=new Map();${detailSource}${headers}${update}${dispose}return {...out,zone:zones[0],farRails,dropFarRails,nearRails,dropNearRails,setLevel:(v)=>{level=v;}};`)({full:1,balanced:.6,light:.3},rockHelpers.installRockCache,dens,tieFunctions.installTuftCache,tieFunctions.installTieCache,THREE,group,paths,profNear,profFar,spec,mat,g=>{marks++;release.releaseAfterUpload(g);},funcs.laySection,funcs.railMesh,zones,reach);return{...out,group,get marks(){return marks;}};}
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
const main=await fs.readFile(`${root}/renderers/web/js/main.js`,'utf8');assert.ok(main.includes('onGeometry: (group) => releaseAfterUpload(group)'));assert.ok(!main.includes('onGeometry: coarse ? (group) => releaseAfterUpload(group) : undefined'));checks+=2;
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


// T-3262: final Float32 tuft payloads, density and first reach, with the former
// native eager producer retained as the byte oracle. Existing tie checks remain.
const eagerTuftSource="    if (tuftGeo && z.tufts.length) {\n      z.tufts.sort((a, b) => a.keep - b.keep);\n      const mesh = new THREE.InstancedMesh(tuftGeo, tuftMat, z.tufts.length);\n      z.tufts.forEach((t, k) => {\n        q.setFromAxisAngle(up, t.yaw);\n        const h = tuftLib.sheet.height_m * t.scale;\n        m4.compose(v3.set(wx(t.e), t.y, wz(t.n)), q, s3.set(h, h, h));\n        mesh.setMatrixAt(k, m4);\n        mesh.setColorAt(k, c.setRGB(t.tone, t.tone, t.tone * 0.92));\n      });\n      mesh.computeBoundingSphere();\n      mesh.name = `railway-tufts-z${zi}`;\n      mesh.castShadow = false; mesh.receiveShadow = true;\n      z.tuftKeeps = z.tufts.map((t) => t.keep);\n      z.tuftMesh = mesh;\n      group.add(mesh);\n    }\n";
const lazyTuftSource=base.slice(base.indexOf('    if (tuftGeo && z.tufts.length) {'),base.indexOf('    z.tufts = null;',base.indexOf('    if (tuftGeo && z.tufts.length) {')));
const tuftGeo=Function('THREE',base.slice(base.indexOf('function tuftGeometry('),base.indexOf('function wetTint('))+';return tuftGeometry;')(THREE)(.5);
const tuftMat=new THREE.MeshStandardMaterial(),tuftLib={sheet:{height_m:.55}};
const tuftRecords=[
 {e:2.1,n:-50,y:1.3,yaw:.2,scale:.56,keep:.05,tone:1.15},
 {e:-0,n:-90,y:-0,yaw:1.5,scale:1.29,keep:.24,tone:1.08},
 {e:7,n:-70,y:.04,yaw:2.9,scale:.87,keep:.6,tone:.8},
];
function tuftPair(source,records=tuftRecords){
 const z={tufts:records.map(r=>({...r}))},group=new THREE.Group(),marker=new THREE.Object3D();
 Function('THREE','packTuftCache','z','group','zi','tuftGeo','tuftMat','tuftLib','wx','wz',`const m4=new THREE.Matrix4(),q=new THREE.Quaternion(),up=new THREE.Vector3(0,1,0),v3=new THREE.Vector3(),s3=new THREE.Vector3(),c=new THREE.Color();${source}`)(THREE,tieFunctions.packTuftCache,z,group,0,tuftGeo,tuftMat,tuftLib,e=>e,n=>-n);
 const after=new THREE.Object3D();assert.equal(after.id-marker.id,2,'Original tuft Object3D id slot retained');checks++;return{z,group};
}
function sameTuft(eager,lazy){
 const a=eager.z.tuftMesh,b=lazy.z.tuftMesh;
 assert.equal(b.count,a.count);assert.equal(b.name,a.name);assert.equal(b.material,a.material);assert.equal(b.geometry,a.geometry);assert.equal(b.castShadow,a.castShadow);assert.equal(b.receiveShadow,a.receiveShadow);
 assert.deepEqual(byteView(b.instanceMatrix.array),byteView(a.instanceMatrix.array));assert.deepEqual(byteView(b.instanceColor.array),byteView(a.instanceColor.array));assert.deepEqual(b.boundingSphere.center.toArray(),a.boundingSphere.center.toArray());assert.equal(b.boundingSphere.radius,a.boundingSphere.radius);checks+=10;
 if(a.boundingBox===null){assert.equal(b.boundingBox,null);checks++;}else{assert.deepEqual(b.boundingBox.min.toArray(),a.boundingBox.min.toArray());assert.deepEqual(b.boundingBox.max.toArray(),a.boundingBox.max.toArray());checks+=2;}
}
{
 const eager=tuftPair(eagerTuftSource),lazy=tuftPair(lazyTuftSource);assert.equal(lazy.z.tuftMesh.count,0);assert.equal(lazy.z.tuftMesh.instanceMatrix.array.byteLength,0);assert.equal(lazy.z.tuftMesh.instanceColor.array.byteLength,0);assert.equal(lazy.z.tuftMesh.boundingSphere,null);assert.equal(lazy.z.tuftCache.stride,8);assert.equal(lazy.z.tuftCache.values.byteLength,tuftRecords.length*32);assert.deepEqual(lazy.z.tuftKeeps,eager.z.tuftKeeps);checks+=7;
 // Empty-shell boxes refresh using the actual selected prefix; sphere retains
 // the original complete built payload, as before applyDetail trimmed count.
 lazy.z.tuftMesh.computeBoundingBox();assert.equal(lazy.z.tuftMesh.boundingBox.isEmpty(),true);checks++;
 eager.z.tuftMesh.count=2;eager.z.tuftMesh.computeBoundingBox();tieFunctions.installTuftCache(lazy.z.tuftMesh,lazy.z.tuftCache,2);sameTuft(eager,lazy);
 const full=new Float32Array(tuftRecords.length*19);for(let i=0;i<tuftRecords.length;i++){full.set(eager.z.tuftMesh.instanceMatrix.array.subarray(i*16,i*16+16),i*19);full.set(eager.z.tuftMesh.instanceColor.array.subarray(i*3,i*3+3),i*19+16);}
 for(const[mutate,stride]of [[a=>{a[19+10]=.4;},11],[a=>{a[19+17]=1.07;},11],[a=>{a[19+2]=0;a[19+8]=0;},11],[a=>{a[19+1]=.125;},19],[a=>{a[19+1]=-0;},19]]){
  const bad=full.slice();mutate(bad);const cache=tieFunctions.packTuftCache(bad);assert.equal(cache.stride,stride);assert.equal(cache.values.byteLength,tuftRecords.length*stride*4);checks+=2;const pair=tuftPair(lazyTuftSource);tieFunctions.installTuftCache(pair.z.tuftMesh,cache,tuftRecords.length);
  for(let i=0;i<tuftRecords.length;i++){assert.deepEqual(byteView(pair.z.tuftMesh.instanceMatrix.array.subarray(i*16,i*16+16)),byteView(bad.subarray(i*19,i*19+16)));assert.deepEqual(byteView(pair.z.tuftMesh.instanceColor.array.subarray(i*3,i*3+3)),byteView(bad.subarray(i*19+16,i*19+19)));checks+=2;}
 }
}
function withTufts(dens={full:4,balanced:2,light:1}){const pair=tuftPair(lazyTuftSource),f=make(dens);f.group.add(...pair.group.children.slice());Object.assign(f.zone,{tuftMesh:pair.z.tuftMesh,tuftKeeps:pair.z.tuftKeeps,tuftCache:pair.z.tuftCache});return f;}
{
 const eager=tuftPair(eagerTuftSource),f=withTufts();f.setDetail('light');assert.equal(f.zone.tuftWanted,2);assert.equal(f.census.tufts,2);assert.equal(f.zone.tuftMesh.count,0);checks+=3;f.update(eye(-900));assert.ok(f.zone.tuftCache);assert.equal(f.zone.tuftMesh.visible,false);checks+=2;
 f.zone.tuftMesh.computeBoundingBox();f.update(eye(-160));assert.equal(f.zone.tuftCache,null);assert.equal(f.zone.tuftMesh.visible,true);eager.z.tuftMesh.count=2;eager.z.tuftMesh.computeBoundingBox();sameTuft(eager,{z:f.zone});checks+=2;
 const matrix=f.zone.tuftMesh.instanceMatrix,color=f.zone.tuftMesh.instanceColor;
 for(const level of ['full','balanced','light'])for(const n of [-50,-209.999,-210,-279.999,-280,-349.999,-350,-900,-160]){
  f.setDetail(level);f.update(eye(n));const d=n<-110?-110-n:n>0?n:0,wanted=tuftRecords.filter(t=>t.keep<({full:4,balanced:2,light:1}[level]/4)).length;assert.equal(f.zone.tuftMesh.count,wanted);assert.equal(f.census.tufts,wanted);assert.equal(f.zone.tuftMesh.visible,d<reach[level].tufts&&wanted>0);assert.equal(f.zone.tuftMesh.instanceMatrix,matrix);assert.equal(f.zone.tuftMesh.instanceColor,color);assert.equal(f.zone.tuftCache,null);checks+=6;
 }
 let disposed=0;f.zone.tuftMesh.addEventListener('dispose',()=>disposed++);f.dispose();assert.equal(disposed,1);assert.equal(f.zone.tuftCache,null);checks+=2;
}
for(const level of ['full','balanced','light']){
 const f=withTufts();f.setDetail(level);f.update(eye(-900));assert.equal(f.zone.tuftMesh.count,0);assert.ok(f.zone.tuftCache);checks+=2;f.update(eye(-110-reach[level].tufts+.001));assert.equal(f.zone.tuftCache,null);assert.equal(f.zone.tuftMesh.visible,true);checks+=2;f.dispose();
}
{
 const f=withTufts({full:4,balanced:2,light:0});f.setDetail('light');f.update(eye(-50));assert.equal(f.zone.tuftWanted,0);assert.equal(f.zone.tuftMesh.count,0);assert.ok(f.zone.tuftCache);assert.equal(f.zone.tuftMesh.visible,false);assert.equal(f.census.tufts,0);checks+=5;
 f.setDetail('full');assert.equal(f.zone.tuftWanted,3);assert.equal(f.zone.tuftMesh.count,0);checks+=2;f.update(eye(-50));assert.equal(f.zone.tuftCache,null);assert.equal(f.zone.tuftMesh.count,3);checks+=2;const matrix=f.zone.tuftMesh.instanceMatrix;f.setDetail('light');f.update(eye(-50));assert.equal(f.zone.tuftMesh.count,0);assert.equal(f.zone.tuftMesh.visible,false);f.setDetail('full');f.update(eye(-50));assert.equal(f.zone.tuftMesh.count,3);assert.equal(f.zone.tuftMesh.instanceMatrix,matrix);checks+=4;f.dispose();
 const pending=withTufts();let disposed=0;pending.zone.tuftMesh.addEventListener('dispose',()=>disposed++);pending.dispose();assert.equal(disposed,1);assert.equal(pending.zone.tuftCache,null);assert.equal(pending.zone.tuftMesh.count,0);checks+=3;
}
{
 const clear='  // Only grade is read by the returned path; the sampling scratch is finished.\n  raw.length = 0;\n';const oldTrack=Function(trackCode.replace(clear,'' )+';return trackPath;')();
 for(const line of [[[0,0],[1,-90],[-4,-220]],[[3,0],[4,-100],[2,-230]]]){
  const terrain={surfaceHeight:(e,n)=>Math.sin(n/70)*.3+Math.cos(e/3)*.2},a=trackPath(line,terrain),b=oldTrack(line,terrain);assert.equal(a.length,b.length);checks++;for(const s of [-3,0,.1,5,a.length*.5,a.length,a.length+4]){assert.deepEqual(a.at(s),b.at(s));checks++;}
 }
 const wrongCode=trackCode.replace('  const grade = raw.map','  raw.length = 0;\n  const grade = raw.map'),wrong=Function(wrongCode+';return trackPath;')();assert.throws(()=>assert.deepEqual(wrong([[0,0],[0,-20]],{surfaceHeight:()=>1}).at(5),trackPath([[0,0],[0,-20]],{surfaceHeight:()=>1}).at(5)));checks++;
}
console.log(JSON.stringify({tuftCacheUniformBytesPerInstance:32,uprightFallbackBytes:44,fullFallbackBytes:76,originalHDRFloat32ColorsAndPoseBytesExact:true,emptySphereAndCachedBoxHandled:true,wantedDensityCountBeforeFirstReach:true,firstEntryReentryAllTiersAndZeroDensityPromotion:true,unreachedAndReachedDisposal:true,trackSamplingScratchClearedAfterGradeOnly:true,trackPositionGradeTangentParity:true,noGpuMemoryPixelOr400GateClaim:true}));

console.log(`PASS ${checks} bounded actual-producer geometry/lifecycle/upload-mark/visibility checks. Browser memory, pixels, complete walk and timing still required.`);

// Explicit railway STATIC matrix release. Actual Three upload callback and bounds;
// no GPU/memory-budget verdict is inferred from these CPU lifecycle controls.
async function matrixReleaseModule(code=releaseSource, keep=false) {
 const previous=globalThis.window;globalThis.window={location:{search:keep?'?keep-geometry=1':''}};
 try {
  const nativeThree=pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href;
  const batch=Buffer.from((await fs.readFile(`${root}/renderers/web/js/batch-bounds.js`,'utf8')).replace("from 'three'",`from '${nativeThree}'`)).toString('base64');
  const module=code.replace("import * as THREE from 'three';",`import * as THREE from '${nativeThree}';`)
   .replace("from './shared-images.js'",`from '${pathToFileURL(`${root}/renderers/web/js/shared-images.js`).href}'`)
   .replace("from './batch-bounds.js'",`from 'data:text/javascript;base64,${batch}'`);
  return await import('data:text/javascript;base64,'+Buffer.from(module+`\n// matrix-keep=${keep}`).toString('base64'));
 } finally {if(previous===undefined)delete globalThis.window;else globalThis.window=previous;}
}
function staticMatrixPair(api,{dynamic=false,unmarked=false,layer='railway',keep=false}={}) {
 const group=new THREE.Group();group.name=layer;const geometry=new THREE.BoxGeometry(1,1,1),material=new THREE.MeshBasicMaterial();
 const near=new THREE.InstancedMesh(geometry,material,3),far=new THREE.InstancedMesh(new THREE.PlaneGeometry(1,1),material,3);
 for(let i=0;i<3;i++)near.setMatrixAt(i,new THREE.Matrix4().makeTranslation(i*100,0,0));
 near.instanceColor=new THREE.InstancedBufferAttribute(new Float32Array(9).fill(.7),3);
 far.instanceMatrix=near.instanceMatrix;far.instanceColor=near.instanceColor;
 near.count=1;far.count=0;near.computeBoundingSphere();far.boundingSphere=near.boundingSphere;
 near.userData.railwayStaticMatrix=true;far.userData.railwayStaticMatrix=!unmarked;
 if(dynamic)near.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
 group.add(near,far);const matrix=near.instanceMatrix,before=matrix.array.slice();
 api.releaseAfterUpload(group);assert.deepEqual(matrix.array,before,'No preupload release');
 matrix.onUploadCallback.call(matrix);
 return{group,near,far,matrix,before,geometry,keep};
}
function fullCapacityBounds(f) {
 assert.equal(f.matrix.array,null);assert.equal(f.near.count,1);assert.equal(f.far.count,0);
 assert.equal(f.matrix.userData.uploadBytes,3*16*4);
 assert.equal(f.near.instanceMatrix,f.far.instanceMatrix);assert.equal(f.near.boundingSphere,f.far.boundingSphere);
 assert(f.near.boundingBox.containsPoint(new THREE.Vector3(200.5,.5,.5)),'Full-capacity future instance must remain in cached box');
 assert(f.near.boundingSphere.containsPoint(new THREE.Vector3(200.5,.5,.5)),'Full-capacity future instance must remain in cached sphere');
 assert(f.geometry.attributes.position.array,'Ordinary railway geometry retained');assert(f.near.instanceColor.array,'Colors retained');
}
{
 const f=staticMatrixPair(release);fullCapacityBounds(f);checks+=11;
 const frustum=new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().makeOrthographic(190,210,10,-10,-10,10));
 for(const m of[f.near,f.far])m.getMatrixAt=()=>{throw Error('CPU matrix read after upload release');};
 for(const count of[0,1,3,2,0,3]){f.near.count=f.far.count=count;assert.doesNotThrow(()=>frustum.intersectsObject(f.near));assert.doesNotThrow(()=>release.releaseAfterUpload(f.group));checks+=2;}
 let disposed=0;f.near.addEventListener('dispose',()=>disposed++);f.far.addEventListener('dispose',()=>disposed++);f.near.dispose();f.far.dispose();assert.equal(disposed,2);checks++;
 for(const opts of[{dynamic:true},{unmarked:true},{layer:'flora'}]){const g=staticMatrixPair(release,opts);assert(g.matrix.array,'Dynamic/unmarked shared/nonrail data must remain');checks++;}
 const kept=staticMatrixPair(await matrixReleaseModule(releaseSource,true));assert(kept.matrix.array);checks++;
 const broken=releaseSource.replace('mesh.count = this.count; mesh.boundingBox = null;','mesh.count = count; mesh.boundingBox = null;');assert.notEqual(broken,releaseSource);
 const brokenRelease=await matrixReleaseModule(broken);
 assert.throws(()=>fullCapacityBounds(staticMatrixPair(brokenRelease)),/Full-capacity/);checks++;
}
{
 const f=withTufts();f.setDetail('light');f.update(eye(-160));const m=f.zone.tuftMesh,a=m.instanceMatrix;assert(a.userData.uploadReleased,'New late-installed tuft marked in same update');
 a.onUploadCallback.call(a);assert.equal(a.array,null);m.getMatrixAt=()=>{throw Error('Tuft matrix reread after upload');};
 for(const level of['full','balanced','light'])for(const n of[-50,-210,-350,-900,-160]){assert.doesNotThrow(()=>{f.setDetail(level);f.update(eye(n));new THREE.Frustum().intersectsObject(m);});checks++;}
 assert(m.instanceColor.array);f.dispose();checks+=2;
 const fresh=withTufts();fresh.setDetail('full');fresh.update(eye(-50));assert(fresh.zone.tuftMesh.instanceMatrix.userData.uploadReleased,'Next zone/new attribute marked independently');fresh.dispose();checks++;
}
const actualPick=base.slice(base.indexOf('  const raycaster = new THREE.Raycaster();'),base.indexOf('  out.dispose = () => {'));
assert(!/getMatrixAt|instanceMatrix|intersectObject|\.raycast\(/.test(actualPick),'Actual railway pick reads strips/terrain, never matrices');checks++;
console.log(JSON.stringify({railwayStaticMatrixUploadDrop:true,allSharedUsersOptedIn:true,fullCapacityBoundsBeforeDrop:true,sharedNearFarSphereRetained:true,countsRestored:true,dynamicAndUnmarkedAndOtherLayersRetained:true,keepGeometryHonored:true,actualLateTuftAllTierRangeAndDisposalPass:true,actualPickAnalyticNoMatrixRead:true,fixtureReleasedBytes:192,officialMemoryAndGPU:'UNRUN'}));

// Execute the unmodified analytic picker after every matrix read is poisoned.
{
 const out={},track={id:'actual-picker-track',centreline_local_m:[[0,0],[0,-110]]};
 const pick=Function('THREE','tracks','data','edgeMeshes','lake','row','terrain','GROUND','railwayCard','edgeCard','halfBed','out',actualPick+';return out;')(
  THREE,[track],{},[],{}, {cinders:[[-1,0,1,0],[-1,-110,1,-110]],verges:[]},
  {surfaceHeight:()=>0},{face:{lift:0}},(_data,near)=>({id:near.track.id}),()=>({id:'edge'}),1,out);
 const camera=new THREE.PerspectiveCamera(60,1,.1,100);camera.position.set(0,5,50);camera.lookAt(0,0,50);camera.updateMatrixWorld();
 const hit=pick.pickAt(new THREE.Vector2(),camera);assert.equal(hit?.id,track.id);assert(hit.distance>0);checks+=2;
 camera.position.x=50;camera.lookAt(50,0,50);camera.updateMatrixWorld();assert.equal(pick.pickAt(new THREE.Vector2(),camera),null);checks++;
}
console.log(`PASS ${checks} total native CPU checks, including actual analytic pick; browser upload, memory and pixels UNRUN.`);

// Original actual rock producers are the oracle, including underwater RNG draws.
const eagerRockScatter="  if (stones && lake && edgeMeshes.length) {\n    const rockRand = rng(19040713);\n    const [smin, smax] = stones.size_m ?? [0.35, 0.85];\n    const per = stones.per_m2?.full ?? 1.5;\n    const wetBelow = edgeSpec.face?.wet_below_m ?? 0.35;\n    const faceSt = lake.face;\n    for (let i = 0; i + 1 < faceSt.length; i += 1) {\n      const [ae0, an0, be0, bn0] = faceSt[i];\n      const [ae1, an1, be1, bn1] = faceSt[i + 1];\n      const along = Math.hypot(ae1 - ae0, an1 - an0);\n      const across = Math.hypot(be0 - ae0, bn0 - an0);\n      // the face is steep: its true area is the plan's over the slope's cosine\n      let count = Math.round(along * across * 1.2 * per);\n      while (count-- > 0) {\n        const u = rockRand(); const v = 0.08 + rockRand() * 0.86;\n        const e = (ae0 + (ae1 - ae0) * u) * (1 - v) + (be0 + (be1 - be0) * u) * v;\n        const n = (an0 + (an1 - an0) * u) * (1 - v) + (bn0 + (bn1 - bn0) * u) * v;\n        const size = smin + (smax - smin) * rockRand() ** 1.6;\n        const rr = size * 0.4;\n        const y = terrain.surfaceHeight(e, n);\n        const low = Math.min(y, terrain.surfaceHeight(e + rr, n), terrain.surfaceHeight(e - rr, n),\n          terrain.surfaceHeight(e, n + rr), terrain.surfaceHeight(e, n - rr));\n        const keep = rockRand();\n        const variant = rockRand() < 0.5 ? 0 : 1;\n        const yaw = rockRand() * Math.PI * 2; const tilt = (rockRand() - 0.5) * 0.7; const roll = (rockRand() - 0.5) * 0.7;\n        const quat = new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, yaw, roll, 'YXZ')).toArray();\n        const tone = 0.5 + rockRand() * 0.32;\n        if (y < 0.05) continue;                        // at or under the water: the map carries it\n        const z = zoneOf(n);\n        // seated: its flat underside on the lowest ground under it, sunk among the rest\n        const seat = (low + y) / 2 + size * (0.2 - 0.3 * (stones.sink ?? 0.35));\n        z.rocks.push({ e, n, y: seat, size, keep, variant, quat, tone, tint: wetTint(y, wetBelow) });\n        z.rockE += e;\n      }\n    }\n  }\n";
const eagerRockBuilder="    if (rockMat && z.rocks.length) {\n      z.rocks.sort((a, b) => a.keep - b.keep);\n      z.rockMeshes = rockGeos.map((g, vi) => {\n        const list = z.rocks.filter((r) => r.variant === vi);\n        const mesh = new THREE.InstancedMesh(g, rockMat, Math.max(1, list.length));\n        list.forEach((r, k) => {\n          q.fromArray(r.quat);\n          m4.compose(v3.set(wx(r.e), r.y, wz(r.n)), q, s3.set(r.size, r.size, r.size));\n          mesh.setMatrixAt(k, m4);\n          mesh.setColorAt(k, c.setRGB(r.tone * r.tint[0], r.tone * r.tint[1], r.tone * r.tint[2]));\n        });\n        mesh.computeBoundingSphere();\n        mesh.userData.railwayStaticMatrix = true;\n        mesh.name = `railway-rocks-z${zi}-${vi}`;\n        mesh.castShadow = false; mesh.receiveShadow = true;\n        mesh.userData.keeps = list.map((r) => r.keep);\n        group.add(mesh);\n        return mesh;\n      });\n      z.rockCentre = z.rockE / z.rocks.length;\n    }\n";
const currentRockScatter=base.slice(base.indexOf('  if (stones && lake && edgeMeshes.length) {'),base.indexOf('\n  /* ---- build each zone',base.indexOf('  if (stones && lake && edgeMeshes.length) {')));
const currentRockBuilder=base.slice(base.indexOf('    if (rockMat && z.rocks.length) {'),base.indexOf('    z.rocks = null;',base.indexOf('    if (rockMat && z.rocks.length) {')));
const wetCode=base.slice(base.indexOf('function wetTint('),base.indexOf('/**',base.indexOf('function wetTint(')));
function scatterRocks(source,face,terrain,stones) {
 const z={rocks:[],rockE:0};
 Function('THREE','rng','WET','UNDER','stones','lake','edgeMeshes','edgeSpec','terrain','zoneOf',wetCode+source)(
  THREE,rockHelpers.rng,[.52,.56,.48],[.36,.42,.38],stones,{face},[{}],{face:{wet_below_m:.35}},terrain,()=>z);
 return z;
}
function buildRocks(source,z,face,stones) {
 const group=new THREE.Group();group.name='railway';const geos=[new THREE.BoxGeometry(1,1,1),new THREE.IcosahedronGeometry(.6)],mat=new THREE.MeshStandardMaterial();
 const marker=new THREE.Object3D();
 Function('THREE','packRockCache','rockReplayFace','lake','stones','z','rockMat','rockGeos','group','zi','wx','wz',
  'const q=new THREE.Quaternion(),m4=new THREE.Matrix4(),v3=new THREE.Vector3(),s3=new THREE.Vector3(),c=new THREE.Color();'+source)(
  THREE,rockHelpers.packRockCache,face.map(st=>new Float64Array(st)),{face},stones,z,mat,geos,group,0,e=>e,n=>-n);
 assert.equal(new THREE.Object3D().id-marker.id,3,'Original two rock Object3D slots retained');checks++;
 return {z,group};
}
const words=a=>new Uint32Array(a.buffer,a.byteOffset,a.length);
const actualRockScene=JSON.parse(await fs.readFile(`${root}/data/railway/1904_context.json`,'utf8'));
if(phase!=='cache-words'){
let sourceRockRows=0,sourceRecipeBytes=0,sourceFullBytes=0;
for(const [label,face,terrain,actualStones] of [
 ['mixed-underwater',[[-0,0,3,0],[1,-30,4,-30],[2,-60,5,-60]],{surfaceHeight:(e,n)=>.15+Math.sin(n/4)*.3}],
 ['actual-1904-complete-face',actualRockScene.lake_edge.face,{surfaceHeight:(e,n)=>.4+Math.sin(n/41)*.4},actualRockScene.edge.stones],
 ['actual-1904-above-water',actualRockScene.lake_edge.face,{surfaceHeight:()=>.5},actualRockScene.edge.stones],
]) {
 const stones=actualStones??{size_m:[.35,.85],sink:.35,per_m2:{full:1.5}};
 const eager=scatterRocks(eagerRockScatter,face,terrain,stones),lazy=scatterRocks(currentRockScatter,face,terrain,stones);
 assert.equal(lazy.rocks.length,eager.rocks.length);checks++;
 for(let k=0;k<lazy.rocks.length;k++) {const {faceIndex,sourceSeed,...r}=lazy.rocks[k];assert.deepEqual(r,eager.rocks[k]);checks++;}
 for(const share of[label==='mixed-underwater'?1:stones.per_m2.light/stones.per_m2.full]) {
  const select=z=>({rocks:z.rocks.filter(r=>r.keep<share),rockE:z.rocks.filter(r=>r.keep<share).reduce((sum,r)=>sum+r.e,0)});
  const a=buildRocks(eagerRockBuilder,select(eager),face,stones),b=buildRocks(currentRockBuilder,select(lazy),face,stones);
  for(let vi=0;vi<2;vi++) {
   const old=a.z.rockMeshes[vi],mesh=b.z.rockMeshes[vi],cache=mesh.userData.rockCache;
   assert(cache&&!cache.matrix,'Every original source row must admit exact compact replay');assert(cache.faces instanceof Uint16Array);assert.equal(mesh.count,0);checks+=3;
   sourceRockRows+=cache.count;sourceRecipeBytes+=cache.faces.byteLength+cache.seeds.byteLength+cache.values.byteLength+(cache.tintMask?.byteLength??0)+(cache.tintValues?.byteLength??0);sourceFullBytes+=old.instanceMatrix.array.byteLength+old.instanceColor.array.byteLength;
   const sphere=mesh.boundingSphere;assert.deepEqual(sphere.center.toArray(),old.boundingSphere.center.toArray());assert.equal(sphere.radius,old.boundingSphere.radius);checks+=2;
   // Original coordinates may be mutated after construction, but replay uses a private double snapshot.
   const original=face[0][0];face[0][0]+=17;
   rockHelpers.installRockCache(mesh,Math.min(2,cache.count));face[0][0]=original;
   assert.deepEqual(words(mesh.instanceMatrix.array),words(old.instanceMatrix.array));assert.deepEqual(words(mesh.instanceColor.array),words(old.instanceColor.array));
   assert.equal(mesh.boundingSphere,sphere);assert.equal(mesh.userData.rockCache,null);checks+=4;
   // Original ground/HDR RGB/negative-zero Float32 bits need no future terrain access.
   const records=lazy.rocks.filter(r=>r.keep<share).sort((a,b)=>a.keep-b.keep).filter(r=>r.variant===vi);
   const colors=old.instanceColor.array.slice();colors[0]=1.25;colors[1]=-0;
   const matrix=old.instanceMatrix.array.slice();matrix[13]=-0;
   const special=rockHelpers.packRockCache(matrix,colors,records,face.map(st=>new Float64Array(st)),stones.size_m);
   assert(!special.matrix);const holder=new THREE.InstancedMesh(old.geometry,old.material,0);holder.userData.rockCache=special;rockHelpers.installRockCache(holder,records.length);
   assert.deepEqual(words(holder.instanceMatrix.array),words(matrix));assert.deepEqual(words(holder.instanceColor.array),words(colors));checks+=3;
   const wrong=records.map((r,k)=>k? r:{...r,sourceSeed:(r.sourceSeed+1)>>>0});
   const fallback=rockHelpers.packRockCache(matrix,colors,wrong,face,stones.size_m);assert.equal(fallback.matrix,matrix);assert.equal(fallback.color,colors);checks+=2;
   const malformed=records.map((r,k)=>k?r:{...r,faceIndex:-1});assert.equal(rockHelpers.packRockCache(matrix,colors,malformed,face,stones.size_m).matrix,matrix);checks++;
  }
  console.log(JSON.stringify({rockSourceCase:label,retainedRows:b.z.rockMeshes.reduce((n,m)=>n+m.instanceMatrix.count,0),actualSpec:!!actualStones,lightBuiltShare:share}));
  // Existing tier/range paths install only on original rock reach and retain later attributes.
  const lazyAgain=buildRocks(currentRockBuilder,select(lazy),face,stones),f=make();
  f.group.add(...lazyAgain.group.children.slice());Object.assign(f.zone,{rockMeshes:lazyAgain.z.rockMeshes,rockCentre:0});f.setDetail('light');f.update(eye(-900));
  assert(f.zone.rockMeshes.every(m=>m.count===0&&m.userData.rockCache));checks++;
  f.update(eye(-50));
  for(const mesh of f.zone.rockMeshes){assert.equal(mesh.userData.rockCache,null);assert(mesh.instanceMatrix.userData.uploadReleased);mesh.instanceMatrix.onUploadCallback.call(mesh.instanceMatrix);assert.equal(mesh.instanceMatrix.array,null);mesh.getMatrixAt=()=>{throw Error('Rock read after release');};checks+=3;}
  for(const level of['full','balanced','light'])for(const n of[-50,-209,-350,-900,-160]){assert.doesNotThrow(()=>{f.setDetail(level);f.update(eye(n));for(const m of f.zone.rockMeshes)new THREE.Frustum().intersectsObject(m);});checks++;}
  f.dispose();assert(f.zone.rockMeshes.every(m=>m.userData.rockCache===null));checks++;
  const pending=buildRocks(currentRockBuilder,select(lazy),face,stones),u=make();u.group.add(...pending.group.children.slice());Object.assign(u.zone,{rockMeshes:pending.z.rockMeshes,rockCentre:0});u.dispose();assert(u.zone.rockMeshes.every(m=>m.userData.rockCache===null));checks++;
 }
}
{
 const face=[[0,0,3,0],[1,-10,4,-10]],stones={size_m:[.45,1.1],per_m2:{full:2},sink:.4};
 const z=scatterRocks(currentRockScatter,face,{surfaceHeight:()=>.5},stones);
 const old=buildRocks(eagerRockBuilder,{rocks:z.rocks,rockE:z.rockE},face,stones);
 const records=z.rocks.sort((a,b)=>a.keep-b.keep).filter(r=>r.variant===0);
 const many=Array(65537).fill([0,0,0,0]);many[65535]=face[0];many[65536]=face[1];
 const mesh=old.z.rockMeshes[0],cache=rockHelpers.packRockCache(mesh.instanceMatrix.array,mesh.instanceColor.array,records.map(r=>({...r,faceIndex:65535})),many,stones.size_m);
 assert(cache.faces instanceof Uint32Array);assert(!cache.matrix);assert.deepEqual(words(rockHelpers.replayRockMatrices(cache)),words(mesh.instanceMatrix.array));checks+=3;
}
console.log(JSON.stringify({sourceRockRows,sourceRecipeBytes,sourceFullBytes,sourceBytesSaved:sourceFullBytes-sourceRecipeBytes,maxRecipeBytesPerRowBeforeGray:22,originalNineDrawSequenceAndWaterFilteringExact:true,allComparedMatrixAndHDRColorWordsExact:true,privateDoubleFaceSnapshot:true,wrongSeedAndMalformedFallback:true,actualSetDetailReachUploadDisposePass:true,browserPixelsAndOfficialMemory:'UNRUN'}));
console.log(`PASS ${checks} total native CPU producer/lifecycle checks; no browser or official-budget claim.`);

// Gray-channel packing must preserve exact Float32 words, including signed zero.
{
 const values=new Float32Array([
  -0,1.25,1.25,1.25, .3,-0,-0,-0, .4,-0,0,-0, .5,.8,.7,.6,
  .6,.9,.9,.9, .7,2,2,2, .8,.5,.5,.5, .9,.4,.4,.4,
  1,.3,.3,.3]);
 const compact=rockHelpers.packRockValues(values,values.length/4);assert.equal(compact.valueStride,2);checks++;
 const restored=new Float32Array(values.length/4*3);let cursor=0;
 for(let k=0;k<values.length/4;k++){
  const r=compact.values[k*2+1],t=compact.tintMask[k>>3]&(1<<(k&7));
  restored[k*3]=r;restored[k*3+1]=t?compact.tintValues[cursor++]:r;restored[k*3+2]=t?compact.tintValues[cursor++]:r;
  assert.equal(Object.is(compact.values[k*2],values[k*4]),true);checks++;
 }
 const actualHolder=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshBasicMaterial(),0);
 actualHolder.userData.rockCache={...compact,count:values.length/4,matrix:new Float32Array(values.length/4*16)};
 rockHelpers.installRockCache(actualHolder,values.length/4);
 const expected=Float32Array.from(Array.from({length:values.length/4},(_,k)=>[...values.subarray(k*4+1,k*4+4)]).flat());
 assert.deepEqual(words(restored),words(expected));assert.deepEqual(words(actualHolder.instanceColor.array),words(expected));assert.equal(cursor,compact.tintValues.length);checks+=3;
 const colorful=new Float32Array([0,1,2,3, 0,4,5,6]);assert.equal(rockHelpers.packRockValues(colorful,2).values,colorful);checks++;
 const nonfinite=values.slice();nonfinite[2]=NaN;assert.equal(rockHelpers.packRockValues(nonfinite,nonfinite.length/4).values,nonfinite);checks++;
 const inf=values.slice();inf[0]=Infinity;assert.equal(rockHelpers.packRockValues(inf,inf.length/4).values,inf);checks++;
 // A wrong gray classifier that equates +0 and -0 must lose a word and fail.
 const wordTest='const tinted = k => words[k * 4 + 1] !== words[k * 4 + 2] || words[k * 4 + 1] !== words[k * 4 + 3];';
 const brokenHelpers=tieHelpers.replace(wordTest,'const tinted = k => values[k * 4 + 1] !== values[k * 4 + 2] || values[k * 4 + 1] !== values[k * 4 + 3];');assert.notEqual(brokenHelpers,tieHelpers);
 const badPack=Function('THREE',brokenHelpers+';return packRockValues;')(THREE),bad=badPack(values,values.length/4);
 const badHolder=new THREE.InstancedMesh(actualHolder.geometry,actualHolder.material,0);badHolder.userData.rockCache={...bad,count:values.length/4,matrix:new Float32Array(values.length/4*16)};
 rockHelpers.installRockCache(badHolder,values.length/4);
 assert.throws(()=>assert.deepEqual(words(badHolder.instanceColor.array),words(expected)),assert.AssertionError);checks++;
}
console.log(`PASS ${checks} native CPU checks including profitable gray/mixed HDR/signed-zero and unprofitable/nonfinite controls; official memory UNRUN.`);
}

// Cache only final Float32 WORDS: no quantization, matrix recipe, or RGB relation.
// Include payloads that cannot be valid scene numbers; their NaN payload/sign bits
// still belong to this storage codec, without ever handing NaNs to a mesh.
if(phase!=='legacy'){
let cacheWordRoundtrips=0;
const cacheBytes=c=>c.values?.byteLength??c.wordColumns.reduce((n,c)=>n+(c.data?.byteLength??0)+(c.dictionary?.byteLength??0),0);
function wordRoundtrip(input,stride,compressed) {
 const values=new Float32Array(input.length);new Uint32Array(values.buffer).set(input);
 const original={count:input.length/stride,stride,values},packed=tieFunctions.packRailCacheWords(original);
 if(compressed===true)assert.notEqual(packed,original);if(compressed===false)assert.equal(packed,original);
 const decoded=tieFunctions.unpackRailCacheWords(packed);
 assert.deepEqual(words(decoded.values),input);cacheWordRoundtrips+=input.length;checks++;
 if(packed!==original){
  assert(!Object.hasOwn(packed,'values'),'Compressed cache must not retain its original Float32 view');
  for(const c of packed.wordColumns)for(const a of[c.data,c.dictionary])if(a)assert.notEqual(a.buffer,values.buffer);
  new Uint32Array(values.buffer).fill(0x12345678);
  assert.deepEqual(words(tieFunctions.unpackRailCacheWords(packed).values),input,'Private encoded data must survive original scratch reuse');checks+=2;
 }
 return packed;
}
{
 const count=1024,input=new Uint32Array(count*8),special=[0,0x80000000,0x7f800000,0xff800000,0x7fc00001,0x7fa12345,0xffa54321,0x3fa00000];
 let seed=0x8b73062;
 for(let i=0;i<count;i++){
  seed=(Math.imul(seed,1664525)+1013904223)>>>0;
  input.set([0x80000000,0x3f800000+i%256,0x3f000000+(i*123)%65536,
   0x3f000000+(i*7919)%0x1000000,seed,special[i%special.length],
   [0x3f333333,0xbf333333,0x3eaaaaab,0xbeaaaaab][i%4],0xffa12345],i*8);
 }
 const packed=wordRoundtrip(input,8,true);
 assert.deepEqual(packed.wordColumns.map(c=>c.width),[0,1,2,3,4,1,1,0]);
 assert(packed.wordColumns[5].dictionary);assert(packed.wordColumns[6].dictionary);checks+=3;
 // Every byte-width boundary, including the entire unsigned word domain.
 for(const[span,width]of[[255,1],[256,2],[65535,2],[65536,3],[0xffffff,3],[0x1000000,4],[0xffffffff,4]]){
  const a=new Uint32Array(count*2);for(let i=0;i<count;i++){a[i*2]=Math.floor(span*i/(count-1));a[i*2+1]=0xdeadbeef;}
  assert.equal(wordRoundtrip(a,2,true).wordColumns[0].width,width);checks++;
 }
 // Full entropy cannot buy an encoding; admission includes 64 + 256/column
 // reserved descriptor/view bytes, not just the encoded typed-array payload.
 const entropy=new Uint32Array(count*8);for(let i=0;i<entropy.length;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;entropy[i]=seed;}
 wordRoundtrip(entropy,8,false);
 wordRoundtrip(new Uint32Array(80).fill(0x80000000),1,false);
 wordRoundtrip(new Uint32Array(81).fill(0x80000000),1,true);
 wordRoundtrip(new Uint32Array(0),11,false);
 assert.throws(()=>tieFunctions.packRailCacheWords({count:1,stride:11,values:new Float32Array(10)}));checks++;
 const wrong=change=>{const c={...packed,wordColumns:packed.wordColumns.map(c=>({...c}))};change(c);return c;};
 for(const corrupt of[
  c=>{c.stride++;},c=>{c.count=-1;},c=>{c.wordColumns[0].width=5;},
  c=>{c.wordColumns[1].data=c.wordColumns[1].data.subarray(1);},
  c=>{c.wordColumns[5].data=c.wordColumns[5].data.slice();c.wordColumns[5].data[0]=255;},
  c=>{c.wordColumns[1].base=0xffffffff;},
 ]){assert.throws(()=>tieFunctions.unpackRailCacheWords(wrong(corrupt)));checks++;}
 // A plausible but wrong byte must fail the same complete word oracle.
 const corrupt=wrong(c=>{c.wordColumns[1].data=c.wordColumns[1].data.slice();c.wordColumns[1].data[0]^=1;});
 assert.throws(()=>assert.deepEqual(words(tieFunctions.unpackRailCacheWords(corrupt).values),input),assert.AssertionError);checks++;
 const broken=tieHelpers.replace('words[i * stride + lane] = word;','words[i * stride + lane] = word & 0x7fffffff;');assert.notEqual(broken,tieHelpers);
 const loseSign=Function('THREE',broken+';return unpackRailCacheWords;')(THREE);
 assert.throws(()=>assert.deepEqual(words(loseSign(packed).values),input),assert.AssertionError);checks++;
}
// Actual Three Matrix4/Quaternion/Color eager producers remain the oracle. The
// larger fixture follows the native 1904 track path and reaches the real codec;
// the existing tiny fixtures above retain their Float32 interfaces and strides.
{
 const source=JSON.parse(await fs.readFile(`${root}/data/railway/1904.json`,'utf8'));
 const path=trackPath(source.tracks.find(t=>t.id==='ic_track_17').centreline_local_m,{surfaceHeight:(e,n)=>.3+Math.sin(n/75)*.1});
 const ties=source.ties,rand=rockHelpers.rng(19040701);
 const records=Array.from({length:Math.min(2048,Math.floor(path.length/ties.spacing_m))},(_,i)=>{
  const s=(i+.5)*ties.spacing_m,sj=s+(rand()-.5)*2*ties.jitter.along_m,a=path.at(Math.max(0,Math.min(path.length,sj)));
  const yaw=Math.atan2(a.tn,a.te)+((rand()-.5)*2*ties.jitter.skew_deg*Math.PI)/180;
  const length=ties.length_m+(rand()-.5)*2*ties.jitter.length_m,shift=(rand()-.5)*.08,tone=.78+rand()*.34;
  return{e:a.e+a.tn*shift,n:a.n-a.te*shift,y:a.y+.024+ties.exposed_m,yaw,length,tone,warm:rand()};
 });
 const eager=tiePair(eagerTieSource,records),lazy=tiePair(lazyTieSource,records),cache=lazy.z.tieCache;
 assert(cache.wordColumns);assert.equal(cache.stride,11);assert(!cache.values);checks+=3;
 const pending=make();pending.group.add(...lazy.group.children.slice());Object.assign(pending.zone,{tiesNear:lazy.z.tiesNear,tiesFar:lazy.z.tiesFar,tieCache:cache});
 pending.update(eye(-900));assert.equal(pending.zone.tieCache,cache);assert.equal(pending.zone.tiesNear.count,0);checks+=2;
 pending.update(eye(-50));assert.equal(pending.zone.tieCache,null);sameTiePair(eager,{z:pending.zone});checks++;
 const matrix=pending.zone.tiesNear.instanceMatrix,color=pending.zone.tiesNear.instanceColor;
 for(const level of['full','balanced','light'])for(const n of[-900,-300,-50]){pending.setDetail(level);pending.update(eye(n));assert.equal(pending.zone.tiesNear.instanceMatrix,matrix);assert.equal(pending.zone.tiesNear.instanceColor,color);checks+=2;}
 pending.dispose();assert.equal(pending.zone.tieCache,null);checks++;
 const tuftRows=records.map((r,i)=>({...r,scale:.6+(i%271)*.002,keep:(i*317%2048)/2048,yaw:((i+1)*1.371)%Math.PI}));
 const eagerTufts=tuftPair(eagerTuftSource,tuftRows),lazyTufts=tuftPair(lazyTuftSource,tuftRows),tuftCache=lazyTufts.z.tuftCache;
 assert(tuftCache.wordColumns);assert.equal(tuftCache.stride,8);assert(!tuftCache.values);checks+=3;
 const f=make();f.group.add(...lazyTufts.group.children.slice());Object.assign(f.zone,{tuftMesh:lazyTufts.z.tuftMesh,tuftKeeps:lazyTufts.z.tuftKeeps,tuftCache});
 f.setDetail('light');f.update(eye(-900));assert.equal(f.zone.tuftCache,tuftCache);assert.equal(f.zone.tuftMesh.count,0);checks+=2;
 const wanted=eagerTufts.z.tuftKeeps.filter(k=>k<.25).length;eagerTufts.z.tuftMesh.count=wanted;
 f.update(eye(-50));assert.equal(f.zone.tuftCache,null);sameTuft(eagerTufts,{z:f.zone});checks++;
 const tm=f.zone.tuftMesh.instanceMatrix,tc=f.zone.tuftMesh.instanceColor;
 for(const level of['full','balanced','light'])for(const n of[-900,-160,-50]){f.setDetail(level);f.update(eye(n));assert.equal(f.zone.tuftMesh.instanceMatrix,tm);assert.equal(f.zone.tuftMesh.instanceColor,tc);checks+=2;}
 f.dispose();assert.equal(f.zone.tuftCache,null);checks++;
 console.log(JSON.stringify({railWordCacheFixtureRows:records.length,tieFloatBytes:records.length*44,tieEncodedPayloadBytes:cacheBytes(cache),tuftFloatBytes:tuftRows.length*32,tuftEncodedPayloadBytes:cacheBytes(tuftCache),admissionReservesDescriptorBytes:true,actualThreeEagerMatrixColorBoundsAndIdOracle:true,originalFirstReachDensityOrderAndReentry:true,noOriginalFloat32CacheRetainer:true,actual1904SceneMemory:'UNRUN'}));
}
console.log(`PASS ${checks} native CPU lifecycle controls plus ${cacheWordRoundtrips} exact cache word roundtrips; GPU, browser, and official memory UNRUN.`);
}

// Exact configured-tier density prefixes: original JS-double comparisons, not
// Float32 thresholds or rounded keep values. Every earlier lifecycle oracle stays.
{
 const prefix=(keeps,threshold)=>{let n=0;while(n<keeps.length&&keeps[n]<threshold)n++;return n;};
 const datasets=[[],[-0,0,Number.MIN_VALUE,.25-Number.EPSILON,.25,.25+Number.EPSILON,.5,.6,1],
  [-Infinity,-0,0,.1,Infinity],[.1,NaN,.2],[.2,.8,.1],[NaN]];
 for(const raw of datasets)for(const initial of[null,.3])for(const dens of[
  {full:4,balanced:2,light:1},{full:0,balanced:0,light:0},
  {full:1,balanced:NaN,light:-0},{full:2,balanced:Infinity,light:-1},
 ]){
  // The existing Light constructor's filter precedes the original sort; kept
  // rows remain a subsequence. Direct unsorted cases also retain old stop-first.
  const kept=initial===null?raw.slice():raw.filter(k=>k<initial);
  const share={full:1,balanced:.6,light:.3},rock={userData:{keeps:kept.slice()},count:0};
  const zone={rockMeshes:[rock],tuftMesh:{count:0},tuftKeeps:kept.slice()};
  const f=Function('zones','dens','rockShare','REACH',`let level='light';const out={census:{}};${detailSource};return out;`)([zone],dens,share,reach);
  let expectedLevel='light';
  for(const next of['full','balanced','light','bogus','',null,undefined,'toString','constructor','light','full']){
   if(reach[next])expectedLevel=next;f.setDetail(next);
   const rocks=prefix(kept,share[expectedLevel]),tufts=prefix(kept,(dens[expectedLevel]??0)/(dens.full||1));
   assert.equal(rock.userData.rockWanted,rocks);assert.equal(rock.count,rocks);assert.equal(f.census.rocks,rocks);
   assert.equal(zone.tuftWanted,tufts);assert.equal(zone.tuftMesh.count,tufts);assert.equal(f.census.tufts,tufts);checks+=6;
  }
  assert.equal(Object.hasOwn(rock.userData,'keeps'),false);assert.equal(Object.hasOwn(zone,'tuftKeeps'),false);
  assert.equal(Object.getPrototypeOf(rock.userData.densityCounts),null);assert.equal(Object.getPrototypeOf(zone.tuftDensityCounts),null);
  assert.deepEqual(Object.keys(rock.userData.densityCounts),['full','balanced','light']);
  assert.deepEqual(Object.keys(zone.tuftDensityCounts),['full','balanced','light']);checks+=6;
 }
}
console.log(`PASS ${checks} total native CPU checks, including exact configured density prefixes; browser/memory UNRUN.`);
