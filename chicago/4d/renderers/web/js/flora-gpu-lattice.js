/**
 * flora.js's lattice walk as GLSL: one slot per `gl_InstanceID` (T-2697, the first
 * piece of T-2557's GPU-procedural near grass).
 *
 * T-2557 asks for the near ring's grass dealt in the vertex shader, with no CPU
 * lattice and no re-deal on move. Its first half is the walk itself: which
 * world-anchored cell and slot an instance is, where its jitter puts it, whether
 * the ring keeps it, its stratified deal rank `u` and the xorshift stream its
 * placement goes on drawing from. That is what `scatter` in flora.js computes per
 * slot on the CPU, and what `jobs/lattice-kernel.js` computes on a worker; this is
 * the same walk in a shader. The deal's questions (zone, water, floors, heights)
 * are T-2698's field tile and the drawing is T-2699; neither is here.
 *
 * **The instance-to-slot mapping is the walk's order.** An instance id is
 * `((row * cols) + col) * perCell + k` over the bounding square of cells the CPU
 * walk visits, so the instances the ring keeps, read in id order, are `scatter`'s
 * slots in `scatter`'s order: rows outer, cells inner, the cell's k slots
 * innermost. The CPU's cell-level ring test is applied too, because it is not
 * only an economy (see the shader: at two slots a cell one of them stands in the
 * next cell north, which that test can drop while the ring would keep it). The view cone is
 * not applied: a GPU culls against the frustum when it rasterises, and the cone is
 * a CPU economy, not part of the field.
 *
 * **Precision, stated rather than hoped for.** Every integer the walk computes —
 * the cell seed, the Feistel permutation, the Morton block phase's bits, the
 * stream state — is a 32-bit unsigned operation and is the CPU's to the bit;
 * `Math.imul` and a GLSL `uint` multiply wrap identically, and a negative cell
 * index enters `hash3` as the same two's-complement bits on both. What is NOT
 * bit-equal is the float arithmetic: flora.js computes `u` and the position in
 * doubles and a shader in float32. Positions are carried RELATIVE to the camera
 * (the camera's own offset from the walk's first cell is computed in doubles on
 * the CPU and passed in), so they are accurate to float32 at a few metres, not at
 * the town's 2 km; `u` is within a few float32 ulps. `tools/measure_flora_gpu_
 * lattice.mjs` reads both back from Chromium against the kernel and prints the
 * largest difference of each and every slot the ring disagrees on.
 *
 * It imports nothing: a tool reads it from Node, the page binds it to three.
 */

// The constants of flora.js's walk, by the values it uses
// (`tools/check_flora_gpu_lattice.mjs` holds this text to flora.js's).
export const STRAT_SALT = 0x7f4a7c15;
export const STRAT_BLOCK_SHIFT = 2;

/** `scatter`'s `draw` argument as the shader's mode number. */
export const DRAW_MODE = Object.freeze({ strata: 0, lattice: 1, wild: 2 });

/**
 * The GLSL ES 3.00 text: `flHash3` … `flStratum` are flora.js's helpers of the same
 * names, and `flLatticeSlot(id, …)` is one slot of `scatter`. It reads five
 * uniforms, which `latticeUniforms` fills:
 *
 *   uLatGrid  ivec4  c0, r0, cols, perCell — the walk's first cell, its width, k
 *   uLatDeal  uvec4  sub, nSlots, half, salt — the jitter grid and the stratum
 *   uLatMode  uint   0 strata · 1 lattice · 2 wild (DRAW_MODE)
 *   uLatRing  vec4   the camera's offset from cell (c0, r0)'s corner, east and
 *                    north, in metres; radius²; inner²
 *   uLatCell  vec2   the cell size in metres; the global block shift
 */
export const LATTICE_GLSL = /* glsl */ `
uniform ivec4 uLatGrid;
uniform uvec4 uLatDeal;
uniform uint uLatMode;
uniform vec4 uLatRing;
uniform vec2 uLatCell;

uint flHash3(uint a, uint b, uint c) {
  uint h = (a * 0x27d4eb2du) ^ (b * 0x165667b1u) ^ (c * 0x9e3779b1u);
  h = (h ^ (h >> 15u)) * 0x85ebca6bu;
  h = (h ^ (h >> 13u)) * 0xc2b2ae35u;
  return h ^ (h >> 16u);
}

uint flFeistel(uint x, uint halfBits, uint key) {
  uint mask = (1u << halfBits) - 1u;
  uint l = (x >> halfBits) & mask;
  uint r = x & mask;
  for (uint i = 0u; i < 4u; i++) {
    uint t = l ^ (flHash3(r, key, i + 1u) & mask);
    l = r;
    r = t;
  }
  return (l << halfBits) | r;
}

float flStratum(uint idx, uint n, uint halfBits, uint key, float phase) {
  uint x = idx;
  for (int guard = 0; guard < 24; guard++) {
    x = flFeistel(x, halfBits, key);
    if (x < n) return fract((float(x) + 0.5) / float(n) + phase);
  }
  return fract((float(idx) + 0.5) / float(n) + phase);
}

uint flSpread16(uint n) {
  uint x = n & 0xffffu;
  x = (x | (x << 8u)) & 0x00ff00ffu;
  x = (x | (x << 4u)) & 0x0f0f0f0fu;
  x = (x | (x << 2u)) & 0x33333333u;
  x = (x | (x << 1u)) & 0x55555555u;
  return x;
}

uint flMorton(int c, int r) {
  return (flSpread16(uint(r + 0x8000)) << 1u) | flSpread16(uint(c + 0x8000));
}

float flVdc(uint i) {
  uint x = i;
  x = ((x & 0x55555555u) << 1u) | ((x >> 1u) & 0x55555555u);
  x = ((x & 0x33333333u) << 2u) | ((x >> 2u) & 0x33333333u);
  x = ((x & 0x0f0f0f0fu) << 4u) | ((x >> 4u) & 0x0f0f0f0fu);
  x = ((x & 0x00ff00ffu) << 8u) | ((x >> 8u) & 0x00ff00ffu);
  return float((x >> 16u) | (x << 16u)) / 4294967296.0;
}

float flBlockPhase(int c, int r, uint n, float globalShift) {
  return fract(globalShift + flVdc(flMorton(c, r)) / float(n));
}

uint flXorshift(uint s) {
  s ^= s << 13u;
  s ^= s >> 17u;
  s ^= s << 5u;
  return s;
}

// One slot of scatter. False when the ring does not keep it; otherwise \`rel\` is
// its position east and north of the camera in metres, \`u\` its deal rank,
// \`rng\` its stream after the two jitter draws and \`cellSeed\` its cell's seed.
bool flLatticeSlot(int id, out vec2 rel, out float u, out uint rng, out uint cellSeed) {
  int perCell = uLatGrid.w;
  int k = id % perCell;
  int cellIdx = id / perCell;
  int ci = cellIdx % uLatGrid.z;
  int ri = cellIdx / uLatGrid.z;
  int c = uLatGrid.x + ci;
  int r = uLatGrid.y + ri;
  // scatter's cell-level ring test. It is not only an economy: at two slots a
  // cell the jitter grid is one column of two rows, so slot 1 stands in the next
  // cell north, and a cell this test drops can own a slot the ring would keep.
  float cell = uLatCell.x;
  float nx0 = float(ci) * cell - uLatRing.x, nx1 = nx0 + cell;
  float ny0 = float(ri) * cell - uLatRing.y, ny1 = ny0 + cell;
  float nx = nx0 > 0.0 ? nx0 : nx1 < 0.0 ? -nx1 : 0.0;
  float ny = ny0 > 0.0 ? ny0 : ny1 < 0.0 ? -ny1 : 0.0;
  float fx = max(abs(nx0), abs(nx1)), fy = max(abs(ny0), abs(ny1));
  bool cellKept = !(nx * nx + ny * ny > uLatRing.z || fx * fx + fy * fy < uLatRing.w);
  uint salt = uLatDeal.w;
  cellSeed = flHash3(uint(c), uint(r), salt);
  uint s = flHash3(cellSeed, uint(k), 0x68bc21ebu);
  if (s == 0u) s = 1u;
  s = flXorshift(s);
  float je = float(s) / 4294967296.0;
  s = flXorshift(s);
  float jn = float(s) / 4294967296.0;
  rng = s;
  if (uLatMode == 0u) {
    int bc = c >> 2;
    int br = r >> 2;
    uint blockHash = flHash3(uint(bc), uint(br), salt ^ 0x7f4a7c15u);
    float shift = flBlockPhase(bc, br, uLatDeal.y, uLatCell.y);
    int base = ((c - (bc << 2)) * 4 + (r - (br << 2))) * perCell;
    u = flStratum(uint(base + k), uLatDeal.y, uLatDeal.z, blockHash, shift);
  } else {
    float cellPhase = flBlockPhase(c, r, uint(perCell), uLatCell.y);
    u = fract(float(k) / float(perCell) + cellPhase);
  }
  int sub = int(uLatDeal.x);
  float fe = uLatMode == 2u ? je : (float(k % sub) + je) / float(sub);
  float fn = uLatMode == 2u ? jn : (float(k / sub) + jn) / float(sub);
  rel = vec2((float(ci) + fe) * cell - uLatRing.x, (float(ri) + fn) * cell - uLatRing.y);
  float d2 = dot(rel, rel);
  return cellKept && !(d2 > uLatRing.z || d2 < uLatRing.w);
}
`;

function hash3(a, b, c) {
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ Math.imul(c, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

function stratumHalf(n) {
  let bits = 1;
  while ((1 << bits) < n) bits++;
  return (bits + 1) >> 1;
}

/**
 * The CPU's whole share of a GPU walk: a handful of numbers per camera move,
 * computed in doubles where precision matters. Takes `scatter`'s own arguments by
 * the same names (`cone` has no meaning here and is not read).
 *
 * @returns {{count: number, grid: number[], deal: number[], mode: number,
 *   ring: number[], cell: number[], origin: {e: number, n: number}}}
 *   `count` instances to draw; `grid` … `cell` the uniforms' values in the order
 *   LATTICE_GLSL declares them; `origin` the world position of cell (c0, r0)'s
 *   corner, so a reader can put a `rel` back into the town.
 */
export function latticeUniforms({ camE, camN, cell, perCell, radius, inner, salt, draw }) {
  if (!(draw in DRAW_MODE)) throw new Error(`flora-gpu-lattice: unknown draw '${draw}'`);
  const c0 = Math.floor((camE - radius) / cell);
  const c1 = Math.ceil((camE + radius) / cell);
  const r0 = Math.floor((camN - radius) / cell);
  const r1 = Math.ceil((camN + radius) / cell);
  const cols = c1 - c0 + 1;
  const rows = r1 - r0 + 1;
  const sub = Math.max(1, Math.round(Math.sqrt(perCell)));
  const span = 1 << STRAT_BLOCK_SHIFT;
  const nSlots = span * span * perCell;
  const globalShift = hash3(salt, STRAT_SALT, 0x9e3779b9) / 4294967296;
  return {
    count: cols * rows * perCell,
    grid: [c0, r0, cols, perCell],
    deal: [sub, nSlots, stratumHalf(nSlots), salt >>> 0],
    mode: DRAW_MODE[draw],
    ring: [camE - c0 * cell, camN - r0 * cell, radius * radius, inner * inner],
    cell: [cell, globalShift],
    origin: { e: c0 * cell, n: r0 * cell },
  };
}
