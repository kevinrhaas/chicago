#!/usr/bin/env node
/**
 * T-2015 fixed vegetation review. Serve the PUBLISHED mirror, save desktop/mobile
 * comparisons and frame census. Usage:
 * NODE_PATH=... PW_EXECUTABLE=... node tools/vegetation_review.mjs ../../site out
 *   --tag before|after --viewport desktop|mobile|both --detail full|balanced|light
 * The same world poses, July light, animation hold and pixel ratio are used in
 * each run. Generated evidence is checked in beside the research note.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
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
const VIEW = flag('--viewport', 'both');
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = {
  desktop: { width: 1280, height: 800 },
  mobile: { width: 390, height: 780 },
};

/** The stands: local ENU, compass yaw, pitch down in degrees. */
const STANDS = [
  ['river-bank', { local_e: 180, local_n: 0, yaw_deg: 0, pitch_deg: 0 }],
  ['north-bridge', { local_e: -81.59, local_n: 262.02, yaw_deg: 90, pitch_deg: 4 }],
  ['prairie', { local_e: -250, local_n: -150, yaw_deg: 90, pitch_deg: -8 }],
  ['woodland-close', null],
];

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
    const body = await readFile(file);
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
for (const [vp, size] of Object.entries(VIEWPORTS)) {
  if (VIEW !== 'both' && VIEW !== vp) continue;
  const page = await browser.newPage({ viewport: size, deviceScaleFactor: 1 });
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
  const close = await page.evaluate(() => {
    const a = window.__chicago4d;
    // Fixed once from the baseline scene. Scanning every zone on every run
    // was slow and allowed a dataset change to move the comparison camera.
    const e = -186, n = 692;
    if (a.flora.zoneAt(e, n) !== 'z06_dense_forest' || !a.flora.plantableAt(e, n))
      throw new Error('The fixed woodland review pose is no longer plantable woodland');
    return {local_e:e, local_n:n, yaw_deg:90, pitch_deg:-8};
  });
  stats[`close-pose-${vp}`] = close;
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
  for (const [name, pose] of STANDS) {
    await page.evaluate((t) => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport(t);
      // Production tick updates placement/culling before the actual render.
      api.step();
      api.step();
    }, pose ?? close);
    await page.waitForTimeout(1500);
    const s = await page.evaluate(() => window.__chicago4d.stats());
    stats[`${name}-${vp}`] = { drawCalls: s.drawCalls, triangles: s.triangles, textures: s.textures, programs: s.programs };
    await page.screenshot({ path: path.join(OUT, `${TAG}-${name}-${vp}.jpg`), type: 'jpeg', quality: 88 });
    console.log(`${TAG} ${name} ${vp}: ${s.triangles} triangles, ${s.drawCalls} calls`);
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
await writeFile(path.join(OUT, `${TAG}-stats.json`), JSON.stringify({ detail: DETAIL, stats, errors }, null, 2));
console.log(JSON.stringify({ frames: Object.keys(stats).filter(k => stats[k].drawCalls !== undefined).length, errors }, null, 2));
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
