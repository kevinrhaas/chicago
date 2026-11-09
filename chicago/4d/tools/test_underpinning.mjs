#!/usr/bin/env node
/**
 * T-3492: renderers/web/js/underpinning.js, the stone under a sill carried level
 * over sloping ground — its pieces, with no browser and no terrain.
 *
 *   node tools/test_underpinning.mjs
 *
 * Holds: a wall run under every footprint edge whose faces point OUT (a wrong
 * winding draws the stone inside out); the stone reaches below the lowest ground
 * and up to the sill; a pier under a gable stack's feet and none under the
 * notched corner log ends; a doorstep only where the door stands clear of its
 * ground, its risers even and no taller than STEP_RISE_M, its top step one tread
 * deep; and the building's sill set at the highest ground plus its clearance.
 */
import fs from 'node:fs';
import assert from 'node:assert/strict';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const js = (name) => new URL(`../renderers/web/js/${name}`, import.meta.url).href;
const text = fs.readFileSync(new URL('../renderers/web/js/underpinning.js', import.meta.url), 'utf8')
  .replace("from 'three'", `from ${JSON.stringify(vendor)}`)
  // scene-loader pulls three by its bare name; the pieces never resolve a base.
  .replace("import { resolveBases } from './scene-loader.js';", 'const resolveBases = () => ({ assetBase: null });')
  .replace("from './angles.js'", `from ${JSON.stringify(js('angles.js'))}`);
const M = await import(`data:text/javascript;base64,${Buffer.from(text).toString('base64')}`);

let passed = 0;
const test = (name, fn) => { fn(); passed += 1; console.log(`PASS ${name}`); };

// The factory's plan: 14.417 x 8.504 m, front on the max-v edge, door at u 6.69-7.73.
const polygon = [[0, 0], [14.417, 0], [14.417, 8.504], [0, 8.504]];
const doors = [[6.6885, 7.7285]];
// local (x, z) = (u, -v). A slope rising 0.93 m from the (0, 0) corner to the far one,
// read relative to a sill set 0.20 m over the high corner.
const slope = (x, z) => 0.93 * ((x / 14.417) * 0.6 + (-z / 8.504) * 0.4);
const sillY = 0.93 + 0.2;
const ground = (x, z) => slope(x, z) - sillY;
// Feet: wall samples, the notched corner log ends 0.24 m out, and a gable stack at u -0.9..0.
const feet = [];
for (let u = 0; u <= 14.417; u += 1) { feet.push([u, 0], [u, -8.504]); }
for (const [x, z] of [[-0.24, 0.24], [14.66, 0.24], [-0.24, -8.74], [14.66, -8.74]]) feet.push([x, z]);
for (const [x, z] of [[-0.9, -3.8], [-0.9, -4.7], [-0.5, -3.8], [-0.5, -4.7]]) feet.push([x, z]);

const { boxes, steps, lowest } = M.underpinningPieces({ polygon, feet, doors, frontV: 8.504, ground });

const area = (c) => c.reduce((a, [x0, z0], i) => { const [x1, z1] = c[(i + 1) % c.length]; return a + x0 * z1 - x1 * z0; }, 0) / 2;
const centre = (c) => [c.reduce((s, p) => s + p[0], 0) / 4, c.reduce((s, p) => s + p[1], 0) / 4];

test('every box is wound so its faces point out', () => {
  for (const b of boxes) assert(area(b.corners) < 0, `box at ${centre(b.corners)} is wound the wrong way`);
});

const doorRise = -ground(7.2085, -8.504 - M.STEP_GROUND_AT_M);
const wantSteps = Math.max(2, Math.ceil(doorRise / M.STEP_RISE_M)) - 1;

test('a wall run under each of the four edges, one stack pier, and the door\'s steps', () => {
  assert(wantSteps >= 1);
  assert.equal(boxes.length, 4 + 1 + wantSteps, `got ${boxes.length} boxes`);
  assert.equal(steps, wantSteps);
});

test('the wall runs reach from below the lowest ground to the sill', () => {
  assert(Math.abs(lowest - ground(0, 0)) < 1e-9 || lowest < ground(0, 0), 'lowest ground not found');
  for (const b of boxes.slice(0, 4)) {
    assert.equal(b.y1, 0);
    assert(Math.abs(b.y0 - (lowest - M.BURY_M)) < 1e-9);
  }
  assert(lowest + sillY < 1e-9 + 0.0 + 1e-6, 'the low corner is the slope foot');
});

test('the stone stands proud of the wall faces and in from them', () => {
  const xs = boxes.slice(0, 4).flatMap((b) => b.corners.map((p) => p[0]));
  assert(Math.abs(Math.min(...xs) - -M.PROUD_M) < 1e-9 && Math.abs(Math.max(...xs) - (14.417 + M.PROUD_M)) < 1e-9);
});

test('the pier stands under the stack, not under a corner log end', () => {
  const pier = boxes[4];
  const [cx, cz] = centre(pier.corners);
  assert(cx < 0 && cz < -3.5 && cz > -5, `pier at ${cx}, ${cz}`);
  const pxs = pier.corners.map((p) => p[0]);
  assert(Math.max(...pxs) >= -1e-9, 'the pier reaches back to the gable wall');
});

test('the doorstep: even risers no taller than the rule, top step one tread deep', () => {
  const step = boxes[5];
  const rise = doorRise;
  const risers = Math.max(2, Math.ceil(rise / M.STEP_RISE_M));
  assert(rise / risers <= M.STEP_RISE_M + 1e-9);
  assert(Math.abs(step.y1 - -rise / risers) < 1e-9);
  const zs = step.corners.map((p) => p[1]);
  assert(Math.abs((Math.max(...zs) - Math.min(...zs)) - M.STEP_TREAD_M) < 1e-9);
  const xs = step.corners.map((p) => p[0]);
  assert(Math.min(...xs) < 6.6885 && Math.max(...xs) > 7.7285, 'the step is wider than the door');
});

test('a door at its own ground gets no step', () => {
  const flat = () => -0.03;
  const r = M.underpinningPieces({ polygon, feet: [], doors, frontV: 8.504, ground: flat });
  assert.equal(r.steps, 0);
});

test('a tall rise takes more steps, each lower one deeper', () => {
  const r = M.underpinningPieces({ polygon, feet: [], doors, frontV: 8.504, ground: () => -0.7 });
  assert.equal(r.steps, Math.ceil(0.7 / M.STEP_RISE_M) - 1);
  const stepBoxes = r.boxes.slice(4);
  for (let i = 1; i < stepBoxes.length; i += 1) {
    assert(stepBoxes[i].y1 < stepBoxes[i - 1].y1);
    const depth = (b) => { const zs = b.corners.map((p) => p[1]); return Math.max(...zs) - Math.min(...zs); };
    assert(depth(stepBoxes[i]) > depth(stepBoxes[i - 1]));
  }
});

test('the sill stands at the highest ground plus its clearance', () => {
  assert.equal(M.underpinnedHeight(1.53, 2.46, 0.2), 2.46 + 0.2);
});

console.log(`test_underpinning: ${passed} passed`);
