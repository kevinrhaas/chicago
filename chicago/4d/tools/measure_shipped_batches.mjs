/**
 * measure_shipped_batches.mjs — what the town's building batches cost, read off
 * a loaded page rather than off the files.
 *
 *   node tools/measure_shipped_batches.mjs               the source tree
 *   node tools/measure_shipped_batches.mjs --published   the mirror a visitor gets
 *   node tools/measure_shipped_batches.mjs --root DIR    any other tree, e.g. a
 *                                                        scratch copy of the mirror
 *                                                        holding the PREVIOUS bytes
 *   node tools/measure_shipped_batches.mjs --json FILE   also write the census
 *
 * WHY IT EXISTS — K36(b). R-W5a collapsed 47 building batches to 16 by taking
 * `color` out of `materialKey`, and every number in that write-up was taken
 * against the SOURCE tree. K36(a) then measured that the source tree and the
 * mirror do not carry the same materials: `gltf-transform`'s palette pass folds
 * the named materials of 38 assets into one `PaletteMaterial001` plus two
 * generated PNGs, so 38 shipped assets carry a texture that no master has.
 *
 * `materialKey` in `renderers/web/js/buildings.js` includes `m.map?.uuid`, and a
 * GLTFLoader mints a fresh uuid per loaded texture. So an asset that arrives
 * with its own generated map cannot join any batch — not even another palette
 * asset's. That is a prediction with a number in it, and this reads the number:
 * batches, how many of them carry a map, and how many buildings each holds.
 *
 * IT ADDS NO RENDERER HOOK. Everything below comes from `window.__chicago4d`'s
 * existing `stats()`, `buildings.batches` and `ready`, the same surface
 * `tools/critic_shots.mjs` and `tools/smoke_renderer.mjs` drive. One page load,
 * one viewport, no captures — it is seconds, not minutes, because the quantity
 * is a property of the SCENE and not of any camera.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

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
const APP = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const value = (name, fallback) => {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};

const ROOT_ARG = value('--root', '');
const PUBLISHED = flag('--published') || !!ROOT_ARG;
const JSON_OUT = value('--json', '');
const PORT = Number(process.env.BATCH_PORT || 4193);
const YEAR = process.env.CRITIC_YEAR || '1835';
const ROOT = ROOT_ARG
  ? path.resolve(ROOT_ARG)
  : (PUBLISHED ? path.resolve(APP, '../../site/chicago/4d') : APP);
const ENTRY = PUBLISHED ? '/walk/' : '/renderers/web/index.html';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
  '.geojson': 'application/json',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' }).end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
if (PUBLISHED && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`;

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
page.setDefaultTimeout(180_000);
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message || e}`));
await page.addInitScript(() => {
  localStorage.setItem('chicago4d.detail', 'full');
  localStorage.setItem('chicago4d.help.seen', '1');
});
await page.goto(base, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180_000 });

const census = await page.evaluate(() => {
  const api = window.__chicago4d;
  const batches = api.buildings.batches.map((b) => {
    const m = b.material;
    // Instances hold structure ids; the batch's own index is the join key the
    // raycast uses, so it is also the honest count of buildings in the batch.
    const ids = (b.userData.batchIndex ?? []).filter(Boolean);
    return {
      name: b.name,
      roughness: typeof m.roughness === 'number' ? Number(m.roughness.toFixed(3)) : null,
      hasMap: !!m.map,
      mapName: m.map?.name || (m.map ? '(unnamed)' : null),
      structures: ids.length,
      sample: ids.slice(0, 3),
    };
  });
  return { stats: api.stats(), batches };
});

/**
 * The batch count is a property of the scene; the DRAW CALL is a property of a
 * pose, because a BatchedMesh holding one building is culled the moment that
 * building leaves the frustum. So the two numbers answer different questions and
 * both belong here: how many batches the town costs at all, and how many of them
 * a visitor actually pays for where the scene invites them to stand.
 *
 * The anchors come from `data/scenes/<year>.json` through the renderer's own
 * `goTo`, the same way `tools/critic_shots.mjs` reaches them — this adds no way
 * to drive the scene that the app does not already offer a visitor.
 */
const ANCHOR_IDS = JSON.parse(
  fs.readFileSync(path.join(APP, 'data/scenes', `${YEAR}.json`), 'utf8'),
).anchors.map((a) => a.id);
const anchors = await page.evaluate(async (ids) => {
  const api = window.__chicago4d;
  const out = [];
  for (const id of ids) {
    if (!api.goTo(id)) continue;
    // Two frames: the first resolves the teleport, the second is the frame whose
    // culling the counter is reading.
    api.step(); api.step();
    out.push({ id, drawCalls: api.stats().drawCalls, triangles: api.stats().triangles });
  }
  return out;
}, ANCHOR_IDS);

await browser.close();
server.close();

const withMap = census.batches.filter((b) => b.hasMap);
const withoutMap = census.batches.filter((b) => !b.hasMap);
const held = (list) => list.reduce((n, b) => n + b.structures, 0);

console.log(`\n== building batches · ${PUBLISHED ? 'published mirror' : 'source tree'} · ${YEAR}`);
console.log(`   batches ............ ${census.batches.length}`);
console.log(`     textured ......... ${withMap.length}  holding ${held(withMap)} building(s)`);
console.log(`     untextured ....... ${withoutMap.length}  holding ${held(withoutMap)} building(s)`);
console.log(`   structures loaded .. ${census.stats.structures}`);
console.log(`   textures in memory . ${census.stats.textures}`);
console.log(`   shader programs .... ${census.stats.programs}`);
console.log(`   draw calls (this frame, 1280x800 at the entry pose)`);
console.log(`                        ${census.stats.drawCalls} of ${census.stats.budget.drawCalls}`);

const roll = new Map();
for (const b of withoutMap) {
  roll.set(b.roughness, (roll.get(b.roughness) ?? 0) + b.structures);
}
console.log('\n   untextured batches, by roughness:');
for (const [r, n] of [...roll].sort((a, b) => b[1] - a[1])) {
  console.log(`     r=${String(r).padEnd(5)}  ${String(n).padStart(4)} building(s)`);
}
if (withMap.length) {
  console.log(`\n   textured batches (one per generated map — these cannot merge):`);
  for (const b of withMap.slice(0, 5)) {
    console.log(`     ${b.name}  r=${b.roughness}  ${b.structures} building(s)  ${b.sample[0] ?? ''}`);
  }
  if (withMap.length > 5) console.log(`     … and ${withMap.length - 5} more`);
}
console.log('\n   draw calls at the scene anchors:');
for (const a of anchors) {
  const over = a.drawCalls > census.stats.budget.drawCalls ? '  OVER BUDGET' : '';
  console.log(`     ${a.id.padEnd(20)} ${String(a.drawCalls).padStart(3)} of `
    + `${census.stats.budget.drawCalls}${over}`);
}
const calls = anchors.map((a) => a.drawCalls);
if (calls.length) {
  console.log(`     ${'worst'.padEnd(20)} ${Math.max(...calls)}`);
}
if (errors.length) {
  console.error(`\n   PAGE ERRORS (${errors.length}):`);
  for (const e of errors.slice(0, 5)) console.error(`     ${e}`);
}
console.log('');

if (JSON_OUT) {
  fs.writeFileSync(JSON_OUT, `${JSON.stringify({ ...census, anchors }, null, 1)}\n`);
  console.log(`   census written to ${JSON_OUT}\n`);
}
process.exit(errors.length ? 1 : 0);
