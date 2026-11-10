import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
const { chromium } = createRequire(import.meta.url)('playwright');
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const root = path.resolve('../../site/4d');
const output = path.dirname(fileURLToPath(import.meta.url));
const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const provenance = { base_commit: execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim(), main_sha256: hash('renderers/web/js/main.js'), mirror_main_sha256: hash(path.join(root, 'walk/js/main.js')), culler_sha256: hash('renderers/web/js/shadow-casters.js') };
assert.equal(provenance.main_sha256, provenance.mirror_main_sha256, 'publish the current source before measuring');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.wasm': 'application/wasm', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  let file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(root) || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
try {
 const page = await browser.newPage({ viewport: { width:1280, height:800 } });
 const errors=[]; page.on('pageerror', e=>{ errors.push(e.message); console.error('page error:', e.message); });
 await page.goto(`http://127.0.0.1:${server.address().port}/1835/`, {waitUntil:'domcontentloaded',timeout:180000});
 await page.waitForFunction(()=>window.__chicago4d?.ready, null, {timeout:240000,polling:1000});
 console.log('ready');
 const result=await page.evaluate(async()=>{
  const a=window.__chicago4d;
  a.renderer.setAnimationLoop(null);
  await a.setDetail('balanced');
  a.setFly(false); a.walker.teleport({local_e:-250,local_n:-150,yaw_deg:90,pitch_deg:-8});
  a.step();a.step();
  const gl=a.renderer.getContext(), w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
  const frame=()=>{
   a.renderer.shadowMap.autoUpdate=true;
   for(let i=0;i<2;i++){a.world.follow(a.camera.position);a.world.aim(a.camera);a.renderer.render(a.scene3d,a.camera);}
   gl.finish();
   const px=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);
   const stats=a.stats(); return {px,triangles:stats.triangles,drawCalls:stats.drawCalls};
  };
  const configured=a.setCastersTowardView();
  a.setCastersTowardView(false);const off=frame();
  a.setCastersTowardView(true);const on=frame();
  a.world.light.castShadow=false;const control=frame();a.world.light.castShadow=true;
  let different=0,controlDifferent=0,maxDelta=0;
  for(let i=0;i<off.px.length;i+=4){let d=0,c=0;for(let j=0;j<3;j++){d=Math.max(d,Math.abs(off.px[i+j]-on.px[i+j]));c=Math.max(c,Math.abs(off.px[i+j]-control.px[i+j]));}if(d){different++;maxDelta=Math.max(maxDelta,d);}if(c)controlDifferent++;}
  return {scene:a.scene?.id,configured,ceiling:a.detailLevels.balanced.triangles,off:{triangles:off.triangles,drawCalls:off.drawCalls},on:{triangles:on.triangles,drawCalls:on.drawCalls},pixels:w*h,different,maxDelta,controlDifferent};
 });
 console.log(JSON.stringify({result,errors},null,2));
 fs.writeFileSync(path.join(output, 'browser-validation.json'),JSON.stringify({provenance,viewport:{width:1280,height:800},result,errors},null,2)+'\n');
 assert.deepEqual(errors,[]);
 assert.equal(result.configured.on,true,'Balanced enables the existing conservative cull');
 assert.equal(result.ceiling,2625000,'the triangle ceiling is unchanged');
 assert.equal(result.different,0);
 assert(result.controlDifferent>0);
 assert(result.on.triangles<result.off.triangles);
 assert(result.on.triangles<=result.ceiling);
} finally { await browser.close();server.close(); }
