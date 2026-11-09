/**
 * qa_garrison_dress_t3523.mjs — the 1812 garrison dressed by rank and armed, in the published app (T-3523).
 *
 *   bash tools/publish.sh && node tools/qa_garrison_dress_t3523.mjs [outdir]     (run from chicago/4d)
 *   QA_VIEWPORT=desktop|mobile    one viewport only;  QA_ONLY=gate,holt_isaac    some shots only
 *
 * Serves ../../site/4d, boots /1812/ (full detail on a desktop, light on a 390 x 780 phone), sets
 * the sun to 14 August 1812 at 15:00, steps the day layer and shoots the guard at the main gate,
 * the knots on the parade, a portrait of one man of each rank and duty and of the officers (from
 * a few metres in front of wherever he stands), the men at work in the garden, and the cornfield
 * party's piled arms. Fails on any page error or failed request, on a soldier whose record names a
 * musket but whose figure carries none, or an officer or NCO whose rank marks did not draw.
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
const out = path.resolve(process.argv[2] ?? path.join(root, 'docs/RESEARCH/garrison-dress-1812-3523'));
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

// [name, eye (local E, N, metres above ground), target (E, N, metres above ground)]
const STANDS = [
  ['gate-guard', [1149.4, 193.2, 1.7], [1149.6, 201.6, 1.15]],
  ['parade-knots', [1150.0, 221.0, 1.8], [1150.0, 213.5, 1.05]],
  ['garden-at-work', [1141.0, 113.0, 2.0], [1138.0, 125.0, 0.9]],
  ['cornfield-arms-piled', [136.4, -235.2, 2.9], [140.3, -238.6, 0.55]],
];
// A portrait of each: a few metres in front of where he stands.
const PORTRAITS = ['holt_isaac', 'forth_thomas', 'adams_george', 'mcpherson_hugh', 'burnett_george', 'hays_otho', 'logan_hugh',
  'heald_nathan', 'helm_linai', 'van_voorhis_isaac'];
const only = process.env.QA_ONLY ? new Set(process.env.QA_ONLY.split(',')) : null;

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
      a.world.setSun({ date: '1812-08-14', time: '15:00' });
      a.step();
    }, detail);
    await page.waitForFunction(() => document.getElementById('gate').hidden);
    await page.addStyleTag({ content: '#look-tag{display:none!important}' });
    await page.evaluate(() => { const a = __chicago4d; for (let i = 0; i < 20; i += 1) a.days?.update?.(0.1); });

    const shoot = (args) => page.evaluate(({ eye, target }) => {
      const a = __chicago4d;
      a.popup?.close?.();
      // A card opened along the way (a figure under the cursor) is folded away for the picture.
      const nc = document.getElementById('nav-close');
      if (nc && nc.offsetParent) nc.click();
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
      const st = a.stats();
      return { stats: { triangles: st.triangles, drawCalls: st.drawCalls ?? st.calls, memory: st.memory } };
    }, args);
    const settle = async (args) => {
      await shoot(args);
      for (let i = 0; i < 6; i += 1) {
        await page.waitForTimeout(1500);
        await page.evaluate(() => { const a = __chicago4d; a.days?.update?.(0.05); a.humans?.update?.(0.05, a.camera); a.step(); });
      }
      return shoot(args);
    };
    // Where a man stands now, and a stand a few metres in front of him.
    const portraitStand = (person) => page.evaluate((pid) => {
      const a = __chicago4d;
      const f = a.humans?.actors?.find((x) => x.personId === pid);
      if (!f || f.indoors) return null;
      const q = f.root.getWorldQuaternion(new f.root.quaternion.constructor());
      const fwd = new f.root.position.constructor(0, 0, 1).applyQuaternion(q);
      const fe = fwd.x, fn = -fwd.z, len = Math.hypot(fe, fn) || 1;
      const d = 3.1, side = 0.9;
      return { eye: [f.e + (fe / len) * d - (fn / len) * side, f.n + (fn / len) * d + (fe / len) * side, 1.55], target: [f.e, f.n, 1.0] };
    }, person);
    const garrisonOf = () => page.evaluate(() => {
      const a = __chicago4d;
      return (a.humans?.actors ?? []).filter((x) => x.body?.garrison).map((x) => {
        const names = [];
        x.body.scene.traverse((o) => { if (o.name?.startsWith('garrison_')) names.push(o.name); });
        return { person: x.personId, lod: x.lod, garrison: x.body.garrison, drawn: [...new Set(names)], carrying: x.actions?.snapshot?.().carrying ?? null };
      });
    });

    const stands = [];
    for (const [name, eye, target] of STANDS) {
      if (only && !only.has(name)) continue;
      const o = await settle({ eye, target });
      await page.screenshot({ path: path.join(out, `${label}-${name}.jpg`), type: 'jpeg', quality: 84, timeout: 240000 });
      stands.push({ name, ...o });
    }
    for (const person of PORTRAITS) {
      if (only && !only.has(person)) continue;
      const st = await portraitStand(person);
      if (!st) { stands.push({ name: person, missing: 'not drawn out of doors at 15:00' }); continue; }
      await settle(st);
      const again = (await portraitStand(person)) ?? st;
      const o = await settle(again);
      await page.screenshot({ path: path.join(out, `${label}-portrait-${person}.jpg`), type: 'jpeg', quality: 86, timeout: 240000 });
      stands.push({ name: person, ...o });
    }
    const garrison = await garrisonOf();
    const problems = [];
    for (const g of garrison) {
      if (g.garrison.arms && !g.drawn.includes('garrison_musket')) problems.push(`${g.person}: ${g.garrison.arms} but no musket drawn`);
      if (g.garrison.arms && !g.carrying) problems.push(`${g.person}: musket not in a held hand`);
      for (const m of g.garrison.marks ?? []) if (!g.drawn.includes(`garrison_${m === 'sash_crimson' ? 'sash' : m}`)) problems.push(`${g.person}: ${m} not drawn`);
    }
    const piles = await page.evaluate(() => { let n = 0; __chicago4d.humans?.group?.traverse((o) => { if (o.name?.startsWith('garrison_arms_pile_')) n += 1; }); return n; });
    results.push({ label, viewport, detail, boot, errors, bad, piles, garrison, problems, stands });
    console.log(`${label}: ${garrison.length} garrison figures loaded, ${piles} arms pile(s), ${problems.length} problem(s), ${errors.length} page error(s), ${bad.length} failed request(s)`);
    if (errors.length || bad.length || problems.length) console.log(JSON.stringify({ errors, bad, problems }, null, 1).slice(0, 4000));
    await context.close();
  }
} finally {
  fs.writeFileSync(path.join(out, process.env.QA_VIEWPORT ? `browser-validation-${process.env.QA_VIEWPORT}.json` : 'browser-validation.json'),
    JSON.stringify({ method: 'Published /1812/ app, normal boot; animation paused after readiness, the sun set to 14 August 1812 15:00, the day layer stepped by hand, fixed stands and portraits from in front of each man. T-3523.', results }, null, 2) + '\n');
  await browser.close();
  server.close();
}
