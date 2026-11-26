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
const people=JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_persons.json',root))).persons;
const query={key:'sample',sex:'male',age:42};
assert.equal(photoFaceFor(kit,query),null,'the default stays on its ordinary library');
assert(attachPhotoLibrary(kit,library,new URL('photo_faces/pilot/review.json',kit.base)));
const face=photoFaceFor(kit,query);
assert.equal(face.sex,'male');assert.equal(photoFaceFor(kit,query).id,face.id);
assert.equal(photoFaceFor(kit,{...query,age:12}),null,'no adult face on a child');
assert.equal(photoFaceFor(kit,{...query,own:true}),null,'a historical portrait wins');
assert.equal(photoFaceFor(kit,{...query,pick:'body'}),null,'the visitor\'s choice wins');
assert.equal(attachPhotoLibrary(kit,{...library,textures:{light:{gpu_bytes_rgba8_mipmaps:2_000_000}}},kit.base),false,'the weak-machine atlas ceiling binds');
const id='pa1904_armour_mrs_philip_d_c1900_joseph_daniels';
const v=personVariation({kit,key:id,record:people[id],assetId:'glessner_john_j_1904',sceneYear:1904});
assert(v.photoFace&&v.lib.url.endsWith('faces_light.jpg'),'an existing generic adult gets a photograph');
assert.equal(v.values.nose_width,v.photoFace.values.nose_width,'the source shapes the head too');
const other=personVariation({kit,key:id,record:people[id],assetId:'bardwell_otis_1835',sceneYear:1904});
assert.equal(other.photoFace.id,v.photoFace.id,'one person keeps one face across bodies');
const grey='pa1904_grey_w_l';
assert.equal(personVariation({kit,key:grey,record:people[grey],assetId:'glessner_john_j_1904',sceneYear:1904}).photoFace,null);
// Use every actual scene assignment, including carriage drivers and household rows.
const docs=new Map(),photoPeople=new Set();let drawn=0,photographic=0,children=0,personal=0;
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
      assert.equal(variant.photoFace.sex,variant.sex,`${key}: compatible face source`);photographic++;photoPeople.add(key);
    }
    chosen.push(variant.photoFace?.id??null);
  }
  if(chosen.length){assert.equal(new Set(chosen).size,1,`${key}: one face across every drawn body`);drawn++;}
}
console.log(JSON.stringify({drawnPeople:drawn,genericPeople:photoPeople.size,photoAssignments:photographic,childAssignmentsProtected:children,personalAssignmentsProtected:personal}));
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
