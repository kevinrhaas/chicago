// SPDX-License-Identifier: GPL-3.0-or-later
// T-3573: someone at home is found and followed (renderers/web/js/block-walk.js and
// human-days.js `homeNow` / `outing`). The owner, 2026-11-12: "if someone is in one of the
// houses and in town they should be able to be go to find or followed and if they are in their
// house they come outside and do a daily task outside so you can follow them, something
// meaningful like a walk around the block". It must: walk a block's four sides and its corners
// by its sidewalks, starting on the street before the door; walk the sides it can reach and
// back where a block has no street behind; walk about the place where there are no blocks;
// say a person indoors and present today is at home, and someone off their dates is not;
// bring them out of their own door on that walk, keep them out while followed and put them
// back in when the walk is over and they are not; and bring a household's undrawn resident
// out the same way, by their own door.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8');
const { blockLoop, walkDoing, footprintCentre, BLOCK_WALK } = await import(data(await js('block-walk.js')));
const { createHumanDays, OUTING } = await import(data(await js('human-days.js')));
const { createInteractions } = await import('../renderers/web/js/interact.js');
const doors = JSON.parse(await fs.readFile(new URL('data/humans/doors_1812.json', here), 'utf8'));
const three = { Vector3: class { constructor() { this.x = 0; this.y = 0; this.z = 0; } } };
const P = (q) => ({ e: q.local_e, n: q.local_n });

// ── the block ──
// A block 120 m east-west and 200 m north-south about the house at (0, 0), its sidewalks 2 m
// wide on all four sides; the house's door faces east (90°).
const band = (x, at) => Math.abs(x - at) <= 1;
const sidewalks = (e, n) => (((band(e, 60) || band(e, -60)) && Math.abs(n) <= 101)
  || ((band(n, 100) || band(n, -100)) && Math.abs(e) <= 61) ? 'sidewalk' : 'open');
const round = blockLoop({ centre: { e: 0, n: 0 }, frontDeg: 90, classAt: sidewalks, ways: ['sidewalk'] });
assert.equal(round.kind, 'block');
assert.equal(round.round, true, 'round the block and back to the door');
const pts = [round.at, ...round.via, round.to_point].map(P);
assert.equal(pts.length, 9, 'four sides and four corners, and the front again');
for (const q of pts) assert.equal(sidewalks(q.e, q.n), 'sidewalk', `every point is on a sidewalk (${q.e}, ${q.n})`);
assert(Math.abs(pts[0].e - 60) <= 1.5 && Math.abs(pts[0].n) < 0.01, 'it starts on the street before the door');
assert(Math.abs(round.at.heading_deg - 180) < 1, 'turned along the front, to the right first');
const corners = [pts[1], pts[3], pts[5], pts[7]];
for (const [q, e, n] of corners.map((q, i) => [q, [60, -60, -60, 60][i], [-100, -100, 100, 100][i]])) {
  assert(Math.hypot(q.e - e, q.n - n) < 3, `a corner at (${e}, ${n}): (${q.e.toFixed(1)}, ${q.n.toFixed(1)})`);
}
assert(round.length_m > 600 && round.length_m < 700, `the perimeter (${round.length_m} m)`);
// A footprint's middle; the walk's name by the hour.
assert.deepEqual(footprintCentre([{ pts: [[0, 0], [10, 0], [10, 20], [0, 20]] }]), { e: 5, n: 10 });
assert.equal(walkDoing('block', 9), 'a morning walk round the block');
assert.equal(walkDoing('block', 14), 'an errand round the block');
assert.equal(walkDoing('block', 19), 'an evening walk round the block');
assert.equal(walkDoing('ring', 14), 'a walk about the place');
assert.equal(walkDoing('block', 2), 'a late walk round the block');

// No street behind (beyond the reach): the front and its two ends, there and back.
const noBack = (e, n) => (e < -30 ? 'open' : sidewalks(e, n));
const front = blockLoop({ centre: { e: 0, n: 0 }, frontDeg: 90, classAt: noBack, ways: ['sidewalk'] });
assert.equal(front.kind, 'block');
assert.equal(front.round, false);
const fp = [front.at, ...front.via, front.to_point].map(P);
assert(Math.abs(fp[0].e - 60) <= 1.5 && Math.abs(fp[0].n) < 0.01, 'it starts before the door');
assert(fp.some((q) => q.n < -95) && fp.some((q) => q.n > 95), 'it goes round both ends of the front');
// An alley is not a side: a track behind the house is passed for the street beyond.
const alley = (e, n) => (band(e, -20) ? 'track' : sidewalks(e, n));
const pastAlley = blockLoop({ centre: { e: 0, n: 0 }, frontDeg: 90, classAt: alley, ways: ['sidewalk'] });
assert([pastAlley.at, ...pastAlley.via].map(P).some((q) => q.e < -58), 'round by the street behind, not the alley');

// No block (1812): a ring about the place, on ground that is clear, straight between points.
const ring = blockLoop({ centre: { e: 0, n: 0 }, frontDeg: 0, classAt: () => 'open', ways: null });
assert.equal(ring.kind, 'ring');
assert([ring.at, ...ring.via].length >= 3);
assert.equal(blockLoop({ centre: { e: 0, n: 0 }, blockedAt: () => true }), null, 'nowhere to stand: no walk');
const halfWater = blockLoop({ centre: { e: 0, n: 0 }, blockedAt: (e) => e > 5 });
for (const q of [halfWater.at, ...halfWater.via, halfWater.to_point].map(P)) assert(q.e <= 5, 'never into the river');

// ── at home, and out ──
function actorOf(rec, name) {
  const a = {
    id: rec.id, personId: rec.person_id, instance: rec, person: { name }, identity: { kind: 'person', person: { name } },
    e: rec.placement.local_e, n: rec.placement.local_n, heading: rec.placement.heading_deg, state: 'standing',
    indoors: false, inRange: true, path: null, walks: [],
    place() {}, setState(s) { a.state = s; }, setIndoors(on) { a.indoors = !!on; }, turnTo(h) { a.heading = h; },
    root: { getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    life: { attend() {}, nod() {} }, actions: { setTalk() {}, greet() {}, hold() {} },
    walkPath(pts, { endHeading = null, onArrive = null } = {}) {
      a.walks.push(pts.map((p) => [p.e, p.n]));
      a.pending = { end: pts.at(-1), endHeading, onArrive, t: 1 };
      a.state = 'walking';
      return true;
    },
    stopPath() { a.pending = null; },
  };
  return a;
}
const rec = (id, behaviour, at = [1150, 221, 0]) => ({ id: `hi_${id}`, person_id: id, scene: '1812', appearance: { asset_id: 'man_1812' },
  placement: { local_e: at[0], local_n: at[1], heading_deg: at[2] }, behaviour: { state: 'standing', ...behaviour } });
const OUT = (from, to, e, n, h, extra = {}) => ({ from, to, indoors: false, at: { local_e: e, local_n: n, heading_deg: h }, ...extra });
const IN = (from, to, where) => ({ from, to, indoors: true, where });
const kinzie = actorOf(rec('kinzie_john_elder', {
  day: [{ spans: [IN(0, 7, 'kinzie_house_1812'), OUT(7, 12, 1150, 332, 180, { activity: 'work' }), IN(12, 24, 'kinzie_house_1812')] }] }), 'John Kinzie');
const lalime = actorOf(rec('lalime_jean', { presence: { to: '1812-06-17' },
  day: [{ spans: [IN(0, 24, 'lalime_house_1812')] }] }), 'Jean Lalime');
const actors = [kinzie, lalime];
const spawned = [];
const humans = { actors, shown: true };
// A household's resident who is not drawn until asked for (inside_<year>.json).
const kinzieDoor = doors.structures.find((s) => s.structure === 'kinzie_house_1812').doors[0];
const inside = { people: [{ person: 'kinzie_cook_x', name: 'A cook', home: 'kinzie_house_1812', door: kinzieDoor.id, asset_id: 'woman_1812',
  day: [{ spans: [IN(0, 24, 'kinzie_house_1812')] }] }] };
const spawn = (entry, door) => {
  const a = actorOf({ id: `hi_inside_${entry.person}`, person_id: entry.person, scene: '1812', appearance: { asset_id: entry.asset_id },
    placement: { local_e: door.step.local_e, local_n: door.step.local_n, heading_deg: door.outward_deg }, behaviour: { state: 'standing' } }, entry.name);
  actors.push(a); spawned.push(a); return a;
};
const despawn = (a) => { actors.splice(actors.indexOf(a), 1); };
let hour = 14, followed = null;
const visitor = { e: 5000, n: 5000 };   // far: people are put where they go
const life = createHumanDays({ humans, three, hour: () => hour, date: () => '1812-08-14', doors, interactions: createInteractions(),
  visitor: () => visitor, inside, spawn, despawn, followed: (a) => a.personId === followed });
const tick = (dt, n) => {
  for (let i = 0; i < n; i++) {
    for (const a of [...actors]) {
      if (!a.pending) continue;
      a.pending.t -= dt;
      if (a.pending.t <= 0) { const p = a.pending; a.pending = null; a.e = p.end.e; a.n = p.end.n; a.state = 'standing'; p.onArrive?.(a); }
    }
    life.update(dt);
  }
};
tick(0.25, 20);
assert.equal(kinzie.indoors, true, 'at two in the afternoon John Kinzie is in his house');
assert.deepEqual(life.homeNow('kinzie_john_elder'), { structure: 'kinzie_house_1812', name: 'John Kinzie' }, 'at home now');
assert.equal(life.homeNow('lalime_jean'), null, 'Lalime is gone on 14 August: not at home in town');
assert.equal(life.outing('lalime_jean').why, 'not here on this date');

// Out of his own door on a walk round a loop, and kept out while followed.
const loopCalls = [];
const loop = (structure, door) => {
  loopCalls.push([structure, door.id]);
  const s = P(door.step);
  const at = { local_e: s.e + 10, local_n: s.n, heading_deg: 0 };
  return { at, via: [{ local_e: s.e + 10, local_n: s.n + 30 }, { local_e: s.e - 20, local_n: s.n + 30 }], to_point: at, doing: 'a walk about the place' };
};
const plan = life.outing('kinzie_john_elder', { loop });
assert.equal(plan.ok, true, plan.why);
assert.deepEqual(loopCalls, [['kinzie_house_1812', kinzieDoor.id]], 'the walk is from his own door');
const kinzieDoors = doors.structures.find((s) => s.structure === 'kinzie_house_1812').doors;
const start = P(plan.door ? { local_e: plan.door.step.e, local_n: plan.door.step.n } : {});
const nearestDoor = kinzieDoors.map((d) => [d.id, Math.hypot(P(d.step).e - (P(kinzieDoor.step).e + 10), P(d.step).n - P(kinzieDoor.step).n)]).sort((a, b) => a[1] - b[1])[0][0];
assert.equal(plan.door.id, nearestDoor, 'out by the door of his house nearest where the walk starts');
assert(Number.isFinite(start.e));
assert.equal(plan.doing, 'a walk about the place');
assert.equal(kinzie.indoors, true, 'nothing moves until the visitor is there');
assert.equal(plan.start().ok, true);
tick(0.25, 8);
assert.equal(kinzie.indoors, false, 'out of the house');
assert.equal(life.homeNow('kinzie_john_elder'), null, 'out, not at home');
const seen = new Set();
for (let i = 0; i < 400; i++) { tick(0.25, 1); seen.add(`${kinzie.e.toFixed(0)},${kinzie.n.toFixed(0)}`); }
assert(seen.size >= 3, `he walks the loop (${seen.size} places)`);
assert.equal(life.snapshot().find((s) => s.person === 'kinzie_john_elder').span.activity, 'walk');
followed = 'kinzie_john_elder';
tick(0.25, Math.ceil(OUTING.for_s / 0.25));
assert.equal(kinzie.indoors, false, 'followed, he walks on past the walk\'s time');
followed = null;
tick(0.25, Math.ceil(OUTING.followed_s / 0.25) + 20);
assert.equal(kinzie.indoors, true, 'no longer followed, the walk ends and he goes back in');
assert(life.homeNow('kinzie_john_elder'), 'at home again');

// A household's undrawn resident comes out of the same house by her own door.
assert.deepEqual(life.homeNow('kinzie_cook_x'), { structure: 'kinzie_house_1812', name: 'A cook' });
const cook = life.outing('kinzie_cook_x', { loop });
assert.equal(cook.ok, true, cook.why);
assert.equal(cook.door.id, kinzieDoor.id, 'her own door');
assert.equal(spawned.length, 0, 'nobody built until she comes out');
assert.equal(cook.start().ok, true);
assert.equal(spawned.length, 1, 'her figure is built at the door');
tick(0.25, 8);
assert.equal(spawned[0].indoors, false, 'and she is out');
assert.equal(life.homeNow('kinzie_cook_x'), null);
tick(0.25, Math.ceil(OUTING.for_s / 0.25) + 40);
assert(!actors.includes(spawned[0]), 'back in, her figure is taken away');
assert(life.homeNow('kinzie_cook_x'), 'and she is at home again');

console.log('STEP OUT PASS: round the block by its sidewalks and corners, the front and both ends where there is no street behind, past an alley; a walk about the place with no blocks; at home today vs away; out by their own door, on while followed, back in after; an undrawn resident built at her door and taken away again');
