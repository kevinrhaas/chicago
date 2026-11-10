// SPDX-License-Identifier: GPL-3.0-or-later
// Pure decision/control cases. No child GLBs, images, Blender or renderer.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {registerHooks} from 'node:module';
import {MATERIAL,splitGroups,linearToSRGB,pixel,validateRecipe,parentTreeBlob} from './human_charles_coat.mjs';
const APP=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const recipe=JSON.parse(fs.readFileSync(path.join(APP,'data/humans/materials/charles-coat-woven-v1.json')));
let controls=0;
validateRecipe(recipe);controls++;
for(const row of recipe.parents){assert.equal(parentTreeBlob(recipe.parent_revision,row.file),row.gitBlob,'actual repository-relative parent identity, even when caller cwd is APP');controls++;}
assert.equal(parentTreeBlob(recipe.parent_revision,'assets/humans/nelson_charles_1904_coachman.lod9.glb'),undefined,'missing actual tree binding cannot fall back');controls++;
for(const mutation of [r=>r.asset_id='bardwell_otis_1835',r=>r.parent_revision='0'.repeat(40),r=>r.parents[0].file='../escape.glb',r=>r.parents[0].sha256='f00',r=>r.parents.push(r.parents[0]),r=>r.linear_color[0]=.1,r=>r.runtime_weave='bypass_all_fabric']){const copy=structuredClone(recipe);mutation(copy);assert.throws(()=>validateRecipe(copy));controls++;}
// Same original index and same exact tangent reuse one row; actual handedness
// conflicts receive a row of their own. Never average or merge old indices.
const indices=[0,1,2,0,2,1],one=[1,0,0,1],other=[1,0,0,-1];
const a=splitGroups(indices,new Float32Array(indices.flatMap(()=>one)),3);
assert.deepEqual(a.source,[0,1,2]);assert.deepEqual(a.indices,indices);assert.equal(a.duplicates,0);controls++;
const b=splitGroups(indices,new Float32Array([one,one,one,other,one,one].flat()),3);
assert.deepEqual(b.source,[0,1,2,0]);assert.deepEqual(b.indices,[0,1,2,3,2,1]);assert.equal(b.tangents.readFloatLE(12),-1);assert.equal(b.tangents.readFloatLE(60),1);controls++;
assert.throws(()=>splitGroups(indices,new Float32Array(indices.flatMap(()=>[NaN,0,0,1])),3));controls++;
assert.throws(()=>splitGroups(indices,new Float32Array(indices.flatMap(()=>one)),4));controls++;
// Quantizer-derived dark-color intervals, not a broad arbitrary palette delta.
const decode=x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4;
for(const value of [0,.0001,.001,.0031308,.014,.026,.019,.045,1]){const byte=Math.round(linearToSRGB(value)*255);assert(decode(Math.max(0,byte-.5)/255)<=value&&decode(Math.min(255,byte+.5)/255)>=value);controls++;}
for(let c=0;c<3;c++){
  let low=0,high=0;for(let y=0;y<128;y++)for(let x=0;x<128;x++){const p=pixel('color',x,y);low+=decode(Math.max(0,p[c]-.5)/255);high+=decode(Math.min(255,p[c]+.5)/255);}
  assert(low/16384<=recipe.linear_color[c]&&high/16384>=recipe.linear_color[c]);controls++;
}
registerHooks({resolve(s,c,next){if(s==='three')return{url:pathToFileURL(path.join(APP,'renderers/web/vendor/three-0.185.1/three.module.js')).href,shortCircuit:true};return next(s,c);}});
const T=await import('three');
const {patchFabric,portableCoatThreads,CLOTHS}=await import(pathToFileURL(path.join(APP,'renderers/web/js/fabric.js')));
const {dressCloth,disposeLooks}=await import(pathToFileURL(path.join(APP,'renderers/web/js/human-looks.js')));
const material=new T.MeshStandardMaterial();material.name=MATERIAL;
material.map=new T.Texture();material.normalMap=new T.Texture();material.roughnessMap=new T.Texture();
material.userData.chicago4d_cloth_microtexture={version:1,profile:'wool',source_material:MATERIAL,runtime_weave:'portable_maps_with_common_macro',license:'CC0-1.0',historical_texture:false};
assert(portableCoatThreads(material));controls++;
const uniforms=m=>{const shader={vertexShader:'#include <begin_vertex>',fragmentShader:['color_fragment','roughnessmap_fragment','normal_fragment_maps','lights_fragment_end'].map(x=>'#include <'+x+'>').join('\n'),uniforms:{}};patchFabric(m);m.onBeforeCompile(shader,{});return shader.uniforms;};
const u=uniforms(material);assert.equal(u.chiFabric.value.y,0);assert.equal(u.chiFabric.value.z,0);assert.equal(u.chiFabric.value.w,CLOTHS.wool.rumple*.01);assert.equal(u.chiFabricWear.value.x,CLOTHS.wool.sheen);controls++;
const geometry=new T.BufferGeometry(),root=new T.Group();root.add(new T.Mesh(geometry,material),new T.Mesh(geometry,material));
let sharedMapDisposed=0,cloneDisposed=0;material.map.addEventListener('dispose',()=>sharedMapDisposed++);
const clones=dressCloth(root,{colours:{[MATERIAL]:[.1,.2,.3]}});assert.equal(clones.length,1);const clone=clones[0];clone.addEventListener('dispose',()=>cloneDisposed++);
assert.equal(clone.name,MATERIAL);assert.equal(clone.map,null);assert.equal(clone.normalMap,material.normalMap);assert.equal(clone.roughnessMap,material.roughnessMap);assert.equal(root.children[0].material,root.children[1].material);assert.notEqual(clone,material);assert.equal(material.map.isTexture,true);assert(portableCoatThreads(clone));controls++;
const recolor=uniforms(clone);assert.equal(recolor.chiFabric.value.y,0);assert.equal(recolor.chiFabric.value.z,CLOTHS.wool.heather);controls++;
disposeLooks(clones);assert.equal(cloneDisposed,1);assert.equal(sharedMapDisposed,0);controls++;
const ordinary=new T.MeshStandardMaterial();ordinary.name=MATERIAL;const defaults=uniforms(ordinary);assert.equal(defaults.chiFabric.value.y,CLOTHS.wool.weave);assert.equal(defaults.chiFabric.value.z,CLOTHS.wool.heather);controls++;
geometry.dispose();for(const texture of [material.map,material.normalMap,material.roughnessMap])texture.dispose();material.dispose();ordinary.dispose();
console.log(JSON.stringify({status:'PURE_SOURCE_CONTROLS_ONLY',controls,child_assets_generated:false,renderer:false,actual_GLTF_loader_invariance:'UNRUN'}));
