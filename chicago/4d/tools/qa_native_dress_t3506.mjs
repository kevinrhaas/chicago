/**
 * qa_native_dress_t3506.mjs — no two of the 1812 Potawatomi and Miami people alike (T-3506).
 *
 *   bash tools/publish.sh && node tools/qa_native_dress_t3506.mjs     (run from chicago/4d)
 *   QA_VIEWPORT=desktop|mobile                                         one viewport only
 *
 * Serves ../../site/4d, boots /1812/, sets the sun to 14 August at 10:00, steps the day layer,
 * and shoots the camp grounds from stands a few metres off, then each of a ground's nearest
 * people face on. Reads every built Native figure's own cloth colours, worn pieces, hair and
 * headcloth, and fails on any page error, failed request, or two built figures of one kind
 * dressed alike. Frames and browser-validation.json go to docs/RESEARCH/native-dress-1812-3506/.
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
const out = path.join(root, 'docs/RESEARCH/native-dress-1812-3506');
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
  ['middle-ground', [772.0, -184.4, 1.8], [765.8, -180.8, 1.0]],
  ['the-bend', [755.0, -211.0, 1.8], [753.0, -218.9, 1.0]],
  ['north-flat-men', [713.4, -76.7, 1.8], [713.4, -84.7, 1.0]],
  ['west-bank', [689.0, -154.0, 1.8], [684.5, -154.0, 1.0]],
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
    page.on('pageerror', (e) => errors.push(String(e.stack || e)));
    page.on('response', (r) => { if (r.status() >= 400) bad.push(`${r.url()}:${r.status()}`); });
    await page.goto(`http://127.0.0.1:${server.address().port}/1812/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 240000, polling: 1000 });
    await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: 240000, polling: 1000 });
    await page.evaluate(async (d) => {
      const a = __chicago4d;
      if (!a.welcome.enter('spawn')) throw Error('welcome entry failed');
      document.exitPointerLock?.();
      document.getElementById('control-help-gotit')?.click();
      a.renderer.setAnimationLoop(null);
      await a.setDetail(d);
      a.world.setSun({ date: '1812-08-14', time: '10:00' });
      a.step();
    }, detail);
    await page.waitForFunction(() => document.getElementById('gate').hidden);
    await page.evaluate(() => { const a = __chicago4d; for (let i = 0; i < 20; i += 1) a.days.update(0.1); });
    const shoot = (args) => page.evaluate(({ eye, target, abs }) => {
      const a = __chicago4d;
      const at = ([e, n, h]) => [e, n, a.terrain.surfaceHeight(e, n) + h];
      const p = abs ? eye : at(eye), t = abs ? target : at(target);
      a.setFly(true);
      a.walker.teleport({ local_e: p[0], local_n: p[1], altitude_m: 30,
        yaw_deg: Math.atan2(t[0] - p[0], t[1] - p[1]) * 180 / Math.PI, pitch_deg: 0 });
      a.step();
      a.camera.position.set(p[0], p[2], -p[1]);
      a.camera.lookAt(t[0], t[2], -t[1]);
      a.camera.updateMatrixWorld();
      a.world.follow(a.camera.position);
      a.world.aim(a.camera);
      a.renderer.render(a.scene3d, a.camera);
      return { problems: a.problems };
    }, args);
    const settle = async (args) => {
      await shoot(args);
      for (let i = 0; i < 6; i += 1) {
        await page.waitForTimeout(1500);
        await page.evaluate(() => { const a = __chicago4d; a.days.update(0.05); a.humans?.update?.(0.05, a.camera); a.step(); });
      }
      return shoot(args);
    };
    const stands = [];
    for (const [name, eye, target] of STANDS) {
      const observation = await settle({ eye, target });
      await page.screenshot({ path: path.join(out, `${label}-${name}.jpg`), type: 'jpeg', quality: 84, timeout: 240000 });
      // The ground's three nearest people, face on, 2.6 m off.
      const near = await page.evaluate(([e, n]) => {
        const a = __chicago4d;
        return (a.humans?.actors ?? []).filter((x) => /potawatomi/.test(x.instance?.appearance?.asset_id ?? '') && x.root.visible)
          .map((x) => ({ id: x.personId, e: x.e, n: x.n, h: x.root.rotation.y, d: Math.hypot(x.e - e, x.n - n) }))
          .sort((p, q) => p.d - q.d).slice(0, 3);
      }, eye);
      for (const [k, who] of near.entries()) {
        const face = await page.evaluate(({ id }) => {
          const a = __chicago4d;
          const x = a.humans.actors.find((y) => y.personId === id);
          const w = x.root.getWorldPosition(new x.root.position.constructor());
          const fwd = new x.root.position.constructor(0, 0, 1).applyQuaternion(x.root.getWorldQuaternion(new x.root.quaternion.constructor()));
          return { eye: [w.x + fwd.x * 2.6, -(w.z + fwd.z * 2.6), w.y + 1.45], target: [w.x, -w.z, w.y + 1.0],
            back: [w.x - fwd.x * 1.8, -(w.z - fwd.z * 1.8), w.y + 1.6], head: [w.x, -w.z, w.y + 1.35] };
        }, who);
        await settle({ eye: face.eye, target: face.target, abs: true });
        await page.screenshot({ path: path.join(out, `${label}-${name}-person-${k + 1}.jpg`), type: 'jpeg', quality: 84, timeout: 240000 });
        // From behind and close: the hair's tie and the tail or club below it.
        if (k === 0) {
          await settle({ eye: face.back, target: face.head, abs: true });
          await page.screenshot({ path: path.join(out, `${label}-${name}-person-${k + 1}-behind.jpg`), type: 'jpeg', quality: 84, timeout: 240000 });
        }
      }
      stands.push({ name, near: near.map((x) => x.id), ...observation });
    }
    // Every built Native figure: its cloth colours, pieces hidden, hair and headcloth.
    const dressed = await page.evaluate(() => {
      const a = __chicago4d;
      const rows = [];
      for (const x of a.humans?.actors ?? []) {
        const asset = x.instance?.appearance?.asset_id ?? '';
        if (!/potawatomi/.test(asset) || !x.body) continue;
        const cloth = [], hidden = [];
        let cut = x.body.hair?.style?.cut ?? null, headcloth = false;
        x.body.scene.traverse((o) => {
          if (!o.isMesh) return;
          if (o.name === 'headcloth') headcloth = true;
          const m = o.material;
          if (!o.visible) hidden.push(o.name.replace(/^potawatomi_[a-z]+_1812_|_lod\d+$/g, ''));
          else if (/^(garment|accessory|footwear)/.test(m?.name ?? '')) cloth.push(`${m.name}=${m.color.getHexString()}`);
        });
        rows.push({ person: x.personId, asset, lod: x.body.lod, key: [cloth.sort().join(','), hidden.sort().join(','), cut, headcloth].join('|'), cut, headcloth, hidden });
      }
      return rows;
    });
    const seen = new Map(), twins = [];
    for (const r of dressed) { const k = `${r.asset}|${r.key}`; if (seen.has(k)) twins.push([seen.get(k), r.person]); else seen.set(k, r.person); }
    results.push({ label, viewport, detail, errors, bad, built: dressed.length, twins, cuts: [...new Set(dressed.map((r) => r.cut))],
      headcloths: dressed.filter((r) => r.headcloth).length, stands, dressed });
    if (errors.length || bad.length || twins.length || dressed.length < 10) throw Error(JSON.stringify(results.at(-1)).slice(0, 4000));
    await context.close();
    console.log(`${label} 1812 Native dress: ${dressed.length} figures built, no two alike, ${new Set(dressed.map((r) => r.cut)).size} hair cuts, ${results.at(-1).headcloths} headcloths: PASS`);
  }
} finally {
  fs.writeFileSync(path.join(out, process.env.QA_VIEWPORT ? `browser-validation-${process.env.QA_VIEWPORT}.json` : 'browser-validation.json'),
    JSON.stringify({ method: 'Published /1812/ app, normal boot; animation paused after readiness, the sun set to 14 August 10:00 and the day layer stepped by hand. T-3506: every built Potawatomi and Miami figure read for its own dress.', results }, null, 2) + '\n');
  await browser.close();
  server.close();
}
