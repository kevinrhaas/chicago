import assert from 'node:assert/strict';
import {
  bootProgress, easeInOut, reducedProgress, settleDurationMs, yearForProgress,
} from '../renderers/web/js/arrival.js';

assert.equal(easeInOut(0), 0);
assert.equal(easeInOut(1), 1);

let previous = 2026;
for (let i = 0; i <= 100; i++) {
  const y = yearForProgress(i / 100, 2026, false);
  assert.ok(y <= previous + 1e-9, `year rolled forward at ${i}%: ${y} > ${previous}`);
  assert.ok(y >= 1836, `pre-ready year crossed 1836: ${y}`);
  previous = y;
}
assert.equal(yearForProgress(1, 2026, false), 1836);
assert.equal(yearForProgress(0.6, 2026, true), 1835);

const phases = [
  { id: 'scene', essential: true, startedAt: 0, endedAt: 1000, units: 10, unitsDone: 10, error: null },
  { id: 'flora', essential: true, startedAt: 1000, endedAt: null, units: null, unitsDone: 0, error: null },
  { id: 'people', essential: false, startedAt: 0, endedAt: null, units: null, unitsDone: 0, error: null },
];
const expected = { scene: 1, flora: 10, people: 99 };
const early = bootProgress(phases, expected, 2000);
const late = bootProgress(phases, expected, 20000);
assert.ok(late >= early, 'elapsed progress must be monotone');
assert.ok(late < 1, 'an overrunning active phase must not claim completion');
assert.ok(late <= (1 + 10 * 0.92) / 11 + 1e-9, 'elapsed phase must ease only to 92% of its weight');

const unitPhases = [
  { id: 'scene', essential: true, startedAt: 0, endedAt: null, units: 100, unitsDone: 50, error: null },
];
assert.equal(bootProgress(unitPhases, { scene: 2 }, 999999), 0.5);

assert.equal(settleDurationMs({ reducedMotion: true, bootDurationMs: 9000 }), 0);
assert.equal(settleDurationMs({ reducedMotion: false, bootDurationMs: 1499 }), 0);
assert.equal(settleDurationMs({ reducedMotion: false, bootDurationMs: 1500 }), 300);

const reduced = new Set([0, .1, .24, .26, .49, .51, .74, .9, .999].map(reducedProgress));
assert.ok(reduced.size <= 4, `reduced motion produced ${reduced.size} pre-ready updates`);

console.log('ARRIVAL PASS — monotone, bounded, honest readiness and reduced-motion pacing');
