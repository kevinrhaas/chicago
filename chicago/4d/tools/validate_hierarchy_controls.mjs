#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
// Concise actual validator issue pointers; no asset bytes emitted.
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
const validator=createRequire(import.meta.url)('gltf-validator'),args=process.argv.slice(2);
if(!args.length||args.length%2)throw Error('usage: validate_hierarchy_controls.mjs CONTROL ROOT [CONTROL ROOT ...]');
let failed=false;
for(let k=0;k<args.length;k+=2)for(const [offset,kind]of [[0,'parented_control'],[1,'root_mesh']]){
 const file=args[k+offset],bytes=await readFile(file);const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString()),parents=new Map();
 for(let i=0;i<(doc.nodes??[]).length;i++)for(const child of doc.nodes[i].children??[]){if(parents.has(child))throw Error('ambiguous node parent');parents.set(child,i);}
 const result=await validator.validateBytes(new Uint8Array(bytes),{uri:file,maxIssues:10000});
 const issues=result.issues.messages.filter(m=>m.severity<=1).map(m=>{const match=/\/nodes\/(\d+)(?:\/|$)/.exec(m.pointer??''),index=match?Number(match[1]):null,node=index===null?null:doc.nodes[index];return{code:m.code,severity:m.severity,pointer:m.pointer,message:m.message,node_index:index,node_name:node?.name??null,mesh_index:node?.mesh??null,skin_index:node?.skin??null,parent_index:index===null?null:parents.get(index)??null};});
 const expected=issues.filter(i=>i.code==='NODE_SKINNED_MESH_NON_ROOT'&&i.severity===1);
 const passed=result.issues.numErrors===0&&!result.issues.truncated&&(kind==='parented_control'?expected.length>0&&issues.length===expected.length&&expected.every(i=>i.mesh_index!==null&&i.skin_index!==null&&i.parent_index!==null):issues.length===0);
 failed ||=!passed;
 console.log(JSON.stringify({scope:'actual supplied hierarchy control/root validator; paths and hashes identify input artifacts, no old CI artifact identity asserted',kind,file,sha256:createHash('sha256').update(bytes).digest('hex'),errors:result.issues.numErrors,warnings:result.issues.numWarnings,truncated:result.issues.truncated,issues,passed}));
}
if(failed)process.exitCode=1;
