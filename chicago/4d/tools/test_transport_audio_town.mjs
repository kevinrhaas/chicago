// Actual generated town, loaded transport assemblies and integrated Effects bus.
// Draws may be held during data/audio reads; this is not a pixel-quality claim.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const published=process.env.C4D_PUBLISHED_ROOT;
assert(published,'Set C4D_PUBLISHED_ROOT to the generated site/4d');
const policy=JSON.parse(await fs.readFile(path.join(root,'tools/audio-hosting.json'),'utf8'));
let pw;try{pw=await import('playwright');}catch{pw=await import(path.join(process.env.NODE_PATH,'playwright/index.mjs'));}
const proxyUrl=process.env.HTTPS_PROXY||process.env.HTTP_PROXY||process.env.https_proxy||process.env.http_proxy;
const u=proxyUrl?new URL(proxyUrl):null;
const proxy=u?{server:u.origin,...(u.username?{username:decodeURIComponent(u.username),password:decodeURIComponent(u.password)}:{})}:undefined;
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.css':'text/css','.wasm':'application/wasm','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.glb':'model/gltf-binary'};
const widths=process.env.TRANSPORT_VIEWPORT?[Number(process.env.TRANSPORT_VIEWPORT)]:[390,1280];
for(const width of widths){
 const browser=await pw.chromium.launch({proxy,executablePath:process.env.PW_EXECUTABLE??'/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
 try{
  const context=await browser.newContext({viewport:{width,height:width===390?780:800},hasTouch:width===390,serviceWorkers:'block'});
  const page=await context.newPage(),errors=[],requests=[];
  page.setDefaultTimeout(90000);
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.url().startsWith(policy.public_base))requests.push(r.url());});
  await context.route(policy.origin+'/**',async route=>{
   const relative=decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\/4d(?=\/)/,'');
   let file=path.resolve(published,'.'+relative);
   if(!file.startsWith(path.resolve(published)+path.sep))return route.fulfill({status:403});
   try{if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');
    return route.fulfill({body:await fs.readFile(file),contentType:mime[path.extname(file)]??'application/octet-stream'});
   }catch{return route.fulfill({status:404,body:relative});}
  });
  await page.addInitScript(()=>localStorage.setItem('chicago4d.settings',JSON.stringify({soundMaster:0,soundEffects:1,soundAmbience:0,soundMusic:0,timeOfDay:'15:00',sceneDetail:'full'})));
  await page.goto(policy.origin+'/4d/walk/?year=1835&keep-geometry=1',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.__chicago4d?.ready===true,null,{timeout:240000,polling:1000});
  console.log(`${width}px: generated town ready`);
  assert.equal(requests.length,0,'default-muted town fetches no audio');
  await page.evaluate(()=>{
   const a=__chicago4d;window.savedDraw=a.renderer.render;
   a.renderer.render=(scene,camera)=>camera?.updateMatrixWorld?.();
  });
  await page.click('#arrival-sound');
  await page.evaluate(async()=>{
   const a=__chicago4d,deadline=Date.now()+90000;
   while(a.welcome?.state!=='world'&&Date.now()<deadline){
    if(a.welcome?.state==='welcome')a.welcome.enter('spawn');
    await new Promise(r=>setTimeout(r,100));
   }
   if(a.welcome?.state!=='world')throw Error('world entry incomplete');
   await a.timeOfDay.set('15:00',{date:'1835-07-01'});
   await a.townTransport.setTier('full');
   const config=await(await fetch('../data/transport/driven/loops.json')).json();
   const row=config.rows.find(r=>r.scene==='1835');
   const {routeFor}=await import('./js/transport-loop.js');
   const p=routeFor(row.route).at(row.initial_distance_m??0);
   a.walker.teleport({local_e:p.e+12,local_n:p.n,yaw_deg:270});a.step();a.step();
   await a.townTransport.ready();document.exitPointerLock?.();
  });
  await page.waitForFunction(()=>__chicago4d.townTransport.audioSources.some(s=>s.moving),null,{timeout:90000,polling:200});
  await page.evaluate(()=>{
   const a=__chicago4d;window.transportMeter=a.sound.nodes.master.context.createAnalyser();
   a.sound.nodes.effects.connect(transportMeter);
   window.peak=()=>{const s=new Float32Array(transportMeter.fftSize);transportMeter.getFloatTimeDomainData(s);return Math.max(...s.map(Math.abs));};
  });
  await page.waitForFunction(()=>__chicago4d.sound.state.recorded.transport.voices.length===2&&peak()>1e-6,null,{timeout:45000,polling:100});
  const proof=await page.evaluate(()=>({sources:__chicago4d.townTransport.audioSources,audio:__chicago4d.sound.state.recorded.transport}));
  assert(proof.sources[0].anchors);assert(proof.audio.decodedBytes<=8*1024*1024);
  assert.deepEqual(proof.audio.errors,[]);assert.equal(requests.length,2,'effects alone load only harness and wagon');
  await page.evaluate(()=>__chicago4d.townTransport.actors[0].stop());
  await page.waitForFunction(()=>!__chicago4d.sound.state.recorded.transport.voices.length&&peak()<1e-6,null,{timeout:5000});
  await page.evaluate(()=>__chicago4d.townTransport.actors[0].resume());
  await page.waitForFunction(()=>__chicago4d.sound.state.recorded.transport.voices.length===2&&peak()>1e-6,null,{timeout:10000});
  await page.evaluate(()=>__chicago4d.townTransport.setTier('light'));
  await page.waitForFunction(()=>__chicago4d.townTransport.audioSources.some(s=>s.moving)&&__chicago4d.sound.state.recorded.transport.voices.length===2&&peak()>1e-6,null,{timeout:10000});
  await page.evaluate(()=>{const a=__chicago4d,p=a.townTransport.audioSources[0].anchors.wagon;
   a.walker.teleport({local_e:p.x+200,local_n:-p.z,yaw_deg:270});a.step();a.step();});
  await page.waitForFunction(()=>!__chicago4d.sound.state.recorded.transport.voices.length&&peak()<1e-6,null,{timeout:5000});
  assert.deepEqual(errors,[]);
  await page.evaluate(()=>{__chicago4d.sound.dispose();__chicago4d.renderer.render=savedDraw;transportMeter.disconnect();});
  console.log(`TRANSPORT TOWN PASS ${width}px: real loaded moving wagon/horse anchors, integrated Effects-only R2 playback, Stop/Continue, audible nearby Light teams and out-of-range silence, ${proof.audio.decodedBytes} bytes, zero page errors`);
 }finally{await browser.close();}
}
