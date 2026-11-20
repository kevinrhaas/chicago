// Real R2 bytes, Web Audio and spatial mixer at both viewports. Actor positions
// are controlled fixtures here; actual mesh anchors have separate assembly tests.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = async file => JSON.parse(await fs.readFile(path.join(root, file), 'utf8'));
const catalog = await read('renderers/web/audio/catalog.json'), policy = await read('tools/audio-hosting.json');
const selected = catalog.assets.filter(a => a.scene_placement?.mode === 'moving-transport');
for (const a of selected) a.url = new URL(`media/${a.delivery.sha256}${path.extname(a.url)}`, policy.public_base).href;
let pw; try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const fixture = `<!doctype html><button id="on">Sound on</button><script type="module">
import {createRecordedAudio} from '/recorded-audio.js';
const catalog=${JSON.stringify(catalog)};
window.env={camera:{position:{x:0,y:2,z:0},quaternion:{x:0,y:0,z:0,w:1}},time:{date:'1835-07-01'},
 transport:[{id:'western_hotel_driven_wagon_loop_1835',scene:'1835',moving:true,speed:1.3,
 anchors:{harness:{x:3,y:0,z:2},wagon:{x:3,y:0,z:5}}}]};
window.enabled=false;window.clock=0;window.meter=null;window.year='1835';
window.sync=()=>engine.sync({active:enabled,effectsOn:true,ambienceOn:false,musicOn:false,year});
document.getElementById('on').onclick=()=>{
 const ctx=new AudioContext({sampleRate:96000});ctx.resume();window.ctx=ctx;
 const effects=ctx.createGain();window.meter=ctx.createAnalyser();effects.connect(meter);meter.connect(ctx.destination);
 window.engine=createRecordedAudio({ctx,effects,ambience:ctx.createGain(),music:ctx.createGain(),environment:()=>env,now:()=>clock,
 fetcher:(url,opts)=>String(url).endsWith('catalog.json')?Promise.resolve({ok:true,json:async()=>catalog}):fetch(url,opts)});
 enabled=true;window.timer=setInterval(sync,100);sync();
};
window.peak=()=>{if(!meter)return 0;const samples=new Float32Array(meter.fftSize);meter.getFloatTimeDomainData(samples);return Math.max(...samples.map(Math.abs));};
</script>`;
const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.https_proxy || process.env.http_proxy;
const u = proxyUrl ? new URL(proxyUrl) : null;
const proxy = u ? {server:u.origin,...(u.username?{username:decodeURIComponent(u.username),password:decodeURIComponent(u.password)}:{})} : undefined;
const browser = await pw.chromium.launch({proxy,executablePath:process.env.PW_EXECUTABLE??'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try {
 for (const width of [390,1280]) {
  const page = await browser.newPage({viewport:{width,height:width===390?780:800}}), requests=[], errors=[];
  page.on('request',r=>{if(r.url().startsWith(policy.public_base)) requests.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(policy.origin+'/**',async route=>{
   const name=new URL(route.request().url()).pathname.slice(1);
   if(name==='fixture')return route.fulfill({contentType:'text/html',body:fixture});
   if(['recorded-audio.js','transport-audio.js','habitat-audio.js','habitat-seasons.js','hoof-contact-events.js','work-audio.js','habitat-town.js','wind-gust.js'].includes(name))
    return route.fulfill({contentType:'text/javascript',body:await fs.readFile(path.join(root,'renderers/web/js',name),'utf8')});
   return route.fulfill({status:404});
  });
  await page.goto(policy.origin+'/fixture');await page.waitForTimeout(200);assert.equal(requests.length,0);
  await page.click('#on');
  await page.waitForFunction(()=>engine.state.transport.voices.length===2&&peak()>1e-6,null,{timeout:45000,polling:50});
  let state=await page.evaluate(()=>({audio:engine.state,rate:ctx.sampleRate}));
  assert.equal(state.rate,96000);assert(state.audio.decodedBytes<=8*1024*1024);assert.deepEqual(state.audio.errors,[]);
  assert.equal(requests.length,2);
  const near=state.audio.transport.sources.find(c=>c.asset==='horse-harness');
  await page.evaluate(()=>{env.transport[0].anchors.harness.x=20;sync();});
  state=await page.evaluate(()=>engine.state);
  const far=state.transport.sources.find(c=>c.asset==='horse-harness');
  assert.equal(far.anchor.x,20);assert(far.gain<near.gain);
  await page.evaluate(()=>{env.transport[0].moving=false;sync();});
  await page.waitForFunction(()=>!engine.state.transport.voices.length&&peak()<1e-6,null,{timeout:5000});
  await page.evaluate(()=>{env.transport[0].moving=true;clock+=10000;sync();});
  await page.waitForFunction(()=>engine.state.transport.voices.length===2&&peak()>1e-6);
  await page.evaluate(()=>{enabled=false;sync();});
  await page.waitForTimeout(150);
  assert(await page.evaluate(()=>!engine.state.voices.length&&engine.state.decodedBytes===0&&peak()<1e-6));
  assert.equal(requests.length,2,'motion restart reuses decoded buffers');
  assert.deepEqual(errors,[]);
  await page.evaluate(()=>{clearInterval(timer);engine.dispose();ctx.close();});await page.close();
  console.log(`TRANSPORT MEDIA PASS ${width}px: both real R2 clips, moving source attenuation, stopped silence, restart, mute, <=8MiB at96kHz output, zero page errors`);
 }
}finally{await browser.close();}
