#!/usr/bin/env node
// T-3495 — a jaunt holds the everyday people out of the scene, but for the people its stop
// calls for, and gives them all back when it ends. Boots a published year (QA_SCENE, default
// 1812), counts the figures drawn, starts a jaunt (QA_JAUNT, default battle-of-fort-dearborn),
// and at its first stop counts again and takes the view twice: as the jaunt shows it, and
// with the hold let go for one frame (what the stop looked like before T-3495). Then End,
// and the count again. A JSON report beside the pictures.
//   node tools/qa_jaunt_crowd_t3495.mjs              # phone 390x780 (after tools/publish.sh)
//   QA_DESKTOP=1 QA_OUT=/tmp/x node tools/qa_jaunt_crowd_t3495.mjs
//   QA_SCENE=1835 QA_JAUNT=new-in-chicago QA_NEXT=2 ...   # its third stop, where Peck is called for
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.SMOKE_ROOT || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-crowd-3495');
fs.mkdirSync(out, { recursive: true });
const SCENE = process.env.QA_SCENE || '1812', JAUNT = process.env.QA_JAUNT || 'battle-of-fort-dearborn';
const NEXT = Number(process.env.QA_NEXT) || 0, desktop = !!process.env.QA_DESKTOP, BOOT_MS = Number(process.env.QA_BOOT_MS) || 600000;
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
const tag = desktop ? 'desktop' : 'phone', report = { scene: SCENE, jaunt: JAUNT, tag }, fail = [];
// Figures the layer would draw: not held by a jaunt, not indoors (drawn or not by distance).
const count = () => page.evaluate(() => { const h = __chicago4d.humans;
  const all = h.actors.filter(a => !a.disposed && !a.indoors);
  return { figures: all.length, held: all.filter(a => h.isHeld?.(a)).length,
    drawn: all.filter(a => a.root.visible && a.root.parent).length, kept: h.crowdKept, shown: h.shown }; });
const frames = async (n = 3) => { for (let i = 0; i < n; ++i) await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r()))); };
const shot = (name) => page.screenshot({ path: path.join(out, `${tag}-${name}.jpg`), type: 'jpeg', quality: 82, timeout: 240000 });
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/${SCENE}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 500 });
  await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: BOOT_MS, polling: 1000 });
  report.before = await count();
  console.log('before the jaunt', JSON.stringify(report.before));
  if (report.before.held) fail.push('figures held before any jaunt');
  await page.evaluate((id) => __chicago4d.jaunts.start(id), JAUNT);
  await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 });
  for (let i = 0; i < NEXT; ++i) {
    await page.evaluate(() => { __chicago4d.jaunts.next(); __chicago4d.jaunts.straight(); });   // Straight there
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 });
  }
  await page.evaluate(() => new Promise(r => setTimeout(r, 1500)));
  await frames(6);
  report.stop = await page.evaluate(() => { const s = __chicago4d.jaunts.state; return s.visited[s.stopIndex]?.id; });
  report.during = await count();
  console.log(`at ${report.stop}`, JSON.stringify(report.during));
  const want = await page.evaluate(() => { const s = __chicago4d.jaunts.state, st = s.jaunt.stops.find(x => x.id === s.visited[s.stopIndex].id);
    return [...new Set([...(st.people || []), ...(st.links || []).filter(l => l.kind === 'person').map(l => l.id)])]; });
  if (JSON.stringify(report.during.kept) !== JSON.stringify(want)) fail.push(`kept ${JSON.stringify(report.during.kept)}, stop calls for ${JSON.stringify(want)}`);
  const keptHere = await page.evaluate(() => __chicago4d.humans.actors.filter(a => !__chicago4d.humans.isHeld(a)).length);
  if (report.during.held !== report.during.figures - keptHere) fail.push('not everyone else is held');
  if (report.during.drawn > keptHere) fail.push(`${report.during.drawn} drawn, only ${keptHere} kept`);
  await shot(`${JAUNT}-${report.stop}-jaunt`);
  // The same view with the hold let go: what this stop showed before T-3495.
  await page.evaluate(() => __chicago4d.humans.releaseCrowd());
  await page.evaluate(() => new Promise(r => setTimeout(r, 4000)));
  await frames(8);
  report.unheld = await count();
  console.log('same view, hold let go', JSON.stringify(report.unheld));
  await shot(`${JAUNT}-${report.stop}-unheld`);
  await page.evaluate((ids) => __chicago4d.humans.holdCrowd(ids), want);
  await page.evaluate(() => __chicago4d.jaunts.end());
  await frames(4);
  report.after = await count();
  console.log('after End', JSON.stringify(report.after));
  if (report.after.held || report.after.kept !== null) fail.push('figures still held after End');
} catch (e) { fail.push(String(e)); }
report.errors = errors; report.fail = fail;
fs.writeFileSync(path.join(out, `${tag}-report.json`), JSON.stringify(report, null, 2));
await browser.close(); server.close();
if (errors.length) fail.push(`${errors.length} page errors: ${errors[0]}`);
console.log(fail.length ? `FAIL\n  ${fail.join('\n  ')}` : `PASS ${tag}: ${report.during?.held} of ${report.during?.figures} held at ${report.stop}, all back after End`);
process.exit(fail.length ? 1 : 0);
