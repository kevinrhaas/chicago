// SPDX-License-Identifier: GPL-3.0-or-later
// Actual per-year populations, and exact-id historical photos over the same bounded cache.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
const root=new URL('../',import.meta.url),three=new URL('renderers/web/vendor/three-0.185.1/three.module.js',root).href;
registerHooks({resolve:(s,c,next)=>s==='three'?{url:three,shortCircuit:true}:next(s,c)});
const V=await import(new URL('renderers/web/js/human-variation.js',root));
const read=async name=>JSON.parse(await fs.readFile(new URL(name,root)));
const header=await read('assets/humans/web/hm08_variation_kit.json');
const bytes=await fs.readFile(new URL(`assets/humans/web/${header.bin}`,root));
const kit=V.parseVariationKit(header,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
kit.base='https://example.org/humans/web/hm08_variation_kit.json';
const generic=await read('assets/humans/web/photo_faces/pilot/review.json');
const historical=await read('assets/humans/web/photo_faces/historical/review.json');
const main=(await read('assets/humans/web/hm08_variation_persons.json')).persons;
assert(V.attachPhotoLibrary(kit,generic,new URL('photo_faces/pilot/review.json',kit.base)));
const docs=new Map(),summary=[];
for(const year of ['1812','1835','1871','1904']){
 const own=['1835','1871'].includes(year)?(await read(`assets/humans/web/hm08_variation_persons_${year}.json`)).persons:{};
 const persons={...own,...main},assignments=new Map();
 const add=(key,asset)=>{assert(asset,`${year}/${key}: a real assigned body`);assignments.set(key+'|'+asset,{key,asset});};
 for(const [key,record]of Object.entries(main))if(String(record.scene)===year)for(const at of record.drawn_as??[]){
  const [file,row]=at.split('#');if(!docs.has(file))docs.set(file,await read(file));const d=docs.get(file);
  add(key,row==null?d.appearance?.asset_id:d.people?.find(p=>p.person===row)?.asset_id??d.rows?.find(r=>r.id===row)?.driver_asset);
 }
 const inside=await read(`data/humans/inside_${year}.json`);
 for(const row of inside.people??[])if(row.asset_id)add(row.person,row.asset_id);
 let adults=0,children=0,personal=0;const used=new Set(),chosen=new Map();
 for(const {key,asset}of assignments.values()){
  const record=persons[key];assert(record,`${year}/${key}: fetched population record`);
  const variant=V.personVariation({kit,key,record,assetId:asset,sceneYear:Number(year)});
  if(variant.age<18){assert.equal(variant.photoFace,null);children++;}
  else if(record.face?.values||record.skin||record.looks?.face_pick){assert.equal(variant.photoFace,null);personal++;}
  else{assert(variant.photoFace,`${year}/${key}: generic adult has a photo`);adults++;used.add(variant.photoFace.id);}
  if(chosen.has(key))assert.equal(chosen.get(key),variant.photoFace?.id??null,`${key}: one face on different bodies`);
  chosen.set(key,variant.photoFace?.id??null);
 }
 assert(adults>0,`${year}: actual adult assignments were exercised`);
 summary.push({year,people:chosen.size,assignments:assignments.size,genericAdultAssignments:adults,childAssignmentsProtected:children,personalAssignmentsProtected:personal,distinctGenericFaces:used.size});
}
console.log(JSON.stringify({allYearCoverage:summary}));
assert.equal(historical.faces.length,6);
assert.equal(V.attachPhotoPortraits(kit,{...historical,faces:[{...historical.faces[0],synthetic:true}]},kit.base),false);
assert.equal(V.attachPhotoPortraits(kit,{...historical,faces:[{...historical.faces[0],historical:{person_id:'someone_else',scene:'1904'}}]},kit.base),false);
assert(V.attachPhotoPortraits(kit,historical,new URL('photo_faces/historical/review.json',kit.base)));
for(const face of historical.faces){
 const record=main[face.id];assert(record);const fit=await read(face.shape_from);
 for(const [key,value]of Object.entries(fit.values))assert.equal(face.values[key],value,`${face.id}: curated ${key} retained`);
 const actual=V.personVariation({kit,key:face.id,record,assetId:face.base_body,sceneYear:1904});
 assert.equal(actual.photoFace.id,face.id);assert.equal(actual.photoFace.synthetic,false);
 assert(actual.lib.url.includes('/historical/'));assert(actual.lib.detail.url.includes('/historical/'));
 assert.equal(actual.age,record.age.years,'the photo does not overwrite the scene age');
 for(const [name,value]of Object.entries(fit.values))assert.equal(name.endsWith('.option')?actual.option[name.slice(0,-7)]:actual.values[name],value);
 assert.equal(V.personVariation({kit,key:face.id,record,assetId:face.base_body,sceneYear:1871}).photoFace,null,'no backdating a named portrait into another scene');
 assert.equal(V.personVariation({kit,key:face.id,record:{...record,skin:{map:'own.jpg'}},assetId:face.base_body,sceneYear:1904}).photoFace,null,'a separate personal likeness stays protected');
 assert.equal(V.personVariation({kit,key:face.id,record:{...record,looks:{...record.looks,face_pick:'body'}},assetId:face.base_body,sceneYear:1904}).photoFace,null,'an explicit visitor choice wins');
}
for(const id of ['pa1904_grey_w_l','pa1904_grey_mrs_w_l'])assert.equal(V.personVariation({kit,key:id,record:main[id],assetId:'glessner_john_j_1904',sceneYear:1904}).photoFace,null);
const crowd=generic.textures.light.gpu_bytes_rgba8_mipmaps+historical.textures.light.gpu_bytes_rgba8_mipmaps;
const detail=Math.max(...[generic,historical].flatMap(l=>l.pages.map(p=>p.textures.full.gpu_bytes_rgba8_mipmaps)));
assert(crowd+detail<12*1024*1024,'the current two catalogs share one detail slot and remain below 12 MiB');
console.log(JSON.stringify({historicalPeople:historical.faces.map(f=>({id:f.id,name:f.label,scene:f.historical.scene})),genericAndHistoricalCrowdBytes:crowd,sharedDetailMaxBytes:detail,totalFaceTextureMaxBytes:crowd+detail}));
console.log('PASS: all four years including their own population tables; six exact-id, scene-bound personal photographs; curated heads, ages and other likenesses preserved; shared texture residency bounded');
