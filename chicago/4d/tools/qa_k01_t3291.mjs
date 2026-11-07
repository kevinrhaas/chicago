// T-3291: 1912 Prairie (Moulton/Lowden) read in the actual published /1904/ app from the views T-1899's
// acceptance asks for — front, oblique (from both walks), rear (the yard, and over the alley) and roof
// (the air) — at 1280x800 full and 390x780 light, with load, JS heap, the house's GLB bytes, draw calls,
// triangles and frame time. tools/qa_k01_t3187.mjs's harness, closed in on 1912, with T-3290's notes:
// the street stands stand on the avenue's roadway (about 14 m out), not 30 m out in the opposite yard,
// and every stand with an altitude is a fly teleport.
//   node tools/qa_k01_t3291.mjs                       (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_k01_t3291.mjs
//   QA_PART=a|b                                       the street stands | the rear and roof stands
//   QA_TAG=before                                     the reading taken before this ticket's change
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/k01-1912-rear-roof-views-3291'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const IDS=['moulton_lowden_house_1912_prairie','moulton_lowden_house_1912_prairie_coach_house'];
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Content-Length':fs.statSync(p).size});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target]: east, north, metres above the ground at the eye (the target's at its own)
// The front block stands at e 1365.8-1386.2, n -3401.1 to -3388.1; its brick rear ranges reach back
// to e 1358.4, and the coach house stands at e 1341.0-1350.3 across the yard. The avenue's walk
// and parkway run to about e 1400, so the street stands stand out on its roadway; the rear stands
// stand over the alley, the elevation square on and the oblique from the north-west.
const STANDS=[
 ['front',[1409,-3394.6,1.7],[1376,-3394.6,8]],
 ['oblique-south',[1399,-3418,1.7],[1378,-3396,6]],
 ['oblique-north',[1405,-3373,1.7],[1378,-3393,7]],
 ['rear',[1335,-3394.6,18],[1364,-3394.6,7]],
 ['rear-alley',[1334,-3376,14],[1362,-3396,8]],
 ['roof',[1394,-3374,46],[1372,-3395,8]],
];
const PART=process.env.QA_PART||'';
const RUN=PART==='a'?STANDS.slice(0,3):PART==='b'?STANDS.slice(3):PART?STANDS.filter(s=>s[0]===PART):STANDS;
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',async r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().endsWith('.glb')&&(r.url().includes('/moulton_lowden_house_1912_prairie')))assets.push({url:r.url().replace(/^.*\/data\//,'data/'),status:r.status(),bytes:Number(r.headers()['content-length']||0)})});
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
 const prairie=await page.evaluate(()=>[...__chicago4d.registry.keys()].filter(k=>/_prairie(_coach_house)?$/.test(k)).length);
 const stands=[];
 for(const [name,pos,target] of RUN){
  const observation=await page.evaluate(({pos,target,N})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();
   // a timed frame: render and wait for the GPU (a one-pixel read) — QA_FRAMES of them (5), median;
   // T-3290 measured a desktop Full stand at over a minute with 12, so five keep a part under the cap
   const gl=a.renderer.getContext(),px=new Uint8Array(4),ms=[];
   for(let i=0;i<N;i++){const s=performance.now();frame();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);ms.push(performance.now()-s);}
   ms.sort((x,y)=>x-y);
   return {detail:a.detail,problems:a.problems,stats:a.stats(),frame_ms_median:Math.round(ms[N>>1]*10)/10,frames_timed:N,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100)};
  },{pos,target,N:Number(process.env.QA_FRAMES||5)});
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,js_heap_used_bytes:heap.usedSize,js_heap_total_bytes:heap.totalSize,prairie_records_in_registry:prairie,placed,boot,errors,bad,glb:{count:assets.length,bytes:assets.reduce((s,a)=>s+a.bytes,0)},stands};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 await context.close();console.log(`${TAG} ${label}: the published 1904 app, ${prairie} Prairie record(s), heap ${(heap.usedSize/1e6).toFixed(1)} MB, load ${loadMs} ms: PASS`);
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'browser-validation-'+TAG+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+(PART?'-'+PART:'')+'.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot (TAG '+TAG+'); js heap after a forced GC via CDP Runtime.getHeapUsage; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is the median of QA_FRAMES (default 5) renders, each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
