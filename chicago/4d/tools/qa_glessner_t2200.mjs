#!/usr/bin/env node
// Dedicated published-page coverage. The town smoke never loads this page.
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const base=process.env.BASELINE_BASE||'http://127.0.0.1:8765/4d/';
const out=process.env.QA_OUT||'/tmp/glessner-t2200';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
try {
 for(const viewport of [{width:1280,height:800},{width:390,height:780}]){
  const page=await browser.newPage({viewport}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  await page.goto(new URL('walk/glessner-baseline.html',base).href);
  await page.waitForFunction(()=>window.__glessnerBaseline?.ready||window.__glessnerBaseline?.error,null,{timeout:120000});
  assert.equal(await page.evaluate(()=>__glessnerBaseline.error),undefined);
  assert.equal(await page.evaluate(()=>__glessnerBaseline.hashMatches),true,'Model is not the frozen baseline');
  const views=await page.evaluate(()=>__glessnerBaseline.data.views.map(v=>({id:v.id,clear:['public domain','no known restrictions'].includes(v.rights),size:v.image_size,count:v.landmarks.length})));
  for(const view of views){
   await page.selectOption('#view-select',view.id);
   if(view.clear)await page.waitForFunction(()=>{const i=document.querySelector('#reference');return !i.hidden&&i.complete&&i.naturalWidth>0},null,{timeout:45000});
   const reading=await page.evaluate(()=>{const a=__glessnerBaseline,r=a.report.views.find(v=>v.id===a.active),i=document.querySelector('#reference');return{diff:Math.max(...r.landmarks.map(p=>Math.hypot(...a.project(p.mesh_vertex_m).map((x,j)=>x-p.predicted_px[j])))),rows:document.querySelectorAll('#landmarks tr').length,overflow:document.documentElement.scrollWidth>innerWidth+1,image:i.getAttribute('src'),size:[i.naturalWidth,i.naturalHeight]}});
   assert(reading.diff<.001,`${view.id}: Python/Three camera mismatch ${reading.diff}`);assert.equal(reading.rows,view.count);assert.equal(reading.overflow,false);
   if(view.clear)assert.deepEqual(reading.size,view.size,'Source pixel coordinates must use the displayed image size');else assert.equal(reading.image,null,'Restricted reference must remain link-only');
   if(['prairie-front','taylor-ne','courtyard-east'].includes(view.id))await page.screenshot({path:`${out}/${viewport.width}-${view.id}.png`,fullPage:true});
  }
  const detail=await page.locator('#detail').inputValue(),other=detail==='full'?'light':'full';await page.selectOption('#detail',other);
  await page.waitForFunction(d=>__glessnerBaseline.detail===d,other,{timeout:120000});
  assert.equal(await page.evaluate(()=>__glessnerBaseline.hashMatches),true);
  await page.uncheck('#markers');assert.equal(await page.locator('#photo-overlay > *').count(),0);
  await page.check('#markers');assert(await page.locator('#photo-overlay > *').count()>0);
  assert.deepEqual(errors,[]);
  // Exercise the real 1904 house card, not a fabricated popup fixture.
  await page.goto(new URL('1904/',base).href,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000});
  assert.equal(await page.evaluate(()=>__chicago4d.ready),true);
  await page.waitForFunction(()=>__chicago4d.welcome.state==='welcome',null,{timeout:120000});
  const href=await page.evaluate(()=>{const a=__chicago4d;a.welcome.enter('spawn');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);a.popup.show(a.registry.get('glessner_house'));return [...document.querySelectorAll('#popup a')].find(x=>x.textContent.includes('Photographic comparison baseline'))?.href});
  assert.equal(href,new URL('walk/glessner-baseline.html',base).href);
  assert.deepEqual(errors,[]);console.log(`PASS ${viewport.width}x${viewport.height}: nine views, source pixels/rights, projection, full/light hashes, markers, 1904 house-card link, no overflow/errors`);await page.close();
 }
} finally {await browser.close()}
