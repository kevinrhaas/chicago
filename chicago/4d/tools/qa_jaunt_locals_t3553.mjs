#!/usr/bin/env node
// T-3553 — the owner, 2026-11-16: "make sure there are people present and doing interactive works
// and daily activities and relevant actions and in scene of jaunt all eras". Boots the app from the
// source tree (QA_SCENE: 1812, 1835 or 1904), plays each jaunt named in QA_JAUNTS (comma list) stop
// by stop, Straight there, and at each stop waits QA_WAIT_S seconds and counts the people out about
// the stand (drawn, not held, not indoors, within JAUNT_LOCALS.r_m), staged castmates apart. A stop
// with no stage or hosts must show at least one. Pictures of QA_SHOTS stops (comma list of
// "<jaunt>:<index>", or "all"); QA_FROM skips the stops before it. A JSON report beside them.
//   QA_SCENE=1835 QA_JAUNTS=news-before-breakfast node tools/qa_jaunt_locals_t3553.mjs
//   QA_DESKTOP=1 QA_OUT=/tmp/x ...
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-locals-3553');
fs.mkdirSync(out, { recursive: true });
const SCENE = process.env.QA_SCENE || '1835';
const JAUNTS = (process.env.QA_JAUNTS || 'news-before-breakfast').split(',').filter(Boolean);
const SHOTS = (process.env.QA_SHOTS || '').split(',').filter(Boolean), FROM = Number(process.env.QA_FROM) || 0;
const WAIT_S = Number(process.env.QA_WAIT_S) || 150, desktop = !!process.env.QA_DESKTOP, BOOT_MS = Number(process.env.QA_BOOT_MS) || 1500000;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.ktx2': 'image/ktx2',
  '.mp3': 'audio/mpeg', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  let p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
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
const tag = desktop ? 'desktop' : 'phone', report = { scene: SCENE, tag, stops: [] }, fail = [];
const sleep = (ms) => page.evaluate((t) => new Promise((r) => setTimeout(r, t)), ms);
const shot = (name) => page.screenshot({ path: path.join(out, `${tag}-${name}.jpg`), type: 'jpeg', quality: 84, timeout: 300000 });
// Who is about the stand: the town's own (drawn, kept, out) and the stop's staged people apart.
const about = () => page.evaluate(() => {
  const c = __chicago4d, h = c.humans, area = h.crowdArea, s = c.jaunts.state;
  const stop = s.jaunt?.stops.find((x) => x.id === s.visited[s.stopIndex]?.id) ?? null;
  const v = c.walker.state;
  const at = area ?? { e: v.e, n: v.n, r: 70 };
  const town = h.actors.filter((a) => !a.disposed && !a.indoors && !h.isHeld?.(a) && Math.hypot(a.e - at.e, a.n - at.n) <= at.r);
  const drawn = town.filter((a) => a.root.visible && a.root.parent);
  const staged = (c.jauntStage?.cast ?? []).filter((a) => a.root.visible && !a.indoors);
  const hosts = (c.jauntHosts?.active ?? []).length;
  return { stop: stop?.id ?? null, phase: s.phase, locals: !!area, kind: stop?.stage?.cast?.length ? 'stage' : stop?.hosts?.length ? 'hosts' : 'plain',
    town: town.length, drawn: drawn.length, staged: staged.length, hosts,
    // T-3554: nobody stands on a stair (walking up or down one is how a door is reached).
    onStairs: drawn.filter((a) => a.state !== 'walking' && c.houseBarriers?.near?.(a.e, a.n, 0.35)).map((a) => a.person?.name ?? a.id),
    who: drawn.slice(0, 8).map((a) => `${a.person?.name ?? a.personId ?? a.id}${a.state ? ` (${a.state})` : ''}`),
    hour: c.timeOfDay?.hour ?? null };
});
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/renderers/web/index.html?year=${SCENE}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 1000 });
  console.log('booted');
  for (let i = 0; i < 30 && await page.evaluate(() => __chicago4d.welcome.state) !== 'world'; i++) {
    await page.evaluate(() => __chicago4d.welcome.enter('spawn')); await sleep(2000);
  }
  console.log('in the world');
  const waitPhase = async (phases) => {
    for (let k = 0; k < 600; k++) {
      const ph = await page.evaluate(() => __chicago4d.jaunts.state?.phase ?? null);
      if (phases.includes(ph)) return ph;
      if (k % 15 === 0) console.log(`  waiting: ${ph}`);
      await sleep(2000);
    }
    throw new Error(`never reached ${phases}`);
  };
  for (const id of JAUNTS) {
    console.log('start', id, await page.evaluate((j) => __chicago4d.jaunts.start(j), id));
    await waitPhase(['atStop']);
    await page.evaluate(() => document.exitPointerLock?.());
    const n = await page.evaluate(() => __chicago4d.jaunts.state.jaunt.stops.length);
    for (let i = 0; i < n; i++) {
      if (i) {
        // On as the primary path goes: Next where the stop lets it, else its first offered choice.
        const moved = await page.evaluate(async () => {
          const j = __chicago4d.jaunts, m = await import('/renderers/web/js/jaunts.js');
          if (!j.state || j.state.phase !== 'atStop') return false;
          if (m.canNext(j.state)) j.next(); else { const c = m.choicesFor(j.state)[0]; if (!c) return false; j.choose(c.id); if (m.canNext(j.state)) j.next(); }
          j.straight(); return true; });
        if (!moved) break;
        if (await waitPhase(['atStop', 'outcome']) === 'outcome') break;
      }
      if (i < FROM) continue; // QA_FROM: on past the stops before it without waiting
      // Frames are slow here (a few a second at best), and the people's clock runs on frames:
      // wait up to WAIT_S for a plain stop's people to come out.
      let row;
      for (let waited = 0; ; waited += 5) {
        await sleep(5000);
        row = { jaunt: id, index: i, waited: waited + 5, ...(await about()), calls: await page.evaluate(() => __chicago4d.days?.locals ?? null) };
        if (row.kind !== 'plain' || row.drawn >= 3 || waited + 5 >= WAIT_S) break;
      }
      // A staged castmate in view is met: aimed at, they answer with who they are.
      if (row.kind === 'stage') {
        row.met = await page.evaluate(() => {
          const c = __chicago4d, cam = c.camera;
          for (const a of c.jauntStage?.cast ?? []) {
            if (!a.root.visible || a.indoors) continue;
            const v = a.root.getWorldPosition(cam.position.clone()); v.y += 1.1;
            const ndc = v.clone().project(cam);
            if (Math.abs(ndc.x) > 0.9 || Math.abs(ndc.y) > 0.9 || ndc.z > 1) continue;
            const hit = c.pick({ x: ndc.x, y: ndc.y });
            if (hit?.actor === a) return { name: hit.name, personId: hit.personId ?? null };
          }
          return null;
        });
        if (!row.met) console.log(`  note: ${id} stop ${i}: no staged castmate in view was met`);
      }
      report.stops.push(row);
      console.log(JSON.stringify(row));
      if (row.kind === 'plain' && !row.drawn) fail.push(`${id} stop ${i} (${row.stop}): nobody about the stand`);
      if (row.onStairs?.length) fail.push(`${id} stop ${i} (${row.stop}): standing on a stair: ${row.onStairs.join(', ')}`);
      if (SHOTS.includes('all') || SHOTS.includes(`${id}:${i}`)) {
        await page.evaluate(() => { const p = document.querySelector('.jaunt-panel'); p?.classList.add('qa-folded'); });
        await shot(`${id}-${i}`);
        // The same view as it was before T-3553's neighbourhood: everyone but the stop's named held.
        if (row.locals) {
          await page.evaluate(() => { const h = __chicago4d.humans; window.__qaArea = h.crowdArea; h.holdCrowd(h.crowdKept ?? []); });
          await sleep(1500);
          await shot(`${id}-${i}-before`);
          await page.evaluate(() => { const h = __chicago4d.humans; h.holdCrowd(h.crowdKept ?? [], { area: window.__qaArea }); });
        }
      }
    }
    await page.evaluate(() => __chicago4d.jaunts.end());
    await sleep(1000);
  }
} catch (e) { fail.push(String(e)); }
report.errors = errors; report.fail = fail;
fs.writeFileSync(path.join(out, `${tag}-${SCENE}-report.json`), JSON.stringify(report, null, 2));
await browser.close(); server.close();
if (errors.length) fail.push(`${errors.length} page errors: ${errors[0]}`);
console.log(fail.length ? `FAIL\n  ${fail.join('\n  ')}` : `PASS ${tag} ${SCENE}: ${report.stops.length} stops, every plain stop has people about it`);
process.exit(fail.length ? 1 : 0);
