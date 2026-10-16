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
  assert.equal(f.filter((x) => x.pace === 1 && x.scale === GOVERNOR.floor).length < 60, true, 'a probe lasts about one window');
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

console.log(`PASS — ${passed} frame-governor checks`);
