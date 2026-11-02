// T-1936: the east side's alley buildings behind 1800-1900 Prairie Avenue, refined by T-1936 (1811 Coleman-Ames,
// 1815 Sears-Meeker, 1827 Doane and 1905 Marshall Field coach houses), read in the actual published /1904/ app:
// T-1936's acceptance 3 — their yard fronts (west faces) from over the houses' back yards, the alley run from
// either end, their east faces from the alley and their roofs from the air — in scene-local metres (east, north,
// height above the ground there), at 1280x800 full and 390x780 light, with load, JS heap, the four buildings'
// GLB bytes and frame time. Adapted from tools/qa_k01_t3283.mjs.
//   node tools/qa_t1936_coach_houses.mjs                       (after tools/publish.sh)
//   QA_VIEWPORT=mobile QA_PART=a QA_FRAMES=3 node tools/qa_t1936_coach_houses.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/t1936-east-coach-houses-views'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const IDS=['coleman_ames_house_1811_prairie_coach_house','sears_meeker_house_1815_prairie_coach_house','doane_house_1827_prairie_coach_house','marshall_field_house_1905_prairie_coach_house'];
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Content-Length':fs.statSync(p).size});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target]: east, north, metres above the ground at the eye (the target's at its own)
const STANDS=[
 ['front-yards',[1432,-3283,32],[1461,-3296,3]],
 ['oblique-alley-north',[1458.4,-3258,1.7],[1466,-3320,4]],
 ['rear-alley-south',[1471,-3375,1.7],[1463,-3320,5]],
 ['roof',[1500,-3250,60],[1461,-3300,0]],
];
const PART=process.env.QA_PART||'';
const RUN=PART==='a'?STANDS.slice(0,2):PART==='b'?STANDS.slice(2):STANDS;
const FRAMES=Number(process.env.QA_FRAMES||12);
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',async r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().endsWith('.glb')&&IDS.some(id=>r.url().includes(id+'__')))assets.push({url:r.url().replace(/^.*\/data\//,'data/'),status:r.status(),bytes:Number(r.headers()['content-length']||0)})});
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
  const observation=await page.evaluate(({pos,target,frames})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();
   // a timed frame: render and wait for the GPU (a one-pixel read) — 12 of them, median
   const gl=a.renderer.getContext(),px=new Uint8Array(4),ms=[];
   for(let i=0;i<frames;i++){const s=performance.now();frame();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);ms.push(performance.now()-s);}
   ms.sort((x,y)=>x-y);const med=ms[Math.floor(ms.length/2)];
   return {detail:a.detail,problems:a.problems,stats:a.stats(),frame_ms_median:Math.round(med*10)/10,frames_timed:frames,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100)};
  },{pos,target,frames:FRAMES});
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,js_heap_used_bytes:heap.usedSize,js_heap_total_bytes:heap.totalSize,prairie_records_in_registry:drafts,placed,boot,errors,bad,glb:{count:assets.length,bytes:assets.reduce((s,a)=>s+a.bytes,0)},stands};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 await context.close();console.log(`${TAG} ${label}: the published 1904 app, ${drafts} Prairie record(s), heap ${(heap.usedSize/1e6).toFixed(1)} MB, load ${loadMs} ms: PASS`);
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'browser-validation-'+TAG+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+(PART?'-'+PART:'')+'.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot (TAG '+TAG+'); js heap after a forced GC via CDP Runtime.getHeapUsage; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is the median of QA_FRAMES renders (frames_timed) each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
