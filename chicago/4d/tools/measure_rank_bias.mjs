/**
 * measure_rank_bias.mjs — TICKET T-0018 (ROADMAP K49(e)).
 *
 *   node tools/measure_rank_bias.mjs              the measurement
 *   node tools/measure_rank_bias.mjs --self-test  the red/green demonstration
 *   node tools/measure_rank_bias.mjs --keys N     independent layer keys (default 400)
 *
 * THE CLAIM UNDER TEST, quoted from `flora.js`'s own `stratum` doc block, where
 * K49(d) left it:
 *
 *   "Rank is a deterministic function of position inside the block, so a filter
 *    that runs AFTER the deal on a spatial rule of its own — `station()` refusing
 *    a building footprint or the far side of a waterline — selects a BIASED set
 *    of ranks, where an independent draw would have been filtered without bias.
 *    ... That is the leading explanation and it is not proven; K49(e) measures
 *    it. Do not reach for `stratum` in a heavily filtered layer until it has."
 *
 * K49(f) refuted it for the settled town by fixing something else — the fixed
 * grid — and left the riverbank's residual as all K49(e) had to explain. This
 * tool settles the MECHANISM rather than that one number, which is the right
 * subject: the number is a single row of a census that has moved many times
 * since, and the sentence above is a standing instruction to every future
 * parcel that touches a filtered layer.
 *
 * WHAT IT MEASURES. Two things, on the same deal:
 *
 *  1. **Is the accepted set of ranks biased?** Pool the ranks of every slot a
 *     filter accepts, over many blocks and many independent layer keys, and
 *     test that pool against uniform. A biased filter shows up as a rank
 *     histogram that leans; an unbiased one does not, however hard it thins.
 *
 *  2. **What does the filter cost?** The stratification's whole benefit is that
 *     a block's `u` are equally spaced, so a CDF band takes its exact count
 *     instead of a Poisson one. A filter that keeps m of n slots keeps an
 *     ARBITRARY m-subset, which is not equally spaced. That is a loss of
 *     precision — variance — and it is a different animal from bias. Reported
 *     as the species-mix deviation against an independent draw of the same size.
 *
 * IT MEASURES THE SHIPPED CODE, NOT A COPY OF IT. Every primitive in the deal —
 * `hash3`, `frac`, `feistel`, `stratum`, `blockPhase`, `morton`, `spread16`,
 * `vdc`, `stratumHalf`, `pick`, `dealt` — is EXTRACTED FROM
 * `renderers/web/js/flora.js` AT RUN TIME by slicing its source, not retyped
 * here. A rename or a rewrite in that file changes this tool's answer or fails
 * it by name; it cannot leave the tool quietly measuring last month's
 * arithmetic. `scatter`'s own index arithmetic is inline rather than a function,
 * so the four lines this tool reproduces are asserted to appear VERBATIM in the
 * shipped `scatter` before anything is dealt. That guard is the same shape as
 * the far-timber gate's "FAR_TIMBER renamed out from under the gate" assertion,
 * and for the same reason.
 *
 * WHY NOT IN THE BROWSER. `tools/measure_sward_draw.mjs` measures the placer
 * through the real renderer and is the right instrument for a question about
 * the drawn scene. This question is about the deal ITSELF — the rank of every
 * slot, including the ones the filter threw away, which nothing drawn can
 * report. So it runs on the arithmetic, and pays for that by extracting the
 * arithmetic rather than restating it.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const FLORA = path.join(APP, 'renderers/web/js/flora.js');

const argv = process.argv.slice(2);
const SELF_TEST = argv.includes('--self-test');
const KEYS = Number(argv[argv.indexOf('--keys') + 1]) || 400;

/* -------------------------------------------------------------------------- */
/* the shipped deal, extracted rather than retyped                            */
/* -------------------------------------------------------------------------- */

/** The declarations this tool runs on. Order matters only for readability —
 *  they are evaluated together in one scope, so hoisting resolves the rest. */
const WANT_FN = [
  'hash3', 'frac', 'feistel', 'stratum', 'blockPhase',
  'morton', 'spread16', 'vdc', 'stratumHalf', 'pick', 'dealt',
];
const WANT_CONST = ['STRAT_SALT', 'STRAT_BLOCK_SHIFT'];

/**
 * `function NAME(` at column 0, through to its OWN closing brace.
 *
 * Column-anchored on purpose: every one of these is a top-level declaration in
 * `flora.js`, and anchoring means a nested helper of the same name inside some
 * other function can never be picked up by mistake. If the file's style ever
 * changes so that these are not top-level, the extraction fails by name here
 * rather than silently returning something else.
 *
 * The end is found by BALANCING BRACES, not by looking for `}` in the first
 * column. The first version of this did the latter and it was wrong on the
 * first file it read: `frac` is a one-liner, so the search ran on for a hundred
 * and twelve lines and swallowed `const STRAT_SALT` along the way — which
 * failed loudly, as a duplicate declaration, rather than quietly. Strings and
 * comments are skipped, because a brace inside either is not a brace.
 */
function sliceFunction(src, name) {
  const head = new RegExp(`^function ${name}\\(`, 'm');
  const m = head.exec(src);
  if (!m) return null;
  let i = src.indexOf('{', m.index);
  if (i < 0) return null;
  let depth = 0;
  for (; i < src.length; i++) {
    const ch = src[i];
    if (ch === '/' && src[i + 1] === '/') { i = src.indexOf('\n', i); if (i < 0) return null; continue; }
    if (ch === '/' && src[i + 1] === '*') { i = src.indexOf('*/', i); if (i < 0) return null; i++; continue; }
    if (ch === '"' || ch === "'" || ch === '`') {
      const quote = ch;
      for (i++; i < src.length && src[i] !== quote; i++) if (src[i] === '\\') i++;
      continue;
    }
    if (ch === '{') depth++;
    else if (ch === '}' && --depth === 0) return src.slice(m.index, i + 1);
  }
  return null;
}

function sliceConst(src, name) {
  const m = new RegExp(`^const ${name} = [^;]+;`, 'm').exec(src);
  return m ? m[0] : null;
}

function loadDeal() {
  const src = fs.readFileSync(FLORA, 'utf8');
  const parts = [];
  const missing = [];
  for (const name of WANT_CONST) {
    const text = sliceConst(src, name);
    if (text) parts.push(text); else missing.push(`const ${name}`);
  }
  for (const name of WANT_FN) {
    const text = sliceFunction(src, name);
    if (text) parts.push(text); else missing.push(`function ${name}`);
  }
  if (missing.length) {
    console.error('REFUSING TO MEASURE — these are not in renderers/web/js/flora.js '
      + 'as top-level declarations any more:');
    for (const m of missing) console.error(`  ${m}`);
    console.error('This tool reads the shipped deal out of that file rather than keeping a');
    console.error('copy. Point it at the new names, or it would be measuring nothing.');
    process.exit(2);
  }

  // `scatter`'s index arithmetic is INLINE, so it cannot be sliced by name. The
  // four expressions reproduced in `dealBlock` below are asserted verbatim
  // instead: change `scatter` and this fails loudly rather than leaving the tool
  // measuring a deal the renderer no longer performs.
  const MIRRORED = [
    'const blockHash = hash3(bc, br, salt ^ (strata ? STRAT_SALT : LD_BLOCK_SALT));',
    '? blockPhase(bc, br, nSlots, globalShift)',
    'const base = ((c - ((c >> shiftBits) << shiftBits)) * span',
    '? stratum(base + k, nSlots, half, blockHash, shift)',
    'const globalShift = hash3(salt, STRAT_SALT, 0x9e3779b9) / 4294967296;',
    'const nSlots = span * span * perCell;',
  ];
  // WHAT THIS GUARD DOES NOT CATCH, stated rather than left to be discovered: it
  // asserts these lines still EXIST, so it fires on a rewrite or a deletion —
  // both demonstrated, rc=2 — and it does NOT fire on a new step ADDED to the
  // deal between them. Slicing `scatter` whole and diffing it would catch that
  // too, and would also go red every time someone edits a comment inside a
  // 90-line function, which is a gate nobody keeps. The named-line form is the
  // trade: it holds the arithmetic this tool reproduces, not the whole routine.
  const drifted = MIRRORED.filter((line) => !src.includes(line));
  if (drifted.length) {
    console.error('REFUSING TO MEASURE — scatter\'s deal has changed and this tool still');
    console.error('reproduces the old one. These lines are no longer in flora.js:');
    for (const d of drifted) console.error(`  ${d}`);
    process.exit(2);
  }

  const make = new Function(`${parts.join('\n\n')}\nreturn { ${[...WANT_CONST, ...WANT_FN].join(', ')} };`);
  return make();
}

/* -------------------------------------------------------------------------- */
/* one block of the matrix deal                                                */
/* -------------------------------------------------------------------------- */

/**
 * The ranks a block deals, in slot order, exactly as `scatter` computes them.
 *
 * `perCell` is 4 and `STRAT_BLOCK_SHIFT` is 2, so a block is 4×4 cells of 4
 * slots — 64 slots, the shipped matrix stratum. `slot.pos` is the slot's place
 * inside the block in cells, which is what a SPATIAL filter sees; `slot.u` is
 * what the CDF sees. The claim under test is that a rule on the first biases
 * the second.
 */
function dealBlock({ D, bc, br, salt, perCell = 4 }) {
  const shiftBits = D.STRAT_BLOCK_SHIFT;
  const span = 1 << shiftBits;
  const nSlots = span * span * perCell;
  const half = D.stratumHalf(nSlots);
  const globalShift = D.hash3(salt, D.STRAT_SALT, 0x9e3779b9) / 4294967296;
  const blockHash = D.hash3(bc, br, salt ^ D.STRAT_SALT);
  const shift = D.blockPhase(bc, br, nSlots, globalShift);
  const sub = Math.max(1, Math.round(Math.sqrt(perCell)));
  const slots = [];
  for (let dc = 0; dc < span; dc++) {
    for (let dr = 0; dr < span; dr++) {
      const base = (dc * span + dr) * perCell;
      for (let k = 0; k < perCell; k++) {
        const u = D.stratum(base + k, nSlots, half, blockHash, shift);
        // The rank the permutation actually assigned, recovered from `u` by
        // undoing the phase. This is the quantity the claim is about.
        const rank = Math.round(D.frac(u - shift) * nSlots - 0.5);
        slots.push({
          // Position inside the block, in cells plus the jittered sub-grid the
          // placer uses — the only thing a spatial rule can see.
          x: dc + (k % sub) / sub,
          y: dr + ((k / sub) | 0) / sub,
          u,
          rank: ((rank % nSlots) + nSlots) % nSlots,
        });
      }
    }
  }
  return { slots, nSlots };
}

/* -------------------------------------------------------------------------- */
/* the filters                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * The shapes a spatial filter actually makes in this scene, plus two controls.
 *
 * `station()` refuses a slot for reasons that are all GEOMETRY: it is inside a
 * building footprint (a disc or a rectangle), it is on the far side of a
 * waterline (a half-plane), it is in a street corridor (a stripe). Those three
 * are the real cases. `rank_low` and `blind` are the controls that make the
 * measurement mean something — one is biased by construction and MUST be
 * caught, the other is unbiased by construction and MUST NOT be.
 *
 * The geometric filters take an angle and an offset per block so the edge is
 * not aligned to the block grid, which is the honest case: a waterline does not
 * know where the blocks are.
 */
const FILTERS = {
  none: () => () => true,
  halfplane: (span, rnd) => {
    const th = rnd() * Math.PI * 2;
    const off = rnd() * span;
    return (s) => s.x * Math.cos(th) + s.y * Math.sin(th) > off - span * 0.7;
  },
  disc: (span, rnd) => {
    const cx = rnd() * span;
    const cy = rnd() * span;
    const r = span * 0.45;
    return (s) => (s.x - cx) ** 2 + (s.y - cy) ** 2 > r * r;
  },
  stripe: (span, rnd) => {
    const th = rnd() * Math.PI * 2;
    const off = rnd() * span;
    const w = span * 0.3;
    return (s) => Math.abs(s.x * Math.cos(th) + s.y * Math.sin(th) - off) > w;
  },
  // POSITIVE CONTROL — a filter that reads the rank itself. Nothing in the
  // renderer does this; it is here so a green result on the real shapes is a
  // measurement rather than an instrument that cannot go red.
  rank_low: (span, rnd, n) => (s) => s.rank < n * 0.55,
  // NEGATIVE CONTROL — refuses at the same rate, on nothing but a coin.
  blind: (span, rnd) => (s) => rnd2(s) > 0.35,
};
// A per-slot coin that does not touch rank or position order.
function rnd2(s) {
  let h = Math.imul((s.rank + 1) * 2654435761 ^ Math.round(s.u * 1e9), 0x9e3779b1);
  h ^= h >>> 15;
  return ((h >>> 0) % 100000) / 100000;
}

function rngFrom(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

/* -------------------------------------------------------------------------- */
/* the measurement                                                             */
/* -------------------------------------------------------------------------- */

/** Chi-square of the accepted ranks against uniform, over `bins` equal bins.
 *  Reported alongside its degrees of freedom so the number can be read without
 *  a table: a pool with no bias sits near `bins - 1`. */
function rankUniformity(ranks, n, bins = 16) {
  const counts = new Array(bins).fill(0);
  for (const r of ranks) counts[Math.min(bins - 1, Math.floor((r / n) * bins))]++;
  const exp = ranks.length / bins;
  if (exp <= 0) return { chi2: 0, df: bins - 1, n: 0, counts };
  let chi2 = 0;
  for (const c of counts) chi2 += ((c - exp) ** 2) / exp;
  return { chi2, df: bins - 1, n: ranks.length, counts };
}

/**
 * The recorded wet-prairie matrix list — the one `z05_riverbank_timber` reads,
 * and the row K49(e) was scoped at. Weights are the midpoints of the record's
 * own `cover_fraction` ranges, normalised; the exact compile is not what is
 * under test here, and rank uniformity does not depend on the weights at all.
 * They are here so the consequence can be stated in species rather than in
 * chi-square.
 */
function wetPrairieMatrix() {
  const doc = JSON.parse(fs.readFileSync(
    path.join(APP, 'data/flora/zones/z01_wet_prairie.json'), 'utf8'));
  const items = [];
  for (const s of doc.species) {
    const cf = s.abundance?.cover_fraction;
    if (!Array.isArray(cf)) continue;
    items.push({ id: s.id, weight: (cf[0] + cf[1]) / 2 });
  }
  const sum = items.reduce((a, b) => a + b.weight, 0);
  for (const it of items) it.weight /= sum;
  return { items, total: 1 };
}

/**
 * Deal a field, filter it, and report both readings.
 *
 * `share` is the matrix cover fraction — the fraction of slots that carry a
 * plant at all. The wet prairie records `matrix_fraction: 1.0`, so every
 * accepted slot is planted and `dealt` reduces to `pick`; the parameter is kept
 * because a sparser community is the interesting stress case and the tool
 * should not have to be edited to ask.
 */
function run({ D, filter, keys, blocks = 3, share = 1.0, subset, independent = false }) {
  const span = 1 << D.STRAT_BLOCK_SHIFT;
  const ranks = [];
  let accepted = 0;
  let dealtSlots = 0;
  let nSlots = 0;
  // Per-key deviations, NOT one pooled figure. Pooling answers the bias
  // question and nothing else: an unbiased filter's deviations cancel across
  // worlds and the pool tends to zero however noisy each world is. The census
  // reads ONE world through one window, so the reading that matches what it
  // sees is the deviation of a single realisation, averaged over many.
  const devs = [];
  for (let key = 0; key < keys; key++) {
    const salt = D.hash3(key + 1, 0x51ed270b, 0x1b873593);
    const drawn = new Map();
    for (let bc = 0; bc < blocks; bc++) {
      for (let br = 0; br < blocks; br++) {
        const block = dealBlock({ D, bc, br, salt });
        nSlots = block.nSlots;
        const keep = FILTERS[filter](span, rngFrom(D.hash3(bc, br, salt ^ 0x2545f491)), block.nSlots);
        const rnd = rngFrom(D.hash3(bc, br, salt ^ 0x7feb352d));
        for (const s of block.slots) {
          dealtSlots++;
          if (!keep(s)) continue;
          accepted++;
          ranks.push(s.rank);
          // `independent` is the pre-K49(d) behaviour and the yardstick the
          // stratification is worth measuring against: the same slots, the same
          // filter, but `u` drawn free instead of dealt off the block's grid.
          const item = D.dealt(subset, share, independent ? rnd() : s.u);
          if (item) drawn.set(item.id, (drawn.get(item.id) || 0) + 1);
        }
      }
    }
    const planted = [...drawn.values()].reduce((a, b) => a + b, 0);
    let dev = 0;
    for (const it of subset.items) dev += Math.abs((drawn.get(it.id) || 0) - planted * it.weight);
    if (planted) devs.push((dev / planted) * 100);
  }
  devs.sort((a, b) => a - b);
  const mean = devs.reduce((a, b) => a + b, 0) / (devs.length || 1);
  return {
    filter,
    kept: accepted / dealtSlots,
    uniformity: rankUniformity(ranks, nSlots),
    devPer100: mean,
    devP95: devs[Math.min(devs.length - 1, Math.floor(devs.length * 0.95))] ?? 0,
  };
}

function report(rows) {
  const w = Math.max(...rows.map((r) => r.filter.length), 6);
  console.log(`${'arm'.padEnd(w)}  slots kept  rank chi2 (df ${rows[0].uniformity.df})`
    + '   mix dev /100   p95');
  for (const r of rows) {
    console.log(`${r.filter.padEnd(w)}  ${(r.kept * 100).toFixed(1).padStart(9)} %`
      + `  ${r.uniformity.chi2.toFixed(1).padStart(14)}`
      + `  ${r.devPer100.toFixed(2).padStart(12)}`
      + `  ${r.devP95.toFixed(2).padStart(5)}`);
  }
}

/* -------------------------------------------------------------------------- */

const D = loadDeal();
const subset = wetPrairieMatrix();

if (SELF_TEST) {
  // The instrument, held to its own contract before any result is quoted.
  const CRIT = 37.7; // chi-square, 15 df, p = 0.001
  const rows = ['none', 'halfplane', 'disc', 'stripe', 'blind', 'rank_low']
    .map((filter) => run({ D, filter, keys: 400, subset }));
  rows.push({ ...run({ D, filter: 'none', keys: 400, subset, independent: true }),
    filter: 'independent' });
  report(rows);
  console.log('');
  let failed = 0;
  const by = Object.fromEntries(rows.map((r) => [r.filter, r]));
  const check = (ok, label, detail) => {
    console.log(`  ${ok ? 'ok   ' : 'FAIL '} ${label}${detail ? ` — ${detail}` : ''}`);
    if (!ok) failed++;
  };
  check(by.rank_low.uniformity.chi2 > CRIT,
    'the positive control is CAUGHT — a filter that reads rank fails uniformity',
    `chi2 ${by.rank_low.uniformity.chi2.toFixed(1)} > ${CRIT}`);
  check(by.blind.uniformity.chi2 < CRIT,
    'the negative control is NOT caught — an unbiased filter passes',
    `chi2 ${by.blind.uniformity.chi2.toFixed(1)} < ${CRIT}`);
  for (const f of ['halfplane', 'disc', 'stripe']) {
    check(by[f].kept < 0.9, `${f} really does thin the deal`,
      `${(by[f].kept * 100).toFixed(1)} % kept`);
  }
  check(by.none.uniformity.chi2 < CRIT,
    'an unfiltered deal is uniform in rank — the baseline the others are read against',
    `chi2 ${by.none.uniformity.chi2.toFixed(1)}`);
  check(by.rank_low.devPer100 > by.none.devPer100,
    'the positive control also moves the species mix, not only the histogram',
    `${by.rank_low.devPer100.toFixed(2)} > ${by.none.devPer100.toFixed(2)} per 100`);
  const ind = rows.find((r) => r.filter === 'independent');
  check(by.none.devPer100 < ind.devPer100,
    'an UNFILTERED stratified deal beats an independent one — the benefit exists at all',
    `${by.none.devPer100.toFixed(2)} < ${ind.devPer100.toFixed(2)} per 100`);
  for (const f of ['halfplane', 'disc', 'stripe']) {
    check(by[f].devPer100 > by.none.devPer100 && by[f].devPer100 < ind.devPer100,
      `${f} costs precision without losing all of it — the alternative to bias`,
      `${by.none.devPer100.toFixed(2)} < ${by[f].devPer100.toFixed(2)} < ${ind.devPer100.toFixed(2)}`);
  }
  console.log('');
  console.log(failed ? `SELF-TEST FAIL — ${failed} check(s)` : 'SELF-TEST PASS');
  process.exit(failed ? 1 : 0);
}

console.log(`rank bias under a spatial filter — ${KEYS} independent layer keys, `
  + '3x3 blocks each, matrix stratum (64 slots/block)');
console.log(`the list is z01_wet_prairie's recorded matrix, ${subset.items.length} species\n`);
const main = ['none', 'halfplane', 'disc', 'stripe', 'blind', 'rank_low']
  .map((filter) => run({ D, filter, keys: KEYS, subset }));
main.push({ ...run({ D, filter: 'none', keys: KEYS, subset, independent: true }),
  filter: 'independent' });
report(main);
console.log('\nA filter that reads only POSITION leaves the rank pool uniform, because the');
console.log('position-to-rank map is a Feistel permutation re-keyed per block on');
console.log('hash3(bc, br, salt ^ STRAT_SALT) — a spatial rule cannot know that key, so the');
console.log('ranks it accepts are an arbitrary subset, re-drawn independently in every');
console.log('block. `rank_low` is the control that shows the instrument can go red.');
console.log('\nWhat a filter DOES cost is the stratification: the surviving u are no longer');
console.log('equally spaced, so the deal slides back towards `independent`. That is');
console.log('precision, not accuracy — and it is still better than an independent draw.');

/* At census scale ---------------------------------------------------------- */

/**
 * The row that opened K49(e): `z05_riverbank_timber` reading `z01_wet_prairie`'s
 * matrix, which on 2026-08-23 draws **44** slots. A deviation figure over 44
 * slots is a small sample, and the question the ticket really asks — is this row
 * a fault or a draw? — is answered by the SPREAD, not by the mean.
 */
const CENSUS_SLOTS = 44;
console.log(`\nAT CENSUS SCALE — the riverbank row draws ${CENSUS_SLOTS} slots. `
  + 'What does a deviation that size look like');
console.log('when nothing at all is wrong? One block, thinned to about that count:\n');
for (const filter of ['halfplane', 'disc', 'blind']) {
  const r = run({ D, filter, keys: KEYS, subset, blocks: 1 });
  const drawnSlots = Math.round(64 * r.kept);
  console.log(`  ${filter.padEnd(10)} ~${String(drawnSlots).padStart(2)} slots drawn  `
    + `mean dev ${r.devPer100.toFixed(1).padStart(5)} /100  `
    + `p95 ${r.devP95.toFixed(1).padStart(5)} /100  `
    + `= ${(r.devPer100 * drawnSlots / 100).toFixed(2)} slots mean, `
    + `${(r.devP95 * drawnSlots / 100).toFixed(2)} at p95`);
}
console.log('\nRead a single census row against those, not against zero.');
