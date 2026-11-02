// T-3272, T-3285: Glessner's relief roof pieces drawn as their crests only past the relief's last visible
// pixel (renderers/web/js/far-roof-relief.js) — the triangles it saves and the proof that no pixel
// moves. The actual published /1904/ app at full: each stand renders the same held frame with the
// swap off and on and reads every pixel back with gl.readPixels; as a positive control it renders
// the frame with the three relief pieces hidden outright, which has to change the frame wherever
// the roof is on screen (or "no pixel changed" could not see the roof). T-3146's harness, verbatim
// in its framing (eye and target in scene-local metres, or relative to Glessner's centre).
//   node tools/qa_t3272_far_relief.mjs                  (after tools/publish.sh)
//   QA_ONLY=alley-from-north QA_VIEWPORT=390x780 QA_TAG=x node tools/qa_t3272_far_relief.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/alley-budget-3272');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target, relative-to-Glessner] — east, north, metres above the ground
const ONLY=process.env.QA_ONLY?process.env.QA_ONLY.split(','):null;
const STANDS=[
 ['alley-from-north',[1331.2,-2992,1.7],[1334,-3015,4],false],
 ['alley-from-south',[1331.2,-3040,1.7],[1334,-3015,4],false],
 ['glessner-18th-far-west',[-150,32,1.7],[0,0,7],true],
 ['glessner-prairie-far-se',[60,-120,1.7],[0,0,7],true],
 ['glessner-prairie-front',[40,0,1.7],[0,0,7],true],
 ['glessner-prairie-se',[38,-30,1.7],[0,0,7],true],
 ['glessner-elevated-ne',[45,45,30],[0,0,5],true],
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
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail('full');a.step();
   return {scene:a.scene?.id,detail:a.detail,budget:a.stats().budget,build:a.version??null};});
 if(boot.scene!=='1904'||boot.detail!=='full')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 // filled as each stand lands, so a run cut short still writes what it read
 row={viewport,detail:'full',boot,errors,bad,stands};
 for(const [name,pos,target,rel] of STANDS){
  const o=await page.evaluate(({pos,target,rel,CONTROL})=>{const a=__chicago4d;
   if(rel){const c=a.structurePosition('glessner_house');pos=[c.e+pos[0],c.n+pos[1],pos[2]];target=[c.e+target[0],c.n+target[1],target[2]];}
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // Render the held frame twice (the shadow box settles on the first), then read it back
   // inside the same task, before the browser can present and clear the buffer.
   const frame=()=>{let tris=0;for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);tris=a.renderer.info.render.triangles;}
     const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);return {triangles:tris,stats:a.stats(),px};};
   const diff=(x,y)=>{let differ=0,maxDelta=0;const at=[];for(let i=0;i<x.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(x[i+c]-y[i+c]));if(d){differ++;maxDelta=Math.max(maxDelta,d);if(at.length<24)at.push([(i/4)%w,h-1-Math.floor(i/4/w),d]);}}return {differ,maxDelta,at};};
   const fr=a.buildings.farRelief,before=fr.on,sunBefore=fr.sun;
   fr.on=false;const off=frame(),off2=CONTROL?frame():off;
   // T-3285: the colour pass swapped and the sun's pass whole (T-3284's state), then both
   fr.on=true;fr.sun=false;const colourOnly=frame();
   fr.sun=true;const on=frame();const swapped=fr.swapped,sunSwapped=fr.sunSwapped;
   // The sun's positive control: the relief batches cast nothing at all, which has to change
   // the frame wherever the roof's shadow is on screen (or "no pixel changed" could not see it).
   const reliefBatches=a.buildings.batches.filter(b=>b.material?.userData?.roofFilter==='course-pixels-v1');
   for(const b of reliefBatches)b.castShadow=false;const noCast=frame();for(const b of reliefBatches)b.castShadow=true;
   // The positive control: the three relief pieces left out outright.
   const pairs=a.buildings.batches.filter(b=>b.material?.userData?.roofFilter==='course-pixels-v1');
   fr.on=false;const hide=[];for(const b of pairs){const info=b._instanceInfo;for(let i=0;i<info.length;i++){if(info[i]?.active!==false&&b.getVisibleAt(i)){hide.push([b,i]);b.setVisibleAt(i,false);}}}
   const gone=frame();for(const [b,i] of hide)b.setVisibleAt(i,true);
   fr.on=before;fr.sun=sunBefore;frame();
   const d=diff(off.px,on.px),dc=diff(off.px,colourOnly.px),c=diff(off.px,gone.px),r=diff(off.px,off2.px),ds=diff(colourOnly.px,on.px),cs=diff(on.px,noCast.px);
   return {tierHasItOn:before,sunHasItOn:sunBefore,pieces:fr.pieces,swapped,sunSwapped,off:{triangles:off.triangles,drawCalls:off.stats.drawCalls},
     colourOnly:{triangles:colourOnly.triangles},on:{triangles:on.triangles,drawCalls:on.stats.drawCalls,withinBudget:on.triangles<=on.stats.budget.triangles&&on.stats.drawCalls<=on.stats.budget.drawCalls,
     farBudget:on.stats.farBudget,withinFarBudget:on.stats.farBudget?on.triangles<=on.stats.farBudget.triangles&&on.stats.drawCalls<=on.stats.farBudget.drawCalls:null},
     colourPixelsDiffering:dc.differ,saved:off.triangles-on.triangles,savedBySun:colourOnly.triangles-on.triangles,pixels:w*h,pixelsDiffering:d.differ,maxChannelDelta:d.maxDelta,
     sunPixelsDiffering:ds.differ,sunMaxChannelDelta:ds.maxDelta,sunDifferingAt:ds.at,controlPixelsDifferingWithReliefCastingNothing:cs.differ,
     controlOffOffPixelsDiffering:CONTROL?r.differ:null,controlPixelsDifferingWithRoofReliefHidden:c.differ,problems:a.problems.length};
  },{pos,target,rel,CONTROL:!!process.env.QA_CONTROL});
  if(process.env.QA_SHOTS)await page.screenshot({path:path.join(out,`after-${tag}-${name}.jpg`),type:'jpeg',quality:82});
  stands.push({name,...o});
  console.log(`${name}: ${o.off.triangles} -> ${o.colourOnly.triangles} (colour pass) -> ${o.on.triangles} triangles (both; -${o.saved}, sun -${o.savedBySun}; budget ${boot.budget.triangles}), ${o.swapped}/${o.sunSwapped} of ${o.pieces} pieces swapped (colour/sun), ${o.pixelsDiffering} of ${o.pixels} pixels differ off/on, ${o.sunPixelsDiffering} colour-only/both (off/off control ${o.controlOffOffPixelsDiffering}; relief hidden ${o.controlPixelsDifferingWithRoofReliefHidden}; relief casting nothing ${o.controlPixelsDifferingWithReliefCastingNothing}), draws ${o.on.drawCalls}; far allowance ${o.on.withinFarBudget===null?'none':o.on.withinFarBudget?'within':'OVER'}`);
 }
}finally{
 fs.writeFileSync(process.env.QA_OUT||path.join(out,`browser-validation-${tag}${process.env.QA_TAG?'-'+process.env.QA_TAG:''}.json`),JSON.stringify({method:`Actual published /1904/ app at ${vw}x${vh}, \`full\`; animation paused after readiness; each stand renders the same held frame with the far-relief swap off (buildings.farRelief.on=false), off again (QA_CONTROL), on in the colour pass only (farRelief.sun=false, T-3284), on in both passes (T-3285), with the relief batches casting nothing (the sun's positive control), and with the three relief pieces hidden outright (the positive control); triangles from renderer.info, every pixel with gl.readPixels in the same task as the render.`,...row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
const SUN_PIXEL_BOUND=1e-4,notes=[];
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
for(const s of row?.stands??[]){
 if(s.on.triangles>s.off.triangles)fail.push(`${s.name}: the swap added triangles`);
 // T-3285: every stand here is held to the far-view allowance Full declares (main.js)
 if(s.on.withinFarBudget===false)fail.push(`${s.name}: ${s.on.triangles} triangles / ${s.on.drawCalls} draws over the far-view allowance ${JSON.stringify(s.on.farBudget)}`);
 // A stand whose roof is off screen (hidden outright changes nothing: T-3284's 'alley from the
 // south' and 'Prairie 60 m E / 120 m S' read 0 too) proves the triangles only, and says so.
 if(!s.controlPixelsDifferingWithRoofReliefHidden){notes.push(`${s.name}: the roof is not on screen (relief hidden changes no pixel): its triangles are read, its pixels prove nothing`);continue;}
 if(!s.tierHasItOn)fail.push(`${s.name}: the swap was not on`);
 if(!s.sunHasItOn)fail.push(`${s.name}: the sun's swap was not on`);
 // T-3285: the sun's swap is an LOD of the shadow map, not a proof: its change is held to
 // SUN_PIXEL_BOUND of the frame (1 in 10,000), and a frame over it fails.
 if(s.sunPixelsDiffering>s.pixels*SUN_PIXEL_BOUND)fail.push(`${s.name}: the sun's swap changed ${s.sunPixelsDiffering} pixels (max ${s.sunMaxChannelDelta}), over ${SUN_PIXEL_BOUND*s.pixels}`);
 // the colour pass's own swap stays a proof (T-3284): off against colour-only reads the same
 if(s.colourPixelsDiffering)fail.push(`${s.name}: the colour pass's swap changed ${s.colourPixelsDiffering} pixels`);
}
if(notes.length)console.log('NOTE\n '+notes.join('\n '));
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
