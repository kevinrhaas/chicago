// T-3272: what fills the desktop full-detail stand down the 16th-18th west alley, looking south
// from 1616 Prairie's rear (T-1932's 'alley-from-north', the only one of its stands over budget).
// The published /1904/ app, T-1932's harness and stand verbatim; then each named top-level group
// hidden in turn, and each structure in the `structures` group, read by renderer.info.
//   node tools/measure_alley_t3272.mjs [--json out.json]     (after tools/publish.sh)
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,'../../site/4d');
const jsonAt=process.argv.indexOf('--json'),jsonOut=jsonAt>0?process.argv[jsonAt+1]:null;
const DETAIL=process.env.QA_DETAIL||'full';
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.wasm':'application/wasm','.ktx2':'image/ktx2'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const STANDS=(process.env.QA_STANDS||'alley-from-north').split(',');
const ALL={'alley-from-south':[[1331.2,-3040,1.7],[1334,-3015,4]],'alley-from-north':[[1331.2,-2992,1.7],[1334,-3015,4]],'yard-face':[[1360,-3005,1.7],[1338,-3015,4]],'air':[[1375,-3050,45],[1337,-3015,0]]};
const out={method:'',stands:[]};
try{
 const context=await browser.newContext({viewport:{width:1280,height:800},deviceScaleFactor:1});
 const page=await context.newPage();page.setDefaultTimeout(240000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:240000,polling:500});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:240000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},DETAIL);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 const t0=Date.now(),log=(m)=>console.log(`[${((Date.now()-t0)/1000).toFixed(0)}s] ${m}`);
 for(const name of STANDS){
  const [pos,target]=ALL[name];
  // one reading per evaluate, so a slow software-GL frame cannot take the whole sweep with it
  await page.evaluate(({pos,target})=>{const a=__chicago4d;
   const p=[pos[0],pos[1],a.terrain.surfaceHeight(pos[0],pos[1])+pos[2]],t=[target[0],target[1],a.terrain.surfaceHeight(target[0],target[1])+target[2]];
   a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:pos[2],yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   window.__t3272={read(){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);const s=a.stats();return {calls:s.drawCalls,tris:s.triangles};}};
  },{pos,target});
  const read=()=>page.evaluate(()=>__t3272.read());
  const base=await read();const st=await page.evaluate(()=>({budget:__chicago4d.stats().budget,detail:__chicago4d.detail}));
  log(`${name} (${st.detail}): ${base.calls} draws / ${base.tris} tris vs ${st.budget.drawCalls} / ${st.budget.triangles}`);
  const held=(sel)=>page.evaluate(sel=>{const a=__chicago4d;const list=sel==='top'?a.scene3d.children.filter(g=>g.name&&g.visible):(a.scene3d.getObjectByName('structures')?.children??[]).filter(c=>c.visible);
   return list.map((g,i)=>{let meshes=0,held=0;g.traverse(o=>{if(!o.isMesh)return;meshes++;const geo=o.geometry;const n=geo?.index?geo.index.count:(geo?.attributes?.position?.count??0);held+=Math.floor(n/3);});return {i,name:g.name||g.userData?.id||g.type,type:g.type,meshes,heldTris:held};});},sel);
  const toggle=(sel,i,v)=>page.evaluate(({sel,i,v})=>{const a=__chicago4d;const list=sel==='top'?a.scene3d.children.filter(g=>g.name&&(g.visible||g.userData.__t3272)):(a.scene3d.getObjectByName('structures')?.children??[]).filter(c=>c.visible||c.userData.__t3272);const g=list[i];g.userData.__t3272=!v;g.visible=v;},{sel,i,v});
  const groups=await held('top');
  for(const g of groups){await toggle('top',g.i,false);const h=await read();await toggle('top',g.i,true);g.calls=base.calls-h.calls;g.tris=base.tris-h.tris;log(`  group ${g.name.padEnd(22)} ${String(g.calls).padStart(6)} draws ${String(g.tris).padStart(9)} tris (held ${g.heldTris}, ${g.meshes} meshes)`);}
  const kids=(await held('structures')).sort((x,y)=>y.heldTris-x.heldTris);
  log(`  structures: ${kids.length} children; sweeping the ${Math.min(kids.length,+(process.env.QA_KIDS||12))} heaviest held`);
  const swept=[];
  for(const k of kids.slice(0,+(process.env.QA_KIDS||12))){await toggle('structures',k.i,false);const h=await read();await toggle('structures',k.i,true);k.calls=base.calls-h.calls;k.tris=base.tris-h.tris;swept.push(k);log(`    ${String(k.name).slice(0,44).padEnd(44)} ${String(k.calls).padStart(6)} ${String(k.tris).padStart(9)} (held ${k.heldTris}, ${k.meshes} meshes, ${k.type})`);}
  const sun=await page.evaluate(()=>{const a=__chicago4d;a.renderer.shadowMap.enabled=false;const r=__t3272.read();a.renderer.shadowMap.enabled=true;return r;});
  const again=await read();
  log(`  sun ${base.calls-sun.calls} draws / ${base.tris-sun.tris} tris; residual ${again.calls-base.calls}/${again.tris-base.tris}`);
  out.stands.push({name,detail:st.detail,budget:st.budget,base,sun:{calls:base.calls-sun.calls,tris:base.tris-sun.tris},residual:{calls:again.calls-base.calls,tris:again.tris-base.tris},groups,structures:swept});
 }
 out.errors=errors;console.log('errors',errors.length);
}finally{if(jsonOut)fs.writeFileSync(jsonOut,JSON.stringify(out,null,1)+'\n');await browser.close();server.close();}
