/**
 * ROADMAP K45(b3) — WHAT THE TIMBER'S DETAIL CONTROL ACTUALLY DOES.
 *
 *   node tools/measure_timber_detail.mjs [--source] [--gate] [--json <file>]
 *
 * K45(b2) finding 2 measured the control and found it inert: `step` is
 * count-neutral by construction (the acceptance roll is `perHa · step² / 10000`,
 * so a coarser step visits proportionally fewer cells and accepts proportionally
 * more at each), and the `STEMS` caps — the only other thing the levels differ
 * by — had never bound. So `light`, `balanced` and `full` planted the SAME wood
 * in slightly different places. When the sweep widened they did bind, at exactly
 * 300 trees, and a bound cap is not a thinning: the loop runs south to north, so
 * it deletes the north end of the wood and leaves a straight edge across the
 * town, on the level phones start at.
 *
 * This tool asks the two questions that tell those apart, at every level:
 *
 *   1. **How many stems does the level plant?** A control that means something
 *      moves this; the caps did not.
 *   2. **How far north does the wood reach, and how is it distributed north to
 *      south?** This is the question a stem count cannot answer and the one that
 *      caught the defect: a truncated wood and a thinned wood can plant the same
 *      number of trees, and only one of them has a straight edge in it.
 *
 * `--gate` exits non-zero when a level truncates rather than thins, when a stem
 * budget binds, or when the planted counts drift from the keep fractions
 * `trees.js` declares. The baseline it reads is `timber_detail_baseline.json`.
 *
 * Defaults to the PUBLISHED mirror for the reason every renderer measurement
 * here does: the source tree loads uncompressed masters and the site loads
 * compressed derivatives, and bugs have shipped in that gap twice. `--source`
 * measures the working tree instead.
 *
 * This is a measurement, not the release gate: it costs about a minute because
 * it renders no frame it does not need, against the smoke's ~13 a viewport.
 * `tools/check.sh` cannot run it — the dev gate's runner has no Playwright, by
 * design (it is the fast half of the two-speed build).
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
const wantGate = process.argv.includes('--gate');
const jsonAt = process.argv.indexOf('--json');
const jsonOut = jsonAt >= 0 ? process.argv[jsonAt + 1] : null;
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.TIMBER_PORT || 4193);
const YEAR = process.env.TIMBER_YEAR || '1835';
const BASELINE = path.join(HERE, 'timber_detail_baseline.json');

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

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
// The woody layer is planted over the whole field once, not into a ring that
// follows the visitor, so unlike the sward its population does not depend on
// the viewport. Desktop is used because that is where `full` is the default.
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

const measured = await page.evaluate(async () => {
  const a = window.__chicago4d;
  const started = a.detail;
  const rows = [];
  for (const level of a.detailOrder) {
    // `setDetail` is the visitor's own control — the same entry point the
    // Settings panel calls — so this measures the shipped path rather than a
    // re-implementation of it.
    await a.setDetail(level);
    // Two frames, the way the smoke's own detail walk does it: `renderer.info`
    // reports the LAST frame drawn, so reading it straight after a rebuild
    // reports the scene that was replaced.
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    const s = a.trees.stats;
    const stations = a.trees.group.userData.stations ?? [];
    const sweep = s.sweep ?? { n: [0, 0], e: [0, 0], step: 0 };
    const [n0, n1] = sweep.n;
    const span = Math.max(1e-6, n1 - n0);
    // The wood's reach north, and its shape north to south. A bound cap on a
    // south-to-north loop shows up here as a maximum that falls with the level
    // and as an emptied top decile; a uniform thinning leaves both alone.
    let maxN = -Infinity;
    let minN = Infinity;
    const deciles = new Array(10).fill(0);
    for (const st of stations) {
      if (st.n > maxN) maxN = st.n;
      if (st.n < minN) minN = st.n;
      const d = Math.min(9, Math.max(0, Math.floor(((st.n - n0) / span) * 10)));
      deciles[d]++;
    }
    rows.push({
      level,
      trees: s.trees,
      thickets: s.thickets,
      stems: stations.length,
      triangles: a.stats().triangles,
      timberTriangles: s.triangles,
      drawCalls: a.stats().drawCalls,
      ceiling: a.detailLevels[level].triangles,
      species: Object.keys(s.species).length,
      keep: s.keep ?? null,
      step: sweep.step,
      sweepN: [n0, n1],
      maxStationN: stations.length ? maxN : null,
      minStationN: stations.length ? minN : null,
      topDecile: deciles[9],
      deciles,
    });
  }
  await a.setDetail(started);
  return { rows, problems: (a.problems ?? []).filter((p) => p.startsWith('trees:')) };
});

await browser.close();
server.close();

const rows = measured.rows;
const byLevel = Object.fromEntries(rows.map((r) => [r.level, r]));
const full = byLevel.full;

for (const r of rows) {
  const share = full && full.stems ? r.stems / full.stems : NaN;
  console.log(`  ${r.level.padEnd(9)} step ${r.step.toFixed(1)} m  keep `
    + `${r.keep === null ? ' n/a ' : r.keep.toFixed(3)}  `
    + `${String(r.trees).padStart(4)} trees + ${String(r.thickets).padStart(4)} stools = `
    + `${String(r.stems).padStart(4)} stems (${(share * 100).toFixed(1)}% of full)  `
    + `${String(r.timberTriangles).padStart(7)} timber tris  scene ${r.triangles}/${r.ceiling}  `
    + `${r.drawCalls} calls  ${r.species} species`);
}
console.log('\nhow far north the wood reaches, and its shape south -> north '
  + '(10 bands of the swept field):');
for (const r of rows) {
  console.log(`  ${r.level.padEnd(9)} N ${r.minStationN === null ? '   —  ' : r.minStationN.toFixed(1)}`
    + ` .. ${r.maxStationN === null ? '   —  ' : r.maxStationN.toFixed(1)} m   `
    + `[${r.deciles.join(' ')}]  northernmost band ${r.topDecile}`);
}
if (measured.problems.length) {
  console.log('\nthe planter reported:');
  for (const p of measured.problems) console.log(`  - ${p}`);
}
if (errors.length) {
  console.log(`\n${errors.length} page error(s):`);
  for (const e of errors) console.log(`  - ${e}`);
}

const report = { rows, problems: measured.problems, pageErrors: errors };
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(report, null, 2)}\n`);

if (!wantGate) {
  console.log('\n(measurement only — pass --gate to assert against '
    + path.basename(BASELINE) + ')');
  process.exit(errors.length ? 1 : 0);
}

/* ---- the gate ------------------------------------------------------------ */

const base = JSON.parse(fs.readFileSync(BASELINE, 'utf8'));
const failures = [];
const check = (name, cond, detail) => {
  if (cond) console.log(`  ok    ${name}`);
  else { failures.push(name); console.log(`  FAIL  ${name} — ${detail}`); }
};
console.log('');

check('no page error while walking the three levels', errors.length === 0,
  errors.join(' | '));
check('the planter reports no bound stem budget at any level',
  measured.problems.length === 0, measured.problems.join(' | '));

const fullTopShare = full.stems ? full.topDecile / full.stems : 0;
for (const r of rows) {
  const b = base.levels[r.level];
  if (!b) { failures.push(`${r.level}: no baseline row`); continue; }
  // 1. THE CONTROL MEANS SOMETHING, and it means what the file says it means.
  //    The tree count follows the level's own declared keep fraction. The
  //    tolerance is a draw's, not a target's: this is a Bernoulli acceptance
  //    over ~190,000 cells and the count is near-Poisson, so ±0.06 of full's
  //    472 trees is about 1.8 standard deviations. It is what the caps never
  //    did — before this parcel the three levels planted 472/470/437.
  check(`${r.level}: declares the keep fraction the baseline banks`,
    r.keep !== null && Math.abs(r.keep - b.keep) < 1e-9,
    `trees.js says ${r.keep}, baseline ${b.keep}`);
  //    Against FULL'S share, not against the keep fraction itself. Until T-1127
  //    `full`'s keep was 1.00, so "40 % of the roll" and "40 % of full's trees"
  //    were the same number and the check could read either. They are not the
  //    same number any more: T-1127 scaled all three fractions down together so
  //    the enlarged field's wood fits the caps, and what the levels still owe
  //    each other is the RATIO — `keep` over `full`'s keep.
  const nominal = base.levels.full.keep ? b.keep / base.levels.full.keep : 0;
  const treeShare = full.trees ? r.trees / full.trees : 0;
  check(`${r.level}: plants ${(nominal * 100).toFixed(1)} % of full's TREES`,
    Math.abs(treeShare - nominal) <= base.tolerance.tree_share,
    `${(treeShare * 100).toFixed(1)} % against ${(nominal * 100).toFixed(1)} % ± `
    + `${(base.tolerance.tree_share * 100).toFixed(0)}`);
  // 2. IT THINS, IT DOES NOT TRUNCATE — the question a stem count cannot answer.
  //    The wood reaches the same latitude at every level and its northernmost
  //    band keeps its share of the stems. A cap bound on a south-to-north loop
  //    plants a perfectly respectable number of trees and fails both of these.
  check(`${r.level}: the wood still reaches the north end of the field`,
    r.maxStationN !== null && r.maxStationN >= base.reach.min_max_station_n_m,
    `northernmost stem at N ${r.maxStationN} m, floor ${base.reach.min_max_station_n_m} m`);
  const topShare = r.stems ? r.topDecile / r.stems : 0;
  check(`${r.level}: the northernmost band keeps its share of the wood`,
    Math.abs(topShare - fullTopShare) <= base.tolerance.band_share,
    `${(topShare * 100).toFixed(2)} % of stems against full's `
    + `${(fullTopShare * 100).toFixed(2)} %`);
  // 3. THE SCREEN IS NOT THE WOOD. The point-bar willow does not take `keep`,
  //    and it must not thin with the sampling step either — that was the defect
  //    this parcel measured (258/190/133 stools before it). The floor is what a
  //    coarse grid can still resolve on a 6–9 m bar, so it is under 1 and stated.
  const stoolShare = full.thickets ? r.thickets / full.thickets : 0;
  check(`${r.level}: keeps the point-bar screen rather than thinning it`,
    stoolShare >= base.screen.min_share_of_full,
    `${(stoolShare * 100).toFixed(1)} % of full's ${full.thickets} stools, floor `
    + `${(base.screen.min_share_of_full * 100).toFixed(0)} % (was `
    + `${(base.screen.before_share[r.level] * 100).toFixed(0)} % before K45(b3))`);
}

console.log(`\n${failures.length} failure(s)`);
process.exit(failures.length ? 1 : 0);
