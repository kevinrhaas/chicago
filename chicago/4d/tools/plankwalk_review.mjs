#!/usr/bin/env node
/**
 * T-2037 paired plankwalk gap-filter review. Serve the PUBLISHED mirror, save desktop/mobile
 * comparisons and frame census. Usage:
 * NODE_PATH=... PW_EXECUTABLE=... node tools/plankwalk_review.mjs ../../site out
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
  const poses = [
    ['river-walk', {local_e:550,local_n:14.8,yaw_deg:90,pitch_deg:-3}],
    ['river-flight', {local_e:550,local_n:14.8,yaw_deg:90,pitch_deg:-20,altitude_m:35}],
    ['outer-lot-flight', {local_e:460,local_n:-20,yaw_deg:70,pitch_deg:-15,altitude_m:12}],
    ['distant-flight', {local_e:200,local_n:-100,yaw_deg:65,pitch_deg:-25,altitude_m:100}],
  ];
  for (const [name, pose] of poses) {
    const shots = [];
    for (let frame=0; frame<3; frame++) {
      const t={...pose, local_e:pose.local_e+frame*0.5};
      for (const enabled of [0,1]) {
        const reading=await page.evaluate(({t,enabled})=>{
          const a=window.__chicago4d;
          a.setFly(t.altitude_m!=null);a.walker.teleport(t);
          const frontage=a.scene3d.getObjectByName('frontage');
          let materials=0;
          const seen=new Set();
          frontage.traverse(m=>{if(m.material&&!seen.has(m.material)){
            seen.add(m.material);const filter=m.material.userData.plankGapFilter;
            if(filter){filter.enabled.value=enabled;materials++;}
          }});
          a.step();
          const gl=a.renderer.getContext();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));
          return {pose:t,enabled,materials,stats:a.stats(),reach:a.furnitureReach,
            merge:a.farMergeStats,problems:a.problems};
        },{t,enabled});
        if(reading.materials!==1)errors.push(`${vp}/${name}: expected shared filter material, got ${reading.materials}`);
        shots.push({frame,...reading});
        await page.screenshot({path:path.join(OUT,`${TAG}-${DETAIL}-${vp}-${name}-${frame}-${enabled?'filtered':'original'}.jpg`),type:'jpeg',quality:92});
      }
    }
    stats[`${name}-${vp}`]=shots;
    console.log(`${DETAIL} ${vp} ${name}: ${shots[0].stats.triangles} triangles / ${shots[0].stats.drawCalls} calls; filter delta ${shots[1].stats.triangles-shots[0].stats.triangles} triangles`);
    if(DETAIL==='light'&&name==='distant-flight'){
      const control=await page.evaluate(()=>{const a=window.__chicago4d;const old=a.furnitureReach.reachM;a.setFurnitureReach(null);a.step();const result={stats:a.stats(),reach:a.furnitureReach,old};return result;});
      await page.screenshot({path:path.join(OUT,`${TAG}-${DETAIL}-${vp}-${name}-reach-control.jpg`),type:'jpeg',quality:92});
      stats[`reach-control-${vp}`]=control;
      await page.evaluate(m=>window.__chicago4d.setFurnitureReach(m),control.old);
    }
  }
  await page.close();
}
} catch (error) { errors.push(`review: ${error.stack ?? error}`); }
finally {
  await writeFile(path.join(OUT, `${TAG}-${DETAIL}-${VIEW}-planks.json`), JSON.stringify({detail:DETAIL,stats,errors},null,2));
  console.log(JSON.stringify({errors},null,2));
  await browser.close();server.close();
}
process.exit(errors.length?1:0);
