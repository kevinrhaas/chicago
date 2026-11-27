/**
 * front_yard_shots.mjs — before/after stills of the 1904 front yards (T-3203).
 *   node tools/front_yard_shots.mjs [root] [entry] [out] [--viewport desktop|mobile|both]
 *                                   [--detail full|balanced|light]
 * The kept-ground rig (`lot_remnant_shots.mjs`): the published page, the clock held, the
 * chrome hidden, `walker.teleport` to fixed stands on Prairie Avenue. AFTER is as published;
 * BEFORE is the same page with `front_yards` taken out of the 1904 scene's layers at the
 * network. `stats()` and the layer's own counts are read at both, so the cost is a
 * difference at one pose. The stands: Prairie at 18th looking north up the east side, the
 * Pullman house from the west walk, the 1600 block's west side, and the 1800 block's east.
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
const FLAGS = new Set(['--viewport', '--detail', '--block', '--layers', '--phase', '--stands']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0] ?? path.join(HERE, '..', '..', '..', 'site', '4d'));
const ENTRY = positional[1] ?? '/walk/';
const OUT = path.resolve(positional[2] ?? '/tmp/front-yard-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

const compass = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const stands = [];
const look = (name, from, to, pitch) => stands.push({ name, local_e: from[0], local_n: from[1],
  yaw_deg: compass(to[0] - from[0], to[1] - from[1]), pitch_deg: pitch });
// T-3786: `--block 20th-22nd` walks the 20th-22nd block instead: its fronts from the street, each
// back yard the second look gave a kitchen door (and 2000's, laid by T-3785) from 9 m out in the
// yard square to the door, and a walk down the middle of Prairie from 20th to 22nd read every 20 m
// (`walk: true` stands take the cost and no still). The coordinates are data/front_yards/1904.json's
// lot frames and data/back_yards/1904.json's doors.
const BLOCK = flags['--block'] ?? null;
if (BLOCK === '20th-22nd') {
  look('w-2000-2010-from-20th', [1408.0, -3480.0], [1385.0, -3505.0], -6);
  look('w-2010-2018', [1408.0, -3522.0], [1384.0, -3506.0], -6);
  look('e-2003-from-20th', [1402.0, -3480.0], [1428.0, -3494.0], -6);
  look('w-2130', [1408.0, -3696.0], [1386.0, -3712.0], -6);
  look('rear-2000', [1352.5, -3490.1], [1361.51, -3489.97], -8);
  look('rear-2010', [1355.3, -3519.7], [1364.31, -3519.62], -8);
  look('rear-2003', [1461.7, -3491.6], [1452.69, -3491.71], -8);
  look('rear-2130', [1350.8, -3710.1], [1359.77, -3709.97], -8);
  for (let n = -3478; n >= -3722; n -= 20) {
    stands.push({ name: `walk-${-n}`, local_e: 1405.0, local_n: n, yaw_deg: 180, pitch_deg: -3, walk: true });
  }
} else {
  look('prairie-at-18th', [1409.0, -3203.0], [1428.0, -3168.0], -5);
  look('pullman', [1396.0, -3190.0], [1432.0, -3170.0], -6);
  look('block-1600-west', [1404.0, -2992.0], [1378.0, -2972.0], -6);
  look('block-1800-east', [1404.0, -3236.0], [1428.0, -3262.0], -6);
}
// the layers BEFORE takes out of the 1904 scene (the front yards alone, by default)
const DROP = (flags['--layers'] ?? 'front_yards').split(',').filter(Boolean);
// T-3786: one phase, or a few stands, a call: on the runner's CPU renderer a stand on the
// 20th-22nd block streams for about a minute, so the whole walk does not fit one 600 s call.
// The report is written after every stand, so a run cut off at the ceiling keeps what it read.
const PHASES = (flags['--phase'] ?? 'both') === 'both' ? ['after', 'before'] : [flags['--phase']];
const ONLY = (flags['--stands'] ?? '').split(',').filter(Boolean);
if (ONLY.length) stands.splice(0, stands.length, ...stands.filter((t) => ONLY.some((o) => t.name.startsWith(o))));

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

async function shoot(vp, phase, onStand = () => {}) {
  const page = await browser.newPage({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  if (phase === 'before') {
    await page.route('**/scenes/1904.json', async (route) => {
      const res = await route.fetch();
      const scene = await res.json();
      scene.layers = scene.layers.filter((l) => !DROP.includes(l));
      await route.fulfill({ response: res, json: scene });
    });
  }
  await page.addInitScript((d) => {
    localStorage.setItem('chicago4d.detail', d);
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  page.setDefaultTimeout(240000);
  await page.goto(`${base}${ENTRY}?year=1904`, { waitUntil: 'load' });
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
  const problems = await page.evaluate(() => (window.__chicago4d.problems ?? []).filter((p) => /front yard/i.test(p)));
  const rows = [];
  for (const t of stands) {
    await page.evaluate((s) => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport(s);
    }, t);
    await page.waitForTimeout(t.walk ? 700 : 1500);
    const stats = await page.evaluate(() => window.__chicago4d.stats?.() ?? null);
    const yards = await page.evaluate(() => ({ ...(window.__chicago4d.frontYards?.stats ?? {}) }));
    if (!t.walk) await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}-${phase}.jpg`), type: 'jpeg', quality: 86 });
    rows.push({ stand: t.name, triangles: stats?.triangles, drawCalls: stats?.drawCalls, yards });
    await onStand({ problems, stands: rows, errors });
  }
  await page.close();
  return { problems, stands: rows, errors };
}

const report = { entry: ENTRY, detail: DETAIL, block: BLOCK, before_drops: DROP, stands, viewports: {} };
const save = () => writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
for (const vp of WANT_VP) {
  report.viewports[vp] = {};
  for (const ph of PHASES) {
    report.viewports[vp][ph] = await shoot(vp, ph, async (partial) => { report.viewports[vp][ph] = partial; await save(); });
  }
}
await save();
const none = { stands: [], errors: [], problems: [] };
for (const [vp, r] of Object.entries(report.viewports)) {
  const after = r.after ?? none, before = r.before ?? none;
  for (const [i, a] of after.stands.entries()) {
    const b = before.stands[i];
    console.log(`${vp} ${a.stand}: triangles ${b ? `${b.triangles} -> ` : ''}${a.triangles}, calls `
      + `${b ? `${b.drawCalls} -> ` : ''}${a.drawCalls} · yard near ${a.yards.near} far ${a.yards.far} plants ${a.yards.plants}`);
  }
  if (!r.after) for (const b of before.stands) console.log(`${vp} ${b.stand} (before): triangles ${b.triangles}, calls ${b.drawCalls}`);
  console.log(`${vp}: page errors after ${after.errors.length}, before ${before.errors.length}; problems ${JSON.stringify(after.problems)}`);
  for (const e of [...after.errors, ...before.errors]) console.log(`  ${e}`);
}
await browser.close();
server.close();
const bad = Object.values(report.viewports).some((r) => [r.after, r.before].some((x) => x && (x.errors.length || x.problems.length)));
process.exit(bad ? 1 : 0);
