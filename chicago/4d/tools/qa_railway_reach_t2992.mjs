// T-2992: the phone's `light` tier was over its 1,270,000-triangle ceiling from the air over the
// district (tools/qa_draft_t2982.mjs's `air` stand, 1,323,370 on dev 7a4c01da4): the railway's far
// rails drew to the far end of the yard at every tier though railway.js's header says a zone past
// the tie reach draws only its ground, and the lake-edge cap, one mesh three kilometres long, drew
// into the sun's pass from anywhere. This reads the actual published /1904/ app at 390x780 `light`
// and renders each stand's held frame twice in the same task: once with the far rails shown
// wherever the near section is not, as dev drew them, and once as shipped. It reports both
// triangle counts and every pixel that differs between the two frames, with a positive control
// (every rail hidden) so "few pixels changed" is a reading the comparison could have failed. It
// fails on a page error, a failed request, a stand over light's ceiling as shipped, a control that
// changes nothing where rails are in view, or a shipped frame that draws more than dev's.
//   node tools/qa_railway_reach_t2992.mjs            (after tools/publish.sh)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/railway-reach-2992');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target, rails in view]: east, north, metres above the ground there. The air is
// tools/qa_draft_t2982.mjs's; the other three stand on and beside the yard (data/railway/1904.json
// runs its tracks from about 1416,-2900 to 1742,-3800), where the rails are what the frame is of.
const STANDS=[
 ['air',[1360,-3620,110],[1300,-3480,0],false],
 ['yard-looking-north',[1566,-3350,1.7],[1430,-2900,1.7],true],
 ['yard-looking-south',[1500,-3020,1.7],[1700,-3800,1.7],true],
 // from Prairie the houses stand between the eye and the yard: no rail in view, so no control
 ['prairie-east-to-yard',[1400,-3300,1.7],[1650,-3300,2],false],
];
const viewport={width:390,height:780};
const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:true,hasTouch:true});
const page=await context.newPage();page.setDefaultTimeout(240000);
const errors=[],bad=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status())});
let row=null;
try{
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail('light');a.step();
   return {scene:a.scene?.id,detail:a.detail,ceiling:a.detailLevels.light.triangles};});
 if(boot.scene!=='1904'||boot.detail!=='light')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 for(const [name,pos,target,railsInView] of STANDS){
  const o=await page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // The held frame, rendered twice (the shadow box settles on the first) and read back inside
   // the same task, before the browser can present and clear the buffer. a.step() above ran the
   // railway's own update for this eye; nothing below calls it again, so the shipped visibility
   // holds until it is overridden by hand.
   const frame=()=>{for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);}
     const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);return {stats:a.stats(),px};};
   const G=a.railway.group;
   const far=G.children.filter(m=>/^railway-rails-far-z\d+$/.test(m.name));
   const near=(m)=>G.getObjectByName(m.name.replace('-far',''));
   const shippedVis=far.map(m=>m.visible);
   const shipped=frame();
   // dev's rule: the far strips wherever the zone's near section is not drawn
   far.forEach(m=>{m.visible=!near(m)?.visible;});
   const dev=frame();
   const farDev=far.filter(m=>m.visible).length;
   // the positive control: no rail at all, near or far
   const railMeshes=G.children.filter(m=>/^railway-rails-/.test(m.name));const railWas=railMeshes.map(m=>m.visible);
   railMeshes.forEach(m=>{m.visible=false;});const none=frame();railMeshes.forEach((m,i)=>{m.visible=railWas[i];});
   far.forEach((m,i)=>{m.visible=shippedVis[i];});
   const diff=(A,B)=>{let n=0,max=0;for(let i=0;i<A.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(A[i+c]-B[i+c]));if(d){n++;max=Math.max(max,d);}}return {n,max};};
   const d=diff(dev.px,shipped.px),c=diff(dev.px,none.px);
   return {dev:{triangles:dev.stats.triangles,drawCalls:dev.stats.drawCalls,farRailZonesDrawn:farDev},
     shipped:{triangles:shipped.stats.triangles,drawCalls:shipped.stats.drawCalls,withinBudget:shipped.stats.withinBudget,farRailZonesDrawn:shippedVis.filter(Boolean).length},
     pixels:w*h,pixelsDiffering:d.n,maxChannelDelta:d.max,controlPixelsDifferingWithNoRails:c.n,problems:a.problems.length};
  },{pos,target});
  await page.screenshot({path:path.join(out,`after-mobile-${name}.jpg`),type:'jpeg',quality:82});
  stands.push({name,railsInView,...o});
  console.log(`${name}: ${o.dev.triangles} -> ${o.shipped.triangles} triangles (ceiling ${boot.ceiling}), far-rail zones ${o.dev.farRailZonesDrawn} -> ${o.shipped.farRailZonesDrawn}, ${o.pixelsDiffering} of ${o.pixels} pixels differ, max ${o.maxChannelDelta} (control without rails: ${o.controlPixelsDifferingWithNoRails})`);
 }
 row={viewport,detail:'light',boot,errors,bad,stands};
}finally{
 fs.writeFileSync(path.join(out,'browser-validation-mobile.json'),JSON.stringify({method:'Actual published /1904/ app at 390x780, `light`; animation paused after readiness; each stand renders the same held frame with the far rails as shipped and as dev drew them (shown wherever the zone\'s near section is not), and once with no rails at all as the control; triangles from renderer.info and every pixel with gl.readPixels in the same task. Software GL on this machine.',result:row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
for(const s of row?.stands??[]){
 if(!s.shipped.withinBudget)fail.push(`${s.name}: ${s.shipped.triangles} is over light's ceiling ${row.boot.ceiling}`);
 if(s.railsInView&&!s.controlPixelsDifferingWithNoRails)fail.push(`${s.name}: the control (no rails at all) changed no pixel, so the comparison cannot see rails`);
 if(s.shipped.triangles>s.dev.triangles)fail.push(`${s.name}: the shipped frame draws more than dev's`);
}
if(!row)fail.push('no reading');
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
