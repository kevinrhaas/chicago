// Focused real-media/decoder check. Habitat geometry is a fixture, not actual town.
// Dated1835 fauna and separately authored1812 policy use real immutable R2 bytes.
// Nonzero output/hashes prove playback plumbing, not an audition or species ID.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = process.env.C4D_SOURCE_ROOT ?? root;
const catalog = JSON.parse(await fs.readFile(path.join(root, 'renderers/web/audio/catalog.json'), 'utf8'));
const policy = JSON.parse(await fs.readFile(path.join(source, 'tools/audio-hosting.json'), 'utf8'));
const index = JSON.parse(await fs.readFile(path.join(source, 'data/fauna/index.json'), 'utf8'));
const zones = await Promise.all(index.zones.map(z => fs.readFile(path.join(source, 'data/fauna', z.file), 'utf8').then(JSON.parse)));
for (const a of catalog.assets.filter(a => a.runtime_enabled))
  a.url = new URL(`media/${a.delivery.sha256}${path.extname(a.url)}`, policy.public_base).href;
const cases = [
  { id: 'summer-cicada-proxy', year: '1835', season: 'summer', zone: 'z01_wet_prairie', night: false },
  { id: 'summer-crickets', year: '1835', season: 'summer', zone: 'z01_wet_prairie', night: true },
  { id: 'redwing-call', year: '1835', season: 'summer', zone: 'z04_marsh', night: false },
  { id: 'robin-calls', year: '1812', season: 'spring', zone: 'z06_dense_forest', night: false },
  { id: 'late-summer-katydid', year: '1812', season: 'summer', zone: 'z06_dense_forest', night: true },
  { id: 'coyote-distant', year: '1812', season: 'winter', zone: 'z01_wet_prairie', night: true },
];
for (const c of cases) assert(catalog.assets.find(a => a.id === c.id)?.approved_eras?.includes(c.year), `${c.id} requires integrated metadata`);
let pw; try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const origin = policy.origin;
const fixture = `<!doctype html><button id="on">Enable sound</button><script type="module">
import {createHabitatAudio,habitatCandidates} from '/habitat-audio.js';
const catalog=${JSON.stringify(catalog)},zones=${JSON.stringify(zones)};
let engine,ctx,decoder,clock=0,env,year='1835',enabled=true;
window.issues=[];window.receipts=[];window.contextCounts={output:0,decoder:0};window.holdNextDecode=false;
const dates={spring:'1812-04-15',summer:'1812-08-14',fall:'1812-10-15',winter:'1812-02-15'};
window.sync=()=>engine?.sync({enabled:enabled&&!document.hidden,year});
window.configure=c=>{
 year=c.year;env={season:c.season,time:{date:year==='1835'?'1835-07-01':dates[c.season],hhmm:c.night?'23:00':'15:00'},
 sunElevation:c.night?-20:45,faunaZones:year==='1835'?zones:undefined,
 camera:{position:{x:0,y:year==='1812'?2.6:2,z:0},quaternion:{x:0,y:0,z:0,w:1}},
 flora:{zoneAt:()=>c.zone},terrain:{loaded:true,epochId:year==='1812'?'e1830_natural':'e1834_harbor_cut',
 surfaceHeight:()=>year==='1812'?1:0,isWater:()=>false,height:()=>4,heightfield:{contains:()=>true}}};
 engine.reset();clock+=1000000;sync();
};
window.advance=ms=>{clock+=ms;sync();};
window.eligibleIds=()=>habitatCandidates(catalog,env,year).map(c=>c.asset.id);
window.setEnabled=v=>{enabled=v;sync();};
window.setFixtureHidden=v=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>v});document.dispatchEvent(new Event('visibilitychange'));};
document.addEventListener('visibilitychange',()=>sync());
document.getElementById('on').onclick=async()=>{
 ctx=new AudioContext({sampleRate:96000});contextCounts.output++;await ctx.resume();window.ctx=ctx;
 decoder=new OfflineAudioContext(1,1,48000);contextCounts.decoder++;
 const output=ctx.createGain();output.gain.value=.5;
 window.meter=ctx.createAnalyser();output.connect(meter);meter.connect(ctx.destination);
 engine=createHabitatAudio({ctx,output,catalog:()=>catalog,environment:()=>env,now:()=>clock,
 random:()=>.5,onError:message=>issues.push(message),
 fetcher:async(url,options)=>{
   const response=await fetch(url,options);if(!response.ok)return response;
   const bytes=await response.arrayBuffer(),asset=catalog.assets.find(a=>a.url===String(url));
   const digest=await crypto.subtle.digest('SHA-256',bytes);
   const hash=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
   if(!asset||hash!==asset.delivery.sha256)throw Error('R2 delivery hash mismatch');
   receipts.push({id:asset.id,hash,bytes:bytes.byteLength});
   return {ok:true,arrayBuffer:async()=>bytes};
 },decodeAudio:async bytes=>{
   const decoded=await decoder.decodeAudioData(bytes);
   if(holdNextDecode){holdNextDecode=false;window.decodeHeld=true;await new Promise(resolve=>{window.releaseDecode=resolve;});window.decodeHeld=false;}
   return decoded;
 }});
 window.engine=engine;window.outputRate=ctx.sampleRate;
 configure(${JSON.stringify(cases[0])});advance(30000);
};
window.peak=()=>{if(!window.meter)return 0;const a=new Float32Array(meter.fftSize);meter.getFloatTimeDomainData(a);return Math.max(...a.map(Math.abs));};
</script>`;
const browser = await pw.chromium.launch({ executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] });
try {
 for (const width of [390,1280]) {
  const page = await browser.newPage({viewport:{width,height:780}}), requests=[], errors=[];
  page.on('request',r=>{if(r.url().startsWith(policy.public_base))requests.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(origin+'/**',async route=>{
   const url=new URL(route.request().url());
   if(url.pathname==='/fixture') return route.fulfill({contentType:'text/html',body:fixture});
   if(['/habitat-audio.js','/habitat-seasons.js'].includes(url.pathname)) return route.fulfill({contentType:'text/javascript',body:await fs.readFile(path.join(root,'renderers/web/js',url.pathname.slice(1)),'utf8')});
   return route.fulfill({status:404,body:'Not found'});
  });
  await page.goto(origin+'/fixture');await page.waitForTimeout(200);assert.equal(requests.length,0);
  await page.click('#on');
  for(const [i,c] of cases.entries()) {
   if(i) await page.evaluate(c=>{configure(c);advance(c.id==='coyote-distant'?180000:30000);},c);
   await page.waitForFunction(id=>engine.state.voices.includes(id)&&peak()>0.000001,c.id,{timeout:30000,polling:50});
   const state=await page.evaluate(()=>({state:engine.state,outputRate,issues,receipts,contextCounts,contextState:ctx.state}));
   assert.equal(state.outputRate,96000);assert.equal(state.contextState,'running');
   assert.deepEqual(state.contextCounts,{output:1,decoder:1});assert(state.state.decodedBytes<=24*48000*4);
   const asset=catalog.assets.find(a=>a.id===c.id), receipt=state.receipts.at(-1);
   assert.equal(receipt.id,c.id);assert.equal(receipt.hash,asset.delivery.sha256);assert.equal(receipt.bytes,asset.delivery.bytes);
   assert(Math.abs(state.state.decodedBytes-asset.duration_s*48000*4)<48000,'clip stays 48 kHz despite 96 kHz output');
   assert.equal(!!state.state.anchor,['redwing-call','robin-calls','coyote-distant'].includes(c.id));assert.deepEqual(state.issues,[]);
   console.log(`HABITAT MEDIA PASS ${width}px ${c.year}/${c.season} ${c.id}: real R2 hash ${receipt.hash}, nonzero samples, ${state.state.decodedBytes} decoded bytes`);
  }
  assert.equal(requests.length,6);
  // Winter daylight is quiet even after advancing the scheduling clock; the
  // preceding real coyote case proves its rare nighttime exception is audible.
  await page.evaluate(()=>{configure({year:'1812',season:'winter',zone:'z01_wet_prairie',night:false});advance(900000);});
  assert.deepEqual(await page.evaluate(()=>eligibleIds()),[]);assert.equal(requests.length,6);
  assert.deepEqual(await page.evaluate(()=>engine.state.voices),[]);
  // A genuine 48k decoded robin result is held across a season change. Its token
  // must stay reserved and the late completion must not revive spring playback.
  await page.evaluate(()=>{holdNextDecode=true;configure({year:'1812',season:'spring',zone:'z06_dense_forest',night:false});advance(30000);});
  await page.waitForFunction(()=>window.decodeHeld===true,null,{timeout:30000});
  assert.equal(await page.evaluate(()=>engine.state.loading),1);
  await page.evaluate(()=>{configure({year:'1812',season:'winter',zone:'z06_dense_forest',night:false});advance(900000);});
  assert.equal(await page.evaluate(()=>engine.state.loading),1);assert.equal(requests.length,7);
  await page.evaluate(()=>releaseDecode());await page.waitForFunction(()=>engine.state.loading===0);
  assert(await page.evaluate(()=>!engine.state.voices.length&&engine.state.decodedBytes===0));
  // Resume a real robin, then exercise the mixer's effective hidden/mute inputs.
  await page.evaluate(()=>{configure({year:'1812',season:'spring',zone:'z06_dense_forest',night:false});advance(30000);});
  await page.waitForFunction(()=>engine.state.voices.includes('robin-calls')&&peak()>0.000001,null,{timeout:30000});
  await page.evaluate(()=>setFixtureHidden(true));await page.waitForTimeout(150);
  assert(await page.evaluate(()=>!engine.state.voices.length&&engine.state.decodedBytes===0&&peak()<0.000001));
  await page.evaluate(()=>{setEnabled(false);setFixtureHidden(false);advance(900000);});
  assert.equal(requests.length,8);assert.deepEqual(errors,[]);assert.deepEqual(await page.evaluate(()=>issues),[]);
  await page.evaluate(()=>{engine.dispose();advance(900000);});assert.equal(requests.length,8);
  assert.deepEqual(await page.evaluate(()=>contextCounts),{output:1,decoder:1});
  await page.evaluate(()=>ctx.close());assert.equal(await page.evaluate(()=>ctx.state),'closed');
  console.log(`HABITAT LIFECYCLE PASS ${width}px: winter insect silence, rare winter coyote, real stale-decode cancellation, hidden/mute/disposal, one output context and one fixed-rate decoder`);
  await page.close();
 }
}finally{await browser.close();}
console.log('HABITAT MEDIA COMPLETE: both widths; six immutable recorded clips; 1835 preservation and 1812 spring/summer/winter playback; no actual-town or listening-quality claim');
