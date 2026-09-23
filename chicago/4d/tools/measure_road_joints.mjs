/**
 * measure_road_joints.mjs — T-0184. Does the road ribbon close at its bends?
 *
 *   node tools/measure_road_joints.mjs            the published mirror
 *   node tools/measure_road_joints.mjs --source   the source tree
 *   node tools/measure_road_joints.mjs --json
 *   node tools/measure_road_joints.mjs --gate     exit 1 on uncovered ground
 *
 * `renderers/web/js/streets.js` used to build every panel square to ITS OWN
 * chord, so at a bend the row at a shared centreline point was drawn twice —
 * once perpendicular to the incoming chord, once to the outgoing one. The two
 * rows crossed at the centreline and diverged towards the edges, which opened a
 * wedge of unpainted ground on the outside of the turn and stacked a matching
 * overlap on the inside. Measured here, on the shipped build, before the fix:
 *
 *   south_water [120, -57]   17.8 deg on a 10.5 m track   4.13 m2 uncovered
 *   dearborn    [698.9, 7]    5.7 deg on a 7 m track      0.29 m2 uncovered
 *
 * — the second being L178's admitted artefact, already half covered by South
 * Water Street's own roadway, and the first the larger one it named and did not
 * fix. The whole town read 15.35 m2 over 27 authored bends.
 *
 * The instrument is `tools/road_joint_probe.mjs`, which the smoke runs too. Its
 * control runs on every build: the same 2 cm lattice is probed against a
 * reference ribbon built from the same committed centrelines under the OLD
 * square-joint rule, so `square` is the wedge and `drawn` is what is left. A
 * build where the reference reads zero is a build where this tool has stopped
 * measuring anything, and it says so and fails.
 *
 * `overhang` is the other half of the answer and the reason a mitre cannot
 * simply be run out to its natural length. A mitred corner stands
 * `half * (sec(turn/2) - 1)` past the bend vertex — 0.17 m at the fort road's
 * 39-degree turn — and `tools/measure_drawn_placement.mjs` holds every drawn
 * vertex within 0.05 m of its own street's half-width. This prints the local
 * reading of that same arithmetic at every joint, so the two gates can be seen
 * to agree rather than assumed to.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { JOINT_PROBE } from './road_joint_probe.mjs';

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
const PORT = Number(process.env.JOINT_PORT || 4197);
const YEAR = process.env.SMOKE_YEAR || '1835';
const JSON_OUT = process.argv.includes('--json');
const GATE = process.argv.includes('--gate');
const SOURCE = process.argv.includes('--source');
const ROOT = SOURCE ? path.resolve(HERE, '..') : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/index.html' : '/walk/';

/** 2 cm: the probe L178 quoted, and fine enough that the 0.30 m2 it reported at
 *  the Dearborn corner is 750 lattice points rather than a handful. */
const CELL_M = 0.02;
/** How far past the half-width the lattice reaches. The nominal ribbon stops at
 *  the half-width; the pad only has to hold the drawn corners that stand outside
 *  it, and the widest a mitre can stand is 0.17 m in this town. */
const PAD_M = 0.35;
/** Below this a "bend" is the rounding of an authored coordinate, not a turn:
 *  four of the committed vertices turn by 0.02-0.06 deg, which opens a wedge
 *  measured in square millimetres. */
const TURN_EPS_DEG = 0.25;

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
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e.message || e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 120000 });

const opts = { cellM: CELL_M, padM: PAD_M, turnEpsDeg: TURN_EPS_DEG };
const out = await page.evaluate(
  `(${JOINT_PROBE.toString()})(${JSON.stringify(opts)})`,
);
await browser.close();
server.close();

// The control: the reference ribbon must show the fault this probe exists to
// see. If a square joint reads clean, nothing below is a measurement.
const instrument = out.totals.squareGapM2 > 0.1;

if (JSON_OUT) {
  console.log(JSON.stringify({ target: SOURCE ? 'source' : 'published', instrument, ...out }, null, 2));
} else {
  console.log(`road joints — ${SOURCE ? 'source tree' : 'published mirror'}, `
    + `${CELL_M * 100} cm plan lattice, turns over ${TURN_EPS_DEG} deg\n`);
  console.log('  street          at                 turn   paintable  UNCOVERED   square-joint   overhang');
  for (const j of out.joints.slice().sort((x, y) => y.drawnGapM2 - x.drawnGapM2
    || y.squareGapM2 - x.squareGapM2)) {
    console.log(`  ${j.street.padEnd(14)} `
      + `${`[${j.at[0]}, ${j.at[1]}]`.padEnd(18)} `
      + `${`${j.turnDeg}`.padStart(6)}   `
      + `${j.nominalM2.toFixed(2).padStart(7)}    `
      + `${j.drawnGapM2.toFixed(3).padStart(8)}   `
      + `${j.squareGapM2.toFixed(3).padStart(8)}       `
      + `${j.overhangM == null ? '     -' : j.overhangM.toFixed(3).padStart(6)}`);
  }
  console.log(`\n  ${out.totals.joints} authored bends, ${out.triangles.toLocaleString('en-US')} `
    + `drawn triangles read back`);
  console.log(`  bends whose own ribbon is refused for water, so they carry no `
    + `joint question: ${out.totals.waterRefusedJoints}`);
  console.log(`  uncovered inside the nominal ribbon: ${out.totals.drawnGapM2.toFixed(3)} m2`);
  console.log(`  the same lattice against SQUARE joints (the control): `
    + `${out.totals.squareGapM2.toFixed(3)} m2`
    + `, closed form ${out.totals.sectorM2.toFixed(3)} m2`);
  console.log(`  worst drawn vertex beyond its own half-width: `
    + `${out.totals.worstOverhangM.toFixed(3)} m (census tolerance 0.05)`);
  console.log(`\npage errors: ${pageErrors.length}`);
  for (const e of pageErrors.slice(0, 5)) console.log(`  ${e}`);
  console.log(instrument
    ? '\nTHE PROBE SEES A SQUARE JOINT'
    : '\nTHE PROBE DOES NOT SEE A SQUARE JOINT — it is not an instrument');
  console.log(out.totals.drawnGapM2 === 0
    ? 'EVERY BEND IS CLOSED'
    : 'BENDS LEAVE GROUND UNCOVERED');
}

const clean = out.totals.drawnGapM2 === 0
  && out.totals.worstOverhangM <= 0.05
  && pageErrors.length === 0;
process.exit(((GATE && !clean) || !instrument) ? 1 : 0);
