#!/usr/bin/env node
// T-3460 — the 1812 commanding officer's garden in each Season. Boots the published
// /1812/, then for each season (summer, spring, fall, winter) sets it by hand and shoots
// the garden from four stands: inside the paling looking north-west over the squash to
// the corn (the owner's view of 2026-11-07), on the north walk over the cabbages and the
// currants, the jaunt's stand at the north gate, and from above the south-west corner. Reads the garden's own stats each time.
//   node tools/qa_garden_season_t3460.mjs            # desktop 1280x800
//   QA_PHONE=1 node tools/qa_garden_season_t3460.mjs # phone 390x780
//   QA_SEASONS=winter,fall QA_STANDS=inside ...      # a subset
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.SMOKE_ROOT || '../../site/4d');
const out = process.env.QA_OUT || '/tmp/garden-season-3460';
fs.mkdirSync(out, { recursive: true });
const phone = !!process.env.QA_PHONE;
const BOOT_MS = Number(process.env.QA_BOOT_MS) || 300000;
const SEASONS = (process.env.QA_SEASONS || 'summer,spring,fall,winter').split(',');
const STANDS = {
  inside: { local_e: 1166, local_n: 113.5, yaw_deg: 292 },
  north: { local_e: 1133, local_n: 134.2, yaw_deg: 248 },
  gate: { anchor: 'first_fort_gardens' },
  above: { local_e: 1104, local_n: 96, yaw_deg: 52, altitude_m: 16, pitch_deg: -24 },
};
const stands = (process.env.QA_STANDS || Object.keys(STANDS).join(',')).split(',');
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
const viewport = phone ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: phone, hasTouch: phone });
const page = await context.newPage(); page.setDefaultTimeout(BOOT_MS);
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
const tag = phone ? 'phone' : 'desktop';
const rows = [];
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/1812/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 500 });
  await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: BOOT_MS, polling: 1000 });
  await page.evaluate(() => { const a = __chicago4d; a.welcome.enter('spawn'); document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click(); });
  await page.waitForFunction(() => document.getElementById('gate').hidden);
  await page.evaluate(() => {
    window.__chicago4d.setAnimationHold?.(true);
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
    document.head.appendChild(style);
  });
  for (const season of SEASONS) {
    await page.evaluate((s) => __chicago4d.season.set(s), season);
    for (const name of stands) {
      const s = STANDS[name];
      await page.evaluate((st) => {
        const api = window.__chicago4d;
        if (st.anchor) { api.goTo(st.anchor); return; }
        api.setFly(st.altitude_m != null);
        api.walker.teleport(st);
      }, s);
      await page.waitForTimeout(phone ? 6000 : 4000);
      const g = await page.evaluate(() => ({ ...window.__chicago4d.gardens.stats }));
      const file = `${tag}-${name}-${season}.jpg`;
      await page.screenshot({ path: path.join(out, file), type: 'jpeg', quality: 84, timeout: 240000 });
      rows.push({ season, stand: name, file, garden: g });
      console.log(season, name, JSON.stringify(g));
    }
  }
} finally {
  fs.writeFileSync(path.join(out, `${tag}.json`), JSON.stringify({ viewport, errors, rows }, null, 1) + '\n');
  await browser.close(); server.close();
}
if (errors.length) { console.error('page errors:\n ' + errors.join('\n ')); process.exit(1); }
console.log('PASS');
