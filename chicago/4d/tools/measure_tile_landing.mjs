/**
 * T-2969 — WHAT A KEPT TILE'S WHOLE LANDING COSTS THE MAIN THREAD, before and after.
 *
 *   node tools/measure_tile_landing.mjs [--only mobile|desktop] [--reps 4]
 *                                       [--moves jump,tier] [--throttle 4]
 *                                       [--year 1835] [--json f]
 *
 * The near deal's field tiles (near-field.js `fieldKeeper`: the near tile, the
 * mid tile, and the carry tile T-2966 keeps the same way) are kept a strip at a
 * time on the job pool, but the FIRST tile — after a boot, a tier change, or a
 * jump of a tile or more — is every texel at once, and its finish and write
 * were one main-thread task. T-2969 lands a whole tile `LAND_BAND_ROWS` rows at
 * a time, handing the thread back between slices of `LAND.sliceMs`.
 *
 * This serves the source tree, enters the town at the phone profile (390x780,
 * touch, Chrome's 4x CPU throttle; `--only desktop` reads 1280x800 bare) and
 * reads, per keeper, every whole landing's slices and its LONGEST slice — the
 * one long task a visitor feels — over two moves:
 *
 *   jump   (the default) the walker set down 600 m away, east then west (a teleport,
 *          as `goTo` does): the mid tile lands whole from the pool, and the
 *          near tile is BUILT in the frame (`keeper.adopt(nf.build(..))`, its
 *          builds and ms printed apart — that is not a landing, and not this
 *          ticket's);
 *   tier   the detail tier changed away and back to `light` (the rig is rebuilt,
 *          so both keepers start from nothing and land whole). Opt-in: at the
 *          4x throttle the tier change's own rebuild is a ~30 s task and two of
 *          them a rep do not fit a 600 s call. Its landing is `landWhole`, the
 *          same as a jump's.
 *
 * The before is the same page with `LAND.sliceMs = Infinity` — one slice a
 * landing, which `check_near_field_keeper.mjs` holds to the old landing byte
 * for byte — set in the page through the module itself, so before and after
 * are read interleaved in one session on one runner. Long tasks (the page's own
 * PerformanceObserver, over 50 ms) are counted per move as well, with their
 * longest: they include the tier change's own rebuild, so they say what else a
 * move costs, and the keepers' slices say what the landing costs.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const argAt = (k) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const ONLY = argAt('--only') || 'mobile';
const REPS = Number(argAt('--reps') || 4);
const MOVES = (argAt('--moves') || 'jump').split(',');
const THROTTLE = Number(argAt('--throttle') || 4);
const YEAR = argAt('--year') || '1835';
const jsonOut = argAt('--json');
const MODULE = '/renderers/web/js/near-field.js';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.webp': 'image/webp', '.ktx2': 'image/ktx2',
};
const PORT = Number(process.env.TILE_LANDING_PORT || 4207);
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

const VIEWPORT = ONLY === 'desktop'
  ? { id: 'desktop', width: 1280, height: 800, touch: false, scale: 1, throttle: 1 }
  : { id: 'mobile', width: 390, height: 780, touch: true, scale: 1.5, throttle: THROTTLE };

/** Runs in the page: one move with the landing budget given, read per keeper. */
async function drive({ move, sliceMs, module, leg }) {
  const a = window.__chicago4d;
  const { LAND } = await import(module);
  LAND.sliceMs = sliceMs;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const long = [];
  const obs = new PerformanceObserver((l) => { for (const e of l.getEntries()) long.push(e.duration); });
  obs.observe({ type: 'longtask' });
  const keepers = () => a.flora.nearDraw?.keepers?.() ?? {};
  const snap = () => {
    const out = {};
    for (const [k, kp] of Object.entries(keepers())) {
      if (!kp) continue;
      out[k] = { whole: kp.stats.whole, slices: kp.stats.slices, lastMs: kp.stats.lastMs };
      kp.stats.sliceMaxMs = 0;
    }
    return out;
  };
  const near0 = { ...(a.flora.nearDraw?.stats ?? {}) };
  let before = {};
  const settle = async () => {
    // Both keepers home, and nothing re-asked behind them.
    for (let i = 0; i < 4; i++) { await a.flora.nearDraw?.settled?.(); await sleep(400); }
  };
  if (move === 'tier') {
    await a.setDetail('balanced');
    await settle();
    await a.setDetail('light');
    await settle();
  } else {
    await settle();
    before = snap();
    const s = (a.scene?.anchors ?? []).find((x) => x.id === 'lake_at_canal') ?? a.scene.anchors[0];
    // Back and forth, 600 m every leg: 300 m east of the anchor, then west.
    const e = (leg % 2 ? 300 : -300) + s.local_e;
    a.walker.teleport({ local_e: e, local_n: s.local_n, yaw_deg: s.yaw_deg ?? 90 });
    const t0 = performance.now();
    // The page's own loop takes the jump, as a goTo would.
    while (performance.now() - t0 < 30_000) {
      await sleep(250);
      const m = keepers().mid;
      if (!m || m.stats.whole > (before.mid?.whole ?? 0)) break;
    }
    await settle();
  }
  obs.disconnect();
  const out = {};
  for (const [k, kp] of Object.entries(keepers())) {
    if (!kp) continue;
    const b = move === 'tier' ? { whole: 0, slices: 0 } : before[k] ?? { whole: 0, slices: 0 };
    out[k] = { size: kp.spec.size, whole: kp.stats.whole - b.whole, slices: kp.stats.slices - b.slices,
      sliceMaxMs: kp.stats.sliceMaxMs, lastMs: kp.stats.lastMs };
  }
  const ns = a.flora.nearDraw?.stats ?? {};
  out.nearBuilds = move === 'tier' ? ns.builds : ns.builds - (near0.builds ?? 0);
  out.nearBuildMs = move === 'tier' ? ns.buildMs : ns.buildMs - (near0.buildMs ?? 0);
  out.longTasks = long.length;
  out.longMaxMs = long.length ? Math.max(...long) : 0;
  out.tier = a.detail ?? null;
  return out;
}

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'] });
const vp = VIEWPORT;
const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height },
  hasTouch: vp.touch, deviceScaleFactor: vp.scale });
const page = await ctx.newPage();
page.setDefaultTimeout(480_000);
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
const t0 = Date.now();
await page.goto(`http://127.0.0.1:${PORT}/renderers/web/index.html?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 480_000 });
const gateBtn = await page.$('#gate button, .gate button');
if (gateBtn) { await gateBtn.click(); await page.waitForTimeout(800); }
const entered = await page.evaluate(async () => {
  const welcome = window.__chicago4d.welcome;
  const deadline = Date.now() + 90_000;
  while (welcome && welcome.state !== 'world' && Date.now() < deadline) {
    if (welcome.state === 'welcome') welcome.enter('spawn');
    await new Promise((r) => setTimeout(r, 100));
  }
  return welcome?.state ?? 'no welcome';
});
if (vp.throttle > 1) {
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: vp.throttle });
}
console.log(`${vp.id} ${vp.width}x${vp.height}, ready in ${((Date.now() - t0) / 1000).toFixed(0)} s, `
  + `${entered}${vp.throttle > 1 ? `, CPU throttled ${vp.throttle}x` : ''}`);
const hasKeepers = await page.evaluate(() => typeof window.__chicago4d.flora.nearDraw?.keepers === 'function');
if (!hasKeepers) {
  console.error('this page has no nearDraw.keepers() (the GPU near ring is off, or the tree predates T-2969)');
  process.exit(2);
}

const out = { year: YEAR, viewport: vp.id, throttle: vp.throttle, reps: REPS, readings: [] };
const f = (x) => (x ?? 0).toFixed(1).padStart(6);
console.log('move  budget  rep | keeper size whole slices  longest slice ms | near builds ms | long tasks, longest ms');
let leg = 0;
for (let rep = 1; rep <= REPS; rep++) {
  for (const move of MOVES) {
    // The legs alternate west and east, so the order flips each rep: each
    // budget lands at both places, and a place's own cost is not read as it.
    const modes = [['before', Infinity], ['after', null]];
    for (const [mode, sliceMs] of rep % 2 ? modes : modes.reverse()) {
      const r = await page.evaluate(drive, { move, leg: leg++, module: MODULE,
        sliceMs: sliceMs ?? 6 });
      out.readings.push({ move, mode, rep, ...r });
      for (const k of ['near', 'mid']) {
        if (!r[k]) continue;
        console.log(`${move.padEnd(5)} ${mode.padEnd(7)} ${rep}  | ${k.padEnd(5)} ${String(r[k].size).padStart(4)}`
          + ` ${String(r[k].whole).padStart(5)} ${String(r[k].slices).padStart(6)} ${f(r[k].sliceMaxMs)}`
          + `           | ${String(r.nearBuilds ?? 0).padStart(3)} ${f(r.nearBuildMs)} | ${r.longTasks}, ${f(r.longMaxMs)}`);
      }
      if (jsonOut) {
        fs.mkdirSync(path.dirname(jsonOut), { recursive: true });
        fs.writeFileSync(jsonOut, `${JSON.stringify(out, (k, v) => (typeof v === 'number'
          ? Math.round(v * 100) / 100 : v), 2)}\n`);
      }
    }
  }
}
// The verdict: every whole landing's longest slice, before against after.
const worst = (mode, k) => Math.max(0, ...out.readings.filter((x) => x.mode === mode && x[k]?.whole)
  .map((x) => x[k].sliceMaxMs));
for (const k of ['near', 'mid']) {
  console.log(`${k}: a whole landing's longest slice ${worst('before', k).toFixed(1)} ms before, `
    + `${worst('after', k).toFixed(1)} ms after`);
}
out.errors = errors;
if (errors.length) console.log(`page errors: ${errors.length}\n  ${errors.slice(0, 3).join('\n  ')}`);
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
