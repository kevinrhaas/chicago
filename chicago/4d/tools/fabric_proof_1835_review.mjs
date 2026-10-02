#!/usr/bin/env node
/**
 * Drive the T-1801 proof page in Chromium at 390x780 and 1280x800, capture the
 * comparison, and price strategy A at the three tiers.
 *
 *   node tools/fabric_proof_1835_review.mjs --work /tmp/fabric-proof-1835 \
 *     --site ../../site/4d --out docs/RESEARCH/1835-fabric-proof
 *
 * Normally run by tools/fabric_proof_1835.sh, which builds the work directory first.
 * Serves four roots from one local server, in-process (no background job):
 *   /page/   tools/fabric_proof/        /vendor/  renderers/web/vendor/
 *   /js/     renderers/web/js/ (world.js: the town's own light rig)
 *   /work/   the proof GLBs and maps    /site/    the published mirror (Glessner v4)
 * Writes <out>/<viewport>-<shot>.jpg and <out>/review.json. Exits non-zero on a page
 * error or a page that never reports ready, so a broken proof is not a quiet one.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const WORK = path.resolve(arg('work', '/tmp/fabric-proof-1835'));
const SITE = path.resolve(ROOT, arg('site', '../../site/4d'));
const OUT = path.resolve(ROOT, arg('out', 'docs/RESEARCH/1835-fabric-proof'));
const ONLY = arg('only', null); // e.g. --only proposed-close: one shot, both viewports, no tier pricing

const MOUNTS = [['/page/', path.join(HERE, 'fabric_proof')], ['/vendor/', path.join(ROOT, 'renderers/web/vendor')],
  ['/js/', path.join(ROOT, 'renderers/web/js')],
  ['/work/', WORK], ['/site/', SITE]];
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.png': 'image/png', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm' };

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const m = MOUNTS.find(([p]) => u.startsWith(p));
  const file = m && path.join(m[1], u.slice(m[0].length));
  if (!file || !file.startsWith(m[1]) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end(); return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const BASE = `http://127.0.0.1:${server.address().port}/page/index.html`;

const { chromium } = await import('playwright');
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined, // T-0153: pointable at any Chromium
  args: ['--enable-unsafe-swiftshader'],
});

const VIEWPORTS = { mobile: { width: 390, height: 780 }, desktop: { width: 1280, height: 800 } };
const SHOTS = [
  ['current-wide', { mode: 'current', view: 'wide' }],
  ['proposed-wide', { mode: 'proposed', view: 'wide' }],
  ['current-close', { mode: 'current', view: 'close' }],
  ['courses-close', { mode: 'courses', view: 'close' }],
  ['proposed-close', { mode: 'proposed', view: 'close' }],
  ['proposed-close-whitelead', { mode: 'proposed', view: 'close', finish: 'white_lead' }],
  ['proposed-close-neutral', { mode: 'proposed', view: 'close', light: 'neutral' }],
  ['proposed-close-transmission', { mode: 'proposed', view: 'close', glass: 'transmission' }],
  ['glessner-wide', { mode: 'glessner', view: 'wide' }],
  ['glessner-close', { mode: 'glessner', view: 'close' }],
];
// The tier prices are read on the desktop wide stand, where every substrate is in view.
const COSTS = ['current', 'proposed'].flatMap((mode) => ['full', 'balanced', 'light']
  .map((tier) => [`${mode}-${tier}`, { mode, view: 'wide', tier }]))
  .concat([['proposed-full-transmission', { mode: 'proposed', view: 'wide', tier: 'full', glass: 'transmission' }]]);

fs.mkdirSync(OUT, { recursive: true });
const errors = [];
const review = { shots: {}, costs: {} };

async function visit(vp, params, shot) {
  const ctx = await browser.newContext({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  // three reports a shader that failed to compile on console.error and draws nothing
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(`console: ${m.text().slice(0, 600)}`); });
  const bytes = { maps: 0, glb: 0 };
  page.on('response', async (r) => {
    const u = r.url();
    try {
      const n = (await r.body()).length;
      if (/\/maps\/.*\.png$/.test(u)) bytes.maps += n;
      else if (u.endsWith('.glb')) bytes.glb += n;
    } catch { /* a body that never arrived is counted by the ready check */ }
  });
  const qs = new URLSearchParams({ tier: 'full', light: 'scene', ...params });
  await page.goto(`${BASE}?${qs}`);
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 240000 });
  const state = await page.evaluate(() => ({ ready: document.body.dataset.ready, proof: window.__proof,
    error: window.__proofError }));
  if (state.ready !== '1') pageErrors.push(state.error ?? 'not ready');
  if (shot) await page.screenshot({ path: path.join(OUT, `${vp}-${shot}.jpg`), type: 'jpeg', quality: 82 });
  await ctx.close();
  for (const e of pageErrors) errors.push(`${vp} ${qs}: ${e}`);
  return { ...state.proof, wireBytes: bytes };
}

for (const vp of Object.keys(VIEWPORTS)) {
  for (const [shot, params] of SHOTS.filter(([s]) => !ONLY || s === ONLY)) {
    const r = await visit(vp, params, shot);
    review.shots[`${vp}-${shot}`] = r;
    console.log(`${vp.padEnd(7)} ${shot.padEnd(26)} calls ${r.calls} tris ${r.triangles} `
      + `tex ${r.textures} ${(r.gpuBytes / 2 ** 20).toFixed(1)} MiB load ${r.loadMs} ms`);
  }
}
for (const [key, params] of (ONLY ? [] : COSTS)) {
  const r = await visit('desktop', params, null);
  review.costs[key] = r;
  console.log(`cost    ${key.padEnd(26)} calls ${r.calls} tris ${r.triangles} tex ${r.textures} `
    + `gpu ${(r.gpuBytes / 2 ** 20).toFixed(1)} MiB wire maps ${(r.wireBytes.maps / 1e6).toFixed(2)} MB `
    + `glb ${(r.wireBytes.glb / 1e3).toFixed(1)} kB load ${r.loadMs} ms`);
}

await browser.close();
server.close();
review.errors = errors;
fs.writeFileSync(path.join(OUT, 'review.json'), `${JSON.stringify(review, null, 2)}\n`);
if (errors.length) { console.error(`PAGE ERRORS (${errors.length}):\n${errors.join('\n')}`); process.exit(1); }
console.log(`review written: ${path.relative(ROOT, OUT)}/ (${Object.keys(review.shots).length} captures, 0 page errors)`);
