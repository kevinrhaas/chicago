// T-2359: the K14 chimney plume on 1808 Prairie's slate, leeward of its two K15 stacks, read in the actual published /1904/ app.
// Fixed stands written in the assembly's own footprint frame (u east, v north, metres
// above the ground at its origin): the roof from above the street, and each stack close
// from its lee side (the library's on the south hip, the hall's on the north), at 1280x800
// full detail and 390x780 light detail. Records the scene load, draws, triangles and a timed
// frame at every stand, and screenshots each.
//   node tools/qa_k14_t2359.mjs            (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_k14_t2359.mjs
//   QA_BEFORE=<a previous web GLB> QA_VIEWPORT=desktop node tools/qa_k14_t2359.mjs
//                                  serves that file as 1808's GLB and writes before-* files
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/k14-1808-roof-2359');
fs.mkdirSync(out,{recursive:true});
const ID='keith_house_1808_prairie';
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const BEFORE=process.env.QA_BEFORE,pre=BEFORE?'before-':'';
const {parseGlb,readAccessor}=await import(path.join(root,'tools/k01_contract.mjs'));
const {MeshoptDecoder}=await import(path.join(root,'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js'));
await MeshoptDecoder.ready;
// the slate's _TONE in each tier: its least value, its mean and how many vertices carry it
async function slateTone(file){
 const {json,bin}=parseGlb(fs.readFileSync(file));
 const ctx={json,bin,views:new Map(),meshopt:MeshoptDecoder};
 for(const mesh of json.meshes)for(const prim of mesh.primitives){
  if(json.materials[prim.material]?.name!=='slate_covering')continue;
  if(prim.attributes._TONE===undefined)return null;
  const t=readAccessor(ctx,prim.attributes._TONE);let lo=1,n=0;for(const x of t){lo=Math.min(lo,x);if(x<0.999)n++;}
  return {vertices:t.length,toned:n,min:+lo.toFixed(4)};}
 return null;
}
const tones={full:await slateTone(path.join(root,`assets/gltf/${ID}__as_built_1886.glb`)),web:await slateTone(BEFORE||path.join(root,`assets/web/${ID}__as_built_1886.glb`))};
console.log('slate tone by tier '+JSON.stringify(tones));
if(!BEFORE&&(!tones.web||tones.web.min>=0.999))throw Error('the slate carries no plume in the web tier: '+JSON.stringify(tones.web));
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));if(BEFORE&&p.endsWith('.glb')&&p.includes(ID))p=path.resolve(BEFORE);try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target] in the footprint frame: the front is the u = 18 face, 10.4 m across;
// the stacks stand at (u 12.1, v 0.65), the library's, and (u 13.6, v 9.75), the hall's, their
// tops 16.8 m up, and each plume runs 1.35 m east-north-east (+u, +v) across the slate
const STANDS=[
 ['roof',[32,-9,24],[13,5,13]],
 ['library-stack',[16.8,-2.6,18.2],[12.9,1.0,13.6]],
 ['hall-stack',[19.2,6.2,18.6],[14.3,10.0,12.9]],
];
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
  await page.screenshot({path:path.join(out,`${pre}${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,boot,errors,bad,assets,stands,slate_tone:tones,before:BEFORE?path.basename(BEFORE):null};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 if(!assets.some(a=>a.url.includes(ID)&&a.status<400))throw Error(`${ID}'s GLB never loaded`);
 await context.close();console.log(label+' actual published 1904 app with the K14 roof plume: PASS');
}
}catch(e){failed=e;}
finally{
 const method='Actual published /1904/ app, normal boot; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is 5 renders each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).';
 for(const row of results){
  const file=path.join(out,`${pre}browser-validation-${row.label}.json`);
  let prev=null;try{prev=JSON.parse(fs.readFileSync(file,'utf8')).results?.[0]}catch{}
  if(prev&&process.env.QA_STANDS){const keep=prev.stands.filter(x=>!row.stands.some(y=>y.name===x.name));row.stands=STANDS.map(([n])=>[...keep,...row.stands].find(x=>x.name===n)).filter(Boolean);}
  fs.writeFileSync(file,JSON.stringify({method,results:[row]},null,2)+'\n');
 }
 await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
