// T-3388: the 1904 placeholder buildings read as believable stand-ins, shot in the published /1904/ app at the
// owner's own views (2026-11-05: free-standing pink tower slabs behind 244-250 E 18th Street) and at two drafted
// houses whose storeyed back pieces stood clear of the house (1931 Indiana, 2124 Calumet). The harness is
// tools/qa_context_clear_t3038.mjs's: scene-local metres (east, north, height above the ground there).
//   node tools/qa_stand_ins_t3388.mjs                                    (after tools/publish.sh)
//   QA_TAG=before QA_BEFORE_DIR=<dir with context.js, 1904.json and old draft GLBs> node tools/qa_stand_ins_t3388.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/believable-stand-ins-3388'),TAG=process.env.QA_TAG||'after';
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
// [name, eye, target]: the owner's two views on 18th Street (heading NW, 40 ft and 18 ft up), then the drafts
const STANDS=[
 ['owner-244-e18th-40ft',[1334,-3204,12],[1290,-3143,4]],
 ['owner-250-e18th-18ft',[1338,-3206,5.5],[1300,-3150,6]],
 ['1931-indiana-from-the-alley',[1345,-3470,16],[1300,-3440,4]],
 ['2124-calumet-from-the-alley',[1470,-3720,16],[1515,-3690,4]],
];
const ONLY=(process.env.QA_ONLY||'').split(',').filter(Boolean);
const RUN=STANDS.filter(([n])=>!ONLY.length||ONLY.includes(n));
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const B=process.env.QA_BEFORE_DIR;
 if(B){
  await page.route(/\/data\/context\/1904\.json(\?.*)?$/,r=>r.fulfill({status:200,contentType:'application/json',body:fs.readFileSync(path.join(B,'1904.json'))}));
  await page.route(/\/js\/context\.js(\?.*)?$/,r=>r.fulfill({status:200,contentType:'text/javascript',body:fs.readFileSync(path.join(B,'context.js'))}));
  await page.route(/\/([a-z0-9_]+__draft_1904\.glb)(\?.*)?$/,r=>{const f=path.join(B,path.basename(new URL(r.request().url()).pathname));return fs.existsSync(f)?r.fulfill({status:200,contentType:'model/gltf-binary',body:fs.readFileSync(f)}):r.continue();});
 }
 const errors=[],bad=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());});
 const t0=Date.now();
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 const loadMs=Date.now()-t0;
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id,context:__chicago4d.contextCity?.census}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const stands=[];
 for(const [name,pos,target] of RUN){
  const observation=await page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);
   return {detail:a.detail,problems:a.problems,camera:p.map(v=>Math.round(v*100)/100),target:t.map(v=>Math.round(v*100)/100),context:a.contextCity?.census};
  },{pos,target});
  await page.screenshot({path:path.join(out,`${TAG}-${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 results.push({label,viewport,detail,load_ms_to_ready:loadMs,boot,errors,bad,stands});
 if(errors.length)throw Error(JSON.stringify(errors));
 await context.close();console.log(`${TAG} ${label}: ${stands.length} stand(s), load ${loadMs} ms, ${bad.length} failed request(s), context ${JSON.stringify(boot.context)}`);
}
}catch(e){failed=e;}
finally{fs.writeFileSync(path.join(out,'browser-validation-'+TAG+(process.env.QA_VIEWPORT?'-'+process.env.QA_VIEWPORT:'')+'.json'),JSON.stringify({method:'Published /1904/ app, normal boot (TAG '+TAG+(process.env.QA_BEFORE_DIR?', context.js, data/context/1904.json and the changed draft GLBs routed to origin/dev\'s':'')+'); desktop 1280x800 at full detail, mobile 390x780 at light; animation paused after readiness.',results},null,2)+'\n');await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
