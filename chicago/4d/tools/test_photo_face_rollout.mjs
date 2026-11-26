// SPDX-License-Identifier: GPL-3.0-or-later
// A preview must reach generic adults without replacing a historical likeness or a child.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const root=new URL('../',import.meta.url);
const three=new URL('renderers/web/vendor/three-0.185.1/three.module.js',root).href;
registerHooks({resolve:(s,c,next)=>s==='three'?{url:three,shortCircuit:true}:next(s,c)});
const {parseVariationKit,attachPhotoLibrary,photoFaceFor,personVariation}=await import(new URL('renderers/web/js/human-variation.js',root));
const header=JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_kit.json',root)));
const bytes=await fs.readFile(new URL(`assets/humans/web/${header.bin}`,root));
const kit=parseVariationKit(header,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));kit.base='https://example.org/humans/web/hm08_variation_kit.json';
const library=JSON.parse(await fs.readFile(new URL('assets/humans/web/photo_faces/pilot/review.json',root)));
const {PhotoFacePages,PHOTO_FACE_BUDGET}=await import(new URL('renderers/web/js/photo-face-pages.js',root));
assert.equal(library.faces.length,256,'the requested library contains 256 prepared sources');
assert.equal(library.pages.length,16,'sixteen bounded pages provide the close detail');
assert.equal(new Set(library.faces.map(f=>f.id)).size,256);
assert.equal(library.faces.filter(f=>f.sex==='female').length,128);
const people=JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_persons.json',root))).persons;
const query={key:'sample',sex:'male',age:42};
assert.equal(photoFaceFor(kit,query),null,'the default stays on its ordinary library');
assert(attachPhotoLibrary(kit,library,new URL('photo_faces/pilot/review.json',kit.base)));
const face=photoFaceFor(kit,query);
assert.equal(face.sex,'male');assert.equal(photoFaceFor(kit,query).id,face.id);
assert.equal(photoFaceFor(kit,{...query,age:12}),null,'no adult face on a child');
assert.equal(photoFaceFor(kit,{...query,own:true}),null,'a historical portrait wins');
assert.equal(photoFaceFor(kit,{...query,pick:'body'}),null,'the visitor\'s choice wins');
assert.equal(attachPhotoLibrary(kit,{...library,textures:{light:{gpu_bytes_rgba8_mipmaps:6_000_000}}},kit.base),false,'the weak-machine atlas ceiling binds');
assert.equal(attachPhotoLibrary(kit,{...library,faces:[...library.faces,library.faces[0]]},kit.base),false,'capacity cannot silently exceed 256');
assert.equal(attachPhotoLibrary(kit,{...library,pages:[{textures:{full:{gpu_bytes_rgba8_mipmaps:6_000_000}}}]},kit.base),false,'oversized detail pages are refused');
const id='pa1904_armour_mrs_philip_d_c1900_joseph_daniels';
const v=personVariation({kit,key:id,record:people[id],assetId:'glessner_john_j_1904',sceneYear:1904});
assert(v.photoFace&&v.lib.url.endsWith('faces_light.jpg'),'an existing generic adult gets a photograph');
assert(v.lib.detail?.url.includes('page_')&&v.lib.detail.bytes<=PHOTO_FACE_BUDGET.pageBytes);
assert.equal(v.values.nose_width,v.photoFace.values.nose_width,'the source shapes the head too');
const other=personVariation({kit,key:id,record:people[id],assetId:'bardwell_otis_1835',sceneYear:1904});
assert.equal(other.photoFace.id,v.photoFace.id,'one person keeps one face across bodies');
const grey='pa1904_grey_w_l';
assert.equal(personVariation({kit,key:grey,record:people[grey],assetId:'glessner_john_j_1904',sceneYear:1904}).photoFace,null);
// Use every actual scene assignment, including carriage drivers and household rows.
const docs=new Map(),photoPeople=new Set(),usedFaces=new Set();let drawn=0,photographic=0,children=0,personal=0;
for(const [key,record] of Object.entries(people)){
  const chosen=[];
  for(const at of record.drawn_as??[]){
    const [file,row]=at.split('#');
    if(!docs.has(file))docs.set(file,JSON.parse(await fs.readFile(new URL(file,root))));
    const d=docs.get(file),assetId=row==null?d.appearance?.asset_id:d.people?.find(p=>p.person===row)?.asset_id??d.rows?.find(r=>r.id===row)?.driver_asset;
    assert(assetId,`${key}: its scene assignment names a real body`);
    const variant=personVariation({kit,key,record,assetId,sceneYear:Number(record.scene)||null});
    const protectedFace=!!record.face?.values||!!record.skin||!!record.looks?.face_pick;
    if(variant.age<18){assert.equal(variant.photoFace,null,`${key}: child protected`);children++;}
    else if(protectedFace){assert.equal(variant.photoFace,null,`${key}: personal face protected`);personal++;}
    else{
      assert(variant.photoFace,`${key}: generic adult reached by the photo preview`);
      assert.equal(variant.photoFace.sex,variant.sex,`${key}: compatible face source`);photographic++;photoPeople.add(key);usedFaces.add(variant.photoFace.id);
    }
    chosen.push(variant.photoFace?.id??null);
  }
  if(chosen.length){assert.equal(new Set(chosen).size,1,`${key}: one face across every drawn body`);drawn++;}
}
console.log(JSON.stringify({drawnPeople:drawn,genericPeople:photoPeople.size,distinctAssignedFaces:usedFaces.size,catalogFaces:library.faces.length,photoAssignments:photographic,childAssignmentsProtected:children,personalAssignmentsProtected:personal}));
// Exercise real asynchronous cache churn and late deliveries. A failed or evicted page
// must leave the crowd fallback available; pending decodes count against the same slot.
const deliveries=[],live=new Set(),released=[];let peak=0,loads=0,now=0;
const cache=new PhotoFacePages({schedule:null,now:()=>now,
  load:page=>{loads++;return new Promise((resolve,reject)=>deliveries.push({page,resolve,reject}));},
  dispose:t=>{assert(live.delete(t),'a page is released exactly once');released.push(t);}});
const page=i=>({url:`https://example.org/page_${i}.jpg`,bytes:5_592_406});
async function deliver(){await Promise.resolve();const d=deliveries.shift();assert(d);const t={url:d.page.url};live.add(t);peak=Math.max(peak,live.size);d.resolve(t);await new Promise(resolve=>setImmediate(resolve));}
cache.demand(page(0),2);cache.demand(page(1),1);cache.flush();await Promise.resolve();
assert.equal(deliveries[0].page.url,page(1).url,'the nearest visible page wins');
cache.demand(page(2),.5);cache.flush();assert.equal(loads,1,'camera movement cannot grow the pending decode queue');
await deliver();assert.equal(cache.get(page(1).url),null,'a late page is disposed without admission');
await deliver();assert(cache.get(page(2).url));
for(let i=3;i<32;i++){
  cache.demand(page(i),1);cache.flush();assert.equal(cache.stats().residentPages+cache.stats().pendingPages,1);
  assert(cache.stats().residentBytes+cache.stats().pendingBytes<=PHOTO_FACE_BUDGET.pageBytes);
  await deliver();assert(cache.get(page(i).url));assert.equal(live.size,1);
}
const beforeOversize=loads;cache.demand({...page(32),bytes:6_000_000},.1);cache.flush();assert.equal(loads,beforeOversize,'an oversized request is never fetched');
cache.demand(page(33),1);cache.flush();await Promise.resolve();deliveries.shift().reject(Error('offline'));
await new Promise(resolve=>setImmediate(resolve));assert.equal(cache.get(page(33).url),null);
const beforeRetry=loads;cache.demand(page(33),1);cache.flush();assert.equal(loads,beforeRetry,'failed requests back off');
now=31_000;cache.demand(page(33),1);cache.flush();await deliver();
cache.demand(page(34),1);cache.flush();cache.dispose();await deliver();
assert.equal(live.size,0,'closing while a page loads releases its late image');assert.equal(peak,1);
console.log('PASS: nearest-page priority, one resident-or-loading slot, late delivery, 32-page traversal, failure fallback, retry, and teardown');
const THREE=await import(three),{dressPhotoEyes,dressPhotoLooks}=await import(new URL('renderers/web/js/human-skin.js',root));
const scene=new THREE.Group(),old=new THREE.MeshStandardMaterial({color:0xffffff});old.name='eyes__sclera';
const eye=new THREE.Mesh(new THREE.BufferGeometry(),old);scene.add(eye);dressPhotoEyes(scene,face);
assert.notEqual(eye.material,old,'the eye colour belongs to this person alone');
assert.equal(old.color.r,1,'the shared exported eye stays unchanged');
assert(eye.material.color.r<.6&&eye.material.color.g<.6,'the pilot uses a softer sclera');
const same=eye.material;dressPhotoEyes(scene,face);assert.equal(eye.material,same,'dressing twice does not allocate twice');
assert(eye.material.userData.chiPhotoOwned,'actor teardown can dispose its eye material');
const {dressLooks}=await import(new URL('renderers/web/js/human-looks.js',root));
const textured=new THREE.MeshStandardMaterial();textured.name='eyes__iris';textured.map=new THREE.Texture();
const iris=new THREE.Mesh(new THREE.BufferGeometry(),textured);scene.add(iris);scene.userData.chiPhotoFace=face;
dressPhotoLooks(scene,{eyes:{drawn:'blue'}});
assert.equal(iris.material.map,textured.map,'photo eyes retain their detail through the recorded-colour layer');
dressPhotoEyes(scene,face);assert.equal(iris.material.map,textured.map);
const plain=new THREE.Group(),flat=new THREE.Mesh(new THREE.BufferGeometry(),textured);plain.add(flat);
dressLooks(plain,{eyes:{drawn:'blue'}});assert.equal(flat.material.map,null,'the existing default colour path is unchanged');
dressPhotoEyes(plain,face);assert(flat.material.color.r<1,'a flat iris takes the measured colour, not a texture gain');
const known=new THREE.Group();known.userData.chiPhotoFace=face;
const knownEye=new THREE.Mesh(new THREE.BufferGeometry(),textured);known.add(knownEye);
dressPhotoLooks(known,{eyes:{drawn:'blue',grade:'attested'}});dressPhotoEyes(known,face);
assert.deepEqual(knownEye.material.color.toArray(),[.10,.17,.30],'a fictional photo cannot overwrite an attested eye colour');
console.log('PASS: photo rollout is opt-in, deterministic, source-shaped, adult-only, within the atlas budget, and preserves personal portraits and visitor choices');
