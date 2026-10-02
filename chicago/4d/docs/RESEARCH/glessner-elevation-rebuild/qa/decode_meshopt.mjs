// Losslessly decode EXT_meshopt_compression only. Quantized values, accessors,
// node transforms, images and materials remain exactly as shipped.
import fs from 'node:fs';
import { MeshoptDecoder } from '/workspace/scratch/61c0efdafb0a/chicago/chicago/4d/renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js';
await MeshoptDecoder.ready;
const [input,output]=process.argv.slice(2);
const file=fs.readFileSync(input); const jsonLength=file.readUInt32LE(12);
const doc=JSON.parse(file.subarray(20,20+jsonLength));
const bin=file.subarray(28+jsonLength);
const chunks=[];let total=0,decoded=0;
for(const view of doc.bufferViews){
 const ext=view.extensions?.EXT_meshopt_compression;
 let bytes;
 if(ext){bytes=Buffer.alloc(ext.count*ext.byteStride);MeshoptDecoder.decodeGltfBuffer(bytes,ext.count,ext.byteStride,bin.subarray(ext.byteOffset,ext.byteOffset+ext.byteLength),ext.mode,ext.filter);decoded++;delete view.extensions.EXT_meshopt_compression;if(!Object.keys(view.extensions).length)delete view.extensions;}
 else bytes=bin.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
 view.buffer=0;view.byteOffset=total;view.byteLength=bytes.length;
 chunks.push(bytes);total+=bytes.length;const pad=(4-total%4)%4;if(pad){chunks.push(Buffer.alloc(pad));total+=pad;}
}
doc.buffers=[{byteLength:total}];
for(const k of ['extensionsUsed','extensionsRequired'])if(doc[k])doc[k]=doc[k].filter(x=>x!=='EXT_meshopt_compression');
const raw=Buffer.from(JSON.stringify(doc));const j=Buffer.concat([raw,Buffer.alloc((4-raw.length%4)%4,32)]);
const b=Buffer.concat(chunks);const h=Buffer.alloc(20);h.writeUInt32LE(0x46546c67,0);h.writeUInt32LE(2,4);h.writeUInt32LE(28+j.length+b.length,8);h.writeUInt32LE(j.length,12);h.writeUInt32LE(0x4e4f534a,16);const bh=Buffer.alloc(8);bh.writeUInt32LE(b.length,0);bh.writeUInt32LE(0x004e4942,4);fs.writeFileSync(output,Buffer.concat([h,j,bh,b]));
console.log(JSON.stringify({input,output,decodedBufferViews:decoded,bytes:28+j.length+b.length}));
