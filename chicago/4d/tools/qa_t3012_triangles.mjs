// T-3012: what carries the triangles at the 1904 desktop stand on Calumet's east walk at 20th
// looking north (T-3008's `calumet-east-walk`, which read 4.63 M against the 4.6 M full budget).
// The actual published /1904/ app at 1280x800 full, framed exactly as tools/qa_draft_t3008.mjs
// frames it; then each
// draw's triangles are charged to its layers (the sun's pass included, which is how the budget
// counts them), three levels deep, largest first.
//   node tools/qa_t3012_triangles.mjs            (after tools/publish.sh)
//   QA_OUT=file.json node tools/qa_t3012_triangles.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d');
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const STANDS=JSON.parse(process.env.QA_STANDS||'[["calumet-east-walk",[1539,-3470,1.7],[1505,-3360,7]]]');
let out={method:'published /1904/, 1280x800, full detail, framed as tools/qa_draft_t3008.mjs; each draw charged through renderBufferDirect to its first three ancestors, view and sun pass apart',stands:[]},failed=null;
try{
 const context=await browser.newContext({viewport:{width:1280,height:800},deviceScaleFactor:1});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async()=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail('full');a.step();});
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 for(const [name,pos,target] of STANDS){
  const r=await page.evaluate(({pos,target,FOCUS,rel,PIXELS,CONTROL,CROPS})=>{const a=__chicago4d;
   if(rel){const c=a.structurePosition('glessner_house');pos=[c.e+pos[0],c.n+pos[1],pos[2]];target=[c.e+target[0],c.n+target[1],target[2]];}
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);return a.renderer.info.render.triangles;};
   frame();
   // every draw goes through renderBufferDirect, the sun's pass included: wrap it once and
   // charge each draw's triangles to the object's first two ancestors under the scene
   const R=a.renderer,orig=R.renderBufferDirect.bind(R),by=new Map(),rec=new Map(),focus=new Map();let unmatched=0;
   const label=o=>(o.name||o.type)+(o.userData?.id?'#'+o.userData.id:'');
   R.renderBufferDirect=function(cam,scene,geo,mat,obj,group){const b=R.info.render.triangles;const res=orig(cam,scene,geo,mat,obj,group);const d=R.info.render.triangles-b;
    const chain=[];for(let o=obj;o&&o!==a.scene3d;o=o.parent)chain.unshift(o);
    const pass=cam===a.camera?'view':'sun';const k=[chain[0],chain[1],chain[2]].filter(Boolean).map(label);
    for(let i=1;i<=k.length;i++){const key=k.slice(0,i).join(' / ');const e=by.get(key)||{view:0,sun:0,draws:0};e[pass]+=d;e.draws++;by.set(key,e);}
    // a structure batch: each multi-draw range is one instance, and batchIndex names its record
    if(obj.isBatchedMesh&&obj.userData.batchIndex){const ids=obj._indirectTexture?.image?.data,n=obj._multiDrawCount;let sum=0;
     for(let i=0;i<n;i++){const t=obj._multiDrawCounts[i]/3,id=obj.userData.batchIndex[ids[i]]??'?';const e=rec.get(id)||{view:0,sun:0};e[pass]+=t;rec.set(id,e);sum+=t;
      if(id===FOCUS){const m=obj.material,b=(m.map?.name||m.map?.source?.data?.src?.split('/').pop()||'')+' '+m.type+(m.transparent?' transparent':'')+' #'+(a.buildings.batches.indexOf(obj));const f=focus.get(b)||{view:0,sun:0,pieces:0};f[pass]+=t;f.pieces++;focus.set(b,f);}}
     unmatched+=d-sum;}
    return res;};
   const total=frame();R.renderBufferDirect=orig;const stats=a.stats();
   // QA_PIXELS: the same frame with Glessner's view filter off and on, read back whole
   let pixels=null;
   if(PIXELS){const gl=R.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
    const read=()=>{const b=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b);return b;};
    a.setGlessnerOcclusion(false);const offTris=frame(),off=read();
    a.setGlessnerOcclusion(true);const onTris=frame(),occ={...a.glessnerOcclusionStats()},on=read();
    const diff=(x,y)=>{let differ=0,maxd=0,at=[];for(let i=0;i<x.length;i+=4){let d=0;for(let k=0;k<3;k++)d=Math.max(d,Math.abs(x[i+k]-y[i+k]));if(d){differ++;maxd=Math.max(maxd,d);if(at.length<8)at.push([(i/4)%w,h-1-Math.floor(i/4/w),d]);}}return {differ,maxd,at};};
    const dd=diff(off,on);
    // QA_CROPS: each frame around the first differing pixel, 48 px square at 8x, as PNG data
    const crop=(b,cx,cy)=>{const S=48,Z=8,cv=document.createElement('canvas');cv.width=cv.height=S*Z;const g=cv.getContext('2d');
     for(let y=0;y<S;y++)for(let x=0;x<S;x++){const px=cx-S/2+x,py=cy-S/2+y;if(px<0||py<0||px>=w||py>=h)continue;const i=((h-1-py)*w+px)*4;g.fillStyle=`rgb(${b[i]},${b[i+1]},${b[i+2]})`;g.fillRect(x*Z,y*Z,Z,Z);}
     g.strokeStyle='#f0f';g.strokeRect(S/2*Z-1,S/2*Z-1,Z+2,Z+2);return cv.toDataURL('image/png');};
    const crops=CROPS&&dd.at.length?{at:dd.at[0],off:crop(off,dd.at[0][0],dd.at[0][1]),on:crop(on,dd.at[0][0],dd.at[0][1])}:null;
    pixels={width:w,height:h,trianglesFilterOff:offTris,trianglesFilterOn:onTris,pixelsDiffering:dd.differ,maxChannelDifference:dd.maxd,differingAt:dd.at,filter:occ,crops};
    // QA_CONTROL: the filter-off frame rendered twice, so a difference above can be read against the renderer's own
    if(CONTROL){a.setGlessnerOcclusion(false);frame();const off2=read();a.setGlessnerOcclusion(true);const c=diff(off,off2);pixels.controlOffOff={pixelsDiffering:c.differ,maxChannelDifference:c.maxd,differingAt:c.at};frame();}}
   const rows=[...by].map(([k,e])=>({layer:k,depth:k.split(' / ').length,...e,drawn:e.view+e.sun})).sort((x,y)=>y.drawn-x.drawn);
   const structures=[...rec].map(([id,e])=>({id,...e,drawn:e.view+e.sun})).sort((x,y)=>y.drawn-x.drawn);
   return {total,budget:stats.budget,withinBudget:stats.withinBudget,drawCalls:stats.drawCalls,rows,structures,structureTrianglesUnmatched:unmatched,pixels,focus:FOCUS?{id:FOCUS,batches:[...focus].map(([k,f])=>({batch:k,...f,drawn:f.view+f.sun})).sort((x,y)=>y.drawn-x.drawn)}:null};
  },{pos,target,FOCUS:process.env.QA_FOCUS||'',rel:name.startsWith('glessner-'),PIXELS:!!process.env.QA_PIXELS,CONTROL:!!process.env.QA_CONTROL,CROPS:!!process.env.QA_CROPS});
  if(r.pixels?.crops){for(const k of ['off','on'])fs.writeFileSync(`${process.env.QA_CROPS}/${name}-${k}.png`,Buffer.from(r.pixels.crops[k].split(',')[1],'base64'));r.pixels.crops={at:r.pixels.crops.at};}
  out.stands.push({name,...r});console.log(name,r.total,JSON.stringify(r.budget),r.pixels?'pixels '+JSON.stringify(r.pixels):'');
  if(process.env.QA_BRIEF)continue;
  for(const d of [1,2,3])for(const l of r.rows.filter(x=>x.depth===d).slice(0,d===1?12:25))console.log(' '.repeat(d*2),l.drawn,'view',l.view,'sun',l.sun,'draws',l.draws,l.layer);
  console.log('  structures (unmatched',r.structureTrianglesUnmatched+'):');for(const x of r.structures.slice(0,40))console.log('    ',x.drawn,'view',x.view,'sun',x.sun,x.id);
  if(r.focus){console.log('  '+r.focus.id+' by batch:');for(const b of r.focus.batches.slice(0,30))console.log('    ',b.drawn,'view',b.view,'sun',b.sun,'pieces',b.pieces,b.batch);}
 }
 out.errors=errors;await context.close();
}catch(e){failed=e;}
finally{if(process.env.QA_OUT)fs.writeFileSync(process.env.QA_OUT,JSON.stringify(out,null,1)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,3000));process.exit(1);}
