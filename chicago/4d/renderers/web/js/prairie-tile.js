/**
 * prairie-tile.js — the July ground tile's PIXELS, and nothing else.
 *
 * Lifted out of `terrain.js` unchanged so that a tool can measure the tile
 * without a browser: the mean of this tile is the divisor that makes every
 * substrate zone's mean albedo come out at exactly the triple its flora record
 * states, so a measurement of it is a gate on a claim and not a curiosity.
 * The same reason `shrub-grain.js` exists — a module that imports nothing.
 *
 * The colour argument, the octave sizes and the thatch minority all live with
 * `prairieTexture()` in `terrain.js`, which is the only caller that draws it.
 * Nothing here decides anything; it fills a buffer.
 */

/** The tile is 256 px over an 11 m footprint — 4 cm per texel. See terrain.js. */
export const PRAIRIE_TILE_PX = 256;

// The July ramp. Dark = shaded green between the clumps; light = sunlit blade,
// which is also the yellower of the two.
const DARK = [68, 87, 49];
const LIGHT = [118, 125, 72];
// Last year's litter, kept to a minority on purpose.
const THATCH = [138, 134, 94];
// Bare loam where the sward thins: the black prairie soil, dry at the surface.
// Reconstructed tone, not a measured reflectance (T-1825).
const LOAM = [78, 66, 48];

/**
 * RGBA bytes for one tile, row-major, `PRAIRIE_TILE_PX` square.
 *
 * Deterministic: the seed is fixed, so the tile a tool measures is the tile the
 * renderer draws, texel for texel.
 *
 * @returns {Uint8ClampedArray} length `PRAIRIE_TILE_PX ** 2 * 4`
 */
export function prairieTilePixels() {
  const S = PRAIRIE_TILE_PX;
  const data = new Uint8ClampedArray(S * S * 4);
  let seed = 20260809;
  const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;

  /** A tiling value-noise octave: `n` cells across the tile, smoothstepped. */
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
  const o16 = octave(16);   // ~0.7 m — clump scale
  const o32 = octave(32);   // ~0.35 m — tussock
  const o64 = octave(64);   // ~0.17 m — leaf mass
  const oThatch = octave(48);

  // THE GROWTH FIELD (T-1825): coherent 1.4-2.75 m patches of vigour, the
  // scale Glessner v4's lawn study found missing from a uniform olive mat. It
  // takes its draws from its OWN seed, so the four octaves above and the
  // per-texel grain below take exactly the draws they always took.
  let gSeed = 20261001;
  const grnd = () => (gSeed = (gSeed * 1664525 + 1013904223) >>> 0) / 4294967296;
  const gOctave = (n) => {
    const g = new Float32Array(n * n);
    for (let i = 0; i < g.length; i++) g[i] = grnd();
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
  const g4 = gOctave(4);    // ~2.75 m: a stand of vigorous growth, or a thin one
  const g8 = gOctave(8);    // ~1.4 m: its ragged edge
  const smooth = (a, b, x) => {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  };

  // The previous revision's texel is computed beside the new one so the drawn
  // tile can be returned to that tile's mean, channel by channel. The mean is a
  // MEASUREMENT (prairieTexture in terrain.js). The growth field moves light
  // and dark around the ground. It must not move the colour that the July
  // photographs set.
  const px = new Float32Array(S * S * 3);
  const want = [0, 0, 0];
  const got = [0, 0, 0];
  const SHADE = [0.74, 0.81, 0.92];
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const v = 0.42 * o16(x, y) + 0.26 * o32(x, y) + 0.18 * o64(x, y) + 0.14 * rnd();
      const t = Math.max(0, oThatch(x, y) - 0.62) * (1.6 - v) * 0.9;
      const G = 0.62 * g4(x, y) + 0.38 * g8(x, y);
      // Lush: the canopy closes, and the ground under it is shaded and bluer.
      const lush = smooth(0.48, 0.74, G);
      // Thin: last year's litter shows through. In the thinnest places a
      // little bare loam shows between the tussocks, but never a bald patch:
      // the loam is gated on the leaf-mass octave, so it is a speckle within
      // the thatch.
      const thin = 1 - smooth(0.26, 0.50, G);
      const tThin = Math.min(0.66, t + thin * (0.26 + 0.34 * o32(x, y)));
      const loam = thin * (1 - smooth(0.14, 0.40, o64(x, y))) * 0.26;
      const j = (y * S + x) * 3;
      for (let ch = 0; ch < 3; ch++) {
        const green = DARK[ch] + (LIGHT[ch] - DARK[ch]) * v;
        want[ch] += green + (THATCH[ch] - green) * Math.min(0.5, t);
        const canopy = green * (1 - lush * (1 - SHADE[ch]));
        let c = canopy + (THATCH[ch] - canopy) * tThin;
        c += (LOAM[ch] - c) * loam;
        px[j + ch] = c;
        got[ch] += c;
      }
    }
  }
  const gain = want.map((w, ch) => w / got[ch]);
  for (let k = 0; k < S * S; k++) {
    for (let ch = 0; ch < 3; ch++) data[k * 4 + ch] = Math.round(px[k * 3 + ch] * gain[ch]);
    data[k * 4 + 3] = 255;
  }
  return data;
}

/** sRGB byte to the renderer's linear working space. */
export function srgbToLinear(u8) {
  const v = u8 / 255;
  return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
}

/**
 * The tile's mean LINEAR luminance, Rec. 709 — the divisor `zoneGlsl` uses.
 * Measured from the pixels, never written down as a constant: retuning the ramp
 * must not silently put every zone's albedo off by the amount the mean moved.
 */
export function prairieTileMeanLuma(data = prairieTilePixels()) {
  let sum = 0;
  for (let i = 0; i < data.length; i += 4) {
    sum += 0.2126 * srgbToLinear(data[i]) + 0.7152 * srgbToLinear(data[i + 1])
         + 0.0722 * srgbToLinear(data[i + 2]);
  }
  return sum / (data.length / 4);
}
