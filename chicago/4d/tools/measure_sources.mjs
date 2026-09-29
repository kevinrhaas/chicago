/** Published T-1276 acceptance. Writes screenshots/receipts outside the source tree. */
import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import zlib from 'node:zlib';import assert from 'node:assert/strict';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../site/4d');
const out=process.env.SOURCES_EVIDENCE || '/tmp/sources-evidence';fs.mkdirSync(out,{recursive:true});
const {chromium}=await import(path.join(process.env.NODE_PATH,'playwright/index.mjs'));
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{let name=decodeURIComponent(req.url.split('?')[0]);if(name.endsWith('/'))name+='index.html';const file=path.resolve(root,'.'+name);if(!file.startsWith(root+'/')){res.writeHead(403).end();return;}try{res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Content-Encoding':'gzip'});res.end(zlib.gzipSync(fs.readFileSync(file)));}catch{res.writeHead(404).end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/walk/?year=1835`;
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE,args:['--no-sandbox','--enable-unsafe-swiftshader']});const results=[];
try{for(const width of [390,1280]){
 const ctx=await browser.newContext({viewport:{width,height:width===390?780:800},hasTouch:width===390});await ctx.addInitScript(()=>localStorage.setItem('chicago4d.settings',JSON.stringify({detail:'light'})));
 const page=await ctx.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 console.log('START',width);await page.goto(url,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.__chicago4d?.ready,null,{timeout:180000});
 assert.equal(requests.filter(u=>u.includes('/sources/index.json')||u.endsWith('/sources.js')).length,0,'no sources fetch at boot');
 await page.locator('#gate-btn').click();
 await page.evaluate(()=>{const a=window.__chicago4d;a.renderer.setAnimationLoop(null);a.hud.setPanel(true);a.hud.selectTab('evidence');});
 await page.locator('.ev-tile[data-topic="sources"]').click();await page.waitForSelector('.src-row');
 const stats=await page.evaluate(()=>({rows:window.__chicago4d.sources.rows.length,scene:window.__chicago4d.sources.rows.filter(r=>r.use==='scene').length,status:document.querySelector('.src-status').textContent,rendered:document.querySelectorAll('.src-row').length}));
 assert.ok(stats.status.startsWith(String(stats.scene)));assert.equal(stats.rendered,40);
 await page.locator('.src-all input').check();assert.ok((await page.locator('.src-status').textContent()).startsWith(String(stats.rows)));
 await page.locator('.src-filters>summary').click();await page.locator('.src-search').fill('Andreas');await page.locator('[data-filter="type"][data-value="book"]').click();await page.locator('[data-filter="tier"][data-value="3"]').click();
 await page.locator('.src-sort').selectOption('title');assert.ok(await page.locator('[data-source-id="andreas_1884_v1"]').count());
 const index=fs.readFileSync(path.join(root,'data/sidecars/1835/sources/index.json'));assert.ok(index.length<=128000,'raw index inside compile_source_use.py INDEX_BUDGET (T-1728 re-budget)');
 const firstWire=['data/sidecars/1835/sources/index.json','walk/js/sources.js','walk/css/sources.css'].reduce((n,p)=>n+zlib.gzipSync(fs.readFileSync(path.join(root,p))).length,0);assert.ok(firstWire<=120000);
 await page.locator('.src-filters>summary').click();await page.locator('[data-source-id="andreas_1884_v1"]').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`${width}-catalog.png`)});
 await page.locator('.src-filters>summary').click();
 // Reset controls through the UI, then keep a newspaper filter across card navigation.
 await page.locator('[data-filter="type"][data-value="newspaper"]').click();await page.locator('[data-filter="tier"][data-value=""]').click();await page.locator('.src-search').fill('Chicago Democrat');
 await page.locator('[data-source="chicago_democrat_1833_1835"]').click();await page.waitForSelector('.src-detail');const savedScroll=await page.evaluate(()=>window.__chicago4d.sources.state.scroll);
 assert.ok(await page.locator('.src-issues details').count()>0);assert.equal(await page.locator('.src-issues details[open]').count(),0);
 await page.locator('.src-groups>details').filter({has:page.locator('summary', {hasText:/^structure ·/})}).locator('summary').first().click();
 const link=page.locator('.src-edges button').filter({hasText:'sauganash hotel'});await link.click();await page.waitForFunction(()=>window.__chicago4d.popup.openId==='sauganash_hotel');
 await page.locator('#popup [data-close]').click();await page.waitForSelector('.src-detail');await page.locator('#panel-back').click();await page.waitForSelector('.src-search');assert.equal(await page.locator('.src-search').inputValue(),'Chicago Democrat');await page.waitForFunction(top=>Math.abs(document.getElementById('panel-scroll').scrollTop-top)<2,savedScroll);
 assert.equal(await page.locator('[data-filter="type"][data-value="newspaper"]').getAttribute('aria-pressed'),'true');
 await page.evaluate(()=>window.__chicago4d.evidenceHub.showTopic('grades'));await page.evaluate(()=>window.__chicago4d.evidenceHub.showTopic('sources'));await page.waitForFunction(top=>Math.abs(document.getElementById('panel-scroll').scrollTop-top)<2,savedScroll);
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth || document.querySelector('#sources').scrollWidth>document.querySelector('#sources').clientWidth+1);assert.equal(overflow,false);
 await page.locator('[data-source="chicago_democrat_1833_1835"]').click();await page.waitForSelector('.src-detail');await page.screenshot({path:path.join(out,`${width}-detail.png`)});
 assert.deepEqual(errors,[]);results.push({width,...stats,indexBytes:index.length,firstOpenGzipBytes:firstWire,errors});console.log('PASS',JSON.stringify(results.at(-1)));
 if(width===390){await page.route('**/sources/index.json',r=>r.fulfill({status:503,body:'unavailable'}));await page.reload({waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.__chicago4d?.ready,null,{timeout:180000});await page.locator('#gate-btn').click();await page.evaluate(()=>{let a=window.__chicago4d;a.renderer.setAnimationLoop(null);a.hud.setPanel(true);a.hud.selectTab('evidence');a.evidenceHub.showTopic('sources');});await page.getByText('The source catalog could not be loaded.',{exact:false}).waitFor();await page.locator('#panel-back').click();await page.locator('.ev-tile[data-topic="grades"]').click();assert.ok(await page.locator('[data-topic="grades"] .legend-list').isVisible());console.log('PASS unavailable catalog / other Evidence usable');}
 await ctx.close();
}}finally{fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');await browser.close();server.close();}
