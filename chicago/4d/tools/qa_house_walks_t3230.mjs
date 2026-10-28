// T-3230: the four unpictured K16 frame houses of the 1600 block (1601, 1609, 1611, 1630 Prairie),
// their walks and front boundaries (tools/qa_house_walks_t3205.mjs's harness), read in
// the actual published /1904/ app (tools/qa_draft_t2352.mjs's harness). For each house: a still
// from the far edge of the public walk looking at the door ('front'), a still from the walk's
// mouth looking up it ('gate'), and a walk: the visitor is put on the public walk square to the
// door and walked toward it with the app's own walker (footprints, step-up rule and all) for up
// to 14 s; the reading is how close they got to the stoop's foot.
//   node tools/qa_house_walks_t3230.mjs            (after tools/publish.sh)
//   QA_VIEWPORT=mobile QA_TAG=before node tools/qa_house_walks_t3230.mjs
//   QA_ONLY=house_1601_prairie,...                  a subset
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/house-boundaries-T-3230/stills'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
// [structure id, street front's depth D (m), the stoop's axis s (m), the walk's start u (m)
//  (the stoop's foot, or a side stoop's flight end), the public walk's inner edge u (m)]
// read off each frame house's built yard (k16_yard.dress: the main block's street wall, the
// porch stair's axis, the walk's stoop_foot socket, the street line street_u_m)
const HOUSES=[
 ['house_1601_prairie',15.5,4.15,17.29,18.09],
 ['house_1609_prairie',10.5,1.0,12.49,14.51],
 ['house_1611_prairie',10.5,4.25,12.49,14.47],
 ['house_1630_prairie',13.25,4.35,15.34,21.37],
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
  // the ground the app lays under the yard, over the house's own base (yard.grade_m, T-3206)
  const pts={front:W([D,axis]),street:W([pub,axis]),street_s_lo:W([pub,axis-3]),street_s_hi:W([pub,axis+3])};
  row.grade=await page.evaluate(({id,pts})=>{const a=__chicago4d,b=a.buildings.positionOf(id);if(!b)return null;
   const r={};for(const [k,[e,n]] of Object.entries(pts))r[k]=Math.round((a.terrain.surfaceHeight(e,n)-b.y)*1000)/1000;
   r.per_m_s=Math.round((r.street_s_hi-r.street_s_lo)/6*10000)/10000;return r;},{id,pts});
  // the walk: on foot at the public walk's middle, square to the door, walking at it
  const [se,sn]=W([pub+1.0,axis]),[fe,fn]=W([foot,axis]);
  row.walk=await page.evaluate(({se,sn,fe,fn})=>{const a=__chicago4d,w=a.walker;
   a.setFly(false);w.teleport({local_e:se,local_n:sn,yaw_deg:Math.atan2(fe-se,fn-sn)*180/Math.PI});
   const intent={yawDelta:0,pitchDelta:0,clearLook(){},flying:false,forward:1,strafe:0,sprint:false};
   let best=Infinity,blocked=0;
   for(let i=0;i<140;i++){w.update(0.1,intent);const d=Math.hypot(w.enu.e-fe,w.enu.n-fn);best=Math.min(best,d);if(w.state.blocked)blocked++;if(d<0.4)break;}
   return {closest_to_foot_m:Math.round(best*100)/100,blocked_frames:blocked,reached:best<0.6};},{se,sn,fe,fn});
  results.push(row);console.log(TAG,label,id,JSON.stringify(row.walk),JSON.stringify(row.grade));
 }
 if(errors.length)results.push({label,errors});
 await context.close();
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,`walks-${TAG}${process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:''}.json`),JSON.stringify({method:'Actual published /1904/ app; stills at 1280x800 full and 390x780 light; the walk is walker.update(0.1 s, forward) from the public walk toward the stoop foot, at most 14 s.',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
