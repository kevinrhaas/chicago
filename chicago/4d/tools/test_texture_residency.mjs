#!/usr/bin/env node
// T-3173: real pinned Three/GLTFLoader image sharing and compressed source ownership.
// Decoder and GPU-property doubles keep this in the existing shared-image native gate;
// real decode, GPU memory, revisit images and context restore remain browser acceptance.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {pathToFileURL, fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const threeUrl=pathToFileURL(`${root}/renderers/web/vendor/three-0.185.1/three.core.js`).href;
const THREE=await import(threeUrl);
const sharedUrl=pathToFileURL(`${root}/renderers/web/js/shared-images.js`).href;
const {shareImageSources, glbImageSource}=await import(sharedUrl);
let tests=[];
function check(label,fn){assert.ok(fn,label);tests.push(label);console.log('PASS '+label)}
let current,loaderInstance;
class FakeKTX2Loader{
 constructor(){loaderInstance=this;this.workerConfig={dxtSupported:true};this.workerPool={workersResolve:[{retained:'task'}],workerStatus:0};}
 detectSupport(){} dispose(){} load(url,onLoad,onProgress,onError){queueMicrotask(()=>url==='fail'?onError(new Error('decode failure')):onLoad(current));return 'request-handle';}
 loadAsync(url){return new Promise((r,j)=>this.load(url,r,undefined,j));}
}
const hadLoader=Object.hasOwn(globalThis,'__T3173KTX2Loader');
const previousLoader=globalThis.__T3173KTX2Loader;
const hadSelf=Object.hasOwn(globalThis,'self');
const previousSelf=globalThis.self;
globalThis.__T3173KTX2Loader=FakeKTX2Loader;
async function moduleFor(name){let src=await fs.readFile(`${root}/renderers/web/js/${name}`,'utf8');
 src=src.replace("from 'three'",`from '${threeUrl}'`).replace("import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';",'const KTX2Loader = globalThis.__T3173KTX2Loader;')
 .replace("from './shared-images.js'",`from '${sharedUrl}'`).replace("import { noteReleasedLevels } from './upload-release.js';",'const noteReleasedLevels = () => {};');
 return import(`data:text/javascript;base64,${Buffer.from(src).toString('base64')}`);}
const kt=await moduleFor('ktx2.js');
function texture(){const levels=Array.from({length:9},(_,i)=>{let width=256>>i;return{width,height:width,data:new Uint8Array(Math.max(16,width*width)).fill(i+1)}});let t=new THREE.CompressedTexture(levels,256,256,THREE.RGBA_BPTC_Format);t.wrapS=THREE.RepeatWrapping;t.anisotropy=4;t.colorSpace=THREE.SRGBColorSpace;return t;}
current=texture();const original=current;const fullBytes=kt.sheetGpuBytes(current);
kt.initKTX2({}, {textures:'light'});
const holder={setKTX2Loader(l){this.l=l}};check('register returns original GLTF loader',kt.registerKTX2(holder)===holder);
const load=(l,url='ok')=>new Promise((r,j)=>l.load(url,r,undefined,j));
const light=await load(holder.l);
check('embedded light GLB drops exactly mip0',light.mipmaps.length===8&&light.image.width===128&&light.mipmaps[0].data[0]===2);
check('cached original texture/source/chain stay full',original.mipmaps.length===9&&original.image.width===256&&original.source!==light.source);
check('sampler and color space survive',light.wrapS===original.wrapS&&light.anisotropy===4&&light.colorSpace===original.colorSpace);
check('remaining mip payloads stay exact',light.mipmaps.every((m,i)=>m.data===original.mipmaps[i+1].data));
check('light retained bytes equal exact existing tail sum',kt.sheetGpuBytes(light)===fullBytes-original.mipmaps[0].data.byteLength);
check('idle transcode resolver no longer retains full reply',loaderInstance.workerPool.workersResolve[0]===null);
const again=await load(holder.l);check('repeat decode never trims cached source twice',again.image.width===128&&original.image.width===256);
check('repeat delivery shares reduced GPU source identity',again.source===light.source&&again!==light);
check('full cache and reduced deliveries own their mip descriptors',light.mipmaps.every((m,i)=>m!==original.mipmaps[i+1]&&m!==again.mipmaps[i]));
const originalPayloads=original.mipmaps.map(m=>Buffer.from(m.data));
for(const m of light.mipmaps)m.data=new Uint8Array(0);
check('releasing one delivery preserves all cached original payloads',original.mipmaps.every((m,i)=>Buffer.from(m.data).equals(originalPayloads[i])));
check('releasing one delivery preserves another delivery payloads',again.mipmaps.every(m=>m.data.byteLength>0));
const afterRelease=await load(holder.l);
check('cached reduced variant still serves populated mips after release',afterRelease.source===again.source&&afterRelease.mipmaps.every(m=>m.data.byteLength>0));
let failure;try{await load(holder.l,'fail')}catch(e){failure=e}check('decode rejection propagates',failure?.message==='decode failure');
kt.initKTX2({}, {textures:'full'});const h2={setKTX2Loader(l){this.l=l}};kt.registerKTX2(h2);check('full profile uses an ownership-isolating adapter',h2.l!==loaderInstance);const fullDelivered=await load(h2.l);check('full GLB retains every mip byte and original GPU source identity',fullDelivered!==original&&fullDelivered.source===original.source&&fullDelivered.mipmaps.length===original.mipmaps.length&&fullDelivered.mipmaps.every((m,i)=>m.data===original.mipmaps[i].data&&m!==original.mipmaps[i]));
current=new THREE.CompressedTexture([{width:1,height:1,data:new Uint8Array(16)}],1,1);kt.initKTX2({}, {textures:'light'});const h3={setKTX2Loader(l){this.l=l}};kt.registerKTX2(h3);const one=await load(h3.l);check('single-mip texture remains valid',one.image.width===1&&one.mipmaps.length===1&&one.mipmaps[0].data.byteLength===16);

// Exercise the real pinned GLTFLoader image/sampler/shared-source integration.
const dataModule=s=>`data:text/javascript;base64,${Buffer.from(s).toString('base64')}`;
const vendor=`${root}/renderers/web/vendor/three-0.185.1/addons`;
const buffersModule=dataModule((await fs.readFile(`${vendor}/utils/BufferGeometryUtils.js`,'utf8')).replace("from 'three'",`from '${threeUrl}'`));
const skeletonModule=dataModule((await fs.readFile(`${vendor}/utils/SkeletonUtils.js`,'utf8')).replace("from 'three'",`from '${threeUrl}'`));
const gltfModule=dataModule((await fs.readFile(`${vendor}/loaders/GLTFLoader.js`,'utf8')).replace("from 'three'",`from '${threeUrl}'`).replace("from '../utils/BufferGeometryUtils.js'",`from '${buffersModule}'`).replace("from '../utils/SkeletonUtils.js'",`from '${skeletonModule}'`));
const {GLTFLoader}=await import(gltfModule);globalThis.self=globalThis;
const bin=Buffer.alloc(60);new Float32Array(bin.buffer,bin.byteOffset,9).set([0,0,0,1,0,0,0,1,0]);new Uint16Array(bin.buffer,bin.byteOffset+36,3).set([0,1,2]);
const spec={asset:{version:'2.0'},buffers:[{byteLength:60}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36},{buffer:0,byteOffset:36,byteLength:6},{buffer:0,byteOffset:44,byteLength:16}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[0,0,0],max:[1,1,0]},{bufferView:1,componentType:5123,count:3,type:'SCALAR'}],images:[{bufferView:2,mimeType:'image/ktx2'}],samplers:[{wrapS:10497,wrapT:10497},{wrapS:33071,wrapT:33071}],textures:[{sampler:0,extensions:{KHR_texture_basisu:{source:0}}},{sampler:1,extensions:{KHR_texture_basisu:{source:0}}}],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0},metallicFactor:0,roughnessFactor:1},emissiveTexture:{index:1}}],meshes:[{primitives:[{attributes:{POSITION:0},indices:1,material:0}]}],nodes:[{mesh:0}],scenes:[{nodes:[0]}],scene:0,extensionsUsed:['KHR_texture_basisu'],extensionsRequired:['KHR_texture_basisu']};
const jsonText=JSON.stringify(spec),json=Buffer.from(jsonText+' '.repeat((4-jsonText.length%4)%4));const glb=Buffer.alloc(28+json.length+bin.length);glb.writeUInt32LE(0x46546c67,0);glb.writeUInt32LE(2,4);glb.writeUInt32LE(glb.length,8);glb.writeUInt32LE(json.length,12);glb.writeUInt32LE(0x4e4f534a,16);json.copy(glb,20);glb.writeUInt32LE(bin.length,20+json.length);glb.writeUInt32LE(0x004e4942,24+json.length);bin.copy(glb,28+json.length);
current=texture();kt.initKTX2({}, {textures:'light'});const gltfLoader=new GLTFLoader();kt.registerKTX2(gltfLoader);shareImageSources(gltfLoader,{keepEncoded:true});
const parse=()=>new Promise((r,j)=>gltfLoader.parse(glb.buffer.slice(glb.byteOffset,glb.byteOffset+glb.byteLength),'',r,j));
const realA=await parse(),realB=await parse();const matA=realA.scene.children[0].material,matB=realB.scene.children[0].material;
check('real GLTFLoader receives reduced embedded basecolor and emissive images',matA.map.image.width===128&&matA.emissiveMap.image.width===128);
check('real GLTFLoader preserves distinct sampler settings',matA.map.wrapS===THREE.RepeatWrapping&&matA.emissiveMap.wrapS===THREE.ClampToEdgeWrapping);
check('two real GLTF parses share reduced image source identity',matA.map.source===matB.map.source&&matA.map!==matB.map);
check('real GLTFLoader full transcoder cache remains unmodified',current.image.width===256&&current.mipmaps.length===9&&current.mipmaps.every(m=>m.data.byteLength>0));

const {createTextureResidency}=await moduleFor('texture-residency.js');

// Combined real-parser + adapter + release + cached reread + revisit lifecycle.
async function combined(profile) {
  current=texture();const cached=current;kt.initKTX2({}, {textures:profile});
  const loader=new GLTFLoader();kt.registerKTX2(loader);shareImageSources(loader,{keepEncoded:true});
  const parse=()=>new Promise((r,j)=>loader.parse(glb.buffer.slice(glb.byteOffset,glb.byteOffset+glb.byteLength),'',r,j));
  const asset=await parse(),material=asset.scene.children[0].material;
  const expected=material.map.mipmaps.map(m=>Buffer.from(m.data));
  const originalPayload=cached.mipmaps.map(m=>Buffer.from(m.data));
  const props=new WeakMap;const get=o=>{if(!props.has(o))props.set(o,{});return props.get(o)};
  let uploads=[];const renderer={properties:{get},initTexture(t){uploads.push(t.mipmaps.map(m=>Buffer.from(m.data)));Object.assign(get(t),{__webglTexture:{},__version:t.version})}};
  renderer.initTexture(material.map);renderer.initTexture(material.emissiveMap);
  const r=createTextureResidency({group:asset.scene,renderer,tier:profile==='light'?'light':'full',closeImages:false,releaseCompressedLevels:true});
  r.prime(new THREE.Vector3());
  check(`${profile}: combined real parser delivery releases uploaded mip arrays`,material.map.mipmaps.every(m=>m.data.byteLength===0)&&r.state.released===1);
  check(`${profile}: combined release keeps cached raw full payloads exact`,cached.mipmaps.every((m,i)=>Buffer.from(m.data).equals(originalPayload[i])));
  const next=await parse(),nextMap=next.scene.children[0].material.map;
  check(`${profile}: cached real GLTF reread after release gets populated exact selected mips`,nextMap.mipmaps.length===expected.length&&nextMap.mipmaps.every((m,i)=>Buffer.from(m.data).equals(expected[i])));
  r.tick(new THREE.Vector3(1000,0,0));r.tick(new THREE.Vector3());await new Promise(r=>setTimeout(r,0));r.tick(new THREE.Vector3());
  check(`${profile}: combined original GLTF residency revisit uploads exact selected bytes`,r.state.retranscodes===1&&r.state.pending===0&&uploads.at(-1).length===expected.length&&uploads.at(-1).every((m,i)=>m.equals(expected[i])));
  check(`${profile}: combined refill preserves full cache and reports zero errors`,cached.mipmaps.every((m,i)=>Buffer.from(m.data).equals(originalPayload[i]))&&r.state.problems.length===0);
}
await combined('full');await combined('light');

async function fixture({encoded=true,release=true,uploaded=true,failRefill=false}={}){
 let full=texture();const payloads=full.mipmaps.map(m=>Buffer.from(m.data));let refills=0;let gpuPayloads=[];
 const imageLoader={load(url,onLoad,onProgress,onError){refills++;queueMicrotask(()=>failRefill?onError(new Error('controlled refill failure')):onLoad(texture()))}};
 class Parser{constructor(){this.json={images:[{bufferView:0,mimeType:'image/ktx2'}]};this.sourceCache={};}getDependency(){return Promise.resolve(new Uint8Array([1,2,3]).buffer)}loadImageSource(){return Promise.resolve(full)}}
 const ll={plugins:[],register(f){this.plugins.push(f)}};shareImageSources(ll,{keepEncoded:encoded});const p=new Parser;for(const plug of ll.plugins)plug(p);const tex=await p.loadImageSource(0,imageLoader);
 const group=new THREE.Group;const mat=new THREE.MeshBasicMaterial({map:tex});const mesh=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),mat);group.add(mesh);
 const cache=new WeakMap;const get=o=>{if(!cache.has(o))cache.set(o,{});return cache.get(o)};
 const renderer={properties:{get},initTexture(t){gpuPayloads.push(t.mipmaps.map(m=>Buffer.from(m.data)));Object.assign(get(t),{__webglTexture:{},__version:t.version})}};
 if(uploaded)renderer.initTexture(tex);
 const residency=createTextureResidency({group,renderer,tier:'full',closeImages:false,releaseCompressedLevels:release});
 return{tex,mat,residency,payloads,renderer,get,refills:()=>refills,gpuPayloads};}
const f=await fixture();f.residency.prime(new THREE.Vector3());
check('desktop uploaded compressed source levels are released',f.tex.mipmaps.every(m=>m.data.byteLength===0)&&f.residency.state.released===1);
check('desktop original material and GPU handle remain unchanged',f.mat.map===f.tex&&f.get(f.tex).__webglTexture!==undefined);
f.residency.tick(new THREE.Vector3(1000,0,0));check('released source can become a populated tail-mip stand-in',f.mat.map!==f.tex&&f.mat.map.mipmaps.length>0&&f.mat.map.mipmaps.every(m=>m.data.byteLength>0));
f.residency.tick(new THREE.Vector3());await new Promise(r=>setTimeout(r,0));f.residency.tick(new THREE.Vector3());
check('returning source is transcoded exactly once',f.refills()===1&&f.residency.state.retranscodes===1);
check('restored desktop uploads every original mip byte exactly',f.gpuPayloads.at(-1).length===f.payloads.length&&f.payloads.every((b,i)=>b.equals(f.gpuPayloads.at(-1)[i])));
check('restored desktop returns to original material slot',f.mat.map===f.tex&&f.residency.state.resident===1&&f.residency.state.pending===0);
check('refilled arrays release again after upload',f.tex.mipmaps.every(m=>m.data.byteLength===0)&&f.residency.state.released===2);
check('desktop roundtrip reports zero problems',f.residency.state.problems.length===0);
const unencoded=await fixture({encoded:false});unencoded.residency.prime(new THREE.Vector3());check('source without encoded recovery is never released',unencoded.tex.mipmaps.every(m=>m.data.byteLength>0));
const disabled=await fixture({release:false});disabled.residency.prime(new THREE.Vector3());check('legacy desktop option retains source levels',disabled.tex.mipmaps.every(m=>m.data.byteLength>0));
const pending=await fixture({uploaded:false});pending.residency.prime(new THREE.Vector3());check('source awaiting GPU upload keeps every byte',pending.tex.mipmaps.every(m=>m.data.byteLength>0));
const denied=await fixture({failRefill:true});denied.residency.prime(new THREE.Vector3());denied.residency.tick(new THREE.Vector3(1000,0,0));denied.residency.tick(new THREE.Vector3());await new Promise(r=>setTimeout(r,0));denied.residency.tick(new THREE.Vector3());
check('failed encoded refill reports the real decoding failure',denied.residency.state.problems.some(p=>p.includes('controlled refill failure')));
check('failed encoded refill keeps the valid stand-in without a pending upload',denied.mat.map!==denied.tex&&denied.residency.state.pending===0&&denied.mat.map.mipmaps.every(m=>m.data.byteLength>0));
// Desktop keeps decoded regular images, so only compressed recovery copies are retained.
const oldDocument = globalThis.document, oldBitmap = globalThis.ImageBitmap;
const hadDocument = Object.hasOwn(globalThis, 'document'), hadBitmap = Object.hasOwn(globalThis, 'ImageBitmap');
let canvasCreates = 0, canvasDraws = 0;
class ImageBitmapDouble {
  constructor(width = 1024, height = 512) { this.width = width; this.height = height; this.closed = false; }
  close() { this.closed = true; this.width = 0; this.height = 0; }
}
globalThis.ImageBitmap = ImageBitmapDouble;
globalThis.document = { createElement(kind) {
  assert.equal(kind, 'canvas'); canvasCreates++;
  return { width: 0, height: 0, getContext() { return { drawImage(image) {
    assert(image.width > 0 && image.height > 0, 'Stand-in must be drawn from a live decoded image'); canvasDraws++;
  } }; } };
} };
async function retainedSource(mode, compressed = false) {
  const original = compressed ? texture() : new THREE.Texture(new ImageBitmapDouble());
  let decodes = 0;
  const imageLoader = { load(url, onLoad) {
    decodes++; queueMicrotask(() => onLoad(compressed ? texture() : new ImageBitmapDouble()));
  } };
  class Parser {
    constructor() { this.json = { images: [{ bufferView: 0, mimeType: compressed ? 'image/ktx2' : 'image/png' }] }; this.sourceCache = {}; }
    getDependency() { return Promise.resolve(new TextEncoder().encode(`retention-${mode}-${compressed}`).buffer); }
    loadImageSource() { return Promise.resolve(original); }
  }
  const loader = { plugins: [], register(fn) { this.plugins.push(fn); } };
  shareImageSources(loader, { keepEncoded: mode });
  const parser = new Parser(); for (const plugin of loader.plugins) plugin(parser);
  const delivered = await parser.loadImageSource(0, imageLoader);
  return { original, delivered, record: glbImageSource(delivered.source), decodes: () => decodes };
}
for (const [mode, expectRegular, expectCompressed] of [[false, false, false], [true, true, true], ['compressed', false, true]]) {
  const regular = await retainedSource(mode, false), compressed = await retainedSource(mode, true);
  check(`${mode}: regular image retains its source record`, regular.record !== null);
  check(`${mode}: regular encoded retention matches the explicit mode`, !!regular.record.encoded === expectRegular);
  check(`${mode}: compressed encoded retention matches the explicit mode`, !!compressed.record.encoded === expectCompressed);
}
const { closeUploadedImages } = await moduleFor('upload-release.js');
async function lifecycleImage({ mode = 'compressed', compressed = false, close = false, uploaded = true } = {}) {
  const item = await retainedSource(mode, compressed), material = new THREE.MeshBasicMaterial({ map: item.delivered });
  const group = new THREE.Group(); group.add(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), material));
  const props = new WeakMap(); const get = (key) => { if (!props.has(key)) props.set(key, {}); return props.get(key); };
  let uploads = 0;
  const renderer = { properties: { get }, initTexture(tex) {
    uploads++; Object.assign(get(tex), { __webglTexture: {}, __version: tex.version });
    get(tex.source).__version = tex.source.version;
  } };
  const residency = createTextureResidency({ group, renderer, closeImages: close, releaseCompressedLevels: true });
  // Native boot prepares stand-ins first, then uploads the selected original map.
  if (uploaded) renderer.initTexture(item.delivered);
  return { ...item, material, group, renderer, residency, uploads: () => uploads };
}
const canvasBeforeRegular = canvasCreates;
const regularDesktop = await lifecycleImage(); regularDesktop.residency.prime(new THREE.Vector3());
check('desktop regular source creates no eager stand-in canvas', canvasCreates === canvasBeforeRegular && regularDesktop.residency.state.standIns === 0);
check('desktop regular source keeps decoded image open without encoded duplicate', !regularDesktop.delivered.image.closed && regularDesktop.record.encoded === null);
const regularSource = regularDesktop.delivered.source;
regularDesktop.residency.tick(new THREE.Vector3(1000, 0, 0));
check('desktop regular source lazily creates valid stand-in on actual eviction', canvasCreates === canvasBeforeRegular + 1 && canvasDraws > 0
  && regularDesktop.residency.state.evictions === 1 && regularDesktop.material.map !== regularDesktop.delivered);
regularDesktop.residency.tick(new THREE.Vector3());
check('desktop regular return reuses the live original image and Source', regularDesktop.material.map === regularDesktop.delivered
  && regularDesktop.material.map.source === regularSource && !regularDesktop.delivered.image.closed);
check('desktop regular return uploads without decoding or pending work', regularDesktop.decodes() === 0 && regularDesktop.uploads() === 2
  && regularDesktop.residency.state.pending === 0 && regularDesktop.residency.state.problems.length === 0);
const recoverableDesktop = await lifecycleImage({ compressed: true });
check('desktop recoverable compressed source eagerly prepares its tail stand-in', recoverableDesktop.residency.state.standIns === 1 && !!recoverableDesktop.record.encoded);
recoverableDesktop.residency.prime(new THREE.Vector3());
check('desktop recoverable compressed source releases only after upload', recoverableDesktop.delivered.mipmaps.every((m) => m.data.byteLength === 0));
recoverableDesktop.residency.tick(new THREE.Vector3(1000, 0, 0)); recoverableDesktop.residency.tick(new THREE.Vector3());
await new Promise((resolve) => setTimeout(resolve, 0)); recoverableDesktop.residency.tick(new THREE.Vector3());
check('desktop compressed-only mode recovers through actual encoded refill path', recoverableDesktop.decodes() === 1
  && recoverableDesktop.material.map === recoverableDesktop.delivered && recoverableDesktop.residency.state.pending === 0
  && recoverableDesktop.residency.state.problems.length === 0);
const noRecovery = await lifecycleImage({ mode: false, compressed: true });
check('compressed source without encoded recovery does not eagerly allocate a stand-in', noRecovery.residency.state.standIns === 0);
noRecovery.residency.prime(new THREE.Vector3());
check('compressed source without encoded recovery retains every original level', noRecovery.delivered.mipmaps.every((m) => m.data.byteLength > 0));
const phone = await lifecycleImage({ mode: true, close: true });
check('phone true/all mode still eagerly prepares regular bitmap stand-in', phone.residency.state.standIns === 1 && !!phone.record.encoded);
phone.residency.prime(new THREE.Vector3()); closeUploadedImages(phone.group, phone.renderer);
check('phone native uploaded-image release still closes its original bitmap', phone.delivered.image.closed);
phone.residency.tick(new THREE.Vector3(1000, 0, 0)); phone.residency.tick(new THREE.Vector3());
await new Promise((resolve) => setTimeout(resolve, 0)); phone.residency.tick(new THREE.Vector3());
check('phone true/all mode decodes, uploads and closes returning image', phone.decodes() === 1 && phone.material.map === phone.delivered
  && phone.delivered.image.closed && phone.residency.state.redecodes === 1 && phone.residency.state.pending === 0
  && phone.residency.state.problems.length === 0);
if (hadDocument) globalThis.document = oldDocument; else delete globalThis.document;
if (hadBitmap) globalThis.ImageBitmap = oldBitmap; else delete globalThis.ImageBitmap;

console.log(`${tests.length} controls PASS; NO actual-browser/GPU/memory/visual qualification claimed`);
if(hadLoader)globalThis.__T3173KTX2Loader=previousLoader;else delete globalThis.__T3173KTX2Loader;
if(hadSelf)globalThis.self=previousSelf;else delete globalThis.self;
