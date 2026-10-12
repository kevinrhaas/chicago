// T-2304: the 1808 exemplar's door and stoop built from the K07 entrance kit, read in the
// actual published /1904/ app. tools/qa_k06_t2298.mjs's harness and frame (u east, v north,
// metres above the ground at the footprint origin); its stands are the K07 acceptance's:
// front, oblique, rear and roof, then the door at 2.5 m from the landing in a raking view,
// and the stoop seen at about 5 m from Prairie Avenue's walk — at 1280x800 full and 390x780 light.
//   node tools/qa_k07_t2304.mjs            (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_k07_t2304.mjs
//   QA_PART=a|b                         the first or last three stands (software GL is slow:
//                                        one viewport's six stands outrun a 600 s call)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/k07-1808-entrance-2304');
fs.mkdirSync(out,{recursive:true});
const ID='keith_house_1808_prairie';
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target] in the footprint frame: the front is the u = 18 face, 10.4 m across,
// its bays at v = 2.0, 5.0, 8.4 (the door, north); the principal floor 1.5 m; the stoop runs
// 3.6 m out to u = 21.6 and the walk begins at u = 22.75
const STANDS=[
 ['street-eye',[40,5.2,1.7],[18,5.2,7]],
 ['oblique',[33,-10,1.7],[12,8,7]],
 ['rear',[-17,-3,1.7],[0,5.2,7]],
 ['roof',[34,-14,27],[9,5.2,11]],
 ['door-2.5m-raking',[20.2,7.1,3.2],[18,8.4,2.9]],
 ['stoop-from-walk',[23.4,4.6,1.7],[19.4,8.4,0.9]],
];
const PART=process.env.QA_PART||'';
const RUN=PART==='a'?STANDS.slice(0,3):PART==='b'?STANDS.slice(3):STANDS;
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
 for(const [name,pos,target] of RUN){
  const observation=await page.evaluate(({pos,target,id})=>{const a=__chicago4d,pl=a.registry.get(id).sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();
   // a timed frame: render and wait for the GPU (a one-pixel read) — 12 of them, median
   const gl=a.renderer.getContext(),px=new Uint8Array(4),ms=[];
   for(let i=0;i<12;i++){const s=performance.now();frame();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);ms.push(performance.now()-s);}
   ms.sort((x,y)=>x-y);
   return {detail:a.detail,problems:a.problems,stats:a.stats(),frame_ms_median:Math.round(ms[6]*10)/10,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100)};
  },{pos,target,id:ID});
  await page.screenshot({path:path.join(out,`${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,boot,errors,bad,assets,stands};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 if(!assets.some(a=>a.url.includes(ID)&&a.status<400))throw Error(`${ID}'s GLB never loaded`);
 await context.close();console.log(label+' actual published 1904 app with the K07 entrance on the 1808 exemplar: PASS');
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'browser-validation'+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+(PART?'-'+PART:'')+'.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is 12 renders each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
