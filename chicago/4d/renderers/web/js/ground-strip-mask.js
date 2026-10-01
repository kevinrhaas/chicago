/**
 * ground-strip-mask.js — the T-1797 ground strip's LAYOUT and its MASK PIXELS,
 * and nothing else.
 *
 * Kept free of three.js for the same reason `prairie-tile.js` is: a tool can
 * read the strip's bands and its multi-scale masks from Node without a browser,
 * and the browser draws exactly the pixels the tool measured. `ground-strip.js`
 * is the only caller that binds them.
 *
 * WHAT THE STRIP IS. A proof, not a place: 48 m of ground laid on open prairie
 * south of the town, reading west to east as packed street dirt, worn bank soil,
 * grey sand, and sand thinning into sparse prairie, feathered into the terrain's
 * own prairie on every side. It shows a method T-1770–T-1772 and T-1210–T-1213
 * can lift — world-space metric tiles from the 1835 library for the fine grain,
 * a seeded runtime-canvas mask for everything coarser — and it claims nothing
 * about where in 1835 Chicago any of these grounds lay. It is drawn only under
 * `?proof=ground`. See docs/RESEARCH/1835_photographic_fabric_preparation.md § 8.
 */

/** The strip, in scene metres. `e0`/`n0` is the centre of its west end. */
export const STRIP = Object.freeze({
  e0: 121, n0: -455,
  lengthM: 48,      // west to east
  widthM: 12,       // across, centred on n0
  featherM: 2,      // the margin over which every side gives way to the prairie
  liftM: 0.03,      // above the heightfield, with polygon offset for the rest
  // Band edges along the strip, metres from the west end, before jitter.
  dirtEndM: 18, sandStartM: 26.5, prairieFromM: 31, prairieToM: 46,
});

/** Mask texels per metre: 12.5 cm, finer than the 0.5–2 m clumps it carries. */
export const MASK_PX_PER_M = 8;

/** The mask's footprint: the strip plus its feather on every side. */
export function maskSize() {
  const F = STRIP.featherM;
  return {
    w: Math.round((STRIP.lengthM + 2 * F) * MASK_PX_PER_M),
    h: Math.round((STRIP.widthM + 2 * F) * MASK_PX_PER_M),
  };
}

/** Scene (e, n) → strip-local (u along from the west end, v across from centre). */
export function stripLocal(e, n) {
  return { u: e - STRIP.e0, v: n - STRIP.n0 };
}

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * A seeded value-noise field in METRES, anisotropic if asked: `cu` metres per
 * cell along the strip, `cv` across. Not tiling — the strip is one footprint.
 */
function field(rnd, cu, cv, spanU, spanV) {
  const nu = Math.ceil(spanU / cu) + 2;
  const nv = Math.ceil(spanV / cv) + 2;
  const g = new Float32Array(nu * nv);
  for (let i = 0; i < g.length; i++) g[i] = rnd();
  return (u, v) => {
    const gx = u / cu, gy = v / cv;
    const x0 = Math.floor(gx), y0 = Math.floor(gy);
    const fx = gx - x0, fy = gy - y0;
    const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    const at = (x, y) => g[Math.min(nv - 1, Math.max(0, y)) * nu + Math.min(nu - 1, Math.max(0, x))];
    return (at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx) * (1 - sy)
         + (at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx) * sy;
  };
}

/**
 * RGBA bytes for the mask, row-major, `maskSize()`; row 0 is the strip's NORTH
 * edge, column 0 its west feather.
 *
 *   R  traffic wear — anisotropic, long along the strip (12 m × 1.4 m cells, then
 *      4 m × 0.5 m), so worn lanes overlap and wander instead of running as the
 *      two clean treads `streets.js` draws; it falls off toward the shoulders.
 *   G  wetness — 7–18 m, isotropic; decides where the dirt turns to local mud
 *      and how far the bank soil has gone to muck.
 *   B  clumping — 0.6–2 m coherent variation (the Glessner lawn's scale, used
 *      here for prairie clumps in the sand and the jitter of every band edge).
 *   A  broad tone — 20–60 m, the low-frequency swing the fabric map calls for.
 *
 * Deterministic: the seed is fixed, so the mask a tool measures is the mask the
 * renderer draws.
 *
 * @returns {{ data: Uint8ClampedArray, w: number, h: number }}
 */
export function stripMaskPixels() {
  const { w, h } = maskSize();
  const F = STRIP.featherM;
  const spanU = STRIP.lengthM + 2 * F, spanV = STRIP.widthM + 2 * F;
  let seed = 18351797;
  const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
  const laneLo = field(rnd, 12, 1.4, spanU, spanV);
  const laneHi = field(rnd, 4, 0.5, spanU, spanV);
  const wetLo = field(rnd, 18, 18, spanU, spanV);
  const wetHi = field(rnd, 7, 7, spanU, spanV);
  const clumpLo = field(rnd, 2, 2, spanU, spanV);
  const clumpHi = field(rnd, 0.6, 0.6, spanU, spanV);
  const broadA = field(rnd, 60, 60, spanU, spanV);
  const broadB = field(rnd, 20, 20, spanU, spanV);

  const data = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) {
    const v = STRIP.widthM / 2 + F - (y + 0.5) / MASK_PX_PER_M;   // + is north
    const vv = v + spanV / 2;                                        // ≥ 0 for the field
    for (let x = 0; x < w; x++) {
      const uu = (x + 0.5) / MASK_PX_PER_M;                          // ≥ 0 for the field
      // Lanes concentrate mid-width and thin toward the shoulders, so the
      // edge of the roadway is irregular, softer and greener than its crown.
      const shoulder = 1 - 0.75 * smooth(3.0, 6.0, Math.abs(v));
      const lane = (0.62 * laneLo(uu, vv) + 0.38 * laneHi(uu, vv));
      const wear = smooth(0.30, 0.78, lane) * shoulder;
      const wet = 0.65 * wetLo(uu, vv) + 0.35 * wetHi(uu, vv);
      const clump = 0.55 * clumpLo(uu, vv) + 0.45 * clumpHi(uu, vv);
      const broad = 0.6 * broadA(uu, vv) + 0.4 * broadB(uu, vv);
      const i = (y * w + x) * 4;
      data[i] = wear * 255;
      data[i + 1] = wet * 255;
      data[i + 2] = clump * 255;
      data[i + 3] = broad * 255;
    }
  }
  return { data, w, h };
}

/**
 * The substrate weights at strip-local (u, v), from mask values in 0..1 — the
 * same arithmetic `ground-strip.js` runs per fragment, so the flora layer is
 * told to leave bare exactly the ground the shader draws bare.
 *
 * @returns {{ dirt: number, mud: number, bank: number, sand: number, prairie: number }}
 *   weights summing to 1; `mud` is the part of `dirt` gone to mud.
 */
export function stripWeights(u, v, m) {
  const S = STRIP, F = S.featherM;
  // Band edges wander by up to ~2 m, on the clump and broad scales together.
  const uj = u + (m.b - 0.5) * 2.4 + (m.a - 0.5) * 1.6;
  const dirtW = 1 - smooth(S.dirtEndM - 1.5, S.dirtEndM + 1.5, uj);
  const sandW = smooth(S.sandStartM - 1.5, S.sandStartM + 1.5, uj);
  const bankW = Math.max(0, 1 - dirtW - sandW);
  // Sand thins into prairie in clumps: a clump goes green once the ramp
  // passes its own clump value, so the prairie arrives as islands, not a line.
  const ramp = smooth(S.prairieFromM, S.prairieToM, uj);
  const clumped = smooth(m.b - 0.12, m.b + 0.12, ramp);
  // A shoulder the traffic leaves alone keeps a little grass.
  // Both are FRACTIONS of the dirt band, and mud only takes what grass left,
  // so no weight goes negative and the five still sum to one.
  const grassF = (1 - m.r) * smooth(0.70, 0.86, m.b) * smooth(4.0, 6.0, Math.abs(v));
  const mudF = smooth(0.60, 0.72, m.g) * (0.4 + 0.6 * m.r) * (1 - grassF);
  const shoulderGrass = dirtW * grassF;
  // Every side gives way to the terrain's own prairie over the feather, on a
  // jittered line so the strip has no ruled edge.
  const inside = Math.min(u + F, S.lengthM + F - u, S.widthM / 2 + F - Math.abs(v));
  const edge = smooth(0, F, inside - F / 2 + (m.b - 0.5) * 1.2);
  const mud = dirtW * mudF;
  const prairie = 1 - edge * (1 - sandW * clumped - shoulderGrass);
  return {
    dirt: edge * (dirtW - mud - shoulderGrass),
    mud: edge * mud,
    bank: edge * bankW,
    sand: edge * sandW * (1 - clumped),
    prairie,
  };
}

/** The mask values at strip-local (u, v), nearest texel; null off the mask. */
export function maskAt(mask, u, v) {
  const F = STRIP.featherM;
  const x = Math.floor((u + F) * MASK_PX_PER_M);
  const y = Math.floor((STRIP.widthM / 2 + F - v) * MASK_PX_PER_M);
  if (x < 0 || y < 0 || x >= mask.w || y >= mask.h) return null;
  const i = (y * mask.w + x) * 4;
  const d = mask.data;
  return { r: d[i] / 255, g: d[i + 1] / 255, b: d[i + 2] / 255, a: d[i + 3] / 255 };
}

/**
 * THE GRIT TILE — the fine relief the library could not supply.
 *
 * The fabric map (§ 4) gave the dirt's fine detail to `packed_black_loam`'s
 * relief. Measured for this proof, that relief is not there: the loam's 1024²
 * basecolor has a luminance spread of 1.8 sRGB units (SD, of 255) and its
 * `normal_gl` an SD under one unit per channel — the muck and the sand are the
 * same — so bound at full strength it draws a smooth brown. Only the AI-derived
 * `muddy_rutted_street` carries relief (SD 17 / 9), and the map has already
 * refused it as a roadway for its repeating ruts. So the grit is generated here,
 * a runtime canvas like the prairie tile: 256 px over 1.6 m (6 mm a texel),
 * tiling, seeded. Clods at 2–5 cm, grit at 1 cm, dust at a texel, and a few
 * hundred pebbles and hoof-pocked hollows as round bumps.
 *
 *   R  height, 0..1 — read as luminance grain (over the tile's own mean)
 *   G  normal east component, B  normal north component (OpenGL, 0.5 = flat)
 */
export const GRIT_TILE_PX = 256;
export const GRIT_TILE_M = 1.6;

export function gritTilePixels() {
  const S = GRIT_TILE_PX;
  let seed = 17971835;
  const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
  const octave = (n) => {
    const g = new Float32Array(n * n);
    for (let i = 0; i < g.length; i++) g[i] = rnd();
    const at = (x, y) => g[(((y % n) + n) % n) * n + (((x % n) + n) % n)];
    return (x, y) => {
      const gx = x * n / S, gy = y * n / S;
      const x0 = Math.floor(gx), y0 = Math.floor(gy);
      const fx = gx - x0, fy = gy - y0;
      const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
      return (at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx) * (1 - sy)
           + (at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx) * sy;
    };
  };
  const clod = octave(48);    // ~3.3 cm
  const grit = octave(128);   // ~1.25 cm
  const h = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      h[y * S + x] = 0.5 * clod(x, y) + 0.32 * grit(x, y) + 0.18 * rnd();
    }
  }
  // Pebbles (raised) and pocks (sunk), 1–3 cm across, wrapping at the edges.
  for (let k = 0; k < 420; k++) {
    const cx = rnd() * S, cy = rnd() * S;
    const r = 1.5 + rnd() * 3.5;                 // texels
    const amp = (rnd() < 0.6 ? 1 : -1) * (0.25 + 0.35 * rnd());
    const R = Math.ceil(r * 2);
    for (let dy = -R; dy <= R; dy++) {
      for (let dx = -R; dx <= R; dx++) {
        const d2 = (dx * dx + dy * dy) / (r * r);
        if (d2 > 4) continue;
        const x = ((Math.floor(cx) + dx) % S + S) % S, y = ((Math.floor(cy) + dy) % S + S) % S;
        h[y * S + x] += amp * Math.exp(-d2 * 1.5);
      }
    }
  }
  let lo = Infinity, hi = -Infinity;
  for (const v of h) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  const data = new Uint8ClampedArray(S * S * 4);
  const H = (x, y) => (h[(((y % S) + S) % S) * S + (((x % S) + S) % S)] - lo) / (hi - lo);
  // Slope per texel → normal: strength chosen so the steepest clod leans ~35°.
  const K = 6;
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const nx = -(H(x + 1, y) - H(x - 1, y)) * 0.5 * K;
      // Row 0 is the tile's north edge (the texture is flipped on upload), so
      // north is DEcreasing y.
      const ny = -(H(x, y - 1) - H(x, y + 1)) * 0.5 * K;
      const inv = 1 / Math.hypot(nx, ny, 1);
      const i = (y * S + x) * 4;
      data[i] = H(x, y) * 255;
      data[i + 1] = (nx * inv * 0.5 + 0.5) * 255;
      data[i + 2] = (ny * inv * 0.5 + 0.5) * 255;
      data[i + 3] = 255;
    }
  }
  return data;
}
