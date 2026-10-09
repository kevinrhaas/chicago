import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright' : 'playwright');
const site=path.resolve(root,'../../site/4d'),out=process.env.QA_OUT || path.join(root,'docs/RESEARCH/glessner-roof-filtering-2204/after');
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=(process.env.QA_BASE_URL||`http://127.0.0.1:${server.address().port}`).replace(/\/$/,'');
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
fs.mkdirSync(out,{recursive:true}); const results=[];
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>bad.push(r.url()+':'+r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().includes('glessner_house')&&r.url().endsWith('.glb'))assets.push({url:r.url(),status:r.status()})});
 await page.goto(`${base}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:1000});
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 const pullback=process.env.QA_PULLBACK==='1',benchmark=process.env.QA_BENCHMARK==='1',review=process.env.QA_REVIEW==='1';
 const pullbackPaths=[3.4,5,7,9,12,16,20,25,32,40,50].map(distance=>{const k=distance/Math.hypot(3.3,.9);return [`pullback-${distance}`,[47.5+3.3*k,15,10.3+.9*k],[47.5,15,10.3]]});
 const motionPaths=[['near',[50.8,15,11.2],[47.5,15,10.3]],['street',[72,45,2],[38,17,10]],['overhead',[65,45,28],[30,17,8]],['northeast',[72,45,9],[38,17,10]]];
 const paths=pullback?pullbackPaths:review?[...motionPaths,...pullbackPaths]:motionPaths;
 for(const [view,start,target] of paths.filter(([name])=>(!process.env.QA_PATH||name===process.env.QA_PATH)&&(!benchmark||pullback||name==='northeast'))){
 const isPullback=view.startsWith('pullback-'),measure=benchmark||(review&&isPullback);
 for(let frame=0;frame<(isPullback?1:6);frame++){
  const name=`${view}-${frame}`,pos=[start[0]+(isPullback?0:(frame-2.5)*.025),start[1],start[2]];
  const beganCapture=performance.now();
  const observation=await page.evaluate(({pos,target,frame,benchmark})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});if(frame===0)a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);if(benchmark&&frame===0){const gl=a.renderer.getContext();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4))}const began=performance.now();a.renderer.render(a.scene3d,a.camera);a.renderer.getContext().finish();
   if(benchmark){const gl=a.renderer.getContext(),pixel=new Uint8Array(4);gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);if(pixel[3]!==255)throw Error('Opaque framebuffer readback failed')}
   const frameMs=performance.now()-began;
   const modes=new Set();a.scene3d.traverse(o=>{for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.userData.glassMode)modes.add(m.userData.glassMode)});
   const heightSamples=[49,50,53.66,54.2,46,41.1].map(x=>{const q=en([x,2.36,0]);return {x,terrain:a.terrain.surfaceHeight(q[0],q[1])-ground}});
   let filterBytes=0;a.buildings.group.traverse(o=>{filterBytes+=(o.geometry?.getAttribute('_roof_detail')?.count||0)*4});
   return {frameMs,filterBytes,textureCount:a.renderer.info.memory.textures,placement:pl,ground,heightSamples,detail:a.detail,glassModes:[...modes],problems:a.problems,stats:a.stats(),camera:p,target:t};
  },{pos,target,frame,benchmark:measure});
  await page.screenshot({path:path.join(out,`${label}-${name}.png`)});observation.frameCaptureWallMs=performance.now()-beganCapture;stands.push({name,...observation});
 }
 }
 const switches=[];
 for(const requested of ((pullback||benchmark)?[]:detail==='full'?['light','balanced','full']:['full','balanced','light'])){
  const switched=await page.evaluate(async requested=>{const a=__chicago4d;await a.setDetail(requested);a.step();
   const filters=[];a.buildings.group.traverse(o=>{if(o.material?.userData.roofFilter)filters.push({filter:o.material.userData.roofFilter,attribute:o.geometry.hasAttribute('_roof_detail'),anisotropy:o.material.map.anisotropy,depthWrite:o.material.depthWrite})});
   return {requested,detail:a.detail,filters,stats:a.stats(),problems:a.problems};},requested);
  if(switched.detail!==requested||!switched.filters.length||switched.filters.some(f=>!f.attribute||f.anisotropy!==8||!f.depthWrite)||!switched.stats.withinBudget||switched.problems.length)throw Error(JSON.stringify(switched));
  switches.push(switched);
 }
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget||x.glassModes.length!==1||x.glassModes[0]!=='dark'))throw Error(JSON.stringify({errors,bad,stands}));
 if(!assets.some(a=>a.url.endsWith(detail==='light'?'.light.glb':'__as_built_1887.glb')))throw Error('Expected canonical detail asset did not load');
 results.push({label,viewport,detail,boot,errors,bad,assets,stands,switches});
 await context.close();console.log(label+' actual published 1904 app: PASS');
}
}finally{fs.writeFileSync(path.join(out,process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+'.json' : 'browser-validation.json'),JSON.stringify({method:process.env.QA_REVIEW==='1'?'Four six-pose lateral paths, eleven 3.4–50 m fixed-target pullback poses, and Full/Light/Balanced switches per viewport. Pullback poses drain warm-up with readPixels before timing one render through a second readPixels. Lateral frameMs times submission only. frameCaptureWallMs includes IPC, optional warm-up and screenshot encoding. Software SwiftShader, not hardware FPS.':process.env.QA_PULLBACK==='1'&&process.env.QA_BENCHMARK==='1'?'Eleven 3.4–50 m fixed-target pullback poses per viewport. Each pose drains its warm-up with readPixels before timing one render through a second readPixels. frameCaptureWallMs also includes warm-up, IPC and screenshot encoding. Software SwiftShader, not hardware FPS.':process.env.QA_BENCHMARK==='1'?'Six northeast renders per viewport; GPU completion forced by readPixels. frameMs is browser render-through-readback time; frameCaptureWallMs also includes IPC and screenshot encoding. Software SwiftShader, not phone FPS.':process.env.QA_PULLBACK==='1'?'Eleven fixed-target pullback poses from 3.4 to 50 m in Full desktop and Light mobile, actual published 1904 app.':'Actual published /1904/ app; six successive rendered camera positions per near/street/overhead/northeast path, 25 mm lateral steps. Full desktop 1280×800 and Light mobile 390×780. Each timed render ends with WebGL finish; software Chromium/SwiftShader cost, not hardware FPS. UI simulation paused for matched before/after lighting and paths.',results},null,2)+'\n');await browser.close();server.close();}
