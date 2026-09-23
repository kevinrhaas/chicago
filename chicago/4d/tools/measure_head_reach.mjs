/**
 * Where the woody layer's flowers actually stand — ROADMAP K45(c).
 *
 * K44 measured that two recorded July inflorescences draw no head, and K45(c)
 * drew them. That settles ROUTING, which is all `tools/measure_flora_reach.py`
 * asks: the record reaches a reader and the reader has an archetype for its
 * shape. It does NOT settle whether a visitor is ever near one, and those are
 * different claims — the same distinction K44 drew between a figure being read
 * and a figure reaching a vertex, one step further along.
 *
 * So this asks the last question in the chain: **how far is the nearest
 * flowering stem from each of the scene's own committed anchors?** The answer
 * on the build this was written against is 269 m at the nearest anchor, which
 * is 0.28 px of flower — the bloom is in the scene, correctly, and no anchor
 * looks at it. That is a fact about where the mesic pocket falls on the
 * modelled ground, not a fault in the head path, and it is recorded rather than
 * discovered later by somebody who expected to see a flowering basswood.
 *
 * NOT in `tools/check.sh`, deliberately: it drives a real browser and costs
 * about forty seconds, against a gate that holds itself to ~90 s in total. It
 * is a measurement to be re-run and quoted, in the shape of
 * `tools/measure_shipped_batches.mjs`.
 *
 *   node tools/measure_head_reach.mjs              the published mirror
 *   node tools/measure_head_reach.mjs --source     the source tree
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = process.argv.includes('--source');
const ROOT = SOURCE ? path.join(APP, 'renderers/web')
  : path.resolve(APP, '../../site/chicago/4d');
const PORT = Number(process.env.HEAD_REACH_PORT || 4291);

/** The eye height the walker stands at, and this file's own field of view, both
 *  copied from the renderer for the one arithmetic step below. */
const PX_PER_RAD = 800 / (55 * Math.PI / 180);

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.glb': 'model/gltf-binary', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.bin': 'application/octet-stream', '.md': 'text/markdown',
  '.webp': 'image/webp', '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); res.end('not here'); return;
  }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] ?? 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));

const { chromium } = await import('playwright');
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}/walk/?year=1835`);
await page.waitForFunction(() => window.__chicago4d?.ready === true, { timeout: 60000 });

const s = await page.evaluate(() => {
  const t = window.__chicago4d.trees;
  return {
    trees: t.stats.trees, thickets: t.stats.thickets,
    triangles: t.stats.triangles, drawCalls: t.stats.drawCalls,
    communities: t.stats.communities, species: t.stats.species,
    headSpecies: t.stats.headSpecies, headStems: t.stats.headStems,
    heads: t.stats.heads, headStations: t.stats.headStations,
    anchors: (window.__chicago4d.scene?.anchors ?? [])
      .map((a) => ({ id: a.id, e: a.local_e, n: a.local_n })),
    problems: (window.__chicago4d.problems ?? []).filter((p) => p.startsWith('trees:')),
  };
});
await browser.close();
server.close();

console.log(`${SOURCE ? 'SOURCE tree' : 'PUBLISHED mirror'}: ${s.trees} tree(s) and `
  + `${s.thickets} thicket(s), ${s.triangles} triangle(s) in ${s.drawCalls} draw call(s)`);
console.log(`  communities: ${Object.entries(s.communities)
  .map(([k, v]) => `${k} ${v}`).join(', ')}`);
console.log(`  ${s.headStems} stem(s) of ${s.trees} carry a drawn July inflorescence `
  + `(${s.headSpecies.join(', ') || 'none'}), ${s.heads} head(s) in all`);
for (const p of s.problems) console.log(`  problem: ${p}`);

if (!s.headStations.length) {
  console.log('  no flowering stem stands in the scene — nothing to measure a range to');
} else {
  const counts = {};
  for (const h of s.headStations) counts[h.id] = (counts[h.id] ?? 0) + 1;
  console.log(`  by species: ${Object.entries(counts)
    .map(([k, v]) => `${k} ${v}`).join(', ')}`);
  console.log('  nearest flowering stem to each committed scene anchor:');
  let worst = 0;
  let best = Infinity;
  for (const a of s.anchors) {
    if (typeof a.e !== 'number' || typeof a.n !== 'number') continue;
    let d = Infinity;
    let who = null;
    for (const h of s.headStations) {
      const r = Math.hypot(h.e - a.e, h.n - a.n);
      if (r < d) { d = r; who = h.id; }
    }
    // One 0.09 m inflorescence — the midpoint of both records' size_m — at that
    // range, in pixels of a 55-degree vertical field.
    const px = (0.09 / d) * PX_PER_RAD;
    console.log(`    ${a.id.padEnd(20)}${d.toFixed(1).padStart(8)} m  `
      + `${px.toFixed(2).padStart(6)} px  ${who}`);
    worst = Math.max(worst, d);
    best = Math.min(best, d);
  }
  console.log(`  nearest anchor to any flower: ${best.toFixed(1)} m; farthest: `
    + `${worst.toFixed(1)} m`);
}
if (pageErrors.length) {
  console.log(`  ${pageErrors.length} page error(s): ${pageErrors[0]}`);
  process.exit(1);
}
