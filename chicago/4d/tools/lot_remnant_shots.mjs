/**
 * lot_remnant_shots.mjs — before/after captures of the vacant lots' prairie remnant (T-2101).
 *   node tools/lot_remnant_shots.mjs [root] [entry] [out] [--viewport desktop|mobile|both]
 *                                    [--detail full|balanced|light]
 *
 * The kept-ground rig (`kept_ground_shots.mjs`): the published page, the clock held, the
 * chrome hidden, `walker.teleport` to stands derived from the record. AFTER is as published;
 * BEFORE is the same page with `z11_lot_remnant` taken out of `flora/index.json` at the
 * network, which is the town as it stood (every vacant lot growing the settled town's weeds).
 * `stats()` is read at both, so the cost is a difference at one pose. The stands: down the
 * length of the single vacant lot nearest the forks from its short side, and across it from
 * its long side.
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
const OUT = path.resolve(positional[2] ?? '/tmp/lot-remnant-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

const ZONE = 'z11_lot_remnant';
const DATA = path.join(HERE, '..', 'data');
const zone = JSON.parse(readFileSync(path.join(DATA, 'flora', 'zones', `${ZONE}.json`), 'utf8'));
const compass = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
const areaOf = (r) => Math.abs(r.reduce((s, p, i) => {
  const q = r[(i + 1) % r.length];
  return s + p[0] * q[1] - q[0] * p[1];
}, 0)) / 2;
const centre = (r) => r.reduce((s, p) => [s[0] + p[0] / r.length, s[1] + p[1] / r.length], [0, 0]);
const stands = [];
const look = (name, from, to, pitch) => stands.push({ name, local_e: from[0], local_n: from[1],
  yaw_deg: compass(to[0] - from[0], to[1] - from[1]), pitch_deg: pitch });
// One platted lot alone (an 80 x 132 ft Thompson lot is about 1,000 m2), nearest the forks.
const rings = [zone.extent.polygon, ...zone.extent.include_polygons];
const lot = rings.filter((r) => r.length === 4 && areaOf(r) > 900 && areaOf(r) < 1200)
  .sort((a, b) => Math.hypot(...centre(a)) - Math.hypot(...centre(b)))[0];
{
  const edges = lot.map((p, i) => [p, lot[(i + 1) % 4]]);
  const len = ([a, b]) => Math.hypot(b[0] - a[0], b[1] - a[1]);
  const short = edges.filter((ed) => len(ed) < 30);
  const long = edges.filter((ed) => len(ed) >= 30);
  const c = centre(lot);
  const out = (m, d) => {
    const u = [m[0] - c[0], m[1] - c[1]];
    const l = Math.hypot(...u);
    return [m[0] + (u[0] / l) * d, m[1] + (u[1] / l) * d];
  };
  const s0 = mid(...short[0]);
  look('vacant-lot-down', out(s0, 2), mid(...short[1]), -8);
  look('vacant-lot-across', out(mid(...long[0]), 6), c, -12);
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
    await page.route('**/flora/index.json', async (route) => {
      const res = await route.fetch();
      const index = await res.json();
      index.zones = index.zones.filter((z) => z.id !== ZONE);
      await route.fulfill({ response: res, json: index });
    });
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
    return { problems: (window.__chicago4d.problems ?? []).filter((p) => /flora|z11/.test(p)) };
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
    const zoneHere = await page.evaluate((s) => window.__chicago4d.flora?.zoneAt?.(s.e, s.n) ?? null,
      { e: centre(lot)[0], n: centre(lot)[1] });
    await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}-${phase}.jpg`),
      type: 'jpeg', quality: 86 });
    rows.push({ stand: t.name, triangles: stats?.triangles, drawCalls: stats?.drawCalls, zoneHere });
  }
  await page.close();
  return { ...census, stands: rows, errors };
}

const report = { entry: ENTRY, detail: DETAIL, lot, stands, viewports: {} };
for (const vp of WANT_VP) {
  report.viewports[vp] = { after: await shoot(vp, 'after'), before: await shoot(vp, 'before') };
}
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
for (const [vp, r] of Object.entries(report.viewports)) {
  console.log(`${vp}: errors after ${r.after.errors.length}, before ${r.before.errors.length}`);
  r.after.stands.forEach((s, i) => {
    const bf = r.before.stands[i];
    console.log(`  ${s.stand.padEnd(18)} tris ${bf.triangles} -> ${s.triangles}  `
      + `calls ${bf.drawCalls} -> ${s.drawCalls}  zone ${bf.zoneHere} -> ${s.zoneHere}`);
  });
  if (r.after.errors.length) console.log('  pageerrors:', r.after.errors.slice(0, 3));
  if (r.after.problems.length) console.log('  problems:', r.after.problems.slice(0, 5));
}
await browser.close();
server.close();
