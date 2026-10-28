// T-3221: the walks of 1616, 1621, 1623, 1625 and 1637 Prairie (piece 1 of T-3215), read in the
// actual published /1904/ app with T-3206's harness (tools/qa_house_walks_t3206.mjs): for each
// house a still from the far edge of the public walk looking at the door ('front', desktop), a
// still from the walk's mouth looking up it ('gate'), and a walk on foot from the public walk to
// the stoop's foot with the app's own walker for up to 14 s.
//   node tools/qa_house_walks_t3221.mjs            (after tools/publish.sh)
//   QA_VIEWPORT=mobile QA_TAG=before node tools/qa_house_walks_t3221.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/house-boundaries-T-3221/stills'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
// [structure id, street front's depth D (m), the stoop's axis s (m), the walk's start u (m)
//  (the stoop's foot, or a side stoop's flight end), the public walk's inner edge u (m)]
// read off each record's built assembly (k01_frontage.build: depth_m, stoop_s_m(door),
// the K11 stoop foot, depth_m + front_yard_m)
const HOUSES=[
 ['house_1616_prairie',23.5,4.75,26.8,32.76],
 ['house_1621_prairie',13.3,6.16,14.5,17.1],
 ['house_1623_prairie',19.5,3.5,22.9,23.3],
 ['house_1625_prairie',19.45,5.75,20.15,23.23],
 ['spalding_house_1637_prairie',11.0,6.25,15.35,21.2],
];
const ONLY=(process.env.QA_ONLY||'').split(',').filter(Boolean);
const RUN=HOUSES.filter(h=>!ONLY.length||ONLY.includes(h[0]));
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT&&process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:900000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome?.state==='welcome',null,{timeout:900000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 for(const [id,D,axis,foot,pub] of RUN){
  // the house's frame -> local ENU, as walker.js footprintsFrom() turns a sidecar footprint
  const geo=await page.evaluate(({id})=>{const r=__chicago4d.registry.get(id);const p=r?.sidecar?.placement;return p?{e0:p.local_e,n0:p.local_n,rot:p.rotation_deg}:null;},{id});
  if(!geo){results.push({label,id,error:'not in the 1904 registry'});continue;}
  const th=geo.rot*Math.PI/180,W=([u,v])=>[geo.e0+u*Math.cos(th)+v*Math.sin(th),geo.n0-u*Math.sin(th)+v*Math.cos(th)];
  const stands=[['front',[pub+3.2,axis+4.5,1.65],[D+0.5,axis,2.6]],['gate',[pub+1.2,axis,1.65],[D,axis,1.8]]];
  const row={label,id,stands:[]};
  for(const [name,eye,tgt] of stands){
   if(label==='mobile'&&name==='front')continue;
   const [pe,pn]=W(eye),[te,tn]=W(tgt);
   const o=await page.evaluate(({pe,pn,te,tn,eh,th})=>{const a=__chicago4d;
    const p=[pe,pn,a.terrain.surfaceHeight(pe,pn)+eh],t=[te,tn,a.terrain.surfaceHeight(te,tn)+th];
    a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:eh,yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
    a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
    a.streetTrees?.update?.(0);a.streetTrees?.settle?.();
    a.renderer.render(a.scene3d,a.camera);return {problems:a.problems};},{pe,pn,te,tn,eh:eye[2],th:tgt[2]});
   const file=`${TAG}-${label}-${id.replace(/_prairie$/,'')}-${name}.jpg`;
   await page.screenshot({path:path.join(out,file),type:'jpeg',quality:80});row.stands.push({name,file,...o});
  }
  // the walk: on foot at the public walk's middle, square to the door, walking at it
  const [se,sn]=W([pub+1.0,axis]),[fe,fn]=W([foot,axis]);
  row.walk=await page.evaluate(({se,sn,fe,fn})=>{const a=__chicago4d,w=a.walker;
   a.setFly(false);w.teleport({local_e:se,local_n:sn,yaw_deg:Math.atan2(fe-se,fn-sn)*180/Math.PI});
   const intent={yawDelta:0,pitchDelta:0,clearLook(){},flying:false,forward:1,strafe:0,sprint:false};
   let best=Infinity,blocked=0;
   for(let i=0;i<140;i++){w.update(0.1,intent);const d=Math.hypot(w.enu.e-fe,w.enu.n-fn);best=Math.min(best,d);if(w.state.blocked)blocked++;if(d<0.4)break;}
   return {closest_to_foot_m:Math.round(best*100)/100,blocked_frames:blocked,reached:best<0.6};},{se,sn,fe,fn});
  results.push(row);console.log(TAG,label,id,JSON.stringify(row.walk));
 }
 if(errors.length)results.push({label,errors});
 await context.close();
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,`walks-${TAG}${process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:''}.json`),JSON.stringify({method:'Actual published /1904/ app; stills at 1280x800 full and 390x780 light; the walk is walker.update(0.1 s, forward) from the public walk toward the stoop foot, at most 14 s.',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
