// SPDX-License-Identifier: GPL-3.0-or-later
// Execute native scheduler/ownership functions; deterministic producer rows expose cancellation.
// This tests commits and retained reach, not real-world frame time or plant-buffer equivalence.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const s=fs.readFileSync(root+'renderers/web/js/flora.js','utf8');
const fixedGuard='if (f.spread && costly && (f.pace > p.reach || f.turnRate > CONE_YAW_STEP)) {';
const oldGuard='if (f.spread && costly) {';
assert.equal(s.split(fixedGuard).length,2,'One native bounded steady-travel guard');
const candidate=s.slice(s.indexOf('  const nearPass ='),s.indexOf('  const api = {',s.indexOf('  const nearPass =')));
const block=candidate.replace(fixedGuard,oldGuard); // Original defect is a required negative control.
assert.notEqual(block,candidate);
const movedSource=s.match(/function moved\([^]*?\n\}/)[0];
const yawSource=s.match(/function yawGap\([^]*?\n\}/)[0];
function rig(src){
 const setup=`let now=0;const performance={now:()=>now};let committed=0,farCommitted=0;
 const stats={rebuilds:0};const step=.6,tune={farShrub:{step:4}};
 const centres={near:{e:0,n:0},yaw:0,farShrub:{e:0,n:0},farShrubYaw:0};
 const CONE_YAW_STEP=.2,SPREAD_MAX_MS=250,JUMP_FRAMES=6,JUMP_SLICE_MS=30;
 const MAY_WAIT=Symbol('may wait'),DRAIN=Symbol('drain'),WALK_WAIT={waiting:true};
 const carryEvents=[];const gpuNear={carryDropped(){carryEvents.push({kind:'drop'});},carryOwned(entry){carryEvents.push({kind:'owned',pass:entry.pass,onGpu:entry.onGpu});}},groundKey=null,groundWorker=null,dealtOnGpu={near:false,far:false};
 const tmpQ={toArray:()=>[0,0,0,1]},tmpV={x:0,y:1,z:0};
 const jobsOnWorkers=()=>false;
 function* rebuildAll(){now+=5;yield{row:1};now+=5;yield{row:2};committed++;}
 function* rebuildFarShrubs(){now+=5;yield{row:1};now+=5;yield{row:2};farCommitted++;}
 `;
 return new Function(setup+movedSource+yawSource+src+`;
 nearPass.cost=farPass.cost=8;
 const makeFrame=(e,pace,turnRate,spread,budgetMs,yaw)=>({e,n:0,yaw,cone:{},pace,turnRate,budgetMs,dealt:0,spread,camera:{getWorldQuaternion(){}}});
 const due=(p,f)=>moved(centres[p.at],f.e,0,p.reach,f.pace)||yawGap(f.yaw,centres[p.yawAt])>CONE_YAW_STEP;
 return{stats,nearPass,farPass,centres,carryEvents,committed:()=>committed,farCommitted:()=>farCommitted,
 frame(e,pace,turnRate=0,spread=true,nativeDue=false,budgetMs=4,yaw=turnRate){tmpV.x=e;const f=makeFrame(e,pace,turnRate,spread,budgetMs,yaw);return runPass(nearPass,f,nativeDue ? due(nearPass,f) : true);},
 farFrame(e,pace){tmpV.x=e;const f=makeFrame(e,pace,0,true,4,0);return runPass(farPass,f,due(farPass,f));},
 pair(e,pace){tmpV.x=e;const f=makeFrame(e,pace,0,true,4,0);const far=runPass(farPass,f,due(farPass,f));const afterFar=f.dealt;const near=runPass(nearPass,f,due(nearPass,f));return{afterFar,total:f.dealt,far,near};}};`)();
}
const results={source_sha256:createHash('sha256').update(s).digest('hex'),actual_block_sha256:createHash('sha256').update(block).digest('hex'),candidate_block_sha256:createHash('sha256').update(candidate).digest('hex'),fixture:'Actual native runPass/begin/advance/drop/land/log functions; deterministic5ms producer rows,8ms priorcost,4ms budget, real continuous0.2m/frame,near reach0.6; no fake last mutation.'};
for(const [name,code]of[['original',block],['candidate',candidate]]){
 const r=rig(code);for(let i=1;i<=20;i++)r.frame(i*.2,.2);results[name]={passes:r.stats.spread.passes.near,dropped:r.stats.spread.abandoned,jumps:r.stats.spread.jumps,committed:r.committed(),shownCentre:r.centres.near.e,pending:!!r.nearPass.pending};
}
assert.equal(results.original.passes,0);assert.equal(results.original.dropped,19);assert.equal(results.original.jumps,20);assert.equal(results.original.committed,0);
assert.equal(results.candidate.passes,20);assert.equal(results.candidate.dropped,0);assert.equal(results.candidate.shownCentre,4);
// Repeat with the ACTUAL native moved() due predicate and require every shown lattice to stay within its reach.
results.nativeDue={};
for(const [name,code]of[['original',block],['candidate',candidate]]) {
 const r=rig(code);let worstStaleness=0;
 for(let i=1;i<=100;i++){const e=i*.2;r.frame(e,.2,0,true,true);worstStaleness=Math.max(worstStaleness,e-r.centres.near.e);}
 results.nativeDue[name]={committed:r.committed(),dropped:r.stats.spread.abandoned,jumps:r.stats.spread.jumps,worstStaleness,pending:!!r.nearPass.pending};
}
assert.equal(results.nativeDue.original.committed,0);assert(results.nativeDue.original.worstStaleness>.6);
assert(results.nativeDue.candidate.committed>0);assert.equal(results.nativeDue.candidate.dropped,0);assert(results.nativeDue.candidate.worstStaleness<=.6);
// The native command chooses horse and advances1/60s; read its real default speed.
const {PACES}=await import('file://'+root+'renderers/web/js/travel-settings.js');
const nativeTool=fs.readFileSync(root+'tools/measure_walk_frames.mjs','utf8');
assert(nativeTool.includes("a.setTravelMode('horse')"));assert(nativeTool.includes('a.travelSimulate(1 / 60, 1 / 60)'));
const actualPace=PACES.horse.defaultSpeed/60;assert(actualPace<.6 && actualPace*4>.6/2);
results.actualNativeHorse={speed_m_s:PACES.horse.defaultSpeed,frame_s:1/60,pace_m:actualPace,near_reach:.6,smooth:false};
for(const [label,pace]of[['actualHorse60fps',actualPace],['steadyHorse20fps',PACES.horse.defaultSpeed/20]]) {
 results[label]={};
 for(const [name,code]of[['original',block],['candidate',candidate]]) {
  const r=rig(code);let maxGap=0;
  for(let i=1;i<=40;i++){const e=i*pace;r.frame(e,pace,0,true,true);maxGap=Math.max(maxGap,e-r.centres.near.e);}
  results[label][name]={commits:r.committed(),dropped:r.stats.spread.abandoned,jumps:r.stats.spread.jumps,maxGap};
 }
 assert.equal(results[label].original.commits,0);assert(results[label].candidate.commits>0);assert.equal(results[label].candidate.dropped,0);assert(results[label].candidate.maxGap<=.6);
}
// At15fps the default horse moves more than reach in one frame; candidate intentionally preserves the original jump classification.
const low=PACES.horse.defaultSpeed/15;
const lowOld=rig(block),lowNext=rig(candidate);lowOld.frame(low,low);lowNext.frame(low,low);assert.equal(lowOld.stats.spread.jumps,1);assert.equal(lowNext.stats.spread.jumps,1);
results.lowFPSLimit={fps:15,pace_m:low,reach_m:.6,originalJump:1,candidateJump:1,scope:'Larger-than-reach sustained motion retains existing behavior; no new complete lowFPS claim.'};
// A cheap<=budget producer still uses the original one-frame path without creating jumps.
for(const src of[block,candidate]){const r=rig(src);r.nearPass.cost=3;r.frame(.2,.2);assert.equal(r.committed(),1);assert.equal(r.stats.spread.jumps,0);}
// Real arrival and snap turns keep the existing bounded-jump path.
for(const [label,pace,turn]of[['teleport',2,0],['snapTurn',0,1]]){
 const old=rig(block),next=rig(candidate);old.frame(2,pace,turn);next.frame(2,pace,turn);assert.equal(old.stats.spread.jumps,1);assert.equal(next.stats.spread.jumps,1);assert.equal(old.committed(),next.committed());results[label]={originalJump:old.stats.spread.jumps,candidateJump:next.stats.spread.jumps};
}
// Caller demanding immediate buffers preserves exact synchronous completion.
for(const src of[block,candidate]){const r=rig(src);r.frame(1,.2,0,false,false,Infinity);assert.equal(r.committed(),1);assert.equal(r.stats.spread.passes.near,1);}
// Cumulative turns include yaw wrap and retain real native yawGap.
results.steadyTurns=[];
for(const rate of[.03,.1,.2]){
 const old=rig(block),next=rig(candidate);let maxCandidateYawGap=0;
 for(let i=1;i<=80;i++){const yaw=(i*rate+Math.PI)%(2*Math.PI)-Math.PI;old.frame(0,0,rate,true,true,4,yaw);next.frame(0,0,rate,true,true,4,yaw);const gap=Math.abs(((yaw-next.centres.yaw+Math.PI*3)%(Math.PI*2))-Math.PI);maxCandidateYawGap=Math.max(maxCandidateYawGap,gap);}
 assert.equal(old.committed(),0);assert(next.committed()>0);assert.equal(next.stats.spread.abandoned,0);assert(maxCandidateYawGap<=.2+1e-12);
 results.steadyTurns.push({rate,originalCommits:old.committed(),candidateCommits:next.committed(),maxCandidateYawGap});
}
// A pending jump or ordinary spread is retired by the actual native ownership path before steady immediate work.
results.pendingTransitions=[];
for(const ordinary of[false,true]){
 const r=rig(candidate);r.frame(ordinary?.55:2,ordinary?.01:2,0,true,true);assert(r.nearPass.pending);assert.equal(!!r.nearPass.pending.jump,!ordinary);
 r.frame(ordinary?.75:2.2,.2,0,true,true);assert.equal(r.stats.spread.abandoned,1);assert.equal(r.committed(),1);assert.equal(r.nearPass.pending,null);
 results.pendingTransitions.push({from:ordinary?'ordinarySpread':'realJump',drops:1,completedCurrent:1});
}
// Near and far consume the same frame.dealt accumulator, as native update does (far first).
for(const src of[block,candidate]){const r=rig(src);for(let i=1;i<=100;i++){const f=r.pair(i*.2,.2);assert(f.total>=f.afterFar && f.afterFar>=0);}assert(r.farCommitted()>0);}
// Explicit still-unfixed larger-than-reach lowFPS steady travel.
for(const src of[block,candidate]){const r=rig(src);for(let i=1;i<=20;i++)r.frame(i*1.2,1.2,0,true,true);assert.equal(r.committed(),0);assert(r.stats.spread.abandoned>0);}
results.lowFPSCounterexample={speed_m_s:12,frame_s:.1,pace_m:1.2,originalCommits:0,candidateCommits:0,retainedLimitation:true};
// Far cancellation and new commit keep the native carry ownership callbacks in order.
{const r=rig(candidate);r.farFrame(5,5);assert(r.farPass.pending?.jump);r.farFrame(5.8,.8);
 assert.equal(r.farCommitted(),1);assert.equal(r.farPass.pending,null);
 assert.deepEqual(r.carryEvents,[{kind:'drop'},{kind:'owned',pass:1,onGpu:false}]);}
results.limits=['This proves the native continuous-motion cancellation loop; it does not prove this caused original33.2ms frame or that the candidate improves realworld performance.','Only5ms producer-row fixture: cannot substitute for actual CPUfallback/plant-buffer validation, moving clocks or currentCI.','Candidate condition is outsideapp exploratory source only; no app patch, cap/assertion change or browser execution.'];
console.log('PASS: native flora commits continuous subreach horseback travel and turns; original defect is rejected; jump, pending ownership, carry, cheap-budget and Infinity-reader controls hold. Larger-than-reach low-FPS behavior remains unchanged.');
