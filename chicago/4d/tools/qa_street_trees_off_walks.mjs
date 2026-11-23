// The 1904 parkway trees off the walks (owner, 2026-11-23: "i am not sure that tree would be in the
// middle of the sidewalk", the Pullman corner at 18th and Prairie). Renders each stand in the
// published /1904/ app at 1280x800 full and 390x780 light, wind held, trees settled.
//   node tools/qa_street_trees_off_walks.mjs                    (after tools/publish.sh)
//   QA_TAG=before QA_OUT=/some/dir QA_VIEWPORT=desktop node tools/qa_street_trees_off_walks.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=await import('/opt/node-tools/node_modules/playwright/index.mjs'));}
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/street-trees-off-walks'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm','.webp':'image/webp'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));
 try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye (east, north, height above ground), target]
const STANDS=process.env.QA_STANDS_JSON?JSON.parse(process.env.QA_STANDS_JSON):[
 // the owner's stand: in Prairie's roadway by the corner's ramp, looking north up the east walk
 ['pullman-corner-north',[1405.2,-3202.6,1.7],[1409.5,-3150,4]],
 ['pullman-corner-from-west',[1398,-3199,1.7],[1412,-3197,2]],
 ['pullman-corner-above',[1402,-3206,9],[1409,-3197,0]],
 // where 16th Street ends at Prairie: the east parkway's first tree
 ['prairie-16th-east',[1400,-2958,1.7],[1406,-2940,3]],
];
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT&&process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(400000);
 const errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:400000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:400000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const frame=(pos,target)=>page.evaluate(({pos,target})=>{const a=__chicago4d;
  const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
  a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
  a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
  a.streetTrees?.update?.(0,a.camera);a.streetTrees?.settle?.();a.contextCity?.update?.(a.camera);a.renderer.render(a.scene3d,a.camera);
  return {problems:a.problems.slice(-5)};
 },{pos,target});
 const stands=[];
 for(const [name,pos,target] of STANDS){
  await frame(pos,target);const o=await frame(pos,target);
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:85,timeout:400000});
  stands.push({name,...o});console.log(TAG,label,name);
 }
 results.push({label,errors,stands});
 console.log(`${TAG} ${label}: errors ${errors.length}`,errors.slice(0,3));
 await context.close();
}
}catch(e){failed=e;}
finally{await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
