// SPDX-License-Identifier: GPL-3.0-or-later
// Default load, real assignments in every year, and age-appropriate child texture transfer.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
const root=new URL('../',import.meta.url),three=new URL('renderers/web/vendor/three-0.185.1/three.module.js',root).href;
registerHooks({resolve:(s,c,next)=>s==='three'?{url:three,shortCircuit:true}:next(s,c)});
const V=await import(new URL('renderers/web/js/human-variation.js',root));
const read=async name=>JSON.parse(await fs.readFile(new URL(name,root)));
const main=(await read('assets/humans/web/hm08_variation_persons.json')).persons;
const asked=[];
const fetchFiles=async url=>{
 const name=String(url).split('/humans/web/')[1];asked.push(name);
 try{const b=await fs.readFile(new URL('assets/humans/web/'+name,root));return{ok:true,json:async()=>JSON.parse(b),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}
 catch{return{ok:false};}
};
const kit=await V.loadVariationKit('https://example.org/humans/web/',fetchFiles);
assert(kit.photoFaces&&kit.photoChildren&&kit.photoPortraits,'all three libraries load without a preview flag');
assert.equal(kit.photoFaces.faces.length,256);assert.equal(kit.photoChildren.faces.length,16);
assert(kit.photoFaces.activation&&kit.photoChildren.activation,'the manifests record owner-approved dev activation');
const noPhotos={...kit,photoFaces:null,photoChildren:null,photoPortraits:null};
const locationBefore=globalThis.location;globalThis.location=new URL('https://example.org/walk/?photoFaces=off');
const off=await V.loadVariationKit('https://example.org/humans/web/',fetchFiles);
assert(!off.photoFaces&&!off.photoChildren&&!off.photoPortraits,'an explicit comparison opt-out keeps the former appearance');
if(locationBefore===undefined)delete globalThis.location;else globalThis.location=locationBefore;
const docs=new Map(),summary=[],namedUsed=new Set();
for(const year of ['1812','1835','1871','1904']){
 const own=['1835','1871'].includes(year)?(await read(`assets/humans/web/hm08_variation_persons_${year}.json`)).persons:{};
 const persons={...own,...main},assignments=new Map();
 const add=(key,asset)=>{assert(asset,`${year}/${key}: assigned body exists`);assignments.set(key+'|'+asset,{key,asset});};
 for(const [key,record]of Object.entries(main))if(String(record.scene)===year)for(const at of record.drawn_as??[]){
  const [file,row]=at.split('#');if(!docs.has(file))docs.set(file,await read(file));const d=docs.get(file);
  add(key,row==null?d.appearance?.asset_id:d.people?.find(p=>p.person===row)?.asset_id??d.rows?.find(r=>r.id===row)?.driver_asset);
 }
 for(const row of (await read(`data/humans/inside_${year}.json`)).people??[])if(row.asset_id)add(row.person,row.asset_id);
 let adults=0,children=0,personal=0,named=0;const chosen=new Map(),adultFaces=new Set(),childFaces=new Set();
 for(const {key,asset}of assignments.values()){
  const record=persons[key];assert(record,`${year}/${key}: its actual fetched population record`);
  const q={kit,key,record,assetId:asset,sceneYear:Number(year)},v=V.personVariation(q);
  const expected=kit.photoPortraits.faces.find(f=>f.id===key&&f.historical.scene===year);
  if(expected&&!record.skin&&!record.looks?.face_pick)assert.equal(v.photoFace?.id,key,`${key}: own portrait on every actual assigned body`);
  if(v.photoFace?.population==='person'){
   assert.equal(v.photoFace.id,key,`${key}: exactly this person’s photograph`);assert.equal(v.photoFace.historical.scene,year);
   if(v.photoFace.texture_only){const old=V.personVariation({...q,kit:noPhotos});assert.deepEqual(v.values,old.values);assert.deepEqual(v.option,old.option);assert.equal(v.height,old.height);}
   personal++;named++;namedUsed.add(key);
  }else if(record.face?.values||record.skin||record.looks?.face_pick){assert.equal(v.photoFace,null,`${key}: personal/visitor likeness protected`);personal++;}
  else if(v.age<18){
   assert(v.photoFace?.population==='child',`${year}/${key}: an age-appropriate child photo`);
   assert(v.photoFace.texture_only);assert.deepEqual(v.photoFace.values,{});
   const old=V.personVariation({...q,kit:noPhotos});
   assert.deepEqual(v.values,old.values,`${key}: child head and body morphs are unchanged`);
   assert.deepEqual(v.option,old.option);assert.equal(v.height,old.height);assert.equal(v.age,old.age);
   assert(v.photoFace.age>=v.age-4&&v.photoFace.age<=v.age+3,`${key}: nearby appearance age`);
   assert(v.photoFace.eyes.centres_uv===null,'native child eye geometry is retained');children++;childFaces.add(v.photoFace.id);
  }else{
   assert(v.photoFace&&v.photoFace.age>=18,`${year}/${key}: an adult photo`);adults++;adultFaces.add(v.photoFace.id);
  }
  if(chosen.has(key))assert.equal(chosen.get(key),v.photoFace?.id??null,`${key}: same source across bodies`);
  chosen.set(key,v.photoFace?.id??null);
 }
 assert(adults>0&&children>0,`${year}: adults and children were both checked`);
 summary.push({year,people:chosen.size,assignments:assignments.size,adultPhotoAssignments:adults,childPhotoAssignments:children,personalAssignmentsProtected:personal,namedPhotoAssignments:named,distinctAdultFaces:adultFaces.size,distinctChildFaces:childFaces.size});
}
assert.equal(namedUsed.size,26,'all 26 currently cast named photo people are reached');
assert.deepEqual(kit.photoPortraits.faces.filter(f=>!namedUsed.has(f.id)).map(f=>f.id),['pa1904_glessner_john_j_c1900_kate_ryan'],'the retained former-cook reference has no active cast; importing a photograph does not create one');
const bad=structuredClone(kit.photoChildren);bad.faces[0].values={head_shape:.8};
assert.equal(V.attachChildPhotoLibrary({},bad,new URL('photo_faces/children/review.json',kit.base)),false,'adult shape transfer cannot enter the child library');
const movedEyes=structuredClone(kit.photoChildren);movedEyes.faces[0].eyes.centres_uv=[[.4,.4],[.6,.4]];
assert.equal(V.attachChildPhotoLibrary({},movedEyes,new URL('photo_faces/children/review.json',kit.base)),false,'a child library cannot reshape the native eyes');
const catalogs=[kit.photoFaces,kit.photoChildren,kit.photoPortraits];
const crowd=catalogs.reduce((s,l)=>s+l.textures.light.gpu_bytes_rgba8_mipmaps,0);
const detail=Math.max(...catalogs.flatMap(l=>l.pages.map(p=>p.textures.full.gpu_bytes_rgba8_mipmaps)));
const rgbaMips=([width,height])=>{let bytes=0;for(;;){bytes+=width*height*4;if(width===1&&height===1)return bytes;width=Math.max(1,Math.floor(width/2));height=Math.max(1,Math.floor(height/2));}};
const actualCrowd=catalogs.reduce((sum,l)=>sum+rgbaMips(l.textures.light.size_px),0);
const actualDetail=Math.max(...catalogs.flatMap(l=>l.pages.map(p=>rgbaMips(p.textures.full.size_px))));
assert(actualCrowd+actualDetail<=13*1024*1024,'actual RGBA8 mip chains for all three crowd sheets and ONE nearby page stay within 13 MiB');
for(const l of catalogs)for(const t of [l.textures.light,...l.pages.map(p=>p.textures.full)]){const exact=rgbaMips(t.size_px);assert(t.gpu_bytes_rgba8_mipmaps>=exact);assert.equal(t.gpu_bytes_rgba8_mipmaps,Math.ceil(t.size_px[0]*t.size_px[1]*16/3),'conservative 4/3 bound also covers rectangular non-power-of-two sheets');}
assert(crowd+detail<=13*1024*1024,'the conservative sum also fits the cap');
console.log(JSON.stringify({allYearCoverage:summary,crowdBytes:crowd,sharedDetailMaxBytes:detail,totalFaceTextureMaxBytes:actualCrowd+actualDetail,conservativeMetadataBytes:crowd+detail}));
console.log('PASS: default photographic adults and children in all four years, complete scene tables, stable identities, preserved child proportions, protected personal likenesses and bounded shared textures');
