// T-3532: replace obsolete synthetic-tone assertions with recorded-audio contracts.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createSound, curve } from '../renderers/web/js/sound.js';
import { createRecordedAudio, nearbyWater, waterKind, musicFor } from '../renderers/web/js/recorded-audio.js';

const catalog = JSON.parse(fs.readFileSync(new URL('../renderers/web/audio/catalog.json', import.meta.url)));
assert.deepEqual(['1812','1835','1904'].map(y => musicFor(catalog,y).length), [3,2,2]);
assert(musicFor(catalog,'1812').every(t => t.title.includes('Frontier')));
assert(musicFor(catalog,'1835').every(t => t.title.includes('Border')));
assert(musicFor(catalog,'1904').every(t => t.title.includes('Waltz')));
assert.equal(musicFor(catalog,'1888').length, 0, 'no cross-era music fallback');
assert.equal(nearbyWater({ loaded: false }, {x:0,z:0}), null);
const terrain = { epochId:'test', loaded: true, heightfield: { contains: () => true }, isWater: x => x >= 20 };
assert.equal(nearbyWater(terrain, {x:0,z:0}).distance, 24);
assert.equal(nearbyWater(terrain, {x:0,y:32,z:0}).distance, 40,
  'water attenuates with the full listener-to-water distance, including altitude');
assert.equal(nearbyWater(terrain, {x:24,y:200,z:0}), null,
  'flying above a river leaves acoustic range rather than becoming louder again');
assert.equal(nearbyWater(terrain, {x:-100,z:0}), null);
assert.equal(curve(.5), .25);
const zone={epoch:'test',features:[{kind:'slough',width_m:10,line:[[20,-10],[20,10]]},{kind:'river',polygon:[[[0,-100],[100,-100],[100,100],[0,100],[0,-100]]]}]};
assert.equal(waterKind({x:20,z:0},terrain,zone),'slough','slough takes precedence over neighbouring river');
assert.equal(waterKind({x:45,z:0},terrain,zone),'river');
assert.equal(waterKind({x:200,z:0},terrain,zone),null,'unknown water is not generic surf');
assert.equal(waterKind({x:200,z:0},{...terrain,lakeShore:{n0:-100,step:100,e:[100,100,100]}},zone),'lake');
assert.equal(waterKind({x:45,z:0},{...terrain,epochId:'other'},zone),null,'epoch mismatch never reuses geography');
const param = () => ({ value:0, setTargetAtTime(v) { this.value = v; } });
function context() {
  const sources = [];
  const node = () => ({ connect() {}, disconnect() {}, gain:param() });
  return { state:'running', currentTime:0, destination:node(), listener:{}, sources,
    addEventListener() {}, removeEventListener() {}, createGain:node,
    createPanner:() => ({ ...node(), positionX:param(), positionY:param(), positionZ:param() }),
    createBufferSource() { const n={...node(), start(){this.started=true;}, stop(){this.stopped=true;}}; sources.push(n);return n; },
    createMediaElementSource:node,
    decodeAudioData:async () => ({ duration:22,length:1056000,numberOfChannels:1 }),
  };
}
function mediaFactory() {
  const made=[];
  return { made, make() { const m={ paused:true, src:'', canPlayType:()=> 'probably', play(){this.paused=false;return Promise.resolve();}, pause(){this.paused=true;}, removeAttribute(){this.src='';},load(){} };made.push(m);return m; } };
}
const flush = async () => { for(let i=0;i<12;i++) await Promise.resolve(); };
{
  // A high-rate device must not quietly multiply the decoded cache budget.
  const ctx=context();
  ctx.decodeAudioData=async()=>({duration:22,length:22*192000,numberOfChannels:1});
  const options={ctx,ambience:ctx.createGain(),music:ctx.createGain(),
    environment:()=>({season:'summer',camera:{position:{x:0,y:2,z:0}},terrain:{loaded:false}}),
    fetcher:async()=>({ok:true,json:async()=>catalog,arrayBuffer:async()=>new ArrayBuffer(0)})};
  const fallback=createRecordedAudio(options);
  fallback.sync({active:true,ambienceOn:true,musicOn:false,year:'1835'});await flush();
  assert.equal(fallback.state.decodedBytes,0);
  assert(fallback.state.errors.some(e=>e.includes('14 MiB')),'fallback decoder cannot exceed the byte budget');
  fallback.dispose();
  const previous=globalThis.OfflineAudioContext;
  globalThis.OfflineAudioContext=class {
    constructor(channels,frames,rate){this.rate=rate;}
    async decodeAudioData(){return {duration:22,length:22*this.rate,numberOfChannels:1};}
  };
  try {
    const fixed=createRecordedAudio(options);
    fixed.sync({active:true,ambienceOn:true,musicOn:false,year:'1835'});await flush();
    assert.equal(fixed.state.decodedBytes,4224000,'fixed-rate decoding keeps the same cache on a192k device');
    assert.deepEqual(fixed.state.voices,['wind']);assert.deepEqual(fixed.state.errors,[]);fixed.dispose();
  } finally { if(previous)globalThis.OfflineAudioContext=previous;else delete globalThis.OfflineAudioContext; }
}
{
  const ctx=context(), doc={ hidden:false,addEventListener(){},removeEventListener(){} };
  let recorded, settings={}; let timer;
  const sound=createSound({audio:()=>ctx, doc,settings:()=>settings,scene:()=> '1835', storage:null,
    every:fn => {timer=fn;return 1;},cancelEvery(){timer=null;},
    recordings:()=> recorded={ sync(v){this.last=v;},dispose(){this.dead=true;},state:{} } });
  assert.equal(recorded.last.active,false,'first visit remains silent');
  settings={soundMaster:.5,soundAmbience:1,soundMusic:.4};sound.sync();
  assert.equal(sound.nodes.master.gain.value,.25);assert(recorded.last.active);
  doc.hidden=true;timer();assert(!recorded.last.active,'hidden tab stops recordings');
  doc.hidden=false;timer();assert(recorded.last.active);
  settings.soundMaster=0;sound.setting('soundMaster');assert(!recorded.last.active);
  assert.equal(sound.state.hum,false);assert.equal(sound.relay(),false);assert.equal(sound.ticker(1812),0);
  sound.dispose();assert(recorded.dead);assert.equal(timer,null);
}
{
  const ctx=context(), media=mediaFactory(), requests=[];
  let season='summer';
  const fixture={...catalog,water_zones:{'1835':{epoch:'test',features:[{kind:'river',polygon:[[[0,-100],[100,-100],[100,100],[0,100],[0,-100]]]}]}}};
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),media:()=>media.make(),
    environment:()=>({season,camera:{position:{x:0,y:2,z:0}},terrain}),
    fetcher:async url=> {requests.push(String(url));return {ok:true,json:async()=>fixture,arrayBuffer:async()=>new ArrayBuffer(0)};} });
  engine.sync({active:false,ambienceOn:true,musicOn:true,year:'1835'});await flush();
  assert.equal(requests.length,0,'muted boot downloads nothing');
  engine.sync({active:true,ambienceOn:true,musicOn:true,year:'1835'});await flush();
  assert.deepEqual(engine.state.voices.sort(),['river','wind']);assert.equal(engine.state.decodedBytes,8448000);
  assert.equal(media.made.length,1);assert.match(media.made[0].src,/1835\/.*border.*ogg$/);
  season='winter';engine.update();assert.deepEqual(engine.state.voices,['river']);
  engine.sync({active:true,ambienceOn:true,musicOn:true,year:'1904'});await flush();
  assert.equal(media.made[0].src,'','scene switch releases the old stream');
  assert.match(media.made.at(-1).src,/1904\/.*waltz.*ogg$/);
  engine.sync({active:false,ambienceOn:true,musicOn:true,year:'1904'});await flush();
  assert.equal(engine.state.voices.length,0);assert.equal(engine.state.decodedBytes,0);assert.equal(engine.state.playing,false);
  engine.dispose();
}
{
  const ctx=context(), media=mediaFactory();let release;
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),media:()=>media.make(),
    fetcher:()=>new Promise(r=>release=r)});
  engine.sync({active:true,ambienceOn:true,musicOn:true,year:'1812'});
  engine.sync({active:false,ambienceOn:true,musicOn:true,year:'1812'});
  release({ok:true,json:async()=>catalog});await flush();
  assert.equal(media.made.length,0,'a stale catalogue completion after mute cannot start playback');engine.dispose();
}
{
  const ctx=context(), media=mediaFactory();let rejectOpus;
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),
    media:()=>{const m=media.make();m.play=function(){this.paused=false;return this.src.endsWith('.ogg')?new Promise((_,reject)=>{rejectOpus=reject;}):Promise.resolve();};return m;},
    fetcher:async()=>({ok:true,json:async()=>catalog})});
  engine.sync({active:true,ambienceOn:false,musicOn:true,year:'1812'});await flush();
  const element=media.made[0];element.onerror();
  assert.match(element.src,/\.m4a$/,'media error tries AAC');
  rejectOpus(Object.assign(Error('unsupported Opus'),{name:'NotSupportedError'}));await flush();
  assert(engine.state.playing,'late Opus rejection cannot stop successful AAC fallback');
  assert.deepEqual(engine.state.errors,[]);engine.dispose();
}
{
  const root=new URL('../renderers/web/audio/',import.meta.url);
  let total=0;
  for(const a of catalog.assets) for(const file of a.kind==='music'?[a.opus,a.aac]:[a.url]) {
    const data=fs.readFileSync(new URL(file,root));total+=data.length;assert(data.length>1000);
  }
  assert(total<40*1024*1024,`both codec alternatives fit 40 MiB: ${total}`);
  assert(catalog.assets.filter(a=>a.kind==='environment').every(a=>a.license==='CC0-1.0'&&a.source_url));
  const candidates=catalog.assets.filter(a=>a.kind==='candidate');
  assert(candidates.length>=17,'expanded library includes the acquired recordings');
  assert(candidates.every(a=>a.runtime_enabled===false&&a.approved_eras.length===0&&a.evidence&&a.source_url),'library intake never invents approved scene placements');
  const sound=fs.readFileSync(new URL('../renderers/web/js/sound.js',import.meta.url),'utf8');
  assert.doesNotMatch(sound,/createOscillator|createBuffer\(/,'no generated hums or tones');
  const main=fs.readFileSync(new URL('../renderers/web/js/main.js',import.meta.url),'utf8');
  assert.match(main,/gesture\.unlockAudio\(\)/);assert.match(main,/environment: \(\) =>/);
}
console.log('SOUND PASS — separate era libraries; no muted fetch; terrain proximity; bounded decoded memory; music stream cleanup; hidden/mute/scene races; no synthetic tones');
