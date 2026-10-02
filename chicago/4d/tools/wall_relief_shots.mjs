/**
 * wall_relief_shots.mjs — the walls' relief (T-1963), before and after, in the town.
 *
 *   node tools/wall_relief_shots.mjs                      both viewports, every shot
 *   node tools/wall_relief_shots.mjs --viewport mobile    one viewport, while iterating
 *   node tools/wall_relief_shots.mjs --out DIR            default /tmp/wall-relief
 *   node tools/wall_relief_shots.mjs --root DIR           the published root (default ../../site)
 *
 * Serves the PUBLISHED mirror (run ./tools/publish.sh first) and shoots, at 390x780
 * and 1280x800, the town with `?walls=flat` (before: every wall the flat colour it
 * was) and without it (after), with the animation clock held:
 *
 *   close-fresh       a fresh-timber frame dwelling        recon_1835_blk_lake_market_d4_02
 *   close-maintained  a whitewashed frame dwelling          recon_1835_blk_lake_market_d3_03
 *   close-whitelead   the Sauganash, the one painted wall   sauganash_hotel
 *   close-weathered   a weathered-timber storefront         recon_1835_blk_lake_market_c2_01
 *   close-log         a hewn-log shop                       philo_carpenter_log_shop
 *   wide-lake_market, wide-south_water   the critic stations, with frame costs
 *
 * and Glessner v4's 1904 default from its own arrival, the benchmark. Each close
 * shot arrives the way a visitor does (`spawnAtDestination`) and then steps in
 * along the line of sight until the wall is CLOSE_M away, so the pair frames the
 * same wall at walking distance. Writes JPEGs and `review.json` (draw calls,
 * triangles, textures and the bound substrates per shot); exits 1 on any page error.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); } catch {
    const root = execSync('npm root -g').toString().trim();
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const flag = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const ROOT = path.resolve(flag('--root', path.join(HERE, '..', '..', '..', 'site')));
const OUT = path.resolve(flag('--out', '/tmp/wall-relief'));
const ONLY = flag('--viewport', null);
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = { mobile: { width: 390, height: 780 }, desktop: { width: 1280, height: 800 } };
/** How far from the wall a close shot stands: walking distance, a door's width off the step. */
const CLOSE_M = 5.0;
const CLOSE = [
  ['close-fresh', 'recon_1835_blk_lake_market_d4_02'],
  ['close-maintained', 'recon_1835_blk_lake_market_d3_03'],
  ['close-whitelead', 'sauganash_hotel'],
  ['close-weathered', 'recon_1835_blk_lake_market_c2_01'],
  ['close-log', 'philo_carpenter_log_shop'],
];
const WIDE = ['lake_market', 'south_water'];

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
  '.bin': 'application/octet-stream', '.webp': 'image/webp' };
const server = createServer(async (req, res) => {
  try {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const file = path.join(ROOT, p);
    if (!file.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'] });
const errors = [];
const review = { close_m: CLOSE_M, shots: [] };

async function boot(vp, query) {
  const ctx = await browser.newContext({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1,
    hasTouch: vp === 'mobile', isMobile: vp === 'mobile' });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errors.push(`${vp} ${query}: ${e}`));
  await page.addInitScript(() => {
    localStorage.setItem('chicago4d.entered', '1');
  });
  page.setDefaultTimeout(240000);
  await page.goto(`${base}/4d/?${query}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it|^\s*(tap to )?enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
    }
  });
  await page.waitForTimeout(800);
  await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
  return { ctx, page };
}

/** Two frames, then the renderer's own reading of the last one. */
async function settle(page) {
  await page.waitForTimeout(1500);
  return page.evaluate(() => new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const s = window.__chicago4d.stats();
      resolve({ drawCalls: s.drawCalls, triangles: s.triangles, textures: s.textures,
        programs: s.programs, batches: s.batches, wallRelief: s.wallRelief });
    }));
  }));
}

async function shoot(page, vp, mode, name, extra = {}) {
  const stats = await settle(page);
  const file = `${vp}-${name}-${mode}.jpg`;
  await page.screenshot({ path: path.join(OUT, file), type: 'jpeg', quality: 86 });
  review.shots.push({ viewport: vp, mode, shot: name, file, ...stats, ...extra });
  console.log(`  ${file}: ${stats.drawCalls} calls, ${stats.triangles} tris, ${stats.batches} batches`);
}

for (const vp of Object.keys(VIEWPORTS)) {
  if (ONLY && ONLY !== vp) continue;
  for (const mode of ['before', 'after']) {
    const { ctx, page } = await boot(vp, `year=1835${mode === 'before' ? '&walls=flat' : ''}`);
    for (const [name, id] of CLOSE) {
      const ok = await page.evaluate((sid) => window.__chicago4d.spawnAtDestination({ kind: 'structure', id: sid }), id);
      await page.waitForTimeout(1200);
      // Step in along the line of sight until the wall the centre ray meets is CLOSE_M off.
      const stood = await page.evaluate(({ sid, close }) => {
        const api = window.__chicago4d;
        const hit = api.buildings.pickAt(null, api.camera);
        const st = api.walker.state;
        if (!hit) return { hit: null };
        const step = Math.max(0, hit.distance - close);
        const bearing = api.walker.bearingDeg;
        const yaw = bearing * Math.PI / 180;
        // The walker's yaw is a compass bearing: 0 north (+n), 90 east (+e).
        const e = st.e + Math.sin(yaw) * step;
        const n = st.n + Math.cos(yaw) * step;
        api.walker.teleport({ local_e: e, local_n: n, yaw_deg: bearing });
        return { hit: hit.id, wanted: sid, from_m: Number(hit.distance.toFixed(2)), step_m: Number(step.toFixed(2)) };
      }, { sid: id, close: CLOSE_M });
      await shoot(page, vp, mode, name, { structure: id, arrived: ok, stood });
    }
    for (const anchor of WIDE) {
      await page.evaluate((a) => window.__chicago4d.goTo(a), anchor);
      await shoot(page, vp, mode, `wide-${anchor}`, { anchor });
    }
    await ctx.close();
  }
  // The benchmark, from its own arrival, in its own year.
  const { ctx, page } = await boot(vp, 'year=1904');
  await page.evaluate(() => window.__chicago4d.spawnAtDestination({ kind: 'structure', id: 'glessner_house' }));
  await page.waitForTimeout(1500);
  await shoot(page, vp, 'benchmark', 'glessner', { structure: 'glessner_house' });
  await ctx.close();
}

await writeFile(path.join(OUT, ONLY ? `review-${ONLY}.json` : 'review.json'), JSON.stringify({ ...review, errors }, null, 2));
await browser.close();
server.close();
if (errors.length) { console.log(errors.slice(0, 10).join('\n')); process.exit(1); }
console.log(`wrote ${review.shots.length} shots to ${OUT}`);
