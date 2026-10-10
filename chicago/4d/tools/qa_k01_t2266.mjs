// T-2266: the K01 frontage at 1808 Prairie, read in the actual published /1904/ app.
// Fixed stands written in the assembly's own footprint frame (u east, v north, metres
// above the ground at its origin): street-eye, oblique, rear, roof and the courtyard
// join with Glessner, at 1280x800 full detail and 390x780 light detail. Records the
// scene load, draws, triangles and a timed frame at every stand, and screenshots each.
//   node tools/qa_k01_t2266.mjs            (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_k01_t2266.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
// T-2293: QA_K04=1 re-reads the same house for its K04 roof — the stands below plus a
// dormer, a grazing look along the eave and a downpipe's shoe — into its own folder.
const K04=process.env.QA_K04==='1';
// T-2289: QA_K02=1 re-reads it for its K02 stone front — the stands below plus the
// front, a flat arch and the rusticated base under an area light at 3-9 m, each twice: in a
// RAKING sun (the scene's own sun moved to 25 degrees up, 10 degrees off the front's
// plane from the south, so every course, joint, chip and rock face throws a shadow) and
// in DIFFUSE light (the sun off; sky and environment only), into its own folder.
const K02=process.env.QA_K02==='1';
const site=path.resolve(root,'../../site/4d'),out=path.join(root,K02?'docs/RESEARCH/k02-1808-stone-2289':K04?'docs/RESEARCH/k04-1808-roof-2293':'docs/RESEARCH/k01-1808-frontage-2266');
fs.mkdirSync(out,{recursive:true});
const ID='keith_house_1808_prairie';
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target] in the footprint frame: the front is the u = 18 face, 10.4 m across
const STANDS=[
 ['street-eye',[40,5.2,1.7],[18,5.2,7]],
 ['oblique',[33,-10,1.7],[12,8,7]],
 ['rear',[-17,-3,1.7],[0,5.2,7]],
 ['roof',[34,-14,27],[9,5.2,11]],
 ['courtyard-join',[-6,21,1.7],[6,10.4,6]],
 ...(K04?[
  ['dormer',[29,5.2,15.5],[17.6,5.2,14]],
  ['eave-grazing',[23,-4.5,13.2],[15,0.6,12]],
  ['downpipe-shoe',[20.6,-1.8,1.3],[18.1,-0.35,0.25]],
 ]:[]),
 ...(K02?['raking','diffuse'].flatMap(light=>[
  [light+'-front',[27,-3,4],[18,4,3.5],light],
  // the third floor's flat arch over the middle window, and the base under the area
  // light beside the stoop: the K08 bow (T-2308) now stands at the south corner
  [light+'-arch',[21.2,7.4,11.0],[18,5,11.4],light],
  [light+'-base',[21.4,2.6,1.5],[18,5.2,0.7],light],
 ]):[]),
// QA_STANDS=a,b runs those stands alone (T-2289): on software GL a stand costs about a
// minute, so the K02 set is read in parts that each fit a 600 s foreground call
].filter(([name])=>!process.env.QA_STANDS||process.env.QA_STANDS.split(',').includes(name));
const PART=process.env.QA_STANDS?'-'+process.env.QA_STANDS.split(',')[0]:'';
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
 for(const [name,pos,target,light] of STANDS){
  const observation=await page.evaluate(({pos,target,id,light})=>{const a=__chicago4d,pl=a.registry.get(id).sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const sun=a.scene3d.getObjectByName('sun');a.__sunIntensity??=sun.intensity;sun.intensity=light==='diffuse'?0:a.__sunIntensity;
   // the raking sun, in the footprint frame (u east, v north, up), then to three's (e, up, -n)
   const alt=25*Math.PI/180,off=10*Math.PI/180,ru=Math.cos(alt)*Math.sin(off),rv=-Math.cos(alt)*Math.cos(off);
   const rake=[ru*Math.cos(th)+rv*Math.sin(th),Math.sin(alt),-(-ru*Math.sin(th)+rv*Math.cos(th))];
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   const frame=()=>{a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);
    if(light==='raking'){sun.position.set(sun.target.position.x+rake[0]*320,sun.target.position.y+rake[1]*320,sun.target.position.z+rake[2]*320);sun.updateMatrixWorld();sun.shadow.needsUpdate=true;}
    a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);};
   frame();
   // a timed frame: render and wait for the GPU (a one-pixel read) — 12 of them, median
   const gl=a.renderer.getContext(),px=new Uint8Array(4),ms=[];
   for(let i=0;i<12;i++){const s=performance.now();frame();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);ms.push(performance.now()-s);}
   ms.sort((x,y)=>x-y);
   return {...(light?{light}:{}),detail:a.detail,problems:a.problems,stats:a.stats(),frame_ms_median:Math.round(ms[6]*10)/10,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100)};
  },{pos,target,id:ID,light});
  await page.screenshot({path:path.join(out,`${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,boot,errors,bad,assets,stands};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget))throw Error(JSON.stringify(row));
 if(!assets.some(a=>a.url.includes(ID)&&a.status<400))throw Error(`${ID}'s GLB never loaded`);
 await context.close();console.log(label+' actual published 1904 app with the K01 frontage: PASS');
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+PART+'.json' : 'browser-validation'+PART+'.json'),JSON.stringify({method:'Actual published /1904/ app, normal boot; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is 12 renders each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
