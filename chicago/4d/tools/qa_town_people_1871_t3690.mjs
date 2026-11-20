/**
 * qa_town_people_1871_t3690.mjs — the 1871 town's people, teams and horse cars in the published
 * app (T-3690).
 *
 *   bash tools/publish.sh && node tools/qa_town_people_1871_t3690.mjs      (run from chicago/4d)
 *   QA_VIEWPORT=desktop|mobile    one viewport only
 *   QA_TAG=before|after           the frames' name prefix (default after)
 *   QA_OUT=<dir>                  where frames go (default the scratch of this ticket's research)
 *   QA_FIRE=<iso local>           set the fire clock first (api.fire.set), when the scene has one
 *   QA_STANDS=a,b                 only these stands (by name)
 *
 * Serves ../../site/4d, boots /1871/ (full on a 1280 x 800 desktop, light on a 390 x 780 phone),
 * holds the sun at 8 October 1871 16:00, steps the day layer, the crowd and the town's teams by
 * hand and shoots fixed stands: State and Madison on foot and from a second-storey window,
 * Madison Street, Clark Street on the North Side and DeKoven Street on the West Side. Fails on
 * a page error, a failed request, or a 1871 stand with nobody out of doors.
 */
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';

const root = process.cwd();
const require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }
const site = path.resolve(root, '../../site/4d');
const tag = process.env.QA_TAG || 'after';
const out = process.env.QA_OUT || path.join(root, 'docs/RESEARCH/town-people-1871-3690/frames');
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp',
  '.glb': 'model/gltf-binary', '.ktx2': 'image/ktx2', '.svg': 'image/svg+xml', '.wasm': 'application/wasm' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try {
    if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));

// [name, visitor on foot (E, N) or null, eye (E, N, metres above ground), target (E, N, metres above ground)]
const STANDS = [
  ['state-street-walk', [873.5, -610], [873.5, -610, 1.65], [873.5, -480, 1.3]],
  ['madison-street-walk', [884, -536.5], [884, -536.5, 1.65], [990, -536, 1.3]],
  ['state-street-from-a-window', null, [884, -640, 9], [862, -470, 0]],
  ['state-and-madison', [874, -556], [874, -556, 1.65], [866, -420, 1.4]],
  ['clark-street-north-side', [552, 860], [552, 860, 1.65], [545, 1000, 1.4]],
  ['dekoven-street', [-300, -2018], [-300, -2018, 1.65], [-450, -2030, 1.4]],
];

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
const results = [];
let failed = null;
try {
  for (const [label, viewport, detail] of [['desktop', { width: 1280, height: 800 }, 'full'], ['mobile', { width: 390, height: 780 }, 'light']]) {
    if (process.env.QA_VIEWPORT && process.env.QA_VIEWPORT !== label) continue;
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: label === 'mobile', hasTouch: label === 'mobile' });
    const page = await context.newPage();
    page.setDefaultTimeout(300000);
    const errors = [], bad = [];
    page.on('pageerror', (e) => errors.push(String(e.stack || e)));
    page.on('response', (r) => { if (r.status() >= 400) bad.push(`${r.url()}:${r.status()}`); });
    await page.goto(`http://127.0.0.1:${server.address().port}/1871/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 900000, polling: 1000 });
    const boot = await page.evaluate(() => ({ ready: __chicago4d.ready, error: __chicago4d.error, scene: __chicago4d.scene?.id }));
    if (!boot.ready || boot.scene !== '1871') throw Error(JSON.stringify(boot));
    await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: 900000, polling: 1000 });
    await page.evaluate(async ({ d, fire }) => {
      const a = __chicago4d;
      if (!a.welcome.enter('spawn')) throw Error('welcome entry failed');
      document.exitPointerLock?.();
      document.getElementById('control-help-gotit')?.click();
      a.renderer.setAnimationLoop(null);
      await a.setDetail(d);
      a.world.setSun({ date: '1871-10-08', time: '16:00' });
      if (fire && a.fire?.set) a.fire.set(fire);
      a.step();
    }, { d: detail, fire: process.env.QA_FIRE || null });
    await page.waitForFunction(() => document.getElementById('gate').hidden).catch(() => {});
    const shoot = (args) => page.evaluate(({ eye, target, visitor }) => {
      const a = __chicago4d;
      const g = (e, n) => (a.walker?.surfaceAt?.(e, n) ?? a.terrain.surfaceHeight(e, n));
      const at = ([e, n, h]) => [e, n, g(e, n) + h];
      const p = at(eye), t = at(target);
      if (visitor) {
        a.setFly(false);
        a.walker.teleport({ local_e: visitor[0], local_n: visitor[1], yaw_deg: Math.atan2(t[0] - visitor[0], t[1] - visitor[1]) * 180 / Math.PI, pitch_deg: 0 });
      } else {
        a.setFly(true);
        a.walker.teleport({ local_e: p[0], local_n: p[1], altitude_m: eye[2],
          yaw_deg: Math.atan2(t[0] - p[0], t[1] - p[1]) * 180 / Math.PI,
          pitch_deg: Math.atan2(t[2] - p[2], Math.hypot(t[0] - p[0], t[1] - p[1])) * 180 / Math.PI });
      }
      a.step();
      a.navigator?.dock?.();   // a drawer left open by the walk's own furniture would hide the street
      a.camera.position.set(p[0], p[2], -p[1]);
      a.camera.lookAt(t[0], t[2], -t[1]);
      a.camera.updateMatrixWorld();
      a.world.follow(a.camera.position);
      a.world.aim(a.camera);
      a.renderer.render(a.scene3d, a.camera);
      const st = a.stats();
      const v = { e: eye[0], n: eye[1] };
      const outNow = a.days?.outdoors ? a.days.outdoors(v, 600, 5000).length : 0;
      const built = (a.humans?.actors ?? []).filter((x) => !x.indoors && x.body).length;
      const teams = a.townTransport?.snapshot ? a.townTransport.snapshot() : null;
      const crowd = a.crowd?.census?.() ?? null;
      return { detail: a.detail, crowd: crowd && { mid: crowd.mid, far: crowd.far, bodies: crowd.bodies, ready: crowd.bodiesReady }, problems: (a.problems ?? []).slice(-12).map(String), out: outNow, built,
        teams: Array.isArray(teams) ? teams.length : (teams?.rows?.length ?? null),
        stats: { withinBudget: st.withinBudget, triangles: st.triangles, drawCalls: st.drawCalls ?? st.calls } };
    }, args);
    // Figures, crowd bodies and teams load after they are first wanted: shoot, wait, shoot again.
    const settle = async (args) => {
      await shoot(args);
      // The crowd's bodies load and bake over frames that run: step until they have, or a while.
      for (let i = 0; i < 90; i += 1) {
        await page.waitForTimeout(400);
        const ready = await page.evaluate(() => {
          const a = __chicago4d;
          a.step?.(0.1);
          const c = a.crowd?.census?.();
          return !!c && c.bodies > 0 && c.bodiesReady >= c.bodies && c.mid + c.far > 0;
        });
        if (ready && i >= 25) break;
      }
      return shoot(args);
    };
    const stands = [];
    const only = process.env.QA_STANDS ? new Set(process.env.QA_STANDS.split(',')) : null;
    for (const [name, visitor, eye, target] of STANDS) {
      if (only && !only.has(name)) continue;
      const observation = await settle({ eye, target, visitor });
      await page.screenshot({ path: path.join(out, `${tag}-${label}-${name}.jpg`), type: 'jpeg', quality: 84, timeout: 300000 });
      stands.push({ name, ...observation });
      console.log(label, name, JSON.stringify(observation).slice(0, 400));
    }
    results.push({ label, viewport, detail, boot, errors, bad, stands });
    await context.close();
    if (errors.length || bad.length) failed = `${label}: ${errors.length} page errors, ${bad.length} failed requests: ${[...errors, ...bad].slice(0, 6).join(' | ')}`;
    else if (tag === 'after' && !stands.some((s) => s.out > 0)) failed = `${label}: nobody out of doors at any stand`;
  }
} finally {
  fs.writeFileSync(path.join(out, `${tag}-browser-validation${process.env.QA_VIEWPORT ? `-${process.env.QA_VIEWPORT}` : ''}.json`),
    JSON.stringify({ method: 'Published /1871/ app; animation paused after readiness, the sun held at 8 October 1871 16:00, the layers stepped by hand, fixed stands (T-3690).', results }, null, 2) + '\n');
  await browser.close();
  server.close();
}
if (failed) { console.error(`FAIL ${failed}`); process.exit(1); }
console.log('qa_town_people_1871_t3690: PASS');
