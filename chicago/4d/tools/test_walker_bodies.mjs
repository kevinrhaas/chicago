#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553 — the visitor on foot never walks into a person (owner, 2026-11-14, walking into a man
 * at Prairie and 18th and seeing the inside of his head: "you should not see inside people's
 * heads and bodies").
 *
 * walker.js holds its capsule off every drawn figure's disc (`setBodies`, `clearOfBodies`), and
 * human-spacing.js steps a walking figure round the visitor (`body`). With a flat ground and
 * stand-in figures:
 *   - walked straight at, a standing person stops the visitor at the touch, eye never nearer
 *     than WALK.radius + BODY_R_M; walked at a slant, the visitor slides round and goes on;
 *   - a sprint on a slow device (10 fps, a metre a frame) never tunnels through anyone;
 *   - someone walking into a standing visitor moves the visitor, never through them;
 *   - a wall wins over a person: pressed between, the visitor is never put in the building;
 *   - nobody is solid in the air (free-fly), and none at all before the layer is set;
 *   - a passer-by on a path through the visitor steps round them; a stander holds their ground.
 *
 *   node tools/test_walker_bodies.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createWalker, clearOfBodies, WALK } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const spacingSrc = await fs.readFile(new URL('renderers/web/js/human-spacing.js', here), 'utf8');
const { createHumanSpacing, VISITOR_M, VISITOR_RATE_M_S } = await import(data(spacingSrc));
const humansSrc = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
const BODY_R_M = Number(/export const BODY_R_M = ([\d.]+);/.exec(humansSrc)?.[1]);
assert(BODY_R_M > 0.2 && BODY_R_M < 0.5, `humans.js BODY_R_M read (${BODY_R_M})`);

const flat = { walkHeight: () => 0, surfaceHeight: () => 0, isWater: () => false };
const TOUCH = WALK.radius + BODY_R_M;
const near = (w, b) => Math.hypot(w.state.e - b.e, w.state.n - b.n);

function walker({ from = [0, 0], yaw = 0, footprints = [], bodies = null } = {}) {
  const camera = new THREE.PerspectiveCamera();
  const w = createWalker({ camera, terrain: flat, footprints, spawn: { local_e: from[0], local_n: from[1], yaw_deg: yaw } });
  if (bodies) w.setBodies(() => bodies.map((b) => ({ ...b, r: BODY_R_M })));
  return w;
}
const speedWas = WALK.speed, sprintWas = WALK.sprintSpeed;
try {
  WALK.speed = 1.5;

  // ── walked straight at: stopped at the touch ──
  {
    const man = { e: 0, n: 5 };
    const w = walker({ bodies: [man] });
    let closest = Infinity;
    const intent = createIntent();
    for (let i = 0; i < 6 * 60; i++) { intent.forward = 1; w.update(1 / 60, intent); closest = Math.min(closest, near(w, man)); }
    assert(closest >= TOUCH - 1e-6, `straight at him: never nearer than ${TOUCH} (${closest.toFixed(3)})`);
    assert(w.state.n < man.n, 'and still on the near side');
    assert(w.state.bumped, 'the walker says it was held off someone');
  }
  // ── walked at a slant: slides round and goes on ──
  {
    const man = { e: 0.15, n: 5 };
    const w = walker({ bodies: [man] });
    let closest = Infinity;
    const intent = createIntent();
    for (let i = 0; i < 10 * 60; i++) { intent.forward = 1; w.update(1 / 60, intent); closest = Math.min(closest, near(w, man)); }
    assert(closest >= TOUCH - 1e-6, `at a slant: never inside (${closest.toFixed(3)})`);
    assert(w.state.n > man.n + 1, `slid round him and walked on (n ${w.state.n.toFixed(2)})`);
  }
  // ── a sprint at 10 fps (over a metre a frame) never goes through anyone ──
  {
    WALK.sprintSpeed = 12;
    for (const off of [0, 0.1, 0.3]) {
      const man = { e: off, n: 3 };
      const w = walker({ bodies: [man] });
      const intent = createIntent();
      let closest = Infinity;
      for (let i = 0; i < 30; i++) { intent.forward = 1; intent.sprint = true; w.update(0.1, intent); closest = Math.min(closest, near(w, man)); }
      assert(closest >= TOUCH - 1e-6, `sprint ${off}: never inside (${closest.toFixed(3)})`);
      if (off === 0) assert(w.state.n < man.n, 'sprinting straight at him: still on the near side');
    }
    // and clearOfBodies itself, one long step straight through a middle
    const out = clearOfBodies(0, 4, 0, 0, [{ e: 0, n: 2, r: BODY_R_M }], WALK.radius);
    assert(out.hit && out.n < 2 - TOUCH + 1e-6, `a step through the middle is put back (${out.n.toFixed(3)})`);
    // a slide along the rim is left alone
    const rim = clearOfBodies(TOUCH + 0.001, 2.05, TOUCH + 0.001, 2, [{ e: 0, n: 2, r: BODY_R_M }], WALK.radius);
    assert(!rim.hit, 'a step along the rim is not stopped');
  }
  // ── someone walking into a standing visitor moves the visitor ──
  {
    const man = { e: 0, n: 3 };
    const w = walker({ bodies: [man] });
    const intent = createIntent();
    let closest = Infinity;
    for (let i = 0; i < 4 * 60; i++) {
      man.n = 3 - i * (1.4 / 60);
      intent.forward = 0; w.update(1 / 60, intent);
      if (man.n > w.state.n) closest = Math.min(closest, near(w, man));
    }
    assert(closest >= TOUCH - 0.03, `walked into: held at the touch (${closest.toFixed(3)})`);
    assert(w.state.n < man.n, 'and never through: he is still in front');
  }
  // ── a wall wins: pressed between a house and a man, never in the house ──
  {
    const house = { id: 'h', pts: [[-5, 1], [5, 1], [5, 6], [-5, 6]] };
    const man = { e: 0, n: 0 };
    const w = walker({ from: [0, -2], footprints: [house], bodies: [man] });
    const intent = createIntent();
    for (let i = 0; i < 3 * 60; i++) { man.n = Math.min(0.5, -1 + i / 60); intent.forward = 0; w.update(1 / 60, intent); }
    assert(w.state.n <= 1 - WALK.radius + 1e-6, `never in the house (n ${w.state.n.toFixed(3)})`);
  }
  // ── in the air nobody is solid; with no layer nobody is ──
  {
    const man = { e: 0, n: 3 };
    const w = walker({ bodies: [man] });
    const intent = createIntent();
    intent.flying = true;
    for (let i = 0; i < 4 * 60; i++) { intent.forward = 1; w.update(1 / 60, intent); }
    assert(w.state.n > 3, 'free-fly passes over and through');
    const w2 = walker();
    const i2 = createIntent();
    for (let i = 0; i < 4 * 60; i++) { i2.forward = 1; w2.update(1 / 60, i2); }
    assert(w2.state.n > 3, 'no bodies set: the walk is as before');
  }

  // ── a passer-by steps round the visitor; a stander holds their ground ──
  {
    const stand = (id, e, n, extra = {}) => {
      const a = { id, e, n, state: 'standing', inRange: true, path: null, standY: null, indoors: false,
        root: { visible: true }, place() {}, ...extra };
      return a;
    };
    const visitor = { e: 0, n: 0 };
    const walking = stand('hi_walk', 0, 3, { state: 'walking', heading: 180 });
    const still = stand('hi_still', 0.5, 0);
    const sp = createHumanSpacing({ humans: { actors: [walking, still] }, visitor: () => visitor, body: () => visitor });
    let closest = Infinity;
    for (let i = 0; i < 6 * 60; i++) {
      walking.n = 3 - i * (1.2 / 60);          // her own path goes straight through the visitor
      sp.update(1 / 60);
      const p = sp.where(walking);
      if (walking.n > -3) closest = Math.min(closest, Math.hypot(p.e - visitor.e, p.n - visitor.n));
    }
    assert(closest >= TOUCH, `a passer-by goes round, never nearer than the touch (${closest.toFixed(3)})`);
    assert(!still.spaceE && !still.spaceN, 'a stander is not shoved by the visitor');
    assert(VISITOR_M > TOUCH && VISITOR_RATE_M_S > 1, 'the passer-by keeps off before the walker would push');
    // Pressed on, the stander steps across the visitor's way (here the visitor faces east).
    const pressed = { ...visitor, pressing: true, bearing: 90 };
    const sp2 = createHumanSpacing({ humans: { actors: [still] }, visitor: () => pressed, body: () => pressed });
    for (let i = 0; i < 60; i++) sp2.update(1 / 60);
    const q = sp2.where(still);
    assert(Math.hypot(q.e - pressed.e, q.n - pressed.n) >= VISITOR_M - 1e-3, `pressed on, a stander steps aside (${Math.hypot(q.e, q.n).toFixed(3)})`);
    assert(Math.abs(q.n) > Math.abs(still.spaceE), 'across the visitor\'s way, not shoved along it');
    // Flying, nobody steps aside.
    const w2 = stand('hi_walk2', 0, 0.3, { state: 'walking' });
    createHumanSpacing({ humans: { actors: [w2] }, visitor: () => visitor, body: () => null }).update(1 / 60);
    assert(!w2.spaceE && !w2.spaceN, 'with no visitor on foot, nobody steps aside');
  }
} finally {
  WALK.speed = speedWas;
  WALK.sprintSpeed = sprintWas;
}
console.log('walker bodies: OK — the visitor slides round people, never into them; passers-by step round the visitor');
