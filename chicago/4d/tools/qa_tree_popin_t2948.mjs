// T-2948: the 1904 parkway elms as the owner walks them, south down Prairie from 18th past 1801
// and 1808 (his three screenshots, 2026-10-20). Each stand is rendered in the published /1904/ app
// at 1280x800 full and 390x780 light, with the frame's triangles and draw calls and the street
// trees' census. QA_WALK=1 also renders a short walk south, a frame every QA_STEP metres, so a
// level change or a shadow edge that snaps shows as a jump between neighbouring frames.
//   node tools/qa_tree_popin_t2948.mjs                         (after tools/publish.sh)
//   QA_BEFORE=/dir/with/old/js QA_TAG=before node tools/qa_tree_popin_t2948.mjs
//   QA_VIEWPORT=mobile QA_WALK=1 QA_OUT=/some/dir node tools/qa_tree_popin_t2948.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=await import('/opt/node-tools/node_modules/playwright/index.mjs'));}
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/tree-popin-2948'),TAG=process.env.QA_TAG||'after';
const BEFORE=process.env.QA_BEFORE||null;
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm','.webp':'image/webp'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));
 // A "before" reading serves the old copy of any script QA_BEFORE holds, by name.
 if(BEFORE&&/\/js\/[^/]+\.js$/.test(p)&&fs.existsSync(path.join(BEFORE,path.basename(p))))p=path.join(BEFORE,path.basename(p));
 try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye (east, north, height above ground), target]: the owner's stands, looking south.
const STANDS=[
 ['prairie-south-from-1801',[1404,-3222,1.7],[1408,-3460,6]],
 ['prairie-south-from-1808',[1401,-3236,1.7],[1403,-3470,9]],
 ['prairie-south-up-into-crowns',[1401,-3240,1.7],[1403,-3300,22]],
];
const ONLY=process.env.QA_STANDS?process.env.QA_STANDS.split(','):null;
const RUN=ONLY?STANDS.filter(s=>ONLY.includes(s[0])):STANDS;
const WALK=process.env.QA_WALK==='1',STEP=Number(process.env.QA_STEP||2),FRAMES=Number(process.env.QA_FRAMES||8);
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT&&process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(400000);
 const errors=[],bad=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status())});
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:400000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:400000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const cdp=await context.newCDPSession(page);
 await cdp.send('HeapProfiler.collectGarbage');
 const heap=await cdp.send('Runtime.getHeapUsage');
 // One frame from a stand. `dt` is the time the street trees are told passed since the last
 // frame (0 holds the wind and settles any dissolve, so a still reads the levels it will hold).
 const frame=(pos,target,dt)=>page.evaluate(({pos,target,dt})=>{const a=__chicago4d;
  const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
  a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
  const draw=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
   a.streetTrees?.update?.(dt,a.camera);if(!dt)a.streetTrees?.settle?.();a.contextCity?.update?.(a.camera);a.renderer.info.reset();a.renderer.render(a.scene3d,a.camera);};
  draw();
  const info={triangles:a.renderer.info.render.triangles,calls:a.renderer.info.render.calls};
  const st=a.streetTrees?.stats??{};
  return {detail:a.detail,problems:a.problems.slice(-5),info,stats:a.stats(),trees:{triangles:st.triangles,drawCalls:st.drawCalls,grown:st.grown&&{near:st.grown.near,mid:st.grown.mid,far:st.grown.far,distant:st.grown.distant,shade:st.grown.shade,fading:st.grown.fading,shadowTriangles:st.grown.shadowTriangles}}};
 },{pos,target,dt});
 const stands=[];
 for(const [name,pos,target] of RUN){
  const observation=await frame(pos,target,0);
  await frame(pos,target,0);
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:85,timeout:400000});stands.push({name,...observation});
  console.log(TAG,label,name,JSON.stringify(observation.info),JSON.stringify(observation.trees));
 }
 if(WALK){
  // South down the middle of Prairie from 18th, a frame every STEP metres at a walk's pace.
  const [, pos0, target0]=STANDS[0];
  for(let i=0;i<FRAMES;i++){
   const pos=[pos0[0],pos0[1]-i*STEP,pos0[2]],target=[target0[0],target0[1]-i*STEP,target0[2]];
   const o=await frame(pos,target,STEP/1.4);
   await page.screenshot({path:path.join(out,`${TAG}-${label}-walk-${String(i).padStart(2,'0')}.jpg`),type:'jpeg',quality:85,timeout:400000});
   stands.push({name:`walk-${i}`,...o});
   console.log(TAG,label,`walk ${i}`,JSON.stringify(o.info),JSON.stringify(o.trees));
  }
 }
 results.push({label,viewport,detail,js_heap_used_bytes:heap.usedSize,errors,bad,stands});
 console.log(`${TAG} ${label}: heap ${(heap.usedSize/1e6).toFixed(1)} MB errors ${errors.length} bad ${bad.length}`);
 await context.close();
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'readings-'+TAG+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+'.json'),JSON.stringify({method:'published /1904/ app, animation loop stopped after readiness, renders driven per stand; heap after a forced GC',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
