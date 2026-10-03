#!/usr/bin/env node
/**
 * Bounded T-2015 species/material review, not the whole-town release smoke.
 * It serves the LIVE trees.js with test-only exports, and compares its generator
 * to a stated git baseline; it never copies production tree geometry.
 *
 * NODE_PATH=... PW_EXECUTABLE=... node tools/tree_surface_review.mjs \
 *   --out /tmp/tree-surface-review --baseline de81fad2
 *
 * Outputs full/light species rows, oak canopy, bark and atlas PNGs, plus JSON.
 * It asserts downstream RNG identity, finite attributes, and no increase in
 * light triangles for every existing species at three fixed seeds (180 cases).
 * This is a manual review tool because a screenshot is evidence to inspect,
 * not an assertion that photographic quality has been achieved.
 */
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers/web');
const args = process.argv.slice(2);
const arg = (key, fallback) => args.includes(key) ? args[args.indexOf(key) + 1] : fallback;
const OUT = path.resolve(arg('--out', '/tmp/tree-surface-review'));
const BASELINE = arg('--baseline', 'de81fad2');
const baselineSource = execFileSync('git', ['show', `${BASELINE}:chicago/4d/renderers/web/js/trees.js`],
  { cwd: ROOT, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
const baselineCommit = execFileSync('git', ['rev-parse', BASELINE], { cwd: ROOT, encoding: 'utf8' }).trim();
const source = await readFile(path.join(WEB, 'js/trees.js'), 'utf8');
const extras = '\nexport { MeshBuf, addTree, mulberry32 };\n';
await mkdir(OUT, { recursive: true });
let playwright;
try { playwright = await import('playwright'); }
catch {
  const root = (process.env.NODE_PATH || execFileSync('npm', ['root', '-g'], { encoding: 'utf8' }).trim())
    .split(path.delimiter)[0];
  playwright = await import(path.join(root, 'playwright/index.js'));
}
const { chromium } = playwright.chromium ? playwright : playwright.default;

const html = `<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,">
<style>body{margin:0;overflow:hidden}#label{position:absolute;top:12px;left:20px;font:16px sans-serif;color:#fff}</style>
<script type="importmap">{"imports":{"three":"/vendor/three-0.185.1/three.module.js"}}</script>
<div id="label">Procedural timber: full</div><script type="module">
import * as THREE from 'three';
import * as current from '/current.js';
import * as baseline from '/baseline.js';
import { createConfidenceView } from '/js/confidence.js';
import { createTreeAtlas, TREE_ALPHA_CUTOFF, patchTreeWind } from '/tree-surface.js';
const tests = [];
for (const [species, spec] of Object.entries(current.SPECIES)) for (let seed = 1; seed <= 3; seed++) {
  const before = new baseline.MeshBuf(), oldRng = baseline.mulberry32(seed);
  baseline.addTree(before, spec, 0, 0, 0, oldRng);
  const next = oldRng();
  for (const tier of ['light', 'balanced', 'full']) {
    const after = new current.MeshBuf(tier), rng = current.mulberry32(seed);
    current.addTree(after, spec, 0, 0, 0, rng);
    if (rng() !== next) throw new Error('Placement RNG drift: ' + species + ':' + tier);
    for (const values of [after.pos, after.nrm, after.col, after.flex, after.conf, after.uv])
      if (values.some(v => !Number.isFinite(v))) throw new Error('Non-finite geometry: ' + species);
    if (tier === 'light' && after.idx.length > before.idx.length)
      throw new Error('Light triangle regression: ' + species);
    tests.push({ species, seed, tier, triangles: after.idx.length / 3, baselineTriangles: before.idx.length / 3 });
  }
}
const scene = new THREE.Scene(); scene.background = new THREE.Color('#b4c8d8');
const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.1, 300);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(innerWidth, innerHeight); renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1; document.body.append(renderer.domElement);
const sun = new THREE.DirectionalLight('#fff5df', 3); sun.position.set(15, 32, 18); sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024); sun.shadow.camera.left = -35; sun.shadow.camera.right = 35;
sun.shadow.camera.top = 30; sun.shadow.camera.bottom = -30; sun.shadow.camera.far = 100;
scene.add(sun); scene.add(new THREE.HemisphereLight('#c7dcec', '#6c6950', 2.4));
const ground = new THREE.Mesh(new THREE.PlaneGeometry(100, 100),
  new THREE.MeshStandardMaterial({ color: '#6b7549', roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const atlas = createTreeAtlas(), wind = { value: 0 }, confidence = createConfidenceView();
const material = new THREE.MeshStandardMaterial({ map: atlas, bumpMap: atlas, bumpScale: 0.015,
  vertexColors: true, side: THREE.DoubleSide, alphaTest: TREE_ALPHA_CUTOFF, roughness: 0.92 });
patchTreeWind(material, wind, { surface: true }); confidence.patch(material);
const depth = new THREE.MeshDepthMaterial({ map: atlas, alphaTest: TREE_ALPHA_CUTOFF,
  side: THREE.DoubleSide, depthPacking: THREE.RGBADepthPacking });
patchTreeWind(depth, wind); confidence.patch(depth);
let batch;
const counts = {};
function makeTrees(tier) {
  if (batch) { scene.remove(batch); batch.dispose(); }
  const b = new current.MeshBuf(tier);
  for (const [i, species] of ['quercus_macrocarpa', 'salix_nigra', 'ulmus_americana', 'populus_deltoides'].entries())
    current.addTree(b, { ...current.SPECIES[species], speciesId: species },
      (i - 1.5) * 13, 0, 0, current.mulberry32(i * 323 + 14), 0.72);
  const geometry = b.build();
  batch = new THREE.BatchedMesh(1, b.count, b.idx.length, material);
  batch.addInstance(batch.addGeometry(geometry)); batch.computeBoundingSphere(); geometry.dispose();
  batch.castShadow = batch.receiveShadow = true; batch.customDepthMaterial = depth; scene.add(batch);
  counts[tier] = { triangles: b.idx.length / 3, vertices: b.count, foliageSprays: b.sprays,
    attributeBytes: Object.values(batch.geometry.attributes).reduce((n, a) => n + a.array.byteLength, 0) };
  document.querySelector('#label').textContent = 'Procedural timber: ' + tier + ' — oak, willow, elm, poplar';
}
function view(name) {
  if (name === 'lineup') { camera.position.set(26, 8, 37); camera.lookAt(2, 8, 0); }
  if (name === 'oak') { camera.position.set(-20, 6, 16); camera.lookAt(-19, 7, 0); }
  if (name === 'bark') { camera.position.set(-19.5, 1.7, 2.2); camera.lookAt(-19.5, 2, 0); }
  renderer.render(scene, camera);
}
window.review = { tests, counts, makeTrees, view, atlas: () => atlas.image.toDataURL('image/png') };
makeTrees('full'); view('lineup'); window.ready = true;
</script>`;

const server = createServer(async (req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname;
  try {
    let body;
    if (pathname === '/') body = html;
    else if (pathname === '/current.js') body = source + extras;
    else if (pathname === '/baseline.js') body = baselineSource + extras;
    else {
      const file = path.resolve(WEB, pathname === '/tree-surface.js' ? 'js/tree-surface.js' : `.${pathname}`);
      if (!file.startsWith(WEB + path.sep)) throw new Error('outside source');
      body = await readFile(file);
    }
    res.writeHead(200, { 'content-type': pathname === '/' ? 'text/html; charset=utf-8' : 'text/javascript' });
    res.end(body);
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
const errors = [];
try {
  browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 960, height: 640 }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(120000);
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', e => { if (e.type() === 'error') errors.push(e.text()); });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.waitForFunction(() => window.ready === true);
  for (const name of ['lineup', 'oak', 'bark']) {
    await page.evaluate(n => window.review.view(n), name);
    await page.screenshot({ path: path.join(OUT, `full-${name}.png`) });
  }
  await page.evaluate(() => { window.review.makeTrees('light'); window.review.view('lineup'); });
  await page.screenshot({ path: path.join(OUT, 'light-lineup.png') });
  const atlas = await page.evaluate(() => window.review.atlas());
  await writeFile(path.join(OUT, 'procedural-atlas.png'), Buffer.from(atlas.split(',')[1], 'base64'));
  const result = await page.evaluate(() => ({ tests: window.review.tests, counts: window.review.counts }));
  await writeFile(path.join(OUT, 'review.json'), JSON.stringify({ baselineCommit, ...result, errors }, null, 2));
  console.log(JSON.stringify({ baselineCommit, cases: result.tests.length, counts: result.counts, errors }, null, 2));
  if (errors.length) process.exitCode = 1;
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
