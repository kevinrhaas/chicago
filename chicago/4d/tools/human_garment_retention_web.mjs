// SPDX-License-Identifier: GPL-3.0-or-later
// Deterministic V3 single-skin rebind. Geometry-only native loader; no image claims.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {registerHooks} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {sha,same,parse,encode,ALLOWED,selected,rigJSON,nativeRig,nativeRigWithoutBinding,
  stream,meshes,nativeGeometry,nativeWorldVertices,validateGarmentDomains} from './human_garment_retention_web_helpers.mjs';
import {garment,deriveGarment,measureGarmentResiduals} from './human_garment_retention_rebind_math.mjs';

export async function geometryRuntime(app){
 assert.equal(process.versions.node.split('.')[0],'22','reviewed native geometry reproduction uses Node22');
 const engine=path.join(app,'renderers/web/vendor/three-0.185.1');
 registerHooks({resolve(s,c,next){
  if(s==='three')return{url:pathToFileURL(path.join(engine,'three.module.js')).href,shortCircuit:true};
  if(s.startsWith('three/addons/'))return{url:pathToFileURL(path.join(engine,s.slice(6))).href,shortCircuit:true};
  return next(s,c);
 }});
 const T=await import(pathToFileURL(path.join(engine,'three.module.js')).href);
 const {GLTFLoader}=await import(pathToFileURL(path.join(engine,'addons/loaders/GLTFLoader.js')).href);
 const {MeshoptDecoder}=await import(pathToFileURL(path.join(engine,'addons/libs/meshopt_decoder.module.js')).href);
 globalThis.self=globalThis;
 globalThis.ProgressEvent=class extends Event{constructor(t,i={}){super(t);Object.assign(this,i);}};
 await MeshoptDecoder.ready;
 const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
 // Intercept only material loading. Do not rewrite input GLB/parser JSON or
 // bypass native geometry/skin parsing and normalizeSkinWeights(). No textures
 // are requested, so this production transform has no external canvas package.
 loader.register(parser=>({name:'CHICAGO_GEOMETRY_ONLY_GARMENT_REPRODUCTION',
  loadMaterial(index){const material=new T.MeshStandardMaterial();
   material.name=parser.json.materials[index].name??'';return Promise.resolve(material);}
 }));
 return {T,MeshoptDecoder,
  async decode(raw){const g=await loader.parseAsync(raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength),'');
   g.scene.updateMatrixWorld(true);for(const m of meshes(g))m.skeleton.update();return g;},
  dispose(g){for(const skeleton of new Set(meshes(g).map(m=>m.skeleton)))skeleton.dispose();
   const geometries=new Set(),materials=new Set();g.scene.traverse(m=>{
    if(m.geometry)geometries.add(m.geometry);
    for(const material of(Array.isArray(m.material)?m.material:[m.material]))if(material)materials.add(material);
   });for(const geometry of geometries)geometry.dispose();for(const material of materials)material.dispose();}
 };
}

function protectDoc(child,parent,replaced){const expected=structuredClone(parent);expected.buffers[0].byteLength=child.buffers[0].byteLength;expected.accessors=child.accessors;expected.bufferViews=child.bufferViews;for(const r of replaced){const p=expected.meshes[r.mi].primitives[r.pi],actual=child.meshes[r.mi].primitives[r.pi];p.attributes=actual.attributes;p.indices=actual.indices;}same(child,expected,'only selected primitive streams and append-only views/accessors/buffer0 length change');same(child.accessors.slice(0,parent.accessors.length),parent.accessors);same(child.bufferViews.slice(0,parent.bufferViews.length),parent.bufferViews);same(child.buffers.slice(1),parent.buffers.slice(1));same(child.skins,parent.skins,'one original skin exact');same(child.nodes,parent.nodes,'all original nodes/skin references/rest/hierarchy exact');assert.equal(child.skins.length,1);}
function preservedNativeGarmentAttributes(g){return nativeGeometry(g,true).map(row=>({...row,attributes:Object.fromEntries(Object.entries(row.attributes).filter(([k])=>!['position','normal','tangent'].includes(k)))}));}
export async function retainWeb(parentRaw,donorRaw,expectedParent,expectedDonor,runtime){
 assert.equal(sha(parentRaw),expectedParent,'exact immutable seated WEB3 parent required');
 assert.equal(sha(donorRaw),expectedDonor,'exact immutable seated WEB0 donor required');
 const source=parse(donorRaw),parentDoc=parse(parentRaw),doc=structuredClone(parentDoc.json),models=[],mixers=[];
 assert.equal(source.json.skins.length,1);assert.equal(doc.skins.length,1);
 same(source.json.skins[0].joints,doc.skins[0].joints);assert.equal(doc.skins[0].joints.length,56);
 try{
 const donor=await runtime.decode(donorRaw);models.push(donor);
 const old=await runtime.decode(parentRaw);models.push(old);
 same(rigJSON(donor),rigJSON(old),'same native joint order, hierarchy, rest and mesh binds');
 same(nativeRigWithoutBinding(donor),nativeRigWithoutBinding(old),'native source/target bones remain exact');
 validateGarmentDomains(donor);validateGarmentDomains(old);
 const donorIBMs=await stream(source.json,source.bin,source.json.skins[0].inverseBindMatrices,runtime.MeshoptDecoder);
 const targetIBMs=await stream(parentDoc.json,parentDoc.bin,doc.skins[0].inverseBindMatrices,runtime.MeshoptDecoder);
 assert.notEqual(sha(donorIBMs),sha(targetIBMs),'keep diagnosed unequal-bind premise; raw copy is not eligible');
 const blocks=[parentDoc.bin],copies=[],derivations=[],replaced=[];let length=parentDoc.bin.length;
 const appendBytes=(bytes,a,target)=>{const pad=(-length%4+4)%4;if(pad){blocks.push(Buffer.alloc(pad));length+=pad;}const vi=doc.bufferViews.length,v={buffer:0,byteOffset:length,byteLength:bytes.length};if(target!==undefined)v.target=target;doc.bufferViews.push(v);blocks.push(bytes);length+=bytes.length;const acc=structuredClone(a);delete acc.byteOffset;acc.bufferView=vi;const ai=doc.accessors.length;doc.accessors.push(acc);return ai;};
 const copyAccessor=async idx=>{const a=source.json.accessors[idx],bytes=await stream(source.json,source.bin,idx,runtime.MeshoptDecoder),ai=appendBytes(bytes,a,source.json.bufferViews[a.bufferView].target);copies.push({kind:'original_donor_component_stream',source_accessor:idx,candidate_accessor:ai,bytes:bytes.length,sha256:sha(bytes)});return ai;};
 const floatAccessor=(array,kind,label)=>{assert(array instanceof Float32Array&&Array.from(array).every(Number.isFinite));const bytes=Buffer.from(array.buffer,array.byteOffset,array.byteLength),width=kind==='VEC4'?4:3,a={componentType:5126,count:array.length/width,type:kind};if(label==='POSITION'){a.min=Array(width).fill(Infinity);a.max=Array(width).fill(-Infinity);for(let i=0;i<a.count;i++)for(let k=0;k<width;k++){a.min[k]=Math.min(a.min[k],array[i*width+k]);a.max[k]=Math.max(a.max[k],array[i*width+k]);}}const ai=appendBytes(bytes,a,34962);copies.push({kind:'NEW_DERIVED_FLOAT32_'+label,candidate_accessor:ai,bytes:bytes.length,sha256:sha(bytes)});return ai;};
 for(const name of ALLOWED){const src=selected(source.json,name),dst=selected(parentDoc.json,name);same(source.json.materials[src.p.material],parentDoc.json.materials[dst.p.material]);const derived=deriveGarment(garment(donor,name),garment(old,name),runtime),attributes={};for(const[key,index]of Object.entries(src.p.attributes)){if(key==='POSITION')attributes[key]=floatAccessor(derived.positions,'VEC3',key);else if(key==='NORMAL')attributes[key]=floatAccessor(derived.normals,'VEC3',key);else if(key==='TANGENT'){assert(derived.tangents);attributes[key]=floatAccessor(derived.tangents,'VEC4',key);}else attributes[key]=await copyAccessor(index);}doc.meshes[dst.mi].primitives[dst.pi].attributes=attributes;doc.meshes[dst.mi].primitives[dst.pi].indices=await copyAccessor(src.p.indices);replaced.push(dst);derivations.push({material:name,source_mesh:source.json.meshes[src.mi].name,destination_mesh:parentDoc.json.meshes[dst.mi].name,source_material:src.p.material,destination_material:dst.p.material,...derived.metrics});}
 doc.buffers[0].byteLength=length;const childRaw=encode(doc,Buffer.concat(blocks)),childDoc=parse(childRaw);same(childDoc.bin.subarray(0,parentDoc.bin.length),parentDoc.bin,'whole old WEB BIN including compressed data/padding exact');protectDoc(childDoc.json,parentDoc.json,replaced);for(const row of copies){const actual=await stream(childDoc.json,childDoc.bin,row.candidate_accessor,runtime.MeshoptDecoder);assert.equal(sha(actual),row.sha256);}
 const child=await runtime.decode(childRaw);models.push(child);same(rigJSON(old),rigJSON(child));same(nativeRig(old),nativeRig(child),'all original native bones/IBMs/bind matrices/Float32 palettes exact');same(nativeGeometry(old,false),nativeGeometry(child,false),'all protected native non-garment component streams exact');same(preservedNativeGarmentAttributes(donor),preservedNativeGarmentAttributes(child),'all donor JOINTS/WEIGHTS/UV/index values exact after native loader');assert.equal(new Set(meshes(child).map(m=>m.skeleton)).size,1,'unchanged one-skeleton fixture premise');// Full image decoding is a separately recorded native/browser proof; protected JSON and complete old BIN remain exact here.

 const readings=[];const inspect=label=>{same(nativeRig(old),nativeRig(child),'protected exact native rig/palettes at '+label);same(nativeWorldVertices(old,false,runtime),nativeWorldVertices(child,false,runtime),'all actual protected world vertices exact at '+label);const rows=measureGarmentResiduals(donor,child,runtime);assert(rows.every(r=>r.within_existing_position_limit),'strict existing1e-6m garment residual exceeded at '+label);readings.push({pose:label,all_original_native_rig_palettes_and_non_garment_world_vertices_exact:true,all_garment_residuals:rows});};inspect('rest');
 for(const g of[donor,old,child]){const clip=g.animations.find(a=>a.name==='sit_drive_look_v2');assert(clip&&clip.duration===8);const mixer=new runtime.T.AnimationMixer(g.scene);mixer.clipAction(clip).play();mixers.push(mixer);}for(const time of[0,2.75]){for(const m of mixers)m.setTime(time);inspect(time);}
 return childRaw;
 }finally{for(const mixer of mixers){mixer.stopAllAction();mixer.uncacheRoot(mixer.getRoot());}
  for(const g of models)runtime.dispose(g);}
}

if(process.argv[1]&&path.resolve(process.argv[1])===path.resolve(fileURLToPath(import.meta.url))){
 const[app,parentFile,donorFile,parentSHA,donorSHA,out]=process.argv.slice(2);
 assert(app&&parentFile&&donorFile&&parentSHA&&donorSHA&&out);
 assert(!path.resolve(out).startsWith(path.resolve(app)+path.sep),'fresh output must stay outside APP');
 const runtime=await geometryRuntime(app);
 const result=await retainWeb(await fs.readFile(parentFile),await fs.readFile(donorFile),parentSHA,donorSHA,runtime);
 await fs.writeFile(out,result,{flag:'wx'});
 console.log(JSON.stringify({sha256:sha(result),bytes:result.length,route:'single_skin_weighted_rebind_v3',
  images_decoded:false,images_encoded:false,full_optimizer_used:false}));
}
