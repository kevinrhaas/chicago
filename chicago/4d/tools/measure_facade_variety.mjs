/**
 * Does the town wear more than one face? — T-0002 (legacy K4).
 *
 * The owner reported that the buildings "read as freshly painted and
 * identical", and until this parcel the second half of that was exact: a wall's
 * colour came from its archetype, so two neighbours of the same archetype were
 * the same brown to the bit. `renderers/web/js/facades.js` gives every
 * structure its own tone; this measures what that actually did, in the
 * browser, off the colour attribute the batch draws.
 *
 * Four questions, in the order they can go wrong:
 *
 *  1. **How many distinct facades does the town draw?** Read per structure from
 *     the batch, not from the tone the module intended.
 *  2. **Do NEIGHBOURS differ?** A town of 333 distinct colours dealt so that
 *     every pair of adjacent houses landed on the same one would satisfy 1 and
 *     fail the ask. Every structure is matched to its nearest neighbour and the
 *     pair's difference in luminance reported as a distribution — including its
 *     bottom tail, because a random deal HAS ties and hiding them would be the
 *     same dishonesty as claiming they do not exist.
 *  3. **Is the documented paint untouched?** The two records whose paint a
 *     source attests must be drawn at exactly the colour their archetype baked,
 *     with the tone at full and with it wound off. Bit-exact, not close.
 *  4. **Does any of it reach the render?** The tone is wound to 0 and the frame
 *     photographed; a difference that never reaches a pixel is not a change to
 *     the town. Then wound back, and the frame compared with the first — a
 *     control that does not restore is a control that has broken something.
 *
 * NOT in `tools/check.sh`: it drives a real browser. It is a measurement to be
 * re-run and quoted, in the shape of `tools/measure_shipped_batches.mjs`; the
 * standing assertions live in `tools/smoke_renderer.mjs`.
 *
 *   node tools/measure_facade_variety.mjs            the published mirror
 *   node tools/measure_facade_variety.mjs --source   the source tree
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = process.argv.includes('--source');
// The source tree is served from the APP ROOT, not from `renderers/web`:
// `scene-loader.js` tells the two layouts apart by the page's own path, so a
// dev page has to be reached at `/renderers/web/index.html` or it looks for the
// dataset where the published mirror keeps it and finds nothing.
const ROOT = SOURCE ? APP : path.resolve(APP, '../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.FACADE_PORT || 4293);
/** `--mobile` runs the release suite's smaller viewport, because a frame-delta
 *  floor set from the desktop reading alone is a floor the mobile half has
 *  never been measured against. */
const VIEWPORT = process.argv.includes('--mobile')
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };
/** How near two structures must be to count as neighbours, in metres. */
const NEAR_M = 60;

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.glb': 'model/gltf-binary', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.bin': 'application/octet-stream', '.md': 'text/markdown',
  '.webp': 'image/webp', '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); res.end('not here'); return;
  }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] ?? 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));

const { chromium } = await import('playwright');
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const page = await browser.newPage({ viewport: VIEWPORT });
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=1835`);
try {
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180_000 });
} catch (err) {
  console.log(`the scene never became ready: ${err.message}`);
  if (pageErrors.length) console.log(`page errors: ${pageErrors.join(' | ')}`);
  const boot = await page.evaluate(() => window.__chicago4d?.error ?? null).catch(() => null);
  if (boot) console.log(`boot error: ${boot}`);
  await browser.close(); server.close();
  process.exit(1);
}

const read = () => page.evaluate((near) => {
  const api = window.__chicago4d;
  const tones = api.buildings.facadeTones();
  const rows = Object.entries(tones).map(([id, t]) => {
    const p = api.buildings.positionOf(id);
    return { id, ...t, x: p ? p.x : null, z: p ? p.z : null };
  });
  return { rows, near, weathering: api.facadeWeathering, batches: api.buildings.batches.length };
}, NEAR_M);

const lum = (c) => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
const quant = (a, p) => (a.length ? a[Math.min(a.length - 1, Math.floor(p * (a.length - 1)))] : NaN);

// --- 1 + 2 + 3, with the tone at full ------------------------------------- //
await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
const full = await read();
const drawnFull = new Map(full.rows.map((r) => [r.id, r.drawn]));

const withColour = full.rows.filter((r) => r.drawn);
const distinct = new Set(withColour.map((r) => r.drawn.map((v) => v.toFixed(6)).join(','))).size;
const eligible = full.rows.filter((r) => r.eligible);
const excluded = full.rows.filter((r) => !r.eligible);
const silvered = full.rows.filter((r) => r.silver > 0.05);

const placed = withColour.filter((r) => Number.isFinite(r.x));
const pairs = [];
for (const a of placed) {
  let best = null; let bd = Infinity;
  for (const b of placed) {
    if (b === a) continue;
    const d = Math.hypot(a.x - b.x, a.z - b.z);
    if (d < bd) { bd = d; best = b; }
  }
  if (best && bd <= NEAR_M) {
    pairs.push({ a: a.id, b: best.id, m: bd, dL: Math.abs(lum(a.drawn) - lum(best.drawn)) });
  }
}
const dLs = pairs.map((p) => p.dL).sort((x, y) => x - y);
const meanL = withColour.reduce((s, r) => s + lum(r.drawn), 0) / (withColour.length || 1);

/**
 * The same pairs, evaluated on a reading.
 *
 * This is here because the raw figure above is CONFOUNDED and saying so is the
 * point: a structure's drawn colour is the mean over all its surfaces, so two
 * neighbours with different material mixes differ whatever this module does.
 * The attributable number is the pairs' difference with the tone wound OFF —
 * the archetype town — against the same pairs with it on.
 */
const pairStats = (rows) => {
  const by = new Map(rows.map((r) => [r.id, r.drawn]));
  const ds = pairs
    .map((p) => (by.get(p.a) && by.get(p.b)
      ? Math.abs(lum(by.get(p.a)) - lum(by.get(p.b))) : null))
    .filter((d) => d !== null)
    .sort((x, y) => x - y);
  return { ds, same: ds.filter((d) => d < 1e-6).length };
};

// --- 4: does it reach a pixel, and does it come back ----------------------- //
const grid = 48;
const before = await page.evaluate((g) => window.__chicago4d.capture(g), grid);
const off = await page.evaluate(() => window.__chicago4d.setFacadeWeathering(0));
const offRead = await read();
const flat = await page.evaluate((g) => window.__chicago4d.capture(g), grid);
const back = await page.evaluate(() => window.__chicago4d.setFacadeWeathering(1));
const restoredRead = await read();
const after = await page.evaluate((g) => window.__chicago4d.capture(g), grid);
await page.evaluate(() => window.__chicago4d.setAnimationHold(false));

/** The same cell-signature distance `tools/smoke_renderer.mjs` uses, so a
 *  number quoted here and a number quoted there mean the same thing. */
const signature = (x, y) => {
  if (!x?.cells || !y?.cells || x.cells.length !== y.cells.length) {
    return { worst: Infinity, mean: Infinity };
  }
  let worst = 0; let sum = 0;
  for (let i = 0; i < x.cells.length; i += 1) {
    const d = Math.abs(x.cells[i] - y.cells[i]);
    if (d > worst) worst = d;
    sum += d;
  }
  return { worst, mean: sum / x.cells.length };
};
const dFlat = signature(before, flat);
const dBack = signature(before, after);

const movedOff = offRead.rows.filter((r) => {
  const was = drawnFull.get(r.id);
  return was && r.drawn && r.drawn.some((v, i) => Math.abs(v - was[i]) > 1e-6);
}).length;
const excludedMoved = excluded.filter((r) => {
  const was = drawnFull.get(r.id);
  const now = offRead.rows.find((q) => q.id === r.id)?.drawn;
  return was && now && now.some((v, i) => v !== was[i]);
});
const restoreError = Math.max(0, ...restoredRead.rows.map((r) => {
  const was = drawnFull.get(r.id);
  return was && r.drawn ? Math.max(...r.drawn.map((v, i) => Math.abs(v - was[i]))) : 0;
}));

await browser.close();
server.close();

const pct = (v) => `${((v / meanL) * 100).toFixed(1)} %`;
console.log(`${SOURCE ? 'SOURCE tree' : 'PUBLISHED mirror'} at ${VIEWPORT.width}x${VIEWPORT.height} `
  + `— ${full.rows.length} structure(s), ${full.batches} batch(es), `
  + `weathering ${full.weathering}`);
console.log(`  1. ${distinct} distinct drawn facade tones across ${withColour.length} structures`);
console.log(`  2. ${pairs.length} nearest-neighbour pairs within ${NEAR_M} m: `
  + `median |dL| ${quant(dLs, 0.5).toFixed(5)} (${pct(quant(dLs, 0.5))} of mean facade luminance), `
  + `p10 ${quant(dLs, 0.1).toFixed(5)} (${pct(quant(dLs, 0.1))}), `
  + `min ${quant(dLs, 0).toFixed(5)}, max ${quant(dLs, 1).toFixed(5)}; `
  + `${dLs.filter((d) => d < 1e-6).length} identical`);
console.log(`  3. ${eligible.length} eligible, ${excluded.length} excluded: `
  + `${excluded.map((r) => `${r.id} (${r.reason})`).join('; ') || 'none'}`);
console.log(`     ${silvered.length} structure(s) silvered by age; `
  + `${excludedMoved.length} documented-paint record(s) moved when the tone was wound off `
  + '(want 0)');
/**
 * The cleanest statement of what a visitor sees, and the one the mean above
 * cannot make: two neighbours' tones differ by this fraction on EVERY surface
 * they share an archetype for, wall for wall and roof for roof.
 */
const byId = new Map(full.rows.map((r) => [r.id, r]));
const factorPairs = pairs.map((p) => {
  const a = byId.get(p.a); const b = byId.get(p.b);
  return Math.abs(a.value * (1 - a.soil) - b.value * (1 - b.soil));
}).sort((x, y) => x - y);
console.log(`  2c. neighbour pairs differ in applied VALUE by a median of `
  + `${(quant(factorPairs, 0.5) * 100).toFixed(1)} %, p10 `
  + `${(quant(factorPairs, 0.1) * 100).toFixed(1)} %, max `
  + `${(quant(factorPairs, 1) * 100).toFixed(1)} % — the same factor on every surface `
  + 'of the building');

const offPairs = pairStats(offRead.rows);
const onPairs = pairStats(full.rows);
console.log(`  2b. the same pairs with the tone wound OFF (the archetype town): `
  + `median |dL| ${quant(offPairs.ds, 0.5).toFixed(5)}, `
  + `${offPairs.same} of ${offPairs.ds.length} indistinguishable; `
  + `with it ON: median ${quant(onPairs.ds, 0.5).toFixed(5)}, ${onPairs.same} indistinguishable`);
console.log(`  4. tone off: ${movedOff} structure(s) changed colour, frame delta mean `
  + `${dFlat.mean.toFixed(2)} / worst ${dFlat.worst} at ${grid}²; restored (${back}): `
  + `residual mean ${dBack.mean.toFixed(2)} / worst ${dBack.worst}, `
  + `worst per-structure restore error ${restoreError.toExponential(2)}`);
console.log(`     setFacadeWeathering(0) read back ${off}`);
if (pageErrors.length) {
  console.log(`  PAGE ERRORS (${pageErrors.length}): ${pageErrors.slice(0, 3).join(' | ')}`);
  process.exitCode = 1;
}
