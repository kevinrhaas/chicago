// SPDX-License-Identifier: GPL-3.0-or-later
// Cheap gate controls; --acquisition is one separately admitted REAL GitHub
// blobless acquisition test, never an automatic per-commit network loop.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import zlib from 'node:zlib';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {ensureParents,trustedPromisor} from './check_human_charles_coat.mjs';
const APP=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const recipeRaw=fs.readFileSync(path.join(APP,'data/humans/materials/charles-coat-woven-v1.json'));
const recipe=JSON.parse(recipeRaw),rows=recipe.parents.filter(r=>r.lod<2&&!r.file.includes('/web/'));
const acquisition=process.argv[2]==='--acquisition';assert(process.argv.length===2||process.argv.length===3&&['--check','--acquisition'].includes(process.argv[2]));
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'charles-parent-inputs-'));
const env={...process.env,GIT_NO_LAZY_FETCH:'1'};
for(const key of ['GIT_DIR','GIT_WORK_TREE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_INDEX_FILE'])delete env[key];
function run(args,{network=false,timeout=10000,okay=true}={}){
  const actual={...env};if(network)delete actual.GIT_NO_LAZY_FETCH;
  const r=spawnSync('git',args,{cwd:temp,env:actual,timeout,maxBuffer:1<<20});if(okay)assert(!r.error&&r.status===0,`bounded fixture Git operation failed (${r.status??r.error?.code})`);return r;
}
let controls=0;
try{
  run(['init','-q']);assert(!fs.existsSync(path.join(temp,'.git/objects/info/alternates')));controls++;
  assert.throws(()=>ensureParents({root:temp,recipeRaw,acquire:false}));controls++;
  const bad=Buffer.from(recipeRaw);bad[0]=32;assert.throws(()=>ensureParents({root:temp,recipeRaw:bad,acquire:true}));controls++;
  run(['remote','add','origin','https://example.invalid/untrusted.git']);assert.throws(()=>trustedPromisor(temp));controls++;
  run(['remote','set-url','origin','https://github.com/kevinrhaas/chicago.git']);
  assert.throws(()=>trustedPromisor(temp));controls++;
  run(['config','remote.origin.promisor','true']);run(['config','remote.origin.partialclonefilter','blob:none']);trustedPromisor(temp);controls++;
  run(['config','remote.other.promisor','true']);assert.throws(()=>trustedPromisor(temp));controls++;
  run(['config','--remove-section','remote.other']);
  if(acquisition){
    // No checkout, no alternates, no shared Git object database. Fetch exactly
    // the declared tree metadata; the subsequent two real object requests are
    // made by the SAME reviewed helper used in blobless CI.
    run(['-c','protocol.version=2','fetch','--no-tags','--depth=1','--filter=blob:none','origin',recipe.parent_revision],{network:true,timeout:60000});
    assert(!fs.existsSync(path.join(temp,'.git/objects/info/alternates')));
    const packDirectory=path.join(temp,'.git/objects/pack');
    const metadataPacks=new Set(fs.readdirSync(packDirectory));
    for(const row of rows)assert.notEqual(run(['cat-file','-e',row.gitBlob],{okay:false}).status,0,'actual parent object absent before acquisition');controls++;
    assert.throws(()=>ensureParents({root:temp,recipeRaw,acquire:false}));controls++;
    const fetched=ensureParents({root:temp,recipeRaw,acquire:true});assert.equal(fetched.acquired,2);controls++;
    const cached=ensureParents({root:temp,recipeRaw,acquire:false});assert.equal(cached.acquired,0);controls++;
    // Remove only packs added by the two exact-object acquisitions in this
    // disposable fixture. Git may prefer a good packed object to a corrupt
    // loose shadow, so first prove the original is actually absent, then prove
    // Git actually reads the bad bytes before asking our independent check.
    const row=rows[0],loose=path.join(temp,'.git/objects',row.gitBlob.slice(0,2),row.gitBlob.slice(2));
    for(const name of fs.readdirSync(packDirectory))if(!metadataPacks.has(name))fs.unlinkSync(path.join(packDirectory,name));
    assert.notEqual(run(['cat-file','-e',row.gitBlob],{okay:false}).status,0);
    fs.mkdirSync(path.dirname(loose),{recursive:true});assert(!fs.existsSync(loose));
    fs.writeFileSync(loose,zlib.deflateSync(Buffer.from('blob 3\0bad')));
    assert.equal(run(['cat-file','blob',row.gitBlob]).stdout.toString(),'bad');
    assert.throws(()=>ensureParents({root:temp,recipeRaw,acquire:false}));fs.unlinkSync(loose);controls++;
    assert(!fs.existsSync(path.join(temp,'assets')));controls++;
    console.log(JSON.stringify({status:'ACTUAL_FRESH_BLOBLESS_ACQUISITION_AND_CACHED_OFFLINE_CONTROLS_PASS',controls,objects:fetched.objects,acquired:2,alternates:false,checkout:false,active_writes:0}));
  }else console.log(JSON.stringify({status:'OFFLINE_RECIPE_TREE_AND_TRUST_POLICY_CONTROLS_PASS',controls,network:false,active_writes:0}));
}finally{fs.rmSync(temp,{recursive:true,force:true});}
