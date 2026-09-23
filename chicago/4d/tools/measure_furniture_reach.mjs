/**
 * T-0150 — WHAT A FURNITURE REACH BUYS, AND WHAT IT COSTS THE PICTURE.
 *
 *   node tools/measure_furniture_reach.mjs [--source] [--json <file>] [--level TIER]
 *
 * T-0149's first piece is a distance cull on the derived furniture at `light`,
 * and the number it turns on — how far down a street a fence, a plank walk, a
 * barrel, a wharf deck or a moored hull is drawn at all — is exactly the kind of
 * number this project has twice set from one camera and had to re-argue. So it
 * is measured before it is set, at the WHOLE stand set T-0135 named, and it is
 * measured on BOTH axes at once:
 *
 *   1. **What it saves** — triangles and draw calls at each candidate reach,
 *      per stand, at `light`.
 *   2. **What it costs the picture** — the 48² frame signature at each reach
 *      against the same frame with everything drawn. A cull that saves 200,000
 *      triangles and moves the frame by twenty counts is not a rendering
 *      decision, it is a deletion; a cull that moves it by one is the trim the
 *      ticket asked for. Only the pair of readings can tell those apart.
 *
 * It drives `__chicago4d.setFurnitureReach`, which is the shipped cull itself
 * rather than a re-implementation of it, so a reach that reads well here is a
 * reach the visitor gets.
 *
 * Defaults to the PUBLISHED mirror, for the reason every renderer measurement
 * here does: the source tree loads uncompressed masters and the site loads
 * compressed derivatives. `--source` measures the working tree instead.
 *
 * This is a measurement, not the release gate — `tools/smoke_renderer.mjs` is
 * where the reach is held to its ceilings.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

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
const jsonAt = process.argv.indexOf('--json');
const jsonOut = jsonAt >= 0 ? process.argv[jsonAt + 1] : null;
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.FURNITURE_PORT || 4197);
const YEAR = process.env.FURNITURE_YEAR || '1835';

/**
 * The five stands, copied from `tools/smoke_renderer.mjs` STANDS — where each
 * one's reason is written and where the set is owned. Copied rather than
 * imported because the smoke is a script and not a module; a stand added there
 * and not here makes this tool less complete, never wrong.
 */
const STANDS = [
  { id: 'lake_at_canal', kind: 'anchor', target: 'green_tree', label: 'Lake at Canal, east' },
  { id: 'the_forks', kind: 'anchor', target: 'forks', label: 'the forks, Wolf Point' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market', label: 'Lake and Market' },
  { id: 'from_above', kind: 'anchor', target: 'from_above', label: 'the open aerial' },
  { id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m' },
];
/** Candidate reaches in metres, plus `null` for the baseline with none.
 *  `--reaches 400,350,300` narrows the sweep; the baseline is always first. */
const reachAt = process.argv.indexOf('--reaches');
const REACHES = [null, ...(reachAt >= 0
  ? process.argv[reachAt + 1].split(',').map(Number).filter((n) => n > 0)
  : [500, 400, 350, 300, 250, 200, 150])];

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

/**
 * BOTH VIEWPORTS, and the mobile one is not an afterthought here: `light` is the
 * tier a PHONE boots into without anybody touching the control, so a reach
 * chosen on the desktop frame alone would be the same one-camera mistake T-0135
 * was opened to end, one axis over. The pixel argument differs between them too
 * — 780 CSS pixels over the same 62 degrees is a slightly smaller pale.
 */
const onlyAt = process.argv.indexOf('--only');
const ONLY = onlyAt >= 0 ? process.argv[onlyAt + 1] : null;
/** WHICH TIER THE SWEEP DRIVES, `light` by default because T-0150 asked the
 *  question about the floor. T-0241 asked it about the middle rung — `balanced`
 *  carried NO reach at all, so "turn the quality down and less is drawn" was
 *  true of the bottom rung and not of the one above it — and the honest way to
 *  answer that was to point the same instrument at the other tier rather than
 *  write a second one. `--level balanced`. */
const levelAt = process.argv.indexOf('--level');
const LEVEL = levelAt >= 0 ? process.argv[levelAt + 1] : 'light';
if (!['full', 'balanced', 'light'].includes(LEVEL)) {
  console.error(`--level must be full, balanced or light — got ${LEVEL}`);
  process.exit(2);
}
const VIEWPORTS = [
  { label: 'desktop 1280x800', width: 1280, height: 800 },
  { label: 'mobile 390x780', width: 390, height: 780 },
].filter((v) => !ONLY || v.label.startsWith(ONLY));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
const errors = [];
const passes = [];
for (const vp of VIEWPORTS) {
const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
page.on('pageerror', (e) => errors.push(`${vp.label}: ${String(e)}`));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

const measured = await page.evaluate(async ({ stands, reaches, level }) => {
  const a = window.__chicago4d;
  const settle = () => new Promise((r) => requestAnimationFrame(
    () => requestAnimationFrame(r)));
  const started = a.detail;
  await a.setDetail(level);
  await settle();
  // THE CLOCK IS HELD FOR THE WHOLE SWEEP, and the first run said why: the wind
  // blows between two captures, so a frame delta taken with the prairie moving
  // measures the weather as well as the cull — it read a floor of about mean
  // 0.10 at the two stands with the most near grass in them, which is the same
  // order as the readings being compared. `setAnimationHold` is the harness
  // switch the confidence-view gate already uses for exactly this. The residual
  // row at the end of each stand proves it: baseline against baseline, which
  // must be 0.
  a.setAnimationHold(true);
  const rows = [];
  for (const st of stands) {
    if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
    else a.goTo(st.target);
    await settle();
    let baseCells = null;
    const at = [];
    for (const reach of reaches) {
      a.setFurnitureReach(reach);
      await settle();
      const s = a.stats();
      const sig = await a.capture(48);
      const r = a.furnitureReach;
      const row = { reach, tris: s.triangles, calls: s.drawCalls,
                    hidden: r.hidden, meshes: r.meshes };
      if (baseCells === null) baseCells = sig.cells;
      let sum = 0;
      let worst = 0;
      for (let i = 0; i < sig.cells.length; i++) {
        const d = Math.abs(sig.cells[i] - baseCells[i]);
        sum += d;
        worst = Math.max(worst, d);
      }
      row.deltaMean = sum / sig.cells.length;
      row.deltaWorst = worst;
      at.push(row);
    }
    // The residual: the baseline measured a second time, at the end, against
    // itself. Anything but zero here is the instrument's own noise and every
    // reading above has to be read against it.
    a.setFurnitureReach(null);
    await settle();
    const again = await a.capture(48);
    let rsum = 0;
    let rworst = 0;
    for (let i = 0; i < again.cells.length; i++) {
      const d = Math.abs(again.cells[i] - baseCells[i]);
      rsum += d;
      rworst = Math.max(rworst, d);
    }
    rows.push({ id: st.id, label: st.label, at,
                residual: { mean: rsum / again.cells.length, worst: rworst } });
  }
  a.setAnimationHold(false);
  a.setFurnitureReach(null);
  await a.setDetail(started);
  return { rows, restored: a.detail === started };
}, { stands: STANDS, reaches: REACHES, level: LEVEL });
passes.push({ viewport: vp.label, ...measured });
await page.close();
}

for (const pass of passes) {
const vp = VIEWPORTS.find((v) => v.label === pass.viewport);
const pxPerRad = vp.height / (62 * Math.PI / 180);
console.log(`================  ${pass.viewport}  ================`);
console.log('a 1.2 m fence pale, in CSS pixels of this frame at 62 deg:');
console.log('  ' + REACHES.filter((r) => r).map((r) =>
  `${r} m ${(pxPerRad * 1.2 / r).toFixed(1)} px`).join('   '));
console.log('');
for (const row of pass.rows) {
  const base = row.at[0];
  console.log(`${row.label}`);
  console.log('   reach      triangles      calls   hidden/meshes   saved   frame delta (48^2)');
  for (const r of row.at) {
    const saved = base.tris - r.tris;
    console.log(`   ${String(r.reach ?? 'none').padStart(5)} m `
      + `${r.tris.toLocaleString('en-US').padStart(12)} `
      + `${String(r.calls).padStart(9)} `
      + `${`${r.hidden}/${r.meshes}`.padStart(14)} `
      + `${saved.toLocaleString('en-US').padStart(9)} `
      + `  mean ${r.deltaMean.toFixed(2)}, worst ${r.deltaWorst}`);
  }
  console.log(`   residual (baseline vs itself): `
    + `mean ${row.residual.mean.toFixed(2)}, worst ${row.residual.worst}`);
  console.log('');
}
}
if (errors.length) console.log(`PAGE ERRORS: ${errors.join('; ')}`);
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(passes, null, 2)}\n`);

await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
