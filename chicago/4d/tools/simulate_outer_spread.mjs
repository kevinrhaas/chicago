/**
 * T-0277 — WHAT A DENSITY HANDOVER WOULD COST ON THE TWO OUTER EDGES, PRICED
 * AGAINST THE STATISTIC THE GATE ACTUALLY READS.
 *
 *   node tools/simulate_outer_spread.mjs [--source] [--viewport mobile|desktop]
 *
 * THE QUESTION. `TUNE.mid.band` and `TUNE.forb.band` are the last two coverage
 * ramps in the sward. Every other boundary — the near ring's outer edge, the
 * mid ring's inner one, both far bands — hands its ground over by DENSITY
 * (`spreadOuter`/`spreadInner`, T-0093/T-0086): each slot carries its own
 * boundary, drawn from a world-anchored rank, and a plant is drawn whole or not
 * at all. These two still ramp, so the last few metres of the sward are drawn
 * through the 4x4 screen door — a band of dots resolved per pixel.
 *
 * T-0187 priced the change and kept the ramp, and its arithmetic is not in
 * dispute. What was wrong was the RULER. Every figure it compared against was
 * read at `fadeAt > 0.02`, a coverage the screen door renders as nothing
 * whatever for two instance phases in three (T-0225), so a coverage ramp was
 * being credited with reach no visitor could see. The gate reads the boundary
 * at 1/16 now — the screen door's own quantum — and carries the `band x 1/16`
 * inset that costs. So the comparison a spread has to win is a different one,
 * and T-0277 is the re-run.
 *
 * WHAT IT DOES. It stands where `tools/measure_sward_reach.mjs` and the gate's
 * part 7 stand, bins the same 16 bearings over the same +/-30 deg cone, and for
 * every placed instance of the mid and forb layers reports the drawn boundary
 * under BOTH representations:
 *
 *   ramp    the plant is drawn where `flora.fadeAt(...) >= 1/16` — today's
 *           reading, and the same one `measure_sward_reach.mjs` prints.
 *   spread  the plant is drawn where `d <= slotOuter`, with
 *           `slotOuter = ring[0] - band x handoverRank(e, n, 0)` — `slotRing`'s
 *           own arithmetic, on this slot's own `aChiRing` and this ground's own
 *           rank, asked of the placer through `flora.handoverAt`.
 *
 * AND IT MOVES THE BARS WITH THE REPRESENTATION, which is the whole reason the
 * answer could not simply be read off `measure_sward_reach.mjs`. `ringsFor`
 * replaces a spread layer's `band` with `HARD`, so the inset a reading at 1/16
 * costs — `band x 1/16`, 0.44 m on the desktop mid ring — VANISHES when the
 * band is spread. A spread therefore has to clear a HIGHER bar with a SHORTER
 * reach. Printing it against the ramp's own bars would flatter it by 0.44 m.
 *
 * A partial spread is priced too: spreading only the outer `x` of the band
 * costs less reach, and the bar moves with it (`HARD` applies to the whole
 * band either way, so any spread at all pays the full bar). The rungs are there
 * so the choice can be read off a curve rather than off one number, exactly as
 * `measure_sward_reach.mjs`'s threshold sweep is.
 *
 * THE FORB ROWS ARE PRINTED AND NOT HELD. The gate reads the forb boundary off
 * its rings rather than off its drawn edge, because at 3.4 m cells a 3.75-deg
 * bin holds one or two forbs and "the furthest one drawn" is a sampling
 * statistic — `measure_sward_reach.mjs` says so at length and collects the same
 * `OVER`s on an unmodified tree. They are here because the ticket asks for both
 * edges, and because a sampled layer is exactly where a density handover is
 * most expensive.
 *
 * The stand is asserted before any figure is believed (T-0162), the same way.
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
const PORT = Number(process.env.SWARD_PORT || 4194);
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
// `typeof` is taken INSIDE the page: Playwright serialises an evaluate's
// result, and a function comes back as `undefined` however live it is.
if (!await page.evaluate(() => typeof window.__chicago4d.flora.handoverAt === 'function')) {
  console.error('this tree\'s flora module does not offer handoverAt — the rank cannot be '
    + 'asked of the placer, and re-deriving it here would price the tool\'s copy of the hash.');
  await browser.close();
  server.close();
  process.exit(2);
}
console.log(`stand: ${MOBILE ? 'MOBILE' : 'desktop'} ${stand.width}x${stand.height} — `
  + `detail ${stand.detail}, sward tune ${stand.tune}\n`);

const out = await page.evaluate(() => {
  const a = window.__chicago4d;
  const SETS = { 'flora-mid': 'mid', 'flora-forb': 'forb' };
  // The gate's own station search, verbatim — see measure_sward_reach.mjs.
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
  const GATE = 1 / 16;
  // How much of the band is handed over by density. 0 is today's ramp; 1 is the
  // full spread T-0187 priced. The rungs between are what a partial handover
  // would cost — the ramp keeps the rest, but `ringsFor` makes the whole band
  // `HARD` the moment a boundary is spread, so every rung pays the same bar.
  const SHARES = [0, 0.25, 0.5, 0.75, 1];
  const out = { station, layers: {} };
  for (const [name, layer] of Object.entries(SETS)) {
    const mesh = a.flora.group.getObjectByName(name);
    const m = mesh?.instanceMatrix?.array;
    const ring = mesh?.geometry.getAttribute('aChiRing')?.array;
    const r = a.flora.rings.layers[layer];
    // One set of bins for today's reading at the gate's threshold, and one per
    // spread share. `placed` is the furthest slot in the bin at any coverage.
    const placedBins = new Array(BINS).fill(null);
    const rampBins = new Array(BINS).fill(null);
    const spreadBins = SHARES.map(() => new Array(BINS).fill(null));
    let slots = 0;
    for (let i = 0; m && ring && i < mesh.count; i++) {
      const o = i * 16;
      const e = m[o + 12];
      const n = -m[o + 14];
      const y = m[o + 13];
      const da = ((Math.atan2(e - cam.x, n + cam.z) - fwd + Math.PI * 3)
        % (Math.PI * 2)) - Math.PI;
      if (Math.abs(da) > HALF) continue;
      slots++;
      const d = Math.hypot(e - cam.x, n + cam.z);
      const b = Math.min(BINS - 1, Math.floor((da + HALF) / (2 * HALF / BINS)));
      const slotOuter = ring[i * 4];
      const band = ring[i * 4 + 1];
      const keep = (bins, hit) => {
        if (hit && (!bins[b] || d > bins[b].d)) bins[b] = { d, y };
      };
      keep(placedBins, true);
      // Today: the shader's own ramp, read at the screen door's quantum.
      const fade = a.flora.fadeAt(name, d, [slotOuter, band,
        ring[i * 4 + 2], ring[i * 4 + 3]]);
      keep(rampBins, fade >= GATE);
      // `slotRing`'s arithmetic, with the rank asked of the placer.
      const rank = a.flora.handoverAt(e, n, 0);
      SHARES.forEach((share, k) => {
        keep(spreadBins[k], d <= slotOuter - band * share * rank);
      });
    }
    const row = (bins, label, inset) => {
      const used = bins.filter(Boolean);
      const reach = used.map((x) => x.d);
      const rows = used.map((x) => rowOf(x.d, x.y));
      return {
        label,
        inset,
        bins: used.length,
        spreadPx: rows.length ? Math.max(...rows) - Math.min(...rows) : 0,
        min: reach.length ? Math.min(...reach) : 0,
        max: reach.length ? Math.max(...reach) : 0,
        mean: reach.length ? reach.reduce((s, v) => s + v, 0) / reach.length : 0,
      };
    };
    out.layers[layer] = {
      nominal: r.fade[0], fringe: r.fringe ?? 0, band: r.fade[1], slots,
      rows: [
        row(placedBins, 'placed', 0),
        // The ramp keeps its band, so a reading at 1/16 sits `band/16` inside
        // the boundary the placer assigned and the bar is lowered by that much.
        row(rampBins, 'ramp @1/16', r.fade[1] * GATE),
        // A spread draws whole plants, so there is no inset to allow — the bar
        // stands at the placer's own boundary. See `ringsFor`: any spread at
        // all replaces the band with `HARD`.
        ...SHARES.map((share, k) => row(spreadBins[k],
          `spread ${(share * 100).toFixed(0)}%`, 0)),
      ],
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
let verdict = [];
for (const [layer, L] of Object.entries(out.layers)) {
  console.log(`${layer} ring — nominal ${L.nominal.toFixed(2)} m +/- ${L.fringe.toFixed(2)} m `
    + `fringe, ${L.band.toFixed(2)} m ramp, ${L.slots} slots in the cone`);
  console.log('  representation   bins   min      mean     max      rows    bars (min / mean)');
  for (const r of L.rows) {
    const barMin = L.nominal - L.fringe - 1.2 - r.inset;
    const barMean = L.nominal - 0.5 * L.fringe - r.inset;
    const clears = r.min >= barMin && r.mean >= barMean;
    console.log(`  ${r.label.padEnd(16)}${String(r.bins).padStart(3)}/16 `
      + `${r.min.toFixed(2).padStart(7)} ${r.mean.toFixed(2).padStart(8)} `
      + `${r.max.toFixed(2).padStart(8)} ${r.spreadPx.toFixed(1).padStart(7)} px  `
      + `${barMin.toFixed(2)} / ${barMean.toFixed(2)}${clears ? '' : '   OVER'}`);
    if (r.label === 'spread 100%') verdict.push(`${layer}: ${clears ? 'clears' : 'OVER'}`);
  }
  console.log('');
}
console.log(`full spread — ${verdict.join(', ')}`);
if (errors.length) console.log(`page errors: ${errors.length}\n${errors.join('\n')}`);
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
