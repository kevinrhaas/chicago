#!/usr/bin/env node
// T-3459 — a jaunt shows its first scene in its own season. Boots a published year
// (QA_SCENE, default 1812) with the visitor's stored Season (QA_BOOT_SEASON, default
// winter), starts a jaunt (QA_JAUNT, default battle-of-fort-dearborn), and reads the
// season on the way in, at the first stop, at each later stop (a dated stop is shown in
// its date's season), and after the end (the visitor's own back). One screenshot of the
// first scene and one of a stop whose season differs; a JSON report beside them.
//   node tools/qa_jaunt_season_t3459.mjs            # phone 390x780 (after tools/publish.sh)
//   QA_DESKTOP=1 QA_OUT=/tmp/x node tools/qa_jaunt_season_t3459.mjs
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.SMOKE_ROOT || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-season-3459');
fs.mkdirSync(out, { recursive: true });
const SCENE = process.env.QA_SCENE || '1812', JAUNT = process.env.QA_JAUNT || 'battle-of-fort-dearborn';
const BOOT_SEASON = process.env.QA_BOOT_SEASON || 'winter';
const desktop = !!process.env.QA_DESKTOP, BOOT_MS = Number(process.env.QA_BOOT_MS) || 600000;
const SEASON = ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'fall', 'fall', 'fall', 'winter'];
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
const tag = desktop ? 'desktop' : 'phone', rows = [], fail = [];
const read = () => page.evaluate(() => { const a = __chicago4d, s = a.jaunts.state, st = s?.jaunt?.stops.find(x => x.id === s.visited[s.stopIndex]?.id);
  return { phase: s?.phase, stop: st?.id, date: st?.date ?? null, season: a.season.current, own: a.season.own, sun: a.season.sunDate,
    chip: document.querySelector('#year-badge .badge-sub')?.textContent, year: document.querySelector('#year-badge .badge-year')?.textContent, light: [...document.querySelectorAll('.jaunt-welcome-facts li')].map(li => li.textContent).join(' | ') }; });
// The light is a queue (a season re-grows the woods, then the hour is solved on its day):
// wait for it to land, up to QA_LIGHT_MS, and say how long it took.
const converge = async (want, date) => { const t0 = Date.now();
  await page.waitForFunction(([w, d]) => __chicago4d.season.current === w && (!d || document.querySelector('#year-badge .badge-sub')?.textContent === d.slice(5).replace('-', '.')),
    [want, date], { polling: 200, timeout: Number(process.env.QA_LIGHT_MS) || 120000 }).catch(() => null);
  return Date.now() - t0; };
const check = (r, want, why) => { const day = r.date ? r.date.slice(5).replace('-', '.') : null;
  const ok = r.season === want && (!day || r.chip === day) && (!r.date || r.year === r.date.slice(0, 4)) && (!r.date || r.sun === `${r.sun.slice(0, 4)}-${r.date.slice(5)}`); rows.push({ why, want, ...r, ok }); console.log(ok ? 'ok  ' : 'FAIL', why, JSON.stringify(r)); if (!ok) fail.push(`${why}: ${JSON.stringify(r)}`); };
const settle = async () => { await page.evaluate(() => new Promise(r => setTimeout(r, 400))); await page.evaluate(() => __chicago4d.step?.()); };
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/${SCENE}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 500 });
  await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: BOOT_MS, polling: 1000 });
  await page.evaluate(() => { __chicago4d.welcome.show(); __chicago4d.welcome.enter('jaunts'); });
  await page.locator(`[data-jaunt="${JAUNT}"] [data-action="start"]`).first().waitFor({ state: 'attached' });
  const menuLight = await page.evaluate((id) => document.querySelector(`[data-jaunt="${id}"] .jaunt-light`)?.textContent ?? null, JAUNT);
  console.log('menu light:', menuLight);
  const own = await page.evaluate(() => __chicago4d.season.current);
  check({ ...(await read()), season: own }, BOOT_SEASON, `the visitor's own ${BOOT_SEASON} before the jaunt`);
  await page.evaluate((id) => __chicago4d.jaunts.start(id), JAUNT);
  await page.waitForFunction(() => ['opening', 'atStop'].includes(__chicago4d.jaunts.state?.phase), null, { polling: 100 });
  await page.evaluate(() => new Promise(r => setTimeout(r, 300)));
  let r = await read();
  const doc = await page.evaluate(() => __chicago4d.jaunts.state.jaunt);
  const wantOf = (st) => (st?.date ? SEASON[+st.date.slice(5, 7) - 1] : doc.ambience?.season) ?? BOOT_SEASON;
  rows.push({ why: 'on the way in', ...r });
  console.log('    on the way in', JSON.stringify(r));
  await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 });
  r = await read(); r.ms = await converge(wantOf(doc.stops[0]), r.date); await settle(); r = { ...(await read()), ms: r.ms }; check(r, wantOf(doc.stops[0]), 'first scene');
  await page.screenshot({ path: path.join(out, `${tag}-${JAUNT}-first-scene.jpg`), type: 'jpeg', quality: 82, timeout: 240000 });
  let shotOther = false;
  for (let i = 1; i < doc.stops.length; ++i) {
    await page.evaluate(() => __chicago4d.jaunts.next());
    for (let k = 0; k < 40; ++k) {
      const ph = await page.evaluate(() => __chicago4d.jaunts.state?.phase);
      if (ph === 'atStop') break;
      if (ph === 'travelling') await page.evaluate(() => __chicago4d.travel.simulate?.(600));
      if (ph === 'paused') await page.evaluate(() => __chicago4d.jaunts.straight());
      await page.evaluate(() => new Promise(r => setTimeout(r, 250)));
    }
    r = await read(); const w = wantOf(doc.stops.find(s => s.id === r.stop)); const ms = await converge(w, r.date);
    r = { ...(await read()), ms }; check(r, w, `stop ${i + 1} ${r.stop}`);
    if (!shotOther && r.season !== wantOf(doc.stops[0])) {
      shotOther = true; await settle();
      await page.screenshot({ path: path.join(out, `${tag}-${JAUNT}-stop${i + 1}-${r.season}.jpg`), type: 'jpeg', quality: 82, timeout: 240000 });
    }
    if (process.env.QA_STOPS && i + 1 >= +process.env.QA_STOPS) break;
  }
  await page.evaluate(() => __chicago4d.jaunts.end());
  await page.evaluate(() => new Promise(r => setTimeout(r, 800)));
  check({ ...(await read()), season: await page.evaluate(() => __chicago4d.season.current) }, BOOT_SEASON, 'after the end: the visitor\'s own back');
  rows.push({ menuLight });
} finally {
  fs.writeFileSync(path.join(out, `${tag}-${JAUNT}.json`), JSON.stringify({ viewport, scene: SCENE, jaunt: JAUNT, errors, rows }, null, 1) + '\n');
  await browser.close(); server.close();
}
if (errors.length) fail.push('page errors: ' + errors.join(' | '));
if (fail.length) { console.error('FAIL\n ' + fail.join('\n ')); process.exit(1); }
console.log('PASS');
