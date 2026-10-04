/**
 * grass-grain.js — the grass's fine relief, as PIXELS, and nothing else (T-2089).
 *
 * The road was made to look like ground by T-1797 and T-1811: one small seeded
 * tile of height and normal (`gritTilePixels`, 256 px over 1.6 m), sampled in
 * WORLD space, read as grain over its own mean and lit through its normal by the
 * real sun. The prairie beside it had colour and nothing else — `prairie-tile.js`
 * paints 11 m at 4 cm a texel and carries no relief — so at the road's edge the
 * dirt had a surface and the grass was a print. This is the grass's version of
 * the grit, in the grit's format, so the two read as one ground:
 *
 *   R  height, 0..1 — read as luminance grain (over the tile's own mean)
 *   G  normal east component, B  normal north component (OpenGL, 0.5 = flat)
 *
 * 256 px over 1.6 m, the grit's own density (6 mm a texel). What it draws, all
 * of it RECONSTRUCTED (docs/LIBERTIES.md): no source records the relief of a July
 * sward, so the scales are bounded by the plant and by the prairie tile above it —
 *
 *   tussocks   ~13 cm value noise: the bunch-grass crowns, raised
 *   leaf mass  ~4 cm value noise and a texel of speckle
 *   blades     2,400 short raised strokes, 3-9 cm long and a texel or two
 *              wide, laid at any bearing but denser on a tussock — a blade
 *              catches the light along its spine and shades the soil beside it
 *   thatch     260 longer flat strokes, 8-20 cm, lower than the blades: last
 *              year's litter lying between the crowns
 *
 * Coarser variation (clumps at a metre, the growth patches, the 15-48 m mosaic)
 * is NOT here: the prairie tile and the shader own it, which is the road's split
 * too. Like `prairie-tile.js` this module imports nothing, so a tool can measure
 * the tile the renderer draws, texel for texel.
 */

export const GRASS_GRAIN_PX = 256;
export const GRASS_GRAIN_M = 1.6;

/**
 * RGBA bytes for one tile, row-major, `GRASS_GRAIN_PX` square. Deterministic.
 *
 * @returns {Uint8ClampedArray} length `GRASS_GRAIN_PX ** 2 * 4`
 */
export function grassGrainPixels() {
  const S = GRASS_GRAIN_PX;
  let seed = 20891835;
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
  const tussock = octave(12);   // ~13 cm
  const leaf = octave(40);      // ~4 cm
  const h = new Float32Array(S * S);
  const tus = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const t = tussock(x, y);
      tus[y * S + x] = t;
      h[y * S + x] = 0.34 * t + 0.20 * leaf(x, y) + 0.10 * rnd();
    }
  }
  const wrap = (v) => ((v % S) + S) % S;
  // A stroke: a line of soft dabs from (cx, cy) along `ang`, its height tapering
  // to the tip, wrapping at the tile's edges so the tile still tiles.
  const stroke = (cx, cy, ang, len, width, amp) => {
    const dx = Math.cos(ang), dy = Math.sin(ang);
    const steps = Math.ceil(len * 2);
    const R = Math.ceil(width * 2);
    for (let s = 0; s <= steps; s++) {
      const f = s / steps;
      const px = cx + dx * len * f, py = cy + dy * len * f;
      const a = amp * (1 - 0.7 * f);
      for (let oy = -R; oy <= R; oy++) {
        for (let ox = -R; ox <= R; ox++) {
          // Distance across the stroke only, so a blade is a ridge, not a bead.
          const across = Math.abs(ox * -dy + oy * dx);
          if (across > width * 2) continue;
          const k = Math.exp(-(across * across) / (width * width) * 1.6) / (steps + 1) * 2.5;
          h[wrap(Math.floor(py) + oy) * S + wrap(Math.floor(px) + ox)] += a * k;
        }
      }
    }
  };
  // Thatch first, so the blades lie over it.
  for (let k = 0; k < 260; k++) {
    stroke(rnd() * S, rnd() * S, rnd() * Math.PI * 2, 13 + rnd() * 20, 0.9 + rnd() * 0.6,
      0.10 + 0.08 * rnd());
  }
  let placed = 0;
  for (let tries = 0; placed < 2400 && tries < 20000; tries++) {
    const cx = rnd() * S, cy = rnd() * S;
    // Denser on a crown: a blade is kept with the tussock's own height.
    if (rnd() > 0.25 + 0.95 * tus[wrap(Math.floor(cy)) * S + wrap(Math.floor(cx))]) continue;
    stroke(cx, cy, rnd() * Math.PI * 2, 5 + rnd() * 10, 0.6 + rnd() * 0.5, 0.22 + 0.16 * rnd());
    placed++;
  }
  // Normalised between the 0.5th and 99.5th percentiles, not the extremes: where
  // a dozen blades cross, the sum spikes, and a min-max range would spend most of
  // the byte on those few texels and leave the sward itself a dim grey.
  const sorted = Float32Array.from(h).sort();
  const lo = sorted[Math.floor(sorted.length * 0.005)];
  const hi = sorted[Math.floor(sorted.length * 0.995)];
  const data = new Uint8ClampedArray(S * S * 4);
  const H = (x, y) => Math.min(1, Math.max(0, (h[wrap(y) * S + wrap(x)] - lo) / (hi - lo)));
  // Slope per texel → normal, the grit's convention: row 0 is the tile's north
  // edge (the texture is flipped on upload), so north is DEcreasing y. A blade's
  // flank leans about 30° at the strongest — softer than the grit's clods,
  // because a sward is a mat and not a scatter of stones.
  const K = 5;
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const nx = -(H(x + 1, y) - H(x - 1, y)) * 0.5 * K;
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

/** The tile's mean height (R over 255) — the divisor the shader reads grain by. */
export function grassGrainMean(data = grassGrainPixels()) {
  let sum = 0;
  for (let i = 0; i < data.length; i += 4) sum += data[i];
  return sum / (data.length / 4) / 255;
}
