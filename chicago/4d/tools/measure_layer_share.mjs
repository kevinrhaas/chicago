/**
 * WHOSE TRIANGLES ARE THEY? THE FRAME, BROKEN DOWN BY SCENE LAYER (T-1244).
 *
 *   node tools/measure_layer_share.mjs [--source] [--tiers full,light]
 *                                      [--only desktop|mobile] [--json out.json]
 *
 * `tools/measure_detail_ceilings.mjs` says whether a stand is over its ceiling.
 * It cannot say what put it there, and on 2026-09-15 that was the whole of the
 * next question: T-1154 found the five downtown stands over every tier at both
 * viewports and had nine days of commits to look through, none of which says in
 * its title how many triangles it added to a frame at Lake and Market.
 *
 * So: the same published mirror, the same renderer, the same `renderer.info`
 * three counts with — and one layer hidden at a time. `scene3d`'s named children
 * ARE the layers (`terrain`, `trees`, `structures`, `frontage`, `enclosures`,
 * `streets`, `flora`, `yard`, `signage`, …), so the drop in the frame's triangle
 * count when one of them is made invisible is exactly that layer's share of it,
 * as the renderer counts it and including whatever batching and culling it does
 * for itself. That last part is why this is a subtraction rather than a walk of
 * the scene graph: a `BatchedMesh` submits a subset of its chunks through one
 * multi-draw, so counting its geometry would report the whole wood at every
 * stand — which is what a first attempt did, and it was wrong by 333,393
 * triangles at the aerial.
 *
 * The figures are the GATE's, not a second opinion: the numbers this prints for
 * the whole frame are the ones `tools/measure_detail_ceilings.mjs` prints for the
 * same stand at the same tier, to the triangle.
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
const ROOT4D = path.resolve(HERE, '..');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const wantSource = process.argv.includes('--source');
const jsonOut = argAt('--json');
const ONLY = argAt('--only') || 'desktop';
const TIERS = (argAt('--tiers') || 'full,light').split(',');
const YEAR = process.env.DETAIL_YEAR || '1835';

// COPIED from tools/measure_detail_ceilings.mjs, which copies them from the
// smoke, for the reason given there: the set is owned in one place and a stand
// added there and not here makes this tool less complete, never wrong.
const STANDS = [
  { id: 'lake_at_canal', target: 'green_tree', label: 'Lake Street at Canal, east down the axis' },
  { id: 'lake_and_market', target: 'lake_market', label: 'Lake and Market' },
  { id: 'the_forks', target: 'forks', label: 'the forks, from Wolf Point' },
  { id: 'from_above', target: 'from_above', label: 'the open aerial', aerial: true },
];
const VIEWPORTS = [
  { label: 'desktop 1280x800', width: 1280, height: 800 },
  { label: 'mobile 390x780', width: 390, height: 780 },
].filter((v) => ONLY === 'both' || v.label.startsWith(ONLY));

const root = wantSource
  ? path.join(ROOT4D, 'renderers/web')
  : path.resolve(ROOT4D, '../../site/chicago/4d');
const entry = wantSource ? '/index.html' : '/walk/index.html';
if (!fs.existsSync(root)) {
  console.error(`no tree at ${root}${wantSource ? '' : ' — run tools/publish.sh first'}`);
  process.exit(2);
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(root, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(root) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
const PORT = 8123;
await new Promise((r) => server.listen(PORT, r));

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
});
const passes = [];
for (const vp of VIEWPORTS) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${PORT}${entry}?year=${YEAR}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300_000 });
  const seen = await page.evaluate(async ({ stands, tiers }) => {
    const a = window.__chicago4d;
    const settle = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    // The sky is excluded: it is two triangles and it is not a layer of the town.
    const layers = a.scene3d.children.filter((c) => c.name && c.name !== 'sky');
    const rows = [];
    for (const level of tiers) {
      await a.setDetail(level);
      await settle();
      for (const st of stands) {
        a.setFly(!!st.aerial);
        a.goTo(st.target);
        await settle(); await settle();
        const whole = a.stats();
        const by = {};
        for (const layer of layers) {
          if (!layer.visible) continue;
          layer.visible = false;
          await settle();
          const share = whole.triangles - a.stats().triangles;
          layer.visible = true;
          if (share) by[layer.name] = share;
        }
        await settle();
        rows.push({ level, stand: st.id, label: st.label,
                    triangles: whole.triangles, calls: whole.drawCalls,
                    ceiling: a.detailLevels[level].triangles, by });
      }
    }
    return rows;
  }, { stands: STANDS, tiers: TIERS });
  passes.push({ viewport: vp.label, seen, errors });
  await page.close();
}
await browser.close();
server.close();

let bad = 0;
for (const pass of passes) {
  console.log(`\n================  ${pass.viewport}  ================`);
  for (const e of pass.errors) { bad++; console.log(`  PAGEERROR  ${e}`); }
  for (const row of pass.seen) {
    const over = row.triangles > row.ceiling;
    console.log(`\n${row.level}  ${row.label}  ${row.triangles.toLocaleString()} triangles, `
      + `${row.calls} calls  — ${over ? `OVER ${row.ceiling.toLocaleString()}` : 'inside the ceiling'}`);
    for (const [name, share] of Object.entries(row.by).sort((x, y) => y[1] - x[1])) {
      console.log(`   ${name.padEnd(16)} ${String(share.toLocaleString()).padStart(11)}`
        + `  ${(100 * share / row.triangles).toFixed(1).padStart(5)}%`);
    }
  }
}
if (jsonOut) {
  fs.writeFileSync(jsonOut, `${JSON.stringify({ tree: wantSource ? 'source' : 'published',
    year: YEAR, passes }, null, 2)}\n`);
  console.log(`\nwritten ${jsonOut}`);
}
process.exit(bad ? 1 : 0);
