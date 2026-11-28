// T-3738: the 1871 house numbers on the DeKoven Street fronts. Renders each stand in the published
// /1871/ app at 1280x800 full and 390x780 light, once with the numbers hidden ("before") and once
// shown ("after"), and reports the layer's census.
//   node tools/qa_house_numbers_1871.mjs                    (after tools/publish.sh)
//   QA_OUT=/some/dir QA_VIEWPORT=desktop node tools/qa_house_numbers_1871.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=await import('/opt/node-tools/node_modules/playwright/index.mjs'));}
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/house-numbers-1871');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.ktx2':'image/ktx2','.wasm':'application/wasm','.webp':'image/webp'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));
 try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye (east, north, height above ground), target]: the O'Leary door is at about (-320.7, -1954.6)
const STANDS=[
 ['oleary-door',[-320.2,-1957.6,1.6],[-320.7,-1954.6,2.3]],
 ['dekoven-north-side',[-314,-1963.5,1.7],[-318,-1954.5,2.0]],
 ['sullivan-door',[-309,-1971.5,1.6],[-308.9,-1974.6,2.3]],
];
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT&&process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(400000);
 const errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1871/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:400000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:400000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const census=await page.evaluate(()=>{const c=__chicago4d.houseNumbers?.census;return c?{numbers:c.numbers,placed:c.placed,unplaced:c.unplaced,draws:c.draws,triangles:c.triangles,hands:c.hands}:null;});
 const frame=(pos,target,show)=>page.evaluate(({pos,target,show})=>{const a=__chicago4d;
  if(a.houseNumbers?.group)a.houseNumbers.group.visible=show;
  const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
  a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
  a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world?.follow?.(a.camera.position);a.world?.aim?.(a.camera);
  a.streetTrees?.update?.(0,a.camera);a.streetTrees?.settle?.();a.contextCity?.update?.(a.camera);a.renderer.render(a.scene3d,a.camera);
  return {problems:a.problems.slice(-5)};
 },{pos,target,show});
 const stands=[];
 for(const [name,pos,target] of STANDS){
  for(const [tag,show] of [['before',false],['after',true]]){
   await frame(pos,target,show);const o=await frame(pos,target,show);
   await page.screenshot({path:path.join(out,`${tag}-${label}-${name}.jpg`),type:'jpeg',quality:85,timeout:400000});
   stands.push({name,tag,...o});console.log(tag,label,name);
  }
 }
 results.push({label,errors,census,stands});
 console.log(`${label}: errors ${errors.length}`,errors.slice(0,3),'census',JSON.stringify(census));
 await context.close();
}
}catch(e){failed=e;}
finally{await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(results,null,1)+'\n');
const bad=results.filter(r=>r.errors.length||!r.census||r.census.placed!==r.census.numbers||!r.census.numbers);
console.log(bad.length?'QA FAIL':'QA PASS');process.exit(bad.length?1:0);
