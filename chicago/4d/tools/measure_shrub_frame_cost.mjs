/**
 * T-0020 (ROADMAP K59) — WHAT A SHRUB'S GRAIN COSTS A FRAME, IN THE WET WOODS.
 *
 *   node tools/measure_shrub_frame_cost.mjs [--source] [--fill N]...
 *        [--frames N] [--warmup N] [--viewport mobile|desktop|both] [--json]
 *
 * K57 shipped 48 sprays a shrub at the knee of a coverage curve and left 64
 * measured and unspent: cover 46.9 % → 51.3 %, stem cover 51.3 % → 54.2 %, for
 * 104 → 136 triangles. K59 is the question of whether to spend them, and it
 * refused to be answered on the numbers K57 had:
 *
 *   > **Take this parcel only with a frame-time measurement in hand**, in the wet
 *   > woods where 167 of them stand; without one it is a preference wearing a
 *   > table, which is exactly what K57 refused.
 *
 * `tools/measure_spray_grain.mjs` answers what the grain BUYS. It renders no
 * frame, so it cannot answer what the grain COSTS: the shrub batch does not
 * split — one instanced set, one draw call, at either grain — so the cost is
 * fill and vertex work and neither had ever been read. This tool reads them.
 *
 * HOW IT MEASURES, and why each choice is the honest one.
 *
 *   one stand, chosen once ..... the two grains must be compared from the SAME
 *                                eye. The stand is found through the placer's
 *                                own `zoneAt`/`plantableAt` — the same entry
 *                                point `measure_sward_draw.mjs` uses — and the
 *                                bearing is swept over 8 points of the compass
 *                                at the SHIPPED grain and fixed at the most
 *                                expensive one. A budget question is asked at
 *                                the worst case or it is not asked.
 *   the clock is held .......... `setAnimationHold(true)`, so the wind does not
 *                                blow between two frames that are supposed to
 *                                differ only in the geometry.
 *   the loop is stopped ........ `setAnimationLoop(null)`, then frames are
 *                                driven one at a time by `step()`. Otherwise the
 *                                browser's own rAF pacing — which throttles at
 *                                the display rate — is what gets measured.
 *   a readback every frame .... `step()` returns when the commands are SUBMITTED,
 *                                not when they are drawn, and MEASURED HERE
 *                                `gl.finish()` does not close that gap: with a
 *                                finish alone the whole town reported 2.9 ms a
 *                                frame while the process took a second per frame
 *                                of wall clock, because ANGLE's SwiftShader
 *                                backend does the work in another process. A
 *                                one-pixel `readPixels` is a real fence — the
 *                                caller cannot be handed a pixel that has not
 *                                been drawn — and it is what the renderer's own
 *                                `capture()` has always used. Without it this
 *                                measures how fast three.js can TALK, which is
 *                                the one quantity that does not move when a
 *                                shrub grows 32 triangles.
 *   the file is patched, served  the candidate grain is injected by rewriting
 *                                `shrub-grain.js` in flight, so both runs load
 *                                the same tree, the same data and the same
 *                                renderer, differing in one integer. The patch
 *                                is read back out of the page and the run aborts
 *                                if it did not take.
 *
 * WHAT THE FIGURE IS AND IS NOT. Chromium headless on this project's runners
 * draws through SwiftShader, a SOFTWARE rasteriser, and the tool prints the
 * renderer string so no reading can be quoted without it. That makes the
 * absolute milliseconds a fact about this machine and not about a visitor's
 * phone. It does NOT make the comparison worthless, and it is worth being
 * precise about why: a software rasteriser is the most fill-sensitive renderer
 * there is, so it is the harshest possible witness for the one risk in this
 * parcel — 33 % more transparent plate over the same silhouette. A grain that
 * is free HERE is free on hardware; a grain that is expensive here needs a
 * second reading before it is refused.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Playwright is installed globally on the runner, and ESM does not honour
// NODE_PATH, so resolve it the way tools/smoke_renderer.mjs does.
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
const flagVals = (name) => {
  const out = [];
  for (let i = 0; i < argv.length; i++) if (argv[i] === name && argv[i + 1] !== undefined) out.push(argv[i + 1]);
  return out;
};

const wantSource = argv.includes('--source');
const wantJson = argv.includes('--json');
const FRAMES = Number(flagVal('--frames', 20));
const WARMUP = Number(flagVal('--warmup', 5));
/** The shipped grain first, always: every later row is read against row one. */
const SHIPPED_FILL = Number(
  /fill:\s*(\d+)/.exec(fs.readFileSync(path.join(HERE, '../renderers/web/js/shrub-grain.js'), 'utf8'))?.[1]);
if (!Number.isFinite(SHIPPED_FILL)) {
  console.error('cannot read `fill` out of renderers/web/js/shrub-grain.js');
  process.exit(2);
}
const fills = flagVals('--fill').map(Number);
/** Duplicates are KEPT on purpose: `--fill 56 --fill 40` is an A/B/A, and an
 *  A/B/A is how a shared runner's own drift is told apart from the geometry's
 *  cost. Every row is read against the FIRST shipped-grain row. */
const FILLS = [SHIPPED_FILL, ...(fills.length ? fills : [SHIPPED_FILL + 16])];
const wantViewport = flagVal('--viewport', 'both');
const VIEWPORTS = [
  ['mobile 390x780', { width: 390, height: 780 }, 2],
  ['desktop 1280x800', { width: 1280, height: 800 }, 1],
].filter(([l]) => wantViewport === 'both' || l.startsWith(wantViewport));
if (!VIEWPORTS.length) {
  console.error(`--viewport must be mobile, desktop or both, got "${wantViewport}"`);
  process.exit(2);
}

const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.SHRUB_PORT || 4193);
const YEAR = process.env.SHRUB_YEAR || '1835';
/** The community K59 names. 167 shrubs stand in one ring here and nowhere else. */
const COMMUNITY = process.env.SHRUB_COMMUNITY || 'z06_dense_forest';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
/**
 * The grain in force for the page currently booting, and the reason it is
 * patched HERE rather than by a Playwright route handler. Registering ANY route
 * on a context turns on network interception for EVERY request in it, and this
 * page pulls several hundred GLB and JSON files through it: measured, one page
 * load went from about eight seconds to over four minutes, which turned a
 * one-minute instrument into a fifteen-minute one. The server already owns the
 * bytes, so it does the one-integer rewrite for free.
 */
let servedFill = null;
let patchTook = false;
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  if (servedFill !== null && path.basename(file) === 'shrub-grain.js') {
    const body = fs.readFileSync(file, 'utf8');
    const next = body.replace(/fill:\s*\d+/, `fill: ${servedFill}`);
    patchTook = next !== body || servedFill === SHIPPED_FILL;
    res.writeHead(200, { 'content-type': 'text/javascript', 'cache-control': 'no-store' });
    res.end(next);
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
if (!wantJson) console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}\n`);

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});

const errors = [];
/**
 * One page, booted with `shrub-grain.js` rewritten to the asked-for `fill`.
 * The rewrite is asserted from inside the page, because a route handler whose
 * pattern stopped matching would otherwise report the shipped grain twice and
 * call the difference zero.
 */
async function openAt(fill, viewport, deviceScaleFactor) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errors.push(`fill ${fill}: ${String(e)}`));
  servedFill = fill;
  patchTook = false;
  await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load', timeout: 240000 });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });
  const seen = await page.evaluate(async () => {
    const mod = await import('./js/shrub-grain.js');
    return mod.SHRUB_GRAIN.fill;
  });
  if (!patchTook || seen !== fill) {
    console.error(`the grain patch did not take: asked for fill ${fill}, the page reports ${seen}`);
    process.exit(2);
  }
  return { ctx, page };
}

/** Where the walker is put, and which way it faces. Decided once. */
async function findStand(page) {
  return page.evaluate((community) => {
    const a = window.__chicago4d;
    // The placer's own plantability rule, not the community's extent: a point
    // this project would refuse to plant is a point with no shrubs at it.
    let spot = null;
    for (let e = -900; e <= 1200 && !spot; e += 6) {
      for (let n = -700; n <= 700; n += 6) {
        if (a.flora.zoneAt(e, n) === community && a.flora.plantableAt(e, n)) { spot = [e, n]; break; }
      }
    }
    if (!spot) return null;
    const [e, n] = spot;
    const bearings = [];
    for (let yaw = 0; yaw < 360; yaw += 45) {
      a.walker.teleport({ local_e: e, local_n: n, yaw_deg: yaw });
      // Two frames: the first moves the eye, the second re-deals the sward for
      // where it ended up.
      a.step(); a.step(); a.step();
      const st = a.stats();
      bearings.push({ yaw, triangles: st.triangles, drawCalls: st.drawCalls,
        shrubs: a.flora.stats.sets['flora-shrub'] ?? 0 });
    }
    const worst = bearings.reduce((m, b) => (b.triangles > m.triangles ? b : m), bearings[0]);
    return { e, n, bearings, yaw: worst.yaw };
  }, COMMUNITY);
}

/** Frame cost at one stand, one grain, one viewport. */
async function timeAt(page, stand, frames, warmup) {
  return page.evaluate(async ({ stand, frames, warmup }) => {
    const a = window.__chicago4d;
    a.walker.teleport({ local_e: stand.e, local_n: stand.n, yaw_deg: stand.yaw });
    a.setAnimationHold(true);
    for (let i = 0; i < 4; i++) a.step();          // settle the re-deal
    // Drive the frames by hand. rAF paces itself against the display, which is
    // a measurement of the pacing and not of the scene.
    a.renderer.setAnimationLoop(null);
    const gl = a.renderer.getContext();
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    const device = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    // The fence. One pixel is enough: readPixels cannot return until the frame
    // it is reading has actually been rasterised.
    const px = new Uint8Array(4);
    const drawAndWait = () => {
      a.step();
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
      gl.finish();
    };
    for (let i = 0; i < warmup; i++) drawAndWait();
    const ms = [];
    for (let i = 0; i < frames; i++) {
      const t0 = performance.now();
      drawAndWait();
      ms.push(performance.now() - t0);
    }
    ms.sort((x, y) => x - y);
    const at = (q) => ms[Math.min(ms.length - 1, Math.floor(q * ms.length))];
    const st = a.stats();
    return {
      device: String(device),
      median: at(0.5), p05: at(0.05), p95: at(0.95),
      mean: ms.reduce((t, v) => t + v, 0) / ms.length,
      triangles: st.triangles, drawCalls: st.drawCalls,
      shrubs: a.flora.stats.sets['flora-shrub'] ?? 0,
    };
  }, { stand, frames, warmup });
}

const rows = [];
let stand = null;
let device = '';
for (const [label, viewport, dsf] of VIEWPORTS) {
  for (const fill of FILLS) {
    const { ctx, page } = await openAt(fill, viewport, dsf);
    // THE STAND IS FOUND ONCE, at the shipped grain, and reused for every row —
    // including across viewports, so one line of this table is comparable with
    // any other.
    if (!stand) {
      stand = await findStand(page);
      if (!stand) {
        console.error(`no plantable point found in ${COMMUNITY}`);
        process.exit(2);
      }
    }
    const r = await timeAt(page, stand, FRAMES, WARMUP);
    device = r.device;
    rows.push({ viewport: label, fill, sprays: 2 * 4 + fill, ...r });
    await ctx.close();
  }
}

await browser.close();
server.close();

if (wantJson) {
  console.log(JSON.stringify({ community: COMMUNITY, stand, frames: FRAMES, warmup: WARMUP, device, rows, errors }, null, 2));
} else {
  console.log(`the stand — ${COMMUNITY} at local E ${stand.e}, N ${stand.n}, facing ${stand.yaw}°`);
  console.log(`  chosen as the most expensive of 8 bearings at the shipped grain: `
    + stand.bearings.map((b) => `${b.yaw}° ${b.triangles.toLocaleString()}`).join(' · '));
  console.log(`  drawn through ${device}\n`);
  console.log(`${FRAMES} timed frames after ${WARMUP} warm-up, clock held, gl.finish() each frame\n`);
  console.log('viewport            sprays   shrubs      tris  calls   median      mean      p05      p95');
  console.log('------------------  ------  -------  --------  -----  -------  --------  -------  -------');
  const base = new Map();
  for (const r of rows) {
    if (r.fill === SHIPPED_FILL && !base.has(r.viewport)) base.set(r.viewport, r);
    const b = base.get(r.viewport);
    const delta = b && b !== r
      ? `   ${(r.median / b.median - 1) * 100 >= 0 ? '+' : ''}${((r.median / b.median - 1) * 100).toFixed(1)}% median`
      : '';
    console.log(`${r.viewport.padEnd(18)}  ${String(r.sprays).padStart(6)}  `
      + `${String(r.shrubs).padStart(7)}  ${r.triangles.toLocaleString().padStart(8)}  `
      + `${String(r.drawCalls).padStart(5)}  ${r.median.toFixed(2).padStart(7)}  `
      + `${r.mean.toFixed(2).padStart(8)}  ${r.p05.toFixed(2).padStart(7)}  ${r.p95.toFixed(2).padStart(7)}`
      + delta);
  }
  console.log(`\nmilliseconds a frame. The absolute numbers are this machine's; the ratio is the answer.`);
  if (errors.length) console.log(`\npage errors: ${errors.length}\n  ${errors.join('\n  ')}`);
}

process.exit(errors.length ? 1 : 0);
