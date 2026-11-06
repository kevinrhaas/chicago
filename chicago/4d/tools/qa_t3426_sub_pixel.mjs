#!/usr/bin/env node
/**
 * T-3426 — WHAT LEAVING THE SUB-PIXEL STRUCTURE PIECES OUT OF `light`'S COLOUR PASS
 * COSTS AND SAVES, at the stand the smoke holds light against full on (West prairie).
 *
 *   node tools/qa_t3426_sub_pixel.mjs [390x780,1280x800]      # reads the PUBLISHED mirror
 *
 * Boots the walk, enters the town, goes to `light` at the smoke's own West prairie pose,
 * stops the animation loop and renders HELD frames (twice each, read back in the same
 * task, as tools/qa_t3312_alley_corner.mjs does), so two frames with the same switch are
 * byte-equal and any pixel that differs is the switch's:
 *   off, off again   — the noise floor, which must be 0
 *   on               — as shipped (sub-pixel.js, MAX_RADIUS_PIXELS 1)
 *   control at 4 px  — a looser bound, to show the comparison CAN see a removed piece
 * then reads `full` at the same pose for the ratio. One JSON line per viewport.
 * This is a measurement, not a gate: tools/smoke_renderer.mjs part 5 holds the ratio.
 */
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { execSync } from 'node:child_process'; import { fileURLToPath } from 'node:url';
const HERE = path.dirname(fileURLToPath(import.meta.url));
async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); } catch {
    const root = (process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();
const ROOT = path.resolve(HERE, '../../../site/4d');
if (!fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) { console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`); process.exit(2); }
const PORT = Number(process.env.QA_PORT || 4212);
const TYPES = { '.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.wasm':'application/wasm','.svg':'image/svg+xml','.png':'image/png' };
const server = http.createServer((req,res)=>{ let f=path.join(ROOT,decodeURIComponent(req.url.split('?')[0])); if(fs.existsSync(f)&&fs.statSync(f).isDirectory()) f=path.join(f,'index.html'); if(!fs.existsSync(f)){res.writeHead(404);res.end();return;} res.writeHead(200,{'content-type':TYPES[path.extname(f)]||'application/octet-stream'}); fs.createReadStream(f).pipe(res);});
await new Promise(r=>server.listen(PORT,r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args:['--enable-unsafe-swiftshader'] });
const vps = (process.argv[2]||'390x780,1280x800').split(',').map(s=>s.split('x').map(Number));
for (const [w,h] of vps) {
  const page = await browser.newPage({ viewport:{width:w,height:h} });
  const errors=[]; page.on('pageerror', e=>errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${PORT}/walk/?year=1835`);
  await page.waitForFunction(()=>window.__chicago4d?.ready===true,null,{timeout:300000});
  const pose = { local_e: -250, local_n: -150, yaw_deg: 90, pitch_deg: -8 };
  const prep = await page.evaluate(async (pose)=>{
    const a=window.__chicago4d;
    if (!document.getElementById('gate').hasAttribute('hidden') && a.welcome) { const d=Date.now()+90000; while(a.welcome.state!=='world'&&Date.now()<d){ if(a.welcome.state==='welcome')a.welcome.enter('spawn'); await new Promise(r=>setTimeout(r,100)); } }
    window.__render=a.renderer.render; a.renderer.render=()=>{};
    const fr=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    await a.setDetail('light'); await fr(); a.setFly(false); a.walker.teleport(pose); await fr();
    a.renderer.render=window.__render; a.step(); a.renderer.render=()=>{};
    return { detail: a.detail, active: a.buildings.subPixel.active };
  }, pose);
  const res = await page.evaluate((pose)=>{ const a=window.__chicago4d; const R=a.renderer; R.render=window.__render; R.setAnimationLoop(null);
    const gl=R.getContext(), W=gl.drawingBufferWidth, H=gl.drawingBufferHeight;
    const frame=()=>{ R.render(a.scene3d,a.camera); R.render(a.scene3d,a.camera); const s=a.stats(); const px=new Uint8Array(W*H*4); gl.readPixels(0,0,W,H,gl.RGBA,gl.UNSIGNED_BYTE,px); return {px, calls:s.drawCalls, tris:s.triangles, skipped:a.buildings.subPixel.skipped}; };
    const diff=(x,y)=>{ let n=0,n24=0,max=0; for(let i=0;i<x.length;i+=4){ const d=Math.max(Math.abs(x[i]-y[i]),Math.abs(x[i+1]-y[i+1]),Math.abs(x[i+2]-y[i+2])); if(d>0)n++; if(d>24)n24++; if(d>max)max=d; } return {n,n24,max}; };
    const B=a.buildings;
    B.subPixel.on=false; const off1=frame(); const off2=frame();
    B.subPixel.on=true; const on=frame();
    B.subPixel.maxPixels=4; const ctrl=frame(); B.subPixel.maxPixels=1;
    const strip=(f)=>({calls:f.calls,tris:f.tris,skipped:f.skipped});
    return { pixels:W*H, off:strip(off1), on:strip(on), control4px:strip(ctrl), offVsOff:diff(off1.px,off2.px), offVsOn:diff(off1.px,on.px), offVsControl:diff(off1.px,ctrl.px) };
  }, pose);
  res.prep = prep; res.errors = errors;
  console.log(`${w}x${h}`, JSON.stringify(res));
  await page.close();
}
await browser.close(); server.close();
