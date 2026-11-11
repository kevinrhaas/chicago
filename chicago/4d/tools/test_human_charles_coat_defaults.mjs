// SPDX-License-Identifier: GPL-3.0-or-later
// Actual pinned writer omission controls, in RAM only. No output assets/images.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {materialFactors,assertMaterialFactors,textureDefaults,assertTextureSampling,assertExact} from './human_charles_coat_semantics.mjs';
const APP=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const check=process.argv[2]==='--check';
const [dependencies,argumentChild]=process.argv.slice(2);
assert(check?process.argv.length===3:dependencies&&argumentChild,'--check OR PINNED_NODE_MODULES VERIFIED_MASTER0_CHILD');
const childFile=check?path.join(APP,'assets/humans/nelson_charles_1904_coachman.lod0.glb'):argumentChild;
const require=createRequire(import.meta.url);
const raw=fs.readFileSync(childFile);assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),'ebb5594ce5aadf36da25f87676252e8026c3cd993760b2cbd9f1c6d3fb9351af','exact reviewed actual MASTER0 child');
const original=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
let canonical;
if(check){
  // The gate reads the ACTUAL canonical WEB produced and independently checked
  // by the pinned owner, not a mock writer or synthesized default fixture.
  const web=fs.readFileSync(path.join(APP,'assets/humans/web/nelson_charles_1904_coachman.lod0.glb'));
  assert.equal(crypto.createHash('sha256').update(web).digest('hex'),'8660b20793909061ecc0c81b31c4b6e4fd26c2da0afa04c7b741788495c28820');
  canonical=JSON.parse(web.subarray(20,20+web.readUInt32LE(12)));assert.equal(canonical.asset.generator,'glTF-Transform v4.5.0');
}else{
  assert.equal(JSON.parse(fs.readFileSync(path.join(dependencies,'@gltf-transform/core/package.json'))).version,'4.5.0');
  const {NodeIO}=require(path.join(dependencies,'@gltf-transform/core')),{ALL_EXTENSIONS}=require(path.join(dependencies,'@gltf-transform/extensions'));
  canonical=(await new NodeIO().registerExtensions(ALL_EXTENSIONS).writeJSON(await new NodeIO().registerExtensions(ALL_EXTENSIONS).readBinary(raw))).json;
}
const coat=doc=>doc.materials.find(m=>m.name==='garment_outer__livery_coat_green_1904');
const source=coat(original),serialized=coat(canonical);assert(source&&serialized);
let controls=0;
assert.equal(serialized.pbrMetallicRoughness.baseColorFactor,undefined);assert.equal(serialized.pbrMetallicRoughness.roughnessFactor,undefined);assert.equal(serialized.normalTexture.scale,undefined);assert.equal(serialized.normalTexture.texCoord,undefined);controls++;
assertMaterialFactors(source,serialized);controls++;
assert.deepEqual(materialFactors({}),{baseColorFactor:[1,1,1,1],roughnessFactor:1,metallicFactor:1});controls++;
assert.throws(()=>assertMaterialFactors(source,{...serialized,pbrMetallicRoughness:{...serialized.pbrMetallicRoughness,metallicFactor:1}}));controls++;
for(const [key,value] of [['baseColorFactor',[.99,1,1,1]],['roughnessFactor',.99]]){const changed=structuredClone(serialized);changed.pbrMetallicRoughness[key]=value;assert.throws(()=>assertMaterialFactors(source,changed));controls++;}
for(const [key,value] of [['baseColorFactor',null],['baseColorFactor',[1,1,1]],['baseColorFactor',[1,1,1,NaN]],['baseColorFactor',[1,1,1,Infinity]],['roughnessFactor',null],['roughnessFactor',NaN],['roughnessFactor','1'],['metallicFactor',undefined],['metallicFactor',1.1]]){const bad=structuredClone(serialized);bad.pbrMetallicRoughness[key]=value;assert.throws(()=>materialFactors(bad));controls++;}
assert.throws(()=>materialFactors({pbrMetallicRoughness:null}));controls++;
const resolve=(doc,info)=>{assert(info);const t=doc.textures[info.index];return {...info,index:{sampler:t.sampler===undefined?null:doc.samplers[t.sampler]}};};
const slots=m=>[m.pbrMetallicRoughness.baseColorTexture,m.pbrMetallicRoughness.metallicRoughnessTexture,m.normalTexture];
for(let i=0;i<3;i++){const a=resolve(original,slots(source)[i]),b=resolve(canonical,slots(serialized)[i]);assertTextureSampling(a,b,i===2?'normal':'ordinary');controls++;}
const normal=resolve(canonical,serialized.normalTexture),explicit=resolve(original,source.normalTexture);
const normalized=textureDefaults(normal,'normal'),reordered=Object.fromEntries(Object.entries(normalized).reverse());
assertExact(normalized,reordered,'actual canonical TextureInfo object insertion order is not semantics');controls++;
const clipOrder=canonical.animations.map(a=>a.name);assert(clipOrder.length>1&&new Set(clipOrder).size===clipOrder.length);
const record={sampling:normalized,clipOrder,factor:1,requiredOwnKey:undefined};
assert.throws(()=>assertExact(record,{...record,clipOrder:[...clipOrder].reverse()},'actual clip array order remains exact'));controls++;
assert.throws(()=>assertExact(record,{...record,factor:.5},'numeric value remains exact'));controls++;
assert.throws(()=>assertExact(record,{...record,factor:'1'},'type remains exact'));controls++;
const missing={...record};delete missing.requiredOwnKey;assert.throws(()=>assertExact(record,missing,'own property presence remains exact'));controls++;
assert.throws(()=>assertExact(-0,0,'signed zero remains exact'));controls++;
for(const [key,value] of [['texCoord',1],['scale',.5]]){const b=structuredClone(normal);b[key]=value;assert.throws(()=>assertTextureSampling(explicit,b,'normal'));controls++;}
for(const [key,value] of [['texCoord',null],['texCoord',.5],['texCoord',undefined],['scale',null],['scale',NaN],['scale','1']]){const b=structuredClone(normal);b[key]=value;assert.throws(()=>textureDefaults(b,'normal'));controls++;}
for(const key of ['magFilter','minFilter','wrapS','wrapT']){const b=structuredClone(normal);b.index.sampler[key]=0;assert.throws(()=>assertTextureSampling(explicit,b,'normal'));controls++;}
const changedTransform=structuredClone(normal);changedTransform.extensions.KHR_texture_transform.scale[0]*=2;assert.throws(()=>assertTextureSampling(explicit,changedTransform,'normal'));controls++;
assert.throws(()=>textureDefaults({texCoord:0},'normal'));controls++;
// No coat occlusion slot is introduced. Exercise only the applicable glTF
// schema helper: absent strength is1, explicit changes remain unequal/invalid.
const occ={index:{sampler:null}},occExplicit={...occ,texCoord:0,strength:1};assertTextureSampling(occExplicit,occ,'occlusion');controls++;
assert.throws(()=>assertTextureSampling(occExplicit,{...occ,strength:.5},'occlusion'));controls++;
for(const strength of [null,undefined,NaN,1.1]){assert.throws(()=>textureDefaults({...occ,strength},'occlusion'));controls++;}
console.log(JSON.stringify({status:'ACTUAL_PINNED_WRITER_DEFAULT_METADATA_CONTROLS_ONLY',controls,actual_input_sha256:'ebb5594ce5aadf36da25f87676252e8026c3cd993760b2cbd9f1c6d3fb9351af',canonical_writer:'glTF-Transform4.5.0',output_files:0,images_decoded:false,WEB_or_render_acceptance:false}));
