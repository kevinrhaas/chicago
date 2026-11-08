/**
 * qa_gathering_people_t3500.mjs — the 1812 gathering's people in the published app (T-3500).
 *
 *   bash tools/publish.sh && node tools/qa_gathering_people_t3500.mjs     (run from chicago/4d)
 *   QA_VIEWPORT=desktop|mobile                                              one viewport only
 *
 * Serves ../../site/4d, boots /1812/ (full detail on a desktop, light on a 390 x 780 phone),
 * sets the sun to 14 August at 10:00, steps the day layer and shoots the camp grounds from
 * fixed stands; then asks, at her lodge's door, for one of the gathering who is not drawn
 * (data/humans/inside_1812.json) and shoots her come out. Fails on any page error, failed
 * request, a camp-person problem, a drawn T-3500 person indoors at 10:00 who should be out,
 * or an Ask for that does not bring the person out. Frames and browser-validation.json go to
 * docs/RESEARCH/gathering-people-1812-3500/.
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
const out = path.join(root, 'docs/RESEARCH/gathering-people-1812-3500');
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
  ['south-grounds-from-above', [800, -150, 36], [700, -230, 0]],
  ['middle-ground-at-work', [777.0, -187.3, 2.0], [765.8, -180.8, 1.0]],
  ['the-bend-at-work', [756.4, -206.3, 2.0], [753.0, -218.9, 1.0]],
  ['north-flat-men', [713.4, -71.7, 2.0], [713.4, -84.7, 1.0]],
  ['west-bank-at-work', [693.5, -154.0, 2.0], [684.5, -154.0, 1.0]],
  ['miami-camp', [1077.2, 57.4, 2.0], [1077.2, 66.4, 1.0]],
];
// One of the gathering who is not drawn, asked for at her lodge's door, and where the
// visitor stands to ask (a few metres out of the door).
const ASK = { person: 'gathering_1812_upper_002', visitor: [615.1, -215.5], eye: [611.5, -214.1, 1.8], target: [616.8, -214.8, 1.0] };

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
      a.world.setSun({ date: '1812-08-14', time: '10:00' });
      a.step();
    }, detail);
    await page.waitForFunction(() => document.getElementById('gate').hidden);
    // The day layer: frameDt is 0 under the harness, so step it by hand.
    const day = await page.evaluate(() => {
      const a = __chicago4d;
      for (let i = 0; i < 20; i += 1) a.days.update(0.1);
      const snap = a.days.snapshot().filter((p) => String(p.instance).startsWith('hi_camp_'));
      return { drawn: snap.length, present: snap.filter((p) => !p.absent).length,
        out: snap.filter((p) => !p.absent && !p.indoors).length,
        indoorsByDay: snap.filter((p) => !p.absent && p.indoors && p.span && p.span.activity !== 'indoors').map((p) => p.person),
        insideOnly: a.days.insideOnly };
    });
    const stands = [];
    const shoot = (args) => page.evaluate(({ eye, target, visitor }) => {
      const a = __chicago4d;
      const at = ([e, n, h]) => [e, n, a.terrain.surfaceHeight(e, n) + h];
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
      a.camera.position.set(p[0], p[2], -p[1]);
      a.camera.lookAt(t[0], t[2], -t[1]);
      a.camera.updateMatrixWorld();
      a.world.follow(a.camera.position);
      a.world.aim(a.camera);
      a.renderer.render(a.scene3d, a.camera);
      const st = a.stats();
      return { detail: a.detail, problems: a.problems, stats: { withinBudget: st.withinBudget, triangles: st.triangles, drawCalls: st.drawCalls ?? st.calls, memory: st.memory } };
    }, args);
    // A figure's model loads after it is first wanted: show the stand, wait, show it again.
    const settle = async (args) => {
      await shoot(args);
      for (let i = 0; i < 6; i += 1) {
        await page.waitForTimeout(1500);
        await page.evaluate(() => { const a = __chicago4d; a.days.update(0.05); a.humans?.update?.(0.05, a.camera); a.step(); });
      }
      return shoot(args);
    };
    for (const [name, eye, target] of STANDS) {
      const observation = await settle({ eye, target });
      await page.screenshot({ path: path.join(out, `${label}-${name}.jpg`), type: 'jpeg', quality: 82, timeout: 240000 });
      stands.push({ name, ...observation });
    }
    // Ask for her at her door, with the visitor standing out of it, and let her come out.
    await shoot({ eye: ASK.eye, target: ASK.target, visitor: ASK.visitor });
    const ask = await page.evaluate(({ person, visitor }) => {
      const a = __chicago4d;
      const r = a.days.ask(person);
      for (let i = 0; i < 120; i += 1) { a.days.update(0.1); a.humans?.update?.(0.1, a.camera, { e: visitor[0], n: visitor[1] }); }
      const figure = a.humans?.actors?.find((x) => x.personId === person);
      return { ...r, out: a.days.insideOnly.out, figure: figure ? { e: +figure.e.toFixed(2), n: +figure.n.toFixed(2), indoors: !!figure.indoors } : null };
    }, ASK);
    await page.keyboard.press('Escape');
    await shoot({ eye: ASK.eye, target: ASK.target, visitor: ASK.visitor });
    // Her model is fetched and compiled when she is first wanted near: wait for it.
    await page.waitForFunction(({ person }) => {
      const a = __chicago4d;
      a.humans?.update?.(0.05, a.camera);
      return !!a.humans?.actors?.find((x) => x.personId === person)?.body;
    }, ASK, { timeout: 120000, polling: 1000 }).catch(() => {});
    const asked = await settle({ eye: ASK.eye, target: ASK.target, visitor: ASK.visitor });
    await page.screenshot({ path: path.join(out, `${label}-asked-for-at-her-lodge-door.jpg`), type: 'jpeg', quality: 82, timeout: 240000 });
    ask.after = await page.evaluate(async ({ person }) => {
      const a = __chicago4d;
      const f = a.humans?.actors?.find((x) => x.personId === person);
      if (!f) return null;
      const w = f.root.getWorldPosition(new f.root.position.constructor());
      return { costs: f.costsNow, body: !!f.body, at: [+f.e.toFixed(2), +f.n.toFixed(2)], world: [+w.x.toFixed(2), +w.y.toFixed(2), +w.z.toFixed(2)],
        ground: +a.terrain.surfaceHeight(f.e, f.n).toFixed(2), indoors: !!f.indoors, assetId: f.assetId ?? f.instance?.appearance?.asset_id, bodyAfter: !!f.body };
    }, ASK);
    stands.push({ name: 'asked-for-at-her-lodge-door', ask, ...asked });
    results.push({ label, viewport, detail, boot, errors, bad, day, stands });
    const campProblems = stands.flatMap((s) => (s.problems ?? []).filter((x) => /camp|gathering|miami|inside/i.test(String(x)) && !/review_required is set/.test(String(x))));
    if (errors.length || bad.length || campProblems.length || day.indoorsByDay.length || !day.out || !ask.ok || !ask.figure || ask.figure.indoors || !ask.after?.costs?.drawn) {
      throw Error(JSON.stringify(results.at(-1)).slice(0, 4000));
    }
    await context.close();
    console.log(`${label} 1812 gathering people: ${day.out} of ${day.drawn} drawn out at 10:00, ${day.insideOnly.listed} asked for at doors, ${ASK.person} came out: PASS`);
  }
} finally {
  fs.writeFileSync(path.join(out, process.env.QA_VIEWPORT ? `browser-validation-${process.env.QA_VIEWPORT}.json` : 'browser-validation.json'),
    JSON.stringify({ method: 'Published /1812/ app, normal boot; animation paused after readiness, the sun set to 14 August 10:00 and the day layer stepped by hand, for fixed review stands. T-3500: the gathering carded and one in five drawn; one asked for at her lodge door.', results }, null, 2) + '\n');
  await browser.close();
  server.close();
}
