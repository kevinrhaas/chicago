#!/usr/bin/env node
// T-3331 — Time of day, photographed. Boots a published year (QA_YEAR, default 1812),
// stands at a few places and renders each at the named hours, writing JPEGs and a
// JSON of what took effect. Also proves `daytime` is the shipped frame: the held
// frame at boot and the same frame after night -> daytime must be identical.
//   node tools/qa_time_of_day_t3331.mjs            # phone 390x780
//   QA_DESKTOP=1 node tools/qa_time_of_day_t3331.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,process.env.SMOKE_ROOT||'../../site/4d');
const out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/time-of-day-3331');
fs.mkdirSync(out,{recursive:true});
const YEAR=process.env.QA_YEAR||'1812';
const desktop=!!process.env.QA_DESKTOP;
const TIMES=(process.env.QA_TIMES||'daytime,daybreak,sunset,dusk,night').split(',');
const STANDS=JSON.parse(process.env.QA_STANDS||JSON.stringify([
 ['fort-sw',[1112,180,1.7],[1152,221,4]],
 ['gate',[1149.6,192,1.7],[1150,215,4]],
 ['above',[1152,40,90],[1152,221,0]],
]));
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.wasm':'application/wasm','.ktx2':'image/ktx2'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const viewport=desktop?{width:1280,height:800}:{width:390,height:780};
const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:!desktop,hasTouch:!desktop});
const page=await context.newPage();page.setDefaultTimeout(240000);
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const tag=desktop?'desktop':'phone';
const rows=[];let identical=null;
try{
 await page.goto(`http://127.0.0.1:${server.address().port}/${YEAR}/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);a.step();});
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const hold=async(pos,target)=>page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});
   for(let i=0;i<3;i++)a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
   a.renderer.render(a.scene3d,a.camera);
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);
   let sum=0;for(let i=0;i<px.length;i+=4)sum+=0.2126*px[i]+0.7152*px[i+1]+0.0722*px[i+2];
   let hash=0;for(let i=0;i<px.length;i+=97)hash=(hash*31+px[i])|0;
   return {mean:Math.round(sum/(w*h)*10)/10,hash};},{pos,target});
 // Identity: the held boot frame, then night, then daytime again — rendered with no
 // step between, so the wind and the clock cannot move a pixel; and the light's own
 // numbers, which a step-free render cannot hide.
 const [n0,p0,t0]=STANDS[0];
 await hold(p0,t0);
 const still=()=>page.evaluate(()=>{const a=__chicago4d,R=a.renderer,L=a.world.light,u=a.world.sky.material.uniforms;
   R.render(a.scene3d,a.camera);const gl=R.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);
   let hash=0;for(let i=0;i<px.length;i++)hash=(hash*31+px[i])|0;
   return {hash,state:JSON.stringify([L.color.toArray(),L.intensity,a.world.direction.toArray(),R.toneMappingExposure,a.scene3d.environmentIntensity,u.sunPosition.value.toArray(),u.nightAmount.value,u.glowAmount.value,a.scene3d.userData.chiSkyFill,a.scene3d.fog?.color?.toArray()])};});
 const before=await still();
 await page.evaluate(()=>__chicago4d.timeOfDay.set('night',{transient:true}));
 await page.evaluate(()=>__chicago4d.timeOfDay.restore());
 const after=await still();
 identical={before,after,same:before.hash===after.hash&&before.state===after.state};
 console.log('daytime identity',JSON.stringify(identical));
 for(const time of TIMES){
  const cur=await page.evaluate((v)=>__chicago4d.timeOfDay.set(v,{transient:true}),time);
  const grade=await page.evaluate(()=>({sun:__chicago4d.world.describe(),exposure:__chicago4d.renderer.toneMappingExposure,key:__chicago4d.world.light.intensity}));
  for(const [name,pos,target] of STANDS){
   const r=await hold(pos,target);
   const file=`${tag}-${YEAR}-${name}-${time}.jpg`;
   await page.screenshot({path:path.join(out,file),type:'jpeg',quality:80});
   rows.push({time,stand:name,hhmm:cur.hhmm,...grade,mean:r.mean,file});
   console.log(time,cur.hhmm,name,grade.sun,'mean',r.mean);
  }
 }
 await page.evaluate(()=>__chicago4d.timeOfDay.restore());
}finally{
 fs.writeFileSync(path.join(out,`${tag}-${YEAR}.json`),JSON.stringify({viewport,year:YEAR,identical,errors,rows},null,1)+'\n');
 await browser.close();server.close();
}
const fail=[];
if(errors.length)fail.push('page errors: '+errors.join(' | '));
if(!identical?.same)fail.push('daytime after night is not the boot frame');
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
