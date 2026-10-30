// SPDX-License-Identifier: GPL-3.0-or-later
// Execute the native clock declarations/call and actual route method, not a copy.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const main = await readFile(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
const engine = await readFile(new URL('../renderers/web/js/humans.js', import.meta.url), 'utf8');
const clock = main.match(/const elapsed = Math\.min\(clock\.getDelta\(\), 0\.25\);\s*const frameDt =[^;]+;\s*const dt =[^;]+;/)?.[0];
const call = main.match(/api\.humans\?\.update\([^;]+;/g)?.find(s => s.includes('walker.state'));
assert(clock && call, 'Native tick clock and human update call must resolve');
const advance = new Function('clock', 'animationHold', 'gateOpen', 'api', 'camera', 'walker', `${clock}\n${call}`);
function time(deltas, held=false, gated=false) {
  let elapsed = 0, ticks = 0;
  const camera = {}, state = {};
  for (const delta of deltas) advance({getDelta:()=>delta}, held, gated,
    {humans:{update(dt, c, s){assert.strictEqual(c,camera);assert.strictEqual(s,state);elapsed+=dt;ticks++;}}}, camera, {state});
  return {elapsed,ticks};
}
assert(Math.abs(time(Array(4).fill(.25)).elapsed-1)<1e-12, 'Four slow frames must advance one second');
assert(Math.abs(time(Array(60).fill(1/60)).elapsed-1)<1e-12, 'Fast/slow native animation wall time must match');
assert.equal(time([1]).elapsed,.25, 'Long background pauses retain the native quarter-second safety clamp');
assert.equal(time([.2,.2],true).elapsed,0, 'Capture hold must stop human animation');
assert.equal(time([.2,.2],false,true).elapsed,0, 'Arrival gate must stop human animation');
advance({getDelta:()=>.2},false,false,{}, {},{state:{}}); // Absent layer is a normal year/scene case.

const source = engine.match(/\n  walk\(dt\) \{([\s\S]*?)\n  \}\n\n  \/\*\*/)?.[1];
assert(source, 'Actual HumanActor route method must resolve');
const walk = new Function('dt', 'findClip', source);
const actor = {state:'walking',route:[{local_e:0,local_n:0},{local_e:.2,local_n:0},{local_e:.2,local_n:.2}],
  body:{clips:new Map()},walkSpeed:1,leg:0,legT:0,e:0,n:0,placements:0,place(){this.placements++;}};
walk.call(actor,.25,()=>null);
assert.equal(actor.leg,1, 'Slow native frame must consume a route corner without losing elapsed time');
assert(Math.abs(actor.e-.2)<1e-12 && Math.abs(actor.n-.05)<1e-12);
actor.state='standing'; const before={e:actor.e,n:actor.n,leg:actor.leg,placements:actor.placements};
walk.call(actor,.25,()=>null);
assert.deepEqual({e:actor.e,n:actor.n,leg:actor.leg,placements:actor.placements},before, 'Standing actors must remain planted');
console.log('PASS: actual human frame clock consumes slow/fast elapsed time, holds, absent layers and route transitions');
