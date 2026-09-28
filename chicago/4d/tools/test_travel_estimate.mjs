#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createRouter } from '../renderers/web/js/route.js';
import { estimateLeg, estimateJaunt, formatEstimate } from '../renderers/web/js/travel-estimate.js';
import { paceSpeed, ARRIVAL_SETTLE_S } from '../renderers/web/js/travel-settings.js';

const place = id => {
  const { placement: p } = JSON.parse(fs.readFileSync(new URL(`../data/sidecars/1835/${id}.json`, import.meta.url)));
  return { e: p.local_e, n: p.local_n };
};
const sauganash = place('sauganash_hotel'), peck = place('peck_store'), greenTree = place('green_tree_tavern');
// Reduced routing fixture, not a reconstruction of the river: actual named
// endpoints, a water barrier, and one off-axis bridge force the real A* detour.
const river = e => e > 20 && e < 60;
const terrain = { heightfield: { loaded: true, originE: -100, originN: -300, widthM: 700, depthM: 600 },
  surfaceHeight: e => river(e) ? -2 : 1, isWater: e => river(e) };
const decks = [{ pts: [[10, -190], [70, -190], [70, -170], [10, -170]], y: 1 }];
const router = createRouter({ terrain, decks });
for (const [name, from, to, mode] of [
  ['Sauganash to Peck near walk', sauganash, peck, 'walk'],
  ['Green Tree to Sauganash bridge horse', greenTree, sauganash, 'horse'],
]) {
  const route = router.plan(from, to); assert(route?.points.length, name);
  const result = estimateLeg({ from, to, mode, router });
  assert(Math.hypot(route.points.at(-1)[0] - to.e, route.points.at(-1)[1] - to.n) < 3, 'route reaches the requested endpoint');
  assert.equal(result.length_m, route.length_m);
  assert.equal(result.seconds, route.length_m / paceSpeed(mode) + ARRIVAL_SETTLE_S);
  assert.equal(result.approx, false);
  if (mode === 'horse') assert(route.length_m > Math.hypot(to.e - from.e, to.n - from.n) * 1.2, 'bridge detour is priced');
  console.log(`PASS ${name}: ${route.length_m.toFixed(1)} m`);
}
const input = { from: greenTree, to: peck, router };
const horse = estimateLeg({ ...input, mode: 'horse' }), fly = estimateLeg({ ...input, mode: 'fly' });
assert(fly.seconds < horse.seconds);
assert.equal(estimateLeg({ ...input, mode: 'instantly' }).seconds, ARRIVAL_SETTLE_S);
assert.equal(estimateLeg({ ...input, mode: 'horse', settings: { horseSpeed: 13 } }).seconds,
  horse.length_m / 13 + ARRIVAL_SETTLE_S);
const fallback = estimateLeg({ ...input, mode: 'walk', router: { plan: () => null } });
assert.equal(fallback.approx, true); assert.equal(fallback.length_m, Math.hypot(peck.e - greenTree.e, peck.n - greenTree.n) * 1.3);
assert.equal(estimateLeg({ ...input, from: null, mode: 'walk' }), null);
assert.equal(estimateLeg({ ...input, to: { e: NaN, n: 0 }, mode: 'fly' }), null);
const story = { opening: { read_s: 15 }, stops: [{ destination: sauganash, read_s: 22 }, { destination: peck, read_s: 22, action_s: 3 }] };
const estimate = estimateJaunt(story, 'walk', { router });
assert.equal(estimate.seconds, 62 + estimate.legs[0].seconds);
assert.equal(estimateJaunt(story, 'walk', { resolve: () => null, router }), null);
assert.equal(formatEstimate(null), 'No estimate'); assert.equal(formatEstimate({ seconds: 150 }), 'about 2.5 min');
assert.match(formatEstimate(fallback), /approximate route/);
console.log('TRAVEL ESTIMATE PASS — routed distance, bridge detour, live paces, flight, instant, fallback and missing positions');
