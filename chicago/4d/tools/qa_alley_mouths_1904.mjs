// The 1904 alley mouths (owner, 2026-11-26: "Correct alleyway grading and remove inappropriate curbs
// at alley entrances"). Renders each stand in the
// published /1904/ app at 1280x800 full and 390x780 light, wind held, trees settled.
//   node tools/qa_alley_mouths_1904.mjs                    (after tools/publish.sh)
//   QA_TAG=before QA_OUT=/some/dir QA_VIEWPORT=desktop node tools/qa_alley_mouths_1904.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=await import('/opt/node-tools/node_modules/playwright/index.mjs'));}
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/alley-mouths-1904'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm','.webp':'image/webp'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));
 try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye (east, north, height above ground), target]
const STANDS=process.env.QA_STANDS_JSON?JSON.parse(process.env.QA_STANDS_JSON):[
 // 18th Street between Indiana and Prairie, looking south into the west alley's mouth
 ['18th-west-alley-from-street',[1336,-3207,1.7],[1336,-3235,0.5]],
 // the same mouth from the alley, looking north out to 18th and the alley across it
 ['18th-west-alley-from-alley',[1334.5,-3232,1.7],[1333.5,-3200,0.5]],
 // walking the east walk of 18th past the mouth
 ['18th-west-alley-along-walk',[1325,-3217.2,1.6],[1350,-3217.2,0.1]],
 ['18th-west-alley-above',[1326,-3200,10],[1335,-3220,0]],
 // 20th Street, the east alley's mouth (Prairie to Calumet)
 ['20th-east-alley-from-street',[1472,-3471,1.7],[1472,-3445,0.5]],
 ['21st-east-alley-from-street',[1473,-3606,1.7],[1473,-3580,0.5]],
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
