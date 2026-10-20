/**
 * T-2696 — the rest of a slot's ground, answered where its community is.
 *
 * T-2695 moved the zone finder onto a worker of the job pool; the deal still
 * asked four more questions of every slot on the main thread: is it under water
 * (terrain.js `isWater`), is it on a floor (a building's footprint, through
 * flora.js's floor circles), where in an opened street's corridor does it stand
 * (streets.js `verge`, for `trodden`), and how high is the ground
 * (`surfaceHeight`). None of them depends on the species, so the worker that
 * holds the zones' ground answers them too, slot for slot, in the same reply
 * (jobs/zone-kernel.js `slotZones`), and the deal reads the answer instead of
 * asking. A slot without one is asked on the page, as before, by the same code:
 * the floor circles and the corridor bands live here and in street-verge.js so
 * that both sides run them.
 *
 * Like the zones, the answer is given only ON the measured grid, where the
 * height is the grid's own bilinear sample (flora-zones.js `gridSampler`); off
 * it a slot comes back `GROUND_UNASKED` and the page asks.
 */
import { gridSampler, onGrid, pointInPolygon } from './flora-zones.js';
import { vergeAt } from './street-verge.js';

/** The slot is under water: terrain.js `isWater`, the grid's height below the shore. */
export const GROUND_WET = 1;
/** The slot is on a floor: inside a building's footprint circle and polygon. */
export const GROUND_FLOOR = 2;
/** The slot is trodden corridor: the worked roadway, or verge farther than
 *  VERGE_KEEP_M in from the lot line, where no tall turf plant stands. */
export const GROUND_TRODDEN = 4;
/** The slot is the last VERGE_KEEP_M of a corridor at its lot line, where a
 *  positional hash keeps some tall weeds (flora.js `trodden`). */
export const GROUND_KEEP = 8;
/** A slot the worker did not answer (off the measured grid, or no ground held). */
export const GROUND_UNASKED = 255;

/**
 * T-2094 — the trodden verge's kept weeds (flora.js `trodden`): within this far
 * of the corridor's edge, one VERGE_CELL_M cell in VERGE_KEEP_SHARE keeps its
 * tall plants. 2.6 m is a plank walk (1.83 m) and its 0.2 m clearance standing
 * at the lot line, plus the half metre at its street edge a boot does not reach.
 */
export const VERGE_KEEP_M = 2.6;
export const VERGE_CELL_M = 1.5;
export const VERGE_KEEP_SHARE = 0.22;

/** Which of the corridor's bands a streets.js `verge` answer falls in, for
 *  `trodden`: 0 outside every corridor, else GROUND_TRODDEN or GROUND_KEEP. */
export function vergeBand(at) {
  if (!at) return 0;
  return at.band !== 'verge' || at.edgeM > VERGE_KEEP_M ? GROUND_TRODDEN : GROUND_KEEP;
}

/** Each footprint's bounding circle, with a metre of clearance: a wall meeting
 *  the sward flush reads as a wall sunk in a lawn. */
export function footprintCircles(footprints) {
  return footprints.map((f) => {
    let e = 0;
    let n = 0;
    for (const p of f.pts) { e += p[0]; n += p[1]; }
    e /= f.pts.length;
    n /= f.pts.length;
    let r2 = 0;
    for (const p of f.pts) r2 = Math.max(r2, (p[0] - e) ** 2 + (p[1] - n) ** 2);
    const r = Math.sqrt(r2) + 1.0;
    return { e, n, r2: r * r, pts: f.pts };
  });
}

/**
 * T-2096. The floor circles bucketed on a world grid, so a slot asks only the
 * ones that can contain it. Every circle is filed in every cell its bounding
 * square touches, and a point inside a circle is inside that square, so the
 * bucket holds every circle the full list would have matched: the answer is
 * the same and only the misses are no longer paid for.
 */
const CIRCLE_CELL_M = 8;
export function circleGrid(circles) {
  const cells = new Map();
  const key = (i, j) => (i + 32768) * 65536 + (j + 32768);
  for (const b of circles) {
    const r = Math.sqrt(b.r2);
    const i0 = Math.floor((b.e - r) / CIRCLE_CELL_M);
    const i1 = Math.floor((b.e + r) / CIRCLE_CELL_M);
    const j0 = Math.floor((b.n - r) / CIRCLE_CELL_M);
    const j1 = Math.floor((b.n + r) / CIRCLE_CELL_M);
    for (let i = i0; i <= i1; i++) {
      for (let j = j0; j <= j1; j++) {
        const k = key(i, j);
        const list = cells.get(k);
        if (list) list.push(b); else cells.set(k, [b]);
      }
    }
  }
  return {
    size: circles.length,
    at(e, n) {
      return cells.get(key(Math.floor(e / CIRCLE_CELL_M), Math.floor(n / CIRCLE_CELL_M)));
    },
  };
}

/** Whether (e, n) is on a floor of `blocks` (a `circleGrid`): nothing roots there. */
export function onFloor(blocks, e, n) {
  const near = blocks.at(e, n);
  if (near) for (const b of near) {
    const dx = e - b.e;
    const dz = n - b.n;
    if (dx * dx + dz * dz < b.r2 && pointInPolygon(b.pts, e, n)) return true;
  }
  return false;
}

/**
 * The worker's side: from a held ground (flora-zones.js `heldGround`, with
 * `floors` — each footprint's points — and `streets` — street-verge.js
 * `vergeRecords` — added by flora.js), a function from a point to its GROUND_*
 * flags, or GROUND_UNASKED off the measured grid. The height it read is left
 * in the function's `y`. Null when the ground carries no floors or streets.
 */
export function groundAnswers(g) {
  if (!g?.hf || !Array.isArray(g.floors) || !Array.isArray(g.streets)) return null;
  const sample = gridSampler(g.hf);
  const blocks = circleGrid(footprintCircles(g.floors.map((pts) => ({ pts }))));
  const at = (e, n) => {
    if (!onGrid(g.hf, e, n)) return GROUND_UNASKED;
    const y = sample(e, n);
    at.y = y;
    let f = y < g.shoreY ? GROUND_WET : 0;
    if (onFloor(blocks, e, n)) f |= GROUND_FLOOR;
    return f | vergeBand(vergeAt(g.streets, e, n));
  };
  at.y = 0;
  return at;
}
