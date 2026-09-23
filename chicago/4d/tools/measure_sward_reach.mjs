/**
 * T-0225 — WHERE THE SWARD IS DRAWN TO, READ AT A COVERAGE A VISITOR CAN SEE.
 *
 *   node tools/measure_sward_reach.mjs [--source] [--viewport mobile|desktop]
 *
 * THE QUESTION. `tools/smoke_renderer.mjs` part 7 reports the sward's outer
 * boundary by binning the view into 16 bearings and taking, in each, the
 * furthest plant that is actually DRAWN. Everything turns on what "drawn"
 * means, and until T-0225 it meant `flora.fadeAt(...) > 0.02`.
 *
 * `fadeAt` is COVERAGE since T-0035 — the alpha the fragment program resolves
 * through an ordered 4x4 Bayer matrix (`flora.js`, `plantMaterial`):
 *
 *     if (vChiFade < 1.0 && fract(chiBayer4(gl_FragCoord.xy) + vChiDither) >= vChiFade) discard;
 *
 * `chiBayer4` returns (v + 0.5)/16 over v = 0..15, and `vChiDither` slides that
 * whole set of sixteen thresholds by a per-instance phase. So the pixels that
 * survive in a 4x4 tile number floor(16F) or ceil(16F) and nothing between —
 * and BELOW F = 1/16 that is 0 or 1, decided by the instance's dither phase,
 * which is a number no reader this side of the GPU has. At F = 0.02 one phase
 * in three keeps a single pixel of the tile and the other two keep NOTHING.
 *
 * **1/16 is therefore the smallest threshold at which "drawn" is a property of
 * the plant's coverage rather than of its dither phase**, and that is the whole
 * of the justification. It is the screen door's own quantum and not a taste.
 *
 * WHY THE TOOL EXISTS RATHER THAN A RE-RUN OF THE GATE. The gate's part 7 costs
 * about six minutes at the phone and overruns the ten-minute ceiling on a
 * loaded steward runner at the desktop (T-0170, T-0235), so the threshold could
 * not be CHOSEN against readings — only asserted and then gated. This stands at
 * the same station the gate finds, bins the same 16 bearings, and prints the
 * boundary at a sweep of thresholds in about a minute, so the shape of the
 * curve is visible and the choice can be argued from it.
 *
 * WHAT IT PRINTS. Per layer and per threshold: how many of the 16 bearing bins
 * carry a boundary, the min/mean/max reach in metres, and the screen-row spread
 * that ROADMAP § S6a item 3 is about. Beside them, the PLACED boundary — the
 * furthest slot's own outer radius in each bin, no threshold at all — which is
 * the number a reading at 0.02 was very nearly reporting.
 *
 * Defaults to the published mirror for the reason `measure_sward_draw.mjs`
 * does: the source tree and the site do not load the same geometry. The stand
 * is printed and ASSERTED before any figure is believed (T-0162): the sward's
 * ring sizes come off the device guess, not off the window, so a run that asked
 * for the phone and reached the desktop tune refuses to report.
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
const wantSource = process.argv.includes('--source');
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.SWARD_PORT || 4193);
const YEAR = process.env.SWARD_YEAR || '1835';
const vpArg = process.argv.indexOf('--viewport');
const MOBILE = (vpArg > -1 ? process.argv[vpArg + 1] : process.env.SWARD_VIEWPORT) === 'mobile';

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

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
// The smoke's own context options, copied rather than imported for the reason
// `measure_sward_draw.mjs` copies them: the smoke is a script and not a module,
// so a drift makes this tool less complete and never wrong. `hasTouch` is what
// carries the phone to the `light` tune — a bare 390 px window does not.
const VIEWPORT = MOBILE ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const context = await browser.newContext({
  viewport: VIEWPORT,
  hasTouch: MOBILE,
  isMobile: false,
  deviceScaleFactor: MOBILE ? 2 : 1,
});
const page = await context.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

const stand = await page.evaluate(() => {
  const a = window.__chicago4d;
  const coarse = !!(window.matchMedia?.('(pointer: coarse)').matches
    || (navigator.maxTouchPoints > 0 && window.innerWidth < 900));
  return {
    width: window.innerWidth, height: window.innerHeight, detail: a.detail,
    tune: coarse && a.detail === 'full' ? 'light' : a.detail,
  };
});
const wantTune = MOBILE ? 'light' : 'full';
if (stand.tune !== wantTune) {
  console.error(`REFUSING TO REPORT: asked for the ${MOBILE ? 'mobile' : 'desktop'} stand and `
    + `reached the '${stand.tune}' tune, not '${wantTune}' (T-0162).`);
  await browser.close();
  server.close();
  process.exit(2);
}
console.log(`stand: ${MOBILE ? 'MOBILE' : 'desktop'} ${stand.width}x${stand.height} — `
  + `detail ${stand.detail}, sward tune ${stand.tune}\n`);

const out = await page.evaluate(() => {
  const a = window.__chicago4d;
  const SETS = { 'flora-mid': 'mid', 'flora-forb': 'forb' };
  // The gate's own station search, verbatim — the reading is only comparable to
  // the gate's if it is taken from the same ground.
  const dense = new Set(a.flora.communities()
    .filter((c) => c.graminoids && c.matrixShare >= 0.7).map((c) => c.id));
  const R = a.flora.rings.layers.mid.lattice.outer;
  const clear = (e, n) => {
    for (let k = 0; k < 12; k++) {
      const t = (k / 12) * Math.PI * 2;
      for (const rr of [R * 0.45, R * 0.75, R]) {
        const pe = e + Math.cos(t) * rr;
        const pn = n + Math.sin(t) * rr;
        if (!dense.has(a.flora.zoneAt(pe, pn))) return false;
        if (!a.flora.plantableAt(pe, pn)) return false;
      }
    }
    return dense.has(a.flora.zoneAt(e, n)) && a.flora.plantableAt(e, n);
  };
  let station = null;
  for (let e = -300; e <= 900 && !station; e += 8) {
    for (let n = -300; n <= 500 && !station; n += 8) {
      if (clear(e, n)) station = { e, n };
    }
  }
  if (!station) return { station: null };
  a.walker.teleport({ local_e: station.e, local_n: station.n, yaw_deg: 0 });
  a.step();
  a.step();
  const cam = a.camera.position;
  const f = cam.clone();
  a.camera.getWorldDirection(f);
  const fwd = Math.atan2(f.x, -f.z);
  const H = a.renderer.domElement.height;
  const halfTan = Math.tan((a.camera.fov * Math.PI / 180) / 2);
  const rowOf = (d, groundY) => (H / 2) * ((cam.y - groundY) / d) / halfTan;

  const BINS = 16;
  const HALF = 30 * Math.PI / 180;
  // 0.02 is what the gate read before T-0225; 1/16 is the screen door's quantum
  // and what it reads now; the rungs above it are here so the choice can be
  // read off a curve rather than off one number. `null` is the PLACED boundary
  // — every slot in the bin, whatever its coverage.
  const LEVELS = [null, 0.02, 1 / 16, 2 / 16, 3 / 16, 4 / 16];
  const out = { station, layers: {} };
  for (const [name, layer] of Object.entries(SETS)) {
    const mesh = a.flora.group.getObjectByName(name);
    const m = mesh?.instanceMatrix?.array;
    const ring = mesh?.geometry.getAttribute('aChiRing')?.array;
    const r = a.flora.rings.layers[layer];
    const bins = LEVELS.map(() => new Array(BINS).fill(null));
    for (let i = 0; m && ring && i < mesh.count; i++) {
      const o = i * 16;
      const e = m[o + 12];
      const n = -m[o + 14];
      const y = m[o + 13];
      const da = ((Math.atan2(e - cam.x, n + cam.z) - fwd + Math.PI * 3)
        % (Math.PI * 2)) - Math.PI;
      if (Math.abs(da) > HALF) continue;
      const d = Math.hypot(e - cam.x, n + cam.z);
      const fade = a.flora.fadeAt(name, d, [ring[i * 4], ring[i * 4 + 1],
        ring[i * 4 + 2], ring[i * 4 + 3]]);
      const b = Math.min(BINS - 1, Math.floor((da + HALF) / (2 * HALF / BINS)));
      LEVELS.forEach((lv, k) => {
        // `null` takes every slot in the bin. 0.02 is read STRICTLY, because
        // that is how the gate read it (`fadeAt(...) <= 0.02` culled) and a
        // before/after that changed the comparison as well as the number would
        // not be a before/after. The rungs at k/16 are read inclusively, which
        // is what "keeps at least one pixel in the tile" means.
        if (lv !== null && (lv === 0.02 ? fade <= lv : fade < lv)) return;
        if (!bins[k][b] || d > bins[k][b].d) bins[k][b] = { d, y };
      });
    }
    out.layers[layer] = {
      nominal: r.fade[0], fringe: r.fringe ?? 0, band: r.fade[1],
      rows: LEVELS.map((lv, k) => {
        const used = bins[k].filter(Boolean);
        const reach = used.map((b) => b.d);
        const rows = used.map((b) => rowOf(b.d, b.y));
        return {
          level: lv,
          bins: used.length,
          spreadPx: rows.length ? Math.max(...rows) - Math.min(...rows) : 0,
          min: reach.length ? Math.min(...reach) : 0,
          max: reach.length ? Math.max(...reach) : 0,
          mean: reach.length ? reach.reduce((s, v) => s + v, 0) / reach.length : 0,
        };
      }),
    };
  }
  return out;
});

if (!out.station) {
  console.error('no dense-matrix community covers a whole ring radius anywhere in the box');
  await browser.close();
  server.close();
  process.exit(2);
}
console.log(`station: E ${out.station.e} N ${out.station.n}, 16 bearing bins over +/-30 deg\n`);
for (const [layer, L] of Object.entries(out.layers)) {
  console.log(`${layer} ring — nominal ${L.nominal.toFixed(2)} m +/- ${L.fringe.toFixed(2)} m `
    + `fringe, ${L.band.toFixed(2)} m ramp`);
  // The bars are the MID ring's, and only the mid ring is held to them: the
  // gate reads the forb boundary off its RINGS rather than off its drawn edge,
  // because at 3.4 m cells a 3.75-degree bin holds one or two forbs and "the
  // furthest one drawn" is a sampling statistic. The forb rows below are
  // printed against the same bars anyway, and the `OVER` they collect is that
  // fact rather than a defect — 11 or 12 bins of 16 and a 4.47 m minimum is
  // what sampling a sparse layer by bearing looks like.
  console.log('  threshold      bins   min      mean     max      rows    bars (min / mean)');
  for (const r of L.rows) {
    // The bars the gate holds the mid ring to, carrying the inset the threshold
    // costs: a linear ramp reaches coverage F at `outer - F x band`, so a
    // reading at F sits that far inside the boundary the placer assigned.
    const inset = r.level === null ? 0 : L.band * r.level;
    const barMin = L.nominal - L.fringe - 1.2 - inset;
    const barMean = L.nominal - 0.5 * L.fringe - inset;
    const label = r.level === null ? 'placed' : `${(r.level * 100).toFixed(2)}%`;
    console.log(`  ${label.padEnd(13)}${String(r.bins).padStart(3)}/16 `
      + `${r.min.toFixed(2).padStart(7)} ${r.mean.toFixed(2).padStart(8)} `
      + `${r.max.toFixed(2).padStart(8)} ${r.spreadPx.toFixed(1).padStart(7)} px  `
      + `${barMin.toFixed(2)} / ${barMean.toFixed(2)}`
      + `${r.min >= barMin && r.mean >= barMean ? '' : '   OVER'}`);
  }
  console.log('');
}
if (errors.length) console.log(`page errors: ${errors.length}\n${errors.join('\n')}`);
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
