// SPDX-License-Identifier: GPL-3.0-or-later
// Named portraits must stay with their person, scene and reviewed head.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
const root=new URL('../',import.meta.url);
registerHooks({resolve:(s,c,next)=>s==='three'?{url:new URL('renderers/web/vendor/three-0.185.1/three.module.js',root).href,shortCircuit:true}:next(s,c)});
const V=await import('../renderers/web/js/human-variation.js');
const read=async p=>JSON.parse(await fs.readFile(new URL(p,root)));
const fetchFiles=async url=>{try{const b=await fs.readFile(new URL('assets/humans/web/'+String(url).split('/humans/web/')[1],root));return{ok:true,json:async()=>JSON.parse(b),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}catch{return{ok:false};}};
const kit=await V.loadVariationKit('https://example.org/humans/web/',fetchFiles),lib=await read('assets/humans/web/photo_faces/historical/review.json');
const main=(await read('assets/humans/web/hm08_variation_persons.json')).persons,before={...kit,photoPortraits:null};
assert.equal(lib.faces.length,27);assert.equal(kit.photoPortraits.faces.length,27);
let own=0,standIn=0,preservedHeads=0,newFits=0;
for(const f of lib.faces){
 const h=f.historical,record=main[f.id],q={kit,key:f.id,record,assetId:h.reference_asset,sceneYear:1904};
 assert(record);const actual=V.personVariation(q),old=V.personVariation({...q,kit:before});
 assert.equal(actual.photoFace.id,f.id);assert(actual.lib.url.includes('/historical/'));assert(actual.lib.detail.url.includes('/historical/'));
 assert.equal(actual.age,old.age);assert.equal(actual.height,old.height);
 if(f.texture_only){assert.deepEqual(actual.values,old.values);assert.deepEqual(actual.option,old.option);assert.equal(f.eyes.centres_uv,null);assert(f.eyes.lid_rest>=0);preservedHeads++;}
 else{assert.equal(h.shape_mode,'new_photo_fit');for(const [axis,value] of Object.entries(f.values))assert.equal(axis.endsWith('.option')?actual.option[axis.slice(0,-7)]:actual.values[axis],value);assert.notDeepEqual(actual.values,old.values);newFits++;}
 if(h.identity_basis==='own_portrait')own++;else{assert(h.stand_in.label.startsWith('STAND-IN'));assert(f.label.includes(h.stand_in.label));assert.equal(f.grade,'reconstructed');standIn++;}
 for(const year of [1812,1835,1871])assert.notEqual(V.personVariation({...q,sceneYear:year}).photoFace?.id,f.id,'no backdated named portrait');
 for(const record of [{...q.record,skin:{map:'own.jpg'}},{...q.record,looks:{...q.record.looks,face_pick:'body'}}])assert.equal(V.personVariation({...q,record}).photoFace,null,'full skins and explicit visitor choices win');
 assert.notEqual(V.personVariation({...q,key:'a-different-person',record:{...record,face:null}}).photoFace?.id,f.id,'another person cannot inherit this photograph');
 const opposite=f.sex==='male'?'female':'male';assert.notEqual(V.personVariation({...q,record:{...record,sex:opposite}}).photoFace?.id,f.id);
}
assert.equal(own,20);assert.equal(standIn,7);assert.equal(preservedHeads,25);assert.equal(newFits,2);
for(const id of ['pa1904_grey_w_l','pa1904_grey_mrs_w_l']){assert(main[id].skin);assert.equal(V.personVariation({kit,key:id,record:main[id],assetId:'glessner_john_j_1904',sceneYear:1904}).photoFace,null);}
for(const changes of [{synthetic:true},{texture_only:false,historical:{...lib.faces[0].historical,shape_mode:null}},{historical:{...lib.faces[0].historical,person_id:'wrong'}},{historical:{...lib.faces[0].historical,identity_basis:'labelled_stand_in',stand_in:null}}])assert.equal(V.attachPhotoPortraits({}, {...lib,faces:[{...lib.faces[0],...changes}]},kit.base),false);
assert.equal(V.attachPhotoPortraits({}, {...lib,textures:{...lib.textures,light:{...lib.textures.light,gpu_bytes_rgba8_mipmaps:350001}}},kit.base),false);
const coverage=await read('assets/humans/web/photo_faces/historical/coverage.json');assert.equal(coverage.people.length,29);assert.equal(coverage.people.filter(p=>!p.active_cast).length,1);assert.equal(coverage.people.filter(p=>p.status==='existing_skin').length,2);
console.log(JSON.stringify({ownPortraits:own,labelledReferences:standIn,preservedHeads,newPhotoHeadFits:newFits,existingGreySkins:2}));
console.log('PASS: all 29 existing/selected portrait references are applied or retained; exact IDs/scenes, head fits, age, height, stand-in labels, existing skins and visitor choices protected');
