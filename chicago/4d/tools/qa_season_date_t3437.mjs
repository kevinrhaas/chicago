#!/usr/bin/env node
// T-3437 — the year chip's date follows Settings › Season. Boots a published year
// (QA_YEAR, default 1835) with the stored Season (QA_BOOT_SEASON, default winter),
// reads the chip, its spoken label, the Navigator's date and the sun's date, then sets
// each season by hand, and holds a jaunt's season (transient) and gives it back.
// Writes one screenshot of the chip per season.
//   node tools/qa_season_date_t3437.mjs            # phone 390x780
//   QA_DESKTOP=1 node tools/qa_season_date_t3437.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.SMOKE_ROOT || '../../site/4d');
const out = process.env.QA_OUT || path.join(root, 'docs/RESEARCH/season-date-3437');
fs.mkdirSync(out, { recursive: true });
const YEAR = process.env.QA_YEAR || '1835';
const BOOT_SEASON = process.env.QA_BOOT_SEASON || 'winter';
const desktop = !!process.env.QA_DESKTOP;
const BOOT_MS = Number(process.env.QA_BOOT_MS) || 300000;
const SUMMER = { 1812: '1812-08-14', 1835: '1835-07-01', 1904: '1904-07-01' }[YEAR];
const WANT = { summer: SUMMER, spring: `${YEAR}-04-15`, fall: `${YEAR}-10-15`, winter: `${YEAR}-02-15` };
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.ktx2': 'image/ktx2' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try {
    if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const viewport = desktop ? { width: 1280, height: 800 } : { width: 390, height: 780 };
const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: !desktop, hasTouch: !desktop });
await context.addInitScript((season) => {
  try { if (!sessionStorage.getItem('qa.seeded')) { localStorage.setItem('chicago4d.settings', JSON.stringify({ season })); sessionStorage.setItem('qa.seeded', '1'); } } catch { /* none */ }
}, BOOT_SEASON);
const page = await context.newPage(); page.setDefaultTimeout(BOOT_MS);
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
const tag = desktop ? 'desktop' : 'phone';
const rows = [], fail = [];
const read = () => page.evaluate(() => ({
  season: window.__chicago4d.season.current,
  sun: window.__chicago4d.season.sunDate,
  chip: document.querySelector('#year-badge .badge-sub')?.textContent,
  label: document.getElementById('year-badge')?.getAttribute('aria-label'),
  nav: document.getElementById('nav-date')?.textContent,
  option: document.querySelector(`#s-season option[value="${window.__chicago4d.season.current}"]`)?.textContent,
}));
const expect = (r, season, why) => {
  const iso = WANT[season], [, mm, dd] = iso.split('-');
  const ok = r.season === season && r.sun === iso && r.chip === `${mm}.${dd}` && r.nav === iso.replace(/-/g, '.')
    && new RegExp(`^${+dd} [A-Z][a-z]+ ${YEAR}\\b`).test(r.label ?? '') && (r.option ?? '').includes(`${+dd} `);
  rows.push({ why, want: iso, ...r, ok });
  console.log(ok ? 'ok  ' : 'FAIL', why, JSON.stringify(r));
  if (!ok) fail.push(`${why}: ${JSON.stringify(r)}`);
};
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/${YEAR}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 500 });
  await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: BOOT_MS, polling: 1000 });
  await page.evaluate(async () => { const a = __chicago4d; if (!a.welcome.enter('spawn')) throw Error('welcome entry failed'); document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click(); });
  await page.waitForFunction(() => document.getElementById('gate').hidden);
  expect(await read(), BOOT_SEASON, `boot with stored ${BOOT_SEASON}`);
  await page.screenshot({ path: path.join(out, `${tag}-${YEAR}-boot-${BOOT_SEASON}.jpg`), type: 'jpeg', quality: 80, timeout: 240000 });
  for (const s of ['spring', 'fall', 'winter', 'summer']) {
    await page.evaluate((v) => __chicago4d.season.set(v), s);
    expect(await read(), s, `set ${s}`);
    await page.screenshot({ path: path.join(out, `${tag}-${YEAR}-${s}.jpg`), type: 'jpeg', quality: 80, timeout: 240000,
      clip: { x: 0, y: 0, width: viewport.width, height: 120 } });
  }
  // A jaunt's season (T-3377) shows its own day, then gives the visitor's back.
  await page.evaluate(() => __chicago4d.season.set('fall', { transient: true }));
  expect(await read(), 'fall', 'jaunt holds fall');
  await page.evaluate(() => __chicago4d.season.restore());
  expect(await read(), 'summer', 'jaunt gives summer back');
  // A jaunt stop with its own date wins over the Season (T-3328), then gives it back.
  await page.evaluate(() => __chicago4d.season.set('winter'));
  await page.evaluate((y) => __chicago4d.timeOfDay.set('morning', { date: `${y}-06-17`, transient: true }), YEAR);
  const stop = await read();
  const stopOk = stop.chip === '06.17' && stop.sun === `${YEAR}-06-17`;
  console.log(stopOk ? 'ok  ' : 'FAIL', 'stop date wins', JSON.stringify(stop));
  if (!stopOk) fail.push(`stop date: ${JSON.stringify(stop)}`);
  await page.evaluate(() => __chicago4d.timeOfDay.restore());
  expect(await read(), 'winter', 'stop gives the winter day back');
  await page.evaluate(() => __chicago4d.season.set('summer'));
} finally {
  fs.writeFileSync(path.join(out, `${tag}-${YEAR}.json`), JSON.stringify({ viewport, year: YEAR, errors, rows }, null, 1) + '\n');
  await browser.close(); server.close();
}
if (errors.length) fail.push('page errors: ' + errors.join(' | '));
if (fail.length) { console.error('FAIL\n ' + fail.join('\n ')); process.exit(1); }
console.log('PASS');
