/**
 * T-0157 — WHAT A PHONE'S EDGES DO WITHOUT MULTISAMPLING, AND WHAT MSAA COSTS IT.
 *
 *   node tools/measure_phone_aa.mjs [--source] [--desktop] [--edges] [--cost]
 *        [--stations a,b,c] [--frames N] [--warmup N] [--ratio N] [--json]
 *
 * `main.js` boots with `antialias: !coarse`, so a touch device draws with no
 * multisampling at all. T-0013 established what an unsampled edge costs: every
 * one of the 627 interior-flickering pixels at `from_above` is an edge internal
 * to a layer, supersampling healed 83–93 % of them, and a shading change that
 * moved 164,572 px healed none. Those readings were all taken at 1280×800 on
 * the DESKTOP boot, which has MSAA on. Nobody had read the phone.
 *
 * This reads the phone, and it refuses to read anything else. Three choices
 * carry the whole instrument, and each one closes a way this could lie:
 *
 *   THE PAGE IS BOOTED AS A PHONE, NOT MERELY SIZED AS ONE. `prefersTouch()` is
 *   `(pointer: coarse)` or `maxTouchPoints > 0 && innerWidth < 900` — a viewport
 *   alone satisfies neither. `tools/measure_tie_class.mjs`'s `TIE_VIEWPORT=mobile`
 *   opens a plain `newPage({ viewport })`, so it boots the DESKTOP renderer at a
 *   phone's size: `antialias: true`, `detail: full`, the pointer-lock backend.
 *   Every reading below comes from a context with `hasTouch: true` and
 *   `deviceScaleFactor: 2`, which is what `tools/smoke_renderer.mjs` — the
 *   release gate — uses for its mobile half, and the run PRINTS the three
 *   readings that prove the coarse path took (`pointer: coarse`, the resolved
 *   detail level, and the renderer's own pixel ratio).
 *
 *   THE TOGGLE IS PROVEN LIVE, NOT ASSERTED. `antialias` is a context-creation
 *   attribute: there is no runtime handle on it, so the only honest control is
 *   to create the context differently. An init script wraps
 *   `HTMLCanvasElement.prototype.getContext` and rewrites the one attribute
 *   before three.js ever sees it. It is then read BACK out of the live context —
 *   `getContextAttributes().antialias` AND `gl.getParameter(gl.SAMPLES)` — and
 *   the run aborts if the two disagree with what was asked for. R-A1's inert
 *   readback and R-BUG6(a)'s inert `--no-sun-shadow` are both in this project's
 *   history; a control that does not reach the render is worse than no control.
 *
 *   THE COST IS TIMED THE WAY THIS PROJECT TIMES COSTS. `tools/measure_shrub_
 *   frame_cost.mjs` established the method and it is followed exactly: the clock
 *   is held, `setAnimationLoop(null)` so rAF's display pacing is not what gets
 *   measured, and a one-pixel `readPixels` every frame as a real fence — a
 *   `gl.finish()` alone reported 2.9 ms a frame while the process took a second
 *   of wall clock, because ANGLE's SwiftShader backend does the work in another
 *   process. And the passes run **A/B/A** — off, on, off — because a shared
 *   runner drifts, and a single before/after cannot tell the drift from the
 *   change. That is the v252 discipline (4282 → 4410 ms, timed twice).
 *
 * WHAT THE MILLISECONDS ARE AND ARE NOT. Chromium headless here draws through
 * SwiftShader, a SOFTWARE rasteriser, and the device string is printed with
 * every table so no figure can be quoted without it. A software rasteriser
 * resolves MSAA on the CPU, so it is the harshest possible witness for this
 * particular question: 4× coverage samples are close to 4× the rasterisation
 * work with no hardware compression to hide it. A phone's GPU has dedicated
 * MSAA resolve hardware and tile memory, and pays a far smaller fraction. So a
 * cost measured here is an UPPER bound and must be reported as one — the number
 * that would be dishonest is a cheap reading, not an expensive one.
 *
 * WHAT THE EDGE COUNTS ARE. The 2 mm camera nudge of R-BUG1, partitioned by
 * `measure_tie_class.mjs`'s ownership rule — a layer's footprint is the set of
 * pixels that change when you hide it — with the shadow map switched off by
 * R-BUG6(a)'s repaired control so the residual is the residual. `interior` and
 * `silhouette` are that tool's columns and are printed here with T-0013's
 * correction attached: `interiorOf` knows a layer's outline against the REST of
 * the scene and cannot see the boundary between two surfaces OF that layer, so
 * 94–98 % of an "interior" count is internal silhouette. The column is exact
 * about ownership and loose about cause, and is quoted on those terms.
 *
 * AND ONE MORE CAVEAT, MEASURED HERE AND NOT PREVIOUSLY KNOWN, because the
 * ownership test had only ever been run from the air. `measure_tie_class.mjs`
 * warns that a large overlap between two layers is a bug in the tool rather
 * than a finding, and at `from_above` the overlaps are small (0–310 of 1,056).
 * At EYE HEIGHT they are not: at `lake_market` the ground's footprint overlaps
 * the streets' on 2,436 of its 2,607 flickering pixels, because the street
 * layer is a skin ON the heightfield and hiding either moves the same pixels.
 * Every pixel is still counted exactly once — `owned` is what splits — but
 * which of those two layers gets the credit is decided by the LAYERS list order
 * rather than by occlusion. So the eye-height `streets`/`ground` split is not
 * an ownership claim. The frame totals below are attribution-free and are what
 * this ticket's conclusion rests on.
 *
 * AND A SEVERITY COLUMN, because a pixel count alone cannot answer this ticket.
 * MSAA does not make an edge stop resampling — the camera really did move — it
 * makes the resample PARTIAL. So the count of pixels that changed at all can
 * stay flat, or even rise, while the picture gets dramatically calmer. `worst`
 * and `mean` are the 8-bit distances those pixels moved, and `flips` counts the
 * ones that moved by 64 counts or more: a quarter of the range is a pixel that
 * swapped which surface it was showing rather than shifting its coverage a
 * little, and a field of those flipping under a walking camera is what crawl
 * looks like. Both are reported beside the raw count, never instead of it.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { decodePng } from './critic_metrics.mjs';

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
const argv = process.argv.slice(2);
const flagVal = (name, dflt) => {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : dflt;
};
const wantSource = argv.includes('--source');
const wantJson = argv.includes('--json');
/** Both halves by default; either alone while iterating. */
const doEdges = argv.includes('--edges') || !argv.includes('--cost');
const doCost = argv.includes('--cost') || !argv.includes('--edges');
const FRAMES = Number(flagVal('--frames', 14));
const WARMUP = Number(flagVal('--warmup', 4));
const DESKTOP = argv.includes('--desktop');
/**
 * `--ratio N` — time the cost half at a pixel ratio the visitor could choose,
 * rather than only at the one the page booted into.
 *
 * It exists because "there is a control in Settings if your phone cannot afford
 * this" is a CLAIM until somebody times it. Render quality is a shipped visitor
 * setting with three stops (1 / 1.5 / 2, `hud.js DEFAULT_SETTINGS.quality`), the
 * default is 1.5 on both platforms, and dropping it to 1 cuts the pixels being
 * multisampled by 56 %. `renderer.setPixelRatio` resizes the drawing buffer
 * itself in three r0.185.1, so this needs no reboot and no shipped change — and
 * the ratio is read BACK off the renderer before any frame is timed.
 */
const RATIOS = flagVal('--ratio', '') === ''
  ? [null]
  : flagVal('--ratio', '').split(',').map((v) => Number(v.trim()));
if (RATIOS.some((r) => r !== null && !(r > 0))) {
  console.error(`--ratio takes one or more positive numbers, got "${flagVal('--ratio', '')}"`);
  process.exit(2);
}

const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.AA_PORT || 4196);
const YEAR = process.env.AA_YEAR || '1835';
const NUDGE_M = Number(process.env.AA_NUDGE_M || 0.002);
/** The same threshold `measure_tie_class.mjs` and `measure_river_edge.mjs` use. */
const CHANNEL_EPS = 2;
/** A quarter of the 8-bit range: a pixel that moved this far swapped surfaces. */
const FLIP_EPS = 64;

/**
 * THE RELEASE VIEWPORT, and the two attributes that make it a phone rather than
 * a narrow window. `isMobile` is left false for the same reason the smoke leaves
 * it false — it forces Chromium-side mobile emulation, which changes far more
 * than this measurement is about.
 */
const VIEWPORT = DESKTOP
  ? { label: 'desktop 1280x800', viewport: { width: 1280, height: 800 }, hasTouch: false, deviceScaleFactor: 1 }
  : { label: 'mobile 390x780', viewport: { width: 390, height: 780 }, hasTouch: true, deviceScaleFactor: 2 };

/**
 * THE EDGE STATIONS.
 *
 * `from_above` is T-0013's station, unchanged, so the mobile numbers can be set
 * beside the desktop ones this ticket was opened against. `lake_market` is a
 * scene anchor at EYE HEIGHT — the corner of Lake and Market — because that is
 * where a visitor on a phone actually stands, and an aerial frame is a different
 * question about the same renderer.
 */
const EDGE_STATIONS = [
  { id: 'from_above', pose: { local_e: 60, local_n: -330, yaw_deg: 0, altitude_m: 175, pitch_deg: -30 } },
  { id: 'lake_market', pose: { local_e: 89.2, local_n: -110.4, yaw_deg: 135 } },
];

/** The layers, by the names their own modules give them — `measure_tie_class.mjs`. */
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

/** The stations the cost half stands at: the scene's own anchors, in order. */
const scene = JSON.parse(fs.readFileSync(
  path.join(HERE, '..', 'data', 'scenes', `${YEAR}.json`), 'utf8'));
const PICK = flagVal('--stations', '').split(',').map((s) => s.trim()).filter(Boolean);
const unknown = PICK.filter((id) => !scene.anchors.some((a) => a.id === id));
if (unknown.length) {
  console.error(`unknown station(s): ${unknown.join(', ')}`);
  console.error(`known: ${scene.anchors.map((a) => a.id).join(', ')}`);
  process.exit(2);
}
const COST_STATIONS = (PICK.length ? scene.anchors.filter((a) => PICK.includes(a.id)) : scene.anchors)
  .map((a) => ({ id: a.id, label: a.label }));

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const log = (...a) => { if (!wantJson) console.log(...a); };
log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}`);
log(`${VIEWPORT.label}, hasTouch=${VIEWPORT.hasTouch}, deviceScaleFactor=${VIEWPORT.deviceScaleFactor}\n`);

const errors = [];

/**
 * One page, booted with the WebGL context's `antialias` forced to `want`, and
 * the forcing PROVEN against the live context before anything is measured.
 */
async function openWith(want, { forCapture }) {
  const ctx = await browser.newContext({
    viewport: VIEWPORT.viewport,
    hasTouch: VIEWPORT.hasTouch,
    isMobile: false,
    deviceScaleFactor: VIEWPORT.deviceScaleFactor,
  });
  const page = await ctx.newPage();
  // Playwright's default 30 s action timeout is not an assertion and on this
  // scene it becomes one: a click queues behind the render loop, and a frame
  // here takes 2–6 s on a software rasteriser. `smoke_renderer.mjs` raised its
  // own budget to 90 s for exactly this reason, and the gate click in this tool
  // died at 30 s on a busy runner having already landed the click. Ninety
  // seconds is room for a slow machine, not permission for a broken control.
  page.setDefaultTimeout(90_000);
  page.on('pageerror', (e) => errors.push(`antialias=${want}: ${String(e)}`));
  await page.addInitScript((aa) => {
    const orig = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function getContext(type, attrs) {
      if (/webgl/i.test(String(type))) {
        return orig.call(this, type, { ...(attrs || {}), antialias: aa });
      }
      return orig.call(this, type, attrs);
    };
  }, want);
  await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load', timeout: 240_000 });
  if (forCapture) {
    // Hold the clock before `ready`, so no two frames below differ by the wind.
    await page.waitForFunction(() => {
      const api = window.__chicago4d;
      if (typeof api?.setAnimationHold !== 'function') return false;
      api.setAnimationHold(true);
      return true;
    }, null, { polling: 'raf', timeout: 240_000 });
  }
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240_000 });

  const seen = await page.evaluate(() => {
    const api = window.__chicago4d;
    const gl = api.renderer.getContext();
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    return {
      antialias: gl.getContextAttributes().antialias,
      samples: gl.getParameter(gl.SAMPLES),
      pixelRatio: api.renderer.getPixelRatio(),
      devicePixelRatio: window.devicePixelRatio,
      coarse: window.matchMedia('(pointer: coarse)').matches,
      maxTouchPoints: navigator.maxTouchPoints,
      detail: api.detail,
      device: String(dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)),
    };
  });
  // The control has to have reached the render. `antialias: true` with SAMPLES
  // 0 is a context that silently refused the request, and every number taken
  // after it would be a second reading of the same frame.
  if (seen.antialias !== want || (want && seen.samples < 2) || (!want && seen.samples !== 0)) {
    console.error(`the antialias control did not take: asked for ${want}, the live context `
      + `reports antialias=${seen.antialias} SAMPLES=${seen.samples}`);
    process.exit(2);
  }
  // And the page has to have booted as a PHONE, or this is the desktop reading
  // again in a narrow window — which is the exact defect this tool exists past.
  if (!DESKTOP && !seen.coarse) {
    console.error('the page did not boot on the coarse path — (pointer: coarse) is false');
    process.exit(2);
  }
  return { ctx, page, seen };
}

// ---- the edge half -------------------------------------------------------- //

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

/** `measure_tie_class.mjs`'s discriminator, unchanged — see the caveat above. */
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

async function measureEdges(page, station) {
  const shot = async () => decodePng(await page.screenshot());

  const stand = async (pose) => page.evaluate(async (p) => {
    const api = window.__chicago4d;
    api.setFly(typeof p.altitude_m === 'number');
    api.walker.teleport(p);
    for (let i = 0; i < 8; i++) await api.capture(4);
  }, pose);

  const setLayer = async (match, visible) => page.evaluate(async ({ src, want }) => {
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

  await stand(station.pose);
  const a = await shot();
  const still = await shot();
  const control = maskOf(a, still);
  await stand({ ...station.pose, local_e: station.pose.local_e + NUDGE_M });
  const b = await shot();
  const flicker = maskOf(a, b);
  await stand(station.pose);
  const drift = maskOf(a, await shot());

  const delta = (p) => {
    const i = p * 4;
    return Math.max(
      Math.abs(a.data[i] - b.data[i]),
      Math.abs(a.data[i + 1] - b.data[i + 1]),
      Math.abs(a.data[i + 2] - b.data[i + 2]),
    );
  };

  const owned = new Uint8Array(flicker.m.length);
  const rows = [];
  for (const layer of LAYERS) {
    const objects = await setLayer(layer.match, false);
    const off = await shot();
    await setLayer(layer.match, true);
    const foot = maskOf(a, off);
    const inner = interiorOf(foot, a.width, a.height);
    let mine = 0; let overlap = 0; let interior = 0; let silhouette = 0;
    let flips = 0; let sum = 0; let worst = 0;
    for (let p = 0; p < foot.m.length; p++) {
      if (!foot.m[p] || !flicker.m[p]) continue;
      mine++;
      if (owned[p]) { overlap++; continue; }
      owned[p] = 1;
      const d = delta(p);
      sum += d;
      worst = Math.max(worst, d);
      if (d >= FLIP_EPS) flips++;
      if (inner[p]) interior++; else silhouette++;
    }
    rows.push({
      id: layer.id,
      objects,
      footprint_px: foot.count,
      flicker_px: mine,
      overlap_px: overlap,
      interior,
      silhouette,
      flips,
      mean_delta: mine - overlap ? sum / (mine - overlap) : 0,
      worst_delta: worst,
    });
  }
  let unattributed = 0; let allFlips = 0; let allSum = 0;
  for (let p = 0; p < flicker.m.length; p++) {
    if (!flicker.m[p]) continue;
    const d = delta(p);
    allSum += d;
    if (d >= FLIP_EPS) allFlips++;
    if (!owned[p]) unattributed++;
  }
  return {
    station: station.id,
    frame_px: a.width * a.height,
    width: a.width,
    height: a.height,
    control_px: control.count,
    return_px: drift.count,
    flicker_px: flicker.count,
    flips_px: allFlips,
    mean_delta: flicker.count ? allSum / flicker.count : 0,
    unattributed,
    rows,
  };
}

// ---- the cost half -------------------------------------------------------- //

async function measureCost(page, stations, frames, warmup, ratio) {
  return page.evaluate(async ({ stations, frames, warmup, ratio }) => {
    const api = window.__chicago4d;
    api.setAnimationHold(true);
    api.renderer.setAnimationLoop(null);
    if (ratio !== null) {
      api.renderer.setPixelRatio(ratio);
      const got = api.renderer.getPixelRatio();
      if (got !== ratio) return { error: `asked for pixelRatio ${ratio}, renderer reports ${got}` };
    }
    const gl = api.renderer.getContext();
    const px = new Uint8Array(4);
    // `step()` returns when the commands are SUBMITTED. A one-pixel readback is
    // a real fence; a bare `gl.finish()` is not, on an out-of-process backend.
    const drawAndWait = () => {
      api.step();
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
      gl.finish();
    };
    const out = [];
    for (const st of stations) {
      if (!api.goTo(st.id)) return { error: `no anchor ${st.id}` };
      for (let i = 0; i < warmup; i++) drawAndWait();
      const ms = [];
      for (let i = 0; i < frames; i++) {
        const t0 = performance.now();
        drawAndWait();
        ms.push(performance.now() - t0);
      }
      ms.sort((x, y) => x - y);
      const at = (q) => ms[Math.min(ms.length - 1, Math.floor(q * ms.length))];
      const s = api.stats();
      out.push({
        id: st.id,
        median: at(0.5), p05: at(0.05), p95: at(0.95),
        mean: ms.reduce((t, v) => t + v, 0) / ms.length,
        triangles: s.triangles, drawCalls: s.drawCalls,
      });
    }
    return { rows: out, pixelRatio: api.renderer.getPixelRatio() };
  }, { stations, frames, warmup, ratio: ratio ?? null });
}

// ---- run ------------------------------------------------------------------ //

const result = { viewport: VIEWPORT.label, published: !wantSource, nudge_m: NUDGE_M, edges: [], cost: [], boot: {} };

if (doEdges) {
  for (const want of [false, true]) {
    const { ctx, page, seen } = await openWith(want, { forCapture: true });
    result.boot[want ? 'on' : 'off'] = seen;
    log(`antialias=${want} — SAMPLES ${seen.samples} · pixelRatio ${seen.pixelRatio} of dpr `
      + `${seen.devicePixelRatio} · detail "${seen.detail}" · pointer:coarse ${seen.coarse}`);
    // R-BUG6(a)'s repaired control: the flag AND a rebuild of every program.
    const shadowOn = await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.renderer.shadowMap.enabled = false;
      api.scene3d.traverse((o) => {
        const m = o.material;
        if (!m) return;
        for (const one of Array.isArray(m) ? m : [m]) one.needsUpdate = true;
      });
      for (let i = 0; i < 4; i++) await api.capture(4);
      return api.renderer.shadowMap.enabled;
    });
    if (shadowOn !== false) {
      console.error('the shadow map would not switch off — the residual is not the residual');
      process.exit(2);
    }
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
    const box = await canvas.boundingBox();
    if (!(box && box.x === 0 && box.y === 0
      && box.width === VIEWPORT.viewport.width && box.height === VIEWPORT.viewport.height)) {
      console.error(`the canvas does not fill the viewport (${JSON.stringify(box)}) — a page `
        + 'capture would not be a frame capture');
      process.exit(2);
    }
    for (const station of EDGE_STATIONS) {
      const r = await measureEdges(page, station);
      result.edges.push({ antialias: want, ...r });
      log(`  ${station.id}: ${r.flicker_px} px flicker, ${r.flips_px} hard flips, `
        + `control ${r.control_px}, return ${r.return_px}`);
    }
    await ctx.close();
  }
}

if (doCost) {
  // A/B/A. The second `false` is not a repeat for its own sake: it is how the
  // runner's own drift between two minutes is told apart from the change.
  for (const [pass, want] of [['A off', false], ['B on', true], ['A2 off', false]]) {
    const { ctx, page, seen } = await openWith(want, { forCapture: false });
    result.boot[pass] = seen;
    log(`\n${pass} — SAMPLES ${seen.samples} · pixelRatio ${seen.pixelRatio} of dpr `
      + `${seen.devicePixelRatio} · detail "${seen.detail}" · pointer:coarse ${seen.coarse}`);
    log(`   ${seen.device}`);
    // Both ratios inside ONE page load. The runner drifted 26 % across the
    // three passes of the first run of this tool, so two ratios compared across
    // two commands would be comparing the machine's afternoon; compared minutes
    // apart on the same page they are comparing the ratio.
    for (const ratio of RATIOS) {
      const r = await measureCost(page, COST_STATIONS, FRAMES, WARMUP, ratio);
      if (r.error) { console.error(r.error); process.exit(2); }
      log(`   timing at pixelRatio ${r.pixelRatio}`);
      result.cost.push({
        pass, antialias: want, device: seen.device, pixelRatio: r.pixelRatio, rows: r.rows,
      });
      for (const row of r.rows) log(`  ${row.id.padEnd(26)} ${row.median.toFixed(1).padStart(8)} ms`);
    }
    await ctx.close();
  }
}

await browser.close();
server.close();
result.errors = errors;

if (wantJson) {
  console.log(JSON.stringify(result, null, 2));
} else {
  if (result.edges.length) {
    console.log('\n\nTHE EDGE, UNDER A 2 MM NUDGE — shadow map off, clock held\n');
    for (const station of EDGE_STATIONS) {
      const off = result.edges.find((e) => e.station === station.id && !e.antialias);
      const on = result.edges.find((e) => e.station === station.id && e.antialias);
      if (!off || !on) continue;
      console.log(`${station.id} — ${off.width}x${off.height} px of frame buffer`);
      console.log(`  control ${off.control_px}/${on.control_px} px · return to base `
        + `${off.return_px}/${on.return_px} px (off/on; both must read 0)`);
      console.log('');
      // `flicker` is every flickering pixel in this layer's footprint; `owned`
      // is the ones no earlier layer had already claimed, and it is `owned` that
      // splits into interior + silhouette. Printing `overlap` is what makes the
      // row add up — and a LARGE overlap is a bug in the ownership test rather
      // than a finding, which is `measure_tie_class.mjs`'s own warning.
      console.log('  layer          footprint    flicker  overlap    owned  interior  silhouette'
        + '   flips  mean d  worst');
      console.log('  ------------  ----------  ---------  -------  -------  --------  ----------'
        + '  ------  ------  -----');
      for (const which of [['antialias OFF (as shipped before T-0157)', off], ['antialias ON', on]]) {
        console.log(`  ${which[0]}`);
        for (const r of which[1].rows) {
          console.log(`  ${r.id.padEnd(12)}  ${String(r.footprint_px).padStart(10)}  `
            + `${String(r.flicker_px).padStart(9)}  ${String(r.overlap_px).padStart(7)}  `
            + `${String(r.flicker_px - r.overlap_px).padStart(7)}  ${String(r.interior).padStart(8)}  `
            + `${String(r.silhouette).padStart(10)}  ${String(r.flips).padStart(6)}  `
            + `${r.mean_delta.toFixed(1).padStart(6)}  ${String(r.worst_delta).padStart(5)}`);
        }
        // The frame's own totals, which are NOT the column sums: a pixel counted
        // in two footprints is one flickering pixel, and `unattributed` is the
        // flicker no layer owns — sky, and the frame's outermost ring.
        console.log(`  ${'THE FRAME'.padEnd(12)}  ${''.padStart(10)}  `
          + `${String(which[1].flicker_px).padStart(9)}  ${''.padStart(7)}  ${''.padStart(7)}  `
          + `${''.padStart(8)}  ${''.padStart(10)}  `
          + `${String(which[1].flips_px).padStart(6)}  ${which[1].mean_delta.toFixed(1).padStart(6)}`
          + `   (unattributed ${which[1].unattributed})`);
      }
      const dFlick = on.flicker_px - off.flicker_px;
      const dFlip = on.flips_px - off.flips_px;
      const pct = (n, d) => (d ? `${(100 * n / d).toFixed(1)} %` : '—');
      console.log(`\n  MSAA moves the flicker count by ${dFlick >= 0 ? '+' : ''}${dFlick} `
        + `(${pct(dFlick, off.flicker_px)}) and the HARD FLIPS by ${dFlip >= 0 ? '+' : ''}${dFlip} `
        + `(${pct(dFlip, off.flips_px)})\n`);
    }
  }
  if (result.cost.length) {
    console.log(`\nTHE COST, ${FRAMES} timed frames after ${WARMUP} warm-up, clock held, `
      + 'readPixels fence each frame');
    console.log(`drawn through ${result.cost[0].device}`);
    console.log('SOFTWARE RASTERISER — MSAA resolves on the CPU here, so this is an UPPER '
      + 'bound on a phone GPU');
    const ids = COST_STATIONS.map((s) => s.id);
    const totals = new Map();
    for (const pr of [...new Set(result.cost.map((c) => c.pixelRatio))]) {
      console.log(`\npixel ratio ${pr}`
        + `${RATIOS[0] === null ? ' (as the page booted)' : ' (set with --ratio)'}`);
      console.log('station                       A off      B on     A2 off    B vs mean(A)   drift A→A2');
      console.log('--------------------------  --------  --------  --------  --------------  ----------');
      const at = (p) => result.cost.find((c) => c.pass === p && c.pixelRatio === pr);
      let sA = 0; let sB = 0; let sA2 = 0;
      for (const id of ids) {
        const get = (p) => at(p).rows.find((r) => r.id === id).median;
        const A = get('A off'); const B = get('B on'); const A2 = get('A2 off');
        sA += A; sB += B; sA2 += A2;
        const base = (A + A2) / 2;
        console.log(`${id.padEnd(26)}  ${A.toFixed(1).padStart(8)}  ${B.toFixed(1).padStart(8)}  `
          + `${A2.toFixed(1).padStart(8)}  ${`${(100 * (B - base) / base).toFixed(1)} %`.padStart(14)}  `
          + `${`${(100 * (A2 - A) / A).toFixed(1)} %`.padStart(10)}`);
      }
      const base = (sA + sA2) / 2;
      console.log('--------------------------  --------  --------  --------  --------------  ----------');
      console.log(`${'ALL STATIONS'.padEnd(26)}  ${sA.toFixed(0).padStart(8)}  ${sB.toFixed(0).padStart(8)}  `
        + `${sA2.toFixed(0).padStart(8)}  ${`${(100 * (sB - base) / base).toFixed(1)} %`.padStart(14)}  `
        + `${`${(100 * (sA2 - sA) / sA).toFixed(1)} %`.padStart(10)}`);
      totals.set(pr, { off: base, on: sB });
    }
    /**
     * THE BUDGET QUESTION, when more than one ratio was timed. The frame that
     * SHIPS is the highest ratio with no MSAA; the question a visitor's phone
     * asks is whether the frame they could choose in Settings — MSAA at the
     * lower ratio — costs more or less than the one they get today.
     */
    if (totals.size > 1) {
      const ratios = [...totals.keys()].sort((a, b) => b - a);
      const shipped = totals.get(ratios[0]).off;
      console.log('\nAGAINST THE FRAME THAT SHIPPED BEFORE T-0157 '
        + `(pixel ratio ${ratios[0]}, no MSAA, ${shipped.toFixed(0)} ms over ${ids.length} stations)`);
      for (const r of ratios) {
        const t = totals.get(r);
        const pc = (v) => {
          const d = 100 * (v - shipped) / shipped;
          return `${d >= 0 ? '+' : '-'}${Math.abs(d).toFixed(1)} %`;
        };
        console.log(`  ratio ${String(r).padEnd(3)} MSAA on   ${t.on.toFixed(0).padStart(8)} ms  `
          + `${pc(t.on).padStart(9)}`);
        console.log(`  ratio ${String(r).padEnd(3)} MSAA off  ${t.off.toFixed(0).padStart(8)} ms  `
          + `${pc(t.off).padStart(9)}`);
      }
    }
  }
  if (errors.length) {
    console.log(`\n${errors.length} page error(s):`);
    for (const e of errors) console.log(`  ${e}`);
  }
}
process.exit(errors.length ? 1 : 0);
