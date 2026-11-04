// First-class binding-v2 source: old8ea/new binding13track parity, new17 physical, paired925 capture.
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
// New explicit binding admission; none of the original physical predicates change.
function bindingAdmission(parent,child,overlay,recipe,role,sourceSHA,recipeSHA){
 need(parent.bin.length===child.bin.length,'Exact parent BIN length');
 const clean=structuredClone(child.doc),notice=clean.asset.extras.chicago4d_natural_planted_binding_v2;
 need(JSON.stringify(notice)===JSON.stringify({source_parent_sha256:sourceSHA,recipe_sha256:recipeSHA,binding_version:2,role,qualification:'UNRUN',old_certificate_transferred:false}),'Exact new binding notice');
 delete clean.asset.extras.chicago4d_natural_planted_binding_v2;
 need(JSON.stringify(clean)===JSON.stringify(parent.doc),'All unlisted parent JSON/geometry/rig/oldclips exact');
 const allowed=new Set();
 for(let mi=0;mi<3;mi++){
  const label=mi===0?'HAIR':'BODY',domain=mi<2?new Set([...recipe.allowed_row_masks[label+'_head_neck'],...recipe.allowed_row_masks[mi===0?'HAIR_original_tail_component':'BODY_tail_dock']]):new Set();
  const rows=new Map((overlay[String(mi)]??[]).map(r=>[r.row,r]));need(rows.size===(overlay[String(mi)]??[]).length,'Unique reviewed tuple rows');
  const pj=rawAttribute(parent,mi,'JOINTS_0'),pw=rawAttribute(parent,mi,'WEIGHTS_0'),cj=rawAttribute(child,mi,'JOINTS_0'),cw=rawAttribute(child,mi,'WEIGHTS_0');
  for(let row=0;row<pj.length/4;row++){
   const changed=rows.get(row);if(changed)need(domain.has(row),'Changed skin tuple inside fixed anatomical domain');
   for(let k=0;k<4;k++)need(cj[row*4+k]===(changed?changed.joints[k]:pj[row*4+k])&&Object.is(cw[row*4+k],changed?changed.weights[k]:pw[row*4+k]),'Actual native resource exact reviewed overlay or protected outside tuple');
   if(changed)for(const name of['JOINTS_0','WEIGHTS_0']){const a=parent.doc.accessors[parent.doc.meshes[mi].primitives[0].attributes[name]],v=parent.doc.bufferViews[a.bufferView],size=name==='JOINTS_0'?8:16;need(!v.byteStride,'Exact dense skin row streams');const start=(v.byteOffset??0)+(a.byteOffset??0)+row*size;for(let k=0;k<size;k++)allowed.add(start+k);}
  }
 }
 let count=0;for(let i=0;i<parent.bin.length;i++)if(parent.bin[i]!==child.bin[i]){need(allowed.has(i),'Every changed BIN byte is reviewed skin-row byte');count++;}
 need(count===61070,'Exact separately reviewed61070 changed BIN bytes');
}

window.runPhysical=async mode=>{
 const started=performance.now(),config=await(await fetch('/CONFIG.json')).json();let source,candidate;
 const report={status:'BINDING_V2_NATIVE_INCOMPLETE',binding_mode:mode,key_count:0,midpoint_count:0,poses:[],normalization:[],failures:[],positions:{tolerance_m:1e-5,maximum_delta_m:0,evaluations:0},normals:{tolerance_degrees:.01,maximum_angle_degrees:0,evaluations:0},joint_world:{maximum_translation_error_m:0,maximum_matrix_component_error:0},physical:{maximum_segment_length_error_m:0,maximum_parent_residual_m:0,maximum_seam_gap_m:0,maximum_contact_error_m:0},WebGL_contexts_created:0,renderers_created:0,walking_enabled:false,photographic_acceptance:false};
 const fail=(condition,label,witness)=>{if(!condition&&report.failures.length<100)report.failures.push({label,witness});};
 try{
  need(mode==='old13'||mode==='new17','Explicit original13 or new17 actual exported clip');
  need(T.REVISION==='185'&&T.ShaderChunk.skinnormal_vertex.includes('skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;')&&T.ShaderChunk.defaultnormal_vertex.includes('transformedNormal = normalMatrix * transformedNormal;'),'Exact native shader normal algebra');
  const resources=Object.fromEntries(await Promise.all(Object.entries(config.inputs).map(async([name,pin])=>[name,await pinned(pin)])));
  const recipe=json(resources.binding_recipe),overlay=json(resources.tuple_overlay),reference=json(resources.cpu_reference),derivation=json(resources.anatomy_receipt),controls=json(resources.controls26),limit=json(resources.limits);
  const frames=json(mode==='old13'?resources.accepted_matrices:resources.expected_matrices).frames;
  need(frames.length===65&&frames.every((f,i)=>f.time_s===i*12/64),'Actual unchanged65 key schedule');
  const oldRaw=glb(resources.motion_source),candidateRaw=glb(resources.candidate),legacyRaw=glb(resources.legacy_parent),pairedRaw=glb(resources.paired_reference),parentRaw=glb(resources.selected_parent);
  need(config.inputs.motion_source.sha256==='8ea7748ffba6c5fe17cde91042c6d8b26ed9a0ab77de69cadd4f4fb12e9c09fa'&&config.inputs.legacy_parent.sha256==='925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48','Exact immutable motion and925 sources');
  const staticProof=json(resources.static_socket_receipt);need(staticProof.status==='BINDING_V2_CURRENT_SOURCE_STATIC_ONLY_PASS'&&staticProof.candidate_sha256===config.inputs.candidate.sha256&&staticProof.paired925_sha256===config.inputs.paired_reference.sha256&&JSON.stringify(staticProof.code_pins)===JSON.stringify(config.code_pins),'Actual same-code new binding static receipt');
  bindingAdmission(oldRaw,candidateRaw,overlay,recipe,'natural-idle-candidate',config.inputs.motion_source.sha256,config.inputs.binding_recipe.sha256);
  bindingAdmission(legacyRaw,pairedRaw,overlay,recipe,'paired-original925-geometry-reference',config.inputs.legacy_parent.sha256,config.inputs.binding_recipe.sha256);
  for(let mi=0;mi<3;mi++)for(const name of['JOINTS_0','WEIGHTS_0'])need(bytesEqual(rawAttribute(candidateRaw,mi,name),rawAttribute(pairedRaw,mi,name)),'Entire actual candidate and paired925 skin streams equal');
  [source,candidate]=await Promise.all([load(config.inputs.motion_source.url,resources.motion_source),load(config.inputs.candidate.url,resources.candidate)]);
  for(const model of[source,candidate])need(model.animations.length===2&&model.animations[0].name==='sevket_reconstructed_planted_posture_v1'&&model.animations[0].tracks.length===13&&model.animations[1].name==='sevket_reconstructed_natural_planted_idle_v1'&&model.animations[1].tracks.length===17,'Genuine retained13 and new17 imported clips');
  need(JSON.stringify(await maps(source))===JSON.stringify(await maps(candidate)),'Actual decoded old and newly bound image/material equality');
  candidate.naturalIdleSelected=mode==='new17';
  const sc=source.meshes.map(cache),cc=candidate.meshes.map(cache),raw=cc.map((_,mi)=>({j:rawAttribute(candidateRaw,mi,'JOINTS_0'),w:rawAttribute(candidateRaw,mi,'WEIGHTS_0')})),rc=cc.map((c,i)=>({...c,j:raw[i].j,w:raw[i].w}));
  const nodes=cc[0].mesh.skeleton.bones,pivots=frames[0].global_canonical_matrices.map(m=>[m[0][3],m[1][3],m[2][3]]);
  const rest=cc.map((c,mi)=>{const a=rawValues(candidateRaw,mi,'POSITION');need(a.rows===c.position.count&&a.count===3,'Exact rest rows');return Array.from({length:a.rows},(_,i)=>a.values.slice(3*i,3*i+3));});
  for(let mi=0;mi<3;mi++){
   need(identity(cc[mi].mesh.matrixWorld)&&identity(cc[mi].mesh.bindMatrix)&&identity(cc[mi].mesh.bindMatrixInverse),'Canonical actual mesh/bind bases');
   for(let i=0;i<cc[mi].position.count;i++){
    const sum=raw[mi].w.slice(i*4,i*4+4).reduce((a,b)=>a+Math.abs(b),0);need(sum>0,'Positive raw skin mass');
    for(let k=0;k<4;k++)need(cc[mi].j[i*4+k]===raw[mi].j[i*4+k]&&Object.is(cc[mi].w[i*4+k],Math.fround(raw[mi].w[i*4+k]*(1/sum))),'Actual loader normalization independently checked');
   }
   for(let bone=0;bone<26;bone++)need(sc[mi].mesh.skeleton.boneInverses[bone].elements.every((v,k)=>v===cc[mi].mesh.skeleton.boneInverses[bone].elements[k]),'Actual source IBM equality');
  }
  const oldIndices=rawValues(parentRaw,1,'indices').values,newIndices=rawValues(candidateRaw,1,'indices').values,legacyIndices=rawValues(legacyRaw,1,'indices').values,faceMap=derivation.source_boundary.hoof_refinement.source_face_to_children,patches={};
  const hoofSemantics=Object.fromEntries(['POSITION','NORMAL','JOINTS_0','WEIGHTS_0'].map(name=>[name,[rawValues(candidateRaw,1,name),rawValues(oldRaw,1,name)]]));
  for(const[label,row]of Object.entries(reference.contacts)){
   const faces=row.source_triangle_ids.flatMap(t=>faceMap[t]);
   patches[label]=[...new Set(faces.flatMap(t=>newIndices.slice(3*t,3*t+3)))].sort((a,b)=>a-b);
   for(const face of faces)need(newIndices.slice(3*face,3*face+3).every((v,k)=>v===legacyIndices[3*face+k]),'Complete source hoof face topology exact');
   for(const vertex of patches[label])for(const name of['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']){const[a,b]=hoofSemantics[name];for(let k=0;k<a.count;k++)need(Object.is(a.values[vertex*a.count+k],b.values[vertex*b.count+k]),'Whole source-derived hoof semantic rows exact');}
  }
  report.new_patch_counts=Object.fromEntries(Object.entries(patches).map(([k,v])=>[k,v.length]));need(JSON.stringify(report.new_patch_counts)===JSON.stringify({fore_l:179,fore_r:179,hind_l:30,hind_r:24}),'Complete original four refined hoof patches');
  const seams=new Map();for(let mi=0;mi<3;mi++)for(let i=0;i<rest[mi].length;i++){const key=rest[mi][i].map(v=>rint(v/1e-6)).join(',');if(!seams.has(key))seams.set(key,[]);seams.get(key).push([mi,i]);}const seamPairs=[...seams.values()].flatMap(v=>v.slice(1).map(p=>[v[0],p]));
  if(mode==='old13'){
   const parity={samples:0,vertices_per_sample:cc.reduce((sum,c)=>sum+c.position.count,0),maximum_position_m:0,maximum_shader_normal_degrees:0,maximum_bone_world_component:0,tolerance_m:1e-5,tolerance_degrees:.01};
   const pa=new T.Vector3(),pb=new T.Vector3(),na=new T.Vector3(),nb=new T.Vector3(),cross=new T.Vector3();
   for(let i=0;i<129;i++){
    pose(source,0,i*3/32);pose(candidate,0,i*3/32);
    for(let mi=0;mi<3;mi++){
     const fa=normalContext(sc[mi]),fb=normalContext(cc[mi]);
     for(let vertex=0;vertex<cc[mi].position.count;vertex++){
      sc[mi].mesh.getVertexPosition(vertex,pa);cc[mi].mesh.getVertexPosition(vertex,pb);parity.maximum_position_m=Math.max(parity.maximum_position_m,pa.distanceTo(pb));
      shaderNormal(sc[mi],fa,vertex,na);shaderNormal(cc[mi],fb,vertex,nb);parity.maximum_shader_normal_degrees=Math.max(parity.maximum_shader_normal_degrees,Math.atan2(cross.crossVectors(na,nb).length(),na.dot(nb))*180/Math.PI);
     }
     for(let bone=0;bone<26;bone++)for(let k=0;k<16;k++)parity.maximum_bone_world_component=Math.max(parity.maximum_bone_world_component,Math.abs(sc[mi].mesh.skeleton.bones[bone].matrixWorld.elements[k]-cc[mi].mesh.skeleton.bones[bone].matrixWorld.elements[k]));
    }
    parity.samples++;
   }
   report.old13_parity=parity;need(parity.samples===129&&parity.maximum_position_m<=1e-5&&parity.maximum_shader_normal_degrees<=.01&&parity.maximum_bone_world_component===0,'Actual all-vertex original13 native pose/shader-normal parity');
  }
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

// Preserve the original loop byte-for-byte, including its historical scope label.
window.compare=async()=>{
 const old=window.old13Report=await window.runPhysical('old13');
 need(old.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&old.old13_parity?.samples===129&&old.failures.length===0,'Original13 native all129 parity AND physical limits must actually pass first');
 const report=window.cpuReport=await window.runPhysical('new17');
 report.metric_loop_historical_scope=report.scope;report.scope='Actual new binding-v2 native second17track physical129 after genuine original13 all129 full-vertex/shader-normal parity and original physical limits. No world/continuous/photo/rider acceptance.';report.selected_exported_clip_index=1;report.selected_exported_track_count=17;report.selected_exported_clip='sevket_reconstructed_natural_planted_idle_v1';report.old_certificate_transferred=false;report.old13_parity=old.old13_parity;
 return report;
};
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
  const[actual,original]=await Promise.all([pinned(config.inputs.candidate),pinned(config.inputs.paired_reference)]);
  [candidate,parent]=await Promise.all([load(config.inputs.candidate.url,actual),load(config.inputs.paired_reference.url,original)]);
  need(candidate.animations.length===2&&candidate.animations[1].name==='sevket_reconstructed_natural_planted_idle_v1'&&candidate.animations[1].tracks.length===17&&parent.animations.length===1,'Explicit new17 clip and separately-versioned paired925 reference inventory');candidate.naturalIdleSelected=true;
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
 // The hidden paired925 clone has no renderer. Copy actual node/root states and force
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
