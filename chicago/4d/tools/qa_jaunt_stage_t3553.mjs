#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553 — a jaunt stop played by its people (renderers/web/js/jaunt-stage.js). Boots the
// source tree (or SMOKE_ROOT's published site) at QA_SCENE (default 1812), starts QA_JAUNT,
// goes Straight to each stop in QA_STOPS ("1,8,9"), and at each of QA_TIMES seconds into the
// stage ("0,8,20") draws the stop's own view (or QA_VIEW "e,n,alt,yaw,pitch" over it) and
// writes it beside a JSON report: where each castmate stands, their pose, LOD, drawn or not,
// and whether the town's own figure of anyone staged is drawn too (it must not be).
// QA_SURVEY="e,n,alt,yaw,pitch;..." instead just draws those views (to place a stage).
//   QA_DESKTOP=1 QA_OUT=/tmp/stage node tools/qa_jaunt_stage_t3553.mjs
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const published = !!process.env.SMOKE_ROOT;
const site = published ? path.resolve(root, process.env.SMOKE_ROOT) : root;
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-stage-3553');
fs.mkdirSync(out, { recursive: true });
const SCENE = process.env.QA_SCENE || '1812', JAUNT = process.env.QA_JAUNT || 'battle-of-fort-dearborn';
const STOPS = (process.env.QA_STOPS || '1').split(',').map(Number), TIMES = (process.env.QA_TIMES || '0,10').split(',').map(Number);
const desktop = !!process.env.QA_DESKTOP, BOOT_MS = Number(process.env.QA_BOOT_MS) || 900000;
const VIEW = process.env.QA_VIEW ? process.env.QA_VIEW.split(',').map(Number) : null;
const SURVEY = process.env.QA_SURVEY ? process.env.QA_SURVEY.split(';').map((v) => v.split(',').map(Number)) : null;
const HOUR = process.env.QA_HOUR || null;
// QA_BEFORE=1: each stop as it was before its stage (the stage taken away), for a before/after pair.
const BEFORE = !!process.env.QA_BEFORE;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.ktx2': 'image/ktx2', '.bin': 'application/octet-stream' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try {
    if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const viewport = desktop ? { width: 1280, height: 800 } : { width: 390, height: 780 };
const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: !desktop, hasTouch: !desktop });
const page = await context.newPage(); page.setDefaultTimeout(BOOT_MS);
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
const tag = desktop ? 'desktop' : 'phone', report = { scene: SCENE, jaunt: JAUNT, tag, stops: [] }, fail = [];
const draw = async (name, view = null) => {
  const url = await page.evaluate(async (view) => {
    const a = window.__chicago4d;
    if (view) { a.setFly?.(view[2] > 2); a.walker.teleport({ local_e: view[0], local_n: view[1], altitude_m: view[2] > 2 ? view[2] : null, yaw_deg: view[3], pitch_deg: view[4] }); }
    for (let i = 0; i < 3; i++) a.step();
    return a.renderer.domElement.toDataURL('image/jpeg', 0.86);
  }, view);
  const file = path.join(out, `${tag}-${name}.jpg`);
  fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
  console.log('  wrote', file);
};
// The browser's resident memory (proportional set, every chromium process; one browser at a time).
const pssMb = () => {
  let kb = 0;
  for (const pid of fs.readdirSync('/proc').filter((d) => /^\d+$/.test(d))) {
    try {
      if (!fs.readFileSync(`/proc/${pid}/cmdline`, 'utf8').includes('chrom')) continue;
      kb += Number(/Pss:\s+(\d+)/.exec(fs.readFileSync(`/proc/${pid}/smaps_rollup`, 'utf8'))?.[1] ?? 0);
    } catch { /* gone */ }
  }
  return Math.round(kb / 1024);
};
// Get to the stop: a straight leg lands at once, but the welcome flight and the legs want
// frames; step the app and say Straight until the visitor stands at the stop.
const reach = async (label) => {
  for (let i = 0; i < 120; i++) {
    const phase = await page.evaluate(() => { const a = window.__chicago4d; if (a.jaunts.state?.phase !== 'atStop') { a.jaunts.straight(); a.step(); } return a.jaunts.state?.phase; });
    if (phase === 'atStop') return;
    if (i % 10 === 0) console.log(`  ${label}: ${phase}`);
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`${label}: never reached the stop`);
};
const settle = (ms) => page.evaluate((ms) => new Promise((r) => setTimeout(r, ms)), ms);
try {
  const url = published ? `/${SCENE}/` : `/renderers/web/index.html?year=${SCENE}`;
  await page.goto(`http://127.0.0.1:${server.address().port}${url}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 1000 });
  console.log('booted');
  report.boot_pss_mb = pssMb();
  if (SURVEY) {
    await page.evaluate(async () => { const a = window.__chicago4d; for (let i = 0; i < 40 && a.welcome.state !== 'world'; i++) { a.welcome.enter('spawn'); await new Promise((r) => setTimeout(r, 500)); } });
    if (HOUR) await page.evaluate((h) => window.__chicago4d.timeOfDay?.set?.(h), HOUR);
    let i = 0;
    for (const v of SURVEY) { await draw(`survey-${i++}-${v.join('_')}`, v); await settle(3000); await draw(`survey-${i - 1}-${v.join('_')}-b`, v); }
  } else {
    await page.evaluate(async () => { const a = window.__chicago4d; for (let i = 0; i < 40 && a.welcome.state !== 'world'; i++) { a.welcome.enter('spawn'); await new Promise((r) => setTimeout(r, 500)); } });
    if (HOUR) await page.evaluate((h) => window.__chicago4d.timeOfDay?.set?.(h), HOUR);
    await page.evaluate((id) => window.__chicago4d.jaunts.start(id, { mode: 'instantly' }), JAUNT);
    console.log('  started', await page.evaluate(() => window.__chicago4d.jaunts.state?.phase));
    await reach('start');
    let at = 0;
    for (const want of STOPS) {
      while (at < want) {
        await page.evaluate(() => { window.__chicago4d.jaunts.next(); window.__chicago4d.jaunts.straight(); });
        await reach(`stop ${at + 1}`);
        at++;
      }
      const stopId = await page.evaluate(() => { const s = window.__chicago4d.jaunts.state; return s.visited[s.stopIndex].id; });
      const row = { stop: stopId, index: want, times: [], before_pss_mb: pssMb() };
      if (BEFORE) {
        await page.evaluate(() => window.__chicago4d.jauntStage?.release());
        await settle(1500);
        await draw(`${JAUNT}-${String(want).padStart(2, '0')}-${stopId}-before`, VIEW);
        report.stops.push(row);
        continue;
      }
      // Build from the beginning, wait for the figures' bodies, then play by hand (the
      // harness's frames carry no time: the gate holds frameDt at 0).
      // The app's own frames would run the stage's clock while the bodies build (one a frame,
      // and a frame here takes seconds): take the stage off the frame loop and run it here.
      await page.evaluate(() => { window.__chicago4d.jaunts.replay(); const st = window.__chicago4d.jauntStage; if (st && !st.byHand) { st.byHand = st.update; st.update = () => {}; } });
      await page.waitForFunction(() => { const st = window.__chicago4d.jauntStage; st?.byHand(0); return !st || (st.cast.every((a) => a.body || !a.root.parent || a.indoors || (a.distance ?? 0) > 135) && (st.snapshot().teams ?? []).every((x) => x.taken)); }, null, { timeout: 900000, polling: 1500 }).catch(() => fail.push(`${stopId}: bodies did not all load`));
      let played = 0;
      for (const t of TIMES) {
        await page.evaluate((dt) => { const st = window.__chicago4d.jauntStage; const n = Math.round(dt / 0.1); for (let i = 0; i < n; i++) st?.byHand(0.1); }, t - played);
        played = t;
        await settle(1500);
        await page.evaluate(() => window.__chicago4d.jauntStage?.byHand(0));
        const snap = await page.evaluate(() => {
          const a = window.__chicago4d, st = a.jauntStage, ids = new Set(st?.ids ?? []);
          const twice = a.humans.actors.filter((x) => ids.has(x.personId) && x.root.visible && !x.disposed).map((x) => x.personId);
          // The posed figures' state, to see a kneel or a lie take (or not) at their LOD.
          const posed = (st?.cast ?? []).filter((x) => x.posture || /^gathering_/.test(x.personId ?? '')).slice(0, 8).map((x) => {
            const p = x.body?.scene?.getObjectByName?.('pelvis'), w = p ? p.getWorldPosition(new p.position.constructor()) : null;
            return { id: x.personId ?? x.instance?.id, lod: x.lod, d: +(x.distance ?? -1).toFixed(1), bound: !!x.life?.bound, kind: x.posture?.kind ?? null, w: +(x.posture?.w ?? 0).toFixed(2),
              state: x.state, path: !!x.path, route: !!x.route, inLayer: a.humans.get?.(x.personId) === x, e: +x.e.toFixed(2), n: +x.n.toFixed(2),
              pelvis_above_root: w ? +(w.y - x.root.position.y).toFixed(2) : null, tip: +x.root.rotation.x.toFixed(2) };
          });
          const tt = a.townTransport;
          const transport = tt ? { group: tt.group.visible, inScene: !!tt.group.parent, roots: tt.roots.length,
            actors: tt.actors.map((x) => ({ id: x.id, mode: x.mode, visible: x.visible, at: x.at.map((v) => +v.toFixed(1)), height: +(x.pose?.height ?? NaN).toFixed(2), err: x.stageError ?? null })) } : null;
          return { ...(st?.snapshot() ?? {}), twice, posed, transport, eye: { e: a.walker.state.e, n: a.walker.state.n, yaw: a.walker.state.yaw } };
        });
        snap.pss_mb = pssMb();
        snap.heap_mb = await page.evaluate(() => Math.round((performance.memory?.usedJSHeapSize ?? 0) / 1048576));
        console.log(JSON.stringify(snap.posed?.slice(0, 4)));
        console.log(`  ${stopId} t=${t} (clock ${snap.clock}): ${snap.cast?.length ?? 0} cast, ${snap.cast?.filter((c) => c.drawn).length ?? 0} drawn, pss ${snap.pss_mb} MB, heap ${snap.heap_mb} MB`);
        if (snap.teams?.length) console.log(`  teams: ${JSON.stringify(snap.teams)}\n  transport: ${JSON.stringify(snap.transport)}`);
        if (snap.twice?.length) fail.push(`${stopId} t=${t}: drawn twice: ${snap.twice.join(', ')}`);
        row.times.push({ t, ...snap });
        await draw(`${JAUNT}-${String(want).padStart(2, '0')}-${stopId}-t${String(t).padStart(3, '0')}`, VIEW);
      }
      report.stops.push(row);
    }
  }
} catch (e) { fail.push(String(e)); }
report.errors = errors; report.fail = fail;
fs.writeFileSync(path.join(out, `${tag}-report.json`), JSON.stringify(report, null, 2));
await browser.close(); server.close();
if (errors.length) fail.push(`${errors.length} page errors: ${errors[0]}`);
console.log(fail.length ? `FAIL\n  ${fail.join('\n  ')}` : `PASS ${tag}: ${report.stops.length} stops staged`);
process.exit(fail.length ? 1 : 0);
