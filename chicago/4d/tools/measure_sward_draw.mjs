/**
 * ROADMAP K49(a) — THE SWARD'S DRAWN CENSUS, ACROSS EVERY COMMUNITY.
 *
 *   node tools/measure_sward_draw.mjs [--source] [--gate] [--declare]
 *
 * `flora.js` keeps the census (`stats.draws`); the release smoke reads it at
 * whatever station the gate happens to be standing in, and that is one
 * community out of ten. This stands the placer in EVERY community in turn and
 * asks the same question of each: which species does a list owe a whole plant
 * to, and draw nowhere?
 *
 * Why a separate tool rather than another smoke assertion. The smoke is a gate
 * and costs ~13 minutes a viewport; this is a measurement and costs about one,
 * because it never renders a frame it does not need. It re-deals the sward by
 * handing `flora.update` a synthetic camera at a plantable point inside each
 * community — the same entry point the render loop uses, so it measures the
 * placer rather than a re-implementation of it.
 *
 * The single-station figure the smoke prints is not wrong, it is SMALL: 68
 * slots in the settled town, where this reports 6,780 across sixteen populated
 * lists. Quote this one for a claim about the dataset, and the smoke's for a
 * claim about the frame the gate stood in.
 *
 * Defaults to the PUBLISHED mirror, for the reason the smoke does: the source
 * tree and the site do not load the same geometry, and the ground a plant is
 * stationed on comes off it. `--source` measures the working tree instead.
 *
 * ROADMAP K54 — it also prints, per (community, list), the ground the drawn
 * plants cover against the ground their own records claim, and the deviation per
 * hundred slots so two draws of different sizes can be compared. The shrub
 * stratum is its own list here because it is its own lattice pass in the
 * renderer; before K54 its rows were inside `forb`.
 *
 * `SWARD_VIEWPORT=mobile` stands the run at a PHONE and not merely at a phone's
 * window (T-0162). The ring sizes a station deals over are cut from the sward
 * tune, and the tune is reached by the DEVICE guess — a coarse pointer, or a
 * touch point under a 900 px window — so a bare 390 px viewport resolved the
 * desktop tune and the two runs came back identical, row for row. The run now
 * prints the stand it reached (window, touch points, pointer, detail level, tune
 * and every layer's ring reach) before its first figure, and REFUSES to print a
 * census at all if the stand it reached is not the one that was asked for.
 *
 * T-0019 / ROADMAP K58 — it also prints what the FORB LATTICE'S CEILING costs each
 * community: the plants per m² its own records ask for, the 0.346 the lattice can
 * carry, and the share of its record the layer is therefore able to draw. Nine of
 * the ten populated forb layers sit on that ceiling. `--gate` asserts the set
 * against `tools/forb_clamp_baseline.json`, which is the declaration itself, and
 * `--declare` rewrites that file from the measurement.
 *
 * ROADMAP K49(f) — `--gate` exits non-zero when any list owes a species a WHOLE
 * slot and deals it none. The same assertion now runs inside
 * `tools/smoke_renderer.mjs`, which is where it belongs; this flag is here so
 * the question can be asked in a minute rather than in a smoke, because that is
 * the difference between a check an agent runs while iterating and one it runs
 * at the end. `tools/check.sh` cannot run either — the dev gate's runner has no
 * Playwright, by design (it is the fast half of the two-speed build).
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
/** T-0019. Rewrite `tools/forb_clamp_baseline.json` from this run's measurement.
 *  The declaration has to be re-made by hand whenever a flora record moves, and a
 *  figure re-typed off a console is a figure that can be re-typed wrongly — so the
 *  tool that measures it is the tool that writes it, and the diff is the review. */
const wantDeclare = process.argv.includes('--declare');
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.SWARD_PORT || 4191);
const YEAR = process.env.SWARD_YEAR || '1835';

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
// The viewport decides the ring sizes and therefore how many slots a station
// deals, so the census has to be answerable at both. `SWARD_VIEWPORT=mobile`
// stands it at the smoke's phone size (ROADMAP K49(f)).
//
// AND UNTIL T-0162 IT DID NOT STAND THERE, which is why this block is now six
// lines instead of one and why the stand is printed and asserted below. The
// page's ring sizes come from `flora.js` `mergeTune(lowSpec && detail === 'full'
// ? 'light' : detail)`, and `lowSpec` is `controls/touch.js` `prefersTouch()` —
// `(pointer: coarse)`, or a touch point with a window under 900 px. A bare
// `browser.newPage({ viewport })` sets the WINDOW and nothing else: Chromium
// reports `navigator.maxTouchPoints === 0` and a fine pointer, so a 390-px page
// resolved `full` exactly as the 1280-px one did and the two runs came back with
// identical censuses, row for row, 7,844 slots either way (T-0018 measured it;
// T-0162 found the cause). A measurement that names a viewport it did not reach
// is worse than no measurement, so the flag now drives the guess itself.
//
// The context options are the smoke's, copied from `tools/smoke_renderer.mjs`
// (`['mobile 390x780', { width: 390, height: 780 }, true]` and the context it
// builds from it) rather than invented here, INCLUDING `isMobile: false` and the
// comment that goes with it — the two tools have to stand in the same place or
// the census cannot be read against the gate's own figures. Copied and not
// imported for the reason `measure_detail_ceilings.mjs` copies the stand list:
// the smoke is a script and not a module, so a drift makes this tool less
// complete, never wrong.
const MOBILE = process.env.SWARD_VIEWPORT === 'mobile';
const VIEWPORT = MOBILE ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const context = await browser.newContext({
  viewport: VIEWPORT,
  hasTouch: MOBILE,
  isMobile: false,          // isMobile forces mobile emulation Chromium-side
  deviceScaleFactor: MOBILE ? 2 : 1,
});
const page = await context.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

// WHERE THIS RUN ACTUALLY STOOD, printed before any figure it produces and
// asserted before any figure is believed (T-0162). The ring sizes are the whole
// reason the viewport is a flag, so the run states the level they were cut at
// and the radii themselves rather than leaving a reader to assume the window
// size reached them.
const stand = await page.evaluate(() => {
  const a = window.__chicago4d;
  // `controls/touch.js` `prefersTouch()`, asked of the page rather than
  // re-implemented against the launch options: the device guess this reports is
  // the one `main.js` actually passed to `flora.build`.
  const coarse = !!(window.matchMedia?.('(pointer: coarse)').matches
    || (navigator.maxTouchPoints > 0 && window.innerWidth < 900));
  const detail = a.detail;
  return {
    width: window.innerWidth,
    height: window.innerHeight,
    touchPoints: navigator.maxTouchPoints,
    coarse,
    detail,
    // `flora.js` line for line: the tune a phone reaches is `light` even when
    // nobody has chosen a level, because the device guess outranks the default.
    tune: coarse && detail === 'full' ? 'light' : detail,
    ringR: Object.fromEntries(Object.entries(a.flora.rings.layers)
      .map(([layer, r]) => [layer, r.fade[0]])),
  };
});
// Two decimals: `ringsFor` multiplies its way to the fade radius, so `near`
// prints as 3.9999999999999996 raw and a reader would be right to distrust a
// measurement tool that cannot say four.
const ringLine = Object.entries(stand.ringR)
  .map(([layer, r]) => `${layer} ${Number(r.toFixed(2))} m`).join(', ');
console.log(`stand: ${MOBILE ? 'MOBILE' : 'desktop'} ${stand.width}x${stand.height}, `
  + `${stand.touchPoints} touch point(s), pointer ${stand.coarse ? 'COARSE' : 'fine'} — `
  + `detail ${stand.detail}, sward tune ${stand.tune}`);
console.log(`       ring reach: ${ringLine}\n`);

// THE ASSERTION THE FLAG WAS MISSING. `SWARD_VIEWPORT=mobile` exists to move the
// ring sizes, so a run that asked for the phone and got the desktop's tune is a
// measurement claiming a viewport it did not stand at — it fails here rather
// than printing a desktop census under a mobile heading, which is exactly what
// it did from T-0018 until T-0162. The desktop stand is asserted the same way
// and for the same reason: a runner that reported a coarse pointer would deal
// this tool a phone's census while the header said 1280x800.
const wantTune = MOBILE ? 'light' : 'full';
if (stand.tune !== wantTune) {
  console.error(`REFUSING TO REPORT: asked for the ${MOBILE ? 'mobile' : 'desktop'} `
    + `stand and reached the '${stand.tune}' tune, not '${wantTune}'. The ring sizes `
    + `are what the viewport is a flag for, so this census would carry a heading it `
    + `did not earn (T-0162).`);
  await browser.close();
  server.close();
  process.exit(2);
}

const measured = await page.evaluate(() => {
  const a = window.__chicago4d;
  const wanted = a.flora.substrates().map((z) => z.id);
  // One plantable point per community, found through the placer's OWN zone
  // finder and its own plantability rule rather than off the extents: a point
  // this project would refuse to plant answers for nothing.
  const spots = {};
  for (let e = -900; e <= 1200 && Object.keys(spots).length < wanted.length; e += 6) {
    for (let n = -700; n <= 700; n += 6) {
      const z = a.flora.zoneAt(e, n);
      if (z && !spots[z] && a.flora.plantableAt(e, n)) spots[z] = [e, n];
    }
  }
  const rows = [];
  const sets = {};
  // ROADMAP K54. The forb and the shrub layers are dealt over the SAME ring, so
  // one radius answers for both and a cover figure is comparable between them.
  // The matrix layer is drawn on two rings (near tufts and mid cards) and its
  // cover column would be a figure over an ambiguous area, so it is not printed.
  const ringR = a.flora.rings.layers.forb.fade[0];
  for (const [zone, [e, n]] of Object.entries(spots)) {
    // The rig re-deals when the camera has moved, so hand it a camera. It reads
    // exactly two things off one, and a duck answers both.
    const camera = {
      getWorldPosition: (v) => { v.set(e, 1.7, -n); return v; },
      getWorldDirection: (v) => { v.set(0, 0, -1); return v; },
    };
    a.flora.update(0.016, camera);
    a.flora.update(0.016, camera);
    sets[zone] = { ...a.flora.stats.sets };
    // ROADMAP K54, and R-M1c's lesson about denominators: a ring standing at the
    // edge of one community reaches over four of them, so the ground a community
    // holds inside this ring has to be MEASURED and not assumed to be the disc.
    // Dividing a community's drawn plants by the whole ring reported 17.9 % where
    // the community holds a fifth of the ring — which is a statement about the
    // mosaic, not about the draw. Plantable ground only, because a plant may not
    // stand on the water, the road or a building footprint and the drawn cover
    // is measured against ground it was actually offered.
    const ringArea = {};
    for (let se = e - ringR; se <= e + ringR; se += 1) {
      for (let sn = n - ringR; sn <= n + ringR; sn += 1) {
        if ((se - e) ** 2 + (sn - n) ** 2 > ringR * ringR) continue;
        const z = a.flora.zoneAt(se, sn);
        if (!z || !a.flora.plantableAt(se, sn)) continue;
        ringArea[z] = (ringArea[z] ?? 0) + 1;                 // 1 m² per sample
      }
    }
    for (const d of a.flora.stats.draws) {
      if (d.drawn <= 0) continue;
      const area = ringArea[d.community] ?? 0;
      rows.push({
        at: zone,
        community: d.community,
        list: d.list,
        drawn: d.drawn,
        species: d.species.length,
        // ROADMAP K54 — WHICH QUANTITY THE SAMPLE REPRODUCES. `recordedCover` is
        // the ground this list's records say it holds; `drawnCover` is the
        // ground the plants actually placed on this ring hold. A layer faithful
        // in head count can be an order of magnitude short in cover, and that
        // difference is the whole of K53's finding 2.
        recordedCover: d.species.reduce((t, s) => t + (s.cover ?? 0), 0),
        drawnCover: d.list === 'matrix' || !area ? null
          : d.species.reduce((t, s) => t + (s.width
            ? s.drawn * Math.PI * (s.width * 0.5) ** 2 : 0), 0) / area,
        /** The community's own plantable ground inside this ring, in m². */
        area,
        worstShortfall: Math.max(0, ...d.species.map((s) => s.expected - s.drawn)),
        // ROADMAP K49(d). The worst shortfall is a max of a max, so it moves on
        // one species in one list and is the noisiest thing this tool prints —
        // it named the fault, but it cannot rank two candidate repairs. This is
        // the whole list's disagreement with its own record, summed over every
        // species and both signs, and it is the figure to compare draws on.
        deviation: d.species.reduce((t, s) => t + Math.abs(s.expected - s.drawn), 0),
        absent: d.species.filter((s) => s.drawn === 0 && s.expected >= 1)
          .map((s) => ({ id: s.id, owed: s.expected, unit: s.unit })),
        // ROADMAP K49(f). The per-station `absent` above is the diagnostic; the
        // GATE is on the scene, so it needs each species' draw summed over every
        // station that reads the list.
        each: d.species.map((s) => ({ id: s.id, drawn: s.drawn, expected: s.expected })),
        // ROADMAP K49(e) / T-0018 — THE SAME ROW ONE STEP EARLIER IN THE DEAL.
        // `drawn` is what survived `station()` and `crowdsTheWalker()`; `dealt`
        // is what the deal handed a species to before either was asked. The
        // question this parcel exists to settle is whether the difference
        // between the two is a biased set of ranks or merely a smaller one, and
        // it cannot be asked of the drawn population alone.
        dealt: d.dealt,
        rejStation: d.rejStation,
        rejWalker: d.rejWalker,
        deal: d.species.map((s) => ({
          id: s.id, dealt: s.dealt, expectedDealt: s.expectedDealt,
          drawn: s.drawn, expected: s.expected, width: s.width,
        })),
      });
    }
  }
  return { spots: Object.keys(spots), rows, sets, abundance: a.flora.stats.abundance };
});

/* -------------------------------------------------------------------------- */
/* T-0019 / ROADMAP K58 — WHAT THE FORB LATTICE'S CEILING COSTS, PER COMMUNITY */
/* -------------------------------------------------------------------------- */
/**
 * `forbShareOf` is `min(1, density x cell^2 / perCell)`, and that `min` is a
 * lattice ceiling of one plant per slot. Where a community's own records ask for
 * more plants per square metre than the lattice can carry, the clamp bites and
 * **the layer is drawn at a density `TUNE.forb` chose and not at one any record
 * states** — `z06_dense_forest` draws a fraction of its recorded cover for that
 * reason and not for want of research.
 *
 * The clamp was invisible from outside `flora.js`: a share reading 1.000 is one
 * plant per slot whatever the slot is, so a layer sitting ON the ceiling and one
 * tuned to it printed the same number. K55 took the count of clamped layers from
 * four to six and nothing said so; T-0034 raised the two prairies onto it and
 * nothing said that either.
 *
 * So this is the declaration T-0019's acceptance asks for. It states, per
 * community and per SIDE of the waterline, the plants per square metre the
 * records ask for, the ceiling, and the share of its own record the layer can
 * actually draw. It is not a fix: the ceiling stands, because raising it is
 * geometry in exactly the communities that already carry the most and the
 * project's triangle ceilings are the binding constraint (T-0223, T-0229).
 * What changes is that the debt is now a number this project prints rather than
 * one a reader has to derive from a saturated share.
 */
const clamp = await page.evaluate(() => {
  const a = window.__chicago4d;
  const lat = a.flora.forbLattice;
  const rows = [];
  for (const z of a.flora.communities()) {
    // T-0282 — BOTH STRATA, because both are dealt through the same `shareOf`
    // against the same ceiling. T-0019 declared the forb layers only, and the
    // gate it built was therefore blind to half of what it was gating:
    // `z06_dense_forest`'s SHRUB layer sits on this ceiling too and has since
    // K54 named it, drawing 85.8 % of its own recorded clump density. A
    // declaration whose whole purpose is that no layer joins the clamp in
    // silence cannot be silent about a stratum.
    for (const [stratum, side, asked, share] of [
      ['forb', 'dry', z.forbDensity, z.forbShare],
      ['forb', 'wet', z.forbDensityWet, z.forbShareWet],
      ['shrub', 'dry', z.shrubDensity, z.shrubShare],
      ['shrub', 'wet', z.shrubDensityWet, z.shrubShareWet],
    ]) {
      if (!(asked > 0)) continue;
      rows.push({
        community: z.id,
        stratum,
        side,
        asked,
        share,
        // The plants per m2 the lattice actually offers this layer: the share
        // it resolved to, back over the ground one slot stands for. Below the
        // ceiling this IS `asked`, to floating point.
        offered: share / lat.slotArea,
        clamped: share >= 1,
      });
    }
  }
  return { lattice: lat, rows };
});

const slots = measured.rows.reduce((t, r) => t + r.drawn, 0);
const lists = new Set(measured.rows.map((r) => `${r.community}.${r.list}`));
const absent = measured.rows.flatMap((r) => r.absent.map(
  (s) => `${r.community}.${r.list}.${s.id} owed ${s.owed.toFixed(2)} (${s.unit}), standing at `
    + `${r.at}`));
// ROADMAP K49(f) — the scene-wide reading of the same question, and the one
// `--gate` asserts. A station missing a plant its ring owes 1.2 of is a sample;
// a plant no station drew while some station owed it a whole one is ABSENT.
const tally = new Map();
for (const r of measured.rows) {
  for (const s of r.each) {
    const key = `${r.community}.${r.list}.${s.id}`;
    const t = tally.get(key) ?? { drawn: 0, owed: 0, at: [] };
    t.drawn += s.drawn;
    t.owed = Math.max(t.owed, s.expected);
    if (s.expected >= 1) t.at.push(r.at);
    tally.set(key, t);
  }
}
const nowhere = [...tally.entries()]
  .filter(([, t]) => t.drawn === 0 && t.owed >= 1)
  .map(([k, t]) => `${k} owed ${t.owed.toFixed(2)} at ${t.at.join('/')}`);
const worst = Math.max(0, ...measured.rows.map((r) => r.worstShortfall));
const devOf = (list) => measured.rows.filter((r) => r.list === list)
  .reduce((t, r) => t + r.deviation, 0);
/** ROADMAP K54. The deviation is an absolute sum over slots, so a list dealt
 *  more slots scores worse at identical fidelity — and K54 SPLIT one list into
 *  two, which no comparison of the raw sums can survive. Per hundred slots is
 *  the figure that compares two draws of different sizes. */
const slotsOf = (list) => measured.rows.filter((r) => r.list === list)
  .reduce((t, r) => t + r.drawn, 0);
const devPer100 = (list) => (slotsOf(list) ? devOf(list) / slotsOf(list) * 100 : 0);

for (const r of measured.rows) {
  console.log(`  at ${r.at.padEnd(22)} ${r.community.padEnd(22)} ${r.list.padEnd(6)} `
    + `drawn ${String(r.drawn).padStart(5)}  of ${String(r.species).padStart(2)} species  `
    + `worst shortfall ${r.worstShortfall.toFixed(2)}  dev ${r.deviation.toFixed(2)}  `
    // ROADMAP K54's own question, one column: the ground the drawn plants hold
    // against the ground their records claim.
    + `cover ${r.drawnCover === null ? '   —  ' : `${(r.drawnCover * 100).toFixed(1)}%`.padStart(6)}`
    + ` of ${`${(r.recordedCover * 100).toFixed(1)}%`.padStart(6)}`
    + `${r.absent.length ? `  ABSENT ${r.absent.map((s) => s.id).join(', ')}` : ''}`);
}
const ab = measured.abundance ?? { lists: 0, mixed: [], unconvertible: [] };
console.log(`\n${measured.spots.length} communities stood in · ${lists.size} populated list(s) · `
  + `${slots} slots dealt · worst shortfall ${worst.toFixed(2)} slot(s)`);
// ROADMAP K54 — THIS FIGURE IS NOT "DEVIATION FROM THE RECORDED COVER" AND HAS
// NOT BEEN SINCE K49(c2), which is what its label said until today. `expected`
// is `share × slots` and `share` is the species' share of the LOTTERY, so this
// measures the lattice's disagreement with its own target distribution — a
// sampling-discrepancy figure, and the right one for comparing two draws. The
// question of whether that target reproduces the recorded ground is the `cover`
// column above, and K54's box quoted this line for it.
console.log(`deviation from each list's own dealt share, summed over every species and both `
  + `signs: matrix ${devOf('matrix').toFixed(2)} · forb ${devOf('forb').toFixed(2)}`
  + ` · shrub ${devOf('shrub').toFixed(2)} slot(s)`);
console.log(`  the same, per 100 slots dealt: matrix ${devPer100('matrix').toFixed(2)} over `
  + `${slotsOf('matrix')} · forb ${devPer100('forb').toFixed(2)} over ${slotsOf('forb')} · `
  + `shrub ${devPer100('shrub').toFixed(2)} over ${slotsOf('shrub')}`);
const shrubInstances = Object.entries(measured.sets)
  .map(([at, s]) => `${at} ${s['flora-shrub'] ?? 0}`).join(' · ');
console.log(`shrub instances standing, per station: ${shrubInstances}`);
console.log(`${absent.length} station-row(s) owe a species a whole slot and deal it none:`);
for (const s of absent) console.log(`  - ${s}`);
console.log(`${nowhere.length} of ${tally.size} (list, species) pair(s) drawn NOWHERE in the `
  + `whole scene:`);
for (const s of nowhere) console.log(`  - ${s}`);
console.log(`\nabundance units: ${ab.mixed.length} of ${ab.lists} lists mix an area with a count; `
  + `${ab.unconvertible.length} record(s) give cover with no width_m`);
for (const m of ab.mixed) {
  console.log(`  - ${m.zone}.${m.list}: ${(m.countedShare * 100).toFixed(1)}% of slots dealt off `
    + `counts, against ${m.area} species recorded as an area`
    // ROADMAP K54 opened this column and K55 closed the question it asked. A
    // mixed list whose SLOT COUNT is dealt off the recorded sum is still adding
    // cover fractions to plants per m²; one dealt off `stems` is not; and a
    // MATRIX list is dealt off neither, because `cover.matrix_fraction` answers
    // that question directly. `basis` is `flora.js`'s own `SLOT_BASIS` now, so
    // a row can no longer report a rule the renderer does not run.
    + (m.basis === null
      ? " — slot count off cover.matrix_fraction, not this sum (lottery only)"
      : ` — slot count off '${m.basis}'`));
}

/* -------------------------------------------------------------------------- */
/* T-0019 / K58 — THE DECLARATION, AND THE GATE THAT HOLDS IT                  */
/* -------------------------------------------------------------------------- */
/**
 * `tools/forb_clamp_baseline.json` is the declaration itself: every (community,
 * stratum, side) the ceiling binds, with the density its records ask for and the
 * share of that density the lattice can draw. `--gate` fails when the measured
 * set stops matching it — a layer joining the clamp, one leaving it, the ceiling
 * moving, or a record's asked density moving past the tolerance.
 *
 * T-0282 added the STRATUM to that identity. As T-0019 wrote it the declaration
 * covered the forb layers alone, so the one thing it existed to prevent — a
 * layer joining the clamp with nobody saying so — could still happen in the
 * shrub stratum, which is dealt through the same `shareOf` against the same
 * ceiling and which had `z06_dense_forest` sitting on it the whole time.
 *
 * A gate on the SET and not on a total, because the fault this closes is silence
 * rather than size: the four-to-six drift of K55 and T-0034's two prairies both
 * happened under a green tree, and both would fail here.
 */
const CLAMP_BASELINE = path.join(HERE, 'forb_clamp_baseline.json');
const REL_TOL = 0.005;         // half a per cent, on the asked density
const base = JSON.parse(fs.readFileSync(CLAMP_BASELINE, 'utf8'));
const near = (a, b) => Math.abs(a - b) <= REL_TOL * Math.max(Math.abs(b), 1e-9);
/** T-0282 — the identity of a declared layer is (community, stratum, side).
 *  A declaration written before the shrub stratum joined carries no `stratum`,
 *  and it meant `forb`: reading it that way migrates the file on the next
 *  `--declare` instead of failing every line of it at once. */
const key = (r) => `${r.community}.${r.stratum ?? 'forb'}.${r.side}`;
const clampProblems = [];
if (!near(clamp.lattice.ceilingPerM2, base.ceilingPerM2)) {
  clampProblems.push(`the forb lattice's ceiling is ${clamp.lattice.ceilingPerM2.toFixed(4)} `
    + `plants/m2, declared ${base.ceilingPerM2.toFixed(4)} — every shortfall below is `
    + `measured against it, so re-declare them together`);
}
const declared = new Map(base.clamped.map((d) => [key(d), d]));
const measuredClamped = clamp.rows.filter((r) => r.clamped);
for (const r of measuredClamped) {
  const d = declared.get(key(r));
  if (!d) {
    clampProblems.push(`${key(r)} is on the lattice ceiling and is NOT declared: its records `
      + `ask ${r.asked.toFixed(3)} plants/m2 and the lattice draws `
      + `${clamp.lattice.ceilingPerM2.toFixed(3)}`);
  } else if (!near(r.asked, d.askedPerM2)) {
    clampProblems.push(`${key(r)} asks ${r.asked.toFixed(3)} plants/m2, declared `
      + `${d.askedPerM2.toFixed(3)} — the records moved, so the declared shortfall is stale`);
  }
}
for (const d of base.clamped) {
  if (!measuredClamped.some((r) => key(r) === key(d))) {
    clampProblems.push(`${key(d)} is declared clamped and no longer is — `
      + `withdraw its line rather than leaving a debt on record that is paid`);
  }
}

console.log(`\nT-0019/K58 — THE FORB LATTICE'S CEILING. One plant per slot, a slot is `
  + `${clamp.lattice.slotArea.toFixed(2)} m2\n  (${clamp.lattice.cell} m cell, `
  + `${clamp.lattice.perCell} per cell), so the most any community may draw is `
  + `${clamp.lattice.ceilingPerM2.toFixed(3)} plants/m2.\n  `
  + `'draws' is the share of its OWN recorded density a layer can put on the ground.`);
for (const r of clamp.rows.slice().sort((x, y) => y.asked - x.asked)) {
  const frac = r.offered / r.asked;
  console.log(`  ${r.community.padEnd(22)} ${r.stratum.padEnd(5)} ${r.side.padEnd(3)} `
    + `asks ${r.asked.toFixed(3).padStart(8)} /m2  offered `
    + `${r.offered.toFixed(3).padStart(6)}  share ${r.share.toFixed(3)}  `
    + `draws ${`${(frac * 100).toFixed(1)}%`.padStart(6)}`
    + `${r.clamped ? `  CLAMPED — short ${(r.asked - r.offered).toFixed(3)} /m2` : ''}`);
}
console.log(`  ${measuredClamped.length} of ${clamp.rows.length} populated (community, stratum, `
  + `side) layer(s) sit on the ceiling; ${base.clamped.length} declared in `
  + `tools/forb_clamp_baseline.json`);
for (const m of clampProblems) console.log(`  - ${m}`);
if (wantDeclare) {
  const doc = {
    _: base._ ?? '',
    measured: new Date().toISOString().slice(0, 10),
    stand: MOBILE ? 'mobile' : 'desktop',
    cell: clamp.lattice.cell,
    perCell: clamp.lattice.perCell,
    slotAreaM2: clamp.lattice.slotArea,
    ceilingPerM2: clamp.lattice.ceilingPerM2,
    clamped: measuredClamped
      .slice().sort((x, y) => y.asked - x.asked)
      .map((r) => ({
        community: r.community,
        stratum: r.stratum,
        side: r.side,
        askedPerM2: r.asked,
        offeredPerM2: r.offered,
        drawsFraction: r.offered / r.asked,
      })),
    fits: clamp.rows.filter((r) => !r.clamped)
      .slice().sort((x, y) => y.asked - x.asked)
      .map((r) => ({
        community: r.community, stratum: r.stratum, side: r.side, askedPerM2: r.asked,
      })),
  };
  fs.writeFileSync(CLAMP_BASELINE, `${JSON.stringify(doc, null, 2)}\n`);
  console.log(`  wrote ${path.relative(process.cwd(), CLAMP_BASELINE)} — `
    + `${doc.clamped.length} clamped, ${doc.fits.length} fitting`);
}

/* -------------------------------------------------------------------------- */
/* ROADMAP K49(e) / T-0018 — DOES A SPATIAL FILTER EAT THE STRATIFICATION?     */
/* -------------------------------------------------------------------------- */
/**
 * K49(d) finding 3 claimed that because the block permutation makes rank a
 * deterministic function of position, any filter applied AFTER the deal that is
 * itself a spatial rule selects a BIASED SET of ranks — so the surviving slots
 * no longer carry the stratification the deal built, and `deviation` reads
 * worse. K49(f) refuted it for the row it was mostly measured on (the fixed
 * grid's own bias explained 23.66 of `z10_settled_town`'s 24.87). What was left
 * for this parcel is the riverbank's residual and the general question.
 *
 * THE INSTRUMENT, and why it is this one. `deviation` is a functional of the
 * SURVIVORS' ranks alone, so the claim can be put exactly rather than
 * correlated: count each species' slots at the moment of the deal (`dealt`) as
 * well as after the filters (`drawn`), and split the survivors' disagreement
 * with the deal into two terms.
 *
 *   dealtDev  Σ|dealt_i − share_i·N|   the discrepancy the DEAL itself has,
 *                                      before any filter — the stratification
 *                                      the parcel is asking about
 *   B         Σ|drawn_i − q·dealt_i|   how far the survivors are from the filter
 *                                      having taken the SAME fraction q = m/N of
 *                                      every species. This is the selection term
 *                                      and it is zero for a perfectly even filter
 *
 * A filter that is blind to rank still moves B, because it is a subsample: it
 * moves it by sampling noise and no more. Under rank-neutral survivorship
 * drawn_i is hypergeometric, so
 *
 *   Bnull = Σ √(2/π) · √( m·p_i(1−p_i)·(N−m)/(N−1) ),   p_i = dealt_i/N
 *
 * is what B reads when the mechanism is ABSENT. **B/Bnull ≈ 1 refutes the
 * mechanism for that row; B/Bnull ≫ 1 proves it, and by how much.**
 *
 * Both controls are run below on the real dealt vectors, because an instrument
 * that has not been shown reading red is not evidence: the GREEN control draws
 * a genuinely uniform subsample of the same size, the RED control draws one of
 * the same size that rejects wide clumps preferentially — which is the rule
 * `crowdsTheWalker()` actually applies.
 */
const TRIALS = 200;
const mad = (v) => Math.sqrt(2 / Math.PI) * Math.sqrt(Math.max(0, v));
function mulberry32(a) {
  return function rnd() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
/** B for a vector of survivor counts against the proportional-filter baseline. */
const selection = (counts, deal, q) => deal
  .reduce((t, s, i) => t + Math.abs(counts[i] - q * s.dealt), 0);
/** The analytic B of a filter that is blind to rank. */
function nullSelection(deal, N, m) {
  if (N < 2 || m <= 0) return 0;
  const fpc = (N - m) / (N - 1);
  return deal.reduce((t, s) => {
    const p = s.dealt / N;
    return t + mad(m * p * (1 - p) * fpc);
  }, 0);
}
/** One subsample of size m. `bias` 0 = uniform; >0 favours narrow clumps, the
 *  way the walker clearance does — key = −ln(U)/w, smallest m kept. */
function subsample(deal, N, m, rnd, bias) {
  const keys = [];
  for (let i = 0; i < deal.length; i++) {
    // The clump radius the walker rule reads. A record with no `width_m` gets
    // the 0.10 m stand-in stated in the PR rather than a silent zero.
    const w = deal[i].width ?? 0.10;
    const weight = bias ? 1 / (0.05 + w * bias) : 1;
    for (let k = 0; k < deal[i].dealt; k++) keys.push([-Math.log(rnd() || 1e-12) / weight, i]);
  }
  keys.sort((a, b) => a[0] - b[0]);
  const counts = new Array(deal.length).fill(0);
  for (let k = 0; k < m && k < keys.length; k++) counts[keys[k][1]]++;
  return counts;
}
function controlRatio(deal, N, m, bias, seed) {
  const bnull = nullSelection(deal, N, m);
  if (!(bnull > 0)) return null;
  const rnd = mulberry32(seed);
  let t = 0;
  for (let i = 0; i < TRIALS; i++) {
    t += selection(subsample(deal, N, m, rnd, bias), deal, m / N);
  }
  return t / TRIALS / bnull;
}

const filtered = measured.rows.filter((r) => r.dealt > 0 && r.drawn > 0 && r.deal.length > 1);
console.log('\nK49(e)/T-0018 — the filters\' own selection, per row. `rej` is the share of '
  + 'DEALT\nslots refused; `B/Bnull` is how far the survivors depart from the filter having '
  + 'taken\nthe same fraction of every species, in units of what a rank-BLIND filter of the '
  + 'same\nsize departs by. 1.0 means the filter did not touch the stratification.');
const analysed = [];
for (const r of filtered) {
  const N = r.dealt;
  const m = r.drawn;
  const q = m / N;
  const dealtDev = r.deal.reduce((t, s) => t + Math.abs(s.dealt - s.expectedDealt), 0);
  const B = selection(r.deal.map((s) => s.drawn), r.deal, q);
  const bnull = nullSelection(r.deal, N, m);
  const ratio = bnull > 0 ? B / bnull : null;
  analysed.push({ r, N, m, q, dealtDev, B, bnull, ratio });
  console.log(`  ${r.at.padEnd(20)} ${r.community.padEnd(20)} ${r.list.padEnd(6)} `
    + `dealt ${String(N).padStart(5)} → drawn ${String(m).padStart(5)}  `
    + `rej ${(100 * (1 - q)).toFixed(1).padStart(5)}%`
    + ` (station ${(100 * r.rejStation / N).toFixed(1)}%, walker ${(100 * r.rejWalker / N).toFixed(1)}%)  `
    + `dev/100 dealt ${(dealtDev / N * 100).toFixed(2)} → drawn ${(r.deviation / m * 100).toFixed(2)}  `
    + `B ${B.toFixed(2)} / Bnull ${bnull.toFixed(2)} = ${ratio === null ? '  —' : ratio.toFixed(2)}`);
}
const wR = analysed.filter((a) => a.ratio !== null);
const pooled = wR.reduce((t, a) => t + a.B, 0) / (wR.reduce((t, a) => t + a.bnull, 0) || 1);
const dealtSlots = analysed.reduce((t, a) => t + a.N, 0);
const drawnSlots = analysed.reduce((t, a) => t + a.m, 0);
console.log(`\n  ${analysed.length} row(s): ${dealtSlots} slot(s) dealt, ${drawnSlots} drawn `
  + `(${(100 * (1 - drawnSlots / dealtSlots)).toFixed(1)}% refused by the two filters). `
  + `Pooled B/Bnull ${pooled.toFixed(2)}`);
console.log(`  worst row ${Math.max(...wR.map((a) => a.ratio)).toFixed(2)} · median `
  + `${wR.map((a) => a.ratio).sort((a, b) => a - b)[wR.length >> 1].toFixed(2)}`);

// The controls, on the three largest dealt populations in the scene — an
// instrument that has not been shown reading red is not evidence.
const biggest = [...analysed].sort((a, b) => b.N - a.N).slice(0, 3);
console.log('\n  CONTROLS on the real dealt vectors — a rank-BLIND filter of the same size '
  + 'must\n  read about 1.0, and a width-selective one (the walker clearance\'s own rule) '
  + 'must not:');
for (const a of biggest) {
  const green = controlRatio(a.r.deal, a.N, a.m, 0, 0x1835c4 + a.N);
  const red = controlRatio(a.r.deal, a.N, a.m, 8, 0x1835c4 + a.N);
  console.log(`    ${a.r.community.padEnd(20)} ${a.r.list.padEnd(6)} ${String(a.N).padStart(5)} `
    + `dealt → ${String(a.m).padStart(5)} drawn   uniform ${green === null ? '—' : green.toFixed(2)}`
    + `   width-selective ${red === null ? '—' : red.toFixed(2)}`
    + `   MEASURED ${a.ratio.toFixed(2)}`);
}

if (errors.length) console.log(`\npage errors: ${errors.length}\n  ${errors.join('\n  ')}`);

await browser.close();
server.close();
if (wantGate) {
  console.log(`\nGATE: ${nowhere.length ? 'FAIL' : 'PASS'} — ${nowhere.length} (list, species) `
    + `pair(s) owed a whole slot and drawn nowhere in the scene, over ${slots} slots in `
    + `${lists.size} list(s)`);
  // T-0019. The second assertion, and it is on the DECLARATION rather than on
  // the clamp: a layer is allowed to sit on the lattice ceiling, and it is not
  // allowed to do so without its shortfall written down.
  console.log(`GATE: ${clampProblems.length ? 'FAIL' : 'PASS'} — the sward lattice's clamped `
    + `layers match their declaration in tools/forb_clamp_baseline.json `
    + `(${measuredClamped.length} clamped, ${clampProblems.length} problem(s))`);
}
process.exit(errors.length || (wantGate && (nowhere.length || clampProblems.length)) ? 1 : 0);
