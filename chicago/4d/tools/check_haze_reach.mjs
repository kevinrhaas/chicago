/**
 * THE AIR IS AS THICK AS THE GROUND APRON REQUIRES, AND NO THICKER (T-1635).
 *
 *   node tools/check_haze_reach.mjs [--json]
 *   node tools/check_haze_reach.mjs --self-test    prove each refusal by breaking it
 *
 * ## The promise this replaces
 *
 * `renderers/web/js/world.js`'s `HAZE_DENSITY` is not a look. docs/LIBERTIES.md
 * L17 carries each boundary vertex of the modelled terrain box outward as an
 * APRON — geometry for the horizon only, nothing out there modelled, sampled or
 * claimed — and the whole standing condition of that liberty is that the scene's
 * air closes before the eye reaches the apron's outer edge. An edge you can see
 * reads as a landform, and this project does not draw landforms it has not built.
 *
 * That condition was written as a sentence, in two files, against numbers that
 * have since moved three times. L17 was recorded with a 640 m heightfield, a
 * radial skirt "carried out to 1400 m" and a fog "total by 1500 m"; the box has
 * since been extended east (S2e), north (T-1123) and south (T-0464), and
 * `generators/terrain_gen.py` re-derives the apron from the box every time
 * (T-0152). The committed apron is 2,659.84 m. The air was left where a
 * 1,500 m argument put it — total at 1,883 m — so the sentence stayed true only
 * in the safe direction, by 776.7 m of air nobody had a reason for, and the cost
 * was a prairie that went featureless at about 1.2 km.
 *
 * A prose condition cannot notice that. This can, in both directions:
 *
 *   1. the two HAZE_DENSITY literals agree. `trees.js` keeps a COPY, by design
 *      and with its reason written down — and the instruction beside it, "if
 *      world.js's haze moves, move these", is exactly the kind a later edit
 *      forgets. Divergence is silent: the far timber band and the ground it
 *      stands on would simply run different atmospheres.
 *   2. the haze's own total distance — sqrt(ln 255) / density, the distance past
 *      which a surface cannot move an 8-bit channel, which is the same function
 *      `terrain.js`'s `hazeReachM()` derives the ground cull from — does not run
 *      past ANY epoch's published `skirt.margin_m`. Every epoch, because each
 *      one derives its own apron from its own box and the scene picks between
 *      them by year.
 *
 * It does NOT assert a particular density. Thinning the air further is a
 * legitimate thing to want and the answer is more ground, not a looser check: the
 * bound moves the moment the apron does, which is the point.
 *
 * ## Why the correction lives here and not in the generator
 *
 * `generators/terrain_gen.py`'s own comment beside `SKIRT_MARGIN_MIN_M` still
 * reads "the margin is AT LEAST the distance at which world.js's haze is total",
 * and that sentence is still TRUE — 2,659.84 m against 2,644.9 m, by 14.9 m. What
 * it no longer conveys is which way the dependence runs: 1500.0 is a FLOOR on the
 * apron, not the haze's figure, and the haze is now solved from the margin the
 * generator derives rather than the other way round. It was left unedited on
 * purpose. That file is an input to the terrain staleness hash, so a comment
 * changed in it makes `terrain__e1834_harbor_cut.glb` and its water stale and
 * demands a full terrain re-bake — measured, on this ticket, by making the edit
 * and watching `validate.py --stale` refuse it. A prose improvement is not worth
 * a regenerated heightfield, and this file plus L17 carry the correction instead.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
/** 8-bit channel: the last representable step is one part in 255. */
const STEPS = 255;
export const hazeTotalM = (density) => Math.sqrt(Math.log(STEPS)) / density;

/** The `const HAZE_DENSITY = <n>;` a file declares, or null. */
export function readDensity(text) {
  const m = /^const HAZE_DENSITY = ([0-9.eE+-]+);$/m.exec(text);
  return m ? Number(m[1]) : null;
}

const DENSITY_FILES = ['renderers/web/js/world.js', 'renderers/web/js/trees.js'];

/** Every epoch's published apron width, from the heightfield meta. */
function aprons(root) {
  const dir = path.join(root, 'data/terrain/epochs');
  const out = [];
  for (const ep of fs.readdirSync(dir).sort()) {
    const f = path.join(dir, ep, 'heightfield.json');
    if (!fs.existsSync(f)) continue;
    const margin = JSON.parse(fs.readFileSync(f, 'utf-8'))?.skirt?.margin_m;
    out.push({ epoch: ep, marginM: typeof margin === 'number' ? margin : null });
  }
  return out;
}

/** The whole reading, so the self-test can drive it over a fabricated tree. */
export function read(root, overrides = {}) {
  const densities = DENSITY_FILES.map((rel) => ({
    file: rel,
    density: rel in overrides ? overrides[rel] : readDensity(
      fs.readFileSync(path.join(root, rel), 'utf-8')),
  }));
  const found = aprons(root).map((a) => (a.epoch in overrides
    ? { ...a, marginM: overrides[a.epoch] } : a));
  const fails = [];
  for (const d of densities) {
    if (!(d.density > 0)) fails.push(`${d.file}: no HAZE_DENSITY literal to read`);
  }
  const distinct = [...new Set(densities.filter((d) => d.density > 0)
    .map((d) => d.density))];
  if (distinct.length > 1) {
    fails.push('the two HAZE_DENSITY literals disagree: '
      + densities.map((d) => `${d.file} ${d.density}`).join(' vs ')
      + ' — trees.js keeps a copy of world.js\'s haze and they must match');
  }
  if (!found.length) fails.push('no epoch publishes skirt.margin_m');
  const density = distinct[0];
  const totalM = density > 0 ? hazeTotalM(density) : null;
  for (const a of found) {
    if (a.marginM === null) {
      fails.push(`${a.epoch}: heightfield.json publishes no skirt.margin_m`);
    } else if (totalM !== null && totalM > a.marginM) {
      fails.push(`${a.epoch}: the haze is not total until ${totalM.toFixed(1)} m `
        + `but the ground apron ends at ${a.marginM.toFixed(2)} m — `
        + `${(totalM - a.marginM).toFixed(1)} m of L17's unclaimed apron would be `
        + 'visible at its outer edge. Thicken the air or widen the apron.');
    }
  }
  return { densities, aprons: found, density, totalM, fails };
}

function selfTest() {
  const cases = [
    ['a density whose total runs past the apron',
      { 'renderers/web/js/world.js': 0.0005, 'renderers/web/js/trees.js': 0.0005 }],
    ['the two literals drifting apart',
      { 'renderers/web/js/trees.js': 0.00125 }],
    ['an apron that has shrunk under the air', { e1834_harbor_cut: 900 }],
    ['a missing density literal', { 'renderers/web/js/world.js': null }],
  ];
  let bad = 0;
  const live = read(ROOT);
  if (live.fails.length) { console.log('   self-test | SKIP — the live tree is already red'); }
  for (const [what, overrides] of cases) {
    const r = read(ROOT, overrides);
    const ok = r.fails.length > 0;
    if (!ok) bad += 1;
    console.log(`   self-test | ${ok ? 'FAIL caught' : 'NOT CAUGHT'} — ${what}`
      + (ok ? `: ${r.fails[0].slice(0, 110)}` : ''));
  }
  console.log(bad ? `SELF-TEST FAILED — ${bad} refusal(s) not caught`
    : 'self-test: every refusal fires when it should');
  return bad === 0;
}

if (process.argv.includes('--self-test')) process.exit(selfTest() ? 0 : 1);

const r = read(ROOT);
if (process.argv.includes('--json')) console.log(JSON.stringify(r, null, 1));
else {
  console.log(`haze density ${r.density} — total at ${r.totalM?.toFixed(1)} m`);
  for (const a of r.aprons) {
    const slack = a.marginM === null || r.totalM === null ? null : a.marginM - r.totalM;
    console.log(`  ${a.epoch}: apron ${a.marginM?.toFixed(2)} m`
      + (slack === null ? '' : `  (total ${slack.toFixed(1)} m inside its edge)`));
  }
}
for (const f of r.fails) console.log(`FAIL ${f}`);
process.exit(r.fails.length ? 1 : 0);
