/**
 * T-0690 — WHAT THE ROAD-LEGIBILITY AID CAN ACTUALLY MOVE, PER VIEWPORT AND
 * PER GRID.
 *
 *   node tools/measure_road_aid.mjs [--source] [--stations a,b]
 *                                   [--grids 12,24,48,96] [--json <file>]
 *   SMOKE_VIEWPORT=mobile node tools/measure_road_aid.mjs
 *
 * `smoke_renderer.mjs` part 8 asserts R-A1's second obligation — that raising
 * the aid REACHES the render — by comparing two 48² frame signatures and
 * demanding `worst >= 4, mean >= 0.15`. Those floors were set on 2026-08-16
 * from ONE reading at ONE viewport: the aid scored worst 2 at 12² and worst 6
 * at 48² on the desktop frame, and 4 is two thirds of the 6. Mobile was never
 * measured, and mobile is where the assertion has been red since 2026-09-04
 * (T-0690): the aid moves the 390×780 frame by a worst cell of 3, one short,
 * while the mean clears its own floor comfortably.
 *
 * A gate cannot be repaired by moving a threshold until somebody has measured
 * what the instrument reads, so this is that measurement — and it measures the
 * GRID as well as the aid, because the grid is the part R-A1 already found to
 * be the deciding variable. The signature averages luma over `grid²` cells; a
 * roadway that occupies a tenth of the frame is diluted inside every cell it
 * only partly covers, so a coarser grid reports a smaller worst cell for the
 * identical change. That is why 12² read 2 where 48² read 6 with nothing about
 * the scene changed between them.
 *
 * Each row reports, at one station and one grid:
 *
 *   1. **the aid's reach** — `|signature(aid=1) − signature(aid=0)|`, mean and
 *      worst cell, the exact quantity part 8 gates on;
 *   2. **the residual** — `|signature(aid=0 again) − signature(aid=0)|`, which
 *      is the noise floor the reach has to stand clear of. Part 8's THIRD
 *      assertion allows a residual of worst 3, so a reach floor of 3 would be
 *      satisfiable by noise and is not a gate at all;
 *   3. **the separation** — worst reach minus worst residual. This is the
 *      number a floor should be derived from, and it is what tells a reader
 *      whether a grid is a usable instrument at this viewport.
 *
 * The clock is held for the whole sweep (`setAnimationHold`), so the three
 * captures behind every row are three readings of one unchanged scene and the
 * residual is readback noise rather than weather.
 *
 * Defaults to the PUBLISHED mirror, for the reason every renderer measurement
 * here does: the source tree loads uncompressed masters and the site loads
 * compressed derivatives, and bugs have shipped in that gap twice. `--source`
 * measures the working tree instead.
 *
 * This is a measurement, not the release gate — the gate assertion is part 8 of
 * `tools/smoke_renderer.mjs`. `tools/check.sh` cannot run it: the dev gate's
 * runner has no Playwright, by design.
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
const argAfter = (flag) => {
  const i = process.argv.indexOf(flag);
  return i >= 0 ? process.argv[i + 1] : null;
};
const wantSource = process.argv.includes('--source');
const jsonOut = argAfter('--json');
const GRIDS = (argAfter('--grids') || '12,24,48,96,144')
  .split(',').map((s) => Number(s.trim())).filter((n) => Number.isFinite(n) && n > 1);
// `lake_market` by default and not the whole anchor list: it is where part 8
// takes R-A1's three assertions, standing at the station whose road bands were
// just read, so it is the frame the gate's floors have to describe.
const PICK = (argAfter('--stations') || 'lake_market')
  .split(',').map((s) => s.trim()).filter(Boolean);
const VIEWPORT = (process.env.SMOKE_VIEWPORT || 'desktop') === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.ROAD_AID_PORT || 4198);
const YEAR = process.env.ROAD_AID_YEAR || '1835';

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
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'} `
  + `at ${VIEWPORT.width}x${VIEWPORT.height}\n`);

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

// The entry gate and the first-run guide, dismissed the way `critic_shots.mjs`
// does it — a signature taken through the intro overlay is a reading of the
// overlay, and the overlay does not carry a road.
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

const delta = (a, b) => {
  let sum = 0;
  let worst = 0;
  const n = Math.min(a.cells.length, b.cells.length);
  for (let i = 0; i < n; i++) {
    const d = Math.abs(a.cells[i] - b.cells[i]);
    sum += d;
    if (d > worst) worst = d;
  }
  return { mean: sum / (n || 1), worst, cells: n };
};

const rows = [];
console.log(`  ${'station'.padEnd(13)} ${'grid'.padStart(5)}  `
  + `${'aid reach'.padStart(18)}  ${'residual'.padStart(18)}  separation`);
for (const station of PICK) {
  const went = await page.evaluate((id) => !!window.__chicago4d.goTo(id), station);
  if (!went) console.log(`  ${station}: no such anchor — skipped`);
  await page.waitForTimeout(400);
  await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
  for (const grid of GRIDS) {
    // Three captures of one held scene, in the order part 8 takes them: the
    // default, the aid full on, and the default restored.
    await page.evaluate(() => window.__chicago4d.setRoadAid(0));
    const off = await page.evaluate((g) => window.__chicago4d.capture(g), grid);
    const set = await page.evaluate(() => window.__chicago4d.setRoadAid(1));
    const live = await page.evaluate(() => window.__chicago4d.roadAid);
    const on = await page.evaluate((g) => window.__chicago4d.capture(g), grid);
    await page.evaluate(() => window.__chicago4d.setRoadAid(0));
    const back = await page.evaluate((g) => window.__chicago4d.capture(g), grid);
    const reach = delta(off, on);
    const residual = delta(off, back);
    const row = {
      station,
      grid,
      cells: reach.cells,
      cellPx: [+(off.width / grid).toFixed(1), +(off.height / grid).toFixed(1)],
      aidSet: set,
      aidLive: live,
      reachMean: +reach.mean.toFixed(3),
      reachWorst: reach.worst,
      residualMean: +residual.mean.toFixed(3),
      residualWorst: residual.worst,
      separation: reach.worst - residual.worst,
    };
    rows.push(row);
    console.log(`  ${station.padEnd(13)} ${String(`${grid}²`).padStart(5)}  `
      + `mean ${row.reachMean.toFixed(2).padStart(6)} worst ${String(row.reachWorst).padStart(3)}  `
      + `mean ${row.residualMean.toFixed(2).padStart(6)} worst ${String(row.residualWorst).padStart(3)}  `
      + `${String(row.separation).padStart(6)}   (cell ${row.cellPx[0]}×${row.cellPx[1]} px)`);
  }
  await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
}

await browser.close();
server.close();

if (errors.length) {
  console.log(`\n${errors.length} page error(s):`);
  for (const e of errors) console.log(`  - ${e}`);
}

const report = { viewport: VIEWPORT, published: !wantSource, rows, pageErrors: errors };
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(report, null, 2)}\n`);
process.exit(errors.length ? 1 : 0);
