/**
 * critic_metrics.mjs — the measurement half of the critic harness (RENDERING G0).
 *
 *   node tools/critic_metrics.mjs <file.png|dir> [...]     print JSON for each frame
 *
 * `tools/critic_shots.mjs` captures frames; this file turns them into the
 * numbers `docs/RENDERING.md` § 5 argues about, so a phase can prove its delta
 * instead of describing it. It reads PNGs and nothing else — which means the
 * SAME code measures a reference photograph and one of our frames. That matters
 * more than it sounds: every number in the 2026-08-10 prairie sweep came out of
 * a harness that no longer exists, so our figures and its reference figures were
 * never once produced by one implementation. Point this at a reference JPEG-
 * turned-PNG and the comparison is finally like for like.
 *
 * NO DEPENDENCIES, deliberately. The PNG decoder below is forty lines over
 * node:zlib, which is cheaper than owning an image library on a gate that has to
 * run in every sandbox.
 *
 * WHAT EACH NUMBER MEANS — the recipes are RENDERING Appendix B; the exact
 * thresholds are this file's, because Appendix B states the shape of each
 * measurement and not its constants. They are stated here rather than tuned per
 * call so that two runs, two phases and two years are comparable:
 *
 *   land/sky boundary   per column, the first row from the top whose next
 *                       `runPx` rows are ALL non-sky. Sky is blue-dominant
 *                       (B > R and B > G); ground is not, at any fog level this
 *                       renderer reaches. The sustained run is what separates
 *                       the GROUND line from the top of a tree: horizon timber
 *                       is two to four pixels tall and never satisfies it.
 *   horizon timber      in the band immediately above that line, a column counts
 *                       as BROKEN if a pixel there falls at least 3 luma below
 *                       — or 3 G−B above — the sky's own gradient EXTRAPOLATED
 *                       into the band from the twenty rows over it. A constant
 *                       sky reference does not work: the haze brightens steeply
 *                       toward the horizon and reports the air itself as trees.
 *                       BROKEN IS NOT TIMBERED: a gable end breaks a skyline as
 *                       surely as an oak, and `coverageAll` counts both. The
 *                       timber figure is `timberOnly`, measured on a second
 *                       capture of the same station with the town hidden, and it
 *                       is the one RENDERING § 5's ≥ 90 % target is about. See
 *                       the block over the recipe in `measure` for why the hue
 *                       discriminator was measured and abandoned.
 *   depth-band RMS      5x5 high-pass on Rec.709 luma over sRGB 0-255, in three
 *                       equal bands down from the median boundary. Collapse
 *                       toward the far band is the tell (§ 1 item 4).
 *   crown fine detail   over crown pixels (above the boundary, non-sky, and
 *                       G >= R so a clapboard gable is not a canopy):
 *                       RMS(I - blur3) / RMS(blur3 - blur9).
 *   shadow decile       mean CIE L* of the darkest tenth of ground pixels, plus
 *                       a count of literal (0,0,0) anywhere in frame.
 *   crown G-B           mean G-B over the brightest third of crown pixels, in
 *                       sRGB units, which is how § 1 item 8 is quoted.
 *   flower load         flower-hued / (plant-hued + flower-hued) over ground
 *                       pixels. Bright and saturated off-green, or near-white
 *                       and bright. HONEST LIMIT: a frame containing streets,
 *                       walls or roofs feeds them into the denominator or worse,
 *                       so this figure is only meaningful at the open-prairie
 *                       stations. It is reported everywhere and quoted there.
 *                       A SECOND HONEST LIMIT, measured by R-W4c: the hue cut at
 *                       50 deg that separates "plant" from "flower" runs through
 *                       the middle of a July prairie's own bloom, so this figure
 *                       is not a count of flowers. `flower.bloom` is, measured
 *                       on a third capture with the heads hidden, and it says
 *                       how much of this recipe's answer was ever about them.
 *
 * Every threshold above is a measurement convention, not a claim about 1835.
 *
 * Two exported colour helpers are not frame metrics and have no thresholds:
 * `relativeLuminance` (linear Y) and `weberContrast` (R-M1's exposure-invariant
 * scale). They live here so that anything measuring contrast in this project
 * measures it the same way — see the block over `weberContrast`.
 */

import zlib from 'node:zlib';
import fs from 'node:fs';
import path from 'node:path';

// ---- PNG ----------------------------------------------------------------- //

/** Decode an 8-bit non-interlaced PNG to `{ width, height, data }` RGBA. */
export function decodePng(buf) {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG');
  let pos = 8;
  let hdr = null;
  const idat = [];
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString('ascii', pos + 4, pos + 8);
    const body = buf.subarray(pos + 8, pos + 8 + len);
    if (type === 'IHDR') {
      hdr = {
        width: body.readUInt32BE(0),
        height: body.readUInt32BE(4),
        depth: body[8],
        color: body[9],
        interlace: body[12],
      };
    } else if (type === 'IDAT') idat.push(Buffer.from(body));
    else if (type === 'IEND') break;
    pos += 12 + len;
  }
  if (!hdr) throw new Error('no IHDR');
  if (hdr.depth !== 8 || hdr.interlace !== 0) {
    throw new Error(`unsupported PNG: depth ${hdr.depth}, interlace ${hdr.interlace}`);
  }
  const channels = { 0: 1, 2: 3, 4: 2, 6: 4 }[hdr.color];
  if (!channels) throw new Error(`unsupported PNG colour type ${hdr.color}`);

  const raw = zlib.inflateSync(Buffer.concat(idat));
  const { width: W, height: H } = hdr;
  const stride = W * channels;
  const out = new Uint8Array(W * H * 4);
  let prev = new Uint8Array(stride);
  let line = new Uint8Array(stride);
  let p = 0;
  for (let y = 0; y < H; y++) {
    const filter = raw[p++];
    for (let i = 0; i < stride; i++) {
      const x = raw[p + i];
      const a = i >= channels ? line[i - channels] : 0;
      const b = prev[i];
      const c = i >= channels ? prev[i - channels] : 0;
      let v;
      switch (filter) {
        case 0: v = x; break;
        case 1: v = x + a; break;
        case 2: v = x + b; break;
        case 3: v = x + ((a + b) >> 1); break;
        case 4: {
          const pa = Math.abs(b - c);
          const pb = Math.abs(a - c);
          const pc = Math.abs(a + b - 2 * c);
          v = x + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
          break;
        }
        default: throw new Error(`bad PNG filter ${filter}`);
      }
      line[i] = v & 0xff;
    }
    p += stride;
    for (let x = 0; x < W; x++) {
      const s = x * channels;
      const d = (y * W + x) * 4;
      if (channels >= 3) {
        out[d] = line[s]; out[d + 1] = line[s + 1]; out[d + 2] = line[s + 2];
        out[d + 3] = channels === 4 ? line[s + 3] : 255;
      } else {
        out[d] = out[d + 1] = out[d + 2] = line[s];
        out[d + 3] = channels === 2 ? line[s + 1] : 255;
      }
    }
    const swap = prev; prev = line; line = swap;
  }
  return { width: W, height: H, data: out };
}

// ---- colour -------------------------------------------------------------- //

const SRGB_LIN = new Float32Array(256);
for (let i = 0; i < 256; i++) {
  const c = i / 255;
  SRGB_LIN[i] = c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** CIE L* (D65), 0..100. Lightness only — hue lives in the raw channels. */
export function labL(r, g, b) {
  const Y = 0.2126 * SRGB_LIN[r] + 0.7152 * SRGB_LIN[g] + 0.0722 * SRGB_LIN[b];
  const f = Y > 0.008856 ? Math.cbrt(Y) : 7.787 * Y + 16 / 116;
  return 116 * f - 16;
}

/**
 * Rec.709 relative luminance in LINEAR light, 0..1, from gamma-encoded sRGB.
 * This is the Y that `labL` then compresses; kept separate because the two
 * answer different questions and one of them is not compressive.
 */
export function relativeLuminance(r, g, b) {
  return 0.2126 * SRGB_LIN[r] + 0.7152 * SRGB_LIN[g] + 0.0722 * SRGB_LIN[b];
}

/**
 * Weber contrast — `(Y_target − Y_background) / Y_background`, on linear
 * luminance, signed, `null` where the background carries no light to divide by.
 *
 * WHY THIS FILE OWNS IT, and why it is not a rewrite of `labL`. Both scales are
 * right about different things and R-M1 is the parcel that needs both.
 *
 *   `labL` is PERCEPTUAL. Equal steps are roughly equal perceived difference —
 *   but only under a fixed adaptation state. That precondition held for as long
 *   as the renderer's exposure was fixed, and R-W1 is the first change to break
 *   it: it preserved the road/ground ratio to within 0.4 % and still lost the
 *   road gate, because the whole scene got 14–17 % darker and ΔL* is
 *   compressive. ΔL* did not fail there; its assumption did.
 *
 *   Weber is EXPOSURE-INVARIANT by construction. Scale both terms by any k and
 *   the k cancels, so it answers "is the road distinguishable from the ground"
 *   without also answering "how bright is the scene". That is exactly the
 *   separation the owner ruled for on 2026-08-14: score contrast, and keep an
 *   absolute floor beside it, because contrast sensitivity genuinely collapses
 *   at low luminance and a ratio alone would pass a scene too dark to see
 *   anything in. Neither number is a replacement for the other.
 *
 * The BACKGROUND is the denominator, which is what makes it Weber rather than a
 * bare ratio: it is the surface the target is being picked out from. For the
 * road gate that is the same pixel with the street layer hidden, so a road on
 * grass and a road on mud are held to one standard.
 *
 * `trees.js` already reasons in this quantity against the reference photograph
 * (0.625 tree-mass-against-sky there, 0.655 in the scene) and `LIBERTIES.md`
 * quotes it, but until now nothing in `tools/` computed it, so every figure was
 * produced by hand at the point of use.
 */
export function weberContrast(targetY, backgroundY) {
  if (!(backgroundY > 0)) return null;
  return (targetY - backgroundY) / backgroundY;
}

/** Hue in degrees and HSL-style saturation, from gamma-encoded sRGB. */
// Exported so a second tool can score the flower recipe against the subtraction
// ground truth with THIS colour maths rather than a copy of it (R-W4c(b1)). A
// re-implementation that drifted by a degree would be a measurement of the copy.
export function hueSat(r, g, b) {
  const mx = Math.max(r, g, b);
  const mn = Math.min(r, g, b);
  const d = mx - mn;
  if (d === 0) return { hue: 0, sat: 0 };
  let h;
  if (mx === r) h = 60 * (((g - b) / d) % 6);
  else if (mx === g) h = 60 * ((b - r) / d + 2);
  else h = 60 * ((r - g) / d + 4);
  if (h < 0) h += 360;
  const l = (mx + mn) / 2 / 255;
  return { hue: h, sat: d / 255 / (1 - Math.abs(2 * l - 1) || 1) };
}

// ---- small array helpers ------------------------------------------------- //

/** Separable box blur of radius r over a W x H Float32Array. */
function boxBlur(src, W, H, r) {
  const tmp = new Float32Array(W * H);
  const out = new Float32Array(W * H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let s = 0; let n = 0;
      for (let i = -r; i <= r; i++) {
        const xx = x + i;
        if (xx < 0 || xx >= W) continue;
        s += src[y * W + xx]; n++;
      }
      tmp[y * W + x] = s / n;
    }
  }
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let s = 0; let n = 0;
      for (let i = -r; i <= r; i++) {
        const yy = y + i;
        if (yy < 0 || yy >= H) continue;
        s += tmp[yy * W + x]; n++;
      }
      out[y * W + x] = s / n;
    }
  }
  return out;
}

function rms(values) {
  if (!values.length) return null;
  let s = 0;
  for (const v of values) s += v * v;
  return Math.sqrt(s / values.length);
}

function round(v, places = 3) {
  return v === null || !Number.isFinite(v) ? null : Number(v.toFixed(places));
}

// ---- the measurements ---------------------------------------------------- //

/**
 * Horizon timber for ONE frame: per column, does anything break the skyline in
 * the band above the land/sky line. Split out of `measure` by R-W4a so the same
 * recipe can be run twice — once on the frame a visitor sees and once on the
 * same frame with the town's structures hidden — because run on one frame it
 * cannot tell an oak from a gable end. See the `horizonTimber` block in
 * `measure` for the whole argument and the numbers behind it.
 */
function timberCoverage(img, luma, gb, boundary, bandPx, fitRows) {
  const { width: W, height: H } = img;
  let timbered = 0; let measurable = 0;
  let timberedCentre = 0; let measurableCentre = 0;
  const hit = new Uint8Array(W);
  const measured = new Uint8Array(W);
  const c0 = Math.floor(W / 6);
  const c1 = Math.ceil(W * 5 / 6);
  for (let x = 0; x < W; x++) {
    const b = boundary[x];
    const bandTop = b - bandPx;
    if (b >= H || bandTop - fitRows < 0) continue;
    // Least squares on the sky ABOVE the band, extrapolated down into it: the
    // haze gradient is steep enough near the horizon that a flat reference
    // reports the air as timber.
    let sx = 0; let sy = 0; let sxx = 0; let sxyL = 0; let syG = 0; let sxyG = 0;
    for (let i = 0; i < fitRows; i++) {
      const y = bandTop - fitRows + i;
      const vL = luma[y * W + x];
      const vG = gb[y * W + x];
      sx += i; sxx += i * i; sy += vL; sxyL += i * vL; syG += vG; sxyG += i * vG;
    }
    const denom = fitRows * sxx - sx * sx;
    const slopeL = (fitRows * sxyL - sx * sy) / denom;
    const interceptL = (sy - slopeL * sx) / fitRows;
    const slopeG = (fitRows * sxyG - sx * syG) / denom;
    const interceptG = (syG - slopeG * sx) / fitRows;

    let broken = false;
    for (let y = bandTop; y < b; y++) {
      const t = y - (bandTop - fitRows);
      const predL = interceptL + slopeL * t;
      const predG = interceptG + slopeG * t;
      if (luma[y * W + x] <= predL - 3 || gb[y * W + x] >= predG + 3) { broken = true; break; }
    }
    measured[x] = 1;
    measurable++;
    if (broken) { hit[x] = 1; timbered++; }
    if (x >= c0 && x < c1) { measurableCentre++; if (broken) timberedCentre++; }
  }
  return {
    columnsMeasured: measurable,
    columnsBroken: timbered,
    coverageAll: measurable ? round(timbered / measurable, 4) : null,
    coverageCentralTwoThirds: measurableCentre
      ? round(timberedCentre / measurableCentre, 4) : null,
    hit,
    measured,
  };
}

/** Luma and G−B planes, the two the horizon recipe reads. */
function planes(img) {
  const { width: W, height: H, data } = img;
  const luma = new Float32Array(W * H);
  const gb = new Float32Array(W * H);
  for (let i = 0, p = 0; i < W * H; i++, p += 4) {
    luma[i] = 0.2126 * data[p] + 0.7152 * data[p + 1] + 0.0722 * data[p + 2];
    gb[i] = data[p + 1] - data[p + 2];
  }
  return { luma, gb };
}

/**
 * Per-column land/sky boundary. Returns an Int32Array of row indices; `H` means
 * the column never reaches sustained ground (all sky, or a frame that is all
 * ground has boundary 0).
 */
export function landSkyBoundary(img, runPx) {
  const { width: W, height: H, data } = img;
  const run = runPx ?? Math.max(8, Math.round(H / 33));
  const boundary = new Int32Array(W).fill(H);
  const sky = new Uint8Array(W * H);
  for (let i = 0, p = 0; i < W * H; i++, p += 4) {
    sky[i] = data[p + 2] > data[p] && data[p + 2] > data[p + 1] ? 1 : 0;
  }
  for (let x = 0; x < W; x++) {
    let streak = 0;
    for (let y = H - 1; y >= 0; y--) {
      if (sky[y * W + x]) streak = 0;
      else {
        streak++;
        if (streak >= run) boundary[x] = y;
      }
    }
  }
  return { boundary, sky, run };
}

/**
 * Every § 1 / § 5 metric for one frame. `opts.horizonBandPx` and `opts.runPx`
 * exist for experiments; the gate quotes the defaults.
 */
export function measure(img, opts = {}) {
  const { width: W, height: H, data } = img;
  const { boundary, sky, run } = landSkyBoundary(img, opts.runPx);

  const { luma, gb } = planes(img);

  // --- where the ground line sits, as one number for the banding ---------- //
  const sorted = [...boundary].sort((a, b) => a - b);
  const medianBoundary = sorted[Math.floor(sorted.length / 2)];
  const skyFraction = boundary.reduce((s, b) => s + Math.min(b, H), 0) / (W * H);

  // --- horizon timber ----------------------------------------------------- //
  //
  // R-W4a, 2026-08-15. THE RECIPE BELOW COUNTS SKYLINE BREAKS, NOT TIMBER, and
  // that is now said in the field names rather than in a footnote. A gable end
  // breaking the skyline satisfies it as surely as an oak — `prairie_south`
  // moved 0.364 → 0.436 on nineteen new roofs with no renderer change — so a
  // town parcel could hand W4 a pass it had not earned.
  //
  // THE DISCRIMINATOR THE ROADMAP NAMED DOES NOT WORK, and it was measured
  // before it was abandoned. G−B cannot separate a roof from a crown here: the
  // sky near the horizon is strongly blue-dominant, so EVERY non-sky pixel in
  // the band clears the +3 G−B test by a wide margin. Measured on the
  // 2026-08-15 `dev` build, desktop: the grey gables at `prairie_south` sit at
  // ΔG−B +22.4, and hazed timber at `prairie_west` ranges +0.1 to +17.5. The
  // channel is a not-sky detector, and its two populations overlap completely.
  // Nor does the fog leave a colour to sort them by — L17 makes extinction
  // total by 1500 m, so distant timber and a distant wall both converge on the
  // fog colour, which is the atmosphere doing its job.
  //
  // WHAT DOES WORK is asking the renderer to take the town away: the harness
  // captures the same station twice, once as the visitor sees it and once with
  // the `structures` group hidden, and this function is run on both. The second
  // frame's coverage is timber and only timber, by construction rather than by
  // heuristic — no threshold, no hue, nothing to tune. `timberOnly` below is
  // therefore the figure RENDERING § 5's ≥ 90 % target is about, and it cannot
  // move when a block lands. `structureOnlyColumns` is the size of the error
  // the old number was carrying.
  //
  // This file still reads PNGs and nothing else. The second frame is another
  // PNG, and a reference photograph — which has no second frame — simply
  // reports `timberOnly: null` and its skyline-break coverage as before.
  const bandPx = opts.horizonBandPx ?? Math.max(3, Math.round(H / 100));
  const fitRows = 20;
  const skyline = timberCoverage(img, luma, gb, boundary, bandPx, fitRows);

  let timberOnly = null;
  const bare = opts.withoutStructures ?? null;
  if (bare) {
    if (bare.width !== W || bare.height !== H) {
      throw new Error('withoutStructures frame is a different size');
    }
    const bp = planes(bare);
    const bareBoundary = landSkyBoundary(bare, opts.runPx).boundary;
    const t = timberCoverage(bare, bp.luma, bp.gb, bareBoundary, bandPx, fitRows);
    // A column the town breaks and the timber does not: the share of the old
    // headline number that was roofs. Counted over columns BOTH frames measure,
    // so a column the town moved out of measurable range cannot be scored.
    let structureOnly = 0; let common = 0;
    for (let x = 0; x < W; x++) {
      if (!skyline.measured[x] || !t.measured[x]) continue;
      common++;
      if (skyline.hit[x] && !t.hit[x]) structureOnly++;
    }
    timberOnly = {
      columnsMeasured: t.columnsMeasured,
      coverageAll: t.coverageAll,
      coverageCentralTwoThirds: t.coverageCentralTwoThirds,
      columnsComparable: common,
      structureOnlyColumns: structureOnly,
      structureShareOfBreaks: skyline.columnsBroken
        ? round(structureOnly / skyline.columnsBroken, 4) : null,
    };
  }

  // --- depth-band high-pass RMS ------------------------------------------- //
  const blur5 = boxBlur(luma, W, H, 2);
  const bands = { far: [], mid: [], near: [] };
  const groundRows = H - medianBoundary;
  const bandH = Math.floor(groundRows / 3);
  if (bandH > 0) {
    const names = ['far', 'mid', 'near'];
    for (let k = 0; k < 3; k++) {
      const y0 = medianBoundary + k * bandH;
      const y1 = y0 + bandH;
      for (let y = y0; y < y1; y++) {
        for (let x = 0; x < W; x++) {
          const i = y * W + x;
          bands[names[k]].push(luma[i] - blur5[i]);
        }
      }
    }
  }

  // --- crowns ------------------------------------------------------------- //
  const crown = [];
  for (let x = 0; x < W; x++) {
    for (let y = 0; y < Math.min(boundary[x], H); y++) {
      const i = y * W + x;
      if (sky[i]) continue;
      const p = i * 4;
      if (data[p + 1] < data[p]) continue;   // foliage is never red-dominant
      crown.push(i);
    }
  }
  const blur3 = boxBlur(luma, W, H, 1);
  const blur9 = boxBlur(luma, W, H, 4);
  const fine = rms(crown.map((i) => luma[i] - blur3[i]));
  const coarse = rms(crown.map((i) => blur3[i] - blur9[i]));

  let crownGB = null;
  if (crown.length) {
    const lums = crown.map((i) => luma[i]).sort((a, b) => a - b);
    const cut = lums[Math.floor(lums.length * 2 / 3)];
    const lit = crown.filter((i) => luma[i] >= cut);
    crownGB = lit.reduce((s, i) => s + gb[i], 0) / (lit.length || 1);
  }

  // --- shadows ------------------------------------------------------------ //
  const groundL = [];
  let literalBlack = 0;
  for (let x = 0; x < W; x++) {
    for (let y = Math.min(boundary[x], H); y < H; y++) {
      const p = (y * W + x) * 4;
      groundL.push(labL(data[p], data[p + 1], data[p + 2]));
    }
  }
  for (let p = 0; p < W * H * 4; p += 4) {
    if (data[p] === 0 && data[p + 1] === 0 && data[p + 2] === 0) literalBlack++;
  }
  groundL.sort((a, b) => a - b);
  const decile = groundL.slice(0, Math.max(1, Math.floor(groundL.length / 10)));
  const darkestDecileL = decile.length
    ? decile.reduce((s, v) => s + v, 0) / decile.length : null;

  // --- flower load -------------------------------------------------------- //
  //
  // THE RECIPE IS UNCHANGED IN VALUE AND IN NAME. It is the figure the 4-6 %
  // target was derived with — the reference photographs were read by this same
  // classifier — so replacing it would strand the target, and the 2026-08-14
  // baseline with it. What R-W4c adds is a measurement of what it counts.
  //
  // THE CUT AT hue 50 RUNS THROUGH THE BLOOM IT IS SORTING. A pixel is "plant"
  // if its hue is in [50, 180) and it carries any chroma at all, and that test
  // is applied FIRST, so no yellow-through-cyan pixel can ever be a flower
  // however brilliant it is. A July prairie's headline colour is the yellow
  // composite. Measured on this project's own committed records, the two
  // compass-plant-family yellows land on opposite sides of the cut half a
  // degree apart: `silphium_laciniatum` (228,200,62) is hue 49.880 and counts
  // as a FLOWER, `ratibida_pinnata` (232,206,72) is hue 50.250 and counts as
  // the GRASS it is being compared against. `opuntia_humifusa` 49.756 is a
  // flower; `nuphar_advena` 50.400 is not. Nobody looking at the frame could
  // tell those pairs apart, and the classifier puts one in the numerator and
  // the other in the denominator. Of the 97 inflorescence colours in
  // `data/flora/zones/`, 52 are called plant, 26 are called neither — dropped
  // from BOTH sides, which is where the saturated dark purples go — and 19 are
  // called flower.
  //
  // SO THE HARNESS ASKS THE RENDERER TO TAKE THE FLOWERS AWAY, the same
  // subtraction R-W4a used for the town. The nine `flora-head-*` instanced sets
  // are hidden and the station is photographed a third time; every ground pixel
  // that changed is a pixel a flower head painted, by construction — no hue, no
  // threshold on colour, nothing to tune, and nothing that moves when the
  // palette is re-tuned. `bloom.headPixels` is that count. `bloom.recipeRecall`
  // and `bloom.recipePrecision` then hold the recipe above to it: what share of
  // the real flower pixels did it call flowers, and what share of what it
  // called flowers were ever flowers at all.
  //
  // The heads cast no shadow (`flora.js` sets `castShadow = false` on every
  // instanced set), so hiding them cannot change a pixel they did not cover.
  // Both frames are read over the VISITOR frame's ground line, because the
  // question is about the visitor's ground: a scape breaking the skyline would
  // otherwise move the boundary and count its own removal as ground.
  let plantHued = 0; let flowerHued = 0;
  const CALLED_PLANT = 1; const CALLED_FLOWER = 2; const CALLED_NEITHER = 3;
  const called = opts.withoutFlowerHeads ? new Uint8Array(W * H) : null;
  for (let x = 0; x < W; x++) {
    for (let y = Math.min(boundary[x], H); y < H; y++) {
      const p = (y * W + x) * 4;
      const { hue, sat } = hueSat(data[p], data[p + 1], data[p + 2]);
      const L = labL(data[p], data[p + 1], data[p + 2]);
      if (hue >= 50 && hue < 180 && sat >= 0.08) {
        plantHued++;
        if (called) called[y * W + x] = CALLED_PLANT;
        continue;
      }
      const chromatic = sat >= 0.25 && L >= 60;
      const white = sat <= 0.12 && L >= 75;
      if (chromatic || white) {
        flowerHued++;
        if (called) called[y * W + x] = CALLED_FLOWER;
      } else if (called) {
        called[y * W + x] = CALLED_NEITHER;
      }
    }
  }

  // --- bloom, by subtraction ---------------------------------------------- //
  let bloom = null;
  const noHeads = opts.withoutFlowerHeads ?? null;
  if (noHeads) {
    if (noHeads.width !== W || noHeads.height !== H) {
      throw new Error('withoutFlowerHeads frame is a different size');
    }
    // A pixel counts as painted by a head when a channel moves by more than
    // this. The two frames come from ONE browser process with the animation
    // clock held and only a `visible` flag between them, so the honest value is
    // 0; the margin is here so that an antialiased edge resolving the other way
    // cannot be read as a flower. It is reported, because a threshold nobody
    // can see is a threshold nobody can check.
    const delta = opts.bloomDeltaTolerance ?? 4;
    const nd = noHeads.data;
    let headPixels = 0; let calledFlower = 0; let calledPlant = 0; let calledNeither = 0;
    let ground = 0;
    for (let x = 0; x < W; x++) {
      for (let y = Math.min(boundary[x], H); y < H; y++) {
        ground++;
        const p = (y * W + x) * 4;
        const moved = Math.max(
          Math.abs(data[p] - nd[p]),
          Math.abs(data[p + 1] - nd[p + 1]),
          Math.abs(data[p + 2] - nd[p + 2]),
        );
        if (moved <= delta) continue;
        headPixels++;
        const c = called[y * W + x];
        if (c === CALLED_FLOWER) calledFlower++;
        else if (c === CALLED_PLANT) calledPlant++;
        else calledNeither++;
      }
    }
    const hued = plantHued + flowerHued;
    bloom = {
      deltaTolerance: delta,
      groundPixels: ground,
      headPixels,
      // The share of the frame's ground a flower head actually paints. No
      // classifier is involved on either side of this ratio.
      shareOfGround: ground ? round(headPixels / ground, 5) : null,
      // The same numerator against the denominator `load` uses, which is the
      // closest this can get to an apples-to-apples reading of the 4-6 % target
      // without a fourth capture that hides the sward as well.
      shareOfHued: hued ? round(headPixels / hued, 5) : null,
      headPixelsCalledFlower: calledFlower,
      headPixelsCalledPlant: calledPlant,
      headPixelsCalledNeither: calledNeither,
      // Of the pixels a flower painted, the share the recipe called a flower.
      recipeRecall: headPixels ? round(calledFlower / headPixels, 4) : null,
      // Of the pixels the recipe called a flower, the share a flower painted.
      recipePrecision: flowerHued ? round(calledFlower / flowerHued, 4) : null,
    };
  }

  return {
    width: W,
    height: H,
    conventions: { runPx: run, horizonBandPx: bandPx, fitRows },
    landSky: {
      medianBoundaryRow: medianBoundary,
      skyFraction: round(skyFraction, 4),
    },
    horizonTimber: {
      columnsMeasured: skyline.columnsMeasured,
      // NOT timber — every skyline break, gables included. Kept under its old
      // name and its old value so the 2026-08-14 baseline stays comparable, and
      // never the figure a W4 acceptance quotes.
      coverageAll: skyline.coverageAll,
      coverageCentralTwoThirds: skyline.coverageCentralTwoThirds,
      // Timber and only timber, measured on the structure-free capture.
      timberOnly,
    },
    depthBandHighPassRms: {
      far: round(rms(bands.far), 2),
      mid: round(rms(bands.mid), 2),
      near: round(rms(bands.near), 2),
      bandHeightPx: bandH,
    },
    crown: {
      pixels: crown.length,
      fineDetailRatio: fine !== null && coarse ? round(fine / coarse, 3) : null,
      fineRms: round(fine, 2),
      coarseRms: round(coarse, 2),
      sunlitGminusB: round(crownGB, 2),
    },
    shadow: {
      darkestDecileL: round(darkestDecileL, 2),
      literalBlackPixels: literalBlack,
    },
    flower: {
      plantHuedPixels: plantHued,
      flowerHuedPixels: flowerHued,
      load: plantHued + flowerHued ? round(flowerHued / (plantHued + flowerHued), 4) : null,
      // Flowers and only flowers, measured on the head-free capture. Null for a
      // reference photograph, which has no second frame — the same way
      // `timberOnly` is.
      bloom,
    },
  };
}

/** Measure one PNG on disk. */
export function measureFile(file, opts) {
  return measure(decodePng(fs.readFileSync(file)), opts);
}

// ---- CLI ----------------------------------------------------------------- //

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  if (!args.length) {
    console.error('usage: node tools/critic_metrics.mjs <file.png|dir> [...]');
    process.exit(2);
  }
  const files = [];
  for (const a of args) {
    const st = fs.statSync(a);
    if (st.isDirectory()) {
      for (const f of fs.readdirSync(a).sort()) {
        if (f.endsWith('.png')) files.push(path.join(a, f));
      }
    } else files.push(a);
  }
  const out = {};
  for (const f of files) out[path.basename(f, '.png')] = measureFile(f);
  console.log(JSON.stringify(out, null, 2));
}
