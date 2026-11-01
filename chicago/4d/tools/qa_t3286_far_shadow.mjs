// T-3286: far structure pieces cast their shadow from a clustered twin (renderers/web/js/far-shadow.js):
// the triangles it saves and how many pixels it moves. The actual published /1904/ app at full: each
// stand renders the same held frame with the twins off and on and reads every pixel back with
// gl.readPixels; as a positive control it renders the frame with no structure casting at all, which
// has to change the frame wherever a structure's shadow is on screen (or "few pixels changed" could
// not see the shadows). T-3272/T-3285's stands, verbatim (eye and target in scene-local metres, or
// relative to Glessner's centre).
//   node tools/qa_t3286_far_shadow.mjs                  (after tools/publish.sh)
//   QA_ONLY=glessner-prairie-far-se QA_VIEWPORT=390x780 QA_TAG=x node tools/qa_t3286_far_shadow.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/far-shadow-3286');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target, relative-to-Glessner] — east, north, metres above the ground
const ONLY=process.env.QA_ONLY?process.env.QA_ONLY.split(','):null;
const STANDS=[
 ['alley-from-north',[1331.2,-2992,1.7],[1334,-3015,4],false],
 ['glessner-18th-far-west',[-150,32,1.7],[0,0,7],true],
 ['glessner-prairie-far-se',[60,-120,1.7],[0,0,7],true],
 ['glessner-prairie-front',[40,0,1.7],[0,0,7],true],
 ['glessner-prairie-se',[38,-30,1.7],[0,0,7],true],
 ['glessner-roof-close',[12,18,16],[0,0,14],true],
].filter(([name])=>!ONLY||ONLY.includes(name));
const [vw,vh]=(process.env.QA_VIEWPORT||'1280x800').split('x').map(Number),mobile=vw<600;
const viewport={width:vw,height:vh},tag=mobile?'mobile':'desktop';
const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});
const page=await context.newPage();page.setDefaultTimeout(240000);
const errors=[],bad=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status())});
let row=null;
try{
 const t0=Date.now();
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 const readyMs=Date.now()-t0;
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail('full');a.step();
   const fs=a.buildings.farShadow;
   return {scene:a.scene?.id,detail:a.detail,budget:a.stats().budget,build:a.version??null,twins:fs.pieces,twinTriangles:fs.twinTriangles,twinVertices:fs.twinVertices,buildMs:Math.round(fs.buildMs)};});
 boot.readyMs=readyMs;
 if(boot.scene!=='1904'||boot.detail!=='full')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 row={viewport,detail:'full',boot,errors,bad,stands};
 console.log(`boot: ${boot.twins} shadow twins, ${boot.twinTriangles} triangles / ${boot.twinVertices} vertices added, cut in ${boot.buildMs} ms, ready in ${readyMs} ms`);
 for(const [name,pos,target,rel] of STANDS){
  const o=await page.evaluate(({pos,target,rel,MAXPX})=>{const a=__chicago4d;
   if(rel){const c=a.structurePosition('glessner_house');pos=[c.e+pos[0],c.n+pos[1],pos[2]];target=[c.e+target[0],c.n+target[1],target[2]];}
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // Render the held frame twice (the shadow box settles on the first), then read it back
   // inside the same task, before the browser can present and clear the buffer.
   const frame=()=>{let tris=0;for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);tris=a.renderer.info.render.triangles;}
     const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);return {triangles:tris,stats:a.stats(),px};};
   const diff=(x,y)=>{let differ=0,over8=0,maxDelta=0;const at=[];for(let i=0;i<x.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(x[i+c]-y[i+c]));if(d){differ++;if(d>8)over8++;maxDelta=Math.max(maxDelta,d);if(at.length<24)at.push([(i/4)%w,h-1-Math.floor(i/4/w),d]);}}return {differ,over8,maxDelta,at};};
   const fs=a.buildings.farShadow,before=fs.on;if(MAXPX!=null)fs.maxPixels=MAXPX;
   fs.on=false;const off=frame(),off2=frame();
   fs.on=true;const on=frame();const swapped=fs.swapped,saved=fs.saved;
   // The positive control: no structure casts at all.
   const bs=a.buildings.batches;for(const b of bs)b.castShadow=false;const noCast=frame();for(const b of bs)b.castShadow=true;
   fs.on=before;frame();
   const d=diff(off.px,on.px),r=diff(off.px,off2.px),c=diff(off.px,noCast.px);
   return {tierHasItOn:before,pieces:fs.pieces,swapped,saved,
     off:{triangles:off.triangles,drawCalls:off.stats.drawCalls},
     on:{triangles:on.triangles,drawCalls:on.stats.drawCalls,withinBudget:on.triangles<=on.stats.budget.triangles&&on.stats.drawCalls<=on.stats.budget.drawCalls,
       farBudget:on.stats.farBudget,withinFarBudget:on.stats.farBudget?on.triangles<=on.stats.farBudget.triangles&&on.stats.drawCalls<=on.stats.farBudget.drawCalls:null},
     pixels:w*h,pixelsDiffering:d.differ,pixelsDifferingOver8:d.over8,maxChannelDelta:d.maxDelta,differingAt:d.at,
     controlOffOffPixelsDiffering:r.differ,controlPixelsDifferingWithNoStructureCasting:c.differ,problems:a.problems.length};
  },{pos,target,rel,MAXPX:process.env.QA_MAX_PIXELS?Number(process.env.QA_MAX_PIXELS):null});
  if(process.env.QA_SHOTS)await page.screenshot({path:path.join(out,`${tag}-${name}.jpg`),type:'jpeg',quality:82});
  stands.push({name,...o});
  console.log(`${name}: ${o.off.triangles} -> ${o.on.triangles} triangles (-${o.off.triangles-o.on.triangles}; ${o.swapped} of ${o.pieces} twins cast, -${o.saved} in the sun's pass), draws ${o.off.drawCalls} -> ${o.on.drawCalls}, ${o.pixelsDiffering} of ${o.pixels} pixels differ off/on (${o.pixelsDifferingOver8} by more than 8, max ${o.maxChannelDelta}; off/off ${o.controlOffOffPixelsDiffering}; no structure casting ${o.controlPixelsDifferingWithNoStructureCasting}); budget ${o.on.withinBudget?'within':'over'}, far allowance ${o.on.withinFarBudget===null?'none':o.on.withinFarBudget?'within':'OVER'}`);
 }
}finally{
 fs.writeFileSync(process.env.QA_OUT||path.join(out,`browser-validation-${tag}${process.env.QA_TAG?'-'+process.env.QA_TAG:''}.json`),JSON.stringify({method:`Actual published /1904/ app at ${vw}x${vh}, \`full\`; animation paused after readiness; each stand renders the same held frame with the far shadow twins off (buildings.farShadow.on=false), off again (control), on, and with no structure casting (the positive control); triangles from renderer.info, every pixel with gl.readPixels in the same task as the render.`,...row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
// The twin's own bound is a shadow edge moving at most a pixel; the frame is held to 1 pixel
// in 1,000 changed at all, and 1 in 10,000 changed by more than 8 levels of 255.
const PIXEL_BOUND=1e-3,STRONG_BOUND=1e-4;
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
if(!(row?.boot?.twins>0))fail.push('no shadow twins were built');
for(const s of row?.stands??[]){
 if(!s.tierHasItOn)fail.push(`${s.name}: the twins were not on`);
 if(s.on.triangles>s.off.triangles)fail.push(`${s.name}: the twins added triangles`);
 // a swapped piece can split a coalesced run in the sun's pass: at most one draw per twin cast
 if(s.on.drawCalls-s.off.drawCalls>s.swapped)fail.push(`${s.name}: the twins added ${s.on.drawCalls-s.off.drawCalls} draws for ${s.swapped} twins`);
 if(s.controlOffOffPixelsDiffering)fail.push(`${s.name}: the held frame is not repeatable (${s.controlOffOffPixelsDiffering} pixels off/off)`);
 if(s.pixelsDiffering>s.pixels*PIXEL_BOUND)fail.push(`${s.name}: the twins changed ${s.pixelsDiffering} pixels, over ${s.pixels*PIXEL_BOUND}`);
 if(s.pixelsDifferingOver8>s.pixels*STRONG_BOUND)fail.push(`${s.name}: the twins changed ${s.pixelsDifferingOver8} pixels by more than 8, over ${s.pixels*STRONG_BOUND}`);
 if(s.on.withinFarBudget===false)fail.push(`${s.name}: ${s.on.triangles} triangles / ${s.on.drawCalls} draws over the far-view allowance ${JSON.stringify(s.on.farBudget)}`);
}
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
