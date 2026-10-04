/**
 * kept_ground_shots.mjs — before/after captures of the kept yards (T-2086).
 *   node tools/kept_ground_shots.mjs [root] [entry] [out] [--viewport desktop|mobile|both]
 *                                    [--detail full|balanced|light]
 *
 * The woodpile rig (`woodpile_shots.mjs`): the published page, the clock held, the chrome
 * hidden, `walker.teleport` to stands derived from the record. AFTER is as published;
 * BEFORE is the same page with `yard/town_kept_ground.json` and
 * `enclosures/town_yard_paths.json` refused at the network, which is the town the two
 * layers degrade to. `stats()` is read at both, so the cost is a difference at one pose.
 * The stands: a house's back yard down its path to the privy, the same yard from its
 * side line, a South Water store's back yard, and the yard's rear corner from its middle.
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
const OUT = path.resolve(positional[2] ?? '/tmp/kept-ground-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

const DATA = path.join(HERE, '..', 'data');
const record = JSON.parse(readFileSync(path.join(DATA, 'yard', 'town_kept_ground.json'), 'utf8'));
const paths = JSON.parse(readFileSync(path.join(DATA, 'enclosures', 'town_yard_paths.json'), 'utf8'));
const compass = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
const rings = paths.ground.interior_local_enu_m;
const stands = [];
const look = (name, from, to, pitch) => stands.push({ name, local_e: from[0], local_n: from[1],
  yaw_deg: compass(to[0] - from[0], to[1] - from[1]), pitch_deg: pitch });
const lengthOf = (r) => Math.hypot(...[0, 1].map((k) => mid(r[2], r[3])[k] - mid(r[0], r[1])[k]));
const privy = paths.paths.map((p, i) => ({ ...p, ring: rings[i] }))
  .filter((p) => p.to.startsWith('privy_') && lengthOf(p.ring) > 9)[0];
const wanted = [privy.lot];
{
  const a = mid(privy.ring[0], privy.ring[1]);
  const b = mid(privy.ring[2], privy.ring[3]);
  const u = [(b[0] - a[0]) / lengthOf(privy.ring), (b[1] - a[1]) / lengthOf(privy.ring)];
  look('backyard', [a[0] + u[0] * 0.8, a[1] + u[1] * 0.8], b, -12);
  const side = [a[0] + u[0] * 4 - u[1] * 7, a[1] + u[1] * 4 + u[0] * 7];
  look('backyard-side', side, [a[0] + u[0] * 5, a[1] + u[1] * 5], -14);
}
const store = record.lots.find((l) => l.lot.startsWith('blk_south_water')
  && l.structures.some((s) => /store|warehouse/.test(s)));
if (store) {
  wanted.push(store.lot);
  const r = store.kept_ring_local_enu_m;
  const c = r.reduce((s, p) => [s[0] + p[0] / r.length, s[1] + p[1] / r.length], [0, 0]);
  const far = r.reduce((best, p) => (Math.hypot(p[0] - c[0], p[1] - c[1])
    > Math.hypot(best[0] - c[0], best[1] - c[1]) ? p : best), r[0]);
  look('store-yard', [c[0] + (c[0] - far[0]) * 0.2, c[1] + (c[1] - far[1]) * 0.2], far, -10);
}
{
  const lot = record.lots.find((l) => l.lot === privy.lot);
  const r = lot.kept_ring_local_enu_m;
  const c = r.reduce((s, p) => [s[0] + p[0] / r.length, s[1] + p[1] / r.length], [0, 0]);
  const far = r.reduce((best, p) => (Math.hypot(p[0] - c[0], p[1] - c[1])
    > Math.hypot(best[0] - c[0], best[1] - c[1]) ? p : best), r[0]);
  look('rear-corner', c, far, -7);
}
const ANCHOR = null;

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
    await page.route('**/yard/town_kept_ground.json', (route) => route.fulfill({ status: 404 }));
    await page.route('**/enclosures/town_yard_paths.json', (route) => route.fulfill({ status: 404 }));
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
    return { kept: window.__chicago4d.keptGround?.census ?? null,
      problems: (window.__chicago4d.problems ?? []).filter((p) => /yard|enclos/.test(p)) };
  });
  const rows = [];
  for (const t of stands) {
    await page.evaluate((s) => {
      const api = window.__chicago4d;
      if (s.anchor) { api.goTo(s.anchor); return; }
      api.setFly(false);
      api.walker.teleport(s);
    }, t);
    await page.waitForTimeout(1200);
    const stats = await page.evaluate(() => window.__chicago4d.stats?.() ?? null);
    await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}-${phase}.jpg`),
      type: 'jpeg', quality: 86 });
    rows.push({ stand: t.name, triangles: stats?.triangles, drawCalls: stats?.drawCalls });
  }
  await page.close();
  return { ...census, stands: rows, errors };
}

const report = { entry: ENTRY, detail: DETAIL, lots: wanted, stands, viewports: {} };
for (const vp of WANT_VP) {
  report.viewports[vp] = { after: await shoot(vp, 'after'), before: await shoot(vp, 'before') };
}
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
for (const [vp, r] of Object.entries(report.viewports)) {
  console.log(`${vp}: errors after ${r.after.errors.length}, before ${r.before.errors.length}; `
    + `kept lots ${r.after.kept?.lots ?? 0} (before ${r.before.kept?.lots ?? 0})`);
  r.after.stands.forEach((s, i) => {
    const bf = r.before.stands[i];
    console.log(`  ${s.stand.padEnd(18)} tris ${bf.triangles} -> ${s.triangles}  `
      + `calls ${bf.drawCalls} -> ${s.drawCalls}`);
  });
  if (r.after.errors.length) console.log('  pageerrors:', r.after.errors.slice(0, 3));
  if (r.after.problems.length) console.log('  problems:', r.after.problems.slice(0, 5));
}
await browser.close();
server.close();
