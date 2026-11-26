// T-3753: the Stops list and a jump in the published app, at a phone and a desktop width.
//   node tools/qa_jaunt_stops_app_t3753.mjs            (after tools/publish.sh)
//   QA_JAUNT=notable-women-1835 QA_SCENE=1835 QA_WIDTHS=390,1280 QA_OUT=/tmp/x node tools/qa_jaunt_stops_app_t3753.mjs
// Shots: <phone|desktop>-1-stops.png (the list open over the town), -2-jumped.png (arrived at
// the stop picked, its key spinning if the scene is still loading).
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-stops-3753');
const SCENE = process.env.QA_SCENE || '1835', JAUNT = process.env.QA_JAUNT || 'notable-women-1835';
const WIDTHS = (process.env.QA_WIDTHS || '390,1280').split(',').map(Number);
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const log = (...a) => console.log('QA 3753', ...a);
let failed = false;
try {
  for (const width of WIDTHS) {
    const phone = width < 600;
    const context = await browser.newContext({ viewport: phone ? { width: 390, height: 780 } : { width: 1280, height: 800 }, deviceScaleFactor: 2, hasTouch: phone, isMobile: phone });
    const page = await context.newPage(); page.setDefaultTimeout(600000);
    const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${server.address().port}/${SCENE}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 600000, polling: 1000 });
    log(width, 'welcome ready');
    const shot = async (name) => { await page.screenshot({ path: path.join(out, `${phone ? 'phone' : 'desktop'}-${name}.png`), timeout: 240000 }); log(width, 'shot', name); };
    await page.evaluate((id) => __chicago4d.jaunts.start(id, { mode: 'walk' }), JAUNT);
    await page.waitForFunction(() => ['opening', 'atStop'].includes(__chicago4d.jaunts.state?.phase), null, { polling: 200 });
    await page.evaluate(() => __chicago4d.jaunts.skip());
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 });
    await page.waitForTimeout(3000);
    await page.locator('#jaunt-panel [data-action="stops"]').click();
    const rows = await page.locator('#jaunt-panel .jaunt-stop-row').evaluateAll((els) => els.map((b) => b.getAttribute('aria-label')));
    log(width, 'rows', JSON.stringify(rows));
    if (rows.length < 3) throw new Error(`the list shows ${rows.length} stops`);
    await shot('1-stops');
    const pick = Math.min(3, rows.length - 1);
    await page.locator('#jaunt-panel .jaunt-stop-row').nth(pick).click();
    await page.waitForFunction((i) => __chicago4d.jaunts.state?.phase === 'atStop' && __chicago4d.jaunts.state.stopIndex === i, pick, { polling: 100, timeout: 120000 });
    const spin = await page.evaluate(() => [...document.querySelectorAll('#jaunt-panel .jaunt-loading')].map((b) => b.dataset.action));
    log(width, 'arrived at stop', pick + 1, 'spinning:', JSON.stringify(spin));
    await page.waitForTimeout(4000);
    await shot('2-jumped');
    log(width, 'page errors', errors.length, errors.slice(0, 3));
    if (errors.length) failed = true;
    await context.close();
  }
} catch (error) { failed = true; console.error(error); }
finally { await browser.close(); server.close(); }
process.exit(failed ? 1 : 0);
