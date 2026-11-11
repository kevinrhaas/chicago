// Focused real-media/decoder check. Habitat geometry in this fixture is synthetic;
// actual dated species records and uploaded immutable files are real. This is not
// the full-town geometry, mobile-device or listening-quality acceptance gate.
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
let pw; try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const origin = policy.origin;
const fixture = `<!doctype html><button id="on">Enable sound</button><script type="module">
import {createHabitatAudio} from '/habitat-audio.js';
const catalog=${JSON.stringify(catalog)},zones=${JSON.stringify(zones)};
let engine,ctx,clock=0,env;
window.issues=[];
window.setMode=id=>{
 env={season:'summer',time:{date:'1835-07-01',hhmm:id==='summer-crickets'?'22:00':'15:00'},
 sunElevation:id==='summer-crickets'?-20:45,faunaZones:zones,
 camera:{position:{x:0,y:2,z:0},quaternion:{x:0,y:0,z:0,w:1}},
 flora:{zoneAt:()=>id==='redwing-call'?'z04_marsh':'z01_wet_prairie'},
 terrain:{loaded:true,surfaceHeight:()=>0,height:()=>4,heightfield:{contains:()=>true}}};
 engine.reset();clock+=50000;engine.sync({enabled:true,year:'1835'});
 clock+=30000;engine.sync({enabled:true,year:'1835'});
};
document.getElementById('on').onclick=()=>{
 ctx=new AudioContext({sampleRate:96000});ctx.resume();
 const output=ctx.createGain();output.gain.value=.5;
 window.meter=ctx.createAnalyser();output.connect(meter);meter.connect(ctx.destination);
 engine=createHabitatAudio({ctx,output,catalog:()=>catalog,environment:()=>env,now:()=>clock,
 random:()=>.5,onError:message=>issues.push(message)});
 window.engine=engine;window.outputRate=ctx.sampleRate;
 setMode('summer-cicada-proxy');
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
   if(url.pathname==='/habitat-audio.js') return route.fulfill({contentType:'text/javascript',body:await fs.readFile(path.join(root,'renderers/web/js/habitat-audio.js'),'utf8')});
   return route.fulfill({status:404,body:'Not found'});
  });
  await page.goto(origin+'/fixture');await page.waitForTimeout(200);assert.equal(requests.length,0);
  await page.click('#on');
  for(const id of ['summer-cicada-proxy','summer-crickets','redwing-call']) {
   if(id!=='summer-cicada-proxy') await page.evaluate(id=>setMode(id),id);
   await page.waitForFunction(id=>engine.state.voices.includes(id)&&peak()>0.000001,id,{timeout:30000,polling:50});
   const state=await page.evaluate(()=>({state:engine.state,outputRate,issues}));
   assert.equal(state.outputRate,96000);
   assert(state.state.decodedBytes<=24*48000*4);
   const asset=catalog.assets.find(a=>a.id===id);
   assert(Math.abs(state.state.decodedBytes-asset.duration_s*48000*4)<48000,'clip stays48kHz despite96kHz output');
   assert.equal(!!state.state.anchor,id==='redwing-call');assert.deepEqual(state.issues,[]);
   console.log(`HABITAT MEDIA PASS ${width}px ${id}: live R2, nonzero samples, ${state.state.decodedBytes} decoded bytes at96kHz output`);
  }
  await page.evaluate(()=>engine.sync({enabled:false,year:'1835'}));await page.waitForTimeout(150);
  assert(await page.evaluate(()=>!engine.state.voices.length&&engine.state.decodedBytes===0&&peak()<0.000001));
  assert.equal(requests.length,3);assert.deepEqual(errors,[]);
  await page.evaluate(()=>engine.dispose());await page.close();
 }
}finally{await browser.close();}

console.log('HABITAT MEDIA COMPLETE: corrected surface API; both widths; all three real R2 clips; fixed48kHz buffers at96kHz output; mute/cache/disposal and zero page errors');
