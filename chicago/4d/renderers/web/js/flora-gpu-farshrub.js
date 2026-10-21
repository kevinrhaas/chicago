/**
 * The far pass's FAR SHRUBS on the GPU's deal (T-2968, the third slice of
 * T-2896: the far shrubs, the carry sets and the far band on the GPU's deal).
 *
 * WHAT MOVES. `rebuildFarShrubs` in flora.js walks T-2014's far shrubs at every
 * far pass (every `TUNE.farShrub.step`, 4 m walked, or a turn of the cone):
 * the shrub stratum's own lattice — the forb cell and its four slots, salt
 * 0x7b5c1d, the `'wild'` draw's full-cell jitter — from just inside the forb
 * ring's handover out to `TUNE.farShrub.radius` (70 m on the phone, 105
 * balanced, 140 at `full`). It is the SAME lattice as the forb ring's shrub
 * walk (T-2895, flora-gpu-forb.js `uShrub`), so a far bush is the near bush's
 * own slot, species, height, width, yaw and colour, drawn coarse. Per slot the
 * walk asks, in order: the slot's own handover and outer edge (`fringeOf`,
 * `farShrubRank`), the community (`zoneOf`), the water (`wetAt`), the shrub
 * share and the weight walk off the slot's one draw (`dealt`), `station`, and
 * then `placeShrub`. Most slots carry nothing — the shrub share is a few per
 * cent of a community — but every one of them was walked on the pool and
 * asked its fringe, its rank, its community and its water on the page.
 *
 *   1. THE DEAL. The far shrub walk is one more point draw in the far pass's
 *      CARRY deal render (T-2896/T-2966, flora-gpu-carry.js): the same target
 *      (rows after the carries' slots, `uSlot0`), the same fence and read-back,
 *      so the same job. One point per FOUR slots (`FARSHRUB_PER_TEXEL`) runs
 *      LATTICE_GLSL and the deal below against the far shrubs' own SLOT FIELD
 *      (T-2967, flora-gpu-far.js `FAR_SLOT_GLSL`, `gpuNear.slotField(walk)`):
 *      one texel per lattice slot — a 2 x 2 block a forb cell, 1.7 m a texel,
 *      190 a side at `full` — holding the pool's answer AT THAT SLOT'S OWN
 *      POINT (community, WET, the floor as BLOCKED, TRODDEN), found by the
 *      slot's integer cell index and `k`. So the slot's class IS the CPU's
 *      answer there: no texel-centre difference to repair or measure around.
 *      The deal is the community, whether it records shrubs, the shrub share
 *      and the weight walk off the slot's draw, and the ground's half of
 *      `station` (a floor, a tall plant on the trodden verge, the water
 *      substrates), off `dealTable`'s forb section, where T-2895 already packs
 *      the shrubs: no new table. Each slot's WORD goes into one channel of one
 *      RGBA32F texel, in `nearWord`'s layout (code, WET, forb-section row + 1).
 *   2. THE REAP. flora.js reaps the part in slot order — `scatter`'s — after
 *      the carries, in the carry job's own reap (and so as a tail when the
 *      pass drains: below). For each slot the deal placed (code 6) or handed
 *      over (code 7) it does what the walk did: the slot's point recomputed in
 *      doubles from its cell and index (the `'wild'` jitter's two draws), the
 *      lattice ring and the pass's view cone, the slot's own HANDOVER
 *      (`fringeOf` on the forb ring's fringe) and OUTER EDGE (`farShrubRank`),
 *      the deal's draw `u` in doubles and the species dealt off it again
 *      (`dealt`); then the page's half of `station` — `growthBlocked`, and the
 *      woody band at `terrain.surfaceHeight` — and `placeShrub` on the slot's
 *      own stream past the jitter's two draws, with `patchOf` in doubles. A
 *      bush the GPU placed where the walk did is the same instance to the bit.
 *
 * WHAT STAYS ON THE PAGE, AND WHY.
 *
 *   - THE FRINGE AND THE RANK. Both hash `round(e * k)` (64 and 8 per metre),
 *     which a float32 `e` lands across a rounding half often enough to move a
 *     bush's edge by most of the fringe (flora-gpu-mid.js says why).
 *   - THE DRAW. `u` is float32 in the shader. A `u` within FARSHRUB_U_EPS of
 *     the share, or a weight walk's target that near a cumulative weight, is
 *     handed over (code 7); a placed slot's species is dealt again on the page
 *     in doubles, and one the doubles deal otherwise is dealt whole.
 *   - `growthBlocked` (the streets' track, the yards, the ground strip, the
 *     worked bank), which no field holds (`keeper({ page: false })`); the
 *     ground's height, never a texel's; the woody band (T-1056) at it.
 *   - A SLOT THE FIELD CANNOT ANSWER — its texel the pool could not ask (off
 *     the measured grid: `FAR_UNASKED`), or outside the tile — is code 7, and
 *     the page deals it whole with the walk's own code. The far pass deals on
 *     the GPU only where the uploaded field covers the walk (`covers`), so the
 *     second is a guard, not a path.
 *   - THE CAP AND THE ORDER. The far shrub set refuses past its cap; reaped in
 *     slot order it fills with the slots the walk filled it with.
 *
 * The far shrubs are not counted in the census (the detailed pass counts these
 * slots), so a slot that comes to nothing is passed over on its word alone.
 *
 * WHY THE CARRY JOB, AND NOT A READ-BACK OF ITS OWN. T-2966 first put the
 * carries on the GPU and was taken back out of PR #1161: a far pass DRAINED
 * late took its read-back in the frame and reaped all of it there (flora's
 * worst moving frame 73.3 ms against a 60 ms ceiling at `full`). Its second
 * cut (#1162) holds the worst frames: a pass resumed with DRAIN never waits on
 * the read-back and never reaps more than it has; what is left becomes the
 * carries' TAIL, which `carryTailStep` runs a slice of each frame inside
 * `flora.update`, counted against the frame's budget, with a NEXT for a pass
 * that lands while a tail holds the target and a landed pass's carries owed
 * until a newer one lands. The far shrubs are the same pass's other walk, so
 * they ride that job: one render, one fence, one read-back, one reap, landing
 * with the carries — never a second read-back scheme beside it (T-2967's
 * between-frames `farRun` is the NEAR pass's far band, in the mid render).
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** Slots a texel carries: one word in each of its four channels, so slot `id`
 *  of a part starting at texel `slot0` is element `4 * slot0 + id` of the
 *  read-back's Float32Array. The far shrubs need nothing else from the GPU —
 *  the point, the fringe and the instance are the page's — so the part is a
 *  quarter of a slot-per-texel one: 8 rows of 256 on the phone, 16 balanced,
 *  28 at `full`. */
export const FARSHRUB_PER_TEXEL = 4;

/** The draws a far shrub slot's stream has taken when its bush is placed: the
 *  `'wild'` jitter's two (`scatter`). `placeShrub` draws from the third on. */
export const FARSHRUB_STREAM_DRAWS = 2;

/** The shrub stratum's lattice salt (flora.js `rebuildFarShrubs`, and the forb
 *  ring's shrub walk: the same slots, K54's independent draw). */
export const FARSHRUB_SALT = 0x7b5c1d;

/** The code of a slot the page deals whole: T-2967's `FAR_DEAL.ask`. 1-6 are
 *  NEAR_DEAL's (flora-gpu-deal.js); 0 is "the lattice does not keep it". */
export const FARSHRUB_ASK = 7;

/** A `u` this near the shrub share, or a weight walk's target this near a
 *  cumulative weight (scaled by the subset's total), is handed to the page:
 *  T-2967's FAR_U_EPS. */
export const FARSHRUB_U_EPS = 1e-5;

/** How far past `scatter`'s ring the shader's lattice ring reaches, out and
 *  in, so a slot float32 puts a micron outside it is still dealt and the page
 *  decides: T-2967's FAR_LATTICE_PAD_M. */
export const FARSHRUB_LATTICE_PAD_M = 0.01;

/**
 * The far shrub walks, from flora.js's own numbers: the forb ring's cell and
 * slots (`TUNE.forb`), out to the far shrubs' radius, in from `inner` (flora.js
 * computes it off the forb ring's fade, fringe and the far step). `page` is
 * `scatter`'s, which the reap holds a slot to; `gpu` is the shader's, padded
 * by FARSHRUB_LATTICE_PAD_M, which the deal pass and the slot field are built
 * on (`latticeUniforms`, `gpuNear.slotField`).
 */
export function farShrubWalks({ cell, perCell, radius, inner }) {
  const page = { cell, perCell, radius, inner, salt: FARSHRUB_SALT, draw: 'wild' };
  const gpu = { ...page, radius: radius + FARSHRUB_LATTICE_PAD_M,
    inner: Math.max(0, inner - FARSHRUB_LATTICE_PAD_M) };
  return { page, gpu };
}

/** The texels the part takes for `count` slots, and the rows of a `width`-
 *  texel target they fill from a row's start. */
export function farShrubTexels(count, width) {
  const texels = Math.max(1, Math.ceil(count / FARSHRUB_PER_TEXEL));
  return { texels, rows: Math.ceil(texels / width) };
}

/**
 * The far shrub deal in GLSL, off DEAL_GLSL's table — its forb section
 * (`dealTable`'s `forbBase`, `forbItemBase`), the shrub half — given the
 * slot's class texel (`flFarClass`). Needs LATTICE_GLSL and DEAL_GLSL before
 * it; `unasked` is T-2967's FAR_UNASKED.
 *
 * Returns a code: none 1 (no community, or no shrubs recorded in it), undealt
 * 3, station 4 (a floor, a plant taller than the community's turf ceiling on
 * the trodden verge, or the species against the water refuses it), placed 6,
 * ask 7. `row` is the forb section's row from the deal on (-1 before it);
 * `wet` the slot's water bit.
 */
export function farShrubDealGlsl({ unasked }) {
  return /* glsl */ `
uniform ivec2 uForbLayout;
int flFarShrubDeal(uvec2 cls, float u, out int row, out bool wet) {
  row = -1;
  wet = false;
  if (cls.x == ${unasked}u) return 7;
  int z = int(cls.x) - 1;
  if (z < 0) return 1;
  int hz = uForbLayout.x + 6 * z;
  vec4 f0 = flDealT(hz), f1 = flDealT(hz + 1);
  // zone.shrubs.length
  if (f1.y < 0.5) return 1;
  uint flags = cls.y;
  wet = (flags & 1u) != 0u;
  // dealt(wet ? zone.wet.shrubs : zone.dry.shrubs,
  //       wet ? zone.shrubShareWet : zone.shrubShare, u)
  float share = wet ? f0.w : f0.z;
  vec4 side = flDealT(hz + 4 + (wet ? 1 : 0));
  int count = int(side.y);
  if (abs(u - share) < ${FARSHRUB_U_EPS}) return 7;
  if (!(share > 0.0) || u >= share || count == 0) return 3;
  float target = (u / share) * side.z;
  float eps = ${FARSHRUB_U_EPS} * max(side.z, 1e-6);
  int first = int(side.x);
  float acc = 0.0;
  row = int(flDealT(first + count - 1).y);
  for (int i = 0; i < count; i++) {
    vec4 ent = flDealT(first + i);
    acc += ent.x;
    if (abs(target - acc) < eps) { row = -1; return 7; }
    if (target <= acc) { row = int(ent.y); break; }
  }
  // station, the ground's half, at the slot's own point: a floor (the
  // worker's floors: no growthBlocked here), the trodden verge against the
  // species' own height, the water substrates.
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
}

/**
 * The far shrub deal pass's two shaders (GLSL ES 3.00, for a RawShaderMaterial),
 * given the chunks they stand on: `lattice`, `field` and `deal` as the other
 * deal passes take them (FIELD_GLSL only because DEAL_GLSL's near deal reads
 * it; nothing here samples it, so its uniforms go unset), `slot`
 * flora-gpu-far.js FAR_SLOT_GLSL (`flFarClass` and its four uniforms) and
 * `unasked` its FAR_UNASKED. Its own uniforms: `uTarget` (the carry target's
 * size, shared), `uSlot0` (the first TEXEL this part writes) and `uSlots` (the
 * slots dealt, `latticeUniforms().count` held to the part's room). One point
 * per texel, four slots to a point: texel `uSlot0 + t` holds slots 4t .. 4t+3
 * in r, g, b, a, each slot's word 0 where the lattice does not keep it.
 */
export function farShrubPassShaders({ lattice, field, deal, slot, unasked }) {
  if (!slot || !Number.isInteger(unasked)) {
    throw new Error('flora-gpu-farshrub: needs the slot field\'s lookup and its unasked class');
  }
  const vertexShader = /* glsl */ `precision highp float; precision highp int;
precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
uniform int uSlot0;
uniform int uSlots;
${lattice}
${field}
${deal}
${slot}
${farShrubDealGlsl({ unasked })}
flat out vec4 v0;
void main() {
  float words[4];
  for (int c = 0; c < 4; c++) words[c] = 0.0;
  for (int c = 0; c < 4; c++) {
    int id = 4 * gl_VertexID + c;
    if (id >= uSlots) break;
    vec2 rel; float u; uint rng; uint cellSeed;
    if (!flLatticeSlot(id, rel, u, rng, cellSeed)) continue;
    uvec2 cls;
    int row = -1; bool wet = false;
    // Outside the slot field's tile: the page deals it whole.
    int code = flFarClass(id, cls) ? flFarShrubDeal(cls, u, row, wet) : ${FARSHRUB_ASK};
    if (code == ${FARSHRUB_ASK}) { row = -1; wet = false; }
    words[c] = float(code | (wet ? 8 : 0) | ((row + 1) << 4));
  }
  v0 = vec4(words[0], words[1], words[2], words[3]);
  int t = uSlot0 + gl_VertexID;
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
