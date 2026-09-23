/**
 * measure_drawn_placement.mjs — where the town is DRAWN, against where its own
 * records say it was PLACED.
 *
 * ROADMAP K50, and the reason it exists is R-BUG5b. The whole near-field wood
 * was drawn on the wrong side of the river for weeks while three gates stayed
 * green, because every one of them walked the list the planter writes at the
 * moment it DECIDES to plant. Nothing anywhere read the geometry back. The
 * conversion that separates the two is one sign — `enuToWorld` in terrain.js is
 * `(e, y, -n)` — so a layer that hands an ENU northing to a slot expecting a
 * three world z draws its whole population mirrored across the datum's
 * east-west line, and every test of the decision passes.
 *
 * Four layers in this renderer decide in ENU and draw in world space:
 *
 *   flora.js .... measured clean by R-BUG5b itself (`_m.setPosition(e, y, -n2)`)
 *   ground ...... answered twice: smoke_renderer.mjs reads the drawn surface
 *                 back against `heightfield.bin` at every field sample, and
 *                 tools/measure_terrain_horizontal.mjs holds its two horizontal
 *                 axes against the master mesh
 *   buildings.js  HERE
 *   streets.js .. HERE
 *
 * What each layer DECIDED is committed and independent of the renderer — a
 * structure's `placement.local_e/local_n` in its sidecar, a street's
 * `path_local_enu_m` — so both halves below compare drawn vertices against the
 * DATA and never against another number the renderer computed. That is the
 * R-BUG3c lesson applied: a gate that compares the renderer with itself is a
 * gate that agrees with itself.
 *
 * THE BUILDING INVARIANT IS NOT "THE CENTRE IS THE ANCHOR". A structure's
 * anchor is its FRONTAGE and the body grows from it — K30(b) measured 331 of
 * 333 footprints growing from the minimum corner — so the honest, sign-sensitive
 * statement is that **the anchor lies inside the body's own drawn plan
 * footprint**. Under a mirrored northing a building 200 m north of the datum is
 * drawn 400 m from its anchor, which no footprint in this town spans.
 *
 * `mirrorCloser` is that signature stated directly: how many bodies stand
 * nearer to the mirror of their anchor than to the anchor, among anchors far
 * enough off the datum's east-west line for the question to mean anything. It
 * prints whether it is zero or not, because a gate whose interesting value
 * never prints is a gate nobody can read.
 *
 * TWO FALSE POSITIVES WERE MEASURED OUT OF THIS INSTRUMENT BEFORE IT WAS
 * BELIEVED, and they are the transferable part:
 *
 *   1. **a per-INSTANCE box is not a building.** A structure joins one batch
 *      per material it uses, so a first reading compared 1,310 "bodies" for a
 *      town of 331 structures and reported 279 anchors outside their footprint
 *      — one body's walls judged without its roof. `buildings.js`
 *      `instanceBounds()` warns about precisely this in its own comment, for
 *      precisely the reason a size gate once passed a town of collapsed boxes.
 *      Unioned per structure id, the count is 0.
 *   2. **the mirror test does not discriminate on a street grid.** Asked of
 *      road vertices it answered "nearer at the mirror" for 3,975 of 19,372 on
 *      a build where every vertex is inside its own track: reflect a point
 *      across an east-west line in a grid town and it lands on another
 *      east-west street, and a vertex at the EDGE of its track scores worse
 *      than a mirror landing mid-track by construction. So the streets half
 *      gates on the half-width test alone, which a mirrored ribbon cannot pass
 *      — it would run where no centreline is recorded — and the mirror figure
 *      is printed as a diagnostic that gates nothing.
 *
 * The instrument that caught R-BUG5b does not transfer whole. What transfers is
 * the QUESTION.
 *
 *   node tools/measure_drawn_placement.mjs              the published mirror
 *   node tools/measure_drawn_placement.mjs --source     the source tree
 *   node tools/measure_drawn_placement.mjs --json
 *   node tools/measure_drawn_placement.mjs --gate       exit 1 on a stray
 *   node tools/measure_drawn_placement.mjs --refute     the negative control:
 *       mirror the drawn scene and prove the census reports it. Exits 1 if the
 *       broken build still reads clean, which is the only way a gate this shape
 *       can be believed.
 *
 * The gate itself lives in `tools/smoke_renderer.mjs`, at both viewports, which
 * is where a release is held. This is the instrument: it runs in about a minute
 * against one viewport, so a change to either layer can be priced without
 * spending a smoke.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { CENSUS, BREAK_IT } from './drawn_placement_census.mjs';

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
const PORT = Number(process.env.SMOKE_PORT || 4191);
const YEAR = process.env.SMOKE_YEAR || '1835';
const JSON_OUT = process.argv.includes('--json');
const GATE = process.argv.includes('--gate');
const SOURCE = process.argv.includes('--source');
const REFUTE = process.argv.includes('--refute');
const ROOT = SOURCE ? path.resolve(HERE, '..') : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/index.html' : '/walk/';

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

const out = await page.evaluate(`(${CENSUS.toString()})()`);
// The negative control runs LAST and on a scene it has ruined, so nothing
// above it can be contaminated by the fault it injects.
let broken = null;
if (REFUTE) {
  const hit = await page.evaluate(`(${BREAK_IT.toString()})()`);
  broken = await page.evaluate(`(${CENSUS.toString()})()`);
  broken.injected = hit;
}
await browser.close();
server.close();

if (JSON_OUT) {
  console.log(JSON.stringify({ target: SOURCE ? 'source' : 'published', ...out }, null, 2));
} else {
  const B = out.buildings;
  const S = out.streets;
  console.log(`drawn-vs-decided — ${SOURCE ? 'source tree' : 'published mirror'}, 1280x800\n`);
  console.log('buildings');
  console.log(`  ${B.compared} structures compared, unioned from ${B.instances} instances in `
    + `${B.batches} batches (${B.verts.toLocaleString()} vertices read back)`);
  console.log(`  anchor outside its own drawn footprint: ${B.outside}`
    + `   worst ${B.worst.toFixed(2)} m${B.worstId ? ` (${B.worstId}, span ${B.worstSpan} m)` : ''}`);
  console.log(`  worst anchor-to-nearest-corner: ${B.worstCorner.toFixed(2)} m`);
  console.log(`  nearer to the MIRROR of its anchor (|N| > 5 m): ${B.mirrorCloser}`
    + `${B.worstMirrorId ? ` (first ${B.worstMirrorId})` : ''}`);
  console.log(`  instances with no readable placement: ${B.unrecorded}`);
  for (const s of B.strays) {
    console.log(`    ${s.id}: anchor E ${s.anchor[0]} N ${s.anchor[1]}, `
      + `drawn centre E ${s.drawn[0]} N ${s.drawn[1]}, ${s.out} m outside a ${s.span} m span `
      + `(${s.parts} material parts)`);
  }
  for (const c of B.corners) {
    console.log(`    mirror: ${c.id} anchor N ${c.anchorN}, drawn N ${c.drawnN}, `
      + `own ${c.own} m vs mirrored ${c.mirrored} m`);
  }
  console.log('\nstreets');
  console.log(`  ${S.verts.toLocaleString()} drawn vertices in ${S.meshes} meshes against `
    + `${S.records} centrelines`);
  console.log(`  further than half a track from every centreline: ${S.stray}`
    + `   worst ${S.worst.toFixed(2)} m`
    + (S.worstAt ? ` at E ${S.worstAt.e} N ${S.worstAt.n}` : '')
    + `, ${S.beyondBounds} outside every street's bounds altogether`);
  console.log(`  diagnostic, gates nothing — mirrored northing also on a road: `
    + `${S.mirrorAlsoOnRoad} of ${S.verts.toLocaleString()}`);
  console.log(`\npage errors: ${pageErrors.length}`);
  for (const e of pageErrors.slice(0, 5)) console.log(`  ${e}`);
  if (broken) {
    const b = broken.buildings;
    const s = broken.streets;
    console.log(`\nnegative control — R-BUG5b's fault injected into this scene `
      + `(${broken.injected.instances} instance matrices, `
      + `${broken.injected.verts.toLocaleString()} road vertices mirrored)`);
    console.log(`  buildings: ${b.outside} of ${b.compared} anchors outside their footprint, `
      + `worst ${b.worst.toFixed(2)} m; ${b.mirrorCloser} nearer to their mirror`);
    console.log(`  streets:   ${s.stray} of ${s.verts.toLocaleString()} vertices off every `
      + `centreline, worst ${s.worst.toFixed(2)} m, `
      + `${s.beyondBounds.toLocaleString()} off the grid altogether`);
  }
}

// A gate that has only ever run on a correct build has demonstrated nothing.
const refuted = !broken
  || (broken.buildings.outside > 0 && broken.buildings.mirrorCloser > 0
    && broken.streets.stray > 0);
if (broken && !JSON_OUT) {
  console.log(refuted
    ? '\nTHE CENSUS SEES THE FAULT'
    : '\nTHE CENSUS DOES NOT SEE THE FAULT — it is not an instrument');
}

const clean = out.buildings.outside === 0 && out.buildings.mirrorCloser === 0
  && out.buildings.unrecorded === 0 && out.streets.stray === 0
  && pageErrors.length === 0;
if (!JSON_OUT) console.log(clean ? '\nBOTH LAYERS DRAW WHERE THEY DECIDED' : '\nSTRAYS FOUND');
if (JSON_OUT && broken) console.log(JSON.stringify({ broken }, null, 2));
process.exit(((GATE && !clean) || !refuted) ? 1 : 0);
