// T-3249: at `light` the sun's pass draws each heavy structure piece from its clustered shadow
// twin (renderers/web/js/far-shadow.js) wherever the twin's edge moves no more than one texel of
// the light tier's 23.4 cm map — near pieces as well as far. The actual published /1904/ app at
// `light`, at T-3247's four phone stands: each held frame is rendered with every piece casting
// whole (the full models), with T-3286's screen bound alone (dev before this change), with the
// texel bound (this change), and with no structure casting at all (the positive control, and the
// subtrahend that isolates the structures' share of the sun's pass). Triangles from
// renderer.info, every pixel with gl.readPixels in the same task as the render.
//   node tools/qa_t3249_sun_twins.mjs                       (after tools/publish.sh)
//   QA_VIEWPORT=1280x800 QA_SHOTS=1 node tools/qa_t3249_sun_twins.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/sun-twins-3249');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// T-3247's stands: [name, eye, target], east/north metres from Prairie Avenue's line in front
// of 1801 Prairie (half-way between Glessner's and Kimball's centres, at Kimball's northing),
// and metres above the ground.
const ONLY=process.env.QA_ONLY?process.env.QA_ONLY.split(','):null;
const STANDS=[
 ['south-from-1801',[0,0,1.7],[0,-150,1.7]],
 ['prairie-and-18th',[0,28,1.7],[-30,-25,6]],
 ['lakeside-south',[180,0,1.7],[180,-150,1.7]],
 ['air-over-indiana',[-120,0,120],[-120,-450,0]],
].filter(([name])=>!ONLY||ONLY.includes(name));
const [vw,vh]=(process.env.QA_VIEWPORT||'390x780').split('x').map(Number),mobile=vw<600;
const viewport={width:vw,height:vh},tag=mobile?'mobile':'desktop';
const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});
const page=await context.newPage();page.setDefaultTimeout(300000);
const errors=[],bad=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status())});
let row=null;
try{
 const t0=Date.now();
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:300000,polling:500});
 const readyMs=Date.now()-t0;
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:300000,polling:1000});
 const boot=await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail('light');a.step();
   const fs=a.buildings.farShadow;
   return {scene:a.scene?.id,detail:a.detail,budget:a.stats().budget,texelM:fs.texelM,twins:fs.pieces,groups:fs.groups,groupTriangles:fs.groupTriangles,groupIndices:fs.groupIndices,groupMs:Math.round(fs.groupMs),twinTriangles:fs.twinTriangles,twinVertices:fs.twinVertices,buildMs:Math.round(fs.buildMs)};});
 boot.readyMs=readyMs;
 if(boot.scene!=='1904'||boot.detail!=='light')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 row={viewport,detail:'light',boot,errors,bad,stands};
 console.log(`boot: texel ${boot.texelM} m; ${boot.groups} group twins (${boot.groupTriangles} triangles, ${boot.groupIndices} index entries, cut in ${boot.groupMs} ms), ${boot.twins} piece twins, ${boot.twinTriangles} triangles / ${boot.twinVertices} vertices, cut in ${boot.buildMs} ms, ready in ${readyMs} ms`);
 for(const [name,pos,target] of STANDS){
  const o=await page.evaluate(({pos,target,SHOTS})=>{const a=__chicago4d;
   const g=a.structurePosition('glessner_house'),k=a.structurePosition('kimball_house_1801_prairie');
   const P={e:(g.e+k.e)/2,n:k.n};
   pos=[P.e+pos[0],P.n+pos[1],pos[2]];target=[P.e+target[0],P.n+target[1],target[2]];
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // Render the held frame twice (the shadow box settles on the first), then read it back
   // inside the same task, before the browser can present and clear the buffer.
   const frame=()=>{let tris=0,calls=0;for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);tris=a.renderer.info.render.triangles;calls=a.renderer.info.render.calls;}
     const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);return {triangles:tris,calls,stats:a.stats(),px};};
   const diff=(x,y)=>{let differ=0,over8=0,maxDelta=0;const at=[];for(let i=0;i<x.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(x[i+c]-y[i+c]));if(d){differ++;if(d>8)over8++;maxDelta=Math.max(maxDelta,d);if(at.length<24)at.push([(i/4)%w,h-1-Math.floor(i/4/w),d]);}}return {differ,over8,maxDelta,at};};
   // a picture of a read-back frame (bottom-up rows) as a JPEG data URL; `mark` paints the
   // pixels that differ from it in magenta
   const picture=(px,mark)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d'),img=x.createImageData(w,h);
     for(let r=0;r<h;r++)for(let q=0;q<w;q++){const i=((h-1-r)*w+q)*4,j=(r*w+q)*4;let R=px[i],G=px[i+1],B=px[i+2];
       if(mark){const d=Math.max(Math.abs(px[i]-mark[i]),Math.abs(px[i+1]-mark[i+1]),Math.abs(px[i+2]-mark[i+2]));if(d){R=255;G=0;B=255;}}
       img.data[j]=R;img.data[j+1]=G;img.data[j+2]=B;img.data[j+3]=255;}
     x.putImageData(img,0,0);return c.toDataURL('image/jpeg',0.85);};
   const fs=a.buildings.farShadow,wasOn=fs.on,wasTexel=fs.byTexel;
   const bs=a.buildings.batches;
   fs.on=false;const whole=frame(),whole2=frame();
   fs.on=true;fs.byTexel=false;const screen=frame();const screenSwapped=fs.swapped;
   fs.byTexel=true;const texel=frame();const swapped=fs.swapped,saved=fs.saved,groupsSwapped=fs.groupsSwapped,swapMs=fs.swapMs;
   // the positive control, and the frame without the structures' share of the sun's pass
   for(const b of bs)b.castShadow=false;const noCast=frame();for(const b of bs)b.castShadow=true;
   fs.on=wasOn;fs.byTexel=wasTexel;frame();
   const sun=(f)=>f.triangles-noCast.triangles;
   const dW=diff(whole.px,texel.px),dS=diff(screen.px,texel.px),r=diff(whole.px,whole2.px),c=diff(whole.px,noCast.px),dWS=diff(whole.px,screen.px);
   return {pieces:fs.pieces,groups:fs.groups,groupsSwapped,swapMs,screenSwapped,swapped,saved,
     frame:{whole:whole.triangles,screen:screen.triangles,texel:texel.triangles,noStructureCasting:noCast.triangles},
     structureSunPass:{whole:sun(whole),screen:sun(screen),texel:sun(texel)},
     calls:{whole:whole.calls,screen:screen.calls,texel:texel.calls},
     withinBudget:texel.triangles<=texel.stats.budget.triangles&&texel.stats.drawCalls<=texel.stats.budget.drawCalls,
     pixels:w*h,
     wholeVsTexel:{differ:dW.differ,over8:dW.over8,maxDelta:dW.maxDelta,at:dW.at},
     wholeVsScreen:{differ:dWS.differ,over8:dWS.over8,maxDelta:dWS.maxDelta},
     screenVsTexel:{differ:dS.differ,over8:dS.over8,maxDelta:dS.maxDelta},
     controlWholeWholePixelsDiffering:r.differ,controlPixelsDifferingWithNoStructureCasting:c.differ,problems:a.problems.length,
     shots:SHOTS?{whole:picture(whole.px),texel:picture(texel.px),marked:picture(texel.px,whole.px)}:null};
  },{pos,target,SHOTS:!!process.env.QA_SHOTS});
  if(o.shots){for(const [k,v] of Object.entries(o.shots))fs.writeFileSync(path.join(out,`${tag}-${name}-${k}.jpg`),Buffer.from(v.split(',')[1],'base64'));delete o.shots;}
  stands.push({name,...o});
  const pct=(a,b)=>a>0?((1-b/a)*100).toFixed(1):'0.0';
  console.log(`${name}: structures in the sun's pass ${o.structureSunPass.whole} whole, ${o.structureSunPass.screen} screen bound (dev), ${o.structureSunPass.texel} texel bound (-${pct(o.structureSunPass.screen,o.structureSunPass.texel)}% on dev, -${pct(o.structureSunPass.whole,o.structureSunPass.texel)}% on whole); ${o.groupsSwapped} of ${o.groups} group twins cast, ${o.swapped-o.groupsSwapped} piece twins (${o.screenSwapped} by the screen bound alone), hooks ${o.swapMs.toFixed(1)} ms; frame ${o.frame.screen} -> ${o.frame.texel}, calls ${o.calls.screen} -> ${o.calls.texel}; pixels whole/texel ${o.wholeVsTexel.differ} of ${o.pixels} (${o.wholeVsTexel.over8} over 8, max ${o.wholeVsTexel.maxDelta}), whole/screen ${o.wholeVsScreen.differ}, screen/texel ${o.screenVsTexel.differ}; whole/whole ${o.controlWholeWholePixelsDiffering}; no structure casting ${o.controlPixelsDifferingWithNoStructureCasting}; budget ${o.withinBudget?'within':'OVER'}`);
 }
}finally{
 fs.writeFileSync(process.env.QA_OUT||path.join(out,`browser-validation-${tag}${process.env.QA_TAG?'-'+process.env.QA_TAG:''}.json`),JSON.stringify({method:`Actual published /1904/ app at ${vw}x${vh}, \`light\`; animation paused after readiness; each stand renders the same held frame with every structure piece casting whole (buildings.farShadow.on=false), whole again (control), with T-3286's screen bound alone (byTexel=false: dev before T-3249), with the texel bound (T-3249), and with no structure casting (the positive control; subtracted from each to give the structures' share of the sun's pass). Triangles from renderer.info, every pixel with gl.readPixels in the same task as the render.`,...row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
// The twin's own bound is a shadow edge moving at most one texel of the map. The frame is held to
// 1 pixel in 100 changed at all against the full models, and 1 in 1,000 by more than 8 levels.
const PIXEL_BOUND=1e-2,STRONG_BOUND=1e-3;
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
if(!(row?.boot?.texelM>0))fail.push('the light tier carries no texel bound');
if(!(row?.boot?.twins>0))fail.push('no shadow twins were built');
for(const s of row?.stands??[]){
 if(s.controlWholeWholePixelsDiffering)fail.push(`${s.name}: the held frame is not repeatable (${s.controlWholeWholePixelsDiffering} pixels whole/whole)`);
 // A stand where no structure casts toward the view (the lakeside: the railway's, T-3247) has nothing
 // to swap; it is reported, and it must stay exactly so.
 if(!s.controlPixelsDifferingWithNoStructureCasting&&s.structureSunPass.whole>0)fail.push(`${s.name}: structures cast but no structure shadow is on screen, so the pixel test sees nothing`);
 if(s.structureSunPass.texel>s.structureSunPass.screen)fail.push(`${s.name}: the texel bound added sun-pass triangles`);
 if(s.wholeVsTexel.differ>s.pixels*PIXEL_BOUND)fail.push(`${s.name}: the twins changed ${s.wholeVsTexel.differ} pixels against the full models, over ${s.pixels*PIXEL_BOUND}`);
 if(s.wholeVsTexel.over8>s.pixels*STRONG_BOUND)fail.push(`${s.name}: the twins changed ${s.wholeVsTexel.over8} pixels by more than 8, over ${s.pixels*STRONG_BOUND}`);
}
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
