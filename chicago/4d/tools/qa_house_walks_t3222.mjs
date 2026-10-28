// T-3222 (from T-3214's tools/qa_house_walks_t3214.mjs): 1638 Shortall-Gregory's front walk, read
// in the actual published /1904/ app (tools/qa_draft_t2352.mjs's harness). The walk is turned
// (in at the gateway, north along the fence's back, west to the porch stair), so besides the
// stills — 'front' from the far edge of the public walk, 'gate' from the public walk outside the
// gateway looking up the walk, 'stair' from the walk's turn looking at the stair — the visitor is
// walked on foot by the app's own walker (footprints, step-up rule and all) from the public walk
// through each corner of the walk to the stair's foot. 'ground' reads the app's terrain over the
// house's bed at points along the walk's legs: what yard.grade_m lifts the flags onto.
//   node tools/qa_house_walks_t3222.mjs            (after tools/publish.sh)
//   QA_TAG=before QA_BASE=https://chicago.polecat.live/4d/dev node tools/qa_house_walks_t3222.mjs
//                                                   (the dev preview, before this change)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/house-boundaries-T-3222/stills'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
// in the house's frame (u out of the front toward Prairie Avenue, s north along it from the
// front's south end), read off the built house (k16_timber.yard_walk): the stair's foot at u 5.02
// on its axis s 6.53; the walk's legs turn at u 9.17 (the middle of the leg along the fence's
// back) and come out through the gateway on s 0.4475; the street line, the public walk's inner
// edge, at u 10.8
const ID='shortall_gregory_house_1638_prairie_front',FOOT=5.02,AXIS=6.53,TURN=9.17,GATE=0.4475,LINE=10.8;
const LEGS=[[5.02,8.57,5.93,7.13],[8.57,9.77,-0.13,7.13],[9.77,10.8,-0.13,1.025]];
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
 await page.goto(`${process.env.QA_BASE||`http://127.0.0.1:${server.address().port}`}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:900000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome?.state==='welcome',null,{timeout:900000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const geo=await page.evaluate(({id})=>{const a=__chicago4d,r=a.registry.get(id);const p=r?.sidecar?.placement;const b=a.buildings?.positionOf?.(id);return p?{e0:p.local_e,n0:p.local_n,rot:p.rotation_deg,bed:b?b.y:null}:null;},{id:ID});
 if(!geo){results.push({label,id:ID,error:'not in the 1904 registry'});await context.close();continue;}
 const th=geo.rot*Math.PI/180,W=([u,v])=>[geo.e0+u*Math.cos(th)+v*Math.sin(th),geo.n0-u*Math.sin(th)+v*Math.cos(th)];
 const row={label,id:ID,bed_m:geo.bed,stands:[]};
 // the ground over the bed along each leg's middle and edges, every 0.5 m
 if(label==='desktop'&&geo.bed!=null){
  const pts=[];
  for(const [u0,u1,s0,s1] of LEGS)for(let u=u0;u<=u1+1e-6;u+=Math.max(0.25,(u1-u0)/Math.ceil((u1-u0)/0.5)))for(let s=s0;s<=s1+1e-6;s+=Math.max(0.25,(s1-s0)/Math.ceil((s1-s0)/0.5)))pts.push([u,s]);
  pts.push([0,AXIS],[0,GATE]);
  const en=pts.map(W);
  const h=await page.evaluate(({en})=>en.map(([e,n])=>__chicago4d.terrain.surfaceHeight(e,n)),{en});
  row.ground=pts.map(([u,s],i)=>({u:Math.round(u*100)/100,s:Math.round(s*100)/100,rise_m:Math.round((h[i]-geo.bed)*1000)/1000}));
 }
 const stands=[['front',[LINE+4.2,3.2,1.65],[1.0,3.2,2.4]],['gate',[LINE+2.6,GATE-0.1,1.65],[TURN-0.4,GATE+1.6,0.1]],['stair',[TURN+0.4,GATE+1.6,1.65],[FOOT,AXIS,0.9]]];
 for(const [name,eye,tgt] of stands){
  if(label==='mobile'&&name!=='gate')continue;
  const [pe,pn]=W(eye),[te,tn]=W(tgt);
  const o=await page.evaluate(({pe,pn,te,tn,eh,th})=>{const a=__chicago4d;
   const p=[pe,pn,a.terrain.surfaceHeight(pe,pn)+eh],t=[te,tn,a.terrain.surfaceHeight(te,tn)+th];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:eh,yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
   a.streetTrees?.update?.(0);a.streetTrees?.settle?.();
   a.renderer.render(a.scene3d,a.camera);return {problems:a.problems};},{pe,pn,te,tn,eh:eye[2],th:tgt[2]});
  const file=`${TAG}-${label}-shortall_gregory_house_1638-${name}.jpg`;
  await page.screenshot({path:path.join(out,file),type:'jpeg',quality:80});row.stands.push({name,file,problems:(o.problems||[]).length});
 }
 // the walk: on foot from the public walk outside the gateway, through the walk's two corners,
 // to the stair's foot, turning at each corner toward the next
 const way=[[LINE+1.0,GATE],[TURN,GATE],[TURN,AXIS],[FOOT,AXIS]].map(W);
 row.walk=await page.evaluate(({way})=>{const a=__chicago4d,w=a.walker;
  a.setFly(false);w.teleport({local_e:way[0][0],local_n:way[0][1],yaw_deg:Math.atan2(way[1][0]-way[0][0],way[1][1]-way[0][1])*180/Math.PI});
  const intent={yawDelta:0,pitchDelta:0,clearLook(){},flying:false,forward:1,strafe:0,sprint:false};
  const legs=[];let blocked=0;
  for(let k=1;k<way.length;k++){const [te,tn]=way[k];let best=Infinity;
   for(let i=0;i<90;i++){const yaw=Math.atan2(te-w.enu.e,tn-w.enu.n)*180/Math.PI;w.teleport({local_e:w.enu.e,local_n:w.enu.n,yaw_deg:yaw});w.update(0.1,intent);
    const d=Math.hypot(w.enu.e-te,w.enu.n-tn);best=Math.min(best,d);if(w.state.blocked)blocked++;if(d<0.35)break;}
   legs.push(Math.round(best*100)/100);if(best>0.6)break;}
  return {closest_at_each_corner_m:legs,blocked_frames:blocked,reached:legs.length===way.length-1&&legs[legs.length-1]<0.6};},{way});
 results.push(row);console.log(TAG,label,ID,JSON.stringify(row.walk),row.ground?`ground ${Math.min(...row.ground.map(g=>g.rise_m))}..${Math.max(...row.ground.map(g=>g.rise_m))} m`:'');
 if(errors.length)results.push({label,errors});
 await context.close();
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,`walks-${TAG}${process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:''}.json`),JSON.stringify({method:'Actual published /1904/ app; stills at 1280x800 full and 390x780 light; the walk is walker.update(0.1 s, forward) from the public walk outside the gateway through the walk\'s corners to the stair foot, at most 9 s a leg; ground is terrain.surfaceHeight less the bed buildings.positionOf() stood the house on.',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
