/**
 * street_dress_shots_1871.mjs — the fixed stands T-3805 judges the 1871 street furniture
 * round the jaunt stops from (fire-alarm boxes, hydrants, the Lake Street telegraph poles,
 * the goods on the walks, the barbers' poles and the tobacconists' figures).
 *
 *   node tools/street_dress_shots_1871.mjs <site-root> <out-dir> [--label before|after]
 *        [--viewport desktop|mobile|both] [--detail full|balanced|light] [--stands a,b]
 *        [--before-from DIR]
 *
 * `--before-from DIR` serves DIR/street-furniture.js and DIR/1871.json (the base branch's
 * renderer and data file, from `git show`) in place of the published ones, so a BEFORE
 * frame can be shot from the same published mirror as the AFTER one.
 *
 * A diagnostic, not a gate. It serves a PUBLISHED mirror (`tools/publish.sh` writes
 * site/4d), opens the 1871 scene, holds the animation clock and hides the HUD the way
 * critic_shots.mjs does, and stands at the ten stands below, each a jaunt stop's own
 * anchor or a walk-level stand beside it, so a before and an after are the same pose by
 * construction. 1280x800 and 390x780 at device scale 1. It prints the renderer's own
 * stats and the street-furniture layer's at every stand, which is the cost a review
 * compares.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';

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

const FLAGS = new Set(['--viewport', '--detail', '--stands', '--label', '--before-from']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0] ?? 'site');
const OUT = path.resolve(positional[1] ?? '/tmp/street-dress-1871');
const LABEL = flags['--label'] ?? 'after';
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both' ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

// Each stand: a jaunt stop's anchor (data/scenes/1871.json) or a walk-level stand by it.
const STANDS = [
  { name: 'lake-and-clark', local_e: 585, local_n: -110, yaw_deg: 90, pitch_deg: 2 },
  { name: 'court-house-square', local_e: 592, local_n: -330, yaw_deg: 270, pitch_deg: 2 },
  { name: 'state-and-washington', local_e: 832, local_n: -402, yaw_deg: 38.7, pitch_deg: 2 },
  { name: 'washington-at-crosbys', local_e: 777, local_n: -405, yaw_deg: 0, pitch_deg: 0 },
  { name: 'dearborn-and-madison', local_e: 683, local_n: -497, yaw_deg: 140.9, pitch_deg: 0 },
  { name: 'chicago-ave-at-pine', local_e: 1135, local_n: 1070, yaw_deg: 355, pitch_deg: 2 },
  // Closer, on the walks: the dress at a walker's eye.
  { name: 'lake-street-north-walk', local_e: 592, local_n: -105.5, yaw_deg: 90, pitch_deg: -6 },
  { name: 'court-house-cupola-wires', local_e: 535, local_n: -320, yaw_deg: 244, pitch_deg: 20 },
  { name: 'dearborn-at-madison-walk', local_e: 697.5, local_n: -503, yaw_deg: 180, pitch_deg: -6 },
  { name: 'pine-street-water-works', local_e: 1151, local_n: 1146, yaw_deg: 20, pitch_deg: -3 },
];
const only = flags['--stands'] ? new Set(flags['--stands'].split(',')) : null;
const shots = only ? STANDS.filter((s) => only.has(s.name)) : STANDS;

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.gz': 'application/gzip',
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

const report = { label: LABEL, detail: DETAIL, stands: shots, viewports: {} };
for (const vp of WANT_VP) {
  const page = await browser.newPage({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.addInitScript((d) => {
    // The Sharpness choice lives in the stored settings (main.js readDetailPreference).
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem('chicago4d.settings') || '{}') ?? {}; } catch { /* fresh */ }
    localStorage.setItem('chicago4d.settings', JSON.stringify({ ...saved, detail: d }));
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  if (flags['--before-from']) {
    const dir = path.resolve(flags['--before-from']);
    const js = await readFile(path.join(dir, 'street-furniture.js'));
    const data = await readFile(path.join(dir, '1871.json'));
    await page.route('**/js/street-furniture.js*', (route) => route.fulfill({ status: 200, contentType: 'text/javascript', body: js }));
    await page.route('**/street_furniture/1871.json*', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: data }));
  }
  page.setDefaultTimeout(240000);
  await page.goto(`${base}/4d/walk/?year=1871`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 600000 });
  await page.evaluate(() => {
    window.__chicago4d.welcome?.enter?.();
    for (const b of document.querySelectorAll('button')) {
      if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
    }
  });
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    window.__chicago4d.setAnimationHold?.(true);
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
    document.head.appendChild(style);
  });
  const rows = [];
  for (const t of shots) {
    await page.evaluate((s) => {
      const api = window.__chicago4d;
      api.setFly?.(false);
      api.walker.teleport(s);
    }, t);
    await page.waitForTimeout(4000);
    const stats = await page.evaluate(() => {
      const api = window.__chicago4d;
      const sf = api.streetFurniture?.stats ?? {};
      const s = api.stats?.() ?? {};
      return { detail: api.detail, triangles: s.triangles, drawCalls: s.drawCalls, heapMB: performance.memory ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : null,
        furniture: { drawCalls: sf.drawCalls, triangles: sf.triangles, items: sf.items, dressDrawn: sf.dressDrawn } };
    });
    const file = path.join(OUT, `${t.name}-${vp}-${LABEL}.jpg`);
    await page.screenshot({ path: file, type: 'jpeg', quality: 86, timeout: 240000 });
    rows.push({ stand: t.name, file, ...stats });
    console.log(`${vp} ${t.name} [${stats.detail}]: tris ${stats.triangles} calls ${stats.drawCalls} furniture ${JSON.stringify(stats.furniture)}`);
  }
  report.viewports[vp] = { stands: rows, errors };
  if (errors.length) console.log(`${vp} pageerrors:`, errors.slice(0, 3));
  await page.close();
}
await writeFile(path.join(OUT, `report-${LABEL}-${DETAIL}.json`), JSON.stringify(report, null, 2));
await browser.close();
server.close();
