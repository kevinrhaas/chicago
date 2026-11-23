// T-3734: jaunt flights in the published app, with and without the flight clearance. Flies a
// jaunt's opening glide and its first legs by Fly in each year asked for, records the eye every
// frame, and counts the frames it spent inside a drawn building (the same index the flights
// read: each structure's whole drawn box over its footprint, and the context city's stand-ins).
// "Before" is the same build with the clearance switched off at run time (needAt answering 0),
// which is exactly the flight as it was. Then it stands the eye at the deepest frame of the
// before run, and at the after run's nearest frame to the same spot, for the pictures.
//   node tools/qa_flight_clearance_t3734.mjs                 (after tools/publish.sh)
//   QA_RUNS=1904:glessner-household-tour,1871:the-great-fire QA_LEGS=3 QA_WIDTHS=1280,390 QA_OUT=/tmp/x node tools/qa_flight_clearance_t3734.mjs
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'flight-clearance-3734');
const RUNS = (process.env.QA_RUNS || '1904:prairie-architects,1871:the-great-fire,1835:across-wolf-point').split(',').map(s => s.split(':'));
const LEGS = Number(process.env.QA_LEGS || 3);
const WIDTHS = (process.env.QA_WIDTHS || '1280').split(',').map(Number);
const MODES = (process.env.QA_MODES || 'before,after').split(',');
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const log = (...a) => console.log('QA 3734', ...a);
const report = [];
try {
  for (const [scene, jaunt] of RUNS) for (const width of WIDTHS) {
    const phone = width < 600, tag = `${scene}-${phone ? 'phone' : 'desktop'}`;
    const context = await browser.newContext({ viewport: phone ? { width: 390, height: 780 } : { width: 1280, height: 800 }, deviceScaleFactor: phone ? 2 : 1, hasTouch: phone, isMobile: phone });
    const page = await context.newPage(); page.setDefaultTimeout(900000);
    const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${server.address().port}/${scene}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 900000, polling: 1000 });
    await page.evaluate(() => __chicago4d.welcome.enter('spawn'));
    await page.waitForTimeout(3000);
    const runs = {};
    for (const mode of MODES) {
      // The recorder: every pose the eye takes in a flight (walker.apply is the one place the
      // camera is written), judged against the real drawn town. Each flight is run through
      // travel.simulate at 60 Hz, synchronously, so a slow software renderer neither slows nor
      // thins it; the poses are the same ones a frame loop would draw.
      await page.evaluate((mode) => {
        const api = __chicago4d, sky = api.skyline, w = api.walker;
        sky.refresh();
        if (!window.__qaNeed) window.__qaNeed = sky.needAt;
        sky.needAt = mode === 'before' ? () => 0 : window.__qaNeed;
        window.__qaFrames = [];
        if (!w.__qaApply) { w.__qaApply = w.apply; w.apply = function () {
          const t = api.travel.state, st = w.state;
          if (window.__qaFrames && ['gliding', 'ascending', 'cruising', 'descending'].includes(t.phase)) {
            window.__qaFrames.push({ leg: api.jaunts.state?.leg ?? 0, phase: t.phase, e: st.e, n: st.n, altitude: st.eyeY - st.groundY, yaw: st.yaw, pitch: st.pitch,
              need: window.__qaNeed(st.e, st.n) });
          }
          return w.__qaApply.call(this);
        }; }
      }, mode);
      // Start where the visitor came in, every time, so both runs fly the same way.
      await page.evaluate(() => { __chicago4d.jaunts.end?.(); __chicago4d.welcome.show(); __chicago4d.welcome.enter('spawn'); });
      await page.waitForTimeout(1500);
      await page.evaluate(({ id }) => { __chicago4d.jaunts.start(id, { mode: 'fly' }); }, { id: jaunt });
      const fly = async () => {
        await page.waitForFunction(() => ['gliding', 'ascending', 'cruising', 'descending'].includes(__chicago4d.travel.state.phase)
          || __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 20, timeout: 600000 });
        await page.evaluate(() => { if (__chicago4d.travel.state.phase !== 'idle') __chicago4d.travelSimulate(240, 1 / 60); });
      };
      const ends = [];
      for (let leg = 0; leg <= LEGS; leg++) {
        await fly();
        await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 100, timeout: 600000 });
        ends.push(await page.evaluate(() => [__chicago4d.walker.state.e, __chicago4d.walker.state.n]));
        log(tag, mode, 'at stop', leg + 1);
        if (leg === LEGS) break;
        await page.evaluate(() => __chicago4d.jaunts.next());
      }
      const frames = await page.evaluate(() => { const f = window.__qaFrames; window.__qaFrames = null; return f; });
      await page.evaluate(() => __chicago4d.jaunts.end?.());
      // A frame is inside a building when it is under the top of something within reach of it,
      // away from the stands it took off from and landed on (each leg's ends).
      const starts = [null, ...ends];
      const judged = frames.map(f => {
        const near = [starts[f.leg], ends[f.leg]].filter(Boolean).some(([e, n]) => Math.hypot(f.e - e, f.n - n) < 4);
        return { ...f, under: near ? 0 : Math.max(0, f.need - 3 - f.altitude) };
      });
      const inside = judged.filter(f => f.under > 0.3);
      const worst = judged.reduce((a, f) => (f.under > (a?.under ?? 0) ? f : a), null);
      runs[mode] = { frames: judged.length, inside: inside.length, worst_m: +(worst?.under ?? 0).toFixed(2), worst, ends, judged };
      log(tag, jaunt, mode, `${inside.length} of ${judged.length} flight frames inside a building, deepest ${runs[mode].worst_m} m`);
    }
    // The pictures: the before run's deepest frame, and the after run where it passes the same spot.
    const pose = async (f, name) => {
      if (!f) return;
      await page.evaluate((f) => {
        __chicago4d.hud.setFly?.(true, { announce: false });
        __chicago4d.walker.teleport({ local_e: f.e, local_n: f.n, altitude_m: f.altitude, yaw_deg: null, pitch_deg: f.pitch * 180 / Math.PI });
        __chicago4d.walker.state.yaw = f.yaw; __chicago4d.walker.apply();
      }, f);
      await page.waitForTimeout(2500);
      await page.screenshot({ path: path.join(out, `${tag}-${name}.png`), timeout: 300000 });
      log(tag, 'shot', name);
    };
    const b = runs.before?.worst;
    if (b && runs.after) {
      const twin = runs.after.judged.filter(f => f.leg === b.leg).reduce((a, f) => {
        const d = Math.hypot(f.e - b.e, f.n - b.n);
        return d < (a?.d ?? Infinity) ? { ...f, d } : a;
      }, null);
      await pose(b, 'before');
      await pose(twin && { ...twin, yaw: b.yaw, pitch: b.pitch }, 'after');
      if (twin) log(tag, `after at the same spot: ${twin.altitude.toFixed(1)} m up, ${twin.d.toFixed(1)} m from it; needs ${(twin.need - 3).toFixed(1)} m`);
    }
    for (const r of Object.values(runs)) delete r.judged;
    report.push({ scene, jaunt, width, runs, errors: errors.slice(0, 5) });
    await context.close();
  }
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await browser.close(); server.close();
}
const bad = report.filter(r => r.runs.after && r.runs.after.inside > 0);
console.log(bad.length ? `QA 3734 FAIL — ${bad.map(r => `${r.scene} ${r.width}: ${r.runs.after.inside} frames inside`).join('; ')}` : 'QA 3734 PASS — no flight frame inside a building after the change');
process.exit(bad.length ? 1 : 0);
