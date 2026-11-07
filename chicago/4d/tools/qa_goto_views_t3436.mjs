// T-3436: survey and shoot the 1904 Go to viewpoints in the published app.
// QA_MODE=survey: print the framing rule's stand for QA_IDS (structure ids) and shoot each.
// QA_MODE=anchors (default): stand at every 1904 anchor (QA_ANCHORS filters) and shoot it,
// with the trunks and posts within 8 m of the line of sight listed.
//   node tools/qa_goto_views_t3436.mjs            (after tools/publish.sh)
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'goto-views-3436');
const MODE = process.env.QA_MODE || 'anchors';
const IDS = (process.env.QA_IDS || '').split(',').filter(Boolean);
const ANCHORS = new Set((process.env.QA_ANCHORS || '').split(',').filter(Boolean));
// QA_MODE=cands: QA_CANDS is a JSON list of {id, e, n, yaw, pitch?, alt?} stands to shoot.
const CANDS = JSON.parse(process.env.QA_CANDS || '[]');
const W = Number(process.env.QA_W || 1280), H = Number(process.env.QA_H || 800);
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
try {
  const context = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const page = await context.newPage(); page.setDefaultTimeout(600000);
  const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/1904/`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 600000, polling: 1000 });
  await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 600000, polling: 1000 });
  await page.evaluate(() => { const a = __chicago4d; a.welcome.enter('spawn'); document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click(); a.renderer.setAnimationLoop(null); a.step(); });
  const stands = await page.evaluate(({ MODE, IDS, ANCHORS, CANDS }) => {
    const a = __chicago4d;
    const occ = a.standOccluders?.() ?? [];
    const near = (e, n, yaw) => {
      // trunks/posts within 8 m in front, within ±20° of the view
      const hits = [];
      for (const o of occ) {
        const oe = o.e ?? o.x ?? o[0], on = o.n ?? o.y ?? o[1];
        const d = Math.hypot(oe - e, on - n); if (d > 12 || d < 0.3) continue;
        const b = (Math.atan2(oe - e, on - n) * 180 / Math.PI + 360) % 360;
        const off = ((b - yaw + 540) % 360) - 180;
        if (Math.abs(off) < 22) hits.push(`${d.toFixed(1)}m@${off.toFixed(0)}°`);
      }
      return hits;
    };
    if (MODE === 'cands') return CANDS.map((c) => ({ ...c, near: c.alt ? [] : near(c.e, c.n, c.yaw) }));
    if (MODE === 'survey') return IDS.map((id) => {
      const f = a.framing(id, { card: false, mode: 'walk' });
      if (!f) return { id, none: true };
      const aim = f.aim ? { e: f.aim.x, n: -f.aim.z } : null;
      const yaw = aim ? (Math.atan2(aim.e - f.e, aim.n - f.n) * 180 / Math.PI + 360) % 360 : f.yaw_deg;
      return { id, e: f.e, n: f.n, yaw, near: near(f.e, f.n, yaw) };
    });
    return (a.scene.anchors ?? []).filter((x) => !ANCHORS.size || ANCHORS.has(x.id))
      .map((x) => ({ id: x.id, e: x.altitude_m ? null : x.local_e, n: x.local_n, yaw: x.yaw_deg ?? 0, pitch: x.pitch_deg ?? 0, alt: x.altitude_m, near: x.altitude_m ? [] : near(x.local_e, x.local_n, x.yaw_deg ?? 0) }));
  }, { MODE, IDS, ANCHORS: [...ANCHORS], CANDS });
  for (const s of stands) {
    console.log(JSON.stringify(s));
    if (s.none) continue;
    await page.evaluate((s) => {
      const a = __chicago4d;
      if (s.alt && !s.e) a.goTo(s.id);
      else if (s.alt) { a.setFly(true); a.walker.teleport({ local_e: s.e, local_n: s.n, yaw_deg: s.yaw, pitch_deg: s.pitch ?? 0, altitude_m: s.alt }); }
      else { a.setFly(false); a.walker.teleport({ local_e: s.e, local_n: s.n, yaw_deg: s.yaw, pitch_deg: s.pitch ?? 0 }); }
      for (let i = 0; i < 3; i++) { a.streetTrees?.update?.(0, a.camera); a.streetTrees?.settle?.(); a.step(); }
    }, s);
    await page.screenshot({ path: path.join(out, `${s.id}-${W}.jpg`), quality: 80, timeout: 240000 });
    console.log(`shot ${s.id}`);
  }
  if (errors.length) console.log(`page errors: ${errors.join(' | ')}`);
  await context.close();
} finally { await browser.close(); server.close(); }
