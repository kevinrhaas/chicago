// T-2529: the phone's `light` tier was over its 1,270,000-triangle ceiling looking down
// Prairie's east row from 1613 to 1621 — every K01 house beside or behind the camera drew
// its whole assembly into the sun's pass, though the sun threw those shadows away from the
// screen. shadow-casters.js now leaves such a piece out of that pass. This reads the actual
// published /1904/ app at 390x780 `light`, at T-2434's five stands round 1619 Prairie, with
// the cull OFF and then ON for the same held frame: the triangles each way, the pieces left
// out, and every pixel of the two frames compared (the cull's claim is that the picture does
// not change). It fails if any stand is over light's ceiling with the cull on, or if any
// pixel differs.
//   node tools/qa_shadow_casters_t2529.mjs            (after tools/publish.sh)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/shadow-casters-2529');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// T-2434's stands round 1619 Prairie: [name, eye, target] — east, north, metres above the ground
const STANDS=[
 ['front',[1394,-3001,1.7],[1413,-3001,8.5]],
 ['oblique-north',[1394,-2979,1.7],[1414,-3001,8]],
 ['oblique-south',[1401,-3017,1.7],[1413,-3002,8]],
 ['rear',[1446,-2994,1.7],[1430,-3003,4]],
 ['roof',[1390,-2972,40],[1421,-3001,8]],
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
   return {scene:a.scene?.id,detail:a.detail,ceiling:a.detailLevels.light.triangles,build:a.version??null};});
 if(boot.scene!=='1904'||boot.detail!=='light')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 for(const [name,pos,target] of STANDS){
  const o=await page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // Render the held frame twice (the shadow box settles on the first), then read it back
   // inside the same task, before the browser can present and clear the buffer.
   const frame=()=>{for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);}
     const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);return {stats:a.stats(),px};};
   const before=a.setCastersTowardView();a.setCastersTowardView(false);const off=frame();
   const on0=a.setCastersTowardView(true).culled;const on=frame();const culled=a.setCastersTowardView(true).culled-on0;
   // The positive control: the same comparison must SEE shadows, or "no pixel changed"
   // proves nothing. With the sun casting nothing at all, the frame has to change.
   const sunLight=a.world.light;sunLight.castShadow=false;const dark=frame();sunLight.castShadow=true;frame();
   let control=0;for(let i=0;i<off.px.length;i+=4)if(off.px[i]!==dark.px[i]||off.px[i+1]!==dark.px[i+1]||off.px[i+2]!==dark.px[i+2])control++;
   let differ=0,maxDelta=0;for(let i=0;i<off.px.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(off.px[i+c]-on.px[i+c]));if(d){differ++;maxDelta=Math.max(maxDelta,d);}}
   return {tierHadItOn:before.on,off:{triangles:off.stats.triangles,drawCalls:off.stats.drawCalls},on:{triangles:on.stats.triangles,drawCalls:on.stats.drawCalls,withinBudget:on.stats.withinBudget},
     piecesLeftOutOfSunPass:culled/2,pixels:w*h,controlPixelsDifferingWithNoShadows:control,pixelsDiffering:differ,maxChannelDelta:maxDelta,problems:a.problems.length};
  },{pos,target});
  await page.screenshot({path:path.join(out,`after-mobile-${name}.jpg`),type:'jpeg',quality:82});
  stands.push({name,...o});
  console.log(`${name}: ${o.off.triangles} -> ${o.on.triangles} triangles (ceiling ${boot.ceiling}), ${o.piecesLeftOutOfSunPass} pieces out of the sun's pass, ${o.pixelsDiffering} of ${o.pixels} pixels differ (control without shadows: ${o.controlPixelsDifferingWithNoShadows})`);
 }
 row={viewport,detail:'light',boot,errors,bad,stands};
}finally{
 fs.writeFileSync(path.join(out,'browser-validation-mobile.json'),JSON.stringify({method:'Actual published /1904/ app at 390x780, `light`; animation paused after readiness; each stand renders the same held frame with the cull off (setCastersTowardView(false)) and on, reads triangles from renderer.info and every pixel with gl.readPixels in the same task. Software GL on this machine.',result:row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
for(const s of row?.stands??[]){
 if(!s.tierHadItOn)fail.push(`${s.name}: light did not switch the cull on`);
 if(!s.on.withinBudget)fail.push(`${s.name}: ${s.on.triangles} is over light's ceiling ${row.boot.ceiling}`);
 if(!s.controlPixelsDifferingWithNoShadows)fail.push(`${s.name}: the control (no shadows at all) changed no pixel, so the comparison cannot see shadows`);
 if(s.pixelsDiffering)fail.push(`${s.name}: ${s.pixelsDiffering} pixels changed (max ${s.maxChannelDelta})`);
 if(s.on.triangles>s.off.triangles)fail.push(`${s.name}: the cull added triangles`);
}
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
