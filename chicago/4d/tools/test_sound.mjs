// T-3532: replace obsolete synthetic-tone assertions with recorded-audio contracts.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createSound, curve } from '../renderers/web/js/sound.js';
import { createJourney } from '../renderers/web/js/journey.js';
import { createRecordedAudio, nearbyWater, waterKind, musicFor, windGain } from '../renderers/web/js/recorded-audio.js';

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
for(const year of ['1812','1835','1904']) {
  const town=windGain(year,'summer',null),shore=windGain(year,'summer','lake',0);
  assert(town < .13/4,'town rustle is substantially below the rejected constant wind');
  assert(shore>town && shore<.13/2,'lake exposure stays restrained, never the old windy bed');
  assert(windGain(year,'summer','lake',24)<shore);
  assert.equal(windGain(year,'summer','lake',56),town);
  assert.equal(windGain(year,'summer','river',0),town,'a river does not inherit exposed lake wind');
  assert.equal(windGain(year,'summer','slough',0),town);
  assert.equal(windGain(year,'fall',null),town/2);
  assert.equal(windGain(year,'winter','lake',0),0,'no leaf rustle in the bare season');
}
assert(windGain('1904','summer',null)<windGain('1812','summer',null),'1904 town uses a quieter mix than open early Chicago');
const selectedRiver=catalog.assets.find(a=>a.id==='river'),heldRiver=catalog.assets.find(a=>a.id==='river-held');
assert.equal(selectedRiver.runtime_enabled,true,'owner-selected calmer river recording is enabled');
assert.equal(selectedRiver.delivery.sha256,'6831b7ad102ec023194c4040776c5245b6cb47451d652a94a07dc742e28362af','the accepted recording is not silently substituted');
assert.equal(heldRiver.runtime_enabled,false,'owner-rejected busy recording remains held under its own library id');
assert.equal(heldRiver.delivery.sha256,'a63798768beaff4eba54e79293c89b81e9940d87d8742b45b0ac93130610bd5a');
assert.notEqual(selectedRiver.url,heldRiver.url);
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
  const ctx=context(),journey=createJourney({initial:'observatory',root:null});let last,calls=0;
  const sound=createSound({audio:()=>ctx,journey,doc:null,storage:null,every:()=>1,cancelEvery(){},
    settings:()=>({soundMaster:1,soundMusic:1,soundAmbience:1,soundEffects:1}),
    recordings:()=>({sync(s){last=s;calls++;},dispose(){}})});
  for(const state of ['observatory','locking','jumping','time-stream','landing','landed']) {
    assert(journey.go(state));assert.equal(last.musicOn,false,`${state} has no period music`);
    assert(last.active&&last.ambienceOn&&last.effectsOn,'arrival leaves ambience and effects independently enabled');
  }
  for(const state of ['exploring','inspecting','on-jaunt','touring']) {
    assert(journey.go(state));assert.equal(last.musicOn,true,`${state} permits the era playlist immediately`);
  }
  assert(journey.recall());assert.equal(last.musicOn,false,'recall stops period music');
  sound.dispose();const disposedCalls=calls;sound.sync();assert.equal(calls,disposedCalls);
}
{
  const ctx=context(), media=mediaFactory();
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),
    media:()=>media.make(),fetcher:async()=>({ok:true,json:async()=>catalog})});
  const sync=musicOn=>engine.sync({active:true,ambienceOn:true,musicOn,year:'1835'});
  sync(true);await flush();const first=media.made[0];
  first.onerror();first.onerror();assert(!engine.state.playing);
  sync(true);await flush();assert.equal(media.made.length,1,'failed media does not spin retries');
  sync(false);sync(true);await flush();
  assert(engine.state.playing,'a deliberate Music off/on retries without muting ambience');
  assert.equal(media.made.length,2);engine.dispose();
}
{
  // Natural ends advance immediately using the already-unlocked media element.
  // No timer tick or clock advance is needed, including the wrap to cue one.
  const ctx=context(), media=mediaFactory(); let connects=0;
  const original=ctx.createMediaElementSource;
  ctx.createMediaElementSource=()=>{connects++;return original();};
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),
    media:()=>media.make(),now:()=>0,fetcher:async()=>({ok:true,json:async()=>catalog})});
  const sync=(year,active=true,musicOn=true)=>engine.sync({active,ambienceOn:false,musicOn,year});
  for(const year of ['1835','1812','1904']) {
    sync(year);await flush();
    const list=musicFor(catalog,year),element=media.made.at(-1),before=media.made.length,links=connects;
    for(let i=1;i<=list.length*2;i++) {
      element.paused=true;element.onended();await flush();
      assert.equal(engine.state.track,list[i%list.length].title);
      assert(engine.state.playing,'natural end immediately starts the next cue');
      assert.equal(media.made.length,before,'all cues reuse the gesture-unlocked player');
      assert.equal(connects,links,'all cues reuse the same media graph node');
    }
    const retired=element.onended;
    sync(year,true,false);retired();await flush();
    assert(!engine.state.playing,'Music off cannot be undone by a queued ending');
    sync(year);await flush();const restarted=media.made.at(-1);
    retired();assert.equal(media.made.at(-1),restarted);assert.equal(engine.state.track,list[0].title);
  }
  const retired=media.made.at(-1).onended;
  sync('1835');await flush();retired();assert.equal(engine.state.track,musicFor(catalog,'1835')[0].title);
  const muted=media.made.at(-1).onended;
  sync('1835',false);muted();assert(!engine.state.playing);
  sync('1835');await flush();const disposed=media.made.at(-1).onended;
  engine.dispose();disposed();assert(!engine.state.playing);
}
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
  let season='summer',activeTerrain=terrain;
  const fixture={...catalog,water_zones:{'1835':{epoch:'test',features:[{kind:'river',polygon:[[[0,-100],[100,-100],[100,100],[0,100],[0,-100]]]}]}}};
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),media:()=>media.make(),
    environment:()=>({season,camera:{position:{x:0,y:2,z:0}},terrain:activeTerrain}),
    fetcher:async url=> {requests.push(String(url));return {ok:true,json:async()=>fixture,arrayBuffer:async()=>new ArrayBuffer(0)};} });
  engine.sync({active:false,ambienceOn:true,musicOn:true,year:'1835'});await flush();
  assert.equal(requests.length,0,'muted boot downloads nothing');
  engine.sync({active:true,ambienceOn:true,musicOn:true,year:'1835'});await flush();
  assert.deepEqual(engine.state.voices,['wind','river']);assert.equal(engine.state.decodedBytes,8448000);
  assert(requests.some(url=>url.endsWith('/river.mp3')),'classified river edge requests the selected recording');
  assert(!requests.some(url=>url.endsWith('/river-held.mp3')),'rejected recording is not fetched, not merely turned down');
  assert.equal(media.made.length,1);assert.match(media.made[0].src,/1835\/.*border.*ogg$/);
  season='winter';engine.update();assert.deepEqual(engine.state.voices,['river'],'bare-season suppression removes leaf rustle independently of water');
  activeTerrain={...terrain,lakeShore:{n0:-100,step:100,e:[0,0,0]}};
  engine.update();await flush();assert.deepEqual(engine.state.voices,['lake'],'lake geography selects the separate lake recording');
  assert(requests.some(url=>url.endsWith('/lake.mp3')));
  assert.equal(engine.state.decodedBytes,12672000,'three environmental loops fit the existing 14 MiB cache');
  const count=requests.length;
  fixture.water_zones['1835'].features.unshift({kind:'slough',width_m:10,line:[[24,-10],[24,10]]});
  engine.update();await flush();assert.deepEqual(engine.state.voices,[],'slough classification suppresses both water proxies');
  assert.equal(requests.length,count,'slough entry does not fetch a substitute');
  activeTerrain={...terrain,epochId:'other'};
  engine.update();await flush();assert.deepEqual(engine.state.voices,[],'unclassified water stays quiet');
  assert.equal(requests.length,count);
  assert.deepEqual(engine.state.errors,[]);
  engine.sync({active:true,ambienceOn:true,musicOn:true,year:'1904'});await flush();
  assert.equal(media.made[0].src,'','scene switch releases the old stream');
  assert.match(media.made.at(-1).src,/1904\/.*waltz.*ogg$/);
  engine.sync({active:false,ambienceOn:true,musicOn:true,year:'1904'});await flush();
  assert.equal(engine.state.voices.length,0);assert.equal(engine.state.decodedBytes,0);assert.equal(engine.state.playing,false);
  engine.dispose();
}
{
  // Exercise the runtime's exclusion guard independently of river-held's id:
  // a rejected asset must remain silent even when occupying the target id.
  const ctx=context(),requests=[];
  const fixture={...catalog,assets:catalog.assets.filter(a=>a.id!=='river'&&a.id!=='river-held').concat({...heldRiver,id:'river'}),
    water_zones:{'1835':{epoch:'test',features:[{kind:'river',polygon:[[[0,-100],[100,-100],[100,100],[0,100],[0,-100]]]}]}}};
  const engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music:ctx.createGain(),
    environment:()=>({season:'summer',camera:{position:{x:0,y:2,z:0}},terrain}),
    fetcher:async url=>{requests.push(String(url));return {ok:true,json:async()=>fixture,arrayBuffer:async()=>new ArrayBuffer(0)};}});
  engine.sync({active:true,ambienceOn:true,musicOn:false,year:'1835'});await flush();
  assert.deepEqual(engine.state.voices,['wind']);assert.equal(engine.state.decodedBytes,4224000);
  assert(!requests.some(url=>url.endsWith('/river-held.mp3')),'runtime_enabled:false excludes fetching even for an otherwise selected river target');
  assert.deepEqual(engine.state.errors,[]);engine.dispose();
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
  assert.deepEqual(candidates.filter(a=>a.runtime_enabled).map(a=>a.id).sort(),
    ['coyote-distant','hammer-nail','horse-harness','horse-walking','late-summer-katydid','redwing-call','robin-calls','summer-cicada-proxy','summer-crickets','wood-wagon']);
  for (const asset of candidates) {
    assert(asset.evidence && asset.source_url);
    if (!asset.runtime_enabled) { assert.deepEqual(asset.approved_eras, []); continue; }
    assert(asset.approved_eras.length > 0);
    const p = asset.scene_placement;
    if (['moving-transport','hoof-contact'].includes(p?.mode)) {
      assert(p.bindings.length > 0 && p.bindings.every(b => asset.approved_eras.includes(b.scene)
        && b.scene_date.startsWith(b.scene+'-') && b.actor_ids.length > 0));
    } else if (p?.mode === 'visible-work') {
      assert.deepEqual(asset.approved_eras, ['1812']);
      assert(p.bindings.length > 0 && p.bindings.every(b => b.scene === '1812'
        && b.dates.from.startsWith('1812-') && b.dates.to.startsWith('1812-')
        && b.dates.from <= b.dates.to && b.hours.length && b.actor_ids.length && b.action_ids.length && b.task_ids.length));
    } else {
      if (asset.approved_eras.includes('1835')) assert.equal(p?.scene_date, '1835-07-01');
      if (asset.approved_eras.includes('1812')) {
        assert(asset.seasonal_placements.length > 0 && asset.seasonal_placements.every(p => p.scene_id === '1812'
          && ['spring','summer','fall','winter'].includes(p.season) && p.confidence === 'reconstructed'
          && p.flora_zone_ids.length && p.active_periods.length && p.source_ids.length
          && p.source_ids.every(id => fs.existsSync(new URL('../data/sources/'+id+'.json', import.meta.url)))));
      }
      assert(asset.approved_eras.every(y => ['1812','1835'].includes(y)), 'nature does not spill into 1904');
    }
  }
  const sound=fs.readFileSync(new URL('../renderers/web/js/sound.js',import.meta.url),'utf8');
  assert.doesNotMatch(sound,/createOscillator|createBuffer\(/,'no generated hums or tones');
  const main=fs.readFileSync(new URL('../renderers/web/js/main.js',import.meta.url),'utf8');
  assert.match(main,/gesture\.unlockAudio\(\)/);assert.match(main,/environment: \(\) =>/);
}
console.log('SOUND PASS — separate era libraries; no muted fetch; terrain proximity; bounded decoded memory; music stream cleanup; hidden/mute/scene races; no synthetic tones');
