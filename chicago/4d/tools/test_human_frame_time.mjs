// SPDX-License-Identifier: GPL-3.0-or-later
// Execute the native shared clock/latches, actor update and route; no browser or copied clock implementation.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const main = await readFile(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
const engine = await readFile(new URL('../renderers/web/js/humans.js', import.meta.url), 'utf8');
const standing = await readFile(new URL('../renderers/web/js/standing-horses.js', import.meta.url), 'utf8');
function required(match, label) { assert(match, `Actual native ${label} must resolve`); return match; }
const clockSource = required(main.match(/function tick\([^\n]*\) \{([\s\S]*?)\n    if \(!gateOpen\)/), 'tick clock')[1];
const call = required(main.match(/api\.humans\?\.update\([^;]+;/g)?.filter(s => s.includes('walker.state')), 'human update calls');
assert.equal(call.length, 1, 'One native human update per tick');
const horseCall = required(main.match(/standingHorses\.update\(camera, [^;]+;/), 'standing update')[0];
const latches = required(main.match(/  let visualClockReset = true;([\s\S]*?)\n  crashGuard\.watchContext/), 'visible clock event latches')[0].replace(/\n  crashGuard\.watchContext$/, '');
const hold = required(main.match(/    setAnimationHold\(on\) \{([\s\S]*?)\n    \},/), 'animation hold')[1];
const pause = required(main.match(/gateOpen = true;\s*visualClockReset = true;/), 'pause clock reset')[0];
const enter = required(main.match(/gateOpen = false;\s*visualClockReset = true;/), 'entry clock reset')[0];
function bus(extra = {}) {
  const handlers = new Map();
  return {...extra, addEventListener(name, fn) { const rows = handlers.get(name) ?? []; rows.push(fn); handlers.set(name, rows); },
    fire(name) { for (const fn of handlers.get(name) ?? []) fn(); }};
}
function clockHarness(absent = false) {
  const document = bus({hidden:false}), window = bus(), dom = bus(), loops = [], calls = [], horses = [];
  const camera = {}, state = {}, clock = {delta:0, reads:0, getDelta() { this.reads++; return this.delta; }};
  const api = absent ? {} : {humans:{update(dt, c, s, visualDt) { assert.strictEqual(c, camera); assert.strictEqual(s, state); calls.push({dt, visualDt}); }}};
  const standingHorses = {update(c, dt, options) { assert.strictEqual(c,camera); horses.push({dt,...options}); }};
  const factory = new Function('document','window','renderer','clock','api','camera','walker','standingHorses', `
    let animationHold = false, gateOpen = false, contextPaused = false;
    const frameLoop = () => {}, contextNeedsReload = () => false;
    ${latches}
    return {
      tick() { ${clockSource}\n${call[0]}\n${horseCall}\nreturn {frameDt, dt, visualDt}; },
      hold(on) { ${hold} }, pause() { ${pause} }, enter() { ${enter} },
      state() { return {visualClockReset,contextPaused}; }
    };`);
  const native = factory(document,window,{domElement:dom,setAnimationLoop(fn) { loops.push(fn); }},clock,api,camera,{state},standingHorses);
  return {document,window,dom,calls,horses,loops,...native,tick(delta) { clock.delta = delta; const before = clock.reads; const row = native.tick(); assert.equal(clock.reads-before,1,'Consume the native clock once per tick'); return row; }};
}
function total(deltas, held = false, gated = false) {
  const h = clockHarness(); if (held) h.hold(true); if (gated) h.pause();
  let elapsed = 0; for (const delta of deltas) elapsed += h.tick(delta).frameDt;
  return elapsed;
}
// Original bounded locomotion/hold assertions remain; cosmetic idle is a separate fourth argument.
assert(Math.abs(total(Array(4).fill(.25))-1)<1e-12, 'Four slow frames must advance one second');
assert(Math.abs(total(Array(60).fill(1/60))-1)<1e-12, 'Fast/slow native locomotion time must match');
assert.equal(total([1]),.25,'Long pauses retain the quarter-second locomotion clamp');
assert.equal(total([.2,.2],true),0,'Capture hold stops human locomotion');
assert.equal(total([.2,.2],false,true),0,'Arrival gate stops human locomotion');
clockHarness(true).tick(.2); // An absent human layer is a normal year/scene case.
const h = clockHarness();
assert.equal(h.tick(25).visualDt,0,'First real frame cannot consume unseen visual time');
assert.deepEqual(h.tick(1.75),{frameDt:.25,dt:.05,visualDt:1.75},'Slow visible idle keeps wall time; locomotion/effects remain bounded');
assert.deepEqual(h.calls.at(-1),{dt:.25,visualDt:1.75},'Only the human fourth argument receives raw cosmetic time');
assert.deepEqual(h.horses.at(-1),{dt:1.75,paused:false,visualFrame:true},'Standing horse gets the same separate cosmetic time');
h.hold(true); assert.deepEqual(h.tick(.2),{frameDt:0,dt:0,visualDt:0});
h.hold(false); assert.equal(h.tick(20).visualDt,0,'Resuming a hold rejects its invisible interval');
assert.equal(h.tick(.2).visualDt,.2);
h.hold(true); h.hold(false); assert.equal(h.tick(20).visualDt,0,'Hold/resume also resets when no held tick occurred');
h.pause(); assert.equal(h.tick(.2).frameDt,0); h.enter(); assert.equal(h.tick(20).visualDt,0,'World entry resets the visual interval');
h.tick(.2); h.document.hidden = true; h.document.fire('visibilitychange'); assert.equal(h.tick(20).visualDt,0);
h.document.hidden = false; h.document.fire('visibilitychange'); assert.equal(h.tick(20).visualDt,0,'Shown page rejects hidden elapsed time');
h.tick(.2); h.document.hidden=true; h.document.fire('visibilitychange'); h.document.hidden=false; h.document.fire('visibilitychange');
assert.equal(h.tick(20).visualDt,0,'Hidden/shown without any hidden tick still rebases visual time');
for (const event of ['pageshow','pagehide']) { h.tick(.2); h.window.fire(event); assert.equal(h.tick(20).visualDt,0,`${event} rebases the first visual frame`); }
h.tick(.2); h.dom.fire('webglcontextlost'); assert.equal(h.state().visualClockReset,true); assert.equal(h.state().contextPaused,true); assert.equal(h.loops.at(-1),null);
h.tick(0); h.dom.fire('webglcontextrestored'); assert.equal(h.state().visualClockReset,true); assert.equal(h.state().contextPaused,false); assert.equal(typeof h.loops.at(-1),'function');
assert.equal(h.tick(20).visualDt,0,'Context restoration rejects the old document gap');
for (const invalid of [NaN,Infinity,-1]) assert.equal(h.tick(invalid).visualDt,0,'Invalid raw intervals never reach cosmetic helpers');

// Actual HumanActor update: substitute only its external scene/body collaborators.
const constants = required(engine.match(/export const HUMAN_TIERS[\s\S]*?export const RECHECK_S = [^;]+;/), 'human distance constants')[0].replace(/^export /gm,'');
const choose = required(engine.match(/export function chooseHumanLod\([\s\S]*?\n\}/), 'native human LOD selector')[0].replace(/^export /,'');
const update = required(engine.match(/\n  update\(dt, cameraPosition, visualDt = dt\) \{([\s\S]*?)\n  \}\n\n  dispose/), 'human update')[1];
const dispose = required(engine.match(/\n  dispose\(\) \{([\s\S]*?)\n  \}\n\}/), 'human disposal')[1];
const actorUpdate = new Function('dt','cameraPosition','visualDt = dt',`${constants}\n${choose}\n${update}`);
const actorDispose = new Function(dispose);
function body() { const values = []; return {values,faces:[{}],mixer:{update(dt) { values.push(dt); }}}; }
function actor() {
  const a = {disposed:false,recheck:0,inRange:true,tier:'full',lod:0,wanted:0,instance:{lod:{}},root:{position:{},visible:true,removeFromParent(){}},
    counters:{updates:0,animated:0,faced:0},body:body(),visualIdleBody:null,state:'standing',clipName:'idle_natural_v1',
    blinkClock:0,expression:{},walks:[],walk(dt) { this.walks.push(dt); },setLod(lod) { this.wanted=lod; return Promise.resolve(); },applyFace(){},applyCosts(){},teardown(){}};
  a.distanceForTest = 2;
  a.step = (dt, visualDt) => actorUpdate.call(a,dt,{distanceTo() { return a.distanceForTest; }},visualDt);
  return a;
}
const a = actor(); a.step(.05,50); assert.equal(a.body.values.at(-1),0,'New body starts without unseen animation');
a.step(.05,1.8); assert.equal(a.body.values.at(-1),1.8); assert.equal(a.walks.at(-1),.05); assert(Math.abs(a.blinkClock-.1)<1e-12,'Face and routes keep bounded dt');
for (const mode of [{state:'walking'},{state:'talking'},{state:'working'},{state:'standing',clipName:'idle'},{state:'standing',clipName:'idle_natural_v1',oneShot:true}]) {
  a.state=mode.state; a.clipName=mode.clipName??'idle_natural_v1'; a.body.oneShot=mode.oneShot; a.step(.05,50);
  assert.equal(a.body.values.at(-1),.05,'Walking/talking/work/old idle/one-shot preserve original bounded dt');
}
a.state='standing'; a.clipName='idle_natural_v1'; a.body.oneShot=false; a.step(.05,50); assert.equal(a.body.values.at(-1),0,'Standing transition does not catch up');
a.step(.05,.2); assert.equal(a.body.values.at(-1),.2);
a.body=body(); a.step(.05,50); assert.equal(a.body.values.at(-1),0,'LOD replacement starts its own idle clock');
a.step(.05,.2); for (const invalid of [NaN,Infinity,-1]) { a.step(.05,invalid); assert.equal(a.body.values.at(-1),0); }
a.distanceForTest=100; const beforeFar=a.body.values.length; a.step(.05,50); assert.equal(a.body.values.length,beforeFar,'Far actor holds its mixer');
a.distanceForTest=2; a.step(.05,50); assert.equal(a.body.values.at(-1),0,'Animation-range re-entry rejects unseen time');
a.step(.05,.2); a.distanceForTest=200; a.step(.05,50); assert.equal(a.inRange,false); assert.equal(a.visualIdleBody,null);
a.distanceForTest=2; a.step(.25,50); a.step(.25,50); assert.equal(a.body.values.at(-1),0,'Draw-range re-entry starts without catchup');
a.step(0,0); assert.equal(a.body.values.at(-1),0,'A held visual tick advances no idle');
actorDispose.call(a); const disposedCount=a.body; assert.equal(a.step(.05,50),false); assert.equal(a.body,disposedCount);
const layerUpdate = required(engine.match(/\n    update\(dt, camera, visitor = null, visualDt = dt\) \{([\s\S]*?)\n    \},\n\n    \/\*\* The selectable/), 'human layer update')[1];
const forwarded=[]; const layer = new Function('actors','near','emit','THREE',`return function(dt,camera,visitor=null,visualDt=dt){${layerUpdate}}`)(new Map([['one',{inRange:true,instance:{},update(...args){forwarded.push(args);}}]]),new Set(),()=>{},{});
const eye={}; layer(.05,{position:eye},{e:1,n:2},3); assert.deepEqual(forwarded.at(-1),[.05,eye,3]);
layer(.05,{position:eye}); assert.deepEqual(forwarded.at(-1),[.05,eye,.05],'Optional visual argument retains existing callers');

// Actual shared horse-layer activation: reduced motion, ancestor/range visibility and tier changes cannot bank unseen time.
const horseUpdate = required(standing.match(/    update\(camera, dt = 0, ([\s\S]*?)\n    \},\n    async setTier/), 'horse update');
const horseSignature = horseUpdate[1].slice(0,horseUpdate[1].indexOf(' {\n')).replace(/\)$/, '');
const horseBody = horseUpdate[1].slice(horseUpdate[1].indexOf(' {\n')+3);
const horseTier = required(standing.match(/    async setTier\(next\) \{([\s\S]*?)\n    \},\n    pickAt/), 'horse tier change')[1];
const horseReset = required(standing.match(/  const resetIdleClock = [\s\S]*?\n  motionPreference\?\.addEventListener\?\.\('change', resetIdleClock\);/), 'horse preference reset')[0];
const reach = required(standing.match(/const REACH = [^;]+;/), 'horse reach')[0];
const horseFactory = new Function('assert','globalThis',`return function(){
  ${reach}
  let tier='full', disposed=false, revision=0, active=null,lastCamera=null;
  const group={visible:true,parent:null}, confidence=null, motionPreference={matches:false,listeners:[],addEventListener(event,fn){this.listeners.push(fn);}};
  const eye={distanceTo(){return distance;}}, values=[];let distance=2;
  const make=()=>({group:{visible:true,position:{}},root:{traverse(fn){fn({isMesh:true});}},idleWasActive:false,idle:{status:{disposed:false},update(dt,options){values.push({dt,...options});}}});
  const withinReach=()=>false,load=async()=>{active??=make();},retire=()=>{if(active)active.idleWasActive=false;active=null;},abort=null;
  ${horseReset}
  active=make();const camera={getWorldPosition(v){return v;}};
  const out={update(camera,dt=0,${horseSignature}){${horseBody}},async setTier(next){${horseTier}}};
  return {values,group,frame(dt,options){out.update(camera,dt,options);},tier:out.setTier.bind(out),distance(v){distance=v;},reduced(v){motionPreference.matches=v;for(const fn of motionPreference.listeners)fn();}};
}`)(assert,{document:{hidden:false}});
const horse = horseFactory(); horse.frame(100,{visualFrame:false}); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Visibility-only refresh must not prime first real horse frame');
horse.frame(.2,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,.2);
horse.frame(100,{paused:true,visualFrame:true}); assert.equal(horse.values.at(-1).dt,0);
horse.frame(100,{paused:false,visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Horse pause resumes without catchup');
horse.frame(.2,{visualFrame:true});
horse.reduced(true); horse.reduced(false); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Preference change without a rendered tick rebases horse');
horse.frame(.2,{visualFrame:true}); horse.reduced(true); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0); assert.equal(horse.values.at(-1).reducedMotion,true);
horse.reduced(false); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0);
horse.frame(.2,{visualFrame:true}); horse.group.visible=false; horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0);
horse.group.visible=true; horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Ancestor visibility resumes without catchup');
horse.frame(.2,{visualFrame:true}); horse.distance(100); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0);
horse.distance(2); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Horse range re-entry rebases idle');
horse.frame(.2,{visualFrame:true}); await horse.tier('balanced'); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Tier refresh does not prime a new real idle interval');
horse.frame(.2,{visualFrame:true}); await horse.tier('light'); const last=horse.values.length; horse.frame(100,{visualFrame:true}); assert.equal(horse.values.length,last,'Phone-light tier has no standing development horse');
await horse.tier('balanced'); horse.frame(100,{visualFrame:true}); assert.equal(horse.values.at(-1).dt,0,'Reloaded owner has a separate activation clock');

assert.throws(()=>horse.frame(NaN,{visualFrame:true}),/finite and nonnegative/);
assert.throws(()=>horse.frame(-1,{visualFrame:true}),/finite and nonnegative/);

const route = required(engine.match(/\n  walk\(dt\) \{([\s\S]*?)\n  \}\n\n  \/\*\*/), 'human route')[1];
const walk = new Function('dt','findClip',route);
const walker = {state:'walking',route:[{local_e:0,local_n:0},{local_e:.2,local_n:0},{local_e:.2,local_n:.2}],
  body:{clips:new Map()},walkSpeed:1,leg:0,legT:0,e:0,n:0,placements:0,place(){this.placements++;}};
walk.call(walker,.25,()=>null); assert.equal(walker.leg,1,'Slow frame consumes a route corner without losing elapsed time');
assert(Math.abs(walker.e-.2)<1e-12&&Math.abs(walker.n-.05)<1e-12);
walker.state='standing';const before={e:walker.e,n:walker.n,leg:walker.leg,placements:walker.placements};walk.call(walker,.25,()=>null);
assert.deepEqual({e:walker.e,n:walker.n,leg:walker.leg,placements:walker.placements},before,'Standing actors remain planted');
console.log('PASS: native clock/latches preserve bounded locomotion and routes; cosmetic idle resets across visibility, holds, context, body/range/tier and reduced motion');
