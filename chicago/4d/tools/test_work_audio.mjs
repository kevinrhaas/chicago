// SPDX-License-Identifier: GPL-3.0-or-later
// Sparse real contact admission and bounded recorded pulse lifecycle; no network/browser.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createWorkAudio,workPolicy,workCandidate,WORK_RECORDING} from '../renderers/web/js/work-audio.js';
const actorId='hi_town_chicago_militia_unnamed_4_1812';
const catalogue=()=>({assets:[{id:'hammer-nail',runtime_enabled:true,approved_eras:['1812'],
 delivery:{sha256:WORK_RECORDING.sha256,bytes:WORK_RECORDING.encodedBytes},url:'https://test.invalid/hammer.mp3',
 scene_placement:{mode:'visible-work',gain:.14,max_distance_m:20,cue:{offset_s:21.526,duration_s:.36},
 bindings:[{scene:'1812',dates:{from:'1812-04-07',to:'1812-08-13'},hours:[[6.5,12],[13,18]],actor_ids:[actorId],action_ids:['nail-wood'],task_ids:['militia-piazza-repair']},
 {scene:'1812',dates:{from:'1812-08-14',to:'1812-08-14'},hours:[[13,18]],actor_ids:[actorId],action_ids:['nail-wood'],task_ids:['militia-packing-chest']}]} }]});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{resolve,promise};};
const flush=async()=>{for(let i=0;i<8;i++)await new Promise(r=>setImmediate(r));};
const whole=()=>{const channel=new Float32Array(24*48000);channel.fill(.25,Math.round(21.526*48000),Math.round((21.526+.36)*48000));
 return{sampleRate:48000,numberOfChannels:1,length:channel.length,duration:24,getChannelData:()=>channel};};
function rig(options={}){
 let time=0,peak=0;const cat=catalogue(),fetches=[],starts=[],sources=[],errors=[];
 const param=()=>({value:0,setTargetAtTime(v){this.value=v;},setValueAtTime(v){this.value=v;},linearRampToValueAtTime(v){this.value=v;},cancelScheduledValues(){}});
 const node=()=>({connected:[],disconnected:false,connect(n){this.connected.push(n);},disconnect(){this.disconnected=true;}});
 const ctx={currentTime:0,createGain:()=>Object.assign(node(),{gain:param()}),createPanner:()=>Object.assign(node(),{positionX:param(),positionY:param(),positionZ:param()}),
 createBuffer(ch,length,rate){const a=new Float32Array(length);return{numberOfChannels:ch,length,sampleRate:rate,duration:length/rate,getChannelData:()=>a};},
 createBufferSource(){const n=Object.assign(node(),{playbackRate:{value:1},onended:null,stops:[],start(...args){starts.push({n,args});peak=Math.max(peak,sources.filter(n=>n.started&&!n.disconnected).length+1);this.started=true;},stop(...args){this.stops.push(args);},end(){this.onended?.();}});sources.push(n);return n;}};
 const output={bus:'Effects'};
 const player=createWorkAudio({ctx,output,catalog:()=>cat,base:new URL('https://test.invalid/'),now:()=>time,
  fetcher:async(url,opts)=>{fetches.push({url,opts});return options.fetcher?options.fetcher():{ok:true,arrayBuffer:async()=>new ArrayBuffer(WORK_RECORDING.encodedBytes)};},
  hashAudio:options.hashAudio??(async()=>WORK_RECORDING.sha256),decodeAudio:options.decodeAudio??(async()=>whole()),onError:e=>errors.push(e)});
 const source={id:'militia-packing-chest',actorId,actionId:'nail-wood',scene:'1812',date:'1812-08-14',hour:15,session:1,contactSerial:0,contactAt:-Infinity,
  visible:true,working:true,updatedAt:0,anchor:{x:10,y:1,z:-5}};
 const frame=(changes={})=>{time+=34;ctx.currentTime=time/1000;source.updatedAt=time;player.frame({enabled:true,scene:'1812',date:'1812-08-14',hour:15,eye:{x:11,y:1,z:-5},sources:()=>[source],...changes});};
 const hit=()=>{source.contactSerial++;source.contactAt=time+34;frame();};
 return{ctx,output,player,cat,source,frame,hit,fetches,starts,sources,errors,get now(){return time;},get peak(){return peak;},advance(ms){time+=ms;}};
}

test('existing delivered recording exactly matches provenance-bound hash/size',async()=>{
 const bytes=await fs.readFile(new URL('../renderers/web/audio/candidates/hammer-nail.mp3',import.meta.url));
 assert.equal(bytes.length,WORK_RECORDING.encodedBytes);assert.equal(createHash('sha256').update(bytes).digest('hex'),WORK_RECORDING.sha256);
});
test('exact date, hour, era, task and actor admission',()=>{
 const cat=catalogue(),q={scene:'1812',date:'1812-08-14',hour:15};assert(workPolicy(cat,q));
 for(const v of [{scene:'1835'},{date:'1812-02-15'},{date:'1812-08-15'},{hour:12},{hour:18}])assert.equal(workPolicy(cat,{...q,...v}),null);
 const r=rig(),policy=workPolicy(cat,q);r.source.updatedAt=10;
 assert(workCandidate(policy,[r.source],{...q,eye:{x:10,y:1,z:-5},now:10}));
 for(const v of [{actorId:'unseen-person'},{actionId:'idle'},{visible:false},{working:false},{date:'1812-04-15'},{id:'militia-piazza-repair'},{hour:14}])
  assert.equal(workCandidate(policy,[{...r.source,...v}],{...q,eye:{x:10,y:1,z:-5},now:10}),null);
});
test('inactive/unapproved frames never evaluate lazy work sources or fetch',async()=>{
 const r=rig();const sources=()=>{throw Error('should not traverse work');};r.frame({enabled:false,sources});
 r.cat.assets[0].runtime_enabled=false;r.frame({sources});await flush();assert.equal(r.fetches.length,0);
});
test('one real contact plays one copied pulse at the actual world anchor, through Effects',async()=>{
 const r=rig();r.frame();await flush();assert.equal(r.player.state.decodedBytes,69120);assert.equal(r.starts.length,0);
 r.hit();assert.equal(r.starts.length,1);assert.equal(r.player.state.started,1);assert.equal(r.player.state.lastContact.serial,1);
 const n=r.starts[0].n;assert.equal(n.buffer.length,17280);assert.equal(n.buffer.getChannelData(0)[500],.25);assert.equal(n.loop,false);assert.equal(n.playbackRate.value,1);
 const pan=n.connected[0].connected[0].connected[0];assert.equal(pan.positionX.value,10);assert.equal(pan.positionY.value,1);assert.deepEqual(pan.connected,[r.output]);
 for(let i=0;i<10;i++)r.frame();assert.equal(r.starts.length,1);assert.equal(r.fetches.length,1);
 n.end();assert.deepEqual(r.player.state.voices,[]);
});
test('late decode never catches up missed contact, next fresh contact can play',async()=>{
 const d=deferred(),r=rig({decodeAudio:()=>d.promise});r.frame();await flush();r.hit();d.resolve(whole());await flush();r.frame();assert.equal(r.starts.length,0);
 r.advance(1000);r.hit();assert.equal(r.starts.length,1);assert.equal(r.player.state.lastContact.serial,2);
});
test('stale/skipped contacts are consumed; one active or cancelling voice never overlaps',async()=>{
 const r=rig();r.frame();await flush();r.source.contactSerial=1;r.source.contactAt=r.now-200;r.frame();assert.equal(r.starts.length,0);
 r.source.contactAt=r.now;r.frame();assert.equal(r.starts.length,0);
 r.hit();assert.equal(r.starts.length,1);r.advance(1000);r.hit();assert.equal(r.starts.length,1,'occupied sole slot drops contact');
 r.starts[0].n.end();r.advance(1000);r.hit();assert.equal(r.starts.length,2);assert.equal(r.peak,1);
 r.starts[1].n.end();r.advance(1000);r.source.contactSerial+=2;r.source.contactAt=r.now;r.frame();assert.equal(r.starts.length,2,'no burst for skipped serials');
});
test('hidden, stale source, date change and mute stop existing voice immediately',async()=>{
 for(const mutate of [r=>({sources:[]}),r=>({date:'1812-04-15'}),r=>({enabled:false}),r=>({sources:[{...r.source,updatedAt:r.now-500}]})]){
  const r=rig();r.frame();await flush();r.hit();r.frame(mutate(r));assert.deepEqual(r.player.state.voices,[]);assert(r.starts[0].n.disconnected);
 }
});
test('session/body reset suppresses first contact snapshot and late prior async result',async()=>{
 const d=deferred(),r=rig({decodeAudio:()=>d.promise});r.frame();await flush();r.player.reset();r.source.session++;r.source.contactSerial=3;r.frame();
 assert.equal(r.fetches.length,1,'outstanding decoder reserves slot');d.resolve(whole());await flush();assert.equal(r.player.state.decodedBytes,0);
 r.frame();await flush();r.frame();assert.equal(r.starts.length,0);
});
test('delivery hash failure prevents decoding and retries',async()=>{
 let decodes=0;const r=rig({hashAudio:async()=> 'wrong',decodeAudio:async()=>{decodes++;return whole();}});
 r.frame();await flush();r.frame();assert.equal(decodes,0);assert.equal(r.fetches.length,1);assert.equal(r.player.state.failed,true);assert.equal(r.errors.length,1);
});
test('budget rejects stereo or oversized decode; disposal rejects late decode',async()=>{
 for(const tweak of [b=>({...b,numberOfChannels:2}),b=>({...b,length:2*1024*1024}),b=>({...b,sampleRate:96000})]){
  const r=rig({decodeAudio:async()=>tweak(whole())});r.frame();await flush();assert.equal(r.player.state.failed,true);assert.equal(r.player.state.decodedBytes,0);
 }
 const d=deferred(),r=rig({decodeAudio:()=>d.promise});r.frame();await flush();r.player.dispose();d.resolve(whole());await flush();r.hit();assert.equal(r.starts.length,0);assert.equal(r.player.state.decodedBytes,0);
});
