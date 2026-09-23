/**
 * critic_shots.mjs — the capture half of the critic harness (RENDERING G0).
 *
 *   node tools/critic_shots.mjs                     capture both viewports
 *   node tools/critic_shots.mjs --metrics           …and measure every frame
 *   node tools/critic_shots.mjs --stability         …and hold them to the repeat contract
 *   node tools/critic_shots.mjs --published         shoot the published mirror
 *   node tools/critic_shots.mjs --viewport desktop  one viewport, while iterating
 *   node tools/critic_shots.mjs --stations a,b      a subset, while iterating
 *   node tools/critic_shots.mjs --no-mask           skip the masked frames
 *   node tools/critic_shots.mjs --out DIR           default /tmp/critic
 *
 * `--metrics` captures each station THREE times — the visitor's frame, the same
 * pose with the town's `structures` group hidden, and the same pose with the
 * nine `flora-head-*` sets hidden. Twice because no property of one frame
 * separates a gable end from an oak on the horizon (R-W4a); three times because
 * no property of one frame separates a yellow coneflower from the grass under
 * it either — the flower-load recipe's hue cut at 50° runs through the middle
 * of a July prairie's own bloom (R-W4c). Both arguments, with their numbers,
 * are in `critic_metrics.mjs`. The extra captures cost frames rather than a
 * page load, and `--no-mask` opts out for a run that only wants the cheap
 * readings.
 *
 * WHY THIS EXISTS. Every rendering round this project has run was judged in
 * adjectives, or in numbers from a harness that was never committed — so no two
 * rounds are comparable and the sweep's own figures cannot be reproduced. This
 * is the fixed rig: the same stations, the same viewports, the same frozen
 * clock, every time, with `tools/critic_metrics.mjs` doing the reading.
 *
 * IT ADDS NO WAY TO DRIVE THE SCENE. It uses `window.__chicago4d`'s existing
 * `goTo`, `setAnimationHold` and `capture`, plus the `walker.teleport` that
 * `tools/shoot.mjs` already uses for poses that are not scene anchors. If a
 * future station wants a new capability, the answer is a scene anchor in
 * `data/scenes/`, not a new hook in the renderer.
 *
 * DETERMINISM, which is what the phase is for — see STABILITY below for what
 * the harness holds itself to, and what it measured before setting it. The animation clock is held
 * BEFORE the render loop's second tick — `setAnimationHold` is polled for on
 * every animation frame from the moment the page loads, and three.js's Clock
 * returns 0 for its first delta — so wind, water drift and every other
 * dt-driven uniform sit at exactly zero in every run rather than at "however
 * long boot took today". The DOM chrome is hidden before any capture: a
 * Playwright element screenshot photographs the PAGE REGION the element covers,
 * overlays included, so shooting `#view` still catches the HUD sitting on top of
 * it — and the HUD carries live readouts whose antialiased glyph edges moved
 * nine pixels between two otherwise identical rounds. Hiding it measures the
 * render instead of the overlay. Device scale factor is pinned to 1 at both
 * viewports so 390x780 means 390x780 pixels and the metrics from the two
 * viewports are on one scale.
 *
 * PITCH IS PRINTED AND ASSERTED. Two rounds of the 2026-08-10 prairie sweep were
 * judged at the wrong look-angle because the harness set no pitch and inherited
 * whatever the previous shot left. Each station declares its pitch, the run
 * prints what the walker actually reports, and a mismatch over 0.5 deg fails.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { measure, decodePng } from './critic_metrics.mjs';

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
const APP = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const value = (name, fallback) => {
  const i = argv.indexOf(name);
  return i > -1 && argv[i + 1] ? argv[i + 1] : fallback;
};

const PUBLISHED = flag('--published');
const WANT_METRICS = flag('--metrics');
const WANT_STABILITY = flag('--stability');
const OUT = path.resolve(value('--out', '/tmp/critic'));
const ONLY = value('--viewport', '');
// `--stations a,b,c` — the budget section of ROADMAP has told runs to use this
// since 2026-08-14 and it did not exist, so every "3 minutes instead of 12" in
// that section was actually a twelve-minute run. It filters the set and says so,
// loudly, because a filtered run is not the baseline and must never be quoted
// as one.
const PICK = value('--stations', '').split(',').map((s) => s.trim()).filter(Boolean);
// `--no-mask` drops the structure-free capture (R-W4a) and the head-free one
// (R-W4c). They cost frames, not a page load, and without them the only horizon
// figure is the one that counts gables as trees and the only flower figure is
// the one that counts coneflowers as grass — so it is opt-OUT, and a run that
// opts out says so.
const NO_MASK = flag('--no-mask');
const PORT = Number(process.env.CRITIC_PORT || 4191);
const YEAR = process.env.CRITIC_YEAR || '1835';

const ROOT = PUBLISHED ? path.resolve(APP, '../../site/chicago/4d') : APP;
const ENTRY = PUBLISHED ? '/walk/' : '/renderers/web/index.html';

/**
 * THE STATIONS.
 *
 * The scene anchors come from `data/scenes/1835.json` and are driven by `goTo`,
 * so the harness cannot drift from the viewpoints a visitor is offered. There
 * were eight when this was written and there are ten now; the list is read, not
 * counted here.
 *
 * The POSE stations below are not anchors. Three of them are the prairie-sweep
 * stands, RE-ESTABLISHED rather than recovered: the 2026-08-10 sweep's own
 * coordinates were never committed, so these are new stands chosen against the
 * committed heightfield to serve the same three briefs the sweep recorded — an
 * open prairie view, an open-sky control, and the water's edge where zone 1
 * cordgrass is specified. Numbers taken here are therefore NOT comparable to the
 * sweep's per-station figures; they are this harness's own baseline. The fourth,
 * `public_square`, is a pose for the opposite reason — it stands on a block a
 * visitor is not offered an anchor to, and T-0224 added it because a change to
 * the whole of that block's sward could not be shown in a picture. Elevations
 * quoted below are read from
 * `data/terrain/epochs/e1834_harbor_cut/heightfield.json`.
 */
const SWEEP_STATIONS = [
  {
    id: 'prairie_south',
    label: 'South of the town, looking east over open prairie',
    // Ground 0.77 m. Looking east down the long axis of the terrain box, which
    // is the only bearing with more terrain ahead than the 1500 m at which fog
    // is total (L17) — so the frame measures atmosphere, not the box edge.
    pose: { local_e: 120, local_n: -330, yaw_deg: 90 },
  },
  {
    id: 'prairie_west',
    label: 'The West Side prairie, the open-sky control',
    // Ground 1.22 m, on the ground Andreas calls "an open prairie, entirely free
    // from timber". The sweep's control shot existed to separate a tuned view
    // from a fixed one; this one keeps that job and looks away from the town.
    pose: { local_e: -250, local_n: -150, yaw_deg: 90 },
  },
  {
    id: 'public_square',
    label: 'The public square, from its south-east corner, looking west-north-west',
    // Ground 0.885 m, standing INSIDE the block bounded by Randolph, Clark,
    // Washington and LaSalle -- the one block this project holds was never
    // private building ground (`data/reconstruction/1835_reserved_ground.json`).
    //
    // WHY HERE, AND WHY THIS BEARING. The stand looks across the block's long
    // diagonal, which is the longest run of reserved sward in the town, and the
    // bearing is the BISECTOR of the two county buildings that stand on 1 July
    // 1835: the estray pen at the south-west corner, 81.8 m off at 264.9 deg,
    // and the log jail at the north-west corner, 131.2 m off at 319.9 deg. They
    // are 55.1 deg apart and the yaw sits midway, so each is 27.5 deg off centre.
    // Projected through the renderer's own camera, that puts them at x = 246 and
    // x = 1047 of 1280 on the desktop frame (half-FOV 39.8 deg, comfortable) and
    // at the extreme left and right edges of the portrait frame (half-FOV
    // 28.2 deg, 0.7 deg of margin). SO: THE DESKTOP ROW READS THE GROUND AND THE
    // TWO BUILDINGS, THE MOBILE ROW READS THE GROUND. No stand on this block can
    // do better -- its corners are 108 m apart and the buildings sit on two of
    // them.
    //
    // THE THIRD COUNTY BUILDING IS NOT HERE, AND MUST NOT BE LOOKED FOR. The
    // first Cook County court-house was erected on the north-east corner in the
    // FALL of 1835 (`data/structures/cook_county_courthouse_1835.json`,
    // documented range from 1835-10-01), so it is dated out of a 1 July scene and
    // is absent from the registry. A frame that showed it would be the bug.
    //
    // WHAT IT IS FOR. T-0027 replanted this whole block from wet prairie to sedge
    // meadow and nothing in this project could show that in a picture; the county
    // buildings, the town's only public ones, had no baseline either. Flower load
    // and the depth-band grain are read here over reserved sward with no street,
    // wall or roof under the near band, which makes this the third station after
    // the two prairie stands where the flower denominator is vegetation (harness
    // note 3 in docs/STATUS.md).
    pose: { local_e: 550, local_n: -370, yaw_deg: 292 },
  },
  {
    id: 'river_bank',
    label: 'The main stem, south bank, at the waterline',
    // Ground 0.39 m with traced water within six metres north — the eight-metre
    // marsh edge where zone 1 specifies cordgrass at 1.2-2.0 m and 40-55 % cover.
    pose: { local_e: 180, local_n: 0, yaw_deg: 0 },
  },
];

const scene = JSON.parse(fs.readFileSync(path.join(APP, 'data/scenes', `${YEAR}.json`), 'utf8'));
const ALL_STATIONS = [
  ...scene.anchors.map((a) => ({
    id: a.id,
    label: a.label,
    anchor: a.id,
    expectPitch: typeof a.pitch_deg === 'number' ? a.pitch_deg : 0,
  })),
  ...SWEEP_STATIONS.map((s) => ({ ...s, expectPitch: 0 })),
].filter((s) => !PICK.length || PICK.includes(s.id));
// ALL_STATIONS, not STATIONS: the filtered list is what this guard is about, and
// STATIONS is declared eighty lines below — so `--stations`, the documented flag for
// iterating on one frame, died in the temporal dead zone before it shot anything.
if (PICK.length && !ALL_STATIONS.length) {
  console.error(`no station matches --stations ${PICK.join(',')}`);
  process.exit(2);
}

/**
 * `--stations a,b,c` — shoot a subset, WHILE ITERATING ONLY.
 *
 * The full rig is fourteen stations at two viewports and takes about fifteen
 * minutes, which is the right cost for a baseline and the wrong cost for the
 * tenth trial of a constant. A phase that has to wait twelve minutes to see a
 * number tunes by eye instead, which is the failure G0 exists to end.
 *
 * It is deliberately NOT a way to report a subset as a result: a phase quotes
 * the full table, and `tools/check.sh` and the baseline runs pass no filter. An
 * unknown id fails loudly rather than silently shooting nothing, because a
 * typo'd station that reports "OK" over zero frames is worse than no harness.
 */
const WANT = (value('--stations', '') || '').split(',').map((s) => s.trim()).filter(Boolean);
const unknown = WANT.filter((id) => !ALL_STATIONS.some((s) => s.id === id));
if (unknown.length) {
  console.error(`unknown station(s): ${unknown.join(', ')}`);
  console.error(`known: ${ALL_STATIONS.map((s) => s.id).join(', ')}`);
  process.exit(2);
}
const STATIONS = WANT.length ? ALL_STATIONS.filter((s) => WANT.includes(s.id)) : ALL_STATIONS;

const VIEWPORTS = [
  ['mobile', { width: 390, height: 780 }],
  ['desktop', { width: 1280, height: 800 }],
].filter(([name]) => !ONLY || name === ONLY);

// ---- a static server, the same shape the smoke test uses ----------------- //

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
  '.geojson': 'application/json',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' }).end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`;

if (PUBLISHED && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}

// ---- the stability contract ---------------------------------------------- //

/**
 * WHAT "REPEATABLE" MEANS HERE, and why it is not a hash comparison.
 *
 * G0 asks for captures byte-stable across two runs. Inside one browser process
 * they are, exactly: revisiting a station after walking away reproduces the file
 * bit for bit, so nothing in the renderer, the scene or this harness carries
 * hidden state or hidden time. ACROSS processes they are not, and the residual
 * was measured before this contract was written rather than assumed: on this
 * software rasteriser, 7 of 11 desktop stations repeat byte for byte and the
 * other 4 differ in 1, 2, 11 and 43 pixels out of 1,024,000 — bimodally, the
 * same two variants recurring, in the horizon row and on alpha-blended surfaces.
 * The renderer is deterministic; the last bit of the rasteriser is not.
 *
 * A hash gate would therefore fail about a third of the time while telling a
 * later phase nothing about whether its change was real. So the contract is the
 * thing the program actually depends on: the frame is stable to well under a
 * hundredth of a percent of its pixels, AND every metric this harness reports
 * repeats to within 1 %. A phase whose delta cannot clear that is not a delta.
 * The per-station byte-identical count is reported anyway — a fall in it is a
 * signal worth reading even though it is not a failure.
 */
const STABILITY = { maxDiffFraction: 0.0005, maxMetricDrift: 0.01 };

/** Differing pixels between two same-size frames. */
function pixelDiff(a, b) {
  if (a.width !== b.width || a.height !== b.height) {
    return { pixels: Infinity, fraction: 1, maxDelta: 255 };
  }
  let pixels = 0; let maxDelta = 0;
  for (let i = 0; i < a.data.length; i += 4) {
    const d = Math.max(
      Math.abs(a.data[i] - b.data[i]),
      Math.abs(a.data[i + 1] - b.data[i + 1]),
      Math.abs(a.data[i + 2] - b.data[i + 2]),
    );
    if (d > 0) { pixels++; if (d > maxDelta) maxDelta = d; }
  }
  const total = a.width * a.height;
  return { pixels, fraction: pixels / total, maxDelta };
}

/** The largest relative move across the reported metrics, and which one moved. */
function compareMetrics(a, b) {
  const readings = [
    ['horizonTimber.coverageAll', (m) => m.horizonTimber.coverageAll],
    ['horizonTimber.coverageCentralTwoThirds', (m) => m.horizonTimber.coverageCentralTwoThirds],
    ['horizonTimber.timberOnly.coverageAll', (m) => m.horizonTimber.timberOnly?.coverageAll],
    ['crown.fineDetailRatio', (m) => m.crown.fineDetailRatio],
    ['crown.sunlitGminusB', (m) => m.crown.sunlitGminusB],
    ['shadow.darkestDecileL', (m) => m.shadow.darkestDecileL],
    ['depthBandHighPassRms.far', (m) => m.depthBandHighPassRms.far],
    ['depthBandHighPassRms.mid', (m) => m.depthBandHighPassRms.mid],
    ['depthBandHighPassRms.near', (m) => m.depthBandHighPassRms.near],
    ['flower.load', (m) => m.flower.load],
    ['flower.bloom.shareOfHued', (m) => m.flower.bloom?.shareOfHued],
    ['landSky.skyFraction', (m) => m.landSky.skyFraction],
  ];
  let worst = null; let value = null;
  for (const [name, read] of readings) {
    const x = read(a);
    const y = read(b);
    if (typeof x !== 'number' || typeof y !== 'number') continue;
    // Relative to the reading's own size, with a floor so a metric that is
    // legitimately near zero (flower load on a street) cannot manufacture a
    // 400 % drift out of two pixels.
    const scale = Math.max(Math.abs(x), Math.abs(y), 0.05);
    const drift = Math.abs(x - y) / scale;
    if (value === null || drift > value) { value = drift; worst = name; }
  }
  return { worst, value };
}

// ---- one capture round --------------------------------------------------- //

const problems = [];

async function round(viewportName, viewport, dir) {
  fs.mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.PW_EXECUTABLE || undefined,
    args: ['--enable-unsafe-swiftshader'],
  });
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  page.setDefaultTimeout(180_000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message || e}`));
  page.on('console', (m) => {
    const t = m.text();
    if (m.type() === 'error' && !t.startsWith('Failed to load resource')) {
      errors.push(`console.error: ${t}`);
    }
  });
  await page.addInitScript(() => {
    localStorage.setItem('chicago4d.detail', 'full');
    localStorage.setItem('chicago4d.help.seen', '1');
  });

  await page.goto(base, { waitUntil: 'domcontentloaded' });

  // Hold the clock at its first frame. Polling on rAF is what makes this land
  // before the loop's second tick, which is what makes wind phase zero rather
  // than "however many seconds boot took".
  await page.waitForFunction(() => {
    const api = window.__chicago4d;
    if (typeof api?.setAnimationHold !== 'function') return false;
    api.setAnimationHold(true);
    return true;
  }, null, { polling: 'raf', timeout: 180_000 });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180_000 });

  const gate = await page.$('#gate-btn');
  if (gate) await page.click('#gate-btn');
  // The first-run guide is dismissible and covers a quarter of the frame; the
  // canvas screenshot excludes it either way, but a modal over the canvas can
  // still take pointer focus, so it goes.
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it|dismiss|close/i.test(b.textContent ?? '')) b.click();
    }
    // Everything except the render surface. Hidden rather than removed: the HUD
    // keeps updating, the navigation readout keeps resolving, and a station that
    // depended on a torn-out element would fail here instead of in the app.
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
    document.head.append(style);
  });

  const shots = [];
  for (const st of STATIONS) {
    const arrived = await page.evaluate(async (s) => {
      const api = window.__chicago4d;
      if (s.anchor) {
        if (!api.goTo(s.anchor)) return { ok: false };
      } else {
        api.setFly(typeof s.pose.altitude_m === 'number');
        api.walker.teleport({ ...s.pose, pitch_deg: s.pose.pitch_deg ?? 0 });
      }
      // Eight frames: the first carries the teleport and the rest let the
      // camera-driven rebuilds settle — the flora rings, the tree horizon and
      // the terrain's own solve all re-run on arrival, and three frames left
      // four of the then-eleven stations still moving between rounds. They advance no
      // time; the clock is held, so this costs frames and not a second of wind.
      for (let i = 0; i < 8; i++) await api.capture(4);
      const stats = api.stats();
      return {
        ok: true,
        pitchDeg: api.player.pitchDeg,
        bearingDeg: api.player.bearingDeg,
        e: api.player.e,
        n: api.player.n,
        eyeY: api.player.y,
        flying: api.player.flying,
        drawCalls: stats.drawCalls,
        triangles: stats.triangles,
      };
    }, st);
    if (!arrived.ok) { problems.push(`${viewportName}/${st.id}: station did not resolve`); continue; }

    const canvas = (await page.$('#view')) ?? (await page.$('canvas'));
    const png = await canvas.screenshot({ path: path.join(dir, `${st.id}.png`) });
    const sha = crypto.createHash('sha256').update(png).digest('hex');

    // THE SECOND CAPTURE, AND WHY IT IS NOT A NEW WAY TO DRIVE THE SCENE.
    // R-W4a: the horizon-timber recipe counts gable ends as trees, and no
    // property of a single frame separates them — the sky is blue-dominant, so
    // every non-sky pixel clears the G−B test, and L17's total extinction by
    // 1500 m converges distant timber and a distant wall on one fog colour.
    // So the harness photographs the same pose twice and lets SUBTRACTION do
    // it: once as the visitor sees it, once with the `structures` group's
    // `visible` flag down. Nothing is moved, nothing is reloaded, no camera
    // changes, and the flag goes straight back up — the station's own frame is
    // still the one in the manifest, and `sha256` is still that frame's.
    if (WANT_METRICS && !NO_MASK) {
      const toggled = await page.evaluate(async (on) => {
        const g = window.__chicago4d.scene3d.getObjectByName('structures');
        if (!g) return false;
        g.visible = on;
        // Two frames, matching the arrival idiom above: the batches carry no
        // camera-driven rebuild, but a frame that has not been drawn is not a
        // frame that can be photographed.
        for (let i = 0; i < 2; i++) await window.__chicago4d.capture(4);
        return true;
      }, false);
      if (!toggled) {
        problems.push(`${viewportName}/${st.id}: no "structures" group to hide — `
          + 'the timber-only figure cannot be measured');
      } else {
        await canvas.screenshot({ path: path.join(dir, `${st.id}__bare.png`) });
        await page.evaluate(async () => {
          window.__chicago4d.scene3d.getObjectByName('structures').visible = true;
          for (let i = 0; i < 2; i++) await window.__chicago4d.capture(4);
        });
      }

      // THE THIRD CAPTURE, for the same reason and by the same means (R-W4c).
      // The flower-load recipe sorts a ground pixel into "plant" or "flower" on
      // a hue cut at 50°, and a July prairie's own bloom straddles it: the
      // committed record for `ratibida_pinnata` is hue 50.250 and counts as
      // grass, `silphium_laciniatum` is 49.880 and counts as a flower. So the
      // harness hides the nine `flora-head-*` instanced sets and photographs the
      // pose again; every ground pixel that moved is one a flower painted, and
      // `critic_metrics.mjs` holds the recipe to it. Frames, not a page load —
      // and `--no-mask` opts out of this capture with the other one.
      const heads = await page.evaluate(async (on) => {
        const flora = window.__chicago4d.scene3d.getObjectByName('flora');
        if (!flora) return 0;
        const sets = [];
        flora.traverse((o) => { if (o.name.startsWith('flora-head-')) sets.push(o); });
        for (const s of sets) s.visible = on;
        for (let i = 0; i < 2; i++) await window.__chicago4d.capture(4);
        return sets.length;
      }, false);
      if (!heads) {
        problems.push(`${viewportName}/${st.id}: no "flora-head-*" sets to hide — `
          + 'the bloom figure cannot be measured');
      } else {
        await canvas.screenshot({ path: path.join(dir, `${st.id}__noflower.png`) });
        await page.evaluate(async () => {
          const flora = window.__chicago4d.scene3d.getObjectByName('flora');
          flora.traverse((o) => { if (o.name.startsWith('flora-head-')) o.visible = true; });
          for (let i = 0; i < 2; i++) await window.__chicago4d.capture(4);
        });
      }
    }
    const pitchOff = Math.abs(arrived.pitchDeg - st.expectPitch);
    if (pitchOff > 0.5) {
      problems.push(`${viewportName}/${st.id}: pitch ${arrived.pitchDeg.toFixed(2)}° `
        + `where the station declares ${st.expectPitch}°`);
    }
    shots.push({
      id: st.id,
      label: st.label,
      viewport: viewportName,
      pitch_deg: Number(arrived.pitchDeg.toFixed(2)),
      bearing_deg: Number(arrived.bearingDeg.toFixed(2)),
      local_e: Number(arrived.e.toFixed(2)),
      local_n: Number(arrived.n.toFixed(2)),
      eye_y_m: Number(arrived.eyeY.toFixed(2)),
      flying: arrived.flying,
      draw_calls: arrived.drawCalls,
      triangles: arrived.triangles,
      sha256: sha,
      png: path.relative(OUT, path.join(dir, `${st.id}.png`)),
    });
    console.log(`  ${viewportName.padEnd(7)} ${st.id.padEnd(18)} `
      + `pitch ${arrived.pitchDeg.toFixed(1).padStart(6)}°  `
      + `bearing ${arrived.bearingDeg.toFixed(0).padStart(4)}°  `
      + `draws ${String(arrived.drawCalls).padStart(3)}  ${sha.slice(0, 12)}`);
  }

  if (errors.length) problems.push(`${viewportName}: ${errors.length} page error(s): ${errors[0]}`);
  await browser.close();
  return { shots, errors };
}

// ---- run ----------------------------------------------------------------- //

console.log(`critic shots — ${PUBLISHED ? 'PUBLISHED mirror (compressed assets)' : 'source tree'}`
  + ` · ${STATIONS.length} stations · out ${OUT}`);
if (ONLY) console.log(`NOT THE FULL SET — viewports filtered to "${ONLY}"`);
if (PICK.length) console.log(`NOT THE FULL SET — stations filtered to ${PICK.join(', ')}`);

const manifest = { target: PUBLISHED ? 'published' : 'source', year: YEAR, viewports: {} };

for (const [name, viewport] of VIEWPORTS) {
  console.log(`\n${name} ${viewport.width}x${viewport.height}:`);
  const dir = path.join(OUT, name);
  const first = await round(name, viewport, dir);
  manifest.viewports[name] = { viewport, shots: first.shots, page_errors: first.errors };

  if (WANT_METRICS || WANT_STABILITY) {
    for (const s of manifest.viewports[name].shots) {
      const bare = path.join(dir, `${s.id}__bare.png`);
      const noflower = path.join(dir, `${s.id}__noflower.png`);
      s.metrics = measure(decodePng(fs.readFileSync(path.join(dir, `${s.id}.png`))), {
        withoutStructures: fs.existsSync(bare) ? decodePng(fs.readFileSync(bare)) : null,
        withoutFlowerHeads: fs.existsSync(noflower)
          ? decodePng(fs.readFileSync(noflower)) : null,
      });
    }
  }

  if (WANT_STABILITY) {
    // A second, entirely separate browser launch. Comparing two shots inside one
    // session would only prove the clock is held; the claim is that a RUN
    // repeats, which is what makes a later phase's delta attributable.
    const dir2 = path.join(OUT, `${name}__repeat`);
    console.log('  — repeat round, in a separate browser, for the stability contract');
    const second = await round(name, viewport, dir2);
    const byId = new Map(second.shots.map((s) => [s.id, s]));
    let failed = 0; let identical = 0;
    for (const s of manifest.viewports[name].shots) {
      const other = byId.get(s.id);
      if (!other) { problems.push(`${name}/${s.id}: missing from the repeat round`); failed++; continue; }
      const a = decodePng(fs.readFileSync(path.join(dir, `${s.id}.png`)));
      const b = decodePng(fs.readFileSync(path.join(dir2, `${s.id}.png`)));
      const diff = pixelDiff(a, b);
      const bare2 = path.join(dir2, `${s.id}__bare.png`);
      const noflower2 = path.join(dir2, `${s.id}__noflower.png`);
      const metricDrift = compareMetrics(s.metrics, measure(b, {
        withoutStructures: fs.existsSync(bare2) ? decodePng(fs.readFileSync(bare2)) : null,
        withoutFlowerHeads: fs.existsSync(noflower2)
          ? decodePng(fs.readFileSync(noflower2)) : null,
      }));
      s.stability = {
        byte_identical: other.sha256 === s.sha256,
        differing_pixels: diff.pixels,
        differing_fraction: Number(diff.fraction.toFixed(7)),
        max_channel_delta: diff.maxDelta,
        worst_metric: metricDrift.worst,
        worst_metric_drift: metricDrift.value === null ? null : Number(metricDrift.value.toFixed(5)),
      };
      if (other.sha256 === s.sha256) identical++;
      const bad = [];
      if (diff.fraction > STABILITY.maxDiffFraction) {
        bad.push(`${diff.pixels} px (${(diff.fraction * 100).toFixed(4)} %) over the `
          + `${(STABILITY.maxDiffFraction * 100).toFixed(2)} % ceiling`);
      }
      if (metricDrift.value !== null && metricDrift.value > STABILITY.maxMetricDrift) {
        bad.push(`${metricDrift.worst} moved ${(metricDrift.value * 100).toFixed(2)} %`);
      }
      if (bad.length) { failed++; problems.push(`${name}/${s.id}: unstable — ${bad.join('; ')}`); }
    }
    manifest.viewports[name].stability = {
      contract: STABILITY,
      byte_identical: identical,
      stations: manifest.viewports[name].shots.length,
      passed: failed === 0,
    };
    console.log(`  stability: ${failed === 0 ? 'PASS' : `FAIL — ${failed} station(s)`}`
      + ` · byte-identical ${identical}/${manifest.viewports[name].shots.length}`);
  }
}

fs.writeFileSync(path.join(OUT, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`\nmanifest: ${path.join(OUT, 'manifest.json')}`);

if (WANT_METRICS) {
  console.log('\nmetric                     station            mobile    desktop');
  const rows = [
    ['skyline breaks (all)', (m) => m.horizonTimber.coverageAll],
    ['skyline breaks (centre)', (m) => m.horizonTimber.coverageCentralTwoThirds],
    ['horizon TIMBER (all)', (m) => m.horizonTimber.timberOnly?.coverageAll ?? null],
    ['horizon TIMBER (centre)',
      (m) => m.horizonTimber.timberOnly?.coverageCentralTwoThirds ?? null],
    ['…of which was the town', (m) => m.horizonTimber.timberOnly?.structureShareOfBreaks ?? null],
    ['crown fine-detail ratio', (m) => m.crown.fineDetailRatio],
    ['sunlit crown G-B', (m) => m.crown.sunlitGminusB],
    ['shadow darkest decile L', (m) => m.shadow.darkestDecileL],
    ['literal black px', (m) => m.shadow.literalBlackPixels],
    ['high-pass RMS far', (m) => m.depthBandHighPassRms.far],
    ['high-pass RMS near', (m) => m.depthBandHighPassRms.near],
    // The recipe's answer, then what the head-free capture says it was about.
    ['flower load (recipe)', (m) => m.flower.load],
    ['BLOOM share of hued', (m) => m.flower.bloom?.shareOfHued ?? null],
    ['BLOOM share of ground', (m) => m.flower.bloom?.shareOfGround ?? null],
    ['bloom px', (m) => m.flower.bloom?.headPixels ?? null],
    ['…recipe recall', (m) => m.flower.bloom?.recipeRecall ?? null],
    ['…recipe precision', (m) => m.flower.bloom?.recipePrecision ?? null],
  ];
  for (const st of STATIONS) {
    for (const [label, read] of rows) {
      const cell = (v) => {
        const s = manifest.viewports[v]?.shots.find((x) => x.id === st.id);
        return s?.metrics ? String(read(s.metrics)).padStart(8) : '       -';
      };
      console.log(`${label.padEnd(26)} ${st.id.padEnd(18)} ${cell('mobile')}   ${cell('desktop')}`);
    }
  }
}

server.close();

if (problems.length) {
  console.log(`\n${problems.length} problem(s):`);
  for (const p of problems) console.log(`  ${p}`);
  process.exit(1);
}
console.log('\nCRITIC SHOTS OK');
