// T-2225 published planting review: frozen before/after cameras and unchanged scene budgets.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright' : 'playwright');
const site=path.resolve(root,'../../site/4d'),out=process.env.QA_OUT || path.join(root,'docs/RESEARCH/glessner-vines-T-2225/browser');
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=(process.env.QA_BASE_URL||`http://127.0.0.1:${server.address().port}`).replace(/\/$/,'');
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
fs.mkdirSync(out,{recursive:true}); const results=[];
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['balanced',{width:1280,height:800},'balanced'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 if(process.env.QA_BOOT_DETAIL)await context.addInitScript(level=>localStorage.setItem('chicago4d.settings',JSON.stringify({detail:level})),process.env.QA_BOOT_DETAIL);
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>bad.push(r.url()+':'+r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().includes('glessner_house')&&r.url().endsWith('.glb'))assets.push({url:r.url(),status:r.status()})});
 console.log(label+' navigation starting');
 await page.goto(`${base}/1904/${process.env.QA_SEARCH||''}`,{waitUntil:'domcontentloaded'});
 console.log(label+' DOM loaded');
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:1000}).catch(error=>{fs.writeFileSync(path.join(out,'startup-failure-'+label+'.json'),JSON.stringify({error:String(error),errors,bad,assets,url:page.url()},null,2));throw error;});
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
 await page.waitForFunction(detail=>{const s=__chicago4d.streetTrees.stats;return s.detail===detail && (s.mode==='hidden'||s.drawCalls===(detail==='full'?2:1));},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 console.log(label+' selected '+detail+' and entered scene');
 const stands=[];
 // Planting stands; local metres, east/north/up. Frozen before implementation.
 const cameras=[['prairie-front',[56,17,7],[49,12,4]],['front-close',[51.6,10,2],[49.15,10,2]],['court-south',[26,5,2.5],[26,.2,1.7]],['court-west',[20,7,4],[10.82,7,2]],['court-north',[27,6,3],[27,15.5,2]]];
 for(const [name,pos,target] of cameras.filter(([name])=>!process.env.QA_VIEW||process.env.QA_VIEW.split(',').includes(name))){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);
   const modes=new Set();a.scene3d.traverse(o=>{for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.userData.glassMode)modes.add(m.userData.glassMode)});
   const heightSamples=[['gate',0,2.4],['gate-court',.16,2.4],['stair-foot-left',14.9809,10.0279],['stair-foot-right',16.1696,10.0279],['landing-pier',18.8352,12.9306]].map(([name,x,y])=>{const q=en([x,y,0]);return {name,x,y,terrain:a.terrain.surfaceHeight(q[0],q[1])-ground}});
   return {placement:pl,ground,heightSamples,detail:a.detail,glassModes:[...modes],problems:a.problems,stats:a.stats(),camera:p,target:t};
  },{pos,target});
  await page.screenshot({path:path.join(out,`${label}-${name}.png`)});stands.push({name,...observation});
  // A workspace interruption must not discard measurements for saved images.
  // This is partial evidence only; the completed result and assertions below
  // remain the authority for a successful run.
  fs.writeFileSync(path.join(out,`capture-checkpoint-${label}.json`),JSON.stringify({partial:true,label,viewport,detail,boot,errors,bad,assets,stands},null,2)+'\n');
  console.log(label+' captured '+name);

 }
 let confidenceView=null;
 if(process.env.QA_CONFIDENCE){
  // The phone's north-court crop puts the vine outside the image. Reuse the
  // measured west-court stand so the confidence capture actually shows leaves.
  const stand=stands.find(s=>s.name==='court-west')||stands[0];confidenceView=stand.name;
  await page.evaluate(({p,t})=>{
   const a=__chicago4d;a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
  },{p:stand.camera,t:stand.target});
  const on=await page.evaluate(()=>{const a=__chicago4d;a.confidence.set(true);a.renderer.render(a.scene3d,a.camera);return a.confidence.enabled;});
  if(!on)throw Error('Confidence display did not enable');
  await page.screenshot({path:path.join(out,`${label}-confidence.png`)});
  await page.evaluate(()=>{const a=__chicago4d;a.confidence.set(false);a.renderer.render(a.scene3d,a.camera);});
 }
 if(process.env.QA_LIBERTY){
  await page.evaluate(()=>__chicago4d.pick('glessner_house'));
  await page.waitForFunction(()=>document.querySelector('#popup [data-pop-tab="liberties"]'));
  await page.evaluate(()=>document.querySelector('#popup [data-pop-tab="liberties"]').click());
  await page.waitForFunction(id=>[...document.querySelectorAll('#popup details.lib')].some(e=>e.dataset.sourceEntity===id),process.env.QA_LIBERTY);
  const liberty=await page.evaluate(id=>{
   const e=[...document.querySelectorAll('#popup details.lib')].find(e=>e.dataset.sourceEntity===id);
   e.open=true;e.scrollIntoView({block:'center'});
   return {id:e.dataset.sourceEntity,text:e.textContent.trim(),shown:!e.closest('[data-pop-pane]').hidden};
  },process.env.QA_LIBERTY);
  if(!liberty.shown||!liberty.text.includes('reconstructed')||!liberty.text.includes('Selective July vines'))throw Error('Vine liberty is absent or lacks its reconstruction scope');
  fs.writeFileSync(path.join(out,`${label}-liberty.json`),JSON.stringify(liberty,null,2)+'\n');
  await page.screenshot({path:path.join(out,`${label}-liberty.png`)});
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
  const pictures=await page.evaluate(()=>{const p=document.querySelector('#popup [data-pop-pane="images"]');return {shown:!p.hidden,tiles:[...p.querySelectorAll('.pop-pic-tile')].map(t=>({label:t.getAttribute('aria-label'),text:t.textContent.trim(),credit:t.querySelector('.pop-pic-tile-credit')?.textContent.trim(),loaded:!!t.querySelector('img')?.naturalWidth})),links:[...p.querySelectorAll('.pop-pic-list li')].map(t=>t.textContent.trim())}});
  if(!pictures.shown||!pictures.tiles.length||pictures.tiles.some(t=>!t.credit||!t.loaded))throw Error('Images tab lacks credited pictures');
  for(const title of ['North courtyard service stairs and rails']){
   const tile=pictures.tiles.find(t=>t.label.includes(title));
   if(!tile?.loaded||!tile.credit.includes('w_lemay')||!tile.credit.includes('CC BY-SA 2.0'))throw Error('New service-stair reference is absent or uncredited: '+title);
  }
  fs.writeFileSync(path.join(out,'mobile-images.json'),JSON.stringify(pictures,null,2)+'\n');
  await page.screenshot({path:path.join(out,'mobile-images.png')});
 }
 let budgetRoundTrip=null;
 if(process.env.QA_CHECK_BUDGET_LEVELS && label==='desktop'){
  budgetRoundTrip=await page.evaluate(async()=>{
   const a=__chicago4d,full={...a.stats().budget};
   await a.setDetail('light');const light={...a.stats().budget};
   await a.setDetail('full');const restored={...a.stats().budget};
   if(full.drawCalls!==360||full.triangles!==4600000||light.drawCalls!==330||light.triangles!==1270000||JSON.stringify(full)!==JSON.stringify(restored))throw Error('Full inspection allowance leaked across the detail setting');
   return {full,light,restored};
  });
 }
 results.push({label,viewport,detail,boot,roundTrip,budgetRoundTrip,confidenceView,errors,bad,assets,stands});
 fs.writeFileSync(process.env.QA_PROGRESS_PATH||path.join(out,'browser-validation-progress.json'),JSON.stringify({partial:true,results},null,2)+'\n');
 // T-2219: measured before 3,890,920; with T-2473 trees 4,274,524; Full-only 4.6M.
 if(label==='desktop' && stands.some(x=>x.stats.budget.triangles!==4600000))throw Error('Selected Full inspection allowance drifted from measured 4.6M ceiling');
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify({errors,bad,stands}));
 if(!assets.some(a=>a.url.endsWith(detail==='full'?'__as_built_1887.glb':'.light.glb')))throw Error('Expected canonical detail asset did not load');
 await context.close();console.log(label+' actual published 1904 app loaded; budget results retained per stand');
}
}finally{fs.writeFileSync(path.join(out,process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+'.json' : 'browser-validation.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot, full desktop and light mobile, 1280×800 / 390×780; animation paused after readiness for deterministic review cameras. Normal scene geometry, materials, lighting and shadows; fixed matched cameras before/after.',results},null,2)+'\n');fs.rmSync(process.env.QA_PROGRESS_PATH||path.join(out,'browser-validation-progress.json'),{force:true});await browser.close();server.close();}
