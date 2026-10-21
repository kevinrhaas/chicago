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
 *
 * T-2696: and the rest of each slot's ground in the same reply — water, floor,
 * corridor band and height (flora-ground.js `groundAnswers`) — which the deal
 * reads instead of asking terrain, the floor circles and streets on the page.
 * One reply, not a third job: the deal needs both answers of a slot together.
 */
import { groundZones, ZONE_UNASKED } from '../flora-zones.js';
import { groundAnswers, GROUND_UNASKED, GROUND_WET, GROUND_FLOOR, GROUND_TRODDEN, GROUND_KEEP,
  VERGE_CELL_M, VERGE_KEEP_SHARE } from '../flora-ground.js';
import { FIELD_FLAGS, FIELD_UNASKED } from '../near-field.js';
import { hash3 } from './lattice-kernel.js';

const grounds = new Map();

/** Keep a page's ground (flora-zones.js `heldGround`) under its key. */
export function holdGround({ key, ground }) {
  grounds.set(key, { zoneAt: groundZones(ground), groundAt: groundAnswers(ground) });
  return {};
}

/** Forget it: the flora layer that held it was disposed. */
export function dropGround({ key }) {
  grounds.delete(key);
  return {};
}

/** Each slot's community, as the page's `zones` place (1-based, 0 for none,
 *  `ZONE_UNASKED` where the page must ask), for a walk's slots `e`, `n`; and
 *  (T-2696) its ground's GROUND_* `flags` (`GROUND_UNASKED` where the page must
 *  ask) with the ground's height `y`, full precision, so the plant stands where
 *  the page would have stood it. */
export function slotZones({ ground, e, n }) {
  const held = ground == null ? null : grounds.get(ground);
  const zone = new Uint8Array(e.length);
  const flags = new Uint8Array(e.length);
  const y = new Float64Array(e.length);
  if (!held) zone.fill(ZONE_UNASKED);
  else for (let i = 0; i < e.length; i++) zone[i] = held.zoneAt(e[i], n[i]);
  const groundAt = held?.groundAt;
  if (!groundAt) flags.fill(GROUND_UNASKED);
  else {
    for (let i = 0; i < e.length; i++) {
      flags[i] = groundAt(e[i], n[i]);
      y[i] = groundAt.y;
    }
  }
  return { zone, flags, y };
}

/** T-2707: a community's bits in `fieldRect`'s `table` — short turf, and a
 *  `turfCeiling` its verge crops tall plants to. */
export const FIELD_TABLE_TURF = 1;
export const FIELD_TABLE_CEILING = 2;

/**
 * T-2707 — one rectangle of the near deal's field tile (near-field.js), asked of
 * the ground this worker holds instead of on the page. The texel centres are the
 * tile's: `e0 + (i0 + i + 0.5) * texel`, row by row northward. Per texel, the
 * community (1-based, 0 for none) in `zone`, the FIELD_FLAGS this ground can
 * answer in `flags` — WET, TURF from `table`, BLOCKED for a floor, TRODDEN as
 * flora.js `trodden` gives it for a plant no ceiling admits — and the height in
 * `y`. What it cannot answer is the page's: `growthBlocked` (the streets' cleared
 * track, the yards, the ground strip and the worked bank live on the main
 * thread), so a texel's BLOCKED is completed there; and a texel off the measured
 * grid comes back FIELD_UNASKED in `flags`, for the page to ask whole.
 */
export function fieldRect({ ground, e0, n0, texel, i0, j0, w, h, table, slot = null }) {
  const held = ground == null ? null : grounds.get(ground);
  const zone = new Uint8Array(w * h);
  const flags = new Uint8Array(w * h);
  const y = new Float32Array(w * h);
  const groundAt = held?.groundAt;
  if (!held || !groundAt) { flags.fill(FIELD_UNASKED); return { zone, flags, y }; }
  // T-2967: a SLOT field asks each texel at its lattice slot (`slotPoint`).
  const I0 = slot ? Math.round(e0 / texel) + i0 : 0;
  const J0 = slot ? Math.round(n0 / texel) + j0 : 0;
  const p = [0, 0];
  for (let j = 0; j < h; j++) {
    let n = n0 + (j0 + j + 0.5) * texel;
    for (let i = 0; i < w; i++) {
      let e = e0 + (i0 + i + 0.5) * texel;
      if (slot) { slotPoint(slot, I0 + i, J0 + j, p); e = p[0]; n = p[1]; }
      const k = j * w + i;
      const z = held.zoneAt(e, n);
      const g = z === ZONE_UNASKED ? GROUND_UNASKED : groundAt(e, n);
      if (g === GROUND_UNASKED) { flags[k] = FIELD_UNASKED; continue; }
      const t = z ? table[z] : 0;
      let f = 0;
      if (g & GROUND_WET) f |= FIELD_FLAGS.WET;
      if (t & FIELD_TABLE_TURF) f |= FIELD_FLAGS.TURF;
      if (g & GROUND_FLOOR) f |= FIELD_FLAGS.BLOCKED;
      if (t & FIELD_TABLE_CEILING) {
        const band = g & (GROUND_TRODDEN | GROUND_KEEP);
        if (band === GROUND_TRODDEN || (band && hash3(Math.floor(e / VERGE_CELL_M),
          Math.floor(n / VERGE_CELL_M), 0x2094) / 4294967296 >= VERGE_KEEP_SHARE)) {
          f |= FIELD_FLAGS.TRODDEN;
        }
      }
      zone[k] = z;
      flags[k] = f;
      y[k] = groundAt.y;
    }
  }
  return { zone, flags, y };
}

/**
 * T-2967 — the point a SLOT field's texel (`I`, `J`, world texel indices) is
 * asked at: the slot of `scatter`'s lattice it stands for. A slot field keeps
 * one texel per lattice slot — `sub` x `sub` texels a cell, `perCell = sub²`,
 * texel `(c * sub + k % sub, r * sub + (k / sub | 0))` for slot `k` of cell
 * (`c`, `r`) — so its texel is `cell / sub` and its answer is the CPU's own at
 * that slot's jittered point, not at a texel centre. The jitter is `scatter`'s
 * to the bit: `rngFrom(hash3(hash3(c, r, salt), k, 0x68bc21eb))`'s two draws,
 * on the jittered sub-grid, or the whole cell for the `wild` draw.
 */
export function slotPoint({ salt, cell, sub, wild }, I, J, out = [0, 0]) {
  const c = Math.floor(I / sub);
  const r = Math.floor(J / sub);
  const sx = I - c * sub;
  const sy = J - r * sub;
  const k = sy * sub + sx;
  let s = hash3(hash3(c, r, salt), k, 0x68bc21eb) >>> 0 || 1;
  s = xorshift(s);
  const je = s / 4294967296;
  s = xorshift(s);
  const jn = s / 4294967296;
  out[0] = (c + (wild ? je : (sx + je) / sub)) * cell;
  out[1] = (r + (wild ? jn : (sy + jn) / sub)) * cell;
  return out;
}

function xorshift(s) {
  s ^= s << 13; s >>>= 0;
  s ^= s >>> 17;
  s ^= s << 5; s >>>= 0;
  return s;
}
