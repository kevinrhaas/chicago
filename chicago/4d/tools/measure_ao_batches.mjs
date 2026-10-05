/**
 * WHOSE OCCLUSION EACH OF THE TOWN'S BATCHES CARRIES (T-0285).
 *
 *   node tools/measure_ao_batches.mjs [--viewport desktop|mobile] [--json f]
 *
 * `buildings.js` merges every structure surface that shares a `materialKey()`
 * into one batch, and the key separates on `aoMap.uuid`. A master baked with
 * `generators/build.py --ao` carries ONE occlusion atlas of its own, bound by
 * the GLTF loader to every material in that file — so on paper every AO'd
 * building gets batches of its own. What the renderer does with that atlas is
 * not on paper: the wall relief (T-1963) and the roof relief (T-1488) rebind
 * `aoMap` to their shared maps BEFORE the key is taken, so the baked atlas on a
 * bound wall or roof is replaced, and only what neither binds keeps it.
 *
 * This boots the source tree once and reads the `structures` group as built:
 * how many batches, how many carry an `aoMap`, and of those how many carry a
 * SHARED relief map (`userData.chiWallRelief` / `chiRoofRelief`) against how
 * many carry a map no other batch has — a building's own atlas, which is a
 * batch, and a draw, that exists only because AO was baked. Run it on the tree
 * as committed and again after `build.py --all --ao`; the difference is the
 * cost, read rather than reasoned. It reads no frame: the draw counts at the
 * critic stations come from `tools/critic_shots.mjs`, which this does not
 * replace.
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

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const VIEWPORT = argAt('--viewport') || 'desktop';
const SIZE = VIEWPORT === 'mobile' ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const jsonOut = argAt('--json');
const PORT = Number(process.env.AO_BATCH_PORT || 4193);

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.geojson': 'application/json',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(APP, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(APP) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' }).end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const errors = [];
let reading;
try {
  const page = await browser.newPage({ viewport: SIZE, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.addInitScript(() => {
    localStorage.setItem('chicago4d.detail', 'full');
    localStorage.setItem('chicago4d.help.seen', '1');
  });
  await page.goto(`http://127.0.0.1:${PORT}/renderers/web/index.html?year=1835`,
    { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300_000 });
  reading = await page.evaluate(() => {
    const group = window.__chicago4d.scene3d.getObjectByName('structures');
    const materials = new Set();
    group.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) materials.add(m);
    });
    const byMap = new Map();
    for (const m of materials) {
      if (!m.aoMap) continue;
      byMap.set(m.aoMap.uuid, (byMap.get(m.aoMap.uuid) ?? 0) + 1);
    }
    const out = { batches: materials.size, withAo: 0, wallRelief: 0, roofRelief: 0,
      ownAtlas: 0, sharedOther: 0, distinctAoMaps: byMap.size };
    for (const m of materials) {
      if (!m.aoMap) continue;
      out.withAo += 1;
      if (m.userData?.chiWallRelief) out.wallRelief += 1;
      else if (m.userData?.chiRoofRelief) out.roofRelief += 1;
      else if (byMap.get(m.aoMap.uuid) === 1) out.ownAtlas += 1;
      else out.sharedOther += 1;
    }
    return out;
  });
} finally {
  await browser.close();
  server.close();
}

console.log(`AO batches — source tree · ${VIEWPORT} ${SIZE.width}x${SIZE.height}`);
console.log(`  structure batches          ${reading.batches}`);
console.log(`  …carrying an aoMap         ${reading.withAo}  (${reading.distinctAoMaps} distinct maps)`);
console.log(`    wall relief (shared)     ${reading.wallRelief}`);
console.log(`    roof relief (shared)     ${reading.roofRelief}`);
console.log(`    a map no other batch has ${reading.ownAtlas}`);
console.log(`    some other shared map    ${reading.sharedOther}`);
if (errors.length) console.log(`  page errors: ${errors.length}\n    ${errors.slice(0, 5).join('\n    ')}`);
if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify({ viewport: VIEWPORT, ...reading, errors }, null, 2));
process.exit(errors.length ? 1 : 0);
