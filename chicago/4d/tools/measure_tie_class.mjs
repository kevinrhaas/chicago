/**
 * ROADMAP R-BUG6(b) — WHICH LAYER OWNS THE FLICKER?
 *
 *   node tools/measure_tie_class.mjs [--source] [--station ID] [--out DIR]
 *
 * R-BUG1 measured that the frame flickers under a two-millimetre camera nudge.
 * R-BUG6(a) measured that the shadow map carries 14–16 % of it and fixed that
 * part. What was left — 1,108 pixels at `from_above` — was attributed to
 * "co-planar ties" in three different boxes of the ROADMAP, on no measurement
 * at all: the class was named from the outside, by analogy with R-W5a2's batch
 * merge, and nothing had ever asked WHICH SURFACES those pixels belong to.
 *
 * This asks. The instrument is one line long and needs no new render path:
 *
 *   **a layer's footprint is the set of pixels that change when you hide it.**
 *
 * Hide `structures` and re-photograph the identical pose: every pixel that
 * moved is a pixel a building was the front-most thing in. That is an exact
 * ownership test, not a proxy — occlusion decides it, the same way the depth
 * buffer does. Intersect each layer's footprint with the flicker mask and the
 * 1,108 pixels are partitioned by what is actually drawn there.
 *
 * Two properties make it trustworthy, and both are printed:
 *
 *   - **the footprints are near-disjoint by construction** — a pixel has one
 *     front-most surface — so a large overlap between two layers is a bug in
 *     this tool rather than a finding. The overlap is reported.
 *   - **the unattributed remainder is reported too.** Flicker on a pixel that
 *     no layer owns is flicker on the sky or on the ground dome, and a number
 *     that quietly dropped it would be a partition of the wrong set.
 *
 * The shadow map is switched off for the whole run, by R-BUG6(a)'s repaired
 * control (`shadowMap.enabled` + `needsUpdate` on every material — a compiled
 * flag is not a runtime handle), so the pixels counted here are the ones that
 * parcel could not explain.
 *
 * Defaults to the PUBLISHED mirror, for the reason every other measurement here
 * does: depth precision is a property of the geometry that actually ships.
 *
 * **T-0156 — THE SECOND COLUMN DID NOT MEAN WHAT IT WAS CALLED.** The partition
 * above was split again, into a layer's OUTLINE against the rest of the scene
 * and its INTERIOR, and the interior share was published and quoted as *the
 * layer fighting itself*. It is not: `interiorOf` sees one layer's outline
 * against everything else and is blind to the boundary between two surfaces OF
 * that layer, so one crown behind another and a chimney against its own roof
 * both land in it. T-0013 measured the size of the error with a depth pass —
 * 94-98 % of the "interior" count sits on a depth BREAK, i.e. is a silhouette
 * by any honest reading, and 0 % is a depth reorder or a shading resample
 * (ROADMAP § R-BUG6(c2)) — and the instrument was deliberately NOT changed in
 * the run that measured it, because closing a ticket by rewriting the
 * instrument that measured it is the one move this project does not allow.
 *
 * This is the change, made afterwards and by ADDING rather than by loosening:
 * the surrounded column is reported with its own composition beside it, from
 * the same depth-break discriminator, shared as `tools/depth_field.mjs` so the
 * two instruments cannot answer the question differently. Nothing here is
 * re-thresholded and no baseline moves; the counts are the counts they were,
 * and what changes is that the file now says which of them is a defect.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { decodePng } from './critic_metrics.mjs';
// T-0156: the interior column is SPLIT by what the depth field does there, using
// T-0013's discriminator rather than a second copy of it.
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
const outArg = process.argv.indexOf('--out');
const OUT = outArg > -1 ? path.resolve(process.argv[outArg + 1]) : null;
const stArg = process.argv.indexOf('--station');
const WANT_STATION = stArg > -1 ? process.argv[stArg + 1] : 'from_above';
/**
 * IS THE RESIDUAL PRECISION, OR IS IT GEOMETRY? — the second half of the
 * diagnosis, and the one that decides whether there is a fix at all.
 *
 * A pixel where two surfaces are separated by LESS THAN ONE DEPTH QUANTUM is
 * decided by rounding, and the rounding re-rolls when the camera moves. Give
 * the buffer more quanta and that pixel stops moving. A pixel where two
 * surfaces genuinely meet — a roof against a wall, one building in front of
 * another, a canopy card crossing its neighbour — is a geometric edge, and no
 * amount of precision changes it, because the camera really did resample the
 * edge.
 *
 * So: measure the same nudge twice, once with the near plane multiplied. The
 * pixels that STOP flickering are the ones a fix could reach; the ones that
 * survive are the scene's own edges and are nobody's defect.
 *
 * It needs no change to the shipped renderer, which is the point. `setNearFor`
 * is a pure function of `walker.state.altitude`, so an accessor on that one
 * field moves the near plane and NOTHING else — and `stats().cameraNear` reads
 * back what the render actually used, so the handle is proven live rather than
 * asserted (R-A1's lesson, and R-BUG6(a)'s inert `--no-sun-shadow` before it).
 */
const nsArg = process.argv.indexOf('--near-scale');
const NEAR_SCALE = nsArg > -1 ? Number(process.argv[nsArg + 1]) : 0;
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.TIE_PORT || 4194);
const YEAR = process.env.TIE_YEAR || '1835';
const NUDGE_M = Number(process.env.TIE_NUDGE_M || 0.002);
/** The same threshold `measure_river_edge.mjs` uses, and for the same reason. */
const CHANNEL_EPS = 2;

/** The two aerial stations R-BUG6(a) left numbers on, so this can be compared. */
const STATIONS = {
  from_above: { local_e: 60, local_n: -330, yaw_deg: 0, altitude_m: 175, pitch_deg: -30 },
  descend_main_stem: { local_e: 40, local_n: -150, yaw_deg: 20, altitude_m: 90, pitch_deg: -25 },
  over_the_forks: { local_e: -60, local_n: -60, yaw_deg: 40, altitude_m: 45, pitch_deg: -20 },
};
if (!STATIONS[WANT_STATION]) {
  console.error(`unknown station ${WANT_STATION} — one of ${Object.keys(STATIONS).join(', ')}`);
  process.exit(2);
}

/**
 * THE LAYERS, by the names their own modules give them. `terrain` is split
 * because the ground and the water are the two halves of the bank line and
 * lumping them would hide exactly the question R-BUG1 asked.
 */
const LAYERS = [
  { id: 'structures', match: "o.name === 'structures'" },
  { id: 'streets', match: "o.name === 'streets'" },
  { id: 'trees', match: "o.name === 'trees'" },
  { id: 'flora', match: "o.name === 'flora'" },
  { id: 'water', match: "o.name.startsWith('water__')" },
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
if (OUT) fs.mkdirSync(OUT, { recursive: true });
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}\n`);

const VIEWPORT = process.env.TIE_VIEWPORT === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
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
  const ok = box && box.x === 0 && box.y === 0
    && box.width === VIEWPORT.width && box.height === VIEWPORT.height;
  if (!ok) {
    console.error(`the canvas does not fill the viewport (${JSON.stringify(box)}) — a page `
      + 'capture would not be a frame capture');
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
console.log('the shadow map is OFF for every frame below (R-BUG6(a)\'s repaired control).\n');

async function stand(pose) {
  return page.evaluate(async (p) => {
    const api = window.__chicago4d;
    api.setFly(typeof p.altitude_m === 'number');
    api.walker.teleport(p);
    for (let i = 0; i < 8; i++) await api.capture(4);
    // `cameraNear` reads back what the render actually used, and the depth pass
    // below cannot linearise a window depth without it.
    return { y: api.player.y, drawCalls: api.stats().drawCalls, near: api.stats().cameraNear };
  }, pose);
}

/** Hide (or show) one layer and settle four frames. Returns how many objects moved. */
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

/** Pixels of `a` that differ from `b` by more than the epsilon, as a bitmap. */
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

const pose = STATIONS[WANT_STATION];
const arrived = await stand(pose);

// ---- the flicker, and its control ---------------------------------------- //
const a = await shot();
const still = await shot();
const control = maskOf(a, still);
await stand({ ...pose, local_e: pose.local_e + NUDGE_M });
const b = await shot();
const flicker = maskOf(a, b);
// Back to the base pose: every footprint below is measured against `a`.
await stand(pose);
const base = await shot();
const drift = maskOf(a, base);

/**
 * THE FOOTPRINT SPLIT — and READ WHAT IT IS, BECAUSE IT IS NOT WHAT IT WAS CALLED.
 *
 * A pixel on the EDGE of a layer's footprint is a silhouette — the boundary
 * between this layer and whatever is behind it. A camera that moves at all
 * resamples every such boundary, because the edge crosses the pixel's sample
 * points somewhere new. That is antialiasing working, not a surface fighting,
 * and it is present in every correct renderer ever written.
 *
 * A pixel the footprint surrounds on all eight sides was called the INTERIOR
 * and read as *the layer fighting itself*. **That reading was wrong, and
 * T-0013 measured how wrong** (ROADMAP § R-BUG6(c2)): `interiorOf` knows the
 * layer's outline against the REST OF THE SCENE and cannot see the boundary
 * between two surfaces OF that layer — one crown behind another, a chimney
 * against its own roof, a house against the house behind it. Those are
 * silhouettes too, and 94-98 % of the count was made of them. The number drove
 * a ticket for six days and would have driven the next one.
 *
 * So this function still draws the mask — the geometry of "surrounded by my own
 * footprint" is exactly what an internal edge hides inside — and the depth pass
 * below is what says which of the two a surrounded pixel actually is. T-0156
 * is that repair, and it is done by ADDING a measurement rather than by
 * loosening this one: the interior count is unchanged and is now reported with
 * its own composition beside it.
 */
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

/** How far a pixel actually moved, in 8-bit counts. */
function delta(p) {
  const i = p * 4;
  return Math.max(
    Math.abs(a.data[i] - b.data[i]),
    Math.abs(a.data[i + 1] - b.data[i + 1]),
    Math.abs(a.data[i + 2] - b.data[i + 2]),
  );
}

// ---- one footprint per layer --------------------------------------------- //
const owned = new Uint8Array(flicker.m.length);
const rows = [];
const interiorMask = new Uint8Array(flicker.m.length);
for (const layer of LAYERS) {
  const hidden = await setLayer(layer.match, false);
  const off = await shot();
  await setLayer(layer.match, true);
  const foot = maskOf(a, off);
  const inner = interiorOf(foot, a.width, a.height);
  let mine = 0;
  let overlap = 0;
  let worstInterior = 0;
  let worstEdge = 0;
  // The pixel INDICES, not only the count: the depth pass below classifies them
  // one at a time and cannot do it from a total.
  const interiorPx = [];
  for (let p = 0; p < foot.m.length; p++) {
    if (!foot.m[p]) continue;
    if (!flicker.m[p]) continue;
    mine++;
    if (owned[p]) { overlap++; continue; }
    owned[p] = 1;
    if (inner[p]) {
      interiorPx.push(p);
      interiorMask[p] = 1;
      worstInterior = Math.max(worstInterior, delta(p));
    } else {
      worstEdge = Math.max(worstEdge, delta(p));
    }
  }
  rows.push({
    id: layer.id,
    objects: hidden,
    footprint_px: foot.count,
    flicker_px: mine,
    overlap,
    exclusive: mine - overlap,
    interiorPx,
    interior: interiorPx.length,
    edge: mine - overlap - interiorPx.length,
    worst_interior: worstInterior,
    worst_edge: worstEdge,
  });
}
let unattributed = 0;
for (let p = 0; p < flicker.m.length; p++) if (flicker.m[p] && !owned[p]) unattributed++;


const w = (s, n) => String(s).padStart(n);
console.log(`R-BUG6(b) — who owns the flicker · ${WANT_STATION} · ${VIEWPORT.width}x`
  + `${VIEWPORT.height} · ${NUDGE_M * 1000} mm nudge · eye ${arrived.y.toFixed(1)} m · `
  + `${arrived.drawCalls} draw calls\n`);
console.log(`the frame flickers on ${flicker.count} pixels of ${flicker.m.length}\n`);
console.log('layer          footprint px   its flicker   share   SURROUNDED   outline edge   '
  + 'worst srd / edge');
for (const r of rows) {
  console.log(`${r.id.padEnd(14)} ${w(r.footprint_px, 12)} ${w(r.exclusive, 13)} `
    + `${w((100 * r.exclusive / (flicker.count || 1)).toFixed(1) + ' %', 8)}`
    + `${w(r.interior, 11)} ${w(r.edge, 12)}   ${w(r.worst_interior, 4)} / ${r.worst_edge}`);
}
console.log(`${'unattributed'.padEnd(14)} ${w('-', 12)} ${w(unattributed, 13)} `
  + `${w((100 * unattributed / (flicker.count || 1)).toFixed(1) + ' %', 8)}`);

/**
 * ---- IS A SURROUNDED PIXEL A FIGHT, OR AN EDGE THE FOOTPRINT HID? -------- //
 *
 * The column above is a fact about the FOOTPRINT — this layer is drawn on all
 * eight neighbours — and for six days it was quoted as a fact about the DEPTH.
 * It is not one, and only the depth field can say which. So ask it: photograph
 * a packed-depth pass at the base pose and at the nudged pose, and classify
 * every surrounded-and-flickering pixel by what the depth does there
 * (`tools/depth_field.mjs`, T-0013's discriminator, shared with
 * `tools/diagnose_interior_flicker.mjs` so the two cannot drift apart).
 *
 * The `internal edge` column is a SILHOUETTE by any honest reading and belongs
 * with the outline column, not against it. `depth reorder` and `same surface`
 * are the two ways a layer can actually fight itself, and their sum is the only
 * number in this file that ever meant what "interior" was taken to mean.
 *
 * Printed only when the pass puts the frame back exactly, because a depth swap
 * that leaves a mark would be classifying the instrument.
 */
const classes = new Map();
{
  await swapDepthMaterials(page, true);
  await stand(pose);
  const d0 = await shot();
  await stand({ ...pose, local_e: pose.local_e + NUDGE_M });
  const d1 = await shot();
  await stand(pose);
  await swapDepthMaterials(page, false);
  const back = maskOf(a, await shot());
  if (back.count) {
    console.log(`\nthe depth pass did not put the frame back (${back.count} px) — the split of `
      + 'the surrounded column would be measuring the instrument, so it is not printed');
  } else {
    const lin0 = lineariseDepth(d0, arrived.near, FAR_M);
    const lin1 = lineariseDepth(d1, arrived.near, FAR_M);
    console.log('\nWHAT THE DEPTH FIELD DOES AT EACH SURROUNDED PIXEL — the split T-0156 asked '
      + 'for');
    console.log('layer        surrounded   internal edge   depth reorder   same surface   '
      + 'no depth');
    for (const r of rows) {
      const c = classifyDepth(r.interiorPx, lin0, lin1, a.width);
      classes.set(r.id, c);
      const pc = (n) => `${String(n).padStart(4)} `
        + `${String(`(${(100 * n / (r.interior || 1)).toFixed(0)}%)`).padStart(6)}`;
      console.log(`${r.id.padEnd(12)} ${String(r.interior).padStart(8)}   ${pc(c.break.length)}`
        + `    ${pc(c.reorder.length)}   ${pc(c.smooth.length)}  ${String(c.sky.length).padStart(4)}`);
    }
    console.log(`\n  internal edge  = a depth BREAK (second difference > ${BREAK_M} m) inside the `
      + "layer's own footprint:\n                   one surface of the layer in front of another, "
      + 'which any camera resamples.\n  depth reorder  = locally smooth depth, front-most surface '
      + `${REORDER_M} m+ further or nearer after the\n                   nudge — two surfaces `
      + 'swapped. This is the fight the column was read as.\n  same surface   = same distance, '
      + 'same shape, different colour — shading, not geometry;\n                   a near-coplanar '
      + 'pair swaps without moving the depth, so it lands here.\n  no depth       = the packed '
      + 'depth does not decode: more than one surface in the pixel,\n                   which is an '
      + 'edge again (a packed depth blended through MSAA is not linear).');
  }
}
/**
 * ---- IS ANYTHING ACTUALLY CO-PLANAR? ------------------------------------- //
 *
 * The discriminator the two above cannot give, and it is one line of WebGL.
 *
 * three.js draws with `LessEqualDepth`, so where two surfaces have EXACTLY the
 * same depth the one drawn second wins. Switch the test to `LessDepth` and the
 * one drawn FIRST wins — at exactly-equal depths, and **nowhere else**. Every
 * other pixel in the frame is decided by a strict inequality and cannot notice
 * the change.
 *
 * So the set of pixels that move under that switch IS the set of pixels where
 * two surfaces are exactly co-planar. No precision argument, no threshold, no
 * proxy: it is the definition of the thing, asked of the renderer directly.
 * Intersect it with the flicker mask and the ROADMAP's claim is settled.
 */
const coplanar = await (async () => {
  const flipped = await page.evaluate(async () => {
    const api = window.__chicago4d;
    const seen = new Set();
    api.scene3d.traverse((o) => {
      const m = o.material;
      if (!m) return;
      for (const one of Array.isArray(m) ? m : [m]) {
        if (seen.has(one.uuid)) continue;
        seen.add(one.uuid);
        one.depthFunc = 2; // THREE.LessDepth
        one.needsUpdate = true;
      }
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
    return seen.size;
  });
  const strict = await shot();
  await page.evaluate(async () => {
    const api = window.__chicago4d;
    const seen = new Set();
    api.scene3d.traverse((o) => {
      const m = o.material;
      if (!m) return;
      for (const one of Array.isArray(m) ? m : [m]) {
        if (seen.has(one.uuid)) continue;
        seen.add(one.uuid);
        one.depthFunc = 3; // THREE.LessEqualDepth, three's default
        one.needsUpdate = true;
      }
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
  });
  const restored = await shot();
  const mask = maskOf(a, strict);
  const back = maskOf(a, restored);
  let onFlicker = 0;
  let onInterior = 0;
  for (let p = 0; p < mask.m.length; p++) {
    if (!mask.m[p]) continue;
    if (flicker.m[p]) onFlicker++;
    if (interiorMask[p]) onInterior++;
  }
  return { materials: flipped, count: mask.count, onFlicker, onInterior, restored: back.count };
})();

// ---- the precision experiment -------------------------------------------- //
let nearRow = null;
if (NEAR_SCALE > 1) {
  const nearBefore = await page.evaluate(() => window.__chicago4d.stats().cameraNear);
  // The shipped `NEAR.max` cap binds at these altitudes, so scaling the altitude
  // that feeds `setNearFor` moves the near plane by 14 % and tests nothing. The
  // accessor goes on `camera.near` itself, which is downstream of the cap.
  const applied = await page.evaluate(async (k) => {
    const cam = window.__chicago4d.camera;
    let real = cam.near;
    Object.defineProperty(cam, 'near', {
      get: () => real * k,
      set: (v) => { real = v; },
      configurable: true,
    });
    cam.updateProjectionMatrix();
    for (let i = 0; i < 4; i++) await window.__chicago4d.capture(4);
    return window.__chicago4d.stats().cameraNear;
  }, NEAR_SCALE);
  if (!(applied > nearBefore)) {
    console.error(`the near plane did not move (${nearBefore} -> ${applied}) — the precision `
      + 'experiment tests nothing');
    process.exit(2);
  }
  await stand(pose);
  const a2 = await shot();
  await stand({ ...pose, local_e: pose.local_e + NUDGE_M });
  const b2 = await shot();
  const flicker2 = maskOf(a2, b2);
  // Does the picture itself survive the change? A near plane that clipped
  // something would "fix" the flicker by deleting the surface that flickered.
  const clipped = maskOf(a, a2);
  let stillInterior = 0;
  let healedInterior = 0;
  for (let p = 0; p < interiorMask.length; p++) {
    if (!interiorMask[p]) continue;
    if (flicker2.m[p]) stillInterior++; else healedInterior++;
  }
  nearRow = {
    near_before: nearBefore,
    near_after: applied,
    frame_before: flicker.count,
    frame_after: flicker2.count,
    interior_before: interiorMask.reduce((s, v) => s + v, 0),
    still: stillInterior,
    healed: healedInterior,
    picture_changed_px: clipped.count,
  };
}

await browser.close();
server.close();

if (OUT) {
  const CRC = (() => {
    const t = new Int32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c;
    }
    return (buf) => {
      let c = -1;
      for (let i = 0; i < buf.length; i++) c = t[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
      return (c ^ -1) >>> 0;
    };
  })();
  const chunk = (type, body) => {
    const head = Buffer.alloc(8);
    head.writeUInt32BE(body.length, 0);
    head.write(type, 4, 'ascii');
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(CRC(Buffer.concat([Buffer.from(type, 'ascii'), body])), 0);
    return Buffer.concat([head, body, crc]);
  };
  const writePng = (file, img) => {
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(img.width, 0);
    ihdr.writeUInt32BE(img.height, 4);
    ihdr[8] = 8; ihdr[9] = 6;
    const stride = img.width * 4;
    const raw = Buffer.alloc((stride + 1) * img.height);
    for (let y = 0; y < img.height; y++) {
      raw[y * (stride + 1)] = 0;
      Buffer.from(img.data.buffer, img.data.byteOffset + y * stride, stride)
        .copy(raw, y * (stride + 1) + 1);
    }
    fs.writeFileSync(file, Buffer.concat([
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0)),
    ]));
  };
  // Green is an outline edge, magenta an edge the footprint HID, red a genuine
  // self-fight: the three colours are the finding, and they do not need a
  // caption to tell apart. Before T-0156 the magenta and the red were one
  // colour and the picture asserted the reading the depth pass refutes.
  const fightMask = new Uint8Array(flicker.m.length);
  for (const c of classes.values()) {
    for (const p of c.reorder) fightMask[p] = 1;
    for (const p of c.smooth) fightMask[p] = 1;
  }
  const paint = new Uint8Array(a.data);
  for (let p = 0; p < flicker.m.length; p++) {
    if (!flicker.m[p]) continue;
    const i = p * 4;
    if (fightMask[p]) { paint[i] = 255; paint[i + 1] = 0; paint[i + 2] = 0; }
    else if (interiorMask[p]) { paint[i] = 255; paint[i + 1] = 0; paint[i + 2] = 255; }
    else { paint[i] = 0; paint[i + 1] = 255; paint[i + 2] = 0; }
  }
  writePng(path.join(OUT, `${WANT_STATION}.png`), a);
  writePng(path.join(OUT, `${WANT_STATION}-ties.png`), { width: a.width, height: a.height, data: paint });
  console.log(`\nmasks written to ${OUT} — green is an outline edge, magenta an edge the `
    + 'footprint hid, red a self-fight.');
}
const interiorTotal = rows.reduce((s, r) => s + r.interior, 0);
console.log(`\nSURROUNDED TOTAL: ${interiorTotal} of ${flicker.count} `
  + `(${(100 * interiorTotal / (flicker.count || 1)).toFixed(1)} %) — the pixels a layer's own `
  + 'footprint\nsurrounds. The rest is its outline against the next layer, which any camera '
  + 'movement resamples.');
if (classes.size) {
  const sum = (k) => rows.reduce((t, r) => t + (classes.get(r.id)?.[k].length ?? 0), 0);
  const edges = sum('break') + sum('sky');
  const fight = sum('reorder') + sum('smooth');
  console.log(`  of which INTERNAL EDGES: ${edges} `
    + `(${(100 * edges / (interiorTotal || 1)).toFixed(0)} %) — silhouettes the footprint hid, `
    + 'and not a defect.');
  console.log(`  of which SELF-FIGHT:     ${fight} `
    + `(${(100 * fight / (interiorTotal || 1)).toFixed(0)} %) — a depth reorder or a shading `
    + 'resample.\n  The second number is the one this instrument was read as reporting all '
    + 'along (T-0156).');
}

console.log(`\nEXACTLY CO-PLANAR? — the depth test switched from LessEqual to Less across all `
  + `${coplanar.materials} materials,\nwhich can change a pixel only where two surfaces have `
  + 'exactly the same depth:');
console.log(`  the switch moves           ${coplanar.count} px of the frame`);
console.log(`  of which flickering        ${coplanar.onFlicker} px `
  + `(${(100 * coplanar.onFlicker / (flicker.count || 1)).toFixed(1)} % of the flicker)`);
console.log(`  of which surrounded        ${coplanar.onInterior} px`);
console.log(`  switching it back restores the frame to within ${coplanar.restored} px `
  + '(0 = the control is sound)');

if (nearRow) {
  console.log(`\nTHE PRECISION EXPERIMENT — near plane ${nearRow.near_before} m -> `
    + `${nearRow.near_after} m, same pose, same nudge:`);
  console.log(`  whole frame        ${nearRow.frame_before} -> ${nearRow.frame_after} px`);
  console.log(`  interior ties      ${nearRow.interior_before}: ${nearRow.healed} stop moving, `
    + `${nearRow.still} survive`);
  console.log(`  the picture itself changed on ${nearRow.picture_changed_px} px — anything large `
    + 'here means the near plane CLIPPED something\n  and the comparison is void.');
}

console.log(`\ncontrol — the same pose photographed twice, nothing moved: ${control.count} px`);
console.log(`return  — back to the base pose after the nudge: ${drift.count} px`);
if (control.count || drift.count) {
  console.log('\nUNSOUND: the harness does not reproduce its own frame, so the partition above '
    + 'is\nmeasuring noise as well as ties.');
}
if (errors.length) console.log(`\npage errors: ${errors.length}\n - ${errors.slice(0, 5).join('\n - ')}`);
if (control.count || drift.count || errors.length) process.exit(2);
