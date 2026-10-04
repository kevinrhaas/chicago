/**
 * turf-tile.js — T-2085, the town's short turf: its tile's PIXELS, the rule that
 * says which community is turf, and the noise the ground shader draws its
 * coarser scales from. Nothing here imports three.js, for the reason
 * `prairie-tile.js` and `shrub-grain.js` give: a tool can read the tile and the
 * bare share from Node, and the browser draws exactly what the tool read.
 *
 * WHAT IT IS FOR. The owner, 2026-10-04, asked for "a lower grass that might be
 * easier for you to depict and render with some strong textures and be
 * reusable so you don't have to spend much rendering on it". A sward 0.05-0.20 m
 * tall is a fraction of a pixel at ten metres, so on short turf the clump cards
 * of the mid and far bands were spending triangles on something a texture
 * carries. This tile is that texture, built the road's way (T-1797/T-1811): a
 * seeded grain-and-normal tile sampled in world space, the coarse 0.5-6 m
 * variation as value noise in the shader, and the recorded tones times the
 * grain. `flora.js` stops drawing the mid and far bands on the communities
 * `isTurfCommunity` selects, and `terrain.js` paints this under them.
 *
 * WHAT IS EVIDENCE AND WHAT IS NOT. The community, its species, their July
 * colours, its bare-soil share and its soil tones are the zone record's and its
 * palette's (`z10_settled_town`, `july_town_ruderal`); this module reads them
 * and decides none of them. The PATTERN — blade strokes, rosettes, crumbs, the
 * scale of the patches — is reconstructed, bounded by the dossier's "cropped,
 * patchy turf ... dotted with dung and hoof pugs" and the photographic
 * preparation's 0.5-2 m coherent growth. docs/LIBERTIES.md records it.
 */

/** 256 px over 2 m: 7.8 mm a texel, finer than a Poa blade is wide. */
export const TURF_TILE_PX = 256;
export const TURF_TILE_M = 2.0;

/**
 * THE RULE THAT MAKES A COMMUNITY TURF, read off its record rather than its id.
 * A community whose every matrix grass tops out at or under the dossier's own
 * height for the trampled halo (§ ZONE 10: 0.05-0.25 m) is drawn as turf. On
 * the committed records that is `z10_settled_town` alone — the next shortest
 * matrix is the riverbank timber's 0.7 m — so a community a later parcel crops
 * short becomes turf by its record and no list here has to learn its name.
 */
export const TURF_MAX_M = 0.25;

export function isTurfCommunity(record) {
  const matrix = (record?.species ?? []).filter((s) => s.role === 'matrix');
  return matrix.length > 0
    && matrix.every((s) => Array.isArray(s.height_m) && s.height_m[1] <= TURF_MAX_M);
}

/**
 * The scene-metre box an extent can reach: its polygon, its `include_polygons`
 * and its box, whichever it carries. Null for an extent with none of them (an
 * elevation band, a buffer, `everywhere` without a box), which the caller
 * treats as "no turf can be painted for this one" and says so.
 */
export function extentBounds(x) {
  const rings = [];
  if (Array.isArray(x?.polygon)) rings.push(x.polygon);
  for (const p of x?.include_polygons ?? []) rings.push(p);
  for (const p of x?.polygons ?? []) rings.push(p);
  let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
  for (const ring of rings) {
    for (const [e, n] of ring) {
      e0 = Math.min(e0, e); e1 = Math.max(e1, e);
      n0 = Math.min(n0, n); n1 = Math.max(n1, n);
    }
  }
  if (x?.box?.e && x?.box?.n) {
    e0 = Math.min(e0, x.box.e[0]); e1 = Math.max(e1, x.box.e[1]);
    n0 = Math.min(n0, x.box.n[0]); n1 = Math.max(n1, x.box.n[1]);
  }
  return Number.isFinite(e0) && e1 > e0 && n1 > n0 ? { e0, e1, n0, n1 } : null;
}

/**
 * The shader's value noise, in JS, statement for statement — `TURF_HEAD` in
 * terrain.js is the GLSL. Kept here so the bare share below is MEASURED off the
 * field the shader draws, not guessed at.
 */
function fract(v) { return v - Math.floor(v); }
function hash(x, y) {
  let qx = fract(x * 0.1031), qy = fract(y * 0.1031), qz = fract(x * 0.1031);
  const d = qx * (qy + 33.33) + qy * (qz + 33.33) + qz * (qx + 33.33);
  qx += d; qy += d; qz += d;
  return fract((qx + qy) * qz);
}
export function turfNoise(x, y) {
  const ix = Math.floor(x), iy = Math.floor(y);
  const fx = x - ix, fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy), b = hash(ix + 1, iy);
  const c = hash(ix, iy + 1), d = hash(ix + 1, iy + 1);
  return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy;
}

/**
 * The sod field the shader thresholds, in metres: 1.7 m patches, 0.62 m edges
 * and a 5.5 m drift. 0.5-2 m is the coherent scale the photographic study found
 * in grazed ground (docs/RESEARCH/1835_photographic_fabric_preparation.md § 1-4).
 */
export function turfSodField(e, n) {
  return 0.55 * turfNoise(e / 1.7, n / 1.7)
       + 0.30 * turfNoise(e / 0.62 + 7.3, n / 0.62 + 2.9)
       + 0.15 * turfNoise(e / 5.5 + 3.1, n / 5.5 + 11.7);
}

/**
 * THE CUT THAT LEAVES THE RECORD'S BARE SHARE BARE. `bare_soil_fraction` is an
 * areal fraction (z10: 0.45); the shader calls a point bare where the sod field
 * falls under this value. Found by bisection over a deterministic 160 m square
 * of the field, so the share a visitor sees is the record's to within the
 * sample's own error (about half a per cent), and a record that changes its
 * fraction moves the ground with no constant here to edit.
 */
export function bareCut(fraction) {
  const f = Math.min(0.95, Math.max(0, fraction ?? 0));
  if (f <= 0) return -1;
  const samples = [];
  for (let i = 0; i < 160; i++) {
    for (let j = 0; j < 160; j++) samples.push(turfSodField(i * 1.003 + 0.37, j * 0.997 + 0.61));
  }
  samples.sort((a, b) => a - b);
  return samples[Math.min(samples.length - 1, Math.floor(f * samples.length))];
}

/**
 * RGBA bytes for one tile, row-major, `TURF_TILE_PX` square, wrapping on every
 * side. R is HEIGHT read as grain (0 the floor between blades, 1 a blade tip);
 * G and B are the OpenGL tangent normal of that height, as the road's grit
 * carries it; A is 255. Deterministic: the seed is fixed.
 *
 * What is in it, all at metric scale over 2 m:
 *   crumbs   the soil floor — 4 cm and 1.5 cm value noise
 *   blades   7,200 short strokes, 2-6 cm, leaning with a weak common grain the
 *            way grazed turf is pushed by feet, tallest at the tip
 *   rosettes 26 plantain and clover rosettes, 6-12 cm across, flat and broad
 */
export function turfTilePixels() {
  const S = TURF_TILE_PX;
  let seed = 20261004;
  const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
  const h = new Float32Array(S * S);
  const wrap = (v) => ((v % S) + S) % S;
  const pxPerM = S / TURF_TILE_M;

  // The floor: crumbs at two scales, tiling because the lattice is in texels.
  const lattice = (cells) => {
    const g = new Float32Array(cells * cells);
    for (let i = 0; i < g.length; i++) g[i] = rnd();
    const at = (x, y) => g[(((y % cells) + cells) % cells) * cells + (((x % cells) + cells) % cells)];
    return (x, y) => {
      const gx = x * cells / S, gy = y * cells / S;
      const x0 = Math.floor(gx), y0 = Math.floor(gy);
      const fx = gx - x0, fy = gy - y0;
      const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
      return (at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx) * (1 - sy)
           + (at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx) * sy;
    };
  };
  const crumb4 = lattice(50);
  const crumb1 = lattice(128);
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) h[y * S + x] = 0.10 + 0.12 * crumb4(x, y) + 0.08 * crumb1(x, y);
  }
  const lift = (x, y, v) => {
    const k = wrap(Math.round(y)) * S + wrap(Math.round(x));
    if (v > h[k]) h[k] = v;
  };

  // Blades: a stroke from root to tip, height rising along it.
  const lean = 0.6;
  for (let i = 0; i < 7200; i++) {
    const x0 = rnd() * S, y0 = rnd() * S;
    const len = (0.02 + 0.04 * rnd()) * pxPerM;
    const a = lean + (rnd() - 0.5) * 2.6;
    const top = 0.55 + 0.45 * rnd();
    const steps = Math.ceil(len * 1.5);
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      lift(x0 + Math.cos(a) * len * t, y0 + Math.sin(a) * len * t, 0.30 + (top - 0.30) * t);
    }
  }
  // Rosettes: broad flat leaves radiating from a crown, lower than a blade tip.
  for (let i = 0; i < 26; i++) {
    const cx = rnd() * S, cy = rnd() * S;
    const leaves = 4 + Math.floor(rnd() * 4);
    const r = (0.03 + 0.03 * rnd()) * pxPerM;
    for (let l = 0; l < leaves; l++) {
      const a = (l / leaves) * Math.PI * 2 + rnd() * 0.5;
      for (let s = 0; s <= r; s += 0.5) {
        const w = Math.sin(Math.PI * s / r) * r * 0.32;
        for (let q = -w; q <= w; q += 0.5) {
          const px = cx + Math.cos(a) * s - Math.sin(a) * q;
          const py = cy + Math.sin(a) * s + Math.cos(a) * q;
          lift(px, py, 0.46 + 0.12 * (1 - Math.abs(q) / (w + 1e-6)));
        }
      }
    }
  }

  const data = new Uint8ClampedArray(S * S * 4);
  // Normal from the height by central differences, in the tile's own wrap. The
  // gain is the relief's strength: a blade's side is steep, a crumb's is not.
  const gain = 2.2;
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const k = y * S + x;
      const dx = (h[y * S + wrap(x + 1)] - h[y * S + wrap(x - 1)]) * gain;
      const dy = (h[wrap(y + 1) * S + x] - h[wrap(y - 1) * S + x]) * gain;
      const len = Math.hypot(dx, dy, 1);
      data[k * 4] = Math.round(h[k] * 255);
      data[k * 4 + 1] = Math.round((-dx / len * 0.5 + 0.5) * 255);
      data[k * 4 + 2] = Math.round((-dy / len * 0.5 + 0.5) * 255);
      data[k * 4 + 3] = 255;
    }
  }
  return data;
}

/** The tile's mean grain, R channel, 0-1 — the divisor that keeps a tone's mean. */
export function turfTileMeanGrain(data = turfTilePixels()) {
  let sum = 0;
  for (let i = 0; i < data.length; i += 4) sum += data[i];
  return sum / (data.length / 4) / 255;
}
