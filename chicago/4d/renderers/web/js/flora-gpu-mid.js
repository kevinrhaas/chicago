/**
 * The near pass's MID cards on the GPU's deal (T-2894, the second slice of
 * T-2774: the near ring's remaining sets on the GPU, so the near re-deal
 * reaches zero).
 *
 * WHICH "MID" THIS IS. The near pass (`rebuildAll` in flora.js) deals three
 * things around the walker: the near tufts, the MID ring's clump cards
 * (`rebuildGround`'s second walk, `flora-mid`: 3-13 m on the phone, 4.5-27 m at
 * `full`), and the forbs, shrubs and far band. This module is the second of
 * them. It is NOT T-2783's far-prairie "mid ring" (the third far band in
 * `TUNE.far.bands`, 12-44 m on the phone), which `rebuildFar` deals and which
 * is still the CPU's (T-2896 carries the far band).
 *
 * WHAT MOVES, AND WHAT DOES NOT. T-2716 drew the near tufts from a deal pass in
 * the shader, and T-2774's first slice (T-2893) retired the CPU near walk: the
 * pass writes every slot a WORD (`nearWord`: the deal's code, the WET bit, the
 * deal-table row) and the page reads the targets back and REAPS them in slot
 * order. This is the same shape for the mid ring:
 *
 *   1. THE DEAL PASS. At every near placement one point per mid lattice slot
 *      (`gl_VertexID` is the slot, in `scatter`'s order, salt 0x9e3779) runs
 *      LATTICE_GLSL, FIELD_GLSL and the deal below against the MID FIELD — a
 *      second kept tile, the near one's 0.125 m texel over the mid ring's
 *      reach (`midFieldSpec`) — and writes, for every slot the lattice keeps
 *      and the tile covers, `(e, tone, -n, word)`: where it stood (float32,
 *      for a reader), the stand's tone (`patchOf` x `vigourTone`, the one
 *      number `placeCard` takes off the ground), and its word. The deal is
 *      `dealNearSlot`'s first four questions — community, short turf, the
 *      matrix share and the weight walk off the slot's ONE draw, `station` —
 *      which is exactly what the mid walk asked; there is no walker test on
 *      the mid ring.
 *   2. THE REAP. flora.js `reap` walks the target in slot order and does what
 *      the CPU mid walk did per slot, on the GPU's answers: the view cone (the
 *      GPU deals the whole ring), the FRINGE (`fringeOf`, the ragged outer
 *      edge, which drops a slot before anything is counted), the matrix census,
 *      `station`'s first question — the page's `growthBlocked`, which the mid
 *      field does not hold — and for a placed slot the INNER HANDOVER
 *      (`slotRing`) and the card (`placeCard`, its five draws on the slot's own
 *      stream). The slot's
 *      position, its fringe and its ring are recomputed there in doubles from
 *      its cell and index (`scatter`'s own arithmetic), and its root is
 *      `terrain.surfaceHeight` there — so a card the GPU places where the CPU
 *      walk did is the same instance to the bit but for its colour's tone,
 *      which is float32. Only the deal runs on the GPU, because only the deal
 *      asks the ground.
 *
 * WHY THE FRINGE IS THE PAGE'S. `fringeOf`'s per-slot dither is a hash of
 * `round(e * 64)`, and a float32 `e` 700 m from the origin can be 30 microns
 * off the double: at 64 per metre that lands a slot across a rounding half
 * about one time in two hundred, and the hash then answers anything at all — a
 * card whose outer edge moves by up to 0.6 of the fringe's amplitude (1 m on
 * the phone, 2.4 m at `full`). Recomputed on the page from the slot's cell and
 * index it is the CPU's own answer, for a few hashes a slot.
 *
 * THE MID FIELD. The near tile is 32 m on a side and keeps the near lattice
 * (7.6 m) inside it from anywhere in its 8 m re-centre cell with 4.4 m in hand
 * for a strip still on its way. The mid lattice reaches 14.6 m on the phone and
 * 31 m at `full`, so the mid deal reads a tile of its own, sized the same way
 * (`midFieldSpec`): the lattice's reach, plus half a re-centre step, plus the
 * near tile's 4.4 m in hand, on each side. It is kept by the pool a strip at a
 * time like the near one (near-field.js `fieldKeeper`) and is NEVER built whole
 * on the main thread: a placement whose lattice the kept mid tile does not wholly
 * cover — the first passes after a boot, a tier change or a teleport, before
 * the pool's tile is home — is dealt by the CPU mid walk exactly as before, and
 * counted (`stats.midCpu`). It holds only what the pool's worker answers
 * (community, WET, TURF, a floor's BLOCKED, TRODDEN, height) on the near tile's
 * texel grid. The page's own share of BLOCKED — the streets' track, the yards,
 * the ground strip and the worked bank, which the near keeper asks at every
 * texel of every strip on the main thread — is left out (`keeper({ page:
 * false })`) and asked at the slot instead, by the reap, for the slots the GPU
 * placed: on the phone profile the near tile's strips cost the main thread
 * about as much as the whole mid walk did, and a tile 1.4-2.5 times as wide
 * asked the same way would have cost more than the walk it retires. Asked at
 * the slot, the answer is also the CPU's own rather than a texel's.
 *
 * FOR THE SLICES AFTER THIS ONE (T-2895 forbs, rosettes and shrubs; T-2896 the
 * far shrubs, the carries and the far band). The forb ring's lattice is never
 * wider than the mid ring's (14.6 m against 14.6 m on the phone, 19.7 against
 * 20.2 balanced, 29 against 31 at full), so its deal can read this same tile;
 * its own pass would add a deal function and a reap beside this one, on the
 * same word layout. The far band reaches 40-150 m and needs a coarser field.
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** The mid deal pass's target width in texels; its height follows the slots. */
export const MID_TARGET_WIDTH = 256;

/** The draws a mid slot's stream has taken when its card is placed: the
 *  jitter's two (`scatter`). `placeCard` draws from the third on. */
export const MID_STREAM_DRAWS = 2;

/**
 * The mid field's spec for a lattice reaching `reach` metres: the near tile's
 * 0.125 m texel and 8 m re-centre step, and a size that keeps the whole lattice
 * inside it from anywhere in the re-centre cell with 4.4 m in hand, rounded up
 * to a whole number of 8-texel blocks. The phone's 14.6 m is 368 texels (46 m),
 * balanced's 20.2 m 464 (58 m) and full's 31 m 632 (79 m). Its origin, the
 * re-centre step's multiple less half the span, falls on the near tile's texel
 * grid at every one of the three.
 */
export function midFieldSpec(reach, { texel = 0.125, recentre = 8, inHand = 4.4 } = {}) {
  const half = reach + recentre / 2 + inHand;
  const size = Math.ceil((2 * half) / texel / 8) * 8;
  return Object.freeze({ texel, size, recentre });
}

/**
 * The mid deal in GLSL: `dealNearSlot`'s community, turf, share-and-weight and
 * station questions, as the mid walk asks them (flora.js `rebuildGround`), off
 * DEAL_GLSL's table. It needs LATTICE_GLSL, FIELD_GLSL and DEAL_GLSL included
 * before it. Returns a NEAR_DEAL code: none 1, turf 2, undealt 3, station 4,
 * placed 6. `row` is the dealt row (-1 before the deal); `tone` the stand's
 * tone where it is placed — `patchOf(e, n) * vigourTone(vigourOf(e, n))`.
 *
 * The station questions are flNearDeal's, line for line, copied rather than
 * shared so the near deal's own compiled code is untouched by this slice.
 */
export const MID_DEAL_GLSL = /* glsl */ `
int flMidDeal(vec2 en, float u, out int row, out float tone) {
  row = -1;
  tone = 0.0;
  uvec2 cls = fieldClass(en);
  int z = int(cls.x) - 1;
  uint flags = cls.y;
  if (z < 0) return 1;
  vec4 z0 = flDealT(4 * z), z1 = flDealT(4 * z + 1);
  if (z1.w < 0.5) return 1;
  if (z0.w > 0.5) return 2;
  bool wet = (flags & 1u) != 0u;
  vec4 side = flDealT(4 * z + (wet ? 3 : 2));
  float share = z0.x;
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
  int it = uDealLayout.y + 5 * row;
  vec4 i0 = flDealT(it), i2 = flDealT(it + 2), i3 = flDealT(it + 3);
  if ((flags & 4u) != 0u) return 4;
  if (z0.y > 0.0 && i0.z > z0.y && (flags & 8u) != 0u) return 4;
  if (wet) {
    if (!(z0.z > 0.5 && i2.w >= 2.0)) return 4;
  } else {
    if (i2.w == 3.0) return 4;
    float y = fieldHeight(en);
    if (z1.z > 0.5 && i3.w > 0.5) {
      float t = flRamp(z1.x, z1.y, y);
      if (t <= 0.0) return 4;
      if (t < 1.0 && flUnit(flHash3(uint(flRoundI(en.x * 4.0)), uint(flRoundI(en.y * 4.0)),
          0x5ad8a1u)) >= t) return 4;
    }
  }
  float vig = flVigour(en);
  tone = flPatch(en) * (0.86 + 0.28 * (1.0 - vig));
  return 6;
}
`;

/**
 * The mid deal pass's two shaders (GLSL ES 3.00, for a RawShaderMaterial),
 * given the chunks they stand on — `ring` is flora-gpu-near.js NEAR_RING_GLSL,
 * for its `flSlotWorld` and `flInTile`. Its own uniform is `uTarget`. One
 * RGBA32F target, one texel per slot: world east, the tone, world z (= -north),
 * and the slot's word (`nearWord`'s layout) — zero where the lattice does not
 * keep the slot or the tile does not cover it.
 */
export function midPassShaders({ lattice, field, deal, ring }) {
  const vertexShader = /* glsl */ `precision highp float; precision highp int;
precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
${lattice}
${field}
${deal}
${ring}
${MID_DEAL_GLSL}
flat out vec4 v0;
void main() {
  int id = gl_VertexID;
  v0 = vec4(0.0);
  vec2 rel; float u; uint rng; uint cellSeed;
  if (flLatticeSlot(id, rel, u, rng, cellSeed)) {
    vec2 en = flSlotWorld(id, cellSeed);
    if (flInTile(en)) {
      int row; float tone;
      int code = flMidDeal(en, u, row, tone);
      bool wet = (fieldClass(en).y & 1u) != 0u;
      v0 = vec4(en.x, tone, -en.y, float(code | (wet ? 8 : 0) | ((row + 1) << 4)));
    }
  }
  float x = float(id % int(uTarget.x)), y = float(id / int(uTarget.x));
  gl_Position = vec4((x + 0.5) / uTarget.x * 2.0 - 1.0, (y + 0.5) / uTarget.y * 2.0 - 1.0, 0.0, 1.0);
  gl_PointSize = 1.0;
}`;
  const fragmentShader = /* glsl */ `precision highp float;
flat in vec4 v0;
layout(location = 0) out vec4 o0;
void main() { o0 = v0; }`;
  return { vertexShader, fragmentShader };
}
