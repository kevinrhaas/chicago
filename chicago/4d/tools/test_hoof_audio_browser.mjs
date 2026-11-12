// SPDX-License-Identifier: GPL-3.0-or-later
// Real R2 media / real WebAudio. Positions, epochs and distance frames are
// controlled fixtures; this does NOT certify the native town or perceived sync.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = async file => JSON.parse(await fs.readFile(path.join(root, file), 'utf8'));
const policy = await read('tools/audio-hosting.json'), catalog = await read('assets/audio/catalog.json');
const assets = catalog.assets.filter(a => ['horse-harness', 'wood-wagon', 'horse-walking'].includes(a.id));
assert.equal(assets.length, 3);
for (const asset of assets) {
  assert.equal(asset.runtime_enabled, true, `${asset.id} must be enabled in the source catalog`);
  asset.url = new URL(`media/${asset.delivery.sha256}${path.extname(asset.url)}`, policy.public_base).href;
}
const reportDir = path.resolve(process.env.HOOF_AUDIO_REPORT_DIR ?? '/tmp/chicago-hoof-audio-browser');
await fs.mkdir(reportDir, { recursive: true });
let pw; try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH ?? '/workspace/audio-tooling/node_modules', 'playwright/index.mjs')); }
const meterCode = `class Meter extends AudioWorkletProcessor {
 constructor(){super();this.collect=false;this.previous=0;this.clear();this.port.onmessage=({data})=>{
  if(data.action==='begin'){this.clear();this.collect=true;this.port.postMessage({id:data.id,ok:true});}
  if(data.action==='end'){this.collect=false;this.port.postMessage({id:data.id,peak:this.peak,
   rms:Math.sqrt(this.energy/Math.max(1,this.count)),derivativeRms:Math.sqrt(this.derivative/Math.max(1,this.count)),
   frames:this.count,seconds:this.count/sampleRate,workletSampleRate:sampleRate});}
 };}
 clear(){this.peak=0;this.energy=0;this.derivative=0;this.count=0;this.previous=0;}
 process(inputs,outputs){const input=inputs[0]??[],output=outputs[0];
  for(let ch=0;ch<output.length;ch++)output[ch].set(input[ch]??input[0]??new Float32Array(output[ch].length));
  if(this.collect&&input.length){for(let i=0;i<input[0].length;i++){
   const x=(input[0][i]+(input[1]?.[i]??input[0][i]))/2;
   this.peak=Math.max(this.peak,Math.abs(x));this.energy+=x*x;
   this.derivative+=(x-this.previous)**2;this.previous=x;this.count++;
  }}return true;}
}registerProcessor('meter',Meter);`;
function fixture(rate) { return `<!doctype html><meta charset="utf-8"><title>Recorded hoof fixture</title>
<p>Standalone real-media audio test. Controlled actor phases, not the native town.</p><button id="on">Enable sound</button>
<script type="module">
import {createTransportAudio} from '/transport-audio.js';
import {WALK_V2_CONTACTS as gait} from '/hoof-contact-events.js';
const allAssets=${JSON.stringify(assets)};
const ids=['fort_wagon_loop_1812','shore_road_wagon_haul_1812'];
const point={x:0,y:0,z:-2};
const horse=(id='right',distanceM=.2)=>({id,distanceM,strideM:gait.strideM,
 clipSha256:gait.clipSha256,modelSha256:gait.modelSha256,
 hooves:Object.fromEntries(gait.contacts.map(c=>[c.foot,{...point}]))});
const actor=(id,epoch='initial',single=false)=>({id,scene:'1812',moving:true,speed:1.3,
 anchors:{harness:{...point},wagon:{...point},hoof:{epoch,horses:single?[horse()]:[horse('left'),horse('right')]}}});
window.env={camera:{position:{x:0,y:1.6,z:0}},season:'summer',snowCover:0,
 time:{date:'1812-08-14'},transport:ids.map(id=>actor(id))};
let selected=allAssets,clock=0,probeId=0,meterId=0;
const pending=new Map(),encoded=new Map();
window.deliveries=[];window.starts=[];window.filters=[];window.gains=[];window.decodeRates=[];
window.environmentReads=0;window.ready=false;
const request=action=>new Promise(resolve=>{const id=++meterId;pending.set(id,resolve);meter.port.postMessage({id,action});});
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const frame=(enabled=true)=>{clock+=16;engine.frame({enabled,year:'1812'});};
const setDistance=d=>{for(const a of env.transport)for(const h of a.anchors.hoof.horses)h.distanceM=d;};
window.pump=()=>{clock=Math.max(clock+1,performance.now());engine.sync({enabled:true,year:'1812'});engine.frame({enabled:true,year:'1812'});return engine.state;};
document.querySelector('#on').onclick=async()=>{
 try{
  window.ctx=new AudioContext({sampleRate:${rate}});await ctx.resume();
  const blob=new Blob([${JSON.stringify(meterCode)}],{type:'text/javascript'});
  const url=URL.createObjectURL(blob);await ctx.audioWorklet.addModule(url);URL.revokeObjectURL(url);
  window.meter=new AudioWorkletNode(ctx,'meter',{outputChannelCount:[2]});
  meter.port.onmessage=({data})=>{pending.get(data.id)?.(data);pending.delete(data.id);};meter.connect(ctx.destination);
  window.output=ctx.createGain();output.connect(meter);
  const source=ctx.createBufferSource.bind(ctx),gain=ctx.createGain.bind(ctx),filter=ctx.createBiquadFilter.bind(ctx);
  ctx.createBufferSource=()=>{const s=source(),start=s.start.bind(s);s.start=(...args)=>{
   starts.push({bufferDuration:s.buffer.duration,bufferRate:s.buffer.sampleRate,bufferFrames:s.buffer.length,
    loop:s.loop,playbackRate:s.playbackRate.value,args});return start(...args);};return s;};
  ctx.createGain=()=>{const g=gain();gains.push(g);return g;};
  ctx.createBiquadFilter=()=>{const f=filter();filters.push(f);return f;};
  window.decoder=new OfflineAudioContext(1,1,48000);
  window.engine=createTransportAudio({ctx,output,catalog:()=>({assets:selected}),now:()=>clock,random:()=>0,
   environment:()=>{environmentReads++;return env;},
   decodeAudio:async bytes=>{const b=await decoder.decodeAudioData(bytes);decodeRates.push(b.sampleRate);return b;},
   fetcher:async(url,options)=>{const r=await fetch(url,options);if(!r.ok)throw Error('R2 '+r.status);
    const bytes=await r.arrayBuffer(),asset=allAssets.find(a=>a.url===String(url));
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(!asset||hash!==asset.delivery.sha256||bytes.byteLength!==asset.delivery.bytes)throw Error('fixture delivery hash/size mismatch');
    deliveries.push({id:asset.id,url:String(url),bytes:bytes.byteLength,sha256:hash});encoded.set(asset.id,bytes);
    return{ok:true,arrayBuffer:async()=>bytes.slice(0)};
   }});
  ready=true;pump();
 }catch(error){window.setupError=String(error.stack??error);}
};
window.isolate=async()=>{
 selected=allAssets.filter(a=>a.id==='horse-walking');env.transport=[actor(ids[0],'isolated',true)];
 pump();await delay(220);return engine.state;
};
window.probe=async snow=>{
 // Vary actual renderer input at fixed fixture date/position to isolate the
 // filter. Native seasonal dates and town poses are verified separately.
 env.snowCover=snow;env.transport=[actor(ids[0],'probe-'+(++probeId),true)];
 frame();const g0=gains.length,f0=filters.length,s0=starts.length;
 await request('begin');setDistance(.22);frame();
 const state=engine.state,profile=filters.slice(f0).map(f=>({type:f.type,hz:f.frequency.value,Q:f.Q.value}));
 const actualGains=gains.slice(g0).map(g=>g.gain.value);
 await delay(400);const signal=await request('end');
 return{signal,state,profile,actualGains,starts:starts.slice(s0),position:{...point}};
};
window.hiddenAndStale=async()=>{
 env.transport=[actor(ids[0],'hidden-test',true)];frame();setDistance(.22);frame();
 const before=engine.state.contactVoices,reads=environmentReads;frame(false);
 const hidden={before,after:engine.state.contactVoices,readDelta:environmentReads-reads};
 await delay(180);await request('begin');setDistance(.47);frame();await delay(180);
 const resumed=await request('end'),afterResume=engine.state.contactVoices;
 env.transport=[actor(ids[0],'gap-test',true)];frame();clock+=1000;setDistance(.22);frame();
 await request('begin');await delay(160);const gap=await request('end');
 return{hidden,resumed,afterResume,gap,afterGap:engine.state.contactVoices};
};
window.withMechanics=()=>{
 selected=allAssets;env.snowCover=0;env.transport=ids.map(id=>actor(id,'mechanics-again'));
 pump();frame();setDistance(.22);frame();return engine.state;
};
window.mute=async()=>{
 engine.sync({enabled:false,year:'1812'});await delay(180);await request('begin');await delay(160);
 return{state:engine.state,signal:await request('end')};
};
window.staleRealDecode=async()=>{
 // A second isolated player re-decodes the SAME already-fetched real encoded
 // bytes. No second R2 request, no mock buffer and no synthetic contact signal.
 let release,started=false;const hold=new Promise(resolve=>{release=resolve;});
 const stale=createTransportAudio({ctx,output,catalog:()=>({assets:allAssets.filter(a=>a.id==='horse-walking')}),
  now:()=>clock,environment:()=>env,
  fetcher:async()=>({ok:true,arrayBuffer:async()=>encoded.get('horse-walking').slice(0)}),
  decodeAudio:async bytes=>{const b=await decoder.decodeAudioData(bytes);started=true;await hold;return b;}});
 env.transport=[actor(ids[0],'late-decode',true)];stale.sync({enabled:true,year:'1812'});stale.frame({enabled:true,year:'1812'});
 const deadline=performance.now()+10000;while(!started){if(performance.now()>deadline)throw Error('stale real decode timeout');await delay(10);}
 stale.sync({enabled:false,year:'1812'});const held=stale.state;
 release();while(stale.state.loading){if(performance.now()>deadline)throw Error('stale completion timeout');await delay(10);}
 const finished=stale.state;await request('begin');await delay(160);const signal=await request('end');stale.dispose();
 return{held,finished,signal,media:'same verified R2 bytes replayed in memory, actual OfflineAudioContext decode'};
};
</script>`; }
const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.https_proxy || process.env.http_proxy;
const proxyURL = proxyUrl ? new URL(proxyUrl) : null;
const proxy = proxyURL ? { server: proxyURL.origin,
  ...(proxyURL.username ? { username: decodeURIComponent(proxyURL.username), password: decodeURIComponent(proxyURL.password) } : {}) } : undefined;
const report = { kind: 'standalone-real-media-controlled-phase-fixture-not-native-town', listening_performed: false,
  source_hashes: Object.fromEntries(assets.map(a => [a.id, a.delivery.sha256])), viewports: [] };
const modules = ['transport-audio.js', 'hoof-contact-events.js'];
report.module_hashes = Object.fromEntries(await Promise.all(modules.map(async name => [name,
  createHash('sha256').update(await fs.readFile(path.join(root, 'renderers/web/js', name))).digest('hex')])));
const browser = await pw.chromium.launch({ proxy, executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium',
  headless: true, args: ['--no-sandbox'] });
try {
  for (const config of [{ width: 390, height: 780, rate: 96000 }, { width: 1280, height: 800, rate: 192000 }]) {
    const page = await browser.newPage({ viewport: { width: config.width, height: config.height } });
    const errors = [], requests = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('request', r => { if (r.url().startsWith(policy.public_base)) requests.push(r.url()); });
    await page.route(policy.origin + '/**', async route => {
      const name = new URL(route.request().url()).pathname.slice(1);
      if (name === 'hoof-fixture') return route.fulfill({ contentType: 'text/html', body: fixture(config.rate) });
      if (name === 'favicon.ico') return route.fulfill({ status: 204 });
      if (modules.includes(name)) return route.fulfill({ contentType: 'text/javascript', body: await fs.readFile(path.join(root, 'renderers/web/js', name), 'utf8') });
      return route.fulfill({ status: 404 });
    });
    const result = { ...config, requests, errors };
    report.viewports.push(result);
    await page.goto(policy.origin + '/hoof-fixture'); await page.waitForTimeout(150);
    assert.equal(requests.length, 0, 'no media before the gesture');
    await page.click('#on');
    await page.waitForFunction(() => window.ready || window.setupError, null, { timeout: 15000 });
    assert.equal(await page.evaluate(() => window.setupError ?? null), null);
    await page.waitForFunction(() => { const s = pump(); return s.voices.length === 4 && s.contactDecodedBytes === 55296; }, null, { timeout: 60000, polling: 50 });
    result.loaded = await page.evaluate(() => ({ state: engine.state, outputRate: ctx.sampleRate, decodeRates, deliveries }));
    assert.equal(result.loaded.outputRate, config.rate);
    assert(result.loaded.decodeRates.every(rate => rate === 48000));
    assert.equal(result.loaded.state.contactVoices, 0, 'steady pose never produces a beat');
    assert.equal(result.loaded.state.decodedBytes, 6792612);
    assert.equal(result.loaded.state.peakDecodedBytes, 8824988);
    assert.equal(result.loaded.deliveries.filter(d => d.id === 'horse-walking').length, 1);
    assert.equal(requests.length, 3, 'one network fetch for each original recording');
    const isolated = await page.evaluate(() => isolate()); assert.equal(isolated.voices.length, 0);
    result.dry = await page.evaluate(() => probe(0));
    result.snow = await page.evaluate(() => probe(1));
    for (const [name, probe] of [['dry', result.dry], ['snow', result.snow]]) {
      assert.equal(probe.state.contactVoices, 1, `${name}: one real phase contact`);
      assert(probe.signal.peak > 1e-5 && probe.signal.rms > 1e-6, `${name}: nonzero actual WebAudio signal`);
      assert.equal(probe.signal.workletSampleRate, config.rate);
      assert.equal(probe.starts.length, 1); const start = probe.starts[0];
      assert.equal(start.bufferRate, 48000); assert.equal(start.bufferFrames, 6144);
      assert.equal(start.loop, false); assert.equal(start.playbackRate, 1);
      assert.equal(start.args[1], 0); assert.equal(start.args[2], .128);
    }
    assert.deepEqual(result.dry.position, result.snow.position);
    assert.equal(result.dry.profile[0].hz, 18000); assert.equal(result.snow.profile[0].hz, 900);
    assert(Math.abs(result.snow.actualGains[1] / result.dry.actualGains[1] - .55) < 1e-6);
    assert(result.snow.signal.rms < result.dry.signal.rms * .8, 'snow processing measurably damps the same real contact');
    result.cleanup = await page.evaluate(() => hiddenAndStale());
    assert.equal(result.cleanup.hidden.before, 1); assert.equal(result.cleanup.hidden.after, 0);
    assert.equal(result.cleanup.hidden.readDelta, 0, 'disabled frame avoids scene snapshot');
    assert.equal(result.cleanup.afterResume, 0); assert.equal(result.cleanup.afterGap, 0);
    assert(result.cleanup.resumed.peak < 1e-6 && result.cleanup.gap.peak < 1e-6);
    result.withMechanics = await page.evaluate(() => withMechanics());
    assert.equal(result.withMechanics.voices.length, 6); assert.equal(result.withMechanics.contactVoices, 2);
    assert.equal(result.withMechanics.voices.filter(key => !key.startsWith('hoof:')).length, 4);
    assert(result.withMechanics.peakDecodedBytes <= 10 * 1024 * 1024);
    result.muted = await page.evaluate(() => mute());
    assert.equal(result.muted.state.voices.length, 0); assert.equal(result.muted.state.decodedBytes, 0);
    assert(result.muted.signal.peak < 1e-6);
    result.staleDecode = await page.evaluate(() => staleRealDecode());
    assert.equal(result.staleDecode.held.loading, 1);
    assert.equal(result.staleDecode.finished.loading, 0); assert.equal(result.staleDecode.finished.decodedBytes, 0);
    assert.equal(result.staleDecode.finished.voices.length, 0); assert(result.staleDecode.signal.peak < 1e-6);
    assert.equal(requests.length, 3, 'phase/proxy/lifecycle tests do not refetch the originals');
    assert.deepEqual(result.loaded.state.errors, []); assert.deepEqual(result.withMechanics.errors, []);
    assert.deepEqual(result.staleDecode.finished.errors, []); assert.deepEqual(errors, []);
    await page.evaluate(async () => { engine.dispose(); meter.disconnect(); await ctx.close(); });
    await page.close();
    result.pass = true;
    await fs.writeFile(path.join(reportDir, 'hoof-browser-report.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(`HOOF MEDIA PASS ${config.width}px/${config.rate}Hz: actual R2 contact signal, 48kHz cuts, dry/snow damping, 4+2 voices, mute/stale cleanup, one original fetch, zero errors`);
  }
  report.pass = true;
} catch (error) {
  report.pass = false; report.failure = String(error.stack ?? error); throw error;
} finally {
  await fs.writeFile(path.join(reportDir, 'hoof-browser-report.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
}
