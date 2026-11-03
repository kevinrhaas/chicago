#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
// Reuse the repository's4.5.0 portable glTF stack; never download packages here.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';

const flags={};
for(let i=2;i<process.argv.length;i+=2){if(!process.argv[i]?.startsWith('--')||!process.argv[i+1])throw Error('Expected named arguments');flags[process.argv[i].slice(2)]=process.argv[i+1];}
for(const name of ['input','output-dir','tools-root','parameters'])if(!flags[name])throw Error(`Missing --${name}`);
const parameters=JSON.parse(fs.readFileSync(flags.parameters));
const tools=path.resolve(flags['tools-root']),require=createRequire(import.meta.url);
const pins={'@gltf-transform/core':'4.5.0','@gltf-transform/functions':'4.5.0','@gltf-transform/extensions':'4.5.0','meshoptimizer':'1.2.0','sharp':'0.35.5'};
for(const [name,version] of Object.entries(pins))if(JSON.parse(fs.readFileSync(path.join(tools,name,'package.json'))).version!==version)throw Error(`Unreviewed ${name} version`);
async function load(name){return import(pathToFileURL(require.resolve(name,{paths:[tools]})).href);}
const {NodeIO}=await load('@gltf-transform/core');
const {prune,weld,reorder,compactPrimitive,textureCompress}=await load('@gltf-transform/functions');
const {EXTMeshoptCompression,EXTTextureWebP}=await load('@gltf-transform/extensions');
const {MeshoptDecoder,MeshoptEncoder,MeshoptSimplifier}=await load('meshoptimizer');
const {default:sharp}=await load('sharp');
sharp.concurrency(1);
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready,MeshoptSimplifier.ready]);
const io=new NodeIO().registerExtensions([EXTMeshoptCompression,EXTTextureWebP]).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const digest=raw=>crypto.createHash('sha256').update(raw).digest('hex');
function rgbaMipEstimate(width,height){let bytes=0;for(;;){bytes+=width*height*4;if(width===1&&height===1)return bytes;width=Math.max(1,Math.floor(width/2));height=Math.max(1,Math.floor(height/2));}}
function triangleSemantics(primitive){
  const semantics=primitive.listSemantics().sort();
  const descriptors=Object.fromEntries(semantics.map(name=>{const a=primitive.getAttribute(name);return [name,{type:a.getType(),componentType:a.getComponentType(),normalized:a.getNormalized()}];}));
  const streams=semantics.map(name=>{const a=primitive.getAttribute(name),array=a.getArray();return {array,width:array.length/a.getCount(),bytes:Buffer.from(array.buffer,array.byteOffset,array.byteLength)};});
  const cache=[];
  const vertex=index=>cache[index]??(cache[index]=streams.map(s=>s.bytes.subarray(index*s.width*s.array.BYTES_PER_ELEMENT,(index+1)*s.width*s.array.BYTES_PER_ELEMENT).toString('hex')).join(''));
  const indices=primitive.getIndices().getArray(),triangles=[];
  for(let i=0;i<indices.length;i+=3){
    const a=vertex(indices[i]),b=vertex(indices[i+1]),c=vertex(indices[i+2]);
    // Rotate the complete paired shader tuples together. Reversing winding,
    // sorting individual vertices, or independently matching attributes is
    // deliberately not allowed. Triangle order alone is irrelevant here.
    triangles.push([a+b+c,b+c+a,c+a+b].sort()[0]);
  }
  triangles.sort();
  return {attributes:descriptors,triangle_count:triangles.length,oriented_paired_triangle_multiset_sha256:digest(triangles.join('\n'))};
}
function snapshot(document){
  const root=document.getRoot();
  return {
    asset_credit:root.getAsset().extras,
    nodes:root.listNodes().map(n=>({name:n.getName(),translation:n.getTranslation(),rotation:n.getRotation(),scale:n.getScale(),children:n.listChildren().map(c=>c.getName()),mesh:n.getMesh()?.getName()??null})),
    images:root.listTextures().map(t=>digest(t.getImage())).sort(),
    materials:root.listMaterials().map(m=>({name:m.getName(),doubleSided:m.getDoubleSided(),alphaMode:m.getAlphaMode(),baseColor:m.getBaseColorFactor(),metallic:m.getMetallicFactor(),roughness:m.getRoughnessFactor(),normalScale:m.getNormalScale(),occlusionStrength:m.getOcclusionStrength(),
      textures:['BaseColor','Normal','MetallicRoughness','Occlusion','Emissive'].map(slot=>{const t=m[`get${slot}Texture`]();return t?{slot,image:digest(t.getImage()),texCoord:m[`get${slot}TextureInfo`]().getTexCoord()}:null;})})),
    meshes:root.listMeshes().map(m=>({name:m.getName(),primitives:m.listPrimitives().map(p=>({material:p.getMaterial().getName(),mode:p.getMode(),...triangleSemantics(p)}))}))
  };
}
function geometryCost(document){
  let triangles=0,vertices=0;
  for(const mesh of document.getRoot().listMeshes())for(const p of mesh.listPrimitives()){triangles+=p.getIndices().getCount()/3;vertices+=p.getAttribute('POSITION').getCount();}
  return {triangles,vertices,draw_batches:document.getRoot().listMeshes().reduce((n,m)=>n+m.listPrimitives().length,0)};
}
async function webTextures(document,level,size){
  const original=snapshot(document),textures=document.getRoot().listTextures();
  const inputs=new Map(textures.map(t=>[t,{bytes:new Uint8Array(t.getImage()),sha256:digest(t.getImage()),roles:[]}]));
  for(const material of document.getRoot().listMaterials())for(const slot of ['BaseColor','Normal','MetallicRoughness','Occlusion','Emissive']){
    const texture=material[`get${slot}Texture`]();if(texture&&!inputs.get(texture).roles.includes(slot))inputs.get(texture).roles.push(slot);
  }
  const quality={near:97,mid:93,far:90}[level];
  await document.transform(
    textureCompress({encoder:sharp,targetFormat:'webp',resize:[size,size],quality,slots:/^(baseColorTexture|emissiveTexture)$/}),
    textureCompress({encoder:sharp,targetFormat:'webp',resize:[size,size],quality:97,nearLossless:true,slots:/^(metallicRoughnessTexture|occlusionTexture)$/}),
    // Downsampled normal pixels can lie closer to a short decoded vector:
    // even one channel step exceeded the fixed one-degree limit in trial1.
    // Keep those smaller normal maps lossless rather than relax that limit.
    textureCompress({encoder:sharp,targetFormat:'webp',resize:[size,size],quality:97,nearLossless:level==='near',lossless:level!=='near',slots:/^normalTexture$/})
  );
  if(document.getRoot().listTextures().some(t=>!inputs.has(t))||document.getRoot().listTextures().length!==textures.length)throw Error('Texture identity changed during declared transcoding');
  const replacements={},measurements=[],failures=[];
  for(const texture of textures){
    const input=inputs.get(texture),image=texture.getImage();replacements[input.sha256]=digest(image);
    const a=await sharp(input.bytes).resize({width:size,height:size,fit:'inside',withoutEnlargement:true}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    const b=await sharp(image).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    if(a.info.width!==b.info.width||a.info.height!==b.info.height||a.info.channels!==4||b.info.channels!==4)throw Error('Unexpected web texture dimensions');
    let sum=0,squared=0,max=0,alphaExact=true;const channelSum=[0,0,0,0],channelSquared=[0,0,0,0],channelMax=[0,0,0,0];
    for(let i=0;i<a.data.length;i++){const error=Math.abs(a.data[i]-b.data[i]),channel=i%4;channelSum[channel]+=error;channelSquared[channel]+=error*error;channelMax[channel]=Math.max(channelMax[channel],error);if(channel===3){alphaExact&&=error===0;continue;}sum+=error;squared+=error*error;max=Math.max(max,error);}
    const count=a.info.width*a.info.height*3,rmse=Math.sqrt(squared/count);
    const pixels=count/3;let normalAngles=null;
    if(input.roles.includes('Normal')){
      let angleSum=0,angleSquared=0,angleMax=0;
      for(let i=0;i<a.data.length;i+=4){const x=[a.data[i]/127.5-1,a.data[i+1]/127.5-1,a.data[i+2]/127.5-1],y=[b.data[i]/127.5-1,b.data[i+1]/127.5-1,b.data[i+2]/127.5-1];const angle=Math.acos(Math.max(-1,Math.min(1,x.reduce((n,v,j)=>n+v*y[j],0)/(Math.hypot(...x)*Math.hypot(...y)))))*180/Math.PI;angleSum+=angle;angleSquared+=angle*angle;angleMax=Math.max(angleMax,angle);}
      normalAngles={mean_deg:angleSum/pixels,rms_deg:Math.sqrt(angleSquared/pixels),max_deg:angleMax};
    }
    const dataTexture=input.roles.some(r=>['Normal','MetallicRoughness','Occlusion'].includes(r));
    if(!alphaExact||rmse>{near:5,mid:6,far:8}[level]||(dataTexture&&Math.max(...channelMax)>2)||(normalAngles&&normalAngles.max_deg>1))failures.push({roles:input.roles,RMSE_RGB:rmse,channel_max:channelMax,normalAngles});
    measurements.push({source_sha256:input.sha256,web_sha256:digest(image),roles:input.roles,codec:input.roles.includes('Normal')&&level!=='near'?'lossless WebP':dataTexture?'near-lossless WebP97':'lossy base-color WebP',source_bytes:input.bytes.length,web_bytes:image.length,width:b.info.width,height:b.info.height,quality:dataTexture?97:quality,mean_absolute_RGB_error:sum/count,RMSE_RGB:rmse,max_absolute_RGB_error:max,channel_MAE:channelSum.map(x=>x/pixels),channel_RMSE:channelSquared.map(x=>Math.sqrt(x/pixels)),channel_max:channelMax,normal_angles:normalAngles,alpha_exact:alphaExact});
  }
  fs.writeFileSync(path.join(output,`TEXTURE-TRIAL-${level}.json`),JSON.stringify({level,measurements,failures},null,2)+'\n');
  if(failures.length)throw Error('Web texture pixel/normal/channel contract exceeded: '+JSON.stringify(failures));
  // Only the explicitly measured image representations may change. Preserve
  // exact slot bindings, every paired geometry attribute, nodes and materials.
  const expected=structuredClone(original);expected.images=expected.images.map(s=>replacements[s]).sort();
  for(const material of expected.materials)for(const slot of material.textures)if(slot)slot.image=replacements[slot.image];
  if(JSON.stringify(expected)!==JSON.stringify(snapshot(document)))throw Error('Web transcoding changed more than its declared image representations');
  return measurements;
}
const output=path.resolve(flags['output-dir']);
if(fs.existsSync(output)&&fs.readdirSync(output).length)throw Error('Fresh export directory required');
fs.mkdirSync(output,{recursive:true});
const input=path.resolve(flags.input),inputRaw=fs.readFileSync(input),source=await io.read(input),before=snapshot(source);
const negativeControls=[];
const control=source.getRoot().listMeshes()[0].listPrimitives()[0],indexArray=control.getIndices().getArray(),first=Array.from(indexArray.slice(0,3));
try{
  indexArray.set([first[1],first[2],first[0]],0);
  if(JSON.stringify(snapshot(source))!==JSON.stringify(before))throw Error('Cyclic tuple rotation was incorrectly rejected');
  negativeControls.push('complete-tuple cyclic rotation accepted');
  indexArray.set([first[0],first[2],first[1]],0);
  if(JSON.stringify(snapshot(source))===JSON.stringify(before))throw Error('Reversed winding escaped the guard');
  negativeControls.push('reversed triangle winding rejected');
}finally{indexArray.set(first,0);}
for(const semantic of control.listSemantics()){
  const a=control.getAttribute(semantic),array=a.getArray(),width=array.length/a.getCount(),offset=first[0]*width,old=array[offset];
  try{array[offset]=old+.125;if(JSON.stringify(snapshot(source))===JSON.stringify(before))throw Error(`${semantic} change escaped the paired tuple guard`);negativeControls.push(`${semantic} shader-data mutation rejected`);}finally{array[offset]=old;}
}
await source.transform(prune({keepLeaves:true,keepAttributes:true,keepIndices:true,keepSolidTextures:true}));
const after=snapshot(source);
if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Prune changed live indexed geometry, normals, UVs, materials, images, frames or credit');
const sourceBytes=await io.writeBinary(source);
const rawPrimitiveSemantics=new Map(source.getRoot().listMeshes().map(m=>[m.getName(),triangleSemantics(m.listPrimitives()[0])]));
const midPrimitiveSemantics=new Map();
const result={schema:'chicago_farm_box_portable_web_lods_v2',input_sha256:digest(inputRaw),parameters_sha256:digest(fs.readFileSync(flags.parameters)),exporter_sha256:digest(fs.readFileSync(fileURLToPath(import.meta.url))),tool_versions:pins,
  equivalence:'Oriented full paired vertex-attribute triangle multiset within each exact primitive/material/node; winding and every live shader attribute retained. Image bytes, nodes, materials and credit checked separately.',negative_controls:negativeControls,
  lossless_prune:{before_bytes:inputRaw.length,after_bytes:sourceBytes.length,live_semantics_sha256:digest(JSON.stringify(after)),exact_live_semantics_equal:true},
  photographic_acceptance:false,lods:[]};
for(const level of ['near','mid','far']){
  const {ratio,error,texture_size:size}=parameters.export_lods[level];
  const document=await io.readBinary(sourceBytes);
  const simplificationErrors=[];
  const protectedStructure=[];
  if(level!=='near'){
    await document.transform(weld({tolerance:0}));
    for(const mesh of document.getRoot().listMeshes())for(const primitive of mesh.listPrimitives()){
      const structuralWood=mesh.getName().includes('CartBase')||['single_reconstructed_pole','central_drawbar_bearing','central_reconstructed_reach'].includes(mesh.getName());
      if(level==='far'&&structuralWood){simplificationErrors.push({mesh:mesh.getName(),preserved:'thin structural timber/board coverage',input_triangles:primitive.getIndices().getCount()/3,output_triangles:primitive.getIndices().getCount()/3,reportedError:0});continue;}
      const positions=primitive.getAttribute('POSITION').getArray(),normals=primitive.getAttribute('NORMAL').getArray(),uv=primitive.getAttribute('TEXCOORD_0').getArray();
      const attributes=new Float32Array(positions.length/3*5);
      for(let i=0;i<positions.length/3;i++)attributes.set([normals[i*3],normals[i*3+1],normals[i*3+2],uv[i*2],uv[i*2+1]],i*5);
      const inputIndices=new Uint32Array(primitive.getIndices().getArray());
      const preserveWheel=level==='far'&&mesh.getName().startsWith('wheel_');
      const effectiveError=preserveWheel ? .001 : error,effectiveRatio=preserveWheel ? .5 : ratio;
      const normalWeight=(level==='mid'||preserveWheel) ? .05 : .01,uvWeight=(level==='mid'||preserveWheel) ? .1 : .025;
      const [indices,reportedError]=MeshoptSimplifier.simplifyWithAttributes(inputIndices,positions,3,attributes,5,
        [normalWeight,normalWeight,normalWeight,uvWeight,uvWeight],null,Math.floor(inputIndices.length*effectiveRatio/3)*3,effectiveError,['Permissive']);
      if(reportedError>effectiveError+1e-7)throw Error(`LOD error bound exceeded: ${mesh.getName()}`);
      primitive.setIndices(primitive.getIndices().clone().setArray(indices));compactPrimitive(primitive);
      simplificationErrors.push({mesh:mesh.getName(),input_triangles:inputIndices.length/3,output_triangles:indices.length/3,reportedError,effectiveError,effectiveRatio,normalWeight,uvWeight,preserved:preserveWheel?'same wheel geometry as mid; retain rim/spoke silhouette':null});
    }
    await document.transform(prune({keepLeaves:true,keepAttributes:true,keepIndices:true,keepSolidTextures:true}));
  }
  for(const mesh of document.getRoot().listMeshes()){
    const semantics=triangleSemantics(mesh.listPrimitives()[0]),name=mesh.getName();
    if(level==='mid')midPrimitiveSemantics.set(name,semantics);
    if(level==='far'){
      const wood=name.includes('CartBase')||['single_reconstructed_pole','central_drawbar_bearing','central_reconstructed_reach'].includes(name);
      const expected=wood?rawPrimitiveSemantics.get(name):name.startsWith('wheel_')?midPrimitiveSemantics.get(name):null;
      if(expected){if(JSON.stringify(expected)!==JSON.stringify(semantics))throw Error('Protected far structure changed: '+name);protectedStructure.push({mesh:name,exact_to:wood?'canonical structural timber':'mid wheel geometry',paired_triangle_multiset_sha256:semantics.oriented_paired_triangle_multiset_sha256});}
    }
  }
  const beforeCleanup=snapshot(document),cleanupCostBefore=geometryCost(document);
  await document.transform(weld({tolerance:0}),reorder({encoder:MeshoptEncoder,target:'size',cleanup:false}),prune({keepLeaves:true,keepAttributes:true,keepIndices:true,keepSolidTextures:true}));
  if(JSON.stringify(beforeCleanup)!==JSON.stringify(snapshot(document)))throw Error('Lossless delivery cleanup changed paired shader semantics');
  const cleanupCostAfter=geometryCost(document);
  const textureMeasurements=await webTextures(document,level,size);
  const decodedBefore=snapshot(document);
  // No quantize() and no lossy FILTER preprocessing: compression retains exact
  // Float32 shader attributes. Web image loss is separately declared/measured.
  document.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({method:EXTMeshoptCompression.EncoderMethod.QUANTIZE});
  const file=path.join(output,`farm-box-${level}.glb`);await io.write(file,document);
  const stored=fs.readFileSync(file),header=JSON.parse(stored.subarray(20,20+stored.readUInt32LE(12)));
  if(!header.extensionsRequired?.includes('EXT_texture_webp')||!header.textures.every(t=>Number.isInteger(t.extensions?.EXT_texture_webp?.source)&&header.images[t.extensions.EXT_texture_webp.source].mimeType==='image/webp'))throw Error('WebP texture representation is not correctly declared in glTF');
  const decoded=await io.read(file),decodedAfter=snapshot(decoded);
  if(JSON.stringify(decodedBefore)!==JSON.stringify(decodedAfter))throw Error(`Meshopt decoded semantics changed: ${level}`);
  const images=decoded.getRoot().listTextures();
  const row={level,file:path.basename(file),sha256:digest(fs.readFileSync(file)),bytes:fs.statSync(file).size,...geometryCost(decoded),
    simplification:{ratio,error,source_geometry_exact:level==='near',method:level==='near'?'none':'meshoptimizer attribute-aware, seam-permissive within each original primitive',primitives:simplificationErrors},texture_dimensions:images.map(t=>t.getSize()),
    texture_representations:{format:'image/webp',representation:'bounded-loss web derivative; exact original/master PNGs preserved',source_PNGs_preserved_in_authored_master:true,measured_loss:textureMeasurements},
    protected_far_structure:protectedStructure,near_geometry_shader_attributes_exact_to_master:level==='near',
    lossless_delivery_cleanup:{before:cleanupCostBefore,after:cleanupCostAfter,oriented_paired_semantics_equal:true},
    webp_extension_declared_required:true,
    texture_RGBA8_mip_estimate_bytes:images.reduce((n,t)=>n+rgbaMipEstimate(...t.getSize()),0),
    decoded_semantics_sha256:digest(JSON.stringify(decodedAfter)),meshopt_decoded_exact_to_precompression:true};
  result.lods.push(row);process.stdout.write(JSON.stringify(row)+'\n');
}
// The25% mid target respects the declared .001 appearance-error bound on this
// seam-rich source. ROOT reviewed the actual26.05% reduction; the initial30%
// trial remains a failed receipt. Do not increase error merely to chase ratio.
// The first aggressively simplified far view damaged visible board coverage
// and rims. Preserve those parts; retain at least40% geometry reduction rather
// than forcing a smaller but visibly broken mesh. Repository caps stay fixed.
if(!(result.lods[1].triangles<=result.lods[0].triangles*.75&&result.lods[2].triangles<=result.lods[0].triangles*.6))throw Error('Substantial LOD triangle reduction was not achieved');
fs.writeFileSync(path.join(output,'EXPORT-RECEIPT.json'),JSON.stringify(result,null,2)+'\n');
