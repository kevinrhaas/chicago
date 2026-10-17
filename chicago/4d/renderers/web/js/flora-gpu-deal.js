/**
 * flora.js's near deal as GLSL: what one near slot comes to, computed in a
 * shader from the slot alone (T-2706, the first piece of T-2699 under T-2557's
 * GPU-procedural near grass).
 *
 * T-2697 put the lattice walk in a shader (`flora-gpu-lattice.js`: which slot an
 * instance is, where its jitter puts it, its deal rank `u` and the xorshift
 * stream its placement draws from) and T-2698 put the ground's answers in a tile
 * (`near-field.js`: community, WET · TURF · BLOCKED · TRODDEN, and height). This
 * is the rule between them — `dealNearSlot` in flora.js, which the draw and the
 * read-back both call:
 *
 *   1. the community the slot stands in, and none or no graminoids: nothing;
 *   2. short turf: nothing (T-2122);
 *   3. the matrix share and the weight walk off the slot's ONE draw `u`
 *      (`dealt` and `pick`, K49(d)), from the dry or the wet half of the
 *      community as the WET bit says;
 *   4. `station`: a dated travelway or a floor (BLOCKED), a plant taller than
 *      a turf community's ceiling on the trodden verge (TRODDEN against the
 *      species' own height), the water substrates (only a non-soil species of a
 *      community that stands in water roots in it, at the water's surface; a
 *      floating leaf has no station on dry ground), and the woody band
 *      (T-1056: a smoothstep over the zone record's `establishes_m` and a
 *      positional hash);
 *   5. `crowdsTheWalker`: a plant whose clump overlaps the walker's shoulders;
 *   6. `placeGraminoid`: height off the stand's vigour and one draw, spread,
 *      the two greens and the tonal jitter under the patch field and the
 *      vigour's tone, the thatch minority, yaw and arch — seven draws, in the
 *      CPU's order, off the slot's own stream.
 *
 * THE TABLE. Every community's header, its two graminoid subsets as (weight,
 * row) entries and one row per graminoid are packed by `dealTable` into one
 * RGBA32F texture the shader reads with `texelFetch`:
 *
 *   zone z header, texels 4z .. 4z+3:
 *     matrixShare, turfCeiling (0 = none), standsInWater, turf
 *     woody low, woody high, has woody band, has graminoids
 *     dry entries' first texel, count, total, 0
 *     wet entries' first texel, count, total, 0
 *   a subset entry, one texel: weight, row, 0, 0
 *   a graminoid row, DEAL_ROW texels from `itemBase + DEAL_ROW * row`:
 *     weight, height low, height high, confidence
 *     clump width (mid of width_m, or -1), shape spread, shape arch, clump radius
 *     base rgb, substrate (SUBSTRATE)
 *     alt rgb, woody role here (0/1)
 *     dry rgb, 0
 *
 * A row is per community, not per species: the woody band binds a ROLE in one
 * community's record, so the same plant can be bound in one zone and free in
 * the next.
 *
 * PRECISION, stated rather than hoped for (as T-2697 does). The integer hashes
 * are the CPU's to the bit. The float arithmetic is float32 against flora.js's
 * doubles, so a comparison that lands within an ulp of its threshold — `u`
 * against the share, the weight walk's target against a boundary, the thatch
 * draw against its chance, the walker's clearance, the woody hash against its
 * ramp — can go the other way. `tools/measure_flora_gpu_deal.mjs` counts those
 * apart from a disagreement in the rule, and from the slots where the TILE
 * answers differently from the CPU (T-2698's 1 %), which this module inherits
 * and cannot repair.
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** What a near slot came to: `dealNearSlot`'s answer, and the shader's.
 *  0 is the shader's own "the ring does not keep this slot". */
export const NEAR_DEAL = Object.freeze({
  none: 1, turf: 2, undealt: 3, station: 4, walker: 5, placed: 6,
});

/** A species' recorded `substrate`, as the station test reads it. */
export const SUBSTRATE = Object.freeze({ unrecorded: 0, soil: 1, wet: 2, open_water: 3 });

/** Texels a graminoid row takes. */
export const DEAL_ROW = 5;
/** The table texture's width in texels. */
export const DEAL_WIDTH = 256;
/** `nearField.deal`'s numbers a slot: e, n, u, code, row, y, yaw, height,
 *  spread, arch, r, g, b, confidence, the thatch draw. */
export const DEAL_STRIDE = 15;

/** flora.js's constants, by the values it uses (WALKER_RADIUS_M, the vnoise,
 *  woody and verge salts). */
const WALKER_RADIUS_M = 0.34;

function substrateOf(sp) {
  if (!sp.substrate) return SUBSTRATE.unrecorded;
  if (sp.substrate === 'soil') return SUBSTRATE.soil;
  return sp.substrate === 'open_water' ? SUBSTRATE.open_water : SUBSTRATE.wet;
}
function mid(range) { return (range[0] + range[1]) / 2; }
/** flora.js `clumpRadiusOf`. */
function clumpRadiusOf(sp) {
  return sp.width ? mid(sp.width) * 0.5 : Math.min(0.35, mid(sp.height) * 0.16);
}

/**
 * Pack flora.js's compiled communities (in `communities()` order, so the field
 * tile's class R channel, index + 1, finds its header) into the table.
 *
 * @returns {{data: Float32Array, width: number, height: number,
 *   entryBase: number, itemBase: number, rows: number,
 *   rowOf: (zone: number, sp: object) => number, species: string[]}}
 *   `rowOf(z, sp)` is the row of community z's record `sp` (-1 if none);
 *   `species[row]` is that row's species id.
 */
export function dealTable(zones) {
  const entryBase = zones.length * 4;
  const entries = [];
  const items = [];
  const rowMaps = zones.map(() => new Map());
  const headers = zones.map((z, zi) => {
    for (const sp of z.graminoids) {
      rowMaps[zi].set(sp, items.length);
      items.push({ z, sp });
    }
    const side = (subset) => {
      const first = entryBase + entries.length;
      for (const sp of subset.items) entries.push([sp.weight, rowMaps[zi].get(sp)]);
      return [first, subset.items.length, subset.total, 0];
    };
    const w = z.woody;
    return [
      [z.matrixShare, z.turfCeiling || 0, z.standsInWater ? 1 : 0, z.turf ? 1 : 0],
      [w ? w.establishes[0] : 0, w ? w.establishes[1] : 0, w ? 1 : 0, z.graminoids.length ? 1 : 0],
      side(z.dry.graminoids),
      side(z.wet.graminoids),
    ];
  });
  const itemBase = entryBase + entries.length;
  const texels = itemBase + items.length * DEAL_ROW;
  const height = Math.max(1, Math.ceil(texels / DEAL_WIDTH));
  const data = new Float32Array(DEAL_WIDTH * height * 4);
  const put = (t, v) => { for (let k = 0; k < 4; k++) data[4 * t + k] = v[k] ?? 0; };
  headers.forEach((h, zi) => h.forEach((v, k) => put(4 * zi + k, v)));
  entries.forEach((v, k) => put(entryBase + k, v));
  items.forEach(({ z, sp }, row) => {
    const t = itemBase + DEAL_ROW * row;
    put(t, [sp.weight, sp.height[0], sp.height[1], sp.conf]);
    put(t + 1, [sp.width ? mid(sp.width) : -1, sp.shape?.spread ?? 0, sp.shape?.arch ?? 0,
      clumpRadiusOf(sp)]);
    put(t + 2, [...sp.base, substrateOf(sp)]);
    put(t + 3, [...sp.alt, z.woody?.roles.has(sp.role) ? 1 : 0]);
    put(t + 4, [...sp.dry, 0]);
  });
  return {
    data, width: DEAL_WIDTH, height, entryBase, itemBase, rows: items.length,
    rowOf: (zi, sp) => rowMaps[zi]?.get(sp) ?? -1,
    species: items.map(({ sp }) => sp.id),
  };
}

/**
 * The GLSL ES 3.00 text. It needs `LATTICE_GLSL` (flHash3, flXorshift) and
 * `FIELD_GLSL` (fieldClass, fieldHeight) included before it. Uniforms:
 *
 *   uDealTable  sampler2D  `dealTable`'s texture, RGBA32F, nearest
 *   uDealLayout ivec2      its width; its itemBase
 *   uDealCam    vec2       the camera east and north, metres (the slot's `rel`
 *                          is from it)
 *   uDealEye    vec3       the water's surface; 1 when the eye flies (the
 *                          cone's `planes`), else 0; the eye's height
 *
 * `flNearDeal(rel, r, u, rng, …)` returns a NEAR_DEAL code; when it is
 * `placed`, `ground` is (e, y, n) and `flora` (height, spread, arch, yaw) and
 * `colour` (r, g, b, confidence) are the instance's, as `placeGraminoid` pushes
 * them. `row` is the dealt row (-1 before the deal), and `vig` the stand's
 * vigour, which the read-back uses to find a thatch draw at its threshold.
 */
export const DEAL_GLSL = /* glsl */ `
uniform highp sampler2D uDealTable;
uniform ivec2 uDealLayout;
uniform vec2 uDealCam;
uniform vec3 uDealEye;

vec4 flDealT(int i) {
  return texelFetch(uDealTable, ivec2(i % uDealLayout.x, i / uDealLayout.x), 0);
}
float flUnit(uint s) { return float(s) / 4294967296.0; }
float flDraw(inout uint s) { s = flXorshift(s); return flUnit(s); }
float flVnoiseHash(int a, int b) {
  return float(flHash3(uint(a), uint(b), 0x2f1cu) & 0xffffu) / 65535.0;
}
// flora.js vnoise.
float flVnoise(float x, float z) {
  float xf = floor(x), zf = floor(z);
  int xi = int(xf), zi = int(zf);
  float fx = x - xf, fz = z - zf;
  float sx = fx * fx * (3.0 - 2.0 * fx);
  float sz = fz * fz * (3.0 - 2.0 * fz);
  float a0 = flVnoiseHash(xi, zi) * (1.0 - sx) + flVnoiseHash(xi + 1, zi) * sx;
  float a1 = flVnoiseHash(xi, zi + 1) * (1.0 - sx) + flVnoiseHash(xi + 1, zi + 1) * sx;
  return a0 * (1.0 - sz) + a1 * sz;
}
// vigourOf, patchOf, smoothstep (flora.js's, which guards hi <= lo; a woody
// band reaching the table has already been held to a rising one).
float flVigour(vec2 en) {
  return 0.62 * flVnoise(en.x * 0.36 + 3.1, en.y * 0.36 - 7.7)
       + 0.38 * flVnoise(en.x * 0.72 - 2.4, en.y * 0.72 + 1.9);
}
float flPatch(vec2 en) {
  return 0.66 + 0.72 * flVnoise(en.x * 0.21 + 5.5, en.y * 0.21 - 2.3)
    * (0.72 + 0.42 * flVnoise(en.x * 0.74 - 1.1, en.y * 0.74 + 6.2));
}
float flRamp(float lo, float hi, float x) {
  float t = clamp((x - lo) / (hi - lo), 0.0, 1.0);
  return t * t * (3.0 - 2.0 * t);
}
int flRoundI(float x) { return int(floor(x + 0.5)); }

int flNearDeal(vec2 rel, float r, float u, uint rng, out int row, out float vig,
    out vec3 ground, out vec4 flora, out vec4 colour) {
  row = -1;
  vig = 0.0;
  vec2 en = uDealCam + rel;
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
  // pick(subset, u / share): the CDF walk, the last entry when rounding
  // leaves the target past the total.
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
  vec4 i0 = flDealT(it), i1 = flDealT(it + 1), i2 = flDealT(it + 2);
  vec4 i3 = flDealT(it + 3), i4 = flDealT(it + 4);
  // station: floors and travelways, the trodden verge, water, the woody band.
  if ((flags & 4u) != 0u) return 4;
  if (z0.y > 0.0 && i0.z > z0.y && (flags & 8u) != 0u) return 4;
  float y;
  if (wet) {
    if (!(z0.z > 0.5 && i2.w >= 2.0)) return 4;
    y = uDealEye.x;
  } else {
    if (i2.w == 3.0) return 4;
    y = fieldHeight(en);
    if (z1.z > 0.5 && i3.w > 0.5) {
      float t = flRamp(z1.x, z1.y, y);
      if (t <= 0.0) return 4;
      if (t < 1.0 && flUnit(flHash3(uint(flRoundI(en.x * 4.0)), uint(flRoundI(en.y * 4.0)),
          0x5ad8a1u)) >= t) return 4;
    }
  }
  // crowdsTheWalker
  float eyeAbove = uDealEye.y > 0.5 ? uDealEye.z - y : 0.0;
  if (!(eyeAbove > i0.z * 1.25 + ${WALKER_RADIUS_M}) && r < ${WALKER_RADIUS_M} + i1.w) return 5;
  // placeGraminoid, its seven draws in the CPU's order.
  uint s = rng;
  vig = flVigour(en);
  float uh = flDraw(s) * 0.35 + vig * 0.65;
  float h = i0.y + (i0.z - i0.y) * uh;
  float spread = (i1.x >= 0.0 ? i1.x : h * i1.y) * (0.78 + flDraw(s) * 0.5);
  float tone = flPatch(en) * (0.86 + 0.28 * (1.0 - vig));
  float tu = flDraw(s);
  float tv = flDraw(s);
  float tt = tu * tu;
  vec3 c = (i2.rgb * (1.0 - tt) + i3.rgb * tt) * (0.82 + tv * 0.40) * tone;
  bool dry = flDraw(s) < 0.14 * (1.0 - vig);
  vec3 col = dry ? c * 0.6 + i4.rgb * vec3(0.5, 0.45, 0.5) : c;
  float yaw = flDraw(s) * 6.283185307179586;
  float arch = i1.z * (0.7 + flDraw(s) * 0.7);
  ground = vec3(en.x, y, en.y);
  flora = vec4(h, spread, arch, yaw);
  colour = vec4(col, i0.w);
  return 6;
}
`;
