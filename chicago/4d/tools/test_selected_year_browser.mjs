import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
const { chromium } = await import(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES || execSync('npm root -g',{encoding:'utf8'}).trim(), 'playwright/index.mjs'));
const root = path.resolve('../../site/4d'), out = '/tmp/t1767-browser';
fs.mkdirSync(out,{recursive:true});
const types = {'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css'};
const server = http.createServer((req,res)=>{
 const pathname = new URL(req.url,'http://local').pathname;
 const file = path.join(root,pathname.endsWith('/')?pathname+'index.html':pathname);
 fs.readFile(file,(err,data)=>{res.writeHead(err?404:200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});res.end(err?'missing':data);});
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE,args:['--enable-unsafe-swiftshader']});
try {
 for(const width of [390,1280]) {
  const context=await browser.newContext({viewport:{width,height:width===390?780:800},hasTouch:width===390,isMobile:width===390,reducedMotion:width===390?'reduce':'no-preference'});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const year of ['1904','1835']) {
   const requests=[];page.on('request',r=>requests.push(r.url()));
   await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=${year}&detail=light&seed=1767`);
   await page.waitForFunction(()=>window.__chicago4d?.welcome?.state==='welcome',null,{timeout:180000});
   assert.equal(await page.locator('#arrival-year').getAttribute('data-year'),year);
   assert((await page.locator('#gate-title').innerText()).includes(year));
   assert((await page.locator('.welcome-intro').innerText()).includes(`1 July ${year}`));
   assert.equal(await page.locator('#gate-sub').isVisible(),false);
   await page.screenshot({path:`${out}/${year}-${width}-welcome.png`});
   await page.locator('#welcome-jaunts').click();
   const expected=year==='1904'?'prairie-avenue-orientation':'new-in-chicago';
   await page.locator(`[data-jaunt="${expected}"]`).waitFor({timeout:30000});
   assert.equal(await page.locator('.jaunt-card').count(),1);
   assert(!requests.some(url=>url.includes(`/sidecars/${year==='1904'?'1835':'1904'}/jaunts/`)));
   await page.screenshot({path:`${out}/${year}-${width}-jaunts.png`});
   await page.getByRole('button',{name:'Start Jaunt',exact:true}).click();
   await page.waitForFunction(id=>window.__chicago4d?.jaunts.state?.jaunt?.id===id,expected,{timeout:30000});
   assert.equal(await page.evaluate(()=>__chicago4d.jaunts.state.jaunt.scene),year);
   const bounds=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);assert(bounds,'horizontal overflow');
   console.log(`PASS ${year} ${width}: arrival, welcome, catalog, start and containment`);
  }
  // The same browser now holds both saves. Revisiting 1904 must offer only its own outing.
  await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1904&detail=light`);
  await page.waitForFunction(()=>window.__chicago4d?.welcome?.state==='welcome',null,{timeout:180000});
  await page.locator('#welcome-jaunts').click();
  await page.waitForFunction(()=>window.__chicago4d?.jaunts.state?.jaunt?.scene==='1904',null,{timeout:30000});
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(`PASS ${width}: scene-specific restore and zero page errors`);
  await context.close();
 }
} finally {await browser.close();server.close();}
