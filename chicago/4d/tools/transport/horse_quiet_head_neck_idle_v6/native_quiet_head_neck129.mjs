// First-class quiet V6: old13 parity, master/runtime quiet15 physical, actual independent pair925 Mixer capture.
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
function pose(model,clip,time){model.mixer.stopAllAction();for(const[o,p,q,s]of model.bind){o.position.copy(p);o.quaternion.copy(q);o.scale.copy(s);}if(clip!==null){const selected=model.selectedClipName?model.animations.find(c=>c.name===model.selectedClipName):model.animations[clip];need(selected,'Exact selected clip must exist, no fallback');const action=model.mixer.clipAction(selected);action.reset();action.setLoop(T.LoopOnce,1);action.clampWhenFinished=true;action.play();model.mixer.setTime(time);}model.scene.updateMatrixWorld(true);for(const m of model.meshes)m.skeleton.update();}
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

function rootBindingAdmission(parent,child,overlay,recipe,role,sourceSHA,recipeSHA){
 need(parent.bin.length===child.bin.length,'Exact v2 parent BIN length');
 const clean=structuredClone(child.doc),notice=clean.asset.extras.chicago4d_natural_planted_binding_v3;
 need(JSON.stringify(notice)===JSON.stringify({source_parent_sha256:sourceSHA,recipe_sha256:recipeSHA,binding_version:3,role,qualification:'UNRUN',old_certificate_transferred:false}),'Exact root-aware v3 notice');
 delete clean.asset.extras.chicago4d_natural_planted_binding_v3;
 need(JSON.stringify(clean)===JSON.stringify(parent.doc),'All unlisted v2 JSON/oldclips/rig/geometry exact');
 const rows=new Map(overlay['0'].map(r=>[r.row,r])),domain=new Set(recipe.head_rows),allowed=new Set();need(rows.size===1119&&domain.size===2306,'Exact reviewed mane row inventories');
 for(const name of['JOINTS_0','WEIGHTS_0']){
  const a=rawAttribute(parent,0,name),b=rawAttribute(child,0,name),key=name==='JOINTS_0'?'joints':'weights';
  for(let row=0;row<a.length/4;row++){const change=rows.get(row);if(change)need(domain.has(row),'Changed mane row inside original2306domain');for(let k=0;k<4;k++)need(Object.is(b[row*4+k],change?change[key][k]:a[row*4+k]),'Exact root tuple overlay or preserved969tail');}
  const ac=parent.doc.accessors[parent.doc.meshes[0].primitives[0].attributes[name]],v=parent.doc.bufferViews[ac.bufferView],size=name==='JOINTS_0'?8:16;need(!v.byteStride,'Dense skin rows');
  for(const row of rows.keys()){const offset=(v.byteOffset??0)+(ac.byteOffset??0)+row*size;for(let k=0;k<size;k++)allowed.add(offset+k);}
 }
 let count=0;for(let i=0;i<parent.bin.length;i++)if(parent.bin[i]!==child.bin[i]){need(allowed.has(i),'Every BODY/EYE/tail/unlisted BIN byte exactv2');count++;}need(count===8874,'Exact reviewed8874mane skin bytes');
}


const QUIET='sevket_reconstructed_quiet_head_neck_idle_v1';
function accessor(g,index){
 const a=g.doc.accessors[index],v=g.doc.bufferViews[a.bufferView],width={SCALAR:1,VEC3:3,VEC4:4}[a.type];need(a.componentType===5126&&!a.sparse&&!a.normalized&&width&&!v.byteStride,'Literal dense float track accessor');
 return{width,values:Array.from(new Float32Array(g.bin.buffer,g.bin.byteOffset+(v.byteOffset??0)+(a.byteOffset??0),a.count*width))};
}
function scalarSlerp(a,b,u){
 let dot=a.reduce((sum,x,i)=>sum+x*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot;}
 let q;if(dot>0.9995)q=a.map((x,i)=>x+(b[i]-x)*u);else{const theta=Math.acos(Math.max(-1,Math.min(1,dot))),den=Math.sin(theta);q=a.map((x,i)=>(Math.sin((1-u)*theta)*x+Math.sin(u*theta)*b[i])/den);}
 const n=Math.hypot(...q);need(n>0,'Literal quaternion mass');return q.map(x=>x/n);
}
function literalWorld(g,time){
 // Independently read the literal source17 curve inventory, retain original13
 // plus targetNECK2/HEAD3, never consume/zero a sampled old17 matrix dump.
 const natural=g.doc.animations[1],channels=natural.channels.filter(c=>c.target.node!==4&&c.target.node!==5);
 need(channels.length===15&&channels.slice(-2).map(c=>c.target.node).join(',')==='2,3','Exact literal quiet source targets');
 const prs=g.doc.nodes.map(n=>({p:(n.translation??[0,0,0]).slice(),q:(n.rotation??[0,0,0,1]).slice(),s:(n.scale??[1,1,1]).slice()}));
 for(const c of channels){const sampler=natural.samplers[c.sampler],times=accessor(g,sampler.input),out=accessor(g,sampler.output);need(sampler.interpolation==='LINEAR'&&times.width===1&&times.values.length===65,'Literal original65-key LINEAR track');let i=0;while(i<63&&times.values[i+1]<time)i++;const u=Math.max(0,Math.min(1,(time-times.values[i])/(times.values[i+1]-times.values[i]))),a=out.values.slice(i*out.width,(i+1)*out.width),b=out.values.slice((i+1)*out.width,(i+2)*out.width);const n=prs[c.target.node];if(c.target.path==='rotation')n.q=scalarSlerp(a,b,u);else{need(c.target.path==='translation','Literal permitted native source path');n.p=a.map((x,k)=>x+(b[k]-x)*u);}}
 const local=prs.map(n=>new T.Matrix4().compose(new T.Vector3(...n.p),new T.Quaternion(...n.q),new T.Vector3(...n.s))),world=local.map(()=>null);
 const visit=(i,parent)=>{need(!g.doc.nodes[i].matrix,'Explicit source PRS hierarchy');world[i]=parent.clone().multiply(local[i]);for(const j of g.doc.nodes[i].children??[])visit(j,world[i]);};
 for(const i of g.doc.scenes[g.doc.scene??0].nodes)visit(i,new T.Matrix4());return g.doc.skins[0].joints.map(i=>world[i]);
}
function literalFrames(g){return Array.from({length:65},(_,i)=>({time_s:i*12/64,global_canonical_matrices:literalWorld(g,i*12/64).map(m=>Array.from({length:4},(_,r)=>Array.from({length:4},(_,c)=>m.elements[c*4+r])))}));}
async function runCrossChecks(){
 const config=await(await fetch('/CONFIG.json')).json(),resources=Object.fromEntries(await Promise.all(Object.entries(config.inputs).map(async([n,p])=>[n,await pinned(p)]))),v2=glb(resources.v2_candidate),raw=glb(resources.runtime_candidate),models=await Promise.all([load('',resources.runtime_candidate),load('',resources.candidate),load('',resources.v2_candidate)]),[quiet,old,natural]=models;
 quiet.selectedClipName=QUIET;old.selectedClipName='sevket_reconstructed_planted_posture_v1';natural.selectedClipName='sevket_reconstructed_natural_planted_idle_v1';
 const pos=rawValues(raw,0,'POSITION').values,tail=Array.from({length:pos.length/3},(_,i)=>i).filter(i=>!(pos[i*3+1]>1.04&&pos[i*3+2]>.28));need(tail.length===969,'All original969 tail rows selected');
 const result={samples:0,actual_quiet_tail_vertices:969,maximum_tail_position_delta_m:0,maximum_tail_relative_bone_component:0,maximum_head_neck_vs_source17_component:0,maximum_all129_literal_reference_component:0,maximum_actual_head_motion_component:0,maximum_actual_neck_motion_component:0,poses:[],source_reference:'Literal original source15 channels/hierarchy/rests, scalar independent slerp; no old17 matrix replacement'};
 let first=null;const a=new T.Vector3(),b=new T.Vector3();
 try{for(let i=0;i<129;i++){
  const time=i*3/32;pose(quiet,0,time);pose(old,0,time);pose(natural,0,time);const qb=quiet.meshes[0].skeleton.bones,ob=old.meshes[0].skeleton.bones,nb=natural.meshes[0].skeleton.bones,expected=literalWorld(v2,time);
  if(!first)first=qb.map(b=>b.matrixWorld.clone());let tailDelta=0,relative=0,head17=0,literal=0;
  for(const v of tail){quiet.meshes[0].getVertexPosition(v,a);old.meshes[0].getVertexPosition(v,b);tailDelta=Math.max(tailDelta,a.distanceTo(b));}
  for(const[j,p]of[[4,1],[5,4]]){const x=qb[p].matrixWorld.clone().invert().multiply(qb[j].matrixWorld),y=ob[p].matrixWorld.clone().invert().multiply(ob[j].matrixWorld);relative=Math.max(relative,...x.elements.map((v,k)=>Math.abs(v-y.elements[k])));}
  for(const j of[2,3])head17=Math.max(head17,...qb[j].matrixWorld.elements.map((v,k)=>Math.abs(v-nb[j].matrixWorld.elements[k])));
  for(let j=0;j<26;j++)literal=Math.max(literal,...qb[j].matrixWorld.elements.map((v,k)=>Math.abs(v-expected[j].elements[k])));
  result.maximum_actual_neck_motion_component=Math.max(result.maximum_actual_neck_motion_component,...qb[2].matrixWorld.elements.map((v,k)=>Math.abs(v-first[2].elements[k])));result.maximum_actual_head_motion_component=Math.max(result.maximum_actual_head_motion_component,...qb[3].matrixWorld.elements.map((v,k)=>Math.abs(v-first[3].elements[k])));
  result.maximum_tail_position_delta_m=Math.max(result.maximum_tail_position_delta_m,tailDelta);result.maximum_tail_relative_bone_component=Math.max(result.maximum_tail_relative_bone_component,relative);result.maximum_head_neck_vs_source17_component=Math.max(result.maximum_head_neck_vs_source17_component,head17);result.maximum_all129_literal_reference_component=Math.max(result.maximum_all129_literal_reference_component,literal);result.samples++;result.poses.push({time,tailDelta,relative,head17,literal});
 }
 need(result.samples===129&&result.maximum_tail_position_delta_m===0&&result.maximum_tail_relative_bone_component===0&&result.maximum_head_neck_vs_source17_component===0&&result.maximum_all129_literal_reference_component<=1e-5,'Actual quiet15 all129 literal/head17/tailold13 independent checks');need(result.maximum_actual_head_motion_component>1e-4&&result.maximum_actual_neck_motion_component>1e-4,'Actual nonzero head/neck motion');result.status='ACTUAL_QUIET15_CROSSCHECK129_ONLY_PASS';return result;
 }finally{for(const m of models){m.mixer.stopAllAction();m.mixer.uncacheRoot(m.scene);for(const x of m.meshes)x.skeleton.dispose();}}
}


function quietSourceAdmission(parent,child,field,recipeSHA,role){
 const clean=structuredClone(child.doc),notice=clean.asset.extras.chicago4d_quiet_head_neck_idle_v6;
 const parentSHA=role==='quiet15-candidate'?'0ced8a09e27da047ad404c902e9d032e43654393027199db8dfd9c315be17929':'a3eca1a164e2adf13d7d5f6699ff43de66d48dde0e3220f4aae90591dcaf4cb3';
 need(JSON.stringify(notice)===JSON.stringify({source_parent_sha256:parentSHA,head_template_sha256:'a9d9573368f48b4df839c3f246035aa7ac96b04ca098c37e015113266954cf8e',recipe_sha256:recipeSHA,binding_version:6,role,selected_clip:role==='quiet15-candidate'?QUIET:null,qualification:'UNRUN',old_certificate_transferred:false}),'Exact new source notice and unqualified creation state');delete clean.asset.extras.chicago4d_quiet_head_neck_idle_v6;
 if(role==='quiet15-candidate'){
  const quiet=clean.animations.pop(),natural=parent.doc.animations[1],retained=natural.channels.filter(c=>c.target.node!==4&&c.target.node!==5);
  need(quiet.name===QUIET&&quiet.channels.length===15&&quiet.samplers.length===15&&JSON.stringify(quiet.channels)===JSON.stringify(retained)&&JSON.stringify(quiet.samplers)===JSON.stringify(natural.samplers.slice(0,15)),'Exact quiet15 retained original source channels/curves, no added tail');
 }
 need(JSON.stringify(clean)===JSON.stringify(parent.doc)&&parent.bin.length===child.bin.length,'All original source metadata/geometry/rig/oldclips retained');
 const change=new Map(field.field_rows.map(x=>[x.row,x])),allowed=new Set();need(change.size===417&&field.head_rows.length===2306,'Exact authored HEAD field inventories');
 for(const name of['JOINTS_0','WEIGHTS_0']){
  const p=rawAttribute(parent,0,name),c=rawAttribute(child,0,name),key=name==='JOINTS_0'?'joints':'weights';
  for(let row=0;row<p.length/4;row++)for(let k=0;k<4;k++)need(Object.is(c[row*4+k],change.has(row)?change.get(row)[key][k]:p[row*4+k]),'Exact V4HEAD field or protected original V2TAIL tuple');
  const a=parent.doc.accessors[parent.doc.meshes[0].primitives[0].attributes[name]],v=parent.doc.bufferViews[a.bufferView],size=name==='JOINTS_0'?8:16;need(!v.byteStride,'Exact dense skin stream');
  for(const row of change.keys()){const begin=(v.byteOffset??0)+(a.byteOffset??0)+row*size;for(let k=0;k<size;k++)allowed.add(begin+k);}
 }
 let changed=0;for(let i=0;i<parent.bin.length;i++)if(parent.bin[i]!==child.bin[i]){need(allowed.has(i),'Only declared HEAD skin bytes may differ');changed++;}need(changed===2938,'Exact reviewed2938 changed HEAD bytes, no BODY/EYE/TAIL/curve/image changes');
}
function runtimeAdmission(master,runtime){
 const clean=structuredClone(runtime.doc),notice=clean.asset.extras.chicago4d_quiet_head_neck_runtime_v6;
 need(JSON.stringify(notice)===JSON.stringify({authored_master_sha256:'0a93029a951c000771c9fc8ca39809fd5323633b2e70fc462ba27b7ab9ccfc5b',selected_clip:QUIET,exported_clips:1,unqualified17_exported:false,all_BIN_and_original_geometry_exact:true,qualification:'UNRUN',runtime_adoption:false}),'Exact one-quiet runtime projection provenance');delete clean.asset.extras.chicago4d_quiet_head_neck_runtime_v6;
 need(clean.animations.length===1&&clean.animations[0].name===QUIET&&JSON.stringify(clean.animations[0])===JSON.stringify(master.doc.animations[2]),'Only exact named quiet15 runtime clip, no failed17 fallback');clean.animations=structuredClone(master.doc.animations);need(JSON.stringify(clean)===JSON.stringify(master.doc)&&bytesEqual(runtime.bin,master.bin),'Whole runtime JSON reversal and completeBIN/geometry equality');
}
async function runtimeMasterParity(){
 const config=await(await fetch('/CONFIG.json')).json(),raw=await Promise.all([pinned(config.inputs.candidate),pinned(config.inputs.runtime_candidate)]),models=await Promise.all(raw.map(b=>load('',b))),[master,runtime]=models;
 master.selectedClipName=runtime.selectedClipName=QUIET;const a=master.meshes.map(cache),b=runtime.meshes.map(cache),p=new T.Vector3(),q=new T.Vector3(),n=new T.Vector3(),m=new T.Vector3(),cross=new T.Vector3();
 const report={samples:0,vertices_per_sample:12838,maximum_position_m:0,maximum_shader_normal_degrees:0,maximum_bone_world_component:0,tolerance_m:1e-5,tolerance_degrees:.01};
 try{for(let i=0;i<129;i++){pose(master,0,i*3/32);pose(runtime,0,i*3/32);for(let mi=0;mi<3;mi++){const af=normalContext(a[mi]),bf=normalContext(b[mi]);for(let v=0;v<a[mi].position.count;v++){a[mi].mesh.getVertexPosition(v,p);b[mi].mesh.getVertexPosition(v,q);report.maximum_position_m=Math.max(report.maximum_position_m,p.distanceTo(q));shaderNormal(a[mi],af,v,n);shaderNormal(b[mi],bf,v,m);report.maximum_shader_normal_degrees=Math.max(report.maximum_shader_normal_degrees,Math.atan2(cross.crossVectors(n,m).length(),n.dot(m))*180/Math.PI);}for(let j=0;j<26;j++)for(let k=0;k<16;k++)report.maximum_bone_world_component=Math.max(report.maximum_bone_world_component,Math.abs(a[mi].mesh.skeleton.bones[j].matrixWorld.elements[k]-b[mi].mesh.skeleton.bones[j].matrixWorld.elements[k]));}report.samples++;}
 need(report.samples===129&&report.maximum_position_m<=1e-5&&report.maximum_shader_normal_degrees<=.01&&report.maximum_bone_world_component===0,'All129 actual runtime/master quiet15 vertex/shadernormal/bone parity');report.status='ACTUAL_RUNTIME_MASTER_QUIET15_PARITY129_ONLY_PASS';return report;
 }finally{for(const m of models){m.mixer.stopAllAction();m.mixer.uncacheRoot(m.scene);for(const x of m.meshes)x.skeleton.dispose();}}
}

window.runPhysical=async mode=>{
 const started=performance.now(),config=await(await fetch('/CONFIG.json')).json();let source,candidate;
 const report={status:'BINDING_V2_NATIVE_INCOMPLETE',binding_mode:mode,key_count:0,midpoint_count:0,poses:[],normalization:[],failures:[],positions:{tolerance_m:1e-5,maximum_delta_m:0,evaluations:0},normals:{tolerance_degrees:.01,maximum_angle_degrees:0,evaluations:0},joint_world:{maximum_translation_error_m:0,maximum_matrix_component_error:0},physical:{maximum_segment_length_error_m:0,maximum_parent_residual_m:0,maximum_seam_gap_m:0,maximum_contact_error_m:0},WebGL_contexts_created:0,renderers_created:0,walking_enabled:false,photographic_acceptance:false};
 const fail=(condition,label,witness)=>{if(!condition&&report.failures.length<100)report.failures.push({label,witness});};
 try{
  need(mode==='old13'||mode==='quiet15'||mode==='runtime15','Explicit original13 or new17 actual exported clip');
  need(T.REVISION==='185'&&T.ShaderChunk.skinnormal_vertex.includes('skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;')&&T.ShaderChunk.defaultnormal_vertex.includes('transformedNormal = normalMatrix * transformedNormal;'),'Exact native shader normal algebra');
  const resources=Object.fromEntries(await Promise.all(Object.entries(config.inputs).map(async([name,pin])=>[name,await pinned(pin)])));
  const reference=json(resources.cpu_reference),derivation=json(resources.anatomy_receipt),controls=json(resources.controls26),limit=json(resources.limits);
  const selectedResource=mode==='runtime15'?'runtime_candidate':'candidate';
  const oldRaw=glb(resources.motion_source),masterRaw=glb(resources.candidate),candidateRaw=glb(resources[selectedResource]),legacyRaw=glb(resources.legacy_parent),pairedRaw=glb(resources.paired_reference),parentRaw=glb(resources.selected_parent),v2Raw=glb(resources.v2_candidate),v2PairRaw=glb(resources.v2_paired_reference);
  const proof=json(resources.static_socket_receipt);
  need(proof.status==='QUIET_HEAD_NECK_V6_CURRENT_SOURCE_STATIC_ONLY_PASS'&&proof.authored_master_sha256===config.inputs.candidate.sha256&&proof.runtime_candidate_sha256===config.inputs.runtime_candidate.sha256&&proof.paired925_sha256===config.inputs.paired_reference.sha256,'Exact current canonical static source/geometry receipt');
  need(JSON.stringify(proof.code_pins)===JSON.stringify(config.code_pins)&&proof.source_controls?.length===23&&proof.source_controls.every(x=>x.detected),'Same-code actual canonical static and all23 source/projection controls');
  quietSourceAdmission(v2Raw,masterRaw,json(resources.head_field),config.inputs.quiet_recipe.sha256,'quiet15-candidate');
  quietSourceAdmission(v2PairRaw,pairedRaw,json(resources.head_field),config.inputs.quiet_recipe.sha256,'paired925-head-neck-reference');
  runtimeAdmission(masterRaw,glb(resources.runtime_candidate));
  const frames=mode==='old13'?json(resources.accepted_matrices).frames:literalFrames(v2Raw);
  need(frames.length===65&&frames.every((f,i)=>f.time_s===i*12/64),'Actual unchanged65 key schedule');
  for(let mi=0;mi<3;mi++)for(const name of['JOINTS_0','WEIGHTS_0'])need(bytesEqual(rawAttribute(candidateRaw,mi,name),rawAttribute(pairedRaw,mi,name)),'Entire actual candidate and paired925 skin streams equal');
  [source,candidate]=await Promise.all([load(config.inputs.motion_source.url,resources.motion_source),load(config.inputs[selectedResource].url,resources[selectedResource])]);
  need(source.animations.length===2&&source.animations[0].tracks.length===13&&source.animations[1].tracks.length===17,'Unchanged original13/17 source clips');
  if(mode==='runtime15')need(candidate.animations.length===1&&candidate.animations[0].name===QUIET&&candidate.animations[0].tracks.length===15,'Only actual runtime quiet15 clip permitted');else need(candidate.animations.length===3&&candidate.animations[0].tracks.length===13&&candidate.animations[1].tracks.length===17&&candidate.animations[2].name===QUIET&&candidate.animations[2].tracks.length===15,'Retained13/failed17 and exact independent masterquiet15 loaded clips');
  need(JSON.stringify(await maps(source))===JSON.stringify(await maps(candidate)),'Actual decoded old and newly bound image/material equality');
  candidate.selectedClipName=mode==='old13'?null:QUIET;
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
 need(old.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&old.old13_parity?.samples===129&&old.failures.length===0,'Fresh master old13 parity and physical must pass');
 const master=window.masterQuietReport=await window.runPhysical('quiet15');
 need(master.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&master.failures.length===0,'Fresh master quiet15 physical129 must pass');
 const runtime=window.cpuReport=await window.runPhysical('runtime15');
 need(runtime.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&runtime.failures.length===0,'Fresh actual runtime quiet15 physical129 must pass');
 const parity=window.runtimeParityReport=await runtimeMasterParity();
 const cross=window.crossReport=await runCrossChecks();
 runtime.metric_loop_historical_scope=runtime.scope;runtime.scope='Actual canonical V6 one-clip runtime quiet head/neck finite129 physical proof; no continuous/world/photo/rider acceptance.';runtime.selected_exported_clip=QUIET;runtime.selected_exported_track_count=15;runtime.old_certificate_transferred=false;
 return{old13:old,master_quiet15:master,runtime_quiet15:runtime,runtime_master_parity129:parity,cross};
};

// Actual separate925 Mixer capture. No copied/fabricated bone transform reference.
let socketState=null;
const socketInventory=model=>{const rows=[],ids=new Map();model.scene.traverse(o=>{ids.set(o,rows.length);rows.push(o);});return rows.map(o=>({o,parent:o.parent===null?-1:ids.get(o.parent)??-1,name:o.name,type:o.type}));};
const disposeSocket=model=>{if(model){model.mixer.stopAllAction();model.mixer.uncacheRoot(model.scene);for(const mesh of model.meshes)mesh.skeleton.dispose();}};
window.beginSocketCapture=async()=>{
 need(!socketState&&window.old13Report?.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&window.masterQuietReport?.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&window.cpuReport?.status==='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'&&window.runtimeParityReport?.status==='ACTUAL_RUNTIME_MASTER_QUIET15_PARITY129_ONLY_PASS'&&window.crossReport?.status==='ACTUAL_QUIET15_CROSSCHECK129_ONLY_PASS','All fresh physical/parity/cross phases before raw capture');
 const config=await(await fetch('/CONFIG.json')).json();let candidate,parent;
 try{[candidate,parent]=await Promise.all([pinned(config.inputs.runtime_candidate).then(b=>load('',b)),pinned(config.inputs.paired_reference).then(b=>load('',b))]);
  need(candidate.animations.length===1&&candidate.animations[0].name===QUIET&&candidate.animations[0].tracks.length===15&&parent.animations.length===1&&parent.animations[0].tracks.length===13,'Exact actual one-quiet runtime and separate paired925 clip inventory');
  const c=socketInventory(candidate),p=socketInventory(parent);need(c.length===p.length&&c.every((r,i)=>r.name===p[i].name&&r.type===p[i].type&&r.parent===p[i].parent),'Exact native925 node/name/type/parent correspondence');
  // Import the genuine runtime-loaded clip into a separate native Mixer using
  // the exact matching paired925 node names. No sample matrices are copied.
  const quiet=candidate.animations[0].clone();need(quiet.name===QUIET&&quiet.tracks.length===15,'Actual runtime imported quiet clip');
  for(const track of quiet.tracks){const parsed=T.PropertyBinding.parseTrackName(track.name);need(T.PropertyBinding.findNode(parent.scene,parsed.nodeName)&&T.PropertyBinding.findNode(candidate.scene,parsed.nodeName),'Exact native clip target binding in both models');}
  parent.animations.push(quiet);candidate.selectedClipName=parent.selectedClipName=QUIET;
  for(const[mi,m]of candidate.meshes.entries()){const n=parent.meshes[mi];need(m.skeleton.bones.length===n.skeleton.bones.length&&m.skeleton.bones.every((b,i)=>b.name===n.skeleton.bones[i].name&&m.skeleton.boneInverses[i].elements.every((v,k)=>Object.is(v,n.skeleton.boneInverses[i].elements[k]))),'Actual paired925 palette and IBM equality');}
  const bodyC=candidate.meshes.find(m=>m.userData.parityKey==='1:0'),bodyP=parent.meshes.find(m=>m.userData.parityKey==='1:0'),eyeC=candidate.meshes.find(m=>m.userData.parityKey==='2:0'),eyeP=parent.meshes.find(m=>m.userData.parityKey==='2:0');need([bodyC,bodyP].every(m=>m?.geometry.attributes.position.count===5595)&&[eyeC,eyeP].every(m=>m?.geometry.attributes.position.count===3968),'Actual BODY/EYE row inventory');
  socketState={candidate,parent,c,p,bodyC,bodyP,eyeC,eyeP,next:0};return{frames_expected:129,reference_pose_method:'separate_native_AnimationMixer_actual_runtime_clip'};
 }catch(e){disposeSocket(candidate);disposeSocket(parent);throw e;}
};
window.captureSocketFrame=index=>{
 const st=socketState;need(st&&index===st.next&&index>=0&&index<129,'Exactly ordered full129 raw capture');const time=index*3/32;
 pose(st.candidate,0,time);pose(st.parent,0,time);
 const boneStates=st.c.every((row,i)=>{const a=row.o,b=st.p[i].o;return a.position.equals(b.position)&&a.quaternion.equals(b.quaternion)&&a.scale.equals(b.scale)&&a.matrixWorld.elements.every((v,k)=>Object.is(v,b.matrixWorld.elements[k]));});need(boneStates,'Actual independent925 Mixer root/bone states differ');
 const meshBases=[st.bodyC,st.bodyP,st.eyeC,st.eyeP].every(m=>identity(m.matrixWorld)&&identity(m.bindMatrix)&&identity(m.bindMatrixInverse));need(meshBases,'Canonical actual mesh/bind bases');
 const read=mesh=>{const p=new T.Vector3(),rows=[];for(let i=0;i<mesh.geometry.attributes.position.count;i++){mesh.getVertexPosition(i,p);need(p.toArray().every(Number.isFinite),'Finite real getVertexPosition readback');rows.push(p.x,p.y,p.z);}return rows;};
 const nodeStates=rows=>rows.map(row=>[...row.o.position.toArray(),...row.o.quaternion.toArray(),...row.o.scale.toArray(),...row.o.matrixWorld.elements]);const skeletonMatrices=model=>model.meshes.map(m=>Array.from(m.skeleton.boneMatrices));const actualBases=[st.bodyC,st.bodyP,st.eyeC,st.eyeP].map(m=>[m.matrixWorld.elements.slice(),m.bindMatrix.elements.slice(),m.bindMatrixInverse.elements.slice()]);
 const record={index,time_s:time,key:index%2===0?index/2:null,bone_states_identical:boneStates,skeletons_updated:true,mesh_bind_bases_identity:meshBases,candidate_node_states:nodeStates(st.c),parent_node_states:nodeStates(st.p),candidate_bone_world_matrices:st.candidate.meshes[0].skeleton.bones.map(b=>b.matrixWorld.elements.slice()),parent_bone_world_matrices:st.parent.meshes[0].skeleton.bones.map(b=>b.matrixWorld.elements.slice()),candidate_skeleton_matrices:skeletonMatrices(st.candidate),parent_skeleton_matrices:skeletonMatrices(st.parent),actual_mesh_bind_bases:actualBases,candidate_body:read(st.bodyC),parent_body:read(st.bodyP),candidate_eye:read(st.eyeC),parent_eye:read(st.eyeP),reference_pose_method:'separate_native_AnimationMixer_actual_runtime_clip',coordinate_precision:'native JS Number stored Float64LE; no extra Float32 vertex snapshot'};st.next++;return record;
};
window.endSocketCapture=()=>{need(socketState?.next===129,'All129 actual raw frames before disposal');const frames=socketState.next;disposeSocket(socketState.candidate);disposeSocket(socketState.parent);socketState=null;return{frames,models_disposed:true};};
