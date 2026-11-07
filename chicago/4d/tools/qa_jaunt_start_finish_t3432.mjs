// T-3432: a jaunt in the published app, start to finish, at a phone and a desktop width:
// the flight to the start (timed, wall clock), the welcome page, a leg's road notes, the
// final stop and the compact Outing complete over the list, in each of the four appearances.
//   node tools/qa_jaunt_start_finish_t3432.mjs            (after tools/publish.sh)
//   QA_JAUNT=across-wolf-point QA_SCENE=1835 QA_WIDTHS=390,1280 QA_OUT=/tmp/x node tools/qa_jaunt_start_finish_t3432.mjs
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'jaunt-start-finish-3432');
const SCENE = process.env.QA_SCENE || '1835', JAUNT = process.env.QA_JAUNT || 'across-wolf-point';
const WIDTHS = (process.env.QA_WIDTHS || '390,1280').split(',').map(Number);
const SKINS = ['control-room', 'brass', 'worlds-fair', 'deep-space'];
const TONE = { 'control-room': 'dark', brass: 'dark', 'worlds-fair': 'light', 'deep-space': 'dark' };
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.webp': 'image/webp', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const report = { scene: SCENE, jaunt: JAUNT, runs: [] };
const log = (...a) => console.log('QA 3432', ...a);
try {
  for (const width of WIDTHS) {
    const phone = width < 600;
    const context = await browser.newContext({ viewport: phone ? { width: 390, height: 780 } : { width: 1280, height: 800 }, deviceScaleFactor: 2,
      hasTouch: phone, isMobile: phone });
    const page = await context.newPage(); page.setDefaultTimeout(600000);
    const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
    const run = { width, errors };
    await page.goto(`http://127.0.0.1:${server.address().port}/${SCENE}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 600000, polling: 1000 });
    log(width, 'welcome ready');
    const skin = (id) => page.evaluate(([id, tone]) => { document.documentElement.dataset.skin = id; document.documentElement.dataset.theme = tone; }, [id, TONE[id]]);
    const shot = async (name) => { await page.screenshot({ path: path.join(out, `${phone ? 'phone' : 'desktop'}-${name}.png`), timeout: 240000 }); log(width, 'shot', name); };
    const state = () => page.evaluate(() => { const s = __chicago4d.jaunts.state; return s && { phase: s.phase, stopIndex: s.stopIndex, leg: s.leg, lines: s.context?.lines?.length ?? 0 }; });
    // From inside the town, as a visitor who has walked somewhere first: the flight starts there.
    await page.evaluate(() => __chicago4d.welcome.enter('spawn'));
    await page.evaluate(() => { __chicago4d.welcome.show(); __chicago4d.welcome.enter('jaunts'); });
    await page.locator(`[data-jaunt="${JAUNT}"] [data-action="start"]`).first().waitFor({ state: 'attached' });
    const before = await page.evaluate(() => ({ ...__chicago4d.walker.state }));
    const t0 = Date.now();
    await page.evaluate((id) => { window.__qaStart = performance.now(); return __chicago4d.jaunts.start(id); }, JAUNT);
    await page.waitForFunction(() => ['opening', 'atStop'].includes(__chicago4d.jaunts.state?.phase), null, { polling: 100 });
    const flying = await state(); run.opening = flying.phase;
    const mid = await page.evaluate(() => ({ e: __chicago4d.walker.state.e, n: __chicago4d.walker.state.n, alt: __chicago4d.walker.state.altitude, travel: __chicago4d.travel.state.phase }));
    if (flying.phase === 'opening') await shot('1-flying-control-room');
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 100 });
    const landed = await page.evaluate(() => performance.now() - window.__qaStart);
    const at = await page.evaluate(() => ({ ...__chicago4d.walker.state }));
    run.flight = { seconds: +(landed / 1000).toFixed(2), wall_s: +((Date.now() - t0) / 1000).toFixed(2), distance_m: Math.round(Math.hypot(at.e - before.e, at.n - before.n)), mid };
    log(width, 'flight', JSON.stringify(run.flight));
    for (const id of SKINS) { await skin(id); await shot(`2-welcome-${id}`); }
    await skin('control-room');
    // A leg: walk to stop 2 and look at the road notes the leg leaves time for.
    await page.evaluate(() => __chicago4d.jaunts.next());
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'travelling' && __chicago4d.jaunts.state.context, null, { polling: 200, timeout: 60000 }).catch(() => null);
    run.leg = await page.evaluate(() => { const s = __chicago4d.jaunts.state; return { seconds: s.estimate?.legs?.[0]?.seconds, lines: s.context?.lines?.map(l => l.text.split(/\s+/).length), shown: document.querySelectorAll('.jaunt-leg-notes > p').length, clipped: [...document.querySelectorAll('.jaunt-leg-notes > p')].some(p => p.scrollHeight > p.clientHeight + 1) }; });
    log(width, 'leg', JSON.stringify(run.leg));
    await shot('3-leg-control-room');
    // On to the last stop.
    for (let i = 0; i < 8; i++) {
      const s = await state();
      if (s.phase === 'travelling') { await page.evaluate(() => __chicago4d.travel.simulate(600)); await page.waitForFunction(() => __chicago4d.jaunts.state?.phase !== 'travelling', null, { polling: 200 }); continue; }
      if (s.phase === 'paused') { await page.evaluate(() => __chicago4d.jaunts.straight()); await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop', null, { polling: 200 }); continue; }
      const final = await page.evaluate(() => document.querySelector('#jaunt-panel').classList.contains('jaunt-final'));
      if (final && s.phase === 'atStop') break;
      const choice = await page.evaluate(() => { const s = __chicago4d.jaunts.state, st = s.jaunt.stops.find(x => x.id === s.visited[s.stopIndex].id); return st.choices?.[0]?.id ?? null; });
      if (choice) await page.evaluate((c) => __chicago4d.jaunts.choose(c), choice);
      await page.evaluate(() => __chicago4d.jaunts.next());
    }
    run.final = await page.evaluate(() => ({ panel: document.querySelector('#jaunt-panel').classList.contains('jaunt-final'), button: document.querySelector('[data-action=next]').textContent, progress: document.querySelector('.jaunt-stop-k')?.textContent }));
    log(width, 'final', JSON.stringify(run.final));
    for (const id of SKINS) { await skin(id); await shot(`4-final-${id}`); }
    await skin('control-room');
    await page.evaluate(() => __chicago4d.jaunts.next());
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'outcome', null, { polling: 200 });
    await page.locator('.jaunt-outcome').waitFor();
    await page.waitForTimeout(1500);
    run.outcome = await page.evaluate(() => { const c = document.querySelector('.jaunt-outcome').getBoundingClientRect(), r = document.querySelector('#welcome-jaunts-region')?.getBoundingClientRect();
      const first = document.querySelector('.jaunt-list [data-jaunt]')?.getBoundingClientRect();
      return { card_h: Math.round(c.height), region_h: r && Math.round(r.height), first_card_visible: !!first && first.top < (r?.bottom ?? innerHeight) && first.bottom > (r?.top ?? 0) }; });
    log(width, 'outcome', JSON.stringify(run.outcome));
    for (const id of SKINS) { await skin(id); await shot(`5-outcome-${id}`); }
    await skin('control-room');
    await page.locator('.jaunt-outcome-more > summary').click();
    await shot('6-outcome-open-control-room');
    run.errors = errors; report.runs.push(run);
    await context.close();
  }
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close(); server.close();
}
console.log(JSON.stringify(report, null, 2));
