// T-2365: K14 compared beside a newer neighbour. 1708 Prairie, an empty lot on the 1886 Robinson plate and
// standing finished in the summer-1901 construction photograph, weathered by the K14 condition kit at that
// later bound (3 years in 1904, a = 0.075), read in the actual published /1904/ app beside 1808 Prairie
// (built 1886, a = 0.45, T-2358) in the same session, so under the same sun, sky and exposure. The T-2364
// script with two houses in one page: each house's stands are fixed in its own footprint frame (u east,
// v north, metres above the ground at its origin), front and oblique, and every material that carries the
// kit's _TONE channel is read off both tiers of both GLBs.
//   node tools/qa_k14_t2365.mjs                 (after tools/publish.sh)
//   QA_VIEWPORT=mobile node tools/qa_k14_t2365.mjs
//   QA_HOUSES=1708 ...            one house's stands only
//   QA_BEFORE=path/to/web.glb ... 1708's stands with that derivative served in place of the shipped one
//                                  (1708 as it stood before, on K03's fixed full-age masks), as before-*.jpg
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d'),out=path.join(root,'docs/RESEARCH/k14-1708-newer-2365');
fs.mkdirSync(out,{recursive:true});
const HOUSES={
 1708:{id:'house_1708_prairie',phase:'as_mapped_1904',
  // the front block's face is u = 12.8, v 0-7.5, its canted bay before the south part; cornice ~13.5 m
  stands:[['front',[37,3.75,1.7],[12.8,3.75,6]],['oblique',[29,-12,1.7],[9,3.5,6]]]},
 1808:{id:'keith_house_1808_prairie',phase:'as_built_1886',
  // T-2358's stands moved to its refined footprint: the stone front is u = 34.7 now
  stands:[['front',[60.7,5.2,1.7],[34.7,5.2,6]],['oblique',[50.7,-14,1.7],[29.7,3,6]]]},
};
const ID=HOUSES[1708].id,GLB=`${ID}__as_mapped_1904.glb`;
const ONLY_HOUSES=(process.env.QA_HOUSES?.split(',')||Object.keys(HOUSES)).filter(h=>!process.env.QA_BEFORE||h==='1708');
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml'};
const BEFORE=process.env.QA_BEFORE?path.resolve(process.env.QA_BEFORE):null,TAG=BEFORE?'before-':'';
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));if(BEFORE&&p.endsWith(GLB))p=BEFORE;try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE || undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const {parseGlb,readAccessor}=await import(path.join(root,'tools/k01_contract.mjs'));
const {MeshoptDecoder}=await import(path.join(root,'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js'));
await MeshoptDecoder.ready;
// each weathering slot's _TONE: its least value, its mean and how many vertices carry it
async function tonesIn(file){
 const {json,bin}=parseGlb(fs.readFileSync(file));
 const ctx={json,bin,views:new Map(),meshopt:MeshoptDecoder};
 const out={};
 for(const mesh of json.meshes)for(const prim of mesh.primitives){
  const name=json.materials[prim.material]?.name;if(prim.attributes._TONE===undefined)continue;
  const t=readAccessor(ctx,prim.attributes._TONE);let lo=1,sum=0;for(const x of t){lo=Math.min(lo,x);sum+=x;}
  const o=out[name]||={vertices:0,min:1,sum:0};o.vertices+=t.length;o.min=Math.min(o.min,+lo.toFixed(3));o.sum+=sum;}
 for(const o of Object.values(out)){o.mean=+(o.sum/o.vertices).toFixed(4);delete o.sum;}
 return out;
}
const tierTones={};
for(const h of ONLY_HOUSES){const g=`${HOUSES[h].id}__${HOUSES[h].phase}.glb`;
 tierTones[h]={full:await tonesIn(path.join(root,`assets/gltf/${g}`)),web:await tonesIn(h==='1708'&&BEFORE||path.join(root,`assets/web/${g}`)),
  bytes:{full:fs.statSync(path.join(root,`assets/gltf/${g}`)).size,web:fs.statSync(h==='1708'&&BEFORE||path.join(root,`assets/web/${g}`)).size}};}
console.log('tones by tier '+JSON.stringify(tierTones));
if(!BEFORE&&tierTones[1708]&&!Object.keys(tierTones[1708].web).length)throw Error('no material carries a tone in 1708\'s web tier');
const results=[];let failed=null;
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT && process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[],bad=[],assets=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',async r=>{if(r.status()>=400)bad.push(r.url()+':'+r.status());if(r.url().endsWith('.glb')&&ONLY_HOUSES.some(h=>r.url().includes(HOUSES[h].id)))assets.push({url:r.url().replace(/^.*\/data\//,'data/'),status:r.status(),bytes:Number(r.headers()['content-length']||0)})});
 const t0=Date.now();
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 const loadMs=Date.now()-t0;
 const boot=await page.evaluate(()=>({ready:__chicago4d.ready,error:__chicago4d.error,scene:__chicago4d.scene?.id}));
 if(!boot.ready||boot.scene!=='1904')throw Error(JSON.stringify(boot));
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 for(const h of ONLY_HOUSES){const placed=await page.evaluate(id=>Boolean(__chicago4d.registry.get(id)?.sidecar?.placement),HOUSES[h].id);
 if(!placed)throw Error(`${HOUSES[h].id} is not in the 1904 registry`);}
 const stands=[];
 const only=process.env.QA_STANDS?.split(',');
 for(const h of ONLY_HOUSES)for(const [stand,pos,target] of HOUSES[h].stands.filter(([n])=>!only||only.includes(n))){const name=`${h}-${stand}`,id=HOUSES[h].id;
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
  },{pos,target,id});
  await page.screenshot({path:path.join(out,`${TAG}${label}-${name}.jpg`),type:'jpeg',quality:82});stands.push({name,...observation});
 }
 const row={label,viewport,detail,load_ms_to_ready:loadMs,boot,errors,bad,assets,stands,tones:tierTones,before:BEFORE?path.relative(root,BEFORE):null};
 results.push(row);
 if(errors.length||bad.length||stands.some(x=>x.problems.some(p=>!/does not block scene release/.test(p))||x.name.startsWith("1708")&&!x.stats.withinBudget))throw Error(JSON.stringify(row));
 for(const h of ONLY_HOUSES)if(!assets.some(a=>a.url.includes(HOUSES[h].id)&&a.status<400))throw Error(`${HOUSES[h].id}'s GLB never loaded`);
 await context.close();console.log(label+' actual published 1904 app, 1708 by K14 beside 1808'+(BEFORE?' (BEFORE)':'')+': PASS');
}
}catch(e){failed=e;}
finally{
 const method='Actual published /1904/ app, normal boot; desktop 1280x800 at full detail, mobile 390x780 at light. Animation paused after readiness so the stands are deterministic; frame_ms_median is 5 renders each waited on with a one-pixel read, on this machine\'s software GL (a relative reading, not a device claim).';
 for(const row of results){
  const file=path.join(out,`${TAG}browser-validation-${row.label}.json`);
  let prev=null;try{prev=JSON.parse(fs.readFileSync(file,'utf8')).results?.[0]}catch{}
  if(prev&&(process.env.QA_STANDS||process.env.QA_HOUSES)){const keep=prev.stands.filter(x=>!row.stands.some(y=>y.name===x.name));row.stands=[...keep,...row.stands];row.tones={...prev.tones,...row.tones};}
  fs.writeFileSync(file,JSON.stringify({method,results:[row]},null,2)+'\n');
 }
 await browser.close();server.close();}
if(failed){console.error(String(failed).slice(0,4000));process.exit(1);}
