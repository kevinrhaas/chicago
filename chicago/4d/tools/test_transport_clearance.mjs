// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { createTransportClearance, giveRoomStand } from '../renderers/web/js/transport-clearance.js';
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

// T-3475: Step back to let it pass. A visitor standing in the road of a team heading south
// (yaw 0: +z is -n) steps sideways out of every envelope along the road ahead.
{
  const envelope = [-1.2, -1.85, 1.2, 4.5];
  const road = Array.from({ length: 121 }, (_, i) => ({ e: 0, n: -i * .25, yaw: 0 }));
  const check = createTransportClearance({ footprints: () => [], visitor: () => person, envelope_local_xz_m: envelope });
  let person = { e: .3, n: -8, flying: false };
  assert.equal(check(road[0], road[1]) && road.every((p, i) => !i || check(road[i - 1], p)), false, 'the visitor is in the road');
  const stand = giveRoomStand({ poses: road, envelope_local_xz_m: envelope, at: person });
  assert(stand && stand.moved_m > 0 && stand.moved_m <= 2.5, `a short step aside (${stand?.moved_m} m)`);
  assert(Math.abs(stand.n - person.n) < .5, 'sideways, not ahead or behind');
  assert(stand.e > person.e, 'to the near side of the road');
  person = { ...stand, flying: false };
  assert(road.every((p, i) => !i || check(road[i - 1], p)), 'clear of the whole road it drives next');
  // Already clear: no step.
  assert.equal(giveRoomStand({ poses: road, envelope_local_xz_m: envelope, at: { e: 6, n: -8 } }).moved_m, 0);
  // The near side is a wall: the far side, or nothing.
  const far = giveRoomStand({ poses: road, envelope_local_xz_m: envelope, at: { e: .3, n: -8 }, blockedAt: e => e > .5 });
  assert(far && far.e < -1.5, 'steps out the other side when the near side is blocked');
  assert.equal(giveRoomStand({ poses: road, envelope_local_xz_m: envelope, at: { e: .3, n: -8 }, blockedAt: () => true }), null);
  assert.throws(() => giveRoomStand({ poses: [], envelope_local_xz_m: envelope, at: { e: 0, n: 0 } }));
  console.log('transport clearance: Step back finds the nearest sideways stand clear of the road ahead, either side, or none PASS');
}
