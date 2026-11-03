// T-3263: every jaunt stop's arrival, measured in the published app with the live trees.
// For each scene with jaunts (1904, 1835) it boots the page, asks the one framing rule
// where a walking arrival at each structure stop stands (api.framing, card down, as a
// jaunt arrives), and measures with route.js frontView how much of the house's street
// front the trunks and posts the page itself hands the rule (api.standOccluders) hide —
// the parkway elms, lamps and poles in 1904, the grown timber's trunks in 1835. QA_SHOTS
// names stops (structure ids) to render at the stand, desktop 1280x800.
//   node tools/qa_jaunt_views_t3263.mjs                       (after tools/publish.sh)
//   QA_TAG=before QA_BEFORE_REF=origin/dev node tools/qa_jaunt_views_t3263.mjs
//   QA_SCENES=1904 QA_SHOTS=jones_house_1834_prairie node tools/qa_jaunt_views_t3263.mjs
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { frontView, VIEW_BLOCKED, VIEW_NEAR_BLOCKED } from '../renderers/web/js/route.js';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-views-3263');
const TAG = process.env.QA_TAG || 'after';
// A "before" reading serves route.js as it stands at this git ref: the rule without trunks.
const BEFORE_REF = process.env.QA_BEFORE_REF || null;
const oldRoute = BEFORE_REF ? execFileSync('git', ['show', `${BEFORE_REF}:chicago/4d/renderers/web/js/route.js`]) : null;
const SCENES = (process.env.QA_SCENES || '1904,1835').split(',');
const SHOTS = new Set((process.env.QA_SHOTS || '').split(',').filter(Boolean));
fs.mkdirSync(out, { recursive: true });

const stopsOf = (scene) => fs.readdirSync(path.join(root, 'data/jaunts')).filter((n) => n.endsWith('.json') && n !== 'schema.json')
  .map((n) => JSON.parse(fs.readFileSync(path.join(root, 'data/jaunts', n))))
  .filter((j) => j.scene === scene)
  .flatMap((j) => (j.stops ?? []).filter((s) => s.destination?.kind === 'structure').map((s) => ({ jaunt: j.id, stop: s.id, id: s.destination.id })));

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  if (oldRoute && /\/js\/route\.js$/.test(p)) { res.writeHead(200, { 'Content-Type': 'text/javascript', 'Cache-Control': 'no-store' }); res.end(oldRoute); return; }
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const report = { tag: TAG, before_ref: BEFORE_REF, scenes: {} };
try {
  for (const scene of SCENES) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
    const page = await context.newPage(); page.setDefaultTimeout(600000);
    const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${server.address().port}/${scene}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 600000, polling: 1000 });
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 600000, polling: 1000 });
    await page.evaluate(() => { const a = __chicago4d; a.welcome.enter('spawn'); document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click(); a.renderer.setAnimationLoop(null); a.step(); });
    const stops = stopsOf(scene);
    const ids = [...new Set(stops.map((s) => s.id))];
    const live = await page.evaluate((ids) => {
      const a = __chicago4d;
      const occ = a.standOccluders?.() ?? [];
      const stands = {};
      for (const id of ids) {
        const f = a.framing(id, { card: false, mode: 'walk' });
        stands[id] = f ? { e: f.e, n: f.n, front: f.front } : null;
      }
      return { occ, stands };
    }, ids);
    const rows = ids.map((id) => {
      const s = live.stands[id];
      const v = s?.front ? frontView(s, s.front, live.occ) : null;
      return { id, e: s?.e ?? null, n: s?.n ?? null, hidden: v?.hidden ?? null, near: v?.near ?? null,
        blocked: !!v && (v.near > VIEW_NEAR_BLOCKED || v.hidden > VIEW_BLOCKED) };
    });
    for (const r of rows) console.log(`${TAG} ${scene} ${r.id.padEnd(44)} e ${r.e?.toFixed(1)} n ${r.n?.toFixed(1)}  hidden ${r.hidden === null ? '—' : (r.hidden * 100).toFixed(0) + '%'}  near ${r.near === null ? '—' : (r.near * 100).toFixed(0) + '%'}${r.blocked ? '  BLOCKED' : ''}`);
    console.log(`${TAG} ${scene}: ${rows.filter((r) => r.blocked).length} of ${rows.length} stop structures stand blocked; ${live.occ.length} trunks and posts`);
    report.scenes[scene] = { occluders: live.occ.length, rows, errors };
    for (const id of ids.filter((i) => SHOTS.has(i))) {
      await page.evaluate((id) => { const a = __chicago4d; a.frame(id, { card: false, mode: 'walk' }); a.streetTrees?.update?.(0, a.camera); a.streetTrees?.settle?.(); a.step(); }, id);
      await page.screenshot({ path: path.join(out, `${scene}-${id}-${TAG}.jpg`), quality: 85, timeout: 240000 });
      console.log(`shot ${scene} ${id}`);
    }
    if (errors.length) console.log(`page errors: ${errors.join(' | ')}`);
    await context.close();
  }
} finally {
  fs.writeFileSync(path.join(out, `report-${TAG}.json`), JSON.stringify(report, null, 1));
  await browser.close(); server.close();
}
