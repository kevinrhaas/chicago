#!/usr/bin/env node
// T-3525 — the Glessner household tour: at each stop its host comes to their mark, turns to
// the visitor and greets them, and the one before goes back about their day. Boots 1904
// (after tools/publish.sh), starts the jaunt, takes each stop Straight there, waits for the
// host to stand at their mark, and photographs the stop. A JSON report beside the pictures.
//   node tools/qa_household_tour_t3525.mjs                # phone 390x780
//   QA_DESKTOP=1 QA_OUT=/tmp/x node tools/qa_household_tour_t3525.mjs
//   QA_STOPS=3 ...                                        # only the first three stops
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.SMOKE_ROOT || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'household-tour-3525');
fs.mkdirSync(out, { recursive: true });
const JAUNT = 'glessner-household-tour', desktop = !!process.env.QA_DESKTOP, BOOT_MS = Number(process.env.QA_BOOT_MS) || 600000;
const STOPS = Number(process.env.QA_STOPS) || 99;
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
const page = await context.newPage(); page.setDefaultTimeout(BOOT_MS);
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
const tag = desktop ? 'desktop' : 'phone', report = { jaunt: JAUNT, tag, stops: [] }, fail = [];
const frames = async (n = 3) => { for (let i = 0; i < n; ++i) await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r()))); };
const shot = (name) => page.screenshot({ path: path.join(out, `${tag}-${name}.jpg`), type: 'jpeg', quality: 84, timeout: 240000 });
// Where the stop's host stands against their mark and the visitor, and what the crowd keeps.
const look = () => page.evaluate(() => {
  const c = __chicago4d, s = c.jaunts.state, stop = s.jaunt.stops.find(x => x.id === s.visited[s.stopIndex].id);
  const v = c.player ?? null;
  return { stop: stop.id, phase: s.phase, kept: c.humans.crowdKept, active: c.jauntHosts?.active ?? null,
    hosts: (stop.hosts || []).map(h => { const a = c.humans.get(h.person);
      if (!a) return { person: h.person, missing: true };
      const toV = v ? (Math.atan2(v.e - a.e, v.n - a.n) * 180 / Math.PI + 360) % 360 : null;
      return { person: h.person, e: +a.e.toFixed(2), n: +a.n.toFixed(2), off_mark_m: +Math.hypot(a.e - h.local_e, a.n - h.local_n).toFixed(2),
        from_visitor_m: v ? +Math.hypot(a.e - v.e, a.n - v.n).toFixed(2) : null, facing_off_deg: toV === null ? null : +Math.abs(((a.heading - toV + 540) % 360) - 180).toFixed(1),
        indoors: !!a.indoors, held: c.humans.isHeld(a), drawn: !!a.root.visible, walking: !!a.path, blocked: c.router?.built ? c.router.blockedAt(a.e, a.n) : null }; }) };
});
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/1904/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 500 });
  await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: BOOT_MS, polling: 1000 });
  await page.evaluate((id) => __chicago4d.jaunts.start(id), JAUNT);
  await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 });
  const total = await page.evaluate(() => __chicago4d.jaunts.state.jaunt.stops.length);
  for (let i = 0; i < Math.min(total, STOPS); ++i) {
    if (i) {
      await page.evaluate(() => { __chicago4d.jaunts.next(); __chicago4d.jaunts.straight(); });
      await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 });
    }
    // Up to 4 minutes of page time for the host to walk out to the mark.
    let row = null;
    for (let k = 0; k < 120; ++k) {
      row = await look();
      if (row.hosts.every(h => !h.missing && h.off_mark_m < 0.6 && !h.walking)) break;
      await page.evaluate(() => new Promise(r => setTimeout(r, 2000)));
    }
    await page.evaluate(() => new Promise(r => setTimeout(r, 2500)));
    await frames(6);
    row = await look();
    console.log(JSON.stringify(row));
    report.stops.push(row);
    for (const h of row.hosts) {
      if (h.missing) { fail.push(`${row.stop}: ${h.person} not in the scene`); continue; }
      if (h.off_mark_m > 0.6) fail.push(`${row.stop}: ${h.person} ${h.off_mark_m} m off the mark`);
      if (h.held || h.indoors || !h.drawn) fail.push(`${row.stop}: ${h.person} not drawn (held ${h.held}, indoors ${h.indoors})`);
      if (h.facing_off_deg > 40) fail.push(`${row.stop}: ${h.person} turned ${h.facing_off_deg} deg from the visitor`);
      if (h.blocked) fail.push(`${row.stop}: ${h.person}'s mark is blocked ground`);
    }
    await shot(`${String(i + 1).padStart(2, '0')}-${row.stop}`);
    if (!desktop) {
      // A phone's panel covers the scene; the visitor folds it to look, so look folded too.
      await page.click('.jaunt-collapse').catch(() => {});
      await frames(4);
      await shot(`${String(i + 1).padStart(2, '0')}-${row.stop}-folded`);
      await page.evaluate(() => document.querySelector('.jaunt-bar-label')?.click());
      await frames(2);
    }
  }
  await page.evaluate(() => __chicago4d.jaunts.end());
  await frames(4);
  report.after = await page.evaluate(() => ({ kept: __chicago4d.humans.crowdKept, active: __chicago4d.jauntHosts?.active ?? null }));
  if (report.after.kept !== null || report.after.active?.length) fail.push(`after End: ${JSON.stringify(report.after)}`);
} catch (e) { fail.push(String(e)); }
report.errors = errors; report.fail = fail;
fs.writeFileSync(path.join(out, `${tag}-report.json`), JSON.stringify(report, null, 2));
await browser.close(); server.close();
if (errors.length) fail.push(`${errors.length} page errors: ${errors[0]}`);
console.log(fail.length ? `FAIL\n  ${fail.join('\n  ')}` : `PASS ${tag}: ${report.stops.length} stops, every host at their mark facing the visitor`);
process.exit(fail.length ? 1 : 0);
