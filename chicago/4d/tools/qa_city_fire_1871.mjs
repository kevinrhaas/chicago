#!/usr/bin/env node
/**
 * T-3687: look at the Great Fire in the published 1871 city, through the real app.
 *
 * node tools/qa_city_fire_1871.mjs --viewport desktop --out /tmp/fire-desktop
 * node tools/qa_city_fire_1871.mjs --viewport mobile --out /tmp/fire-mobile
 * node tools/qa_city_fire_1871.mjs --root /path/to/site/4d --viewport both --stands dekoven,court
 * node tools/qa_city_fire_1871.mjs --self-test
 *
 * Reads an already-published mirror (tools/publish.sh); never publishes or changes data.
 * For each camera stand it sets the fire time with window.__chicago4d.fire.set (which sets
 * the hour and the day as well), runs the drawn fire on for a few seconds so its smoke and
 * sparks fill in, and writes a JPEG and a reading of the engine (buildings unburnt, burning,
 * collapsing, burnt; flames, smoke, lights) to report.json. A "before" frame at each stand is
 * the free-walk city at the scene's own hour. Stands are this tool's own (local east/north
 * metres, eye height above the datum); the jaunt's anchors are T-3691's.
 * Frame times are headless software-renderer timings and are reported as such, never as a
 * hardware claim.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { massOf, massEmitters, clearOf, compositionPrisms } from '../renderers/web/js/fire-mass.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');

/** The stands: where the eye is and what it looks at (local e, n, height in metres), and when. */
export const STANDS = [
  { id: 'dekoven', label: "DeKoven Street at 9:30 Sunday night: the O'Learys' block alight", at: '1871-10-08T21:30', eye: [-420, -2014, 4.2], target: [-300, -1960, 9] },
  { id: 'court', label: 'Clark and Washington at 1:45 Monday morning, across the Court House square', at: '1871-10-09T01:45', eye: [600, -402, 4.2], target: [500, -300, 14] },
  { id: 'courtstop', label: 'The Great Fire jaunt\'s Court House stop at 1:32 Monday morning (T-3802)', at: '1871-10-09T01:32', eye: [580, -408, 4.2], target: [516, -328, 18] },
  { id: 'courtnorth', label: 'The Court House from Clark and Randolph at 2:07 Monday morning, the Sherman House stop (T-3802)', at: '1871-10-09T02:07', eye: [592, -268, 4.2], target: [516, -330, 16] },
  { id: 'state', label: 'State Street at 3:00 Monday morning, the front coming up the street', at: '1871-10-09T03:00', eye: [860, -505, 4.2], target: [860, -300, 12] },
  { id: 'north', label: 'The North Side at noon Monday, the fire at North Avenue', at: '1871-10-09T12:00', eye: [427, 2380, 5], target: [424, 2640, 16] },
  { id: 'burnt', label: 'Washington Street on Tuesday morning, after the rain', at: '1871-10-10T08:30', eye: [440, -396, 4.2], target: [800, -380, 6] },
  { id: 'aerial', label: 'The city from the south-west at 1:45 Monday morning', at: '1871-10-09T01:45', eye: [-900, -2900, 320], target: [500, -200, 0] },
];

export function selfTest() {
  const ids = new Set(STANDS.map((s) => s.id));
  assert.equal(ids.size, STANDS.length);
  for (const s of STANDS) {
    assert.match(s.at, /^1871-10-(08|09|10)T\d{2}:\d{2}$/);
    assert.ok(s.at >= '1871-10-08T21:00', `${s.id} before the fire`);
    assert.ok(s.eye.length === 3 && s.target.length === 3 && [...s.eye, ...s.target].every(Number.isFinite));
  }
  assert.deepEqual(parseArgs(['--stands', 'court,state', '--viewport', 'mobile']).stands, ['court', 'state']);
  assert.throws(() => parseArgs(['--stands', 'nowhere']), /Unknown stand/);
  // T-3802 (the owner: "the fires sometimes appear above the building"): every named 1871
  // structure that burns and carries its composition keeps its flames on its own roofs and at
  // its own walls' windows, and its storeys are its main wall head's, not its tower's. The Court
  // House's pieces are per material, so its Lockport stone piece's box ran from the 1853 house to
  // the cupola's top (57 m): its whole plan read that tall, and the roof flames floated there.
  const fireDoc = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/fire/1871.json'), 'utf8'));
  let seed = 1, flamesChecked = 0, massed = 0;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
  for (const id of Object.keys(fireDoc.structures ?? {})) {
    const file = path.join(ROOT, 'data/sidecars/1871', `${id}.json`);
    if (!fs.existsSync(file)) continue;
    const prisms = compositionPrisms(JSON.parse(fs.readFileSync(file, 'utf8')), 0);
    const mass = prisms && massOf(prisms, 0);
    if (!mass) continue;
    massed++;
    const { roof, wins } = massEmitters(mass, rnd, { spacing: 1 });
    for (const e of [...roof, ...wins]) {
      const c = clearOf(e, mass);
      assert.ok(c.plan <= 2 && c.over <= 1, `${id}: a flame at (${e.x.toFixed(1)}, ${e.y.toFixed(1)}, ${e.z.toFixed(1)}) stands ${c.plan.toFixed(2)} m off and ${c.over.toFixed(2)} m over it`);
      flamesChecked++;
    }
    for (const e of wins) {
      assert.ok(e.y <= Math.max(...prisms.map((p) => p.wall)), `${id}: a window flame above every wall head`);
    }
    if (id === 'cook_county_court_house_1871') {
      assert.ok(mass.eave > 15 && mass.eave < 32, `the Court House's main wall head is its blocks' (${mass.eave.toFixed(1)} m), not the cupola's`);
      assert.ok(roof.every((e) => e.y < 40 || Math.hypot(e.x - (475.74 + 44.62), e.z + (-348.83 + 19.81)) < 8), 'a Court House roof flame over 40 m is on the cupola');
    }
  }
  assert.ok(massed >= 8, `the burning landmarks are massed from their compositions (${massed})`);
  // The old reading, caught: a roof flame at 0.97 x 0.8 of the cupola's height over a wing.
  const ch = compositionPrisms(JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1871/cook_county_court_house_1871.json'), 'utf8')), 0);
  const chMass = massOf(ch, 0);
  assert.ok(clearOf({ x: 475.74 + 15, y: 0.97 * 0.8 * 57, z: 348.83 - 20 }, chMass).over > 10, 'the bounding-box roof flame over the west wing is caught');
  assert.ok(clearOf({ x: 475.74 + 15, y: 10, z: 348.83 + 30 }, chMass).plan > 2, 'a flame in the air beside the building is caught');
  console.log(`CITY FIRE QA SELF-TEST PASS — ${STANDS.length} stands, each dated inside the fire; ${massed} burning landmarks keep their ${flamesChecked} flames on their own roofs and walls`);
}

function parseArgs(args) {
  const opts = { root: path.resolve(ROOT, '../../site/4d'), viewport: 'both', out: path.join(os.tmpdir(), `chicago-fire-1871-${Date.now()}`),
    stands: STANDS.map((s) => s.id), warm: 30, frames: 12, before: true, detail: null };
  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    if (key === '--no-before') { opts.before = false; continue; }
    if (!['--root', '--viewport', '--out', '--stands', '--warm', '--frames', '--detail'].includes(key) || !args[i + 1]) throw Error(`Unknown or incomplete option ${key}`);
    const value = args[++i];
    if (key === '--stands') {
      opts.stands = value.split(',');
      for (const id of opts.stands) if (!STANDS.some((s) => s.id === id)) throw Error(`Unknown stand ${id}`);
    } else if (key === '--warm' || key === '--frames') opts[key.slice(2)] = Number(value);
    else opts[key.slice(2)] = value;
  }
  if (!['mobile', 'desktop', 'both'].includes(opts.viewport)) throw Error('--viewport is mobile, desktop or both');
  opts.root = path.resolve(opts.root); opts.out = path.resolve(opts.out);
  return opts;
}

async function serverFor(root) {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2',
    '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.webmanifest': 'application/manifest+json' };
  const server = http.createServer((req, res) => {
    try {
      const url = new URL(req.url, 'http://local');
      let file = path.resolve(root, `.${decodeURIComponent(url.pathname)}`);
      if (file !== root && !file.startsWith(`${root}${path.sep}`)) throw Error('outside mirror');
      if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    } catch { res.writeHead(404); res.end('missing'); }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  return server;
}

function stand(spec) {
  const a = window.__chicago4d, { eye, target } = spec;
  a.setFly(true);
  a.walker.teleport({ local_e: eye[0], local_n: eye[1], altitude_m: eye[2],
    yaw_deg: Math.atan2(target[0] - eye[0], target[1] - eye[1]) * 180 / Math.PI,
    pitch_deg: Math.atan2(target[2] - eye[2], Math.hypot(target[0] - eye[0], target[1] - eye[1])) * 180 / Math.PI });
  a.step(); a.step();
}

async function run(opts) {
  if (!fs.existsSync(path.join(opts.root, '1871/index.html'))) throw Error(`Publish first: ${opts.root}/1871/index.html does not exist`);
  if (!fs.existsSync(path.join(opts.root, 'data/fire/1871.json'))) throw Error(`Publish first: ${opts.root}/data/fire/1871.json does not exist`);
  const require = createRequire(import.meta.url);
  const { chromium } = require('playwright');
  fs.mkdirSync(opts.out, { recursive: true });
  const report = { date: new Date().toISOString(), root: opts.root, method: 'Published /1871/ actual app; api.fire.set at each stand, the drawn fire run on with api.fire.warm; headless software renderer, so frame times are relative only.', viewports: [], failures: [] };
  const check = (ok, text) => { if (!ok) { report.failures.push(text); console.error(`FAIL ${text}`); } else console.log(`PASS ${text}`); };
  const server = await serverFor(opts.root);
  const launch = { args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--ignore-gpu-blocklist'] };
  const executablePath = process.env.PW_EXECUTABLE || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  if (executablePath) launch.executablePath = executablePath;
  const browser = await chromium.launch(launch);
  try {
    for (const vp of [{ name: 'mobile', width: 390, height: 780, detail: 'light' }, { name: 'desktop', width: 1280, height: 800, detail: 'full' }]
      .filter((v) => opts.viewport === 'both' || opts.viewport === v.name)) {
      const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1,
        isMobile: vp.name === 'mobile', hasTouch: vp.name === 'mobile', reducedMotion: 'reduce' });
      const page = await ctx.newPage(); page.setDefaultTimeout(600_000); // a shared, loaded machine draws a frame slowly
      const row = { viewport: vp, errors: [], failedResponses: [], stands: [] };
      report.viewports.push(row);
      page.on('pageerror', (error) => row.errors.push(error.message));
      page.on('console', (msg) => { if (/\[fire\]/.test(msg.text())) row.errors.push(msg.text()); });
      page.on('response', (response) => { if (response.status() >= 400) row.failedResponses.push({ url: response.url(), status: response.status() }); });
      const detail = opts.detail ?? vp.detail;
      await page.goto(`http://127.0.0.1:${server.address().port}/1871/?detail=${detail}&seed=3687`, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 300_000 });
      const bootError = await page.evaluate(() => window.__chicago4d?.error);
      if (bootError) throw Error(bootError);
      await page.waitForFunction(() => ['welcome', 'world'].includes(window.__chicago4d?.welcome?.state), null, { timeout: 90_000 });
      await page.evaluate(() => {
        const a = window.__chicago4d;
        if (a.welcome.state === 'welcome') a.welcome.enter('spawn');
        document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click();
        a.renderer.setAnimationLoop(null); a.setAnimationHold(true);
      });
      await page.waitForFunction(() => document.getElementById('gate')?.hidden === true, null, { timeout: 30_000 });
      await page.addScriptTag({ content: `window.__fireStand = ${stand.toString()};` });
      // The pointer hint is the visitor's, not the picture's.
      await page.addStyleTag({ content: '#look-tag{display:none!important}' });
      check(await page.evaluate(() => window.__chicago4d.fire?.time() === null), `${vp.name}: free walk is the city before the fire`);
      check(await page.evaluate(() => !performance.getEntriesByType('resource').some((r) => /city-fire\.js|fire\/1871\.json/.test(r.name))),
        `${vp.name}: free walk loads none of the fire`);
      for (const id of opts.stands) {
        const spec = STANDS.find((s) => s.id === id);
        const shot = (suffix) => path.join(opts.out, `${vp.name}-${spec.id}-${suffix}.jpg`);
        if (opts.before) {
          await page.evaluate(async () => { await window.__chicago4d.fire.set(null); });
          await page.evaluate((spec) => window.__fireStand(spec), spec);
          await page.screenshot({ path: shot('before'), type: 'jpeg', quality: 86 });
        }
        const snap = await page.evaluate(async ({ spec, warm }) => {
          const a = window.__chicago4d;
          await a.fire.set(spec.at);
          window.__fireStand(spec);
          a.fire.warm(warm);
          return a.fire.snapshot();
        }, { spec, warm: opts.warm });
        const timing = await page.evaluate((n) => {
          const a = window.__chicago4d, t = [];
          for (let i = 0; i < n; i++) { const t0 = performance.now(); a.fire.update(1 / 30, a.camera); a.step(); t.push(performance.now() - t0); }
          t.sort((x, y) => x - y);
          return { medianMs: +t[Math.floor(t.length / 2)].toFixed(1), stats: a.stats() };
        }, opts.frames);
        await page.screenshot({ path: shot('fire'), type: 'jpeg', quality: 86 });
        row.stands.push({ id: spec.id, label: spec.label, at: spec.at, snapshot: snap, timing });
        console.log(`${vp.name} ${spec.id} ${spec.at}: unburnt ${snap?.unburnt} burning ${snap?.burning} collapsing ${snap?.collapsing} burnt ${snap?.burnt}; flames ${snap?.fx?.flames} smoke ${snap?.fx?.smoke} plume ${snap?.plume} lights ${snap?.lights} sky ${snap?.sky}; ${timing.medianMs} ms/frame (software)`);
        check(snap && snap.iso === spec.at, `${vp.name} ${spec.id}: the fire time is ${spec.at}`);
        if (spec.id !== 'burnt') check((snap?.burning ?? 0) + (snap?.collapsing ?? 0) > 0 && (snap?.fx?.flames ?? 0) > 0, `${vp.name} ${spec.id}: buildings burning and flames drawn`);
        else check((snap?.burnt ?? 0) > 1000, `${vp.name} ${spec.id}: the district burnt`);
        for (const nb of snap?.named ?? []) if (nb.heat > 0.05) check(nb.clear && nb.clear.plan <= 2 && nb.clear.over <= 1,
          `${vp.name} ${spec.id}: ${nb.id}'s flames stand on it (${nb.clear?.plan} m off, ${nb.clear?.over} m over) (T-3802)`);
      }
      await page.evaluate(async () => { await window.__chicago4d.fire.set(null); });
      check(await page.evaluate(() => window.__chicago4d.fire.time() === null && window.__chicago4d.timeOfDay.current.hhmm === '16:00'),
        `${vp.name}: putting the fire out gives back the city and its afternoon`);
      check(!row.errors.length, `${vp.name}: no page errors (${row.errors.slice(0, 3).join(' | ')})`);
      check(!row.failedResponses.length, `${vp.name}: no failed requests (${row.failedResponses.slice(0, 3).map((r) => r.url).join(' ')})`);
      await ctx.close();
    }
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
  fs.writeFileSync(path.join(opts.out, 'report.json'), `${JSON.stringify(report, null, 1)}\n`);
  console.log(`${report.failures.length ? 'CITY FIRE QA FAIL' : 'CITY FIRE QA PASS'} — ${opts.out}`);
  if (report.failures.length) process.exitCode = 1;
}

if (process.argv.includes('--self-test')) selfTest();
else run(parseArgs(process.argv.slice(2))).catch((error) => { console.error(error); process.exit(1); });
