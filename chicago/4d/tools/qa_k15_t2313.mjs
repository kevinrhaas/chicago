// T-2313: 1808 Prairie's two K15 chimney stacks (over the 1888 plan's library and hall fireplaces), read in the actual published /1904/ app.
// Fixed stands written in the assembly's own footprint frame (u east, v north, metres
// above the ground at its origin): the front, an oblique, the rear and the roof, and each stack
// close from above (its flues, cap, flashing and cricket),
// at 1280x800 full detail and 390x780 light detail. Records the
// scene load, draws, triangles and a timed frame at every stand, and screenshots each; and
// reads every stack's plan centre and top off BOTH shipped tiers' bytes (the master and the
// web derivative every detail level loads), so the reduced tier is shown to keep them.
//   node tools/qa_k15_t2313.mjs            (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_k15_t2313.mjs
//   QA_STANDS=front,oblique ...   a subset, so each run fits a 600 s foreground call; the stands
//                                  it reads are merged into that viewport's JSON by name
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/k15-1808-chimneys-2313');
fs.mkdirSync(out,{recursive:true});
const ID='keith_house_1808_prairie';
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target] in the footprint frame: the front is the u = 18 face, 10.4 m across;
// the library stack stands at (12.1, 0.65) on the south wall, the hall stack at (13.6, 9.75)
// on the north wall, both topping at 16.8 m; the eave is 12.4 m and the ridge 17.6 m
const STANDS=[
 ['front',[44,5.2,1.7],[18,5.2,10]],
 ['oblique',[34,-14,1.7],[13,3,11]],
 ['rear',[-18,4,1.7],[0,5.2,11]],
 ['roof',[30,-10,26],[12,5.2,14]],
 ['library-stack-close',[16.5,-3.5,19.5],[12.1,0.65,15.6]],
 ['hall-stack-close',[17.5,6.5,19.5],[13.6,9.75,15.6]],
];
const STACKS={library:[12.1,0.65],hall:[13.6,9.75]};
// the GLB frame is the footprint frame: x = u, y up, z = -v. Vertices within 0.9 m of a
// stack's plan centre and above 13.4 m (the eave is 12.4 m) are that stack's.
const {parseGlb,readAccessor}=await import(path.join(root,'tools/k01_contract.mjs'));
const {MeshoptDecoder}=await import(path.join(root,'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js'));
await MeshoptDecoder.ready;
async function stacksIn(rel){
 const {json,bin}=parseGlb(fs.readFileSync(path.join(root,rel)));
 const ctx={json,bin,views:new Map(),meshopt:MeshoptDecoder};
 const out=Object.fromEntries(Object.keys(STACKS).map(k=>[k,[]]));
 for(const node of json.nodes.filter(n=>n.mesh!==undefined)){
  const [tx,ty,tz]=node.translation||[0,0,0],[sx,sy,sz]=node.scale||[1,1,1];
  if(node.rotation&&node.rotation.some((x,i)=>Math.abs(x-[0,0,0,1][i])>1e-9))throw Error(rel+': a rotated node');
  for(const prim of json.meshes[node.mesh].primitives){
   const raw=readAccessor(ctx,prim.attributes.POSITION);
   for(let i=0;i<raw.length;i+=3){const u=raw[i]*sx+tx,y=raw[i+1]*sy+ty,v=-(raw[i+2]*sz+tz);if(y<13.4)continue;
    for(const k in STACKS){const [cu,cv]=STACKS[k];if(Math.abs(u-cu)<0.9&&Math.abs(v-cv)<0.9)out[k].push([u,v,y]);}}}}
 // the plan centre off the cap course alone (the top 0.25 m): the cricket and flashing
 // below it stand to one side of the shaft, the cap all round it
 return Object.fromEntries(Object.entries(out).map(([k,pts])=>{if(!pts.length)return [k,null];
  const top=Math.max(...pts.map(p=>p[2])),cap=pts.filter(p=>p[2]>=top-0.25),mid=i=>(Math.min(...cap.map(p=>p[i]))+Math.max(...cap.map(p=>p[i])))/2;
  return [k,{vertices:pts.length,centre:[+mid(0).toFixed(3),+mid(1).toFixed(3)],top_m:+top.toFixed(3)}];}));
}
const tierStacks={full:await stacksIn(`assets/gltf/${ID}__as_built_1886.glb`),web:await stacksIn(`assets/web/${ID}__as_built_1886.glb`)};
console.log('stacks by tier '+JSON.stringify(tierStacks));
if(Object.values(tierStacks).some(t=>Object.values(t).some(x=>!x)))throw Error('a stack is missing from a tier: '+JSON.stringify(tierStacks));
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',async r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().endsWith('.glb')&&(r.url().includes(ID)||r.url().includes('glessner_house')))assets.push({url:r.url().replace(/^.*\/data\//,'data/'),status:r.status(),bytes:Number(r.headers()['content-length']||0)})});
 const t0=Date.now();
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 const loadMs=Date.now()-t0;
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const placed=await page.evaluate(id=>Boolean(__chicago4d.registry.get(id)?.sidecar?.placement),ID);
 if(!placed)throw Error(`${ID} is not in the 1904 registry`);
 const stands=[];
 const only=process.env.QA_STANDS?.split(',');
 for(const [name,pos,target] of STANDS.filter(([n])=>!only||only.includes(n))){
  const observation=await page.evaluate(({pos,target,id})=>{const a=__chicago4d,pl=a.registry.get(id).sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();
   // a timed frame: render and wait for the GPU (a one-pixel read) — 5 of them, median
   const gl=a.renderer.getContext(),px=new Uint8Array(4),ms=[];
   for(let i=0;i<5;i++){const s=performance.now();frame();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);ms.push(performance.now()-s);}
   ms.sort((x,y)=>x-y);
   return {detail:a.detail,problems:a.problems,stats:a.stats(),frame_ms_median:Math.round(ms[2]*10)/10,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100)};
  },{pos,target,id:ID});
  await page.screenshot({path:path.join(out,`${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,boot,errors,bad,assets,stands,stacks:tierStacks};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 if(!assets.some(a=>a.url.includes(ID)&&a.status<400))throw Error(`${ID}'s GLB never loaded`);
 await context.close();console.log(label+' actual published 1904 app with the K15 chimneys: PASS');
}
}catch(e){failed=e;}
finally{
 const method='Actual published /1904/ app, normal boot; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is 5 renders each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).';
 for(const row of results){
  const file=path.join(out,`browser-validation-${row.label}.json`);
  let prev=null;try{prev=JSON.parse(fs.readFileSync(file,'utf8')).results?.[0]}catch{}
  if(prev&&process.env.QA_STANDS){const keep=prev.stands.filter(x=>!row.stands.some(y=>y.name===x.name));row.stands=STANDS.map(([n])=>[...keep,...row.stands].find(x=>x.name===n)).filter(Boolean);}
  fs.writeFileSync(file,JSON.stringify({method,results:[row]},null,2)+'\n');
 }
 await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
