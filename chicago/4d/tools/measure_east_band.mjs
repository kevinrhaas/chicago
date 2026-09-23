/**
 * measure_east_band.mjs — does the ground east of where the field used to stop
 * actually carry a visitor?
 *
 *   node tools/measure_east_band.mjs            table + verdict
 *   node tools/measure_east_band.mjs --json     machine-readable
 *
 * T-0010 ("finish the heightfield east") asked for "ground a visitor can walk
 * onto that is not there today", and its acceptance clause is one sentence:
 * **the eastern band walks.** By 2026-08-22 the card read as already delivered
 * — the S2e parcel of 2026-08-11 grew the field from a 257² box to 809×321 —
 * but "reads as delivered" is prose, and this project closes a ticket on a
 * measurement. This is that measurement, and it is deliberately not a
 * screenshot: standing somewhere is a fact about the walker, so it is asked of
 * the walker, in the real page, at every record that stands on the new ground.
 *
 * WHERE THE FIELD USED TO STOP, AND WHY THAT NUMBER IS HERE RATHER THAN DERIVED.
 * The first committed field (2026-08-10, "Terrain and river for the forks,
 * traced from Wright 1834") was 257 × 257 cells of 2.5 m from `origin_e`
 * −320.0, so its east edge was local **E +320.0** — the whole harbour reach,
 * the fort and both piers lay off the east side of the world. The very next
 * day's parcel replaced it with the 809-column field that ships today. The old
 * edge is not recoverable from the committed data (the file that held it was
 * overwritten, which is what a generated artefact does), so it is written down
 * here with its provenance rather than silently recomputed from something that
 * no longer says it.
 *
 * WHAT IS MEASURED, in the order the report prints it:
 *
 *   1. the field's own east reach, against the requirement S2e set itself
 *      ("the box must reach about E +1700") and against the old edge;
 *   2. the band, split at the ticket's own cuts, as DRY FRACTION and RELIEF —
 *      because a box that reaches east and holds a flat fill has not delivered
 *      ground, it has delivered a lid;
 *   3. every 1835 record placed east of the old edge, and whether the field
 *      under it is dry land;
 *   4. **the walk**: each of those records' stands, taken in a real browser —
 *      the point is on the measured grid rather than the out-of-bounds fallback
 *      (`terrain.inBounds`), the walker's floor is the field's own answer to
 *      the micron, and the eye stands exactly one eye-height over it; then
 *      a continuous east-bound walk from the old edge, driven by the same key
 *      a visitor presses, sampled every leg.
 *
 * Exit status: 0 when the band walks, 1 when any land stand fails one of those
 * clauses or the walk does not move. This reports AND gates its own claim,
 * unlike the `measure_*` tools that only report, because a closed ticket is
 * exactly the thing that needs to be re-runnable by whoever doubts it.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { loadHeightfield } from './measure_terrain_fit.mjs';

// Playwright is installed globally here, and ESM does not honour NODE_PATH, so
// resolve the global root and import by absolute path. Same shape as the smoke.
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

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const PORT = Number(process.env.EAST_BAND_PORT || 4191);
const YEAR = process.env.EAST_BAND_YEAR || '1835';
const EPOCH = process.env.EAST_BAND_EPOCH || 'e1834_harbor_cut';
const asJson = process.argv.includes('--json');

/**
 * The east edge of the 2026-08-10 field, in local ENU metres. See the header:
 * 257 columns of 2.5 m from origin_e −320.0. Everything east of this line is
 * "the eastern band" T-0010 names.
 */
const OLD_EDGE_E = 320.0;

/** S2e's own requirement for the replacement box, quoted in T-0010. */
const REQUIRED_EAST_M = 1700.0;

/** `renderers/web/js/terrain.js` — below this the surface is river, not land. */
const SHORE_Y = -0.10;

/** The cuts T-0010's own note reports the band at, so the two can be compared. */
const BAND_CUTS = [OLD_EDGE_E, 800, 1200, Infinity];

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};

// --- 1 + 2: the field, read straight off the committed bytes -------------- //

function bandStats(hf) {
  const { cols, rows, cell_m: cell, origin_e: oe, origin_n: on } = hf.meta;
  const bands = [];
  for (let b = 0; b < BAND_CUTS.length - 1; b += 1) {
    bands.push({
      from_e: BAND_CUTS[b],
      to_e: BAND_CUTS[b + 1],
      cells: 0, dry: 0, min_m: Infinity, max_m: -Infinity,
    });
  }
  for (let j = 0; j < rows; j += 1) {
    const n = on + j * cell;
    for (let i = 0; i < cols; i += 1) {
      const e = oe + i * cell;
      const band = bands.find((s) => e >= s.from_e && e < s.to_e);
      if (!band) continue;
      const y = hf.height(e, n);
      band.cells += 1;
      if (y >= SHORE_Y) band.dry += 1;
      if (y < band.min_m) band.min_m = y;
      if (y > band.max_m) band.max_m = y;
    }
  }
  return bands.map((b) => ({
    ...b,
    to_e: Number.isFinite(b.to_e) ? b.to_e : oe + (cols - 1) * cell,
    dry_pct: b.cells ? (100 * b.dry) / b.cells : 0,
  }));
}

// --- 3: the records that stand on it -------------------------------------- //

function placedEastOfOldEdge(hf) {
  const dir = path.join(ROOT, 'data', 'sidecars', YEAR);
  const out = [];
  for (const file of fs.readdirSync(dir).sort()) {
    if (!file.endsWith('.json')) continue;
    let doc;
    try { doc = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8')); } catch { continue; }
    const p = doc.placement ?? {};
    if (typeof p.local_e !== 'number' || typeof p.local_n !== 'number') continue;
    if (p.local_e <= OLD_EDGE_E) continue;
    const y = hf.height(p.local_e, p.local_n);
    out.push({
      id: doc.id ?? file.replace(/\.json$/, ''),
      e: p.local_e,
      n: p.local_n,
      field_y_m: y,
      land: y >= SHORE_Y,
      in_field: hf.inside(p.local_e, p.local_n),
    });
  }
  return out.sort((a, b) => a.e - b.e);
}

// --- 4: the walk ----------------------------------------------------------- //

/**
 * The east-bound transect, as (E, N) pairs a visitor could walk between. It
 * starts ON the old edge — the last ground the 2026-08-10 field held — and runs
 * out along the north bank of the harbour reach, which is the ground the fort,
 * the lighthouse and the north pier stand on. Nothing here is a camera invented
 * for the test: each leg ends within a few metres of a placed record.
 */
const TRANSECT = [
  { at: [OLD_EDGE_E, 200], why: 'the last ground the old field held' },
  { at: [700, 200], why: 'the North Division infill east of the old edge' },
  { at: [1000, 180], why: 'the ground between the town and the fort' },
  { at: [1180, 300], why: 'north of the fort, on the way to the piers' },
];

async function walkTheBand(chromium, stands) {
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
  const base = `http://127.0.0.1:${PORT}/renderers/web/index.html?year=${YEAR}`;

  const browser = await chromium.launch({
    executablePath: process.env.PW_EXECUTABLE || undefined,
    args: ['--enable-unsafe-swiftshader'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    page.setDefaultTimeout(90_000);
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e?.message || e)));

    await page.goto(base, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready === true, { timeout: 60_000 });

    const eyeHeight = await page.evaluate(() => window.__chicago4d.walkBudget.eyeHeight);

    // Every record's stand, taken through the walker rather than through the
    // field: `teleport` runs the same floor resolution walking does, so a stand
    // that disagrees with the field here is a stand a visitor would fall through.
    //
    // THE POINT IS ASKED WHERE THE WALKER ENDED UP, NOT WHERE IT WAS SENT. A
    // record's placement is the centre of a building, so a frame stepped after
    // the teleport slides the capsule out of that footprint (`pushOut`) — the
    // walker declining to stand inside a wall, which is correct and is the whole
    // reason it exists. Reading the field at the REQUESTED point instead scored
    // 104 of these 229 stands as failures on differences of half a millimetre,
    // which was the instrument disagreeing with itself rather than the ground
    // being wrong. The push-out distance is reported instead.
    const taken = await page.evaluate((list) => {
      const a = window.__chicago4d;
      return list.map((s) => {
        a.walker.teleport({ local_e: s.e, local_n: s.n, yaw_deg: 90 });
        a.step();
        const e = a.walker.state.e;
        const n = a.walker.state.n;
        return {
          id: s.id,
          pushed_out_m: Math.hypot(e - s.e, n - s.n),
          in_bounds: a.terrain.inBounds(e, n),
          walk_height_m: a.terrain.walkHeight(e, n),
          ground_y_m: a.walker.state.groundY,
          eye_y_m: a.walker.state.eyeY,
          is_water: a.terrain.isWater(e, n),
        };
      });
    }, stands.map(({ id, e, n }) => ({ id, e, n })));

    // The transect, walked with the key a visitor presses. Software
    // rasterisation runs this scene at a handful of frames a second, so each
    // leg gets a wall-clock window that survives it: 3.5 s, chosen because the
    // first leg cleared the 0.3 m floor by only 0.06 m at 2.2 s and a gate that
    // narrow measures the host's load rather than the ground.
    const legs = [];
    for (let i = 0; i < TRANSECT.length; i += 1) {
      const stand = TRANSECT[i];
      await page.evaluate(([e, n]) => {
        window.__chicago4d.walker.teleport({ local_e: e, local_n: n, yaw_deg: 90 });
        window.__chicago4d.step();
      }, stand.at);
      const before = await page.evaluate(() => ({ ...window.__chicago4d.player }));
      await page.keyboard.down('KeyW');
      await page.waitForTimeout(3500);
      await page.keyboard.up('KeyW');
      const after = await page.evaluate(() => {
        const a = window.__chicago4d;
        return {
          ...a.player,
          in_bounds: a.terrain.inBounds(a.walker.state.e, a.walker.state.n),
          walk_height_m: a.terrain.walkHeight(a.walker.state.e, a.walker.state.n),
          ground_y_m: a.walker.state.groundY,
          eye_y_m: a.walker.state.eyeY,
        };
      });
      legs.push({
        from: stand.at, why: stand.why,
        moved_m: Math.hypot(after.e - before.e, after.n - before.n),
        ended_e: after.e, ended_n: after.n,
        in_bounds: after.in_bounds,
        floor_error_m: Math.abs(after.ground_y_m - after.walk_height_m),
        eye_error_m: Math.abs(after.eye_y_m - after.ground_y_m - eyeHeight),
      });
    }

    return { eyeHeight, taken, legs, errors };
  } finally {
    await browser.close();
    await new Promise((r) => server.close(r));
  }
}

// --- report ---------------------------------------------------------------- //

const hf = await loadHeightfield(path.join(ROOT, 'data', 'terrain', 'epochs', EPOCH));
const { cols, cell_m: cell, origin_e: oe } = hf.meta;
const eastReach = oe + (cols - 1) * cell;
const bands = bandStats(hf);
const records = placedEastOfOldEdge(hf);
// A record east of the old edge is not automatically ON the field: the box grew
// EAST, not south, and `heacock_house_monroe` stands 220 m off the south edge and
// says so in its own note. Those are reported by name and not gated — the southern
// ground is T-0026's ticket, and folding it in here would let this one fail for
// work it never claimed.
const onField = records.filter((r) => r.in_field);
const offField = records.filter((r) => !r.in_field);

const { chromium } = await loadPlaywright();
const walk = await walkTheBand(chromium, onField);

// The clauses, and what each of them refuses.
//
// `walkHeight` is the walker's contract with the field, so its tolerance is a
// float-comparison epsilon and not a budget: the two are the same number
// computed twice, and any gap is a bug rather than a drift.
//
// A FLOOR ABOVE THE FIELD IS NOT A FAILURE, and getting that wrong was this
// tool's first reading. Two of the 229 — `slough_log_bridge` and `north_pier` —
// carry a DECK, and `walker.surfaceAt` gives a deck the floor over land. A
// visitor standing on the planks of a bridge is standing, which is the thing
// being measured. What may never happen is the floor sinking BELOW the field:
// that is falling through the ground. So the clause is one-sided, and the
// stands that stand higher are named rather than counted as passes in silence.
const EPS_M = 1e-6;
const sank = (s) => s.ground_y_m < s.walk_height_m - EPS_M;
const onADeck = walk.taken.filter((s) => s.ground_y_m > s.walk_height_m + EPS_M);
const badStands = walk.taken.filter((s) => !s.in_bounds || sank(s)
  || Math.abs(s.eye_y_m - s.ground_y_m - walk.eyeHeight) > EPS_M);
const badLegs = walk.legs.filter((l) => l.moved_m <= 0.3 || !l.in_bounds
  || l.floor_error_m > EPS_M || l.eye_error_m > EPS_M);
const reaches = eastReach >= REQUIRED_EAST_M;
const ok = reaches && !badStands.length && !badLegs.length && !walk.errors.length;

const result = {
  epoch: EPOCH,
  old_edge_e_m: OLD_EDGE_E,
  east_reach_m: eastReach,
  required_east_m: REQUIRED_EAST_M,
  gained_east_m: eastReach - OLD_EDGE_E,
  bands,
  records: records.length,
  on_field_records: onField.length,
  dry_records: onField.filter((r) => r.land).length,
  stands_walked: walk.taken.length,
  stands_on_a_deck: onADeck.map((s) => s.id),
  stands_off_the_field: offField.map((r) => r.id),
  stands_failing: badStands,
  legs: walk.legs,
  page_errors: walk.errors,
  verdict: ok ? 'the eastern band walks' : 'the eastern band does NOT walk',
};

if (asJson) {
  console.log(JSON.stringify(result, null, 2));
} else {
  console.log(`east band — epoch ${EPOCH}, year ${YEAR}\n`);
  console.log(`  the field used to stop at E +${OLD_EDGE_E.toFixed(1)} m (257² box, 2026-08-10)`);
  console.log(`  it now reaches            E +${eastReach.toFixed(1)} m `
    + `(${reaches ? 'meets' : 'MISSES'} S2e's own E +${REQUIRED_EAST_M} requirement)`);
  console.log(`  gained                      ${(eastReach - OLD_EDGE_E).toFixed(1)} m of ground east\n`);
  console.log('  band                cells      dry      min m     max m');
  for (const b of bands) {
    console.log(`  E ${String(b.from_e).padStart(6)}..${String(Math.round(b.to_e)).padEnd(6)} `
      + `${String(b.cells).padStart(7)}  ${b.dry_pct.toFixed(1).padStart(6)} % `
      + `${b.min_m.toFixed(2).padStart(8)}  ${b.max_m.toFixed(2).padStart(8)}`);
  }
  console.log(`\n  ${records.length} placed record(s) east of the old edge, `
    + `${onField.length} of them on the field and `
    + `${onField.filter((r) => r.land).length} of those over dry ground`);
  console.log(`  ${walk.taken.length} stand(s) taken through the walker — `
    + `${walk.taken.length - badStands.length} stood, ${badStands.length} failed`);
  if (onADeck.length) {
    console.log(`  ${onADeck.length} of them stood on a DECK rather than on the field, `
      + `which is what a deck is for: ${onADeck.map((s) => s.id).join(', ')}`);
  }
  if (offField.length) {
    console.log(`  ${offField.length} record(s) east of the old edge are off the field `
      + `entirely and are not this ticket's ground: ${offField.map((r) => r.id).join(', ')}`);
  }
  for (const s of badStands.slice(0, 10)) {
    console.log(`    FAIL ${s.id}: in_bounds=${s.in_bounds} `
      + `floor ${s.ground_y_m.toFixed(4)} vs field ${s.walk_height_m.toFixed(4)} `
      + `eye ${(s.eye_y_m - s.ground_y_m).toFixed(4)}`);
  }
  console.log('\n  the transect, walked on the W key:');
  for (const l of walk.legs) {
    console.log(`    from E ${String(l.from[0]).padStart(6)} N ${String(l.from[1]).padStart(5)} `
      + `— moved ${l.moved_m.toFixed(2)} m in 3.5 s to E ${l.ended_e.toFixed(1)} `
      + `N ${l.ended_n.toFixed(1)}, on the grid: ${l.in_bounds}  (${l.why})`);
  }
  if (walk.errors.length) {
    console.log(`\n  PAGE ERRORS: ${walk.errors.length}`);
    for (const e of walk.errors.slice(0, 5)) console.log(`    ${e}`);
  }
  console.log(`\n  ${ok ? 'PASS' : 'FAIL'} — ${result.verdict}`);
}

process.exit(ok ? 0 : 1);
