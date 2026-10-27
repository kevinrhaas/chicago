// SPDX-License-Identifier: GPL-3.0-or-later
// Separate thin-sheet optical delivery; all physical geometry remains byte exact.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {parseArgs} from 'node:util';
import {fileURLToPath} from 'node:url';
const {values}=parseArgs({options:{'source-dir':{type:'string'},output:{type:'string'}}});
if(!values['source-dir']||!values.output)throw Error('Explicit source-dir and fresh output required');
const source=path.resolve(values['source-dir']),out=path.resolve(values.output);
if(out===source||out.startsWith(source+'/')||fs.existsSync(out))throw Error('Fresh external output required');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),need=(x,m)=>{if(!x)throw Error(m)};
const producer=sha(fs.readFileSync(fileURLToPath(import.meta.url)));
const inputs=[
 ['near','3d2f3a802f4b32dba6a3e61f2c188dddce4db05cecfcbba81e1e8d369d5dfe89',45338],
 ['mid','d5cdd34e981d29db41634ac780c22526742f6a20527b5866d2349c727a67400d',23062],
];
fs.mkdirSync(out,{recursive:true});const rows=[];
for(const[detail,expected,triangles]of inputs){
 const file=`brougham-${detail}.glb`,output=`brougham-${detail}-delivery-v1.glb`,raw=fs.readFileSync(path.join(source,file));
 need(sha(raw)===expected,'Exact physical indexed source '+detail);
 need(raw.readUInt32LE(0)===0x46546c67&&raw.readUInt32LE(4)===2&&raw.readUInt32LE(8)===raw.length,'GLB envelope');
 const n=raw.readUInt32LE(12);need(raw.readUInt32LE(16)===0x4e4f534a,'JSON chunk');
 const original=JSON.parse(raw.subarray(20,20+n)),doc=structuredClone(original),off=20+n;
 need(raw.readUInt32LE(off+4)===0x004e4942&&off+8+raw.readUInt32LE(off)===raw.length,'One final BIN chunk');
 const binChunk=raw.subarray(off); // Header, payload and padding remain BYTE EXACT.
 need(doc.materials.length===8&&doc.extras.statistics.triangles===triangles,'Exact physical inventory');
 const glass=doc.materials[7];need(glass.extensions.KHR_materials_transmission.transmissionFactor===.98&&glass.pbrMetallicRoughness.baseColorFactor[3]===1,'Physical optical input');
 glass.name='thin_sheet_cabin_glass_delivery_reconstruction';delete glass.extensions.KHR_materials_transmission;
 glass.alphaMode='BLEND';glass.pbrMetallicRoughness.baseColorFactor[3]=.14;
 for(const key of['extensionsUsed','extensionsRequired'])if(doc[key])doc[key]=doc[key].filter(x=>x!=='KHR_materials_transmission');
 doc.extras.runtime_derivation={schema:1,source_indexed_sha256:expected,producer_sha256:producer,
  geometry_and_all_binary_bytes_unchanged:true,materials0_through6_unchanged:true,
  glass_delivery_profile:{alphaMode:'BLEND',opacity:.14,transmission:0,ior:1.5,
   interpretation:'Reconstructed thin-sheet appearance approximation to avoid the whole-scene transmission pass; full physical optical master retained'},
  photographic_accepted:false,world_budget_accepted:false};
 doc.extras.status+='; separate thin-sheet optical delivery approximation; all physical geometry retained; acceptance pending';
 for(const key of['nodes','meshes','accessors','bufferViews','buffers','scenes','scene'])need(JSON.stringify(doc[key])===JSON.stringify(original[key]),'Geometry/layout changed '+key);
 need(JSON.stringify(doc.materials.slice(0,7))===JSON.stringify(original.materials.slice(0,7)),'Protected optics changed');
 const json=Buffer.from(JSON.stringify(doc)),pad=Buffer.alloc((-json.length)&3,0x20),header=Buffer.alloc(20);
 header.writeUInt32LE(0x46546c67);header.writeUInt32LE(2,4);header.writeUInt32LE(20+json.length+pad.length+binChunk.length,8);
 header.writeUInt32LE(json.length+pad.length,12);header.writeUInt32LE(0x4e4f534a,16);
 const bytes=Buffer.concat([header,json,pad,binChunk]);fs.writeFileSync(path.join(out,output),bytes);
 need(sha(fs.readFileSync(path.join(source,file)))===expected,'Physical source mutated');
 rows.push({detail,file:output,sha256:sha(bytes),bytes:bytes.length,triangles,source_file:file,source_sha256:expected,
  binary_chunk_sha256:sha(binChunk),all_geometry_and_BIN_bytes_exact_source:true,materials0_through6_exact_source:true});
}
const result={scope:'External unadopted optical-only delivery; no geometry simplification or app mutation',producer_sha256:producer,
 rows,independent_structure_loader_Khronos:'UNRUN',photographic_accepted:false,world_budget_accepted:false};
fs.writeFileSync(path.join(out,'CANDIDATE.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
