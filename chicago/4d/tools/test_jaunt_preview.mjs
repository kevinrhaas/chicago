#!/usr/bin/env node
// T-1253: published preview, lazy requests, retry paths and mobile containment.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
const pw = await import(path.join((process.env.NODE_PATH || execSync('npm root -g', { encoding:'utf8' }).trim()).split(path.delimiter)[0], 'playwright/index.js'));
const { chromium } = pw.chromium ? pw : pw.default;
const root = path.resolve('../../site/4d'), out = path.resolve('docs/performance/jaunts');
fs.mkdirSync(out, { recursive: true });
const types = { '.js':'text/javascript', '.css':'text/css', '.html':'text/html', '.json':'application/json', '.glb':'model/gltf-binary' };
const server = http.createServer((req,res) => {
  const pathname = new URL(req.url,'http://local').pathname.replace(/^\/dev\//, '/');
  const file = path.join(root, pathname.endsWith('/') ? pathname+'index.html' : pathname);
  fs.readFile(file,(err,bytes) => {res.writeHead(err ? 404 : 200, {'Content-Type':types[path.extname(file)] || 'application/octet-stream'});res.end(err ? 'Not found' : bytes);});
});
await new Promise(r => server.listen(0,'127.0.0.1',r));
const browser = await chromium.launch({executablePath:process.env.PW_EXECUTABLE,args:['--enable-unsafe-swiftshader']});
const receipts=[];
try {
  for (const viewport of [{width:390,height:780},{width:1280,height:800}]) {
    const context=await browser.newContext({viewport,hasTouch:viewport.width===390,isMobile:viewport.width===390,reducedMotion:'reduce'});
    const page=await context.newPage(), requests=[], errors=[];
    page.on('request',r => {if (/jaunts\/|jaunt-preview.js/.test(r.url())) requests.push(r.url());});
    page.on('pageerror',e=>errors.push(e.message));
    let catalogFailures=0, contentFailures=0;
    await page.route('**/jaunts/catalog.json',r => ++catalogFailures===1 ? r.fulfill({status:503,body:'Temporarily unavailable'}) : r.continue());
    await page.route('**/jaunts/new-in-chicago.json',r => ++contentFailures===1 ? r.fulfill({status:503,body:'Temporarily unavailable'}) : r.continue());
    const prefix=viewport.width===390 ? '/walk/' : '/dev/walk/';
    await page.goto(`http://127.0.0.1:${server.address().port}${prefix}?year=1835&seed=1253`);
    await page.waitForFunction(()=>window.__chicago4d?.welcome?.state==='welcome',{},{timeout:180000});
    assert.equal(requests.length,0,'no jaunt module, catalog or story at boot');
    await page.locator('#welcome-jaunts').click();
    await page.getByRole('button',{name:'Try again',exact:true}).click();
    await page.waitForSelector('[data-jaunt="new-in-chicago"]');
    assert(!requests.some(r=>r.endsWith('/new-in-chicago.json')),'content stays lazy until selected');
    await page.screenshot({path:path.join(out,`${viewport.width}-catalog.png`)});
    await page.locator('[data-jaunt="new-in-chicago"] [data-action="more"]').click();
    await page.getByRole('button',{name:'Preview the route',exact:true}).click();
    await page.getByRole('button',{name:'Try the route again'}).click();
    await page.waitForSelector('.jaunt-stops');
    assert.equal(await page.locator('.jaunt-stops > li').count(),5);
    assert.match(await page.locator('.jaunt-stops').innerText(),/former mail corner/);
    assert.match(await page.locator('.jaunt-stops').innerText(),/by May 1835/);
    await page.screenshot({path:path.join(out,`${viewport.width}-preview.png`)});
    await page.getByRole('button',{name:'Evidence for this stop'}).first().click();
    assert.match(await page.locator('.jaunt-evidence').first().innerText(),/\[DOC\].*Kinzie/s);
    await page.keyboard.press('w');
    assert.equal(await page.evaluate(()=>!!document.pointerLockElement),false);
    assert.equal(await page.evaluate(()=>__chicago4d.welcome.state),'welcome');
    for (const size of viewport.width===390 ? [{width:320,height:568},{width:780,height:390},{width:390,height:780}] : [viewport]) {
      await page.setViewportSize(size);
      // The last button must be scroll-reachable, without horizontal overflow.
      await page.getByRole('button',{name:'Evidence for this stop'}).last().scrollIntoViewIfNeeded();
      const layout=await page.evaluate(()=>({body:document.body.scrollWidth,viewport:innerWidth,controls:[...document.querySelectorAll('#welcome-jaunts-content button')].map(e=>e.getBoundingClientRect().height)}));
      assert(layout.body<=layout.viewport+1,JSON.stringify(layout));
      assert(layout.controls.every(h=>h>=44),'44px tap targets');
    }
    await page.getByRole('button',{name:'Back to Jaunts',exact:true}).click();
    assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Preview the route');
    const count=requests.filter(r=>r.endsWith('/new-in-chicago.json')).length;
    await page.getByRole('button',{name:'Preview the route',exact:true}).click();
    await page.waitForSelector('.jaunt-stops');
    assert.equal(requests.filter(r=>r.endsWith('/new-in-chicago.json')).length,count,'cached selection');
    await page.locator('#welcome-explore').click();
    assert(await page.locator('#welcome-search').isVisible());
    assert.equal(errors.length,0,errors.join('\n'));
    receipts.push({viewport,prefix,bootJauntRequests:0,stops:5,catalogAttempts:catalogFailures,contentAttempts:contentFailures,requests,pageErrors:errors});
    await context.close();
  }
  // Module-only catalog behavior, still served from the published mirror.
  const page=await browser.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  const unavailable=await page.evaluate(async()=>{
    const {createJauntPreview}=await import('/walk/js/jaunt-preview.js');
    const root=document.createElement('div');document.body.replaceChildren(root);
    const api={};const fetcher=async()=>({ok:true,json:async()=>({jaunts:[{id:'held',title:'Awaiting review',premise:'A held story.',category:'Orientation',stop_count:2,primary_family:'Wayfinding',availability:'unavailable',reason:'Consultation required.'}]})});
    await createJauntPreview({root,dataBase:new URL('/data/',location.href),destinations:{},api,fetcher}).open();
    return {text:root.textContent,buttons:root.querySelectorAll('[data-action="start"], [data-action="preview"]').length};
  });
  assert.match(unavailable.text,/Unavailable — Consultation required/);assert.equal(unavailable.buttons,0);
  receipts.push({unavailable});
  fs.writeFileSync(path.join(out,'preview.json'),JSON.stringify(receipts,null,2)+'\n');
  console.log('JAUNT PREVIEW PASS — both viewports, production/dev bases, 0 boot requests, isolated retries, 5 stops, evidence, unavailable reasons and layouts');
} finally {await browser.close();server.close();}
