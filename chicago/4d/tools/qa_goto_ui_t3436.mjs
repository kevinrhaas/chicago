// T-3436: the Navigator's Go to in 1904, shot in the published app: the featured tiles and
// viewpoint rows, the Photos filter, and a photo view gone to instantly and on foot.
//   node tools/qa_goto_ui_t3436.mjs            (after tools/publish.sh)
//   QA_PHONE=1 for 390x780 (touch). QA_SCENE=1835 shows another year's tiles.
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'goto-ui-3436');
const PHONE = !!process.env.QA_PHONE, SCENE = process.env.QA_SCENE || '1904';
const tag = `${SCENE}-${PHONE ? 'phone' : 'desktop'}`;
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY, bypass: '127.0.0.1,localhost' } : undefined;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, proxy, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--ignore-certificate-errors'] });
const shot = async (page, name) => { await page.screenshot({ path: path.join(out, `${tag}-${name}.jpg`), quality: 80, timeout: 240000 }); console.log(`shot ${tag}-${name}`); };
try {
  const context = await browser.newContext(PHONE ? { viewport: { width: 390, height: 780 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1, ignoreHTTPSErrors: true }
    : { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, ignoreHTTPSErrors: true });
  const page = await context.newPage(); page.setDefaultTimeout(600000);
  const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/${SCENE}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 600000, polling: 1000 });
  await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 600000, polling: 1000 });
  await page.evaluate(() => { const a = __chicago4d; a.welcome.enter('spawn'); document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click(); a.renderer.setAnimationLoop(null); a.step(); });
  await page.evaluate(async () => { const a = __chicago4d; await a.navigator.select('jaunts'); a.jauntsApp.segment('goto'); document.activeElement?.blur?.(); a.step(); });
  await page.waitForTimeout(500);
  const viewRows = await page.evaluate(() => [...document.querySelectorAll('.welcome-quick-start')].map((b) => b.textContent.trim()));
  console.log('tiles', JSON.stringify(viewRows));
  await page.evaluate(() => { __chicago4d.step(); });
  await shot(page, '1-goto');
  // The tiles at Settings' 140 % text: none past the screen's edge (the T-2656 reflow check).
  const at140 = await page.evaluate(async () => {
    const sel = document.getElementById('s-text-size'); const set = (v) => { sel.value = String(v); sel.dispatchEvent(new Event('change', { bubbles: true })); };
    set(1.4); await new Promise((r) => setTimeout(r, 400)); __chicago4d.step();
    const box = document.querySelector('#nav-app-jaunts')?.getBoundingClientRect();
    const tiles = [...document.querySelectorAll('.welcome-quick-start')].map((b) => b.getBoundingClientRect());
    return { rows: new Set(tiles.map((r) => Math.round(r.top))).size, past: tiles.filter((r) => r.right > box.right + 1 || r.left < box.left - 1).length };
  });
  console.log('tiles at 140%', JSON.stringify(at140));
  await shot(page, '1b-goto-140');
  await page.evaluate(() => { const sel = document.getElementById('s-text-size'); sel.value = '1'; sel.dispatchEvent(new Event('change', { bubbles: true })); __chicago4d.step(); });
  // Viewpoints filter.
  await page.evaluate(() => { document.querySelector('#welcome-kinds button[data-kind="anchor"]')?.click(); __chicago4d.step(); });
  await shot(page, '2-viewpoints');
  // Photos: offered once the pictures file is read.
  await page.waitForFunction(() => !document.querySelector('#welcome-kinds button[data-kind="photo"]')?.hidden, null, { timeout: 120000, polling: 500 }).catch(() => console.log('no Photos pill'));
  const pill = await page.evaluate(() => { const b = document.querySelector('#welcome-kinds button[data-kind="photo"]'); b?.click(); __chicago4d.step(); return b?.textContent; });
  console.log('photos pill', pill, await page.evaluate(() => document.querySelectorAll('.welcome-destination[data-kind="photo"]').length));
  await page.waitForFunction(() => [...document.querySelectorAll('.welcome-thumb')].slice(0, 4).every((i) => i.complete), null, { timeout: 60000, polling: 500 }).catch(() => console.log('thumbs slow'));
  await page.evaluate(() => { __chicago4d.step(); });
  await shot(page, '3-photos');
  // Go instantly to the first photo row (nearest), then on foot to another.
  const first = await page.evaluate(() => { const a = __chicago4d; a.setTravelMode('instantly'); const b = document.querySelector('.welcome-destination[data-kind="photo"]'); const id = b?.dataset.id; b?.click(); for (let i = 0; i < 4; i++) { a.streetTrees?.update?.(0, a.camera); a.step(); } return { id, p: a.player }; });
  console.log('instant', JSON.stringify(first));
  await shot(page, '4-instant');
  const walked = await page.evaluate(() => {
    const a = __chicago4d; a.setTravelMode('walk');
    const row = a.welcome && document.querySelector('.welcome-destination[data-kind="photo"][data-id="a16-pullman-det-4a08065"]');
    const target = { kind: 'photo', id: 'a16-pullman-det-4a08065' };
    const ok = a.goToTarget(target);
    a.travelSimulate(240);
    for (let i = 0; i < 4; i++) { a.streetTrees?.update?.(0, a.camera); a.step(); }
    return { ok, row: !!row, p: a.player };
  });
  console.log('walked', JSON.stringify(walked));
  await shot(page, '5-walked-pullman-1890s');
  if (errors.length) console.log(`page errors: ${errors.join(' | ')}`);
  await context.close();
} finally { await browser.close(); server.close(); }
