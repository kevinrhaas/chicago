/**
 * WHAT A FRAME COSTS WHILE THE VISITOR IS MOVING — T-2096.
 *
 *   node tools/measure_walk_frames.mjs [--only desktop|mobile] [--tiers full,balanced,light]
 *                                      [--moves walk,turn,flight] [--year 1835]
 *                                      [--throttle 4] [--source] [--json f]
 *                                      [--sync] [--verify] [--gate] [--xray]
 *                                      [--sward grid|scan|both] [--profile N]
 *   node tools/measure_walk_frames.mjs --live [--only mobile] [--tiers light]
 *                                      [--seconds 12] [--stills] [--json f]
 *                                      [--gl swiftshader|llvmpipe] [--no-gaze] [--profile N]
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
 * T-2717: each move also prints its `near re-deal` line — the near passes and
 * each one's main-thread ms, and where the GPU draws the near ring (T-2716), its
 * deal passes, tile builds and uploads (`flora.nearDraw.stats`) — so the near
 * ring's share of a moving frame is read on its own (docs/RENDERING.md App. B).
 * T-2774: and the read-backs its heads and census are reaped from, with the
 * main thread's ms asking and reaping them.
 *
 * T-2106: the moves are driven with the flora rebuild SPREAD over frames, as
 * the animation loop runs it (`setFloraSpread`); `--sync` reads the one-frame
 * pass every rebuild was before, and is the "before" of T-2106's reading.
 * `--verify` checks, after every move, that the pass the move left in flight
 * lands EXACTLY the plants a one-frame pass deals from the same camera: the
 * rebuild was spread, not changed.
 * T-2695: and that the zone answers the job pool's workers give a spread pass
 * (jobs/zone-kernel.js) are the page's own finder's, at 20,000 points over the
 * measured grid and its edge (`flora.checkHeldZones`).
 * T-2696: and so are the water, floor, verge band and height those workers
 * answer beside the zones (flora-ground.js), at the same points and as many
 * again near footprints and street lines, the height to the last bit.
 *
 *
 * T-2606 `--sward`: which of the yards' two sward tests the page's slots ask
 * while a move is driven (the tier's own rebuild included). `grid`, the
 * default, is the page as it ships: the 16 m cells T-2696 filed the yards in
 * (yards.js `swardGrid`). `scan` puts back the full walk over every interior's
 * box (`suppressesSwardScan`), so `--profile` can read the test's cost before
 * and after on the same tree. `both` asks the two at EVERY slot the moves ask,
 * hands the page the grid's answer, and fails the run if any slot is answered
 * differently — where `--verify`'s 20,000 points are a sample over the boxes.
 * It doubles the test's cost, so its frame times are not a reading.
 * Readings: docs/measurements/t-2606-sward-test-mobile.json (the scan 14.9 and
 * 18.3 s of a walk and turn's profile at 4x/390x780, the grid 0.13 and 0.18 s;
 * 2,215,145 slots asked over every tier and move, 0 answered differently).
 *
 * Defaults to the PUBLISHED mirror, as every renderer measurement here does.
 * `--gate` holds the result: `FLORA_MOVE_CEILING_MS` and `FLORA_MOVE_P95_MS`
 * below, per tier, on the desktop reading. It is a seven-minute browser run, so
 * it is NOT in check.sh: since T-2106 it is its own CI leg,
 * .github/workflows/chicago-4d-moving-frames.yml.
 *
 * ## `--live`: the frame the visitor gets, governed and Fixed (T-2555)
 *
 * The driven moves above cannot see the frame governor: they call `step()`,
 * which bypasses the animation loop the governor sits in, and they skip the
 * draw, which is the cost the governor trims. So `--live` drives each move
 * through the page's OWN loop instead — the walker posed from the wall clock on
 * every rAF, the draw on — for `--seconds` of real time, once with Frame
 * pacing at Adaptive and once at Fixed (Fixed is the renderer as it was before
 * T-2555: the Sharpness ratio, every rAF, a shadow every frame). The reading is
 * the interval between drawn frames: its standard deviation and p95, which are
 * what "uneven" means. On this runner the draw is SwiftShader rasterising on
 * the CPU, whose cost goes as the pixels drawn, so the comparison is real but
 * it is a software rasteriser's, not a phone GPU's: the two modes are read in
 * the same page, minutes apart, and only their DIFFERENCE is the finding.
 *
 * `--stills` then asks the other half of the claim at every anchor of the year
 * (`--moves none` asks only it): with the governor put where a slow moving
 * window puts it — this runner's frames are too slow to drive it there, see
 * T-2592 — the loop's own still frames put the ratio back at the ceiling with a
 * shadow every frame, and the held frame captured under Adaptive is the same
 * signature as the one captured under Fixed.
 *
 * ## `--gl llvmpipe`: a software stand-in weighed, and rejected (T-2721)
 *
 * T-2592 asked for the governor's moving reading and found this runner's
 * SwiftShader frames seconds apart. Mesa's llvmpipe is the other software
 * rasteriser here (`--gl llvmpipe` = ANGLE on EGL; every reading now prints and
 * records the rasteriser that drew it), multithreaded and usually the faster,
 * so it was read as a stand-in before anything was read with it
 * (docs/measurements/t-2721-live-llvmpipe-mobile*.json, phone profile, light):
 *
 *   - A live frame comes about every 1.0 to 1.5 s, and still every 0.9 to
 *     1.3 s with the gaze target's pick held off (`--no-gaze`). The governor
 *     acts between 18 and 38 ms and reads any interval over 250 ms as a gap, so
 *     every frame here is a gap: it made no decision in any of the twelve
 *     readings (ratio held at 1.00), and whatever Adaptive against Fixed shows
 *     is noise at 8 to 14 frames a move (sd and p95 "fell" on one move of three
 *     with the pick on, two with it off). Rejected: the reading needs hardware
 *     whose frame costs tens of milliseconds, which is T-2722.
 *   - `--profile` over the live moves put 63 s of 72 in `readPixels`, called
 *     from gpu-pick.js through target.js's look: the gaze target's one-pixel
 *     pick waits for the GPU to finish the frame before it, on the main thread,
 *     every 500 ms of movement. That is the runner's multi-second frame, and on
 *     any device a stall the governor cannot remove (T-2723). T-2723 reads that
 *     pick back behind a fence instead (gpu-pick.js `gpuPickAsync`): on the
 *     desktop profile `readPixels` went from 41 s of the moves to none, and the
 *     frame interval did not move — the software draw is the floor here.
 *   - The pick's own `renderer.render` calls into its 1x1 target were counted
 *     as frames until this: only a draw to the canvas is one now, and the rest
 *     are reported as `offscreen`.
 *
 * ## The same reading on a phone (T-2732)
 *
 * The owner chose to take T-2722's reading on his own phone (T-2733). The page
 * carries it as Settings → Performance → Read frame pacing on the dev preview
 * (or with `?pacing=read`): `renderers/web/js/pacing-read.js` drives the moves
 * `driveLive` below drives, with its poses, tier and arithmetic (`summarise`),
 * and prints a block to copy back. Change one and change the other.
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
/** T-2606 `--sward grid|scan|both` (see the header). */
const SWARD = argAt('--sward') || 'grid';
if (!['grid', 'scan', 'both'].includes(SWARD)) throw new Error(`--sward ${SWARD}: one of grid, scan, both`);
const LIVE = process.argv.includes('--live');
const STILLS = process.argv.includes('--stills');
const SECONDS = Number(argAt('--seconds') || 12);
/** T-2646 `--xray`: every move driven with the Confidence view on at X-RAY —
 *  Inferred ghosted at 50 %, Reconstructed at 25 % — so its two-pass draw is
 *  in the frame the moves time. */
const XRAY = process.argv.includes('--xray');
/** T-2721 `--no-gaze` (with `--live`): the gaze target's GPU pick held off. */
const NO_GAZE = process.argv.includes('--no-gaze');
/** T-2592 `--gl llvmpipe`: draw with Mesa's llvmpipe (ANGLE on EGL) instead of
 *  SwiftShader. See § `--gl llvmpipe` above for why it is the stand-in. */
const GL = argAt('--gl') || 'swiftshader';
const GL_ARGS = {
  swiftshader: ['--enable-unsafe-swiftshader'],
  llvmpipe: ['--use-angle=gl-egl', '--ignore-gpu-blocklist'],
};
if (!GL_ARGS[GL]) throw new Error(`--gl ${GL}: one of ${Object.keys(GL_ARGS).join(', ')}`);

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
async function driveMove({ move, tier, render, profile, sync, verify, xray, sward }) {
  const a = window.__chicago4d;
  // T-2606 `--sward`: which sward test the slots ask, installed before the tier
  // change so its rebuild asks it too. main.js reads `yards.suppressesSward`
  // at every slot, so swapping the property is enough.
  const yards = a.yards;
  const swardShipped = yards?.suppressesSward;
  const scan = yards?.suppressesSwardScan;
  const swardEvery = sward === 'both' && scan ? { asked: 0, suppressed: 0, differ: 0, first: [] } : null;
  if (sward === 'scan' && scan) yards.suppressesSward = scan;
  if (swardEvery) {
    yards.suppressesSward = (e, n) => {
      const got = swardShipped(e, n);
      const want = scan(e, n);
      swardEvery.asked++;
      if (want) swardEvery.suppressed++;
      if (got !== want) {
        swardEvery.differ++;
        if (swardEvery.first.length < 5) swardEvery.first.push({ e, n, got, want });
      }
      return got;
    };
  }
  // A tier change REPLACES the flora and trees rigs (main.js applyDetail), so
  // the hooks are wrapped on the objects that exist once it has settled.
  await a.setDetail(tier);
  if (xray) {
    a.setConfidenceView(true);
    a.confidence.setGrade('inferred', { mode: 'ghost', opacity: 0.5 });
    a.confidence.setGrade('reconstructed', { mode: 'ghost', opacity: 0.25 });
  }
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
  if (spread0.slots) spread0.slots = { ...spread0.slots }; // T-2696: counted in place
  spread0.passes = { ...(spread0.passes ?? {}) }; // counted in place, so copied
  // T-2717: the near ring's own re-deal. Each near pass's main-thread ms (a
  // spread pass's from its landing record, a one-frame pass's as the frame's
  // flora ms, which is all it can be told apart by), and where the GPU draws the
  // near tufts (T-2716) what its deal pass, tile builds and uploads spent.
  const nearStats = a.flora.nearDraw?.stats;
  const nearDraw0 = nearStats ? { ...nearStats } : null;
  const nearMs = [];
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
  const longs = [];
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
    // T-2604: the page's own loop gives the event loop a turn between frames, and
    // a spread flora pass's walk comes back from its worker in one. Driven back to
    // back, no reply could ever land and every such pass would finish late, in
    // the frame — so a driven move yields between frames too. Outside the timing.
    if (a.jobs?.mode === 'workers') await new Promise((r) => setTimeout(r, 0));
    for (const k in t) t[k] = 0;
    const sp0 = a.flora.stats?.spread;
    const before = sp0 && [sp0.passes.near + sp0.passes.far, sp0.landings, sp0.drained];
    const sp0Near = sp0?.passes.near ?? 0;
    const t0 = now();
    a.step();
    const sp1 = a.flora.stats?.spread;
    // T-2683: what kind of pass a frame finished, so a long one can be named:
    // `one-frame` (dealt where it was needed), `drained` (a spread pass
    // finished late) or `landed` (a spread pass landing on time).
    const kind = !before ? null
      : sp1.drained > before[2] ? 'drained'
        : sp1.landings > before[1] ? 'landed'
          : sp1.passes.near + sp1.passes.far > before[0] ? 'one-frame' : null;
    rows.push({ frame: now() - t0, ...t });
    if (before && sp1.passes.near > sp0Near) {
      const last = sp1.last?.near;
      nearMs.push(sp1.landings > before[1] && last?.pass === sp1.passes.near ? last.ms
        : (t['flora.update'] ?? 0));
    }
    // T-2605: a frame over 50 ms is named — its index along the move, its flora
    // milliseconds and what the spread passes had done by then — because a count
    // of them cannot say WHICH pass it was. That is how the walk's grade-change
    // re-deal was told apart from its right turn's.
    if (rows[rows.length - 1].frame > 50) {
      const sp = sp1 ?? {};
      longs.push({ frame: i, ms: Math.round(rows[rows.length - 1].frame * 10) / 10,
        flora: Math.round((t['flora.update'] ?? 0) * 10) / 10, pass: kind,
        landings: sp.landings, drained: sp.drained, abandoned: sp.abandoned });
    }
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
  // Put back before the checks below: `checkSwardGrid` asks the property too.
  if (yards && swardShipped) yards.suppressesSward = swardShipped;
  // T-2106 `--verify`: each pass's last spread landing, dealt again in ONE
  // frame from the camera it started at, must put the same plants in the same
  // slots — the near rings (`rebuildAll`) and the far shrubs with their carries
  // (`rebuildFarShrubs`) each against their own sets.
  let verified = null;
  // T-2695: and the zone answers a spread pass's walks bring home from the job
  // pool, held against the page's own finder over the whole measured grid.
  const heldZones = verify ? a.flora.checkHeldZones?.(20000) ?? null : null;
  // T-2696: and the yards' bucketed sward test against its full walk.
  const swardGrid = verify ? a.yards?.checkSwardGrid?.(20000) ?? null : null;
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
    // T-2774: the near heads hang off a read-back the frame loop does not wait
    // for; the landed pass's own is taken now, as the one-frame pass takes it.
    a.flora.nearDraw?.flush?.();
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
    // T-2604: what a landed pass spent on the main thread, and the frames the
    // passes let go by while a walk was on a worker.
    msPerPass: ((s1.ms ?? 0) - (spread0.ms ?? 0))
      / Math.max(1, (s1.landings ?? 0) - (spread0.landings ?? 0)),
    waits: (s1.waits ?? 0) - (spread0.waits ?? 0),
    // T-2696: of the slots the passes dealt off the pool, the share whose
    // worker answers (zones; water, floor, verge and height) were home in time.
    slots: s1.slots ? {
      dealt: s1.slots.dealt - (spread0.slots?.dealt ?? 0),
      zoned: s1.slots.zoned - (spread0.slots?.zoned ?? 0),
      grounded: s1.slots.grounded - (spread0.slots?.grounded ?? 0),
    } : null,
    // T-2683: the passes a snap turn or an arrival started, dealt over frames
    // where they used to be dealt in one.
    jumps: (s1.jumps ?? 0) - (spread0.jumps ?? 0),
    jumpFrames: (s1.jumpFrames ?? 0) - (spread0.jumpFrames ?? 0),
    // And the passes still dealt whole in the frame that needed them: every
    // pass counted that did not land as a spread or jump pass.
    oneFrame: ((s1.passes?.near ?? 0) + (s1.passes?.far ?? 0))
      - ((spread0.passes?.near ?? 0) + (spread0.passes?.far ?? 0))
      - ((s1.landings ?? 0) - (spread0.landings ?? 0)),
  } : null;
  const rebuilds = (a.flora.stats?.rebuilds ?? 0) - rebuilds0;
  const nearSorted = nearMs.slice().sort((x, y) => x - y);
  const near = {
    passes: nearMs.length,
    median: nearSorted[Math.floor(nearSorted.length / 2)] ?? 0,
    max: nearSorted[nearSorted.length - 1] ?? 0,
    ms: nearMs.reduce((x, y) => x + y, 0),
    gpu: nearDraw0 ? Object.fromEntries(Object.keys(nearDraw0)
      .map((k) => [k, nearStats[k] - nearDraw0[k]])) : null,
  };
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
    frames: rows.length, rebuilds, digests, spread, near, verified, heldZones, swardGrid, swardEvery, longs,
    scripted: describe(scripted),
    layers: Object.fromEntries(Object.keys(t).map((k) => [k, describe(col(k))])),
    heapMB: performance.memory ? performance.memory.usedJSHeapSize / 1048576 : null,
  };
}

/** Runs in the page (T-2555): one move through the animation loop itself, for
 *  `seconds` of wall clock, with Frame pacing at `mode`, timing every draw. */
async function driveLive({ move, tier, mode, seconds, xray, profile, noGaze }) {
  const a = window.__chicago4d;
  await a.setDetail(tier);
  a.setGovernor(mode === 'adaptive');
  if (xray) {
    a.setConfidenceView(true);
    a.confidence.setGrade('inferred', { mode: 'ghost', opacity: 0.5 });
    a.confidence.setGrade('reconstructed', { mode: 'ghost', opacity: 0.25 });
  }
  const anchors = new Map((a.scene?.anchors ?? []).map((x) => [x.id, x]));
  const pick = (...ids) => ids.map((id) => anchors.get(id)).find(Boolean) ?? a.scene?.anchors?.[0];
  const rad = (d) => d * Math.PI / 180;
  let pose;
  if (move === 'walk') {
    const v = a.walkBudget?.speed ?? 1.4;
    const s = pick('lake_at_canal', 'spawn');
    const b = s.yaw_deg ?? 90;
    pose = (t) => {
      const d = Math.min(40, v * t);
      const d2 = Math.max(0, v * t - 40);
      return { local_e: s.local_e + Math.sin(rad(b)) * d + Math.sin(rad(b + 90)) * d2,
        local_n: s.local_n + Math.cos(rad(b)) * d + Math.cos(rad(b + 90)) * d2,
        yaw_deg: d2 > 0 ? b + 90 : b };
    };
  } else if (move === 'turn') {
    const s = pick('lake_market', 'lake_at_canal', 'spawn');
    pose = (t) => ({ local_e: s.local_e, local_n: s.local_n, yaw_deg: (s.yaw_deg ?? 0) + 45 * t });
  } else {
    const s = pick('from_above', 'aerial');
    pose = (t) => ({ local_e: s.local_e + 12 * t, local_n: s.local_n, yaw_deg: s.yaw_deg ?? 0,
      altitude_m: s.altitude_m ?? 120, pitch_deg: s.pitch_deg ?? -30 });
  }
  a.setFly(move === 'flight');
  a.walker.teleport(pose(0));
  // At rest first, so both modes start from the same neutral state.
  await new Promise((r) => setTimeout(r, 800));
  const draws = [];
  // T-2721: only a draw to the canvas is a frame. The gaze target's pick
  // (gpu-pick.js) calls renderer.render too, once per layer into its 1x1
  // target, and counted as frames those put intervals of a millisecond or two
  // into every reading taken while it looked.
  let offscreen = 0;
  const render = a.renderer.render;
  a.renderer.render = function timed(...args) {
    if (a.renderer.getRenderTarget() !== null) { offscreen += 1; return render.apply(this, args); }
    const t = performance.now();
    try { return render.apply(this, args); } finally {
      draws.push([t, a.renderer.getPixelRatio(), performance.now() - t]);
    }
  };
  // T-2721 `--no-gaze`: the gaze target's look (target.js) held off for the
  // move, so a reading can say what its one-pixel GPU pick costs the loop.
  const gazeTick = a.target?.tick;
  if (noGaze && gazeTick) a.target.tick = () => null;
  if (profile) console.profile(`${tier}/${move}/${mode}`);
  const t0 = performance.now();
  let paced = 0;
  await new Promise((resolve) => {
    const frame = () => {
      const el = (performance.now() - t0) / 1000;
      if (el >= seconds) { resolve(); return; }
      a.walker.teleport(pose(el));
      if (a.governor.pace === 2) paced += 1;
      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  });
  if (profile) console.profileEnd(`${tier}/${move}/${mode}`);
  if (noGaze && gazeTick) a.target.tick = gazeTick;
  a.renderer.render = render;
  const g = a.governor;
  a.setGovernor(true);
  const iv = [];
  for (let i = 1; i < draws.length; i++) iv.push(draws[i][0] - draws[i - 1][0]);
  const sorted = iv.slice().sort((x, y) => x - y);
  const q = (p) => sorted[Math.min(sorted.length - 1, Math.floor(p * sorted.length))];
  const mean = iv.reduce((t, x) => t + x, 0) / Math.max(1, iv.length);
  const sd = Math.sqrt(iv.reduce((t, x) => t + (x - mean) ** 2, 0) / Math.max(1, iv.length));
  const ratios = draws.map((d) => d[1]).sort((x, y) => x - y);
  // What the draw itself cost, so a slow interval says whose it is.
  const renderMs = draws.map((d) => d[2]).sort((x, y) => x - y)[Math.floor(draws.length / 2)] ?? null;
  return { draws: draws.length, mean, sd, median: q(0.5), p95: q(0.95), max: sorted[sorted.length - 1],
    over33: iv.filter((x) => x > 33.4).length, over50: iv.filter((x) => x > 50).length,
    ratioMin: ratios[0], ratioMedian: ratios[Math.floor(ratios.length / 2)], ceiling: g.ceiling,
    pacedRafs: paced, decisions: g.decisions, renderMs, offscreen };
}

/** Runs in the page (T-2555): at one anchor, put the governor where a slow
 *  moving window puts it (this runner's frames are too slow to drive it there),
 *  let the loop's own still frames rest it, and compare the held frame under
 *  Adaptive with Fixed's. */
async function stillAt({ id }) {
  const a = window.__chicago4d;
  const s = (a.scene?.anchors ?? []).find((x) => x.id === id);
  if (!s || !a.goTo(id)) return { id, skipped: true };
  a.setGovernor(true);
  const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  await frame();
  a.forceGovernor({ scale: 0.67, pace: 2 });
  // The next drawn frame is drawn at the lowered ratio; read it off a draw.
  const render = a.renderer.render;
  let lowered = null;
  a.renderer.render = function timed(...args) {
    if (lowered === null) lowered = a.renderer.getPixelRatio();
    return render.apply(this, args);
  };
  // Still frames — the loop's own, no hold, no step — until the governor rests.
  const t0 = performance.now();
  while (performance.now() - t0 < 30000) {
    await new Promise((r) => setTimeout(r, 100));
    const g = a.governor;
    if (lowered !== null && !g.moving && Math.abs(g.ratio - g.ceiling) < 1e-9) break;
  }
  a.renderer.render = render;
  const rested = a.governor;
  const shadowAuto = a.renderer.shadowMap.autoUpdate;
  const restMs = performance.now() - t0;
  a.setAnimationHold(true);
  const adaptive = await a.capture(24);
  a.setGovernor(false);
  const fixed = await a.capture(24);
  a.setGovernor(true);
  a.setAnimationHold(false);
  const sig = (x) => JSON.stringify(x);
  return { id, lowered, restMs, rested: { ratio: rested.ratio, ceiling: rested.ceiling, scale: rested.scale,
    pace: rested.pace, moving: rested.moving, shadowAuto }, same: sig(adaptive) === sig(fixed) };
}

/** Prints what `--profile N` collected over a viewport's moves. */
async function printProfile(prof, vpId) {
  await new Promise((r) => setTimeout(r, 500));
  const self = new Map();
  const incl = new Map();
  for (const profile of prof.profiles) {
    const dt = profile.timeDeltas;
    const byId = new Map(profile.nodes.map((nd) => [nd.id, nd]));
    const parent = new Map();
    for (const nd of profile.nodes) for (const c of nd.children ?? []) parent.set(c, nd.id);
    const keyOf = (id) => {
      const cf = byId.get(id).callFrame;
      return `${cf.functionName || '(anon)'} ${path.basename(cf.url)}:${cf.lineNumber + 1}`;
    };
    profile.samples.forEach((id, i) => {
      const ms = (dt[i] ?? 0) / 1000;
      self.set(keyOf(id), (self.get(keyOf(id)) ?? 0) + ms);
      const seen = new Set();
      for (let at = id; at !== undefined; at = parent.get(at)) {
        const key = keyOf(at);
        if (seen.has(key) || key.startsWith('(root)')) continue;
        seen.add(key);
        incl.set(key, (incl.get(key) ?? 0) + ms);
      }
    });
  }
  console.log(`\nself time, top ${PROFILE} (ms, over every move above):`);
  for (const [k, ms] of [...self].sort((x, y) => y[1] - x[1]).slice(0, PROFILE)) {
    console.log(`  ${ms.toFixed(0).padStart(7)}  ${k}`);
  }
  // T-2721: and with its callers, so a native call (readPixels) says who made it.
  const top = (m) => [...m].sort((x, y) => y[1] - x[1]).slice(0, PROFILE).map(([k, ms]) => [k, Math.round(ms)]);
  (out.profiles ??= {})[vpId] = { selfMs: top(self), totalMs: top(incl) };
  if (jsonOut) writeJson();
  console.log(`\ntotal time with callees, top ${PROFILE} (ms):`);
  for (const [k, ms] of [...incl].sort((x, y) => y[1] - x[1]).slice(0, PROFILE)) {
    console.log(`  ${ms.toFixed(0).padStart(7)}  ${k}`);
  }
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: GL_ARGS[GL],
});
const out = { year: YEAR, source: wantSource ? 'source' : 'published', throttle: THROTTLE,
  rebuild: SYNC ? 'sync' : 'spread', gl: GL, ...(LIVE ? { noGaze: NO_GAZE } : {}),
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
  // T-2721: every reading names the rasteriser that drew it.
  const rasteriser = await page.evaluate(() => {
    const gl = window.__chicago4d.renderer?.getContext?.();
    const ext = gl?.getExtension('WEBGL_debug_renderer_info');
    return gl ? String(gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER)) : null;
  });
  (out.rasterisers ??= {})[vp.id] = rasteriser;
  console.log(`\n${vp.id} ${vp.width}x${vp.height} — ready in ${((Date.now() - t0) / 1000).toFixed(0)} s` +
    (vp.throttle > 1 ? `, CPU throttled ${vp.throttle}×` : '') + `\n  drawn by ${rasteriser}`);
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
  if (LIVE) {
    // Into the town: under the welcome the loop draws only a frame that changed
    // (T-2113) and the governor is held at rest, so nothing live is read there.
    const entered = await page.evaluate(async () => {
      const welcome = window.__chicago4d.welcome;
      const deadline = Date.now() + 90_000;
      while (welcome && welcome.state !== 'world' && Date.now() < deadline) {
        if (welcome.state === 'welcome') welcome.enter('spawn');
        await new Promise((r) => setTimeout(r, 100));
      }
      document.exitPointerLock?.();
      return welcome?.state ?? 'no welcome';
    });
    console.log(`entered the town: ${entered}`);
    console.log('tier      move    mode      draws | interval ms mean   sd  med  p95  max  >33 >50 | ratio min/med (ceiling) | paced rAFs');
    for (const tier of TIERS) {
      for (const move of MOVES.filter((m) => !['travel', 'none'].includes(m))) {
        const pair = {};
        for (const mode of ['fixed', 'adaptive']) {
          const r = await page.evaluate(driveLive, { move, tier, mode, seconds: SECONDS, xray: XRAY,
            profile: PROFILE > 0, noGaze: NO_GAZE });
          pair[mode] = r;
          const f = (x) => x.toFixed(1).padStart(5);
          console.log(`${tier.padEnd(9)} ${move.padEnd(7)} ${mode.padEnd(9)} ${String(r.draws).padStart(5)} |`
            + ` ${f(r.mean)}${f(r.sd)}${f(r.median)}${f(r.p95)}${f(r.max)} ${String(r.over33).padStart(4)}${String(r.over50).padStart(4)} |`
            + ` ${r.ratioMin.toFixed(2)}/${r.ratioMedian.toFixed(2)} (${r.ceiling.toFixed(2)}) | ${r.pacedRafs}`
            + ` | draw median ${r.renderMs?.toFixed(0)} ms | ${r.offscreen} offscreen`);
          out.readings.push({ viewport: vp.id, throttle: vp.throttle, live: true, tier, move, mode, ...r });
          if (jsonOut) writeJson();
        }
        const fell = pair.adaptive.sd < pair.fixed.sd && pair.adaptive.p95 < pair.fixed.p95;
        console.log(`  ${fell ? 'FELL' : 'DID NOT FALL'}: sd ${pair.fixed.sd.toFixed(1)} → ${pair.adaptive.sd.toFixed(1)} ms,`
          + ` p95 ${pair.fixed.p95.toFixed(1)} → ${pair.adaptive.p95.toFixed(1)} ms`);
        if (!fell) failed++;
      }
    }
    if (STILLS) {
      out.stills = [];
      for (const { id } of await page.evaluate(() => window.__chicago4d.scene?.anchors ?? [])) {
        const r = await page.evaluate(stillAt, { id });
        out.stills.push({ viewport: vp.id, ...r });
        if (jsonOut) writeJson();
        if (r.skipped) { console.log(`  still ${id}: not an anchor of this year`); continue; }
        const rested = r.lowered !== null && r.lowered < r.rested.ceiling
          && Math.abs(r.rested.ratio - r.rested.ceiling) < 1e-9 && r.rested.scale === 1
          && r.rested.pace === 1 && r.rested.shadowAuto === true;
        console.log(`  still ${id.padEnd(26)} drawn at ${r.lowered?.toFixed(2)}, rested at ${r.rested.ratio.toFixed(2)}`
          + ` in ${(r.restMs / 1000).toFixed(1)} s`
          + ` (ceiling ${r.rested.ceiling.toFixed(2)})${rested ? '' : ' NOT AT REST'}; held frame Adaptive ${r.same ? '==' : '!='} Fixed`);
        if (!rested || !r.same) failed++;
      }
    }
    if (prof) await printProfile(prof, vp.id);
    if (errors.length) {
      console.log(`pageerrors: ${JSON.stringify(errors.slice(0, 5))}`);
      failed++;
    }
    await ctx.close();
    continue;
  }
  console.log('tier      move    frames rebuilds | scripted ms med/p95/max  >16 >33 >50 | flora p95/max | trees p95/max | other hooks max');
  for (const tier of TIERS) {
    for (const move of MOVES) {
      const r = await page.evaluate(driveMove, { move, tier, render: RENDER, profile: PROFILE > 0,
        sync: SYNC, verify: VERIFY, xray: XRAY, sward: SWARD });
      const f = (x) => x.toFixed(1).padStart(5);
      const n = (x) => String(x).padStart(3);
      const L = r.layers;
      const others = Object.entries(L)
        .filter(([k, d]) => !['flora.update', 'trees.update', 'renderer.render'].includes(k) && d.max >= 1)
        .map(([k, d]) => `${k} ${d.max.toFixed(1)}`).join(', ');
      console.log(`${tier.padEnd(9)} ${move.padEnd(7)} ${String(r.frames).padStart(6)} ${String(r.rebuilds).padStart(8)} |`
        + ` ${f(r.scripted.median)} ${f(r.scripted.p95)} ${f(r.scripted.max)} ${n(r.scripted.over16)} ${n(r.scripted.over33)} ${n(r.scripted.over50)} |`
        + ` ${f(L['flora.update'].p95)} ${f(L['flora.update'].max)} | ${f(L['trees.update'].p95)} ${f(L['trees.update'].max)} | ${others || '-'}`
        + (r.spread ? ` | spread ${r.spread.landings} passes, ${r.spread.framesPerPass.toFixed(1)} frames each, ${r.spread.drained} finished early, ${r.spread.abandoned} dropped`
          + `, ${r.spread.msPerPass.toFixed(1)} ms each on the main thread, ${r.spread.waits} frames waiting on a worker`
          + `, ${r.spread.oneFrame} dealt in one frame, ${r.spread.jumps} after a jump`
          + (r.spread.slots?.dealt ? `, ${(100 * r.spread.slots.grounded / r.spread.slots.dealt).toFixed(0)} % of`
            + ` ${r.spread.slots.dealt} pool slots dealt off the workers' ground` : '')
          + (r.spread.jumps ? ` (landing in ${r.spread.jumpFrames} frames between them)` : '') : ''));
      if (r.near?.passes) {
        const g = r.near.gpu;
        console.log(`  near re-deal: ${r.near.passes} passes, ${r.near.median.toFixed(1)} ms median and`
          + ` ${r.near.max.toFixed(1)} max on the main thread (${r.near.ms.toFixed(0)} ms in all)`
          + (g ? ` | GPU near ring: ${g.passes} deal passes ${g.passMs.toFixed(0)} ms, ${g.builds} tile builds`
            + ` ${g.buildMs.toFixed(0)} ms, ${g.uploads} uploads, ${g.readBacks} read-backs`
            // T-2774: the read-backs the near heads and census are reaped from,
            // and the main thread's ms asking and reaping them (a reap that lands
            // between frames is in no frame's flora ms, so it is printed here).
            + (g.reaps != null ? `, ${g.reads} reads asked without waiting and ${g.syncReads} in the frame`
              + ` ${g.readMs.toFixed(0)} ms, collected ${(g.collectMs ?? 0).toFixed(0)} ms,`
              + ` ${g.reaps} reaped ${g.reapMs.toFixed(0)} ms, ${g.stale} stale` : '')
            : ' | near tufts drawn by the CPU'));
      }
      for (const l of r.longs ?? []) {
        console.log(`  over 50 ms: frame ${l.frame} of the ${move}, ${l.ms} ms (flora ${l.flora}, ${l.pass ?? 'no'} pass),`
          + ` after ${l.landings} spread landings, ${l.drained} finished early, ${l.abandoned} dropped`);
      }
      if (r.heldZones?.held) {
        const z = r.heldZones;
        console.log(`  verify zones: ${z.asked} points asked of the workers' ground, ${z.unasked} left to the page,`
          + ` ${z.differ} answered differently${z.differ ? ` ${JSON.stringify(z.first)}` : ''}`);
        if (z.differ) failed++;
        // T-2696: the slots' water, floor, verge and height from the same ground.
        if (z.ground) {
          const g = z.ground;
          console.log(`  verify ground: ${g.asked} points asked (${g.wet} wet, ${g.floor} on a floor, ${g.trodden} trodden,`
            + ` ${g.keep} kept verge), ${g.differ} answered differently${g.differ ? ` ${JSON.stringify(g.first)}` : ''}`);
          if (g.differ) failed++;
        }
      }
      if (r.swardGrid) {
        const y = r.swardGrid;
        console.log(`  verify yards: ${y.asked} points over the yards' boxes (${y.suppressed} without sward),`
          + ` ${y.differ} answered differently by the grid than by the full walk${y.differ ? ` ${JSON.stringify(y.first)}` : ''}`);
        if (y.differ) failed++;
      }
      if (r.swardEvery) {
        const y = r.swardEvery;
        console.log(`  verify yards, every slot: ${y.asked} slots asked (${y.suppressed} without sward),`
          + ` ${y.differ} answered differently by the grid than by the full walk${y.differ ? ` ${JSON.stringify(y.first)}` : ''}`);
        if (y.differ || !y.asked) failed++;
      }
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
  if (prof) await printProfile(prof, vp.id);
  if (errors.length) {
    console.log(`pageerrors: ${JSON.stringify(errors.slice(0, 5))}`);
    failed++;
  }
  await ctx.close();
}
await browser.close();
server.close();
if (jsonOut) console.log(`\nwrote ${jsonOut}`);
if (LIVE) {
  console.log(failed ? `\nFAIL — ${failed} live reading(s) did not hold` : '\nPASS — governed moves steadier, still frames unchanged');
  process.exit(failed ? 1 : 0);
}
if (SWARD === 'both' && !VERIFY && !GATE) {
  console.log(failed ? `\nFAIL — ${failed} move(s) answered a slot's sward differently or threw` : '\nPASS — every slot answered the same by the grid and the full walk');
  process.exit(failed ? 1 : 0);
}
if (VERIFY && !GATE) {
  console.log(failed ? `\nFAIL — ${failed} move(s) failed verification or threw` : '\nPASS — every spread pass landed the one-frame pass');
  process.exit(failed ? 1 : 0);
}
if (GATE) {
  console.log(failed ? `\nFAIL — ${failed} reading(s) over the moving-frame ceiling` : '\nPASS — every moving frame inside the ceiling');
  process.exit(failed ? 1 : 0);
}
