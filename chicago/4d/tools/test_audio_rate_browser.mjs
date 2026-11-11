// T-3532: real media and bounded decoded memory at high hardware sample rates.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hostedCatalog } from './audio_hosting.mjs';
let pw;
try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const { chromium } = pw;

const root=fileURLToPath(new URL('../renderers/web/', import.meta.url)).replace(/\/$/, '');
const origin='https://chicago.polecat.live';
const { catalog } = hostedCatalog();
const selectedRiver=catalog.assets.find(a=>a.id==='river'),heldRiver=catalog.assets.find(a=>a.id==='river-held');
assert.equal(selectedRiver.runtime_enabled,true);assert.equal(heldRiver.runtime_enabled,false);
assert.equal(selectedRiver.delivery.sha256,'6831b7ad102ec023194c4040776c5245b6cb47451d652a94a07dc742e28362af');
catalog.water_zones={'1835':{epoch:'test',features:[
 {kind:'river',polygon:[[[0,-100],[100,-100],[100,100],[0,100],[0,-100]]]},
 {kind:'slough',width_m:10,line:[[300,-100],[300,100]]}
]}};
const fixture=`<!doctype html><button id="on">On</button><script type="module">
import {createRecordedAudio} from '/js/recorded-audio.js';
window.requestedRate=Number(new URL(location.href).searchParams.get('rate'));
window.mode='wind';window.analyser=null;window.ctx=null;window.engine=null;
const environment=()=>({season:mode==='wind'?'summer':'winter',camera:{position:{x:mode==='slough'?300:mode==='lake'?200:0,y:2,z:0}},
terrain:{loaded:mode!=='wind',epochId:'test',heightfield:{contains:()=>true},
isWater:x=>x>=20,lakeShore:{n0:-100,step:100,e:[100,100,100]}}});
document.getElementById('on').onclick=()=>{
 ctx=new AudioContext({sampleRate:requestedRate});ctx.resume();
 const ambience=ctx.createGain(),music=ctx.createGain();
 analyser=ctx.createAnalyser();ambience.connect(analyser);analyser.connect(ctx.destination);
 engine=createRecordedAudio({ctx,ambience,music,environment});
 engine.sync({active:true,ambienceOn:true,musicOn:false,year:'1835'});
};
window.samplePeak=()=>{const v=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(v);return Math.max(...v.map(Math.abs));};
</script>`;

const proxyURL=process.env.HTTPS_PROXY||process.env.HTTP_PROXY||process.env.https_proxy||process.env.http_proxy;
const proxyInfo=proxyURL?new URL(proxyURL):null;
const proxy=proxyInfo?{server:proxyInfo.origin,...(proxyInfo.username?{username:decodeURIComponent(proxyInfo.username),password:decodeURIComponent(proxyInfo.password)}:{})}:undefined;
const browser=await chromium.launch({proxy,executablePath:process.env.PW_EXECUTABLE??'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const results=[];
try {
 for(const rate of [96000,192000]) {
  const page=await browser.newPage(),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.url().startsWith(catalog.hosting.public_base))requests.push(r.url());});
  await page.route(origin+'/**',async route=>{
   const url=new URL(route.request().url());
   if(url.pathname==='/fixture')return route.fulfill({contentType:'text/html',body:fixture});
   if(url.pathname==='/audio/catalog.json')return route.fulfill({contentType:'application/json',body:JSON.stringify(catalog)});
   const file=path.resolve(root,'.'+url.pathname);
   if(!file.startsWith(root+path.sep))return route.abort();
   try{return route.fulfill({contentType:'text/javascript',body:await fs.readFile(file)});}catch{return route.fulfill({status:404,body:'Missing'});}
  });
  await page.goto(origin+'/fixture?rate='+rate);
  await page.click('#on');
  await page.waitForFunction(()=>engine?.state.voices.includes('wind'),null,{timeout:30000});
  await page.waitForFunction(()=>samplePeak()>0.000001,null,{timeout:30000});
  const first=await page.evaluate(()=>({rate:ctx.sampleRate,state:engine.state,peak:samplePeak()}));
  assert.equal(first.rate,rate);
  assert.equal(first.state.decodedBytes,4224000);
  const waterPeaks={};
  for(const [mode,bytes] of [['river',8448000],['lake',12672000]]) {
   await page.evaluate(m=>{window.mode=m;window.changedAt=ctx.currentTime;engine.update();},mode);
   await page.waitForFunction(m=>engine.state.voices.includes(m),mode,{timeout:30000});
   // Winter removes wind; wait beyond the previous source's 1.5 s stop fade.
   // A nonzero master signal now proves this water recording, not leftover wind.
   await page.waitForFunction(()=>ctx.currentTime-changedAt>2&&samplePeak()>0.000001,null,{timeout:30000});
   assert.deepEqual(await page.evaluate(()=>engine.state.voices),[mode]);
   assert.equal(await page.evaluate(()=>engine.state.decodedBytes),bytes);
   waterPeaks[mode]=await page.evaluate(()=>samplePeak());
  }
  const all=await page.evaluate(()=>engine.state);
  assert.deepEqual(all.errors,[]);assert.deepEqual(errors,[]);
  assert.deepEqual([...new Set(requests)].sort(),catalog.assets.filter(a=>['wind','river','lake'].includes(a.id)).map(a=>a.url).sort(),
   'only the three eligible environmental deliveries are requested');
  assert(!requests.includes(heldRiver.url),'the rejected old recording is never fetched');
  const count=requests.length;
  await page.evaluate(()=>{window.mode='slough';engine.update();});
  assert.deepEqual(await page.evaluate(()=>engine.state.voices),[],'sloughs do not borrow the new river or lake waves');
  assert.equal(requests.length,count);
  await page.evaluate(()=>engine.sync({active:false,ambienceOn:true,musicOn:false,year:'1835'}));
  assert.equal(await page.evaluate(()=>engine.state.decodedBytes),0);
  await page.evaluate(async()=>{engine.dispose();await ctx.close();});
  results.push({hardwareRate:rate,firstDecodedBytes:first.state.decodedBytes,firstPeak:first.peak,waterPeaks,allDecodedBytes:all.decodedBytes,heldRiverFetched:false,errors,deliveries:requests});
  console.log('FIXED DECODE BROWSER PASS '+rate+'Hz: actual R2 wind/selected river/lake, rejected river not fetched, 4,224,000 bytes per22s loop, 12,672,000-byte cache, isolated nonzero water signals, slough quiet, mute releases cache');
  await page.close();
 }
 if (process.env.AUDIO_RATE_REPORT) await fs.writeFile(process.env.AUDIO_RATE_REPORT,JSON.stringify(results,null,2)+'\n');
} finally {await browser.close();}
