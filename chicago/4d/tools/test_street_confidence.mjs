#!/usr/bin/env node
/**
 * T-0100 / T-0713 — a street's grades reach the picture, and each grades the
 * thing it is a claim about.
 *
 * T-0100. `streets.js` used to grade a ribbon by `surface_confidence` and
 * `wear_confidence` alone and never by `geometry_confidence` — the field that
 * says whether the LINE was traced, inferred or invented. A street whose route
 * was invented but whose surface and wear were attested drew at full
 * confidence, and turning `reconstructed` off left the invention standing.
 * T-0100 fixed that by taking the weakest of all three.
 *
 * T-0713 splits the one grade back into the two claims it had flattened:
 *
 *   `_confidence`, the contract's channel and the one the confidence view
 *   reads, carries the LINE's grade alone — presence, dither, and which level
 *   hides the ribbon. That is the claim "a street ran here".
 *
 *   `_trackConfidence`, a second channel read only inside the street material,
 *   carries the weakest of surface and wear and fades the WORN TEXTURE while
 *   the view is on. That is the claim "and it looked like this".
 *
 * The guard T-0100 bought is not weakened by the split and this file is what
 * proves it: an invented line under an attested surface still dithers out, and
 * a record with no geometry grade still reads as invented rather than as
 * attested. What the split adds is the converse — an ATTESTED line under an
 * invented wear no longer dithers away, because "we do not know how worn it
 * was" is not a reason to tell the visitor the street was not there.
 *
 * WHY THIS TEST SLICES THE SOURCE INSTEAD OF IMPORTING IT. `addRecord` is not
 * exported and `streets.js` pulls in three, which will not load headless. The
 * alternative — copying the expressions into the test — would let the shipped
 * ones drift away from the tested ones silently, which is the failure mode
 * these tickets are about in the first place. So both expressions are
 * EXTRACTED from `renderers/web/js/streets.js` and evaluated, the same way
 * `tools/measure_rank_bias.mjs` takes its primitives out of `flora.js`. Every
 * extraction is guarded: if the shape moves, this file fails loudly rather
 * than testing a stale copy of itself.
 *
 *   node tools/test_street_confidence.mjs
 *
 * Exit 0 on pass, 1 on any failed check, 2 if the source could not be read the
 * way this test needs to read it (drift).
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = join(ROOT, 'renderers/web/js/streets.js');
const INDEX = join(ROOT, 'data/sidecars/1835/index.json');

const src = readFileSync(SRC, 'utf8');

function drift(msg) {
  console.error(`DRIFT — ${msg}`);
  console.error(`  ${SRC} no longer has the shape this test reads it with.`);
  console.error('  Fix the test against the source; do NOT weaken the checks.');
  process.exit(2);
}

/* ---- the shipped LEVEL map -------------------------------------------- */

const levelMatch = /^const LEVEL = (\{[^}]*\});/m.exec(src);
if (!levelMatch) drift('cannot find `const LEVEL = { ... };`');
let LEVEL;
try {
  LEVEL = Function(`"use strict"; return (${levelMatch[1]});`)();
} catch (e) {
  drift(`the LEVEL literal did not evaluate: ${e.message}`);
}
for (const k of ['attested', 'inferred', 'reconstructed']) {
  if (typeof LEVEL[k] !== 'number') drift(`LEVEL is missing the grade \`${k}\``);
}

/* ---- the two shipped expressions --------------------------------------- */

// The RIBBON's grade — one expression, terminated by the first `;`. Anchored on
// the declaration inside addRecord; nothing else in the file declares it.
const confMatch = /const confidence = ([^;]*);/.exec(src);
if (!confMatch) drift('cannot find `const confidence = ...;`');
const confExpr = confMatch[1].trim();

// The point of T-0100, still: the ribbon's grade must consult the LINE.
if (!confExpr.includes('geometry_confidence')) {
  drift('the ribbon expression does not read `geometry_confidence` — T-0100 is not fixed');
}
// The point of T-0713: and it must consult NOTHING ELSE, or the split has been
// quietly undone and the platted town is dithering as invention again.
for (const field of ['surface_confidence', 'wear_confidence']) {
  if (confExpr.includes(field)) {
    drift(`the ribbon expression still reads \`${field}\` — T-0713's split is undone. `
      + 'The line decides whether the ribbon stands; surface and wear grade the track.');
  }
}

// The TRACK's grade, which is where surface and wear went.
const trackMatch = /const trackConfidence = Math\.max\(\s*([\s\S]*?)\s*\);/.exec(src);
if (!trackMatch) drift('cannot find `const trackConfidence = Math.max( ... );`');
const trackTerms = trackMatch[1]
  .split('\n')
  .map((s) => s.trim().replace(/,$/, ''))
  .filter(Boolean);
if (trackTerms.length !== 2) {
  drift(`expected two terms in the track expression, found ${trackTerms.length}`);
}
for (const field of ['surface_confidence', 'wear_confidence']) {
  if (!trackMatch[1].includes(field)) {
    drift(`the track expression does not read \`${field}\` — the grade has been dropped, `
      + 'not moved. T-0713 relocated these two; it did not retire them.');
  }
}

// The shader must actually spend the track grade, or the channel is carried and
// then thrown away — which would look exactly like a passing test.
if (!/_trackConfidence/.test(src)) {
  drift('`_trackConfidence` is not set as a geometry attribute — the track grade never '
    + 'reaches the shader');
}
if (!/vTrackConfidence \* uConfMode/.test(src)) {
  drift('the fragment block does not fade by `vTrackConfidence * uConfMode` — the track '
    + 'grade reaches the shader and is not spent, or it is spent with the view switched off');
}

const ev = (expr, record) => Function('LEVEL', 'record', `"use strict"; return (${expr});`)(LEVEL, record);
const shipped = (record) => ev(confExpr, record);
const track = (record) => Math.max(...trackTerms.map((t) => ev(t, record)));

// The pre-T-0100 expression: surface and wear only. This is the positive
// control — the case T-0100 describes MUST come out differently under it — and
// it is now exactly the TRACK expression, which is the tidiest possible
// statement of what T-0713 did with those two grades.
const before = track;

/* ---- the checks -------------------------------------------------------- */

let failed = 0;
const ok = (cond, label) => {
  console.log(`  ${cond ? 'ok  ' : 'FAIL'}  ${label}`);
  if (!cond) failed++;
};

const rec = (geometry, surface, wear) => ({
  geometry_confidence: geometry,
  surface_confidence: surface,
  wear_confidence: wear,
});

const INVENTED = LEVEL.reconstructed;
const ATTESTED = LEVEL.attested;

console.log('\n\x1b[1m== the line decides the ribbon, surface and wear decide the track '
  + '(T-0100, T-0713)\x1b[0m');

// T-0100's case, stated as the ticket states it, and it must still hold.
const inventedLine = rec('reconstructed', 'attested', 'attested');
ok(shipped(inventedLine) === INVENTED,
  `an invented LINE under an attested surface dithers out — ${shipped(inventedLine)} of ${INVENTED}`);
ok(before(inventedLine) === ATTESTED,
  `  ...and drew at FULL confidence before T-0100 — the bug, reproduced — ${before(inventedLine)}`);
ok(shipped(inventedLine) !== before(inventedLine),
  '  ...so this test still distinguishes the fix from the fault');

// An inferred line grades as inferred, not rounded to either end.
const inferredLine = rec('inferred', 'attested', 'attested');
ok(shipped(inferredLine) === LEVEL.inferred,
  `an inferred line grades inferred, not attested — ${shipped(inferredLine)}`);

// Fully attested stays fully attested.
ok(shipped(rec('attested', 'attested', 'attested')) === ATTESTED,
  'a wholly attested street still draws at full confidence');

// T-0713's case — the one the old max() could not express. An attested line
// under an invented wear STANDS, and the invention is carried by the track.
const wornAttested = rec('attested', 'inferred', 'reconstructed');
ok(shipped(wornAttested) === ATTESTED,
  'an attested LINE under an invented wear still stands — the ribbon is the line\'s claim');
ok(before(wornAttested) === INVENTED,
  '  ...and dithered away as invention before T-0713 — the fault, reproduced');
ok(track(wornAttested) === INVENTED,
  '  ...while the TRACK on it grades invented, so the invention is shown, not dropped');

// The track grade is the weakest of the two, not the first of them.
ok(track(rec('attested', 'reconstructed', 'attested')) === INVENTED,
  'an invented SURFACE grades the track invented even under attested wear');

// A record with no geometry grade must fall to the conservative end rather than
// silently reading as attested. This is the guard that must never be weakened.
ok(shipped({ surface_confidence: 'attested', wear_confidence: 'attested' }) === INVENTED,
  'a record with NO geometry grade is treated as invented, not as attested');
ok(track({ geometry_confidence: 'attested' }) === INVENTED,
  'a record with NO surface or wear grade grades its track invented, not attested');

/* ---- and what the shipped town does ------------------------------------ */

const index = JSON.parse(readFileSync(INDEX, 'utf8'));
const streets = index.streets ?? [];
ok(streets.length > 0, `the shipped index carries street records — ${streets.length}`);

const missing = streets.filter((r) => !('geometry_confidence' in r));
ok(missing.length === 0,
  `every shipped street record carries a geometry grade — ${streets.length - missing.length} of ${streets.length}`);

// T-0713 is the commit that made this layer stop being degenerate, and the
// measurement is the deliverable rather than a footnote: before the split every
// record was pinned at `reconstructed` by its wear grade, so no street could
// draw at any other level whatever its line said.
// A STREET THAT WAS NEVER OPENED IS NOT IN THIS MEASUREMENT. T-0713's finding is about
// the gap between a street's LINE and the invented wear on its TRACK, and the twenty-six
// lines Wright ruled across the School Section have no track: they compile with
// `opened: false` and a zero track width, and the renderer draws no ribbon for them.
// Grading their wear `reconstructed` to keep the count below would be asserting an
// invented wear on ground nobody had yet worn (T-0797).
const trodden = streets.filter((r) => r.opened !== false);
const stands = trodden.filter((r) => shipped(r) === ATTESTED);
const moved = trodden.filter((r) => shipped(r) !== before(r));
ok(stands.length >= 17,
  `the platted streets stand at full confidence — ${stands.length} attested of ${trodden.length}`);
ok(moved.length === stands.length + trodden.filter((r) => shipped(r) === LEVEL.inferred).length,
  `every street whose line outgrades its track moved — ${moved.length} of ${trodden.length}`);
ok(trodden.every((r) => before(r) === INVENTED),
  'every trodden street still carries an invented WEAR — which is why the split was needed');
ok(streets.length - trodden.length === 49,
  `and the platted-but-unopened lines ship with no track at all — the School Section's`
  + ` twelve east-west tiers and, since T-0877, the fifteen records carrying its fourteen`
  + ` north-south lines (Market is two, because Wright rules it in two stretches),`
  + ` Kinzie's Addition's eleven since T-1060, the Michigan St tract's two streets`
  + ` and two alleys since T-1075, Wabansia's six since T-1070, and Kinzie Street's own`
  + ` reach west of the town since T-1085 — that last one is the only line here whose`
  + ` street is trodden somewhere else, and it is in this population because the wear is`
  + ` attested where the town is and nowhere west of it`
  + ` — ${streets.length - trodden.length}`);
ok(streets.filter((r) => shipped(r) === INVENTED).every((r) => r.geometry_confidence === 'reconstructed'),
  'and the only ribbons still graded invented are the ones whose LINE is invented');

const byLevel = { attested: 0, inferred: 0, reconstructed: 0 };
for (const r of streets) {
  byLevel[shipped(r) === ATTESTED ? 'attested' : shipped(r) === LEVEL.inferred ? 'inferred' : 'reconstructed']++;
}
console.log(`  note  ribbons by level — attested ${byLevel.attested}, inferred ${byLevel.inferred},`
  + ` reconstructed ${byLevel.reconstructed}.`);
console.log('        Hiding `inferred` drops ' + streets.filter((r) => shipped(r) === LEVEL.inferred)
  .map((r) => r.id).join(', ') + ' and leaves the platted town standing.');

console.log(failed ? `\n\x1b[31mSTREET CONFIDENCE FAIL\x1b[0m — ${failed} check(s)` : '\n\x1b[32mSTREET CONFIDENCE PASS\x1b[0m');
process.exit(failed ? 1 : 0);
