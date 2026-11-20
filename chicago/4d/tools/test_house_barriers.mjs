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
 *
 * T-3554, the owner 2026-11-13, of a maid standing half inside the bottom steps of a front stoop:
 * "she cannot stand where there are stairs like that, no one should be able to".
 *
 *   4. Every stair is a barrier from its bottom tread: each front stoop's lowest treads, each back
 *      yard's stoop, and 1835's street-front stoops and mounting blocks; and every door's
 *      answering place stands off them.
 *   5. planDay (human-days.js) stands nobody in a stair: a talk's ring about a place beside a
 *      stoop is moved off it (and without standClear it would not be, so the check bites), and
 *      every place 1904's drawn people are played at stands clear.
 *   6. human-spacing.js steps anyone standing in a stair out of it (at once when not drawn, a
 *      step at a time when drawn), never a walker nor one on a way's treads.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHouseBarriers, BARRIER_SKIRT_M, BARRIER_STAND_M } from '../renderers/web/js/house-barriers.js';
import { clearWayOf, planDay, dayOn } from '../renderers/web/js/human-days.js';
import { createHumanSpacing, BODY_R_M } from '../renderers/web/js/human-spacing.js';

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

// 4. Every stair is a barrier from its bottom tread.
const KNEE_M = 0.14;                       // prairie_barriers.py KNEE_M: a riser's height
const worldOf = (pl) => {
  const th = ((pl.rotation_deg ?? 0) * Math.PI) / 180;
  return (u, v) => ({ e: pl.local_e + u * Math.cos(th) + v * Math.sin(th), n: pl.local_n - u * Math.sin(th) + v * Math.cos(th) });
};
let treads = 0, ways = 0;
for (const r of doors.structures) {
  const W = worldOf(r.placement);
  for (const d of r.doors) {
    ok(!barriers.near(d.step.local_e, d.step.local_n, BARRIER_SKIRT_M - 0.01), `${d.id}: its answering place stands off every stair`);
    const way = d.plan?.way;
    if (!way) continue;
    ways++;
    // The bottom three treads: those a body beside the stoop would stand in.
    const low = [...new Set(way.filter(([, , y]) => y != null && y >= KNEE_M).map(([, , y]) => y))].sort((a, b) => a - b).slice(0, 3);
    for (const [u, v, y] of way) {
      if (y == null || !low.includes(y)) continue;
      treads++;
      const q = W(u, v);
      ok(barriers.near(q.e, q.n, 0.01), `${d.id}: its tread ${y} m up at ${u},${v} is a barrier`);
    }
  }
}
ok(ways >= 50 && treads >= 3 * ways, `the front stoops' bottom treads are asked (${ways} stoops, ${treads} points)`);
const backYards = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/back_yards/1904.json'), 'utf8'));
let backs = 0;
for (const lot of backYards.lots) {
  for (const d of lot.doors ?? []) {
    if (!d.stoop?.run_m) continue;
    backs++;
    const th = (d.facing_deg * Math.PI) / 180;
    for (const t of [0.15, 0.5, 0.9]) {
      const s = d.stoop.run_m * t;
      ok(barriers.near(d.e + Math.sin(th) * s, d.n + Math.cos(th) * s, 0.01), `${d.id}: its back stoop ${s.toFixed(2)} m out is a barrier`);
    }
  }
}
ok(backs >= 100, `the back yards' stoops are barriers (${backs})`);
const doors1835 = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/humans/doors_1835.json'), 'utf8'));
const town1835 = createHouseBarriers(doors1835.barriers ?? []);
const fits = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/frontage/town_street_edge.json'), 'utf8')).fittings ?? [];
let fitParts = 0;
for (const f of fits) {
  for (const part of f.parts ?? []) {
    if (!part.at_local_enu_m || !(part.top_m > KNEE_M)) continue;
    fitParts++;
    ok(town1835.near(part.at_local_enu_m[0], part.at_local_enu_m[1], 0.01), `1835 ${f.id} ${part.part}: a barrier`);
  }
}
ok(!(doors1835.barriers ?? []).some((r) => r.what === 'wagon_apron'), "1835's wagon aprons are planks laid on the walk, walked on, not barriers");
ok(fitParts >= 80 && town1835.count >= fitParts, `1835's street-front stoops and mounting blocks are barriers (${fitParts} parts, ${town1835.count} rows)`);

// 5. planDay stands nobody in a stair.
const standClear = (q) => barriers.clearOf(q.e, q.n, BARRIER_STAND_M);
const standsClear = (q) => !barriers.near(q.local_e ?? q.e, q.local_n ?? q.n, BARRIER_STAND_M - 0.01);
const placesOf = (s) => [s.at, s.to_point, ...(s.spots ?? []), ...(s.via ?? []),
  ...(s.round?.own ? [s.round.own.at, s.round.own.to_point, ...(s.round.own.spots ?? []), ...(s.round.own.via ?? [])] : [])].filter(Boolean);
{
  // Three people talking, each written at a place by the foot of a real stoop (the maid's place
  // in the owner's picture): their ring about the middle puts one on the treads.
  const r = doors.structures.find((x) => x.doors[0]?.plan?.way?.length > 8);
  const W = worldOf(r.placement), way = r.doors[0].plan.way;
  const tread = way.find(([, , y]) => y != null && y >= KNEE_M);
  const foot = W(tread[0] + 0.2, tread[1]), side = W(tread[0] - 0.4, tread[1] + 1.2);
  const span = (q, key) => ({ from: 9, to: 11, indoors: false, at: { local_e: q.e, local_n: q.n, heading_deg: 0 }, activity: 'talk', knot: 'stoop', doing: key });
  const people = [['a', foot], ['b', side], ['c', W(tread[0] + 0.6, tread[1] - 0.6)]].map(([key, q]) => ({ key, b: { day: [{ spans: [span(q, key)] }] } }));
  const placed = (opts) => {
    const out = planDay(people, '1904-07-01', opts);
    return people.flatMap((p) => dayOn(p.b, '1904-07-01', p.key).spans.map((s) => out.get(s) ?? s)).flatMap(placesOf);
  };
  ok(placed({}).some((q) => !standsClear(q)), 'without standClear a ring beside the stoop stands someone in its treads (the check bites)');
  const after = placed({ standClear });
  ok(after.length >= 3 && after.every(standsClear), `with standClear nobody of the ring stands in the stoop (${after.filter((q) => !standsClear(q)).length} in it)`);
}
{
  const dir = path.join(ROOT, 'data/humans/instances/1904');
  const idx = JSON.parse(fs.readFileSync(path.join(dir, 'index.json'), 'utf8'));
  const recs = idx.instances.map((id) => JSON.parse(fs.readFileSync(path.join(dir, `${id}.json`), 'utf8'))).filter((r) => Array.isArray(r.behaviour?.day));
  const people = recs.map((r) => ({ key: r.person_id ?? r.id, b: r.behaviour }));
  let n = 0;
  for (const date of ['1904-01-15', '1904-07-01', '1904-10-15']) {
    const out = planDay(people, date, { clear: clearWayOf([], { barriers }), standClear });
    for (const p of people) {
      for (const s of dayOn(p.b, date, p.key)?.spans ?? []) {
        if (s.indoors || !s.at) continue;
        for (const q of placesOf(out.get(s) ?? s)) { n++; ok(standsClear(q), `${p.key} ${date}: a place they are played at (${q.local_e},${q.local_n}) stands clear of every stair`); }
      }
    }
  }
  ok(n >= 20, `1904's drawn people's played places are asked (${n})`);
}

// 6. human-spacing steps anyone standing in a stair out of it.
{
  const r = doors.structures.find((x) => x.doors[0]?.plan?.way?.length > 8);
  const W = worldOf(r.placement), way = r.doors[0].plan.way;
  const tread = way.find(([, , y]) => y != null && y >= KNEE_M);
  const on = W(tread[0], tread[1]);
  const actor = (id, extra = {}) => {
    const a = { id, e: on.e, n: on.n, state: 'standing', indoors: false, inRange: true, path: null, standY: null,
      root: { visible: false }, place() {}, ...extra };
    return a;
  };
  const inStair = (a) => barriers.near(a.e + (a.spaceE ?? 0), a.n + (a.spaceN ?? 0), BODY_R_M - 0.01);
  const clearOf = (e, n) => barriers.clearOf(e, n, BODY_R_M);
  const stander = actor('stander');
  ok(inStair(stander), 'the stand-in stands on a tread to begin with');
  createHumanSpacing({ humans: { actors: [stander] }, clearOf }).update(0.016);
  ok(!inStair(stander), 'one standing in a stair, not drawn, is out of it at once');
  const seen = actor('seen', { root: { visible: true } });
  const spSeen = createHumanSpacing({ humans: { actors: [seen] }, clearOf });
  spSeen.update(0.016);
  const first = Math.hypot(seen.spaceE ?? 0, seen.spaceN ?? 0);
  ok(first > 0 && first <= 0.9 * 0.016 + 1e-9, `one drawn steps out a step at a time (${first.toFixed(4)} m in a frame)`);
  for (let i = 0; i < 300 && inStair(seen); i++) spSeen.update(0.016);
  ok(!inStair(seen), 'and is out of it within a few seconds');
  const w = actor('w', { state: 'walking' }), c = actor('c', { standY: 0.17 });
  createHumanSpacing({ humans: { actors: [w] }, clearOf }).update(0.016);
  createHumanSpacing({ humans: { actors: [c] }, clearOf }).update(0.016);
  ok(!(w.spaceE || w.spaceN), 'a walker is never stepped out (their way keeps off the stair itself)');
  ok(!(c.spaceE || c.spaceN), 'one on a way\'s treads is never moved');
}

if (fails.length) {
  for (const f of fails.slice(0, 40)) console.error(`FAIL ${f}`);
  console.error(`test_house_barriers: FAIL ${fails.length} of ${checks}`);
  process.exit(1);
}
console.log(`test_house_barriers: PASS (${checks} checks; ${barriers.count} houses, ${barriers.rects} barrier rectangles; ${places} outdoor places, ${legs} walks, ${squeezed} through a narrow gate)`);
