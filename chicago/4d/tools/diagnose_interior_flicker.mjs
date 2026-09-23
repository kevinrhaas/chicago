/**
 * T-0013 — WHAT IS FIGHTING INSIDE A LAYER?
 *
 *   node tools/diagnose_interior_flicker.mjs [--source] [--station ID] [--out DIR]
 *
 * `measure_tie_class.mjs` partitions the 2 mm-nudge flicker by WHICH LAYER owns
 * each moving pixel, and separates a layer's INTERIOR (surrounded on all eight
 * sides by its own footprint) from its silhouette against the rest of the scene.
 * It found 709 interior pixels, two thirds of them owned by `structures` and
 * `trees`, and the ticket it opened says plainly that nobody has asked WHY.
 *
 * This asks. The exact-depth-tie hypothesis is already dead (21 px under the
 * LessEqual -> Less switch), so the question is what else can move a pixel that
 * a layer surrounds. There are exactly three answers a renderer can give, and
 * they are distinguishable from the DEPTH FIELD itself rather than by analogy:
 *
 *   1. **an internal silhouette** — the pixel straddles a depth DISCONTINUITY
 *      between two surfaces of the same layer (one crown in front of another,
 *      a chimney against its own roof, one house against the house behind).
 *      `interiorOf` cannot see it, because it only knows the layer's outline
 *      against everything else. A camera resamples such an edge whatever it is
 *      made of: this is antialiasing working, exactly as the layer-to-layer
 *      silhouette is, and it is not a defect.
 *   2. **a depth REORDER** — the depth field is locally smooth, and yet the
 *      front-most surface is at a different distance after a 2 mm nudge. Two
 *      surfaces swapped. That IS a fight, and it is the thing the ticket looked
 *      for.
 *   3. **neither** — the same surface, at the same distance, drawn a different
 *      colour. Then nothing about the geometry moved and the cause is shading:
 *      a specular lobe or an interpolated normal resampled a shade differently.
 *
 * So: photograph the DEPTH BUFFER at the base pose and at the nudged pose, and
 * classify each interior-flickering pixel by what the depth field does there.
 *
 *   - a discontinuity is a SECOND difference, not a slope. A roof at grazing
 *     incidence changes depth fast and linearly across a pixel; an edge breaks
 *     the linearity. `|d(-1) + d(+1) - 2*d(0)|` is ~0 on any plane however
 *     steeply it is seen, and large at a break, so it separates the two without
 *     a per-surface threshold.
 *   - a 2 mm camera translation moves a true surface's distance by at most
 *     2 mm. Anything past 0.3 m is a different surface, not the same one.
 *
 * Two controlled toggles then confirm the reading against its neighbours, each
 * reverted with the frame asserted back to the base:
 *
 *   - **supersample** (`setPixelRatio(2)`): four times the sample density, same
 *     geometry, same shading. Sampling-bound pixels — edges and shading
 *     aliasing alike — heal. A depth reorder does not care how many samples you
 *     take, because every sample gets the same wrong answer.
 *   - **matte** (`roughness = 1`, `metalness = 0` everywhere): the specular
 *     lobe is the one part of the shading that varies fastest with the normal,
 *     so if class 3 is a specular resample it collapses here and nothing else
 *     in the frame's geometry has changed.
 *
 * Defaults to the PUBLISHED mirror, as every other flicker instrument here
 * does: depth precision is a property of the geometry that actually ships.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { decodePng } from './critic_metrics.mjs';
// The discriminator itself, in one place because `tools/measure_tie_class.mjs`
// asks the same question of the same frames (T-0156). Two copies would be two
// discriminators the moment either was tuned.
import {
  BREAK_M, REORDER_M, FAR_M, swapDepthMaterials, lineariseDepth, classifyDepth,
} from './depth_field.mjs';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const wantSource = process.argv.includes('--source');
const stArg = process.argv.indexOf('--station');
const WANT_STATION = stArg > -1 ? process.argv[stArg + 1] : 'from_above';
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.TIE_PORT || 4195);
const YEAR = process.env.TIE_YEAR || '1835';
const NUDGE_M = Number(process.env.TIE_NUDGE_M || 0.002);
const CHANNEL_EPS = 2;

const STATIONS = {
  from_above: { local_e: 60, local_n: -330, yaw_deg: 0, altitude_m: 175, pitch_deg: -30 },
  descend_main_stem: { local_e: 40, local_n: -150, yaw_deg: 20, altitude_m: 90, pitch_deg: -25 },
  over_the_forks: { local_e: -60, local_n: -60, yaw_deg: 40, altitude_m: 45, pitch_deg: -20 },
};
if (!STATIONS[WANT_STATION]) {
  console.error(`unknown station ${WANT_STATION}`);
  process.exit(2);
}
/** The two layers the ticket is about, plus ground as the comparison it names. */
const LAYERS = [
  { id: 'structures', match: "o.name === 'structures'" },
  { id: 'trees', match: "o.name === 'trees'" },
  { id: 'ground', match: "o.name.startsWith('terrain__')" },
];

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}\n`);

const VIEWPORT = process.env.TIE_VIEWPORT === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => {
  const api = window.__chicago4d;
  if (typeof api?.setAnimationHold !== 'function') return false;
  api.setAnimationHold(true);
  return true;
}, null, { polling: 'raf', timeout: 240_000 });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240_000 });
const gate = await page.$('#gate-btn');
if (gate) await page.click('#gate-btn');
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (/got it|dismiss|close/i.test(b.textContent ?? '')) b.click();
  }
  const style = document.createElement('style');
  style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
  document.head.append(style);
});
const canvas = (await page.$('#view')) ?? (await page.$('canvas'));
{
  const box = await canvas.boundingBox();
  if (!(box && box.x === 0 && box.y === 0
    && box.width === VIEWPORT.width && box.height === VIEWPORT.height)) {
    console.error(`the canvas does not fill the viewport (${JSON.stringify(box)})`);
    process.exit(2);
  }
}
const shot = async () => decodePng(await page.screenshot());

/** R-BUG6(a)'s repaired control: the flag AND a rebuild of every program. */
const shadowOn = await page.evaluate(async (want) => {
  const api = window.__chicago4d;
  api.renderer.shadowMap.enabled = want;
  api.scene3d.traverse((o) => {
    const m = o.material;
    if (!m) return;
    for (const one of Array.isArray(m) ? m : [m]) one.needsUpdate = true;
  });
  for (let i = 0; i < 4; i++) await api.capture(4);
  return api.renderer.shadowMap.enabled;
}, false);
if (shadowOn !== false) {
  console.error('the shadow map would not switch off — the residual is not the residual');
  process.exit(2);
}

async function stand(pose) {
  return page.evaluate(async (p) => {
    const api = window.__chicago4d;
    api.setFly(typeof p.altitude_m === 'number');
    api.walker.teleport(p);
    for (let i = 0; i < 8; i++) await api.capture(4);
    return { y: api.player.y, drawCalls: api.stats().drawCalls, near: api.stats().cameraNear };
  }, pose);
}
async function setLayer(match, visible) {
  return page.evaluate(async ({ src, want }) => {
    const api = window.__chicago4d;
    // eslint-disable-next-line no-new-func
    const pred = new Function('o', `return ${src};`);
    let n = 0;
    api.scene3d.traverse((o) => {
      if (!o.name) return;
      if (pred(o)) { o.visible = want; n++; }
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
    return n;
  }, { src: match, want: visible });
}
function maskOf(a, b) {
  const n = a.width * a.height;
  const m = new Uint8Array(n);
  let count = 0;
  for (let p = 0; p < n; p++) {
    const i = p * 4;
    const d = Math.max(
      Math.abs(a.data[i] - b.data[i]),
      Math.abs(a.data[i + 1] - b.data[i + 1]),
      Math.abs(a.data[i + 2] - b.data[i + 2]),
    );
    if (d > CHANNEL_EPS) { m[p] = 1; count++; }
  }
  return { m, count, width: a.width, height: a.height };
}
function interiorOf(foot, W, H) {
  const inner = new Uint8Array(foot.m.length);
  for (let y = 1; y < H - 1; y++) {
    for (let x = 1; x < W - 1; x++) {
      const p = y * W + x;
      if (!foot.m[p]) continue;
      if (foot.m[p - 1] && foot.m[p + 1] && foot.m[p - W] && foot.m[p + W]
        && foot.m[p - W - 1] && foot.m[p - W + 1] && foot.m[p + W - 1] && foot.m[p + W + 1]) {
        inner[p] = 1;
      }
    }
  }
  return inner;
}

const pose = STATIONS[WANT_STATION];
const arrived = await stand(pose);
const a = await shot();
const still = await shot();
const control = maskOf(a, still);
await stand({ ...pose, local_e: pose.local_e + NUDGE_M });
const b = await shot();
const flicker = maskOf(a, b);
await stand(pose);
const base = await shot();
const drift = maskOf(a, base);
if (control.count || drift.count) {
  console.error(`UNSOUND: control ${control.count} px, return ${drift.count} px — the harness `
    + 'does not reproduce its own frame');
  process.exit(2);
}
console.log(`T-0013 — what fights inside a layer · ${WANT_STATION} · ${VIEWPORT.width}x`
  + `${VIEWPORT.height} · ${NUDGE_M * 1000} mm nudge · near ${arrived.near} m · `
  + `${arrived.drawCalls} draw calls`);
console.log(`the frame flickers on ${flicker.count} px; control 0, return 0.\n`);

// ---- interior masks, exactly as measure_tie_class draws them --------------- //
const owned = new Uint8Array(flicker.m.length);
const interior = new Map();
for (const layer of LAYERS) {
  await setLayer(layer.match, false);
  const off = await shot();
  await setLayer(layer.match, true);
  const foot = maskOf(a, off);
  const inner = interiorOf(foot, a.width, a.height);
  const mine = [];
  for (let p = 0; p < foot.m.length; p++) {
    if (!foot.m[p] || !flicker.m[p] || owned[p]) continue;
    owned[p] = 1;
    if (inner[p]) mine.push(p);
  }
  interior.set(layer.id, mine);
  console.log(`${layer.id.padEnd(11)} interior ${String(mine.length).padStart(4)} px`);
}

// ---- the depth field, at both poses --------------------------------------- //
let depthOk = true;
await swapDepthMaterials(page, true);
await stand(pose);
const d0 = await shot();
await stand({ ...pose, local_e: pose.local_e + NUDGE_M });
const d1 = await shot();
await stand(pose);
await swapDepthMaterials(page, false);
const restored = maskOf(a, await shot());
if (restored.count) {
  console.log(`\nthe depth pass did not put the frame back (${restored.count} px) — `
    + 'the classification below would be measuring the instrument');
  depthOk = false;
}

const W = a.width;
const lin0 = lineariseDepth(d0, arrived.near, FAR_M);
const lin1 = lineariseDepth(d1, arrived.near, FAR_M);
const classify = (px) => classifyDepth(px, lin0, lin1, W);
const classes = new Map();
if (depthOk) {
  console.log('\nWHAT THE DEPTH FIELD DOES AT EACH INTERIOR-FLICKERING PIXEL');
  console.log('layer        interior   internal edge   depth reorder   same surface   no depth');
  for (const layer of LAYERS) {
    const px = interior.get(layer.id);
    const c = classify(px);
    classes.set(layer.id, c);
    const pc = (n) => `${String(n).padStart(4)} ${String(`(${(100 * n / (px.length || 1)).toFixed(0)}%)`).padStart(6)}`;
    console.log(`${layer.id.padEnd(12)} ${String(px.length).padStart(6)}   ${pc(c.break.length)}    `
      + `${pc(c.reorder.length)}   ${pc(c.smooth.length)}  ${String(c.sky.length).padStart(4)}`);
  }
  console.log(`\n  internal edge  = a depth BREAK (second difference > ${BREAK_M} m) inside the `
    + "layer's own footprint:\n                   one surface of the layer in front of another, "
    + 'which any camera resamples.\n  depth reorder  = locally smooth depth, front-most surface '
    + `${REORDER_M} m+ further or nearer after a\n                   2 mm nudge — two surfaces `
    + 'swapped. This is the fight the ticket looked for.\n  same surface   = same distance, same '
    + 'shape, different colour — shading, not geometry.');
}

// ---- the toggles ---------------------------------------------------------- //
async function nudgeAgain() {
  await stand(pose);
  const x = await shot();
  await stand({ ...pose, local_e: pose.local_e + NUDGE_M });
  const y = await shot();
  return { flick: maskOf(x, y), changed: maskOf(a, x) };
}
function healing(m) {
  const rows = [];
  for (const layer of LAYERS) {
    const px = interior.get(layer.id);
    const c = classes.get(layer.id);
    const still = px.filter((p) => m.m[p]).length;
    const per = (k) => (c ? c[k].filter((p) => m.m[p]).length : 0);
    rows.push({ id: layer.id, before: px.length, still,
      break: per('break'), reorder: per('reorder'), smooth: per('smooth') });
  }
  return rows;
}
function report(title, rows, changed) {
  console.log(`\n${title}`);
  console.log('layer        interior   still moving   of which edge / reorder / same-surface');
  for (const r of rows) {
    console.log(`${r.id.padEnd(12)} ${String(r.before).padStart(6)}   ${String(r.still).padStart(6)} `
      + `${String(`(${(100 * r.still / (r.before || 1)).toFixed(0)}%)`).padStart(7)}   `
      + `${r.break} / ${r.reorder} / ${r.smooth}`);
  }
  console.log(`  the picture itself moved on ${changed.count} px under this toggle`);
}

// supersample: four times the samples, same geometry, same shading.
{
  const ratio = await page.evaluate(async () => {
    const api = window.__chicago4d;
    api.renderer.setPixelRatio(2);
    for (let i = 0; i < 4; i++) await api.capture(4);
    return api.renderer.getPixelRatio();
  });
  if (ratio !== 2) console.log('\nthe pixel ratio would not move — the supersample toggle is inert');
  else {
    const r = await nudgeAgain();
    report(`SUPERSAMPLED (device pixel ratio 1 -> 2, ${flicker.count} px of whole-frame flicker `
      + `becomes ${r.flick.count})`, healing(r.flick), r.changed);
  }
  await page.evaluate(async () => {
    const api = window.__chicago4d;
    api.renderer.setPixelRatio(1);
    for (let i = 0; i < 4; i++) await api.capture(4);
  });
  await stand(pose);
  const back = maskOf(a, await shot());
  console.log(`  restored to within ${back.count} px (0 = the toggle is sound)`);
}

// matte: kill the specular lobe, leave every vertex where it was.
{
  const touched = await page.evaluate(async () => {
    const api = window.__chicago4d;
    const seen = new Set();
    let n = 0;
    api.scene3d.traverse((o) => {
      const m = o.material;
      if (!m) return;
      for (const one of Array.isArray(m) ? m : [m]) {
        if (seen.has(one.uuid) || typeof one.roughness !== 'number') continue;
        seen.add(one.uuid);
        one.userData.__rough = [one.roughness, one.metalness];
        one.roughness = 1;
        one.metalness = 0;
        one.needsUpdate = true;
        n++;
      }
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
    return n;
  });
  const r = await nudgeAgain();
  report(`MATTE (${touched} materials at roughness 1, metalness 0 — the specular lobe gone, `
    + `every vertex where it was; whole frame ${flicker.count} -> ${r.flick.count} px)`,
  healing(r.flick), r.changed);
  await page.evaluate(async () => {
    const api = window.__chicago4d;
    api.scene3d.traverse((o) => {
      const m = o.material;
      if (!m) return;
      for (const one of Array.isArray(m) ? m : [m]) {
        if (!one.userData?.__rough) continue;
        [one.roughness, one.metalness] = one.userData.__rough;
        delete one.userData.__rough;
        one.needsUpdate = true;
      }
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
  });
  await stand(pose);
  const back = maskOf(a, await shot());
  console.log(`  restored to within ${back.count} px (0 = the toggle is sound)`);
}

await browser.close();
server.close();
if (errors.length) {
  console.log(`\npage errors: ${errors.length}\n - ${errors.slice(0, 5).join('\n - ')}`);
  process.exit(2);
}
