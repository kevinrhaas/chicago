/**
 * qa_camp_t3342.mjs — the rebuilt 1812 Potawatomi camp in the published app (T-3342).
 *
 *   node tools/publish.sh && node tools/qa_camp_t3342.mjs       (run from chicago/4d)
 *   QA_VIEWPORT=desktop|mobile                                     one viewport only
 *
 * Serves ../../site/4d, boots /1812/ normally (full detail on a desktop, light on a
 * 390 x 780 phone), holds the clock, and shoots the camp from fixed stands: above the
 * creek's mouth, inside the landing group's yard, the middle group, the west bank's group
 * and the horse ground. Each stand records the page's problems, its stats and whether the
 * camp's three coverings were bound (camp-surfaces.js), and the run fails on any page error,
 * failed request or unbound covering. Frames and browser-validation.json go to
 * docs/RESEARCH/potawatomi-camp-3342/.
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
const out = path.join(root, 'docs/RESEARCH/potawatomi-camp-3342');
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
const STANDS = [
  ['above-the-mouth', [812, -6, 24], [730, -150, 0]],
  ['landing-yard', [784, -47, 1.7], [776, -37, 0.9]],
  ['landing-canoes', [770, -20, 1.7], [782, -27, 0.3]],
  ['middle-group', [770, -199, 2.6], [770, -176, 1.2]],
  ['west-bank', [657, -160, 2.6], [680, -154, 1.0]],
  ['horse-ground', [688, -147, 3.2], [710, -126, 0.4]],
];

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const results = [];
try {
  for (const [label, viewport, detail] of [['desktop', { width: 1280, height: 800 }, 'full'], ['mobile', { width: 390, height: 780 }, 'light']]) {
    if (process.env.QA_VIEWPORT && process.env.QA_VIEWPORT !== label) continue;
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: label === 'mobile', hasTouch: label === 'mobile' });
    const page = await context.newPage();
    page.setDefaultTimeout(240000);
    const errors = [], bad = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('response', (r) => { if (r.status() >= 400) bad.push(`${r.url()}:${r.status()}`); });
    await page.goto(`http://127.0.0.1:${server.address().port}/1812/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 240000, polling: 1000 });
    const boot = await page.evaluate(() => ({ ready: __chicago4d.ready, error: __chicago4d.error, scene: __chicago4d.scene?.id }));
    if (!boot.ready || boot.scene !== '1812') throw Error(JSON.stringify(boot));
    await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: 240000, polling: 1000 });
    await page.evaluate(async (d) => {
      const a = __chicago4d;
      if (!a.welcome.enter('spawn')) throw Error('welcome entry failed');
      document.exitPointerLock?.();
      document.getElementById('control-help-gotit')?.click();
      a.renderer.setAnimationLoop(null);
      await a.setDetail(d);
      a.step();
    }, detail);
    await page.waitForFunction(() => document.getElementById('gate').hidden);
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
        a.step();
        a.camera.position.set(p[0], p[2], -p[1]);
        a.camera.lookAt(t[0], t[2], -t[1]);
        a.camera.updateMatrixWorld();
        a.world.follow(a.camera.position);
        a.world.aim(a.camera);
        a.renderer.render(a.scene3d, a.camera);
        const bound = new Set();
        a.scene3d.traverse((o) => {
          for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
            if (m?.userData?.chiCampSurface) bound.add(m.userData.chiCampSurface);
          }
        });
        const st = a.stats();
        return { detail: a.detail, campCoverings: [...bound].sort(), problems: a.problems, stats: { withinBudget: st.withinBudget, triangles: st.triangles, drawCalls: st.drawCalls ?? st.calls, memory: st.memory }, camera: p, target: t };
      }, { eye, target });
      await page.screenshot({ path: path.join(out, `${label}-${name}.jpg`), type: 'jpeg', quality: 82, timeout: 240000 });
      stands.push({ name, ...observation });
    }
    results.push({ label, viewport, detail, boot, errors, bad, stands });
    const unbound = stands.some((s) => s.campCoverings.length < 3);
    const campProblems = stands.flatMap((s) => (s.problems ?? []).filter((x) => /camp|potawatomi/i.test(String(x)) && !/review_required is set/.test(String(x))));
    if (errors.length || bad.length || unbound || campProblems.length) throw Error(JSON.stringify(results.at(-1)).slice(0, 4000));
    await context.close();
    console.log(`${label} published 1812 camp: PASS`);
  }
} finally {
  fs.writeFileSync(path.join(out, process.env.QA_VIEWPORT ? `browser-validation-${process.env.QA_VIEWPORT}.json` : 'browser-validation.json'),
    JSON.stringify({ method: 'Published /1812/ app, normal boot; animation paused after readiness for fixed review stands. T-3342: the Potawatomi camp of August 1812 rebuilt as a working camp.', results }, null, 2) + '\n');
  await browser.close();
  server.close();
}
