// T-3199/T-3201/T-3202: the 1904 street furniture at its pictured stands, rendered in the published
// /1904/ app at 1280x800 full and 390x780 light, each stand twice: with the street-furniture layer
// hidden (`before`, the same frame without it) and shown (`after`), with the frame's triangles and
// draw calls, the layer's own census and the page's heap.
//   node tools/qa_street_furniture_t3199.mjs                  (after tools/publish.sh)
//   QA_VIEWPORT=mobile QA_STANDS=glessner-corner QA_OUT=/some/dir node tools/qa_street_furniture_t3199.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=await import('/opt/node-tools/node_modules/playwright/index.mjs'));}
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/street-furniture-3199');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm','.webp':'image/webp'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));
 try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye (east, north, height above ground), target (east, north, height), vertical fov]
const STANDS=[
 // Taylor 2135's stand: the north-east corner of Prairie and 18th, looking south-west at
 // Glessner's corner lamp (its solved camera: about 1.8 m up, a 37-degree vertical field).
 ['glessner-corner',[1408.1,-3205.1,1.8],[1395.7,-3213.5,1.6],37],
 // The Detroit Publishing Pullman view: from the south-west corner across the crossing to
 // Pullman's corner lamp and the Prairie parkway north of it.
 ['pullman-corner',[1392.5,-3219.5,1.7],[1408.4,-3193.0,2.2],46],
 // The 1811 photograph's stand: the west walk south-west of 1811, the lamp at its north lot line.
 ['ames-1811',[1396.5,-3262.0,1.7],[1410.0,-3244.0,3.0],50],
 // Glessner's stable end on 18th, from 18th Street near the alley (the c. 1887 photograph).
 ['glessner-stable-18th',[1336.0,-3201.0,1.7],[1352.0,-3215.0,4.0],50],
 // A long look south down Prairie from 18th: the file of lamps on both parkways.
 ['prairie-south',[1402.0,-3222.0,1.7],[1405.0,-3420.0,4.0],62],
 // T-3201: Pullman's hydrant, from the Prairie roadway south-west of it, the corner lamp behind
 // (the owner's crop of the Detroit Publishing view).
 ['pullman-hydrant',[1401.0,-3194.0,1.6],[1409.4,-3187.9,0.45],34],
 // Tucker's hydrant toward 22nd Street, from the south-east as in the second 2140 photograph.
 ['tucker-hydrant',[1408.0,-3750.0,1.6],[1400.5,-3741.8,0.45],40],
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
 const frame=(pos,target,fov,shown)=>page.evaluate(({pos,target,fov,shown})=>{const a=__chicago4d;
  const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
  a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
  if(a.streetFurniture)a.streetFurniture.group.visible=shown;
  a.camera.fov=fov;a.camera.updateProjectionMatrix();
  a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
  a.streetTrees?.update?.(0,a.camera);a.streetTrees?.settle?.();a.streetFurniture?.settle?.(a.camera);a.contextCity?.update?.(a.camera);
  a.renderer.info.reset();a.renderer.render(a.scene3d,a.camera);
  const sf=a.streetFurniture?.stats??{};
  return {info:{triangles:a.renderer.info.render.triangles,calls:a.renderer.info.render.calls},furniture:{near:sf.near,far:sf.far,hydrants:sf.hydrantsDrawn,triangles:sf.triangles,drawCalls:sf.drawCalls,detail:sf.detail},problems:a.problems.slice(-3)};
 },{pos,target,fov,shown});
 const stands=[];
 for(const [name,pos,target,fov] of RUN){
  const row={name};
  for(const [tag,shown] of [['before',false],['after',true]]){
   await frame(pos,target,fov,shown);const o=await frame(pos,target,fov,shown);
   await page.screenshot({path:path.join(out,`${tag}-${label}-${name}.jpg`),type:'jpeg',quality:85,timeout:400000});
   row[tag]=o;console.log(label,name,tag,JSON.stringify(o.info),JSON.stringify(o.furniture));
  }
  stands.push(row);
 }
 results.push({label,viewport,detail,js_heap_used_bytes:heap.usedSize,errors,bad,stands});
 console.log(`${label}: heap ${(heap.usedSize/1e6).toFixed(1)} MB errors ${errors.length} bad ${bad.length}`);
 await context.close();
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'readings'+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+'.json'),JSON.stringify({method:'published /1904/ app, animation loop stopped after readiness, each stand rendered with the street-furniture layer hidden (before) and shown (after); heap after a forced GC',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
