// T-2334: the Prairie district draft's west side of the 16th-18th block, read in the actual published
// /1904/ app. tools/qa_draft_t2330.mjs's harness, moved two blocks north: T-2160's acceptance 3 —
// both walks, the west alley and the air, plus the 1700/1706 pair seen from across the avenue —
// in scene-local metres (east, north, height above the ground there), at 1280x800 full and
// 390x780 light, with load, JS heap and frame time.
//   node tools/qa_draft_t2334.mjs                     (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_draft_t2334.mjs
//   QA_TAG=before                                     the reading taken before the draft
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/prairie-draft-16-18-west-2334'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const IDS=['law_house_1620_prairie','glessner_lee_house_1700_prairie','george_glessner_house_1706_prairie','walker_house_1720_prairie','shortall_gregory_house_1638_prairie_coach_house'];
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target]: east, north, metres above the ground at the eye (the target's at its own)
const STANDS=[
 ['north-walk',[1391.2,-2962,1.7],[1362,-3010,7]],
 ['across-1620',[1408.6,-3030,1.7],[1372,-3022,7]],
 ['across-1700',[1409.2,-3098,1.7],[1372,-3098,8]],
 ['south-walk',[1392.4,-3195,1.7],[1366,-3140,7]],
 ['alley',[1330.6,-2965,1.7],[1332,-3080,4.5]],
 ['air',[1470,-2990,75],[1360,-3080,0]],
];
const PART=process.env.QA_PART||'';
const RUN=PART==='a'?STANDS.slice(0,3):PART==='b'?STANDS.slice(3):STANDS;
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',async r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().endsWith('.glb')&&(r.url().includes('__draft_1904')||r.url().includes('glessner_house')))assets.push({url:r.url().replace(/^.*\/data\//,'data/'),status:r.status(),bytes:Number(r.headers()['content-length']||0)})});
 const t0=Date.now();
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 const loadMs=Date.now()-t0;
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const placed=await page.evaluate(ids=>ids.filter(id=>Boolean(__chicago4d.registry.get(id)?.sidecar?.placement)),IDS);
 if(TAG!=='before'&&placed.length!==IDS.length)throw Error(`only ${placed} of ${IDS} are in the 1904 registry`);
 const cdp=await context.newCDPSession(page);
 await cdp.send('HeapProfiler.collectGarbage');
 const heap=await cdp.send('Runtime.getHeapUsage');
 const drafts=await page.evaluate(()=>[...__chicago4d.registry.keys()].filter(k=>/_prairie(_coach_house)?$/.test(k)&&k!=='keith_house_1808_prairie').length);
 const stands=[];
 for(const [name,pos,target] of RUN){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();
   // a timed frame: render and wait for the GPU (a one-pixel read) — 12 of them, median
   const gl=a.renderer.getContext(),px=new Uint8Array(4),ms=[];
   for(let i=0;i<12;i++){const s=performance.now();frame();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);ms.push(performance.now()-s);}
   ms.sort((x,y)=>x-y);
   return {detail:a.detail,problems:a.problems,stats:a.stats(),frame_ms_median:Math.round(ms[6]*10)/10,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100)};
  },{pos,target});
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,js_heap_used_bytes:heap.usedSize,js_heap_total_bytes:heap.totalSize,draft_records_in_registry:drafts,placed,boot,errors,bad,glb:{count:assets.length,bytes:assets.reduce((s,a)=>s+a.bytes,0)},stands};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 await context.close();console.log(`${TAG} ${label}: the published 1904 app, ${drafts} draft record(s), heap ${(heap.usedSize/1e6).toFixed(1)} MB, load ${loadMs} ms: PASS`);
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'browser-validation-'+TAG+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+(PART?'-'+PART:'')+'.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot (TAG '+TAG+'); js heap after a forced GC via CDP Runtime.getHeapUsage; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is 12 renders each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
