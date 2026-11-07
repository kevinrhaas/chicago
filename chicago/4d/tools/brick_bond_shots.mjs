/**
 * brick_bond_shots.mjs — before/after stills of the K03 brick walls (T-3295).
 *   node tools/brick_bond_shots.mjs [root] [entry] [out] [--viewport desktop|mobile|both]
 *                                   [--detail full|balanced|light]
 * The front-yard rig (`front_yard_shots.mjs`): the published page, the clock held, the chrome
 * hidden, `walker.teleport` to fixed stands. AFTER is as published; BEFORE is the same page
 * with `?bricks=tiled`, the panel repeated as it was. Stands: the owner's own spot (Dent's
 * north flank from 1825 Prairie, looking south, close), the same flank obliquely, and
 * the 1800 block's east side from the walk. `stats()` is read at both, so any cost shows.
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
const ROOT = path.resolve(positional[0] ?? path.join(HERE, '..', '..', '..', 'site', '4d'));
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
look('owner-1825-flank', [1426.0, -3276.5], [1426.0, -3290.0], 10);
look('flank-oblique', [1414.0, -3273.0], [1434.0, -3283.0], 8);
look('block-1800-east', [1404.0, -3236.0], [1428.0, -3262.0], -6);

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
    await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}-${phase}.jpg`), type: 'jpeg', quality: 86 });
    rows.push({ stand: t.name, triangles: stats?.triangles, drawCalls: stats?.drawCalls, textures: stats?.textures, programs: stats?.programs, brickBond: stats?.brickBond });
  }
  await page.close();
  return { problems, stands: rows, errors };
}

const report = { entry: ENTRY, detail: DETAIL, stands, viewports: {} };
for (const vp of WANT_VP) {
  report.viewports[vp] = { after: await shoot(vp, 'after'), before: await shoot(vp, 'before') };
}
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
for (const [vp, r] of Object.entries(report.viewports)) {
  for (const [i, a] of r.after.stands.entries()) {
    const b = r.before.stands[i];
    console.log(`${vp} ${a.stand}: triangles ${b.triangles} -> ${a.triangles}, calls ${b.drawCalls} -> ${a.drawCalls}`
      + `, textures ${b.textures} -> ${a.textures}`);
  }
  console.log(`${vp}: page errors after ${r.after.errors.length}, before ${r.before.errors.length}; problems ${JSON.stringify(r.after.problems)}`);
  for (const e of [...r.after.errors, ...r.before.errors]) console.log(`  ${e}`);
}
await browser.close();
server.close();
const bad = Object.values(report.viewports).some((r) => r.after.errors.length || r.after.problems.length);
process.exit(bad ? 1 : 0);
