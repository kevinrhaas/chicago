#!/usr/bin/env node
/**
 * T-2943 — a visitor walks through a building's modelled passage.
 *
 * The walker holds every footprint solid; a sidecar's `footprint.passages` carves the
 * opening the model really has (Glessner's carriage passage, Prairie Avenue to the court)
 * wherever its clear height clears the eye. Here: a box with a passage through it and the
 * same box without one, on flat ground — through, the walk passes and the side walls hold;
 * without, it stops at the façade; a rider whose eye would strike the soffit is stopped.
 * Then the real 1904 Glessner sidecar: from Prairie Avenue through the passage into the
 * court, the visitor never inside the masonry and held off both reveals.
 *
 *   node tools/test_walker_passage.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createWalker, footprintsFrom, passageLane, WALK, HEADROOM_MARGIN_M, LANE_REACH_M } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');
const { passageGroundFrom, passageDepth } = await import('../renderers/web/js/passage-ground.js');

const flat = { walkHeight: () => 0, surfaceHeight: () => 0, isWater: () => false };
const inside = (e, n, pts) => {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};

/** Walk `seconds` at 60 fps holding forward (and `strafe`), facing `yawDeg` (compass). */
function walk(footprints, from, yawDeg, seconds, { strafe = 0 } = {}) {
  const camera = new THREE.PerspectiveCamera();
  const w = createWalker({ camera, terrain: flat, footprints, spawn: { local_e: from[0], local_n: from[1], yaw_deg: yawDeg } });
  const intent = createIntent();
  const path = [];
  for (let i = 0; i < seconds * 60; i++) {
    intent.forward = 1; intent.strafe = strafe;
    w.update(1 / 60, intent);
    path.push([w.state.e, w.state.n, w.state.groundY]);
  }
  return { w, path, end: path.at(-1) };
}

const box = [[0, 0], [10, 0], [10, 10], [0, 10]];
const passage = { kind: 'carriage passage', polygon: [[0, 6], [0, 4], [10, 4], [10, 6]], open_edges: [[0, 1], [2, 3]], floor_m: 0, clear_m: 2.2 };
const reg = (fp) => new Map([['b', { id: 'b', sidecar: { id: 'b', placement: { local_e: 0, local_n: 0, rotation_deg: 0 }, footprint: fp } }]]);
const speedWas = WALK.speed, eyeWas = WALK.eyeHeight;
WALK.speed = 1.5;
try {
  // ---- the lane: open ends reach past the walls; the side walls are the other edges
  const lane = passageLane(passage);
  assert.equal(lane.walls.length, 2, 'two side walls, two open ends');
  assert.deepEqual(lane.lane[0], [-LANE_REACH_M, 6]); assert.deepEqual(lane.lane[2], [10 + LANE_REACH_M, 4]);
  assert.equal(passageLane({ polygon: [[0, 0], [1, 1]] }), null, 'a malformed passage is ignored');
  assert.equal(HEADROOM_MARGIN_M, 0.1);

  // ---- without the passage: the façade stops the walk
  const solid = footprintsFrom(reg({ polygon: box }));
  assert.equal(solid[0].passages, undefined, 'a footprint with no passage is as before');
  const blocked = walk(solid, [-3, 5], 90, 8);
  assert(blocked.end[0] < -WALK.radius + 0.01, `without the passage the walk stops at the façade (${blocked.end[0].toFixed(2)})`);

  // ---- with it: through, never inside the masonry, held off the reveals
  const open = footprintsFrom(reg({ polygon: box, passages: [passage] }));
  assert.equal(open[0].passages.length, 1);
  const through = walk(open, [-3, 5], 90, 12);
  assert(through.end[0] > 12, `with the passage the walk comes out the far side (${through.end[0].toFixed(2)})`);
  for (const [e, n] of through.path) assert(!(inside(e, n, box) && (n < 4 + WALK.radius - 1e-6 || n > 6 - WALK.radius + 1e-6)), `never in the walls at ${e.toFixed(2)},${n.toFixed(2)}`);
  // Strafing into a reveal mid-passage: held WALK.radius off it.
  const scrape = walk(open, [2, 5], 90, 3, { strafe: 1 });
  for (const [e, n] of scrape.path) if (e > 0 && e < 10) assert(n >= 4 + WALK.radius - 1e-6 && n <= 6 - WALK.radius + 1e-6, `held off the reveal at ${e.toFixed(2)},${n.toFixed(3)}`);
  // Beside the mouth, outside the lane, the façade still stands.
  const beside = walk(open, [-3, 8], 90, 6);
  assert(beside.end[0] < -WALK.radius + 0.01, 'the wall beside the opening is still a wall');
  // A rider's eye (the seat raises it) that would strike the soffit is stopped at the mouth.
  WALK.eyeHeight = 1.68 + 0.75;
  const rider = walk(open, [-3, 5], 90, 8);
  assert(rider.end[0] < 0, `a rider who would strike the 2.2 m soffit stops (${rider.end[0].toFixed(2)})`);
  WALK.eyeHeight = eyeWas;

  // ---- the real thing: Glessner's sidecar, Prairie Avenue to the court, on flat ground
  const side = JSON.parse(fs.readFileSync(new URL('../data/sidecars/1904/glessner_house.json', import.meta.url)));
  const gl = footprintsFrom(new Map([[side.id, { id: side.id, sidecar: side }]]));
  assert.equal(gl[0].passages?.length, 1, 'Glessner declares its carriage passage');
  const g = gl[0].passages[0];
  assert(g.clear >= 1.68 + HEADROOM_MARGIN_M, `its ${g.clear} m clears a standing eye`);
  // The mouth's centre on Prairie, and the court end's centre, in world metres.
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const mouth = mid(g.pts[0], g.pts[1]), court = mid(g.pts[2], g.pts[3]);
  const bearing = (Math.atan2(court[0] - mouth[0], court[1] - mouth[1]) * 180 / Math.PI + 360) % 360;
  const start = [mouth[0] + (mouth[0] - court[0]) * 0.4, mouth[1] + (mouth[1] - court[1]) * 0.4];
  const run = walk(gl, start, bearing, 14);
  const past = (court[0] - mouth[0]) * (run.end[0] - court[0]) + (court[1] - mouth[1]) * (run.end[1] - court[1]);
  assert(past > 0, `from Prairie Avenue the walk comes out into the court (ended ${run.end.map((v) => v.toFixed(2))})`);
  for (const [e, n] of run.path) {
    if (!inside(e, n, gl[0].pts)) continue;
    assert(inside(e, n, g.pts), `inside the house only within the passage (${e.toFixed(2)},${n.toFixed(2)})`);
  }
  // T-2976: the floor sunk where the HABS sheets draw it, the passage clears a seated
  // driver (eye 1.68 + 0.5 m) and the walk steps down onto the paving, not the field.
  assert(g.clear >= 1.68 + 0.5 + HEADROOM_MARGIN_M, `its ${g.clear} m clears a driver's eye`);
  const sunk = passageGroundFrom(new Map([[side.id, { id: side.id, sidecar: side }]]));
  // T-2978: and the court ground's fall to the mouth, four quads (bank and low ground,
  // each out to the section plane and on to where it rises back to the court's level).
  assert.equal(sunk.length, 8, 'approach, threshold, passage floor, court ramp and the court fall are declared');
  const atMouth = passageDepth(sunk, mouth[0] + (mouth[0] - court[0]) * 0.005, mouth[1] + (mouth[1] - court[1]) * 0.005);
  assert(Math.abs(atMouth - -0.3536) < 0.01, `the mouth's paving is 1.16 ft under the sidewalk (${atMouth})`);
  const atCourt = passageDepth(sunk, court[0] - (mouth[0] - court[0]) * 0.001, court[1] - (mouth[1] - court[1]) * 0.001);
  assert(Math.abs(atCourt - -0.6858) < 0.01, `the court mouth's paving is 2.45 ft under the court face's zero, 9.65 ft under its lintel (${atCourt})`);
  assert.equal(passageDepth(sunk, mouth[0] + 50, mouth[1]), null, 'off the carriage way the field is the ground');
  const sunkTerrain = { ...flat, walkHeight: (e, n) => passageDepth(sunk, e, n) ?? 0 };
  {
    const camera = new THREE.PerspectiveCamera();
    const w = createWalker({ camera, terrain: sunkTerrain, footprints: gl, spawn: { local_e: start[0], local_n: start[1], yaw_deg: bearing } });
    const intent = createIntent();
    let lowest = Infinity;
    for (let i = 0; i < 14 * 60; i++) { intent.forward = 1; w.update(1 / 60, intent); lowest = Math.min(lowest, w.state.groundY); }
    const past = (court[0] - mouth[0]) * (w.state.e - court[0]) + (court[1] - mouth[1]) * (w.state.n - court[1]);
    assert(past > 0, 'down the approach, through the sunk passage and up the ramp into the court');
    assert(lowest < -0.3, `the walk went down onto the sunk floor (lowest ${lowest.toFixed(3)} m)`);
  }
  const solidG = footprintsFrom(new Map([[side.id, { id: side.id, sidecar: { ...side, footprint: { ...side.footprint, passages: undefined } } }]]));
  const before = walk(solidG, start, bearing, 14);
  const gone = (court[0] - mouth[0]) * (before.end[0] - mouth[0]) + (court[1] - mouth[1]) * (before.end[1] - mouth[1]);
  assert(gone < 0, 'without the passage the same walk stops on Prairie Avenue, as the owner found it');
} finally { WALK.speed = speedWas; WALK.eyeHeight = eyeWas; }
console.log('WALKER PASSAGE PASS — a declared passage is walked through where its soffit clears the eye, held off its reveals, the façade beside it still a wall, a rider stopped; Glessner from Prairie Avenue into the court, which a solid footprint refuses');
