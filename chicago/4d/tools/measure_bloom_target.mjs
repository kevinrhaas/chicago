/**
 * measure_bloom_target.mjs — R-W4c(b1): can the flower-load target be re-derived?
 *
 *   node tools/measure_bloom_target.mjs                  the four sections
 *   node tools/measure_bloom_target.mjs --shots /tmp/critic/desktop
 *   node tools/measure_bloom_target.mjs --assert         hold them to the numbers below
 *
 * WHY THIS EXISTS. R-W4c(a) measured that the flower-load recipe misses 94.5 %
 * of the bloom it is sorting, and it ruled that the tuning half's FIRST job is
 * to re-derive the 4-6 % target "with a method of known recall, before it tunes
 * anything — otherwise the tuning half will chase a bar that was never on this
 * scale". This is that job. Its answer is no: the target cannot be re-derived
 * from anything in this repository, and three of the four sections below are the
 * proof. The fourth is the route that does exist.
 *
 * The target's stated derivation (STATUS §00, from the 2026-08-10 prairie sweep)
 * is: the recipe read 12.91 % on a restoration planting and 1.79-5.54 % on a
 * never-plowed remnant, so the honest target for unmanaged 1835 prairie is 4-6 %.
 * Every clause of that is checked here.
 *
 * §1 THE SOURCE. Lists every committed photograph and searches the source
 * records for the remnant. There is no never-plowed remnant photograph in this
 * repository and no source record for one: the remnant reading appears exactly
 * once, inside the record of the photograph that is not the remnant, citing
 * nothing. Half the target's derivation is therefore unsourced.
 *
 * §2 THE READING. Runs the COMMITTED recipe on the committed photograph. It does
 * not reproduce 12.91 %, on the full frame or on any sub-region, so the other
 * half of the derivation does not reproduce either.
 *
 * §3 THE INSTRUMENT. R-W4c(a) diagnosed the recipe exactly — the plant test runs
 * first and swallows every yellow-through-cyan pixel — and the repair that
 * diagnosis implies is to run the flower test first. Measured against the
 * subtraction ground truth, that repair FAILS: recall rises and precision
 * collapses, because the recipe's near-perfect precision was the plant test's
 * pre-filter and never the flower test's discrimination. So the target cannot be
 * rescued by re-reading the photograph with a fixed recipe either.
 *
 * §4 THE BAR THAT DOES EXIST. Every flowering forb in `data/flora/zones/` carries
 * a `density_per_ha` and an inflorescence `size_m`, both sourced. Heads as discs
 * of diameter `size_m`, that is a bloom fraction IN PLAN, by arithmetic, from
 * committed records — the first bloom figure in this project that needs neither a
 * classifier nor a photograph. IT IS NOT THE SAME QUANTITY AS `flower.load` OR
 * `flower.bloom`, which are screen-space readings at an oblique pose, and the
 * conversion between them is not attempted here. It is quoted as what the data
 * specifies, not as a target.
 *
 * ON THE PHOTOGRAPH AND ITS LICENCE. §2 decodes a committed JPEG by shelling out
 * to Pillow and writing a PNG to the system temp directory, never into this
 * repository — a transient format conversion for a measurement, which is why
 * `assets/LICENSES.md` says of these files "it is measured, not sampled". No
 * crop, no resample, no derived asset, nothing committed, nothing published.
 * Without Pillow §2 says how to get it and carries on, the way
 * `tools/measure_reference.py` does. This tool is NOT part of `tools/check.sh`:
 * §2 needs Pillow and §3 needs frames from `tools/critic_shots.mjs --metrics`,
 * and the gate's promise is that it runs in seconds with no dependencies.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { decodePng, landSkyBoundary, labL, hueSat, measure } from './critic_metrics.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const flag = (n) => argv.includes(n);
const value = (n, d) => {
  const i = argv.indexOf(n);
  return i > -1 && argv[i + 1] ? argv[i + 1] : d;
};
const SHOTS = path.resolve(value('--shots', '/tmp/critic/desktop'));
const ASSERT = flag('--assert');

const pct = (v) => (v === null || v === undefined ? '   —  ' : `${(v * 100).toFixed(2)} %`);
const problems = [];
const check = (label, got, want, tol) => {
  if (!ASSERT) return;
  if (got === null || got === undefined || Math.abs(got - want) > tol) {
    problems.push(`${label}: ${got} where R-W4c(b1) committed ${want} (±${tol})`);
  }
};

/**
 * The recipe's two tests, and the repair R-W4c(a)'s diagnosis implies.
 * 1 plant, 2 flower, 3 neither. `flowerFirst` swaps which one runs first, which
 * is the whole of the repair — the tests themselves are the committed ones,
 * copied from `critic_metrics.mjs` alongside the `hueSat` it exports.
 */
function classify(r, g, b, flowerFirst) {
  const { hue, sat } = hueSat(r, g, b);
  const L = labL(r, g, b);
  const plant = hue >= 50 && hue < 180 && sat >= 0.08;
  const flower = (sat >= 0.25 && L >= 60) || (sat <= 0.12 && L >= 75);
  if (flowerFirst) return flower ? 2 : (plant ? 1 : 3);
  return plant ? 1 : (flower ? 2 : 3);
}

/** `load` over one image's ground, under either ordering. */
function scorePhoto(img, flowerFirst) {
  const { boundary } = landSkyBoundary(img);
  const W = img.width; const H = img.height; const d = img.data;
  let f = 0; let p = 0;
  for (let x = 0; x < W; x++) {
    for (let y = Math.min(boundary[x], H); y < H; y++) {
      const q = (y * W + x) * 4;
      const c = classify(d[q], d[q + 1], d[q + 2], flowerFirst);
      if (c === 2) f++; else if (c === 1) p++;
    }
  }
  return f + p ? f / (f + p) : null;
}

// ---- §1 the source ------------------------------------------------------- //
//
// The claim under test: the target's lower reference is "a never-plowed
// remnant". A reading with no photograph behind it is an assertion, which is the
// one thing this project's provenance model exists to prevent.

console.log('§1 THE SOURCE — is there a never-plowed remnant photograph?\n');

const SRC = path.join(APP, 'data/sources');
const records = fs.readdirSync(SRC).filter((f) => f.endsWith('.json'))
  .map((f) => ({ file: f, json: JSON.parse(fs.readFileSync(path.join(SRC, f), 'utf8')) }));
const photos = records.filter((r) => r.json.type === 'photograph');
console.log(`  ${photos.length} photograph source records, of which the committed prairie frames are:`);
for (const p of photos) {
  const dir = path.join(SRC, 'assets', p.json.id);
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => /\.(jpe?g|png)$/i.test(f)) : [];
  if (!files.length) continue;
  console.log(`    ${p.json.id.padEnd(34)} ${p.json.describes_date}  ${p.json.citation.slice(0, 72)}`);
}

// The phrase, wherever it occurs in the records. It occurs once, and not in a
// record of a remnant.
const NEEDLE = /never-plowed|never plowed|virgin remnant|unplowed/i;
const hits = records.filter((r) => NEEDLE.test(JSON.stringify(r.json)));
console.log(`\n  records mentioning a never-plowed remnant: ${hits.length}`);
for (const h of hits) {
  console.log(`    ${h.json.id} — type "${h.json.type}", `
    + `which this project's own record calls ${h.json.id === 'saari_2018_dupage_tallgrass'
      ? 'a RESTORATION PLANTING and forbids quoting for this number' : 'something else'}`);
}
const remnantAssets = photos.filter((p) => NEEDLE.test(JSON.stringify(p.json))
  && p.json.id !== 'saari_2018_dupage_tallgrass');
console.log(`\n  VERDICT: ${remnantAssets.length
  ? `a remnant photograph is committed (${remnantAssets.map((r) => r.json.id).join(', ')}) — `
    + 'this section is out of date and the target may be re-derivable'
  : 'NO never-plowed remnant photograph is committed and no source record describes one. '
    + 'The 1.79–5.54 % reading — the target\'s entire lower reference — cites nothing, '
    + 'and appears only inside the record of the photograph that is not the remnant.'}`);
if (ASSERT && remnantAssets.length) {
  problems.push('§1: a remnant photograph now exists — re-derive the target and rewrite this tool');
}

// ---- §2 the reading ------------------------------------------------------ //
//
// The committed recipe, on the committed photograph, over the whole frame and
// over the sub-regions a "nearest quarter" reading could plausibly have meant.

console.log('\n§2 THE READING — does 12.91 % reproduce on the committed photograph?\n');

const PHOTO = path.join(SRC, 'assets/saari_2018_dupage_tallgrass/dupage_tallgrass_2018-07-24.jpg');
let photoLoad = null;
let photoFlowerFirst = null;
function toPng(jpg) {
  // Transient, outside the repository, never committed — see the header.
  const out = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'bloomtgt-')), 'frame.png');
  execFileSync('python3', ['-c',
    'import sys\nfrom PIL import Image\nImage.open(sys.argv[1]).convert("RGB").save(sys.argv[2])',
    jpg, out], { stdio: ['ignore', 'ignore', 'pipe'] });
  return out;
}
try {
  const png = toPng(PHOTO);
  const img = decodePng(fs.readFileSync(png));
  const whole = measure(img, {});
  photoLoad = whole.flower.load;
  console.log(`  ${'the full frame'.padEnd(22)} ${img.width}x${img.height}   `
    + `flower load ${pct(whole.flower.load)}   sky ${pct(whole.landSky.skyFraction)}`);
  // Sub-regions, because the sweep judged a "nearest quarter" and a crop is the
  // only way its figure could have been higher than the frame's.
  const H = img.height;
  for (const [name, top] of [['the nearest quarter', 0.75], ['the nearer half', 0.5]]) {
    const y0 = Math.floor(H * top);
    const sub = { width: img.width, height: H - y0, data: img.data.slice(y0 * img.width * 4) };
    const m = measure(sub, {});
    console.log(`  ${name.padEnd(22)} ${sub.width}x${sub.height}   flower load ${pct(m.flower.load)}`);
  }
  // THE ONE CANDIDATE CAUSE WITH A MOTIVE, TESTED AND REFUTED. §3 finds that the
  // render reads 12.93 % under the other test ordering, a hair from the 12.91 %
  // this section cannot reproduce — so the obvious explanation is that the
  // sweep's uncommitted harness ordered its tests the other way. It did not:
  // flower-first reads 25.82 % here, not 12.91 %. The coincidence at 12.9 % is
  // between two different images and means nothing.
  const ff = scorePhoto(img, true);
  photoFlowerFirst = ff;
  console.log(`  ${'flower test first'.padEnd(22)} ${img.width}x${img.height}   `
    + `flower load ${pct(ff)}   ← the §3 repair, on the photograph`);
  console.log('\n  VERDICT: 12.91 % does not reproduce — not on the full frame, not on a nearer crop, '
    + 'and not\n           under either ordering of the recipe\'s two tests. The committed recipe reads '
    + `${pct(photoLoad).trim()},`);
  console.log('           and 5.54 % is, to the digit, the figure this project attributes to the '
    + 'never-plowed\n           remnant it has no photograph of. That coincidence is recorded, not '
    + 'explained.');
  fs.rmSync(path.dirname(png), { recursive: true, force: true });
} catch (e) {
  console.log('  SKIPPED — this section decodes a JPEG and needs Pillow: pip install pillow');
  console.log(`  (${String(e.message).split('\n')[0].slice(0, 120)})`);
}
check('§2 the committed photograph\'s flower load', photoLoad, 0.0554, 0.0002);
check('§2 the same photograph, flower test first', photoFlowerFirst, 0.2582, 0.0005);

// ---- §3 the instrument --------------------------------------------------- //
//
// Ground truth is the subtraction R-W4c(a) built: a ground pixel that moved when
// the nine `flora-head-*` sets were hidden is a pixel a flower painted. Both
// classifiers are scored against it on the same pixels.

console.log('\n§3 THE INSTRUMENT — does running the flower test first repair the recipe?\n');

const STATIONS = ['prairie_west', 'prairie_south', 'river_bank'];
const scored = [];
for (const id of STATIONS) {
  const a = path.join(SHOTS, `${id}.png`);
  const b = path.join(SHOTS, `${id}__noflower.png`);
  if (!fs.existsSync(a) || !fs.existsSync(b)) continue;
  const img = decodePng(fs.readFileSync(a));
  const noh = decodePng(fs.readFileSync(b));
  const { boundary } = landSkyBoundary(img);
  const W = img.width; const H = img.height; const d = img.data; const nd = noh.data;
  const row = { id, truth: 0, ground: 0, variants: {} };
  const acc = { false: { f: 0, p: 0, hit: 0 }, true: { f: 0, p: 0, hit: 0 } };
  for (let x = 0; x < W; x++) {
    for (let y = Math.min(boundary[x], H); y < H; y++) {
      const p = (y * W + x) * 4;
      row.ground++;
      // The same 4-channel tolerance `critic_metrics.mjs` reports and defends.
      const moved = Math.max(Math.abs(d[p] - nd[p]), Math.abs(d[p + 1] - nd[p + 1]),
        Math.abs(d[p + 2] - nd[p + 2])) > 4;
      if (moved) row.truth++;
      for (const ff of [false, true]) {
        const c = classify(d[p], d[p + 1], d[p + 2], ff);
        if (c === 2) { acc[ff].f++; if (moved) acc[ff].hit++; } else if (c === 1) acc[ff].p++;
      }
    }
  }
  for (const ff of [false, true]) {
    const { f, p, hit } = acc[ff];
    row.variants[ff ? 'flowerFirst' : 'committed'] = {
      load: f + p ? f / (f + p) : null,
      recall: row.truth ? hit / row.truth : null,
      precision: f ? hit / f : null,
    };
  }
  scored.push(row);
}

if (!scored.length) {
  console.log(`  SKIPPED — no station frames under ${SHOTS}. Capture them with:`);
  console.log('    node tools/critic_shots.mjs --metrics --viewport desktop '
    + '--stations prairie_west,prairie_south,river_bank');
} else {
  // The last column is bloom OVER GROUND, which is `bloom.shareOfGround` and not
  // R-W4c(a)'s headline 2.19 % — that is `shareOfHued`, over the smaller
  // denominator `load` uses. Both are in the metrics; they are not the same number.
  console.log(`  ${'station'.padEnd(15)}${'instrument'.padEnd(15)}${'load'.padStart(9)}`
    + `${'recall'.padStart(9)}${'precision'.padStart(11)}${'bloom / ground'.padStart(16)}`);
  for (const r of scored) {
    const trueShare = r.truth / r.ground;
    for (const name of ['committed', 'flowerFirst']) {
      const v = r.variants[name];
      console.log(`  ${r.id.padEnd(15)}${name.padEnd(15)}${pct(v.load).padStart(9)}`
        + `${v.recall.toFixed(3).padStart(9)}${v.precision.toFixed(3).padStart(11)}`
        + `${name === 'committed' ? pct(trueShare).padStart(16) : ''}`);
    }
  }
  const west = scored.find((r) => r.id === 'prairie_west');
  if (west) {
    console.log('\n  VERDICT: the repair fails. At prairie_west recall rises '
      + `${west.variants.committed.recall.toFixed(3)} → ${west.variants.flowerFirst.recall.toFixed(3)} `
      + `and precision collapses ${west.variants.committed.precision.toFixed(3)} → `
      + `${west.variants.flowerFirst.precision.toFixed(3)},`);
    console.log('           calling ' + pct(west.variants.flowerFirst.load).trim()
      + ' of the ground flower where a flower painted ' + pct(west.truth / west.ground).trim()
      + '. The recipe\'s near-perfect\n           precision was the plant test\'s pre-filter, not the '
      + 'flower test\'s discrimination: the flower\n           test cannot tell a bloom pixel from a '
      + 'sunlit grass one. Ordering is not the whole bug.');
    check('§3 prairie_west committed recall', west.variants.committed.recall, 0.055, 0.002);
    check('§3 prairie_west flower-first recall', west.variants.flowerFirst.recall, 0.367, 0.005);
    check('§3 prairie_west flower-first precision', west.variants.flowerFirst.precision, 0.062, 0.005);
  }
}

// ---- §4 the bar that does exist ------------------------------------------ //

console.log('\n§4 THE BAR THAT DOES EXIST — bloom IN PLAN, from the committed records\n');

const ZONES = path.join(APP, 'data/flora/zones');
const bars = [];
for (const f of fs.readdirSync(ZONES).sort()) {
  const z = JSON.parse(fs.readFileSync(path.join(ZONES, f), 'utf8'));
  let lo = 0; let hi = 0; let counted = 0; let noDensity = 0;
  for (const s of z.species || []) {
    const j = s.july || {};
    if (j.phenology !== 'flowering' || !j.inflorescence) continue;
    const size = j.inflorescence.size_m;
    const dens = s.abundance?.density_per_ha;
    if (!size || !dens) { noDensity++; continue; }
    // A head as a disc of diameter `size_m`, which is the shape the record
    // states and the only one it states. Per hectare, so /10 000 m².
    lo += dens[0] * (Math.PI / 4) * size[0] ** 2 / 10000;
    hi += dens[1] * (Math.PI / 4) * size[1] ** 2 / 10000;
    counted++;
  }
  if (!counted && !noDensity) continue;
  bars.push({ id: z.id, lo, hi, counted, noDensity });
}
console.log(`  ${'zone'.padEnd(24)}${'bloom in plan'.padStart(18)}   species counted / stated by cover`);
for (const b of bars) {
  console.log(`  ${b.id.padEnd(24)}${(`${(b.lo * 100).toFixed(3)} – ${(b.hi * 100).toFixed(3)} %`).padStart(18)}`
    + `   ${String(b.counted).padStart(2)} / ${b.noDensity}`);
}
const mesic = bars.find((b) => b.id === 'z02_mesic_prairie');
const wet = bars.find((b) => b.id === 'z01_wet_prairie');
if (mesic && wet) {
  console.log(`\n  VERDICT: the mesic prairie the render's prairie stations stand on specifies `
    + `${(mesic.lo * 100).toFixed(3)}–${(mesic.hi * 100).toFixed(3)} %`);
  console.log(`           bloom in plan, the wet prairie ${(wet.lo * 100).toFixed(3)}–`
    + `${(wet.hi * 100).toFixed(3)} %. Against a 4–6 % target that is a factor of 20 to 200 —`);
  console.log('           but the two are DIFFERENT PROJECTIONS and the difference is expected: a '
    + 'head is\n           seen frontally from an eye at 1.6 m while the ground it stands on is '
    + 'foreshortened to\n           nothing. This is what the data specifies, not what a frame '
    + 'should show. What it does\n           settle is where a bloom change lives — `density_per_ha` '
    + 'and `size_m` are sourced record\n           fields, so raising the bloom is a DATA change '
    + 'needing source support, not a renderer knob.');
  check('§4 mesic prairie plan bloom, low', mesic.lo, 0.00027, 0.00002);
  check('§4 mesic prairie plan bloom, high', mesic.hi, 0.00219, 0.00002);
}

if (ASSERT) {
  console.log('');
  if (problems.length) {
    for (const p of problems) console.log(`FAIL  ${p}`);
    process.exit(1);
  }
  console.log('ASSERTIONS OK — every figure R-W4c(b1) committed still comes out of the inputs');
}
