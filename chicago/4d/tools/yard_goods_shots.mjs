/**
 * yard_goods_shots.mjs — before/after captures of the yard goods (T-2121).
 *
 *   node tools/yard_goods_shots.mjs [root] [entry] [out] [--viewport desktop|mobile|both]
 *                                   [--base origin/dev] [--detail full|balanced|light]
 *
 *   root   the directory to serve (default `../../site/4d`, the published mirror)
 *   entry  the page under it (default `/walk/`)
 *   out    where the frames and report.json go (default /tmp/yard-goods-shots)
 *
 * The same rig as `woodpile_shots.mjs`: a static server, the published page, the clock
 * held, the chrome hidden, `walker.teleport` to stands derived from the records. Each
 * stand is shot AFTER, as published, and BEFORE — the same page with `yard.js` and
 * `frontage.js` served as they stand on `--base` (default origin/dev), so the only
 * difference between the two frames is this layer's code.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync, readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = execSync('npm root -g').toString().trim();
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FLAGS = new Set(['--viewport', '--detail', '--base', '--only']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0] ?? path.join(HERE, '..', '..', '..', 'site', '4d'));
const ENTRY = positional[1] ?? '/walk/';
const OUT = path.resolve(positional[2] ?? '/tmp/yard-goods-shots');
const DETAIL = flags['--detail'] ?? 'full';
const BASE_REF = flags['--base'] ?? 'origin/dev';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'desktop') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport'] ?? 'desktop'];
mkdirSync(OUT, { recursive: true });

const before = {};
for (const f of ['yard.js', 'frontage.js']) {
  before[f] = execSync(`git show ${BASE_REF}:chicago/4d/renderers/web/js/${f}`,
    { cwd: HERE, maxBuffer: 64 << 20 }).toString();
}

const DATA = path.join(HERE, '..', 'data', 'yard');
const goods = JSON.parse(readFileSync(path.join(DATA, 'town_trade_goods.json'), 'utf8'));
const yards = JSON.parse(readFileSync(path.join(DATA, 'town_trade_yards.json'), 'utf8'));
const compass = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const stands = [];
/** Stand `d` metres out from a row of things, `s` along it, looking at its middle. */
function standAt(name, items, d, s, pitch) {
  const e0 = items.reduce((a, it) => a + it.at_local_enu_m[0], 0) / items.length;
  const n0 = items.reduce((a, it) => a + it.at_local_enu_m[1], 0) / items.length;
  const b = ((items[0].bearing_deg ?? 0) * Math.PI) / 180;
  const along = [Math.cos(b), -Math.sin(b)];
  const out = [Math.sin(b), Math.cos(b)];
  const e = e0 + out[0] * d + along[0] * s;
  const n = n0 + out[1] * d + along[1] * s;
  stands.push({ name, local_e: e, local_n: n, yaw_deg: compass(e0 - e, n0 - n),
    pitch_deg: pitch });
}
const front = (id) => goods.frontages.find((f) => f.structure_id === id).items;
const lot = (id) => yards.lots.find((l) => l.structure_id === id).items
  .filter((it) => it.kind === 'barrel');
standAt('cooperage-rank', lot('inf_cooperage_south'), 3.2, 1.2, -18);
standAt('cooperage-close', lot('inf_cooperage_south').slice(0, 2), 1.5, 0.3, -30);
standAt('packing-house-rank', lot('newberry_dole_packing_house_south_branch'), 3.6, -1.5, -16);
standAt('coffee-house-goods', front('exchange_coffee_house'), 3.4, -0.8, -14);
standAt('auction-room-goods', front('bates_auction_room'), 3.4, 0.5, -12);
const wagon = (id) => goods.wagons.find((w) => w.id === id);
const pairStand = (name, ids, d, pitch) => {
  const ws = ids.map(wagon);
  const e0 = ws.reduce((a, w) => a + w.at_local_enu_m[0], 0) / ws.length;
  const n0 = ws.reduce((a, w) => a + w.at_local_enu_m[1], 0) / ws.length;
  const b = ((ws[0].bearing_deg ?? 0) * Math.PI) / 180 + Math.PI / 2.6;
  const e = e0 + Math.sin(b) * d;
  const n = n0 + Math.cos(b) * d;
  stands.push({ name, local_e: e, local_n: n, yaw_deg: compass(e0 - e, n0 - n), pitch_deg: pitch });
};
pairStand('green-tree-wagons', ['green_tree_tavern_yard_wagon_1', 'green_tree_tavern_yard_wagon_2',
  'green_tree_tavern_shed_wagon'], 7, -18);
pairStand('wolf-point-wagons', ['town_wagon_wolf_point_tavern_yard_1',
  'town_wagon_wolf_point_tavern_yard_2', 'town_wagon_wolf_point_tavern_yard_3'], 9, -16);
const carts = goods.wagons.filter((w) => w.kind === 'cart').slice(0, 2);
carts.forEach((c, i) => pairStand(`cart-${i + 1}`, [c.id], 4.5, -12));
const only = flags['--only'] ? new Set(flags['--only'].split(',')) : null;
const shots = only ? stands.filter((s) => only.has(s.name)) : stands;

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ktx2': 'image/ktx2',
  '.geojson': 'application/json', '.webmanifest': 'application/manifest+json',
};
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  try {
    if (file.endsWith('/')) file = path.join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404).end('nope');
  }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
});

async function shoot(vp, phase) {
  const page = await browser.newPage({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  if (phase === 'before') {
    for (const f of Object.keys(before)) {
      await page.route(`**/js/${f}*`, (route) => route.fulfill({
        status: 200, contentType: 'text/javascript', body: before[f] }));
    }
  }
  await page.addInitScript((d) => {
    localStorage.setItem('chicago4d.detail', d);
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  page.setDefaultTimeout(240000);
  await page.goto(`${base}${ENTRY}?year=1835`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
    }
  });
  await page.waitForTimeout(600);
  await page.evaluate(() => {
    window.__chicago4d.setAnimationHold?.(true);
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
    document.head.appendChild(style);
  });
  const census = await page.evaluate(() => {
    const y = window.__chicago4d.yard;
    let tris = 0;
    y?.group?.traverse((o) => {
      if (o.isMesh && !o.userData.farMerged) tris += (o.geometry.attributes.position.count / 3);
    });
    return { census: y?.group?.userData?.census ?? null, yardTriangles: tris,
      heap: performance.memory?.usedJSHeapSize ?? null,
      problems: (window.__chicago4d.problems ?? []).filter((p) => /yard|frontage/.test(p)) };
  });
  const rows = [];
  for (const t of shots) {
    await page.evaluate((s) => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport(s);
    }, t);
    await page.waitForTimeout(1500);
    const stats = await page.evaluate(() => window.__chicago4d.stats?.() ?? null);
    await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}-${phase}.jpg`),
      type: 'jpeg', quality: 88 });
    rows.push({ stand: t.name, triangles: stats?.triangles, drawCalls: stats?.drawCalls });
  }
  await page.close();
  return { ...census, stands: rows, errors };
}

const report = { entry: ENTRY, detail: DETAIL, base: BASE_REF, stands: shots, viewports: {} };
for (const vp of WANT_VP) {
  report.viewports[vp] = { after: await shoot(vp, 'after'), before: await shoot(vp, 'before') };
}
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
for (const [vp, r] of Object.entries(report.viewports)) {
  console.log(`${vp}: errors after ${r.after.errors.length}, before ${r.before.errors.length}; `
    + `yard triangles ${r.before.yardTriangles} -> ${r.after.yardTriangles}; `
    + `relief ${r.after.census?.relief}; chunks ${r.before.census?.chunks} -> ${r.after.census?.chunks}`);
  r.after.stands.forEach((s, i) => {
    const bf = r.before.stands[i];
    console.log(`  ${s.stand.padEnd(22)} tris ${bf.triangles} -> ${s.triangles}  `
      + `calls ${bf.drawCalls} -> ${s.drawCalls}`);
  });
  if (r.after.errors.length) console.log('  pageerrors:', r.after.errors.slice(0, 3));
  if (r.after.problems.length) console.log('  problems:', r.after.problems.slice(0, 5));
}
await browser.close();
server.close();
