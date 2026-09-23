/**
 * measure_drawn_timber.mjs — where the near-field wood is DRAWN, against the
 * stations that decided to plant it, and whether the gate that asks it can
 * still fail.
 *
 * T-0243. The two timber-placement gates in `tools/smoke_renderer.mjs` matched
 * no mesh from the moment T-0223's `BatchedMesh` landed: one went red on its own
 * liveness clause and the other — `no timber is drawn out in the channel` —
 * passed on an empty traversal, week after week, asserting nothing. This is the
 * instrument for the repaired census, and `--refute` is the part that matters:
 * it displaces two chunks of the live timber and requires the census to report
 * both, because a gate that has only ever run on a correct build has
 * demonstrated nothing.
 *
 *   node tools/measure_drawn_timber.mjs              the published mirror
 *   node tools/measure_drawn_timber.mjs --source     the source tree
 *   node tools/measure_drawn_timber.mjs --json
 *   node tools/measure_drawn_timber.mjs --gate       exit 1 on a stray
 *   node tools/measure_drawn_timber.mjs --refute     the negative control:
 *       mirror one chunk across the datum and shove another into open water,
 *       and prove the census sees each. Exits 1 if the broken build still
 *       reads clean, which is the only way a gate this shape can be believed.
 *
 * The gate itself lives in `tools/smoke_renderer.mjs` stage 7, at both
 * viewports, which is where a release is held. This runs against one viewport
 * in about a minute, so a change to `trees.js` can be priced without spending a
 * smoke. It is the sibling of `tools/measure_drawn_placement.mjs`, deliberately
 * the same shape.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { TIMBER_CENSUS, BREAK_TIMBER } from './drawn_timber_census.mjs';

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
const PORT = Number(process.env.SMOKE_PORT || 4193);
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

const out = await page.evaluate(`(${TIMBER_CENSUS.toString()})()`);
// The negative control runs LAST and on a scene it has ruined, so nothing above
// it can be contaminated by the fault it injects.
let broken = null;
let injected = null;
if (REFUTE) {
  injected = await page.evaluate(`(${BREAK_TIMBER.toString()})()`);
  broken = await page.evaluate(`(${TIMBER_CENSUS.toString()})()`);
}
await browser.close();
server.close();

const live = out.chunks > 0 && out.verts > 1000 && out.stations > 10 && out.unreadable === 0;
const clean = live && out.stray === 0 && out.offshore === 0 && pageErrors.length === 0;

if (JSON_OUT) {
  console.log(JSON.stringify({
    target: SOURCE ? 'source' : 'published', census: out, injected, broken, pageErrors,
  }, null, 2));
} else {
  console.log(`drawn timber — ${SOURCE ? 'source tree' : 'published mirror'}, 1280x800\n`);
  console.log(`  ${out.verts.toLocaleString()} vertices read back from ${out.chunks} chunk(s) `
    + `in ${out.batches} batch(es) and ${out.plainMeshes} plain mesh(es), `
    + `against ${out.stations} stations`);
  console.log(`  further than ${out.strayBarM} m from every station: ${out.stray}`
    + `   worst measurable ${out.worstStray} m`
    + (out.worstStrayAt ? ` at E ${out.worstStrayAt.e} N ${out.worstStrayAt.n}` : '')
    + `, ${out.outOfHash} beyond the hash altogether`);
  console.log(`  over water at all: ${out.wet}; further than ${out.offshoreBarM} m from dry `
    + `ground: ${out.offshore}   worst ${out.worstOffshore} m`
    + (out.worstOffshoreAt ? ` at E ${out.worstOffshoreAt.e} N ${out.worstOffshoreAt.n}` : ''));
  console.log(`  chunks the census could not read: ${out.unreadable}`
    + `   (inactive, skipped: ${out.inactiveChunks})`);
  console.log(`\npage errors: ${pageErrors.length}`);
  for (const e of pageErrors.slice(0, 5)) console.log(`  ${e}`);
}

// A gate that has only ever run on a correct build has demonstrated nothing.
// Each bar is refuted SEPARATELY: the mirror is what `stray` exists to catch,
// open water is what `offshore` exists to catch, and it was `offshore` that had
// been passing on nothing.
let refuted = true;
if (broken) {
  refuted = injected?.ok === true && broken.stray > 0 && broken.offshore > 0
    && broken.verts > 1000;
  if (!JSON_OUT) {
    console.log(`\nnegative control — ${injected?.ok
      ? `chunk ${injected.mirrored.chunk} mirrored across the datum `
        + `(N ${injected.mirrored.n} m, moved ${injected.mirrored.movedM} m, `
        + `${injected.mirrored.verts} vertices); chunk ${injected.drowned.chunk} moved from `
        + `E ${injected.drowned.from.e} N ${injected.drowned.from.n} to open water at `
        + `E ${injected.drowned.to.e} N ${injected.drowned.to.n}`
      : `NOT INJECTED — ${injected?.why}`}`);
    console.log(`  census on the broken scene: ${broken.stray} stray of `
      + `${broken.verts.toLocaleString()} vertices (worst measurable `
      + `${broken.worstStray} m, ${broken.outOfHash} beyond the hash), `
      + `${broken.offshore} offshore (worst ${broken.worstOffshore} m)`);
    console.log(refuted
      ? '\nTHE CENSUS SEES BOTH FAULTS'
      : '\nTHE CENSUS DOES NOT SEE THE FAULT — it is not an instrument');
  }
}

if (!JSON_OUT) {
  console.log(clean
    ? '\nEVERY TREE IS DRAWN AT ITS OWN STATION, AND NONE OF IT IS IN THE RIVER'
    : '\nSTRAYS FOUND');
}
process.exit(((GATE && !clean) || !refuted) ? 1 : 0);
