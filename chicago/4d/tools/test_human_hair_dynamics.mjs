// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { HairSpring, HairDynamics, HairBudget, HAIR_QUALITY } from '../renderers/web/js/human-hair-dynamics.js';

// The unit step of a critically damped system has this independent closed form.
const s = new HairSpring({ frequency: 1, limit: 2 });
s.advance(.2, 1, 0);
const w = 2 * Math.PI, expected = 1 - (1 + w * .2) * Math.exp(-w * .2);
assert(Math.abs(s.x - expected) < 1e-12); assert.equal(s.z, 0);
const many = new HairSpring({ frequency: 1, limit: 2 });
for (let i = 0; i < 20; i++) many.advance(.01, 1, 0);
assert(Math.abs(many.x - s.x) < 1e-12, 'constant-force motion is independent of frame subdivision');
const capped = new HairSpring({ limit: .008 });
for (let i = 0; i < 300; i++) {
  capped.advance(i % 3 === 0 ? .2 : 1 / 120, Math.sin(i) * 100, Math.cos(i) * 100);
  assert(Math.hypot(capped.x, capped.z) <= .008 + 1e-12);
  assert([capped.x, capped.z, capped.vx, capped.vz].every(Number.isFinite));
}
capped.advance(Infinity, NaN, Infinity); assert(Number.isFinite(capped.x));
capped.reset(); assert.deepEqual([capped.x,capped.z,capped.vx,capped.vz],[0,0,0,0]);

const make = (id, distance, triangles = 9000, tied = false) => {
  const layer = { visible: true }, uniform = { value: { x: 0, y: 0, z: 0, w: 1 } };
  const runtime = new HairDynamics({ uniform, triangles, tied, phase: distance, setVisible: on => layer.visible = on });
  return { id, distance, root: { visible: true, position: { x: 0, z: 0 } }, heading: 0, inRange: true, hair: { runtime }, layer, uniform };
};
const actors = Array.from({ length: 60 }, (_, i) => make('person-'+i, 1 + i / 10));
const budget = new HairBudget();
let stats = budget.update(actors, .016, 'balanced');
assert.equal(stats.heads, 8); assert.equal(stats.triangles, 72000);
assert.equal(stats.addedTriangles,0,'all existing near cards are budgeted even without new geometry');
actors[0].hair.runtime.addedTriangles=4000;
stats=budget.update(actors,.016,'balanced');assert.equal(stats.addedTriangles,4000,'added geometry is separately reported inside the total cap');
assert(actors.every(a => a.root.visible), 'a hair budget never hides people');
assert(actors.slice(0,8).every(a=>a.layer.visible)); assert(actors.slice(8).every(a=>!a.layer.visible));
for (let i = 0; i < 40; i++) stats = budget.update(actors, .016, 'full');
assert(stats.heads <= HAIR_QUALITY.full.heads && stats.triangles <= HAIR_QUALITY.full.triangles);
assert(actors[0].uniform.value.x !== 0, 'admitted loose hair has controlled secondary motion');
const previous = actors[0].uniform.value.x;
const parked = make('parked-lod', 1);
parked.hair.runtime.takePoseFrom(actors[0].hair.runtime);
assert.equal(parked.uniform.value.x, previous, 'a cached LOD resumes the same physical tip position');
parked.hair.runtime.advance(0, parked, HAIR_QUALITY.full);
assert.equal(parked.uniform.value.x, previous, 'pausing the scene preserves its hair pose');
assert.equal(actors[1].uniform.value.x !== undefined, true);
actors[0].root.position.x = 10000; budget.update(actors, .016, 'full');
assert(Math.hypot(actors[0].uniform.value.x,actors[0].uniform.value.y) <= .008, 'teleport cannot explode the spring');
assert(Number.isFinite(previous));
stats = budget.update(actors, .016, 'light');
assert.equal(stats.heads, 0); assert.equal(stats.triangles, 0);
assert(actors.every(a=>a.root.visible&&!a.layer.visible&&a.uniform.value.x===0&&a.uniform.value.y===0));
const tied = make('tied', 1, 9000, true), loose = make('loose', 1, 9000, false);
for (let i=0;i<80;i++) { tied.heading += 2; loose.heading += 2; budget.update([tied,loose],.016,'full'); }
assert(Math.hypot(tied.uniform.value.x,tied.uniform.value.y) <= .002+1e-12, 'period updos remain restrained');
assert(Math.hypot(loose.uniform.value.x,loose.uniform.value.y) <= .008+1e-12);
const other = loose.uniform.value.x;
tied.hair.runtime.dispose(); tied.hair.runtime.dispose(); budget.update([tied,loose],.016,'full');
assert.equal(tied.hair.runtime.uniform,null); assert(Number.isFinite(loose.uniform.value.x));
assert(Number.isFinite(other), 'disposing one head leaves another head’s independent uniform alive');
budget.dispose(); assert.equal(budget.candidates.length,0);
const lifecycle = new HairBudget(), owned = make('owned', 1);
lifecycle.register(owned); lifecycle.update(null,.016,'full');
assert.equal(lifecycle.candidates.length,1);
lifecycle.unregister(owned); assert.equal(lifecycle.actors.size,0); assert.equal(lifecycle.candidates.length,0);
assert.equal(lifecycle.stats.heads,0,'the last disposed head leaves no stale per-frame ownership');
console.log('hair dynamics: analytical spring, frame subdivision, bounded motion, teleports, independent heads, tier/crowd limits, visible people and disposal PASS');
