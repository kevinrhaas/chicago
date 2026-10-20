#!/usr/bin/env node
/**
 * THE FLORA WALK ON A WORKER IS THE FLORA WALK IN THE FRAME — T-2604.
 *
 *   node tools/check_lattice_kernel.mjs [--self-test] [--cameras N]
 *
 * A spread flora pass sends its lattice walks to the job pool
 * (`renderers/web/js/jobs/lattice-kernel.js`) and deals the slots that come back;
 * a one-frame pass walks in flora.js's own `scatter`. Both must hand `emit` the
 * same slots, in the same order, at the same yields, with the same xorshift
 * stream behind each, or a pass dealt over frames plants a different field from
 * one dealt at once. They are two texts — a module worker cannot import flora.js,
 * and flora.js's `hash3`/`stratum` stay where a dozen tools read them — so this
 * holds them together.
 *
 * It reads flora.js AT RUN TIME (`scatter`, `scatterOnPool`, `outsideFrustum`,
 * `rngFrom` and the deal helpers, sliced by name as measure_rank_bias.mjs slices
 * them), imports the kernel module itself, and walks every layer's own lattice
 * and several hundred random ones — every draw, cones of every width with and
 * without a margin, an aerial frustum, no cone at all, negative coordinates. Each
 * walk is driven four ways: `scatter` in the frame; `scatterOnPool` with its job
 * answered on a later task and resumed with MAY_WAIT, as `runPass` drives it;
 * `scatterOnPool` drained by `for…of` with the job never answered, as `settle`
 * and a late slice drive it; and (T-2683) `scatterOnPool` handed the reply to a
 * walk its pass sent ahead, which it must take without sending the walk again. A slot is compared bit for bit — position, distance,
 * rank, cell seed and the next three draws of its stream — and so is every yield.
 *
 * `--self-test` proves the gate can fail: a kernel that is one ulp off in one
 * slot's rank, drops one slot, swaps two, or yields a row late must each be
 * refused.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const FLORA = path.join(APP, 'renderers/web/js/flora.js');
const KERNEL = path.join(APP, 'renderers/web/js/jobs/lattice-kernel.js');

const argv = process.argv.slice(2);
const SELF_TEST = argv.includes('--self-test');
const CAMERAS = Number(argv[argv.indexOf('--cameras') + 1]) || 300;

const WANT_FN = ['scatter', 'scatterOnPool', 'outsideFrustum', 'rngFrom', 'hash3', 'frac',
  'feistel', 'stratum', 'blockPhase', 'morton', 'spread16', 'vdc', 'stratumHalf',
  'walkJob', 'walkKey', 'sendWalk'];
const WANT_CONST = ['CONE_KEEP_M', 'STRAT_SALT', 'STRAT_BLOCK_SHIFT', 'WALK_WAIT', 'MAY_WAIT',
  'HELD_SLOT'];

/** `function NAME(` or `function* NAME(` at column 0, to its own closing brace. */
function sliceFunction(src, name) {
  const m = new RegExp(`^function\\*? ${name}\\(`, 'm').exec(src);
  if (!m) return null;
  let i = src.indexOf('{', m.index);
  let depth = 0;
  for (; i < src.length; i++) {
    const ch = src[i];
    if (ch === '/' && src[i + 1] === '/') { i = src.indexOf('\n', i); continue; }
    if (ch === '/' && src[i + 1] === '*') { i = src.indexOf('*/', i) + 1; continue; }
    if (ch === '"' || ch === "'" || ch === '`') {
      const q = ch;
      for (i++; i < src.length && src[i] !== q; i++) if (src[i] === '\\') i++;
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

/** flora.js's walk, with the pool replaced by `pool` (see `drive`). */
function loadFlora(latticeSlots) {
  const src = fs.readFileSync(FLORA, 'utf8');
  const parts = [];
  const missing = [];
  for (const name of WANT_CONST) {
    const t = sliceConst(src, name);
    if (t) parts.push(t); else missing.push(`const ${name}`);
  }
  for (const name of WANT_FN) {
    const t = sliceFunction(src, name);
    if (t) parts.push(t); else missing.push(`function ${name}`);
  }
  if (missing.length) {
    console.error(`REFUSING TO CHECK — not found in renderers/web/js/flora.js: ${missing.join(', ')}`);
    process.exit(2);
  }
  const body = `${parts.join('\n\n')}\nreturn { scatter, scatterOnPool, walkJob, walkKey, WALK_WAIT, MAY_WAIT };`;
  // eslint-disable-next-line no-new-func
  return new Function('latticeSlots', 'pool', `
    const runJob = (kind, job) => pool.runJob(kind, job);
    const jobsOnWorkers = () => pool.onWorkers;
    ${body}`)(latticeSlots, POOL);
}

/** What the sliced flora code sees as the job pool; `drive` sets it per walk. */
const POOL = { onWorkers: false, runJob: () => new Promise(() => {}) };

/** A frustum that keeps part of the ring and drops part, and a ground to stand on. */
function aerial(cone, seed) {
  const a = (seed % 360) * Math.PI / 180;
  return { ...cone, eyeY: 140, halfHeight: 0.9, bodyRadius: 3.1,
    surface: (e, n) => 180 + 0.02 * e - 0.015 * n + Math.sin(e * 0.1) * 0.7,
    planes: [
      { normal: { x: Math.cos(a), y: 0.2, z: -Math.sin(a) }, constant: -30 },
      { normal: { x: -Math.sin(a), y: -0.1, z: -Math.cos(a) }, constant: 55 },
    ] };
}

/** Run one walk and record everything `emit` and the yields are given. */
async function drive(flora, mode, args, kernel) {
  const rec = [];
  const emit = (e, n, d, rng, cellSeed, u) => {
    rec.push(['slot', e, n, d, cellSeed, u, rng(), rng(), rng()]);
  };
  const [camE, camN, cell, perCell, radius, inner, salt, draw, cone] = args;
  if (mode === 'frame') {
    POOL.onWorkers = false;
    for (const y of flora.scatter(camE, camN, cell, perCell, radius, inner, salt, draw, cone, emit)) {
      rec.push(['yield', y.done, y.total]);
    }
    return rec;
  }
  // Both pool modes enter through `scatter`, with the pass's mark on the cone.
  POOL.onWorkers = true;
  const marked = { ...cone, jobs: true };
  if (mode === 'drain') {
    POOL.runJob = () => new Promise(() => {});
    let declined = 0;
    for (const y of flora.scatter(camE, camN, cell, perCell, radius, inner, salt, draw, marked, emit)) {
      // It is offered the wait once, declines it by not passing MAY_WAIT, and the
      // walk is taken there and then (`settle` ignores what a drain yields).
      if (y === flora.WALK_WAIT) { if (++declined > 1) throw new Error('a drain was asked to wait twice'); continue; }
      rec.push(['yield', y.done, y.total]);
    }
    return rec;
  }
  // 'pool': answered on a later task, by structured clone as a worker answers.
  POOL.runJob = (kind, job) => new Promise((resolve) => {
    setImmediate(() => resolve(structuredClone(kernel(structuredClone(job)))));
  });
  if (mode === 'ahead') {
    // T-2683: the walk was sent ahead by the pass (`begin`), from the walk the
    // last pass wrote down; the deal must take THAT reply and send nothing.
    const w = { cell, perCell, radius, inner, salt, draw };
    const job = flora.walkJob(camE, camN, w, marked);
    // T-2695: a walk sent ahead is a `sendWalk` record — its slots' reply, and
    // the zone answers that follow it (none here: the fixtures hold no ground).
    marked.ahead = new Map([[flora.walkKey(job), { slots: POOL.runJob('latticeSlots', job), zone: null }]]);
    marked.walks = [];
    POOL.runJob = () => { throw new Error('a walk sent ahead was sent again'); };
  }
  const gen = flora.scatter(camE, camN, cell, perCell, radius, inner, salt, draw, marked, emit);
  let waits = 0;
  for (;;) {
    const s = gen.next(flora.MAY_WAIT);
    if (s.done) break;
    if (s.value === flora.WALK_WAIT) {
      if (++waits > 50) throw new Error('the walk never came back');
      await new Promise((r) => setImmediate(r));
      continue;
    }
    rec.push(['yield', s.value.done, s.value.total]);
  }
  if (mode === 'ahead') {
    if (marked.ahead.size) throw new Error('the walk sent ahead was never taken');
    if (marked.walks.length !== 1) throw new Error('the walk was not written down for the next pass');
  } else if (!waits) throw new Error('a pool walk that never waited — the job was not sent');
  return rec;
}

/** Bit-for-bit: every number compared as its float64 bytes (so -0 ≠ 0, NaN = NaN). */
function same(a, b) {
  if (a.length !== b.length) return `${a.length} records against ${b.length}`;
  const fa = new Float64Array(1), fb = new Float64Array(1);
  const ua = new Uint32Array(fa.buffer), ub = new Uint32Array(fb.buffer);
  for (let i = 0; i < a.length; i++) {
    if (a[i][0] !== b[i][0]) return `record ${i}: ${a[i][0]} against ${b[i][0]}`;
    for (let k = 1; k < a[i].length; k++) {
      fa[0] = a[i][k]; fb[0] = b[i][k];
      if (ua[0] !== ub[0] || ua[1] !== ub[1]) {
        return `record ${i} (${a[i][0]}) field ${k}: ${a[i][k]} against ${b[i][k]}`;
      }
    }
  }
  return null;
}

/** Every layer's own lattice, as flora.js's passes call `scatter` (TUNE, full). */
function layerWalks() {
  const step = 0.6;
  const cone = { fe: 0.6, fn: 0.8, cos: Math.cos(62 * Math.PI / 180) };
  const at = [[412.37, -218.9], [-1033.2, 761.55], [0.3, 0.2]];
  const out = [];
  for (const [e, n] of at) {
    out.push([e, n, 0.74, 4, 7.6, 0, 0x51ed27, 'strata', cone], // near
      [e, n, 1.55, 4, 27 + 4 + step, 4.5 - 3 - step, 0x9e3779, 'strata', cone], // mid
      [e, n, 3.4, 4, 26 + 3 + step, 0, 0x2545f9, 'lattice', cone], // forb
      [e, n, 3.4, 4, 26 + 3 + step, 0, 0x7b5c1d, 'wild', cone], // wild shrubs
      [e, n, 3.4, 1, 62 + step, 16 - step, 0x3a91c7, 'lattice', { ...cone, margin: 0.6 }], // far band 1
      [e, n, 9.5, 1, 175 + step, 44 - step, 0x3a91c7 ^ 0x85ebca6b, 'lattice', cone], // far band 2
      [e, n, 3.4, 4, 140, 0, 0x2545f9, 'wild', aerial(cone, 37)]); // aerial
  }
  return out;
}

function rngOf(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

function randomWalks(count) {
  const r = rngOf(0x2604);
  const out = [];
  const draws = ['strata', 'lattice', 'wild'];
  for (let i = 0; i < count; i++) {
    const cell = 0.4 + r() * 11;
    const perCell = [1, 2, 3, 4, 9][Math.floor(r() * 5)];
    const radius = cell * (1 + r() * 14);
    const inner = r() < 0.4 ? 0 : radius * r() * 0.8;
    const camE = (r() - 0.5) * 4000, camN = (r() - 0.5) * 4000;
    const yaw = r() * Math.PI * 2;
    const kind = Math.floor(r() * 4);
    let cone = { fe: Math.sin(yaw), fn: Math.cos(yaw), cos: -0.3 + r() * 1.2 };
    if (kind === 1) cone.margin = r() * 2.5;
    if (kind === 2) cone = aerial(cone, i * 7);
    if (kind === 3) cone = null;
    out.push([camE, camN, cell, perCell, radius, inner, (r() * 4294967296) >>> 0,
      draws[Math.floor(r() * 3)], cone]);
  }
  return out;
}

/** Check every walk; null if all agree, else the first disagreement. */
async function check(kernel, walks) {
  const flora = loadFlora(kernel);
  let slots = 0;
  for (const [i, args] of walks.entries()) {
    const ref = await drive(flora, 'frame', args, kernel);
    slots += ref.filter((x) => x[0] === 'slot').length;
    for (const mode of args[8] ? ['pool', 'drain', 'ahead'] : []) {
      const got = await drive(flora, mode, args, kernel);
      const diff = same(ref, got);
      if (diff) return { walk: i, mode, diff, args };
    }
  }
  return { ok: true, slots };
}

const { latticeSlots } = await import(pathToFileURL(KERNEL).href);
const walks = [...layerWalks(), ...randomWalks(CAMERAS)];

if (SELF_TEST) {
  // Each of these is a kernel that is wrong in one way a port could be wrong.
  const target = (s) => s.u.length > 3;
  const broken = {
    'one slot one ulp off in its rank': (job) => {
      const s = latticeSlots(job);
      if (target(s)) { const i = s.u.length >> 1; s.u[i] = s.u[i] + Math.max(Number.EPSILON, Math.abs(s.u[i]) * Number.EPSILON); }
      return s;
    },
    'one slot dropped': (job) => {
      const s = latticeSlots(job);
      if (!target(s)) return s;
      const keep = (a) => a.filter((_, i) => i !== 1);
      return { ...s, e: keep(s.e), n: keep(s.n), d: keep(s.d), u: keep(s.u),
        cellSeed: keep(s.cellSeed), rng: keep(s.rng), rowEnd: s.rowEnd.map((x) => (x > 1 ? x - 1 : x)) };
    },
    'two slots swapped': (job) => {
      const s = latticeSlots(job);
      if (!target(s)) return s;
      for (const k of ['e', 'n', 'd', 'u', 'cellSeed', 'rng']) [s[k][0], s[k][1]] = [s[k][1], s[k][0]];
      return s;
    },
    'a stream one draw ahead': (job) => {
      const s = latticeSlots(job);
      if (target(s)) { let x = s.rng[2]; x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; s.rng[2] = x >>> 0; }
      return s;
    },
    'a row yielded late': (job) => {
      const s = latticeSlots(job);
      const k = s.rowEnd.findIndex((x, i) => i + 1 < s.rowEnd.length && s.rowEnd[i + 1] > x);
      if (k >= 0) s.rowEnd[k] = s.rowEnd[k + 1];
      return s;
    },
  };
  let bad = 0;
  for (const [name, kernel] of Object.entries(broken)) {
    const r = await check(kernel, walks.slice(0, 40));
    if (r.ok) { console.log(`  self-test | FAIL a kernel with ${name} passed`); bad++; } else {
      console.log(`  self-test | ok   a kernel with ${name} is refused (walk ${r.walk}, ${r.mode}: ${r.diff})`);
    }
  }
  const good = await check(latticeSlots, walks.slice(0, 40));
  if (!good.ok) { console.log(`  self-test | FAIL the real kernel failed: ${good.diff}`); bad++; }
  console.log(bad ? `\nFAIL — ${bad} self-test case(s)` : '\nPASS — the gate refuses every broken kernel and passes the real one');
  process.exit(bad ? 1 : 0);
}

const r = await check(latticeSlots, walks);
if (!r.ok) {
  const [camE, camN, cell, perCell, radius, inner, salt, draw, cone] = r.args;
  console.log(`FAIL — walk ${r.walk} (${draw}, cell ${cell}, ${perCell}/cell, radius ${radius}, inner ${inner},`
    + ` salt ${salt}, at ${camE}, ${camN}, cone ${cone ? (cone.planes ? 'aerial' : 'level') : 'none'}),`
    + ` ${r.mode} against the frame: ${r.diff}`);
  process.exit(1);
}
console.log(`PASS — ${walks.length} walks (${layerWalks().length} of the layers' own lattices), `
  + `${r.slots} slots, identical in the frame, on the pool, drained and sent ahead`);
