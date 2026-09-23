/**
 * measure_far_split.mjs — T-0280, then T-1106: what the far band's
 * grass-or-flower split was made on, what it is made on now, and what that
 * moves. Three columns, because there have been three answers.
 *
 *   node tools/measure_far_split.mjs              the published mirror
 *   node tools/measure_far_split.mjs --source     the working tree
 *   FAR_SPLIT_VIEWPORT=mobile node tools/measure_far_split.mjs
 *
 * THE QUESTION. `rebuildFar` deals a far card as grass or as a flowering plant
 * with
 *
 *     split = matrixShare * (1 - forbside / (matrixShare + forbside))
 *
 * so the forb's share of the cards the band occupies is exactly
 *
 *     forbside / (matrixShare + forbside)
 *
 * and the whole ticket is about WHICH NUMBER `forbside` is. It was `forbShare`,
 * the forb RING's lattice occupancy, `min(1, density x cell^2 / perCell)` — a
 * probability, clamped at one plant per 2.89 m^2 slot, and nine of the ten
 * populated forb layers sit on that clamp. It is now the forb subset's own
 * AREAL COVER, `sum stems x pi (width/2)^2`, which is the unit `matrixShare`
 * (`cover.matrix_fraction`) is already in and is bounded by no lattice.
 *
 * T-1106 CHANGED THE UNIT AGAIN, and this tool gained its third column. Areal
 * cover is the honest mix for GROUND; the far band is a WALL. Its nearest card
 * stands 34 m from the visitor and its furthest 95, and at fifty metres a 1.7 m
 * eye looks 1.9 degrees below horizontal — the sward is seen edge-on and the
 * plant that fills a pixel is the first element the ray meets. So `forbside` is
 * now the forb subset's SILHOUETTE-AREA DENSITY, `sum stems x w x h`, and the
 * matrix side is the record's own `matrix_fraction` converted by the graminoid
 * stratum's own measured aspect `sil / cover`. It is the model
 * `measure_far_bloom.mjs` §1 has priced the BLOOM on since T-0209.
 *
 * All three numbers are exported by `flora.communities()` — `forbShare` beside
 * `forbCover` beside `forbSil` — so T-0209, T-0280 and T-1106 here are
 * arithmetic on the renderer's own compiled communities, not three runs compared
 * by hand. §1 is that table.
 *
 * §2 asks what a visitor actually stands in front of. A stand sees whatever
 * communities its far band's annulus lands on, so the tool samples that annulus
 * with the placer's own `zoneAt` and `isWaterAt`, weights each sample by
 * `farBand.coverAt(d)` — the fraction of ground carrying a card at that
 * distance — and reports the stand's aggregate flower-card share before and
 * after. `prairie_west` is the stand T-0209's acceptance was written against and
 * is reported first.
 *
 * §3 is the drawn bloom that follows from it: the heads the renderer actually
 * puts past the forb ring at each stand, which is the figure T-1106 was raised
 * over. `tools/measure_far_bloom.mjs --source` is the fuller reach measurement.
 *
 * NOT in `tools/check.sh`: it drives a real browser.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const SOURCE = process.argv.slice(2).includes('--source');

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

const ROOT = SOURCE ? APP : path.resolve(APP, '../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.FAR_SPLIT_PORT || 4399);
const YEAR = process.env.FAR_SPLIT_YEAR || '1835';
const VIEWPORT = process.env.FAR_SPLIT_VIEWPORT === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };

/** `measure_far_bloom.mjs`'s three stands, verbatim, `prairie_west` first. */
const STANDS = [
  { id: 'prairie_west', e: -250, n: -150, yaw: 90 },
  { id: 'prairie_south', e: 120, n: -330, yaw: 90 },
  { id: 'river_bank', e: 180, n: 0, yaw: 0 },
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

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

const report = await page.evaluate((stands) => {
  const a = window.__chicago4d;
  const f = a.flora;
  const communities = f.communities();
  const lattice = f.forbLattice;
  const band = f.farBand;

  /** The forb's share of the cards the far band occupies, for a given forb-side
   *  quantity. Zero matrix cover means the band occupies nothing there, so the
   *  share is undefined rather than nought. */
  const mixOf = (matrixShare, forbSide) => (
    matrixShare > 0 && forbSide > 0 ? forbSide / (matrixShare + forbSide)
      : (matrixShare > 0 ? 0 : null));

  const rows = communities.map((c) => {
    /** The matrix side the placer deals on since T-1106: the record's own
     *  `matrix_fraction` in the silhouette unit, by the graminoid stratum's own
     *  aspect. A stratum with no silhouette to convert by keeps the cover
     *  reading, exactly as `farSplitOf` does. */
    const mSil = c.matrixSilAspect === null ? null : c.matrixShare * c.matrixSilAspect;
    const mSilWet = c.matrixSilAspectWet === null ? null : c.matrixShare * c.matrixSilAspectWet;
    return {
      id: c.id,
      matrixShare: c.matrixShare,
      matrixCover: c.matrixCover,
      forbShare: c.forbShare,
      forbShareWet: c.forbShareWet,
      forbDensity: c.forbDensity,
      forbCover: c.forbCover,
      forbCoverWet: c.forbCoverWet,
      forbCoverHigh: c.forbCoverHigh,
      matrixSil: c.matrixSil,
      matrixSilAspect: c.matrixSilAspect,
      matrixSilAspectWet: c.matrixSilAspectWet,
      forbSil: c.forbSil,
      forbSilWet: c.forbSilWet,
      forbSilAspect: c.forbSilAspect,
      forbSilAspectWet: c.forbSilAspectWet,
      coverUnknown: c.coverUnknown,
      silUnknown: c.silUnknown,
      fallbacks: c.forbCoverFallbacks,
      fallbacksWet: c.forbCoverFallbacksWet,
      clamped: c.forbShare >= 1,
      before: mixOf(c.matrixShare, c.forbShare),
      after: mixOf(c.matrixShare, c.forbCover),
      now: mSil === null ? mixOf(c.matrixShare, c.forbCover) : mixOf(mSil, c.forbSil),
      beforeWet: mixOf(c.matrixShare, c.forbShareWet),
      afterWet: mixOf(c.matrixShare, c.forbCoverWet),
      nowWet: mSilWet === null
        ? mixOf(c.matrixShare, c.forbCoverWet) : mixOf(mSilWet, c.forbSilWet),
    };
  });
  const byId = new Map(rows.map((r) => [r.id, r]));

  // §2 — the ground the far band's annulus actually covers, sampled with the
  // placer's own zone finder and waterline. Polar, so the sample density
  // follows the annulus rather than a square that mostly misses it; the weight
  // is the ring's own area element r·dr·dθ times `coverAt(d)`, the fraction of
  // that ground carrying a card.
  const inner = Math.min(...band.bands.map((b) => b.inner));
  const outer = Math.max(...band.bands.map((b) => b.radius));
  const NR = 160;
  const NT = 360;
  const dr = (outer - inner) / NR;
  const dt = (2 * Math.PI) / NT;
  const stood = [];
  for (const st of stands) {
    const ground = new Map();
    let weight = 0;
    let unzoned = 0;
    for (let i = 0; i < NR; i++) {
      const r = inner + (i + 0.5) * dr;
      const cover = band.coverAt(r);
      if (!(cover > 0)) continue;
      const w = cover * r * dr * dt;
      for (let j = 0; j < NT; j++) {
        const th = (j + 0.5) * dt;
        const e = st.e + r * Math.cos(th);
        const n = st.n + r * Math.sin(th);
        const id = f.zoneAt(e, n);
        if (!id) { unzoned += w; continue; }
        const wet = f.isWaterAt(e, n);
        const key = `${id}|${wet ? 'wet' : 'dry'}`;
        ground.set(key, (ground.get(key) ?? 0) + w);
        weight += w;
      }
    }
    let before = 0;
    let after = 0;
    let nowAgg = 0;
    const parts = [];
    for (const [key, w] of [...ground.entries()].sort((x, y) => y[1] - x[1])) {
      const [id, side] = key.split('|');
      const row = byId.get(id);
      if (!row) continue;
      const b = side === 'wet' ? row.beforeWet : row.before;
      const f2 = side === 'wet' ? row.afterWet : row.after;
      const f3 = side === 'wet' ? row.nowWet : row.now;
      if (b === null || f2 === null || f3 === null) continue;
      before += (w / weight) * b;
      after += (w / weight) * f2;
      nowAgg += (w / weight) * f3;
      parts.push({ id, side, share: w / weight, b, a: f2, s: f3 });
    }
    // And the drawn frame at the same stand, so the modelled share sits beside
    // what the renderer put on screen: far cards, and the heads only a far
    // FORB card past the forb ring can be carrying.
    const camera = {
      getWorldPosition: (v) => { v.set(st.e, 1.7, -st.n); return v; },
      getWorldDirection: (v) => {
        const rad = (st.yaw * Math.PI) / 180;
        v.set(Math.sin(rad), 0, -Math.cos(rad));
        return v;
      },
    };
    f.update(0.016, camera);
    f.update(0.016, camera);
    let headsPastRing = 0;
    let heads = 0;
    f.group.traverse((m) => {
      if (!m.isInstancedMesh || !m.name.startsWith('flora-head-')) return;
      const arr = m.instanceMatrix.array;
      for (let i = 0; i < m.count; i++) {
        const x = arr[i * 16 + 12];
        const z = arr[i * 16 + 14];
        const d = Math.hypot(x - st.e, z - (-st.n));
        heads++;
        if (d > inner) headsPastRing++;
      }
    });
    stood.push({
      id: st.id,
      zone: f.zoneAt(st.e, st.n),
      before,
      after,
      now: nowAgg,
      unzoned: unzoned / (weight + unzoned),
      parts: parts.slice(0, 5),
      farCards: f.stats.sets['flora-far'] ?? 0,
      heads,
      headsPastRing,
    });
  }
  return { rows, lattice, stood, inner, outer };
}, STANDS);

const pct = (x) => (x === null ? '     —' : `${(x * 100).toFixed(2)}%`.padStart(7));
console.log(`T-0280 / T-1106 — the far band's grass-or-flower split, in each of the`
  + ` three units it has been dealt on`
  + ` · ${SOURCE ? 'SOURCE tree' : 'published mirror'} · ${VIEWPORT.width}x${VIEWPORT.height}\n`);
console.log(`  the forb ring's ceiling: ${report.lattice.ceilingPerM2.toFixed(3)} plants/m²`
  + ` (one per ${report.lattice.slotArea.toFixed(2)} m² slot)`);
console.log(`  the far band's annulus:  ${report.inner} – ${report.outer} m\n`);

console.log('§1 PER COMMUNITY — the forb\'s share of the cards the far band occupies\n');
console.log('  community               T-0209   T-0280   T-1106   move    aspect gram/forb  w-less');
console.log('                          lattice    cover   silhou.  0280→1106');
for (const r of report.rows) {
  const move = (r.now !== null && r.after !== null && r.after > 0)
    ? `${(r.now / r.after).toFixed(3)}x` : '—';
  const asp = r.matrixSilAspect === null || r.forbSilAspect === null ? '     —      —'
    : `${r.matrixSilAspect.toFixed(2).padStart(6)} ${r.forbSilAspect.toFixed(2).padStart(6)}`;
  console.log(`  ${r.id.padEnd(22)}`
    + `${pct(r.before)}${r.clamped ? '*' : ' '}`
    + `${pct(r.after)} ${pct(r.now)}  ${move.padStart(7)}`
    + `   ${asp}${String(r.fallbacks).padStart(8)}`);
}
console.log('\n  * on the forb ring\'s 1.000 lattice ceiling — the split was reading a constant.');
console.log('  T-0280\'s two sides are the same quantity: a fraction of GROUND covered.');
console.log('  T-1106\'s two sides are the same quantity one step further: m² of upright');
console.log('  SILHOUETTE per m² of ground, which is what fills a pixel of a wall seen');
console.log('  edge-on at 34–95 m. `aspect` is each stratum\'s own `sil / cover` — the wall');
console.log('  one m² of its floor stands up — and the move is the ratio of the two.');
console.log('  `w-less` is how many of that community\'s forbs state no `width_m` and are');
console.log('  therefore measured at the footprint the placer already gives them — a fifth of');
console.log('  the sward records, and the whole forb list of three communities.');
const unknown = report.rows.reduce((a, r) => a + r.coverUnknown, 0);
const silUnknown = report.rows.reduce((a, r) => a + r.silUnknown, 0);
console.log(`  records whose abundance converts to no count at all: ${unknown}.`);
console.log(`  records that convert to no SILHOUETTE — no \`height_m\` — at all: ${silUnknown}.`);

console.log('\n  the WET side of the waterline, where a community plants a different list\n');
console.log('  community                forbCoverWet   forbSilWet   T-0209   T-0280   T-1106  w-less');
for (const r of report.rows) {
  if (!(r.forbCoverWet > 0) && !(r.forbShareWet > 0)) continue;
  console.log(`  ${r.id.padEnd(22)}${r.forbCoverWet.toFixed(4).padStart(12)}`
    + `${r.forbSilWet.toFixed(4).padStart(13)} ${pct(r.beforeWet)} ${pct(r.afterWet)}`
    + ` ${pct(r.nowWet)}${String(r.fallbacksWet).padStart(8)}`);
}

console.log('\n§2 AT THE STANDS — the annulus weighted by the ground it lands on\n');
console.log('  stand            stands in            T-0209   T-0280   T-1106    move   far cards   heads>ring');
for (const s of report.stood) {
  const move = s.after > 0 ? `${(s.now / s.after).toFixed(3)}x` : '—';
  console.log(`  ${s.id.padEnd(15)}  ${String(s.zone).padEnd(20)}`
    + ` ${pct(s.before)} ${pct(s.after)} ${pct(s.now)}  ${move.padStart(6)}`
    + `${String(s.farCards).padStart(12)}${String(s.headsPastRing).padStart(13)}`);
}
for (const s of report.stood) {
  console.log(`\n  ${s.id} — the communities its far band lands on`
    + ` (${(s.unzoned * 100).toFixed(1)} % of the annulus is in no community)`);
  for (const p of s.parts) {
    console.log(`    ${`${p.id} (${p.side})`.padEnd(30)}${(p.share * 100).toFixed(1).padStart(6)} %`
      + ` of the band   ${pct(p.b)} → ${pct(p.a)} → ${pct(p.s)}`);
  }
}

if (errors.length) {
  console.error(`\nPAGEERRORS (${errors.length}):`);
  for (const e of errors) console.error(`  ${e}`);
}
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
