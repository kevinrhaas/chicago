// Glessner window surrounds and the Prairie front walk's street end: fixed close stands
// on the published /1904/ app, desktop `full` and phone `light`. Local GLB metres
// (x east, y north, z up) from the house's own placement, as qa_glessner_stone.mjs.
//   QA_OUT=<dir> [QA_VIEWPORT=desktop|mobile] [QA_VIEW=name] node tools/qa_glessner_window_surrounds.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(path.join(root,'tools/qa.mjs'));
const {chromium}=require('playwright');
const site=path.resolve(root,process.env.QA_SITE||'../../site/4d'),out=process.env.QA_OUT||path.join(root,'docs/RESEARCH/glessner-window-surrounds/after');
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.svg':'image/svg+xml','.wasm':'application/wasm','.ktx2':'image/ktx2'};
const server=http.createServer((req,res)=>{let p=path.join(site,decodeURIComponent(req.url.split('?')[0]));try{if(fs.statSync(p).isDirectory())p=path.join(p,'index.html');res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res)}catch{res.writeHead(404);res.end('missing')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({args:['--no-sandbox','--enable-unsafe-swiftshader']});
const CAMERAS=[
 // the alley (west) stable wall: the owner's stand under the south broad light, and square on
 ['alley-broad-light-from-below',[-3.2,12.6,1.6],[0,15.3,3.6]],
 ['alley-wall-square',[-9,14.5,3.2],[0,14.5,4.6]],
 ['alley-rear-lights',[-5.5,4.5,2.0],[0,8.2,3.3]],
 ['alley-gable-slits',[-6,15.5,4],[0,17.9,7.2]],
 // 18th Street (north): the stable's two windows beside the loft door, and the house's ground floor
 ['north-stable-windows',[6,27.5,4.5],[6,22.6,6.3]],
 ['north-house-windows',[30,27,1.7],[30,22.6,3.7]],
 // Prairie Avenue (east): the porte's first-floor lights and the front walk's street end
 ['east-porte-lights',[55,4,2.4],[49.2,2.4,4.4]],
 ['front-walk-street-end',[56.2,9.6,1.7],[53.8,12.6,0]],
 ['front-walk-from-walk',[58.5,12.5,1.7],[53.4,12.5,0.1]],
];
fs.mkdirSync(out,{recursive:true});
try{
for(const [label,viewport,detail] of [['desktop',{width:1280,height:800},'full'],['mobile',{width:390,height:780},'light']]){
 if(process.env.QA_VIEWPORT&&process.env.QA_VIEWPORT!==label)continue;
 const context=await browser.newContext({viewport,deviceScaleFactor:1,isMobile:label==='mobile',hasTouch:label==='mobile'});
 const page=await context.newPage();page.setDefaultTimeout(300000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/1904/`,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__chicago4d?.ready||window.__chicago4d?.error,null,{timeout:300000,polling:1000});
 await page.waitForFunction(()=>window.__chicago4d?.welcome.state==='welcome',null,{timeout:300000,polling:1000});
 await page.evaluate(async detail=>{const a=__chicago4d;if(!a.welcome.enter('spawn'))throw Error('welcome entry failed');document.exitPointerLock?.();document.getElementById('control-help-gotit')?.click();a.renderer.setAnimationLoop(null);await a.setDetail(detail);a.step();},detail);
 await page.waitForFunction(()=>document.getElementById('gate').hidden);
 for(const [name,pos,target] of CAMERAS.filter(([n])=>!process.env.QA_VIEW||process.env.QA_VIEW.split(',').includes(n))){
  await page.evaluate(({pos,target})=>{const a=__chicago4d,pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
   const ground=a.terrain.surfaceHeight(pl.local_e,pl.local_n);
   const en=([x,y,z])=>[pl.local_e+x*Math.cos(th)+y*Math.sin(th),pl.local_n-x*Math.sin(th)+y*Math.cos(th),ground+z];
   const p=en(pos),t=en(target);a.setFly(true);a.walker.teleport({local_e:p[0],local_n:p[1],altitude_m:p[2]-a.terrain.surfaceHeight(p[0],p[1]),yaw_deg:Math.atan2(t[0]-p[0],t[1]-p[1])*180/Math.PI,pitch_deg:Math.atan2(t[2]-p[2],Math.hypot(t[0]-p[0],t[1]-p[1]))*180/Math.PI});a.step();
   for(let k=0;k<2;k++){a.camera.position.set(p[0],p[2],-p[1]);a.camera.lookAt(t[0],t[2],-t[1]);a.camera.updateMatrixWorld();a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);}
  },{pos,target});
  await page.screenshot({path:path.join(out,`${label}-${name}.jpg`),type:'jpeg',quality:85});console.log(label,name);
 }
 // The front walk's street end: the top of whatever is drawn at each point, cast straight
 // down, against the house's own walk height (local z, metres over the house's ground).
 const probe=await page.evaluate(async()=>{const a=__chicago4d,THREE=await import('three');const pl=a.registry.get('glessner_house').sidecar.placement,th=pl.rotation_deg*Math.PI/180;
  const m=a.buildings?.matrixOf?.('glessner_house');const houseY=m?m.elements[13]:a.terrain.surfaceHeight(pl.local_e,pl.local_n);
  const meshes=[];a.scene3d.traverse(o=>{if(o.isMesh&&!o.isBatchedMesh&&!o.isInstancedMesh&&o.visible)meshes.push(o)});
  const rc=new THREE.Raycaster();const rows=[];
  for(const y of [11.3,12.5,13.8,2.4])for(const x of [53.0,53.5,53.8,53.92,53.96,54.1,54.5]){
   const E=pl.local_e+x*Math.cos(th)+y*Math.sin(th),N=pl.local_n-x*Math.sin(th)+y*Math.cos(th);
   rc.set(new THREE.Vector3(E,houseY+5,-N),new THREE.Vector3(0,-1,0));
   const hits=[];for(const o of meshes){try{for(const h of rc.intersectObject(o,false))hits.push({y:+(h.point.y-houseY).toFixed(4),what:o.name||o.parent?.name||o.type})}catch{}}
   hits.sort((p,q)=>q.y-p.y);
   rows.push({x,y,terrain:+(a.terrain.surfaceHeight(E,N)-houseY).toFixed(4),hits:hits.slice(0,4)});}
  return {houseY,rows};}).catch(e=>String(e));
 fs.writeFileSync(path.join(out,`${label}-front-walk-probe.json`),JSON.stringify(probe,null,1));
 if(errors.length)throw Error(errors.join(' | '));
 await context.close();
}
}finally{await browser.close();server.close();}
