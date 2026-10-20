/**
 * The near pass's FORBS, ROSETTES and SHRUBS on the GPU's deal (T-2895, the
 * third slice of T-2774: the near ring's remaining sets on the GPU, so the near
 * re-deal reaches zero).
 *
 * WHAT MOVES. `rebuildForbs` in flora.js walks the forb ring twice per near
 * pass: the forb lattice (salt 0x2545f9, the sparse `'lattice'` draw), whose
 * slots are forbs or basal rosettes (`flora-forb`, `flora-rosette`), and the
 * shrub stratum's own pass over the same ring (salt 0x7b5c1d, the `'wild'`
 * draw: K54, an independent draw so a shrub stands OVER the herbs rather than
 * instead of them), `flora-shrub`. Both put up the flowering plants' heads.
 * T-2894 dealt the mid ring's cards in GLSL against the MID FIELD (flora-gpu-
 * mid.js); this is the same shape for these two walks, against the SAME tile:
 *
 *   1. THE DEAL. The forb ring's lattice is never wider than the mid ring's
 *      (14.6 against 14.6 m on the phone, 19.7 against 20.2 balanced, 29
 *      against 31 at `full`), so the kept mid tile already covers it. Two more
 *      point draws go into the mid deal pass's own render — the same target,
 *      the same tile and its textures, no upload of their own — one point per
 *      slot of each walk, written after the mid slots (`uSlot0`). Each slot
 *      runs LATTICE_GLSL and the deal below: the community, the forb (or
 *      shrub) share and the weight walk off the slot's ONE draw (K49(b)), and
 *      the ground's half of `station` — a floor (BLOCKED), the trodden verge
 *      (TRODDEN against the species' own height), the water substrates — and
 *      writes `(e, 0, -n, word)` with T-2774's word layout (`nearWord`: code,
 *      WET, the forb row + 1). A slot the deal hands a species carries its row
 *      whatever `station` says, because the page asks the rest.
 *   2. THE REAP. flora.js `reapForbs` walks the targets in slot order and does
 *      what the two CPU walks did per slot, on the GPU's answers: the slot's
 *      point recomputed in doubles from its cell and index, the ring and the
 *      view cone, the FRINGE (`fringeOf`), the census, and then the page's
 *      half — see below — and `placeForb` / `placeShrub` and the heads
 *      (`maybeHead`, a forb's several inflorescences) on the slot's own stream
 *      past the jitter's two draws.
 *
 * WHAT STAYS ON THE PAGE, AND WHY. Everything a slot is asked after its deal
 * that a texel cannot answer to the bit, or that the tile does not hold:
 *
 *   - FORBSEAT (T-2086): a kept yard turns its forb slot out, and a stated
 *     share of those slots is re-seated in the strip beside the lot line. That
 *     is the record's geometry (kept-ground.js), and a re-seated slot is asked
 *     EVERYTHING again at its new foot — so the page asks `station` there
 *     itself, whole, as the walk did. On short turf a forb stands only where a
 *     kept lot re-seats it (T-2122), which is the same question.
 *   - `growthBlocked` (the streets' track, the yards, the ground strip, the
 *     worked bank), which the mid field leaves out (`keeper({ page: false })`).
 *   - THE WOODY BAND (T-1056): a woody role's station is a smoothstep over the
 *     zone record's `establishes_m` at the ground's height, and a positional
 *     hash inside the ramp. The texel's float32 height is up to a texel's
 *     slope off the slot's own, and on the shrubs this band is most of what
 *     `station` refuses; asked on the page at `terrain.surfaceHeight` it is
 *     the CPU's own answer.
 *   - the walker's clearance (`crowdsTheWalker`), off that height.
 *   - the patch tone (`patchOf`), which is noise and no ground: computed
 *     there in doubles, a forb's colour is the CPU's to the bit.
 *
 * What the GPU answers is the ground's half: the community, the water test, the
 * floors and the verge band at every slot. On the phone profile that was the
 * cheap half — the pool's workers already brought those answers home with the
 * walk's slots — so the reap costs the main thread about what the two walks did
 * (docs/RENDERING.md App. B, T-2895). What leaves the near pass is the walks
 * themselves and their trips to the pool and back, so a spread pass lands in
 * fewer frames and more passes fit in one.
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** The draws a forb or shrub slot's stream has taken when its plant is placed:
 *  the jitter's two (`scatter`). `placeForb` and `placeShrub` draw from the
 *  third on. */
export const FORB_STREAM_DRAWS = 2;

/**
 * The forb deal in GLSL, off DEAL_GLSL's table — its forb section
 * (`dealTable`'s `forbBase`, `forbItemBase`). Needs LATTICE_GLSL, FIELD_GLSL and
 * DEAL_GLSL included before it. `shrub` picks the shrub stratum's share and
 * subsets. Returns a NEAR_DEAL code: none 1 (no community, or none of this
 * stratum in it), undealt 3, station 4 (the ground's half of `station`
 * refuses it), placed 6 (it does not: the page asks the rest). `row` is the
 * forb section's row from the deal on (-1 before it).
 */
export const FORB_DEAL_GLSL = /* glsl */ `
uniform ivec2 uForbLayout;
int flForbDeal(vec2 en, float u, bool shrub, out int row) {
  row = -1;
  uvec2 cls = fieldClass(en);
  int z = int(cls.x) - 1;
  uint flags = cls.y;
  if (z < 0) return 1;
  int hz = uForbLayout.x + 6 * z;
  vec4 f0 = flDealT(hz), f1 = flDealT(hz + 1);
  if ((shrub ? f1.y : f1.x) < 0.5) return 1;
  bool wet = (flags & 1u) != 0u;
  float share = shrub ? (wet ? f0.w : f0.z) : (wet ? f0.y : f0.x);
  vec4 side = flDealT(hz + 2 + (shrub ? 2 : 0) + (wet ? 1 : 0));
  int count = int(side.y);
  if (!(share > 0.0) || u >= share || count == 0) return 3;
  float target = (u / share) * side.z;
  int first = int(side.x);
  float acc = 0.0;
  row = int(flDealT(first + count - 1).y);
  for (int i = 0; i < count; i++) {
    vec4 ent = flDealT(first + i);
    acc += ent.x;
    if (target <= acc) { row = int(ent.y); break; }
  }
  // station, the ground's half: a floor, the trodden verge, the water.
  vec4 z0 = flDealT(4 * z);
  vec4 i0 = flDealT(uForbLayout.y + 2 * row);
  if ((flags & 4u) != 0u) return 4;
  if (z0.y > 0.0 && i0.z > z0.y && (flags & 8u) != 0u) return 4;
  float substrate = flDealT(uForbLayout.y + 2 * row + 1).x;
  if (wet) {
    if (!(z0.z > 0.5 && substrate >= 2.0)) return 4;
  } else if (substrate == 3.0) return 4;
  return 6;
}
`;

/**
 * The forb deal's two shaders (GLSL ES 3.00, for a RawShaderMaterial), given
 * the chunks they stand on — `ring` is flora-gpu-near.js NEAR_RING_GLSL, for
 * its `flSlotWorld` and `flInTile`. Its own uniforms are `uTarget` (the mid
 * target's size, shared), `uSlot0` (the first texel this walk writes) and
 * `uShrub` (1 for the shrub stratum). One texel per slot: world east, 0, world
 * z (= -north), and the slot's word — zero where the lattice does not keep the
 * slot or the tile does not cover it.
 */
export function forbPassShaders({ lattice, field, deal, ring }) {
  const vertexShader = /* glsl */ `precision highp float; precision highp int;
precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
uniform int uSlot0;
uniform int uShrub;
${lattice}
${field}
${deal}
${ring}
${FORB_DEAL_GLSL}
flat out vec4 v0;
void main() {
  int id = gl_VertexID;
  v0 = vec4(0.0);
  vec2 rel; float u; uint rng; uint cellSeed;
  if (flLatticeSlot(id, rel, u, rng, cellSeed)) {
    vec2 en = flSlotWorld(id, cellSeed);
    if (flInTile(en)) {
      int row;
      int code = flForbDeal(en, u, uShrub == 1, row);
      bool wet = (fieldClass(en).y & 1u) != 0u;
      v0 = vec4(en.x, 0.0, -en.y, float(code | (wet ? 8 : 0) | ((row + 1) << 4)));
    }
  }
  int t = uSlot0 + id;
  float x = float(t % int(uTarget.x)), y = float(t / int(uTarget.x));
  gl_Position = vec4((x + 0.5) / uTarget.x * 2.0 - 1.0, (y + 0.5) / uTarget.y * 2.0 - 1.0, 0.0, 1.0);
  gl_PointSize = 1.0;
}`;
  const fragmentShader = /* glsl */ `precision highp float;
flat in vec4 v0;
layout(location = 0) out vec4 o0;
void main() { o0 = v0; }`;
  return { vertexShader, fragmentShader };
}
