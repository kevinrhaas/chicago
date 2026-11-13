#!/usr/bin/env node
/**
 * T-3554 — a 1904 house's stoop, area walls, railings and bays keep people out
 * (renderers/web/js/house-barriers.js, data from tools/prairie_barriers.py via derive_doors_scene.py).
 *
 * The owner, 2026-11-12: "people should not be able to walk through walls or barriers".
 *
 *   1. The reader: a rectangle's cells are near, a skirt's width off is clear, the house's turn
 *      is the walker's clockwise compass turn, and a leg through a rectangle is refused.
 *   2. The real file: every Prairie resident's outdoor place stands clear of every barrier, and
 *      the walk out to it from the door and the walk along the frontage keep a skirt's width
 *      off them (a narrow front gate: the body itself, never through a rail).
 *   3. human-days.js clearWayOf refuses a way through a barrier and keeps one beside it.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHouseBarriers, BARRIER_SKIRT_M } from '../renderers/web/js/house-barriers.js';
import { clearWayOf } from '../renderers/web/js/human-days.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let checks = 0;
const fails = [];
const ok = (cond, msg) => { checks++; if (!cond) fails.push(msg); };

// 1. A house at (100, 200) turned 90° (its plan's u runs east... turned clockwise: u -> south).
{
  // One rectangle: cells i 10..20, j 0..5 at 0.1 m, u0 = v0 = 0 -> u 0.95..1.95, v -0.05..0.45.
  const row = { structure: 'x', placement: { local_e: 100, local_n: 200, rotation_deg: 90 },
    barrier: { cell: 0.1, u0: 0, v0: 0, count: 1, rects: '10 20 0 5' } };
  const b = createHouseBarriers([row]);
  ok(b.count === 1 && b.rects === 1, 'one house, one rectangle read');
  // walker.js: e = e0 + u cos + v sin, n = n0 - u sin + v cos; at 90°: e = e0 + v, n = n0 - u.
  const at = (u, v) => ({ e: 100 + v, n: 200 - u });
  const c = at(1.5, 0.2);
  ok(b.near(c.e, c.n, 0.01), 'a point inside the rectangle is near it');
  const off = at(1.5, 0.45 + BARRIER_SKIRT_M + 0.02);
  ok(!b.near(off.e, off.n), 'a skirt and a hair off its side is clear');
  const edge = at(1.5, 0.45 + BARRIER_SKIRT_M - 0.05);
  ok(b.near(edge.e, edge.n), 'within a skirt of its side is near');
  const wrong = { e: 100 - 0.2, n: 200 + 1.5 };   // the counter-clockwise turn's place for it
  ok(!b.near(wrong.e, wrong.n, 0.01), 'the turn is clockwise, as walker.js turns a footprint');
  ok(!b.clearLeg(at(1.5, -2), at(1.5, 2)), 'a leg across the rectangle is refused');
  ok(b.clearLeg(at(3, -2), at(3, 2)), 'a leg past its end is clear');
  const clear = clearWayOf([], { barriers: b });
  ok(!clear(at(1.5, -2), at(1.5, 2)), 'clearWayOf refuses a way through a barrier');
  ok(clear(at(3, -2), at(3, 2)), 'clearWayOf keeps a way beside it');
  ok(createHouseBarriers([{ structure: 'bad', placement: row.placement, barrier: { cell: 0.1, u0: 0, v0: 0, rects: '1 2 3' } }]).count === 0,
    'a malformed barrier is refused, not half read');
}

// 2. The real file.
const doors = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/humans/doors_1904.json'), 'utf8'));
const inside = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/humans/inside_1904.json'), 'utf8'));
const barriers = createHouseBarriers([...doors.structures, ...(doors.barriers ?? [])]);
const rows = doors.structures.filter((r) => r.barrier).length;
ok(rows >= 60, `the houses people live in carry their barriers (${rows})`);
ok(barriers.count >= 140, `every built Prairie house's barriers are read (${barriers.count})`);
const steps = new Map(doors.structures.flatMap((r) => r.doors.map((d) => [d.id, { e: d.step.local_e, n: d.step.local_n }])));
let legs = 0, squeezed = 0, places = 0;
const seen = new Set();
for (const p of inside.people) {
  const step = steps.get(p.door);
  ok(!!step, `${p.person}: their door ${p.door} is in the doors file`);
  if (!step) continue;
  ok(!barriers.near(step.e, step.n, 0.25), `${p.door}: its answering place stands clear of every barrier`);
  for (const day of p.day ?? []) {
    for (const s of day.spans ?? []) {
      if (s.indoors || !s.at) continue;
      const at = { e: s.at.local_e, n: s.at.local_n };
      const key = `${p.door}|${at.e}|${at.n}|${s.to_point?.local_e}|${s.to_point?.local_n}`;
      if (seen.has(key)) continue;
      seen.add(key);
      places++;
      ok(!barriers.near(at.e, at.n, 0.5), `${p.person}: their outdoor place ${at.e},${at.n} stands clear of every barrier`);
      legs++;
      if (!barriers.clearLeg(step, at)) {
        squeezed++;
        ok(barriers.clearLeg(step, at, 0.15), `${p.person}: the walk out of ${p.door} to their place never passes through a barrier`);
      }
      if (s.to_point) {
        const end = { e: s.to_point.local_e, n: s.to_point.local_n };
        legs++;
        ok(!barriers.near(end.e, end.n, 0.5), `${p.person}: the end of their walk stands clear of every barrier`);
        ok(barriers.clearLeg(at, end), `${p.person}: their walk along the frontage keeps a skirt's width off every barrier`);
      }
    }
  }
}
ok(legs > 500, `the residents' walks are asked (${legs})`);
ok(squeezed <= 6, `few walks squeeze through a narrow gate (${squeezed})`);

if (fails.length) {
  for (const f of fails.slice(0, 40)) console.error(`FAIL ${f}`);
  console.error(`test_house_barriers: FAIL ${fails.length} of ${checks}`);
  process.exit(1);
}
console.log(`test_house_barriers: PASS (${checks} checks; ${barriers.count} houses, ${barriers.rects} barrier rectangles; ${places} outdoor places, ${legs} walks, ${squeezed} through a narrow gate)`);
