#!/usr/bin/env node
/**
 * THE FRAME GOVERNOR HOLDS A FRAME STEADY AND LEAVES A STILL ONE ALONE (T-2555).
 *
 * `renderers/web/js/frame-governor.js` is pure logic, so this drives it with
 * synthetic frame times: a device that holds 60 is never touched; a slow one
 * is drawn at fewer pixels down to the floor and never past it; one that cannot
 * hold 60 at the floor and can hold 30 is paced to 30, probes 60 again, and is
 * unpaced when 30 fails too; `light` refreshes the shadow every second moving
 * frame; and every one of those is neutral again the moment the camera rests,
 * or always under Fixed. No browser.
 *
 * T-2829: a device that draws at a rate of its own between 60 and 30 (a 120 Hz
 * display's every third vsync) is never paced to 30, a pace is earned over
 * `paceAfter` windows, and a step down that bought nothing stops the ladder —
 * then the owner's turn, modelled (tools/model_governor_phone.mjs), reads no
 * worse under Adaptive than under Fixed.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { createFrameGovernor, GOVERNOR, describeGovernor } = await import(
  pathToFileURL(path.join(root, 'renderers/web/js/frame-governor.js')).href);

let passed = 0;
const ok = (name, fn) => { fn(); passed += 1; console.log(`  ok  ${name}`); };

/**
 * A device as a function of the scale it is drawn at: `costMs(scale)` is the
 * frame's cost. rAF fires every `vsync` ms; a drawn frame occupies
 * ceil(cost / vsync) vsyncs, and a paced governor skips rAFs it is too early for.
 */
const clocks = new WeakMap();
function drive(gov, { frames, costMs, moving = () => true, vsync = 1000 / 60 }) {
  // Each governor keeps its own clock across drives, as a page's rAF does.
  let t = clocks.get(gov) ?? 0;
  const drawnAt = [];
  let busyUntil = 0;
  for (let rafs = 0; drawnAt.length < frames && rafs < frames * 20; rafs++) {
    t += vsync;
    if (t < busyUntil) continue;
    if (!gov.shouldDraw(t)) continue;
    const cost = costMs(gov.scale);
    busyUntil = t + Math.max(vsync, Math.ceil(cost / vsync) * vsync) - 0.01;
    drawnAt.push({ t, scale: gov.scale, pace: gov.pace, shadow: gov.shadowFresh });
    gov.frameDrawn(t, moving(drawnAt.length));
  }
  clocks.set(gov, t);
  return drawnAt;
}

ok('a device that holds 60 is never touched while it moves', () => {
  const g = createFrameGovernor();
  const f = drive(g, { frames: 300, costMs: () => 9 });
  assert.ok(f.every((x) => x.scale === 1 && x.pace === 1));
});

ok('a slow device steps its scale down, and never under the floor', () => {
  const g = createFrameGovernor();
  // 60 ms at full scale, falling with the pixels: never reaches 60 or 30.
  const f = drive(g, { frames: 400, costMs: (s) => 60 * s * s });
  const scales = f.map((x) => x.scale);
  assert.ok(Math.min(...scales) >= GOVERNOR.floor - 1e-9, `min ${Math.min(...scales)}`);
  assert.equal(g.scale, GOVERNOR.floor);
  for (let i = 1; i < scales.length; i++) {
    assert.ok(scales[i] <= scales[i - 1] + 1e-9, 'a device that never has headroom never steps up');
    assert.ok(scales[i] >= scales[i - 1] * GOVERNOR.stepDownMin - 1e-9, 'no step cuts more than stepDownMin');
  }
});

ok('a device that cannot hold 30 at the floor is not paced', () => {
  const g = createFrameGovernor();
  drive(g, { frames: 400, costMs: (s) => 120 * s * s });
  assert.equal(g.scale, GOVERNOR.floor);
  assert.equal(g.pace, 1, 'pacing a 54 ms frame would only add an idle rAF');
});

ok('one that cannot hold 60 at the floor and can hold 30 is paced to a steady 30', () => {
  const g = createFrameGovernor();
  // 40 ms at full; 18 ms at the floor — over 60's budget, inside 30's.
  const f = drive(g, { frames: 300, costMs: (s) => 40 * s * s });
  const paced = f.filter((x) => x.pace === 2);
  assert.ok(paced.length > 100, `paced ${paced.length} of ${f.length}`);
  // Paced frames are drawn every other 60 Hz vsync: 33.3 ms apart, steady.
  const gaps = [];
  for (let i = 1; i < f.length; i++) if (f[i].pace === 2 && f[i - 1].pace === 2) gaps.push(f[i].t - f[i - 1].t);
  assert.ok(gaps.length > 50 && gaps.every((d) => Math.abs(d - 1000 / 30) < 0.5), `gaps ${[...new Set(gaps.map((d) => d.toFixed(1)))]}`);
});

ok('paced, it probes 60 again after probeMs of moving, and paces again when 60 still fails', () => {
  const g = createFrameGovernor();
  const f = drive(g, { frames: 900, costMs: (s) => 40 * s * s });
  let back = 0;
  for (let i = 1; i < f.length; i++) if (f[i - 1].pace === 2 && f[i].pace === 1) back += 1;
  // 900 frames, most at 33 ms ≈ 29 s of moving: a probe every 8 s or so.
  assert.ok(back >= 2 && back <= 5, `probes ${back}`);
  const first = f.findIndex((x) => x.pace === 2);
  assert.ok(f.slice(first).filter((x) => x.pace === 1).length < 60, 'a probe lasts about one window');
});

ok('a device that gets faster is stepped back up to the ceiling', () => {
  const g = createFrameGovernor();
  drive(g, { frames: 200, costMs: (s) => 60 * s * s });
  assert.ok(g.scale < 1);
  drive(g, { frames: 300, costMs: () => 6 });
  assert.equal(g.scale, 1);
  assert.equal(g.pace, 1);
});

ok('a device on the boundary does not see-saw: a failed step up doubles the wait', () => {
  const g = createFrameGovernor();
  // Holds 60 at 0.9 of the ceiling and not at 1.
  const f = drive(g, { frames: 3600, costMs: (s) => (s > 0.95 ? 20 : 12) });
  let ups = 0;
  for (let i = 1; i < f.length; i++) if (f[i].scale > f[i - 1].scale) ups += 1;
  // Two minutes of moving. Without the backoff this climbs 0.85 → 0.94 → 1 and
  // falls back every seven windows, about 100 steps up; with it the failing step
  // is retried at most every 48 windows, about eight seconds.
  assert.ok(ups >= 1 && ups <= 16, `steps up ${ups}`);
});

ok('the moment the camera rests, scale, pace and shadow are neutral', () => {
  const g = createFrameGovernor({ tier: 'light' });
  drive(g, { frames: 300, costMs: (s) => 40 * s * s });
  assert.ok(g.scale < 1 && g.pace === 2);
  const f = drive(g, { frames: 10, costMs: () => 40, moving: () => false });
  // A rest is restFrames still frames: a single skipped input is not one.
  assert.ok(f[GOVERNOR.restFrames].scale === 1 && f[GOVERNOR.restFrames].pace === 1);
  assert.ok(f.slice(GOVERNOR.restFrames).every((x) => x.scale === 1 && x.pace === 1 && x.shadow));
  assert.equal(g.state.moving, false);
});

ok('one still frame between moving ones is not a rest', () => {
  const g = createFrameGovernor();
  drive(g, { frames: 200, costMs: (s) => 60 * s * s });
  const before = g.scale;
  assert.ok(before < 1);
  drive(g, { frames: 1, costMs: () => 60, moving: () => false });
  assert.equal(g.scale, before);
});

ok('on light, a moving frame re-renders the shadow every second frame; elsewhere every frame', () => {
  const light = createFrameGovernor({ tier: 'light' });
  const f = drive(light, { frames: 60, costMs: () => 9 });
  const fresh = f.slice(1).filter((x) => x.shadow).length;
  assert.ok(Math.abs(fresh - 59 / 2) <= 1, `fresh ${fresh} of 59`);
  assert.equal(light.state.shadowEvery, 2);
  const full = createFrameGovernor({ tier: 'full' });
  assert.ok(drive(full, { frames: 60, costMs: () => 9 }).every((x) => x.shadow));
});

ok('Fixed holds every frame neutral, however slow', () => {
  const g = createFrameGovernor({ enabled: false, tier: 'light' });
  const f = drive(g, { frames: 300, costMs: (s) => 40 * s * s });
  assert.ok(f.every((x) => x.scale === 1 && x.pace === 1 && x.shadow));
  assert.equal(g.state.mode, 'fixed');
  // And switching to Fixed mid-move is neutral at once.
  const h = createFrameGovernor();
  drive(h, { frames: 300, costMs: (s) => 40 * s * s });
  h.setEnabled(false);
  assert.ok(h.scale === 1 && h.pace === 1 && h.shadowFresh);
});

ok('a forced state (the harness) is undone by a rest like any other, and Fixed ignores it', () => {
  const g = createFrameGovernor();
  g.force({ scale: 0.1, pace: 2 });
  assert.equal(g.scale, GOVERNOR.floor, 'force is clamped to the floor');
  assert.equal(g.pace, 2);
  drive(g, { frames: GOVERNOR.restFrames, costMs: () => 9, moving: () => false });
  assert.ok(g.scale === 1 && g.pace === 1);
  const f = createFrameGovernor({ enabled: false });
  f.force({ scale: 0.67, pace: 2 });
  assert.ok(f.scale === 1 && f.pace === 1);
});

ok('a gap (a hidden tab, a long task) is not read as a frame time', () => {
  const g = createFrameGovernor();
  let t = 0;
  for (let i = 0; i < 50; i++) { t += i % 2 ? 16.7 : 900; g.frameDrawn(t, true); }
  assert.equal(g.scale, 1);
});

ok('the state reports what it did, and Settings can say it', () => {
  const g = createFrameGovernor();
  const seen = [];
  const h = createFrameGovernor({ onChange: (s) => seen.push(s) });
  drive(h, { frames: 300, costMs: (s) => 40 * s * s });
  assert.ok(seen.some((s) => s.pace === 2 && s.fps === 30 && s.moving));
  const s = h.state;
  for (const k of ['mode', 'scale', 'pace', 'fps', 'moving', 'shadowEvery', 'decisions']) assert.ok(k in s, k);
  assert.match(describeGovernor(s, 0.67), /steady 30/);
  assert.match(describeGovernor(g.state, 1), /^Adaptive: at the sharpness chosen/);
  assert.match(describeGovernor({ ...g.state, mode: 'fixed' }, 1), /^Fixed/);
});

// ---- T-2829 ------------------------------------------------------------- //

const HZ120 = 1000 / 120;
const changes = (f, k) => f.slice(1).filter((x, i) => x[k] !== f[i][k]).length;

ok('a 120 Hz device drawing every third vsync (25 ms) is never paced to 30', () => {
  const g = createFrameGovernor({ tier: 'light' });
  // 22 ms whatever the scale: not fill-bound, on the 25 ms rung of a 120 Hz grid.
  const f = drive(g, { frames: 600, costMs: () => 22, vsync: HZ120 });
  assert.ok(f.every((x) => x.pace === 1), 'pacing would hold every 25 ms frame back to 33 ms');
  const gaps = f.slice(1).map((x, i) => x.t - f[i].t);
  assert.ok(gaps.every((d) => Math.abs(d - 25) < 0.1), `gaps ${[...new Set(gaps.map((d) => d.toFixed(1)))]}`);
});

ok('a step down that bought nothing stops the ladder: one resize, not three', () => {
  const g = createFrameGovernor({ tier: 'light' });
  const f = drive(g, { frames: 600, costMs: () => 22, vsync: HZ120 });
  assert.equal(changes(f, 'scale'), 1, 'one step down, and no more');
  assert.ok(g.scale < 1 && g.scale > GOVERNOR.floor);
  assert.equal(g.state.scaleHeld, true);
  // A device that IS fill-bound still walks the whole ladder (the T-2555 check above
  // holds it to the floor); here, the same at 60 Hz with cost falling with the pixels.
  const h = createFrameGovernor();
  drive(h, { frames: 400, costMs: (s) => 60 * s * s });
  assert.equal(h.scale, GOVERNOR.floor, 'each step that paid was followed by the next');
});

ok('the held ladder is kept across a rest, and let go on a tier or setting change', () => {
  const g = createFrameGovernor({ tier: 'light' });
  drive(g, { frames: 300, costMs: () => 22, vsync: HZ120 });
  drive(g, { frames: 5, costMs: () => 22, vsync: HZ120, moving: () => false });
  assert.equal(g.scale, 1, 'a rest is still neutral');
  const again = drive(g, { frames: 300, costMs: () => 22, vsync: HZ120 });
  assert.ok(again.every((x) => x.scale === 1 && x.pace === 1), 'the next move does not resize again');
  g.setTier('light');
  assert.equal(g.state.scaleHeld, true, 'the same tier is not a change');
  g.setTier('balanced');
  assert.equal(g.state.scaleHeld, false);
  drive(g, { frames: 300, costMs: () => 22, vsync: HZ120 });
  assert.equal(g.state.scaleHeld, true);
  g.setEnabled(true);
  assert.equal(g.state.scaleHeld, false);
});

ok('the 60/30 alternation T-2555 paces is still paced, at 60 Hz', () => {
  const g = createFrameGovernor();
  let n = 0;
  // Every other frame misses a 60 Hz vsync, whatever the scale.
  const f = drive(g, { frames: 400, costMs: () => (n++ % 2 ? 20 : 12) });
  assert.equal(g.pace, 2);
  const paced = f.filter((x) => x.pace === 2).length;
  assert.ok(paced > 250, `paced ${paced} of ${f.length}`);
});

ok('one window whose median lands on 33 ms is not a pace; three in a row are', () => {
  const g = createFrameGovernor();
  let t = 0;
  const feed = (ms) => { for (const d of ms) { t += d; g.frameDrawn(t, true); } };
  const win = (slow) => Array.from({ length: 10 }, (_, i) => (i < slow ? 1000 / 30 : 25));
  feed([25]);
  feed(win(3)); // p80 33 ms: a step down
  feed(win(3)); // the same p80: the step bought nothing, the ladder is held
  assert.equal(g.state.scaleHeld, true);
  feed(win(6)); feed(win(3)); feed(win(6)); feed(win(3));
  assert.equal(g.pace, 1, 'a window that asks, then one that does not, is not a pace');
  feed(win(6)); feed(win(6));
  assert.equal(g.pace, 1);
  feed(win(6));
  assert.equal(g.pace, 2);
});

const { PHONE, OWNER, meanOf } = await import(pathToFileURL(path.join(root, 'tools/model_governor_phone.mjs')).href);
ok("the owner's turn, modelled: Adaptive no worse than Fixed in sd, p95 or rate", () => {
  const fixed = meanOf({ ...PHONE.turn, adaptive: false });
  // The model is his Fixed turn first: within a millisecond on mean, sd, median and p95.
  const [draws, mean, sd, median, p95] = OWNER.turn[0];
  assert.ok(Math.abs(fixed.mean - mean) < 1 && Math.abs(fixed.sd - sd) < 1 && Math.abs(fixed.median - median) < 1
    && Math.abs(fixed.p95 - p95) < 1.5 && Math.abs(fixed.draws - draws) < 6, JSON.stringify(fixed));
  const adaptive = meanOf({ ...PHONE.turn, adaptive: true });
  assert.ok(adaptive.sd <= fixed.sd + 0.1, `sd ${fixed.sd.toFixed(2)} -> ${adaptive.sd.toFixed(2)}`);
  assert.ok(adaptive.p95 <= fixed.p95 + 0.2, `p95 ${fixed.p95.toFixed(2)} -> ${adaptive.p95.toFixed(2)}`);
  assert.ok(adaptive.mean <= fixed.mean + 0.5, `mean ${fixed.mean.toFixed(2)} -> ${adaptive.mean.toFixed(2)}`);
  assert.ok(adaptive.resizes <= 1.5, `resizes ${adaptive.resizes}`);
});

console.log(`PASS — ${passed} frame-governor checks`);
