// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { createTransportClearance } from '../renderers/web/js/transport-clearance.js';
let footprints = [], visitor = null;
const clear = createTransportClearance({ footprints: () => footprints, visitor: () => visitor,
  envelope_local_xz_m: [-1.2, -1.85, 1.2, 4.5] });
const start = { e: 0, n: 0, yaw: 0 };
assert(clear(start, start));
// The vehicle's root clears this obstacle, but the horse/team does not.
footprints = [{ id: 'ahead', pts: [[-.1, -4], [.1, -4], [.1, -3.8], [-.1, -3.8]] }];
assert.equal(clear(start, start), false); assert.equal(clear.lastBlocker, 'ahead');
// A thin wall crossed between two clear endpoints cannot be tunnelled through.
footprints = [{ id: 'thin', pts: [[5, -10], [5.01, -10], [5.01, 10], [5, 10]] }];
assert.equal(clear(start, { e: 10, n: 0, yaw: 0 }), false);
footprints = [];
visitor = { e: 0, n: -4.5, flying: false };
assert.equal(clear(start, start), false); assert.equal(clear.lastBlocker, 'visitor');
visitor = { e: 8, n: 0, flying: false }; assert(clear(start, start));
visitor = { e: 0, n: 0, flying: true }; assert(clear(start, start));
visitor = null;
let shut = true;
footprints = [{ id: 'gate', walls: [{ a: [-3, -3], b: [3, -3], halfThickness: .05, blocks: () => shut }] }];
assert.equal(clear(start, start), false);
shut = false; assert(clear(start, start));
footprints = [{ id: 'parade', ground: true, pts: [[-50, -50], [50, -50], [50, 50], [-50, 50]] }];
assert(clear(start, start));
// A narrow shape fully inside the envelope still collides; a nearby shape outside
// the rotated envelope does not. These are not just root-point/vertex tests.
footprints = [{ id: 'small', pts: [[-.1, -.1], [.1, -.1], [.1, .1], [-.1, .1]] }];
assert.equal(clear(start, start), false);
footprints = [{ id: 'clear', pts: [[8, 8], [9, 8], [9, 9], [8, 9]] }];
assert(clear(start, { e: 0, n: 0, yaw: Math.PI / 2 }));
console.log('transport clearance: whole-team / swept thin wall / actual-state gate / visitor / disposal-independent readers PASS');
