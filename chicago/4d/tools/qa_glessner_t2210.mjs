// T-2210 (GA-10): Glessner courtyard brick and limestone under the actual scene light
// AND a neutral diagnostic light, from courtyard stands and the audit views.
// The neutral pass swaps the sky fill for a white hemisphere and whitens the sun
// for the capture only; it is a diagnostic, never shipped lighting.
//   node tools/qa_glessner_t2210.mjs                    desktop (full) + mobile (light)
//   QA_TAG=before- QA_VIEWPORT=desktop node tools/qa_glessner_t2210.mjs
//   QA_STANDS=court-sill QA_LIGHTS=scene,unshadowed QA_OUT=/tmp …   one stand, chosen lights
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/glessner-court-materials-2210'),tag=process.env.QA_TAG||'';
const only=process.env.QA_STANDS?process.env.QA_STANDS.split(','):null;
// 'unshadowed' is the scene light with the sun's shadow map off: it separates a
// shading (normal) defect from a shadow-map one. Diagnostic only.
const LIGHTS=process.env.QA_LIGHTS?process.env.QA_LIGHTS.split(','):['scene','neutral'];
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const STANDS=[['courtyard',[20,4,3.6],[20,18,5.2]],['court-east',[16,6,2.2],[40,10,4]],['court-west',[34,8,2.2],[6,14,4.5]],
 ['court-sill',[18,9.5,1.9],[18,14,2.4]],['court-corner',[36,4,1.8],[30,12,3]]];
const results=[];
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().includes('glessner_house')&&r.url().endsWith('.glb'))assets.push({url:r.url(),status:r.status()})});
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 for(const [name,pos,target] of STANDS){
  if(only&&!only.includes(name))continue;
  for(const light of LIGHTS){
  if(label==='mobile'&&light!=='scene')continue;
  const observation=await page.evaluate(({pos,target,light})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
   const s=a.scene3d,restore=[];
   if(light==='neutral'){const env=s.environment;s.environment=null;restore.push(()=>{s.environment=env});
     s.traverse(o=>{if(o.isDirectionalLight){const c=o.color.clone();o.color.set(0xffffff);restore.push(()=>o.color.copy(c))}else if(o.isHemisphereLight||o.isAmbientLight){const v=o.visible;o.visible=false;restore.push(()=>{o.visible=v})}});}
   if(light==='unshadowed')s.traverse(o=>{if(o.isDirectionalLight&&o.castShadow){o.castShadow=false;restore.push(()=>{o.castShadow=true})}});
   a.__t2210restore=restore;return true;},{pos,target,light});
  if(light==='neutral')await page.evaluate(async()=>{const T=await import('three');const h=new T.HemisphereLight(0xffffff,0x7a7a7a,1.6);__chicago4d.scene3d.add(h);__chicago4d.__t2210restore.push(()=>__chicago4d.scene3d.remove(h));});
  const obs=await page.evaluate(()=>{const a=__chicago4d;a.renderer.render(a.scene3d,a.camera);return {detail:a.detail,problems:a.problems,stats:a.stats(),camera:a.camera.position.toArray()};});
  await page.screenshot({path:path.join(out,`${tag}${label}-${name}${light==='scene'?'':'-'+light}.png`)});
  await page.evaluate(()=>{for(const f of __chicago4d.__t2210restore.reverse())f();__chicago4d.__t2210restore=[];});
  stands.push({name,light,...obs});
  }
 }
 if(!assets.some(a=>a.url.endsWith(detail==='light'?'.light.glb':'__as_built_1887.glb')))throw Error('The '+detail+' canonical asset must load');
 results.push({label,viewport,detail,boot,errors,bad,assets,stands});
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(results.at(-1)));
 await context.close();console.log(label+' actual published 1904 app: PASS · '+stands.length+' capture(s)');
}
}finally{fs.writeFileSync(path.join(out,tag+(process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+'.json' : 'browser-validation.json')),JSON.stringify({method:'Actual published /1904/ app, normal boot, full desktop and light mobile; animation paused after readiness. T-2210: each desktop courtyard stand under the actual scene light and under a neutral diagnostic light (sky fill swapped for a white hemisphere, sun whitened, capture only).',results},null,2)+'\n');await browser.close();server.close();}
