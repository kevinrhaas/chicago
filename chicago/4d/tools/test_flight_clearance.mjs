#!/usr/bin/env node
/**
 * T-3734 (the owner, 2026-11-23: "when you fly on the jaunts in 1904 and probably others you
 * will often clip fly though a building or chimney ... you should fly over or around"): both
 * flights a jaunt makes, the timed glide and the steered Fly ride, keep the eye over what stands
 * in their way. Node only: flight-clearance.js, and travel.js driving a real walker over a
 * street of tall houses with chimneys, with the clearance and (to prove the check bites) without.
 *
 *   node tools/test_flight_clearance.mjs
 */
import assert from 'node:assert/strict';
import { register } from 'node:module';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createWalker } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');
const { createTravel, glidePose } = await import('../renderers/web/js/travel.js');
const fc = await import('../renderers/web/js/flight-clearance.js');
const { createSkyline, clearanceProfile, envelope, distanceToPolygon, floorAhead, ABOVE_M, REACH_M, END_M } = fc;

// ---- the pure parts.
const sq = [[0, 0], [10, 0], [10, 10], [0, 10]];
assert.equal(distanceToPolygon(5, 5, sq), 0, 'inside is no distance');
assert(Math.abs(distanceToPolygon(13, 5, sq) - 3) < 1e-9);
assert(Math.abs(distanceToPolygon(13, 14, sq) - 5) < 1e-9, 'to the corner');
{
  const lift = envelope(Float32Array.from([0, 0, 0, 0, 10, 0, 0, 0, 0]), 2, 0.7);
  assert.equal(lift[4], 10);
  assert(Math.abs(lift[3] - 8.6) < 1e-5 && Math.abs(lift[5] - 8.6) < 1e-5, 'rises before and falls after, at the slope');
  assert(Math.abs(lift[0] - 4.4) < 1e-5);
}
console.log('PASS clearance arithmetic: polygon distance and the climb-before envelope');

// ---- a street of five tall houses, 20 m to the eaves and a chimney stack to 24 m, between two
// stands 12 m before the first and 12 m past the last. Ground at 1 m.
const GROUND = 1;
const houses = [0, 1, 2, 3, 4].map(i => ({ pts: [[20 + i * 24, -10], [40 + i * 24, -10], [40 + i * 24, 10], [20 + i * 24, 10]], top: GROUND + 24 }));
const skyline = createSkyline({ sources: () => houses, ground: () => GROUND });
assert.equal(skyline.needAt(200, 0), 0, 'open ground needs nothing');
assert.equal(skyline.needAt(30, 0), 24 + ABOVE_M, 'over a house: its top and the margin');
assert.equal(skyline.needAt(18, 0), 24 + ABOVE_M, `within ${REACH_M} m of its wall`);
assert.equal(skyline.needAt(16, 0), 0, 'and not beyond');
{
  const p = clearanceProfile(skyline.needAt, [[8, 0], [148, 0]]);
  assert.equal(p.need[0], 0, 'the stand it leaves is ground the walker stood on');
  assert(Math.max(...p.lift) === 24 + ABOVE_M);
  assert(floorAhead(skyline.needAt, 8, 0, 148, 0, 40) > 15, 'a steered ride 12 m short of the first house must already be climbing');
}
console.log('PASS skyline: tops, reach, the stands left out');

/** Every pose the eye takes, judged against the houses: how far under its clearance it went. */
function worstUnder(poses, a, b) {
  let worst = 0;
  for (const p of poses) {
    if (Math.hypot(p.e - a[0], p.n - a[1]) < END_M || Math.hypot(p.e - b[0], p.n - b[1]) < END_M) continue;
    const need = skyline.needAt(p.e, p.n) - ABOVE_M; // the building itself, with no margin
    if (need > 0) worst = Math.max(worst, need - p.altitude);
  }
  return worst;
}
const dry = { heightfield: { loaded: true, originE: -200, originN: -200, widthM: 600, depthM: 600 },
  surfaceHeight: () => GROUND, walkHeight: () => GROUND, isWater: () => false };

// ---- the glide (the flight to a jaunt's start and its closing look).
function glideRig(clearance) {
  const state = { e: 0, n: 0, yaw: 0, pitch: 0, groundY: GROUND, eyeY: GROUND + 1.68, altitude: 0, flying: false, bob: 0, speed: 0 };
  const intent = createIntent();
  const poses = [];
  const travel = createTravel({ walker: { state, resettle() {}, update() {} }, intent, settings: {}, clearance,
    setFly: on => { intent.flying = on; state.flying = on; },
    teleport: ({ local_e, local_n, altitude_m = null }) => {
      state.e = local_e; state.n = local_n; state.altitude = altitude_m ?? 0;
      poses.push({ e: local_e, n: local_n, altitude: altitude_m ?? 0 });
    } });
  return { travel, poses };
}
const legs = [
  ['a hop past one house', { e: 8, n: 0 }, { e: 52, n: 0 }],
  ['a short glide down the street', { e: 8, n: 0 }, { e: 152, n: 0 }],
  ['across the street diagonally', { e: 30, n: -40 }, { e: 100, n: 40 }],
];
for (const [what, a, b] of legs) {
  const from = { ...a, altitude: 1.68, yaw: 0, pitch: 0 }, to = { ...b, altitude: 1.68, yaw: 0, pitch: 0 };
  const before = glideRig(null);
  assert(before.travel.glide(from, to, {}));
  before.travel.simulate(30, 1 / 60);
  const old = worstUnder(before.poses, [a.e, a.n], [b.e, b.n]);
  assert(old > 1, `self-test: without the clearance, ${what} goes ${old.toFixed(1)} m into the houses`);
  const after = glideRig(skyline);
  let arrived = 0;
  assert(after.travel.glide(from, to, { onArrive: () => arrived++ }));
  after.travel.simulate(30, 1 / 60);
  assert.equal(arrived, 1, `${what}: it lands`);
  const under = worstUnder(after.poses, [a.e, a.n], [b.e, b.n]);
  assert(under <= 0, `${what}: the eye goes ${under.toFixed(2)} m into a house`);
  const last = after.poses.at(-1);
  assert.equal(last.e, b.e); assert.equal(last.n, b.n);
  // No jump: the lifted climb is no steeper than the glide's own climb was on a 150 m hop
  // (1.79 m a 60 Hz frame, measured on the unlifted glidePose 2026-11-23; 5.5 m on a 720 m one).
  let jump = 0;
  for (let i = 1; i < after.poses.length - 1; i++) jump = Math.max(jump, Math.abs(after.poses[i].altitude - after.poses[i - 1].altitude));
  assert(jump < 1.8, `${what}: the climb is flown, not a jump (${jump.toFixed(2)} m in a frame)`);
  console.log(`PASS glide, ${what}: was ${old.toFixed(1)} m inside, now clear (largest step ${jump.toFixed(2)} m a frame)`);
}
{
  // The closing look hovers over the place; a view inside a building is lifted out of it.
  const { travel, poses } = glideRig(skyline);
  assert(travel.glide({ e: 8, n: 0, altitude: 1.68, yaw: 0, pitch: 0 }, { e: 54, n: 0, altitude: 12, yaw: 0, pitch: -0.3 }, {}, { seconds: 6, hover: true }));
  travel.simulate(30, 1 / 30);
  assert(poses.at(-1).altitude >= 24 - GROUND + ABOVE_M - 1e-6, 'the hover ends above the roofs');
}
console.log('PASS closing look: hovers over the roofs, not inside them');

// ---- the steered Fly ride (Go to, and every jaunt leg flown between stops).
function flyRig(clearance, start) {
  const camera = new THREE.PerspectiveCamera();
  const walker = createWalker({ camera, terrain: dry, footprints: [], spawn: { local_e: start[0], local_n: start[1] } });
  const intent = createIntent();
  const travel = createTravel({ walker, intent, terrain: dry, settings: {}, clearance,
    setFly: on => { intent.flying = on; } });
  travel.setMode('fly');
  return { walker, intent, travel };
}
for (const [what, a, b] of [
  ['down the street of houses', [8, 0], [152, 0]],
  ['over one house to the next street', [30, -16], [30, 16]],
  ['diagonally across the block', [10, -30], [120, 30]],
]) {
  const results = [];
  for (const clearance of [null, skyline]) {
    const { walker, intent, travel } = flyRig(clearance, a);
    let arrived = 0;
    assert(travel.go({ kind: 'point', local_e: b[0], local_n: b[1], label: 'the stand' }, { onArrive: () => arrived++ }));
    const poses = [];
    for (let i = 0; i < 60 * 120 && travel.state.phase !== 'idle'; i++) {
      travel.update(1 / 60, intent); walker.update(1 / 60, intent); travel.afterWalk(intent, 1 / 60);
      const w = walker.state;
      poses.push({ e: w.e, n: w.n, altitude: w.eyeY - w.groundY });
    }
    results.push({ under: worstUnder(poses, a, b), arrived, at: [walker.state.e, walker.state.n] });
  }
  const [old, now] = results;
  assert(old.under > 1, `self-test: without the clearance, the ride ${what} goes ${old.under.toFixed(1)} m into a house`);
  assert.equal(now.arrived, 1, `${what}: it arrives`);
  assert(Math.hypot(now.at[0] - b[0], now.at[1] - b[1]) < 4, `${what}: on the stand`);
  assert(now.under <= 0, `${what}: the eye goes ${now.under.toFixed(2)} m into a house`);
  console.log(`PASS Fly ride ${what}: was ${old.under.toFixed(1)} m inside, now clear`);
}
{
  // A tower 60 m tall beside the stand: the ride climbs in place for several seconds, which is
  // not a stall, and still arrives.
  const tower = createSkyline({ sources: () => [{ pts: [[12, -8], [28, -8], [28, 8], [12, 8]], top: GROUND + 60 }], ground: () => GROUND });
  const { walker, intent, travel } = flyRig(tower, [6, 0]);
  let arrived = 0, stopped = null;
  travel.go({ kind: 'point', local_e: 60, local_n: 0, label: 'past the tower' }, { onArrive: () => arrived++, onStop: (r) => { stopped = r; } });
  let top = 0;
  for (let i = 0; i < 60 * 120 && travel.state.phase !== 'idle'; i++) {
    travel.update(1 / 60, intent); walker.update(1 / 60, intent); travel.afterWalk(intent, 1 / 60);
    top = Math.max(top, walker.state.eyeY - walker.state.groundY);
  }
  assert.equal(stopped, null, 'not stopped as stalled'); assert.equal(arrived, 1);
  assert(top >= 60 - GROUND, `over the tower (${top.toFixed(1)} m)`);
  console.log('PASS Fly ride beside a 60 m tower: climbs in place, then over it, and arrives');
}
// The glide's own shape is unchanged where nothing is in its way.
{
  const from = { e: 0, n: 0, altitude: 1.68, yaw: 0, pitch: 0 }, to = { e: 600, n: 400, altitude: 1.68, yaw: 1.2, pitch: -0.1 };
  const p = glidePose(from, to, 0.5);
  assert(p.altitude > 60 && Math.abs(p.u - 0.5) < 1e-9);
}
console.log('PASS flight clearance (T-3734)');
