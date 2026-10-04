/**
 * WHAT A FRAME COSTS WHILE THE VISITOR IS MOVING — T-2096.
 *
 *   node tools/measure_walk_frames.mjs [--only desktop|mobile] [--tiers full,balanced,light]
 *                                      [--moves walk,turn,flight] [--year 1835]
 *                                      [--throttle 4] [--source] [--json f]
 *                                      [--sync] [--verify] [--gate]
 *
 * Every other frame budget in this project is read at a STAND: T-0135's five
 * cameras, T-1975's triangle ceilings, T-1976's light trim. A stand is a still
 * frame, and the owner's report (2026-10-04) was that WALKING is laggy. So this
 * drives fixed, scripted moves and reads every frame of them:
 *
 *   walk    Lake Street east from Canal at walking pace, then a right turn and
 *           on into the block — the town's busiest street and then a back lot.
 *   turn    a slow full turn in place at the Sauganash, 45° a second.
 *   flight  a pan over the town from the open aerial, 12 m a second.
 *   travel  T-2106: a ride on horseback from Lake at Canal to a point 120 m on
 *           along the walk's bearing, routed and paced by the page's own travel
 *           controller (`travelSimulate`), a 60 Hz frame at a time, to arrival.
 *
 * ## How a frame is timed, and what that reading can and cannot say
 *
 * The moves are DRIVEN rather than played: the animation clock is held, the
 * walker is teleported along the path one 60 Hz frame's travel at a time, and
 * the page's own `step()` runs one whole frame — the same `tick()` the
 * animation loop runs, with its flora, trees and render. `flora.update`,
 * `trees.update` and `renderer.render` are wrapped in `performance.now()` so the
 * frame splits into the layers named in the ticket, and "other" is the rest of
 * the tick (the walker, travel, reach, haze, HUD).
 *
 * The runner has no GPU. `renderer.render` here is SwiftShader rasterising on
 * the CPU, so its milliseconds are NOT what a phone's GPU spends — and at about
 * 200 ms a frame they would put one walk past a run's 600 s ceiling — so the
 * draw is SKIPPED while a move is driven, and `--render` puts it back (its
 * column is printed on its own and never folded into a verdict). The JavaScript columns
 * are real: they are the same code on a slower or faster core. That is why the
 * ticket's question — what does moving cost that standing does not — is
 * answered on `flora` and `scripted` (= the tick less the render), where the
 * renderer cannot hide it.
 *
 * The phone stand-in is the 390x780 touch viewport under Chrome's CPU throttle,
 * 4× by default: the factor Lighthouse's mobile preset uses for a mid-range
 * phone. An iPhone's core is faster than that preset assumes, so 4× is a
 * pessimistic stand-in and is chosen as one; `--throttle 1` reads it bare.
 *
 * T-2106: the moves are driven with the flora rebuild SPREAD over frames, as
 * the animation loop runs it (`setFloraSpread`); `--sync` reads the one-frame
 * pass every rebuild was before, and is the "before" of T-2106's reading.
 * `--verify` checks, after every move, that the pass the move left in flight
 * lands EXACTLY the plants a one-frame pass deals from the same camera: the
 * rebuild was spread, not changed.
 *
 * Defaults to the PUBLISHED mirror, as every renderer measurement here does.
 * `--gate` holds the result: `FLORA_MOVE_CEILING_MS` and `FLORA_MOVE_P95_MS`
 * below, per tier, on the desktop reading. It is a seven-minute browser run, so
 * it is NOT in check.sh: since T-2106 it is its own CI leg,
 * .github/workflows/chicago-4d-moving-frames.yml.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const wantSource = process.argv.includes('--source');
const GATE = process.argv.includes('--gate');
const jsonOut = argAt('--json');
const ONLY = argAt('--only');
const YEAR = argAt('--year') || '1835';
const TIERS = (argAt('--tiers') || 'full,balanced,light').split(',').map((s) => s.trim());
const MOVES = (argAt('--moves') || 'walk,turn,flight,travel').split(',').map((s) => s.trim());
const THROTTLE = Number(argAt('--throttle') || 4);
const RENDER = process.argv.includes('--render');
/** `--profile N`: a CPU profile over the moves, printing the N functions that
 *  spent the most self time — which line of the rebuild the time is in. */
const PROFILE = Number(argAt('--profile') || 0);
const SYNC = process.argv.includes('--sync');
const VERIFY = process.argv.includes('--verify');

/**
 * THE CEILINGS, T-2096 § 3, per tier, on the desktop viewport unthrottled —
 * the one reading on this runner that is not scaled by a throttle factor
 * somebody chose.
 *
 * `FLORA_MOVE_CEILING_MS` is the worst single frame flora's per-frame update
 * may spend while the visitor walks, turns, flies or rides. Before T-2096 those
 * worst frames read 70 ms at `full`, 46 at `balanced` and 31 at `light`; T-2105
 * took them to 38, 21 and 15 (docs/measurements/t-2096-walk-frames-*.json).
 * T-2106 spread the rebuilds over frames and they read 21, 12 and 9.4 on a
 * steward runner (docs/measurements/t-2106-walk-frames-after-desktop.json) —
 * each on the ride, whose near passes at a horse's pace are still one frame.
 *
 * THE CEILINGS ARE WRITTEN AGAINST THE RUNNER THAT ENFORCES THEM: the CI leg,
 * .github/workflows/chicago-4d-moving-frames.yml. Its first run on PR #436 read
 * the same moves about twice as slow (the page was ready in 169 s against 105;
 * the ride's worst frame at `full` 43.2 ms against 21) and failed six of the
 * ceilings first written from the steward reading. Its readings were 43.2,
 * 22.6 and 14.8 worst and 10.7, 6.3 and 4.4 at p95; each ceiling below is that
 * with about forty per cent on top, because a single frame is the noisiest
 * number a shared runner reads.
 *
 * `FLORA_MOVE_P95_MS` is the 95th-percentile flora frame of every move, and it
 * is what holds T-2106's gain: a turn read 26, 16 and 11 ms at p95 on the
 * steward runner with each pass taken in one frame, against 6.2, 4.1 and 4.1
 * spread — the same fourfold gap on a runner twice as slow puts a one-frame
 * rebuild far over these, however its worst frame reads.
 */
const FLORA_MOVE_CEILING_MS = { full: 60, balanced: 32, light: 21 };
const FLORA_MOVE_P95_MS = { full: 15, balanced: 9, light: 7 };

const VIEWPORTS = [
  { id: 'desktop', width: 1280, height: 800, touch: false, scale: 1, throttle: 1 },
  { id: 'mobile', width: 390, height: 780, touch: true, scale: 1.5, throttle: THROTTLE },
].filter((v) => !ONLY || v.id === ONLY);

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
  '.webp': 'image/webp', '.ktx2': 'image/ktx2',
};
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
const PORT = Number(process.env.WALK_FRAMES_PORT || 4201);
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}, year ${YEAR}`);

/** Runs in the page: drive one move at one tier and time every frame of it. */
async function driveMove({ move, tier, render, profile, sync, verify }) {
  const a = window.__chicago4d;
  // A tier change REPLACES the flora and trees rigs (main.js applyDetail), so
  // the hooks are wrapped on the objects that exist once it has settled.
  await a.setDetail(tier);
  // T-2106: `step()` spreads the near rebuild as the animation loop does, or
  // with `--sync` pays for each pass in the frame that needs it.
  const spreading = !sync && a.setFloraSpread?.(true) === true;
  const now = () => performance.now();
  // The per-frame hooks `tick()` calls on the layers, each timed on its own.
  const HOOKS = [['flora', 'update'], ['trees', 'update'], ['terrain', 'update'],
    ['terrain', 'updateGroundReach'], ['world', 'aim'], ['terrain', 'setHaze'],
    ['renderer', 'render']];
  const t = {};
  const wrap = (obj, key, slot) => {
    const orig = obj?.[key];
    if (typeof orig !== 'function') return () => {};
    t[slot] = 0;
    obj[key] = function wrapped(...args) {
      const t0 = now();
      try { return orig.apply(this, args); } finally { t[slot] += now() - t0; }
    };
    return () => { obj[key] = orig; };
  };
  const undo = HOOKS.map(([o, k]) => wrap(a[o], k, `${o}.${k}`));
  // Without `--render` the draw itself is skipped while the move is driven: on
  // SwiftShader it is ~200 ms of CPU rasterising per frame, which says nothing
  // about a phone's GPU and would put a 40 m walk past the 600 s ceiling.
  if (!render) {
    const timed = a.renderer.render;
    a.renderer.render = () => {};
    undo.unshift(() => { a.renderer.render = timed; });
  }
  const anchors = new Map((a.scene?.anchors ?? []).map((x) => [x.id, x]));
  const pick = (...ids) => ids.map((id) => anchors.get(id)).find(Boolean)
    ?? a.scene?.anchors?.[0];
  const rad = (d) => d * Math.PI / 180;
  const FPS = 60;
  const path = [];
  if (move === 'walk') {
    // Walking pace is the walker's own, read from its budget rather than copied.
    const v = a.walkBudget?.speed ?? 1.4;
    const s = pick('lake_at_canal', 'spawn');
    let e = s.local_e, n = s.local_n, b = s.yaw_deg ?? 90;
    const legs = [[40, b], [14, b + 90]];
    for (const [len, bearing] of legs) {
      const frames = Math.round(len / v * FPS);
      for (let i = 0; i < frames; i++) {
        e += Math.sin(rad(bearing)) * v / FPS; n += Math.cos(rad(bearing)) * v / FPS;
        path.push({ local_e: e, local_n: n, yaw_deg: bearing });
      }
    }
  } else if (move === 'turn') {
    const s = pick('lake_market', 'lake_at_canal', 'spawn');
    for (let i = 0; i < 8 * FPS; i++) {
      path.push({ local_e: s.local_e, local_n: s.local_n, yaw_deg: (s.yaw_deg ?? 0) + i * 45 / FPS });
    }
  } else if (move === 'flight') {
    const s = pick('from_above', 'aerial');
    const alt = s.altitude_m ?? 120;
    for (let i = 0; i < 6 * FPS; i++) {
      path.push({ local_e: s.local_e + i * 12 / FPS, local_n: s.local_n,
        yaw_deg: s.yaw_deg ?? 0, altitude_m: alt, pitch_deg: s.pitch_deg ?? -30 });
    }
  }
  if (move === 'travel') {
    // Driven below, frame by frame: the route is the router's, not ours.
    const s = pick('lake_at_canal', 'spawn');
    const b = rad(s.yaw_deg ?? 90);
    path.push({ local_e: s.local_e, local_n: s.local_n, yaw_deg: s.yaw_deg ?? 90 });
    path.target = { kind: 'intersection', local_e: s.local_e + Math.sin(b) * 120,
      local_n: s.local_n + Math.cos(b) * 120 };
  }
  a.setFly(move === 'flight');
  a.walker.teleport(path[0]);
  a.setAnimationHold(true);
  // Let the tier's own rebuild and any first-sight upload land before reading.
  for (let i = 0; i < 4; i++) a.step();
  await new Promise((r) => setTimeout(r, 300));
  const rebuilds0 = a.flora.stats?.rebuilds ?? 0;
  const spread0 = { ...(a.flora.stats?.spread ?? {}) };
  // T-2096 § acceptance, "no visible change in where plants stand": a digest of
  // every instance buffer the flora layer holds, taken along the move, so two
  // builds can be compared plant for plant (`--json` keeps them).
  const digest = () => {
    let h = 0x811c9dc5;
    a.flora.group.traverse((o) => {
      if (!o.isInstancedMesh) return;
      const mix = (x) => { h = Math.imul(h ^ x, 0x01000193) >>> 0; };
      mix(o.count);
      for (const attr of [o.instanceMatrix, ...Object.values(o.geometry.attributes)
        .filter((x) => x.isInstancedBufferAttribute)]) {
        const arr = attr.array;
        const n = Math.min(arr.length, o.count * attr.itemSize);
        const u = new Uint32Array(arr.buffer, arr.byteOffset, (n * arr.BYTES_PER_ELEMENT) >> 2);
        for (let i = 0; i < u.length; i++) mix(u[i]);
      }
    });
    return h.toString(16);
  };
  const digests = [];
  const rows = [];
  // A digest is taken between passes, never across one in flight: a spread
  // pass has written part of its sets and committed none of them.
  let digestDue = false;
  // Only the driven frames are profiled, not the settling between moves.
  if (profile) console.profile(`${tier}/${move}`);
  const travelling = move === 'travel';
  if (travelling) {
    a.setTravelMode('horse');
    a.goToTarget(path.target);
  }
  const frames = travelling ? 1800 : path.length;
  for (let i = 0; i < frames; i++) {
    if (travelling) {
      if (a.travelState.phase === 'idle') break;
      a.travelSimulate(1 / 60, 1 / 60);
    } else {
      a.walker.teleport(path[i]);
    }
    for (const k in t) t[k] = 0;
    const t0 = now();
    a.step();
    rows.push({ frame: now() - t0, ...t });
    if (rows.length % 150 === 0) digestDue = true;
    if (digestDue && !a.flora.inFlight?.()) {
      if (profile) console.profileEnd(`${tier}/${move}`);
      digests.push(digest());
      digestDue = false;
      if (profile && rows.length < frames) console.profile(`${tier}/${move}`);
    }
  }
  if (profile) console.profileEnd(`${tier}/${move}`);
  a.flora.settle?.();
  digests.push(digest());
  // T-2106 `--verify`: each pass's last spread landing, dealt again in ONE
  // frame from the camera it started at, must put the same plants in the same
  // slots — the near rings (`rebuildAll`) and the far shrubs with their carries
  // (`rebuildFarShrubs`) each against their own sets.
  let verified = null;
  const FAR = ['flora-shrub-far', 'flora-near-carry', 'flora-mid-carry'];
  const ofPass = { near: (o) => !FAR.includes(o.name), far: (o) => FAR.includes(o.name) };
  const passDigest = (kind) => {
    let h = 0x811c9dc5;
    const mix = (x) => { h = Math.imul(h ^ x, 0x01000193) >>> 0; };
    a.flora.group.traverse((o) => {
      if (!o.isInstancedMesh || !ofPass[kind](o)) return;
      mix(o.count);
      for (const attr of [o.instanceMatrix, ...Object.values(o.geometry.attributes)
        .filter((x) => x.isInstancedBufferAttribute)]) {
        const arr = attr.array;
        const n = Math.min(arr.length, o.count * attr.itemSize);
        const u = new Uint32Array(arr.buffer, arr.byteOffset, (n * arr.BYTES_PER_ELEMENT) >> 2);
        for (let i = 0; i < u.length; i++) mix(u[i]);
      }
    });
    return h.toString(16);
  };
  // An inert rig (a year with nothing planted) has no passes to compare.
  const sp = a.flora.stats?.spread;
  if (verify && spreading && sp) {
    // Only a landing still on its sets: a one-frame rebuild after it (a
    // dropped pass, a flight's step) would be compared with the wrong pose.
    const kinds = ['near', 'far'].filter((k) => sp.last[k]?.camera
      && sp.last[k].pass === sp.passes[k]);
    const spreadDigests = Object.fromEntries(kinds.map((k) => [k, passDigest(k)]));
    verified = {};
    for (const k of kinds) {
      const cam = a.camera.clone();
      const [x, y, z, qx, qy, qz, qw] = sp.last[k].camera;
      cam.quaternion.set(qx, qy, qz, qw);
      cam.position.set(x + 500, y, z);
      cam.updateMatrixWorld(true);
      a.flora.update(0, cam);
      cam.position.set(x, y, z);
      cam.updateMatrixWorld(true);
      a.flora.update(0, cam);
      const one = passDigest(k);
      verified[k] = { spread: spreadDigests[k], sync: one, same: spreadDigests[k] === one };
    }
  }
  if (spreading) a.setFloraSpread(false);
  const s1 = a.flora.stats?.spread ?? {};
  const spread = spreading ? {
    landings: (s1.landings ?? 0) - (spread0.landings ?? 0),
    drained: (s1.drained ?? 0) - (spread0.drained ?? 0),
    abandoned: (s1.abandoned ?? 0) - (spread0.abandoned ?? 0),
    framesPerPass: ((s1.frames ?? 0) - (spread0.frames ?? 0))
      / Math.max(1, (s1.landings ?? 0) - (spread0.landings ?? 0)),
  } : null;
  const rebuilds = (a.flora.stats?.rebuilds ?? 0) - rebuilds0;
  a.setAnimationHold(false);
  for (const u of undo) u();
  const col = (k) => rows.map((r) => r[k] ?? 0).sort((x, y) => x - y);
  const q = (xs, p) => xs[Math.min(xs.length - 1, Math.floor(p * xs.length))];
  const sum = (xs) => xs.reduce((s, x) => s + x, 0);
  const describe = (xs) => ({ median: q(xs, 0.5), p95: q(xs, 0.95), p99: q(xs, 0.99),
    max: xs[xs.length - 1], mean: sum(xs) / xs.length,
    over16: xs.filter((x) => x > 16.7).length, over33: xs.filter((x) => x > 33).length,
    over50: xs.filter((x) => x > 50).length });
  // `scripted` is the frame less the draw: everything the page's own JavaScript
  // spent, which is the part of the frame this runner can honestly read.
  const scripted = rows.map((r) => r.frame - (r['renderer.render'] ?? 0)).sort((x, y) => x - y);
  return {
    frames: rows.length, rebuilds, digests, spread, verified,
    scripted: describe(scripted),
    layers: Object.fromEntries(Object.keys(t).map((k) => [k, describe(col(k))])),
    heapMB: performance.memory ? performance.memory.usedJSHeapSize / 1048576 : null,
  };
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const out = { year: YEAR, source: wantSource ? 'source' : 'published', throttle: THROTTLE,
  rebuild: SYNC ? 'sync' : 'spread',
  ceilingMs: FLORA_MOVE_CEILING_MS, p95CeilingMs: FLORA_MOVE_P95_MS, readings: [] };
let failed = 0;
function writeJson() {
  fs.mkdirSync(path.dirname(jsonOut), { recursive: true });
  fs.writeFileSync(jsonOut, `${JSON.stringify(out, (k, v) => (typeof v === 'number'
    ? Math.round(v * 100) / 100 : v), 2)}\n`);
}
for (const vp of VIEWPORTS) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height },
    hasTouch: vp.touch, deviceScaleFactor: vp.scale });
  const page = await ctx.newPage();
  page.setDefaultTimeout(480_000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  const t0 = Date.now();
  await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 480_000 });
  const gateBtn = await page.$('#gate button, .gate button');
  if (gateBtn) { await gateBtn.click(); await page.waitForTimeout(800); }
  console.log(`\n${vp.id} ${vp.width}x${vp.height} — ready in ${((Date.now() - t0) / 1000).toFixed(0)} s` +
    (vp.throttle > 1 ? `, CPU throttled ${vp.throttle}×` : ''));
  if (vp.throttle > 1) {
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: vp.throttle });
  }
  let prof = null;
  if (PROFILE) {
    prof = await ctx.newCDPSession(page);
    await prof.send('Profiler.enable');
    await prof.send('Profiler.setSamplingInterval', { interval: 200 });
    prof.profiles = [];
    prof.on('Profiler.consoleProfileFinished', (ev) => prof.profiles.push(ev.profile));
  }
  console.log('tier      move    frames rebuilds | scripted ms med/p95/max  >16 >33 >50 | flora p95/max | trees p95/max | other hooks max');
  for (const tier of TIERS) {
    for (const move of MOVES) {
      const r = await page.evaluate(driveMove, { move, tier, render: RENDER, profile: PROFILE > 0,
        sync: SYNC, verify: VERIFY });
      const f = (x) => x.toFixed(1).padStart(5);
      const n = (x) => String(x).padStart(3);
      const L = r.layers;
      const others = Object.entries(L)
        .filter(([k, d]) => !['flora.update', 'trees.update', 'renderer.render'].includes(k) && d.max >= 1)
        .map(([k, d]) => `${k} ${d.max.toFixed(1)}`).join(', ');
      console.log(`${tier.padEnd(9)} ${move.padEnd(7)} ${String(r.frames).padStart(6)} ${String(r.rebuilds).padStart(8)} |`
        + ` ${f(r.scripted.median)} ${f(r.scripted.p95)} ${f(r.scripted.max)} ${n(r.scripted.over16)} ${n(r.scripted.over33)} ${n(r.scripted.over50)} |`
        + ` ${f(L['flora.update'].p95)} ${f(L['flora.update'].max)} | ${f(L['trees.update'].p95)} ${f(L['trees.update'].max)} | ${others || '-'}`
        + (r.spread ? ` | spread ${r.spread.landings} passes, ${r.spread.framesPerPass.toFixed(1)} frames each, ${r.spread.drained} finished early, ${r.spread.abandoned} dropped` : ''));
      for (const [k, v] of Object.entries(r.verified ?? {})) {
        console.log(`  verify ${k}: the spread pass ${v.same ? 'IS' : 'IS NOT'} the one-frame pass (${v.spread} / ${v.sync})`);
        if (!v.same) failed++;
      }
      out.readings.push({ viewport: vp.id, throttle: vp.throttle, tier, move, ...r });
      // Written after every reading: a run that meets the 600 s ceiling keeps
      // what it had read rather than losing the lot.
      if (jsonOut) writeJson();
      const worst = L['flora.update'].max;
      const ceiling = FLORA_MOVE_CEILING_MS[tier];
      if (GATE && vp.throttle === 1 && ceiling && worst > ceiling) {
        console.log(`  FAIL flora's worst moving frame ${worst.toFixed(1)} ms > ${tier}'s ceiling ${ceiling} ms`);
        failed++;
      }
      const p95 = L['flora.update'].p95;
      const p95Ceiling = FLORA_MOVE_P95_MS[tier];
      if (GATE && vp.throttle === 1 && p95Ceiling && p95 > p95Ceiling) {
        console.log(`  FAIL flora's p95 moving frame ${p95.toFixed(1)} ms > ${tier}'s p95 ceiling ${p95Ceiling} ms`);
        failed++;
      }
    }
  }
  if (prof) {
    await new Promise((r) => setTimeout(r, 500));
    const self = new Map();
    for (const profile of prof.profiles) {
      const dt = profile.timeDeltas;
      const byId = new Map(profile.nodes.map((nd) => [nd.id, nd]));
      profile.samples.forEach((id, i) => {
        const cf = byId.get(id).callFrame;
        const key = `${cf.functionName || '(anon)'} ${path.basename(cf.url)}:${cf.lineNumber + 1}`;
        self.set(key, (self.get(key) ?? 0) + (dt[i] ?? 0) / 1000);
      });
    }
    console.log(`\nself time, top ${PROFILE} (ms, over every move above):`);
    for (const [k, ms] of [...self].sort((x, y) => y[1] - x[1]).slice(0, PROFILE)) {
      console.log(`  ${ms.toFixed(0).padStart(7)}  ${k}`);
    }
  }
  if (errors.length) {
    console.log(`pageerrors: ${JSON.stringify(errors.slice(0, 5))}`);
    failed++;
  }
  await ctx.close();
}
await browser.close();
server.close();
if (jsonOut) console.log(`\nwrote ${jsonOut}`);
if (VERIFY && !GATE) {
  console.log(failed ? `\nFAIL — ${failed} move(s) failed verification or threw` : '\nPASS — every spread pass landed the one-frame pass');
  process.exit(failed ? 1 : 0);
}
if (GATE) {
  console.log(failed ? `\nFAIL — ${failed} reading(s) over the moving-frame ceiling` : '\nPASS — every moving frame inside the ceiling');
  process.exit(failed ? 1 : 0);
}
