// SPDX-License-Identifier: GPL-3.0-or-later
/** Kevin, 2026-11-13: where the 1904 carriages' roads cross, one waits for the other to
 * cross, then proceeds (renderers/web/js/transport-crossings.js). This plays the actual
 * 1904 rows of data/transport/driven/loops.json for two hours of scene time, and a
 * three-way crossing built to deadlock a naive rule, and proves: no two teams' footprints
 * ever overlap, nobody waits long, everybody keeps going round, and the waits happen. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { routeFor, circleRoute, createTransportLoop } from '../renderers/web/js/transport-loop.js';
import { createCrossings, conflictZones, footprintAt, overlaps } from '../renderers/web/js/transport-crossings.js';
import { buildRows, frontWheelsClear } from './lay_driven_carriages_1904.mjs';

const loops = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url)));

function play(rows, seconds, { dt = 1 / 10, routes = rows.map(r => routeFor(r.route)) } = {}) {
  const circuits = rows.map((row, i) => ({ id: row.id, row, route: routes[i] }));
  const crossings = createCrossings(circuits);
  const actors = circuits.map(c => createTransportLoop({ ...c.row, route: c.route, heightAt: () => 0,
    assembly: { pose() {}, stop() {} }, gate: crossings.gateFor(c.id) }));
  const waits = [], open = new Map();
  let worstOverlap = null;
  for (let f = 0; f * dt < seconds; f++) {
    for (const a of actors) a.update(dt);
    const prints = actors.map((a, i) => footprintAt(circuits[i].route, circuits[i].row, a.snapshot().distance_m, 0));
    for (let i = 0; i < actors.length; i++) for (let j = i + 1; j < actors.length; j++) {
      if (overlaps(prints[i], prints[j])) worstOverlap ??= { t: f * dt, a: actors[i].id, b: actors[j].id };
    }
    for (const a of actors) {
      const w = a.givingWayTo;
      if (w && !open.has(a.id)) open.set(a.id, { t: f * dt, to: w });
      if (!w && open.has(a.id)) { const o = open.get(a.id); waits.push({ id: a.id, to: o.to, at_s: o.t, for_s: f * dt - o.t }); open.delete(a.id); }
    }
  }
  return { crossings, actors, waits, open, worstOverlap };
}

// The three 1904 carriages: Hans's and the two the layer writes, as loops.json holds them.
const rows1904 = loops.rows.filter(r => r.scene === '1904');
assert.deepEqual(rows1904.map(r => r.id), ['prairie_driven_brougham_loop_1904',
  'prairie_driven_brougham_north_loop_1904', 'prairie_driven_brougham_south_loop_1904']);
const { rows: written } = buildRows();
assert.deepEqual(rows1904.slice(1), written, 'the two new rows are what tools/lay_driven_carriages_1904.mjs writes');
// Hans's and Henry Windish's rounds are counter-clockwise (every corner a left turn, positive
// curvature); Joseph Daniels's is clockwise (Kevin, 2026-11-14: every corner a right turn).
// The team keeps right either way.
const turns = { prairie_driven_brougham_loop_1904: 1, prairie_driven_brougham_north_loop_1904: 1, prairie_driven_brougham_south_loop_1904: -1 };
for (const row of rows1904) {
  const route = routeFor(row.route);
  let turned = 0;
  for (let s = 0; s < route.length; s += 1) {
    const k = route.at(s).curvature;
    assert(k * turns[row.id] >= -1e-12, `${row.id} turns the wrong way at ${s} m`);
    if (Math.abs(k) > 1e-9) turned++;
  }
  assert(turned > 20, `${row.id} turns its corners`);
  // The brougham's lock (15°) covers the sharpest corner of each round.
  assert.equal(row.steering_limit_deg, 15);
  assert(Math.atan(row.wheelbase_m * route.maxCurvature) <= 15 * Math.PI / 180);
}
assert(routeFor(rows1904[2].route).maxCurvature > Math.tan(8 * Math.PI / 180) / rows1904[2].wheelbase_m, 'the clockwise round needs more than the old 8° of lock');
// The lock is the coach's own: its front wheels clear the body at 16°, and the check bites at 25°.
const brougham = new URL(`../renderers/web/${rows1904[0].vehicle_file}`, import.meta.url).pathname;
assert(frontWheelsClear(brougham, 16) && !frontWheelsClear(brougham, 25), 'front-wheel lock read off the brougham');
const zones = conflictZones(rows1904.map(row => ({ id: row.id, row, route: routeFor(row.route) })));
// Hans crosses Henry twice a lap (at Indiana and at Prairie). Joseph's clockwise round, east
// of Prairie, shares no lane and no turn with either.
const pairs = zones.map(z => `${z.a}|${z.b}`).sort();
assert.deepEqual(pairs, [
  'prairie_driven_brougham_loop_1904|prairie_driven_brougham_north_loop_1904',
  'prairie_driven_brougham_loop_1904|prairie_driven_brougham_north_loop_1904',
]);
for (const z of zones) for (const [a, b] of Object.values(z.at)) assert(b - a > 5 && b - a < 30, `zone ${z.id} spans ${b - a} m`);
// Opposing lanes on 18th pass clear: no zone runs along a shared street.
console.log(`1904 conflict zones PASS: ${zones.length}, two crossings a lap between Hans and Henry; two rounds counter-clockwise, one clockwise`);

const TWO_HOURS = 7200;
const run = play(rows1904, TWO_HOURS);
assert.equal(run.worstOverlap, null, `teams overlap: ${JSON.stringify(run.worstOverlap)}`);
assert(run.waits.length >= 3, `only ${run.waits.length} waits in two hours`);
assert(run.waits.every(w => w.for_s <= 30), `a wait too long: ${JSON.stringify(run.waits.find(w => w.for_s > 30))}`);
const first = run.waits[0];
assert(first.at_s < 600 && first.for_s >= 2, `the first give-way comes within ten minutes and is seen: ${JSON.stringify(first)}`);
for (const [i, actor] of run.actors.entries()) {
  const row = rows1904[i], dwell = (row.stops ?? []).reduce((sum, s) => sum + s.dwell_s, 0);
  const lap = routeFor(row.route).length / row.speed_m_s + dwell;
  const free = TWO_HOURS / lap * routeFor(row.route).length;
  assert(actor.snapshot().total_distance_m > free * .95, `${row.id} fell behind: ${actor.snapshot().total_distance_m} of ${free}`);
}
console.log(`1904 two hours PASS: no overlap, ${run.waits.length} give-ways (first at ${first.at_s.toFixed(0)} s, ${first.for_s.toFixed(1)} s), longest ${Math.max(...run.waits.map(w => w.for_s)).toFixed(1)} s, every team keeps its pace`);

// Three teams whose circles all pass one point: a rule that let a waiting team hold its
// first zone while asking for its next would lock all three. Nobody overlaps; all go round.
{
  const base = rows1904[0];
  const at = [[0, 0], [1, 0], [.5, .866]].map(([x, y]) => [x * 40, y * 40]);
  const centre = [20, 11.547];
  const routes = at.map(([e, n]) => {
    const phase = Math.atan2(centre[1] - n, centre[0] - e);
    return circleRoute({ center_enu_m: [e, n], radius_m: Math.hypot(centre[0] - e, centre[1] - n), phase_rad: phase });
  });
  const rows = routes.map((_, i) => ({ ...base, id: `ring_${i}`, route: null, stops: [], initial_distance_m: 20 + 3 * i, speed_m_s: 1.2 + .1 * i }));
  const ring = play(rows, 1800, { routes });
  assert.equal(ring.worstOverlap, null, `ring overlap: ${JSON.stringify(ring.worstOverlap)}`);
  assert(ring.waits.length > 5);
  for (const actor of ring.actors) assert(actor.snapshot().total_distance_m > 1800 * 1.2 * .6, `${actor.id} stalled at ${actor.snapshot().total_distance_m}`);
  console.log(`three-way crossing PASS: ${ring.waits.length} give-ways in 30 min, no overlap, no lock`);
}

// A team taken away (disposed) lets go of what it holds; the other is never left waiting.
{
  const rows = rows1904.slice(0, 2);
  const circuits = rows.map(row => ({ id: row.id, row, route: routeFor(row.route) }));
  const crossings = createCrossings(circuits);
  const g = crossings.gateFor(rows[1].id);
  const cluster = crossings.state.get(rows[1].id).clusters[0];
  assert.equal(g.allow(cluster.start - 1, .1), .1);
  assert.equal(crossings.snapshot()[rows[1].id].holding.length > 0, true);
  const other = crossings.gateFor(rows[0].id);
  const zone = crossings.zones.find(z => cluster.ids.includes(z.id));
  const before = zone.at[rows[0].id][0] - .08;
  assert(other.allow(before, .1) < .1, 'Hans waits while the north carriage holds the crossing');
  assert.equal(other.waitingFor, rows[1].id);
  g.drop();
  assert.equal(other.allow(before, .1), .1, 'and goes once it has gone');
  console.log('claims PASS: one holds, the other waits for it by name, a dropped team lets go');
}
