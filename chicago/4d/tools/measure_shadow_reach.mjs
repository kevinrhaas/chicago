/**
 * ROADMAP R-W3b(a) — HOW FAR THE SUN'S SHADOW REACHES, AND WHAT REACHING
 * FURTHER COSTS.
 *
 *   node tools/measure_shadow_reach.mjs [--source] [--stations a,b]
 *                                       [--reaches 60,120,180] [--shots <dir>]
 *                                       [--json <file>]
 *
 * `world.js` gives the sun ONE orthographic shadow camera, a ±60 m box that
 * follows the visitor. Everything beyond 60 m is clipped out of the depth map,
 * so it casts no shadow on anything: the mid-field town and the whole river
 * timber meet the ground with no contact shadow at all.
 *
 * The parcel's question is not "would more reach look better" — it obviously
 * would. It is **what the reach costs**, because the answer decides whether one
 * map can pay for it or whether R-W3b needs true cascades. So this measures,
 * per station and per candidate reach:
 *
 *   1. **How much of the town is inside the shadow camera** — counted off the
 *      DATA (each structure's `placement.local_e/local_n` in its sidecar, each
 *      planted stem's own station) rather than off a renderer number, and
 *      tested against the shadow camera's own matrices.
 *   2. **What the frame costs** — draw calls, triangles and frame time. Draw
 *      calls and triangles are `renderer.info` AFTER the render, which in three
 *      includes the shadow pass: the shadow map is rendered inside `render()`,
 *      after `info.reset()`.
 *   3. **The texel size the reach implies** — `2 · reach / mapSize`. A reach
 *      bought by stretching the same map over more ground is bought by blurring
 *      the shadows a visitor stands next to, which is why every row here names
 *      its map size instead of holding it fixed.
 *   4. **Whether the frame actually changed** — `capture()`'s pixel signature
 *      against the 60 m frame. R-A1's finding: a control asserted only to be
 *      inert may be wired to nothing, so a reach that costs nothing and changes
 *      no pixel has done nothing.
 *
 * `--shots <dir>` writes one PNG per station per reach, which is the evidence
 * a visitor-visible parcel owes.
 *
 * Defaults to the PUBLISHED mirror, for the reason every renderer measurement
 * here does: the source tree loads uncompressed masters and the site loads
 * compressed derivatives, and bugs have shipped in that gap twice. `--source`
 * measures the working tree instead.
 *
 * This is a measurement, not the release gate — the gate assertion R-W3b(a)
 * lands is in `tools/smoke_renderer.mjs`. `tools/check.sh` cannot run either:
 * the dev gate's runner has no Playwright, by design.
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
const shotDir = argAfter('--shots');
const PICK = (argAfter('--stations') || '').split(',').map((s) => s.trim()).filter(Boolean);
const REACHES = (argAfter('--reaches') || '60,120,180,240')
  .split(',').map((s) => Number(s.trim())).filter((n) => Number.isFinite(n) && n > 0);
// One map size per reach, when the candidate being measured is a REAL rig
// rather than a rung on the sharpness-held ladder. Without it each reach gets
// the map that holds the shipped texel size, which is the ladder's own rule.
const MAPS = (argAfter('--maps') || '')
  .split(',').map((s) => Number(s.trim())).filter((n) => Number.isFinite(n) && n > 0);
// How many frames the cost sample takes. Under swiftshader a desktop frame is
// ~2 s, so a full-station sweep needs a short sample and a single-station
// candidate can afford a long one.
const FRAMES = Number(argAfter('--frames') || 24);
const VIEWPORT = (process.env.SMOKE_VIEWPORT || 'desktop') === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.SHADOW_PORT || 4197);
const YEAR = process.env.SHADOW_YEAR || '1835';

/**
 * The stations. The town ones are scene anchors — a visitor's own viewpoints —
 * and `river_bank` is the sweep station the timber is read from, because the
 * wood is the population with the most ground to sit on and no shadow on it.
 */
const STATIONS = [
  'south_water', 'sauganash', 'sauganash_wing', 'lake_market',
  'first_post_office', 'forks', 'green_tree', 'from_above',
].map((id) => ({ id, anchor: id }))
  .filter((s) => !PICK.length || PICK.includes(s.id));
if (!STATIONS.length) {
  console.error(`no station matches --stations ${PICK.join(',')}`);
  process.exit(2);
}

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
if (shotDir) fs.mkdirSync(shotDir, { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

// The entry gate and the first-run guide, dismissed the way `critic_shots.mjs`
// does it — a shot taken through the intro overlay is a photograph of the
// overlay, which is how this tool's first evidence pair came out.
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

/** The rig as it ships, read before anything is touched. */
const shipped = await page.evaluate(() => {
  const c = window.__chicago4d.world.light.shadow;
  return {
    half: c.camera.right,
    mapSize: c.mapSize.x,
    near: c.camera.near,
    far: c.camera.far,
    bias: c.bias,
    normalBias: c.normalBias,
  };
});
console.log(`shipped rig: ±${shipped.half} m, ${shipped.mapSize}² map, `
  + `${(2 * shipped.half / shipped.mapSize * 100).toFixed(1)} cm per texel, `
  + `near ${shipped.near} far ${shipped.far}\n`);

const rows = [];
for (const station of STATIONS) {
  await page.evaluate((id) => window.__chicago4d.goTo(id), station.anchor);
  await page.waitForTimeout(400);
  let reference = null;
  for (const [i, reach] of REACHES.entries()) {
    // Hold the texel size the shipped rig has: a reach bought by stretching
    // the same map over more ground is a different change, and conflating them
    // would let a softer shadow be read as a longer one. `--maps` overrides
    // that rule, for measuring a candidate rig as it would actually ship.
    const mapSize = MAPS[i] ?? Math.min(4096, 2 ** Math.round(Math.log2(
      shipped.mapSize * (reach / shipped.half))));
    const got = await page.evaluate(async ({ reach: half, mapSize: size, frames }) => {
      const a = window.__chicago4d;
      const light = a.world.light;
      const sh = light.shadow;
      if (sh.mapSize.x !== size) {
        sh.mapSize.setScalar(size);
        // A shadow map already allocated does not resize itself; dropping it
        // makes three build the next one at the size just asked for.
        sh.map?.dispose();
        sh.map = null;
      }
      sh.camera.left = -half; sh.camera.right = half;
      sh.camera.top = half; sh.camera.bottom = -half;
      sh.camera.updateProjectionMatrix();
      sh.needsUpdate = true;
      const frame = () => new Promise((r) => requestAnimationFrame(() => r()));
      // Two frames: `renderer.info` reports the LAST frame drawn, so reading it
      // straight after a change reports the rig that was replaced.
      await frame(); await frame();

      // ---- what is inside the box, counted off the DATA ----
      //
      // The shadow camera's own matrices decide it, the way three's caster
      // culling does: a point is inside when its clip coordinates are all
      // within ±1. `matrixWorldInverse` is refreshed by the render that just
      // happened, after world.follow() put the box on the walker.
      const p = sh.camera.projectionMatrix.elements;
      const v = sh.camera.matrixWorldInverse.elements;
      const inside = (e, n, y) => {
        // world = (e, y, -n) — terrain.js enuToWorld.
        const x = e; const z = -n;
        const vx = v[0] * x + v[4] * y + v[8] * z + v[12];
        const vy = v[1] * x + v[5] * y + v[9] * z + v[13];
        const vz = v[2] * x + v[6] * y + v[10] * z + v[14];
        const cx = p[0] * vx + p[4] * vy + p[8] * vz + p[12];
        const cy = p[1] * vx + p[5] * vy + p[9] * vz + p[13];
        const cz = p[2] * vx + p[6] * vy + p[10] * vz + p[14];
        return Math.abs(cx) <= 1 && Math.abs(cy) <= 1 && Math.abs(cz) <= 1;
      };
      let structures = 0; let structuresTotal = 0;
      for (const rec of a.registry.values()) {
        const pl = rec?.sidecar?.placement;
        if (!pl || typeof pl.local_e !== 'number' || typeof pl.local_n !== 'number') continue;
        structuresTotal++;
        // Sampled at 2 m, which is inside every roof in the town: a building
        // is a body, and asking only about the ground point under it would
        // count a wall the box cuts through as absent.
        if (inside(pl.local_e, pl.local_n, 2)) structures++;
      }
      let stems = 0; let stemsTotal = 0;
      for (const st of a.trees.group.userData.stations ?? []) {
        stemsTotal++;
        if (inside(st.e, st.n, 3)) stems++;
      }

      // ---- what the frame costs ----
      const times = [];
      let last = performance.now();
      for (let i = 0; i < frames; i++) {
        await frame();
        const now = performance.now();
        times.push(now - last);
        last = now;
      }
      times.sort((x, y) => x - y);
      const s = a.stats();
      return {
        structures, structuresTotal, stems, stemsTotal,
        drawCalls: s.drawCalls, triangles: s.triangles,
        medianFrameMs: +times[Math.floor(times.length / 2)].toFixed(1),
        signature: await a.capture(48),
      };
    }, { reach, mapSize, frames: FRAMES });
    if (shotDir) {
      await page.screenshot({
        path: path.join(shotDir, `${station.id}-${reach}m.png`),
      });
    }
    if (!reference) reference = got.signature;
    const cells = got.signature.cells ?? [];
    const refCells = reference.cells ?? [];
    let changed = 0;
    let worstCell = 0;
    for (let i = 0; i < Math.min(refCells.length, cells.length); i++) {
      const d = Math.abs(refCells[i] - cells[i]);
      if (d > 1) changed++;
      if (d > worstCell) worstCell = d;
    }
    rows.push({
      station: station.id,
      reach,
      mapSize,
      texelCm: +(2 * reach / mapSize * 100).toFixed(1),
      structures: got.structures,
      structuresTotal: got.structuresTotal,
      stems: got.stems,
      stemsTotal: got.stemsTotal,
      drawCalls: got.drawCalls,
      triangles: got.triangles,
      medianFrameMs: got.medianFrameMs,
      meanLuminance: +got.signature.mean.toFixed(2),
      cellsChangedVsShipped: changed,
      worstCellDelta: worstCell,
      signatureCells: refCells.length,
    });
    const r = rows[rows.length - 1];
    console.log(`  ${station.id.padEnd(13)} ±${String(reach).padStart(3)} m  `
      + `${String(mapSize).padStart(4)}²  ${String(r.texelCm).padStart(4)} cm/texel  `
      + `${String(r.structures).padStart(3)}/${r.structuresTotal} structures  `
      + `${String(r.stems).padStart(3)}/${r.stemsTotal} stems  `
      + `${String(r.drawCalls).padStart(3)} calls  ${String(r.triangles).padStart(7)} tris  `
      + `${String(r.medianFrameMs).padStart(6)} ms  mean L ${String(r.meanLuminance).padStart(6)}  `
      + `${String(r.cellsChangedVsShipped).padStart(3)}/${r.signatureCells} cells differ`
      + ` (worst ${r.worstCellDelta})`);
  }
  console.log('');
}

await browser.close();
server.close();

if (errors.length) {
  console.log(`${errors.length} page error(s):`);
  for (const e of errors) console.log(`  - ${e}`);
}

const report = { shipped, viewport: VIEWPORT, published: !wantSource, rows, pageErrors: errors };
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(report, null, 2)}\n`);
process.exit(errors.length ? 1 : 0);
