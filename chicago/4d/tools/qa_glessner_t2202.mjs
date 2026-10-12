import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright' : 'playwright');
const site=path.resolve(root,'../../site/4d'),out=process.env.QA_OUT || path.join(root,'docs/RESEARCH/glessner-frontage-2202/after');
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
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>bad.push(r.url()+':'+r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().includes('glessner_house')&&r.url().endsWith('.glb'))assets.push({url:r.url(),status:r.status()})});
 await page.goto(`${base}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const contact=await page.evaluate(async()=>{
  const THREE=await import('three'),a=__chicago4d,m=a.buildings.matrixOf('glessner_house');
  if(!m)throw Error('Glessner placement matrix missing');
  a.scene3d.updateMatrixWorld(true);
  const samples=[];
  for(const [name,x,y] of [['entry-sill',49.3,12.5273],['entry-step',49.6,12.5273],['entry-approach',52,12.5273],['entry-walk-join',53.92,12.5273],['carriage-approach',52,2.34],['porte-threshold',49.149,2.34],['passage-front',48,2.30],['passage-middle',45,2.13],['passage-exit',41.1,1.80]]){
   const origin=new THREE.Vector3(x,.8,-y).applyMatrix4(m);
   const ray=new THREE.Raycaster(origin,new THREE.Vector3(0,-1,0),0,1.1);
   // Building batches retain CPU geometry for picking. Some unrelated light
   // scene batches release theirs after upload and cannot be CPU-raycast.
   const hit=ray.intersectObjects(a.buildings.batches,false)[0];
   if(!hit)throw Error('No ground contact at '+name);
   const material=Array.isArray(hit.object.material)?hit.object.material[hit.face.materialIndex]:hit.object.material;
   const terrain=a.terrain.surfaceHeight(hit.point.x,-hit.point.z);
   const structure=hit.object.userData.batchIndex?.[hit.batchId]??hit.object.userData.structure_id;
   const expected=name==='entry-sill'?.2256:name==='entry-step'?.1448:x<48.9966?.064+(48.9966-x)/(48.9966-41.0718)*(.0366-.064):.064;
   samples.push({name,material:material?.name,structure,height:hit.point.y,expectedLocalZ:expected,
    heightError:hit.point.y-m.elements[13]-expected,terrain,clearance:hit.point.y-terrain});
  }
  return {anchorY:m.elements[13],samples};
 });
 // The published palette merges material names. Verify the actual hit's
 // structure identity and designed surface height instead: lawn/terrain
 // cannot pass merely by sharing a texture or an optimised material name.
 if(contact.samples.some(s=>s.structure!=='glessner_house'||Math.abs(s.heightError)>.002||s.clearance<.008||s.clearance>.25))throw Error('Invalid ground contact '+JSON.stringify(contact));
 const stands=[];
 for(const [name,pos,target] of [["entry", [57,12.54,1.65], [49,12.54,1]], ["porte", [57,2.36,1.65], [43,2.36,.45]], ["frontage", [58,23,2.1], [50,10,.75]], ["passage", [46,2.36,1.65], [40,2.36,.4]]]){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);
   const modes=new Set();a.scene3d.traverse(o=>{for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.userData.glassMode)modes.add(m.userData.glassMode)});
   const heightSamples=[49,50,53.66,54.2,46,41.1].map(x=>{const q=en([x,2.36,0]);return {x,terrain:a.terrain.surfaceHeight(q[0],q[1])-ground}});
   return {placement:pl,ground,heightSamples,detail:a.detail,glassModes:[...modes],problems:a.problems,stats:a.stats(),camera:p,target:t};
  },{pos,target});
  await page.screenshot({path:path.join(out,`${label}-${name}.png`)});stands.push({name,...observation});
 }
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget||x.glassModes.length!==1||x.glassModes[0]!=='dark'))throw Error(JSON.stringify({errors,bad,stands}));
 if(!assets.some(a=>a.url.endsWith(detail==='light'?'.light.glb':'__as_built_1887.glb')))throw Error('Expected canonical detail asset did not load');
 results.push({label,viewport,detail,boot,errors,bad,assets,stands,contact});
 await context.close();console.log(label+' actual published 1904 app: PASS');
}
}finally{fs.writeFileSync(path.join(out,process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+'.json' : 'browser-validation.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot, full desktop and light mobile, 1280×800 / 390×780; animation paused after readiness for deterministic review cameras. Normal scene geometry, materials, lighting and shadows; fixed matched cameras before/after.',results},null,2)+'\n');await browser.close();server.close();}
