/**
 * prairie-macro.js — the prairie's WORLD-SCALE variation map, its pixels and
 * nothing else (T-2552).
 *
 * The owner, 2026-10-16, from 1,197 ft up: "you can see a grid of your variable
 * surface. It looks like an even plaid. Close up it looks great, but from above
 * it looks like a grid." Two things drew that grid. The 11 m colour tile
 * repeated on a square lattice, and the "community mosaic" laid over it was
 * `sin(x) * sin(z)` — an egg-crate, which is a plaid by construction: 42 by 48 m
 * cells, square to the compass, light and dark in turn to the horizon.
 *
 * This map replaces the mosaic. It is ONE texture, 512 px over 3,072 m, so its
 * own repeat is longer than the haze reach (2,660 m, world.js) and no view sees
 * it twice; the shader also turns it 27 degrees off the compass, so what little
 * lattice bias a gradient noise keeps does not line up with the streets. Each
 * channel is an independent, seeded, domain-warped gradient noise:
 *
 *   R  patch tone — lush and thin ground, 18-400 m. The role, the sign and the
 *      spread of the old mosaic (see MACRO_GAIN), with the regularity taken out.
 *   G  the colour tile's VARIANT: the shader cuts it into eight bands and
 *      draws each band's ground from its own offset of the tile, cross-fading
 *      at the band edges (Inigo Quilez's two-fetch repeat break). A band runs
 *      about 22 m (measured), so the 11 m tile stops lining up in rows.
 *   B  the tile's lookup shear along one diagonal. Smooth over 100 m and more,
 *      so it moves the tile without visibly stretching it.
 *   A  dry against fresh — a ZERO-MEAN hue lean, yellower where it is high.
 *
 * Every channel is read over its own measured mean, so the prairie's mean
 * albedo is exactly what it was with the mosaic (the July calibration in
 * terrain.js `prairieTexture`). Deterministic: a fixed seed, so a tool measures
 * the map the renderer draws. Reconstructed patchiness, like the mosaic it
 * replaces — there is no plant-community record in `data/` to draw it from, and
 * none is claimed (docs/LIBERTIES.md, T-2552).
 */

/** 512 px a side. */
export const MACRO_PX = 512;
/** Over 3,072 m — 6 m a texel, a repeat longer than the haze reach. */
export const MACRO_M = 3072;
/**
 * The patch channel's gain: (R - mean) x MACRO_GAIN has the standard deviation
 * the old mosaic had (0.66 — `sin*sin` contributes 0.5, the 0.6 diagonal 0.42),
 * so the tone it drives keeps its tuned strength. Measured, not chosen: it is
 * computed from the pixels by `macroStats`.
 */
export const MOSAIC_STD = 0.656;

/**
 * Periodic 2-D gradient noise on an `n`-cell lattice that wraps at the map's
 * edge, so the texture tiles seamlessly when it does repeat.
 */
function gradientNoise(n, seed) {
  let s = seed >>> 0;
  const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
  const gx = new Float32Array(n * n), gy = new Float32Array(n * n);
  for (let i = 0; i < n * n; i++) {
    const a = rnd() * Math.PI * 2;
    gx[i] = Math.cos(a); gy[i] = Math.sin(a);
  }
  const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);
  // (u, v) in [0, 1) of the map.
  return (u, v) => {
    const x = u * n, y = v * n;
    const x0 = Math.floor(x), y0 = Math.floor(y);
    const fx = x - x0, fy = y - y0;
    const dot = (ix, iy, dx, dy) => {
      const k = (((iy % n) + n) % n) * n + (((ix % n) + n) % n);
      return gx[k] * dx + gy[k] * dy;
    };
    const n00 = dot(x0, y0, fx, fy), n10 = dot(x0 + 1, y0, fx - 1, fy);
    const n01 = dot(x0, y0 + 1, fx, fy - 1), n11 = dot(x0 + 1, y0 + 1, fx - 1, fy - 1);
    const sx = fade(fx), sy = fade(fy);
    return (n00 + (n10 - n00) * sx) + ((n01 + (n11 - n01) * sx) - (n00 + (n10 - n00) * sx)) * sy;
  };
}

/**
 * A sum of periodic octaves, `cells` across the map each. `weights` is a number
 * (each octave that fraction of the one before) or one weight per octave.
 */
function fbm(cells, seed, weights = 0.5) {
  const oct = cells.map((n, i) => gradientNoise(n, seed + i * 7919));
  const w = Array.isArray(weights) ? weights : cells.map((_, i) => weights ** i);
  const norm = w.reduce((a, b) => a + b, 0);
  return (u, v) => {
    let sum = 0;
    for (let i = 0; i < oct.length; i++) sum += oct[i](u, v) * w[i];
    return sum / norm;
  };
}

/**
 * RGBA bytes for the map, row-major, `MACRO_PX` square. Row 0 is the map's
 * v = 0 edge; the shader reads it with no flip (a DataTexture).
 *
 * @returns {Uint8Array} length `MACRO_PX ** 2 * 4`
 */
export function macroPixels() {
  const S = MACRO_PX;
  // Cells across 3,072 m: 12 -> 256 m, 24 -> 128 m, 48 -> 64 m stands, 96 ->
  // 32 m, 192 -> 16 m ragged edges. The weight sits on the 32-64 m stands: put
  // on the 256 m swells it read as cloud shadow, the failure the old mosaic's
  // own comment names. The warp is coarser, so the stands bend into lobes and
  // lanes instead of sitting on a lattice.
  const tone = fbm([12, 24, 48, 96, 192], 20261018, [0.45, 0.8, 1.0, 0.85, 0.55]);
  // The tile's VARIANT index (G): which offset of the colour tile a stretch of
  // ground draws (the shader's repeat break). 128 m and 64 m and a little 32 m
  // only: the shader cuts it into eight bands, and an index with finer detail
  // packed their edges a few metres apart, where they drew as swirls.
  const variant = fbm([24, 48, 96], 20261022, [1.0, 0.5, 0.2]);
  // The smooth fields — the warp, the shear and the dry lean — change over a
  // hundred metres and more, so they are evaluated on a quarter-resolution grid
  // and read back bilinearly. Exact enough for a field that slow, and it keeps
  // the whole map near a tenth of a second on a laptop core.
  const L = S / 4;
  const fields = [fbm([3, 6, 12], 20261016), fbm([3, 6, 12], 20261017),
    fbm([8, 16], 20261019), fbm([5, 10, 20], 20261021, 0.6)];
  const low = fields.map(() => new Float32Array(L * L));
  for (let y = 0; y < L; y++) {
    for (let x = 0; x < L; x++) {
      for (let f = 0; f < fields.length; f++) low[f][y * L + x] = fields[f](x / L, y / L);
    }
  }
  const lerpLow = (g, u, v) => {
    const x = u * L, y = v * L;
    const x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
    const at = (i, j) => g[((j + L) % L) * L + ((i + L) % L)];
    return (at(x0, y0) * (1 - fx) + at(x0 + 1, y0) * fx) * (1 - fy)
         + (at(x0, y0 + 1) * (1 - fx) + at(x0 + 1, y0 + 1) * fx) * fy;
  };
  const WARP = 0.07;   // of the map: about 200 m of bend at most
  const smooth = (a, b, x) => {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  };
  const data = new Uint8Array(S * S * 4);
  const byte = (x) => Math.max(0, Math.min(255, Math.round(x * 255)));
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const u = x / S, v = y / S;
      const wu = u + WARP * lerpLow(low[0], u, v), wv = v + WARP * lerpLow(low[1], u, v);
      // Patches with edges: a prairie's lush and thin stands meet over metres,
      // not over a whole cell, so the warped field is pushed toward its two
      // ends and kept partly linear so the middle ground is not flat.
      const t = tone(wu, wv);
      const patch = 0.5 * smooth(-0.16, 0.16, t) + 0.5 * (t * 1.4 + 0.5);
      const k = (y * S + x) * 4;
      data[k] = byte(patch);
      data[k + 1] = byte(0.5 + 1.6 * variant(u, v));
      data[k + 2] = byte(0.5 + 1.2 * lerpLow(low[2], u, v));
      data[k + 3] = byte(0.5 + 1.4 * lerpLow(low[3], u, v));
    }
  }
  return data;
}

/**
 * Each channel's mean (0-1) and the patch channel's standard deviation, measured
 * from the pixels — the shader reads every channel over its mean, so what the map
 * moves around the ground it never adds to it.
 */
export function macroStats(data) {
  const n = data.length / 4;
  const mean = [0, 0, 0, 0];
  for (let i = 0; i < data.length; i += 4) for (let c = 0; c < 4; c++) mean[c] += data[i + c];
  for (let c = 0; c < 4; c++) mean[c] /= n * 255;
  let v = 0;
  for (let i = 0; i < data.length; i += 4) v += (data[i] / 255 - mean[0]) ** 2;
  const std = Math.sqrt(v / n);
  return { mean, patchStd: std, gain: MOSAIC_STD / std };
}
