/**
 * qa_haystacks_t3401.mjs — the haystacks at Lee's Place in the published app (T-3401).
 *
 *   bash tools/publish.sh && node tools/qa_haystacks_t3401.mjs     (run from chicago/4d)
 *   QA_VIEWPORT=desktop|mobile   one viewport only
 *   QA_OUT=dir                   where the frames go (default: a temp dir)
 *   QA_SITE=dir                  the published site to serve (default ../../site/4d)
 *
 * Serves the site, boots /1812/ (full detail on a desktop, light on a 390 x 780 phone),
 * holds the clock at the battle jaunt's first stop (6 April 1812, sunset) and shoots the
 * four stacks from fixed stands: the stop's own camera turned to them, the stack yard
 * from twenty metres, and the cut stack close to. Each stand records the hay sheets
 * bound (camp-surfaces.js HAY_COVERINGS); the run fails on a page error, a failed request
 * or a stand where the hay is not bound.
 */
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';

const root = process.cwd();
const require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'haystacks-3401');
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

// [name, eye (local E, N, metres above the ground), target (E, N, metres above the ground)]
// The stacks' centres: a (-1602.8, -4298.6), b (-1606.9, -4310.7), c (-1588.4, -4302.5),
// d (-1597.1, -4318.7); the stop's camera `lees_place_cabin` stands at (-1647.2, -4317.0).
const STANDS = (process.env.QA_STANDS ? JSON.parse(process.env.QA_STANDS) : [
  ['stop-camera-to-the-stacks', [-1647.2, -4317.0, 1.7], [-1599, -4307, 2.2]],
  ['stack-yard-20m', [-1622, -4326, 1.7], [-1599, -4308, 2.0]],
  ['cut-stack-close', [-1594, -4330, 1.7], [-1597.1, -4318.7, 1.6]],
  ['fed-stack-close', [-1579, -4293, 1.7], [-1588.4, -4302.5, 1.4]],
]);

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const results = [];
try {
  for (const [label, viewport, detail] of [['desktop', { width: 1280, height: 800 }, 'full'], ['mobile', { width: 390, height: 780 }, 'light']]) {
    if (process.env.QA_VIEWPORT && process.env.QA_VIEWPORT !== label) continue;
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: label === 'mobile', hasTouch: label === 'mobile' });
    const page = await context.newPage();
    page.setDefaultTimeout(600000);
    const errors = [], bad = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('response', (r) => { if (r.status() >= 400) bad.push(`${r.url()}:${r.status()}`); });
    await page.goto(`http://127.0.0.1:${server.address().port}/1812/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 600000, polling: 1000 });
    await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: 600000, polling: 1000 });
    await page.evaluate(async ({ d, hour }) => {
      const a = __chicago4d;
      if (!a.welcome.enter('spawn')) throw Error('welcome entry failed');
      document.exitPointerLock?.();
      document.getElementById('control-help-gotit')?.click();
      a.renderer.setAnimationLoop(null);
      await a.setDetail(d);
      // The stop's own hour and day: sunset, 6 April 1812 (data/jaunts/battle-of-fort-dearborn.json).
      if (hour !== 'scene') await a.timeOfDay.set(hour, { date: '1812-04-06', transient: true });
      a.step();
    }, { d: detail, hour: process.env.QA_HOUR || 'sunset' });
    const stands = [];
    for (const [name, eye, target] of STANDS) {
      const observation = await page.evaluate(({ eye, target }) => {
        const a = __chicago4d;
        const at = ([e, n, h]) => [e, n, a.terrain.surfaceHeight(e, n) + h];
        const p = at(eye), t = at(target);
        a.setFly(true);
        a.walker.teleport({ local_e: p[0], local_n: p[1], altitude_m: eye[2],
          yaw_deg: Math.atan2(t[0] - p[0], t[1] - p[1]) * 180 / Math.PI,
          pitch_deg: Math.atan2(t[2] - p[2], Math.hypot(t[0] - p[0], t[1] - p[1])) * 180 / Math.PI });
        for (let i = 0; i < 3; i += 1) a.step();
        a.camera.position.set(p[0], p[2], -p[1]);
        a.camera.lookAt(t[0], t[2], -t[1]);
        a.camera.updateMatrixWorld();
        a.world.follow(a.camera.position);
        a.world.aim(a.camera);
        a.renderer.render(a.scene3d, a.camera);
        const bound = new Set(), named = new Set();
        a.scene3d.traverse((o) => {
          for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
            if (m?.userData?.chiCampSurface) bound.add(m.userData.chiCampSurface);
            if (/^stack_hay/.test(m?.name ?? '')) named.add(m.name);
          }
        });
        return { detail: a.detail, hay: [...bound].filter((x) => x.startsWith('stack_hay')).sort(),
          hayNamed: [...named].sort(), camera: p, target: t };
      }, { eye, target });
      await page.screenshot({ path: path.join(out, `${label}-${name}.jpg`), type: 'jpeg', quality: 85, timeout: 240000 });
      stands.push({ name, ...observation });
      console.log(label, name, JSON.stringify(observation.hay));
    }
    results.push({ label, viewport, detail, errors, bad, stands });
    // A site from before T-3401 (QA_SITE at a baseline) draws no `stack_hay` material at
    // all and is shot, not failed; one that draws them must have bound all three.
    const unbound = stands.some((s) => s.hay.length < 3 && (s.hayNamed.length > 0 || !process.env.QA_SITE));
    if (errors.length || bad.length || unbound) throw Error(JSON.stringify(results.at(-1)).slice(0, 4000));
    await context.close();
    console.log(`${label} published 1812 haystacks: PASS`);
  }
} finally {
  fs.writeFileSync(path.join(out, 'browser-validation.json'), JSON.stringify({ results }, null, 2) + '\n');
  await browser.close();
  server.close();
}
