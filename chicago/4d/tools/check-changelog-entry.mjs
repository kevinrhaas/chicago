// check-changelog-entry.mjs — does this change carry a changelog entry?
//
// T-0409. `tools/check-changelog.mjs` checks the changelog's SHAPE: that it
// parses, that versions are dense and descending, that timestamps are stamped
// and the two mirrors match. It is green on a file nobody touched. So a PR that
// changes the app and writes nothing about it passes every gate the pipeline
// has, and AGENTS.md's "prepend one entry … before merging to dev" is a rule
// with no enforcement behind it.
//
// It has happened twice that we know of. PR #549 (T-0399) merged on 2026-08-29
// having removed 21 business records and added a whole identity structure, with
// no entry — found only because a sibling slice read the file afterwards. Then
// on 2026-08-31 PR #619 changed where the town stands its hitching posts and
// shipped no entry either; the owner noticed because the walkthrough's What's-new
// tab was showing a change two merges old. Both entries had to be written
// retroactively by someone who had not done the work, which is the wrong shape:
// whoever made the change is the only one who knows what to say about it.
//
// WHY THIS IS NOT IN check.sh. The nightly bake regenerates `data/` and ships no
// changelog entry, correctly — it carries no change, only rebuilt bytes. A gate
// inside `check.sh` would fail every bake. This runs from the PR gate workflow
// instead, where a base ref exists and the question is meaningful.
//
//   node tools/check-changelog-entry.mjs <base-sha> <head-sha>
//
// THE OPT-OUT IS A SENTENCE SOMEBODY HAS TO WRITE. A branch that genuinely
// changes nothing a reader would care about says so in a commit trailer:
//
//   Changelog: none — <why this changes nothing a visitor or the feed would see>
//
// The reason is required and is not checked for content. The point is that a
// person had to decide and had to sign it, which is the same trade the liberty
// ledger and the refusal lists make everywhere else in this project.
import { execFileSync } from 'node:child_process';

const [base, head] = process.argv.slice(2);
if (!base || !head) {
  console.error('usage: check-changelog-entry.mjs <base-sha> <head-sha>');
  process.exit(2);
}

const git = (...args) => execFileSync('git', args, { encoding: 'utf8' });

/** The paths whose change is a change to the town or to how it is built. */
const WATCHED = [
  'chicago/4d/renderers/',
  'chicago/4d/data/',
  'chicago/4d/tools/',
  'chicago/4d/generators/',
  'chicago/4d/assets/',
];
/** …and the ones inside those that are bookkeeping rather than the thing itself. */
const EXEMPT = [
  'chicago/4d/tickets/',
  'chicago/4d/docs/',
  // A SMOKE READING IS EVIDENCE THAT A GATE WAS RUN, NEVER A CHANGE TO THE TOWN,
  // and this file was the single commonest cause of a red PR on 2026-09-13. The
  // owner: "Getting some red PR's, can you find what is going on make the fix so
  // they don't break again".
  //
  // `tools/dev-smoke-state.json` is T-0216's append-only register of smoke results,
  // and it sits under the watched `tools/` prefix by accident of where it lives.
  // AGENTS.md REQUIRES a run to file its readings (`dev-smoke-state.mjs record`),
  // so the gate was firing on runs for doing exactly what the contract asks — and
  // the fix every time was a `Changelog: none` trailer explaining that a test
  // result is not a release note, written by hand, over and over.
  //
  // Measured on the open PRs that afternoon: #1264 and #1269 were red with this
  // file as the ONLY watched path they touched, and #1263 is a PR whose whole
  // content is five smoke readings. The same hand-written trailer had already been
  // added to #1090, #1108, #1126 and #1247 on 2026-09-11.
  //
  // #1255 is the shape this does NOT excuse, and it was checked rather than assumed:
  // it touched the smoke register AND `tools/smoke_renderer.mjs`, a real change to
  // the suite, so it stays red until it carries an entry or a reason. Readings filed
  // beside a change are still readings beside a change.
  //
  // NOTHING ELSE UNDER tools/ IS EXEMPTED, deliberately. The baselines beside it —
  // research_spend_baseline.json, layer_reads_baseline.json, the Chappel banked
  // reading — MOVE when real work moves, and a changed baseline is a claim about
  // the town that a reader may well want to hear about. Only the record of having
  // run a test is exempt, because it says nothing about the town at all.
  'chicago/4d/tools/dev-smoke-state.json',
];
const CHANGELOG = 'chicago/4d/renderers/web/js/changelog.js';

const changed = git('diff', '--name-only', `${base}...${head}`)
  .split('\n').map((s) => s.trim()).filter(Boolean);

const touched = changed.filter((f) =>
  WATCHED.some((w) => f.startsWith(w)) && !EXEMPT.some((e) => f.startsWith(e)));

if (touched.length === 0) {
  console.log('changelog entry: not required — this change touches nothing under '
    + WATCHED.map((w) => w.replace('chicago/4d/', '')).join(', '));
  process.exit(0);
}

if (changed.includes(CHANGELOG)) {
  console.log(`changelog entry: present — ${touched.length} watched file(s) changed `
    + 'and changelog.js changed with them');
  process.exit(0);
}

// The opt-out, read from every commit the PR carries.
const trailer = git('log', '--format=%B', `${base}..${head}`)
  .split('\n').find((l) => /^Changelog:\s*none\b/i.test(l.trim()));
if (trailer) {
  const why = trailer.replace(/^Changelog:\s*none\s*[—:-]?\s*/i, '').trim();
  if (!why) {
    console.error('changelog entry: `Changelog: none` was written with no reason after it.');
    console.error('The reason is the whole point — write what changes nothing a reader would see.');
    process.exit(1);
  }
  console.log(`changelog entry: opted out — "${why}"`);
  process.exit(0);
}

console.error('changelog entry: MISSING.\n');
console.error(`${touched.length} file(s) under the watched paths changed and `
  + `${CHANGELOG} did not:\n`);
for (const f of touched.slice(0, 12)) console.error(`  ${f}`);
if (touched.length > 12) console.error(`  … and ${touched.length - 12} more`);
console.error('\nAGENTS.md: "prepend one entry to renderers/web/js/changelog.js …');
console.error('Stamp BEFORE merging to dev; nothing stamps later in the pipeline."\n');
console.error('Write the entry, then `node tools/stamp-changelog.mjs`. If this branch');
console.error('genuinely changes nothing a visitor or the release feed would see, say so');
console.error('in a commit trailer and this gate will take your word for it:\n');
console.error('  Changelog: none — <why>\n');
process.exit(1);
