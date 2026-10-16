// T-2217: actual published 1904 app, carriage-door stands, Full/Light and credited Images tab.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright' : 'playwright');
const site=path.resolve(root,'../../site/4d'),out=process.env.QA_OUT || path.join(root,'docs/RESEARCH/glessner-porte-cochere-T-2217/after');
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=(process.env.QA_BASE_URL||`http://127.0.0.1:${server.address().port}`).replace(/\/$/,'');
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
fs.mkdirSync(out,{recursive:true}); const results=[];
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 if(process.env.QA_BOOT_DETAIL)await context.addInitScript(level=>localStorage.setItem('chicago4d.settings',JSON.stringify({detail:level})),process.env.QA_BOOT_DETAIL);
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>bad.push(r.url()+':'+r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().includes('glessner_house')&&r.url().endsWith('.glb'))assets.push({url:r.url(),status:r.status()})});
 await page.goto(`${base}/1904/${process.env.QA_SEARCH||''}`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id,detail:__chicago4d.detail}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 console.log(label+' boot ready');
 if(process.env.QA_BOOT_DETAIL && boot.detail!==process.env.QA_BOOT_DETAIL)throw Error('Requested saved boot detail was not used');
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 const roundTrip=process.env.QA_CYCLE_DETAIL ? await page.evaluate(async()=>{
  const a=__chicago4d,first={...a.contextCity.census};
  await a.setDetail('balanced');const balanced={...a.contextCity.census};
  await a.setDetail('light');const light={...a.contextCity.census};
  if(JSON.stringify(first)!==JSON.stringify(light)||balanced.triangles<=light.triangles)throw Error('Context detail round trip did not restore its exact census');
  return {first,balanced,light,season:a.season?.current};
 }) : null;
 await page.waitForFunction(detail=>{const s=__chicago4d.streetTrees.stats;return s.detail===detail && (s.mode==='hidden'||s.drawCalls===1);},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 console.log(label+' selected '+detail+' and entered scene');
 const stands=[];
 // Prairie passage and both leaf faces; local metres, east/north/up.
 const cameras=[['porte',[57,2.36,1.65],[43,2.36,.45]],['passage',[46,2.36,1.65],[40,2.36,.4]],['north-leaf',[47.3,1.25,1.35],[48.3,3.35,1.25]],['south-leaf',[47.3,3.35,1.35],[48.3,1.1,1.25]],['passage-out',[42.5,2.0,1.65],[49.0,2.356,1.2]]];
 for(const [name,pos,target] of cameras.filter(([name])=>!process.env.QA_VIEW||name===process.env.QA_VIEW)){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);
   const modes=new Set();a.scene3d.traverse(o=>{for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.userData.glassMode)modes.add(m.userData.glassMode)});
   const heightSamples=[49,50,53.66,54.2,46,41.1].map(x=>{const q=en([x,2.36,0]);return {x,terrain:a.terrain.surfaceHeight(q[0],q[1])-ground}});
   return {placement:pl,ground,heightSamples,detail:a.detail,glassModes:[...modes],problems:a.problems,stats:a.stats(),camera:p,target:t};
  },{pos,target});
  await page.screenshot({path:path.join(out,`${label}-${name}.png`)});stands.push({name,...observation});console.log(label+' captured '+name);
  if(label==='desktop' && name==='service-front'){
   // An additional architectural inspection through the shipped Hidden setting.
   // The ordinary summer capture and its budget receipt above remain the gate.
   const clear=await page.evaluate(async()=>{const a=__chicago4d;await a.streetTrees.setMode('hidden');a.renderer.render(a.scene3d,a.camera);return {mode:'hidden',stats:a.stats()}});
   await page.screenshot({path:path.join(out,`${label}-${name}-trees-hidden.png`)});
   stands.at(-1).additionalClearView=clear;
   await page.evaluate(async()=>{const a=__chicago4d;await a.streetTrees.setMode('summer');a.renderer.render(a.scene3d,a.camera)});
  }
 }
 if(label==='mobile' && process.env.QA_IMAGES){
  await page.evaluate(()=>__chicago4d.pick('glessner_house'));
  await page.waitForFunction(()=>document.querySelector('#popup [data-pop-tab="images"]'));
  await page.evaluate(()=>document.querySelector('#popup [data-pop-tab="images"]').click());
  await page.waitForFunction(()=>!document.querySelector('#popup [data-pop-pane="images"]')?.textContent.includes('LOADING IMAGE INDEX'));
  const tiles=page.locator('#popup [data-pop-pane="images"] .pop-pic-tile');
  for(let i=0;i<await tiles.count();i++){
   await tiles.nth(i).scrollIntoViewIfNeeded();
   await page.waitForFunction(i=>{const img=document.querySelectorAll('#popup [data-pop-pane="images"] .pop-pic-tile')[i]?.querySelector('img');return img?.complete&&img.naturalWidth>0;},i,{timeout:60000});
  }
  if(await tiles.count())await tiles.first().scrollIntoViewIfNeeded();
  const pictures=await page.evaluate(()=>{const p=document.querySelector('#popup [data-pop-pane="images"]');return {shown:!p.hidden,tiles:[...p.querySelectorAll('.pop-pic-tile')].map(t=>({text:t.textContent.trim(),credit:t.querySelector('.pop-pic-tile-credit')?.textContent.trim(),loaded:!!t.querySelector('img')?.naturalWidth})),links:[...p.querySelectorAll('.pop-pic-list li')].map(t=>t.textContent.trim())}});
  if(!pictures.shown||!pictures.tiles.length||pictures.tiles.some(t=>!t.credit||!t.loaded))throw Error('Images tab lacks credited pictures');
  fs.writeFileSync(path.join(out,'mobile-images.json'),JSON.stringify(pictures,null,2)+'\n');
  await page.screenshot({path:path.join(out,'mobile-images.png')});
 }
 let budgetRoundTrip=null;
 if(process.env.QA_CHECK_BUDGET_LEVELS && label==='desktop'){
  budgetRoundTrip=await page.evaluate(async()=>{
   const a=__chicago4d,full={...a.stats().budget};
   await a.setDetail('light');const light={...a.stats().budget};
   await a.setDetail('full');const restored={...a.stats().budget};
   if(full.drawCalls!==360||full.triangles!==4600000||light.drawCalls!==330||light.triangles!==1190000||JSON.stringify(full)!==JSON.stringify(restored))throw Error('Full inspection allowance leaked across the detail setting');
   return {full,light,restored};
  });
 }
 results.push({label,viewport,detail,boot,roundTrip,budgetRoundTrip,errors,bad,assets,stands});
 // T-2219: measured before 3,890,920; with T-2473 trees 4,274,524; Full-only 4.6M.
 if(label==='desktop' && stands.some(x=>x.stats.budget.triangles!==4600000))throw Error('Selected Full inspection allowance drifted from measured 4.6M ceiling');
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify({errors,bad,stands}));
 if(!assets.some(a=>a.url.endsWith(detail==='light'?'.light.glb':'__as_built_1887.glb')))throw Error('Expected canonical detail asset did not load');
 await context.close();console.log(label+' actual published 1904 app: PASS');
}
}finally{fs.writeFileSync(path.join(out,process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+'.json' : 'browser-validation.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot, full desktop and light mobile, 1280×800 / 390×780; animation paused after readiness for deterministic review cameras. Normal scene geometry, materials, lighting and shadows; fixed matched cameras before/after.',results},null,2)+'\n');await browser.close();server.close();}
