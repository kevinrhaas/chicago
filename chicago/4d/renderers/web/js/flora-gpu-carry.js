/**
 * The far pass's CARRY SETS on the GPU's deal (T-2896, the fourth slice of
 * T-2774: the near ring's remaining sets on the GPU).
 *
 * WHAT THE CARRIES ARE. T-2035's `flora-near-carry` and `flora-mid-carry`: the
 * SAME near and mid lattice slots as the detailed rings (the near ring's salt
 * 0x51ed27 and the mid ring's 0x9e3779, both on the `'strata'` draw), dealt
 * the same matrix species and drawn with a cheaper archetype past the detailed
 * ring's handover, out to the mid ring's edge (the near carry) and the far
 * band's first edge (the mid carry): 18.6 and 45.6 m on the phone, 35 and 69 m
 * at `full`. flora.js `rebuildCarry` walked both lattices on every far pass
 * (every 4 m walked, or a turn), and the T-2895 profile read that walk as
 * flora's largest main-thread cost: 3.9 s of the far pass's 4.7 over the phone
 * profile's walk, turn and flight. Most of it was not the walk: about half of a
 * spread pass's slots reached the deal before the job pool's answers for them
 * came home, and the page asked its own zone finder and the ground for those.
 *
 * WHAT MOVES. The deal, onto a kept tile that is always home:
 *
 *   1. THE CARRY FIELD. A third kept tile, the near and mid tiles' 0.125 m
 *      texel over the mid carry's reach (`midFieldSpec` of it: 864 texels on
 *      the phone, 1072 balanced, 1240 at `full`), kept by the pool a strip at a
 *      time and holding only the workers' answers (`keeper({ page: false })`),
 *      exactly as the mid field does. Its texel grid is the mid field's, so a
 *      slot both tiles cover reads the same texel answer from either.
 *   2. THE DEAL. One point per slot of each carry walk (`gl_VertexID` is the
 *      slot, in `scatter`'s order), the near carry's rows first and the mid
 *      carry's after (`uSlot0`), one render into one RGBA32F target: the
 *      community, short turf, the matrix share and the weight walk off the
 *      slot's one draw, and the ground's half of `station` — a floor, the
 *      trodden verge against the species' height, the water substrates — and
 *      `(e, 0, -n, word)` with T-2774's word layout (`nearWord`).
 *   3. THE REAP. flora.js `reapCarry` walks the target in slot order and does
 *      what the walk did per slot: the point in doubles from cell and index,
 *      the lattice ring and the view cone, the slot's own handover (the
 *      detailed ring's `slotRing` with its fringe) and its own edge (the carry
 *      fringe), and the page's half of `station`: `growthBlocked` and the woody
 *      band (T-1056) at `terrain.surfaceHeight`, which the tile's float32
 *      height cannot answer to the bit; then `placeGraminoid` / `placeCard` on
 *      the slot's own stream past the jitter's two draws, the card's tone
 *      computed there in doubles. A carry the GPU places where the walk did is
 *      the same instance to the bit, colour included.
 *
 * The carries are not counted into the drawn census (they never were), and
 * carry no heads, so the reap has nothing to hand anyone else.
 *
 * A far pass whose carries the kept tile does not wholly cover (after a boot,
 * a tier change or a jump, until the pool's tile is home) walks them on the CPU
 * exactly as before, counted (`carryCpu`).
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** The draws a carry slot's stream has taken when its plant is placed: the
 *  jitter's two (`scatter`). `placeGraminoid` and `placeCard` draw from the
 *  third on. */
export const CARRY_STREAM_DRAWS = 2;

/**
 * The carry deal in GLSL: the matrix deal both carries make (flora.js
 * `rebuildCarry`: community, short turf, `zone.matrixShare` and the weight
 * walk over the dry or wet graminoids), and the ground's half of `station` —
 * flora-gpu-mid.js `flMidDeal` without the woody band (the page asks it at the
 * slot's own height) and without the tone (the page computes it in doubles).
 * Needs LATTICE_GLSL, FIELD_GLSL and DEAL_GLSL before it. Returns a NEAR_DEAL
 * code: none 1, turf 2, undealt 3, station 4, placed 6 (the page asks the
 * rest). `row` is the dealt graminoid row (-1 before the deal).
 */
export const CARRY_DEAL_GLSL = /* glsl */ `
int flCarryDeal(vec2 en, float u, out int row) {
  row = -1;
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
  vec4 i0 = flDealT(it), i2 = flDealT(it + 2);
  if ((flags & 4u) != 0u) return 4;
  if (z0.y > 0.0 && i0.z > z0.y && (flags & 8u) != 0u) return 4;
  if (wet) {
    if (!(z0.z > 0.5 && i2.w >= 2.0)) return 4;
  } else if (i2.w == 3.0) return 4;
  return 6;
}
`;

/**
 * The carry deal's two shaders (GLSL ES 3.00, for a RawShaderMaterial), given
 * the chunks they stand on — `ring` is flora-gpu-near.js NEAR_RING_GLSL, for
 * its `flSlotWorld` and `flInTile`. Its own uniforms are `uTarget` (the target's
 * size) and `uSlot0` (the first texel this walk writes). One texel per slot:
 * world east, 0, world z (= -north), and the slot's word — zero where the
 * lattice does not keep the slot or the tile does not cover it.
 */
export function carryPassShaders({ lattice, field, deal, ring }) {
  const vertexShader = /* glsl */ `precision highp float; precision highp int;
precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
uniform int uSlot0;
${lattice}
${field}
${deal}
${ring}
${CARRY_DEAL_GLSL}
flat out vec4 v0;
void main() {
  int id = gl_VertexID;
  v0 = vec4(0.0);
  vec2 rel; float u; uint rng; uint cellSeed;
  if (flLatticeSlot(id, rel, u, rng, cellSeed)) {
    vec2 en = flSlotWorld(id, cellSeed);
    if (flInTile(en)) {
      int row;
      int code = flCarryDeal(en, u, row);
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
