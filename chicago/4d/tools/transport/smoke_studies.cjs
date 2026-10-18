// SPDX-License-Identifier: GPL-3.0-or-later
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const path=require('node:path');
const out=path.resolve(__dirname,'../../docs/RESEARCH/period-transport-2026-10-18');
const base=(process.env.TRANSPORT_STUDY_URL||'http://127.0.0.1:8774/renderers/web/transport').replace(/\/$/,'');
let browser;
(async()=>{const b=browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const receipt={};
for(const [size,width,height] of [['desktop',1280,800],['mobile',390,780]]) for(const name of ['wagon','carriage','horse','harness']){
 const p=await b.newPage({viewport:{width,height}}),errors=[],failed=[];p.on('pageerror',e=>errors.push(e.message));p.on('requestfailed',r=>failed.push(r.url()));p.on('response',r=>{if(r.status()>=400)failed.push(r.url()+':'+r.status());});
 await p.goto(base+'/'+name+'/');let result={};
 if(['wagon','carriage'].includes(name)){
  await p.waitForFunction(()=>window.fixtureState?.loaded);
  await p.locator('#travel').evaluate(e=>{e.value='1.5';e.dispatchEvent(new Event('input'));});
  await p.locator('#steer').evaluate(e=>{e.value=e.max;e.dispatchEvent(new Event('input'));});
  const state=await p.evaluate(()=>window.fixtureState);assert.notEqual(state.wheelAngles[0],state.wheelAngles[1]);assert.equal(state.travel,1.5);assert.equal(state.wheelAngles.length,4);
  if(name==='carriage')for(const wheel of state.wheels){const radius=wheel.center[1];const polygonGap=radius*(1-Math.cos(Math.PI/48));assert(wheel.bounds[1]>=-1e-5 && wheel.bounds[1]<=polygonGap+1e-5, 'rolling rim outside its polygonal contact bound');}
  await p.locator('#reset').click();const initial=await p.evaluate(()=>window.fixtureState);assert.equal(initial.travel,0);await p.locator('#play').click();await p.waitForFunction(()=>window.fixtureState.travel>0);await p.locator('#play').click();await p.locator('#reset').click();
  await p.waitForFunction(()=>window.renderReceipt?.drawCalls>5);result={controls:'load, travel, turn, unequal wheel paths, reset, play passed',render:await p.evaluate(()=>window.renderReceipt)};
 }else if(name==='horse'){
  await p.waitForFunction(()=>window.fixture?.ready);await p.evaluate(()=>{fixture.pause();fixture.setClip('idle');fixture.setPhase(0);});const neutral=await p.evaluate(()=>fixture.measure());assert(Math.max(...neutral.map(x=>Math.abs(x.position[1])))<1e-5);
  const samples=await p.evaluate(()=>{fixture.setClip('walk');const out=[];for(let i=0;i<=1000;i++){fixture.setPhase(i/1000);out.push(fixture.measure());}return out;});
  const offsets={fore_l_contact:.25,fore_r_contact:.75,hind_l_contact:0,hind_r_contact:.5},groups={};let drift=0,stanceHeight=0;
  for(let i=0;i<samples.length;i++)for(const contact of samples[i]){const absolute=i/1000+offsets[contact.name];if(absolute%1<.62){const key=contact.name+':'+Math.floor(absolute);(groups[key]??=[]).push(contact.position[2]+i/1000*.72/.62);stanceHeight=Math.max(stanceHeight,Math.abs(contact.position[1]));}}
  for(const values of Object.values(groups))drift=Math.max(drift,Math.max(...values)-Math.min(...values));assert(drift<.020);assert(stanceHeight<.005);await p.evaluate(()=>{fixture.setClip('walk');fixture.setPhase(.32);});
  result={neutral_contacts:neutral,walk_samples:1001,walk_compensated_stance_drift_m:drift,max_stance_height_error_m:stanceHeight};
 }else{
  await p.waitForFunction(()=>window.harnessFixture?.ready);await p.locator('#motion').check();await p.waitForTimeout(200);
  result=await p.evaluate(()=>{let meshes=0;harnessFixture.harness.traverse(n=>{if(n.isMesh)meshes++;});return {loaded_meshes:meshes,render_calls:harnessFixture.renderer.info.render.calls};});assert.equal(result.loaded_meshes,32);await p.locator('#motion').uncheck();await p.locator('#horse').uncheck();await p.locator('#horse').check();
 }
 await p.waitForTimeout(100);await p.screenshot({path:out+'/'+name+'/integrated-'+size+'.png'});assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);receipt[name+'-'+size]={...result,page_errors:errors,failed_requests:failed};await p.close();
}
const p=await b.newPage();await p.goto(base+'/');assert.equal(await p.locator('main article a').count(),5);await b.close();fs.writeFileSync(out+'/integrated-browser-validation.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));})().catch(async e=>{console.error(e);if(browser)await browser.close();process.exitCode=1;});
