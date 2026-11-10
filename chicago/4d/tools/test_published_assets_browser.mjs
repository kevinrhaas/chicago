/** Small real HTTP/Chromium fixture; no whole-world or photographic acceptance claim. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';
import { writeYearPacks, checkYearPacks } from './write_year_packs.mjs';
import { assetAliasIdInput } from '../renderers/web/js/published-assets.js';

const args = process.argv.slice(2);
const option = (name) => { const at = args.indexOf(name); return at < 0 ? null : args[at + 1]; };
const output = option('--output'), ktxSource = option('--ktx-source');
if (!args.includes('--check') || !output || !ktxSource || args.length !== 5)
  throw new Error('Use --check --output DIR --ktx-source FILE');
fs.mkdirSync(output, { recursive: true });
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'asset-browser-'));
const source = path.resolve(new URL('..', import.meta.url).pathname);
const site = path.join(tmp, 'site'), production = path.join(site, '4d'), dev = path.join(production, 'dev');
const write = (file, bytes) => { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes); };
const sheetBytes = fs.readFileSync(ktxSource), sheetRel = `data/gltf/sheets/${sha(sheetBytes).slice(0, 16)}.ktx2`;
function triangle(bufferView = true) {
  const geometry = Buffer.from(new Float32Array([-1,-1,0, 1,-1,0, 0,1,0, 0,0, 1,0, 0.5,1]).buffer);
  const json = { asset: { version: '2.0' }, extensionsUsed: ['KHR_texture_basisu'], extensionsRequired: ['KHR_texture_basisu'],
    buffers: [{ byteLength: geometry.length }], bufferViews: [{ buffer:0, byteOffset:0, byteLength:36 },{ buffer:0, byteOffset:36, byteLength:24 }],
    accessors: [{ bufferView:0, componentType:5126, count:3, type:'VEC3', min:[-1,-1,0],max:[1,1,0] },
      { bufferView:1, componentType:5126, count:3, type:'VEC2' }],
    images:[{ uri:`sheets/${path.basename(sheetRel)}` }], textures:[{ extensions:{ KHR_texture_basisu:{ source:0 } } }],
    materials:[{ pbrMetallicRoughness:{ baseColorTexture:{ index:0 },metallicFactor:0,roughnessFactor:1 },doubleSided:true }],
    meshes:[{ primitives:[{ attributes:{ POSITION:0,TEXCOORD_0:1 },material:0 }] }],nodes:[{ mesh:0 }],scenes:[{ nodes:[0] }],scene:0 };
  if(bufferView){json.buffers.push({uri:`sheets/${path.basename(sheetRel)}`,byteLength:sheetBytes.length});
    json.bufferViews.push({buffer:1,byteOffset:0,byteLength:sheetBytes.length});json.images=[{bufferView:2,mimeType:'image/ktx2'}];}
  let j=Buffer.from(JSON.stringify(json));j=Buffer.concat([j,Buffer.alloc((4-j.length%4)%4,32)]);
  const h=Buffer.alloc(20);h.writeUInt32LE(0x46546c67);h.writeUInt32LE(2,4);h.writeUInt32LE(28+j.length+geometry.length,8);
  h.writeUInt32LE(j.length,12);h.writeUInt32LE(0x4e4f534a,16);
  const b=Buffer.alloc(8);b.writeUInt32LE(geometry.length);b.writeUInt32LE(0x004e4942,4);
  return Buffer.concat([h,j,b,geometry]);
}
const fullRel='data/gltf/glessner_house__as_built_1887.glb', lightRel='data/gltf/fixture-light.glb';
const uriRelA='data/gltf/fixture-uri-a.glb',uriRelB='data/gltf/fixture-uri-b.glb';
const bytes=triangle(),uriBytes=triangle(false),payloads={ [fullRel]:bytes,[lightRel]:bytes,[uriRelA]:uriBytes,[uriRelB]:uriBytes,[sheetRel]:sheetBytes,
  'data/prebuilt/1835/ground.bin.gz':Buffer.from('not geometry: alias buffer integrity fixture') };
const aliases=Object.fromEntries(Object.entries(payloads).map(([rel,b])=>[rel,{source:`/4d/${rel}`,sha256:sha(b),bytes:b.length}]));
const catalogue={schema:1,scope:'/4d/dev/',productionScope:'/4d/',id:sha(assetAliasIdInput(aliases)),aliases};
const catName=`asset-aliases.${catalogue.id}.json`;
const moduleScript=`
import * as THREE from 'three';
import { initKTX2, registerKTX2 } from './js/ktx2.js';
import { loadScene, detailAssetPath } from './js/scene-loader.js';
import { createYearPack } from './js/year-pack.js';
import { fetchPublishedAssetBytes, publishedAssetAddress } from './js/published-assets.js';
const renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setSize(160,160);document.body.append(renderer.domElement);
initKTX2(renderer,{textures:'full'});
const bases={dataBase:new URL('../data/',document.baseURI),assetBase:new URL('../data/',document.baseURI),sourceAssetLayout:false};
const pack=createYearPack({year:'1904',mount:document.querySelector('#pack'),base:document.baseURI});
const fixture={pack,fetchPublishedAssetBytes,publishedAssetAddress,logical:new URL('${fullRel}',new URL('../',document.baseURI)).href};window.fixture=fixture;
fixture.ready=(async()=>{await pack.ready;const loaded=await loadScene('1904',bases,{detail:'full',keepAssetBytes:false});
if(loaded.problems.length)throw new Error(JSON.stringify(loaded.problems));const record=loaded.registry.get('glessner_house');
const scene=new THREE.Scene();scene.background=new THREE.Color(0x202020);scene.add(record.gltf.scene);scene.add(new THREE.AmbientLight(0xffffff,3));
const camera=new THREE.PerspectiveCamera(50,1,0.1,10);camera.position.z=3;renderer.render(scene,camera);
const map=record.gltf.scene.children[0].material.map;const companion=loaded.registry.get('fixture_companion').gltf.scene.children[0].material.map;
const uriA=loaded.registry.get('fixture_uri_a').gltf.scene.children[0].material.map;const uriB=loaded.registry.get('fixture_uri_b').gltf.scene.children[0].material.map;
fixture.result={assetUrl:record.assetUrl,light:detailAssetPath(record,'light'),sourcesShared:map.source===companion.source,uriSourcesShared:uriA.source===uriB.source,
width:map.image.width,height:map.image.height,mips:map.mipmaps.length,programs:renderer.info.programs.length};
const pixel=new Uint8Array(4);renderer.getContext().readPixels(80,80,1,1,renderer.getContext().RGBA,renderer.getContext().UNSIGNED_BYTE,pixel);
fixture.result.pixel=[...pixel];return fixture.result;})();fixture.ready.catch(e=>{fixture.error=String(e.stack||e);});
`;
function html(withAlias) { return `<!doctype html><html><head><base href="/4d/dev/walk/">${withAlias?`<meta name="c4d-asset-aliases" content="/4d/dev/${catName}" data-sha256="${catalogue.id}">`:''}
<script type="importmap">{"imports":{"three":"./vendor/three-0.185.1/three.module.js","three/addons/":"./vendor/three-0.185.1/addons/"}}</script></head><body><div id="pack"></div><script type="module">${moduleScript}</script></body></html>`; }
fs.cpSync(path.join(source,'renderers/web/js'),path.join(dev,'walk/js'),{recursive:true});
fs.cpSync(path.join(source,'renderers/web/vendor/three-0.185.1'),path.join(dev,'walk/vendor/three-0.185.1'),{recursive:true});
for(const [rel,b]of Object.entries(payloads)){write(path.join(production,rel),b);write(path.join(dev,rel),b);}
write(path.join(dev,'build.json'),'{}');
write(path.join(dev,'data/datum.json'),'{}');
for(const year of ['1812','1835','1904']){write(path.join(dev,`data/scenes/${year}.json`),JSON.stringify({id:year}));write(path.join(dev,`${year}/index.html`),html(false));}
write(path.join(dev,'data/sidecars/1904/index.json'),JSON.stringify({structures:['glessner_house','fixture_companion','fixture_uri_a','fixture_uri_b']}));
write(path.join(dev,'data/sidecars/1904/glessner_house.json'),JSON.stringify({id:'glessner_house',asset:fullRel.slice(5),asset_lods:{light:lightRel.slice(5)}}));
write(path.join(dev,'data/sidecars/1904/fixture_companion.json'),JSON.stringify({id:'fixture_companion',asset:lightRel.slice(5)}));
for(const [id,rel]of [['fixture_uri_a',uriRelA],['fixture_uri_b',uriRelB]])write(path.join(dev,`data/sidecars/1904/${id}.json`),JSON.stringify({id,asset:rel.slice(5)}));
write(path.join(dev,'walk/index.html'),html(false));writeYearPacks(dev);
const baseline=execFileSync('git',['-C',path.resolve(source,'../..'),'show','6f2ebb8107815a47dda0e3e7f4416665ad70d57d:chicago/4d/offline/sw.js']);
write(path.join(dev,'sw.js'),baseline);write(path.join(production,'sw.js'),baseline);
let server,browser,context,coexistence;const errors=[],requests=[],phases=[];let online=true;const started=Date.now();
const phase=(name,details={})=>{const row={phase:name,seconds:(Date.now()-started)/1000,...details};phases.push(row);console.log(JSON.stringify(row));};
const waitFor=async(fn)=>{for(let i=0;i<100;i++){if(await fn())return;await new Promise(r=>setTimeout(r,50));}throw new Error('Bounded worker condition not met');};
try{
 server=http.createServer((req,res)=>{const u=new URL(req.url,'http://localhost');requests.push({path:u.pathname,query:u.search,online});
  if(!online){res.destroy();return;}const file=path.resolve(site,'.'+decodeURIComponent(u.pathname));
  if(!file.startsWith(site+path.sep)){res.writeHead(403);res.end();return;}
  let actual=file;try{if(fs.statSync(actual).isDirectory())actual=path.join(actual,'index.html');const data=fs.readFileSync(actual);
  const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.wasm':'application/wasm','.ktx2':'image/ktx2','.glb':'model/gltf-binary','.webmanifest':'application/manifest+json'}[path.extname(actual)];
  res.writeHead(200,{'Content-Type':mime||'application/octet-stream','Cache-Control':'no-store'});res.end(data);
  }catch{res.writeHead(404);res.end();}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 browser=await chromium.launch({headless:true,executablePath:process.env.PW_EXECUTABLE||process.env.PW_CHROMIUM||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});context=await browser.newContext({viewport:{width:390,height:780}});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));const cdp=await context.newCDPSession(page);const versions=new Map();
 cdp.on('ServiceWorker.workerVersionUpdated',({versions:rows})=>{for(const v of rows)versions.set(v.versionId,v);});await cdp.send('ServiceWorker.enable');
 await page.goto(origin+'/4d/dev/walk/');await page.waitForFunction(()=>window.fixture?.result||window.fixture?.error);assert.equal(await page.evaluate(()=>fixture.error),undefined);
 const sourceResult=await page.evaluate(()=>fixture.result);assert(sourceResult.programs>0&&sourceResult.width>0&&sourceResult.sourcesShared&&sourceResult.uriSourcesShared);phase('source-default-real-KTX2-WebGL-both-native-buffer-and-image-URI',sourceResult);
 await page.evaluate(()=>fixture.pack.install());assert.equal(await page.evaluate(()=>fixture.pack.state.status),'kept');phase('old-classic-worker-installed');
 await waitFor(()=>[...versions.values()].some(v=>v.scriptURL===origin+'/4d/dev/sw.js'&&v.status==='activated'));
 const oldVersion=[...versions.values()].find(v=>v.scriptURL===origin+'/4d/dev/sw.js'&&v.status==='activated').versionId;
 write(path.join(dev,catName),JSON.stringify(catalogue));for(const rel of Object.keys(payloads))fs.unlinkSync(path.join(dev,rel));
 write(path.join(dev,'walk/index.html'),html(true));for(const year of ['1812','1835','1904'])write(path.join(dev,`${year}/index.html`),html(true));
 writeYearPacks(dev);assert.deepEqual(checkYearPacks(dev),[]);phase('alias-publication-native-pack-check');
 await page.reload();await page.waitForFunction(()=>window.fixture?.result||window.fixture?.error);assert.equal(await page.evaluate(()=>fixture.error),undefined);
 await page.evaluate(()=>fixture.pack.settled());assert.equal(await page.evaluate(()=>fixture.pack.state.status),'kept');
 await page.evaluate(async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();});
 await waitFor(()=>[...versions.values()].some(v=>v.scriptURL===origin+'/4d/dev/sw.js'&&v.status==='activated'&&v.versionId!==oldVersion));
 phase('actual-old-to-new-worker-transition',{oldVersion});
 // A separately controlled DEV document with only an OLD production pack must
 // bypass that worker's stale production bytes without unregistering it.
 coexistence=await browser.newContext({viewport:{width:390,height:780}});const legacy=await coexistence.newPage();
 legacy.on('pageerror',e=>errors.push(String(e)));
 await legacy.goto(origin+'/4d/dev/walk/');await legacy.waitForFunction(()=>window.fixture?.result||window.fixture?.error);
 assert.equal(await legacy.evaluate(()=>fixture.error),undefined);
 await legacy.evaluate(async({rel,length})=>{
  const cache=await caches.open('c4d-pack /4d/ 1904');
  await cache.put(new URL('/4d/'+rel,location.href),new Response(new Uint8Array(length)));
  await cache.put(new URL('/4d/__pack__.json',location.href),new Response(JSON.stringify({files:[[rel,'old',length]],network_first:[]})));
  await navigator.serviceWorker.register('/4d/sw.js',{scope:'/4d/'});await navigator.serviceWorker.ready;
 },{rel:fullRel,length:bytes.length});
 await legacy.waitForFunction(()=>navigator.serviceWorker.controller?.scriptURL.endsWith('/4d/sw.js'));
 const stale=await legacy.evaluate(async rel=>[...new Uint8Array(await(await fetch('/4d/'+rel)).arrayBuffer())],fullRel);
 assert(Buffer.from(stale).equals(Buffer.alloc(bytes.length)),'actual old production worker serves its stale cached body without bypass');
 await legacy.reload();await legacy.waitForFunction(()=>window.fixture?.result||window.fixture?.error);assert.equal(await legacy.evaluate(()=>fixture.error),undefined);
 assert.deepEqual(await legacy.evaluate(()=>fixture.result),sourceResult);
 const scopes=await legacy.evaluate(async()=>[...(await navigator.serviceWorker.getRegistrations())].map(r=>new URL(r.scope).pathname));
 assert.deepEqual(scopes,['/4d/']);phase('actual-old-PROD-worker-controls-DEV-fresh-alias-bypass',{scopes});
 await coexistence.close();coexistence=null;
 await page.reload();await page.waitForFunction(()=>window.fixture?.result||window.fixture?.error);assert.equal(await page.evaluate(()=>fixture.error),undefined);
 const aliasResult=await page.evaluate(()=>fixture.result);assert.deepEqual(aliasResult,sourceResult);phase('alias-real-KTX2-WebGL-matches-default',aliasResult);
 await page.screenshot({path:path.join(output,'native-alias-fixture.png')});
 online=false;await context.setOffline(true);await page.reload();await page.waitForFunction(()=>window.fixture?.result||window.fixture?.error);assert.equal(await page.evaluate(()=>fixture.error),undefined);
 assert.deepEqual(await page.evaluate(()=>fixture.result),sourceResult);phase('warm-offline-page-KTX2-reload');
 const running=[...versions.values()].findLast(v=>v.scriptURL===origin+'/4d/dev/sw.js'&&v.status==='activated'&&v.runningStatus==='running');assert(running);
 await cdp.send('ServiceWorker.stopWorker',{versionId:running.versionId});phase('actual-worker-stopped',{version:running.versionId});
 const cold=await page.evaluate(async()=>{const b=await fixture.fetchPublishedAssetBytes(fixture.logical);return [...new Uint8Array(b)];});assert(Buffer.from(cold).equals(bytes));phase('cold-worker-first-request-is-canonical-alias');
 const controls=await page.evaluate(async()=>{
  const fail=async(p)=>{try{await p;return false;}catch{return true;}};
  const address=await fixture.publishedAssetAddress(fixture.logical);const cache=await caches.open('c4d-pack /4d/dev/ 1904');
  const saved=await cache.match(fixture.logical);const body=await saved.clone().arrayBuffer();
  const unknown=new URL(address.source);unknown.pathname='/4d/data/gltf/unknown.glb';
  const unknownRejected=await fail(fetch(unknown));
  const arbitrary=new URL(address.source);arbitrary.pathname='/unrelated.bin';const arbitraryRejected=await fail(fetch(arbitrary));
  const plain=await (await fetch(fixture.logical)).arrayBuffer();
  const rangeRejected=await fail(fetch(address.source,{headers:{Range:'bytes=0-1'}}));
  const browser206Rejected=await fail(cache.put(fixture.logical,new Response(new Uint8Array([1]),{status:206,headers:{'Content-Range':'bytes 0-0/'+body.byteLength}})));
  await cache.put(fixture.logical,new Response(new Uint8Array([1]),{status:200,headers:{'Content-Range':'bytes 0-0/'+body.byteLength}}));
  const partialRejected=await fail(fixture.fetchPublishedAssetBytes(fixture.logical));
  const logicalPartialRejected=await fail(fetch(fixture.logical));
  await cache.put(fixture.logical,new Response(new Uint8Array([1])));
  const shortRejected=await fail(fixture.fetchPublishedAssetBytes(fixture.logical));
  await cache.put(fixture.logical,new Response(new Uint8Array(body.byteLength)));
  const corruptionRejected=await fail(fixture.fetchPublishedAssetBytes(fixture.logical));
  await cache.put(fixture.logical,saved);
  const prod=await caches.open('c4d-pack /4d/ 1904');await prod.put(new URL('/4d/data/gltf/glessner_house__as_built_1887.glb',location.href),new Response(new Uint8Array(body.byteLength)));
  const isolated=await fixture.fetchPublishedAssetBytes(fixture.logical);
  return{unknownRejected,arbitraryRejected,rangeRejected,browser206Rejected,partialRejected,logicalPartialRejected,shortRejected,corruptionRejected,plain:[...new Uint8Array(plain)],isolated:[...new Uint8Array(isolated)]};
 });
 for(const key of ['unknownRejected','arbitraryRejected','rangeRejected','browser206Rejected','partialRejected','logicalPartialRejected','shortRejected','corruptionRejected'])assert(controls[key],key);
 assert(Buffer.from(controls.plain).equals(bytes));assert(Buffer.from(controls.isolated).equals(bytes));phase('exact-allowlist-full-body-range-and-cache-isolation-controls');
 assert.deepEqual(errors,[]);
 const result={status:'PASS',seconds:(Date.now()-started)/1000,sourceResult,aliasResult,controls:Object.fromEntries(Object.entries(controls).filter(([k])=>!['plain','isolated'].includes(k))),
 catalogueId:catalogue.id,ktxSourceSha256:sha(sheetBytes),ktxSourceBytes:sheetBytes.length,phases,pageErrors:errors,requestCount:requests.length,
 qualification:'Tiny real HTTP/classic service-worker/native GLTF/KTX2 fixture only; no full app, performance, published Pages or photo acceptance'};
 fs.writeFileSync(path.join(output,'RESULT.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}catch(error){fs.writeFileSync(path.join(output,'FAIL.json'),JSON.stringify({status:'FAIL',error:String(error.stack||error),phases,pageErrors:errors,requests},null,2)+'\n');throw error;}
finally{if(coexistence)await coexistence.close();if(context)await context.close();if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));fs.rmSync(tmp,{recursive:true,force:true});
 fs.writeFileSync(path.join(output,'OWNED-CLEANUP.json'),JSON.stringify({contextClosed:!!context,browserClosed:!!browser,serverClosed:!!server,fixtureRemoved:!fs.existsSync(tmp)},null,2)+'\n');}
