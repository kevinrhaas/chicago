#!/usr/bin/env node
// T-2732: Read frame pacing's arithmetic and its visibility rule, without a browser.
// The page drive itself is shown by tools/qa_pacing_read_t2732.mjs in the real app.
import assert from 'node:assert/strict';
import {
  pacingReadOffered, summarise, fell, formatReading, MOVES, MODES, READ_TIER,
} from '../renderers/web/js/pacing-read.js';

const loc = (pathname, search = '') => ({ pathname, search });
const doc = (pill) => ({ getElementById: (id) => (pill && id === '__devpill' ? {} : null) });

// Offered on the dev preview (by its path or its banner) and with ?pacing=read; never on
// production without the parameter, and ?pacing=off hides it even on the preview.
assert.equal(pacingReadOffered(loc('/4d/walk/'), doc(false)), false);
assert.equal(pacingReadOffered(loc('/4d/1835/'), doc(false)), false);
assert.equal(pacingReadOffered(loc('/4d/dev/walk/'), doc(false)), true);
assert.equal(pacingReadOffered(loc('/4d/dev/1835/'), doc(false)), true);
assert.equal(pacingReadOffered(loc('/site/4d/walk/index.html'), doc(true)), true);
assert.equal(pacingReadOffered(loc('/4d/walk/', '?pacing=read'), doc(false)), true);
assert.equal(pacingReadOffered(loc('/4d/dev/walk/', '?pacing=off'), doc(true)), false);
assert.equal(pacingReadOffered(undefined, undefined), false);

// The moves and tier are the ones `measure_walk_frames.mjs --live` reads at the phone profile.
assert.deepEqual(MOVES, ['walk', 'turn', 'flight']);
assert.deepEqual(MODES, ['fixed', 'adaptive']);
assert.equal(READ_TIER, 'light');

// driveLive's arithmetic: population sd, p95 as the floor(0.95 n)-th sorted interval.
{
  // Intervals 10, 20, 30, 40: mean 25, population sd sqrt(125).
  const r = summarise([0, 10, 30, 60, 100]);
  assert.equal(r.draws, 5);
  assert.equal(r.mean, 25);
  assert.ok(Math.abs(r.sd - Math.sqrt(125)) < 1e-12);
  assert.equal(r.median, 30); // floor(0.5 * 4) = index 2
  assert.equal(r.p95, 40); // floor(0.95 * 4) = index 3
  assert.equal(r.max, 40);
  assert.equal(r.over33, 1);
  assert.equal(r.over50, 0);
}
{
  // A steady 60 Hz with one 50.1 ms hitch in twenty: the p95 is the hitch's index.
  const starts = [0];
  for (let i = 0; i < 20; i++) starts.push(starts.at(-1) + (i === 7 ? 50.1 : 16.7));
  const r = summarise(starts);
  assert.ok(Math.abs(r.p95 - 50.1) < 1e-9);
  assert.equal(r.over50, 1);
  assert.equal(r.over33, 1);
}
{
  // Nothing drawn, or one draw: zeros, never NaN.
  for (const s of [[], [5]]) {
    const r = summarise(s);
    assert.deepEqual([r.mean, r.sd, r.median, r.p95, r.max], [0, 0, 0, 0, 0]);
  }
}

// FELL needs both sd and p95 down; one alone is not a fall.
const m = (sd, p95) => ({ sd, p95 });
assert.equal(fell({ fixed: m(10, 40), adaptive: m(6, 30) }), true);
assert.equal(fell({ fixed: m(10, 40), adaptive: m(6, 45) }), false);
assert.equal(fell({ fixed: m(10, 40), adaptive: m(12, 30) }), false);
assert.equal(fell({ fixed: m(10, 40), adaptive: m(10, 40) }), false);

// The copied text names the device and carries a row per move and mode plus its verdict.
{
  const row = (sd, p95) => ({ draws: 300, mean: 16.8, sd, median: 16.7, p95, max: 70, over33: 3, over50: 1 });
  const pairs = Object.fromEntries(MOVES.map((mv) => [mv, { fixed: row(9, 33), adaptive: row(4, 17) }]));
  pairs.turn.adaptive = row(11, 20);
  const text = formatReading({ when: '2026-10-17T18:00:00.000Z', tier: 'light', seconds: 5, build: 'v-test',
    device: { screen: '390x844 (screen 390x844)', ratio: 3, ua: 'Mozilla/5.0 (iPhone)' }, pairs });
  assert.match(text, /^Read frame pacing \(T-2733\)/);
  assert.match(text, /390x844 \(screen 390x844\) at ratio 3, detail light, 5 s a mode/);
  assert.match(text, /Mozilla\/5\.0 \(iPhone\)/);
  for (const mv of MOVES) for (const md of MODES) assert.match(text, new RegExp(`^${mv}\\s+${md}\\s+300 `, 'm'));
  assert.equal((text.match(/^ {2}FELL:/gm) ?? []).length, 2);
  assert.equal((text.match(/^ {2}DID NOT FALL:/gm) ?? []).length, 1);
  assert.match(text, /DID NOT FALL: sd 9\.0 → 11\.0 ms, p95 33\.0 → 20\.0 ms/);
}

console.log('pacing-read: visibility, driveLive arithmetic, verdict and copied text hold (T-2732)');
