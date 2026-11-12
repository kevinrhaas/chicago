// SPDX-License-Identifier: GPL-3.0-or-later
// Serial input bootstrap + unchanged independent registration check. The pool
// must not race a separate acquisition step against the actual owner check.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const APP=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const REF='fc5a52b6cab3eed78e2db5864aa811dff5df2795';
const RECIPE_SHA='2b604e409564a0340c497bd158307a22620aad3efaa542aecff55a2e0d8dc4d3';
const hash=(kind,raw)=>crypto.createHash(kind).update(raw).digest('hex');
const noFetch=()=>({...process.env,GIT_NO_LAZY_FETCH:'1'});
function git(root,args,{network=false,bytes=1<<20,timeout=10000}={}){
  const env=noFetch();if(network)delete env.GIT_NO_LAZY_FETCH;
  const result=spawnSync('git',args,{cwd:root,env,maxBuffer:bytes,timeout});
  assert(!result.error&&result.status===0,`bounded Git input operation failed (${result.status??result.error?.code}); no active asset was written`);
  return result.stdout;
}
export function trustedPromisor(root){
  const origin=git(root,['config','--get','remote.origin.url']).toString().trim();
  assert(/^(https:\/\/github\.com\/kevinrhaas\/chicago(?:\.git)?|git@github\.com:kevinrhaas\/chicago(?:\.git)?)$/.test(origin),'origin must be the declared Chicago repository');
  assert.equal(git(root,['config','--get','remote.origin.promisor']).toString().trim(),'true');
  assert.equal(git(root,['config','--get','remote.origin.partialclonefilter']).toString().trim(),'blob:none');
  const promises=git(root,['config','--get-regexp','^remote\\..*\\.promisor$']).toString().trim().split('\n');
  assert(promises.every(line=>line==='remote.origin.promisor true'),'no alternate promisor network fallback');
}
export function ensureParents({root,recipeRaw,acquire=false}){
  assert.equal(hash('sha256',recipeRaw),RECIPE_SHA,'exact reviewed recipe before any Git/network operation');
  const recipe=JSON.parse(recipeRaw);assert.equal(recipe.parent_revision,REF);
  const rows=recipe.parents.filter(r=>r.lod<2&&!r.file.includes('/web/'));
  assert.deepEqual(rows.map(r=>r.file),[0,1].map(lod=>`assets/humans/nelson_charles_1904_coachman.lod${lod}.glb`));
  const tree=git(root,['ls-tree',REF,'--',...rows.map(r=>'chicago/4d/'+r.file)]).toString().trim().split('\n');
  const actual=new Map(tree.map(line=>{const [meta,file]=line.split('\t');return[file,meta.split(/\s+/)[2]];}));
  assert.equal(actual.size,2,'the full immutable tree must exist before acquisition');
  for(const row of rows)assert.equal(actual.get('chicago/4d/'+row.file),row.gitBlob,'fixed object/tree membership');
  let acquired=0;const verified=[];
  for(const row of rows){
    assert(/^[a-f0-9]{40}$/.test(row.gitBlob)&&/^[a-f0-9]{64}$/.test(row.sha256)&&row.bytes>0&&row.bytes<=16*1024**2);
    const exists=spawnSync('git',['cat-file','-e',row.gitBlob],{cwd:root,env:noFetch(),timeout:10000,maxBuffer:1<<20});
    const missing=exists.error||exists.status!==0;
    if(missing){
      assert(acquire,'reviewed parent missing offline; explicit --acquire-reviewed-parents is required');
      // Only the declared GitHub repository's existing origin promisor is a
      // source. No arbitrary URL, alternate remote or revision fallback.
      trustedPromisor(root);
    }
    // Git's promisor protocol requests this ONE exact object ID. A network
    // miss is bounded to20s/object; successful contents must match BOTH hashes
    // and exact bytes. Existing cache reads always disable lazy fetching.
    const raw=git(root,['cat-file','blob',row.gitBlob],{network:Boolean(missing),bytes:16*1024**2,timeout:missing?20000:10000});
    assert.equal(raw.length,row.bytes);assert.equal(hash('sha256',raw),row.sha256);
    assert.equal(hash('sha1',Buffer.concat([Buffer.from(`blob ${raw.length}\0`),raw])),row.gitBlob);
    acquired+=missing?1:0;verified.push({file:row.file,gitBlob:row.gitBlob,sha256:row.sha256,bytes:raw.length});
  }
  return {immutable_parent_ref:REF,verified_MASTER_objects:2,acquired,objects:verified,active_writes:0};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const args=process.argv.slice(2),acquire=args[0]==='--acquire-reviewed-parents';if(acquire)args.shift();
  // Spell the actual fixed owner command in check.sh as well as running it, so
  // the existing derivation/writer coverage audit can see the real --check.
  const owner=['--','python3','tools/human_charles_coat.py','--check'];
  const then=['--then','python3','tools/test_human_charles_coat_regeneration.py'];
  const controls=args.length>owner.length;
  assert.deepEqual(args,controls?[...owner,...then]:owner,'only the fixed owner and optional real-parent controls may follow bootstrap');
  console.log(JSON.stringify(ensureParents({root:path.resolve(APP,'../..'),recipeRaw:fs.readFileSync(path.join(APP,'data/humans/materials/charles-coat-woven-v1.json')),acquire})));
  for(const command of [owner.slice(1),...(controls?[then.slice(1)]:[])]){
    const child=spawnSync(command[0],command.slice(1),{cwd:APP,env:noFetch(),stdio:'inherit',timeout:60000});
    assert(!child.error&&child.status===0,'independent owner or real-parent control failed after input bootstrap');
  }
}
