// SPDX-License-Identifier: GPL-3.0-or-later
/** T-3690: the 1871 city's people are put on its walks (renderers/web/js/town-1871.js), and the
 * people file, its drivers and their wagons agree. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { placeTown1871, walkIndex } from '../renderers/web/js/town-1871.js';
import { expandInside, templateSpanAt } from '../renderers/web/js/human-days.js';

// A street running north, its walk on the east side, a building behind the walk.
const walk = { id: 'w', kind: 'walk', a: [10, 0], b: [10, 200], width_m: 3, y: 3.32 };
const road = { id: 'r', kind: 'road', a: [0, 0], b: [0, 200], width_m: 16, y: 3.23 };
const house = { e: 16, n: 100, w: 6, d: 10 };
const city = {
  doc: { walk_surfaces: [walk, road] },
  containsBuilding: (e, n, pad = 0) => Math.abs(e - house.e) < house.w / 2 + pad && Math.abs(n - house.n) < house.d / 2 + pad,
  floorHeight: (e, n) => (Math.abs(e - 10) <= 1.5 ? 3.32 : Math.abs(e) <= 8 ? 3.23 : null),
};
const inside = {
  homes: { hh_a: 'the A house', hh_far: 'the far house' },
  people: [
    { person: 'p1', home: 'hh_a', near: [14, 98], asset_id: 'x', routine: 'r' },
    { person: 'p2', home: 'hh_a', near: [14, 98], asset_id: 'x', routine: 'r' },
    { person: 'p3', home: 'hh_far', near: [5000, 5000], asset_id: 'x', routine: 'r' },
  ],
  care: [],
};
const { doors, census } = placeTown1871(inside, city);
assert.deepEqual(census, { households: 2, placed: 1, dropped: 1, faces: 1 }, 'one household placed at a building face, one with no walk dropped');
assert.equal(inside.people.length, 2, 'the household with no walk is not drawn');
const [s] = doors.structures;
assert.equal(s.structure, 'hh_a');
assert.equal(s.name, 'the A house');
const [door] = s.doors;
assert(door.leaf.local_e > 11 && door.leaf.local_e < 13.1, `the door is on the building's face behind the walk (${door.leaf.local_e})`);
assert(door.step.local_e < door.leaf.local_e, 'its step is toward the street');
assert(Math.abs(door.outward_deg - 270) < 1, `it opens toward the street (${door.outward_deg})`);
const onWalk = ([e, n]) => Math.abs(e - 10) <= 1.5 + 1e-9 && n >= 0 && n <= 200;
for (const p of inside.people) {
  assert.equal(p.door, 'hh_a:front');
  for (const [k, q] of Object.entries(p.points)) assert(onWalk(q), `${p.person} ${k} ${q} is on the walk`);
}
assert.notDeepEqual(inside.people[0].points.front, inside.people[1].points.front, 'two of a household do not stand on one spot');
assert.equal(walkIndex([road]).rows.length, 0, 'only walks are indexed');

// The generated file: every person has a template and a home; drivers are out all day; the
// wagons' drivers are those people.
const doc = JSON.parse(fs.readFileSync(new URL('../data/humans/inside_1871.json', import.meta.url)));
assert.equal(doc.format, 'chicago4d_inside_only_v2');
assert(doc.people.length > 3000 && doc.people.length < 4000, `${doc.people.length} people, bounded by the census at the 1835 scale`);
const homes = new Set(Object.keys(doc.homes));
for (const p of doc.people) {
  assert(doc.routines[p.routine], `${p.person} has a routine`);
  assert(homes.has(p.home) && Array.isArray(p.near), `${p.person} has a home and a place`);
}
expandInside(doc);
const at = (p, h) => templateSpanAt(doc.routines[p.routine], { ...p, points: { front: [0, 0, 0], front_end: [1, 0], stroll: [0, 0, 0], stroll_end: [1, 0] } }, '1871-10-08', h);
const out16 = doc.people.filter((p) => { const s = at(p, 16); return s && !s.indoors; }).length;
assert(out16 / doc.people.length > 0.5, `most are out of doors at four on the Sunday (${out16})`);
const drivers = doc.people.filter((p) => p.drives);
const loops = JSON.parse(fs.readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url))).rows.filter((r) => r.scene === '1871');
assert.equal(drivers.length, loops.length, 'one carded driver a wagon');
for (const r of loops) {
  const d = drivers.find((p) => p.drives === r.id);
  assert(d && r.person_id === d.person && r.driver_asset === d.asset_id, `${r.id} is driven by its carded man`);
  assert(at(d, 16).away && at(d, 12).away, `${d.person} is out with his team, not at home or in the crowd`);
  assert.deepEqual(r.stops, [], `${r.id} stands at no door`);
}
console.log(`town people 1871: ${doc.people.length} people placed on the walks at run time; ${out16} out at 16:00; ${loops.length} wagons each led by its carded driver PASS`);

// The teams read the roadway alone, never a walk laid across it.
{
  const { roadHeightOf } = await import('../renderers/web/js/town-1871.js');
  const at = roadHeightOf([{ kind: 'road', a: [0, -100], b: [0, 100], width_m: 20, y: 3.23 },
    { kind: 'walk', a: [-20, 11], b: [20, 11], width_m: 3, y: 3.32 }]);
  assert.equal(at(0, 11), 3.23, 'a crossing walk is not the roadway');
  assert.equal(at(30, 0), null, 'off the roadway, no reading');
  const ctx = JSON.parse(fs.readFileSync(new URL('../data/context/1871.json', import.meta.url)));
  const road = roadHeightOf(ctx.walk_surfaces);
  const { routeFor } = await import('../renderers/web/js/transport-loop.js');
  for (const r of loops) {
    const route = routeFor(r.route), ys = new Set();
    for (let s = 0; s < route.length; s += 2) { const p = route.at(s); ys.add(road(p.e, p.n)); }
    assert(!ys.has(null) && ys.size === 1, `${r.id} runs on one level roadway the whole way round (${[...ys]})`);
  }
}
