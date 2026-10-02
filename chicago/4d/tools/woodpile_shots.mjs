/**
 * woodpile_shots.mjs — before/after captures of the woodpiles (T-1959).
 *
 *   node tools/woodpile_shots.mjs [root] [entry] [out] [--viewport desktop|mobile|both]
 *                                 [--detail full|balanced|light] [--lots a,b,c]
 *                                 [--anchor lake_at_canal]
 *
 *   root   the directory to serve (default `../../site/4d`, the published mirror)
 *   entry  the page under it (default `/walk/`)
 *   out    where the frames and report.json go (default /tmp/woodpile-shots)
 *
 * The same rig as `signboard_shots.mjs`: a static server, the published page, the
 * clock held, the chrome hidden, `walker.teleport` to stands derived from the record.
 * Each stand is shot twice — AFTER, as published, and BEFORE, the same page with
 * `yard/town_woodpiles.json` refused at the network, which is exactly the town the
 * layer degrades to when the record is missing — and `stats()` is read at both, so
 * the frame cost of the layer is the difference of two readings at one pose.
 *
 * The stands: one close and one oblique on a pile of each row of the rule (shanty,
 * cabin, cottage, house, merchant, keeper), and a context view of the cottage's back
 * lot from 22 m. A pile's OUTWARD side is the side away from its own house.
 *
 * `--anchor <id>` replaces those stands with one of the scene's authored anchors,
 * driven by `goTo` exactly as the smoke's budget ladder drives it (part 5), so the
 * layer's cost can be read at the stand the triangle ceilings are gated at.
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
const FLAGS = new Set(['--viewport', '--detail', '--lots', '--anchor']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0] ?? path.join(HERE, '..', '..', '..', 'site', '4d'));
const ENTRY = positional[1] ?? '/walk/';
const OUT = path.resolve(positional[2] ?? '/tmp/woodpile-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

const DATA = path.join(HERE, '..', 'data');
const record = JSON.parse(readFileSync(path.join(DATA, 'yard', 'town_woodpiles.json'), 'utf8'));
const ROWS = ['shanty', 'cabin', 'cottage', 'house', 'merchant', 'keeper'];
const wanted = flags['--lots'] ? flags['--lots'].split(',')
  : ROWS.map((row) => record.lots.find((l) => l.row === row && l.wall === 'back')?.structure_id)
    .filter(Boolean);

const ANCHOR = flags['--anchor'] ?? null;
const compass = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const stands = [];
for (const id of ANCHOR ? [] : wanted) {
  const lot = record.lots.find((l) => l.structure_id === id);
  if (!lot) { console.error(`no woodpile at ${id}`); process.exit(2); }
  const sc = JSON.parse(readFileSync(path.join(DATA, 'sidecars', '1835', `${id}.json`), 'utf8'));
  const pile = lot.items[0];
  const [e0, n0] = pile.at_local_enu_m;
  const b = (pile.bearing_deg * Math.PI) / 180;
  const u = [Math.cos(b), -Math.sin(b)];
  let out = [-u[1], u[0]];
  const toHouse = [sc.placement.local_e - e0, sc.placement.local_n - n0];
  if (out[0] * toHouse[0] + out[1] * toHouse[1] > 0) out = [-out[0], -out[1]];
  const at = (d, s) => [e0 + out[0] * d + u[0] * s, n0 + out[1] * d + u[1] * s];
  const pose = (name, d, s, pitch) => {
    const [e, n] = at(d, s);
    stands.push({ name: `${lot.row}-${name}`, lot: id, row: lot.row,
      local_e: e, local_n: n, yaw_deg: compass(e0 - e, n0 - n), pitch_deg: pitch });
  };
  pose('close', 3.4, 0.6, -14);
  pose('oblique', 4.6, 3.4, -9);
  if (lot.row === 'cottage') pose('context', 22, 6, -4);
}

if (ANCHOR) stands.push({ name: `anchor-${ANCHOR}`, anchor: ANCHOR });

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
    await page.route('**/yard/town_woodpiles.json', (route) => route.fulfill({ status: 404 }));
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
      problems: (window.__chicago4d.problems ?? []).filter((p) => /yard/.test(p)) };
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
    + `yard triangles ${r.before.yardTriangles} -> ${r.after.yardTriangles}; `
    + `woodpiles ${r.after.census?.woodpiles}, wood chunks ${r.after.census?.woodChunks}, `
    + `goods chunks ${r.after.census?.chunks}`);
  r.after.stands.forEach((s, i) => {
    const bf = r.before.stands[i];
    console.log(`  ${s.stand.padEnd(18)} tris ${bf.triangles} -> ${s.triangles}  `
      + `calls ${bf.drawCalls} -> ${s.drawCalls}`);
  });
  if (r.after.errors.length) console.log('  pageerrors:', r.after.errors.slice(0, 3));
  if (r.after.problems.length) console.log('  problems:', r.after.problems.slice(0, 5));
}
await browser.close();
