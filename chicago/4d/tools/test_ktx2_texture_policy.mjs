import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
if (process.argv.slice(2).some(x => x !== '--self-test')) throw new Error('Only --self-test is supported');
const proposed = await fs.readFile(new URL('../renderers/web/js/ktx2.js', import.meta.url), 'utf8');
async function moduleFor(profile, disabled = false) {
  const fixtures = new Map();
  const code = proposed.replace("import * as THREE from 'three';", `const THREE={SRGBColorSpace:'srgb',NoColorSpace:'linear'};`)
    .replace("import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';", `
class KTX2Loader {
 constructor(){this.workerPool={workerStatus:0,workersResolve:[()=>{}]};}
 detectSupport(){this.workerConfig={dxtSupported:true};return this;}
 dispose(){}
 load(url,onLoad,onProgress,onError){
  const f=globalThis.__mipPolicyFixtures.get(url);
  if(f instanceof Error){onError?.(f);return 'returned-error';}
  onProgress?.({loaded:1});onLoad?.(f());return 'returned-load';
 }
 loadAsync(url){return new Promise((resolve,reject)=>this.load(url,resolve,undefined,reject));}
}
`);
  globalThis.__mipPolicyFixtures = fixtures;
  const module = await import('data:text/javascript;base64,' + Buffer.from(code + `\n// profile ${profile}:${disabled}:${Math.random()}`).toString('base64'));
  module.initKTX2({}, {textures:profile,disabled});
  const gltf={setKTX2Loader(l){this.ktx2Loader=l;}};
  module.registerKTX2(gltf);
  return {module,fixtures,l:gltf.ktx2Loader};
}
function tex(size=1024, levels=11){return {isCompressedTexture:true,mipmaps:Array.from({length:levels},(_,i)=>({width:Math.max(1,size>>i),height:Math.max(1,size>>i),data:new Uint8Array(Math.max(16,(size>>i)**2))})),image:{width:size,height:size,depth:1},userData:{}};}
let checks=0;
for(const profile of ['full','light']){
 const {module,fixtures,l}=await moduleFor(profile);
 fixtures.set('initial',()=>tex());fixtures.set('reload',()=>tex());fixtures.set('sheet',()=>tex());fixtures.set('single',()=>tex(1,1));
 const load=url=>new Promise((resolve,reject)=>l.load(url,resolve,undefined,reject));
 const first=await load('initial'), reload=await load('reload'), sheet=await module.loadCompressed('sheet');
 const expected=profile==='light'?512:1024, count=profile==='light'?10:11;
 for(const image of [first,reload,sheet]){assert.equal(image.image.width,expected);assert.equal(image.image.height,expected);assert.equal(image.mipmaps.length,count);checks+=3;}
 assert.deepEqual(first.mipmaps.map(m=>[m.width,m.height]),reload.mipmaps.map(m=>[m.width,m.height]));checks++;
 fixtures.set('clone',()=>({...first,userData:{...first.userData},image:{...first.image},mipmaps:first.mipmaps.slice()}));
 const clone=await load('clone');assert.equal(clone.image.width,expected);assert.equal(clone.mipmaps.length,count);checks+=2;
 const single=await load('single');assert.equal(single.image.width,1);assert.equal(single.mipmaps.length,1);checks+=2;
 const originalBytes=tex().mipmaps.reduce((s,m)=>s+m.data.byteLength,0), kept=first.mipmaps.reduce((s,m)=>s+m.data.byteLength,0);
 assert.equal(kept,profile==='light'?originalBytes-1024*1024:originalBytes);checks++;
 assert.equal(l.workerPool.workersResolve[0],null);checks++;
 let progress=0;assert.equal(l.load('initial',()=>{},()=>progress++),'returned-load');assert.equal(progress,1);checks+=2;
 fixtures.set('error',new Error('decode refused'));let error;assert.equal(l.load('error',()=>assert.fail('must not load'),undefined,e=>error=e),'returned-error');assert.equal(error.message,'decode refused');checks+=2;
 console.log(JSON.stringify({profile,initialWidth:first.image.width,reloadWidth:reload.image.width,sheetWidth:sheet.image.width,keptLevels:count,keptBytes:kept,originalBytes}));
}
{
 const {fixtures,l}=await moduleFor('light',true);fixtures.set('rgba',()=>tex());const result=await new Promise(r=>l.load('rgba',r));assert.equal(result.image.width,512);assert.equal(result.mipmaps.length,10);assert.ok(Object.values(l.workerConfig).every(v=>!v));checks+=3;
}
console.log(`PASS ${checks} device texture policy checks. Mock loader verifies policy routing and dimensions, not browser/GPU or appearance.`);
