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
const provenance = { base_commit: execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim(), main_sha256: hash('renderers/web/js/main.js'), mirror_main_sha256: hash(path.join(root, 'walk/js/main.js')), budget_sha256: hash('renderers/web/js/render-budget.js'), mirror_budget_sha256: hash(path.join(root, 'walk/js/render-budget.js')) };
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

assert.equal(provenance.budget_sha256, provenance.mirror_budget_sha256, 'publish the current budget before measuring');

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
const receipts=[];
try {
 for (const viewport of [{width:1280,height:800},{width:390,height:780}]) {
  const page=await browser.newPage({viewport,hasTouch:viewport.width<600});
  const errors=[]; page.on('pageerror',e=>{errors.push(e.message);console.error('page error:',e.message);});
  await page.goto(`http://127.0.0.1:${server.address().port}/1835/`,{waitUntil:'domcontentloaded',timeout:180000});
  await page.waitForFunction(()=>window.__chicago4d?.ready,null,{timeout:240000,polling:1000});
  console.log('ready',JSON.stringify(viewport));
  const result=await page.evaluate(async()=>{
   const a=window.__chicago4d; a.renderer.setAnimationLoop(null);a.setAnimationHold(true);
   await a.setDetail('full'); a.setFly(false);a.setTravelMode('instantly');
   a.goToTarget({kind:'structure',id:'sauganash_hotel',label:'Sauganash Hotel'});a.closeBuilding();
   a.step();a.step();
   await a.navigator.select('confidence');
   const read=()=>{
    a.step();a.step();
    const s=a.stats();return {detail:a.detail,ghosting:a.confidence.ghosting,triangles:s.triangles,drawCalls:s.drawCalls,budget:{...s.budget},publicBudget:{...a.budget},position:a.camera.position.toArray(),quaternion:a.camera.quaternion.toArray()};
   };
   const preset=id=>{const b=document.querySelector(`#navigator .nav-preset[data-preset="${id}"]`);if(!b)throw Error('Missing preset '+id);b.click();};
   const modes={};
   preset('normal');modes.normal=read();
   preset('xray');modes.xray=read();
   preset('normal');a.setConfidenceView(true);a.confidence.setGrade('reconstructed',{mode:'ghost',opacity:.4});modes.ghost40=read();
   await a.setDetail('balanced');preset('xray');modes.balanced=read();
   await a.setDetail('light');modes.light=read();
   await a.setDetail('full');preset('normal');modes.restored=read();
   return modes;
  });
  receipts.push({viewport,result,errors});
  console.log(JSON.stringify(receipts.at(-1),null,2));
  fs.writeFileSync(path.join(output,'ghost-validation.json'),JSON.stringify({provenance,receipts},null,2)+'\n');
  assert.deepEqual(errors,[]);
  for(const [mode,s] of Object.entries(result)){
   assert.deepEqual(s.budget,s.publicBudget,mode+' public/stat agreement');
   const ghost=s.detail==='full'&&s.ghosting;
   assert.equal(s.budget.triangles,ghost?3760000:({full:3470000,balanced:2625000,light:1190000}[s.detail]));
   assert.equal(s.budget.drawCalls,ghost?8900:7800);
   assert(s.drawCalls<=s.budget.drawCalls,mode+' draw allowance');
   if(s.detail==='full')assert(s.triangles<=s.budget.triangles,mode+' triangle allowance');
  }
  assert(result.xray.ghosting && result.ghost40.ghosting);
  assert(!result.normal.ghosting && !result.restored.ghosting);
  await page.close();
 }
} finally {await browser.close();server.close();}
console.log('PASS published phone/desktop Full Ghost budgets and lower-tier/normal restoration');
