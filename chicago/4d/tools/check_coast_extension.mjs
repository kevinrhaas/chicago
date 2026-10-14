#!/usr/bin/env node
/** T-2495: runtime sampling and GLB geometry agree, including both seams. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { contextSample } from '../renderers/web/js/coast-extension.js';
const dir = new URL('../data/terrain/epochs/e1871_postfire/', import.meta.url);
const read = n => JSON.parse(fs.readFileSync(new URL(n,dir),'utf8'));
const m=read('heightfield.json'), coast=read('context.json');
const bytes=fs.readFileSync(new URL('heightfield.bin',dir));
const raw=new Int16Array(bytes.buffer,bytes.byteOffset,bytes.length/2);
const sample=(e,n)=>{
  const x=Math.max(0,Math.min(m.cols-1,(e-m.origin_e)/m.cell_m));
  const y=Math.max(0,Math.min(m.rows-1,(n-m.origin_n)/m.cell_m));
  const c=Math.min(Math.floor(x),m.cols-2),r=Math.min(Math.floor(y),m.rows-2),u=x-c,v=y-r;
  const at=(c,r)=>raw[r*m.cols+c]*m.scale+m.offset;
  return (at(c,r)*(1-u)+at(c+1,r)*u)*(1-v)+(at(c,r+1)*(1-u)+at(c+1,r+1)*u)*v;
};
const hf={originE:m.origin_e,originN:m.origin_n,widthM:(m.cols-1)*m.cell_m,depthM:(m.rows-1)*m.cell_m,contextCoast:coast};
const glb=fs.readFileSync(new URL('context_ground.glb',dir));
const len=glb.readUInt32LE(12),doc=JSON.parse(glb.subarray(20,20+len).toString());
const ac=doc.accessors[0],bv=doc.bufferViews[ac.bufferView],start=28+len+(bv.byteOffset||0)+(ac.byteOffset||0);
let worst=0;
for(let i=0;i<ac.count;i++){
 const e=glb.readFloatLE(start+i*12),y=glb.readFloatLE(start+i*12+4),n=-glb.readFloatLE(start+i*12+8);
 worst=Math.max(worst,Math.abs(contextSample(hf,e,n,sample)-y));
}
assert(worst<0.003,`apron/sampler departure ${worst} m`);
for(const side of ['north','south']){
 const n=coast[side].join_n;
 for(let e=hf.originE;e<=hf.originE+hf.widthM;e+=2.5){
  assert(Math.abs(contextSample(hf,e,n,sample)-sample(e,n))<1e-8,'join moved');
 }
 // Confirm the new coast is actually used: the old straight extrusion is different.
 const p=coast[side].shoreline_local_m.find(p=>Math.abs(p[1]-n)>1000);
 assert(p && Math.abs(p[0]-coast[side].join_shore_e)>50,'coast stayed straight');
 assert(contextSample(hf,p[0]+20,p[1],sample)<0,'lake is land');
 assert(contextSample(hf,p[0]-20,p[1],sample)>1,'land is lake');
}
console.log(`OK 1904 coast runtime: ${ac.count} apron vertices, worst sampler error ${(worst*1000).toFixed(2)} mm; both seams and land/water sides hold`);
