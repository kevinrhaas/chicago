/**
 * town_dress_shots_1812.mjs — before/after stills of the 1812 townspeople's own dress (T-3522).
 *   node tools/town_dress_shots_1812.mjs [root] [out] [--viewport desktop|mobile|both] [--before <persons.json>]
 * The published /walk/ page at 1812, 14 August 10:00, the chrome hidden. Each stand is placed
 * from where the people of a group actually are once the day layer has set them about (their
 * mean position), at a near (about 10 m) and a normal (about 25 m) distance, looking at them.
 * AFTER is as published; BEFORE swaps in an older assets/humans/web/hm08_variation_persons.json
 * (the dev one, `git show origin/dev:...`), which carries no town dress and no hats.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  for (const p of ['playwright', '/opt/node-tools/node_modules/playwright/index.mjs']) {
    try { const ns = await import(p); return ns.chromium ? ns : ns.default; } catch { /* next */ }
  }
  const root = execSync('npm root -g').toString().trim();
  const ns = await import(path.join(root, 'playwright', 'index.js'));
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();
const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2), flags = {}, positional = [];
for (let i = 0; i < argv.length; i++) { if (argv[i].startsWith('--')) flags[argv[i]] = argv[++i]; else positional.push(argv[i]); }
const ROOT = path.resolve(positional[0] ?? path.join(HERE, '..', '..', '..', 'site', '4d'));
const OUT = path.resolve(positional[1] ?? '/tmp/town-dress-shots');
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT = (flags['--viewport'] ?? 'both') === 'both' ? ['desktop', 'mobile'] : [flags['--viewport']];
const BEFORE = flags['--before'] ?? null;
mkdirSync(OUT, { recursive: true });

const GROUPS = {
  militia: ['chicago_militia_unnamed_1', 'chicago_militia_unnamed_2', 'chicago_militia_unnamed_3', 'chicago_militia_unnamed_4',
    'chicago_militia_unnamed_5', 'chicago_militia_unnamed_6', 'burns_thomas', 'cooper_joseph', 'lee_charles', 'lee_son'],
  kinzie: ['kinzie_john_elder', 'kinzie_eleanor', 'kinzie_engage_1812', 'kinzie_boatman_1812', 'kinzie_servant_second', 'laframboise_josette_1812',
    'chandonnai_jean_baptiste', 'black_jim', 'leclerc_pierre'],
  women: ['holt_mrs', 'needs_mrs', 'simmons_susan_millhouse', 'cicely', 'corbin_mrs', 'burns_mrs', 'lee_mrs'],
};

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.geojson': 'application/json', '.webmanifest': 'application/manifest+json' };
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  try {
    if (file.endsWith('/')) file = path.join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404).end('nope'); }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });

const STANDS = {};
async function shoot(vp, phase) {
  const page = await browser.newPage({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  if (phase === 'before') {
    const old = await readFile(BEFORE);
    await page.route('**/hm08_variation_persons.json', (route) => route.fulfill({ body: old, contentType: 'application/json' }));
  }
  await page.addInitScript(() => { localStorage.setItem('chicago4d.entered', '1'); });
  page.setDefaultTimeout(300000);
  await page.goto(`${base}/walk/?year=1812`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300000 });
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(async () => {
    const api = window.__chicago4d;
    api.welcome?.enter?.('spawn');
    await api.timeOfDay?.set?.('10:00');
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; } canvas.minimap, #minimap { display: none !important; }';
    document.head.appendChild(style);
    for (let i = 0; i < 40; i++) api.days?.update?.(0.25);
  });
  const rows = [];
  for (const [name, ids] of Object.entries(GROUPS)) {
    // First go near where the group's records place them, so their figures are made.
    const seeds = [];
    for (const id of ids) {
      try { const j = JSON.parse(await readFile(path.join(HERE, '..', 'data/humans/instances/1812', `hi_town_${id}_1812.json`), 'utf8')); seeds.push([j.placement.local_e, j.placement.local_n]); } catch { /* not a town record */ }
    }
    if (seeds.length) {
      const se = seeds.reduce((s, p) => s + p[0], 0) / seeds.length, sn = seeds.reduce((s, p) => s + p[1], 0) / seeds.length;
      await page.evaluate((s) => { const api = window.__chicago4d; api.setFly?.(false); api.walker.teleport(s); }, { local_e: se, local_n: sn - 15, yaw_deg: 0, pitch_deg: -3 });
      await page.waitForTimeout(8000);
      await page.evaluate(() => { for (let i = 0; i < 8; i++) window.__chicago4d.days?.update?.(0.25); });
    }
    // Where the group's people are drawn now (each actor's own root), the ones showing.
    const at = await page.evaluate((ids) => {
      const api = window.__chicago4d, pts = [];
      for (const id of ids) {
        const a = api.humans?.get?.(id) ?? api.humans?.actors?.find((x) => x.personId === id || x.id === id);
        if (!a || a.root?.visible === false || !a.root?.parent) continue;
        const p = a.position;
        pts.push([p.e, p.n, id]);
      }
      return pts;
    }, ids);
    console.log(vp, phase, name, JSON.stringify(at.map((p) => [p[2], Math.round(p[0]), Math.round(p[1])])));
    // The densest knot: everyone within 12 m of the person with the most others near.
    let knot = [];
    for (const p of at) { const near = at.filter((q) => Math.hypot(q[0] - p[0], q[1] - p[1]) < 12); if (near.length > knot.length) knot = near; }
    at.length = 0; at.push(...knot);
    // BEFORE stands where AFTER stood (the same page; only the persons file differs).
    if (phase === 'before' && STANDS[`${vp}:${name}`]) at.splice(0, at.length, ...STANDS[`${vp}:${name}`]);
    if (!at.length) continue;
    STANDS[`${vp}:${name}`] = at.slice();
    const me = at.reduce((s, p) => s + p[0], 0) / at.length, mn = at.reduce((s, p) => s + p[1], 0) / at.length;
    for (const dist of [10, 25]) {
      // From the south-south-west, looking at the group's middle.
      const yaw = 20, r = (yaw * Math.PI) / 180;
      const stand = { local_e: me - Math.sin(r) * dist, local_n: mn - Math.cos(r) * dist, yaw_deg: yaw, pitch_deg: dist > 15 ? -2 : -4 };
      await page.evaluate((s) => { const api = window.__chicago4d; api.setFly?.(false); api.walker.teleport(s); }, stand);
      await page.waitForTimeout(dist > 15 ? 9000 : 7000);
      await page.screenshot({ path: path.join(OUT, `${vp}-${name}-${dist}m-${phase}.jpg`), type: 'jpeg', quality: 88, timeout: 300000 });
      rows.push({ group: name, dist, stand });
    }
  }
  const mem = await page.evaluate(() => window.__chicago4d.stats?.() ?? null).catch(() => null);
  await page.close();
  return { rows, errors, stats: mem };
}

const report = { viewports: {} };
for (const vp of WANT) {
  report.viewports[vp] = { after: await shoot(vp, 'after') };
  if (BEFORE) report.viewports[vp].before = await shoot(vp, 'before');
}
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(Object.fromEntries(Object.entries(report.viewports).map(([k, v]) => [k, { after: v.after.errors, before: v.before?.errors }]))));
await browser.close();
server.close();
