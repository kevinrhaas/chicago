#!/usr/bin/env node
/**
 * T-2035 moving-camera vegetation continuity review. Serve the PUBLISHED mirror, save desktop/mobile
 * comparisons and frame census. Usage:
 * NODE_PATH=... PW_EXECUTABLE=... node tools/vegetation_motion_review.mjs ../../site out
 *   --tag before|after --viewport desktop|mobile|both --detail full|balanced|light
 * The same world poses, July light, animation hold and pixel ratio are used in
 * each run. Generated evidence is checked in beside the research note.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync, execFileSync } from 'node:child_process';
import path from 'node:path';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH || execSync('npm root -g').toString().trim()).split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const argv = process.argv.slice(2);
const flag = (name, dflt) => {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : dflt;
};
const positional = argv.filter((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));
const ROOT = path.resolve(positional[0] ?? '../../site');
const OUT = path.resolve(positional[1] ?? '/tmp/vegetation-review');
const TAG = flag('--tag', 'after');
const DETAIL = flag('--detail', 'full');
const IS_BASELINE = argv.includes('--baseline');
const baselineRef = flag('--baseline-ref', null);
const baselineFlora = baselineRef ? execFileSync('git', ['show', baselineRef + ':chicago/4d/renderers/web/js/flora.js'], {encoding:'utf8'}) : null;
const VIEW = flag('--viewport', 'both');
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = {
  desktop: { width: 1280, height: 800 },
  mobile: { width: 390, height: 780 },
};

/** The stands: local ENU, compass yaw, pitch down in degrees. */
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.wasm': 'application/wasm', '.svg': 'image/svg+xml', '.geojson': 'application/json', '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json',
};
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  try {
    if (file.endsWith('/')) file = path.join(file, 'index.html');
    const body = baselineFlora && url.pathname.endsWith('/walk/js/flora.js') ? baselineFlora : await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404).end('nope');
  }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
});
const errors = [];
const stats = {};
try {
for (const [vp, size] of Object.entries(VIEWPORTS)) {
  if (VIEW !== 'both' && VIEW !== vp) continue;
  const page = await browser.newPage({ viewport: size, deviceScaleFactor: 1, hasTouch: vp === 'mobile', isMobile: vp === 'mobile' });
  page.on('pageerror', (e) => errors.push(`${vp}: ${e}`));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`${vp} console: ${m.text()}`); });
  await page.addInitScript((d) => {
    localStorage.setItem('chicago4d.detail', d);
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  page.setDefaultTimeout(240000);
  const start = Date.now();
  await page.goto(`${base}/4d/walk/?year=1835`, { waitUntil: 'load', timeout: 240000 });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });
  stats[`startup-${vp}`] = { readyMs: Date.now() - start };
  console.log(`${TAG} ${vp} ready in ${Date.now() - start} ms`);
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
    }
    window.__chicago4d.setAnimationHold?.(true);
    window.__chicago4d.renderer.setAnimationLoop(null);
  });
  await page.waitForTimeout(600);
  // The chrome is hidden so the frame is the render and not the overlay.
  await page.addStyleTag({
    content: 'body > *:not(canvas):not(#view):not(main) { visibility: hidden !important; }'
      + ' #hud, .hud, #help, .card, .popup, .toast, header, nav, footer { visibility: hidden !important; }',
  });
  const routes = [
    ['verge', {local_e:305,local_n:0.6,yaw_deg:84,pitch_deg:-8}, 1,0,0.25,32],
    ['reeds', {local_e:550,local_n:14.8,yaw_deg:90,pitch_deg:-3}, 1,0,0.25,32],
    ['flight', {local_e:170,local_n:-75,yaw_deg:90,pitch_deg:-35,altitude_m:18}, 1,0,0.75,24],
    ['strafe', {local_e:550,local_n:14.8,yaw_deg:0,pitch_deg:-8}, 1,0,0.25,24],
    ['reverse', {local_e:313,local_n:0.6,yaw_deg:84,pitch_deg:-8}, -1,0,0.25,24],
    ['prairie-down', {local_e:-400,local_n:-700,yaw_deg:0,pitch_deg:-80,altitude_m:18}, 1,0,0.25,12],
    ['downward', {local_e:180,local_n:-75,yaw_deg:90,pitch_deg:-58,altitude_m:18}, 0,0,0,12],
  ];
  for (const [name,pose,de,dn,stride,count] of routes) {
    const selected=flag('--routes','');if(selected&&!selected.split(',').includes(name))continue;
    const route = {frames:[],jumps:[],identityErrors:[],maxTriangles:0,maxCalls:0};
    await page.evaluate(()=>{window.__motionPrior=null;});
    for (let frame=0;frame<count;frame++) {
      const t={...pose, local_e:pose.local_e+de*stride*frame,local_n:pose.local_n+dn*stride*frame};
      if(name==='downward')t.pitch_deg=pose.pitch_deg-frame*2;
      const reading=await page.evaluate(t=>{
        const a=window.__chicago4d;a.setFly(t.altitude_m!=null);a.walker.teleport(t);a.step();
        const gl=a.renderer.getContext();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));
        const current=new Map(), identities=new Map(), identityErrors=[];
        const V=new a.camera.position.constructor();
        function group(name){if(name==='flora-near-carry')return 'flora-near';if(name==='flora-mid-carry')return 'flora-mid';if(name==='flora-shrub-far')return 'flora-shrub';return name;}
        const screen=(p,cam)=>{V.set(p[0],p[1]+p[3]*0.5,p[2]).project(cam);return Math.abs(V.x)<0.9&&Math.abs(V.y)<0.9&&V.z>-1&&V.z<1;};
        a.flora.group.traverse(m=>{
          if(!m.isInstancedMesh||m.name.includes('head'))return;
          const mm=m.instanceMatrix.array,fa=m.geometry.getAttribute('aFlora'),ra=m.geometry.getAttribute('aChiRing');if(!fa||!ra)return;
          for(let i=0;i<m.count;i++){
            const x=mm[i*16+12],y=mm[i*16+13],z=mm[i*16+14],p=[x,y,z,fa.getX(i)];
            const key=group(m.name)+':'+x.toFixed(4)+':'+z.toFixed(4);
            const d=Math.hypot(a.camera.position.x-x,a.camera.position.z-z);
            const outer=Math.max(0,Math.min(1,(ra.getX(i)-d)/Math.max(ra.getY(i),1e-6)));
            const inner=ra.getW(i)>0?Math.max(0,Math.min(1,(d-ra.getZ(i))/ra.getW(i))):1;
            const fade=outer*inner;
            if(!current.has(key)||current.get(key).fade<fade)current.set(key,{p,fade});
            const transform=[y,fa.getX(i),fa.getY(i),fa.getZ(i),fa.getW(i)];
            if(identities.has(key)&&transform.some((v,j)=>Math.abs(v-identities.get(key)[j])>1e-5))identityErrors.push(key);
            identities.set(key,transform);
          }
        });
        const jumps=[]; const prior=window.__motionPrior;
        if(prior)for(const key of new Set([...prior.plants.keys(),...current.keys()])){
          const old=prior.plants.get(key),now=current.get(key),p=(now??old).p;
          const jump=Math.abs((now?.fade??0)-(old?.fade??0));
          if(jump>0.45&&screen(p,a.camera)&&screen(p,prior.camera))jumps.push({key,jump,from:old?.fade??0,to:now?.fade??0,p});
        }
        window.__motionPrior={plants:current,camera:a.camera.clone()};
        return {pose:t,jumps,identityErrors,stats:a.stats(),flora:a.flora.stats,
          zone:a.flora.zoneAt(t.local_e,t.local_n),near:a.camera.near,
          shrubZones:[...current].filter(([k,v])=>k.startsWith('flora-shrub')&&v.fade>0.9).slice(0,20).map(([k,v])=>({key:k,zone:a.flora.zoneAt(v.p[0],-v.p[2])}))};
      },t);
      route.jumps.push(...reading.jumps.map(j=>({frame,...j})));route.identityErrors.push(...reading.identityErrors);
      route.maxTriangles=Math.max(route.maxTriangles,reading.stats.triangles);route.maxCalls=Math.max(route.maxCalls,reading.stats.drawCalls);
      route.frames.push({frame,...reading});
      if(!IS_BASELINE&&Object.keys(reading.flora.shortfall).length)errors.push(`${vp}/${name}/${frame}: instance cap truncated ${JSON.stringify(reading.flora.shortfall)}`);
      if(frame%4===0||frame===count-1)await page.screenshot({path:path.join(OUT,`${TAG}-${DETAIL}-${vp}-${name}-${String(frame).padStart(3,'0')}.jpg`),type:'jpeg',quality:85});
    }
    stats[`${name}-${vp}`]=route;
    console.log(`${TAG} ${DETAIL} ${vp} ${name}: ${route.jumps.length} abrupt on-screen changes; ${route.identityErrors.length} identity errors; ${route.maxTriangles} triangles / ${route.maxCalls} calls`);
    if(!IS_BASELINE&&(route.jumps.length||route.identityErrors.length))errors.push(`${vp}/${name}: discontinuity or identity mismatch`);
  }
  stats[`vegetation-${vp}`] = await page.evaluate(() => {
    const a = window.__chicago4d;
    const gl = a.renderer.getContext();
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    return { trees: a.trees.stats, flora: a.flora.stats, problems: a.problems,
      device: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER) };
  });
  await page.close();
}
} catch (error) {
  errors.push(`review: ${error.stack ?? error}`);
} finally {
await writeFile(path.join(OUT, `${TAG}-${DETAIL}-${VIEW}-motion.json`), JSON.stringify({ detail: DETAIL, stats, errors }, null, 2));
console.log(JSON.stringify({ frames: Object.keys(stats).filter(k => stats[k].frames).reduce((n,k)=>n+stats[k].frames.length,0), errors }, null, 2));
await browser.close();
server.close();
}
process.exit(errors.length ? 1 : 0);
