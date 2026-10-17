/**
 * near-field.js — T-2698, the near deal's FIELD as textures: the five things the
 * near ring's deal asks of the ground at every slot, rasterised into one
 * world-anchored tile a vertex shader can sample instead of asking the CPU.
 *
 * WHY. T-2557 moves the near ring's grass into the vertex shader: each instance
 * finds its own slot from `gl_InstanceID` and the lattice hash (T-2697), and
 * then has to answer, with no CPU in the loop, the questions `flora.js` asks of
 * every near slot today — which community stands here (`finder`), is it water
 * (`water.isWater`), is it short turf (`zone.turf`, where the near ring plants
 * nothing), may anything root here (`station`'s floors and travelways, and the
 * verge a turf community's tall plants give way on), and how high is the ground
 * (`terrain.surfaceHeight`). This module is those answers as a raster.
 *
 * WHAT IS IN A TEXEL, and what is NOT. A texel holds the CPU's own answer at
 * its CENTRE, asked through the same closures the deal asks (`flora.js`'s
 * `nearField.at`), so nothing here re-derives a rule; the only thing the tile
 * changes is WHERE the question is asked — at the texel's centre rather than at
 * the slot. That is the whole of the disagreement `tools/measure_near_field.mjs`
 * quotes, slot by slot. The species-dependent halves of `station()` are not in
 * the tile and cannot be: the substrate test is the wet bit plus the species'
 * own record, the woody band is the height channel against the zone record's
 * `woody_stratum`, and the trodden verge is the TRODDEN bit against the
 * species' height and the zone's `turfCeiling` — all three a lookup the shader
 * makes per species, not per texel.
 *
 *   class texture (RG8UI, texelFetch, nearest):
 *     R  community: index into `flora.communities()` plus one; 0 = no zone
 *     G  flags: WET · TURF · BLOCKED · TRODDEN (see FIELD_FLAGS)
 *   height texture (R32F, texelFetch four times, bilinear between centres):
 *     R  terrain.surfaceHeight at the texel centre, metres
 *
 * WORLD-ANCHORED. The tile's origin is a multiple of its own re-centre step, so
 * a texel centre is a fixed point of the world and two walkers standing a metre
 * apart sample the same texel for the same slot. It is rebuilt only when the
 * camera's snapped origin moves — every `recentre` metres of walking, where the
 * near deal re-deals every 0.6 m (`TUNE.step.near`). The spec below keeps the
 * near ring's whole lattice (7.6 m at `full`) inside the tile from anywhere in
 * the re-centre cell: half the tile less half a step is 12 m.
 *
 * Nothing here imports three.js, for the reason `turf-tile.js` gives: the tool
 * builds and samples the tile from the same code the page uploads.
 */

/**
 * 0.125 m a texel over 32 m: 256 x 256, re-centred every 8 m.
 *
 * Read at every near slot of the 22 critic stations
 * (docs/measurements/t-2698-near-field.json): 1.17 % of slots on the phone and
 * 0.90 % on the desktop disagree with the CPU on some channel, height p95
 * under 0.6 mm. Halving the texel buys a quarter of a point; doubling it costs
 * half a point and doubles the community misses. About half of the phone's
 * misses are the worked bank at the wharf, whose bare patches are a per-point
 * hash (`working-bank.js`, `blocksGrowth`): no texel holds that, and the raster
 * keeps its share, not its slots.
 *
 * THE BUILD IS THE COST: about 0.4 s a tile on the runner, ~50 ms per metre
 * walked against the near re-deal's 2-9 ms. It cannot be built on the main
 * thread as it is — it wants the job pool and a strip at a time.
 */
export const FIELD_SPEC = Object.freeze({ texel: 0.125, size: 256, recentre: 8 });

/** The flag bits of the class texture's G channel. */
export const FIELD_FLAGS = Object.freeze({
  /** `water.isWater` — which half of the community the slot may pick from. */
  WET: 1,
  /** `zone.turf` — the near ring plants nothing on short turf (T-2122). */
  TURF: 2,
  /** No rooted plant at all: a dated travelway (`growthBlocked`) or a floor
   *  whose polygon holds the point (the plank walks and the decks, T-0085). */
  BLOCKED: 4,
  /** A plant taller than its turf community's `turfCeiling` is cropped here:
   *  the worked roadway and the verge, less the kept patches (T-2094). */
  TRODDEN: 8,
});

/** Where the tile covering a camera at (`camE`, `camN`) starts: snapped to the
 *  re-centre step, so the origin moves only when the walker crosses a step. */
export function fieldOrigin(camE, camN, spec = FIELD_SPEC) {
  const span = spec.texel * spec.size;
  const snap = (v) => Math.round(v / spec.recentre) * spec.recentre - span / 2;
  return { e0: snap(camE), n0: snap(camN) };
}

/**
 * Build the tile at an origin. `at(e, n, out)` is the CPU's answer at one point
 * — `out[0]` community (0 = none), `out[1]` flags, `out[2]` ground height — and
 * is asked once per texel centre, row by row northward. `ms` is the wall time
 * the build took, which is the number the ticket asks to be set against today's
 * near re-deal.
 */
export function buildField(at, e0, n0, spec = FIELD_SPEC) {
  const { texel, size } = spec;
  const cls = new Uint8Array(size * size * 2);
  const height = new Float32Array(size * size);
  const out = [0, 0, 0];
  const t0 = performance.now();
  for (let j = 0; j < size; j++) {
    const n = n0 + (j + 0.5) * texel;
    for (let i = 0; i < size; i++) {
      at(e0 + (i + 0.5) * texel, n, out);
      const k = j * size + i;
      cls[2 * k] = out[0];
      cls[2 * k + 1] = out[1];
      height[k] = out[2];
    }
  }
  return { e0, n0, texel, size, cls, height, ms: performance.now() - t0 };
}

/**
 * The CPU mirror of `FIELD_GLSL`, line for line: the texel a slot falls in for
 * the class, and the bilinear blend of the four texel centres around it for the
 * height, clamped at the tile's edge. `out` is [community, flags, height], and
 * null comes back for a point outside the tile.
 */
export function sampleField(tile, e, n, out = [0, 0, 0]) {
  const { e0, n0, texel, size, cls, height } = tile;
  const fx = (e - e0) / texel;
  const fy = (n - n0) / texel;
  const i = Math.floor(fx);
  const j = Math.floor(fy);
  if (i < 0 || j < 0 || i >= size || j >= size) return null;
  const k = j * size + i;
  out[0] = cls[2 * k];
  out[1] = cls[2 * k + 1];
  const gx = fx - 0.5, gy = fy - 0.5;
  const i0 = Math.min(Math.max(Math.floor(gx), 0), size - 1);
  const j0 = Math.min(Math.max(Math.floor(gy), 0), size - 1);
  const i1 = Math.min(i0 + 1, size - 1);
  const j1 = Math.min(j0 + 1, size - 1);
  const tx = Math.min(Math.max(gx - Math.floor(gx), 0), 1);
  const ty = Math.min(Math.max(gy - Math.floor(gy), 0), 1);
  const h0 = height[j0 * size + i0] * (1 - tx) + height[j0 * size + i1] * tx;
  const h1 = height[j1 * size + i0] * (1 - tx) + height[j1 * size + i1] * tx;
  out[2] = h0 * (1 - ty) + h1 * ty;
  return out;
}

/**
 * The shader's half (GLSL ES 3.00). `en` is a point in the town's (east, north)
 * metres — world x and -z. The uniforms are the tile's origin, its texel in
 * metres and its size in texels; `uFieldClass` is the RG8UI texture and
 * `uFieldHeight` the R32F one, both uploaded with `NearestFilter`. The near
 * grass material (T-2699) includes this chunk; `measure_near_field.mjs` reads
 * it back through the GPU against `sampleField` and the CPU's own answers.
 */
export const FIELD_GLSL = /* glsl */ `
uniform highp usampler2D uFieldClass;
uniform highp sampler2D uFieldHeight;
uniform vec2 uFieldOrigin;
uniform float uFieldTexel;
uniform int uFieldSize;

uvec2 fieldClass(vec2 en) {
  ivec2 t = ivec2(floor((en - uFieldOrigin) / uFieldTexel));
  t = clamp(t, ivec2(0), ivec2(uFieldSize - 1));
  return texelFetch(uFieldClass, t, 0).rg;
}

float fieldHeight(vec2 en) {
  vec2 g = (en - uFieldOrigin) / uFieldTexel - 0.5;
  vec2 f = clamp(g - floor(g), 0.0, 1.0);
  ivec2 a = clamp(ivec2(floor(g)), ivec2(0), ivec2(uFieldSize - 1));
  ivec2 b = min(a + 1, ivec2(uFieldSize - 1));
  float h00 = texelFetch(uFieldHeight, a, 0).r;
  float h10 = texelFetch(uFieldHeight, ivec2(b.x, a.y), 0).r;
  float h01 = texelFetch(uFieldHeight, ivec2(a.x, b.y), 0).r;
  float h11 = texelFetch(uFieldHeight, b, 0).r;
  return mix(mix(h00, h10, f.x), mix(h01, h11, f.x), f.y);
}
`;
