// T-2227 external audit harness, reusing the established published camera/render instrumentation.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright' : 'playwright');
const site=path.resolve(root,'../../site/4d'),out=process.env.QA_OUT || '/tmp/glessner-performance';
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=(process.env.QA_BASE_URL||`http://127.0.0.1:${server.address().port}`).replace(/\/$/,'');
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
fs.mkdirSync(out,{recursive:true}); const results=[];
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['balanced',{width:1280,height:800},'balanced'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 if(process.env.QA_BOOT_DETAIL)await context.addInitScript(level=>localStorage.setItem('chicago4d.settings',JSON.stringify({detail:level})),process.env.QA_BOOT_DETAIL);
 const page=await context.newPage();page.setDefaultTimeout(240000);
 page.on('console', msg=>{if(msg.text().startsWith('QA_MOTION '))console.log(label+' '+msg.text());});
 const errors=[],bad=[],assets=[],requestedPaths=new Set();
 page.on('request',r=>{const u=new URL(r.url());if(u.origin===new URL(base).origin)requestedPaths.add(u.pathname);});
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>bad.push(r.url()+':'+r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().includes('glessner_house')&&r.url().endsWith('.glb'))assets.push({url:r.url(),status:r.status()})});
 console.log(label+' navigation starting');
 await page.goto(`${base}/1904/${process.env.QA_SEARCH||''}`,{waitUntil:'domcontentloaded'});
 console.log(label+' DOM loaded');
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:1000}).catch(error=>{fs.writeFileSync(path.join(out,'startup-failure-'+label+'.json'),JSON.stringify({error:String(error),errors,bad,assets,url:page.url()},null,2));throw error;});
 const boot=await page.evaluate(()=>{const a=__chicago4d,gl=a.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {ready:a.ready,error:a.error,scene:a.scene?.id,detail:a.detail,readyAt:a.boot.readyAt,renderedAt:a.boot.renderedAt,phases:a.boot.timings(),userAgent:navigator.userAgent,cores:navigator.hardwareConcurrency,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),memory:a.renderer.info.memory,programs:a.renderer.info.programs.length};});
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 console.log(label+' boot ready');
 if(process.env.QA_BOOT_DETAIL && boot.detail!==process.env.QA_BOOT_DETAIL)throw Error('Requested saved boot detail was not used');
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;a.setAnimationHold(true);if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 const roundTrip=process.env.QA_CYCLE_DETAIL ? await page.evaluate(async()=>{
  const a=__chicago4d,first={...a.contextCity.census};
  await a.setDetail('balanced');const balanced={...a.contextCity.census};
  await a.setDetail('light');const light={...a.contextCity.census};
  if(JSON.stringify(first)!==JSON.stringify(light)||balanced.triangles<=light.triangles)throw Error('Context detail round trip did not restore its exact census');
  return {first,balanced,light,season:a.season?.current};
 }) : null;
 await page.waitForFunction(detail=>{const s=__chicago4d.streetTrees.stats;return s.detail===detail && (s.mode==='hidden'||s.drawCalls===(detail==='full'?2:1));},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 await page.waitForFunction(()=>{const h=document.getElementById('hint');return !h || (!h.classList.contains('on') && getComputedStyle(h).opacity==='0');});
 console.log(label+' selected '+detail+' and entered scene');
 // Same existing API census as tools/measure_shipped_batches.mjs. This is
 // scene construction cost, distinct from the per-camera main/shadow draws.
 const buildingBatchCensus=await page.evaluate(()=>__chicago4d.buildings.batches.map(b=>{
  const m=b.material, ids=b.userData.batchIndex||[];
  const maps=Object.fromEntries(['map','normalMap','aoMap','roughnessMap','metalnessMap','emissiveMap'].map(k=>{
   const t=m[k];return [k,t?{uuid:t.uuid,source:t.source.uuid,channel:t.channel,wrapS:t.wrapS,wrapT:t.wrapT,minFilter:t.minFilter,magFilter:t.magFilter,colorSpace:t.colorSpace,repeat:t.repeat.toArray(),offset:t.offset.toArray()}:null];
  }));
  return {name:b.name,instances:ids.length,structures:[...new Set(ids.filter(Boolean))],materialType:m.type,maps,normalScale:m.normalScale?.toArray(),aoMapIntensity:m.aoMapIntensity,roughness:m.roughness,metalness:m.metalness,side:m.side,transparent:m.transparent};
 }));
 fs.writeFileSync(path.join(out,'building-batches-'+label+'.json'),JSON.stringify({method:'Existing building batch API; instance counts include spatial pieces. Source identities compare only within this page load, not between runs. This is not a per-frame draw count.',batches:buildingBatchCensus},null,2)+'\n');
 const stands=[];
 // Isolate sorting/visibility CPU cost from driver submission and software-GPU
 // cadence, using the existing paired renders (no extra frame or scene change).
 if(process.env.QA_OCCLUSION && label==='mobile')await page.evaluate(()=>{
  globalThis.__qaTimedRender=()=>{
   const a=__chicago4d,undo=[],timing={mainCallbacks:0,shadowCallbacks:0,mainCallbackMs:0,shadowCallbackMs:0};
   a.scene3d.traverse(o=>{if(!o.isBatchedMesh||!o.customSort)return;
    const prior=o.customSort;
    o.setCustomSort(function(list,camera){const start=performance.now();try{return prior.call(this,list,camera);}finally{
     const kind=camera===a.camera?'main':'shadow';timing[kind+'Callbacks']++;timing[kind+'CallbackMs']+=performance.now()-start;
    }});undo.push(()=>o.setCustomSort(prior));
   });
   const start=performance.now();
   try{a.renderer.render(a.scene3d,a.camera);}finally{timing.renderSubmissionMs=performance.now()-start;for(const fn of undo)fn();}
   return timing;
  };
 });
 // All previously failing poses, plus exterior/roof/interface controls; same local ENU metres.
 const cameras=JSON.parse(fs.readFileSync(new URL('./camera-plan.json',import.meta.url),'utf8')).cameras.map(c=>[c.name,c.position,c.target]);
 for(const [name,pos,target] of cameras.filter(([name])=>!process.env.QA_VIEW||process.env.QA_VIEW.split(',').includes(name))){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);const draws=[];const original=a.renderer.renderBufferDirect;
   a.renderer.renderBufferDirect=function(cam,scene,geometry,material,object,group){
    const before={calls:this.info.render.calls,triangles:this.info.render.triangles};
    const result=original.call(this,cam,scene,geometry,material,object,group);
    const calls=this.info.render.calls-before.calls,triangles=this.info.render.triangles-before.triangles;
    if(calls||triangles){let parents=[];for(let o=object;o;o=o.parent)parents.push(o.name||o.type);
     draws.push({uuid:object.uuid,name:object.name,type:object.type,parents,material:material.name,pass:cam===a.camera?'main':'shadow',calls,triangles,
      structureIds:[...new Set(object.userData.batchIndex||[])],spatialBatch:object.userData.spatialBatch||null});}
    return result;
   };
   try{a.renderer.render(a.scene3d,a.camera);}finally{a.renderer.renderBufferDirect=original;}
   const sums=draws.reduce((s,d)=>({calls:s.calls+d.calls,triangles:s.triangles+d.triangles}),{calls:0,triangles:0});
   const totals={calls:a.renderer.info.render.calls,triangles:a.renderer.info.render.triangles};
   if(sums.calls!==totals.calls||sums.triangles!==totals.triangles)throw Error('Draw profile does not reconcile: '+JSON.stringify({sums,totals}));
   const drawProfile={draws,sums,totals,reconciled:true};
   const modes=new Set();a.scene3d.traverse(o=>{for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.userData.glassMode)modes.add(m.userData.glassMode)});
   const heightSamples=[49,50,53.66,54.2,46,41.1].map(x=>{const q=en([x,2.36,0]);return {x,terrain:a.terrain.surfaceHeight(q[0],q[1])-ground}});
   return {drawProfile,placement:pl,ground,heightSamples,detail:a.detail,glassModes:[...modes],problems:a.problems,stats:a.stats(),camera:p,target:t,cameraPosition:a.camera.position.toArray(),cameraQuaternion:a.camera.quaternion.toArray(),projection:a.camera.projectionMatrix.toArray(),exposure:a.renderer.toneMappingExposure};
  },{pos,target});
  if(!observation.glassModes.includes('dark') || observation.glassModes.some(m=>m!=='dark'))throw Error('Owner dark-glass setting changed: '+JSON.stringify(observation.glassModes));
  await page.screenshot({path:path.join(out,`${label}-${name}.png`)});stands.push({name,...observation});
  if(process.env.QA_DIAG_BOW && name==='bow-leader') {
   const diagnosis=await page.evaluate(async()=>{
    const a=__chicago4d,T=await import('/walk/vendor/three-0.185.1/three.module.js');
    const ray=new T.Raycaster();ray.setFromCamera(new T.Vector2((7.5/390)*2-1,1-(346.5/780)*2),a.camera);
    const hits=ray.intersectObjects(a.buildings.batches,false).slice(0,20).map(h=>{
     const b=h.object,visibleIds=new Set(b._indirectTexture.image.data.slice(0,b._multiDrawCount));
     const box=b.getBoundingBoxAt(b.getGeometryIdAt(h.batchId),new T.Box3()).applyMatrix4(b.getMatrixAt(h.batchId,new T.Matrix4())).applyMatrix4(b.matrixWorld);
     return {batch:b.uuid,instance:h.batchId,face:h.faceIndex,distance:h.distance,point:h.point.toArray(),submitted:visibleIds.has(h.batchId),bounds:[box.min.toArray(),box.max.toArray()],structure:b.userData.batchIndex[h.batchId]};
    });return {hits,camera:a.camera.position.toArray(),cull:a.glessnerOcclusionStats()};
   });
   fs.writeFileSync(path.join(out,'bow-pixel-ray.json'),JSON.stringify(diagnosis,null,2)+'\n');
   for(const subset of ['buildings','railway','none']) {
    const result=await page.evaluate(async subset=>{
     const a=__chicago4d,{createViewOcclusion}=await import('/walk/js/view-occlusion.js');
     globalThis.__qaCull?.dispose();a.setGlessnerOcclusion(false);const batches=[];
     if(subset==='buildings')batches.push(...a.buildings.batches);
     if(subset==='railway')a.railway.group.traverse(o=>{if(o.isBatchedMesh)batches.push(o);});
     globalThis.__qaCull=createViewOcclusion({camera:a.camera,renderer:a.renderer,triangles:a.buildings.viewOccluders,batches});
     a.renderer.render(a.scene3d,a.camera);return {stats:a.stats(),cull:globalThis.__qaCull.stats};
    },subset);
    await page.screenshot({path:path.join(out,`bow-filter-${subset}.png`)});
    fs.writeFileSync(path.join(out,`bow-filter-${subset}.json`),JSON.stringify(result,null,2)+'\n');
   }
   await page.evaluate(()=>{const a=__chicago4d;globalThis.__qaCull.dispose();delete globalThis.__qaCull;a.setGlessnerOcclusion(true);a.renderer.render(a.scene3d,a.camera);});
  }
  if(process.env.QA_OCCLUSION && label==='mobile') {
   if(process.env.QA_REPEAT_FRAME && name==='bow-leader'){
    await page.evaluate(()=>{const a=__chicago4d;a.renderer.render(a.scene3d,a.camera);});
    await page.screenshot({path:path.join(out,`${label}-${name}-repeat-on.png`)});
   }
   const off=await page.evaluate(()=>{const a=__chicago4d;
    const pick=()=>{const p=a.buildings.pickAt(null,a.camera);return p?{id:p.id,point:p.point.toArray(),distance:p.distance}:null;};
    const onPick=pick(),onCull=a.glessnerOcclusionStats();
    a.setGlessnerOcclusion(false);const timing=__qaTimedRender();
    return {onPick,onCull,pick:pick(),stats:a.stats(),cull:a.glessnerOcclusionStats(),timing};});
   await page.screenshot({path:path.join(out,`${label}-${name}-occlusion-off.png`)});
   const restored=await page.evaluate(()=>{const a=__chicago4d;a.setGlessnerOcclusion(true);const timing=__qaTimedRender();
    return {stats:a.stats(),cull:a.glessnerOcclusionStats(),timing};});
   if(JSON.stringify(off.onPick)!==JSON.stringify(off.pick))throw Error('Occlusion changed picking');
   if(restored.stats.drawCalls!==observation.stats.drawCalls||restored.stats.triangles!==observation.stats.triangles)throw Error('Occlusion toggle did not restore counts');
   const confidence=[];
   if(process.env.QA_EVIDENCE_COMPARE && name==='bow-leader')for(const mode of ['evidence','hidden-reconstructed','hidden-inferred']) {
    const on=await page.evaluate(mode=>{const a=__chicago4d;a.confidence.set(false);a.confidence.showAll();
     if(mode==='evidence')a.confidence.set(true);else a.confidence.setHidden(mode.slice(7),true);
     a.setGlessnerOcclusion(true);a.renderer.render(a.scene3d,a.camera);
     return {stats:a.stats(),cull:a.glessnerOcclusionStats()};},mode);
    await page.screenshot({path:path.join(out,`${label}-${name}-${mode}-on.png`)});
    const off=await page.evaluate(()=>{const a=__chicago4d;a.setGlessnerOcclusion(false);a.renderer.render(a.scene3d,a.camera);
     return {stats:a.stats(),cull:a.glessnerOcclusionStats()};});
    await page.screenshot({path:path.join(out,`${label}-${name}-${mode}-off.png`)});
    confidence.push({mode,on,off});
   }
   const finalRestore=await page.evaluate(()=>{const a=__chicago4d;a.confidence.set(false);a.confidence.showAll();a.setGlessnerOcclusion(true);a.renderer.render(a.scene3d,a.camera);return a.stats();});
   if(finalRestore.triangles!==observation.stats.triangles)throw Error('Evidence restore lost geometry');
   fs.writeFileSync(path.join(out,`${label}-${name}-occlusion.json`),JSON.stringify({off,restored,confidence,finalRestore},null,2)+'\n');
  }
  // A workspace interruption must not discard measurements for saved images.
  // This is partial evidence only; the completed result and assertions below
  // remain the authority for a successful run.
  fs.writeFileSync(path.join(out,`capture-checkpoint-${label}.json`),JSON.stringify({partial:true,label,viewport,detail,boot,errors,bad,assets,stands},null,2)+'\n');
  console.log(label+' captured '+name);

 }
 if(process.env.QA_LIBERTY){
  await page.evaluate(()=>__chicago4d.pick('glessner_house'));
  await page.waitForFunction(()=>document.querySelector('#popup [data-pop-tab="liberties"]'));
  await page.evaluate(()=>document.querySelector('#popup [data-pop-tab="liberties"]').click());
  await page.waitForFunction(id=>[...document.querySelectorAll('#popup details.lib')].some(e=>e.dataset.sourceEntity===id),process.env.QA_LIBERTY);
  const liberty=await page.evaluate(id=>{
   const e=[...document.querySelectorAll('#popup details.lib')].find(e=>e.dataset.sourceEntity===id);
   e.open=true;e.scrollIntoView({block:'center'});
   return {id:e.dataset.sourceEntity,text:e.textContent.trim(),shown:!e.closest('[data-pop-pane]').hidden};
  },process.env.QA_LIBERTY);
  if(!liberty.shown||!liberty.text.includes('reconstructed')||!liberty.text.includes('Rainwater fitting stock'))throw Error('Rainwater liberty is absent or lacks its reconstruction scope');
  fs.writeFileSync(path.join(out,`${label}-liberty.json`),JSON.stringify(liberty,null,2)+'\n');
  await page.screenshot({path:path.join(out,`${label}-liberty.png`)});
 }
 if(label==='mobile' && process.env.QA_IMAGES){
  await page.evaluate(()=>__chicago4d.pick('glessner_house'));
  await page.waitForFunction(()=>document.querySelector('#popup [data-pop-tab="images"]'));
  await page.evaluate(()=>document.querySelector('#popup [data-pop-tab="images"]').click());
  await page.waitForFunction(()=>!document.querySelector('#popup [data-pop-pane="images"]')?.textContent.includes('LOADING IMAGE INDEX'));
  const tiles=page.locator('#popup [data-pop-pane="images"] .pop-pic-tile');
  for(let i=0;i<await tiles.count();i++){
   await tiles.nth(i).scrollIntoViewIfNeeded();
   await page.waitForFunction(i=>{const img=document.querySelectorAll('#popup [data-pop-pane="images"] .pop-pic-tile')[i]?.querySelector('img');return img?.complete&&img.naturalWidth>0;},i,{timeout:60000});
  }
  if(await tiles.count())await tiles.first().scrollIntoViewIfNeeded();
  const pictures=await page.evaluate(()=>{const p=document.querySelector('#popup [data-pop-pane="images"]');return {shown:!p.hidden,tiles:[...p.querySelectorAll('.pop-pic-tile')].map(t=>({text:t.textContent.trim(),credit:t.querySelector('.pop-pic-tile-credit')?.textContent.trim(),loaded:!!t.querySelector('img')?.naturalWidth})),links:[...p.querySelectorAll('.pop-pic-list li')].map(t=>t.textContent.trim())}});
  if(!pictures.shown||!pictures.tiles.length||pictures.tiles.some(t=>!t.credit||!t.loaded))throw Error('Images tab lacks credited pictures');
  fs.writeFileSync(path.join(out,'mobile-images.json'),JSON.stringify(pictures,null,2)+'\n');
  await page.screenshot({path:path.join(out,'mobile-images.png')});
 }
 if(process.env.QA_SEASON_ROUNDTRIP && label==='mobile'){
  await page.evaluate(required=>globalThis.__qaRequireSeasonFallback=required,!!process.env.QA_REQUIRE_SEASON_FALLBACK);
  const seasons=await page.evaluate(async()=>{
   const a=__chicago4d,rows=[];
   const capture=()=>{a.renderer.render(a.scene3d,a.camera);return {stats:a.stats(),cull:a.glessnerOcclusionStats(),image:a.renderer.domElement.toDataURL('image/png')};};
   a.setGlessnerOcclusion(true);const before=capture();
   for(const season of ['winter','summer']){
    await a.season.set(season);
    a.setGlessnerOcclusion(true);capture();const on=capture(),repeatOn=capture();
    a.setGlessnerOcclusion(false);const off=capture(),repeatOff=capture();
    a.setGlessnerOcclusion(true);const restoredOn=capture();
    if(season==='winter' && globalThis.__qaRequireSeasonFallback && (on.cull.active || on.cull.culled || on.stats.drawCalls!==off.stats.drawCalls || on.stats.triangles!==off.stats.triangles))throw Error('Winter failed to retain the complete draw list');
    if(season==='summer' && !on.cull.active)throw Error('Summer filter was not restored');
    rows.push({season,on,repeatOn,off,repeatOff,restoredOn});console.log('QA_MOTION season '+season+' paired');
   }
   a.setGlessnerOcclusion(true);const restored=capture();
   if(restored.stats.drawCalls!==before.stats.drawCalls || restored.stats.triangles!==before.stats.triangles)throw Error('Summer draw counts changed after season round trip');
   if(!restored.stats.withinBudget)throw Error('Restored summer exceeds unchanged Light budget');
   return {before,rows,restored};
  });
  const save=(name,row)=>{fs.writeFileSync(path.join(out,`mobile-season-${name}.png`),Buffer.from(row.image.split(',')[1],'base64'));delete row.image;};
  save('before',seasons.before);for(const row of seasons.rows){save(row.season+'-on',row.on);save(row.season+'-off',row.off);for(const key of ['repeatOn','repeatOff','restoredOn'])save(row.season+'-'+key,row[key]);}save('restored',seasons.restored);
  fs.writeFileSync(path.join(out,'mobile-season-roundtrip.json'),JSON.stringify(seasons,null,2)+'\n');
 }
 const textureMemory=await page.evaluate(()=>{
  const a=__chicago4d,seen=new Map(),unpriced=[];
  const inspect=t=>{
   if(!t?.isTexture)return;
   const key=JSON.stringify([t.source?.uuid,t.wrapS,t.wrapT,t.minFilter,t.magFilter,t.anisotropy,t.internalFormat,t.format,t.type,t.generateMipmaps,t.premultiplyAlpha,t.flipY,t.unpackAlignment,t.colorSpace]);
   if(seen.has(key))return;
   const imgs=Array.isArray(t.image)?t.image:[t.image];
   const channels={1028:1,1023:4,1022:3,1021:1,1029:1,1030:2,1031:2,1033:4}[t.format];
   const component={1009:1,1010:1,1011:2,1012:2,1013:4,1014:4,1015:4,1016:2}[t.type];
   let bytes=0;
   for(const im of imgs){
    if(!channels||!component||!im?.width||!im?.height||t.isCompressedTexture){unpriced.push({name:t.name,format:t.format,type:t.type,compressed:!!t.isCompressedTexture});seen.set(key,{unpriced:true});return;}
    let w=im.width,h=im.height;do{bytes+=w*h*channels*component;if(!t.generateMipmaps||(w===1&&h===1))break;w=Math.max(1,Math.floor(w/2));h=Math.max(1,Math.floor(h/2));}while(true);
   }
   seen.set(key,{name:t.name,width:imgs[0]?.width,height:imgs[0]?.height,faces:imgs.length,bytes});
  };
  a.scene3d.traverse(o=>{for(const m of(Array.isArray(o.material)?o.material:[o.material]))if(m)for(const v of Object.values(m))inspect(v);});inspect(a.scene3d.environment);inspect(a.scene3d.background);
  return {method:'Unique scene texture source/sampler bindings; estimated uncompressed texel storage including generated mip levels. Not measured GPU allocation; excludes render targets, driver alignment and internal PMREM copies. Unsupported formats listed explicitly.',estimatedBytes:[...seen.values()].reduce((s,x)=>s+(x.bytes||0),0),bindings:[...seen.values()],unpriced,rendererMemory:{...a.renderer.info.memory}};
 });
 fs.writeFileSync(path.join(out,'texture-memory-'+label+'.json'),JSON.stringify(textureMemory,null,2)+'\n');
 let motion=null;
 if(process.env.QA_MOTION){
  // Existing public step() runs the application's whole tick, including moving
  // layers and shadows. Record RAF cadence and wall time as well as the
  // JavaScript step/finish duration; the latter alone did not track GPU cadence.
  // This is controlled traversal timing, not a phone hardware-FPS promise.
  const motionName=process.env.QA_MOTION_VIEW || (label==='balanced'?'owner-angle':'north-court');
  const motionStand=stands.find(s=>s.name===motionName);
  if(!motionStand)throw Error('Required fixed motion stand absent: '+motionName);
  motion=await page.evaluate(async stand=>{
   const a=__chicago4d,gl=a.renderer.getContext(),samples=[];
   const wallStart=performance.now();let priorCallback=null;
   a.camera.position.fromArray(stand.position);a.camera.quaternion.fromArray(stand.quaternion);
   const origin=a.camera.position.clone();
   const forward=origin.clone().set(0,0,-1).applyQuaternion(a.camera.quaternion);
   const yaw=Math.atan2(forward.x,-forward.z)*180/Math.PI;
   const pitch=Math.atan2(forward.y,Math.hypot(forward.x,forward.z))*180/Math.PI;
   const saved={stand:stand.name,position:a.camera.position.toArray(),quaternion:a.camera.quaternion.toArray()};
   a.setFloraSpread(true);a.setAnimationHold(false);
   try {
   for(let i=0;i<33;i++){
    await new Promise(requestAnimationFrame);
    const callbackAt=performance.now(), cadenceMs=priorCallback===null?null:callbackAt-priorCallback;priorCallback=callbackAt;
    const f=i/32, p=origin.clone();p.x+=Math.sin(f*Math.PI*2)*.5;
    a.walker.teleport({local_e:p.x,local_n:-p.z,altitude_m:p.y-a.terrain.surfaceHeight(p.x,-p.z),yaw_deg:yaw+Math.sin(f*Math.PI*2)*6,pitch_deg:pitch});
    const start=performance.now();a.step();gl.finish();const elapsedMs=performance.now()-start;
    if(i>=3)samples.push({frame:i-3,elapsedMs,cadenceMs,callbackAt,camera:a.camera.position.toArray(),quaternion:a.camera.quaternion.toArray(),stats:a.stats()});
    if(i%5===0)console.log('QA_MOTION '+i+'/33 elapsed '+Math.round(performance.now()-wallStart)+'ms; measured max triangles '+Math.max(0,...samples.map(s=>s.stats.triangles))+'; budgets '+samples.every(s=>s.stats.withinBudget));
   }
   } finally { a.setAnimationHold(true);a.setFloraSpread(false); }
   const times=samples.map(x=>x.elapsedMs).sort((a,b)=>a-b);
   return {wallElapsedMs:performance.now()-wallStart,method:'30 moving application steps at a named fixed stand after 3 warmups, 1m lateral/12degree pan; RAF scheduled, live flora frame budget, performance.now around step+gl.finish. Step cost excludes RAF/compositor wait, which is recorded separately as cadence and wall elapsed. Declared renderer only; no hardware-FPS claim.',saved,samples,minMs:times[0],medianMs:times[Math.floor(times.length/2)],p95Ms:times[Math.ceil(.95*times.length)-1],maxMs:times.at(-1)};
  },{name:motionName,position:motionStand.cameraPosition,quaternion:motionStand.cameraQuaternion});
  fs.writeFileSync(path.join(out,'motion-'+label+'.json'),JSON.stringify(motion,null,2)+'\n');
 }
 let budgetRoundTrip=null;
 if(process.env.QA_CHECK_BUDGET_LEVELS && label==='desktop'){
  budgetRoundTrip=await page.evaluate(async()=>{
   const a=__chicago4d,full={...a.stats().budget};
   const position=a.camera.position.clone(),quaternion=a.camera.quaternion.clone();
   const projection=a.camera.projectionMatrix.clone();
   const capture=()=>{
    a.camera.position.copy(position);a.camera.quaternion.copy(quaternion);
    a.camera.projectionMatrix.copy(projection);a.camera.projectionMatrixInverse.copy(projection).invert();
    a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);
    a.renderer.render(a.scene3d,a.camera);
    return {stats:a.stats(),image:a.renderer.domElement.toDataURL('image/png'),
     batches:a.buildings.batches.map(b=>({instances:b.instanceCount,material:b.material.type,transparent:b.material.transparent,glass:b.material.userData.glassMode||null}))};
   };
   const settleTrees=async level=>{const start=performance.now();while(a.streetTrees.stats.detail!==level || (a.streetTrees.stats.mode!=='hidden' && a.streetTrees.stats.drawCalls!==(level==='full'?2:1))){if(performance.now()-start>60000)throw Error('Detail tree transition failed to settle');await new Promise(r=>setTimeout(r,50));}};
   const before=capture();
   await a.setDetail('light');await settleTrees('light');const light={...a.stats().budget},reduced=capture();
   await a.setDetail('full');await settleTrees('full');const restored={...a.stats().budget},after=capture();
   if(full.drawCalls!==360||full.triangles!==4600000||light.drawCalls!==330||light.triangles!==1270000||JSON.stringify(full)!==JSON.stringify(restored))throw Error('Full inspection allowance leaked across the detail setting');
   if(JSON.stringify(before.batches)!==JSON.stringify(after.batches))throw Error('Full material/instance census changed after detail round trip');
   return {full,light,restored,before,reduced,after};
  });
  for(const name of ['before','reduced','after']){
   fs.writeFileSync(path.join(out,`desktop-detail-roundtrip-${name}.png`),Buffer.from(budgetRoundTrip[name].image.split(',')[1],'base64'));
   delete budgetRoundTrip[name].image;
  }
  fs.writeFileSync(path.join(out,'desktop-detail-roundtrip.json'),JSON.stringify(budgetRoundTrip,null,2)+'\n');
 }
 results.push({label,viewport,detail,boot,roundTrip,budgetRoundTrip,motion,textureMemory,buildingBatchCensus,errors,bad,assets,requestedPaths:[...requestedPaths].sort(),stands});
 fs.writeFileSync(process.env.QA_PROGRESS_PATH||path.join(out,'browser-validation-progress.json'),JSON.stringify({partial:true,results},null,2)+'\n');
 // T-2219: measured before 3,890,920; with T-2473 trees 4,274,524; Full-only 4.6M.
 if(label==='desktop' && stands.some(x=>x.stats.budget.triangles!==4600000))throw Error('Selected Full inspection allowance drifted from measured 4.6M ceiling');
 if(errors.length||bad.length||stands.some(x=>x.problems.length||!x.stats.withinBudget)||motion?.samples.some(x=>!x.stats.withinBudget))throw Error(JSON.stringify({errors,bad,stands:stands.map(s=>({name:s.name,stats:s.stats,problems:s.problems}))}));
 if(!assets.some(a=>a.url.endsWith(detail==='full'?'__as_built_1887.glb':'.light.glb')))throw Error('Expected canonical detail asset did not load');
 await context.close();console.log(label+' actual published 1904 app loaded; budget results retained per stand');
}
}finally{fs.writeFileSync(path.join(out,process.env.QA_VIEWPORT ? 'browser-validation-'+process.env.QA_VIEWPORT+'.json' : 'browser-validation.json'),JSON.stringify({method:'Actual published /1904/ app; normal Full/Light boot at 1280x800/390x780 (Balanced separately). Animation held with the existing harness API for frozen camera comparisons, then released for moving-frame timing. RenderBufferDirect instrumentation reconciles actual main/shadow draw counts, then restores the method. Software renderer and boot phases declared; still captures are not frame-time measurements.',results},null,2)+'\n');fs.rmSync(process.env.QA_PROGRESS_PATH||path.join(out,'browser-validation-progress.json'),{force:true});await browser.close();server.close();}
