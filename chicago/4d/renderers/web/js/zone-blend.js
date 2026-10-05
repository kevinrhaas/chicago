/**
 * zone-blend.js — where one plant community gives way to the next, as a wide,
 * wandering band instead of a line (T-2125).
 *
 * The owner, 2026-10-05: "the edge of your areas is very sharp between the fort
 * and prairie and prairie and settled lands ... the separations are linear and
 * sharp, please make them less linear ... graduate the areas together ... so its
 * barely perceptible that you cross an area ... maybe 100 meter ... there is a
 * cabin there with a perfectly round settled area around it and it would be
 * irregular".
 *
 * He was reading the code correctly. `flora.js` asked every community's extent
 * an exact question — inside this polygon, inside this elevation band, inside
 * this distance of the water — so the sward changed species, height and density
 * along a line one lattice slot wide. And the settled town's extent is the plat
 * and every standing structure grown by a 50 m Euclidean halo
 * (`tools/derive_settled_town_extent.py`), so a lone cabin out on the prairie
 * stood in a disc of town ground cut out of it with a compass.
 *
 * WHAT THIS MODULE DOES. It answers, for a point, WHERE TO ASK the extents, and
 * it is the only thing that changes. The records, their polygons, their bands
 * and their priorities are untouched, and so is every tool that reads them: the
 * question is moved, not the answer's rule.
 *
 *  - A polygon or box extent is asked at a point MOVED off the plant's own: a
 *    slow wander (a few hundred metres to a few tens, so the line bends the way
 *    a grazed margin or a burn edge does), plus a per-plant draw spread over
 *    the band. The draw is the sum of two uniforms, so it peaks at the plant's
 *    own point: deep in a community every plant still belongs to it, and across
 *    the band the share of each community changes smoothly from all to none.
 *    A cabin's halo is still the record's 50 m — the town is still its own at
 *    the door — but its rim is now a ragged margin that thins over about
 *    100 m, and not a circle.
 *  - An elevation band's limits are DITHERED by a few centimetres, the same
 *    wander and draw scaled to height, so wet prairie climbs into the mesic in
 *    tongues along the contour instead of stopping on it.
 *  - A water buffer keeps its inner limit (the marsh stays at the water) and
 *    only a buffer reaching far from the water — the riverbank timber's 90 m —
 *    has its outer limit spread.
 *
 * WHY THE DRAW IS POSITIONAL. The plant layer re-deals its rings as the walker
 * moves, and the same slot must always answer the same community or the sward
 * would shimmer. The draw is a hash of position alone.
 *
 * WHAT IS EVIDENCE AND WHAT IS NOT. Nothing here is. No survey drew any of
 * these edges — the zone records say so in their own notes — and no survey drew
 * a margin's width either. The band widths are reconstructed, bounded by the
 * dossier's 50-200 m grazed halo around a settlement (`docs/research/02-flora.md`
 * § ZONE 10) and by the owner's "maybe 100 meter"; docs/LIBERTIES.md records it.
 * The communities that meet in a band, and their species, are the records'.
 */

/**
 * The band, per kind of edge, in metres (heights in metres too).
 *
 *  - `reach` — the per-plant draw spans +/-reach, so the whole visible band is
 *    about twice it. 50 m on a polygon is the owner's 100 m.
 *  - `wander` — how far the band's middle swings either side of the recorded
 *    line.
 *
 * A polygon edge is the town's against the prairie, the forest's against the
 * prairie: margins made by grazing, cutting and fire, which wander widely. An
 * elevation band is a contour on a plain with under two metres of relief, so
 * 0.10 m of reach moves the edge tens of metres across a gentle swale and
 * almost nothing up a steep bank — the ground decides how wide it is. A buffer
 * is a distance from the water, and only its far side spreads.
 */
export const ZONE_BLEND = Object.freeze({
  polygon: Object.freeze({ reach: 50, wander: 26 }),
  elevation_band: Object.freeze({ reach: 0.10, wander: 0.06 }),
  buffer: Object.freeze({ reach: 30, wander: 18, from: 30 }),
});

/** The farthest a polygon's answer is asked from the plant's own point, so a
 *  rasterised mask (the town's turf) knows how far past an extent's bounds the
 *  community can now reach. */
export const ZONE_BLEND_MAX_M = ZONE_BLEND.polygon.reach + ZONE_BLEND.polygon.wander;

/**
 * The slow wander, about -1..+1: three waves (~280 m, ~120 m, ~43 m) at oblique
 * angles, so no swing lines up with the grid or the shore. The plant layer asks
 * this millions of times per deal, so it is read from a table and not computed:
 * one 1,024 m tile at 16 m, whose waves complete a whole number of cycles across
 * it so the tile wraps with no seam, bilinear between its nodes. 4,096 floats.
 */
const WANDER_TILE_M = 1024;
const WANDER_CELL_M = 16;
const WANDER_N = WANDER_TILE_M / WANDER_CELL_M;
const WANDER = (() => {
  const t = new Float32Array(WANDER_N * WANDER_N);
  const k = (2 * Math.PI) / WANDER_TILE_M;
  for (let j = 0; j < WANDER_N; j++) {
    for (let i = 0; i < WANDER_N; i++) {
      const e = i * WANDER_CELL_M;
      const n = j * WANDER_CELL_M;
      t[j * WANDER_N + i] = 0.42 * Math.sin(k * (3 * e + 2 * n) + 1.7)
                          + 0.30 * Math.sin(k * (-5 * e + 7 * n) + 0.4)
                          + 0.28 * Math.sin(k * (19 * e - 15 * n) + 2.9);
    }
  }
  return t;
})();

/** The wander at (e, n); `salt` reads the tile elsewhere, so the two axes and
 *  the band limits each wander on their own. */
export function blendWander(e, n, salt = 0) {
  const x = (e + 317 * salt) / WANDER_CELL_M;
  const y = (n + 541 * salt) / WANDER_CELL_M;
  const fx = Math.floor(x);
  const fy = Math.floor(y);
  const tx = x - fx;
  const ty = y - fy;
  const i0 = ((fx % WANDER_N) + WANDER_N) % WANDER_N;
  const j0 = ((fy % WANDER_N) + WANDER_N) % WANDER_N;
  const i1 = i0 + 1 === WANDER_N ? 0 : i0 + 1;
  const j1 = (j0 + 1 === WANDER_N ? 0 : j0 + 1) * WANDER_N;
  const r0 = j0 * WANDER_N;
  const a = WANDER[r0 + i0] + (WANDER[r0 + i1] - WANDER[r0 + i0]) * tx;
  const b = WANDER[j1 + i0] + (WANDER[j1 + i1] - WANDER[j1 + i0]) * tx;
  return a + (b - a) * ty;
}

/** A 32-bit positional hash on a 0.5 m grain (lakeshore.js `ditherHash`'s
 *  mixer), salted, so the same point always answers the same. */
function hash32(e, n, salt) {
  const a = Math.round(e * 2) | 0;
  const b = Math.round(n * 2) | 0;
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ salt;
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

/** Two bytes of a hash as one draw, -1..+1, peaked at 0 (two uniforms summed). */
function draw(h, shift) {
  return (((h >>> shift) & 255) + ((h >>> (shift + 8)) & 255) + 1) / 256 - 1;
}

/**
 * Where to ask a polygon or box extent about the plant at (e, n), written into
 * `out` so the caller's hot loop allocates nothing. `out.w` and `out.d` are a
 * third wander and a third draw, for the band limits below.
 */
const P_REACH = ZONE_BLEND.polygon.reach;
const P_WANDER = ZONE_BLEND.polygon.wander;
export function blendPoint(e, n, out) {
  const reach = P_REACH;
  const wander = P_WANDER;
  const h = hash32(e, n, 0x51ed270b);
  out.e = e + wander * blendWander(e, n, 0) + reach * draw(h, 0);
  out.n = n + wander * blendWander(e, n, 1) + reach * draw(h, 16);
  out.w = blendWander(e, n, 2);
  out.d = draw(hash32(e, n, 0x2c1b3c6d), 0);
  return out;
}

/** How far to shift an elevation band's limits, from a `blendPoint` result. */
export function blendElevation(q) {
  const { reach, wander } = ZONE_BLEND.elevation_band;
  return wander * q.w + reach * q.d;
}

/** How far to shift a far-reaching buffer's outer limit, from a `blendPoint` result. */
export function blendBuffer(q) {
  const { reach, wander } = ZONE_BLEND.buffer;
  return wander * q.w + reach * q.d;
}
