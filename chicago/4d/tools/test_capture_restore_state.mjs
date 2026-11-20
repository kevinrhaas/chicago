// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('./smoke_renderer.mjs',import.meta.url),'utf8');
const start=source.indexOf('async function captureWithRestoreState(');
const end=source.indexOf('// The gate is both viewports',start);
assert.ok(start>=0&&end>start,'exercise the actual capture helper');
const helper=source.slice(start,end);
const pending={inFlight:true,landings:30,drained:30,abandoned:6,passes:{near:22,far:22},version:1};
const landed={inFlight:false,landings:32,drained:32,abandoned:6,passes:{near:23,far:23},version:2};

function harness(states,{stalled=false,humans}={}){
  let at=-1,captures=0,current=states[0];
  const geometry={id:1,drawRange:{start:0,count:3},index:{version:0},attributes:{position:{count:3,version:0}}};
  const mesh={id:2,isMesh:true,visible:true,layers:{mask:1},geometry};
  const array=values=>({toArray:()=>[...values]});
  const api={camera:{position:array([122.5,2.555,100]),quaternion:array([0,0,0,1]),projectionMatrix:array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])},scene3d:{traverse(fn){geometry.attributes.position.version=current.version;fn(mesh);}},flora:{inFlight:()=>current.inFlight,stats:{}},textureResidency:{state:{pending:0,resident:0,residentBytes:0,uploads:0,evictions:0,redecodes:0}},capture:async grid=>{captures++;assert.equal(grid,12);return{signature:[42],mean:42};},humans};
  Object.defineProperty(api.flora.stats,'spread',{get:()=>current});
  const context=vm.createContext({window:{__chicago4d:api},setTimeout:stalled?callback=>{queueMicrotask(callback);return 1;}:setTimeout,clearTimeout:stalled?()=>{}:clearTimeout,requestAnimationFrame:callback=>{if(stalled)return;at++;current=states[Math.min(at,states.length-1)];queueMicrotask(callback);}});
  vm.runInContext(helper,context);
  // Playwright's page.evaluate always answers with a promise, whatever the function returns.
  const page={evaluate:async(fn,arg)=>fn(arg)};
  return{run:when=>context.captureWithRestoreState(page,12,when),get captures(){return captures;},get frames(){return at+1;}};
}

const normal=harness([pending,pending,landed]);
const result=await normal.run('before');
assert.equal(normal.captures,1);
assert.equal(normal.frames,6,'capture must wait for pending work plus four complete unchanged observations');
assert.equal(result.settle.stable_samples,4);
assert.equal(result.state.flora.inFlight,false);
assert.equal(result.state.flora.landings,32);

const late=harness([landed,landed,pending,landed]);
await late.run('before');assert.equal(late.frames,7,'late work restarts stability');
const never=harness([pending]);
await assert.rejects(never.run('before'),/120 animation-frame observations/);
assert.equal(never.captures,0,'failed readiness must not capture or silently retry');
const stopped=harness([pending],{stalled:true});
await assert.rejects(stopped.run('before'),/within 60s/);
assert.equal(stopped.captures,0,'wall deadline must reject even when no frame arrives');
const after=harness([pending]);
const restored=await after.run('after');
assert.equal(after.frames,0,'the restored image must remain an honest immediate comparison');
assert.equal(after.captures,1);assert.equal(restored.settle,null);

// T-3630: the baseline holds the people out of frame (hidden layer, held update) instead of
// waiting on a figure's level; the restored capture leaves that hold to the pair's own let-go.
const live=()=>'live';
const people={group:{visible:true},update:live,actors:[{pending:true},{pending:false}]};
const held=harness([landed],{humans:people});
const heldResult=await held.run('before');
assert.equal(people.group.visible,false,'the baseline draws no figure');
assert.notEqual(people.update,live,'no level is asked for or let go while the pair is held');
assert.equal(people.heldByPair,live);assert.equal(people.hiddenByPair,true);
assert.equal(heldResult.state.humans,1,'the receipt counts the figures still loading, without waiting on them');
await held.run('after');
assert.equal(people.group.visible,false,'the restored frame keeps the hold the baseline took');
assert.equal(people.heldByPair,live,'a second capture does not stack the hold');
console.log('PASS actual capture helper: observed pending/landing states, four quiet observations, late-work reset, frame/wall deadlines and unchanged restoration capture; people held out of the baseline, not waited on; no browser/pixel acceptance');
