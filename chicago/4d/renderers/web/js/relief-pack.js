/**
 * relief-pack.js — the relief maps a page derives at load, packed in the row
 * order three uploads them. T-2300.
 *
 * `wall-relief.js` packs an `orl` (AO, roughness, the albedo ratio) from the
 * library's orm and basecolor, and `frontage.js` packs the board face's albedo
 * modulation from its basecolor. Both read the image through a canvas, whose
 * `getImageData` lists rows TOP first, and both hand the bytes to a
 * `THREE.DataTexture`, which three uploads with `flipY` false: data row 0 lands
 * at v = 0, the BOTTOM of the tile. The `normal_gl` and `orm` beside them are
 * plain image textures, uploaded with `flipY` true: the image's top row lands at
 * v = 1. Packed in canvas order, every derived map was therefore the relief's
 * mirror image along v — a board's dark knot sat a tile's height away from the
 * knot its normal map raised, and a log's checks were rough where the relief was
 * smooth. `fabric_proof/proof.js` never showed it: it loads its `orl.png` as an
 * image texture, flipped like its normal.
 *
 * So the packers write each texel to the row three will put where the image
 * texture puts its source: `bottomUp(r, h)`. Pure and three-free, so
 * `tools/check_relief_rows.mjs` runs them under node.
 */

/** The DataTexture row that a canvas row `r` of an `h`-row image belongs in. */
export function bottomUp(r, h) {
  return h - 1 - r;
}

const LUT = (() => {
  const lut = new Float32Array(256);
  for (let i = 0; i < 256; i += 1) {
    const c = i / 255;
    lut[i] = c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }
  return lut;
})();

/** Each texel's linear luminance (canvas order) and the map's mean. */
function luminance(rgba, n) {
  const lum = new Float32Array(n);
  let sum = 0;
  for (let i = 0, j = 0; i < n; i += 1, j += 4) {
    lum[i] = 0.2126 * LUT[rgba[j]] + 0.7152 * LUT[rgba[j + 1]] + 0.0722 * LUT[rgba[j + 2]];
    sum += lum[i];
  }
  return { lum, mean: sum / n };
}

/**
 * The wall's `orl`, from an orm and a basecolor of `px` x `px` canvas pixels:
 * R = AO, G = roughness (the library's own), B = 0.5 * L / mean(L), so a texel
 * can carry up to twice the mean (fabric_proof_1835_maps.py, verbatim).
 * Returns the bytes, bottom row first, and the mean roughness over 0..1.
 */
export function packOrl(orm, col, px) {
  const n = px * px;
  const { lum, mean: m } = luminance(col, n);
  const mean = Math.max(m, 1e-6);
  const data = new Uint8Array(n * 4);
  let roughSum = 0;
  for (let r = 0, i = 0; r < px; r += 1) {
    let k = bottomUp(r, px) * px * 4;
    for (let x = 0; x < px; x += 1, i += 1, k += 4) {
      const j = i * 4;
      data[k] = orm[j];
      data[k + 1] = orm[j + 1];
      data[k + 2] = Math.max(0, Math.min(255, Math.round(255 * Math.min(1, 0.5 * lum[i] / mean))));
      data[k + 3] = 255;
      roughSum += orm[j + 1];
    }
  }
  return { data, meanRough: Math.max(roughSum / n / 255, 1e-3) };
}

/**
 * The board face's albedo modulation, from a `w` x `h` canvas basecolor: each
 * texel's luminance over the map's mean, pulled toward 1 by `strength` and
 * stored under `headroom`, grey in RGB. Bottom row first.
 */
export function packGrain(base, w, h, strength, headroom) {
  const { lum, mean } = luminance(base, w * h);
  const data = new Uint8Array(w * h * 4);
  for (let r = 0, i = 0; r < h; r += 1) {
    let k = bottomUp(r, h) * w * 4;
    for (let x = 0; x < w; x += 1, i += 1, k += 4) {
      const m = 1 + strength * (lum[i] / mean - 1);
      const v = Math.max(0, Math.min(255, Math.round((255 * m) / headroom)));
      data[k] = v; data[k + 1] = v; data[k + 2] = v; data[k + 3] = 255;
    }
  }
  return data;
}
