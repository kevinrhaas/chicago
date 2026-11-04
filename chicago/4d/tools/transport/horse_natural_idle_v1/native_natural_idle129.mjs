// First-class NEW8ea natural planted idle producer; exact bd443 parent, no old verdict transfer.
// Source-only standalone loader/Mixer proof; no renderer or app injection.

import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkinned} from 'three/addons/utils/SkeletonUtils.js';
const need=(x,message)=>{if(!x)throw Error(message);};
const get=(a,i,k)=>k===0?a.getX(i):k===1?a.getY(i):k===2?a.getZ(i):a.getW(i);
const bytesEqual=(a,b)=>a.byteLength===b.byteLength&&new Uint8Array(a.buffer,a.byteOffset,a.byteLength).every((v,i)=>v===new Uint8Array(b.buffer,b.byteOffset,b.byteLength)[i]);
const pixelHashes=new WeakMap();
async function textureInfo(texture){
 if(!texture)return null;
 const image=texture.image;need(image&&image.width&&image.height,'actual decoded map image unavailable');
 let pixel_sha256=pixelHashes.get(image);
 if(!pixel_sha256){const canvas=new OffscreenCanvas(image.width,image.height),ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,image.width,image.height).data;pixel_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',pixels)),v=>v.toString(16).padStart(2,'0')).join('');pixelHashes.set(image,pixel_sha256);}
 return{width:image.width,height:image.height,pixel_sha256,colorSpace:texture.colorSpace,flipY:texture.flipY,channel:texture.channel,wrapS:texture.wrapS,wrapT:texture.wrapT,minFilter:texture.minFilter,magFilter:texture.magFilter,offset:texture.offset.toArray(),repeat:texture.repeat.toArray(),rotation:texture.rotation};
}
async function maps(model){const rows=[];for(const m of model.meshes){const slots=[];for(const material of[].concat(m.material)){const textures={};for(const key of['map','normalMap','roughnessMap','metalnessMap','aoMap','emissiveMap','alphaMap','bumpMap','lightMap'])textures[key]=await textureInfo(material[key]);slots.push({name:material.name,type:material.type,color:material.color?.toArray(),side:material.side,roughness:material.roughness,metalness:material.metalness,opacity:material.opacity,alphaTest:material.alphaTest,transparent:material.transparent,normalScale:material.normalScale?.toArray(),textures});}rows.push({mesh_key:m.userData.parityKey,materials:slots});}return rows;}
async function load(url,raw){
 const gltf=await new GLTFLoader().parseAsync(raw,location.origin+'/');
 gltf.scene.traverse(o=>{if(o.isSkinnedMesh){const a=gltf.parser.associations.get(o);need(a&&Number.isInteger(a.meshes)&&Number.isInteger(a.primitives),'Parser correspondence');o.userData.parityKey=a.meshes+':'+a.primitives;}});
 const scene=cloneSkinned(gltf.scene),meshes=[];scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});meshes.sort((a,b)=>a.userData.parityKey.localeCompare(b.userData.parityKey));need(meshes.length===3&&new Set(meshes.map(m=>m.userData.parityKey)).size===3,'Three unique cloned primitives');
 const bind=[];scene.traverse(o=>bind.push([o,o.position.clone(),o.quaternion.clone(),o.scale.clone()]));return{...gltf,scene,meshes,bind,mixer:new T.AnimationMixer(scene)};
}
function pose(model,clip,time){model.mixer.stopAllAction();for(const[o,p,q,s]of model.bind){o.position.copy(p);o.quaternion.copy(q);o.scale.copy(s);}if(clip!==null){const selected=model.naturalIdleSelected===true?1:clip;const action=model.mixer.clipAction(model.animations[selected]);action.reset();action.setLoop(T.LoopOnce,1);action.clampWhenFinished=true;action.play();model.mixer.setTime(time);}model.scene.updateMatrixWorld(true);for(const m of model.meshes)m.skeleton.update();}
function cache(mesh){
 const g=mesh.geometry,position=g.attributes.position,normal=g.attributes.normal,skinIndex=g.attributes.skinIndex,skinWeight=g.attributes.skinWeight,index=g.index;
 need(position&&normal&&skinIndex&&skinWeight&&index,'indexed normal/skinned geometry required');need(!Object.values(g.morphAttributes).some(a=>a.length),'morphs require separate explicit handling');
 const ids=Array.from({length:position.count},(_,i)=>i),j=new Uint32Array(position.count*4),w=new Float64Array(position.count*4),bn=new Float64Array(position.count*3),B=mesh.bindMatrix.elements;let zeroOut=0;
 for(const i of ids){need(i>=0&&i<position.count,'index outside position buffer');const x=normal.getX(i),y=normal.getY(i),z=normal.getZ(i);bn.set([B[0]*x+B[4]*y+B[8]*z,B[1]*x+B[5]*y+B[9]*z,B[2]*x+B[6]*y+B[10]*z],i*3);for(let k=0;k<4;k++){j[i*4+k]=get(skinIndex,i,k);w[i*4+k]=get(skinWeight,i,k);if(w[i*4+k]!==0)need(j[i*4+k]<mesh.skeleton.bones.length,'positive weight outside actual bone palette');else if(j[i*4+k]>=mesh.skeleton.bones.length)zeroOut++;}}
 return{mesh,position,normal,index,ids,j,w,bn,zero_weight_out_of_palette_components:zeroOut};
}
function normalContext(c){
 const m=c.mesh,b=m.skeleton.boneMatrices;for(let i=0;i<b.length;i+=16)need(b[i+3]===0&&b[i+7]===0&&b[i+11]===0&&b[i+15]===1,'nonaffine bone matrices unsupported');
 // Exact affine factorization of ShaderChunk.skinnormal_vertex and
 // defaultnormal_vertex with identity view: normalMatrix(world) * B^-1 *
 // [sum(w_j * actual GPU boneMatrix_j)] * B * vec4(normal,0).
 // Deliberately no inverse transpose of the weighted bone blend.
 return{b,prefix:new T.Matrix3().getNormalMatrix(m.matrixWorld).multiply(new T.Matrix3().setFromMatrix4(m.bindMatrixInverse))};
}
function shaderNormal(c,frame,i,out){const q=i*3,bx=c.bn[q],by=c.bn[q+1],bz=c.bn[q+2],b=frame.b;let x=0,y=0,z=0;for(let k=0;k<4;k++){const w=c.w[i*4+k];if(w===0)continue;const o=c.j[i*4+k]*16;x+=w*(b[o]*bx+b[o+4]*by+b[o+8]*bz);y+=w*(b[o+1]*bx+b[o+5]*by+b[o+9]*bz);z+=w*(b[o+2]*bx+b[o+6]*by+b[o+10]*bz);}out.set(x,y,z).applyMatrix3(frame.prefix);need(Number.isFinite(out.lengthSq())&&out.lengthSq()>1e-24,'degenerate/nonfinite shader normal');return out.normalize();}

const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
async function pinned(pin){const r=await fetch(pin.url,{cache:'no-cache'});need(r.ok,'Actual proof resource HTTP '+pin.url);const b=await r.arrayBuffer();need(b.byteLength===pin.bytes&&await digest(b)===pin.sha256,'Actual proof bytes '+pin.url);return b;}
const json=bytes=>JSON.parse(new TextDecoder().decode(bytes));
function glb(raw){const v=new DataView(raw),n=v.getUint32(12,true);need(v.getUint32(0,true)===0x46546c67&&v.getUint32(4,true)===2&&v.getUint32(8,true)===raw.byteLength&&v.getUint32(16,true)===0x4e4f534a,'GLB header');return{doc:json(raw.slice(20,20+n)),bin:new Uint8Array(raw,28+n)};}
function rawAttribute(g,mi,name){const a=g.doc.accessors[g.doc.meshes[mi].primitives[0].attributes[name]],v=g.doc.bufferViews[a.bufferView],C=a.componentType===5123?Uint16Array:a.componentType===5126?Float32Array:null;need(C&&!v.byteStride&&!a.sparse&&!a.normalized,'Direct source-bound raw accessor');return new C(g.bin.buffer,g.bin.byteOffset+(v.byteOffset??0)+(a.byteOffset??0),a.count*(a.type==='VEC3'?3:4)).slice();}
const rint=x=>{const f=Math.floor(x),d=x-f;return d===.5?(f%2===0?f:f+1):Math.round(x);};
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const cross3=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot3=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const norm3=a=>Math.hypot(...a);
const xyz=(a,i)=>[a[i*3],a[i*3+1],a[i*3+2]];
function expectedBones(world,inverses){const b=new Float64Array(26*16);for(let i=0;i<26;i++)new T.Matrix4().set(...world[i].flat()).multiply(inverses[i]).toArray(b,i*16);return b;}
function affineSkin(c,b,i,out){const x=c.position.getX(i),y=c.position.getY(i),z=c.position.getZ(i);let px=0,py=0,pz=0;for(let k=0;k<4;k++){const w=c.w[i*4+k];if(!w)continue;const o=c.j[i*4+k]*16;px+=w*(b[o]*x+b[o+4]*y+b[o+8]*z+b[o+12]);py+=w*(b[o+1]*x+b[o+5]*y+b[o+9]*z+b[o+13]);pz+=w*(b[o+2]*x+b[o+6]*y+b[o+10]*z+b[o+14]);}return out.set(px,py,pz);}
function identity(matrix){const a=matrix.elements,b=new T.Matrix4().elements;return a.every((v,i)=>Math.abs(v-b[i])<=1e-12);}
function denseAt(c,i){const a=new Float64Array(26);for(let k=0;k<4;k++)a[c.j[i*4+k]]+=c.w[i*4+k];return a;}
function chainErrors(nodes,pivots,limbs){let length=0,parent=0;for(const row of Object.values(limbs))for(let k=0;k<4;k++){const a=row.joints[k],b=row.joints[k+1],pa=new T.Vector3().setFromMatrixPosition(nodes[a].matrixWorld),pb=new T.Vector3().setFromMatrixPosition(nodes[b].matrixWorld),offset=new T.Vector3().fromArray(sub(pivots[b],pivots[a]));length=Math.max(length,Math.abs(pa.distanceTo(pb)-offset.length()));const expected=offset.clone().applyMatrix4(nodes[a].matrixWorld);parent=Math.max(parent,expected.distanceTo(pb));}return{length,parent};}
function maxContact(moved,rest,patches){let worst={gap:0};for(const[label,ids]of Object.entries(patches))for(const i of ids){const gap=distance(xyz(moved[1],i),rest[1][i]);if(gap>worst.gap)worst={gap,label,vertex:i,actual:xyz(moved[1],i),expected:rest[1][i]};}return worst;}


function rawValues(g, mi, name) {
 const index=name==='indices'?g.doc.meshes[mi].primitives[0].indices:g.doc.meshes[mi].primitives[0].attributes[name];
 const a=g.doc.accessors[index],v=g.doc.bufferViews[a.bufferView],count={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];
 need(!a.sparse&&!a.normalized&&count,'Explicit dense semantic stream');
 const step={5121:1,5123:2,5125:4,5126:4}[a.componentType],view=new DataView(g.bin.buffer,g.bin.byteOffset,g.bin.byteLength);
 const read={5121:'getUint8',5123:'getUint16',5125:'getUint32',5126:'getFloat32'}[a.componentType];
 const offset=(v.byteOffset??0)+(a.byteOffset??0),stride=v.byteStride??step*count,result=[];
 for(let i=0;i<a.count;i++)for(let k=0;k<count;k++)result.push(view[read](offset+i*stride+k*step,true));
 return {values:result,count,rows:a.count};
}
function prefixEqual(a,b){return a.length<=b.length&&a.every((v,i)=>Object.is(v,b[i]));}
// Explicit new eye-NORMAL-only admission. No old master/policy constant is reassigned.
function normalChildSourceGuard(parent,child){
 need(parent.bin.length===child.bin.length,'New child BIN length fixed');
 const a=parent.doc.accessors[208],v=parent.doc.bufferViews[a.bufferView];
 need(a.componentType===5126&&a.type==='VEC3'&&a.count===3968&&!a.sparse&&!a.normalized,'Explicit dense3968eye NORMAL source');
 const start=(v.byteOffset??0)+(a.byteOffset??0),stride=v.byteStride??12;
 const allowed=new Set();for(let row=0;row<a.count;row++)for(let k=0;k<12;k++)allowed.add(start+row*stride+k);
 let changes=0;for(let i=0;i<parent.bin.length;i++)if(parent.bin[i]!==child.bin[i]){need(allowed.has(i),'Protected NORMAL-child BIN byte');changes++;}
 need(changes===37722,'Exact reviewed NORMAL-child byte difference');
 const clean=structuredClone(child.doc);for(const k of ['min','max'])clean.accessors[208][k]=parent.doc.accessors[208][k];
 need(JSON.stringify(clean)===JSON.stringify(parent.doc),'Only NORMAL208extrema may change in JSON');
 const p=rawValues(child,2,'POSITION').values,n=rawValues(child,2,'NORMAL').values;
 need(n.length===3968*3,'New child eye NORMAL count');
 for(let i=0;i<n.length;i+=3){
  const center=p[i]<0?[-.08190010690063015,1.5196372239921074,1.3421662949986715]:[.08116699382591966,1.5196359365078531,1.3421654682847983];
  const r=[p[i]-center[0],p[i+1]-center[1],p[i+2]-center[2]],length=Math.hypot(...r),unit=Math.hypot(n[i],n[i+1],n[i+2]);
  need(Math.abs(unit-1)<1e-7&&(r[0]*n[i]+r[1]*n[i+1]+r[2]*n[i+2])/length>.9999999,'Actual child radial outward unit eye normals');
 }
}
// Exact animation-only admission. The old NORMAL admission above remains genuine.
function naturalIdleSourceGuard(parent,child,recipe){
 need(child.bin.length===parent.bin.length+4160&&bytesEqual(parent.bin,child.bin.subarray(0,parent.bin.length)),'Entire bd443 BIN prefix exact, exactly4new quaternion streams');
 need(recipe.source_parent_sha256==='bd443df87b92d19266284cb9b52d30e791215cddf099876c774e9cfb5f5a79b6'&&recipe.candidate_clip==='sevket_reconstructed_natural_planted_idle_v1','Explicit actual reconstructed natural-idle recipe');
 need(child.doc.animations.length===2&&child.doc.animations[1].channels.length===17&&child.doc.animations[1].samplers.length===17,'Exact two-clip/new17channel inventory');
 const old=parent.doc.animations[0],clip=child.doc.animations[1],targets=[2,3,4,5],input=old.samplers[0].input;
 need(JSON.stringify(clip.channels.slice(0,13))===JSON.stringify(old.channels)&&JSON.stringify(clip.samplers.slice(0,13))===JSON.stringify(old.samplers),'All old13 selected tracks exact');
 for(let k=0;k<4;k++){
  const output=parent.doc.accessors.length+k,view=parent.doc.bufferViews.length+k;
  need(JSON.stringify(clip.channels[13+k])===JSON.stringify({sampler:13+k,target:{node:targets[k],path:'rotation'}}),'Only new declared4rotation targets');
  need(JSON.stringify(clip.samplers[13+k])===JSON.stringify({input,output,interpolation:'LINEAR'}),'Exact new4selected sampler bindings');
  const a=child.doc.accessors[output],v=child.doc.bufferViews[view];need(a.bufferView===view&&a.componentType===5126&&a.count===65&&a.type==='VEC4'&&v.buffer===0&&v.byteOffset===parent.bin.length+1040*k&&v.byteLength===1040,'Exact4new65FLOAT output views');
  const values=new Float32Array(child.bin.buffer,child.bin.byteOffset+v.byteOffset,260);for(let i=0;i<65;i++)need(Math.abs(Math.hypot(...values.slice(4*i,4*i+4))-1)<1e-6,'Unit actual new quaternion');
 }
 const restored=structuredClone(child.doc);restored.accessors=restored.accessors.slice(0,parent.doc.accessors.length);restored.bufferViews=restored.bufferViews.slice(0,parent.doc.bufferViews.length);restored.animations=restored.animations.slice(0,1);restored.buffers[0].byteLength=parent.doc.buffers[0].byteLength;delete restored.asset.extras.chicago4d_natural_planted_idle_v1;
 need(JSON.stringify(restored)===JSON.stringify(parent.doc),'Every unlisted bd443 document field exact');
}
window.compare=async()=>{
 const started=performance.now(),config=await(await fetch('/CONFIG.json')).json();let source,candidate;
 const report=window.cpuReport={status:'NEW_NATURAL_IDLE_LOADED129_INCOMPLETE',key_count:0,midpoint_count:0,poses:[],normalization:[],failures:[],positions:{tolerance_m:1e-5,maximum_delta_m:0,evaluations:0},normals:{tolerance_degrees:.01,maximum_angle_degrees:0,evaluations:0},joint_world:{maximum_translation_error_m:0,maximum_matrix_component_error:0},physical:{maximum_segment_length_error_m:0,maximum_parent_residual_m:0,maximum_seam_gap_m:0,maximum_contact_error_m:0},WebGL_contexts_created:0,renderers_created:0,walking_enabled:false,head_tail_composed:true,selected_exported_clip_index:1,selected_exported_track_count:17,photographic_acceptance:false};
 const fail=(condition,label,witness)=>{if(!condition&&report.failures.length<100)report.failures.push({label,witness});};
 try{
  need(T.REVISION==='185','Actual project Three revision');
  need(T.ShaderChunk.skinnormal_vertex.includes('skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;')&&T.ShaderChunk.defaultnormal_vertex.includes('transformedNormal = normalMatrix * transformedNormal;'),'Native shader normal algebra');
  report.shader_normal_algebra='normalMatrix(meshWorld) * bindInverse * weighted Float32 boneMatrices * bind * normal; no inverse-transpose of weighted blend';
  const entries=await Promise.all(Object.entries(config.inputs).map(async([k,p])=>[k,await pinned(p)])),resources=Object.fromEntries(entries);
  const reference=json(resources.cpu_reference),frames=json(resources.expected_matrices).frames,controls=json(resources.controls26),limit=json(resources.limits),derivation=json(resources.anatomy_receipt);
  need(config.inputs.selected_parent.sha256==='d4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914'&&derivation.parent_sha256===config.inputs.selected_parent.sha256&&derivation.candidate_sha256===config.inputs.legacy_parent.sha256,'Actual d454 and legacy925 foot ancestry, not replacement face ancestry');
  need(config.inputs.legacy_parent.sha256==='925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48'&&config.inputs.candidate.sha256==='8ea7748ffba6c5fe17cde91042c6d8b26ed9a0ab77de69cadd4f4fb12e9c09fa'&&config.inputs.idle_parent.sha256==='bd443df87b92d19266284cb9b52d30e791215cddf099876c774e9cfb5f5a79b6'&&config.inputs.normal_parent.sha256==='e49b6f1c9f7b70f1fcdf19fa7f6dddf54048b32256b4d8030d6238d6dfe79d49','Exact source socket candidate');
  const staticProof=json(resources.static_socket_receipt),socketRecipe=json(resources.socket_recipe),legacyRaw=glb(resources.legacy_parent);
  need(staticProof.status==='NATURAL_IDLE_CURRENT_SOURCE_STATIC_ONLY_PASS'&&staticProof.source_admission==='natural_planted_idle_v1'&&staticProof.collision_mode==='canonical_socket_interface_v1'&&staticProof.collision_reference925_sha256===config.inputs.legacy_parent.sha256&&staticProof.motion_parent_bd443_sha256===config.inputs.idle_parent.sha256&&staticProof.candidate_sha256===config.inputs.candidate.sha256&&JSON.stringify(staticProof.code_pins)===JSON.stringify(config.code_pins),'Actual new-mode static proof and same implementation required');
  need(socketRecipe.maximum_original_source_displacement_m===.020&&socketRecipe.maximum_parent_displacement_m===.020&&socketRecipe.maximum_internal_BODY_UV_displacement===.00030,'Unchanged source displacement and two UV repair bounds');
  const originalRaw=glb(resources.original),parentRaw=glb(resources.selected_parent),candidateRaw=glb(resources.candidate);
  const normalParentRaw=glb(resources.normal_parent);
  need(bytesEqual(parentRaw.bin,normalParentRaw.bin.subarray(0,parentRaw.bin.length)),'Historical e49 preserves every original d454 BIN byte');
  const idleParentRaw=glb(resources.idle_parent);normalChildSourceGuard(normalParentRaw,idleParentRaw);naturalIdleSourceGuard(idleParentRaw,candidateRaw,json(resources.motion_recipe));
  need(JSON.stringify(parentRaw.doc.nodes)===JSON.stringify(normalParentRaw.doc.nodes),'Actual e49 rig remains unchanged');
  for(const key of ['nodes','skins','materials','images','textures','samplers','scenes'])need(JSON.stringify(parentRaw.doc[key])===JSON.stringify(candidateRaw.doc[key]),'Protected live rig/image/material graph '+key);need(JSON.stringify(parentRaw.doc.animations)===JSON.stringify(candidateRaw.doc.animations.slice(0,1)),'Exact retained old13trackclip graph');
  for(const mi of [0,2])need(JSON.stringify(parentRaw.doc.meshes[mi])===JSON.stringify(candidateRaw.doc.meshes[mi]),'Hair and eye stream selection exact');
  need(frames.length===65&&frames[0].time_s===0&&frames[64].time_s===12,'Unchanged independently accepted65 timeline');
  [source,candidate]=await Promise.all([load(config.inputs.original.url,resources.original),load(config.inputs.candidate.url,resources.candidate)]);
  need(source.animations.length===0&&candidate.animations.length===2&&candidate.animations[0].name==='sevket_reconstructed_planted_posture_v1'&&candidate.animations[0].duration===12&&candidate.animations[0].tracks.length===13&&candidate.animations[1].name==='sevket_reconstructed_natural_planted_idle_v1'&&candidate.animations[1].duration===12&&candidate.animations[1].tracks.length===17,'Explicit retained13track plus actual selected second17track clip');candidate.naturalIdleSelected=true;
  for(const track of candidate.animations[1].tracks)need(track.getInterpolation()===T.InterpolateLinear&&track.times.length===65&&track.times.every((t,i)=>t===frames[i].time_s),'Actual selected17 imported65 linear key streams');
  const expectedInput=json(resources.expected_matrices);need(expectedInput.schema==='natural_planted_idle_independent_expected65_v1'&&expectedInput.parent65_sha256===config.inputs.accepted_matrices.sha256&&expectedInput.motion_recipe_sha256===config.inputs.motion_recipe.sha256&&expectedInput.controls26_sha256===config.inputs.controls26.sha256,'Independent new65 expectation binds old65, exact motion recipe and unchanged hierarchy');
  pose(source,null,null);pose(candidate,0,0);
  const [sourceMaps,candidateMaps]=await Promise.all([maps(source),maps(candidate)]);need(JSON.stringify(sourceMaps)===JSON.stringify(candidateMaps),'Actual decoded source image/material equality');report.decoded_maps_equal=true;
  const raw=[],rawParent=[];for(let mi=0;mi<3;mi++){
   raw.push({j:rawAttribute(candidateRaw,mi,'JOINTS_0'),w:rawAttribute(candidateRaw,mi,'WEIGHTS_0')});
   rawParent.push({j:rawAttribute(parentRaw,mi,'JOINTS_0'),w:rawAttribute(parentRaw,mi,'WEIGHTS_0')});
   need(prefixEqual([...rawParent[mi].j],[...raw[mi].j])&&prefixEqual([...rawParent[mi].w],[...raw[mi].w]),'All original accepted V16 skin rows remain exact');
  }
  const knownReference=json(resources.accepted_known),knownRows=new Map(knownReference.rows.map(r=>[r.class_id,r]));
  need(knownReference.protected_non_tail_classes===5605&&knownReference.phase_a_arrays_sha256===config.inputs.phase_a_arrays.sha256,'Accepted PhaseA declaration lineage');
  const tailClasses=new Set(reference.tail_vertex_ids.map(i=>reference.vertex_classes[0][i])),protectedSet=new Set(reference.source_protected_classes);
  need(tailClasses.size===901&&protectedSet.size===6506&&reference.tail_vertex_ids.length===969,'Original protected/tail inventory');
  const sc=source.meshes.map(cache),cc=candidate.meshes.map(cache),rc=cc.map((c,i)=>({...c,j:raw[i].j,w:raw[i].w}));
  const nodes=candidate.meshes[0].skeleton.bones;
  for(let i=0;i<26;i++){need(candidate.meshes.every(m=>m.skeleton.bones[i]===nodes[i]),'Shared cloned joint identity');need(nodes[i].name===candidateRaw.doc.nodes[i].name,'Actual cloned node identity');const p=controls.nodes[i].parent_index;if(p!==null)need(nodes[i].parent===nodes[p],'Actual cloned parent chain');}
  const rest=cc.map((c,mi)=>{const a=rawValues(candidateRaw,mi,'POSITION');need(a.count===3&&a.rows===c.position.count,'Serialized canonical rest inventory');return Array.from({length:a.rows},(_,i)=>a.values.slice(3*i,3*i+3));});
  const pivots=frames[0].global_canonical_matrices.map(m=>[m[0][3],m[1][3],m[2][3]]);
  for(let mi=0;mi<3;mi++){
   const b=cc[mi];need(identity(b.mesh.matrixWorld)&&identity(b.mesh.bindMatrix)&&identity(b.mesh.bindMatrixInverse),'Canonical identity mesh/bind basis');
   for(let j=0;j<26;j++)need(sc[mi].mesh.skeleton.boneInverses[j].elements.every((v,k)=>v===b.mesh.skeleton.boneInverses[j].elements[k]),'Original inverse binds');
   let changed=0,max=0;for(let i=0;i<b.position.count;i++){
    const slots=Array.from({length:4},(_,k)=>raw[mi].w[4*i+k]),sum=slots.reduce((s,v)=>s+Math.abs(v),0);need(sum>0,'Positive skin mass');
    for(let k=0;k<4;k++){need(b.j[i*4+k]===raw[mi].j[i*4+k]&&Object.is(b.w[i*4+k],Math.fround(slots[k]*(1/sum))),'Independent actual loader normalization');max=Math.max(max,Math.abs(b.w[i*4+k]-slots[k]));}
    const ci=reference.vertex_classes[mi][i];if(i<reference.vertex_classes[mi].length&&protectedSet.has(ci)&&!tailClasses.has(ci)){
     const known=knownRows.get(ci);need(known,'Every original protected non-tail class retained');const expected=denseAt({j:known.joints,w:known.weights},0),actual=denseAt(raw[mi],i);need(expected.every((v,j)=>Object.is(v,actual[j])),'Original accepted PhaseA semantic-vector bits');changed++;
    }
   }
   report.normalization.push({mesh:mi,original_protected_rows_checked:changed,maximum_loader_component_delta:max,new_rows_checked:Math.max(0,b.position.count-reference.vertex_classes[mi].length)});
  }
  for(const i of reference.tail_vertex_ids)for(let k=0;k<4;k++)need(sc[0].j[i*4+k]===cc[0].j[i*4+k]&&Object.is(sc[0].w[i*4+k],cc[0].w[i*4+k]),'Same-loader original tail slots/bits');
  const ancestry=derivation.source_boundary.hoof_refinement,oldBody=rawValues(parentRaw,1,'POSITION').rows,newBody=cc[1].position.count;
  need(ancestry.original_vertices===oldBody&&ancestry.new_vertices===newBody&&ancestry.added_vertices.length===newBody-oldBody,'Complete new-vertex ancestry');
  const parentFacesForAncestry=rawValues(parentRaw,1,'indices').values;
  const parentUV=rawValues(parentRaw,1,'TEXCOORD_0').values,candidateUV=rawValues(candidateRaw,1,'TEXCOORD_0').values;
  const parentUV1=rawValues(parentRaw,1,'TEXCOORD_1').values,candidateUV1=rawValues(candidateRaw,1,'TEXCOORD_1').values;
  const legacyUV=rawValues(legacyRaw,1,'TEXCOORD_0').values,legacyUV1=rawValues(legacyRaw,1,'TEXCOORD_1').values;
  need(candidateUV.length===legacyUV.length&&candidateUV.every((v,i)=>Object.is(v,candidateUV1[i])),'Same BODY UV aliases and unchanged925 row count');
  const uvRepairs=new Map([[2410,[2372,2373,2411]],[2412,[2374,2375,2413]]]);
  for(let row=0;row<legacyUV.length/2;row++)for(let k=0;k<2;k++){
   if(uvRepairs.has(row))need(Object.is(candidateUV[2*row+k],Math.fround(uvRepairs.get(row).reduce((sum,i)=>sum+legacyUV[2*i+k],0)/3)),'Exact source-bound internal head UV barycentre');
   else need(Object.is(candidateUV[2*row+k],legacyUV[2*row+k])&&Object.is(candidateUV1[2*row+k],legacyUV1[2*row+k]),'All other BODY UV rows exact');
  }
  for(const row of uvRepairs.keys())need(Math.hypot(candidateUV[2*row]-legacyUV[2*row],candidateUV[2*row+1]-legacyUV[2*row+1])<=.00030,'Original fixed internal BODY UV bound');
  for(let i=0;i<parentUV.length;i++)if(!uvRepairs.has(Math.floor(i/2)))need(Object.is(parentUV[i],candidateUV[i])&&Object.is(parentUV1[i],candidateUV1[i]),'Original d454 UV rows exact outside explicit head repairs');
  const sourceBodyPosition=rawValues(parentRaw,1,'POSITION').values,candidateBodyPosition=rawValues(candidateRaw,1,'POSITION').values;
  let maximumOriginalDisplacement=0;
  for(let vertex=0;vertex<oldBody;vertex++){
   const shift=distance(sourceBodyPosition.slice(3*vertex,3*vertex+3),candidateBodyPosition.slice(3*vertex,3*vertex+3));
   need(shift<=.020,'Unchanged20mm source displacement bound for every original body vertex');maximumOriginalDisplacement=Math.max(maximumOriginalDisplacement,shift);
  }
  let originalEdgeRows=0,barycentricRows=0,maxNewDisplacement=0;
  const declared=new Set();for(const row of ancestry.added_vertices){
   need(row.vertex>=oldBody&&row.vertex<newBody&&!declared.has(row.vertex),'Unique appended vertex');declared.add(row.vertex);
   let ids,coefficients;
   if(Array.isArray(row.source_edge)){
    ids=row.source_edge;coefficients=[.5,.5];originalEdgeRows++;
    need(ids.length===2&&JSON.stringify(row.source_interpolation)==='[0.5,0.5]','Exact original-edge interpolation');
   }else{
    ids=row.source_vertex_ids;coefficients=row.source_barycentric_weights;barycentricRows++;
    need(Number.isInteger(row.source_parent_face)&&row.source_parent_face>=0&&row.source_parent_face<parentFacesForAncestry.length/3,'Actual original parent face');
    const parentFace=new Set(parentFacesForAncestry.slice(3*row.source_parent_face,3*row.source_parent_face+3));
    need(Array.isArray(ids)&&ids.length>=1&&ids.length<=3&&ids.every(i=>parentFace.has(i)),'Barycentric parents belong to that original face');
    need(row.source_interpolation==='original-face barycentric','Explicit new ancestry kind');
   }
   need(ids.length===coefficients.length&&new Set(ids).size===ids.length&&ids.every(i=>Number.isInteger(i)&&i>=0&&i<oldBody),'Unique original-source parents');
   need(coefficients.every(x=>Number.isFinite(x)&&x>0)&&coefficients.reduce((a,b)=>a+b,0)===1,'Positive exact source barycentric mass');
   const dense=new Float64Array(26),sourcePoint=[0,0,0],uvPoint=[0,0],uv1Point=[0,0];
   for(let index=0;index<ids.length;index++){
    const vertex=ids[index],coefficient=coefficients[index];
    for(let k=0;k<4;k++)dense[rawParent[1].j[4*vertex+k]]+=coefficient*rawParent[1].w[4*vertex+k];
    for(let k=0;k<3;k++)sourcePoint[k]+=coefficient*sourceBodyPosition[3*vertex+k];
    for(let k=0;k<2;k++){uvPoint[k]+=coefficient*parentUV[2*vertex+k];uv1Point[k]+=coefficient*parentUV1[2*vertex+k];}
   }
   const wanted=[...dense].map((w,j)=>[j,w]).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]||a[0]-b[0]);need(wanted.length<=4,'No dropped skin influences');const total=wanted.reduce((s,x)=>s+x[1],0);
   for(let k=0;k<4;k++){need(raw[1].j[4*row.vertex+k]===(wanted[k]?.[0]??0)&&Object.is(raw[1].w[4*row.vertex+k],Math.fround((wanted[k]?.[1]??0)/total)),'Exact original-source skin interpolation');}
   for(let k=0;k<2;k++)need(Object.is(candidateUV[2*row.vertex+k],Math.fround(uvPoint[k]))&&Object.is(candidateUV1[2*row.vertex+k],Math.fround(uv1Point[k])),'Exact original-source UV interpolation');
   const actualPoint=candidateBodyPosition.slice(3*row.vertex,3*row.vertex+3),shift=distance(sourcePoint,actualPoint);maxNewDisplacement=Math.max(maxNewDisplacement,shift);
   need(shift<=.020,'Unchanged20mm source displacement bound for every added vertex');
  }
  report.anatomy_lineage={original_body_vertices:oldBody,new_body_vertices:newBody,original_uv_rows_exact_except_two_declared_head_repairs:true,head_UV_repairs:[2410,2412],new_head_faces_claim_no_parent_face_ancestry:true,maximum_original_body_displacement_m:maximumOriginalDisplacement,original_edge_rows:originalEdgeRows,barycentric_rows:barycentricRows,maximum_new_vertex_displacement_from_ancestral_source_m:maxNewDisplacement};
  const oldIndices=rawValues(parentRaw,1,'indices').values,newIndices=rawValues(candidateRaw,1,'indices').values,legacyIndices=rawValues(legacyRaw,1,'indices').values,faceMap=ancestry.source_face_to_children;
  const replacedHeadSlots=new Set(socketRecipe.patches.flatMap(p=>p.removed_parent_925_faces));need(replacedHeadSlots.size===142,'Bound replacement slot count');
  need(faceMap.length===oldIndices.length/3,'Every source face mapped');const seenFaces=new Set();
  for(const children of faceMap)for(const face of children){need(Number.isInteger(face)&&face>=0&&face<legacyIndices.length/3&&!seenFaces.has(face),'Unique valid child face');seenFaces.add(face);}
  need(seenFaces.size===legacyIndices.length/3&&legacyIndices.length===newIndices.length,'Legacy925 foot provenance partitions legacy925 only, not new head faces');
  const patches={};for(const[label,row]of Object.entries(reference.contacts)){
   const childFaces=row.source_triangle_ids.flatMap(t=>faceMap[t]);
   need(childFaces.every(t=>!replacedHeadSlots.has(t)&&newIndices.slice(3*t,3*t+3).every((v,k)=>v===legacyIndices[3*t+k])),'Every physical contact face unchanged from legacy925 and outside new head strip');
   const legacyPosition=rawValues(legacyRaw,1,'POSITION').values,legacyJoints=rawValues(legacyRaw,1,'JOINTS_0').values,legacyWeights=rawValues(legacyRaw,1,'WEIGHTS_0').values;
   for(const vertex of new Set(childFaces.flatMap(t=>legacyIndices.slice(3*t,3*t+3)))){
    for(let k=0;k<3;k++)need(Object.is(candidateBodyPosition[3*vertex+k],legacyPosition[3*vertex+k]),'Physical foot source positions unchanged');
    for(let k=0;k<4;k++)need(raw[1].j[4*vertex+k]===legacyJoints[4*vertex+k]&&Object.is(raw[1].w[4*vertex+k],legacyWeights[4*vertex+k]),'Physical foot source skin unchanged');
    for(let k=0;k<2;k++)need(Object.is(candidateUV[2*vertex+k],legacyUV[2*vertex+k])&&Object.is(candidateUV1[2*vertex+k],legacyUV1[2*vertex+k]),'Physical foot UV unchanged');
   }
   const oldIds=new Set(row.source_triangle_ids.flatMap(t=>oldIndices.slice(3*t,3*t+3)));
   patches[label]=[...new Set(row.source_triangle_ids.flatMap(t=>faceMap[t]).flatMap(t=>newIndices.slice(3*t,3*t+3)))].sort((a,b)=>a-b);
   need([...oldIds].every(i=>patches[label].includes(i))&&patches[label].length>=oldIds.size,'Complete original and refined contact-child domain');
  }
  report.original_patch_counts=Object.fromEntries(Object.entries(reference.contacts).map(([name,row])=>[name,new Set(row.source_triangle_ids.flatMap(t=>oldIndices.slice(3*t,3*t+3))).size]));
  need(Object.entries({fore_l:59,fore_r:59,hind_l:13,hind_r:10}).every(([name,count])=>report.original_patch_counts[name]===count),'Original four complete parent patches');
  report.new_patch_counts=Object.fromEntries(Object.entries(patches).map(([k,v])=>[k,v.length]));
  report.rest_reference='New serialized canonical body, independently checked against actual neutral skin; old b479 surface acceptance is not inherited';
  const seams=new Map();for(let mi=0;mi<3;mi++)for(let i=0;i<rest[mi].length;i++){const key=rest[mi][i].map(v=>rint(v/1e-6)).join(',');if(!seams.has(key))seams.set(key,[]);seams.get(key).push([mi,i]);}const seamPairs=[...seams.values()].flatMap(v=>v.slice(1).map(p=>[v[0],p]));
  const base=cc.map((c,mi)=>Array.from({length:c.index.count/3},(_,t)=>{const ids=[0,1,2].map(k=>c.index.getX(t*3+k)),p=ids.map(i=>rest[mi][i]),n=cross3(sub(p[1],p[0]),sub(p[2],p[0]));return{ids,edges:[distance(p[1],p[0]),distance(p[2],p[1]),distance(p[0],p[2])],normal:n,area:norm3(n)};}));
  const timeline=frames.flatMap((f,i)=>i===64?[{time:f.time_s,key:i}]:[{time:f.time_s,key:i},{time:(f.time_s+frames[i+1].time_s)/2,key:null}]);need(timeline.length===129,'65keys+64midpoints');
  let firstNodes=null,firstPoints=null,neutralResidual=0;
  const p=new T.Vector3(),q=new T.Vector3(),e=new T.Vector3(),actualNormal=new T.Vector3(),expectedNormal=new T.Vector3(),cross=new T.Vector3();
  for(const sample of timeline){
   pose(candidate,0,sample.time);const actualWorld=nodes.map(n=>n.matrixWorld.clone()),metrics=chainErrors(nodes,pivots,controls.limbs),moved=[];let maxP=0,maxN=0,maxNative=0,keyMatrix=0,keyTranslation=0;
   report.physical.maximum_segment_length_error_m=Math.max(report.physical.maximum_segment_length_error_m,metrics.length);report.physical.maximum_parent_residual_m=Math.max(report.physical.maximum_parent_residual_m,metrics.parent);
   fail(metrics.length<=limit.segment_length_error_m,'Original segment length',{time:sample.time,error:metrics.length});fail(metrics.parent<=limit.segment_length_error_m,'Original parent linkage',{time:sample.time,error:metrics.parent});
   let expected=null;if(sample.key!==null){expected=expectedBones(frames[sample.key].global_canonical_matrices,cc[0].mesh.skeleton.boneInverses);for(let i=0;i<26;i++){const wanted=new T.Matrix4().set(...frames[sample.key].global_canonical_matrices[i].flat());keyMatrix=Math.max(keyMatrix,...wanted.elements.map((v,k)=>Math.abs(v-actualWorld[i].elements[k])));keyTranslation=Math.max(keyTranslation,new T.Vector3().setFromMatrixPosition(wanted).distanceTo(new T.Vector3().setFromMatrixPosition(actualWorld[i])));}}
   const surfaces=[];
   for(let mi=0;mi<3;mi++){
    const c=cc[mi],nf=normalContext(c),points=new Float64Array(c.position.count*3);let minY=Infinity;
    for(let i=0;i<c.position.count;i++){
     affineSkin(c,nf.b,i,p);points.set(p.toArray(),i*3);minY=Math.min(minY,p.y);need(p.toArray().every(Number.isFinite),'Finite actual shader position');
     c.mesh.applyBoneTransform(i,q.fromBufferAttribute(c.position,i)).applyMatrix4(c.mesh.matrixWorld);maxNative=Math.max(maxNative,p.distanceTo(q));
     shaderNormal(c,nf,i,actualNormal);
     if(expected){affineSkin(rc[mi],expected,i,e);maxP=Math.max(maxP,p.distanceTo(e),q.distanceTo(e));shaderNormal(rc[mi],{b:expected,prefix:nf.prefix},i,expectedNormal);const angle=Math.atan2(cross.crossVectors(actualNormal,expectedNormal).length(),actualNormal.dot(expectedNormal))*180/Math.PI;maxN=Math.max(maxN,angle);report.positions.evaluations++;report.normals.evaluations++;}
    }
    moved.push(points);let edgeMin=1,edgeMax=1,areaMin=1,areaMax=1,negative=0,worstEdge=null;
    for(let ti=0;ti<base[mi].length;ti++){const b=base[mi][ti],v=b.ids.map(i=>xyz(points,i));for(let k=0;k<3;k++)if(b.edges[k]>1e-8){const ratio=distance(v[(k+1)%3],v[k])/b.edges[k];if(ratio<edgeMin){edgeMin=ratio;worstEdge={triangle:ti,vertices:b.ids,ratio};}edgeMax=Math.max(edgeMax,ratio);}const normal=cross3(sub(v[1],v[0]),sub(v[2],v[0]));if(b.area>1e-12){const ratio=norm3(normal)/b.area;areaMin=Math.min(areaMin,ratio);areaMax=Math.max(areaMax,ratio);negative+=+(dot3(b.normal,normal)<0);}}
    surfaces.push({mesh:mi,edgeMin,edgeMax,areaMin,areaMax,negative,minY,worstEdge});
    fail(edgeMin>=limit.minimum_triangle_edge_ratio&&edgeMax<=limit.maximum_triangle_edge_ratio,'Original edge limits',{time:sample.time,key:sample.key,mesh:mi,edgeMin,edgeMax,worstEdge});fail(areaMin>=limit.minimum_triangle_area_ratio&&areaMax<=limit.maximum_triangle_area_ratio,'Original area limits',{time:sample.time,mesh:mi,areaMin,areaMax});fail(negative===limit.allowed_rest_relative_triangle_normal_dot_negative,'Original normal sign',{time:sample.time,mesh:mi,negative});fail(minY>=limit.minimum_all_surface_y_m,'Original ground limit',{time:sample.time,mesh:mi,minY});
   }
   const contact=maxContact(moved,rest,patches);let seam=0;for(const[[ma,va],[mb,vb]]of seamPairs)seam=Math.max(seam,distance(xyz(moved[ma],va),xyz(moved[mb],vb)));
   report.physical.maximum_contact_error_m=Math.max(report.physical.maximum_contact_error_m,contact.gap);report.physical.maximum_seam_gap_m=Math.max(report.physical.maximum_seam_gap_m,seam);
   fail(contact.gap<=limit.stance_patch_drift_m,'Original whole-hoof contact limit',{time:sample.time,key:sample.key,...contact});fail(seam<=limit.minimum_seam_gap_tolerance_m,'Original seam limit',{time:sample.time,seam});
   if(sample.key===0){firstNodes=actualWorld.map(m=>m.clone());firstPoints=moved.map(a=>a.slice());for(let mi=0;mi<3;mi++)for(let i=0;i<rest[mi].length;i++)neutralResidual=Math.max(neutralResidual,distance(xyz(moved[mi],i),rest[mi][i]));fail(neutralResidual<=1e-6,'Original neutral position limit',{neutralResidual});}
   if(sample.key!==null){report.key_count++;report.positions.maximum_delta_m=Math.max(report.positions.maximum_delta_m,maxP);report.normals.maximum_angle_degrees=Math.max(report.normals.maximum_angle_degrees,maxN);report.joint_world.maximum_translation_error_m=Math.max(report.joint_world.maximum_translation_error_m,keyTranslation);report.joint_world.maximum_matrix_component_error=Math.max(report.joint_world.maximum_matrix_component_error,keyMatrix);fail(maxP<=1e-5&&maxN<=.01&&keyTranslation<=1e-5&&keyMatrix<=1e-5,'Actual loaded key equivalence',{time:sample.time,maxP,maxN,keyTranslation,keyMatrix});}else report.midpoint_count++;
   report.poses.push({time:sample.time,key:sample.key,contact,seam,surfaces,metrics,maxP,maxN,maxNative,keyMatrix,keyTranslation,world_matrices:actualWorld.map(m=>m.elements.slice())});
   console.log('STANDING_READBACK_PROGRESS '+JSON.stringify({time:sample.time,key:sample.key,contact:contact.gap,failures:report.failures.length}));
  }
  let loopP=0,loopR=0,loopSkin=0;for(let i=0;i<26;i++){const last=nodes[i].matrixWorld.elements,first=firstNodes[i].elements;for(const k of[12,13,14])loopP=Math.max(loopP,Math.abs(last[k]-first[k]));for(const k of[0,1,2,4,5,6,8,9,10])loopR=Math.max(loopR,Math.abs(last[k]-first[k]));}for(let mi=0;mi<3;mi++){const c=cc[mi],nf=normalContext(c);for(let i=0;i<c.position.count;i++)loopSkin=Math.max(loopSkin,affineSkin(c,nf.b,i,p).distanceTo(new T.Vector3().fromArray(firstPoints[mi],i*3)));}fail(loopP<=limit.loop_position_m&&loopR<=limit.loop_rotation_matrix_abs&&loopSkin<=limit.stance_patch_drift_m,'Original loop limits',{loopP,loopR,loopSkin});
  // Actual temporary wrong-local and hoof corruptions; no second model/grid.
  pose(candidate,0,3);const cnode=nodes[controls.limbs.fore_l.joints[2]],savedQ=cnode.quaternion.clone(),worldQ=cnode.getWorldQuaternion(new T.Quaternion());cnode.quaternion.copy(worldQ);candidate.scene.updateMatrixWorld(true);candidate.meshes.forEach(m=>m.skeleton.update());
  const sampleContact=()=>{const moved=cc.map(c=>{const a=new Float64Array(c.position.count*3),f=normalContext(c);for(let i=0;i<c.position.count;i++)a.set(affineSkin(c,f.b,i,p).toArray(),i*3);return a;});return maxContact(moved,rest,patches).gap;};const wrongLocal=sampleContact();cnode.quaternion.copy(savedQ);candidate.scene.updateMatrixWorld(true);candidate.meshes.forEach(m=>m.skeleton.update());
  const hoof=nodes[controls.limbs.fore_l.joints[4]],savedP=hoof.position.clone();hoof.position.y+=.003;candidate.scene.updateMatrixWorld(true);candidate.meshes.forEach(m=>m.skeleton.update());const hoofCorruption=sampleContact(),badLength=chainErrors(nodes,pivots,controls.limbs).length;hoof.position.copy(savedP);candidate.scene.updateMatrixWorld(true);candidate.meshes.forEach(m=>m.skeleton.update());
  report.negative_controls={wrong_world_as_local_contact_error_m:wrongLocal,three_mm_hoof_contact_error_m:hoofCorruption,three_mm_segment_error_m:badLength};fail(wrongLocal>limit.stance_patch_drift_m&&hoofCorruption>=limit.negative_control_min_detected_m&&badLength>=limit.negative_control_min_detected_m,'Meaningful actual corruption controls',report.negative_controls);
  report.loop={loopP,loopR,loopSkin};report.neutral_residual_m=neutralResidual;report.original_physical_limits=limit;report.WebGL_contexts_created=window.__proofGLContexts??0;need(report.WebGL_contexts_created===0,'No WebGL context allowed');
  report.status=report.key_count===65&&report.midpoint_count===64&&report.failures.length===0?'LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY':'LOADED_STANDING129_FAIL_NO_RETRY';
 }catch(error){report.status='LOADED_STANDING129_FAIL_NO_RETRY';report.error={name:error.name,message:error.message,stack:error.stack};}
 finally{for(const model of[source,candidate])if(model){model.mixer.stopAllAction();model.mixer.uncacheRoot(model.scene);for(const c of model.meshes??[])c.skeleton.dispose();}report.elapsed_ms=performance.now()-started;report.scope='Actual standard-loader/Mixer imported13track standing clip at65keys+64midpoints. No renderer/GPUfloat-arithmetic/continuous collision/photographic/app/independentheadtail/walking acceptance.';}
 return report;
};
window.ready=true;

// The entire9176B original metric block above, including its historical scope
// label, remains byte-exact. Transparently report the new admitted second clip;
// no Three/native renderer method or measured numerical value is changed here.
const compareOriginalPhysicalMetric=window.compare;
window.compare=async()=>{const report=await compareOriginalPhysicalMetric();report.metric_loop_historical_scope=report.scope;report.scope='Actual native GLTFLoader/SkeletonUtils/AnimationMixer second exported17track natural planted clip at65keys+64midpoints; unchanged original physical limits/metric loop. No world/GPU/continuous collision/photographic/walk/rider acceptance.';report.selected_exported_clip='sevket_reconstructed_natural_planted_idle_v1';report.old_certificate_transferred=false;return report;};

// Distinct external capture only. The original physical metric/limit loop above
// is byte-identical. No renderer, no GPU/continuous-motion or interface verdict.
let socketState=null;
const socketInventory=model=>{const rows=[],ids=new Map();model.scene.traverse(o=>{ids.set(o,rows.length);rows.push(o);});return rows.map(o=>({o,parent:o.parent===null?-1:ids.get(o.parent)??-1,name:o.name,type:o.type}));};
const disposeSocket=model=>{if(model){model.mixer.stopAllAction();model.mixer.uncacheRoot(model.scene);for(const mesh of model.meshes)mesh.skeleton.dispose();}};
window.beginSocketCapture=async()=>{
 need(!socketState,'Fresh socket capture required');
 need(window.cpuReport?.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&window.cpuReport.key_count===65&&window.cpuReport.midpoint_count===64&&window.cpuReport.failures.length===0,'Original native physical129 must actually pass first');
 const config=await(await fetch('/CONFIG.json')).json();let candidate,parent;
 try{
  const[actual,original]=await Promise.all([pinned(config.inputs.candidate),pinned(config.inputs.legacy_parent)]);
  [candidate,parent]=await Promise.all([load(config.inputs.candidate.url,actual),load(config.inputs.legacy_parent.url,original)]);
  need(candidate.animations.length===2&&candidate.animations[1].name==='sevket_reconstructed_natural_planted_idle_v1'&&candidate.animations[1].tracks.length===17&&parent.animations.length===1,'Explicit new17 clip and unchanged925 reference inventory');candidate.naturalIdleSelected=true;
  const c=socketInventory(candidate),p=socketInventory(parent);
  need(c.length===p.length&&c.every((row,i)=>row.name===p[i].name&&row.type===p[i].type&&row.parent===p[i].parent),'Exact native925 candidate node correspondence');
  const bodyC=candidate.meshes.find(m=>m.userData.parityKey==='1:0'),bodyP=parent.meshes.find(m=>m.userData.parityKey==='1:0'),eyeC=candidate.meshes.find(m=>m.userData.parityKey==='2:0'),eyeP=parent.meshes.find(m=>m.userData.parityKey==='2:0');
  need([bodyC,bodyP].every(m=>m?.geometry.attributes.position.count===5595)&&[eyeC,eyeP].every(m=>m?.geometry.attributes.position.count===3968),'Actual BODY and immutable Eye row inventory');
  socketState={candidate,parent,c,p,bodyC,bodyP,eyeC,eyeP,next:0};return{state:'SOCKET_CAPTURE_READY_ONLY',frames_expected:129};
 }catch(error){disposeSocket(candidate);disposeSocket(parent);throw error;}
};
window.captureSocketFrame=index=>{
 const st=socketState;need(st&&index===st.next&&index>=0&&index<129,'Exactly ordered full native129 capture');
 const time=index*3/32;pose(st.candidate,0,time);
 // The hidden925 clone has no renderer. Copy actual node/root states and force
 // every world/skeleton update explicitly. Tiny neck influence is never erased.
 st.parent.mixer.stopAllAction();
 for(let i=0;i<st.c.length;i++){
  const a=st.c[i].o,b=st.p[i].o;need(a.matrixAutoUpdate&&b.matrixAutoUpdate,'Supported native auto-updated PRS nodes');
  b.position.copy(a.position);b.quaternion.copy(a.quaternion);b.scale.copy(a.scale);
 }
 st.parent.scene.updateMatrixWorld(true);for(const mesh of st.parent.meshes)mesh.skeleton.update();
 const boneStates=st.c.every((row,i)=>{const a=row.o,b=st.p[i].o;return a.position.equals(b.position)&&a.quaternion.equals(b.quaternion)&&a.scale.equals(b.scale)&&a.matrixWorld.elements.every((v,k)=>Object.is(v,b.matrixWorld.elements[k]));});
 need(boneStates,'Copied actual925 root/bone transforms differ');
 const meshBases=[st.bodyC,st.bodyP,st.eyeC,st.eyeP].every(m=>identity(m.matrixWorld)&&identity(m.bindMatrix)&&identity(m.bindMatrixInverse));need(meshBases,'Native canonical mesh/bind coordinate basis changed');
 const read=mesh=>{const p=new T.Vector3(),rows=[];for(let i=0;i<mesh.geometry.attributes.position.count;i++){mesh.getVertexPosition(i,p);need(Number.isFinite(p.x)&&Number.isFinite(p.y)&&Number.isFinite(p.z),'Finite actual getVertexPosition result');rows.push(p.x,p.y,p.z);}return rows;};
 const nodeStates=rows=>rows.map(row=>[...row.o.position.toArray(),...row.o.quaternion.toArray(),...row.o.scale.toArray(),...row.o.matrixWorld.elements]);
 const skeletonMatrices=model=>model.meshes.map(mesh=>Array.from(mesh.skeleton.boneMatrices));
 const actualBases=[st.bodyC,st.bodyP,st.eyeC,st.eyeP].map(mesh=>[mesh.matrixWorld.elements.slice(),mesh.bindMatrix.elements.slice(),mesh.bindMatrixInverse.elements.slice()]);
 const record={index,time_s:time,key:index%2===0?index/2:null,bone_states_identical:boneStates,skeletons_updated:true,mesh_bind_bases_identity:meshBases,candidate_node_states:nodeStates(st.c),parent_node_states:nodeStates(st.p),candidate_bone_world_matrices:st.candidate.meshes[0].skeleton.bones.map(b=>b.matrixWorld.elements.slice()),parent_bone_world_matrices:st.parent.meshes[0].skeleton.bones.map(b=>b.matrixWorld.elements.slice()),candidate_skeleton_matrices:skeletonMatrices(st.candidate),parent_skeleton_matrices:skeletonMatrices(st.parent),actual_mesh_bind_bases:actualBases,candidate_body:read(st.bodyC),parent_body:read(st.bodyP),candidate_eye:read(st.eyeC),parent_eye:read(st.eyeP),coordinate_precision:'native JS Number, transferred and stored Float64LE; no added Float32 snapshot'};
 st.next++;return record;
};
window.endSocketCapture=()=>{
 const st=socketState;need(st&&st.next===129,'Native socket capture incomplete');
 disposeSocket(st.candidate);disposeSocket(st.parent);socketState=null;
 need((window.__proofGLContexts??0)===0,'No WebGL context allowed');return{frames:129,models_disposed:true,WebGL_contexts_created:0};
};
