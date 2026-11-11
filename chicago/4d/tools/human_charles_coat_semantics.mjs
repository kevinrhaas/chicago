// SPDX-License-Identifier: GPL-3.0-or-later
// Independent pinned-codec semantic reader. No generator imports, no file writes,
// no image decoding, no rendering. Exact comparison is deliberately conservative.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {isDeepStrictEqual} from 'node:util';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url),APP=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const COAT='garment_outer__livery_coat_green_1904';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const vector=(a,i)=>{const out=[];a.getElement(i,out);return out;};
const numberKey=x=>{const b=Buffer.alloc(8);b.writeDoubleLE(x);return b.toString('hex');};
const rowKey=values=>values.flat(Infinity).map(numberKey).join('');
function attributes(p){return p.listSemantics().filter(s=>s!=='TANGENT').sort();}
function vertex(p,i){return [attributes(p).map(s=>vector(p.getAttribute(s),i)),p.listTargets().map(t=>t.listSemantics().sort().map(s=>vector(t.getAttribute(s),i)))];}
const cycle=parts=>[parts,parts.slice(1).concat(parts[0]),parts.slice(2).concat(parts.slice(0,2))].map(p=>p.join(':')).sort()[0];
function triangles(p){assert.equal(p.getMode(),4,'actual TRIANGLES mode required');const index=Array.from(p.getIndices().getArray());assert.equal(index.length%3,0);return Array.from({length:index.length/3},(_,t)=>index.slice(t*3,t*3+3));}
function triangleKey(p,t){return hash(cycle(t.map(i=>rowKey(vertex(p,i)))));}
function tangentTriangleKey(p,t){return hash(cycle(t.map(i=>rowKey([vertex(p,i),p.getAttribute('TANGENT')?vector(p.getAttribute('TANGENT'),i):[]]))));}
function multiset(rows){const m=new Map();for(const row of rows)m.set(row,(m.get(row)??0)+1);return [...m].sort(([a],[b])=>a.localeCompare(b));}
function same(a,b,label){
  if(!isDeepStrictEqual(a,b)){const x=JSON.stringify(a)??'<undefined>',y=JSON.stringify(b)??'<undefined>';
    let first=0;while(first<Math.min(x.length,y.length)&&x[first]===y[first])first++;
    throw Error(JSON.stringify({label,left_sha256:hash(x),right_sha256:hash(y),left_entries:a?.length??null,right_entries:b?.length??null,first_difference:first}));}
}
export {same as assertExact};
const has=(o,key)=>Object.prototype.hasOwnProperty.call(o,key);
function object(value,label){assert(value!==null&&typeof value==='object'&&!Array.isArray(value),label+' must be an object');return value;}
// glTF2 material.pbrMetallicRoughness schema defaults. Only ABSENT fields
// default; explicit null/undefined, wrong shapes and nonfinite values fail.
export function materialFactors(material){
  object(material,'material');const p=has(material,'pbrMetallicRoughness')?object(material.pbrMetallicRoughness,'pbrMetallicRoughness'):{};
  const color=has(p,'baseColorFactor')?p.baseColorFactor:[1,1,1,1];
  assert(Array.isArray(color)&&color.length===4&&color.every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=0&&x<=1),'baseColorFactor four finite unit components');
  const scalar=key=>{const v=has(p,key)?p[key]:1;assert(typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=1,key+' finite unit factor');return v;};
  return {baseColorFactor:color,roughnessFactor:scalar('roughnessFactor'),metallicFactor:scalar('metallicFactor')};
}
export function assertMaterialFactors(expected,actual){same(materialFactors(expected),materialFactors(actual),'coat exact spec-defined material factors');}
// TextureInfo.texCoord=0; normalTextureInfo.scale=1;
// occlusionTextureInfo.strength=1. Preserve all other fields, actual map and
// sampler references. No inferred fallback for malformed explicit values.
export function textureDefaults(info,role='ordinary'){
  object(info,'TextureInfo');assert(has(info,'index')&&info.index!==null&&info.index!==undefined,'actual texture reference required');
  const out={...info},texCoord=has(info,'texCoord')?info.texCoord:0;
  assert(Number.isSafeInteger(texCoord)&&texCoord>=0,'texCoord nonnegative integer');out.texCoord=texCoord;
  if(role==='normal'||role==='occlusion'){
    const key=role==='normal'?'scale':'strength',v=has(info,key)?info[key]:1;
    assert(typeof v==='number'&&Number.isFinite(v)&&(role!=='occlusion'||v>=0&&v<=1),key+' finite schema value');out[key]=v;
  }
  return out;
}
export function assertTextureSampling(expected,actual,role='ordinary'){
  const binding=info=>{const normalized=textureDefaults(info,role);object(normalized.index,'resolved texture');return {...normalized,index:{sampler:normalized.index.sampler}};};
  same(binding(expected),binding(actual),'coat exact TextureInfo/default/sampler binding');
}
function primitiveRows(root){return root.listMeshes().flatMap(mesh=>mesh.listPrimitives().map((p,pi)=>({mesh:mesh.getName(),pi,p})));}
function rig(root){
  return root.listNodes().map(n=>({name:n.getName(),extras:n.getExtras(),matrix:n.getMatrix(),children:n.listChildren().map(c=>c.getName()),mesh:n.getMesh()?.getName()??null,weights:n.getWeights(),skin:n.getSkin()?{joints:n.getSkin().listJoints().map(j=>j.getName()),skeleton:n.getSkin().getSkeleton()?.getName()??null,ibm:Array.from(n.getSkin().getInverseBindMatrices().getArray())}:null}));
}
function clips(root){return root.listAnimations().map(a=>({name:a.getName(),extras:a.getExtras(),channels:a.listChannels().map(c=>({node:c.getTargetNode().getName(),path:c.getTargetPath(),interpolation:c.getSampler().getInterpolation(),input:Array.from(c.getSampler().getInput().getArray()),output:Array.from(c.getSampler().getOutput().getArray())}))}));}
// Read complete material definitions, including extension fields and every
// TextureInfo. Resolve array indices into the actual image/sampler definition;
// repacking table indices may change, physical sampling semantics may not.
function materialRecords(raw,coat){
  const n=raw.readUInt32LE(12),doc=JSON.parse(raw.subarray(20,20+n)),bin=raw.subarray(28+n);
  const image=i=>{const im=doc.images[i];assert(im&&im.bufferView!==undefined&&!im.uri,'embedded material image');const v=doc.bufferViews[im.bufferView];assert.equal(v.buffer,0);return {...im,bufferView:undefined,sha256:hash(bin.subarray(v.byteOffset??0,(v.byteOffset??0)+v.byteLength))};};
  const texture=i=>{const t=doc.textures[i];assert(t&&t.source!==undefined&&!t.extensions,'reviewed ordinary image texture');return {...t,source:image(t.source),sampler:t.sampler===undefined?null:doc.samplers[t.sampler]};};
  function walk(value,key=''){
    if(Array.isArray(value))return value.map(v=>walk(v,key));
    if(value&&typeof value==='object'){const out={};for(const k of Object.keys(value).sort())out[k]=(k==='index'&&/Texture$/.test(key))?texture(value[k]):walk(value[k],k);return out;}
    return value;
  }
  return doc.materials.filter(m=>(m.name===COAT)===coat).map(m=>walk(m));
}
function coatBindings(masterRaw,colorRaw,webRaw){
  const master=materialRecords(masterRaw,true),color=materialRecords(colorRaw,true),web=materialRecords(webRaw,true);assert.equal(master.length,1);assert.equal(color.length,1);assert.equal(web.length,1);
  for(const material of [color[0],web[0]]){
    const marker=material.extras?.chicago4d_cloth_microtexture;assert(marker&&marker.source_material===COAT&&marker.runtime_weave==='portable_maps_with_common_macro');
    same(master[0].extras,material.extras,'coat material derivative marker preserved from verified MASTER');
    assertMaterialFactors(master[0],material);
    const slots=m=>[m.pbrMetallicRoughness.baseColorTexture,m.pbrMetallicRoughness.metallicRoughnessTexture,m.normalTexture];
    for(let i=0;i<3;i++){const expected=slots(master[0])[i],actual=slots(material)[i];assert(expected&&actual?.index?.source,'all coat map slots remain bound');
      assertTextureSampling(expected,actual,i===2?'normal':'ordinary');
      if(i>0)assert.equal(actual.index.source.mimeType,'image/png','normal/ORM remain linear-data PNGs');
    }
  }
  same(color,web,'coat material/image/sampling exact to actual canonical JPEG-stage child');
}
function morphMetadata(root){
  return {meshes:root.listMeshes().map(m=>({name:m.getName(),extras:m.getExtras(),weights:m.getWeights(),primitives:m.listPrimitives().map(p=>({mode:p.getMode(),extras:p.getExtras(),targets:p.listTargets().map(t=>({name:t.getName(),extras:t.getExtras(),semantics:t.listSemantics().sort()}))}))})),nodes:root.listNodes().map(n=>{const mesh=n.getMesh(),count=mesh?.listPrimitives()[0]?.listTargets().length??0;return{name:n.getName(),effective_weights:n.getWeights().length?n.getWeights():mesh?.getWeights().length?mesh.getWeights():Array(count).fill(0)};})};
}
function degeneracy(p,ts){const pos=p.getAttribute('POSITION'),uv=p.getAttribute('TEXCOORD_0');const geometry=[],texture=[];
  for(let ti=0;ti<ts.length;ti++){const ids=ts[ti],P=ids.map(i=>vector(pos,i)),U=uv?ids.map(i=>vector(uv,i)):null,a=P[1].map((v,k)=>v-P[0][k]),b=P[2].map((v,k)=>v-P[0][k]);
    if(a[1]*b[2]===a[2]*b[1]&&a[2]*b[0]===a[0]*b[2]&&a[0]*b[1]===a[1]*b[0])geometry.push(ti);
    if(U&&(U[1][0]-U[0][0])*(U[2][1]-U[0][1])===(U[1][1]-U[0][1])*(U[2][0]-U[0][0]))texture.push(ti);
  }return {geometry,texture};
}
function winding(indices){return cycle(indices.map(String));}
async function runtime(dependencyRoot){
  for(const name of ['core','functions','extensions','cli'])assert.equal(JSON.parse(fs.readFileSync(path.join(dependencyRoot,'@gltf-transform',name,'package.json'))).version,'4.5.0');
  assert.equal(JSON.parse(fs.readFileSync(path.join(dependencyRoot,'mikktspace/package.json'))).version,'1.1.1');
  const {NodeIO}=require(path.join(dependencyRoot,'@gltf-transform/core')),{ALL_EXTENSIONS}=require(path.join(dependencyRoot,'@gltf-transform/extensions'));
  const {MeshoptDecoder}=await import(pathToFileURL(path.join(APP,'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js')));await MeshoptDecoder.ready;
  return {io:new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder}),mikk:require(path.join(dependencyRoot,'mikktspace'))};
}
export async function verifyMasterPair(recipeFile,inputRoot,masterRoot,dependencyRoot){
  const recipe=JSON.parse(fs.readFileSync(recipeFile)),{io,mikk}=await runtime(dependencyRoot),rows=[];
  for(const lod of [0,1]){
    const row=recipe.parents.find(r=>r.lod===lod&&!r.file.includes('/web/')),sourceRaw=fs.readFileSync(path.join(inputRoot,row.file)),childRaw=fs.readFileSync(path.join(masterRoot,path.basename(row.file)));assert.equal(hash(sourceRaw),row.sha256);
    const parent=await io.readBinary(sourceRaw),child=await io.readBinary(childRaw);
    same(rig(parent.getRoot()),rig(child.getRoot()),'MASTER actual decoded nodes/rig/frame/binds exact');same(clips(parent.getRoot()),clips(child.getRoot()),'MASTER all idle/walk channels exact');same(morphMetadata(parent.getRoot()),morphMetadata(child.getRoot()),'MASTER target names/semantic sets/order/defaults exact');same(materialRecords(sourceRaw,false),materialRecords(childRaw,false),'MASTER all noncoat material/sampling/extensions/images exact');
    const a=primitiveRows(parent.getRoot()),b=primitiveRows(child.getRoot());assert.equal(a.length,b.length);
    for(let k=0;k<a.length;k++){
      const {p}=a[k],q=b[k].p;assert.equal(a[k].mesh,b[k].mesh);assert.equal(p.getMode(),q.getMode());assert.equal(p.getMaterial().getName(),q.getMaterial().getName());
      const oldCorners=triangles(p).flat(),newCorners=triangles(q).flat();assert.equal(oldCorners.length,newCorners.length);
      if(p.getMaterial().getName()!==COAT){same(oldCorners.map(i=>rowKey(vertex(p,i))),newCorners.map(i=>rowKey(vertex(q,i))),'MASTER all noncoat expanded corners exact');continue;}
      const pos=[],norm=[],uv=[];for(const i of oldCorners){pos.push(...vector(p.getAttribute('POSITION'),i));const n=vector(p.getAttribute('NORMAL'),i),l=Math.hypot(...n);norm.push(...n.map(x=>x/l));uv.push(...vector(p.getAttribute('TEXCOORD_0'),i));}
      const expected=mikk.generateTangents(new Float32Array(pos),new Float32Array(norm),new Float32Array(uv));
      for(let c=0;c<oldCorners.length;c++){assert.equal(rowKey(vertex(p,oldCorners[c])),rowKey(vertex(q,newCorners[c])),'independent protected MASTER corner');const actual=vector(q.getAttribute('TANGENT'),newCorners[c]),want=Array.from(expected.subarray(c*4,c*4+4));want[3]*=-1;assert.deepEqual(actual,want,'actual official Mikk exact corner, no averaging');}
      rows.push({lod,mesh:a[k].mesh,corners:oldCorners.length,old_vertices:p.getAttribute('POSITION').getCount(),new_vertices:q.getAttribute('POSITION').getCount(),actual_Mikk_corners_exact:true});
    }
  }return {status:'INDEPENDENT_MASTER_MIKK_AND_DECODED_SEMANTICS_PASS_NOT_RENDER_ACCEPTANCE',rows,WEB_generated:false,rendered:false};
}
export async function verifyAll(recipeFile,inputRoot,masterRoot,webRoot,dependencyRoot,colorReferenceRoot){
  const recipeRaw=fs.readFileSync(recipeFile),recipe=JSON.parse(recipeRaw);
  for(const name of ['core','functions','extensions','cli'])assert.equal(JSON.parse(fs.readFileSync(path.join(dependencyRoot,'@gltf-transform',name,'package.json'))).version,'4.5.0');
  assert.equal(JSON.parse(fs.readFileSync(path.join(dependencyRoot,'mikktspace/package.json'))).version,'1.1.1');
  const {NodeIO}=require(path.join(dependencyRoot,'@gltf-transform/core')),{ALL_EXTENSIONS}=require(path.join(dependencyRoot,'@gltf-transform/extensions'));
  const {reorder,quantize}=require(path.join(dependencyRoot,'@gltf-transform/functions'));
  const {MeshoptEncoder}=require(path.join(dependencyRoot,'meshoptimizer'));
  const mikk=require(path.join(dependencyRoot,'mikktspace'));
  const {MeshoptDecoder}=await import(pathToFileURL(path.join(APP,'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js')));
  await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready]);
  const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});const findings=[];
  for(const lod of [0,1]){
    const sourceRow=recipe.parents.find(r=>r.lod===lod&&!r.file.includes('/web/')),webRow=recipe.parents.find(r=>r.lod===lod&&r.file.includes('/web/'));
    const sourceRaw=fs.readFileSync(path.join(inputRoot,sourceRow.file)),oldWebRaw=fs.readFileSync(path.join(inputRoot,webRow.file)),childRaw=fs.readFileSync(path.join(masterRoot,path.basename(sourceRow.file)));assert.equal(hash(sourceRaw),sourceRow.sha256);assert.equal(hash(oldWebRaw),webRow.sha256);
    const newWebRaw=fs.readFileSync(path.join(webRoot,path.basename(sourceRow.file))),parent=await io.readBinary(sourceRaw),child=await io.readBinary(childRaw),oldWeb=await io.readBinary(oldWebRaw),newWeb=await io.readBinary(newWebRaw);
    same(rig(parent.getRoot()),rig(child.getRoot()),'MASTER actual decoded nodes/rig/frame/binds exact');same(clips(parent.getRoot()),clips(child.getRoot()),'MASTER all idle/walk channels exact');
    same(rig(oldWeb.getRoot()),rig(newWeb.getRoot()),'WEB actual decoded nodes/rig/frame/binds exact');same(clips(oldWeb.getRoot()),clips(newWeb.getRoot()),'WEB all idle/walk channels exact');
    same(materialRecords(oldWebRaw,false),materialRecords(newWebRaw,false),'all noncoat WEB material/extensions/TextureInfo/sampling/images exact');
    same(morphMetadata(oldWeb.getRoot()),morphMetadata(newWeb.getRoot()),'WEB target names/semantic sets/order/effective defaults exact');
    const colorRaw=fs.readFileSync(path.join(colorReferenceRoot,path.basename(sourceRow.file)));
    coatBindings(childRaw,colorRaw,newWebRaw);
    assert.deepEqual(oldWeb.getRoot().listScenes().map(s=>s.getExtras()),newWeb.getRoot().listScenes().map(s=>s.getExtras()),'identity/provenance unchanged');
    const originalRows=primitiveRows(parent.getRoot()),childRows=primitiveRows(child.getRoot()),oldRows=primitiveRows(oldWeb.getRoot()),newRows=primitiveRows(newWeb.getRoot());
    assert.equal(originalRows.length,childRows.length);assert.equal(oldRows.length,newRows.length);
    // Verify Mikk independently through decoded MASTER component streams; no
    // generator mapping/receipt is trusted. Original triangle order is retained.
    for(let k=0;k<originalRows.length;k++){
      const {p}=originalRows[k],q=childRows[k].p;assert.equal(originalRows[k].mesh,childRows[k].mesh);
      if(p.getMaterial().getName()!==COAT)continue;
      const oldCorners=triangles(p).flat(),newCorners=triangles(q).flat();assert.equal(oldCorners.length,newCorners.length);
      const pos=[],norm=[],uv=[];for(const i of oldCorners){pos.push(...vector(p.getAttribute('POSITION'),i));const n=vector(p.getAttribute('NORMAL'),i),l=Math.hypot(...n);norm.push(...n.map(x=>x/l));uv.push(...vector(p.getAttribute('TEXCOORD_0'),i));}
      const expected=mikk.generateTangents(new Float32Array(pos),new Float32Array(norm),new Float32Array(uv));
      for(let c=0;c<oldCorners.length;c++){assert.equal(rowKey(vertex(p,oldCorners[c])),rowKey(vertex(q,newCorners[c])),'independent decoded protected MASTER corner');const tangent=vector(q.getAttribute('TANGENT'),newCorners[c]);const want=Array.from(expected.subarray(c*4,c*4+4));want[3]*=-1;assert.deepEqual(tangent,want,'actual official Mikk exact corner; no handedness averaging');}
    }
    // Reconstruct the repository's existing medium/scene/16-normal codec in
    // RAM only. Record original source triangle identities before quantization;
    // neither this reference nor its temporary mapping is written as an asset.
    const reference=await io.readBinary(sourceRaw),rr=primitiveRows(reference.getRoot());
    const sourceFaces=rr.map(({p})=>{const map=new Map();for(const ids of triangles(p)){const key=triangleKey(p,ids);const queue=map.get(key)??[];queue.push(winding(ids));map.set(key,queue);}return map;});
    await reference.transform(reorder({encoder:MeshoptEncoder,target:'size'}));
    const faceMap=primitiveRows(reference.getRoot()).map(({p},k)=>triangles(p).map(ids=>{const queue=sourceFaces[k].get(triangleKey(p,ids));assert(queue?.length,'reference reorder must preserve every source triangle/winding');return queue.shift();}));
    assert(sourceFaces.every(m=>[...m.values()].every(q=>q.length===0)),'every source triangle used once');
    await reference.transform(quantize({pattern:/.*/,patternTargets:/.*/,quantizationVolume:'scene',quantizeNormal:16}));
    const refs=primitiveRows(reference.getRoot());assert.equal(refs.length,oldRows.length);
    const tangentReference=await io.readBinary(childRaw);
    await tangentReference.transform(reorder({encoder:MeshoptEncoder,target:'size'}),quantize({pattern:/.*/,patternTargets:/.*/,quantizationVolume:'scene',quantizeNormal:16}));
    const tangentRefs=primitiveRows(tangentReference.getRoot());assert.equal(tangentRefs.length,newRows.length);
    const rows=[];
    for(let k=0;k<oldRows.length;k++){
      const o=oldRows[k],n=newRows[k],ref=refs[k];assert.equal(o.mesh,n.mesh);assert.equal(o.mesh,ref.mesh);assert.equal(o.pi,n.pi);
      assert.equal(o.p.getMaterial().getName(),n.p.getMaterial().getName(),'original exact material binding per primitive');
      assert.deepEqual(attributes(o.p),attributes(n.p),'protected semantic membership');
      const oldTriangles=triangles(o.p),newTriangles=triangles(n.p),refTriangles=triangles(ref.p);
      const oldKeys=oldTriangles.map(t=>triangleKey(o.p,t)),newKeys=newTriangles.map(t=>triangleKey(n.p,t)),refKeys=refTriangles.map(t=>triangleKey(ref.p,t));
      same(multiset(oldKeys),multiset(refKeys),'old WEB must match exact pinned codec reference; otherwise STOP, no epsilon');
      same(multiset(oldKeys),multiset(newKeys),'all expanded WEB PN/UV/J/W/morph values exact to proven old codec; winding retained');
      same(multiset(newTriangles.map(t=>tangentTriangleKey(n.p,t))),multiset(triangles(tangentRefs[k].p).map(t=>tangentTriangleKey(tangentRefs[k].p,t))),'actual WEB tangent groups/handedness equal independently pinned codec of verified Mikk MASTER');
      const sourceByKey=new Map();refKeys.forEach((key,i)=>{const q=sourceByKey.get(key)??[];q.push(faceMap[k][i]);sourceByKey.set(key,q);});
      const sourceIds=oldKeys.map(key=>{const q=sourceByKey.get(key);assert(q?.length);return q.shift();});
      const baseline=degeneracy(o.p,oldTriangles),actual=degeneracy(n.p,newTriangles);
      // Match degen faces semantically, not by optimizer-dependent row index.
      for(const kind of ['geometry','texture'])assert.deepEqual(multiset(baseline[kind].map(i=>oldKeys[i])),multiset(actual[kind].map(i=>newKeys[i])),'no NEW or removed '+kind+' degen faces');
      if(o.p.getMaterial().getName()!==COAT)assert(!n.p.getAttribute('TANGENT'),'noncoat tangent/default behavior unchanged');
      else assert(n.p.getAttribute('TANGENT'),'near coat portable normal map requires actual WEB tangents');
      rows.push({mesh:o.mesh,primitive:o.pi,triangles:oldTriangles.length,semantic_multiset_sha256:hash(JSON.stringify(multiset(oldKeys))),baseline_geometry_degenerate:baseline.geometry.length,baseline_uv_degenerate:baseline.texture.length,baseline_geometry_source_faces:baseline.geometry.map(i=>sourceIds[i]),baseline_uv_source_faces:baseline.texture.map(i=>sourceIds[i]),new_geometry_degenerate:actual.geometry.length,new_uv_degenerate:actual.texture.length});
    }
    findings.push({lod,old_web_sha256:hash(oldWebRaw),new_web_sha256:hash(fs.readFileSync(path.join(webRoot,path.basename(sourceRow.file)))),rows});
  }
  return {status:'EXACT_PINNED_CODEC_SEMANTICS_ONLY',recipe_sha256:hash(recipeRaw),codec:'actual repository4.5.0 medium/scene/normal16',findings,images_decoded:false,native_GLTFLoader_render_fit_budget_photo:'UNRUN'};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv[2]==='--master-only'){
    const [recipe,inputs,masters,dependencies]=process.argv.slice(3);assert(recipe&&inputs&&masters&&dependencies,'--master-only RECIPE INPUT_ROOT MASTER_CHILD_DIR PINNED_NODE_MODULES');console.log(JSON.stringify(await verifyMasterPair(recipe,inputs,masters,dependencies),null,2));
  }else{
    const [recipe,inputs,masters,web,dependencies,color]=process.argv.slice(2);assert(recipe&&inputs&&masters&&web&&dependencies&&color,'RECIPE INPUT_ROOT MASTER_CHILD_DIR WEB_CHILD_DIR PINNED_NODE_MODULES CANONICAL_COLOR_REFERENCE_DIR');console.log(JSON.stringify(await verifyAll(recipe,inputs,masters,web,dependencies,color),null,2));
  }
}
