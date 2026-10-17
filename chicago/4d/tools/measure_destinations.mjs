/** Published T-1277 acceptance. Writes screenshots/receipts outside the source tree.
 *  T-2620: the drawer's Go to list retired with the drawer; Go to is the Jaunts app's own
 *  segment (T-2630), the arrival's search (#welcome-search, rows .welcome-destination), so
 *  this drives that. It lists 40 rows at a time, so the inventory is read off the search it
 *  renders, and a row with no known address is disabled rather than opening a card. */
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
 console.log('START',width);await page.goto(url,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.__chicago4d?.ready,null,{timeout:180000});await page.locator('#home-roam').click();
 const openGoTo=()=>page.evaluate(async()=>{const a=window.__chicago4d;a.hud.setHidden('reconstructed',false,{announce:false});await a.openJaunts('goto');});
 const row=(kind,id)=>page.locator(`#welcome-results .welcome-destination[data-kind="${kind}"][data-id="${id}"]`);
 await page.evaluate(()=>window.__chicago4d.renderer.setAnimationLoop(null));await openGoTo();await page.locator('#welcome-search').waitFor({state:'visible'});
 const inventory=await page.evaluate(()=>{const a=window.__chicago4d,d=a.destinations;return {count:d.count,rows:d.search('',{kind:'all',includeReconstructed:true}).length,shown:document.querySelectorAll('#welcome-results .welcome-destination').length,shared:d.targets===a.hud.goTo.targets};});
 assert.equal(inventory.rows,inventory.count);assert.equal(inventory.shown,Math.min(40,inventory.count));assert.ok(inventory.shared);
 await page.locator('#welcome-search').fill('peck');
 assert.ok(await row('structure','peck_store').count());
 const firm=row('business','biz_p_f_peck');assert.equal(await firm.count(),1);await firm.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`${width}-search.png`)});
 // In the town a pick goes there as the retired drawer list did (goToTarget, T-2620): to the firm's building, its card open.
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
  assert.ok(t?.limit);await openGoTo();
  await page.locator('#welcome-search').fill(t.label);
  const unlocated=row(t.kind,t.id);
  // No invented distance and no invented destination: the row says so and cannot be chosen.
  assert.equal(await unlocated.locator('.welcome-dist').count(),0);
  assert.ok(await unlocated.isDisabled());assert.match(await unlocated.textContent(),/no known starting place/);
  const before=await page.evaluate(()=>{const s=window.__chicago4d.walker.state;return [s.e,s.n];});await unlocated.click({force:true});
  assert.deepEqual(await page.evaluate(()=>{const s=window.__chicago4d.walker.state;return [s.e,s.n];}),before);
  if(t.kind==='person')await page.screenshot({path:path.join(out,`${width}-unlocated.png`)});
 }
 assert.deepEqual(errors,[]);results.push({width,inventory,safeStructures:proof.safeStructures.length,resolution:proof.resolution,spawned:proof.spawned,errors});
 console.log('PASS',JSON.stringify(results.at(-1)));await ctx.close();
}}finally{fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');await browser.close();server.close();}
