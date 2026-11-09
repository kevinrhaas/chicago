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
const ENTRY = positional[1] ?? '/walk/';
const OUT = path.resolve(positional[2] ?? '/tmp/brick-bond-shots');
const DETAIL = flags['--detail'] ?? 'full';
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const WANT_VP = (flags['--viewport'] ?? 'both') === 'both'
  ? ['desktop', 'mobile'] : [flags['--viewport']];
mkdirSync(OUT, { recursive: true });

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


// T-3524: Kate Ryan goes in by the Glessner court's service door at noon, up the stair, and
// comes out again at three. Stills every few seconds, and a log of where she is and how far
// the door has swung.
//   node docs/RESEARCH/glessner-passages-T-3524/shots.mjs <site/4d root> /walk/ <out> [--viewport desktop|mobile|both]
const STAND = { local_e: 1361.2, local_n: -3238.4, yaw_deg: 330, pitch_deg: 6 };
async function shoot(vp) {
  const page = await browser.newPage({ viewport: VIEWPORTS[vp], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.addInitScript((d) => {
    localStorage.setItem('chicago4d.detail', d);
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  page.setDefaultTimeout(400000);
  await page.goto(`${base}${ENTRY}?year=1904`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 400000 });
  await page.evaluate(() => window.__chicago4d.welcome.enter('spawn'));
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
    document.head.appendChild(style);
  });
  const info = await page.evaluate(() => {
    const api = window.__chicago4d;
    return { passages: (api.houseDoors?.passages ?? []).map((p) => p.id),
      problems: (api.problems ?? []).filter((p) => /door|passage|days/i.test(p)) };
  });
  console.log(vp, JSON.stringify(info));
  const state = () => page.evaluate(() => {
    const api = window.__chicago4d;
    const s = api.days?.snapshot?.().find((x) => /kate_ryan/.test(x.person ?? '')) ?? null;
    const a = api.humans?.actors?.find((x) => /kate_ryan/.test(x.personId ?? ''));
    const p = api.houseDoors?.passage?.('glessner_house:service_stair');
    return { t: performance.now() / 1000, mode: s?.mode, indoors: s?.indoors, on_way: s?.on_way, e: a?.e, n: a?.n, y: a?.standY, swing: p?.swing };
  });
  await page.evaluate(async (s) => {
    const api = window.__chicago4d;
    api.setFly(false);
    api.walker.teleport(s);
    await api.timeOfDay.set('11:00');
    // The page's own frames stand still (a slow software GPU); the people are stepped here.
    api.setAnimationHold(true);
    window.__simPeople = (seconds, dt = 0.05) => {
      const v = api.walker.state;
      const cam = { getWorldPosition(w) { w.set(v.e, 6, -v.n); return w; } };
      for (let t = 0; t < seconds; t += dt) {
        api.humans?.update(dt, cam, { e: v.e, n: v.n }, dt);
        api.duties?.update(dt);
        api.days?.update(dt);
        api.houseDoors?.update?.(dt);
        api.spacing?.update(dt);
      }
    };
  }, STAND);
  await page.evaluate(() => window.__simPeople(4));
  await page.waitForTimeout(4000);
  const log = [];
  log.push({ at: '11:00', ...(await state()) });
  console.log(vp, '11:00', JSON.stringify(log[0]));
  await page.screenshot({ path: path.join(OUT, `${vp}-0-out-1100.jpg`), type: 'jpeg', quality: 86 });
  for (const [hour, name] of [['12:00', 'in'], ['15:00', 'out']]) {
    await page.evaluate(async (h) => { await window.__chicago4d.timeOfDay.set(h); }, hour);
    let after = 0;
    for (let i = 0; i < 40 && after < 2; i += 1) {
      await page.evaluate(() => window.__simPeople(1.5));
      const s = await state();
      log.push({ at: hour, i, ...s });
      console.log(vp, hour, i, JSON.stringify(s));
      const moving = s.on_way || (s.mode && s.mode !== 'in' && s.mode !== 'out');
      if (!moving) after += 1;
      if (!s.on_way && s.swing === 0 && !moving) { if (after > 1) break; continue; }
      await page.waitForTimeout(1500);
      await page.screenshot({ path: path.join(OUT, `${vp}-${name}-${String(i).padStart(2, '0')}.jpg`), type: 'jpeg', quality: 86 });
    }
  }
  await page.close();
  return { info, log, errors };
}

const report = { entry: ENTRY, detail: DETAIL, stand: STAND, viewports: {} };
for (const vp of WANT_VP) report.viewports[vp] = await shoot(vp);
await writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
await browser.close();
server.close();
