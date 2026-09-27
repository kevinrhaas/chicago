/** Published T-1277 acceptance. Writes screenshots/receipts outside the source tree. */
import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import zlib from 'node:zlib';import assert from 'node:assert/strict';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../site/4d');
const out=process.env.DESTINATIONS_EVIDENCE || '/tmp/destinations-evidence';fs.mkdirSync(out,{recursive:true});
const {chromium}=await import(path.join(process.env.NODE_PATH,'playwright/index.mjs'));
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{let name=decodeURIComponent(req.url.split('?')[0]);if(name.endsWith('/'))name+='index.html';const file=path.resolve(root,'.'+name);if(!file.startsWith(root+'/')){res.writeHead(403).end();return;}try{res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Content-Encoding':'gzip'});res.end(zlib.gzipSync(fs.readFileSync(file)));}catch{res.writeHead(404).end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/walk/?year=1835`;
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE,args:['--no-sandbox','--enable-unsafe-swiftshader']});const results=[];

try { for (const width of [390,1280]) {
 const ctx=await browser.newContext({viewport:{width,height:width===390?780:800},hasTouch:width===390});
 await ctx.addInitScript(()=>localStorage.setItem('chicago4d.settings',JSON.stringify({detail:'light',travelMode:'instantly'})));
 const page=await ctx.newPage(),errors=[];page.setDefaultTimeout(90000);page.on('pageerror',e=>errors.push(e.message));
 console.log('START',width);await page.goto(url,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.__chicago4d?.ready,null,{timeout:180000});await page.locator('#gate-btn').click();
 const inventory=await page.evaluate(()=>{const a=window.__chicago4d;a.renderer.setAnimationLoop(null);a.hud.setPanel(true);a.hud.selectTab('goto');a.hud.goTo.setIncludeReconstructed(true);return {count:a.destinations.count,rows:document.querySelectorAll('.jump-result').length,shared:a.destinations.targets===a.hud.goTo.targets};});
 assert.equal(inventory.rows,inventory.count);assert.ok(inventory.shared);
 await page.locator('#jump-search').fill('peck');
 assert.ok(await page.locator('[data-jump-kind="structure"][data-jump-id="peck_store"]').count());
 const firm=page.locator('[data-jump-kind="business"][data-jump-id="biz_p_f_peck"]');assert.equal(await firm.count(),1);await firm.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`${width}-search.png`)});
 await firm.click();await page.waitForFunction(()=>window.__chicago4d.popup.openId==='peck_store');await page.evaluate(()=>window.__chicago4d.popup.close());
 const proof=await page.evaluate(()=>{
  const a=window.__chicago4d,d=a.destinations;
  const state=()=>({e:a.walker.state.e,n:a.walker.state.n,flying:a.flying});
  const samples=[d.byId('structure','peck_store'),d.targets.find(t=>t.kind==='person'&&t.at==='peck_store'),d.targets.find(t=>t.kind==='anchor'&&!t.altitude_m&&!a.router.blockedAt(t.e,t.n)),d.targets.find(t=>t.kind==='intersection'&&!a.router.blockedAt(t.e,t.n))];
  const resolution=samples.map(t=>{const r=d.resolve(t);return {kind:t.kind,ok:!!r,blocked:a.router.blockedAt(r.standOff.e,r.standOff.n),ground:r.standOff.y===a.terrain.surfaceHeight(r.standOff.e,r.standOff.n)};});
  a.travel.setMode('walk');
  const spawned=samples.map(t=>{const r=d.resolve(t,{card:false}),ok=a.spawnAtDestination(t),first=state();a.spawnAtDestination(t);return {kind:t.kind,ok,stable:JSON.stringify(first)===JSON.stringify(state()),distance:Math.hypot(first.e-r.standOff.e,first.n-r.standOff.n),phase:a.travel.state.phase,flying:a.flying};});
  const safeStructures=d.targets.filter(t=>t.kind==='structure').map(t=>{const r=d.resolve(t,{card:false}),ok=a.spawnAtDestination(t),s=state();return {id:t.id,ok,blocked:a.router.blockedAt(s.e,s.n),distance:r?Math.hypot(s.e-r.standOff.e,s.n-r.standOff.n):null};});
  const unknown=d.targets.find(t=>t.kind==='person'&&!t.at),business=d.targets.find(t=>t.kind==='business'&&!t.at);
  const before=state(),dismiss=a.spawnAtDestination(null),unlocated=a.spawnAtDestination(unknown),unchanged=JSON.stringify(before)===JSON.stringify(state());
  return {resolution,spawned,safeStructures,unknown,business,dismiss,unlocated,unchanged};
 });
 for(const r of proof.resolution){assert.ok(r.ok);assert.equal(r.blocked,false);assert.ok(r.ground);}
 for(const r of proof.spawned){assert.ok(r.ok&&r.stable);assert.ok(r.distance<0.01);assert.equal(r.phase,'idle');assert.equal(r.flying,false);}
 assert.ok(proof.safeStructures.length>300);for(const r of proof.safeStructures){assert.ok(r.ok&&!r.blocked&&r.distance<0.01,JSON.stringify(r));}
 assert.equal(proof.dismiss,false);assert.equal(proof.unlocated,false);assert.ok(proof.unchanged);
 for(const t of [proof.unknown,proof.business]){
  assert.ok(t?.limit);await page.evaluate(()=>{const a=window.__chicago4d;a.hud.setPanel(true);a.hud.selectTab('goto');a.hud.goTo.setKind('all');});
  await page.locator('#jump-search').fill(t.label);
  const row=page.locator(`[data-jump-kind="${t.kind}"][data-jump-id="${t.id}"]`);
  assert.equal((await row.locator('.jump-dist').textContent()).trim(),'');
  const before=await page.evaluate(()=>{const s=window.__chicago4d.walker.state;return [s.e,s.n];});await row.click();
  await page.waitForFunction(t=>window.__chicago4d[t.kind==='person'?'people':'businesses'].state.open===t.id,t);
  assert.deepEqual(await page.evaluate(()=>{const s=window.__chicago4d.walker.state;return [s.e,s.n];}),before);
  assert.equal(await page.locator('.hud-panel').getAttribute('hidden'),null);
  if(t.kind==='person')await page.screenshot({path:path.join(out,`${width}-unlocated.png`)});
 }
 assert.deepEqual(errors,[]);results.push({width,inventory,safeStructures:proof.safeStructures.length,resolution:proof.resolution,spawned:proof.spawned,errors});
 console.log('PASS',JSON.stringify(results.at(-1)));await ctx.close();
}}finally{fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');await browser.close();server.close();}
