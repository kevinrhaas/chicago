// T-2833: the 1904 context city as it is seen down the streets out of the worked Prairie band, in
// the actual published /1904/ app. The owner's two iPhone views (north up Prairie from 1626, west
// along 18th from 266 E 18th) and three more street ends, in scene-local metres (east, north,
// height above the ground there), at 1280x800 full and 390x780 light, with JS heap, the context
// layer's census and the frame's triangles.
//   node tools/qa_context_ends_t2833.mjs                (after tools/publish.sh)
//   QA_VIEWPORT=mobile QA_TAG=before QA_OUT=/some/dir node tools/qa_context_ends_t2833.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=await import('/opt/node-tools/node_modules/playwright/index.mjs'));}
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/context-ends-2833'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target]
const STANDS=[
 ['prairie-north-from-1626',[1399,-3000,1.7],[1394,-2800,7]],
 ['18th-west-from-266',[1372,-3204,1.7],[1180,-3236,6]],
 ['prairie-south-from-2100',[1407,-3690,1.7],[1412,-3950,6]],
 ['16th-west-from-prairie',[1392,-2950,1.7],[1190,-2955,6]],
 ['20th-west-from-calumet',[1520,-3478,1.7],[1300,-3478,6]],
];
const ONLY=process.env.QA_STANDS?process.env.QA_STANDS.split(','):null;
const RUN=ONLY?STANDS.filter(s=>ONLY.includes(s[0])):STANDS;
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
 const stands=[];
 for(const [name,pos,target] of RUN){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.streetTrees?.update?.(0,a.camera);a.contextCity?.update?.(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();frame();
   return {detail:a.detail,problems:a.problems,stats:a.stats(),context:a.contextCity?.census};
  },{pos,target});
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:85});stands.push({name,...observation});
  console.log(TAG,label,name,observation.stats.triangles,JSON.stringify(observation.context));
 }
 results.push({label,viewport,detail,js_heap_used_bytes:heap.usedSize,errors,bad,stands});
 console.log(`${TAG} ${label}: heap ${(heap.usedSize/1e6).toFixed(1)} MB errors ${errors.length} bad ${bad.length}`);
 await context.close();
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'readings-'+TAG+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+'.json'),JSON.stringify({method:'published /1904/ app, animation paused after readiness, two renders per stand; heap after a forced GC',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
