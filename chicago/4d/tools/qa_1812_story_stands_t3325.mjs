// T-3325..T-3327: the 1812 story jaunts' stands, rendered in the published app.
// Each stand (a JSON file: [{id, anchor, yaw, e, n}]) is reached with api.goTo(anchor), the
// trunks the stand-off rule sees (api.standOccluders) within 15 m and 40 degrees of the view
// are listed, and a 1280x800 (or QA_VIEW=390x780) shot is written to QA_OUT.
//   node tools/qa_1812_story_stands_t3325.mjs stands.json      (after tools/publish.sh)
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'stands-1812');
const [vw, vh] = (process.env.QA_VIEW || '1280x800').split('x').map(Number);
const stands = JSON.parse(fs.readFileSync(process.argv[2]));
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
try {
  const context = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: 1, isMobile: vw < 600, hasTouch: vw < 600 });
  const page = await context.newPage(); page.setDefaultTimeout(600000);
  const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/1812/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 600000, polling: 1000 });
  await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 600000, polling: 1000 });
  await page.evaluate(() => { const a = __chicago4d; a.welcome.enter('spawn'); document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click(); a.renderer.setAnimationLoop(null); a.step(); });
  for (const s of stands) {
    const r = await page.evaluate((s) => {
      const a = __chicago4d;
      a.goTo(s.anchor);
      for (let i = 0; i < 4; i++) a.step();
      const an = a.scene?.anchors?.find?.((x) => x.id === s.anchor); const w = { e: s.e ?? an?.local_e, n: s.n ?? an?.local_n };
      const occ = (a.standOccluders?.() ?? []);
      const yaw = (s.yaw ?? 0) * Math.PI / 180;
      const near = occ.map((o) => { const de = (o.e ?? o.x) - w.e, dn = (o.n ?? o.z) - w.n; const d = Math.hypot(de, dn);
        const ang = Math.atan2(de, dn); let off = Math.abs(((ang - yaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
        return { d: +d.toFixed(1), off: +(off * 180 / Math.PI).toFixed(0), r: o.r ?? o.radius }; })
        .filter((o) => o.d < 15 && o.off < 40);
      return { e: w.e, n: w.n, y: w.eyeY ?? w.y, flying: w.flying, near, occ: occ.length };
    }, s);
    await page.waitForTimeout(500);
    await page.evaluate(() => { __chicago4d.step(); __chicago4d.step(); });
    await page.screenshot({ path: path.join(out, `${s.id}-${vw}.jpg`), quality: 80, timeout: 240000 });
    console.log(s.id, JSON.stringify(r));
  }
  if (errors.length) console.log('page errors:', errors.join(' | '));
} finally { await browser.close(); server.close(); }
