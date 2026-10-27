import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
if(process.argv.slice(2).some(v=>v!=='--self-test'))throw Error('Only --self-test is supported');
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url)).replace(/\/$/,''),base=await fs.readFile(`${root}/renderers/web/js/railway.js`,'utf8'),proposed=base;
const THREE=await import(pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href);
const producer=s=>s.slice(s.indexOf('function railProfile('),s.indexOf('/* -------------------------------------------------------------------------- */\n/* the layer'));
// Geometry fixture below pins the output; lifecycle functions are the actual producer.
const funcs=Function('THREE','GROUND','STEEL','RUST','HEAD_SIDE','wx','wz',producer(base)+';return {railProfile,laySection,railMesh};')(THREE,{bed:{lift:.024}},new THREE.Color(0xa3a4a6),new THREE.Color(0x4f3527),new THREE.Color(0x6b5546),e=>e,n=>-n);
const trackCode=base.slice(base.indexOf('function trackPath('),base.indexOf('/* -------------------------------------------------------------------------- */\n/* draped ribbons'));
const trackPath=Function(trackCode+';return trackPath;')();
const spec={gauge_m:1.435,rail:{base_m:.125,base_depth_m:.018,web_m:.013,head_width_m:.065,height_m:.145,head_depth_m:.034},ties:{exposed_m:.025}};
const paths=[trackPath([[0,0],[1,-90],[-4,-220]],{surfaceHeight:(e,n)=>Math.sin(n/70)*.3}),trackPath([[3,0],[4,-100],[2,-230]],{surfaceHeight:(e,n)=>Math.cos(n/60)*.2})];
const profNear=funcs.railProfile(spec.rail,true),profFar=funcs.railProfile(spec.rail,false),mat=new THREE.MeshStandardMaterial();
const headers=proposed.slice(proposed.indexOf('  const nearRails = (z) => {'),proposed.indexOf('  /* ---- level and reach ---- */'));
const update=proposed.slice(proposed.indexOf('  out.update = (camera) => {'),proposed.indexOf('  /* ---- what a pick answers ---- */'));
const dispose=proposed.slice(proposed.indexOf('  out.dispose = () => {'),proposed.indexOf('  group.userData.census = out.census;'));
const reach={full:{near:130,ties:650,tufts:240,rocks:110},balanced:{near:100,ties:480,tufts:170,rocks:85},light:{near:60,ties:220,tufts:100,rocks:50}};
const releaseSource=await fs.readFile(`${root}/renderers/web/js/upload-release.js`,'utf8');
const release=await import('data:text/javascript;base64,'+Buffer.from(releaseSource.replace("import * as THREE from 'three';",`import * as THREE from '${pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.module.js`).href}';`).replace("import { isSharedImage, retireSharedImage } from './shared-images.js';",'const isSharedImage=()=>false,retireSharedImage=()=>{};')).toString('base64'));
function make(){const group=new THREE.Group();group.name='railway';let marks=0;const zone={index:0,nHi:0,nLo:-110,centre:new THREE.Vector3(0,0,55),level:.5,sections:[[0,0,70],[1,10,100]]};const zones=[zone];const out=Function('THREE','group','paths','profNear','profFar','spec','railMat','onGeometry','laySection','railMesh','zones','REACH',`const out={census:{nearZones:0}},ZONE_M=110;let level='light';const capPile=null,pileSpots=[],geometries=[],materials=[],maps=new Map();${headers}${update}${dispose}return {...out,zone:zones[0],farRails,dropFarRails,nearRails,dropNearRails,setLevel:(v)=>{level=v;}};`)(THREE,group,paths,profNear,profFar,spec,mat,g=>{marks++;release.releaseAfterUpload(g);},funcs.laySection,funcs.railMesh,zones,reach);return{...out,group,get marks(){return marks;}};}
const hashMesh=m=>createHash('sha256').update(Buffer.concat([...Object.entries(m.geometry.attributes).map(([k,a])=>Buffer.concat([Buffer.from(k),Buffer.from(a.array.buffer,a.array.byteOffset,a.array.byteLength)])),Buffer.from(m.geometry.index.array.buffer,m.geometry.index.array.byteOffset,m.geometry.index.array.byteLength)])).digest('hex');
function eager(){const b={pos:[],nrm:[],col:[],idx:[]};for(const[i,s0,s1]of [[0,0,70],[1,10,100]])funcs.laySection(paths[i],s0,s1,profFar,spec,b);return funcs.railMesh('railway-rails-far-z0',b,.5,mat,false);}
const expected=eager(),expectedHash=hashMesh(expected);assert.equal(expectedHash,'87c4ce9d4ed5fa06e903dcef68b2b162c35aeca4fa783499b207450c61f3edfb');let checks=1;
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
console.log(`PASS ${checks} bounded actual-producer geometry/lifecycle/upload-mark/visibility checks. Browser memory, pixels, complete walk and timing still required.`);
