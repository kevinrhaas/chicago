// SPDX-License-Identifier: GPL-3.0-or-later
// Source prototype: exact current MASTER GLB -> coat-only material child.
// Generated pixels are original CC0-1.0 artwork; no historical textile capture.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const APP=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const MATERIAL='garment_outer__livery_coat_green_1904';
const WIDTH={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16};
const SIZE={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};
export const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const need=(ok,msg)=>{if(!ok)throw Error(msg);};
export function parse(raw){
  need(raw.length>=28&&raw.readUInt32LE(0)===0x46546c67&&raw.readUInt32LE(4)===2&&raw.readUInt32LE(8)===raw.length,'complete GLB2');
  const n=raw.readUInt32LE(12),at=20+n;
  need(n%4===0&&raw.readUInt32LE(16)===0x4e4f534a&&at+8<=raw.length,'JSON chunk');
  const doc=JSON.parse(raw.subarray(20,at));
  need(raw.readUInt32LE(at+4)===0x004e4942&&raw.readUInt32LE(at)===raw.length-at-8,'single BIN chunk');
  need(doc.buffers.length===1&&!doc.buffers[0].uri&&!doc.extensionsUsed?.length&&!doc.extensionsRequired?.length,'uncompressed MASTER only');
  const bin=raw.subarray(at+8);need(doc.buffers[0].byteLength<=bin.length,'embedded buffer bounds');
  return {doc,bin};
}
function encode(doc,bin){
  let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
  bin=Buffer.concat([bin,Buffer.alloc((4-bin.length%4)%4)]);
  const head=Buffer.alloc(20);head.writeUInt32LE(0x46546c67);head.writeUInt32LE(2,4);head.writeUInt32LE(28+json.length+bin.length,8);head.writeUInt32LE(json.length,12);head.writeUInt32LE(0x4e4f534a,16);
  const bh=Buffer.alloc(8);bh.writeUInt32LE(bin.length);bh.writeUInt32LE(0x004e4942,4);
  return Buffer.concat([head,json,bh,bin]);
}
export function rows(doc,bin,index){
  const a=doc.accessors[index],v=doc.bufferViews[a.bufferView],width=WIDTH[a.type]*SIZE[a.componentType];
  need(width&&!a.sparse&&!a.extensions&&!v.extensions&&v.buffer===0,'plain MASTER accessor required');
  const step=v.byteStride??width,start=(v.byteOffset??0)+(a.byteOffset??0),end=start+(a.count-1)*step+width;
  need(a.count>0&&step>=width&&end<=(v.byteOffset??0)+v.byteLength&&end<=bin.length,'accessor bounds');
  return Array.from({length:a.count},(_,i)=>bin.subarray(start+i*step,start+i*step+width));
}
function floats(doc,bin,index,width){
  const a=doc.accessors[index];need(a.componentType===5126&&!a.normalized&&WIDTH[a.type]===width,'FLOAT MASTER attribute');
  return rows(doc,bin,index).map(b=>Array.from({length:width},(_,i)=>b.readFloatLE(i*4)));
}
function indexRows(doc,bin,index){
  const a=doc.accessors[index];need(a.type==='SCALAR'&&!a.normalized&&[5121,5123,5125].includes(a.componentType),'unsigned indices');
  return rows(doc,bin,index).map(b=>b.readUIntLE(0,b.length));
}
export function splitGroups(indices,tangents,count){
  need(indices.length%3===0&&tangents.length===indices.length*4,'triangle corner tangents');
  const source=Array.from({length:count},(_,i)=>i),groups=Array.from({length:count},()=>new Map()),values=Array(count),out=[];
  for(let c=0;c<indices.length;c++){
    const old=indices[c];need(Number.isInteger(old)&&old>=0&&old<count,'index in original domain');
    const v=Float32Array.from(tangents.subarray(c*4,c*4+4));v[3]*=-1;
    need([...v].every(Number.isFinite)&&Math.abs(v[3])===1,'finite Mikk tangent with signed handedness');
    const bytes=Buffer.from(v.buffer),key=bytes.toString('hex');let next=groups[old].get(key);
    if(next===undefined){next=groups[old].size===0?old:source.length;groups[old].set(key,next);if(next===source.length)source.push(old);values[next]=bytes;}
    out.push(next);
  }
  need(groups.every(g=>g.size>0),'unreferenced vertices refused, no arbitrary tangent fill');
  return {source,indices:out,tangents:Buffer.concat(values),duplicates:source.length-count};
}
function expand(doc,bin,p){
  need((p.mode??4)===4&&p.indices!==undefined&&!p.attributes.TANGENT,'indexed original coat triangles without TANGENT');
  const idx=indexRows(doc,bin,p.indices),P=floats(doc,bin,p.attributes.POSITION,3),N=floats(doc,bin,p.attributes.NORMAL,3),U=floats(doc,bin,p.attributes.TEXCOORD_0,2);
  const po=[],no=[],uv=[];
  for(const i of idx){need(P[i]&&N[i]&&U[i],'same attribute domain');const len=Math.hypot(...N[i]);need(len>0,'nonzero original normal');po.push(...P[i]);no.push(...N[i].map(x=>x/len));uv.push(...U[i]);}
  need([...po,...no,...uv].every(Number.isFinite),'finite original corners');
  for(let c=0;c<idx.length;c+=3){const a=U[idx[c]],b=U[idx[c+1]],d=U[idx[c+2]];need((b[0]-a[0])*(d[1]-a[1])!==(b[1]-a[1])*(d[0]-a[0]),'no UV-degenerate MASTER triangles');}
  return {idx,P,U,positions:new Float32Array(po),normals:new Float32Array(no),uvs:new Float32Array(uv)};
}
function transform(p,m){return [0,1,2].map(i=>m[i]*p[0]+m[4+i]*p[1]+m[8+i]*p[2]+m[12+i]);}
// Matrix evaluation is performed by pinned glTF-Transform, not inferred from WEB normalized coordinates.
async function calibration(raw,io){
  const doc=await io.readBinary(raw),r=doc.getRoot();let area=0,uvArea=0;const parts=[];
  for(const mesh of r.listMeshes())for(const p of mesh.listPrimitives())if(p.getMaterial()?.getName()===MATERIAL){
    const nodes=r.listNodes().filter(n=>n.getMesh()===mesh);need(nodes.length===1,'one actual world transform per coat mesh');
    const m=nodes[0].getWorldMatrix(),pos=p.getAttribute('POSITION'),uv=p.getAttribute('TEXCOORD_0'),ix=p.getIndices().getArray();let a=0,u=0;
    for(let c=0;c<ix.length;c+=3){const P=[],U=[];for(const i of ix.slice(c,c+3)){let q=[],v=[];pos.getElement(i,q);uv.getElement(i,v);P.push(transform(q,m));U.push(v);}
      const v=P[1].map((x,j)=>x-P[0][j]),w=P[2].map((x,j)=>x-P[0][j]);const ar=Math.hypot(v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0])/2;
      need(ar>0,'no geometry-degenerate MASTER triangles');a+=ar;u+=Math.abs((U[1][0]-U[0][0])*(U[2][1]-U[0][1])-(U[1][1]-U[0][1])*(U[2][0]-U[0][0]))/2;}
    parts.push({mesh:mesh.getName(),world_area_m2:a,uv_area:u});area+=a;uvArea+=u;
  }
  need(parts.length===2&&area>0&&uvArea>0,'actual two-part Charles coat calibration');
  const repeat=1/(.032*Math.sqrt(uvArea/area));
  return {world_area_m2:area,uv_area:uvArea,repeat,metric_source:'MASTER positions with actual node world matrices; not normalized WEB accessor coordinates',parts:parts.map(p=>({...p,aggregate_area_based_tile_side_m:1/(repeat*Math.sqrt(p.uv_area/p.world_area_m2))})),limits:'One shared original coat slot requires one repeat. Partwise and local UV stretch remain; this is not a UV repair or uniform physical-thread-size claim.'};
}
export const linearToSRGB=x=>x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;
const height=(u,v)=>.000020*(.65*Math.cos(2*Math.PI*32*(u+v))+.25*Math.cos(2*Math.PI*16*(u-v))+.10*Math.cos(2*Math.PI*(3*u+5*v)));
export function pixel(channel,x,y,size=128){
  const u=(x+.5)/size,v=(y+.5)/size,h=height(u,v),heather=.65*Math.sin(2*Math.PI*(3*u+5*v))+.35*Math.sin(2*Math.PI*(13*u-7*v));let rgb;
  if(channel==='color'){const s=1+.045*h/.000025+.025*heather;rgb=[.014,.026,.019].map(c=>linearToSRGB(c*s));}
  else if(channel==='orm')rgb=[1,.86+.025*heather-.018*h/.000025,0];
  else {need(channel==='normal','known channel');const e=.00001,dx=(height(u+e,v)-height(u-e,v))/(2*e*.032),dy=(height(u,v+e)-height(u,v-e))/(2*e*.032),l=Math.hypot(dx,dy,1);rgb=[(1-dx/l)/2,(1-dy/l)/2,(1+1/l)/2];}
  return [...rgb.map(c=>Math.max(0,Math.min(255,Math.round(c*255)))),255];
}
function crc32(buf){let n=-1;for(const b of buf){n^=b;for(let j=0;j<8;j++)n=(n>>>1)^(0xedb88320&-(n&1));}return(n^-1)>>>0;}
function chunk(name,data){const t=Buffer.from(name),n=Buffer.alloc(4),c=Buffer.alloc(4);n.writeUInt32BE(data.length);c.writeUInt32BE(crc32(Buffer.concat([t,data])));return Buffer.concat([n,t,data,c]);}
function png(channel){const ih=Buffer.alloc(13);ih.writeUInt32BE(128);ih.writeUInt32BE(128,4);ih[8]=8;ih[9]=6;const data=Buffer.alloc(128*(1+128*4));for(let y=0;y<128;y++)for(let x=0;x<128;x++)data.set(pixel(channel,x,y),y*513+1+x*4);return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(data)),chunk('IEND',Buffer.alloc(0))]);}
export function derive(raw,recipe,recipeSHA,parentSHA,lod,mikk,repeat){
  const {doc:parent,bin}=parse(raw),doc=structuredClone(parent),blocks=[bin],report=[];let length=bin.length;
  const append=(bytes)=>{const pad=(4-length%4)%4;if(pad){blocks.push(Buffer.alloc(pad));length+=pad;}const i=doc.bufferViews.length;doc.bufferViews.push({buffer:0,byteOffset:length,byteLength:bytes.length});blocks.push(bytes);length+=bytes.length;return i;};
  const accessor=(bytes,old,count)=>{const a=structuredClone(old);delete a.byteOffset;a.count=count;a.bufferView=append(bytes);doc.accessors.push(a);return doc.accessors.length-1;};
  const selected=[];
  for(const [mi,m]of doc.meshes.entries())for(const [pi,p]of m.primitives.entries())if(doc.materials[p.material]?.name===MATERIAL){
    const e=expand(parent,bin,parent.meshes[mi].primitives[pi]),t=mikk.generateTangents(e.positions,e.normals,e.uvs),g=splitGroups(e.idx,t,e.P.length);
    for(const [semantic,ai]of Object.entries(p.attributes)){const original=rows(parent,bin,ai);need(original.length===e.P.length,'coat attribute domain');p.attributes[semantic]=accessor(Buffer.concat(g.source.map(i=>original[i])),parent.accessors[ai],g.source.length);}
    for(const target of p.targets??[])for(const [semantic,ai]of Object.entries(target)){const original=rows(parent,bin,ai);need(original.length===e.P.length,'morph domain');target[semantic]=accessor(Buffer.concat(g.source.map(i=>original[i])),parent.accessors[ai],g.source.length);}
    p.attributes.TANGENT=accessor(g.tangents,{componentType:5126,type:'VEC4'},g.source.length);
    const idx=Buffer.alloc(g.indices.length*4);g.indices.forEach((v,i)=>idx.writeUInt32LE(v,i*4));p.indices=accessor(idx,{componentType:5125,type:'SCALAR'},g.indices.length);
    report.push({mesh:mi,primitive:pi,old_vertices:e.P.length,new_vertices:g.source.length,duplicates:g.duplicates,corners:e.idx.length,source_vertex:g.source,corner_to_vertex:g.indices,mikk_corner_sha256:sha(Buffer.from(t.buffer,t.byteOffset,t.byteLength)),glTF_tangent_sha256:sha(g.tangents)});selected.push(p.material);
  }
  need(report.length===2&&new Set(selected).size===1,'only current two-part shared coat');
  const material=doc.materials[selected[0]];need(!material.normalTexture&&!material.pbrMetallicRoughness?.baseColorTexture,'factor-only original coat');
  doc.images??=[];doc.textures??=[];doc.samplers??=[];const sampler=doc.samplers.length;doc.samplers.push({magFilter:9729,minFilter:9987,wrapS:10497,wrapT:10497});
  const maps={};for(const channel of ['color','orm','normal']){const bytes=png(channel),image=doc.images.length;doc.images.push({name:'original_CC0_charles_wool_'+channel,mimeType:'image/png',bufferView:append(bytes)});maps[channel]=doc.textures.length;doc.textures.push({source:image,sampler});}
  const info=index=>({index,texCoord:0,extensions:{KHR_texture_transform:{scale:[repeat,repeat]}}});
  material.pbrMetallicRoughness={...material.pbrMetallicRoughness,baseColorFactor:[1,1,1,1],metallicFactor:0,roughnessFactor:1,baseColorTexture:info(maps.color),metallicRoughnessTexture:info(maps.orm)};
  material.normalTexture={...info(maps.normal),scale:1};
  material.extras={...material.extras,chicago4d_cloth_microtexture:{version:1,profile:'wool',source_material:MATERIAL,runtime_weave:recipe.runtime_weave,grade:'reconstructed',license:'CC0-1.0',historical_texture:false,photo_quality_accepted:false,recipe_sha256:recipeSHA,parent_glb_sha256:parentSHA,uv_repeat:repeat,tile_side_m:.032,lod}};
  doc.extensionsUsed=['KHR_texture_transform'];doc.buffers[0].byteLength=length;
  return {raw:encode(doc,Buffer.concat(blocks)),report};
}
export function dependencies(root){
  const require=createRequire(import.meta.url);for(const name of ['cli','core','extensions','functions']){const p=JSON.parse(fs.readFileSync(path.join(root,'@gltf-transform',name,'package.json')));need(p.version==='4.5.0','actual repository toolchain pin4.5.0: '+name);}
  const pkg=JSON.parse(fs.readFileSync(path.join(root,'mikktspace/package.json')));need(pkg.version==='1.1.1'&&pkg.license==='MIT','official pinned Mikk implementation');
  return {mikk:require(path.join(root,'mikktspace')),NodeIO:require(path.join(root,'@gltf-transform/core')).NodeIO,ALL_EXTENSIONS:require(path.join(root,'@gltf-transform/extensions')).ALL_EXTENSIONS};
}
export function validateRecipe(r){
  need(r.id==='charles-coat-woven-v1'&&r.asset_id==='nelson_charles_1904_coachman'&&r.material===MATERIAL,'explicit Charles-only recipe');
  need(r.parent_revision==='fc5a52b6cab3eed78e2db5864aa811dff5df2795'&&r.parents?.length===8,'exact approved base and eight bindings');
  const names=new Set();for(const row of r.parents){need(/^assets\/humans\/(?:web\/)?nelson_charles_1904_coachman\.lod[0-3]\.glb$/.test(row.file)&&!names.has(row.file),'only eight unique Charles paths');names.add(row.file);need(Number.isInteger(row.lod)&&row.file.endsWith('.lod'+row.lod+'.glb')&&Number.isSafeInteger(row.bytes)&&row.bytes>0&&row.bytes<=16*1024**2&&/^[a-f0-9]{64}$/.test(row.sha256)&&/^[a-f0-9]{40}$/.test(row.gitBlob),'exact parent byte/blob binding');}
  need(JSON.stringify(r.linear_color)==='[0.014,0.026,0.019,1]'&&r.roughness===.86&&r.metalness===0&&r.tile_px===128&&r.tile_side_m===.032&&r.runtime_weave==='portable_maps_with_common_macro','reviewed palette/scale/runtime mode');
}
export function parentTreeBlob(revision,file){
  // Paths here are repository-relative; running ls-tree inside APP would
  // silently prefix chicago/4d/ a second time and return an empty match.
  return execFileSync('git',['ls-tree',revision,'--','chicago/4d/'+file],{cwd:path.resolve(APP,'../..'),encoding:'utf8',env:{...process.env,GIT_NO_LAZY_FETCH:'1'}}).trim().split(/\s+/)[2];
}
async function main(){
  const [recipeFile,inputRoot,outRoot,depRoot]=process.argv.slice(2);need(recipeFile&&inputRoot&&outRoot&&depRoot,'usage: node human_charles_coat.mjs RECIPE INPUT_ROOT FRESH_EXTERNAL_OUT NODE_MODULES');
  need(!path.resolve(outRoot).startsWith(APP+path.sep)&&!fs.existsSync(outRoot),'new external output directory only');
  const recipeRaw=fs.readFileSync(recipeFile),r=JSON.parse(recipeRaw);validateRecipe(r);
  const {mikk,NodeIO,ALL_EXTENSIONS}=dependencies(depRoot),io=new NodeIO().registerExtensions(ALL_EXTENSIONS),inputs=[];
  for(const row of r.parents.filter(p=>p.lod<2&&!p.file.includes('/web/'))){const raw=fs.readFileSync(path.join(inputRoot,row.file));need(raw.length===row.bytes&&sha(raw)===row.sha256,'exact MASTER parent');need(parentTreeBlob(r.parent_revision,row.file)===row.gitBlob,'parent tree binding');inputs.push({row,raw});}
  need(inputs.length===2&&inputs.some(x=>x.row.lod===0)&&inputs.some(x=>x.row.lod===1),'exact two MASTER near inputs');
  const metric=await calibration(inputs.find(x=>x.row.lod===0).raw,io),children=inputs.map(({row,raw})=>({row,...derive(raw,r,sha(recipeRaw),row.sha256,row.lod,mikk,metric.repeat)}));
  // No original input or APP path is opened for writing. No WEB output yet.
  fs.mkdirSync(outRoot);for(const child of children){const name=path.basename(child.row.file);fs.writeFileSync(path.join(outRoot,name),child.raw,{flag:'wx'});fs.writeFileSync(path.join(outRoot,name+'.corners.json'),JSON.stringify({recipe_sha256:sha(recipeRaw),parent_sha256:child.row.sha256,child_sha256:sha(child.raw),rows:child.report},null,2)+'\n',{flag:'wx'});}
  fs.writeFileSync(path.join(outRoot,'receipt.json'),JSON.stringify({status:'UNQUALIFIED_MASTER_CHILDREN',recipe_sha256:sha(recipeRaw),calibration:metric,children:children.map(c=>({file:path.basename(c.row.file),sha256:sha(c.raw),bytes:c.raw.length,duplicates:c.report.map(x=>x.duplicates)})),web_generated:false,assets_installed:false,native_or_photo_accepted:false},null,2)+'\n',{flag:'wx'});
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
