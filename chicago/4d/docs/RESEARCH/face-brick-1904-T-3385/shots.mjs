/**
 * T-3385: before/after stills of Prairie Avenue's brick fronts, after tools/brick_bond_shots.mjs's rig.
 *   node shots.mjs <site/4d root> /walk/ <out> <phase> [--viewport desktop|mobile|both]
 * Run once on a site published from the branch (phase "after") and once on the same site with
 * the changed web GLBs put back to dev's (phase "before"); the renderer is the same in both.
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
const FLAGS = new Set(['--viewport', '--detail']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0]);
const PHASE = positional[3] ?? 'after';
const ENTRY = positional[1] ?? '/walk/';
const OUT = path.resolve(positional[2] ?? '/tmp/brick-bond-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

const compass = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const stands = [];
const look = (name, from, to, pitch) => stands.push({ name, local_e: from[0], local_n: from[1],
  yaw_deg: compass(to[0] - from[0], to[1] - from[1]), pitch_deg: pitch });
look('west-1600-block', [1397.0, -3018.0], [1378.0, -2978.0], 4);
look('east-1613-1615', [1389.0, -3000.0], [1410.0, -2972.0], 4);
look('field-1905', [1394.0, -3335.0], [1412.0, -3362.0], 6);
look('henderson-1816', [1399.0, -3296.0], [1381.0, -3268.0], 6);
look('west-1700-block', [1398.0, -3185.0], [1380.0, -3150.0], 4);

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
  await page.addInitScript((d) => {
    localStorage.setItem('chicago4d.detail', d);
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  page.setDefaultTimeout(240000);
  await page.goto(`${base}${ENTRY}?year=1904${phase === 'before' ? '&bricks=tiled' : ''}`, { waitUntil: 'load' });
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
  const problems = await page.evaluate(() => (window.__chicago4d.problems ?? []).filter((p) => /brick/i.test(p)));
  const rows = [];
  for (const t of stands) {
    await page.evaluate((s) => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport(s);
    }, t);
    await page.waitForTimeout(2500);
    const stats = await page.evaluate(() => window.__chicago4d.stats?.() ?? null);
    await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}-${PHASE}.jpg`), type: 'jpeg', quality: 86 });
    rows.push({ stand: t.name, triangles: stats?.triangles, drawCalls: stats?.drawCalls, textures: stats?.textures, programs: stats?.programs, brickBond: stats?.brickBond });
  }
  await page.close();
  return { problems, stands: rows, errors };
}

const report = { entry: ENTRY, detail: DETAIL, stands, viewports: {} };
for (const vp of WANT_VP) {
  report.viewports[vp] = { [PHASE]: await shoot(vp, 'after_named') };
}
await writeFile(path.join(OUT, `report-${PHASE}.json`), JSON.stringify(report, null, 2));
await browser.close();
server.close();
