#!/usr/bin/env node
/** T-1247 browser acceptance, against the generated visitor mirror.
 * NODE_PATH=<playwright module root> PW_EXECUTABLE=<chromium> node tools/measure_arrival.mjs
 * Captures are written to ARRIVAL_EVIDENCE (default /tmp/arrival-evidence).
 * Real cold boot: 390x780 touch/light, CPU 4x, Fast 3G (1.6 Mbps / 150ms).
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../site/4d');
const out = process.env.ARRIVAL_EVIDENCE || '/tmp/arrival-evidence';
fs.mkdirSync(out, { recursive: true });
const pwRoot = process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' }).trim();
const { chromium } = await import(path.join(pwRoot, 'playwright/index.mjs'));
const mime = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.json':'application/json', '.wasm':'application/wasm' };
const cache = new Map();
const server = http.createServer((req,res) => {
  let name = decodeURIComponent(req.url.split('?')[0]); if (name.endsWith('/')) name += 'index.html';
  const file = path.resolve(root, '.' + name);
  if (!file.startsWith(root + '/')) { res.writeHead(403).end(); return; }
  try { if (!cache.has(file)) cache.set(file, zlib.gzipSync(fs.readFileSync(file)));
    res.writeHead(200, { 'Content-Type':mime[path.extname(file)] || 'application/octet-stream', 'Content-Encoding':'gzip' }); res.end(cache.get(file));
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => server.listen(0,'127.0.0.1',r));
const url = `http://127.0.0.1:${server.address().port}/walk/?year=1835`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args:['--no-sandbox','--enable-unsafe-swiftshader'] });
const results = { browser: browser.version(), measuredAt: new Date().toISOString(), cases:[] };
function observe() {
  localStorage.setItem('chicago4d.settings', JSON.stringify({ detail:'light' }));
  window.arrivalProbe = [];
  addEventListener('DOMContentLoaded', () => {
    const year = document.getElementById('arrival-year');
    const read = () => { const a = window.__chicago4d; window.arrivalProbe.push({at:performance.now(), year:Number(year.dataset.year), ready:!!a?.ready, phase:document.getElementById('gate-sub').textContent}); };
    new MutationObserver(read).observe(year,{attributes:true,attributeFilter:['data-year']}); read();
  });
}
async function bootCase(name, { slow=false, reduced=false, fail=null } = {}) {
  const ctx = await browser.newContext({ viewport:{width:390,height:780}, hasTouch:true, reducedMotion:reduced?'reduce':'no-preference' });
  await ctx.addInitScript(observe);
  const page = await ctx.newPage(); const errors=[]; page.on('pageerror', e=>errors.push(e.message));
  if (fail) await page.route(fail === 'terrain' ? '**/terrain.js' : '**/people.json', route => {
    if(fail==='terrain') return route.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.join(root,'walk/js/terrain.js'),'utf8').replace('const heightfield = new Heightfield();','throw new Error("forced terrain failure"); const heightfield = new Heightfield();')});
    return route.fulfill({status:503,body:'forced optional failure'});
  });
  if (slow) { const cdp=await ctx.newCDPSession(page); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4}); await cdp.send('Network.enable'); await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:1.6e6/8,uploadThroughput:750e3/8}); }
  console.log(`START ${name}`);
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:120000});
  if (fail==='terrain') await page.waitForFunction(()=>window.__chicago4d?.arrival.state.failed,{},{timeout:120000});
  else {
    // Six actual loading/arrival stills; repeat stages on very fast hosts are honest.
    for(const [i, threshold] of [2026, 1990, 1940, 1890, 1840].entries()) {
      if(!slow) break;
      await page.waitForFunction(t=>Number(document.getElementById('arrival-year').dataset.year)<=t,threshold,{timeout:180000});
      await page.screenshot({path:path.join(out,`${name}-${i+1}.png`)});
    }
    await page.waitForFunction(()=>window.__chicago4d?.ready && document.getElementById('arrival-year').dataset.year==='1835',{},{timeout:180000});
  }
  await page.waitForTimeout(400);
  const data=await page.evaluate(()=>({probe:window.arrivalProbe,state:window.__chicago4d.arrival.state,phases:window.__chicago4d.boot.timings(),readyAt:window.__chicago4d.boot.readyAt,copy:document.getElementById('gate-sub').textContent,button:document.getElementById('gate-btn').textContent,disabled:document.getElementById('gate-btn').disabled,hidden:document.getElementById('arrival-year').getAttribute('aria-hidden'),animations:document.getElementById('arrival-year').getAnimations({subtree:true}).length}));
  const ys=data.probe.filter(x=>Number.isFinite(x.year)&&x.year>0);
  assert.ok(ys.every((x,i)=>!i || x.year<=ys[i-1].year),'year never rolls forward');
  assert.ok(ys.every(x=>x.year>=1836||x.ready),'1835 requires api.ready');
  assert.equal(data.hidden,'true'); assert.deepEqual(errors,[]);
  if(fail==='terrain'){assert.match(data.copy,/forced terrain failure/);assert.doesNotMatch(data.copy,/arrived/);assert.equal(data.button,'Retry'); assert.ok(data.state.year>=1836);}
  else {if(fail==='people') assert.ok(data.phases.find(p=>p.id==='people').error,'optional failure was actually injected');assert.equal(data.copy,'You have arrived in Chicago, summer 1835.');assert.equal(data.state.year,1835);assert.equal(data.disabled,false);}
  if(reduced){assert.ok(new Set(ys.map(x=>x.year)).size<=5);assert.equal(data.animations,0);}
  await page.screenshot({path:path.join(out,`${name}-6.png`)});
  results.cases.push({name,...data,errors});
  console.log(`PASS ${name}: ${ys.length} year readings, ${data.copy}`);
  if(name==='cold'){
    // Long-text layout checks retain the real gate and styles, with the renderer
    // paused so software WebGL does not dominate screenshot timing.
    await page.evaluate(()=>window.__chicago4d.renderer.setAnimationLoop(null));
    for(const width of [320,390,1280]) for(const theme of ['light','dark']){
      await page.setViewportSize({width,height:width===1280?800:780});
      const layout=await page.evaluate(({theme})=>{ document.documentElement.dataset.theme=theme;
        const label=document.getElementById('gate-sub'), card=document.getElementById('arrival-card');
        label.textContent='Reading the reconstructed city and its carefully documented sources now';
        card.textContent='Drawing on previously researched sources, maps, newspapers and accounts to reconstruct the streets of Chicago in summer 1835.';
        const nodes=['gate-title','arrival-year','arrival-card','gate-sub','gate-btn'].map(id=>{const el=document.getElementById(id),r=el.getBoundingClientRect();return {id,left:r.left,right:r.right,top:r.top,bottom:r.bottom};});
        return {nodes,width:innerWidth,live:[...document.querySelectorAll('#gate [aria-live]')].map(el=>el.id)};
      },{theme});
      assert.ok(layout.nodes.every(n=>n.left>=0&&n.right<=width),`horizontal layout ${width}/${theme}`);
      assert.ok(layout.nodes.every((n,i)=>!i||n.top>=layout.nodes[i-1].bottom),`overlap ${width}/${theme}`);
      assert.deepEqual(layout.live,['gate-sub']);
      await page.screenshot({path:path.join(out,`layout-${width}-${theme}.png`)});
      results.cases.push({name:`layout-${width}-${theme}`,...layout});
    }
  }
  await ctx.close();
}
async function fastFixture() {
  const ctx=await browser.newContext({viewport:{width:390,height:780}});
  const page=await ctx.newPage();
  await page.route('**/main.js',route=>route.fulfill({contentType:'text/javascript',body:''}));
  await page.goto(url);
  const result=await page.evaluate(async()=>{
    const {createBoot}=await import('./js/boot-phases.js');
    const {createArrival}=await import('./js/arrival.js');
    const boot=createBoot(); const yearEl=document.getElementById('arrival-year');
    const phaseEl=document.getElementById('gate-sub'), buttonEl=document.getElementById('gate-btn');
    const arrival=createArrival({boot,yearEl,phaseEl,buttonEl,currentYear:2026});
    const started=performance.now(); boot.start('scene');
    await new Promise(r=>setTimeout(r,100));
    for(const p of boot.phases.filter(p=>p.essential)){boot.start(p.id);boot.end(p.id);}
    boot.frameRendered(); const ready=boot.finish();
    return {durationMs:performance.now()-started,ready,state:arrival.state,year:yearEl.dataset.year,copy:phaseEl.textContent,disabled:buttonEl.disabled,animations:yearEl.getAnimations({subtree:true}).length};
  });
  assert.ok(result.durationMs<1500);assert.equal(result.year,'1835');assert.equal(result.disabled,false);assert.equal(result.animations,0);assert.match(result.copy,/You have arrived/);
  results.cases.push({name:'fast-browser-fixture',...result});
  console.log('PASS fast-browser-fixture',JSON.stringify(result));
  await ctx.close();
}
try {
  if(process.argv.includes('--fast-only')) await fastFixture();
  else {
    await bootCase('cold',{slow:true});
    if(!process.argv.includes('--cold-only')) {
      await bootCase('reduced',{reduced:true});
      await bootCase('essential-failure',{fail:'terrain'});
      await bootCase('optional-failure',{fail:'people'});
      await fastFixture();
    }
  }
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');
} finally { await browser.close(); await new Promise(r=>server.close(r)); }
