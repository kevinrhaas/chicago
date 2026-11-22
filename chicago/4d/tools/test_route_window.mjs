#!/usr/bin/env node
/**
 * T-3691 — a world too big for one route grid keeps a window round the visitor, and the
 * 1871 context city's buildings, streets and plank walks are planned round and along.
 *
 * Kevin, 2026-11-21, on his phone: the Great Fire, The Last Sunday and Who Started the Fire
 * would not start, or died part way. 1871's heightfield is 10.8 x 11.45 km, so the first
 * stand check of a jaunt built a 1 m grid of 124 million cells (2.9 GB, 12 s) and the tab
 * was killed. And mid-walk "we ran into a wall": the planner did not know the context city's
 * buildings, so its routes crossed the blocks straight through them.
 *
 * On flat ground, a 1000 m world at a 2 m cell (250,000 cells):
 *   - under `maxCells` the grid is the whole world, as before;
 *   - over it, a window of at most `windowCells` round the visitor, cell-aligned with the
 *     whole grid, so a plan inside it is the whole grid's plan to the last digit;
 *   - off the window a plan is null (travel flies), a point is not blocked (as before the
 *     grid is built), and off the world it is blocked, as before;
 *   - the window moves when the visitor nears its edge, not while they fly, and to a
 *     building a stand is asked for;
 *   - an `extra` layer's buildings block, and a walk keeps to its plank walks round them.
 *
 *   node tools/test_route_window.mjs
 */
import assert from 'node:assert/strict';
import { createRouter } from '../renderers/web/js/route.js';

let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };
const box = (id, e0, n0, e1, n1) => ({ id, pts: [[e0, n0], [e1, n0], [e1, n1], [e0, n1]] });
const terrain = {
  heightfield: { loaded: true, originE: -500, originN: -500, widthM: 1000, depthM: 1000 },
  walkHeight: () => 0, surfaceHeight: () => 0, isWater: () => false,
};
const footprints = [box('house', 20, 20, 40, 40), box('far_house', 380, 380, 400, 400)];
const visitor = { e: 0, n: 0, flying: false };
const focus = () => (visitor.flying ? null : visitor);
const make = (o = {}) => createRouter({ terrain, footprints, cell: 2, radius: 0.34, inflate: 0.1, focus, ...o });

// Under the ceiling: the whole world, as before.
{
  const R = make({ maxCells: 300000 });
  R.warm();
  ok(!R.stats.windowed, 'a world under maxCells is not windowed');
  ok(R.bounds.cols === 500 && R.bounds.rows === 500, `its grid is the whole world (${R.bounds.cols} x ${R.bounds.rows})`);
}

const whole = make({ maxCells: 300000 });
const R = make({ maxCells: 100000, windowCells: 40000 });
R.warm();
ok(R.stats.windowed, 'a world over maxCells is windowed');
ok(R.bounds.cols * R.bounds.rows <= 40000, `the window keeps to windowCells (${R.bounds.cols} x ${R.bounds.rows})`);
ok(R.bounds.e0 <= -150 && R.bounds.e1 >= 150 && R.bounds.n0 <= -150 && R.bounds.n1 >= 150, 'and is centred on the visitor');
ok((R.bounds.e0 + 500) % 2 === 0 && (R.bounds.n0 + 500) % 2 === 0, 'cell-aligned with the whole grid');

// Inside the window, the whole grid's plans exactly.
for (const [a, b] of [[[-50, -60], [60, 70]], [[0, 0], [45, 30]], [[-120, 100], [90, -110]]]) {
  const p = R.plan({ e: a[0], n: a[1] }, { e: b[0], n: b[1] });
  const q = whole.plan({ e: a[0], n: a[1] }, { e: b[0], n: b[1] });
  ok(p && q && JSON.stringify(p.points) === JSON.stringify(q.points), `plan ${a} -> ${b} is the whole grid's`);
}
// Off the window.
{
  const t0 = performance.now();
  ok(R.plan({ e: 0, n: 0 }, { e: 450, n: 450 }) === null, 'a plan to a point off the window is null (travel flies)');
  ok(performance.now() - t0 < 50, 'and is answered at once');
  ok(R.blockedAt(450, 450) === false, 'a point off the window but in the world is not blocked');
  ok(R.blockedAt(390, 390) === false, 'even inside a building the window has not reached');
  ok(R.blockedAt(900, 900) === true, 'a point off the world is blocked, as before');
  ok(R.blockedAt(30, 30) === true, 'a building in the window is blocked');
  ok(R.stats.recentres === 0, 'none of that moved the window');
}
// Flying holds it; standing near its edge moves it.
{
  visitor.flying = true; visitor.e = 300; visitor.n = 300;
  R.plan({ e: 300, n: 300 }, { e: 310, n: 310 });
  ok(R.stats.recentres === 0, 'the window stays put while the visitor flies');
  visitor.flying = false;
  const p = R.plan({ e: 300, n: 300 }, { e: 360, n: 330 });
  ok(R.stats.recentres === 1, 'landed near its edge, the window moves to the visitor');
  ok(p && p.points.length >= 2, 'and the plan there is made');
  ok(R.bounds.e1 >= 450 && R.bounds.n1 >= 450, 'the window now reaches round them');
  ok(R.blockedAt(390, 390) === true, 'the far house is now blocked');
  const n = R.stats.recentres;
  R.plan({ e: 310, n: 300 }, { e: 330, n: 330 }); R.blockedAt(320, 320);
  ok(R.stats.recentres === n, 'small moves inside it do not move it again');
}
// The visitor's own walk: the window moves to hold both ends when they fit, and only then.
{
  visitor.e = 300; visitor.n = 300;
  const n = R.stats.recentres;
  const p = R.plan({ e: 300, n: 300 }, { e: 120, n: 160 }, { mode: 'walk' });
  ok(p && R.stats.recentres === n + 1, 'a walk the visitor asks for that the window does not hold moves it to hold both ends');
  ok(R.bounds.e0 <= 20 && R.bounds.e1 >= 400, 'with room round both');
  ok(R.plan({ e: 300, n: 300 }, { e: -300, n: -300 }) === null && R.stats.recentres === n + 1, 'a walk too long for any window is not planned (it is flown), and moves nothing');
  ok(R.plan({ e: 310, n: 310 }, { e: 120, n: 160 }) && R.stats.recentres === n + 1, "someone else's plan does not move it");
}
// A building's stand: the window goes to the building.
{
  visitor.e = 300; visitor.n = 300;
  const s = R.standOff('house', { e: 30, n: 30 }, 10);
  ok(R.bounds.e0 <= 30 - 150 && R.bounds.n0 <= 30 - 150, 'a stand asked for moves the window to the building');
  ok(s && !R.blockedAt(s.e, s.n) && Math.hypot(s.e - 30, s.n - 30) >= 10, `the stand is free ground before it (${s && [s.e, s.n]})`);
}

// An extra layer (1871's context city): its buildings block, its walks are kept to.
{
  visitor.e = -100; visitor.n = -100;
  // A block 60 m square centred on (-100, -100), a 3 m plank walk round it 4 m off its walls, a street beside it.
  const C = -100, at = (e, n) => [C + e, C + n];
  const block = { id: 'ctx_block', pts: [at(-30, -30), at(30, -30), at(30, 30), at(-30, 30)] };
  const walk = (a, b) => ({ centreline_local_enu_m: [at(...a), at(...b)], width_m: 3, kind: 'walk' });
  const extra = (b) => ({
    footprints: b.e0 <= C - 30 && b.e1 >= C + 30 ? [block] : [],
    streets: [{ id: 'ctx_street', path: [at(-36, -80), at(-36, 80)], track_width_m: 8, corridor_width_m: 20 }],
    walks: [walk([-34, -34], [34, -34]), walk([34, -34], [34, 34]), walk([34, 34], [-34, 34]), walk([-34, 34], [-34, -34])],
  });
  const plain = make({ maxCells: 100000, windowCells: 40000 });
  const X = make({ maxCells: 100000, windowCells: 40000, extra });
  const from = { e: C - 34, n: C - 40 }, to = { e: C + 34, n: C + 40 };
  const inBlock = (p) => p.points.some(([e, n], i) => {
    const [pe, pn] = i ? p.points[i - 1] : [from.e, from.n];
    for (let t = 0; t <= 1; t += 0.02) { const x = pe + (e - pe) * t - C, y = pn + (n - pn) * t - C; if (x > -30 && x < 30 && y > -30 && y < 30) return true; }
    return false;
  });
  const through = plain.plan(from, to);
  ok(through && inBlock(through), 'without the layer a route crosses the block (the wall Kevin walked into)');
  ok(X.blockedAt(C, C) === true, 'with it the block is blocked');
  const round = X.plan(from, to, { mode: 'walk' });
  ok(round && !inBlock(round), 'and a walk goes round it');
  ok(X.classAt(C + 34, C) === 'sidewalk', 'along its plank walk');
  ok(!X.clearSegment(C - 40, C, C + 40, C), 'the exact capsule test meets the block too');
}

console.log(`test_route_window: PASS (${checks} checks)`);
