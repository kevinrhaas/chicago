#!/usr/bin/env node
/** T-1275 loading-card browser acceptance, against the generated visitor mirror.
 * NODE_PATH=<playwright module root> PW_EXECUTABLE=<chromium> node tools/measure_arrival.mjs
 * Captures are written to LOADING_EVIDENCE (default /tmp/loading-evidence).
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
const out = process.env.LOADING_EVIDENCE || '/tmp/loading-evidence';
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
async function run(width, slow) {
 const ctx=await browser.newContext({viewport:{width,height:780},hasTouch:width<500});
 await ctx.addInitScript(()=>{
  localStorage.setItem('chicago4d.settings',JSON.stringify({detail:'light'}));
  window.loadingProbe=[];let attached=false;
  const attach=()=>{const el=document.getElementById('arrival-card');if(!el||attached)return;attached=true;
   new MutationObserver(()=>window.loadingProbe.push({at:performance.now(),text:el.textContent,id:el.dataset.loadingId,kind:el.dataset.loadingKind,phase:el.dataset.loadingPhase,year:document.getElementById('arrival-year').dataset.year})).observe(el,{childList:true,attributes:true});
  };
  new MutationObserver(attach).observe(document,{childList:true,subtree:true});attach();
 });
 const page=await ctx.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 if(slow){const cdp=await ctx.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:1.6e6/8,uploadThroughput:750e3/8});}
 console.log(`START loading ${width}`);
 await page.goto(url+'&seed=1275',{waitUntil:'domcontentloaded',timeout:120000});
 for(const phase of ['assess','collect','prepare']){
  if(!slow)break;
  await page.waitForFunction(p=>{const d=document.getElementById('arrival-card').dataset;return d.loadingPhase===p&&(p!=='prepare'||d.loadingKind==='build');},phase,{timeout:180000});
  await page.screenshot({path:path.join(out,`${width}-${phase}.png`)});
 }
 await page.waitForFunction(()=>window.__chicago4d?.ready&&document.getElementById('arrival-year').dataset.year==='1835',{},{timeout:180000});
 await page.screenshot({path:path.join(out,`${width}-land.png`)});
 const cold=await page.evaluate(()=>window.loadingProbe.filter(e=>e.id));
 assert.equal(await page.locator('#gate-sub').textContent(),'Ready to explore.');
 assert.deepEqual(errors,[]);assert.equal(cold.filter(e=>e.id==='arrival').length,1);
 assert.equal(cold.find(e=>e.id==='arrival').year,'1835');
 assert.ok(cold.some(e=>e.kind==='source'&&e.phase==='assess'));
 if(slow){assert.ok(cold.some(e=>e.kind==='build'&&e.phase==='collect'));assert.ok(cold.some(e=>e.kind==='build'&&e.phase==='prepare'));}
 await page.evaluate(()=>window.__chicago4d.renderer.setAnimationLoop(null));
 await page.setViewportSize({width:320,height:780});
 const layout=await page.evaluate(async()=>{
  const entries=(await (await fetch('../data/loading/statuses.json')).json()).entries;
  const card=document.getElementById('arrival-card');const bad=[];let tallest=0;
  for(const e of entries){card.textContent=e.text+(e.source_label?' — '+e.source_label:'');
   const r=card.getBoundingClientRect(),lh=parseFloat(getComputedStyle(card).lineHeight);tallest=Math.max(tallest,card.scrollHeight/lh);
   if(r.left<0||r.right>320||card.scrollHeight>2*lh+2)bad.push({id:e.id,text:card.textContent,lines:card.scrollHeight/lh});}
  return {bad,tallest};
 });
 results.cases.push({width,cold,layout,errors});
 console.log(`LAYOUT ${width}: ${JSON.stringify(layout)}`);assert.deepEqual(layout.bad,[],'all cards fit two lines at 320px');
 // Repeat visit retains cache and session, but returns to normal network and CPU.
 if(slow){const cdp=await ctx.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});}
 await page.reload({waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready&&document.getElementById('arrival-year').dataset.year==='1835',{},{timeout:180000});
 const warm=await page.evaluate(()=>window.loadingProbe.filter(e=>e.id));
 assert.equal(await page.evaluate(()=>window.__chicago4d.arrival.content.state.count),2);assert.equal(warm.length,2);
 results.cases.at(-1).warm=warm;console.log(`PASS ${width}: cold ${cold.length} cards, warm ${warm.length}, no page errors`);
 await ctx.close();
}
try {await run(390,true);await run(1280,false);}
finally {fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');await browser.close();server.close();}
