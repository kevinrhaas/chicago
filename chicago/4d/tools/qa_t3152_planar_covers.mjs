// T-3152: Glessner's 18th Street stand 45 m west and 32 m north stood only 5,843 triangles
// inside Full's 4.6 M budget after T-3146, because the house's court, south and east walls,
// hidden behind its own north and west fronts, still went to the colour pass: T-2227's filter
// proves a piece hidden only inside ONE backing triangle, and Glessner's flat mortar backing is
// cut into thousands of slivers. planar-occluders.js now proves rectangles of each large plane
// covered and hands them to the same filter. This reads the actual published /1904/ app at
// 1280x800 `full` (or QA_VIEWPORT=390x780), at the T-3146 stands, rendering the same held frame
// with the rectangles OFF and ON (the filter itself on both times), the triangles each way and
// every pixel compared. Two controls: the whole filter off must change no pixel either, and
// hiding Glessner must change the frame, so "no pixel changed" can see the house.
//   node tools/qa_t3152_planar_covers.mjs            (after tools/publish.sh)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/glessner-planar-covers-3152');
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
  const o=await page.evaluate(({pos,target,rel,CONTROL,BISECT})=>{const a=__chicago4d;
   if(rel){const c=a.structurePosition('glessner_house');pos=[c.e+pos[0],c.n+pos[1],pos[2]];target=[c.e+target[0],c.n+target[1],target[2]];}
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=a.renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // Render the held frame twice (the shadow box settles on the first), then read it back
   // inside the same task, before the browser can present and clear the buffer.
   const frame=()=>{let tris=0;for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);tris=a.renderer.info.render.triangles;}
     const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);return {triangles:tris,stats:a.stats(),px};};
   const diff=(x,y)=>{let differ=0,maxDelta=0;const at=[];for(let i=0;i<x.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(x[i+c]-y[i+c]));if(d){differ++;maxDelta=Math.max(maxDelta,d);if(at.length<8)at.push({x:(i/4)%w,y:Math.floor(i/4/w),a:[x[i],x[i+1],x[i+2]],b:[y[i],y[i+1],y[i+2]]});}}return {differ,maxDelta,at};};
   if(!a.setGlessnerOcclusion(true))throw Error('the view filter is not on at this tier');
   a.setPlanarCovers(false);const off=frame(),off2=CONTROL?frame():off;const statsOff=a.glessnerOcclusionStats();
   let bisect=null;
   if(BISECT){console.log('bisect start',Date.now());bisect=[];const covers=a.buildings.planarCovers,saved=covers.map(c=>c.active);
     const only=(set)=>{covers.forEach((c,i)=>{c.active=set.includes(i)?saved[i]:()=>false;});a.setPlanarCovers(true);return diff(off.px,frame().px);};
     let set=covers.map((c,i)=>i);
     while(set.length>1){const half=set.slice(0,set.length>>1),dd=only(half);bisect.push({half:half.length,differ:dd.differ});set=dd.differ?half:set.slice(set.length>>1);}
     const k=set[0],dd=only(set);const c=covers[k];
     bisect.push({k,structure:c.structure,n:c.n,o:c.o,u:c.u,v:c.v,W:c.W,H:c.H,cells:c.cells,differ:dd.differ,at:dd.at,stats:a.glessnerOcclusionStats()});
     covers.forEach((c,i)=>{c.active=saved[i];});return {bisect};}
   a.setPlanarCovers(true);const on=frame();const statsOn=a.glessnerOcclusionStats();
   a.setGlessnerOcclusion(false);const none=frame();a.setGlessnerOcclusion(true);a.setPlanarCovers(true);frame();
   // The positive control: Glessner hidden, the frame has to change.
   const g=a.buildings.group;const hidden=[];g.traverse(o=>{if(o.isBatchedMesh&&o.userData.batchIndex)o.userData.batchIndex.forEach((id,i)=>{if(id==='glessner_house'&&o.getVisibleAt(i)){o.setVisibleAt(i,false);hidden.push([o,i]);}});});
   const dark=frame();for(const [o,i] of hidden)o.setVisibleAt(i,true);frame();
   const d=diff(off.px,on.px),n=diff(none.px,on.px),f0=diff(none.px,off.px),c=diff(off.px,dark.px),r=diff(off.px,off2.px);
   return {off:{triangles:off.triangles,drawCalls:off.stats.drawCalls,culled:statsOff.culled,culledTriangles:statsOff.triangles,occluders:statsOff.occluders},
     on:{triangles:on.triangles,drawCalls:on.stats.drawCalls,withinBudget:on.triangles<=on.stats.budget.triangles,culled:statsOn.culled,culledTriangles:statsOn.triangles,planeCulled:statsOn.planeCulled,planeTriangles:statsOn.planeTriangles,planes:statsOn.planes,occluders:statsOn.occluders},
     filterOff:{triangles:none.triangles},
     bisect,pixels:w*h,pixelsDiffering:d.differ,differingAt:d.at,noFilterDifferingAt:n.at,maxChannelDelta:d.maxDelta,pixelsDifferingFromNoFilter:n.differ,offPixelsDifferingFromNoFilter:f0.differ,
     controlOffOffPixelsDiffering:CONTROL?r.differ:null,controlPixelsDifferingWithoutGlessner:c.differ,problems:a.problems.length};
  },{pos,target,rel,CONTROL:!!process.env.QA_CONTROL,BISECT:!!process.env.QA_BISECT});
  if(process.env.QA_SHOTS)await page.screenshot({path:path.join(out,`after-${tag}-${name}.jpg`),type:'jpeg',quality:82});
  stands.push({name,...o});if(o.bisect){console.log(JSON.stringify(o.bisect));continue;}
  console.log(`${name}: ${o.off.triangles} -> ${o.on.triangles} triangles (budget ${boot.budget.triangles}; filter off ${o.filterOff.triangles}), pieces hidden ${o.off.culled} -> ${o.on.culled} + ${o.on.planeCulled} by ${o.on.planes} covers (${o.on.planeTriangles} triangles), ${o.pixelsDiffering} of ${o.pixels} pixels differ (from no filter ${o.pixelsDifferingFromNoFilter}, T-2227 alone ${o.offPixelsDifferingFromNoFilter}; off/off control ${o.controlOffOffPixelsDiffering}; without Glessner ${o.controlPixelsDifferingWithoutGlessner})`);
 }
}finally{
 fs.writeFileSync(process.env.QA_OUT||path.join(out,`browser-validation-${tag}.json`),JSON.stringify({method:`Actual published /1904/ app at ${vw}x${vh}, \`full\`; animation paused after readiness; each stand renders the same held frame with the T-3152 planar backings off (setPlanarCovers(false)), off again (QA_CONTROL), on, and with the whole T-2227 filter off, and with Glessner hidden as the positive control, reads triangles from renderer.info and every pixel with gl.readPixels in the same task. glessner-* stands are offsets in metres from Glessner's footprint centre. Software GL on this machine.`,result:row},null,2)+'\n');
 await browser.close();server.close();
}
const fail=[];
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
for(const s of row?.stands??[]){
 if(s.bisect)continue;
 if(!s.on.withinBudget)fail.push(`${s.name}: ${s.on.triangles} is over full's budget ${row.boot.budget.triangles}`);
 if(!s.controlPixelsDifferingWithoutGlessner)fail.push(`${s.name}: hiding Glessner changed no pixel, so the comparison cannot see the house`);
 // T-3012 accepted T-2227 alone at 3 pixels of 1,024,000 a few levels apart. The covers are
 // held to the same bar and every pixel they change is listed: at most 4, none over 4 levels.
 if(s.pixelsDiffering>4||s.maxChannelDelta>4)fail.push(`${s.name}: the covers changed ${s.pixelsDiffering} pixels against T-2227 alone (max ${s.maxChannelDelta} levels)`);
 if(s.on.triangles>s.off.triangles)fail.push(`${s.name}: the rectangles added triangles`);
}
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
