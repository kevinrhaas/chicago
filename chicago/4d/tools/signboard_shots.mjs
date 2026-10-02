/**
 * signboard_shots.mjs — the fixed stands T-1836 judges the signboards from.
 *
 *   node tools/signboard_shots.mjs <root-dir> <entry> <out-dir>
 *        [--viewport desktop|mobile|both] [--detail full|balanced|light]
 *        [--signs id,id,…]
 *
 * A diagnostic, not a gate — `tools/shoot.mjs`'s shape, with two differences
 * the review needs. It takes BOTH viewports (390×780 and 1280×800, device scale
 * 1, the critic harness's pinning), and it stands relative to a SIGN rather than
 * at a scene anchor: each stand is computed from the record's own
 * `anchor_local_enu_m` and `facade_bearing_deg`, so the before and after frames
 * of a review are the same pose by construction rather than by remembering a
 * coordinate. Three stands per sign:
 *
 *   close    3.6 m out from the wall, square on, looking up at the board
 *   oblique  the same distance, 38° along the street — the footway's view
 *   context  13 m out, level — the board among its neighbours
 *
 * The default subjects are the three the ticket names: a STORE BOARD
 * (Carpenter's wall board, which carries the Golden Mortar), a BRACKET SIGN
 * (Peck's store) and a TAVERN's post board (the Tremont).
 *
 * The animation clock is held and the HUD hidden before any frame, the same way
 * `critic_shots.mjs` does it, so two runs of one tree are one picture. It
 * prints the renderer's own stats (`__chicago4d.stats()`) at every stand,
 * which is the frame cost the review compares.
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

const FLAGS = new Set(['--viewport', '--detail', '--signs']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0] ?? '.');
const ENTRY = positional[1] ?? '/renderers/web/';
const OUT = path.resolve(positional[2] ?? '/tmp/signboard-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = {
  desktop: { width: 1280, height: 800 },
  mobile: { width: 390, height: 780 },
};
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
const SUBJECTS = (flags['--signs']
  ?? 'carpenter_south_water_store,peck_store,tremont_house_1').split(',');
mkdirSync(OUT, { recursive: true });

// The stands, from the record. Outward is (sin b, cos b) in ENU and along the
// wall is (cos b, −sin b) — `signage.js::buildSign`'s frame.
const HERE = path.dirname(fileURLToPath(import.meta.url));
const record = JSON.parse(readFileSync(
  path.join(HERE, '..', 'data', 'signage', 'town_business_signboards.json'), 'utf8'));
const stands = [];
for (const id of SUBJECTS) {
  const sign = record.signs.find((s) => s.structure_id === id);
  if (!sign) { console.error(`no sign ${id} in the record`); process.exit(2); }
  const [e0, n0] = sign.anchor_local_enu_m;
  const b = (sign.facade_bearing_deg ?? 0) * Math.PI / 180;
  const out = [Math.sin(b), Math.cos(b)];
  const along = [Math.cos(b), -Math.sin(b)];
  const face = (sign.facade_bearing_deg + 180) % 360;
  const at = (d, s) => [e0 + out[0] * d + along[0] * s, n0 + out[1] * d + along[1] * s];
  const [ce, cn] = at(3.6, 0);
  const [oe, on] = at(3.6 * Math.cos(38 * Math.PI / 180), 3.6 * Math.sin(38 * Math.PI / 180));
  const [xe, xn] = at(13, 0);
  stands.push(
    { name: `${id}-close`, local_e: ce, local_n: cn, yaw_deg: face, pitch_deg: 14 },
    { name: `${id}-oblique`, local_e: oe, local_n: on, yaw_deg: (face + 38) % 360, pitch_deg: 12 },
    { name: `${id}-context`, local_e: xe, local_n: xn, yaw_deg: face, pitch_deg: 4 },
  );
}

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
    res.writeHead(200, {
      'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream',
    });
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

const report = { entry: ENTRY, detail: DETAIL, viewports: {} };
for (const vp of WANT_VP) {
  const page = await browser.newPage({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
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
  const atlas = await page.evaluate(() => {
    const s = window.__chicago4d.signage;
    const mat = s?.group?.children?.[0]?.material;
    return {
      atlas: s?.atlas ?? null,
      maps: mat ? {
        map: !!mat.map, normalMap: !!mat.normalMap, roughnessMap: !!mat.roughnessMap,
      } : null,
      problems: (window.__chicago4d.problems ?? []).filter((p) => /signage/.test(p)),
    };
  });
  const rows = [];
  for (const t of stands) {
    await page.evaluate((s) => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport(s);
    }, t);
    await page.waitForTimeout(1200);
    const stats = await page.evaluate(() => window.__chicago4d.stats?.() ?? null);
    await page.screenshot({ path: path.join(OUT, `${vp}-${t.name}.jpg`), type: 'jpeg', quality: 86 });
    rows.push({ stand: t.name, stats });
  }
  report.viewports[vp] = { atlas, stands: rows, errors };
  await page.close();
}
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(Object.fromEntries(Object.entries(report.viewports).map(
  ([vp, r]) => [vp, { atlas: r.atlas, errors: r.errors.slice(0, 5),
    first: r.stands[0]?.stats }])), null, 1));
await browser.close();
server.close();
