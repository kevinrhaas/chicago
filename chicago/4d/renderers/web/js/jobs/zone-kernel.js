/**
 * The zone finder on a worker (T-2695, the first piece of T-2684's flora deal off
 * the main thread).
 *
 * A spread pass's lattice walk (lattice-kernel.js) used to come back as bare
 * slots, and the page then asked its zone finder of every one of them: about a
 * quarter of what a turn's flora spends on the main thread at the throttled phone
 * profile. `slotZones` answers that question here for a walk's slots, by the
 * same finder code the page runs (flora-zones.js), from the ground the page
 * handed one worker once with `holdGround`
 * (pool.js `holdOnWorker`: it is megabytes, so it is held once, not once a core). It is a job of its own, sent when
 * the walk's slots come home, so the slots come home no later than they did:
 * the walk's reply is what a pass waits on, and a pass that is late finishes
 * in its frame (measured: folding the zones into the walk's own job made each
 * walk about 3 ms slower and a turn drained a third more passes, up to 64 ms).
 *
 * A slot off the measured grid comes back `ZONE_UNASKED`, and so does every slot
 * of a walk whose ground this worker does not hold (it was dropped, or the walk
 * was sent without one): the page asks its own finder for those, so a missing
 * ground costs time, never a different plant.
 */
import { groundZones, ZONE_UNASKED } from '../flora-zones.js';

const grounds = new Map();

/** Keep a page's ground (flora-zones.js `heldGround`) under its key. */
export function holdGround({ key, ground }) {
  grounds.set(key, groundZones(ground));
  return {};
}

/** Forget it: the flora layer that held it was disposed. */
export function dropGround({ key }) {
  grounds.delete(key);
  return {};
}

/** Each slot's community, as the page's `zones` place (1-based, 0 for none,
 *  `ZONE_UNASKED` where the page must ask), for a walk's slots `e`, `n`. */
export function slotZones({ ground, e, n }) {
  const zoneAt = ground == null ? null : grounds.get(ground);
  const zone = new Uint8Array(e.length);
  if (!zoneAt) zone.fill(ZONE_UNASKED);
  else for (let i = 0; i < e.length; i++) zone[i] = zoneAt(e[i], n[i]);
  return { zone };
}
