/**
 * THE SCENE-DETAIL LADDER IS A LADDER — the gate half of T-0135's seal.
 *
 *   node tools/check_detail_ladder.mjs [--self-test]
 *
 * `renderers/web/js/main.js` declares three quality tiers and a triangle ceiling
 * for each. They are meant to be a LADDER — full the machine this project
 * targets, balanced the median visitor, light the weak-machine floor — and the
 * owner's ruling of 2026-09-21 is about what happens when they stop being one:
 * "three rungs that no longer ascend are not a quality ladder — they are three
 * numbers."
 *
 * `sealLadder()` in that file is the construction that answers it: the ceiling a
 * tier carries is the RUNNING MINIMUM down `DETAIL_ORDER`, so a rung typed too
 * high cannot BE too high. This is the gate beside it, and it is a gate rather
 * than only a smoke check for one reason: the dev gate is `check.sh` and nothing
 * else (docs/PIPELINE.md), so a structural fault that only the renderer smoke
 * can see is a fault that reaches the dev preview.
 *
 * It reads the COMMITTED SOURCE — the declaration and the function are sliced
 * out of `main.js` and imported, not copied — because a check standing on a copy
 * is checking the copy. `main.js` cannot be imported whole here (it pulls in
 * three.js and a DOM), which is why it is sliced.
 *
 * `--self-test` proves each assertion by breaking it, in the house idiom: every
 * line is meant to fire, and `check.sh` runs it through `selftest` so a green run
 * cannot be misread as a broken one.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const MAIN = path.join(here, '..', 'renderers', 'web', 'js', 'main.js');

/** Slice `name`'s declaration out of `src`, from its `const name` to `end`. */
function slice(src, start, end, what) {
  const i = src.indexOf(start);
  if (i < 0) throw new Error(`${what}: '${start}' is not in main.js any more`);
  const j = src.indexOf(end, i);
  if (j < 0) throw new Error(`${what}: '${start}' is not closed by '${end}'`);
  return src.slice(i, j + end.length);
}

async function loadLadder(src) {
  // The rung literals name the furniture reaches; they are not what this gate is
  // about, so they are stubbed rather than sliced in.
  const mod = 'const FURNITURE_REACH_BALANCED_M = null, FURNITURE_REACH_LIGHT_M = null;\n'
    + slice(src, 'const DETAIL_DECLARED = {', '\n};', 'the declared table') + '\n'
    + slice(src, "const DETAIL_ORDER = [", '];', 'the tier order') + '\n'
    + slice(src, 'const sealLadder = (declared, order) => {', '\n};', 'the seal') + '\n'
    + 'export { DETAIL_DECLARED, DETAIL_ORDER, sealLadder };\n';
  return import(`data:text/javascript;base64,${Buffer.from(mod).toString('base64')}`);
}

const n = (x) => x.toLocaleString('en-US');

/** The four things the ruling asks of the ladder, asserted on one table. */
function assertions({ DETAIL_DECLARED, DETAIL_ORDER, sealLadder }) {
  const out = [];
  const errs = [];
  const real = console.error;
  console.error = (m) => errs.push(m);
  let sealed;
  try { sealed = sealLadder(DETAIL_DECLARED, DETAIL_ORDER); } finally { console.error = real; }
  const rungs = DETAIL_ORDER.map((level) => ({ level, ...sealed[level] }));

  const notDescending = rungs.filter((r, i) => i > 0 && !(rungs[i - 1].declared > r.declared));
  out.push([notDescending.length === 0,
    'the declared ceilings descend — it is a ladder, not three numbers',
    rungs.map((r) => `${r.level} ${n(r.declared)}`).join(' > ')
      + (notDescending.length ? ` — ${notDescending.map((r) => r.level).join(', ')} does not sit under the rung above` : '')]);

  const clamped = rungs.filter((r) => r.clamped);
  out.push([clamped.length === 0,
    'no rung is running clamped — the table and the scene agree',
    clamped.length ? clamped.map((r) => `${r.level} declared ${n(r.declared)} running ${n(r.triangles)}`).join('; ')
      : 'every rung carries the ceiling its table declares']);

  out.push([errs.length === 0,
    'the seal is silent on a table that is already a ladder',
    errs.length ? errs[0] : 'no clamp reported at boot']);

  const unstated = rungs.filter((r) => !(r.protects || '').trim() || !(r.measured || '').trim());
  out.push([unstated.length === 0,
    'every rung says what it protects and what measurement set it',
    unstated.length
      ? unstated.map((r) => `${r.level} is missing ${[!r.protects && 'protects', !r.measured && 'measured'].filter(Boolean).join(' and ')}`).join('; ')
      : rungs.map((r) => `${r.level} ${n(r.declared)}`).join(' · ')]);
  return out;
}

/**
 * The construction itself, broken four ways. These are not assertions about the
 * committed table — they are assertions about `sealLadder`, which is the thing
 * that has to hold when somebody mistypes the table.
 */
function selfTest(sealLadder) {
  const order = ['full', 'balanced', 'light'];
  const quiet = (f) => {
    const errs = []; const real = console.error;
    console.error = (m) => errs.push(m);
    try { return { got: f(), errs }; } finally { console.error = real; }
  };
  const out = [];
  {
    const { got, errs } = quiet(() => sealLadder(
      { full: { triangles: 1460000 }, balanced: { triangles: 1280000 }, light: { triangles: 825000 } }, order));
    out.push([got.full.triangles === 1460000 && got.balanced.triangles === 1280000
      && got.light.triangles === 825000 && !got.light.clamped && errs.length === 0,
    'a table that is already a ladder passes through untouched and silent']);
  }
  {
    const { got, errs } = quiet(() => sealLadder(
      { full: { triangles: 1460000 }, balanced: { triangles: 1280000 }, light: { triangles: 1500000 } }, order));
    out.push([got.light.triangles === 1279999 && got.light.clamped === true
      && got.light.declared === 1500000 && errs.length === 1 && /light/.test(errs[0]),
    'a rung typed above the one above it runs clamped under it, marked, and shouted']);
  }
  {
    const { got } = quiet(() => sealLadder(
      { full: { triangles: 900000 }, balanced: { triangles: 900000 }, light: { triangles: 900000 } }, order));
    out.push([got.balanced.triangles === 899999 && got.light.triangles === 899998,
      'equal rungs are not a ladder either — they are pushed strictly under']);
  }
  {
    let threw = false;
    try { quiet(() => sealLadder({ full: { triangles: 10 } }, order)); } catch { threw = true; }
    out.push([threw, 'a level in the order and not in the table is loud, not silent']);
  }
  return out;
}

const src = fs.readFileSync(MAIN, 'utf8');
const ladder = await loadLadder(src);
const selfTesting = process.argv.includes('--self-test');
const rows = selfTesting
  ? selfTest(ladder.sealLadder).map(([ok, what]) => [ok, what, ''])
  : assertions(ladder);
let failed = 0;
for (const [ok, what, detail] of rows) {
  if (!ok) failed++;
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? `\n          ${detail}` : ''}`);
}
console.log(`  ${failed} failure(s)`);
process.exit(failed ? 1 : 0);
