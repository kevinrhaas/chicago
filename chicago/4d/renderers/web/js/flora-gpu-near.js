/**
 * The near ring's grass DRAWN from the shader in the page (T-2716, the second
 * piece of T-2708 under T-2557's GPU-procedural near grass).
 *
 * T-2697 put the lattice walk in GLSL (`flora-gpu-lattice.js`), T-2698 and
 * T-2707 the ground's answers in a tile kept around the walker
 * (`near-field.js`), T-2706 the deal between them (`flora-gpu-deal.js`), and
 * T-2715 made the tile's BLOCKED hold the CPU's exclusion slot for slot. All
 * four were read back by tools and drew nothing. This is the draw:
 *
 *   1. THE DEAL PASS. At every near placement the page draws one point per
 *      lattice slot (`gl_VertexID` is the slot, in `scatter`'s order) through
 *      LATTICE_GLSL, FIELD_GLSL and DEAL_GLSL into four float targets at once
 *      (one MRT pass). A placed slot writes its instance: where it roots, its
 *      height, spread, arch and yaw, its colour and confidence, and its OWN
 *      ring — `slotRing`'s handover, in GLSL below — and every other slot
 *      writes zeros. The CPU deals nothing for it.
 *   2. THE TUFT. The near ring's tuft mesh draws one instance per slot; its
 *      vertex program fetches its slot's four texels (`NEAR_FETCH_GLSL`) where
 *      `plantMaterial` used to read the instance attributes, and a slot the
 *      deal did not place collapses to a point, as a plant outside its ring
 *      always has.
 *
 * A slot the kept tile does not cover is NOT placed (`flInTile`). The keeper
 * re-centres a strip at a time on the job pool, so for a moment after a step
 * its tile can lag the walker; a lagging tile used to be clamped at its edge,
 * which would have dealt the edge texel's community to every slot past it.
 * Now those slots are empty until the strip lands, and the page re-runs the
 * deal pass the moment it does.
 *
 * Positions are WORLD metres in float32 — what the CPU set's instance matrix
 * carried too; the deal itself is camera-relative (T-2697's precision note).
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

/** The deal pass's target width in texels; its height follows the slot count. */
export const NEAR_TARGET_WIDTH = 256;

/** The MOST slots a near walk can visit: `latticeUniforms`' count at its
 *  widest, which a target and a record are sized to. */
export function nearSlotsMax({ cell, perCell, radius }) {
  const side = Math.ceil((2 * radius) / cell) + 3;
  return side * side * perCell;
}

/** The deal pass's target size for `count` slots. */
export function nearTarget(count) {
  return { width: NEAR_TARGET_WIDTH, height: Math.max(1, Math.ceil(count / NEAR_TARGET_WIDTH)) };
}

/**
 * flora.js `slotRing` for the near ring, in GLSL: the ring's nominal fade, with
 * the outer boundary moved IN by the slot's world-anchored share of the band
 * (`handoverRank`: `unitHash(round(e * 8), round(n * 8), salt)`), and the inner
 * one moved OUT likewise. Uniforms:
 *
 *   uNearFade    vec4   `rings.near.fade`: outer, band, inner, innerBand
 *   uNearSpread  vec2   `rings.near.spread`: outer, inner (0 = not spread)
 *   uNearSalt    uvec2  flora.js HANDOVER_SALT
 *
 * `round` is `floor(x + 0.5)`, which is Math.round's rule at a half, negative
 * halves included. The float32 product `e * 8` can land a slot on the other
 * side of a rounding half from the CPU's double — one slot's rank then differs,
 * which moves that one plant's own boundary within the band and nothing else.
 */
export const NEAR_RING_GLSL = /* glsl */ `
uniform vec4 uNearFade;
uniform vec2 uNearSpread;
uniform uvec2 uNearSalt;

float flHandover(vec2 en, uint salt) {
  return flUnit(flHash3(uint(flRoundI(en.x * 8.0)), uint(flRoundI(en.y * 8.0)), salt));
}

vec4 flNearRing(vec2 en) {
  return vec4(
    uNearFade.x - (uNearSpread.x > 0.0 ? uNearSpread.x * flHandover(en, uNearSalt.x) : 0.0),
    uNearFade.y,
    uNearFade.z + (uNearSpread.y > 0.0 ? uNearSpread.y * flHandover(en, uNearSalt.y) : 0.0),
    uNearFade.w);
}

// The slot's WORLD position from its absolute cell and its jitter alone —
// \`scatter\`'s \`(c + fe) * cell\` — so a slot is the same float32 point from every
// camera. \`flLatticeSlot\`'s \`rel\` is camera-relative (T-2697), and the camera
// plus \`rel\` rounds differently as the camera moves: the same tuft stood a few
// microns elsewhere after each pass, and the deal's texel and hash lookups could
// flip with it. The jitter is re-derived exactly as flLatticeSlot draws it.
vec2 flSlotWorld(int id, uint cellSeed) {
  int perCell = uLatGrid.w;
  int k = id % perCell;
  int cellIdx = id / perCell;
  int c = uLatGrid.x + cellIdx % uLatGrid.z;
  int r = uLatGrid.y + cellIdx / uLatGrid.z;
  uint s = flHash3(cellSeed, uint(k), 0x68bc21ebu);
  if (s == 0u) s = 1u;
  s = flXorshift(s);
  float je = float(s) / 4294967296.0;
  s = flXorshift(s);
  float jn = float(s) / 4294967296.0;
  int sub = int(uLatDeal.x);
  float fe = uLatMode == 2u ? je : (float(k % sub) + je) / float(sub);
  float fn = uLatMode == 2u ? jn : (float(k / sub) + jn) / float(sub);
  return vec2(float(c) + fe, float(r) + fn) * uLatCell.x;
}

// Is (east, north) inside the kept tile? FIELD_GLSL clamps a point outside it to
// the edge texel, which is right for a read-back and wrong for a draw.
bool flInTile(vec2 en) {
  vec2 t = (en - uFieldOrigin) / uFieldTexel;
  float s = float(uFieldSize);
  return t.x >= 0.0 && t.y >= 0.0 && t.x < s && t.y < s;
}
`;

/**
 * The deal pass's two shaders (GLSL ES 3.00, for a RawShaderMaterial), given
 * the three chunks they stand on — passed in so this module imports nothing.
 * Its own uniform is `uTarget` (the target's width and height); the rest are
 * the chunks'. Outputs, one texel per slot in each of four targets:
 *
 *   0  world x, y, z of the root (x east, z = -north), 1 when placed else 0
 *   1  height, spread, arch, yaw (`aFlora`)
 *   2  r, g, b, confidence
 *   3  the slot's own ring (`aChiRing`)
 */
export function nearPassShaders({ lattice, field, deal }) {
  const vertexShader = /* glsl */ `precision highp float; precision highp int;
precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
${lattice}
${field}
${deal}
${NEAR_RING_GLSL}
flat out vec4 v0;
flat out vec4 v1;
flat out vec4 v2;
flat out vec4 v3;
void main() {
  int id = gl_VertexID;
  v0 = vec4(0.0); v1 = vec4(0.0); v2 = vec4(0.0); v3 = vec4(0.0);
  vec2 rel; float u; uint rng; uint cellSeed;
  if (flLatticeSlot(id, rel, u, rng, cellSeed)) {
    // The deal is asked at the slot's world point: \`uDealCam\` is held at zero
    // for this pass, so \`flNearDeal\`'s \`uDealCam + rel\` IS that point, and the
    // walker's clearance still reads the camera-relative distance.
    vec2 en = flSlotWorld(id, cellSeed);
    int row; float vig;
    vec3 ground; vec4 fl; vec4 col;
    if (flInTile(en) && flNearDeal(en, length(rel), u, rng, row, vig, ground, fl, col) == 6) {
      v0 = vec4(ground.x, ground.y, -ground.z, 1.0);
      v1 = fl;
      v2 = col;
      v3 = flNearRing(ground.xz);
    }
  }
  float x = float(id % int(uTarget.x)), y = float(id / int(uTarget.x));
  gl_Position = vec4((x + 0.5) / uTarget.x * 2.0 - 1.0, (y + 0.5) / uTarget.y * 2.0 - 1.0, 0.0, 1.0);
  gl_PointSize = 1.0;
}`;
  const fragmentShader = /* glsl */ `precision highp float;
flat in vec4 v0;
flat in vec4 v1;
flat in vec4 v2;
flat in vec4 v3;
layout(location = 0) out vec4 o0;
layout(location = 1) out vec4 o1;
layout(location = 2) out vec4 o2;
layout(location = 3) out vec4 o3;
void main() { o0 = v0; o1 = v1; o2 = v2; o3 = v3; }`;
  return { vertexShader, fragmentShader };
}

/**
 * The tuft's half: what `plantMaterial` reads off the instance, fetched from the
 * deal pass's four targets by `gl_InstanceID` instead. It declares the globals
 * the material's program reads in place of its instance attributes —
 * `instanceMatrix` (with USE_INSTANCING defined here, so three's own chunks use
 * this one and declare no attribute), `aFlora`, `aChiRing`, `aChiFamily` — plus
 * the colour and confidence the CPU set carried as `instanceColor` and
 * `_confidence`, and `chiNearInstance()`, which the program calls first.
 * A slot the deal did not place gets a ring whose outer radius is behind the
 * camera, so the program's own ramp collapses it to a point.
 *
 * Uniforms: `uNearI0` … `uNearI3`, the targets' textures (nearest); `uNearW`,
 * their width.
 */
export const NEAR_FETCH_GLSL = /* glsl */ `
#define USE_INSTANCING
mat4 instanceMatrix;
vec4 aFlora;
vec4 aChiRing;
float aChiFamily;
vec3 chiNearCol;
float chiNearConf;
uniform highp sampler2D uNearI0;
uniform highp sampler2D uNearI1;
uniform highp sampler2D uNearI2;
uniform highp sampler2D uNearI3;
uniform int uNearW;
void chiNearInstance() {
  ivec2 t = ivec2(gl_InstanceID % uNearW, gl_InstanceID / uNearW);
  vec4 root = texelFetch(uNearI0, t, 0);
  instanceMatrix = mat4(1.0);
  aChiFamily = 0.0;
  if (root.w < 0.5) {
    aFlora = vec4(0.0);
    aChiRing = vec4(-1.0, 1e-6, 0.0, 0.0);
    chiNearCol = vec3(0.0);
    chiNearConf = 0.0;
    return;
  }
  instanceMatrix[3] = vec4(root.xyz, 1.0);
  aFlora = texelFetch(uNearI1, t, 0);
  vec4 col = texelFetch(uNearI2, t, 0);
  chiNearCol = col.rgb;
  chiNearConf = col.w;
  aChiRing = texelFetch(uNearI3, t, 0);
}
`;
