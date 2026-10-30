// T-3146: Glessner's own close stands were over Full's 4.6 M triangle budget (found by T-3012):
// on Prairie 38 m east and 30 m south of the house's centre looking at it, and on 18th 45 m west
// and 32 m north. The house itself is about 1.42 M in each pass there, and the sun's pass also
// carried every house beside and behind the camera whose shadow falls away from the screen.
// Full now runs the conservative sun-pass test Light has carried since T-2529
// (shadow-casters.js). This reads the actual published /1904/ app at 1280x800 `full` (or
// QA_VIEWPORT=390x780), at stands round Glessner given as offsets in metres from its footprint's
// centre plus T-3008's Calumet east walk, with the test OFF and then ON for the same held frame:
// the triangles each way, the pieces left out, and every pixel of the two frames compared. A
// positive control (the sun casting nothing) must change the frame, so "no pixel changed" can see
// shadows. It fails on a page error, a stand over the budget with the test on, or a changed pixel.
//   node tools/qa_t3146_glessner_close.mjs            (after tools/publish.sh)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/glessner-close-budget-3146');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target, relative-to-Glessner] — east, north, metres above the ground
const ONLY=process.env.QA_ONLY?process.env.QA_ONLY.split(','):null;
const STANDS=[
 ['glessner-prairie-se',[38,-30,1.7],[0,0,7],true],
 ['glessner-18th-nw',[-45,32,1.7],[0,0,7],true],
 ['glessner-prairie-ne',[38,30,1.7],[0,0,7],true],
 ['glessner-prairie-front',[40,0,1.7],[0,0,7],true],
 ['glessner-18th-ne',[20,35,1.7],[0,0,7],true],
 ['glessner-elevated-ne',[45,45,30],[0,0,5],true],
 ['calumet-east-walk',[1539,-3470,1.7],[1505,-3360,7],false],
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
   const diff=(x,y)=>{let differ=0,maxDelta=0;for(let i=0;i<x.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(x[i+c]-y[i+c]));if(d){differ++;maxDelta=Math.max(maxDelta,d);}}return {differ,maxDelta};};
   const before=a.setCastersTowardView();a.setCastersTowardView(false);const off=frame(),off2=CONTROL?frame():off;
   const on0=a.setCastersTowardView(true).culled;const on=frame();const culled=a.setCastersTowardView(true).culled-on0;
   // The positive control: with the sun casting nothing at all, the frame has to change.
   const sunLight=a.world.light;sunLight.castShadow=false;const dark=frame();sunLight.castShadow=true;
   a.setCastersTowardView(before.on);frame();
   const d=diff(off.px,on.px),c=diff(off.px,dark.px),r=diff(off.px,off2.px);
   return {tierHasItOn:before.on,off:{triangles:off.triangles,drawCalls:off.stats.drawCalls},on:{triangles:on.triangles,drawCalls:on.stats.drawCalls,withinBudget:on.triangles<=on.stats.budget.triangles},
     piecesLeftOutOfSunPass:culled/2,pixels:w*h,pixelsDiffering:d.differ,maxChannelDelta:d.maxDelta,
     controlOffOffPixelsDiffering:CONTROL?r.differ:null,controlPixelsDifferingWithNoShadows:c.differ,problems:a.problems.length};
  },{pos,target,rel,CONTROL:!!process.env.QA_CONTROL});
  if(process.env.QA_SHOTS)await page.screenshot({path:path.join(out,`after-${tag}-${name}.jpg`),type:'jpeg',quality:82});
  stands.push({name,...o});
  console.log(`${name}: ${o.off.triangles} -> ${o.on.triangles} triangles (budget ${boot.budget.triangles}), ${o.piecesLeftOutOfSunPass} pieces out of the sun's pass, ${o.pixelsDiffering} of ${o.pixels} pixels differ (off/off control ${o.controlOffOffPixelsDiffering}; without shadows ${o.controlPixelsDifferingWithNoShadows})`);
 }
}finally{
 fs.writeFileSync(process.env.QA_OUT||path.join(out,`browser-validation-${tag}.json`),JSON.stringify({method:`Actual published /1904/ app at ${vw}x${vh}, \`full\`; animation paused after readiness; each stand renders the same held frame with the sun-pass test off (setCastersTowardView(false)), off again (the control) and on, reads triangles from renderer.info and every pixel with gl.readPixels in the same task. glessner-* stands are offsets in metres from Glessner's footprint centre. Software GL on this machine.`,result:row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
for(const s of row?.stands??[]){
 if(!process.env.QA_BEFORE&&!s.tierHasItOn)fail.push(`${s.name}: full did not switch the test on`);
 if(!s.on.withinBudget)fail.push(`${s.name}: ${s.on.triangles} is over full's budget ${row.boot.budget.triangles}`);
 if(!s.controlPixelsDifferingWithNoShadows)fail.push(`${s.name}: the control (no shadows at all) changed no pixel, so the comparison cannot see shadows`);
 if(s.pixelsDiffering)fail.push(`${s.name}: ${s.pixelsDiffering} pixels changed (max ${s.maxChannelDelta})`);
 if(s.on.triangles>s.off.triangles)fail.push(`${s.name}: the test added triangles`);
}
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
