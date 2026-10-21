/**
 * The near pass's FAR BAND on the GPU's deal (T-2967, the second slice of
 * T-2896: the far shrubs, the carry sets and the far band on the GPU's deal).
 *
 * WHAT MOVES. `rebuildFar` in flora.js deals the sward past the detailed rings
 * on every near pass: three lattices (`TUNE.far.bands`, the sparse `'lattice'`
 * draw, one slot a cell), out to 120 m on the phone, 150 m balanced and 175 m
 * at `full`, each slot asked its community, short turf, the far split (T-1106:
 * whether this card stands for the grass or the flowers), the species off the
 * slot's one draw, and `station`. Since T-2894 and T-2895 the near pass's
 * other walks are dealt in GLSL against the MID FIELD; the far band was the
 * near pass's largest remaining walk. This is the same shape for it:
 *
 *   1. THE DEAL. One more point draw per band goes into the mid deal pass's own
 *      render — its target (rows after the forb and shrub walks, `uSlot0`), no
 *      render-target bind or read-back of its own — against that band's FAR
 *      FIELD (below). Each slot runs LATTICE_GLSL and the deal below and writes
 *      `(e, 0, -n, word)` (`farWord`): what it came to, its water bit, whether
 *      it stands for a forb, and its row.
 *   2. THE REAP. flora.js `farRun` walks the target in slot order and does the
 *      rest on the page, in doubles — see below — and places the card
 *      (`placeFarCard`) and its head on the slot's own stream past the jitter's
 *      two draws. It is spread over tasks between frames (never inside
 *      `flora.update`, and never all at once with a pass drained in one frame:
 *      T-2966's worst frames were exactly that), into a staging list the far
 *      set is filled from only when the whole band is reaped.
 *
 * THE FAR FIELD IS A SLOT FIELD, AND ITS TEXEL IS THE LATTICE'S CELL. A far
 * slot is the only point a far band ever asks the ground about, and the far
 * lattices are world-anchored: the same cell holds the same slot, at the same
 * jittered point, from wherever it is dealt. So the far field keeps ONE TEXEL
 * PER LATTICE SLOT — texel (c, r) of a band is cell (c, r) of its lattice, its
 * size the band's cell (3.9, 11 and 3.8 m on the phone; 3.4, 9.5 and 2.3 at
 * `full`) — holding the pool's answer AT THAT SLOT'S OWN POINT (jobs/
 * zone-kernel.js `slotPoint`, `scatter`'s jitter to the bit): its community,
 * WET, TURF, the floor (BLOCKED) and TRODDEN. The shader finds its slot's
 * texel by the cell's integer index (`flFarClass`), with no float position in
 * the lookup, so a slot's class IS the CPU's answer at that slot: the tile-
 * class difference is zero by construction, and `tools/measure_far_field.mjs`
 * holds it at zero. A band's tile is 28 to 94 texels a side (`farSlotSpec`),
 * and the three together 3,104 texels on the phone, 6,424 balanced and 13,272
 * at `full`: 6.2, 12.8 and 26.5 KB of class on the GPU (`farSlotBytes`; three
 * times that on the page, with the keeper's unused height array).
 *
 * WHY NOT A TEXEL-CENTRE FIELD. The first cut was a plain near-field.js tile
 * on a 1 m texel over the band's reach (`farFieldSpec`, 280-392 texels a
 * side, 0.47-0.92 MB on the page and as much again uploaded), each slot asked
 * at its texel's centre, with an eight-texel edge test sending a slot near a
 * boundary back to the page. Measured over the 1835 scene's 18 anchors and the
 * four critic poses (`measure_far_field.mjs`, docs/measurements/t-2967-far-
 * field.json), a far slot's community differed from its texel centre's at
 * 3.6-4.0 % of slots at 1 m (3.1-3.4 % at 0.5 m, 5.4-5.6 % at 2 m), the edge
 * test handed 17.5-18.5 % of slots back to the page, and 0.31-0.46 % of the
 * slots a card can stand on still differed past it (0.08-0.13 % at 0.5 m, for
 * four times the bytes). The cause is zone-blend.js
 * (T-2125): across a ~100 m band at every community's edge, membership is
 * dithered per plant on a 0.5 m grain, so the community is noise below a
 * metre and no texel centre answers for a point half a metre away. Only the
 * slot's own point does — and the far band has a few thousand of them.
 *
 * WHAT THE PAGE STILL ASKS. For the slots the GPU placed: the slot's point in
 * doubles, its band rank (`farRank` hashes `round(e * 8)`, which a float32
 * point lands across a rounding half about one slot in a few hundred) and its
 * ring, the view cone, the deal's one draw `u` in doubles (a placed slot whose
 * species the doubles do not give is dealt whole), `growthBlocked` (the
 * page's: the streets' track, the yards, the ground strip, the worked bank),
 * the ground's height (`terrain.surfaceHeight`, or the water's) and the woody
 * band. A slot whose texel the pool could not answer (off the measured grid:
 * `FAR_UNASKED`), or outside its band's tile, comes back `FAR_DEAL.ask` and
 * the page deals it whole with the CPU's own code (`farSlot`).
 *
 * THE SHADER'S CULLS ARE CONSERVATIVE. The GPU drops a slot before the deal
 * only where the answer cannot be the page's: its rank is past the band's keep
 * (and `e * 8`, `n * 8` are not near a half), it stands outside its own ring or
 * the view cone by more than FAR_MARGIN_M, or the lattice's ring, which it is
 * given FAR_LATTICE_PAD_M wider than `scatter`'s. A `u` within FAR_U_EPS of a
 * threshold of the deal (the far split, the share, a species' cumulative
 * weight) is answered `ask`. So every slot the CPU walk would place reaches the
 * page, and the page decides.
 *
 * FOR T-2968 (the far shrubs). The same machinery keeps a slot field for any
 * lattice whose `perCell` is a square (`sub * sub` texels a cell, slot k at
 * `(c * sub + k % sub, r * sub + k / sub)`), the `wild` draw included: the
 * far shrubs' walk (the forb cell, four a cell, `wild`) is a 2 x 2 texel block
 * a cell. flora.js `gpuNear.slotField(walk)` builds one.
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** A far slot's code: NEAR_DEAL's (none 1, turf 2, undealt 3, station 4,
 *  placed 6), and `ask` — the page deals the slot whole. */
export const FAR_DEAL = Object.freeze({ none: 1, turf: 2, undealt: 3, station: 4, placed: 6, ask: 7 });

/** The class texel's community where the pool did not answer it. */
export const FAR_UNASKED = 255;

/** How far past `scatter`'s lattice ring the shader's ring reaches, so a slot
 *  float32 puts a micron outside it is still dealt, and the page decides. */
export const FAR_LATTICE_PAD_M = 0.01;
/** The shader drops a slot outside its band ring or the view cone only by more
 *  than this: float32 at 2 km is a tenth of a millimetre. */
export const FAR_MARGIN_M = 0.05;
/** A `u` this near a threshold of the deal is answered `ask`. */
export const FAR_U_EPS = 1e-5;

/** The draws a far slot's stream has taken when its card is placed: the
 *  jitter's two (`scatter`). `placeFarCard` draws from the third on. */
export const FAR_STREAM_DRAWS = 2;

/**
 * A far band's SLOT FIELD spec, for a lattice walk `{cell, perCell, radius}`
 * (the band's, with the near step and the shader's pad in its radius): one
 * texel per slot, so a texel of `cell / sub` where `perCell = sub²`, re-centred
 * on a whole number of texels near `recentre` metres, and wide enough that
 * every cell the walk visits — every cell whose square meets the ring, so a
 * cell past the radius — is in the tile from anywhere in the re-centre cell,
 * with `inHand` metres to spare for a strip still on the pool. An even size,
 * so the origin (the re-centre step's multiple less half the span) is a whole
 * texel, and texel `i` of a tile at `e0` is world texel `e0 / texel + i`.
 */
export function farSlotSpec({ cell, perCell, radius }, { recentre = 16, inHand = 8 } = {}) {
  const sub = Math.round(Math.sqrt(perCell));
  if (sub * sub !== perCell) throw new Error(`a slot field needs a square perCell, not ${perCell}`);
  const texel = cell / sub;
  const step = texel * Math.max(1, Math.ceil(recentre / texel - 1e-9));
  const half = radius + cell + step / 2 + inHand;
  const size = 2 * Math.ceil(half / texel);
  return Object.freeze({ texel, size, recentre: step, sub, cell });
}

/** How far around a camera a slot field's tile must reach to hold every cell
 *  its walk visits (`covers`): the radius and one cell. */
export function farSlotReach({ cell, radius }) {
  return radius + cell;
}

/** The bytes a slot field of `spec` holds: two class bytes a texel on the GPU
 *  (RG8UI), and on the page the keeper's class bytes and its four-byte height
 *  (which a slot field never fills or uploads). */
export function farSlotBytes(spec) {
  const texels = spec.size * spec.size;
  return { gpu: texels * 2, page: texels * 6, texels };
}

/**
 * The TEXEL-CENTRE far field the slot field replaced (see the header), kept for
 * `measure_far_field.mjs`, which reads it as the argument: a plain near-field
 * tile of `texel` metres over a band's `reach`, re-centred every 16 m, with a
 * texel ring past the lattice for the eight-texel edge test.
 */
export function farFieldSpec(reach, { texel = 1, recentre = 16, inHand = 8 } = {}) {
  const half = reach + 1.5 * texel + recentre / 2 + inHand;
  const size = Math.ceil((2 * half) / texel / 8) * 8;
  return Object.freeze({ texel, size, recentre });
}

/** Its bytes on each side: two class bytes and four height bytes a texel. */
export function farFieldBytes(spec) {
  return spec.size * spec.size * 6;
}

/**
 * T-2967. A far slot's WORD, the target's fourth channel: its code, the water
 * bit, whether the far split made it a forb, and its row plus one — of the
 * deal table's graminoid rows (`items`) or, for a forb, of its forb section
 * (`forbItems`). `code | wet << 3 | forb << 4 | (row + 1) << 5`, an integer a
 * float32 carries exactly.
 */
export function farWord(w) {
  const x = w | 0;
  return { code: x & 7, wet: (x & 8) !== 0, forb: (x & 16) !== 0, row: (x >> 5) - 1 };
}

/**
 * The slot field's lookup (GLSL ES 3.00), after LATTICE_GLSL. Its uniforms:
 * `uFarClass` (RG8UI: community 1-based, 0 none, FAR_UNASKED; FIELD_FLAGS),
 * `uFarIdx0` (the tile's origin in world texel indices, `e0 / texel`),
 * `uFarSize` (texels a side) and `uFarWrap` (near-field.js `fieldWrap`: where
 * the tile's local texel 0 is kept). `flFarClass(id, cls)` is the class of the
 * walk's slot `id`, found by its cell's integer index and its `k` — the texel
 * `(c * sub + k % sub, r * sub + k / sub)` — and false where the tile does
 * not hold it.
 */
export const FAR_SLOT_GLSL = /* glsl */ `
uniform highp usampler2D uFarClass;
uniform ivec2 uFarIdx0;
uniform int uFarSize;
uniform ivec2 uFarWrap;

bool flFarClass(int id, out uvec2 cls) {
  int perCell = uLatGrid.w;
  int k = id % perCell;
  int cellIdx = id / perCell;
  int sub = int(uLatDeal.x);
  int c = uLatGrid.x + cellIdx % uLatGrid.z;
  int r = uLatGrid.y + cellIdx / uLatGrid.z;
  ivec2 t = ivec2(c * sub + k % sub, r * sub + k / sub) - uFarIdx0;
  cls = uvec2(0u);
  if (t.x < 0 || t.y < 0 || t.x >= uFarSize || t.y >= uFarSize) return false;
  cls = texelFetch(uFarClass, (t + uFarWrap) % uFarSize, 0).rg;
  return true;
}
`;

/**
 * The far deal in GLSL: `rebuildFar`'s per-slot questions from the community
 * on, off DEAL_GLSL's table — its graminoid section, its forb section (T-2895)
 * and its far section (`dealTable`'s `farBase`: each community's far split,
 * dry and wet) — given the slot's class texel (`flFarClass`). Needs
 * LATTICE_GLSL and DEAL_GLSL before it. Returns a FAR_DEAL code; `row` is the
 * dealt row (-1 before the deal), `forb` whether it is a forb row, `wet` the
 * slot's water bit.
 *
 * The ground's half of `station` is the floor (BLOCKED, the worker's floors
 * only: this field holds no `growthBlocked`) and the water substrates; the
 * trodden verge never binds here (it crops only a turf community's plants, and
 * the far band deals nothing on turf), and the woody band and the height are
 * the page's.
 */
export const FAR_DEAL_GLSL = /* glsl */ `
uniform ivec2 uForbLayout;
uniform int uFarBase;

bool flNearU(float a, float b) { return abs(a - b) < ${FAR_U_EPS}; }

int flFarPick(vec4 side, float uu, float share, out int row) {
  int count = int(side.y);
  row = -1;
  if (!(share > 0.0) || uu >= share || count == 0) return flNearU(uu, share) ? 7 : 3;
  float target = (uu / share) * side.z;
  int first = int(side.x);
  float acc = 0.0;
  float eps = ${FAR_U_EPS} * max(side.z, 1e-6);
  row = int(flDealT(first + count - 1).y);
  for (int i = 0; i < count; i++) {
    vec4 ent = flDealT(first + i);
    acc += ent.x;
    if (abs(target - acc) < eps) return 7;
    if (target <= acc) { row = int(ent.y); break; }
  }
  return 6;
}

int flFarDeal(uvec2 cls, float u, out int row, out bool forb, out bool wet) {
  row = -1;
  forb = false;
  wet = false;
  if (cls.x == ${FAR_UNASKED}u) return 7;
  int z = int(cls.x) - 1;
  vec4 z0 = z >= 0 ? flDealT(4 * z) : vec4(0.0);
  vec4 z1 = z >= 0 ? flDealT(4 * z + 1) : vec4(0.0);
  if (z < 0 || z1.w < 0.5) return 1;
  if (z0.w > 0.5) return 2;
  uint flags = cls.y;
  wet = (flags & 1u) != 0u;
  vec4 fz = flDealT(uFarBase + z);
  float split = wet ? fz.y : fz.x;
  if (flNearU(u, split)) return 7;
  forb = u >= split;
  int code = forb
    ? flFarPick(flDealT(uForbLayout.x + 6 * z + 2 + (wet ? 1 : 0)), u - split, z0.x - split, row)
    : flFarPick(flDealT(4 * z + (wet ? 3 : 2)), u, split, row);
  if (code != 6) return code;
  // station, the ground's half: a floor, the water substrates.
  if ((flags & 4u) != 0u) return 4;
  float substrate = forb ? flDealT(uForbLayout.y + 2 * row + 1).x
    : flDealT(uDealLayout.y + 5 * row + 2).w;
  if (wet) {
    if (!(z0.z > 0.5 && substrate >= 2.0)) return 4;
  } else if (substrate == 3.0) return 4;
  return 6;
}
`;

/**
 * The far deal pass's two shaders (GLSL ES 3.00, for a RawShaderMaterial),
 * given the chunks they stand on — `ring` is flora-gpu-near.js NEAR_RING_GLSL,
 * for its `flSlotWorld`, and `field` FIELD_GLSL, which it declares against.
 * Its own uniforms: `uTarget` (the mid target's size, shared), `uSlot0` (the
 * first texel this band writes), `uFarBand` (radius, ramp, inner, innerRamp),
 * `uFarKeep` (the band's keep, the near step), `uFarSalt` (the band rank's
 * salt), `uFarCam` (camera east, north), `uFarCone` (forward east, north, the
 * cone's cosine, its margin; a cosine below -1 is no cone), and FAR_SLOT_GLSL's
 * four. One texel per slot: world east, 0, world z (= -north), and the slot's
 * word — zero where the lattice does not keep the slot or the shader's culls
 * drop it.
 */
export function farPassShaders({ lattice, field, deal, ring }) {
  const vertexShader = /* glsl */ `precision highp float; precision highp int;
precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
uniform int uSlot0;
uniform vec4 uFarBand;
uniform vec2 uFarKeep;
uniform uint uFarSalt;
uniform vec2 uFarCam;
uniform vec4 uFarCone;
${lattice}
${field}
${deal}
${ring}
${FAR_SLOT_GLSL}
${FAR_DEAL_GLSL}
flat out vec4 v0;
// Whether x * 8 lands near a rounding half, where float32 and a double can
// round it to different integers (and so hash a different rank).
bool flHalfish(float x) { float f = fract(x * 8.0); return abs(f - 0.5) < 0.05; }
void main() {
  int id = gl_VertexID;
  v0 = vec4(0.0);
  vec2 rel; float u; uint rng; uint cellSeed;
  if (flLatticeSlot(id, rel, u, rng, cellSeed)) {
    vec2 en = flSlotWorld(id, cellSeed);
    vec2 d2 = en - uFarCam;
    float r = length(d2);
    bool keep = true;
    // The view cone, with the margin scatter gives it and FAR_MARGIN_M more.
    if (keep && uFarCone.z >= -1.0 && r > 3.5
        && dot(d2, uFarCone.xy) < r * uFarCone.z - 2.0 * uFarCone.w - ${FAR_MARGIN_M}) keep = false;
    // The band's own rank and ring, where float32 cannot have rounded the rank.
    if (keep && !flHalfish(en.x) && !flHalfish(en.y)) {
      float rank = flUnit(flHash3(uint(flRoundI(en.x * 8.0)), uint(flRoundI(en.y * 8.0)), uFarSalt))
        / uFarKeep.x;
      if (rank >= 1.0 + 1e-4) keep = false;
      else {
        float outer = uFarBand.x - uFarBand.y * rank;
        float inner = uFarBand.z + uFarBand.w * rank;
        if (r > outer + uFarKeep.y + ${FAR_MARGIN_M} || r < inner - uFarKeep.y - ${FAR_MARGIN_M}) keep = false;
      }
    }
    if (keep) {
      int row; bool forb; bool wet;
      uvec2 cls;
      // Outside the band's tile: the page deals it whole.
      int code = flFarClass(id, cls) ? flFarDeal(cls, u, row, forb, wet) : 7;
      if (code == 7) { row = -1; forb = false; wet = false; }
      v0 = vec4(en.x, 0.0, -en.y,
        float(code | (wet ? 8 : 0) | (forb ? 16 : 0) | ((row + 1) << 5)));
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
