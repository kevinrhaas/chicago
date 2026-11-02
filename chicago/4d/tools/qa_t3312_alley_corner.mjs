// T-3312: the 1904 phone's `light` tier was over its 1,270,000-triangle ceiling from 60 m over the 18th Street /
// Prairie-Calumet alley corner (T-1936's `roof` stand, tools/qa_t1936_coach_houses.mjs: 1,598,204). This reads the
// actual published /1904/ app at 390x780 `light` and, at that stand and the others named below, renders each held
// frame three times in the same task: with the colour pass's far twins off (every structure piece drawn whole, as dev
// drew it), on (as shipped), and a positive control with every piece the shipped frame swapped hidden outright, so
// "few pixels changed" is a reading the comparison could have failed. Every draw of the off frame is charged to its
// layer and every structure range to its record (the method of tools/qa_t3012_triangles.mjs), so the table says what
// carries the stand. It fails on a page error, a failed request, a stand over light's ceiling as shipped, a shipped
// frame that draws more than the off frame, a control that changes no pixel at any stand, or more than
// QA_MAX_PIXELS (default 1% of the frame) pixels changed by the swap.
//   node tools/qa_t3312_alley_corner.mjs            (after tools/publish.sh)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/alley-corner-budget-3312');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.wasm':'application/wasm','.ktx2':'image/ktx2'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target, gated]: east, north, metres above the ground there. The first four are T-1936's
// (tools/qa_t1936_coach_houses.mjs), `roof` the one that was over; `air` is T-2992's, the district from 110 m,
// read for what the swap does there and NOT held to the ceiling here: it was already over on dev before this
// change (1,823,232 off), which is its own ticket, not this one.
const STANDS=JSON.parse(process.env.QA_STANDS||JSON.stringify([
 ['roof',[1500,-3250,60],[1461,-3300,0]],
 ['front-yards',[1432,-3283,32],[1461,-3296,3]],
 ['oblique-alley-north',[1458.4,-3258,1.7],[1466,-3320,4]],
 ['rear-alley-south',[1471,-3375,1.7],[1463,-3320,5]],
 ['air',[1360,-3620,110],[1300,-3480,0],false],
]));
const MAX_PIXELS=Number(process.env.QA_MAX_PIXELS||0.01);
const viewport={width:390,height:780};
const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:true,hasTouch:true});
const page=await context.newPage();page.setDefaultTimeout(240000);
const errors=[],bad=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status())});
let row=null;
try{
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/${process.env.QA_QUERY||''}`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail('light');a.step();
   const f=a.buildings.farColour;
   return {scene:a.scene?.id,detail:a.detail,ceiling:a.detailLevels.light.triangles,farColour:{active:f.active,pieces:f.pieces,twinTriangles:f.twinTriangles,twinVertices:f.twinVertices,buildMs:Math.round(f.buildMs)}};});
 if(boot.scene!=='1904'||boot.detail!=='light')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 console.log('boot',JSON.stringify(boot));
 const stands=[];
 for(const [name,pos,target,gated=true] of STANDS){
  const o=await page.evaluate(({pos,target,IMAGES})=>{const a=__chicago4d,B=a.buildings,R=a.renderer;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const gl=R.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
   // The held frame, rendered twice (the shadow box settles on the first) and read back inside the same task.
   const frame=(charge)=>{let by=null,rec=null;const orig=R.renderBufferDirect;
     for(let k=0;k<2;k++){
      if(charge&&k===1){by=new Map();rec=new Map();const o=orig.bind(R);
       R.renderBufferDirect=function(cam,scene,geo,mat,obj,group){const b=R.info.render.triangles;const res=o(cam,scene,geo,mat,obj,group);const d=R.info.render.triangles-b;
        let top=obj;while(top.parent&&top.parent!==a.scene3d)top=top.parent;const pass=cam===a.camera?'view':'sun';
        const e=by.get(top.name||top.type)||{view:0,sun:0};e[pass]+=d;by.set(top.name||top.type,e);
        if(obj.isBatchedMesh&&obj.userData.batchIndex){const ids=obj._indirectTexture?.image?.data,n=obj._multiDrawCount;
         for(let i=0;i<n;i++){const tr=obj._multiDrawCounts[i]/3,id=obj.userData.batchIndex[ids[i]]??'?';const r=rec.get(id)||{view:0,sun:0};r[pass]+=tr;rec.set(id,r);}}
        return res;};}
      a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);R.render(a.scene3d,a.camera);}
     R.renderBufferDirect=orig;
     const s=a.stats(),px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);
     const sum=(m)=>[...m].map(([k,e])=>({k,view:e.view,sun:e.sun,drawn:e.view+e.sun})).sort((x,y)=>y.drawn-x.drawn);
     return {triangles:s.triangles,drawCalls:s.drawCalls,withinBudget:s.withinBudget,px,layers:by&&sum(by).slice(0,10),structures:rec&&sum(rec).slice(0,15)};};
   const was=B.farColour.on;
   B.farColour.on=false;const off=frame(true);
   // the positive control: every piece the shipped test passes, hidden outright with no twin in its place
   B.farColour.on=true;B.farColour.control=true;const ctrl=frame(false);B.farColour.control=false;
   // and the shipped frame last, so the screenshot below is of it
   const on=frame(false);const swapped=B.farColour.swapped,saved=B.farColour.saved;
   B.farColour.on=was;
   const diff=(A,Bx)=>{let n=0,max=0;for(let i=0;i<A.length;i+=4){let d=0;for(let c=0;c<3;c++)d=Math.max(d,Math.abs(A[i+c]-Bx[i+c]));if(d){n++;max=Math.max(max,d);}}return {n,max};};
   const d=diff(off.px,on.px),c=diff(off.px,ctrl.px);
   // QA_IMAGES: the off and on frames whole, and the pixels that differ marked magenta on the off frame
   let images=null;
   if(IMAGES){const png=(px,mark)=>{const cv=document.createElement('canvas');cv.width=w;cv.height=h;const g=cv.getContext('2d'),im=g.createImageData(w,h);
     for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=((h-1-y)*w+x)*4,o=(y*w+x)*4;let r=px[i],gg=px[i+1],b=px[i+2];
      if(mark&&(on.px[i]!==off.px[i]||on.px[i+1]!==off.px[i+1]||on.px[i+2]!==off.px[i+2])){r=255;gg=0;b=255;}
      im.data[o]=r;im.data[o+1]=gg;im.data[o+2]=b;im.data[o+3]=255;}
     g.putImageData(im,0,0);return cv.toDataURL('image/png');};
    images={off:png(off.px,false),on:png(on.px,false),diff:png(off.px,true)};}
   return {off:{triangles:off.triangles,drawCalls:off.drawCalls,withinBudget:off.withinBudget},
     on:{triangles:on.triangles,drawCalls:on.drawCalls,withinBudget:on.withinBudget},
     swapped,saved,layersOff:off.layers,structuresOff:off.structures,pixels:w*h,pixelsDiffering:d.n,maxChannelDelta:d.max,controlPixelsDiffering:c.n,controlTriangles:ctrl.triangles,images};
  },{pos,target,IMAGES:!!process.env.QA_IMAGES});
  if(o.images){for(const k of ['off','on','diff'])fs.writeFileSync(path.join(out,`${name}-${k}.png`),Buffer.from(o.images[k].split(',')[1],'base64'));delete o.images;}
  stands.push({name,gated,...o});
  console.log(`${name}: ${o.off.triangles} -> ${o.on.triangles} (ceiling ${boot.ceiling}), draws ${o.off.drawCalls} -> ${o.on.drawCalls}, ${o.swapped} pieces swapped saving ${o.saved}, ${o.pixelsDiffering} of ${o.pixels} px differ (max ${o.maxChannelDelta}); control (swapped pieces hidden) ${o.controlPixelsDiffering} px`);
  await page.screenshot({path:path.join(out,`after-mobile-${name}.jpg`),type:'jpeg',quality:82});
 }
 row={viewport,detail:'light',boot,errors,bad,stands};
}finally{
 if(row)fs.writeFileSync(path.join(out,'browser-validation-mobile.json'),JSON.stringify({method:'Actual published /1904/ app at 390x780, `light`; animation paused after readiness; each stand renders the same held frame with the colour far twins off and on, read back whole; the off frame charged draw by draw to its layers and structure records.',...row},null,1)+'\n');
 await browser.close();server.close();
}
const fail=[];
if(errors.length)fail.push(`page errors: ${errors.join(' | ')}`);
if(bad.length)fail.push(`failed requests: ${bad.join(' ')}`);
for(const s of row?.stands??[]){
 if(s.gated&&!s.on.withinBudget)fail.push(`${s.name}: ${s.on.triangles} is over light's ceiling ${row.boot.ceiling}`);
 if(s.on.triangles>s.off.triangles)fail.push(`${s.name}: the shipped frame draws more than the off frame`);
 if(s.pixelsDiffering>MAX_PIXELS*s.pixels)fail.push(`${s.name}: ${s.pixelsDiffering} pixels changed, over ${MAX_PIXELS*100}% of the frame`);
}
// A stand whose swapped pieces all stand behind nearer walls (the alley at eye height) changes no pixel either
// way, rightly; what the control has to show is that the comparison CAN see a swapped piece somewhere.
if(row&&!row.stands.some(s=>s.controlPixelsDiffering>0))fail.push('the control (swapped pieces hidden) changed no pixel at any stand, so the comparison cannot see them');
if(!row)fail.push('no reading');
if(fail.length){console.error('FAIL\n '+fail.join('\n '));process.exit(1);}
console.log('PASS');
