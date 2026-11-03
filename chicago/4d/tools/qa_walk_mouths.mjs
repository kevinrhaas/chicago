// Stills of the 1904 app from given stands, for walk-to-sidewalk joins (T-3274).
//   QA_SHOTS=shots.json QA_OUT=dir QA_TAG=before node tools/qa_walk_mouths.mjs   (after tools/publish.sh)
// shots.json: [{name, eye:[e,n,h], at:[e,n,h], viewport:'desktop'|'mobile'}]
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(process.env.QA_SITE||path.resolve(root,'../../site/4d'));
const out=path.resolve(process.env.QA_OUT||'docs/RESEARCH/walk-mouths/stills'),TAG=process.env.QA_TAG||'after';
const SHOTS=JSON.parse(fs.readFileSync(process.env.QA_SHOTS,'utf8'));
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 const mine=SHOTS.filter(s=>(s.viewport||'desktop')===label);if(!mine.length)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:900000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome?.state==='welcome',null,{timeout:900000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 for(const s of mine){
  const [pe,pn,eh]=s.eye,[te,tn,th]=s.at;
  for(let k=0;k<3;k++) await page.evaluate(({pe,pn,te,tn,eh,th})=>{const a=__chicago4d;
    const p=[pe,pn,a.terrain.surfaceHeight(pe,pn)+eh],t=[te,tn,a.terrain.surfaceHeight(te,tn)+th];
    a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:eh,yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
    a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
    a.streetTrees?.update?.(0);a.streetTrees?.settle?.();a.renderer.render(a.scene3d,a.camera);},{pe,pn,te,tn,eh,th});
  await page.waitForTimeout(1500);
  await page.evaluate(()=>{const a=__chicago4d;a.renderer.render(a.scene3d,a.camera);});
  const file=`${TAG}-${label}-${s.name}.jpg`;
  await page.screenshot({path:path.join(out,file),type:'jpeg',quality:82});console.log('shot',file);
 }
 if(errors.length)console.log('pageerrors',label,errors.slice(0,5));
 await context.close();
}
}catch(e){failed=e;}
finally{await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
