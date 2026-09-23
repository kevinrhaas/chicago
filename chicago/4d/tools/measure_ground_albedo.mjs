#!/usr/bin/env node
/**
 * measure_ground_albedo.mjs — what the ground mesh actually averages inside each
 * substrate zone, against what that zone's record says it should.
 *
 * T-1055. `renderers/web/js/terrain.js` now paints the ground a flora zone's own
 * `ground.rgb` / `ground.wet_rgb` where the zone covers it, by taking the July
 * tile's luminance, dividing it by the tile's own mean and multiplying the
 * record's triple through it. That construction is SUPPOSED to make the mean
 * albedo inside a zone come out at exactly the recorded triple. "Supposed to" is
 * the part this tool removes: it runs the same arithmetic on the same pixels and
 * prints what comes out, so the claim in the PR is a measurement.
 *
 * It is not a screenshot test and does not need a browser — `prairie-tile.js`
 * imports nothing and generates the tile deterministically, which is why it was
 * lifted out of terrain.js.
 *
 * The one thing that could move the answer is the clamp the shader applies —
 * an albedo cannot exceed 1.0 — and on the committed records it does not bind:
 * the brightest texel is 1.378x the mean and the brightest zone's largest
 * channel product is 0.778. That is why every departure below reads 0.00, and
 * it is also why this tool is worth running again: a brighter triple, or a
 * retuned tile, would start clipping and the zeroes would move.
 *
 *   node tools/measure_ground_albedo.mjs            # report
 *   node tools/measure_ground_albedo.mjs --gate     # report, non-zero if adrift
 *
 * The gate tolerance is ONE sRGB unit per channel — a unit is the smallest
 * difference the 8-bit record can express, so anything inside it is the record.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { prairieTilePixels, prairieTileMeanLuma, srgbToLinear }
  from '../renderers/web/js/prairie-tile.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TOLERANCE_SRGB = 1.0;

/** Linear working value back to an sRGB 0-255 byte, for reporting. */
function linearToSrgb255(v) {
  const c = v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055;
  return c * 255;
}

const index = JSON.parse(
  readFileSync(path.join(ROOT, 'data/flora/index.json'), 'utf8'));
const pixels = prairieTilePixels();
const meanLuma = prairieTileMeanLuma(pixels);

/**
 * The mean of `min(1, recorded * grain)` over every texel of the tile — the
 * shader's own expression, with `chiWet` held at the end being measured and the
 * community mosaic left out exactly as zoneGlsl leaves it out.
 */
function meanAlbedo(rgb255) {
  const rec = rgb255.map((v) => srgbToLinear(v));
  const acc = [0, 0, 0];
  const n = pixels.length / 4;
  for (let i = 0; i < pixels.length; i += 4) {
    const grain = (0.2126 * srgbToLinear(pixels[i])
                 + 0.7152 * srgbToLinear(pixels[i + 1])
                 + 0.0722 * srgbToLinear(pixels[i + 2])) / meanLuma;
    for (let ch = 0; ch < 3; ch++) acc[ch] += Math.min(1, rec[ch] * grain);
  }
  return acc.map((v) => linearToSrgb255(v / n));
}

const zones = (index.zones || []).filter(
  (z) => z.extent?.kind === 'everywhere' && z.extent.box && z.plantable_in_scene !== false);

console.log(`tile mean linear luminance ${meanLuma.toFixed(6)}  `
  + `(sRGB ${linearToSrgb255(meanLuma).toFixed(1)} as a grey)`);
console.log(`${zones.length} substrate zone(s) painted by the ground mesh\n`);

let worst = 0;
for (const z of zones) {
  for (const [which, rec] of [['dry', z.ground_rgb], ['wet', z.ground_wet_rgb]]) {
    const got = meanAlbedo(rec);
    const dev = got.map((v, i) => v - rec[i]);
    worst = Math.max(worst, ...dev.map(Math.abs));
    console.log(`  ${z.id.padEnd(18)} ${which}  recorded `
      + `${rec.map((v) => String(v).padStart(3)).join(',')}   drawn `
      + `${got.map((v) => v.toFixed(1).padStart(5)).join(',')}   `
      + `Δ ${dev.map((v) => (v >= 0 ? '+' : '') + v.toFixed(2)).join(', ')}`);
  }
}

console.log(`\nworst departure ${worst.toFixed(2)} sRGB units `
  + `(tolerance ${TOLERANCE_SRGB.toFixed(1)})`);
if (process.argv.includes('--gate') && worst > TOLERANCE_SRGB) {
  console.error('FAIL: the ground does not average what the records state');
  process.exit(1);
}
