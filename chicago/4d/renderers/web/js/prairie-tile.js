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

  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const v = 0.42 * o16(x, y) + 0.26 * o32(x, y) + 0.18 * o64(x, y) + 0.14 * rnd();
      // Thatch shows only where the litter octave peaks and the sward is thin.
      const t = Math.max(0, oThatch(x, y) - 0.62) * (1.6 - v) * 0.9;
      const i = (y * S + x) * 4;
      for (let ch = 0; ch < 3; ch++) {
        const green = DARK[ch] + (LIGHT[ch] - DARK[ch]) * v;
        data[i + ch] = green + (THATCH[ch] - green) * Math.min(0.5, t);
      }
      data[i + 3] = 255;
    }
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
