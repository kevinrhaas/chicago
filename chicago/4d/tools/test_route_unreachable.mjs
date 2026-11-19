#!/usr/bin/env node
/**
 * T-3695 — a goal nobody can walk to is refused at once, and the refusal is exact.
 *
 * Kevin, 2026-11-19: 1812 on dev was "entirely unusable", seconds between frames, once the
 * Jaunts list had opened. Opening it prices every card by route, which builds the 1 m route
 * grid; from then on two people's rounds (human-days.js go) asked every half second for a
 * doorstep in a closed pocket of the fort, and each plan expanded the town's 5.8 million
 * reachable cells before giving up: 2.5 s a frame. route.js now looks back from the goal
 * first (a pocket runs out in a few cells), and keeps the reach set of any plain search that
 * runs out, so the same question is answered by a lookup.
 *
 * On flat ground, a cell-1 grid with a walled pocket and a large walled yard:
 *   - a plan into the pocket is null, refused by the goal-side look (a few cells, no long
 *     search), and the next one is refused too;
 *   - a plan into a walled yard too large for the look is null; the first runs out the
 *     start's side (and keeps it), the next from that side is refused without a search; and
 *     out of the yard the same, the yard's own cells kept;
 *   - every plan is the same from two routers that kept different reach sets (points and
 *     length, to the last digit), over a spread of pairs on both sides, into and out of the
 *     pocket and the yard, so nothing a search would find is ever refused. (Checked against
 *     route.js before T-3695 too, in the PR: the same answers for the same pairs.)
 *
 *   node tools/test_route_unreachable.mjs
 */
import assert from 'node:assert/strict';
import { createRouter } from '../renderers/web/js/route.js';

const flat = { walkHeight: () => 0, surfaceHeight: () => 0, isWater: () => false };
const box = (id, e0, n0, e1, n1) => ({ id, pts: [[e0, n0], [e1, n0], [e1, n1], [e0, n1]] });
// A pocket: a 12 m room walled all round (0.6 m walls), at (40..52, 40..52).
// A yard 300 m square walled all round at (-150..150, -350..-50): large on both sides.
const footprints = [
  box('pocket_s', 40, 40, 52, 40.6), box('pocket_n', 40, 51.4, 52, 52),
  box('pocket_w', 40, 40, 40.6, 52), box('pocket_e', 51.4, 40, 52, 52),
  box('yard_s', -150, -350, 150, -349), box('yard_n', -150, -51, 150, -50),
  box('yard_w', -150, -350, -149, -50), box('yard_e', 149, -350, 150, -50),
];
const make = () => createRouter({ terrain: flat, footprints, cell: 1, radius: 0.34, inflate: 0.1 });
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };

const R = make();
R.warm();
const inPocket = { e: 46, n: 46 };

// Into the pocket.
{
  const before = R.stats.refused ?? 0;
  const t0 = performance.now();
  const r = R.plan({ e: 0, n: 0 }, inPocket, { mode: 'walk' });
  const ms = performance.now() - t0;
  ok(r === null, 'a doorstep inside a closed pocket has no route');
  ok((R.stats.refused ?? 0) === before + 1, 'it is refused by the look back from the goal');
  ok(R.stats.lastExpanded < 4096, `the look runs out inside the pocket (${R.stats.lastExpanded} cells)`);
  ok(R.plan({ e: 10, n: -20 }, inPocket) === null && R.stats.refused === before + 2, 'the next ask is refused too');
  ok(ms < 200, `and quickly (${ms.toFixed(1)} ms)`);
}

// Into and out of the walled yard: both sides larger than the look.
{
  const r = R.plan({ e: 0, n: 0 }, { e: 0, n: -200 });
  ok(r === null, 'nothing walks into a yard walled all round');
  ok(R.stats.lastExpanded > 100000, `the first plan ran out the start's side (${R.stats.lastExpanded} cells)`);
  let before = R.stats.refused;
  let t0 = performance.now();
  ok(R.plan({ e: 120, n: 200 }, { e: -50, n: -300 }) === null && R.stats.refused === before + 1,
    'the next from that side is refused from the kept set, with no search');
  ok(performance.now() - t0 < 50, 'at once');
  ok(R.plan({ e: 0, n: -200 }, { e: 0, n: 0 }) === null && R.stats.lastExpanded > 65536, `out of the yard runs out the yard (${R.stats.lastExpanded} cells)`);
  before = R.stats.refused; t0 = performance.now();
  ok(R.plan({ e: 100, n: -100 }, { e: 300, n: 300 }) === null && R.stats.refused === before + 1, 'and is then refused from the yard\'s kept set');
  ok(performance.now() - t0 < 50, 'at once');
}

// Exact: routers with different kept sets answer alike.
{
  const pairs = [];
  const pts = [[0, 0], [-200, 300], [46, 30], [60, 46], [46, 46], [44, 49], [0, -48.5], [0, -52], [120, -300], [-300, -380]];
  for (const a of pts) for (const b of pts) if (a !== b) pairs.push([a, b]);
  let same = 0, routes = 0, nulls = 0;
  // A router per start, so each start's plans meet a different history of kept sets.
  const fresh = new Map();
  for (const [a, b] of pairs) {
    if (!fresh.has(a)) fresh.set(a, make());
    for (const mode of ['walk', null]) {
      const kept = R.plan({ e: a[0], n: a[1] }, { e: b[0], n: b[1] }, { mode });
      const other = fresh.get(a).plan({ e: a[0], n: a[1] }, { e: b[0], n: b[1] }, { mode });
      assert.deepEqual(kept, other, `${a} -> ${b} (${mode}): one router's answer is the other's`);
      same++; if (other) routes++; else nulls++;
    }
  }
  ok(same === pairs.length * 2 && routes > 0 && nulls > 0, `${same} plans agree (${routes} routes, ${nulls} refused or none)`);
  ok(R.stats.reachSets >= 2, `reach sets kept: ${R.stats.reachSets}`);
}

console.log(`test_route_unreachable: PASS (${checks} checks)`);
